from pathlib import Path
import json
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "script"))

import assemble_agent_operation_profile as assemble


class AssembleAgentOperationProfileTests(unittest.TestCase):
    def test_contracts_one_turn_root_only_prefix_into_first_responsibility(self) -> None:
        packets = {
            "s": {
                "turns": [
                    {"first_operation_id": "1"},
                    {"first_operation_id": "2"},
                    {"first_operation_id": "3"},
                ]
            }
        }
        annotations = {
            "s": {
                "marks": [
                    {"start_operation_id": "1", "semantic_path": ["task"]},
                    {"start_operation_id": "2", "semantic_path": ["task", "inspect"]},
                    {"start_operation_id": "3", "semantic_path": ["task", "change"]},
                ],
                "findings": [],
            }
        }
        marks, normalized, _ = assemble.validate_and_merge_marks(
            packets, annotations, {"s": "task"}, {}, {}, True
        )
        self.assertEqual(len(marks["marks"]), 2)
        self.assertEqual(
            normalized["s"][0]["semantic_path"], ["task", "inspect"]
        )
        self.assertEqual(normalized["s"][0]["start_operation_id"], "1")

    def test_source_only_main_agent_override_replaces_named_session(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            base = root / "base"
            base.mkdir()
            (base / "batch-01.json").write_text(
                json.dumps({
                    "batch": 1,
                    "sessions": [
                        {"session": "s", "marks": [{"start_operation_id": "1", "semantic_path": ["old"]}]}
                    ],
                })
            )
            override = root / "override.json"
            override.write_text(
                json.dumps({
                    "backend": "automatic-main-agent",
                    "sessions": [
                        {"session": "s", "marks": [{"start_operation_id": "1", "semantic_path": ["new"]}]}
                    ],
                })
            )
            loaded = assemble.load_annotations([base], 1, [override])
            self.assertEqual(loaded["s"]["marks"][0]["semantic_path"], ["new"])

    def test_adjacent_identical_paths_contract_after_canonicalization(self) -> None:
        packets = {
            "s": {
                "turns": [
                    {"first_operation_id": "1"},
                    {"first_operation_id": "2"},
                    {"first_operation_id": "3"},
                ]
            }
        }
        annotations = {
            "s": {
                "marks": [
                    {"start_operation_id": "1", "semantic_path": ["A"]},
                    {"start_operation_id": "2", "semantic_path": ["alias A"]},
                    {"start_operation_id": "3", "semantic_path": ["B"]},
                ],
                "findings": [],
            }
        }
        marks, normalized, _ = assemble.validate_and_merge_marks(
            packets,
            annotations,
            {"s": "task"},
            {},
            {"alias A": "A"},
        )
        self.assertEqual(len(marks["marks"]), 2)
        self.assertEqual(
            [mark["start_operation_id"] for mark in normalized["s"]], ["1", "3"]
        )

    def test_case_only_label_variants_share_one_semantic_id(self) -> None:
        packets = {
            "s": {
                "turns": [
                    {"first_operation_id": "1"},
                    {"first_operation_id": "2"},
                ]
            }
        }
        annotations = {
            "s": {
                "marks": [
                    {"start_operation_id": "1", "semantic_path": ["Inspect repository"]},
                    {"start_operation_id": "2", "semantic_path": ["inspect repository"]},
                ],
                "findings": [],
            }
        }
        marks, normalized, _ = assemble.validate_and_merge_marks(
            packets, annotations, {"s": "task"}, {}, {}
        )
        self.assertEqual(len(marks["marks"]), 1)
        self.assertEqual(
            normalized["s"][0]["semantic_path"], ["inspect repository"]
        )

    def test_source_order_rejects_reordered_operations(self) -> None:
        rows = [
            {"fields": {"traj_id": "s", "step_id": step}}
            for step in (1, 3, 2, 4)
        ]
        with self.assertRaisesRegex(RuntimeError, "source order mismatch"):
            assemble.validate_source_order(rows, {"s": [1, 2, 3, 4]})

    def test_returned_path_gets_fresh_contiguous_occurrence(self) -> None:
        rows = [
            {
                "fields": {
                    "traj_id": "s",
                    "step_id": step,
                    "source_ref": f"r{step}",
                    "agent": "a",
                    "call": "t1" if step < 3 else f"t{step}",
                }
            }
            for step in (1, 2, 3, 4)
        ]
        marks = {
            "operation_names": {"a": "A", "b": "B"},
            "marks": [
                {"sequence": "s", "start_operation_id": "1", "operation_ids": ["a"]},
                {"sequence": "s", "start_operation_id": "3", "operation_ids": ["b"]},
                {"sequence": "s", "start_operation_id": "4", "operation_ids": ["a"]},
            ],
        }
        predictions = assemble.expand_predictions(rows, marks, 4)
        self.assertEqual(
            [row["task_occurrence_instance"] for row in predictions],
            ["s:mark-0000", "s:mark-0000", "s:mark-0001", "s:mark-0002"],
        )
        self.assertEqual(
            [row["source_turn_instance"] for row in predictions],
            ["s:turn:t1", "s:turn:t1", "s:turn:t3", "s:turn:t4"],
        )
        self.assertEqual(
            [row["source_turn_id"] for row in predictions],
            ["t1", "t1", "t3", "t4"],
        )


if __name__ == "__main__":
    unittest.main()
