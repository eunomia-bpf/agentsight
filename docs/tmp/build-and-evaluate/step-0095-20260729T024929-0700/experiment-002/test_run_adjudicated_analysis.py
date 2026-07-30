#!/usr/bin/env python3
"""Adversarial tests for anchored snapshot analysis."""

from __future__ import annotations

import copy
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

import freeze_adjudicated_rank1_policies as policy_subject
import run_adjudicated_analysis as subject


class AdjudicatedAnalysisTests(unittest.TestCase):
    def test_launch_literal_carries_external_contract_anchor(self) -> None:
        anchor = "a" * 64
        bootstrap = "b" * 64
        script = "c" * 64
        interpreter = "d" * 64
        command = subject.launch_literal(
            anchor, bootstrap, script, interpreter
        )
        self.assertEqual(
            command[:3],
            [str(Path(sys.executable).resolve()), "-I", "-S"],
        )
        self.assertEqual(
            command[command.index("--expected-contract-sha256") + 1],
            anchor,
        )
        self.assertEqual(
            command[command.index("--output") + 1],
            str(subject.OUTPUT.resolve()),
        )
        self.assertEqual(
            command[command.index("--expected-bootstrap-sha256") + 1],
            bootstrap,
        )
        self.assertEqual(
            command[command.index("--expected-script-sha256") + 1],
            script,
        )
        self.assertEqual(
            command[command.index("--expected-interpreter-sha256") + 1],
            interpreter,
        )

    def test_contract_file_lookup_requires_one_binding(self) -> None:
        contract = {
            "original_contract": {"files": {"a": "1"}},
            "original_runtime_files": {},
            "postreview_static_files": {
                subject.NUMPY_SHIM_RELATIVE: "5" * 64,
                subject.BOOTSTRAP_INDICES_RELATIVE: "6" * 64,
            },
            "adjudication_files": {},
        }
        self.assertEqual(subject.contract_file_hash(contract, "a"), "1")
        contract["original_runtime_files"]["a"] = "2"
        with self.assertRaises(subject.AdjudicatedAnalysisError):
            subject.contract_file_hash(contract, "a")

    def test_sealed_payload_rejects_unregistered_live_input(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source.txt"
            source.write_text("changed", encoding="utf-8")
            expected = hashlib.sha256(b"frozen").hexdigest()
            with self.assertRaises(subject.AdjudicatedAnalysisError):
                subject.SealedPayload.from_live(
                    source, expected, "source.txt"
                )

    def test_transient_path_replace_cannot_change_sealed_consumption(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            virtual = root / "input.json"
            registry = subject.SealedRegistry({})
            try:
                registry.add_generated(
                    virtual, b'{"value":"bound"}', "synthetic"
                )
                virtual.chmod(0o600)
                virtual.write_text(
                    '{"value":"transient"}', encoding="utf-8"
                )
                self.assertEqual(
                    registry.json(virtual), {"value": "bound"}
                )
                virtual.write_text("", encoding="utf-8")
                registry.verify_all()
            finally:
                registry.close()

    def test_frozen_analyzer_imports_contract_bound_numpy_subset(self) -> None:
        payloads = []
        previous_numpy = sys.modules.get("numpy")
        try:
            for path in (
                subject.EXPERIMENT / subject.NUMPY_SHIM_RELATIVE,
                subject.EXPERIMENT / subject.BOOTSTRAP_INDICES_RELATIVE,
                subject.EXPERIMENT / "analyze_analyst_efficiency.py",
            ):
                payloads.append(
                    subject.SealedPayload.from_live(
                        path,
                        subject.sha256_file(path),
                        path.name,
                    )
                )
            shim = subject.load_verified_module(
                payloads[0], "_test_bound_numpy", path.name
            )
            shim.configure_indices(payloads[1].read())
            sys.modules["numpy"] = shim
            analyzer = subject.load_verified_module(
                payloads[2],
                "_test_bound_frozen_analyzer",
                "analyze_analyst_efficiency.py",
            )
            self.assertIs(analyzer.np, shim)
            indices = analyzer.draw_whole_block_indices()
            self.assertEqual(indices.shape, (100_000, 20))
            self.assertEqual(
                hashlib.sha256(indices.tobytes(order="C")).hexdigest(),
                (
                    "5ba4965f21a1250288aab0447beec0300"
                    "f3ed84744a9f34564c98dc7edd7a7ef"
                ),
            )
        finally:
            if previous_numpy is None:
                sys.modules.pop("numpy", None)
            else:
                sys.modules["numpy"] = previous_numpy
            for payload in reversed(payloads):
                payload.close()

    def _projection_fixture(
        self, projection: Path, projected: Path
    ) -> dict:
        return {
            "input_provenance": {
                "schedule": {"path": str(projection / "order.json")},
                "validity_review": {
                    "path": str(
                        projection / "review-run" / "decisions.json"
                    )
                },
                "alias_map": {
                    "path": str(
                        projection / "review-alias-map.private.json"
                    )
                },
                "run_record_sha256_by_run_id": {},
                "review_provenance": {
                    "path": str(projected),
                    "decisions_path": str(
                        projection / "review-run" / "decisions.json"
                    ),
                    "sha256": "x",
                    "frozen_artifacts": {
                        "review_prompt": {
                            "path": str(projection / "review-prompt.txt")
                        },
                        "review_model_contract": {
                            "path": str(
                                projection / "review-model-contract.json"
                            )
                        },
                        "review_command": {
                            "path": str(projection / "review-command.json")
                        },
                        "review_bundle_manifest": {
                            "path": str(
                                projection
                                / "review-bundle"
                                / "manifest.json"
                            )
                        },
                    },
                },
            }
        }

    def _normalization_contract(self) -> dict:
        return {
            "original_contract": {"files": {}},
            "original_runtime_files": {
                "analyst/review-run/run.json": "c" * 64,
                "analyst/order.json": "d" * 64,
                "analyst/review-run/decisions.json": "e" * 64,
                "analyst/review-alias-map.private.json": "f" * 64,
                "analyst/review-prompt.txt": "1" * 64,
                "analyst/review-model-contract.json": "2" * 64,
                "analyst/review-command.json": "3" * 64,
                "analyst/review-bundle/manifest.json": "4" * 64,
            },
            "postreview_static_files": {
                subject.NUMPY_SHIM_RELATIVE: "5" * 64,
                subject.BOOTSTRAP_INDICES_RELATIVE: "6" * 64,
            },
            "adjudication_files": {
                (
                    "postreview-adjudication/adjudication/"
                    "corrected-provenance.json"
                ): "a" * 64,
                "postreview-adjudication/adjudication/report.json": "b" * 64,
            },
        }

    def test_projection_path_is_checked_before_normalization(self) -> None:
        projection = Path("/tmp/example/analyst")
        projected = projection / "review-run" / "run.json"
        fixture = self._projection_fixture(projection, projected)
        contract = self._normalization_contract()
        normalized = subject._normalize_projection_paths(
            copy.deepcopy(fixture), projection, projected, contract
        )
        self.assertTrue(
            normalized["postreview_adjudication"][
                "all_seals_reverified_after_analysis"
            ]
        )
        self.assertEqual(
            normalized["input_provenance"]["schedule"]["sha256"],
            "d" * 64,
        )
        self.assertEqual(
            normalized["input_provenance"]["validity_review"]["sha256"],
            "e" * 64,
        )
        self.assertEqual(
            normalized["input_provenance"]["alias_map"]["sha256"],
            "f" * 64,
        )
        self.assertEqual(
            normalized["input_provenance"]["review_provenance"][
                "frozen_artifacts"
            ]["review_prompt"]["sha256"],
            "1" * 64,
        )
        bad = self._projection_fixture(projection, Path("/tmp/wrong.json"))
        with self.assertRaises(subject.AdjudicatedAnalysisError):
            subject._normalize_projection_paths(
                bad, projection, projected, contract
            )

    def test_two_snapshot_paths_normalize_bit_identically_for_policy(
        self,
    ) -> None:
        contract = self._normalization_contract()
        normalized = []
        for label in ("snapshot-a", "snapshot-b"):
            projection = Path("/tmp") / label / "analyst"
            projected = projection / "review-run" / "run.json"
            fixture = self._projection_fixture(projection, projected)
            fixture["confirmatory_gate"] = {"pass": True}
            fixture["rank_1_policy_gate"] = {"pass": True}
            normalized.append(
                subject._normalize_projection_paths(
                    fixture, projection, projected, contract
                )
            )
        self.assertEqual(normalized[0], normalized[1])
        policy_subject.assert_analysis_admission(
            normalized[0], normalized[1]
        )
        decisions_path = normalized[0]["input_provenance"][
            "review_provenance"
        ]["decisions_path"]
        self.assertEqual(
            decisions_path,
            str(
                (
                    subject.ANALYST
                    / "review-run"
                    / "decisions.json"
                ).resolve()
            ),
        )

    def test_unnamed_inode_publication_is_exact_and_read_only(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "analysis.json"
            expected = {"ours": True, "nested": [1, 2, 3]}
            result = subject.atomic_write_json_noreplace(output, expected)
            payload = output.read_bytes()
            self.assertEqual(json.loads(payload), expected)
            self.assertEqual(hashlib.sha256(payload).hexdigest(), result)
            self.assertEqual(output.stat().st_mode & 0o777, 0o444)

    def test_unnamed_inode_publication_refuses_existing_target(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "analysis.json"
            output.write_text("competitor", encoding="utf-8")
            with self.assertRaises(subject.AdjudicatedAnalysisError):
                subject.atomic_write_json_noreplace(output, {"ours": True})
            self.assertEqual(
                output.read_text(encoding="utf-8"), "competitor"
            )

    def test_directory_path_swap_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            parent = root / "analyst"
            parent.mkdir()
            output = parent / "analysis.json"
            moved = root / "analyst-held"
            real_write_all = subject._write_all

            def swap_after_write(descriptor: int, payload: bytes) -> None:
                real_write_all(descriptor, payload)
                parent.rename(moved)
                parent.mkdir()

            with (
                mock.patch.object(
                    subject, "_write_all", side_effect=swap_after_write
                ),
                self.assertRaises(subject.AdjudicatedAnalysisError),
            ):
                subject.atomic_write_json_noreplace(output, {"ours": True})
            self.assertFalse(output.exists())
            self.assertTrue((moved / "analysis.json").exists())


if __name__ == "__main__":
    unittest.main()
