#!/usr/bin/env python3
"""R355: oracle-depth adequacy audit for ranked operation-stack profiles.

R339 scored whether ranked groups take an analyst to useful sessions. R355
extends that audit downward: for each existing labeled task, it classifies and
scores progressively finer oracle units (session, operation/step, positive-run
episodes, and OSWorld human groups where available). Hidden labels are used
only after visible ranking for offline scoring.

The run does not fetch, sync, create, or relabel datasets. ScaleCUA's
`history_depth` is recorded as a context-only field and excluded from accuracy
claims because it is not a problem oracle in the tracked sample.
"""

from __future__ import annotations

import argparse
import csv
import html
import json
import math
import subprocess
import time
from collections import defaultdict
from pathlib import Path
from statistics import mean, median
from typing import Any

import sys

ROOT = Path(__file__).resolve().parents[1]
OUT_ROOT = ROOT / "docs" / "visexp" / "out"
DEFAULT_OUT_DIR = OUT_ROOT / "operation-oracle-depth-adequacy-r355"
RUN_ID = "R355"
SCALECUA_OPERATIONS = OUT_ROOT / "external-agent-trace-scalecua-r292" / "scalecua-operations.jsonl"

sys.path.insert(0, str(Path(__file__).resolve().parent))
import operation_query_utility_eval as r300  # noqa: E402
import operation_sequence_adequacy_eval as r339  # noqa: E402


VISIBLE_POLICIES = [
    ("flat", "width"),
    ("fixed_session", "query_aware"),
    ("dataset_native", "query_aware"),
    ("raw_action_stack", "query_aware"),
    ("operation_stack", "width"),
    ("operation_stack", "query_aware"),
]
TOP_K_VALUES = [1, 3, 5]
OPERATION_BUDGETS = [0.10, 0.20, 0.30]
RECALL_TARGETS = [0.25, 0.50]
HEADLINE_POLICY = "operation_stack:query_aware"


TASK_DEPTH_NOTES: dict[str, dict[str, Any]] = {
    "agentreward_looping": {
        "task_specific_depth": "agentreward_turn",
        "task_specific_fields": ["session", "turn"],
        "task_specific_kind": "turn",
        "task_specific_role": "middle_unit_proxy",
        "claim_note": "trajectory-level failure label; positive-run and turn units are proxy sub-session episodes, not gold intent boundaries",
    },
    "agentreward_side_effect": {
        "task_specific_depth": "agentreward_turn",
        "task_specific_fields": ["session", "turn"],
        "task_specific_kind": "turn",
        "task_specific_role": "middle_unit_proxy",
        "claim_note": "side-effect has few positive sessions, so sub-session proxy metrics are high-variance",
    },
    "satraj_unsafe": {
        "task_specific_depth": "satraj_step",
        "task_specific_fields": ["session", "step", "_source_line"],
        "task_specific_kind": "step",
        "task_specific_role": "operation_equivalent_control",
        "claim_note": "safety labels are step/operation-local in the tracked sample",
    },
    "agentnet_incorrect_step": {
        "task_specific_depth": "agentnet_step",
        "task_specific_fields": ["session", "step", "_source_line"],
        "task_specific_kind": "step",
        "task_specific_role": "operation_equivalent_control",
        "claim_note": "AgentNet correctness labels are step-local and mostly operation-equivalent",
    },
    "agentnet_redundant_step": {
        "task_specific_depth": "agentnet_step",
        "task_specific_fields": ["session", "step", "_source_line"],
        "task_specific_kind": "step",
        "task_specific_role": "operation_equivalent_control",
        "claim_note": "AgentNet redundancy labels are step-local and mostly operation-equivalent",
    },
    "osworld_group_start": {
        "task_specific_depth": "osworld_human_group",
        "task_specific_fields": ["session", "human_group"],
        "task_specific_kind": "human_group",
        "task_specific_role": "true_subtask_segment",
        "claim_note": "OSWorld exact human_group fields are the strongest true subtask/segment oracle; group-start remains a boundary objective",
    },
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    return parser.parse_args()


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return str(path.resolve())


def git_output(args: list[str]) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip()
        raise SystemExit(f"git {' '.join(args)} failed: {detail}")
    return result.stdout.strip()


def git_check(description: str, path: Path, args: list[str]) -> None:
    result = subprocess.run(
        ["git", *args, "--", rel(path)],
        cwd=ROOT,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip()
        suffix = f": {detail}" if detail else ""
        raise SystemExit(f"{rel(path)} failed source check: {description}{suffix}")


def ensure_sources_tracked_clean(paths: list[Path]) -> dict[str, str]:
    status = {}
    for path in sorted(set(paths)):
        if not path.exists():
            raise SystemExit(f"missing source artifact {rel(path)}")
        git_check("source artifact is not git-tracked", path, ["ls-files", "--error-unmatch"])
        git_check("source artifact has unstaged changes", path, ["diff", "--quiet"])
        git_check("source artifact has staged changes", path, ["diff", "--cached", "--quiet"])
        status[rel(path)] = "tracked_clean"
    return status


def round_value(value: Any) -> Any:
    if isinstance(value, float):
        if math.isnan(value):
            return None
        if math.isinf(value):
            return "inf"
        return round(value, 4)
    if isinstance(value, dict):
        return {key: round_value(child) for key, child in value.items()}
    if isinstance(value, list):
        return [round_value(child) for child in value]
    return value


def format_value(value: Any) -> Any:
    if value is None:
        return ""
    if isinstance(value, float):
        if math.isnan(value):
            return ""
        if math.isinf(value):
            return "inf"
        return round(value, 6)
    if isinstance(value, bool):
        return str(value)
    if isinstance(value, list):
        return "; ".join(str(item) for item in value)
    if isinstance(value, dict):
        return json.dumps(round_value(value), sort_keys=True)
    return value


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(round_value(payload), indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: format_value(row.get(field)) for field in fields})


def median_or_zero(values: list[float]) -> float:
    return float(median(values)) if values else 0.0


def mean_or_zero(values: list[float]) -> float:
    return float(mean(values)) if values else 0.0


def f1_score(precision: float, recall: float) -> float:
    if precision + recall == 0:
        return 0.0
    return 2 * precision * recall / (precision + recall)


def op_value(operation: dict[str, Any]) -> int:
    return int(operation.get("value") or 1)


def is_positive(operation: dict[str, Any]) -> bool:
    return operation["fields"].get("target_positive") == "positive"


def field_value(operation: dict[str, Any], field: str) -> str:
    if field == "_source_line":
        return str(operation.get("_source_line", "unknown"))
    return operation["fields"].get(field, "unknown")


def unit_id_from_fields(operation: dict[str, Any], fields: list[str]) -> str:
    return "|".join(f"{field}={field_value(operation, field)}" for field in fields)


def operation_identity_fields(task: dict[str, Any]) -> list[str]:
    if task["dataset"] in {"agentnet", "satraj-os-safety", "osworld-human"}:
        return ["session", "step", "_source_line"]
    return ["session", "turn", "_source_line"]


def positive_run_ids(operations: list[dict[str, Any]]) -> dict[int, str]:
    ids: dict[int, str] = {}
    by_session: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for operation in operations:
        by_session[field_value(operation, "session")].append(operation)
    for session, rows in by_session.items():
        rows.sort(key=r339.operation_order)
        run_index = -1
        last_state: str | None = None
        for operation in rows:
            state = "positive" if is_positive(operation) else "negative"
            if state != last_state:
                run_index += 1
                last_state = state
            ids[int(operation.get("_source_line") or 0)] = (
                f"session={session}|positive_run={run_index}|state={state}"
            )
    return ids


def depth_specs_for_task(task: dict[str, Any]) -> list[dict[str, Any]]:
    note = TASK_DEPTH_NOTES[task["id"]]
    return [
        {
            "unit_depth": "session",
            "unit_kind": "session",
            "unit_fields": ["session"],
            "segment_fields": ["session"],
            "claim_role": "session_anchor",
            "subtask_eligible": False,
            "true_subtask_oracle": False,
        },
        {
            "unit_depth": "operation",
            "unit_kind": "operation",
            "unit_fields": operation_identity_fields(task),
            "segment_fields": ["session"],
            "claim_role": "operation_anchor",
            "subtask_eligible": True,
            "true_subtask_oracle": task["dataset"] not in {"agent-reward-bench"},
        },
        {
            "unit_depth": "positive_run",
            "unit_kind": "contiguous_target_positive_run",
            "computed": "positive_run",
            "unit_fields": ["session", "positive_run", "state"],
            "segment_fields": ["session"],
            "claim_role": "sub_session_episode_proxy",
            "subtask_eligible": True,
            "true_subtask_oracle": False,
        },
        {
            "unit_depth": note["task_specific_depth"],
            "unit_kind": note["task_specific_kind"],
            "unit_fields": note["task_specific_fields"],
            "segment_fields": ["session"],
            "claim_role": note["task_specific_role"],
            "subtask_eligible": note["task_specific_role"] != "middle_unit_proxy"
            or task["dataset"] == "osworld-human",
            "true_subtask_oracle": note["task_specific_role"] == "true_subtask_segment",
            "claim_note": note["claim_note"],
        },
    ]


def depth_unit_id(
    operation: dict[str, Any],
    spec: dict[str, Any],
    run_ids: dict[int, str],
) -> str:
    if spec.get("computed") == "positive_run":
        return run_ids[int(operation.get("_source_line") or 0)]
    return unit_id_from_fields(operation, spec["unit_fields"])


def depth_maps(
    operations: list[dict[str, Any]],
    spec: dict[str, Any],
    run_ids: dict[int, str],
) -> dict[str, Any]:
    all_units: dict[str, list[dict[str, Any]]] = defaultdict(list)
    all_segments: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for operation in operations:
        all_units[depth_unit_id(operation, spec, run_ids)].append(operation)
        all_segments[unit_id_from_fields(operation, spec.get("segment_fields") or ["session"])].append(operation)
    positive_units = {
        key for key, rows in all_units.items() if any(is_positive(operation) for operation in rows)
    }
    positive_segments = {
        key for key, rows in all_segments.items() if any(is_positive(operation) for operation in rows)
    }
    positive_sessions = {
        field_value(operation, "session") for operation in operations if is_positive(operation)
    }
    unit_lengths = {
        key: sum(op_value(operation) for operation in rows) for key, rows in all_units.items()
    }
    return {
        "all_units": all_units,
        "positive_units": positive_units,
        "all_segments": all_segments,
        "positive_segments": positive_segments,
        "positive_sessions": positive_sessions,
        "unit_lengths": unit_lengths,
    }


def selected_rows(groups: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for group in groups:
        rows.extend(group["rows"])
    return rows


def unit_metrics(
    selected: list[dict[str, Any]],
    operations: list[dict[str, Any]],
    spec: dict[str, Any],
    maps: dict[str, Any],
    run_ids: dict[int, str],
    label: str,
) -> dict[str, Any]:
    rows = selected_rows(selected)
    selected_units = {depth_unit_id(operation, spec, run_ids) for operation in rows}
    selected_positive_units = selected_units & maps["positive_units"]
    selected_segments = {
        unit_id_from_fields(operation, spec.get("segment_fields") or ["session"])
        for operation in rows
    }
    selected_positive_segments = selected_segments & maps["positive_segments"]
    selected_ops = sum(op_value(operation) for operation in rows)
    selected_positive_ops = sum(op_value(operation) for operation in rows if is_positive(operation))
    total_ops = sum(op_value(operation) for operation in operations)
    total_positive_ops = sum(op_value(operation) for operation in operations if is_positive(operation))
    total_units = len(maps["all_units"])
    positive_units = len(maps["positive_units"])
    total_segments = len(maps["all_segments"])
    positive_segments = len(maps["positive_segments"])
    unit_work = len(selected_units) / total_units if total_units else 0.0
    unit_precision = len(selected_positive_units) / len(selected_units) if selected_units else 0.0
    unit_recall = len(selected_positive_units) / positive_units if positive_units else 0.0
    unit_prevalence = positive_units / total_units if total_units else 0.0
    segment_work = len(selected_segments) / total_segments if total_segments else 0.0
    segment_precision = (
        len(selected_positive_segments) / len(selected_segments) if selected_segments else 0.0
    )
    segment_recall = (
        len(selected_positive_segments) / positive_segments if positive_segments else 0.0
    )
    segment_prevalence = positive_segments / total_segments if total_segments else 0.0

    selected_by_unit: dict[str, int] = defaultdict(int)
    for operation in rows:
        selected_by_unit[depth_unit_id(operation, spec, run_ids)] += op_value(operation)
    hit_unit_fractions = [
        selected_by_unit[unit] / maps["unit_lengths"][unit]
        for unit in selected_positive_units
        if maps["unit_lengths"].get(unit)
    ]

    selected_sessions = {field_value(operation, "session") for operation in rows}
    selected_positive_sessions = selected_sessions & maps["positive_sessions"]
    hit_unit_sessions = {
        field_value(operation, "session")
        for operation in rows
        if depth_unit_id(operation, spec, run_ids) in selected_positive_units
    }
    positive_session_without_unit = len(selected_positive_sessions - hit_unit_sessions)

    operation_precision = selected_positive_ops / selected_ops if selected_ops else 0.0
    operation_recall = selected_positive_ops / total_positive_ops if total_positive_ops else 0.0
    spillover_fraction = (
        (selected_ops - selected_positive_ops) / selected_ops if selected_ops else 0.0
    )
    return {
        f"{label}_operation_work": selected_ops / total_ops if total_ops else 0.0,
        f"{label}_positive_operation_recall": operation_recall,
        f"{label}_positive_operation_precision": operation_precision,
        f"{label}_positive_operation_f1": f1_score(operation_precision, operation_recall),
        f"{label}_spillover_operation_fraction": spillover_fraction,
        f"{label}_selected_units": len(selected_units),
        f"{label}_hit_positive_units": len(selected_positive_units),
        f"{label}_unit_work": unit_work,
        f"{label}_positive_unit_precision": unit_precision,
        f"{label}_positive_unit_recall": unit_recall,
        f"{label}_positive_unit_f1": f1_score(unit_precision, unit_recall),
        f"{label}_positive_unit_lift": unit_precision / unit_prevalence if unit_prevalence else 0.0,
        f"{label}_unit_efficiency": unit_recall / unit_work if unit_work else 0.0,
        f"{label}_median_selected_fraction_of_hit_unit": median_or_zero(hit_unit_fractions),
        f"{label}_operation_recall_minus_unit_recall": operation_recall - unit_recall,
        f"{label}_positive_session_without_unit_hit": positive_session_without_unit,
        f"{label}_selected_segments": len(selected_segments),
        f"{label}_hit_positive_segments": len(selected_positive_segments),
        f"{label}_segment_work": segment_work,
        f"{label}_positive_segment_precision": segment_precision,
        f"{label}_positive_segment_recall": segment_recall,
        f"{label}_positive_segment_f1": f1_score(segment_precision, segment_recall),
        f"{label}_positive_segment_lift": (
            segment_precision / segment_prevalence if segment_prevalence else 0.0
        ),
    }


def prefix_targets(
    ranked: list[dict[str, Any]],
    operations: list[dict[str, Any]],
    spec: dict[str, Any],
    maps: dict[str, Any],
    run_ids: dict[int, str],
) -> dict[str, Any]:
    total_ops = sum(op_value(operation) for operation in operations)
    result: dict[str, Any] = {}
    for target in RECALL_TARGETS:
        hit_units: set[str] = set()
        selected_units: set[str] = set()
        inspected_ops = 0
        target_count = max(1, math.ceil(len(maps["positive_units"]) * target))
        found = False
        for index, group in enumerate(ranked, 1):
            inspected_ops += int(group["operations"])
            for operation in group["rows"]:
                unit = depth_unit_id(operation, spec, run_ids)
                selected_units.add(unit)
                if unit in maps["positive_units"]:
                    hit_units.add(unit)
            if len(hit_units) >= target_count:
                result[f"groups_to_{int(target * 100)}pct_positive_units"] = index
                result[f"operation_work_to_{int(target * 100)}pct_positive_units"] = (
                    inspected_ops / total_ops if total_ops else 0.0
                )
                result[f"unit_work_to_{int(target * 100)}pct_positive_units"] = (
                    len(selected_units) / len(maps["all_units"]) if maps["all_units"] else 0.0
                )
                found = True
                break
        if not found:
            result[f"groups_to_{int(target * 100)}pct_positive_units"] = len(ranked)
            result[f"operation_work_to_{int(target * 100)}pct_positive_units"] = 1.0
            result[f"unit_work_to_{int(target * 100)}pct_positive_units"] = 1.0

    hit_units = set()
    inspected_ops = 0
    for index, group in enumerate(ranked, 1):
        inspected_ops += int(group["operations"])
        for operation in group["rows"]:
            unit = depth_unit_id(operation, spec, run_ids)
            if unit in maps["positive_units"]:
                hit_units.add(unit)
        if hit_units:
            result["groups_to_first_positive_unit"] = index
            result["operation_work_to_first_positive_unit"] = inspected_ops / total_ops if total_ops else 0.0
            break
    if not hit_units:
        result["groups_to_first_positive_unit"] = None
        result["operation_work_to_first_positive_unit"] = None
    return result


def fragmentation_metrics(
    groups: list[dict[str, Any]],
    spec: dict[str, Any],
    maps: dict[str, Any],
    run_ids: dict[int, str],
) -> dict[str, Any]:
    unit_to_groups: dict[str, set[str]] = defaultdict(set)
    group_to_units: dict[str, set[str]] = defaultdict(set)
    for group in groups:
        group_key = group["group_id"]
        for operation in group["rows"]:
            unit = depth_unit_id(operation, spec, run_ids)
            unit_to_groups[unit].add(group_key)
            group_to_units[group_key].add(unit)
    positive_unit_fragmentation = [
        float(len(unit_to_groups[unit])) for unit in maps["positive_units"]
    ]
    positive_group_unit_counts = [
        float(len(group_to_units[group["group_id"]])) for group in groups if group["positives"] > 0
    ]
    return {
        "positive_units_median_group_fragmentation": median_or_zero(positive_unit_fragmentation),
        "positive_units_mean_group_fragmentation": mean_or_zero(positive_unit_fragmentation),
        "positive_groups_median_units_per_group": median_or_zero(positive_group_unit_counts),
        "positive_groups_mean_units_per_group": mean_or_zero(positive_group_unit_counts),
    }


def score_policy_depth(
    task: dict[str, Any],
    view: str,
    ranker: str,
    operations: list[dict[str, Any]],
    groups: list[dict[str, Any]],
    summary: dict[str, Any],
    spec: dict[str, Any],
    maps: dict[str, Any],
    run_ids: dict[int, str],
) -> dict[str, Any]:
    ranked = r339.rank_groups(task, groups, ranker)
    row = {
        "task": task["id"],
        "dataset": task["dataset"],
        "query_family": task["query_family"],
        "view": view,
        "ranker": ranker,
        "policy": f"{view}:{ranker}",
        "uses_hidden_fields": r339.r320.policy_uses_hidden_fields(view, ranker),
        "unit_depth": spec["unit_depth"],
        "unit_kind": spec["unit_kind"],
        "claim_role": spec["claim_role"],
        "subtask_eligible": spec["subtask_eligible"],
        "true_subtask_oracle": spec["true_subtask_oracle"],
        "operations": summary["operations"],
        "positives": summary["positives"],
        "groups": summary["groups"],
        "oracle_units": len(maps["all_units"]),
        "positive_oracle_units": len(maps["positive_units"]),
        "oracle_unit_prevalence": (
            len(maps["positive_units"]) / len(maps["all_units"]) if maps["all_units"] else 0.0
        ),
        "stack_fields": summary["stack"],
    }
    for k in TOP_K_VALUES:
        row.update(unit_metrics(ranked[:k], operations, spec, maps, run_ids, f"top{k}"))
    for budget in OPERATION_BUDGETS:
        selected = r339.select_for_operation_budget(ranked, summary, budget)
        row.update(unit_metrics(selected, operations, spec, maps, run_ids, f"budget{int(budget * 100)}"))
    row.update(prefix_targets(ranked, operations, spec, maps, run_ids))
    row.update(fragmentation_metrics(groups, spec, maps, run_ids))
    return row


def evaluate_policies() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    matrix = []
    rows = []
    for task in r300.TASKS:
        operations_for_depth = r300.load_task_operations(task)
        run_ids = positive_run_ids(operations_for_depth)
        for spec in depth_specs_for_task(task):
            maps = depth_maps(operations_for_depth, spec, run_ids)
            matrix.append(
                {
                    "task": task["id"],
                    "dataset": task["dataset"],
                    "query_family": task["query_family"],
                    "oracle_field": task["oracle_field"],
                    "positive_values": sorted(task["positive_values"]),
                    "unit_depth": spec["unit_depth"],
                    "unit_kind": spec["unit_kind"],
                    "claim_role": spec["claim_role"],
                    "unit_fields": spec["unit_fields"],
                    "segment_fields": spec.get("segment_fields", []),
                    "subtask_eligible": spec["subtask_eligible"],
                    "true_subtask_oracle": spec["true_subtask_oracle"],
                    "operations": sum(op_value(operation) for operation in operations_for_depth),
                    "positive_operations": sum(
                        op_value(operation) for operation in operations_for_depth if is_positive(operation)
                    ),
                    "oracle_units": len(maps["all_units"]),
                    "positive_oracle_units": len(maps["positive_units"]),
                    "included_in_accuracy": True,
                    "claim_note": TASK_DEPTH_NOTES[task["id"]]["claim_note"],
                }
            )
            for view, ranker in VISIBLE_POLICIES:
                operations, groups, summary = r339.group_task_view(task, view)
                rows.append(
                    score_policy_depth(task, view, ranker, operations, groups, summary, spec, maps, run_ids)
                )
    matrix.extend(scalecua_context_rows())
    return matrix, rows


def scalecua_context_rows() -> list[dict[str, Any]]:
    if not SCALECUA_OPERATIONS.exists():
        return []
    rows = 0
    sessions: set[str] = set()
    history_depths: set[str] = set()
    history_states: set[str] = set()
    with SCALECUA_OPERATIONS.open(encoding="utf-8") as file:
        for line in file:
            if not line.strip():
                continue
            rows += 1
            fields = json.loads(line).get("fields") or {}
            sessions.add(str(fields.get("session", "unknown")))
            history_depths.add(str(fields.get("history_depth", "unknown")))
            history_states.add(str(fields.get("history_state", "unknown")))
    return [
        {
            "task": "scalecua_history_depth",
            "dataset": "scalecua-navigation",
            "query_family": "context-history",
            "oracle_field": "history_depth",
            "positive_values": [],
            "unit_depth": "history_context",
            "unit_kind": "history_context",
            "claim_role": "context_only",
            "unit_fields": ["session", "history_depth", "history_state"],
            "segment_fields": ["session"],
            "subtask_eligible": False,
            "true_subtask_oracle": False,
            "operations": rows,
            "positive_operations": 0,
            "oracle_units": len(sessions) * max(len(history_depths), 1),
            "positive_oracle_units": 0,
            "included_in_accuracy": False,
            "claim_note": "ScaleCUA history_depth is context/provenance in this tracked sample, not a problem oracle.",
        }
    ]


def rows_by_task_depth_policy(rows: list[dict[str, Any]]) -> dict[tuple[str, str, str], dict[str, Any]]:
    return {(row["task"], row["unit_depth"], row["policy"]): row for row in rows}


def compare_default(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by = rows_by_task_depth_policy(rows)
    task_depths = sorted({(row["task"], row["unit_depth"]) for row in rows})
    baselines = [
        "flat:width",
        "fixed_session:query_aware",
        "dataset_native:query_aware",
        "raw_action_stack:query_aware",
        "operation_stack:width",
    ]
    metrics = [
        ("top5_unit_work", "lower"),
        ("top5_positive_unit_recall", "higher"),
        ("budget30_positive_unit_recall", "higher"),
        ("budget30_positive_unit_f1", "higher"),
        ("budget30_unit_efficiency", "higher"),
        ("groups_to_25pct_positive_units", "lower"),
        ("groups_to_50pct_positive_units", "lower"),
        ("operation_work_to_50pct_positive_units", "lower"),
        ("positive_groups_median_units_per_group", "lower"),
        ("budget30_positive_session_without_unit_hit", "lower"),
    ]
    comparisons = []
    for baseline in baselines:
        for metric, direction in metrics:
            deltas = []
            improved = 0
            worse = 0
            comparable = 0
            for task, depth in task_depths:
                left = by[(task, depth, HEADLINE_POLICY)].get(metric)
                right = by[(task, depth, baseline)].get(metric)
                if left in (None, "") or right in (None, ""):
                    continue
                comparable += 1
                delta = float(left) - float(right)
                deltas.append(delta)
                if direction == "higher":
                    improved += delta > 0
                    worse += delta < 0
                else:
                    improved += delta < 0
                    worse += delta > 0
            comparisons.append(
                {
                    "left": HEADLINE_POLICY,
                    "right": baseline,
                    "metric": metric,
                    "direction": direction,
                    "task_depth_rows": comparable,
                    "improved_rows": improved,
                    "worse_rows": worse,
                    "tied_rows": comparable - improved - worse,
                    "median_delta": median_or_zero(deltas),
                    "mean_delta": mean_or_zero(deltas),
                }
            )
    return comparisons


def policy_summary(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by[(row["policy"], row["unit_depth"])].append(row)
    metrics = [
        "top5_unit_work",
        "top5_positive_unit_recall",
        "budget30_positive_unit_recall",
        "budget30_positive_unit_f1",
        "budget30_unit_efficiency",
        "groups_to_50pct_positive_units",
        "operation_work_to_50pct_positive_units",
        "budget30_spillover_operation_fraction",
        "budget30_positive_session_without_unit_hit",
        "positive_groups_median_units_per_group",
    ]
    summary = []
    for (policy, depth), items in sorted(by.items()):
        row = {
            "policy": policy,
            "unit_depth": depth,
            "rows": len(items),
            "tasks": len({item["task"] for item in items}),
        }
        for metric in metrics:
            row[f"median_{metric}"] = median_or_zero(
                [float(item[metric]) for item in items if item.get(metric) not in (None, "")]
            )
        summary.append(row)
    return summary


def task_cards(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by = rows_by_task_depth_policy(rows)
    cards = []
    for task in r300.TASKS:
        depths = [spec["unit_depth"] for spec in depth_specs_for_task(task)]
        for depth in depths:
            default = by[(task["id"], depth, HEADLINE_POLICY)]
            fixed = by[(task["id"], depth, "fixed_session:query_aware")]
            raw = by[(task["id"], depth, "raw_action_stack:query_aware")]
            candidates = [row for row in rows if row["task"] == task["id"] and row["unit_depth"] == depth]
            best = max(
                candidates,
                key=lambda row: (
                    row["budget30_positive_unit_f1"],
                    row["budget30_positive_unit_recall"],
                    -row["budget30_unit_work"],
                ),
            )
            if depth == "osworld_human_group" and default["budget30_positive_unit_recall"] <= fixed["budget30_positive_unit_recall"]:
                action = "Boundary/subtask depth needs boundary-derived fields before claiming recovery."
            elif default["budget30_positive_unit_recall"] > fixed["budget30_positive_unit_recall"]:
                action = "Operation-stack improves oracle-unit recall over fixed-session for this depth."
            elif raw["budget30_positive_unit_recall"] > default["budget30_positive_unit_recall"]:
                action = "Raw action has higher unit recall; use operation-stack to reduce broad action groups."
            else:
                action = "Preserve baseline counterpoint; operation-stack is an explanation view here."
            cards.append(
                {
                    "task": task["id"],
                    "dataset": task["dataset"],
                    "query_family": task["query_family"],
                    "unit_depth": depth,
                    "unit_kind": default["unit_kind"],
                    "claim_role": default["claim_role"],
                    "subtask_eligible": default["subtask_eligible"],
                    "positive_oracle_units": default["positive_oracle_units"],
                    "best_budget30_unit_policy": best["policy"],
                    "best_budget30_positive_unit_f1": best["budget30_positive_unit_f1"],
                    "operation_stack_budget30_positive_unit_recall": default["budget30_positive_unit_recall"],
                    "operation_stack_budget30_positive_unit_f1": default["budget30_positive_unit_f1"],
                    "operation_stack_groups_to_50pct_positive_units": default["groups_to_50pct_positive_units"],
                    "operation_stack_budget30_spillover": default["budget30_spillover_operation_fraction"],
                    "operation_stack_depth_gap_sessions": default["budget30_positive_session_without_unit_hit"],
                    "fixed_session_budget30_positive_unit_recall": fixed["budget30_positive_unit_recall"],
                    "raw_action_budget30_positive_unit_recall": raw["budget30_positive_unit_recall"],
                    "positive_groups_median_units_per_group": default["positive_groups_median_units_per_group"],
                    "action": action,
                }
            )
    return cards


def claim_summary(
    matrix: list[dict[str, Any]],
    rows: list[dict[str, Any]],
    comparisons: list[dict[str, Any]],
) -> dict[str, Any]:
    default_rows = [row for row in rows if row["policy"] == HEADLINE_POLICY]
    positive_run_rows = [row for row in default_rows if row["unit_depth"] == "positive_run"]
    true_subtask_rows = [row for row in default_rows if row["true_subtask_oracle"]]
    subtask_rows = [row for row in default_rows if row["subtask_eligible"]]

    def improved(metric: str, baseline: str) -> int:
        for row in comparisons:
            if row["metric"] == metric and row["right"] == baseline:
                return int(row["improved_rows"])
        return 0

    matrix_included = [row for row in matrix if row["included_in_accuracy"]]
    return {
        "tasks": len({row["task"] for row in default_rows}),
        "datasets": len({row["dataset"] for row in default_rows}),
        "accuracy_unit_depth_rows": len(matrix_included),
        "context_only_rows": sum(not row["included_in_accuracy"] for row in matrix),
        "subtask_eligible_unit_depth_rows": sum(row["subtask_eligible"] for row in matrix_included),
        "true_subtask_oracle_rows": sum(row["true_subtask_oracle"] for row in matrix_included),
        "unit_depths": sorted({row["unit_depth"] for row in default_rows}),
        "default_policy": HEADLINE_POLICY,
        "default_all_depth_medians": {
            "top5_unit_work": median_or_zero([row["top5_unit_work"] for row in default_rows]),
            "budget30_positive_unit_recall": median_or_zero(
                [row["budget30_positive_unit_recall"] for row in default_rows]
            ),
            "budget30_positive_unit_f1": median_or_zero(
                [row["budget30_positive_unit_f1"] for row in default_rows]
            ),
            "groups_to_50pct_positive_units": median_or_zero(
                [float(row["groups_to_50pct_positive_units"]) for row in default_rows]
            ),
            "budget30_spillover_operation_fraction": median_or_zero(
                [row["budget30_spillover_operation_fraction"] for row in default_rows]
            ),
        },
        "positive_run_medians": {
            "budget30_positive_unit_recall": median_or_zero(
                [row["budget30_positive_unit_recall"] for row in positive_run_rows]
            ),
            "budget30_positive_unit_f1": median_or_zero(
                [row["budget30_positive_unit_f1"] for row in positive_run_rows]
            ),
            "groups_to_50pct_positive_units": median_or_zero(
                [float(row["groups_to_50pct_positive_units"]) for row in positive_run_rows]
            ),
        },
        "subtask_eligible_medians": {
            "budget30_positive_unit_recall": median_or_zero(
                [row["budget30_positive_unit_recall"] for row in subtask_rows]
            ),
            "budget30_positive_unit_f1": median_or_zero(
                [row["budget30_positive_unit_f1"] for row in subtask_rows]
            ),
        },
        "true_subtask_oracle_medians": {
            "budget30_positive_unit_recall": median_or_zero(
                [row["budget30_positive_unit_recall"] for row in true_subtask_rows]
            ),
            "budget30_positive_unit_f1": median_or_zero(
                [row["budget30_positive_unit_f1"] for row in true_subtask_rows]
            ),
        },
        "paired_checks": {
            "top5_unit_work_lt_flat_rows": improved("top5_unit_work", "flat:width"),
            "budget30_unit_recall_gt_fixed_rows": improved(
                "budget30_positive_unit_recall", "fixed_session:query_aware"
            ),
            "budget30_unit_f1_gt_fixed_rows": improved(
                "budget30_positive_unit_f1", "fixed_session:query_aware"
            ),
            "groups_to_50pct_units_lt_fixed_rows": improved(
                "groups_to_50pct_positive_units", "fixed_session:query_aware"
            ),
            "positive_units_per_group_lt_raw_rows": improved(
                "positive_groups_median_units_per_group", "raw_action_stack:query_aware"
            ),
            "depth_gap_lt_fixed_rows": improved(
                "budget30_positive_session_without_unit_hit", "fixed_session:query_aware"
            ),
        },
        "supported_wording": (
            "On existing labeled traces, the profiler can be evaluated at the oracle "
            "depth provided by each dataset. Operation-stack rankings give a measurable "
            "depth-aware triage surface across session, operation/step, positive-run, "
            "and OSWorld human-group units, while preserving explicit baseline and "
            "oracle-depth counterpoints."
        ),
        "counterpoints": [
            "session-level AgentRewardBench labels do not prove latent subtask boundaries",
            "positive-run units are a cross-dataset proxy, not human intent annotations",
            "AgentNet/SATraj step units are often operation-equivalent controls",
            "OSWorld human_group is the strongest true subtask oracle and remains boundary-field sensitive",
            "ScaleCUA history_depth is context-only in this tracked sample and excluded from accuracy claims",
        ],
    }


def render_markdown(report: dict[str, Any]) -> str:
    claim = report["claim_summary"]
    med = claim["default_all_depth_medians"]
    pos = claim["positive_run_medians"]
    lines = [
        "# R355 Oracle-Depth Adequacy Audit",
        "",
        "R355 extends R339 below session scope. It reuses tracked labeled operation JSONL and scores visible-ranked groups only after ranking.",
        "",
        "## Summary",
        "",
        f"- Overall: `{report['status']}`.",
        f"- Tasks / datasets: {claim['tasks']} / {claim['datasets']}.",
        f"- Accuracy unit-depth rows: {claim['accuracy_unit_depth_rows']}.",
        f"- Subtask-eligible rows: {claim['subtask_eligible_unit_depth_rows']}.",
        f"- True subtask oracle rows: {claim['true_subtask_oracle_rows']}.",
        f"- Unit depths: `{', '.join(claim['unit_depths'])}`.",
        f"- Default policy: `{claim['default_policy']}`.",
        f"- Median top-5 oracle-unit work across depths: {med['top5_unit_work']:.4f}.",
        f"- Median budget-30 positive oracle-unit recall across depths: {med['budget30_positive_unit_recall']:.4f}.",
        f"- Median budget-30 positive-run recall: {pos['budget30_positive_unit_recall']:.4f}.",
        f"- Median groups to 50% positive oracle units: {med['groups_to_50pct_positive_units']:.1f}.",
        "",
        "## Paired Checks",
        "",
        "| Check | Rows |",
        "|---|---:|",
    ]
    for key, value in claim["paired_checks"].items():
        lines.append(f"| {key} | {value}/{claim['accuracy_unit_depth_rows']} |")
    lines.extend(
        [
            "",
            "## Task-Depth Cards",
            "",
            "| Task | Depth | Best policy | OS budget-30 unit recall | OS groups to 50% units | Action |",
            "|---|---|---|---:|---:|---|",
        ]
    )
    for row in report["task_cards"]:
        lines.append(
            "| {task} | {depth} | {best} | {recall:.4f} | {groups} | {action} |".format(
                task=row["task"],
                depth=row["unit_depth"],
                best=row["best_budget30_unit_policy"],
                recall=row["operation_stack_budget30_positive_unit_recall"],
                groups=row["operation_stack_groups_to_50pct_positive_units"],
                action=row["action"],
            )
        )
    lines.extend(
        [
            "",
            "## Claim Boundary",
            "",
            claim["supported_wording"],
            "",
            "Counterpoints:",
        ]
    )
    lines.extend(f"- {item}" for item in claim["counterpoints"])
    lines.append("")
    return "\n".join(lines)


def render_html(report: dict[str, Any]) -> str:
    rows = "\n".join(
        "<tr>"
        f"<td>{html.escape(row['task'])}</td>"
        f"<td>{html.escape(row['unit_depth'])}</td>"
        f"<td>{html.escape(row['best_budget30_unit_policy'])}</td>"
        f"<td>{row['operation_stack_budget30_positive_unit_recall']:.4f}</td>"
        f"<td>{row['operation_stack_groups_to_50pct_positive_units']}</td>"
        f"<td>{html.escape(row['action'])}</td>"
        "</tr>"
        for row in report["task_cards"]
    )
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>R355 Oracle-Depth Adequacy Audit</title>
<style>
body {{ font-family: system-ui, sans-serif; margin: 32px; color: #1f2937; }}
table {{ border-collapse: collapse; width: 100%; }}
th, td {{ border-bottom: 1px solid #d1d5db; padding: 8px; vertical-align: top; }}
td:nth-child(4), td:nth-child(5), th:nth-child(4), th:nth-child(5) {{ text-align: right; }}
code {{ background: #f3f4f6; padding: 1px 4px; border-radius: 4px; }}
</style>
</head>
<body>
<h1>R355 Oracle-Depth Adequacy Audit</h1>
<p>Visible-ranked profiler groups scored at dataset-provided oracle depth; no dataset sync or relabeling.</p>
<table>
<thead><tr><th>Task</th><th>Depth</th><th>Best policy</th><th>OS budget-30 unit recall</th><th>OS groups to 50% units</th><th>Action</th></tr></thead>
<tbody>{rows}</tbody>
</table>
</body>
</html>
"""


def write_outputs(out_dir: Path, report: dict[str, Any]) -> None:
    write_json(out_dir / "oracle-depth-adequacy-report.json", report)
    write_json(
        out_dir / "run-result.json",
        {"status": report["status"], "report": rel(out_dir / "oracle-depth-adequacy-report.json")},
    )
    matrix_fields = [
        "task",
        "dataset",
        "query_family",
        "oracle_field",
        "positive_values",
        "unit_depth",
        "unit_kind",
        "claim_role",
        "unit_fields",
        "subtask_eligible",
        "true_subtask_oracle",
        "operations",
        "positive_operations",
        "oracle_units",
        "positive_oracle_units",
        "included_in_accuracy",
        "claim_note",
    ]
    write_csv(out_dir / "oracle-depth-matrix.csv", report["oracle_depth_matrix"], matrix_fields)
    policy_fields = [
        "task",
        "dataset",
        "query_family",
        "policy",
        "view",
        "ranker",
        "unit_depth",
        "unit_kind",
        "claim_role",
        "subtask_eligible",
        "true_subtask_oracle",
        "operations",
        "positives",
        "groups",
        "oracle_units",
        "positive_oracle_units",
        "top5_unit_work",
        "top5_positive_unit_recall",
        "top5_positive_unit_f1",
        "budget30_unit_work",
        "budget30_positive_unit_recall",
        "budget30_positive_unit_f1",
        "budget30_unit_efficiency",
        "budget30_spillover_operation_fraction",
        "budget30_positive_session_without_unit_hit",
        "groups_to_25pct_positive_units",
        "groups_to_50pct_positive_units",
        "operation_work_to_50pct_positive_units",
        "operation_work_to_first_positive_unit",
        "positive_units_median_group_fragmentation",
        "positive_groups_median_units_per_group",
    ]
    write_csv(out_dir / "policy-depth-adequacy.csv", report["policy_rows"], policy_fields)
    comparison_fields = [
        "left",
        "right",
        "metric",
        "direction",
        "task_depth_rows",
        "improved_rows",
        "worse_rows",
        "tied_rows",
        "median_delta",
        "mean_delta",
    ]
    write_csv(out_dir / "depth-policy-comparisons.csv", report["comparisons"], comparison_fields)
    card_fields = [
        "task",
        "dataset",
        "query_family",
        "unit_depth",
        "unit_kind",
        "claim_role",
        "subtask_eligible",
        "positive_oracle_units",
        "best_budget30_unit_policy",
        "best_budget30_positive_unit_f1",
        "operation_stack_budget30_positive_unit_recall",
        "operation_stack_budget30_positive_unit_f1",
        "operation_stack_groups_to_50pct_positive_units",
        "operation_stack_budget30_spillover",
        "operation_stack_depth_gap_sessions",
        "fixed_session_budget30_positive_unit_recall",
        "raw_action_budget30_positive_unit_recall",
        "positive_groups_median_units_per_group",
        "action",
    ]
    write_csv(out_dir / "task-depth-cards.csv", report["task_cards"], card_fields)
    summary_fields = [
        "policy",
        "unit_depth",
        "rows",
        "tasks",
        "median_top5_unit_work",
        "median_top5_positive_unit_recall",
        "median_budget30_positive_unit_recall",
        "median_budget30_positive_unit_f1",
        "median_groups_to_50pct_positive_units",
        "median_budget30_spillover_operation_fraction",
        "median_budget30_positive_session_without_unit_hit",
    ]
    write_csv(out_dir / "policy-depth-summary.csv", report["policy_summary"], summary_fields)
    (out_dir / "oracle-depth-adequacy-report.md").write_text(render_markdown(report), encoding="utf-8")
    (out_dir / "index.html").write_text(render_html(report), encoding="utf-8")


def main() -> None:
    start = time.perf_counter()
    args = parse_args()
    out_dir = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    source_paths = [
        SCALECUA_OPERATIONS,
        OUT_ROOT / "operation-sequence-adequacy-r339" / "sequence-adequacy-report.json",
        OUT_ROOT / "operation-profile-accuracy-r320" / "profile-accuracy-report.json",
        *(task["operation_file"] for task in r300.TASKS),
    ]
    source_status = ensure_sources_tracked_clean(source_paths)
    matrix, policy_rows = evaluate_policies()
    comparisons = compare_default(policy_rows)
    cards = task_cards(policy_rows)
    report = {
        "run_id": RUN_ID,
        "status": "pass",
        "commit": git_output(["rev-parse", "HEAD"]),
        "elapsed_s": round(time.perf_counter() - start, 3),
        "source_status": source_status,
        "oracle_depth_matrix": matrix,
        "policy_rows": round_value(policy_rows),
        "policy_summary": round_value(policy_summary(policy_rows)),
        "comparisons": round_value(comparisons),
        "task_cards": round_value(cards),
        "claim_summary": round_value(claim_summary(matrix, policy_rows, comparisons)),
        "non_claims": [
            "This is not a human or agent analyst study.",
            "This does not fetch, sync, create, or relabel datasets.",
            "This does not claim automatic discovery of all intent boundaries.",
            "Positive-run units are derived proxy episodes, not human intent annotations.",
            "ScaleCUA history_depth is context-only in this tracked sample and excluded from accuracy claims.",
            "Session-level labels do not prove subtask-boundary recovery.",
        ],
    }
    write_outputs(out_dir, report)
    print(json.dumps({"status": "pass", "report": rel(out_dir / "oracle-depth-adequacy-report.json")}, sort_keys=True))


if __name__ == "__main__":
    main()
