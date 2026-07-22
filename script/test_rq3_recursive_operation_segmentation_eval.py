#!/usr/bin/env python3

from __future__ import annotations

import sys
from pathlib import Path
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "script"))

import rq3_recursive_operation_segmentation_eval as recursive  # noqa: E402


class RecursiveOperationSegmentationTest(unittest.TestCase):
    def test_parse_decision_rejects_invalid_or_colliding_split(self) -> None:
        self.assertEqual(
            recursive.parse_decision('{"decision":"stop"}', ["2"], ["root"]),
            {"decision": "stop"},
        )
        self.assertEqual(
            recursive.parse_decision(
                '{"decision":"split","split_before":"2","left":"inspect code","right":"test fix"}',
                ["2", "3"],
                ["root"],
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
                ["root"],
            )
        with self.assertRaisesRegex(RuntimeError, "equals ancestor"):
            recursive.parse_decision(
                '{"decision":"split","split_before":"2","left":"root","right":"test fix"}',
                ["2"],
                ["root"],
            )

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

    def test_inference_contract_changes_with_prompt_contract(self) -> None:
        baseline = recursive.inference_contract_hash()
        with mock.patch.object(
            recursive,
            "ROOT_SYSTEM",
            recursive.ROOT_SYSTEM + "\nchanged prompt contract",
        ):
            self.assertNotEqual(baseline, recursive.inference_contract_hash())


if __name__ == "__main__":
    unittest.main()
