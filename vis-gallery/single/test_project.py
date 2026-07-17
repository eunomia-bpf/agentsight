import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from project import build, build_tree, new_file_stats


class GalleryProjectionTests(unittest.TestCase):
    def test_lean_nebula_preserves_every_agent_event_not_only_path_rows(self):
        artifact = {
            "repository": {"name": "repo", "head": "deadbeef", "root_id": "root"},
            "window": {
                "since_ms": 1, "until_ms": 100, "retrieval_after_ms": 0,
                "global": True,
            },
            "sessions": [{
                "id": "session", "conversation_id": None, "vendor": "codex", "model": "gpt",
                "started_at_ms": 1, "ended_at_ms": 99, "tool_events": 2, "total_tokens": 3,
            }],
            "events": [
                {
                    "id": "pathless", "session_id": "session", "vendor": "codex", "model": "gpt",
                    "ts_ms": 10, "kind": "tool", "action": "exec_command", "category": "shell",
                    "effect": "process", "status": "success", "prompt_index": 0, "paths": [],
                    "write_paths": [], "path_groups": [], "process_chain": ["cargo"], "domains": [],
                    "input_tokens": 0, "output_tokens": 0, "cache_tokens": 0,
                },
                {
                    "id": "network", "session_id": "session", "vendor": "codex", "model": "gpt",
                    "ts_ms": 20, "kind": "tool", "action": "web_fetch", "category": "network",
                    "effect": "network", "status": "success", "prompt_index": 0, "paths": [],
                    "write_paths": [], "path_groups": [], "process_chain": [], "domains": ["example.test"],
                    "input_tokens": 0, "output_tokens": 0, "cache_tokens": 0,
                },
                {
                    "id": "model", "session_id": "session", "vendor": "codex", "model": "gpt",
                    "ts_ms": 30, "kind": "llm_response", "action": "model_response", "category": "model",
                    "effect": "compute", "status": "observed", "prompt_index": 0, "paths": [],
                    "write_paths": [], "path_groups": [], "process_chain": [], "domains": [],
                    "input_tokens": 1, "output_tokens": 2, "cache_tokens": 0,
                },
            ],
            "file_lifetimes": [{
                "id": "dead", "paths": ["old.txt"], "birth_ms": 0, "death_ms": 1,
                "current_path": None, "survives_to_head": False,
            }],
            "changes": [], "associations": [], "commits": [],
        }
        output = build([artifact], Path("/does/not/exist"), lean_nebula=True)
        self.assertEqual(output["meta"]["session_scope"], "global_tool_operations")
        self.assertEqual(len(output["agent_events"]), 3)
        self.assertEqual(
            set(output), {"meta", "agent_events", "files", "commits", "file_lifetimes"}
        )
        self.assertEqual(output["agent_events"][0]["process_chain"], ["cargo"])
        self.assertEqual(output["agent_events"][1]["domains"], ["example.test"])

    def test_endpoint_lifetime_wins_when_literal_path_is_reused(self):
        old = {
            "id": "old",
            "birth_ms": 10,
            "death_ms": 20,
            "survives_to_head": False,
            "current_path": None,
            "current_bytes": None,
        }
        endpoint = {
            "id": "endpoint",
            "birth_ms": 30,
            "death_ms": None,
            "survives_to_head": True,
            "current_path": "src/reused.rs",
            "current_bytes": 12,
        }
        record = new_file_stats("src/reused.rs", endpoint, [old, endpoint])
        self.assertEqual(record["lifetime_id"], "endpoint")
        self.assertEqual(record["lifetime_ids"], ["endpoint", "old"])
        self.assertTrue(record["survives_to_head"])

    def test_endpoint_tree_ignores_surviving_lifetime_aliases(self):
        endpoint = new_file_stats(
            "src/new.rs",
            {
                "id": "life",
                "birth_ms": 10,
                "death_ms": None,
                "survives_to_head": True,
                "current_path": "src/new.rs",
                "current_bytes": 12,
            },
        )
        endpoint["risk_score"] = 0
        endpoint["pattern"] = "Steady"
        alias = {**endpoint, "path": "src/old.rs"}
        tree = build_tree([alias, endpoint])
        src = tree["children"][0]
        self.assertEqual(
            [child["path"] for child in src["children"]], ["src/new.rs"]
        )


if __name__ == "__main__":
    unittest.main()
