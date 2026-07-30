#!/usr/bin/env python3
"""Adversarial tests for the external contract trust anchor."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

import verify_postreview_adjudication_contract as subject


class PostreviewContractTests(unittest.TestCase):
    def test_payload_cache_hash_and_parse_use_one_immutable_payload(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "value.json"
            path.write_text('{"version":"bound"}', encoding="utf-8")
            cache = subject.PayloadCache()
            expected = cache.sha256(path)
            path.write_text('{"version":"transient"}', encoding="utf-8")
            self.assertEqual(cache.json(path), {"version": "bound"})
            self.assertEqual(cache.sha256(path), expected)

    def test_hash_map_rejects_hash_and_file_set_drift(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            target = root / "value.txt"
            target.write_text("frozen", encoding="utf-8")
            registered = {
                "value.txt": hashlib.sha256(target.read_bytes()).hexdigest()
            }
            with mock.patch.object(subject, "EXPERIMENT", root):
                subject._verify_hash_map(
                    registered,
                    ("value.txt",),
                    subject.PayloadCache(),
                    label="test",
                )
                target.write_text("changed", encoding="utf-8")
                with self.assertRaises(subject.PostreviewContractError):
                    subject._verify_hash_map(
                        registered,
                        ("value.txt",),
                        subject.PayloadCache(),
                        label="test",
                    )
                with self.assertRaises(subject.PostreviewContractError):
                    subject._verify_hash_map(
                        registered,
                        ("value.txt", "extra"),
                        subject.PayloadCache(),
                        label="test",
                    )

    def test_external_anchor_rejects_synchronized_contract_rewrite(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            contract = Path(directory) / "contract.json"
            contract.write_text('{"changed": true}\n', encoding="utf-8")
            old_anchor = hashlib.sha256(b'{"old": true}\n').hexdigest()
            with (
                mock.patch.object(subject, "CONTRACT", contract),
                self.assertRaises(subject.PostreviewContractError),
            ):
                subject.verify_contract(contract, None, old_anchor)

    def test_contract_parse_and_hash_use_same_bytes_with_end_recheck(
        self,
    ) -> None:
        bindings = {
            "original_contract": {},
            "original_runtime_files": {},
            "postreview_static_files": {},
            "adjudication_files": {},
            "rejected_attempt_archives": {},
            "trusted_runtime": {},
            "semantics": {},
        }
        document = {
            "schema": (
                "agentsight.utility2."
                "postreview-adjudication-contract.v8"
            ),
            "stage": "postreview-adjudication-attempt-8-pre-analysis",
            "created_at": "test",
            "experiment": str(subject.EXPERIMENT.resolve()),
            "analysis_absent_at_creation": True,
            "policies_absent_at_creation": True,
            **bindings,
        }
        payload = json.dumps(document).encode("utf-8")
        anchor = hashlib.sha256(payload).hexdigest()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "contract.json"
            with (
                mock.patch.object(subject, "CONTRACT", path),
                mock.patch.object(
                    subject, "_current_bindings", return_value=bindings
                ),
                mock.patch.object(
                    Path,
                    "read_bytes",
                    side_effect=[payload, payload + b" "],
                ),
                self.assertRaises(subject.PostreviewContractError),
            ):
                subject.verify_contract(path, None, anchor)

    def test_exact_contract_field_set_rejects_extra_key(self) -> None:
        minimum = {field: None for field in subject.CONTRACT_FIELDS}
        self.assertEqual(set(minimum), subject.CONTRACT_FIELDS)
        minimum["extra"] = True
        self.assertNotEqual(set(minimum), subject.CONTRACT_FIELDS)

    def test_creation_rejects_analysis_or_policy_presence(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            analysis = root / "analysis.json"
            policies = root / "policies"
            with (
                mock.patch.object(subject, "ANALYSIS_OUTPUT", analysis),
                mock.patch.object(subject, "POLICIES_OUTPUT", policies),
            ):
                subject._assert_downstream_absent_for_creation()
                analysis.write_text("{}", encoding="utf-8")
                with self.assertRaises(subject.PostreviewContractError):
                    subject._assert_downstream_absent_for_creation()
                analysis.unlink()
                policies.mkdir()
                with self.assertRaises(subject.PostreviewContractError):
                    subject._assert_downstream_absent_for_creation()

    def test_creation_literal_uses_absolute_isolated_interpreter(self) -> None:
        self.assertEqual(
            subject.create_literal()[:3],
            [str(Path(sys.executable).resolve()), "-I", "-S"],
        )


if __name__ == "__main__":
    unittest.main()
