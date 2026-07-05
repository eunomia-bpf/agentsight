#!/usr/bin/env python3
"""R346: diagnostic casebook over existing labeled agent traces.

This run does not fetch, sync, create, or relabel datasets. It reads the
tracked R300/R335/R345 artifacts and existing public labeled operation JSONL,
then builds a reviewer-facing casebook that connects top-ranked operation-stack
groups to hidden-label scoring, diagnostic lenses, optimization actions, and
baseline counterpoints.
"""

from __future__ import annotations

import argparse
import csv
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
R335_DIR = OUT_ROOT / "operation-actionability-synthesis-r335"
R345_DIR = OUT_ROOT / "operation-diagnostic-lens-portfolio-r345"
DEFAULT_OUT_DIR = OUT_ROOT / "operation-diagnostic-casebook-r346"
RUN_ID = "R346"

R335_CARDS = R335_DIR / "task-actionability-cards.csv"
R345_REPORT = R345_DIR / "diagnostic-lens-report.json"
R345_TASK_CARDS = R345_DIR / "task-lens-cards.csv"
R345_COUNTERPOINTS = R345_DIR / "counterpoint-ledger.csv"

CASE_GROUPS_PER_TASK = 5
COUNTERPOINTS_PER_TASK = 3

sys.path.insert(0, str(Path(__file__).resolve().parent))
import operation_analyst_ranking_eval as r302  # noqa: E402
import operation_case_study_eval as r304  # noqa: E402
import operation_query_utility_eval as r300  # noqa: E402

HIDDEN_FIELDS = set(r304.HIDDEN_FIELDS) | {
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
    parser.add_argument("--groups-per-task", type=int, default=CASE_GROUPS_PER_TASK)
    return parser.parse_args()


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return str(path.resolve())


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
    statuses: dict[str, str] = {}
    for path in paths:
        if not path.exists():
            raise SystemExit(f"missing source artifact {rel(path)}")
        git_check("source artifact is not git-tracked", path, ["ls-files", "--error-unmatch"])
        git_check("source artifact has unstaged changes", path, ["diff", "--quiet"])
        git_check("source artifact has staged changes", path, ["diff", "--cached", "--quiet"])
        statuses[rel(path)] = "tracked_clean"
    return statuses


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(round_value(payload), indent=2, sort_keys=True) + "\n", encoding="utf-8")


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as file:
        return list(csv.DictReader(file))


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: format_value(row.get(field)) for field in fields})


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


def split_semicolon(value: str) -> list[str]:
    return [item.strip() for item in value.split(";") if item.strip()]


def assert_visible_packet_has_no_hidden_fields(packet: dict[str, Any]) -> None:
    def walk(value: Any, path: str = "$") -> None:
        if isinstance(value, dict):
            for key, child in value.items():
                if key in HIDDEN_FIELDS:
                    raise SystemExit(f"hidden field {key!r} leaked at {path}")
                walk(child, f"{path}.{key}")
        elif isinstance(value, list):
            for index, child in enumerate(value):
                walk(child, f"{path}[{index}]")

    walk(packet)


def first_positive_location(ranked_groups: list[dict[str, Any]], total_ops: int) -> dict[str, Any]:
    inspected = 0
    for rank, group in enumerate(ranked_groups, 1):
        inspected += group["operations"]
        if group["positives"] > 0:
            return {
                "first_positive_rank": rank,
                "first_positive_work": inspected / total_ops if total_ops else 0.0,
                "first_positive_group_id": r304.short_hash(group["stack"]),
                "first_positive_positive_rate": group["positives"] / group["operations"]
                if group["operations"]
                else 0.0,
            }
    return {
        "first_positive_rank": None,
        "first_positive_work": None,
        "first_positive_group_id": "",
        "first_positive_positive_rate": 0.0,
    }


def group_counterpoints(rows: list[dict[str, str]]) -> dict[str, list[dict[str, str]]]:
    grouped: dict[str, list[dict[str, str]]] = {}
    for row in rows:
        grouped.setdefault(row["task"], []).append(row)
    for task, task_rows in grouped.items():
        task_rows.sort(key=lambda row: (row["source"], row["objective_or_metric"], row["best_policy"]))
        grouped[task] = task_rows[:COUNTERPOINTS_PER_TASK]
    return grouped


def summarize_counterpoints(rows: list[dict[str, str]]) -> list[str]:
    summaries = []
    for row in rows:
        regret = row.get("operation_stack_query_aware_regret", "")
        suffix = f", regret={regret}" if regret else ""
        summaries.append(f"{row['objective_or_metric']}->{row['best_policy']}{suffix}")
    return summaries


def task_by_id() -> dict[str, dict[str, Any]]:
    return {task["id"]: task for task in r300.TASKS}


def build_casebook(groups_per_task: int) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    r302.validate_no_hidden_rank_features()

    action_cards = {row["task"]: row for row in read_csv(R335_CARDS)}
    lens_cards = {row["task"]: row for row in read_csv(R345_TASK_CARDS)}
    counterpoints = group_counterpoints(read_csv(R345_COUNTERPOINTS))
    r345_report = load_json(R345_REPORT)

    visible_cases: list[dict[str, Any]] = []
    answer_cases: list[dict[str, Any]] = []
    scored_cards: list[dict[str, Any]] = []
    top_stack_rows: list[dict[str, Any]] = []

    for task in r300.TASKS:
        groups, op_summary = r304.group_task_operations(task)
        ranked = sorted(
            groups,
            key=lambda group: r302.rank_score(group, task, "query_aware"),
            reverse=True,
        )
        selected = ranked[:groups_per_task]
        score = r304.score_selected(selected, op_summary)
        first_positive = first_positive_location(ranked, op_summary["operations"])
        action_card = action_cards[task["id"]]
        lens_card = lens_cards[task["id"]]
        task_counterpoints = counterpoints.get(task["id"], [])

        visible_cases.append(
            {
                "task": task["id"],
                "dataset": task["dataset"],
                "query_family": task["query_family"],
                "problem": task["problem"],
                "ranker": "query_aware",
                "view": "operation_stack",
                "groups": [
                    r304.visible_group(group, index) for index, group in enumerate(selected, 1)
                ],
                "visible_stack_fields": split_semicolon(lens_card["useful_stack_fields"].replace(",", ";")),
                "visual_recipe": lens_card["visual_recipe"],
            }
        )

        answer_cases.append(
            {
                "task": task["id"],
                "dataset": task["dataset"],
                "oracle_field": task["oracle_field"],
                "positive_values": sorted(task["positive_values"]),
                "score": score,
                "first_positive": first_positive,
                "groups": [
                    r304.answer_group(group, index) for index, group in enumerate(selected, 1)
                ],
                "optimization_action": lens_card["optimization_action"],
                "counterpoints": task_counterpoints,
            }
        )

        top_group = selected[0] if selected else None
        top_positive_rate = (
            top_group["positives"] / top_group["operations"] if top_group and top_group["operations"] else 0.0
        )
        task_row = {
            "task": task["id"],
            "dataset": task["dataset"],
            "query_family": task["query_family"],
            "operations": op_summary["operations"],
            "positives": op_summary["positives"],
            "operation_stack_groups": op_summary["groups"],
            "top_groups": groups_per_task,
            "top1_positive": bool(top_group and top_group["positives"] > 0),
            "top1_positive_rate": top_positive_rate,
            "top5_positive_groups": sum(1 for group in selected if group["positives"] > 0),
            "top5_recall": score["positive_recall"],
            "top5_precision": score["positive_precision"],
            "top5_lift": score["positive_lift"],
            "top5_work": score["inspected_operation_fraction"],
            "first_positive_rank": first_positive["first_positive_rank"],
            "first_positive_work": first_positive["first_positive_work"],
            "distinct_best_views": int(lens_card["distinct_best_views"]),
            "best_views": lens_card["best_views"],
            "visual_recipe": lens_card["visual_recipe"],
            "optimization_action": lens_card["optimization_action"],
            "counterpoints": summarize_counterpoints(task_counterpoints),
            "actionability_status": lens_card["actionability_status"],
            "recommendation": action_card.get("recommendation", action_card["optimization_action"]),
        }
        scored_cards.append(task_row)

        for rank, group in enumerate(selected, 1):
            top_stack_rows.append(
                {
                    "task": task["id"],
                    "dataset": task["dataset"],
                    "rank": rank,
                    "group_id": r304.short_hash(group["stack"]),
                    "stack": group["stack"],
                    "operations": group["operations"],
                    "positive_operations": group["positives"],
                    "positive_rate": group["positives"] / group["operations"]
                    if group["operations"]
                    else 0.0,
                    "sessions": group["sessions"],
                    "visible_score_policy": "query_aware",
                }
            )

    summary = build_summary(scored_cards, r345_report, groups_per_task)
    visible_packet = {
        "run_id": RUN_ID,
        "schema": "agentsight.diagnostic-casebook.visible.v1",
        "input_policy": "no dataset sync; top groups selected by visible query-aware operation-stack ranking",
        "withheld_field_policy": "hidden labels and scoring fields are excluded from this visible packet and kept in the answer key",
        "groups_per_task": groups_per_task,
        "cases": visible_cases,
    }
    answer_key = {
        "run_id": RUN_ID,
        "schema": "agentsight.diagnostic-casebook.answer-key.v1",
        "input_policy": "hidden labels are used only after visible ranking to score case evidence",
        "cases": answer_cases,
    }
    report = {
        "run_id": RUN_ID,
        "schema": "agentsight.diagnostic-casebook.v1",
        "summary": summary,
        "task_cards": scored_cards,
        "top_stack_evidence": top_stack_rows,
        "claim_scope": {
            "supported": "top-ranked operation-stack groups can be audited as concrete failure, safety, quality, and boundary cases and linked to diagnostic lenses and optimization actions",
            "narrowed": "casebook evidence is automated hidden-label scoring over existing public labels, not a human productivity study",
            "not_supported": "automatic discovery of all intent boundaries, universal selector, or complete trace-ecosystem compatibility",
        },
    }
    assert_visible_packet_has_no_hidden_fields(visible_packet)
    return visible_packet, answer_key, report


def build_summary(
    scored_cards: list[dict[str, Any]],
    r345_report: dict[str, Any],
    groups_per_task: int,
) -> dict[str, Any]:
    datasets = sorted({row["dataset"] for row in scored_cards})
    return {
        "overall": "pass",
        "network_access_required": False,
        "tasks": len(scored_cards),
        "datasets": len(datasets),
        "top_groups_per_task": groups_per_task,
        "case_groups": sum(row["top_groups"] for row in scored_cards),
        "tasks_with_top1_positive": sum(row["top1_positive"] for row in scored_cards),
        "tasks_with_positive_in_top5": sum(row["top5_positive_groups"] > 0 for row in scored_cards),
        "median_top5_recall": median(row["top5_recall"] for row in scored_cards),
        "median_top5_precision": median(row["top5_precision"] for row in scored_cards),
        "median_top5_lift": median(row["top5_lift"] for row in scored_cards),
        "median_top5_work": median(row["top5_work"] for row in scored_cards),
        "median_first_positive_work": median(
            row["first_positive_work"]
            for row in scored_cards
            if row["first_positive_work"] is not None
        ),
        "tasks_with_actionable_case_cards": sum(
            row["actionability_status"].startswith("actionable") for row in scored_cards
        ),
        "tasks_with_counterpoints": sum(bool(row["counterpoints"]) for row in scored_cards),
        "tasks_with_three_or_more_best_views": r345_report["summary"][
            "tasks_with_three_or_more_best_views"
        ],
        "min_distinct_best_views_per_task": min(row["distinct_best_views"] for row in scored_cards),
        "max_distinct_best_views_per_task": max(row["distinct_best_views"] for row in scored_cards),
    }


def render_markdown(report: dict[str, Any]) -> str:
    summary = report["summary"]
    lines = [
        "# R346 Diagnostic Casebook",
        "",
        "R346 links visible top-ranked operation-stack groups to hidden-label scoring, "
        "diagnostic lenses, optimization actions, and counterpoints without fetching or "
        "relabeling datasets.",
        "",
        "## Summary",
        "",
        f"- Overall: {summary['overall']}.",
        f"- Tasks / datasets: {summary['tasks']} / {summary['datasets']}.",
        f"- Case groups: {summary['case_groups']}.",
        f"- Top-1 positive tasks: {summary['tasks_with_top1_positive']}/{summary['tasks']}.",
        f"- Top-5 positive tasks: {summary['tasks_with_positive_in_top5']}/{summary['tasks']}.",
        f"- Median top-5 recall / precision / work: {summary['median_top5_recall']:.4f} / {summary['median_top5_precision']:.4f} / {summary['median_top5_work']:.4f}.",
        f"- Actionable case cards: {summary['tasks_with_actionable_case_cards']}/{summary['tasks']}.",
        "",
        "## Task Cards",
        "",
        "| Task | Dataset | Top-5 recall | Top-5 precision | Work | First-positive work | Best views | Optimization action |",
        "|---|---|---:|---:|---:|---:|---|---|",
    ]
    for row in report["task_cards"]:
        lines.append(
            f"| {row['task']} | {row['dataset']} | {row['top5_recall']:.4f} | {row['top5_precision']:.4f} | {row['top5_work']:.4f} | {row['first_positive_work']:.4f} | {row['best_views']} | {row['optimization_action']} |"
        )
    lines.extend(
        [
            "",
            "## Claim Scope",
            "",
            "- Supports: concrete label-scored case evidence for profiler localization and actionability.",
            "- Narrows: automated case evidence, not a human analyst study.",
            "- Excludes: automatic universal selector, complete boundary discovery, and trace-ecosystem compatibility.",
        ]
    )
    return "\n".join(lines) + "\n"


def render_html(report: dict[str, Any]) -> str:
    summary = report["summary"]
    cards = "\n".join(
        "<section>"
        f"<h2>{html.escape(row['task'])}</h2>"
        f"<p><strong>Dataset:</strong> {html.escape(row['dataset'])}. "
        f"<strong>Top-5 recall:</strong> {row['top5_recall']:.4f}. "
        f"<strong>Top-5 work:</strong> {row['top5_work']:.4f}. "
        f"<strong>First-positive work:</strong> {row['first_positive_work']:.4f}.</p>"
        f"<p><strong>Diagnostic recipe:</strong> {html.escape(row['visual_recipe'])}</p>"
        f"<p><strong>Optimization action:</strong> {html.escape(row['optimization_action'])}</p>"
        f"<p><strong>Counterpoints:</strong> {html.escape('; '.join(row['counterpoints']))}</p>"
        "</section>"
        for row in report["task_cards"]
    )
    return f"""<!doctype html>
<html lang="en">
<meta charset="utf-8">
<title>R346 Diagnostic Casebook</title>
<style>
body {{ font-family: system-ui, sans-serif; margin: 32px; color: #202124; }}
p {{ max-width: 980px; line-height: 1.5; }}
section {{ border-top: 1px solid #d7dce2; padding: 18px 0; }}
h1, h2 {{ margin-bottom: 8px; }}
.summary {{ background: #f4f7fb; padding: 16px; max-width: 980px; }}
</style>
<h1>R346 Diagnostic Casebook</h1>
<div class="summary">
<p>Overall: {html.escape(summary['overall'])}. Tasks: {summary['tasks']}. Datasets: {summary['datasets']}. Case groups: {summary['case_groups']}.</p>
<p>Top-1 positive tasks: {summary['tasks_with_top1_positive']}/{summary['tasks']}; top-5 positive tasks: {summary['tasks_with_positive_in_top5']}/{summary['tasks']}; median top-5 recall: {summary['median_top5_recall']:.4f}; median work: {summary['median_top5_work']:.4f}.</p>
</div>
{cards}
</html>
"""


def main() -> None:
    args = parse_args()
    out_dir = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    operation_files = sorted({Path(task["operation_file"]) for task in r300.TASKS})
    source_paths = [R335_CARDS, R345_REPORT, R345_TASK_CARDS, R345_COUNTERPOINTS, *operation_files]
    source_status = ensure_sources_tracked_clean(source_paths)

    visible_packet, answer_key, report = build_casebook(args.groups_per_task)
    report["source_status"] = source_status

    write_json(out_dir / "visible-diagnostic-casebook.json", visible_packet)
    write_json(out_dir / "answer-key.json", answer_key)
    write_json(out_dir / "diagnostic-casebook-report.json", report)
    write_csv(
        out_dir / "task-diagnostic-case-cards.csv",
        report["task_cards"],
        [
            "task",
            "dataset",
            "query_family",
            "operations",
            "positives",
            "operation_stack_groups",
            "top_groups",
            "top1_positive",
            "top1_positive_rate",
            "top5_positive_groups",
            "top5_recall",
            "top5_precision",
            "top5_lift",
            "top5_work",
            "first_positive_rank",
            "first_positive_work",
            "distinct_best_views",
            "best_views",
            "visual_recipe",
            "optimization_action",
            "counterpoints",
            "actionability_status",
            "recommendation",
        ],
    )
    write_csv(
        out_dir / "top-stack-evidence.csv",
        report["top_stack_evidence"],
        [
            "task",
            "dataset",
            "rank",
            "group_id",
            "stack",
            "operations",
            "positive_operations",
            "positive_rate",
            "sessions",
            "visible_score_policy",
        ],
    )
    (out_dir / "diagnostic-casebook-report.md").write_text(render_markdown(report), encoding="utf-8")
    (out_dir / "index.html").write_text(render_html(report), encoding="utf-8")

    run_result = {
        "run_id": RUN_ID,
        "schema": "agentsight.diagnostic-casebook-run.v1",
        "status": "ok",
        "summary": report["summary"],
        "json": rel(out_dir / "diagnostic-casebook-report.json"),
        "visible_packet": rel(out_dir / "visible-diagnostic-casebook.json"),
        "answer_key": rel(out_dir / "answer-key.json"),
        "markdown": rel(out_dir / "diagnostic-casebook-report.md"),
        "html": rel(out_dir / "index.html"),
    }
    write_json(out_dir / "run-result.json", run_result)
    print(json.dumps(round_value(run_result), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
