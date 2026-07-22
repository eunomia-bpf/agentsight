from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import source_native_task_stack_eval as taskstack


def row(timestamp: str, kind: str, payload: dict) -> str:
    return json.dumps({"timestamp": timestamp, "type": kind, "payload": payload})


class SourceNativeTaskStackTest(unittest.TestCase):
    def write_fixture(self, root: Path) -> tuple[Path, Path]:
        parent = root / "parent.jsonl"
        child = root / "child.jsonl"
        parent.write_text(
            "\n".join(
                [
                    row("1", "session_meta", {"id": "parent", "cwd": "/repo"}),
                    row("2", "event_msg", {"type": "user_message", "message": "Audit the paper evidence"}),
                    row(
                        "3",
                        "response_item",
                        {
                            "type": "function_call",
                            "name": "update_plan",
                            "call_id": "plan-1",
                            "arguments": json.dumps(
                                {"plan": [{"step": "Check experimental results", "status": "in_progress"}]}
                            ),
                        },
                    ),
                    row(
                        "4",
                        "response_item",
                        {
                            "type": "function_call",
                            "name": "spawn_agent",
                            "call_id": "spawn-1",
                            "arguments": json.dumps({"message": "Check implementation against the paper"}),
                        },
                    ),
                    row(
                        "5",
                        "response_item",
                        {
                            "type": "function_call_output",
                            "call_id": "spawn-1",
                            "output": json.dumps({"task_name": "/root/child"}),
                        },
                    ),
                    row(
                        "5.1",
                        "event_msg",
                        {
                            "type": "sub_agent_activity",
                            "event_id": "spawn-1",
                            "agent_thread_id": "child",
                            "kind": "started",
                        },
                    ),
                    row(
                        "6",
                        "response_item",
                        {
                            "type": "function_call",
                            "name": "exec_command",
                            "call_id": "parent-tool",
                            "arguments": json.dumps({"cmd": "rg result docs/results.md"}),
                        },
                    ),
                    row("7", "event_msg", {"type": "token_count", "info": {"last_token_usage": {"input_tokens": 10, "output_tokens": 2}}}),
                    row(
                        "7.1",
                        "response_item",
                        {
                            "type": "function_call",
                            "name": "update_plan",
                            "call_id": "plan-2",
                            "arguments": json.dumps(
                                {"plan": [{"step": "Check experimental results", "status": "completed"}]}
                            ),
                        },
                    ),
                    row(
                        "7.2",
                        "response_item",
                        {
                            "type": "function_call",
                            "name": "update_plan",
                            "call_id": "plan-3",
                            "arguments": json.dumps(
                                {"plan": [{"step": "Check experimental results", "status": "completed"}]}
                            ),
                        },
                    ),
                ]
            )
            + "\n",
            encoding="utf-8",
        )
        child.write_text(
            "\n".join(
                [
                    row(
                        "4.5",
                        "session_meta",
                        {
                            "id": "child",
                            "parent_thread_id": "parent",
                            "timestamp": "2026-03-07T03:31:58.279Z",
                            "thread_source": "subagent",
                            "cwd": "/repo",
                            "source": {"subagent": {"thread_spawn": {"depth": 1}}},
                        },
                    ),
                    row("4.6", "session_meta", {"id": "parent", "cwd": "/repo"}),
                    row(
                        "4.65",
                        "event_msg",
                        {
                            "type": "task_started",
                            "turn_id": "019cc649-4ce9-73a1-b5a2-e3941b2ab717",
                        },
                    ),
                    row(
                        "4.7",
                        "response_item",
                        {
                            "type": "function_call",
                            "name": "exec_command",
                            "call_id": "copied-parent-tool",
                            "arguments": json.dumps({"cmd": "echo copied"}),
                        },
                    ),
                    row(
                        "5.0",
                        "event_msg",
                        {
                            "type": "task_started",
                            "turn_id": "019cc65a-14f5-7e13-a77e-49809a09618b",
                        },
                    ),
                    row(
                        "5.5",
                        "response_item",
                        {
                            "type": "function_call",
                            "name": "update_plan",
                            "call_id": "child-plan",
                            "arguments": json.dumps(
                                {"plan": [{"step": "Locate stack construction", "status": "in_progress"}]}
                            ),
                        },
                    ),
                    row(
                        "6.5",
                        "response_item",
                        {
                            "type": "function_call",
                            "name": "exec_command",
                            "call_id": "child-tool",
                            "arguments": json.dumps({"cmd": "rg stack script/profile.py"}),
                        },
                    ),
                    row("7.5", "event_msg", {"type": "agent_message", "phase": "final_answer", "message": "Found it"}),
                ]
            )
            + "\n",
            encoding="utf-8",
        )
        return parent, child

    def test_concurrent_parent_and_child_paths(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            parent, child = self.write_fixture(Path(tmp))
            candidate_sessions = {
                session.session_id: session
                for session in (taskstack.candidate_parse_session(parent), taskstack.candidate_parse_session(child))
                if session
            }
            reference_sessions = {
                session.session_id: session
                for session in (taskstack.reference_parse_session(parent), taskstack.reference_parse_session(child))
                if session
            }
            candidate = taskstack.candidate_replay(candidate_sessions)
            reference = taskstack.reference_replay(reference_sessions)
            metrics = taskstack.score(candidate, reference)
            self.assertEqual(metrics["primary"]["accuracy"], 1.0)
            self.assertEqual(metrics["operation_alignment"]["path_mismatch"], 0)
            parent_op = next(op for op in candidate.operations if op.operation_id.endswith("parent-tool"))
            child_op = next(op for op in candidate.operations if op.operation_id.endswith("child-tool"))
            self.assertEqual(len(parent_op.task_ids), 2)
            self.assertEqual(len(child_op.task_ids), 4)
            self.assertNotIn("delegate:spawn-1:child:child", parent_op.task_ids)
            self.assertIn("delegate:spawn-1:child:child", child_op.task_ids)
            self.assertFalse(any(op.operation_id.endswith("copied-parent-tool") for op in candidate.operations))
            self.assertTrue(candidate_sessions["child"].ownership_boundary_required)
            self.assertTrue(candidate_sessions["child"].ownership_boundary_found)
            self.assertGreater(candidate_sessions["child"].copied_records_skipped, 0)
            self.assertEqual(candidate.task_outcomes["source_declared_completion"], 2)
            self.assertEqual(reference.task_outcomes["source_declared_completion"], 2)

    def test_pprof_record_keeps_variable_task_path_without_system_metadata(self) -> None:
        op = taskstack.OperationPath(
            "op",
            "session-secret",
            1,
            "",
            ("root",),
            ("Review evidence",),
            "tool",
            "Inspect evidence",
            "Read or search",
            "results.md",
            "Observed",
            1,
            0,
        )
        record = taskstack.pprof_operation_record(op)
        self.assertEqual(record["value"], 1)
        self.assertEqual(record["fields"]["task"], ["Review evidence"])
        self.assertEqual(record["fields"]["phase"], "Inspect evidence")
        self.assertNotIn("session", record["fields"])
        self.assertNotIn("tool", record["fields"])

    def test_candidate_and_reference_read_the_same_complete_prefix(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            parent, _ = self.write_fixture(Path(tmp))
            byte_limit = parent.stat().st_size
            with parent.open("a", encoding="utf-8") as handle:
                handle.write(
                    row(
                        "8",
                        "response_item",
                        {
                            "type": "function_call",
                            "name": "exec_command",
                            "call_id": "late-tool",
                            "arguments": json.dumps({"cmd": "echo late"}),
                        },
                    )
                    + "\n"
                )
            candidate = taskstack.candidate_parse_session(parent, byte_limit)
            reference = taskstack.reference_parse_session(parent, byte_limit)
            self.assertIsNotNone(candidate)
            self.assertIsNotNone(reference)
            self.assertFalse(any(event.call_id == "late-tool" for event in candidate.events))
            self.assertFalse(any(event.call_id == "late-tool" for event in reference.events))

    def test_response_item_user_message_is_a_concrete_root(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "response-root.jsonl"
            path.write_text(
                "\n".join(
                    [
                        row("1", "session_meta", {"id": "response-root"}),
                        row(
                            "2",
                            "response_item",
                            {
                                "type": "message",
                                "role": "user",
                                "content": [
                                    {"type": "input_text", "text": "Write the paper abstract"}
                                ],
                            },
                        ),
                        row(
                            "3",
                            "response_item",
                            {
                                "type": "function_call",
                                "name": "update_plan",
                                "call_id": "plan-response-root",
                                "arguments": json.dumps(
                                    {
                                        "plan": [
                                            {
                                                "step": "Draft the opening paragraph",
                                                "status": "in_progress",
                                            }
                                        ]
                                    }
                                ),
                            },
                        ),
                        row(
                            "4",
                            "response_item",
                            {
                                "type": "function_call",
                                "name": "exec_command",
                                "call_id": "rooted-tool",
                                "arguments": json.dumps({"cmd": "sed -n '1,80p' main.tex"}),
                            },
                        ),
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            candidate_session = taskstack.candidate_parse_session(path)
            reference_session = taskstack.reference_parse_session(path)
            self.assertIsNotNone(candidate_session)
            self.assertIsNotNone(reference_session)
            candidate = taskstack.candidate_replay({"response-root": candidate_session})
            reference = taskstack.reference_replay({"response-root": reference_session})
            self.assertEqual(taskstack.score(candidate, reference)["primary"]["accuracy"], 1.0)
            self.assertTrue(candidate.operations)
            self.assertTrue(all(op.task_ids[0].startswith("root:") for op in candidate.operations))
            self.assertEqual(candidate.operations[-1].task_labels[:2], ("Write the paper abstract", "Draft the opening paragraph"))

    def test_status_parser_uses_explicit_machine_outcomes(self) -> None:
        self.assertEqual(taskstack.tool_output_status("Process exited with code 0"), "success")
        self.assertEqual(taskstack.tool_output_status("Process exited with code 2"), "error")
        self.assertEqual(taskstack.tool_output_status("review error handling documentation"), "observed")
        self.assertEqual(taskstack.tool_output_status("0 tests failed"), "observed")

    def test_zoom_prefers_the_largest_nested_task_path(self) -> None:
        def operation(name: str, path: tuple[str, ...]) -> taskstack.OperationPath:
            return taskstack.OperationPath(
                name,
                "session",
                1,
                "",
                path,
                tuple(path),
                "tool",
                "Inspect evidence",
                "Read or search",
                "artifact",
                "No source-visible semantic result",
                1,
                0,
            )

        operations = [
            operation("root-only", ("root",)),
            operation("a-1", ("root", "subtask-a")),
            operation("a-2", ("root", "subtask-a")),
            operation("b-1", ("root", "subtask-b")),
            operation("delegated", ("root", "delegate:call:child")),
        ]
        selected, zoom = taskstack.largest_nested_task_path(operations)
        self.assertEqual(selected, ("root", "delegate:call:child"))
        self.assertEqual([op.operation_id for op in zoom], ["delegated"])


if __name__ == "__main__":
    unittest.main()
