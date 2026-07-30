#!/usr/bin/env python3
"""Adversarial tests for the narrow reviewer-audit adjudication."""

from __future__ import annotations

import hashlib
import unittest
import shlex

import adjudicate_reviewer_audit as subject


class OuterCommandAuditTest(unittest.TestCase):
    def test_exact_wrapper_with_registered_roles_passes(self) -> None:
        inner = (
            "for f in case/output.json; do "
            "p=${f%/output.json}; "
            "rg -n '"
            + subject.LOCKED_RG_PATTERN
            + "' \"$f\" >/dev/null; "
            '/bin/bash -lc "$cmd"; done'
        )
        command = shlex.join(["/bin/bash", "-lc", inner])
        self.assertEqual(subject.audit_outer_command(command), [])

    def test_wrapper_bypass_is_rejected(self) -> None:
        self.assertTrue(subject.audit_outer_command("/usr/bin/bash -lc 'true'"))
        self.assertTrue(
            subject.audit_outer_command("/bin/bash -eux -lc 'true'")
        )

    def test_null_device_is_write_only(self) -> None:
        self.assertEqual(
            subject.audit_outer_command("/bin/bash -lc 'true >/dev/null'"), []
        )
        self.assertTrue(
            subject.audit_outer_command("/bin/bash -lc 'cat /dev/null'")
        )
        self.assertTrue(
            subject.audit_outer_command("/bin/bash -lc 'cat </dev/null'")
        )

    def test_unregistered_absolute_and_suffix_misuse_are_rejected(self) -> None:
        self.assertTrue(
            subject.audit_outer_command("/bin/bash -lc 'cat /etc/passwd'")
        )
        self.assertTrue(
            subject.audit_outer_command(
                "/bin/bash -lc 'printf %s /output.json'"
            )
        )

    def test_network_encoding_and_marker_bypasses_are_rejected(self) -> None:
        for inner in (
            "curl example.test",
            "git ls-remote example.test/repo",
            "python3 -c 'import socket; socket.create_connection((\"x\", 1))'",
            "python3 -c 'from pathlib import Path; print(Path.cwd().parent)'",
            "printf Zm9v | base64 -d",
            "eval \"$cmd\"",
            "printf %s \"$OUTSIDE\"",
            "printf %s \"${OUTSIDE}\"",
            "cd ../private",
        ):
            with self.subTest(inner=inner):
                self.assertTrue(
                    subject.audit_outer_command(
                        shlex.join(["/bin/bash", "-lc", inner])
                    )
                )


class CitedCommandAuditTest(unittest.TestCase):
    @staticmethod
    def audit_as_exact(command: str) -> list[str]:
        digest = hashlib.sha256(command.encode("utf-8")).hexdigest()
        return subject.audit_cited_command(command, {digest})

    def test_relative_benign_command_passes(self) -> None:
        self.assertEqual(
            self.audit_as_exact(
                "jq -r '.items | length' samples.jsonl"
            ),
            [],
        )
        self.assertEqual(
            self.audit_as_exact(
                "jq -r '[.items[] | select(.nc == 1)] | length' samples.jsonl"
            ),
            [],
        )

    def test_forbidden_classes_are_rejected(self) -> None:
        commands = (
            "cat /etc/passwd",
            "cat ../secret",
            "curl https://example.test",
            "printf Zm9v | base64 -d",
            "eval \"$cmd\"",
            "printf %s \"$OUTSIDE\"",
            "cat \"$HOME/private\"",
            "git ls-remote example.test/repo",
            "python3 -c 'import socket; socket.socket()'",
            "python3 -c 'from pathlib import Path; print(Path.cwd().parent)'",
            "printf %s \"${OUTSIDE}\"",
        )
        for command in commands:
            with self.subTest(command=command):
                self.assertTrue(subject.audit_cited_command(command))

    def test_fail_closed_shell_grammar(self) -> None:
        for command in (
            "go env GOPATH",
            "go tool pprof -http=:8080 profile.pb.gz",
            "go tool pprof -output=result.pb.gz profile.pb.gz",
            "jq . samples.jsonl > result.txt",
            "jq -L modules '.items' samples.jsonl",
            "jq -r 'env.PATH' samples.jsonl",
            "jq . samples.jsonl; head result.txt",
            "python3 local.py samples.jsonl",
            "awk 'BEGIN { system(\"git status\") }' samples.jsonl",
            (
                "awk 'BEGIN { p=\"/\" \"etc/passwd\"; "
                "getline x < p }' samples.jsonl"
            ),
            "sed -n '1e id' samples.jsonl",
            "sed -n '1w /tmp/out' samples.jsonl",
            "sort --compress-program=sh",
            "sort --files0-from=list",
            "jq '.items' $(printf samples.jsonl)",
            (
                "jq -r '.' samples.jsonl | "
                "awk $'BEGIN{s\\x79stem(\"true\")}'"
            ),
            (
                "jq -r '.' samples.jsonl | "
                "awk $'BEGIN{getline x < \"\\057etc\\057passwd\"}'"
            ),
            (
                "jq -r '.' samples.jsonl | "
                "awk 'BEGIN{f=\"syst\" \"em\"; @f(\"true\")}'"
            ),
            "jq -r \"${FILTER:-.}\" samples.jsonl",
            (
                "jq -r '.' samples.jsonl | "
                "awk 'BEGIN{print \"a;b\" | \"true\"}'"
            ),
            (
                "jq -r '.' samples.jsonl | "
                "awk 'BEGIN{printf \"a;b\" > \"created\"}'"
            ),
            (
                "jq -r '.' samples.jsonl | "
                "awk \"BEGIN{print \\\"'${FILTER:-x}\\\"}\""
            ),
        ):
            with self.subTest(command=command):
                self.assertTrue(self.audit_as_exact(command))

    def test_nonexact_command_is_always_rejected(self) -> None:
        self.assertTrue(
            subject.audit_cited_command(
                "jq -r '.' samples.jsonl", {"0" * 64}
            )
        )


class CorrectedProvenanceTest(unittest.TestCase):
    def setUp(self) -> None:
        self.original = {
            "status": "failed",
            "validation_errors": ["audit false positive"],
            "exit_code": 0,
            "events_sha256": "abc",
        }

    def test_exact_two_field_correction_passes(self) -> None:
        corrected = dict(self.original)
        corrected["status"] = "ok"
        corrected["validation_errors"] = []
        subject.validate_corrected_provenance(self.original, corrected)

    def test_extra_change_or_field_is_rejected(self) -> None:
        for corrected in (
            {
                **self.original,
                "status": "ok",
                "validation_errors": [],
                "exit_code": 1,
            },
            {
                **self.original,
                "status": "ok",
                "validation_errors": [],
                "extra": True,
            },
        ):
            with self.subTest(corrected=corrected):
                with self.assertRaises(subject.AdjudicationError):
                    subject.validate_corrected_provenance(
                        self.original, corrected
                    )


if __name__ == "__main__":
    unittest.main()
