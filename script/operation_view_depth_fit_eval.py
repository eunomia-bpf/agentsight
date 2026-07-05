#!/usr/bin/env python3
"""R332: task-fit audit for view/depth selection on R320 policy scores.

This audit does not fetch, sync, or create datasets. It reuses the tracked R320
policy scores and asks whether one fixed hierarchy/ranker is enough, or whether
different labeled tasks need different operation-stack depths, baseline
hierarchies, and rankers. Hidden labels are not passed to the profiler; they are
only reused here to audit already-generated R320 localization scores.
"""

from __future__ import annotations

import argparse
import csv
import html
import json
import math
import subprocess
import time
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean, median
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OUT_ROOT = ROOT / "docs" / "visexp" / "out"
DEFAULT_OUT_DIR = OUT_ROOT / "operation-view-depth-fit-r332"
R320_OUT = OUT_ROOT / "operation-profile-accuracy-r320"
R320_REPORT = R320_OUT / "profile-accuracy-report.json"
R320_POLICY_CSV = R320_OUT / "policy-scores.csv"
RUN_ID = "R332"

DEFAULT_POLICY = ("operation_stack", "query_aware")
BASELINE_POLICIES = [
    ("flat", "width"),
    ("fixed_session", "query_aware"),
    ("dataset_native", "query_aware"),
    ("raw_action_stack", "query_aware"),
    DEFAULT_POLICY,
]
METRICS = {
    "average_precision": "higher",
    "top5_f1": "higher",
    "budget30_recall": "higher",
    "work_to_first_positive": "lower",
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


def numeric(value: str) -> float | None:
    if value == "":
        return None
    return float(value)


def policy_key(view: str, ranker: str) -> str:
    return f"{view}:{ranker}"


def load_visible_policy_rows() -> list[dict[str, Any]]:
    rows = []
    with R320_POLICY_CSV.open(encoding="utf-8", newline="") as file:
        reader = csv.DictReader(file)
        for row in reader:
            if row["uses_hidden_fields"] != "False":
                continue
            parsed: dict[str, Any] = dict(row)
            for field in [
                "operations",
                "positives",
                "prevalence",
                "groups",
                "positive_groups",
                "average_precision",
                "ndcg",
                "top5_precision",
                "top5_recall",
                "top5_f1",
                "top5_work",
                "budget30_recall",
                "budget30_f1",
                "budget30_work",
                "work_to_first_positive",
                "groups_to_50pct_recall",
                "work_to_50pct_recall",
            ]:
                parsed[field] = numeric(row[field])
            parsed["policy"] = policy_key(parsed["view"], parsed["ranker"])
            rows.append(parsed)
    return rows


def better_key(metric: str, row: dict[str, Any]) -> tuple[float, ...]:
    direction = METRICS[metric]
    value = row[metric]
    if value is None:
        return (-float("inf"),)
    if direction == "higher":
        return (value, row["average_precision"] or 0.0, -(row["top5_work"] or 0.0), -(row["groups"] or 0.0))
    return (-value, row["average_precision"] or 0.0, -(row["groups"] or 0.0))


def regret(metric: str, best_value: float | None, candidate_value: float | None) -> float | None:
    if best_value is None or candidate_value is None:
        return None
    if METRICS[metric] == "higher":
        return best_value - candidate_value
    return candidate_value - best_value


def build_task_fit_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_task: dict[str, list[dict[str, Any]]] = defaultdict(list)
    by_key = {(row["task"], row["view"], row["ranker"]): row for row in rows}
    for row in rows:
        by_task[row["task"]].append(row)
    output = []
    for task in sorted(by_task):
        task_rows = by_task[task]
        default = by_key[(task, *DEFAULT_POLICY)]
        fixed = by_key[(task, "fixed_session", "query_aware")]
        flat = by_key[(task, "flat", "width")]
        dataset_native = by_key[(task, "dataset_native", "query_aware")]
        raw_action = by_key[(task, "raw_action_stack", "query_aware")]
        for metric in METRICS:
            scoped = [row for row in task_rows if row[metric] is not None]
            best = max(scoped, key=lambda row: better_key(metric, row))
            row = {
                "task": task,
                "dataset": best["dataset"],
                "query_family": best["query_family"],
                "metric": metric,
                "direction": METRICS[metric],
                "best_policy": best["policy"],
                "best_view": best["view"],
                "best_ranker": best["ranker"],
                "best_value": best[metric],
                "default_policy": policy_key(*DEFAULT_POLICY),
                "default_value": default[metric],
                "default_regret": regret(metric, best[metric], default[metric]),
                "fixed_session_value": fixed[metric],
                "fixed_session_regret": regret(metric, best[metric], fixed[metric]),
                "flat_value": flat[metric],
                "flat_regret": regret(metric, best[metric], flat[metric]),
                "dataset_native_value": dataset_native[metric],
                "dataset_native_regret": regret(metric, best[metric], dataset_native[metric]),
                "raw_action_value": raw_action[metric],
                "raw_action_regret": regret(metric, best[metric], raw_action[metric]),
                "best_groups": best["groups"],
                "default_groups": default["groups"],
                "fixed_session_groups": fixed["groups"],
                "dataset_native_groups": dataset_native["groups"],
                "raw_action_groups": raw_action["groups"],
            }
            output.append(row)
    return output


def build_single_policy_regret(rows: list[dict[str, Any]], task_fit_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_key = {(row["task"], row["view"], row["ranker"]): row for row in rows}
    tasks = sorted({row["task"] for row in rows})
    policies = sorted({(row["view"], row["ranker"]) for row in rows})
    best_by_task_metric = {(row["task"], row["metric"]): row for row in task_fit_rows}
    output = []
    for policy in policies:
        for metric in METRICS:
            regrets = []
            best_count = 0
            for task in tasks:
                candidate = by_key[(task, *policy)]
                best = best_by_task_metric[(task, metric)]
                value = regret(metric, best["best_value"], candidate[metric])
                if value is not None:
                    regrets.append(value)
                    if abs(value) <= 1e-12:
                        best_count += 1
            output.append(
                {
                    "policy": policy_key(*policy),
                    "view": policy[0],
                    "ranker": policy[1],
                    "metric": metric,
                    "tasks": len(tasks),
                    "best_tasks": best_count,
                    "median_regret": median(regrets) if regrets else None,
                    "mean_regret": mean(regrets) if regrets else None,
                    "max_regret": max(regrets) if regrets else None,
                }
            )
    return output


def source_mean(rows: list[dict[str, Any]], policy: tuple[str, str], metric: str, target: str) -> float:
    values = [
        row[metric]
        for row in rows
        if row["task"] != target and row["view"] == policy[0] and row["ranker"] == policy[1] and row[metric] is not None
    ]
    if not values:
        return -float("inf") if METRICS[metric] == "higher" else float("inf")
    value = mean(values)
    return value if METRICS[metric] == "higher" else -value


def build_leave_task_rows(rows: list[dict[str, Any]], task_fit_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    tasks = sorted({row["task"] for row in rows})
    policies = sorted({(row["view"], row["ranker"]) for row in rows})
    by_key = {(row["task"], row["view"], row["ranker"]): row for row in rows}
    best_by_task_metric = {(row["task"], row["metric"]): row for row in task_fit_rows}
    output = []
    for task in tasks:
        for metric in METRICS:
            selected = max(policies, key=lambda policy: source_mean(rows, policy, metric, task))
            target = by_key[(task, *selected)]
            best = best_by_task_metric[(task, metric)]
            default = by_key[(task, *DEFAULT_POLICY)]
            output.append(
                {
                    "task": task,
                    "dataset": target["dataset"],
                    "query_family": target["query_family"],
                    "metric": metric,
                    "selected_policy": policy_key(*selected),
                    "selected_view": selected[0],
                    "selected_ranker": selected[1],
                    "selected_value": target[metric],
                    "best_policy": best["best_policy"],
                    "best_value": best["best_value"],
                    "selected_regret": regret(metric, best["best_value"], target[metric]),
                    "default_policy": policy_key(*DEFAULT_POLICY),
                    "default_value": default[metric],
                    "default_regret": regret(metric, best["best_value"], default[metric]),
                    "selected_beats_default": (
                        (regret(metric, best["best_value"], target[metric]) or 0.0)
                        < (regret(metric, best["best_value"], default[metric]) or 0.0)
                    ),
                    "selected_equals_best": policy_key(*selected) == best["best_policy"],
                }
            )
    return output


def build_fragmentation_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_key = {(row["task"], row["view"], row["ranker"]): row for row in rows}
    output = []
    for task in sorted({row["task"] for row in rows}):
        op = by_key[(task, *DEFAULT_POLICY)]
        fixed = by_key[(task, "fixed_session", "query_aware")]
        dataset_native = by_key[(task, "dataset_native", "query_aware")]
        raw = by_key[(task, "raw_action_stack", "query_aware")]
        output.append(
            {
                "task": task,
                "dataset": op["dataset"],
                "query_family": op["query_family"],
                "operation_stack_groups": op["groups"],
                "fixed_session_groups": fixed["groups"],
                "dataset_native_groups": dataset_native["groups"],
                "raw_action_groups": raw["groups"],
                "operation_stack_vs_fixed_group_ratio": op["groups"] / fixed["groups"] if fixed["groups"] else None,
                "operation_stack_fewer_than_fixed": op["groups"] < fixed["groups"],
                "operation_stack_vs_dataset_group_ratio": (
                    op["groups"] / dataset_native["groups"] if dataset_native["groups"] else None
                ),
                "operation_stack_vs_raw_group_ratio": op["groups"] / raw["groups"] if raw["groups"] else None,
                "operation_stack_top5_recall": op["top5_recall"],
                "fixed_session_top5_recall": fixed["top5_recall"],
                "operation_stack_work_to_first_positive": op["work_to_first_positive"],
                "fixed_session_work_to_first_positive": fixed["work_to_first_positive"],
            }
        )
    return output


def summarize(
    task_fit_rows: list[dict[str, Any]],
    single_policy_rows: list[dict[str, Any]],
    leave_task_rows: list[dict[str, Any]],
    fragmentation_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    best_view_counts = {}
    best_policy_counts = {}
    default_best_counts = {}
    for metric in METRICS:
        scoped = [row for row in task_fit_rows if row["metric"] == metric]
        best_view_counts[metric] = dict(Counter(row["best_view"] for row in scoped))
        best_policy_counts[metric] = dict(Counter(row["best_policy"] for row in scoped))
        default_best_counts[metric] = sum(row["best_policy"] == policy_key(*DEFAULT_POLICY) for row in scoped)
    source_selection = {}
    for metric in METRICS:
        scoped = [row for row in leave_task_rows if row["metric"] == metric]
        source_selection[metric] = {
            "selected_equals_best": f"{sum(row['selected_equals_best'] for row in scoped)}/{len(scoped)}",
            "selected_beats_default": f"{sum(row['selected_beats_default'] for row in scoped)}/{len(scoped)}",
            "median_selected_regret": median(row["selected_regret"] for row in scoped if row["selected_regret"] is not None),
            "median_default_regret": median(row["default_regret"] for row in scoped if row["default_regret"] is not None),
        }
    default_regret = {}
    for metric in METRICS:
        scoped = [
            row
            for row in single_policy_rows
            if row["metric"] == metric and row["policy"] == policy_key(*DEFAULT_POLICY)
        ][0]
        default_regret[metric] = {
            "best_tasks": scoped["best_tasks"],
            "median_regret": scoped["median_regret"],
            "max_regret": scoped["max_regret"],
        }
    return {
        "best_view_counts": best_view_counts,
        "best_policy_counts": best_policy_counts,
        "operation_stack_query_aware_best_tasks": default_best_counts,
        "operation_stack_query_aware_regret": default_regret,
        "fragmentation": {
            "operation_stack_fewer_groups_than_fixed_session": f"{sum(row['operation_stack_fewer_than_fixed'] for row in fragmentation_rows)}/{len(fragmentation_rows)}",
            "median_operation_stack_vs_fixed_group_ratio": median(
                row["operation_stack_vs_fixed_group_ratio"]
                for row in fragmentation_rows
                if row["operation_stack_vs_fixed_group_ratio"] is not None
            ),
        },
        "leave_task_source_selection": source_selection,
    }


def build_findings(summary: dict[str, Any]) -> list[str]:
    ap_counts = summary["best_view_counts"]["average_precision"]
    f1_counts = summary["best_view_counts"]["top5_f1"]
    recall_counts = summary["best_view_counts"]["budget30_recall"]
    wtfp_counts = summary["best_view_counts"]["work_to_first_positive"]
    return [
        (
            "Best visible AP is split across operation_stack, fixed_session, and dataset_native views "
            f"({ap_counts}); best top-5 F1 spans {f1_counts}. No single hierarchy is the best visible "
            "choice across tasks and objectives."
        ),
        (
            "operation_stack:query_aware is the best visible AP policy on "
            f"{summary['operation_stack_query_aware_best_tasks']['average_precision']}/6 tasks and best "
            f"30% budget-recall policy on {summary['operation_stack_query_aware_best_tasks']['budget30_recall']}/6 tasks, "
            "but it has large regret on side-effect and safety when another task-specific view is better."
        ),
        (
            "operation stacks reduce fragmentation relative to fixed-session query-aware on "
            f"{summary['fragmentation']['operation_stack_fewer_groups_than_fixed_session']} tasks "
            f"(median group ratio {summary['fragmentation']['median_operation_stack_vs_fixed_group_ratio']:.4f}), "
            "while fixed-session remains a first-positive counterpoint."
        ),
        (
            "Leave-task source selection does not solve view choice universally: selected-equals-best is "
            f"{summary['leave_task_source_selection']['average_precision']['selected_equals_best']} for AP and "
            f"{summary['leave_task_source_selection']['top5_f1']['selected_equals_best']} for top-5 F1. This keeps "
            "view/depth choice as a task-aware analysis knob rather than a deployed universal selector."
        ),
        (
            "The supported design implication is to expose view, stack fields, predicates, and rankers as query-time "
            "configuration over the same operations; fixed session/span trees remain baselines, not profiler abstractions."
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
        "# R332 View/Depth Task-Fit Audit",
        "",
        "R332 audits whether a fixed hierarchy is enough, using only tracked R320 visible policy scores.",
        "Hidden labels are used here only to score already-generated policies and to identify task-fit regret.",
        "",
        "## Primary Findings",
        "",
    ]
    lines.extend(f"- {finding}" for finding in report["primary_findings"])
    lines.extend(
        [
            "",
            "## Best Visible View Counts",
            "",
            "| Metric | Best views | operation_stack:query_aware best tasks |",
            "|---|---|---:|",
        ]
    )
    for metric, counts in report["summary"]["best_view_counts"].items():
        lines.append(
            f"| {metric} | {counts} | {report['summary']['operation_stack_query_aware_best_tasks'][metric]}/6 |"
        )
    lines.extend(
        [
            "",
            "## Leave-Task Source Selection",
            "",
            "| Metric | Selected equals best | Selected beats default | Median selected regret | Median default regret |",
            "|---|---:|---:|---:|---:|",
        ]
    )
    for metric, row in report["summary"]["leave_task_source_selection"].items():
        lines.append(
            f"| {metric} | {row['selected_equals_best']} | {row['selected_beats_default']} | {row['median_selected_regret']} | {row['median_default_regret']} |"
        )
    lines.extend(
        [
            "",
            "## Claim Boundary",
            "",
            "- Supports: view/depth/ranker choice is an actionable query-time configuration over the same operations.",
            "- Supports: fixed-session is a real baseline and first-positive counterpoint, while operation stacks reduce fragmentation on most tasks.",
            "- Does not support: a universal label-free selector, one default stack for every task, or operation-stack dominance on every metric.",
        ]
    )
    return "\n".join(lines) + "\n"


def render_html(report: dict[str, Any]) -> str:
    findings = "".join(f"<li>{html.escape(finding)}</li>" for finding in report["primary_findings"])
    rows = []
    for metric, counts in report["summary"]["best_view_counts"].items():
        rows.append(
            "<tr>"
            f"<th>{html.escape(metric)}</th>"
            f"<td>{html.escape(str(counts))}</td>"
            f"<td>{report['summary']['operation_stack_query_aware_best_tasks'][metric]}/6</td>"
            "</tr>"
        )
    return f"""<!doctype html>
<meta charset="utf-8">
<title>R332 View/Depth Task-Fit Audit</title>
<style>
body {{ font-family: system-ui, sans-serif; margin: 32px; color: #202124; }}
table {{ border-collapse: collapse; width: 100%; margin: 24px 0; font-size: 13px; }}
th, td {{ border-bottom: 1px solid #d8dee8; padding: 7px 8px; text-align: left; vertical-align: top; }}
th {{ background: #eef2f6; }}
.note {{ max-width: 980px; line-height: 1.45; }}
</style>
<h1>R332 View/Depth Task-Fit Audit</h1>
<p class="note">This audit reuses R320 visible policy scores to test whether fixed hierarchy is enough.</p>
<h2>Primary Findings</h2>
<ul>{findings}</ul>
<h2>Best Visible View Counts</h2>
<table>
<thead><tr><th>Metric</th><th>Best views</th><th>operation_stack:query_aware best tasks</th></tr></thead>
<tbody>{''.join(rows)}</tbody>
</table>
"""


def main() -> None:
    start = time.perf_counter()
    args = parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)
    ensure_sources_tracked_clean([R320_REPORT, R320_POLICY_CSV])
    r320_report = load_json(R320_REPORT)
    rows = load_visible_policy_rows()
    task_fit_rows = build_task_fit_rows(rows)
    single_policy_rows = build_single_policy_regret(rows, task_fit_rows)
    leave_task_rows = build_leave_task_rows(rows, task_fit_rows)
    fragmentation_rows = build_fragmentation_rows(rows)
    summary = summarize(task_fit_rows, single_policy_rows, leave_task_rows, fragmentation_rows)
    findings = build_findings(summary)
    elapsed = time.perf_counter() - start
    report = round_value(
        {
            "run_id": RUN_ID,
            "schema": "agentsight.view-depth-fit.v1",
            "purpose": "test whether view/depth/ranker choice is task-specific over the same R320 operations",
            "source_check": {
                "status": "pass",
                "tracked_clean_files": 2,
                "files": [rel(R320_REPORT), rel(R320_POLICY_CSV)],
            },
            "input_policy": {
                "dataset_sync": "none",
                "dataset_creation": "none",
                "profiler_rerun": "none",
                "hidden_label_use": "R320 hidden-label scores are reused only for offline task-fit/regret auditing",
            },
            "r320_totals": r320_report["totals"],
            "metrics": METRICS,
            "default_policy": policy_key(*DEFAULT_POLICY),
            "baseline_policies": [policy_key(*policy) for policy in BASELINE_POLICIES],
            "summary": summary,
            "primary_findings": findings,
            "non_claims": [
                "This does not create, sync, download, or relabel a dataset.",
                "This does not claim a universal label-free view selector.",
                "This does not claim operation stacks dominate every hierarchy or metric.",
                "This does not add a third profiler abstraction; views are query-time projections over operation fields.",
            ],
            "reproducibility": {
                "commit": git_output(["rev-parse", "HEAD"]),
                "elapsed_seconds": round(elapsed, 4),
                "network_access_required": False,
            },
        }
    )
    write_json(args.out_dir / "view-depth-fit-report.json", report)
    (args.out_dir / "view-depth-fit-report.md").write_text(render_markdown(report), encoding="utf-8")
    (args.out_dir / "index.html").write_text(render_html(report), encoding="utf-8")
    write_csv(
        args.out_dir / "task-fit.csv",
        task_fit_rows,
        [
            "task",
            "dataset",
            "query_family",
            "metric",
            "direction",
            "best_policy",
            "best_view",
            "best_ranker",
            "best_value",
            "default_value",
            "default_regret",
            "fixed_session_value",
            "fixed_session_regret",
            "flat_value",
            "flat_regret",
            "dataset_native_value",
            "dataset_native_regret",
            "raw_action_value",
            "raw_action_regret",
            "best_groups",
            "default_groups",
            "fixed_session_groups",
            "dataset_native_groups",
            "raw_action_groups",
        ],
    )
    write_csv(
        args.out_dir / "single-policy-regret.csv",
        single_policy_rows,
        [
            "policy",
            "view",
            "ranker",
            "metric",
            "tasks",
            "best_tasks",
            "median_regret",
            "mean_regret",
            "max_regret",
        ],
    )
    write_csv(
        args.out_dir / "leave-task-view-selection.csv",
        leave_task_rows,
        [
            "task",
            "dataset",
            "query_family",
            "metric",
            "selected_policy",
            "selected_value",
            "best_policy",
            "best_value",
            "selected_regret",
            "default_policy",
            "default_value",
            "default_regret",
            "selected_beats_default",
            "selected_equals_best",
        ],
    )
    write_csv(
        args.out_dir / "fragmentation.csv",
        fragmentation_rows,
        [
            "task",
            "dataset",
            "query_family",
            "operation_stack_groups",
            "fixed_session_groups",
            "dataset_native_groups",
            "raw_action_groups",
            "operation_stack_vs_fixed_group_ratio",
            "operation_stack_fewer_than_fixed",
            "operation_stack_vs_dataset_group_ratio",
            "operation_stack_vs_raw_group_ratio",
            "operation_stack_top5_recall",
            "fixed_session_top5_recall",
            "operation_stack_work_to_first_positive",
            "fixed_session_work_to_first_positive",
        ],
    )
    write_json(
        args.out_dir / "run-result.json",
        {
            "run_id": RUN_ID,
            "status": "pass",
            "report": rel(args.out_dir / "view-depth-fit-report.json"),
            "task_fit_csv": rel(args.out_dir / "task-fit.csv"),
            "single_policy_regret_csv": rel(args.out_dir / "single-policy-regret.csv"),
            "leave_task_selection_csv": rel(args.out_dir / "leave-task-view-selection.csv"),
            "fragmentation_csv": rel(args.out_dir / "fragmentation.csv"),
            "markdown": rel(args.out_dir / "view-depth-fit-report.md"),
            "html": rel(args.out_dir / "index.html"),
        },
    )


if __name__ == "__main__":
    main()
