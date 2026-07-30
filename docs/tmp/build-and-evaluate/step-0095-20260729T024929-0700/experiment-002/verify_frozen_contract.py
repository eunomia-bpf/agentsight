#!/usr/bin/env python3
"""Create or verify the fail-closed experiment-002 analyst-stage contract."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import re
from pathlib import Path
from typing import Any

import run_analysts
import run_all_analysts
import run_output_review
import freeze_rank1_policies
import verify_analyst_packages


EXPERIMENT = Path(__file__).resolve().parent
STATIC_FILES = (
    "experiment-plan.md",
    "plan-review-round-1.md",
    "plan-review-round-2.md",
    "plan-review-round-3.md",
    "prepare_analyst_packages.py",
    "test_prepare_analyst_packages.py",
    "verify_analyst_packages.py",
    "test_analyst_stage.py",
    "prepare_review_bundle.py",
    "test_prepare_review_bundle.py",
    "run_output_review.py",
    "test_run_output_review.py",
    "run_all_analysts.py",
    "test_run_all_analysts.py",
    "freeze_rank1_policies.py",
    "test_freeze_rank1_policies.py",
    "analyze_analyst_efficiency.py",
    "test_analyze_analyst_efficiency.py",
    "run_analysts.py",
    "verify_frozen_contract.py",
    "source-records/experiment-001-preparation-report.json",
    "preparation-report.json",
    "analyst-packages/PROFILE/README.md",
    (
        "analyst-packages/PROFILE/"
        "agentreward-338-pairs-bad-minus-good.operations.pb.gz"
    ),
    "analyst-packages/RAW-OPERATIONS/README.md",
    "analyst-packages/RAW-OPERATIONS/samples.jsonl",
    "analyst/order.json",
    "analyst/output.schema.json",
    "analyst/model-contract.json",
    "analyst/commands.json",
    "analyst/preparation.json",
    "analyst/review-alias-map.private.json",
    "analyst/review-output.schema.json",
    "analyst/review-preparation.private.json",
    "analyst/review-prompt.txt",
    "analyst/review-model-contract.json",
    "analyst/review-command.json",
    "analyst/batch-command.json",
    "analyst/analysis-command.json",
    "analyst/policy-freeze-command.json",
)


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def required_files() -> tuple[str, ...]:
    prompts = tuple(
        f"analyst/prompts/{run['run_id']}.txt"
        for run in run_analysts.registered_runs()
    )
    return STATIC_FILES + prompts


def _schedule_semantics() -> dict[str, Any]:
    order_path = EXPERIMENT / "analyst" / "order.json"
    commands_path = EXPERIMENT / "analyst" / "commands.json"
    model_path = EXPERIMENT / "analyst" / "model-contract.json"
    preparation_path = EXPERIMENT / "analyst" / "preparation.json"
    alias_path = EXPERIMENT / "analyst" / "review-alias-map.private.json"
    review_schema_path = EXPERIMENT / "analyst" / "review-output.schema.json"
    review_preparation_path = (
        EXPERIMENT / "analyst" / "review-preparation.private.json"
    )
    review_prompt_path = EXPERIMENT / "analyst" / "review-prompt.txt"
    review_model_path = (
        EXPERIMENT / "analyst" / "review-model-contract.json"
    )
    review_command_path = EXPERIMENT / "analyst" / "review-command.json"
    batch_command_path = EXPERIMENT / "analyst" / "batch-command.json"
    analysis_command_path = EXPERIMENT / "analyst" / "analysis-command.json"
    policy_freeze_command_path = (
        EXPERIMENT / "analyst" / "policy-freeze-command.json"
    )
    order = json.loads(order_path.read_text(encoding="utf-8"))
    commands = json.loads(commands_path.read_text(encoding="utf-8"))
    model = json.loads(model_path.read_text(encoding="utf-8"))
    preparation = json.loads(preparation_path.read_text(encoding="utf-8"))
    alias_map = json.loads(alias_path.read_text(encoding="utf-8"))
    review_schema = json.loads(review_schema_path.read_text(encoding="utf-8"))
    review_preparation = json.loads(
        review_preparation_path.read_text(encoding="utf-8")
    )
    review_model = json.loads(review_model_path.read_text(encoding="utf-8"))
    review_command = json.loads(
        review_command_path.read_text(encoding="utf-8")
    )
    batch_command = json.loads(
        batch_command_path.read_text(encoding="utf-8")
    )
    analysis_command = json.loads(
        analysis_command_path.read_text(encoding="utf-8")
    )
    policy_freeze_command = json.loads(
        policy_freeze_command_path.read_text(encoding="utf-8")
    )
    expected = run_analysts.registered_runs()
    rows = order.get("runs")
    if not isinstance(rows, list) or len(rows) != 40:
        raise RuntimeError("frozen schedule must contain exactly 40 runs")
    if order.get("seed") != run_analysts.ORDER_SEED:
        raise RuntimeError("frozen schedule seed changed")

    identity_fields = (
        "run_id",
        "arm",
        "block_id",
        "block_index",
        "within_block_order",
        "arm_rank",
        "position",
    )
    if [
        {key: row[key] for key in identity_fields}
        for row in rows
    ] != expected:
        raise RuntimeError("frozen schedule differs from deterministic schedule")
    if len({row["run_id"] for row in rows}) != 40 or any(
        re.fullmatch(r"run-[0-9a-f]{12}", row["run_id"]) is None
        for row in rows
    ):
        raise RuntimeError("run identifiers are not unique and opaque")
    if len({row["block_id"] for row in rows}) != 20 or any(
        re.fullmatch(r"block-[0-9a-f]{12}", row["block_id"]) is None
        for row in rows
    ):
        raise RuntimeError("block identifiers are not unique and opaque")
    if sorted(row["position"] for row in rows) != list(range(1, 41)):
        raise RuntimeError("global schedule positions are not exactly 1..40")

    first_counts = {"PROFILE": 0, "RAW-OPERATIONS": 0}
    rank_1: dict[str, str] = {}
    for block_index in range(1, 21):
        block = [row for row in rows if row["block_index"] == block_index]
        if (
            len(block) != 2
            or {row["arm"] for row in block}
            != {"PROFILE", "RAW-OPERATIONS"}
            or sorted(row["within_block_order"] for row in block) != [1, 2]
            or {row["arm_rank"] for row in block} != {block_index}
        ):
            raise RuntimeError(f"invalid temporal block {block_index}")
        first = next(row for row in block if row["within_block_order"] == 1)
        first_counts[first["arm"]] += 1
    if first_counts != {"PROFILE": 10, "RAW-OPERATIONS": 10}:
        raise RuntimeError("within-block first-arm assignment is not 10/10")
    for arm in ("PROFILE", "RAW-OPERATIONS"):
        ranks = sorted(row["arm_rank"] for row in rows if row["arm"] == arm)
        if ranks != list(range(1, 21)):
            raise RuntimeError(f"{arm} ranks are not exactly 1..20")
        rank_1[arm] = next(
            row["run_id"]
            for row in rows
            if row["arm"] == arm and row["arm_rank"] == 1
        )
    if order.get("rank_1") != rank_1:
        raise RuntimeError("rank-1 selections changed")

    command_rows = commands.get("runs")
    if not isinstance(command_rows, list) or len(command_rows) != 40:
        raise RuntimeError("literal command record must contain exactly 40 runs")
    frozen_commands = {row["run_id"]: row["command"] for row in command_rows}
    if set(frozen_commands) != {row["run_id"] for row in rows}:
        raise RuntimeError("literal command run set differs from schedule")
    for row in rows:
        prompt_path = Path(row["prompt_file"])
        if (
            prompt_path
            != (
                EXPERIMENT / "analyst" / "prompts" / f"{row['run_id']}.txt"
            ).resolve()
            or prompt_path.read_text(encoding="utf-8")
            != run_analysts.prompt_for(row["arm"]) + "\n"
            or sha256_file(prompt_path) != row["prompt_sha256"]
        ):
            raise RuntimeError(f"prompt changed for {row['run_id']}")
        if frozen_commands[row["run_id"]] != run_analysts.command_for(row):
            raise RuntimeError(f"literal command changed for {row['run_id']}")

    if model != run_analysts.model_contract():
        raise RuntimeError("model/timeout/tool contract changed")
    expected_alias_map = run_analysts.review_alias_assignment(rows)
    if alias_map != expected_alias_map:
        raise RuntimeError("private review alias assignment changed")
    cases = alias_map.get("cases")
    case_ids = [case["case_id"] for case in cases]
    mapped_run_ids = [case["run_id"] for case in cases]
    if (
        len(case_ids) != 40
        or len(set(case_ids)) != 40
        or len(set(mapped_run_ids)) != 40
        or set(mapped_run_ids) != {row["run_id"] for row in rows}
        or any(
            re.fullmatch(r"case-[0-9a-f]{12}", case_id) is None
            for case_id in case_ids
        )
    ):
        raise RuntimeError("private review aliases are not a complete opaque bijection")
    if review_schema != run_analysts.review_output_schema(case_ids):
        raise RuntimeError("public blind-review decision schema changed")
    if set(
        review_schema["properties"]["cases"]["items"]["properties"]
    ) != {"case_id", *run_analysts.REVIEW_DECISION_FIELDS}:
        raise RuntimeError("public review schema exposes fields beyond case decisions")
    expected_review_preparation = {
        "status": "PASS",
        "seed": run_analysts.REVIEW_ALIAS_SEED,
        "case_count": 40,
        "bijection": True,
        "alias_map_sha256": sha256_file(alias_path),
        "output_schema_sha256": sha256_file(review_schema_path),
        "bundle_creation_rule": "only_after_40_terminal_run_records",
        "public_decision_key": "case_id_only",
        "public_decision_fields": list(run_analysts.REVIEW_DECISION_FIELDS),
    }
    for key, value in expected_review_preparation.items():
        if review_preparation.get(key) != value:
            raise RuntimeError(f"blind-review preparation invariant changed: {key}")
    if (
        review_prompt_path.read_text(encoding="utf-8")
        != run_output_review.REVIEW_PROMPT + "\n"
        or review_model != run_output_review.model_contract()
        or review_command != run_output_review.command_document()
    ):
        raise RuntimeError("frozen output-review prompt/model/command changed")
    if (
        review_model.get("model_identifier") != "gpt-5.6-sol"
        or review_model.get("timeout_seconds") != 1800
        or review_model.get("output_schema")
        != str(run_output_review.INTERNAL_OUTPUT_SCHEMA_PATH.resolve())
        or review_model.get("output_schema_expected_sha256")
        != sha256_file(EXPERIMENT / "analyst" / "review-output.schema.json")
    ):
        raise RuntimeError("output-review model/schema contract changed")
    if batch_command != run_all_analysts.command_document():
        raise RuntimeError("frozen no-interim analyst batch command changed")
    expected_analysis_command = {
        "schema": "agentsight.utility2.analyst-analysis-command.v1",
        "command_identifier": (
            freeze_rank1_policies.ANALYSIS_COMMAND_IDENTIFIER
        ),
        "command": freeze_rank1_policies.analysis_command(),
    }
    expected_policy_freeze_command = {
        "schema": "agentsight.utility2.rank1-policy-freeze-command.v1",
        "command_identifier": (
            freeze_rank1_policies.FREEZE_COMMAND_IDENTIFIER
        ),
        "command": freeze_rank1_policies.freeze_command(),
    }
    if analysis_command != expected_analysis_command:
        raise RuntimeError("frozen analyst analysis command changed")
    if policy_freeze_command != expected_policy_freeze_command:
        raise RuntimeError("frozen rank-1 policy-freeze command changed")
    expected_preparation = {
        "status": "PASS",
        "block_count": 20,
        "run_count": 40,
        "arm_counts": {"PROFILE": 20, "RAW-OPERATIONS": 20},
        "first_arm_counts": {"PROFILE": 10, "RAW-OPERATIONS": 10},
        "rank_1": rank_1,
        "model": "gpt-5.6-sol",
        "timeout_seconds": 900,
        "model_calls_made": 0,
    }
    for key, value in expected_preparation.items():
        if preparation.get(key) != value:
            raise RuntimeError(f"analyst preparation invariant changed: {key}")
    if (
        preparation["order_sha256"] != sha256_file(order_path)
        or preparation["commands_sha256"] != sha256_file(commands_path)
        or preparation["schema_sha256"]
        != sha256_file(EXPERIMENT / "analyst" / "output.schema.json")
        or preparation["model_contract_sha256"] != sha256_file(model_path)
        or preparation["review_alias_map_sha256"] != sha256_file(alias_path)
        or preparation["review_output_schema_sha256"]
        != sha256_file(review_schema_path)
    ):
        raise RuntimeError("analyst preparation hashes are stale")

    runs_dir = EXPERIMENT / "analyst" / "runs"
    terminal_count = 0
    if runs_dir.is_dir():
        for row in rows:
            record_path = runs_dir / row["run_id"] / "run.json"
            if record_path.is_file():
                record = json.loads(record_path.read_text(encoding="utf-8"))
                if record.get("status") in run_analysts.TERMINAL_STATUSES:
                    terminal_count += 1
    forbidden_summaries = (
        EXPERIMENT / "analyst" / "analyst-summary.json",
        EXPERIMENT / "analyst" / "efficiency-summary.json",
    )
    if terminal_count < 40 and any(path.exists() for path in forbidden_summaries):
        raise RuntimeError("interim arm-level summary exists before 40 terminal runs")

    return {
        "block_count": 20,
        "run_count": 40,
        "arm_counts": {"PROFILE": 20, "RAW-OPERATIONS": 20},
        "first_arm_counts": first_counts,
        "rank_1": rank_1,
        "model": model["model"],
        "timeout_seconds": model["timeout_seconds"],
        "review_case_count": 40,
        "review_alias_bijection": True,
        "reviewer_model": review_model["model_identifier"],
        "reviewer_timeout_seconds": review_model["timeout_seconds"],
        "reviewer_command_identifier": review_command["command_identifier"],
        "batch_command_identifier": batch_command["command_identifier"],
        "analysis_command_identifier": analysis_command["command_identifier"],
        "policy_freeze_command_identifier": policy_freeze_command[
            "command_identifier"
        ],
    }


def assert_semantics() -> dict[str, Any]:
    package = verify_analyst_packages.verify_packages()
    schedule = _schedule_semantics()
    return {
        "tuple_count": package["tuple_equivalence"]["profile_tuple_count"],
        "tuple_unique_count": package["tuple_equivalence"][
            "profile_unique_tuple_count"
        ],
        "tuple_multiset_equal": package["tuple_equivalence"][
            "complete_multiset_equal"
        ],
        "mass": package["mass_conservation"]["profile"],
        "schedule": schedule,
    }


def verify_file_hashes(
    base: Path, registered: dict[str, str], expected_names: set[str]
) -> list[dict[str, str | None]]:
    if set(registered) != expected_names:
        raise RuntimeError("registered frozen-file set mismatch")
    changes: list[dict[str, str | None]] = []
    for relative, expected in registered.items():
        path = base / relative
        actual = sha256_file(path) if path.is_file() else None
        if actual != expected:
            changes.append(
                {"path": relative, "expected": expected, "actual": actual}
            )
    return changes


def create_contract(output: Path) -> dict[str, Any]:
    semantics = assert_semantics()
    hashes: dict[str, str] = {}
    for relative in required_files():
        path = EXPERIMENT / relative
        if not path.is_file() or path.is_symlink():
            raise FileNotFoundError(path)
        hashes[relative] = sha256_file(path)
    payload = {
        "schema": "agentsight.utility2.frozen-contract.v1",
        "stage": "analyst",
        "created_at": utc_now(),
        "experiment": str(EXPERIMENT.resolve()),
        "semantics": semantics,
        "files": hashes,
    }
    output.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return payload


def verify_contract(contract_path: Path, output: Path) -> dict[str, Any]:
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    if (
        contract.get("stage") != "analyst"
        or contract.get("experiment") != str(EXPERIMENT.resolve())
    ):
        raise RuntimeError("wrong experiment or contract stage")
    current_semantics = assert_semantics()
    if current_semantics != contract.get("semantics"):
        raise RuntimeError("semantic invariants changed after freeze")
    changes = verify_file_hashes(
        EXPERIMENT,
        contract.get("files", {}),
        set(required_files()),
    )
    if changes:
        raise RuntimeError(f"frozen files changed: {changes}")
    record = {
        "schema": "agentsight.utility2.contract-verification.v1",
        "status": "PASS",
        "stage": "analyst",
        "checked_at": utc_now(),
        "contract": str(contract_path.resolve()),
        "contract_sha256": sha256_file(contract_path),
        "file_count": len(contract["files"]),
        "semantic_invariants": current_semantics,
    }
    output.write_text(
        json.dumps(record, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return record


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    actions = parser.add_mutually_exclusive_group(required=True)
    actions.add_argument("--create", action="store_true")
    actions.add_argument("--verify", action="store_true")
    parser.add_argument("--contract", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.create:
        result = create_contract(args.output)
    else:
        if args.contract is None:
            raise SystemExit("--verify requires --contract")
        result = verify_contract(args.contract, args.output)
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
