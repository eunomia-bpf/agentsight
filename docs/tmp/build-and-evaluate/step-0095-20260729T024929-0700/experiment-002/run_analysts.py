#!/usr/bin/env python3
"""Prepare or execute the frozen 20-block analyst replication.

Preparation is deterministic and makes no model call. Execution is a separate,
explicit action that runs exactly one registered cell after a fresh fail-closed
contract verification.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import random
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Any


EXPERIMENT = Path(__file__).resolve().parent
ANALYST_DIR = EXPERIMENT / "analyst"
PACKAGES = {
    "PROFILE": EXPERIMENT / "analyst-packages" / "PROFILE",
    "RAW-OPERATIONS": EXPERIMENT / "analyst-packages" / "RAW-OPERATIONS",
}
ORDER_SEED = 2026072902
REVIEW_ALIAS_SEED = 2026072905
BLOCK_COUNT = 20
TIMEOUT_SECONDS = 900
MODEL = "gpt-5.6-sol"
TERMINAL_STATUSES = {"ok", "failed", "timeout"}

COMMON_TASK = """You are an independent agent-performance analyst.

Your current directory is the complete and only evidence package you may
inspect. Do not read, search, or infer from any path outside it. Do not use the
internet. Identify exactly one recurring behavior that is overrepresented in
candidate/bad agent runs relative to base/good runs. Cite reproducible commands
and quantitative evidence from this package. Then propose one benchmark- and
domain-agnostic addition to an agent system policy, at most 60 English words,
that addresses the behavior. State the expected success/cost mechanism.

Do not mention or speculate about any downstream evaluation. Do not modify
files. Return only the JSON object required by the supplied output schema."""

FORMAT_HINTS = {
    "PROFILE": """The evidence is one standard differential pprof. Use stock
`go tool pprof` commands such as `-top`, `-traces`, `-tags`, `-focus`, and
`-ignore` against the `.pb.gz` file. Positive values are candidate/bad excess;
negative values are base/good excess.""",
    "RAW-OPERATIONS": """The evidence is a flat JSONL lossless decode of the
same differential pprof samples. Use shell, `jq`, or Python to aggregate
`samples.jsonl`. Positive values are candidate/bad excess; negative values are
base/good excess.""",
}

OUTPUT_SCHEMA: dict[str, Any] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object",
    "additionalProperties": False,
    "required": [
        "diagnosis",
        "quantitative_evidence",
        "policy_text",
        "expected_mechanism",
    ],
    "properties": {
        "diagnosis": {"type": "string", "minLength": 1},
        "quantitative_evidence": {
            "type": "array",
            "minItems": 1,
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["command", "finding"],
                "properties": {
                    "command": {"type": "string", "minLength": 1},
                    "finding": {"type": "string", "minLength": 1},
                },
            },
        },
        "policy_text": {"type": "string", "minLength": 1},
        "expected_mechanism": {"type": "string", "minLength": 1},
    },
}

REVIEW_DECISION_FIELDS = (
    "recurring_bad_vs_good_diagnosis_valid",
    "quantitative_support_valid",
    "executable_benchmark_agnostic_policy_at_most_60_words",
    "no_benchmark_specific_or_hidden_data_reference",
    "no_evidence_read_outside_assigned_package",
)


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


def opaque_id(kind: str, *parts: int) -> str:
    encoded = ":".join([kind, str(ORDER_SEED), *(str(part) for part in parts)])
    return f"{kind}-" + hashlib.sha256(encoded.encode("ascii")).hexdigest()[:12]


def registered_runs() -> list[dict[str, Any]]:
    """Return 40 runs in 20 randomized, exactly balanced temporal blocks."""

    first_arms = ["PROFILE"] * (BLOCK_COUNT // 2) + [
        "RAW-OPERATIONS"
    ] * (BLOCK_COUNT // 2)
    random.Random(ORDER_SEED).shuffle(first_arms)
    rows: list[dict[str, Any]] = []
    for block_index, first_arm in enumerate(first_arms, 1):
        second_arm = (
            "RAW-OPERATIONS" if first_arm == "PROFILE" else "PROFILE"
        )
        block_id = opaque_id("block", block_index)
        for within_block_order, arm in enumerate((first_arm, second_arm), 1):
            position = 2 * (block_index - 1) + within_block_order
            rows.append(
                {
                    "run_id": opaque_id("run", block_index, within_block_order),
                    "arm": arm,
                    "block_id": block_id,
                    "block_index": block_index,
                    "within_block_order": within_block_order,
                    "arm_rank": block_index,
                    "position": position,
                }
            )
    return rows


def prompt_for(arm: str) -> str:
    return COMMON_TASK + "\n\nEvidence format:\n" + FORMAT_HINTS[arm]


def command_for(run: dict[str, Any]) -> list[str]:
    run_dir = ANALYST_DIR / "runs" / run["run_id"]
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
        MODEL,
        "--sandbox",
        "read-only",
        "--cd",
        str(PACKAGES[run["arm"]].resolve()),
        "--output-schema",
        str((ANALYST_DIR / "output.schema.json").resolve()),
        "--json",
        "--output-last-message",
        str((run_dir / "final.json").resolve()),
        prompt_for(run["arm"]),
    ]


def model_contract() -> dict[str, Any]:
    return {
        "schema": "agentsight.utility2.analyst-model-contract.v1",
        "model": MODEL,
        "fresh_execution": {
            "ephemeral": True,
            "ignore_user_config": True,
            "ignore_repository_rules": True,
        },
        "timeout_seconds": TIMEOUT_SECONDS,
        "sandbox": "read-only",
        "working_directory": "assigned evidence package only",
        "network_permitted_by_task": False,
        "allowed_inspection": {
            "PROFILE": ["stock go tool pprof", "read-only shell"],
            "RAW-OPERATIONS": ["read-only shell", "jq", "Python"],
        },
        "output_schema": "analyst/output.schema.json",
        "stream_json_events": True,
        "rank_1_policy_selection": "block_index_1_in_each_arm",
        "interim_arm_summaries": "forbidden_until_40_terminal_records",
    }


def review_alias_assignment(runs: list[dict[str, Any]]) -> dict[str, Any]:
    shuffled_run_ids = [run["run_id"] for run in runs]
    random.Random(REVIEW_ALIAS_SEED).shuffle(shuffled_run_ids)
    cases = []
    for index, run_id in enumerate(shuffled_run_ids, 1):
        digest = hashlib.sha256(
            f"case:{REVIEW_ALIAS_SEED}:{index}".encode("ascii")
        ).hexdigest()[:12]
        cases.append({"case_id": f"case-{digest}", "run_id": run_id})
    return {
        "schema": "agentsight.utility2.review-alias-map.private.v1",
        "seed": REVIEW_ALIAS_SEED,
        "case_count": len(cases),
        "cases": cases,
    }


def review_output_schema(case_ids: list[str]) -> dict[str, Any]:
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "object",
        "additionalProperties": False,
        "required": ["cases"],
        "properties": {
            "cases": {
                "type": "array",
                "minItems": 40,
                "maxItems": 40,
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["case_id", *REVIEW_DECISION_FIELDS],
                    "properties": {
                        "case_id": {"type": "string", "enum": case_ids},
                        **{
                            field: {"type": "boolean"}
                            for field in REVIEW_DECISION_FIELDS
                        },
                    },
                },
            }
        },
    }


def prepare() -> dict[str, Any]:
    for arm, package in PACKAGES.items():
        if not package.is_dir():
            raise FileNotFoundError(f"{arm} package missing: {package}")
    if (ANALYST_DIR / "runs").exists():
        raise RuntimeError("refusing to prepare after analyst execution has started")

    dump_json(ANALYST_DIR / "output.schema.json", OUTPUT_SCHEMA)
    dump_json(ANALYST_DIR / "model-contract.json", model_contract())
    runs = registered_runs()
    prepared_runs: list[dict[str, Any]] = []
    for frozen in runs:
        run = dict(frozen)
        prompt_path = ANALYST_DIR / "prompts" / f"{run['run_id']}.txt"
        prompt_path.parent.mkdir(parents=True, exist_ok=True)
        prompt_path.write_text(prompt_for(run["arm"]) + "\n", encoding="utf-8")
        run["package"] = str(PACKAGES[run["arm"]].resolve())
        run["prompt_file"] = str(prompt_path.resolve())
        run["prompt_sha256"] = sha256_file(prompt_path)
        prepared_runs.append(run)

    order_payload = {
        "schema": "agentsight.utility2.analyst-order.v1",
        "seed": ORDER_SEED,
        "block_count": BLOCK_COUNT,
        "run_count": len(prepared_runs),
        "exact_first_arm_balance": {
            "PROFILE": sum(
                row["arm"] == "PROFILE" and row["within_block_order"] == 1
                for row in prepared_runs
            ),
            "RAW-OPERATIONS": sum(
                row["arm"] == "RAW-OPERATIONS"
                and row["within_block_order"] == 1
                for row in prepared_runs
            ),
        },
        "rank_1": {
            arm: next(
                row["run_id"]
                for row in prepared_runs
                if row["arm"] == arm and row["arm_rank"] == 1
            )
            for arm in PACKAGES
        },
        "runs": prepared_runs,
    }
    dump_json(ANALYST_DIR / "order.json", order_payload)
    commands = {
        "schema": "agentsight.utility2.analyst-commands.v1",
        "model": MODEL,
        "timeout_seconds": TIMEOUT_SECONDS,
        "runs": [
            {"run_id": run["run_id"], "command": command_for(run)}
            for run in prepared_runs
        ],
    }
    dump_json(ANALYST_DIR / "commands.json", commands)
    alias_map = review_alias_assignment(prepared_runs)
    dump_json(ANALYST_DIR / "review-alias-map.private.json", alias_map)
    dump_json(
        ANALYST_DIR / "review-output.schema.json",
        review_output_schema([case["case_id"] for case in alias_map["cases"]]),
    )
    review_preparation = {
        "schema": "agentsight.utility2.review-preparation.private.v1",
        "status": "PASS",
        "seed": REVIEW_ALIAS_SEED,
        "case_count": 40,
        "bijection": True,
        "alias_map_sha256": sha256_file(
            ANALYST_DIR / "review-alias-map.private.json"
        ),
        "output_schema_sha256": sha256_file(
            ANALYST_DIR / "review-output.schema.json"
        ),
        "bundle_creation_rule": "only_after_40_terminal_run_records",
        "public_decision_key": "case_id_only",
        "public_decision_fields": list(REVIEW_DECISION_FIELDS),
        "public_forbidden_fields": [
            "run_id",
            "arm",
            "timing",
            "usage",
            "schedule_position",
            "within_block_order",
            "arm_rank",
            "block_id",
            "block_index",
        ],
    }
    dump_json(ANALYST_DIR / "review-preparation.private.json", review_preparation)
    report = {
        "schema": "agentsight.utility2.analyst-preparation.v1",
        "status": "PASS",
        "seed": ORDER_SEED,
        "block_count": BLOCK_COUNT,
        "run_count": len(prepared_runs),
        "arm_counts": {
            arm: sum(run["arm"] == arm for run in prepared_runs)
            for arm in PACKAGES
        },
        "first_arm_counts": order_payload["exact_first_arm_balance"],
        "rank_1": order_payload["rank_1"],
        "order_sha256": sha256_file(ANALYST_DIR / "order.json"),
        "schema_sha256": sha256_file(ANALYST_DIR / "output.schema.json"),
        "commands_sha256": sha256_file(ANALYST_DIR / "commands.json"),
        "model_contract_sha256": sha256_file(
            ANALYST_DIR / "model-contract.json"
        ),
        "review_alias_map_sha256": review_preparation["alias_map_sha256"],
        "review_output_schema_sha256": review_preparation[
            "output_schema_sha256"
        ],
        "model": MODEL,
        "timeout_seconds": TIMEOUT_SECONDS,
        "model_calls_made": 0,
    }
    dump_json(ANALYST_DIR / "preparation.json", report)
    return report


def load_registered_run(run_id: str) -> dict[str, Any]:
    order = json.loads((ANALYST_DIR / "order.json").read_text(encoding="utf-8"))
    matches = [run for run in order["runs"] if run["run_id"] == run_id]
    if len(matches) != 1:
        raise KeyError(f"unregistered analyst run: {run_id}")
    return matches[0]


def frozen_command_for(run_id: str) -> list[str]:
    commands = json.loads(
        (ANALYST_DIR / "commands.json").read_text(encoding="utf-8")
    )
    matches = [
        row["command"] for row in commands["runs"] if row["run_id"] == run_id
    ]
    if len(matches) != 1:
        raise RuntimeError(f"frozen command missing or duplicated: {run_id}")
    return matches[0]


def enforce_frozen_order(run_id: str, analyst_dir: Path = ANALYST_DIR) -> None:
    order = json.loads((analyst_dir / "order.json").read_text(encoding="utf-8"))
    rows = sorted(order["runs"], key=lambda row: int(row["position"]))
    positions = {row["run_id"]: int(row["position"]) for row in rows}
    if run_id not in positions:
        raise RuntimeError(f"run is absent from frozen order: {run_id}")
    current = positions[run_id]
    for row in rows:
        position = int(row["position"])
        run_dir = analyst_dir / "runs" / row["run_id"]
        record_path = run_dir / "run.json"
        if position < current:
            if not record_path.is_file():
                raise RuntimeError(
                    f"frozen predecessor has not completed: {row['run_id']}"
                )
            record = json.loads(record_path.read_text(encoding="utf-8"))
            if record.get("status") not in TERMINAL_STATUSES:
                raise RuntimeError(
                    f"frozen predecessor is not terminal: {row['run_id']}"
                )
        elif position >= current and run_dir.exists():
            raise RuntimeError(
                f"current/later frozen run already exists: {row['run_id']}"
            )


def verify_execution_gate(verification_path: Path) -> Path:
    record = json.loads(verification_path.read_text(encoding="utf-8"))
    if record.get("status") != "PASS" or record.get("stage") != "analyst":
        raise RuntimeError("analyst frozen-contract verification is not PASS")
    contract_path = Path(record["contract"])
    if sha256_file(contract_path) != record.get("contract_sha256"):
        raise RuntimeError("analyst contract changed after verification")

    from verify_frozen_contract import verify_contract

    with tempfile.TemporaryDirectory(
        prefix="agentprof-utility2-contract-check-"
    ) as directory:
        fresh_path = Path(directory) / "verification.json"
        fresh = verify_contract(contract_path, fresh_path)
    if fresh.get("status") != "PASS" or fresh.get("stage") != "analyst":
        raise RuntimeError("fresh analyst contract verification failed")
    return contract_path


def event_summary(
    event: Any,
) -> tuple[str | None, dict[str, Any] | None, str | None, str | None]:
    if not isinstance(event, dict):
        return None, None, None, None
    event_type = event.get("type") if isinstance(event.get("type"), str) else None
    usage = event.get("usage") if isinstance(event.get("usage"), dict) else None
    item = event.get("item")
    tool_type = None
    tool_command = None
    if event_type == "item.completed" and isinstance(item, dict):
        if item.get("type") in {"command_execution", "mcp_tool_call", "web_search"}:
            tool_type = str(item["type"])
        if item.get("type") == "command_execution":
            command = item.get("command")
            if isinstance(command, str):
                tool_command = command
            elif isinstance(command, list) and all(
                isinstance(part, str) for part in command
            ):
                tool_command = json.dumps(command)
    return event_type, usage, tool_type, tool_command


def aggregate_provider_usage(rows: list[dict[str, Any]]) -> dict[str, int | float]:
    totals: dict[str, int | float] = {"input_tokens": 0, "output_tokens": 0}
    total_tokens_was_emitted = False
    for row in rows:
        if "total_tokens" in row:
            total_tokens_was_emitted = True
            if row.get("total_tokens") != row.get("input_tokens", 0) + row.get(
                "output_tokens", 0
            ):
                raise RuntimeError(
                    "provider total_tokens is not input_tokens + output_tokens"
                )
        for key, value in row.items():
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                totals[key] = totals.get(key, 0) + value
    if total_tokens_was_emitted and totals["total_tokens"] != (
        totals["input_tokens"] + totals["output_tokens"]
    ):
        raise RuntimeError("aggregated provider total_tokens is inconsistent")
    return totals


def execute(run_id: str, verification_path: Path) -> int:
    verify_execution_gate(verification_path)
    run = load_registered_run(run_id)
    enforce_frozen_order(run_id)
    command = command_for(run)
    if command != frozen_command_for(run_id):
        raise RuntimeError(
            f"dynamic command differs from frozen literal command: {run_id}"
        )

    run_dir = ANALYST_DIR / "runs" / run_id
    run_dir.mkdir(parents=True)
    metadata: dict[str, Any] = {
        "schema": "agentsight.utility2.analyst-run.v1",
        "run": run,
        "command": command,
        "started_at": utc_now(),
        "status": "running",
    }
    dump_json(run_dir / "run.json", metadata)

    started = time.monotonic()
    first_event_at: str | None = None
    last_event_at: str | None = None
    final_response_received_at: str | None = None
    first_event_elapsed_seconds: float | None = None
    last_event_elapsed_seconds: float | None = None
    final_response_elapsed_seconds: float | None = None
    usage_rows: list[dict[str, Any]] = []
    tool_counts: dict[str, int] = {}
    tool_records: list[dict[str, Any]] = []
    model_turns = 0
    event_count = 0
    events_path = run_dir / "events.jsonl"
    receipts_path = run_dir / "event-receipts.jsonl"
    stderr_path = run_dir / "stderr.log"
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
            event_type, usage, tool_type, tool_command = event_summary(parsed)
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

    wall = time.monotonic() - started
    telemetry_error: str | None = None
    try:
        usage_totals = aggregate_provider_usage(usage_rows)
    except RuntimeError as exc:
        usage_totals = {"input_tokens": 0, "output_tokens": 0}
        telemetry_error = str(exc)
    status = "ok" if return_code == 0 else "timeout" if return_code == 124 else "failed"
    if status == "ok" and (
        usage_totals["input_tokens"] <= 0
        or usage_totals["output_tokens"] <= 0
        or final_response_elapsed_seconds is None
        or not (run_dir / "final.json").is_file()
        or telemetry_error is not None
    ):
        status = "failed"
        telemetry_error = telemetry_error or (
            "successful process lacked positive usage, final receipt, or final JSON"
        )
    metadata.update(
        {
            "finished_at": utc_now(),
            "wall_seconds": wall,
            "exit_code": return_code,
            "status": status,
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
            "final_exists": (run_dir / "final.json").is_file(),
            "telemetry_error": telemetry_error,
        }
    )
    if metadata["final_exists"]:
        metadata["final_sha256"] = sha256_file(run_dir / "final.json")
    dump_json(run_dir / "run.json", metadata)
    return 0 if status == "ok" else 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    actions = parser.add_mutually_exclusive_group(required=True)
    actions.add_argument("--prepare", action="store_true")
    actions.add_argument("--execute-run")
    parser.add_argument("--contract-verification", type=Path)
    args = parser.parse_args()
    if args.prepare:
        print(json.dumps(prepare(), sort_keys=True))
        return 0
    if args.contract_verification is None:
        raise SystemExit("--execute-run requires --contract-verification")
    return execute(args.execute_run, args.contract_verification)


if __name__ == "__main__":
    raise SystemExit(main())
