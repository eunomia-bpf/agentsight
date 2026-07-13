#!/usr/bin/env python3
"""Regression tests for the AgentProcessBench RQ2 experiment."""

from __future__ import annotations

from collections import Counter
import importlib.util
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock

import numpy as np


SCRIPT_PATH = Path(__file__).with_name("agentprocessbench_profile_eval.py")
AGENTPPROF = SCRIPT_PATH.parent.parent / "agentpprof" / "target" / "release" / "agentpprof"
SPEC = importlib.util.spec_from_file_location("agentprocessbench_profile_eval", SCRIPT_PATH)
assert SPEC is not None
experiment = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(experiment)


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def visible_row(index: int, intent: str, phase: str) -> dict:
    return {
        "operation_id": f"bfcl:0:0:{index}",
        "family": "bfcl",
        "task_id": "bfcl:0",
        "trajectory_id": "bfcl:0:0",
        "session": "bfcl:0:0",
        "query_index": 0,
        "sample_index": 0,
        "message_index": index,
        "step_ordinal": index,
        "intent": intent,
        "phase": phase,
        "action": "tool_call",
        "target": "search",
        "repeat_state": "single",
        "flat": "all",
    }


class AgentProcessBenchExperimentTests(unittest.TestCase):
    def test_message_action_target_and_phase_are_visible_only(self) -> None:
        tool_message = {
            "role": "assistant",
            "tool_calls": [
                {"function": {"name": "Web Search"}},
                {"function": {"name": "Calculator"}},
                {"function": {"name": "Web Search"}},
            ],
        }
        self.assertEqual(
            ("tool_call", "calculator+web-search"),
            experiment.message_action_target(tool_message, final_assistant=False),
        )
        self.assertEqual(
            ("reasoning", "user"),
            experiment.message_action_target(
                {"role": "assistant", "content": "thinking"},
                final_assistant=False,
            ),
        )
        self.assertEqual(
            ("final_answer", "final"),
            experiment.message_action_target(
                {"role": "assistant", "content": "done"},
                final_assistant=True,
            ),
        )
        self.assertEqual("no_tool", experiment.phase_for_ordinal(0, []))
        self.assertEqual("open", experiment.phase_for_ordinal(0, [1, 3]))
        self.assertEqual("work", experiment.phase_for_ordinal(2, [1, 3]))
        self.assertEqual("close", experiment.phase_for_ordinal(4, [1, 3]))

    def test_metric_treats_equal_score_tier_atomically(self) -> None:
        metric = experiment.metric_from_group_arrays(
            scores=np.asarray([1.0, 1.0, 0.0]),
            counts=np.asarray([2.0, 2.0, 4.0]),
            positives=np.asarray([2.0, 0.0, 2.0]),
        )
        self.assertAlmostEqual(0.5, metric["average_precision"])
        self.assertEqual(0.0, metric["recall_at_30"])
        self.assertEqual(0.5, metric["work_to_50"])
        self.assertEqual(2, metric["groups_to_50"])

    def test_metric_accepts_all_positive_bootstrap_population(self) -> None:
        metric = experiment.metric_from_group_arrays(
            scores=np.asarray([0.5]),
            counts=np.asarray([3.0]),
            positives=np.asarray([3.0]),
        )
        self.assertEqual(1.0, metric["average_precision"])
        self.assertEqual(1.0, metric["work_to_50"])

    def test_matched_shuffle_is_deterministic_and_size_preserving(self) -> None:
        rows = [
            visible_row(index, f"intent{index % 3}", ("open", "work")[index % 2])
            for index in range(24)
        ]
        state = {"rows": rows}
        first, exact = experiment.shuffled_semantic_keys(state, 4204, 7, 0)
        second, second_exact = experiment.shuffled_semantic_keys(state, 4204, 7, 0)
        original = [experiment.method_key(row, "semantic") for row in rows]
        self.assertTrue(exact)
        self.assertTrue(second_exact)
        self.assertEqual(first, second)
        self.assertEqual(
            sorted(Counter(original).values()),
            sorted(Counter(first).values()),
        )
        self.assertNotEqual(original, first)

    def test_released_judge_consensus_and_all_null_rule(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            source = Path(raw_tmp)
            full_ids = {
                experiment.operation_id(family, 0, 0, step)
                for family in experiment.FAMILIES
                for step in (0, 1)
            }
            for model in range(experiment.EXPECTED_MODELS):
                model_dir = source / "eval" / "results" / f"model-{model:02d}"
                model_dir.mkdir(parents=True)
                for family in experiment.FAMILIES:
                    labels = {
                        "0": None
                        if family == "bfcl"
                        else (-1 if model < 10 else 1),
                        "1": -1 if model < 10 else 1,
                    }
                    path = model_dir / f"{family}__predictions.jsonl"
                    path.write_text(
                        json.dumps(
                            {
                                "query_index": 0,
                                "sample_index": 0,
                                "step_labels": labels,
                            }
                        )
                        + "\n",
                        encoding="utf-8",
                    )

            selected_ids = {
                experiment.operation_id("bfcl", 0, 0, 0),
                experiment.operation_id("tau2", 0, 0, 1),
            }
            with (
                mock.patch.object(
                    experiment, "EXPECTED_TRAJECTORIES_PER_FAMILY", 1
                ),
                mock.patch.object(experiment, "EXPECTED_ALL_NULL", 1),
            ):
                risks, audit = experiment.load_external_risks(
                    source, full_ids, selected_ids
                )

            null_id = experiment.operation_id("bfcl", 0, 0, 0)
            consensus_id = experiment.operation_id("tau2", 0, 0, 1)
            self.assertEqual(0.5, risks[null_id]["risk"])
            self.assertEqual(0, risks[null_id]["available_predictions"])
            self.assertEqual(0.5, risks[consensus_id]["risk"])
            self.assertEqual(20, risks[consensus_id]["available_predictions"])
            self.assertEqual(experiment.RISK_SCALE // 2, risks[null_id]["risk_units"])
            self.assertEqual([null_id], audit["all_null_steps"])

    @unittest.skipUnless(AGENTPPROF.exists(), "release AgentProf binary is absent")
    def test_real_agentprof_profiles_visible_fields_without_labels(self) -> None:
        rows = [
            visible_row(0, "lookup", "open"),
            visible_row(1, "lookup", "work"),
            visible_row(2, "compare", "work"),
            visible_row(3, "compare", "close"),
        ]
        risks = {
            row["operation_id"]: {
                "risk": index / 3,
                "risk_units": (index * experiment.RISK_SCALE) // 3,
                "available_predictions": 20,
                "negative_predictions": index,
                "prediction_slots": 20,
            }
            for index, row in enumerate(rows)
        }
        with tempfile.TemporaryDirectory() as raw_tmp:
            out = Path(raw_tmp)
            assignments, report = experiment.construct_profiles(
                rows, risks, AGENTPPROF, out
            )
            projection = read_jsonl(out / "projection.jsonl")
            operations = read_jsonl(out / "operations.jsonl")
            risk_operations = read_jsonl(out / "risk-operations.jsonl")
            self.assertEqual(len(rows), len(assignments))
            self.assertNotIn("human_label", json.dumps(projection))
            self.assertNotIn("risk", json.dumps(operations))
            self.assertNotIn("human_label", json.dumps(risk_operations))
            self.assertEqual(set(experiment.ALL_VIEWS), set(report["views"]))
            self.assertTrue(
                all(
                    view["operation_conservation_exact"]
                    and view["risk_conservation_exact"]
                    and view["per_group_risk_exact"]
                    for view in report["views"].values()
                )
            )
            self.assertTrue(
                all(
                    view["expected_risk_units"] == view["observed_risk_units"]
                    for view in report["views"].values()
                )
            )

    def test_profile_construction_rejects_lost_risk_units(self) -> None:
        rows = [
            visible_row(0, "lookup", "open"),
            visible_row(1, "compare", "work"),
        ]
        risks = {
            row["operation_id"]: {
                "risk": 0.5,
                "risk_units": experiment.RISK_SCALE // 2,
                "available_predictions": 20,
                "negative_predictions": 10,
                "prediction_slots": 20,
            }
            for row in rows
        }
        invocations: list[Counter] = []
        for method in experiment.PROFILE_FIELDS:
            count = Counter(experiment.method_key(row, method) for row in rows)
            risk = Counter()
            for row in rows:
                risk[experiment.method_key(row, method)] += experiment.RISK_SCALE // 2
            shifted_risk = Counter(
                {group: risk[group] + count[group] for group in count}
            )
            if method == "semantic":
                shifted_risk[next(iter(shifted_risk))] -= 1
            invocations.extend([count, shifted_risk])
        with (
            tempfile.TemporaryDirectory() as raw_tmp,
            mock.patch.object(
                experiment, "agentprof_version", return_value=experiment.AGENTPROF_VERSION
            ),
            mock.patch.object(
                experiment, "invoke_agentprof", side_effect=invocations
            ),
            self.assertRaises(experiment.ExperimentError),
        ):
            experiment.construct_profiles(rows, risks, AGENTPPROF, Path(raw_tmp))

    def test_run_loads_human_label_values_only_after_profiles(self) -> None:
        row = visible_row(0, "lookup", "work")
        op_id = row["operation_id"]
        risk = {
            "risk": 0.5,
            "risk_units": experiment.RISK_SCALE // 2,
            "available_predictions": 20,
            "negative_predictions": 10,
            "prediction_slots": 20,
        }
        assignment = {
            "operation_id": op_id,
            "groups": {method: op_id for method in experiment.ALL_VIEWS},
        }
        order: list[str] = []

        def profiles(*_args, **_kwargs):
            order.append("profiles")
            return [assignment], {
                "agentprof_version": experiment.AGENTPROF_VERSION,
                "views": {},
            }

        def labels(*_args, **_kwargs):
            order.append("labels")
            return {op_id: -1}, {"loaded_after_profiles": True}

        bootstrap = {
            "complete": True,
            "intervals": {
                "semantic_minus_raw_ap": [0.0, 0.0],
                "raw_minus_semantic_work50": [0.0, 0.0],
            },
            "valid": 1,
            "examined": 1,
            "discarded": 0,
        }
        with tempfile.TemporaryDirectory() as raw_tmp:
            args = SimpleNamespace(
                mode="preflight",
                source=raw_tmp,
                agentpprof_bin=str(AGENTPPROF),
                out=str(Path(raw_tmp) / "out"),
                query_limit=10,
                permutations=200,
                bootstraps=1000,
                max_bootstrap_attempts=5000,
                seed=4204,
                workers=1,
            )
            with (
                mock.patch.object(experiment, "validate_cli_contract"),
                mock.patch.object(
                    experiment,
                    "load_source",
                    return_value=([row], {op_id}, {"source_commit": "fixture"}),
                ),
                mock.patch.object(
                    experiment,
                    "load_external_risks",
                    return_value=({op_id: risk}, {"models": 20}),
                ),
                mock.patch.object(experiment, "construct_profiles", side_effect=profiles),
                mock.patch.object(experiment, "load_human_labels", side_effect=labels),
                mock.patch.object(experiment, "build_states", return_value={}),
                mock.patch.object(
                    experiment,
                    "base_results",
                    return_value={"effects": {}, "per_family": {}, "macro": {}},
                ),
                mock.patch.object(
                    experiment,
                    "run_shuffles",
                    return_value=([], {"p_shuffle": 1.0}),
                ),
                mock.patch.object(
                    experiment, "run_bootstrap", return_value=([], bootstrap)
                ),
                mock.patch.object(
                    experiment, "scientific_verdict", return_value="PREFLIGHT_ONLY"
                ),
                mock.patch.object(experiment, "markdown_report", return_value="# fixture\n"),
            ):
                experiment.run(args)
        self.assertEqual(["profiles", "labels"], order)

    def test_scientific_verdict_uses_only_predeclared_conditions(self) -> None:
        bootstrap = {
            "complete": True,
            "intervals": {
                "semantic_minus_raw_ap": [0.01, 0.08],
                "raw_minus_semantic_work50": [0.02, 0.12],
            },
        }
        self.assertEqual(
            "PREFLIGHT_ONLY",
            experiment.scientific_verdict(
                "preflight", bootstrap, {"p_shuffle": 0.001}
            ),
        )
        self.assertEqual(
            "SUPPORTED",
            experiment.scientific_verdict(
                "full", bootstrap, {"p_shuffle": 0.01}
            ),
        )
        adverse = {
            "complete": True,
            "intervals": {
                "semantic_minus_raw_ap": [-0.08, -0.01],
                "raw_minus_semantic_work50": [-0.02, 0.02],
            },
        }
        self.assertEqual(
            "CONTRADICTED",
            experiment.scientific_verdict(
                "full", adverse, {"p_shuffle": 0.01}
            ),
        )


if __name__ == "__main__":
    unittest.main()
