#!/usr/bin/env python3
"""R330: paired-bootstrap uncertainty audit for R320 profiler accuracy.

R320 reports point estimates over six real oracle-backed analysis tasks.  R330
does not re-profile and does not fetch data.  It treats the R320 task-level
policy scores as the unit of analysis and asks whether the main paper
comparisons remain directionally stable under paired task bootstrap.
"""

from __future__ import annotations

import csv
import html
import json
import random
import subprocess
import time
from pathlib import Path
from statistics import mean, median
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OUT_ROOT = ROOT / "docs" / "visexp" / "out"
R320_DIR = OUT_ROOT / "operation-profile-accuracy-r320"
R320_REPORT = R320_DIR / "profile-accuracy-report.json"
R320_POLICY_CSV = R320_DIR / "policy-scores.csv"
DEFAULT_OUT_DIR = OUT_ROOT / "operation-profile-uncertainty-r330"
RUN_ID = "R330"
BOOTSTRAP_REPS = 10000
BOOTSTRAP_SEED = 330


PAIRED_TESTS = [
    {
        "comparison": "operation_stack_query_aware_vs_flat_width",
        "left": ("operation_stack", "query_aware"),
        "right": ("flat", "width"),
        "claim_role": "less_work_than_flat_and_better_budgeted_localization",
        "metrics": {
            "average_precision": "higher",
            "top5_work": "lower",
            "budget30_recall": "higher",
            "work_to_first_positive": "lower",
            "top5_recall": "counterpoint_lower",
        },
    },
    {
        "comparison": "operation_stack_query_aware_vs_fixed_session_query_aware",
        "left": ("operation_stack", "query_aware"),
        "right": ("fixed_session", "query_aware"),
        "claim_role": "less_fragmented_higher_top5_recall_than_fixed_session",
        "metrics": {
            "top5_recall": "higher",
            "top5_f1": "higher",
            "groups": "lower",
            "top5_work": "counterpoint_mixed",
            "work_to_first_positive": "counterpoint_mixed",
            "average_precision": "counterpoint_mixed",
        },
    },
    {
        "comparison": "operation_stack_query_aware_vs_operation_stack_width",
        "left": ("operation_stack", "query_aware"),
        "right": ("operation_stack", "width"),
        "claim_role": "query_aware_ranker_improves_width_ranked_operation_stack",
        "metrics": {
            "average_precision": "higher",
            "top5_work": "lower",
            "budget30_recall": "higher",
            "work_to_first_positive": "lower",
            "top5_f1": "counterpoint_mixed",
        },
    },
    {
        "comparison": "operation_stack_query_aware_vs_raw_action_stack_query_aware",
        "left": ("operation_stack", "query_aware"),
        "right": ("raw_action_stack", "query_aware"),
        "claim_role": "mapping_depth_is_task_sensitive",
        "metrics": {
            "average_precision": "higher",
            "budget30_recall": "higher",
            "top5_f1": "counterpoint_mixed",
            "top5_recall": "counterpoint_mixed",
        },
    },
]


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


def ensure_sources_tracked_clean(paths: list[Path]) -> dict[str, Any]:
    checked = []
    for path in sorted({item.resolve() for item in paths}):
        if not path.exists():
            raise SystemExit(f"missing source artifact {rel(path)}")
        git_check("source artifact is not git-tracked", ["ls-files", "--error-unmatch"], path)
        git_check("source artifact has unstaged changes", ["diff", "--quiet"], path)
        git_check("source artifact has staged changes", ["diff", "--cached", "--quiet"], path)
        checked.append(rel(path))
    return {"status": "pass", "tracked_clean_files": len(checked), "files": checked}


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def parse_float(value: str) -> float | None:
    if value == "" or value is None:
        return None
    return float(value)


def rounded(value: Any) -> Any:
    if isinstance(value, float):
        return round(value, 4)
    if isinstance(value, dict):
        return {key: rounded(child) for key, child in value.items()}
    if isinstance(value, list):
        return [rounded(child) for child in value]
    return value


def percentile(values: list[float], q: float) -> float:
    if not values:
        raise ValueError("empty percentile input")
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    position = (len(ordered) - 1) * q
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    fraction = position - lower
    return ordered[lower] * (1 - fraction) + ordered[upper] * fraction


def expected_direction(metric_role: str) -> str | None:
    if metric_role in {"higher", "counterpoint_higher"}:
        return "higher"
    if metric_role in {"lower", "counterpoint_lower"}:
        return "lower"
    return None


def direction_good(delta: float, direction: str) -> bool:
    return delta > 0 if direction == "higher" else delta < 0


def direction_bad(delta: float, direction: str) -> bool:
    return delta < 0 if direction == "higher" else delta > 0


def load_policy_rows() -> list[dict[str, Any]]:
    rows = []
    with R320_POLICY_CSV.open(encoding="utf-8", newline="") as file:
        reader = csv.DictReader(file)
        for row in reader:
            converted: dict[str, Any] = dict(row)
            converted["uses_hidden_fields"] = row["uses_hidden_fields"] == "True"
            for key, value in row.items():
                if key in {
                    "task",
                    "dataset",
                    "query_family",
                    "view",
                    "ranker",
                    "uses_hidden_fields",
                }:
                    continue
                converted[key] = parse_float(value)
            rows.append(converted)
    return rows


def paired_task_deltas(
    rows: list[dict[str, Any]],
    left: tuple[str, str],
    right: tuple[str, str],
    metric: str,
) -> list[dict[str, Any]]:
    by_key = {(row["task"], row["view"], row["ranker"]): row for row in rows}
    deltas = []
    for task in sorted({row["task"] for row in rows}):
        left_row = by_key.get((task, *left))
        right_row = by_key.get((task, *right))
        if not left_row or not right_row:
            continue
        left_value = left_row.get(metric)
        right_value = right_row.get(metric)
        if left_value is None or right_value is None:
            continue
        deltas.append(
            {
                "task": task,
                "dataset": left_row["dataset"],
                "query_family": left_row["query_family"],
                "left_value": float(left_value),
                "right_value": float(right_value),
                "delta": float(left_value) - float(right_value),
            }
        )
    return deltas


def bootstrap_means(deltas: list[float], reps: int, rng: random.Random) -> list[float]:
    if not deltas:
        return []
    means = []
    n = len(deltas)
    for _ in range(reps):
        means.append(sum(deltas[rng.randrange(n)] for _ in range(n)) / n)
    return means


def summarize_metric(
    rows: list[dict[str, Any]],
    comparison: dict[str, Any],
    metric: str,
    metric_role: str,
    reps: int,
    rng: random.Random,
) -> dict[str, Any]:
    task_deltas = paired_task_deltas(rows, comparison["left"], comparison["right"], metric)
    values = [row["delta"] for row in task_deltas]
    direction = expected_direction(metric_role)
    boot = bootstrap_means(values, reps, rng)
    ci_low = percentile(boot, 0.025) if boot else None
    ci_high = percentile(boot, 0.975) if boot else None
    if direction is None:
        directional_support = None
        ci_supports_direction = None
        improved_tasks = None
        worse_tasks = None
    else:
        directional_support = sum(direction_good(value, direction) for value in boot) / len(boot)
        ci_supports_direction = (
            ci_low is not None
            and ci_high is not None
            and (ci_low > 0 if direction == "higher" else ci_high < 0)
        )
        improved_tasks = sum(direction_good(value, direction) for value in values)
        worse_tasks = sum(direction_bad(value, direction) for value in values)
    return rounded(
        {
            "comparison": comparison["comparison"],
            "claim_role": comparison["claim_role"],
            "left_policy": ":".join(comparison["left"]),
            "right_policy": ":".join(comparison["right"]),
            "metric": metric,
            "metric_role": metric_role,
            "expected_direction": direction,
            "tasks": len(values),
            "observed_mean_delta": mean(values) if values else None,
            "observed_median_delta": median(values) if values else None,
            "bootstrap_reps": reps,
            "bootstrap_mean_delta_ci95": [ci_low, ci_high] if boot else None,
            "bootstrap_directional_support": directional_support,
            "ci_supports_expected_direction": ci_supports_direction,
            "improved_tasks": improved_tasks,
            "worse_tasks": worse_tasks,
            "tied_tasks": sum(value == 0 for value in values),
            "task_deltas": task_deltas,
        }
    )


def classify_findings(metric_rows: list[dict[str, Any]]) -> dict[str, Any]:
    support_rows = []
    mixed_rows = []
    for row in metric_rows:
        role = row["metric_role"]
        if role.startswith("counterpoint"):
            mixed_rows.append(row)
            continue
        if row["ci_supports_expected_direction"] or (
            row["bootstrap_directional_support"] is not None
            and row["bootstrap_directional_support"] >= 0.95
            and row["improved_tasks"] >= max(4, row["tasks"] - 1)
        ):
            support_rows.append(row)
        else:
            mixed_rows.append(row)
    return {
        "supported_metric_checks": len(support_rows),
        "mixed_or_counterpoint_metric_checks": len(mixed_rows),
        "supported": [
            {
                "comparison": row["comparison"],
                "metric": row["metric"],
                "mean_delta": row["observed_mean_delta"],
                "ci95": row["bootstrap_mean_delta_ci95"],
                "directional_support": row["bootstrap_directional_support"],
                "improved_tasks": f"{row['improved_tasks']}/{row['tasks']}",
            }
            for row in support_rows
        ],
        "mixed_or_counterpoint": [
            {
                "comparison": row["comparison"],
                "metric": row["metric"],
                "metric_role": row["metric_role"],
                "mean_delta": row["observed_mean_delta"],
                "ci95": row["bootstrap_mean_delta_ci95"],
                "directional_support": row["bootstrap_directional_support"],
                "improved_tasks": (
                    None
                    if row["improved_tasks"] is None
                    else f"{row['improved_tasks']}/{row['tasks']}"
                ),
            }
            for row in mixed_rows
        ],
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# R330 Paired-Bootstrap Uncertainty Audit",
        "",
        f"- Source R320 report: `{report['r320_report']}`",
        f"- Source R320 policy CSV: `{report['r320_policy_csv']}`",
        f"- Bootstrap repetitions: {report['bootstrap']['reps']}",
        f"- Bootstrap seed: {report['bootstrap']['seed']}",
        "",
        "## Supported Checks",
        "",
        "| Comparison | Metric | Mean delta | 95% CI | Direction support | Tasks |",
        "|---|---|---:|---|---:|---:|",
    ]
    for row in report["finding_summary"]["supported"]:
        ci = row["ci95"]
        lines.append(
            f"| {row['comparison']} | {row['metric']} | {row['mean_delta']:.4f} | "
            f"[{ci[0]:.4f}, {ci[1]:.4f}] | {row['directional_support']:.3f} | "
            f"{row['improved_tasks']} |"
        )
    lines.extend(
        [
            "",
            "## Mixed Or Counterpoint Checks",
            "",
            "| Comparison | Metric | Role | Mean delta | 95% CI | Direction support | Tasks |",
            "|---|---|---|---:|---|---:|---:|",
        ]
    )
    for row in report["finding_summary"]["mixed_or_counterpoint"]:
        ci = row["ci95"]
        support = "" if row["directional_support"] is None else f"{row['directional_support']:.3f}"
        tasks = "" if row["improved_tasks"] is None else row["improved_tasks"]
        lines.append(
            f"| {row['comparison']} | {row['metric']} | {row['metric_role']} | "
            f"{row['mean_delta']:.4f} | [{ci[0]:.4f}, {ci[1]:.4f}] | {support} | {tasks} |"
        )
    lines.extend(
        [
            "",
            "R330 bootstraps over the six R320 task families. It is an uncertainty audit over task-level policy scores, not a new dataset, human study, or per-operation independence claim.",
            "",
        ]
    )
    return "\n".join(lines)


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    fieldnames = [
        "comparison",
        "claim_role",
        "left_policy",
        "right_policy",
        "metric",
        "metric_role",
        "expected_direction",
        "tasks",
        "observed_mean_delta",
        "observed_median_delta",
        "ci95_low",
        "ci95_high",
        "bootstrap_directional_support",
        "ci_supports_expected_direction",
        "improved_tasks",
        "worse_tasks",
        "tied_tasks",
    ]
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            ci = row["bootstrap_mean_delta_ci95"] or [None, None]
            writer.writerow(
                {
                    "comparison": row["comparison"],
                    "claim_role": row["claim_role"],
                    "left_policy": row["left_policy"],
                    "right_policy": row["right_policy"],
                    "metric": row["metric"],
                    "metric_role": row["metric_role"],
                    "expected_direction": row["expected_direction"] or "",
                    "tasks": row["tasks"],
                    "observed_mean_delta": row["observed_mean_delta"],
                    "observed_median_delta": row["observed_median_delta"],
                    "ci95_low": ci[0],
                    "ci95_high": ci[1],
                    "bootstrap_directional_support": row["bootstrap_directional_support"],
                    "ci_supports_expected_direction": row["ci_supports_expected_direction"],
                    "improved_tasks": row["improved_tasks"],
                    "worse_tasks": row["worse_tasks"],
                    "tied_tasks": row["tied_tasks"],
                }
            )


def render_html(report: dict[str, Any]) -> str:
    supported = "\n".join(
        f"<tr><td>{html.escape(row['comparison'])}</td><td>{html.escape(row['metric'])}</td>"
        f"<td>{row['mean_delta']:.4f}</td><td>[{row['ci95'][0]:.4f}, {row['ci95'][1]:.4f}]</td>"
        f"<td>{row['directional_support']:.3f}</td><td>{html.escape(row['improved_tasks'])}</td></tr>"
        for row in report["finding_summary"]["supported"]
    )
    mixed = "\n".join(
        f"<tr><td>{html.escape(row['comparison'])}</td><td>{html.escape(row['metric'])}</td>"
        f"<td>{html.escape(row['metric_role'])}</td><td>{row['mean_delta']:.4f}</td>"
        f"<td>[{row['ci95'][0]:.4f}, {row['ci95'][1]:.4f}]</td></tr>"
        for row in report["finding_summary"]["mixed_or_counterpoint"]
    )
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>R330 Paired-Bootstrap Uncertainty Audit</title>
<style>
body {{ font-family: system-ui, sans-serif; margin: 32px; color: #1f2937; }}
table {{ border-collapse: collapse; width: 100%; margin: 16px 0 28px; }}
th, td {{ border-bottom: 1px solid #d1d5db; padding: 8px; text-align: right; }}
th:first-child, td:first-child, th:nth-child(2), td:nth-child(2), th:nth-child(3), td:nth-child(3) {{ text-align: left; }}
code {{ background: #f3f4f6; padding: 1px 4px; border-radius: 4px; }}
</style>
</head>
<body>
<h1>R330 Paired-Bootstrap Uncertainty Audit</h1>
<p>Input: <code>{html.escape(report['r320_policy_csv'])}</code>. Bootstrap is over six R320 task families.</p>
<h2>Supported Checks</h2>
<table><thead><tr><th>Comparison</th><th>Metric</th><th>Mean delta</th><th>95% CI</th><th>Support</th><th>Tasks</th></tr></thead><tbody>{supported}</tbody></table>
<h2>Mixed Or Counterpoint Checks</h2>
<table><thead><tr><th>Comparison</th><th>Metric</th><th>Role</th><th>Mean delta</th><th>95% CI</th></tr></thead><tbody>{mixed}</tbody></table>
</body>
</html>
"""


def main() -> None:
    start = time.perf_counter()
    out_dir = DEFAULT_OUT_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    source_check = ensure_sources_tracked_clean([R320_REPORT, R320_POLICY_CSV])
    rows = load_policy_rows()
    rng = random.Random(BOOTSTRAP_SEED)
    metric_rows = []
    for comparison in PAIRED_TESTS:
        for metric, metric_role in comparison["metrics"].items():
            metric_rows.append(
                summarize_metric(
                    rows,
                    comparison,
                    metric,
                    metric_role,
                    BOOTSTRAP_REPS,
                    rng,
                )
            )
    finding_summary = classify_findings(metric_rows)
    report = rounded(
        {
            "run_id": RUN_ID,
            "status": "pass",
            "purpose": "task-paired uncertainty audit for R320 profiler localization/ranking comparisons",
            "r320_report": rel(R320_REPORT),
            "r320_policy_csv": rel(R320_POLICY_CSV),
            "source_check": source_check,
            "bootstrap": {
                "unit": "R320 task family",
                "tasks": sorted({row["task"] for row in rows}),
                "reps": BOOTSTRAP_REPS,
                "seed": BOOTSTRAP_SEED,
                "ci": "percentile 95% interval over paired task-resampled mean deltas",
            },
            "finding_summary": finding_summary,
            "metric_rows": metric_rows,
            "claim": (
                "R330 quantifies which R320 policy comparisons are directionally "
                "stable across task-family resampling and which remain tradeoffs."
            ),
            "non_claims": [
                "This does not create, sync, or download a dataset.",
                "This does not rerun the profiler or change R320 point estimates.",
                "This is not a per-operation independence or human-utility claim.",
                "This does not claim operation stacks dominate every baseline on every metric.",
            ],
            "reproducibility": {
                "commit": git_output(["rev-parse", "HEAD"]),
                "elapsed_seconds": round(time.perf_counter() - start, 4),
            },
        }
    )
    report_path = out_dir / "uncertainty-report.json"
    csv_path = out_dir / "paired-bootstrap-summary.csv"
    markdown_path = out_dir / "uncertainty-report.md"
    html_path = out_dir / "index.html"
    write_json(report_path, report)
    write_csv(csv_path, metric_rows)
    markdown_path.write_text(render_markdown(report), encoding="utf-8")
    html_path.write_text(render_html(report), encoding="utf-8")
    write_json(
        out_dir / "run-result.json",
        {
            "status": "pass",
            "run_id": RUN_ID,
            "report": rel(report_path),
            "csv": rel(csv_path),
            "markdown": rel(markdown_path),
            "html": rel(html_path),
        },
    )


if __name__ == "__main__":
    main()
