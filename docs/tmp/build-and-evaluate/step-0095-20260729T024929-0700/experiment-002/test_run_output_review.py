#!/usr/bin/env python3
"""Focused tests for the frozen blinded output-review runner."""

from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

import run_analysts
import run_output_review as review


class OutputReviewRunnerTests(unittest.TestCase):
    def decisions(self) -> tuple[set[str], dict]:
        aliases = run_analysts.review_alias_assignment(
            run_analysts.registered_runs()
        )
        case_ids = {case["case_id"] for case in aliases["cases"]}
        document = {
            "cases": [
                {
                    "case_id": case_id,
                    **{
                        field: True
                        for field in run_analysts.REVIEW_DECISION_FIELDS
                    },
                }
                for case_id in sorted(case_ids)
            ]
        }
        return case_ids, document

    def test_prompt_is_complete_and_has_no_private_or_outcome_target(self) -> None:
        self.assertIn("all 40", review.REVIEW_PROMPT)
        self.assertIn("rerun every cited", review.REVIEW_PROMPT)
        self.assertIn("execution.json", review.REVIEW_PROMPT)
        self.assertNotIn("ToolSandbox", review.REVIEW_PROMPT)
        self.assertNotIn("confirmatory", review.REVIEW_PROMPT)
        self.assertNotIn("experiment-001", review.REVIEW_PROMPT)

    def test_command_fixes_fresh_model_timeout_cwd_schema_and_decisions(self) -> None:
        command = review.review_command()
        self.assertEqual(command[:3], ["timeout", "1800", "codex"])
        self.assertIn("--ephemeral", command)
        self.assertIn("--ignore-user-config", command)
        self.assertIn("--ignore-rules", command)
        self.assertEqual(
            command[command.index("--model") + 1], "gpt-5.6-sol"
        )
        self.assertEqual(
            command[command.index("--sandbox") + 1], "read-only"
        )
        self.assertEqual(
            command[command.index("--cd") + 1],
            str(review.REVIEW_BUNDLE.resolve()),
        )
        self.assertEqual(
            command[command.index("--output-schema") + 1],
            str(review.INTERNAL_OUTPUT_SCHEMA_PATH.resolve()),
        )
        self.assertEqual(
            command[command.index("--output-last-message") + 1],
            str(review.DECISIONS_PATH.resolve()),
        )

    def test_decisions_require_exact_cases_fields_and_booleans(self) -> None:
        case_ids, document = self.decisions()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "decisions.json"
            path.write_text(json.dumps(document), encoding="utf-8")
            self.assertEqual(
                review.validate_decisions(path, case_ids), document
            )
            document["cases"][0]["extra"] = True
            path.write_text(json.dumps(document), encoding="utf-8")
            with self.assertRaises(review.ReviewRunError):
                review.validate_decisions(path, case_ids)
            del document["cases"][0]["extra"]
            document["cases"][0][
                run_analysts.REVIEW_DECISION_FIELDS[0]
            ] = 1
            path.write_text(json.dumps(document), encoding="utf-8")
            with self.assertRaises(review.ReviewRunError):
                review.validate_decisions(path, case_ids)

    def test_decisions_reject_duplicate_or_missing_case(self) -> None:
        case_ids, document = self.decisions()
        document["cases"][1]["case_id"] = document["cases"][0]["case_id"]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "decisions.json"
            path.write_text(json.dumps(document), encoding="utf-8")
            with self.assertRaises(review.ReviewRunError):
                review.validate_decisions(path, case_ids)

    def test_contract_gate_rejects_nonpass_without_reviewer_call(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "verification.json"
            path.write_text(
                json.dumps({"status": "FAIL", "stage": "analyst"}),
                encoding="utf-8",
            )
            with self.assertRaises(review.ReviewRunError):
                review.verify_contract_fresh(path)

    def test_tool_audit_allows_relative_local_evidence_computation(self) -> None:
        records = [
            {
                "type": "command_execution",
                "command": (
                    "cd cases/case-abcd/evidence && "
                    "jq -s 'map(.value) | add' samples.jsonl"
                ),
            },
            {
                "type": "command_execution",
                "command": "sed -n '1,80p' cases/case-abcd/output.json",
            },
        ]
        self.assertEqual(review.audit_tool_commands(records), [])

    def test_tool_audit_rejects_nonlocal_network_or_unrecorded_calls(self) -> None:
        rejected = [
            {"type": "web_search", "command": None},
            {"type": "mcp_tool_call", "command": None},
            {"type": "command_execution", "command": None},
            {"type": "command_execution", "command": "cat ../order.json"},
            {"type": "command_execution", "command": "cat ~/.codex/config.toml"},
            {"type": "command_execution", "command": "cat $HOME/.codex/config.toml"},
            {"type": "command_execution", "command": "cat ${PWD}/../order.json"},
            {"type": "command_execution", "command": "cat /etc/passwd"},
            {
                "type": "command_execution",
                "command": "cat review-alias-map.private.json",
            },
            {
                "type": "command_execution",
                "command": "curl http://127.0.0.1:18185/v1/models",
            },
        ]
        errors = review.audit_tool_commands(rejected)
        self.assertGreaterEqual(len(errors), len(rejected))
        self.assertTrue(any("disallowed type" in error for error in errors))
        self.assertTrue(any("network/endpoint" in error for error in errors))
        self.assertTrue(any("absolute path" in error for error in errors))
        self.assertTrue(any("private artifact" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
