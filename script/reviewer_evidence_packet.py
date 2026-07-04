#!/usr/bin/env python3
"""Build a reviewer-facing evidence packet from tracked semantic-profiler artifacts."""

from __future__ import annotations

import argparse
import html
import json
import os
import subprocess
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OUT_ROOT = ROOT / "docs" / "visexp" / "out"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate an OSDI/NeurIPS-style evidence packet from tracked artifacts."
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=OUT_ROOT / "reviewer-evidence-packet-r296",
    )
    return parser.parse_args()


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def display_path(path: Path) -> str:
    try:
        return rel(path)
    except ValueError:
        return str(path)


def out_rel(path: Path, out_dir: Path) -> str:
    return os.path.relpath(path, out_dir)


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


def ensure_tracked_clean(paths: list[Path]) -> None:
    for path in paths:
        if not path.exists():
            raise SystemExit(f"missing artifact {rel(path)}")
        run_git_check("source artifact is not git-tracked", ["ls-files", "--error-unmatch"], path)
        run_git_check("source artifact has unstaged changes", ["diff", "--quiet"], path)
        run_git_check("source artifact has staged changes", ["diff", "--cached", "--quiet"], path)


def pct(numerator: float, denominator: float) -> float:
    if denominator == 0:
        return 0.0
    return round(numerator / denominator * 100.0, 3)


def ratio(numerator: float, denominator: float) -> float:
    if denominator == 0:
        return 0.0
    return round(numerator / denominator, 3)


def artifact_paths() -> dict[str, Path]:
    return {
        "claim_synthesis": OUT_ROOT / "paper-claim-synthesis-r295" / "claim-synthesis.json",
        "claim_synthesis_md": OUT_ROOT / "paper-claim-synthesis-r295" / "claim-synthesis.md",
        "depth_json": OUT_ROOT / "operation-stack-depth-r286" / "depth-summary.json",
        "depth_html": OUT_ROOT / "operation-stack-depth-r286" / "depth-summary.html",
        "heldout_quality": OUT_ROOT / "operation-map-heldout-r282" / "quality.json",
        "heldout_quality_html": OUT_ROOT / "operation-map-heldout-r282" / "quality.html",
        "heldout_nomap_quality": OUT_ROOT / "operation-map-heldout-r282" / "quality-nomap.json",
        "heldout_stack_html": OUT_ROOT / "operation-map-heldout-r282" / "stack-analysis.html",
        "heldout_nomap_stack_html": OUT_ROOT / "operation-map-heldout-r282" / "stack-analysis-nomap.html",
        "leaveout_json": OUT_ROOT / "operation-map-leaveout-api-r285" / "leaveout-summary.json",
        "leaveout_html": OUT_ROOT / "operation-map-leaveout-api-r285" / "leaveout-summary.html",
        "osworld_quality": OUT_ROOT
        / "external-agent-trace-osworldhuman-r290"
        / "osworld-human-quality.json",
        "osworld_quality_html": OUT_ROOT
        / "external-agent-trace-osworldhuman-r290"
        / "osworld-human-quality.html",
        "osworld_action_stack": OUT_ROOT
        / "external-agent-trace-osworldhuman-r290"
        / "osworld-human-stack-analysis.json",
        "osworld_action_stack_html": OUT_ROOT
        / "external-agent-trace-osworldhuman-r290"
        / "osworld-human-stack-analysis.html",
        "osworld_grouped_stack": OUT_ROOT
        / "external-agent-trace-osworldhuman-r290"
        / "osworld-human-grouped-stack-analysis.json",
        "osworld_grouped_stack_html": OUT_ROOT
        / "external-agent-trace-osworldhuman-r290"
        / "osworld-human-grouped-stack-analysis.html",
        "agentnet_quality": OUT_ROOT
        / "external-agent-trace-agentnet-r291"
        / "agentnet-quality.json",
        "agentnet_quality_html": OUT_ROOT
        / "external-agent-trace-agentnet-r291"
        / "agentnet-quality.html",
        "agentnet_stack_html": OUT_ROOT
        / "external-agent-trace-agentnet-r291"
        / "agentnet-stack-analysis.html",
        "combined14_quality": OUT_ROOT
        / "external-agent-trace-agentnet-r291"
        / "combined-14datasets-quality.json",
        "combined14_stack_html": OUT_ROOT
        / "external-agent-trace-agentnet-r291"
        / "combined-14datasets-stack-analysis.html",
        "agentreward_quality": OUT_ROOT
        / "external-agent-trace-agentreward-r288"
        / "agentreward-quality.json",
        "agentreward_quality_html": OUT_ROOT
        / "external-agent-trace-agentreward-r288"
        / "agentreward-quality.html",
        "agentreward_stack_html": OUT_ROOT
        / "external-agent-trace-agentreward-r288"
        / "agentreward-stack-analysis.html",
        "satraj_quality": OUT_ROOT / "external-agent-trace-satraj-r289" / "satraj-quality.json",
        "satraj_quality_html": OUT_ROOT
        / "external-agent-trace-satraj-r289"
        / "satraj-quality.html",
        "satraj_stack_html": OUT_ROOT
        / "external-agent-trace-satraj-r289"
        / "satraj-stack-analysis.html",
        "combined15_quality": OUT_ROOT
        / "external-agent-trace-scalecua-r292"
        / "combined-15datasets-quality.json",
        "combined15_stack": OUT_ROOT
        / "external-agent-trace-scalecua-r292"
        / "combined-15datasets-stack-analysis.json",
        "combined15_stack_html": OUT_ROOT
        / "external-agent-trace-scalecua-r292"
        / "combined-15datasets-stack-analysis.html",
        "scalecua_history": OUT_ROOT
        / "external-agent-trace-scalecua-r292"
        / "scalecua-history-analysis.json",
        "scalecua_history_html": OUT_ROOT
        / "external-agent-trace-scalecua-r292"
        / "scalecua-history-analysis.html",
        "profile_spec": OUT_ROOT / "profile-spec-r293" / "agentnet-diagnostic-spec.json",
        "profile_spec_result": OUT_ROOT
        / "profile-spec-r293"
        / "agentnet-diagnostic-result.json",
        "profile_spec_override": OUT_ROOT
        / "profile-spec-r293"
        / "agentnet-diagnostic-override-result.json",
        "trace_convert": OUT_ROOT
        / "agent-trace-exchange-r294"
        / "trace-to-operations-result.json",
        "trace_import": OUT_ROOT / "agent-trace-exchange-r294" / "trace-import-result.json",
        "operation_import": OUT_ROOT
        / "agent-trace-exchange-r294"
        / "operation-import-result.json",
    }


def top_by_field(path: Path, field: str) -> list[dict[str, Any]]:
    data = load_json(path)
    top_by_field = require(data, "top_by_field", path)
    values = top_by_field.get(field)
    if not isinstance(values, list):
        raise SystemExit(f"{rel(path)} missing top_by_field.{field}")
    return values


def build_packet(out_dir: Path) -> dict[str, Any]:
    paths = artifact_paths()
    ensure_tracked_clean(list(paths.values()))

    claim_synthesis = load_json(paths["claim_synthesis"])
    evidence = require(claim_synthesis, "evidence", paths["claim_synthesis"])
    claims = require(claim_synthesis, "claims", paths["claim_synthesis"])

    heterogeneous = require(evidence, "heterogeneous_coverage", paths["claim_synthesis"])
    recursive = require(evidence, "recursive_depth", paths["claim_synthesis"])
    mapping = require(evidence, "mapping_generalization", paths["claim_synthesis"])
    human = require(evidence, "human_boundaries", paths["claim_synthesis"])
    diagnostics = require(evidence, "quality_and_failure_diagnostics", paths["claim_synthesis"])
    replay = require(evidence, "reproducibility_and_exchange", paths["claim_synthesis"])

    depth = load_json(paths["depth_json"])
    depth_rows = require(depth, "rows", paths["depth_json"])
    combined15_datasets = top_by_field(paths["combined15_quality"], "dataset")

    dataset_total = heterogeneous["supplemental_operations"]
    top5_weight = sum(row["weight"] for row in combined15_datasets[:5])
    top10_weight = sum(row["weight"] for row in combined15_datasets[:10])

    osworld_action = load_json(paths["osworld_action_stack"])
    osworld_grouped = load_json(paths["osworld_grouped_stack"])
    spec = load_json(paths["profile_spec_result"])
    spec_override = load_json(paths["profile_spec_override"])

    derived_metrics = {
        "dataset_coverage": {
            "datasets": heterogeneous["supplemental_datasets"],
            "operations": dataset_total,
            "unique_stacks": heterogeneous["supplemental_unique_stacks"],
            "top5_operation_share_percent": pct(top5_weight, dataset_total),
            "top10_operation_share_percent": pct(top10_weight, dataset_total),
        },
        "recursive_foldability": {
            "same_operations": recursive["samples"],
            "dataset_unique_stacks": recursive["dataset_unique_stacks"],
            "phase_unique_stacks": recursive["phase_unique_stacks"],
            "action_unique_stacks": recursive["action_unique_stacks"],
            "fixed_session_unique_stacks": recursive["fixed_session_unique_stacks"],
            "phase_expansion_vs_dataset": ratio(
                recursive["phase_unique_stacks"], recursive["dataset_unique_stacks"]
            ),
            "action_expansion_vs_dataset": ratio(
                recursive["action_unique_stacks"], recursive["dataset_unique_stacks"]
            ),
            "fixed_session_expansion_vs_dataset": recursive[
                "fixed_session_expansion_vs_dataset"
            ],
        },
        "mapping_value": {
            "heldout_operations": mapping["heldout_operations"],
            "unique_stack_reduction_percent": pct(
                mapping["nomap_unique_stacks"] - mapping["mapped_unique_stacks"],
                mapping["nomap_unique_stacks"],
            ),
            "compression_improvement_percent": pct(
                mapping["mapped_compression"] - mapping["nomap_compression"],
                mapping["nomap_compression"],
            ),
            "leaveout_positive_rate_percent": pct(
                mapping["leaveout_positive_stack_reduction"], mapping["leaveout_datasets"]
            ),
            "leaveout_negative_folds": mapping["leaveout_negative_stack_reduction"],
            "boundary_precision": mapping["phase_action_boundary_precision"],
        },
        "human_group_value": {
            "operations": human["operations"],
            "exact_group_coverage_percent": pct(
                human["human_group_present"], human["human_group_total"]
            ),
            "action_unique_stacks": human["action_unique_stacks"],
            "grouped_unique_stacks": human["grouped_unique_stacks"],
            "grouped_stack_reduction_percent": pct(
                human["action_unique_stacks"] - human["grouped_unique_stacks"],
                human["action_unique_stacks"],
            ),
            "action_stack_compression": osworld_action["compression_ratio"],
            "grouped_stack_compression": osworld_grouped["compression_ratio"],
            "group_pattern_human_group_f1": human["group_pattern_human_group_f1"],
            "group_pattern_human_group_precision": human[
                "group_pattern_human_group_precision"
            ],
            "group_pattern_human_group_recall": human["group_pattern_human_group_recall"],
        },
        "diagnostic_value": {
            "agentnet_step_label_coverage_percent": pct(
                diagnostics["agentnet_step_correct_present"],
                diagnostics["agentnet_operations"],
            ),
            "agentreward_repeat_looping_v": diagnostics["agentreward_repeat_looping_v"],
            "agentreward_step_error_looping_v": diagnostics[
                "agentreward_step_error_looping_v"
            ],
            "agentreward_repeat_vs_step_error_looping_v_ratio": ratio(
                diagnostics["agentreward_repeat_looping_v"],
                diagnostics["agentreward_step_error_looping_v"],
            ),
            "agentnet_status_step_correct_v": diagnostics["agentnet_status_step_correct_v"],
            "agentnet_repeat_step_redundant_v": diagnostics[
                "agentnet_repeat_step_redundant_v"
            ],
            "satraj_attack_action_v": diagnostics["satraj_attack_action_v"],
        },
        "reproducibility_value": {
            "profile_spec_samples": replay["profile_spec_samples"],
            "profile_spec_unique_stacks": replay["profile_spec_unique_stacks"],
            "profile_spec_override_unique_stacks": replay[
                "profile_spec_override_unique_stacks"
            ],
            "profile_spec_override_reduction_percent": pct(
                spec["unique_stacks"] - spec_override["unique_stacks"],
                spec["unique_stacks"],
            ),
            "trace_converted_operations": replay["trace_converted_operations"],
            "trace_import_samples": replay["trace_import_samples"],
            "operation_import_samples": replay["operation_import_samples"],
            "folded_outputs_identical": replay["folded_outputs_identical"],
        },
    }

    visualizations = visualization_catalog(paths)
    reviewer_questions = [
        {
            "question": "Does the profiler avoid prompt/session-specific abstraction?",
            "answer": (
                "Yes for the tested scope: heterogeneous public trajectories and a local "
                "session trace enter the same operation/operation-stack path."
            ),
            "claim": "C1",
            "primary_evidence": [
                "R291/R292 combined quality",
                "R293 profile-spec replay",
                "R294 trace exchange",
                "R295 claim synthesis",
            ],
            "auditable_outputs": [
                rel(paths["combined15_quality"]),
                rel(paths["profile_spec_result"]),
                rel(paths["trace_import"]),
                rel(paths["operation_import"]),
            ],
            "caveat": "This does not prove full-scale conversion of every public benchmark.",
        },
        {
            "question": "Can one operation sequence be folded at multiple useful depths?",
            "answer": (
                "Yes. R286 sweeps identical operations across eight stack depths, while "
                "R290 folds OSWorld-Human single actions at action or grouped depth."
            ),
            "claim": "C2",
            "primary_evidence": ["R286 recursive depth", "R290 grouped-action oracle"],
            "auditable_outputs": [
                rel(paths["depth_json"]),
                rel(paths["depth_html"]),
                rel(paths["osworld_action_stack_html"]),
                rel(paths["osworld_grouped_stack_html"]),
            ],
            "caveat": "The current grouped-boundary detector is conservative and incomplete.",
        },
        {
            "question": "Does mapping/tagging add value beyond pretty printing?",
            "answer": (
                "Partially. R282 improves held-out compression and R285 has zero negative "
                "leave-dataset-out folds after operation-family precedence fixes."
            ),
            "claim": "C3",
            "primary_evidence": ["R282 held-out mapping", "R285 leave-dataset-out"],
            "auditable_outputs": [
                rel(paths["heldout_quality"]),
                rel(paths["heldout_nomap_quality"]),
                rel(paths["leaveout_json"]),
            ],
            "caveat": "This remains label-derived deterministic mapping, not unsupervised discovery.",
        },
        {
            "question": "Does the profiler solve real diagnostic tasks, not just flamegraphs?",
            "answer": (
                "Yes as a mechanism: AgentRewardBench, SATraj, and AgentNet expose "
                "looping, safety, attack, correctness, and redundancy fields as stackable "
                "operation fields with negative controls."
            ),
            "claim": "C2",
            "primary_evidence": [
                "R288 failure diagnostics",
                "R289 safety diagnostics",
                "R291 step-quality diagnostics",
            ],
            "auditable_outputs": [
                rel(paths["agentreward_quality_html"]),
                rel(paths["satraj_quality_html"]),
                rel(paths["agentnet_quality_html"]),
            ],
            "caveat": "No user study yet proves developer productivity gains.",
        },
    ]

    expansion_gates = [
        {
            "gate": "Non-rule boundary backend",
            "why": "Would convert C3 from deterministic mapping to a stronger boundary-detection claim.",
            "datasets": ["OSWorld-Human", "AgentNet", "tau-bench"],
            "oracle": "human_group, step_correct/step_redundant, task/action labels",
            "success_condition": "Improve recall/calibration without losing the high precision seen in R282/R290/R291.",
        },
        {
            "gate": "User utility task study",
            "why": "Would support a developer-productivity claim now explicitly excluded by R295/R296.",
            "datasets": ["OSWorld-Human", "AgentRewardBench", "SATraj-OS"],
            "oracle": "debugging-task answer correctness and time",
            "success_condition": "Operation-stack views outperform flat traces and fixed-session stacks.",
        },
        {
            "gate": "Larger streaming corpus",
            "why": "Would expand C1 from sampled public trajectories to broader benchmark coverage.",
            "datasets": ["AgentNet full platform shards", "ScaleCUA multi-platform", "VisualWebArena/UI-Vision"],
            "oracle": "streaming conversion success, redaction policy, stack-quality summaries",
            "success_condition": "Keep raw archives out of git while preserving auditable operation summaries.",
        },
    ]

    conclusions = [
        "The two-object abstraction is sufficient for the tested public trajectories: operations carry all event and label shapes, while operation stacks encode query-time recursive folding.",
        "The best current novelty claim is configurable semantic profiling over labeled agent trajectories, not a new benchmark and not another fixed flamegraph.",
        "The strongest value evidence is diagnostic: human-group boundaries, step-quality labels, looping, safety, and attack labels remain ordinary stackable operation fields.",
        "The current boundary mechanism is intentionally scoped: deterministic label-derived mapping improves aggregation, but unsupervised or LLM-backed boundary discovery remains future work.",
    ]

    packet = {
        "schema": "agentsight.reviewer-evidence-packet.v1",
        "run_id": "R296",
        "source_window": "R282-R295",
        "provenance": {
            "input_artifacts_git_tracked_and_clean": True,
            "input_artifact_count": len(paths),
        },
        "claim_verdicts": claims,
        "derived_metrics": derived_metrics,
        "depth_rows": depth_rows,
        "dataset_weights": combined15_datasets,
        "visualization_catalog": visualizations,
        "reviewer_questions": reviewer_questions,
        "expansion_gates": expansion_gates,
        "paper_ready_conclusions": conclusions,
        "unsupported_final_claims": claim_synthesis.get("unsupported_final_claims", []),
        "generated_from": {name: rel(path) for name, path in paths.items()},
    }
    return packet


def visualization_catalog(paths: dict[str, Path]) -> list[dict[str, Any]]:
    return [
        {
            "name": "Claim synthesis gate",
            "kind": "claim table",
            "claim": "C1/C2/C3",
            "primary_path": rel(paths["claim_synthesis"]),
            "output_path": rel(paths["claim_synthesis_md"]),
            "takeaway": "Paper wording is grounded in tracked artifacts and unsupported claims stay explicit.",
        },
        {
            "name": "Recursive stack-depth sweep",
            "kind": "depth sweep",
            "claim": "C1/C2",
            "primary_path": rel(paths["depth_json"]),
            "output_path": rel(paths["depth_html"]),
            "takeaway": "The same operations fold from dataset to phase/action/fixed-session depths.",
        },
        {
            "name": "Held-out mapping quality",
            "kind": "quality report",
            "claim": "C2/C3",
            "primary_path": rel(paths["heldout_quality"]),
            "output_path": rel(paths["heldout_quality_html"]),
            "takeaway": "Label-derived mappings improve held-out aggregation against no-map baseline.",
        },
        {
            "name": "Leave-dataset-out mapping",
            "kind": "cross-dataset ablation",
            "claim": "C3",
            "primary_path": rel(paths["leaveout_json"]),
            "output_path": rel(paths["leaveout_html"]),
            "takeaway": "Operation-family precedence removes negative leave-out stack-reduction folds.",
        },
        {
            "name": "OSWorld-Human action-depth stack",
            "kind": "stack tree and transitions",
            "claim": "C2",
            "primary_path": rel(paths["osworld_action_stack"]),
            "output_path": rel(paths["osworld_action_stack_html"]),
            "takeaway": "Desktop single-action trajectories profile through the same operation-stack path.",
        },
        {
            "name": "OSWorld-Human grouped-depth stack",
            "kind": "human-boundary stack tree",
            "claim": "C2",
            "primary_path": rel(paths["osworld_grouped_stack"]),
            "output_path": rel(paths["osworld_grouped_stack_html"]),
            "takeaway": "Validated human grouped-action fields fold the same sequence at coarser depth.",
        },
        {
            "name": "AgentNet step-quality report",
            "kind": "quality and coverage report",
            "claim": "C1/C2",
            "primary_path": rel(paths["agentnet_quality"]),
            "output_path": rel(paths["agentnet_quality_html"]),
            "takeaway": "Step correctness and redundancy are ordinary operation fields with full coverage.",
        },
        {
            "name": "AgentRewardBench failure diagnostics",
            "kind": "failure-quality report",
            "claim": "C2",
            "primary_path": rel(paths["agentreward_quality"]),
            "output_path": rel(paths["agentreward_quality_html"]),
            "takeaway": "Looping labels expose sequence diagnostics beyond per-step error labels.",
        },
        {
            "name": "SATraj safety diagnostics",
            "kind": "safety-quality report",
            "claim": "C2",
            "primary_path": rel(paths["satraj_quality"]),
            "output_path": rel(paths["satraj_quality_html"]),
            "takeaway": "Safety and attack labels are diagnostic operation fields, not phase proxies.",
        },
        {
            "name": "ScaleCUA history-depth analysis",
            "kind": "history-depth report",
            "claim": "C1/C2",
            "primary_path": rel(paths["scalecua_history"]),
            "output_path": rel(paths["scalecua_history_html"]),
            "takeaway": "Previous-operation context can be represented as stackable operation fields.",
        },
        {
            "name": "Fifteen-dataset combined stack analysis",
            "kind": "stack tree and transitions",
            "claim": "C1/C2",
            "primary_path": rel(paths["combined15_stack"]),
            "output_path": rel(paths["combined15_stack_html"]),
            "takeaway": "The same profiler path spans web, desktop, mobile, API, dialogue, safety, and quality traces.",
        },
    ]


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def markdown(packet: dict[str, Any]) -> str:
    m = packet["derived_metrics"]
    lines = [
        "# R296 Reviewer Evidence Packet",
        "",
        "This packet is generated from tracked R282-R295 artifacts. It is a reviewer navigation layer over existing results, not a new empirical dataset run.",
        "",
        "## Claim Verdicts",
        "",
        "| Claim | Verdict | Paper-ready wording | Unsupported wording |",
        "|---|---|---|---|",
    ]
    for claim in packet["claim_verdicts"]:
        lines.append(
            "| {claim} | {verdict} | {wording} | {unsupported} |".format(
                claim=claim["claim"],
                verdict=claim["verdict"],
                wording=claim["paper_ready_wording"],
                unsupported=", ".join(claim["not_supported"]),
            )
        )

    lines.extend(
        [
            "",
            "## Derived Reviewer Metrics",
            "",
            "- Coverage: {datasets} datasets, {operations} operations, {unique_stacks} unique stacks; top-5 datasets hold {top5_operation_share_percent}% of operations.".format(
                **m["dataset_coverage"]
            ),
            "- Recursive foldability: the same {same_operations} operations fold from {dataset_unique_stacks} dataset stacks to {phase_unique_stacks} phase, {action_unique_stacks} action, and {fixed_session_unique_stacks} fixed-session stacks.".format(
                **m["recursive_foldability"]
            ),
            "- Mapping value: held-out mapping reduces unique stacks by {unique_stack_reduction_percent}% and improves compression by {compression_improvement_percent}%; leave-dataset-out positive folds are {leaveout_positive_rate_percent}% with {leaveout_negative_folds} negative folds.".format(
                **m["mapping_value"]
            ),
            "- Human-group value: OSWorld grouped-depth stacks reduce action-depth unique stacks by {grouped_stack_reduction_percent}%; group-pattern/human-group F1 is {group_pattern_human_group_f1} at precision {group_pattern_human_group_precision}.".format(
                **m["human_group_value"]
            ),
            "- Diagnostic value: AgentRewardBench repeat-signal/looping V-measure is {agentreward_repeat_looping_v} vs {agentreward_step_error_looping_v} for the step-error baseline ({agentreward_repeat_vs_step_error_looping_v_ratio}x); AgentNet task status and repeat signal remain weak proxies for per-step quality.".format(
                **m["diagnostic_value"]
            ),
            "- Reproducibility value: profile-spec override reduces AgentNet stacks by {profile_spec_override_reduction_percent}% without changing operations; trace and operation imports remain folded-output equivalent.".format(
                **m["reproducibility_value"]
            ),
            "",
            "## Visualization Catalog",
            "",
            "| View | Kind | Claim | Output | Takeaway |",
            "|---|---|---|---|---|",
        ]
    )
    for view in packet["visualization_catalog"]:
        lines.append(
            "| {name} | {kind} | {claim} | `{output_path}` | {takeaway} |".format(**view)
        )

    lines.extend(
        [
            "",
            "## Reviewer Questions",
            "",
            "| Question | Answer | Caveat |",
            "|---|---|---|",
        ]
    )
    for question in packet["reviewer_questions"]:
        lines.append(
            "| {question} | {answer} | {caveat} |".format(
                question=question["question"],
                answer=question["answer"],
                caveat=question["caveat"],
            )
        )

    lines.extend(
        [
            "",
            "## Expansion Gates",
            "",
            "| Gate | Why | Success condition |",
            "|---|---|---|",
        ]
    )
    for gate in packet["expansion_gates"]:
        lines.append(
            "| {gate} | {why} | {success_condition} |".format(
                gate=gate["gate"], why=gate["why"], success_condition=gate["success_condition"]
            )
        )

    lines.extend(["", "## Unsupported Final Claims", ""])
    for claim in packet["unsupported_final_claims"]:
        lines.append(f"- {claim}")
    lines.append("")
    return "\n".join(lines)


def render_html(packet: dict[str, Any], out_dir: Path) -> str:
    m = packet["derived_metrics"]
    cards = [
        (
            "Datasets",
            str(m["dataset_coverage"]["datasets"]),
            f"{m['dataset_coverage']['operations']} operations",
        ),
        (
            "Recursive Depth",
            f"{m['recursive_foldability']['dataset_unique_stacks']} -> {m['recursive_foldability']['fixed_session_unique_stacks']}",
            "dataset to fixed-session stacks",
        ),
        (
            "Mapping Reduction",
            f"{m['mapping_value']['unique_stack_reduction_percent']}%",
            "held-out unique-stack reduction",
        ),
        (
            "Human Groups",
            f"{m['human_group_value']['group_pattern_human_group_f1']}",
            "OSWorld boundary F1",
        ),
        (
            "Spec Override",
            f"{m['reproducibility_value']['profile_spec_override_reduction_percent']}%",
            "fewer AgentNet stacks",
        ),
    ]
    return f"""<!doctype html>
<html>
<head>
<meta charset="utf-8">
<title>R296 Reviewer Evidence Packet</title>
<style>
body{{font-family:system-ui,-apple-system,Segoe UI,sans-serif;margin:0;background:#f7f8fb;color:#171717}}
header{{background:#ffffff;border-bottom:1px solid #d9dde7;padding:24px 32px}}
main{{padding:24px 32px;max-width:1180px;margin:0 auto}}
h1{{font-size:26px;margin:0 0 8px}}
h2{{font-size:18px;margin:28px 0 12px}}
.meta{{color:#555;font-size:14px}}
.cards{{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:12px;margin:18px 0}}
.card{{background:white;border:1px solid #d9dde7;border-radius:6px;padding:14px}}
.card .value{{font-size:24px;font-weight:700;margin:4px 0}}
.card .label{{font-size:12px;color:#555}}
table{{border-collapse:collapse;width:100%;background:white;border:1px solid #d9dde7}}
th,td{{padding:8px 10px;border-bottom:1px solid #edf0f5;text-align:left;vertical-align:top;font-size:13px}}
th{{background:#eef2f7;font-weight:650}}
.claim{{font-weight:700;white-space:nowrap}}
.pill{{display:inline-block;border:1px solid #c6d4ea;border-radius:999px;padding:2px 8px;margin:2px;background:#eef5ff;font-size:12px}}
.risk{{color:#8a3c00}}
a{{color:#174ea6;text-decoration:none}}
a:hover{{text-decoration:underline}}
</style>
</head>
<body>
<header>
<h1>R296 Reviewer Evidence Packet</h1>
<div class="meta">Generated from tracked R282-R295 artifacts. Navigation layer only; no new dataset run.</div>
</header>
<main>
<div class="cards">
{''.join(card_html(title, value, label) for title, value, label in cards)}
</div>
<h2>Claim Verdicts</h2>
{claims_table(packet)}
<h2>Reviewer Questions</h2>
{questions_table(packet)}
<h2>Visualization Catalog</h2>
{visual_table(packet, out_dir)}
<h2>Expansion Gates</h2>
{gates_table(packet)}
<h2>Unsupported Final Claims</h2>
<ul>{''.join('<li class="risk">' + html.escape(item) + '</li>' for item in packet['unsupported_final_claims'])}</ul>
</main>
</body>
</html>
"""


def card_html(title: str, value: str, label: str) -> str:
    return (
        "<div class='card'>"
        f"<div class='label'>{html.escape(title)}</div>"
        f"<div class='value'>{html.escape(value)}</div>"
        f"<div class='label'>{html.escape(label)}</div>"
        "</div>"
    )


def claims_table(packet: dict[str, Any]) -> str:
    rows = ["<table><tr><th>Claim</th><th>Verdict</th><th>Wording</th><th>Not Supported</th></tr>"]
    for claim in packet["claim_verdicts"]:
        rows.append(
            "<tr>"
            f"<td class='claim'>{html.escape(claim['claim'])}</td>"
            f"<td>{html.escape(claim['verdict'])}</td>"
            f"<td>{html.escape(claim['paper_ready_wording'])}</td>"
            f"<td>{', '.join(html.escape(item) for item in claim['not_supported'])}</td>"
            "</tr>"
        )
    rows.append("</table>")
    return "\n".join(rows)


def questions_table(packet: dict[str, Any]) -> str:
    rows = ["<table><tr><th>Question</th><th>Answer</th><th>Evidence</th><th>Caveat</th></tr>"]
    for item in packet["reviewer_questions"]:
        evidence = " ".join(
            f"<span class='pill'>{html.escape(source)}</span>"
            for source in item["primary_evidence"]
        )
        rows.append(
            "<tr>"
            f"<td>{html.escape(item['question'])}</td>"
            f"<td>{html.escape(item['answer'])}</td>"
            f"<td>{evidence}</td>"
            f"<td class='risk'>{html.escape(item['caveat'])}</td>"
            "</tr>"
        )
    rows.append("</table>")
    return "\n".join(rows)


def visual_table(packet: dict[str, Any], out_dir: Path) -> str:
    rows = ["<table><tr><th>View</th><th>Kind</th><th>Claim</th><th>Output</th><th>Takeaway</th></tr>"]
    for item in packet["visualization_catalog"]:
        target = ROOT / item["output_path"]
        link = out_rel(target, out_dir)
        rows.append(
            "<tr>"
            f"<td>{html.escape(item['name'])}</td>"
            f"<td>{html.escape(item['kind'])}</td>"
            f"<td>{html.escape(item['claim'])}</td>"
            f"<td><a href='{html.escape(link)}'>{html.escape(item['output_path'])}</a></td>"
            f"<td>{html.escape(item['takeaway'])}</td>"
            "</tr>"
        )
    rows.append("</table>")
    return "\n".join(rows)


def gates_table(packet: dict[str, Any]) -> str:
    rows = ["<table><tr><th>Gate</th><th>Why</th><th>Datasets</th><th>Success Condition</th></tr>"]
    for gate in packet["expansion_gates"]:
        rows.append(
            "<tr>"
            f"<td>{html.escape(gate['gate'])}</td>"
            f"<td>{html.escape(gate['why'])}</td>"
            f"<td>{', '.join(html.escape(item) for item in gate['datasets'])}</td>"
            f"<td>{html.escape(gate['success_condition'])}</td>"
            "</tr>"
        )
    rows.append("</table>")
    return "\n".join(rows)


def main() -> None:
    args = parse_args()
    out_dir = args.out_dir
    if not out_dir.is_absolute():
        out_dir = ROOT / out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    packet = build_packet(out_dir)
    json_path = out_dir / "reviewer-evidence.json"
    md_path = out_dir / "reviewer-evidence.md"
    html_path = out_dir / "index.html"
    write_json(json_path, packet)
    md_path.write_text(markdown(packet), encoding="utf-8")
    html_path.write_text(render_html(packet, out_dir), encoding="utf-8")
    print(
        json.dumps(
            {
                "status": "ok",
                "run_id": packet["run_id"],
                "json": display_path(json_path),
                "markdown": display_path(md_path),
                "html": display_path(html_path),
                "visualizations": len(packet["visualization_catalog"]),
                "reviewer_questions": len(packet["reviewer_questions"]),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
