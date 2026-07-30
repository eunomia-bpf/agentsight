#!/usr/bin/env python3
"""Create or verify a fail-closed stage-specific execution contract."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

EXPERIMENT = Path(__file__).resolve().parent
REPO = EXPERIMENT.parents[4]
TOOL_SANDBOX = REPO / ".agentsight" / "external" / "ToolSandbox"
TOOL_SANDBOX_COMMIT = "165848b9a78cead7ca7fe7c89c688b58e6501219"

COMMON_FILES = (
    "experiment-plan.md",
    "plan-review-round-1.md",
    "plan-review-round-2.md",
    "dependency-screen-amendment.md",
    "prepare_analyst_packages.py",
    "test_prepare_analyst_packages.py",
    "preparation-report.json",
    "analyst-packages/PROFILE/README.md",
    "analyst-packages/PROFILE/agentreward-338-pairs-bad-minus-good.operations.pb.gz",
    "analyst-packages/RAW-OPERATIONS/README.md",
    "analyst-packages/RAW-OPERATIONS/samples.jsonl",
    "run_analysts.py",
    "test_contract_helpers.py",
    "verify_frozen_contract.py",
    "analyst/order.json",
    "analyst/output.schema.json",
    "analyst/commands.json",
    "analyst/preparation.json",
    "analyst/prompts/profile-1.txt",
    "analyst/prompts/profile-2.txt",
    "analyst/prompts/profile-3.txt",
    "analyst/prompts/raw-operations-1.txt",
    "analyst/prompts/raw-operations-2.txt",
    "analyst/prompts/raw-operations-3.txt",
    "runtime/requirements.lock",
    "runtime/installed-packages.txt",
)

TOOLSB_FILES = (
    "inventory_toolsandbox.py",
    "run_toolsandbox.py",
    "test_run_toolsandbox.py",
    "toolsandbox-inventory.json",
    "prepare_episode_manifest.py",
    "toolsandbox/scenarios-32.json",
    "toolsandbox/scenarios-31.json",
    "toolsandbox/trial-seeds.json",
    "toolsandbox/condition-order.json",
    "toolsandbox/expected-episodes.jsonl",
    "toolsandbox/preflight-manifest.json",
    "toolsandbox/manifest-report.json",
    "analyst/policies/profile-policy.txt",
    "analyst/policies/raw-policy.txt",
    "analyst/independent-output-review.json",
    "toolsandbox/server-metadata.json",
)


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def git(checkout: Path, *args: str) -> str:
    return subprocess.check_output(
        ["git", "-C", str(checkout), *args], text=True
    ).strip()


def assert_semantics(stage: str) -> dict[str, Any]:
    if git(TOOL_SANDBOX, "rev-parse", "HEAD") != TOOL_SANDBOX_COMMIT:
        raise RuntimeError("ToolSandbox commit mismatch")
    if git(TOOL_SANDBOX, "status", "--porcelain"):
        raise RuntimeError("ToolSandbox checkout is dirty")
    prep = json.loads(
        (EXPERIMENT / "preparation-report.json").read_text(encoding="utf-8")
    )
    if prep.get("status") != "PASS":
        raise RuntimeError("analyst package preparation is not PASS")
    if not prep["tuple_equivalence"]["complete_multiset_equal"]:
        raise RuntimeError("flat/profile tuple multiset mismatch")
    if not prep["mass_conservation"]["equal"]:
        raise RuntimeError("flat/profile mass mismatch")
    analyst = json.loads(
        (EXPERIMENT / "analyst" / "preparation.json").read_text(encoding="utf-8")
    )
    if analyst != {
        **analyst,
        "status": "PASS",
        "run_count": 6,
        "arm_counts": {"PROFILE": 3, "RAW-OPERATIONS": 3},
    }:
        # The dictionary expansion keeps non-registered hash fields while making
        # the four registered values exact.
        raise RuntimeError("analyst order/preparation invariants failed")
    result: dict[str, Any] = {
        "tuple_count": prep["tuple_equivalence"]["stock_raw_tuple_count"],
        "tuple_unique_count": prep["tuple_equivalence"]["stock_raw_unique_tuple_count"],
        "mass": prep["mass_conservation"]["stock_raw"],
        "analyst_runs": analyst["run_count"],
    }
    if stage == "toolsandbox":
        inventory = json.loads(
            (EXPERIMENT / "toolsandbox-inventory.json").read_text(encoding="utf-8")
        )
        expected_counts = {
            "declared": 37,
            "offline": 32,
            "outcome_after_preflight_removal": 31,
            "requires_rapidapi": 5,
        }
        if inventory["counts"] != expected_counts:
            raise RuntimeError("ToolSandbox dependency counts changed")
        manifest = json.loads(
            (EXPERIMENT / "toolsandbox" / "manifest-report.json").read_text(
                encoding="utf-8"
            )
        )
        if (
            manifest.get("status") != "PASS"
            or manifest.get("full_episode_count") != 744
            or manifest.get("pilot_episode_count") != 372
        ):
            raise RuntimeError("ToolSandbox manifest invariants failed")
        review = json.loads(
            (EXPERIMENT / "analyst" / "independent-output-review.json").read_text(
                encoding="utf-8"
            )
        )
        if review.get("status") != "PASS":
            raise RuntimeError("independent analyst-output review is not PASS")
        result.update(
            {
                "scenario_counts": inventory["counts"],
                "full_episode_count": manifest["full_episode_count"],
                "pilot_episode_count": manifest["pilot_episode_count"],
            }
        )
    return result


def required_files(stage: str) -> tuple[str, ...]:
    if stage == "analyst":
        return COMMON_FILES
    if stage == "toolsandbox":
        return COMMON_FILES + TOOLSB_FILES
    raise ValueError(stage)


def create_contract(stage: str, output: Path) -> dict[str, Any]:
    semantics = assert_semantics(stage)
    hashes: dict[str, str] = {}
    for relative in required_files(stage):
        path = EXPERIMENT / relative
        if not path.is_file():
            raise FileNotFoundError(path)
        hashes[relative] = sha256_file(path)
    payload = {
        "schema": "agentsight.utility.frozen-contract.v1",
        "stage": stage,
        "created_at": utc_now(),
        "experiment": str(EXPERIMENT),
        "tool_sandbox": {
            "path": str(TOOL_SANDBOX),
            "commit": TOOL_SANDBOX_COMMIT,
            "clean": True,
        },
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
    stage = contract.get("stage")
    if stage not in {"analyst", "toolsandbox"}:
        raise RuntimeError(f"invalid contract stage: {stage}")
    current_semantics = assert_semantics(stage)
    if current_semantics != contract.get("semantics"):
        raise RuntimeError("semantic invariants changed after freeze")
    registered = contract.get("files")
    if set(registered) != set(required_files(stage)):
        raise RuntimeError("registered frozen-file set mismatch")
    changes = []
    for relative, expected in registered.items():
        path = EXPERIMENT / relative
        actual = sha256_file(path) if path.is_file() else None
        if actual != expected:
            changes.append(
                {"path": relative, "expected": expected, "actual": actual}
            )
    if changes:
        raise RuntimeError(f"frozen files changed: {changes}")
    record = {
        "schema": "agentsight.utility.contract-verification.v1",
        "status": "PASS",
        "stage": stage,
        "checked_at": utc_now(),
        "contract": str(contract_path.resolve()),
        "contract_sha256": sha256_file(contract_path),
        "file_count": len(registered),
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
    parser.add_argument("--stage", choices=("analyst", "toolsandbox"))
    parser.add_argument("--contract", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.create:
        if args.stage is None or args.output is None:
            raise SystemExit("--create requires --stage and --output")
        result = create_contract(args.stage, args.output)
    else:
        if args.contract is None or args.output is None:
            raise SystemExit("--verify requires --contract and --output")
        result = verify_contract(args.contract, args.output)
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
