import json
import tempfile
import unittest
from pathlib import Path

import run_pairs
import run_idfix_pairs
import run_converter_pairs
import summarize


class HelpersTest(unittest.TestCase):
    def test_population_partition(self) -> None:
        self.assertEqual(len(run_pairs.PILOT), 8)
        self.assertEqual(len(run_pairs.CONFIRMATION), 23)
        self.assertFalse(set(run_pairs.PILOT) & set(run_pairs.CONFIRMATION))
        self.assertEqual(
            set(run_pairs.ALL_OUTCOME),
            set(run_pairs.PILOT) | set(run_pairs.CONFIRMATION),
        )
        self.assertNotIn(run_pairs.PREFLIGHT[0], run_pairs.ALL_OUTCOME)

    def test_condition_seed_is_paired(self) -> None:
        self.assertEqual(run_pairs.seed_for("pilot", 3), 202607303)

    def test_expanded_pilot_population(self) -> None:
        cells = run_idfix_pairs.cells_for_group("pilot-expanded")
        self.assertEqual(len(cells), 32)
        self.assertEqual(len({seed for _, seed, _ in cells}), 32)
        self.assertEqual(
            {scenario for scenario, _, _ in cells},
            set(run_pairs.PILOT),
        )
        self.assertEqual(
            {repetition for _, _, repetition in cells},
            {0, 1, 2, 3},
        )

    def test_converter_populations_are_fixed_and_disjoint(self) -> None:
        pilot = run_converter_pairs.cells_for_group("pilot")
        confirmation = run_converter_pairs.cells_for_group("confirmation")
        mechanism = run_converter_pairs.cells_for_group("preflight-mechanism")
        self.assertEqual(len(mechanism), 5)
        self.assertEqual(len({seed for _, seed, _ in mechanism}), 5)
        self.assertEqual(len(pilot), 8 * 3)
        self.assertEqual(len(confirmation), 23 * 3)
        self.assertFalse(
            {scenario for scenario, _, _ in pilot}
            & {scenario for scenario, _, _ in confirmation}
        )
        self.assertEqual(len({seed for _, seed, _ in pilot}), len(pilot))
        self.assertEqual(
            len({seed for _, seed, _ in confirmation}),
            len(confirmation),
        )

    def test_cell_metrics(self) -> None:
        record = {
            "status": "ok",
            "evaluation": {
                "similarity": 1,
                "milestone_similarity": 1,
                "minefield_similarity": 0,
                "turn_count": 5,
            },
            "agent": {
                "model_calls": 2,
                "tool_calls": 3,
                "usage": {
                    "prompt_tokens": 10,
                    "completion_tokens": 4,
                    "total_tokens": 14,
                },
            },
        }
        metrics = summarize.cell_metrics(record)
        self.assertEqual(metrics["success"], 1)
        self.assertEqual(metrics["agent_total_tokens"], 14)
        self.assertEqual(metrics["agent_tool_calls"], 3)

    def test_paired_ratio_ci(self) -> None:
        rows = [
            {
                "before": {"agent_total_tokens": 10},
                "after": {"agent_total_tokens": 5},
            },
            {
                "before": {"agent_total_tokens": 20},
                "after": {"agent_total_tokens": 10},
            },
        ]
        self.assertEqual(
            summarize.paired_ratio_ci(rows, "agent_total_tokens"),
            [0.5, 0.5],
        )


if __name__ == "__main__":
    unittest.main()
