#!/usr/bin/env python3
"""Reviewer-facing claim/RQ readiness gate for AgentFlame.

R219 is an audit artifact, not new outcome evidence. It reads already generated
public/research summaries and records which OSDI claims are supported, partial,
or still blocked. It must not read raw agent traces or call any model.
"""

from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent.parent
DEFAULT_OUT_DIR = SCRIPT_DIR / "out" / "claim-readiness-r219"


SOURCE_PATHS = {
    "r170_full_history": "docs/visexp/out/full-history-r170.json",
    "r180_model_benchmarks": "docs/visexp/out/model-benchmarks-r180.json",
    "r131_semantic_ablation": "docs/visexp/out/semantic-ablation-r131.json",
    "r114_live_record": "docs/visexp/out/live-record-r114.json",
    "r182_live_network": "docs/visexp/out/live-network-r182.json",
    "r191_target_network": "docs/visexp/out/live-network-r191.json",
    "r229_exact_lineage_replication": "docs/visexp/out/exact-lineage-replication-r229.json",
    "r230_full_history_lineage": "docs/visexp/out/full-history-lineage-r230/full-history-lineage-r230.json",
    "r231_drift_root_cause": "docs/visexp/out/drift-root-cause-r231/drift-root-cause-r231.json",
    "r232_external_crossrepo": "docs/visexp/out/external-crossrepo-lineage-r232/external-crossrepo-lineage-r232.json",
    "r233_prompt_row_lineage": "docs/visexp/out/prompt-row-lineage-r233/prompt-row-lineage-r233.json",
    "r234_broader_agent_network": "docs/visexp/out/broader-agent-network-lineage-r234/broader-agent-network-lineage-r234.json",
    "r184_weak_accept": "docs/visexp/out/weak-accept-gate-r184.json",
    "r195_human_pipeline": "docs/visexp/out/human-evidence-pipeline-r195.json",
    "r207_launch_readiness": "docs/visexp/out/human-evidence-launch-r207/human-evidence-launch-r207.json",
    "r160_artifact_usability": "docs/visexp/out/artifact-usability-r160.json",
    "r213_display_mode": "docs/visexp/out/display-mode-drilldown-r213/display-mode-drilldown-r213.json",
    "r214_long_tail_control": "docs/visexp/out/long-tail-control-r214/long-tail-control-r214.json",
    "r215_frontend_renderer": "docs/visexp/out/frontend-renderer-mode-r215/frontend-renderer-mode-r215.json",
    "r216_browser_dom": "docs/visexp/out/browser-dom-mode-r216/browser-dom-mode-r216.json",
    "r217_production_react": "docs/visexp/out/production-react-display-r217/production-react-display-r217.json",
    "r218_update_gate": "docs/visexp/out/display-map-update-gate-r218/display-map-update-gate-r218.json",
    "r124_tag_adequacy": "docs/visexp/out/tag-adequacy-results-r124.json",
    "r190_merge_quality": "docs/visexp/out/tag-consolidation-audit-r190/merge-risk-audit-results-r190.json",
    "r203_promotion_quality": "docs/visexp/out/long-tail-promotion-r203/long-tail-promotion-r203.json",
    "r142_user_task_results": "docs/visexp/out/user-task-results.json",
    "r200_community_smoke": "docs/visexp/out/community-smoke-r200.json",
    "r209_display_map": "docs/visexp/out/reversible-display-map-r209/reversible-display-map-r209.json",
    "r211_stack_examples": "docs/visexp/out/stack-examples-r211/stack-examples-r211.json",
    "r212_display_ablation": "docs/visexp/out/display-compaction-ablation-r212/display-compaction-ablation-r212.json",
    "r223_projection_tradeoff": "docs/visexp/out/projection-tradeoff-r223/projection-tradeoff-r223.json",
    "r225_prompt_span_duration": "docs/visexp/out/prompt-span-duration-r225/prompt-span-duration-r225.json",
    "r220_fresh_clone_agentpprof": "docs/visexp/out/fresh-clone-agentpprof-r220/fresh-clone-agentpprof-r220.json",
}

C4_CONTROLLED_LINEAGE_VERDICT = "supported_for_controlled_live_lineage_suites"


CLAIM_FIELDS = [
    "claim",
    "verdict",
    "evidence_level",
    "primary_evidence",
    "blocking_gap",
    "next_gate",
]

RQ_FIELDS = [
    "rq",
    "verdict",
    "evidence_level",
    "primary_evidence",
    "falsifier_remaining",
    "next_gate",
]

NEXT_FIELDS = [
    "priority",
    "run_id",
    "claim",
    "block",
    "purpose",
    "command_or_input",
    "oracle",
    "result_path",
]


def repo_path(relative: str) -> Path:
    return REPO_ROOT / relative


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def read_json_required(relative: str) -> dict[str, Any]:
    path = repo_path(relative)
    if not path.exists():
        raise FileNotFoundError(f"required R219 source artifact is missing: {relative}")
    return json.loads(path.read_text(encoding="utf-8"))


def as_int(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def required_field(mapping: dict[str, Any], key: str, artifact: str) -> Any:
    if key not in mapping:
        raise KeyError(f"{artifact} is missing required field {key!r}")
    return mapping[key]


def required_int(mapping: dict[str, Any], key: str, artifact: str) -> int:
    value = required_field(mapping, key, artifact)
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{artifact}.{key} must be an integer, got {value!r}") from exc


def percent(numerator: int, denominator: int) -> float:
    if denominator <= 0:
        return 0.0
    return round(100.0 * numerator / denominator, 3)


def c4_lineage_supported(status: dict[str, Any]) -> bool:
    r114_ok = (
        status["r114_status"] == "ok"
        and float(status["r114_precision_pct"]) >= 98.0
        and float(status["r114_recall_pct"]) >= 95.0
        and as_int(status["r114_negative_observed"]) > 0
        and as_int(status["r114_negative_joined"]) == 0
    )
    r191_target = as_int(status["r191_target_network_effect_events"])
    r191_joined = as_int(status["r191_joined_target_network_effect_events"])
    r191_ok = (
        status["r191_status"] == "ok"
        and r191_target > 0
        and r191_joined == r191_target
        and as_int(status["r191_negative_observed"]) > 0
        and as_int(status["r191_negative_joined"]) == 0
        and float(status["r191_precision_pct"]) >= 98.0
        and float(status["r191_recall_pct"]) >= 95.0
    )
    r229_ok = (
        status["r229_status"] == "ok"
        and as_int(status["r229_tasks"]) >= 5
        and as_int(status["r229_in_scope_effect_events"]) > 0
        and as_int(status["r229_negative_observed"]) > 0
        and as_int(status["r229_negative_joined"]) == 0
        and float(status["r229_precision_pct"]) >= 98.0
        and float(status["r229_recall_pct"]) >= 95.0
    )
    r232_ok = (
        status["r232_status"] == "ok"
        and bool(status["r232_external_crossrepo_supported"])
        and bool(status["r232_normal_gate"])
        and bool(status["r232_network_gate"])
        and as_int(status["r232_in_scope_effect_events"]) > 0
        and as_int(status["r232_target_network_effect_events"]) > 0
        and as_int(status["r232_joined_target_network_effect_events"])
        == as_int(status["r232_target_network_effect_events"])
        and as_int(status["r232_negative_observed"]) > 0
        and as_int(status["r232_negative_joined"]) == 0
        and float(status["r232_precision_pct"]) >= 98.0
        and float(status["r232_recall_pct"]) >= 95.0
    )
    r234_ok = (
        status["r234_status"] == "ok"
        and bool(status["r234_broader_agent_network_supported"])
        and bool(status["r234_agent_family_gate"])
        and bool(status["r234_network_gate"])
        and as_int(status["r234_in_scope_effect_events"]) > 0
        and as_int(status["r234_target_network_effect_events"]) > 0
        and as_int(status["r234_joined_target_network_effect_events"])
        == as_int(status["r234_target_network_effect_events"])
        and as_int(status["r234_negative_observed"]) > 0
        and as_int(status["r234_negative_joined"]) == 0
        and float(status["r234_precision_pct"]) >= 98.0
        and float(status["r234_recall_pct"]) >= 95.0
    )
    return r114_ok and r191_ok and r229_ok and r232_ok and r234_ok


def artifact_statuses(artifacts: dict[str, dict[str, Any]]) -> dict[str, Any]:
    r170 = artifacts["r170_full_history"]
    r180 = artifacts["r180_model_benchmarks"]
    r114 = artifacts["r114_live_record"]
    r182 = artifacts["r182_live_network"]
    r191 = artifacts["r191_target_network"]
    r229 = artifacts["r229_exact_lineage_replication"]
    r230 = artifacts["r230_full_history_lineage"]
    r231 = artifacts["r231_drift_root_cause"]
    r232 = artifacts["r232_external_crossrepo"]
    r233 = artifacts["r233_prompt_row_lineage"]
    r234 = artifacts["r234_broader_agent_network"]
    r184 = artifacts["r184_weak_accept"]
    r195 = artifacts["r195_human_pipeline"]
    r160 = artifacts["r160_artifact_usability"]
    r213 = artifacts["r213_display_mode"]
    r214 = artifacts["r214_long_tail_control"]
    r215 = artifacts["r215_frontend_renderer"]
    r216 = artifacts["r216_browser_dom"]
    r217 = artifacts["r217_production_react"]
    r218 = artifacts["r218_update_gate"]
    r223 = artifacts["r223_projection_tradeoff"]
    r225 = artifacts["r225_prompt_span_duration"]
    r220 = artifacts["r220_fresh_clone_agentpprof"]
    r124 = artifacts["r124_tag_adequacy"]
    r190 = artifacts["r190_merge_quality"]
    r203 = artifacts["r203_promotion_quality"]
    r142 = artifacts["r142_user_task_results"]

    r114_aggregate = r114.get("aggregate") or {}
    r114_tp = as_int(r114_aggregate.get("true_positives"))
    r114_fp = as_int(r114_aggregate.get("false_positives"))
    r114_fn = as_int(r114_aggregate.get("false_negatives"))
    r114_negative_joined = as_int(r114_aggregate.get("negative_joined_effect_events"))
    r114_negative_observed = as_int(r114_aggregate.get("negative_effect_events_observed"))
    r191_aggregate = r191.get("aggregate") or {}
    r229_aggregate = r229.get("aggregate") or {}
    r230_gate = r230.get("claim_gate") or {}
    r230_raw = r230.get("raw_event_index_audit") or {}
    r230_folded = r230.get("folded_audit") or {}
    r231_gate = r231.get("claim_gate") or {}
    r231_summary = r231.get("summary") or {}
    r231_display = r231.get("display_projection") or {}
    r232_aggregate = r232.get("aggregate") or {}
    r232_normal = r232.get("normal_aggregate") or {}
    r232_network = r232.get("network_aggregate") or {}
    r233_gate = r233.get("claim_gate") or {}
    r233_summary = r233.get("summary") or {}
    r234_aggregate = r234.get("aggregate") or {}
    r234_agent = r234.get("agent_aggregate") or {}
    r234_network = r234.get("network_aggregate") or {}

    r170_summary = r170.get("summary") or {}
    r180_aggregate = r180.get("aggregate") or {}
    r217_summary = r217.get("summary") or {}
    r218_summary = r218.get("summary") or {}
    r184_c5 = r184.get("c5_user_utility") or {}
    r184_c6 = r184.get("c6_tag_adequacy") or {}
    r223_rows = r223.get("rows") or []
    r223_prompt_only = next(
        (
            row
            for row in r223_rows
            if row.get("projection_family") == "semantic-axis"
            and row.get("variant") == "prompt-only"
        ),
        {},
    )
    r223_no_semantic = next(
        (
            row
            for row in r223_rows
            if row.get("projection_family") == "semantic-axis"
            and row.get("variant") == "no-semantic"
        ),
        {},
    )

    return {
        "r170_sessions": as_int(r170_summary.get("session_count")),
        "r170_system_observations": as_int(r170_summary.get("system_observations")),
        "r170_semantic_system_stacks": as_int(r170_summary.get("semantic_system_stacks")),
        "r180_total_runs": as_int(r180_aggregate.get("total_runs")),
        "r180_ok_runs": as_int(r180_aggregate.get("ok_runs")),
        "r180_exact_stable_fragments": as_int(r180_aggregate.get("exact_stable_fragments")),
        "r180_fragment_count": as_int(r180_aggregate.get("fragment_count")),
        "r114_status": r114.get("status"),
        "r114_precision_pct": percent(r114_tp, r114_tp + r114_fp),
        "r114_recall_pct": percent(r114_tp, r114_tp + r114_fn),
        "r114_negative_joined": r114_negative_joined,
        "r114_negative_observed": r114_negative_observed,
        "r182_status": r182.get("status"),
        "r191_status": r191.get("status"),
        "r191_target_network_effect_events": as_int(r191_aggregate.get("target_network_effect_events")),
        "r191_joined_target_network_effect_events": as_int(
            r191_aggregate.get("joined_target_network_effect_events")
        ),
        "r191_negative_joined": as_int(r191_aggregate.get("negative_joined_effect_events")),
        "r191_negative_observed": as_int(r191_aggregate.get("negative_effect_events_observed")),
        "r191_precision_pct": r191_aggregate.get("precision_pct", "n/a"),
        "r191_recall_pct": r191_aggregate.get("recall_pct", "n/a"),
        "r229_status": r229.get("status"),
        "r229_tasks": as_int(r229_aggregate.get("tasks")),
        "r229_joined_effect_events": as_int(r229_aggregate.get("joined_effect_events")),
        "r229_effect_events": as_int(r229_aggregate.get("effect_events")),
        "r229_in_scope_effect_events": as_int(r229_aggregate.get("in_scope_effect_events")),
        "r229_out_of_scope_effect_events": as_int(r229_aggregate.get("out_of_scope_effect_events")),
        "r229_negative_joined": as_int(r229_aggregate.get("negative_joined_effect_events")),
        "r229_negative_observed": as_int(r229_aggregate.get("negative_effect_events_observed")),
        "r229_raw_join_pct": r229_aggregate.get("raw_join_pct", "n/a"),
        "r229_precision_pct": r229_aggregate.get("precision_pct", "n/a"),
        "r229_recall_pct": r229_aggregate.get("recall_pct", "n/a"),
        "r230_status": r230.get("status"),
        "r230_system_effect_history_projection_supported": bool(
            r230_gate.get("system_effect_history_projection_supported")
        ),
        "r230_strict_full_history_supported": bool(
            r230_gate.get("strict_full_history_semantic_lineage_supported")
        ),
        "r230_folded_total_weight": required_int(r230_folded, "total_weight", "R230.folded_audit"),
        "r230_missing_frame_weight": required_int(r230_folded, "missing_total_weight", "R230.folded_audit"),
        "r230_prompt_rows": required_int(r230_raw, "prompt_rows", "R230.raw_event_index_audit"),
        "r230_unique_prompt_indexes": required_int(r230_raw, "unique_prompt_indexes", "R230.raw_event_index_audit"),
        "r230_duplicate_prompt_index_rows": required_int(
            r230_raw, "duplicate_prompt_index_rows", "R230.raw_event_index_audit"
        ),
        "r230_sessions_with_duplicate_prompt_indexes": required_int(
            r230_raw, "sessions_with_duplicate_prompt_indexes", "R230.raw_event_index_audit"
        ),
        "r230_tool_prompt_index_weight_pct": required_field(
            r230_raw, "tool_valid_prompt_index_weight_pct", "R230.raw_event_index_audit"
        ),
        "r230_tool_ambiguous_prompt_index_weight": required_int(
            r230_raw, "tool_ambiguous_prompt_index_weight", "R230.raw_event_index_audit"
        ),
        "r230_tool_ambiguous_prompt_index_weight_pct": required_field(
            r230_raw, "tool_ambiguous_prompt_index_weight_pct", "R230.raw_event_index_audit"
        ),
        "r230_tool_prompt_tag_mismatch_weight": required_int(
            r230_raw, "tool_prompt_tag_mismatch_weight", "R230.raw_event_index_audit"
        ),
        "r230_tool_prompt_tag_mismatch_weight_pct": required_field(
            r230_raw, "tool_prompt_tag_mismatch_weight_pct", "R230.raw_event_index_audit"
        ),
        "r230_llm_prompt_tag_mismatch_events": required_int(
            r230_raw, "llm_prompt_tag_mismatch_events", "R230.raw_event_index_audit"
        ),
        "r230_llm_prompt_tag_mismatch_event_pct": required_field(
            r230_raw, "llm_prompt_tag_mismatch_event_pct", "R230.raw_event_index_audit"
        ),
        "r231_status": r231.get("status"),
        "r231_display_projection_exact": bool(
            r231_gate.get("display_projection_matches_event_local_prompt_tags")
        ),
        "r231_r230_reproduced": bool(r231_gate.get("r230_field_index_drift_reproduced")),
        "r231_field_drift_localized": bool(
            r231_gate.get("field_index_drift_localized_to_duplicate_index_sessions")
        ),
        "r231_strict_prompt_row_lineage_supported": bool(
            r231_gate.get("strict_prompt_row_lineage_supported")
        ),
        "r231_external_crossrepo_supported": bool(
            r231_gate.get("external_crossrepo_live_lineage_supported")
        ),
        "r231_display_event_weight": required_int(
            r231_display, "event_total_weight", "R231.display_projection"
        ),
        "r231_display_folded_weight": required_int(
            r231_display, "folded_total_weight", "R231.display_projection"
        ),
        "r231_field_tool_mismatch_weight": required_int(
            r231_summary, "field_tool_mismatch_weight", "R231.summary"
        ),
        "r231_field_tool_mismatch_pct": required_field(
            r231_summary, "field_tool_mismatch_pct", "R231.summary"
        ),
        "r231_field_llm_mismatch_events": required_int(
            r231_summary, "field_llm_mismatch_events", "R231.summary"
        ),
        "r231_field_llm_mismatch_pct": required_field(
            r231_summary, "field_llm_mismatch_pct", "R231.summary"
        ),
        "r231_position_tool_mismatch_weight": required_int(
            r231_summary, "position_tool_mismatch_weight", "R231.summary"
        ),
        "r231_position_tool_mismatch_pct": required_field(
            r231_summary, "position_tool_mismatch_pct", "R231.summary"
        ),
        "r231_position_llm_mismatch_events": required_int(
            r231_summary, "position_llm_mismatch_events", "R231.summary"
        ),
        "r231_position_llm_mismatch_pct": required_field(
            r231_summary, "position_llm_mismatch_pct", "R231.summary"
        ),
        "r231_duplicate_prompt_index_rows": required_int(
            r231_summary, "duplicate_prompt_index_rows", "R231.summary"
        ),
        "r231_sessions_with_duplicate_prompt_indexes": required_int(
            r231_summary, "sessions_with_duplicate_prompt_indexes", "R231.summary"
        ),
        "r231_field_unique_tool_mismatch_weight": required_int(
            r231_summary, "field_mismatch_unique_session_tool_weight", "R231.summary"
        ),
        "r231_field_unique_llm_mismatch_events": required_int(
            r231_summary, "field_mismatch_unique_session_llm_events", "R231.summary"
        ),
        "r232_status": r232.get("status"),
        "r232_external_crossrepo_supported": bool(r232.get("external_crossrepo_lineage_supported")),
        "r232_normal_gate": bool(r232.get("normal_gate")),
        "r232_network_gate": bool(r232.get("network_gate")),
        "r232_tasks": required_int(r232_aggregate, "tasks", "R232.aggregate"),
        "r232_normal_tasks": required_int(r232_aggregate, "normal_tasks", "R232.aggregate"),
        "r232_network_tasks": required_int(r232_aggregate, "network_tasks", "R232.aggregate"),
        "r232_in_scope_effect_events": required_int(
            r232_aggregate, "in_scope_effect_events", "R232.aggregate"
        ),
        "r232_joined_effect_events": required_int(r232_aggregate, "joined_effect_events", "R232.aggregate"),
        "r232_effect_events": required_int(r232_aggregate, "effect_events", "R232.aggregate"),
        "r232_target_network_effect_events": required_int(
            r232_aggregate, "target_network_effect_events", "R232.aggregate"
        ),
        "r232_joined_target_network_effect_events": required_int(
            r232_aggregate, "joined_target_network_effect_events", "R232.aggregate"
        ),
        "r232_negative_observed": required_int(
            r232_aggregate, "negative_effect_events_observed", "R232.aggregate"
        ),
        "r232_negative_joined": required_int(
            r232_aggregate, "negative_joined_effect_events", "R232.aggregate"
        ),
        "r232_precision_pct": required_field(r232_aggregate, "precision_pct", "R232.aggregate"),
        "r232_recall_pct": required_field(r232_aggregate, "recall_pct", "R232.aggregate"),
        "r232_normal_in_scope_effect_events": required_int(
            r232_normal, "in_scope_effect_events", "R232.normal_aggregate"
        ),
        "r232_normal_negative_observed": required_int(
            r232_normal, "negative_effect_events_observed", "R232.normal_aggregate"
        ),
        "r232_network_target_actions": required_field(
            r232_network, "target_network_actions", "R232.network_aggregate"
        ),
        "r233_status": r233.get("status"),
        "r233_normalized_semantic_supported": bool(
            r233_gate.get("normalized_semantic_prompt_row_lineage_supported")
        ),
        "r233_strict_prompt_row_identity_supported": bool(
            r233_gate.get("strict_prompt_row_identity_supported")
        ),
        "r233_duplicate_indexes_non_keyed": bool(
            r233_gate.get("duplicate_prompt_indexes_explicitly_non_keyed")
        ),
        "r233_display_projection_exact": bool(
            r233_gate.get("display_projection_matches_event_local_prompt_tags")
        ),
        "r233_prompt_rows": required_int(r233_summary, "prompt_rows", "R233.summary"),
        "r233_duplicate_prompt_index_rows": required_int(
            r233_summary, "duplicate_prompt_index_rows", "R233.summary"
        ),
        "r233_sessions_with_duplicate_prompt_indexes": required_int(
            r233_summary, "sessions_with_duplicate_prompt_indexes", "R233.summary"
        ),
        "r233_duplicate_same_tag_groups": required_int(
            r233_summary, "duplicate_same_tag_groups", "R233.summary"
        ),
        "r233_duplicate_mixed_tag_groups": required_int(
            r233_summary, "duplicate_mixed_tag_groups", "R233.summary"
        ),
        "r233_legacy_field_tool_mismatch_weight": required_int(
            r233_summary, "legacy_field_tool_mismatch_weight", "R233.summary"
        ),
        "r233_legacy_field_llm_mismatch_events": required_int(
            r233_summary, "legacy_field_llm_mismatch_events", "R233.summary"
        ),
        "r233_normalized_tool_mismatch_weight": required_int(
            r233_summary, "normalized_tool_mismatch_weight", "R233.summary"
        ),
        "r233_normalized_tool_mismatch_pct": required_field(
            r233_summary, "normalized_tool_mismatch_pct", "R233.summary"
        ),
        "r233_normalized_llm_mismatch_events": required_int(
            r233_summary, "normalized_llm_mismatch_events", "R233.summary"
        ),
        "r233_normalized_llm_mismatch_pct": required_field(
            r233_summary, "normalized_llm_mismatch_pct", "R233.summary"
        ),
        "r233_same_tag_identity_ambiguous_tool_weight": required_int(
            r233_summary, "duplicate_same_tag_identity_ambiguous_tool_weight", "R233.summary"
        ),
        "r233_same_tag_identity_ambiguous_llm_events": required_int(
            r233_summary, "duplicate_same_tag_identity_ambiguous_llm_events", "R233.summary"
        ),
        "r234_status": r234.get("status"),
        "r234_broader_agent_network_supported": bool(r234.get("broader_agent_network_lineage_supported")),
        "r234_agent_family_gate": bool(r234.get("agent_family_gate")),
        "r234_network_gate": bool(r234.get("network_gate")),
        "r234_tasks": required_int(r234_aggregate, "tasks", "R234.aggregate"),
        "r234_agent_tasks": required_int(r234_aggregate, "agent_tasks", "R234.aggregate"),
        "r234_network_tasks": required_int(r234_aggregate, "network_tasks", "R234.aggregate"),
        "r234_in_scope_effect_events": required_int(
            r234_aggregate, "in_scope_effect_events", "R234.aggregate"
        ),
        "r234_target_network_effect_events": required_int(
            r234_aggregate, "target_network_effect_events", "R234.aggregate"
        ),
        "r234_joined_target_network_effect_events": required_int(
            r234_aggregate, "joined_target_network_effect_events", "R234.aggregate"
        ),
        "r234_negative_observed": required_int(
            r234_aggregate, "negative_effect_events_observed", "R234.aggregate"
        ),
        "r234_negative_joined": required_int(
            r234_aggregate, "negative_joined_effect_events", "R234.aggregate"
        ),
        "r234_precision_pct": required_field(r234_aggregate, "precision_pct", "R234.aggregate"),
        "r234_recall_pct": required_field(r234_aggregate, "recall_pct", "R234.aggregate"),
        "r234_agent_families": required_field(r234_agent, "agents", "R234.agent_aggregate"),
        "r234_network_probes": required_field(r234_network, "probes", "R234.network_aggregate"),
        "r234_network_target_actions": required_field(
            r234_network, "target_network_actions", "R234.network_aggregate"
        ),
        "r184_status": r184.get("status"),
        "r195_status": r195.get("status"),
        "r160_status": r160.get("status"),
        "r213_status": r213.get("status"),
        "r214_status": r214.get("status"),
        "r215_status": r215.get("status"),
        "r216_status": r216.get("status"),
        "r142_status": r142.get("status"),
        "r124_status": r124.get("status"),
        "r190_status": r190.get("status"),
        "r203_status": r203.get("status"),
        "c5_supported": bool(r184_c5.get("supported")),
        "c5_participants": as_int(r184_c5.get("participant_count")),
        "c5_responses": as_int(r184_c5.get("response_count")),
        "c6_supported": bool(r184_c6.get("supported")),
        "c6_final_labels": as_int(r184_c6.get("final_label_count")),
        "r217_display_buckets": as_int(r217_summary.get("visible_bucket_count")),
        "r217_support": as_int(r217_summary.get("visible_total_support")),
        "r218_accepted_diff_rows": as_int(r218_summary.get("accepted_diff_rows")),
        "r218_rejected_rows": as_int(r218_summary.get("rejected_rows")),
        "r218_canonical_map_updated": bool(r218_summary.get("canonical_map_updated")),
        "r223_no_semantic_mixed_pct": r223_no_semantic.get("mixed_weight_pct", "n/a"),
        "r223_prompt_only_mixed_pct": r223_prompt_only.get("mixed_weight_pct", "n/a"),
        "r223_prompt_only_residual_pct": r223_prompt_only.get("mixed_residual_pct", "n/a"),
        "r225_prompt_spans": as_int(r225.get("prompt_spans_total")),
        "r225_duration_hours": r225.get("total_prompt_duration_h", "n/a"),
        "r225_covered_effect_total": as_int(r225.get("covered_effect_total_weight")),
        "r225_effect_total": as_int(r225.get("effect_total_weight")),
        "r225_covered_effect_share_pct": r225.get("covered_effect_share_pct", "n/a"),
        "r225_top10_overlap": as_int(r225.get("top10_overlap_count")),
        "r225_spearman": r225.get("spearman_rank_correlation", "n/a"),
        "r225_true_tool_or_llm_duration_supported": bool(r225.get("true_tool_or_llm_duration_supported")),
        "r220_status": r220.get("status"),
        "r220_tasks_samples": as_int((r220.get("agentpprof") or {}).get("tasks", {}).get("samples")),
        "r220_tools_samples": as_int((r220.get("agentpprof") or {}).get("tools", {}).get("samples")),
        "r220_tokens_samples": as_int((r220.get("agentpprof") or {}).get("tokens", {}).get("samples")),
        "r220_files_samples": as_int((r220.get("agentpprof") or {}).get("files", {}).get("samples")),
        "r220_network_samples": as_int((r220.get("agentpprof") or {}).get("network", {}).get("samples")),
        "r220_pprof_readback": bool((r220.get("gates") or {}).get("pprof_readback")),
        "r220_expected_stacks": bool((r220.get("gates") or {}).get("fixture_projection_expected_stacks")),
        "r220_no_real_agent_history_reads": bool((r220.get("gates") or {}).get("no_real_agent_history_reads")),
        "r220_no_llm_calls": bool((r220.get("gates") or {}).get("no_llm_calls")),
    }


def claim_rows(status: dict[str, Any]) -> list[dict[str, str]]:
    c5_missing = status["c5_participants"] == 0 or status["c5_responses"] == 0
    c6_missing = status["c6_final_labels"] == 0
    c4_ok = c4_lineage_supported(status)
    return [
        {
            "claim": "C1 semantic folded stacks over real histories",
            "verdict": "supported",
            "evidence_level": "mechanism/full-local-history",
            "primary_evidence": (
                f"R170: {status['r170_sessions']} sessions, "
                f"{status['r170_system_observations']} system observations, "
                f"{status['r170_semantic_system_stacks']} semantic system stacks"
            ),
            "blocking_gap": "multi-repo generalization and public package remain C7 scope",
            "next_gate": "rerun only after parser/tagger changes",
        },
        {
            "claim": "C2 local one-word tagging feasibility",
            "verdict": "supported_for_syntax_latency",
            "evidence_level": "local-small-model-benchmark",
            "primary_evidence": (
                f"R180: {status['r180_ok_runs']}/{status['r180_total_runs']} valid outputs, "
                f"{status['r180_exact_stable_fragments']}/{status['r180_fragment_count']} exact-stable fragments"
            ),
            "blocking_gap": "human semantic adequacy is C6, not C2",
            "next_gate": "collect R124 labels before claiming adequacy",
        },
        {
            "claim": "C3 semantic partitioning and display mechanics",
            "verdict": "supported_as_mechanism",
            "evidence_level": "ablation/display-contract",
            "primary_evidence": (
                f"R223: no-semantic mixed {status['r223_no_semantic_mixed_pct']}%, "
                f"prompt-only mixed/residual {status['r223_prompt_only_mixed_pct']}%/"
                f"{status['r223_prompt_only_residual_pct']}%; R225: "
                f"{status['r225_prompt_spans']} prompt spans, {status['r225_duration_hours']} h, "
                f"covered effects {status['r225_covered_effect_total']}/"
                f"{status['r225_effect_total']} ({status['r225_covered_effect_share_pct']}%), "
                f"top-10 duration/effect overlap {status['r225_top10_overlap']}/10, "
                f"Spearman {status['r225_spearman']}; R217/R218 display/update gates pass"
            ),
            "blocking_gap": "visual drilldown, developer utility, true tool/LLM spans, and merge quality are not proven",
            "next_gate": "C5 participant study and R190/R203 human review labels",
        },
        {
            "claim": "C4 exact semantic-effect lineage",
            "verdict": C4_CONTROLLED_LINEAGE_VERDICT if c4_ok else "partial_or_failed",
            "evidence_level": (
                "controlled-live-lineage-plus-generated-history-audit"
                if c4_ok
                else "insufficient-controlled-live-lineage-or-history-audit"
            ),
            "primary_evidence": (
                f"Live lineage: R114 status {status['r114_status']}: precision {status['r114_precision_pct']}%, "
                f"recall {status['r114_recall_pct']}%, negative joins "
                f"{status['r114_negative_joined']}/{status['r114_negative_observed']}; "
                f"R182 network status {status['r182_status']}; R191 status {status['r191_status']}: "
                f"target network {status['r191_joined_target_network_effect_events']}/"
                f"{status['r191_target_network_effect_events']} joined, negative joins "
                f"{status['r191_negative_joined']}/{status['r191_negative_observed']}, "
                f"precision/recall {status['r191_precision_pct']}%/{status['r191_recall_pct']}%; "
                f"R229 status {status['r229_status']}: {status['r229_tasks']} tasks, "
                f"in-scope effects {status['r229_in_scope_effect_events']}, negative joins "
                f"{status['r229_negative_joined']}/{status['r229_negative_observed']}, "
                f"precision/recall {status['r229_precision_pct']}%/{status['r229_recall_pct']}%; "
                f"R232 status {status['r232_status']}: external controlled tasks "
                f"{status['r232_tasks']} ({status['r232_normal_tasks']} normal, "
                f"{status['r232_network_tasks']} network), in-scope effects "
                f"{status['r232_in_scope_effect_events']}, target network "
                f"{status['r232_joined_target_network_effect_events']}/"
                f"{status['r232_target_network_effect_events']} joined, negative joins "
                f"{status['r232_negative_joined']}/{status['r232_negative_observed']}, "
                f"precision/recall {status['r232_precision_pct']}%/{status['r232_recall_pct']}%, "
                f"normal/network gates {str(status['r232_normal_gate']).lower()}/"
                f"{str(status['r232_network_gate']).lower()}; "
                f"R234 status {status['r234_status']}: {status['r234_agent_tasks']} Claude-family "
                f"agent task(s), {status['r234_network_tasks']} Codex HTTP-network probe(s), "
                f"in-scope effects {status['r234_in_scope_effect_events']}, target network "
                f"{status['r234_joined_target_network_effect_events']}/"
                f"{status['r234_target_network_effect_events']} joined, negative joins "
                f"{status['r234_negative_joined']}/{status['r234_negative_observed']}, "
                f"precision/recall {status['r234_precision_pct']}%/{status['r234_recall_pct']}%; "
                f"Generated-history audit: "
                f"R230 status {status['r230_status']}: full-history projection "
                f"{str(status['r230_system_effect_history_projection_supported']).lower()}, "
                f"folded weight {status['r230_folded_total_weight']}, missing frame weight "
                f"{status['r230_missing_frame_weight']}, tool prompt-index coverage "
                f"{status['r230_tool_prompt_index_weight_pct']}%, duplicate prompt-index rows "
                f"{status['r230_duplicate_prompt_index_rows']}, prompt-tag drift "
                f"{status['r230_tool_prompt_tag_mismatch_weight']} weight "
                f"({status['r230_tool_prompt_tag_mismatch_weight_pct']}%), LLM drift "
                f"{status['r230_llm_prompt_tag_mismatch_events']} events "
                f"({status['r230_llm_prompt_tag_mismatch_event_pct']}%), strict full-history "
                f"{str(status['r230_strict_full_history_supported']).lower()}; "
                f"R231 status {status['r231_status']}: display projection event/folded weights "
                f"{status['r231_display_event_weight']}/{status['r231_display_folded_weight']} exact "
                f"{str(status['r231_display_projection_exact']).lower()}, R230 drift reproduced "
                f"{str(status['r231_r230_reproduced']).lower()}, field-index drift localized "
                f"{str(status['r231_field_drift_localized']).lower()}, unique-index field drift "
                f"{status['r231_field_unique_tool_mismatch_weight']} tool weight/"
                f"{status['r231_field_unique_llm_mismatch_events']} LLM events, strict prompt-row lineage "
                f"{str(status['r231_strict_prompt_row_lineage_supported']).lower()}, external cross-repo "
                f"{str(status['r231_external_crossrepo_supported']).lower()}; "
                f"R233 status {status['r233_status']}: normalized semantic prompt-row lineage "
                f"{str(status['r233_normalized_semantic_supported']).lower()}, legacy drift "
                f"{status['r233_legacy_field_tool_mismatch_weight']} tool weight/"
                f"{status['r233_legacy_field_llm_mismatch_events']} LLM events -> normalized drift "
                f"{status['r233_normalized_tool_mismatch_weight']} tool weight "
                f"({status['r233_normalized_tool_mismatch_pct']}%)/"
                f"{status['r233_normalized_llm_mismatch_events']} LLM events "
                f"({status['r233_normalized_llm_mismatch_pct']}%), duplicate rows "
                f"{status['r233_duplicate_prompt_index_rows']} explicitly non-keyed, strict row identity "
                f"{str(status['r233_strict_prompt_row_identity_supported']).lower()}"
            ),
            "blocking_gap": (
                "strict prompt-row identity for same-tag duplicate rows, raw-socket and Claude-launched target-network workloads, arbitrary repositories, and more agent families remain partial"
                if c4_ok
                else "R114/R191/R229 lineage gates did not all pass; rerun controlled lineage before broader replication"
            ),
            "next_gate": (
                "run raw-socket and Claude-launched target-network lineage replication; keep duplicate prompt-row identity non-keyed"
                if c4_ok
                else "rerun R114, R191, and R229, requiring target rows > 0, all joined, and negative joins = 0"
            ),
        },
        {
            "claim": "C5 developer utility",
            "verdict": "unsupported" if c5_missing else "partial_or_failed",
            "evidence_level": "launch_ready_no_outcomes",
            "primary_evidence": (
                f"R184/R195: {status['c5_participants']} participants, "
                f"{status['c5_responses']} responses, pipeline {status['r195_status']}"
            ),
            "blocking_gap": "real participant responses are missing",
            "next_gate": "collect and score R142 pilot responses through R195",
        },
        {
            "claim": "C6 tag adequacy and merge/promotion quality",
            "verdict": "partial_syntax_stability_only" if c6_missing else "partial_or_failed",
            "evidence_level": "protocol_ready_no_human_labels",
            "primary_evidence": (
                f"R124 {status['r124_status']}, R190 {status['r190_status']}, "
                f"R203 {status['r203_status']}, final adequacy labels {status['c6_final_labels']}"
            ),
            "blocking_gap": "independent adequacy, merge-risk, and promotion labels are missing",
            "next_gate": "collect R124/R190/R203 paired labels and score through R195",
        },
        {
            "claim": "C7 community/open-source usefulness",
            "verdict": "partial",
            "evidence_level": "local-public-safe-plus-fresh-clone-smoke",
            "primary_evidence": (
                "R160 fixed-session smoke and R200 generated-fixture smoke pass; "
                f"R220 fresh-clone agentpprof {status['r220_status']}: "
                f"tasks/tools/tokens/files/network samples "
                f"{status['r220_tasks_samples']}/{status['r220_tools_samples']}/"
                f"{status['r220_tokens_samples']}/{status['r220_files_samples']}/"
                f"{status['r220_network_samples']}, pprof readback "
                f"{str(status['r220_pprof_readback']).lower()}, "
                f"expected stacks {str(status['r220_expected_stacks']).lower()}, "
                f"no real agent-history reads {str(status['r220_no_real_agent_history_reads']).lower()}"
            ),
            "blocking_gap": "no external-machine run, real-history public sanitization audit, or external developer feedback",
            "next_gate": "external-machine fresh clone plus real-report sanitization and developer-feedback audit",
        },
    ]


def rq_rows(status: dict[str, Any]) -> list[dict[str, str]]:
    c4_ok = c4_lineage_supported(status)
    return [
        {
            "rq": "RQ1 feasibility/cost",
            "verdict": "supported",
            "evidence_level": "full-history plus local model benchmark",
            "primary_evidence": f"R170 full run and R180 {status['r180_ok_runs']}/{status['r180_total_runs']} valid model outputs",
            "falsifier_remaining": "parser/tagger changes could invalidate the run",
            "next_gate": "rerun after implementation changes only",
        },
        {
            "rq": "RQ2 semantic partitioning",
            "verdict": "supported_as_mechanism",
            "evidence_level": "ablation plus display artifacts",
            "primary_evidence": "R131/R211 show baseline collapse; R209-R218 show reversible display mechanics",
            "falsifier_remaining": "developer tasks may show no practical benefit",
            "next_gate": "R142 C5 outcomes",
        },
        {
            "rq": "RQ3 exact lineage",
            "verdict": C4_CONTROLLED_LINEAGE_VERDICT if c4_ok else "partial_or_failed",
            "evidence_level": (
                "controlled live AgentSight suite plus generated-history audit"
                if c4_ok
                else "insufficient controlled live suite or generated-history audit"
            ),
            "primary_evidence": (
                f"Live lineage: R114 precision {status['r114_precision_pct']}%, recall {status['r114_recall_pct']}%; "
                f"R191 target network {status['r191_joined_target_network_effect_events']}/"
                f"{status['r191_target_network_effect_events']} joined; "
                f"R229 {status['r229_tasks']} controlled multi-workspace tasks, "
                f"{status['r229_in_scope_effect_events']} in-scope effects; "
                f"R232 external {status['r232_tasks']} tasks, "
                f"{status['r232_in_scope_effect_events']} in-scope effects, target network "
                f"{status['r232_joined_target_network_effect_events']}/"
                f"{status['r232_target_network_effect_events']} joined, negative joins "
                f"{status['r232_negative_joined']}/{status['r232_negative_observed']}; "
                f"R234 {status['r234_agent_tasks']} Claude-family agent task(s), "
                f"{status['r234_network_tasks']} Codex HTTP-network probe(s), "
                f"{status['r234_in_scope_effect_events']} in-scope effects, target network "
                f"{status['r234_joined_target_network_effect_events']}/"
                f"{status['r234_target_network_effect_events']} joined, negative joins "
                f"{status['r234_negative_joined']}/{status['r234_negative_observed']}; "
                f"Generated-history audit: "
                f"R230 full-history projection weight {status['r230_folded_total_weight']} "
                f"with duplicate prompt-index rows {status['r230_duplicate_prompt_index_rows']} "
                f"and prompt-tag drift {status['r230_tool_prompt_tag_mismatch_weight_pct']}%/"
                f"{status['r230_llm_prompt_tag_mismatch_event_pct']}% tool/LLM; "
                f"R231 display projection exact {str(status['r231_display_projection_exact']).lower()}, "
                f"drift localized {str(status['r231_field_drift_localized']).lower()}, "
                f"list-position drift {status['r231_position_tool_mismatch_pct']}%/"
                f"{status['r231_position_llm_mismatch_pct']}% tool/LLM; "
                f"R233 normalized semantic drift {status['r233_normalized_tool_mismatch_weight']} tool weight/"
                f"{status['r233_normalized_llm_mismatch_events']} LLM events, "
                f"strict row identity {str(status['r233_strict_prompt_row_identity_supported']).lower()}"
            ),
            "falsifier_remaining": (
                "strict same-tag prompt-row identity, raw-socket and Claude-launched target-network workloads, arbitrary repositories, and more agent families remain open"
                if c4_ok
                else "controlled exact-lineage run failed before broader generalization"
            ),
            "next_gate": (
                "run raw-socket and Claude-launched target-network lineage replication; keep duplicate prompt-row identity non-keyed"
                if c4_ok
                else "rerun R114/R191/R229 controlled exact-lineage gates"
            ),
        },
        {
            "rq": "RQ4 developer utility",
            "verdict": "unsupported",
            "evidence_level": "materials_ready_no_outcomes",
            "primary_evidence": f"R142/R187/R207 launch materials; {status['c5_responses']} scored responses",
            "falsifier_remaining": "semantic view may not improve accuracy/time or may increase false positives",
            "next_gate": "collect real R142 responses",
        },
        {
            "rq": "RQ5 tag adequacy",
            "verdict": "partial",
            "evidence_level": "syntax_stability_plus_empty_human_protocol",
            "primary_evidence": f"R180 syntax/stability; R124/R190/R203 human-label gates all {status['r124_status']}/{status['r190_status']}/{status['r203_status']}",
            "falsifier_remaining": "labels may be generic, misleading, or low agreement",
            "next_gate": "collect paired R124/R190/R203 labels",
        },
        {
            "rq": "RQ6 artifact/community",
            "verdict": "partial",
            "evidence_level": "local smoke plus clean-clone public-fixture readback",
            "primary_evidence": (
                "R160/R200 pass bounded local/generated-fixture smokes; "
                f"R220 fresh-clone agentpprof {status['r220_status']} with pprof readback "
                f"{str(status['r220_pprof_readback']).lower()} and expected stacks "
                f"{str(status['r220_expected_stacks']).lower()}"
            ),
            "falsifier_remaining": "external-machine install, real-report sanitization, or developer run may fail",
            "next_gate": "external-machine smoke and public real-report audit",
        },
    ]


def next_experiment_rows() -> list[dict[str, str]]:
    return [
        {
            "priority": "P0",
            "run_id": "R142-pilot-return",
            "claim": "C5/RQ4",
            "block": "B4",
            "purpose": "Score real developer responses for the frozen semantic-vs-baseline forensic tasks.",
            "command_or_input": "place r142-pilot-responses.csv in docs/visexp/out/human-evidence-r195/inbox and run python3 docs/visexp/r195_human_evidence_pipeline.py",
            "oracle": "frozen answer key, response contract, Holm-corrected participant/task/order blocked permutation gate",
            "result_path": "docs/visexp/out/human-evidence-r195/scored/",
        },
        {
            "priority": "P0",
            "run_id": "R124-labels-return",
            "claim": "C6/RQ5",
            "block": "B5",
            "purpose": "Score independent human adequacy labels for one-word session/prompt/LLM-call tags.",
            "command_or_input": "return r124-labeler-1.csv and r124-labeler-2.csv, adjudicate disagreements, then run R195",
            "oracle": "adequacy/generic/misleading rubric, paired label coverage, kappa/agreement and adequacy thresholds",
            "result_path": "docs/visexp/out/human-evidence-r195/scored/",
        },
        {
            "priority": "P1",
            "run_id": "R190-R203-labels-return",
            "claim": "C3/C6",
            "block": "B8",
            "purpose": "Score merge-risk and regenerated-label promotion quality before any display-map promotion claim.",
            "command_or_input": "return r190-labeler-*.csv and r203-labeler-*.csv, adjudicate disagreements, then run R195",
            "oracle": "overmerge/undermerge and promote/reject rubrics with no canonical-map update unless gates pass",
            "result_path": "docs/visexp/out/human-evidence-r195/scored/",
        },
        {
            "priority": "P2",
            "run_id": "R235-raw-claude-network-lineage",
            "claim": "C4/RQ3",
            "block": "B3",
            "purpose": "Replicate exact-lineage gates for raw-socket and Claude-launched target-network workloads after R234's HTTP/Codex expansion.",
            "command_or_input": "controlled raw TCP/multiprocess probes plus Claude-launched HTTP/TCP probes with wrapper negative controls",
            "oracle": "target network rows are observed and all join; negative joins remain zero; precision/recall thresholds match R234",
            "result_path": "docs/visexp/out/raw-claude-network-lineage-r235/",
        },
        {
            "priority": "P2",
            "run_id": "R227-external-community",
            "claim": "C7/RQ6",
            "block": "B7",
            "purpose": "Run agentpprof on an external machine or container with a real sanitized report audit and developer-feedback checklist.",
            "command_or_input": "fresh clone or clean container, documented install, public fixture plus opt-in real-history report, write-set/sanitization audit, short developer feedback form",
            "oracle": "expected files exist, pprof readback works, no raw trace leaks, no writes outside declared output paths, feedback records blockers",
            "result_path": "docs/visexp/out/external-community-r227/",
        },
    ]


def overall_status(claims: list[dict[str, str]], summary: dict[str, Any]) -> dict[str, Any]:
    verdict_by_claim = {row["claim"].split()[0]: row["verdict"] for row in claims}
    c4_ok = verdict_by_claim.get("C4") == C4_CONTROLLED_LINEAGE_VERDICT
    c5_ok = verdict_by_claim.get("C5") == "supported"
    c6_ok = verdict_by_claim.get("C6") == "supported"
    blockers: list[str] = []
    if not c4_ok:
        blockers.append("C4/RQ3 controlled exact lineage gates are not supported")
    if not c5_ok:
        blockers.append("C5/RQ4 has no supported real participant outcome")
    if not c6_ok:
        blockers.append("C6/RQ5 has no supported independent human adequacy labels")
    open_scope_gaps = [
        "C4 strict same-tag prompt-row identity remains intentionally non-keyed",
        "C4 raw-socket, Claude-launched target-network, arbitrary-repository, and more-agent-family lineage remain open",
        "C7 external-machine/community evidence remains open",
    ]
    if not (
        summary["r232_external_crossrepo_supported"]
        and summary["r232_normal_gate"]
        and summary["r232_network_gate"]
    ):
        open_scope_gaps.insert(1, "C4 controlled external cross-repo live exact-lineage remains open")
    if not (
        summary["r234_broader_agent_network_supported"]
        and summary["r234_agent_family_gate"]
        and summary["r234_network_gate"]
    ):
        open_scope_gaps.insert(1, "C4 controlled broader agent/network lineage remains open")
    return {
        "status": "osdi_weak_accept_not_supported" if blockers else "human_evidence_ready_for_claim_audit",
        "weak_accept_supported": False,
        "human_evidence_supported": not blockers,
        "blockers": blockers,
        "open_scope_gaps": open_scope_gaps,
        "disallowed_evidence": [
            "subagent review",
            "LLM-filled labels",
            "synthetic review fixtures",
            "empty launch packets",
            "syntax-only tag validity",
        ],
    }


def claim_gate(overall: dict[str, Any], summary: dict[str, Any]) -> dict[str, bool]:
    r232_ok = (
        summary["r232_external_crossrepo_supported"]
        and summary["r232_normal_gate"]
        and summary["r232_network_gate"]
    )
    r234_ok = (
        summary["r234_broader_agent_network_supported"]
        and summary["r234_agent_family_gate"]
        and summary["r234_network_gate"]
    )
    return {
        "claim_readiness_gap_gate_supported": True,
        "reads_generated_artifacts_only": True,
        "raw_trace_read": False,
        "llm_called": False,
        "weak_accept_supported": bool(overall.get("weak_accept_supported")),
        "requires_c4_exact_lineage": "C4/RQ3 controlled exact lineage gates are not supported"
        in (overall.get("blockers") or []),
        "requires_c4_strict_prompt_row_lineage": not (
            summary["r233_normalized_semantic_supported"]
            and summary["r233_duplicate_indexes_non_keyed"]
        ),
        "requires_c4_strict_prompt_row_identity": not summary["r233_strict_prompt_row_identity_supported"],
        "requires_c4_external_crossrepo_lineage": not r232_ok,
        "requires_c4_r234_controlled_expansion": not r234_ok,
        "requires_c4_raw_or_claude_network_lineage": True,
        "requires_c5_human_participants": "C5/RQ4 has no supported real participant outcome"
        in (overall.get("blockers") or []),
        "requires_c6_human_labels": "C6/RQ5 has no supported independent human adequacy labels"
        in (overall.get("blockers") or []),
        "synthetic_or_subagent_evidence_disallowed": True,
    }


def write_csv(path: Path, rows: list[dict[str, str]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_markdown(path: Path, result: dict[str, Any]) -> None:
    summary = result["summary"]
    lines = [
        "# R219 Claim Readiness Gap Gate",
        "",
        f"Status: `{result['status']}`",
        "",
        "R219 is a reviewer-facing claim-readiness audit over generated artifacts.",
        "It does not read raw agent traces, does not call an LLM, and does not count synthetic or subagent evidence as C5/C6 support.",
        "",
        "## Summary",
        "",
        f"- R170 full-history sessions: {summary['r170_sessions']}.",
        f"- R170 system observations: {summary['r170_system_observations']}.",
        f"- R180 valid outputs: {summary['r180_ok_runs']}/{summary['r180_total_runs']}.",
        f"- R114 command-mode precision/recall: {summary['r114_precision_pct']}%/{summary['r114_recall_pct']}%.",
        f"- R191 target network joined: {summary['r191_joined_target_network_effect_events']}/{summary['r191_target_network_effect_events']}.",
        (
            f"- R229 controlled replication: {summary['r229_tasks']} tasks, "
            f"{summary['r229_in_scope_effect_events']} in-scope effects, "
            f"{summary['r229_negative_joined']}/{summary['r229_negative_observed']} negative joins, "
            f"raw join {summary['r229_joined_effect_events']}/{summary['r229_effect_events']} = "
            f"{summary['r229_raw_join_pct']}%."
        ),
        (
            f"- R230 full-history projection: {summary['r230_folded_total_weight']} folded weight, "
            f"missing frame weight {summary['r230_missing_frame_weight']}, "
            f"tool prompt-index coverage {summary['r230_tool_prompt_index_weight_pct']}%, "
            f"duplicate prompt-index rows {summary['r230_duplicate_prompt_index_rows']}, "
            f"prompt-tag drift {summary['r230_tool_prompt_tag_mismatch_weight']} weight "
            f"({summary['r230_tool_prompt_tag_mismatch_weight_pct']}%), LLM drift "
            f"{summary['r230_llm_prompt_tag_mismatch_events']} events "
            f"({summary['r230_llm_prompt_tag_mismatch_event_pct']}%)."
        ),
        (
            f"- R231 drift root cause: display projection exact "
            f"{str(summary['r231_display_projection_exact']).lower()}, "
            f"R230 reproduced {str(summary['r231_r230_reproduced']).lower()}, "
            f"field drift localized {str(summary['r231_field_drift_localized']).lower()}, "
            f"unique-index field drift {summary['r231_field_unique_tool_mismatch_weight']} tool weight/"
            f"{summary['r231_field_unique_llm_mismatch_events']} LLM events, "
            f"external cross-repo supported {str(summary['r231_external_crossrepo_supported']).lower()}."
        ),
        (
            f"- R232 external cross-repo lineage: {summary['r232_tasks']} controlled tasks "
            f"({summary['r232_normal_tasks']} normal, {summary['r232_network_tasks']} network), "
            f"{summary['r232_in_scope_effect_events']} in-scope effects, target network "
            f"{summary['r232_joined_target_network_effect_events']}/"
            f"{summary['r232_target_network_effect_events']} joined, negative joins "
            f"{summary['r232_negative_joined']}/{summary['r232_negative_observed']}, "
            f"precision/recall {summary['r232_precision_pct']}%/"
            f"{summary['r232_recall_pct']}%."
        ),
        (
            f"- R234 broader agent/network lineage: {summary['r234_tasks']} controlled tasks "
            f"({summary['r234_agent_tasks']} Claude-family agent, "
            f"{summary['r234_network_tasks']} Codex HTTP-network), "
            f"{summary['r234_in_scope_effect_events']} in-scope effects, target network "
            f"{summary['r234_joined_target_network_effect_events']}/"
            f"{summary['r234_target_network_effect_events']} joined, negative joins "
            f"{summary['r234_negative_joined']}/{summary['r234_negative_observed']}, "
            f"precision/recall {summary['r234_precision_pct']}%/"
            f"{summary['r234_recall_pct']}%."
        ),
        (
            f"- R233 prompt-row normalization: legacy drift "
            f"{summary['r233_legacy_field_tool_mismatch_weight']} tool weight/"
            f"{summary['r233_legacy_field_llm_mismatch_events']} LLM events -> normalized drift "
            f"{summary['r233_normalized_tool_mismatch_weight']} tool weight/"
            f"{summary['r233_normalized_llm_mismatch_events']} LLM events; "
            f"duplicate rows {summary['r233_duplicate_prompt_index_rows']} non-keyed, "
            f"strict row identity {str(summary['r233_strict_prompt_row_identity_supported']).lower()}."
        ),
        f"- R217 production display buckets/support: {summary['r217_display_buckets']}/{summary['r217_support']}.",
        f"- R218 preview accepted/rejected rows: {summary['r218_accepted_diff_rows']}/{summary['r218_rejected_rows']}.",
        f"- C5 participant responses: {summary['c5_responses']}.",
        f"- C6 final adequacy labels: {summary['c6_final_labels']}.",
        "",
        "## Verdict",
        "",
        f"- Weak accept supported: `{result['overall']['weak_accept_supported']}`.",
        f"- Human evidence supported: `{result['overall']['human_evidence_supported']}`.",
        f"- Blockers: {result['overall']['blockers']}.",
        f"- Open scope gaps: {result['overall']['open_scope_gaps']}.",
        "",
        "## Claim Rows",
        "",
    ]
    for row in result["claims"]:
        lines.append(f"- {row['claim']}: `{row['verdict']}`. Next: {row['next_gate']}")
    lines.extend(["", "## RQ Rows", ""])
    for row in result["rqs"]:
        lines.append(f"- {row['rq']}: `{row['verdict']}`. Next: {row['next_gate']}")
    lines.extend(["", "## Next Experiments", ""])
    for row in result["next_experiments"]:
        lines.append(f"- {row['priority']} {row['run_id']}: {row['purpose']}")
    lines.extend(["", "## Disallowed Evidence", ""])
    for item in result["overall"]["disallowed_evidence"]:
        lines.append(f"- {item}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_result(args: argparse.Namespace) -> dict[str, Any]:
    artifacts = {key: read_json_required(path) for key, path in SOURCE_PATHS.items()}
    summary = artifact_statuses(artifacts)
    claims = claim_rows(summary)
    rqs = rq_rows(summary)
    next_rows = next_experiment_rows()
    overall = overall_status(claims, summary)
    gate = claim_gate(overall, summary)
    return {
        "schema_version": 1,
        "run_id": "R219",
        "claim": "Claim/RQ readiness gap gate for OSDI review",
        "status": overall["status"],
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source_artifacts": SOURCE_PATHS,
        "summary": summary,
        "claims": claims,
        "rqs": rqs,
        "next_experiments": next_rows,
        "overall": overall,
        "claim_gate": gate,
        "claim_boundary": (
            "R219 is an audit/readiness artifact only. It cannot satisfy C5/C6, cannot replace human "
            "participant responses or independent labels, and cannot upgrade the paper to weak accept."
        ),
        "outputs": {
            "claim_csv": rel(Path(args.out_dir) / "claim-readiness-r219.csv"),
            "rq_csv": rel(Path(args.out_dir) / "rq-readiness-r219.csv"),
            "next_experiments_csv": rel(Path(args.out_dir) / "next-experiments-r219.csv"),
            "summary_md": rel(Path(args.out_dir) / "claim-readiness-r219.md"),
        },
    }


def run(args: argparse.Namespace) -> dict[str, Any]:
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    result = build_result(args)
    result_path = out_dir / "claim-readiness-r219.json"
    result_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_csv(out_dir / "claim-readiness-r219.csv", result["claims"], CLAIM_FIELDS)
    write_csv(out_dir / "rq-readiness-r219.csv", result["rqs"], RQ_FIELDS)
    write_csv(out_dir / "next-experiments-r219.csv", result["next_experiments"], NEXT_FIELDS)
    write_markdown(out_dir / "claim-readiness-r219.md", result)
    return result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", default=str(DEFAULT_OUT_DIR))
    return parser.parse_args()


def main() -> None:
    result = run(parse_args())
    print(json.dumps({"status": result["status"], "run_id": result["run_id"]}, sort_keys=True))


if __name__ == "__main__":
    main()
