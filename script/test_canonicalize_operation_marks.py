#!/usr/bin/env python3

import importlib.util
from pathlib import Path
import sys
import unittest


MODULE_PATH = Path(__file__).with_name("canonicalize_operation_marks.py")
sys.path.insert(0, str(MODULE_PATH.parent))
SPEC = importlib.util.spec_from_file_location("canonicalize_operation_marks", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class CanonicalizeOperationMarksTest(unittest.TestCase):
    def test_boundary_safe_refinement_preserves_structure(self) -> None:
        mark_file = {
            "id_field": "step",
            "sequence_field": "session",
            "operation_names": {
                "root": "Repair software regression",
                "a": "convert the training corpus",
                "b": "convert the evaluation corpus",
                "c": "propagate movement validation to openmp",
                "d": "propagate movement validation to mpi",
                "e": "manually inspect motion",
                "f": "malformed html parser",
            },
            "marks": [
                {"sequence": "s", "start_operation_id": "1", "operation_ids": ["root", "a"]},
                {"sequence": "s", "start_operation_id": "2", "operation_ids": ["root", "b"]},
                {"sequence": "s", "start_operation_id": "3", "operation_ids": ["root", "c"]},
                {"sequence": "s", "start_operation_id": "4", "operation_ids": ["root", "d"]},
                {"sequence": "s", "start_operation_id": "5", "operation_ids": ["root", "e"]},
                {"sequence": "s", "start_operation_id": "6", "operation_ids": ["root", "f"]},
            ],
        }
        operations = [
            {
                "value": 1,
                "fields": {
                    "traj_id": "s",
                    "step_id": index,
                    "agent": "test-agent",
                    "source_ref": f"source-{index}",
                    "call": f"call-{index}",
                },
            }
            for index in range(1, 7)
        ]

        transformed, transformed_predictions, report = MODULE.transform(
            mark_file, operations
        )

        self.assertEqual(
            [
                (row["sequence"], row["start_operation_id"], len(row["operation_ids"]))
                for row in mark_file["marks"]
            ],
            [
                (row["sequence"], row["start_operation_id"], len(row["operation_ids"]))
                for row in transformed["marks"]
            ],
        )
        self.assertEqual(
            report["structural_sha256_before"], report["structural_sha256_after"]
        )
        self.assertEqual(report["remaining_adjacent_collisions"], 0)
        self.assertIsNone(report["reference_temporal_partition_equal"])
        self.assertNotEqual(
            transformed["marks"][0]["operation_ids"][-1],
            transformed["marks"][1]["operation_ids"][-1],
        )
        self.assertNotEqual(
            transformed["marks"][2]["operation_ids"][-1],
            transformed["marks"][3]["operation_ids"][-1],
        )
        self.assertTrue(
            all(
                len(value.split()) <= 3
                for value in transformed["operation_names"].values()
            )
        )
        self.assertEqual(len(transformed_predictions), 6)
        self.assertEqual(
            [row["task_occurrence_instance"] for row in transformed_predictions],
            [f"s:mark-{index:04d}" for index in range(6)],
        )
        emitted = set(transformed["operation_names"].values())
        self.assertEqual(
            MODULE.specific_tag("manually inspect motion"),
            "inspect manually motion",
        )
        self.assertEqual(
            MODULE.specific_tag("malformed html parser"),
            "execute malformed html",
        )
        allowed = {verb for verb, _phrases in MODULE.VERB_RULES}
        self.assertTrue(all(value.split()[0] in allowed for value in emitted))


if __name__ == "__main__":
    unittest.main()
