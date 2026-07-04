#!/usr/bin/env python3
"""Integration tests for agent_trace_convert.py."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


SCRIPT_PATH = Path(__file__).with_name("agent_trace_convert.py")


def sample_agent_trace() -> dict:
    return {
        "schema": "agentsight.agent-session.trace.v1",
        "sessions": [
            {
                "agent_type": "codex",
                "session_id": "s1",
                "display_id": "s1",
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
                    "llm_responses": [
                        {
                            "ts_ms": 1020,
                            "prompt_index": 0,
                            "model": "gpt-test",
                            "text_hash": "h2",
                            "preview": "looks fine",
                            "input_tokens": 11,
                            "output_tokens": 7,
                            "cache_tokens": 0,
                            "total_tokens": 18,
                            "tag": "review",
                        }
                    ],
                },
            }
        ],
    }


def jsonl(path: Path) -> list[dict]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


class AgentTraceConvertTests(unittest.TestCase):
    def run_converter(self, *args: str) -> dict:
        result = subprocess.run(
            [sys.executable, str(SCRIPT_PATH), *args],
            check=True,
            text=True,
            capture_output=True,
        )
        return json.loads(result.stdout)

    def test_agent_session_exports_standard_trace_and_imports_to_operations(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            agent_trace = tmp / "agent-trace.json"
            chrome_trace = tmp / "standard-trace.json"
            direct_operations = tmp / "direct-operations.jsonl"
            imported_operations = tmp / "imported-operations.jsonl"
            agent_trace.write_text(json.dumps(sample_agent_trace()), encoding="utf-8")

            export_result = self.run_converter(
                "export-standard",
                "--format",
                "chrome",
                "--trace-file",
                str(agent_trace),
                "--project-name",
                "agentsight",
                "--out",
                str(chrome_trace),
            )
            direct_result = self.run_converter(
                "to-operations",
                "--trace-file",
                str(agent_trace),
                "--project-name",
                "agentsight",
                "--out",
                str(direct_operations),
            )
            import_result = self.run_converter(
                "import-standard",
                "--format",
                "chrome",
                "--trace-file",
                str(chrome_trace),
                "--project-name",
                "agentsight",
                "--out",
                str(imported_operations),
            )

            chrome_payload = json.loads(chrome_trace.read_text(encoding="utf-8"))
            direct_rows = jsonl(direct_operations)
            imported_rows = jsonl(imported_operations)

        self.assertEqual("ok", export_result["status"])
        self.assertEqual("chrome-trace-event-json", export_result["format"])
        self.assertEqual("chrome", export_result["format_alias"])
        self.assertEqual(3, export_result["events"])
        self.assertEqual(3, direct_result["operations"])
        self.assertEqual(3, import_result["operations"])
        self.assertEqual("chrome-trace-event-json", chrome_payload["metadata"]["format"])
        self.assertEqual(direct_rows, imported_rows)

    def test_import_standard_trace_keeps_common_generic_args(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            standard_trace = tmp / "generic-trace.json"
            operations = tmp / "operations.jsonl"
            standard_trace.write_text(
                json.dumps(
                    {
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
                ),
                encoding="utf-8",
            )

            result = self.run_converter(
                "import-standard",
                "--trace-file",
                str(standard_trace),
                "--project-name",
                "external-trace",
                "--out",
                str(operations),
            )
            rows = jsonl(operations)

        self.assertEqual("ok", result["status"])
        self.assertEqual(1, result["operations"])
        fields = rows[0]["fields"]
        self.assertEqual("external-trace", fields["project"])
        self.assertEqual("action", fields["op"])
        self.assertEqual("navigate", fields["phase"])
        self.assertEqual("weblinx", fields["dataset"])
        self.assertEqual("click", fields["action"])
        self.assertEqual("submit", fields["target"])


if __name__ == "__main__":
    unittest.main()
