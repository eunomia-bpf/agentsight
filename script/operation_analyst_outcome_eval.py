#!/usr/bin/env python3
"""R308: score label-hidden analyst outcomes from existing case packets.

R308 does not fetch datasets and does not introduce a profiler abstraction. It
reuses the R305 visible cross-view case packets and their hidden answer key to
ask whether an analyst would see useful evidence early in a packet. The visible
surface remains a report over operations and operation stacks; oracle fields are
used only after packet construction for scoring.
"""

from __future__ import annotations

import argparse
import html
import json
import math
import subprocess
import sys
from pathlib import Path
from statistics import median
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OUT_ROOT = ROOT / "docs" / "visexp" / "out"
DEFAULT_OUT_DIR = OUT_ROOT / "operation-analyst-outcome-r308"
SOURCE_DIR = OUT_ROOT / "operation-case-baseline-r305"
VIEWS = ["flat", "fixed_session", "operation_stack"]
HIGH_LIFT_THRESHOLD = 1.5

sys.path.insert(0, str(Path(__file__).resolve().parent))
import operation_case_study_eval as r304  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--high-lift-threshold", type=float, default=HIGH_LIFT_THRESHOLD)
    return parser.parse_args()


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def load_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as file:
        return json.load(file)


def git_check(description: str, args: list[str], path: Path) -> None:
    result = subprocess.run(
        ["git", *args, "--", rel(path)],
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
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
        return round(value, 4)
    if isinstance(value, dict):
        return {key: round_value(child) for key, child in value.items()}
    if isinstance(value, list):
        return [round_value(child) for child in value]
    return value


def safe_ratio(left: float | None, right: float | None) -> float | str | None:
    if left is None or right is None:
        return None
    if right == 0:
        return "inf" if left > 0 else 0.0
    return left / right


def median_or_none(values: list[float | int]) -> float | None:
    return float(median(values)) if values else None


def case_key(case: dict[str, Any]) -> tuple[str, str]:
    return (case["task"], case["view"])


def derive_task_totals(answer_cases: list[dict[str, Any]]) -> dict[str, dict[str, float]]:
    totals: dict[str, dict[str, float]] = {}
    for case in answer_cases:
        score = case["score"]
        work = float(score["inspected_operation_fraction"])
        recall = float(score["positive_recall"])
        if work <= 0 or recall <= 0:
            continue
        total_operations = float(score["inspected_operations"]) / work
        total_positives = float(score["positive_operations"]) / recall
        current = totals.get(case["task"])
        if current is None or case["view"] == "flat":
            totals[case["task"]] = {
                "operations": total_operations,
                "positives": total_positives,
                "prevalence": total_positives / total_operations if total_operations else 0.0,
            }
    missing = sorted({case["task"] for case in answer_cases} - set(totals))
    if missing:
        raise SystemExit(f"could not derive task totals for {missing}")
    return totals


def validate_case_alignment(
    visible_packet: dict[str, Any],
    answer_key: dict[str, Any],
) -> None:
    if visible_packet.get("run_id") != "R305" or answer_key.get("run_id") != "R305":
        raise SystemExit("R308 expects R305 visible packets and answer key")
    r304.assert_visible_packet_has_no_hidden_fields(visible_packet)
    visible_by_key = {case_key(case): case for case in visible_packet["cases"]}
    answer_by_key = {case_key(case): case for case in answer_key["cases"]}
    if set(visible_by_key) != set(answer_by_key):
        raise SystemExit("visible packets and answer key have different task/view cases")
    for key, visible in visible_by_key.items():
        answer = answer_by_key[key]
        visible_ids = [group["group_id"] for group in visible["groups"]]
        answer_ids = [group["group_id"] for group in answer["groups"]]
        if visible_ids != answer_ids:
            raise SystemExit(f"group order mismatch for {key}")


def cumulative_hit(
    groups: list[dict[str, Any]],
    prevalence: float,
    total_operations: float,
    predicate: Any,
) -> dict[str, Any] | None:
    cumulative_operations = 0.0
    cumulative_positives = 0.0
    for group in groups:
        operations = float(group["operations"])
        positives = float(group["positive_operations"])
        rate = float(group["positive_rate"])
        lift = rate / prevalence if prevalence else 0.0
        cumulative_operations += operations
        cumulative_positives += positives
        if predicate(positives, lift):
            return {
                "rank": group["rank"],
                "operation_fraction": cumulative_operations / total_operations
                if total_operations
                else 0.0,
                "positive_operations_seen": cumulative_positives,
                "group_positive_rate": rate,
                "group_lift": lift,
            }
    return None


def score_case(
    answer_case: dict[str, Any],
    task_totals: dict[str, dict[str, float]],
    high_lift_threshold: float,
) -> dict[str, Any]:
    task_total = task_totals[answer_case["task"]]
    prevalence = task_total["prevalence"]
    total_operations = task_total["operations"]
    groups = answer_case["groups"]
    lifts = [
        float(group["positive_rate"]) / prevalence if prevalence else 0.0 for group in groups
    ]
    first_positive = cumulative_hit(
        groups,
        prevalence,
        total_operations,
        lambda positives, _lift: positives > 0,
    )
    first_enriched = cumulative_hit(
        groups,
        prevalence,
        total_operations,
        lambda positives, lift: positives > 0 and lift >= 1.0,
    )
    first_high_lift = cumulative_hit(
        groups,
        prevalence,
        total_operations,
        lambda positives, lift: positives > 0 and lift >= high_lift_threshold,
    )
    top_group = groups[0] if groups else {"positive_rate": 0.0, "positive_operations": 0}
    score = answer_case["score"]
    return round_value(
        {
            "task": answer_case["task"],
            "dataset": answer_case["dataset"],
            "view": answer_case["view"],
            "oracle_field": answer_case["oracle_field"],
            "selected_groups": len(groups),
            "task_operations": task_total["operations"],
            "task_positive_operations": task_total["positives"],
            "task_prevalence": prevalence,
            "selected_operation_fraction": score["inspected_operation_fraction"],
            "selected_positive_recall": score["positive_recall"],
            "selected_positive_precision": score["positive_precision"],
            "selected_positive_lift": score["positive_lift"],
            "top_group_positive_rate": float(top_group["positive_rate"]),
            "top_group_positive_operations": int(top_group["positive_operations"]),
            "top_group_lift": lifts[0] if lifts else 0.0,
            "max_group_lift": max(lifts) if lifts else 0.0,
            "groups_with_positive": sum(
                1 for group in groups if int(group["positive_operations"]) > 0
            ),
            "groups_with_lift_ge_1": sum(
                1
                for group, lift in zip(groups, lifts)
                if int(group["positive_operations"]) > 0 and lift >= 1.0
            ),
            "groups_with_lift_ge_threshold": sum(
                1
                for group, lift in zip(groups, lifts)
                if int(group["positive_operations"]) > 0 and lift >= high_lift_threshold
            ),
            "first_positive": first_positive,
            "first_enriched": first_enriched,
            "first_high_lift": first_high_lift,
        }
    )


def summarize_by_view(rows: list[dict[str, Any]]) -> dict[str, Any]:
    summary = {}
    for view in VIEWS:
        items = [row for row in rows if row["view"] == view]
        if not items:
            continue
        first_positive_items = [row["first_positive"] for row in items if row["first_positive"]]
        first_enriched_items = [row["first_enriched"] for row in items if row["first_enriched"]]
        high_lift_items = [row["first_high_lift"] for row in items if row["first_high_lift"]]
        summary[view] = round_value(
            {
                "tasks": len(items),
                "tasks_with_first_positive": len(first_positive_items),
                "tasks_with_first_enriched": len(first_enriched_items),
                "tasks_with_high_lift_group": len(high_lift_items),
                "median_first_positive_rank": median_or_none(
                    [hit["rank"] for hit in first_positive_items]
                ),
                "median_first_positive_operation_fraction": median_or_none(
                    [hit["operation_fraction"] for hit in first_positive_items]
                ),
                "median_first_enriched_rank": median_or_none(
                    [hit["rank"] for hit in first_enriched_items]
                ),
                "median_first_enriched_operation_fraction": median_or_none(
                    [hit["operation_fraction"] for hit in first_enriched_items]
                ),
                "median_first_high_lift_rank": median_or_none(
                    [hit["rank"] for hit in high_lift_items]
                ),
                "median_first_high_lift_operation_fraction": median_or_none(
                    [hit["operation_fraction"] for hit in high_lift_items]
                ),
                "median_top_group_lift": median_or_none(
                    [row["top_group_lift"] for row in items]
                ),
                "median_top_group_positive_rate": median_or_none(
                    [row["top_group_positive_rate"] for row in items]
                ),
                "median_selected_operation_fraction": median_or_none(
                    [row["selected_operation_fraction"] for row in items]
                ),
                "median_selected_positive_recall": median_or_none(
                    [row["selected_positive_recall"] for row in items]
                ),
                "median_selected_positive_precision": median_or_none(
                    [row["selected_positive_precision"] for row in items]
                ),
                "median_selected_positive_lift": median_or_none(
                    [row["selected_positive_lift"] for row in items]
                ),
            }
        )
    return summary


def compare_views(rows: list[dict[str, Any]], left: str, right: str) -> dict[str, Any]:
    by_key = {(row["task"], row["view"]): row for row in rows}
    tasks = sorted({row["task"] for row in rows})
    comparisons = []
    for task in tasks:
        lhs = by_key[(task, left)]
        rhs = by_key[(task, right)]
        comparisons.append(
            {
                "task": task,
                "left": left,
                "right": right,
                "selected_recall_ratio": safe_ratio(
                    lhs["selected_positive_recall"],
                    rhs["selected_positive_recall"],
                ),
                "selected_work_ratio": safe_ratio(
                    lhs["selected_operation_fraction"],
                    rhs["selected_operation_fraction"],
                ),
                "top_group_lift_ratio": safe_ratio(
                    lhs["top_group_lift"],
                    rhs["top_group_lift"],
                ),
                "first_positive_work_ratio": safe_ratio(
                    lhs["first_positive"]["operation_fraction"]
                    if lhs["first_positive"]
                    else None,
                    rhs["first_positive"]["operation_fraction"]
                    if rhs["first_positive"]
                    else None,
                ),
                "left_has_high_lift": lhs["first_high_lift"] is not None,
                "right_has_high_lift": rhs["first_high_lift"] is not None,
            }
        )
    numeric_keys = [
        "selected_recall_ratio",
        "selected_work_ratio",
        "top_group_lift_ratio",
        "first_positive_work_ratio",
    ]
    summary = {}
    for key in numeric_keys:
        numeric_values = [
            value for value in (row[key] for row in comparisons) if isinstance(value, float)
        ]
        summary[f"median_{key}"] = median_or_none(numeric_values)
    summary["left_high_lift_tasks"] = sum(row["left_has_high_lift"] for row in comparisons)
    summary["right_high_lift_tasks"] = sum(row["right_has_high_lift"] for row in comparisons)
    summary["tasks"] = len(comparisons)
    return round_value({"summary": summary, "tasks": comparisons})


def build_headline(summary: dict[str, Any]) -> str:
    by_view = summary["by_view"]
    stack = by_view["operation_stack"]
    fixed = by_view["fixed_session"]
    flat = by_view["flat"]
    return (
        "R308 scores analyst-outcome proxies on the R305 label-hidden packets. "
        f"Operation-stack packets contain a positive group in {stack['tasks_with_first_positive']}/"
        f"{stack['tasks']} tasks and a >=1.5x high-lift group in "
        f"{stack['tasks_with_high_lift_group']}/{stack['tasks']} tasks. Fixed-session "
        f"packets reach {fixed['tasks_with_first_positive']}/{fixed['tasks']} and "
        f"{fixed['tasks_with_high_lift_group']}/{fixed['tasks']}; flat packets reach "
        f"{flat['tasks_with_first_positive']}/{flat['tasks']} and "
        f"{flat['tasks_with_high_lift_group']}/{flat['tasks']}. Operation stacks keep "
        f"median selected work at {stack['median_selected_operation_fraction'] * 100:.1f}% "
        f"with recall {stack['median_selected_positive_recall'] * 100:.1f}% and top-group "
        f"lift {stack['median_top_group_lift']:.3f}."
    )


def build_report(high_lift_threshold: float) -> dict[str, Any]:
    source_paths = {
        "r305_report": SOURCE_DIR / "case-baseline-report.json",
        "r305_visible_packet": SOURCE_DIR / "visible-case-packets.json",
        "r305_answer_key": SOURCE_DIR / "answer-key.json",
    }
    ensure_sources_tracked_clean(list(source_paths.values()))
    visible_packet = load_json(source_paths["r305_visible_packet"])
    answer_key = load_json(source_paths["r305_answer_key"])
    r305_report = load_json(source_paths["r305_report"])
    validate_case_alignment(visible_packet, answer_key)

    task_totals = derive_task_totals(answer_key["cases"])
    task_view_outcomes = [
        score_case(case, task_totals, high_lift_threshold) for case in answer_key["cases"]
    ]
    summary = {
        "by_view": summarize_by_view(task_view_outcomes),
        "operation_stack_vs_flat": compare_views(task_view_outcomes, "operation_stack", "flat"),
        "operation_stack_vs_fixed_session": compare_views(
            task_view_outcomes, "operation_stack", "fixed_session"
        ),
    }
    report = {
        "schema": "agentsight.operation-analyst-outcome.v1",
        "run_id": "R308",
        "purpose": "score label-hidden analyst outcome proxies over existing cross-view case packets",
        "input_policy": "no dataset sync; reads tracked R305 visible packets and answer key only",
        "source_artifacts": {key: rel(path) for key, path in source_paths.items()},
        "views": VIEWS,
        "tasks": r305_report["tasks"],
        "ranker": r305_report["ranker"],
        "groups_per_task": r305_report["groups_per_task"],
        "high_lift_threshold": high_lift_threshold,
        "protocol": {
            "visible_surface": "R305 visible-case-packets.json",
            "hidden_scoring": "R305 answer-key.json",
            "outcomes": [
                "first positive group",
                "first group enriched over task prevalence",
                f"first group with lift >= {high_lift_threshold}",
                "selected packet recall, precision, work, and top-group lift",
            ],
            "not_a_human_study": True,
            "profiler_abstractions": ["operation", "operation stack"],
        },
        "task_view_outcomes": task_view_outcomes,
        "summary": summary,
        "claim_scope": {
            "supported": (
                "operation-stack packets expose early positive and high-lift evidence "
                "on existing labeled analyst tasks while staying much more selective "
                "than flat packets"
            ),
            "narrowed": (
                "fixed-session packets remain cheaper on some first-positive work "
                "metrics, so operation stacks are a configurable inspectability "
                "tradeoff rather than a universal winner"
            ),
            "not_supported": (
                "human analyst accuracy/time improvement, automatic anomaly detection, "
                "or dominance over every baseline on every metric"
            ),
        },
    }
    report["headline"] = build_headline(summary)
    return report


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# R308 Analyst Outcome Proxy",
        "",
        report["headline"],
        "",
        "## View Summary",
        "",
        "| View | Positive tasks | High-lift tasks | First-positive work | Top-group lift | Work | Recall | Precision |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for view in VIEWS:
        row = report["summary"]["by_view"][view]
        lines.append(
            f"| {view} | {row['tasks_with_first_positive']}/{row['tasks']} | {row['tasks_with_high_lift_group']}/{row['tasks']} | {row['median_first_positive_operation_fraction']} | {row['median_top_group_lift']} | {row['median_selected_operation_fraction']} | {row['median_selected_positive_recall']} | {row['median_selected_positive_precision']} |"
        )

    lines.extend(
        [
            "",
            "## Task-View Outcomes",
            "",
            "| Task | View | Top lift | First positive work | High-lift rank | Work | Recall | Precision |",
            "|---|---|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for row in report["task_view_outcomes"]:
        first_positive = row["first_positive"] or {}
        first_high = row["first_high_lift"] or {}
        lines.append(
            f"| {row['task']} | {row['view']} | {row['top_group_lift']} | {first_positive.get('operation_fraction', 'n/a')} | {first_high.get('rank', 'n/a')} | {row['selected_operation_fraction']} | {row['selected_positive_recall']} | {row['selected_positive_precision']} |"
        )

    lines.extend(
        [
            "",
            "## Claim Scope",
            "",
            f"- Supports: {report['claim_scope']['supported']}.",
            f"- Narrows: {report['claim_scope']['narrowed']}.",
            f"- Does not support: {report['claim_scope']['not_supported']}.",
            "",
            "## Source Artifacts",
            "",
        ]
    )
    lines.extend(f"- `{key}`: `{path}`" for key, path in report["source_artifacts"].items())
    return "\n".join(lines) + "\n"


def render_html(report: dict[str, Any]) -> str:
    rows = []
    for view in VIEWS:
        row = report["summary"]["by_view"][view]
        rows.append(
            "<tr>"
            f"<th>{html.escape(view)}</th>"
            f"<td>{row['tasks_with_first_positive']}/{row['tasks']}</td>"
            f"<td>{row['tasks_with_high_lift_group']}/{row['tasks']}</td>"
            f"<td>{row['median_first_positive_operation_fraction']}</td>"
            f"<td>{row['median_top_group_lift']}</td>"
            f"<td>{row['median_selected_positive_recall']}</td>"
            "</tr>"
        )
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>R308 Analyst Outcome Proxy</title>
  <style>
    body {{ font-family: system-ui, sans-serif; margin: 2rem; color: #1f2933; }}
    p {{ max-width: 980px; line-height: 1.5; }}
    table {{ border-collapse: collapse; margin-top: 1.25rem; font-size: 13px; }}
    th, td {{ border: 1px solid #d8dee9; padding: 0.5rem 0.7rem; text-align: left; }}
    th {{ background: #f6f8fa; }}
  </style>
</head>
<body>
  <h1>R308 Analyst Outcome Proxy</h1>
  <p>{html.escape(report['headline'])}</p>
  <table>
    <tr><th>View</th><th>Positive tasks</th><th>High-lift tasks</th><th>First-positive work</th><th>Top-group lift</th><th>Recall</th></tr>
    {''.join(rows)}
  </table>
</body>
</html>
"""


def main() -> None:
    args = parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)
    report = build_report(args.high_lift_threshold)

    json_path = args.out_dir / "analyst-outcome-report.json"
    markdown_path = args.out_dir / "analyst-outcome-report.md"
    html_path = args.out_dir / "index.html"
    run_result_path = args.out_dir / "run-result.json"
    report["outputs"] = {
        "json": rel(json_path),
        "markdown": rel(markdown_path),
        "html": rel(html_path),
        "run_result": rel(run_result_path),
    }
    write_json(json_path, report)
    markdown_path.write_text(render_markdown(report), encoding="utf-8")
    html_path.write_text(render_html(report), encoding="utf-8")
    write_json(
        run_result_path,
        {
            "status": "ok",
            "run_id": report["run_id"],
            "tasks": report["tasks"],
            "views": report["views"],
            "json": rel(json_path),
            "markdown": rel(markdown_path),
            "html": rel(html_path),
        },
    )
    print(json.dumps(load_json(run_result_path), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
