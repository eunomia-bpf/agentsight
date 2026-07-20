#!/usr/bin/env python3
"""Causally replay the fixed task stack with one exact-leaf identity rule.

The sole intervention applies a proposed push/replace as stay when its label is
byte-identical to the active visible leaf. Requests are reused from Step 0054
only through the first affected turn; every later turn is newly inferred.
"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path
import re
import sys
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "script"))

import rq3_source_native_task_progress_boundary_eval as source  # noqa: E402
import rq3_stateful_native_turn_task_stack_eval as stateful  # noqa: E402
import rq3_stateful_visible_path_identity_eval as visible  # noqa: E402


base = source.base
ALGORITHM_VERSION = "stateful-exact-leaf-invariant-v1"
SCHEMA = "agentsight.rq3-stateful-exact-leaf-invariant"
EXPECTED_SESSIONS = 405
EXPECTED_TURNS = 17_148
EXPECTED_OPERATIONS = 20_866
EXPECTED_STAGES = 2_948
EXPECTED_TASKS = 251
PHASE_LABEL = re.compile(r"^phase-?\d+$")
ORIGINAL_CACHE_DIR: Path | None = None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    infer = commands.add_parser("infer")
    infer.add_argument("mode", choices=("preflight", "full"))
    infer.add_argument("--target-operations", type=Path, required=True)
    infer.add_argument("--raw-root", type=Path, required=True)
    infer.add_argument("--original-cache-dir", type=Path, required=True)
    infer.add_argument("--llama-url", required=True)
    infer.add_argument("--workers", type=int, default=4)
    infer.add_argument("--timeout-seconds", type=int, default=600)
    infer.add_argument("--out", type=Path, required=True)

    score = commands.add_parser("score")
    score.add_argument("--predictions", type=Path, required=True)
    score.add_argument("--inference-summary", type=Path, required=True)
    score.add_argument("--step0054-score-rows", type=Path, required=True)
    score.add_argument("--step0055-score-rows", type=Path, required=True)
    score.add_argument("--out", type=Path, required=True)
    return parser.parse_args()


def absolute(path: Path) -> Path:
    return path if path.is_absolute() else ROOT / path


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def cache_path(cache_dir: Path, session: str) -> Path:
    return cache_dir / source.cache_name(session)


def apply_invariant(
    proposal: dict[str, Any], stack: list[dict[str, str]], root: str
) -> tuple[dict[str, Any], bool]:
    leaf = stack[-1]["label"] if stack else root
    matched = (
        proposal["transition"] in {"push", "replace"}
        and proposal.get("label") == leaf
    )
    return ({"transition": "stay"}, True) if matched else (dict(proposal), False)


def load_original(session: str) -> dict[str, Any]:
    require(ORIGINAL_CACHE_DIR is not None, "original cache directory unset")
    path = cache_path(ORIGINAL_CACHE_DIR, session)
    require(path.is_file(), f"missing Step 0054 session cache: {session}")
    value = json.loads(path.read_text(encoding="utf-8"))
    require(value.get("algorithm_version") == stateful.ALGORITHM_VERSION, "source cache version")
    require(value.get("session") == session, "source cache session")
    return value


def infer_session(
    session: str,
    rows: list[dict[str, Any]],
    raw_root: Path,
    llama_url: str,
    timeout_seconds: int,
    output_cache_dir: Path,
) -> dict[str, Any]:
    material = source.reconstruct_source(raw_root, session, rows)
    turns = stateful.group_turns(material["operations"])
    original = load_original(session)
    require(original["archive_sha256"] == material["archive_sha256"], "source archive drift")
    require(original["adapter"] == material["adapter"], "source adapter drift")
    require(original["model"] == base.MODEL, "source model drift")
    require(original["model_sha256"] == base.MODEL_SHA256, "source model hash drift")
    require(len(original["transitions"]) == len(turns), "source turn coverage")

    path = cache_path(output_cache_dir, session)
    if path.is_file():
        result = json.loads(path.read_text(encoding="utf-8"))
        require(result.get("algorithm_version") == ALGORITHM_VERSION, "cache version")
        require(result.get("session") == session, "cache session")
        require(result.get("archive_sha256") == material["archive_sha256"], "cache archive")
        require(result.get("model_sha256") == base.MODEL_SHA256, "cache model")
    else:
        result = {
            "schema": SCHEMA + ".session.v1",
            "algorithm_version": ALGORITHM_VERSION,
            "source_algorithm_version": stateful.ALGORITHM_VERSION,
            "session": session,
            "framework": material["framework"],
            "adapter": material["adapter"],
            "archive": material["archive"],
            "archive_sha256": material["archive_sha256"],
            "task_source": material["task_source"],
            "model": base.MODEL,
            "model_sha256": base.MODEL_SHA256,
            "seed": stateful.SEED,
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
    diverged = False
    for index, turn in enumerate(turns):
        grammar = stateful.grammar_for_depth(len(stack))
        user = stateful.prompt_for(
            material["task"], result["root_label"], stack, turn, preceding_result
        )
        digest = stateful.request_hash(user, grammar)
        stack_before = [dict(frame) for frame in stack]
        original_record = original["transitions"][index]

        if index < len(cached):
            record = cached[index]
            require(int(record["turn_index"]) == index, "cached turn order")
            require(record["request_sha256"] == digest, "cached request drift")
            proposal = stateful.parse_transition(record["raw_response"], len(stack))
            applied, invariant_applied = apply_invariant(
                proposal, stack, result["root_label"]
            )
            require(record["proposed_transition"] == proposal, "cached proposal")
            require(record["transition"] == applied, "cached applied transition")
            require(bool(record["invariant_applied"]) == invariant_applied, "cached invariant")
            require(record["stack_before"] == stack_before, "cached stack before")
            stack, next_frame = stateful.apply_transition(
                session, stack, applied, next_frame
            )
            require(record["stack_after"] == stack, "cached stack after")
        else:
            if not diverged:
                require(original_record["request_sha256"] == digest, "prefix request mismatch")
                require(original_record["stack_before"] == stack_before, "prefix stack mismatch")
                raw = str(original_record["raw_response"])
                response = {"usage": original_record.get("usage") or {}}
                attempts = original_record.get("attempts") or []
                response_source = "step0054-exact-request"
            else:
                raw, response, attempts = base.call_model(
                    llama_url,
                    stateful.SYSTEM_PROMPT,
                    user,
                    grammar,
                    timeout_seconds,
                    stateful.OUTPUT_TOKENS,
                )
                response_source = "new-model-call"
            proposal = stateful.parse_transition(raw, len(stack))
            applied, invariant_applied = apply_invariant(
                proposal, stack, result["root_label"]
            )
            stack, next_frame = stateful.apply_transition(
                session, stack, applied, next_frame
            )
            record = {
                "turn_index": index,
                "source_turn_id": turn["source_turn_id"],
                "step_ids": [int(row["step"]) for row in turn["operations"]],
                "request_sha256": digest,
                "prompt": user,
                "raw_response": raw,
                "proposed_transition": proposal,
                "transition": applied,
                "invariant_applied": invariant_applied,
                "response_source": response_source,
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
        diverged = diverged or invariant_applied
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
                    "transition": record["transition"]["transition"],
                    "proposed_transition": record["proposed_transition"]["transition"],
                    "invariant_applied": bool(record["invariant_applied"]),
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


def preflight_sessions(_: dict[str, list[dict[str, Any]]]) -> list[str]:
    require(ORIGINAL_CACHE_DIR is not None, "original cache directory unset")
    categories: dict[str, list[tuple[int, str]]] = defaultdict(list)
    for path in ORIGINAL_CACHE_DIR.glob("*.json"):
        result = json.loads(path.read_text(encoding="utf-8"))
        root = result["root_label"]
        matched = False
        for record in result["transitions"]:
            proposal = record["transition"]
            before = record["stack_before"]
            leaf = before[-1]["label"] if before else root
            if proposal["transition"] in {"push", "replace"} and proposal.get("label") == leaf:
                matched = True
                break
        if matched:
            categories[result["adapter"]].append((len(result["transitions"]), result["session"]))
    require(set(categories) == source.EXPECTED_LAYOUTS, "invariant preflight layouts")
    return sorted(min(candidates)[1] for candidates in categories.values())


def enhance_inference_summary(out_dir: Path) -> None:
    summary_path = out_dir / "inference-summary.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    records: list[dict[str, Any]] = []
    affected_sessions = 0
    session_max_depths: list[int] = []
    never_decreased = 0
    for path in sorted((out_dir / "sessions").glob("*.json")):
        result = json.loads(path.read_text(encoding="utf-8"))
        transitions = result["transitions"]
        records.extend(transitions)
        affected_sessions += any(row["invariant_applied"] for row in transitions)
        depths = [1 + len(row["stack_after"]) for row in transitions]
        session_max_depths.append(max(depths))
        never_decreased += all(right >= left for left, right in zip(depths, depths[1:]))
    new_usage = Counter()
    reused_usage = Counter()
    for row in records:
        target = new_usage if row["response_source"] == "new-model-call" else reused_usage
        target.update(
            {
                key: value
                for key, value in (row.get("usage") or {}).items()
                if isinstance(value, int)
            }
        )
    labels = [
        row["proposed_transition"].get("label", "")
        for row in records
        if "label" in row["proposed_transition"]
    ]
    summary.update(
        {
            "schema": SCHEMA + ".inference.v1",
            "algorithm_version": ALGORITHM_VERSION,
            "source_algorithm_version": stateful.ALGORITHM_VERSION,
            "intervention": "exact same active-leaf push/replace applied as stay",
            "proposed_transition_counts": dict(
                Counter(row["proposed_transition"]["transition"] for row in records)
            ),
            "applied_transition_counts": dict(
                Counter(row["transition"]["transition"] for row in records)
            ),
            "invariant_applications": sum(row["invariant_applied"] for row in records),
            "affected_sessions": affected_sessions,
            "response_sources": dict(Counter(row["response_source"] for row in records)),
            "new_model_usage": dict(new_usage),
            "reused_response_usage": dict(reused_usage),
            "exact_phase_like_proposals": sum(bool(PHASE_LABEL.fullmatch(label)) for label in labels),
            "session_max_depth": {
                "minimum": min(session_max_depths),
                "maximum": max(session_max_depths),
                "median": base.percentile(session_max_depths, 0.5),
                "p90": base.percentile(session_max_depths, 0.9),
            },
            "sessions_with_no_depth_decrease": never_decreased,
        }
    )
    if summary["mode"] == "full":
        require(len(records) == EXPECTED_TURNS, "full enhanced turns")
        require(summary["operations"] == EXPECTED_OPERATIONS, "full enhanced operations")
    stateful.write_json(summary_path, summary)


def run_inference(args: argparse.Namespace) -> None:
    global ORIGINAL_CACHE_DIR
    ORIGINAL_CACHE_DIR = absolute(args.original_cache_dir)
    require(ORIGINAL_CACHE_DIR.is_dir(), "missing original cache directory")
    stateful.infer_session = infer_session
    stateful.preflight_sessions = preflight_sessions
    stateful.run_inference(args)
    enhance_inference_summary(absolute(args.out))


def load_keyed(path: Path) -> dict[tuple[str, int], dict[str, Any]]:
    rows: dict[tuple[str, int], dict[str, Any]] = {}
    for row in visible.load_jsonl(path):
        key = visible.prediction_key(row)
        require(key not in rows, f"duplicate key in {path}")
        rows[key] = row
    return rows


def build_score_rows(
    predictions: dict[tuple[str, int], dict[str, Any]],
    step0054: dict[tuple[str, int], dict[str, Any]],
    step0055: dict[tuple[str, int], dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    require(set(predictions) <= set(step0054), "Step 0054 score coverage")
    require(set(predictions) <= set(step0055), "Step 0055 score coverage")
    operations: list[dict[str, Any]] = []
    global_paths: dict[str, set[str]] = defaultdict(set)
    for key in sorted(predictions):
        prediction = predictions[key]
        source_row = step0054[key]
        baseline_row = step0055[key]
        labels = visible.visible_labels(prediction)
        exact_global = visible.encode_path(labels)
        collapsed_global = visible.encode_path(visible.adjacent_idempotent(labels))
        session = key[0]
        require(source_row["official_stage"] == baseline_row["official_stage"], "gold drift")
        require(source_row["multires_recurrence"] == baseline_row["multires_recurrence"], "recurrence drift")
        global_paths[exact_global].add(session)
        operations.append(
            {
                **source_row,
                "causal_visible_path": session + "::" + exact_global,
                "causal_adjacent_diagnostic": session + "::" + collapsed_global,
                "step0055_visible_path": str(baseline_row["visible_path"]),
                "causal_hidden_instance": str(prediction["active_leaf_instance"]),
                "invariant_applied": bool(prediction["invariant_applied"]),
                "causal_labels": list(labels),
            }
        )

    by_session: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in operations:
        by_session[str(row["session"])].append(row)
    methods = (
        "causal_visible_path",
        "step0055_visible_path",
        "multires_recurrence",
        "causal_adjacent_diagnostic",
        "causal_hidden_instance",
    )
    pairs: list[dict[str, Any]] = []
    for session in sorted(by_session):
        rows = sorted(by_session[session], key=lambda row: int(row["step_id"]))
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
    recurring = [sessions for sessions in global_paths.values() if len(sessions) >= 2]
    folding = {
        "distinct_global_exact_paths": len(global_paths),
        "paths_seen_in_multiple_sessions": len(recurring),
        "maximum_sessions_for_one_path": max(map(len, global_paths.values()), default=0),
        "accuracy_interpretation": "none; global path recurrence is descriptive only",
    }
    return operations, pairs, folding


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
        "# Causal Exact Task-Identity Invariant — Result",
        "",
        f"- status: {summary['status']}",
        f"- online constructor: **{summary['decision']['constructor_adoption']}**",
        f"- branch: **{summary['decision']['branch_disposition']}**",
        "",
        "## Standard metrics",
        "",
        "| Method | B³ P | B³ R | B³ F1 | Boundary F1 | Span F1 |",
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
    step0054_path = absolute(args.step0054_score_rows)
    step0055_path = absolute(args.step0055_score_rows)
    out_dir = absolute(args.out)
    for path in (prediction_path, inference_path, step0054_path, step0055_path):
        require(path.is_file(), f"missing score input: {path}")
    inference = json.loads(inference_path.read_text(encoding="utf-8"))
    require(inference["status"] == "complete", "inference incomplete")
    predictions = load_keyed(prediction_path)
    step0054 = load_keyed(step0054_path)
    step0055 = load_keyed(step0055_path)
    operations, pairs, folding = build_score_rows(predictions, step0054, step0055)
    methods = (
        "causal_visible_path",
        "step0055_visible_path",
        "multires_recurrence",
        "causal_adjacent_diagnostic",
        "causal_hidden_instance",
    )
    metrics = metric_bundle(pairs, operations, methods)
    out_dir.mkdir(parents=True, exist_ok=True)
    causal_minus_recurrence = source.bcubed_task_bootstrap(
        operations,
        "causal_visible_path",
        "multires_recurrence",
        out_dir / "bootstrap-causal-minus-recurrence.jsonl",
    )
    causal_minus_step0055 = source.bcubed_task_bootstrap(
        operations,
        "causal_visible_path",
        "step0055_visible_path",
        out_dir / "bootstrap-causal-minus-step0055.jsonl",
    )
    per_framework: dict[str, Any] = {}
    for framework in sorted({str(row["framework"]) for row in operations}):
        operation_slice = [row for row in operations if row["framework"] == framework]
        pair_slice = [row for row in pairs if row["framework"] == framework]
        per_framework[framework] = metric_bundle(
            pair_slice,
            operation_slice,
            ("causal_visible_path", "step0055_visible_path", "multires_recurrence"),
        )
    causal_f1 = metrics["causal_visible_path"]["bcubed"]["f1"]
    recurrence_f1 = metrics["multires_recurrence"]["bcubed"]["f1"]
    adopted = causal_f1 > recurrence_f1 and causal_minus_recurrence["ci95"][0] > 0
    contradicted = causal_minus_recurrence["ci95"][1] <= 0
    summary = {
        "schema": SCHEMA + ".score.v1",
        "status": "complete",
        "mode": inference["mode"],
        "population": {
            "sessions": len({row["session"] for row in operations}),
            "operations": len(operations),
            "pairs": len(pairs),
            "stage_occurrences": len({row["official_stage"] for row in operations}),
            "task_clusters": len({row["task_name"] for row in operations}),
            "frameworks": dict(Counter(row["framework"] for row in operations)),
        },
        "metrics": metrics,
        "bootstrap": {
            "causal_minus_recurrence": causal_minus_recurrence,
            "causal_minus_step0055": causal_minus_step0055,
        },
        "per_framework": per_framework,
        "global_folding_behavior": folding,
        "inference_behavior": {
            key: inference[key]
            for key in (
                "proposed_transition_counts",
                "applied_transition_counts",
                "invariant_applications",
                "affected_sessions",
                "response_sources",
                "exact_phase_like_proposals",
                "session_max_depth",
                "sessions_with_no_depth_decrease",
            )
        },
        "decision": {
            "constructor_adoption": "adopted" if adopted else "not-adopted",
            "branch_disposition": (
                "adopt-and-sync"
                if adopted
                else "close-online-qwen3b-branch"
                if contradicted
                else "close-online-qwen3b-branch-inconclusive"
            ),
            "primary_identity": "complete ordered visible task label path",
            "incumbent": "multires_recurrence",
            "adoption_interval_wholly_positive": causal_minus_recurrence["ci95"][0] > 0,
            "adoption_interval_wholly_nonpositive": contradicted,
        },
        "claim_boundary": (
            "One fixed online policy and session-local flat stage partition only; "
            "no validation of cross-run equivalence, ancestor topology, variable "
            "depth meaning, generated label semantics, root canonicalization, or "
            "the lower phase/action/object/result suffix."
        ),
    }
    if inference["mode"] == "full":
        require(len(operations) == EXPECTED_OPERATIONS, "full scored operations")
        require(len(predictions) == EXPECTED_OPERATIONS, "full prediction coverage")
        require(summary["population"]["sessions"] == EXPECTED_SESSIONS, "full sessions")
        require(summary["population"]["stage_occurrences"] == EXPECTED_STAGES, "full stages")
        require(summary["population"]["task_clusters"] == EXPECTED_TASKS, "full tasks")
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
