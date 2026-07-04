#!/usr/bin/env python3
"""Evaluate width-ranked analyst tasks over existing labeled operations.

R301 is a conservative follow-up to R300. R300 asks how well an oracle could
rank operation-stack groups by label density. R301 asks what a default analyst
sees first when groups are ranked only by width, as in a flamegraph or top-list.
It writes visible packets without oracle labels and a hidden answer key so the
same benchmark can be reviewed or replayed without leaking target labels into
the browsing surface.
"""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from statistics import median
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
OUT_ROOT = ROOT / "docs" / "visexp" / "out"
DEFAULT_OUT_DIR = OUT_ROOT / "operation-analyst-task-r301"

sys.path.insert(0, str(Path(__file__).resolve().parent))
import operation_query_utility_eval as r300  # noqa: E402

TOP_GROUP_BUDGETS = [5, 10, 20]
OPERATION_FRACTION_BUDGETS = [0.10, 0.20, 0.30, 0.50]
VISIBLE_PACKET_GROUPS = 20
VISIBLE_EXAMPLE_LIMIT = 5
HIDDEN_ORACLE_VIEWS = {"label_drilldown"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    return parser.parse_args()


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def short_hash(text: str, length: int = 12) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()[:length]


def stack_label(fields: dict[str, str], stack: list[str]) -> str:
    return ";".join(f"{field}:{fields.get(field, 'unknown')}" for field in stack)


def group_operations(
    operations: list[dict[str, Any]],
    stack: list[str],
    task_id: str,
    view: str,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for operation in operations:
        grouped[stack_label(operation["fields"], stack)].append(operation)

    groups = []
    total_ops = 0
    total_positive = 0
    for key, rows in grouped.items():
        size = sum(int(operation["value"]) for operation in rows)
        positives = sum(
            int(operation["value"])
            for operation in rows
            if operation["fields"].get("target_positive") == "positive"
        )
        sessions = sorted({operation["fields"].get("session", "unknown") for operation in rows})
        total_ops += size
        total_positive += positives
        representative = rows[0]["fields"]
        group_id = f"{task_id}:{view}:{short_hash(key)}"
        groups.append(
            {
                "group_id": group_id,
                "stack": key,
                "stack_frames": [
                    {"field": field, "value": representative.get(field, "unknown")}
                    for field in stack
                ],
                "operations": size,
                "positives": positives,
                "sessions": len(sessions),
                "session_examples": sessions[:VISIBLE_EXAMPLE_LIMIT],
                "field_examples": field_examples(rows),
            }
        )

    ranked = sorted(
        groups,
        key=lambda group: (group["operations"], group["sessions"], group["stack"]),
        reverse=True,
    )
    for index, group in enumerate(ranked, 1):
        group["width_rank"] = index

    summary = {
        "operations": total_ops,
        "positives": total_positive,
        "prevalence": total_positive / total_ops if total_ops else 0.0,
        "groups": len(groups),
        "compression": total_ops / len(groups) if groups else 0.0,
    }
    return ranked, summary


def field_examples(rows: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    counters: dict[str, Counter[str]] = {
        "op": Counter(),
        "phase": Counter(),
        "action": Counter(),
        "tool": Counter(),
        "status": Counter(),
        "repeat_signal": Counter(),
        "environment": Counter(),
        "benchmark": Counter(),
        "app": Counter(),
    }
    for operation in rows:
        fields = operation["fields"]
        weight = int(operation["value"])
        for field, counter in counters.items():
            value = fields.get(field)
            if value:
                counter[value] += weight
    return {
        field: [{"value": value, "operations": count} for value, count in counter.most_common(3)]
        for field, counter in counters.items()
        if counter
    }


def visible_group(group: dict[str, Any]) -> dict[str, Any]:
    return {
        "group_id": group["group_id"],
        "width_rank": group["width_rank"],
        "stack": group["stack"],
        "stack_frames": group["stack_frames"],
        "operations": group["operations"],
        "sessions": group["sessions"],
        "session_examples": group["session_examples"],
        "field_examples": group["field_examples"],
    }


def answer_group(group: dict[str, Any]) -> dict[str, Any]:
    operations = group["operations"]
    positives = group["positives"]
    return {
        "group_id": group["group_id"],
        "width_rank": group["width_rank"],
        "operations": operations,
        "positives": positives,
        "positive_rate": positives / operations if operations else 0.0,
    }


def score_top_k(groups: list[dict[str, Any]], summary: dict[str, Any], k: int) -> dict[str, Any]:
    selected = groups[:k]
    return score_selection(selected, summary, groups_inspected=len(selected), budget=f"top_{k}_groups")


def score_operation_budget(
    groups: list[dict[str, Any]],
    summary: dict[str, Any],
    fraction: float,
) -> dict[str, Any]:
    total_ops = summary["operations"]
    limit = total_ops * fraction
    selected = []
    inspected = 0
    for group in groups:
        if inspected + group["operations"] > limit:
            continue
        selected.append(group)
        inspected += group["operations"]
    return score_selection(
        selected,
        summary,
        groups_inspected=len(selected),
        budget=f"budget_{int(fraction * 100)}pct_operations",
    )


def score_selection(
    selected: list[dict[str, Any]],
    summary: dict[str, Any],
    groups_inspected: int,
    budget: str,
) -> dict[str, Any]:
    inspected_ops = sum(group["operations"] for group in selected)
    positives = sum(group["positives"] for group in selected)
    total_ops = summary["operations"]
    total_positive = summary["positives"]
    prevalence = summary["prevalence"]
    precision = positives / inspected_ops if inspected_ops else 0.0
    return {
        "budget": budget,
        "groups_inspected": groups_inspected,
        "inspected_operations": inspected_ops,
        "inspected_operation_fraction": inspected_ops / total_ops if total_ops else 0.0,
        "positive_recall": positives / total_positive if total_positive else 0.0,
        "positive_precision": precision,
        "positive_lift": precision / prevalence if prevalence else 0.0,
        "positive_operations": positives,
    }


def summarize_scores(rows: list[dict[str, Any]]) -> dict[str, Any]:
    by_view_budget: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    by_view: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_view_budget[(row["view"], row["budget"])].append(row)
        by_view[row["view"]].append(row)

    view_budget_summary = {}
    for (view, budget), items in sorted(by_view_budget.items()):
        view_budget_summary[f"{view}:{budget}"] = {
            "view": view,
            "budget": budget,
            "tasks": len(items),
            "median_positive_recall": round(median(item["positive_recall"] for item in items), 4),
            "median_positive_lift": round(median(item["positive_lift"] for item in items), 4),
            "median_inspected_operation_fraction": round(
                median(item["inspected_operation_fraction"] for item in items), 4
            ),
            "median_groups_inspected": round(median(item["groups_inspected"] for item in items), 3),
            "tasks_with_recall_ge_50pct": sum(item["positive_recall"] >= 0.5 for item in items),
        }

    return {
        "view_budget_summary": view_budget_summary,
        "operation_stack_vs_fixed_session": compare_views(rows, "operation_stack", "fixed_session"),
        "operation_stack_vs_flat": compare_views(rows, "operation_stack", "flat"),
        "operation_stack_vs_label_drilldown": compare_views(
            rows, "operation_stack", "label_drilldown"
        ),
    }


def compare_views(rows: list[dict[str, Any]], left: str, right: str) -> dict[str, Any]:
    by_key = {(row["task"], row["view"], row["budget"]): row for row in rows}
    budgets = sorted({row["budget"] for row in rows})
    out = {}
    for budget in budgets:
        recall_ratios = []
        lift_ratios = []
        group_ratios = []
        work_ratios = []
        for task in sorted({row["task"] for row in rows}):
            lhs = by_key.get((task, left, budget))
            rhs = by_key.get((task, right, budget))
            if not lhs or not rhs:
                continue
            recall_ratios.append(safe_ratio(lhs["positive_recall"], rhs["positive_recall"]))
            lift_ratios.append(safe_ratio(lhs["positive_lift"], rhs["positive_lift"]))
            group_ratios.append(safe_ratio(lhs["groups_inspected"], rhs["groups_inspected"]))
            work_ratios.append(
                safe_ratio(lhs["inspected_operation_fraction"], rhs["inspected_operation_fraction"])
            )
        out[budget] = {
            "left": left,
            "right": right,
            "tasks": len(recall_ratios),
            "median_positive_recall_ratio": round(median(recall_ratios), 4),
            "median_positive_lift_ratio": round(median(lift_ratios), 4),
            "median_groups_inspected_ratio": round(median(group_ratios), 4),
            "median_inspected_operation_fraction_ratio": round(median(work_ratios), 4),
        }
    return out


def safe_ratio(left: float | int, right: float | int) -> float:
    if right == 0:
        return 0.0 if left == 0 else float("inf")
    return float(left) / float(right)


def finite_round(value: float, digits: int = 4) -> float | str:
    if value == float("inf"):
        return "inf"
    return round(value, digits)


def sanitize_numbers(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: sanitize_numbers(item) for key, item in value.items()}
    if isinstance(value, list):
        return [sanitize_numbers(item) for item in value]
    if isinstance(value, float):
        return finite_round(value)
    return value


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# R301 Width-Ranked Analyst Task Proxy",
        "",
        "R301 reuses the labeled operation JSONL from R300 and ranks groups only by width. The visible packet excludes oracle labels; the answer key is separate.",
        "",
        "## Headline",
        "",
        report["headline"],
        "",
        "## Median Scores",
        "",
        "| View | Budget | Tasks | Median recall | Median lift | Median work fraction | Median groups | Tasks recall >= 50% |",
        "|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    for key, row in sorted(report["summary"]["view_budget_summary"].items()):
        lines.append(
            f"| {row['view']} | {row['budget']} | {row['tasks']} | {row['median_positive_recall']} | {row['median_positive_lift']} | {row['median_inspected_operation_fraction']} | {row['median_groups_inspected']} | {row['tasks_with_recall_ge_50pct']} |"
        )
    lines.extend(
        [
            "",
            "## Task Scores",
            "",
            "| Task | View | Budget | Recall | Lift | Work fraction | Groups | Positives found |",
            "|---|---|---|---:|---:|---:|---:|---:|",
        ]
    )
    for row in report["scores"]:
        lines.append(
            f"| {row['task']} | {row['view']} | {row['budget']} | {row['positive_recall']} | {row['positive_lift']} | {row['inspected_operation_fraction']} | {row['groups_inspected']} | {row['positive_operations']} |"
        )
    lines.extend(
        [
            "",
            "## Claim Scope",
            "",
            "- Supports: operation stacks provide a label-free, width-ranked browsing surface that often recovers more labeled problem operations than fixed-session stacks at far fewer inspected groups.",
            "- Narrows: width ranking alone is not sufficient for all safety labels, and oracle label drilldown is not a valid default browsing baseline because it uses the hidden answer.",
            "- Does not support: claims about human productivity or unsupervised anomaly detection without a separate user study or online detector.",
        ]
    )
    return "\n".join(lines) + "\n"


def render_html(report: dict[str, Any]) -> str:
    cards = "".join(
        f"<section><h3>{html.escape(row['view'])}</h3><p>{html.escape(row['budget'])}</p><b>{row['median_positive_recall']}</b><span> median recall</span></section>"
        for row in report["summary"]["view_budget_summary"].values()
        if row["budget"] in {"top_10_groups", "budget_30pct_operations"}
    )
    rows = "".join(
        "<tr>"
        f"<td>{html.escape(row['task'])}</td>"
        f"<td>{html.escape(row['view'])}</td>"
        f"<td>{html.escape(row['budget'])}</td>"
        f"<td>{row['positive_recall']}</td>"
        f"<td>{row['positive_lift']}</td>"
        f"<td>{row['inspected_operation_fraction']}</td>"
        f"<td>{row['groups_inspected']}</td>"
        "</tr>"
        for row in report["scores"]
    )
    return f"""<!doctype html>
<meta charset="utf-8">
<title>R301 Width-Ranked Analyst Task Proxy</title>
<style>
body {{ font-family: system-ui, sans-serif; margin: 32px; color: #202124; }}
.grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(190px, 1fr)); gap: 12px; }}
section {{ border: 1px solid #d7dce2; border-radius: 6px; padding: 12px; background: #fbfcfd; }}
table {{ border-collapse: collapse; width: 100%; margin-top: 24px; font-size: 13px; }}
th, td {{ border-bottom: 1px solid #d7dce2; padding: 7px 8px; text-align: left; }}
th {{ background: #edf1f5; }}
</style>
<h1>R301 Width-Ranked Analyst Task Proxy</h1>
<p>{html.escape(report['headline'])}</p>
<div class="grid">{cards}</div>
<table>
<thead><tr><th>Task</th><th>View</th><th>Budget</th><th>Recall</th><th>Lift</th><th>Work fraction</th><th>Groups</th></tr></thead>
<tbody>{rows}</tbody>
</table>
"""


def validate_visible_packets(packets: list[dict[str, Any]]) -> None:
    payload = json.dumps(packets, sort_keys=True)
    banned = [
        "target_positive",
        "positive_rate",
        "positives",
        "oracle_field",
        "problem_value",
    ]
    leaks = [field for field in banned if field in payload]
    if leaks:
        raise SystemExit(f"visible task packet leaks hidden answer fields: {', '.join(leaks)}")
    for packet in packets:
        if packet["view"] in HIDDEN_ORACLE_VIEWS:
            if packet.get("visibility") != "hidden_oracle_baseline" or packet.get("groups"):
                raise SystemExit(f"oracle view {packet['view']} must not expose visible groups")
        elif packet.get("visibility") != "visible":
            raise SystemExit(f"non-oracle view {packet['view']} must be visible")


def build_headline(summary: dict[str, Any]) -> str:
    rows = summary["view_budget_summary"]
    operation_budget = rows["operation_stack:budget_30pct_operations"]
    fixed_budget = rows["fixed_session:budget_30pct_operations"]
    operation_top = rows["operation_stack:top_10_groups"]
    fixed_top = rows["fixed_session:top_10_groups"]
    return (
        "At a 30% inspected-operation budget, operation stacks recover a median "
        f"{operation_budget['median_positive_recall'] * 100:.1f}% of hidden positives "
        f"while inspecting {operation_budget['median_groups_inspected']} groups; "
        f"fixed-session stacks recover {fixed_budget['median_positive_recall'] * 100:.1f}% "
        f"while inspecting {fixed_budget['median_groups_inspected']} groups. At top-10 "
        "width-ranked groups, operation stacks recover a median "
        f"{operation_top['median_positive_recall'] * 100:.1f}% of positives, compared with "
        f"{fixed_top['median_positive_recall'] * 100:.1f}% for fixed-session stacks, but "
        "they require a larger work fraction, so the result supports cross-session "
        "aggregation rather than a universal default-ranking win."
    )


def main() -> None:
    args = parse_args()
    out_dir = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    visible_packets = []
    answer_key = []
    score_rows = []
    task_metadata = []
    source_files = sorted({rel(task["operation_file"]) for task in r300.TASKS})

    for task in r300.TASKS:
        operations = r300.load_task_operations(task)
        if not operations:
            raise SystemExit(f"task {task['id']} produced no operations")
        task_metadata.append(
            {
                "task": task["id"],
                "dataset": task["dataset"],
                "problem": task["problem"],
                "oracle_field": task["oracle_field"],
                "source_operation_file": rel(task["operation_file"]),
                "operations": sum(int(operation["value"]) for operation in operations),
            }
        )
        for view in r300.VIEW_SPECS:
            stack = r300.stack_for_view(task, view)
            groups, group_summary = group_operations(operations, stack, task["id"], view)
            packet = {
                "task": task["id"],
                "dataset": task["dataset"],
                "view": view,
                "problem": task["problem"],
                "ranking": "width_descending",
                "groups": [],
            }
            if view in HIDDEN_ORACLE_VIEWS:
                packet["visibility"] = "hidden_oracle_baseline"
                packet["note"] = (
                    "This view is scored as an oracle baseline and is omitted from the "
                    "visible packet because it uses hidden answer labels."
                )
            else:
                packet["visibility"] = "visible"
                packet["stack"] = stack
                packet["groups"] = [
                    visible_group(group) for group in groups[:VISIBLE_PACKET_GROUPS]
                ]
            visible_packets.append(packet)
            answer_key.append(
                {
                    "task": task["id"],
                    "view": view,
                    "oracle_field": task["oracle_field"],
                    "positive_values": sorted(task["positive_values"]),
                    "total_operations": group_summary["operations"],
                    "total_positive_operations": group_summary["positives"],
                    "groups": [answer_group(group) for group in groups],
                }
            )
            for k in TOP_GROUP_BUDGETS:
                score_rows.append(
                    {
                        "task": task["id"],
                        "dataset": task["dataset"],
                        "view": view,
                        **score_top_k(groups, group_summary, k),
                    }
                )
            for fraction in OPERATION_FRACTION_BUDGETS:
                score_rows.append(
                    {
                        "task": task["id"],
                        "dataset": task["dataset"],
                        "view": view,
                        **score_operation_budget(groups, group_summary, fraction),
                    }
                )

    score_rows = [sanitize_numbers(row) for row in score_rows]
    summary = sanitize_numbers(summarize_scores(score_rows))
    headline = build_headline(summary)
    report = {
        "run_id": "R301",
        "purpose": "width-ranked analyst-task proxy over existing labeled operation traces",
        "input_policy": "no dataset sync; reuses tracked operation JSONL from R288-R291/R300",
        "source_operation_files": source_files,
        "tasks": task_metadata,
        "visible_task_packets": rel(out_dir / "visible-task-packets.json"),
        "hidden_answer_key": rel(out_dir / "answer-key.json"),
        "budgets": {
            "top_group_budgets": TOP_GROUP_BUDGETS,
            "operation_fraction_budgets": OPERATION_FRACTION_BUDGETS,
        },
        "headline": headline,
        "summary": summary,
        "scores": score_rows,
        "claim_scope": {
            "supported": "operation stacks provide a label-free width-ranked browsing surface that reduces fixed-session fragmentation and exposes many labeled problem operations across real annotated trajectories",
            "narrowed": "width ranking is a browsing heuristic, not a detector; some labels remain buried without oracle-aware or learned ranking",
            "not_supported": "human productivity improvement, fully unsupervised anomaly detection, or production online alert quality",
        },
    }
    validate_visible_packets(visible_packets)

    visible_path = out_dir / "visible-task-packets.json"
    answer_path = out_dir / "answer-key.json"
    report_path = out_dir / "analyst-task-report.json"
    markdown_path = out_dir / "analyst-task-report.md"
    html_path = out_dir / "index.html"
    visible_path.write_text(json.dumps(visible_packets, indent=2, sort_keys=True) + "\n")
    answer_path.write_text(json.dumps(answer_key, indent=2, sort_keys=True) + "\n")
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    markdown_path.write_text(render_markdown(report), encoding="utf-8")
    html_path.write_text(render_html(report), encoding="utf-8")

    run_result = {
        "status": "ok",
        "run_id": "R301",
        "tasks": len(r300.TASKS),
        "views": list(r300.VIEW_SPECS),
        "scores": len(score_rows),
        "json": rel(report_path),
        "markdown": rel(markdown_path),
        "html": rel(html_path),
        "visible_task_packets": rel(visible_path),
        "hidden_answer_key": rel(answer_path),
    }
    (out_dir / "run-result.json").write_text(json.dumps(run_result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(run_result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
