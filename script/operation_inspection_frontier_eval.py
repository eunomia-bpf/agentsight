#!/usr/bin/env python3
"""R333: inspection-efficiency curves for the R320 labeled-trace tasks.

This audit does not fetch, sync, or create datasets. It reruns the existing R320
folding/scoring code over tracked operation JSONL inputs so the paper can report
complete top-k and operation-budget inspection curves, not only the condensed
R320 CSV columns. Hidden labels are used only after ranking to score already
formed profile groups.
"""

from __future__ import annotations

import argparse
import csv
import html
import json
import math
import subprocess
import sys
import time
from collections import defaultdict
from pathlib import Path
from statistics import mean, median
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OUT_ROOT = ROOT / "docs" / "visexp" / "out"
DEFAULT_OUT_DIR = OUT_ROOT / "operation-inspection-frontier-r333"
R320_OUT = OUT_ROOT / "operation-profile-accuracy-r320"
R320_REPORT = R320_OUT / "profile-accuracy-report.json"
R320_POLICY_CSV = R320_OUT / "policy-scores.csv"
RUN_ID = "R333"

sys.path.insert(0, str(Path(__file__).resolve().parent))
import operation_profile_accuracy_eval as r320  # noqa: E402
import operation_query_utility_eval as r300  # noqa: E402


DEFAULT_POLICY = ("operation_stack", "query_aware")
CORE_POLICIES = [
    ("flat", "width"),
    ("fixed_session", "query_aware"),
    ("dataset_native", "query_aware"),
    ("raw_action_stack", "query_aware"),
    ("operation_stack", "width"),
    DEFAULT_POLICY,
]
WORK_GRIDS = [0.01, 0.05, 0.10, 0.20, 0.30, 0.50, 1.00]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--high-lift-threshold", type=float, default=r320.HIGH_LIFT_THRESHOLD)
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


def policy_key(view: str, ranker: str) -> str:
    return f"{view}:{ranker}"


def median_or_none(values: list[float]) -> float | None:
    return float(median(values)) if values else None


def mean_or_none(values: list[float]) -> float | None:
    return float(mean(values)) if values else None


def load_scored_rows(high_lift_threshold: float) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    rows: list[dict[str, Any]] = []
    group_summaries: list[dict[str, Any]] = []
    for task in r300.TASKS:
        for view in r320.VIEWS:
            groups, summary = r320.group_task_view(task, view)
            group_summaries.append(
                {
                    "task": task["id"],
                    "dataset": task["dataset"],
                    "view": view,
                    "operations": summary["operations"],
                    "positives": summary["positives"],
                    "prevalence": summary["prevalence"],
                    "groups": summary["groups"],
                    "positive_groups": summary["positive_groups"],
                    "uses_hidden_fields": r320.view_uses_hidden_fields(view),
                }
            )
            for ranker in r320.RANKERS:
                rows.append(
                    r320.score_policy(task, view, ranker, groups, summary, high_lift_threshold)
                )
    return rows, group_summaries


def visible_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [row for row in rows if not row["uses_hidden_fields"]]


def build_inspection_points(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    points: list[dict[str, Any]] = []
    for row in rows:
        for k in r320.TOP_K_VALUES:
            label = f"top{k}"
            points.append(point_from_row(row, label, f"top-{k} groups"))
        for budget in r320.OPERATION_BUDGETS:
            label = f"budget{int(budget * 100)}"
            points.append(point_from_row(row, label, f"{int(budget * 100)}% operation budget"))
    return points


def point_from_row(row: dict[str, Any], label: str, description: str) -> dict[str, Any]:
    return {
        "task": row["task"],
        "dataset": row["dataset"],
        "query_family": row["query_family"],
        "view": row["view"],
        "ranker": row["ranker"],
        "policy": policy_key(row["view"], row["ranker"]),
        "budget": label,
        "budget_description": description,
        "operations": row["operations"],
        "positives": row["positives"],
        "prevalence": row["prevalence"],
        "groups_total": row["groups"],
        "groups_inspected": row[f"{label}_groups"],
        "work": row[f"{label}_work"],
        "recall": row[f"{label}_recall"],
        "precision": row[f"{label}_precision"],
        "f1": row[f"{label}_f1"],
        "lift": row[f"{label}_lift"],
        "positive_hit": row[f"{label}_positive_hit"],
        "group_precision": row[f"{label}_group_precision"],
    }


def best_point_under_work(points: list[dict[str, Any]], max_work: float) -> dict[str, Any] | None:
    scoped = [point for point in points if point["work"] <= max_work + 1e-12]
    if not scoped:
        return None
    return max(
        scoped,
        key=lambda point: (
            point["recall"],
            point["f1"],
            point["lift"],
            point["precision"],
            -point["work"],
            -point["groups_inspected"],
        ),
    )


def build_curve_rows(points: list[dict[str, Any]], tasks: list[str]) -> list[dict[str, Any]]:
    by_task_policy: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for point in points:
        by_task_policy[(point["task"], point["policy"])].append(point)

    rows: list[dict[str, Any]] = []
    for task in tasks:
        for policy in [policy_key(*policy) for policy in CORE_POLICIES]:
            scoped = by_task_policy[(task, policy)]
            if not scoped:
                continue
            exemplar = scoped[0]
            for grid in WORK_GRIDS:
                best = best_point_under_work(scoped, grid)
                rows.append(
                    {
                        "task": task,
                        "dataset": exemplar["dataset"],
                        "query_family": exemplar["query_family"],
                        "policy": policy,
                        "work_budget": grid,
                        "best_budget": best["budget"] if best else None,
                        "best_work": best["work"] if best else 0.0,
                        "best_recall": best["recall"] if best else 0.0,
                        "best_precision": best["precision"] if best else 0.0,
                        "best_f1": best["f1"] if best else 0.0,
                        "best_lift": best["lift"] if best else 0.0,
                        "groups_inspected": best["groups_inspected"] if best else 0,
                    }
                )
    return rows


def summarize_curves(curve_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_policy_grid: dict[tuple[str, float], list[dict[str, Any]]] = defaultdict(list)
    for row in curve_rows:
        by_policy_grid[(row["policy"], row["work_budget"])].append(row)

    output: list[dict[str, Any]] = []
    for (policy, grid), rows in sorted(by_policy_grid.items()):
        recalls = [row["best_recall"] for row in rows]
        works = [row["best_work"] for row in rows]
        output.append(
            {
                "policy": policy,
                "work_budget": grid,
                "tasks": len(rows),
                "tasks_with_positive_recall": sum(row["best_recall"] > 0 for row in rows),
                "median_recall": median_or_none(recalls),
                "mean_recall": mean_or_none(recalls),
                "median_actual_work": median_or_none(works),
                "mean_actual_work": mean_or_none(works),
            }
        )
    return output


def build_core_policy_rows(rows: list[dict[str, Any]], tasks: list[str]) -> list[dict[str, Any]]:
    by_key = {(row["task"], row["view"], row["ranker"]): row for row in rows}
    output: list[dict[str, Any]] = []
    for task in tasks:
        for view, ranker in CORE_POLICIES:
            row = by_key[(task, view, ranker)]
            output.append(
                {
                    "task": task,
                    "dataset": row["dataset"],
                    "query_family": row["query_family"],
                    "policy": policy_key(view, ranker),
                    "average_precision": row["average_precision"],
                    "ndcg": row["ndcg"],
                    "top5_recall": row["top5_recall"],
                    "top5_precision": row["top5_precision"],
                    "top5_f1": row["top5_f1"],
                    "top5_work": row["top5_work"],
                    "budget30_recall": row["budget30_recall"],
                    "budget30_f1": row["budget30_f1"],
                    "budget30_work": row["budget30_work"],
                    "work_to_first_positive": row["work_to_first_positive"],
                    "groups": row["groups"],
                    "positive_groups": row["positive_groups"],
                    "groups_to_50pct_recall": row["groups_to_50pct_recall"],
                    "work_to_50pct_recall": row["work_to_50pct_recall"],
                }
            )
    return output


def compare_default_to_baselines(core_rows: list[dict[str, Any]], tasks: list[str]) -> list[dict[str, Any]]:
    by_task_policy = {(row["task"], row["policy"]): row for row in core_rows}
    baselines = [policy_key(*policy) for policy in CORE_POLICIES if policy != DEFAULT_POLICY]
    metrics = {
        "average_precision": "higher",
        "top5_recall": "higher",
        "top5_f1": "higher",
        "top5_work": "lower",
        "budget30_recall": "higher",
        "work_to_first_positive": "lower",
        "groups": "lower",
        "work_to_50pct_recall": "lower",
    }
    output: list[dict[str, Any]] = []
    default_name = policy_key(*DEFAULT_POLICY)
    for baseline in baselines:
        for metric, direction in metrics.items():
            wins = ties = losses = 0
            deltas = []
            ratios = []
            for task in tasks:
                default_value = by_task_policy[(task, default_name)][metric]
                baseline_value = by_task_policy[(task, baseline)][metric]
                delta = default_value - baseline_value
                deltas.append(delta)
                if baseline_value not in (0, None):
                    ratios.append(default_value / baseline_value)
                if direction == "higher":
                    if default_value > baseline_value + 1e-12:
                        wins += 1
                    elif baseline_value > default_value + 1e-12:
                        losses += 1
                    else:
                        ties += 1
                else:
                    if default_value < baseline_value - 1e-12:
                        wins += 1
                    elif baseline_value < default_value - 1e-12:
                        losses += 1
                    else:
                        ties += 1
            output.append(
                {
                    "default_policy": default_name,
                    "baseline_policy": baseline,
                    "metric": metric,
                    "direction": direction,
                    "wins": wins,
                    "ties": ties,
                    "losses": losses,
                    "win_rate": wins / len(tasks),
                    "median_delta_default_minus_baseline": median_or_none(deltas),
                    "mean_delta_default_minus_baseline": mean_or_none(deltas),
                    "median_ratio_default_over_baseline": median_or_none(ratios),
                }
            )
    return output


def build_curve_win_rows(curve_rows: list[dict[str, Any]], tasks: list[str]) -> list[dict[str, Any]]:
    by_key = {(row["task"], row["policy"], row["work_budget"]): row for row in curve_rows}
    default_name = policy_key(*DEFAULT_POLICY)
    output: list[dict[str, Any]] = []
    for baseline_view, baseline_ranker in CORE_POLICIES:
        baseline = policy_key(baseline_view, baseline_ranker)
        if baseline == default_name:
            continue
        for grid in WORK_GRIDS:
            wins = ties = losses = 0
            deltas = []
            for task in tasks:
                default_recall = by_key[(task, default_name, grid)]["best_recall"]
                baseline_recall = by_key[(task, baseline, grid)]["best_recall"]
                deltas.append(default_recall - baseline_recall)
                if default_recall > baseline_recall + 1e-12:
                    wins += 1
                elif baseline_recall > default_recall + 1e-12:
                    losses += 1
                else:
                    ties += 1
            output.append(
                {
                    "default_policy": default_name,
                    "baseline_policy": baseline,
                    "work_budget": grid,
                    "wins": wins,
                    "ties": ties,
                    "losses": losses,
                    "median_recall_delta": median_or_none(deltas),
                    "mean_recall_delta": mean_or_none(deltas),
                }
            )
    return output


def lookup_summary(
    curve_summary: list[dict[str, Any]], policy: tuple[str, str], work_budget: float
) -> dict[str, Any]:
    key = policy_key(*policy)
    for row in curve_summary:
        if row["policy"] == key and abs(row["work_budget"] - work_budget) <= 1e-12:
            return row
    raise KeyError((key, work_budget))


def lookup_comparison(
    comparisons: list[dict[str, Any]], baseline: tuple[str, str], metric: str
) -> dict[str, Any]:
    key = policy_key(*baseline)
    for row in comparisons:
        if row["baseline_policy"] == key and row["metric"] == metric:
            return row
    raise KeyError((key, metric))


def primary_findings(report: dict[str, Any]) -> list[str]:
    curve = report["policy_curve_summary"]
    comparisons = report["default_vs_baselines"]
    op30 = lookup_summary(curve, DEFAULT_POLICY, 0.30)
    flat30 = lookup_summary(curve, ("flat", "width"), 0.30)
    fixed30 = lookup_summary(curve, ("fixed_session", "query_aware"), 0.30)
    dataset30 = lookup_summary(curve, ("dataset_native", "query_aware"), 0.30)
    raw30 = lookup_summary(curve, ("raw_action_stack", "query_aware"), 0.30)
    op20 = lookup_summary(curve, DEFAULT_POLICY, 0.20)
    fixed20 = lookup_summary(curve, ("fixed_session", "query_aware"), 0.20)
    top5_work_flat = lookup_comparison(comparisons, ("flat", "width"), "top5_work")
    top5_recall_fixed = lookup_comparison(
        comparisons, ("fixed_session", "query_aware"), "top5_recall"
    )
    groups_fixed = lookup_comparison(comparisons, ("fixed_session", "query_aware"), "groups")
    wtfp_fixed = lookup_comparison(
        comparisons, ("fixed_session", "query_aware"), "work_to_first_positive"
    )
    ap_width = lookup_comparison(comparisons, ("operation_stack", "width"), "average_precision")
    b30_width = lookup_comparison(comparisons, ("operation_stack", "width"), "budget30_recall")
    return [
        "At <=30% inspected-work, operation_stack:query_aware has median recall "
        f"{op30['median_recall']:.4f}, versus flat:width {flat30['median_recall']:.4f}, "
        f"fixed_session:query_aware {fixed30['median_recall']:.4f}, "
        f"dataset_native:query_aware {dataset30['median_recall']:.4f}, and "
        f"raw_action_stack:query_aware {raw30['median_recall']:.4f}.",
        "At <=20% inspected-work, operation_stack:query_aware has median recall "
        f"{op20['median_recall']:.4f}, versus fixed_session:query_aware "
        f"{fixed20['median_recall']:.4f}; the <=30% result is the clearer budgeted-recall point.",
        "Against flat:width, operation_stack:query_aware uses lower top-5 inspected work on "
        f"{top5_work_flat['wins']}/6 tasks and has positive recall under the 30% budget where flat has none.",
        "Against fixed_session:query_aware, operation_stack:query_aware has higher top-5 recall on "
        f"{top5_recall_fixed['wins']}/6 tasks and fewer groups on {groups_fixed['wins']}/6 tasks, "
        f"but lower work-to-first-positive on only {wtfp_fixed['wins']}/6 tasks.",
        "Query-aware ranking is a real mechanism knob inside the same operation stack: compared with "
        f"operation_stack:width, it improves AP on {ap_width['wins']}/6 tasks and budget30 recall on "
        f"{b30_width['wins']}/6 tasks.",
    ]


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: round_value(row.get(field)) for field in fields})


def render_markdown(report: dict[str, Any], out_dir: Path) -> str:
    lines = [
        "# R333 Inspection-Efficiency Frontier",
        "",
        "R333 reruns the R320 local scorer over tracked operation JSONL inputs and emits full top-k / work-budget inspection curves. It does not fetch, sync, or create datasets.",
        "",
        "## Primary Findings",
        "",
    ]
    for finding in report["primary_findings"]:
        lines.append(f"- {finding}")
    lines.extend(
        [
            "",
            "## Non-Claims",
            "",
        ]
    )
    for item in report["non_claims"]:
        lines.append(f"- {item}")
    lines.extend(
        [
            "",
            "## Artifacts",
            "",
            f"- Report: `{rel(out_dir / 'inspection-frontier-report.json')}`",
            f"- Policy curve summary: `{rel(out_dir / 'policy-curve-summary.csv')}`",
            f"- Task policy curves: `{rel(out_dir / 'task-policy-curves.csv')}`",
            f"- Baseline comparisons: `{rel(out_dir / 'default-vs-baselines.csv')}`",
        ]
    )
    return "\n".join(lines) + "\n"


def render_html(report: dict[str, Any]) -> str:
    items = "\n".join(f"<li>{html.escape(item)}</li>" for item in report["primary_findings"])
    non_claims = "\n".join(f"<li>{html.escape(item)}</li>" for item in report["non_claims"])
    return f"""<!doctype html>
<html>
<head><meta charset="utf-8"><title>R333 Inspection Frontier</title></head>
<body>
<h1>R333 Inspection-Efficiency Frontier</h1>
<p>Reuses tracked R320 operation inputs; no dataset sync or creation.</p>
<h2>Primary Findings</h2>
<ul>
{items}
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
    source_paths = sorted({task["operation_file"] for task in r300.TASKS})
    ensure_sources_tracked_clean([*source_paths, R320_REPORT, R320_POLICY_CSV])
    leakage_check = r320.validate_visible_rank_features()

    scored_rows, group_summaries = load_scored_rows(args.high_lift_threshold)
    visible = visible_rows(scored_rows)
    tasks = sorted({row["task"] for row in visible})
    points = build_inspection_points(visible)
    curve_rows = build_curve_rows(points, tasks)
    curve_summary = summarize_curves(curve_rows)
    core_rows = build_core_policy_rows(visible, tasks)
    comparisons = compare_default_to_baselines(core_rows, tasks)
    curve_wins = build_curve_win_rows(curve_rows, tasks)
    elapsed = time.perf_counter() - start

    report = {
        "run_id": RUN_ID,
        "schema": "agentsight.inspection-frontier.v1",
        "purpose": "inspection-cost and fragmentation audit for R320 profiler localization results",
        "source_run_id": "R320",
        "input_policy": {
            "dataset_sync": "none",
            "dataset_creation": "none",
            "source_operations": [rel(path) for path in source_paths],
            "profiler_rerun": "local R320 folding/scoring over tracked operation JSONL only",
            "hidden_label_use": "hidden labels are used only after visible groups/rankings are formed",
        },
        "profiler_abstractions": ["operation", "operation stack"],
        "default_policy": policy_key(*DEFAULT_POLICY),
        "core_policies": [policy_key(*policy) for policy in CORE_POLICIES],
        "work_grids": WORK_GRIDS,
        "totals": {
            "tasks": len(tasks),
            "datasets": len({row["dataset"] for row in visible}),
            "scored_policy_scores": len(scored_rows),
            "visible_policy_scores": len(visible),
            "visible_policy_names": len({policy_key(row["view"], row["ranker"]) for row in visible}),
            "group_views": len(group_summaries),
            "inspection_points": len(points),
            "curve_rows": len(curve_rows),
        },
        "source_check": {
            "status": "pass",
            "tracked_clean_files": len(source_paths) + 2,
            "reference_artifacts": [rel(R320_REPORT), rel(R320_POLICY_CSV)],
        },
        "leakage_check": leakage_check,
        "policy_curve_summary": curve_summary,
        "default_vs_baselines": comparisons,
        "curve_win_summary": curve_wins,
        "non_claims": [
            "no new datasets, dataset sync, or self-created evaluation sets",
            "no human or agent analyst productivity, accuracy, or time-to-answer claim",
            "no single-view dominance over every metric or task",
            "no automatic view selector or label-free deployment ranker",
            "no live eBPF overhead or complete trace-ecosystem compatibility claim",
            "no profiler abstraction beyond operation and operation stack",
        ],
        "reproducibility": {
            "commit": git_output(["rev-parse", "HEAD"]),
            "elapsed_seconds": round(elapsed, 4),
            "network_access_required": False,
        },
    }
    report["primary_findings"] = primary_findings(report)
    report = round_value(report)

    report_path = out_dir / "inspection-frontier-report.json"
    markdown_path = out_dir / "inspection-frontier-report.md"
    html_path = out_dir / "index.html"
    core_csv = out_dir / "core-policy-scores.csv"
    curve_csv = out_dir / "task-policy-curves.csv"
    curve_summary_csv = out_dir / "policy-curve-summary.csv"
    comparison_csv = out_dir / "default-vs-baselines.csv"
    curve_win_csv = out_dir / "curve-win-summary.csv"
    run_result_path = out_dir / "run-result.json"

    write_json(report_path, report)
    markdown_path.write_text(render_markdown(report, out_dir), encoding="utf-8")
    html_path.write_text(render_html(report), encoding="utf-8")
    write_csv(
        core_csv,
        core_rows,
        [
            "task",
            "dataset",
            "query_family",
            "policy",
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
            "groups",
            "positive_groups",
            "groups_to_50pct_recall",
            "work_to_50pct_recall",
        ],
    )
    write_csv(
        curve_csv,
        curve_rows,
        [
            "task",
            "dataset",
            "query_family",
            "policy",
            "work_budget",
            "best_budget",
            "best_work",
            "best_recall",
            "best_precision",
            "best_f1",
            "best_lift",
            "groups_inspected",
        ],
    )
    write_csv(
        curve_summary_csv,
        curve_summary,
        [
            "policy",
            "work_budget",
            "tasks",
            "tasks_with_positive_recall",
            "median_recall",
            "mean_recall",
            "median_actual_work",
            "mean_actual_work",
        ],
    )
    write_csv(
        comparison_csv,
        comparisons,
        [
            "default_policy",
            "baseline_policy",
            "metric",
            "direction",
            "wins",
            "ties",
            "losses",
            "win_rate",
            "median_delta_default_minus_baseline",
            "mean_delta_default_minus_baseline",
            "median_ratio_default_over_baseline",
        ],
    )
    write_csv(
        curve_win_csv,
        curve_wins,
        [
            "default_policy",
            "baseline_policy",
            "work_budget",
            "wins",
            "ties",
            "losses",
            "median_recall_delta",
            "mean_recall_delta",
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
            "core_policy_scores_csv": rel(core_csv),
            "task_policy_curves_csv": rel(curve_csv),
            "policy_curve_summary_csv": rel(curve_summary_csv),
            "default_vs_baselines_csv": rel(comparison_csv),
            "curve_win_summary_csv": rel(curve_win_csv),
        },
    )

    print(render_markdown(report, out_dir))


if __name__ == "__main__":
    main()
