#!/usr/bin/env python3
import tempfile
import unittest
from collections import Counter
from pathlib import Path
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
from visual_summary import bar_width, label_lines, verdict_color, verdict_score


class AggregationTests(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
