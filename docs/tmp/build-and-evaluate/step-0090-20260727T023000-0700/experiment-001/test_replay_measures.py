#!/usr/bin/env python3

from pathlib import Path
import unittest

import replay_measures as replay


class ReplayMeasureTests(unittest.TestCase):
    REPO = Path(__file__).resolve().parents[5]

    def test_elapsed_values_use_floor_minimum_and_terminal_one(self) -> None:
        self.assertEqual(replay.elapsed_values([10.0, 10.9, 13.2]), [1, 2, 1])
        self.assertEqual(replay.elapsed_values([10.0]), [1])
        self.assertEqual(replay.elapsed_values([]), [])

    def test_terminal_control_key_normalization(self) -> None:
        self.assertEqual(replay.normalize_terminal_input("C-c"), "\x03")
        self.assertEqual(replay.normalize_terminal_input("ls\r"), "ls")
        self.assertEqual(replay.normalize_terminal_input("ls\n"), "ls")

    def test_patch_targets_preserve_exact_created_and_updated_files(self) -> None:
        repo = Path("/workspace/repo")
        preview = (
            "*** Begin Patch *** Add File: docs/new.md +hello "
            "*** Update File: /workspace/repo/src/lib.rs @@ old new "
            "*** Move to: docs/moved.md"
        )
        self.assertEqual(
            replay.patch_targets(preview, repo),
            [
                ("docs/new.md", "created"),
                ("src/lib.rs", "updated"),
                ("docs/moved.md", "moved"),
            ],
        )

    def test_patch_targets_deduplicate_same_header(self) -> None:
        preview = "*** Add File: a.txt *** Add File: a.txt"
        self.assertEqual(
            replay.patch_targets(preview, Path("/repo")),
            [("a.txt", "created")],
        )

    def test_target_evidence_id_is_stable_and_target_specific(self) -> None:
        first = replay.target_evidence_id("node", "created", "a.txt")
        self.assertEqual(first, replay.target_evidence_id("node", "created", "a.txt"))
        self.assertNotEqual(first, replay.target_evidence_id("node", "created", "b.txt"))

    def test_ancestry_is_root_to_leaf(self) -> None:
        nodes = {
            "session": {"id": "session", "parent": None},
            "llm": {"id": "llm", "parent": "session"},
            "tool": {"id": "tool", "parent": "llm"},
        }
        self.assertEqual(
            [node["id"] for node in replay.ancestry(nodes["tool"], nodes)],
            ["session", "llm", "tool"],
        )

    def test_frozen_git_hierarchy_oracle_matches_all_489_paths(self) -> None:
        source = (
            self.REPO
            / ".agentsight/experiments/rq1-matched-organization-v1/full/"
            "operations-count.jsonl"
        )
        check = replay.accepted_git_paths(self.REPO, replay.read_jsonl(source))
        self.assertEqual(check["rows"], 489)
        self.assertEqual(check["expanded_paths"], 489)
        self.assertEqual(check["workspace_paths"], 489)
        self.assertTrue(check["exact_match"])
        self.assertEqual(check["mismatches"], [])


if __name__ == "__main__":
    unittest.main()
