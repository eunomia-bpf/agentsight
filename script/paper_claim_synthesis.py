#!/usr/bin/env python3
"""Synthesize paper-claim evidence from tracked semantic-profiler artifacts."""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OUT_ROOT = ROOT / "docs" / "visexp" / "out"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate a reviewer-facing claim synthesis from tracked artifacts."
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=OUT_ROOT / "paper-claim-synthesis-r295",
    )
    return parser.parse_args()


def load_json(path: Path) -> Any:
    with path.open() as file:
        return json.load(file)


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


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
        run_git_check("source artifact is not git-tracked", ["ls-files", "--error-unmatch"], path)
        run_git_check("source artifact has unstaged changes", ["diff", "--quiet"], path)
        run_git_check(
            "source artifact has staged changes", ["diff", "--cached", "--quiet"], path
        )


def require(data: dict[str, Any], key: str, path: Path) -> Any:
    if key not in data:
        raise SystemExit(f"{rel(path)} missing key {key!r}")
    return data[key]


def quality_summary(path: Path) -> dict[str, Any]:
    data = load_json(path)
    return require(data, "summary", path)


def top_values(path: Path, field: str) -> list[dict[str, Any]]:
    data = load_json(path)
    top_by_field = require(data, "top_by_field", path)
    values = top_by_field.get(field)
    if not isinstance(values, list):
        raise SystemExit(f"{rel(path)} missing top_by_field.{field}")
    return values


def find_alignment(path: Path, predicted: str, oracle: str) -> dict[str, Any]:
    data = load_json(path)
    for row in data.get("oracle_alignment", []):
        if row.get("predicted") == predicted and row.get("oracle") == oracle:
            return row
    raise SystemExit(f"{rel(path)} missing oracle alignment {predicted}:{oracle}")


def find_boundary(path: Path, predicted: str, oracle: str) -> dict[str, Any]:
    data = load_json(path)
    for row in data.get("boundary_alignment", []):
        if row.get("predicted") == predicted and row.get("oracle") == oracle:
            return row
    raise SystemExit(f"{rel(path)} missing boundary alignment {predicted}:{oracle}")


def coverage(path: Path, field: str) -> dict[str, Any]:
    data = load_json(path)
    for row in data.get("coverage", []):
        if row.get("field") == field:
            return row
    raise SystemExit(f"{rel(path)} missing coverage field {field}")


def profile_result(path: Path) -> dict[str, Any]:
    data = load_json(path)
    if "samples" in data:
        return data
    profile = data.get("profile")
    if isinstance(profile, dict):
        summary = profile.get("summary")
        if isinstance(summary, dict):
            return {
                "samples": summary.get("operations") or summary.get("total_weight"),
                "unique_stacks": summary.get("unique_stacks"),
                "compression_ratio": summary.get("compression_ratio"),
                "sample_type": profile.get("sample_type"),
                "unit": profile.get("unit"),
                "view": profile.get("view"),
            }
    raise SystemExit(f"{rel(path)} is not a recognized profile result")


def folded_lines(path: Path) -> int:
    with path.open() as file:
        return sum(1 for line in file if line.strip())


def build_synthesis() -> dict[str, Any]:
    paths = {
        "combined14_quality": OUT_ROOT
        / "external-agent-trace-agentnet-r291"
        / "combined-14datasets-quality.json",
        "combined15_quality": OUT_ROOT
        / "external-agent-trace-scalecua-r292"
        / "combined-15datasets-quality.json",
        "depth": OUT_ROOT / "operation-stack-depth-r286" / "depth-summary.json",
        "heldout_profile": OUT_ROOT
        / "operation-map-heldout-r282"
        / "agentpprof-result.json",
        "heldout_nomap_profile": OUT_ROOT
        / "operation-map-heldout-r282"
        / "agentpprof-nomap-result.json",
        "heldout_quality": OUT_ROOT / "operation-map-heldout-r282" / "quality.json",
        "heldout_nomap_quality": OUT_ROOT
        / "operation-map-heldout-r282"
        / "quality-nomap.json",
        "leaveout": OUT_ROOT / "operation-map-leaveout-api-r285" / "leaveout-summary.json",
        "osworld_quality": OUT_ROOT
        / "external-agent-trace-osworldhuman-r290"
        / "osworld-human-quality.json",
        "osworld_stack": OUT_ROOT
        / "external-agent-trace-osworldhuman-r290"
        / "osworld-human-stack-analysis.json",
        "osworld_grouped_stack": OUT_ROOT
        / "external-agent-trace-osworldhuman-r290"
        / "osworld-human-grouped-stack-analysis.json",
        "agentnet_quality": OUT_ROOT
        / "external-agent-trace-agentnet-r291"
        / "agentnet-quality.json",
        "agentreward_quality": OUT_ROOT
        / "external-agent-trace-agentreward-r288"
        / "agentreward-quality.json",
        "satraj_quality": OUT_ROOT
        / "external-agent-trace-satraj-r289"
        / "satraj-quality.json",
        "profile_spec": OUT_ROOT / "profile-spec-r293" / "agentnet-diagnostic-result.json",
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
        "trace_folded": OUT_ROOT / "agent-trace-exchange-r294" / "trace-import.folded",
        "operation_folded": OUT_ROOT
        / "agent-trace-exchange-r294"
        / "operation-import.folded",
    }

    for path in paths.values():
        if not path.exists():
            raise SystemExit(f"missing artifact {rel(path)}")
    ensure_sources_tracked_clean(list(paths.values()))

    combined14 = quality_summary(paths["combined14_quality"])
    combined15 = quality_summary(paths["combined15_quality"])
    combined14_datasets = top_values(paths["combined14_quality"], "dataset")
    combined15_datasets = top_values(paths["combined15_quality"], "dataset")

    depth = load_json(paths["depth"])
    depth_summary = require(depth, "summary", paths["depth"])
    depth_rows = require(depth, "rows", paths["depth"])
    depth_by_name = {row["name"]: row for row in depth_rows}

    heldout = profile_result(paths["heldout_profile"])
    heldout_nomap = profile_result(paths["heldout_nomap_profile"])
    heldout_quality = quality_summary(paths["heldout_quality"])
    heldout_nomap_quality = quality_summary(paths["heldout_nomap_quality"])
    heldout_phase = find_boundary(paths["heldout_quality"], "phase", "action")
    heldout_task = find_alignment(paths["heldout_quality"], "task", "dataset")
    heldout_nomap_task = find_alignment(paths["heldout_nomap_quality"], "task", "dataset")

    leaveout = load_json(paths["leaveout"])
    leaveout_summary = require(leaveout, "summary", paths["leaveout"])

    osworld = quality_summary(paths["osworld_quality"])
    osworld_action_stack = load_json(paths["osworld_stack"])
    osworld_grouped_stack = load_json(paths["osworld_grouped_stack"])
    osworld_phase_boundary = find_boundary(paths["osworld_quality"], "phase", "action")
    osworld_group_boundary = find_boundary(
        paths["osworld_quality"], "group_pattern", "human_group"
    )
    osworld_group_coverage = coverage(paths["osworld_quality"], "human_group")

    agentnet = quality_summary(paths["agentnet_quality"])
    agentnet_phase_boundary = find_boundary(paths["agentnet_quality"], "phase", "action")
    agentnet_step_correct = coverage(paths["agentnet_quality"], "step_correct")
    agentnet_step_redundant = coverage(paths["agentnet_quality"], "step_redundant")
    agentnet_status_step = find_alignment(paths["agentnet_quality"], "status", "step_correct")
    agentnet_repeat_redundant = find_alignment(
        paths["agentnet_quality"], "repeat_signal", "step_redundant"
    )

    agentreward = quality_summary(paths["agentreward_quality"])
    agentreward_repeat_loop = find_alignment(
        paths["agentreward_quality"], "repeat_signal", "looping"
    )
    agentreward_step_loop = find_alignment(paths["agentreward_quality"], "step_error", "looping")

    satraj = quality_summary(paths["satraj_quality"])
    satraj_phase_boundary = find_boundary(paths["satraj_quality"], "phase", "action")
    satraj_safety = coverage(paths["satraj_quality"], "safety")
    satraj_attack_action = find_alignment(paths["satraj_quality"], "attack_type", "action")

    spec = profile_result(paths["profile_spec"])
    spec_override = profile_result(paths["profile_spec_override"])
    trace_convert = load_json(paths["trace_convert"])
    trace_import = profile_result(paths["trace_import"])
    operation_import = profile_result(paths["operation_import"])
    trace_equivalent = paths["trace_folded"].read_bytes() == paths["operation_folded"].read_bytes()

    evidence = {
        "heterogeneous_coverage": {
            "core_datasets": len(combined14_datasets),
            "core_operations": combined14["operations"],
            "core_unique_stacks": combined14["unique_stacks"],
            "core_compression_ratio": combined14["compression_ratio"],
            "supplemental_datasets": len(combined15_datasets),
            "supplemental_operations": combined15["operations"],
            "supplemental_unique_stacks": combined15["unique_stacks"],
            "top_dataset_weights": combined15_datasets,
            "source": [rel(paths["combined14_quality"]), rel(paths["combined15_quality"])],
        },
        "recursive_depth": {
            "samples": depth_summary["samples"],
            "stack_depths": depth_summary["stack_depths"],
            "dataset_unique_stacks": depth_by_name["dataset"]["unique_stacks"],
            "phase_unique_stacks": depth_by_name["phase"]["unique_stacks"],
            "tool_unique_stacks": depth_by_name["tool"]["unique_stacks"],
            "semantic_unique_stacks": depth_by_name["semantic"]["unique_stacks"],
            "action_unique_stacks": depth_by_name["action"]["unique_stacks"],
            "fixed_session_unique_stacks": depth_by_name["fixed-session"]["unique_stacks"],
            "fixed_session_expansion_vs_dataset": depth_summary[
                "max_expansion_vs_dataset_depth"
            ],
            "source": rel(paths["depth"]),
        },
        "mapping_generalization": {
            "heldout_operations": heldout["samples"],
            "mapped_unique_stacks": heldout["unique_stacks"],
            "nomap_unique_stacks": heldout_nomap["unique_stacks"],
            "mapped_compression": heldout_quality["compression_ratio"],
            "nomap_compression": heldout_nomap_quality["compression_ratio"],
            "mapped_task_dataset_v": heldout_task["v_measure"],
            "nomap_task_dataset_v": heldout_nomap_task["v_measure"],
            "phase_action_boundary_f1": heldout_phase["f1"],
            "phase_action_boundary_precision": heldout_phase["precision"],
            "leaveout_datasets": leaveout_summary["datasets"],
            "leaveout_positive_stack_reduction": leaveout_summary[
                "positive_stack_reduction_datasets"
            ],
            "leaveout_negative_stack_reduction": leaveout_summary[
                "negative_stack_reduction_datasets"
            ],
            "weighted_stack_reduction_per_1k_ops": leaveout_summary[
                "weighted_stack_reduction_per_1k_ops"
            ],
            "source": [rel(paths["heldout_quality"]), rel(paths["leaveout"])],
        },
        "human_boundaries": {
            "operations": osworld["operations"],
            "action_unique_stacks": osworld_action_stack["unique_stacks"],
            "grouped_unique_stacks": osworld_grouped_stack["unique_stacks"],
            "human_group_present": osworld_group_coverage["present"],
            "human_group_total": osworld_group_coverage["total"],
            "phase_action_boundary_f1": osworld_phase_boundary["f1"],
            "group_pattern_human_group_f1": osworld_group_boundary["f1"],
            "group_pattern_human_group_precision": osworld_group_boundary["precision"],
            "group_pattern_human_group_recall": osworld_group_boundary["recall"],
            "skipped_missing_fields": osworld_group_boundary["skipped_missing_fields"],
            "source": rel(paths["osworld_quality"]),
        },
        "quality_and_failure_diagnostics": {
            "agentnet_operations": agentnet["operations"],
            "agentnet_unique_stacks": agentnet["unique_stacks"],
            "agentnet_phase_action_boundary_f1": agentnet_phase_boundary["f1"],
            "agentnet_phase_action_boundary_precision": agentnet_phase_boundary["precision"],
            "agentnet_step_correct_present": agentnet_step_correct["present"],
            "agentnet_step_redundant_present": agentnet_step_redundant["present"],
            "agentnet_status_step_correct_v": agentnet_status_step["v_measure"],
            "agentnet_repeat_step_redundant_v": agentnet_repeat_redundant["v_measure"],
            "agentreward_operations": agentreward["operations"],
            "agentreward_repeat_looping_v": agentreward_repeat_loop["v_measure"],
            "agentreward_step_error_looping_v": agentreward_step_loop["v_measure"],
            "satraj_operations": satraj["operations"],
            "satraj_phase_action_boundary_f1": satraj_phase_boundary["f1"],
            "satraj_safety_present": satraj_safety["present"],
            "satraj_attack_action_v": satraj_attack_action["v_measure"],
            "source": [
                rel(paths["agentnet_quality"]),
                rel(paths["agentreward_quality"]),
                rel(paths["satraj_quality"]),
            ],
        },
        "reproducibility_and_exchange": {
            "profile_spec_samples": spec["samples"],
            "profile_spec_unique_stacks": spec["unique_stacks"],
            "profile_spec_override_unique_stacks": spec_override["unique_stacks"],
            "trace_converted_operations": trace_convert["operations"],
            "trace_import_samples": trace_import["samples"],
            "trace_import_unique_stacks": trace_import["unique_stacks"],
            "operation_import_samples": operation_import["samples"],
            "operation_import_unique_stacks": operation_import["unique_stacks"],
            "folded_outputs_identical": trace_equivalent,
            "trace_folded_lines": folded_lines(paths["trace_folded"]),
            "operation_folded_lines": folded_lines(paths["operation_folded"]),
            "source": [
                rel(paths["profile_spec"]),
                rel(paths["profile_spec_override"]),
                rel(paths["trace_convert"]),
                rel(paths["trace_import"]),
                rel(paths["operation_import"]),
            ],
        },
    }

    claims = [
        {
            "claim": "C1",
            "verdict": "supported",
            "paper_ready_wording": (
                "The semantic profiler can represent heterogeneous public agent "
                "trajectories and local agent sessions as operations, then profile "
                "them through user-selected operation stacks without hard-coding "
                "prompt/session boundaries."
            ),
            "evidence": [
                "heterogeneous_coverage",
                "recursive_depth",
                "reproducibility_and_exchange",
            ],
            "not_supported": [
                "complete conversion of every public agent benchmark",
                "raw image/video archive profiling",
            ],
        },
        {
            "claim": "C2",
            "verdict": "supported with scoped limits",
            "paper_ready_wording": (
                "Recursive operation stacks recover useful task, phase, action, "
                "human-group, safety, and quality-label views, and expose when a "
                "coarse field is not a valid proxy for a finer oracle."
            ),
            "evidence": [
                "recursive_depth",
                "human_boundaries",
                "quality_and_failure_diagnostics",
            ],
            "not_supported": [
                "perfect intent recovery",
                "single universal stack depth",
                "quality prediction from task outcome alone",
            ],
        },
        {
            "claim": "C3",
            "verdict": "partial",
            "paper_ready_wording": (
                "Label-derived deterministic mappings improve semantic aggregation "
                "on held-out sessions and leave-dataset-out folds; they should be "
                "presented as reproducible mapping/tagging, not as unsupervised "
                "boundary discovery."
            ),
            "evidence": ["mapping_generalization"],
            "not_supported": [
                "fully unsupervised boundary detection",
                "LLM-backed or model-backed boundary inference",
            ],
        },
    ]

    return {
        "schema": "agentsight.paper-claim-synthesis.v1",
        "run_id": "R295",
        "source_window": "R282-R294",
        "provenance": {"input_artifacts_git_tracked_and_clean": True},
        "generated_from": {name: rel(path) for name, path in paths.items()},
        "evidence": evidence,
        "claims": claims,
        "unsupported_final_claims": [
            "The profiler fully discovers latent intent boundaries without labels or rules.",
            "The profiler improves human developer productivity.",
            "Every public agent trajectory dataset can be profiled at full scale without additional engineering.",
        ],
    }


def markdown(synthesis: dict[str, Any]) -> str:
    e = synthesis["evidence"]
    lines = [
        "# R295 Paper Claim Synthesis",
        "",
        "This artifact is generated from tracked R282-R294 result JSON files. It is a paper-claim gate, not a new dataset run.",
        "",
        "## Claim Verdicts",
        "",
        "| Claim | Verdict | Paper-ready wording | Evidence keys | Unsupported wording |",
        "|---|---|---|---|---|",
    ]
    for claim in synthesis["claims"]:
        lines.append(
            "| {claim} | {verdict} | {wording} | {evidence} | {unsupported} |".format(
                claim=claim["claim"],
                verdict=claim["verdict"],
                wording=claim["paper_ready_wording"],
                evidence=", ".join(claim["evidence"]),
                unsupported=", ".join(claim["not_supported"]),
            )
        )
    lines.extend(
        [
            "",
            "## Key Evidence",
            "",
            "- Heterogeneous coverage: {core_datasets} core datasets / {core_operations} operations / {core_unique_stacks} stacks; with ScaleCUA supplement: {supplemental_datasets} datasets / {supplemental_operations} operations / {supplemental_unique_stacks} stacks.".format(
                **e["heterogeneous_coverage"]
            ),
            "- Recursive depth: the same {samples} operations fold from {dataset_unique_stacks} dataset stacks to {phase_unique_stacks} phase stacks, {semantic_unique_stacks} semantic stacks, {action_unique_stacks} action stacks, and {fixed_session_unique_stacks} fixed-session stacks.".format(
                **e["recursive_depth"]
            ),
            "- Mapping generalization: R282 held-out mapping improves compression from {nomap_compression} to {mapped_compression} and unique stacks from {nomap_unique_stacks} to {mapped_unique_stacks}; R285 leave-dataset-out has {leaveout_positive_stack_reduction}/{leaveout_datasets} positive stack-reduction folds and {leaveout_negative_stack_reduction} negative folds.".format(
                **e["mapping_generalization"]
            ),
            "- Human grouped boundaries: OSWorld-Human has {operations} operations, {human_group_present}/{human_group_total} with exact human-group fields, and group-pattern vs human-group boundary F1 {group_pattern_human_group_f1} at precision {group_pattern_human_group_precision}.".format(
                **e["human_boundaries"]
            ),
            "- Quality/failure diagnostics: AgentNet has {agentnet_operations} operations with full step correctness/redundancy fields; AgentRewardBench repeat-signal/looping V-measure is {agentreward_repeat_looping_v} vs step-error/looping {agentreward_step_error_looping_v}; SATraj attack/action V-measure is only {satraj_attack_action_v}, so safety remains a diagnostic field rather than a phase proxy.".format(
                **e["quality_and_failure_diagnostics"]
            ),
            "- Reproducibility/exchange: R293 spec replays {profile_spec_samples} AgentNet samples with {profile_spec_unique_stacks} stacks and a stack override gives {profile_spec_override_unique_stacks}; R294 trace and operation imports both have {trace_import_samples} samples / {trace_import_unique_stacks} stacks and byte-identical folded output is {folded_outputs_identical}.".format(
                **e["reproducibility_and_exchange"]
            ),
            "",
            "## Negative And Scope-Setting Evidence",
            "",
            "- AgentNet task status is a weak proxy for per-step correctness (V-measure {agentnet_status_step_correct_v}); repeat signal is a weak proxy for step redundancy (V-measure {agentnet_repeat_step_redundant_v}).".format(
                **e["quality_and_failure_diagnostics"]
            ),
            "- SATraj attack type is weakly aligned with action taxonomy (V-measure {satraj_attack_action_v}), so attack/safety should be treated as operation fields for filtering and diagnosis, not as inferred phases.".format(
                **e["quality_and_failure_diagnostics"]
            ),
            "- C3 remains partial: current boundary evidence is deterministic mapping/tagging over labeled fields, not unsupervised boundary discovery.",
            "",
            "## Sources",
            "",
        ]
    )
    for key, source in synthesis["generated_from"].items():
        lines.append(f"- `{key}`: `{source}`")
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    args = parse_args()
    out_dir = args.out_dir
    if not out_dir.is_absolute():
        out_dir = ROOT / out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    synthesis = build_synthesis()
    json_path = out_dir / "claim-synthesis.json"
    md_path = out_dir / "claim-synthesis.md"
    json_path.write_text(json.dumps(synthesis, indent=2, sort_keys=True) + "\n")
    md_path.write_text(markdown(synthesis))
    print(
        json.dumps(
            {
                "status": "ok",
                "run_id": synthesis["run_id"],
                "json": rel(json_path),
                "markdown": rel(md_path),
                "claims": len(synthesis["claims"]),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
