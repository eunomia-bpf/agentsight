#!/usr/bin/env python3
"""R339: score sequence-level adequacy of ranked operation-stack profiles.

R339 reuses the existing R300 real labeled operation JSONL and R320 visible
rankers.  It asks whether ranked profile groups localize problems to a useful
trajectory/session scope, not only to positive operations.  Hidden labels are
used only after ranking for scoring.
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
DEFAULT_OUT_DIR = OUT_ROOT / "operation-sequence-adequacy-r339"

sys.path.insert(0, str(Path(__file__).resolve().parent))
import operation_analyst_ranking_eval as r302  # noqa: E402
import operation_profile_accuracy_eval as r320  # noqa: E402
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
PRIMARY_SELECTIONS = ["top5", "budget30"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    return parser.parse_args()


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return str(path.resolve())


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


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


def operation_order(operation: dict[str, Any]) -> tuple[str, int, int]:
    fields = operation["fields"]
    raw_turn = fields.get("turn") or fields.get("step") or fields.get("index") or ""
    try:
        turn = int(float(raw_turn))
    except (TypeError, ValueError):
        turn = int(operation.get("_source_line") or 0)
    return (fields.get("session", "unknown"), turn, int(operation.get("_source_line") or 0))


def session_id(operation: dict[str, Any]) -> str:
    return operation["fields"].get("session", "unknown")


def is_positive(operation: dict[str, Any]) -> bool:
    return operation["fields"].get("target_positive") == "positive"


def op_value(operation: dict[str, Any]) -> int:
    return int(operation.get("value") or 1)


def group_task_view(task: dict[str, Any], view: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    operations = sorted(r300.load_task_operations(task), key=operation_order)
    stack = r320.stack_for_view(task, view)
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for operation in operations:
        grouped[stack_label(operation["fields"], stack)].append(operation)

    groups = []
    for label, rows in grouped.items():
        operations_in_group = sum(op_value(operation) for operation in rows)
        positives = sum(op_value(operation) for operation in rows if is_positive(operation))
        sessions = sorted({session_id(operation) for operation in rows})
        groups.append(
            {
                "group_id": stack_hash(f"{view}:{label}"),
                "stack": label,
                "stack_frames": stack_frames(label),
                "operations": operations_in_group,
                "positives": positives,
                "positive_rate": positives / operations_in_group if operations_in_group else 0.0,
                "sessions": len(sessions),
                "rows": rows,
                "features": r302.visible_features(rows),
            }
        )

    total_ops = sum(op_value(operation) for operation in operations)
    total_positive = sum(op_value(operation) for operation in operations if is_positive(operation))
    by_session: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for operation in operations:
        by_session[session_id(operation)].append(operation)
    positive_sessions = {
        session
        for session, rows in by_session.items()
        if any(is_positive(operation) for operation in rows)
    }
    summary = {
        "operations": total_ops,
        "positives": total_positive,
        "prevalence": total_positive / total_ops if total_ops else 0.0,
        "groups": len(groups),
        "positive_groups": sum(1 for group in groups if group["positives"] > 0),
        "sessions": len(by_session),
        "positive_sessions": len(positive_sessions),
        "positive_session_prevalence": len(positive_sessions) / len(by_session)
        if by_session
        else 0.0,
        "stack": stack,
    }
    return operations, groups, summary


def rank_groups(task: dict[str, Any], groups: list[dict[str, Any]], ranker: str) -> list[dict[str, Any]]:
    return sorted(
        groups,
        key=lambda group: (
            r302.rank_score(group, task, ranker),
            group["operations"] if ranker != "oracle_upper_bound" else group["positives"],
            group["group_id"],
        ),
        reverse=True,
    )


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


def score_sequence_selection(
    selected: list[dict[str, Any]],
    operations: list[dict[str, Any]],
    summary: dict[str, Any],
    label: str,
) -> dict[str, Any]:
    selected_rows: list[dict[str, Any]] = []
    for group in selected:
        selected_rows.extend(group["rows"])

    selected_ops = sum(op_value(operation) for operation in selected_rows)
    selected_positive_ops = sum(
        op_value(operation) for operation in selected_rows if is_positive(operation)
    )
    selected_sessions = {session_id(operation) for operation in selected_rows}
    hit_positive_sessions = {
        session_id(operation) for operation in selected_rows if is_positive(operation)
    }

    selected_by_session: dict[str, int] = defaultdict(int)
    session_lengths: dict[str, int] = defaultdict(int)
    for operation in operations:
        session_lengths[session_id(operation)] += op_value(operation)
    for operation in selected_rows:
        selected_by_session[session_id(operation)] += op_value(operation)

    selected_session_fractions = [
        selected_by_session[session] / session_lengths[session]
        for session in selected_sessions
        if session_lengths[session]
    ]
    selected_ops_per_session = [
        selected_by_session[session] for session in selected_sessions
    ]

    total_ops = summary["operations"]
    total_pos = summary["positives"]
    total_sessions = summary["sessions"]
    total_positive_sessions = summary["positive_sessions"]
    selected_session_count = len(selected_sessions)
    hit_positive_session_count = len(hit_positive_sessions)

    operation_precision = selected_positive_ops / selected_ops if selected_ops else 0.0
    operation_recall = selected_positive_ops / total_pos if total_pos else 0.0
    session_precision = (
        hit_positive_session_count / selected_session_count if selected_session_count else 0.0
    )
    session_recall = (
        hit_positive_session_count / total_positive_sessions if total_positive_sessions else 0.0
    )
    session_work = selected_session_count / total_sessions if total_sessions else 0.0
    session_lift = (
        session_precision / summary["positive_session_prevalence"]
        if summary["positive_session_prevalence"]
        else 0.0
    )
    session_efficiency = session_recall / session_work if session_work else 0.0

    return {
        f"{label}_groups": len(selected),
        f"{label}_positive_groups": sum(1 for group in selected if group["positives"] > 0),
        f"{label}_operation_work": selected_ops / total_ops if total_ops else 0.0,
        f"{label}_positive_operation_recall": operation_recall,
        f"{label}_positive_operation_precision": operation_precision,
        f"{label}_positive_operation_f1": f1_score(operation_precision, operation_recall),
        f"{label}_selected_sessions": selected_session_count,
        f"{label}_hit_positive_sessions": hit_positive_session_count,
        f"{label}_session_work": session_work,
        f"{label}_positive_session_recall": session_recall,
        f"{label}_positive_session_precision": session_precision,
        f"{label}_positive_session_f1": f1_score(session_precision, session_recall),
        f"{label}_positive_session_lift": session_lift,
        f"{label}_session_efficiency": session_efficiency,
        f"{label}_median_selected_ops_per_session": median_or_none(
            [float(value) for value in selected_ops_per_session]
        ),
        f"{label}_median_selected_session_fraction": median_or_none(
            [float(value) for value in selected_session_fractions]
        ),
    }


def top_group_snapshot(
    ranked: list[dict[str, Any]],
    summary: dict[str, Any],
    limit: int = 3,
) -> list[dict[str, Any]]:
    rows = []
    for index, group in enumerate(ranked[:limit], 1):
        rows.append(
            {
                "rank": index,
                "group_id": group["group_id"],
                "operations": group["operations"],
                "positive_operations": group["positives"],
                "positive_rate": group["positive_rate"],
                "sessions": group["sessions"],
                "session_share": group["sessions"] / summary["sessions"]
                if summary["sessions"]
                else 0.0,
                "stack_frames": group["stack_frames"],
                "visible_features": group["features"],
            }
        )
    return rows


def score_policy(
    task: dict[str, Any],
    view: str,
    ranker: str,
    operations: list[dict[str, Any]],
    groups: list[dict[str, Any]],
    summary: dict[str, Any],
) -> dict[str, Any]:
    ranked = rank_groups(task, groups, ranker)
    row: dict[str, Any] = {
        "task": task["id"],
        "dataset": task["dataset"],
        "query_family": task["query_family"],
        "problem": task["problem"],
        "view": view,
        "ranker": ranker,
        "uses_hidden_fields": r320.policy_uses_hidden_fields(view, ranker),
        "operations": summary["operations"],
        "positives": summary["positives"],
        "sessions": summary["sessions"],
        "positive_sessions": summary["positive_sessions"],
        "positive_session_prevalence": summary["positive_session_prevalence"],
        "groups": summary["groups"],
        "positive_groups": summary["positive_groups"],
        "stack_fields": summary["stack"],
    }
    for k in TOP_K_VALUES:
        row.update(score_sequence_selection(ranked[:k], operations, summary, f"top{k}"))
    for budget in OPERATION_BUDGETS:
        selected = select_for_operation_budget(ranked, summary, budget)
        row.update(
            score_sequence_selection(
                selected,
                operations,
                summary,
                f"budget{int(budget * 100)}",
            )
        )
    row["top_groups"] = top_group_snapshot(ranked, summary, 3)
    return row


def policy_key(view: str, ranker: str) -> str:
    return f"{view}:{ranker}"


def summarize_policy_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    by_policy: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_policy[(row["view"], row["ranker"])].append(row)

    metrics = []
    for label in PRIMARY_SELECTIONS:
        metrics.extend(
            [
                f"{label}_operation_work",
                f"{label}_positive_operation_recall",
                f"{label}_positive_operation_precision",
                f"{label}_positive_operation_f1",
                f"{label}_session_work",
                f"{label}_positive_session_recall",
                f"{label}_positive_session_precision",
                f"{label}_positive_session_f1",
                f"{label}_positive_session_lift",
                f"{label}_session_efficiency",
                f"{label}_median_selected_session_fraction",
            ]
        )

    summary = {}
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
            "uses_hidden_fields": r320.policy_uses_hidden_fields(view, ranker),
            **values,
        }
    return round_value(summary)


def compare_policies(rows: list[dict[str, Any]]) -> dict[str, Any]:
    by_key = {(row["task"], row["view"], row["ranker"]): row for row in rows}
    tasks = sorted({row["task"] for row in rows})
    default = ("operation_stack", "query_aware")
    baselines = {
        "vs_flat_width": ("flat", "width"),
        "vs_fixed_session_query_aware": ("fixed_session", "query_aware"),
        "vs_dataset_native_query_aware": ("dataset_native", "query_aware"),
        "vs_raw_action_query_aware": ("raw_action_stack", "query_aware"),
        "vs_operation_stack_width": ("operation_stack", "width"),
    }
    metrics = [
        "top5_operation_work",
        "top5_session_work",
        "top5_positive_session_recall",
        "top5_positive_session_f1",
        "budget30_positive_operation_recall",
        "budget30_session_work",
        "budget30_positive_session_recall",
        "budget30_positive_session_f1",
        "budget30_positive_session_lift",
        "budget30_session_efficiency",
    ]
    comparisons = {}
    for name, baseline in baselines.items():
        task_rows = []
        metric_summary = {}
        for task in tasks:
            left = by_key.get((task, *default))
            right = by_key.get((task, *baseline))
            if not left or not right:
                continue
            task_row = {
                "task": task,
                "left": policy_key(*default),
                "right": policy_key(*baseline),
            }
            for metric in metrics:
                left_value = left.get(metric)
                right_value = right.get(metric)
                delta = (
                    float(left_value) - float(right_value)
                    if left_value is not None and right_value is not None
                    else None
                )
                task_row[f"{metric}_left"] = left_value
                task_row[f"{metric}_right"] = right_value
                task_row[f"{metric}_delta"] = delta
                task_row[f"{metric}_ratio"] = safe_ratio(left_value, right_value)
            task_rows.append(task_row)
        for metric in metrics:
            deltas = [row[f"{metric}_delta"] for row in task_rows if row[f"{metric}_delta"] is not None]
            lower_is_better = metric.endswith("_work")
            if lower_is_better:
                improved = sum(1 for delta in deltas if delta < 0)
                worse = sum(1 for delta in deltas if delta > 0)
            else:
                improved = sum(1 for delta in deltas if delta > 0)
                worse = sum(1 for delta in deltas if delta < 0)
            metric_summary[metric] = {
                "median_delta": median_or_none(deltas),
                "mean_delta": mean_or_none(deltas),
                "improved_tasks": improved,
                "worse_tasks": worse,
                "tied_tasks": len(deltas) - improved - worse,
            }
        comparisons[name] = {
            "left": policy_key(*default),
            "right": policy_key(*baseline),
            "tasks": len(task_rows),
            "metrics": round_value(metric_summary),
            "task_rows": round_value(task_rows),
        }
    return comparisons


def task_sequence_cards(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_task: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        if not row["uses_hidden_fields"]:
            by_task[row["task"]].append(row)

    cards = []
    for task, items in sorted(by_task.items()):
        default = next(
            row
            for row in items
            if row["view"] == "operation_stack" and row["ranker"] == "query_aware"
        )
        fixed = next(
            row
            for row in items
            if row["view"] == "fixed_session" and row["ranker"] == "query_aware"
        )
        raw = next(
            row
            for row in items
            if row["view"] == "raw_action_stack" and row["ranker"] == "query_aware"
        )
        best = max(
            items,
            key=lambda row: (
                row["budget30_positive_session_f1"],
                row["budget30_positive_session_recall"],
                -row["budget30_session_work"],
                row["budget30_positive_operation_recall"],
            ),
        )
        if (
            default["budget30_positive_session_recall"]
            > fixed["budget30_positive_session_recall"]
            and default["budget30_session_work"] < raw["budget30_session_work"]
        ):
            action = "Use operation-stack query-aware for sequence-scope triage; keep fixed-session for first-positive drilldown."
        elif raw["budget30_positive_session_recall"] > default["budget30_positive_session_recall"]:
            action = "Raw action reaches more positive sessions but over-touches sessions; add mapping/ranker rules before using it as the primary view."
        elif fixed["budget30_positive_session_f1"] > default["budget30_positive_session_f1"]:
            action = "Fixed-session is the stronger sequence policy here; use operation-stack as a secondary semantic explanation layer."
        else:
            action = "Keep operation-stack query-aware as the default visible policy and tune stack fields for the remaining missed sessions."
        cards.append(
            {
                "task": task,
                "dataset": default["dataset"],
                "query_family": default["query_family"],
                "best_visible_sequence_policy": policy_key(best["view"], best["ranker"]),
                "best_visible_budget30_session_f1": best["budget30_positive_session_f1"],
                "operation_stack_budget30_positive_session_recall": default[
                    "budget30_positive_session_recall"
                ],
                "operation_stack_budget30_session_work": default["budget30_session_work"],
                "fixed_session_budget30_positive_session_recall": fixed[
                    "budget30_positive_session_recall"
                ],
                "fixed_session_budget30_session_work": fixed["budget30_session_work"],
                "raw_action_budget30_positive_session_recall": raw[
                    "budget30_positive_session_recall"
                ],
                "raw_action_budget30_session_work": raw["budget30_session_work"],
                "sequence_action": action,
            }
        )
    return round_value(cards)


def make_claim_summary(policy_summary: dict[str, Any], comparisons: dict[str, Any]) -> dict[str, Any]:
    default = policy_summary["operation_stack:query_aware"]
    fixed = policy_summary["fixed_session:query_aware"]
    raw = policy_summary["raw_action_stack:query_aware"]
    flat = policy_summary["flat:width"]
    return round_value(
        {
            "default_policy": "operation_stack:query_aware",
            "top5": {
                "median_operation_work": default["median_top5_operation_work"],
                "median_positive_session_recall": default[
                    "median_top5_positive_session_recall"
                ],
                "median_session_work": default["median_top5_session_work"],
                "flat_operation_work": flat["median_top5_operation_work"],
                "fixed_positive_session_recall": fixed[
                    "median_top5_positive_session_recall"
                ],
            },
            "budget30": {
                "median_positive_operation_recall": default[
                    "median_budget30_positive_operation_recall"
                ],
                "median_positive_session_recall": default[
                    "median_budget30_positive_session_recall"
                ],
                "median_session_work": default["median_budget30_session_work"],
                "fixed_positive_session_recall": fixed[
                    "median_budget30_positive_session_recall"
                ],
                "fixed_session_work": fixed["median_budget30_session_work"],
                "raw_action_positive_session_recall": raw[
                    "median_budget30_positive_session_recall"
                ],
                "raw_action_session_work": raw["median_budget30_session_work"],
            },
            "paired_checks": {
                "budget30_session_recall_gt_fixed_tasks": comparisons[
                    "vs_fixed_session_query_aware"
                ]["metrics"]["budget30_positive_session_recall"]["improved_tasks"],
                "budget30_session_work_lt_raw_action_tasks": comparisons[
                    "vs_raw_action_query_aware"
                ]["metrics"]["budget30_session_work"]["improved_tasks"],
                "top5_operation_work_lt_flat_tasks": comparisons["vs_flat_width"]["metrics"][
                    "top5_operation_work"
                ]["improved_tasks"],
            },
            "supported_wording": (
                "Operation-stack query-aware ranking gives a sequence-scope triage "
                "tradeoff: it covers more positive sessions than fixed-session under "
                "a 30% operation budget while touching far fewer sessions than raw "
                "action stacks, and it inspects much less work than flat summaries."
            ),
            "must_not_claim": [
                "does not prove human or agent analyst productivity",
                "does not prove automatic discovery of all intent boundaries",
                "does not dominate fixed-session on first-positive work",
                "does not make raw action stacks obsolete for high session recall",
            ],
        }
    )


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field) for field in fieldnames})


def render_markdown(report: dict[str, Any]) -> str:
    summary = report["summary"]
    claim = report["claim_summary"]
    budget = claim["budget30"]
    top5 = claim["top5"]
    lines = [
        "# R339 Sequence Adequacy",
        "",
        "This run reuses existing tracked labeled operation JSONL. It does not fetch, sync, create, or relabel datasets.",
        "It scores ranked profile groups after visible ranking, using hidden labels only for offline evaluation.",
        "",
        "## Headline",
        "",
        (
            f"Overall status: `{summary['overall']}`. The default visible policy is "
            "`operation_stack:query_aware`."
        ),
        (
            "At top-5 groups, it inspects median "
            f"{top5['median_operation_work']:.4f} operation work and covers median "
            f"{top5['median_positive_session_recall']:.4f} positive-session recall, "
            f"versus fixed-session recall {top5['fixed_positive_session_recall']:.4f} "
            f"and flat operation work {top5['flat_operation_work']:.4f}."
        ),
        (
            "At a 30% operation budget, it reaches median "
            f"{budget['median_positive_operation_recall']:.4f} positive-operation recall "
            f"and {budget['median_positive_session_recall']:.4f} positive-session recall "
            f"while touching median {budget['median_session_work']:.4f} sessions."
        ),
        (
            "Fixed-session reaches median "
            f"{budget['fixed_positive_session_recall']:.4f} positive-session recall at "
            f"{budget['fixed_session_work']:.4f} session work. Raw action reaches "
            f"{budget['raw_action_positive_session_recall']:.4f} positive-session recall "
            f"but touches {budget['raw_action_session_work']:.4f} sessions."
        ),
        "",
        "## Claim Boundary",
        "",
        claim["supported_wording"],
        "",
        "Must not claim:",
    ]
    for item in claim["must_not_claim"]:
        lines.append(f"- {item}")
    lines.extend(
        [
            "",
            "## Artifacts",
            "",
            "- `sequence-adequacy-report.json`",
            "- `task-sequence-adequacy.csv`",
            "- `policy-sequence-summary.csv`",
            "- `default-sequence-comparisons.csv`",
            "- `task-sequence-cards.csv`",
        ]
    )
    return "\n".join(lines) + "\n"


def render_html(report: dict[str, Any], markdown: str) -> str:
    body = html.escape(markdown)
    return (
        "<!doctype html><meta charset='utf-8'><title>R339 Sequence Adequacy</title>"
        "<style>body{font-family:system-ui,sans-serif;max-width:960px;margin:40px auto;"
        "line-height:1.5}pre{white-space:pre-wrap;background:#f6f8fa;padding:16px}</style>"
        f"<pre>{body}</pre>"
    )


def main() -> None:
    args = parse_args()
    out_dir = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    source_paths = sorted({Path(task["operation_file"]) for task in r300.TASKS})
    source_paths.extend(
        [
            OUT_ROOT / "operation-profile-accuracy-r320" / "profile-accuracy-report.json",
            OUT_ROOT / "operation-inspection-target-r337" / "inspection-target-report.json",
        ]
    )
    ensure_sources_tracked_clean(source_paths)

    start = time.time()
    rows: list[dict[str, Any]] = []
    group_cache: dict[tuple[str, str], tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]] = {}
    for task in r300.TASKS:
        for view in VIEWS:
            group_cache[(task["id"], view)] = group_task_view(task, view)
            operations, groups, summary = group_cache[(task["id"], view)]
            for ranker in RANKERS:
                rows.append(score_policy(task, view, ranker, operations, groups, summary))

    policy_summary = summarize_policy_rows(rows)
    comparisons = compare_policies(rows)
    cards = task_sequence_cards(rows)
    claim_summary = make_claim_summary(policy_summary, comparisons)

    summary = {
        "run_id": "R339",
        "schema": "agentsight.operation-sequence-adequacy.v1",
        "overall": "pass",
        "tasks": len(r300.TASKS),
        "datasets": sorted({task["dataset"] for task in r300.TASKS}),
        "operation_sources": [rel(path) for path in sorted({Path(task["operation_file"]) for task in r300.TASKS})],
        "policies_scored": len(rows),
        "network_access_required": False,
        "source_artifacts_tracked_clean": True,
        "hidden_labels_used_only_for_scoring": True,
        "profiler_abstractions": ["operation", "operation stack"],
        "duration_seconds": time.time() - start,
    }
    report = {
        "commit": git_output(["rev-parse", "HEAD"]),
        "summary": round_value(summary),
        "claim_summary": claim_summary,
        "policy_summary": policy_summary,
        "comparisons": comparisons,
        "task_sequence_cards": cards,
        "source_paths": [rel(path) for path in source_paths],
    }
    write_json(out_dir / "sequence-adequacy-report.json", round_value(report))
    run_result = {
        "commit": report["commit"],
        "run_id": "R339",
        "schema": summary["schema"],
        "summary": round_value(summary),
    }
    write_json(out_dir / "run-result.json", run_result)

    task_fields = [
        "task",
        "dataset",
        "query_family",
        "view",
        "ranker",
        "uses_hidden_fields",
        "operations",
        "positives",
        "sessions",
        "positive_sessions",
        "groups",
        "top5_operation_work",
        "top5_positive_operation_recall",
        "top5_session_work",
        "top5_positive_session_recall",
        "top5_positive_session_f1",
        "budget30_operation_work",
        "budget30_positive_operation_recall",
        "budget30_session_work",
        "budget30_positive_session_recall",
        "budget30_positive_session_f1",
        "budget30_positive_session_lift",
        "budget30_session_efficiency",
    ]
    csv_rows = []
    for row in rows:
        flat = {field: row.get(field) for field in task_fields}
        csv_rows.append(round_value(flat))
    write_csv(out_dir / "task-sequence-adequacy.csv", csv_rows, task_fields)

    policy_fields = [
        "policy",
        "view",
        "ranker",
        "tasks",
        "uses_hidden_fields",
        "median_top5_operation_work",
        "median_top5_positive_session_recall",
        "median_top5_session_work",
        "median_top5_positive_session_f1",
        "median_budget30_positive_operation_recall",
        "median_budget30_positive_session_recall",
        "median_budget30_session_work",
        "median_budget30_positive_session_f1",
        "median_budget30_positive_session_lift",
        "median_budget30_session_efficiency",
    ]
    policy_rows = []
    for policy, item in sorted(policy_summary.items()):
        row = {"policy": policy, **item}
        policy_rows.append(row)
    write_csv(out_dir / "policy-sequence-summary.csv", policy_rows, policy_fields)

    comparison_rows = []
    for name, comparison in sorted(comparisons.items()):
        for metric, values in comparison["metrics"].items():
            comparison_rows.append(
                {
                    "comparison": name,
                    "left": comparison["left"],
                    "right": comparison["right"],
                    "metric": metric,
                    **values,
                }
            )
    comparison_fields = [
        "comparison",
        "left",
        "right",
        "metric",
        "median_delta",
        "mean_delta",
        "improved_tasks",
        "worse_tasks",
        "tied_tasks",
    ]
    write_csv(
        out_dir / "default-sequence-comparisons.csv",
        round_value(comparison_rows),
        comparison_fields,
    )

    card_fields = [
        "task",
        "dataset",
        "query_family",
        "best_visible_sequence_policy",
        "best_visible_budget30_session_f1",
        "operation_stack_budget30_positive_session_recall",
        "operation_stack_budget30_session_work",
        "fixed_session_budget30_positive_session_recall",
        "fixed_session_budget30_session_work",
        "raw_action_budget30_positive_session_recall",
        "raw_action_budget30_session_work",
        "sequence_action",
    ]
    write_csv(out_dir / "task-sequence-cards.csv", cards, card_fields)

    markdown = render_markdown(round_value(report))
    (out_dir / "sequence-adequacy-report.md").write_text(markdown, encoding="utf-8")
    (out_dir / "index.html").write_text(
        render_html(round_value(report), markdown), encoding="utf-8"
    )
    print(json.dumps(round_value(summary), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
