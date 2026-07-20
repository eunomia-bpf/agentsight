#!/usr/bin/env python3
"""Infer and score a source-native variable-depth task stack.

``infer`` reads only the public task and trajectory. It maintains an immutable
concrete-task root and asks a fixed local model for one legal stack transition
per source-native agent turn. ``score`` opens human stages only after all stack
paths have been materialized.
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


base = source.base
ALGORITHM_VERSION = "stateful-native-turn-task-stack-v1"
SCHEMA = "agentsight.rq3-stateful-native-turn-task-stack"
EXPECTED_SESSIONS = 405
EXPECTED_OPERATIONS = 20_866
EXPECTED_TURNS = 17_148
EXPECTED_STAGES = 2_948
EXPECTED_TASKS = 251
EXPECTED_FRAMEWORKS = base.EXPECTED_FRAMEWORKS
SEED = 20_260_720
BOOTSTRAP_RESAMPLES = 10_000
LABEL_MAX_CHARS = 64
TASK_CHARS = 6_000
INTENT_CHARS = 2_400
PROGRESS_CHARS = 1_600
ACTION_CHARS = 2_400
RESULT_CHARS = 2_400
OUTPUT_TOKENS = 96
LABEL_PATTERN = re.compile(r"^[a-z][a-z0-9 /+._-]*$")
PREFLIGHT_TERMINUS = (
    "terminus2-DeepSeek__DeepSeek-V3.2-organization-json-generator-30fb23d8"
)

SYSTEM_PROMPT = """Maintain the active TASK stack for one AI agent. The
immutable concrete task is the root and is never removed. Persistent frames are
only nested task goals or responsibilities with a completion condition that can
span multiple agent turns. A phase, strategy, semantic action, tool, command,
file, path, object, status, result, inspect, edit, test, retry, or one atomic
operation is evidence about a task, not by itself a task frame. A change in
such evidence does not justify a new frame.

Use stay when the turn advances, inspects, edits, tests, retries, or checks the
current leaf goal. Use push only when the turn begins a genuinely nested goal.
Use pop to resume an existing ancestor after completing or abandoning the
current suffix. Use replace to begin a sibling after completing or abandoning
the suffix. Add at most one frame per turn. A new label is a concise lowercase
English task-goal phrase, not a tool/action/file/status description. Return only
the required JSON."""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    infer = commands.add_parser("infer")
    infer.add_argument("mode", choices=("preflight", "full"))
    infer.add_argument("--target-operations", type=Path, required=True)
    infer.add_argument("--raw-root", type=Path, required=True)
    infer.add_argument("--llama-url", required=True)
    infer.add_argument("--workers", type=int, default=4)
    infer.add_argument("--timeout-seconds", type=int, default=600)
    infer.add_argument("--out", type=Path, required=True)

    score = commands.add_parser("score")
    score.add_argument("--target-operations", type=Path, required=True)
    score.add_argument("--predictions", type=Path, required=True)
    score.add_argument("--inference-summary", type=Path, required=True)
    score.add_argument("--verified-manifest", type=Path, required=True)
    score.add_argument("--multires-assignments", type=Path, required=True)
    score.add_argument("--prior-stateful-assignments", type=Path, required=True)
    score.add_argument("--out", type=Path, required=True)
    return parser.parse_args()


def absolute(path: Path) -> Path:
    return path if path.is_absolute() else ROOT / path


def relative(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return str(path.resolve())


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def write_json(path: Path, value: Any) -> None:
    source.write_json(path, value)


def write_json_atomic(path: Path, value: Any) -> None:
    source.write_json_atomic(path, value)


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    source.write_jsonl(path, rows)


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
    targets = " | ".join(f'"{value}"' for value in range(depth))
    pop = (
        'pop ::= "{\\\"transition\\\":\\\"pop\\\",'
        '\\\"target_depth\\\":" target "}"\n'
    )
    replace = (
        'replace ::= "{\\\"transition\\\":\\\"replace\\\",'
        '\\\"target_depth\\\":" target ",\\\"label\\\":" label "}"\n'
    )
    return (
        "root ::= stay | push | pop | replace\n"
        + stay
        + push
        + pop
        + replace
        + f"target ::= {targets}\n"
        + label
    )


def parse_transition(raw: str, depth: int) -> dict[str, Any]:
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as error:
        raise RuntimeError(f"model output is not JSON: {raw!r}") from error
    require(isinstance(value, dict), "transition is not an object")
    kind = value.get("transition")
    if kind == "stay":
        require(set(value) == {"transition"}, "stay keys")
    elif kind == "push":
        require(set(value) == {"transition", "label"}, "push keys")
    elif kind == "pop":
        require(set(value) == {"transition", "target_depth"}, "pop keys")
        require(depth > 0, "pop at root")
    elif kind == "replace":
        require(
            set(value) == {"transition", "target_depth", "label"},
            "replace keys",
        )
        require(depth > 0, "replace at root")
    else:
        raise RuntimeError(f"unknown transition: {kind!r}")
    if "target_depth" in value:
        target = value["target_depth"]
        require(type(target) is int and 0 <= target < depth, "target depth")
    if "label" in value:
        label = value["label"]
        require(type(label) is str and 0 < len(label) <= LABEL_MAX_CHARS, "label length")
        require(LABEL_PATTERN.fullmatch(label) is not None, "label syntax")
    return value


def apply_transition(
    session: str,
    stack: list[dict[str, str]],
    transition: dict[str, Any],
    next_frame: int,
) -> tuple[list[dict[str, str]], int]:
    kind = transition["transition"]
    if kind == "stay":
        output = [dict(frame) for frame in stack]
    elif kind == "push":
        output = [dict(frame) for frame in stack]
        output.append(
            {
                "instance": f"{session}:frame-{next_frame:05d}",
                "label": str(transition["label"]),
            }
        )
        next_frame += 1
    elif kind == "pop":
        output = [dict(frame) for frame in stack[: int(transition["target_depth"])]]
    else:
        require(kind == "replace", "apply transition kind")
        output = [dict(frame) for frame in stack[: int(transition["target_depth"])]]
        output.append(
            {
                "instance": f"{session}:frame-{next_frame:05d}",
                "label": str(transition["label"]),
            }
        )
        next_frame += 1
    return output, next_frame


def unique_text(rows: list[dict[str, Any]], key: str) -> str:
    values: list[str] = []
    for row in rows:
        value = str(row.get(key) or "").strip()
        if value and value not in values:
            values.append(value)
    return "\n---\n".join(values)


def group_turns(operations: list[dict[str, Any]]) -> list[dict[str, Any]]:
    turns: list[dict[str, Any]] = []
    seen: set[str] = set()
    for operation in operations:
        turn_id = str(operation.get("turn_id") or "")
        require(bool(turn_id), "missing native turn id")
        if not turns or turns[-1]["source_turn_id"] != turn_id:
            require(turn_id not in seen, "noncontiguous native turn id")
            seen.add(turn_id)
            turns.append(
                {
                    "turn_index": len(turns),
                    "source_turn_id": turn_id,
                    "operations": [],
                }
            )
        turns[-1]["operations"].append(operation)
    require(
        sum(len(turn["operations"]) for turn in turns) == len(operations),
        "native turn coverage",
    )
    return turns


def root_label(task: str) -> str:
    line = next((line.strip() for line in task.splitlines() if line.strip()), "concrete task")
    return base.clip_text(line, 120)


def prompt_for(
    task: str,
    root: str,
    stack: list[dict[str, str]],
    turn: dict[str, Any],
    preceding_result: str,
) -> str:
    operations = turn["operations"]
    visible = {
        "native_intent": base.clip_text(unique_text(operations, "intent"), INTENT_CHARS),
        "native_progress": base.clip_text(unique_text(operations, "progress"), PROGRESS_CHARS),
        "planned_actions": base.clip_text(unique_text(operations, "action"), ACTION_CHARS),
        "preceding_result": base.clip_text(preceding_result, RESULT_CHARS),
    }
    active = [
        {"depth": 0, "kind": "concrete_task", "label": root},
        *[
            {"depth": index + 1, "kind": "subtask", "label": frame["label"]}
            for index, frame in enumerate(stack)
        ],
    ]
    return (
        "CONCRETE TASK\n"
        + base.clip_text(task, TASK_CHARS)
        + "\n\nACTIVE TASK STACK\n"
        + json.dumps(active, ensure_ascii=False, separators=(",", ":"))
        + "\n\nNEXT SOURCE-NATIVE AGENT TURN\n"
        + json.dumps(visible, ensure_ascii=False, separators=(",", ":"))
    )


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
    turns = group_turns(material["operations"])
    path = cache_dir / source.cache_name(session)
    if path.is_file():
        result = json.loads(path.read_text(encoding="utf-8"))
        require(result.get("algorithm_version") == ALGORITHM_VERSION, "cache version")
        require(result.get("session") == session, "cache session")
        require(result.get("archive_sha256") == material["archive_sha256"], "cache archive")
        require(result.get("adapter") == material["adapter"], "cache adapter")
        require(result.get("model") == base.MODEL, "cache model")
        require(result.get("model_sha256") == base.MODEL_SHA256, "cache model hash")
        require(result.get("seed") == SEED, "cache seed")
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
            "root_label": root_label(material["task"]),
            "input_turns": len(turns),
            "input_operations": len(material["operations"]),
            "transitions": [],
        }
        write_json_atomic(path, result)

    cached = result["transitions"]
    require(len(cached) <= len(turns), "cache longer than native turns")
    stack: list[dict[str, str]] = []
    next_frame = 0
    preceding_result = ""
    for index, turn in enumerate(turns):
        grammar = grammar_for_depth(len(stack))
        user = prompt_for(
            material["task"], result["root_label"], stack, turn, preceding_result
        )
        digest = request_hash(user, grammar)
        stack_before = [dict(frame) for frame in stack]
        if index < len(cached):
            record = cached[index]
            require(int(record["turn_index"]) == index, "cached turn order")
            require(record["request_sha256"] == digest, "cached request drift")
            transition = parse_transition(str(record["raw_response"]), len(stack))
            updated, next_frame = apply_transition(
                session, stack, transition, next_frame
            )
            require(record["stack_before"] == stack_before, "cached stack before")
            require(record["stack_after"] == updated, "cached stack after")
            stack = updated
        else:
            raw, response, attempts = base.call_model(
                llama_url,
                SYSTEM_PROMPT,
                user,
                grammar,
                timeout_seconds,
                OUTPUT_TOKENS,
            )
            transition = parse_transition(raw, len(stack))
            stack, next_frame = apply_transition(
                session, stack, transition, next_frame
            )
            usage = response.get("usage") or {}
            record = {
                "turn_index": index,
                "source_turn_id": turn["source_turn_id"],
                "step_ids": [int(row["step"]) for row in turn["operations"]],
                "request_sha256": digest,
                "prompt": user,
                "raw_response": raw,
                "transition": transition,
                "stack_before": stack_before,
                "stack_after": [dict(frame) for frame in stack],
                "active_leaf_instance": (
                    stack[-1]["instance"] if stack else f"{session}:task-root"
                ),
                "active_leaf_label": (
                    stack[-1]["label"] if stack else result["root_label"]
                ),
                "usage": usage,
                "attempts": attempts,
            }
            cached.append(record)
            write_json_atomic(path, result)
        preceding_result = unique_text(turn["operations"], "result")

    require(len(cached) == len(turns), "transition coverage")
    predictions = []
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


def preflight_sessions(grouped: dict[str, list[dict[str, Any]]]) -> list[str]:
    categories: dict[str, list[tuple[int, str]]] = defaultdict(list)
    for session, rows in grouped.items():
        framework = base.framework_for_session(session)
        if framework == "OpenHands":
            layout = (
                "openhands-maximal-visible-action-context"
                if "#message-" in rows[0]["source_ref"]
                else "openhands-agent-actions"
            )
        elif framework == "mini-SWE-agent":
            layout = "miniswe-message-trajectory"
        elif framework == "SWE-agent":
            layout = "sweagent-trajectory-elements"
        else:
            layout = "terminus2-commands-txt-strings"
        categories[layout].append((len(rows), session))
    require(set(categories) == source.EXPECTED_LAYOUTS, "preflight layout categories")
    selected = []
    for layout in sorted(categories):
        if layout == "terminus2-commands-txt-strings":
            require(PREFLIGHT_TERMINUS in grouped, "fixed multi-command preflight")
            selected.append(PREFLIGHT_TERMINUS)
        else:
            selected.append(min(categories[layout])[1])
    return sorted(selected)


def run_inference(args: argparse.Namespace) -> None:
    started = time.monotonic()
    target_path = absolute(args.target_operations)
    raw_root = absolute(args.raw_root)
    out_dir = absolute(args.out)
    grouped = base.load_visible_operations(target_path)
    require(len(grouped) == EXPECTED_SESSIONS, "target session count")
    require(sum(map(len, grouped.values())) == EXPECTED_OPERATIONS, "target operation count")
    selected = preflight_sessions(grouped) if args.mode == "preflight" else sorted(grouped)
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
    write_jsonl(out_dir / "predictions.jsonl", predictions)
    depths = [int(row["task_depth"]) for row in predictions]
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
        "transition_counts": dict(
            Counter(row["transition"]["transition"] for row in transitions)
        ),
        "new_frame_rate": sum(
            row["transition"]["transition"] in {"push", "replace"}
            for row in transitions
        )
        / len(transitions),
        "depth_including_root": {
            "minimum": min(depths),
            "maximum": max(depths),
            "mean": sum(depths) / len(depths),
            "counts": dict(sorted(Counter(depths).items())),
        },
        "intent_operations": sum(row["intent_available"] for row in predictions),
        "progress_operations": sum(row["progress_available"] for row in predictions),
        "result_operations": sum(row["result_available"] for row in predictions),
        "model_usage": dict(usage),
        "wall_seconds": time.monotonic() - started,
        "predictions": relative(out_dir / "predictions.jsonl"),
        "isolation": {
            "official_manifest_opened": False,
            "official_stages_opened": False,
            "visible_fields": [
                "concrete task",
                "complete active task labels",
                "native intent",
                "native progress",
                "planned source action",
                "preceding turn result",
            ],
            "current_turn_result_visible": False,
            "agent_model_session_status_visible": False,
            "active_stack_truncated": False,
            "all_operations_retained": True,
        },
    }
    write_json(out_dir / "inference-summary.json", summary)
    print(json.dumps(summary, sort_keys=True), flush=True)


def load_predictions(path: Path) -> dict[tuple[str, int], dict[str, Any]]:
    rows: dict[tuple[str, int], dict[str, Any]] = {}
    with path.open(encoding="utf-8") as stream:
        for line_number, line in enumerate(stream, 1):
            row = json.loads(line)
            key = (str(row["session"]), int(row["step_id"]))
            require(key not in rows, f"duplicate prediction line {line_number}")
            require(bool(row.get("active_leaf_instance")), "missing active leaf")
            rows[key] = row
    return rows


def load_prior_stateful(path: Path) -> dict[tuple[str, int], str]:
    rows: dict[tuple[str, int], str] = {}
    with path.open(encoding="utf-8") as stream:
        for line_number, line in enumerate(stream, 1):
            row = json.loads(line)
            key = (str(row["session"]), int(row["step_id"]))
            require(key not in rows, f"duplicate prior stateful line {line_number}")
            rows[key] = str(row["raw_semantic_stack"])
    return rows


def score_rows(
    grouped: dict[str, list[dict[str, Any]]],
    selected: list[str],
    predictions: dict[tuple[str, int], dict[str, Any]],
    baselines: dict[tuple[str, int], dict[str, str]],
    prior: dict[tuple[str, int], str],
    official: dict[tuple[str, int], str],
    frameworks: dict[str, str],
    tasks: dict[str, str],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    operations = []
    pairs = []
    methods = (
        "candidate",
        "multires_recurrence",
        "prior_stateful_raw",
        "native_turn",
        "one_span",
        "phase",
        "raw_action",
    )
    for session in selected:
        previous = None
        for row in grouped[session]:
            key = (session, int(row["step_id"]))
            require(key in predictions and key in baselines and key in prior, "score input coverage")
            prediction = predictions[key]
            operation = {
                "session": session,
                "framework": frameworks[session],
                "task_name": tasks[session],
                "step_id": int(row["step_id"]),
                "official_stage": official[key],
                "candidate": str(prediction["active_leaf_instance"]),
                "candidate_label": str(prediction["active_leaf_label"]),
                "candidate_depth": int(prediction["task_depth"]),
                "native_turn": str(prediction["turn_instance"]),
                "prior_stateful_raw": prior[key],
                **baselines[key],
            }
            operations.append(operation)
            if previous is not None:
                pair = {
                    "session": session,
                    "framework": frameworks[session],
                    "task_name": tasks[session],
                    "position": int(row["step_id"]) - 1,
                    "official_boundary": previous["official_stage"]
                    != operation["official_stage"],
                }
                for method in methods:
                    pair[method] = previous[method] != operation[method]
                pairs.append(pair)
            previous = operation
    return pairs, operations


def metric_bundle(
    pairs: list[dict[str, Any]], operations: list[dict[str, Any]], methods: Iterable[str]
) -> dict[str, Any]:
    return {
        method: {
            "bcubed": base.bcubed(operations, method),
            "span": base.span_metrics(operations, method),
            "boundary": base.boundary_metrics(pairs, method),
        }
        for method in methods
    }


def result_report(summary: dict[str, Any]) -> str:
    lines = [
        "# Stateful Native-Turn Task Stack — Result",
        "",
        f"- mode: {summary['mode']}",
        f"- status: {summary['status']}",
        f"- registered interpretation: **{summary['registered_interpretation']}**",
        "",
        "## Standard metrics",
        "",
        "| Method | B³ P | B³ R | B³ F1 | Span F1 | Boundary F1 |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for method, values in summary["metrics"].items():
        lines.append(
            f"| {method} | {values['bcubed']['precision']:.6f} | "
            f"{values['bcubed']['recall']:.6f} | {values['bcubed']['f1']:.6f} | "
            f"{values['span']['f1']:.6f} | {values['boundary']['f1']:.6f} |"
        )
    lines.extend(
        [
            "",
            "## Claim boundary",
            "",
            summary["claim_boundary"],
            "",
        ]
    )
    return "\n".join(lines)


def run_score(args: argparse.Namespace) -> None:
    target_path = absolute(args.target_operations)
    prediction_path = absolute(args.predictions)
    inference_path = absolute(args.inference_summary)
    manifest_path = absolute(args.verified_manifest)
    baseline_path = absolute(args.multires_assignments)
    prior_path = absolute(args.prior_stateful_assignments)
    out_dir = absolute(args.out)
    for path in (
        target_path,
        prediction_path,
        inference_path,
        manifest_path,
        baseline_path,
        prior_path,
    ):
        require(path.is_file(), f"missing score input: {path}")
    inference = json.loads(inference_path.read_text(encoding="utf-8"))
    require(inference.get("status") == "complete", "inference incomplete")
    mode = str(inference["mode"])
    grouped = base.load_visible_operations(target_path)
    predictions = load_predictions(prediction_path)
    selected = sorted({session for session, _ in predictions})
    expected = {
        (session, int(row["step_id"]))
        for session in selected
        for row in grouped[session]
    }
    require(set(predictions) == expected, "prediction coverage")
    baselines = base.load_baselines(baseline_path)
    prior = load_prior_stateful(prior_path)
    require(expected <= set(baselines) and expected <= set(prior), "baseline coverage")

    # Human stages are opened only after all source-only assignments exist.
    official, frameworks, tasks = base.load_stages_after_prediction(
        manifest_path, grouped, selected
    )
    pairs, operations = score_rows(
        grouped, selected, predictions, baselines, prior, official, frameworks, tasks
    )
    methods = (
        "candidate",
        "multires_recurrence",
        "prior_stateful_raw",
        "native_turn",
        "one_span",
        "phase",
        "raw_action",
    )
    metrics = metric_bundle(pairs, operations, methods)
    out_dir.mkdir(parents=True, exist_ok=True)
    bootstrap = source.bcubed_task_bootstrap(
        operations,
        "candidate",
        "multires_recurrence",
        out_dir / "bootstrap-candidate-minus-multires.jsonl",
    )
    per_framework = {}
    for framework in sorted(set(frameworks.values())):
        framework_operations = [row for row in operations if row["framework"] == framework]
        framework_pairs = [row for row in pairs if row["framework"] == framework]
        per_framework[framework] = metric_bundle(
            framework_pairs,
            framework_operations,
            ("candidate", "multires_recurrence"),
        )
    candidate_f1 = metrics["candidate"]["bcubed"]["f1"]
    incumbent_f1 = metrics["multires_recurrence"]["bcubed"]["f1"]
    supported = candidate_f1 > incumbent_f1 and bootstrap["ci95"][0] > 0
    contradicted = bootstrap["ci95"][1] <= 0
    interpretation = (
        "diagnostic-preflight"
        if mode == "preflight"
        else "supported-and-adopted"
        if supported
        else "contradicted-not-adopted"
        if contradicted
        else "inconclusive-not-adopted"
    )
    summary = {
        "schema": SCHEMA + ".score.v1",
        "mode": mode,
        "status": "complete",
        "registered_interpretation": interpretation,
        "population": {
            "sessions": len(selected),
            "operations": len(operations),
            "pairs": len(pairs),
            "official_stages": len(set(official.values())),
            "tasks": len(set(tasks.values())),
            "frameworks": dict(Counter(frameworks.values())),
            "turns": int(inference["turns"]),
        },
        "metrics": metrics,
        "bootstrap": bootstrap,
        "per_framework": per_framework,
        "decision": {
            "primary_metric": "ordinary operation-level B-cubed F1",
            "incumbent": "multires_recurrence",
            "candidate_point_higher": candidate_f1 > incumbent_f1,
            "candidate_interval_wholly_positive": bootstrap["ci95"][0] > 0,
            "candidate_interval_wholly_nonpositive": contradicted,
            "per_framework_results_are_diagnostic_not_vetoes": True,
        },
        "claim_boundary": (
            "Flat CodeTrace workflow stages test only the active task-leaf instance "
            "partition. They do not validate ancestor topology, variable depth, nested "
            "label meaning, or the transient phase/action/object/result suffix."
        ),
    }
    if mode == "full":
        require(len(selected) == EXPECTED_SESSIONS, "full scored sessions")
        require(len(operations) == EXPECTED_OPERATIONS, "full scored operations")
        require(len(pairs) == EXPECTED_OPERATIONS - EXPECTED_SESSIONS, "full pairs")
        require(len(set(official.values())) == EXPECTED_STAGES, "full official stages")
        require(len(set(tasks.values())) == EXPECTED_TASKS, "full task count")
    write_jsonl(out_dir / "operation-score-rows.jsonl", operations)
    write_jsonl(out_dir / "boundary-score-rows.jsonl", pairs)
    write_json(out_dir / "summary.json", summary)
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
