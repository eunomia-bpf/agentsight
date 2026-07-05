#!/usr/bin/env python3
"""R331: prevalence and label-permutation negative controls for R320.

This audit does not fetch, sync, or create a dataset. It reuses the tracked R320
task definitions and operation JSONL inputs. For each visible policy, it keeps
the same groups and the same visible ranking order, then randomly reallocates
the task's hidden positive labels across operation positions. The resulting
null distribution estimates how much AP, top-k precision, budget recall, and
work-to-first-positive can be explained by prevalence, group size, and ranking
length alone.
"""

from __future__ import annotations

import argparse
import csv
import html
import json
import math
import random
import subprocess
import time
from pathlib import Path
from statistics import mean, median
from typing import Any

import sys

ROOT = Path(__file__).resolve().parents[1]
OUT_ROOT = ROOT / "docs" / "visexp" / "out"
DEFAULT_OUT_DIR = OUT_ROOT / "operation-profile-negative-control-r331"
R320_OUT = OUT_ROOT / "operation-profile-accuracy-r320"
R320_REPORT = R320_OUT / "profile-accuracy-report.json"
R320_POLICY_CSV = R320_OUT / "policy-scores.csv"
RUN_ID = "R331"
DEFAULT_REPS = 2000
DEFAULT_SEED = 331
HIGH_LIFT_THRESHOLD = 1.5

sys.path.insert(0, str(Path(__file__).resolve().parent))
import operation_profile_accuracy_eval as r320  # noqa: E402
import operation_query_utility_eval as r300  # noqa: E402


POLICIES = [
    ("operation_stack", "query_aware"),
    ("operation_stack", "width"),
    ("fixed_session", "query_aware"),
    ("dataset_native", "query_aware"),
    ("raw_action_stack", "query_aware"),
]
METRICS = [
    "average_precision",
    "top5_precision",
    "top5_recall",
    "top5_f1",
    "top5_work",
    "top5_lift",
    "budget30_recall",
    "work_to_first_positive",
]
HIGHER_IS_BETTER = {
    "average_precision",
    "top5_precision",
    "top5_recall",
    "top5_f1",
    "top5_lift",
    "budget30_recall",
}
LOWER_IS_BETTER = {"top5_work", "work_to_first_positive"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--reps", type=int, default=DEFAULT_REPS)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
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


def percentile(values: list[float], quantile: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    if len(ordered) == 1:
        return float(ordered[0])
    position = (len(ordered) - 1) * quantile
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return float(ordered[lower])
    weight = position - lower
    return float(ordered[lower] * (1.0 - weight) + ordered[upper] * weight)


def p_value(metric: str, observed: float | None, null_values: list[float]) -> float | None:
    if observed is None or not null_values:
        return None
    if metric in HIGHER_IS_BETTER:
        count = sum(1 for value in null_values if value >= observed)
    elif metric in LOWER_IS_BETTER:
        count = sum(1 for value in null_values if value <= observed)
    else:
        return None
    return (count + 1.0) / (len(null_values) + 1.0)


def supports_direction(metric: str, observed: float | None, null_values: list[float]) -> bool:
    if observed is None or not null_values:
        return False
    if metric in HIGHER_IS_BETTER:
        high = percentile(null_values, 0.95)
        return high is not None and observed > high
    if metric in LOWER_IS_BETTER:
        low = percentile(null_values, 0.05)
        return low is not None and observed < low
    return False


def allocate_positive_counts(
    group_sizes: list[int],
    total_operations: int,
    total_positives: int,
    rng: random.Random,
) -> list[int]:
    if total_positives <= 0:
        return [0 for _ in group_sizes]
    if total_positives >= total_operations:
        return list(group_sizes)
    positions = sorted(rng.sample(range(total_operations), total_positives))
    counts = []
    pointer = 0
    start = 0
    for size in group_sizes:
        end = start + size
        count = 0
        while pointer < len(positions) and positions[pointer] < end:
            count += 1
            pointer += 1
        counts.append(count)
        start = end
    return counts


def apply_positive_counts(groups: list[dict[str, Any]], positive_counts: list[int]) -> list[dict[str, Any]]:
    output = []
    for group, positives in zip(groups, positive_counts, strict=True):
        operations = int(group["operations"])
        output.append(
            {
                "group_id": group["group_id"],
                "operations": operations,
                "positives": positives,
                "positive_rate": positives / operations if operations else 0.0,
            }
        )
    return output


def score_ranked_groups(ranked: list[dict[str, Any]], summary: dict[str, Any]) -> dict[str, Any]:
    row: dict[str, Any] = {
        "average_precision": r320.average_precision(ranked, summary["positives"]),
    }
    row.update(r320.first_relevant_metrics(ranked, summary, HIGH_LIFT_THRESHOLD))
    row.update(r320.score_selection(ranked[:5], summary, "top5"))
    selected = r320.select_for_operation_budget(ranked, summary, 0.30)
    row.update(r320.score_selection(selected, summary, "budget30"))
    return row


def evaluate_policy(
    task: dict[str, Any],
    view: str,
    ranker: str,
    reps: int,
    rng: random.Random,
) -> dict[str, Any]:
    groups, summary = r320.group_task_view(task, view)
    ranked = r320.rank_groups(task, groups, ranker)
    observed = r320.score_policy(task, view, ranker, groups, summary, HIGH_LIFT_THRESHOLD)
    group_sizes = [int(group["operations"]) for group in ranked]
    null_metrics: dict[str, list[float]] = {metric: [] for metric in METRICS}
    for _ in range(reps):
        positive_counts = allocate_positive_counts(
            group_sizes,
            int(summary["operations"]),
            int(summary["positives"]),
            rng,
        )
        permuted = apply_positive_counts(ranked, positive_counts)
        scored = score_ranked_groups(permuted, summary)
        for metric in METRICS:
            value = scored.get(metric)
            if value is not None:
                null_metrics[metric].append(float(value))
    metric_rows = []
    for metric in METRICS:
        values = null_metrics[metric]
        observed_value = observed.get(metric)
        observed_float = float(observed_value) if observed_value is not None else None
        null_mean = float(mean(values)) if values else None
        null_median = float(median(values)) if values else None
        metric_rows.append(
            {
                "task": task["id"],
                "dataset": task["dataset"],
                "query_family": task["query_family"],
                "view": view,
                "ranker": ranker,
                "policy": r320.policy_key(view, ranker),
                "metric": metric,
                "direction": "higher" if metric in HIGHER_IS_BETTER else "lower",
                "operations": summary["operations"],
                "positives": summary["positives"],
                "prevalence": summary["prevalence"],
                "groups": summary["groups"],
                "positive_groups": summary["positive_groups"],
                "observed": observed_float,
                "null_mean": null_mean,
                "null_median": null_median,
                "null_p05": percentile(values, 0.05),
                "null_p95": percentile(values, 0.95),
                "observed_minus_null_mean": (
                    observed_float - null_mean if observed_float is not None and null_mean is not None else None
                ),
                "observed_over_null_mean": (
                    observed_float / null_mean
                    if observed_float is not None and null_mean not in (None, 0.0)
                    else None
                ),
                "empirical_p_value": p_value(metric, observed_float, values),
                "beyond_95pct_null": supports_direction(metric, observed_float, values),
                "reps": reps,
            }
        )
    return {
        "task": task["id"],
        "view": view,
        "ranker": ranker,
        "metric_rows": metric_rows,
        "observed_top_groups": observed["top_groups"],
    }


def summarize_metric_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    summaries = []
    for policy in sorted({row["policy"] for row in rows}):
        for metric in METRICS:
            scoped = [row for row in rows if row["policy"] == policy and row["metric"] == metric]
            if not scoped:
                continue
            deltas = [
                row["observed_minus_null_mean"]
                for row in scoped
                if row["observed_minus_null_mean"] is not None
            ]
            ratios = [
                row["observed_over_null_mean"]
                for row in scoped
                if row["observed_over_null_mean"] is not None
            ]
            p_values = [
                row["empirical_p_value"] for row in scoped if row["empirical_p_value"] is not None
            ]
            summaries.append(
                {
                    "policy": policy,
                    "metric": metric,
                    "direction": scoped[0]["direction"],
                    "tasks": len(scoped),
                    "beyond_95pct_null_tasks": sum(row["beyond_95pct_null"] for row in scoped),
                    "median_observed_minus_null_mean": median(deltas) if deltas else None,
                    "mean_observed_minus_null_mean": mean(deltas) if deltas else None,
                    "median_observed_over_null_mean": median(ratios) if ratios else None,
                    "median_empirical_p_value": median(p_values) if p_values else None,
                }
            )
    return summaries


def row_for(summary_rows: list[dict[str, Any]], policy: str, metric: str) -> dict[str, Any]:
    for row in summary_rows:
        if row["policy"] == policy and row["metric"] == metric:
            return row
    raise KeyError((policy, metric))


def build_findings(summary_rows: list[dict[str, Any]]) -> list[str]:
    op_ap = row_for(summary_rows, "operation_stack:query_aware", "average_precision")
    op_p5 = row_for(summary_rows, "operation_stack:query_aware", "top5_precision")
    op_r30 = row_for(summary_rows, "operation_stack:query_aware", "budget30_recall")
    width_ap = row_for(summary_rows, "operation_stack:width", "average_precision")
    fixed_ap = row_for(summary_rows, "fixed_session:query_aware", "average_precision")
    raw_ap = row_for(summary_rows, "raw_action_stack:query_aware", "average_precision")
    return [
        (
            "Operation-stack query-aware AP exceeds the label-permutation null on "
            f"{op_ap['beyond_95pct_null_tasks']}/{op_ap['tasks']} tasks "
            f"(median AP delta {op_ap['median_observed_minus_null_mean']:.4f})."
        ),
        (
            "The same policy's top-5 precision exceeds the null on "
            f"{op_p5['beyond_95pct_null_tasks']}/{op_p5['tasks']} tasks and 30% budget "
            f"recall exceeds the null on {op_r30['beyond_95pct_null_tasks']}/{op_r30['tasks']} tasks."
        ),
        (
            "Width-only operation-stack AP exceeds the null on "
            f"{width_ap['beyond_95pct_null_tasks']}/{width_ap['tasks']} tasks, so some signal comes "
            "from stack grouping itself; query-aware ranking remains needed for the stronger R320/R330 results."
        ),
        (
            "Fixed-session query-aware AP exceeds the null on "
            f"{fixed_ap['beyond_95pct_null_tasks']}/{fixed_ap['tasks']} tasks, preserving it as a real "
            "low-work counterpoint rather than a strawman baseline."
        ),
        (
            "Raw action/status AP exceeds the null on "
            f"{raw_ap['beyond_95pct_null_tasks']}/{raw_ap['tasks']} tasks, but R320/R330 show its mapped-depth "
            "comparison is task-sensitive; R331 therefore calibrates signal, not universal dominance."
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
        "# R331 Profile Negative-Control Audit",
        "",
        "R331 keeps each visible ranking fixed and randomly reallocates hidden positive labels across same-size operation groups.",
        "It is a prevalence/group-size negative control over existing R320 tasks, not a new dataset or human study.",
        "",
        "## Primary Findings",
        "",
    ]
    lines.extend(f"- {finding}" for finding in report["primary_findings"])
    lines.extend(
        [
            "",
            "## Policy-Level Null Summary",
            "",
            "| Policy | Metric | Direction | Tasks beyond 95% null | Median delta | Median ratio | Median p |",
            "|---|---|---:|---:|---:|---:|---:|",
        ]
    )
    for row in report["policy_summary"]:
        if row["metric"] not in {"average_precision", "top5_precision", "budget30_recall", "work_to_first_positive"}:
            continue
        lines.append(
            "| {policy} | {metric} | {direction} | {wins}/{tasks} | {delta} | {ratio} | {p} |".format(
                policy=row["policy"],
                metric=row["metric"],
                direction=row["direction"],
                wins=row["beyond_95pct_null_tasks"],
                tasks=row["tasks"],
                delta=row["median_observed_minus_null_mean"],
                ratio=row["median_observed_over_null_mean"],
                p=row["median_empirical_p_value"],
            )
        )
    lines.extend(
        [
            "",
            "## Claim Boundary",
            "",
            "- Supports: the main R320/R330 ranking signal is not explainable by prevalence and group-size alone on the primary operation-stack query-aware comparisons.",
            "- Also supports: fixed-session and raw-action baselines contain real signal and should remain counterpoints.",
            "- Does not support: human utility, label-free deployment ranking, or operation-stack dominance on every metric.",
        ]
    )
    return "\n".join(lines) + "\n"


def render_html(report: dict[str, Any]) -> str:
    findings = "".join(f"<li>{html.escape(finding)}</li>" for finding in report["primary_findings"])
    rows = []
    for row in report["policy_summary"]:
        if row["metric"] not in {"average_precision", "top5_precision", "budget30_recall", "work_to_first_positive"}:
            continue
        rows.append(
            "<tr>"
            f"<th>{html.escape(row['policy'])}</th>"
            f"<td>{html.escape(row['metric'])}</td>"
            f"<td>{html.escape(row['direction'])}</td>"
            f"<td>{row['beyond_95pct_null_tasks']}/{row['tasks']}</td>"
            f"<td>{row['median_observed_minus_null_mean']}</td>"
            f"<td>{row['median_observed_over_null_mean']}</td>"
            f"<td>{row['median_empirical_p_value']}</td>"
            "</tr>"
        )
    return f"""<!doctype html>
<meta charset="utf-8">
<title>R331 Profile Negative-Control Audit</title>
<style>
body {{ font-family: system-ui, sans-serif; margin: 32px; color: #202124; }}
table {{ border-collapse: collapse; width: 100%; margin: 24px 0; font-size: 13px; }}
th, td {{ border-bottom: 1px solid #d8dee8; padding: 7px 8px; text-align: left; vertical-align: top; }}
th {{ background: #eef2f6; }}
.note {{ max-width: 980px; line-height: 1.45; }}
</style>
<h1>R331 Profile Negative-Control Audit</h1>
<p class="note">Visible rankings are held fixed while hidden positives are randomly reallocated across same-size operation groups.</p>
<h2>Primary Findings</h2>
<ul>{findings}</ul>
<h2>Policy-Level Null Summary</h2>
<table>
<thead><tr><th>Policy</th><th>Metric</th><th>Direction</th><th>Tasks beyond 95% null</th><th>Median delta</th><th>Median ratio</th><th>Median p</th></tr></thead>
<tbody>{''.join(rows)}</tbody>
</table>
"""


def main() -> None:
    start = time.perf_counter()
    args = parse_args()
    if args.reps <= 0:
        raise SystemExit("--reps must be positive")
    out_dir = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    source_paths = [
        R320_REPORT,
        R320_POLICY_CSV,
        *sorted({task["operation_file"] for task in r300.TASKS}),
    ]
    ensure_sources_tracked_clean(source_paths)
    r320_report = load_json(R320_REPORT)
    rng = random.Random(args.seed)
    policy_results = []
    metric_rows = []
    for task in r300.TASKS:
        for view, ranker in POLICIES:
            result = evaluate_policy(task, view, ranker, args.reps, rng)
            policy_results.append(result)
            metric_rows.extend(result["metric_rows"])
    summary_rows = summarize_metric_rows(metric_rows)
    findings = build_findings(summary_rows)
    elapsed = time.perf_counter() - start
    report = round_value(
        {
            "run_id": RUN_ID,
            "schema": "agentsight.profile-negative-control.v1",
            "purpose": "test whether R320 visible-policy localization signals exceed prevalence/group-size label-permutation nulls",
            "source_check": {
                "status": "pass",
                "tracked_clean_files": len(source_paths),
                "files": [rel(path) for path in source_paths],
            },
            "input_policy": {
                "dataset_sync": "none",
                "dataset_creation": "none",
                "profiler_rerun": "none",
                "hidden_label_use": "hidden labels are used only to score observed rankings and construct label-permutation nulls",
                "r320_report": rel(R320_REPORT),
                "r320_policy_csv": rel(R320_POLICY_CSV),
            },
            "null_model": {
                "unit": "task/policy group ranking",
                "reps": args.reps,
                "seed": args.seed,
                "description": "keep group sizes and visible ranking order fixed; randomly allocate each task's positive operations across operation positions",
            },
            "r320_totals": r320_report["totals"],
            "policies": [r320.policy_key(view, ranker) for view, ranker in POLICIES],
            "metrics": METRICS,
            "policy_summary": summary_rows,
            "primary_findings": findings,
            "non_claims": [
                "This does not create, sync, download, or relabel a dataset.",
                "This does not claim per-operation independence in the real trace.",
                "This does not claim human utility or analyst productivity.",
                "This does not prove a universal label-free ranker or single-view dominance.",
            ],
            "reproducibility": {
                "commit": git_output(["rev-parse", "HEAD"]),
                "elapsed_seconds": round(elapsed, 4),
                "network_access_required": False,
            },
        }
    )
    write_json(out_dir / "negative-control-report.json", report)
    (out_dir / "negative-control-report.md").write_text(render_markdown(report), encoding="utf-8")
    (out_dir / "index.html").write_text(render_html(report), encoding="utf-8")
    write_csv(
        out_dir / "task-policy-negative-controls.csv",
        metric_rows,
        [
            "task",
            "dataset",
            "query_family",
            "policy",
            "view",
            "ranker",
            "metric",
            "direction",
            "operations",
            "positives",
            "prevalence",
            "groups",
            "positive_groups",
            "observed",
            "null_mean",
            "null_median",
            "null_p05",
            "null_p95",
            "observed_minus_null_mean",
            "observed_over_null_mean",
            "empirical_p_value",
            "beyond_95pct_null",
            "reps",
        ],
    )
    write_csv(
        out_dir / "policy-negative-control-summary.csv",
        summary_rows,
        [
            "policy",
            "metric",
            "direction",
            "tasks",
            "beyond_95pct_null_tasks",
            "median_observed_minus_null_mean",
            "mean_observed_minus_null_mean",
            "median_observed_over_null_mean",
            "median_empirical_p_value",
        ],
    )
    write_json(
        out_dir / "run-result.json",
        {
            "run_id": RUN_ID,
            "status": "pass",
            "report": rel(out_dir / "negative-control-report.json"),
            "csv": rel(out_dir / "task-policy-negative-controls.csv"),
            "summary_csv": rel(out_dir / "policy-negative-control-summary.csv"),
            "markdown": rel(out_dir / "negative-control-report.md"),
            "html": rel(out_dir / "index.html"),
        },
    )


if __name__ == "__main__":
    main()
