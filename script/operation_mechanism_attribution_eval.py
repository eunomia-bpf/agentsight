#!/usr/bin/env python3
"""R341: mechanism and error attribution over existing profiler results.

This audit does not fetch, sync, create, or relabel datasets. It reads tracked
R320/R335/R336/R340 artifacts and turns objective-level policy choices plus
held-out transfer misses into reviewer-auditable mechanism attribution:
which profiler knobs explain wins, which counterpoints explain losses, and
where operation-stack ranking should be tuned rather than treated as universal.
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
R320_DIR = OUT_ROOT / "operation-profile-accuracy-r320"
R335_DIR = OUT_ROOT / "operation-actionability-synthesis-r335"
R336_DIR = OUT_ROOT / "operation-actionability-selection-r336"
R340_DIR = OUT_ROOT / "operation-policy-transfer-r340"
DEFAULT_OUT_DIR = OUT_ROOT / "operation-mechanism-attribution-r341"
RUN_ID = "R341"

R320_REPORT = R320_DIR / "profile-accuracy-report.json"
R320_POLICY_SCORES = R320_DIR / "policy-scores.csv"
R335_REPORT = R335_DIR / "actionability-synthesis-report.json"
R335_CARDS = R335_DIR / "task-actionability-cards.csv"
R336_REPORT = R336_DIR / "actionability-selection-report.json"
R336_OBJECTIVES = R336_DIR / "objective-recommendations.csv"
R336_POLICY_SUMMARY = R336_DIR / "policy-objective-summary.csv"
R340_REPORT = R340_DIR / "policy-transfer-report.json"
R340_DECISIONS = R340_DIR / "transfer-decisions.csv"

DEFAULT_POLICY = "operation_stack:query_aware"
FIXED_POLICY = "fixed_session:query_aware"
FLAT_POLICY = "flat:width"
WIDTH_POLICY = "operation_stack:width"


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


def parse_float(value: Any) -> float | None:
    if value in ("", None):
        return None
    return float(value)


def parse_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).lower() == "true"


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
    if isinstance(value, float):
        if math.isnan(value):
            return ""
        if math.isinf(value):
            return "inf"
        return round(value, 4)
    if value is None:
        return ""
    if isinstance(value, bool):
        return str(value)
    if isinstance(value, list):
        return "; ".join(str(item) for item in value)
    if isinstance(value, dict):
        return json.dumps(round_value(value), sort_keys=True)
    return value


def policy_view(policy: str) -> str:
    return policy.split(":", 1)[0] if ":" in policy else policy


def policy_ranker(policy: str) -> str:
    return policy.split(":", 1)[1] if ":" in policy else ""


def classify_policy(policy: str) -> str:
    if not policy_is_non_oracle(policy):
        raise SystemExit(f"R341 cannot attribute hidden/oracle policy {policy}")
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


def policy_key(row: dict[str, str]) -> str:
    return f"{row['view']}:{row['ranker']}"


def policy_is_non_oracle(policy: str) -> bool:
    return "oracle" not in policy and not policy.startswith("label_drilldown:")


def visible_policy_names(rows: list[dict[str, str]]) -> set[str]:
    return {
        policy_key(row)
        for row in rows
        if row.get("uses_hidden_fields") == "False" and policy_is_non_oracle(policy_key(row))
    }


def card_mechanisms(card: dict[str, str]) -> list[str]:
    mechanisms: list[str] = []
    if (parse_float(card.get("query_aware_ap_gain_vs_width")) or 0.0) > 0.02:
        mechanisms.append("query_aware_ranker")
    mapping_gain = parse_float(card.get("mapping_gain_top5_f1_vs_raw_action"))
    if mapping_gain is not None and mapping_gain > 0.02:
        mechanisms.append("mapping_helps")
    if mapping_gain is not None and mapping_gain < -0.02:
        mechanisms.append("mapping_hurts")
    if card.get("critical_features"):
        mechanisms.append("critical_rank_features")
    if card.get("misleading_features"):
        mechanisms.append("misleading_feature_risk")
    if (parse_float(card.get("coarse_group_reduction")) or 0.0) > 0:
        mechanisms.append("stack_depth_tradeoff")
    if card.get("leave_task_transfer_selections"):
        mechanisms.append("transfer_policy_signal")
    if "fixed_session_lower_work_to_first_positive" in card.get("counterpoints", ""):
        mechanisms.append("fixed_session_first_positive_counterpoint")
    if "raw_action_or_baseline_stack_beats_mapping" in card.get("counterpoints", ""):
        mechanisms.append("raw_action_or_baseline_counterpoint")
    return mechanisms


def objective_tradeoff(row: dict[str, str]) -> str:
    best = row["best_policy"]
    objective = row["objective"]
    if best == DEFAULT_POLICY:
        return "default_operation_stack_suffices"
    if best.startswith("operation_stack:"):
        return "operation_stack_ranker_or_depth_tuning"
    if best.startswith("fixed_session:"):
        if objective == "first_positive_work":
            return "fixed_session_first_positive_counterpoint"
        return "fixed_session_drilldown_counterpoint"
    if best.startswith("flat:"):
        return "flat_summary_counterpoint"
    if best.startswith("dataset_native:"):
        return "dataset_native_boundary_or_task_hierarchy"
    if best.startswith("raw_action_stack:"):
        return "raw_action_mapping_counterpoint"
    return "other_visible_policy_counterpoint"


def build_objective_attribution_rows(
    objective_rows: list[dict[str, str]], cards: dict[str, dict[str, str]], visible_policies: set[str]
) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for row in objective_rows:
        task = row["task"]
        card = cards[task]
        best_policy = row["best_policy"]
        if best_policy not in visible_policies:
            raise SystemExit(f"R341 objective best policy is not visible/non-oracle: {task} {best_policy}")
        mechanisms = card_mechanisms(card)
        output.append(
            {
                "task": task,
                "dataset": row["dataset"],
                "query_family": row["query_family"],
                "objective": row["objective"],
                "metric": row["metric"],
                "direction": row["direction"],
                "best_policy": best_policy,
                "best_policy_class": classify_policy(best_policy),
                "best_view": policy_view(best_policy),
                "best_ranker": policy_ranker(best_policy),
                "best_value": parse_float(row["best_value"]),
                "operation_stack_query_aware_value": parse_float(row.get(f"{DEFAULT_POLICY}_value")),
                "operation_stack_query_aware_regret": parse_float(row.get(f"{DEFAULT_POLICY}_regret")),
                "fixed_session_query_aware_regret": parse_float(row.get(f"{FIXED_POLICY}_regret")),
                "flat_width_regret": parse_float(row.get(f"{FLAT_POLICY}_regret")),
                "tradeoff_class": objective_tradeoff(row),
                "mechanism_labels": mechanisms,
                "mechanism_count": len(mechanisms),
                "optimization_action": row.get("optimization_action", ""),
                "useful_stack_fields": row.get("useful_stack_fields", ""),
                "counterpoints": row.get("counterpoints", ""),
                "actionable": bool(row.get("optimization_action")) and bool(mechanisms),
            }
        )
    return output


def classify_transfer_outcome(row: dict[str, str]) -> str:
    if parse_bool(row["selected_exact_best"]):
        return "exact_transfer"
    if parse_bool(row["selected_within_tolerance"]):
        return "near_best_transfer"
    selected = row["selected_policy"]
    best = row["best_visible_policy"]
    if parse_bool(row["default_within_tolerance"]):
        return "selector_missed_good_default"
    if best.startswith("operation_stack:") and not selected.startswith("operation_stack:"):
        return "view_mismatch_operation_stack_best"
    if selected.startswith("operation_stack:") and not best.startswith("operation_stack:"):
        return "operation_stack_overselected"
    if best.startswith("fixed_session:"):
        return "fixed_session_counterpoint"
    if best.startswith("flat:"):
        return "flat_summary_counterpoint"
    if best.startswith("dataset_native:"):
        return "dataset_native_counterpoint"
    if best.startswith("raw_action_stack:"):
        return "raw_action_counterpoint"
    if policy_view(selected) == policy_view(best) and policy_ranker(selected) != policy_ranker(best):
        return "ranker_mismatch_same_view"
    return "objective_or_task_shift"


def build_transfer_diagnostic_rows(decisions: list[dict[str, str]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for row in decisions:
        selected = row["selected_policy"]
        best = row["best_visible_policy"]
        if not policy_is_non_oracle(selected) or not policy_is_non_oracle(best):
            raise SystemExit(f"R341 transfer decision contains hidden/oracle policy: {selected} {best}")
        selected_delta_vs_best = parse_float(row.get("selected_delta_vs_best"))
        output.append(
            {
                "protocol": row["protocol"],
                "task": row["task"],
                "dataset": row["dataset"],
                "query_family": row["query_family"],
                "objective": row["objective"],
                "metric": row["metric"],
                "direction": row["direction"],
                "selected_policy": selected,
                "selected_view": policy_view(selected),
                "selected_ranker": policy_ranker(selected),
                "best_visible_policy": best,
                "best_view": policy_view(best),
                "best_ranker": policy_ranker(best),
                "selected_exact_best": parse_bool(row["selected_exact_best"]),
                "selected_within_tolerance": parse_bool(row["selected_within_tolerance"]),
                "default_within_tolerance": parse_bool(row["default_within_tolerance"]),
                "selected_target_rank": int(float(row["selected_target_rank"])),
                "selected_delta_vs_best": selected_delta_vs_best,
                "selected_delta_vs_width": parse_float(row.get("selected_delta_vs_width")),
                "selected_delta_vs_fixed": parse_float(row.get("selected_delta_vs_fixed")),
                "selected_delta_vs_flat": parse_float(row.get("selected_delta_vs_flat")),
                "outcome_class": classify_transfer_outcome(row),
                "view_changed": policy_view(selected) != policy_view(best),
                "ranker_changed": policy_ranker(selected) != policy_ranker(best),
                "high_regret_miss": (
                    not parse_bool(row["selected_within_tolerance"])
                    and selected_delta_vs_best is not None
                    and selected_delta_vs_best < -0.05
                ),
            }
        )
    return output


def counter_by(rows: list[dict[str, Any]], key: str) -> dict[str, int]:
    return dict(Counter(str(row[key]) for row in rows))


def summarize(
    cards: dict[str, dict[str, str]],
    objective_rows: list[dict[str, Any]],
    transfer_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    tasks = sorted(cards)
    mechanisms_by_task = {task: card_mechanisms(card) for task, card in cards.items()}
    transfer_misses = [row for row in transfer_rows if not row["selected_within_tolerance"]]
    objective_regrets = [
        row["operation_stack_query_aware_regret"]
        for row in objective_rows
        if row["operation_stack_query_aware_regret"] is not None
    ]
    summary = {
        "overall": "pass",
        "tasks": len(tasks),
        "objective_rows": len(objective_rows),
        "transfer_decisions": len(transfer_rows),
        "transfer_misses": len(transfer_misses),
        "actionable_objective_rows": sum(row["actionable"] for row in objective_rows),
        "nondefault_best_objective_rows": sum(row["best_policy"] != DEFAULT_POLICY for row in objective_rows),
        "objective_best_policy_non_oracle_rows": sum(policy_is_non_oracle(row["best_policy"]) for row in objective_rows),
        "default_best_objective_rows": sum(row["best_policy"] == DEFAULT_POLICY for row in objective_rows),
        "median_default_regret_across_objectives": median(objective_regrets) if objective_regrets else None,
        "objective_best_policy_classes": counter_by(objective_rows, "best_policy_class"),
        "objective_tradeoff_classes": counter_by(objective_rows, "tradeoff_class"),
        "task_mechanism_labels": mechanisms_by_task,
        "mechanism_task_counts": dict(Counter(label for labels in mechanisms_by_task.values() for label in labels)),
        "tasks_with_three_or_more_mechanism_labels": sum(len(labels) >= 3 for labels in mechanisms_by_task.values()),
        "transfer_outcome_classes": counter_by(transfer_rows, "outcome_class"),
        "transfer_miss_classes": counter_by(transfer_misses, "outcome_class"),
        "transfer_misses_where_default_was_within_tolerance": sum(
            row["outcome_class"] == "selector_missed_good_default" for row in transfer_misses
        ),
        "transfer_misses_with_view_change": sum(row["view_changed"] for row in transfer_misses),
        "transfer_misses_with_ranker_change": sum(row["ranker_changed"] for row in transfer_misses),
        "high_regret_transfer_misses": sum(row["high_regret_miss"] for row in transfer_misses),
    }
    return summary


def build_primary_findings(summary: dict[str, Any]) -> list[str]:
    return [
        (
            f"R341 audits {summary['objective_rows']} objective-task recommendations and "
            f"{summary['transfer_decisions']} held-out transfer decisions using only tracked R320/R335/R336/R340 artifacts."
        ),
        (
            f"All {summary['actionable_objective_rows']}/{summary['objective_rows']} objective rows have a concrete "
            "optimization action tied to visible mechanism labels; the mechanism labels cover "
            f"{format_counts(summary['mechanism_task_counts'])}."
        ),
        (
            f"The best visible policy is not the default operation-stack view on "
            f"{summary['nondefault_best_objective_rows']}/{summary['objective_rows']} objective rows, so the actionable "
            "claim is knob selection and counterpoint exposure rather than a universal default hierarchy."
        ),
        (
            f"Transfer misses are classifiable rather than opaque: {summary['transfer_misses']}/"
            f"{summary['transfer_decisions']} held-out decisions are outside tolerance, with classes "
            f"{format_counts(summary['transfer_miss_classes'])}."
        ),
        (
            f"{summary['transfer_misses_with_view_change']}/{summary['transfer_misses']} transfer misses change view "
            f"relative to the held-out best and {summary['transfer_misses_with_ranker_change']}/"
            f"{summary['transfer_misses']} change ranker, identifying whether to adjust stack shape or ranking policy."
        ),
    ]


def format_counts(counts: dict[str, Any]) -> str:
    if not counts:
        return "none"
    return ", ".join(f"{key}={counts[key]}" for key in sorted(counts))


def build_markdown(path: Path, report: dict[str, Any]) -> None:
    summary = report["summary"]
    lines = [
        "# Operation Mechanism Attribution Audit R341",
        "",
        "R341 reuses existing labeled-trace results. It does not fetch, sync, create, or relabel datasets.",
        "It asks whether actionability is visible as concrete mechanism attribution rather than only as headline wins.",
        "",
        "## Primary Findings",
        "",
    ]
    lines.extend(f"- {finding}" for finding in report["primary_findings"])
    lines.extend(
        [
            "",
            "## Summary",
            "",
            f"- Objective rows: {summary['objective_rows']}.",
            f"- Actionable objective rows: {summary['actionable_objective_rows']}/{summary['objective_rows']}.",
            f"- Non-default best objective rows: {summary['nondefault_best_objective_rows']}/{summary['objective_rows']}.",
            f"- Transfer misses: {summary['transfer_misses']}/{summary['transfer_decisions']}.",
            f"- Transfer miss classes: {format_counts(summary['transfer_miss_classes'])}.",
            f"- Mechanism task counts: {format_counts(summary['mechanism_task_counts'])}.",
            "",
            "## Objective Tradeoff Classes",
            "",
            "| Class | Count |",
            "|---|---:|",
        ]
    )
    for key, value in sorted(summary["objective_tradeoff_classes"].items()):
        lines.append(f"| {key} | {value} |")
    lines.extend(
        [
            "",
            "## Transfer Miss Classes",
            "",
            "| Class | Count |",
            "|---|---:|",
        ]
    )
    for key, value in sorted(summary["transfer_miss_classes"].items()):
        lines.append(f"| {key} | {value} |")
    lines.extend(
        [
            "",
            "## Non-Claims",
            "",
        ]
    )
    lines.extend(f"- {item}" for item in report["non_claims"])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_html(path: Path, report: dict[str, Any]) -> None:
    def table_from_counts(counts: dict[str, Any]) -> str:
        rows = "".join(
            f"<tr><td>{html.escape(str(key))}</td><td>{html.escape(str(value))}</td></tr>"
            for key, value in sorted(counts.items())
        )
        return f"<table><tr><th>Class</th><th>Count</th></tr>{rows}</table>"

    findings = "".join(f"<li>{html.escape(item)}</li>" for item in report["primary_findings"])
    summary = report["summary"]
    content = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>R341 Operation Mechanism Attribution</title>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, sans-serif; margin: 32px; line-height: 1.45; color: #24292f; }}
    table {{ border-collapse: collapse; width: 100%; margin: 16px 0; font-size: 13px; }}
    th, td {{ border: 1px solid #d0d7de; padding: 6px 8px; text-align: left; vertical-align: top; }}
    th {{ background: #f6f8fa; }}
    code {{ background: #f6f8fa; padding: 1px 4px; border-radius: 4px; }}
  </style>
</head>
<body>
  <h1>R341 Operation Mechanism Attribution</h1>
  <p>This audit reuses tracked profiler results and classifies objective-level mechanisms plus held-out transfer misses.</p>
  <h2>Primary Findings</h2>
  <ul>{findings}</ul>
  <h2>Summary</h2>
  <table>
    <tr><th>Objective rows</th><td>{summary['objective_rows']}</td></tr>
    <tr><th>Actionable objective rows</th><td>{summary['actionable_objective_rows']}/{summary['objective_rows']}</td></tr>
    <tr><th>Non-default best objective rows</th><td>{summary['nondefault_best_objective_rows']}/{summary['objective_rows']}</td></tr>
    <tr><th>Transfer misses</th><td>{summary['transfer_misses']}/{summary['transfer_decisions']}</td></tr>
  </table>
  <h2>Objective Tradeoff Classes</h2>
  {table_from_counts(summary['objective_tradeoff_classes'])}
  <h2>Transfer Miss Classes</h2>
  {table_from_counts(summary['transfer_miss_classes'])}
</body>
</html>
"""
    path.write_text(content, encoding="utf-8")


def main() -> None:
    args = parse_args()
    start = time.time()
    sources = [
        R320_REPORT,
        R320_POLICY_SCORES,
        R335_REPORT,
        R335_CARDS,
        R336_REPORT,
        R336_OBJECTIVES,
        R336_POLICY_SUMMARY,
        R340_REPORT,
        R340_DECISIONS,
    ]
    source_status = ensure_sources_tracked_clean(sources)
    r320 = load_json(R320_REPORT)
    r335 = load_json(R335_REPORT)
    r336 = load_json(R336_REPORT)
    r340 = load_json(R340_REPORT)
    visible_policies = visible_policy_names(read_csv(R320_POLICY_SCORES))
    cards = {row["task"]: row for row in read_csv(R335_CARDS)}
    objective_rows = build_objective_attribution_rows(read_csv(R336_OBJECTIVES), cards, visible_policies)
    transfer_rows = build_transfer_diagnostic_rows(read_csv(R340_DECISIONS))
    summary = summarize(cards, objective_rows, transfer_rows)
    report = {
        "schema": "agentsight.operation-mechanism-attribution.v1",
        "run_id": RUN_ID,
        "created_unix": time.time(),
        "commit": git_output(["rev-parse", "HEAD"]),
        "source_run_ids": ["R320", "R335", "R336", "R340"],
        "source_status": source_status,
        "source_paths": [rel(path) for path in sources],
        "source_totals": {
            "R320": r320.get("totals"),
            "R335": r335.get("summary"),
            "R336": r336.get("summary"),
            "R340": r340.get("claim_summary"),
        },
        "input_policy": {
            "dataset_sync": "none",
            "dataset_creation": "none",
            "dataset_relabeling": "none",
            "network_access_required": False,
            "hidden_label_use": "R341 reads already-scored visible-policy artifacts; it does not form new rankings",
        },
        "profiler_abstractions": ["operation", "operation stack"],
        "summary": summary,
        "primary_findings": build_primary_findings(summary),
        "non_claims": [
            "no new datasets, dataset sync, dataset creation, or relabeling",
            "no human or agent analyst productivity, accuracy, or time-to-answer claim",
            "no automatic universal policy selector",
            "no operation-stack dominance on every objective or cost metric",
            "no profiler abstraction beyond operation and operation stack",
        ],
        "reproducibility": {
            "commit": git_output(["rev-parse", "HEAD"]),
            "elapsed_seconds": round(time.time() - start, 4),
        },
    }

    args.out_dir.mkdir(parents=True, exist_ok=True)
    write_json(args.out_dir / "mechanism-attribution-report.json", report)
    write_csv(
        args.out_dir / "objective-mechanism-attribution.csv",
        objective_rows,
        [
            "task",
            "dataset",
            "query_family",
            "objective",
            "metric",
            "direction",
            "best_policy",
            "best_policy_class",
            "best_view",
            "best_ranker",
            "best_value",
            "operation_stack_query_aware_value",
            "operation_stack_query_aware_regret",
            "fixed_session_query_aware_regret",
            "flat_width_regret",
            "tradeoff_class",
            "mechanism_labels",
            "mechanism_count",
            "optimization_action",
            "useful_stack_fields",
            "counterpoints",
            "actionable",
        ],
    )
    write_csv(
        args.out_dir / "transfer-error-attribution.csv",
        transfer_rows,
        [
            "protocol",
            "task",
            "dataset",
            "query_family",
            "objective",
            "metric",
            "direction",
            "selected_policy",
            "selected_view",
            "selected_ranker",
            "best_visible_policy",
            "best_view",
            "best_ranker",
            "selected_exact_best",
            "selected_within_tolerance",
            "default_within_tolerance",
            "selected_target_rank",
            "selected_delta_vs_best",
            "selected_delta_vs_width",
            "selected_delta_vs_fixed",
            "selected_delta_vs_flat",
            "outcome_class",
            "view_changed",
            "ranker_changed",
            "high_regret_miss",
        ],
    )
    build_markdown(args.out_dir / "mechanism-attribution-report.md", report)
    build_html(args.out_dir / "index.html", report)
    write_json(
        args.out_dir / "run-result.json",
        {
            "run_id": RUN_ID,
            "status": "pass",
            "summary": summary,
            "output_dir": rel(args.out_dir),
            "network_access_required": False,
            "elapsed_seconds": round(time.time() - start, 4),
            "commit": git_output(["rev-parse", "HEAD"]),
        },
    )
    print(json.dumps(round_value({"run_id": RUN_ID, "status": "pass", "summary": summary}), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
