#!/usr/bin/env python3
"""R368: audit trace-tree-shaped baseline tradeoffs for the core claim.

This is a paper-integration and baseline-scope gate, not a new profiler run. It
reads existing hidden-label scoring artifacts and makes explicit what the paper
can claim against flat summaries, fixed-session trace-tree-shaped drilldown,
dataset-native hierarchies, and raw-action stacks.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import html
import json
import math
import subprocess
import time
from pathlib import Path
from statistics import mean, median
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OUT_ROOT = ROOT / "docs" / "visexp" / "out"
SUBMODULE_ROOT = ROOT / "docs" / "agentpprof-paper"
DEFAULT_OUT_DIR = OUT_ROOT / "paper-trace-tree-baseline-r368"
RUN_ID = "R368"
SCRIPT_PATH = Path(__file__).resolve()

R320_DIR = OUT_ROOT / "operation-profile-accuracy-r320"
R355_DIR = OUT_ROOT / "operation-oracle-depth-adequacy-r355"
SOURCE_PATHS = {
    "generator script": SCRIPT_PATH,
    "R320 profile accuracy report": R320_DIR / "profile-accuracy-report.json",
    "R320 policy scores": R320_DIR / "policy-scores.csv",
    "R320 task accuracy": R320_DIR / "task-accuracy.csv",
    "R355 oracle depth report": R355_DIR / "oracle-depth-adequacy-report.json",
    "R355 depth comparisons": R355_DIR / "depth-policy-comparisons.csv",
    "R361 core claim evidence": OUT_ROOT / "paper-core-claim-evidence-r361" / "core-claim-evidence.json",
    "R364 core experiment sufficiency": OUT_ROOT
    / "paper-core-experiment-sufficiency-r364"
    / "core-experiment-sufficiency.json",
    "R367 entry claim path": OUT_ROOT / "paper-entry-claim-path-r367" / "entry-claim-path-report.json",
    "Chinese paper": ROOT / "docs" / "visexp" / "paper" / "main.tex",
    "English paper": SUBMODULE_ROOT / "main.tex",
    "evaluation ledger": ROOT / "docs" / "evaluation.md",
}

HEADLINE_POLICY = "operation_stack:query_aware"
BASELINE_POLICIES = [
    ("flat:width", "flat summary", "summary baseline"),
    ("fixed_session:query_aware", "fixed-session drilldown", "trace-tree-shaped baseline"),
    ("dataset_native:query_aware", "dataset-native hierarchy", "native hierarchy baseline"),
    ("raw_action_stack:query_aware", "raw-action stack", "action-tree baseline"),
]
METRICS = {
    "average_precision": "higher",
    "budget30_recall": "higher",
    "ndcg": "higher",
    "top5_f1": "higher",
    "top5_precision": "higher",
    "top5_recall": "higher",
    "top5_work": "lower",
    "work_to_first_positive": "lower",
    "groups": "lower",
    "groups_to_50pct_recall": "lower",
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


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(read_text(path))


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(round_value(payload), indent=2, sort_keys=True) + "\n", encoding="utf-8")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def git_status(path: Path) -> str:
    repo_root = ROOT
    try:
        path.resolve().relative_to(SUBMODULE_ROOT)
        repo_root = SUBMODULE_ROOT
    except ValueError:
        pass
    try:
        display = str(path.resolve().relative_to(repo_root))
    except ValueError:
        display = str(path)
    tracked = subprocess.run(
        ["git", "ls-files", "--error-unmatch", "--", display],
        cwd=repo_root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if tracked.returncode != 0:
        return "untracked_or_missing"
    unstaged = subprocess.run(["git", "diff", "--quiet", "--", display], cwd=repo_root, check=False)
    staged = subprocess.run(["git", "diff", "--cached", "--quiet", "--", display], cwd=repo_root, check=False)
    return "tracked_clean" if unstaged.returncode == 0 and staged.returncode == 0 else "tracked_dirty_allowed"


def git_commit() -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=ROOT,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
    )
    return result.stdout.strip()


def source_rows() -> list[dict[str, str]]:
    return [
        {"source": source, "path": rel(path), "status": git_status(path), "sha256": sha256(path)}
        for source, path in SOURCE_PATHS.items()
    ]


def parse_float(value: str | None) -> float | None:
    if value is None or value == "":
        return None
    if value == "inf":
        return math.inf
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


def fmt(value: Any) -> Any:
    if value is None:
        return ""
    if isinstance(value, float):
        if math.isinf(value):
            return "inf"
        if math.isnan(value):
            return ""
        return round(value, 6)
    if isinstance(value, dict):
        return json.dumps(round_value(value), sort_keys=True)
    if isinstance(value, list):
        return "; ".join(str(v) for v in value)
    return value


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: fmt(row.get(field)) for field in fields})


def policy_key(row: dict[str, str]) -> str:
    return f"{row['view']}:{row['ranker']}"


def task_policy_map(policy_rows: list[dict[str, str]]) -> dict[tuple[str, str], dict[str, str]]:
    mapping: dict[tuple[str, str], dict[str, str]] = {}
    for row in policy_rows:
        if row.get("uses_hidden_fields") == "True":
            continue
        mapping[(row["task"], policy_key(row))] = row
    return mapping


def compare_policies(
    policy_rows: list[dict[str, str]],
    left_policy: str,
    right_policy: str,
) -> dict[str, Any]:
    rows_by_key = task_policy_map(policy_rows)
    tasks = sorted(task for task, policy in rows_by_key if policy == left_policy and (task, right_policy) in rows_by_key)
    metrics: dict[str, Any] = {}
    task_rows: list[dict[str, Any]] = []
    for metric, direction in METRICS.items():
        deltas: list[float] = []
        ratios: list[float] = []
        improved = worse = tied = 0
        for task in tasks:
            left = parse_float(rows_by_key[(task, left_policy)].get(metric))
            right = parse_float(rows_by_key[(task, right_policy)].get(metric))
            if left is None or right is None:
                continue
            delta = left - right
            ratio = math.inf if right == 0 and left > 0 else (0.0 if right == 0 else left / right)
            deltas.append(delta)
            ratios.append(ratio)
            if abs(delta) < 1e-12:
                tied += 1
            elif (direction == "higher" and left > right) or (direction == "lower" and left < right):
                improved += 1
            else:
                worse += 1
        metrics[metric] = {
            "direction": direction,
            "improved_tasks": improved,
            "worse_tasks": worse,
            "tied_tasks": tied,
            "median_delta": median(deltas) if deltas else None,
            "mean_delta": mean(deltas) if deltas else None,
            "median_ratio": median(ratios) if ratios else None,
        }
    for task in tasks:
        left_row = rows_by_key[(task, left_policy)]
        right_row = rows_by_key[(task, right_policy)]
        task_rows.append(
            {
                "task": task,
                "dataset": left_row["dataset"],
                "baseline": right_policy,
                "operation_stack_ap": parse_float(left_row["average_precision"]),
                "baseline_ap": parse_float(right_row["average_precision"]),
                "operation_stack_top5_recall": parse_float(left_row["top5_recall"]),
                "baseline_top5_recall": parse_float(right_row["top5_recall"]),
                "operation_stack_top5_work": parse_float(left_row["top5_work"]),
                "baseline_top5_work": parse_float(right_row["top5_work"]),
                "operation_stack_budget30_recall": parse_float(left_row["budget30_recall"]),
                "baseline_budget30_recall": parse_float(right_row["budget30_recall"]),
                "operation_stack_groups": parse_float(left_row["groups"]),
                "baseline_groups": parse_float(right_row["groups"]),
                "operation_stack_wtfp": parse_float(left_row["work_to_first_positive"]),
                "baseline_wtfp": parse_float(right_row["work_to_first_positive"]),
            }
        )
    return {"left": left_policy, "right": right_policy, "tasks": len(tasks), "metrics": metrics, "task_rows": task_rows}


def baseline_summary_rows(r320: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    policies = [(HEADLINE_POLICY, "operation-stack query-aware", "proposed operation/operation-stack view")]
    policies += BASELINE_POLICIES
    for policy, label, role in policies:
        summary = r320["policy_summary"][policy]
        rows.append(
            {
                "policy": policy,
                "label": label,
                "role": role,
                "median_ap": summary["median_average_precision"],
                "median_ndcg": summary["median_ndcg"],
                "median_top5_precision": summary["median_top5_precision"],
                "median_top5_recall": summary["median_top5_recall"],
                "median_top5_work": summary["median_top5_work"],
                "median_budget30_recall": summary["median_budget30_recall"],
                "median_work_to_first_positive": summary["median_work_to_first_positive"],
                "median_groups": summary["median_groups"],
                "median_groups_to_50pct_recall": summary["median_groups_to_50pct_recall"],
            }
        )
    return rows


def comparison_rows(comparisons: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for comparison in comparisons:
        for metric, values in comparison["metrics"].items():
            rows.append(
                {
                    "left": comparison["left"],
                    "right": comparison["right"],
                    "metric": metric,
                    "direction": values["direction"],
                    "tasks": comparison["tasks"],
                    "improved_tasks": values["improved_tasks"],
                    "worse_tasks": values["worse_tasks"],
                    "tied_tasks": values["tied_tasks"],
                    "median_delta": values["median_delta"],
                    "mean_delta": values["mean_delta"],
                    "median_ratio": values["median_ratio"],
                }
            )
    return rows


def build_checks(
    r320: dict[str, Any],
    r355: dict[str, Any],
    r361: dict[str, Any],
    r364: dict[str, Any],
    r367: dict[str, Any],
    comparisons: dict[str, dict[str, Any]],
    paper_text: str,
) -> list[dict[str, str]]:
    checks: list[dict[str, str]] = []

    def add(name: str, condition: bool, evidence: str) -> None:
        checks.append({"check": name, "status": "pass" if condition else "fail", "evidence": evidence})

    fixed = comparisons["fixed_session:query_aware"]
    flat = comparisons["flat:width"]
    dataset_native = comparisons["dataset_native:query_aware"]
    raw_action = comparisons["raw_action_stack:query_aware"]
    r355_claim = r355["claim_summary"]

    add(
        "real_labeled_trace_scale_preserved",
        r320["totals"]["tasks"] == 6
        and r320["totals"]["datasets"] == 4
        and r320["totals"]["task_operations"] == 34539
        and r320["totals"]["positive_operations"] == 3699,
        "R320 covers 6 tasks / 4 datasets / 34,539 operations / 3,699 positives.",
    )
    add(
        "span_tree_scope_is_fixed_session_proxy_not_ecosystem_claim",
        "fixed-session drilldown" in paper_text
        and "trace-tree-shaped baseline" in paper_text
        and "real span-tree imports remain future" in paper_text
        and "complete trace-ecosystem compatibility" in paper_text,
        "Paper text scopes the evaluated trace-tree-shaped baseline to fixed-session drilldown and leaves real ecosystem imports for future work.",
    )
    add(
        "operation_stack_vs_fixed_session_fragmentation_tradeoff",
        fixed["metrics"]["top5_recall"]["improved_tasks"] == 5
        and fixed["metrics"]["top5_f1"]["improved_tasks"] == 5
        and fixed["metrics"]["budget30_recall"]["improved_tasks"] == 4
        and fixed["metrics"]["groups"]["improved_tasks"] == 4
        and r320["policy_summary"][HEADLINE_POLICY]["median_groups"] == 157.5
        and r320["policy_summary"]["fixed_session:query_aware"]["median_groups"] == 285.0,
        "Operation-stack beats fixed-session on top-5 recall/F1 for 5/6 tasks, budget-30 recall for 4/6, group count for 4/6, and median groups 157.5 vs 285.0.",
    )
    add(
        "fixed_session_counterpoints_preserved",
        fixed["metrics"]["top5_work"]["worse_tasks"] == 4
        and fixed["metrics"]["work_to_first_positive"]["worse_tasks"] == 4
        and r320["policy_summary"]["fixed_session:query_aware"]["median_work_to_first_positive"] == 0.0044,
        "Fixed-session remains a counterpoint: it wins top-5 work and first-positive work on 4/6 tasks, with 0.0044 median WTFP.",
    )
    add(
        "operation_stack_vs_flat_inspection_work_tradeoff",
        flat["metrics"]["average_precision"]["improved_tasks"] == 6
        and flat["metrics"]["budget30_recall"]["improved_tasks"] == 6
        and flat["metrics"]["top5_work"]["improved_tasks"] == 6
        and r320["policy_summary"][HEADLINE_POLICY]["median_top5_work"] == 0.0937,
        "Operation-stack improves AP, budget-30 recall, and top-5 work on 6/6 tasks vs flat; median top-5 work is 0.0937 vs flat 1.0.",
    )
    add(
        "dataset_native_tradeoff_preserved",
        dataset_native["metrics"]["average_precision"]["improved_tasks"] == 4
        and dataset_native["metrics"]["budget30_recall"]["improved_tasks"] == 5
        and dataset_native["metrics"]["top5_work"]["improved_tasks"] == 6
        and dataset_native["metrics"]["groups"]["worse_tasks"] == 6,
        "Dataset-native hierarchy has fewer groups and broader top-5 recall, but operation-stack improves AP on 4/6, budget recall on 5/6, and top-5 work on 6/6.",
    )
    add(
        "raw_action_stack_is_not_sufficient_baseline",
        raw_action["metrics"]["average_precision"]["improved_tasks"] >= 4
        and raw_action["metrics"]["budget30_recall"]["improved_tasks"] >= 4
        and raw_action["metrics"]["top5_recall"]["worse_tasks"] >= 3,
        "Raw-action stacks are useful counterpoints but miss task-aware aggregation: operation-stack improves AP/budget recall on at least 4/6 while raw-action keeps some top-5 recall wins.",
    )
    add(
        "oracle_depth_confirms_fixed_session_fragmentation_support",
        r355_claim["paired_checks"]["budget30_unit_recall_gt_fixed_rows"] == 20
        and r355_claim["paired_checks"]["groups_to_50pct_units_lt_fixed_rows"] == 22
        and r355_claim["accuracy_unit_depth_rows"] == 24,
        "R355 confirms depth-aware support: 20/24 fixed-session unit-recall wins and 22/24 groups-to-50%-positive-unit wins.",
    )
    add(
        "core_experiment_structure_remains_e1_e4",
        r361["status"] == "pass"
        and r361["summary"]["core_experiments"] == 4
        and r364["status"] == "pass"
        and r364["summary"]["core_experiments"] == 4
        and r367["status"] == "pass",
        "R361/R364/R367 keep this as E2 baseline evidence inside E1-E4, not a fifth core experiment.",
    )
    add(
        "two_abstractions_and_no_new_data_policy_preserved",
        r320["profiler_abstractions"] == ["operation", "operation stack"]
        and r367["profiler_abstractions"] == ["operation", "operation stack"]
        and r320["input_policy"]["dataset_sync"] == "none"
        and r367["input_policy"]["dataset_sync"] == "none"
        and r367["input_policy"]["profiler_rerun"] is False,
        "The audit reads tracked outputs only and preserves operation/operation-stack as the only profiler abstractions.",
    )
    return checks


def write_markdown(path: Path, payload: dict[str, Any]) -> None:
    lines = [
        "# R368 Trace-Tree Baseline Tradeoff Audit",
        "",
        f"- Status: `{payload['status']}`.",
        f"- Checks: {payload['summary']['checks_passed']}/{payload['summary']['checks_total']}.",
        "- This is an E2 paper-integration audit over existing R320/R355 hidden-label scoring outputs.",
        "- It does not import real OpenTelemetry/Phoenix/LangSmith/Perfetto traces; fixed-session is the evaluated trace-tree-shaped baseline.",
        "",
        "## Baseline Summary",
        "",
        "| Policy | Role | AP | Top-5 work | Budget-30 recall | WTFP | Groups |",
        "|---|---|---:|---:|---:|---:|---:|",
    ]
    for row in payload["baseline_rows"]:
        lines.append(
            f"| `{row['policy']}` | {row['role']} | {row['median_ap']} | {row['median_top5_work']} | "
            f"{row['median_budget30_recall']} | {row['median_work_to_first_positive']} | {row['median_groups']} |"
        )
    lines.extend(["", "## Checks", "", "| Check | Status | Evidence |", "|---|---|---|"])
    for check in payload["checks"]:
        lines.append(f"| `{check['check']}` | {check['status']} | {check['evidence']} |")
    lines.extend(["", "## Non-Claims", ""])
    for item in payload["non_claims"]:
        lines.append(f"- {item}")
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def write_html(path: Path, payload: dict[str, Any]) -> None:
    baseline_rows = "\n".join(
        "<tr>"
        f"<td>{html.escape(row['policy'])}</td>"
        f"<td>{html.escape(row['role'])}</td>"
        f"<td>{row['median_ap']}</td>"
        f"<td>{row['median_top5_work']}</td>"
        f"<td>{row['median_budget30_recall']}</td>"
        f"<td>{row['median_work_to_first_positive']}</td>"
        f"<td>{row['median_groups']}</td>"
        "</tr>"
        for row in payload["baseline_rows"]
    )
    check_rows = "\n".join(
        "<tr>"
        f"<td>{html.escape(row['check'])}</td>"
        f"<td>{html.escape(row['status'])}</td>"
        f"<td>{html.escape(row['evidence'])}</td>"
        "</tr>"
        for row in payload["checks"]
    )
    path.write_text(
        f"""<!doctype html>
<html>
<head>
<meta charset=\"utf-8\">
<title>R368 Trace-Tree Baseline Tradeoff Audit</title>
<style>
body {{ font-family: system-ui, sans-serif; margin: 2rem; line-height: 1.45; }}
table {{ border-collapse: collapse; width: 100%; margin: 1rem 0; }}
th, td {{ border: 1px solid #ddd; padding: 0.45rem; vertical-align: top; }}
th {{ background: #f5f5f5; text-align: left; }}
code {{ background: #f3f3f3; padding: 0.1rem 0.2rem; }}
</style>
</head>
<body>
<h1>R368 Trace-Tree Baseline Tradeoff Audit</h1>
<p>Status: <code>{html.escape(payload['status'])}</code>;
checks: {payload['summary']['checks_passed']}/{payload['summary']['checks_total']}.</p>
<h2>Baseline Summary</h2>
<table>
<tr><th>Policy</th><th>Role</th><th>AP</th><th>Top-5 work</th><th>Budget-30 recall</th><th>WTFP</th><th>Groups</th></tr>
{baseline_rows}
</table>
<h2>Checks</h2>
<table>
<tr><th>Check</th><th>Status</th><th>Evidence</th></tr>
{check_rows}
</table>
</body>
</html>
""",
        encoding="utf-8",
    )


def main() -> int:
    args = parse_args()
    out_dir = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    start = time.time()

    r320 = read_json(SOURCE_PATHS["R320 profile accuracy report"])
    r355 = read_json(SOURCE_PATHS["R355 oracle depth report"])
    r361 = read_json(SOURCE_PATHS["R361 core claim evidence"])
    r364 = read_json(SOURCE_PATHS["R364 core experiment sufficiency"])
    r367 = read_json(SOURCE_PATHS["R367 entry claim path"])
    policy_rows = read_csv(SOURCE_PATHS["R320 policy scores"])
    paper_text = "\n".join(
        read_text(SOURCE_PATHS[name])
        for name in ["Chinese paper", "English paper", "evaluation ledger"]
    )

    comparisons = {
        policy: compare_policies(policy_rows, HEADLINE_POLICY, policy)
        for policy, _label, _role in BASELINE_POLICIES
    }
    baseline_rows = baseline_summary_rows(r320)
    comp_rows = comparison_rows(list(comparisons.values()))
    task_rows = [row for comparison in comparisons.values() for row in comparison["task_rows"]]
    checks = build_checks(r320, r355, r361, r364, r367, comparisons, paper_text)
    checks_passed = sum(row["status"] == "pass" for row in checks)
    status = "pass" if checks_passed == len(checks) else "fail"
    payload = {
        "run_id": RUN_ID,
        "schema": "agentsight.paper-trace-tree-baseline.v1",
        "status": status,
        "commit": git_commit(),
        "elapsed_s": round(time.time() - start, 3),
        "claim": (
            "Operation-stack profiling has a measurable Pareto tradeoff against "
            "flat summaries, fixed-session trace-tree-shaped drilldown, "
            "dataset-native hierarchies, and raw-action stacks on real labeled traces."
        ),
        "input_policy": {
            "dataset_creation": "none",
            "dataset_relabeling": "none",
            "dataset_sync": "none",
            "hidden_label_use": "only through already-scored R320/R355 artifacts",
            "network_access_required": False,
            "profiler_rerun": False,
        },
        "not_new_empirical_result": True,
        "not_a_human_study_result": True,
        "not_an_agent_analyst_task_result": True,
        "profiler_abstractions": ["operation", "operation stack"],
        "summary": {
            "checks_passed": checks_passed,
            "checks_total": len(checks),
            "tasks": r320["totals"]["tasks"],
            "datasets": r320["totals"]["datasets"],
            "operations": r320["totals"]["task_operations"],
            "positives": r320["totals"]["positive_operations"],
            "operation_stack_median_top5_work": r320["policy_summary"][HEADLINE_POLICY]["median_top5_work"],
            "flat_median_top5_work": r320["policy_summary"]["flat:width"]["median_top5_work"],
            "operation_stack_median_groups": r320["policy_summary"][HEADLINE_POLICY]["median_groups"],
            "fixed_session_median_groups": r320["policy_summary"]["fixed_session:query_aware"]["median_groups"],
            "fixed_session_counterpoint_wtfp": r320["policy_summary"]["fixed_session:query_aware"][
                "median_work_to_first_positive"
            ],
            "oracle_depth_budget30_unit_recall_gt_fixed_rows": r355["claim_summary"]["paired_checks"][
                "budget30_unit_recall_gt_fixed_rows"
            ],
            "oracle_depth_groups_to_50pct_units_lt_fixed_rows": r355["claim_summary"]["paired_checks"][
                "groups_to_50pct_units_lt_fixed_rows"
            ],
        },
        "baseline_rows": baseline_rows,
        "comparison_rows": comp_rows,
        "task_rows": task_rows,
        "checks": checks,
        "source_status": source_rows(),
        "non_claims": [
            "not a new profiler run",
            "not a new dataset, dataset sync, or relabeling step",
            "not a human or agent analyst study",
            "not a complete trace-ecosystem compatibility claim",
            "not a real OpenTelemetry/Phoenix/LangSmith/Perfetto span-tree import",
            "not metric dominance over every baseline and metric",
        ],
    }

    write_json(out_dir / "trace-tree-baseline-report.json", payload)
    write_csv(
        out_dir / "baseline-family-summary.csv",
        baseline_rows,
        [
            "policy",
            "label",
            "role",
            "median_ap",
            "median_ndcg",
            "median_top5_precision",
            "median_top5_recall",
            "median_top5_work",
            "median_budget30_recall",
            "median_work_to_first_positive",
            "median_groups",
            "median_groups_to_50pct_recall",
        ],
    )
    write_csv(
        out_dir / "trace-tree-comparisons.csv",
        comp_rows,
        [
            "left",
            "right",
            "metric",
            "direction",
            "tasks",
            "improved_tasks",
            "worse_tasks",
            "tied_tasks",
            "median_delta",
            "mean_delta",
            "median_ratio",
        ],
    )
    write_csv(
        out_dir / "task-baseline-cards.csv",
        task_rows,
        [
            "task",
            "dataset",
            "baseline",
            "operation_stack_ap",
            "baseline_ap",
            "operation_stack_top5_recall",
            "baseline_top5_recall",
            "operation_stack_top5_work",
            "baseline_top5_work",
            "operation_stack_budget30_recall",
            "baseline_budget30_recall",
            "operation_stack_groups",
            "baseline_groups",
            "operation_stack_wtfp",
            "baseline_wtfp",
        ],
    )
    write_csv(out_dir / "trace-tree-baseline-checks.csv", checks, ["check", "status", "evidence"])
    write_csv(out_dir / "source-status.csv", payload["source_status"], ["source", "path", "status", "sha256"])
    write_markdown(out_dir / "trace-tree-baseline.md", payload)
    write_html(out_dir / "index.html", payload)
    run_result = {
        "run_id": RUN_ID,
        "status": status,
        "checks_passed": checks_passed,
        "checks_total": len(checks),
        "report": rel(out_dir / "trace-tree-baseline-report.json"),
        "network_access_required": False,
        "not_new_empirical_result": True,
        "not_a_human_study_result": True,
        "not_an_agent_analyst_task_result": True,
    }
    write_json(out_dir / "run-result.json", run_result)
    print(json.dumps(run_result, indent=2, sort_keys=True))
    return 0 if status == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
