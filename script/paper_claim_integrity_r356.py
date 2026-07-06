#!/usr/bin/env python3
"""R356: refresh paper-claim integrity over R354/R355 supplements.

This audit is intentionally narrow. It reuses the R338 R320--R350 gate, then
adds the executable profile-spec patch audit (R354) and oracle-depth adequacy
audit (R355). It does not fetch, sync, create, or relabel datasets.
"""

from __future__ import annotations

import argparse
import csv
import html
import json
import math
from pathlib import Path
from statistics import median
from typing import Any

import paper_claim_integrity_audit as r338


ROOT = r338.ROOT
OUT_ROOT = r338.OUT_ROOT
SUBMODULE_ROOT = r338.SUBMODULE_ROOT
RUN_ID = "R356"
DEFAULT_OUT_DIR = OUT_ROOT / "paper-claim-integrity-r356"

R354_DIR = OUT_ROOT / "operation-profile-patch-r354"
R355_DIR = OUT_ROOT / "operation-oracle-depth-adequacy-r355"

R354_REPORT = R354_DIR / "profile-patch-report.json"
R354_SUMMARY = R354_DIR / "profile-patch-summary.csv"
R354_RUN_RESULT = R354_DIR / "run-result.json"

R355_REPORT = R355_DIR / "oracle-depth-adequacy-report.json"
R355_TASK_CARDS = R355_DIR / "task-depth-cards.csv"
R355_POLICY_SUMMARY = R355_DIR / "policy-depth-summary.csv"
R355_POLICY_ADEQUACY = R355_DIR / "policy-depth-adequacy.csv"
R355_MATRIX = R355_DIR / "oracle-depth-matrix.csv"
R355_COMPARISONS = R355_DIR / "depth-policy-comparisons.csv"
R355_RUN_RESULT = R355_DIR / "run-result.json"

TEXT_SOURCES = {
    **r338.PAPER_SOURCES,
    "design": ROOT / "docs" / "design.md",
    "implementation": ROOT / "docs" / "implementation.md",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    return parser.parse_args()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as file:
        return list(csv.DictReader(file))


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    r338.write_csv(path, rows, fields)


def fmt(value: Any) -> str:
    if isinstance(value, float):
        return f"{value:.4f}".rstrip("0").rstrip(".")
    return str(value)


def as_float(value: str | float | int | None) -> float:
    return r338.as_float(value)


def as_int(value: str | int) -> int:
    return r338.as_int(value)


def normalize_path(value: str | Path) -> Path:
    return r338.normalize_repo_path(str(value))


def add_check(
    rows: list[dict[str, Any]],
    *,
    run_id: str,
    key: str,
    actual: Any,
    expected: Any,
    source: str,
    paper_token: str | None = None,
    tolerance: float = 1e-9,
) -> None:
    r338.add_check(
        rows,
        run_id=run_id,
        key=key,
        actual=actual,
        expected=expected,
        source=source,
        paper_token=paper_token,
        tolerance=tolerance,
    )


def add_source_status(
    source_status: dict[str, dict[str, str]],
    name: str,
    path: Path,
    *,
    repo_root: Path = ROOT,
    require_clean: bool = True,
) -> None:
    path = normalize_path(path)
    key = name
    suffix = 2
    while key in source_status:
        key = f"{name} ({suffix})"
        suffix += 1
    source_status[key] = {
        "path": r338.rel(path),
        "status": r338.git_path_status(path, repo_root=repo_root, require_clean=require_clean),
        "sha256": r338.sha256_file(path),
    }


def collect_empirical_sources(
    r354_report: dict[str, Any], r355_report: dict[str, Any]
) -> dict[str, dict[str, str]]:
    source_status: dict[str, dict[str, str]] = {}

    for path in sorted(R354_DIR.iterdir()):
        if path.is_file():
            add_source_status(source_status, f"R354 artifact: {path.name}", path)
    for path in sorted(R355_DIR.iterdir()):
        if path.is_file():
            add_source_status(source_status, f"R355 artifact: {path.name}", path)

    for label, report in [("R354 upstream", r354_report), ("R355 upstream", r355_report)]:
        for raw_path in sorted(report.get("source_status", {})):
            add_source_status(source_status, f"{label}: {raw_path}", normalize_path(raw_path))

    for detail in r354_report["tasks_detail"]:
        for key in [
            "default_profile_spec",
            "patched_profile_spec",
            "default_rust_json",
            "patched_rust_json",
        ]:
            add_source_status(source_status, f"R354 referenced {key}: {detail['task']}", normalize_path(detail[key]))
    return source_status


def load_texts() -> tuple[dict[str, str], dict[str, dict[str, str]]]:
    texts: dict[str, str] = {}
    paper_status: dict[str, dict[str, str]] = {}
    for name, path in TEXT_SOURCES.items():
        repo_root = SUBMODULE_ROOT if path.is_relative_to(SUBMODULE_ROOT) else ROOT
        r338.git_path_status(path, repo_root=repo_root, require_clean=False)
        texts[name] = path.read_text(encoding="utf-8")
        paper_status[name] = {
            "path": r338.rel(path),
            "status": "tracked_hashed",
            "sha256": r338.sha256_file(path),
        }
    return texts, paper_status


def profile_spec_is_label_free(path: Path) -> bool:
    text = path.read_text(encoding="utf-8").lower()
    disallowed = ["positive", "oracle", "human_group", "label_drilldown"]
    return not any(token in text for token in disallowed)


def build_r354_checks(
    r354_report: dict[str, Any],
    r354_summary: list[dict[str, str]],
    r354_run: dict[str, Any],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    summary = r354_report["summary"]
    spec_paths = sorted(R354_DIR.glob("*-profile-spec.json"))
    rust_json_paths = sorted(
        path
        for path in R354_DIR.glob("*.json")
        if not path.name.endswith("-profile-spec.json")
        and path.name not in {"profile-patch-report.json", "run-result.json"}
    )
    accepted_rows = [row for row in r354_summary if row["patch_verdict"] == "accept_patch"]
    rejected_rows = [row for row in r354_summary if row["patch_verdict"] != "accept_patch"]

    add_check(rows, run_id="R354", key="status", actual=r354_report["status"], expected="pass", source="profile-patch-report.json", paper_token="R354")
    add_check(rows, run_id="R354", key="run_result_status", actual=r354_run["status"], expected="pass", source="run-result.json", paper_token="pass")
    add_check(rows, run_id="R354", key="tasks", actual=r354_report["tasks"], expected=6, source="profile-patch-report.json", paper_token="6 tasks")
    add_check(rows, run_id="R354", key="datasets", actual=r354_report["datasets"], expected=4, source="profile-patch-report.json", paper_token="4 datasets")
    add_check(rows, run_id="R354", key="summary_rows", actual=len(r354_summary), expected=6, source="profile-patch-summary.csv", paper_token="6")
    add_check(rows, run_id="R354", key="profile_spec_files", actual=len(spec_paths), expected=12, source="R354 glob *-profile-spec.json", paper_token="12")
    add_check(rows, run_id="R354", key="rust_json_profiles", actual=len(rust_json_paths), expected=12, source="R354 glob profile JSON outputs", paper_token="12")

    for key, expected in [
        ("accepted_patches", "5/6"),
        ("rejected_or_needs_mapping", "1/6"),
        ("ap_improved_tasks", "5/6"),
        ("top5_lift_improved_tasks", "5/6"),
        ("first_positive_work_improved_tasks", "5/6"),
        ("groups_reduced_tasks", "2/6"),
    ]:
        add_check(rows, run_id="R354", key=key, actual=summary[key], expected=expected, source="profile-patch-report.json summary", paper_token=expected)
    for key, expected in [
        ("median_delta_ap", 0.0376),
        ("median_delta_top5_lift", 0.5750),
        ("median_delta_first_positive_work", -0.0859),
        ("median_group_reduction", 0.0),
    ]:
        add_check(rows, run_id="R354", key=key, actual=summary[key], expected=expected, source="profile-patch-report.json summary", paper_token=f"{expected:.4f}", tolerance=5e-5)

    add_check(rows, run_id="R354", key="csv_accepted_patch_rows", actual=len(accepted_rows), expected=5, source="profile-patch-summary.csv", paper_token="5/6")
    add_check(rows, run_id="R354", key="csv_rejected_patch_rows", actual=len(rejected_rows), expected=1, source="profile-patch-summary.csv", paper_token="1/6")
    add_check(
        rows,
        run_id="R354",
        key="csv_rejected_patch_task",
        actual=rejected_rows[0]["task"] if rejected_rows else "missing",
        expected="osworld_group_start",
        source="profile-patch-summary.csv",
        paper_token="OSWorld-Human",
    )
    add_check(
        rows,
        run_id="R354",
        key="csv_ap_improved_rows",
        actual=sum(as_float(row["delta_ap"]) > 0 for row in r354_summary),
        expected=5,
        source="profile-patch-summary.csv",
        paper_token="5/6",
    )
    add_check(
        rows,
        run_id="R354",
        key="csv_top5_lift_improved_rows",
        actual=sum(as_float(row["delta_top5_lift"]) > 0 for row in r354_summary),
        expected=5,
        source="profile-patch-summary.csv",
        paper_token="5/6",
    )
    add_check(
        rows,
        run_id="R354",
        key="csv_first_positive_improved_rows",
        actual=sum(as_float(row["delta_first_positive_work"]) < 0 for row in r354_summary),
        expected=5,
        source="profile-patch-summary.csv",
        paper_token="5/6",
    )
    add_check(
        rows,
        run_id="R354",
        key="csv_groups_reduced_rows",
        actual=sum(as_int(row["patched_groups"]) < as_int(row["default_groups"]) for row in r354_summary),
        expected=2,
        source="profile-patch-summary.csv",
        paper_token="2/6",
    )
    add_check(
        rows,
        run_id="R354",
        key="csv_median_delta_ap",
        actual=round(float(median(as_float(row["delta_ap"]) for row in r354_summary)), 4),
        expected=0.0376,
        source="profile-patch-summary.csv",
        paper_token="0.0376",
        tolerance=5e-5,
    )
    add_check(
        rows,
        run_id="R354",
        key="csv_median_delta_top5_lift",
        actual=round(float(median(as_float(row["delta_top5_lift"]) for row in r354_summary)), 4),
        expected=0.5750,
        source="profile-patch-summary.csv",
        paper_token="0.5750",
        tolerance=2e-4,
    )
    add_check(
        rows,
        run_id="R354",
        key="csv_median_delta_first_positive_work",
        actual=round(float(median(as_float(row["delta_first_positive_work"]) for row in r354_summary)), 4),
        expected=-0.0859,
        source="profile-patch-summary.csv",
        paper_token="-0.0859",
        tolerance=5e-5,
    )

    add_check(
        rows,
        run_id="R354",
        key="agentpprof_result_status_ok",
        actual=sum(
            detail["default_agentpprof_result"]["status"] == "ok"
            and detail["patched_agentpprof_result"]["status"] == "ok"
            for detail in r354_report["tasks_detail"]
        ),
        expected=6,
        source="profile-patch-report.json tasks_detail",
        paper_token="12 Rust profile-spec invocations",
    )
    add_check(
        rows,
        run_id="R354",
        key="profile_specs_label_free",
        actual=sum(profile_spec_is_label_free(path) for path in spec_paths),
        expected=12,
        source="R354 profile specs",
        paper_token="hidden labels score after profiling",
    )
    add_check(
        rows,
        run_id="R354",
        key="nonclaim_no_human_or_agent_analyst",
        actual=any("not a human or agent analyst study" in item.lower() for item in r354_report["non_claims"]),
        expected=True,
        source="profile-patch-report.json non_claims",
        paper_token="not a human or agent analyst study",
    )
    add_check(
        rows,
        run_id="R354",
        key="nonclaim_not_automatic_patch_selector",
        actual=any("not an automatic label-free patch selector" in item.lower() for item in r354_report["non_claims"]),
        expected=True,
        source="profile-patch-report.json non_claims",
        paper_token="not an automatic label-free patch selector",
    )
    add_check(
        rows,
        run_id="R354",
        key="nonclaim_two_abstractions_only",
        actual=any("only profiler objects are operations and operation stacks" in item.lower() for item in r354_report["non_claims"]),
        expected=True,
        source="profile-patch-report.json non_claims",
        paper_token="operations and operation stacks",
    )
    return rows


def build_r355_checks(
    r355_report: dict[str, Any],
    r355_task_cards: list[dict[str, str]],
    r355_policy_summary: list[dict[str, str]],
    r355_policy_adequacy: list[dict[str, str]],
    r355_matrix: list[dict[str, str]],
    r355_comparisons: list[dict[str, str]],
    r355_run: dict[str, Any],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    claim = r355_report["claim_summary"]
    default_medians = claim["default_all_depth_medians"]
    positive_run_medians = claim["positive_run_medians"]
    paired = claim["paired_checks"]
    unit_depths = sorted(claim["unit_depths"])
    expected_depths = sorted(
        [
            "agentnet_step",
            "agentreward_turn",
            "operation",
            "osworld_human_group",
            "positive_run",
            "satraj_step",
            "session",
        ]
    )

    add_check(rows, run_id="R355", key="status", actual=r355_report["status"], expected="pass", source="oracle-depth-adequacy-report.json", paper_token="R355")
    add_check(rows, run_id="R355", key="run_result_status", actual=r355_run["status"], expected="pass", source="run-result.json", paper_token="pass")
    add_check(rows, run_id="R355", key="tasks", actual=claim["tasks"], expected=6, source="claim_summary", paper_token="6 tasks")
    add_check(rows, run_id="R355", key="datasets", actual=claim["datasets"], expected=4, source="claim_summary", paper_token="4 datasets")
    add_check(rows, run_id="R355", key="accuracy_unit_depth_rows", actual=claim["accuracy_unit_depth_rows"], expected=24, source="claim_summary", paper_token="24")
    add_check(rows, run_id="R355", key="subtask_eligible_unit_depth_rows", actual=claim["subtask_eligible_unit_depth_rows"], expected=16, source="claim_summary", paper_token="16")
    add_check(rows, run_id="R355", key="true_subtask_oracle_rows", actual=claim["true_subtask_oracle_rows"], expected=5, source="claim_summary", paper_token="5")
    add_check(rows, run_id="R355", key="context_only_rows", actual=claim["context_only_rows"], expected=1, source="claim_summary", paper_token="1 context-only")
    add_check(rows, run_id="R355", key="default_policy", actual=claim["default_policy"], expected="operation_stack:query_aware", source="claim_summary", paper_token="operation_stack:query_aware")
    add_check(rows, run_id="R355", key="unit_depths", actual=unit_depths, expected=expected_depths, source="claim_summary", paper_token="session, operation/step, positive-run")

    for key, expected in [
        ("top5_unit_work", 0.1307),
        ("budget30_positive_unit_recall", 0.4342),
        ("budget30_positive_unit_f1", 0.4484),
        ("budget30_spillover_operation_fraction", 0.7290),
        ("groups_to_50pct_positive_units", 27.5),
    ]:
        add_check(
            rows,
            run_id="R355",
            key=f"default_median_{key}",
            actual=default_medians[key],
            expected=expected,
            source="claim_summary.default_all_depth_medians",
            paper_token=f"{expected:.4f}",
            tolerance=5e-5,
        )
    add_check(
        rows,
        run_id="R355",
        key="positive_run_median_recall",
        actual=positive_run_medians["budget30_positive_unit_recall"],
        expected=0.4908,
        source="claim_summary.positive_run_medians",
        paper_token="0.4908",
        tolerance=5e-5,
    )
    for key, expected in [
        ("top5_unit_work_lt_flat_rows", 24),
        ("budget30_unit_recall_gt_fixed_rows", 20),
        ("budget30_unit_f1_gt_fixed_rows", 18),
        ("groups_to_50pct_units_lt_fixed_rows", 22),
        ("positive_units_per_group_lt_raw_rows", 24),
        ("depth_gap_lt_fixed_rows", 0),
    ]:
        add_check(
            rows,
            run_id="R355",
            key=key,
            actual=paired[key],
            expected=expected,
            source="claim_summary.paired_checks",
            paper_token=f"{expected}/24" if key != "depth_gap_lt_fixed_rows" else "0/24",
        )

    add_check(rows, run_id="R355", key="task_depth_card_rows", actual=len(r355_task_cards), expected=24, source="task-depth-cards.csv", paper_token="24")
    add_check(rows, run_id="R355", key="oracle_depth_matrix_rows", actual=len(r355_matrix), expected=25, source="oracle-depth-matrix.csv", paper_token="24 accuracy rows plus 1 context-only row")
    add_check(rows, run_id="R355", key="policy_depth_summary_rows", actual=len(r355_policy_summary), expected=42, source="policy-depth-summary.csv", paper_token="42")
    add_check(rows, run_id="R355", key="policy_depth_adequacy_rows", actual=len(r355_policy_adequacy), expected=144, source="policy-depth-adequacy.csv", paper_token="144")
    add_check(rows, run_id="R355", key="depth_policy_comparison_rows", actual=len(r355_comparisons), expected=50, source="depth-policy-comparisons.csv", paper_token="50")
    add_check(
        rows,
        run_id="R355",
        key="task_cards_default_policy_rows",
        actual=sum(row["best_budget30_unit_policy"] == "operation_stack:query_aware" for row in r355_task_cards),
        expected=10,
        source="task-depth-cards.csv",
        paper_token="operation-stack query-aware",
    )
    add_check(
        rows,
        run_id="R355",
        key="nonclaim_no_human_or_agent_analyst",
        actual=any("not a human or agent analyst study" in item.lower() for item in r355_report["non_claims"]),
        expected=True,
        source="oracle-depth-adequacy-report.json non_claims",
        paper_token="not a human or agent analyst study",
    )
    add_check(
        rows,
        run_id="R355",
        key="nonclaim_no_auto_all_boundaries",
        actual=any("does not claim automatic discovery of all intent boundaries" in item.lower() for item in r355_report["non_claims"]),
        expected=True,
        source="oracle-depth-adequacy-report.json non_claims",
        paper_token="does not claim automatic discovery of all intent boundaries",
    )
    add_check(
        rows,
        run_id="R355",
        key="nonclaim_positive_run_proxy",
        actual=any("positive-run units are derived proxy episodes" in item.lower() for item in r355_report["non_claims"]),
        expected=True,
        source="oracle-depth-adequacy-report.json non_claims",
        paper_token="positive-run proxy",
    )
    add_check(
        rows,
        run_id="R355",
        key="nonclaim_scalecua_context_only",
        actual=any("scalecua" in item.lower() and "context-only" in item.lower() for item in r355_report["non_claims"]),
        expected=True,
        source="oracle-depth-adequacy-report.json non_claims",
        paper_token="ScaleCUA context-only",
    )
    return rows


def contains_any(text: str, tokens: list[str]) -> bool:
    return any(token in text for token in tokens)


def contains_all(text: str, tokens: list[str]) -> bool:
    return all(token in text for token in tokens)


def line_hits(text: str, tokens: list[str], *, all_tokens: bool = False, limit: int = 8) -> list[int]:
    hits: list[int] = []
    for index, line in enumerate(text.splitlines(), start=1):
        matched = all(token in line for token in tokens) if all_tokens else any(token in line for token in tokens)
        if matched:
            hits.append(index)
            if len(hits) >= limit:
                break
    return hits


def add_text_check(
    rows: list[dict[str, Any]],
    doc: str,
    key: str,
    text: str,
    tokens: list[str],
    source: str,
    *,
    all_tokens: bool = True,
) -> None:
    status = "pass" if (contains_all(text, tokens) if all_tokens else contains_any(text, tokens)) else "fail"
    rows.append(
        {
            "doc": doc,
            "key": key,
            "source": source,
            "tokens": " / ".join(tokens),
            "status": status,
            "lines": ",".join(str(line) for line in line_hits(text, tokens, all_tokens=all_tokens)) or "missing",
        }
    )


def build_r356_text_coverage(texts: dict[str, str]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    requirements = [
        ("evaluation", "R354 profile patch", ["R354", "5/6", "0.0376", "0.5750"], "R354"),
        ("evaluation", "R355 oracle depth", ["R355", "24", "0.4342", "20/24", "22/24"], "R355"),
        ("evaluation", "R356 refresh", ["R356", "R354", "R355", "claim-integrity"], "R356"),
        ("zh_main", "R354 profile patch", ["R354", "5/6", "0.0376", "0.5750"], "R354"),
        ("zh_main", "R355 oracle depth", ["R355", "24", "0.4342", "20/24", "22/24"], "R355"),
        ("zh_main", "R356 refresh", ["R356", "R354", "R355", "claim-integrity"], "R356"),
        ("en_main", "R354 profile patch", ["R354", "5 of 6", "0.0376", "0.5750"], "R354"),
        ("en_main", "R355 oracle depth", ["R355", "24", "0.4342", "20/24", "22/24"], "R355"),
        ("en_main", "R356 refresh", ["R356", "R354", "R355", "claim-integrity"], "R356"),
        ("zh_claim_setup", "R354 profile patch", ["R354", "5/6", "0.0376", "0.5750"], "R354"),
        ("zh_claim_setup", "R355 oracle depth", ["R355", "24", "0.4342", "20/24", "22/24"], "R355"),
        ("zh_claim_setup", "R356 refresh", ["R356", "R354", "R355", "claim-integrity"], "R356"),
        ("design", "R356 audit boundary", ["R356", "R354", "R355", "operation stack"], "R356"),
        ("implementation", "R356 script", ["script/paper_claim_integrity_r356.py", "R356"], "R356"),
    ]
    for doc, key, tokens, source in requirements:
        add_text_check(rows, doc, key, texts[doc], tokens, source)

    add_text_check(
        rows,
        "evaluation",
        "R355 depth-gap counterpoint",
        texts["evaluation"],
        ["R355", "depth-gap", "fixed-session"],
        "R355",
    )
    add_text_check(
        rows,
        "en_main",
        "R355 depth-gap counterpoint",
        texts["en_main"],
        ["R355", "depth-gap", "fixed-session"],
        "R355",
    )
    add_text_check(
        rows,
        "zh_main",
        "R355 depth-gap counterpoint",
        texts["zh_main"],
        ["R355", "depth-gap", "fixed-session"],
        "R355",
    )
    add_text_check(
        rows,
        "zh_claim_setup",
        "R355 depth-gap counterpoint",
        texts["zh_claim_setup"],
        ["R355", "depth-gap", "fixed-session"],
        "R355",
    )
    return rows


def build_r356_guardrails(texts: dict[str, str]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for doc, text in texts.items():
        lower = text.lower()
        if "r354" in lower or "profile-spec patch" in lower:
            automatic_patch_guard = (
                "not an automatic" in lower
                or "not automatic" in lower
                or "不支持自动" in lower
                or "不是自动" in lower
                or "不是 label-free patch selector" in lower
                or "automatic patch selector" in lower
            )
            boundary_guard = "boundary-derived" in lower or "boundary backend" in lower or "边界" in text
            rows.append(
                {
                    "doc": doc,
                    "guardrail": "r354_not_automatic_patch_selector",
                    "status": "pass" if automatic_patch_guard else "fail",
                    "occurrences": lower.count("r354"),
                    "occurrence_lines": ",".join(str(line) for line in line_hits(text, ["R354"], all_tokens=False)) or "none",
                    "unguarded_lines": "none" if automatic_patch_guard else "missing automatic-patch guard",
                }
            )
            rows.append(
                {
                    "doc": doc,
                    "guardrail": "r354_boundary_derived_counterpoint",
                    "status": "pass" if boundary_guard else "fail",
                    "occurrences": lower.count("r354"),
                    "occurrence_lines": ",".join(str(line) for line in line_hits(text, ["R354"], all_tokens=False)) or "none",
                    "unguarded_lines": "none" if boundary_guard else "missing boundary-derived counterpoint",
                }
            )
        if "r355" in lower or "oracle-depth" in lower:
            boundary_guard = (
                "does not claim automatic discovery" in lower
                or "does not claim automatic boundary discovery" in lower
                or "does not support automatic" in lower
                or "does not prove" in lower
                or "not automatic recovery" in lower
                or "not complete intent-boundary discovery" in lower
                or "not complete intent-boundary" in lower
                or "not support" in lower
                or "不支持" in text
                or "不证明" in text
            )
            proxy_guard = "positive-run" in lower and ("proxy" in lower or "not human intent" in lower or "不是 human intent" in lower)
            depth_gap_guard = "depth-gap" in lower and "fixed-session" in lower
            rows.extend(
                [
                    {
                        "doc": doc,
                        "guardrail": "r355_no_latent_boundary_discovery",
                        "status": "pass" if boundary_guard else "fail",
                        "occurrences": lower.count("r355"),
                        "occurrence_lines": ",".join(str(line) for line in line_hits(text, ["R355"], all_tokens=False)) or "none",
                        "unguarded_lines": "none" if boundary_guard else "missing boundary-discovery guard",
                    },
                    {
                        "doc": doc,
                        "guardrail": "r355_positive_run_proxy",
                        "status": "pass" if proxy_guard else "fail",
                        "occurrences": lower.count("positive-run"),
                        "occurrence_lines": ",".join(str(line) for line in line_hits(text, ["positive-run"], all_tokens=False)) or "none",
                        "unguarded_lines": "none" if proxy_guard else "missing positive-run proxy guard",
                    },
                    {
                        "doc": doc,
                        "guardrail": "r355_depth_gap_counterpoint",
                        "status": "pass" if depth_gap_guard else "fail",
                        "occurrences": lower.count("depth-gap"),
                        "occurrence_lines": ",".join(str(line) for line in line_hits(text, ["depth-gap"], all_tokens=False)) or "none",
                        "unguarded_lines": "none" if depth_gap_guard else "missing fixed-session depth-gap counterpoint",
                    },
                ]
            )
    return rows


def row_status(rows: list[dict[str, Any]], *, fail_on_warn: bool = False) -> str:
    return r338.row_status(rows, fail_on_warn=fail_on_warn)


def build_markdown(path: Path, payload: dict[str, Any]) -> None:
    summary = payload["summary"]
    lines = [
        "# Paper Claim Integrity Refresh R356",
        "",
        "R356 reuses the R338 R320-R350 paper gate and extends it to R354/R355. It does not fetch, sync, create, or relabel datasets.",
        "",
        "## Verdict",
        "",
        f"- Overall: {summary['overall']}.",
        f"- Base R338 gate: {summary['base_r338_overall']}.",
        f"- R354/R355 result invariants: {summary['r354_r355_result_invariants']}.",
        f"- Paper text coverage: {summary['paper_text_coverage']}.",
        f"- Guardrails: {summary['guardrails']}.",
        f"- Two-abstraction boundary: {summary['two_abstraction_boundary']}.",
        f"- Source artifacts tracked clean: {summary['source_artifacts_tracked_clean']}.",
        "",
        "## Claim Position",
        "",
        payload["claim_position"],
        "",
        "## R354/R355 Checks",
        "",
        "| Run | Key | Expected | Actual | Status | Source |",
        "|---|---|---:|---:|---|---|",
    ]
    for row in payload["number_checks"]:
        lines.append(
            f"| {row['run_id']} | {row['key']} | {row['expected']} | {row['actual']} | {row['status']} | {row['source']} |"
        )
    lines.extend(
        [
            "",
            "## Text Coverage",
            "",
            "| Doc | Key | Tokens | Status | Lines |",
            "|---|---|---|---|---|",
        ]
    )
    for row in payload["text_coverage"]:
        lines.append(f"| {row['doc']} | {row['key']} | {row['tokens']} | {row['status']} | {row['lines']} |")
    lines.extend(
        [
            "",
            "## Guardrails",
            "",
            "| Doc | Guardrail | Status | Occurrences | Occurrence lines | Unguarded lines |",
            "|---|---|---|---:|---|---|",
        ]
    )
    for row in payload["guardrail_checks"]:
        lines.append(
            f"| {row['doc']} | {row['guardrail']} | {row['status']} | {row['occurrences']} | {row['occurrence_lines']} | {row['unguarded_lines']} |"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_html(path: Path, payload: dict[str, Any]) -> None:
    def table(rows: list[dict[str, Any]], fields: list[str]) -> str:
        head = "".join(f"<th>{html.escape(field)}</th>" for field in fields)
        body = []
        for row in rows:
            body.append(
                "<tr>"
                + "".join(f"<td>{html.escape(str(r338.round_value(row.get(field, ''))))}</td>" for field in fields)
                + "</tr>"
            )
        return f"<table><thead><tr>{head}</tr></thead><tbody>{''.join(body)}</tbody></table>"

    summary = payload["summary"]
    content = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>R356 Paper Claim Integrity Refresh</title>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, sans-serif; margin: 32px; line-height: 1.45; }}
    table {{ border-collapse: collapse; width: 100%; margin: 16px 0; font-size: 13px; }}
    th, td {{ border: 1px solid #d0d7de; padding: 6px 8px; text-align: left; vertical-align: top; }}
    th {{ background: #f6f8fa; }}
    code {{ background: #f6f8fa; padding: 1px 4px; border-radius: 4px; }}
  </style>
</head>
<body>
  <h1>R356 Paper Claim Integrity Refresh</h1>
  <p><strong>Overall:</strong> {html.escape(summary['overall'])}</p>
  <p>{html.escape(payload['claim_position'])}</p>
  <h2>Summary</h2>
  {table([summary], ['base_r338_overall', 'r354_r355_result_invariants', 'paper_text_coverage', 'guardrails', 'two_abstraction_boundary', 'source_artifacts_tracked_clean'])}
  <h2>Number Checks</h2>
  {table(payload['number_checks'], ['run_id', 'key', 'expected', 'actual', 'status', 'source'])}
  <h2>Text Coverage</h2>
  {table(payload['text_coverage'], ['doc', 'key', 'source', 'tokens', 'status', 'lines'])}
  <h2>Guardrails</h2>
  {table(payload['guardrail_checks'], ['doc', 'guardrail', 'status', 'occurrences', 'occurrence_lines', 'unguarded_lines'])}
</body>
</html>
"""
    path.write_text(content, encoding="utf-8")


def build_payload() -> dict[str, Any]:
    base_payload = r338.build_payload()
    r354_report = load_json(R354_REPORT)
    r354_summary = read_csv(R354_SUMMARY)
    r354_run = load_json(R354_RUN_RESULT)
    r355_report = load_json(R355_REPORT)
    r355_task_cards = read_csv(R355_TASK_CARDS)
    r355_policy_summary = read_csv(R355_POLICY_SUMMARY)
    r355_policy_adequacy = read_csv(R355_POLICY_ADEQUACY)
    r355_matrix = read_csv(R355_MATRIX)
    r355_comparisons = read_csv(R355_COMPARISONS)
    r355_run = load_json(R355_RUN_RESULT)

    source_status = collect_empirical_sources(r354_report, r355_report)
    texts, paper_status = load_texts()

    base_checks: list[dict[str, Any]] = []
    add_check(base_checks, run_id="R338", key="overall", actual=base_payload["summary"]["overall"], expected="pass", source="R338 build_payload summary", paper_token="R338")
    add_check(base_checks, run_id="R338", key="number_checks_total", actual=base_payload["summary"]["number_checks_total"], expected=350, source="R338 build_payload summary", paper_token="350")
    add_check(base_checks, run_id="R338", key="source_policy", actual=base_payload["summary"]["source_policy"], expected="pass", source="R338 build_payload summary", paper_token="source policy")
    add_check(base_checks, run_id="R338", key="guardrails", actual=base_payload["summary"]["guardrails"], expected="pass", source="R338 build_payload summary", paper_token="guardrails")
    add_check(base_checks, run_id="R338", key="two_abstraction_boundary", actual=base_payload["summary"]["two_abstraction_boundary"], expected="pass", source="R338 build_payload summary", paper_token="two abstractions")

    number_checks = (
        base_checks
        + build_r354_checks(r354_report, r354_summary, r354_run)
        + build_r355_checks(
            r355_report,
            r355_task_cards,
            r355_policy_summary,
            r355_policy_adequacy,
            r355_matrix,
            r355_comparisons,
            r355_run,
        )
    )
    text_coverage = build_r356_text_coverage(texts)
    guardrail_checks = r338.build_guardrail_checks(texts) + build_r356_guardrails(texts)
    abstraction_text_checks = r338.build_abstraction_text_checks(texts)

    result_status = row_status(number_checks)
    text_status = row_status(text_coverage, fail_on_warn=True)
    guardrail_status = row_status(guardrail_checks)
    abstraction_status = row_status(abstraction_text_checks)
    source_artifacts_clean = all(item["status"] == "tracked_clean" for item in source_status.values())

    status_pairs = [
        ("result_invariants", result_status),
        ("paper_text_coverage", text_status),
        ("guardrails", guardrail_status),
        ("two_abstraction_boundary", abstraction_status),
    ]
    blocking = [name for name, status in status_pairs if status == "fail"]
    warnings = [name for name, status in status_pairs if status == "warn"]
    if not source_artifacts_clean:
        blocking.append("source_artifacts_tracked_clean")
    overall = "pass" if not blocking else "fail"

    return {
        "schema": "agentsight.paper-claim-integrity-r356.v1",
        "run_id": RUN_ID,
        "input_policy": {
            "dataset_sync": "none",
            "dataset_creation": "none",
            "dataset_relabeling": "none",
            "network_access_required": False,
            "source_text_clean_policy": "paper/doc text sources may be current worktree edits and are hashed; empirical source artifacts must be tracked clean",
            "hidden_label_use": "R356 reads already-scored R354/R355 artifacts and verifies that hidden labels score profiles after visible ranking/profiling",
        },
        "non_claims": [
            "not a human/agent analyst study",
            "not evidence of human productivity, analyst accuracy, or time-to-answer",
            "not automatic discovery of all intent or semantic boundaries",
            "not an automatic label-free patch selector",
            "not complete compatibility with OpenTelemetry, Phoenix, LangSmith, Langfuse, or Perfetto ecosystems",
            "not a universal selector for one view, depth, ranker, or patch",
        ],
        "profiler_abstractions": r338.ABSTRACTIONS,
        "source_status": source_status,
        "paper_status": paper_status,
        "base_r338_summary": base_payload["summary"],
        "number_checks": number_checks,
        "text_coverage": text_coverage,
        "guardrail_checks": guardrail_checks,
        "abstraction_text_checks": abstraction_text_checks,
        "claim_position": (
            "R356 keeps the paper claim scoped to profiler fidelity, ranking, "
            "inspection work, fragmentation, oracle-depth triage, and executable "
            "profile-spec actionability on existing labeled traces. R354/R355 "
            "strengthen actionability and boundary-depth evidence, but they do "
            "not support automatic patch selection, human utility, or complete "
            "latent intent-boundary discovery."
        ),
        "summary": {
            "overall": overall,
            "blocking": blocking,
            "warnings": warnings,
            "base_r338_overall": base_payload["summary"]["overall"],
            "r354_r355_result_invariants": result_status,
            "paper_text_coverage": text_status,
            "guardrails": guardrail_status,
            "two_abstraction_boundary": abstraction_status,
            "number_checks_total": len(number_checks),
            "number_checks_passed": sum(row["status"] == "pass" for row in number_checks),
            "text_checks_total": len(text_coverage),
            "text_checks_passed": sum(row["status"] == "pass" for row in text_coverage),
            "guardrail_checks_total": len(guardrail_checks),
            "guardrail_checks_passed": sum(row["status"] == "pass" for row in guardrail_checks),
            "source_artifacts_tracked_clean": source_artifacts_clean,
            "paper_sources_hashed": len(paper_status),
            "profiler_abstractions": r338.ABSTRACTIONS,
            "network_access_required": False,
        },
    }


def main() -> None:
    args = parse_args()
    out_dir = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    payload = build_payload()
    write_json(out_dir / "claim-integrity-r356-report.json", payload)
    build_markdown(out_dir / "claim-integrity-r356-report.md", payload)
    build_html(out_dir / "index.html", payload)
    write_csv(
        out_dir / "number-checks.csv",
        payload["number_checks"],
        ["run_id", "key", "actual", "expected", "status", "source", "paper_token"],
    )
    write_csv(
        out_dir / "text-coverage.csv",
        payload["text_coverage"],
        ["doc", "key", "source", "tokens", "status", "lines"],
    )
    write_csv(
        out_dir / "guardrail-checks.csv",
        payload["guardrail_checks"],
        ["doc", "guardrail", "status", "occurrences", "occurrence_lines", "unguarded_lines"],
    )
    write_csv(
        out_dir / "abstraction-text-checks.csv",
        payload["abstraction_text_checks"],
        ["doc", "check", "status", "detail"],
    )
    source_rows = [
        {"name": name, **item} for name, item in payload["source_status"].items()
    ] + [{"name": name, **item} for name, item in payload["paper_status"].items()]
    write_csv(out_dir / "source-status.csv", source_rows, ["name", "path", "status", "sha256"])
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
