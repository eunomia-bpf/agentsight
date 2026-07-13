#!/usr/bin/env python3
"""Focused tests for the approved AgentProcessBench Wilson construction."""

from __future__ import annotations

import importlib.util
import inspect
import json
from pathlib import Path
import tempfile
import unittest

import numpy as np


SCRIPT_PATH = Path(__file__).with_name("agentprocessbench_wilson_eval.py")
SPEC = importlib.util.spec_from_file_location("agentprocessbench_wilson_eval", SCRIPT_PATH)
assert SPEC is not None and SPEC.loader is not None
experiment = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(experiment)


def visible_row(family: str, index: int) -> dict:
    return {
        "operation_id": f"{family}:0:0:{index}",
        "family": family,
        "task_id": f"{family}:0",
        "trajectory_id": f"{family}:0:0",
        "session": f"{family}:0:0",
        "query_index": 0,
        "sample_index": 0,
        "message_index": index,
        "step_ordinal": index,
        "intent": "lookup",
        "phase": "work",
        "action": "tool_call",
        "target": "search",
        "repeat_state": "single",
        "flat": "all",
    }


def assignment(row: dict, stack_key: str = "same") -> dict:
    return {
        "operation_id": row["operation_id"],
        "family": row["family"],
        "groups": {view: stack_key for view in experiment.ALL_VIEWS},
    }


def risk(negative: int, available: int) -> dict:
    return {
        "risk": negative / available if available else 0.5,
        "risk_units": 0,
        "available_predictions": available,
        "negative_predictions": negative,
        "prediction_slots": 20,
    }


class AgentProcessBenchWilsonTests(unittest.TestCase):
    def test_wilson_formula_and_zero_vote_rule(self) -> None:
        self.assertEqual(0.0, experiment.wilson_lower_score(0, 0))
        self.assertAlmostEqual(
            0.4038315303659956,
            experiment.wilson_lower_score(50, 100),
        )
        scores = experiment.wilson_score_array(
            np.asarray([0.0, 50.0]), np.asarray([0.0, 100.0])
        )
        np.testing.assert_allclose(scores, [0.0, 0.4038315303659956])
        with self.assertRaises(experiment.ExperimentError):
            experiment.wilson_lower_score(2, 1)

    def test_materialization_keeps_identical_keys_family_local(self) -> None:
        rows = [visible_row(family, 0) for family in experiment.FAMILIES]
        risks = {row["operation_id"]: risk(10, 20) for row in rows}
        assignments = [assignment(row, "flat:all") for row in rows]
        with tempfile.TemporaryDirectory() as raw_tmp:
            group_rows, operation_rows, audit = experiment.materialize_group_scores(
                rows, risks, assignments, Path(raw_tmp)
            )
            flat = [row for row in group_rows if row["view"] == "flat"]
            self.assertEqual(4, len(flat))
            self.assertEqual(set(experiment.FAMILIES), {row["family"] for row in flat})
            self.assertTrue(audit["views"]["flat"]["family_local_exact"])
            self.assertEqual(4, len(operation_rows))
            written = [
                json.loads(line)
                for line in (Path(raw_tmp) / "wilson-group-scores.jsonl")
                .read_text(encoding="utf-8")
                .splitlines()
            ]
            self.assertFalse(any("human_label" in row for row in written))

    def test_all_null_operation_scores_zero_and_remains_counted(self) -> None:
        rows = [visible_row(family, 0) for family in experiment.FAMILIES]
        risks = {
            row["operation_id"]: (
                risk(0, 0) if row["family"] == "gaia_dev" else risk(10, 20)
            )
            for row in rows
        }
        with tempfile.TemporaryDirectory() as raw_tmp:
            group_rows, operation_rows, audit = experiment.materialize_group_scores(
                rows,
                risks,
                [assignment(row) for row in rows],
                Path(raw_tmp),
            )
        self.assertEqual(len(experiment.ALL_VIEWS), len(audit["zero_vote_groups"]))
        self.assertEqual(4 * len(experiment.ALL_VIEWS), len(group_rows))
        self.assertTrue(
            all(
                record["score"] == 0.0
                for record in group_rows
                if record["family"] == "gaia_dev"
            )
        )
        gaia_operation = next(
            record for record in operation_rows if record["family"] == "gaia_dev"
        )
        self.assertTrue(all(score == 0.0 for score in gaia_operation["scores"].values()))
        self.assertTrue(
            all(view["operations"] == 4 for view in audit["views"].values())
        )

    def test_metric_uses_complete_equal_score_tiers(self) -> None:
        state = {
            "groups": {
                "semantic": np.asarray([0, 0, 1, 1, 2, 2, 2, 2], dtype=np.int32)
            },
            "group_labels": {"semantic": ["g0", "g1", "g2"]},
            "harmful_votes": np.asarray([10, 10, 10, 10, 0, 0, 0, 0]),
            "available_votes": np.asarray([20] * 8),
            "labels": np.asarray([1, 1, 0, 0, 1, 1, 0, 0]),
        }
        metric = experiment.metric_for_view(
            state, "semantic", np.ones(8, dtype=np.float64)
        )
        self.assertAlmostEqual(0.5, metric["average_precision"])
        self.assertAlmostEqual(0.5, metric["work_to_50"])
        self.assertEqual(2, metric["groups_to_50"])

    def test_metric_recomputes_score_from_resampling_weights(self) -> None:
        state = {
            "groups": {"raw_action": np.asarray([0, 0, 1], dtype=np.int32)},
            "group_labels": {"raw_action": ["mixed", "other"]},
            "harmful_votes": np.asarray([20, 0, 5]),
            "available_votes": np.asarray([20, 20, 20]),
            "labels": np.asarray([0, 1, 1]),
        }
        first = experiment.metric_for_view(
            state, "raw_action", np.asarray([1.0, 0.0, 1.0])
        )
        second = experiment.metric_for_view(
            state, "raw_action", np.asarray([0.0, 1.0, 1.0])
        )
        self.assertLess(first["average_precision"], second["average_precision"])
        self.assertEqual(40.0, first["available_votes"])
        self.assertEqual(40.0, second["available_votes"])

    def test_shuffle_is_deterministic_and_family_local(self) -> None:
        for family_index, family in enumerate(experiment.FAMILIES):
            rows = []
            for index in range(24):
                row = visible_row(family, index)
                row["intent"] = f"intent-{index % 3}"
                row["phase"] = ("open", "work")[index % 2]
                rows.append(row)
            state = {"rows": rows}
            first, exact = experiment.base.shuffled_semantic_keys(
                state, 4204, 7, family_index
            )
            second, second_exact = experiment.base.shuffled_semantic_keys(
                state, 4204, 7, family_index
            )
            self.assertTrue(exact and second_exact)
            self.assertEqual(first, second)
            self.assertTrue(
                all(
                    f"{other}:" not in key
                    for key in first
                    for other in experiment.FAMILIES
                    if other != family
                )
            )

    def test_verdict_is_mechanical(self) -> None:
        supported_bootstrap = {
            "complete": True,
            "intervals": {
                "semantic_minus_raw_ap": [0.01, 0.03],
                "raw_minus_semantic_work50": [0.02, 0.04],
            },
        }
        self.assertEqual(
            "SUPPORTED",
            experiment.scientific_verdict(
                "full", supported_bootstrap, {"p_shuffle_ap": 0.01}
            ),
        )
        crossing = {
            "complete": True,
            "intervals": {
                "semantic_minus_raw_ap": [0.01, 0.03],
                "raw_minus_semantic_work50": [-0.01, 0.04],
            },
        }
        self.assertEqual(
            "INCONCLUSIVE",
            experiment.scientific_verdict("full", crossing, {"p_shuffle_ap": 0.01}),
        )

    def test_run_materializes_scores_before_loading_human_labels(self) -> None:
        source = inspect.getsource(experiment.run)
        self.assertLess(
            source.index("materialize_group_scores"),
            source.index("load_human_labels"),
        )


if __name__ == "__main__":
    unittest.main()
