#!/usr/bin/env python3
"""R336: multi-objective actionability selection audit.

This audit does not fetch, sync, create, or relabel data. It reads tracked
R320/R333/R334/R335 artifacts and asks whether the operation-stack profiler
produces actionable policy choices across different diagnostic objectives:
ranking fidelity, top-k localization, budgeted recall, first-positive work,
and fragmentation.

Hidden labels are only reused to score already-generated visible profiles.
They are not passed to the Rust profiler, ranker, or policy selector.
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
R320_OUT = OUT_ROOT / "operation-profile-accuracy-r320"
R333_OUT = OUT_ROOT / "operation-inspection-frontier-r333"
R334_OUT = OUT_ROOT / "operation-fragmentation-tradeoff-r334"
R335_OUT = OUT_ROOT / "operation-actionability-synthesis-r335"
DEFAULT_OUT_DIR = OUT_ROOT / "operation-actionability-selection-r336"
RUN_ID = "R336"

R320_REPORT = R320_OUT / "profile-accuracy-report.json"
R320_POLICY_CSV = R320_OUT / "policy-scores.csv"
R333_REPORT = R333_OUT / "inspection-frontier-report.json"
R333_BUDGET_CSV = R333_OUT / "budget-fragmentation-comparisons.csv"
R334_REPORT = R334_OUT / "fragmentation-tradeoff-report.json"
R334_DEFAULT_CSV = R334_OUT / "default-fragmentation-comparisons.csv"
R334_BUDGET_CSV = R334_OUT / "budget-fragmentation-comparisons.csv"
R335_REPORT = R335_OUT / "actionability-synthesis-report.json"
R335_CARDS_CSV = R335_OUT / "task-actionability-cards.csv"

DEFAULT_POLICY = "operation_stack:query_aware"
WIDTH_POLICY = "operation_stack:width"
FLAT_POLICY = "flat:width"
FIXED_POLICY = "fixed_session:query_aware"
DATASET_NATIVE_POLICY = "dataset_native:query_aware"
RAW_ACTION_POLICY = "raw_action_stack:query_aware"
CORE_POLICIES = [
    DEFAULT_POLICY,
    WIDTH_POLICY,
    FLAT_POLICY,
    FIXED_POLICY,
    DATASET_NATIVE_POLICY,
    RAW_ACTION_POLICY,
]

OBJECTIVES = {
    "ranking_fidelity_ap": {
        "metric": "average_precision",
        "direction": "higher",
        "question": "Which visible policy best orders labeled positives over the full ranked profile?",
    },
    "top5_localization_f1": {
        "metric": "top5_f1",
        "direction": "higher",
        "question": "Which visible policy best balances top-5 precision and recall?",
    },
    "budget30_recall": {
        "metric": "budget30_recall",
        "direction": "higher",
        "question": "Which visible policy recovers the most positives inside a 30% work budget?",
    },
    "first_positive_work": {
        "metric": "work_to_first_positive",
        "direction": "lower",
        "question": "Which visible policy reaches the first positive with least operation work?",
    },
    "groups_to_50pct": {
        "metric": "groups_to_50pct_recall",
        "direction": "lower",
        "question": "Which visible policy reaches 50% positives with fewest ranked groups?",
    },
    "total_group_fragmentation": {
        "metric": "groups",
        "direction": "lower",
        "question": "Which visible policy creates the fewest groups to inspect?",
    },
}

PARETO_METRICS = {
    "average_precision": "higher",
    "budget30_recall": "higher",
    "top5_f1": "higher",
    "top5_work": "lower",
    "groups_to_50pct_recall": "lower",
    "groups": "lower",
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


def ensure_sources_tracked_clean(paths: list[Path]) -> dict[str, str]:
    statuses: dict[str, str] = {}
    for path in paths:
        if not path.exists():
            raise SystemExit(f"missing source artifact {rel(path)}")
        git_check("source artifact is not git-tracked", ["ls-files", "--error-unmatch"], path)
        git_check("source artifact has unstaged changes", ["diff", "--quiet"], path)
        git_check("source artifact has staged changes", ["diff", "--cached", "--quiet"], path)
        statuses[rel(path)] = "pass"
    return statuses


def load_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as file:
        return json.load(file)


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(round_value(payload), indent=2, sort_keys=True) + "\n", encoding="utf-8")


def read_csv(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8", newline="") as file:
        return list(csv.DictReader(file))


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: format_value(row.get(field)) for field in fields})


def parse_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    return float(value)


def format_value(value: Any) -> Any:
    if isinstance(value, float):
        if math.isnan(value):
            return ""
        if math.isinf(value):
            return "inf"
        return round(value, 4)
    if value is None:
        return ""
    if isinstance(value, list):
        return "; ".join(str(item) for item in value)
    if isinstance(value, dict):
        return json.dumps(round_value(value), sort_keys=True)
    return value


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


def policy_key(row: dict[str, Any]) -> str:
    return f"{row['view']}:{row['ranker']}"


def policy_view(policy: str) -> str:
    return policy.split(":", 1)[0]


def load_visible_policy_scores() -> list[dict[str, Any]]:
    numeric_fields = {
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
    }
    rows: list[dict[str, Any]] = []
    for row in read_csv(R320_POLICY_CSV):
        if row["uses_hidden_fields"] != "False":
            continue
        parsed: dict[str, Any] = dict(row)
        parsed["policy"] = policy_key(parsed)
        for field in numeric_fields:
            parsed[field] = parse_float(parsed.get(field))
        rows.append(parsed)
    return rows


def load_actionability_cards() -> dict[str, dict[str, Any]]:
    return {row["task"]: row for row in read_csv(R335_CARDS_CSV)}


def metric_value(row: dict[str, Any], metric: str) -> float | None:
    value = row.get(metric)
    if value is None:
        return None
    return float(value)


def better_than(candidate: dict[str, Any], incumbent: dict[str, Any], metric: str, direction: str) -> bool:
    c_value = metric_value(candidate, metric)
    i_value = metric_value(incumbent, metric)
    if c_value is None:
        return False
    if i_value is None:
        return True
    if direction == "higher":
        if c_value != i_value:
            return c_value > i_value
    else:
        if c_value != i_value:
            return c_value < i_value
    c_ap = metric_value(candidate, "average_precision") or 0.0
    i_ap = metric_value(incumbent, "average_precision") or 0.0
    if c_ap != i_ap:
        return c_ap > i_ap
    c_work = metric_value(candidate, "top5_work")
    i_work = metric_value(incumbent, "top5_work")
    if c_work is not None and i_work is not None and c_work != i_work:
        return c_work < i_work
    return (metric_value(candidate, "groups") or float("inf")) < (metric_value(incumbent, "groups") or float("inf"))


def regret(best: float | None, candidate: float | None, direction: str) -> float | None:
    if best is None or candidate is None:
        return None
    if direction == "higher":
        return best - candidate
    return candidate - best


def classify_policy(policy: str) -> str:
    if policy == DEFAULT_POLICY:
        return "default_operation_stack"
    if policy == WIDTH_POLICY:
        return "operation_stack_width_counterpoint"
    if policy.startswith("operation_stack:"):
        return "operation_stack_variant"
    if policy.startswith("fixed_session:"):
        return "fixed_session_drilldown"
    if policy.startswith("flat:"):
        return "flat_summary_counterpoint"
    if policy.startswith("dataset_native:"):
        return "dataset_native_hierarchy"
    if policy.startswith("raw_action_stack:"):
        return "raw_action_stack_counterpoint"
    return "other_visible_policy"


def dominates(a: dict[str, Any], b: dict[str, Any]) -> bool:
    has_strict = False
    for metric, direction in PARETO_METRICS.items():
        a_value = metric_value(a, metric)
        b_value = metric_value(b, metric)
        if a_value is None or b_value is None:
            return False
        if direction == "higher":
            if a_value < b_value:
                return False
            if a_value > b_value:
                has_strict = True
        else:
            if a_value > b_value:
                return False
            if a_value < b_value:
                has_strict = True
    return has_strict


def build_objective_rows(
    rows: list[dict[str, Any]], cards: dict[str, dict[str, Any]]
) -> list[dict[str, Any]]:
    by_task: dict[str, list[dict[str, Any]]] = defaultdict(list)
    by_task_policy = {(row["task"], row["policy"]): row for row in rows}
    for row in rows:
        by_task[row["task"]].append(row)

    output: list[dict[str, Any]] = []
    for task in sorted(by_task):
        card = cards.get(task, {})
        for objective, spec in OBJECTIVES.items():
            metric = spec["metric"]
            direction = spec["direction"]
            candidates = [row for row in by_task[task] if metric_value(row, metric) is not None]
            if not candidates:
                continue
            best = candidates[0]
            for candidate in candidates[1:]:
                if better_than(candidate, best, metric, direction):
                    best = candidate
            row: dict[str, Any] = {
                "task": task,
                "dataset": best["dataset"],
                "query_family": best["query_family"],
                "objective": objective,
                "metric": metric,
                "direction": direction,
                "question": spec["question"],
                "best_policy": best["policy"],
                "best_view": best["view"],
                "best_ranker": best["ranker"],
                "best_value": metric_value(best, metric),
                "recommendation_class": classify_policy(best["policy"]),
                "optimization_action": card.get("optimization_action", ""),
                "useful_stack_fields": card.get("useful_stack_fields", ""),
                "counterpoints": card.get("counterpoints", ""),
            }
            for policy in CORE_POLICIES:
                candidate = by_task_policy[(task, policy)]
                candidate_value = metric_value(candidate, metric)
                row[f"{policy}_value"] = candidate_value
                row[f"{policy}_regret"] = regret(metric_value(best, metric), candidate_value, direction)
            row["default_is_best"] = best["policy"] == DEFAULT_POLICY
            row["fixed_session_is_best"] = best["policy"] == FIXED_POLICY
            output.append(row)
    return output


def build_pareto_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_task: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_task[row["task"]].append(row)
    output: list[dict[str, Any]] = []
    for task in sorted(by_task):
        task_rows = by_task[task]
        frontier = [row for row in task_rows if not any(dominates(other, row) for other in task_rows if other is not row)]
        frontier_policies = sorted(row["policy"] for row in frontier)
        for row in task_rows:
            output.append(
                {
                    "task": task,
                    "dataset": row["dataset"],
                    "query_family": row["query_family"],
                    "policy": row["policy"],
                    "view": row["view"],
                    "ranker": row["ranker"],
                    "on_frontier": row["policy"] in frontier_policies,
                    "frontier_policies": frontier_policies if row["policy"] in CORE_POLICIES else [],
                    "average_precision": row["average_precision"],
                    "budget30_recall": row["budget30_recall"],
                    "top5_f1": row["top5_f1"],
                    "top5_work": row["top5_work"],
                    "groups_to_50pct_recall": row["groups_to_50pct_recall"],
                    "groups": row["groups"],
                }
            )
    return output


def build_policy_summary(objective_rows: list[dict[str, Any]], pareto_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    policies = sorted(CORE_POLICIES)
    tasks = sorted({row["task"] for row in objective_rows})
    output: list[dict[str, Any]] = []
    pareto_by_policy = {
        policy: sum(row["policy"] == policy and row["on_frontier"] for row in pareto_rows)
        for policy in policies
    }
    for policy in policies:
        for objective in OBJECTIVES:
            scoped = [row for row in objective_rows if row["objective"] == objective]
            best_count = sum(row["best_policy"] == policy for row in scoped)
            regrets = [row.get(f"{policy}_regret") for row in scoped if row.get(f"{policy}_regret") is not None]
            values = [row.get(f"{policy}_value") for row in scoped if row.get(f"{policy}_value") is not None]
            output.append(
                {
                    "policy": policy,
                    "view": policy_view(policy),
                    "objective": objective,
                    "tasks": len(tasks),
                    "best_tasks": best_count,
                    "frontier_task_rows": pareto_by_policy[policy],
                    "median_value": median(values) if values else None,
                    "median_regret": median(regrets) if regrets else None,
                    "mean_regret": mean(regrets) if regrets else None,
                    "max_regret": max(regrets) if regrets else None,
                }
            )
    return output


def core_row(rows: list[dict[str, Any]], task: str, policy: str) -> dict[str, Any]:
    for row in rows:
        if row["task"] == task and row["policy"] == policy:
            return row
    raise KeyError((task, policy))


def compare_default_to_baselines(rows: list[dict[str, Any]]) -> dict[str, int]:
    tasks = sorted({row["task"] for row in rows})
    result = {
        "top5_work_lower_than_flat": 0,
        "budget30_recall_higher_than_flat": 0,
        "top5_recall_higher_than_fixed": 0,
        "groups_lower_than_fixed": 0,
        "groups_to_50pct_lower_than_fixed": 0,
        "work_to_first_positive_lower_than_fixed": 0,
    }
    for task in tasks:
        op = core_row(rows, task, DEFAULT_POLICY)
        flat = core_row(rows, task, FLAT_POLICY)
        fixed = core_row(rows, task, FIXED_POLICY)
        if (op["top5_work"] or 0.0) < (flat["top5_work"] or 0.0):
            result["top5_work_lower_than_flat"] += 1
        if (op["budget30_recall"] or 0.0) > (flat["budget30_recall"] or 0.0):
            result["budget30_recall_higher_than_flat"] += 1
        if (op["top5_recall"] or 0.0) > (fixed["top5_recall"] or 0.0):
            result["top5_recall_higher_than_fixed"] += 1
        if (op["groups"] or float("inf")) < (fixed["groups"] or float("inf")):
            result["groups_lower_than_fixed"] += 1
        if (op["groups_to_50pct_recall"] or float("inf")) < (fixed["groups_to_50pct_recall"] or float("inf")):
            result["groups_to_50pct_lower_than_fixed"] += 1
        if (op["work_to_first_positive"] or float("inf")) < (fixed["work_to_first_positive"] or float("inf")):
            result["work_to_first_positive_lower_than_fixed"] += 1
    return result


def summarize(
    rows: list[dict[str, Any]],
    objective_rows: list[dict[str, Any]],
    pareto_rows: list[dict[str, Any]],
    policy_summary: list[dict[str, Any]],
) -> dict[str, Any]:
    tasks = sorted({row["task"] for row in rows})
    datasets = sorted({row["dataset"] for row in rows})
    objective_best_view_counts = {
        objective: dict(Counter(row["best_view"] for row in objective_rows if row["objective"] == objective))
        for objective in OBJECTIVES
    }
    objective_best_policy_counts = {
        objective: dict(Counter(row["best_policy"] for row in objective_rows if row["objective"] == objective))
        for objective in OBJECTIVES
    }
    objective_default_best = {
        objective: sum(row["best_policy"] == DEFAULT_POLICY for row in objective_rows if row["objective"] == objective)
        for objective in OBJECTIVES
    }
    objectives_per_task = defaultdict(set)
    for row in objective_rows:
        objectives_per_task[row["task"]].add(row["best_policy"])
    pareto_by_policy = {
        policy: len({row["task"] for row in pareto_rows if row["policy"] == policy and row["on_frontier"]})
        for policy in CORE_POLICIES
    }
    summary = {
        "tasks": len(tasks),
        "datasets": len(datasets),
        "visible_policy_rows": len(rows),
        "visible_policies": len({row["policy"] for row in rows}),
        "objectives": len(OBJECTIVES),
        "objective_rows": len(objective_rows),
        "tasks_with_multiple_best_policies_across_objectives": sum(
            len(policies) > 1 for policies in objectives_per_task.values()
        ),
        "objective_best_view_counts": objective_best_view_counts,
        "objective_best_policy_counts": objective_best_policy_counts,
        "operation_stack_query_aware_best_counts": objective_default_best,
        "pareto_frontier_task_counts": pareto_by_policy,
        "default_vs_baselines": compare_default_to_baselines(rows),
        "policy_summary_rows": len(policy_summary),
    }
    return summary


def build_findings(summary: dict[str, Any]) -> list[str]:
    default_counts = summary["operation_stack_query_aware_best_counts"]
    baseline = summary["default_vs_baselines"]
    pareto = summary["pareto_frontier_task_counts"]
    return [
        (
            f"R336 scores {summary['visible_policies']} visible policies across {summary['tasks']} tasks and "
            f"{summary['objectives']} diagnostic objectives without fetching, syncing, creating, or relabeling data."
        ),
        (
            "Best visible policy depends on the analysis objective: objective best views are "
            f"{format_nested_counts(summary['objective_best_view_counts'])}. "
            "This strengthens the design choice to expose view, "
            "stack fields, predicates, and rankers as query-time knobs over the same operations."
        ),
        (
            f"{DEFAULT_POLICY} remains a strong default: it is Pareto-frontier on {pareto[DEFAULT_POLICY]}/6 tasks, "
            f"best AP on {default_counts['ranking_fidelity_ap']}/6 tasks, best 30% budget recall on "
            f"{default_counts['budget30_recall']}/6 tasks, and lower top-5 work than flat on "
            f"{baseline['top5_work_lower_than_flat']}/6 tasks."
        ),
        (
            "The fixed-session/span-tree proxy remains a real counterpoint: operation stacks improve top-5 recall "
            f"over fixed-session on {baseline['top5_recall_higher_than_fixed']}/6 tasks and reduce total groups on "
            f"{baseline['groups_lower_than_fixed']}/6 tasks, but lower work-to-first-positive on only "
            f"{baseline['work_to_first_positive_lower_than_fixed']}/6 tasks."
        ),
        (
            f"Every task needs more than one best policy across the diagnostic objectives in "
            f"{summary['tasks_with_multiple_best_policies_across_objectives']}/6 tasks. R336 therefore supports "
            "actionable optimization insight, not an automatic universal selector."
        ),
    ]


def format_counts(counts: dict[str, Any]) -> str:
    return ", ".join(f"{key}={counts[key]}" for key in sorted(counts))


def format_nested_counts(counts: dict[str, dict[str, Any]]) -> str:
    return "; ".join(f"{key}: {format_counts(counts[key])}" for key in sorted(counts))


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# R336 Actionability Selection Audit",
        "",
        "R336 reuses tracked R320/R333/R334/R335 artifacts. It treats already-generated",
        "visible profiles as policy choices and asks which policy is best for each",
        "diagnostic objective. Hidden labels are used only for offline scoring.",
        "",
        "## Primary Findings",
        "",
    ]
    lines.extend(f"- {finding}" for finding in report["primary_findings"])
    lines.extend(
        [
            "",
            "## Objective Best Policies",
            "",
            "| Objective | Best view counts | operation_stack:query_aware best tasks |",
            "|---|---|---:|",
        ]
    )
    for objective in OBJECTIVES:
        lines.append(
            f"| {objective} | {format_counts(report['summary']['objective_best_view_counts'][objective])} | "
            f"{report['summary']['operation_stack_query_aware_best_counts'][objective]}/6 |"
        )
    lines.extend(
        [
            "",
            "## Pareto And Baseline Readout",
            "",
            f"- Pareto-frontier task counts: {format_counts(report['summary']['pareto_frontier_task_counts'])}.",
            f"- Default-vs-baseline readout: {format_counts(report['summary']['default_vs_baselines'])}.",
            "",
            "## Non-Claims",
            "",
        ]
    )
    lines.extend(f"- {claim}" for claim in report["non_claims"])
    return "\n".join(lines) + "\n"


def render_html(report: dict[str, Any]) -> str:
    finding_items = "".join(f"<li>{html.escape(finding)}</li>" for finding in report["primary_findings"])
    objective_rows = []
    for objective in OBJECTIVES:
        objective_rows.append(
            "<tr>"
            f"<th>{html.escape(objective)}</th>"
            f"<td>{html.escape(format_counts(report['summary']['objective_best_view_counts'][objective]))}</td>"
            f"<td>{report['summary']['operation_stack_query_aware_best_counts'][objective]}/6</td>"
            "</tr>"
        )
    return f"""<!doctype html>
<meta charset="utf-8">
<title>R336 Actionability Selection Audit</title>
<style>
body {{ font-family: system-ui, sans-serif; color: #202124; margin: 32px; line-height: 1.45; }}
table {{ border-collapse: collapse; width: 100%; margin: 24px 0; font-size: 13px; }}
th, td {{ border-bottom: 1px solid #d8dee8; padding: 7px 8px; text-align: left; vertical-align: top; }}
th {{ background: #eef2f6; }}
.note {{ max-width: 980px; }}
</style>
<h1>R336 Actionability Selection Audit</h1>
<p class="note">This audit reuses tracked R320/R333/R334/R335 artifacts and scores visible policy choices across diagnostic objectives.</p>
<h2>Primary Findings</h2>
<ul>{finding_items}</ul>
<h2>Objective Best Policies</h2>
<table>
<tr><th>Objective</th><th>Best view counts</th><th>operation_stack:query_aware best tasks</th></tr>
{''.join(objective_rows)}
</table>
<h2>Pareto And Baselines</h2>
<p>Frontier task counts: <code>{html.escape(format_counts(report['summary']['pareto_frontier_task_counts']))}</code></p>
<p>Default-vs-baseline readout: <code>{html.escape(format_counts(report['summary']['default_vs_baselines']))}</code></p>
"""


def main() -> None:
    args = parse_args()
    start = time.time()
    sources = [
        R320_REPORT,
        R320_POLICY_CSV,
        R333_REPORT,
        R334_REPORT,
        R334_DEFAULT_CSV,
        R334_BUDGET_CSV,
        R335_REPORT,
        R335_CARDS_CSV,
    ]
    source_status = ensure_sources_tracked_clean(sources)
    r320 = load_json(R320_REPORT)
    r333 = load_json(R333_REPORT)
    r334 = load_json(R334_REPORT)
    r335 = load_json(R335_REPORT)
    rows = load_visible_policy_scores()
    cards = load_actionability_cards()
    objective_rows = build_objective_rows(rows, cards)
    pareto_rows = build_pareto_rows(rows)
    policy_summary = build_policy_summary(objective_rows, pareto_rows)
    summary = summarize(rows, objective_rows, pareto_rows, policy_summary)
    report = {
        "run_id": RUN_ID,
        "schema": "agentsight.actionability-selection.v1",
        "purpose": (
            "Audit whether visible operation-stack profiles provide objective-specific actionable policy choices "
            "on real labeled traces without adding profiler abstractions."
        ),
        "source_run_ids": ["R320", "R333", "R334", "R335"],
        "source_status": source_status,
        "source_totals": {
            "R320": r320.get("totals"),
            "R333": r333.get("totals"),
            "R334": r334.get("totals"),
            "R335": r335.get("summary"),
        },
        "input_policy": {
            "sync": "none",
            "create": "none",
            "relabel": "none",
            "hidden_label_use": "offline scoring after visible profiles/rankings already exist",
            "source_artifacts": [rel(path) for path in sources],
        },
        "network_access_required": False,
        "profiler_abstractions": ["operation", "operation stack"],
        "objectives": OBJECTIVES,
        "core_policies": CORE_POLICIES,
        "summary": summary,
        "primary_findings": build_findings(summary),
        "non_claims": [
            "no new datasets, dataset sync, dataset creation, or relabeling",
            "no human or agent analyst productivity, accuracy, or time-to-answer claim",
            "no automatic universal policy selector",
            "no operation-stack dominance on every metric",
            "no profiler abstraction beyond operation and operation stack",
        ],
        "reproducibility": {
            "commit": git_output(["rev-parse", "HEAD"]),
            "elapsed_seconds": round(time.time() - start, 4),
        },
    }
    args.out_dir.mkdir(parents=True, exist_ok=True)
    write_json(args.out_dir / "actionability-selection-report.json", report)
    write_csv(
        args.out_dir / "objective-recommendations.csv",
        objective_rows,
        [
            "task",
            "dataset",
            "query_family",
            "objective",
            "metric",
            "direction",
            "best_policy",
            "best_value",
            "recommendation_class",
            f"{DEFAULT_POLICY}_value",
            f"{DEFAULT_POLICY}_regret",
            f"{FIXED_POLICY}_value",
            f"{FIXED_POLICY}_regret",
            f"{FLAT_POLICY}_value",
            f"{FLAT_POLICY}_regret",
            f"{DATASET_NATIVE_POLICY}_value",
            f"{DATASET_NATIVE_POLICY}_regret",
            f"{RAW_ACTION_POLICY}_value",
            f"{RAW_ACTION_POLICY}_regret",
            "optimization_action",
            "useful_stack_fields",
            "counterpoints",
        ],
    )
    write_csv(
        args.out_dir / "policy-objective-summary.csv",
        policy_summary,
        [
            "policy",
            "view",
            "objective",
            "tasks",
            "best_tasks",
            "frontier_task_rows",
            "median_value",
            "median_regret",
            "mean_regret",
            "max_regret",
        ],
    )
    write_csv(
        args.out_dir / "pareto-frontier.csv",
        pareto_rows,
        [
            "task",
            "dataset",
            "query_family",
            "policy",
            "view",
            "ranker",
            "on_frontier",
            "frontier_policies",
            "average_precision",
            "budget30_recall",
            "top5_f1",
            "top5_work",
            "groups_to_50pct_recall",
            "groups",
        ],
    )
    markdown = render_markdown(report)
    (args.out_dir / "actionability-selection-report.md").write_text(markdown, encoding="utf-8")
    (args.out_dir / "index.html").write_text(render_html(report), encoding="utf-8")
    run_result = {
        "run_id": RUN_ID,
        "status": "ok",
        "report": rel(args.out_dir / "actionability-selection-report.json"),
        "summary": summary,
    }
    write_json(args.out_dir / "run-result.json", run_result)
    print(markdown)


if __name__ == "__main__":
    main()
