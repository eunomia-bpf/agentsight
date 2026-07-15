import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from build_gallery_data import build_tree, new_file_stats, validate_public_output


def valid_output():
    return {
        "meta": {"right_censored_days": ["2026-07-14"]},
        "sessions": [{"id": "session-1", "days": ["2026-07-14"]}],
        "source_days": [
            {
                "day": "2026-07-14",
                "sessions": 1,
                "write_event_paths": 0,
                "verification_events": 0,
            }
        ],
        "verification_events": [],
        "events": [
            {
                "id": "event-1",
                "day": "2026-07-14",
                "path": "src/lib.rs",
                "effect": "read",
                "association_state": "not_eligible",
                "candidate_count": 0,
                "evidence_bin": None,
                "exact_hunk": False,
            }
        ],
    }


class PublicGalleryValidationTests(unittest.TestCase):
    def test_accepts_process_only_censored_event(self):
        validate_public_output(valid_output())

    def test_rejects_home_relative_native_path(self):
        output = valid_output()
        output["events"][0]["path"] = "~/.claude/projects/session.jsonl"
        with self.assertRaisesRegex(ValueError, "non-repository paths"):
            validate_public_output(output)

    def test_rejects_glob_and_command_fragments_as_paths(self):
        for path in [
            "src/*.rs",
            "cargo run --manifest-path Cargo.toml",
            "#!/bin/bash",
            "s#^frontend/##",
            "HEAD..origin/master",
            "origin/master:collector/Cargo.toml",
            "ghcr.io/eunomia-bpf/agentsight:latest",
            "repos/eunomia-bpf/agentsight/pulls/109/comments",
            "bpf/$f",
            "100644,$blob,collector/src/cmd_perf.rs",
            "CLI/TUI/Web",
            ".git/rebase-merge/msgnum",
        ]:
            output = valid_output()
            output["events"][0]["path"] = path
            with self.assertRaisesRegex(ValueError, "non-repository paths"):
                validate_public_output(output)

    def test_rejects_association_on_censored_day(self):
        output = valid_output()
        output["events"][0]["association_state"] = "unique_candidate"
        output["events"][0]["candidate_count"] = 1
        with self.assertRaisesRegex(ValueError, "association evidence"):
            validate_public_output(output)

    def test_rejects_mature_write_without_association(self):
        output = valid_output()
        output["meta"]["right_censored_days"] = []
        output["events"][0]["effect"] = "write"
        output["source_days"][0]["write_event_paths"] = 1
        with self.assertRaisesRegex(ValueError, "mature writes"):
            validate_public_output(output)

    def test_rejects_non_deduplicated_day_count(self):
        output = valid_output()
        output["source_days"][0]["sessions"] = 2
        with self.assertRaisesRegex(ValueError, "not deduplicated"):
            validate_public_output(output)

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
