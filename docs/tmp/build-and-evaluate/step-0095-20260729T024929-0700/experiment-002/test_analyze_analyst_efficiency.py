#!/usr/bin/env python3
"""Synthetic golden tests for the frozen analyst-efficiency analysis."""

from __future__ import annotations

import json
import hashlib
import math
import tempfile
import unittest
from pathlib import Path

import numpy as np

import analyze_analyst_efficiency as analysis


class SyntheticExperiment:
    def __init__(
        self,
        root: Path,
        *,
        profile_time: float = 50.0,
        raw_time: float = 100.0,
        profile_tokens: int = 90,
        raw_tokens: int = 100,
    ) -> None:
        self.root = root
        self.runs_root = root / "runs"
        self.schedule_path = root / "schedule.json"
        self.review_path = root / "review.json"
        self.alias_path = root / "alias.json"
        self.analyst_dir = root / "analyst"
        self.review_model_contract_path = (
            self.analyst_dir / "review-model-contract.json"
        )
        self.review_command_path = self.analyst_dir / "review-command.json"
        self.review_prompt_path = self.analyst_dir / "review-prompt.txt"
        self.bundle_manifest_path = (
            self.analyst_dir / "review-bundle" / "manifest.json"
        )
        self.review_provenance_path = (
            self.analyst_dir / "review-run" / "run.json"
        )
        runs = []
        decisions = []
        case_to_run = {}
        rank_1 = {}
        for block_index in range(1, 21):
            profile_first = block_index <= 10
            for arm, arm_slug, rank, time, total in (
                (
                    analysis.PROFILE_ARM,
                    "profile",
                    block_index,
                    profile_time,
                    profile_tokens,
                ),
                (
                    analysis.RAW_ARM,
                    "raw-operations",
                    block_index,
                    raw_time,
                    raw_tokens,
                ),
            ):
                within_order = (
                    1
                    if (arm == analysis.PROFILE_ARM) == profile_first
                    else 2
                )
                position = (block_index - 1) * 2 + within_order
                run_id = f"run-{arm_slug}-{block_index:02d}"
                case_id = f"case-{arm_slug}-{block_index:02d}"
                run_metadata = {
                    "run_id": run_id,
                    "arm": arm,
                    "block_id": f"block-{block_index:02d}",
                    "within_block_order": within_order,
                    "arm_rank": rank,
                }
                schedule_entry = {
                    **run_metadata,
                    "block_index": block_index,
                    "package": str((root / f"package-{arm_slug}").resolve()),
                    "position": position,
                    "prompt_file": str(
                        (root / "prompts" / f"{run_id}.txt").resolve()
                    ),
                    "prompt_sha256": (
                        "a" * 64 if arm == analysis.PROFILE_ARM else "b" * 64
                    ),
                }
                runs.append(schedule_entry)
                if rank == 1:
                    rank_1[arm] = run_id
                run_dir = self.runs_root / run_id
                run_dir.mkdir(parents=True)
                self._write_json(
                    run_dir / "run.json",
                    {
                        "run": run_metadata,
                        "status": "ok",
                        "exit_code": 0,
                        "final_response_elapsed_seconds": time,
                        "provider_usage_totals": {
                            "input_tokens": total - 10,
                            "output_tokens": 10,
                            "cached_input_tokens": 0,
                            "reasoning_output_tokens": 0,
                        },
                    },
                )
                decisions.append(
                    {
                        "case_id": case_id,
                        **{name: True for name in analysis.REVIEW_CHECKS},
                    }
                )
                case_to_run[case_id] = run_id
        runs.sort(key=lambda item: item["position"])
        self._write_json(
            self.schedule_path,
            {
                "block_count": 20,
                "exact_first_arm_balance": {
                    analysis.PROFILE_ARM: 10,
                    analysis.RAW_ARM: 10,
                },
                "rank_1": rank_1,
                "run_count": 40,
                "runs": runs,
                "schema": analysis.SCHEDULE_SCHEMA,
                "seed": analysis.SCHEDULE_SEED,
            },
        )
        self._write_json(self.review_path, {"cases": decisions})
        self._write_json(
            self.alias_path,
            {
                "case_count": 40,
                "cases": [
                    {"case_id": case_id, "run_id": run_id}
                    for case_id, run_id in case_to_run.items()
                ],
                "schema": analysis.ALIAS_MAP_SCHEMA,
                "seed": analysis.ALIAS_MAP_SEED,
            },
        )
        self._write_reviewer_artifacts()
        self.refresh_review_provenance()

    @staticmethod
    def _write_json(path: Path, value: object) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")

    @staticmethod
    def _sha256(path: Path) -> str:
        return hashlib.sha256(path.read_bytes()).hexdigest()

    def _write_reviewer_artifacts(self) -> None:
        self._write_json(
            self.review_model_contract_path,
            {
                "schema": analysis.REVIEW_MODEL_CONTRACT_SCHEMA,
                "model_identifier": analysis.REVIEWER_MODEL_IDENTIFIER,
                "timeout_seconds": analysis.REVIEWER_TIMEOUT_SECONDS,
            },
        )
        self._write_json(
            self.review_command_path,
            {
                "schema": analysis.REVIEW_COMMAND_SCHEMA,
                "command_identifier": analysis.REVIEWER_COMMAND_IDENTIFIER,
                "command": ["codex", "exec", "--ephemeral"],
            },
        )
        self.review_prompt_path.parent.mkdir(parents=True, exist_ok=True)
        self.review_prompt_path.write_text(
            "Synthetic frozen blind-review prompt.\n", encoding="utf-8"
        )
        self._write_json(
            self.bundle_manifest_path,
            {
                "schema": "agentsight.utility2.output-review-bundle-manifest.v1",
                "case_count": 40,
            },
        )

    def refresh_review_provenance(self) -> None:
        manifest_sha = self._sha256(self.bundle_manifest_path)
        zeros = "0" * 64
        self._write_json(
            self.review_provenance_path,
            {
                "schema": analysis.REVIEW_RUN_SCHEMA,
                "status": "ok",
                "command": ["codex", "exec", "--ephemeral"],
                "exit_code": 0,
                "reviewer_model_identifier": analysis.REVIEWER_MODEL_IDENTIFIER,
                "reviewer_command_identifier": analysis.REVIEWER_COMMAND_IDENTIFIER,
                "decisions_path": str(self.review_path.resolve()),
                "decisions_sha256": self._sha256(self.review_path),
                "frozen_review_prompt_sha256": self._sha256(
                    self.review_prompt_path
                ),
                "frozen_review_model_contract_sha256": self._sha256(
                    self.review_model_contract_path
                ),
                "frozen_review_command_sha256": self._sha256(
                    self.review_command_path
                ),
                "review_bundle_manifest_sha256_before": manifest_sha,
                "review_bundle_manifest_sha256_after": manifest_sha,
                "review_bundle_manifest_unchanged": True,
                "started_at": "2026-07-29T00:00:00Z",
                "finished_at": "2026-07-29T00:00:01Z",
                "wall_seconds": 1.0,
                "event_count": 1,
                "first_event_at": "2026-07-29T00:00:00.100000Z",
                "last_event_at": "2026-07-29T00:00:00.900000Z",
                "final_response_received_at": "2026-07-29T00:00:00.800000Z",
                "first_event_elapsed_seconds": 0.1,
                "last_event_elapsed_seconds": 0.9,
                "final_response_elapsed_seconds": 0.8,
                "events_sha256": zeros,
                "event_receipts_sha256": zeros,
                "stderr_sha256": zeros,
                "provider_usage_events": [],
                "provider_usage_totals": {
                    "input_tokens": 1,
                    "output_tokens": 1,
                },
                "model_turns": 1,
                "tool_call_counts": {},
                "tool_call_total": 0,
                "actual_tool_commands": [],
                "validation_errors": [],
            },
        )

    def run_path(self, arm: str, block: int) -> Path:
        return self.runs_root / f"run-{arm}-{block:02d}" / "run.json"

    def read_run(self, arm: str, block: int) -> dict:
        return json.loads(self.run_path(arm, block).read_text(encoding="utf-8"))

    def write_run(self, arm: str, block: int, document: dict) -> None:
        self._write_json(self.run_path(arm, block), document)

    def set_review_valid(self, arm: str, block: int, valid: bool) -> None:
        case_id = f"case-{arm}-{block:02d}"
        review = json.loads(self.review_path.read_text(encoding="utf-8"))
        decision = next(item for item in review["cases"] if item["case_id"] == case_id)
        decision[analysis.REVIEW_CHECKS[0]] = valid
        self._write_json(self.review_path, review)
        self.refresh_review_provenance()

    def analyze(self) -> dict:
        return analysis.analyze(
            self.schedule_path,
            self.runs_root,
            self.review_path,
            self.alias_path,
            self.review_provenance_path,
        )


class AnalystEfficiencyGoldenTests(unittest.TestCase):
    def test_no_interpolation_order_statistic_retains_ties(self) -> None:
        values = np.asarray([1.0] * 97_499 + [2.0] * 2_501)
        self.assertEqual(analysis.no_interpolation_order_statistic(values, 0.975), 2.0)
        self.assertEqual(
            analysis.no_interpolation_order_statistic(values, 0.97499), 1.0
        )
        self.assertEqual(
            analysis.no_interpolation_order_statistic([4.0, 1.0, 3.0, 2.0], 0.5),
            2.0,
        )

    def test_pcg64_whole_block_sampling_and_endpoint_pairing_golden(self) -> None:
        indices = analysis.draw_whole_block_indices()
        self.assertEqual(indices.shape, (100_000, 20))
        self.assertEqual(
            indices[:2].tolist(),
            [
                [5, 2, 10, 15, 0, 2, 7, 5, 15, 0, 3, 7, 15, 8, 18, 1, 7, 5, 11, 5],
                [2, 19, 12, 13, 17, 3, 15, 6, 1, 19, 0, 5, 16, 3, 13, 17, 13, 9, 0, 19],
            ],
        )
        self.assertEqual(
            hashlib.sha256(
                indices.astype("<i8", copy=False).tobytes(order="C")
            ).hexdigest(),
            "5ba4965f21a1250288aab0447beec0300f3ed84744a9f34564c98dc7edd7a7ef",
        )
        time_logs = np.arange(20, dtype=np.float64) / 100.0
        token_logs = 1.75 * time_logs + 0.03
        boot_time, boot_tokens, returned_indices = analysis.bootstrap_paired_thetas(
            time_logs, token_logs
        )
        np.testing.assert_array_equal(returned_indices, indices)
        # A positive affine transform commutes with the sample median.  This
        # identity can only hold row-wise here because both endpoints use the
        # exact same sampled whole-block indices.
        np.testing.assert_allclose(boot_tokens, 1.75 * boot_time + 0.03, rtol=0, atol=1e-15)

    def test_missing_and_zero_provider_usage_are_hard_stops(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            fixture = SyntheticExperiment(Path(directory))
            run = fixture.read_run("profile", 1)
            del run["provider_usage_totals"]["input_tokens"]
            fixture.write_run("profile", 1, run)
            with self.assertRaisesRegex(analysis.AnalysisInputError, "input_tokens"):
                fixture.analyze()

        with tempfile.TemporaryDirectory() as directory:
            fixture = SyntheticExperiment(Path(directory))
            run = fixture.read_run("profile", 1)
            run["provider_usage_totals"]["input_tokens"] = 0
            run["provider_usage_totals"]["output_tokens"] = 0
            fixture.write_run("profile", 1, run)
            with self.assertRaisesRegex(analysis.AnalysisInputError, "must be positive"):
                fixture.analyze()

        with tempfile.TemporaryDirectory() as directory:
            fixture = SyntheticExperiment(Path(directory))
            run = fixture.read_run("profile", 1)
            run["provider_usage_totals"]["total_tokens"] = 999
            fixture.write_run("profile", 1, run)
            with self.assertRaisesRegex(analysis.AnalysisInputError, "must equal"):
                fixture.analyze()

    def test_invalid_and_timeout_penalty_is_900_but_usage_is_retained(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            fixture = SyntheticExperiment(Path(directory))
            fixture.set_review_valid("profile", 1, False)
            invalid_run = fixture.read_run("profile", 1)
            invalid_run["final_response_elapsed_seconds"] = 1.0
            invalid_run["provider_usage_totals"]["input_tokens"] = 767
            invalid_run["provider_usage_totals"]["output_tokens"] = 10
            fixture.write_run("profile", 1, invalid_run)

            timeout_run = fixture.read_run("raw-operations", 2)
            timeout_run["status"] = "timeout"
            timeout_run["exit_code"] = 124
            timeout_run["final_response_elapsed_seconds"] = None
            timeout_run["provider_usage_totals"]["input_tokens"] = 878
            timeout_run["provider_usage_totals"]["output_tokens"] = 10
            fixture.write_run("raw-operations", 2, timeout_run)

            result = fixture.analyze()
            by_id = {
                item["run_id"]: item
                for block in result["individual_blocks"]
                for item in (block["profile"], block["raw_operations"])
            }
            invalid = by_id["run-profile-01"]
            timeout = by_id["run-raw-operations-02"]
            self.assertEqual(invalid["reported_final_answer_seconds"], 1.0)
            self.assertEqual(invalid["effective_final_answer_seconds"], 900.0)
            self.assertEqual(invalid["provider_total_tokens"], 777)
            self.assertEqual(timeout["reported_final_answer_seconds"], None)
            self.assertEqual(timeout["effective_final_answer_seconds"], 900.0)
            self.assertEqual(timeout["provider_total_tokens"], 888)
            self.assertFalse(invalid["effective_valid"])
            self.assertFalse(timeout["effective_valid"])

    def test_constant_ratio_golden_pass_and_descriptives(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            fixture = SyntheticExperiment(
                Path(directory),
                profile_time=50.0,
                raw_time=100.0,
                profile_tokens=100,
                raw_tokens=100,
            )
            result = fixture.analyze()
            time = result["confirmatory_endpoints"]["time"]
            tokens = result["confirmatory_endpoints"]["provider_tokens"]
            self.assertAlmostEqual(time["theta_median_log_ratio"], math.log(0.5))
            self.assertAlmostEqual(time["ratio_exp_theta"], 0.5)
            self.assertAlmostEqual(
                time["bonferroni_one_sided_97_5_percent_upper"], 0.5
            )
            self.assertAlmostEqual(tokens["ratio_exp_theta"], 1.0)
            self.assertAlmostEqual(
                tokens["bonferroni_one_sided_97_5_percent_upper"], 1.0
            )
            self.assertTrue(result["confirmatory_gate"]["pass"])
            self.assertEqual(result["analysis"]["status"], "PASS")
            self.assertTrue(result["rank_1_policy_gate"]["pass"])
            self.assertTrue(result["downstream_readiness"]["pass"])
            self.assertEqual(len(result["individual_blocks"]), 20)
            strata = result["descriptive"]["within_block_order_strata"]
            self.assertEqual(strata["profile_first"]["n_blocks"], 10)
            self.assertEqual(strata["raw_first"]["n_blocks"], 10)
            self.assertEqual(
                result["descriptive"]["arms"][analysis.PROFILE_ARM][
                    "effective_final_answer_seconds"
                ]["raw_median"],
                50.0,
            )

    def test_confirmatory_strict_and_nonstrict_boundaries(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            # U_T == 1 fails because the registered time boundary is strict.
            fixture = SyntheticExperiment(
                Path(directory),
                profile_time=100.0,
                raw_time=100.0,
                profile_tokens=100,
                raw_tokens=100,
            )
            result = fixture.analyze()
            self.assertFalse(
                result["confirmatory_gate"]["clauses"][
                    "time_upper_strictly_below_1_00"
                ]
            )
            self.assertTrue(
                result["confirmatory_gate"]["clauses"][
                    "provider_token_upper_at_or_below_1_00"
                ]
            )
            self.assertFalse(result["confirmatory_gate"]["pass"])

    def test_validity_count_and_profile_not_lower_boundaries(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            fixture = SyntheticExperiment(Path(directory))
            for block in (1, 2):
                fixture.set_review_valid("profile", block, False)
            fixture.set_review_valid("raw-operations", 1, False)
            result = fixture.analyze()
            self.assertEqual(result["validity"][analysis.PROFILE_ARM], 18)
            self.assertEqual(result["validity"][analysis.RAW_ARM], 19)
            self.assertTrue(
                result["confirmatory_gate"]["clauses"][
                    "both_arms_valid_at_least_18_of_20"
                ]
            )
            self.assertFalse(
                result["confirmatory_gate"]["clauses"][
                    "profile_valid_count_not_lower_than_raw"
                ]
            )
            self.assertFalse(result["confirmatory_gate"]["pass"])

        with tempfile.TemporaryDirectory() as directory:
            fixture = SyntheticExperiment(Path(directory))
            for block in (1, 2, 3):
                fixture.set_review_valid("profile", block, False)
            result = fixture.analyze()
            self.assertEqual(result["validity"][analysis.PROFILE_ARM], 17)
            self.assertFalse(
                result["confirmatory_gate"]["clauses"][
                    "both_arms_valid_at_least_18_of_20"
                ]
            )

    def test_alias_map_must_be_complete_bijective_and_review_remains_case_keyed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            fixture = SyntheticExperiment(Path(directory))
            alias = json.loads(fixture.alias_path.read_text(encoding="utf-8"))
            alias["cases"][1]["run_id"] = alias["cases"][0]["run_id"]
            fixture._write_json(fixture.alias_path, alias)
            with self.assertRaisesRegex(analysis.AnalysisInputError, "bijective"):
                fixture.analyze()

        with tempfile.TemporaryDirectory() as directory:
            fixture = SyntheticExperiment(Path(directory))
            review = json.loads(fixture.review_path.read_text(encoding="utf-8"))
            review["cases"][0]["run_id"] = "forbidden-unblinded-key"
            fixture._write_json(fixture.review_path, review)
            fixture.refresh_review_provenance()
            with self.assertRaisesRegex(
                analysis.AnalysisInputError, "case_id and exactly"
            ):
                fixture.analyze()

    def test_frozen_schedule_metadata_and_terminal_status_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            fixture = SyntheticExperiment(Path(directory))
            schedule = json.loads(fixture.schedule_path.read_text(encoding="utf-8"))
            schedule["seed"] += 1
            fixture._write_json(fixture.schedule_path, schedule)
            with self.assertRaisesRegex(analysis.AnalysisInputError, "schedule seed"):
                fixture.analyze()

        with tempfile.TemporaryDirectory() as directory:
            fixture = SyntheticExperiment(Path(directory))
            schedule = json.loads(fixture.schedule_path.read_text(encoding="utf-8"))
            schedule["rank_1"][analysis.PROFILE_ARM] = schedule["rank_1"][
                analysis.RAW_ARM
            ]
            fixture._write_json(fixture.schedule_path, schedule)
            with self.assertRaisesRegex(analysis.AnalysisInputError, "rank_1.PROFILE"):
                fixture.analyze()

        with tempfile.TemporaryDirectory() as directory:
            fixture = SyntheticExperiment(Path(directory))
            run = fixture.read_run("profile", 1)
            run["status"] = "running"
            fixture.write_run("profile", 1, run)
            with self.assertRaisesRegex(analysis.AnalysisInputError, "terminal statuses"):
                fixture.analyze()

        with tempfile.TemporaryDirectory() as directory:
            fixture = SyntheticExperiment(Path(directory))
            run = fixture.read_run("profile", 1)
            run["status"] = "failed"
            run["exit_code"] = 1
            fixture.write_run("profile", 1, run)
            result = fixture.analyze()
            failed = result["individual_blocks"][0]["profile"]
            self.assertFalse(failed["effective_valid"])
            self.assertEqual(failed["effective_final_answer_seconds"], 900.0)

    def test_rank_1_policy_gate_blocks_downstream_without_substitution(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            fixture = SyntheticExperiment(Path(directory))
            fixture.set_review_valid("profile", 1, False)
            fixture.set_review_valid("raw-operations", 1, False)
            result = fixture.analyze()
            # Nineteen valid outputs per arm and a single paired 900/900 block
            # leave the separately registered efficiency estimator passing.
            self.assertTrue(result["confirmatory_gate"]["pass"])
            self.assertFalse(result["rank_1_policy_gate"]["pass"])
            self.assertTrue(result["rank_1_policy_gate"]["no_substitution"])
            self.assertFalse(result["downstream_readiness"]["pass"])
            self.assertTrue(result["downstream_readiness"]["downstream_forbidden"])

    def test_review_provenance_binds_status_decisions_and_frozen_artifacts(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            fixture = SyntheticExperiment(Path(directory))
            provenance = json.loads(
                fixture.review_provenance_path.read_text(encoding="utf-8")
            )
            provenance["status"] = "error"
            fixture._write_json(fixture.review_provenance_path, provenance)
            with self.assertRaisesRegex(
                analysis.AnalysisInputError, "status must be ok"
            ):
                fixture.analyze()

        with tempfile.TemporaryDirectory() as directory:
            fixture = SyntheticExperiment(Path(directory))
            provenance = json.loads(
                fixture.review_provenance_path.read_text(encoding="utf-8")
            )
            del provenance["decisions_sha256"]
            fixture._write_json(fixture.review_provenance_path, provenance)
            with self.assertRaisesRegex(
                analysis.AnalysisInputError, "exactly the frozen"
            ):
                fixture.analyze()

        with tempfile.TemporaryDirectory() as directory:
            fixture = SyntheticExperiment(Path(directory))
            review = json.loads(fixture.review_path.read_text(encoding="utf-8"))
            review["cases"][0][analysis.REVIEW_CHECKS[0]] = False
            fixture._write_json(fixture.review_path, review)
            with self.assertRaisesRegex(
                analysis.AnalysisInputError, "decisions_sha256"
            ):
                fixture.analyze()

        with tempfile.TemporaryDirectory() as directory:
            fixture = SyntheticExperiment(Path(directory))
            model_contract = json.loads(
                fixture.review_model_contract_path.read_text(encoding="utf-8")
            )
            model_contract["model_identifier"] = "different-model"
            fixture._write_json(fixture.review_model_contract_path, model_contract)
            with self.assertRaisesRegex(
                analysis.AnalysisInputError, "reviewer model identifier"
            ):
                fixture.analyze()

        with tempfile.TemporaryDirectory() as directory:
            fixture = SyntheticExperiment(Path(directory))
            command = json.loads(
                fixture.review_command_path.read_text(encoding="utf-8")
            )
            command["command_identifier"] = "different-command"
            fixture._write_json(fixture.review_command_path, command)
            with self.assertRaisesRegex(
                analysis.AnalysisInputError, "reviewer command identifier"
            ):
                fixture.analyze()

        with tempfile.TemporaryDirectory() as directory:
            fixture = SyntheticExperiment(Path(directory))
            fixture.review_prompt_path.write_text(
                "Changed after reviewer execution.\n", encoding="utf-8"
            )
            with self.assertRaisesRegex(
                analysis.AnalysisInputError, "frozen_review_prompt_sha256"
            ):
                fixture.analyze()

    def test_review_bundle_manifest_must_match_before_after_and_current(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            fixture = SyntheticExperiment(Path(directory))
            fixture._write_json(
                fixture.bundle_manifest_path,
                {
                    "schema": "agentsight.utility2.output-review-bundle-manifest.v1",
                    "case_count": 39,
                },
            )
            with self.assertRaisesRegex(
                analysis.AnalysisInputError, "before/after/current"
            ):
                fixture.analyze()

        with tempfile.TemporaryDirectory() as directory:
            fixture = SyntheticExperiment(Path(directory))
            provenance = json.loads(
                fixture.review_provenance_path.read_text(encoding="utf-8")
            )
            provenance["review_bundle_manifest_unchanged"] = False
            fixture._write_json(fixture.review_provenance_path, provenance)
            with self.assertRaisesRegex(
                analysis.AnalysisInputError, "manifest_unchanged=true"
            ):
                fixture.analyze()

    def test_review_provenance_pass_is_reported_and_requires_all_40_cases(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            fixture = SyntheticExperiment(Path(directory))
            result = fixture.analyze()
            review_provenance = result["input_provenance"]["review_provenance"]
            self.assertEqual(review_provenance["status"], "ok")
            self.assertEqual(
                review_provenance["reviewer_model_identifier"],
                analysis.REVIEWER_MODEL_IDENTIFIER,
            )
            manifest = review_provenance["frozen_artifacts"][
                "review_bundle_manifest"
            ]
            self.assertEqual(
                manifest["sha256_before"],
                manifest["sha256_after"],
            )
            self.assertEqual(
                manifest["sha256_after"],
                manifest["sha256_current"],
            )
            self.assertEqual(
                result["input_provenance"]["validity_review"]["case_count"], 40
            )

        with tempfile.TemporaryDirectory() as directory:
            fixture = SyntheticExperiment(Path(directory))
            review = json.loads(fixture.review_path.read_text(encoding="utf-8"))
            review["cases"].pop()
            fixture._write_json(fixture.review_path, review)
            fixture.refresh_review_provenance()
            with self.assertRaisesRegex(
                analysis.AnalysisInputError, "exactly 40 decisions"
            ):
                fixture.analyze()

    def test_sensitivity_thresholds_are_separate_and_cannot_flip_confirmatory_fail(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            fixture = SyntheticExperiment(
                Path(directory),
                profile_time=85.0,
                raw_time=100.0,
                profile_tokens=104,
                raw_tokens=100,
            )
            result = fixture.analyze()
            sensitivity = result[
                "sensitivity_only_post_experiment_001_adaptation"
            ]
            self.assertTrue(sensitivity["time_upper_strictly_below_0_90"])
            self.assertTrue(sensitivity["provider_token_upper_at_or_below_1_05"])
            self.assertTrue(sensitivity["both_alternative_thresholds_hold"])
            self.assertFalse(result["confirmatory_gate"]["pass"])
            self.assertTrue(
                sensitivity[
                    "cannot_determine_confirmatory_gate_or_paper_admission"
                ]
            )


if __name__ == "__main__":
    unittest.main(verbosity=2)
