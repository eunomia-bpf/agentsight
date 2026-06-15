#!/usr/bin/env python3
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
    compression_summary,
    mixing_summary,
    tag_quality,
)
from tag_stability_smoke import (
    annotator_metrics,
    cross_annotator_metrics,
    smoke_verdict,
)
from user_task_benchmark import parse_variants, participant_packets, stack_frame
from effect_lineage_smoke import lineage_rows
from live_lineage_harness import synthesize
from r114_live_record_suite import Task, precision_recall_summary, task_command
from score_user_task_results import is_placeholder_response, score_response, summarize
from visual_summary import bar_width, label_lines, verdict_color, verdict_score


class AggregationTests(unittest.TestCase):
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

    def test_participant_packets_exclude_oracles(self) -> None:
        tasks = [
            {
                "task_id": "UTX",
                "claim": "C5",
                "skill": "demo",
                "title": "Demo",
                "question": "Find the answer.",
                "participant_view_conditions": [
                    {"condition": "semantic", "views": ["system-flamegraph.svg"]},
                ],
                "answer_format": {"weight": "int"},
            }
        ]

        packets = participant_packets(tasks)

        self.assertEqual(packets[0]["contains_oracle"], False)
        self.assertNotIn("oracle", packets[0])

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

    def test_user_task_scoring_ignores_empty_template_rows(self) -> None:
        self.assertTrue(
            is_placeholder_response(
                {
                    "participant_id": "",
                    "task_id": "UT1",
                    "condition": "semantic",
                    "response_json": "{}",
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
                }
            )
        )

    def test_visual_summary_helpers_keep_svg_values_bounded(self) -> None:
        self.assertEqual(verdict_color("supported"), "#2f855a")
        self.assertEqual(verdict_color("unknown"), "#5f6b76")
        self.assertEqual(verdict_score("unsupported"), 0.18)
        self.assertEqual(bar_width(150, 100, 200), 200)
        self.assertEqual(bar_width(-1, 100, 200), 0)
        self.assertLessEqual(max(len(line) for line in label_lines("one two three four", 8)), 8)


if __name__ == "__main__":
    unittest.main()
