#!/usr/bin/env python3
"""Evaluate index-free task-responsibility alignment on CodeTraceBench.

Inference reuses the fixed Step0050 task plans and source-only causal evidence.
The model sees and emits responsibility text, never a numeric plan index.  The
separate scorer opens human stages only after complete predictions exist and
reuses the registered standard scorers and completed comparator assignments.
"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import json
from pathlib import Path
import sys
import time
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "script"))

import rq3_task_rooted_stage_alignment_eval as base  # noqa: E402


ALGORITHM_VERSION = "index-free-responsibility-alignment-v1"
SCHEMA = "agentsight.rq3-index-free-responsibility-alignment"
EXPECTED_SESSIONS = 405
EXPECTED_OPERATIONS = 20_866
EXPECTED_STAGES = 2_948
EXPECTED_TASKS = 251
EXPECTED_FRAMEWORKS = base.EXPECTED_FRAMEWORKS
MAX_REQUEST_TOKENS = base.MAX_REQUEST_TOKENS
CAUSAL_OUTPUT_TOKENS = base.CAUSAL_OUTPUT_TOKENS
SYSTEM_PROMPT = """Maintain one active workflow responsibility while reading an
agent trajectory causally. Decide whether the current operation continues the
active responsibility or switches to a different exact responsibility from the
retained task plan. The displayed plan order is arbitrary, not a workflow
sequence: never choose a responsibility because it is the next list item. Stay
by default when the operation advances the active concrete work. Switch only
when the concrete responsibility changes. A responsibility can be revisited
after other work. Return only the required JSON and copy a switch label exactly."""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    infer = subparsers.add_parser("infer")
    infer.add_argument("mode", choices=("preflight", "full"))
    infer.add_argument("--source-sessions", type=Path, required=True)
    infer.add_argument("--numeric-predictions", type=Path, required=True)
    infer.add_argument("--llama-url", required=True)
    infer.add_argument("--workers", type=int, default=4)
    infer.add_argument("--timeout-seconds", type=int, default=600)
    infer.add_argument("--out", type=Path, required=True)

    score = subparsers.add_parser("score")
    score.add_argument("--target-operations", type=Path, required=True)
    score.add_argument("--predictions", type=Path, required=True)
    score.add_argument("--numeric-predictions", type=Path, required=True)
    score.add_argument("--verified-manifest", type=Path, required=True)
    score.add_argument("--multires-assignments", type=Path, required=True)
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


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def write_json_atomic(path: Path, payload: Any) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    write_json(temporary, payload)
    temporary.replace(path)


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as output:
        for row in rows:
            output.write(json.dumps(row, sort_keys=True, ensure_ascii=False) + "\n")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        while chunk := source.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def cache_name(session: str) -> str:
    return hashlib.sha256(session.encode()).hexdigest()[:24] + ".json"


def load_source_sessions(path: Path) -> dict[str, dict[str, Any]]:
    source_dir = absolute(path)
    require(source_dir.is_dir(), f"missing source session directory: {source_dir}")
    sessions: dict[str, dict[str, Any]] = {}
    for source_path in sorted(source_dir.glob("*.json")):
        row = json.loads(source_path.read_text(encoding="utf-8"))
        require(
            row.get("algorithm_version") == base.ALGORITHM_VERSION,
            f"unexpected source algorithm: {source_path}",
        )
        session = str(row["session"])
        require(session not in sessions, f"duplicate source session: {session}")
        require(bool(row.get("plan")), f"empty retained plan: {session}")
        require(
            len(row.get("transitions") or []) > 0,
            f"empty retained transitions: {session}",
        )
        require(
            len(row["transitions"])
            == len({int(transition["step"]) for transition in row["transitions"]}),
            f"duplicate source step: {session}",
        )
        row["_source_path"] = str(source_path)
        row["_source_sha256"] = sha256_file(source_path)
        sessions[session] = row
    require(len(sessions) == EXPECTED_SESSIONS, "unexpected retained session count")
    require(
        sum(len(row["transitions"]) for row in sessions.values())
        == EXPECTED_OPERATIONS,
        "unexpected retained operation count",
    )
    require(
        {str(row["framework"]) for row in sessions.values()} == EXPECTED_FRAMEWORKS,
        "unexpected retained framework set",
    )
    return sessions


def preflight_selection(sessions: dict[str, dict[str, Any]]) -> list[str]:
    selected = []
    for framework in sorted(EXPECTED_FRAMEWORKS):
        candidates = [
            row for row in sessions.values() if str(row["framework"]) == framework
        ]
        require(bool(candidates), f"no source session for {framework}")
        chosen = max(
            candidates,
            key=lambda row: (
                max(
                    int(transition["candidate"]["request_tokens"])
                    for transition in row["transitions"]
                ),
                len(row["transitions"]),
                str(row["session"]),
            ),
        )
        selected.append(str(chosen["session"]))
    return sorted(selected)


def gbnf_terminal(value: str) -> str:
    """Return a GBNF terminal whose matched bytes equal ``value``."""
    return json.dumps(value, ensure_ascii=True)


def response_grammar(plan: list[str], active: str | None) -> str:
    require(plan and len(plan) == len(set(plan)), "plan must be nonempty and unique")
    allowed = [label for label in plan if label != active]
    label_rule = " | ".join(
        gbnf_terminal(json.dumps(label, ensure_ascii=False)) for label in allowed
    )
    switch_rule = (
        'switch ::= "{\\\"decision\\\":\\\"switch\\\",\\\"responsibility\\\":" label "}"\n'
        f"label ::= {label_rule}\n"
        if allowed
        else ""
    )
    if active is None:
        require(bool(allowed), "first operation has no switch target")
        return "root ::= switch\n" + switch_rule
    stay_rule = (
        'stay ::= "{\\\"decision\\\":\\\"stay\\\",\\\"responsibility\\\":null}"\n'
    )
    root = "root ::= stay | switch\n" if allowed else "root ::= stay\n"
    return root + stay_rule + switch_rule


def prompt(shared_evidence: str, plan: list[str], active: str | None) -> str:
    plan_text = "\n".join(f"- {label}" for label in plan)
    return (
        f"{shared_evidence}\n\n"
        "ACTIVE RESPONSIBILITY\n"
        f"{active if active is not None else 'none'}\n\n"
        "RETAINED RESPONSIBILITIES (unordered semantic choices)\n"
        f"{plan_text}"
    )


def parse_response(
    raw: str,
    plan: list[str],
    active: str | None,
) -> tuple[str, str]:
    value = json.loads(raw)
    require(
        isinstance(value, dict) and set(value) == {"decision", "responsibility"},
        "unexpected response keys",
    )
    decision = value["decision"]
    responsibility = value["responsibility"]
    require(decision in {"stay", "switch"}, "unexpected decision")
    if active is None:
        require(decision == "switch", "first operation must switch")
    if decision == "stay":
        require(active is not None, "cannot stay without active responsibility")
        require(responsibility is None, "stay responsibility must be null")
        return decision, active
    require(isinstance(responsibility, str), "switch responsibility must be text")
    require(responsibility in plan, "switch responsibility is not retained exact text")
    require(responsibility != active, "switch must change responsibility")
    return decision, responsibility


def infer_session(
    source: dict[str, Any],
    llama_url: str,
    timeout_seconds: int,
    cache_dir: Path,
) -> dict[str, Any]:
    session = str(source["session"])
    cache_path = cache_dir / cache_name(session)
    if cache_path.is_file():
        result = json.loads(cache_path.read_text(encoding="utf-8"))
        require(result.get("algorithm_version") == ALGORITHM_VERSION, "cache version")
        require(result.get("session") == session, "cache session")
        require(result.get("model_sha256") == base.MODEL_SHA256, "cache model")
        require(result.get("source_cache_sha256") == source["_source_sha256"], "cache source")
    else:
        result = {
            "schema": SCHEMA + ".session.v1",
            "algorithm_version": ALGORITHM_VERSION,
            "session": session,
            "framework": source["framework"],
            "model": base.MODEL,
            "model_sha256": base.MODEL_SHA256,
            "seed": base.SEED,
            "source_cache": relative(Path(source["_source_path"])),
            "source_cache_sha256": source["_source_sha256"],
            "plan": list(source["plan"]),
            "transitions": [],
        }
        write_json_atomic(cache_path, result)

    plan = list(result["plan"])
    transitions = result["transitions"]
    require(
        len(transitions) <= len(source["transitions"]),
        f"{session}: excessive cached transitions",
    )
    active = str(transitions[-1]["active_responsibility"]) if transitions else None
    stage_instance = int(transitions[-1]["stage_instance"]) if transitions else -1

    for operation_number in range(len(transitions), len(source["transitions"])):
        source_transition = source["transitions"][operation_number]
        shared_evidence = str(source_transition["projection"]["shared_evidence"])
        user = prompt(shared_evidence, plan, active)
        raw, response, attempts = base.call_model(
            llama_url,
            SYSTEM_PROMPT,
            user,
            response_grammar(plan, active),
            timeout_seconds,
            CAUSAL_OUTPUT_TOKENS,
        )
        decision, next_active = parse_response(raw, plan, active)
        if decision == "switch":
            stage_instance += 1
        active = next_active
        usage = response.get("usage") or {}
        transition = {
            "operation_number": operation_number,
            "step": int(source_transition["step"]),
            "decision": decision,
            "active_responsibility": active,
            "stage_instance": stage_instance,
            "system": SYSTEM_PROMPT,
            "user": user,
            "shared_evidence_sha256": hashlib.sha256(
                shared_evidence.encode()
            ).hexdigest(),
            "request_tokens": int(usage.get("prompt_tokens", 0)),
            "raw": raw,
            "usage": usage,
            "attempts": attempts,
        }
        require(
            0 < transition["request_tokens"] <= MAX_REQUEST_TOKENS,
            f"{session}: request token limit",
        )
        transitions.append(transition)
        write_json_atomic(cache_path, result)

    require(
        len(result["transitions"]) == len(source["transitions"]),
        f"{session}: incomplete transitions",
    )
    return result


def usage_totals(results: dict[str, dict[str, Any]]) -> Counter[str]:
    usage: Counter[str] = Counter()
    for result in results.values():
        for transition in result["transitions"]:
            for key, value in (transition.get("usage") or {}).items():
                if isinstance(value, int):
                    usage[key] += value
    return usage


def materialize_predictions(
    selected: list[str],
    sources: dict[str, dict[str, Any]],
    results: dict[str, dict[str, Any]],
    numeric: dict[tuple[str, int], dict[str, Any]],
) -> list[dict[str, Any]]:
    rows = []
    for session in selected:
        source = sources[session]
        result = results[session]
        plan = list(result["plan"])
        semantic_by_label = dict(zip(source["plan"], source["plan_semantic"]))
        for source_transition, transition in zip(
            source["transitions"], result["transitions"], strict=True
        ):
            step = int(transition["step"])
            key = (session, step)
            require(key in numeric, f"missing numeric prediction: {key}")
            old = dict(numeric[key])
            require(
                hashlib.sha256(
                    str(source_transition["projection"]["shared_evidence"]).encode()
                ).hexdigest()
                == transition["shared_evidence_sha256"],
                f"source evidence drift: {key}",
            )
            label = str(transition["active_responsibility"])
            row = {
                **old,
                "candidate_index": plan.index(label),
                "candidate_label": label,
                "candidate_label_semantic": bool(semantic_by_label[label]),
                "candidate_decision": transition["decision"],
                "candidate_stage_instance": int(transition["stage_instance"]),
                "candidate_interface": ALGORITHM_VERSION,
            }
            rows.append(row)
    rows.sort(key=lambda row: (str(row["session"]), int(row["step_id"])))
    return rows


def run_inference(args: argparse.Namespace) -> None:
    started = time.monotonic()
    source_sessions = load_source_sessions(args.source_sessions)
    numeric_path = absolute(args.numeric_predictions)
    require(numeric_path.is_file(), f"missing numeric predictions: {numeric_path}")
    numeric = base.load_prediction_rows(numeric_path)
    require(len(numeric) == EXPECTED_OPERATIONS, "unexpected numeric prediction count")
    selected = (
        preflight_selection(source_sessions)
        if args.mode == "preflight"
        else sorted(source_sessions)
    )
    out_dir = absolute(args.out)
    cache_dir = out_dir / "sessions"
    cache_dir.mkdir(parents=True, exist_ok=True)
    results: dict[str, dict[str, Any]] = {}

    def infer(session: str) -> dict[str, Any]:
        return infer_session(
            source_sessions[session],
            args.llama_url,
            args.timeout_seconds,
            cache_dir,
        )

    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = {executor.submit(infer, session): session for session in selected}
        for future in as_completed(futures):
            session = futures[future]
            results[session] = future.result()
            print(f"inferred {len(results)}/{len(selected)} {session}", flush=True)

    predictions = materialize_predictions(
        selected, source_sessions, results, numeric
    )
    expected_operations = sum(
        len(source_sessions[session]["transitions"]) for session in selected
    )
    require(len(predictions) == expected_operations, "prediction coverage")
    require(
        len({(row["session"], row["step_id"]) for row in predictions})
        == expected_operations,
        "prediction uniqueness",
    )
    request_tokens = [
        int(transition["request_tokens"])
        for result in results.values()
        for transition in result["transitions"]
    ]
    switches = sum(
        transition["decision"] == "switch"
        for result in results.values()
        for transition in result["transitions"]
    )
    used = sum(
        len({transition["active_responsibility"] for transition in result["transitions"]})
        for result in results.values()
    )
    plan_items = sum(len(result["plan"]) for result in results.values())
    write_jsonl(out_dir / "predictions.jsonl", predictions)
    summary = {
        "schema": SCHEMA + ".inference.v1",
        "algorithm_version": ALGORITHM_VERSION,
        "status": "complete",
        "mode": args.mode,
        "model": base.MODEL,
        "model_sha256": base.MODEL_SHA256,
        "seed": base.SEED,
        "sessions": len(selected),
        "operations": len(predictions),
        "selected_sessions": selected,
        "model_calls": len(predictions),
        "request_token_max": max(request_tokens),
        "switches_including_first": switches,
        "adjacent_boundary_rate": (switches - len(selected))
        / max(1, len(predictions) - len(selected)),
        "responsibility_types_used": used,
        "responsibility_types_available": plan_items,
        "model_usage": dict(usage_totals(results)),
        "wall_seconds": time.monotonic() - started,
        "predictions": relative(out_dir / "predictions.jsonl"),
        "isolation": {
            "official_manifest_opened": False,
            "official_stages_opened": False,
            "reused_source_evidence_byte_hash_checked": True,
            "model_saw_numeric_plan_index": False,
            "model_emitted_numeric_plan_index": False,
            "all_operations_retained": True,
        },
    }
    if args.mode == "full":
        require(summary["sessions"] == EXPECTED_SESSIONS, "full session count")
        require(summary["operations"] == EXPECTED_OPERATIONS, "full operation count")
    write_json(out_dir / "inference-summary.json", summary)
    print(json.dumps(summary, sort_keys=True), flush=True)


def add_numeric_candidate(
    operations: list[dict[str, Any]],
    pairs: list[dict[str, Any]],
    numeric: dict[tuple[str, int], dict[str, Any]],
) -> None:
    by_key: dict[tuple[str, int], str] = {}
    previous_session = None
    previous_index = None
    instance = -1
    for operation in operations:
        session = str(operation["session"])
        step = int(operation["step_id"])
        if session != previous_session:
            previous_session = session
            previous_index = None
            instance = -1
        index = int(numeric[(session, step)]["candidate_index"])
        if index != previous_index:
            instance += 1
            previous_index = index
        value = f"{session}:numeric-run-{instance:04d}"
        operation["numeric_candidate"] = value
        by_key[(session, step)] = value
    for pair in pairs:
        session = str(pair["session"])
        left = int(pair["position"])
        right = left + 1
        pair["numeric_candidate"] = by_key[(session, left)] != by_key[(session, right)]


def score_report(summary: dict[str, Any]) -> str:
    lines = [
        "# Index-Free Responsibility Alignment — Complete Result",
        "",
        f"- status: {summary['status']}",
        f"- registered interpretation: **{summary['registered_interpretation']}**",
        "- evidence status: post-hoc development on reused CodeTraceBench trajectories",
        "",
        "## Standard Metrics",
        "",
        "| Method | Span P | Span R | Span F1 | B³ F1 | Boundary F1 |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for method, metric in summary["metrics"].items():
        lines.append(
            f"| {method} | {metric['span']['precision']:.6f} | "
            f"{metric['span']['recall']:.6f} | {metric['span']['f1']:.6f} | "
            f"{metric['bcubed']['f1']:.6f} | {metric['boundary']['f1']:.6f} |"
        )
    lines.extend(["", "## Paired Task-Cluster Bootstrap", ""])
    for name, result in summary["bootstrap"].items():
        lines.append(
            f"- candidate minus {name}: mean {result['mean_delta']:.6f}, "
            f"95% CI [{result['ci95'][0]:.6f}, {result['ci95'][1]:.6f}], "
            f"positive fraction {result['positive_fraction']:.4f}"
        )
    lines.extend(
        [
            "",
            "## Interpretation Boundary",
            "",
            "Adoption is decided only against both recurrence comparators. "
            "The numeric comparison diagnoses the complete interface bundle, "
            "not numeric tokens alone. This experiment scores flat unlabeled "
            "workflow-stage fidelity and cannot validate generated names, nested "
            "subtasks, or the complete task-semantic hierarchy.",
        ]
    )
    return "\n".join(lines) + "\n"


def run_scoring(args: argparse.Namespace) -> None:
    target_path = absolute(args.target_operations)
    prediction_input = absolute(args.predictions)
    numeric_path = absolute(args.numeric_predictions)
    manifest_path = absolute(args.verified_manifest)
    baseline_path = absolute(args.multires_assignments)
    out_dir = absolute(args.out)
    require(prediction_input.is_dir(), "predictions must be a complete inference directory")
    inference_summary_path = prediction_input / "inference-summary.json"
    prediction_path = prediction_input / "predictions.jsonl"
    for path in (
        target_path,
        inference_summary_path,
        prediction_path,
        numeric_path,
        manifest_path,
        baseline_path,
    ):
        require(path.is_file(), f"missing score input: {path}")
    inference_summary = json.loads(inference_summary_path.read_text(encoding="utf-8"))
    require(inference_summary.get("status") == "complete", "inference not complete")
    require(inference_summary.get("mode") == "full", "score requires full inference")
    require(inference_summary.get("sessions") == EXPECTED_SESSIONS, "inference sessions")
    require(inference_summary.get("operations") == EXPECTED_OPERATIONS, "inference operations")

    grouped = base.load_visible_operations(target_path)
    require(len(grouped) == EXPECTED_SESSIONS, "target session count")
    require(sum(map(len, grouped.values())) == EXPECTED_OPERATIONS, "target operation count")
    selected = sorted(grouped)
    predictions = base.load_prediction_rows(prediction_path)
    numeric = base.load_prediction_rows(numeric_path)
    expected = {
        (session, int(row["step_id"]))
        for session, rows in grouped.items()
        for row in rows
    }
    require(set(predictions) == expected, "candidate prediction coverage")
    require(set(numeric) == expected, "numeric prediction coverage")
    baselines = base.load_baselines(baseline_path)
    require(expected <= set(baselines), "recurrence baseline coverage")

    official, frameworks, tasks = base.load_stages_after_prediction(
        manifest_path, grouped, selected
    )
    pairs, operations = base.score_rows(
        grouped, predictions, baselines, official, frameworks, tasks
    )
    add_numeric_candidate(operations, pairs, numeric)
    require(len(operations) == EXPECTED_OPERATIONS, "scored operation count")
    require(len(pairs) == EXPECTED_OPERATIONS - EXPECTED_SESSIONS, "pair count")
    require(len(set(official.values())) == EXPECTED_STAGES, "official stage count")
    require(len(set(tasks.values())) == EXPECTED_TASKS, "task count")
    require(set(frameworks.values()) == EXPECTED_FRAMEWORKS, "framework set")

    methods = (
        "candidate",
        "numeric_candidate",
        "current_recurrence",
        "multires_recurrence",
        "plan_free_qwen",
        "phase",
        "raw_action",
        "action",
        "one_span",
    )
    metrics = {
        method: {
            "span": base.span_metrics(operations, method),
            "bcubed": base.bcubed(operations, method),
            "boundary": base.boundary_metrics(pairs, method),
        }
        for method in methods
    }
    out_dir.mkdir(parents=True, exist_ok=True)
    bootstrap = {
        baseline_name: base.task_cluster_bootstrap(
            operations,
            "candidate",
            baseline_name,
            out_dir / f"bootstrap-candidate-minus-{baseline_name}.jsonl",
        )
        for baseline_name in (
            "current_recurrence",
            "multires_recurrence",
            "numeric_candidate",
        )
    }
    main = ("current_recurrence", "multires_recurrence")
    candidate_f1 = metrics["candidate"]["span"]["f1"]
    higher = all(candidate_f1 > metrics[name]["span"]["f1"] for name in main)
    positive = all(bootstrap[name]["ci95"][0] > 0 for name in main)
    interpretation = (
        "supported-and-adopted"
        if higher and positive
        else "promising-not-adopted"
        if higher
        else "contradicted"
    )

    per_framework = {}
    for framework in sorted(EXPECTED_FRAMEWORKS):
        operation_slice = [row for row in operations if row["framework"] == framework]
        pair_slice = [row for row in pairs if row["framework"] == framework]
        per_framework[framework] = {
            method: {
                "span": base.span_metrics(operation_slice, method),
                "bcubed": base.bcubed(operation_slice, method),
                "boundary": base.boundary_metrics(pair_slice, method),
            }
            for method in ("candidate", *main, "numeric_candidate")
        }

    summary = {
        "schema": SCHEMA + ".score.v1",
        "status": "complete",
        "registered_interpretation": interpretation,
        "population": {
            "sessions": len(selected),
            "operations": len(operations),
            "pairs": len(pairs),
            "official_stages": len(set(official.values())),
            "tasks": len(set(tasks.values())),
            "frameworks": dict(Counter(frameworks.values())),
        },
        "metrics": metrics,
        "bootstrap": bootstrap,
        "per_framework": per_framework,
        "decision": {
            "main_adoption_comparators": list(main),
            "candidate_point_higher_than_both": higher,
            "candidate_intervals_positive_against_both": positive,
            "numeric_predecessor_role": "paired interface diagnostic only",
        },
        "claim_boundary": (
            "post-hoc flat human workflow-stage span fidelity only; generated "
            "names and deeper task-semantic hierarchy remain unvalidated"
        ),
    }
    write_jsonl(out_dir / "operation-score-rows.jsonl", operations)
    write_jsonl(out_dir / "boundary-score-rows.jsonl", pairs)
    write_json(out_dir / "summary.json", summary)
    (out_dir / "report.md").write_text(score_report(summary), encoding="utf-8")
    print(json.dumps(summary, sort_keys=True), flush=True)


def main() -> None:
    args = parse_args()
    if args.command == "infer":
        run_inference(args)
    else:
        run_scoring(args)


if __name__ == "__main__":
    main()
