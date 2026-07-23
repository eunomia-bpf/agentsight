#!/usr/bin/env python3

import importlib.util
from pathlib import Path
import tempfile
import unittest


MODULE_PATH = Path(__file__).with_name("rq2_canonical_tag_compare.py")
SPEC = importlib.util.spec_from_file_location("rq2_canonical_tag_compare", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class CanonicalTagTest(unittest.TestCase):
    def test_action_object_tags_are_short_and_reusable(self) -> None:
        cases = {
            "Gather external evidence": "collect evidence external",
            "Repair software regression": "resolve failure",
            "Run regression tests": "test failure",
            "Report task completion": "report completion",
            "Manage GitHub workflow": "execute workflow",
            "Repeat evidence search": "repeat evidence",
        }
        for source, expected in cases.items():
            with self.subTest(source=source):
                actual = MODULE.canonicalize_tag(source)
                self.assertEqual(actual, expected)
                self.assertLessEqual(len(actual.split()), 3)

    def test_prepare_preserves_sparse_annotation_structure(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for workload in MODULE.WORKLOADS:
                MODULE.write_json(
                    root / "current" / workload / "annotations" / "batch-0001.json",
                    {
                        "batch": 1,
                        "sessions": [
                            {
                                "sequence": f"{workload}:1",
                                "marks": [
                                    {
                                        "start_operation_id": f"{workload}:op:0",
                                        "semantic_path": [
                                            "Repair software regression",
                                            "Run regression tests",
                                        ],
                                    }
                                ],
                            }
                        ],
                    },
                )
            report = MODULE.prepare(
                root / "current", root / "candidate", root / "mapping.json"
            )
            self.assertEqual(report["old_unique_tags"], 2)
            self.assertEqual(report["counts"]["hint"]["marks"], 1)
            payload = MODULE.read_json(
                root / "candidate" / "trace" / "annotations" / "batch-0001.json"
            )
            self.assertEqual(
                payload["sessions"][0]["marks"][0]["semantic_path"],
                ["resolve failure", "test failure"],
            )

    def test_adjacent_collision_is_invalid(self) -> None:
        payload = {
            "batch": 1,
            "sessions": [
                {
                    "sequence": "s",
                    "marks": [
                        {"start_operation_id": "a", "semantic_path": ["Inspect file"]},
                        {"start_operation_id": "b", "semantic_path": ["Review file"]},
                    ],
                }
            ],
        }
        mapping = {"Inspect file": "inspect artifact", "Review file": "inspect artifact"}
        with self.assertRaises(MODULE.ExperimentError):
            MODULE.transformed_payload(payload, mapping, Path("synthetic.json"))

    def test_head_noun_refinement_preserves_a_colliding_boundary(self) -> None:
        left = MODULE.specific_canonicalize_tag("Use task-specific tool")
        right = MODULE.specific_canonicalize_tag("Execute travel action")
        self.assertEqual(left, "execute tool")
        self.assertEqual(right, "execute travel action")
        self.assertNotEqual(left, right)

    def test_refinement_preserves_action_and_discriminative_qualifier(self) -> None:
        self.assertNotEqual(
            MODULE.specific_canonicalize_tag("Inspect candidate source"),
            MODULE.specific_canonicalize_tag("Read candidate source"),
        )
        self.assertEqual(
            MODULE.specific_canonicalize_tag("Review environmental health data"),
            "inspect environmental data",
        )
        self.assertEqual(
            MODULE.specific_canonicalize_tag("Review population health data"),
            "inspect population data",
        )

    def test_hint_clusters_come_from_projection_environment(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "operations" / "test-projection.jsonl"
            path.parent.mkdir(parents=True)
            path.write_text(
                '{"record_key":"test:7","raw_fields":{"environment":"security"}}\n'
                '{"record_key":"test:7","raw_fields":{"environment":"security"}}\n',
                encoding="utf-8",
            )
            assignments, universe = MODULE.workload_clusters(
                "hint", root, {"test:7"}
            )
            self.assertEqual(assignments, {"test:7": ("security", "test:7")})
            self.assertIsNone(universe)

    def test_source_evidence_and_fixed_suffix_must_match(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            current = root / "current" / "per-query.jsonl"
            candidate = root / "candidate" / "per-query.jsonl"
            current.parent.mkdir()
            candidate.parent.mkdir()
            current.write_text("", encoding="utf-8")
            candidate.write_text("", encoding="utf-8")
            current_source = current.parent / "source-operations.jsonl"
            candidate_source = candidate.parent / "source-operations.jsonl"
            current_source.write_text('{"fields":{"tool":"bash"}}\n', encoding="utf-8")
            candidate_source.write_text(
                '{"fields":{"tool":"bash","outcome":"ok"}}\n', encoding="utf-8"
            )
            with self.assertRaisesRegex(
                MODULE.ExperimentError, "source-evidence rows differ"
            ):
                MODULE.require_fair_group_inputs(current, candidate)
            candidate_source.write_bytes(current_source.read_bytes())
            row = {
                "operation_id": "op:1",
                "sequence": "s:1",
                "task_family": "coding",
                "groups": {
                    "native_tree": ["native"],
                    "recurrence": ["recurrence"],
                    "automatic_agent": ["project", "inspect source"],
                    "source_preserving_agent": [
                        "project",
                        "inspect source",
                        "tool_call",
                        "bash",
                    ],
                },
            }
            (current.parent / "fixed-groups.jsonl").write_text(
                MODULE.json.dumps(row) + "\n", encoding="utf-8"
            )
            candidate_row = MODULE.json.loads(MODULE.json.dumps(row))
            candidate_row["groups"]["automatic_agent"][-1] = "inspect artifact"
            candidate_row["groups"]["source_preserving_agent"] = [
                "project",
                "inspect artifact",
                "tool_call",
                "bash",
            ]
            (candidate.parent / "fixed-groups.jsonl").write_text(
                MODULE.json.dumps(candidate_row) + "\n", encoding="utf-8"
            )
            MODULE.require_fair_group_inputs(current, candidate)
            candidate_row["groups"]["source_preserving_agent"][-1] = "ok"
            (candidate.parent / "fixed-groups.jsonl").write_text(
                MODULE.json.dumps(candidate_row) + "\n", encoding="utf-8"
            )
            with self.assertRaisesRegex(
                MODULE.ExperimentError, "source-evidence suffix differs"
            ):
                MODULE.require_fair_group_inputs(current, candidate)


if __name__ == "__main__":
    unittest.main()
