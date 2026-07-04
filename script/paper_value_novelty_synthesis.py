#!/usr/bin/env python3
"""Synthesize reviewer-facing value and novelty evidence from tracked artifacts."""

from __future__ import annotations

import argparse
import html
import json
import subprocess
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OUT_ROOT = ROOT / "docs" / "visexp" / "out"
DEFAULT_OUT_DIR = OUT_ROOT / "paper-value-novelty-r298"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    return parser.parse_args()


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def load_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as file:
        return json.load(file)


def require(data: dict[str, Any], key: str, path: Path) -> Any:
    if key not in data:
        raise SystemExit(f"{rel(path)} missing key {key!r}")
    return data[key]


def run_git_check(description: str, args: list[str], path: Path) -> None:
    result = subprocess.run(
        ["git", *args, "--", rel(path)],
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip()
        suffix = f": {detail}" if detail else ""
        raise SystemExit(f"{rel(path)} failed provenance check: {description}{suffix}")


def ensure_sources_tracked_clean(paths: list[Path]) -> None:
    for path in paths:
        if not path.exists():
            raise SystemExit(f"missing source artifact {rel(path)}")
        run_git_check("source artifact is not git-tracked", ["ls-files", "--error-unmatch"], path)
        run_git_check("source artifact has unstaged changes", ["diff", "--quiet"], path)
        run_git_check("source artifact has staged changes", ["diff", "--cached", "--quiet"], path)


def top_field(path: Path, field: str, value: str) -> dict[str, Any]:
    data = load_json(path)
    for row in data.get("top_by_field", {}).get(field, []):
        if row.get("value") == value:
            return row
    raise SystemExit(f"{rel(path)} missing top_by_field.{field} value {value!r}")


def coverage(path: Path, field: str) -> dict[str, Any]:
    data = load_json(path)
    for row in data.get("coverage", []):
        if row.get("field") == field:
            return row
    raise SystemExit(f"{rel(path)} missing coverage field {field!r}")


def build_synthesis() -> dict[str, Any]:
    paths = {
        "claim_synthesis": OUT_ROOT / "paper-claim-synthesis-r295" / "claim-synthesis.json",
        "reviewer_packet": OUT_ROOT / "reviewer-evidence-packet-r296" / "reviewer-evidence.json",
        "boundary_report": OUT_ROOT
        / "operation-boundary-backend-r297"
        / "boundary-backend-report.json",
        "boundary_profile": OUT_ROOT
        / "operation-boundary-backend-r297"
        / "learned-boundary-agentpprof-result.json",
        "boundary_stack": OUT_ROOT
        / "operation-boundary-backend-r297"
        / "learned-boundary-stack-analysis.json",
        "agentreward_quality": OUT_ROOT
        / "external-agent-trace-agentreward-r288"
        / "agentreward-quality.json",
        "satraj_quality": OUT_ROOT / "external-agent-trace-satraj-r289" / "satraj-quality.json",
        "agentnet_quality": OUT_ROOT
        / "external-agent-trace-agentnet-r291"
        / "agentnet-quality.json",
    }
    ensure_sources_tracked_clean(list(paths.values()))

    claim_synthesis = load_json(paths["claim_synthesis"])
    reviewer_packet = load_json(paths["reviewer_packet"])
    boundary_report = load_json(paths["boundary_report"])
    boundary_profile = load_json(paths["boundary_profile"])
    boundary_stack = load_json(paths["boundary_stack"])

    claim_rows = require(claim_synthesis, "claims", paths["claim_synthesis"])
    derived = require(reviewer_packet, "derived_metrics", paths["reviewer_packet"])
    dataset = require(derived, "dataset_coverage", paths["reviewer_packet"])
    recursive = require(derived, "recursive_foldability", paths["reviewer_packet"])
    mapping = require(derived, "mapping_value", paths["reviewer_packet"])
    human = require(derived, "human_group_value", paths["reviewer_packet"])
    diagnostics = require(derived, "diagnostic_value", paths["reviewer_packet"])
    reproducibility = require(derived, "reproducibility_value", paths["reviewer_packet"])

    boundary_metrics = boundary_report["test_metrics"]["learned_boundary_backend"]
    boundary_baselines = {
        row["name"]: row for row in boundary_report["test_metrics"]["baselines"]
    }
    unsafe = top_field(paths["satraj_quality"], "safety", "unsafe")
    step_correct = coverage(paths["agentnet_quality"], "step_correct")
    step_redundant = coverage(paths["agentnet_quality"], "step_redundant")
    if boundary_profile.get("samples") != boundary_stack["total_weight"]:
        raise SystemExit("R297 boundary profile samples do not match stack-analysis total_weight")
    if boundary_profile.get("unique_stacks") != boundary_stack["unique_stacks"]:
        raise SystemExit("R297 boundary profile unique_stacks do not match stack analysis")

    real_problem_evidence = [
        {
            "id": "P1",
            "claim": "C1",
            "real_problem": "Agent traces mix prompts, tools, GUI actions, API calls, safety labels, and quality labels; prompt/session/span object models split these into incompatible pipelines.",
            "profiler_mechanism": "Normalize every source row into operations, then use operation stacks as query-time projections.",
            "public_oracle": "15 public labeled trajectory sources with dataset/session/task/action/quality fields.",
            "headline_evidence": f"{dataset['datasets']} datasets, {dataset['operations']} operations, {dataset['unique_stacks']} stacks in the supplemental smoke set.",
            "novelty_value": "The paper artifact under test is a two-object profiler model, not another fixed agent trace viewer.",
            "status": "supported for sampled public trajectories",
            "limitations": "Does not prove full-scale conversion of every public benchmark or image/video archive.",
            "source_paths": [
                rel(paths["claim_synthesis"]),
                rel(paths["reviewer_packet"]),
            ],
        },
        {
            "id": "P2",
            "claim": "C2",
            "real_problem": "The useful boundary depends on the debugging question; a fixed session/prompt stack either hides phase structure or fragments aggregation.",
            "profiler_mechanism": "Fold the same operations at different stack depths by changing only the stack specification.",
            "public_oracle": "R286 depth sweep and R293 AgentNet profile-spec override.",
            "headline_evidence": f"R286 folds the same {recursive['same_operations']} operations from {recursive['dataset_unique_stacks']} dataset stacks to {recursive['phase_unique_stacks']} phase, {recursive['action_unique_stacks']} action, and {recursive['fixed_session_unique_stacks']} fixed-session stacks; R293 stack override reduces AgentNet stacks by {reproducibility['profile_spec_override_reduction_percent']}%.",
            "novelty_value": "Recursive folding is a query over operation fields rather than a hard-coded prompt/session hierarchy.",
            "status": "supported with scoped limits",
            "limitations": "Does not identify one universal best stack for every task.",
            "source_paths": [rel(paths["reviewer_packet"])],
        },
        {
            "id": "P3",
            "claim": "C3",
            "real_problem": "Raw dataset labels and action names are inconsistent; without field derivation, stacks are either too shallow or too fragmented.",
            "profiler_mechanism": "Run deterministic or learned field derivation before stack construction, then fold ordinary operation fields.",
            "public_oracle": "R282 held-out mappings, R285 leave-dataset-out mappings, and R297 held-out OSWorld-Human boundary labels.",
            "headline_evidence": f"R282 mapping reduces held-out unique stacks by {mapping['unique_stack_reduction_percent']}% and improves compression by {mapping['compression_improvement_percent']}%; R285 has {mapping['leaveout_negative_folds']} negative folds; R297 supervised boundary F1 is {boundary_metrics['f1']}.",
            "novelty_value": "Mapping/tagging and boundary backends are one extension point: derive fields, never introduce a third profiler object.",
            "status": "partial, with supervised expansion evidence",
            "limitations": "Does not support unsupervised or cross-family general boundary detection.",
            "source_paths": [
                rel(paths["reviewer_packet"]),
                rel(paths["boundary_report"]),
            ],
        },
        {
            "id": "P4",
            "claim": "C2",
            "real_problem": "Desktop agents often need subtask-level inspection below a task but above a raw click/key action.",
            "profiler_mechanism": "Carry human-group labels and learned-group fields as stackable operation fields.",
            "public_oracle": "OSWorld-Human single-action and grouped-action human trajectories.",
            "headline_evidence": f"Conservative human-group projection reaches boundary F1 {human['group_pattern_human_group_f1']} at precision {human['group_pattern_human_group_precision']}; R297 learned backend improves over phase/action/target baselines and folds {boundary_stack['total_weight']} held-out operations into {boundary_stack['unique_stacks']} stacks.",
            "novelty_value": "The same action sequence supports action-depth, human-group-depth, and learned-boundary-depth views.",
            "status": "supported as scoped boundary evidence",
            "limitations": "R290 conservative recall is limited; R297 is supervised and OSWorld-only.",
            "source_paths": [
                rel(paths["reviewer_packet"]),
                rel(paths["boundary_report"]),
                rel(paths["boundary_stack"]),
            ],
        },
        {
            "id": "P5",
            "claim": "C2",
            "real_problem": "Agent debugging requires failure, safety, looping, and step-quality diagnostics, not only hot paths.",
            "profiler_mechanism": "Represent expert labels, safety labels, and sequence-derived repetition signals as operation fields, then score and visualize them with stack reports.",
            "public_oracle": "AgentRewardBench expert looping labels, SATraj-OS safety labels, and AgentNet step correctness/redundancy labels.",
            "headline_evidence": f"AgentRewardBench repeat-signal/looping V-measure is {diagnostics['agentreward_repeat_looping_v']} versus {diagnostics['agentreward_step_error_looping_v']} for step-error; SATraj has {unsafe['weight']} unsafe operations; AgentNet step_correct and step_redundant fields have {step_correct['present']} and {step_redundant['present']} covered operations.",
            "novelty_value": "The profiler exposes non-flamegraph quality and safety views without creating separate failure or safety profilers.",
            "status": "supported as diagnostic mechanism",
            "limitations": "Does not prove developer productivity or automatic quality prediction.",
            "source_paths": [
                rel(paths["reviewer_packet"]),
                rel(paths["agentreward_quality"]),
                rel(paths["satraj_quality"]),
                rel(paths["agentnet_quality"]),
            ],
        },
        {
            "id": "P6",
            "claim": "C1",
            "real_problem": "Paper claims drift when results are scattered across shell commands, folded files, and one-off visualizations.",
            "profiler_mechanism": "Use tracked profile specs, trace exchange, claim synthesis, and reviewer evidence packets as reproducibility surfaces.",
            "public_oracle": "R293 profile spec, R294 trace exchange, R295 claim synthesis, and R296 reviewer packet.",
            "headline_evidence": f"R294 trace import and operation import folded outputs are identical; R296 indexes 11 visualization/evidence entries and {len(reviewer_packet['reviewer_questions'])} reviewer questions.",
            "novelty_value": "The contribution includes an auditable research workflow around configurable profiler queries, not just a rendered flamegraph.",
            "status": "supported for artifact auditability",
            "limitations": "Reviewer packets are synthesis artifacts, not new empirical evidence.",
            "source_paths": [
                rel(paths["claim_synthesis"]),
                rel(paths["reviewer_packet"]),
            ],
        },
    ]

    boundary_delta = {
        "learned_vs_phase_change_f1": round(
            boundary_metrics["f1"] - boundary_baselines["phase_change"]["f1"], 4
        ),
        "learned_vs_action_change_f1": round(
            boundary_metrics["f1"] - boundary_baselines["action_change"]["f1"], 4
        ),
        "learned_vs_target_change_f1": round(
            boundary_metrics["f1"] - boundary_baselines["target_change"]["f1"], 4
        ),
        "learned_vs_group_pattern_reference_f1": round(
            boundary_metrics["f1"] - boundary_baselines["group_pattern_reference"]["f1"], 4
        ),
    }

    novelty_claims = [
        {
            "claim": "Two-object agent profiling model",
            "why_new": "The profiler does not privilege prompt, session, span, GUI, safety, or quality objects; they are operation shapes or fields.",
            "evidence": "C1 supported by 15 public labeled sources plus local trace exchange.",
        },
        {
            "claim": "Query-time recursive operation stacks",
            "why_new": "Folded-stack output is reused, but frames come from semantic operation fields and can be changed after capture.",
            "evidence": "R286 depth sweep and R293 profile-spec override on identical operations.",
        },
        {
            "claim": "Unified field-derivation extension point",
            "why_new": "Regex mappings, learned label-derived mappings, and supervised boundary backends all write operation fields before folding.",
            "evidence": "R282/R285 mapping generalization and R297 learned boundary backend.",
        },
        {
            "claim": "Non-flamegraph diagnostic views over real labels",
            "why_new": "Quality, looping, safety, attack, redundancy, and human-group labels become stackable and scoreable fields.",
            "evidence": "R288/R289/R290/R291 diagnostics and R296 evidence packet.",
        },
    ]

    paper_readiness = {
        "osdi_neurips_maturity": "level-3 conference-paper evidence, approaching level 4 for mechanism claims",
        "ready_claims": [row for row in claim_rows if row["verdict"].startswith("supported")],
        "partial_claims": [row for row in claim_rows if row["verdict"].startswith("partial")],
        "must_not_claim": claim_synthesis["unsupported_final_claims"]
        + [
            "R297 generalizes beyond OSWorld-Human",
            "R296 reviewer packet is itself empirical evidence",
        ],
        "remaining_level4_gaps": [
            "replicate the learned boundary backend on another family such as AgentNet or tau-bench",
            "add a user-utility or task-answering study comparing flat trace, fixed session stack, and operation-stack views",
            "add calibration/error analysis for boundary backends",
        ],
    }

    return {
        "schema": "agentsight.paper-value-novelty-synthesis.v1",
        "run_id": "R298",
        "generated_from": {key: rel(path) for key, path in paths.items()},
        "claim_verdicts_from_r295": claim_rows,
        "real_problem_evidence": real_problem_evidence,
        "novelty_claims": novelty_claims,
        "derived_decision_metrics": {
            "dataset_coverage": dataset,
            "recursive_foldability": recursive,
            "mapping_value": mapping,
            "human_group_value": human,
            "diagnostic_value": diagnostics,
            "reproducibility_value": reproducibility,
            "boundary_backend": {
                "split": boundary_report["split"],
                "test_pairs": boundary_report["test_pairs"],
                "test_metrics": boundary_metrics,
                "baseline_delta_f1": boundary_delta,
                "folded_operations": boundary_stack["total_weight"],
                "folded_unique_stacks": boundary_stack["unique_stacks"],
                "agentpprof_samples": boundary_profile["samples"],
                "agentpprof_unique_stacks": boundary_profile["unique_stacks"],
            },
            "diagnostic_oracle_counts": {
                "satraj_unsafe_operations": unsafe["weight"],
                "agentnet_step_correct_present": step_correct["present"],
                "agentnet_step_redundant_present": step_redundant["present"],
            },
        },
        "paper_readiness": paper_readiness,
        "paper_ready_takeaway": (
            "AgentSight should claim configurable semantic profiling over real labeled "
            "agent trajectories: operations provide the common record, operation stacks "
            "provide recursive query-time folding, and mappings/boundary backends only "
            "derive fields before folding. The evidence supports mechanism and diagnostic "
            "value, not unsupervised intent discovery or developer productivity."
        ),
    }


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def markdown(report: dict[str, Any]) -> str:
    lines = [
        "# R298 Paper Value And Novelty Synthesis",
        "",
        report["paper_ready_takeaway"],
        "",
        "## Real Problems And Evidence",
        "",
        "| ID | Claim | Real problem | Headline evidence | Status | Limitation |",
        "|---|---|---|---|---|---|",
    ]
    for row in report["real_problem_evidence"]:
        lines.append(
            "| {id} | {claim} | {problem} | {evidence} | {status} | {limit} |".format(
                id=row["id"],
                claim=row["claim"],
                problem=row["real_problem"],
                evidence=row["headline_evidence"],
                status=row["status"],
                limit=row["limitations"],
            )
        )
    lines.extend(
        [
            "",
            "## Novelty Claims",
            "",
        ]
    )
    for row in report["novelty_claims"]:
        lines.append(f"- **{row['claim']}**: {row['why_new']} Evidence: {row['evidence']}")
    readiness = report["paper_readiness"]
    lines.extend(
        [
            "",
            "## Paper Readiness",
            "",
            f"- Maturity: {readiness['osdi_neurips_maturity']}.",
            "- Remaining level-4 gaps:",
        ]
    )
    for item in readiness["remaining_level4_gaps"]:
        lines.append(f"  - {item}")
    lines.append("- Must not claim:")
    for item in readiness["must_not_claim"]:
        lines.append(f"  - {item}")
    lines.append("")
    return "\n".join(lines)


def html_table(rows: list[dict[str, Any]], columns: list[str]) -> str:
    out = ["<table><tr>"]
    out.extend(f"<th>{html.escape(col)}</th>" for col in columns)
    out.append("</tr>")
    for row in rows:
        out.append("<tr>")
        for col in columns:
            out.append(f"<td>{html.escape(str(row.get(col, '')))}</td>")
        out.append("</tr>")
    out.append("</table>")
    return "\n".join(out)


def render_html(report: dict[str, Any]) -> str:
    metrics = report["derived_decision_metrics"]
    return f"""<!doctype html>
<html>
<head>
<meta charset="utf-8">
<title>R298 Paper Value And Novelty Synthesis</title>
<style>
body{{font-family:system-ui,-apple-system,Segoe UI,sans-serif;margin:28px;background:#fafafa;color:#171717}}
h1{{font-size:24px;margin-bottom:6px}}
h2{{font-size:17px;margin-top:24px}}
.takeaway{{max-width:980px;color:#333}}
.cards{{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:12px;margin:16px 0}}
.card{{background:#fff;border:1px solid #ddd;border-radius:6px;padding:12px}}
.value{{font-size:24px;font-weight:700}}
table{{border-collapse:collapse;width:100%;background:#fff;border:1px solid #ddd}}
th,td{{padding:7px 9px;border-bottom:1px solid #eee;text-align:left;vertical-align:top;font-size:13px}}
th{{background:#f0f3f8}}
</style>
</head>
<body>
<h1>R298 Paper Value And Novelty Synthesis</h1>
<p class="takeaway">{html.escape(report['paper_ready_takeaway'])}</p>
<div class="cards">
<div class="card"><div>Datasets</div><div class="value">{metrics['dataset_coverage']['datasets']}</div></div>
<div class="card"><div>Operations</div><div class="value">{metrics['dataset_coverage']['operations']}</div></div>
<div class="card"><div>R297 F1</div><div class="value">{metrics['boundary_backend']['test_metrics']['f1']}</div></div>
<div class="card"><div>Evidence Problems</div><div class="value">{len(report['real_problem_evidence'])}</div></div>
</div>
<h2>Real Problems And Evidence</h2>
{html_table(report['real_problem_evidence'], ['id', 'claim', 'real_problem', 'headline_evidence', 'status', 'limitations'])}
<h2>Novelty Claims</h2>
{html_table(report['novelty_claims'], ['claim', 'why_new', 'evidence'])}
</body>
</html>
"""


def main() -> None:
    args = parse_args()
    out_dir = args.out_dir if args.out_dir.is_absolute() else ROOT / args.out_dir
    report = build_synthesis()

    json_path = out_dir / "value-novelty-synthesis.json"
    md_path = out_dir / "value-novelty-synthesis.md"
    html_path = out_dir / "index.html"
    write_json(json_path, report)
    md_path.write_text(markdown(report), encoding="utf-8")
    html_path.write_text(render_html(report), encoding="utf-8")

    run_result = {
        "status": "ok",
        "run_id": report["run_id"],
        "json": rel(json_path),
        "markdown": rel(md_path),
        "html": rel(html_path),
        "real_problem_evidence": len(report["real_problem_evidence"]),
        "novelty_claims": len(report["novelty_claims"]),
        "maturity": report["paper_readiness"]["osdi_neurips_maturity"],
    }
    write_json(out_dir / "run-result.json", run_result)
    print(json.dumps(run_result, indent=2))


if __name__ == "__main__":
    main()
