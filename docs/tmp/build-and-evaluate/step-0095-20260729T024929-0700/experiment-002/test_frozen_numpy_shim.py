#!/usr/bin/env python3
"""Synthetic equivalence tests for the contract-bound NumPy subset."""

from __future__ import annotations

import ast
import hashlib
import importlib.util
import math
from pathlib import Path
import unittest

import numpy as real_numpy


ROOT = Path(__file__).resolve().parent
SHIM_PATH = ROOT / "frozen_numpy_shim.py"
INDICES_PATH = (
    ROOT / "bootstrap-indices-pcg64-seed2026072903-i8le.bin"
)
EXPECTED_INDICES_SHA256 = (
    "5ba4965f21a1250288aab0447beec0300"
    "f3ed84744a9f34564c98dc7edd7a7ef"
)


def load_shim():
    specification = importlib.util.spec_from_file_location(
        "_test_frozen_numpy_shim", SHIM_PATH
    )
    if specification is None or specification.loader is None:
        raise RuntimeError("cannot load frozen NumPy shim")
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    module.configure_indices(INDICES_PATH.read_bytes())
    return module


class FrozenNumpyShimTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.shim = load_shim()

    def test_frozen_indices_exactly_match_real_numpy_pcg64(self) -> None:
        payload = INDICES_PATH.read_bytes()
        self.assertEqual(
            hashlib.sha256(payload).hexdigest(),
            EXPECTED_INDICES_SHA256,
        )
        expected = real_numpy.random.Generator(
            real_numpy.random.PCG64(2026072903)
        ).integers(
            0,
            20,
            size=(100_000, 20),
            dtype=real_numpy.int64,
        )
        actual = self.shim.random.Generator(
            self.shim.random.PCG64(2026072903)
        ).integers(
            0,
            20,
            size=(100_000, 20),
            dtype=self.shim.int64,
        )
        self.assertEqual(actual.shape, expected.shape)
        self.assertEqual(actual.tobytes(order="C"), payload)
        self.assertEqual(
            actual.tobytes(order="C"),
            expected.astype("<i8", copy=False).tobytes(order="C"),
        )

    def test_one_dimensional_operations_match_real_numpy(self) -> None:
        values = [
            0.125,
            17.0,
            3.5,
            3.5,
            91.25,
            0.75,
            8.0,
            2.25,
            33.0,
            1.125,
            6.75,
            0.5,
            11.0,
            4.125,
            55.0,
            0.25,
            23.5,
            5.25,
            13.0,
            2.0,
        ]
        actual = self.shim.asarray(values, dtype=self.shim.float64)
        expected = real_numpy.asarray(values, dtype=real_numpy.float64)
        self.assertEqual(actual.ndim, expected.ndim)
        self.assertEqual(actual.size, expected.size)
        self.assertEqual(actual.shape, expected.shape)
        self.assertEqual(
            list(self.shim.sort(actual, kind="stable")),
            list(real_numpy.sort(expected, kind="stable")),
        )
        self.assertEqual(
            self.shim.median(actual),
            float(real_numpy.median(expected)),
        )
        self.assertEqual(
            self.shim.mean(actual),
            float(real_numpy.mean(expected)),
        )
        self.assertEqual(
            list(self.shim.log(actual)),
            list(real_numpy.log(expected)),
        )
        self.assertEqual(
            self.shim.all(self.shim.isfinite(actual)),
            bool(real_numpy.all(real_numpy.isfinite(expected))),
        )
        self.assertEqual(
            self.shim.any(actual <= 1.0),
            bool(real_numpy.any(expected <= 1.0)),
        )
        self.assertEqual(
            list(actual / 2.5),
            list(expected / 2.5),
        )
        self.assertEqual(
            self.shim.exp(math.log(7.25)),
            float(real_numpy.exp(real_numpy.log(7.25))),
        )

    def test_full_bootstrap_medians_match_real_numpy(self) -> None:
        source_values = [
            math.log(value)
            for value in (
                0.51,
                0.63,
                0.71,
                0.79,
                0.83,
                0.88,
                0.91,
                0.94,
                0.97,
                0.99,
                1.01,
                1.04,
                1.08,
                1.12,
                1.17,
                1.23,
                1.31,
                1.42,
                1.57,
                1.81,
            )
        ]
        payload = INDICES_PATH.read_bytes()
        expected_indices = real_numpy.frombuffer(
            payload, dtype="<i8"
        ).reshape((100_000, 20))
        expected_source = real_numpy.asarray(
            source_values, dtype=real_numpy.float64
        )
        expected = real_numpy.median(
            expected_source[expected_indices], axis=1
        )

        actual_indices = self.shim.random.Generator(
            self.shim.random.PCG64(2026072903)
        ).integers(
            0,
            20,
            size=(100_000, 20),
            dtype=self.shim.int64,
        )
        actual_source = self.shim.asarray(
            source_values, dtype=self.shim.float64
        )
        actual = self.shim.median(
            actual_source[actual_indices], axis=1
        )
        self.assertEqual(actual.shape, expected.shape)
        self.assertEqual(list(actual), list(expected))

    def test_frozen_descriptor_rejects_other_draws(self) -> None:
        with self.assertRaises(ValueError):
            self.shim.random.PCG64(0)
        generator = self.shim.random.Generator(
            self.shim.random.PCG64(2026072903)
        )
        with self.assertRaises(ValueError):
            generator.integers(
                0,
                19,
                size=(100_000, 20),
                dtype=self.shim.int64,
            )

    def test_arithmetic_mean_is_descriptive_only_not_a_gate_input(
        self,
    ) -> None:
        tree = ast.parse(
            (ROOT / "analyze_analyst_efficiency.py").read_bytes()
        )
        functions = {
            node.name: node
            for node in tree.body
            if isinstance(node, ast.FunctionDef)
        }
        attribute_mean_callers = {
            name
            for name, function in functions.items()
            if any(
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and node.func.attr == "mean"
                for node in ast.walk(function)
            )
        }
        self.assertEqual(
            attribute_mean_callers, {"_mean", "_stratum_descriptive"}
        )
        direct_mean_callers = {
            name
            for name, function in functions.items()
            if any(
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Name)
                and node.func.id == "_mean"
                for node in ast.walk(function)
            )
        }
        self.assertEqual(
            direct_mean_callers, {"_arm_descriptive", "analyze"}
        )

        analyze_function = functions["analyze"]
        return_nodes = [
            node
            for node in ast.walk(analyze_function)
            if isinstance(node, ast.Return)
            and isinstance(node.value, ast.Dict)
        ]
        self.assertEqual(len(return_nodes), 1)
        returned = return_nodes[0].value
        top_level = {
            key.value: value
            for key, value in zip(returned.keys, returned.values)
            if isinstance(key, ast.Constant)
            and isinstance(key.value, str)
        }
        descriptive_calls = {
            node.func.id
            for node in ast.walk(top_level["descriptive"])
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id
            in {"_mean", "_arm_descriptive", "_stratum_descriptive"}
        }
        all_analyze_descriptive_calls = {
            node.func.id
            for node in ast.walk(analyze_function)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id
            in {"_mean", "_arm_descriptive", "_stratum_descriptive"}
        }
        self.assertEqual(
            descriptive_calls,
            {"_mean", "_arm_descriptive", "_stratum_descriptive"},
        )
        self.assertEqual(
            all_analyze_descriptive_calls, descriptive_calls
        )
        for gate in (
            "confirmatory_gate",
            "rank_1_policy_gate",
            "downstream_readiness",
        ):
            self.assertFalse(
                any(
                    (
                        isinstance(node, ast.Name)
                        and node.id
                        in {
                            "_mean",
                            "_arm_descriptive",
                            "_stratum_descriptive",
                        }
                    )
                    or (
                        isinstance(node, ast.Attribute)
                        and node.attr == "mean"
                    )
                    for node in ast.walk(top_level[gate])
                ),
                gate,
            )


if __name__ == "__main__":
    unittest.main()
