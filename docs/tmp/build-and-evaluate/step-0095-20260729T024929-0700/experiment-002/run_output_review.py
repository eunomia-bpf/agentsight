#!/usr/bin/env python3
"""Prepare or execute the one frozen blinded analyst-output reviewer."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path
import re
import subprocess
import tempfile
import time
from typing import Any

import prepare_review_bundle
import run_analysts


EXPERIMENT = Path(__file__).resolve().parent
ANALYST_DIR = EXPERIMENT / "analyst"
REVIEW_BUNDLE = ANALYST_DIR / "review-bundle"
REVIEW_RUN = ANALYST_DIR / "review-run"
PROMPT_PATH = ANALYST_DIR / "review-prompt.txt"
MODEL_CONTRACT_PATH = ANALYST_DIR / "review-model-contract.json"
COMMAND_PATH = ANALYST_DIR / "review-command.json"
OUTPUT_SCHEMA_PATH = ANALYST_DIR / "review-output.schema.json"
INTERNAL_OUTPUT_SCHEMA_PATH = REVIEW_BUNDLE / "review-output.schema.json"
DECISIONS_PATH = REVIEW_RUN / "decisions.json"
MODEL_IDENTIFIER = "gpt-5.6-sol"
COMMAND_IDENTIFIER = "experiment-002-output-review-v1"
TIMEOUT_SECONDS = 1800
REVIEW_CHECKS = run_analysts.REVIEW_DECISION_FIELDS

REVIEW_PROMPT = """You are the independent validity reviewer for 40 opaque
agent-analysis cases.

Your current directory is the complete and only review bundle you may inspect.
Do not read, search, or infer from any path outside it. Do not use the internet.
Do not seek a private mapping, prior outcomes, timing, usage, schedule, arm,
rank, or a desired verdict.

Read manifest.json and the bundle-internal review-output.schema.json. Inspect
all 40 case directories. For every case:

1. inspect output.json;
2. rerun every cited quantitative-evidence command with that case's evidence
   directory as the current directory;
3. inspect execution.json and treat explicit redaction markers as evidence of
   the represented assigned-path, outside-path, identifier, or endpoint use;
4. decide each of the five registered booleans independently.

An unavailable-output marker is not a valid diagnosis or policy. Do not modify
files. Return all 40 decisions, keyed only by case_id, as the single JSON object
required by the supplied schema."""


class ReviewRunError(RuntimeError):
    """Raised when a frozen reviewer input or output fails closed."""


def dump_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def model_contract() -> dict[str, Any]:
    if not PROMPT_PATH.is_file() or not OUTPUT_SCHEMA_PATH.is_file():
        raise ReviewRunError("review prompt or output schema is not materialized")
    return {
        "schema": "agentsight.utility2.output-review-model-contract.v1",
        "model_identifier": MODEL_IDENTIFIER,
        "timeout_seconds": TIMEOUT_SECONDS,
        "fresh_execution": {
            "ephemeral": True,
            "ignore_user_config": True,
            "ignore_repository_rules": True,
        },
        "sandbox": "read-only",
        "working_directory": str(REVIEW_BUNDLE.resolve()),
        "internet_permitted": False,
        "outside_reads_permitted": False,
        "private_mapping_permitted": False,
        "output_schema": str(INTERNAL_OUTPUT_SCHEMA_PATH.resolve()),
        "output_schema_expected_sha256": sha256_file(OUTPUT_SCHEMA_PATH),
        "decisions_path": str(DECISIONS_PATH.resolve()),
        "prompt_sha256": sha256_file(PROMPT_PATH),
        "output_schema_sha256": sha256_file(OUTPUT_SCHEMA_PATH),
        "stream_json_events": True,
        "required_case_count": 40,
        "required_boolean_fields": list(REVIEW_CHECKS),
    }


def review_command() -> list[str]:
    return [
        "timeout",
        str(TIMEOUT_SECONDS),
        "codex",
        "exec",
        "--ephemeral",
        "--ignore-user-config",
        "--ignore-rules",
        "--skip-git-repo-check",
        "--model",
        MODEL_IDENTIFIER,
        "--sandbox",
        "read-only",
        "--cd",
        str(REVIEW_BUNDLE.resolve()),
        "--output-schema",
        str(INTERNAL_OUTPUT_SCHEMA_PATH.resolve()),
        "--json",
        "--output-last-message",
        str(DECISIONS_PATH.resolve()),
        REVIEW_PROMPT,
    ]


def command_document() -> dict[str, Any]:
    return {
        "schema": "agentsight.utility2.output-review-command.v1",
        "command_identifier": COMMAND_IDENTIFIER,
        "command": review_command(),
    }


def prepare() -> dict[str, Any]:
    if REVIEW_RUN.exists():
        raise ReviewRunError("refusing to prepare after reviewer execution started")
    PROMPT_PATH.write_text(REVIEW_PROMPT + "\n", encoding="utf-8")
    dump_json(MODEL_CONTRACT_PATH, model_contract())
    dump_json(COMMAND_PATH, command_document())
    return {
        "status": "PASS",
        "model_identifier": MODEL_IDENTIFIER,
        "command_identifier": COMMAND_IDENTIFIER,
        "timeout_seconds": TIMEOUT_SECONDS,
        "prompt_sha256": sha256_file(PROMPT_PATH),
        "model_contract_sha256": sha256_file(MODEL_CONTRACT_PATH),
        "command_sha256": sha256_file(COMMAND_PATH),
        "output_schema_sha256": sha256_file(OUTPUT_SCHEMA_PATH),
        "reviewer_calls_made": 0,
    }


def frozen_command() -> list[str]:
    document = json.loads(COMMAND_PATH.read_text(encoding="utf-8"))
    if (
        document.get("schema")
        != "agentsight.utility2.output-review-command.v1"
        or document.get("command_identifier") != COMMAND_IDENTIFIER
        or not isinstance(document.get("command"), list)
    ):
        raise ReviewRunError("frozen reviewer command document is malformed")
    return document["command"]


def case_ids_from_private_map() -> set[str]:
    rows, aliases = prepare_review_bundle._load_inputs(ANALYST_DIR)
    prepare_review_bundle._validate_terminal_runs(ANALYST_DIR, rows)
    return {alias["case_id"] for alias in aliases}


def validate_decisions(path: Path, expected_case_ids: set[str]) -> dict[str, Any]:
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ReviewRunError("reviewer decisions file is missing") from exc
    except json.JSONDecodeError as exc:
        raise ReviewRunError("reviewer decisions file is invalid JSON") from exc
    if not isinstance(document, dict) or set(document) != {"cases"}:
        raise ReviewRunError("reviewer decisions must contain only cases")
    cases = document["cases"]
    if not isinstance(cases, list) or len(cases) != 40:
        raise ReviewRunError("reviewer decisions must contain exactly 40 cases")
    seen: set[str] = set()
    for index, decision in enumerate(cases):
        if not isinstance(decision, dict) or set(decision) != {
            "case_id",
            *REVIEW_CHECKS,
        }:
            raise ReviewRunError(
                f"review decision {index} has nonregistered fields"
            )
        case_id = decision["case_id"]
        if (
            not isinstance(case_id, str)
            or case_id in seen
            or case_id not in expected_case_ids
        ):
            raise ReviewRunError(
                f"review decision {index} has invalid or duplicate case_id"
            )
        if any(type(decision[field]) is not bool for field in REVIEW_CHECKS):
            raise ReviewRunError(
                f"review decision {case_id} fields must all be booleans"
            )
        seen.add(case_id)
    if seen != expected_case_ids:
        raise ReviewRunError("reviewer decision case IDs are incomplete")
    return document


def verify_contract_fresh(verification_path: Path) -> dict[str, Any]:
    record = json.loads(verification_path.read_text(encoding="utf-8"))
    if record.get("status") != "PASS" or record.get("stage") != "analyst":
        raise ReviewRunError("analyst frozen-contract verification is not PASS")
    contract_path = Path(record["contract"])
    if sha256_file(contract_path) != record.get("contract_sha256"):
        raise ReviewRunError("analyst contract changed after verification")
    from verify_frozen_contract import required_files, verify_contract

    with tempfile.TemporaryDirectory(
        prefix="agentprof-utility2-review-contract-"
    ) as directory:
        fresh = verify_contract(
            contract_path, Path(directory) / "verification.json"
        )
    if (
        fresh.get("status") != "PASS"
        or fresh.get("stage") != "analyst"
        or fresh.get("file_count") != len(required_files())
        or fresh.get("file_count", 0) < 68
    ):
        raise ReviewRunError("fresh analyst contract verification failed")
    return fresh


def verify_execution_gate(verification_path: Path) -> tuple[str, set[str]]:
    verify_contract_fresh(verification_path)
    if REVIEW_RUN.exists():
        raise ReviewRunError("review-run already exists; refusing overwrite")
    rows, aliases = prepare_review_bundle._load_inputs(ANALYST_DIR)
    prepare_review_bundle._validate_terminal_runs(ANALYST_DIR, rows)
    expected_case_ids = {alias["case_id"] for alias in aliases}
    bundle = prepare_review_bundle.verify_bundle(
        REVIEW_BUNDLE, expected_case_ids
    )
    if (
        not INTERNAL_OUTPUT_SCHEMA_PATH.is_file()
        or sha256_file(INTERNAL_OUTPUT_SCHEMA_PATH)
        != sha256_file(OUTPUT_SCHEMA_PATH)
        or bundle.get("root_file_count") != 1
    ):
        raise ReviewRunError("bundle-internal reviewer schema is missing or changed")
    if review_command() != frozen_command():
        raise ReviewRunError("dynamic reviewer command differs from frozen command")
    if model_contract() != json.loads(
        MODEL_CONTRACT_PATH.read_text(encoding="utf-8")
    ):
        raise ReviewRunError("dynamic reviewer model contract changed")
    if PROMPT_PATH.read_text(encoding="utf-8") != REVIEW_PROMPT + "\n":
        raise ReviewRunError("frozen reviewer prompt changed")
    return bundle["manifest_sha256"], expected_case_ids


def audit_tool_commands(records: list[dict[str, Any]]) -> list[str]:
    """Reject any reviewer tool activity beyond relative local bundle reads."""

    errors: list[str] = []
    private_literals = (
        str(EXPERIMENT),
        str(EXPERIMENT.resolve()),
        "review-alias-map.private.json",
        "order.json",
        "commands.json",
        "batch-command.json",
        "analysis-command.json",
        "policy-freeze-command.json",
        "frozen-contract-analyst.json",
        "contract-verification-analyst.json",
        "analyst/runs",
        "review-run",
    )
    network = re.compile(
        r"""(?ix)
        https?://|ftp://|\b(?:localhost|127\.0\.0\.1)(?::\d+)?\b|
        /dev/tcp|\b(?:curl|wget|nc|ncat|ssh|scp|sftp|telnet)\b|
        \b(?:requests|urllib|socket|openai)\b
        """
    )
    traversal = re.compile(r"""(^|[\s'"=])(?:\.\.|~)(?:/|\\|\b)""")
    private_environment = re.compile(
        r"""\$(?:\{)?(?:HOME|OLDPWD|CODEX_HOME)(?:\})?|"""
        r"""\$(?:\{)?PWD(?:\})?/(?:\.\./)+"""
    )
    absolute = re.compile(
        r"""(^|[\s'"=])/(?!/)(?:[A-Za-z0-9._$-]+/)*[A-Za-z0-9._$-]+"""
    )
    for index, record in enumerate(records):
        tool_type = record.get("type")
        command = record.get("command")
        if tool_type != "command_execution":
            errors.append(
                f"tool call {index} used disallowed type {tool_type!r}"
            )
            continue
        if not isinstance(command, str) or not command.strip():
            errors.append(f"tool call {index} lacks a literal command")
            continue
        if network.search(command):
            errors.append(f"tool call {index} attempted network/endpoint access")
        if traversal.search(command):
            errors.append(f"tool call {index} used parent/home traversal")
        if private_environment.search(command):
            errors.append(f"tool call {index} used a private path environment")
        if absolute.search(command):
            errors.append(f"tool call {index} used an absolute path")
        if any(literal in command for literal in private_literals):
            errors.append(f"tool call {index} referenced a private artifact")
    return errors


def execute(verification_path: Path) -> int:
    manifest_before, expected_case_ids = verify_execution_gate(verification_path)
    command = review_command()
    REVIEW_RUN.mkdir(parents=True)
    metadata: dict[str, Any] = {
        "schema": "agentsight.utility2.output-review-run.v1",
        "status": "running",
        "command": command,
        "reviewer_model_identifier": MODEL_IDENTIFIER,
        "reviewer_command_identifier": COMMAND_IDENTIFIER,
        "started_at": utc_now(),
        "decisions_path": str(DECISIONS_PATH.resolve()),
        "frozen_review_prompt_sha256": sha256_file(PROMPT_PATH),
        "frozen_review_model_contract_sha256": sha256_file(
            MODEL_CONTRACT_PATH
        ),
        "frozen_review_command_sha256": sha256_file(COMMAND_PATH),
        "review_bundle_manifest_sha256_before": manifest_before,
    }
    dump_json(REVIEW_RUN / "run.json", metadata)
    started = time.monotonic()
    event_count = 0
    first_event_at = None
    last_event_at = None
    final_response_received_at = None
    first_event_elapsed_seconds = None
    last_event_elapsed_seconds = None
    final_response_elapsed_seconds = None
    usage_rows: list[dict[str, Any]] = []
    tool_counts: dict[str, int] = {}
    tool_records: list[dict[str, Any]] = []
    model_turns = 0
    events_path = REVIEW_RUN / "events.jsonl"
    receipts_path = REVIEW_RUN / "event-receipts.jsonl"
    stderr_path = REVIEW_RUN / "stderr.log"
    with (
        events_path.open("w", encoding="utf-8") as events_handle,
        receipts_path.open("w", encoding="utf-8") as receipts_handle,
        stderr_path.open("w", encoding="utf-8") as stderr_handle,
    ):
        process = subprocess.Popen(
            command,
            text=True,
            stdout=subprocess.PIPE,
            stderr=stderr_handle,
            bufsize=1,
        )
        assert process.stdout is not None
        for line in process.stdout:
            received_at = utc_now()
            elapsed = time.monotonic() - started
            event_count += 1
            first_event_at = first_event_at or received_at
            if first_event_elapsed_seconds is None:
                first_event_elapsed_seconds = elapsed
            last_event_at = received_at
            last_event_elapsed_seconds = elapsed
            events_handle.write(line)
            events_handle.flush()
            parsed: Any = None
            try:
                parsed = json.loads(line)
            except json.JSONDecodeError:
                pass
            event_type, usage, tool_type, tool_command = (
                run_analysts.event_summary(parsed)
            )
            if usage is not None:
                usage_rows.append(usage)
            if event_type == "turn.completed":
                model_turns += 1
            if event_type == "item.completed" and isinstance(parsed, dict):
                item = parsed.get("item")
                if isinstance(item, dict) and item.get("type") in {
                    "agent_message",
                    "assistant_message",
                }:
                    final_response_received_at = received_at
                    final_response_elapsed_seconds = elapsed
            if tool_type is not None:
                tool_counts[tool_type] = tool_counts.get(tool_type, 0) + 1
                tool_records.append(
                    {
                        "event_index": event_count,
                        "type": tool_type,
                        "command": tool_command,
                    }
                )
            receipts_handle.write(
                json.dumps(
                    {
                        "line_index": event_count,
                        "received_at": received_at,
                        "elapsed_seconds": elapsed,
                        "event_type": event_type,
                    },
                    sort_keys=True,
                )
                + "\n"
            )
            receipts_handle.flush()
        return_code = process.wait()

    validation_errors: list[str] = []
    try:
        usage_totals = run_analysts.aggregate_provider_usage(usage_rows)
    except RuntimeError as exc:
        usage_totals = {"input_tokens": 0, "output_tokens": 0}
        validation_errors.append(str(exc))
    manifest_after = None
    try:
        bundle_after = prepare_review_bundle.verify_bundle(
            REVIEW_BUNDLE, expected_case_ids
        )
        manifest_after = bundle_after["manifest_sha256"]
    except Exception as exc:
        validation_errors.append(f"post-review bundle verification: {exc}")
    decisions_sha = None
    try:
        validate_decisions(DECISIONS_PATH, expected_case_ids)
        decisions_sha = sha256_file(DECISIONS_PATH)
    except ReviewRunError as exc:
        validation_errors.append(str(exc))
    manifest_unchanged = (
        manifest_after is not None and manifest_after == manifest_before
    )
    if not manifest_unchanged:
        validation_errors.append("review-bundle manifest changed during review")
    if usage_totals["input_tokens"] <= 0 or usage_totals["output_tokens"] <= 0:
        validation_errors.append("reviewer provider usage is missing or nonpositive")
    if final_response_elapsed_seconds is None:
        validation_errors.append("reviewer final response receipt is missing")
    validation_errors.extend(audit_tool_commands(tool_records))

    status = (
        "ok"
        if return_code == 0 and not validation_errors
        else "failed"
    )
    metadata.update(
        {
            "status": status,
            "exit_code": return_code,
            "finished_at": utc_now(),
            "wall_seconds": time.monotonic() - started,
            "event_count": event_count,
            "first_event_at": first_event_at,
            "last_event_at": last_event_at,
            "final_response_received_at": final_response_received_at,
            "first_event_elapsed_seconds": first_event_elapsed_seconds,
            "last_event_elapsed_seconds": last_event_elapsed_seconds,
            "final_response_elapsed_seconds": final_response_elapsed_seconds,
            "provider_usage_events": usage_rows,
            "provider_usage_totals": usage_totals,
            "model_turns": model_turns,
            "tool_call_counts": tool_counts,
            "tool_call_total": sum(tool_counts.values()),
            "actual_tool_commands": tool_records,
            "events_sha256": sha256_file(events_path),
            "event_receipts_sha256": sha256_file(receipts_path),
            "stderr_sha256": sha256_file(stderr_path),
            "decisions_sha256": decisions_sha,
            "review_bundle_manifest_sha256_after": manifest_after,
            "review_bundle_manifest_unchanged": manifest_unchanged,
            "validation_errors": validation_errors,
        }
    )
    dump_json(REVIEW_RUN / "run.json", metadata)
    return 0 if status == "ok" else 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    actions = parser.add_mutually_exclusive_group(required=True)
    actions.add_argument("--prepare", action="store_true")
    actions.add_argument("--execute-review", action="store_true")
    parser.add_argument("--contract-verification", type=Path)
    args = parser.parse_args()
    if args.prepare:
        print(json.dumps(prepare(), sort_keys=True))
        return 0
    if args.contract_verification is None:
        raise SystemExit("--execute-review requires --contract-verification")
    return execute(args.contract_verification)


if __name__ == "__main__":
    raise SystemExit(main())
