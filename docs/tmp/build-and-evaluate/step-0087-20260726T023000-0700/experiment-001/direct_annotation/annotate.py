#!/usr/bin/env python3
"""Run one direct multi-level Codex annotation call per CodeTrace trajectory."""

from __future__ import annotations

import argparse
import concurrent.futures
from dataclasses import dataclass
import json
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import threading
import time
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
EXPERIMENT = SCRIPT_DIR.parent
REPO = EXPERIMENT.parents[4]
SOURCE_PACKETS = (
    REPO
    / ".agentsight"
    / "experiments"
    / "rq4-end-to-end-cost-v1"
    / "full"
    / "source-packets-rep-1"
)
SOURCE_MANIFEST = SOURCE_PACKETS / "manifest.json"
SCHEMA = SCRIPT_DIR / "response-schema.json"
INDEX = EXPERIMENT / "packet-index.json"
RAW_MARKS = EXPERIMENT / "raw-marks"
RAW_EVENTS = EXPERIMENT / "raw-events"
RUN_RECORDS = EXPERIMENT / "annotation-run-records.jsonl"
RAW_ANNOTATIONS = EXPERIMENT / "raw-annotations"
PREFLIGHT = EXPERIMENT / "preflight"
PILOT = EXPERIMENT / "pilot"

MODEL = "gpt-5.6-sol"
EXPECTED_SESSIONS = 405
EXPECTED_TURNS = 17_148
EXPECTED_OPERATIONS = 20_866
PILOT_SESSIONS = 40
DEFAULT_WORKERS = 4
DEFAULT_TIMEOUT_SECONDS = 1_200
LABEL_PATTERN = re.compile(
    r"^(repeat|recover|understand|plan|search|locate|navigate|extract|compare|"
    r"compute|diagnose|reproduce|test|edit|build|configure|verify|validate|"
    r"coordinate|authenticate|update|create|remove|deploy|submit|escalate|"
    r"communicate|report|resolve|collect|read|inspect|execute)"
    r"( [a-z0-9-]+){0,2}$"
)
PROHIBITED_ITEM_TYPES = {
    "command_execution",
    "file_change",
    "mcp_tool_call",
    "web_search",
}
RECORD_LOCK = threading.Lock()


SYSTEM_INSTRUCTION = """You are the automatic semantic annotation backend.
Use only the SOURCE_PACKET in this request. Do not invoke tools, execute shell
commands, inspect files, inspect a repository, use the network, or run Git.
Return only the JSON object required by the response schema.

Read the complete already-finished trajectory and directly write sparse
multi-level transition marks in one pass. Do not use a STOP/SPLIT protocol and
do not recursively ask yourself binary questions.

The output is the A2 sparse complete-path mark format:
- `session` must exactly equal the packet's `session`.
- `marks` are ordered by the packet's turn order.
- every `start_operation_id` must equal a turn's `first_operation_id`;
- the first mark must start at the first turn;
- omit a mark when the complete semantic path is unchanged;
- each mark's `semantic_path` is the complete active path for that span;
- every path starts with the same mandatory session root;
- depth is variable and has no fixed cap;
- every tag is lowercase, action-first, and contains 1--3 meaningful words;
- the allowed action-first verbs are fixed by the response schema.

Choose boundaries for persistent changes in what responsibility the agent is
trying to accomplish. Do not create a boundary merely because a command, file,
tool, observation, status, or retry changes. Do not force every turn to become
a mark. Add nested levels only when they express meaningful task/subtask,
strategy or phase, and semantic-action responsibility. Keep the root concrete
to the requested task. Prefer stable reusable wording when the same
responsibility recurs. Never mention framework, agent, model, session, score,
outcome, success/failure label, or official stage in a tag.
"""


@dataclass(frozen=True)
class PacketRow:
    ordinal: int
    source_batch: str
    packet: dict[str, Any]

    @property
    def session(self) -> str:
        return str(self.packet["session"])

    @property
    def raw_path(self) -> Path:
        return RAW_MARKS / f"{self.ordinal:04d}.json"


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )


def load_packets() -> list[PacketRow]:
    manifest = read_json(SOURCE_MANIFEST)
    packets: list[tuple[str, dict[str, Any]]] = []
    for batch_path in sorted(SOURCE_PACKETS.glob("batch-*.json")):
        payload = read_json(batch_path)
        if payload.get("schema") != "agentsight.agent-operation-annotation-packet.v1":
            raise ValueError(f"unexpected packet schema: {batch_path}")
        for packet in payload["sessions"]:
            packets.append((batch_path.name, packet))
    packets.sort(key=lambda item: str(item[1]["session"]))
    rows = [
        PacketRow(ordinal=index, source_batch=batch, packet=packet)
        for index, (batch, packet) in enumerate(packets, 1)
    ]
    sessions = [row.session for row in rows]
    if len(rows) != EXPECTED_SESSIONS or len(set(sessions)) != EXPECTED_SESSIONS:
        raise ValueError("source packet population is not exactly 405 unique sessions")
    turns = sum(int(row.packet["turn_count"]) for row in rows)
    operations = sum(int(row.packet["operation_count"]) for row in rows)
    if turns != EXPECTED_TURNS or operations != EXPECTED_OPERATIONS:
        raise ValueError(
            f"source population mass mismatch: turns={turns}, operations={operations}"
        )
    if (
        int(manifest["sessions"]) != EXPECTED_SESSIONS
        or int(manifest["turns"]) != EXPECTED_TURNS
        or int(manifest["operations"]) != EXPECTED_OPERATIONS
    ):
        raise ValueError("source manifest totals do not match the fixed population")
    return rows


def prepare() -> None:
    rows = load_packets()
    write_json(
        INDEX,
        {
            "schema": "agentsight.direct-multilevel-annotation.packet-index.v1",
            "source": str(SOURCE_PACKETS.relative_to(REPO)),
            "sessions": EXPECTED_SESSIONS,
            "turns": EXPECTED_TURNS,
            "operations": EXPECTED_OPERATIONS,
            "rows": [
                {
                    "ordinal": row.ordinal,
                    "session": row.session,
                    "framework": row.packet["framework"],
                    "source_batch": row.source_batch,
                    "turns": row.packet["turn_count"],
                    "operations": row.packet["operation_count"],
                }
                for row in rows
            ],
        },
    )
    print(
        json.dumps(
            {
                "status": "ok",
                "sessions": len(rows),
                "turns": EXPECTED_TURNS,
                "operations": EXPECTED_OPERATIONS,
                "index": str(INDEX.relative_to(EXPERIMENT)),
            },
            sort_keys=True,
        ),
        flush=True,
    )


def validate_response(packet: dict[str, Any], response: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(response, dict):
        return ["response is not an object"]
    if set(response) != {"session", "marks"}:
        errors.append("response keys must be exactly session and marks")
    if response.get("session") != packet["session"]:
        errors.append("session does not exactly match the packet")
    marks = response.get("marks")
    if not isinstance(marks, list) or not marks:
        return [*errors, "marks must be a nonempty list"]

    turns = packet["turns"]
    turn_starts = [str(turn["first_operation_id"]) for turn in turns]
    positions = {start: index for index, start in enumerate(turn_starts)}
    observed_starts: list[str] = []
    observed_paths: list[tuple[str, ...]] = []
    for index, mark in enumerate(marks):
        if not isinstance(mark, dict) or set(mark) != {
            "start_operation_id",
            "semantic_path",
        }:
            errors.append(f"mark {index} has invalid keys")
            continue
        start = mark.get("start_operation_id")
        path = mark.get("semantic_path")
        if not isinstance(start, str) or start not in positions:
            errors.append(f"mark {index} start is not a turn first_operation_id")
        else:
            observed_starts.append(start)
        if not isinstance(path, list) or not path:
            errors.append(f"mark {index} semantic_path is empty")
            continue
        clean_path: list[str] = []
        for depth, label in enumerate(path):
            if not isinstance(label, str) or not LABEL_PATTERN.fullmatch(label):
                errors.append(
                    f"mark {index} depth {depth} tag violates action-first 1-3-word format"
                )
            else:
                clean_path.append(label)
        if len(clean_path) == len(path):
            observed_paths.append(tuple(clean_path))

    if observed_starts:
        if observed_starts[0] != turn_starts[0]:
            errors.append("first mark does not start at the first turn")
        numeric_positions = [positions[start] for start in observed_starts]
        if numeric_positions != sorted(set(numeric_positions)):
            errors.append("mark starts are not strictly ordered and unique")
    if len(observed_paths) == len(marks):
        roots = {path[0] for path in observed_paths}
        if len(roots) != 1:
            errors.append("mandatory session root is not identical across all paths")
        if any(left == right for left, right in zip(observed_paths, observed_paths[1:])):
            errors.append("adjacent marks repeat an unchanged complete path")
    return errors


def parse_codex_events(stdout: str) -> tuple[Any, dict[str, Any] | None, list[str]]:
    final_message = ""
    usage = None
    prohibited: list[str] = []
    for line in stdout.splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if event.get("type") == "turn.completed":
            usage = event.get("usage")
        item = event.get("item")
        if not isinstance(item, dict):
            continue
        item_type = str(item.get("type") or "")
        if item_type in PROHIBITED_ITEM_TYPES:
            prohibited.append(item_type)
        if event.get("type") == "item.completed" and item_type == "agent_message":
            final_message = str(item.get("text") or "")
    if not final_message:
        return None, usage, [*prohibited, "missing final agent message"]
    try:
        response = json.loads(final_message)
    except json.JSONDecodeError as error:
        return None, usage, [*prohibited, f"final message is not JSON: {error}"]
    return response, usage, prohibited


def prompt_for(packet: dict[str, Any], retry_errors: list[str] | None) -> str:
    retry = ""
    if retry_errors:
        retry = (
            "\nFORMAT RETRY. The previous response was rejected only for these "
            "schema/contract errors:\n- "
            + "\n- ".join(retry_errors)
            + "\nReturn a corrected complete object from the same source packet.\n"
        )
    return (
        SYSTEM_INSTRUCTION
        + retry
        + "\nSOURCE_PACKET\n"
        + json.dumps(packet, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        + "\n"
    )


def run_attempt(
    row: PacketRow, attempt: int, retry_errors: list[str] | None, timeout_seconds: int
) -> dict[str, Any]:
    temporary = Path(tempfile.mkdtemp(prefix="direct-annotation-backend-"))
    command = [
        "codex",
        "exec",
        "--model",
        MODEL,
        "--sandbox",
        "read-only",
        "--ephemeral",
        "--skip-git-repo-check",
        "--ignore-user-config",
        "--output-schema",
        str(SCHEMA),
        "--json",
        "--color",
        "never",
        "-C",
        str(temporary),
        "-",
    ]
    started_wall = time.time()
    started = time.monotonic()
    try:
        result = subprocess.run(
            command,
            input=prompt_for(row.packet, retry_errors),
            text=True,
            encoding="utf-8",
            capture_output=True,
            timeout=timeout_seconds,
            check=False,
        )
    except subprocess.TimeoutExpired as error:
        elapsed = time.monotonic() - started
        stdout = error.stdout if isinstance(error.stdout, str) else ""
        stderr = error.stderr if isinstance(error.stderr, str) else ""
        return {
            "attempt": attempt,
            "returncode": None,
            "started_unix": started_wall,
            "wall_seconds": elapsed,
            "stdout": stdout,
            "stderr": stderr,
            "response": None,
            "usage": None,
            "errors": [f"backend timeout after {timeout_seconds} seconds"],
        }
    finally:
        shutil.rmtree(temporary, ignore_errors=True)

    elapsed = time.monotonic() - started
    response, usage, event_errors = parse_codex_events(result.stdout)
    errors = list(event_errors)
    if result.returncode != 0:
        errors.append(f"codex exit status {result.returncode}")
    if usage is None:
        errors.append("missing Codex usage counters")
    if response is not None:
        errors.extend(validate_response(row.packet, response))
    return {
        "attempt": attempt,
        "returncode": result.returncode,
        "started_unix": started_wall,
        "wall_seconds": elapsed,
        "stdout": result.stdout,
        "stderr": result.stderr,
        "response": response,
        "usage": usage,
        "errors": errors,
    }


def write_attempt_artifacts(row: PacketRow, attempt: dict[str, Any]) -> None:
    RAW_EVENTS.mkdir(parents=True, exist_ok=True)
    prefix = RAW_EVENTS / f"{row.ordinal:04d}-attempt-{attempt['attempt']}"
    (prefix.with_suffix(".jsonl")).write_text(
        str(attempt["stdout"]), encoding="utf-8"
    )
    (prefix.with_suffix(".stderr.txt")).write_text(
        str(attempt["stderr"]), encoding="utf-8"
    )


def existing_ok(row: PacketRow) -> bool:
    if not row.raw_path.is_file():
        return False
    try:
        response = read_json(row.raw_path)
    except (json.JSONDecodeError, OSError):
        return False
    return not validate_response(row.packet, response)


def recover_orphan_attempt(row: PacketRow) -> dict[str, Any] | None:
    event_path = RAW_EVENTS / f"{row.ordinal:04d}-attempt-1.jsonl"
    stderr_path = RAW_EVENTS / f"{row.ordinal:04d}-attempt-1.stderr.txt"
    if row.raw_path.is_file() or not event_path.is_file():
        return None
    stdout = event_path.read_text(encoding="utf-8")
    stderr = (
        stderr_path.read_text(encoding="utf-8")
        if stderr_path.is_file()
        else ""
    )
    response, usage, event_errors = parse_codex_events(stdout)
    errors = list(event_errors)
    if usage is None:
        errors.append("missing Codex usage counters")
    if response is not None:
        errors.extend(validate_response(row.packet, response))

    completed_at = event_path.stat().st_mtime
    prior_ends: list[float] = []
    if RUN_RECORDS.is_file():
        for line in RUN_RECORDS.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            record = json.loads(line)
            if int(record.get("ordinal", 0)) >= row.ordinal:
                continue
            for attempt in record.get("attempt_records", []):
                started = attempt.get("started_unix")
                wall = attempt.get("wall_seconds")
                if isinstance(started, (int, float)) and isinstance(
                    wall, (int, float)
                ):
                    end = float(started) + float(wall)
                    if end <= completed_at:
                        prior_ends.append(end)
    started_at = min(prior_ends) if prior_ends else completed_at
    wall_seconds = max(0.0, completed_at - started_at)
    return {
        "attempt": 1,
        "returncode": 0,
        "started_unix": started_at,
        "wall_seconds": wall_seconds,
        "stdout": stdout,
        "stderr": stderr,
        "response": response,
        "usage": usage,
        "errors": errors,
        "recovered_after_interruption": True,
        "timing_basis": (
            "artifact completion mtime minus earliest prior worker completion"
            if prior_ends
            else "duration unavailable; artifact completion mtime only"
        ),
    }


def annotate_one(row: PacketRow, timeout_seconds: int) -> dict[str, Any]:
    attempts: list[dict[str, Any]] = []
    recovered = recover_orphan_attempt(row)
    if recovered is not None:
        attempts.append(recovered)
        if not recovered["errors"]:
            write_json(row.raw_path, recovered["response"])
    retry_errors = list(attempts[-1]["errors"]) if attempts else None
    for attempt_number in range(len(attempts) + 1, 3):
        if attempts and not attempts[-1]["errors"]:
            break
        attempt = run_attempt(row, attempt_number, retry_errors, timeout_seconds)
        write_attempt_artifacts(row, attempt)
        attempts.append(attempt)
        if not attempt["errors"]:
            write_json(row.raw_path, attempt["response"])
            break
        retry_errors = list(attempt["errors"])

    final_ok = bool(attempts) and not attempts[-1]["errors"]
    record = {
        "ordinal": row.ordinal,
        "session": row.session,
        "framework": row.packet["framework"],
        "turns": row.packet["turn_count"],
        "operations": row.packet["operation_count"],
        "status": "ok" if final_ok else "failed",
        "attempts": len(attempts),
        "format_retry": len(attempts) == 2,
        "worker_pattern": "isolated one-trajectory Codex CLI calls",
        "model": MODEL,
        "attempt_records": [
            {
                "attempt": attempt["attempt"],
                "returncode": attempt["returncode"],
                "started_unix": attempt["started_unix"],
                "wall_seconds": round(float(attempt["wall_seconds"]), 6),
                "usage": attempt["usage"],
                "errors": attempt["errors"],
                "recovered_after_interruption": bool(
                    attempt.get("recovered_after_interruption")
                ),
                "timing_basis": attempt.get("timing_basis", "direct monotonic timer"),
            }
            for attempt in attempts
        ],
    }
    with RECORD_LOCK:
        with RUN_RECORDS.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(record, sort_keys=True) + "\n")
    return record


def completed_ordinals() -> set[int]:
    rows = load_packets()
    return {row.ordinal for row in rows if existing_ok(row)}


def run_population(
    selected: list[PacketRow], workers: int, timeout_seconds: int
) -> None:
    RAW_MARKS.mkdir(parents=True, exist_ok=True)
    pending = [row for row in selected if not existing_ok(row)]
    print(
        json.dumps(
            {
                "status": "starting",
                "selected": len(selected),
                "already_complete": len(selected) - len(pending),
                "pending": len(pending),
                "workers": workers,
            },
            sort_keys=True,
        ),
        flush=True,
    )
    if not pending:
        return
    failures = 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {
            executor.submit(annotate_one, row, timeout_seconds): row for row in pending
        }
        for completed, future in enumerate(
            concurrent.futures.as_completed(futures), 1
        ):
            row = futures[future]
            try:
                record = future.result()
            except Exception as error:
                failures += 1
                print(
                    json.dumps(
                        {
                            "completed_now": completed,
                            "ordinal": row.ordinal,
                            "session": row.session,
                            "status": "harness-failed",
                            "error": str(error),
                        },
                        sort_keys=True,
                    ),
                    flush=True,
                )
                continue
            if record["status"] != "ok":
                failures += 1
            usage = record["attempt_records"][-1].get("usage") or {}
            print(
                json.dumps(
                    {
                        "completed_now": completed,
                        "total_complete": len(completed_ordinals()),
                        "ordinal": row.ordinal,
                        "session": row.session,
                        "status": record["status"],
                        "attempts": record["attempts"],
                        "wall_seconds": sum(
                            item["wall_seconds"] for item in record["attempt_records"]
                        ),
                        "input_tokens": usage.get("input_tokens"),
                        "output_tokens": usage.get("output_tokens"),
                    },
                    sort_keys=True,
                ),
                flush=True,
            )
    print(
        json.dumps(
            {
                "status": "finished",
                "complete": len(completed_ordinals()),
                "failed_in_this_run": failures,
            },
            sort_keys=True,
        ),
        flush=True,
    )


def package_annotations(mode: str) -> None:
    rows = load_packets()
    if mode == "preflight":
        selected = [
            min(rows, key=lambda row: (int(row.packet["turn_count"]), row.session))
        ]
    elif mode == "pilot":
        selected = rows[:PILOT_SESSIONS]
    else:
        selected = rows
    missing = [row.session for row in selected if not existing_ok(row)]
    if missing:
        raise RuntimeError(f"cannot package missing annotations: {missing[:3]}")
    sessions = [read_json(row.raw_path) for row in selected]
    annotation_dir = (
        PREFLIGHT / "annotations"
        if mode == "preflight"
        else PILOT / "annotations"
        if mode == "pilot"
        else RAW_ANNOTATIONS
    )
    write_json(
        annotation_dir / "batch-01.json",
        {"batch": "batch-01", "sessions": sessions},
    )
    if mode in {"preflight", "pilot"}:
        packet_dir = PREFLIGHT / "packets" if mode == "preflight" else PILOT / "packets"
        source_payload = {
            "schema": "agentsight.agent-operation-annotation-packet.v1",
            "sessions": [row.packet for row in selected],
        }
        source_payload = {
            **source_payload,
            "sessions": [row.packet for row in selected],
        }
        write_json(packet_dir / "batch-01.json", source_payload)
        write_json(
            packet_dir / "manifest.json",
            {
                "schema": "agentsight.agent-operation-annotation-packet.manifest.v1",
                "selection": (
                    "one smallest real trajectory; recipe validation only"
                    if mode == "preflight"
                    else "first 40 trajectory IDs in sorted order; binding pilot"
                ),
                "sessions": len(selected),
                "turns": sum(int(row.packet["turn_count"]) for row in selected),
                "operations": sum(
                    int(row.packet["operation_count"]) for row in selected
                ),
                "batches": [
                    {
                        "file": "batch-01.json",
                        "sessions": len(selected),
                        "turns": sum(
                            int(row.packet["turn_count"]) for row in selected
                        ),
                        "operations": sum(
                            int(row.packet["operation_count"]) for row in selected
                        ),
                        "session_ids": [row.session for row in selected],
                    }
                ],
            },
        )
    print(
        json.dumps(
            {
                "status": "ok",
                "mode": mode,
                "sessions": len(selected),
                "annotations": sum(len(row["marks"]) for row in sessions),
                "output": str(annotation_dir.relative_to(EXPERIMENT)),
            },
            sort_keys=True,
        ),
        flush=True,
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("prepare")
    preflight = commands.add_parser("preflight")
    preflight.add_argument("--timeout-seconds", type=int, default=DEFAULT_TIMEOUT_SECONDS)
    pilot = commands.add_parser("pilot")
    pilot.add_argument("--workers", type=int, default=DEFAULT_WORKERS)
    pilot.add_argument("--timeout-seconds", type=int, default=DEFAULT_TIMEOUT_SECONDS)
    full = commands.add_parser("full")
    full.add_argument("--workers", type=int, default=DEFAULT_WORKERS)
    full.add_argument("--timeout-seconds", type=int, default=DEFAULT_TIMEOUT_SECONDS)
    package = commands.add_parser("package")
    package.add_argument("--preflight", action="store_true")
    package.add_argument("--pilot", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    rows = load_packets()
    if args.command == "prepare":
        prepare()
    elif args.command == "preflight":
        selected = [min(rows, key=lambda row: (int(row.packet["turn_count"]), row.session))]
        run_population(selected, 1, args.timeout_seconds)
        package_annotations(mode="preflight")
    elif args.command == "pilot":
        if args.workers < 1:
            raise SystemExit("--workers must be positive")
        run_population(rows[:PILOT_SESSIONS], args.workers, args.timeout_seconds)
        package_annotations(mode="pilot")
    elif args.command == "full":
        if args.workers < 1:
            raise SystemExit("--workers must be positive")
        run_population(rows, args.workers, args.timeout_seconds)
    else:
        if args.command != "package":
            raise RuntimeError("unknown command")
        if args.preflight and args.pilot:
            raise SystemExit("--preflight and --pilot are mutually exclusive")
        package_annotations(
            mode="preflight" if args.preflight else "pilot" if args.pilot else "full"
        )


if __name__ == "__main__":
    main()
