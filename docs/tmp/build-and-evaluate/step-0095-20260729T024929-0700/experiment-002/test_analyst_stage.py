#!/usr/bin/env python3
"""Focused tests for the fresh experiment-002 analyst stage."""

from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

import run_analysts as runner
import verify_analyst_packages as packages
import verify_frozen_contract as contract


class AnalystStageTests(unittest.TestCase):
    def test_packages_are_exact_and_information_matched(self) -> None:
        report = packages.verify_packages()
        self.assertEqual(report["status"], "PASS")
        self.assertEqual(
            report["tuple_equivalence"]["profile_tuple_count"], 11_146
        )
        self.assertEqual(
            report["tuple_equivalence"]["profile_unique_tuple_count"], 7_229
        )
        self.assertTrue(
            report["tuple_equivalence"]["complete_multiset_equal"]
        )
        self.assertTrue(report["mass_conservation"]["equal"])

    def test_schedule_is_deterministic_paired_and_exactly_balanced(self) -> None:
        first = runner.registered_runs()
        second = runner.registered_runs()
        self.assertEqual(first, second)
        self.assertEqual(len(first), 40)
        self.assertEqual(len({row["run_id"] for row in first}), 40)
        profile_first = 0
        raw_first = 0
        for block_index in range(1, 21):
            block = [
                row for row in first if row["block_index"] == block_index
            ]
            self.assertEqual(len(block), 2)
            self.assertEqual(
                {row["arm"] for row in block},
                {"PROFILE", "RAW-OPERATIONS"},
            )
            self.assertEqual(
                sorted(row["within_block_order"] for row in block), [1, 2]
            )
            self.assertEqual({row["arm_rank"] for row in block}, {block_index})
            first_arm = next(
                row["arm"] for row in block if row["within_block_order"] == 1
            )
            profile_first += first_arm == "PROFILE"
            raw_first += first_arm == "RAW-OPERATIONS"
        self.assertEqual((profile_first, raw_first), (10, 10))
        for arm in runner.PACKAGES:
            self.assertEqual(
                sorted(row["arm_rank"] for row in first if row["arm"] == arm),
                list(range(1, 21)),
            )

    def test_prompts_share_task_and_contain_no_downstream_literal(self) -> None:
        profile = runner.prompt_for("PROFILE")
        raw = runner.prompt_for("RAW-OPERATIONS")
        self.assertTrue(profile.startswith(runner.COMMON_TASK))
        self.assertTrue(raw.startswith(runner.COMMON_TASK))
        self.assertEqual(
            profile.removesuffix(runner.FORMAT_HINTS["PROFILE"]),
            raw.removesuffix(runner.FORMAT_HINTS["RAW-OPERATIONS"]),
        )
        self.assertNotIn("ToolSandbox", profile)
        self.assertNotIn("ToolSandbox", raw)

    def test_commands_freeze_model_timeout_and_run_metadata_fields(self) -> None:
        for run in runner.registered_runs():
            command = runner.command_for(run)
            self.assertEqual(command[:3], ["timeout", "900", "codex"])
            self.assertEqual(command[command.index("--model") + 1], "gpt-5.6-sol")
            self.assertEqual(command[command.index("--sandbox") + 1], "read-only")
            self.assertEqual(
                {
                    "run_id",
                    "arm",
                    "block_id",
                    "within_block_order",
                    "arm_rank",
                }
                - set(run),
                set(),
            )

    def test_review_aliases_are_complete_bijection_and_public_schema_is_blind(
        self,
    ) -> None:
        runs = runner.registered_runs()
        mapping = runner.review_alias_assignment(runs)
        mapping_again = runner.review_alias_assignment(runs)
        self.assertEqual(mapping, mapping_again)
        cases = mapping["cases"]
        self.assertEqual(len({case["case_id"] for case in cases}), 40)
        self.assertEqual(
            {case["run_id"] for case in cases},
            {run["run_id"] for run in runs},
        )
        schema = runner.review_output_schema(
            [case["case_id"] for case in cases]
        )
        public_fields = set(
            schema["properties"]["cases"]["items"]["properties"]
        )
        self.assertEqual(
            public_fields,
            {"case_id", *runner.REVIEW_DECISION_FIELDS},
        )
        self.assertTrue(
            public_fields.isdisjoint(
                {
                    "run_id",
                    "arm",
                    "timing",
                    "usage",
                    "schedule_position",
                    "within_block_order",
                    "arm_rank",
                }
            )
        )

    def test_frozen_order_rejects_skip_and_accepts_terminal_predecessor(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            analyst_dir = Path(directory)
            order = {
                "runs": [
                    {"run_id": "first", "position": 1},
                    {"run_id": "second", "position": 2},
                ]
            }
            (analyst_dir / "order.json").write_text(
                json.dumps(order), encoding="utf-8"
            )
            with self.assertRaises(RuntimeError):
                runner.enforce_frozen_order("second", analyst_dir)
            first = analyst_dir / "runs" / "first"
            first.mkdir(parents=True)
            (first / "run.json").write_text(
                json.dumps({"status": "timeout"}), encoding="utf-8"
            )
            runner.enforce_frozen_order("second", analyst_dir)

    def test_event_and_provider_usage_capture(self) -> None:
        event = {
            "type": "item.completed",
            "usage": {"input_tokens": 10, "output_tokens": 2},
            "item": {
                "type": "command_execution",
                "command": "go tool pprof -top evidence.pb.gz",
            },
        }
        self.assertEqual(
            runner.event_summary(event),
            (
                "item.completed",
                {"input_tokens": 10, "output_tokens": 2},
                "command_execution",
                "go tool pprof -top evidence.pb.gz",
            ),
        )
        self.assertEqual(
            runner.aggregate_provider_usage(
                [
                    {"input_tokens": 10, "output_tokens": 2},
                    {"input_tokens": 5, "output_tokens": 1},
                ]
            ),
            {"input_tokens": 15, "output_tokens": 3},
        )
        self.assertEqual(
            runner.aggregate_provider_usage(
                [{"input_tokens": 10, "output_tokens": 2, "total_tokens": 12}]
            )["total_tokens"],
            12,
        )
        with self.assertRaises(RuntimeError):
            runner.aggregate_provider_usage(
                [{"input_tokens": 10, "output_tokens": 2, "total_tokens": 13}]
            )

    def test_contract_hash_helper_detects_changes_and_set_drift(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "frozen.txt"
            path.write_text("one", encoding="utf-8")
            registered = {"frozen.txt": contract.sha256_file(path)}
            self.assertEqual(
                contract.verify_file_hashes(
                    root, registered, {"frozen.txt"}
                ),
                [],
            )
            path.write_text("two", encoding="utf-8")
            self.assertEqual(
                contract.verify_file_hashes(
                    root, registered, {"frozen.txt"}
                )[0]["path"],
                "frozen.txt",
            )
            with self.assertRaises(RuntimeError):
                contract.verify_file_hashes(root, registered, {"other.txt"})

    def test_execution_gate_rejects_nonpass_without_model_call(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            record = Path(directory) / "verification.json"
            record.write_text(
                json.dumps({"status": "FAIL", "stage": "analyst"}),
                encoding="utf-8",
            )
            with self.assertRaises(RuntimeError):
                runner.verify_execution_gate(record)


if __name__ == "__main__":
    unittest.main()
