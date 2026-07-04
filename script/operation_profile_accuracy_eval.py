#!/usr/bin/env python3
"""R320: score profiler localization/ranking accuracy on real labeled traces.

R320 treats profile outputs as ranked localization results.  It does not fetch
or create datasets.  It reuses the existing public labeled operation JSONL from
R288-R291/R300, folds each task through several operation-stack views, ranks
the resulting groups with visible-field policies, and scores the ranking with
hidden labels only after ranking.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
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
DEFAULT_OUT_DIR = OUT_ROOT / "operation-profile-accuracy-r320"

sys.path.insert(0, str(Path(__file__).resolve().parent))
import operation_analyst_ranking_eval as r302  # noqa: E402
import operation_query_utility_eval as r300  # noqa: E402


VIEWS = [
    "flat",
    "fixed_session",
    "dataset_native",
    "raw_action_stack",
    "operation_stack",
    "label_drilldown",
]
RANKERS = ["width", "visible_risk", "query_aware", "oracle_upper_bound"]
VISIBLE_RANKERS = ["width", "visible_risk", "query_aware"]
TOP_K_VALUES = [1, 3, 5, 10]
OPERATION_BUDGETS = [0.05, 0.10, 0.20, 0.30, 0.50]
HIGH_LIFT_THRESHOLD = 1.5
PRIMARY_POLICIES = [
    ("flat", "width"),
    ("fixed_session", "query_aware"),
    ("dataset_native", "query_aware"),
    ("raw_action_stack", "query_aware"),
    ("operation_stack", "width"),
    ("operation_stack", "query_aware"),
    ("operation_stack", "oracle_upper_bound"),
    ("label_drilldown", "oracle_upper_bound"),
]
HIDDEN_FIELDS = set(r302.HIDDEN_FIELDS) | {
    "target_positive",
    "problem_oracle",
    "problem_value",
    "looping",
    "side_effect",
    "safety",
    "step_correct",
    "step_redundant",
    "group_position",
    "human_group",
    "group_index",
    "group_size",
    "group_pattern",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--high-lift-threshold", type=float, default=HIGH_LIFT_THRESHOLD)
    return parser.parse_args()


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return str(path.resolve())


def load_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as file:
        return json.load(file)


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


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


def git_check(description: str, args: list[str], path: Path) -> None:
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


def ensure_sources_tracked_clean(paths: list[Path]) -> None:
    for path in paths:
        if not path.exists():
            raise SystemExit(f"missing source artifact {rel(path)}")
        git_check("source artifact is not git-tracked", ["ls-files", "--error-unmatch"], path)
        git_check("source artifact has unstaged changes", ["diff", "--quiet"], path)
        git_check("source artifact has staged changes", ["diff", "--cached", "--quiet"], path)


def round_value(value: Any) -> Any:
    if isinstance(value, float):
        if math.isinf(value):
            return "inf"
        if math.isnan(value):
            return None
        return round(value, 4)
    if isinstance(value, dict):
        return {key: round_value(child) for key, child in value.items()}
    if isinstance(value, list):
        return [round_value(child) for child in value]
    return value


def median_or_none(values: list[float]) -> float | None:
    return float(median(values)) if values else None


def mean_or_none(values: list[float]) -> float | None:
    return float(mean(values)) if values else None


def safe_ratio(left: float | int | None, right: float | int | None) -> float | None:
    if left is None or right is None:
        return None
    if right == 0:
        return None if left == 0 else float("inf")
    return float(left) / float(right)


def f1_score(precision: float, recall: float) -> float:
    if precision + recall == 0:
        return 0.0
    return 2 * precision * recall / (precision + recall)


def stack_label(fields: dict[str, str], stack: list[str]) -> str:
    return ";".join(f"{field}:{fields.get(field, 'unknown')}" for field in stack)


def stack_frames(label: str) -> list[dict[str, str]]:
    frames = []
    for part in label.split(";"):
        if ":" in part:
            field, value = part.split(":", 1)
        else:
            field, value = "frame", part
        frames.append({"field": field, "value": value})
    return frames


def stack_hash(label: str) -> str:
    return hashlib.sha1(label.encode("utf-8")).hexdigest()[:12]


def dataset_native_stack(task: dict[str, Any]) -> list[str]:
    dataset = task["dataset"]
    if dataset == "agent-reward-bench":
        return ["analysis_task", "dataset", "benchmark", "environment"]
    if dataset == "satraj-os-safety":
        return ["analysis_task", "dataset", "benchmark", "category", "environment"]
    if dataset == "agentnet":
        return [
            "analysis_task",
            "dataset",
            "benchmark",
            "domain",
            "task_difficulty",
            "environment",
        ]
    if dataset == "osworld-human":
        return ["analysis_task", "dataset", "benchmark", "app", "environment"]
    return ["analysis_task", "dataset", "benchmark", "environment"]


def stack_for_view(task: dict[str, Any], view: str) -> list[str]:
    if view == "flat":
        return ["analysis_task", "dataset"]
    if view == "fixed_session":
        return ["analysis_task", "dataset", "session"]
    if view == "dataset_native":
        return dataset_native_stack(task)
    if view == "raw_action_stack":
        return ["analysis_task", "dataset", "tool", "action", "status"]
    if view == "operation_stack":
        return list(task["semantic_stack"])
    if view == "label_drilldown":
        return list(task["label_stack"])
    raise ValueError(f"unknown view {view}")


def view_uses_hidden_fields(view: str) -> bool:
    return view == "label_drilldown"


def ranker_uses_hidden_fields(ranker: str) -> bool:
    return ranker == "oracle_upper_bound"


def policy_uses_hidden_fields(view: str, ranker: str) -> bool:
    return view_uses_hidden_fields(view) or ranker_uses_hidden_fields(ranker)


def group_task_view(task: dict[str, Any], view: str) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    operations = r300.load_task_operations(task)
    stack = stack_for_view(task, view)
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for operation in operations:
        grouped[stack_label(operation["fields"], stack)].append(operation)

    groups = []
    total_ops = 0
    total_positive = 0
    for label, rows in grouped.items():
        operations_in_group = sum(int(operation["value"]) for operation in rows)
        positives = sum(
            int(operation["value"])
            for operation in rows
            if operation["fields"].get("target_positive") == "positive"
        )
        sessions = sorted({operation["fields"].get("session", "unknown") for operation in rows})
        total_ops += operations_in_group
        total_positive += positives
        groups.append(
            {
                "group_id": stack_hash(f"{view}:{label}"),
                "stack": label,
                "stack_frames": stack_frames(label),
                "operations": operations_in_group,
                "positives": positives,
                "positive_rate": positives / operations_in_group if operations_in_group else 0.0,
                "sessions": len(sessions),
                "session_examples": [stack_hash(session) for session in sessions[:5]],
                "features": r302.visible_features(rows),
            }
        )

    summary = {
        "operations": total_ops,
        "positives": total_positive,
        "prevalence": total_positive / total_ops if total_ops else 0.0,
        "groups": len(groups),
        "positive_groups": sum(1 for group in groups if group["positives"] > 0),
        "stack": stack,
    }
    return groups, summary


def rank_groups(
    task: dict[str, Any],
    groups: list[dict[str, Any]],
    ranker: str,
) -> list[dict[str, Any]]:
    ranked = sorted(
        groups,
        key=lambda group: (
            r302.rank_score(group, task, ranker),
            group["operations"] if ranker != "oracle_upper_bound" else group["positives"],
            group["group_id"],
        ),
        reverse=True,
    )
    return ranked


def score_selection(
    selected: list[dict[str, Any]],
    summary: dict[str, Any],
    label: str,
) -> dict[str, Any]:
    inspected_ops = sum(group["operations"] for group in selected)
    positive_ops = sum(group["positives"] for group in selected)
    total_ops = summary["operations"]
    total_pos = summary["positives"]
    prevalence = summary["prevalence"]
    precision = positive_ops / inspected_ops if inspected_ops else 0.0
    recall = positive_ops / total_pos if total_pos else 0.0
    return {
        f"{label}_groups": len(selected),
        f"{label}_work": inspected_ops / total_ops if total_ops else 0.0,
        f"{label}_positive_operations": positive_ops,
        f"{label}_precision": precision,
        f"{label}_recall": recall,
        f"{label}_f1": f1_score(precision, recall),
        f"{label}_lift": precision / prevalence if prevalence else 0.0,
        f"{label}_positive_hit": positive_ops > 0,
        f"{label}_group_precision": (
            sum(1 for group in selected if group["positives"] > 0) / len(selected)
            if selected
            else 0.0
        ),
    }


def select_for_operation_budget(
    ranked: list[dict[str, Any]], summary: dict[str, Any], budget: float
) -> list[dict[str, Any]]:
    limit = summary["operations"] * budget
    selected = []
    inspected = 0
    for group in ranked:
        next_inspected = inspected + group["operations"]
        if next_inspected > limit + 1e-12:
            continue
        selected.append(group)
        inspected = next_inspected
    return selected


def average_precision(ranked: list[dict[str, Any]], total_positive: int) -> float:
    if total_positive <= 0:
        return 0.0
    cumulative_ops = 0
    cumulative_pos = 0
    weighted_precision = 0.0
    for group in ranked:
        cumulative_ops += group["operations"]
        cumulative_pos += group["positives"]
        if group["positives"] > 0:
            weighted_precision += (cumulative_pos / cumulative_ops) * group["positives"]
    return weighted_precision / total_positive


def ndcg_at_all(ranked: list[dict[str, Any]]) -> float:
    def dcg(items: list[dict[str, Any]]) -> float:
        total = 0.0
        for index, group in enumerate(items, 1):
            relevance = float(group["positives"])
            if relevance:
                total += relevance / math.log2(index + 1)
        return total

    actual = dcg(ranked)
    ideal = dcg(sorted(ranked, key=lambda group: group["positives"], reverse=True))
    return actual / ideal if ideal else 0.0


def first_relevant_metrics(
    ranked: list[dict[str, Any]],
    summary: dict[str, Any],
    high_lift_threshold: float,
) -> dict[str, Any]:
    cumulative_ops = 0
    first_positive = None
    first_high_lift = None
    prevalence = summary["prevalence"]
    for index, group in enumerate(ranked, 1):
        cumulative_ops += group["operations"]
        lift = (group["positive_rate"] / prevalence) if prevalence else 0.0
        if first_positive is None and group["positives"] > 0:
            first_positive = {
                "rank": index,
                "work": cumulative_ops / summary["operations"],
                "group_id": group["group_id"],
                "positive_rate": group["positive_rate"],
                "lift": lift,
            }
        if first_high_lift is None and group["positives"] > 0 and lift >= high_lift_threshold:
            first_high_lift = {
                "rank": index,
                "work": cumulative_ops / summary["operations"],
                "group_id": group["group_id"],
                "positive_rate": group["positive_rate"],
                "lift": lift,
            }
        if first_positive is not None and first_high_lift is not None:
            break
    return {
        "rank_to_first_positive": first_positive["rank"] if first_positive else None,
        "work_to_first_positive": first_positive["work"] if first_positive else None,
        "mrr_positive": 1.0 / first_positive["rank"] if first_positive else 0.0,
        "first_positive_group_id": first_positive["group_id"] if first_positive else None,
        "rank_to_first_high_lift": first_high_lift["rank"] if first_high_lift else None,
        "work_to_first_high_lift": first_high_lift["work"] if first_high_lift else None,
        "mrr_high_lift": 1.0 / first_high_lift["rank"] if first_high_lift else 0.0,
        "first_high_lift_group_id": first_high_lift["group_id"] if first_high_lift else None,
    }


def recall_target_metrics(ranked: list[dict[str, Any]], summary: dict[str, Any], target: float) -> dict[str, Any]:
    if summary["positives"] <= 0 or summary["operations"] <= 0:
        return {"groups_to_recall": None, "work_to_recall": None}
    cumulative_ops = 0
    cumulative_pos = 0
    needed = summary["positives"] * target
    for index, group in enumerate(ranked, 1):
        cumulative_ops += group["operations"]
        cumulative_pos += group["positives"]
        if cumulative_pos >= needed:
            return {
                "groups_to_recall": index,
                "work_to_recall": cumulative_ops / summary["operations"],
            }
    return {"groups_to_recall": len(ranked), "work_to_recall": 1.0}


def top_group_snapshot(
    ranked: list[dict[str, Any]],
    summary: dict[str, Any],
    high_lift_threshold: float,
    limit: int = 3,
) -> list[dict[str, Any]]:
    prevalence = summary["prevalence"]
    rows = []
    for index, group in enumerate(ranked[:limit], 1):
        lift = (group["positive_rate"] / prevalence) if prevalence else 0.0
        rows.append(
            {
                "rank": index,
                "group_id": group["group_id"],
                "operations": group["operations"],
                "positive_operations": group["positives"],
                "positive_rate": group["positive_rate"],
                "lift": lift,
                "high_lift": group["positives"] > 0 and lift >= high_lift_threshold,
                "sessions": group["sessions"],
                "stack_frames": group["stack_frames"],
                "visible_features": group["features"],
            }
        )
    return rows


def score_policy(
    task: dict[str, Any],
    view: str,
    ranker: str,
    groups: list[dict[str, Any]],
    summary: dict[str, Any],
    high_lift_threshold: float,
) -> dict[str, Any]:
    ranked = rank_groups(task, groups, ranker)
    row: dict[str, Any] = {
        "task": task["id"],
        "dataset": task["dataset"],
        "query_family": task["query_family"],
        "problem": task["problem"],
        "view": view,
        "ranker": ranker,
        "uses_hidden_fields": policy_uses_hidden_fields(view, ranker),
        "operations": summary["operations"],
        "positives": summary["positives"],
        "prevalence": summary["prevalence"],
        "groups": summary["groups"],
        "positive_groups": summary["positive_groups"],
        "positive_group_fraction": summary["positive_groups"] / summary["groups"]
        if summary["groups"]
        else 0.0,
        "stack_fields": summary["stack"],
        "average_precision": average_precision(ranked, summary["positives"]),
        "ndcg": ndcg_at_all(ranked),
    }
    row.update(first_relevant_metrics(ranked, summary, high_lift_threshold))
    recall_50 = recall_target_metrics(ranked, summary, 0.50)
    row["groups_to_50pct_recall"] = recall_50["groups_to_recall"]
    row["work_to_50pct_recall"] = recall_50["work_to_recall"]
    for k in TOP_K_VALUES:
        row.update(score_selection(ranked[:k], summary, f"top{k}"))
    for budget in OPERATION_BUDGETS:
        selected = select_for_operation_budget(ranked, summary, budget)
        row.update(score_selection(selected, summary, f"budget{int(budget * 100)}"))
    row["top_groups"] = top_group_snapshot(ranked, summary, high_lift_threshold, 3)
    return row


def policy_key(view: str, ranker: str) -> str:
    return f"{view}:{ranker}"


def summarize_policy_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    by_policy: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_policy[(row["view"], row["ranker"])].append(row)
    summary = {}
    metrics = [
        "average_precision",
        "ndcg",
        "top5_precision",
        "top5_recall",
        "top5_f1",
        "top5_work",
        "top5_lift",
        "budget30_recall",
        "budget30_f1",
        "budget30_work",
        "work_to_first_positive",
        "work_to_first_high_lift",
        "mrr_positive",
        "mrr_high_lift",
        "groups",
        "positive_groups",
        "groups_to_50pct_recall",
        "work_to_50pct_recall",
    ]
    for (view, ranker), items in sorted(by_policy.items()):
        values = {}
        for metric in metrics:
            numeric = [float(item[metric]) for item in items if item.get(metric) is not None]
            values[f"median_{metric}"] = median_or_none(numeric)
            values[f"mean_{metric}"] = mean_or_none(numeric)
        summary[policy_key(view, ranker)] = {
            "view": view,
            "ranker": ranker,
            "tasks": len(items),
            "uses_hidden_fields": policy_uses_hidden_fields(view, ranker),
            **values,
        }
    return round_value(summary)


def paired_comparisons(rows: list[dict[str, Any]]) -> dict[str, Any]:
    by_key = {(row["task"], row["view"], row["ranker"]): row for row in rows}
    tasks = sorted({row["task"] for row in rows})
    pairs = {
        "operation_stack_query_aware_vs_flat_width": (
            ("operation_stack", "query_aware"),
            ("flat", "width"),
        ),
        "operation_stack_query_aware_vs_fixed_session_query_aware": (
            ("operation_stack", "query_aware"),
            ("fixed_session", "query_aware"),
        ),
        "operation_stack_query_aware_vs_dataset_native_query_aware": (
            ("operation_stack", "query_aware"),
            ("dataset_native", "query_aware"),
        ),
        "operation_stack_query_aware_vs_raw_action_query_aware": (
            ("operation_stack", "query_aware"),
            ("raw_action_stack", "query_aware"),
        ),
        "operation_stack_query_aware_vs_operation_stack_width": (
            ("operation_stack", "query_aware"),
            ("operation_stack", "width"),
        ),
        "operation_stack_query_aware_vs_operation_stack_oracle": (
            ("operation_stack", "query_aware"),
            ("operation_stack", "oracle_upper_bound"),
        ),
    }
    metrics = [
        "average_precision",
        "ndcg",
        "top5_precision",
        "top5_recall",
        "top5_f1",
        "top5_work",
        "budget30_recall",
        "work_to_first_positive",
        "groups",
    ]
    output = {}
    for name, (left_key, right_key) in pairs.items():
        pair_rows = []
        metric_summary = {}
        for task in tasks:
            left = by_key.get((task, *left_key))
            right = by_key.get((task, *right_key))
            if not left or not right:
                continue
            task_row = {"task": task, "left": policy_key(*left_key), "right": policy_key(*right_key)}
            for metric in metrics:
                left_value = left.get(metric)
                right_value = right.get(metric)
                delta = (
                    float(left_value) - float(right_value)
                    if left_value is not None and right_value is not None
                    else None
                )
                ratio = safe_ratio(left_value, right_value)
                task_row[f"{metric}_left"] = left_value
                task_row[f"{metric}_right"] = right_value
                task_row[f"{metric}_delta"] = delta
                task_row[f"{metric}_ratio"] = ratio
            pair_rows.append(task_row)
        for metric in metrics:
            deltas = [row[f"{metric}_delta"] for row in pair_rows if row[f"{metric}_delta"] is not None]
            ratios = [row[f"{metric}_ratio"] for row in pair_rows if row[f"{metric}_ratio"] is not None]
            lower_is_better = metric in {"top5_work", "work_to_first_positive", "groups"}
            if lower_is_better:
                improved = sum(1 for delta in deltas if delta < 0)
                worse = sum(1 for delta in deltas if delta > 0)
            else:
                improved = sum(1 for delta in deltas if delta > 0)
                worse = sum(1 for delta in deltas if delta < 0)
            metric_summary[metric] = {
                "median_delta": median_or_none(deltas),
                "median_ratio": median_or_none(ratios),
                "improved_tasks": improved,
                "tied_tasks": sum(1 for delta in deltas if delta == 0),
                "worse_tasks": worse,
                "lower_is_better": lower_is_better,
            }
        output[name] = {"tasks": len(pair_rows), "metrics": round_value(metric_summary)}
    return output


def dominates(left: dict[str, Any], right: dict[str, Any]) -> bool:
    eps = 1e-12
    at_least = (
        left["recall"] >= right["recall"] - eps
        and left["lift"] >= right["lift"] - eps
        and left["precision"] >= right["precision"] - eps
        and left["work"] <= right["work"] + eps
        and left["groups"] <= right["groups"] + eps
    )
    strict = (
        left["recall"] > right["recall"] + eps
        or left["lift"] > right["lift"] + eps
        or left["precision"] > right["precision"] + eps
        or left["work"] < right["work"] - eps
        or left["groups"] < right["groups"] - eps
    )
    return at_least and strict


def pareto_frontier(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        row
        for row in candidates
        if not any(dominates(other, row) for other in candidates if other is not row)
    ]


def build_pareto(rows: list[dict[str, Any]]) -> dict[str, Any]:
    candidates = []
    for row in rows:
        if row["uses_hidden_fields"]:
            continue
        for k in TOP_K_VALUES:
            candidates.append(
                {
                    "task": row["task"],
                    "dataset": row["dataset"],
                    "view": row["view"],
                    "ranker": row["ranker"],
                    "budget": f"top{k}",
                    "recall": row[f"top{k}_recall"],
                    "precision": row[f"top{k}_precision"],
                    "lift": row[f"top{k}_lift"],
                    "work": row[f"top{k}_work"],
                    "groups": row[f"top{k}_groups"],
                }
            )
        for budget in OPERATION_BUDGETS:
            label = f"budget{int(budget * 100)}"
            candidates.append(
                {
                    "task": row["task"],
                    "dataset": row["dataset"],
                    "view": row["view"],
                    "ranker": row["ranker"],
                    "budget": label,
                    "recall": row[f"{label}_recall"],
                    "precision": row[f"{label}_precision"],
                    "lift": row[f"{label}_lift"],
                    "work": row[f"{label}_work"],
                    "groups": row[f"{label}_groups"],
                }
            )
    task_rows = []
    frontier_rows = []
    for task in sorted({row["task"] for row in candidates}):
        scoped = [row for row in candidates if row["task"] == task]
        frontier = pareto_frontier(scoped)
        frontier_rows.extend(frontier)
        views = sorted({row["view"] for row in frontier})
        best_f1_source = max(
            [row for row in rows if row["task"] == task and not row["uses_hidden_fields"]],
            key=lambda row: (row["top5_f1"], row["average_precision"], -row["top5_work"]),
        )
        best_recall_under_30 = max(
            [
                row
                for row in candidates
                if row["task"] == task and row["work"] <= 0.30 + 1e-12
            ]
            or scoped,
            key=lambda row: (row["recall"], row["lift"], row["precision"], -row["work"]),
        )
        task_rows.append(
            {
                "task": task,
                "frontier_points": len(frontier),
                "views_on_frontier": views,
                "operation_stack_on_frontier": any(
                    row["view"] == "operation_stack" for row in frontier
                ),
                "fixed_session_on_frontier": any(
                    row["view"] == "fixed_session" for row in frontier
                ),
                "flat_on_frontier": any(row["view"] == "flat" for row in frontier),
                "best_visible_top5_f1": {
                    "view": best_f1_source["view"],
                    "ranker": best_f1_source["ranker"],
                    "top5_f1": best_f1_source["top5_f1"],
                    "top5_recall": best_f1_source["top5_recall"],
                    "top5_work": best_f1_source["top5_work"],
                },
                "best_recall_under_30pct_work": {
                    "view": best_recall_under_30["view"],
                    "ranker": best_recall_under_30["ranker"],
                    "budget": best_recall_under_30["budget"],
                    "recall": best_recall_under_30["recall"],
                    "work": best_recall_under_30["work"],
                    "lift": best_recall_under_30["lift"],
                },
            }
        )
    summary = {
        "candidate_points": len(candidates),
        "frontier_points": len(frontier_rows),
        "tasks": len(task_rows),
        "operation_stack_on_frontier": f"{sum(row['operation_stack_on_frontier'] for row in task_rows)}/{len(task_rows)}",
        "fixed_session_on_frontier": f"{sum(row['fixed_session_on_frontier'] for row in task_rows)}/{len(task_rows)}",
        "flat_on_frontier": f"{sum(row['flat_on_frontier'] for row in task_rows)}/{len(task_rows)}",
        "operation_stack_best_visible_top5_f1": f"{sum(row['best_visible_top5_f1']['view'] == 'operation_stack' for row in task_rows)}/{len(task_rows)}",
        "operation_stack_best_recall_under_30pct_work": f"{sum(row['best_recall_under_30pct_work']['view'] == 'operation_stack' for row in task_rows)}/{len(task_rows)}",
    }
    return {
        "summary": summary,
        "task_frontiers": round_value(task_rows),
        "frontier_candidates": round_value(frontier_rows),
    }


def task_policy(rows: list[dict[str, Any]], task: str, view: str, ranker: str) -> dict[str, Any]:
    for row in rows:
        if row["task"] == task and row["view"] == view and row["ranker"] == ranker:
            return row
    raise KeyError((task, view, ranker))


def visible_best_for_task(rows: list[dict[str, Any]], task: str) -> dict[str, Any]:
    scoped = [row for row in rows if row["task"] == task and not row["uses_hidden_fields"]]
    return max(scoped, key=lambda row: (row["top5_f1"], row["average_precision"], -row["top5_work"]))


def insight_for_task(rows: list[dict[str, Any]], task_info: dict[str, Any]) -> dict[str, Any]:
    task = task_info["id"]
    best = visible_best_for_task(rows, task)
    op = task_policy(rows, task, "operation_stack", "query_aware")
    fixed = task_policy(rows, task, "fixed_session", "query_aware")
    raw = task_policy(rows, task, "raw_action_stack", "query_aware")
    width = task_policy(rows, task, "operation_stack", "width")
    oracle = task_policy(rows, task, "operation_stack", "oracle_upper_bound")
    flat = task_policy(rows, task, "flat", "width")
    mapping_gain_f1 = op["top5_f1"] - raw["top5_f1"]
    ranking_gain_ap = op["average_precision"] - width["average_precision"]
    oracle_gap_ap = oracle["average_precision"] - op["average_precision"]
    fixed_work_advantage = (
        (op["work_to_first_positive"] or 1.0) - (fixed["work_to_first_positive"] or 1.0)
    )
    notes = []
    if best["view"] == "operation_stack":
        notes.append("operation_stack is the best visible top-5 F1 policy for this task")
    elif fixed["work_to_first_positive"] is not None and (
        op["work_to_first_positive"] is None
        or fixed["work_to_first_positive"] < op["work_to_first_positive"]
    ):
        notes.append("fixed_session finds the first positive with less work; use it as drilldown")
    if mapping_gain_f1 > 0.02:
        notes.append("phase/repeat/environment mapping improves top-5 localization over raw action/status")
    elif mapping_gain_f1 < -0.02:
        notes.append("raw action/status beats the current mapped stack; tune stack depth for this query")
    else:
        notes.append("mapping and raw action stack are close; ranker choice matters more than fields")
    if ranking_gain_ap > 0.02:
        notes.append("query-aware visible ranking improves AP over flamegraph-width ranking")
    elif ranking_gain_ap < -0.02:
        notes.append("width ranking is competitive; query heuristic needs calibration")
    if oracle_gap_ap > 0.15:
        notes.append("oracle upper bound leaves substantial ranker headroom")
    if flat["top5_work"] >= 0.99:
        notes.append("flat summary finds prevalent positives only by inspecting the whole task")
    recommendation = "; ".join(notes)
    useful_fields = op["stack_fields"]
    if task == "agentreward_looping":
        action = "Keep repeat_signal in the stack, but add prevalence-aware ranking because looping positives are common."
    elif task == "agentreward_side_effect":
        action = "Increase weight on write/input actions or use a deeper side-effect mapping before ranking."
    elif task == "satraj_unsafe":
        action = "Use environment + phase + action stack fields; prioritize risky environments and write actions."
    elif task.startswith("agentnet_"):
        action = "Use desktop environment + phase + repeat/action fields, then drill into fixed sessions for examples."
    elif task == "osworld_group_start":
        action = "Use group-depth or boundary-derived fields for higher recall; action-depth alone fragments starts."
    else:
        action = "Compare operation_stack and fixed_session on the Pareto frontier before selecting a view."
    return round_value(
        {
            "task": task,
            "dataset": task_info["dataset"],
            "query_family": task_info["query_family"],
            "best_visible_policy": policy_key(best["view"], best["ranker"]),
            "best_visible_top5_f1": best["top5_f1"],
            "operation_stack_top5_precision": op["top5_precision"],
            "operation_stack_top5_recall": op["top5_recall"],
            "operation_stack_top5_work": op["top5_work"],
            "fixed_session_top5_recall": fixed["top5_recall"],
            "fixed_session_top5_work": fixed["top5_work"],
            "mapping_gain_top5_f1_vs_raw_action": mapping_gain_f1,
            "query_aware_ap_gain_vs_width": ranking_gain_ap,
            "oracle_ap_gap": oracle_gap_ap,
            "fixed_session_first_positive_work_advantage": fixed_work_advantage,
            "useful_stack_fields": ",".join(useful_fields),
            "recommendation": recommendation,
            "optimization_action": action,
        }
    )


def build_task_accuracy(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    task_rows = []
    for task in r300.TASKS:
        op = task_policy(rows, task["id"], "operation_stack", "query_aware")
        fixed = task_policy(rows, task["id"], "fixed_session", "query_aware")
        flat = task_policy(rows, task["id"], "flat", "width")
        raw = task_policy(rows, task["id"], "raw_action_stack", "query_aware")
        oracle = task_policy(rows, task["id"], "operation_stack", "oracle_upper_bound")
        task_rows.append(
            round_value(
                {
                    "task": task["id"],
                    "dataset": task["dataset"],
                    "query_family": task["query_family"],
                    "operations": op["operations"],
                    "positives": op["positives"],
                    "prevalence": op["prevalence"],
                    "operation_stack_ap": op["average_precision"],
                    "fixed_session_ap": fixed["average_precision"],
                    "flat_ap": flat["average_precision"],
                    "raw_action_ap": raw["average_precision"],
                    "oracle_ap": oracle["average_precision"],
                    "operation_stack_ndcg": op["ndcg"],
                    "operation_stack_top5_precision": op["top5_precision"],
                    "operation_stack_top5_recall": op["top5_recall"],
                    "operation_stack_top5_f1": op["top5_f1"],
                    "operation_stack_top5_work": op["top5_work"],
                    "fixed_session_top5_precision": fixed["top5_precision"],
                    "fixed_session_top5_recall": fixed["top5_recall"],
                    "fixed_session_top5_work": fixed["top5_work"],
                    "flat_top1_precision": flat["top1_precision"],
                    "flat_top1_recall": flat["top1_recall"],
                    "flat_top1_work": flat["top1_work"],
                    "operation_stack_budget30_recall": op["budget30_recall"],
                    "fixed_session_budget30_recall": fixed["budget30_recall"],
                    "operation_stack_work_to_first_positive": op["work_to_first_positive"],
                    "fixed_session_work_to_first_positive": fixed["work_to_first_positive"],
                    "operation_stack_groups": op["groups"],
                    "fixed_session_groups": fixed["groups"],
                    "raw_action_groups": raw["groups"],
                }
            )
        )
    return task_rows


def primary_findings(report: dict[str, Any]) -> list[str]:
    summary = report["policy_summary"]
    comparisons = report["paired_comparisons"]
    op = summary["operation_stack:query_aware"]
    flat = summary["flat:width"]
    fixed = summary["fixed_session:query_aware"]
    raw_pair = comparisons["operation_stack_query_aware_vs_raw_action_query_aware"]["metrics"]
    fixed_pair = comparisons[
        "operation_stack_query_aware_vs_fixed_session_query_aware"
    ]["metrics"]
    width_pair = comparisons["operation_stack_query_aware_vs_operation_stack_width"]["metrics"]
    return [
        (
            "Operation-stack query-aware profiling inspects median "
            f"{op['median_top5_work']:.2%} of operations in top-5 groups, versus "
            f"{flat['median_top5_work']:.2%} for flat summaries."
        ),
        (
            "Against fixed-session query-aware drilldown, operation stacks improve top-5 "
            f"recall on {fixed_pair['top5_recall']['improved_tasks']}/6 tasks and reduce "
            f"group fragmentation from median {fixed['median_groups']} to "
            f"{op['median_groups']} groups."
        ),
        (
            "Mapping/tagging matters but is task-sensitive: operation stacks beat the raw "
            "action/status stack on top-5 F1 in "
            f"{raw_pair['top5_f1']['improved_tasks']}/6 tasks."
        ),
        (
            "Query-aware visible ranking improves AP over width-only operation-stack ranking "
            f"on {width_pair['average_precision']['improved_tasks']}/6 tasks; top-5 F1 and "
            "work still expose calibration and prevalence counterexamples."
        ),
        (
            "The Pareto analysis keeps operation stacks on the non-oracle frontier for "
            f"{report['pareto']['summary']['operation_stack_on_frontier']} tasks; flat and "
            "fixed-session remain useful counterpoints rather than defeated baselines."
        ),
    ]


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fields, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: round_value(row.get(field)) for field in fields})


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# R320 Profile Accuracy and Actionability",
        "",
        "R320 scores profiler outputs as ranked localization results on existing public labeled agent traces.",
        "It does not fetch, sync, or create datasets; hidden labels are used only after ranking.",
        "",
        "## Primary Findings",
        "",
    ]
    lines.extend(f"- {finding}" for finding in report["primary_findings"])
    lines.extend(
        [
            "",
            "## Primary Accuracy Table",
            "",
            "| Policy | Hidden? | AP | nDCG | P@5 | R@5 | F1@5 | Work@5 | Recall@30% | WTFP | Groups |",
            "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for view, ranker in PRIMARY_POLICIES:
        key = policy_key(view, ranker)
        row = report["policy_summary"][key]
        lines.append(
            "| {key} | {hidden} | {ap} | {ndcg} | {p5} | {r5} | {f5} | {w5} | {r30} | {wtfp} | {groups} |".format(
                key=key,
                hidden=row["uses_hidden_fields"],
                ap=row["median_average_precision"],
                ndcg=row["median_ndcg"],
                p5=row["median_top5_precision"],
                r5=row["median_top5_recall"],
                f5=row["median_top5_f1"],
                w5=row["median_top5_work"],
                r30=row["median_budget30_recall"],
                wtfp=row["median_work_to_first_positive"],
                groups=row["median_groups"],
            )
        )
    lines.extend(
        [
            "",
            "## Actionable Optimization Insights",
            "",
            "| Task | Best visible policy | Stack/ranker diagnosis | Optimization action |",
            "|---|---|---|---|",
        ]
    )
    for row in report["optimization_insights"]:
        lines.append(
            f"| {row['task']} | {row['best_visible_policy']} | {row['recommendation']} | {row['optimization_action']} |"
        )
    lines.extend(
        [
            "",
            "## Claim Boundary",
            "",
            "- Supports: profiler fidelity/localization, ranking quality, work tradeoffs, fragmentation reduction, and actionability on six real oracle-backed tasks from four public trace families.",
            "- Supports as broader context: the repository already has 15 source conversions; R320 uses the four oracle-rich families as the main accuracy line.",
            "- Does not support: human productivity, human or agent analyst time-to-answer, automatic discovery of all intent boundaries, or full trace-platform ecosystem compatibility.",
        ]
    )
    return "\n".join(lines) + "\n"


def render_html(report: dict[str, Any]) -> str:
    policy_rows = []
    for view, ranker in PRIMARY_POLICIES:
        key = policy_key(view, ranker)
        row = report["policy_summary"][key]
        policy_rows.append(
            "<tr>"
            f"<th>{html.escape(key)}</th>"
            f"<td>{row['uses_hidden_fields']}</td>"
            f"<td>{row['median_average_precision']}</td>"
            f"<td>{row['median_ndcg']}</td>"
            f"<td>{row['median_top5_precision']}</td>"
            f"<td>{row['median_top5_recall']}</td>"
            f"<td>{row['median_top5_f1']}</td>"
            f"<td>{row['median_top5_work']}</td>"
            f"<td>{row['median_budget30_recall']}</td>"
            f"<td>{row['median_work_to_first_positive']}</td>"
            f"<td>{row['median_groups']}</td>"
            "</tr>"
        )
    insight_rows = []
    for row in report["optimization_insights"]:
        insight_rows.append(
            "<tr>"
            f"<th>{html.escape(row['task'])}</th>"
            f"<td>{html.escape(row['best_visible_policy'])}</td>"
            f"<td>{html.escape(row['recommendation'])}</td>"
            f"<td>{html.escape(row['optimization_action'])}</td>"
            "</tr>"
        )
    findings = "".join(f"<li>{html.escape(text)}</li>" for text in report["primary_findings"])
    return f"""<!doctype html>
<meta charset="utf-8">
<title>R320 Profile Accuracy</title>
<style>
body {{ font-family: system-ui, sans-serif; margin: 32px; color: #202124; }}
table {{ border-collapse: collapse; width: 100%; margin: 24px 0; font-size: 13px; }}
th, td {{ border-bottom: 1px solid #d8dee8; padding: 7px 8px; text-align: left; vertical-align: top; }}
th {{ background: #eef2f6; }}
.note {{ max-width: 980px; line-height: 1.45; }}
</style>
<h1>R320 Profile Accuracy and Actionability</h1>
<p class="note">Profiler outputs are scored as ranked localization results on existing public labeled traces. Hidden labels are used only after ranking.</p>
<h2>Primary Findings</h2>
<ul>{findings}</ul>
<h2>Primary Accuracy Table</h2>
<table>
<thead><tr><th>Policy</th><th>Hidden?</th><th>AP</th><th>nDCG</th><th>P@5</th><th>R@5</th><th>F1@5</th><th>Work@5</th><th>Recall@30%</th><th>WTFP</th><th>Groups</th></tr></thead>
<tbody>{''.join(policy_rows)}</tbody>
</table>
<h2>Actionability</h2>
<table>
<thead><tr><th>Task</th><th>Best visible policy</th><th>Diagnosis</th><th>Optimization action</th></tr></thead>
<tbody>{''.join(insight_rows)}</tbody>
</table>
"""


def validate_visible_rank_features() -> dict[str, Any]:
    allowed = {"status", "repeat_signal", "phase", "action", "environment"}
    overlap = sorted(allowed & HIDDEN_FIELDS)
    if overlap:
        raise SystemExit(f"visible rank features overlap hidden fields: {overlap}")
    return {
        "status": "pass",
        "visible_rank_feature_fields": sorted(allowed),
        "hidden_fields": sorted(HIDDEN_FIELDS),
        "overlap": overlap,
    }


def main() -> None:
    start = time.perf_counter()
    args = parse_args()
    out_dir = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    source_paths = sorted({task["operation_file"] for task in r300.TASKS})
    ensure_sources_tracked_clean(source_paths)
    leakage_check = validate_visible_rank_features()

    rows = []
    group_summaries = []
    for task in r300.TASKS:
        for view in VIEWS:
            groups, summary = group_task_view(task, view)
            group_summaries.append(
                {
                    "task": task["id"],
                    "dataset": task["dataset"],
                    "view": view,
                    "operations": summary["operations"],
                    "positives": summary["positives"],
                    "prevalence": summary["prevalence"],
                    "groups": summary["groups"],
                    "positive_groups": summary["positive_groups"],
                    "stack_fields": summary["stack"],
                    "uses_hidden_fields": view_uses_hidden_fields(view),
                }
            )
            for ranker in RANKERS:
                rows.append(
                    score_policy(
                        task,
                        view,
                        ranker,
                        groups,
                        summary,
                        args.high_lift_threshold,
                    )
                )

    policy_summary = summarize_policy_rows(rows)
    task_accuracy = build_task_accuracy(rows)
    insights = [insight_for_task(rows, task) for task in r300.TASKS]
    pareto = build_pareto(rows)
    comparisons = paired_comparisons(rows)
    elapsed = time.perf_counter() - start
    totals = {
        "tasks": len(r300.TASKS),
        "datasets": len({task["dataset"] for task in r300.TASKS}),
        "task_operations": sum(row["operations"] for row in task_accuracy),
        "positive_operations": sum(row["positives"] for row in task_accuracy),
        "policy_scores": len(rows),
        "group_views": len(group_summaries),
    }
    report = {
        "run_id": "R320",
        "schema": "agentsight.profile-accuracy.v1",
        "purpose": "profiler fidelity, ranking/localization accuracy, actionability, and baseline tradeoff on real labeled agent traces",
        "input_policy": {
            "dataset_sync": "none",
            "dataset_creation": "none",
            "source_operations": [rel(path) for path in source_paths],
            "hidden_label_use": "labels are used only after groups are ranked; label_drilldown and oracle_upper_bound are marked hidden upper bounds",
        },
        "profiler_abstractions": ["operation", "operation stack"],
        "views": VIEWS,
        "rankers": RANKERS,
        "primary_policies": [policy_key(view, ranker) for view, ranker in PRIMARY_POLICIES],
        "metrics": {
            "fidelity_accuracy": [
                "precision@k",
                "recall@operation-budget",
                "F1@k",
                "average precision / AUPRC-style block AP",
                "nDCG over positive operation counts",
                "work-to-first-positive",
            ],
            "fragmentation": [
                "group count",
                "positive group count",
                "groups/work to 50% positive recall",
            ],
            "actionability": [
                "best visible policy per task",
                "mapping/tagging gain versus raw action stack",
                "query-aware gain versus width ranker",
                "oracle headroom",
            ],
        },
        "totals": totals,
        "leakage_check": leakage_check,
        "policy_summary": policy_summary,
        "paired_comparisons": comparisons,
        "pareto": pareto,
        "task_accuracy": task_accuracy,
        "optimization_insights": insights,
        "claim_scope": {
            "supports": "operation/operation-stack profiling can localize and rank labeled failures, quality problems, and semantic boundaries on real labeled traces with useful work/fragmentation tradeoffs",
            "supports_with_scope": "operation-stack query-aware ranking is a strong visible policy but not universally dominant; fixed-session and flat remain counterpoints on some metrics",
            "does_not_support": [
                "human productivity or time-to-answer",
                "automatic discovery of all intent boundaries",
                "complete compatibility with OpenTelemetry, Phoenix, LangSmith, Langfuse, or Perfetto",
                "single-view dominance on every task and metric",
            ],
        },
        "reproducibility": {
            "commit": git_output(["rev-parse", "HEAD"]),
            "elapsed_seconds": round(elapsed, 4),
            "source_artifacts_tracked_clean": True,
            "network_access_required": False,
        },
    }
    report["primary_findings"] = primary_findings(report)

    report = round_value(report)
    report_path = out_dir / "profile-accuracy-report.json"
    markdown_path = out_dir / "profile-accuracy-report.md"
    html_path = out_dir / "index.html"
    policy_csv = out_dir / "policy-scores.csv"
    task_csv = out_dir / "task-accuracy.csv"
    insight_csv = out_dir / "optimization-insights.csv"

    write_json(report_path, report)
    markdown_path.write_text(render_markdown(report), encoding="utf-8")
    html_path.write_text(render_html(report), encoding="utf-8")
    write_csv(
        policy_csv,
        rows,
        [
            "task",
            "dataset",
            "query_family",
            "view",
            "ranker",
            "uses_hidden_fields",
            "operations",
            "positives",
            "prevalence",
            "groups",
            "positive_groups",
            "average_precision",
            "ndcg",
            "top1_precision",
            "top1_recall",
            "top1_f1",
            "top1_work",
            "top3_precision",
            "top3_recall",
            "top3_f1",
            "top3_work",
            "top5_precision",
            "top5_recall",
            "top5_f1",
            "top5_work",
            "budget30_recall",
            "budget30_f1",
            "budget30_work",
            "work_to_first_positive",
            "work_to_first_high_lift",
            "groups_to_50pct_recall",
            "work_to_50pct_recall",
        ],
    )
    write_csv(
        task_csv,
        task_accuracy,
        [
            "task",
            "dataset",
            "query_family",
            "operations",
            "positives",
            "prevalence",
            "operation_stack_ap",
            "fixed_session_ap",
            "flat_ap",
            "raw_action_ap",
            "oracle_ap",
            "operation_stack_ndcg",
            "operation_stack_top5_precision",
            "operation_stack_top5_recall",
            "operation_stack_top5_f1",
            "operation_stack_top5_work",
            "fixed_session_top5_precision",
            "fixed_session_top5_recall",
            "fixed_session_top5_work",
            "flat_top1_precision",
            "flat_top1_recall",
            "flat_top1_work",
            "operation_stack_budget30_recall",
            "fixed_session_budget30_recall",
            "operation_stack_work_to_first_positive",
            "fixed_session_work_to_first_positive",
            "operation_stack_groups",
            "fixed_session_groups",
            "raw_action_groups",
        ],
    )
    write_csv(
        insight_csv,
        insights,
        [
            "task",
            "dataset",
            "query_family",
            "best_visible_policy",
            "best_visible_top5_f1",
            "operation_stack_top5_precision",
            "operation_stack_top5_recall",
            "operation_stack_top5_work",
            "fixed_session_top5_recall",
            "fixed_session_top5_work",
            "mapping_gain_top5_f1_vs_raw_action",
            "query_aware_ap_gain_vs_width",
            "oracle_ap_gap",
            "fixed_session_first_positive_work_advantage",
            "useful_stack_fields",
            "recommendation",
            "optimization_action",
        ],
    )
    run_result = {
        "status": "ok",
        "run_id": "R320",
        "tasks": totals["tasks"],
        "datasets": totals["datasets"],
        "task_operations": totals["task_operations"],
        "positive_operations": totals["positive_operations"],
        "policy_scores": totals["policy_scores"],
        "json": rel(report_path),
        "markdown": rel(markdown_path),
        "html": rel(html_path),
        "policy_csv": rel(policy_csv),
        "task_csv": rel(task_csv),
        "insight_csv": rel(insight_csv),
    }
    write_json(out_dir / "run-result.json", run_result)
    print(json.dumps(run_result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
