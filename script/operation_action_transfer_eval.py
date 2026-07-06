#!/usr/bin/env python3
"""R349: held-out action-transfer audit over existing labeled traces.

R348 asks which action class would improve each task/objective when the target
labels are available offline. R349 asks a stricter question: if R340 selects a
visible policy from non-target tasks/families, does that policy imply the same
action class on the held-out target, or at least land within the target metric
tolerance?

The audit reads only tracked R340/R348 artifacts. It does not fetch, sync,
create, or relabel datasets, and it does not convert hidden labels into a
deployment-time action selector.
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
from statistics import median
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OUT_ROOT = ROOT / "docs" / "visexp" / "out"
R340_DIR = OUT_ROOT / "operation-policy-transfer-r340"
R348_DIR = OUT_ROOT / "operation-action-counterfactual-r348"
DEFAULT_OUT_DIR = OUT_ROOT / "operation-action-transfer-r349"
RUN_ID = "R349"

DEFAULT_POLICY = "operation_stack:query_aware"
DEFAULT_ACTION_CLASS = "keep_default_operation_stack"

SOURCE_ARTIFACTS = {
    "R340 report": R340_DIR / "policy-transfer-report.json",
    "R340 transfer decisions": R340_DIR / "transfer-decisions.csv",
    "R340 objective summary": R340_DIR / "objective-transfer-summary.csv",
    "R348 report": R348_DIR / "action-counterfactual-report.json",
    "R348 objective counterfactuals": R348_DIR / "objective-counterfactuals.csv",
    "R348 action summary": R348_DIR / "action-class-summary.csv",
}

OBJECTIVE_MAP = {
    "budget30_operation_recall": "budget30_recall",
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


def as_bool(value: str | bool) -> bool:
    if isinstance(value, bool):
        return value
    return value.lower() == "true"


def as_float(value: Any) -> float | None:
    if value in ("", None):
        return None
    return float(value)


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
    if isinstance(value, (dict, list)):
        return json.dumps(round_value(value), sort_keys=True)
    return value


def policy_view(policy: str) -> str:
    return policy.split(":", 1)[0]


def policy_ranker(policy: str) -> str:
    return policy.split(":", 1)[1]


def policy_is_visible_non_oracle(policy: str) -> bool:
    return "oracle" not in policy and not policy.startswith("label_drilldown:")


def objective_for_r348(objective: str) -> str:
    return OBJECTIVE_MAP.get(objective, objective)


def action_class_for_policy(policy: str) -> str:
    view = policy_view(policy)
    ranker = policy_ranker(policy)
    if policy == DEFAULT_POLICY:
        return DEFAULT_ACTION_CLASS
    if view == "operation_stack":
        if ranker == "query_aware":
            return "retune_operation_stack_mapping_or_depth"
        return "retune_operation_stack_ranker"
    if view == "fixed_session":
        return "drill_down_fixed_session"
    if view == "flat":
        return "use_flat_full_recall_counterpoint"
    if view == "dataset_native":
        return "use_dataset_native_hierarchy"
    if view == "raw_action_stack":
        return "use_raw_action_mapping_counterpoint"
    return f"use_{view}"


def action_verdict(row: dict[str, Any]) -> str:
    if row["selected_action_exact"]:
        return "exact_action"
    if row["selected_within_tolerance"]:
        return "metric_within_tolerance"
    if row["selected_beats_default"]:
        return "beats_default_only"
    return "miss"


def group_by(rows: list[dict[str, Any]], keys: list[str]) -> dict[tuple[Any, ...], list[dict[str, Any]]]:
    groups: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[tuple(row[key] for key in keys)].append(row)
    return groups


def summarize_group(rows: list[dict[str, Any]], prefix: dict[str, Any]) -> dict[str, Any]:
    deltas = [row["selected_delta_vs_best"] for row in rows if row["selected_delta_vs_best"] is not None]
    return {
        **prefix,
        "decisions": len(rows),
        "selected_action_exact": sum(row["selected_action_exact"] for row in rows),
        "selected_r348_policy_exact": sum(row["selected_r348_policy_exact"] for row in rows),
        "selected_view_exact": sum(row["selected_view_exact"] for row in rows),
        "selected_ranker_exact": sum(row["selected_ranker_exact"] for row in rows),
        "selected_within_tolerance": sum(row["selected_within_tolerance"] for row in rows),
        "selected_beats_default": sum(row["selected_beats_default"] for row in rows),
        "default_within_tolerance": sum(row["default_within_tolerance"] for row in rows),
        "target_best_nondefault": sum(row["target_best_nondefault"] for row in rows),
        "nondefault_target_action_exact": sum(
            row["selected_action_exact"] and row["target_best_nondefault"] for row in rows
        ),
        "nondefault_target_within_tolerance": sum(
            row["selected_within_tolerance"] and row["target_best_nondefault"] for row in rows
        ),
        "nondefault_target_selected_default_action": sum(
            row["target_best_nondefault"] and row["selected_action_class"] == DEFAULT_ACTION_CLASS for row in rows
        ),
        "median_delta_vs_best": float(median(deltas)) if deltas else None,
    }


def align_decisions(
    transfer_decisions: list[dict[str, str]],
    r348_rows: list[dict[str, str]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    r348_by_key = {(row["task"], row["objective"]): row for row in r348_rows}
    aligned: list[dict[str, Any]] = []
    excluded: list[dict[str, Any]] = []
    seen_r348_keys: set[tuple[str, str]] = set()

    for decision in transfer_decisions:
        mapped_objective = objective_for_r348(decision["objective"])
        r348 = r348_by_key.get((decision["task"], mapped_objective))
        if r348 is None:
            reason = (
                "sequence_objective_not_in_r348"
                if decision["objective"].startswith("sequence_")
                else "no_r348_counterfactual_objective"
            )
            excluded.append(
                {
                    "protocol": decision["protocol"],
                    "task": decision["task"],
                    "dataset": decision["dataset"],
                    "query_family": decision["query_family"],
                    "objective": decision["objective"],
                    "mapped_objective": mapped_objective,
                    "reason": reason,
                    "selected_policy": decision["selected_policy"],
                    "best_visible_policy": decision["best_visible_policy"],
                }
            )
            continue

        seen_r348_keys.add((r348["task"], r348["objective"]))
        selected_policy = decision["selected_policy"]
        selected_action = action_class_for_policy(selected_policy)
        best_action = r348["action_class"]
        row: dict[str, Any] = {
            "protocol": decision["protocol"],
            "task": decision["task"],
            "dataset": decision["dataset"],
            "query_family": decision["query_family"],
            "objective": decision["objective"],
            "mapped_objective": mapped_objective,
            "metric": decision["metric"],
            "direction": decision["direction"],
            "selected_policy": selected_policy,
            "selected_view": policy_view(selected_policy),
            "selected_ranker": policy_ranker(selected_policy),
            "selected_action_class": selected_action,
            "selected_target_value": as_float(decision["selected_target_value"]),
            "selected_target_rank": int(decision["selected_target_rank"]),
            "best_r340_policy": decision["best_visible_policy"],
            "best_r340_value": as_float(decision["best_visible_value"]),
            "best_r348_policy": r348["best_policy"],
            "best_r348_view": r348["best_view"],
            "best_r348_ranker": r348["best_ranker"],
            "best_r348_action_class": best_action,
            "best_r348_value": as_float(r348["best_value"]),
            "default_value": as_float(decision["default_value"]),
            "default_action_class": DEFAULT_ACTION_CLASS,
            "r340_r348_best_policy_match": decision["best_visible_policy"] == r348["best_policy"],
            "selected_visible_non_oracle": policy_is_visible_non_oracle(selected_policy),
            "best_r348_visible_non_oracle": as_bool(r348["best_is_visible_non_oracle"]),
            "selected_r340_exact_best": as_bool(decision["selected_exact_best"]),
            "selected_r348_policy_exact": selected_policy == r348["best_policy"],
            "selected_action_exact": selected_action == best_action,
            "selected_view_exact": policy_view(selected_policy) == r348["best_view"],
            "selected_ranker_exact": policy_ranker(selected_policy) == r348["best_ranker"],
            "selected_within_tolerance": as_bool(decision["selected_within_tolerance"]),
            "selected_delta_vs_best": as_float(decision["selected_delta_vs_best"]),
            "selected_delta_vs_default": as_float(decision["selected_delta_vs_default"]),
            "selected_beats_default": as_bool(decision["selected_beats_default"]),
            "default_within_tolerance": as_bool(decision["default_within_tolerance"]),
            "target_best_nondefault": best_action != DEFAULT_ACTION_CLASS,
            "r348_gain_over_default": as_float(r348["gain_over_default"]),
            "r348_optimization_action": r348["optimization_action"],
            "r348_counterpoints": r348["counterpoints"],
        }
        row["action_transfer_verdict"] = action_verdict(row)
        aligned.append(row)

    untransferred_r348 = [
        {
            "task": row["task"],
            "dataset": row["dataset"],
            "query_family": row["query_family"],
            "objective": row["objective"],
            "best_policy": row["best_policy"],
            "action_class": row["action_class"],
            "reason": "r348_objective_not_in_r340_transfer",
        }
        for row in r348_rows
        if (row["task"], row["objective"]) not in seen_r348_keys
    ]
    return aligned, excluded, untransferred_r348


def build_summary_rows(aligned: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = [summarize_group(aligned, {"scope": "all", "protocol": "all", "objective": "all"})]
    for (protocol,), group in sorted(group_by(aligned, ["protocol"]).items()):
        rows.append(summarize_group(group, {"scope": "protocol", "protocol": protocol, "objective": "all"}))
    for (protocol, objective), group in sorted(group_by(aligned, ["protocol", "mapped_objective"]).items()):
        rows.append(summarize_group(group, {"scope": "objective", "protocol": protocol, "objective": objective}))
    return rows


def build_confusion_rows(aligned: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for (selected, best), group in sorted(group_by(aligned, ["selected_action_class", "best_r348_action_class"]).items()):
        rows.append(
            {
                "selected_action_class": selected,
                "best_action_class": best,
                "decisions": len(group),
                "selected_within_tolerance": sum(row["selected_within_tolerance"] for row in group),
                "selected_beats_default": sum(row["selected_beats_default"] for row in group),
                "example_tasks": sorted({row["task"] for row in group})[:6],
            }
        )
    return sorted(rows, key=lambda row: (-row["decisions"], row["selected_action_class"], row["best_action_class"]))


def build_task_cards(aligned: list[dict[str, Any]]) -> list[dict[str, Any]]:
    cards = []
    for (protocol, task), group in sorted(group_by(aligned, ["protocol", "task"]).items()):
        selected_actions = Counter(row["selected_action_class"] for row in group)
        best_actions = Counter(row["best_r348_action_class"] for row in group)
        misses = [
            f"{row['mapped_objective']} selected={row['selected_action_class']} best={row['best_r348_action_class']}"
            for row in group
            if not row["selected_action_exact"]
        ][:3]
        cards.append(
            {
                "protocol": protocol,
                "task": task,
                "dataset": group[0]["dataset"],
                "objectives": len(group),
                "selected_action_exact": sum(row["selected_action_exact"] for row in group),
                "selected_within_tolerance": sum(row["selected_within_tolerance"] for row in group),
                "selected_beats_default": sum(row["selected_beats_default"] for row in group),
                "dominant_selected_action": selected_actions.most_common(1)[0][0],
                "dominant_best_action": best_actions.most_common(1)[0][0],
                "selected_action_classes": dict(selected_actions),
                "best_action_classes": dict(best_actions),
                "hard_counterexamples": "; ".join(misses),
            }
        )
    return cards


def build_markdown(path: Path, payload: dict[str, Any]) -> None:
    summary = payload["summary"]
    lines = [
        "# R349 Held-Out Action-Transfer Audit",
        "",
        "R349 maps R340 held-out policy selections to action classes and compares",
        "them against the R348 target-task counterfactual action oracle. It is a",
        "guardrail experiment: metric-tolerance transfer is useful, but exact",
        "action-class transfer is intentionally not promoted to an automatic",
        "selector claim.",
        "",
        "## Summary",
        "",
        f"- Overall: {summary['overall']}.",
        f"- R340 transfer decisions: {summary['transfer_decisions_total']}.",
        f"- Aligned R340/R348 decisions: {summary['aligned_decisions']}.",
        f"- Excluded sequence decisions: {summary['sequence_objective_excluded_rows']}.",
        f"- R348 objective rows not covered by R340 transfer: {summary['r348_untransferred_objective_rows']}.",
        f"- Exact action-class transfer: {summary['selected_action_exact']}/{summary['aligned_decisions']}.",
        f"- Within metric tolerance: {summary['selected_within_tolerance']}/{summary['aligned_decisions']}.",
        f"- Beats default operation stack: {summary['selected_beats_default']}/{summary['aligned_decisions']}.",
        f"- Default operation stack already within tolerance: {summary['default_within_tolerance']}/{summary['aligned_decisions']}.",
        f"- Non-default target rows: {summary['nondefault_target_rows']}.",
        f"- Non-default target rows with exact action transfer: {summary['nondefault_target_action_exact']}/{summary['nondefault_target_rows']}.",
        f"- Non-default target rows within metric tolerance: {summary['nondefault_target_within_tolerance']}/{summary['nondefault_target_rows']}.",
        "",
        "## Interpretation",
        "",
        "- R349 supports using held-out policy transfer as an automated proxy for",
        "  finding promising diagnostic views/rankers under a metric budget.",
        "- R349 does not support claiming a label-free automatic action selector:",
        "  exact action-class transfer is low, especially when the target best",
        "  action is non-default.",
        "- The paper should frame this as a protocol-sensitivity/actionability",
        "  tradeoff and keep task-specific operation-stack inspection in scope.",
        "",
        "## Protocol Summary",
        "",
        "| Protocol | Decisions | Action exact | Within tolerance | Beats default |",
        "|---|---:|---:|---:|---:|",
    ]
    for row in payload["summary_rows"]:
        if row["scope"] == "protocol":
            lines.append(
                f"| {row['protocol']} | {row['decisions']} | {row['selected_action_exact']} | "
                f"{row['selected_within_tolerance']} | {row['selected_beats_default']} |"
            )
    lines.extend(
        [
            "",
            "## Action Confusion",
            "",
            "| Selected action | Best action | Decisions | Within tolerance | Beats default |",
            "|---|---|---:|---:|---:|",
        ]
    )
    for row in payload["action_confusion"]:
        lines.append(
            f"| {row['selected_action_class']} | {row['best_action_class']} | {row['decisions']} | "
            f"{row['selected_within_tolerance']} | {row['selected_beats_default']} |"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_html(path: Path, payload: dict[str, Any]) -> None:
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

    summary = payload["summary"]
    content = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>R349 Held-Out Action-Transfer Audit</title>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, sans-serif; margin: 32px; line-height: 1.45; }}
    table {{ border-collapse: collapse; width: 100%; margin: 16px 0; font-size: 13px; }}
    th, td {{ border: 1px solid #d0d7de; padding: 6px 8px; text-align: left; vertical-align: top; }}
    th {{ background: #f6f8fa; }}
  </style>
</head>
<body>
  <h1>R349 Held-Out Action-Transfer Audit</h1>
  <p><strong>Overall:</strong> {html.escape(summary['overall'])}</p>
  <h2>Summary</h2>
  {table([summary], ['aligned_decisions', 'selected_action_exact', 'selected_within_tolerance', 'selected_beats_default', 'default_within_tolerance', 'nondefault_target_rows', 'nondefault_target_action_exact', 'nondefault_target_within_tolerance'])}
  <h2>Summary Rows</h2>
  {table(payload['summary_rows'], ['scope', 'protocol', 'objective', 'decisions', 'selected_action_exact', 'selected_within_tolerance', 'selected_beats_default', 'default_within_tolerance'])}
  <h2>Action Confusion</h2>
  {table(payload['action_confusion'], ['selected_action_class', 'best_action_class', 'decisions', 'selected_within_tolerance', 'selected_beats_default'])}
  <h2>Task Cards</h2>
  {table(payload['task_cards'], ['protocol', 'task', 'dataset', 'objectives', 'selected_action_exact', 'selected_within_tolerance', 'dominant_selected_action', 'dominant_best_action', 'hard_counterexamples'])}
</body>
</html>
"""
    path.write_text(content, encoding="utf-8")


def build_payload() -> dict[str, Any]:
    source_status = ensure_sources_tracked_clean(list(SOURCE_ARTIFACTS.values()))
    r340_report = load_json(SOURCE_ARTIFACTS["R340 report"])
    r348_report = load_json(SOURCE_ARTIFACTS["R348 report"])
    transfer_decisions = read_csv(SOURCE_ARTIFACTS["R340 transfer decisions"])
    r348_rows = read_csv(SOURCE_ARTIFACTS["R348 objective counterfactuals"])

    aligned, excluded, untransferred_r348 = align_decisions(transfer_decisions, r348_rows)
    summary_rows = build_summary_rows(aligned)
    action_confusion = build_confusion_rows(aligned)
    task_cards = build_task_cards(aligned)

    total = summarize_group(aligned, {"scope": "all", "protocol": "all", "objective": "all"})
    nondefault_rows = [row for row in aligned if row["target_best_nondefault"]]
    sequence_excluded = [row for row in excluded if row["reason"] == "sequence_objective_not_in_r348"]
    selected_actions = Counter(row["selected_action_class"] for row in aligned)
    best_actions = Counter(row["best_r348_action_class"] for row in aligned)
    summary = {
        "overall": "pass"
        if len(transfer_decisions) == 96
        and len(aligned) == 60
        and len(excluded) == 36
        and len(sequence_excluded) == 36
        and len(untransferred_r348) == 6
        and all(row["selected_visible_non_oracle"] for row in aligned)
        and all(row["best_r348_visible_non_oracle"] for row in aligned)
        and all(status == "tracked_clean" for status in source_status.values())
        else "fail",
        "transfer_decisions_total": len(transfer_decisions),
        "aligned_decisions": len(aligned),
        "excluded_decisions": len(excluded),
        "aligned_objectives": len({row["mapped_objective"] for row in aligned}),
        "protocols": len({row["protocol"] for row in aligned}),
        "tasks": len({row["task"] for row in aligned}),
        "datasets": len({row["dataset"] for row in aligned}),
        "selected_visible_non_oracle_rows": sum(row["selected_visible_non_oracle"] for row in aligned),
        "best_visible_non_oracle_rows": sum(row["best_r348_visible_non_oracle"] for row in aligned),
        "r340_r348_best_policy_match_rows": sum(row["r340_r348_best_policy_match"] for row in aligned),
        "r340_r348_best_policy_mismatch_rows": sum(not row["r340_r348_best_policy_match"] for row in aligned),
        "selected_action_exact": total["selected_action_exact"],
        "selected_r348_policy_exact": total["selected_r348_policy_exact"],
        "selected_r340_exact_best": sum(row["selected_r340_exact_best"] for row in aligned),
        "selected_view_exact": total["selected_view_exact"],
        "selected_ranker_exact": total["selected_ranker_exact"],
        "selected_within_tolerance": total["selected_within_tolerance"],
        "selected_beats_default": total["selected_beats_default"],
        "default_within_tolerance": total["default_within_tolerance"],
        "nondefault_target_rows": len(nondefault_rows),
        "nondefault_target_action_exact": total["nondefault_target_action_exact"],
        "nondefault_target_within_tolerance": total["nondefault_target_within_tolerance"],
        "nondefault_target_selected_default_action": total["nondefault_target_selected_default_action"],
        "leave_task_action_exact": next(
            row["selected_action_exact"]
            for row in summary_rows
            if row["scope"] == "protocol" and row["protocol"] == "leave_task"
        ),
        "leave_dataset_action_exact": next(
            row["selected_action_exact"]
            for row in summary_rows
            if row["scope"] == "protocol" and row["protocol"] == "leave_dataset"
        ),
        "leave_task_within_tolerance": next(
            row["selected_within_tolerance"]
            for row in summary_rows
            if row["scope"] == "protocol" and row["protocol"] == "leave_task"
        ),
        "leave_dataset_within_tolerance": next(
            row["selected_within_tolerance"]
            for row in summary_rows
            if row["scope"] == "protocol" and row["protocol"] == "leave_dataset"
        ),
        "sequence_objective_excluded_rows": len(sequence_excluded),
        "r348_untransferred_objective_rows": len(untransferred_r348),
        "selected_action_counts": dict(selected_actions),
        "best_action_counts": dict(best_actions),
        "network_access_required": False,
        "dataset_sync": "none",
        "r340_transfer_decisions": r340_report["summary"]["transfer_decisions"],
        "r348_objective_rows": r348_report["summary"]["objective_rows"],
    }

    return {
        "schema": "agentsight.operation-action-transfer.v1",
        "run_id": RUN_ID,
        "created_unix": time.time(),
        "commit": git_output(["rev-parse", "HEAD"]),
        "input_policy": {
            "dataset_sync": "none",
            "dataset_creation": "none",
            "dataset_relabeling": "none",
            "network_access_required": False,
            "target_hidden_label_use": "not used for held-out policy selection; R348 labels are used only as an offline scoring oracle",
            "hidden_label_use": "reads already-scored R340/R348 artifacts and compares held-out visible decisions against target-task counterfactual labels",
        },
        "profiler_abstractions": ["operation", "operation stack"],
        "supported_wording": (
            "Held-out visible-policy transfer often preserves metric tolerance and sometimes beats "
            "the default operation stack, but exact action-class transfer is too weak to claim a "
            "label-free automatic optimization selector."
        ),
        "scope_guardrails": [
            "supports protocol-sensitivity and actionability tradeoff claims, not automatic action selection",
            "keeps target hidden labels out of held-out policy selection",
            "compares only objectives shared by R340 and R348",
            "excludes sequence-only objectives and R348 fragmentation-only rows from action-transfer rates",
        ],
        "must_not_claim": [
            "R349 proves automatic discovery of the best action class",
            "R349 proves operation-stack query-aware is always sufficient",
            "R349 validates human analyst speed, accuracy, or productivity",
            "R349 evaluates sequence-boundary objectives or fragmentation objectives directly",
        ],
        "source_status": source_status,
        "summary": summary,
        "summary_rows": summary_rows,
        "action_confusion": action_confusion,
        "task_cards": task_cards,
        "action_transfer_decisions": aligned,
        "excluded_transfer_decisions": excluded,
        "untransferred_r348_objectives": untransferred_r348,
    }


def main() -> None:
    args = parse_args()
    out_dir = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    payload = build_payload()
    write_json(out_dir / "action-transfer-report.json", payload)
    build_markdown(out_dir / "action-transfer-report.md", payload)
    build_html(out_dir / "index.html", payload)
    write_csv(
        out_dir / "action-transfer-decisions.csv",
        payload["action_transfer_decisions"],
        [
            "protocol",
            "task",
            "dataset",
            "query_family",
            "objective",
            "mapped_objective",
            "metric",
            "direction",
            "selected_policy",
            "selected_view",
            "selected_ranker",
            "selected_action_class",
            "selected_target_value",
            "selected_target_rank",
            "best_r340_policy",
            "best_r340_value",
            "best_r348_policy",
            "best_r348_view",
            "best_r348_ranker",
            "best_r348_action_class",
            "best_r348_value",
            "default_value",
            "r340_r348_best_policy_match",
            "selected_visible_non_oracle",
            "best_r348_visible_non_oracle",
            "selected_r340_exact_best",
            "selected_r348_policy_exact",
            "selected_action_exact",
            "selected_view_exact",
            "selected_ranker_exact",
            "selected_within_tolerance",
            "selected_delta_vs_best",
            "selected_delta_vs_default",
            "selected_beats_default",
            "default_within_tolerance",
            "target_best_nondefault",
            "r348_gain_over_default",
            "action_transfer_verdict",
            "r348_optimization_action",
            "r348_counterpoints",
        ],
    )
    write_csv(
        out_dir / "action-transfer-summary.csv",
        payload["summary_rows"],
        [
            "scope",
            "protocol",
            "objective",
            "decisions",
            "selected_action_exact",
            "selected_r348_policy_exact",
            "selected_view_exact",
            "selected_ranker_exact",
            "selected_within_tolerance",
            "selected_beats_default",
            "default_within_tolerance",
            "target_best_nondefault",
            "nondefault_target_action_exact",
            "nondefault_target_within_tolerance",
            "nondefault_target_selected_default_action",
            "median_delta_vs_best",
        ],
    )
    write_csv(
        out_dir / "action-transfer-confusion.csv",
        payload["action_confusion"],
        [
            "selected_action_class",
            "best_action_class",
            "decisions",
            "selected_within_tolerance",
            "selected_beats_default",
            "example_tasks",
        ],
    )
    write_csv(
        out_dir / "task-action-transfer-cards.csv",
        payload["task_cards"],
        [
            "protocol",
            "task",
            "dataset",
            "objectives",
            "selected_action_exact",
            "selected_within_tolerance",
            "selected_beats_default",
            "dominant_selected_action",
            "dominant_best_action",
            "selected_action_classes",
            "best_action_classes",
            "hard_counterexamples",
        ],
    )
    write_csv(
        out_dir / "excluded-transfer-decisions.csv",
        payload["excluded_transfer_decisions"],
        [
            "protocol",
            "task",
            "dataset",
            "query_family",
            "objective",
            "mapped_objective",
            "reason",
            "selected_policy",
            "best_visible_policy",
        ],
    )
    write_csv(
        out_dir / "untransferred-r348-objectives.csv",
        payload["untransferred_r348_objectives"],
        ["task", "dataset", "query_family", "objective", "best_policy", "action_class", "reason"],
    )
    write_json(
        out_dir / "run-result.json",
        {
            "run_id": RUN_ID,
            "schema": payload["schema"],
            "summary": payload["summary"],
            "commit": payload["commit"],
        },
    )
    print(json.dumps(payload["summary"], indent=2, sort_keys=True))
    if payload["summary"]["overall"] != "pass":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
