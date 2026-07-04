#!/usr/bin/env python3
"""Compare label-hidden case packets across flat, fixed-session, and operation-stack views.

R305 reuses the R300/R302/R304 task operations. It does not fetch data. The
goal is to make the case-packet evidence falsifiable against two simpler
views: a flat per-task grouping and a fixed session grouping. Oracle labels stay
in the answer key and are used only after visible query-aware ranking.
"""

from __future__ import annotations

import argparse
import html
import json
import sys
from collections import defaultdict
from pathlib import Path
from statistics import median
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
OUT_ROOT = ROOT / "docs" / "visexp" / "out"
DEFAULT_OUT_DIR = OUT_ROOT / "operation-case-baseline-r305"

sys.path.insert(0, str(Path(__file__).resolve().parent))
import operation_analyst_ranking_eval as r302  # noqa: E402
import operation_case_study_eval as r304  # noqa: E402
import operation_query_utility_eval as r300  # noqa: E402


VIEWS = ["flat", "fixed_session", "operation_stack"]
CASE_GROUPS_PER_TASK = 5


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--groups-per-task", type=int, default=CASE_GROUPS_PER_TASK)
    return parser.parse_args()


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def group_task_view(
    task: dict[str, Any],
    view: str,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    operations = r300.load_task_operations(task)
    stack = r300.stack_for_view(task, view)
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for operation in operations:
        grouped[r302.stack_label(operation["fields"], stack)].append(operation)

    groups = []
    total_ops = 0
    total_positive = 0
    for stack_key, rows in grouped.items():
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
                "stack": stack_key,
                "stack_frames": r304.stack_frames(stack_key),
                "operations": operations_in_group,
                "positives": positives,
                "sessions": len(sessions),
                "session_examples": [r304.short_hash(session) for session in sessions[:5]],
                "features": r302.visible_features(rows),
                "field_examples": r304.visible_field_examples(rows),
                "operation_examples": r304.visible_operation_examples(rows),
            }
        )

    summary = {
        "operations": total_ops,
        "positives": total_positive,
        "prevalence": total_positive / total_ops if total_ops else 0.0,
        "groups": len(groups),
    }
    return groups, summary


def score_selected(selected: list[dict[str, Any]], summary: dict[str, Any]) -> dict[str, Any]:
    inspected_ops = sum(group["operations"] for group in selected)
    positives = sum(group["positives"] for group in selected)
    total_ops = summary["operations"]
    total_positive = summary["positives"]
    prevalence = summary["prevalence"]
    precision = positives / inspected_ops if inspected_ops else 0.0
    return {
        "groups": len(selected),
        "inspected_operations": inspected_ops,
        "inspected_operation_fraction": inspected_ops / total_ops if total_ops else 0.0,
        "positive_operations": positives,
        "positive_recall": positives / total_positive if total_positive else 0.0,
        "positive_precision": precision,
        "positive_lift": precision / prevalence if prevalence else 0.0,
    }


def visible_group(group: dict[str, Any], view: str, rank: int) -> dict[str, Any]:
    group_key = f"{view}:{group['stack']}"
    return {
        "rank": rank,
        "group_id": r304.short_hash(group_key),
        "stack": group["stack"],
        "stack_frames": group["stack_frames"],
        "operations": group["operations"],
        "sessions": group["sessions"],
        "session_examples": group["session_examples"],
        "visible_features": group["features"],
        "field_examples": group["field_examples"],
        "operation_examples": group["operation_examples"],
    }


def answer_group(group: dict[str, Any], view: str, rank: int) -> dict[str, Any]:
    operations = group["operations"]
    positives = group["positives"]
    return {
        "rank": rank,
        "group_id": r304.short_hash(f"{view}:{group['stack']}"),
        "operations": operations,
        "positive_operations": positives,
        "positive_rate": positives / operations if operations else 0.0,
    }


def build_cases(groups_per_task: int) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    visible_cases = []
    answer_cases = []
    task_view_scores = []
    for task in r300.TASKS:
        for view in VIEWS:
            groups, summary = group_task_view(task, view)
            ranked = sorted(
                groups,
                key=lambda group: r302.rank_score(group, task, "query_aware"),
                reverse=True,
            )
            selected = ranked[:groups_per_task]
            score = score_selected(selected, summary)
            visible_cases.append(
                {
                    "task": task["id"],
                    "dataset": task["dataset"],
                    "query_family": task["query_family"],
                    "problem": task["problem"],
                    "view": view,
                    "ranker": "query_aware",
                    "groups": [
                        visible_group(group, view, index)
                        for index, group in enumerate(selected, 1)
                    ],
                }
            )
            answer_cases.append(
                {
                    "task": task["id"],
                    "dataset": task["dataset"],
                    "view": view,
                    "oracle_field": task["oracle_field"],
                    "positive_values": sorted(task["positive_values"]),
                    "score": score,
                    "groups": [
                        answer_group(group, view, index)
                        for index, group in enumerate(selected, 1)
                    ],
                }
            )
            task_view_scores.append(
                {
                    "task": task["id"],
                    "dataset": task["dataset"],
                    "query_family": task["query_family"],
                    "problem": task["problem"],
                    "view": view,
                    "available_groups": summary["groups"],
                    "operations": summary["operations"],
                    "positives": summary["positives"],
                    **round_score(score),
                }
            )

    summary = summarize_scores(task_view_scores)
    report = {
        "run_id": "R305",
        "purpose": "compare label-hidden case packets against flat and fixed-session baselines",
        "input_policy": "no dataset sync; reuses existing R300 task operations and R302 query-aware ranking",
        "views": VIEWS,
        "ranker": "query_aware",
        "groups_per_task": groups_per_task,
        "tasks": len(r300.TASKS),
        "task_view_scores": task_view_scores,
        "summary": summary,
        "claim_scope": {
            "supported": "operation-stack case packets provide a middle ground between flat all-task packets and fixed-session fragmentation on existing labeled tasks",
            "narrowed": "the comparison is an automated label-hidden proxy, not a human study or detector benchmark",
            "not_supported": "automatic anomaly detection, fully optimal ranking, or guaranteed dominance over fixed-session views on every task",
        },
        "headline": build_headline(summary),
    }
    visible_packet = {
        "run_id": "R305",
        "purpose": "label-hidden cross-view reviewer case packets",
        "input_policy": report["input_policy"],
        "views": VIEWS,
        "ranker": "query_aware",
        "visible_fields": r304.VISIBLE_OPERATION_FIELDS,
        "withheld_field_policy": "oracle and scoring fields are omitted from visible packets and kept in the answer key",
        "cases": visible_cases,
    }
    answer_key = {
        "run_id": "R305",
        "purpose": "hidden scoring for R305 visible cross-view case packets",
        "cases": answer_cases,
    }
    return visible_packet, answer_key, report


def round_score(score: dict[str, Any]) -> dict[str, Any]:
    return {
        key: round(value, 4) if isinstance(value, float) else value
        for key, value in score.items()
    }


def summarize_scores(rows: list[dict[str, Any]]) -> dict[str, Any]:
    by_view: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_view[row["view"]].append(row)

    view_summary = {}
    for view, items in by_view.items():
        view_summary[view] = {
            "tasks": len(items),
            "median_available_groups": round(median(row["available_groups"] for row in items), 3),
            "median_selected_groups": round(median(row["groups"] for row in items), 3),
            "median_inspected_operation_fraction": round(
                median(row["inspected_operation_fraction"] for row in items), 4
            ),
            "median_positive_recall": round(
                median(row["positive_recall"] for row in items), 4
            ),
            "median_positive_precision": round(
                median(row["positive_precision"] for row in items), 4
            ),
            "median_positive_lift": round(median(row["positive_lift"] for row in items), 4),
            "tasks_with_lift_ge_1": sum(row["positive_lift"] >= 1.0 for row in items),
        }

    return {
        "by_view": view_summary,
        "operation_stack_vs_flat": compare_views(rows, "operation_stack", "flat"),
        "operation_stack_vs_fixed_session": compare_views(
            rows, "operation_stack", "fixed_session"
        ),
    }


def compare_views(rows: list[dict[str, Any]], left: str, right: str) -> dict[str, Any]:
    by_key = {(row["task"], row["view"]): row for row in rows}
    tasks = sorted({row["task"] for row in rows})
    recall_ratios = []
    lift_ratios = []
    work_ratios = []
    precision_ratios = []
    group_ratios = []
    left_better_lift = 0
    left_lower_work = 0
    for task in tasks:
        lhs = by_key.get((task, left))
        rhs = by_key.get((task, right))
        if not lhs or not rhs:
            continue
        recall_ratios.append(safe_ratio(lhs["positive_recall"], rhs["positive_recall"]))
        lift_ratios.append(safe_ratio(lhs["positive_lift"], rhs["positive_lift"]))
        work_ratios.append(
            safe_ratio(lhs["inspected_operation_fraction"], rhs["inspected_operation_fraction"])
        )
        precision_ratios.append(
            safe_ratio(lhs["positive_precision"], rhs["positive_precision"])
        )
        group_ratios.append(safe_ratio(lhs["groups"], rhs["groups"]))
        left_better_lift += int(lhs["positive_lift"] > rhs["positive_lift"])
        left_lower_work += int(
            lhs["inspected_operation_fraction"] < rhs["inspected_operation_fraction"]
        )
    return {
        "left": left,
        "right": right,
        "tasks": len(recall_ratios),
        "median_positive_recall_ratio": round(median(recall_ratios), 4),
        "median_positive_lift_ratio": round(median(lift_ratios), 4),
        "median_inspected_operation_fraction_ratio": round(median(work_ratios), 4),
        "median_positive_precision_ratio": round(median(precision_ratios), 4),
        "median_selected_group_ratio": round(median(group_ratios), 4),
        "left_higher_lift_tasks": left_better_lift,
        "left_lower_work_tasks": left_lower_work,
    }


def safe_ratio(left: float | int, right: float | int) -> float:
    if right == 0:
        return 0.0 if left == 0 else float("inf")
    return float(left) / float(right)


def build_headline(summary: dict[str, Any]) -> str:
    stack = summary["by_view"]["operation_stack"]
    flat = summary["by_view"]["flat"]
    fixed = summary["by_view"]["fixed_session"]
    stack_vs_flat = summary["operation_stack_vs_flat"]
    stack_vs_fixed = summary["operation_stack_vs_fixed_session"]
    return (
        "R305 compares the same label-hidden case-packet task across flat, fixed-session, "
        "and operation-stack views. Top-5 query-aware operation-stack packets inspect "
        f"a median {stack['median_inspected_operation_fraction'] * 100:.1f}% of operations "
        f"with lift {stack['median_positive_lift']:.3f}. Flat packets recover "
        f"{flat['median_positive_recall'] * 100:.1f}% recall by inspecting "
        f"{flat['median_inspected_operation_fraction'] * 100:.1f}% of operations, while "
        f"fixed-session packets inspect {fixed['median_inspected_operation_fraction'] * 100:.1f}% "
        f"with lift {fixed['median_positive_lift']:.3f}. Operation stacks reduce work versus "
        f"flat by a median ratio of {stack_vs_flat['median_inspected_operation_fraction_ratio']:.3f} "
        f"and improve lift versus fixed-session by a median ratio of "
        f"{stack_vs_fixed['median_positive_lift_ratio']:.3f}."
    )


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# R305 Cross-View Case-Packet Baseline",
        "",
        report["headline"],
        "",
        "## View Summary",
        "",
        "| View | Tasks | Available groups | Selected groups | Work fraction | Recall | Precision | Lift | Lift>=1 tasks |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for view in VIEWS:
        row = report["summary"]["by_view"][view]
        lines.append(
            f"| {view} | {row['tasks']} | {row['median_available_groups']} | {row['median_selected_groups']} | {row['median_inspected_operation_fraction']} | {row['median_positive_recall']} | {row['median_positive_precision']} | {row['median_positive_lift']} | {row['tasks_with_lift_ge_1']} |"
        )

    lines.extend(
        [
            "",
            "## Task-View Scores",
            "",
            "| Task | View | Available groups | Work fraction | Recall | Precision | Lift |",
            "|---|---|---:|---:|---:|---:|---:|",
        ]
    )
    for row in report["task_view_scores"]:
        lines.append(
            f"| {row['task']} | {row['view']} | {row['available_groups']} | {row['inspected_operation_fraction']} | {row['positive_recall']} | {row['positive_precision']} | {row['positive_lift']} |"
        )

    lines.extend(
        [
            "",
            "## Claim Scope",
            "",
            "- Supports: operation-stack case packets provide a label-hidden middle ground between flat all-task packets and fixed-session fragmentation.",
            "- Narrows: operation stacks do not dominate fixed-session packets on every task; this is an automated proxy, not a human study.",
            "- Integrity: visible packet fields exclude hidden oracle labels; the answer key is separate.",
        ]
    )
    return "\n".join(lines) + "\n"


def render_html(report: dict[str, Any]) -> str:
    summary_rows = "".join(
        "<tr>"
        f"<td>{html.escape(view)}</td>"
        f"<td>{row['median_available_groups']}</td>"
        f"<td>{row['median_inspected_operation_fraction']}</td>"
        f"<td>{row['median_positive_recall']}</td>"
        f"<td>{row['median_positive_lift']}</td>"
        f"<td>{row['tasks_with_lift_ge_1']}</td>"
        "</tr>"
        for view, row in report["summary"]["by_view"].items()
    )
    task_rows = "".join(
        "<tr>"
        f"<td>{html.escape(row['task'])}</td>"
        f"<td>{html.escape(row['view'])}</td>"
        f"<td>{row['available_groups']}</td>"
        f"<td>{row['inspected_operation_fraction']}</td>"
        f"<td>{row['positive_recall']}</td>"
        f"<td>{row['positive_precision']}</td>"
        f"<td>{row['positive_lift']}</td>"
        "</tr>"
        for row in report["task_view_scores"]
    )
    return f"""<!doctype html>
<meta charset="utf-8">
<title>R305 Cross-View Case-Packet Baseline</title>
<style>
body {{ font-family: system-ui, sans-serif; margin: 32px; color: #202124; }}
p {{ max-width: 980px; line-height: 1.5; }}
table {{ border-collapse: collapse; width: 100%; margin-top: 20px; font-size: 13px; }}
th, td {{ border-bottom: 1px solid #d7dce2; padding: 7px 8px; text-align: left; }}
th {{ background: #edf1f5; }}
</style>
<h1>R305 Cross-View Case-Packet Baseline</h1>
<p>{html.escape(report['headline'])}</p>
<h2>View Summary</h2>
<table>
<thead><tr><th>View</th><th>Available groups</th><th>Work fraction</th><th>Recall</th><th>Lift</th><th>Lift>=1 tasks</th></tr></thead>
<tbody>{summary_rows}</tbody>
</table>
<h2>Task-View Scores</h2>
<table>
<thead><tr><th>Task</th><th>View</th><th>Available groups</th><th>Work fraction</th><th>Recall</th><th>Precision</th><th>Lift</th></tr></thead>
<tbody>{task_rows}</tbody>
</table>
"""


def main() -> None:
    args = parse_args()
    r302.validate_no_hidden_rank_features()
    out_dir = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    visible_packet, answer_key, report = build_cases(args.groups_per_task)
    r304.assert_visible_packet_has_no_hidden_fields(visible_packet)

    visible_path = out_dir / "visible-case-packets.json"
    answer_path = out_dir / "answer-key.json"
    report_path = out_dir / "case-baseline-report.json"
    markdown_path = out_dir / "case-baseline-report.md"
    html_path = out_dir / "index.html"

    visible_path.write_text(json.dumps(visible_packet, indent=2, sort_keys=True) + "\n")
    answer_path.write_text(json.dumps(answer_key, indent=2, sort_keys=True) + "\n")
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    markdown_path.write_text(render_markdown(report), encoding="utf-8")
    html_path.write_text(render_html(report), encoding="utf-8")

    run_result = {
        "status": "ok",
        "run_id": "R305",
        "tasks": report["tasks"],
        "views": VIEWS,
        "case_packets": len(visible_packet["cases"]),
        "json": rel(report_path),
        "visible_packet": rel(visible_path),
        "answer_key": rel(answer_path),
        "markdown": rel(markdown_path),
        "html": rel(html_path),
    }
    (out_dir / "run-result.json").write_text(json.dumps(run_result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(run_result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
