#!/usr/bin/env python3
"""Frozen confirmatory analysis for experiment-002 analyst efficiency.

The command consumes the frozen 40-run schedule, one ``run.json`` per opaque
run identifier, a still-blinded validity review keyed by case identifier, and
the separately frozen case-to-run alias map.  It intentionally exposes no CLI
controls for the bootstrap seed, number of resamples, block count, timeout, or
decision thresholds.

Expected input shapes
---------------------

``schedule.json``::

    {
      "schema": "agentsight.utility2.analyst-order.v1",
      "seed": 2026072902,
      "block_count": 20,
      "run_count": 40,
      "exact_first_arm_balance": {"PROFILE": 10, "RAW-OPERATIONS": 10},
      "rank_1": {"PROFILE": "...", "RAW-OPERATIONS": "..."},
      "runs": [{
      "run_id": "opaque-run-id",
      "arm": "PROFILE",
      "block_id": "block-01",
      "block_index": 1,
      "within_block_order": 1,
      "position": 1,
      "arm_rank": 1,
      "package": "/absolute/package/path",
      "prompt_file": "/absolute/prompt/path",
      "prompt_sha256": "..."
    }, ...]}

``runs-root/<run_id>/run.json`` must repeat the five fields above under
``run`` and contain top-level ``status``, ``exit_code``,
``final_response_elapsed_seconds``, and ``provider_usage_totals``.  The latter
must contain nonnegative integer ``input_tokens`` and ``output_tokens``.  A
positive provider total is computed as their sum.  If ``total_tokens`` is
present, it must equal that sum.

``validity-review.json``::

    {"cases": [{
      "case_id": "opaque-case-id",
      "recurring_bad_vs_good_diagnosis_valid": true,
      "quantitative_support_valid": true,
      "executable_benchmark_agnostic_policy_at_most_60_words": true,
      "no_benchmark_specific_or_hidden_data_reference": true,
      "no_evidence_read_outside_assigned_package": true
    }, ...]}

``alias-map.json``::

    {
      "schema": "agentsight.utility2.review-alias-map.private.v1",
      "seed": 2026072905,
      "case_count": 40,
      "cases": [{"case_id": "...", "run_id": "..."}, ...]
    }

Validity is derived as the conjunction of the five frozen boolean checks.
The alias map, review cases, schedule runs, and on-disk run records must be
complete and bijective before any endpoint is computed.

``--review-provenance`` must point to ``analyst/review-run/run.json``.  The
analyzer derives the frozen model contract, command, prompt, and bundle
manifest paths from that location and rejects the review unless all recorded
identifiers, hashes, decision bindings, and before/after/current manifest
hashes agree.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

import numpy as np


BLOCK_COUNT = 20
RUN_COUNT = 40
RUNS_PER_ARM = 20
SCHEDULE_SCHEMA = "agentsight.utility2.analyst-order.v1"
SCHEDULE_SEED = 2026072902
ALIAS_MAP_SCHEMA = "agentsight.utility2.review-alias-map.private.v1"
ALIAS_MAP_SEED = 2026072905
REVIEW_MODEL_CONTRACT_SCHEMA = (
    "agentsight.utility2.output-review-model-contract.v1"
)
REVIEW_COMMAND_SCHEMA = "agentsight.utility2.output-review-command.v1"
REVIEW_RUN_SCHEMA = "agentsight.utility2.output-review-run.v1"
REVIEWER_MODEL_IDENTIFIER = "gpt-5.6-sol"
REVIEWER_COMMAND_IDENTIFIER = "experiment-002-output-review-v1"
REVIEWER_TIMEOUT_SECONDS = 1800
PROFILE_ARM = "PROFILE"
RAW_ARM = "RAW-OPERATIONS"
ARMS = (PROFILE_ARM, RAW_ARM)
TIMEOUT_SECONDS = 900.0
BOOTSTRAP_SEED = 2026072903
BOOTSTRAP_RESAMPLES = 100_000
SIMULTANEOUS_UPPER_P = 0.975
UNADJUSTED_LOWER_P = 0.025
UNADJUSTED_UPPER_P = 0.975
MIN_VALID_PER_ARM = 18
TERMINAL_STATUSES = ("ok", "timeout", "failed")

REVIEW_CHECKS = (
    "recurring_bad_vs_good_diagnosis_valid",
    "quantitative_support_valid",
    "executable_benchmark_agnostic_policy_at_most_60_words",
    "no_benchmark_specific_or_hidden_data_reference",
    "no_evidence_read_outside_assigned_package",
)

SCHEDULE_FIELDS = (
    "run_id",
    "arm",
    "block_id",
    "within_block_order",
    "arm_rank",
)

SCHEDULE_ENTRY_FIELDS = (
    "arm",
    "arm_rank",
    "block_id",
    "block_index",
    "package",
    "position",
    "prompt_file",
    "prompt_sha256",
    "run_id",
    "within_block_order",
)

SCHEDULE_TOP_LEVEL_FIELDS = (
    "block_count",
    "exact_first_arm_balance",
    "rank_1",
    "run_count",
    "runs",
    "schema",
    "seed",
)

REVIEW_PROVENANCE_FIELDS = (
    "schema",
    "status",
    "command",
    "exit_code",
    "reviewer_model_identifier",
    "reviewer_command_identifier",
    "decisions_path",
    "decisions_sha256",
    "frozen_review_prompt_sha256",
    "frozen_review_model_contract_sha256",
    "frozen_review_command_sha256",
    "review_bundle_manifest_sha256_before",
    "review_bundle_manifest_sha256_after",
    "review_bundle_manifest_unchanged",
    "started_at",
    "finished_at",
    "wall_seconds",
    "event_count",
    "first_event_at",
    "last_event_at",
    "final_response_received_at",
    "first_event_elapsed_seconds",
    "last_event_elapsed_seconds",
    "final_response_elapsed_seconds",
    "events_sha256",
    "event_receipts_sha256",
    "stderr_sha256",
    "provider_usage_events",
    "provider_usage_totals",
    "model_turns",
    "tool_call_counts",
    "tool_call_total",
    "actual_tool_commands",
    "validation_errors",
)


class AnalysisInputError(ValueError):
    """A fail-closed input or telemetry error."""


def _load_json(path: Path) -> Any:
    try:
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)
    except FileNotFoundError as exc:
        raise AnalysisInputError(f"missing required file: {path}") from exc
    except json.JSONDecodeError as exc:
        raise AnalysisInputError(f"invalid JSON in {path}: {exc}") from exc


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _required_sha256(path: Path, field: str) -> str:
    try:
        return _sha256(path)
    except FileNotFoundError as exc:
        raise AnalysisInputError(f"missing frozen reviewer artifact for {field}: {path}") from exc


def _is_sha256(value: Any) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(character in "0123456789abcdef" for character in value)
    )


def _is_nonnegative_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def _positive_finite_number(value: Any, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise AnalysisInputError(f"{field} must be a number")
    result = float(value)
    if not math.isfinite(result) or result <= 0:
        raise AnalysisInputError(f"{field} must be positive and finite")
    return result


def no_interpolation_order_statistic(
    values: Sequence[float] | np.ndarray, p: float
) -> float:
    """Return x_(ceil(p*n)) using 1-indexing, retaining ties.

    This is deliberately not ``numpy.quantile``: interpolation is forbidden by
    the frozen plan.
    """

    array = np.asarray(values, dtype=np.float64)
    if array.ndim != 1 or array.size == 0:
        raise AnalysisInputError("order statistic requires a nonempty 1-D array")
    if not np.all(np.isfinite(array)):
        raise AnalysisInputError("order statistic values must all be finite")
    if not (0.0 < p <= 1.0):
        raise AnalysisInputError("order statistic p must be in (0, 1]")
    sorted_values = np.sort(array, kind="stable")
    one_indexed_rank = math.ceil(p * sorted_values.size)
    return float(sorted_values[one_indexed_rank - 1])


def median_log_ratio(numerators: Sequence[float], denominators: Sequence[float]) -> float:
    numerator = np.asarray(numerators, dtype=np.float64)
    denominator = np.asarray(denominators, dtype=np.float64)
    if numerator.shape != denominator.shape or numerator.ndim != 1:
        raise AnalysisInputError("paired endpoint arrays must be equally sized 1-D arrays")
    if numerator.size == 0:
        raise AnalysisInputError("paired endpoint arrays must not be empty")
    if (
        not np.all(np.isfinite(numerator))
        or not np.all(np.isfinite(denominator))
        or np.any(numerator <= 0)
        or np.any(denominator <= 0)
    ):
        raise AnalysisInputError("paired endpoint values must be positive and finite")
    return float(np.median(np.log(numerator / denominator)))


def draw_whole_block_indices() -> np.ndarray:
    """Draw the one frozen PCG64 bootstrap schedule."""

    generator = np.random.Generator(np.random.PCG64(BOOTSTRAP_SEED))
    return generator.integers(
        0,
        BLOCK_COUNT,
        size=(BOOTSTRAP_RESAMPLES, BLOCK_COUNT),
        dtype=np.int64,
    )


def bootstrap_paired_thetas(
    time_log_ratios: Sequence[float],
    token_log_ratios: Sequence[float],
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Bootstrap both endpoints from the same whole-block indices."""

    time_logs = np.asarray(time_log_ratios, dtype=np.float64)
    token_logs = np.asarray(token_log_ratios, dtype=np.float64)
    if time_logs.shape != (BLOCK_COUNT,) or token_logs.shape != (BLOCK_COUNT,):
        raise AnalysisInputError(
            f"bootstrap requires exactly {BLOCK_COUNT} paired block values per endpoint"
        )
    if not np.all(np.isfinite(time_logs)) or not np.all(np.isfinite(token_logs)):
        raise AnalysisInputError("bootstrap log ratios must be finite")

    indices = draw_whole_block_indices()
    # The same ``indices`` object is deliberately used for T and K.
    boot_time = np.median(time_logs[indices], axis=1)
    boot_tokens = np.median(token_logs[indices], axis=1)
    return boot_time, boot_tokens, indices


def _parse_schedule(schedule_path: Path) -> list[dict[str, Any]]:
    document = _load_json(schedule_path)
    if not isinstance(document, dict) or set(document) != set(
        SCHEDULE_TOP_LEVEL_FIELDS
    ):
        raise AnalysisInputError(
            f"schedule must contain exactly {SCHEDULE_TOP_LEVEL_FIELDS}"
        )
    if document["schema"] != SCHEDULE_SCHEMA:
        raise AnalysisInputError(f"schedule schema must equal {SCHEDULE_SCHEMA}")
    if document["seed"] != SCHEDULE_SEED:
        raise AnalysisInputError(f"schedule seed must equal {SCHEDULE_SEED}")
    if document["block_count"] != BLOCK_COUNT:
        raise AnalysisInputError(f"schedule block_count must equal {BLOCK_COUNT}")
    if document["run_count"] != RUN_COUNT:
        raise AnalysisInputError(f"schedule run_count must equal {RUN_COUNT}")
    if document["exact_first_arm_balance"] != {
        PROFILE_ARM: 10,
        RAW_ARM: 10,
    }:
        raise AnalysisInputError(
            "schedule exact_first_arm_balance must equal "
            '{"PROFILE": 10, "RAW-OPERATIONS": 10}'
        )
    rank_1 = document["rank_1"]
    if (
        not isinstance(rank_1, dict)
        or set(rank_1) != set(ARMS)
        or any(not isinstance(value, str) or not value for value in rank_1.values())
    ):
        raise AnalysisInputError(
            "schedule rank_1 must map PROFILE and RAW-OPERATIONS to run_id"
        )
    runs = document["runs"]
    if not isinstance(runs, list) or len(runs) != RUN_COUNT:
        raise AnalysisInputError(f"schedule must contain exactly {RUN_COUNT} runs")

    normalized: list[dict[str, Any]] = []
    for index, entry in enumerate(runs):
        if not isinstance(entry, dict) or set(entry) != set(SCHEDULE_ENTRY_FIELDS):
            raise AnalysisInputError(
                f"schedule run {index} must contain exactly {SCHEDULE_ENTRY_FIELDS}"
            )
        item = {field: entry[field] for field in SCHEDULE_ENTRY_FIELDS}
        if not isinstance(item["run_id"], str) or not item["run_id"]:
            raise AnalysisInputError(f"schedule run {index} has invalid run_id")
        if item["arm"] not in ARMS:
            raise AnalysisInputError(f"schedule run {item['run_id']} has invalid arm")
        if not isinstance(item["block_id"], str) or not item["block_id"]:
            raise AnalysisInputError(f"schedule run {item['run_id']} has invalid block_id")
        if item["within_block_order"] not in (1, 2):
            raise AnalysisInputError(
                f"schedule run {item['run_id']} within_block_order must be 1 or 2"
            )
        if not isinstance(item["arm_rank"], int) or isinstance(item["arm_rank"], bool):
            raise AnalysisInputError(f"schedule run {item['run_id']} has invalid arm_rank")
        expected_position = index + 1
        expected_block_index = index // 2 + 1
        expected_within_block_order = index % 2 + 1
        if item["position"] != expected_position:
            raise AnalysisInputError(
                f"schedule run {item['run_id']} position must equal {expected_position}"
            )
        if item["block_index"] != expected_block_index:
            raise AnalysisInputError(
                f"schedule run {item['run_id']} block_index must equal "
                f"{expected_block_index}"
            )
        if item["within_block_order"] != expected_within_block_order:
            raise AnalysisInputError(
                f"schedule run {item['run_id']} within_block_order conflicts with position"
            )
        if item["arm_rank"] != expected_block_index:
            raise AnalysisInputError(
                f"schedule run {item['run_id']} arm_rank must equal block_index"
            )
        for path_field in ("package", "prompt_file"):
            if (
                not isinstance(item[path_field], str)
                or not item[path_field]
                or not Path(item[path_field]).is_absolute()
            ):
                raise AnalysisInputError(
                    f"schedule run {item['run_id']} {path_field} must be absolute"
                )
        prompt_sha = item["prompt_sha256"]
        if (
            not isinstance(prompt_sha, str)
            or len(prompt_sha) != 64
            or any(character not in "0123456789abcdef" for character in prompt_sha)
        ):
            raise AnalysisInputError(
                f"schedule run {item['run_id']} has invalid prompt_sha256"
            )
        normalized.append(item)

    run_ids = [item["run_id"] for item in normalized]
    if len(set(run_ids)) != RUN_COUNT:
        raise AnalysisInputError("schedule run_id values must be unique")

    for arm in ARMS:
        arm_entries = [item for item in normalized if item["arm"] == arm]
        if len(arm_entries) != RUNS_PER_ARM:
            raise AnalysisInputError(f"schedule must contain exactly 20 {arm} runs")
        if {item["arm_rank"] for item in arm_entries} != set(range(1, 21)):
            raise AnalysisInputError(f"{arm} arm_rank values must be exactly 1..20")
        rank_one_run = next(item for item in arm_entries if item["arm_rank"] == 1)
        if rank_1[arm] != rank_one_run["run_id"]:
            raise AnalysisInputError(f"schedule rank_1.{arm} is inconsistent")

    block_ids = {item["block_id"] for item in normalized}
    if len(block_ids) != BLOCK_COUNT:
        raise AnalysisInputError(f"schedule must contain exactly {BLOCK_COUNT} blocks")

    profile_first_count = 0
    for block_index in range(1, BLOCK_COUNT + 1):
        block = [item for item in normalized if item["block_index"] == block_index]
        block_id = block[0]["block_id"] if block else f"missing-index-{block_index}"
        if len(block) != 2 or {item["arm"] for item in block} != set(ARMS):
            raise AnalysisInputError(
                f"block index {block_index} must contain one PROFILE and one "
                "RAW-OPERATIONS run"
            )
        if len({item["block_id"] for item in block}) != 1:
            raise AnalysisInputError(
                f"block index {block_index} must have one shared block_id"
            )
        if {item["within_block_order"] for item in block} != {1, 2}:
            raise AnalysisInputError(
                f"block {block_id} must use within_block_order values 1 and 2"
            )
        profile_first_count += int(
            next(item for item in block if item["arm"] == PROFILE_ARM)[
                "within_block_order"
            ]
            == 1
        )
    if profile_first_count != 10:
        raise AnalysisInputError(
            "schedule must contain exactly ten profile-first and ten raw-first blocks"
        )
    return normalized


def _parse_alias_map(
    alias_map_path: Path, scheduled_run_ids: set[str]
) -> dict[str, str]:
    document = _load_json(alias_map_path)
    if not isinstance(document, dict) or set(document) != {
        "schema",
        "seed",
        "case_count",
        "cases",
    }:
        raise AnalysisInputError(
            "alias map must contain exactly schema, seed, case_count, and cases"
        )
    if document["schema"] != ALIAS_MAP_SCHEMA:
        raise AnalysisInputError(f"alias-map schema must equal {ALIAS_MAP_SCHEMA}")
    if document["seed"] != ALIAS_MAP_SEED:
        raise AnalysisInputError(f"alias-map seed must equal {ALIAS_MAP_SEED}")
    if document["case_count"] != RUN_COUNT:
        raise AnalysisInputError(f"alias-map case_count must equal {RUN_COUNT}")
    cases = document["cases"]
    if not isinstance(cases, list) or len(cases) != RUN_COUNT:
        raise AnalysisInputError(f"alias map must contain exactly {RUN_COUNT} mappings")
    mapping: dict[str, str] = {}
    for index, item in enumerate(cases):
        if not isinstance(item, dict) or set(item) != {"case_id", "run_id"}:
            raise AnalysisInputError(
                f"alias-map case {index} must contain exactly case_id and run_id"
            )
        case_id = item["case_id"]
        run_id = item["run_id"]
        if not isinstance(case_id, str) or not case_id or case_id in mapping:
            raise AnalysisInputError(
                f"alias-map case {index} has invalid or duplicate case_id"
            )
        if not isinstance(run_id, str) or not run_id:
            raise AnalysisInputError(f"alias-map case {case_id} has invalid run_id")
        mapping[case_id] = run_id
    values = list(mapping.values())
    if len(set(values)) != RUN_COUNT:
        raise AnalysisInputError("alias map must be bijective (run_id values repeat)")
    if set(values) != scheduled_run_ids:
        raise AnalysisInputError("alias map run_id values do not exactly match schedule")
    return dict(mapping)


def _parse_validity_review(
    review_path: Path, expected_case_ids: set[str]
) -> dict[str, bool]:
    document = _load_json(review_path)
    if not isinstance(document, dict) or set(document) != {"cases"}:
        raise AnalysisInputError(
            "validity review must contain exactly one top-level key: cases"
        )
    decisions = document["cases"]
    if not isinstance(decisions, list) or len(decisions) != RUN_COUNT:
        raise AnalysisInputError(
            f"validity review must contain exactly {RUN_COUNT} decisions"
        )

    validity: dict[str, bool] = {}
    for index, decision in enumerate(decisions):
        if not isinstance(decision, dict) or set(decision) != {
            "case_id",
            *REVIEW_CHECKS,
        }:
            raise AnalysisInputError(
                f"review decision {index} must contain case_id and exactly the "
                "five frozen boolean checks"
            )
        case_id = decision["case_id"]
        if not isinstance(case_id, str) or not case_id or case_id in validity:
            raise AnalysisInputError(f"review decision {index} has invalid/duplicate case_id")
        if any(type(decision[name]) is not bool for name in REVIEW_CHECKS):
            raise AnalysisInputError(
                f"review decision {case_id} checks must all be booleans"
            )
        validity[case_id] = all(decision[name] for name in REVIEW_CHECKS)

    if set(validity) != expected_case_ids:
        raise AnalysisInputError(
            "validity-review case_id values do not exactly match alias map"
        )
    return validity


def _verify_review_provenance(
    provenance_path: Path,
    validity_review_path: Path,
) -> dict[str, Any]:
    """Bind the locked review decisions to its frozen reviewer execution."""

    if (
        provenance_path.name != "run.json"
        or provenance_path.parent.name != "review-run"
        or provenance_path.parent.parent.name != "analyst"
    ):
        raise AnalysisInputError(
            "--review-provenance must point to analyst/review-run/run.json"
        )
    analyst_dir = provenance_path.parent.parent
    model_contract_path = analyst_dir / "review-model-contract.json"
    command_path = analyst_dir / "review-command.json"
    prompt_path = analyst_dir / "review-prompt.txt"
    manifest_path = analyst_dir / "review-bundle" / "manifest.json"

    provenance = _load_json(provenance_path)
    if not isinstance(provenance, dict) or set(provenance) != set(
        REVIEW_PROVENANCE_FIELDS
    ):
        raise AnalysisInputError(
            "review provenance must contain exactly the frozen provenance fields"
        )
    if provenance["schema"] != REVIEW_RUN_SCHEMA:
        raise AnalysisInputError(
            f"review provenance schema must equal {REVIEW_RUN_SCHEMA}"
        )
    if provenance["status"] != "ok" or provenance["exit_code"] != 0:
        raise AnalysisInputError("review provenance status must be ok with exit_code 0")

    model_contract = _load_json(model_contract_path)
    if not isinstance(model_contract, dict):
        raise AnalysisInputError("frozen review model contract must be a JSON object")
    if model_contract.get("schema") != REVIEW_MODEL_CONTRACT_SCHEMA:
        raise AnalysisInputError(
            f"review model-contract schema must equal {REVIEW_MODEL_CONTRACT_SCHEMA}"
        )
    if model_contract.get("model_identifier") != REVIEWER_MODEL_IDENTIFIER:
        raise AnalysisInputError(
            f"frozen reviewer model identifier must equal {REVIEWER_MODEL_IDENTIFIER}"
        )
    if model_contract.get("timeout_seconds") != REVIEWER_TIMEOUT_SECONDS:
        raise AnalysisInputError(
            f"frozen reviewer timeout must equal {REVIEWER_TIMEOUT_SECONDS}"
        )

    command_contract = _load_json(command_path)
    if not isinstance(command_contract, dict):
        raise AnalysisInputError("frozen review command must be a JSON object")
    if command_contract.get("schema") != REVIEW_COMMAND_SCHEMA:
        raise AnalysisInputError(
            f"review command schema must equal {REVIEW_COMMAND_SCHEMA}"
        )
    if (
        command_contract.get("command_identifier")
        != REVIEWER_COMMAND_IDENTIFIER
    ):
        raise AnalysisInputError(
            "frozen reviewer command identifier must equal "
            f"{REVIEWER_COMMAND_IDENTIFIER}"
        )
    command = command_contract.get("command")
    if (
        not isinstance(command, list)
        or not command
        or any(not isinstance(part, str) or not part for part in command)
    ):
        raise AnalysisInputError("frozen review command must be a nonempty string list")
    if provenance["command"] != command:
        raise AnalysisInputError(
            "review provenance command does not match frozen review command"
        )

    if provenance["reviewer_model_identifier"] != REVIEWER_MODEL_IDENTIFIER:
        raise AnalysisInputError(
            "review provenance reviewer_model_identifier does not match frozen model"
        )
    if (
        provenance["reviewer_command_identifier"]
        != REVIEWER_COMMAND_IDENTIFIER
    ):
        raise AnalysisInputError(
            "review provenance reviewer_command_identifier does not match frozen command"
        )

    decisions_resolved = validity_review_path.resolve(strict=True)
    if provenance["decisions_path"] != str(decisions_resolved):
        raise AnalysisInputError(
            "review provenance decisions_path does not match supplied validity review"
        )
    decisions_sha = _required_sha256(validity_review_path, "decisions_sha256")
    if provenance["decisions_sha256"] != decisions_sha:
        raise AnalysisInputError(
            "review provenance decisions_sha256 does not match supplied validity review"
        )

    artifact_hashes = {
        "frozen_review_prompt_sha256": _required_sha256(
            prompt_path, "frozen_review_prompt_sha256"
        ),
        "frozen_review_model_contract_sha256": _required_sha256(
            model_contract_path, "frozen_review_model_contract_sha256"
        ),
        "frozen_review_command_sha256": _required_sha256(
            command_path, "frozen_review_command_sha256"
        ),
    }
    for field, current_hash in artifact_hashes.items():
        if provenance[field] != current_hash:
            raise AnalysisInputError(
                f"review provenance {field} does not match current frozen artifact"
            )

    manifest_sha = _required_sha256(
        manifest_path, "review_bundle_manifest_sha256"
    )
    if provenance["review_bundle_manifest_unchanged"] is not True:
        raise AnalysisInputError(
            "review provenance must record review_bundle_manifest_unchanged=true"
        )
    if not (
        provenance["review_bundle_manifest_sha256_before"]
        == provenance["review_bundle_manifest_sha256_after"]
        == manifest_sha
    ):
        raise AnalysisInputError(
            "review bundle manifest before/after/current hashes must all match"
        )

    for field in (
        "decisions_sha256",
        "frozen_review_prompt_sha256",
        "frozen_review_model_contract_sha256",
        "frozen_review_command_sha256",
        "review_bundle_manifest_sha256_before",
        "review_bundle_manifest_sha256_after",
        "events_sha256",
        "event_receipts_sha256",
        "stderr_sha256",
    ):
        if not _is_sha256(provenance[field]):
            raise AnalysisInputError(
                f"review provenance {field} must be a lowercase SHA-256"
            )
    for field in (
        "started_at",
        "finished_at",
        "first_event_at",
        "last_event_at",
        "final_response_received_at",
    ):
        if not isinstance(provenance[field], str) or not provenance[field]:
            raise AnalysisInputError(
                f"review provenance {field} must be a nonempty string"
            )
    _positive_finite_number(
        provenance["wall_seconds"], "review provenance wall_seconds"
    )
    for field in (
        "first_event_elapsed_seconds",
        "last_event_elapsed_seconds",
        "final_response_elapsed_seconds",
    ):
        _positive_finite_number(
            provenance[field], f"review provenance {field}"
        )
    for field in ("event_count", "model_turns", "tool_call_total"):
        if not _is_nonnegative_int(provenance[field]):
            raise AnalysisInputError(
                f"review provenance {field} must be a nonnegative integer"
            )
    if not isinstance(provenance["provider_usage_events"], list):
        raise AnalysisInputError(
            "review provenance provider_usage_events must be a list"
        )
    if not isinstance(provenance["provider_usage_totals"], dict):
        raise AnalysisInputError(
            "review provenance provider_usage_totals must be an object"
        )
    if not isinstance(provenance["tool_call_counts"], dict):
        raise AnalysisInputError(
            "review provenance tool_call_counts must be an object"
        )
    if not isinstance(provenance["actual_tool_commands"], list):
        raise AnalysisInputError(
            "review provenance actual_tool_commands must be a list"
        )
    if provenance["validation_errors"] != []:
        raise AnalysisInputError(
            "successful review provenance validation_errors must be empty"
        )

    return {
        "path": str(provenance_path),
        "sha256": _required_sha256(provenance_path, "review_provenance"),
        "status": "ok",
        "reviewer_model_identifier": REVIEWER_MODEL_IDENTIFIER,
        "reviewer_command_identifier": REVIEWER_COMMAND_IDENTIFIER,
        "decisions_path": str(decisions_resolved),
        "decisions_sha256": decisions_sha,
        "frozen_artifacts": {
            "review_prompt": {
                "path": str(prompt_path),
                "sha256": artifact_hashes["frozen_review_prompt_sha256"],
            },
            "review_model_contract": {
                "path": str(model_contract_path),
                "sha256": artifact_hashes[
                    "frozen_review_model_contract_sha256"
                ],
            },
            "review_command": {
                "path": str(command_path),
                "sha256": artifact_hashes["frozen_review_command_sha256"],
            },
            "review_bundle_manifest": {
                "path": str(manifest_path),
                "sha256_before": manifest_sha,
                "sha256_after": manifest_sha,
                "sha256_current": manifest_sha,
                "unchanged": True,
            },
        },
    }


def _parse_run_record(
    path: Path,
    schedule_entry: Mapping[str, Any],
    independently_valid: bool,
) -> dict[str, Any]:
    document = _load_json(path)
    if not isinstance(document, dict):
        raise AnalysisInputError(f"run record must be a JSON object: {path}")

    metadata = document.get("run")
    if not isinstance(metadata, dict):
        raise AnalysisInputError(f"run record lacks run metadata: {path}")
    for field in SCHEDULE_FIELDS:
        if metadata.get(field) != schedule_entry[field]:
            raise AnalysisInputError(
                f"{path}: run.{field} does not match frozen schedule"
            )

    status = document.get("status")
    if not isinstance(status, str) or not status:
        raise AnalysisInputError(f"{path}: status must be a nonempty string")
    if status.lower() not in TERMINAL_STATUSES:
        raise AnalysisInputError(
            f"{path}: status is not one of the frozen terminal statuses "
            f"{TERMINAL_STATUSES}"
        )
    if "exit_code" not in document:
        raise AnalysisInputError(f"{path}: missing exit_code")
    exit_code = document["exit_code"]
    if exit_code is not None and (
        not isinstance(exit_code, int) or isinstance(exit_code, bool)
    ):
        raise AnalysisInputError(f"{path}: exit_code must be an integer or null")
    if status.lower() == "ok" and exit_code != 0:
        raise AnalysisInputError(f"{path}: ok status requires exit_code 0")

    usage = document.get("provider_usage_totals")
    if not isinstance(usage, dict):
        raise AnalysisInputError(f"{path}: missing provider_usage_totals")
    for field in ("input_tokens", "output_tokens"):
        if field not in usage or not _is_nonnegative_int(usage[field]):
            raise AnalysisInputError(
                f"{path}: provider_usage_totals.{field} must be a nonnegative integer"
            )
    provider_total = usage["input_tokens"] + usage["output_tokens"]
    if provider_total <= 0:
        raise AnalysisInputError(f"{path}: provider-total tokens must be positive")
    if "total_tokens" in usage:
        if not _is_nonnegative_int(usage["total_tokens"]):
            raise AnalysisInputError(
                f"{path}: provider_usage_totals.total_tokens must be a nonnegative integer"
            )
        if usage["total_tokens"] != provider_total:
            raise AnalysisInputError(
                f"{path}: provider total must equal input_tokens + output_tokens"
            )

    status_ok = status.lower() == "ok"
    effective_valid = independently_valid and status_ok
    reported_time = document.get("final_response_elapsed_seconds")
    if effective_valid:
        reported_time_float = _positive_finite_number(
            reported_time, f"{path}: final_response_elapsed_seconds"
        )
        if reported_time_float > TIMEOUT_SECONDS:
            raise AnalysisInputError(
                f"{path}: valid final-answer time exceeds the frozen timeout"
            )
        effective_time = reported_time_float
    else:
        if reported_time is None:
            reported_time_float = None
        else:
            reported_time_float = _positive_finite_number(
                reported_time, f"{path}: final_response_elapsed_seconds"
            )
        effective_time = TIMEOUT_SECONDS

    return {
        **{field: schedule_entry[field] for field in SCHEDULE_FIELDS},
        "status": status,
        "exit_code": exit_code,
        "independent_review_valid": independently_valid,
        "effective_valid": effective_valid,
        "penalized_time": not effective_valid,
        "reported_final_answer_seconds": reported_time_float,
        "effective_final_answer_seconds": effective_time,
        "provider_input_tokens": usage["input_tokens"],
        "provider_output_tokens": usage["output_tokens"],
        "provider_total_tokens": provider_total,
        "cached_input_tokens_detail": usage.get("cached_input_tokens"),
        "reasoning_output_tokens_detail": usage.get("reasoning_output_tokens"),
        "run_record_sha256": _sha256(path),
    }


def _mean(values: Iterable[float]) -> float:
    return float(np.mean(np.asarray(list(values), dtype=np.float64)))


def _median(values: Iterable[float]) -> float:
    return float(np.median(np.asarray(list(values), dtype=np.float64)))


def _arm_descriptive(records: Sequence[Mapping[str, Any]], arm: str) -> dict[str, Any]:
    selected = [record for record in records if record["arm"] == arm]
    times = [record["effective_final_answer_seconds"] for record in selected]
    tokens = [record["provider_total_tokens"] for record in selected]
    return {
        "n": len(selected),
        "independently_valid_count": sum(
            bool(record["effective_valid"]) for record in selected
        ),
        "penalized_time_count": sum(bool(record["penalized_time"]) for record in selected),
        "effective_final_answer_seconds": {
            "mean": _mean(times),
            "raw_median": _median(times),
        },
        "provider_total_tokens": {
            "mean": _mean(tokens),
            "raw_median": _median(tokens),
            "sum": int(sum(tokens)),
        },
    }


def _stratum_descriptive(
    blocks: Sequence[Mapping[str, Any]], profile_first: bool
) -> dict[str, Any]:
    selected = [
        block for block in blocks if bool(block["profile_first"]) is profile_first
    ]
    time_ratios = np.asarray([block["time_ratio"] for block in selected], dtype=np.float64)
    token_ratios = np.asarray(
        [block["provider_token_ratio"] for block in selected], dtype=np.float64
    )
    return {
        "n_blocks": len(selected),
        "block_ids": [block["block_id"] for block in selected],
        "time": {
            "theta_median_log_ratio": float(np.median(np.log(time_ratios))),
            "ratio_exp_theta": float(np.exp(np.median(np.log(time_ratios)))),
            "arithmetic_mean_ratio": float(np.mean(time_ratios)),
            "raw_median_ratio": float(np.median(time_ratios)),
        },
        "provider_tokens": {
            "theta_median_log_ratio": float(np.median(np.log(token_ratios))),
            "ratio_exp_theta": float(np.exp(np.median(np.log(token_ratios)))),
            "arithmetic_mean_ratio": float(np.mean(token_ratios)),
            "raw_median_ratio": float(np.median(token_ratios)),
        },
        "validity": {
            PROFILE_ARM: sum(block["profile"]["effective_valid"] for block in selected),
            RAW_ARM: sum(block["raw_operations"]["effective_valid"] for block in selected),
        },
    }


def _endpoint_result(
    name: str,
    log_ratios: np.ndarray,
    bootstrap_thetas: np.ndarray,
) -> dict[str, Any]:
    theta = float(np.median(log_ratios))
    lower_theta = no_interpolation_order_statistic(
        bootstrap_thetas, UNADJUSTED_LOWER_P
    )
    upper_theta = no_interpolation_order_statistic(
        bootstrap_thetas, UNADJUSTED_UPPER_P
    )
    return {
        "name": name,
        "theta_median_log_ratio": theta,
        "ratio_exp_theta": float(math.exp(theta)),
        "unadjusted_percentile_95_interval": {
            "lower": float(math.exp(lower_theta)),
            "upper": float(math.exp(upper_theta)),
            "lower_p": UNADJUSTED_LOWER_P,
            "upper_p": UNADJUSTED_UPPER_P,
            "order_statistic": "ceil(p * 100000), 1-indexed, no interpolation",
        },
        "bonferroni_one_sided_97_5_percent_upper": float(math.exp(upper_theta)),
    }


def analyze(
    schedule_path: Path,
    runs_root: Path,
    validity_review_path: Path,
    alias_map_path: Path,
    review_provenance_path: Path,
) -> dict[str, Any]:
    """Validate all frozen inputs and return the complete analysis record."""

    schedule = _parse_schedule(schedule_path)
    scheduled_run_ids = {entry["run_id"] for entry in schedule}
    alias_map = _parse_alias_map(alias_map_path, scheduled_run_ids)
    review_by_case = _parse_validity_review(
        validity_review_path, set(alias_map.keys())
    )
    review_provenance = _verify_review_provenance(
        review_provenance_path, validity_review_path
    )
    validity_by_run = {
        run_id: review_by_case[case_id] for case_id, run_id in alias_map.items()
    }

    records: list[dict[str, Any]] = []
    run_file_hashes: dict[str, str] = {}
    for entry in schedule:
        path = runs_root / entry["run_id"] / "run.json"
        record = _parse_run_record(path, entry, validity_by_run[entry["run_id"]])
        records.append(record)
        run_file_hashes[entry["run_id"]] = record["run_record_sha256"]

    blocks: list[dict[str, Any]] = []
    for block_index in range(1, BLOCK_COUNT + 1):
        scheduled_block = [
            entry for entry in schedule if entry["block_index"] == block_index
        ]
        block_id = scheduled_block[0]["block_id"]
        block_records = [record for record in records if record["block_id"] == block_id]
        profile = next(record for record in block_records if record["arm"] == PROFILE_ARM)
        raw = next(record for record in block_records if record["arm"] == RAW_ARM)
        time_ratio = (
            profile["effective_final_answer_seconds"]
            / raw["effective_final_answer_seconds"]
        )
        token_ratio = (
            profile["provider_total_tokens"] / raw["provider_total_tokens"]
        )
        blocks.append(
            {
                "block_id": block_id,
                "block_index": block_index,
                "profile_first": profile["within_block_order"] == 1,
                "profile": profile,
                "raw_operations": raw,
                "time_ratio": float(time_ratio),
                "time_log_ratio": float(math.log(time_ratio)),
                "provider_token_ratio": float(token_ratio),
                "provider_token_log_ratio": float(math.log(token_ratio)),
            }
        )

    time_logs = np.asarray([block["time_log_ratio"] for block in blocks])
    token_logs = np.asarray([block["provider_token_log_ratio"] for block in blocks])
    boot_time, boot_tokens, indices = bootstrap_paired_thetas(time_logs, token_logs)
    time_endpoint = _endpoint_result("T_profile_over_raw", time_logs, boot_time)
    token_endpoint = _endpoint_result(
        "K_profile_over_raw_provider_total_tokens", token_logs, boot_tokens
    )

    profile_valid = sum(
        record["effective_valid"] for record in records if record["arm"] == PROFILE_ARM
    )
    raw_valid = sum(
        record["effective_valid"] for record in records if record["arm"] == RAW_ARM
    )
    time_upper = time_endpoint["bonferroni_one_sided_97_5_percent_upper"]
    token_upper = token_endpoint["bonferroni_one_sided_97_5_percent_upper"]
    clauses = {
        "both_arms_valid_at_least_18_of_20": (
            profile_valid >= MIN_VALID_PER_ARM
            and raw_valid >= MIN_VALID_PER_ARM
        ),
        "profile_valid_count_not_lower_than_raw": profile_valid >= raw_valid,
        "time_upper_strictly_below_1_00": time_upper < 1.0,
        "provider_token_upper_at_or_below_1_00": token_upper <= 1.0,
    }
    rank_1_records = {
        arm: next(
            record
            for record in records
            if record["arm"] == arm and record["arm_rank"] == 1
        )
        for arm in ARMS
    }
    rank_1_validity = {
        arm: bool(record["effective_valid"])
        for arm, record in rank_1_records.items()
    }
    analyst_efficiency_pass = all(clauses.values())
    rank_1_policy_pass = all(rank_1_validity.values())

    index_bytes = indices.astype("<i8", copy=False).tobytes(order="C")
    return {
        "analysis": {
            "name": "experiment-002 confirmatory analyst-efficiency",
            "status": "PASS" if analyst_efficiency_pass else "FAIL",
            "bootstrap": {
                "generator": "numpy.random.Generator(PCG64)",
                "seed": BOOTSTRAP_SEED,
                "resamples": BOOTSTRAP_RESAMPLES,
                "blocks_per_resample": BLOCK_COUNT,
                "paired_same_indices_for_time_and_tokens": True,
                "indices_sha256_little_endian_int64": hashlib.sha256(
                    index_bytes
                ).hexdigest(),
                "simultaneous_familywise_confidence": 0.95,
                "bonferroni_one_sided_endpoint_percentile": 0.975,
            },
            "invalid_or_non_ok_time_penalty_seconds": TIMEOUT_SECONDS,
            "provider_total_definition": "input_tokens + output_tokens",
        },
        "input_provenance": {
            "schedule": {
                "path": str(schedule_path),
                "sha256": _sha256(schedule_path),
            },
            "validity_review": {
                "path": str(validity_review_path),
                "sha256": _sha256(validity_review_path),
                "joined_only_through_case_to_run_alias_map": True,
                "case_count": len(review_by_case),
            },
            "review_provenance": review_provenance,
            "alias_map": {
                "path": str(alias_map_path),
                "sha256": _sha256(alias_map_path),
                "bijective_and_complete": True,
            },
            "run_record_sha256_by_run_id": run_file_hashes,
        },
        "validity": {
            PROFILE_ARM: profile_valid,
            RAW_ARM: raw_valid,
            "required_per_arm": MIN_VALID_PER_ARM,
        },
        "confirmatory_endpoints": {
            "time": time_endpoint,
            "provider_tokens": token_endpoint,
        },
        "confirmatory_gate": {
            "clauses": clauses,
            "pass": analyst_efficiency_pass,
            "failure_is_valid_negative": not analyst_efficiency_pass,
        },
        "rank_1_policy_gate": {
            "selected_runs": {
                arm: {
                    "run_id": rank_1_records[arm]["run_id"],
                    "valid": rank_1_validity[arm],
                }
                for arm in ARMS
            },
            "no_substitution": True,
            "pass": rank_1_policy_pass,
        },
        "downstream_readiness": {
            "requires_confirmatory_analyst_efficiency_pass": analyst_efficiency_pass,
            "requires_both_frozen_rank_1_outputs_valid": rank_1_policy_pass,
            "pass": analyst_efficiency_pass and rank_1_policy_pass,
            "downstream_forbidden": not (
                analyst_efficiency_pass and rank_1_policy_pass
            ),
        },
        "sensitivity_only_post_experiment_001_adaptation": {
            "cannot_determine_confirmatory_gate_or_paper_admission": True,
            "time_upper_strictly_below_0_90": time_upper < 0.90,
            "provider_token_upper_at_or_below_1_05": token_upper <= 1.05,
            "both_alternative_thresholds_hold": time_upper < 0.90
            and token_upper <= 1.05,
            "both_alternative_thresholds_and_confirmatory_validity_hold": (
                profile_valid >= MIN_VALID_PER_ARM
                and raw_valid >= MIN_VALID_PER_ARM
                and profile_valid >= raw_valid
                and time_upper < 0.90
                and token_upper <= 1.05
            ),
        },
        "descriptive": {
            "arms": {
                PROFILE_ARM: _arm_descriptive(records, PROFILE_ARM),
                RAW_ARM: _arm_descriptive(records, RAW_ARM),
            },
            "paired_ratios": {
                "time": {
                    "arithmetic_mean": _mean(block["time_ratio"] for block in blocks),
                    "raw_median": _median(block["time_ratio"] for block in blocks),
                },
                "provider_tokens": {
                    "arithmetic_mean": _mean(
                        block["provider_token_ratio"] for block in blocks
                    ),
                    "raw_median": _median(
                        block["provider_token_ratio"] for block in blocks
                    ),
                },
            },
            "within_block_order_strata": {
                "profile_first": _stratum_descriptive(blocks, True),
                "raw_first": _stratum_descriptive(blocks, False),
            },
        },
        "individual_blocks": blocks,
    }


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--schedule", required=True, type=Path)
    parser.add_argument("--runs-root", required=True, type=Path)
    parser.add_argument("--validity-review", required=True, type=Path)
    parser.add_argument("--alias-map", required=True, type=Path)
    parser.add_argument("--review-provenance", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    result = analyze(
        schedule_path=args.schedule,
        runs_root=args.runs_root,
        validity_review_path=args.validity_review,
        alias_map_path=args.alias_map,
        review_provenance_path=args.review_provenance,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as handle:
        json.dump(result, handle, indent=2, sort_keys=True, allow_nan=False)
        handle.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
