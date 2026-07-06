#!/usr/bin/env python3
"""R338: paper-claim integrity audit over R320-R347 evidence.

This audit does not fetch, sync, create, or relabel datasets. It reads tracked
result artifacts from the existing profiling-paper evaluation runs and the
current Chinese/English paper text, then checks that headline numbers, scope
guardrails, and the two-abstraction boundary remain aligned.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import html
import json
import math
import re
import subprocess
from collections import Counter, defaultdict
from pathlib import Path
from statistics import median
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OUT_ROOT = ROOT / "docs" / "visexp" / "out"
SUBMODULE_ROOT = ROOT / "docs" / "agentpprof-paper"
DEFAULT_OUT_DIR = OUT_ROOT / "paper-claim-integrity-r338"
RUN_ID = "R338"
ABSTRACTIONS = ["operation", "operation stack"]

R320_DIR = OUT_ROOT / "operation-profile-accuracy-r320"
R333_DIR = OUT_ROOT / "operation-inspection-frontier-r333"
R334_DIR = OUT_ROOT / "operation-fragmentation-tradeoff-r334"
R335_DIR = OUT_ROOT / "operation-actionability-synthesis-r335"
R336_DIR = OUT_ROOT / "operation-actionability-selection-r336"
R337_DIR = OUT_ROOT / "operation-inspection-target-r337"
R339_DIR = OUT_ROOT / "operation-sequence-adequacy-r339"
R340_DIR = OUT_ROOT / "operation-policy-transfer-r340"
R341_DIR = OUT_ROOT / "operation-mechanism-attribution-r341"
R342_DIR = OUT_ROOT / "operation-profile-spec-composition-r342"
R344_DIR = OUT_ROOT / "operation-metric-consistency-r344"
R345_DIR = OUT_ROOT / "operation-diagnostic-lens-portfolio-r345"
R346_DIR = OUT_ROOT / "operation-diagnostic-casebook-r346"
R347_DIR = OUT_ROOT / "operation-case-baseline-contrast-r347"

SOURCE_ARTIFACTS = {
    "R320 report": R320_DIR / "profile-accuracy-report.json",
    "R320 policy scores": R320_DIR / "policy-scores.csv",
    "R333 report": R333_DIR / "inspection-frontier-report.json",
    "R333 curve summary": R333_DIR / "policy-curve-summary.csv",
    "R334 report": R334_DIR / "fragmentation-tradeoff-report.json",
    "R334 default comparisons": R334_DIR / "default-fragmentation-comparisons.csv",
    "R334 budget comparisons": R334_DIR / "budget-fragmentation-comparisons.csv",
    "R335 report": R335_DIR / "actionability-synthesis-report.json",
    "R336 report": R336_DIR / "actionability-selection-report.json",
    "R336 policy objectives": R336_DIR / "policy-objective-summary.csv",
    "R337 report": R337_DIR / "inspection-target-report.json",
    "R337 policy targets": R337_DIR / "policy-target-summary.csv",
    "R337 default comparisons": R337_DIR / "default-target-comparisons.csv",
    "R339 report": R339_DIR / "sequence-adequacy-report.json",
    "R339 policy sequence summary": R339_DIR / "policy-sequence-summary.csv",
    "R339 default comparisons": R339_DIR / "default-sequence-comparisons.csv",
    "R340 report": R340_DIR / "policy-transfer-report.json",
    "R340 transfer decisions": R340_DIR / "transfer-decisions.csv",
    "R340 objective summary": R340_DIR / "objective-transfer-summary.csv",
    "R341 report": R341_DIR / "mechanism-attribution-report.json",
    "R341 objective attribution": R341_DIR / "objective-mechanism-attribution.csv",
    "R341 transfer attribution": R341_DIR / "transfer-error-attribution.csv",
    "R342 report": R342_DIR / "profile-spec-composition-report.json",
    "R342 variants": R342_DIR / "profile-spec-composition-variants.csv",
    "R342 tasks": R342_DIR / "profile-spec-composition-tasks.csv",
    "R344 report": R344_DIR / "metric-consistency-report.json",
    "R344 metric summary": R344_DIR / "metric-summary.csv",
    "R344 task metric deltas": R344_DIR / "task-metric-deltas.csv",
    "R345 report": R345_DIR / "diagnostic-lens-report.json",
    "R345 lens summary": R345_DIR / "diagnostic-lens-summary.csv",
    "R345 task cards": R345_DIR / "task-lens-cards.csv",
    "R345 counterpoint ledger": R345_DIR / "counterpoint-ledger.csv",
    "R346 report": R346_DIR / "diagnostic-casebook-report.json",
    "R346 task cards": R346_DIR / "task-diagnostic-case-cards.csv",
    "R346 top stack evidence": R346_DIR / "top-stack-evidence.csv",
    "R347 report": R347_DIR / "case-baseline-contrast-report.json",
    "R347 view metrics": R347_DIR / "view-case-metrics.csv",
    "R347 task cards": R347_DIR / "task-baseline-contrast-cards.csv",
    "R347 pair summary": R347_DIR / "baseline-pair-summary.csv",
    "R347 top group contrast": R347_DIR / "top-group-contrast.csv",
}

PAPER_SOURCES = {
    "evaluation": ROOT / "docs" / "evaluation.md",
    "zh_claim_setup": ROOT / "docs" / "visexp" / "paper" / "evaluation-claims-setup.zh-CN.md",
    "zh_main": ROOT / "docs" / "visexp" / "paper" / "main.tex",
    "en_main": SUBMODULE_ROOT / "main.tex",
}

NEGATION_MARKERS = [
    "不支持",
    "不能",
    "不是",
    "不证明",
    "没有证明",
    "不声称",
    "不 claim",
    "当前不",
    "不引入",
    "不增加",
    "不新增",
    "限制",
    "后续",
    "future",
    "not ",
    "not-",
    "does not",
    "without",
    "do not",
    "cannot",
    "limitation",
    "scope",
    "guardrail",
    "must-not",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    return parser.parse_args()


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return str(path.resolve())


def rel_to(path: Path, base: Path) -> str:
    try:
        return str(path.resolve().relative_to(base))
    except ValueError:
        return str(path.resolve())


def git_path_status(path: Path, *, repo_root: Path = ROOT, require_clean: bool) -> str:
    if not path.exists():
        raise SystemExit(f"missing source path {rel(path)}")
    display = rel_to(path, repo_root)
    tracked = subprocess.run(
        ["git", "ls-files", "--error-unmatch", "--", display],
        cwd=repo_root,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if tracked.returncode != 0:
        detail = tracked.stderr.strip() or tracked.stdout.strip()
        raise SystemExit(f"{rel(path)} is not git-tracked: {detail}")
    unstaged = subprocess.run(
        ["git", "diff", "--quiet", "--", display],
        cwd=repo_root,
        check=False,
    )
    staged = subprocess.run(
        ["git", "diff", "--cached", "--quiet", "--", display],
        cwd=repo_root,
        check=False,
    )
    dirty = unstaged.returncode != 0 or staged.returncode != 0
    if require_clean and dirty:
        raise SystemExit(f"{rel(path)} must be tracked-clean source evidence")
    return "tracked_clean" if not dirty else "tracked_dirty_allowed"


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as file:
        return list(csv.DictReader(file))


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


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: round_value(row.get(field)) for field in fields})


def as_float(value: str | float | int | None) -> float:
    if value in ("", None):
        return 0.0
    return float(value)


def as_int(value: str | int) -> int:
    return int(float(value))


def as_bool(value: str | bool) -> bool:
    if isinstance(value, bool):
        return value
    return value.lower() == "true"


def normalize_repo_path(value: str) -> Path:
    path = Path(value)
    if not path.is_absolute():
        path = ROOT / path
    else:
        parts = path.parts
        marker = ("docs", "visexp", "out")
        for index in range(0, len(parts) - len(marker) + 1):
            if parts[index : index + len(marker)] == marker:
                # Historical profiler artifacts may contain the worktree's
                # absolute path; preserve the artifact while making audits
                # reproducible from a relocated checkout.
                path = ROOT.joinpath(*parts[index:])
                break
    return path


def fmt_number(value: Any) -> str:
    if isinstance(value, float):
        if value.is_integer():
            return f"{value:.1f}"
        return f"{value:.4f}".rstrip("0").rstrip(".")
    if isinstance(value, int):
        return str(value)
    return str(value)


def policy_key(row: dict[str, str]) -> str:
    return f"{row['view']}:{row['ranker']}"


def visible_policy_names(rows: list[dict[str, str]]) -> set[str]:
    return {
        policy_key(row)
        for row in rows
        if row.get("uses_hidden_fields") == "False" and policy_is_non_oracle(policy_key(row))
    }


def policy_is_non_oracle(policy: str) -> bool:
    return "oracle" not in policy and not policy.startswith("label_drilldown:")


def median_metric(rows: list[dict[str, str]], policy: str, metric: str) -> float:
    values = [as_float(row[metric]) for row in rows if policy_key(row) == policy]
    if not values:
        raise SystemExit(f"missing policy metric {policy} {metric}")
    return float(median(values))


def paired_win_count(
    rows: list[dict[str, str]],
    policy: str,
    baseline: str,
    metric: str,
    *,
    higher: bool,
) -> int:
    by_task = {(row["task"], policy_key(row)): row for row in rows}
    tasks = sorted({row["task"] for row in rows})
    wins = 0
    for task in tasks:
        current = as_float(by_task[(task, policy)][metric])
        other = as_float(by_task[(task, baseline)][metric])
        if (higher and current > other) or (not higher and current < other):
            wins += 1
    return wins


def csv_lookup(rows: list[dict[str, str]], **filters: str) -> dict[str, str]:
    for row in rows:
        if all(row.get(key) == value for key, value in filters.items()):
            return row
    raise SystemExit(f"missing CSV row: {filters}")


def profile_stack_has_forbidden_frames(profile: dict[str, Any]) -> bool:
    stacks = profile["profile"]["stacks"]
    return any("session:" in stack or "prompt:" in stack for stack in stacks)


def r342_task_key(row: dict[str, str] | dict[str, Any]) -> tuple[str, str]:
    return (str(row["task"]), str(row["stack_kind"]))


def r342_source_paths(report: dict[str, Any]) -> list[Path]:
    paths = [normalize_repo_path(path) for path in report.get("source_paths", [])]
    if not paths:
        raise SystemExit("R342 report has no source_paths")
    return paths


def build_r342_rows_from_sources(report: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    source_paths = r342_source_paths(report)
    source_set = {path.resolve() for path in source_paths}
    r324_reports = [path for path in source_paths if path.name == "rank-feature-report.json"]
    r324_summaries = [path for path in source_paths if path.name == "rank-feature-summary.csv"]
    if len(r324_reports) != 1 or len(r324_summaries) != 1:
        raise SystemExit("R342 source_paths must contain exactly one R324 report and summary")
    r324_report = load_json(r324_reports[0])
    r324_summary = read_csv(r324_summaries[0])
    summary_by_key = {r342_task_key(row): row for row in r324_summary}

    variant_rows: list[dict[str, Any]] = []
    for detail in r324_report["tasks_detail"]:
        key = (detail["task"], detail["stack_kind"])
        summary = summary_by_key[key]
        spec_path = normalize_repo_path(detail["profile_spec"])
        rust_json_path = normalize_repo_path(detail["rust_json"])
        if spec_path.resolve() not in source_set:
            raise SystemExit(f"R342 source_paths omit profile spec {rel(spec_path)}")
        if rust_json_path.resolve() not in source_set:
            raise SystemExit(f"R342 source_paths omit Rust JSON {rel(rust_json_path)}")
        spec = load_json(spec_path)
        rust_profile = load_json(rust_json_path)
        operation_paths = [normalize_repo_path(path) for path in spec.get("operation_files") or []]
        if not operation_paths:
            raise SystemExit(f"R342 profile spec has no operation files: {rel(spec_path)}")
        for operation_path in operation_paths:
            if operation_path.resolve() not in source_set:
                raise SystemExit(f"R342 source_paths omit operation file {rel(operation_path)}")
        where_rules = spec.get("where_rules") or []
        rank_op_rules = spec.get("rank_op_rules") or []
        stack = spec["stack"]
        variant_rows.append(
            {
                "task": detail["task"],
                "dataset": detail["dataset"],
                "stack_kind": detail["stack_kind"],
                "summary_groups": int(summary["groups"]),
                "positives": int(summary["positives"]),
                "profile_spec_composes_pipeline": bool(
                    operation_paths
                    and all(path.exists() for path in operation_paths)
                    and where_rules
                    and rank_op_rules
                    and spec.get("rank_mode") == "rule-score"
                    and stack
                ),
                "has_prompt_or_session_frame": profile_stack_has_forbidden_frames(rust_profile),
                "ranking_policy": rust_profile["profile"]["ranking"]["policy"],
                "width_ap": as_float(summary["width_ap"]),
                "op_feature_ap": as_float(summary["op_feature_ap"]),
                "delta_ap": as_float(summary["delta_ap"]),
                "delta_top5_lift": as_float(summary["delta_top5_lift"]),
                "width_first_positive_work": as_float(summary["width_first_positive_work"]),
                "op_feature_first_positive_work": as_float(summary["op_feature_first_positive_work"]),
                "delta_first_positive_work": as_float(summary["delta_first_positive_work"]),
                "operation_file_count": len(operation_paths),
                "profile_spec": rel(spec_path),
                "rust_json": rel(rust_json_path),
            }
        )

    by_task: dict[str, dict[str, dict[str, Any]]] = {}
    for row in variant_rows:
        by_task.setdefault(row["task"], {})[row["stack_kind"]] = row
    task_rows: list[dict[str, Any]] = []
    for task, variants in sorted(by_task.items()):
        semantic = variants["semantic"]
        coarse = variants["coarse"]
        group_reduction = 1.0 - (coarse["summary_groups"] / semantic["summary_groups"])
        best_ap = max(variants.values(), key=lambda row: row["op_feature_ap"])
        best_first_positive = min(
            variants.values(),
            key=lambda row: (
                row["op_feature_first_positive_work"] is None,
                row["op_feature_first_positive_work"] if row["op_feature_first_positive_work"] is not None else 1e9,
            ),
        )
        task_rows.append(
            {
                "task": task,
                "dataset": semantic["dataset"],
                "semantic_groups": semantic["summary_groups"],
                "coarse_groups": coarse["summary_groups"],
                "coarse_group_reduction": group_reduction,
                "best_ap_stack_kind": best_ap["stack_kind"],
                "best_ap": best_ap["op_feature_ap"],
                "best_first_positive_stack_kind": best_first_positive["stack_kind"],
                "best_first_positive_work": best_first_positive["op_feature_first_positive_work"],
                "best_first_positive_delta": best_first_positive["delta_first_positive_work"],
                "ap_improves_at_any_depth": any(row["delta_ap"] > 0 for row in variants.values()),
                "first_positive_improves_at_any_depth": any(
                    row["delta_first_positive_work"] is not None
                    and row["delta_first_positive_work"] < 0
                    for row in variants.values()
                ),
                "depth_choice_changes_objective": best_ap["stack_kind"] != best_first_positive["stack_kind"],
            }
        )
    return variant_rows, task_rows


def r342_committed_variant_matches(derived: dict[str, Any], committed: dict[str, str]) -> bool:
    return (
        committed["profile_spec_composes_pipeline"] == str(derived["profile_spec_composes_pipeline"])
        and committed["has_prompt_or_session_frame"] == str(derived["has_prompt_or_session_frame"])
        and committed["ranking_policy"] == derived["ranking_policy"]
        and as_int(committed["operation_file_count"]) == derived["operation_file_count"]
        and abs(as_float(committed["delta_ap"]) - derived["delta_ap"]) <= 5e-5
        and abs(as_float(committed["delta_top5_lift"]) - derived["delta_top5_lift"]) <= 5e-5
        and abs(as_float(committed["delta_first_positive_work"]) - derived["delta_first_positive_work"]) <= 5e-5
    )


def r342_committed_task_matches(derived: dict[str, Any], committed: dict[str, str]) -> bool:
    return (
        committed["best_ap_stack_kind"] == derived["best_ap_stack_kind"]
        and committed["best_first_positive_stack_kind"] == derived["best_first_positive_stack_kind"]
        and committed["depth_choice_changes_objective"] == str(derived["depth_choice_changes_objective"])
        and abs(as_float(committed["coarse_group_reduction"]) - derived["coarse_group_reduction"]) <= 5e-5
    )


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
    if isinstance(expected, float) or isinstance(actual, float):
        status = "pass" if abs(float(actual) - float(expected)) <= tolerance else "fail"
    else:
        status = "pass" if actual == expected else "fail"
    rows.append(
        {
            "run_id": run_id,
            "key": key,
            "actual": actual,
            "expected": expected,
            "status": status,
            "source": source,
            "paper_token": paper_token or fmt_number(expected),
        }
    )


def validate_source_policies(reports: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for run_id, report in reports.items():
        input_policy = report.get("input_policy", {})
        summary = report.get("summary", {})
        abstractions = report.get("profiler_abstractions", summary.get("profiler_abstractions"))
        add_check(
            rows,
            run_id=run_id,
            key="profiler_abstractions",
            actual=abstractions,
            expected=ABSTRACTIONS,
            source="report.profiler_abstractions",
            paper_token="operation stack",
        )
        for field in ["dataset_sync", "sync"]:
            if field in input_policy:
                add_check(
                    rows,
                    run_id=run_id,
                    key=field,
                    actual=input_policy[field],
                    expected="none",
                    source=f"report.input_policy.{field}",
                    paper_token="sync",
                )
        for field in ["dataset_creation", "create"]:
            if field in input_policy:
                add_check(
                    rows,
                    run_id=run_id,
                    key=field,
                    actual=input_policy[field],
                    expected="none",
                    source=f"report.input_policy.{field}",
                    paper_token="create",
                )
        for field in ["dataset_relabeling", "relabel"]:
            if field in input_policy:
                add_check(
                    rows,
                    run_id=run_id,
                    key=field,
                    actual=input_policy[field],
                    expected="none",
                    source=f"report.input_policy.{field}",
                    paper_token="relabel",
                )
        if "network_access_required" in report:
            add_check(
                rows,
                run_id=run_id,
                key="network_access_required",
                actual=report["network_access_required"],
                expected=False,
                source="report.network_access_required",
                paper_token="network",
            )
        elif "reproducibility" in report and "network_access_required" in report["reproducibility"]:
            add_check(
                rows,
                run_id=run_id,
                key="network_access_required",
                actual=report["reproducibility"]["network_access_required"],
                expected=False,
                source="report.reproducibility.network_access_required",
                paper_token="network",
            )
        elif "network_access_required" in summary:
            add_check(
                rows,
                run_id=run_id,
                key="network_access_required",
                actual=summary["network_access_required"],
                expected=False,
                source="report.summary.network_access_required",
                paper_token="network",
            )
        if "hidden_labels_used_only_for_scoring" in summary:
            add_check(
                rows,
                run_id=run_id,
                key="hidden_labels_used_only_for_scoring",
                actual=summary["hidden_labels_used_only_for_scoring"],
                expected=True,
                source="report.summary.hidden_labels_used_only_for_scoring",
                paper_token="hidden labels only for scoring",
            )
        if "source_artifacts_tracked_clean" in summary:
            add_check(
                rows,
                run_id=run_id,
                key="source_artifacts_tracked_clean",
                actual=summary["source_artifacts_tracked_clean"],
                expected=True,
                source="report.summary.source_artifacts_tracked_clean",
                paper_token="tracked clean",
            )
    return rows


def build_number_checks(
    reports: dict[str, dict[str, Any]],
    r320_scores: list[dict[str, str]],
    r333_summary: list[dict[str, str]],
    r334_default: list[dict[str, str]],
    r334_budget: list[dict[str, str]],
    r337_targets: list[dict[str, str]],
    r337_comparisons: list[dict[str, str]],
    r339_policy_summary: list[dict[str, str]],
    r339_comparisons: list[dict[str, str]],
    r340_decisions: list[dict[str, str]],
    r340_objectives: list[dict[str, str]],
    r341_objectives: list[dict[str, str]],
    r341_transfer: list[dict[str, str]],
    r342_variants: list[dict[str, str]],
    r342_tasks: list[dict[str, str]],
    r342_source_variants: list[dict[str, Any]],
    r342_source_tasks: list[dict[str, Any]],
    r344_metric_summary: list[dict[str, str]],
    r344_task_deltas: list[dict[str, str]],
    r345_lens_summary: list[dict[str, str]],
    r345_task_cards: list[dict[str, str]],
    r345_counterpoints: list[dict[str, str]],
    r346_task_cards: list[dict[str, str]],
    r346_top_stack_evidence: list[dict[str, str]],
    r347_view_metrics: list[dict[str, str]],
    r347_task_cards: list[dict[str, str]],
    r347_pair_summary: list[dict[str, str]],
    r347_top_group_contrast: list[dict[str, str]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    r320 = reports["R320"]
    totals = r320["totals"]
    add_check(rows, run_id="R320", key="datasets", actual=totals["datasets"], expected=4, source="R320 totals")
    add_check(rows, run_id="R320", key="tasks", actual=totals["tasks"], expected=6, source="R320 totals")
    add_check(
        rows,
        run_id="R320",
        key="operations",
        actual=totals["task_operations"],
        expected=34539,
        source="R320 totals",
        paper_token="34,539",
    )
    add_check(
        rows,
        run_id="R320",
        key="positives",
        actual=totals["positive_operations"],
        expected=3699,
        source="R320 totals",
        paper_token="3,699",
    )
    add_check(
        rows,
        run_id="R320",
        key="policies",
        actual=totals["policy_scores"],
        expected=144,
        source="R320 totals",
    )
    add_check(
        rows,
        run_id="R320",
        key="operation_stack_top5_work_median",
        actual=median_metric(r320_scores, "operation_stack:query_aware", "top5_work"),
        expected=0.0937,
        source="R320 policy-scores.csv",
        paper_token="0.0937",
        tolerance=5e-5,
    )
    add_check(
        rows,
        run_id="R320",
        key="flat_top5_work_median",
        actual=median_metric(r320_scores, "flat:width", "top5_work"),
        expected=1.0,
        source="R320 policy-scores.csv",
        paper_token="1.0",
    )
    add_check(
        rows,
        run_id="R320",
        key="operation_stack_groups_median",
        actual=median_metric(r320_scores, "operation_stack:query_aware", "groups"),
        expected=157.5,
        source="R320 policy-scores.csv",
        paper_token="157.5",
    )
    add_check(
        rows,
        run_id="R320",
        key="fixed_session_groups_median",
        actual=median_metric(r320_scores, "fixed_session:query_aware", "groups"),
        expected=285.0,
        source="R320 policy-scores.csv",
        paper_token="285.0",
    )
    add_check(
        rows,
        run_id="R320",
        key="top5_recall_wins_vs_fixed",
        actual=paired_win_count(
            r320_scores,
            "operation_stack:query_aware",
            "fixed_session:query_aware",
            "top5_recall",
            higher=True,
        ),
        expected=5,
        source="R320 policy-scores.csv",
        paper_token="5/6",
    )
    add_check(
        rows,
        run_id="R320",
        key="ap_wins_vs_width",
        actual=paired_win_count(
            r320_scores,
            "operation_stack:query_aware",
            "operation_stack:width",
            "average_precision",
            higher=True,
        ),
        expected=6,
        source="R320 policy-scores.csv",
        paper_token="6/6",
    )

    for policy, expected in [
        ("operation_stack:query_aware", 0.3900),
        ("flat:width", 0.0),
        ("fixed_session:query_aware", 0.3559),
        ("dataset_native:query_aware", 0.3377),
        ("raw_action_stack:query_aware", 0.3325),
    ]:
        row = csv_lookup(r333_summary, policy=policy, work_budget="0.3")
        add_check(
            rows,
            run_id="R333",
            key=f"{policy}_budget30_median_recall",
            actual=as_float(row["median_recall"]),
            expected=expected,
            source="R333 policy-curve-summary.csv",
            paper_token=f"{expected:.4f}",
            tolerance=5e-5,
        )

    fixed_rows = [
        ("groups", "groups_lower_than_fixed", 4),
        ("positive_groups", "positive_groups_lower_than_fixed", 4),
        ("groups_to_50pct_recall", "groups_to_50pct_lower_than_fixed", 5),
        ("work_to_50pct_recall", "work_to_50pct_lower_than_fixed", 1),
        ("top5_work", "top5_work_lower_than_fixed", 2),
        ("work_to_first_positive", "wtfp_lower_than_fixed", 2),
    ]
    for metric, key, expected in fixed_rows:
        row = csv_lookup(
            r334_default,
            baseline_policy="fixed_session:query_aware",
            metric=metric,
        )
        add_check(
            rows,
            run_id="R334",
            key=key,
            actual=as_int(row["wins"]),
            expected=expected,
            source="R334 default-fragmentation-comparisons.csv",
            paper_token=f"{expected}/6",
        )
    row = csv_lookup(
        r334_budget,
        baseline_policy="fixed_session:query_aware",
        work_budget="0.3",
        metric="groups_inspected",
    )
    add_check(
        rows,
        run_id="R334",
        key="budget30_groups_lower_than_fixed",
        actual=as_int(row["wins"]),
        expected=5,
        source="R334 budget-fragmentation-comparisons.csv",
        paper_token="5/6",
    )
    add_check(
        rows,
        run_id="R334",
        key="budget30_groups_median_delta_vs_fixed",
        actual=as_float(row["median_delta_default_minus_baseline"]),
        expected=-54.0,
        source="R334 budget-fragmentation-comparisons.csv",
        paper_token="-54.0",
    )

    r335 = reports["R335"]["summary"]
    for key, expected in [
        ("actionability_cards", 6),
        ("cards_with_optimization_action", 6),
        ("cards_with_ranker_ap_gain", 6),
        ("cards_with_positive_mapping_gain", 2),
        ("cards_with_negative_mapping_gain", 4),
        ("cards_with_critical_features", 4),
        ("cards_with_misleading_features", 2),
        ("cards_where_coarse_reduces_groups", 6),
        ("cards_where_coarse_preferred_by_ap", 2),
        ("cards_where_fixed_session_has_lower_wtfp", 4),
    ]:
        add_check(
            rows,
            run_id="R335",
            key=key,
            actual=r335[key],
            expected=expected,
            source="R335 summary",
            paper_token=f"{expected}/6" if expected <= 6 else str(expected),
        )

    r336 = reports["R336"]["summary"]
    add_check(rows, run_id="R336", key="visible_policies", actual=r336["visible_policies"], expected=15, source="R336 summary")
    add_check(rows, run_id="R336", key="objectives", actual=r336["objectives"], expected=6, source="R336 summary")
    add_check(
        rows,
        run_id="R336",
        key="pareto_operation_stack_query_aware",
        actual=r336["pareto_frontier_task_counts"]["operation_stack:query_aware"],
        expected=6,
        source="R336 summary",
        paper_token="6/6",
    )
    add_check(
        rows,
        run_id="R336",
        key="best_ap_operation_stack_query_aware",
        actual=r336["operation_stack_query_aware_best_counts"]["ranking_fidelity_ap"],
        expected=3,
        source="R336 summary",
        paper_token="3/6",
    )
    add_check(
        rows,
        run_id="R336",
        key="best_budget30_operation_stack_query_aware",
        actual=r336["operation_stack_query_aware_best_counts"]["budget30_recall"],
        expected=3,
        source="R336 summary",
        paper_token="3/6",
    )
    for key, expected in [
        ("top5_work_lower_than_flat", 6),
        ("top5_recall_higher_than_fixed", 5),
        ("groups_to_50pct_lower_than_fixed", 5),
        ("work_to_first_positive_lower_than_fixed", 2),
    ]:
        add_check(
            rows,
            run_id="R336",
            key=key,
            actual=r336["default_vs_baselines"][key],
            expected=expected,
            source="R336 summary.default_vs_baselines",
            paper_token=f"{expected}/6",
        )
    add_check(
        rows,
        run_id="R336",
        key="multiple_best_policies_across_objectives",
        actual=r336["tasks_with_multiple_best_policies_across_objectives"],
        expected=6,
        source="R336 summary",
        paper_token="6/6",
    )

    r337 = reports["R337"]["summary"]
    op = r337["operation_stack_query_aware"]
    fixed = r337["fixed_session_query_aware"]
    flat = r337["flat_width"]
    for key, actual, expected, token in [
        ("target25_tasks_reached", op["target25_tasks_reached"], 6, "6/6"),
        ("target25_median_work", op["target25_median_work"], 0.2, "0.2000"),
        ("target25_median_groups", op["target25_median_groups"], 16.0, "16.0"),
        ("target10_tasks_reached", op["target10_tasks_reached"], 6, "6/6"),
        ("target10_median_groups", op["target10_median_groups"], 12.5, "12.5"),
        ("target50_tasks_reached", op["target50_tasks_reached"], 5, "5/6"),
        ("flat_target25_median_work", flat["target25_median_work"], 1.0, "1.0000"),
        ("fixed_target25_median_groups", fixed["target25_median_groups"], 50.0, "50.0"),
        ("fixed_target10_median_groups", fixed["target10_median_groups"], 37.5, "37.5"),
        ("default_vs_flat_target25_work_wins", r337["default_vs_flat_target25"]["work_wins"], 6, "6/6"),
        ("default_vs_fixed_target25_group_wins", r337["default_vs_fixed_target25"]["group_wins"], 5, "5/6"),
        ("default_vs_fixed_target10_group_wins", r337["default_vs_fixed_target10"]["group_wins"], 5, "5/6"),
    ]:
        add_check(
            rows,
            run_id="R337",
            key=key,
            actual=actual,
            expected=expected,
            source="R337 summary",
            paper_token=token,
            tolerance=5e-5,
        )

    # Cross-check the summary against the public CSV rows used by readers.
    row = csv_lookup(r337_targets, policy="operation_stack:query_aware", target_recall="0.25")
    add_check(
        rows,
        run_id="R337",
        key="target25_csv_median_work",
        actual=as_float(row["median_min_work"]),
        expected=0.2,
        source="R337 policy-target-summary.csv",
        paper_token="0.2000",
    )
    row = csv_lookup(
        r337_comparisons,
        baseline_policy="fixed_session:query_aware",
        target_recall="0.25",
    )
    add_check(
        rows,
        run_id="R337",
        key="target25_csv_group_wins_vs_fixed",
        actual=as_int(row["group_wins"]),
        expected=5,
        source="R337 default-target-comparisons.csv",
        paper_token="5/6",
    )

    r339 = reports["R339"]
    r339_summary = r339["summary"]
    r339_claim = r339["claim_summary"]
    add_check(rows, run_id="R339", key="overall", actual=r339_summary["overall"], expected="pass", source="R339 summary")
    add_check(rows, run_id="R339", key="datasets", actual=len(r339_summary["datasets"]), expected=4, source="R339 summary")
    add_check(rows, run_id="R339", key="tasks", actual=r339_summary["tasks"], expected=6, source="R339 summary")
    add_check(rows, run_id="R339", key="policies_scored", actual=r339_summary["policies_scored"], expected=144, source="R339 summary")
    add_check(
        rows,
        run_id="R339",
        key="hidden_labels_used_only_for_scoring",
        actual=r339_summary["hidden_labels_used_only_for_scoring"],
        expected=True,
        source="R339 summary",
        paper_token="hidden labels only for scoring",
    )
    for key, expected, token in [
        ("median_operation_work", 0.0937, "0.0937"),
        ("median_positive_session_recall", 0.2629, "0.2629"),
        ("fixed_positive_session_recall", 0.0160, "0.0160"),
        ("flat_operation_work", 1.0, "1.0000"),
    ]:
        add_check(
            rows,
            run_id="R339",
            key=f"top5_{key}",
            actual=r339_claim["top5"][key],
            expected=expected,
            source="R339 claim_summary.top5",
            paper_token=token,
            tolerance=5e-5,
        )
    for key, expected, token in [
        ("median_positive_operation_recall", 0.3900, "0.3900"),
        ("median_positive_session_recall", 0.4669, "0.4669"),
        ("median_session_work", 0.3467, "0.3467"),
        ("fixed_positive_session_recall", 0.3230, "0.3230"),
        ("raw_action_positive_session_recall", 0.5147, "0.5147"),
        ("raw_action_session_work", 0.9103, "0.9103"),
    ]:
        add_check(
            rows,
            run_id="R339",
            key=f"budget30_{key}",
            actual=r339_claim["budget30"][key],
            expected=expected,
            source="R339 claim_summary.budget30",
            paper_token=token,
            tolerance=5e-5,
        )
    for key, expected, token in [
        ("top5_operation_work_lt_flat_tasks", 6, "6/6"),
        ("budget30_session_recall_gt_fixed_tasks", 6, "6/6"),
        ("budget30_session_work_lt_raw_action_tasks", 5, "5/6"),
    ]:
        add_check(
            rows,
            run_id="R339",
            key=key,
            actual=r339_claim["paired_checks"][key],
            expected=expected,
            source="R339 claim_summary.paired_checks",
            paper_token=token,
        )
    row = csv_lookup(r339_policy_summary, policy="operation_stack:query_aware")
    for field, expected, token in [
        ("median_top5_operation_work", 0.0937, "0.0937"),
        ("median_top5_positive_session_recall", 0.2629, "0.2629"),
        ("median_budget30_positive_operation_recall", 0.3900, "0.3900"),
        ("median_budget30_positive_session_recall", 0.4669, "0.4669"),
        ("median_budget30_session_work", 0.3467, "0.3467"),
    ]:
        add_check(
            rows,
            run_id="R339",
            key=f"csv_default_{field}",
            actual=as_float(row[field]),
            expected=expected,
            source="R339 policy-sequence-summary.csv",
            paper_token=token,
            tolerance=5e-5,
        )
    row = csv_lookup(
        r339_comparisons,
        comparison="vs_fixed_session_query_aware",
        metric="budget30_positive_session_recall",
    )
    add_check(
        rows,
        run_id="R339",
        key="csv_budget30_session_recall_wins_vs_fixed",
        actual=as_int(row["improved_tasks"]),
        expected=6,
        source="R339 default-sequence-comparisons.csv",
        paper_token="6/6",
    )
    row = csv_lookup(
        r339_comparisons,
        comparison="vs_raw_action_query_aware",
        metric="budget30_session_work",
    )
    add_check(
        rows,
        run_id="R339",
        key="csv_budget30_session_work_wins_vs_raw_action",
        actual=as_int(row["improved_tasks"]),
        expected=5,
        source="R339 default-sequence-comparisons.csv",
        paper_token="5/6",
    )

    r340 = reports["R340"]
    r340_summary = r340["summary"]
    r340_claim = r340["claim_summary"]
    add_check(rows, run_id="R340", key="overall", actual=r340_summary["overall"], expected="pass", source="R340 summary")
    add_check(rows, run_id="R340", key="tasks", actual=r340_claim["tasks"], expected=6, source="R340 claim_summary")
    add_check(rows, run_id="R340", key="visible_policies", actual=r340_claim["visible_policies"], expected=15, source="R340 claim_summary")
    add_check(rows, run_id="R340", key="objectives", actual=r340_claim["objectives"], expected=8, source="R340 claim_summary")
    add_check(rows, run_id="R340", key="total_decisions", actual=r340_claim["total_decisions"], expected=96, source="R340 claim_summary")
    add_check(rows, run_id="R340", key="exact_best_decisions", actual=r340_claim["exact_best_decisions"], expected=31, source="R340 claim_summary")
    add_check(rows, run_id="R340", key="within_tolerance_decisions", actual=r340_claim["within_tolerance_decisions"], expected=62, source="R340 claim_summary")
    add_check(rows, run_id="R340", key="selected_beats_width", actual=r340_claim["selected_beats_width_decisions"], expected=72, source="R340 claim_summary")
    add_check(rows, run_id="R340", key="selected_beats_fixed", actual=r340_claim["selected_beats_fixed_decisions"], expected=69, source="R340 claim_summary")
    add_check(rows, run_id="R340", key="selected_beats_flat", actual=r340_claim["selected_beats_flat_decisions"], expected=41, source="R340 claim_summary")
    add_check(rows, run_id="R340", key="operation_stack_selected", actual=r340_claim["operation_stack_selected_decisions"], expected=16, source="R340 claim_summary")
    add_check(rows, run_id="R340", key="leave_task_decisions", actual=r340_claim["leave_task"]["decisions"], expected=48, source="R340 claim_summary.leave_task")
    add_check(rows, run_id="R340", key="leave_task_within_tolerance", actual=r340_claim["leave_task"]["within_tolerance"], expected=32, source="R340 claim_summary.leave_task")
    add_check(rows, run_id="R340", key="leave_dataset_decisions", actual=r340_claim["leave_dataset"]["decisions"], expected=48, source="R340 claim_summary.leave_dataset")
    add_check(rows, run_id="R340", key="leave_dataset_within_tolerance", actual=r340_claim["leave_dataset"]["within_tolerance"], expected=30, source="R340 claim_summary.leave_dataset")
    add_check(rows, run_id="R340", key="decision_rows", actual=len(r340_decisions), expected=96, source="R340 transfer-decisions.csv")
    add_check(rows, run_id="R340", key="objective_rows", actual=len(r340_objectives), expected=16, source="R340 objective-transfer-summary.csv")

    visible_policies = visible_policy_names(r320_scores)
    task_dataset = {}
    for row in r320_scores:
        task_dataset.setdefault(row["task"], row["dataset"])
    dataset_task_counts = Counter(task_dataset.values())
    total_tasks = len(task_dataset)
    add_check(
        rows,
        run_id="R340",
        key="selected_policy_visible_rows",
        actual=sum(row["selected_policy"] in visible_policies for row in r340_decisions),
        expected=len(r340_decisions),
        source="R340 transfer-decisions.csv + R320 policy-scores.csv",
        paper_token="96/96",
    )
    add_check(
        rows,
        run_id="R340",
        key="best_policy_visible_rows",
        actual=sum(row["best_visible_policy"] in visible_policies for row in r340_decisions),
        expected=len(r340_decisions),
        source="R340 transfer-decisions.csv + R320 policy-scores.csv",
        paper_token="96/96",
    )
    add_check(
        rows,
        run_id="R340",
        key="selected_policy_no_oracle_or_label_drilldown",
        actual=sum(policy_is_non_oracle(row["selected_policy"]) for row in r340_decisions),
        expected=len(r340_decisions),
        source="R340 transfer-decisions.csv",
        paper_token="96/96",
    )
    add_check(
        rows,
        run_id="R340",
        key="best_policy_no_oracle_or_label_drilldown",
        actual=sum(policy_is_non_oracle(row["best_visible_policy"]) for row in r340_decisions),
        expected=len(r340_decisions),
        source="R340 transfer-decisions.csv",
        paper_token="96/96",
    )
    add_check(
        rows,
        run_id="R340",
        key="leave_task_excludes_target_task",
        actual=sum(
            row["protocol"] != "leave_task" or as_int(row["train_tasks"]) == total_tasks - 1
            for row in r340_decisions
        ),
        expected=len(r340_decisions),
        source="R340 transfer-decisions.csv",
        paper_token="96/96",
    )
    add_check(
        rows,
        run_id="R340",
        key="leave_dataset_excludes_target_dataset",
        actual=sum(
            row["protocol"] != "leave_dataset"
            or as_int(row["train_tasks"]) == total_tasks - dataset_task_counts[row["dataset"]]
            for row in r340_decisions
        ),
        expected=len(r340_decisions),
        source="R340 transfer-decisions.csv + R320 policy-scores.csv",
        paper_token="96/96",
    )

    r341_tasks = sorted({row["task"] for row in r341_objectives})
    r341_transfer_misses = [row for row in r341_transfer if not as_bool(row["selected_within_tolerance"])]
    r341_mechanisms_by_task: dict[str, set[str]] = defaultdict(set)
    for row in r341_objectives:
        for label in row["mechanism_labels"].split("; "):
            if label:
                r341_mechanisms_by_task[row["task"]].add(label)
    r341_mechanism_counts = Counter(
        label for labels in r341_mechanisms_by_task.values() for label in labels
    )
    r341_overall = "pass" if (
        len(r341_tasks) == 6
        and len(r341_objectives) == 36
        and sum(row["best_policy"] in visible_policies for row in r341_objectives) == 36
        and sum(policy_is_non_oracle(row["best_policy"]) for row in r341_objectives) == 36
        and sum(as_bool(row["actionable"]) for row in r341_objectives) == 36
        and sum(row["best_policy"] != "operation_stack:query_aware" for row in r341_objectives) == 27
        and len(r341_transfer) == 96
        and len(r341_transfer_misses) == 34
        and sum(as_bool(row["view_changed"]) for row in r341_transfer_misses) == 32
        and sum(as_bool(row["ranker_changed"]) for row in r341_transfer_misses) == 26
        and sum(as_bool(row["high_regret_miss"]) for row in r341_transfer_misses) == 29
        and r341_mechanism_counts["stack_depth_tradeoff"] == 6
        and r341_mechanism_counts["transfer_policy_signal"] == 6
        and r341_mechanism_counts["critical_rank_features"] == 4
        and r341_mechanism_counts["misleading_feature_risk"] == 2
        and sum(len(labels) >= 3 for labels in r341_mechanisms_by_task.values()) == 6
    ) else "fail"
    add_check(rows, run_id="R341", key="overall", actual=r341_overall, expected="pass", source="R341 CSV-derived invariants", paper_token="R341")
    add_check(rows, run_id="R341", key="tasks", actual=len(r341_tasks), expected=6, source="R341 objective-mechanism-attribution.csv", paper_token="6 tasks")
    add_check(rows, run_id="R341", key="objective_rows", actual=len(r341_objectives), expected=36, source="R341 objective-mechanism-attribution.csv", paper_token="36 objective rows")
    add_check(rows, run_id="R341", key="objective_best_policy_visible_rows", actual=sum(row["best_policy"] in visible_policies for row in r341_objectives), expected=36, source="R341 objective-mechanism-attribution.csv + R320 policy-scores.csv", paper_token="36/36 best policies visible")
    add_check(rows, run_id="R341", key="objective_best_policy_non_oracle_rows", actual=sum(policy_is_non_oracle(row["best_policy"]) for row in r341_objectives), expected=36, source="R341 objective-mechanism-attribution.csv", paper_token="36/36 best policies non-oracle")
    add_check(rows, run_id="R341", key="actionable_objective_rows", actual=sum(as_bool(row["actionable"]) for row in r341_objectives), expected=36, source="R341 objective-mechanism-attribution.csv", paper_token="36/36 objective rows have optimization actions")
    add_check(rows, run_id="R341", key="nondefault_best_objective_rows", actual=sum(row["best_policy"] != "operation_stack:query_aware" for row in r341_objectives), expected=27, source="R341 objective-mechanism-attribution.csv", paper_token="27/36 best visible policies are non-default")
    add_check(rows, run_id="R341", key="transfer_decisions", actual=len(r341_transfer), expected=96, source="R341 transfer-error-attribution.csv", paper_token="96 transfer decisions")
    add_check(rows, run_id="R341", key="transfer_misses", actual=len(r341_transfer_misses), expected=34, source="R341 transfer-error-attribution.csv", paper_token="34/96 transfer decisions")
    add_check(rows, run_id="R341", key="transfer_misses_with_view_change", actual=sum(as_bool(row["view_changed"]) for row in r341_transfer_misses), expected=32, source="R341 transfer-error-attribution.csv", paper_token="32/34 misses change view")
    add_check(rows, run_id="R341", key="transfer_misses_with_ranker_change", actual=sum(as_bool(row["ranker_changed"]) for row in r341_transfer_misses), expected=26, source="R341 transfer-error-attribution.csv", paper_token="26/34 change ranker")
    add_check(rows, run_id="R341", key="high_regret_transfer_misses", actual=sum(as_bool(row["high_regret_miss"]) for row in r341_transfer_misses), expected=29, source="R341 transfer-error-attribution.csv", paper_token="29/34 high-regret misses")
    add_check(rows, run_id="R341", key="stack_depth_tradeoff_tasks", actual=r341_mechanism_counts["stack_depth_tradeoff"], expected=6, source="R341 objective-mechanism-attribution.csv", paper_token="stack-depth signals on 6/6")
    add_check(rows, run_id="R341", key="transfer_policy_signal_tasks", actual=r341_mechanism_counts["transfer_policy_signal"], expected=6, source="R341 objective-mechanism-attribution.csv", paper_token="transfer-policy signals on 6/6")
    add_check(rows, run_id="R341", key="critical_rank_feature_tasks", actual=r341_mechanism_counts["critical_rank_features"], expected=4, source="R341 objective-mechanism-attribution.csv", paper_token="critical features on 4/6")
    add_check(rows, run_id="R341", key="misleading_feature_tasks", actual=r341_mechanism_counts["misleading_feature_risk"], expected=2, source="R341 objective-mechanism-attribution.csv", paper_token="misleading features on 2/6")
    add_check(rows, run_id="R341", key="tasks_with_three_or_more_mechanism_labels", actual=sum(len(labels) >= 3 for labels in r341_mechanisms_by_task.values()), expected=6, source="R341 objective-mechanism-attribution.csv", paper_token="three or more mechanism labels on 6/6")

    r342_best_ap_counts = Counter(row["best_ap_stack_kind"] for row in r342_source_tasks)
    r342_committed_variants_by_key = {r342_task_key(row): row for row in r342_variants}
    r342_committed_tasks_by_task = {row["task"]: row for row in r342_tasks}
    r342_variant_csv_matches = sum(
        r342_task_key(row) in r342_committed_variants_by_key
        and r342_committed_variant_matches(row, r342_committed_variants_by_key[r342_task_key(row)])
        for row in r342_source_variants
    )
    r342_task_csv_matches = sum(
        row["task"] in r342_committed_tasks_by_task
        and r342_committed_task_matches(row, r342_committed_tasks_by_task[row["task"]])
        for row in r342_source_tasks
    )
    r342_overall = "pass" if (
        len(r342_source_tasks) == 6
        and len(r342_source_variants) == 12
        and sum(as_bool(row["profile_spec_composes_pipeline"]) for row in r342_source_variants) == 12
        and sum(not as_bool(row["has_prompt_or_session_frame"]) for row in r342_source_variants) == 12
        and sum(row["ranking_policy"] == "visible_operation_rule_score_then_width" for row in r342_source_variants) == 12
        and sum(as_float(row["delta_ap"]) > 0 for row in r342_source_variants) == 9
        and sum(as_float(row["delta_top5_lift"]) > 0 for row in r342_source_variants) == 8
        and sum(as_float(row["delta_first_positive_work"]) < 0 for row in r342_source_variants) == 10
        and sum(as_bool(row["ap_improves_at_any_depth"]) for row in r342_source_tasks) == 5
        and sum(as_bool(row["first_positive_improves_at_any_depth"]) for row in r342_source_tasks) == 6
        and sum(as_float(row["coarse_group_reduction"]) > 0 for row in r342_source_tasks) == 6
        and round(float(median(as_float(row["coarse_group_reduction"]) for row in r342_source_tasks)), 4) == 0.8267
        and sum(as_bool(row["depth_choice_changes_objective"]) for row in r342_source_tasks) == 3
        and r342_best_ap_counts["semantic"] == 4
        and r342_best_ap_counts["coarse"] == 2
        and r342_variant_csv_matches == 12
        and r342_task_csv_matches == 6
    ) else "fail"
    add_check(rows, run_id="R342", key="overall", actual=r342_overall, expected="pass", source="R342 upstream-source-derived invariants", paper_token="R342")
    add_check(rows, run_id="R342", key="tasks", actual=len(r342_source_tasks), expected=6, source="R342 source_paths -> R324 report/summary/specs/Rust JSON", paper_token="6 tasks")
    add_check(rows, run_id="R342", key="profile_spec_variants", actual=len(r342_source_variants), expected=12, source="R342 source_paths -> R324 report/summary/specs/Rust JSON", paper_token="12 profile-spec variants")
    add_check(rows, run_id="R342", key="composition_variants", actual=sum(as_bool(row["profile_spec_composes_pipeline"]) for row in r342_source_variants), expected=12, source="R342 source_paths -> R324 profile specs", paper_token="12/12 compose")
    add_check(rows, run_id="R342", key="prompt_session_free_variants", actual=sum(not as_bool(row["has_prompt_or_session_frame"]) for row in r342_source_variants), expected=12, source="R342 source_paths -> R324 Rust JSON", paper_token="12/12 prompt/session-free")
    add_check(rows, run_id="R342", key="rule_score_rank_policy_variants", actual=sum(row["ranking_policy"] == "visible_operation_rule_score_then_width" for row in r342_source_variants), expected=12, source="R342 source_paths -> R324 Rust JSON", paper_token="rank_mode=rule-score")
    add_check(rows, run_id="R342", key="ap_improves_vs_width_variants", actual=sum(as_float(row["delta_ap"]) > 0 for row in r342_source_variants), expected=9, source="R342 source_paths -> R324 summary", paper_token="9/12 variants")
    add_check(rows, run_id="R342", key="top5_lift_improves_vs_width_variants", actual=sum(as_float(row["delta_top5_lift"]) > 0 for row in r342_source_variants), expected=8, source="R342 source_paths -> R324 summary", paper_token="8/12")
    add_check(rows, run_id="R342", key="first_positive_work_improves_vs_width_variants", actual=sum(as_float(row["delta_first_positive_work"]) < 0 for row in r342_source_variants), expected=10, source="R342 source_paths -> R324 summary", paper_token="10/12")
    add_check(rows, run_id="R342", key="tasks_with_ap_improvement_any_depth", actual=sum(as_bool(row["ap_improves_at_any_depth"]) for row in r342_source_tasks), expected=5, source="R342 source_paths -> R324 summary", paper_token="5/6")
    add_check(rows, run_id="R342", key="tasks_with_first_positive_improvement_any_depth", actual=sum(as_bool(row["first_positive_improves_at_any_depth"]) for row in r342_source_tasks), expected=6, source="R342 source_paths -> R324 summary", paper_token="6/6")
    add_check(rows, run_id="R342", key="tasks_where_coarse_reduces_groups", actual=sum(as_float(row["coarse_group_reduction"]) > 0 for row in r342_source_tasks), expected=6, source="R342 source_paths -> R324 summary", paper_token="6/6 tasks")
    add_check(rows, run_id="R342", key="median_coarse_group_reduction", actual=round(float(median(as_float(row["coarse_group_reduction"]) for row in r342_source_tasks)), 4), expected=0.8267, source="R342 source_paths -> R324 summary", paper_token="0.8267", tolerance=5e-5)
    add_check(rows, run_id="R342", key="tasks_where_depth_choice_changes_objective", actual=sum(as_bool(row["depth_choice_changes_objective"]) for row in r342_source_tasks), expected=3, source="R342 source_paths -> R324 summary", paper_token="3/6 tasks")
    add_check(rows, run_id="R342", key="best_ap_semantic_depth_tasks", actual=r342_best_ap_counts["semantic"], expected=4, source="R342 source_paths -> R324 summary", paper_token="semantic 4 / coarse 2")
    add_check(rows, run_id="R342", key="best_ap_coarse_depth_tasks", actual=r342_best_ap_counts["coarse"], expected=2, source="R342 source_paths -> R324 summary", paper_token="semantic 4 / coarse 2")
    add_check(rows, run_id="R342", key="committed_variant_csv_matches_sources", actual=r342_variant_csv_matches, expected=12, source="R342 CSV compared with upstream-derived rows", paper_token="12/12")
    add_check(rows, run_id="R342", key="committed_task_csv_matches_sources", actual=r342_task_csv_matches, expected=6, source="R342 CSV compared with upstream-derived rows", paper_token="6/6")

    r344 = reports["R344"]["summary"]
    r344_metric_keys = {row["metric"] for row in r344_metric_summary}
    r344_support = sum(row["verdict"] == "supports" for row in r344_metric_summary)
    r344_counterpoints = sum(row["verdict"] == "counterpoint" for row in r344_metric_summary)
    r344_mixed_or_weak = len(r344_metric_summary) - r344_support - r344_counterpoints

    def r344_row(baseline: str, metric: str) -> dict[str, str]:
        return csv_lookup(r344_metric_summary, baseline=baseline, metric=metric)

    add_check(rows, run_id="R344", key="overall", actual=r344["overall"], expected="pass", source="R344 report summary", paper_token="R344")
    add_check(rows, run_id="R344", key="tasks", actual=r344["tasks"], expected=6, source="R344 report summary", paper_token="6 tasks")
    add_check(rows, run_id="R344", key="metric_comparisons", actual=r344["metric_comparisons"], expected=50, source="R344 report summary", paper_token="50 baseline-metric comparisons")
    add_check(rows, run_id="R344", key="task_metric_delta_rows", actual=r344["task_metric_delta_rows"], expected=300, source="R344 report summary", paper_token="300 task-metric deltas")
    add_check(rows, run_id="R344", key="support_verdicts", actual=r344["support_verdicts"], expected=30, source="R344 report summary", paper_token="30 support verdicts")
    add_check(rows, run_id="R344", key="counterpoint_verdicts", actual=r344["counterpoint_verdicts"], expected=16, source="R344 report summary", paper_token="16 counterpoints")
    add_check(rows, run_id="R344", key="mixed_or_weak_verdicts", actual=r344["mixed_or_weak_verdicts"], expected=4, source="R344 report summary", paper_token="4 mixed/weak")
    add_check(rows, run_id="R344", key="required_metric_count", actual=len(r344["required_metrics_covered"]), expected=9, source="R344 report summary", paper_token="groups")
    add_check(rows, run_id="R344", key="required_groups_metric_present", actual="groups" in r344["required_metrics_covered"], expected=True, source="R344 report summary", paper_token="groups")
    add_check(rows, run_id="R344", key="metric_summary_rows", actual=len(r344_metric_summary), expected=50, source="R344 metric-summary.csv", paper_token="50")
    add_check(rows, run_id="R344", key="task_delta_rows", actual=len(r344_task_deltas), expected=300, source="R344 task-metric-deltas.csv", paper_token="300")
    add_check(rows, run_id="R344", key="summary_support_verdicts", actual=r344_support, expected=30, source="R344 metric-summary.csv", paper_token="30 support verdicts")
    add_check(rows, run_id="R344", key="summary_counterpoint_verdicts", actual=r344_counterpoints, expected=16, source="R344 metric-summary.csv", paper_token="16 counterpoints")
    add_check(rows, run_id="R344", key="summary_mixed_or_weak_verdicts", actual=r344_mixed_or_weak, expected=4, source="R344 metric-summary.csv", paper_token="4 mixed/weak")
    add_check(rows, run_id="R344", key="required_metric_groups_in_summary", actual="groups" in r344_metric_keys, expected=True, source="R344 metric-summary.csv", paper_token="groups")
    add_check(rows, run_id="R344", key="flat_ap_wins", actual=as_int(r344_row("flat_width", "average_precision")["wins"]), expected=6, source="R344 metric-summary.csv", paper_token="flat AP 6/6")
    add_check(rows, run_id="R344", key="flat_budget30_recall_wins", actual=as_int(r344_row("flat_width", "budget30_recall")["wins"]), expected=6, source="R344 metric-summary.csv", paper_token="budget30 recall 6/6")
    add_check(rows, run_id="R344", key="flat_work_to_first_positive_wins", actual=as_int(r344_row("flat_width", "work_to_first_positive")["wins"]), expected=6, source="R344 metric-summary.csv", paper_token="work-to-first-positive 6/6")
    add_check(rows, run_id="R344", key="fixed_session_top5_f1_wins", actual=as_int(r344_row("fixed_session_query_aware", "top5_f1")["wins"]), expected=5, source="R344 metric-summary.csv", paper_token="top-5 F1 5/6")
    add_check(rows, run_id="R344", key="fixed_session_group_wins", actual=as_int(r344_row("fixed_session_query_aware", "groups")["wins"]), expected=4, source="R344 metric-summary.csv", paper_token="groups 4/6")
    add_check(rows, run_id="R344", key="width_ap_wins", actual=as_int(r344_row("operation_stack_width", "average_precision")["wins"]), expected=6, source="R344 metric-summary.csv", paper_token="width AP 6/6")
    add_check(rows, run_id="R344", key="width_budget30_recall_wins", actual=as_int(r344_row("operation_stack_width", "budget30_recall")["wins"]), expected=5, source="R344 metric-summary.csv", paper_token="budget30 recall 5/6")
    add_check(rows, run_id="R344", key="flat_ndcg_losses", actual=as_int(r344_row("flat_width", "ndcg")["losses"]), expected=6, source="R344 metric-summary.csv", paper_token="nDCG")
    add_check(rows, run_id="R344", key="flat_top5_recall_losses", actual=as_int(r344_row("flat_width", "top5_recall")["losses"]), expected=6, source="R344 metric-summary.csv", paper_token="top-k recall")

    r345 = reports["R345"]["summary"]
    add_check(rows, run_id="R345", key="overall", actual=r345["overall"], expected="pass", source="R345 report summary", paper_token="R345")
    add_check(rows, run_id="R345", key="tasks", actual=r345["tasks"], expected=6, source="R345 report summary", paper_token="6 tasks")
    add_check(rows, run_id="R345", key="datasets", actual=r345["datasets"], expected=4, source="R345 report summary", paper_token="4 datasets")
    add_check(rows, run_id="R345", key="lens_count", actual=r345["lens_count"], expected=6, source="R345 report summary", paper_token="6 diagnostic lenses")
    add_check(rows, run_id="R345", key="objective_rows", actual=r345["objective_rows"], expected=36, source="R345 report summary", paper_token="36 objective rows")
    add_check(rows, run_id="R345", key="task_cards", actual=r345["task_cards"], expected=6, source="R345 report summary", paper_token="6/6 actionable task cards")
    add_check(rows, run_id="R345", key="actionable_task_cards", actual=r345["actionable_task_cards"], expected=6, source="R345 report summary", paper_token="6/6 actionable task cards")
    add_check(rows, run_id="R345", key="distinct_optimization_actions", actual=r345["distinct_optimization_actions"], expected=5, source="R345 report summary", paper_token="5 distinct optimization actions")
    add_check(rows, run_id="R345", key="default_operation_stack_best_objectives", actual=r345["default_operation_stack_best_objectives"], expected=9, source="R345 report summary", paper_token="9/36 default operation-stack")
    add_check(rows, run_id="R345", key="operation_stack_family_best_objectives", actual=r345["operation_stack_family_best_objectives"], expected=11, source="R345 report summary", paper_token="11/36 operation-stack family")
    add_check(rows, run_id="R345", key="non_operation_stack_best_objectives", actual=r345["non_operation_stack_best_objectives"], expected=25, source="R345 report summary", paper_token="25/36 counterpoints")
    add_check(rows, run_id="R345", key="tasks_with_three_or_more_best_views", actual=r345["tasks_with_three_or_more_best_views"], expected=6, source="R345 report summary", paper_token="6/6 tasks need at least three best views")
    add_check(rows, run_id="R345", key="min_distinct_best_views_per_task", actual=r345["min_distinct_best_views_per_task"], expected=3, source="R345 report summary", paper_token="3 best views")
    add_check(rows, run_id="R345", key="max_distinct_best_views_per_task", actual=r345["max_distinct_best_views_per_task"], expected=4, source="R345 report summary", paper_token="4 best views")
    add_check(rows, run_id="R345", key="counterpoint_rows", actual=r345["counterpoint_rows"], expected=46, source="R345 report summary", paper_token="46 counterpoint rows")
    add_check(rows, run_id="R345", key="r344_support_verdicts", actual=r345["r344_support_verdicts"], expected=30, source="R345 report summary", paper_token="30 support")
    add_check(rows, run_id="R345", key="r344_counterpoint_verdicts", actual=r345["r344_counterpoint_verdicts"], expected=16, source="R345 report summary", paper_token="16 counterpoints")
    add_check(rows, run_id="R345", key="r344_mixed_or_weak_verdicts", actual=r345["r344_mixed_or_weak_verdicts"], expected=4, source="R345 report summary", paper_token="4 mixed/weak")
    add_check(rows, run_id="R345", key="lens_summary_rows", actual=len(r345_lens_summary), expected=6, source="R345 diagnostic-lens-summary.csv", paper_token="6 diagnostic lenses")
    add_check(rows, run_id="R345", key="task_lens_card_rows", actual=len(r345_task_cards), expected=6, source="R345 task-lens-cards.csv", paper_token="6 tasks")
    add_check(rows, run_id="R345", key="counterpoint_ledger_rows", actual=len(r345_counterpoints), expected=46, source="R345 counterpoint-ledger.csv", paper_token="46 counterpoint rows")

    r346 = reports["R346"]["summary"]
    add_check(rows, run_id="R346", key="overall", actual=r346["overall"], expected="pass", source="R346 report summary", paper_token="R346")
    add_check(rows, run_id="R346", key="tasks", actual=r346["tasks"], expected=6, source="R346 report summary", paper_token="6 tasks")
    add_check(rows, run_id="R346", key="datasets", actual=r346["datasets"], expected=4, source="R346 report summary", paper_token="4 datasets")
    add_check(rows, run_id="R346", key="case_groups", actual=r346["case_groups"], expected=30, source="R346 report summary", paper_token="30 case groups")
    add_check(rows, run_id="R346", key="top_groups_per_task", actual=r346["top_groups_per_task"], expected=5, source="R346 report summary", paper_token="top-5")
    add_check(rows, run_id="R346", key="tasks_with_top1_positive", actual=r346["tasks_with_top1_positive"], expected=5, source="R346 report summary", paper_token="5/6 top-1")
    add_check(rows, run_id="R346", key="tasks_with_positive_in_top5", actual=r346["tasks_with_positive_in_top5"], expected=6, source="R346 report summary", paper_token="6/6 top-5")
    add_check(rows, run_id="R346", key="median_top5_recall", actual=r346["median_top5_recall"], expected=0.188, source="R346 report summary", paper_token="0.188", tolerance=5e-5)
    add_check(rows, run_id="R346", key="median_top5_precision", actual=r346["median_top5_precision"], expected=0.1991, source="R346 report summary", paper_token="0.1991", tolerance=5e-5)
    add_check(rows, run_id="R346", key="median_top5_lift", actual=r346["median_top5_lift"], expected=1.6508, source="R346 report summary", paper_token="1.6508", tolerance=5e-5)
    add_check(rows, run_id="R346", key="median_top5_work", actual=r346["median_top5_work"], expected=0.0937, source="R346 report summary", paper_token="0.0937", tolerance=5e-5)
    add_check(rows, run_id="R346", key="median_first_positive_work", actual=r346["median_first_positive_work"], expected=0.0378, source="R346 report summary", paper_token="0.0378", tolerance=5e-5)
    add_check(rows, run_id="R346", key="tasks_with_actionable_case_cards", actual=r346["tasks_with_actionable_case_cards"], expected=6, source="R346 report summary", paper_token="6/6 actionable case cards")
    add_check(rows, run_id="R346", key="tasks_with_counterpoints", actual=r346["tasks_with_counterpoints"], expected=6, source="R346 report summary", paper_token="6/6 counterpoints")
    add_check(rows, run_id="R346", key="tasks_with_three_or_more_best_views", actual=r346["tasks_with_three_or_more_best_views"], expected=6, source="R346 report summary", paper_token="6/6 tasks need at least three best views")
    add_check(rows, run_id="R346", key="min_distinct_best_views_per_task", actual=r346["min_distinct_best_views_per_task"], expected=3, source="R346 report summary", paper_token="3 best views")
    add_check(rows, run_id="R346", key="max_distinct_best_views_per_task", actual=r346["max_distinct_best_views_per_task"], expected=4, source="R346 report summary", paper_token="4 best views")
    add_check(rows, run_id="R346", key="task_case_card_rows", actual=len(r346_task_cards), expected=6, source="R346 task-diagnostic-case-cards.csv", paper_token="6 tasks")
    add_check(rows, run_id="R346", key="top_stack_evidence_rows", actual=len(r346_top_stack_evidence), expected=30, source="R346 top-stack-evidence.csv", paper_token="30 case groups")

    def r347_pair_row(baseline: str, metric: str) -> dict[str, str]:
        return csv_lookup(r347_pair_summary, baseline=baseline, metric=metric)

    r347 = reports["R347"]["summary"]
    add_check(rows, run_id="R347", key="overall", actual=r347["overall"], expected="pass", source="R347 report summary", paper_token="R347")
    add_check(rows, run_id="R347", key="tasks", actual=r347["tasks"], expected=6, source="R347 report summary", paper_token="6 tasks")
    add_check(rows, run_id="R347", key="datasets", actual=r347["datasets"], expected=4, source="R347 report summary", paper_token="4 datasets")
    add_check(rows, run_id="R347", key="visible_views", actual=r347["visible_views"], expected=5, source="R347 report summary", paper_token="5 visible views")
    add_check(rows, run_id="R347", key="view_task_rows", actual=r347["view_task_rows"], expected=30, source="R347 report summary", paper_token="30 view-task rows")
    add_check(rows, run_id="R347", key="top_groups_per_view", actual=r347["top_groups_per_view"], expected=5, source="R347 report summary", paper_token="top-5 groups")
    add_check(rows, run_id="R347", key="operation_stack_top5_positive_tasks", actual=r347["operation_stack_top5_positive_tasks"], expected=6, source="R347 report summary", paper_token="6/6 top-5 positive tasks")
    add_check(rows, run_id="R347", key="operation_stack_top1_positive_tasks", actual=r347["operation_stack_top1_positive_tasks"], expected=5, source="R347 report summary", paper_token="5/6 top-1 positive tasks")
    add_check(rows, run_id="R347", key="operation_stack_median_top5_recall", actual=r347["operation_stack_median_top5_recall"], expected=0.188, source="R347 report summary", paper_token="0.188", tolerance=5e-5)
    add_check(rows, run_id="R347", key="operation_stack_median_top5_lift", actual=r347["operation_stack_median_top5_lift"], expected=1.6508, source="R347 report summary", paper_token="1.6508", tolerance=5e-5)
    add_check(rows, run_id="R347", key="operation_stack_median_top5_work", actual=r347["operation_stack_median_top5_work"], expected=0.0937, source="R347 report summary", paper_token="0.0937", tolerance=5e-5)
    add_check(rows, run_id="R347", key="operation_stack_median_first_positive_work", actual=r347["operation_stack_median_first_positive_work"], expected=0.0378, source="R347 report summary", paper_token="0.0378", tolerance=5e-5)
    add_check(rows, run_id="R347", key="wins_vs_flat_top5_work", actual=r347["wins_vs_flat_top5_work"], expected=6, source="R347 report summary", paper_token="6/6 wins vs flat top-5 work")
    add_check(rows, run_id="R347", key="wins_vs_fixed_top5_recall", actual=r347["wins_vs_fixed_top5_recall"], expected=5, source="R347 report summary", paper_token="5/6 wins vs fixed-session top-5 recall")
    add_check(rows, run_id="R347", key="wins_vs_fixed_group_count", actual=r347["wins_vs_fixed_group_count"], expected=4, source="R347 report summary", paper_token="4/6 wins vs fixed-session group count")
    add_check(rows, run_id="R347", key="tasks_with_counterpoints", actual=r347["tasks_with_counterpoints"], expected=6, source="R347 report summary", paper_token="6/6 tasks with counterpoints")
    add_check(rows, run_id="R347", key="view_case_metric_rows", actual=len(r347_view_metrics), expected=30, source="R347 view-case-metrics.csv", paper_token="30 view-task rows")
    add_check(rows, run_id="R347", key="task_baseline_card_rows", actual=len(r347_task_cards), expected=6, source="R347 task-baseline-contrast-cards.csv", paper_token="6 task cards")
    add_check(rows, run_id="R347", key="baseline_pair_summary_rows", actual=len(r347_pair_summary), expected=24, source="R347 baseline-pair-summary.csv", paper_token="24 baseline-pair rows")
    add_check(rows, run_id="R347", key="top_group_contrast_rows", actual=len(r347_top_group_contrast), expected=124, source="R347 top-group-contrast.csv", paper_token="124 top-group rows")
    add_check(rows, run_id="R347", key="flat_top5_work_wins", actual=as_int(r347_pair_row("flat:width", "top5_work")["operation_stack_wins"]), expected=6, source="R347 baseline-pair-summary.csv", paper_token="6/6 wins vs flat top-5 work")
    add_check(rows, run_id="R347", key="fixed_session_top5_recall_wins", actual=as_int(r347_pair_row("fixed_session:query_aware", "top5_recall")["operation_stack_wins"]), expected=5, source="R347 baseline-pair-summary.csv", paper_token="5/6 wins vs fixed-session top-5 recall")
    add_check(rows, run_id="R347", key="fixed_session_group_wins", actual=as_int(r347_pair_row("fixed_session:query_aware", "groups")["operation_stack_wins"]), expected=4, source="R347 baseline-pair-summary.csv", paper_token="4/6 wins vs fixed-session group count")
    add_check(rows, run_id="R347", key="fixed_session_first_positive_losses", actual=as_int(r347_pair_row("fixed_session:query_aware", "work_to_first_positive")["operation_stack_losses"]), expected=4, source="R347 baseline-pair-summary.csv", paper_token="fixed-session first-positive counterpoint 4/6")
    add_check(rows, run_id="R347", key="flat_top5_recall_losses", actual=as_int(r347_pair_row("flat:width", "top5_recall")["operation_stack_losses"]), expected=6, source="R347 baseline-pair-summary.csv", paper_token="flat full-work recall counterpoint 6/6")
    return rows


def contains_any(text: str, tokens: list[str]) -> bool:
    return any(token in text for token in tokens)


def contains_all(text: str, tokens: list[str]) -> bool:
    return all(token in text for token in tokens)


def line_hits(text: str, tokens: list[str], limit: int = 8) -> list[int]:
    hits: list[int] = []
    for index, line in enumerate(text.splitlines(), start=1):
        if any(token in line for token in tokens):
            hits.append(index)
            if len(hits) >= limit:
                break
    return hits


def line_hits_all(text: str, tokens: list[str], limit: int = 8) -> list[int]:
    hits: list[int] = []
    for index, line in enumerate(text.splitlines(), start=1):
        if all(token in line for token in tokens):
            hits.append(index)
            if len(hits) >= limit:
                break
    return hits


def build_text_coverage(
    texts: dict[str, str], number_checks: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    required: list[tuple[str, str, list[str], str]] = [
        ("evaluation", "R320 headline operations", ["34,539", "34539"], "R320"),
        ("evaluation", "R320 top5 work", ["0.0937", "9.37%"], "R320"),
        ("evaluation", "R333 budget30 recall", ["0.3900", "0.39"], "R333"),
        ("evaluation", "R334 fragmentation", ["5/6", "-54.0", "fewer groups"], "R334"),
        ("evaluation", "R335 actionability", ["actionability", "6/6", "optimization"], "R335"),
        ("evaluation", "R336 visible policies", ["15 visible", "15 个", "6 diagnostic"], "R336"),
        ("evaluation", "R337 fixed recall", ["25%", "0.2000", "16.0"], "R337"),
        ("evaluation", "R339 sequence adequacy", ["R339", "0.4669", "0.9103"], "R339"),
        ("evaluation", "R340 policy transfer", ["R340", "96", "62/96", "72/96"], "R340"),
        ("evaluation", "R341 mechanism attribution", ["R341", "36/36", "27/36", "34/96"], "R341"),
        ("evaluation", "R342 profile spec composition", ["R342", "12/12", "9/12", "0.8267"], "R342"),
        ("evaluation", "R344 metric consistency", ["R344", "30", "16", "groups"], "R344"),
        ("evaluation", "R345 diagnostic lens portfolio", ["R345", "6 diagnostic lenses", "11/36", "25/36"], "R345"),
        ("evaluation", "R346 diagnostic casebook", ["R346", "30 case groups", "5/6", "1.6508"], "R346"),
        ("evaluation", "R347 case baseline contrast", ["R347", "5 visible views", "6/6", "5/6", "4/6"], "R347"),
        ("zh_main", "R320 headline", ["0.0937", "9.37", "285.0", "157.5"], "R320"),
        ("zh_main", "R333 headline", ["0.3900", "0.390"], "R333"),
        ("zh_main", "R337 headline", ["0.2000", "16.0", "50.0"], "R337"),
        ("zh_main", "R339 headline", ["0.4669", "0.9103", "0.3467"], "R339"),
        ("zh_main", "R340 headline", ["R340", "62/96", "72/96", "69/96"], "R340"),
        ("zh_main", "R341 headline", ["R341", "36/36", "27/36", "34/96"], "R341"),
        ("zh_main", "R342 headline", ["R342", "12/12", "9/12", "0.8267"], "R342"),
        ("zh_main", "R344 headline", ["R344", "30", "16", "nDCG"], "R344"),
        ("zh_main", "R345 headline", ["R345", "6", "11/36", "25/36"], "R345"),
        ("zh_main", "R346 headline", ["R346", "30", "5/6", "1.6508"], "R346"),
        ("zh_main", "R347 headline", ["R347", "5", "6/6", "5/6", "4/6"], "R347"),
        ("en_main", "R320 headline", ["0.0937", "9.37", "285.0", "157.5"], "R320"),
        ("en_main", "R333 headline", ["0.3900", "0.390"], "R333"),
        ("en_main", "R337 headline", ["0.2000", "16.0", "50.0"], "R337"),
        ("en_main", "R339 headline", ["0.4669", "0.9103", "0.3467"], "R339"),
        ("en_main", "R340 headline", ["R340", "62 of 96", "72 of 96", "69 of 96"], "R340"),
        ("en_main", "R341 headline", ["R341", "36 of 36", "27 of 36", "34 of 96"], "R341"),
        ("en_main", "R342 headline", ["R342", "12/12", "9/12", "0.8267"], "R342"),
        ("en_main", "R344 headline", ["R344", "30", "16", "nDCG"], "R344"),
        ("en_main", "R345 headline", ["R345", "6", "11/36", "25/36"], "R345"),
        ("en_main", "R346 headline", ["R346", "30", "5/6", "1.6508"], "R346"),
        ("en_main", "R347 headline", ["R347", "5", "6/6", "5/6", "4/6"], "R347"),
        ("zh_claim_setup", "two abstractions", ["两个核心抽象", "operation stack"], "C2"),
        ("zh_claim_setup", "R337 result", ["R337", "0.2000", "16.0"], "R337"),
        ("zh_claim_setup", "R339 result", ["R339", "0.4669", "0.9103"], "R339"),
        ("zh_claim_setup", "R340 result", ["R340", "62/96", "72/96", "69/96"], "R340"),
        ("zh_claim_setup", "R341 result", ["R341", "36/36", "27/36", "34/96"], "R341"),
        ("zh_claim_setup", "R342 result", ["R342", "12/12", "9/12", "0.8267"], "R342"),
        ("zh_claim_setup", "R344 result", ["R344", "30", "16", "nDCG"], "R344"),
        ("zh_claim_setup", "R345 result", ["R345", "6", "11/36", "25/36"], "R345"),
        ("zh_claim_setup", "R346 result", ["R346", "30", "5/6", "1.6508"], "R346"),
        ("zh_claim_setup", "R347 result", ["R347", "5", "6/6", "5/6", "4/6"], "R347"),
    ]
    rows: list[dict[str, Any]] = []
    for doc, key, tokens, source in required:
        text = texts[doc]
        status = "pass" if (contains_all(text, tokens) if source in {"R341", "R342", "R344", "R345", "R346", "R347"} else contains_any(text, tokens)) else "fail"
        rows.append(
            {
                "doc": doc,
                "key": key,
                "source": source,
                "tokens": " / ".join(tokens),
                "status": status,
                "lines": ",".join(map(str, line_hits(text, tokens))) or "missing",
            }
        )

    eval_text = texts["evaluation"]
    for row in number_checks:
        if row["run_id"] not in {"R320", "R333", "R337", "R339", "R340", "R341", "R342", "R344", "R345", "R346", "R347"}:
            continue
        token = str(row["paper_token"])
        hits = line_hits_all(eval_text, [row["run_id"], token]) if row["run_id"] in {"R341", "R342", "R344", "R345", "R346", "R347"} else line_hits(eval_text, [token])
        status = "pass" if hits else "warn"
        rows.append(
            {
                "doc": "evaluation",
                "key": f"{row['run_id']}:{row['key']}",
                "source": row["source"],
                "tokens": token,
                "status": status,
                "lines": ",".join(map(str, hits)) or "missing",
            }
        )
    return rows


def guarded_occurrences(text: str, pattern: str) -> dict[str, Any]:
    regex = re.compile(pattern, re.IGNORECASE)
    occurrences = []
    unguarded = []
    for index, line in enumerate(text.splitlines(), start=1):
        if regex.search(line):
            item = {"line": index, "text": line.strip()}
            occurrences.append(item)
            lower = line.lower()
            if not any(marker in lower for marker in NEGATION_MARKERS):
                unguarded.append(item)
    return {"occurrences": occurrences, "unguarded": unguarded}


def build_guardrail_checks(texts: dict[str, str]) -> list[dict[str, Any]]:
    required_guardrails = [
        (
            "human_utility",
            [r"human.*productivity", r"human utility", r"人类.*效率", r"human/agent analyst study"],
            [
                r"not .*human.*productivity",
                r"not .*human utility",
                r"does not .*human",
                r"不能.*human",
                r"不能.*productivity",
                r"不能.*效率",
                r"不支持.*human utility",
                r"productivity claims.*not required",
                r"不是 human utility",
            ],
            [
                r"improv(e|es|ed).*human.*(productivity|accuracy)",
                r"human.*(faster|more accurate)",
                r"analyst.*(faster|more accurate|productivity)",
                r"time-to-answer.*(improv|reduc)",
                r"提升.*(开发者|人类|analyst).*(效率|准确率)",
                r"(减少|降低).*(耗时|time-to-answer)",
            ],
        ),
        (
            "automatic_boundary",
            [r"complete.*boundar", r"完整恢复.*边界", r"automatic.*boundar", r"自动.*边界"],
            [
                r"not .*automatic.*boundar",
                r"does not .*automatic.*boundar",
                r"cannot .*boundar",
                r"不能.*boundary",
                r"不能.*边界",
                r"不支持.*intent",
                r"not .*all intent boundaries",
                r"不证明.*intent detector",
            ],
            [
                r"automatic.*discover.*(all|intent|semantic).*boundar",
                r"discover.*all.*intent.*boundar",
                r"complete.*intent.*boundar",
                r"完整.*(恢复|发现).*边界",
                r"自动.*(发现|恢复).*所有.*边界",
                r"通用.*intent detector",
            ],
        ),
        (
            "ecosystem_compatibility",
            [r"OpenTelemetry", r"Phoenix", r"LangSmith", r"Langfuse", r"Perfetto"],
            [
                r"not .*compatib",
                r"does not .*compatib",
                r"complete compatibility",
                r"完整.*兼容",
                r"不证明.*兼容",
                r"不是.*compatibility",
                r"future .*baseline",
                r"future .*interoperability",
                r"后续.*baseline",
                r"后续.*互操作",
                r"exchange container",
            ],
            [
                r"complete.*compatib.*(OpenTelemetry|Phoenix|LangSmith|Langfuse|Perfetto)",
                r"fully.*compatib.*(OpenTelemetry|Phoenix|LangSmith|Langfuse|Perfetto)",
                r"full.*trace.*ecosystem.*compatib",
                r"完整.*(OpenTelemetry|Phoenix|LangSmith|Langfuse|Perfetto).*兼容",
                r"完整.*trace.*ecosystem.*兼容",
            ],
        ),
        (
            "universal_selector",
            [r"universal selector", r"single.*view", r"单一.*最优", r"automatic.*selector"],
            [
                r"not .*universal selector",
                r"not .*single-view",
                r"not .*automatic .*selector",
                r"不能.*single-view",
                r"不支持.*single-view",
                r"不支持.*automatic universal selector",
                r"不是.*selector",
                r"best visible view.*var",
                r"每个 task 都有多个",
                r"vary by task and objective",
            ],
            [
                r"automatic.*universal selector",
                r"universal selector",
                r"single.*best.*(view|hierarchy|policy)",
                r"single-view dominance",
                r"always.*best",
                r"唯一最优",
                r"单一.*支配",
                r"无条件支配",
            ],
        ),
    ]

    def context_exempt(line: str) -> bool:
        stripped = line.strip()
        lower = stripped.lower()
        return (
            stripped.startswith(r"\bibitem")
            or stripped.startswith(r"\noindent [")
            or r"\url{" in stripped
            or lower.startswith("| related-work")
            or lower.startswith("| paper claim-integrity audit")
            or "source/command:" in lower
        )

    def locally_guarded(lines: list[str], index: int, guard_regex: re.Pattern[str]) -> bool:
        start = max(0, index - 2)
        end = min(len(lines), index + 3)
        window = "\n".join(lines[start:end])
        lower_window = window.lower()
        return bool(guard_regex.search(window)) or any(
            marker in lower_window for marker in NEGATION_MARKERS
        )

    rows: list[dict[str, Any]] = []
    for doc, text in texts.items():
        lines = text.splitlines()
        for key, occurrence_patterns, guard_patterns, overclaim_patterns in required_guardrails:
            guard_regex = re.compile("|".join(guard_patterns), re.IGNORECASE | re.DOTALL)
            guarded = bool(guard_regex.search(text))
            occurrence_regex = re.compile("|".join(occurrence_patterns), re.IGNORECASE)
            overclaim_regex = re.compile("|".join(overclaim_patterns), re.IGNORECASE)
            occurrences: list[str] = []
            unguarded: list[str] = []
            for line_index, line in enumerate(lines):
                if occurrence_regex.search(line):
                    occurrences.append(str(line_index + 1))
                if overclaim_regex.search(line) and not context_exempt(line):
                    if not locally_guarded(lines, line_index, guard_regex):
                        unguarded.append(str(line_index + 1))
            if unguarded:
                status = "fail"
            elif guarded:
                status = "pass"
            else:
                status = "warn_missing_guardrail"
            rows.append(
                {
                    "doc": doc,
                    "guardrail": key,
                    "status": status,
                    "occurrences": len(occurrences[:12]),
                    "occurrence_lines": ",".join(occurrences[:12]) or "none",
                    "unguarded_lines": ",".join(unguarded[:12]) or "none",
                }
            )
    return rows


def build_abstraction_text_checks(texts: dict[str, str]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for doc, text in texts.items():
        has_operation = "operation" in text
        has_stack = "operation stack" in text or "operation-stack" in text
        has_two = bool(
            re.search(r"two[- ]abstraction|two[- ]object|两个核心抽象|only operations and operation stacks", text, re.I)
        )
        third = guarded_occurrences(text, r"third abstraction|第三个抽象")
        rows.extend(
            [
                {
                    "doc": doc,
                    "check": "operation_named",
                    "status": "pass" if has_operation else "fail",
                    "detail": "operation",
                },
                {
                    "doc": doc,
                    "check": "operation_stack_named",
                    "status": "pass" if has_stack else "fail",
                    "detail": "operation stack",
                },
                {
                    "doc": doc,
                    "check": "two_abstraction_boundary",
                    "status": "pass" if has_two else "warn_missing_guardrail",
                    "detail": "two abstractions wording",
                },
                {
                    "doc": doc,
                    "check": "third_abstraction_guarded",
                    "status": "pass" if not third["unguarded"] else "fail",
                    "detail": ",".join(str(item["line"]) for item in third["occurrences"]) or "none",
                },
            ]
        )
    return rows


def row_status(rows: list[dict[str, Any]], fail_on_warn: bool = False) -> str:
    statuses = [row["status"] for row in rows]
    if any(status == "fail" for status in statuses):
        return "fail"
    if fail_on_warn and any(status.startswith("warn") or status == "warn" for status in statuses):
        return "fail"
    if any(status.startswith("warn") or status == "warn" for status in statuses):
        return "warn"
    return "pass"


def build_markdown(path: Path, payload: dict[str, Any]) -> None:
    summary = payload["summary"]
    lines = [
        "# Paper Claim Integrity Audit R338",
        "",
        "R338 mechanically audits the current profiling-paper claim against R320-R347 result artifacts and the Chinese/English paper text. It does not fetch, sync, create, or relabel datasets.",
        "",
        "## Verdict",
        "",
        f"- Overall: {summary['overall']}.",
        f"- Result invariants: {summary['result_invariants']}.",
        f"- Source policy: {summary['source_policy']}.",
        f"- Paper text coverage: {summary['paper_text_coverage']}.",
        f"- Guardrails: {summary['guardrails']}.",
        f"- Two-abstraction boundary: {summary['two_abstraction_boundary']}.",
        f"- Source artifacts tracked clean: {summary['source_artifacts_tracked_clean']}.",
        f"- Paper sources hashed: {summary['paper_sources_hashed']}.",
        "",
        "## Claim Position",
        "",
        payload["claim_position"],
        "",
        "## Headline Checks",
        "",
        "| Run | Key | Expected | Actual | Status | Source |",
        "|---|---|---:|---:|---|---|",
    ]
    for row in payload["number_checks"]:
        if row["run_id"] in {"R320", "R333", "R334", "R337", "R339", "R340", "R341", "R342", "R344", "R345", "R346", "R347"}:
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
        lines.append(
            f"| {row['doc']} | {row['key']} | {row['tokens']} | {row['status']} | {row['lines']} |"
        )
    lines.extend(
        [
            "",
            "## Guardrails",
            "",
            "| Doc | Guardrail | Status | Occurrences | Occurrence lines | Unguarded overclaim lines |",
            "|---|---|---|---:|---|---|",
        ]
    )
    for row in payload["guardrail_checks"]:
        lines.append(
            f"| {row['doc']} | {row['guardrail']} | {row['status']} | {row['occurrences']} | {row['occurrence_lines']} | {row['unguarded_lines']} |"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_html(path: Path, payload: dict[str, Any]) -> None:
    summary = payload["summary"]
    def table(rows: list[dict[str, Any]], fields: list[str]) -> str:
        head = "".join(f"<th>{html.escape(field)}</th>" for field in fields)
        body = []
        for row in rows:
            cells = "".join(html.escape(str(round_value(row.get(field, "")))) for field in fields)
            body.append("<tr>" + "".join(f"<td>{cell}</td>" for cell in cells.split("</td><td>")) + "</tr>")
        # Rebuild cells plainly to avoid depending on separators.
        body = []
        for row in rows:
            body.append(
                "<tr>"
                + "".join(f"<td>{html.escape(str(round_value(row.get(field, ''))))}</td>" for field in fields)
                + "</tr>"
            )
        return f"<table><thead><tr>{head}</tr></thead><tbody>{''.join(body)}</tbody></table>"

    content = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>R338 Paper Claim Integrity Audit</title>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, sans-serif; margin: 32px; line-height: 1.45; }}
    table {{ border-collapse: collapse; width: 100%; margin: 16px 0; font-size: 13px; }}
    th, td {{ border: 1px solid #d0d7de; padding: 6px 8px; text-align: left; vertical-align: top; }}
    th {{ background: #f6f8fa; }}
    code {{ background: #f6f8fa; padding: 1px 4px; border-radius: 4px; }}
  </style>
</head>
<body>
  <h1>R338 Paper Claim Integrity Audit</h1>
  <p><strong>Overall:</strong> {html.escape(summary['overall'])}</p>
  <p>{html.escape(payload['claim_position'])}</p>
  <h2>Summary</h2>
  {table([summary], ['result_invariants', 'source_policy', 'paper_text_coverage', 'guardrails', 'two_abstraction_boundary', 'source_artifacts_tracked_clean', 'paper_sources_hashed'])}
  <h2>Number Checks</h2>
  {table(payload['number_checks'], ['run_id', 'key', 'expected', 'actual', 'status', 'source'])}
  <h2>Guardrails</h2>
  {table(payload['guardrail_checks'], ['doc', 'guardrail', 'status', 'occurrences', 'occurrence_lines', 'unguarded_lines'])}
</body>
</html>
"""
    path.write_text(content, encoding="utf-8")


def build_payload() -> dict[str, Any]:
    source_status = {}
    for name, path in SOURCE_ARTIFACTS.items():
        source_status[name] = {
            "path": rel(path),
            "status": git_path_status(path, require_clean=True),
            "sha256": sha256_file(path),
        }
    r342_report_for_sources = load_json(SOURCE_ARTIFACTS["R342 report"])
    for path in r342_source_paths(r342_report_for_sources):
        key = f"R342 upstream source: {rel(path)}"
        source_status[key] = {
            "path": rel(path),
            "status": git_path_status(path, require_clean=True),
            "sha256": sha256_file(path),
        }

    paper_status = {}
    texts = {}
    for name, path in PAPER_SOURCES.items():
        repo_root = SUBMODULE_ROOT if path.is_relative_to(SUBMODULE_ROOT) else ROOT
        git_path_status(path, repo_root=repo_root, require_clean=False)
        paper_status[name] = {
            "path": rel(path),
            "status": "tracked_hashed",
            "sha256": sha256_file(path),
        }
        texts[name] = path.read_text(encoding="utf-8")

    reports = {
        "R320": load_json(SOURCE_ARTIFACTS["R320 report"]),
        "R333": load_json(SOURCE_ARTIFACTS["R333 report"]),
        "R334": load_json(SOURCE_ARTIFACTS["R334 report"]),
        "R335": load_json(SOURCE_ARTIFACTS["R335 report"]),
        "R336": load_json(SOURCE_ARTIFACTS["R336 report"]),
        "R337": load_json(SOURCE_ARTIFACTS["R337 report"]),
        "R339": load_json(SOURCE_ARTIFACTS["R339 report"]),
        "R340": load_json(SOURCE_ARTIFACTS["R340 report"]),
        "R341": load_json(SOURCE_ARTIFACTS["R341 report"]),
        "R342": load_json(SOURCE_ARTIFACTS["R342 report"]),
        "R344": load_json(SOURCE_ARTIFACTS["R344 report"]),
        "R345": load_json(SOURCE_ARTIFACTS["R345 report"]),
        "R346": load_json(SOURCE_ARTIFACTS["R346 report"]),
        "R347": load_json(SOURCE_ARTIFACTS["R347 report"]),
    }
    r320_scores = read_csv(SOURCE_ARTIFACTS["R320 policy scores"])
    r333_summary = read_csv(SOURCE_ARTIFACTS["R333 curve summary"])
    r334_default = read_csv(SOURCE_ARTIFACTS["R334 default comparisons"])
    r334_budget = read_csv(SOURCE_ARTIFACTS["R334 budget comparisons"])
    r337_targets = read_csv(SOURCE_ARTIFACTS["R337 policy targets"])
    r337_comparisons = read_csv(SOURCE_ARTIFACTS["R337 default comparisons"])
    r339_policy_summary = read_csv(SOURCE_ARTIFACTS["R339 policy sequence summary"])
    r339_comparisons = read_csv(SOURCE_ARTIFACTS["R339 default comparisons"])
    r340_decisions = read_csv(SOURCE_ARTIFACTS["R340 transfer decisions"])
    r340_objectives = read_csv(SOURCE_ARTIFACTS["R340 objective summary"])
    r341_objectives = read_csv(SOURCE_ARTIFACTS["R341 objective attribution"])
    r341_transfer = read_csv(SOURCE_ARTIFACTS["R341 transfer attribution"])
    r342_variants = read_csv(SOURCE_ARTIFACTS["R342 variants"])
    r342_tasks = read_csv(SOURCE_ARTIFACTS["R342 tasks"])
    r342_source_variants, r342_source_tasks = build_r342_rows_from_sources(reports["R342"])
    r344_metric_summary = read_csv(SOURCE_ARTIFACTS["R344 metric summary"])
    r344_task_deltas = read_csv(SOURCE_ARTIFACTS["R344 task metric deltas"])
    r345_lens_summary = read_csv(SOURCE_ARTIFACTS["R345 lens summary"])
    r345_task_cards = read_csv(SOURCE_ARTIFACTS["R345 task cards"])
    r345_counterpoints = read_csv(SOURCE_ARTIFACTS["R345 counterpoint ledger"])
    r346_task_cards = read_csv(SOURCE_ARTIFACTS["R346 task cards"])
    r346_top_stack_evidence = read_csv(SOURCE_ARTIFACTS["R346 top stack evidence"])
    r347_view_metrics = read_csv(SOURCE_ARTIFACTS["R347 view metrics"])
    r347_task_cards = read_csv(SOURCE_ARTIFACTS["R347 task cards"])
    r347_pair_summary = read_csv(SOURCE_ARTIFACTS["R347 pair summary"])
    r347_top_group_contrast = read_csv(SOURCE_ARTIFACTS["R347 top group contrast"])

    number_checks = build_number_checks(
        reports,
        r320_scores,
        r333_summary,
        r334_default,
        r334_budget,
        r337_targets,
        r337_comparisons,
        r339_policy_summary,
        r339_comparisons,
        r340_decisions,
        r340_objectives,
        r341_objectives,
        r341_transfer,
        r342_variants,
        r342_tasks,
        r342_source_variants,
        r342_source_tasks,
        r344_metric_summary,
        r344_task_deltas,
        r345_lens_summary,
        r345_task_cards,
        r345_counterpoints,
        r346_task_cards,
        r346_top_stack_evidence,
        r347_view_metrics,
        r347_task_cards,
        r347_pair_summary,
        r347_top_group_contrast,
    )
    policy_checks = validate_source_policies(reports)
    text_coverage = build_text_coverage(texts, number_checks)
    guardrail_checks = build_guardrail_checks(texts)
    abstraction_text_checks = build_abstraction_text_checks(texts)

    result_status = row_status(number_checks)
    source_policy_status = row_status(policy_checks)
    text_status = row_status(text_coverage)
    guardrail_status = row_status(guardrail_checks)
    abstraction_status = row_status(policy_checks + abstraction_text_checks)
    blocking = [
        name
        for name, status in [
            ("result_invariants", result_status),
            ("source_policy", source_policy_status),
            ("paper_text_coverage", text_status),
            ("guardrails", guardrail_status),
            ("two_abstraction_boundary", abstraction_status),
        ]
        if status == "fail"
    ]
    warnings = [
        name
        for name, status in [
            ("result_invariants", result_status),
            ("source_policy", source_policy_status),
            ("paper_text_coverage", text_status),
            ("guardrails", guardrail_status),
            ("two_abstraction_boundary", abstraction_status),
        ]
        if status == "warn"
    ]
    overall = "pass" if not blocking else "fail"

    return {
        "schema": "agentsight.paper-claim-integrity.v1",
        "run_id": RUN_ID,
        "input_policy": {
            "dataset_sync": "none",
            "dataset_creation": "none",
            "dataset_relabeling": "none",
            "network_access_required": False,
            "source_text_clean_policy": "paper text sources may be current worktree edits and are hashed; empirical source artifacts must be tracked clean",
            "hidden_label_use": "R338 reads already-scored R320-R347 artifacts and does not form new rankings from hidden labels",
        },
        "non_claims": [
            "not a human/agent analyst study",
            "not evidence of human productivity, analyst accuracy, or time-to-answer",
            "not automatic discovery of all intent or semantic boundaries",
            "not complete compatibility with OpenTelemetry, Phoenix, LangSmith, Langfuse, or Perfetto ecosystems",
            "not a universal selector for one view, depth, or ranker",
        ],
        "profiler_abstractions": ABSTRACTIONS,
        "source_status": source_status,
        "paper_status": paper_status,
        "number_checks": number_checks,
        "source_policy_checks": policy_checks,
        "text_coverage": text_coverage,
        "guardrail_checks": guardrail_checks,
        "abstraction_text_checks": abstraction_text_checks,
        "claim_position": (
            "Operation/operation-stack profiling is currently supported as a "
            "profiler localization, ranking, fragmentation, and actionability "
            "claim over real labeled traces. The evidence supports faithful "
            "attribution and lower inspection work or fragmentation in scoped "
            "settings, while preserving counterpoints where fixed-session, flat, "
            "dataset-native, raw-action, or width policies are better."
        ),
        "summary": {
            "overall": overall,
            "blocking": blocking,
            "warnings": warnings,
            "result_invariants": result_status,
            "source_policy": source_policy_status,
            "paper_text_coverage": text_status,
            "guardrails": guardrail_status,
            "two_abstraction_boundary": abstraction_status,
            "number_checks_total": len(number_checks),
            "number_checks_passed": sum(row["status"] == "pass" for row in number_checks),
            "source_policy_checks_total": len(policy_checks),
            "source_policy_checks_passed": sum(row["status"] == "pass" for row in policy_checks),
            "guardrail_checks_total": len(guardrail_checks),
            "guardrail_checks_passed": sum(row["status"] == "pass" for row in guardrail_checks),
            "source_artifacts_tracked_clean": all(
                item["status"] == "tracked_clean" for item in source_status.values()
            ),
            "paper_sources_hashed": len(paper_status),
            "profiler_abstractions": ABSTRACTIONS,
            "network_access_required": False,
        },
    }


def main() -> None:
    args = parse_args()
    out_dir = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    payload = build_payload()
    write_json(out_dir / "claim-integrity-report.json", payload)
    build_markdown(out_dir / "claim-integrity-report.md", payload)
    build_html(out_dir / "index.html", payload)
    write_csv(
        out_dir / "claim-number-checks.csv",
        payload["number_checks"],
        ["run_id", "key", "actual", "expected", "status", "source", "paper_token"],
    )
    write_csv(
        out_dir / "source-policy-checks.csv",
        payload["source_policy_checks"],
        ["run_id", "key", "actual", "expected", "status", "source", "paper_token"],
    )
    write_csv(
        out_dir / "paper-text-coverage.csv",
        payload["text_coverage"],
        ["doc", "key", "source", "tokens", "status", "lines"],
    )
    write_csv(
        out_dir / "guardrail-checks.csv",
        payload["guardrail_checks"],
        ["doc", "guardrail", "status", "occurrences", "occurrence_lines", "unguarded_lines"],
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
