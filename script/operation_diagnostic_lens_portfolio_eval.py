#!/usr/bin/env python3
"""R345: diagnostic-lens portfolio over existing profiler results.

This audit does not fetch, sync, create, or relabel datasets. It reads tracked
R335/R341/R344 artifacts and turns actionability cards, objective-level
mechanism attribution, and metric-surface counterpoints into a reviewer-facing
portfolio of diagnostic lenses. The goal is to show which analysis views help
which real labeled tasks, where they mislead, and which optimization action a
profiler user should take next.
"""

from __future__ import annotations

import argparse
import csv
import html
import json
import math
import subprocess
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OUT_ROOT = ROOT / "docs" / "visexp" / "out"
R335_DIR = OUT_ROOT / "operation-actionability-synthesis-r335"
R341_DIR = OUT_ROOT / "operation-mechanism-attribution-r341"
R344_DIR = OUT_ROOT / "operation-metric-consistency-r344"
DEFAULT_OUT_DIR = OUT_ROOT / "operation-diagnostic-lens-portfolio-r345"
RUN_ID = "R345"

R335_REPORT = R335_DIR / "actionability-synthesis-report.json"
R335_CARDS = R335_DIR / "task-actionability-cards.csv"
R335_MECHANISMS = R335_DIR / "mechanism-evidence.csv"
R341_REPORT = R341_DIR / "mechanism-attribution-report.json"
R341_OBJECTIVES = R341_DIR / "objective-mechanism-attribution.csv"
R341_TRANSFER_ERRORS = R341_DIR / "transfer-error-attribution.csv"
R344_REPORT = R344_DIR / "metric-consistency-report.json"
R344_METRIC_SUMMARY = R344_DIR / "metric-summary.csv"

DEFAULT_POLICY_CLASS = "default_operation_stack"

LENS_SPECS = {
    "ranking_fidelity_ap": {
        "lens": "ranked-stack table",
        "visualization": "ranked table sorted by visible rank score with AP/AUPRC-style score",
        "question": "Which stack ordering is faithful over all labeled positives?",
    },
    "top5_localization_f1": {
        "lens": "hot-stack table",
        "visualization": "top-k hot-stack table with precision/recall/F1@5",
        "question": "Do the first hot groups contain task-relevant positives?",
    },
    "budget30_recall": {
        "lens": "budgeted inspection curve",
        "visualization": "recall vs. inspected-operation-work curve",
        "question": "How much labeled evidence appears under a fixed inspection budget?",
    },
    "first_positive_work": {
        "lens": "first-positive drilldown",
        "visualization": "ranked drilldown to first positive operation",
        "question": "How soon can the profiler surface the first relevant example?",
    },
    "groups_to_50pct": {
        "lens": "recall-fragmentation curve",
        "visualization": "groups required to reach 50% positive recall",
        "question": "How many groups must be inspected to cover half the positives?",
    },
    "total_group_fragmentation": {
        "lens": "group-fragmentation overview",
        "visualization": "group-count summary by view and stack depth",
        "question": "How fragmented is this view before any drilldown?",
    },
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


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as file:
        return list(csv.DictReader(file))


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: format_value(row.get(field)) for field in fields})


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(round_value(payload), indent=2, sort_keys=True) + "\n", encoding="utf-8")


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


def view_family(policy_class: str, best_view: str) -> str:
    if policy_class == DEFAULT_POLICY_CLASS:
        return "operation_stack_default"
    if best_view == "operation_stack":
        return "operation_stack_variant"
    return best_view


def task_cards_by_task(rows: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    return {row["task"]: row for row in rows}


def lens_interpretation(objective: str, view_counts: Counter[str], default_count: int) -> str:
    if objective == "ranking_fidelity_ap":
        return "Operation-stack query-aware is often the AP-faithful ranking view, but fixed-session and dataset-native remain task-specific counterpoints."
    if objective == "top5_localization_f1":
        return "Hot-group F1 is the most fragmented lens: raw-action, dataset-native, fixed-session, flat, and operation-stack each win at least one task."
    if objective == "budget30_recall":
        return "Budgeted recall mostly favors operation stacks, but a width variant and dataset-native hierarchy win on boundary/safety tasks."
    if objective == "first_positive_work":
        return "First-positive search is a drilldown counterpoint: fixed-session or raw-action can surface an example earlier even when operation stacks rank better overall."
    if objective == "groups_to_50pct":
        return "Coverage at 50% positives often prefers raw-action or dataset-native groups, exposing mapping/depth tuning needs."
    if objective == "total_group_fragmentation":
        return "Flat has the lowest group count by construction, so group count alone is a counterpoint metric, not a localization metric."
    dominant = view_counts.most_common(1)[0][0] if view_counts else "unknown"
    return f"{dominant} is the most common winner for this objective; default operation-stack wins {default_count} tasks."


def build_lens_summary(objective_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    by_objective: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in objective_rows:
        by_objective[row["objective"]].append(row)

    rows: list[dict[str, Any]] = []
    for objective in LENS_SPECS:
        items = by_objective.get(objective, [])
        view_counts = Counter(row["best_view"] for row in items)
        class_counts = Counter(row["best_policy_class"] for row in items)
        default_count = class_counts[DEFAULT_POLICY_CLASS]
        op_family_count = sum(1 for row in items if row["best_view"] == "operation_stack")
        rows.append(
            {
                "objective": objective,
                "lens": LENS_SPECS[objective]["lens"],
                "visualization": LENS_SPECS[objective]["visualization"],
                "question": LENS_SPECS[objective]["question"],
                "tasks": len(items),
                "distinct_best_views": len(view_counts),
                "dominant_best_view": view_counts.most_common(1)[0][0] if view_counts else "",
                "operation_stack_family_best_tasks": op_family_count,
                "default_operation_stack_best_tasks": default_count,
                "non_operation_stack_best_tasks": len(items) - op_family_count,
                "best_view_distribution": dict(sorted(view_counts.items())),
                "best_policy_class_distribution": dict(sorted(class_counts.items())),
                "interpretation": lens_interpretation(objective, view_counts, default_count),
            }
        )
    return rows


def build_task_lens_cards(cards: list[dict[str, str]], objective_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    by_task: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in objective_rows:
        by_task[row["task"]].append(row)

    rows: list[dict[str, Any]] = []
    for card in cards:
        task = card["task"]
        items = by_task[task]
        best_views = sorted({row["best_view"] for row in items})
        objective_policy_map = [
            f"{row['objective']}={row['best_policy']}"
            for row in sorted(items, key=lambda row: row["objective"])
        ]
        default_objectives = sorted(row["objective"] for row in items if row["best_policy_class"] == DEFAULT_POLICY_CLASS)
        operation_stack_objectives = sorted(row["objective"] for row in items if row["best_view"] == "operation_stack")
        counterpoint_objectives = sorted(row["objective"] for row in items if row["best_view"] != "operation_stack")
        evidence_tags = split_semicolon(card.get("evidence_tags", ""))
        counterpoints = split_semicolon(card.get("counterpoints", ""))
        rows.append(
            {
                "task": task,
                "dataset": card["dataset"],
                "query_family": card["query_family"],
                "distinct_best_views": len(best_views),
                "best_views": best_views,
                "objective_policy_map": objective_policy_map,
                "operation_stack_best_objectives": operation_stack_objectives,
                "default_operation_stack_best_objectives": default_objectives,
                "counterpoint_objectives": counterpoint_objectives,
                "useful_stack_fields": card["useful_stack_fields"],
                "optimization_action": card["optimization_action"],
                "evidence_tags": evidence_tags,
                "counterpoints": counterpoints,
                "visual_recipe": visual_recipe(card, items),
                "actionability_status": card["actionability_status"],
            }
        )
    return rows


def visual_recipe(card: dict[str, str], objective_rows: list[dict[str, str]]) -> str:
    family = card["query_family"]
    if family == "failure-looping":
        return "Start with a ranked operation-stack table over repeat_signal/phase/action, then inspect budgeted recall for prevalence."
    if family == "failure-side-effect":
        return "Compare fixed-session drilldown with deeper write/input operation-stack fields before trusting hot groups."
    if family == "safety":
        return "Use environment/phase/action operation stacks for hot groups, then check dataset-native safety hierarchy for AP headroom."
    if family == "step-quality":
        return "Use desktop phase/repeat/action stacks for AP and budget recall, with raw-action/fixed-session drilldown for examples."
    if family == "human-boundary":
        return "Use group-depth or boundary-derived stack fields, then inspect fixed-session examples for first-positive work."
    best_views = sorted({row["best_view"] for row in objective_rows})
    return f"Compare {', '.join(best_views)} views under ranked, budgeted, and fragmentation lenses."


def build_counterpoint_rows(
    objective_rows: list[dict[str, str]], metric_rows: list[dict[str, str]], cards: dict[str, dict[str, str]]
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in objective_rows:
        if row["best_policy_class"] == DEFAULT_POLICY_CLASS:
            continue
        card = cards[row["task"]]
        rows.append(
            {
                "source": "R341 objective lens",
                "task": row["task"],
                "dataset": row["dataset"],
                "objective_or_metric": row["objective"],
                "counterpoint": row["best_policy_class"],
                "best_policy": row["best_policy"],
                "operation_stack_query_aware_regret": row["operation_stack_query_aware_regret"],
                "action": card["optimization_action"],
            }
        )

    for row in metric_rows:
        if row["verdict"] not in {"counterpoint", "mixed"}:
            continue
        rows.append(
            {
                "source": "R344 metric surface",
                "task": "all_tasks",
                "dataset": "mixed",
                "objective_or_metric": f"{row['baseline']}:{row['metric']}",
                "counterpoint": row["verdict"],
                "best_policy": row["baseline"],
                "operation_stack_query_aware_regret": row["median_delta_default_minus_baseline"],
                "action": "Treat this metric as a scope guardrail or secondary lens rather than a dominance claim.",
            }
        )
    return rows


def build_summary(
    cards: list[dict[str, str]],
    objective_rows: list[dict[str, str]],
    lens_rows: list[dict[str, Any]],
    task_rows: list[dict[str, Any]],
    counterpoint_rows: list[dict[str, Any]],
    metric_report: dict[str, Any],
) -> dict[str, Any]:
    objective_classes = Counter(row["best_policy_class"] for row in objective_rows)
    objective_views = Counter(row["best_view"] for row in objective_rows)
    task_view_counts = {row["task"]: row["distinct_best_views"] for row in task_rows}
    unique_actions = {row["optimization_action"] for row in cards if row.get("optimization_action")}
    r344_summary = metric_report["summary"]
    summary = {
        "overall": "pass",
        "tasks": len(cards),
        "datasets": len({row["dataset"] for row in cards}),
        "lens_count": len(lens_rows),
        "objective_rows": len(objective_rows),
        "task_cards": len(task_rows),
        "actionable_task_cards": sum(row.get("actionability_status", "").startswith("actionable") for row in cards),
        "distinct_optimization_actions": len(unique_actions),
        "default_operation_stack_best_objectives": objective_classes[DEFAULT_POLICY_CLASS],
        "operation_stack_family_best_objectives": objective_views["operation_stack"],
        "non_operation_stack_best_objectives": len(objective_rows) - objective_views["operation_stack"],
        "tasks_with_three_or_more_best_views": sum(count >= 3 for count in task_view_counts.values()),
        "min_distinct_best_views_per_task": min(task_view_counts.values()) if task_view_counts else 0,
        "max_distinct_best_views_per_task": max(task_view_counts.values()) if task_view_counts else 0,
        "counterpoint_rows": len(counterpoint_rows),
        "r344_support_verdicts": r344_summary["support_verdicts"],
        "r344_counterpoint_verdicts": r344_summary["counterpoint_verdicts"],
        "r344_mixed_or_weak_verdicts": r344_summary["mixed_or_weak_verdicts"],
        "network_access_required": False,
    }
    if summary["tasks"] != 6 or summary["lens_count"] != 6 or summary["actionable_task_cards"] != 6:
        summary["overall"] = "fail"
    if summary["tasks_with_three_or_more_best_views"] != 6:
        summary["overall"] = "fail"
    if summary["r344_counterpoint_verdicts"] == 0 or summary["non_operation_stack_best_objectives"] == 0:
        summary["overall"] = "fail"
    return summary


def build_markdown(path: Path, payload: dict[str, Any]) -> None:
    summary = payload["summary"]
    lines = [
        "# Diagnostic Lens Portfolio R345",
        "",
        "R345 reuses tracked R335/R341/R344 artifacts to summarize which diagnostic lens helps each real labeled task. It does not fetch, sync, create, relabel, or rerank datasets.",
        "",
        "## Verdict",
        "",
        f"- Overall: {summary['overall']}.",
        f"- Tasks: {summary['tasks']} across {summary['datasets']} datasets.",
        f"- Diagnostic lenses: {summary['lens_count']} over {summary['objective_rows']} objective rows.",
        f"- Actionable task cards: {summary['actionable_task_cards']}/{summary['task_cards']}.",
        f"- Best objective views: operation-stack family {summary['operation_stack_family_best_objectives']}/{summary['objective_rows']}; non-operation-stack counterpoints {summary['non_operation_stack_best_objectives']}/{summary['objective_rows']}.",
        f"- View diversity: {summary['tasks_with_three_or_more_best_views']}/{summary['tasks']} tasks need at least three best views across objectives.",
        f"- R344 metric surface: {summary['r344_support_verdicts']} support, {summary['r344_counterpoint_verdicts']} counterpoints, {summary['r344_mixed_or_weak_verdicts']} mixed/weak.",
        "",
        "## Lens Summary",
        "",
        "| Objective | Lens | Best Views | Default Op-Stack | Interpretation |",
        "|---|---|---|---:|---|",
    ]
    for row in payload["lens_summary"]:
        lines.append(
            f"| {row['objective']} | {row['lens']} | {row['best_view_distribution']} | "
            f"{row['default_operation_stack_best_tasks']}/{row['tasks']} | {row['interpretation']} |"
        )
    lines.extend(
        [
            "",
            "## Task Cards",
            "",
            "| Task | Views | Operation-Stack Objectives | Action | Counterpoints |",
            "|---|---:|---|---|---|",
        ]
    )
    for row in payload["task_lens_cards"]:
        lines.append(
            f"| {row['task']} | {row['distinct_best_views']} | {row['operation_stack_best_objectives']} | "
            f"{row['optimization_action']} | {row['counterpoints']} |"
        )
    lines.extend(
        [
            "",
            "## Scope",
            "",
            "R345 supports diagnostic-lens actionability: the profiler exposes which stack fields, rankers, mappings, and drilldowns to tune. It does not support human productivity, automatic boundary discovery, metric dominance, a universal selector, or full trace-ecosystem compatibility.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def build_html(path: Path, payload: dict[str, Any]) -> None:
    def esc(value: Any) -> str:
        return html.escape(str(format_value(value)))

    summary = payload["summary"]
    lens_rows = "\n".join(
        "<tr>"
        f"<td>{esc(row['objective'])}</td>"
        f"<td>{esc(row['lens'])}</td>"
        f"<td>{esc(row['best_view_distribution'])}</td>"
        f"<td>{esc(row['interpretation'])}</td>"
        "</tr>"
        for row in payload["lens_summary"]
    )
    task_rows = "\n".join(
        "<tr>"
        f"<td>{esc(row['task'])}</td>"
        f"<td>{esc(row['distinct_best_views'])}</td>"
        f"<td>{esc(row['visual_recipe'])}</td>"
        f"<td>{esc(row['optimization_action'])}</td>"
        "</tr>"
        for row in payload["task_lens_cards"]
    )
    path.write_text(
        f"""<!doctype html>
<html lang=\"en\">
<meta charset=\"utf-8\">
<title>R345 Diagnostic Lens Portfolio</title>
<style>
body {{ font-family: system-ui, sans-serif; margin: 2rem; line-height: 1.45; }}
table {{ border-collapse: collapse; width: 100%; margin: 1rem 0; }}
th, td {{ border: 1px solid #d0d7de; padding: 0.45rem; vertical-align: top; }}
th {{ background: #f6f8fa; text-align: left; }}
code {{ background: #f6f8fa; padding: 0.1rem 0.25rem; }}
</style>
<h1>R345 Diagnostic Lens Portfolio</h1>
<p>Overall: <strong>{esc(summary['overall'])}</strong>. R345 reads tracked R335/R341/R344 artifacts only.</p>
<ul>
  <li>{esc(summary['tasks'])} tasks across {esc(summary['datasets'])} datasets.</li>
  <li>{esc(summary['lens_count'])} diagnostic lenses over {esc(summary['objective_rows'])} objective rows.</li>
  <li>{esc(summary['tasks_with_three_or_more_best_views'])}/{esc(summary['tasks'])} tasks need at least three best views across objectives.</li>
  <li>R344 metric surface: {esc(summary['r344_support_verdicts'])} support, {esc(summary['r344_counterpoint_verdicts'])} counterpoints, {esc(summary['r344_mixed_or_weak_verdicts'])} mixed/weak.</li>
</ul>
<h2>Lens Summary</h2>
<table><thead><tr><th>Objective</th><th>Lens</th><th>Best view distribution</th><th>Interpretation</th></tr></thead><tbody>{lens_rows}</tbody></table>
<h2>Task Cards</h2>
<table><thead><tr><th>Task</th><th>Views</th><th>Visual recipe</th><th>Optimization action</th></tr></thead><tbody>{task_rows}</tbody></table>
</html>
""",
        encoding="utf-8",
    )


def build_payload(out_dir: Path) -> dict[str, Any]:
    source_paths = [
        R335_REPORT,
        R335_CARDS,
        R335_MECHANISMS,
        R341_REPORT,
        R341_OBJECTIVES,
        R341_TRANSFER_ERRORS,
        R344_REPORT,
        R344_METRIC_SUMMARY,
    ]
    source_status = ensure_sources_tracked_clean(source_paths)
    cards = read_csv(R335_CARDS)
    objective_rows = read_csv(R341_OBJECTIVES)
    metric_rows = read_csv(R344_METRIC_SUMMARY)
    metric_report = load_json(R344_REPORT)

    card_map = task_cards_by_task(cards)
    lens_rows = build_lens_summary(objective_rows)
    task_rows = build_task_lens_cards(cards, objective_rows)
    counterpoint_rows = build_counterpoint_rows(objective_rows, metric_rows, card_map)
    summary = build_summary(cards, objective_rows, lens_rows, task_rows, counterpoint_rows, metric_report)

    return {
        "run_id": RUN_ID,
        "schema": "agentsight.operation-diagnostic-lens-portfolio.v1",
        "summary": summary,
        "profiler_abstractions": ["operation", "operation stack"],
        "input_policy": {
            "dataset_sync": "none",
            "dataset_creation": "none",
            "dataset_relabeling": "none",
            "ranking_recomputed": False,
            "network_access_required": False,
            "hidden_label_use": "R345 reads already-scored R335/R341/R344 artifacts; it does not form new rankings from hidden labels",
        },
        "source_status": source_status,
        "source_artifacts": [rel(path) for path in source_paths],
        "lens_summary": lens_rows,
        "task_lens_cards": task_rows,
        "counterpoint_ledger": counterpoint_rows,
    }


def main() -> None:
    args = parse_args()
    out_dir = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    payload = build_payload(out_dir)

    write_json(out_dir / "diagnostic-lens-report.json", payload)
    write_json(out_dir / "run-result.json", {"run_id": RUN_ID, "schema": payload["schema"], "summary": payload["summary"]})
    write_csv(
        out_dir / "diagnostic-lens-summary.csv",
        payload["lens_summary"],
        [
            "objective",
            "lens",
            "visualization",
            "question",
            "tasks",
            "distinct_best_views",
            "dominant_best_view",
            "operation_stack_family_best_tasks",
            "default_operation_stack_best_tasks",
            "non_operation_stack_best_tasks",
            "best_view_distribution",
            "best_policy_class_distribution",
            "interpretation",
        ],
    )
    write_csv(
        out_dir / "task-lens-cards.csv",
        payload["task_lens_cards"],
        [
            "task",
            "dataset",
            "query_family",
            "distinct_best_views",
            "best_views",
            "objective_policy_map",
            "operation_stack_best_objectives",
            "default_operation_stack_best_objectives",
            "counterpoint_objectives",
            "useful_stack_fields",
            "optimization_action",
            "evidence_tags",
            "counterpoints",
            "visual_recipe",
            "actionability_status",
        ],
    )
    write_csv(
        out_dir / "counterpoint-ledger.csv",
        payload["counterpoint_ledger"],
        [
            "source",
            "task",
            "dataset",
            "objective_or_metric",
            "counterpoint",
            "best_policy",
            "operation_stack_query_aware_regret",
            "action",
        ],
    )
    build_markdown(out_dir / "diagnostic-lens-report.md", payload)
    build_html(out_dir / "index.html", payload)
    print(json.dumps(round_value(payload["summary"]), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
