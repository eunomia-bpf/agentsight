#!/usr/bin/env python3
"""Adversarial tests for the small externally anchored bootstrap."""

from __future__ import annotations

import hashlib
import ast
import errno
import fcntl
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

import postreview_bootstrap as subject


class PostreviewBootstrapTests(unittest.TestCase):
    def test_postreview_chain_has_no_live_project_imports(self) -> None:
        root = Path(__file__).resolve().parent
        forbidden = {
            "prepare_review_bundle",
            "run_analysts",
            "analyze_analyst_efficiency",
            "freeze_rank1_policies",
        }
        for filename in (
            "adjudicate_reviewer_audit.py",
            "run_adjudicated_analysis.py",
            "freeze_adjudicated_rank1_policies.py",
            "verify_postreview_adjudication_contract.py",
        ):
            tree = ast.parse((root / filename).read_bytes())
            imported = {
                alias.name.split(".", 1)[0]
                for node in ast.walk(tree)
                if isinstance(node, ast.Import)
                for alias in node.names
            } | {
                (node.module or "").split(".", 1)[0]
                for node in ast.walk(tree)
                if isinstance(node, ast.ImportFrom)
            }
            self.assertFalse(imported & forbidden, filename)

    def test_stable_contract_read_rejects_mid_read_change(self) -> None:
        path = mock.Mock(spec=Path)
        path.read_bytes.side_effect = [b'{"old":true}', b'{"new":true}']
        with self.assertRaises(subject.BootstrapError):
            subject.load_contract(
                path, hashlib.sha256(b'{"old":true}').hexdigest()
            )

    def test_unknown_script_is_rejected_before_read(self) -> None:
        with self.assertRaises(subject.BootstrapError):
            subject.verified_script_bytes(
                Path("/nonexistent"),
                {"postreview_static_files": {}},
                "../other.py",
                "a" * 64,
            )

    def test_exec_uses_exact_contract_bound_memfd_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            experiment = Path(directory)
            post = experiment / "postreview-adjudication"
            post.mkdir()
            bootstrap = experiment / "postreview_bootstrap.py"
            bootstrap_payload = b"# bootstrap test bytes\n"
            bootstrap.write_bytes(bootstrap_payload)
            script_relative = "run_adjudicated_analysis.py"
            script = experiment / script_relative
            script_payload = b"print('verified')\n"
            script.write_bytes(script_payload)
            bootstrap_hash = hashlib.sha256(bootstrap_payload).hexdigest()
            script_hash = hashlib.sha256(script_payload).hexdigest()
            interpreter = Path(sys.executable).resolve()
            interpreter_hash = hashlib.sha256(
                interpreter.read_bytes()
            ).hexdigest()
            contract_document = {
                "schema": (
                    "agentsight.utility2."
                    "postreview-adjudication-contract.v8"
                ),
                "stage": "postreview-adjudication-attempt-8-pre-analysis",
                "experiment": str(experiment.resolve()),
                "trusted_runtime": {
                    "interpreter_path": str(interpreter),
                    "interpreter_sha256": interpreter_hash,
                    "isolated_flag": True,
                    "no_site_flag": True,
                    "safe_path_flag": True,
                },
                "postreview_static_files": {
                    "postreview_bootstrap.py": bootstrap_hash,
                    script_relative: script_hash,
                },
            }
            contract = post / "frozen-contract.json"
            contract.write_text(
                json.dumps(contract_document), encoding="utf-8"
            )
            contract_hash = hashlib.sha256(contract.read_bytes()).hexdigest()
            with (
                mock.patch.object(subject, "__file__", str(bootstrap)),
                mock.patch.object(subject, "require_isolated_runtime"),
                mock.patch.object(subject.os, "execve") as execve,
            ):
                subject.execute_verified(
                    contract_path=contract,
                    expected_contract_sha256=contract_hash,
                    script_relative=script_relative,
                    expected_script_sha256=script_hash,
                    expected_bootstrap_sha256=bootstrap_hash,
                    expected_interpreter_sha256=interpreter_hash,
                    script_args=["--execute"],
                )
            argv = execve.call_args.args[1]
            self.assertEqual(
                argv[:3], [str(interpreter), "-I", "-S"]
            )
            self.assertTrue(argv[3].startswith("/proc/self/fd/"))
            self.assertEqual(argv[4:], ["--execute"])
            environment = execve.call_args.args[2]
            self.assertEqual(
                set(environment),
                {
                    "AGENTSIGHT_EXPERIMENT_ROOT",
                    "PYTHONDONTWRITEBYTECODE",
                    "PYTHONHASHSEED",
                },
            )

    def test_bootstrap_requires_isolated_no_site_safe_path(self) -> None:
        if (
            sys.flags.isolated == 1
            and sys.flags.no_site == 1
            and sys.flags.safe_path
        ):
            subject.require_isolated_runtime()
        else:
            with self.assertRaises(subject.BootstrapError):
                subject.require_isolated_runtime()

    def test_memfd_is_fully_sealed_and_cannot_be_rewritten(self) -> None:
        descriptor = subject.sealed_memfd(b"verified bytes")
        try:
            seals = fcntl.fcntl(descriptor, fcntl.F_GET_SEALS)
            self.assertEqual(
                seals & subject.REQUIRED_SEALS, subject.REQUIRED_SEALS
            )
            with self.assertRaises(OSError) as raised:
                subject.os.pwrite(descriptor, b"x", 0)
            self.assertIn(raised.exception.errno, {errno.EPERM, errno.EBADF})
        finally:
            subject.os.close(descriptor)


if __name__ == "__main__":
    unittest.main()
