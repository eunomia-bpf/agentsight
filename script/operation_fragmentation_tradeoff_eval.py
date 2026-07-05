#!/usr/bin/env python3
"""R334: positive-fragmentation and coverage audit for R320/R333.

This audit strengthens the "less fragmentation than fixed session/span trees"
part of the profiler claim without fetching, syncing, or creating datasets. It
reuses tracked R320 policy scores and R333 inspection curves. Hidden labels are
used only through the already-scored R320/R333 metrics after visible policies
have formed and ranked groups.
"""

from __future__ import annotations

import argparse
import csv
import html
import json
import math
import subprocess
import time
from pathlib import Path
from statistics import mean, median
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OUT_ROOT = ROOT / "docs" / "visexp" / "out"
R320_OUT = OUT_ROOT / "operation-profile-accuracy-r320"
R333_OUT = OUT_ROOT / "operation-inspection-frontier-r333"
R320_REPORT = R320_OUT / "profile-accuracy-report.json"
R320_POLICY_CSV = R320_OUT / "policy-scores.csv"
R333_REPORT = R333_OUT / "inspection-frontier-report.json"
R333_CURVES_CSV = R333_OUT / "task-policy-curves.csv"
DEFAULT_OUT_DIR = OUT_ROOT / "operation-fragmentation-tradeoff-r334"
RUN_ID = "R334"

DEFAULT_POLICY = "operation_stack:query_aware"
CORE_POLICIES = [
    "flat:width",
    "fixed_session:query_aware",
    "dataset_native:query_aware",
    "raw_action_stack:query_aware",
    "operation_stack:width",
    DEFAULT_POLICY,
]
BASELINES = [policy for policy in CORE_POLICIES if policy != DEFAULT_POLICY]

R320_METRICS = {
    "groups": ("lower", "all folded groups"),
    "positive_groups": ("lower", "groups containing at least one positive operation"),
    "groups_to_50pct_recall": ("lower", "ranked groups needed to cover 50% positives"),
    "work_to_50pct_recall": ("lower", "operation work needed to cover 50% positives"),
    "top5_recall": ("higher", "positive recall in top-5 groups"),
    "top5_work": ("lower", "operation work in top-5 groups"),
    "budget30_recall": ("higher", "recall under 30% operation budget"),
    "work_to_first_positive": ("lower", "work to first positive group"),
    "average_precision": ("higher", "AUPRC-style average precision"),
}
CURVE_METRICS = {
    "groups_inspected": ("lower", "groups inspected under the same work budget"),
    "best_recall": ("higher", "best recall under the same work budget"),
    "best_f1": ("higher", "best F1 under the same work budget"),
    "best_work": ("lower", "actual work consumed under the same budget"),
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


def load_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as file:
        return json.load(file)


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def parse_float(value: str) -> float | None:
    if value == "":
        return None
    return float(value)


def policy_key(row: dict[str, Any]) -> str:
    return f"{row['view']}:{row['ranker']}"


def load_r320_rows() -> list[dict[str, Any]]:
    numeric = {
        "operations",
        "positives",
        "prevalence",
        "groups",
        "positive_groups",
        "average_precision",
        "ndcg",
        "top5_recall",
        "top5_precision",
        "top5_f1",
        "top5_work",
        "budget30_recall",
        "budget30_f1",
        "budget30_work",
        "work_to_first_positive",
        "groups_to_50pct_recall",
        "work_to_50pct_recall",
    }
    rows: list[dict[str, Any]] = []
    with R320_POLICY_CSV.open(encoding="utf-8", newline="") as file:
        for row in csv.DictReader(file):
            row["policy"] = policy_key(row)
            row["uses_hidden_fields"] = row["uses_hidden_fields"] == "True"
            for key in numeric:
                row[key] = parse_float(row[key])
            if not row["uses_hidden_fields"] and row["policy"] in CORE_POLICIES:
                rows.append(row)
    return rows


def load_r333_curve_rows() -> list[dict[str, Any]]:
    numeric = {
        "work_budget",
        "best_work",
        "best_recall",
        "best_precision",
        "best_f1",
        "best_lift",
        "groups_inspected",
    }
    rows: list[dict[str, Any]] = []
    with R333_CURVES_CSV.open(encoding="utf-8", newline="") as file:
        for row in csv.DictReader(file):
            for key in numeric:
                row[key] = parse_float(row[key])
            if row["policy"] in CORE_POLICIES:
                rows.append(row)
    return rows


def median_or_none(values: list[float]) -> float | None:
    return float(median(values)) if values else None


def mean_or_none(values: list[float]) -> float | None:
    return float(mean(values)) if values else None


def safe_ratio(left: float | None, right: float | None) -> float | None:
    if left is None or right is None:
        return None
    if right == 0:
        return None if left == 0 else float("inf")
    return left / right


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


def compare_metric(
    left: float | None,
    right: float | None,
    direction: str,
) -> int:
    if left is None or right is None:
        return 0
    if direction == "higher":
        if left > right + 1e-12:
            return 1
        if right > left + 1e-12:
            return -1
        return 0
    if left < right - 1e-12:
        return 1
    if right < left - 1e-12:
        return -1
    return 0


def build_r320_comparisons(rows: list[dict[str, Any]], tasks: list[str]) -> list[dict[str, Any]]:
    by_key = {(row["task"], row["policy"]): row for row in rows}
    output: list[dict[str, Any]] = []
    for baseline in BASELINES:
        for metric, (direction, description) in R320_METRICS.items():
            wins = ties = losses = 0
            deltas: list[float] = []
            ratios: list[float] = []
            for task in tasks:
                default = by_key[(task, DEFAULT_POLICY)][metric]
                base = by_key[(task, baseline)][metric]
                if default is None or base is None:
                    continue
                delta = default - base
                deltas.append(delta)
                ratio = safe_ratio(default, base)
                if ratio is not None:
                    ratios.append(ratio)
                result = compare_metric(default, base, direction)
                if result > 0:
                    wins += 1
                elif result < 0:
                    losses += 1
                else:
                    ties += 1
            output.append(
                {
                    "source": "R320",
                    "default_policy": DEFAULT_POLICY,
                    "baseline_policy": baseline,
                    "metric": metric,
                    "metric_description": description,
                    "direction": direction,
                    "wins": wins,
                    "ties": ties,
                    "losses": losses,
                    "median_delta_default_minus_baseline": median_or_none(deltas),
                    "mean_delta_default_minus_baseline": mean_or_none(deltas),
                    "median_ratio_default_over_baseline": median_or_none(ratios),
                }
            )
    return output


def build_curve_comparisons(rows: list[dict[str, Any]], tasks: list[str]) -> list[dict[str, Any]]:
    by_key = {(row["task"], row["policy"], row["work_budget"]): row for row in rows}
    output: list[dict[str, Any]] = []
    for baseline in BASELINES:
        for metric, (direction, description) in CURVE_METRICS.items():
            for budget in [0.20, 0.30]:
                wins = ties = losses = 0
                deltas: list[float] = []
                ratios: list[float] = []
                for task in tasks:
                    default = by_key[(task, DEFAULT_POLICY, budget)][metric]
                    base = by_key[(task, baseline, budget)][metric]
                    if default is None or base is None:
                        continue
                    delta = default - base
                    deltas.append(delta)
                    ratio = safe_ratio(default, base)
                    if ratio is not None:
                        ratios.append(ratio)
                    result = compare_metric(default, base, direction)
                    if result > 0:
                        wins += 1
                    elif result < 0:
                        losses += 1
                    else:
                        ties += 1
                output.append(
                    {
                        "source": "R333",
                        "work_budget": budget,
                        "default_policy": DEFAULT_POLICY,
                        "baseline_policy": baseline,
                        "metric": metric,
                        "metric_description": description,
                        "direction": direction,
                        "wins": wins,
                        "ties": ties,
                        "losses": losses,
                        "median_delta_default_minus_baseline": median_or_none(deltas),
                        "mean_delta_default_minus_baseline": mean_or_none(deltas),
                        "median_ratio_default_over_baseline": median_or_none(ratios),
                    }
                )
    return output


def task_fragmentation_cases(
    r320_rows: list[dict[str, Any]],
    curve_rows: list[dict[str, Any]],
    tasks: list[str],
) -> list[dict[str, Any]]:
    r320 = {(row["task"], row["policy"]): row for row in r320_rows}
    curves = {(row["task"], row["policy"], row["work_budget"]): row for row in curve_rows}
    output: list[dict[str, Any]] = []
    for task in tasks:
        op = r320[(task, DEFAULT_POLICY)]
        fixed = r320[(task, "fixed_session:query_aware")]
        op_curve = curves[(task, DEFAULT_POLICY, 0.30)]
        fixed_curve = curves[(task, "fixed_session:query_aware", 0.30)]
        output.append(
            {
                "task": task,
                "dataset": op["dataset"],
                "query_family": op["query_family"],
                "operation_stack_groups": op["groups"],
                "fixed_session_groups": fixed["groups"],
                "group_delta": op["groups"] - fixed["groups"],
                "operation_stack_positive_groups": op["positive_groups"],
                "fixed_session_positive_groups": fixed["positive_groups"],
                "positive_group_delta": op["positive_groups"] - fixed["positive_groups"],
                "operation_stack_groups_to_50pct": op["groups_to_50pct_recall"],
                "fixed_session_groups_to_50pct": fixed["groups_to_50pct_recall"],
                "groups_to_50pct_delta": (
                    op["groups_to_50pct_recall"] - fixed["groups_to_50pct_recall"]
                    if op["groups_to_50pct_recall"] is not None
                    and fixed["groups_to_50pct_recall"] is not None
                    else None
                ),
                "operation_stack_work_to_50pct": op["work_to_50pct_recall"],
                "fixed_session_work_to_50pct": fixed["work_to_50pct_recall"],
                "work_to_50pct_delta": (
                    op["work_to_50pct_recall"] - fixed["work_to_50pct_recall"]
                    if op["work_to_50pct_recall"] is not None
                    and fixed["work_to_50pct_recall"] is not None
                    else None
                ),
                "operation_stack_budget30_groups": op_curve["groups_inspected"],
                "fixed_session_budget30_groups": fixed_curve["groups_inspected"],
                "budget30_group_delta": (
                    op_curve["groups_inspected"] - fixed_curve["groups_inspected"]
                ),
                "operation_stack_budget30_recall": op_curve["best_recall"],
                "fixed_session_budget30_recall": fixed_curve["best_recall"],
                "budget30_recall_delta": op_curve["best_recall"] - fixed_curve["best_recall"],
            }
        )
    return output


def find_comparison(
    rows: list[dict[str, Any]],
    baseline: str,
    metric: str,
    source: str,
    budget: float | None = None,
) -> dict[str, Any]:
    for row in rows:
        if row["baseline_policy"] != baseline or row["metric"] != metric or row["source"] != source:
            continue
        if budget is None or abs(row.get("work_budget", -1) - budget) <= 1e-12:
            return row
    raise KeyError((source, baseline, metric, budget))


def summary_value(rows: list[dict[str, Any]], policy: str, metric: str) -> float:
    values = [row[metric] for row in rows if row["policy"] == policy and row[metric] is not None]
    return float(median(values))


def primary_findings(
    r320_rows: list[dict[str, Any]],
    comparisons: list[dict[str, Any]],
    curve_comparisons: list[dict[str, Any]],
) -> list[str]:
    fixed_groups = find_comparison(comparisons, "fixed_session:query_aware", "groups", "R320")
    fixed_positive = find_comparison(
        comparisons, "fixed_session:query_aware", "positive_groups", "R320"
    )
    fixed_g50 = find_comparison(
        comparisons, "fixed_session:query_aware", "groups_to_50pct_recall", "R320"
    )
    fixed_w50 = find_comparison(
        comparisons, "fixed_session:query_aware", "work_to_50pct_recall", "R320"
    )
    fixed_top5_work = find_comparison(
        comparisons, "fixed_session:query_aware", "top5_work", "R320"
    )
    fixed_wtfp = find_comparison(
        comparisons, "fixed_session:query_aware", "work_to_first_positive", "R320"
    )
    fixed_budget_groups = find_comparison(
        curve_comparisons,
        "fixed_session:query_aware",
        "groups_inspected",
        "R333",
        0.30,
    )
    fixed_budget_recall = find_comparison(
        curve_comparisons,
        "fixed_session:query_aware",
        "best_recall",
        "R333",
        0.30,
    )
    flat_w50 = summary_value(r320_rows, "flat:width", "work_to_50pct_recall")
    op_w50 = summary_value(r320_rows, DEFAULT_POLICY, "work_to_50pct_recall")
    flat_top5_work = find_comparison(comparisons, "flat:width", "top5_work", "R320")
    raw_w50 = find_comparison(
        comparisons, "raw_action_stack:query_aware", "work_to_50pct_recall", "R320"
    )
    dataset_budget = find_comparison(
        curve_comparisons,
        "dataset_native:query_aware",
        "best_recall",
        "R333",
        0.30,
    )
    width_ap = find_comparison(comparisons, "operation_stack:width", "average_precision", "R320")
    width_budget = find_comparison(
        comparisons, "operation_stack:width", "budget30_recall", "R320"
    )
    width_g50 = find_comparison(
        comparisons, "operation_stack:width", "groups_to_50pct_recall", "R320"
    )
    return [
        "Against fixed_session:query_aware, operation_stack:query_aware reduces total groups "
        f"on {fixed_groups['wins']}/6 tasks and positive groups on {fixed_positive['wins']}/6 tasks; "
        "it reaches 50% positive recall with fewer ranked groups on "
        f"{fixed_g50['wins']}/6 tasks (median delta {fixed_g50['median_delta_default_minus_baseline']:.1f} groups).",
        "At the same 30% inspected-work budget, operation_stack:query_aware inspects fewer groups than "
        f"fixed_session:query_aware on {fixed_budget_groups['wins']}/6 tasks "
        f"(median delta {fixed_budget_groups['median_delta_default_minus_baseline']:.1f} groups) "
        f"while its median recall delta is {fixed_budget_recall['median_delta_default_minus_baseline']:.4f}.",
        "The fixed-session result is a fragmentation result, not work dominance: operation_stack:query_aware "
        f"has lower work-to-50%-recall on only {fixed_w50['wins']}/6 tasks, lower top-5 work on only "
        f"{fixed_top5_work['wins']}/6 tasks, and lower work-to-first-positive on only "
        f"{fixed_wtfp['wins']}/6 tasks.",
        "Against flat summaries, operation_stack:query_aware reaches 50% positive recall with median work "
        f"{op_w50:.4f} instead of {flat_w50:.4f}, and top-5 work is lower on "
        f"{flat_top5_work['wins']}/6 tasks; flat remains a single coarse group, not a fragmentation win.",
        "Mapping and ranker choices remain mechanisms, not magic defaults: relative to raw_action_stack:query_aware, "
        f"operation_stack:query_aware lowers work-to-50%-recall on {raw_w50['wins']}/6 tasks; relative to "
        f"dataset_native:query_aware, it improves 30%-budget recall on {dataset_budget['wins']}/6 tasks. "
        f"Relative to operation_stack:width, query-aware ranking improves AP on {width_ap['wins']}/6 tasks "
        f"and budget30 recall on {width_budget['wins']}/6 tasks, but reaches 50% positives with fewer groups "
        f"on only {width_g50['wins']}/6 tasks.",
    ]


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: round_value(row.get(field)) for field in fields})


def render_markdown(report: dict[str, Any], out_dir: Path) -> str:
    lines = [
        "# R334 Fragmentation Tradeoff Audit",
        "",
        "R334 reads tracked R320 policy scores and R333 inspection curves to separate group fragmentation from operation-work cost. It does not fetch, sync, create, or relabel a dataset.",
        "",
        "## Primary Findings",
        "",
    ]
    for item in report["primary_findings"]:
        lines.append(f"- {item}")
    lines.extend(["", "## Non-Claims", ""])
    for item in report["non_claims"]:
        lines.append(f"- {item}")
    lines.extend(
        [
            "",
            "## Artifacts",
            "",
            f"- Report: `{rel(out_dir / 'fragmentation-tradeoff-report.json')}`",
            f"- Default comparisons: `{rel(out_dir / 'default-fragmentation-comparisons.csv')}`",
            f"- Budget comparisons: `{rel(out_dir / 'budget-fragmentation-comparisons.csv')}`",
            f"- Fixed-session task cases: `{rel(out_dir / 'fixed-session-fragmentation-cases.csv')}`",
        ]
    )
    return "\n".join(lines) + "\n"


def render_html(report: dict[str, Any]) -> str:
    findings = "\n".join(f"<li>{html.escape(item)}</li>" for item in report["primary_findings"])
    non_claims = "\n".join(f"<li>{html.escape(item)}</li>" for item in report["non_claims"])
    return f"""<!doctype html>
<html>
<head><meta charset="utf-8"><title>R334 Fragmentation Tradeoff</title></head>
<body>
<h1>R334 Fragmentation Tradeoff Audit</h1>
<p>Reuses tracked R320/R333 artifacts; no dataset sync, creation, or relabeling.</p>
<h2>Primary Findings</h2>
<ul>
{findings}
</ul>
<h2>Non-Claims</h2>
<ul>
{non_claims}
</ul>
</body>
</html>
"""


def main() -> None:
    start = time.perf_counter()
    args = parse_args()
    out_dir = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    r320_report = load_json(R320_REPORT)
    r333_report = load_json(R333_REPORT)
    source_operations = [
        ROOT / path for path in r333_report["input_policy"]["source_operations"]
    ]
    ensure_sources_tracked_clean(
        [
            R320_REPORT,
            R320_POLICY_CSV,
            R333_REPORT,
            R333_CURVES_CSV,
            *source_operations,
        ]
    )

    r320_rows = load_r320_rows()
    curve_rows = load_r333_curve_rows()
    tasks = sorted({row["task"] for row in r320_rows})
    if len(tasks) != 6:
        raise SystemExit(f"expected 6 tasks, found {len(tasks)}")
    comparisons = build_r320_comparisons(r320_rows, tasks)
    curve_comparisons = build_curve_comparisons(curve_rows, tasks)
    cases = task_fragmentation_cases(r320_rows, curve_rows, tasks)
    elapsed = time.perf_counter() - start

    report = {
        "run_id": RUN_ID,
        "schema": "agentsight.fragmentation-tradeoff.v1",
        "purpose": "separate positive-fragmentation evidence from operation-work cost for the R320/R333 profiler claim",
        "source_run_ids": ["R320", "R333"],
        "network_access_required": False,
        "input_policy": {
            "sync": "none",
            "create": "none",
            "relabel": "none",
            "dataset_sync": "none",
            "dataset_creation": "none",
            "dataset_relabeling": "none",
            "source_operations": [rel(path) for path in source_operations],
            "hidden_label_use": "R320/R333 hidden labels are used only after visible groups/rankings are formed",
        },
        "profiler_abstractions": ["operation", "operation stack"],
        "default_policy": DEFAULT_POLICY,
        "core_policies": CORE_POLICIES,
        "totals": {
            "tasks": len(tasks),
            "datasets": r320_report["totals"]["datasets"],
            "task_operations": r320_report["totals"]["task_operations"],
            "positive_operations": r320_report["totals"]["positive_operations"],
            "r320_core_policy_scores": len(r320_rows),
            "r320_default_comparison_rows": len(comparisons),
            "r333_core_curve_rows": len(curve_rows),
            "r333_budget_comparison_rows": len(curve_comparisons),
            "fixed_session_case_rows": len(cases),
        },
        "source_check": {
            "status": "pass",
            "tracked_clean_files": len(source_operations) + 4,
            "reference_artifacts": [
                rel(R320_REPORT),
                rel(R320_POLICY_CSV),
                rel(R333_REPORT),
                rel(R333_CURVES_CSV),
            ],
        },
        "non_claims": [
            "no new datasets, dataset sync, dataset creation, or relabeling",
            "no human or agent analyst productivity, accuracy, or time-to-answer claim",
            "no claim that operation stacks minimize every group-count or work metric",
            "no automatic view selector, universal boundary detector, or label-free deployed ranker",
            "no full OpenTelemetry/Phoenix/LangSmith/Langfuse/Perfetto compatibility claim",
            "no profiler abstraction beyond operation and operation stack",
        ],
        "comparisons": comparisons,
        "budget_comparisons": curve_comparisons,
        "fixed_session_task_cases": cases,
        "reproducibility": {
            "commit": git_output(["rev-parse", "HEAD"]),
            "elapsed_seconds": round(elapsed, 4),
            "network_access_required": False,
        },
    }
    report["primary_findings"] = primary_findings(r320_rows, comparisons, curve_comparisons)
    report = round_value(report)

    report_path = out_dir / "fragmentation-tradeoff-report.json"
    markdown_path = out_dir / "fragmentation-tradeoff-report.md"
    html_path = out_dir / "index.html"
    comparison_csv = out_dir / "default-fragmentation-comparisons.csv"
    budget_csv = out_dir / "budget-fragmentation-comparisons.csv"
    cases_csv = out_dir / "fixed-session-fragmentation-cases.csv"
    run_result_path = out_dir / "run-result.json"

    write_json(report_path, report)
    markdown_path.write_text(render_markdown(report, out_dir), encoding="utf-8")
    html_path.write_text(render_html(report), encoding="utf-8")
    write_csv(
        comparison_csv,
        comparisons,
        [
            "source",
            "default_policy",
            "baseline_policy",
            "metric",
            "metric_description",
            "direction",
            "wins",
            "ties",
            "losses",
            "median_delta_default_minus_baseline",
            "mean_delta_default_minus_baseline",
            "median_ratio_default_over_baseline",
        ],
    )
    write_csv(
        budget_csv,
        curve_comparisons,
        [
            "source",
            "work_budget",
            "default_policy",
            "baseline_policy",
            "metric",
            "metric_description",
            "direction",
            "wins",
            "ties",
            "losses",
            "median_delta_default_minus_baseline",
            "mean_delta_default_minus_baseline",
            "median_ratio_default_over_baseline",
        ],
    )
    write_csv(
        cases_csv,
        cases,
        [
            "task",
            "dataset",
            "query_family",
            "operation_stack_groups",
            "fixed_session_groups",
            "group_delta",
            "operation_stack_positive_groups",
            "fixed_session_positive_groups",
            "positive_group_delta",
            "operation_stack_groups_to_50pct",
            "fixed_session_groups_to_50pct",
            "groups_to_50pct_delta",
            "operation_stack_work_to_50pct",
            "fixed_session_work_to_50pct",
            "work_to_50pct_delta",
            "operation_stack_budget30_groups",
            "fixed_session_budget30_groups",
            "budget30_group_delta",
            "operation_stack_budget30_recall",
            "fixed_session_budget30_recall",
            "budget30_recall_delta",
        ],
    )
    write_json(
        run_result_path,
        {
            "run_id": RUN_ID,
            "status": "pass",
            "report": rel(report_path),
            "markdown": rel(markdown_path),
            "html": rel(html_path),
            "default_fragmentation_comparisons_csv": rel(comparison_csv),
            "budget_fragmentation_comparisons_csv": rel(budget_csv),
            "fixed_session_fragmentation_cases_csv": rel(cases_csv),
        },
    )

    print(render_markdown(report, out_dir))


if __name__ == "__main__":
    main()
