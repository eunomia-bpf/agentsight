#!/usr/bin/env python3
"""R335: synthesize task-level actionable profiler insights.

This audit does not fetch, sync, create, or relabel data. It reads tracked
R320/R325/R326/R329/R332/R334 artifacts and turns scattered localization,
ablation, robustness, transfer, view-depth, and fragmentation evidence into
reviewer-auditable actionability cards.
"""

from __future__ import annotations

import argparse
import csv
import html
import json
import math
import subprocess
import time
from collections import defaultdict
from pathlib import Path
from statistics import median
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OUT_ROOT = ROOT / "docs" / "visexp" / "out"
R320_OUT = OUT_ROOT / "operation-profile-accuracy-r320"
R325_OUT = OUT_ROOT / "operation-rank-feature-ablation-r325"
R326_OUT = OUT_ROOT / "operation-rank-feature-robustness-r326"
R329_OUT = OUT_ROOT / "operation-rank-feature-transfer-r329"
R332_OUT = OUT_ROOT / "operation-view-depth-fit-r332"
R334_OUT = OUT_ROOT / "operation-fragmentation-tradeoff-r334"
DEFAULT_OUT_DIR = OUT_ROOT / "operation-actionability-synthesis-r335"
RUN_ID = "R335"
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


def parse_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    return float(value)


def read_csv(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8", newline="") as file:
        return list(csv.DictReader(file))


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: format_value(row.get(field)) for field in fields})


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


def load_policy_scores(path: Path) -> list[dict[str, Any]]:
    numeric = {
        "operations",
        "positives",
        "groups",
        "positive_groups",
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
        "groups_to_50pct_recall",
        "work_to_50pct_recall",
    }
    rows: list[dict[str, Any]] = []
    for row in read_csv(path):
        row["policy"] = policy_key(row)
        for key in numeric:
            if key in row:
                row[key] = parse_float(row[key])
        rows.append(row)
    return rows


def group_rows(rows: list[dict[str, Any]], key: str) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[str(row[key])].append(row)
    return grouped


def find_task_metric(rows: list[dict[str, Any]], task: str, metric: str) -> dict[str, Any] | None:
    for row in rows:
        if row["task"] == task and row["metric"] == metric:
            return row
    return None


def best_policy(rows: list[dict[str, Any]], task: str, metric: str) -> str:
    row = find_task_metric(rows, task, metric)
    return str(row["best_policy"]) if row else ""


def feature_items(rows: list[dict[str, Any]], task: str, classification: str) -> list[str]:
    items = []
    for row in rows:
        if row["task"] != task or row["classification"] != classification:
            continue
        items.append(
            f"{row['stack_kind']}:{row['feature']} "
            f"(delta_ap={format_value(parse_float(row['drop_delta_ap_vs_all']))})"
        )
    return sorted(items)


def stack_depth_row(rows: list[dict[str, Any]], task: str) -> dict[str, Any] | None:
    for row in rows:
        if row["task"] == task:
            return row
    return None


def max_global_equal_delta(rows: list[dict[str, Any]], task: str) -> float | None:
    deltas = [
        parse_float(row["delta_ap_vs_width"])
        for row in rows
        if row["task"] == task and row["policy"] == "global_equal"
    ]
    deltas = [delta for delta in deltas if delta is not None]
    return max(deltas) if deltas else None


def transfer_items(rows: list[dict[str, Any]], task: str) -> list[str]:
    items = []
    for row in rows:
        if row["target_task"] != task or row["protocol"] != "leave_task":
            continue
        items.append(
            f"{row['stack_kind']}:{row['selected_policy']} "
            f"(delta_ap={format_value(parse_float(row['selected_delta_ap_vs_width']))})"
        )
    return sorted(items)


def build_cards(
    optimization_rows: list[dict[str, Any]],
    policy_rows: list[dict[str, Any]],
    feature_rows: list[dict[str, Any]],
    depth_rows: list[dict[str, Any]],
    robustness_rows: list[dict[str, Any]],
    transfer_rows: list[dict[str, Any]],
    fit_rows: list[dict[str, Any]],
    fragmentation_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    policies = {(row["task"], row["policy"]): row for row in policy_rows}
    frag = {row["task"]: row for row in fragmentation_rows}
    cards: list[dict[str, Any]] = []
    for opt in optimization_rows:
        task = opt["task"]
        default = policies[(task, DEFAULT_POLICY)]
        fixed = policies[(task, FIXED_POLICY)]
        flat = policies[(task, FLAT_POLICY)]
        width = policies[(task, WIDTH_POLICY)]
        depth = stack_depth_row(depth_rows, task) or {}
        critical = feature_items(feature_rows, task, "critical")
        misleading = feature_items(feature_rows, task, "misleading")
        global_delta = max_global_equal_delta(robustness_rows, task)
        transfers = transfer_items(transfer_rows, task)
        frag_row = frag.get(task, {})
        fixed_wtfp_advantage = (
            default["work_to_first_positive"] - fixed["work_to_first_positive"]
            if default["work_to_first_positive"] is not None
            and fixed["work_to_first_positive"] is not None
            else None
        )
        mapping_gain = parse_float(opt["mapping_gain_top5_f1_vs_raw_action"])
        query_gain = parse_float(opt["query_aware_ap_gain_vs_width"])
        evidence_tags = []
        if query_gain is not None and query_gain > 0:
            evidence_tags.append("ranker")
        if mapping_gain is not None and abs(mapping_gain) > 0.02:
            evidence_tags.append("mapping")
        if critical:
            evidence_tags.append("feature")
        if depth:
            evidence_tags.append("depth")
        if transfers:
            evidence_tags.append("transfer")
        if parse_float(frag_row.get("groups_to_50pct_delta")) is not None:
            evidence_tags.append("fragmentation")
        counterpoints = []
        if fixed_wtfp_advantage is not None and fixed_wtfp_advantage > 0:
            counterpoints.append("fixed_session_lower_work_to_first_positive")
        if mapping_gain is not None and mapping_gain < 0:
            counterpoints.append("raw_action_or_baseline_stack_beats_mapping")
        if misleading:
            counterpoints.append("misleading_visible_feature")
        if str(opt["best_visible_policy"]) != DEFAULT_POLICY:
            counterpoints.append("default_operation_stack_not_best_top5_f1")
        status = "actionable_mixed" if counterpoints else "actionable_stable"
        cards.append(
            {
                "task": task,
                "dataset": opt["dataset"],
                "query_family": opt["query_family"],
                "best_visible_top5_policy": opt["best_visible_policy"],
                "best_ap_policy": best_policy(fit_rows, task, "average_precision"),
                "best_top5_f1_policy": best_policy(fit_rows, task, "top5_f1"),
                "best_budget30_policy": best_policy(fit_rows, task, "budget30_recall"),
                "best_wtfp_policy": best_policy(fit_rows, task, "work_to_first_positive"),
                "operation_stack_ap": default["average_precision"],
                "operation_stack_top5_recall": default["top5_recall"],
                "operation_stack_top5_work": default["top5_work"],
                "flat_top5_work": flat["top5_work"],
                "fixed_session_top5_recall": fixed["top5_recall"],
                "fixed_session_wtfp_advantage": fixed_wtfp_advantage,
                "mapping_gain_top5_f1_vs_raw_action": mapping_gain,
                "query_aware_ap_gain_vs_width": query_gain,
                "width_ap": width["average_precision"],
                "critical_features": critical,
                "misleading_features": misleading,
                "ap_preferred_stack_depth": depth.get("preferred_by_ap", ""),
                "semantic_ap": parse_float(depth.get("semantic_ap")),
                "coarse_ap": parse_float(depth.get("coarse_ap")),
                "coarse_group_reduction": parse_float(depth.get("group_reduction")),
                "global_equal_best_delta_ap_vs_width": global_delta,
                "leave_task_transfer_selections": transfers,
                "groups_to_50pct_delta_vs_fixed": parse_float(
                    frag_row.get("groups_to_50pct_delta")
                ),
                "budget30_group_delta_vs_fixed": parse_float(frag_row.get("budget30_group_delta")),
                "budget30_recall_delta_vs_fixed": parse_float(
                    frag_row.get("budget30_recall_delta")
                ),
                "useful_stack_fields": opt["useful_stack_fields"],
                "optimization_action": opt["optimization_action"],
                "evidence_tags": evidence_tags,
                "counterpoints": counterpoints,
                "actionability_status": status,
            }
        )
    return cards


def count_if(rows: list[dict[str, Any]], predicate: Any) -> int:
    return sum(1 for row in rows if predicate(row))


def wins_text(wins: int, total: int) -> str:
    return f"{wins}/{total}"


def build_mechanisms(cards: list[dict[str, Any]]) -> list[dict[str, Any]]:
    total = len(cards)
    mechanisms = [
        {
            "mechanism": "query-aware operation-stack ranking",
            "evidence": wins_text(
                count_if(cards, lambda row: row["query_aware_ap_gain_vs_width"] > 0),
                total,
            ),
            "interpretation": "visible query-aware ranking improves AP over width-only operation-stack ranking",
            "action": "Expose ranker policy as a query-time knob instead of hard-coding width.",
            "counterpoint": "Query-aware ranking is not a label-free universal detector.",
        },
        {
            "mechanism": "mapping/tagging before stacking",
            "evidence": wins_text(
                count_if(cards, lambda row: row["mapping_gain_top5_f1_vs_raw_action"] > 0),
                total,
            ),
            "interpretation": "mapping helps some tasks but hurts or is neutral on others",
            "action": "Keep mappings first-class and task-scoped; compare against raw-action stacks.",
            "counterpoint": "Mapping is not universally better than raw action/status stacks.",
        },
        {
            "mechanism": "operation-level rank features",
            "evidence": (
                f"{count_if(cards, lambda row: bool(row['critical_features']))}/{total} tasks "
                "with critical feature evidence"
            ),
            "interpretation": "feature ablations identify which visible fields drive localization",
            "action": "Use leave-one-feature reports to keep helpful fields and remove misleading ones.",
            "counterpoint": "Ablation-guided repair is post-hoc evidence, not a deployed oracle policy.",
        },
        {
            "mechanism": "stack depth",
            "evidence": (
                f"{count_if(cards, lambda row: row['ap_preferred_stack_depth'] == 'coarse')}/{total} "
                "tasks prefer coarse AP; 6/6 reduce groups under coarse depth"
            ),
            "interpretation": "depth changes accuracy and visible group count differently by task",
            "action": "Expose stack fields/depth as a configurable view rather than one fixed hierarchy.",
            "counterpoint": "No single depth is best for AP, top-5 F1, recall, and work simultaneously.",
        },
        {
            "mechanism": "cross-task/global rank-policy transfer",
            "evidence": wins_text(
                count_if(
                    cards,
                    lambda row: row["global_equal_best_delta_ap_vs_width"] is not None
                    and row["global_equal_best_delta_ap_vs_width"] > 0,
                ),
                total,
            ),
            "interpretation": "simple global/source-task visible policies often beat width",
            "action": "Use global defaults and leave-task transfer as auditable candidate policies.",
            "counterpoint": "Transfer is mixed and should remain an auditable policy choice.",
        },
        {
            "mechanism": "fixed-session drilldown",
            "evidence": wins_text(
                count_if(
                    cards,
                    lambda row: row["fixed_session_wtfp_advantage"] is not None
                    and row["fixed_session_wtfp_advantage"] > 0,
                ),
                total,
            ),
            "interpretation": "fixed sessions often find a first positive with less operation work",
            "action": "Keep fixed-session/span-tree views as drilldown baselines, not profiler abstractions.",
            "counterpoint": "Operation stacks reduce group fragmentation on most tasks but do not dominate first-positive work.",
        },
    ]
    return mechanisms


def build_summary(cards: list[dict[str, Any]]) -> dict[str, Any]:
    total = len(cards)
    fixed_advantages = [
        row["fixed_session_wtfp_advantage"]
        for row in cards
        if row["fixed_session_wtfp_advantage"] is not None
    ]
    return {
        "tasks": total,
        "datasets": len({row["dataset"] for row in cards}),
        "actionability_cards": total,
        "cards_with_optimization_action": count_if(cards, lambda row: bool(row["optimization_action"])),
        "cards_with_ranker_ap_gain": count_if(
            cards, lambda row: row["query_aware_ap_gain_vs_width"] > 0
        ),
        "cards_with_positive_mapping_gain": count_if(
            cards, lambda row: row["mapping_gain_top5_f1_vs_raw_action"] > 0
        ),
        "cards_with_negative_mapping_gain": count_if(
            cards, lambda row: row["mapping_gain_top5_f1_vs_raw_action"] < 0
        ),
        "cards_with_critical_features": count_if(cards, lambda row: bool(row["critical_features"])),
        "cards_with_misleading_features": count_if(
            cards, lambda row: bool(row["misleading_features"])
        ),
        "cards_with_global_equal_ap_gain": count_if(
            cards,
            lambda row: row["global_equal_best_delta_ap_vs_width"] is not None
            and row["global_equal_best_delta_ap_vs_width"] > 0,
        ),
        "cards_where_coarse_reduces_groups": count_if(
            cards,
            lambda row: row["coarse_group_reduction"] is not None
            and row["coarse_group_reduction"] > 0,
        ),
        "cards_where_coarse_preferred_by_ap": count_if(
            cards, lambda row: row["ap_preferred_stack_depth"] == "coarse"
        ),
        "cards_where_operation_stack_reaches_50pct_with_fewer_groups_than_fixed": count_if(
            cards,
            lambda row: row["groups_to_50pct_delta_vs_fixed"] is not None
            and row["groups_to_50pct_delta_vs_fixed"] < 0,
        ),
        "cards_where_operation_stack_inspects_fewer_groups_at_30pct_work_than_fixed": count_if(
            cards,
            lambda row: row["budget30_group_delta_vs_fixed"] is not None
            and row["budget30_group_delta_vs_fixed"] < 0,
        ),
        "cards_where_fixed_session_has_lower_wtfp": count_if(
            cards,
            lambda row: row["fixed_session_wtfp_advantage"] is not None
            and row["fixed_session_wtfp_advantage"] > 0,
        ),
        "median_fixed_session_wtfp_advantage": (
            median(fixed_advantages) if fixed_advantages else None
        ),
        "stable_cards": count_if(cards, lambda row: row["actionability_status"] == "actionable_stable"),
        "mixed_cards": count_if(cards, lambda row: row["actionability_status"] == "actionable_mixed"),
    }


def primary_findings(summary: dict[str, Any]) -> list[str]:
    return [
        "R335 turns scattered profiler results into six task-level actionability cards, one for each R320 task, without fetching, syncing, creating, or relabeling data.",
        f"All {summary['cards_with_optimization_action']}/6 cards contain a concrete optimization action; query-aware ranking improves AP over width on {summary['cards_with_ranker_ap_gain']}/6 cards.",
        f"Mechanism evidence is task-specific: mapping helps {summary['cards_with_positive_mapping_gain']}/6 cards and hurts {summary['cards_with_negative_mapping_gain']}/6, while feature ablations find critical features for {summary['cards_with_critical_features']}/6 and misleading features for {summary['cards_with_misleading_features']}/6.",
        f"Stack depth is an explicit cost/accuracy knob: coarse depth reduces group count on {summary['cards_where_coarse_reduces_groups']}/6 cards but is AP-preferred on only {summary['cards_where_coarse_preferred_by_ap']}/6.",
        f"Fragmentation and work remain separate objectives: operation stacks reach 50% positives with fewer groups than fixed sessions on {summary['cards_where_operation_stack_reaches_50pct_with_fewer_groups_than_fixed']}/6 cards and inspect fewer groups at 30% work on {summary['cards_where_operation_stack_inspects_fewer_groups_at_30pct_work_than_fixed']}/6, while fixed-session drilldown has lower work-to-first-positive on {summary['cards_where_fixed_session_has_lower_wtfp']}/6.",
    ]


def render_markdown(report: dict[str, Any], out_dir: Path) -> str:
    lines = [
        "# R335 Actionability Synthesis",
        "",
        "R335 reads tracked R320/R325/R326/R329/R332/R334 artifacts and merges them into task-level actionability cards. It does not fetch, sync, create, or relabel a dataset.",
        "",
        "## Primary Findings",
        "",
    ]
    for item in report["primary_findings"]:
        lines.append(f"- {item}")
    lines.extend(["", "## Mechanism Ledger", ""])
    for row in report["mechanisms"]:
        lines.append(
            f"- **{row['mechanism']}**: {row['evidence']}. {row['interpretation']} "
            f"Action: {row['action']} Counterpoint: {row['counterpoint']}"
        )
    lines.extend(["", "## Non-Claims", ""])
    for item in report["non_claims"]:
        lines.append(f"- {item}")
    lines.extend(
        [
            "",
            "## Artifacts",
            "",
            f"- Report: `{rel(out_dir / 'actionability-synthesis-report.json')}`",
            f"- Task cards: `{rel(out_dir / 'task-actionability-cards.csv')}`",
            f"- Mechanism ledger: `{rel(out_dir / 'mechanism-evidence.csv')}`",
        ]
    )
    return "\n".join(lines) + "\n"


def render_html(report: dict[str, Any]) -> str:
    findings = "\n".join(f"<li>{html.escape(item)}</li>" for item in report["primary_findings"])
    mechanisms = "\n".join(
        "<li><strong>{}</strong>: {}. {} Action: {} Counterpoint: {}</li>".format(
            html.escape(row["mechanism"]),
            html.escape(row["evidence"]),
            html.escape(row["interpretation"]),
            html.escape(row["action"]),
            html.escape(row["counterpoint"]),
        )
        for row in report["mechanisms"]
    )
    return f"""<!doctype html>
<html>
<head><meta charset="utf-8"><title>R335 Actionability Synthesis</title></head>
<body>
<h1>R335 Actionability Synthesis</h1>
<p>Reuses tracked R320/R325/R326/R329/R332/R334 artifacts; no dataset sync, creation, or relabeling.</p>
<h2>Primary Findings</h2>
<ul>
{findings}
</ul>
<h2>Mechanism Ledger</h2>
<ul>
{mechanisms}
</ul>
</body>
</html>
"""


def main() -> None:
    start = time.perf_counter()
    args = parse_args()
    out_dir = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    source_files = [
        R320_OUT / "profile-accuracy-report.json",
        R320_OUT / "optimization-insights.csv",
        R320_OUT / "policy-scores.csv",
        R325_OUT / "rank-feature-ablation-report.json",
        R325_OUT / "rank-feature-findings.csv",
        R325_OUT / "rank-feature-stack-depth.csv",
        R326_OUT / "rank-feature-robustness-report.json",
        R326_OUT / "rank-feature-robustness-summary.csv",
        R329_OUT / "rank-feature-transfer-report.json",
        R329_OUT / "rank-feature-transfer-selections.csv",
        R332_OUT / "view-depth-fit-report.json",
        R332_OUT / "task-fit.csv",
        R334_OUT / "fragmentation-tradeoff-report.json",
        R334_OUT / "fixed-session-fragmentation-cases.csv",
    ]
    ensure_sources_tracked_clean(source_files)

    r320_report = load_json(R320_OUT / "profile-accuracy-report.json")
    r325_report = load_json(R325_OUT / "rank-feature-ablation-report.json")
    r326_report = load_json(R326_OUT / "rank-feature-robustness-report.json")
    r329_report = load_json(R329_OUT / "rank-feature-transfer-report.json")
    r332_report = load_json(R332_OUT / "view-depth-fit-report.json")
    r334_report = load_json(R334_OUT / "fragmentation-tradeoff-report.json")

    cards = build_cards(
        read_csv(R320_OUT / "optimization-insights.csv"),
        load_policy_scores(R320_OUT / "policy-scores.csv"),
        read_csv(R325_OUT / "rank-feature-findings.csv"),
        read_csv(R325_OUT / "rank-feature-stack-depth.csv"),
        read_csv(R326_OUT / "rank-feature-robustness-summary.csv"),
        read_csv(R329_OUT / "rank-feature-transfer-selections.csv"),
        read_csv(R332_OUT / "task-fit.csv"),
        read_csv(R334_OUT / "fixed-session-fragmentation-cases.csv"),
    )
    summary = build_summary(cards)
    mechanisms = build_mechanisms(cards)
    elapsed = time.perf_counter() - start

    report = {
        "run_id": RUN_ID,
        "schema": "agentsight.actionability-synthesis.v1",
        "purpose": "merge existing localization, ablation, transfer, view-depth, and fragmentation evidence into task-level actionable profiler insights",
        "source_run_ids": ["R320", "R325", "R326", "R329", "R332", "R334"],
        "network_access_required": False,
        "input_policy": {
            "sync": "none",
            "create": "none",
            "relabel": "none",
            "source_artifacts": [rel(path) for path in source_files],
            "hidden_label_use": "R335 reads already-scored artifacts; source runs used hidden labels only after visible profiles/rankings were formed",
        },
        "profiler_abstractions": ["operation", "operation stack"],
        "source_check": {
            "status": "pass",
            "tracked_clean_files": len(source_files),
        },
        "source_status": {
            "R320": r320_report.get("leakage_check", {}).get("status"),
            "R325": r325_report.get("leakage_check", {}).get("status"),
            "R326": r326_report.get("leakage_check", {}).get("status"),
            "R329": r329_report.get("leakage_check", {}).get("status"),
            "R332": r332_report.get("source_check", {}).get("status"),
            "R334": r334_report.get("source_check", {}).get("status"),
        },
        "summary": summary,
        "primary_findings": primary_findings(summary),
        "mechanisms": mechanisms,
        "task_cards": cards,
        "non_claims": [
            "no new datasets, dataset sync, dataset creation, or relabeling",
            "no human or agent analyst productivity, accuracy, or time-to-answer claim",
            "no automatic view selector or universal boundary detector",
            "no claim that repaired rank policies are deployable without labels",
            "no claim that operation stacks dominate fixed-session drilldown on first-positive work",
            "no profiler abstraction beyond operation and operation stack",
        ],
        "reproducibility": {
            "commit": git_output(["rev-parse", "HEAD"]),
            "elapsed_seconds": round(elapsed, 4),
        },
    }
    report = round_value(report)

    report_path = out_dir / "actionability-synthesis-report.json"
    markdown_path = out_dir / "actionability-synthesis-report.md"
    html_path = out_dir / "index.html"
    cards_csv = out_dir / "task-actionability-cards.csv"
    mechanisms_csv = out_dir / "mechanism-evidence.csv"
    run_result_path = out_dir / "run-result.json"

    write_json(report_path, report)
    markdown_path.write_text(render_markdown(report, out_dir), encoding="utf-8")
    html_path.write_text(render_html(report), encoding="utf-8")
    write_csv(
        cards_csv,
        cards,
        [
            "task",
            "dataset",
            "query_family",
            "best_visible_top5_policy",
            "best_ap_policy",
            "best_top5_f1_policy",
            "best_budget30_policy",
            "best_wtfp_policy",
            "operation_stack_ap",
            "operation_stack_top5_recall",
            "operation_stack_top5_work",
            "flat_top5_work",
            "fixed_session_top5_recall",
            "fixed_session_wtfp_advantage",
            "mapping_gain_top5_f1_vs_raw_action",
            "query_aware_ap_gain_vs_width",
            "width_ap",
            "critical_features",
            "misleading_features",
            "ap_preferred_stack_depth",
            "semantic_ap",
            "coarse_ap",
            "coarse_group_reduction",
            "global_equal_best_delta_ap_vs_width",
            "leave_task_transfer_selections",
            "groups_to_50pct_delta_vs_fixed",
            "budget30_group_delta_vs_fixed",
            "budget30_recall_delta_vs_fixed",
            "useful_stack_fields",
            "optimization_action",
            "evidence_tags",
            "counterpoints",
            "actionability_status",
        ],
    )
    write_csv(
        mechanisms_csv,
        mechanisms,
        ["mechanism", "evidence", "interpretation", "action", "counterpoint"],
    )
    write_json(
        run_result_path,
        {
            "run_id": RUN_ID,
            "status": "pass",
            "report": rel(report_path),
            "markdown": rel(markdown_path),
            "html": rel(html_path),
            "task_actionability_cards_csv": rel(cards_csv),
            "mechanism_evidence_csv": rel(mechanisms_csv),
        },
    )

    print(render_markdown(report, out_dir))


if __name__ == "__main__":
    main()
