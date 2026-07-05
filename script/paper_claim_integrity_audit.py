#!/usr/bin/env python3
"""R338: paper-claim integrity audit over R320-R341 evidence.

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
import time
from collections import Counter
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


def git_output(args: list[str], cwd: Path = ROOT) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=cwd,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip()
        raise SystemExit(f"git {' '.join(args)} failed in {cwd}: {detail}")
    return result.stdout.strip()


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
        if row.get("uses_hidden_fields") == "False" and not policy_key(row).startswith("label_drilldown:")
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

    r341 = reports["R341"]
    r341_summary = r341["summary"]
    add_check(rows, run_id="R341", key="overall", actual=r341_summary["overall"], expected="pass", source="R341 summary")
    add_check(rows, run_id="R341", key="tasks", actual=r341_summary["tasks"], expected=6, source="R341 summary")
    add_check(rows, run_id="R341", key="objective_rows", actual=r341_summary["objective_rows"], expected=36, source="R341 summary")
    add_check(rows, run_id="R341", key="objective_csv_rows", actual=len(r341_objectives), expected=36, source="R341 objective-mechanism-attribution.csv")
    add_check(rows, run_id="R341", key="actionable_objective_rows", actual=r341_summary["actionable_objective_rows"], expected=36, source="R341 summary", paper_token="36/36")
    add_check(rows, run_id="R341", key="nondefault_best_objective_rows", actual=r341_summary["nondefault_best_objective_rows"], expected=27, source="R341 summary", paper_token="27/36")
    add_check(rows, run_id="R341", key="transfer_decisions", actual=r341_summary["transfer_decisions"], expected=96, source="R341 summary")
    add_check(rows, run_id="R341", key="transfer_csv_rows", actual=len(r341_transfer), expected=96, source="R341 transfer-error-attribution.csv")
    add_check(rows, run_id="R341", key="transfer_misses", actual=r341_summary["transfer_misses"], expected=34, source="R341 summary", paper_token="34/96")
    add_check(rows, run_id="R341", key="transfer_misses_with_view_change", actual=r341_summary["transfer_misses_with_view_change"], expected=32, source="R341 summary", paper_token="32/34")
    add_check(rows, run_id="R341", key="transfer_misses_with_ranker_change", actual=r341_summary["transfer_misses_with_ranker_change"], expected=26, source="R341 summary", paper_token="26/34")
    add_check(rows, run_id="R341", key="high_regret_transfer_misses", actual=r341_summary["high_regret_transfer_misses"], expected=29, source="R341 summary", paper_token="29/34")
    add_check(rows, run_id="R341", key="stack_depth_tradeoff_tasks", actual=r341_summary["mechanism_task_counts"]["stack_depth_tradeoff"], expected=6, source="R341 summary.mechanism_task_counts", paper_token="6/6")
    add_check(rows, run_id="R341", key="transfer_policy_signal_tasks", actual=r341_summary["mechanism_task_counts"]["transfer_policy_signal"], expected=6, source="R341 summary.mechanism_task_counts", paper_token="6/6")
    add_check(rows, run_id="R341", key="critical_rank_feature_tasks", actual=r341_summary["mechanism_task_counts"]["critical_rank_features"], expected=4, source="R341 summary.mechanism_task_counts", paper_token="4/6")
    add_check(rows, run_id="R341", key="misleading_feature_tasks", actual=r341_summary["mechanism_task_counts"]["misleading_feature_risk"], expected=2, source="R341 summary.mechanism_task_counts", paper_token="2/6")
    add_check(rows, run_id="R341", key="tasks_with_three_or_more_mechanism_labels", actual=r341_summary["tasks_with_three_or_more_mechanism_labels"], expected=6, source="R341 summary", paper_token="6/6")
    return rows


def contains_any(text: str, tokens: list[str]) -> bool:
    return any(token in text for token in tokens)


def line_hits(text: str, tokens: list[str], limit: int = 8) -> list[int]:
    hits: list[int] = []
    for index, line in enumerate(text.splitlines(), start=1):
        if any(token in line for token in tokens):
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
        ("zh_main", "R320 headline", ["0.0937", "9.37", "285.0", "157.5"], "R320"),
        ("zh_main", "R333 headline", ["0.3900", "0.390"], "R333"),
        ("zh_main", "R337 headline", ["0.2000", "16.0", "50.0"], "R337"),
        ("zh_main", "R339 headline", ["0.4669", "0.9103", "0.3467"], "R339"),
        ("zh_main", "R340 headline", ["R340", "62/96", "72/96", "69/96"], "R340"),
        ("zh_main", "R341 headline", ["R341", "36/36", "27/36", "34/96"], "R341"),
        ("en_main", "R320 headline", ["0.0937", "9.37", "285.0", "157.5"], "R320"),
        ("en_main", "R333 headline", ["0.3900", "0.390"], "R333"),
        ("en_main", "R337 headline", ["0.2000", "16.0", "50.0"], "R337"),
        ("en_main", "R339 headline", ["0.4669", "0.9103", "0.3467"], "R339"),
        ("en_main", "R340 headline", ["R340", "62 of 96", "72 of 96", "69 of 96"], "R340"),
        ("en_main", "R341 headline", ["R341", "36 of 36", "27 of 36", "34 of 96"], "R341"),
        ("zh_claim_setup", "two abstractions", ["两个核心抽象", "operation stack"], "C2"),
        ("zh_claim_setup", "R337 result", ["R337", "0.2000", "16.0"], "R337"),
        ("zh_claim_setup", "R339 result", ["R339", "0.4669", "0.9103"], "R339"),
        ("zh_claim_setup", "R340 result", ["R340", "62/96", "72/96", "69/96"], "R340"),
        ("zh_claim_setup", "R341 result", ["R341", "36/36", "27/36", "34/96"], "R341"),
    ]
    rows: list[dict[str, Any]] = []
    for doc, key, tokens, source in required:
        text = texts[doc]
        status = "pass" if contains_any(text, tokens) else "fail"
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
        if row["run_id"] not in {"R320", "R333", "R337", "R339", "R340", "R341"}:
            continue
        token = str(row["paper_token"])
        status = "pass" if token in eval_text else "warn"
        rows.append(
            {
                "doc": "evaluation",
                "key": f"{row['run_id']}:{row['key']}",
                "source": row["source"],
                "tokens": token,
                "status": status,
                "lines": ",".join(map(str, line_hits(eval_text, [token]))) or "missing",
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
        "R338 mechanically audits the current profiling-paper claim against R320-R341 result artifacts and the Chinese/English paper text. It does not fetch, sync, create, or relabel datasets.",
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
        if row["run_id"] in {"R320", "R333", "R334", "R337", "R339", "R340", "R341"}:
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

    paper_status = {}
    texts = {}
    for name, path in PAPER_SOURCES.items():
        repo_root = SUBMODULE_ROOT if path.is_relative_to(SUBMODULE_ROOT) else ROOT
        paper_status[name] = {
            "path": rel(path),
            "status": git_path_status(path, repo_root=repo_root, require_clean=False),
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
        "created_unix": time.time(),
        "commit": git_output(["rev-parse", "HEAD"]),
        "submodule_commit": git_output(["rev-parse", "HEAD"], cwd=SUBMODULE_ROOT),
        "input_policy": {
            "dataset_sync": "none",
            "dataset_creation": "none",
            "dataset_relabeling": "none",
            "network_access_required": False,
            "source_text_clean_policy": "paper text sources may be current worktree edits and are hashed; empirical source artifacts must be tracked clean",
            "hidden_label_use": "R338 reads already-scored R320-R341 artifacts and does not form new rankings from hidden labels",
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
            "commit": payload["commit"],
            "submodule_commit": payload["submodule_commit"],
        },
    )
    print(json.dumps(payload["summary"], indent=2, sort_keys=True))
    if payload["summary"]["overall"] != "pass":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
