#!/usr/bin/env python3
"""Focused tests for immutable rank-1 policy freezing."""

from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

import freeze_rank1_policies as freeze


class FreezeRank1PoliciesTests(unittest.TestCase):
    @staticmethod
    def source_fixture(root: Path) -> tuple[Path, Path]:
        rows = []
        rank_1 = {}
        for block in range(1, 21):
            for arm, slug in (
                ("PROFILE", "profile"),
                ("RAW-OPERATIONS", "raw"),
            ):
                run_id = f"run-{slug}-{block}"
                rows.append(
                    {
                        "run_id": run_id,
                        "arm": arm,
                        "arm_rank": block,
                    }
                )
                if block == 1:
                    rank_1[arm] = run_id
                    run_dir = root / "runs" / run_id
                    run_dir.mkdir(parents=True)
                    (run_dir / "run.json").write_text(
                        json.dumps(
                            {
                                "status": "ok",
                                "run": {"run_id": run_id, "arm": arm},
                            }
                        ),
                        encoding="utf-8",
                    )
                    (run_dir / "final.json").write_text(
                        json.dumps(
                            {
                                "diagnosis": "recurring behavior",
                                "quantitative_evidence": [
                                    {"command": "jq .", "finding": "one"}
                                ],
                                "policy_text": (
                                    "Observe state before retrying and change "
                                    "strategy after repeated nonprogress."
                                ),
                                "expected_mechanism": "Avoids wasted retries.",
                            }
                        ),
                        encoding="utf-8",
                    )
        schedule = root / "order.json"
        schedule.write_text(
            json.dumps({"runs": rows, "rank_1": rank_1}),
            encoding="utf-8",
        )
        return schedule, root / "runs"

    def test_extracts_only_fixed_rank1_and_exact_policy_text(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            schedule, runs = self.source_fixture(Path(directory))
            selected = freeze._rank1_policy_sources(schedule, runs)
            self.assertEqual(
                selected["PROFILE"]["run_id"], "run-profile-1"
            )
            self.assertEqual(selected["RAW-OPERATIONS"]["run_id"], "run-raw-1")
            self.assertEqual(selected["PROFILE"]["word_count"], 10)

    def test_rejects_rank1_substitution_and_policy_over_60_words(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            schedule, runs = self.source_fixture(Path(directory))
            document = json.loads(schedule.read_text(encoding="utf-8"))
            document["rank_1"]["PROFILE"] = "run-profile-2"
            schedule.write_text(json.dumps(document), encoding="utf-8")
            with self.assertRaises(freeze.PolicyFreezeError):
                freeze._rank1_policy_sources(schedule, runs)

        with tempfile.TemporaryDirectory() as directory:
            schedule, runs = self.source_fixture(Path(directory))
            final = runs / "run-profile-1" / "final.json"
            document = json.loads(final.read_text(encoding="utf-8"))
            document["policy_text"] = "word " * 61
            final.write_text(json.dumps(document), encoding="utf-8")
            with self.assertRaises(freeze.PolicyFreezeError):
                freeze._rank1_policy_sources(schedule, runs)

    def test_admission_requires_exact_recomputation_and_both_gates(self) -> None:
        passing = {
            "confirmatory_gate": {"pass": True},
            "rank_1_policy_gate": {"pass": True},
        }
        freeze._assert_analysis_admission(passing, passing)
        with self.assertRaises(freeze.PolicyFreezeError):
            freeze._assert_analysis_admission(passing, {**passing, "x": 1})
        with self.assertRaises(freeze.PolicyFreezeError):
            freeze._assert_analysis_admission(
                {
                    "confirmatory_gate": {"pass": False},
                    "rank_1_policy_gate": {"pass": True},
                },
                {
                    "confirmatory_gate": {"pass": False},
                    "rank_1_policy_gate": {"pass": True},
                },
            )

    def test_writes_exact_text_manifest_and_refuses_overwrite(self) -> None:
        selected = {
            arm: {
                "run_id": f"run-{arm}",
                "policy_text": f"Exact {arm} policy.",
                "word_count": 3,
                "run_record_sha256": "a" * 64,
                "final_sha256": "b" * 64,
            }
            for arm in freeze.POLICY_FILES
        }
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "policies"
            manifest = freeze._write_policy_artifacts(
                output, selected, {"binding": "test"}
            )
            for arm, filename in freeze.POLICY_FILES.items():
                self.assertEqual(
                    (output / filename).read_text(encoding="utf-8"),
                    selected[arm]["policy_text"],
                )
            self.assertTrue(manifest["no_substitution"])
            with self.assertRaises(freeze.PolicyFreezeError):
                freeze._write_policy_artifacts(
                    output, selected, {"binding": "test"}
                )

    def test_commands_bind_all_postreview_inputs(self) -> None:
        command = freeze.analysis_command()
        for flag in (
            "--schedule",
            "--runs-root",
            "--validity-review",
            "--alias-map",
            "--review-provenance",
            "--output",
        ):
            self.assertIn(flag, command)
        freeze_command = freeze.freeze_command()
        self.assertIn("--execute-freeze", freeze_command)
        self.assertIn("--contract-verification", freeze_command)
        self.assertIn("--review-provenance", freeze_command)


if __name__ == "__main__":
    unittest.main()
