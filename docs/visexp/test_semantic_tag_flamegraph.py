#!/usr/bin/env python3
import tempfile
import unittest
from collections import Counter
from pathlib import Path
from types import SimpleNamespace
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from semantic_tag_flamegraph import (
    LlmEvent,
    SessionRecord,
    ToolEvent,
    UserRequest,
    build_agent_diff,
    build_dimension_views,
    build_folded_stacks,
    build_nonsemantic_system,
    project_folded,
)
from evaluate_artifacts import (
    compact_model_benchmark,
    compression_summary,
    mixing_summary,
    model_benchmark_evidence,
    model_benchmark_size_classes,
    model_benchmark_valid,
    network_lineage_supported,
    tag_quality,
)
from tag_stability_smoke import (
    annotator_metrics,
    cross_annotator_metrics,
    smoke_verdict,
)
from user_task_benchmark import (
    build_assignments,
    CONDITION_ORDER,
    parse_variants,
    participant_packets,
    percentile_nearest_rank,
    stack_frame,
)
from effect_lineage_smoke import lineage_rows
from live_lineage_harness import synthesize
from r114_live_record_suite import Task, precision_recall_summary, task_command
from r182_network_record_suite import aggregate_network, network_gate
from r184_weak_accept_gate import c5_gate as r184_c5_gate
from r184_weak_accept_gate import c6_gate as r184_c6_gate
from r184_weak_accept_gate import overall_gate as r184_overall_gate
from r187_prepare_pilot_materials import group_assignments as r187_group_assignments
from r187_prepare_pilot_materials import scan_forbidden_keys as r187_scan_forbidden_keys
from r124_blinded_label_sheet import (
    VISIBLE_FIELDS as R124_BLINDED_FIELDS,
    blinded_row as r124_blinded_row,
)
from r124_join_blinded_labels import join_rows as join_r124_label_rows
from r124_join_blinded_labels import read_labeler_sheet as read_r124_labeler_sheet
from r124_join_blinded_labels import status_for as r124_join_status
from r121_model_benchmark_summary import model_size_class as r121_model_size_class
from r170_full_history_refresh import counter_summary as r170_counter_summary
from r170_full_history_refresh import read_folded_total as r170_read_folded_total
from r142_preregistration import validate_preregistration as validate_r142_preregistration
from score_user_task_results import (
    BASELINE_CONDITIONS,
    REQUIRED_RESPONSE_FIELDS,
    SEMANTIC_CONDITION,
    claim_analysis,
    is_placeholder_response,
    paired_sign_flip_p_value,
    score_response,
    summarize,
    validate_response_contract,
)
from score_tag_adequacy import (
    claim_gate as tag_adequacy_claim_gate,
    cohen_kappa,
    result_status as tag_adequacy_status,
    score_rows as score_tag_adequacy_rows,
)
from r190_score_merge_audit import (
    claim_gate as r190_merge_claim_gate,
    result_status as r190_merge_status,
    score_rows as score_r190_merge_rows,
)
from r194_human_evidence_preflight import gate_status as r194_gate_status
from r195_human_evidence_pipeline import group_readiness as r195_group_readiness
from r195_human_evidence_pipeline import pipeline_status as r195_pipeline_status
from r196_long_tail_governance import GovernanceConfig, governance_decision, summarize as r196_summarize
from r200_community_smoke import sanitize_value as r200_sanitize_value
from r200_community_smoke import write_public_codex_fixture as r200_write_public_codex_fixture
from r201_long_tail_sensitivity import compute_variant_record as r201_compute_variant_record
from r201_long_tail_sensitivity import grid_rationale as r201_grid_rationale
from r201_long_tail_sensitivity import rows_by_key as r201_rows_by_key
from r201_long_tail_sensitivity import variant_specs as r201_variant_specs
from r202_long_tail_regeneration_smoke import status_for as r202_status_for
from r202_long_tail_regeneration_smoke import summarize_attempts as r202_summarize_attempts
from r203_long_tail_promotion_gate import claim_gate as r203_claim_gate
from r203_long_tail_promotion_gate import packet_rows_from_attempts as r203_packet_rows_from_attempts
from r203_long_tail_promotion_gate import result_status as r203_result_status
from r203_long_tail_promotion_gate import score_rows as r203_score_rows
from r205_long_tail_compaction_metrics import dimension_metrics as r205_dimension_metrics
from r205_long_tail_compaction_metrics import canonical_map_consistency as r205_canonical_map_consistency
from r205_long_tail_compaction_metrics import summarize_regeneration as r205_summarize_regeneration
from r205_long_tail_compaction_metrics import top_k_coverage as r205_top_k_coverage
from r209_reversible_display_map import (
    build_display_map as r209_build_display_map,
    build_drilldown_rows as r209_build_drilldown_rows,
    build_reviewed_diff as r209_build_reviewed_diff,
    summarize as r209_summarize,
)
from r211_stack_examples import (
    baseline_collapse_rows as r211_baseline_collapse_rows,
    baseline_key_for as r211_baseline_key_for,
    frames_from_stack as r211_frames_from_stack,
    process_split_rows as r211_process_split_rows,
    tag_distribution_rows as r211_tag_distribution_rows,
)
from r212_display_compaction_ablation import (
    COMPACTED_TAG_LEVELS as R212_COMPACTED_TAG_LEVELS,
    EXCLUDED_TAG_LEVELS as R212_EXCLUDED_TAG_LEVELS,
    behavior_ambiguity_rows as r212_behavior_ambiguity_rows,
    build_maps as r212_build_maps,
    summarize as r212_summarize,
    variant_summary_rows as r212_variant_summary_rows,
)
from r213_display_mode_drilldown_smoke import (
    drilldown_membership_matches_display_map as r213_drilldown_matches_display,
    mode_summary_rows as r213_mode_summary_rows,
    pending_review_queue as r213_pending_review_queue,
    summarize as r213_summarize,
)
from r214_long_tail_control_loop import (
    action_rows as r214_action_rows,
    dimension_priority as r214_dimension_priority,
    regeneration_version_policy as r214_regeneration_version_policy,
    rollup_preview_rows as r214_rollup_preview_rows,
    trigger_row as r214_trigger_row,
)
from r215_frontend_renderer_mode_smoke import summarize as r215_summarize
from r216_browser_dom_mode_smoke import claim_gate as r216_claim_gate
from r216_browser_dom_mode_smoke import summarize as r216_summarize
from r217_production_react_display_mode_smoke import claim_gate as r217_claim_gate
from r218_display_map_update_gate import (
    claim_gate as r218_claim_gate,
    preview_rows as r218_preview_rows,
    reviewed_display_diff_rows as r218_reviewed_display_diff_rows,
    summarize as r218_summarize,
    valid_display_tag as r218_valid_display_tag,
)
from r219_claim_readiness_gap_gate import (
    artifact_statuses as r219_artifact_statuses,
    claim_gate as r219_claim_gate,
    claim_rows as r219_claim_rows,
    next_experiment_rows as r219_next_experiment_rows,
    overall_status as r219_overall_status,
    rq_rows as r219_rq_rows,
)
from r207_human_launch_readiness import build_return_plan as r207_build_return_plan
from r207_human_launch_readiness import count_nonblank as r207_count_nonblank
from r207_human_launch_readiness import response_template_audit as r207_response_template_audit
from visual_summary import bar_width, label_lines, verdict_color, verdict_score


class AggregationTests(unittest.TestCase):
    def test_r200_sanitizes_paths_before_committed_summary(self) -> None:
        payload = {
            "cmd": [
                "/home/tester/workspace/agentsight/.agentsight/agentflame/out",
                "/tmp/agentsight-r200-abc/public-fixture/codex/sessions/session.jsonl",
                "/home/tester/workspace/llama.cpp/model.gguf",
            ],
            "nested": {"stdout": "wrote /home/tester/workspace/agentsight/report using /tmp/agentsight-r200-abc"},
        }

        sanitized = r200_sanitize_value(
            payload,
            [
                ("/home/tester/workspace/agentsight", "<repo>"),
                ("/tmp/agentsight-r200-abc", "<tmp>"),
                ("/home/tester", "~"),
            ],
        )
        rendered = str(sanitized)

        self.assertIn("<repo>", rendered)
        self.assertIn("<tmp>", rendered)
        self.assertIn("~/workspace/llama.cpp/model.gguf", rendered)
        self.assertNotIn("/home/tester/workspace/agentsight", rendered)
        self.assertNotIn("/tmp/agentsight-r200-abc", rendered)

    def test_r200_public_fixture_is_codex_shaped_and_not_real_trace(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "public-fixture/codex/sessions/2026/06/15/r200-public-codex.jsonl"
            info = r200_write_public_codex_fixture(path)
            text = path.read_text(encoding="utf-8")

        self.assertEqual(info["schema"], "r200-public-codex-fixture-v1")
        self.assertFalse(info["contains_real_trace"])
        self.assertFalse(info["contains_private_prompt"])
        self.assertIn('"type": "session_meta"', text)
        self.assertIn('"originator": "codex-cli"', text)
        self.assertIn('"type": "function_call"', text)

    def test_r201_variant_specs_include_threshold_and_vocab_sensitivity(self) -> None:
        names = {spec["variant"] for spec in r201_variant_specs()}

        self.assertIn("baseline", names)
        self.assertIn("higher_tail_threshold", names)
        self.assertIn("aggressive_split", names)
        self.assertIn("narrow_generic_vocab", names)
        self.assertIn("expanded_generic_vocab", names)

    def test_r201_grid_rationale_names_each_sensitivity_axis(self) -> None:
        rationale = r201_grid_rationale()

        self.assertIn("tail_thresholds", rationale)
        self.assertIn("split_thresholds", rationale)
        self.assertIn("generic_vocabulary", rationale)
        self.assertIn("half/default/double", rationale["tail_thresholds"])
        self.assertIn("raw tags", rationale["generic_vocabulary"])

    def test_r201_variant_record_tracks_review_counts_and_head_stability(self) -> None:
        baseline_rows = [
            {
                "dimension": "prompt",
                "raw_tag": "refactor",
                "support": 100,
                "governance_action": "keep_head",
                "requires_review": False,
                "is_long_tail": False,
            },
            {
                "dimension": "prompt",
                "raw_tag": "update",
                "support": 10,
                "governance_action": "regenerate_candidate",
                "requires_review": True,
                "is_long_tail": True,
            },
        ]
        variant_rows = [
            {
                "dimension": "prompt",
                "raw_tag": "refactor",
                "support": 100,
                "governance_action": "keep_head",
                "requires_review": False,
                "is_long_tail": False,
            },
            {
                "dimension": "prompt",
                "raw_tag": "update",
                "support": 10,
                "governance_action": "keep_rare_distinct",
                "requires_review": False,
                "is_long_tail": True,
            },
        ]
        summary = {
            "action_counts": {"keep_head": 1, "keep_rare_distinct": 1},
            "review_required_tags": 0,
            "long_tail_tags": 1,
        }
        spec = r201_variant_specs()[0] | {"variant": "toy", "description": "toy"}
        baseline_by_key = r201_rows_by_key(baseline_rows)
        baseline_head_keys = {("prompt", "refactor")}

        record = r201_compute_variant_record(
            spec,
            variant_rows,
            summary,
            baseline_by_key,
            baseline_head_keys,
        )

        self.assertEqual(record["total_support"], 110)
        self.assertEqual(record["review_required_support_pct"], 0.0)
        self.assertEqual(record["long_tail_support_pct"], 9.091)
        self.assertEqual(record["changed_action_tags_vs_baseline"], 1)
        self.assertEqual(record["changed_review_gate_tags_vs_baseline"], 1)
        self.assertEqual(record["baseline_head_stability_pct"], 100.0)

    def test_r202_attempt_summary_counts_candidate_only_regeneration(self) -> None:
        rows = [
            {
                "dimension": "prompt",
                "raw_tag": "update",
                "governance_action": "regenerate_candidate",
                "regenerated_tag": "docs",
                "regenerated_valid": "True",
                "regeneration_error": "",
            },
            {
                "dimension": "llm",
                "raw_tag": "ignored",
                "governance_action": "regenerate_candidate",
                "regenerated_tag": "",
                "regenerated_valid": "False",
                "regeneration_error": "invalid",
            },
        ]

        summary = r202_summarize_attempts(rows)
        status = r202_status_for({"summary": {"regeneration": {"enabled": True}}}, summary)

        self.assertEqual(summary["attempted_rows"], 2)
        self.assertEqual(summary["valid_rows"], 1)
        self.assertEqual(summary["invalid_rows"], 1)
        self.assertEqual(summary["changed_valid_rows"], 1)
        self.assertEqual(summary["unique_valid_regenerated_tags"], 1)
        self.assertEqual(status, "long_tail_regeneration_smoke_needs_review")

    def test_r203_promotion_packet_preserves_candidate_gate(self) -> None:
        attempts = [
            {
                "dimension": "prompt",
                "raw_tag": "update",
                "canonical_tag": "update",
                "governance_action": "regenerate_candidate",
                "governance_reasons": "generic_or_noisy_tag",
                "support": "10",
                "top_processes": "rg=3",
                "top_effects": "read=3",
                "top_context_tags": "docs=4",
                "regeneration_context_hash": "abc",
                "regenerated_tag": "docs",
                "regenerated_valid": "True",
            },
            {
                "dimension": "prompt",
                "raw_tag": "ignored",
                "canonical_tag": "ignored",
                "governance_action": "contextual_split_candidate",
                "governance_reasons": "multi_peak_processes",
                "support": "20",
                "top_processes": "git=9",
                "top_effects": "process=9",
                "top_context_tags": "refactor=8",
                "regeneration_context_hash": "def",
                "regenerated_tag": "refactor",
                "regenerated_valid": "True",
            },
        ]

        packet = r203_packet_rows_from_attempts(attempts)
        scored, summary = r203_score_rows(
            [{**row, "labeler_1": "", "labeler_2": "", "adjudicated_label": ""} for row in packet]
        )
        gate = r203_claim_gate(summary)

        self.assertEqual(packet[0]["proposed_action"], "review_promote_candidate")
        self.assertEqual(packet[1]["proposed_action"], "review_split_candidate")
        self.assertEqual(summary["packet_row_count"], 2)
        self.assertEqual(summary["final_label_count"], 0)
        self.assertEqual(r203_result_status(summary), "human_labels_empty")
        self.assertFalse(gate["long_tail_promotion_review_supported"])
        self.assertFalse(gate["canonical_map_updated"])
        self.assertEqual(len(scored), 2)

    def test_r203_complete_labels_enable_review_only_not_map_update(self) -> None:
        packet = r203_packet_rows_from_attempts(
            [
                {
                    "dimension": "prompt",
                    "raw_tag": "update",
                    "canonical_tag": "update",
                    "governance_action": "regenerate_candidate",
                    "governance_reasons": "generic_or_noisy_tag",
                    "support": "10",
                    "top_processes": "",
                    "top_effects": "",
                    "top_context_tags": "docs=4",
                    "regeneration_context_hash": "abc",
                    "regenerated_tag": "docs",
                    "regenerated_valid": "True",
                }
            ]
        )
        rows = [
            {
                **packet[0],
                "labeler_1": "promote",
                "labeler_2": "promote",
                "adjudicated_label": "",
            }
        ]

        _, summary = r203_score_rows(rows)
        gate = r203_claim_gate(summary)

        self.assertEqual(r203_result_status(summary), "human_labels_scored")
        self.assertTrue(gate["long_tail_promotion_review_supported"])
        self.assertTrue(gate["promotion_decisions_ready"])
        self.assertFalse(gate["canonical_map_updated"])
        self.assertFalse(gate["canonical_map_update_allowed_by_this_script"])
        self.assertFalse(gate["semantic_adequacy_supported"])

    def test_r205_top_k_coverage_aggregates_support_by_label(self) -> None:
        rows = [
            {"raw_tag": "docs", "support": "10"},
            {"raw_tag": "test", "support": "5"},
            {"raw_tag": "docs", "support": "7"},
        ]

        coverage = r205_top_k_coverage(rows, "raw_tag", 1)

        self.assertEqual(coverage["unique_labels"], 2)
        self.assertEqual(coverage["total_support"], 22)
        self.assertEqual(coverage["top_k_support"], 17)
        self.assertEqual(coverage["top_k_coverage_pct"], 77.273)
        self.assertEqual(coverage["top_labels"][0]["label"], "docs")

    def test_r205_dimension_metrics_keeps_compaction_separate_from_review(self) -> None:
        rows = [
            {
                "raw_tag": "docsupdate",
                "canonical_tag": "docs",
                "support": "10",
                "governance_action": "auto_canonicalize_existing",
                "is_long_tail": "False",
                "requires_review": "False",
                "is_generic_or_noisy": "True",
                "is_multimodal": "False",
            },
            {
                "raw_tag": "docs",
                "canonical_tag": "docs",
                "support": "90",
                "governance_action": "keep_head",
                "is_long_tail": "False",
                "requires_review": "False",
                "is_generic_or_noisy": "False",
                "is_multimodal": "False",
            },
            {
                "raw_tag": "update",
                "canonical_tag": "update",
                "support": "5",
                "governance_action": "regenerate_candidate",
                "is_long_tail": "True",
                "requires_review": "True",
                "is_generic_or_noisy": "True",
                "is_multimodal": "False",
            },
        ]

        metrics = r205_dimension_metrics(rows, top_k=1)

        self.assertEqual(metrics["raw_unique_tags"], 3)
        self.assertEqual(metrics["canonical_unique_tags"], 2)
        self.assertEqual(metrics["canonical_unique_reduction"], 1)
        self.assertEqual(metrics["long_tail_support_pct"], 4.762)
        self.assertEqual(metrics["review_required_support_pct"], 4.762)
        self.assertEqual(metrics["top_k_coverage_gain_pct_points"], 9.524)
        self.assertEqual(metrics["actions"]["regenerate_candidate"]["rows"], 1)

    def test_r205_canonical_map_consistency_detects_r196_drift(self) -> None:
        r189_rows = [
            {
                "dimension": "prompt",
                "raw_tag": "docsupdate",
                "canonical_tag": "docs",
                "action": "merge",
            },
            {
                "dimension": "prompt",
                "raw_tag": "rare",
                "canonical_tag": "rare",
                "action": "keep",
            },
        ]
        consistent_rows = [
            {
                "dimension": "prompt",
                "raw_tag": "docsupdate",
                "canonical_tag": "docs",
                "governance_action": "auto_canonicalize_existing",
            },
            {
                "dimension": "prompt",
                "raw_tag": "rare",
                "canonical_tag": "rare",
                "governance_action": "keep_rare_distinct",
            },
        ]

        consistent = r205_canonical_map_consistency(r189_rows, consistent_rows)

        self.assertTrue(consistent["consistent"])
        self.assertEqual(consistent["r196_rows_missing_from_r189"], 0)
        self.assertEqual(consistent["canonical_mismatch_rows"], 0)
        self.assertEqual(consistent["auto_canonicalize_existing_bad_rows"], 0)

        drifted_rows = [
            {
                "dimension": "prompt",
                "raw_tag": "docsupdate",
                "canonical_tag": "update",
                "governance_action": "auto_canonicalize_existing",
            },
            {
                "dimension": "prompt",
                "raw_tag": "rare",
                "canonical_tag": "rare",
                "governance_action": "auto_canonicalize_existing",
            },
        ]

        drifted = r205_canonical_map_consistency(r189_rows, drifted_rows)

        self.assertFalse(drifted["consistent"])
        self.assertEqual(drifted["canonical_mismatch_rows"], 1)
        self.assertEqual(drifted["auto_canonicalize_existing_bad_rows"], 1)

    def test_r209_display_map_keeps_regenerated_tags_candidate_only(self) -> None:
        governance_rows = [
            {
                "dimension": "prompt",
                "raw_tag": "docsupdate",
                "canonical_tag": "docs",
                "governance_action": "auto_canonicalize_existing",
                "governance_reasons": "r189_alias",
                "requires_review": "False",
                "is_long_tail": "False",
                "support": "10",
                "top_processes": "rg=4; sed=2",
                "top_effects": "read=6",
                "top_paths": "docs=6",
                "top_context_tags": "review=5",
            },
            {
                "dimension": "prompt",
                "raw_tag": "update",
                "canonical_tag": "update",
                "governance_action": "regenerate_candidate",
                "governance_reasons": "generic_or_noisy_tag;long_tail",
                "requires_review": "True",
                "is_long_tail": "True",
                "support": "5",
                "top_processes": "python3=3",
                "top_effects": "write=3",
                "top_paths": "docs=3",
                "top_context_tags": "paper=3",
            },
        ]
        promotion_rows = [
            {
                "dimension": "prompt",
                "raw_tag": "update",
                "regenerated_tag": "paper",
                "grammar_valid": "True",
                "final_label": "",
                "promotion_label": "",
                "final_source": "empty",
                "label_state": "unlabeled",
            }
        ]

        display = r209_build_display_map(governance_rows, promotion_rows)
        by_raw = {row["raw_tag"]: row for row in display}
        drilldown = r209_build_drilldown_rows(governance_rows, display)
        diff = r209_build_reviewed_diff(display)
        summary = r209_summarize(
            governance_rows,
            display,
            drilldown,
            diff,
            {"status": "human_labels_empty", "summary": {"final_label_count": 0}},
            {"status": "compaction_metrics_ready_no_quality_claims"},
        )

        self.assertEqual(by_raw["docsupdate"]["active_display_tag"], "docs")
        self.assertEqual(by_raw["update"]["active_display_tag"], "update")
        self.assertEqual(by_raw["update"]["candidate_display_tag"], "paper")
        self.assertEqual(by_raw["update"]["candidate_state"], "pending_review:unlabeled")
        self.assertEqual(by_raw["update"]["promotion_final_source"], "empty")
        self.assertFalse(by_raw["update"]["map_update_allowed"])
        self.assertEqual(len(diff), 0)
        self.assertTrue(summary["raw_coverage_complete"])
        self.assertTrue(summary["drilldown_support_preserved"])
        self.assertTrue(summary["drilldown_raw_tags_complete"])
        self.assertTrue(summary["no_hidden_other_bucket"])
        self.assertEqual(sum(row["support"] for row in drilldown), 15)

    def test_r209_profile_guarded_merges_are_pending_not_active(self) -> None:
        governance_rows = [
            {
                "dimension": "llm",
                "raw_tag": "loganalyze",
                "canonical_tag": "analyze",
                "governance_action": "auto_canonicalize_existing",
                "governance_reasons": "r189_lexical+profile",
                "requires_review": "True",
                "is_long_tail": "False",
                "support": "14",
            },
            {
                "dimension": "llm",
                "raw_tag": "rqanalyze",
                "canonical_tag": "analyze",
                "governance_action": "auto_canonicalize_existing",
                "governance_reasons": "r189_alias",
                "requires_review": "False",
                "is_long_tail": "True",
                "support": "1",
            },
        ]

        display = r209_build_display_map(governance_rows, [])
        by_raw = {row["raw_tag"]: row for row in display}

        self.assertEqual(by_raw["loganalyze"]["active_display_tag"], "loganalyze")
        self.assertEqual(by_raw["loganalyze"]["active_source"], "raw_preserved")
        self.assertEqual(by_raw["loganalyze"]["candidate_display_tag"], "analyze")
        self.assertEqual(
            by_raw["loganalyze"]["candidate_source"],
            "r189_profile_guarded_merge_candidate",
        )
        self.assertEqual(by_raw["loganalyze"]["candidate_state"], "pending_merge_review")
        self.assertEqual(by_raw["rqanalyze"]["active_display_tag"], "analyze")
        self.assertEqual(by_raw["rqanalyze"]["active_source"], "r189_alias_overlay")

    def test_r209_drilldown_lists_all_raw_tags_not_only_top_k(self) -> None:
        governance_rows = [
            {
                "dimension": "prompt",
                "raw_tag": f"raw{idx}",
                "canonical_tag": "docs",
                "governance_action": "auto_canonicalize_existing",
                "governance_reasons": "r189_alias",
                "requires_review": "False",
                "is_long_tail": "True",
                "support": "1",
            }
            for idx in range(10)
        ]

        display = r209_build_display_map(governance_rows, [])
        drilldown = r209_build_drilldown_rows(governance_rows, display)

        self.assertEqual(len(drilldown), 1)
        self.assertEqual(drilldown[0]["raw_tag_count"], 10)
        for idx in range(10):
            self.assertIn(f"raw{idx}=1", drilldown[0]["raw_tags"])

    def test_r209_reviewed_promote_creates_diff_without_active_update(self) -> None:
        governance_rows = [
            {
                "dimension": "llm",
                "raw_tag": "check",
                "canonical_tag": "check",
                "governance_action": "regenerate_candidate",
                "governance_reasons": "generic_or_noisy_tag",
                "requires_review": "True",
                "is_long_tail": "False",
                "support": "20",
            }
        ]
        promotion_rows = [
            {
                "dimension": "llm",
                "raw_tag": "check",
                "regenerated_tag": "review",
                "grammar_valid": "True",
                "final_label": "promote",
                "promotion_label": "",
                "final_source": "consensus",
                "label_state": "final",
            }
        ]

        display = r209_build_display_map(governance_rows, promotion_rows)
        diff = r209_build_reviewed_diff(display)

        self.assertEqual(display[0]["active_display_tag"], "check")
        self.assertEqual(display[0]["candidate_display_tag"], "review")
        self.assertEqual(display[0]["candidate_state"], "reviewed_promote:consensus")
        self.assertEqual(display[0]["promotion_final_source"], "consensus")
        self.assertFalse(display[0]["map_update_allowed"])
        self.assertEqual(diff[0]["from_display_tag"], "check")
        self.assertEqual(diff[0]["to_display_tag"], "review")
        self.assertEqual(diff[0]["diff_source"], "r203_reviewed_promotion")
        self.assertEqual(diff[0]["promotion_final_source"], "consensus")

        weak_display = r209_build_display_map(
            governance_rows,
            [{**promotion_rows[0], "final_source": "single_label", "label_state": "weak_final"}],
        )
        self.assertEqual(r209_build_reviewed_diff(weak_display), [])

    def test_r212_r209_conservative_display_matches_alias_only(self) -> None:
        self.assertEqual(R212_COMPACTED_TAG_LEVELS, ["session", "prompt"])
        self.assertEqual(R212_EXCLUDED_TAG_LEVELS, ["llm", "token"])

        folded = Counter(
            {
                "project:p;agent:a;session:reviewfix;prompt:docupdate;call:tool/shell;process:git;effect:read;status:ok": 5,
                "project:p;agent:a;session:reviewfix;prompt:designcodex;call:tool/shell;process:git;effect:read;status:ok": 7,
            }
        )
        r196_rows = [
            {
                "dimension": "session",
                "raw_tag": "reviewfix",
                "canonical_tag": "review",
                "governance_action": "auto_canonicalize_existing",
                "governance_reasons": "r189_alias",
            },
            {
                "dimension": "prompt",
                "raw_tag": "docupdate",
                "canonical_tag": "docs",
                "governance_action": "auto_canonicalize_existing",
                "governance_reasons": "r189_alias",
            },
            {
                "dimension": "prompt",
                "raw_tag": "designcodex",
                "canonical_tag": "design",
                "governance_action": "auto_canonicalize_existing",
                "governance_reasons": "r189_lexical+profile",
            },
        ]
        r209_rows = [
            {"dimension": "session", "raw_tag": "reviewfix", "active_display_tag": "review"},
            {"dimension": "prompt", "raw_tag": "docupdate", "active_display_tag": "docs"},
            {"dimension": "prompt", "raw_tag": "designcodex", "active_display_tag": "designcodex"},
        ]

        maps, pending = r212_build_maps(r196_rows, r209_rows)
        variant_rows, transformed, _stats = r212_variant_summary_rows(folded, maps, pending)
        behavior_rows = r212_behavior_ambiguity_rows(transformed)
        summary = r212_summarize(
            folded,
            variant_rows,
            behavior_rows,
            transformed,
            {"summary": {"active_display_unique_labels": 3, "alias_active_rows": 2}},
        )

        self.assertEqual(transformed["alias_only"], transformed["r209_conservative_display"])
        self.assertNotEqual(transformed["profile_guarded_candidate_applied"], transformed["r209_conservative_display"])
        self.assertTrue(summary["effect_weight_conserved"])
        self.assertTrue(summary["r209_alias_only_equivalent"])
        profile_row = {
            row["variant"]: row for row in variant_rows
        }["profile_guarded_candidate_applied"]
        self.assertEqual(profile_row["unreviewed_profile_merge_weight_active"], 7)

    def test_r212_behavior_ambiguity_tracks_prompt_merges(self) -> None:
        folded = Counter(
            {
                "project:p;agent:a;session:s;prompt:docupdate;call:tool/shell;process:git;effect:read;status:ok": 4,
                "project:p;agent:a;session:s;prompt:docs;call:tool/shell;process:git;effect:read;status:ok": 6,
            }
        )
        r196_rows = [
            {
                "dimension": "prompt",
                "raw_tag": "docupdate",
                "canonical_tag": "docs",
                "governance_action": "auto_canonicalize_existing",
                "governance_reasons": "r189_alias",
            }
        ]
        r209_rows = [{"dimension": "prompt", "raw_tag": "docupdate", "active_display_tag": "docs"}]

        maps, pending = r212_build_maps(r196_rows, r209_rows)
        _variant_rows, transformed, _stats = r212_variant_summary_rows(folded, maps, pending)
        rows = r212_behavior_ambiguity_rows(transformed)
        by_variant = {
            row["variant"]: row
            for row in rows
            if row["behavior_key"] == "process:git;effect:read;status:ok"
        }

        self.assertEqual(by_variant["raw"]["distinct_prompt_tags"], 2)
        self.assertEqual(by_variant["raw"]["ambiguous_share_pct"], 40.0)
        self.assertEqual(by_variant["alias_only"]["distinct_prompt_tags"], 1)
        self.assertEqual(by_variant["alias_only"]["ambiguous_share_pct"], 0.0)
        self.assertEqual(by_variant["alias_only"]["total_weight"], 10)

    def test_r213_pending_mode_preserves_display_membership(self) -> None:
        display_rows = [
            {
                "dimension": "prompt",
                "raw_tag": "docupdate",
                "active_display_tag": "docs",
                "support": "4",
                "requires_review": "False",
                "candidate_display_tag": "",
            },
            {
                "dimension": "prompt",
                "raw_tag": "docs",
                "active_display_tag": "docs",
                "support": "6",
                "requires_review": "False",
                "candidate_display_tag": "",
            },
            {
                "dimension": "prompt",
                "raw_tag": "ignored",
                "active_display_tag": "ignored",
                "support": "2",
                "requires_review": "True",
                "candidate_display_tag": "refactor",
                "candidate_source": "r202_llama_candidate",
                "candidate_state": "pending_review",
                "is_long_tail": "False",
                "governance_action": "regenerate_candidate",
                "governance_reasons": "generic_or_noisy_tag",
            },
        ]
        drilldown_rows = [
            {
                "dimension": "prompt",
                "active_display_tag": "docs",
                "support": "10",
                "raw_tag_count": "2",
                "raw_tags": "docupdate=4; docs=6",
            },
            {
                "dimension": "prompt",
                "active_display_tag": "ignored",
                "support": "2",
                "raw_tag_count": "1",
                "raw_tags": "ignored=2",
            },
        ]

        mode_rows = r213_mode_summary_rows(display_rows, drilldown_rows)
        queue_rows = r213_pending_review_queue(display_rows)
        summary = r213_summarize(display_rows, drilldown_rows, mode_rows, queue_rows, {"summary": {}})
        by_mode = {row["mode"]: row for row in mode_rows}

        self.assertEqual(by_mode["raw"]["bucket_count"], 3)
        self.assertEqual(by_mode["display"]["bucket_count"], 2)
        self.assertEqual(by_mode["pending"]["bucket_count"], 2)
        self.assertEqual(by_mode["pending"]["candidate_overlay_rows"], 1)
        self.assertEqual(len(queue_rows), 1)
        self.assertEqual(queue_rows[0]["review_reason"], "pending regenerated-label promotion review")
        self.assertTrue(summary["all_modes_support_preserved"])
        self.assertTrue(summary["pending_membership_unchanged"])
        self.assertTrue(summary["drilldown_raw_tags_complete"])
        self.assertTrue(summary["drilldown_membership_matches_display_map"])
        self.assertTrue(r213_drilldown_matches_display(display_rows, drilldown_rows))
        self.assertIsNone(summary["false_merge_rate_pct"])
        self.assertIsNone(summary["missed_merge_rate_pct"])

    def test_r213_rejects_self_consistent_but_wrong_drilldown_membership(self) -> None:
        display_rows = [
            {
                "dimension": "prompt",
                "raw_tag": "docupdate",
                "active_display_tag": "docs",
                "support": "4",
            },
            {
                "dimension": "prompt",
                "raw_tag": "docs",
                "active_display_tag": "docs",
                "support": "6",
            },
        ]
        wrong_drilldown_rows = [
            {
                "dimension": "prompt",
                "active_display_tag": "docs",
                "support": "10",
                "raw_tag_count": "2",
                "raw_tags": "docupdate=4; build=6",
            },
        ]

        mode_rows = r213_mode_summary_rows(display_rows, wrong_drilldown_rows)
        summary = r213_summarize(display_rows, wrong_drilldown_rows, mode_rows, [], {"summary": {}})

        self.assertTrue(summary["drilldown_raw_tags_complete"])
        self.assertFalse(summary["drilldown_membership_matches_display_map"])
        self.assertFalse(r213_drilldown_matches_display(display_rows, wrong_drilldown_rows))

    def test_r214_long_tail_controller_keeps_candidates_pending(self) -> None:
        r196_rows = [
            {"governance_action": "keep_rare_distinct", "support": "3"},
            {"governance_action": "keep_head", "support": "97"},
        ]
        display_rows = [
            {
                "active_source": "r189_alias_overlay",
                "support": "10",
                "candidate_source": "",
                "requires_review": "False",
            },
            {
                "active_source": "raw_preserved",
                "support": "7",
                "candidate_source": "r189_profile_guarded_merge_candidate",
                "requires_review": "True",
            },
            {
                "active_source": "raw_preserved",
                "support": "5",
                "candidate_source": "r202_llama_candidate",
                "requires_review": "True",
            },
        ]
        r196_summary = {
            "action_counts": {"keep_rare_distinct": 1, "keep_head": 1},
        }
        r209_summary = {
            "total_support": 100,
            "pending_merge_candidate_rows": 1,
            "regenerated_candidate_rows": 1,
            "review_required_rows": 2,
        }

        rows = {row["action"]: row for row in r214_action_rows(r196_rows, display_rows, r196_summary, r209_summary)}

        self.assertEqual(rows["active_alias_display"]["rows"], 1)
        self.assertEqual(rows["active_alias_display"]["default_display_effect"], "active")
        self.assertEqual(rows["pending_profile_merge_candidate"]["default_display_effect"], "pending")
        self.assertEqual(rows["pending_llm_regenerated_or_split_candidate"]["default_display_effect"], "candidate_only")
        self.assertEqual(rows["review_required_total"]["support"], 12)

    def test_r214_rollup_and_regeneration_policy_are_candidate_only(self) -> None:
        display_rows = [
            {
                "governance_action": "keep_head",
                "active_source": "raw_preserved",
                "candidate_source": "",
                "support": "40",
            },
            {
                "governance_action": "keep_rare_distinct",
                "active_source": "raw_preserved",
                "candidate_source": "",
                "support": "3",
            },
            {
                "governance_action": "auto_canonicalize_existing",
                "active_source": "r189_alias_overlay",
                "candidate_source": "",
                "support": "7",
            },
            {
                "governance_action": "auto_canonicalize_existing",
                "active_source": "raw_preserved",
                "candidate_source": "r189_profile_guarded_merge_candidate",
                "support": "5",
            },
            {
                "governance_action": "review_merge",
                "active_source": "raw_preserved",
                "candidate_source": "",
                "support": "2",
            },
            {
                "governance_action": "regenerate_candidate",
                "active_source": "raw_preserved",
                "candidate_source": "r202_llama_candidate",
                "support": "11",
            },
            {
                "governance_action": "contextual_split_candidate",
                "active_source": "raw_preserved",
                "candidate_source": "r202_llama_candidate",
                "support": "13",
            },
        ]

        rollups = {row["rollup_bucket"]: row for row in r214_rollup_preview_rows(display_rows, 81)}

        self.assertEqual(sum(row["rows"] for row in rollups.values()), len(display_rows))
        self.assertEqual(sum(row["support"] for row in rollups.values()), 81)
        self.assertTrue(rollups["active_alias_overlay"]["active_display_allowed"])
        self.assertFalse(rollups["pending_profile_merge"]["active_display_allowed"])
        self.assertFalse(rollups["pending_llm_regeneration"]["active_display_allowed"])
        self.assertFalse(rollups["pending_contextual_split"]["active_display_allowed"])
        self.assertIn("review", rollups["pending_llm_regeneration"]["required_gate"])

        policy = r214_regeneration_version_policy(
            {
                "attempt_summary": {
                    "attempted_rows": 2,
                    "valid_rows": 2,
                    "changed_valid_rows": 1,
                    "unique_valid_regenerated_tags": 2,
                }
            },
            {"regenerated_candidate_rows": 2, "r203_final_labels": 0},
        )

        self.assertTrue(policy["candidate_only"])
        self.assertEqual(policy["promotable_rows_now"], 0)
        self.assertFalse(policy["map_update_allowed"])
        self.assertIn("generator_version", policy["candidate_key"])

    def test_r214_control_triggers_prioritize_prompt_review(self) -> None:
        priority, mode, reason = r214_dimension_priority(2.996, 3.258)
        self.assertEqual(priority, "prioritize_review")
        self.assertEqual(mode, "pending")
        self.assertIn("review-required", reason)

        prompt_gate = r214_trigger_row(
            "prompt_review_budget",
            3.258,
            3.0,
            "<=",
            "ok",
            "prioritize prompt review",
        )
        stability_gate = r214_trigger_row(
            "head_stability_under_high_tail_threshold",
            65.217,
            80.0,
            ">=",
            "ok",
            "do not raise thresholds automatically",
        )

        self.assertFalse(prompt_gate["passed"])
        self.assertFalse(stability_gate["passed"])
        self.assertEqual(stability_gate["response"], "do not raise thresholds automatically")

    def test_r215_summary_scopes_frontend_renderer_model_not_dom(self) -> None:
        harness = {
            "membershipMatches": True,
            "pendingMembershipEqualsDisplay": True,
            "wrongDrilldownRejected": True,
            "candidatePromotionRejected": True,
            "modes": {
                "raw": {
                    "totalSupport": 12,
                    "bucketCount": 3,
                    "hiddenOtherRows": 0,
                },
                "display": {
                    "bucketCount": 2,
                    "hiddenOtherRows": 0,
                    "activeMergeRows": 1,
                },
                "pending": {
                    "bucketCount": 2,
                    "hiddenOtherRows": 0,
                    "candidateOverlayRows": 1,
                    "reviewRequiredRows": 1,
                    "reviewRequiredSupport": 2,
                },
            },
        }
        summary = r215_summarize(
            harness,
            {"summary": {"display_bucket_count": 2}},
            {"summary": {"pending_candidate_rows": 1}},
            {"tsc_ms": 10.0, "node_ms": 2.0},
        )

        self.assertTrue(summary["compiled_frontend_module"])
        self.assertTrue(summary["node_harness_executed"])
        self.assertFalse(summary["frontend_dom_renderer_exercised"])
        self.assertTrue(summary["wrong_drilldown_rejected"])
        self.assertTrue(summary["candidate_promotion_rejected"])

    def test_r216_summary_scopes_browser_dom_not_production_ui(self) -> None:
        browser_result = {
            "domReady": True,
            "modeButtons": 3,
            "renderedRows": 12,
            "currentModeAfterChecks": "pending",
            "visibleBucketCount": 2,
            "visibleTotalSupport": 12,
            "visibleCandidateOverlayRows": 1,
            "visibleReviewRequiredRows": 1,
            "membershipMatches": True,
            "pendingMembershipEqualsDisplay": True,
            "wrongDrilldownRejected": True,
            "candidatePromotionRejected": True,
            "checks": [
                {"check": "click_raw", "passed": True},
                {"check": "click_display", "passed": True},
                {"check": "click_pending", "passed": True},
            ],
            "modes": {
                "raw": {
                    "totalSupport": 12,
                    "bucketCount": 3,
                    "hiddenOtherRows": 0,
                },
                "display": {
                    "bucketCount": 2,
                    "hiddenOtherRows": 0,
                    "activeMergeRows": 1,
                },
                "pending": {
                    "bucketCount": 2,
                    "hiddenOtherRows": 0,
                    "candidateOverlayRows": 1,
                    "reviewRequiredRows": 1,
                    "reviewRequiredSupport": 2,
                },
            },
        }
        summary = r216_summarize(
            browser_result,
            {"summary": {"display_bucket_count": 2}},
            {"summary": {"pending_candidate_rows": 1}},
            {"summary": {"display_bucket_count": 2}},
            {"tsc_ms": 10.0},
            {"browser_ms": 20.0, "dom_dump_bytes": 1000, "screenshot_bytes": 2000},
        )

        self.assertTrue(summary["browser_dom_renderer_exercised"])
        self.assertTrue(summary["mode_clicks_verified"])
        self.assertEqual(summary["current_mode_after_checks"], "pending")
        self.assertEqual(summary["visible_candidate_overlay_rows"], 1)
        self.assertFalse(summary["production_agentflame_view_exercised"])
        self.assertFalse(summary["visual_drilldown_exercised"])
        self.assertTrue(summary["candidate_promotion_rejected"])

        gate = r216_claim_gate(summary, {"total_support": 12})
        self.assertTrue(gate["browser_dom_mode_smoke_supported"])
        self.assertTrue(gate["browser_dom_harness_supported"])
        self.assertFalse(gate["production_agentflame_view_supported"])
        self.assertFalse(gate["visual_drilldown_supported"])
        self.assertFalse(gate["semantic_adequacy_supported"])
        self.assertFalse(gate["canonicalization_quality_supported"])
        self.assertFalse(gate["developer_utility_supported"])
        self.assertFalse(gate["canonical_map_updated"])

    def test_r217_claim_gate_scopes_production_render_not_click_or_quality(self) -> None:
        summary = {
            "production_agentflame_view_exercised": True,
            "browser_dom_renderer_exercised": True,
            "display_panel_rendered": True,
            "mode_controls_rendered": True,
            "default_display_mode": "display",
            "visible_bucket_count": 1748,
            "visible_total_support": 482398,
            "membership_matches_display_map": True,
        }

        gate = r217_claim_gate(summary)

        self.assertTrue(gate["production_react_display_mode_smoke_supported"])
        self.assertTrue(gate["built_static_frontend"])
        self.assertTrue(gate["display_artifacts_loaded"])
        self.assertTrue(gate["support_preserved"])
        self.assertTrue(gate["mode_controls_rendered"])
        self.assertFalse(gate["mode_click_path_supported"])
        self.assertFalse(gate["visual_drilldown_supported"])
        self.assertFalse(gate["semantic_adequacy_supported"])
        self.assertFalse(gate["canonicalization_quality_supported"])
        self.assertFalse(gate["developer_utility_supported"])
        self.assertFalse(gate["canonical_map_updated"])

        wrong_default = {**summary, "default_display_mode": "raw"}
        self.assertFalse(r217_claim_gate(wrong_default)["production_react_display_mode_smoke_supported"])

    def test_r218_reviewed_display_map_diff_gate_rejects_unsafe_updates(self) -> None:
        display_rows = [
            {
                "dimension": "prompt",
                "raw_tag": "docupdate",
                "active_display_tag": "docupdate",
                "candidate_display_tag": "docs",
                "support": "7",
            },
            {
                "dimension": "llm",
                "raw_tag": "bpfanalyze",
                "active_display_tag": "bpfanalyze",
                "candidate_display_tag": "analyze",
                "support": "5",
            },
        ]
        review_rows = [
            {
                "case": "accept_profile",
                "dimension": "prompt",
                "raw_tag": "docupdate",
                "from_display_tag": "docupdate",
                "to_display_tag": "docs",
                "review_label": "promote",
                "review_source": "consensus",
                "label_state": "final",
                "candidate_valid": "True",
            },
            {
                "case": "reject_other",
                "dimension": "llm",
                "raw_tag": "bpfanalyze",
                "from_display_tag": "bpfanalyze",
                "to_display_tag": "other",
                "review_label": "promote",
                "review_source": "adjudicated",
                "label_state": "final",
                "candidate_valid": "True",
            },
            {
                "case": "reject_missing",
                "dimension": "prompt",
                "raw_tag": "missing",
                "from_display_tag": "missing",
                "to_display_tag": "review",
                "review_label": "promote",
                "review_source": "consensus",
                "label_state": "final",
                "candidate_valid": "True",
            },
            {
                "case": "reject_weak",
                "dimension": "llm",
                "raw_tag": "bpfanalyze",
                "from_display_tag": "bpfanalyze",
                "to_display_tag": "analyze",
                "review_label": "promote",
                "review_source": "single_label",
                "label_state": "weak_final",
                "candidate_valid": "True",
            },
        ]

        diff_rows, rejected_rows = r218_reviewed_display_diff_rows(display_rows, review_rows)
        preview = r218_preview_rows(display_rows, diff_rows)
        summary = r218_summarize(
            display_rows,
            [
                {**review_rows[0], "expected_result": "accepted"},
                {**review_rows[1], "expected_result": "rejected"},
                {**review_rows[2], "expected_result": "rejected"},
                {**review_rows[3], "expected_result": "rejected"},
            ],
            diff_rows,
            rejected_rows,
            preview,
        )

        self.assertTrue(r218_valid_display_tag("docs"))
        self.assertFalse(r218_valid_display_tag("other"))
        self.assertEqual(len(diff_rows), 1)
        self.assertEqual(diff_rows[0]["to_display_tag"], "docs")
        self.assertEqual(len(rejected_rows), 3)
        self.assertEqual(summary["original_total_support"], 12)
        self.assertEqual(summary["preview_total_support"], 12)
        self.assertTrue(summary["support_preserved"])
        self.assertTrue(summary["raw_key_coverage_preserved"])
        self.assertEqual(summary["hidden_other_rows"], 0)
        self.assertFalse(r218_claim_gate(summary)["reviewed_display_map_update_gate_supported"])

    def test_r211_tag_distribution_keeps_dimension_coverage(self) -> None:
        rows = [
            {
                "dimension": "session_tag_by_sessions",
                "rank": "1",
                "tag": "review",
                "count": "8",
                "share_pct": "80.0",
                "unit": "sessions",
            },
            {
                "dimension": "session_tag_by_sessions",
                "rank": "2",
                "tag": "docs",
                "count": "2",
                "share_pct": "20.0",
                "unit": "sessions",
            },
            {
                "dimension": "prompt_tag_by_system_effect_weight",
                "rank": "1",
                "tag": "refactor",
                "count": "7",
                "share_pct": "70.0",
                "unit": "system_effect_weight",
            },
        ]

        distribution = r211_tag_distribution_rows(rows, top_n=2)
        by_dimension = {(row["dimension"], row["rank"]): row for row in distribution}

        self.assertEqual(by_dimension[("session_tag_by_sessions", 1)]["tag"], "review")
        self.assertEqual(by_dimension[("session_tag_by_sessions", 1)]["coverage_top_5_pct"], 100.0)
        self.assertEqual(by_dimension[("session_tag_by_sessions", 1)]["unique_tags_in_dimension"], 2)
        self.assertEqual(by_dimension[("prompt_tag_by_system_effect_weight", 1)]["coverage_top_5_pct"], 70.0)

    def test_r211_baseline_collapse_groups_same_system_behavior_by_prompt(self) -> None:
        folded = Counter(
            {
                "project:p;agent:codex;session:refactor;prompt:refactor;call:tool/shell;process:cargo;effect:test;status:ok": 7,
                "project:p;agent:codex;session:review;prompt:review;call:tool/shell;process:cargo;effect:test;status:ok": 5,
                "project:p;agent:codex;session:docs;prompt:docs;call:tool/shell;process:cargo;effect:test;status:ok": 3,
                "project:p;agent:codex;session:docs;prompt:docs;call:tool/shell;process:rg;effect:read;status:ok": 9,
            }
        )

        rows = r211_baseline_collapse_rows(folded, top_n=3)
        cargo = next(row for row in rows if row["system_key"] == "process:cargo;effect:test;status:ok")

        self.assertEqual(cargo["total_weight"], 15)
        self.assertEqual(cargo["distinct_prompt_tags"], 3)
        self.assertEqual(cargo["top_prompt"], "refactor")
        self.assertEqual(cargo["ambiguous_weight"], 8)
        self.assertIn("review=5", cargo["top_prompt_splits"])
        self.assertIn("prompt:docs", cargo["example_semantic_stacks"])

    def test_r211_process_split_reports_non_top_prompt_weight(self) -> None:
        rows = r211_process_split_rows(
            [
                {
                    "process": "git",
                    "total_weight": "20",
                    "top_prompt": "review",
                    "top_prompt_weight": "5",
                    "top_prompt_share_pct": "25.0",
                    "distinct_prompt_tags": "4",
                    "top_prompt_splits": "review=5; refactor=5; docs=5; test=5",
                }
            ]
        )

        self.assertEqual(rows[0]["ambiguous_weight"], 15)
        self.assertEqual(rows[0]["ambiguous_share_pct"], 75.0)

    def test_r211_baseline_key_uses_process_effect_status_and_path(self) -> None:
        frames = r211_frames_from_stack(
            "project:p;agent:codex;session:review;prompt:review;call:tool/shell;"
            "process:rg;effect:read;path:collector/src;status:ok"
        )

        self.assertEqual(
            r211_baseline_key_for(frames),
            "process:rg;effect:read;status:ok;path:collector/src",
        )

    def test_r205_regeneration_summary_reports_candidates_only(self) -> None:
        rows = [
            {
                "dimension": "prompt",
                "raw_tag": "update",
                "regenerated_tag": "docs",
                "regenerated_valid": "True",
            },
            {
                "dimension": "prompt",
                "raw_tag": "ignored",
                "regenerated_tag": "ignored",
                "regenerated_valid": "True",
            },
            {
                "dimension": "llm",
                "raw_tag": "check",
                "regenerated_tag": "",
                "regenerated_valid": "False",
                "regeneration_error": "invalid",
            },
        ]

        summary = r205_summarize_regeneration(rows)

        self.assertEqual(summary["attempted_rows"], 3)
        self.assertEqual(summary["valid_rows"], 2)
        self.assertEqual(summary["invalid_rows"], 1)
        self.assertEqual(summary["changed_valid_rows"], 1)
        self.assertEqual(summary["grammar_valid_pct"], 66.667)
        self.assertEqual(summary["changed_valid_pct"], 50.0)

    def test_r207_count_nonblank_only_checks_return_fields(self) -> None:
        rows = [
            {"label": "", "notes": "", "candidate_tag": "review"},
            {"label": "adequate", "notes": "", "candidate_tag": "test"},
            {"label": "", "notes": "unclear fragment", "candidate_tag": "docs"},
        ]

        cells, rows_with_values = r207_count_nonblank(rows, ["label", "notes"])

        self.assertEqual(cells, 2)
        self.assertEqual(rows_with_values, 2)

    def test_r207_response_template_audit_keeps_blank_template_non_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "responses.csv"
            path.write_text(
                "\n".join(
                    [
                        "participant_id,order_index,packet_id,task_id,condition,response_json,task_time_seconds,confidence,notes",
                        "P01,1,UT01-trace-tree,UT01,trace-tree,{},,,",
                        "P01,2,UT02-semantic-stack,UT02,semantic-stack,{},,,",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            audit = r207_response_template_audit(path)

        self.assertTrue(audit["fields_match"])
        self.assertTrue(audit["blank"])
        self.assertEqual(audit["row_count"], 2)
        self.assertEqual(audit["real_response_like_rows"], 0)
        self.assertEqual(audit["participant_ids"], ["P01"])

    def test_r207_return_plan_maps_human_files_to_r195_inbox_names(self) -> None:
        required_inputs = {
            "r142_responses": {
                "path": "docs/visexp/out/human-evidence-r195/inbox/r142-pilot-responses.csv"
            },
            "r124_labeler_1": {
                "path": "docs/visexp/out/human-evidence-r195/inbox/r124-labeler-1.csv"
            },
            "r124_labeler_2": {
                "path": "docs/visexp/out/human-evidence-r195/inbox/r124-labeler-2.csv"
            },
            "r190_labeler_1": {
                "path": "docs/visexp/out/human-evidence-r195/inbox/r190-labeler-1.csv"
            },
            "r190_labeler_2": {
                "path": "docs/visexp/out/human-evidence-r195/inbox/r190-labeler-2.csv"
            },
            "r203_labeler_1": {
                "path": "docs/visexp/out/human-evidence-r195/inbox/r203-labeler-1.csv"
            },
            "r203_labeler_2": {
                "path": "docs/visexp/out/human-evidence-r195/inbox/r203-labeler-2.csv"
            },
        }

        plan = r207_build_return_plan(required_inputs)
        inbox_names = {row["r195_inbox_name"] for row in plan}
        inbox_names_by_key = {row["r195_input_key"]: row["r195_inbox_name"] for row in plan}

        self.assertEqual(
            inbox_names,
            {
                "r142-pilot-responses.csv",
                "r124-labeler-1.csv",
                "r124-labeler-2.csv",
                "r190-labeler-1.csv",
                "r190-labeler-2.csv",
                "r203-labeler-1.csv",
                "r203-labeler-2.csv",
            },
        )
        self.assertEqual(
            inbox_names_by_key,
            {key: Path(record["path"]).name for key, record in required_inputs.items()},
        )
        self.assertTrue(all("counts_as_evidence_when" in row for row in plan))

    def test_r195_no_inputs_waits_without_supporting_gates(self) -> None:
        readiness = r195_group_readiness(
            {
                "r124_labeler_1": False,
                "r124_labeler_2": False,
                "r190_labeler_1": False,
                "r190_labeler_2": False,
                "r142_responses": False,
            }
        )
        gates = {
            "c5_supported": False,
            "c6_adequacy_supported": False,
            "canonicalization_quality_supported": False,
        }

        self.assertEqual(readiness["overall_status"], "awaiting_human_inputs")
        self.assertFalse(readiness["any_present"])
        self.assertEqual(r195_pipeline_status(readiness, {}, gates), "awaiting_human_inputs")

    def test_r195_partial_inputs_do_not_run_scoring(self) -> None:
        readiness = r195_group_readiness(
            {
                "r124_labeler_1": True,
                "r124_labeler_2": False,
                "r190_labeler_1": False,
                "r190_labeler_2": False,
                "r142_responses": False,
            }
        )
        gates = {
            "c5_supported": False,
            "c6_adequacy_supported": False,
            "canonicalization_quality_supported": False,
        }

        self.assertEqual(readiness["overall_status"], "partial_human_inputs")
        self.assertTrue(readiness["r124"]["partial"])
        self.assertEqual(r195_pipeline_status(readiness, {}, gates), "partial_human_inputs")

    def test_r195_ready_no_run_is_not_scored_evidence(self) -> None:
        readiness = r195_group_readiness(
            {
                "r124_labeler_1": True,
                "r124_labeler_2": True,
                "r190_labeler_1": False,
                "r190_labeler_2": False,
                "r142_responses": False,
            }
        )
        operations = {"r124": {"status": "ready_no_run"}}
        gates = {
            "c5_supported": False,
            "c6_adequacy_supported": False,
            "canonicalization_quality_supported": False,
        }

        self.assertEqual(r195_pipeline_status(readiness, operations, gates), "ready_to_score_no_run")

    def test_r195_scored_false_gates_remain_no_supported_claims(self) -> None:
        readiness = r195_group_readiness(
            {
                "r124_labeler_1": True,
                "r124_labeler_2": True,
                "r190_labeler_1": True,
                "r190_labeler_2": True,
                "r142_responses": True,
            }
        )
        operations = {
            "r124": {"status": "human_labels_empty"},
            "r190": {"status": "human_labels_empty"},
            "r142": {"status": "participant_results_empty"},
        }
        gates = {
            "c5_supported": False,
            "c6_adequacy_supported": False,
            "canonicalization_quality_supported": False,
        }

        self.assertEqual(
            r195_pipeline_status(readiness, operations, gates),
            "scored_human_inputs_no_supported_gate",
        )

    def test_r195_r203_supported_gate_does_not_imply_c5_c6_or_map_update(self) -> None:
        readiness = r195_group_readiness(
            {
                "r203_labeler_1": True,
                "r203_labeler_2": True,
            }
        )
        operations = {
            "r203": {
                "status": "human_labels_scored",
                "claim_gate": {
                    "long_tail_promotion_review_supported": True,
                    "canonical_map_updated": False,
                },
            }
        }
        gates = {
            "c5_supported": False,
            "c6_adequacy_supported": False,
            "canonicalization_quality_supported": False,
            "long_tail_promotion_review_supported": True,
            "canonical_map_updated": False,
        }

        self.assertTrue(readiness["r203"]["ready"])
        self.assertEqual(r195_pipeline_status(readiness, operations, gates), "scored_human_inputs_with_supported_gate")
        self.assertFalse(gates["c5_supported"])
        self.assertFalse(gates["c6_adequacy_supported"])
        self.assertFalse(gates["canonical_map_updated"])

    def _r196_profile(
        self,
        *,
        row_count: int = 0,
        effect_weight: int = 0,
        event_count: int = 0,
        token_weight: int = 0,
        processes: Counter[str] | None = None,
        effects: Counter[str] | None = None,
        paths: Counter[str] | None = None,
        sessions: Counter[str] | None = None,
        prompts: Counter[str] | None = None,
        models: Counter[str] | None = None,
        kinds: Counter[str] | None = None,
    ) -> SimpleNamespace:
        return SimpleNamespace(
            row_count=row_count,
            effect_weight=effect_weight,
            event_count=event_count,
            token_weight=token_weight,
            processes=processes or Counter(),
            effects=effects or Counter(),
            paths=paths or Counter(),
            sessions=sessions or Counter(),
            prompts=prompts or Counter(),
            models=models or Counter(),
            kinds=kinds or Counter(),
        )

    def test_r196_keeps_semantic_head_despite_multipeak_profile(self) -> None:
        profile = self._r196_profile(
            effect_weight=1000,
            processes=Counter({"rg": 300, "sed": 250, "git": 200, "cargo": 150, "find": 100}),
            effects=Counter({"read": 800, "write": 200}),
            paths=Counter({"docs": 300, "collector": 250, "agentflame": 200, "tests": 150, "frontend": 100}),
            sessions=Counter({"refactor": 700, "review": 200, "test": 100}),
        )
        mapping = {
            "raw_tag": "refactor",
            "canonical_tag": "refactor",
            "action": "keep",
            "reason": "head",
            "support": "1000",
        }

        decision = governance_decision(mapping, profile, "prompt", GovernanceConfig())

        self.assertEqual(decision["governance_action"], "keep_head")
        self.assertFalse(decision["requires_review"])
        self.assertTrue(decision["is_multimodal"])

    def test_r196_flags_generic_multipeak_tag_for_contextual_split(self) -> None:
        profile = self._r196_profile(
            effect_weight=500,
            processes=Counter({"git": 150, "rg": 110, "sed": 100, "cargo": 80, "nl": 60}),
            effects=Counter({"read": 350, "write": 150}),
            paths=Counter({"docs": 170, "collector": 120, "agentflame": 110, "tests": 100}),
            sessions=Counter({"review": 250, "design": 140, "test": 110}),
        )
        mapping = {
            "raw_tag": "codex",
            "canonical_tag": "codex",
            "action": "keep",
            "reason": "low_confidence",
            "support": "500",
        }

        decision = governance_decision(mapping, profile, "prompt", GovernanceConfig())

        self.assertEqual(decision["governance_action"], "contextual_split_candidate")
        self.assertTrue(decision["requires_review"])
        self.assertTrue(decision["is_generic_or_noisy"])

    def test_r196_flags_generic_tail_for_regeneration(self) -> None:
        profile = self._r196_profile(
            effect_weight=20,
            processes=Counter({"rg": 8, "sed": 7, "git": 5}),
            effects=Counter({"read": 20}),
            paths=Counter({"docs": 20}),
            sessions=Counter({"review": 20}),
        )
        mapping = {
            "raw_tag": "update",
            "canonical_tag": "update",
            "action": "keep",
            "reason": "low_confidence",
            "support": "20",
        }

        decision = governance_decision(mapping, profile, "prompt", GovernanceConfig())

        self.assertEqual(decision["governance_action"], "regenerate_candidate")
        self.assertTrue(decision["is_long_tail"])
        self.assertTrue(decision["requires_review"])

    def test_r196_preserves_rare_distinct_tags(self) -> None:
        profile = self._r196_profile(
            effect_weight=2,
            processes=Counter({"cargo": 2}),
            effects=Counter({"read": 2}),
            paths=Counter({"agentflame": 2}),
            sessions=Counter({"benchmark": 2}),
        )
        mapping = {
            "raw_tag": "flame",
            "canonical_tag": "flame",
            "action": "keep",
            "reason": "no_candidate",
            "support": "2",
        }

        decision = governance_decision(mapping, profile, "prompt", GovernanceConfig())

        self.assertEqual(decision["governance_action"], "keep_rare_distinct")
        self.assertFalse(decision["requires_review"])

    def test_r196_keeps_existing_canonical_merge_auditable(self) -> None:
        profile = self._r196_profile(effect_weight=50, processes=Counter({"sed": 50}))
        mapping = {
            "raw_tag": "docsupdate",
            "canonical_tag": "docs",
            "action": "merge",
            "reason": "alias",
            "support": "50",
        }

        decision = governance_decision(mapping, profile, "prompt", GovernanceConfig())

        self.assertEqual(decision["governance_action"], "auto_canonicalize_existing")
        self.assertFalse(decision["requires_review"])

    def test_r196_regeneration_smoke_still_does_not_support_quality_claims(self) -> None:
        rows = [
            {
                "dimension": "prompt",
                "governance_action": "regenerate_candidate",
                "support": 20,
                "is_long_tail": True,
                "requires_review": True,
            }
        ]
        summary = r196_summarize(
            rows,
            {"enabled": True, "attempted": 1, "valid": 1, "invalid": 0, "failures": []},
        )
        gate = summary["claim_gate"]

        self.assertEqual(summary["status"], "long_tail_governance_candidates_ready_with_regeneration_smoke")
        self.assertTrue(gate["long_tail_governance_supported"])
        self.assertFalse(gate["semantic_adequacy_supported"])
        self.assertFalse(gate["canonicalization_quality_supported"])
        self.assertTrue(gate["llm_regeneration_is_candidate_only"])

    def test_r190_merge_audit_empty_labels_do_not_support_canonicalization(self) -> None:
        rows = [
            {
                "audit_id": "R190-0001",
                "audit_type": "overmerge_proxy",
                "dimension": "prompt",
                "raw_tag": "docupdate",
                "canonical_tag": "docs",
                "labeler_1": "",
                "labeler_2": "",
                "adjudicated_label": "",
            }
        ]

        _, summary = score_r190_merge_rows(rows)
        gate = r190_merge_claim_gate(summary)

        self.assertEqual(r190_merge_status(summary), "human_labels_empty")
        self.assertFalse(gate["canonicalization_quality_supported"])
        self.assertTrue(gate["requires_real_human_labels"])

    def test_r190_merge_audit_accepts_complete_low_risk_labels(self) -> None:
        rows = [
            {
                "audit_id": "R190-0001",
                "audit_type": "overmerge_proxy",
                "dimension": "prompt",
                "raw_tag": "docupdate",
                "canonical_tag": "docs",
                "labeler_1": "acceptable",
                "labeler_2": "ok",
                "adjudicated_label": "",
            },
            {
                "audit_id": "R190-0002",
                "audit_type": "undermerge_proxy",
                "dimension": "llm",
                "raw_tag": "testcodex",
                "canonical_tag": "test",
                "labeler_1": "acceptable",
                "labeler_2": "acceptable",
                "adjudicated_label": "",
            },
        ]

        _, summary = score_r190_merge_rows(rows)
        gate = r190_merge_claim_gate(summary)

        self.assertEqual(r190_merge_status(summary), "human_labels_scored")
        self.assertTrue(gate["canonicalization_quality_supported"])
        self.assertEqual(summary["overmerge_rate_pct"], 0.0)
        self.assertEqual(summary["undermerge_rate_pct"], 0.0)

    def test_r190_merge_audit_rejects_high_overmerge_rate(self) -> None:
        rows = [
            {
                "audit_id": "R190-0001",
                "audit_type": "overmerge_proxy",
                "dimension": "prompt",
                "raw_tag": "fix",
                "canonical_tag": "debug",
                "labeler_1": "overmerge",
                "labeler_2": "wrong_merge",
                "adjudicated_label": "",
            },
            {
                "audit_id": "R190-0002",
                "audit_type": "undermerge_proxy",
                "dimension": "prompt",
                "raw_tag": "testcodex",
                "canonical_tag": "test",
                "labeler_1": "acceptable",
                "labeler_2": "acceptable",
                "adjudicated_label": "",
            },
        ]

        _, summary = score_r190_merge_rows(rows)
        gate = r190_merge_claim_gate(summary)

        self.assertEqual(r190_merge_status(summary), "human_labels_scored")
        self.assertFalse(gate["canonicalization_quality_supported"])
        self.assertFalse(gate["overmerge_ok"])
        self.assertEqual(summary["overmerge_rate_pct"], 100.0)

    def test_r194_preflight_gate_recognizes_empty_collection_ready_state(self) -> None:
        manifest = {
            "claim_gate": {
                "c5_supported": False,
                "c6_adequacy_supported": False,
                "canonicalization_quality_supported": False,
                "long_tail_promotion_review_supported": False,
                "canonical_map_updated": False,
            }
        }
        files = [{"exists": True, "sha256_match": True}]
        sheets = {
            "r124_labeler_1": {"blank": True, "fields_match": True, "row_count": 300},
            "r124_labeler_2": {"blank": True, "fields_match": True, "row_count": 300},
            "r190_labeler_1": {"blank": True, "fields_match": True, "row_count": 160},
            "r190_labeler_2": {"blank": True, "fields_match": True, "row_count": 160},
            "r203_labeler_1": {"blank": True, "fields_match": True, "row_count": 41},
            "r203_labeler_2": {"blank": True, "fields_match": True, "row_count": 41},
            "r142_response_template": {"blank": True, "row_count": 70},
        }
        scores = {
            "r124": {"status": "human_labels_empty", "final_label_count": 0, "adequacy_supported": False},
            "r190": {
                "status": "human_labels_empty",
                "final_label_count": 0,
                "canonicalization_quality_supported": False,
            },
            "r203": {
                "status": "human_labels_empty",
                "final_label_count": 0,
                "long_tail_promotion_review_supported": False,
                "canonical_map_updated": False,
            },
            "r142": {"status": "participant_results_empty", "response_count": 0, "c5_supported": False},
            "r187": {"real_response_count": 0},
        }

        gate = r194_gate_status(manifest, files, sheets, scores)

        self.assertEqual(gate["status"], "ready_for_human_collection_no_outcomes")
        self.assertTrue(gate["ready_for_collection"])
        self.assertFalse(gate["c5_supported"])
        self.assertFalse(gate["c6_adequacy_supported"])
        self.assertFalse(gate["long_tail_promotion_review_supported"])

    def test_model_benchmark_size_class_accepts_local_small_models(self) -> None:
        self.assertEqual(r121_model_size_class("Qwen3-0.6B-FP32.gguf"), "0.6b")
        self.assertEqual(r121_model_size_class("tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf"), "1b")
        self.assertEqual(r121_model_size_class("qwen2.5-3b-instruct-q4_k_m.gguf"), "3b")

    def test_model_benchmark_gate_evidence_includes_classes(self) -> None:
        bench = {
            "run_id": "R180",
            "aggregate": {"total_runs": 6, "ok_runs": 6, "failed_runs": 0, "valid_run_pct": 100.0},
            "bench": {
                "models": [
                    {
                        "label": "0.6b",
                        "size_class": "0.6b",
                        "ok_runs": 3,
                        "latency_ms": [8, 9, 23],
                        "stability": {"exact_stable_fragments": 1, "fragment_count": 1},
                    },
                    {
                        "label": "1.1b",
                        "size_class": "1b",
                        "ok_runs": 3,
                        "latency_ms": [10, 11, 18],
                        "stability": {"exact_stable_fragments": 1, "fragment_count": 1},
                    },
                ]
            },
        }

        self.assertTrue(model_benchmark_valid(bench))
        self.assertEqual(model_benchmark_size_classes(bench), {"0.6b", "1b"})
        evidence = model_benchmark_evidence(bench)
        self.assertIn("model_benchmark=R180", evidence)
        self.assertIn("1.1b_class=1b", evidence)
        compact = compact_model_benchmark(
            {
                **bench,
                "bench": {
                    "runs_per_model": 3,
                    "fragments_per_model": 1,
                    "models": [
                        {
                            **bench["bench"]["models"][0],
                            "total_runs": 3,
                            "failed_runs": 0,
                            "valid_tags": 3,
                            "invalid_tags": [],
                            "fragments": [{"fragment_id": "f0", "preview": "redacted"}],
                        }
                    ],
                },
            }
        )
        self.assertNotIn("fragments", compact["bench"]["models"][0])

    def test_repeated_system_stack_is_collapsed(self) -> None:
        session = SessionRecord(source="codex", path=Path("session.jsonl"), session_id="s1")
        session.session_tag = "design"
        session.user_requests.append(UserRequest(0, None, "abc", "write docs", tag="design"))
        for idx in range(3):
            session.tools.append(
                ToolEvent(
                    ts_ms=None,
                    request_index=0,
                    tool_name="exec_command",
                    category="shell",
                    command="rg flamegraph docs",
                    command_name="rg",
                    effect="read",
                    status="ok",
                    path_groups=["docs/design"],
                    source_id=str(idx),
                )
            )

        system, token, _ = build_folded_stacks([session], "agentsight")

        self.assertEqual(sum(system.values()), 3)
        self.assertEqual(len(system), 1)
        self.assertIn("cmd:rg", next(iter(system)))
        self.assertEqual(token, Counter())

    def test_token_stack_uses_token_weight(self) -> None:
        session = SessionRecord(source="claude", path=Path("session.jsonl"), session_id="s2")
        session.session_tag = "audit"
        session.user_requests.append(UserRequest(0, None, "abc", "review code", tag="review"))
        session.llm_calls.append(
            LlmEvent(
                ts_ms=None,
                request_index=0,
                model="claude-opus",
                text_hash="def",
                preview="reviewed",
                input_tokens=10,
                output_tokens=5,
                cache_tokens=20,
                tag="review",
            )
        )

        _, token, _ = build_folded_stacks([session], "agentsight")

        self.assertEqual(sum(token.values()), 35)
        self.assertEqual(len(token), 3)
        self.assertTrue(any("kind:input" in stack for stack in token))
        self.assertTrue(any("kind:output" in stack for stack in token))
        self.assertTrue(any("kind:cache" in stack for stack in token))

    def test_nonsemantic_baseline_removes_prompt_frames(self) -> None:
        sessions = []
        for prompt_tag in ("design", "debug"):
            session = SessionRecord(source="codex", path=Path(f"{prompt_tag}.jsonl"), session_id=prompt_tag)
            session.session_tag = prompt_tag
            session.user_requests.append(UserRequest(0, None, prompt_tag, prompt_tag, tag=prompt_tag))
            session.tools.append(
                ToolEvent(
                    ts_ms=None,
                    request_index=0,
                    tool_name="exec_command",
                    category="shell",
                    command="git status",
                    command_name="git",
                    effect="read",
                    status="ok",
                )
            )
            sessions.append(session)

        system, _, _ = build_folded_stacks(sessions, "agentsight")
        nonsemantic = build_nonsemantic_system(system)

        self.assertEqual(sum(system.values()), 2)
        self.assertEqual(len(system), 2)
        self.assertEqual(len(nonsemantic), 1)
        self.assertNotIn("prompt:", next(iter(nonsemantic)))

    def test_dimension_views_project_without_changing_total_weight(self) -> None:
        system = Counter(
            {
                "project:agentsight;agent:codex;session:design;prompt:fix;tool:shell;cmd:git;effect:read;status:ok": 3,
                "project:agentsight;agent:codex;session:design;prompt:test;tool:shell;cmd:git;effect:read;status:ok": 2,
            }
        )
        token = Counter(
            {
                "project:agentsight;agent:codex;session:design;prompt:fix;llm:review;model:gpt;kind:input": 11,
                "project:agentsight;agent:codex;session:design;prompt:test;llm:review;model:gpt;kind:output": 7,
            }
        )

        prompt_only = project_folded(system, ("project:", "agent:", "prompt:", "cmd:", "effect:", "status:"))
        views = build_dimension_views(system, token)

        self.assertEqual(sum(prompt_only.values()), sum(system.values()))
        self.assertEqual(sum(views["session-system"].values()), sum(system.values()))
        self.assertEqual(sum(views["llm-token"].values()), sum(token.values()))
        self.assertNotIn("prompt:", next(iter(views["session-system"])))
        self.assertNotIn("session:", next(iter(views["prompt-system"])))

    def test_agent_diff_uses_rate_normalization(self) -> None:
        system = Counter(
            {
                "project:agentsight;agent:codex;session:x;prompt:x;tool:shell;cmd:git;effect:read;status:ok": 10,
                "project:agentsight;agent:codex;session:x;prompt:x;tool:shell;cmd:sed;effect:read;status:ok": 90,
                "project:agentsight;agent:claude;session:x;prompt:x;tool:shell;cmd:git;effect:read;status:ok": 5,
                "project:agentsight;agent:claude;session:x;prompt:x;tool:shell;cmd:sed;effect:read;status:ok": 5,
            }
        )

        diff = build_agent_diff(system)
        git_row = next(row for row in diff if "cmd:git" in row["stack"] and row["cohort"] == "top")

        self.assertEqual(git_row["codex"], 10)
        self.assertEqual(git_row["claude"], 5)
        self.assertEqual(git_row["winner"], "claude")
        self.assertAlmostEqual(git_row["codex_rate_per_1k"], 100.0)
        self.assertAlmostEqual(git_row["claude_rate_per_1k"], 500.0)

    def test_mixing_summary_detects_prompt_information_loss(self) -> None:
        system = Counter(
            {
                "project:agentsight;agent:codex;session:design;prompt:flamegraph;tool:shell;cmd:git;effect:read;status:ok": 3,
                "project:agentsight;agent:codex;session:debug;prompt:test;tool:shell;cmd:git;effect:read;status:ok": 2,
                "project:agentsight;agent:codex;session:debug;prompt:test;tool:shell;cmd:rg;effect:read;status:ok": 1,
            }
        )

        summary = mixing_summary(system, ("session:", "prompt:"), "nonsemantic")

        self.assertEqual(summary["mixed_bucket_count"], 1)
        self.assertEqual(summary["mixed_weight"], 5)
        self.assertEqual(summary["max_semantic_variants_per_bucket"], 2)

    def test_tag_quality_finds_same_hash_conflicts_and_generic_share(self) -> None:
        rows = [
            {"prompt_hash": "abc", "prompt_tag": "flamegraph"},
            {"prompt_hash": "abc", "prompt_tag": "visual"},
            {"prompt_hash": "def", "prompt_tag": "prompt"},
        ]
        sessions = [{"session_tag": "design"}]
        aggregation = {"tag_contract": {"invalid_count": 0}}

        quality = tag_quality(rows, sessions, aggregation)

        self.assertEqual(quality["same_hash_multi_tag_count"], 1)
        self.assertEqual(quality["invalid_prompt_tag_count"], 0)
        self.assertAlmostEqual(quality["generic_prompt_row_share_pct"], 33.333)

    def test_compression_summary_reports_collapsed_observations(self) -> None:
        stacks = Counter({"a;b": 4, "a;c": 1})

        summary = compression_summary(stacks)

        self.assertEqual(summary["total_observations"], 5)
        self.assertEqual(summary["unique_stacks"], 2)
        self.assertEqual(summary["collapsed_observations"], 3)
        self.assertEqual(summary["compression_ratio"], 2.5)

    def test_tag_stability_metrics_report_repeated_run_stability(self) -> None:
        rows = [
            {"annotator": "fallback", "fragment_id": "a", "tag": "debug", "valid": True, "generic": False},
            {"annotator": "fallback", "fragment_id": "a", "tag": "debug", "valid": True, "generic": False},
            {"annotator": "fallback", "fragment_id": "b", "tag": "work", "valid": True, "generic": True},
            {"annotator": "fallback", "fragment_id": "b", "tag": "work", "valid": True, "generic": True},
            {"annotator": "llama", "fragment_id": "a", "tag": "debug", "valid": True, "generic": False},
            {"annotator": "llama", "fragment_id": "a", "tag": "debug", "valid": True, "generic": False},
            {"annotator": "llama", "fragment_id": "b", "tag": "model", "valid": True, "generic": False},
            {"annotator": "llama", "fragment_id": "b", "tag": "model", "valid": True, "generic": False},
        ]

        metrics = annotator_metrics(rows)
        cross = cross_annotator_metrics(rows)
        verdict = smoke_verdict({"annotator_metrics": metrics})

        self.assertEqual(metrics["fallback"]["exact_stable_fragment_share_pct"], 100.0)
        self.assertEqual(metrics["fallback"]["generic_output_share_pct"], 50.0)
        self.assertEqual(cross["pairs"][0]["modal_exact_match_pct"], 50.0)
        self.assertEqual(verdict, "smoke_supported")

    def test_user_task_helpers_parse_variants_and_stack_frames(self) -> None:
        variants = parse_variants("session:a/prompt:b=7; session:c/prompt:d=2")
        stack = "project:agentsight;session:paper;prompt:debug;cmd:git;effect:read"

        self.assertEqual(variants[0]["semantic"], "session:a/prompt:b")
        self.assertEqual(variants[0]["weight"], 7)
        self.assertEqual(stack_frame(stack, "prompt:"), "debug")
        self.assertEqual(stack_frame(stack, "model:", "none"), "none")

    def test_user_task_percentile_uses_nearest_rank(self) -> None:
        values = [42, 13, 8, 18, 10, 10, 53, 38, 39, 67]

        self.assertEqual(percentile_nearest_rank(values, 50), 18)
        self.assertEqual(percentile_nearest_rank(values, 95), 67)

    def test_participant_packets_exclude_oracles(self) -> None:
        tasks = [
            {
                "task_id": "UTX",
                "claim": "C5",
                "skill": "demo",
                "title": "Demo",
                "question": "Find the answer.",
                "participant_view_conditions": [
                    {
                        "condition": "semantic-stack",
                        "views": ["semantic folded excerpt"],
                        "view_excerpt": [{"title": "semantic", "rows": [{"slice_id": "slice-a", "weight": 7}]}],
                    },
                ],
                "answer_format": {"weight": "int"},
            }
        ]

        packets = participant_packets(tasks)

        self.assertIn("semantic-stack", CONDITION_ORDER)
        self.assertEqual(packets[0]["packet_id"], "UTX-semantic-stack")
        self.assertNotIn("skill", packets[0])
        self.assertEqual(packets[0]["view_excerpt"][0]["rows"][0]["weight"], 7)
        self.assertNotIn("oracle", packets[0])
        self.assertFalse(any("oracle" in key for key in packets[0]))

    def test_participant_packets_reject_oracle_only_excerpt_keys(self) -> None:
        tasks = [
            {
                "task_id": "UTX",
                "claim": "C5",
                "skill": "demo",
                "title": "Demo",
                "question": "Find the answer.",
                "participant_view_conditions": [
                    {
                        "condition": "nonsemantic-stack",
                        "views": ["nonsemantic folded excerpt"],
                        "view_excerpt": [
                            {
                                "title": "bad",
                                "rows": [{"slice_id": "slice-a", "variant_count": 133}],
                            }
                        ],
                    },
                ],
                "answer_format": {"weight": "int"},
            }
        ]

        with self.assertRaises(AssertionError):
            participant_packets(tasks)

    def test_participant_packets_reject_condition_slice_mismatch(self) -> None:
        tasks = [
            {
                "task_id": "UTX",
                "claim": "C5",
                "skill": "demo",
                "title": "Demo",
                "question": "Find the answer.",
                "participant_view_conditions": [
                    {
                        "condition": "flat-summary",
                        "views": ["flat"],
                        "view_excerpt": [{"title": "flat", "rows": [{"slice_id": "slice-a", "weight": 7}]}],
                    },
                    {
                        "condition": "semantic-stack",
                        "views": ["semantic"],
                        "view_excerpt": [{"title": "semantic", "rows": [{"slice_id": "slice-b", "weight": 7}]}],
                    },
                ],
                "answer_format": {"weight": "int"},
            }
        ]

        with self.assertRaises(AssertionError):
            participant_packets(tasks)

    def test_r187_launch_scan_recurses_for_forbidden_keys(self) -> None:
        payload = {
            "participant_id": "P01",
            "tasks": [
                {
                    "packet_id": "UT01-semantic-stack",
                    "view_excerpt": [{"rows": [{"slice_id": "a", "oracle": {"answer": 7}}]}],
                }
            ],
        }

        hits = r187_scan_forbidden_keys(payload)

        self.assertEqual(hits, ["$.tasks[0].view_excerpt[0].rows[0].oracle"])

    def test_r187_launch_assignment_grouping_sorts_by_order(self) -> None:
        rows = [
            {"participant_id": "P02", "order_index": "2", "packet_id": "UT02-flat-summary"},
            {"participant_id": "P01", "order_index": "1", "packet_id": "UT01-semantic-stack"},
            {"participant_id": "P02", "order_index": "1", "packet_id": "UT01-trace-tree"},
        ]

        grouped = r187_group_assignments(rows)

        self.assertEqual(list(grouped), ["P01", "P02"])
        self.assertEqual([row["packet_id"] for row in grouped["P02"]], ["UT01-trace-tree", "UT02-flat-summary"])

    def test_user_task_assignments_cover_one_condition_per_task(self) -> None:
        tasks = [
            {
                "task_id": f"UT{idx:02d}",
                "participant_view_conditions": [{"condition": condition} for condition in CONDITION_ORDER],
            }
            for idx in range(1, 6)
        ]

        assignments = build_assignments(tasks)

        self.assertEqual(len(assignments), 25)
        self.assertEqual(len([row for row in assignments if row["participant_id"] == "P01"]), 5)
        self.assertEqual(
            sorted(row["condition"] for row in assignments if row["task_id"] == "UT01"),
            sorted(CONDITION_ORDER),
        )
        self.assertIn("event-count-proxy", CONDITION_ORDER)
        self.assertNotIn("span-duration", CONDITION_ORDER)

    def test_r142_preregistration_accepts_event_count_proxy_contract(self) -> None:
        tasks = []
        for idx in range(1, 15):
            tasks.append(
                {
                    "task_id": f"UT{idx:02d}",
                    "analysis_role": "primary_utility" if idx <= 8 else "limitation_check",
                    "participant_view_conditions": [{"condition": condition} for condition in CONDITION_ORDER],
                }
            )
        assignments = build_assignments(tasks)
        response_rows = [
            {
                **row,
                "response_json": "{}",
                "task_time_seconds": "",
                "confidence": "",
                "notes": "",
            }
            for row in assignments
        ]
        answer_rows = [{"task_id": task["task_id"]} for task in tasks]

        errors = validate_r142_preregistration(
            {"tasks": tasks, "condition_order": CONDITION_ORDER},
            assignments,
            answer_rows,
            response_rows,
            sorted(REQUIRED_RESPONSE_FIELDS),
        )

        self.assertEqual(errors, [])

    def test_r142_preregistration_rejects_span_duration_proxy_name(self) -> None:
        bad_conditions = [
            "trace-tree",
            "span-duration",
            "flat-summary",
            "nonsemantic-stack",
            "semantic-stack",
        ]
        tasks = [
            {
                "task_id": f"UT{idx:02d}",
                "analysis_role": "primary_utility" if idx <= 8 else "limitation_check",
                "participant_view_conditions": [{"condition": condition} for condition in bad_conditions],
            }
            for idx in range(1, 15)
        ]
        assignments = build_assignments(tasks)
        response_rows = [
            {
                **row,
                "response_json": "{}",
                "task_time_seconds": "",
                "confidence": "",
                "notes": "",
            }
            for row in assignments
        ]

        errors = validate_r142_preregistration(
            {"tasks": tasks, "condition_order": bad_conditions},
            assignments,
            [{"task_id": task["task_id"]} for task in tasks],
            response_rows,
            sorted(REQUIRED_RESPONSE_FIELDS),
        )

        self.assertTrue(any("span-duration" in error for error in errors))

    def test_effect_lineage_joins_child_process_effects_to_tool(self) -> None:
        snapshot = {
            "project": "agentsight",
            "sessions": [
                {
                    "id": "s1",
                    "agent_type": "codex",
                    "start_timestamp_ms": 1,
                    "attributes": {"session_tag": "debug"},
                }
            ],
            "tool_calls": [
                {
                    "id": "t1",
                    "session_id": "s1",
                    "timestamp_ms": 10,
                    "tool_name": "shell",
                    "tool_call_id": "call-1",
                    "start_timestamp_ms": 10,
                    "end_timestamp_ms": 100,
                    "input": {"prompt_tag": "test"},
                    "related_pid": 10,
                }
            ],
            "process_nodes": [
                {"id": "p10", "pid": 10, "root_pid": 10, "start_timestamp_ms": 10, "end_timestamp_ms": 100, "comm": "bash"},
                {"id": "p11", "pid": 11, "ppid": 10, "root_pid": 10, "start_timestamp_ms": 20, "end_timestamp_ms": 80, "comm": "cat"},
            ],
            "audit_events": [
                {
                    "id": "a1",
                    "timestamp_ms": 30,
                    "audit_type": "file",
                    "pid": 11,
                    "action": "read",
                    "target": "docs/visexp",
                    "status": "ok",
                    "details": {},
                }
            ],
        }

        rows, orphans, folded = lineage_rows(snapshot)

        self.assertEqual(len(rows), 1)
        self.assertEqual(orphans, [])
        self.assertEqual(rows[0]["join_method"], "pid_family_time_window")
        self.assertEqual(sum(folded.values()), 1)

    def test_effect_lineage_joins_child_when_related_process_node_is_missing(self) -> None:
        snapshot = {
            "project": "agentsight",
            "sessions": [{"id": "s1", "agent_type": "codex", "attributes": {"session_tag": "record"}}],
            "tool_calls": [
                {
                    "id": "t1",
                    "session_id": "s1",
                    "tool_name": "agent-run",
                    "start_timestamp_ms": 10,
                    "end_timestamp_ms": 100,
                    "input": {"prompt_tag": "record"},
                    "related_pid": 20,
                }
            ],
            "process_nodes": [
                {"id": "child", "pid": 21, "ppid": 20, "root_pid": 10, "start_timestamp_ms": 20, "end_timestamp_ms": 80, "comm": "git"},
            ],
            "audit_events": [
                {
                    "id": "a1",
                    "timestamp_ms": 30,
                    "audit_type": "process",
                    "pid": 21,
                    "action": "exec",
                    "target": "/usr/bin/git",
                    "status": "observed",
                    "details": {},
                }
            ],
        }

        rows, orphans, folded = lineage_rows(snapshot)

        self.assertEqual(len(rows), 1)
        self.assertEqual(orphans, [])
        self.assertEqual(rows[0]["join_method"], "pid_family_time_window")
        self.assertEqual(sum(folded.values()), 1)

    def test_effect_lineage_joins_root_pid_even_when_parent_node_is_missing(self) -> None:
        snapshot = {
            "project": "agentsight",
            "sessions": [{"id": "s1", "agent_type": "codex", "attributes": {"session_tag": "record"}}],
            "tool_calls": [
                {
                    "id": "t1",
                    "session_id": "s1",
                    "tool_name": "agent-run",
                    "start_timestamp_ms": 10,
                    "end_timestamp_ms": 100,
                    "input": {"prompt_tag": "record"},
                    "related_pid": 10,
                }
            ],
            "process_nodes": [
                {"id": "p10", "pid": 10, "root_pid": 10, "start_timestamp_ms": 10, "end_timestamp_ms": 100, "comm": "node"},
                {"id": "p12", "pid": 12, "ppid": 11, "root_pid": 10, "start_timestamp_ms": 20, "end_timestamp_ms": 80, "comm": "cut"},
            ],
            "audit_events": [
                {
                    "id": "a1",
                    "timestamp_ms": 30,
                    "audit_type": "process",
                    "pid": 12,
                    "action": "exec",
                    "target": "/usr/bin/cut",
                    "status": "observed",
                    "details": {},
                }
            ],
        }

        rows, orphans, folded = lineage_rows(snapshot)

        self.assertEqual(len(rows), 1)
        self.assertEqual(orphans, [])
        self.assertEqual(rows[0]["join_method"], "root_pid_time_window")
        self.assertEqual(sum(folded.values()), 1)

    def test_effect_lineage_rejects_out_of_window_process_event(self) -> None:
        snapshot = {
            "project": "agentsight",
            "sessions": [{"id": "s1", "attributes": {"session_tag": "debug"}}],
            "tool_calls": [
                {
                    "id": "t1",
                    "session_id": "s1",
                    "tool_name": "shell",
                    "start_timestamp_ms": 10,
                    "end_timestamp_ms": 100,
                    "input": {"prompt_tag": "test"},
                    "related_pid": 10,
                }
            ],
            "process_nodes": [
                {"id": "p10", "pid": 10, "start_timestamp_ms": 10, "end_timestamp_ms": 100, "comm": "bash"},
            ],
            "audit_events": [
                {
                    "id": "a1",
                    "timestamp_ms": 150,
                    "audit_type": "file",
                    "pid": 10,
                    "action": "read",
                    "target": "docs/visexp",
                    "status": "ok",
                }
            ],
        }

        rows, orphans, folded = lineage_rows(snapshot)

        self.assertEqual(len(rows), 1)
        self.assertEqual(len(orphans), 1)
        self.assertEqual(rows[0]["orphan_reason"], "missing_process_time_match")
        self.assertEqual(sum(folded.values()), 0)

    def test_effect_lineage_does_not_cross_pid_reuse(self) -> None:
        snapshot = {
            "project": "agentsight",
            "sessions": [{"id": "s1", "attributes": {"session_tag": "debug"}}],
            "tool_calls": [
                {
                    "id": "t1",
                    "session_id": "s1",
                    "tool_name": "shell",
                    "start_timestamp_ms": 10,
                    "end_timestamp_ms": 100,
                    "input": {"prompt_tag": "test"},
                    "related_pid": 10,
                }
            ],
            "process_nodes": [
                {"id": "old-root", "pid": 10, "start_timestamp_ms": 10, "end_timestamp_ms": 100, "comm": "bash"},
                {"id": "new-root", "pid": 10, "start_timestamp_ms": 200, "end_timestamp_ms": 300, "comm": "bash"},
                {"id": "new-child", "pid": 11, "ppid": 10, "start_timestamp_ms": 220, "end_timestamp_ms": 260, "comm": "cat"},
            ],
            "audit_events": [
                {
                    "id": "a1",
                    "timestamp_ms": 230,
                    "audit_type": "file",
                    "pid": 11,
                    "action": "read",
                    "target": "docs/visexp",
                    "status": "ok",
                }
            ],
        }

        rows, orphans, folded = lineage_rows(snapshot)

        self.assertEqual(len(rows), 1)
        self.assertEqual(len(orphans), 1)
        self.assertEqual(rows[0]["process_id"], "new-child")
        self.assertEqual(rows[0]["orphan_reason"], "missing_tool_ancestry")
        self.assertEqual(sum(folded.values()), 0)

    def test_r114_precision_recall_counts_negative_control_false_positive(self) -> None:
        snapshot = {
            "audit_events": [
                {"id": "agent-joined", "audit_type": "file", "target": "docs/visexp/STATE.md"},
                {"id": "agent-orphan", "audit_type": "file", "target": "docs/visexp/MISSING.md"},
                {"id": "neg-joined", "audit_type": "file", "target": "/tmp/R114_NEGATIVE_CONTROL_x/file.txt"},
                {"id": "neg-orphan", "audit_type": "file", "target": "/tmp/R114_NEGATIVE_CONTROL_x/other.txt"},
            ]
        }
        rows = [
            {"event_id": "agent-joined", "joined": "True"},
            {"event_id": "agent-orphan", "joined": "False"},
            {"event_id": "neg-joined", "joined": "True"},
            {"event_id": "neg-orphan", "joined": "False"},
        ]

        summary = precision_recall_summary(snapshot, rows, ["R114_NEGATIVE_CONTROL_x"])

        self.assertEqual(summary["negative_effect_events_observed"], 2)
        self.assertEqual(summary["negative_joined_effect_events"], 1)
        self.assertEqual(summary["true_positives"], 1)
        self.assertEqual(summary["false_positives"], 1)
        self.assertEqual(summary["false_negatives"], 1)
        self.assertEqual(summary["precision_pct"], 50.0)
        self.assertEqual(summary["recall_pct"], 50.0)

    def test_r114_task_command_skips_git_check_for_disposable_workspaces(self) -> None:
        repo_task = Task("repo", "read", "prompt")
        disposable_task = Task("tmp", "edit", "prompt", workspace="doc_note", sandbox="workspace-write")

        repo_cmd = task_command(repo_task, Path("/repo"), Path("/tmp/answer.txt"), "codex")
        disposable_cmd = task_command(disposable_task, Path("/tmp/task"), Path("/tmp/answer.txt"), "codex")

        self.assertNotIn("--skip-git-repo-check", repo_cmd)
        self.assertIn("--skip-git-repo-check", disposable_cmd)
        self.assertLess(disposable_cmd.index("--skip-git-repo-check"), disposable_cmd.index("--output-last-message"))

    def test_r114_precision_recall_scopes_agent_process_family(self) -> None:
        tool_id = "record:codex:20:agent-run"
        snapshot = {
            "tool_calls": [
                {
                    "id": tool_id,
                    "related_pid": 20,
                    "view_source": "record_capture_time_agent_envelope",
                }
            ],
            "process_nodes": [
                {"id": "wrapper", "pid": 10, "ppid": 1, "start_timestamp_ms": 100, "end_timestamp_ms": 500},
                {"id": "agent", "pid": 20, "ppid": 10, "start_timestamp_ms": 110, "end_timestamp_ms": 480},
                {"id": "agent-child", "pid": 21, "ppid": 20, "start_timestamp_ms": 130, "end_timestamp_ms": 180},
                {"id": "sibling", "pid": 30, "ppid": 10, "start_timestamp_ms": 120, "end_timestamp_ms": 470},
            ],
            "audit_events": [
                {"id": "agent-event", "audit_type": "process", "target": "codex"},
                {"id": "agent-child-event", "audit_type": "file", "target": "docs/visexp/STATE.md"},
                {"id": "wrapper-event", "audit_type": "process", "target": "bash"},
                {"id": "negative-event", "audit_type": "file", "target": "/tmp/R114_NEGATIVE_CONTROL_y/file.txt"},
            ],
        }
        rows = [
            {"event_id": "agent-event", "process_id": "agent", "tool_id": tool_id, "joined": "True"},
            {"event_id": "agent-child-event", "process_id": "agent-child", "tool_id": tool_id, "joined": "True"},
            {"event_id": "wrapper-event", "process_id": "wrapper", "tool_id": "", "joined": "False"},
            {"event_id": "negative-event", "process_id": "sibling", "tool_id": "", "joined": "False"},
        ]

        summary = precision_recall_summary(snapshot, rows, ["R114_NEGATIVE_CONTROL_y"])

        self.assertEqual(summary["agent_process_count"], 2)
        self.assertEqual(summary["in_scope_effect_events"], 2)
        self.assertEqual(summary["out_of_scope_effect_events"], 1)
        self.assertEqual(summary["negative_effect_events_observed"], 1)
        self.assertEqual(summary["negative_joined_effect_events"], 0)
        self.assertEqual(summary["true_positives"], 2)
        self.assertEqual(summary["false_negatives"], 0)
        self.assertEqual(summary["precision_pct"], 100.0)
        self.assertEqual(summary["recall_pct"], 100.0)

    def test_r114_precision_recall_scopes_missing_agent_root_children(self) -> None:
        tool_id = "record:codex:20:agent-run"
        snapshot = {
            "tool_calls": [
                {
                    "id": tool_id,
                    "related_pid": 20,
                    "view_source": "record_capture_time_agent_envelope",
                }
            ],
            "process_nodes": [
                {"id": "wrapper", "pid": 10, "ppid": 1, "start_timestamp_ms": 100, "end_timestamp_ms": 500},
                {"id": "agent-child", "pid": 21, "ppid": 20, "start_timestamp_ms": 130, "end_timestamp_ms": 180},
                {"id": "sibling", "pid": 30, "ppid": 10, "start_timestamp_ms": 120, "end_timestamp_ms": 470},
            ],
            "audit_events": [
                {"id": "agent-child-event", "audit_type": "file", "target": "docs/visexp/STATE.md"},
                {"id": "wrapper-event", "audit_type": "process", "target": "bash"},
                {"id": "negative-event", "audit_type": "file", "target": "/tmp/R114_NEGATIVE_CONTROL_z/file.txt"},
            ],
        }
        rows = [
            {"event_id": "agent-child-event", "process_id": "agent-child", "tool_id": tool_id, "joined": "True"},
            {"event_id": "wrapper-event", "process_id": "wrapper", "tool_id": "", "joined": "False"},
            {"event_id": "negative-event", "process_id": "sibling", "tool_id": "", "joined": "False"},
        ]

        summary = precision_recall_summary(snapshot, rows, ["R114_NEGATIVE_CONTROL_z"])

        self.assertEqual(summary["agent_process_count"], 1)
        self.assertEqual(summary["in_scope_effect_events"], 1)
        self.assertEqual(summary["out_of_scope_effect_events"], 1)
        self.assertEqual(summary["true_positives"], 1)
        self.assertEqual(summary["false_negatives"], 0)
        self.assertEqual(summary["negative_joined_effect_events"], 0)
        self.assertEqual(summary["recall_pct"], 100.0)

    def test_r182_network_aggregate_counts_joined_and_orphan_rows(self) -> None:
        rows = [
            {
                "network_lineage": {
                    "network_effect_events": 2,
                    "joined_network_effect_events": 1,
                    "orphan_network_effect_events": 1,
                    "target_specific_network_effect_events": 1,
                    "joined_target_specific_network_effect_events": 1,
                    "orphan_target_specific_network_effect_events": 0,
                    "network_target_groups": {"127.0.0.1:3000": 2},
                    "target_specific_network_target_groups": {"127.0.0.1:3000": 1},
                    "network_actions": {"connect": 2},
                    "network_join_methods": {"pid_family_time_window": 1, "orphan": 1},
                    "network_process_comms": {"python3": 1, "codex": 1},
                }
            },
            {
                "network_lineage": {
                    "network_effect_events": 1,
                    "joined_network_effect_events": 1,
                    "orphan_network_effect_events": 0,
                    "target_specific_network_effect_events": 1,
                    "joined_target_specific_network_effect_events": 1,
                    "orphan_target_specific_network_effect_events": 0,
                    "network_target_groups": {"localhost:8080": 1},
                    "target_specific_network_target_groups": {"localhost:8080": 1},
                    "network_actions": {"accept": 1},
                    "network_join_methods": {"root_pid_time_window": 1},
                    "network_process_comms": {"python3": 1},
                }
            },
        ]

        summary = aggregate_network(rows)

        self.assertEqual(summary["network_effect_events"], 3)
        self.assertEqual(summary["joined_network_effect_events"], 2)
        self.assertEqual(summary["orphan_network_effect_events"], 1)
        self.assertEqual(summary["target_specific_network_effect_events"], 2)
        self.assertEqual(summary["joined_target_specific_network_effect_events"], 2)
        self.assertEqual(summary["orphan_target_specific_network_effect_events"], 0)
        self.assertEqual(summary["tasks_with_network_effects"], 2)
        self.assertEqual(summary["tasks_with_joined_network_effects"], 2)
        self.assertEqual(summary["tasks_with_target_specific_network_effects"], 2)
        self.assertAlmostEqual(summary["network_join_pct"], 66.667)
        self.assertAlmostEqual(summary["target_specific_network_join_pct"], 100.0)
        self.assertEqual(summary["network_target_groups"]["127.0.0.1:3000"], 2)
        self.assertEqual(summary["network_process_comms"]["python3"], 2)

    def test_r182_gate_requires_network_rows_and_clean_negative_controls(self) -> None:
        aggregate_result = {
            "target_statuses": {"completed": 2},
            "precision_pct": 100.0,
            "recall_pct": 100.0,
            "negative_effect_events_observed": 12,
            "negative_joined_effect_events": 0,
            "negative_control_tasks_observed": 2,
        }
        network_result = {
            "network_effect_events": 4,
            "joined_network_effect_events": 4,
            "orphan_network_effect_events": 0,
            "target_specific_network_effect_events": 2,
            "joined_target_specific_network_effect_events": 2,
            "orphan_target_specific_network_effect_events": 0,
        }

        self.assertTrue(network_gate(aggregate_result, network_result, 2))

        self.assertFalse(network_gate(aggregate_result, {**network_result, "network_effect_events": 0}, 2))
        self.assertFalse(network_gate(aggregate_result, {**network_result, "orphan_network_effect_events": 1}, 2))
        self.assertFalse(network_gate(aggregate_result, {**network_result, "target_specific_network_effect_events": 0}, 2))
        self.assertFalse(network_gate(aggregate_result, {**network_result, "joined_target_specific_network_effect_events": 1}, 2))
        self.assertFalse(network_gate({**aggregate_result, "negative_joined_effect_events": 1}, network_result, 2))

    def test_evaluator_network_lineage_support_requires_negative_controls(self) -> None:
        artifact = {
            "status": "ok",
            "aggregate": {
                "tasks": 2,
                "precision_pct": 100.0,
                "recall_pct": 100.0,
                "negative_effect_events_observed": 9,
                "negative_joined_effect_events": 0,
                "negative_control_tasks_observed": 2,
            },
            "network_aggregate": {
                "network_effect_events": 4,
                "joined_network_effect_events": 4,
                "orphan_network_effect_events": 0,
                "target_specific_network_effect_events": 2,
                "joined_target_specific_network_effect_events": 2,
                "orphan_target_specific_network_effect_events": 0,
            },
        }

        self.assertTrue(network_lineage_supported(artifact))
        self.assertFalse(
            network_lineage_supported(
                {
                    **artifact,
                    "aggregate": {
                        **artifact["aggregate"],
                        "negative_effect_events_observed": 0,
                    },
                }
            )
        )
        self.assertFalse(
            network_lineage_supported(
                {
                    **artifact,
                    "network_aggregate": {
                        **artifact["network_aggregate"],
                        "target_specific_network_effect_events": 0,
                    },
                }
            )
        )
        self.assertFalse(
            network_lineage_supported(
                {
                    **artifact,
                    "aggregate": {
                        **artifact["aggregate"],
                        "negative_control_tasks_observed": 1,
                    },
                }
            )
        )

    def test_live_lineage_harness_scopes_detected_agent_process_family(self) -> None:
        snapshot = {
            "project": "agentsight",
            "sessions": [],
            "tool_calls": [],
            "process_nodes": [
                {
                    "id": "p10",
                    "pid": 10,
                    "start_timestamp_ms": 10,
                    "end_timestamp_ms": 100,
                    "comm": "codex",
                },
                {
                    "id": "p11",
                    "pid": 11,
                    "ppid": 10,
                    "start_timestamp_ms": 20,
                    "end_timestamp_ms": 80,
                    "comm": "cat",
                },
            ],
            "audit_events": [
                {
                    "id": "root",
                    "timestamp_ms": 10,
                    "audit_type": "process",
                    "pid": 10,
                    "action": "exec",
                    "comm": "codex",
                    "target": "/usr/bin/codex",
                    "summary": "codex exec --skip-git-repo-check fix prompt tags",
                    "status": "ok",
                    "details": {"full_command": "codex exec --skip-git-repo-check fix prompt tags"},
                },
                {
                    "id": "child-read",
                    "timestamp_ms": 30,
                    "audit_type": "file",
                    "pid": 11,
                    "action": "read",
                    "target": "docs/visexp/DESIGN.md",
                    "status": "ok",
                },
                {
                    "id": "unrelated",
                    "timestamp_ms": 35,
                    "audit_type": "network",
                    "pid": 99,
                    "action": "connect",
                    "target": "example.com:443",
                    "status": "ok",
                },
            ],
        }

        enriched, metrics = synthesize(snapshot, scope_covered_effects=True)
        rows, orphans, folded = lineage_rows(enriched)

        self.assertEqual(metrics["detected_agent_roots"], 1)
        self.assertEqual(metrics["synthesized_sessions"], 1)
        self.assertEqual(metrics["synthesized_tool_calls"], 1)
        self.assertEqual(metrics["covered_effect_events"], 2)
        self.assertEqual(metrics["excluded_out_of_scope_effect_events"], 1)
        self.assertEqual(len(rows), 2)
        self.assertEqual(orphans, [])
        self.assertEqual({row["prompt_tag"] for row in rows}, {"prompt"})
        self.assertEqual(sum(folded.values()), 2)

    def test_user_task_scoring_detects_exact_and_false_positive_fields(self) -> None:
        answer = {"weight": 7, "stack": "cmd:git", "semantic_adequacy_proven": False}
        required = ["weight", "stack", "semantic_adequacy_proven"]
        exact = score_response(
            {
                "participant_id": "p1",
                "packet_id": "UTX-semantic",
                "task_id": "UTX",
                "condition": "semantic",
                "response_json": '{"weight": "7", "stack": "cmd:git", "semantic_adequacy_proven": false}',
                "task_time_seconds": "11.5",
                "confidence": "4",
            },
            answer,
            required,
        )
        wrong = score_response(
            {
                "participant_id": "p2",
                "packet_id": "UTX-flat",
                "task_id": "UTX",
                "condition": "flat",
                "response_json": '{"weight": 8, "stack": "cmd:git", "semantic_adequacy_proven": false, "extra": "x"}',
                "task_time_seconds": "20",
                "confidence": "2",
            },
            answer,
            required,
        )

        self.assertTrue(exact["exact"])
        self.assertEqual(exact["field_accuracy_pct"], 100.0)
        self.assertFalse(wrong["exact"])
        self.assertEqual(wrong["mismatched_fields"], ["weight"])
        self.assertEqual(wrong["extra_fields"], ["extra"])
        self.assertEqual(wrong["false_positive_count"], 2)

    def test_user_task_summary_groups_by_condition(self) -> None:
        rows = [
            {"condition": "semantic", "task_id": "UT1", "participant_id": "p1", "exact": True, "field_accuracy_pct": 100.0, "task_time_seconds": 10.0, "confidence": 5.0, "false_positive_count": 0, "parse_error": ""},
            {"condition": "flat", "task_id": "UT1", "participant_id": "p2", "exact": False, "field_accuracy_pct": 50.0, "task_time_seconds": 20.0, "confidence": 2.0, "false_positive_count": 1, "parse_error": ""},
        ]

        summary = summarize(rows)

        self.assertEqual(summary["overall"]["response_count"], 2)
        self.assertEqual(summary["overall"]["exact_accuracy_pct"], 50.0)
        self.assertEqual(summary["by_condition"]["semantic"]["exact_accuracy_pct"], 100.0)
        self.assertEqual(summary["by_condition"]["flat"]["false_positive_count"], 1)

    def test_user_task_empty_summary_uses_null_metrics(self) -> None:
        summary = summarize([])

        self.assertEqual(summary["overall"]["response_count"], 0)
        self.assertIsNone(summary["overall"]["exact_accuracy_pct"])
        self.assertIsNone(summary["overall"]["mean_time_seconds"])
        self.assertIsNone(summary["overall"]["false_positive_count"])

    def test_user_task_scoring_ignores_empty_template_rows(self) -> None:
        self.assertTrue(
            is_placeholder_response(
                {
                    "participant_id": "P01",
                    "task_id": "UT1",
                    "condition": "semantic",
                    "response_json": "{}",
                    "task_time_seconds": "",
                    "confidence": "",
                }
            )
        )
        self.assertFalse(
            is_placeholder_response(
                {
                    "participant_id": "p1",
                    "task_id": "UT1",
                    "condition": "semantic",
                    "response_json": "{}",
                    "task_time_seconds": "12",
                    "confidence": "3",
                }
            )
        )

    def test_user_task_claim_analysis_empty_results_do_not_support_c5(self) -> None:
        analysis = claim_analysis([], {"tasks": []})

        self.assertEqual(analysis["status"], "participant_results_empty")
        self.assertFalse(analysis["claim_gate"]["c5_supported"])
        self.assertTrue(analysis["claim_gate"]["requires_real_participants"])
        self.assertIsNone(analysis["primary_utility"])

    def balanced_user_task_rows(self, participants: int = 12) -> tuple[list[dict[str, object]], list[dict[str, str]]]:
        tasks = [
            {"task_id": f"UT{idx:02d}", "analysis_role": "primary_utility"}
            for idx in range(1, 9)
        ]
        rows = []
        condition_order = [*BASELINE_CONDITIONS, SEMANTIC_CONDITION]
        for participant_idx in range(participants):
            participant_id = f"P{participant_idx + 1:02d}"
            for task_idx, task in enumerate(tasks):
                condition = condition_order[(participant_idx + task_idx) % len(condition_order)]
                semantic = condition == SEMANTIC_CONDITION
                rows.append(
                    {
                        "participant_id": participant_id,
                        "packet_id": f"{task['task_id']}-{condition}",
                        "task_id": task["task_id"],
                        "condition": condition,
                        "task_time_seconds": 8.0 if semantic else 12.0,
                        "confidence": 5.0 if semantic else 3.0,
                        "exact": semantic,
                        "field_accuracy_pct": 100.0 if semantic else 50.0,
                        "false_positive_count": 0,
                        "parse_error": "",
                    }
                )
        return rows, tasks

    def test_user_task_claim_analysis_uses_paper_scale_gate(self) -> None:
        rows, tasks = self.balanced_user_task_rows()

        analysis = claim_analysis(rows, {"tasks": tasks})

        self.assertTrue(analysis["claim_gate"]["c5_supported"])
        self.assertTrue(analysis["claim_gate"]["pilot_ready"])
        self.assertTrue(analysis["claim_gate"]["paper_model_ready"])
        self.assertEqual(analysis["paper_scale_primary"]["successful_comparison_count"], len(BASELINE_CONDITIONS))
        for comparison in analysis["paper_scale_primary"]["comparisons"]:
            self.assertEqual(comparison["task_pair_count"], 8)
            self.assertGreaterEqual(comparison["model_accuracy_delta_pp"], 90.0)
            self.assertEqual(comparison["median_task_time_reduction_pct"], 33.333)
            self.assertLessEqual(comparison["accuracy_holm_p_value"], 0.05)

    def test_user_task_claim_analysis_requires_enough_participants(self) -> None:
        rows, tasks = self.balanced_user_task_rows(participants=5)

        analysis = claim_analysis(rows, {"tasks": tasks})

        self.assertFalse(analysis["claim_gate"]["c5_supported"])
        self.assertFalse(analysis["claim_gate"]["enough_participants_for_claim"])
        self.assertTrue(analysis["claim_gate"]["pilot_ready"])

    def test_user_task_sign_flip_p_value_handles_zero_deltas(self) -> None:
        self.assertEqual(paired_sign_flip_p_value([0.0, 0.0], "greater"), 1.0)
        self.assertEqual(paired_sign_flip_p_value([1.0, 1.0], "greater"), 0.25)

    def test_user_task_response_contract_rejects_bad_measurements_and_duplicates(self) -> None:
        bundle = {
            "tasks": [
                {
                    "task_id": "UT01",
                    "participant_view_conditions": [
                        {"condition": "semantic-stack"},
                    ],
                }
            ]
        }
        assignment = [
            {
                "participant_id": "P01",
                "order_index": "1",
                "task_id": "UT01",
                "condition": "semantic-stack",
                "packet_id": "UT01-semantic-stack",
            }
        ]
        response = {
            **assignment[0],
            "response_json": "{\"answer\": true}",
            "task_time_seconds": "fast",
            "confidence": "9",
            "notes": "",
        }
        contract = validate_response_contract([response, response], bundle, assignment)

        self.assertFalse(contract["valid"])
        self.assertTrue(any("duplicate response" in error for error in contract["errors"]))
        self.assertTrue(any("invalid task_time_seconds" in error for error in contract["errors"]))
        self.assertTrue(any("invalid confidence" in error for error in contract["errors"]))

    def test_tag_adequacy_empty_rows_do_not_support_c6(self) -> None:
        rows = [
            {
                "fragment_index": "0",
                "fragment_hash": "abc",
                "kind": "prompt",
                "source": "codex",
                "labeler_1": "",
                "labeler_2": "",
                "adjudicated_label": "",
            }
        ]

        scored, summary = score_tag_adequacy_rows(rows)
        gate = tag_adequacy_claim_gate(summary)

        self.assertEqual(scored[0]["label_state"], "unlabeled")
        self.assertEqual(tag_adequacy_status(summary), "human_labels_empty")
        self.assertEqual(summary["final_label_count"], 0)
        self.assertIsNone(summary["adequate_share_pct"])
        self.assertFalse(gate["adequacy_supported"])
        self.assertTrue(gate["requires_real_human_labels"])

    def test_tag_adequacy_scores_agreement_and_label_shares(self) -> None:
        rows = [
            {
                "fragment_index": "0",
                "fragment_hash": "a",
                "kind": "prompt",
                "source": "codex",
                "candidate_tag": "review",
                "labeler_1": "adequate",
                "labeler_2": "good",
                "adjudicated_label": "",
            },
            {
                "fragment_index": "1",
                "fragment_hash": "b",
                "kind": "llm",
                "source": "claude",
                "candidate_tag": "task",
                "labeler_1": "generic/noisy",
                "labeler_2": "generic-noisy",
                "adjudicated_label": "",
            },
            {
                "fragment_index": "2",
                "fragment_hash": "c",
                "kind": "session",
                "source": "codex",
                "candidate_tag": "debug",
                "labeler_1": "misleading",
                "labeler_2": "wrong",
                "adjudicated_label": "",
            },
        ]

        _, summary = score_tag_adequacy_rows(rows)

        self.assertEqual(tag_adequacy_status(summary), "human_labels_scored")
        self.assertEqual(summary["final_label_counts"]["adequate"], 1)
        self.assertEqual(summary["final_label_counts"]["generic_noisy"], 1)
        self.assertEqual(summary["final_label_counts"]["misleading"], 1)
        self.assertEqual(summary["inter_labeler_agreement_pct"], 100.0)
        self.assertEqual(cohen_kappa([("adequate", "adequate"), ("misleading", "misleading")]), 1.0)
        self.assertFalse(tag_adequacy_claim_gate(summary)["adequacy_supported"])

    def test_tag_adequacy_gate_requires_candidate_tags_and_strong_labels(self) -> None:
        strong_rows = [
            {
                "fragment_index": str(idx),
                "fragment_hash": f"h{idx}",
                "kind": "prompt",
                "source": "codex",
                "candidate_tag": "review",
                "labeler_1": "adequate",
                "labeler_2": "adequate",
                "adjudicated_label": "",
            }
            for idx in range(3)
        ]
        _, strong_summary = score_tag_adequacy_rows(strong_rows)
        strong_gate = tag_adequacy_claim_gate(strong_summary)

        self.assertTrue(strong_gate["complete_candidate_tags"])
        self.assertTrue(strong_gate["complete_strong_final_labels"])
        self.assertTrue(strong_gate["adequacy_supported"])

        single_label_rows = [
            {
                **row,
                "labeler_2": "",
            }
            for row in strong_rows
        ]
        _, single_summary = score_tag_adequacy_rows(single_label_rows)
        single_gate = tag_adequacy_claim_gate(single_summary)

        self.assertEqual(single_summary["single_label_count"], 3)
        self.assertFalse(single_gate["complete_strong_final_labels"])
        self.assertFalse(single_gate["adequacy_supported"])

        missing_tag_rows = [
            {
                **row,
                "candidate_tag": "",
            }
            for row in strong_rows
        ]
        _, missing_tag_summary = score_tag_adequacy_rows(missing_tag_rows)
        missing_tag_gate = tag_adequacy_claim_gate(missing_tag_summary)

        self.assertFalse(missing_tag_gate["complete_candidate_tags"])
        self.assertFalse(missing_tag_gate["adequacy_supported"])

    def test_tag_adequacy_gate_rejects_adjudicated_only_rows(self) -> None:
        rows = [
            {
                "fragment_index": "0",
                "fragment_hash": "h0",
                "kind": "prompt",
                "source": "codex",
                "candidate_tag": "review",
                "labeler_1": "adequate",
                "labeler_2": "adequate",
                "adjudicated_label": "",
            },
            {
                "fragment_index": "1",
                "fragment_hash": "h1",
                "kind": "prompt",
                "source": "codex",
                "candidate_tag": "review",
                "labeler_1": "",
                "labeler_2": "",
                "adjudicated_label": "adequate",
            },
        ]

        _, summary = score_tag_adequacy_rows(rows)
        gate = tag_adequacy_claim_gate(summary)

        self.assertEqual(summary["final_label_count"], 2)
        self.assertEqual(summary["strong_final_label_count"], 2)
        self.assertEqual(summary["both_labeler_count"], 1)
        self.assertFalse(gate["complete_paired_labels"])
        self.assertFalse(gate["adequacy_supported"])

    def test_tag_adequacy_requires_adjudication_for_disagreement(self) -> None:
        rows = [
            {
                "fragment_index": "0",
                "fragment_hash": "abc",
                "kind": "prompt",
                "source": "codex",
                "candidate_tag": "review",
                "labeler_1": "adequate",
                "labeler_2": "misleading",
                "adjudicated_label": "",
            }
        ]

        scored, summary = score_tag_adequacy_rows(rows)

        self.assertEqual(scored[0]["label_state"], "needs_adjudication")
        self.assertEqual(summary["unadjudicated_disagreement_count"], 1)
        self.assertEqual(tag_adequacy_status(summary), "human_labels_partial")

    def test_r124_blinded_sheet_hides_model_and_stability_columns(self) -> None:
        source = {
            "fragment_index": "7",
            "fragment_hash": "abc123",
            "kind": "prompt",
            "source": "codex",
            "model": "gpt-5",
            "candidate_tag": "review",
            "candidate_model": "3b",
            "candidate_exact_stable": "true",
            "candidate_distinct_tags": "1",
            "text_chars": "42",
            "preview": "Review the patch.",
            "labeler_1": "",
            "labeler_2": "",
            "adjudicated_label": "",
        }

        row = r124_blinded_row(source)

        self.assertEqual(list(row), R124_BLINDED_FIELDS)
        self.assertEqual(row["row_id"], "R124-007")
        self.assertEqual(row["fragment_level"], "prompt")
        self.assertEqual(row["candidate_tag"], "review")
        self.assertNotIn("model", row)
        self.assertNotIn("candidate_model", row)
        self.assertNotIn("candidate_exact_stable", row)
        self.assertNotIn("source", row)

    def test_r124_label_join_reaches_ready_for_scoring_when_complete(self) -> None:
        source_rows = [
            {
                "fragment_index": "0",
                "fragment_hash": "h0",
                "kind": "prompt",
                "source": "codex",
                "model": "gpt-5",
                "candidate_tag": "review",
                "labeler_1": "",
                "labeler_2": "",
                "adjudicated_label": "",
                "notes": "",
            },
            {
                "fragment_index": "1",
                "fragment_hash": "h1",
                "kind": "session",
                "source": "claude",
                "model": "opus",
                "candidate_tag": "debug",
                "labeler_1": "",
                "labeler_2": "",
                "adjudicated_label": "",
                "notes": "",
            },
        ]
        labeler_1 = {
            "R124-000": {"label": "adequate", "notes": "clear"},
            "R124-001": {"label": "generic_noisy", "notes": ""},
        }
        labeler_2 = {
            "R124-000": {"label": "adequate", "notes": ""},
            "R124-001": {"label": "generic_noisy", "notes": "broad"},
        }

        joined, disagreements, summary = join_r124_label_rows(source_rows, labeler_1, labeler_2, {})

        self.assertEqual(disagreements, [])
        self.assertEqual(r124_join_status(True, summary), "ready_for_scoring")
        self.assertEqual(joined[0]["labeler_1"], "adequate")
        self.assertEqual(joined[1]["labeler_2"], "generic_noisy")
        self.assertIn("labeler_1: clear", joined[0]["notes"])
        self.assertIn("labeler_2: broad", joined[1]["notes"])

    def test_r124_label_join_requires_adjudication_for_disagreements(self) -> None:
        source_rows = [
            {
                "fragment_index": "0",
                "fragment_hash": "h0",
                "kind": "prompt",
                "source": "codex",
                "model": "gpt-5",
                "candidate_tag": "review",
                "labeler_1": "",
                "labeler_2": "",
                "adjudicated_label": "",
                "notes": "",
            }
        ]
        labeler_1 = {"R124-000": {"label": "adequate", "notes": ""}}
        labeler_2 = {"R124-000": {"label": "misleading", "notes": ""}}

        joined, disagreements, summary = join_r124_label_rows(source_rows, labeler_1, labeler_2, {})

        self.assertEqual(r124_join_status(True, summary), "needs_adjudication")
        self.assertEqual(summary["missing_adjudication_count"], 1)
        self.assertEqual(disagreements[0]["row_id"], "R124-000")
        self.assertEqual(joined[0]["adjudicated_label"], "")

        joined, disagreements, summary = join_r124_label_rows(
            source_rows,
            labeler_1,
            labeler_2,
            {"R124-000": {"label": "adequate", "notes": "keeps intent"}},
        )

        self.assertEqual(r124_join_status(True, summary), "ready_for_scoring")
        self.assertEqual(summary["adjudicated_disagreement_count"], 1)
        self.assertEqual(joined[0]["adjudicated_label"], "adequate")
        self.assertIn("adjudication: keeps intent", joined[0]["notes"])

    def test_r124_label_join_rejects_unblinded_labeler_sheet(self) -> None:
        source_rows = [
            {
                "fragment_index": "0",
                "kind": "prompt",
                "candidate_tag": "review",
            }
        ]
        with tempfile.TemporaryDirectory() as tmp:
            sheet = Path(tmp) / "labeler.csv"
            sheet.write_text(
                "\n".join(
                    [
                        "row_id,fragment_index,fragment_level,redacted_preview,candidate_tag,rubric,label,notes,source",
                        "R124-000,0,prompt,redacted,review,rubric,adequate,,codex",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            with self.assertRaisesRegex(AssertionError, "hidden fields"):
                read_r124_labeler_sheet(sheet, source_rows)

    def test_r170_folded_integrity_summary_detects_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            folded = Path(tmp) / "semantic-system.folded.txt"
            folded.write_text("project:x;session:a 2\nproject:x;session:b 3\n", encoding="utf-8")

            totals = r170_read_folded_total(folded)
            matching = r170_counter_summary(
                {"summary": {"system": {"unique_stacks": 2, "total_weight": 5}}},
                "system",
                totals,
            )
            mismatching = r170_counter_summary(
                {"summary": {"system": {"unique_stacks": 2, "total_weight": 6}}},
                "system",
                totals,
            )

            self.assertEqual(totals, {"unique_stacks": 2, "total_weight": 5})
            self.assertTrue(matching["matches_folded"])
            self.assertFalse(mismatching["matches_folded"])

    def test_visual_summary_helpers_keep_svg_values_bounded(self) -> None:
        self.assertEqual(verdict_color("supported"), "#2f855a")
        self.assertEqual(verdict_color("unknown"), "#5f6b76")
        self.assertEqual(verdict_score("unsupported"), 0.18)
        self.assertEqual(bar_width(150, 100, 200), 200)
        self.assertEqual(bar_width(-1, 100, 200), 0)
        self.assertLessEqual(max(len(line) for line in label_lines("one two three four", 8)), 8)

    def test_r184_gate_rejects_empty_human_evidence(self) -> None:
        c5 = r184_c5_gate(
            {"status": "frozen_before_collection", "validation": {"status": "ok"}},
            {
                "status": "participant_results_empty",
                "participant_count": 0,
                "response_count": 0,
                "claim_analysis": {"claim_gate": {"c5_supported": False, "pilot_ready": False}},
            },
        )
        c6 = r184_c6_gate(
            {
                "summary": {
                    "row_count": 300,
                    "labeler_1_count": 0,
                    "labeler_2_count": 0,
                    "paired_label_count": 0,
                    "complete_two_labeler_sheets": False,
                    "complete_adjudication": True,
                }
            },
            {
                "summary": {"packet_row_count": 300, "final_label_count": 0, "both_labeler_count": 0},
                "claim_gate": {"adequacy_supported": False},
            },
        )
        overall = r184_overall_gate(c5, c6)

        self.assertEqual(c5["status"], "ready_for_participant_collection")
        self.assertEqual(c6["status"], "ready_for_independent_label_collection")
        self.assertFalse(overall["human_evidence_supported"])
        self.assertEqual(overall["status"], "not_weak_accept")
        self.assertIn("subagent review", overall["disallowed_evidence"])

    def test_r184_gate_can_only_clear_human_evidence_after_both_claims_pass(self) -> None:
        c5 = r184_c5_gate(
            {"status": "frozen_before_collection", "validation": {"status": "ok"}},
            {
                "participant_count": 12,
                "response_count": 840,
                "claim_analysis": {
                    "claim_gate": {
                        "c5_supported": True,
                        "pilot_ready": True,
                        "paper_model_ready": True,
                    }
                },
            },
        )
        c6 = r184_c6_gate(
            {
                "summary": {
                    "row_count": 300,
                    "labeler_1_count": 300,
                    "labeler_2_count": 300,
                    "paired_label_count": 300,
                    "complete_two_labeler_sheets": True,
                    "complete_adjudication": True,
                }
            },
            {
                "summary": {"packet_row_count": 300, "final_label_count": 300, "both_labeler_count": 300},
                "claim_gate": {"adequacy_supported": True},
            },
        )
        overall = r184_overall_gate(c5, c6)

        self.assertTrue(c5["supported"])
        self.assertTrue(c6["supported"])
        self.assertEqual(overall["status"], "human_evidence_ready_for_osdi_claim_audit")
        self.assertTrue(overall["human_evidence_supported"])

    def test_r219_claim_readiness_gate_keeps_osdi_blockers_explicit(self) -> None:
        artifacts = {
            "r170_full_history": {
                "summary": {
                    "session_count": 325,
                    "system_observations": 183714,
                    "semantic_system_stacks": 26829,
                }
            },
            "r180_model_benchmarks": {
                "aggregate": {
                    "total_runs": 2700,
                    "ok_runs": 2700,
                    "exact_stable_fragments": 863,
                    "fragment_count": 900,
                }
            },
            "r114_live_record": {
                "status": "ok",
                "aggregate": {
                    "true_positives": 1273,
                    "false_positives": 0,
                    "false_negatives": 0,
                    "negative_joined_effect_events": 0,
                    "negative_effect_events_observed": 3170,
                },
            },
            "r182_live_network": {"status": "partial"},
            "r184_weak_accept": {
                "status": "not_weak_accept",
                "c5_user_utility": {"supported": False, "participant_count": 0, "response_count": 0},
                "c6_tag_adequacy": {"supported": False, "final_label_count": 0},
            },
            "r195_human_pipeline": {"status": "awaiting_human_inputs"},
            "r160_artifact_usability": {"status": "artifact_usability_smoke_passed"},
            "r213_display_mode": {"status": "display_mode_drilldown_smoke_ready_no_quality_claims"},
            "r214_long_tail_control": {"status": "long_tail_control_loop_ready_no_quality_claims"},
            "r215_frontend_renderer": {"status": "frontend_renderer_mode_smoke_ready_no_quality_claims"},
            "r216_browser_dom": {"status": "browser_dom_mode_smoke_ready_no_quality_claims"},
            "r217_production_react": {
                "summary": {"visible_bucket_count": 1748, "visible_total_support": 482398}
            },
            "r218_update_gate": {
                "summary": {
                    "accepted_diff_rows": 2,
                    "rejected_rows": 4,
                    "canonical_map_updated": False,
                }
            },
            "r124_tag_adequacy": {"status": "human_labels_empty"},
            "r190_merge_quality": {"status": "human_labels_empty"},
            "r203_promotion_quality": {"status": "human_labels_empty"},
            "r142_user_task_results": {"status": "participant_results_empty"},
        }

        status = r219_artifact_statuses(artifacts)
        claims = r219_claim_rows(status)
        rqs = r219_rq_rows(status)
        overall = r219_overall_status(claims)
        gate = r219_claim_gate(overall)
        next_rows = r219_next_experiment_rows()

        self.assertEqual(status["r170_sessions"], 325)
        self.assertEqual(status["r114_precision_pct"], 100.0)
        self.assertEqual(status["r114_recall_pct"], 100.0)
        self.assertEqual(status["r160_status"], "artifact_usability_smoke_passed")
        self.assertEqual(status["r216_status"], "browser_dom_mode_smoke_ready_no_quality_claims")
        self.assertFalse(status["r218_canonical_map_updated"])
        self.assertEqual(overall["status"], "osdi_weak_accept_not_supported")
        self.assertFalse(overall["weak_accept_supported"])
        self.assertIn("C5/RQ4 has no supported real participant outcome", overall["blockers"])
        self.assertIn("C6/RQ5 has no supported independent human adequacy labels", overall["blockers"])
        self.assertTrue(gate["requires_c5_human_participants"])
        self.assertTrue(gate["requires_c6_human_labels"])
        self.assertTrue(gate["synthetic_or_subagent_evidence_disallowed"])
        self.assertEqual(len(claims), 7)
        self.assertEqual(len(rqs), 6)
        self.assertEqual(next_rows[0]["run_id"], "R142-pilot-return")
        self.assertEqual(next_rows[1]["run_id"], "R124-labels-return")


if __name__ == "__main__":
    unittest.main()
