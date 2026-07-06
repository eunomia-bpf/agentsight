#!/usr/bin/env python3
"""R350: evidence-packet budget audit over existing labeled agent traces.

This audit does not fetch, sync, create, or relabel datasets. It reads tracked
R346/R347/R348/R349 artifacts and asks whether the profiler output can form a
bounded, reviewer-auditable diagnostic packet: top-ranked operation-stack
evidence, a baseline counterpoint, an action counterfactual, and a held-out
transfer guardrail.
"""

from __future__ import annotations

import argparse
import csv
import html
import json
import math
import subprocess
from pathlib import Path
from statistics import median
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OUT_ROOT = ROOT / "docs" / "visexp" / "out"
R346_DIR = OUT_ROOT / "operation-diagnostic-casebook-r346"
R347_DIR = OUT_ROOT / "operation-case-baseline-contrast-r347"
R348_DIR = OUT_ROOT / "operation-action-counterfactual-r348"
R349_DIR = OUT_ROOT / "operation-action-transfer-r349"
DEFAULT_OUT_DIR = OUT_ROOT / "operation-evidence-packet-r350"
RUN_ID = "R350"

STRICT_OPERATION_WORK_BUDGET = 0.30
FIRST_POSITIVE_WORK_BUDGET = 0.10

SOURCE_ARTIFACTS = {
    "R346 report": R346_DIR / "diagnostic-casebook-report.json",
    "R346 task cards": R346_DIR / "task-diagnostic-case-cards.csv",
    "R346 top stack evidence": R346_DIR / "top-stack-evidence.csv",
    "R347 report": R347_DIR / "case-baseline-contrast-report.json",
    "R347 task cards": R347_DIR / "task-baseline-contrast-cards.csv",
    "R347 view metrics": R347_DIR / "view-case-metrics.csv",
    "R348 report": R348_DIR / "action-counterfactual-report.json",
    "R348 task cards": R348_DIR / "task-action-counterfactual-cards.csv",
    "R348 objective counterfactuals": R348_DIR / "objective-counterfactuals.csv",
    "R348 action summary": R348_DIR / "action-class-summary.csv",
    "R349 report": R349_DIR / "action-transfer-report.json",
    "R349 task cards": R349_DIR / "task-action-transfer-cards.csv",
    "R349 summary": R349_DIR / "action-transfer-summary.csv",
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
    status: dict[str, str] = {}
    for path in paths:
        if not path.exists():
            raise SystemExit(f"missing source artifact {rel(path)}")
        git_check("source artifact is not git-tracked", path, ["ls-files", "--error-unmatch"])
        git_check("source artifact has unstaged changes", path, ["diff", "--quiet"])
        git_check("source artifact has staged changes", path, ["diff", "--cached", "--quiet"])
        status[rel(path)] = "tracked_clean"
    return status


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as file:
        return list(csv.DictReader(file))


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: format_value(row.get(field)) for field in fields})


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(round_value(payload), indent=2, sort_keys=True) + "\n", encoding="utf-8")


def as_float(value: Any) -> float:
    if value in ("", None):
        return 0.0
    return float(value)


def as_int(value: Any) -> int:
    if value in ("", None):
        return 0
    return int(float(value))


def as_bool(value: str | bool) -> bool:
    if isinstance(value, bool):
        return value
    return value.lower() == "true"


def split_items(value: str) -> list[str]:
    return [item.strip() for item in value.split(";") if item.strip()]


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
    if isinstance(value, (list, dict)):
        return json.dumps(round_value(value), sort_keys=True)
    return value


def rows_by_key(rows: list[dict[str, str]], key: str) -> dict[str, dict[str, str]]:
    result: dict[str, dict[str, str]] = {}
    for row in rows:
        if row[key] in result:
            raise SystemExit(f"duplicate {key}={row[key]}")
        result[row[key]] = row
    return result


def transfer_by_task_protocol(rows: list[dict[str, str]]) -> dict[tuple[str, str], dict[str, str]]:
    return {(row["task"], row["protocol"]): row for row in rows}


def summarize_top_stack_evidence(rows: list[dict[str, str]]) -> dict[str, dict[str, Any]]:
    by_task: dict[str, list[dict[str, str]]] = {}
    for row in rows:
        by_task.setdefault(row["task"], []).append(row)
    summary: dict[str, dict[str, Any]] = {}
    for task, task_rows in by_task.items():
        task_rows.sort(key=lambda row: as_int(row["rank"]))
        summary[task] = {
            "top_stack_groups": len(task_rows),
            "top_stack_positive_groups": sum(as_int(row["positive_operations"]) > 0 for row in task_rows),
            "top_stack_operations": sum(as_int(row["operations"]) for row in task_rows),
            "top_stack_positive_operations": sum(as_int(row["positive_operations"]) for row in task_rows),
            "top_stack_group_ids": [row["group_id"] for row in task_rows],
        }
    return summary


def build_task_packets(
    r346_cards: list[dict[str, str]],
    r347_cards: list[dict[str, str]],
    r348_cards: list[dict[str, str]],
    r349_cards: list[dict[str, str]],
    top_stack_summary: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    r347_by_task = rows_by_key(r347_cards, "task")
    r348_by_task = rows_by_key(r348_cards, "task")
    r349_by_key = transfer_by_task_protocol(r349_cards)

    rows: list[dict[str, Any]] = []
    for card in sorted(r346_cards, key=lambda row: row["task"]):
        task = card["task"]
        case = r347_by_task[task]
        action = r348_by_task[task]
        leave_task = r349_by_key.get((task, "leave_task"), {})
        leave_dataset = r349_by_key.get((task, "leave_dataset"), {})
        top_stack = top_stack_summary[task]
        operations = as_int(card["operations"])
        positives = as_int(card["positives"])
        top5_work = as_float(card["top5_work"])
        first_positive_work = as_float(card["first_positive_work"])
        top5_positive = as_int(card["top5_positive_groups"]) > 0
        has_counterpoint = bool(card["counterpoints"] or case["counterpoints"] or action["case_counterpoints"])
        has_nondefault_action = as_int(action["nondefault_action_rows"]) > 0
        strict_budget = top5_positive and top5_work <= STRICT_OPERATION_WORK_BUDGET
        first_positive_budget = first_positive_work <= FIRST_POSITIVE_WORK_BUDGET
        if top5_positive and has_counterpoint and has_nondefault_action and strict_budget:
            verdict = "bounded_30pct_packet"
        elif top5_positive and has_counterpoint and has_nondefault_action:
            verdict = "actionable_budget_exception"
        else:
            verdict = "insufficient_packet"

        rows.append(
            {
                "task": task,
                "dataset": card["dataset"],
                "query_family": card["query_family"],
                "operations": operations,
                "positives": positives,
                "prevalence": positives / operations if operations else 0.0,
                "operation_stack_groups": as_int(card["operation_stack_groups"]),
                "evidence_groups_inspected": as_int(card["top_groups"]),
                "top_stack_positive_groups": top_stack["top_stack_positive_groups"],
                "top_stack_positive_operations": top_stack["top_stack_positive_operations"],
                "top_stack_group_ids": top_stack["top_stack_group_ids"],
                "top1_positive": as_bool(card["top1_positive"]),
                "top5_positive": top5_positive,
                "top5_recall": as_float(card["top5_recall"]),
                "top5_precision": as_float(card["top5_precision"]),
                "top5_lift": as_float(card["top5_lift"]),
                "top5_work": top5_work,
                "first_positive_rank": as_int(card["first_positive_rank"]),
                "first_positive_work": first_positive_work,
                "top5_work_le_30pct": strict_budget,
                "first_positive_work_le_10pct": first_positive_budget,
                "flat_top5_work": as_float(case["flat_top5_work"]),
                "fixed_session_top5_recall": as_float(case["fixed_session_top5_recall"]),
                "operation_stack_beats_flat_work": as_bool(case["operation_stack_beats_flat_work"]),
                "operation_stack_beats_fixed_recall": as_bool(case["operation_stack_beats_fixed_recall"]),
                "operation_stack_has_fewer_groups_than_fixed": as_bool(case["operation_stack_has_fewer_groups_than_fixed"]),
                "baseline_counterpoints": split_items(case["counterpoints"]),
                "nondefault_action_rows": as_int(action["nondefault_action_rows"]),
                "default_best_rows": as_int(action["default_best_rows"]),
                "action_class_count": as_int(action["action_class_count"]),
                "action_classes": split_items(action["action_classes"]),
                "median_gain_over_default": as_float(action["median_gain_over_default"]),
                "max_gain_over_default": as_float(action["max_gain_over_default"]),
                "optimization_action": action["optimization_action"],
                "useful_stack_fields": action["useful_stack_fields"],
                "leave_task_within_tolerance": as_int(leave_task.get("selected_within_tolerance", 0)),
                "leave_task_exact_action": as_int(leave_task.get("selected_action_exact", 0)),
                "leave_task_beats_default": as_int(leave_task.get("selected_beats_default", 0)),
                "leave_dataset_within_tolerance": as_int(leave_dataset.get("selected_within_tolerance", 0)),
                "leave_dataset_exact_action": as_int(leave_dataset.get("selected_action_exact", 0)),
                "leave_dataset_beats_default": as_int(leave_dataset.get("selected_beats_default", 0)),
                "transfer_guardrail": "held_out_metric_partial_not_action_exact",
                "packet_verdict": verdict,
            }
        )
    return rows


def build_objective_packets(
    objective_rows: list[dict[str, str]],
    task_packets: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    packet_by_task = {row["task"]: row for row in task_packets}
    rows: list[dict[str, Any]] = []
    for row in objective_rows:
        packet = packet_by_task[row["task"]]
        rows.append(
            {
                "task": row["task"],
                "dataset": row["dataset"],
                "query_family": row["query_family"],
                "objective": row["objective"],
                "metric": row["metric"],
                "default_policy": row["default_policy"],
                "best_policy": row["best_policy"],
                "best_view": row["best_view"],
                "best_ranker": row["best_ranker"],
                "action_class": row["action_class"],
                "gain_over_default": as_float(row["gain_over_default"]),
                "default_is_best": as_bool(row["default_is_best"]),
                "best_is_visible_non_oracle": as_bool(row["best_is_visible_non_oracle"]),
                "top5_positive": packet["top5_positive"],
                "top5_work": packet["top5_work"],
                "packet_verdict": packet["packet_verdict"],
                "optimization_action": row["optimization_action"],
                "counterpoints": split_items(row["counterpoints"]),
            }
        )
    return rows


def build_summary(
    task_packets: list[dict[str, Any]],
    objective_packets: list[dict[str, Any]],
    action_summary: list[dict[str, str]],
    reports: dict[str, Any],
) -> dict[str, Any]:
    top5_work = [row["top5_work"] for row in task_packets]
    first_work = [row["first_positive_work"] for row in task_packets]
    top5_recall = [row["top5_recall"] for row in task_packets]
    top5_lift = [row["top5_lift"] for row in task_packets]
    nondefault_objectives = [row for row in objective_packets if not row["default_is_best"]]
    visible_best = [row for row in objective_packets if row["best_is_visible_non_oracle"]]
    strict_packets = [row for row in task_packets if row["packet_verdict"] == "bounded_30pct_packet"]
    actionable_packets = [row for row in task_packets if row["packet_verdict"] != "insufficient_packet"]
    action_classes = {row["action_class"] for row in objective_packets}
    transfer_summary = reports["R349"]["summary"]

    return {
        "overall": "pass"
        if len(task_packets) == 6
        and len(actionable_packets) == 6
        and len(strict_packets) >= 4
        and len(objective_packets) == 36
        and len(visible_best) == 36
        and transfer_summary["aligned_decisions"] == 60
        else "fail",
        "tasks": len(task_packets),
        "datasets": len({row["dataset"] for row in task_packets}),
        "objective_rows": len(objective_packets),
        "action_classes": len(action_classes),
        "action_summary_rows": len(action_summary),
        "packets_with_top5_positive": sum(row["top5_positive"] for row in task_packets),
        "packets_with_top1_positive": sum(row["top1_positive"] for row in task_packets),
        "packets_with_30pct_work_budget": len(strict_packets),
        "packets_with_first_positive_10pct_budget": sum(row["first_positive_work_le_10pct"] for row in task_packets),
        "packets_with_baseline_counterpoints": sum(bool(row["baseline_counterpoints"]) for row in task_packets),
        "packets_with_nondefault_actions": sum(row["nondefault_action_rows"] > 0 for row in task_packets),
        "packets_with_three_or_more_action_classes": sum(row["action_class_count"] >= 3 for row in task_packets),
        "operation_stack_beats_flat_work_tasks": sum(row["operation_stack_beats_flat_work"] for row in task_packets),
        "operation_stack_beats_fixed_recall_tasks": sum(row["operation_stack_beats_fixed_recall"] for row in task_packets),
        "operation_stack_fewer_groups_than_fixed_tasks": sum(row["operation_stack_has_fewer_groups_than_fixed"] for row in task_packets),
        "median_top5_work": float(median(top5_work)),
        "max_top5_work": max(top5_work),
        "median_first_positive_work": float(median(first_work)),
        "median_top5_recall": float(median(top5_recall)),
        "median_top5_lift": float(median(top5_lift)),
        "nondefault_objective_rows": len(nondefault_objectives),
        "visible_non_oracle_best_rows": len(visible_best),
        "median_nondefault_gain_over_default": float(median(row["gain_over_default"] for row in nondefault_objectives))
        if nondefault_objectives
        else 0.0,
        "max_gain_over_default": max(row["gain_over_default"] for row in objective_packets),
        "r349_aligned_transfer_decisions": transfer_summary["aligned_decisions"],
        "r349_selected_within_tolerance": transfer_summary["selected_within_tolerance"],
        "r349_selected_action_exact": transfer_summary["selected_action_exact"],
        "r349_nondefault_target_within_tolerance": transfer_summary["nondefault_target_within_tolerance"],
        "network_access_required": False,
    }


def build_budget_summary(summary: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "claim_test": "localized_positive_evidence",
            "metric": "top5_positive_tasks",
            "value": summary["packets_with_top5_positive"],
            "denominator": summary["tasks"],
            "interpretation": "top operation-stack packet contains at least one positive group",
        },
        {
            "claim_test": "strict_inspection_budget",
            "metric": "top5_work_le_30pct",
            "value": summary["packets_with_30pct_work_budget"],
            "denominator": summary["tasks"],
            "interpretation": "top five stack groups inspect <=30% of operations",
        },
        {
            "claim_test": "first_positive_budget",
            "metric": "first_positive_work_le_10pct",
            "value": summary["packets_with_first_positive_10pct_budget"],
            "denominator": summary["tasks"],
            "interpretation": "first positive appears within 10% operation work",
        },
        {
            "claim_test": "less_work_than_flat",
            "metric": "operation_stack_beats_flat_top5_work",
            "value": summary["operation_stack_beats_flat_work_tasks"],
            "denominator": summary["tasks"],
            "interpretation": "operation-stack top-5 requires less operation work than flat summary",
        },
        {
            "claim_test": "less_fragmented_than_fixed",
            "metric": "operation_stack_fewer_groups_than_fixed",
            "value": summary["operation_stack_fewer_groups_than_fixed_tasks"],
            "denominator": summary["tasks"],
            "interpretation": "operation-stack has fewer ranked groups than fixed-session tree",
        },
        {
            "claim_test": "actionable_counterfactual",
            "metric": "nondefault_objective_rows",
            "value": summary["nondefault_objective_rows"],
            "denominator": summary["objective_rows"],
            "interpretation": "offline objective rows where a visible non-default knob improves the default",
        },
        {
            "claim_test": "held_out_guardrail",
            "metric": "selected_within_tolerance",
            "value": summary["r349_selected_within_tolerance"],
            "denominator": summary["r349_aligned_transfer_decisions"],
            "interpretation": "held-out policy selection is a partial proxy, not an exact action selector",
        },
    ]


def build_markdown(path: Path, payload: dict[str, Any]) -> None:
    summary = payload["summary"]
    lines = [
        "# R350 Evidence-Packet Budget Audit",
        "",
        "R350 checks whether existing profiler outputs form bounded diagnostic packets",
        "over real labeled agent traces. Each packet joins top-ranked operation-stack",
        "evidence, baseline counterpoints, action counterfactuals, and a held-out",
        "transfer guardrail. Hidden labels are used only through already-scored",
        "artifacts, not to rank deployment-time traces.",
        "",
        "## Summary",
        "",
        f"- Overall: {summary['overall']}.",
        f"- Tasks / datasets / objective rows: {summary['tasks']} / {summary['datasets']} / {summary['objective_rows']}.",
        f"- Top-5 operation-stack packets contain positives on {summary['packets_with_top5_positive']}/{summary['tasks']} tasks; top-1 contains positives on {summary['packets_with_top1_positive']}/{summary['tasks']}.",
        f"- Strict 30% operation-work budget holds on {summary['packets_with_30pct_work_budget']}/{summary['tasks']} tasks; first-positive <=10% work holds on {summary['packets_with_first_positive_10pct_budget']}/{summary['tasks']}.",
        f"- Median top-5 work / recall / lift: {summary['median_top5_work']:.4f} / {summary['median_top5_recall']:.4f} / {summary['median_top5_lift']:.4f}.",
        f"- Operation-stack beats flat top-5 work on {summary['operation_stack_beats_flat_work_tasks']}/{summary['tasks']} tasks and has fewer groups than fixed-session on {summary['operation_stack_fewer_groups_than_fixed_tasks']}/{summary['tasks']} tasks.",
        f"- Non-default visible action rows: {summary['nondefault_objective_rows']}/{summary['objective_rows']}; median non-default gain over default: {summary['median_nondefault_gain_over_default']:.4f}.",
        f"- Held-out action transfer is partial: {summary['r349_selected_within_tolerance']}/{summary['r349_aligned_transfer_decisions']} within tolerance and {summary['r349_selected_action_exact']}/{summary['r349_aligned_transfer_decisions']} exact action.",
        "",
        "## Task Packets",
        "",
        "| Task | Verdict | Top-5 work | Top-5 recall | First-positive work | Non-default rows | Counterpoints |",
        "|---|---|---:|---:|---:|---:|---|",
    ]
    for row in payload["task_packets"]:
        lines.append(
            f"| {row['task']} | {row['packet_verdict']} | {row['top5_work']:.4f} | "
            f"{row['top5_recall']:.4f} | {row['first_positive_work']:.4f} | "
            f"{row['nondefault_action_rows']} | {'; '.join(row['baseline_counterpoints'])} |"
        )
    lines.extend(
        [
            "",
            "## Claim Scope",
            "",
            "- Supports: operation/operation-stack profiler output can localize positives, expose counterpoints, and identify actionable knobs under bounded inspection budgets on real labeled traces.",
            "- Narrows: two tasks exceed the strict 30% work budget, and held-out action transfer is only a partial proxy.",
            "- Excludes: human utility, label-free universal action selection, complete intent-boundary recovery, and complete trace-ecosystem compatibility.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_html(path: Path, payload: dict[str, Any]) -> None:
    summary = payload["summary"]

    def table(rows: list[dict[str, Any]], fields: list[str]) -> str:
        head = "".join(f"<th>{html.escape(field)}</th>" for field in fields)
        body = []
        for row in rows:
            body.append(
                "<tr>"
                + "".join(f"<td>{html.escape(str(format_value(row.get(field, ''))))}</td>" for field in fields)
                + "</tr>"
            )
        return f"<table><thead><tr>{head}</tr></thead><tbody>{''.join(body)}</tbody></table>"

    content = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>R350 Evidence-Packet Budget Audit</title>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, sans-serif; margin: 32px; line-height: 1.45; color: #202124; }}
    table {{ border-collapse: collapse; width: 100%; margin: 16px 0; font-size: 13px; }}
    th, td {{ border: 1px solid #d0d7de; padding: 6px 8px; text-align: left; vertical-align: top; }}
    th {{ background: #f6f8fa; }}
  </style>
</head>
<body>
  <h1>R350 Evidence-Packet Budget Audit</h1>
  <p><strong>Overall:</strong> {html.escape(summary['overall'])}. Top-5 packets contain positives on {summary['packets_with_top5_positive']}/{summary['tasks']} tasks; strict 30% work budget holds on {summary['packets_with_30pct_work_budget']}/{summary['tasks']} tasks.</p>
  <h2>Summary</h2>
  {table([summary], ['tasks', 'datasets', 'objective_rows', 'packets_with_top5_positive', 'packets_with_30pct_work_budget', 'median_top5_work', 'median_top5_recall', 'nondefault_objective_rows', 'r349_selected_within_tolerance', 'r349_selected_action_exact'])}
  <h2>Task Packets</h2>
  {table(payload['task_packets'], ['task', 'packet_verdict', 'top5_work', 'top5_recall', 'first_positive_work', 'nondefault_action_rows', 'baseline_counterpoints', 'optimization_action'])}
</body>
</html>
"""
    path.write_text(content, encoding="utf-8")


def build_payload() -> dict[str, Any]:
    source_status = ensure_sources_tracked_clean(list(SOURCE_ARTIFACTS.values()))
    reports = {
        "R346": load_json(SOURCE_ARTIFACTS["R346 report"]),
        "R347": load_json(SOURCE_ARTIFACTS["R347 report"]),
        "R348": load_json(SOURCE_ARTIFACTS["R348 report"]),
        "R349": load_json(SOURCE_ARTIFACTS["R349 report"]),
    }
    r346_cards = read_csv(SOURCE_ARTIFACTS["R346 task cards"])
    r347_cards = read_csv(SOURCE_ARTIFACTS["R347 task cards"])
    r348_cards = read_csv(SOURCE_ARTIFACTS["R348 task cards"])
    r349_cards = read_csv(SOURCE_ARTIFACTS["R349 task cards"])
    action_summary = read_csv(SOURCE_ARTIFACTS["R348 action summary"])
    objective_rows = read_csv(SOURCE_ARTIFACTS["R348 objective counterfactuals"])
    top_stack_summary = summarize_top_stack_evidence(read_csv(SOURCE_ARTIFACTS["R346 top stack evidence"]))

    task_packets = build_task_packets(r346_cards, r347_cards, r348_cards, r349_cards, top_stack_summary)
    objective_packets = build_objective_packets(objective_rows, task_packets)
    summary = build_summary(task_packets, objective_packets, action_summary, reports)

    return {
        "schema": "agentsight.operation-evidence-packet.v1",
        "run_id": RUN_ID,
        "input_policy": {
            "dataset_sync": "none",
            "dataset_creation": "none",
            "dataset_relabeling": "none",
            "network_access_required": False,
            "hidden_label_use": "reads already-scored R346-R349 artifacts; hidden labels are used only for offline scoring and never for visible ranking",
        },
        "profiler_abstractions": ["operation", "operation stack"],
        "source_status": source_status,
        "summary": summary,
        "budget_summary": build_budget_summary(summary),
        "task_packets": task_packets,
        "objective_packets": objective_packets,
        "claim_scope": {
            "supported": "bounded evidence packets can combine operation-stack localization, counterpoint views, and action counterfactuals on real labeled traces",
            "narrowed": "strict operation-work budgets have high-prevalence and boundary-task exceptions, and held-out action transfer is only a partial proxy",
            "not_supported": "human utility, label-free universal action selection, complete intent-boundary recovery, or complete trace-ecosystem compatibility",
        },
    }


def main() -> None:
    args = parse_args()
    out_dir = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    payload = build_payload()

    write_json(out_dir / "evidence-packet-report.json", payload)
    build_markdown(out_dir / "evidence-packet-report.md", payload)
    build_html(out_dir / "index.html", payload)
    write_csv(
        out_dir / "task-evidence-packets.csv",
        payload["task_packets"],
        [
            "task",
            "dataset",
            "query_family",
            "operations",
            "positives",
            "prevalence",
            "operation_stack_groups",
            "evidence_groups_inspected",
            "top_stack_positive_groups",
            "top_stack_positive_operations",
            "top_stack_group_ids",
            "top1_positive",
            "top5_positive",
            "top5_recall",
            "top5_precision",
            "top5_lift",
            "top5_work",
            "first_positive_rank",
            "first_positive_work",
            "top5_work_le_30pct",
            "first_positive_work_le_10pct",
            "flat_top5_work",
            "fixed_session_top5_recall",
            "operation_stack_beats_flat_work",
            "operation_stack_beats_fixed_recall",
            "operation_stack_has_fewer_groups_than_fixed",
            "baseline_counterpoints",
            "nondefault_action_rows",
            "default_best_rows",
            "action_class_count",
            "action_classes",
            "median_gain_over_default",
            "max_gain_over_default",
            "optimization_action",
            "useful_stack_fields",
            "leave_task_within_tolerance",
            "leave_task_exact_action",
            "leave_task_beats_default",
            "leave_dataset_within_tolerance",
            "leave_dataset_exact_action",
            "leave_dataset_beats_default",
            "transfer_guardrail",
            "packet_verdict",
        ],
    )
    write_csv(
        out_dir / "objective-evidence-packets.csv",
        payload["objective_packets"],
        [
            "task",
            "dataset",
            "query_family",
            "objective",
            "metric",
            "default_policy",
            "best_policy",
            "best_view",
            "best_ranker",
            "action_class",
            "gain_over_default",
            "default_is_best",
            "best_is_visible_non_oracle",
            "top5_positive",
            "top5_work",
            "packet_verdict",
            "optimization_action",
            "counterpoints",
        ],
    )
    write_csv(
        out_dir / "budget-summary.csv",
        payload["budget_summary"],
        ["claim_test", "metric", "value", "denominator", "interpretation"],
    )
    write_json(
        out_dir / "run-result.json",
        {
            "run_id": RUN_ID,
            "schema": payload["schema"],
            "summary": payload["summary"],
        },
    )
    print(json.dumps(round_value(payload["summary"]), indent=2, sort_keys=True))
    if payload["summary"]["overall"] != "pass":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
