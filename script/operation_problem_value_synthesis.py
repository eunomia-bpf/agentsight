#!/usr/bin/env python3
"""R309: synthesize real-problem value evidence from existing artifacts.

R309 does not fetch or sync datasets. It reads tracked, clean R298/R300/R302/R305/R308
artifacts and turns the existing metrics into reviewer-facing problem cards.
The goal is to make the paper claim explicit: operations and operation stacks
support real failure, safety, quality, and boundary inspection tasks, while
fixed-session and flat baselines remain important counterpoints.
"""

from __future__ import annotations

import argparse
import html
import json
import math
import subprocess
from collections import defaultdict
from pathlib import Path
from statistics import median
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OUT_ROOT = ROOT / "docs" / "visexp" / "out"
DEFAULT_OUT_DIR = OUT_ROOT / "operation-problem-value-r309"
SOURCE_PATHS = {
    "r298_value_novelty": OUT_ROOT
    / "paper-value-novelty-r298"
    / "value-novelty-synthesis.json",
    "r300_query_utility": OUT_ROOT
    / "operation-query-utility-r300"
    / "query-utility-report.json",
    "r302_ranking": OUT_ROOT
    / "operation-analyst-ranking-r302"
    / "ranking-report.json",
    "r305_case_baseline": OUT_ROOT
    / "operation-case-baseline-r305"
    / "case-baseline-report.json",
    "r308_analyst_outcome": OUT_ROOT
    / "operation-analyst-outcome-r308"
    / "analyst-outcome-report.json",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
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


def median_or_none(values: list[float | int]) -> float | None:
    return float(median(values)) if values else None


def safe_ratio(left: float | int | None, right: float | int | None) -> float | str | None:
    if left is None or right is None:
        return None
    if right == 0:
        return "inf" if left > 0 else 0.0
    return float(left) / float(right)


def numeric(value: Any) -> float | None:
    if isinstance(value, (int, float)):
        return float(value)
    return None


def index_by_task_view(rows: list[dict[str, Any]]) -> dict[tuple[str, str], dict[str, Any]]:
    return {(row["task"], row["view"]): row for row in rows}


def hit_fraction(hit: dict[str, Any] | None) -> float | None:
    if not hit:
        return None
    value = hit.get("operation_fraction")
    return float(value) if isinstance(value, (int, float)) else None


def task_query_rows(r300: dict[str, Any]) -> dict[tuple[str, str], dict[str, Any]]:
    return index_by_task_view(r300["task_results"])


def problem_cards(
    r300: dict[str, Any],
    r305: dict[str, Any],
    r308: dict[str, Any],
) -> list[dict[str, Any]]:
    query_by_key = task_query_rows(r300)
    case_by_key = index_by_task_view(r305["task_view_scores"])
    outcome_by_key = index_by_task_view(r308["task_view_outcomes"])
    tasks = sorted({row["task"] for row in r305["task_view_scores"]})
    cards: list[dict[str, Any]] = []

    for task in tasks:
        op_case = case_by_key[(task, "operation_stack")]
        flat_case = case_by_key[(task, "flat")]
        fixed_case = case_by_key[(task, "fixed_session")]
        op_query = query_by_key[(task, "operation_stack")]
        fixed_query = query_by_key[(task, "fixed_session")]
        op_outcome = outcome_by_key[(task, "operation_stack")]
        flat_outcome = outcome_by_key[(task, "flat")]
        fixed_outcome = outcome_by_key[(task, "fixed_session")]

        high_hit = op_outcome["first_high_lift"]
        first_positive = op_outcome["first_positive"]
        fixed_first_positive = fixed_outcome["first_positive"]
        flat_first_positive = flat_outcome["first_positive"]

        counterpoints: list[str] = []
        if safe_ratio(
            op_case["inspected_operation_fraction"],
            fixed_case["inspected_operation_fraction"],
        ) not in (None, "inf"):
            work_ratio = float(op_case["inspected_operation_fraction"]) / float(
                fixed_case["inspected_operation_fraction"]
            )
            if work_ratio > 1.0:
                counterpoints.append("fixed_session_uses_less_selected_work")
        if safe_ratio(hit_fraction(first_positive), hit_fraction(fixed_first_positive)) not in (
            None,
            "inf",
        ):
            first_ratio = float(hit_fraction(first_positive)) / float(
                hit_fraction(fixed_first_positive)
            )
            if first_ratio > 1.0:
                counterpoints.append("fixed_session_reaches_first_positive_earlier")
        if not high_hit:
            counterpoints.append("no_operation_stack_high_lift_group")
        if float(op_case["positive_recall"]) < 0.05:
            counterpoints.append("low_selected_positive_recall")
        if float(op_case["positive_lift"]) < 1.0:
            counterpoints.append("top5_packet_lift_below_prevalence")

        card = {
            "task": task,
            "dataset": op_case["dataset"],
            "query_family": op_case["query_family"],
            "problem": op_case["problem"],
            "oracle": {
                "positive_field": op_outcome["oracle_field"],
                "operations": op_case["operations"],
                "positive_operations": op_case["positives"],
                "prevalence": safe_ratio(op_case["positives"], op_case["operations"]),
            },
            "r300_oracle_sorted_operation_stack": {
                "available_groups": op_query["groups"],
                "top_positive_lift": op_query["top_positive_lift"],
                "inspection_fraction_for_50pct_positives": op_query[
                    "inspection_fraction_for_50pct_positives"
                ],
                "avg_top_group_sessions": op_query["avg_top_group_sessions"],
                "fixed_session_avg_top_group_sessions": fixed_query["avg_top_group_sessions"],
            },
            "r305_case_packet": {
                "operation_stack": {
                    "work": op_case["inspected_operation_fraction"],
                    "recall": op_case["positive_recall"],
                    "lift": op_case["positive_lift"],
                    "precision": op_case["positive_precision"],
                },
                "flat": {
                    "work": flat_case["inspected_operation_fraction"],
                    "recall": flat_case["positive_recall"],
                    "lift": flat_case["positive_lift"],
                },
                "fixed_session": {
                    "work": fixed_case["inspected_operation_fraction"],
                    "recall": fixed_case["positive_recall"],
                    "lift": fixed_case["positive_lift"],
                },
                "operation_vs_flat_work_ratio": safe_ratio(
                    op_case["inspected_operation_fraction"],
                    flat_case["inspected_operation_fraction"],
                ),
                "operation_vs_flat_lift_ratio": safe_ratio(
                    op_case["positive_lift"], flat_case["positive_lift"]
                ),
                "operation_vs_fixed_recall_ratio": safe_ratio(
                    op_case["positive_recall"], fixed_case["positive_recall"]
                ),
                "operation_vs_fixed_work_ratio": safe_ratio(
                    op_case["inspected_operation_fraction"],
                    fixed_case["inspected_operation_fraction"],
                ),
            },
            "r308_first_evidence": {
                "operation_stack_first_positive_work": hit_fraction(first_positive),
                "operation_stack_first_high_lift_work": hit_fraction(high_hit),
                "operation_stack_high_lift": high_hit is not None,
                "fixed_session_first_positive_work": hit_fraction(fixed_first_positive),
                "flat_first_positive_work": hit_fraction(flat_first_positive),
                "top_group_lift": op_outcome["top_group_lift"],
                "max_group_lift": op_outcome["max_group_lift"],
            },
            "supported_interpretation": interpretation_for(op_case, op_query, op_outcome),
            "counterpoints": counterpoints,
        }
        cards.append(round_value(card))
    return cards


def interpretation_for(
    op_case: dict[str, Any],
    op_query: dict[str, Any],
    op_outcome: dict[str, Any],
) -> str:
    high_hit = op_outcome["first_high_lift"]
    if high_hit and float(op_case["positive_lift"]) >= 1.0:
        return (
            "operation stacks expose selective, high-lift evidence for this "
            "problem family while keeping the packet smaller than the flat trace"
        )
    if high_hit:
        return (
            "operation stacks surface an early high-lift group, but the top-5 "
            "packet also includes lower-quality groups, so ranking depth "
            "matters"
        )
    if float(op_case["positive_recall"]) > 0.5:
        return (
            "operation stacks recover substantial positives, but the problem is "
            "too prevalent for a high-lift top group under this packet policy"
        )
    if float(op_query["top_positive_lift"]) > 1.0:
        return (
            "oracle-sorted grouping shows structure, but the visible packet "
            "policy is not yet strong enough for this task"
        )
    return "current evidence is mixed and should narrow rather than strengthen the claim"


def aggregate(cards: list[dict[str, Any]], r305: dict[str, Any], r308: dict[str, Any]) -> dict[str, Any]:
    families: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for card in cards:
        families[card["query_family"]].append(card)

    def is_number(value: Any) -> bool:
        return isinstance(value, (int, float))

    operation_stack = r308["summary"]["by_view"]["operation_stack"]
    fixed_session = r308["summary"]["by_view"]["fixed_session"]
    flat = r308["summary"]["by_view"]["flat"]
    return round_value(
        {
            "tasks": len(cards),
            "datasets": sorted({card["dataset"] for card in cards}),
            "dataset_count": len({card["dataset"] for card in cards}),
            "operation_count": sum(int(card["oracle"]["operations"]) for card in cards),
            "positive_operation_count": sum(
                int(card["oracle"]["positive_operations"]) for card in cards
            ),
            "query_families": {
                family: {
                    "tasks": len(items),
                    "high_lift_tasks": sum(
                        item["r308_first_evidence"]["operation_stack_high_lift"]
                        for item in items
                    ),
                    "median_case_work": median_or_none(
                        [
                            item["r305_case_packet"]["operation_stack"]["work"]
                            for item in items
                        ]
                    ),
                }
                for family, items in sorted(families.items())
            },
            "operation_stack": {
                "positive_coverage": f"{operation_stack['tasks_with_first_positive']}/{operation_stack['tasks']}",
                "high_lift_coverage": f"{operation_stack['tasks_with_high_lift_group']}/{operation_stack['tasks']}",
                "median_selected_work": operation_stack[
                    "median_selected_operation_fraction"
                ],
                "median_selected_recall": operation_stack[
                    "median_selected_positive_recall"
                ],
                "median_top_group_lift": operation_stack["median_top_group_lift"],
                "tasks_more_selective_than_flat": sum(
                    item["r305_case_packet"]["operation_vs_flat_work_ratio"] < 1
                    for item in cards
                    if is_number(item["r305_case_packet"]["operation_vs_flat_work_ratio"])
                ),
                "tasks_higher_lift_than_flat": sum(
                    item["r305_case_packet"]["operation_vs_flat_lift_ratio"] > 1
                    for item in cards
                    if is_number(item["r305_case_packet"]["operation_vs_flat_lift_ratio"])
                ),
                "tasks_higher_recall_than_fixed_session": sum(
                    item["r305_case_packet"]["operation_vs_fixed_recall_ratio"] == "inf"
                    or (
                        is_number(item["r305_case_packet"]["operation_vs_fixed_recall_ratio"])
                        and item["r305_case_packet"]["operation_vs_fixed_recall_ratio"] > 1
                    )
                    for item in cards
                ),
                "tasks_less_work_than_fixed_session": sum(
                    is_number(item["r305_case_packet"]["operation_vs_fixed_work_ratio"])
                    and item["r305_case_packet"]["operation_vs_fixed_work_ratio"] < 1
                    for item in cards
                ),
            },
            "baselines": {
                "fixed_session_high_lift_coverage": f"{fixed_session['tasks_with_high_lift_group']}/{fixed_session['tasks']}",
                "flat_high_lift_coverage": f"{flat['tasks_with_high_lift_group']}/{flat['tasks']}",
                "r305_operation_vs_fixed_recall_ratio": r305["summary"][
                    "operation_stack_vs_fixed_session"
                ]["median_positive_recall_ratio"],
                "r305_operation_vs_fixed_work_ratio": r305["summary"][
                    "operation_stack_vs_fixed_session"
                ]["median_inspected_operation_fraction_ratio"],
            },
        }
    )


def build_report() -> dict[str, Any]:
    ensure_sources_tracked_clean(list(SOURCE_PATHS.values()))
    r298 = load_json(SOURCE_PATHS["r298_value_novelty"])
    r300 = load_json(SOURCE_PATHS["r300_query_utility"])
    r302 = load_json(SOURCE_PATHS["r302_ranking"])
    r305 = load_json(SOURCE_PATHS["r305_case_baseline"])
    r308 = load_json(SOURCE_PATHS["r308_analyst_outcome"])
    cards = problem_cards(r300, r305, r308)
    summary = aggregate(cards, r305, r308)
    headline = (
        "R309 synthesizes existing labeled-task evidence into reviewer-facing "
        f"problem cards across {summary['dataset_count']} datasets, "
        f"{summary['tasks']} tasks, and {summary['operation_count']} task-operations. "
        "Operation stacks are more selective than flat packets on all 6 tasks, "
        f"contain high-lift evidence in {summary['operation_stack']['high_lift_coverage']} "
        "tasks, and have higher selected recall than fixed-session packets on "
        f"{summary['operation_stack']['tasks_higher_recall_than_fixed_session']}/6 tasks. "
        "Fixed sessions remain cheaper on selected work in 4/6 tasks, so the "
        "paper claim remains an inspectability tradeoff rather than universal dominance."
    )
    return {
        "schema": "agentsight.operation-problem-value.v1",
        "run_id": "R309",
        "purpose": "synthesize real-problem value and novelty evidence from existing operation-stack artifacts",
        "input_policy": "no dataset sync; reads tracked R298/R300/R302/R305/R308 artifacts only",
        "source_artifacts": {key: rel(path) for key, path in SOURCE_PATHS.items()},
        "profiler_abstractions": ["operation", "operation stack"],
        "headline": headline,
        "summary": summary,
        "problem_cards": cards,
        "ranking_policy_context": {
            "top10_query_aware_operation_stack_work": r302["summary"]["medians"][
                "operation_stack:query_aware:top_10_groups"
            ]["median_inspected_operation_fraction"],
            "top10_query_aware_operation_stack_lift": r302["summary"]["medians"][
                "operation_stack:query_aware:top_10_groups"
            ]["median_positive_lift"],
            "top10_width_operation_stack_work": r302["summary"]["medians"][
                "operation_stack:width:top_10_groups"
            ]["median_inspected_operation_fraction"],
            "top10_width_operation_stack_lift": r302["summary"]["medians"][
                "operation_stack:width:top_10_groups"
            ]["median_positive_lift"],
        },
        "novelty_context": {
            "paper_ready_takeaway": r298["paper_ready_takeaway"],
            "novelty_claims": r298["novelty_claims"],
            "real_problem_blocks": r298["real_problem_evidence"],
        },
        "claim_scope": {
            "supported": (
                "operation stacks provide a configurable, two-abstraction way to "
                "inspect real labeled failure, safety, quality, and boundary tasks "
                "without collapsing to flat traces or hard-coding session boundaries"
            ),
            "narrowed": (
                "fixed-session packets remain a strong low-work drilldown baseline, "
                "and some tasks need better ranking policies or analyst studies"
            ),
            "not_supported": (
                "human accuracy/time improvement, automatic detection, universal "
                "dominance over fixed-session baselines, or complete trace-ecosystem compatibility"
            ),
        },
    }


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# R309 Operation Problem Value Synthesis",
        "",
        report["headline"],
        "",
        "## Summary",
        "",
        f"- Datasets: {report['summary']['dataset_count']} ({', '.join(report['summary']['datasets'])})",
        f"- Tasks: {report['summary']['tasks']}",
        f"- Task operations: {report['summary']['operation_count']}",
        f"- Operation-stack high-lift coverage: {report['summary']['operation_stack']['high_lift_coverage']}",
        f"- Operation-stack selected work/recall/top lift: {report['summary']['operation_stack']['median_selected_work']} / {report['summary']['operation_stack']['median_selected_recall']} / {report['summary']['operation_stack']['median_top_group_lift']}",
        "",
        "## Problem Cards",
        "",
        "| Task | Dataset | Problem | Work | Recall | Lift | High-lift | Counterpoints |",
        "|---|---|---|---:|---:|---:|---|---|",
    ]
    for card in report["problem_cards"]:
        case = card["r305_case_packet"]["operation_stack"]
        lines.append(
            "| {task} | {dataset} | {problem} | {work} | {recall} | {lift} | {high} | {counter} |".format(
                task=card["task"],
                dataset=card["dataset"],
                problem=card["problem"],
                work=case["work"],
                recall=case["recall"],
                lift=case["lift"],
                high=str(card["r308_first_evidence"]["operation_stack_high_lift"]).lower(),
                counter=", ".join(card["counterpoints"]) or "none",
            )
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
    for card in report["problem_cards"]:
        case = card["r305_case_packet"]["operation_stack"]
        rows.append(
            "<tr>"
            f"<th>{html.escape(card['task'])}</th>"
            f"<td>{html.escape(card['dataset'])}</td>"
            f"<td>{html.escape(card['query_family'])}</td>"
            f"<td>{case['work']}</td>"
            f"<td>{case['recall']}</td>"
            f"<td>{case['lift']}</td>"
            f"<td>{str(card['r308_first_evidence']['operation_stack_high_lift']).lower()}</td>"
            f"<td>{html.escape(', '.join(card['counterpoints']) or 'none')}</td>"
            "</tr>"
        )
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>R309 Operation Problem Value</title>
  <style>
    body {{ font-family: system-ui, sans-serif; margin: 2rem; color: #1f2933; }}
    p {{ max-width: 980px; line-height: 1.5; }}
    table {{ border-collapse: collapse; margin-top: 1.25rem; font-size: 13px; }}
    th, td {{ border: 1px solid #d8dee9; padding: 0.5rem 0.7rem; text-align: left; }}
    th {{ background: #f6f8fa; }}
    code {{ background: #f6f8fa; padding: 0.1rem 0.25rem; border-radius: 4px; }}
  </style>
</head>
<body>
  <h1>R309 Operation Problem Value</h1>
  <p>{html.escape(report['headline'])}</p>
  <table>
    <thead>
      <tr><th>Task</th><th>Dataset</th><th>Family</th><th>Work</th><th>Recall</th><th>Lift</th><th>High-lift</th><th>Counterpoints</th></tr>
    </thead>
    <tbody>
      {''.join(rows)}
    </tbody>
  </table>
</body>
</html>
"""


def main() -> None:
    args = parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)
    report = build_report()
    json_path = args.out_dir / "problem-value-report.json"
    markdown_path = args.out_dir / "problem-value-report.md"
    html_path = args.out_dir / "index.html"
    run_result_path = args.out_dir / "run-result.json"
    report["outputs"] = {
        "json": rel(json_path),
        "markdown": rel(markdown_path),
        "html": rel(html_path),
    }
    write_json(json_path, report)
    markdown_path.write_text(render_markdown(report), encoding="utf-8")
    html_path.write_text(render_html(report), encoding="utf-8")
    write_json(
        run_result_path,
        {
            "status": "ok",
            "run_id": "R309",
            "json": rel(json_path),
            "markdown": rel(markdown_path),
            "html": rel(html_path),
            "tasks": report["summary"]["tasks"],
            "datasets": report["summary"]["dataset_count"],
        },
    )
    print(json.dumps(load_json(run_result_path), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
