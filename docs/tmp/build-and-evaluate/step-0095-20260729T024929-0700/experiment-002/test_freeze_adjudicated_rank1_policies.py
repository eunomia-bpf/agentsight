#!/usr/bin/env python3
"""Adversarial tests for anchored snapshot policy freezing."""

from __future__ import annotations

from pathlib import Path
import hashlib
import sys
import tempfile
import unittest
from unittest import mock

import freeze_adjudicated_rank1_policies as subject


class AdjudicatedPolicyFreezeTests(unittest.TestCase):
    def test_launch_literal_carries_external_contract_anchor(self) -> None:
        anchor = "b" * 64
        bootstrap = "c" * 64
        script = "d" * 64
        interpreter = "e" * 64
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
            command[command.index("--analysis") + 1],
            str(subject.ANALYSIS.resolve()),
        )
        self.assertEqual(
            command[command.index("--expected-bootstrap-sha256") + 1],
            bootstrap,
        )
        self.assertEqual(
            command[command.index("--expected-interpreter-sha256") + 1],
            interpreter,
        )

    def test_atomic_directory_reservation_refuses_existing_output(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            policies = Path(directory) / "policies"
            policies.mkdir()
            marker = policies / "owner.txt"
            marker.write_text("competitor", encoding="utf-8")
            with (
                mock.patch.object(subject, "POLICIES", policies),
                self.assertRaises(subject.AdjudicatedPolicyFreezeError),
            ):
                subject.write_policy_artifacts_exclusive({}, {})
            self.assertEqual(marker.read_text(encoding="utf-8"), "competitor")

    def test_exclusive_writer_preserves_exact_rank1_text(self) -> None:
        selected = {
            arm: {
                "run_id": f"run-{arm}",
                "policy_text": f"Exact {arm} policy.",
                "word_count": 3,
                "run_record_sha256": "a" * 64,
                "final_sha256": "b" * 64,
            }
            for arm in subject.POLICY_FILES
        }
        with tempfile.TemporaryDirectory() as directory:
            policies = Path(directory) / "policies"
            with mock.patch.object(subject, "POLICIES", policies):
                manifest = subject.write_policy_artifacts_exclusive(
                    selected, {"snapshot": True}
                )
            self.assertTrue(manifest["atomic_final_symlink_publication"])
            self.assertTrue(manifest["manifest_committed_last"])
            self.assertTrue(policies.is_symlink())
            self.assertTrue(policies.is_dir())
            self.assertEqual(policies.stat().st_mode & 0o777, 0o555)
            for arm, filename in subject.POLICY_FILES.items():
                self.assertEqual(
                    (policies / filename).read_text(encoding="utf-8"),
                    selected[arm]["policy_text"],
                )
                self.assertEqual(
                    (policies / filename).stat().st_mode & 0o777, 0o444
                )
            self.assertEqual(
                (policies / "manifest.json").stat().st_mode & 0o777,
                0o444,
            )

    def test_public_name_is_never_opened_before_atomic_symlink_publish(
        self,
    ) -> None:
        selected = {
            arm: {
                "run_id": f"run-{arm}",
                "policy_text": f"Exact {arm} policy.",
                "word_count": 3,
                "run_record_sha256": "a" * 64,
                "final_sha256": "b" * 64,
            }
            for arm in subject.POLICY_FILES
        }
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            policies = root / "policies"
            real_open = subject.os.open
            real_mkdir = subject.os.mkdir
            prepublication_public_opens = []
            mkdir_names = []

            def traced_open(path, *args, **kwargs):
                if (
                    path == policies.name
                    and not policies.is_symlink()
                ):
                    prepublication_public_opens.append(path)
                return real_open(path, *args, **kwargs)

            def traced_mkdir(path, *args, **kwargs):
                mkdir_names.append(path)
                return real_mkdir(path, *args, **kwargs)

            with (
                mock.patch.object(subject, "POLICIES", policies),
                mock.patch.object(
                    subject.os, "open", side_effect=traced_open
                ),
                mock.patch.object(
                    subject.os, "mkdir", side_effect=traced_mkdir
                ),
            ):
                subject.write_policy_artifacts_exclusive(
                    selected, {"snapshot": True}
                )
            self.assertEqual(prepublication_public_opens, [])
            self.assertNotIn(policies.name, mkdir_names)
            self.assertTrue(policies.is_symlink())

    def test_private_held_directory_path_swap_fails_closed(self) -> None:
        selected = {
            arm: {
                "run_id": f"run-{arm}",
                "policy_text": f"Exact {arm} policy.",
                "word_count": 3,
                "run_record_sha256": "a" * 64,
                "final_sha256": "b" * 64,
            }
            for arm in subject.POLICY_FILES
        }
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            policies = root / "policies"
            moved = root / "private-held"
            real_writer = subject._write_policy_file_at
            call_count = 0

            def swap_after_first_file(*args, **kwargs):
                nonlocal call_count
                result = real_writer(*args, **kwargs)
                call_count += 1
                if call_count == 1:
                    held = subject.os.fstat(args[0])
                    candidates = [
                        path
                        for path in root.iterdir()
                        if path.name.startswith(".policies.store-")
                        and path.stat().st_ino == held.st_ino
                    ]
                    self.assertEqual(len(candidates), 1)
                    private = candidates[0]
                    private.rename(moved)
                    private.mkdir()
                return result

            with (
                mock.patch.object(subject, "POLICIES", policies),
                mock.patch.object(
                    subject,
                    "_write_policy_file_at",
                    side_effect=swap_after_first_file,
                ),
                self.assertRaises(subject.AdjudicatedPolicyFreezeError),
            ):
                subject.write_policy_artifacts_exclusive(
                    selected, {"snapshot": True}
                )
            self.assertFalse(policies.exists())
            self.assertFalse(policies.is_symlink())
            self.assertTrue((moved / "manifest.json").exists())

    def test_public_name_competitor_wins_without_overwrite(self) -> None:
        selected = {
            arm: {
                "run_id": f"run-{arm}",
                "policy_text": f"Exact {arm} policy.",
                "word_count": 3,
                "run_record_sha256": "a" * 64,
                "final_sha256": "b" * 64,
            }
            for arm in subject.POLICY_FILES
        }
        with tempfile.TemporaryDirectory() as directory:
            policies = Path(directory) / "policies"
            real_symlink = subject.os.symlink

            def competitor_before_publish(
                source, target, *, dir_fd=None
            ):
                subject.os.mkdir(target, 0o700, dir_fd=dir_fd)
                return real_symlink(
                    source, target, dir_fd=dir_fd
                )

            with (
                mock.patch.object(subject, "POLICIES", policies),
                mock.patch.object(
                    subject.os,
                    "symlink",
                    side_effect=competitor_before_publish,
                ),
                self.assertRaises(subject.AdjudicatedPolicyFreezeError),
            ):
                subject.write_policy_artifacts_exclusive(
                    selected, {"snapshot": True}
                )
            self.assertTrue(policies.is_dir())
            self.assertFalse(policies.is_symlink())
            self.assertEqual(list(policies.iterdir()), [])

    def test_review7_seventh_fd_read_symlink_swap_fails_closed(
        self,
    ) -> None:
        selected = {
            arm: {
                "run_id": f"run-{arm}",
                "policy_text": f"Exact {arm} policy.",
                "word_count": 3,
                "run_record_sha256": "a" * 64,
                "final_sha256": "b" * 64,
            }
            for arm in subject.POLICY_FILES
        }
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            policies = root / "policies"
            competitor = root / "competitor"
            competitor.mkdir()
            real_reader = subject._read_policy_fd
            read_count = 0

            def swap_on_seventh_read(descriptor: int) -> bytes:
                nonlocal read_count
                read_count += 1
                if read_count == 7:
                    policies.unlink()
                    policies.symlink_to(
                        competitor.name, target_is_directory=True
                    )
                return real_reader(descriptor)

            with (
                mock.patch.object(subject, "POLICIES", policies),
                mock.patch.object(
                    subject,
                    "_read_policy_fd",
                    side_effect=swap_on_seventh_read,
                ),
                self.assertRaises(subject.AdjudicatedPolicyFreezeError),
            ):
                subject.write_policy_artifacts_exclusive(
                    selected, {"snapshot": True}
                )
            self.assertGreaterEqual(read_count, 7)
            self.assertEqual(
                policies.readlink(), Path(competitor.name)
            )

    def test_consumer_revalidation_rejects_postpublication_swap(
        self,
    ) -> None:
        selected = {
            arm: {
                "run_id": f"run-{arm}",
                "policy_text": f"Exact {arm} policy.",
                "word_count": 3,
                "run_record_sha256": "a" * 64,
                "final_sha256": "b" * 64,
            }
            for arm in subject.POLICY_FILES
        }
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            policies = root / "policies"
            with mock.patch.object(subject, "POLICIES", policies):
                manifest = subject.write_policy_artifacts_exclusive(
                    selected, {"snapshot": True}
                )
            self.assertEqual(
                subject.validate_published_policy_bundle(
                    policies, manifest
                ),
                manifest,
            )
            original_store = policies.resolve()
            competitor = root / "competitor"
            competitor.mkdir()
            for source in original_store.iterdir():
                (competitor / source.name).write_bytes(
                    source.read_bytes()
                )
                (competitor / source.name).chmod(
                    source.stat().st_mode & 0o777
                )
            competitor.chmod(0o555)
            policies.unlink()
            policies.symlink_to(
                competitor.name, target_is_directory=True
            )
            with self.assertRaises(
                subject.AdjudicatedPolicyFreezeError
            ):
                subject.validate_published_policy_bundle(
                    policies, manifest
                )

    def test_registered_analysis_payload_is_independent_of_live_drift(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            analysis = Path(directory) / "analysis.json"
            analysis.write_text("version-a", encoding="utf-8")
            registered = subject.read_regular_file_once(analysis)
            expected = hashlib.sha256(registered).hexdigest()
            analysis.write_text("version-b", encoding="utf-8")
            self.assertEqual(
                hashlib.sha256(registered).hexdigest(), expected
            )
            self.assertNotEqual(
                hashlib.sha256(analysis.read_bytes()).hexdigest(), expected
            )

    def test_policy_publication_does_not_reopen_live_analysis(self) -> None:
        selected = {
            arm: {
                "run_id": f"run-{arm}",
                "policy_text": f"Sealed {arm} policy.",
                "word_count": 3,
                "run_record_sha256": "a" * 64,
                "final_sha256": "b" * 64,
            }
            for arm in subject.POLICY_FILES
        }
        with tempfile.TemporaryDirectory() as directory:
            policies = Path(directory) / "policies"
            nonexistent = Path(directory) / "missing-analysis.json"
            with (
                mock.patch.object(subject, "POLICIES", policies),
                mock.patch.object(subject, "ANALYSIS", nonexistent),
            ):
                manifest = subject.write_policy_artifacts_exclusive(
                    selected,
                    {
                        "analysis": {
                            "sha256": "c" * 64,
                            "consumed_from_fully_sealed_memfd": True,
                        }
                    },
                )
            self.assertEqual(
                manifest["bindings"]["analysis"]["sha256"], "c" * 64
            )


if __name__ == "__main__":
    unittest.main()
