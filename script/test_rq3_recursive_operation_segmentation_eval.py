#!/usr/bin/env python3

from __future__ import annotations

import json
import sys
from pathlib import Path
import tempfile
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "script"))

import rq3_recursive_operation_segmentation_eval as recursive  # noqa: E402


class RecursiveOperationSegmentationTest(unittest.TestCase):
    def test_parse_decision_rejects_invalid_or_colliding_split(self) -> None:
        self.assertEqual(
            recursive.parse_decision('{"decision":"stop"}', ["2"]),
            {"decision": "stop"},
        )
        self.assertEqual(
            recursive.parse_decision(
                '{"decision":"split","split_before":"2","left":"inspect code","right":"test fix"}',
                ["2", "3"],
            ),
            {
                "decision": "split",
                "split_before": "2",
                "left": "inspect code",
                "right": "test fix",
            },
        )
        with self.assertRaisesRegex(RuntimeError, "outside interval"):
            recursive.parse_decision(
                '{"decision":"split","split_before":"9","left":"inspect code","right":"test fix"}',
                ["2"],
            )
        self.assertEqual(
            recursive.parse_decision(
                '{"decision":"split","split_before":"2","left":"inspect code","right":"Inspect   Code"}',
                ["2"],
            )["left"],
            "inspect code",
        )

    def test_resolve_child_implements_stay_pop_and_push(self) -> None:
        active = ["repair software", "inspect implementation", "trace state"]
        self.assertEqual(recursive.resolve_child(active, "trace state"), active)
        self.assertEqual(
            recursive.resolve_child(active, "inspect implementation"),
            ["repair software", "inspect implementation"],
        )
        self.assertEqual(recursive.resolve_child(active, "repair software"), ["repair software"])
        self.assertEqual(
            recursive.resolve_child(active, "validate fix"),
            [*active, "validate fix"],
        )
        with self.assertRaisesRegex(RuntimeError, "duplicate operation"):
            recursive.resolve_child(["repair software", "repair software"], "validate fix")

    def test_split_resolution_only_totalizes_both_current(self) -> None:
        active = ["repair software", "inspect implementation"]
        same_current = recursive.resolve_split(
            active,
            "inspect implementation",
            " Inspect   Implementation ",
        )
        self.assertEqual(
            same_current["controller_resolution"],
            "degenerate_current_split_stop",
        )
        with self.assertRaisesRegex(RuntimeError, "identical noncurrent"):
            recursive.resolve_split(active, "repair software", " Repair   Software ")
        with self.assertRaisesRegex(RuntimeError, "identical noncurrent"):
            recursive.resolve_split(active, "validate fix", " Validate   Fix ")

    def test_current_continuation_does_not_push_duplicate_frame(self) -> None:
        turns = [{"turn_id": str(index)} for index in range(1, 6)]

        def decide(start: int, end: int, ancestors: list[str], current: str) -> dict[str, str]:
            if (start, end) == (0, 5):
                return {
                    "decision": "split",
                    "split_before": "3",
                    "left": "inspect implementation",
                    "right": "repair software behavior",
                }
            if (start, end) == (2, 5):
                return {
                    "decision": "split",
                    "split_before": "4",
                    "left": "repair software behavior",
                    "right": "validate fix",
                }
            return {"decision": "stop"}

        leaves = recursive.decompose_turns(turns, "repair software behavior", decide)
        self.assertEqual([(row["start"], row["end"]) for row in leaves], [(0, 2), (2, 3), (3, 5)])
        self.assertEqual(
            [row["labels"] for row in leaves],
            [
                ["repair software behavior", "inspect implementation"],
                ["repair software behavior"],
                ["repair software behavior", "validate fix"],
            ],
        )
        self.assertTrue(all(left != right for row in leaves for left, right in zip(row["labels"], row["labels"][1:])))

    def test_recursive_pop_discards_the_deeper_suffix(self) -> None:
        turns = [{"turn_id": str(index)} for index in range(1, 7)]

        def decide(start: int, end: int, ancestors: list[str], current: str) -> dict[str, str]:
            if (start, end) == (0, 6):
                return {
                    "decision": "split",
                    "split_before": "4",
                    "left": "inspect implementation",
                    "right": "validate fix",
                }
            if (start, end) == (0, 3):
                return {
                    "decision": "split",
                    "split_before": "2",
                    "left": "inspect implementation",
                    "right": "repair software behavior",
                }
            return {"decision": "stop"}

        leaves = recursive.decompose_turns(turns, "repair software behavior", decide)
        self.assertEqual(
            [row["labels"] for row in leaves],
            [
                ["repair software behavior", "inspect implementation"],
                ["repair software behavior"],
                ["repair software behavior", "validate fix"],
            ],
        )

    def test_resolved_sibling_paths_must_differ(self) -> None:
        turns = [{"turn_id": "1"}, {"turn_id": "2"}]

        def decide(start: int, end: int, ancestors: list[str], current: str) -> dict[str, str]:
            return {
                "decision": "split",
                "split_before": "2",
                "left": "inspect implementation",
                "right": " Inspect   Implementation ",
            }

        with self.assertRaisesRegex(RuntimeError, "identical noncurrent resolved paths"):
            recursive.decompose_turns(turns, "repair software behavior", decide)

    def test_degenerate_current_split_is_audited_stop(self) -> None:
        turns = [{"turn_id": "1"}, {"turn_id": "2"}]
        decision = {
            "decision": "split",
            "split_before": "2",
            "left": "repair software behavior",
            "right": "repair software behavior",
        }

        def decide(start: int, end: int, ancestors: list[str], current: str) -> dict[str, str]:
            return decision

        leaves = recursive.decompose_turns(turns, "repair software behavior", decide)
        self.assertEqual(decision["controller_resolution"], "degenerate_current_split_stop")
        self.assertEqual(len(leaves), 1)
        self.assertEqual(leaves[0]["labels"], ["repair software behavior"])
        self.assertEqual(leaves[0]["terminal_reasons"], ["degenerate_current_split_stop"])

    def test_nested_pop_coalesces_adjacent_identical_paths_and_marks(self) -> None:
        turns = [{"turn_id": str(index)} for index in range(1, 7)]

        def decide(start: int, end: int, ancestors: list[str], current: str) -> dict[str, str]:
            if (start, end) == (0, 6):
                return {
                    "decision": "split",
                    "split_before": "4",
                    "left": "inspect implementation",
                    "right": "repair software behavior",
                }
            if (start, end) == (0, 3):
                return {
                    "decision": "split",
                    "split_before": "3",
                    "left": "inspect implementation",
                    "right": "repair software behavior",
                }
            return {"decision": "stop"}

        leaves = recursive.decompose_turns(turns, "repair software behavior", decide)
        self.assertEqual(
            [(row["start"], row["end"], row["labels"]) for row in leaves],
            [
                (0, 2, ["repair software behavior", "inspect implementation"]),
                (2, 6, ["repair software behavior"]),
            ],
        )
        operations = [
            {"step": index, "turn_id": f"turn-{index}", "source_ref": f"trace#{index}"}
            for index in range(1, 7)
        ]
        prepared = {
            "session": {
                "material": {"session": "session", "framework": "test", "operations": operations},
                "turns": [
                    {
                        "turn_index": index - 1,
                        "source_turn_id": f"turn-{index}",
                        "operations": [operation],
                    }
                    for index, operation in enumerate(operations, 1)
                ],
            }
        }
        predictions, marks = recursive.build_outputs(
            prepared,
            {"session": {"leaves": leaves}},
            ["session"],
        )
        self.assertEqual(len(predictions), 6)
        self.assertEqual([row["start_operation_id"] for row in marks["marks"]], ["1", "3"])
        self.assertEqual(predictions[2]["operation_ids"], predictions[-1]["operation_ids"])

    def test_recursive_split_has_variable_depth_and_complete_coverage(self) -> None:
        turns = [{"turn_id": str(index)} for index in range(1, 7)]

        def decide(start: int, end: int, ancestors: list[str], current: str) -> dict[str, str]:
            if (start, end) == (0, 6):
                return {
                    "decision": "split",
                    "split_before": "4",
                    "left": "inspect implementation",
                    "right": "validate behavior",
                }
            if (start, end) == (0, 3):
                return {
                    "decision": "split",
                    "split_before": "2",
                    "left": "locate mechanism",
                    "right": "explain mechanism",
                }
            return {"decision": "stop"}

        leaves = recursive.decompose_turns(turns, "repair software behavior", decide)
        self.assertEqual([(row["start"], row["end"]) for row in leaves], [(0, 1), (1, 3), (3, 6)])
        self.assertEqual([len(row["labels"]) for row in leaves], [3, 3, 2])
        self.assertEqual(leaves[-1]["labels"], ["repair software behavior", "validate behavior"])

    def test_build_outputs_preserves_same_turn_and_sparse_marks(self) -> None:
        session = "session-1"
        operations = [
            {"step": 1, "turn_id": "turn-a", "source_ref": "a"},
            {"step": 2, "turn_id": "turn-a", "source_ref": "b"},
            {"step": 3, "turn_id": "turn-b", "source_ref": "c"},
        ]
        turns = [
            {"turn_index": 0, "source_turn_id": "turn-a", "operations": operations[:2]},
            {"turn_index": 1, "source_turn_id": "turn-b", "operations": operations[2:]},
        ]
        prepared = {
            session: {
                "material": {
                    "session": session,
                    "framework": "test",
                    "operations": operations,
                },
                "turns": turns,
            }
        }
        results = {
            session: {
                "leaves": [
                    {"start": 0, "end": 1, "labels": ["repair software", "inspect code"]},
                    {"start": 1, "end": 2, "labels": ["repair software", "test fix"]},
                ]
            }
        }
        predictions, marks = recursive.build_outputs(prepared, results, [session])
        self.assertEqual([row["step_id"] for row in predictions], [1, 2, 3])
        self.assertEqual(predictions[0]["operation_ids"], predictions[1]["operation_ids"])
        self.assertNotEqual(predictions[1]["operation_ids"], predictions[2]["operation_ids"])
        self.assertEqual([row["start_operation_id"] for row in marks["marks"]], ["1", "3"])
        self.assertEqual(marks["sequence_field"], "traj_id")
        self.assertEqual(marks["id_field"], "step_id")

    def test_semantic_ids_are_stable_after_canonicalization(self) -> None:
        self.assertEqual(
            recursive.semantic_id("Inspect   Code"),
            recursive.semantic_id("inspect code"),
        )
        with self.assertRaisesRegex(RuntimeError, "characters"):
            recursive.canonical_label("run pytest -q /tmp/x.py")

    def test_native_tree_contracts_only_adjacent_equal_visible_paths(self) -> None:
        grouped = {
            "s": [
                {"step_id": 1, "phase": "explore", "action": "inspect", "action_detail": "rg"},
                {"step_id": 2, "phase": "explore", "action": "inspect", "action_detail": "rg"},
                {"step_id": 3, "phase": "implement", "action": "edit", "action_detail": "patch"},
                {"step_id": 4, "phase": "explore", "action": "inspect", "action_detail": "rg"},
            ]
        }
        occurrences = recursive.native_tree_occurrences(grouped, ["s"])
        self.assertEqual(
            [occurrences[("s", step)] for step in range(1, 5)],
            [
                "s:native-tree:00000",
                "s:native-tree:00000",
                "s:native-tree:00001",
                "s:native-tree:00002",
            ],
        )

    def test_inference_contract_changes_with_prompt_contract(self) -> None:
        baseline = recursive.inference_contract_hash()
        with mock.patch.object(
            recursive,
            "ROOT_SYSTEM",
            recursive.ROOT_SYSTEM + "\nchanged prompt contract",
        ):
            self.assertNotEqual(baseline, recursive.inference_contract_hash())

    def test_continuation_marks_replay_through_agentpprof(self) -> None:
        session = "continuation-session"
        operation_rows = [
            {
                "fields": {
                    "traj_id": session,
                    "step_id": str(step),
                    "source_ref": f"trace.json#{step}",
                },
                "value": 1,
            }
            for step in range(1, 5)
        ]
        root = recursive.semantic_id("repair software behavior")
        inspect = recursive.semantic_id("inspect implementation")
        validate = recursive.semantic_id("validate fix")
        mark_payload = {
            "sequence_field": "traj_id",
            "id_field": "step_id",
            "operation_names": {
                root: "repair software behavior",
                inspect: "inspect implementation",
                validate: "validate fix",
            },
            "marks": [
                {"sequence": session, "start_operation_id": "1", "operation_ids": [root, inspect]},
                {"sequence": session, "start_operation_id": "2", "operation_ids": [root]},
                {"sequence": session, "start_operation_id": "3", "operation_ids": [root, validate]},
            ],
        }
        with tempfile.TemporaryDirectory() as directory:
            root_dir = Path(directory)
            operations = root_dir / "operations.jsonl"
            marks = root_dir / "marks.json"
            profile = root_dir / "operations.pb.gz"
            operations.write_text(
                "".join(json.dumps(row, sort_keys=True) + "\n" for row in operation_rows),
                encoding="utf-8",
            )
            marks.write_text(json.dumps(mark_payload, sort_keys=True), encoding="utf-8")
            result = recursive.run_agentpprof(
                ROOT / "agentpprof/Cargo.toml",
                operations,
                marks,
                profile,
                expected_operations=4,
                expected_sessions=1,
                expected_marks=3,
            )
            self.assertEqual(result["report"]["samples"], 4)
            self.assertEqual(result["report"]["unique_stacks"], 3)


if __name__ == "__main__":
    unittest.main()
