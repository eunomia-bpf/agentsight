#!/usr/bin/env python3
"""Unit tests for agent_trace_chrome_trace.py."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


SCRIPT_PATH = Path(__file__).with_name("agent_trace_chrome_trace.py")
SPEC = importlib.util.spec_from_file_location("agent_trace_chrome_trace", SCRIPT_PATH)
assert SPEC is not None
agent_trace_chrome_trace = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(agent_trace_chrome_trace)


class AgentTraceChromeTraceTests(unittest.TestCase):
    def test_agent_trace_round_trips_operation_fields(self) -> None:
        trace = {
            "schema": "agentsight.agent-session.trace.v1",
            "sessions": [
                {
                    "agent_type": "codex",
                    "session_id": "s1",
                    "path": "trace/codex/s1.jsonl",
                    "cwd": "repo",
                    "start_timestamp_ms": 1000,
                    "events": {
                        "prompts": [
                            {
                                "index": 0,
                                "ts_ms": 1000,
                                "text_hash": "h1",
                                "tag": "review",
                                "preview": "review this change",
                            }
                        ],
                        "tools": [
                            {
                                "ts_ms": 1010,
                                "prompt_index": 0,
                                "tool_name": "bash",
                                "category": "shell",
                                "command": "rg",
                                "command_name": "rg",
                                "effect": "read",
                                "process_chain": ["rg"],
                                "status": "ok",
                                "path_groups": ["docs/design.md"],
                                "domains": [],
                            }
                        ],
                        "llm_responses": [],
                    },
                }
            ],
        }

        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            trace_path = tmp / "agent-trace.json"
            trace_path.write_text(json.dumps(trace), encoding="utf-8")
            chrome = agent_trace_chrome_trace.chrome_payload_from_agent_trace_files(
                [trace_path], "agentsight"
            )
            operations = agent_trace_chrome_trace.operations_from_chrome_trace_payload(
                chrome, "agentsight"
            )

        self.assertEqual(2, len(chrome["traceEvents"]))
        self.assertEqual(2, len(operations))
        fields = [operation["fields"] for operation in operations]
        self.assertEqual(["prompt", "tool"], [field["op"] for field in fields])
        self.assertEqual("review", fields[0]["prompt"])
        self.assertEqual("rg", fields[1]["command"])
        payload = json.dumps(chrome, sort_keys=True)
        self.assertNotIn("review this change", payload)

    def test_generic_complete_event_import_keeps_common_labels(self) -> None:
        payload = {
            "traceEvents": [
                {
                    "name": "browser.click",
                    "cat": "action;navigate",
                    "ph": "X",
                    "ts": 10,
                    "dur": 20,
                    "pid": 7,
                    "tid": 1,
                    "args": {
                        "dataset": "weblinx",
                        "task": "login",
                        "action": "click",
                        "target": "submit",
                        "status": "gold",
                    },
                }
            ]
        }

        operations = agent_trace_chrome_trace.operations_from_chrome_trace_payload(
            payload, "external-trace"
        )

        self.assertEqual(1, len(operations))
        fields = operations[0]["fields"]
        self.assertEqual("external-trace", fields["project"])
        self.assertEqual("action", fields["op"])
        self.assertEqual("navigate", fields["phase"])
        self.assertEqual("weblinx", fields["dataset"])
        self.assertEqual("click", fields["action"])
        self.assertEqual("submit", fields["target"])
        self.assertEqual(20, fields["trace_dur_us"])

    def test_begin_end_events_import_as_one_operation(self) -> None:
        payload = {
            "traceEvents": [
                {
                    "name": "tool.exec",
                    "cat": "tool;shell",
                    "ph": "B",
                    "ts": 100,
                    "pid": 3,
                    "tid": 0,
                    "args": {"tool": "bash"},
                },
                {
                    "name": "tool.exec",
                    "cat": "tool;shell",
                    "ph": "E",
                    "ts": 160,
                    "pid": 3,
                    "tid": 0,
                    "args": {"status": "ok"},
                },
            ]
        }

        operations = agent_trace_chrome_trace.operations_from_chrome_trace_payload(
            payload, "external-trace"
        )

        self.assertEqual(1, len(operations))
        fields = operations[0]["fields"]
        self.assertEqual("tool", fields["op"])
        self.assertEqual("shell", fields["phase"])
        self.assertEqual("bash", fields["tool"])
        self.assertEqual("ok", fields["status"])
        self.assertEqual(60, fields["trace_dur_us"])


if __name__ == "__main__":
    unittest.main()
