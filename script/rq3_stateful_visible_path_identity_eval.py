#!/usr/bin/env python3
"""Score the visible semantic path emitted by the fixed stateful stack run.

This is a score-only construct audit. It does not replay transitions or call a
model. The primary candidate is the complete ordered visible label path. An
adjacent-identical-label contraction is reported only as a secondary mechanism
diagnostic, not as ordinary flamegraph identity.
"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import json
import math
from pathlib import Path
import sys
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "script"))

import rq3_source_native_task_progress_boundary_eval as source  # noqa: E402
import rq3_stateful_native_turn_task_stack_eval as stateful  # noqa: E402


base = source.base
SCHEMA = "agentsight.rq3-stateful-visible-path-identity"
EXPECTED_SESSIONS = 405
EXPECTED_OPERATIONS = 20_866
EXPECTED_STAGES = 2_948
EXPECTED_TASKS = 251
PREFLIGHT_TERMINUS = stateful.PREFLIGHT_TERMINUS


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("preflight", "full"))
    parser.add_argument("--predictions", type=Path, required=True)
    parser.add_argument("--step0054-score-rows", type=Path, required=True)
    parser.add_argument("--step0054-summary", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    return parser.parse_args()


def absolute(path: Path) -> Path:
    return path if path.is_absolute() else ROOT / path


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as stream:
        for line_number, line in enumerate(stream, 1):
            try:
                row = json.loads(line)
            except json.JSONDecodeError as error:
                raise RuntimeError(f"invalid JSON at {path}:{line_number}") from error
            require(isinstance(row, dict), f"non-object at {path}:{line_number}")
            rows.append(row)
    return rows


def prediction_key(row: dict[str, Any]) -> tuple[str, int]:
    return str(row["session"]), int(row["step_id"])


def visible_labels(prediction: dict[str, Any]) -> tuple[str, ...]:
    path = prediction.get("task_path")
    require(isinstance(path, list) and bool(path), "missing visible task path")
    labels: list[str] = []
    for frame in path:
        require(isinstance(frame, dict), "non-object task frame")
        label = frame.get("label")
        require(isinstance(label, str) and bool(label), "empty visible task label")
        labels.append(label)
    require(int(prediction["task_depth"]) == len(labels), "task depth mismatch")
    require(prediction["active_leaf_label"] == labels[-1], "active label mismatch")
    return tuple(labels)


def adjacent_idempotent(labels: tuple[str, ...]) -> tuple[str, ...]:
    output: list[str] = []
    for label in labels:
        if not output or output[-1] != label:
            output.append(label)
    return tuple(output)


def encode_path(labels: tuple[str, ...]) -> str:
    return json.dumps(labels, ensure_ascii=False, separators=(",", ":"))


def select_preflight_sessions(
    predictions: dict[tuple[str, int], dict[str, Any]],
) -> list[str]:
    by_adapter: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for (session, _), row in predictions.items():
        by_adapter[str(row["adapter"])][session] += 1
    require(set(by_adapter) == source.EXPECTED_LAYOUTS, "source layout coverage")
    selected: list[str] = []
    for adapter in sorted(by_adapter):
        if adapter == "terminus2-commands-txt-strings":
            require(PREFLIGHT_TERMINUS in by_adapter[adapter], "Terminus preflight")
            selected.append(PREFLIGHT_TERMINUS)
        else:
            selected.append(min((count, session) for session, count in by_adapter[adapter].items())[1])
    return sorted(selected)


def build_score_rows(
    prediction_rows: list[dict[str, Any]],
    step0054_rows: list[dict[str, Any]],
    selected: set[str],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    predictions: dict[tuple[str, int], dict[str, Any]] = {}
    for row in prediction_rows:
        key = prediction_key(row)
        require(key not in predictions, "duplicate prediction key")
        predictions[key] = row

    source_rows: dict[tuple[str, int], dict[str, Any]] = {}
    for row in step0054_rows:
        key = prediction_key(row)
        require(key not in source_rows, "duplicate Step 0054 score key")
        source_rows[key] = row
    require(set(predictions) == set(source_rows), "prediction/score-row coverage")

    operations: list[dict[str, Any]] = []
    global_exact_sessions: dict[str, set[str]] = defaultdict(set)
    global_collapsed_sessions: dict[str, set[str]] = defaultdict(set)
    for key in sorted(source_rows):
        session, _ = key
        if session not in selected:
            continue
        source_row = source_rows[key]
        prediction = predictions[key]
        require(
            str(source_row["candidate"]) == str(prediction["active_leaf_instance"]),
            "hidden instance reproduction",
        )
        labels = visible_labels(prediction)
        collapsed = adjacent_idempotent(labels)
        exact_global = encode_path(labels)
        collapsed_global = encode_path(collapsed)
        global_exact_sessions[exact_global].add(session)
        global_collapsed_sessions[collapsed_global].add(session)
        operations.append(
            {
                **source_row,
                "hidden_instance": str(source_row["candidate"]),
                "visible_path": session + "::" + exact_global,
                "adjacent_idempotent_path": session + "::" + collapsed_global,
                "visible_path_labels": list(labels),
                "adjacent_idempotent_labels": list(collapsed),
            }
        )

    by_session: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in operations:
        by_session[str(row["session"])].append(row)
    pairs: list[dict[str, Any]] = []
    methods = (
        "hidden_instance",
        "visible_path",
        "adjacent_idempotent_path",
        "multires_recurrence",
    )
    for session in sorted(by_session):
        rows = sorted(by_session[session], key=lambda row: int(row["step_id"]))
        require(
            len({int(row["step_id"]) for row in rows}) == len(rows),
            "duplicate session step",
        )
        for left, right in zip(rows, rows[1:]):
            pair = {
                "session": session,
                "framework": str(left["framework"]),
                "task_name": str(left["task_name"]),
                "position": int(left["step_id"]),
                "official_boundary": left["official_stage"] != right["official_stage"],
            }
            for method in methods:
                pair[method] = left[method] != right[method]
            pairs.append(pair)

    def fold_stats(paths: dict[str, set[str]]) -> dict[str, int]:
        recurring = {path for path, sessions in paths.items() if len(sessions) >= 2}
        return {
            "distinct_global_paths": len(paths),
            "paths_seen_in_multiple_sessions": len(recurring),
            "maximum_sessions_for_one_path": max(map(len, paths.values()), default=0),
        }

    folding = {
        "exact_visible_path": fold_stats(global_exact_sessions),
        "adjacent_idempotent_path": fold_stats(global_collapsed_sessions),
        "accuracy_interpretation": "none; global folds are behavior statistics",
    }
    return operations, pairs, folding


def metric_bundle(
    pairs: list[dict[str, Any]],
    operations: list[dict[str, Any]],
    methods: Iterable[str],
) -> dict[str, Any]:
    return {
        method: {
            "bcubed": base.bcubed(operations, method),
            "boundary": base.boundary_metrics(pairs, method),
            "span": base.span_metrics(operations, method),
        }
        for method in methods
    }


def same_metric(left: dict[str, Any], right: dict[str, Any]) -> bool:
    for family in ("bcubed", "boundary", "span"):
        for key, value in left[family].items():
            other = right[family][key]
            if isinstance(value, float):
                if not math.isclose(value, other, rel_tol=0.0, abs_tol=1e-12):
                    return False
            elif value != other:
                return False
    return True


def report(summary: dict[str, Any]) -> str:
    lines = [
        "# Stateful Visible-Path Identity — Result",
        "",
        f"- mode: {summary['mode']}",
        f"- status: {summary['status']}",
        "- disclosure: retrospective construct-correction audit over fixed Step 0054 outputs",
        f"- construct effect: **{summary['decision']['construct_effect']}**",
        f"- online constructor: **{summary['decision']['constructor_adoption']}**",
        "",
        "## Standard session-local stage metrics",
        "",
        "| Identity/method | B³ P | B³ R | B³ F1 | Boundary F1 | Span F1 |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for method, values in summary["metrics"].items():
        lines.append(
            f"| {method} | {values['bcubed']['precision']:.6f} | "
            f"{values['bcubed']['recall']:.6f} | {values['bcubed']['f1']:.6f} | "
            f"{values['boundary']['f1']:.6f} | {values['span']['f1']:.6f} |"
        )
    lines.extend(
        [
            "",
            "## Paired task-cluster effects",
            "",
            f"- exact visible minus hidden instance: {summary['bootstrap']['visible_minus_hidden']}",
            f"- exact visible minus recurrence: {summary['bootstrap']['visible_minus_recurrence']}",
            "",
            "## Claim boundary",
            "",
            summary["claim_boundary"],
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    args = parse_args()
    prediction_path = absolute(args.predictions)
    score_rows_path = absolute(args.step0054_score_rows)
    summary_path = absolute(args.step0054_summary)
    out_dir = absolute(args.out)
    for path in (prediction_path, score_rows_path, summary_path):
        require(path.is_file(), f"missing input: {path}")

    prediction_rows = load_jsonl(prediction_path)
    step0054_rows = load_jsonl(score_rows_path)
    step0054_summary = json.loads(summary_path.read_text(encoding="utf-8"))
    prediction_map = {prediction_key(row): row for row in prediction_rows}
    require(len(prediction_map) == len(prediction_rows), "prediction uniqueness")
    selected = (
        set(select_preflight_sessions(prediction_map))
        if args.mode == "preflight"
        else {session for session, _ in prediction_map}
    )
    operations, pairs, folding = build_score_rows(
        prediction_rows, step0054_rows, selected
    )
    methods = (
        "hidden_instance",
        "visible_path",
        "adjacent_idempotent_path",
        "multires_recurrence",
    )
    metrics = metric_bundle(pairs, operations, methods)

    if args.mode == "full":
        require(len(selected) == EXPECTED_SESSIONS, "full session count")
        require(len(operations) == EXPECTED_OPERATIONS, "full operation count")
        require(len(set(row["official_stage"] for row in operations)) == EXPECTED_STAGES, "stage count")
        require(len(set(row["task_name"] for row in operations)) == EXPECTED_TASKS, "task count")
        require(
            same_metric(metrics["hidden_instance"], step0054_summary["metrics"]["candidate"]),
            "Step 0054 hidden-instance metric drift",
        )
        require(
            same_metric(metrics["multires_recurrence"], step0054_summary["metrics"]["multires_recurrence"]),
            "Step 0054 recurrence metric drift",
        )

    out_dir.mkdir(parents=True, exist_ok=True)
    visible_minus_hidden = source.bcubed_task_bootstrap(
        operations,
        "visible_path",
        "hidden_instance",
        out_dir / "bootstrap-visible-minus-hidden.jsonl",
    )
    visible_minus_recurrence = source.bcubed_task_bootstrap(
        operations,
        "visible_path",
        "multires_recurrence",
        out_dir / "bootstrap-visible-minus-recurrence.jsonl",
    )
    per_framework: dict[str, Any] = {}
    for framework in sorted({str(row["framework"]) for row in operations}):
        framework_operations = [row for row in operations if row["framework"] == framework]
        framework_pairs = [row for row in pairs if row["framework"] == framework]
        per_framework[framework] = metric_bundle(
            framework_pairs, framework_operations, methods
        )

    construct_supported = visible_minus_hidden["ci95"][0] > 0
    constructor_adopted = visible_minus_recurrence["ci95"][0] > 0
    summary = {
        "schema": SCHEMA + ".score.v1",
        "status": "complete",
        "mode": args.mode,
        "retrospective": True,
        "population": {
            "sessions": len(selected),
            "operations": len(operations),
            "pairs": len(pairs),
            "stage_occurrences": len(set(row["official_stage"] for row in operations)),
            "task_clusters": len(set(row["task_name"] for row in operations)),
            "frameworks": dict(Counter(row["framework"] for row in operations)),
        },
        "metrics": metrics,
        "bootstrap": {
            "visible_minus_hidden": visible_minus_hidden,
            "visible_minus_recurrence": visible_minus_recurrence,
        },
        "per_framework": per_framework,
        "global_folding_behavior": folding,
        "decision": {
            "construct_effect": "supported" if construct_supported else "not-supported",
            "constructor_adoption": "adopted" if constructor_adopted else "not-adopted",
            "primary_identity": "complete ordered visible task label path",
            "adjacent_contraction_is_secondary_only": True,
            "session_is_namespace_not_stack_frame": True,
        },
        "claim_boundary": (
            "CodeTrace stages quantify only session-local occurrence partition fidelity. "
            "They do not validate cross-run path equivalence, ancestor topology, variable "
            "depth, label meaning, root canonicalization, or the transient "
            "phase/action/object/result suffix."
        ),
    }
    stateful.write_jsonl(out_dir / "operation-score-rows.jsonl", operations)
    stateful.write_jsonl(out_dir / "boundary-score-rows.jsonl", pairs)
    stateful.write_json(out_dir / "summary.json", summary)
    (out_dir / "report.md").write_text(report(summary), encoding="utf-8")
    print(json.dumps(summary, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
