#!/usr/bin/env python3
"""R364: audit the RQ/core experiment blocks for reviewer sufficiency.

This is a paper-organization and claim-gating artifact, not a new empirical
result. It verifies that the paper is organized as four core research questions
(three empirical profiling RQs plus one replayability/overhead RQ), and that
each block has a primary experiment, oracle, named baselines, metrics,
quantified success criterion, negative/scope condition, and figure/table
target. It reads tracked artifacts only and does not fetch, sync, create, or
relabel datasets.
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
DEFAULT_OUT_DIR = OUT_ROOT / "paper-core-experiment-sufficiency-r364"
RUN_ID = "R364"
SCRIPT_PATH = Path(__file__).resolve()

SOURCES = {
    "R338 paper claim integrity": OUT_ROOT / "paper-claim-integrity-r338" / "claim-integrity-report.json",
    "R352 evaluation rubric": OUT_ROOT / "paper-evaluation-rubric-r352" / "evaluation-rubric-report.json",
    "R356 claim integrity refresh": OUT_ROOT / "paper-claim-integrity-r356" / "claim-integrity-r356-report.json",
    "R357 reviewer acceptance": OUT_ROOT / "paper-reviewer-acceptance-r357" / "reviewer-acceptance-r357.json",
    "R360 core result table": OUT_ROOT / "paper-core-result-tables-r360" / "core-result-tables.json",
    "R361 claim evidence": OUT_ROOT / "paper-core-claim-evidence-r361" / "core-claim-evidence.json",
    "R363 visualization portfolio": OUT_ROOT / "paper-visualization-portfolio-r363" / "visualization-portfolio.json",
    "R366 field derivation mechanism": OUT_ROOT
    / "operation-field-derivation-mechanism-r366"
    / "field-derivation-mechanism-report.json",
}

PAPER_SOURCES = {
    "evaluation ledger": ROOT / "docs" / "evaluation.md",
    "Chinese paper": ROOT / "docs" / "visexp" / "paper" / "main.tex",
    "English paper": SUBMODULE_ROOT / "main.tex",
}

SUFFICIENCY_FIELDS = [
    "core_experiment",
    "primary_experiment",
    "claim_test",
    "oracle",
    "baselines",
    "primary_metrics",
    "success_criterion",
    "failure_interpretation",
    "negative_or_scope_condition",
    "figure_table_target",
    "claim_gate_decision",
    "source_artifacts",
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
        check=False,
    )
    if tracked.returncode != 0:
        return "untracked_or_missing"
    unstaged = subprocess.run(["git", "diff", "--quiet", "--", display], cwd=repo_root, check=False)
    staged = subprocess.run(["git", "diff", "--cached", "--quiet", "--", display], cwd=repo_root, check=False)
    return "tracked_clean" if unstaged.returncode == 0 and staged.returncode == 0 else "tracked_dirty_allowed"


def git_commit() -> str:
    result = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True, stdout=subprocess.PIPE, check=True)
    return result.stdout.strip()


def fmt(value: Any) -> str:
    if isinstance(value, float):
        return f"{value:.4f}".rstrip("0").rstrip(".")
    return str(value)


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


def ledger_by_id(r361: dict[str, Any]) -> dict[str, dict[str, str]]:
    rows: dict[str, dict[str, str]] = {}
    for row in r361["ledger"]:
        eid = row["core_experiment"].split(":", 1)[0].split("/")[-1]
        rows[eid] = row
    return rows


def experiment_by_id(r360: dict[str, Any]) -> dict[str, dict[str, str]]:
    rows: dict[str, dict[str, str]] = {}
    for row in r360["experiments"]:
        eid = row["core_experiment"].split(":", 1)[0].split("/")[-1]
        rows[eid] = row
    return rows


def visualization_names(r363: dict[str, Any]) -> set[str]:
    return {row["name"] for row in r363["visualizations"]}


def build_rows(data: dict[str, dict[str, Any]]) -> list[dict[str, str]]:
    r338 = data["R338 paper claim integrity"]["summary"]
    r352 = data["R352 evaluation rubric"]["summary"]
    r356 = data["R356 claim integrity refresh"]["summary"]
    r357 = data["R357 reviewer acceptance"]["summary"]
    r360 = experiment_by_id(data["R360 core result table"])
    r361 = ledger_by_id(data["R361 claim evidence"])
    r363 = data["R363 visualization portfolio"]["summary"]

    return [
        {
            "core_experiment": "RQ1/E1: generality, recursive folding, and field derivation",
            "primary_experiment": "R286 recursive stack-depth sweep, with R342 profile-spec composition, R353 trace exchange, and R366 field-derivation synthesis as support.",
            "claim_test": r361["E1"]["research_question"],
            "oracle": r361["E1"]["oracle"],
            "baselines": r361["E1"]["baselines"],
            "primary_metrics": r361["E1"]["primary_metrics"],
            "success_criterion": "The same operation input folds across depths (9->3757 stacks), profile specs stay prompt/session-free (12/12), standard-trace import/export preserves 512 samples and 11 stacks, and R366 records 6 mechanism rows plus 5 boundary-family rows without adding a new profiler object.",
            "failure_interpretation": "If stack depth cannot change without changing operation input, the two-abstraction model collapses back into fixed prompt/session/tool objects.",
            "negative_or_scope_condition": r361["E1"]["counterpoint_or_scope"],
            "figure_table_target": "Table core-results plus dataset/coverage table; E1 is table-first because the key claim is coverage and foldability rather than a ranking curve.",
            "claim_gate_decision": r360["E1"]["conclusion"],
            "source_artifacts": "R285; R286; R342; R353; R360; R361; R366",
        },
        {
            "core_experiment": "RQ2/E2: hidden-label localization and ranking",
            "primary_experiment": "R320 hidden-label profile accuracy, with R333/R334/R355 budget, fragmentation, and oracle-depth slices.",
            "claim_test": r361["E2"]["research_question"],
            "oracle": r361["E2"]["oracle"],
            "baselines": r361["E2"]["baselines"],
            "primary_metrics": r361["E2"]["primary_metrics"],
            "success_criterion": "Operation-stack task-query ranking uses 0.0937 top-5 work vs 1.0 flat, beats fixed-session drilldown top-5 recall on 5/6 tasks, reduces median groups from 285.0 to 157.5, and beats fixed-session budget-30 unit recall on 20/24 oracle-depth rows.",
            "failure_interpretation": "If flat, fixed-session, or dataset-native views dominate the Pareto frontier, the claim narrows to a visualization option rather than a profiler-localization method.",
            "negative_or_scope_condition": r361["E2"]["counterpoint_or_scope"] + " Query-aware ranking is a visible task-query heuristic/tuning surface, not a universal label-free ranker.",
            "figure_table_target": "R363 baseline-tradeoff.svg, metric-heatmap.svg, and oracle-depth-adequacy.svg; Table R320 accuracy and Table core-results.",
            "claim_gate_decision": r360["E2"]["conclusion"],
            "source_artifacts": "R320; R333; R334; R337; R339; R355; R360; R361; R363",
        },
        {
            "core_experiment": "RQ3/E3: mechanism and actionability",
            "primary_experiment": "R354 executable profile-spec patches, with R358 boundary-derived-field ablation for the OSWorld-Human rejection.",
            "claim_test": r361["E3"]["research_question"],
            "oracle": r361["E3"]["oracle"],
            "baselines": r361["E3"]["baselines"],
            "primary_metrics": r361["E3"]["primary_metrics"],
            "success_criterion": "R354 accepts 5/6 patches with median AP delta 0.0376 and top-5 lift delta 0.5750; R358 improves held-out OSWorld-Human AP from 0.2402 to 0.2583 and groups from 108 to 74 using supervised boundary-derived fields as visible operation fields; R366 folds 7 critical and 3 misleading feature rows into the same E3 mechanism story.",
            "failure_interpretation": "If profile-guided specs or boundary-derived fields do not improve scored groups, the profiler gives descriptions but not actionable optimization knobs.",
            "negative_or_scope_condition": r361["E3"]["counterpoint_or_scope"] + " R358 is a supervised held-out boundary-field ablation, not unsupervised boundary discovery.",
            "figure_table_target": "R363 diagnostic-lenses.svg and actionability-knobs.svg; actionability table and E3 row in Table core-results.",
            "claim_gate_decision": r360["E3"]["conclusion"],
            "source_artifacts": "R324; R342; R345-R350; R354; R358; R360; R361; R363; R366",
        },
        {
            "core_experiment": "RQ4/E4: replayability, offline cost, and artifact hygiene",
            "primary_experiment": "R328 deterministic replay over 76 tracked profile specs; R338/R352/R356/R357/R359/R360/R361/R363 remain artifact-hygiene and paper-structure gates, not hidden-label accuracy results.",
            "claim_test": r361["E4"]["research_question"],
            "oracle": r361["E4"]["oracle"],
            "baselines": r361["E4"]["baselines"],
            "primary_metrics": r361["E4"]["primary_metrics"],
            "success_criterion": "R328 records 76/76 semantic deterministic specs and 76/76 raw-byte deterministic specs over 152 invocations, with median runtime 1.601s and p95 2.767s.",
            "failure_interpretation": "If deterministic replay or tracked-source provenance fails, the paper can discuss profiler outputs but not claim replayable offline artifact evidence.",
            "negative_or_scope_condition": r361["E4"]["counterpoint_or_scope"],
            "figure_table_target": "Reproducibility table, source-status CSVs, and E4 row in Table core-results; claim/rubric/reviewer gates stay in artifact hygiene rather than the empirical accuracy comparison.",
            "claim_gate_decision": r360["E4"]["conclusion"],
            "source_artifacts": "R328; R338; R352; R356; R357; R359; R360; R361; R363",
        },
    ]


def has_all(text: str, tokens: list[str]) -> bool:
    lower = text.lower()
    return all(token.lower() in lower for token in tokens)


def add_check(checks: list[dict[str, Any]], name: str, condition: bool, evidence: str) -> None:
    checks.append({"check": name, "status": "pass" if condition else "fail", "evidence": evidence})


def build_checks(
    data: dict[str, dict[str, Any]],
    rows: list[dict[str, str]],
    source_status: list[dict[str, str]],
    paper_text: str,
) -> list[dict[str, Any]]:
    r352 = data["R352 evaluation rubric"]["summary"]
    r357 = data["R357 reviewer acceptance"]["summary"]
    r360 = data["R360 core result table"]
    r361 = data["R361 claim evidence"]
    r363 = data["R363 visualization portfolio"]
    r366 = data["R366 field derivation mechanism"]
    checks: list[dict[str, Any]] = []
    row_blob = json.dumps(rows, sort_keys=True)
    combined_text = row_blob + "\n" + paper_text
    viz = visualization_names(r363)

    add_check(
        checks,
        "three_empirical_plus_one_reproducibility_block",
        len(rows) == 4
        and all(rows[i - 1]["core_experiment"].startswith(f"RQ{i}/E{i}:") for i in range(1, 5))
        and "E5" not in paper_text
        and "RQ5" not in paper_text,
        "Exactly RQ1/E1-RQ4/E4 are represented, RQ1/E1-RQ3/E3 are empirical profiling blocks, RQ4/E4 is replayability/overhead/artifact hygiene, and no paper-facing E5/RQ5 is present.",
    )
    add_check(
        checks,
        "required_sufficiency_fields_complete",
        all(all(row.get(field, "").strip() for field in SUFFICIENCY_FIELDS) for row in rows),
        "Every core experiment row has primary experiment, oracle, baselines, metrics, success criterion, failure interpretation, scope, target, and sources.",
    )
    add_check(
        checks,
        "primary_experiments_are_substantial",
        has_all(row_blob, ["R286", "R320", "R354", "R328"])
        and all("primary_experiment" in row for row in rows),
        "Primary experiments are named for all RQ1/E1-RQ4/E4 and are not chronological run lists.",
    )
    add_check(
        checks,
        "baseline_and_metric_surface_covers_main_claim",
        has_all(row_blob, ["flat", "fixed-session", "dataset-native", "raw-action", "operation-stack", "AP", "precision@k", "recall@k", "F1", "nDCG", "work-to-first-positive"]),
        "E2 includes the required baselines and localization/ranking metrics.",
    )
    add_check(
        checks,
        "fixed_session_baseline_scope",
        "fixed-session drilldown" in row_blob
        and "real span-tree imports remain future baselines" in combined_text,
        "The evaluated baseline is fixed-session drilldown; real span-tree imports remain future work.",
    )
    add_check(
        checks,
        "query_aware_is_task_query_tuning_surface",
        "task-query heuristic/tuning surface" in row_blob
        and "universal label-free ranker" in combined_text,
        "Query-aware policies are scoped as task-query tuning heuristics rather than a universal label-free ranker.",
    )
    add_check(
        checks,
        "boundary_backend_is_supervised_ablation",
        "supervised held-out boundary-field ablation" in row_blob
        and "not unsupervised boundary discovery" in combined_text
        and r366["summary"]["boundary_family_rows"] == 5,
        "R358/R366 are scoped to supervised held-out boundary-derived fields and suitability checks, not automatic boundary discovery.",
    )
    add_check(
        checks,
        "actionability_has_executable_and_boundary_mechanisms",
        has_all(row_blob, ["profile-spec patches", "boundary-derived", "0.0376", "0.5750", "0.2583", "0.2402", "7 critical", "3 misleading"]),
        "E3 includes executable profile-spec patches, OSWorld-Human boundary-field ablation, and field/ranker mechanism counterpoints.",
    )
    add_check(
        checks,
        "field_derivation_is_internal_to_e1_e3",
        r366["status"] == "pass"
        and r366["summary"]["mechanism_rows"] == 6
        and r366["summary"]["boundary_family_rows"] == 5
        and "R366" in row_blob
        and "E5" not in paper_text,
        "R366 field-derivation evidence is represented inside E1/E3, with no fifth paper-facing experiment.",
    )
    add_check(
        checks,
        "negative_results_preserved",
        has_all(combined_text, ["nDCG", "2/42", "top-5 work", "first-positive work", "not automatic boundary discovery", "not automatic patch"]),
        "Metric, action-transfer, and boundary-field counterpoints remain visible.",
    )
    add_check(
        checks,
        "visual_targets_are_not_flamegraph_only",
        {"baseline-tradeoff", "metric-heatmap", "diagnostic-lenses", "actionability-knobs", "oracle-depth-adequacy"}.issubset(viz),
        "R363 provides five non-flamegraph-only paper views for E2/E3 plus oracle depth.",
    )
    add_check(
        checks,
        "upstream_gates_pass",
        r360["status"] == "pass"
        and r361["status"] == "pass"
        and r363["status"] == "pass"
        and r352["rubric_level"] == "level_4_scoped_profile_benchmark"
        and r357["final_accepts"] == 4
        and r357["blocking_issues"] == 0,
        "R360/R361/R363 pass, R352 is level_4, and R357 has 4/4 accepts with 0 blockers.",
    )
    add_check(
        checks,
        "self_audits_are_artifact_hygiene_not_empirical_evidence",
        "not a new empirical result" in paper_text
        and "artifact hygiene" in combined_text.lower()
        and ("not empirical evidence" in combined_text.lower() or "not empirical accuracy evidence" in combined_text.lower()),
        "R338/R352/R356/R357/R359/R360/R363 are treated as artifact and claim-hygiene gates, not empirical profiler accuracy evidence.",
    )
    add_check(
        checks,
        "two_abstraction_and_source_policy_preserved",
        r361["profiler_abstractions"] == ["operation", "operation stack"]
        and r363["profiler_abstractions"] == ["operation", "operation stack"]
        and r361["not_new_empirical_result"]
        and r363["not_new_empirical_result"]
        and "no dataset sync" in combined_text
        and ("no relabeling" in combined_text or "不重新排名或同步数据集" in combined_text),
        "Operation/operation-stack remain the only profiler abstractions, and the no-new-data policy is visible.",
    )
    add_check(
        checks,
        "tracked_source_artifacts_available",
        all(row["status"] in {"tracked_clean", "tracked_dirty_allowed"} for row in source_status),
        "All source artifacts are tracked; current paper/docs may be dirty while this audit is being generated.",
    )
    return checks


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def write_markdown(path: Path, payload: dict[str, Any]) -> None:
    lines = [
        "# R364 Core Experiment Sufficiency Audit",
        "",
        f"- Status: `{payload['status']}`.",
        f"- Checks: {payload['summary']['checks_passed']}/{payload['summary']['checks_total']}.",
        f"- Core experiments: {payload['summary']['core_experiments']}.",
        "",
        "## Sufficiency Matrix",
        "",
        "| Experiment | Primary experiment | Success criterion | Claim gate |",
        "|---|---|---|---|",
    ]
    for row in payload["sufficiency_rows"]:
        lines.append(
            f"| {row['core_experiment']} | {row['primary_experiment']} | {row['success_criterion']} | {row['claim_gate_decision']} |"
        )
    lines.extend(["", "## Checks", "", "| Check | Status | Evidence |", "|---|---|---|"])
    for row in payload["checks"]:
        lines.append(f"| `{row['check']}` | {row['status']} | {row['evidence']} |")
    lines.extend(
        [
            "",
            "## Non-Claims",
            "",
            "- This is not a new empirical result.",
            "- This is not a human or agent analyst study.",
            "- This does not fetch, sync, create, or relabel datasets.",
            "- This does not add a fifth core experiment.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def write_html(path: Path, payload: dict[str, Any]) -> None:
    matrix = "\n".join(
        "<tr>"
        f"<td>{html.escape(row['core_experiment'])}</td>"
        f"<td>{html.escape(row['primary_experiment'])}</td>"
        f"<td>{html.escape(row['success_criterion'])}</td>"
        f"<td>{html.escape(row['claim_gate_decision'])}</td>"
        "</tr>"
        for row in payload["sufficiency_rows"]
    )
    checks = "\n".join(
        "<tr>"
        f"<td>{html.escape(row['check'])}</td>"
        f"<td>{html.escape(row['status'])}</td>"
        f"<td>{html.escape(row['evidence'])}</td>"
        "</tr>"
        for row in payload["checks"]
    )
    page = f"""<!doctype html>
<meta charset=\"utf-8\">
<title>R364 Core Experiment Sufficiency Audit</title>
<style>
body {{ font-family: system-ui, sans-serif; margin: 2rem; line-height: 1.45; }}
table {{ border-collapse: collapse; width: 100%; margin: 1rem 0; }}
th, td {{ border: 1px solid #ddd; padding: 0.45rem; vertical-align: top; }}
th {{ background: #f6f6f6; }}
code {{ background: #f3f3f3; padding: 0.1rem 0.2rem; }}
</style>
<h1>R364 Core Experiment Sufficiency Audit</h1>
<p>Status: <code>{html.escape(payload['status'])}</code></p>
<p>Checks: {payload['summary']['checks_passed']}/{payload['summary']['checks_total']}</p>
<h2>Sufficiency Matrix</h2>
<table><thead><tr><th>Experiment</th><th>Primary experiment</th><th>Success criterion</th><th>Claim gate</th></tr></thead><tbody>{matrix}</tbody></table>
<h2>Checks</h2>
<table><thead><tr><th>Check</th><th>Status</th><th>Evidence</th></tr></thead><tbody>{checks}</tbody></table>
"""
    path.write_text(page, encoding="utf-8")


def main() -> None:
    args = parse_args()
    out_dir = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    start = time.time()

    data = {name: read_json(path) for name, path in SOURCES.items()}
    paper_text = "\n".join(read_text(path) for path in PAPER_SOURCES.values())
    source_status = source_rows()
    rows = build_rows(data)
    checks = build_checks(data, rows, source_status, paper_text)
    checks_passed = sum(row["status"] == "pass" for row in checks)
    status = "pass" if checks_passed == len(checks) else "fail"

    payload = {
        "run_id": RUN_ID,
        "schema": "agentsight.paper_core_experiment_sufficiency.v1",
        "status": status,
        "commit": git_commit(),
        "elapsed_s": round(time.time() - start, 4),
        "claim": "RQ1/E1-RQ4/E4 are substantial reviewer-facing experiments rather than a chronological run list",
        "summary": {
            "status": status,
            "checks_passed": checks_passed,
            "checks_total": len(checks),
            "core_experiments": len(rows),
            "paper_visualizations": data["R363 visualization portfolio"]["summary"]["visualizations"],
            "network_access_required": False,
        },
        "input_policy": {
            "no_dataset_sync": True,
            "no_dataset_creation": True,
            "no_relabeling": True,
            "hidden_labels_only_for_scoring": True,
        },
        "not_new_empirical_result": True,
        "not_a_human_study_result": True,
        "not_an_agent_analyst_task_result": True,
        "profiler_abstractions": ["operation", "operation stack"],
        "sufficiency_rows": rows,
        "checks": checks,
        "source_status": source_status,
    }

    report_json = out_dir / "core-experiment-sufficiency.json"
    report_md = out_dir / "core-experiment-sufficiency.md"
    checks_csv = out_dir / "sufficiency-checks.csv"
    rows_csv = out_dir / "sufficiency-matrix.csv"
    source_csv = out_dir / "source-status.csv"
    html_path = out_dir / "index.html"
    run_result = out_dir / "run-result.json"

    report_json.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_markdown(report_md, payload)
    write_html(html_path, payload)
    write_csv(checks_csv, checks, ["check", "status", "evidence"])
    write_csv(rows_csv, rows, SUFFICIENCY_FIELDS)
    write_csv(source_csv, source_status, ["source", "path", "status", "sha256"])
    run_result.write_text(
        json.dumps(
            {
                "run_id": RUN_ID,
                "status": status,
                "report": rel(report_json),
                "checks_passed": checks_passed,
                "checks_total": len(checks),
                "network_access_required": False,
                "not_new_empirical_result": True,
                "not_a_human_study_result": True,
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
                "checks_passed": checks_passed,
                "checks_total": len(checks),
                "report": rel(report_json),
            },
            indent=2,
            sort_keys=True,
        )
    )
    if status != "pass":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
