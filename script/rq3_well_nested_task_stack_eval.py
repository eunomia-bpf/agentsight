#!/usr/bin/env python3
"""Infer and score a literal well-nested online task stack.

The controller reads one source-native turn at a time and emits exactly one
of three transitions: stay, push one concrete nested task, or pop one leaf.
Human stages are never opened by inference.  Scoring reuses the independently
verified Step 0056 score rows after all candidate paths are materialized.
"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import json
from pathlib import Path
import re
import sys
import time
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "script"))

import rq3_source_native_task_progress_boundary_eval as source  # noqa: E402
import rq3_stateful_native_turn_task_stack_eval as stateful  # noqa: E402
import rq3_stateful_visible_path_identity_eval as visible  # noqa: E402


base = source.base
ALGORITHM_VERSION = "well-nested-task-stack-v1"
SCHEMA = "agentsight.rq3-well-nested-task-stack"
EXPECTED_SESSIONS = 405
EXPECTED_TURNS = 17_148
EXPECTED_OPERATIONS = 20_866
EXPECTED_STAGES = 2_948
EXPECTED_TASKS = 251
SEED = 20_260_720
BOOTSTRAP_RESAMPLES = 10_000
LABEL_MAX_CHARS = stateful.LABEL_MAX_CHARS
OUTPUT_TOKENS = stateful.OUTPUT_TOKENS
LABEL_PATTERN = stateful.LABEL_PATTERN
PHASE_LABEL = re.compile(r"^phase-?\d+$")

SYSTEM_PROMPT = """Maintain the active TASK stack for one AI agent. The
immutable concrete task is the root and is never removed. Persistent frames are
only nested task goals or responsibilities with a completion condition that can
span multiple agent turns. A phase, strategy, semantic action, tool, command,
file, path, object, status, result, inspect, edit, test, retry, or one atomic
operation is evidence about a task, not by itself a task frame. A change in
such evidence does not justify a new frame.

Use stay when the turn advances, inspects, edits, tests, retries, or checks the
current leaf goal. Use push only when the turn begins one genuinely nested goal.
Use pop only when the current leaf has completed or been abandoned and its
immediate parent resumes. Pop removes exactly one frame. A sibling can begin
only on a later turn after returning to the parent. Add at most one frame per
turn. A new label is a concise lowercase English task-goal phrase, not a
tool/action/file/status description. Return only the required JSON."""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    infer = commands.add_parser("infer")
    infer.add_argument("mode", choices=("preflight", "full"))
    infer.add_argument("--target-operations", type=Path, required=True)
    infer.add_argument("--raw-root", type=Path, required=True)
    infer.add_argument("--llama-url", required=True)
    infer.add_argument("--workers", type=int, default=8)
    infer.add_argument("--timeout-seconds", type=int, default=600)
    infer.add_argument("--out", type=Path, required=True)

    score = commands.add_parser("score")
    score.add_argument("--predictions", type=Path, required=True)
    score.add_argument("--inference-summary", type=Path, required=True)
    score.add_argument("--step0056-score-rows", type=Path, required=True)
    score.add_argument("--out", type=Path, required=True)
    return parser.parse_args()


def absolute(path: Path) -> Path:
    return path if path.is_absolute() else ROOT / path


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def grammar_for_depth(depth: int) -> str:
    label = (
        'label ::= "\\\"" [a-z] [a-z0-9 /+._-]'
        f'{{0,{LABEL_MAX_CHARS - 1}}} "\\\""\n'
    )
    stay = 'stay ::= "{\\\"transition\\\":\\\"stay\\\"}"\n'
    push = (
        'push ::= "{\\\"transition\\\":\\\"push\\\",'
        '\\\"label\\\":" label "}"\n'
    )
    if depth == 0:
        return "root ::= stay | push\n" + stay + push + label
    pop = 'pop ::= "{\\\"transition\\\":\\\"pop\\\"}"\n'
    return "root ::= stay | push | pop\n" + stay + push + pop + label


def parse_transition(raw: str, depth: int) -> dict[str, Any]:
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as error:
        raise RuntimeError(f"model output is not JSON: {raw!r}") from error
    require(isinstance(value, dict), "transition is not an object")
    kind = value.get("transition")
    if kind in {"stay", "pop"}:
        require(set(value) == {"transition"}, f"{kind} keys")
        if kind == "pop":
            require(depth > 0, "pop at root")
    elif kind == "push":
        require(set(value) == {"transition", "label"}, "push keys")
        label = value["label"]
        require(type(label) is str and 0 < len(label) <= LABEL_MAX_CHARS, "label length")
        require(LABEL_PATTERN.fullmatch(label) is not None, "label syntax")
    else:
        raise RuntimeError(f"unknown transition: {kind!r}")
    return value


def apply_transition(
    session: str,
    stack: list[dict[str, str]],
    proposal: dict[str, Any],
    next_frame: int,
    root: str,
) -> tuple[list[dict[str, str]], int, dict[str, Any], bool]:
    leaf = stack[-1]["label"] if stack else root
    duplicate = proposal["transition"] == "push" and proposal["label"] == leaf
    transition = {"transition": "stay"} if duplicate else dict(proposal)
    if transition["transition"] == "stay":
        output = [dict(frame) for frame in stack]
    elif transition["transition"] == "push":
        output = [dict(frame) for frame in stack]
        output.append(
            {
                "instance": f"{session}:frame-{next_frame:05d}",
                "label": str(transition["label"]),
            }
        )
        next_frame += 1
    else:
        require(transition["transition"] == "pop" and bool(stack), "invalid pop")
        output = [dict(frame) for frame in stack[:-1]]
    return output, next_frame, transition, duplicate


def request_hash(user: str, grammar: str) -> str:
    return hashlib.sha256(
        json.dumps(
            {
                "algorithm": ALGORITHM_VERSION,
                "model": base.MODEL,
                "model_sha256": base.MODEL_SHA256,
                "seed": SEED,
                "temperature": 0,
                "system": SYSTEM_PROMPT,
                "grammar": grammar,
                "user": user,
            },
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode()
    ).hexdigest()


def infer_session(
    session: str,
    rows: list[dict[str, Any]],
    raw_root: Path,
    llama_url: str,
    timeout_seconds: int,
    cache_dir: Path,
) -> dict[str, Any]:
    material = source.reconstruct_source(raw_root, session, rows)
    turns = stateful.group_turns(material["operations"])
    path = cache_dir / source.cache_name(session)
    if path.is_file():
        result = json.loads(path.read_text(encoding="utf-8"))
        require(result.get("algorithm_version") == ALGORITHM_VERSION, "cache version")
        require(result.get("session") == session, "cache session")
        require(result.get("archive_sha256") == material["archive_sha256"], "cache archive")
        require(result.get("adapter") == material["adapter"], "cache adapter")
        require(result.get("model") == base.MODEL, "cache model")
        require(result.get("model_sha256") == base.MODEL_SHA256, "cache model hash")
    else:
        result = {
            "schema": SCHEMA + ".session.v1",
            "algorithm_version": ALGORITHM_VERSION,
            "session": session,
            "framework": material["framework"],
            "adapter": material["adapter"],
            "archive": material["archive"],
            "archive_sha256": material["archive_sha256"],
            "task_source": material["task_source"],
            "model": base.MODEL,
            "model_sha256": base.MODEL_SHA256,
            "seed": SEED,
            "root_label": stateful.root_label(material["task"]),
            "input_turns": len(turns),
            "input_operations": len(material["operations"]),
            "transitions": [],
        }
        stateful.write_json_atomic(path, result)

    cached = result["transitions"]
    require(len(cached) <= len(turns), "cache longer than turns")
    stack: list[dict[str, str]] = []
    next_frame = 0
    preceding_result = ""
    for index, turn in enumerate(turns):
        grammar = grammar_for_depth(len(stack))
        user = stateful.prompt_for(
            material["task"], result["root_label"], stack, turn, preceding_result
        )
        digest = request_hash(user, grammar)
        stack_before = [dict(frame) for frame in stack]
        if index < len(cached):
            record = cached[index]
            require(int(record["turn_index"]) == index, "cached turn order")
            require(record["request_sha256"] == digest, "cached request drift")
            proposal = parse_transition(str(record["raw_response"]), len(stack))
            stack, next_frame, transition, duplicate = apply_transition(
                session, stack, proposal, next_frame, result["root_label"]
            )
            require(record["proposed_transition"] == proposal, "cached proposal")
            require(record["transition"] == transition, "cached transition")
            require(bool(record["duplicate_leaf_stay"]) == duplicate, "cached invariant")
            require(record["stack_before"] == stack_before, "cached stack before")
            require(record["stack_after"] == stack, "cached stack after")
        else:
            raw, response, attempts = base.call_model(
                llama_url,
                SYSTEM_PROMPT,
                user,
                grammar,
                timeout_seconds,
                OUTPUT_TOKENS,
            )
            proposal = parse_transition(raw, len(stack))
            stack, next_frame, transition, duplicate = apply_transition(
                session, stack, proposal, next_frame, result["root_label"]
            )
            record = {
                "turn_index": index,
                "source_turn_id": turn["source_turn_id"],
                "step_ids": [int(row["step"]) for row in turn["operations"]],
                "request_sha256": digest,
                "prompt": user,
                "raw_response": raw,
                "proposed_transition": proposal,
                "transition": transition,
                "duplicate_leaf_stay": duplicate,
                "stack_before": stack_before,
                "stack_after": [dict(frame) for frame in stack],
                "active_leaf_instance": (
                    stack[-1]["instance"] if stack else f"{session}:task-root"
                ),
                "active_leaf_label": (
                    stack[-1]["label"] if stack else result["root_label"]
                ),
                "usage": response.get("usage") or {},
                "attempts": attempts,
            }
            cached.append(record)
            stateful.write_json_atomic(path, result)
        preceding_result = stateful.unique_text(turn["operations"], "result")

    require(len(cached) == len(turns), "transition coverage")
    predictions: list[dict[str, Any]] = []
    for turn, record in zip(turns, cached, strict=True):
        for operation in turn["operations"]:
            predictions.append(
                {
                    "session": session,
                    "framework": material["framework"],
                    "adapter": material["adapter"],
                    "step_id": int(operation["step"]),
                    "source_ref": operation["source_ref"],
                    "turn_index": int(turn["turn_index"]),
                    "turn_instance": f"{session}:turn-{int(turn['turn_index']):04d}",
                    "proposed_transition": record["proposed_transition"]["transition"],
                    "transition": record["transition"]["transition"],
                    "duplicate_leaf_stay": bool(record["duplicate_leaf_stay"]),
                    "task_depth": 1 + len(record["stack_after"]),
                    "task_path": [
                        {
                            "instance": f"{session}:task-root",
                            "label": result["root_label"],
                        },
                        *record["stack_after"],
                    ],
                    "active_leaf_instance": record["active_leaf_instance"],
                    "active_leaf_label": record["active_leaf_label"],
                    "intent_available": bool(str(operation["intent"]).strip()),
                    "progress_available": bool(str(operation["progress"]).strip()),
                    "result_available": bool(str(operation["result"]).strip()),
                }
            )
    return {"cache": result, "predictions": predictions}


def run_inference(args: argparse.Namespace) -> None:
    started = time.monotonic()
    target_path = absolute(args.target_operations)
    raw_root = absolute(args.raw_root)
    out_dir = absolute(args.out)
    grouped = base.load_visible_operations(target_path)
    require(len(grouped) == EXPECTED_SESSIONS, "target session count")
    require(sum(map(len, grouped.values())) == EXPECTED_OPERATIONS, "target operation count")
    selected = stateful.preflight_sessions(grouped) if args.mode == "preflight" else sorted(grouped)
    cache_dir = out_dir / "sessions"
    cache_dir.mkdir(parents=True, exist_ok=True)
    results: dict[str, dict[str, Any]] = {}
    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = {
            executor.submit(
                infer_session,
                session,
                grouped[session],
                raw_root,
                args.llama_url,
                args.timeout_seconds,
                cache_dir,
            ): session
            for session in selected
        }
        for future in as_completed(futures):
            session = futures[future]
            results[session] = future.result()
            print(f"inferred {len(results)}/{len(selected)} {session}", flush=True)

    predictions = [
        row for session in sorted(results) for row in results[session]["predictions"]
    ]
    transitions = [
        row
        for session in sorted(results)
        for row in results[session]["cache"]["transitions"]
    ]
    expected_operations = sum(len(grouped[session]) for session in selected)
    require(len(predictions) == expected_operations, "prediction coverage")
    require(
        len({(row["session"], row["step_id"]) for row in predictions})
        == expected_operations,
        "prediction uniqueness",
    )
    if args.mode == "full":
        require(len(transitions) == EXPECTED_TURNS, "full native turn count")
    stateful.write_jsonl(out_dir / "predictions.jsonl", predictions)

    depths = [int(row["task_depth"]) for row in predictions]
    session_depths: dict[str, list[int]] = defaultdict(list)
    for row in predictions:
        session_depths[str(row["session"])].append(int(row["task_depth"]))
    usage = sum(
        (
            Counter(
                {
                    key: value
                    for key, value in (row.get("usage") or {}).items()
                    if isinstance(value, int)
                }
            )
            for row in transitions
        ),
        Counter(),
    )
    proposed = Counter(row["proposed_transition"]["transition"] for row in transitions)
    applied = Counter(row["transition"]["transition"] for row in transitions)
    labels = [
        row["proposed_transition"].get("label", "")
        for row in transitions
        if "label" in row["proposed_transition"]
    ]
    summary = {
        "schema": SCHEMA + ".inference.v1",
        "algorithm_version": ALGORITHM_VERSION,
        "status": "complete",
        "mode": args.mode,
        "model": base.MODEL,
        "model_sha256": base.MODEL_SHA256,
        "seed": SEED,
        "sessions": len(selected),
        "turns": len(transitions),
        "operations": len(predictions),
        "adapter_layouts": dict(Counter(row["adapter"] for row in predictions)),
        "frameworks": dict(Counter(row["framework"] for row in predictions)),
        "proposed_transition_counts": dict(proposed),
        "applied_transition_counts": dict(applied),
        "duplicate_leaf_stays": sum(row["duplicate_leaf_stay"] for row in transitions),
        "new_frame_rate": applied["push"] / len(transitions),
        "depth_including_root": {
            "minimum": min(depths),
            "maximum": max(depths),
            "mean": sum(depths) / len(depths),
            "counts": dict(sorted(Counter(depths).items())),
        },
        "session_max_depth": {
            "minimum": min(max(values) for values in session_depths.values()),
            "maximum": max(max(values) for values in session_depths.values()),
            "median": base.percentile([max(values) for values in session_depths.values()], 0.5),
            "p90": base.percentile([max(values) for values in session_depths.values()], 0.9),
        },
        "sessions_with_no_depth_decrease": sum(
            all(right >= left for left, right in zip(values, values[1:]))
            for values in session_depths.values()
        ),
        "exact_phase_like_proposals": sum(bool(PHASE_LABEL.fullmatch(label)) for label in labels),
        "model_usage": dict(usage),
        "wall_seconds": time.monotonic() - started,
        "predictions": stateful.relative(out_dir / "predictions.jsonl"),
        "isolation": {
            "official_stages_opened": False,
            "recurrence_assignments_opened": False,
            "current_turn_result_visible": False,
            "active_stack_truncated": False,
            "depth_cap": None,
            "all_operations_retained": True,
        },
    }
    stateful.write_json(out_dir / "inference-summary.json", summary)
    print(json.dumps(summary, sort_keys=True), flush=True)


def load_keyed(path: Path) -> dict[tuple[str, int], dict[str, Any]]:
    rows: dict[tuple[str, int], dict[str, Any]] = {}
    for row in visible.load_jsonl(path):
        key = visible.prediction_key(row)
        require(key not in rows, f"duplicate key in {path}")
        rows[key] = row
    return rows


def build_score_rows(
    predictions: dict[tuple[str, int], dict[str, Any]],
    step0056: dict[tuple[str, int], dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    require(set(predictions) <= set(step0056), "Step 0056 score coverage")
    operations: list[dict[str, Any]] = []
    for key in sorted(predictions):
        prediction = predictions[key]
        source_row = step0056[key]
        labels = visible.visible_labels(prediction)
        operations.append(
            {
                **source_row,
                "candidate_visible_path": key[0] + "::" + visible.encode_path(labels),
                "candidate_hidden_instance": str(prediction["active_leaf_instance"]),
                "candidate_labels": list(labels),
                "candidate_depth": int(prediction["task_depth"]),
            }
        )

    by_session: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in operations:
        by_session[str(row["session"])].append(row)
    methods = (
        "candidate_task_occurrence",
        "step0056_task_occurrence",
        "multires_recurrence",
    )
    pairs: list[dict[str, Any]] = []
    for session in sorted(by_session):
        rows = sorted(by_session[session], key=lambda row: int(row["step_id"]))
        candidate_run = -1
        step0056_run = -1
        previous_candidate: str | None = None
        previous_step0056: str | None = None
        for row in rows:
            candidate_path = str(row["candidate_visible_path"])
            step0056_path = str(row["causal_visible_path"])
            if candidate_path != previous_candidate:
                candidate_run += 1
                previous_candidate = candidate_path
            if step0056_path != previous_step0056:
                step0056_run += 1
                previous_step0056 = step0056_path
            row["candidate_task_occurrence"] = (
                f"{session}:candidate-occurrence-{candidate_run:04d}"
            )
            row["step0056_task_occurrence"] = (
                f"{session}:step0056-occurrence-{step0056_run:04d}"
            )
        for left, right in zip(rows, rows[1:]):
            pair = {
                "session": session,
                "framework": left["framework"],
                "task_name": left["task_name"],
                "position": int(left["step_id"]),
                "official_boundary": left["official_stage"] != right["official_stage"],
            }
            for method in methods:
                pair[method] = left[method] != right[method]
            pairs.append(pair)
    return operations, pairs


def metric_bundle(
    pairs: list[dict[str, Any]], operations: list[dict[str, Any]], methods: Iterable[str]
) -> dict[str, Any]:
    return {
        method: {
            "bcubed": base.bcubed(operations, method),
            "boundary": base.boundary_metrics(pairs, method),
            "span": base.span_metrics(operations, method),
        }
        for method in methods
    }


def result_report(summary: dict[str, Any]) -> str:
    lines = [
        "# Three-Transition Well-Nested Task Stack — Result",
        "",
        f"- status: {summary['status']}",
        f"- registered interpretation: **{summary['registered_interpretation']}**",
        "",
        "## Standard metrics",
        "",
        "| Method | B³ P | B³ R | B³ F1 | Boundary F1 | Exact-span F1 |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for method, values in summary["metrics"].items():
        lines.append(
            f"| {method} | {values['bcubed']['precision']:.6f} | "
            f"{values['bcubed']['recall']:.6f} | {values['bcubed']['f1']:.6f} | "
            f"{values['boundary']['f1']:.6f} | {values['span']['f1']:.6f} |"
        )
    lines.extend(["", "## Claim boundary", "", summary["claim_boundary"], ""])
    return "\n".join(lines)


def run_score(args: argparse.Namespace) -> None:
    prediction_path = absolute(args.predictions)
    inference_path = absolute(args.inference_summary)
    step0056_path = absolute(args.step0056_score_rows)
    out_dir = absolute(args.out)
    for path in (prediction_path, inference_path, step0056_path):
        require(path.is_file(), f"missing score input: {path}")
    inference = json.loads(inference_path.read_text(encoding="utf-8"))
    require(inference["status"] == "complete", "inference incomplete")
    predictions = load_keyed(prediction_path)
    step0056 = load_keyed(step0056_path)
    operations, pairs = build_score_rows(predictions, step0056)
    methods = (
        "candidate_task_occurrence",
        "step0056_task_occurrence",
        "multires_recurrence",
    )
    metrics = metric_bundle(pairs, operations, methods)
    out_dir.mkdir(parents=True, exist_ok=True)
    candidate_minus_recurrence = source.bcubed_task_bootstrap(
        operations,
        "candidate_task_occurrence",
        "multires_recurrence",
        out_dir / "bootstrap-candidate-minus-recurrence.jsonl",
    )
    candidate_minus_step0056 = source.bcubed_task_bootstrap(
        operations,
        "candidate_task_occurrence",
        "step0056_task_occurrence",
        out_dir / "bootstrap-candidate-minus-step0056.jsonl",
    )
    candidate_f1 = metrics["candidate_task_occurrence"]["bcubed"]["f1"]
    recurrence_f1 = metrics["multires_recurrence"]["bcubed"]["f1"]
    supported = candidate_minus_recurrence["ci95"][0] > 0
    contradicted = candidate_minus_recurrence["ci95"][1] <= 0
    interpretation = (
        "diagnostic-preflight"
        if inference["mode"] == "preflight"
        else "supported-and-adopted"
        if supported
        else "contradicted-not-adopted"
        if contradicted
        else "inconclusive-not-adopted"
    )
    summary = {
        "schema": SCHEMA + ".score.v1",
        "status": "complete",
        "mode": inference["mode"],
        "registered_interpretation": interpretation,
        "population": {
            "sessions": len({row["session"] for row in operations}),
            "operations": len(operations),
            "pairs": len(pairs),
            "stage_occurrences": len({row["official_stage"] for row in operations}),
            "task_clusters": len({row["task_name"] for row in operations}),
            "frameworks": dict(Counter(row["framework"] for row in operations)),
            "turns": int(inference["turns"]),
        },
        "metrics": metrics,
        "bootstrap": {
            "candidate_minus_recurrence": candidate_minus_recurrence,
            "candidate_minus_step0056": candidate_minus_step0056,
        },
        "decision": {
            "constructor_adoption": "adopted" if supported else "not-adopted",
            "primary_identity": (
                "maximal contiguous occurrence of one complete ordered "
                "visible task label path"
            ),
            "incumbent": "multires_recurrence",
            "candidate_point_higher": candidate_f1 > recurrence_f1,
            "adoption_interval_wholly_positive": candidate_minus_recurrence["ci95"][0] > 0,
            "adoption_interval_wholly_nonpositive": contradicted,
        },
        "inference_behavior": {
            key: inference[key]
            for key in (
                "proposed_transition_counts",
                "applied_transition_counts",
                "duplicate_leaf_stays",
                "new_frame_rate",
                "depth_including_root",
                "session_max_depth",
                "sessions_with_no_depth_decrease",
                "exact_phase_like_proposals",
            )
        },
        "claim_boundary": (
            "One fixed online controller and session-local flat stage partition only; "
            "no validation of cross-run equivalence, ancestor topology, variable-depth "
            "meaning, generated label semantics, root canonicalization, or the lower "
            "phase/action/object/result suffix."
        ),
    }
    if inference["mode"] == "full":
        require(len(predictions) == EXPECTED_OPERATIONS, "full prediction coverage")
        require(len(operations) == EXPECTED_OPERATIONS, "full scored operations")
        require(summary["population"]["sessions"] == EXPECTED_SESSIONS, "full sessions")
        require(summary["population"]["stage_occurrences"] == EXPECTED_STAGES, "full stages")
        require(summary["population"]["task_clusters"] == EXPECTED_TASKS, "full tasks")
        require(summary["population"]["turns"] == EXPECTED_TURNS, "full turns")
    stateful.write_jsonl(out_dir / "operation-score-rows.jsonl", operations)
    stateful.write_jsonl(out_dir / "boundary-score-rows.jsonl", pairs)
    stateful.write_json(out_dir / "summary.json", summary)
    (out_dir / "report.md").write_text(result_report(summary), encoding="utf-8")
    print(json.dumps(summary, sort_keys=True), flush=True)


def main() -> None:
    args = parse_args()
    if args.command == "infer":
        run_inference(args)
    else:
        run_score(args)


if __name__ == "__main__":
    main()
