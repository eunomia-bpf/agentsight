#!/usr/bin/env python3
"""R337: inspection-target cost audit over existing labeled-trace profiles.

This audit reuses tracked R333 inspection curves and R336 actionability
recommendations. It asks how much operation work and how many profile groups a
visible policy needs to reach fixed positive-recall targets. No datasets are
fetched, synced, created, or relabeled.
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
R333_OUT = OUT_ROOT / "operation-inspection-frontier-r333"
R333_REPORT = R333_OUT / "inspection-frontier-report.json"
R333_CORE_CSV = R333_OUT / "core-policy-scores.csv"
R333_CURVES_CSV = R333_OUT / "task-policy-curves.csv"
R336_OUT = OUT_ROOT / "operation-actionability-selection-r336"
R336_REPORT = R336_OUT / "actionability-selection-report.json"
R336_RECOMMENDATIONS_CSV = R336_OUT / "objective-recommendations.csv"
DEFAULT_OUT_DIR = OUT_ROOT / "operation-inspection-target-r337"
RUN_ID = "R337"

DEFAULT_POLICY = "operation_stack:query_aware"
BASELINE_POLICIES = [
    "flat:width",
    "fixed_session:query_aware",
    "dataset_native:query_aware",
    "raw_action_stack:query_aware",
    "operation_stack:width",
]
RECALL_TARGETS = [0.10, 0.25, 0.50]


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


def ensure_sources_tracked_clean(paths: list[Path]) -> dict[str, str]:
    statuses: dict[str, str] = {}
    for path in paths:
        if not path.exists():
            raise SystemExit(f"missing source artifact {rel(path)}")
        git_check("source artifact is not git-tracked", ["ls-files", "--error-unmatch"], path)
        git_check("source artifact has unstaged changes", ["diff", "--quiet"], path)
        git_check("source artifact has staged changes", ["diff", "--cached", "--quiet"], path)
        statuses[rel(path)] = "tracked_clean"
    return statuses


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as file:
        return list(csv.DictReader(file))


def as_float(value: Any, default: float = 0.0) -> float:
    if value in ("", None):
        return default
    return float(value)


def median_or_none(values: list[float]) -> float | None:
    return float(median(values)) if values else None


def mean_or_none(values: list[float]) -> float | None:
    return float(mean(values)) if values else None


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


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: round_value(row.get(field)) for field in fields})


def task_actions(recommendations: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    actions: dict[str, dict[str, str]] = {}
    for row in recommendations:
        task = row["task"]
        actions.setdefault(
            task,
            {
                "dataset": row["dataset"],
                "query_family": row["query_family"],
                "optimization_action": row["optimization_action"],
                "useful_stack_fields": row["useful_stack_fields"],
                "counterpoints": row["counterpoints"],
            },
        )
    return actions


def build_target_rows(
    curves: list[dict[str, str]], recommendations: dict[str, dict[str, str]]
) -> list[dict[str, Any]]:
    by_task_policy: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in curves:
        by_task_policy[(row["task"], row["policy"])].append(row)

    output: list[dict[str, Any]] = []
    for (task, policy), rows in sorted(by_task_policy.items()):
        exemplar = rows[0]
        action = recommendations.get(task, {})
        for target in RECALL_TARGETS:
            candidates = [
                row for row in rows if as_float(row["best_recall"]) >= target - 1e-12
            ]
            if candidates:
                best = min(
                    candidates,
                    key=lambda row: (
                        as_float(row["best_work"]),
                        as_float(row["groups_inspected"]),
                        -as_float(row["best_recall"]),
                    ),
                )
                reached = True
                best_work = as_float(best["best_work"])
                groups = int(as_float(best["groups_inspected"]))
                recall = as_float(best["best_recall"])
                precision = as_float(best["best_precision"])
                f1 = as_float(best["best_f1"])
                budget = best["best_budget"]
            else:
                reached = False
                best = max(rows, key=lambda row: as_float(row["best_recall"]))
                best_work = None
                groups = None
                recall = as_float(best["best_recall"])
                precision = as_float(best["best_precision"])
                f1 = as_float(best["best_f1"])
                budget = None
            output.append(
                {
                    "task": task,
                    "dataset": exemplar["dataset"],
                    "query_family": exemplar["query_family"],
                    "policy": policy,
                    "target_recall": target,
                    "reached": reached,
                    "min_work": best_work,
                    "groups_inspected": groups,
                    "achieved_recall": recall,
                    "precision_at_target": precision,
                    "f1_at_target": f1,
                    "selected_budget": budget,
                    "optimization_action": action.get("optimization_action", ""),
                    "useful_stack_fields": action.get("useful_stack_fields", ""),
                    "counterpoints": action.get("counterpoints", ""),
                }
            )
    return output


def summarize_targets(target_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, float], list[dict[str, Any]]] = defaultdict(list)
    for row in target_rows:
        grouped[(row["policy"], row["target_recall"])].append(row)

    output: list[dict[str, Any]] = []
    for (policy, target), rows in sorted(grouped.items()):
        reached = [row for row in rows if row["reached"]]
        output.append(
            {
                "policy": policy,
                "target_recall": target,
                "tasks": len(rows),
                "tasks_reached": len(reached),
                "median_min_work": median_or_none([row["min_work"] for row in reached]),
                "mean_min_work": mean_or_none([row["min_work"] for row in reached]),
                "median_groups_inspected": median_or_none(
                    [row["groups_inspected"] for row in reached]
                ),
                "mean_groups_inspected": mean_or_none(
                    [row["groups_inspected"] for row in reached]
                ),
                "median_achieved_recall": median_or_none(
                    [row["achieved_recall"] for row in reached]
                ),
                "unreached_tasks": "; ".join(row["task"] for row in rows if not row["reached"]),
            }
        )
    return output


def build_task_best_rows(target_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, float], list[dict[str, Any]]] = defaultdict(list)
    for row in target_rows:
        grouped[(row["task"], row["target_recall"])].append(row)

    output: list[dict[str, Any]] = []
    for (task, target), rows in sorted(grouped.items()):
        reached = [row for row in rows if row["reached"]]
        exemplar = rows[0]
        if not reached:
            output.append(
                {
                    "task": task,
                    "dataset": exemplar["dataset"],
                    "query_family": exemplar["query_family"],
                    "target_recall": target,
                    "best_work_policy": "",
                    "best_work": None,
                    "best_work_groups": None,
                    "best_group_policy": "",
                    "best_groups": None,
                    "best_group_work": None,
                    "policies_reached": 0,
                    "default_reached": False,
                    "default_work": None,
                    "default_groups": None,
                    "optimization_action": exemplar["optimization_action"],
                }
            )
            continue
        best_work = min(
            reached,
            key=lambda row: (
                row["min_work"],
                row["groups_inspected"],
                -row["achieved_recall"],
                row["policy"],
            ),
        )
        best_groups = min(
            reached,
            key=lambda row: (
                row["groups_inspected"],
                row["min_work"],
                -row["achieved_recall"],
                row["policy"],
            ),
        )
        default = next(row for row in rows if row["policy"] == DEFAULT_POLICY)
        output.append(
            {
                "task": task,
                "dataset": exemplar["dataset"],
                "query_family": exemplar["query_family"],
                "target_recall": target,
                "best_work_policy": best_work["policy"],
                "best_work": best_work["min_work"],
                "best_work_groups": best_work["groups_inspected"],
                "best_group_policy": best_groups["policy"],
                "best_groups": best_groups["groups_inspected"],
                "best_group_work": best_groups["min_work"],
                "policies_reached": len(reached),
                "default_reached": default["reached"],
                "default_work": default["min_work"],
                "default_groups": default["groups_inspected"],
                "optimization_action": exemplar["optimization_action"],
            }
        )
    return output


def compare_default(target_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_key = {
        (row["task"], row["policy"], row["target_recall"]): row for row in target_rows
    }
    tasks = sorted({row["task"] for row in target_rows})
    output: list[dict[str, Any]] = []
    for baseline in BASELINE_POLICIES:
        for target in RECALL_TARGETS:
            reach_wins = reach_ties = reach_losses = 0
            work_wins = work_ties = work_losses = 0
            group_wins = group_ties = group_losses = 0
            work_deltas = []
            group_deltas = []
            for task in tasks:
                default = by_key[(task, DEFAULT_POLICY, target)]
                other = by_key[(task, baseline, target)]
                if default["reached"] and not other["reached"]:
                    reach_wins += 1
                    work_wins += 1
                    group_wins += 1
                    continue
                if other["reached"] and not default["reached"]:
                    reach_losses += 1
                    work_losses += 1
                    group_losses += 1
                    continue
                if not default["reached"] and not other["reached"]:
                    reach_ties += 1
                    work_ties += 1
                    group_ties += 1
                    continue
                reach_ties += 1
                work_delta = default["min_work"] - other["min_work"]
                group_delta = default["groups_inspected"] - other["groups_inspected"]
                work_deltas.append(work_delta)
                group_deltas.append(float(group_delta))
                if default["min_work"] < other["min_work"] - 1e-12:
                    work_wins += 1
                elif other["min_work"] < default["min_work"] - 1e-12:
                    work_losses += 1
                else:
                    work_ties += 1
                if default["groups_inspected"] < other["groups_inspected"]:
                    group_wins += 1
                elif other["groups_inspected"] < default["groups_inspected"]:
                    group_losses += 1
                else:
                    group_ties += 1
            output.append(
                {
                    "default_policy": DEFAULT_POLICY,
                    "baseline_policy": baseline,
                    "target_recall": target,
                    "reach_wins": reach_wins,
                    "reach_ties": reach_ties,
                    "reach_losses": reach_losses,
                    "work_wins": work_wins,
                    "work_ties": work_ties,
                    "work_losses": work_losses,
                    "group_wins": group_wins,
                    "group_ties": group_ties,
                    "group_losses": group_losses,
                    "median_work_delta_default_minus_baseline": median_or_none(work_deltas),
                    "median_group_delta_default_minus_baseline": median_or_none(group_deltas),
                }
            )
    return output


def policy_summary_lookup(summary: list[dict[str, Any]]) -> dict[tuple[str, float], dict[str, Any]]:
    return {(row["policy"], row["target_recall"]): row for row in summary}


def comparison_lookup(rows: list[dict[str, Any]]) -> dict[tuple[str, float], dict[str, Any]]:
    return {(row["baseline_policy"], row["target_recall"]): row for row in rows}


def summarize(
    r333: dict[str, Any],
    r336: dict[str, Any],
    target_rows: list[dict[str, Any]],
    target_summary: list[dict[str, Any]],
    task_best: list[dict[str, Any]],
    comparisons: list[dict[str, Any]],
) -> dict[str, Any]:
    lookup = policy_summary_lookup(target_summary)
    comp = comparison_lookup(comparisons)
    best_work_counts = {
        str(target): dict(
            Counter(
                row["best_work_policy"]
                for row in task_best
                if row["target_recall"] == target and row["best_work_policy"]
            )
        )
        for target in RECALL_TARGETS
    }
    best_group_counts = {
        str(target): dict(
            Counter(
                row["best_group_policy"]
                for row in task_best
                if row["target_recall"] == target and row["best_group_policy"]
            )
        )
        for target in RECALL_TARGETS
    }
    op25 = lookup[(DEFAULT_POLICY, 0.25)]
    flat25 = lookup[("flat:width", 0.25)]
    fixed25 = lookup[("fixed_session:query_aware", 0.25)]
    op10 = lookup[(DEFAULT_POLICY, 0.10)]
    fixed10 = lookup[("fixed_session:query_aware", 0.10)]
    op50 = lookup[(DEFAULT_POLICY, 0.50)]
    return {
        "tasks": r333["totals"]["tasks"],
        "datasets": r333["totals"]["datasets"],
        "policies": len({row["policy"] for row in target_rows}),
        "recall_targets": RECALL_TARGETS,
        "target_rows": len(target_rows),
        "task_best_rows": len(task_best),
        "source_run_totals": {"R333": r333.get("totals"), "R336": r336.get("summary")},
        "operation_stack_query_aware": {
            "target10_tasks_reached": op10["tasks_reached"],
            "target10_median_work": op10["median_min_work"],
            "target10_median_groups": op10["median_groups_inspected"],
            "target25_tasks_reached": op25["tasks_reached"],
            "target25_median_work": op25["median_min_work"],
            "target25_median_groups": op25["median_groups_inspected"],
            "target50_tasks_reached": op50["tasks_reached"],
            "target50_median_work": op50["median_min_work"],
            "target50_median_groups": op50["median_groups_inspected"],
        },
        "flat_width": {
            "target25_tasks_reached": flat25["tasks_reached"],
            "target25_median_work": flat25["median_min_work"],
            "target25_median_groups": flat25["median_groups_inspected"],
        },
        "fixed_session_query_aware": {
            "target10_tasks_reached": fixed10["tasks_reached"],
            "target10_median_work": fixed10["median_min_work"],
            "target10_median_groups": fixed10["median_groups_inspected"],
            "target25_tasks_reached": fixed25["tasks_reached"],
            "target25_median_work": fixed25["median_min_work"],
            "target25_median_groups": fixed25["median_groups_inspected"],
        },
        "default_vs_flat_target25": comp[("flat:width", 0.25)],
        "default_vs_fixed_target25": comp[("fixed_session:query_aware", 0.25)],
        "default_vs_fixed_target10": comp[("fixed_session:query_aware", 0.10)],
        "best_work_policy_counts": best_work_counts,
        "best_group_policy_counts": best_group_counts,
    }


def build_findings(summary: dict[str, Any]) -> list[str]:
    op = summary["operation_stack_query_aware"]
    flat = summary["flat_width"]
    fixed = summary["fixed_session_query_aware"]
    default_flat_25 = summary["default_vs_flat_target25"]
    default_fixed_25 = summary["default_vs_fixed_target25"]
    default_fixed_10 = summary["default_vs_fixed_target10"]
    best50 = summary["best_work_policy_counts"]["0.5"]
    return [
        (
            "At the 25% positive-recall target, operation_stack:query_aware reaches "
            f"{op['target25_tasks_reached']}/6 tasks with median inspected work "
            f"{op['target25_median_work']:.4f} and median {op['target25_median_groups']:.1f} groups. "
            f"Flat reaches the same target only by inspecting median work {flat['target25_median_work']:.4f}."
        ),
        (
            "At the same 25% target, fixed_session:query_aware also reaches "
            f"{fixed['target25_tasks_reached']}/6 tasks but needs median "
            f"{fixed['target25_median_groups']:.1f} groups versus "
            f"{op['target25_median_groups']:.1f} for operation stacks; default has fewer groups on "
            f"{default_fixed_25['group_wins']}/6 tasks."
        ),
        (
            "At the 10% early-recall target, operation_stack:query_aware and fixed_session:query_aware "
            f"both reach 6/6 tasks with about 10% work, but operation stacks use median "
            f"{op['target10_median_groups']:.1f} groups versus {fixed['target10_median_groups']:.1f}; "
            f"default has fewer groups on {default_fixed_10['group_wins']}/6 tasks."
        ),
        (
            "Compared with flat at the 25% target, operation_stack:query_aware has lower target work on "
            f"{default_flat_25['work_wins']}/6 tasks, keeping the flat summary as a complete but expensive baseline."
        ),
        (
            "The 50% target is an explicit counterpoint: operation_stack:query_aware reaches "
            f"{op['target50_tasks_reached']}/6 tasks and the best-work policies are {format_counts(best50)}. "
            "This supports configurable stack/ranker choices rather than a universal default."
        ),
    ]


def format_counts(counts: dict[str, Any]) -> str:
    return ", ".join(f"{key}={counts[key]}" for key in sorted(counts))


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# R337 Inspection-Target Cost Audit",
        "",
        "R337 reuses tracked R333 inspection curves and R336 actionability recommendations.",
        "It computes the minimum visible inspection point needed to reach fixed positive-recall targets.",
        "Hidden labels are used only through the already-scored R333 curves.",
        "",
        "## Primary Findings",
        "",
    ]
    lines.extend(f"- {finding}" for finding in report["primary_findings"])
    lines.extend(
        [
            "",
            "## Target Summary",
            "",
            "| Policy | Target | Tasks reached | Median work | Median groups |",
            "|---|---:|---:|---:|---:|",
        ]
    )
    for row in report["policy_target_summary"]:
        if row["policy"] in [DEFAULT_POLICY, "flat:width", "fixed_session:query_aware"]:
            lines.append(
                f"| {row['policy']} | {row['target_recall']} | {row['tasks_reached']}/6 | "
                f"{row['median_min_work']} | {row['median_groups_inspected']} |"
            )
    lines.extend(["", "## Non-Claims", ""])
    lines.extend(f"- {claim}" for claim in report["non_claims"])
    return "\n".join(lines) + "\n"


def render_html(report: dict[str, Any]) -> str:
    findings = "\n".join(
        f"<li>{html.escape(finding)}</li>" for finding in report["primary_findings"]
    )
    rows = []
    for row in report["policy_target_summary"]:
        if row["policy"] in [DEFAULT_POLICY, "flat:width", "fixed_session:query_aware"]:
            rows.append(
                "<tr>"
                f"<td>{html.escape(row['policy'])}</td>"
                f"<td>{row['target_recall']}</td>"
                f"<td>{row['tasks_reached']}/6</td>"
                f"<td>{row['median_min_work']}</td>"
                f"<td>{row['median_groups_inspected']}</td>"
                "</tr>"
            )
    non_claims = "\n".join(
        f"<li>{html.escape(claim)}</li>" for claim in report["non_claims"]
    )
    return f"""<!doctype html>
<meta charset="utf-8">
<title>R337 Inspection-Target Cost Audit</title>
<style>
body {{ font-family: system-ui, sans-serif; color: #202124; margin: 32px; line-height: 1.45; }}
table {{ border-collapse: collapse; width: 100%; margin: 24px 0; font-size: 13px; }}
th, td {{ border-bottom: 1px solid #d8dee8; padding: 7px 8px; text-align: left; }}
th {{ background: #eef2f6; }}
</style>
<h1>R337 Inspection-Target Cost Audit</h1>
<p>Reuses tracked R333/R336 artifacts; no dataset sync, creation, or relabeling.</p>
<h2>Primary Findings</h2>
<ul>{findings}</ul>
<h2>Target Summary</h2>
<table>
<tr><th>Policy</th><th>Target recall</th><th>Tasks reached</th><th>Median work</th><th>Median groups</th></tr>
{''.join(rows)}
</table>
<h2>Non-Claims</h2>
<ul>{non_claims}</ul>
"""


def main() -> None:
    args = parse_args()
    start = time.perf_counter()
    sources = [R333_REPORT, R333_CORE_CSV, R333_CURVES_CSV, R336_REPORT, R336_RECOMMENDATIONS_CSV]
    source_status = ensure_sources_tracked_clean(sources)
    r333 = load_json(R333_REPORT)
    r336 = load_json(R336_REPORT)
    curves = read_csv(R333_CURVES_CSV)
    recommendations = task_actions(read_csv(R336_RECOMMENDATIONS_CSV))
    target_rows = build_target_rows(curves, recommendations)
    target_summary = summarize_targets(target_rows)
    task_best = build_task_best_rows(target_rows)
    comparisons = compare_default(target_rows)
    summary = summarize(r333, r336, target_rows, target_summary, task_best, comparisons)

    report = {
        "run_id": RUN_ID,
        "schema": "agentsight.inspection-target.v1",
        "purpose": (
            "Measure inspection work and group fragmentation needed to reach fixed recall targets "
            "on real labeled agent traces."
        ),
        "source_run_ids": ["R333", "R336"],
        "source_status": source_status,
        "input_policy": {
            "sync": "none",
            "create": "none",
            "relabel": "none",
            "hidden_label_use": "offline scoring already materialized in R333 visible inspection curves",
            "source_artifacts": [rel(path) for path in sources],
        },
        "network_access_required": False,
        "profiler_abstractions": ["operation", "operation stack"],
        "default_policy": DEFAULT_POLICY,
        "baseline_policies": BASELINE_POLICIES,
        "recall_targets": RECALL_TARGETS,
        "summary": summary,
        "primary_findings": build_findings(summary),
        "policy_target_summary": target_summary,
        "non_claims": [
            "no new datasets, dataset sync, dataset creation, or relabeling",
            "no human or agent analyst productivity, accuracy, or time-to-answer claim",
            "no automatic universal policy selector",
            "no operation-stack dominance on every recall target or task",
            "no live eBPF overhead or trace-ecosystem compatibility claim",
            "no profiler abstraction beyond operation and operation stack",
        ],
        "reproducibility": {
            "commit": git_output(["rev-parse", "HEAD"]),
            "elapsed_seconds": round(time.perf_counter() - start, 4),
        },
    }
    report = round_value(report)

    args.out_dir.mkdir(parents=True, exist_ok=True)
    write_json(args.out_dir / "inspection-target-report.json", report)
    (args.out_dir / "inspection-target-report.md").write_text(
        render_markdown(report), encoding="utf-8"
    )
    (args.out_dir / "index.html").write_text(render_html(report), encoding="utf-8")
    write_csv(
        args.out_dir / "inspection-targets.csv",
        target_rows,
        [
            "task",
            "dataset",
            "query_family",
            "policy",
            "target_recall",
            "reached",
            "min_work",
            "groups_inspected",
            "achieved_recall",
            "precision_at_target",
            "f1_at_target",
            "selected_budget",
            "optimization_action",
            "useful_stack_fields",
            "counterpoints",
        ],
    )
    write_csv(
        args.out_dir / "policy-target-summary.csv",
        target_summary,
        [
            "policy",
            "target_recall",
            "tasks",
            "tasks_reached",
            "median_min_work",
            "mean_min_work",
            "median_groups_inspected",
            "mean_groups_inspected",
            "median_achieved_recall",
            "unreached_tasks",
        ],
    )
    write_csv(
        args.out_dir / "task-target-best.csv",
        task_best,
        [
            "task",
            "dataset",
            "query_family",
            "target_recall",
            "best_work_policy",
            "best_work",
            "best_work_groups",
            "best_group_policy",
            "best_groups",
            "best_group_work",
            "policies_reached",
            "default_reached",
            "default_work",
            "default_groups",
            "optimization_action",
        ],
    )
    write_csv(
        args.out_dir / "default-target-comparisons.csv",
        comparisons,
        [
            "default_policy",
            "baseline_policy",
            "target_recall",
            "reach_wins",
            "reach_ties",
            "reach_losses",
            "work_wins",
            "work_ties",
            "work_losses",
            "group_wins",
            "group_ties",
            "group_losses",
            "median_work_delta_default_minus_baseline",
            "median_group_delta_default_minus_baseline",
        ],
    )
    run_result = {
        "run_id": RUN_ID,
        "status": "ok",
        "out_dir": rel(args.out_dir),
        "summary": report["summary"],
        "network_access_required": False,
    }
    write_json(args.out_dir / "run-result.json", round_value(run_result))
    print(
        f"{RUN_ID} wrote {rel(args.out_dir)}: "
        f"{summary['tasks']} tasks, {summary['policies']} policies, "
        f"{len(RECALL_TARGETS)} recall targets"
    )
    op = summary["operation_stack_query_aware"]
    print(
        "operation_stack:query_aware target25: "
        f"{op['target25_tasks_reached']}/6 tasks, median work "
        f"{op['target25_median_work']:.4f}, median groups "
        f"{op['target25_median_groups']:.1f}"
    )


if __name__ == "__main__":
    main()
