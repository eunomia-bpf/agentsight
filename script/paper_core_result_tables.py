#!/usr/bin/env python3
"""R360: generate paper-facing core result tables from tracked artifacts.

This is a table-consolidation gate, not a new empirical result. It reads the
existing result artifacts that already support E1--E4 and writes compact
paper-ready tables plus provenance rows. No profiler is rerun and no dataset is
downloaded, synced, created, or relabeled.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import html
import json
import subprocess
import time
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OUT_ROOT = ROOT / "docs" / "visexp" / "out"
SUBMODULE_ROOT = ROOT / "docs" / "agentpprof-paper"
DEFAULT_OUT_DIR = OUT_ROOT / "paper-core-result-tables-r360"
RUN_ID = "R360"
SCRIPT_PATH = Path(__file__).resolve()

SOURCES = {
    "R285 leave-dataset-out mapping": OUT_ROOT
    / "operation-map-leaveout-api-r285"
    / "leaveout-summary.json",
    "R286 recursive stack-depth sweep": OUT_ROOT
    / "operation-stack-depth-r286"
    / "depth-summary.json",
    "R320 profile accuracy": OUT_ROOT
    / "operation-profile-accuracy-r320"
    / "profile-accuracy-report.json",
    "R328 deterministic output": OUT_ROOT
    / "operation-profile-deterministic-output-r328"
    / "deterministic-output-report.json",
    "R338 paper claim integrity": OUT_ROOT
    / "paper-claim-integrity-r338"
    / "claim-integrity-report.json",
    "R342 profile-spec composition": OUT_ROOT
    / "operation-profile-spec-composition-r342"
    / "profile-spec-composition-report.json",
    "R353 standard-trace exchange": OUT_ROOT
    / "operation-standard-trace-exchange-r353"
    / "standard-trace-exchange-report.json",
    "R354 executable profile patch": OUT_ROOT
    / "operation-profile-patch-r354"
    / "profile-patch-report.json",
    "R355 oracle-depth adequacy": OUT_ROOT
    / "operation-oracle-depth-adequacy-r355"
    / "oracle-depth-adequacy-report.json",
    "R357 reviewer acceptance": OUT_ROOT
    / "paper-reviewer-acceptance-r357"
    / "reviewer-acceptance-r357.json",
    "R358 boundary profile patch": OUT_ROOT
    / "operation-boundary-profile-patch-r358"
    / "boundary-profile-patch-report.json",
    "R359 core-experiment consolidation": OUT_ROOT
    / "paper-core-experiments-r359"
    / "core-experiment-report.json",
}

PAPER_SOURCES = {
    "evaluation ledger": ROOT / "docs" / "evaluation.md",
    "Chinese claim setup": ROOT / "docs" / "visexp" / "paper" / "evaluation-claims-setup.zh-CN.md",
    "Chinese paper": ROOT / "docs" / "visexp" / "paper" / "main.tex",
    "English paper": SUBMODULE_ROOT / "main.tex",
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


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


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
    )
    if tracked.returncode != 0:
        return "untracked_or_missing"
    unstaged = subprocess.run(["git", "diff", "--quiet", "--", display], cwd=repo_root)
    staged = subprocess.run(["git", "diff", "--cached", "--quiet", "--", display], cwd=repo_root)
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


def fmt(value: Any) -> str:
    if isinstance(value, float):
        return f"{value:.4f}".rstrip("0").rstrip(".")
    return str(value)


def ratio(numerator: Any, denominator: Any) -> str:
    return f"{numerator}/{denominator}"


def source_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for name, path in {"generator script": SCRIPT_PATH, **SOURCES, **PAPER_SOURCES}.items():
        rows.append(
            {
                "source": name,
                "path": rel(path),
                "status": git_status(path),
                "sha256": sha256(path),
            }
        )
    return rows


def metric_rows(data: dict[str, dict[str, Any]]) -> list[dict[str, str]]:
    r285 = data["R285 leave-dataset-out mapping"]["summary"]
    r286 = data["R286 recursive stack-depth sweep"]["summary"]
    r320 = data["R320 profile accuracy"]
    r328 = data["R328 deterministic output"]["summary"]
    r338 = data["R338 paper claim integrity"]["summary"]
    r342 = data["R342 profile-spec composition"]["summary"]
    r353 = data["R353 standard-trace exchange"]
    r354 = data["R354 executable profile patch"]["summary"]
    r355 = data["R355 oracle-depth adequacy"]["claim_summary"]
    r357 = data["R357 reviewer acceptance"]["summary"]
    r358 = data["R358 boundary profile patch"]["summary"]
    r359 = data["R359 core-experiment consolidation"]["summary"]

    policy_summary = r320["policy_summary"]
    paired = r320["paired_comparisons"]
    op_default = policy_summary["operation_stack:query_aware"]
    flat_width = policy_summary["flat:width"]
    fixed_q = policy_summary["fixed_session:query_aware"]
    fixed_cmp = paired["operation_stack_query_aware_vs_fixed_session_query_aware"]["metrics"]
    flat_cmp = paired["operation_stack_query_aware_vs_flat_width"]["metrics"]

    rows = [
        {
            "experiment": "E1",
            "metric": "recursive_depth_sweep_operations",
            "value": fmt(r286["samples"]),
            "baseline_or_comparator": "same operation input",
            "evidence": "R286",
        },
        {
            "experiment": "E1",
            "metric": "stack_depths_and_unique_stack_range",
            "value": f"{r286['stack_depths']} depths, {r286['min_unique_stacks']}->{r286['max_unique_stacks']} stacks",
            "baseline_or_comparator": "dataset depth to fixed-session depth",
            "evidence": "R286",
        },
        {
            "experiment": "E1",
            "metric": "leave_dataset_out_positive_stack_reductions",
            "value": ratio(r285["positive_stack_reduction_datasets"], r285["datasets"]),
            "baseline_or_comparator": "generated mapping vs no-map",
            "evidence": "R285",
        },
        {
            "experiment": "E1",
            "metric": "prompt_session_free_profile_specs",
            "value": ratio(r342["prompt_session_free_variants"], r342["profile_spec_variants"]),
            "baseline_or_comparator": "profile-spec composition",
            "evidence": "R342",
        },
        {
            "experiment": "E1",
            "metric": "real_operation_standard_trace_roundtrip",
            "value": f"{r353['prefix_operations']} ops, {r353['direct_profile']['samples']} samples, "
            f"{r353['direct_profile']['unique_stacks']} stacks, equal={r353['folded_outputs_equal']}",
            "baseline_or_comparator": "direct operation-file profile vs imported standard trace",
            "evidence": "R353",
        },
        {
            "experiment": "E2",
            "metric": "labeled_profile_benchmark_scale",
            "value": f"{r320['totals']['tasks']} tasks / {r320['totals']['datasets']} datasets / "
            f"{r320['totals']['task_operations']} ops / {r320['totals']['positive_operations']} positives / "
            f"{r320['totals']['policy_scores']} policy scores",
            "baseline_or_comparator": "flat, fixed-session, dataset-native, raw-action, operation-stack, oracle",
            "evidence": "R320",
        },
        {
            "experiment": "E2",
            "metric": "top5_inspection_work",
            "value": f"{fmt(op_default['median_top5_work'])} vs {fmt(flat_width['median_top5_work'])}",
            "baseline_or_comparator": "operation_stack:query_aware vs flat:width",
            "evidence": "R320",
        },
        {
            "experiment": "E2",
            "metric": "top5_recall_wins_vs_fixed_session",
            "value": ratio(fixed_cmp["top5_recall"]["improved_tasks"], r320["totals"]["tasks"]),
            "baseline_or_comparator": "operation_stack:query_aware vs fixed_session:query_aware",
            "evidence": "R320",
        },
        {
            "experiment": "E2",
            "metric": "median_group_fragmentation",
            "value": f"{fmt(op_default['median_groups'])} vs {fmt(fixed_q['median_groups'])}",
            "baseline_or_comparator": "operation_stack:query_aware vs fixed_session:query_aware",
            "evidence": "R320",
        },
        {
            "experiment": "E2",
            "metric": "budget30_recall_wins_vs_flat",
            "value": ratio(flat_cmp["budget30_recall"]["improved_tasks"], r320["totals"]["tasks"]),
            "baseline_or_comparator": "operation_stack:query_aware vs flat:width",
            "evidence": "R320",
        },
        {
            "experiment": "E2",
            "metric": "oracle_depth_unit_recall",
            "value": f"{fmt(r355['default_all_depth_medians']['budget30_positive_unit_recall'])}; "
            f"{r355['paired_checks']['budget30_unit_recall_gt_fixed_rows']}/"
            f"{r355['accuracy_unit_depth_rows']} rows beat fixed-session",
            "baseline_or_comparator": "operation_stack:query_aware vs fixed-session at dataset oracle depths",
            "evidence": "R355",
        },
        {
            "experiment": "E3",
            "metric": "profile_spec_patch_acceptance",
            "value": r354["accepted_patches"],
            "baseline_or_comparator": "patched profile specs vs default semantic-width specs",
            "evidence": "R354",
        },
        {
            "experiment": "E3",
            "metric": "patch_median_delta_ap_top5_lift_wtfp",
            "value": f"{fmt(r354['median_delta_ap'])} AP, {fmt(r354['median_delta_top5_lift'])} lift, "
            f"{fmt(r354['median_delta_first_positive_work'])} first-positive work",
            "baseline_or_comparator": "profile-guided patch vs default",
            "evidence": "R354",
        },
        {
            "experiment": "E3",
            "metric": "recursive_depth_actionability",
            "value": f"{r342['ap_improves_vs_width_variants']}/{r342['profile_spec_variants']} AP variants, "
            f"{r342['tasks_where_coarse_reduces_groups']}/{r342['tasks']} tasks reduce groups",
            "baseline_or_comparator": "ranked operation-stack variants vs width",
            "evidence": "R342",
        },
        {
            "experiment": "E3",
            "metric": "boundary_field_patch",
            "value": f"AP {fmt(r358['learned_boundary_ap'])} vs {fmt(r358['semantic_width_ap'])}; "
            f"groups {r358['learned_boundary_groups']} vs {r358['semantic_width_groups']}",
            "baseline_or_comparator": "learned-boundary fields vs semantic width",
            "evidence": "R358",
        },
        {
            "experiment": "E3",
            "metric": "boundary_counterpoint",
            "value": f"top5 work +{fmt(r358['learned_boundary_delta_top5_work_vs_semantic'])}; "
            f"first-positive work +{fmt(r358['learned_boundary_delta_first_positive_work_vs_semantic'])}",
            "baseline_or_comparator": "learned-boundary fields vs semantic width",
            "evidence": "R358",
        },
        {
            "experiment": "E4",
            "metric": "deterministic_profile_specs",
            "value": f"{r328['semantic_deterministic_specs']} semantic, {r328['raw_byte_deterministic_specs']} raw-byte, "
            f"{r328['profiler_invocations']} invocations",
            "baseline_or_comparator": "deterministic-output mode",
            "evidence": "R328",
        },
        {
            "experiment": "E4",
            "metric": "offline_runtime",
            "value": f"median {fmt(r328['median_runtime_ms'] / 1000)}s, p95 {fmt(r328['p95_runtime_ms'] / 1000)}s",
            "baseline_or_comparator": "76 tracked profile specs",
            "evidence": "R328",
        },
    ]
    return rows


def experiment_rows(metrics: list[dict[str, str]]) -> list[dict[str, str]]:
    grouped: dict[str, list[dict[str, str]]] = {}
    for row in metrics:
        grouped.setdefault(row["experiment"], []).append(row)
    summaries = {
        "E1": {
            "core_experiment": "E1: coverage, recursive folding, and field derivation",
            "claim": "Heterogeneous agent traces enter one operation layer, and operation stacks are query-time recursive projections over fields.",
            "workload": "15 public labeled trace families / 47,590 operations, plus local-session and standard-trace exchange fixtures.",
            "conclusion": "Supported as operation/operation-stack coverage and configurability, not a new trace ecosystem compatibility claim.",
        },
        "E2": {
            "core_experiment": "E2: hidden-label localization and ranking",
            "claim": "Profile groups can be scored as ranked localization outputs against real hidden labels.",
            "workload": "Six oracle-backed tasks over AgentRewardBench, SATraj-OS, AgentNet, and OSWorld-Human.",
            "conclusion": "Supported as a hidden-label profiler benchmark with baseline tradeoffs, not human utility.",
        },
        "E3": {
            "core_experiment": "E3: mechanism and actionability",
            "claim": "Stack fields, mapping/tagging, rankers, and profile specs expose actionable optimization knobs.",
            "workload": "The same six labeled tasks plus held-out OSWorld-Human boundary-backend operations.",
            "conclusion": "Supported as actionable profile-spec and field/ranker guidance, not an automatic selector or boundary detector.",
        },
        "E4": {
            "core_experiment": "E4: reproducibility and offline cost",
            "claim": "The offline profiler path is replayable over tracked inputs at low local cost.",
            "workload": "76 tracked profile specs over tracked operation JSONL inputs.",
            "conclusion": "Supported as replayable offline profiling artifact evidence, not live overhead, human productivity, or trace-ecosystem compatibility.",
        },
    }
    rows: list[dict[str, str]] = []
    for eid in ["E1", "E2", "E3", "E4"]:
        evidence = "; ".join(f"{m['metric']}={m['value']} ({m['evidence']})" for m in grouped[eid])
        row = dict(summaries[eid])
        row["evidence"] = evidence
        rows.append(row)
    return rows


def build_checks(data: dict[str, dict[str, Any]], metrics: list[dict[str, str]], experiments: list[dict[str, str]]) -> list[dict[str, Any]]:
    r320 = data["R320 profile accuracy"]
    r328 = data["R328 deterministic output"]["summary"]
    r338 = data["R338 paper claim integrity"]["summary"]
    r352_status = read_json(OUT_ROOT / "paper-evaluation-rubric-r352" / "evaluation-rubric-report.json")
    r357 = data["R357 reviewer acceptance"]
    r359 = data["R359 core-experiment consolidation"]
    metric_blob = json.dumps(metrics, sort_keys=True)
    paper_blob = "\n".join(read_text(path) for path in PAPER_SOURCES.values())
    checks = [
        {
            "check": "four_core_experiment_rows",
            "status": "pass" if len(experiments) == 4 else "fail",
            "evidence": f"{len(experiments)} generated rows.",
        },
        {
            "check": "real_labeled_profile_scale_preserved",
            "status": "pass"
            if r320["totals"]["tasks"] == 6
            and r320["totals"]["datasets"] == 4
            and r320["totals"]["task_operations"] == 34539
            and r320["totals"]["positive_operations"] == 3699
            else "fail",
            "evidence": "R320 scale tokens match the labeled profiler benchmark.",
        },
        {
            "check": "baseline_tradeoff_tokens_present",
            "status": "pass"
            if all(token in metric_blob for token in ["0.0937", "1", "5/6", "157.5", "285"])
            else "fail",
            "evidence": "R320 flat/fixed-session comparison tokens are present.",
        },
        {
            "check": "actionability_tokens_present",
            "status": "pass"
            if all(token in metric_blob for token in ["5/6", "0.0376", "0.575", "0.2583", "0.2402", "74"])
            else "fail",
            "evidence": "R354/R358 actionability and boundary-field tokens are present.",
        },
        {
            "check": "artifact_hygiene_gates_available",
            "status": "pass"
            if r328["semantic_deterministic_specs"] == "76/76"
            and r338["number_checks_passed"] == r338["number_checks_total"] == 350
            and r352_status["summary"]["rubric_level"] == "level_4_scoped_profile_benchmark"
            and r357["overall"] == "accepted"
            and r359["status"] == "pass"
            else "fail",
            "evidence": "R338/R352/R357/R359 remain artifact-hygiene gates, not main empirical evidence.",
        },
        {
            "check": "two_abstractions_and_nonclaims_visible",
            "status": "pass"
            if all(token in paper_blob for token in ["operation", "operation stack", "human utility", "automatic boundary discovery"])
            else "fail",
            "evidence": "Current paper/docs preserve abstraction and must-not-claim text.",
        },
        {
            "check": "fixed_session_baseline_scope_visible",
            "status": "pass"
            if "fixed-session drilldown" in paper_blob
            and "real span-tree imports remain future" in paper_blob
            and "complete trace-ecosystem compatibility" in paper_blob
            else "fail",
            "evidence": "Current paper/docs use fixed-session drilldown as the evaluated baseline and leave real span-tree imports for future ecosystem baselines.",
        },
    ]
    return checks


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def markdown_table(rows: list[dict[str, str]]) -> str:
    lines = [
        "| Core experiment | Workload | Key evidence | Scoped conclusion |",
        "|---|---|---|---|",
    ]
    for row in rows:
        lines.append(
            "| "
            + " | ".join(
                [
                    row["core_experiment"],
                    row["workload"],
                    row["evidence"],
                    row["conclusion"],
                ]
            ).replace("\n", " ")
            + " |"
        )
    return "\n".join(lines)


def latex_table(rows: list[dict[str, str]]) -> str:
    def esc(value: str) -> str:
        return (
            value.replace("\\", "\\textbackslash{}")
            .replace("&", "\\&")
            .replace("%", "\\%")
            .replace("_", "\\_")
            .replace("#", "\\#")
        )

    lines = [
        "% Generated by script/paper_core_result_tables.py (R360).",
        "\\begin{tabular}{p{0.18\\linewidth}p{0.22\\linewidth}p{0.34\\linewidth}p{0.20\\linewidth}}",
        "  \\toprule",
        "  Core experiment & Workload & Key generated evidence & Scoped conclusion \\\\",
        "  \\midrule",
    ]
    for row in rows:
        lines.append(
            "  "
            + " & ".join(
                [
                    esc(row["core_experiment"]),
                    esc(row["workload"]),
                    esc(row["evidence"]),
                    esc(row["conclusion"]),
                ]
            )
            + " \\\\"
        )
    lines.extend(["  \\bottomrule", "\\end{tabular}", ""])
    return "\n".join(lines)


def write_markdown(path: Path, payload: dict[str, Any]) -> None:
    lines = [
        "# R360 Paper Core Result Tables",
        "",
        f"- Status: `{payload['status']}`.",
        f"- Checks: {payload['summary']['checks_passed']}/{payload['summary']['checks_total']}.",
        "- This is a table-consolidation gate, not a new empirical result.",
        "",
        "## Core Table",
        "",
        markdown_table(payload["experiments"]),
        "",
        "## Checks",
        "",
        "| Check | Status | Evidence |",
        "|---|---|---|",
    ]
    for check in payload["checks"]:
        lines.append(f"| `{check['check']}` | {check['status']} | {check['evidence']} |")
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def write_html(path: Path, payload: dict[str, Any]) -> None:
    table_rows = "\n".join(
        "<tr>"
        f"<td>{html.escape(row['core_experiment'])}</td>"
        f"<td>{html.escape(row['workload'])}</td>"
        f"<td>{html.escape(row['evidence'])}</td>"
        f"<td>{html.escape(row['conclusion'])}</td>"
        "</tr>"
        for row in payload["experiments"]
    )
    check_rows = "\n".join(
        "<tr>"
        f"<td>{html.escape(check['check'])}</td>"
        f"<td>{html.escape(check['status'])}</td>"
        f"<td>{html.escape(check['evidence'])}</td>"
        "</tr>"
        for check in payload["checks"]
    )
    path.write_text(
        f"""<!doctype html>
<html>
<head>
<meta charset=\"utf-8\">
<title>R360 Paper Core Result Tables</title>
<style>
body {{ font-family: system-ui, sans-serif; margin: 2rem; line-height: 1.45; }}
table {{ border-collapse: collapse; width: 100%; margin: 1rem 0; }}
th, td {{ border: 1px solid #ddd; padding: 0.45rem; vertical-align: top; }}
th {{ background: #f5f5f5; text-align: left; }}
</style>
</head>
<body>
<h1>R360 Paper Core Result Tables</h1>
<p>Status: <code>{html.escape(payload['status'])}</code>;
checks: {payload['summary']['checks_passed']}/{payload['summary']['checks_total']}.</p>
<h2>Core Experiments</h2>
<table>
<tr><th>Core experiment</th><th>Workload</th><th>Evidence</th><th>Conclusion</th></tr>
{table_rows}
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
    start = time.time()
    out_dir.mkdir(parents=True, exist_ok=True)

    data = {name: read_json(path) for name, path in SOURCES.items()}
    metrics = metric_rows(data)
    experiments = experiment_rows(metrics)
    checks = build_checks(data, metrics, experiments)
    status = "pass" if all(check["status"] == "pass" for check in checks) else "fail"

    payload = {
        "run_id": RUN_ID,
        "schema": "agentsight.paper-core-result-tables.v1",
        "status": status,
        "commit": git_commit(),
        "input_policy": {
            "dataset_creation": "none",
            "dataset_relabeling": "none",
            "dataset_sync": "none",
            "network_access_required": False,
            "profiler_rerun": False,
            "hidden_label_use": "only through already-scored upstream artifacts",
        },
        "not_new_empirical_result": True,
        "not_a_human_study_result": True,
        "not_an_agent_analyst_task_result": True,
        "profiler_abstractions": ["operation", "operation stack"],
        "summary": {
            "checks_passed": sum(1 for check in checks if check["status"] == "pass"),
            "checks_total": len(checks),
            "core_experiments": 4,
            "metrics": len(metrics),
            "status": status,
        },
        "experiments": experiments,
        "metrics": metrics,
        "checks": checks,
        "source_status": source_rows(),
        "elapsed_s": round(time.time() - start, 3),
    }

    write_csv(
        out_dir / "core-result-metrics.csv",
        metrics,
        ["experiment", "metric", "value", "baseline_or_comparator", "evidence"],
    )
    write_csv(
        out_dir / "core-result-experiments.csv",
        experiments,
        ["core_experiment", "claim", "workload", "evidence", "conclusion"],
    )
    write_csv(out_dir / "core-result-checks.csv", checks, ["check", "status", "evidence"])
    write_csv(out_dir / "source-status.csv", payload["source_status"], ["source", "path", "status", "sha256"])
    (out_dir / "core-result-tables.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (out_dir / "paper-table.tex").write_text(latex_table(experiments), encoding="utf-8")
    write_markdown(out_dir / "core-result-tables.md", payload)
    write_html(out_dir / "index.html", payload)
    (out_dir / "run-result.json").write_text(
        json.dumps(
            {
                "run_id": RUN_ID,
                "status": status,
                "checks_passed": payload["summary"]["checks_passed"],
                "checks_total": payload["summary"]["checks_total"],
                "report": rel(out_dir / "core-result-tables.json"),
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "run_id": RUN_ID,
                "status": status,
                "checks_passed": payload["summary"]["checks_passed"],
                "checks_total": payload["summary"]["checks_total"],
                "report": rel(out_dir / "core-result-tables.json"),
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if status == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
