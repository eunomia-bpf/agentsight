#!/usr/bin/env python3
"""Prepare or execute the frozen no-interim 40-run analyst batch."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path
import subprocess
from typing import Any, Callable

import run_analysts


EXPERIMENT = Path(__file__).resolve().parent
ANALYST_DIR = EXPERIMENT / "analyst"
RUNNER = EXPERIMENT / "run_analysts.py"
DEFAULT_VERIFICATION = EXPERIMENT / "contract-verification-analyst.json"
BATCH_COMMAND_PATH = ANALYST_DIR / "batch-command.json"
BATCH_RECEIPT_PATH = ANALYST_DIR / "batch-run.json"
COMMAND_IDENTIFIER = "experiment-002-analyst-batch-v1"


class BatchRunError(RuntimeError):
    """Raised when the no-interim batch cannot continue exactly as frozen."""


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def dump_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def batch_command() -> list[str]:
    return [
        "python3",
        str(Path(__file__).resolve()),
        "--execute-batch",
        "--contract-verification",
        str(DEFAULT_VERIFICATION.resolve()),
    ]


def command_document() -> dict[str, Any]:
    return {
        "schema": "agentsight.utility2.analyst-batch-command.v1",
        "command_identifier": COMMAND_IDENTIFIER,
        "command": batch_command(),
    }


def prepare() -> dict[str, Any]:
    if (ANALYST_DIR / "runs").exists() or BATCH_RECEIPT_PATH.exists():
        raise BatchRunError("refusing to prepare after analyst batch started")
    dump_json(BATCH_COMMAND_PATH, command_document())
    return {
        "status": "PASS",
        "command_identifier": COMMAND_IDENTIFIER,
        "command_sha256": sha256_file(BATCH_COMMAND_PATH),
        "registered_run_count": 40,
        "analyst_calls_made": 0,
    }


def frozen_command() -> list[str]:
    document = json.loads(BATCH_COMMAND_PATH.read_text(encoding="utf-8"))
    if (
        document.get("schema")
        != "agentsight.utility2.analyst-batch-command.v1"
        or document.get("command_identifier") != COMMAND_IDENTIFIER
        or not isinstance(document.get("command"), list)
    ):
        raise BatchRunError("frozen batch command is malformed")
    return document["command"]


def child_command(run_id: str, verification_path: Path) -> list[str]:
    return [
        "python3",
        str(RUNNER.resolve()),
        "--execute-run",
        run_id,
        "--contract-verification",
        str(verification_path.resolve()),
    ]


def _run_batch_rows(
    rows: list[dict[str, Any]],
    analyst_dir: Path,
    verification_path: Path,
    invoke: Callable[..., Any],
) -> list[str]:
    ordered = sorted(rows, key=lambda row: int(row["position"]))
    if [int(row["position"]) for row in ordered] != list(range(1, 41)):
        raise BatchRunError("frozen batch positions are not exactly 1..40")
    completed: list[str] = []
    for row in ordered:
        run_id = row["run_id"]
        try:
            invoke(
                child_command(run_id, verification_path),
                check=False,
            )
        except OSError as exc:
            raise BatchRunError(f"analyst launch defect: {run_id}") from exc
        record_path = analyst_dir / "runs" / run_id / "run.json"
        if not record_path.is_file():
            raise BatchRunError(
                f"analyst invocation left no terminal record: {run_id}"
            )
        record = json.loads(record_path.read_text(encoding="utf-8"))
        if record.get("status") not in run_analysts.TERMINAL_STATUSES:
            raise BatchRunError(
                f"analyst invocation left nonterminal record: {run_id}"
            )
        completed.append(run_id)
    return completed


def execute(verification_path: Path) -> dict[str, Any]:
    if verification_path.resolve() != DEFAULT_VERIFICATION.resolve():
        raise BatchRunError("batch must use the frozen verification path")
    run_analysts.verify_execution_gate(verification_path)
    if batch_command() != frozen_command():
        raise BatchRunError("dynamic batch command differs from frozen command")
    runs_dir = ANALYST_DIR / "runs"
    if runs_dir.exists():
        raise BatchRunError("batch requires analyst/runs to be absent initially")
    if BATCH_RECEIPT_PATH.exists():
        raise BatchRunError("batch receipt already exists; refusing overwrite")
    order_path = ANALYST_DIR / "order.json"
    order = json.loads(order_path.read_text(encoding="utf-8"))
    rows = order.get("runs")
    if not isinstance(rows, list) or len(rows) != 40:
        raise BatchRunError("frozen schedule does not contain exactly 40 runs")
    completed = _run_batch_rows(
        rows, ANALYST_DIR, verification_path, subprocess.run
    )
    if len(completed) != 40:
        raise BatchRunError("batch did not produce 40 terminal records")
    verification = json.loads(verification_path.read_text(encoding="utf-8"))
    receipt = {
        "schema": "agentsight.utility2.analyst-batch-receipt.v1",
        "status": "completed",
        "command_identifier": COMMAND_IDENTIFIER,
        "run_count": 40,
        "ordered_run_ids": completed,
        "order_sha256": sha256_file(order_path),
        "contract_sha256": verification["contract_sha256"],
        "batch_command_sha256": sha256_file(BATCH_COMMAND_PATH),
        "finished_at": utc_now(),
        "scientific_summary_fields": [],
        "endpoint_identifiers": [],
    }
    dump_json(BATCH_RECEIPT_PATH, receipt)
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    actions = parser.add_mutually_exclusive_group(required=True)
    actions.add_argument("--prepare", action="store_true")
    actions.add_argument("--execute-batch", action="store_true")
    parser.add_argument("--contract-verification", type=Path)
    args = parser.parse_args()
    if args.prepare:
        print(json.dumps(prepare(), sort_keys=True))
        return 0
    if args.contract_verification is None:
        raise SystemExit("--execute-batch requires --contract-verification")
    receipt = execute(args.contract_verification)
    print(json.dumps(receipt, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
