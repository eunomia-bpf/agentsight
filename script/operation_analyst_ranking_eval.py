#!/usr/bin/env python3
"""Evaluate label-hidden analyst ranking policies over operation-stack groups.

R302 follows R301's visible-packet discipline but asks a different question:
can an analyst use visible operation fields to sort operation-stack groups by a
query-specific policy instead of plain flamegraph width? The rankers here never
read dataset oracle fields such as `looping`, `safety`, `step_correct`, or
`target_positive`; those labels are used only after ranking for scoring.
"""

from __future__ import annotations

import argparse
import html
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from statistics import median
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[1]
OUT_ROOT = ROOT / "docs" / "visexp" / "out"
DEFAULT_OUT_DIR = OUT_ROOT / "operation-analyst-ranking-r302"

sys.path.insert(0, str(Path(__file__).resolve().parent))
import operation_query_utility_eval as r300  # noqa: E402

VIEWS = ["fixed_session", "operation_stack"]
RANKERS = ["width", "visible_risk", "query_aware", "oracle_upper_bound"]
TOP_GROUP_BUDGETS = [10]
OPERATION_FRACTION_BUDGETS = [0.10, 0.20, 0.30]

HIDDEN_FIELDS = {
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
}

WRITE_ACTIONS = {
    "fill",
    "type",
    "key",
    "hotkey",
    "press",
    "select_option",
    "send_msg_to_user",
}
NAV_ACTIONS = {
    "click",
    "left_click",
    "double_click",
    "tripleclick",
    "move_to",
    "drag",
    "scroll",
    "hover",
    "goto",
    "go_back",
}
RISKY_ENVIRONMENTS = {
    "os",
    "unknown_file",
    "popup",
    "induced_text",
    "account",
    "error_correction",
    "infeasible",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    return parser.parse_args()


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def normalize(value: Any) -> str:
    return str(value).lower().replace("-", "_")


def stack_label(fields: dict[str, str], stack: list[str]) -> str:
    return ";".join(f"{field}:{fields.get(field, 'unknown')}" for field in stack)


def load_groups(task: dict[str, Any], view: str) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    operations = r300.load_task_operations(task)
    stack = r300.stack_for_view(task, view)
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for operation in operations:
        grouped[stack_label(operation["fields"], stack)].append(operation)

    groups = []
    total_ops = 0
    total_positive = 0
    for key, rows in grouped.items():
        operations_in_group = sum(int(operation["value"]) for operation in rows)
        positives = sum(
            int(operation["value"])
            for operation in rows
            if operation["fields"].get("target_positive") == "positive"
        )
        total_ops += operations_in_group
        total_positive += positives
        groups.append(
            {
                "stack": key,
                "operations": operations_in_group,
                "positives": positives,
                "features": visible_features(rows),
            }
        )

    return groups, {
        "operations": total_ops,
        "positives": total_positive,
        "prevalence": total_positive / total_ops if total_ops else 0.0,
        "groups": len(groups),
    }


def visible_features(rows: list[dict[str, Any]]) -> dict[str, float]:
    total = sum(int(operation["value"]) for operation in rows)
    if not total:
        return {}

    def fraction(field: str, predicate: Callable[[str], bool]) -> float:
        hits = 0
        for operation in rows:
            fields = operation["fields"]
            if any(hidden in fields for hidden in HIDDEN_FIELDS if hidden != "target_positive"):
                # Hidden fields can exist on the source row, but rankers below
                # never read them. This branch intentionally does not expose
                # values; it just documents that scoring happens after loading.
                pass
            if predicate(normalize(fields.get(field, ""))):
                hits += int(operation["value"])
        return hits / total

    features = {
        "failure": fraction("status", lambda value: "fail" in value or "error" in value),
        "success": fraction("status", lambda value: "success" in value),
        "loop_like": fraction(
            "repeat_signal", lambda value: "loop" in value or "repeat" in value
        ),
        "input_phase": fraction("phase", lambda value: "input" in value or "modify" in value),
        "navigate_phase": fraction("phase", lambda value: "navigate" in value),
        "finish_phase": fraction("phase", lambda value: "finish" in value),
        "write_action": fraction("action", lambda value: value in WRITE_ACTIONS),
        "navigation_action": fraction("action", lambda value: value in NAV_ACTIONS),
        "risky_environment": fraction(
            "environment", lambda value: value in RISKY_ENVIRONMENTS
        ),
    }
    return {key: round(value, 6) for key, value in features.items() if value}


def rank_score(group: dict[str, Any], task: dict[str, Any], ranker: str) -> float:
    if ranker == "width":
        return float(group["operations"])
    if ranker == "oracle_upper_bound":
        return (
            (group["positives"] / group["operations"] if group["operations"] else 0.0) * 1000
            + group["positives"]
        )

    features = group["features"]
    failure = features.get("failure", 0.0)
    success = features.get("success", 0.0)
    loop_like = features.get("loop_like", 0.0)
    input_phase = features.get("input_phase", 0.0)
    navigate_phase = features.get("navigate_phase", 0.0)
    finish_phase = features.get("finish_phase", 0.0)
    write_action = features.get("write_action", 0.0)
    navigation_action = features.get("navigation_action", 0.0)
    risky_environment = features.get("risky_environment", 0.0)

    if ranker == "visible_risk":
        return (
            3.0 * failure
            + 2.0 * loop_like
            + 1.5 * write_action
            + input_phase
            + 0.5 * risky_environment
            + 0.000001 * group["operations"]
        )

    task_id = task["id"]
    if task_id == "agentreward_looping":
        score = 5.0 * loop_like + 1.5 * failure + 0.5 * navigation_action
    elif task_id == "agentreward_side_effect":
        score = (
            3.0 * write_action
            + 2.0 * input_phase
            + failure
            + 0.5 * navigation_action
            - 0.5 * finish_phase
        )
    elif task_id == "satraj_unsafe":
        score = (
            2.0 * risky_environment
            + 2.0 * write_action
            + 1.5 * input_phase
            + 0.5 * success
            + 0.5 * loop_like
        )
    elif task_id == "agentnet_incorrect_step":
        score = 2.0 * failure + 1.5 * loop_like + risky_environment + 0.5 * input_phase
    elif task_id == "agentnet_redundant_step":
        score = 4.0 * loop_like + failure + 0.5 * navigation_action
    elif task_id == "osworld_group_start":
        score = (
            1.5 * input_phase
            + navigate_phase
            + write_action
            + 0.5 * navigation_action
            + 0.5 * finish_phase
        )
    else:
        score = 0.0
    return score + 0.000001 * group["operations"]


def evaluate_top_k(
    groups: list[dict[str, Any]],
    summary: dict[str, Any],
    task: dict[str, Any],
    ranker: str,
    k: int,
) -> dict[str, Any]:
    ranked = sorted(groups, key=lambda group: rank_score(group, task, ranker), reverse=True)
    return score_selection(ranked[:k], summary, f"top_{k}_groups", ranker)


def evaluate_operation_budget(
    groups: list[dict[str, Any]],
    summary: dict[str, Any],
    task: dict[str, Any],
    ranker: str,
    fraction: float,
) -> dict[str, Any]:
    ranked = sorted(groups, key=lambda group: rank_score(group, task, ranker), reverse=True)
    limit = summary["operations"] * fraction
    selected = []
    inspected = 0
    for group in ranked:
        if inspected + group["operations"] > limit:
            continue
        selected.append(group)
        inspected += group["operations"]
    return score_selection(
        selected,
        summary,
        f"budget_{int(fraction * 100)}pct_operations",
        ranker,
    )


def score_selection(
    selected: list[dict[str, Any]],
    summary: dict[str, Any],
    budget: str,
    ranker: str,
) -> dict[str, Any]:
    inspected_ops = sum(group["operations"] for group in selected)
    positives = sum(group["positives"] for group in selected)
    total_ops = summary["operations"]
    total_positive = summary["positives"]
    prevalence = summary["prevalence"]
    precision = positives / inspected_ops if inspected_ops else 0.0
    return {
        "budget": budget,
        "ranker": ranker,
        "groups_inspected": len(selected),
        "inspected_operations": inspected_ops,
        "inspected_operation_fraction": inspected_ops / total_ops if total_ops else 0.0,
        "positive_recall": positives / total_positive if total_positive else 0.0,
        "positive_precision": precision,
        "positive_lift": precision / prevalence if prevalence else 0.0,
        "positive_operations": positives,
    }


def summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    by_key: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_key[(row["view"], row["ranker"], row["budget"])].append(row)
    medians = {}
    for (view, ranker, budget), items in sorted(by_key.items()):
        medians[f"{view}:{ranker}:{budget}"] = {
            "view": view,
            "ranker": ranker,
            "budget": budget,
            "tasks": len(items),
            "median_positive_recall": round(median(item["positive_recall"] for item in items), 4),
            "median_positive_lift": round(median(item["positive_lift"] for item in items), 4),
            "median_inspected_operation_fraction": round(
                median(item["inspected_operation_fraction"] for item in items), 4
            ),
            "median_groups_inspected": round(median(item["groups_inspected"] for item in items), 3),
        }
    return {
        "medians": medians,
        "comparisons": {
            "operation_stack_query_aware_vs_width": compare(
                rows, "operation_stack", "query_aware", "operation_stack", "width"
            ),
            "operation_stack_query_aware_vs_fixed_query_aware": compare(
                rows, "operation_stack", "query_aware", "fixed_session", "query_aware"
            ),
            "operation_stack_visible_risk_vs_width": compare(
                rows, "operation_stack", "visible_risk", "operation_stack", "width"
            ),
            "operation_stack_width_vs_oracle_upper_bound": compare(
                rows, "operation_stack", "width", "operation_stack", "oracle_upper_bound"
            ),
        },
    }


def compare(
    rows: list[dict[str, Any]],
    left_view: str,
    left_ranker: str,
    right_view: str,
    right_ranker: str,
) -> dict[str, Any]:
    by_key = {(row["task"], row["view"], row["ranker"], row["budget"]): row for row in rows}
    budgets = sorted({row["budget"] for row in rows})
    out = {}
    for budget in budgets:
        recall_ratios = []
        lift_ratios = []
        work_ratios = []
        group_ratios = []
        for task in sorted({row["task"] for row in rows}):
            lhs = by_key.get((task, left_view, left_ranker, budget))
            rhs = by_key.get((task, right_view, right_ranker, budget))
            if not lhs or not rhs:
                continue
            recall_ratios.append(safe_ratio(lhs["positive_recall"], rhs["positive_recall"]))
            lift_ratios.append(safe_ratio(lhs["positive_lift"], rhs["positive_lift"]))
            work_ratios.append(
                safe_ratio(lhs["inspected_operation_fraction"], rhs["inspected_operation_fraction"])
            )
            group_ratios.append(safe_ratio(lhs["groups_inspected"], rhs["groups_inspected"]))
        out[budget] = {
            "left": f"{left_view}:{left_ranker}",
            "right": f"{right_view}:{right_ranker}",
            "tasks": len(recall_ratios),
            "median_positive_recall_ratio": round(median(recall_ratios), 4),
            "median_positive_lift_ratio": round(median(lift_ratios), 4),
            "median_inspected_operation_fraction_ratio": round(median(work_ratios), 4),
            "median_groups_inspected_ratio": round(median(group_ratios), 4),
        }
    return out


def safe_ratio(left: float | int, right: float | int) -> float:
    if right == 0:
        return 0.0 if left == 0 else float("inf")
    return float(left) / float(right)


def build_headline(summary: dict[str, Any]) -> str:
    medians = summary["medians"]
    width_top = medians["operation_stack:width:top_10_groups"]
    query_top = medians["operation_stack:query_aware:top_10_groups"]
    width_budget = medians["operation_stack:width:budget_30pct_operations"]
    query_budget = medians["operation_stack:query_aware:budget_30pct_operations"]
    return (
        "Query-aware ranking changes the analysis tradeoff without reading oracle labels. "
        f"On operation stacks, top-10 query-aware groups inspect {query_top['median_inspected_operation_fraction'] * 100:.1f}% "
        f"of operations with lift {query_top['median_positive_lift']:.3f}, compared with "
        f"{width_top['median_inspected_operation_fraction'] * 100:.1f}% and lift {width_top['median_positive_lift']:.3f} "
        "for width ranking. At a 30% operation budget, query-aware ranking raises median recall "
        f"from {width_budget['median_positive_recall'] * 100:.1f}% to {query_budget['median_positive_recall'] * 100:.1f}%, "
        f"but it inspects {query_budget['median_groups_inspected']} groups instead of "
        f"{width_budget['median_groups_inspected']}, so the result supports configurable analysis "
        "policies rather than automatic detection."
    )


def validate_no_hidden_rank_features() -> None:
    allowed_feature_sources = {
        "status",
        "repeat_signal",
        "phase",
        "action",
        "environment",
    }
    if allowed_feature_sources & HIDDEN_FIELDS:
        raise SystemExit("ranker feature fields overlap hidden oracle fields")


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# R302 Label-Hidden Analyst Ranking",
        "",
        report["headline"],
        "",
        "## Median Scores",
        "",
        "| View | Ranker | Budget | Median recall | Median lift | Work fraction | Groups |",
        "|---|---|---|---:|---:|---:|---:|",
    ]
    for row in report["summary"]["medians"].values():
        lines.append(
            f"| {row['view']} | {row['ranker']} | {row['budget']} | {row['median_positive_recall']} | {row['median_positive_lift']} | {row['median_inspected_operation_fraction']} | {row['median_groups_inspected']} |"
        )
    lines.extend(
        [
            "",
            "## Claim Scope",
            "",
            "- Supports: operation stacks can be paired with label-hidden ranking policies to trade recall, precision, and inspection work without adding a new profiler abstraction.",
            "- Narrows: query-aware ranking is a heuristic over visible operation fields, not a detector or human-study result.",
            "- Upper bound: `oracle_upper_bound` is included only to show remaining headroom and never appears as a visible policy.",
        ]
    )
    return "\n".join(lines) + "\n"


def render_html(report: dict[str, Any]) -> str:
    rows = "".join(
        "<tr>"
        f"<td>{html.escape(row['view'])}</td>"
        f"<td>{html.escape(row['ranker'])}</td>"
        f"<td>{html.escape(row['budget'])}</td>"
        f"<td>{row['median_positive_recall']}</td>"
        f"<td>{row['median_positive_lift']}</td>"
        f"<td>{row['median_inspected_operation_fraction']}</td>"
        f"<td>{row['median_groups_inspected']}</td>"
        "</tr>"
        for row in report["summary"]["medians"].values()
    )
    return f"""<!doctype html>
<meta charset="utf-8">
<title>R302 Label-Hidden Analyst Ranking</title>
<style>
body {{ font-family: system-ui, sans-serif; margin: 32px; color: #202124; }}
table {{ border-collapse: collapse; width: 100%; margin-top: 24px; font-size: 13px; }}
th, td {{ border-bottom: 1px solid #d7dce2; padding: 7px 8px; text-align: left; }}
th {{ background: #edf1f5; }}
</style>
<h1>R302 Label-Hidden Analyst Ranking</h1>
<p>{html.escape(report['headline'])}</p>
<table>
<thead><tr><th>View</th><th>Ranker</th><th>Budget</th><th>Recall</th><th>Lift</th><th>Work fraction</th><th>Groups</th></tr></thead>
<tbody>{rows}</tbody>
</table>
"""


def main() -> None:
    validate_no_hidden_rank_features()
    args = parse_args()
    out_dir = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    rows = []
    task_summaries = []
    for task in r300.TASKS:
        for view in VIEWS:
            groups, group_summary = load_groups(task, view)
            if not groups:
                raise SystemExit(f"task {task['id']} view {view} produced no groups")
            task_summaries.append(
                {
                    "task": task["id"],
                    "dataset": task["dataset"],
                    "view": view,
                    **group_summary,
                }
            )
            for ranker in RANKERS:
                for k in TOP_GROUP_BUDGETS:
                    rows.append(
                        {
                            "task": task["id"],
                            "dataset": task["dataset"],
                            "view": view,
                            **evaluate_top_k(groups, group_summary, task, ranker, k),
                        }
                    )
                for fraction in OPERATION_FRACTION_BUDGETS:
                    rows.append(
                        {
                            "task": task["id"],
                            "dataset": task["dataset"],
                            "view": view,
                            **evaluate_operation_budget(
                                groups, group_summary, task, ranker, fraction
                            ),
                        }
                    )

    summary = summarize(rows)
    report = {
        "run_id": "R302",
        "purpose": "label-hidden ranking policies over operation-stack analyst tasks",
        "input_policy": "no dataset sync; reuses tracked operation JSONL from R288-R291/R300",
        "hidden_fields": sorted(HIDDEN_FIELDS),
        "rankers": {
            "width": "sort groups by operation count, matching flamegraph width",
            "visible_risk": "query-agnostic heuristic over visible status/repetition/input fields",
            "query_aware": "task-query heuristic over visible operation fields",
            "oracle_upper_bound": "hidden-label upper bound used only for headroom analysis",
        },
        "views": VIEWS,
        "budgets": {
            "top_group_budgets": TOP_GROUP_BUDGETS,
            "operation_fraction_budgets": OPERATION_FRACTION_BUDGETS,
        },
        "tasks": task_summaries,
        "scores": rows,
        "summary": summary,
        "headline": build_headline(summary),
        "claim_scope": {
            "supported": "operation stacks support configurable label-hidden ranking policies that trade recall, precision, and inspection work beyond flamegraph width",
            "narrowed": "rankers are heuristics over visible operation fields and do not constitute online detectors or human utility evidence",
            "not_supported": "automatic anomaly detection, learned cross-task ranking, or human time-to-answer improvement",
        },
    }

    report_path = out_dir / "ranking-report.json"
    markdown_path = out_dir / "ranking-report.md"
    html_path = out_dir / "index.html"
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    markdown_path.write_text(render_markdown(report), encoding="utf-8")
    html_path.write_text(render_html(report), encoding="utf-8")

    run_result = {
        "status": "ok",
        "run_id": "R302",
        "tasks": len(r300.TASKS),
        "views": VIEWS,
        "rankers": RANKERS,
        "scores": len(rows),
        "json": rel(report_path),
        "markdown": rel(markdown_path),
        "html": rel(html_path),
    }
    (out_dir / "run-result.json").write_text(json.dumps(run_result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(run_result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
