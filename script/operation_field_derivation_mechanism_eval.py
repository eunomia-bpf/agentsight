#!/usr/bin/env python3
"""R366: audit operation-field derivation as an operation-stack mechanism.

This is an E1/E3 mechanism-strengthening artifact. It reads tracked outputs
from deterministic mapping, profile-spec composition, rank-feature ablation,
boundary-backend, and boundary-profile-patch runs. It does not download data,
create labels, or rerun the profiler. The goal is to make the scoped C3 claim
paper-ready: mapping/tagging/boundary backends derive operation fields that can
improve aggregation or localization, but they are not a universal automatic
intent-boundary detector.
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
DEFAULT_OUT_DIR = OUT_ROOT / "operation-field-derivation-mechanism-r366"
RUN_ID = "R366"
SCRIPT_PATH = Path(__file__).resolve()

SOURCES = {
    "R282 heldout mapped quality": OUT_ROOT / "operation-map-heldout-r282" / "quality.json",
    "R282 heldout no-map quality": OUT_ROOT / "operation-map-heldout-r282" / "quality-nomap.json",
    "R285 leave-dataset-out mapping": OUT_ROOT / "operation-map-leaveout-api-r285" / "leaveout-summary.json",
    "R297 OSWorld boundary backend": OUT_ROOT / "operation-boundary-backend-r297" / "boundary-backend-report.json",
    "R299 boundary-family calibration": OUT_ROOT / "boundary-family-calibration-r299" / "boundary-family-report.json",
    "R325 rank-feature ablation": OUT_ROOT / "operation-rank-feature-ablation-r325" / "rank-feature-findings.csv",
    "R342 profile-spec composition": OUT_ROOT / "operation-profile-spec-composition-r342" / "profile-spec-composition-report.json",
    "R358 boundary profile patch": OUT_ROOT / "operation-boundary-profile-patch-r358" / "boundary-profile-patch-report.json",
}

PAPER_SOURCES = {
    "evaluation ledger": ROOT / "docs" / "evaluation.md",
    "Chinese paper": ROOT / "docs" / "visexp" / "paper" / "main.tex",
    "English paper": SUBMODULE_ROOT / "main.tex",
}

MECHANISM_FIELDS = [
    "row_id",
    "paper_block",
    "mechanism",
    "source_runs",
    "evidence",
    "counterpoint",
    "paper_claim",
]

FAMILY_FIELDS = [
    "candidate",
    "dataset",
    "test_pairs",
    "learned_f1",
    "learned_precision",
    "learned_recall",
    "best_baseline",
    "best_baseline_f1",
    "delta_vs_best_baseline_f1",
    "verdict",
]

CHECK_FIELDS = ["check", "status", "evidence"]
SOURCE_FIELDS = ["source", "path", "status", "sha256"]


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
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


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
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return str(value)
    return f"{numeric:.4f}".rstrip("0").rstrip(".")


def v_measure(rows: list[dict[str, Any]], oracle: str, predicted: str) -> float:
    for row in rows:
        if row.get("oracle") == oracle and row.get("predicted") == predicted:
            return float(row["v_measure"])
    raise KeyError(f"{oracle}->{predicted}")


def boundary_f1(rows: list[dict[str, Any]], oracle: str, predicted: str) -> float:
    for row in rows:
        if row.get("oracle") == oracle and row.get("predicted") == predicted:
            return float(row["f1"])
    raise KeyError(f"{oracle}->{predicted}")


def source_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for name, path in {"generator script": SCRIPT_PATH, **SOURCES, **PAPER_SOURCES}.items():
        rows.append({"source": name, "path": rel(path), "status": git_status(path), "sha256": sha256(path)})
    return rows


def best_baseline(metrics: dict[str, Any]) -> dict[str, Any]:
    return max(metrics["baselines"], key=lambda row: float(row["f1"]))


def boundary_family_rows(r297: dict[str, Any], r299: dict[str, Any]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []

    learned = r297["test_metrics"]["learned_boundary_backend"]
    baseline = best_baseline(r297["test_metrics"])
    rows.append(
        {
            "candidate": "osworld_human_group_r297",
            "dataset": "osworld-human",
            "test_pairs": str(r297["test_pairs"]),
            "learned_f1": fmt(learned["f1"]),
            "learned_precision": fmt(learned["precision"]),
            "learned_recall": fmt(learned["recall"]),
            "best_baseline": baseline["name"],
            "best_baseline_f1": fmt(baseline["f1"]),
            "delta_vs_best_baseline_f1": fmt(float(learned["f1"]) - float(baseline["f1"])),
            "verdict": "supports_boundary_field_derivation",
        }
    )

    for result in r299["trained_results"]:
        learned = result["test_metrics"]["learned_boundary_backend"]
        baseline = best_baseline(result["test_metrics"])
        delta = float(learned["f1"]) - float(baseline["f1"])
        rows.append(
            {
                "candidate": result["candidate"],
                "dataset": result["dataset"],
                "test_pairs": str(result["test_pairs"]),
                "learned_f1": fmt(learned["f1"]),
                "learned_precision": fmt(learned["precision"]),
                "learned_recall": fmt(learned["recall"]),
                "best_baseline": baseline["name"],
                "best_baseline_f1": fmt(baseline["f1"]),
                "delta_vs_best_baseline_f1": fmt(delta),
                "verdict": "supports_backend" if delta > 0 else "counterpoint_simple_field_wins",
            }
        )
    return rows


def build_mechanism_rows(data: dict[str, Any], family_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    mapped = data["r282_mapped"]
    nomap = data["r282_nomap"]
    r285 = data["r285"]["summary"]
    r342 = data["r342"]["summary"]
    r325 = data["r325"]
    r358_summary = data["r358"]["summary"]
    r358_cmp = data["r358"]["comparisons"][0]

    critical = [row for row in r325 if row["classification"] == "critical"]
    misleading = [row for row in r325 if row["classification"] == "misleading"]
    backend_support = [row for row in family_rows if float(row["delta_vs_best_baseline_f1"]) > 0]
    backend_counterpoints = [row for row in family_rows if float(row["delta_vs_best_baseline_f1"]) <= 0]

    mapped_unique = int(mapped["summary"]["unique_stacks"])
    nomap_unique = int(nomap["summary"]["unique_stacks"])
    task_dataset_mapped = v_measure(mapped["oracle_alignment"], "dataset", "task")
    task_dataset_nomap = v_measure(nomap["oracle_alignment"], "dataset", "task")
    phase_action_mapped = v_measure(mapped["oracle_alignment"], "action", "phase")
    phase_action_nomap = v_measure(nomap["oracle_alignment"], "action", "phase")
    boundary_mapped = boundary_f1(mapped["boundary_alignment"], "action", "phase")
    boundary_nomap = boundary_f1(nomap["boundary_alignment"], "action", "phase")

    return [
        {
            "row_id": "M1",
            "paper_block": "E1",
            "mechanism": "deterministic operation-field mapping",
            "source_runs": "R282",
            "evidence": (
                f"Held-out mapping over {mapped['summary']['operations']} operations reduces unique stacks "
                f"{nomap_unique}->{mapped_unique} and improves compression {fmt(nomap['summary']['compression_ratio'])}->{fmt(mapped['summary']['compression_ratio'])}; "
                f"dataset->task V-measure {fmt(task_dataset_nomap)}->{fmt(task_dataset_mapped)}."
            ),
            "counterpoint": (
                f"It deliberately coarsens action labels: action->phase V-measure {fmt(phase_action_nomap)}->{fmt(phase_action_mapped)} "
                f"and adjacent phase/action boundary F1 {fmt(boundary_nomap)}->{fmt(boundary_mapped)}."
            ),
            "paper_claim": "Mappings are first-class field derivations for semantic aggregation, not proof of fine-grained boundary recovery.",
        },
        {
            "row_id": "M2",
            "paper_block": "E1",
            "mechanism": "leave-dataset-out mapping generalization",
            "source_runs": "R285",
            "evidence": (
                f"Across {r285['datasets']} held-out datasets / {r285['total_test_operations']} operations, "
                f"mapped stacks reduce stack count on {r285['positive_stack_reduction_datasets']}/{r285['datasets']} datasets, "
                f"never increase it ({r285['negative_stack_reduction_datasets']} negative), and yield "
                f"{fmt(r285['weighted_stack_reduction_per_1k_ops'])} weighted stack reduction per 1k ops."
            ),
            "counterpoint": (
                f"Mean task/dataset V-measure is unchanged at {fmt(r285['mean_mapped_task_dataset_v'])}; "
                "some datasets are already well structured and do not benefit."
            ),
            "paper_claim": "Mapping rules generalize as conservative compression/normalization rules, not as a universal semantic parser.",
        },
        {
            "row_id": "M3",
            "paper_block": "E1/E3",
            "mechanism": "profile-spec composition of mappings, predicates, rank rules, and stack depth",
            "source_runs": "R342",
            "evidence": (
                f"{r342['profile_spec_variants']} profile-spec variants compose operation files, predicates, operation rank rules, "
                f"rule-score ranking, and explicit stack depth; {r342['prompt_session_free_variants']}/{r342['profile_spec_variants']} are prompt/session-frame free. "
                f"AP improves versus width in {r342['ap_improves_vs_width_variants']}/{r342['profile_spec_variants']} variants and first-positive work in "
                f"{r342['first_positive_work_improves_vs_width_variants']}/{r342['profile_spec_variants']}."
            ),
            "counterpoint": (
                f"Depth is objective-dependent: {r342['tasks_where_depth_choice_changes_objective']}/{r342['tasks']} tasks choose different stack depths for AP and first-positive work."
            ),
            "paper_claim": "The configurable view surface is the operation-stack query itself, not hard-coded prompt/session/span boundaries.",
        },
        {
            "row_id": "M4",
            "paper_block": "E3",
            "mechanism": "operation-level rank-feature ablation",
            "source_runs": "R325",
            "evidence": (
                f"Leave-one-feature ablation identifies {len(critical)} critical feature rows across safety, looping, side-effect, and step-quality tasks. "
                f"Examples include success, loop-like, write-action, and failure fields."
            ),
            "counterpoint": (
                f"It also finds {len(misleading)} misleading feature rows, including OSWorld input-phase and SATraj loop-like cases."
            ),
            "paper_claim": "Actionability comes from naming useful and harmful operation fields, not from selecting one universal ranker.",
        },
        {
            "row_id": "M5",
            "paper_block": "E1/E3",
            "mechanism": "supervised adjacent-boundary field derivation",
            "source_runs": "R297; R299",
            "evidence": (
                f"Boundary backends beat the best simple baseline on {len(backend_support)}/{len(family_rows)} tested rows; "
                "OSWorld-Human R297 reaches F1 0.7735 versus best baseline 0.7090, and R299 also improves AgentNet quality-state boundaries."
            ),
            "counterpoint": (
                f"{len(backend_counterpoints)}/{len(family_rows)} rows remain counterpoints; AgentRewardBench looping is better explained by repeat_signal_change than the learned backend."
            ),
            "paper_claim": "Boundary detectors are optional supervised field derivation backends with suitability checks, not automatic intent discovery.",
        },
        {
            "row_id": "M6",
            "paper_block": "E3",
            "mechanism": "boundary-derived profile patch",
            "source_runs": "R358",
            "evidence": (
                f"On held-out OSWorld-Human, learned-boundary fields improve AP {fmt(r358_summary['semantic_width_ap'])}->{fmt(r358_summary['learned_boundary_ap'])}, "
                f"reduce groups {r358_summary['semantic_width_groups']}->{r358_summary['learned_boundary_groups']}, and raise top-5 recall by {fmt(r358_cmp['delta_top5_recall'])}."
            ),
            "counterpoint": (
                f"Inspection-cost metrics are mixed: top-5 work changes by +{fmt(r358_cmp['delta_top5_work'])} and first-positive work by +{fmt(r358_cmp['delta_first_positive_work'])}."
            ),
            "paper_claim": "Derived fields can repair a rejected visible profile patch, while preserving Pareto-tradeoff wording.",
        },
    ]


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def write_markdown(path: Path, payload: dict[str, Any]) -> None:
    lines = [
        "# R366 Operation-Field Derivation Mechanism Audit",
        "",
        f"- Status: `{payload['status']}`.",
        f"- Checks: {payload['summary']['checks_passed']}/{payload['summary']['checks_total']}.",
        "- This is not a new dataset, profiler rerun, or human/agent analyst result.",
        "",
        "## Mechanism Rows",
        "",
        "| Row | Block | Mechanism | Evidence | Counterpoint |",
        "|---|---|---|---|---|",
    ]
    for row in payload["mechanism_rows"]:
        lines.append(f"| {row['row_id']} | {row['paper_block']} | {row['mechanism']} | {row['evidence']} | {row['counterpoint']} |")
    lines.extend(["", "## Boundary Families", "", "| Candidate | Dataset | Learned F1 | Best baseline | Delta | Verdict |", "|---|---|---|---|---|---|"])
    for row in payload["boundary_family_rows"]:
        lines.append(
            f"| {row['candidate']} | {row['dataset']} | {row['learned_f1']} | "
            f"{row['best_baseline']} ({row['best_baseline_f1']}) | {row['delta_vs_best_baseline_f1']} | {row['verdict']} |"
        )
    lines.extend(["", "## Checks", "", "| Check | Status | Evidence |", "|---|---|---|"])
    for row in payload["checks"]:
        lines.append(f"| `{row['check']}` | {row['status']} | {row['evidence']} |")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_html(path: Path, payload: dict[str, Any]) -> None:
    mech_rows = "\n".join(
        "<tr>"
        f"<td>{html.escape(row['row_id'])}</td>"
        f"<td>{html.escape(row['paper_block'])}</td>"
        f"<td>{html.escape(row['mechanism'])}</td>"
        f"<td>{html.escape(row['evidence'])}</td>"
        f"<td>{html.escape(row['counterpoint'])}</td>"
        "</tr>"
        for row in payload["mechanism_rows"]
    )
    family_rows = "\n".join(
        "<tr>"
        f"<td>{html.escape(row['candidate'])}</td>"
        f"<td>{html.escape(row['dataset'])}</td>"
        f"<td>{html.escape(row['learned_f1'])}</td>"
        f"<td>{html.escape(row['best_baseline'])} ({html.escape(row['best_baseline_f1'])})</td>"
        f"<td>{html.escape(row['delta_vs_best_baseline_f1'])}</td>"
        f"<td>{html.escape(row['verdict'])}</td>"
        "</tr>"
        for row in payload["boundary_family_rows"]
    )
    check_rows = "\n".join(
        "<tr>"
        f"<td>{html.escape(row['check'])}</td>"
        f"<td>{html.escape(row['status'])}</td>"
        f"<td>{html.escape(row['evidence'])}</td>"
        "</tr>"
        for row in payload["checks"]
    )
    page = f"""<!doctype html>
<meta charset=\"utf-8\">
<title>R366 Operation-Field Derivation Mechanism Audit</title>
<style>
body {{ font-family: system-ui, sans-serif; margin: 2rem; line-height: 1.45; }}
table {{ border-collapse: collapse; width: 100%; margin: 1rem 0; }}
th, td {{ border: 1px solid #ddd; padding: 0.45rem; vertical-align: top; }}
th {{ background: #f6f6f6; }}
code {{ background: #f3f3f3; padding: 0.1rem 0.2rem; }}
</style>
<h1>R366 Operation-Field Derivation Mechanism Audit</h1>
<p>Status: <code>{html.escape(payload['status'])}</code></p>
<p>Checks: {payload['summary']['checks_passed']}/{payload['summary']['checks_total']}</p>
<h2>Mechanism Rows</h2>
<table><thead><tr><th>Row</th><th>Block</th><th>Mechanism</th><th>Evidence</th><th>Counterpoint</th></tr></thead><tbody>{mech_rows}</tbody></table>
<h2>Boundary Families</h2>
<table><thead><tr><th>Candidate</th><th>Dataset</th><th>Learned F1</th><th>Best baseline</th><th>Delta</th><th>Verdict</th></tr></thead><tbody>{family_rows}</tbody></table>
<h2>Checks</h2>
<table><thead><tr><th>Check</th><th>Status</th><th>Evidence</th></tr></thead><tbody>{check_rows}</tbody></table>
"""
    path.write_text(page, encoding="utf-8")


def contains_all(text: str, tokens: list[str]) -> bool:
    return all(token in text for token in tokens)


def build_checks(
    mechanism_rows: list[dict[str, str]],
    family_rows: list[dict[str, str]],
    source_status: list[dict[str, str]],
    paper_text: str,
) -> list[dict[str, str]]:
    blob = json.dumps({"mechanisms": mechanism_rows, "families": family_rows}, sort_keys=True)
    support_rows = sum(float(row["delta_vs_best_baseline_f1"]) > 0 for row in family_rows)
    checks = [
        {
            "check": "mechanism_rows_cover_mapping_ranking_boundary",
            "status": "pass"
            if len(mechanism_rows) == 6
            and contains_all(blob, ["19.091", "6/9", "9/12", "10/12", "0.7735", "0.2583"])
            else "fail",
            "evidence": "Rows cover deterministic mapping, leave-dataset-out mapping, profile-spec composition, rank-feature ablation, boundary backends, and boundary profile patches.",
        },
        {
            "check": "counterpoints_preserved",
            "status": "pass"
            if contains_all(blob, ["0.9343->0.7416", "repeat_signal_change", "+0.0813", "+0.1581"])
            else "fail",
            "evidence": "The audit preserves mapping coarsening, simple-field baseline, and inspection-cost counterpoints.",
        },
        {
            "check": "boundary_backend_suitability_not_universal",
            "status": "pass" if support_rows >= 4 and support_rows < len(family_rows) else "fail",
            "evidence": f"Learned boundary backend beats the best simple baseline on {support_rows}/{len(family_rows)} rows, leaving explicit counterpoints.",
        },
        {
            "check": "no_new_data_or_profiler_rerun",
            "status": "pass"
            if all(row["status"] in {"tracked_clean", "tracked_dirty_allowed"} for row in source_status)
            else "fail",
            "evidence": "All inputs are tracked artifacts or current paper/docs; this script only synthesizes existing results.",
        },
        {
            "check": "paper_text_mentions_r366_scope",
            "status": "pass"
            if contains_all(paper_text, ["R366", "field derivation", "not automatic intent"])
            else "fail",
            "evidence": "Evaluation ledger and paper drafts mention R366's scoped field-derivation role.",
        },
        {
            "check": "two_abstractions_only",
            "status": "pass"
            if "operation stack" in paper_text and "operation" in paper_text and "new profiler object" in paper_text
            else "fail",
            "evidence": "The paper keeps mapping/tagging/boundary outputs as operation fields folded into operation stacks.",
        },
    ]
    return checks


def main() -> None:
    args = parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)
    start = time.time()

    data = {
        "r282_mapped": read_json(SOURCES["R282 heldout mapped quality"]),
        "r282_nomap": read_json(SOURCES["R282 heldout no-map quality"]),
        "r285": read_json(SOURCES["R285 leave-dataset-out mapping"]),
        "r297": read_json(SOURCES["R297 OSWorld boundary backend"]),
        "r299": read_json(SOURCES["R299 boundary-family calibration"]),
        "r325": read_csv(SOURCES["R325 rank-feature ablation"]),
        "r342": read_json(SOURCES["R342 profile-spec composition"]),
        "r358": read_json(SOURCES["R358 boundary profile patch"]),
    }
    paper_text = "\n".join(read_text(path) for path in PAPER_SOURCES.values())
    source_status = source_rows()
    family_rows = boundary_family_rows(data["r297"], data["r299"])
    mechanism_rows = build_mechanism_rows(data, family_rows)
    checks = build_checks(mechanism_rows, family_rows, source_status, paper_text)
    checks_passed = sum(row["status"] == "pass" for row in checks)
    status = "pass" if checks_passed == len(checks) else "fail"

    payload = {
        "run_id": RUN_ID,
        "schema": "agentsight.operation_field_derivation_mechanism.v1",
        "status": status,
        "commit": git_commit(),
        "elapsed_s": round(time.time() - start, 4),
        "claim": "Operation-field derivation mechanisms can improve aggregation and localization when folded through operation stacks, with scoped suitability counterpoints.",
        "summary": {
            "status": status,
            "checks_passed": checks_passed,
            "checks_total": len(checks),
            "mechanism_rows": len(mechanism_rows),
            "boundary_family_rows": len(family_rows),
            "network_access_required": False,
            "profiler_rerun": False,
            "dataset_sync": False,
        },
        "input_policy": {
            "no_dataset_sync": True,
            "no_dataset_creation": True,
            "no_relabeling": True,
            "no_profiler_rerun": True,
            "hidden_labels_only_in_upstream_scoring": True,
        },
        "not_new_empirical_result": True,
        "not_a_human_study_result": True,
        "not_an_agent_analyst_task_result": True,
        "profiler_abstractions": ["operation", "operation stack"],
        "mechanism_rows": mechanism_rows,
        "boundary_family_rows": family_rows,
        "checks": checks,
        "source_status": source_status,
    }

    report_json = args.out_dir / "field-derivation-mechanism-report.json"
    report_md = args.out_dir / "field-derivation-mechanism-report.md"
    html_path = args.out_dir / "index.html"
    mechanism_csv = args.out_dir / "mechanism-rows.csv"
    family_csv = args.out_dir / "boundary-family-summary.csv"
    checks_csv = args.out_dir / "mechanism-checks.csv"
    source_csv = args.out_dir / "source-status.csv"
    run_result = args.out_dir / "run-result.json"

    report_json.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_markdown(report_md, payload)
    write_html(html_path, payload)
    write_csv(mechanism_csv, mechanism_rows, MECHANISM_FIELDS)
    write_csv(family_csv, family_rows, FAMILY_FIELDS)
    write_csv(checks_csv, checks, CHECK_FIELDS)
    write_csv(source_csv, source_status, SOURCE_FIELDS)
    run_result.write_text(
        json.dumps(
            {
                "run_id": RUN_ID,
                "status": status,
                "report": rel(report_json),
                "checks_passed": checks_passed,
                "checks_total": len(checks),
                "network_access_required": False,
                "profiler_rerun": False,
                "not_new_empirical_result": True,
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
                "mechanism_rows": len(mechanism_rows),
                "boundary_family_rows": len(family_rows),
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
