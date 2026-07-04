#!/usr/bin/env python3
"""Unit tests for agent_trace_to_operations.py."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import unittest


SCRIPT_PATH = Path(__file__).with_name("agent_trace_to_operations.py")
SPEC = importlib.util.spec_from_file_location("agent_trace_to_operations", SCRIPT_PATH)
assert SPEC is not None
agent_trace_to_operations = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(agent_trace_to_operations)


class AgentTraceToOperationsTests(unittest.TestCase):
    def test_session_fallback_groups_private_paths(self) -> None:
        session = {
            "agent_type": "codex",
            "session_id": "s1",
            "cwd": "/repo",
            "events": {},
            "tools": {"Bash": 1},
            "files": {"/home/alice/private/secret.txt": 1},
        }

        operations = list(
            agent_trace_to_operations.operations_for_session(session, "agentsight", False)
        )
        payload = "\n".join(json.dumps(operation, sort_keys=True) for operation in operations)

        self.assertIn("external/home", payload)
        self.assertNotIn("/home/alice", payload)
        self.assertNotIn("secret.txt", payload)

    def test_tool_operation_uses_command_name_not_raw_command(self) -> None:
        session = {
            "agent_type": "codex",
            "session_id": "s1",
            "cwd": "/repo",
            "events": {
                "prompts": [{"index": 0, "text_hash": "h1", "tag": "review"}],
                "tools": [
                    {
                        "prompt_index": 0,
                        "tool_name": "bash",
                        "category": "shell",
                        "command": "cat /home/alice/private/secret.txt",
                        "command_name": "cat",
                        "effect": "read",
                        "status": "ok",
                        "path_groups": ["external/home"],
                        "domains": [],
                        "process_chain": ["cat"],
                    }
                ],
                "llm_responses": [],
            },
        }

        operations = list(
            agent_trace_to_operations.operations_for_session(session, "agentsight", False)
        )
        payload = "\n".join(json.dumps(operation, sort_keys=True) for operation in operations)

        self.assertIn('"command": "cat"', payload)
        self.assertNotIn("/home/alice", payload)
        self.assertNotIn("secret.txt", payload)


if __name__ == "__main__":
    unittest.main()
