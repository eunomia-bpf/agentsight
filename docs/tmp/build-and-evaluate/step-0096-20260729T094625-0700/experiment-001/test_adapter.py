import copy
import unittest

import run_annotation


class AdapterTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.packet = run_annotation.load_packets()[0]

    def test_skeleton_omits_results_and_preserves_turns(self) -> None:
        skeleton = run_annotation.skeleton(self.packet)
        self.assertEqual(len(skeleton["turns"]), len(self.packet["turns"]))
        self.assertTrue(all("visible_result" not in turn for turn in skeleton["turns"]))
        self.assertEqual(
            [turn["first_operation_id"] for turn in skeleton["turns"]],
            [turn["first_operation_id"] for turn in self.packet["turns"]],
        )

    def test_deterministic_selector_is_bounded(self) -> None:
        selected = run_annotation.deterministic_detail_turns(self.packet)
        expected = max(
            2, min(10, __import__("math").ceil(len(self.packet["turns"]) * 0.15))
        )
        self.assertEqual(len(selected), expected)
        self.assertEqual(selected, sorted(set(selected)))
        compact = run_annotation.selective_packet(self.packet, selected)
        for index, turn in enumerate(compact["turns"]):
            self.assertEqual("visible_result" in turn, index in set(selected))

    def test_refinement_is_local_and_stitches(self) -> None:
        root = "resolve compiler crash"
        coarse = {
            "session": self.packet["session"],
            "marks": [
                {
                    "start_operation_id": self.packet["turns"][0][
                        "first_operation_id"
                    ],
                    "semantic_path": [root, "inspect repository"],
                }
            ],
            "detail_turns": [1],
        }
        payload, allowed = run_annotation.refinement_packet(self.packet, coarse)
        self.assertEqual(
            len(payload["global_skeleton"]), int(self.packet["turn_count"])
        )
        self.assertIn("visible_result", payload["selected_full_turns"][0])
        update_start = self.packet["turns"][2]["first_operation_id"]
        refinement = {
            "session": self.packet["session"],
            "updates": [
                {
                    "start_operation_id": update_start,
                    "semantic_path": [root, "diagnose crash"],
                }
            ],
            "remove_start_operation_ids": [],
        }
        self.assertFalse(
            run_annotation.validate_refinement(
                self.packet, coarse, allowed, refinement
            )
        )
        result = run_annotation.stitch(self.packet, coarse, refinement)
        self.assertFalse(run_annotation.direct.validate_response(self.packet, result))

    def test_outside_window_update_is_rejected(self) -> None:
        coarse = {
            "session": self.packet["session"],
            "marks": [
                {
                    "start_operation_id": self.packet["turns"][0][
                        "first_operation_id"
                    ],
                    "semantic_path": ["resolve compiler crash"],
                }
            ],
            "detail_turns": [1],
        }
        _, allowed = run_annotation.refinement_packet(self.packet, coarse)
        bad = {
            "session": self.packet["session"],
            "updates": [
                {
                    "start_operation_id": self.packet["turns"][-1][
                        "first_operation_id"
                    ],
                    "semantic_path": ["resolve compiler crash", "verify tests"],
                }
            ],
            "remove_start_operation_ids": [],
        }
        self.assertTrue(
            run_annotation.validate_refinement(self.packet, coarse, allowed, bad)
        )

    def test_split_metadata_is_not_counted_as_attempts(self) -> None:
        summary = run_annotation.summarize_attempts(
            {
                "router": [
                    {
                        "attempt": 1,
                        "started_unix": 1.0,
                        "wall_seconds": 2.0,
                        "usage": {"input_tokens": 10, "output_tokens": 2},
                        "errors": [],
                    }
                ],
                "refine": [
                    {
                        "attempt": 1,
                        "started_unix": 3.0,
                        "wall_seconds": 4.0,
                        "usage": {"input_tokens": 5, "output_tokens": 1},
                        "errors": [],
                    }
                ],
                "detail_turns": [1, 2],
            }
        )
        self.assertEqual(summary["calls"], 2)
        self.assertEqual(summary["provider_tokens"], 18)


if __name__ == "__main__":
    unittest.main()
