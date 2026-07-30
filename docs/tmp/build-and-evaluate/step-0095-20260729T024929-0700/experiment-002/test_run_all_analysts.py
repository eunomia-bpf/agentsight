#!/usr/bin/env python3
"""Focused tests for the no-interim analyst batch orchestrator."""

from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

import run_all_analysts as batch
import run_analysts


class BatchOrchestratorTests(unittest.TestCase):
    def test_frozen_batch_command_has_one_entrypoint_and_verification(self) -> None:
        command = batch.batch_command()
        self.assertEqual(command[0], "python3")
        self.assertEqual(command[1], str(batch.Path(__file__).resolve().parent / "run_all_analysts.py"))
        self.assertIn("--execute-batch", command)
        self.assertEqual(
            command[command.index("--contract-verification") + 1],
            str(batch.DEFAULT_VERIFICATION.resolve()),
        )

    def test_runs_all_40_in_position_order_and_accepts_terminal_failures(
        self,
    ) -> None:
        rows = run_analysts.registered_runs()
        with tempfile.TemporaryDirectory() as directory:
            analyst_dir = Path(directory) / "analyst"
            calls: list[str] = []

            def invoke(command: list[str], check: bool) -> object:
                self.assertFalse(check)
                run_id = command[command.index("--execute-run") + 1]
                calls.append(run_id)
                status = (
                    "timeout"
                    if len(calls) == 7
                    else "failed"
                    if len(calls) == 13
                    else "ok"
                )
                path = analyst_dir / "runs" / run_id / "run.json"
                path.parent.mkdir(parents=True)
                path.write_text(
                    json.dumps({"status": status, "do_not_read": {
                        "timing": 123,
                        "usage": 456,
                    }}),
                    encoding="utf-8",
                )
                return object()

            completed = batch._run_batch_rows(
                list(reversed(rows)),
                analyst_dir,
                Path(directory) / "verification.json",
                invoke,
            )
            expected = [
                row["run_id"]
                for row in sorted(rows, key=lambda row: row["position"])
            ]
            self.assertEqual(calls, expected)
            self.assertEqual(completed, expected)

    def test_hard_stops_on_missing_or_nonterminal_record(self) -> None:
        rows = run_analysts.registered_runs()
        with tempfile.TemporaryDirectory() as directory:
            analyst_dir = Path(directory) / "analyst"
            with self.assertRaises(batch.BatchRunError):
                batch._run_batch_rows(
                    rows,
                    analyst_dir,
                    Path(directory) / "verification.json",
                    lambda command, check: object(),
                )
            self.assertFalse((analyst_dir / "batch-run.json").exists())

        with tempfile.TemporaryDirectory() as directory:
            analyst_dir = Path(directory) / "analyst"

            def nonterminal(command: list[str], check: bool) -> object:
                run_id = command[command.index("--execute-run") + 1]
                path = analyst_dir / "runs" / run_id / "run.json"
                path.parent.mkdir(parents=True)
                path.write_text(
                    json.dumps({"status": "running"}), encoding="utf-8"
                )
                return object()

            with self.assertRaises(batch.BatchRunError):
                batch._run_batch_rows(
                    rows,
                    analyst_dir,
                    Path(directory) / "verification.json",
                    nonterminal,
                )

    def test_child_command_contains_only_registered_run_and_frozen_gate(
        self,
    ) -> None:
        path = Path("/tmp/frozen-verification.json")
        command = batch.child_command("run-opaque", path)
        self.assertEqual(
            command,
            [
                "python3",
                str(batch.RUNNER.resolve()),
                "--execute-run",
                "run-opaque",
                "--contract-verification",
                str(path.resolve()),
            ],
        )


if __name__ == "__main__":
    unittest.main()
