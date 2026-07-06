#!/usr/bin/env python3
"""R348: action-counterfactual audit over existing labeled agent traces.

This audit does not fetch, sync, create, or relabel datasets. It reads tracked
R335/R341/R347 artifacts, treats hidden labels as an offline scoring oracle over
already-scored visible policies, and asks which profiler knobs would have to
change to improve a default operation-stack diagnosis.
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
from statistics import median
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OUT_ROOT = ROOT / "docs" / "visexp" / "out"
R335_DIR = OUT_ROOT / "operation-actionability-synthesis-r335"
R341_DIR = OUT_ROOT / "operation-mechanism-attribution-r341"
R347_DIR = OUT_ROOT / "operation-case-baseline-contrast-r347"
DEFAULT_OUT_DIR = OUT_ROOT / "operation-action-counterfactual-r348"
RUN_ID = "R348"
DEFAULT_POLICY = "operation_stack:query_aware"

SOURCE_ARTIFACTS = {
    "R335 report": R335_DIR / "actionability-synthesis-report.json",
    "R335 task cards": R335_DIR / "task-actionability-cards.csv",
    "R341 report": R341_DIR / "mechanism-attribution-report.json",
    "R341 objective attribution": R341_DIR / "objective-mechanism-attribution.csv",
    "R347 report": R347_DIR / "case-baseline-contrast-report.json",
    "R347 task cards": R347_DIR / "task-baseline-contrast-cards.csv",
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


def as_float(value: Any) -> float:
    if value in ("", None):
        return 0.0
    return float(value)


def as_bool(value: str | bool) -> bool:
    if isinstance(value, bool):
        return value
    return value.lower() == "true"


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


def policy_is_visible_non_oracle(policy: str) -> bool:
    return "oracle" not in policy and not policy.startswith("label_drilldown:")


def action_class(row: dict[str, str]) -> str:
    best_policy = row["best_policy"]
    best_view = row["best_view"]
    best_ranker = row["best_ranker"]
    if best_policy == DEFAULT_POLICY:
        return "keep_default_operation_stack"
    if best_view == "operation_stack":
        if best_ranker != "query_aware":
            return "retune_operation_stack_ranker"
        return "retune_operation_stack_mapping_or_depth"
    if best_view == "fixed_session":
        return "drill_down_fixed_session"
    if best_view == "flat":
        return "use_flat_full_recall_counterpoint"
    if best_view == "dataset_native":
        return "use_dataset_native_hierarchy"
    if best_view == "raw_action_stack":
        return "use_raw_action_mapping_counterpoint"
    return f"use_{best_view}"


def split_items(value: str) -> list[str]:
    return [item.strip() for item in value.split(";") if item.strip()]


def counterfactual_rows(objective_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in objective_rows:
        default_regret = as_float(row["operation_stack_query_aware_regret"])
        best_policy = row["best_policy"]
        default_is_best = best_policy == DEFAULT_POLICY
        best_is_visible = policy_is_visible_non_oracle(best_policy)
        row_action = action_class(row)
        mechanism_labels = split_items(row.get("mechanism_labels", ""))
        rows.append(
            {
                "task": row["task"],
                "dataset": row["dataset"],
                "query_family": row["query_family"],
                "objective": row["objective"],
                "metric": row["metric"],
                "direction": row["direction"],
                "default_policy": DEFAULT_POLICY,
                "best_policy": best_policy,
                "best_policy_class": row["best_policy_class"],
                "best_view": row["best_view"],
                "best_ranker": row["best_ranker"],
                "best_value": as_float(row["best_value"]),
                "default_value": as_float(row["operation_stack_query_aware_value"]),
                "gain_over_default": default_regret,
                "default_is_best": default_is_best,
                "best_is_visible_non_oracle": best_is_visible,
                "action_class": row_action,
                "changes_view": row["best_view"] != "operation_stack",
                "changes_ranker": row["best_view"] == "operation_stack" and row["best_ranker"] != "query_aware",
                "mechanism_labels": mechanism_labels,
                "mechanism_count": int(row["mechanism_count"]),
                "optimization_action": row["optimization_action"],
                "counterpoints": split_items(row.get("counterpoints", "")),
                "actionable": as_bool(row["actionable"]),
            }
        )
    return rows


def build_action_summary(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_action: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_action[row["action_class"]].append(row)
    summary = []
    for action, action_rows in sorted(by_action.items()):
        gains = [row["gain_over_default"] for row in action_rows]
        tasks = sorted({row["task"] for row in action_rows})
        summary.append(
            {
                "action_class": action,
                "objective_rows": len(action_rows),
                "tasks": len(tasks),
                "median_gain_over_default": float(median(gains)) if gains else 0.0,
                "max_gain_over_default": max(gains) if gains else 0.0,
                "example_tasks": tasks[:6],
            }
        )
    return summary


def build_task_cards(
    rows: list[dict[str, Any]],
    r335_task_cards: list[dict[str, str]],
    r347_task_cards: list[dict[str, str]],
) -> list[dict[str, Any]]:
    rows_by_task: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        rows_by_task[row["task"]].append(row)
    r335_by_task = {row["task"]: row for row in r335_task_cards}
    r347_by_task = {row["task"]: row for row in r347_task_cards}
    cards: list[dict[str, Any]] = []
    for task, task_rows in sorted(rows_by_task.items()):
        gains = [row["gain_over_default"] for row in task_rows]
        nondefault = [row for row in task_rows if not row["default_is_best"]]
        action_classes = sorted({row["action_class"] for row in task_rows})
        case = r347_by_task[task]
        synthesis = r335_by_task[task]
        cards.append(
            {
                "task": task,
                "dataset": task_rows[0]["dataset"],
                "query_family": task_rows[0]["query_family"],
                "objective_rows": len(task_rows),
                "nondefault_action_rows": len(nondefault),
                "default_best_rows": len(task_rows) - len(nondefault),
                "action_class_count": len(action_classes),
                "action_classes": action_classes,
                "median_gain_over_default": float(median(gains)) if gains else 0.0,
                "max_gain_over_default": max(gains) if gains else 0.0,
                "operation_stack_top5_recall": as_float(case["operation_stack_top5_recall"]),
                "operation_stack_top5_work": as_float(case["operation_stack_top5_work"]),
                "operation_stack_top5_lift": as_float(case["operation_stack_top5_lift"]),
                "operation_stack_top1_positive": as_bool(case["operation_stack_top1_positive"]),
                "operation_stack_beats_flat_work": as_bool(case["operation_stack_beats_flat_work"]),
                "operation_stack_beats_fixed_recall": as_bool(case["operation_stack_beats_fixed_recall"]),
                "operation_stack_has_fewer_groups_than_fixed": as_bool(case["operation_stack_has_fewer_groups_than_fixed"]),
                "case_counterpoints": case["counterpoints"],
                "optimization_action": synthesis["optimization_action"],
                "useful_stack_fields": synthesis["useful_stack_fields"],
                "counterfactual_verdict": "actionable_with_counterpoints"
                if nondefault and case["counterpoints"]
                else "actionable",
            }
        )
    return cards


def build_markdown(path: Path, payload: dict[str, Any]) -> None:
    summary = payload["summary"]
    lines = [
        "# R348 Action-Counterfactual Audit",
        "",
        "R348 asks whether the profiler's actionability cards correspond to measurable",
        "counterfactual changes in already-scored visible policies. It does not fetch,",
        "sync, create, or relabel datasets, and it does not turn hidden labels into a",
        "deployment selector.",
        "",
        "## Summary",
        "",
        f"- Overall: {summary['overall']}.",
        f"- Objective rows: {summary['objective_rows']}.",
        f"- Non-default action rows: {summary['nondefault_action_rows']}.",
        f"- Rows where the best policy is visible and non-oracle: {summary['visible_non_oracle_best_rows']}.",
        f"- Objective rows requiring a view change: {summary['view_change_rows']}.",
        f"- Objective rows requiring operation-stack ranker/depth tuning: {summary['operation_stack_tuning_rows']}.",
        f"- Tasks with at least three action classes: {summary['tasks_with_three_or_more_action_classes']}.",
        f"- Median default regret: {summary['median_gain_over_default']}.",
        "",
        "## Action Classes",
        "",
        "| Action class | Rows | Tasks | Median gain | Max gain |",
        "|---|---:|---:|---:|---:|",
    ]
    for row in payload["action_class_summary"]:
        lines.append(
            f"| {row['action_class']} | {row['objective_rows']} | {row['tasks']} | "
            f"{row['median_gain_over_default']} | {row['max_gain_over_default']} |"
        )
    lines.extend(["", "## Task Cards", "", "| Task | Non-default rows | Action classes | Case counterpoints |", "|---|---:|---|---|"])
    for row in payload["task_cards"]:
        lines.append(
            f"| {row['task']} | {row['nondefault_action_rows']} | "
            f"{'; '.join(row['action_classes'])} | {row['case_counterpoints']} |"
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
  <title>R348 Action-Counterfactual Audit</title>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, sans-serif; margin: 32px; line-height: 1.45; }}
    table {{ border-collapse: collapse; width: 100%; margin: 16px 0; font-size: 13px; }}
    th, td {{ border: 1px solid #d0d7de; padding: 6px 8px; text-align: left; vertical-align: top; }}
    th {{ background: #f6f8fa; }}
  </style>
</head>
<body>
  <h1>R348 Action-Counterfactual Audit</h1>
  <p><strong>Overall:</strong> {html.escape(summary['overall'])}</p>
  <h2>Summary</h2>
  {table([summary], ['tasks', 'objective_rows', 'nondefault_action_rows', 'visible_non_oracle_best_rows', 'view_change_rows', 'operation_stack_tuning_rows', 'tasks_with_three_or_more_action_classes', 'median_gain_over_default'])}
  <h2>Action Classes</h2>
  {table(payload['action_class_summary'], ['action_class', 'objective_rows', 'tasks', 'median_gain_over_default', 'max_gain_over_default'])}
  <h2>Task Cards</h2>
  {table(payload['task_cards'], ['task', 'nondefault_action_rows', 'action_class_count', 'action_classes', 'case_counterpoints'])}
</body>
</html>
"""
    path.write_text(content, encoding="utf-8")


def build_payload() -> dict[str, Any]:
    source_status = ensure_sources_tracked_clean(list(SOURCE_ARTIFACTS.values()))
    r335_report = load_json(SOURCE_ARTIFACTS["R335 report"])
    r341_report = load_json(SOURCE_ARTIFACTS["R341 report"])
    r347_report = load_json(SOURCE_ARTIFACTS["R347 report"])
    objective_rows = read_csv(SOURCE_ARTIFACTS["R341 objective attribution"])
    r335_task_cards = read_csv(SOURCE_ARTIFACTS["R335 task cards"])
    r347_task_cards = read_csv(SOURCE_ARTIFACTS["R347 task cards"])

    objective_counterfactuals = counterfactual_rows(objective_rows)
    action_summary = build_action_summary(objective_counterfactuals)
    task_cards = build_task_cards(objective_counterfactuals, r335_task_cards, r347_task_cards)
    gains = [row["gain_over_default"] for row in objective_counterfactuals]
    nondefault_rows = [row for row in objective_counterfactuals if not row["default_is_best"]]
    view_change_rows = [row for row in objective_counterfactuals if row["changes_view"]]
    stack_tuning_rows = [
        row
        for row in objective_counterfactuals
        if row["action_class"] in {"retune_operation_stack_ranker", "retune_operation_stack_mapping_or_depth"}
    ]
    visible_best_rows = [row for row in objective_counterfactuals if row["best_is_visible_non_oracle"]]
    non_operation_stack_rows = [row for row in objective_counterfactuals if row["best_view"] != "operation_stack"]
    tasks_with_three_classes = [row for row in task_cards if row["action_class_count"] >= 3]
    summary = {
        "overall": "pass"
        if len(objective_counterfactuals) == 36
        and len(task_cards) == 6
        and len(visible_best_rows) == 36
        and all(row["counterfactual_verdict"] == "actionable_with_counterpoints" for row in task_cards)
        else "fail",
        "tasks": len(task_cards),
        "datasets": len({row["dataset"] for row in objective_counterfactuals}),
        "objective_rows": len(objective_counterfactuals),
        "nondefault_action_rows": len(nondefault_rows),
        "default_best_rows": len(objective_counterfactuals) - len(nondefault_rows),
        "visible_non_oracle_best_rows": len(visible_best_rows),
        "view_change_rows": len(view_change_rows),
        "operation_stack_tuning_rows": len(stack_tuning_rows),
        "non_operation_stack_counterpoint_rows": len(non_operation_stack_rows),
        "tasks_with_nondefault_actions": sum(row["nondefault_action_rows"] > 0 for row in task_cards),
        "tasks_with_three_or_more_action_classes": len(tasks_with_three_classes),
        "tasks_with_case_counterpoints": sum(bool(row["case_counterpoints"]) for row in task_cards),
        "median_gain_over_default": float(median(gains)) if gains else 0.0,
        "median_nondefault_gain_over_default": float(median(row["gain_over_default"] for row in nondefault_rows))
        if nondefault_rows
        else 0.0,
        "max_gain_over_default": max(gains) if gains else 0.0,
        "r335_actionability_cards": r335_report["summary"]["actionability_cards"],
        "r341_actionable_objective_rows": r341_report["summary"]["actionable_objective_rows"],
        "r347_visible_views": r347_report["summary"]["visible_views"],
        "network_access_required": False,
    }

    return {
        "schema": "agentsight.operation-action-counterfactual.v1",
        "run_id": RUN_ID,
        "input_policy": {
            "dataset_sync": "none",
            "dataset_creation": "none",
            "dataset_relabeling": "none",
            "network_access_required": False,
            "hidden_label_use": "reads already-scored visible policy artifacts; labels are used only to score counterfactual objective rows, not to rank deployment traces",
        },
        "profiler_abstractions": ["operation", "operation stack"],
        "non_claims": [
            "not a human/agent analyst study",
            "not a label-free automatic selector",
            "not proof that one view dominates all objectives",
            "not complete trace-ecosystem compatibility evidence",
        ],
        "source_status": source_status,
        "summary": summary,
        "action_class_summary": action_summary,
        "objective_counterfactuals": objective_counterfactuals,
        "task_cards": task_cards,
    }


def main() -> None:
    args = parse_args()
    out_dir = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    payload = build_payload()
    write_json(out_dir / "action-counterfactual-report.json", payload)
    build_markdown(out_dir / "action-counterfactual-report.md", payload)
    build_html(out_dir / "index.html", payload)
    write_csv(
        out_dir / "objective-counterfactuals.csv",
        payload["objective_counterfactuals"],
        [
            "task",
            "dataset",
            "query_family",
            "objective",
            "metric",
            "direction",
            "default_policy",
            "best_policy",
            "best_policy_class",
            "best_view",
            "best_ranker",
            "best_value",
            "default_value",
            "gain_over_default",
            "default_is_best",
            "best_is_visible_non_oracle",
            "action_class",
            "changes_view",
            "changes_ranker",
            "mechanism_labels",
            "mechanism_count",
            "optimization_action",
            "counterpoints",
            "actionable",
        ],
    )
    write_csv(
        out_dir / "action-class-summary.csv",
        payload["action_class_summary"],
        ["action_class", "objective_rows", "tasks", "median_gain_over_default", "max_gain_over_default", "example_tasks"],
    )
    write_csv(
        out_dir / "task-action-counterfactual-cards.csv",
        payload["task_cards"],
        [
            "task",
            "dataset",
            "query_family",
            "objective_rows",
            "nondefault_action_rows",
            "default_best_rows",
            "action_class_count",
            "action_classes",
            "median_gain_over_default",
            "max_gain_over_default",
            "operation_stack_top5_recall",
            "operation_stack_top5_work",
            "operation_stack_top5_lift",
            "operation_stack_top1_positive",
            "operation_stack_beats_flat_work",
            "operation_stack_beats_fixed_recall",
            "operation_stack_has_fewer_groups_than_fixed",
            "case_counterpoints",
            "optimization_action",
            "useful_stack_fields",
            "counterfactual_verdict",
        ],
    )
    write_json(
        out_dir / "run-result.json",
        {
            "run_id": RUN_ID,
            "schema": payload["schema"],
            "summary": payload["summary"],
        },
    )
    print(json.dumps(payload["summary"], indent=2, sort_keys=True))
    if payload["summary"]["overall"] != "pass":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
