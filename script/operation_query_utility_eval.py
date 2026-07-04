#!/usr/bin/env python3
"""Evaluate operation-stack views on oracle-backed analysis tasks.

R300 is an automated proxy for user utility. It does not simulate humans and it
does not fetch new data. Instead, it turns existing labeled operation JSONL into
analysis tasks such as "localize looping" or "localize unsafe operations", then
compares flat, fixed-session, semantic operation-stack, and label-drilldown
views as groupings over the same operations.
"""

from __future__ import annotations

import argparse
import html
import json
import math
from collections import Counter, defaultdict
from pathlib import Path
from statistics import median
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OUT_ROOT = ROOT / "docs" / "visexp" / "out"
DEFAULT_OUT_DIR = OUT_ROOT / "operation-query-utility-r300"


TASKS = [
    {
        "id": "agentreward_looping",
        "dataset": "agent-reward-bench",
        "query_family": "failure-looping",
        "operation_file": OUT_ROOT
        / "external-agent-trace-agentreward-r288"
        / "agentreward-operations.jsonl",
        "oracle_field": "looping",
        "positive_values": {"yes"},
        "problem": "Find repetitive web-agent behavior in expert-reviewed trajectories.",
        "semantic_stack": [
            "analysis_task",
            "dataset",
            "benchmark",
            "phase",
            "action",
            "repeat_signal",
            "status",
        ],
        "label_stack": [
            "analysis_task",
            "dataset",
            "target_positive",
            "phase",
            "action",
            "repeat_signal",
            "status",
        ],
    },
    {
        "id": "agentreward_side_effect",
        "dataset": "agent-reward-bench",
        "query_family": "failure-side-effect",
        "operation_file": OUT_ROOT
        / "external-agent-trace-agentreward-r288"
        / "agentreward-operations.jsonl",
        "oracle_field": "side_effect",
        "positive_values": {"yes"},
        "problem": "Find side-effectful web-agent trajectories.",
        "semantic_stack": [
            "analysis_task",
            "dataset",
            "benchmark",
            "phase",
            "action",
            "repeat_signal",
            "status",
        ],
        "label_stack": [
            "analysis_task",
            "dataset",
            "target_positive",
            "phase",
            "action",
            "repeat_signal",
            "status",
        ],
    },
    {
        "id": "satraj_unsafe",
        "dataset": "satraj-os-safety",
        "query_family": "safety",
        "operation_file": OUT_ROOT / "external-agent-trace-satraj-r289" / "satraj-operations.jsonl",
        "oracle_field": "safety",
        "positive_values": {"unsafe"},
        "problem": "Find unsafe desktop computer-use operations.",
        "semantic_stack": [
            "analysis_task",
            "dataset",
            "environment",
            "phase",
            "action",
            "repeat_signal",
            "status",
        ],
        "label_stack": [
            "analysis_task",
            "dataset",
            "target_positive",
            "environment",
            "phase",
            "action",
            "repeat_signal",
        ],
    },
    {
        "id": "agentnet_incorrect_step",
        "dataset": "agentnet",
        "query_family": "step-quality",
        "operation_file": OUT_ROOT / "external-agent-trace-agentnet-r291" / "agentnet-operations.jsonl",
        "oracle_field": "step_correct",
        "positive_values": {"incorrect"},
        "exclude_values": {"unknown"},
        "problem": "Find incorrect human desktop steps.",
        "semantic_stack": [
            "analysis_task",
            "dataset",
            "environment",
            "phase",
            "action",
            "repeat_signal",
            "status",
        ],
        "label_stack": [
            "analysis_task",
            "dataset",
            "target_positive",
            "environment",
            "phase",
            "action",
            "repeat_signal",
        ],
    },
    {
        "id": "agentnet_redundant_step",
        "dataset": "agentnet",
        "query_family": "step-quality",
        "operation_file": OUT_ROOT / "external-agent-trace-agentnet-r291" / "agentnet-operations.jsonl",
        "oracle_field": "step_redundant",
        "positive_values": {"redundant"},
        "exclude_values": {"unknown"},
        "problem": "Find redundant human desktop steps.",
        "semantic_stack": [
            "analysis_task",
            "dataset",
            "environment",
            "phase",
            "action",
            "repeat_signal",
            "status",
        ],
        "label_stack": [
            "analysis_task",
            "dataset",
            "target_positive",
            "environment",
            "phase",
            "action",
            "repeat_signal",
        ],
    },
    {
        "id": "osworld_group_start",
        "dataset": "osworld-human",
        "query_family": "human-boundary",
        "operation_file": OUT_ROOT
        / "external-agent-trace-osworldhuman-r290"
        / "osworld-human-operations.jsonl",
        "oracle_field": "group_position",
        "positive_values": {"start"},
        "require": {"group_alignment": "exact"},
        "problem": "Find human grouped-action segment starts in desktop traces.",
        "semantic_stack": [
            "analysis_task",
            "dataset",
            "app",
            "phase",
            "action",
            "repeat_signal",
            "status",
        ],
        "label_stack": [
            "analysis_task",
            "dataset",
            "target_positive",
            "group_pattern",
            "phase",
            "action",
        ],
    },
]

VIEW_SPECS = {
    "flat": ["analysis_task", "dataset"],
    "fixed_session": ["analysis_task", "dataset", "session"],
    "operation_stack": None,
    "label_drilldown": None,
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--top-groups", type=int, default=5)
    return parser.parse_args()


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def normalize_fields(fields: dict[str, Any]) -> dict[str, str]:
    out = {}
    for key, value in fields.items():
        if isinstance(value, list):
            if not value:
                continue
            value = value[0]
        if isinstance(value, (dict, list)):
            text = json.dumps(value, sort_keys=True, ensure_ascii=True)
        else:
            text = str(value)
        if text:
            out[str(key)] = text
    return out


def load_task_operations(task: dict[str, Any]) -> list[dict[str, Any]]:
    operations = []
    path = task["operation_file"]
    exclude_values = set(task.get("exclude_values", set()))
    requirements = dict(task.get("require", {}))
    with path.open(encoding="utf-8") as file:
        for line_number, line in enumerate(file, 1):
            if not line.strip():
                continue
            row = json.loads(line)
            fields = normalize_fields(row.get("fields") or {})
            oracle = fields.get(task["oracle_field"])
            if not oracle or oracle in exclude_values:
                continue
            if any(fields.get(key) != value for key, value in requirements.items()):
                continue
            positive = oracle in task["positive_values"]
            fields = dict(fields)
            fields.update(
                {
                    "analysis_task": task["id"],
                    "query_family": task["query_family"],
                    "problem_oracle": task["oracle_field"],
                    "problem_value": oracle,
                    "target_positive": "positive" if positive else "negative",
                    "source_operation_file": rel(path),
                }
            )
            operations.append(
                {
                    "fields": fields,
                    "value": int(row.get("value") or 1),
                    "_source_line": line_number,
                }
            )
    return operations


def stack_for_view(task: dict[str, Any], view: str) -> list[str]:
    if view == "operation_stack":
        return list(task["semantic_stack"])
    if view == "label_drilldown":
        return list(task["label_stack"])
    return list(VIEW_SPECS[view] or [])


def stack_key(fields: dict[str, str], stack: list[str]) -> str:
    return ";".join(f"{field}:{fields.get(field, 'unknown')}" for field in stack)


def evaluate_view(
    operations: list[dict[str, Any]],
    stack: list[str],
    top_groups: int,
) -> dict[str, Any]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for operation in operations:
        grouped[stack_key(operation["fields"], stack)].append(operation)

    groups = []
    total_ops = 0
    total_positive = 0
    for key, rows in grouped.items():
        size = sum(operation["value"] for operation in rows)
        positives = sum(
            operation["value"]
            for operation in rows
            if operation["fields"].get("target_positive") == "positive"
        )
        sessions = {operation["fields"].get("session", "unknown") for operation in rows}
        total_ops += size
        total_positive += positives
        groups.append(
            {
                "stack": key,
                "operations": size,
                "positives": positives,
                "positive_rate": positives / size if size else 0.0,
                "sessions": len(sessions),
            }
        )

    prevalence = total_positive / total_ops if total_ops else 0.0
    ranked = sorted(
        groups,
        key=lambda group: (
            group["positive_rate"],
            group["positives"],
            -group["operations"],
            group["sessions"],
        ),
        reverse=True,
    )
    top = ranked[:top_groups]
    top_ops = sum(group["operations"] for group in top)
    top_positive = sum(group["positives"] for group in top)
    top_precision = top_positive / top_ops if top_ops else 0.0
    top_recall = top_positive / total_positive if total_positive else 0.0
    inspection_fraction = inspection_fraction_for_recall(ranked, total_ops, total_positive, 0.5)
    avg_top_sessions = sum(group["sessions"] for group in top) / len(top) if top else 0.0
    positive_groups = [group for group in groups if group["positives"] > 0]
    avg_positive_group_sessions = (
        sum(group["sessions"] for group in positive_groups) / len(positive_groups)
        if positive_groups
        else 0.0
    )
    return {
        "stack": stack,
        "operations": total_ops,
        "positives": total_positive,
        "prevalence": round(prevalence, 4),
        "groups": len(groups),
        "compression": round(total_ops / len(groups), 3) if groups else 0.0,
        "positive_groups": len(positive_groups),
        "top_groups": top_groups,
        "top_positive_precision": round(top_precision, 4),
        "top_positive_recall": round(top_recall, 4),
        "top_positive_lift": round(top_precision / prevalence, 3) if prevalence else 0.0,
        "inspection_fraction_for_50pct_positives": round(inspection_fraction, 4)
        if inspection_fraction is not None
        else None,
        "avg_top_group_sessions": round(avg_top_sessions, 3),
        "avg_positive_group_sessions": round(avg_positive_group_sessions, 3),
        "top_group_examples": [
            {
                "stack": group["stack"],
                "operations": group["operations"],
                "positives": group["positives"],
                "positive_rate": round(group["positive_rate"], 4),
                "sessions": group["sessions"],
            }
            for group in top
        ],
    }


def inspection_fraction_for_recall(
    ranked_groups: list[dict[str, Any]],
    total_ops: int,
    total_positive: int,
    target_recall: float,
) -> float | None:
    if not total_ops or not total_positive:
        return None
    needed = total_positive * target_recall
    seen_ops = 0
    seen_positive = 0
    for group in ranked_groups:
        seen_ops += group["operations"]
        seen_positive += group["positives"]
        if seen_positive >= needed:
            return seen_ops / total_ops
    return 1.0


def summarize(task_results: list[dict[str, Any]]) -> dict[str, Any]:
    by_view: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in task_results:
        by_view[row["view"]].append(row)

    view_summary = {}
    for view, rows in by_view.items():
        view_summary[view] = {
            "tasks": len(rows),
            "median_groups": round(median(row["groups"] for row in rows), 3),
            "median_compression": round(median(row["compression"] for row in rows), 3),
            "median_top_positive_lift": round(median(row["top_positive_lift"] for row in rows), 3),
            "median_inspection_fraction_for_50pct_positives": round(
                median(row["inspection_fraction_for_50pct_positives"] for row in rows), 4
            ),
            "median_avg_top_group_sessions": round(
                median(row["avg_top_group_sessions"] for row in rows), 3
            ),
        }

    return {
        "views": view_summary,
        "operation_stack_vs_flat": compare_views(by_view, "operation_stack", "flat"),
        "operation_stack_vs_fixed_session": compare_views(
            by_view, "operation_stack", "fixed_session"
        ),
        "label_drilldown_vs_operation_stack": compare_views(
            by_view, "label_drilldown", "operation_stack"
        ),
    }


def compare_views(
    by_view: dict[str, list[dict[str, Any]]],
    left: str,
    right: str,
) -> dict[str, Any]:
    left_rows = {row["task"]: row for row in by_view[left]}
    right_rows = {row["task"]: row for row in by_view[right]}
    common = sorted(set(left_rows) & set(right_rows))
    lift_ratios = []
    inspection_ratios = []
    group_ratios = []
    top_session_ratios = []
    for task in common:
        lhs = left_rows[task]
        rhs = right_rows[task]
        lift_ratios.append(safe_ratio(lhs["top_positive_lift"], rhs["top_positive_lift"]))
        inspection_ratios.append(
            safe_ratio(
                lhs["inspection_fraction_for_50pct_positives"],
                rhs["inspection_fraction_for_50pct_positives"],
            )
        )
        group_ratios.append(safe_ratio(lhs["groups"], rhs["groups"]))
        top_session_ratios.append(
            safe_ratio(lhs["avg_top_group_sessions"], rhs["avg_top_group_sessions"])
        )
    return {
        "left": left,
        "right": right,
        "tasks": len(common),
        "median_top_positive_lift_ratio": round(median(lift_ratios), 3),
        "median_inspection_fraction_ratio": round(median(inspection_ratios), 3),
        "median_group_count_ratio": round(median(group_ratios), 3),
        "median_top_group_session_ratio": round(median(top_session_ratios), 3),
    }


def safe_ratio(left: float | int | None, right: float | int | None) -> float:
    if left is None or right in (None, 0):
        return 0.0
    return float(left) / float(right)


def write_operations(path: Path, operations: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as out:
        for operation in operations:
            out.write(json.dumps({"value": operation["value"], "fields": operation["fields"]}, sort_keys=True) + "\n")


def write_profile_specs(out_dir: Path, operation_file: Path) -> dict[str, str]:
    specs = {}
    generic_stacks = {
        "flat": VIEW_SPECS["flat"],
        "fixed_session": VIEW_SPECS["fixed_session"],
        "operation_stack": [
            "analysis_task",
            "dataset",
            "query_family",
            "environment",
            "phase",
            "action",
            "repeat_signal",
            "status",
        ],
        "label_drilldown": [
            "analysis_task",
            "dataset",
            "target_positive",
            "query_family",
            "phase",
            "action",
            "repeat_signal",
            "status",
        ],
    }
    for view, stack in generic_stacks.items():
        spec_path = out_dir / f"{view}-profile-spec.json"
        payload = {
            "output": f"{view}.folded",
            "format": "folded",
            "view": "operations",
            "operation_files": [operation_file.name],
            "stack": ",".join(stack or []),
            "project_name": "external-agent-traces",
        }
        spec_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
        specs[view] = rel(spec_path)
    return specs


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# R300 Operation-Query Utility",
        "",
        "This run uses existing tracked operation JSONL only. It is an automated oracle-backed proxy for analysis utility, not a human user study.",
        "",
        "## View Summary",
        "",
        "| View | Tasks | Median groups | Median top-positive lift | Median inspection fraction for 50% positives | Median top-group sessions |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for view, row in report["summary"]["views"].items():
        lines.append(
            f"| {view} | {row['tasks']} | {row['median_groups']} | {row['median_top_positive_lift']} | {row['median_inspection_fraction_for_50pct_positives']} | {row['median_avg_top_group_sessions']} |"
        )
    lines.extend(
        [
            "",
            "## Task Results",
            "",
            "| Task | View | Ops | Positives | Groups | Top lift | Inspect frac @50% positives | Top sessions |",
            "|---|---|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for row in report["task_results"]:
        lines.append(
            f"| {row['task']} | {row['view']} | {row['operations']} | {row['positives']} | {row['groups']} | {row['top_positive_lift']} | {row['inspection_fraction_for_50pct_positives']} | {row['avg_top_group_sessions']} |"
        )
    lines.extend(
        [
            "",
            "## Claim Scope",
            "",
            "- Supports: operation-stack views can make existing labeled problems more inspectable than flat summaries, while avoiding fixed-session fragmentation.",
            "- Does not support: human productivity improvement, unsupervised intent discovery, or online anomaly detection without labels/proxies.",
        ]
    )
    return "\n".join(lines) + "\n"


def render_html(report: dict[str, Any]) -> str:
    rows = "".join(
        "<tr>"
        f"<td>{html.escape(row['task'])}</td>"
        f"<td>{html.escape(row['view'])}</td>"
        f"<td>{row['operations']}</td>"
        f"<td>{row['positives']}</td>"
        f"<td>{row['groups']}</td>"
        f"<td>{row['top_positive_lift']}</td>"
        f"<td>{row['inspection_fraction_for_50pct_positives']}</td>"
        f"<td>{row['avg_top_group_sessions']}</td>"
        "</tr>"
        for row in report["task_results"]
    )
    cards = "".join(
        f"<div class='card'><h3>{html.escape(view)}</h3><p>median lift <b>{row['median_top_positive_lift']}</b></p><p>median inspect frac <b>{row['median_inspection_fraction_for_50pct_positives']}</b></p></div>"
        for view, row in report["summary"]["views"].items()
    )
    return f"""<!doctype html>
<meta charset="utf-8">
<title>R300 Operation-Query Utility</title>
<style>
body {{ font-family: system-ui, sans-serif; margin: 32px; color: #1f2933; }}
.grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(190px, 1fr)); gap: 12px; }}
.card {{ border: 1px solid #d9e2ec; border-radius: 6px; padding: 12px; background: #f8fafc; }}
table {{ border-collapse: collapse; width: 100%; margin-top: 20px; font-size: 13px; }}
th, td {{ border-bottom: 1px solid #d9e2ec; padding: 7px 8px; text-align: left; }}
th {{ background: #eef2f7; }}
</style>
<h1>R300 Operation-Query Utility</h1>
<p>Automated oracle-backed proxy over existing tracked operation JSONL. It is not a human user study.</p>
<div class="grid">{cards}</div>
<table>
<thead><tr><th>Task</th><th>View</th><th>Ops</th><th>Positives</th><th>Groups</th><th>Top lift</th><th>Inspect frac @50%</th><th>Top sessions</th></tr></thead>
<tbody>{rows}</tbody>
</table>
"""


def main() -> None:
    args = parse_args()
    out_dir = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    all_operations = []
    task_results = []
    task_summaries = []
    for task in TASKS:
        operations = load_task_operations(task)
        if not operations:
            raise SystemExit(f"task {task['id']} produced no operations")
        all_operations.extend(operations)
        positives = sum(
            operation["value"]
            for operation in operations
            if operation["fields"]["target_positive"] == "positive"
        )
        task_summaries.append(
            {
                "task": task["id"],
                "dataset": task["dataset"],
                "oracle_field": task["oracle_field"],
                "operations": sum(operation["value"] for operation in operations),
                "positives": positives,
                "prevalence": round(positives / len(operations), 4),
                "problem": task["problem"],
                "source_operation_file": rel(task["operation_file"]),
            }
        )
        for view in VIEW_SPECS:
            metrics = evaluate_view(operations, stack_for_view(task, view), args.top_groups)
            task_results.append(
                {
                    "task": task["id"],
                    "dataset": task["dataset"],
                    "view": view,
                    **metrics,
                }
            )

    operation_path = out_dir / "query-utility-operations.jsonl"
    write_operations(operation_path, all_operations)
    profile_specs = write_profile_specs(out_dir, operation_path)
    report = {
        "run_id": "R300",
        "purpose": "automated proxy for real-problem analysis utility over existing labeled operations",
        "claim_scope": {
            "supported": "operation-stack views improve oracle-backed problem localization and cross-session aggregation over flat/fixed-session summaries on existing labeled traces",
            "not_supported": "human productivity improvement, unsupervised intent discovery, or online detection without labels/proxies",
        },
        "tasks": task_summaries,
        "views": list(VIEW_SPECS),
        "top_groups": args.top_groups,
        "summary": summarize(task_results),
        "task_results": task_results,
        "operation_jsonl": rel(operation_path),
        "profile_specs": profile_specs,
    }

    json_path = out_dir / "query-utility-report.json"
    markdown_path = out_dir / "query-utility-report.md"
    html_path = out_dir / "index.html"
    json_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    markdown_path.write_text(render_markdown(report), encoding="utf-8")
    html_path.write_text(render_html(report), encoding="utf-8")
    run_result = {
        "status": "ok",
        "run_id": "R300",
        "tasks": len(TASKS),
        "operations": sum(operation["value"] for operation in all_operations),
        "json": rel(json_path),
        "markdown": rel(markdown_path),
        "html": rel(html_path),
        "operation_jsonl": rel(operation_path),
        "profile_specs": profile_specs,
    }
    (out_dir / "run-result.json").write_text(json.dumps(run_result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(run_result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
