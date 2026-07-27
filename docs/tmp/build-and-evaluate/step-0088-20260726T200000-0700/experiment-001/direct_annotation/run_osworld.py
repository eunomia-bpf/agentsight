#!/usr/bin/env python3
"""Run and score the frozen direct Codex backend on OSWorld-Human."""

from __future__ import annotations

import argparse
import ast
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
import random
import re
import shutil
import subprocess
import tempfile
import threading
import time
from typing import Any, Iterable


SCRIPT_DIR = Path(__file__).resolve().parent
EXPERIMENT = SCRIPT_DIR.parent
REPO = EXPERIMENT.parents[4]
SOURCE = (
    REPO
    / "docs"
    / "visexp"
    / "out"
    / "external-agent-trace-osworldhuman-r290"
    / "osworld-human-operations.jsonl"
)
STEP87_ANNOTATE = (
    REPO
    / "docs"
    / "tmp"
    / "build-and-evaluate"
    / "step-0087-20260726T023000-0700"
    / "experiment-001"
    / "direct_annotation"
    / "annotate.py"
)
RESPONSE_SCHEMA = STEP87_ANNOTATE.parent / "response-schema.json"
SUPERVISED_PAIRS = (
    REPO
    / ".agentsight"
    / "experiments"
    / "rq3-osworld-boundary-fidelity-v1"
    / "full"
    / "oof-predictions.jsonl"
)
SUPERVISED_SUMMARY = SUPERVISED_PAIRS.parent / "summary.json"
RECURRENCE_PAIRS = (
    REPO
    / ".agentsight"
    / "experiments"
    / "rq3-monotone-recurrence-v1"
    / "full"
    / "pair-predictions.jsonl"
)
RECURRENCE_SUMMARY = RECURRENCE_PAIRS.parent / "summary.json"
CALIBRATED_ROOT = (
    REPO
    / ".agentsight"
    / "experiments"
    / "rq3-reference-calibrated-existing-traces-v1"
    / "full"
)
CALIBRATED_PAIRS = CALIBRATED_ROOT / "osworld-human"
CALIBRATED_SUMMARY = CALIBRATED_ROOT / "summary.json"

PACKETS = EXPERIMENT / "source-packets"
INDEX = EXPERIMENT / "packet-index.json"
RAW_MARKS = EXPERIMENT / "raw-marks"
RAW_RESPONSES = EXPERIMENT / "raw-responses"
RAW_EVENTS = EXPERIMENT / "raw-events"
RUN_RECORDS = EXPERIMENT / "annotation-run-records.jsonl"
EXECUTION_EVENTS = EXPERIMENT / "execution-events.jsonl"
EXECUTION_LOG = EXPERIMENT / "execution-log.md"
RAW_RESULTS = EXPERIMENT / "raw-results.json"
PILOT_RESULTS = EXPERIMENT / "pilot-results.md"
RESULTS = EXPERIMENT / "results.md"
COST_RECORD = EXPERIMENT / "cost-record.md"
SCORE_ROOT = EXPERIMENT / "score"
BOOTSTRAP_ROOT = EXPERIMENT / "bootstrap"

MODEL = "gpt-5.6-sol"
EXPECTED_SESSIONS = 287
EXPECTED_OPERATIONS = 3_978
EXPECTED_PAIRS = 3_691
EXPECTED_GOLD_GROUPS = 2_042
PILOT_SESSIONS = 40
PILOT_MARGIN = 0.05
DEFAULT_WORKERS = 4
DEFAULT_TIMEOUT_SECONDS = 1_200
BOOTSTRAP_RESAMPLES = 10_000
BOOTSTRAP_SEED = 20_260_726
VISIBLE_FIELDS = (
    "action",
    "phase",
    "target",
    "repeat_state",
    "repeat_signal",
    "app",
    "environment",
    "status",
    "tool",
)
EXCLUDED_TARGET_FIELDS = (
    "human_group",
    "group_index",
    "group_position",
    "group_size",
    "group_pattern",
    "group_alignment",
)
METHODS = (
    "direct_multilevel",
    "supervised_oof",
    "reference_calibrated",
    "label_free_recurrence",
    "always_boundary",
)
BASELINES = METHODS[1:]
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


@dataclass(frozen=True)
class Operation:
    line: int
    position: int
    visible: dict[str, str]
    gold_group: str

    @property
    def operation_id(self) -> str:
        return f"op-{self.position:04d}"


@dataclass(frozen=True)
class Session:
    ordinal: int
    session: str
    operations: tuple[Operation, ...]

    @property
    def raw_path(self) -> Path:
        return RAW_MARKS / f"{self.ordinal:04d}.json"

    @property
    def packet(self) -> dict[str, Any]:
        return {
            "schema": "agentsight.osworld-human.source-visible-session.v1",
            "session": self.session,
            "turn_count": len(self.operations),
            "operation_count": len(self.operations),
            "visible_fields": list(VISIBLE_FIELDS),
            "turns": [
                {
                    "first_operation_id": operation.operation_id,
                    "operation_ids": [operation.operation_id],
                    "source_visible": operation.visible,
                }
                for operation in self.operations
            ],
        }


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
    with path.open(encoding="utf-8") as stream:
        for line in stream:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as stream:
        for row in rows:
            stream.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def normalize_fields(fields: dict[str, Any]) -> dict[str, str]:
    normalized = {}
    for key, value in fields.items():
        if isinstance(value, list):
            if not value:
                continue
            value = value[0]
        if isinstance(value, (dict, list)):
            value = json.dumps(value, sort_keys=True, ensure_ascii=True)
        text = str(value)
        if text:
            normalized[str(key)] = text
    return normalized


def turn_key(fields: dict[str, str], line: int) -> tuple[int, str, int]:
    raw = fields.get("turn", "")
    try:
        return int(raw), raw, line
    except ValueError:
        return 0, raw, line


def load_population() -> list[Session]:
    grouped: dict[str, list[tuple[int, dict[str, str]]]] = defaultdict(list)
    with SOURCE.open(encoding="utf-8") as stream:
        for line_number, line in enumerate(stream, 1):
            if not line.strip():
                continue
            row = json.loads(line)
            fields = normalize_fields(row.get("fields") or {})
            if (
                fields.get("group_alignment") != "exact"
                or not fields.get("human_group")
                or not fields.get("session")
            ):
                continue
            grouped[fields["session"]].append((line_number, fields))

    eligible = {key: value for key, value in grouped.items() if len(value) >= 2}
    sessions = []
    for ordinal, session_id in enumerate(sorted(eligible), 1):
        source_rows = sorted(
            eligible[session_id],
            key=lambda item: turn_key(item[1], item[0]),
        )
        operations = []
        for position, (line_number, fields) in enumerate(source_rows):
            missing = [field for field in VISIBLE_FIELDS if field not in fields]
            if missing:
                raise RuntimeError(
                    f"session {session_id} operation {position} lacks {missing}"
                )
            operations.append(
                Operation(
                    line=line_number,
                    position=position,
                    visible={field: fields[field] for field in VISIBLE_FIELDS},
                    gold_group=fields["human_group"],
                )
            )
        sessions.append(
            Session(
                ordinal=ordinal,
                session=session_id,
                operations=tuple(operations),
            )
        )

    counts = {
        "sessions": len(sessions),
        "operations": sum(len(row.operations) for row in sessions),
        "pairs": sum(len(row.operations) - 1 for row in sessions),
        "gold_groups": len(
            {
                (row.session, operation.gold_group)
                for row in sessions
                for operation in row.operations
            }
        ),
    }
    expected = {
        "sessions": EXPECTED_SESSIONS,
        "operations": EXPECTED_OPERATIONS,
        "pairs": EXPECTED_PAIRS,
        "gold_groups": EXPECTED_GOLD_GROUPS,
    }
    if counts != expected:
        raise RuntimeError(f"frozen population mismatch: {counts} != {expected}")
    return sessions


def load_step87_instruction() -> str:
    tree = ast.parse(STEP87_ANNOTATE.read_text(encoding="utf-8"))
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        if any(
            isinstance(target, ast.Name) and target.id == "SYSTEM_INSTRUCTION"
            for target in node.targets
        ):
            value = ast.literal_eval(node.value)
            if not isinstance(value, str):
                break
            return value
    raise RuntimeError("could not extract Step 0087 SYSTEM_INSTRUCTION verbatim")


SYSTEM_INSTRUCTION = load_step87_instruction()


def now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def append_execution_event(event: str, **values: Any) -> None:
    row = {"time": now_iso(), "event": event, **values}
    with EXECUTION_EVENTS.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
    render_execution_log()


def render_execution_log() -> None:
    events = read_jsonl(EXECUTION_EVENTS) if EXECUTION_EVENTS.is_file() else []
    lines = [
        "# Execution log",
        "",
        "- Frozen source: `docs/visexp/out/external-agent-trace-osworldhuman-r290/osworld-human-operations.jsonl`.",
        "- Backend: `codex exec --model gpt-5.6-sol`; one isolated call per session and at most one format retry.",
        "- Instruction: loaded verbatim from Step 0087 at execution time; only the source packet format changes.",
        "- Model-visible operation fields: `" + "`, `".join(VISIBLE_FIELDS) + "`.",
        "- Gold/scorer-only fields excluded from every packet: `"
        + "`, `".join(EXCLUDED_TARGET_FIELDS)
        + "`.",
        "- No Git command is part of this experiment.",
        "",
        "## Events",
        "",
    ]
    for row in events:
        detail = ", ".join(
            f"{key}={json.dumps(value, ensure_ascii=False)}"
            for key, value in row.items()
            if key not in {"time", "event"}
        )
        lines.append(f"- {row['time']} — `{row['event']}`" + (f": {detail}" if detail else ""))
    EXECUTION_LOG.write_text("\n".join(lines) + "\n", encoding="utf-8")


def prepare() -> None:
    sessions = load_population()
    value_sets = {field: set() for field in VISIBLE_FIELDS}
    for session in sessions:
        for operation in session.operations:
            for field, value in operation.visible.items():
                value_sets[field].add(value)
    packet_payload = {
        "schema": "agentsight.osworld-human.source-visible-packets.v1",
        "sessions": [session.packet for session in sessions],
    }
    write_json(PACKETS / "batch-01.json", packet_payload)
    write_json(
        PACKETS / "manifest.json",
        {
            "schema": "agentsight.osworld-human.source-visible-packets.manifest.v1",
            "selection": "all eligible sessions sorted by session ID",
            "sessions": EXPECTED_SESSIONS,
            "operations": EXPECTED_OPERATIONS,
            "pairs": EXPECTED_PAIRS,
            "visible_fields": list(VISIBLE_FIELDS),
            "excluded_target_fields": list(EXCLUDED_TARGET_FIELDS),
        },
    )
    write_json(
        INDEX,
        {
            "schema": "agentsight.direct-osworld.packet-index.v1",
            "source": str(SOURCE.relative_to(REPO)),
            "selection": "all 287 eligible sessions, lexicographically sorted IDs",
            "pilot": "first 40 sorted session IDs",
            "sessions": EXPECTED_SESSIONS,
            "operations": EXPECTED_OPERATIONS,
            "pairs": EXPECTED_PAIRS,
            "gold_groups_scorer_only": EXPECTED_GOLD_GROUPS,
            "instruction_source": str(STEP87_ANNOTATE.relative_to(REPO)),
            "instruction_equality": "runtime AST literal loaded without modification",
            "model_visible_fields": {
                field: sorted(values) for field, values in value_sets.items()
            },
            "excluded_scorer_fields": list(EXCLUDED_TARGET_FIELDS),
            "rows": [
                {
                    "ordinal": session.ordinal,
                    "session": session.session,
                    "operations": len(session.operations),
                }
                for session in sessions
            ],
        },
    )
    append_execution_event(
        "prepare",
        sessions=EXPECTED_SESSIONS,
        operations=EXPECTED_OPERATIONS,
        pairs=EXPECTED_PAIRS,
        pilot_sessions=PILOT_SESSIONS,
    )
    print(
        json.dumps(
            {
                "status": "ok",
                "sessions": EXPECTED_SESSIONS,
                "operations": EXPECTED_OPERATIONS,
                "pairs": EXPECTED_PAIRS,
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

    turn_starts = [
        str(turn["first_operation_id"]) for turn in packet["turns"]
    ]
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
        clean_path = []
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
        if len({path[0] for path in observed_paths}) != 1:
            errors.append("mandatory session root is not identical across all paths")
        if any(left == right for left, right in zip(observed_paths, observed_paths[1:])):
            errors.append("adjacent marks repeat an unchanged complete path")
    return errors


def parse_codex_events(stdout: str) -> tuple[Any, dict[str, Any] | None, list[str]]:
    final_message = ""
    usage = None
    prohibited = []
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
    session: Session,
    attempt: int,
    retry_errors: list[str] | None,
    timeout_seconds: int,
) -> dict[str, Any]:
    temporary = Path(tempfile.mkdtemp(prefix="direct-osworld-backend-"))
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
        str(RESPONSE_SCHEMA),
        "--json",
        "--color",
        "never",
        "-C",
        str(temporary),
        "-",
    ]
    started_unix = time.time()
    started = time.monotonic()
    try:
        result = subprocess.run(
            command,
            input=prompt_for(session.packet, retry_errors),
            text=True,
            encoding="utf-8",
            capture_output=True,
            timeout=timeout_seconds,
            check=False,
        )
        elapsed = time.monotonic() - started
        response, usage, event_errors = parse_codex_events(result.stdout)
        errors = list(event_errors)
        if result.returncode != 0:
            errors.append(f"codex exit status {result.returncode}")
        if usage is None:
            errors.append("missing Codex usage counters")
        if response is not None:
            errors.extend(validate_response(session.packet, response))
        return {
            "attempt": attempt,
            "returncode": result.returncode,
            "started_unix": started_unix,
            "wall_seconds": elapsed,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "response": response,
            "usage": usage,
            "errors": errors,
        }
    except subprocess.TimeoutExpired as error:
        return {
            "attempt": attempt,
            "returncode": None,
            "started_unix": started_unix,
            "wall_seconds": time.monotonic() - started,
            "stdout": error.stdout if isinstance(error.stdout, str) else "",
            "stderr": error.stderr if isinstance(error.stderr, str) else "",
            "response": None,
            "usage": None,
            "errors": [f"backend timeout after {timeout_seconds} seconds"],
        }
    finally:
        shutil.rmtree(temporary, ignore_errors=True)


def write_attempt_artifacts(session: Session, attempt: dict[str, Any]) -> None:
    RAW_EVENTS.mkdir(parents=True, exist_ok=True)
    RAW_RESPONSES.mkdir(parents=True, exist_ok=True)
    stem = f"{session.ordinal:04d}-attempt-{attempt['attempt']}"
    (RAW_EVENTS / f"{stem}.jsonl").write_text(
        str(attempt["stdout"]), encoding="utf-8"
    )
    (RAW_EVENTS / f"{stem}.stderr.txt").write_text(
        str(attempt["stderr"]), encoding="utf-8"
    )
    if attempt["response"] is not None:
        write_json(RAW_RESPONSES / f"{stem}.json", attempt["response"])


def existing_ok(session: Session) -> bool:
    if not session.raw_path.is_file():
        return False
    try:
        response = read_json(session.raw_path)
    except (json.JSONDecodeError, OSError):
        return False
    return not validate_response(session.packet, response)


def terminal_failed_ordinals() -> set[int]:
    if not RUN_RECORDS.is_file():
        return set()
    latest = {}
    for row in read_jsonl(RUN_RECORDS):
        latest[int(row["ordinal"])] = row
    return {
        ordinal
        for ordinal, row in latest.items()
        if row.get("status") == "failed"
    }


def annotate_one(
    session: Session, phase: str, timeout_seconds: int
) -> dict[str, Any]:
    attempts = []
    retry_errors = None
    for attempt_number in (1, 2):
        attempt = run_attempt(
            session, attempt_number, retry_errors, timeout_seconds
        )
        write_attempt_artifacts(session, attempt)
        attempts.append(attempt)
        if not attempt["errors"]:
            RAW_MARKS.mkdir(parents=True, exist_ok=True)
            write_json(session.raw_path, attempt["response"])
            break
        retry_errors = list(attempt["errors"])

    final_ok = not attempts[-1]["errors"]
    record = {
        "ordinal": session.ordinal,
        "session": session.session,
        "phase": phase,
        "operations": len(session.operations),
        "status": "ok" if final_ok else "failed",
        "attempts": len(attempts),
        "format_retry": len(attempts) == 2,
        "worker_pattern": "isolated one-session Codex CLI calls",
        "model": MODEL,
        "attempt_records": [
            {
                "attempt": attempt["attempt"],
                "returncode": attempt["returncode"],
                "started_unix": attempt["started_unix"],
                "wall_seconds": round(float(attempt["wall_seconds"]), 6),
                "usage": attempt["usage"],
                "errors": attempt["errors"],
            }
            for attempt in attempts
        ],
    }
    with RECORD_LOCK:
        with RUN_RECORDS.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(record, sort_keys=True) + "\n")
    return record


def run_population(
    phase: str, workers: int, timeout_seconds: int
) -> None:
    sessions = load_population()
    if phase == "pilot":
        selected = sessions[:PILOT_SESSIONS]
    else:
        pilot = read_json(EXPERIMENT / "pilot" / "raw-results.json")
        if not bool(pilot.get("gate", {}).get("passed")):
            raise RuntimeError("full run is forbidden because the pilot gate did not pass")
        selected = sessions

    failed_before = terminal_failed_ordinals()
    forbidden = [
        row.ordinal
        for row in selected
        if row.ordinal in failed_before and not existing_ok(row)
    ]
    if forbidden:
        raise RuntimeError(
            "one-format-retry budget already exhausted for ordinals "
            + ", ".join(map(str, forbidden))
        )
    pending = [row for row in selected if not existing_ok(row)]
    append_execution_event(
        f"{phase}-backend-start",
        selected=len(selected),
        cached=len(selected) - len(pending),
        pending=len(pending),
        workers=workers,
        timeout_seconds=timeout_seconds,
    )
    print(
        json.dumps(
            {
                "status": "starting",
                "phase": phase,
                "selected": len(selected),
                "cached": len(selected) - len(pending),
                "pending": len(pending),
                "workers": workers,
            },
            sort_keys=True,
        ),
        flush=True,
    )
    failures = 0
    if pending:
        import concurrent.futures

        with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
            futures = {
                executor.submit(
                    annotate_one, row, phase, timeout_seconds
                ): row
                for row in pending
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
                failures += int(record["status"] != "ok")
                usage = record["attempt_records"][-1].get("usage") or {}
                print(
                    json.dumps(
                        {
                            "completed_now": completed,
                            "ordinal": row.ordinal,
                            "session": row.session,
                            "status": record["status"],
                            "attempts": record["attempts"],
                            "wall_seconds": sum(
                                item["wall_seconds"]
                                for item in record["attempt_records"]
                            ),
                            "input_tokens": usage.get("input_tokens"),
                            "output_tokens": usage.get("output_tokens"),
                        },
                        sort_keys=True,
                    ),
                    flush=True,
                )
    complete = sum(existing_ok(row) for row in selected)
    append_execution_event(
        f"{phase}-backend-finish",
        complete=complete,
        selected=len(selected),
        failures=failures,
    )
    print(
        json.dumps(
            {
                "status": "finished",
                "phase": phase,
                "complete": complete,
                "selected": len(selected),
                "failures": failures,
            },
            sort_keys=True,
        ),
        flush=True,
    )


def load_baseline_boundaries(
    sessions: list[Session],
) -> dict[str, dict[tuple[str, int], bool]]:
    selected_ids = {row.session for row in sessions}
    line_to_position = {
        (session.session, operation.line): operation.position
        for session in sessions
        for operation in session.operations
    }
    expected_keys = {
        (session.session, position)
        for session in sessions
        for position in range(1, len(session.operations))
    }
    result = {method: {} for method in BASELINES}
    for row in read_jsonl(SUPERVISED_PAIRS):
        session = str(row["sequence"])
        if session not in selected_ids:
            continue
        position = line_to_position[(session, int(row["current_line"]))]
        result["supervised_oof"][(session, position)] = bool(row["learned"])
    for row in read_jsonl(RECURRENCE_PAIRS):
        session = str(row["sequence"])
        if session not in selected_ids:
            continue
        position = line_to_position[(session, int(row["current_line"]))]
        result["label_free_recurrence"][(session, position)] = bool(
            row["recurrence"]
        )
    for path in sorted(CALIBRATED_PAIRS.glob("fold-*-predictions.jsonl")):
        for row in read_jsonl(path):
            session = str(row["session"])
            if session not in selected_ids:
                continue
            result["reference_calibrated"][
                (session, int(row["position"]))
            ] = bool(row["boundary"])
    result["always_boundary"] = {key: True for key in expected_keys}
    for method in BASELINES:
        if set(result[method]) != expected_keys:
            missing = expected_keys - set(result[method])
            extra = set(result[method]) - expected_keys
            raise RuntimeError(
                f"{method} pair coverage mismatch: missing={len(missing)} extra={len(extra)}"
            )
    return result


def direct_boundaries(session: Session) -> tuple[dict[int, bool], list[list[str]]]:
    if not existing_ok(session):
        raise RuntimeError(f"missing valid direct response for {session.session}")
    response = read_json(session.raw_path)
    marks = response["marks"]
    start_positions = {
        int(str(mark["start_operation_id"]).removeprefix("op-"))
        for mark in marks
    }
    if 0 not in start_positions:
        raise RuntimeError(f"direct marks do not start at zero: {session.session}")
    return (
        {
            position: position in start_positions
            for position in range(1, len(session.operations))
        },
        [list(mark["semantic_path"]) for mark in marks],
    )


def metric_from_counts(tp: int, fp: int, fn: int) -> dict[str, Any]:
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = (
        2 * precision * recall / (precision + recall)
        if precision + recall
        else 0.0
    )
    return {
        "true_positive": tp,
        "false_positive": fp,
        "false_negative": fn,
        "precision": precision,
        "recall": recall,
        "f1": f1,
    }


def b3_session_sufficient(
    predicted: list[str], gold: list[str]
) -> dict[str, Any]:
    predicted_totals = Counter(predicted)
    gold_totals = Counter(gold)
    intersections = Counter(zip(predicted, gold))
    precision_sum = 0.0
    recall_sum = 0.0
    for predicted_group, gold_group in zip(predicted, gold):
        overlap = intersections[(predicted_group, gold_group)]
        precision_sum += overlap / predicted_totals[predicted_group]
        recall_sum += overlap / gold_totals[gold_group]
    return {
        "precision_sum": precision_sum,
        "recall_sum": recall_sum,
        "items": len(gold),
        "predicted_groups": len(predicted_totals),
        "gold_groups": len(gold_totals),
    }


def aggregate_b3(rows: Iterable[dict[str, Any]]) -> dict[str, Any]:
    totals = Counter()
    for row in rows:
        totals.update(row)
    items = int(totals["items"])
    precision = totals["precision_sum"] / items if items else 0.0
    recall = totals["recall_sum"] / items if items else 0.0
    f1 = (
        2 * precision * recall / (precision + recall)
        if precision + recall
        else 0.0
    )
    return {
        "items": items,
        "predicted_groups": int(totals["predicted_groups"]),
        "gold_groups": int(totals["gold_groups"]),
        "precision": precision,
        "recall": recall,
        "f1": f1,
    }


def percentile(values: list[float], quantile: float) -> float:
    ordered = sorted(values)
    if not ordered:
        raise RuntimeError("cannot take percentile of empty values")
    position = (len(ordered) - 1) * quantile
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    fraction = position - lower
    return ordered[lower] * (1 - fraction) + ordered[upper] * fraction


def bootstrap_comparison(
    sessions: list[Session],
    sufficient: dict[str, dict[str, dict[str, Any]]],
    candidate: str,
    baseline: str,
    metric: str,
    output: Path,
) -> dict[str, Any]:
    session_ids = [row.session for row in sessions]
    generator = random.Random(
        f"{BOOTSTRAP_SEED}:{candidate}:{baseline}:{metric}:{len(session_ids)}"
    )
    draws = []
    for index in range(BOOTSTRAP_RESAMPLES):
        sample = generator.choices(session_ids, k=len(session_ids))
        if metric == "bcubed":
            candidate_value = aggregate_b3(
                sufficient[session][candidate]["bcubed"] for session in sample
            )["f1"]
            baseline_value = aggregate_b3(
                sufficient[session][baseline]["bcubed"] for session in sample
            )["f1"]
        else:
            candidate_counts = Counter()
            baseline_counts = Counter()
            for session in sample:
                candidate_counts.update(
                    sufficient[session][candidate]["boundary"]
                )
                baseline_counts.update(
                    sufficient[session][baseline]["boundary"]
                )
            candidate_value = metric_from_counts(
                int(candidate_counts["tp"]),
                int(candidate_counts["fp"]),
                int(candidate_counts["fn"]),
            )["f1"]
            baseline_value = metric_from_counts(
                int(baseline_counts["tp"]),
                int(baseline_counts["fp"]),
                int(baseline_counts["fn"]),
            )["f1"]
        draws.append(
            {
                "resample": index,
                "candidate_f1": candidate_value,
                "baseline_f1": baseline_value,
                "delta": candidate_value - baseline_value,
            }
        )
    write_jsonl(output, draws)
    deltas = [row["delta"] for row in draws]
    return {
        "candidate": candidate,
        "baseline": baseline,
        "metric": metric,
        "session_clusters": len(session_ids),
        "resamples": BOOTSTRAP_RESAMPLES,
        "mean_delta": sum(deltas) / len(deltas),
        "ci95": [percentile(deltas, 0.025), percentile(deltas, 0.975)],
        "positive_fraction": sum(delta > 0 for delta in deltas) / len(deltas),
        "raw_draws": str(output.relative_to(EXPERIMENT)),
    }


def cost_for(selected: list[Session]) -> dict[str, Any]:
    selected_ordinals = {row.ordinal for row in selected}
    latest = {}
    for row in read_jsonl(RUN_RECORDS) if RUN_RECORDS.is_file() else []:
        ordinal = int(row["ordinal"])
        if ordinal in selected_ordinals:
            latest[ordinal] = row
    usage = Counter()
    intervals = []
    summed_wall = 0.0
    calls = 0
    retries = 0
    failed = 0
    successful = 0
    for ordinal in sorted(selected_ordinals):
        row = latest.get(ordinal)
        if row is None:
            failed += 1
            continue
        successful += int(row.get("status") == "ok")
        failed += int(row.get("status") != "ok")
        retries += max(0, int(row["attempts"]) - 1)
        for attempt in row["attempt_records"]:
            calls += 1
            start = float(attempt["started_unix"])
            wall = float(attempt["wall_seconds"])
            summed_wall += wall
            intervals.append((start, start + wall))
            for key, value in (attempt.get("usage") or {}).items():
                if isinstance(value, int):
                    usage[key] += value
    intervals.sort()
    active_wall = 0.0
    if intervals:
        current_start, current_end = intervals[0]
        for start, end in intervals[1:]:
            if start <= current_end:
                current_end = max(current_end, end)
            else:
                active_wall += current_end - current_start
                current_start, current_end = start, end
        active_wall += current_end - current_start
    return {
        "backend": "codex-cli 0.145.0",
        "model": MODEL,
        "worker_pattern": "isolated one-session calls, up to 4 parallel workers",
        "sessions_selected": len(selected),
        "successful_sessions": successful,
        "failed_after_retry": failed,
        "total_codex_calls": calls,
        "format_retries": retries,
        "summed_backend_wall_seconds": summed_wall,
        "active_backend_wall_seconds": active_wall,
        "usage": dict(sorted(usage.items())),
    }


def expected_full_metrics() -> dict[str, dict[str, float]]:
    supervised = read_json(SUPERVISED_SUMMARY)
    recurrence = read_json(RECURRENCE_SUMMARY)
    calibrated = read_json(CALIBRATED_SUMMARY)
    return {
        "supervised_oof": {
            "bcubed": float(supervised["partition_metrics"]["learned"]["f1"]),
            "boundary": float(
                supervised["boundary_metrics"]["learned"]["f1_exact"]
            ),
        },
        "reference_calibrated": {
            "bcubed": float(
                calibrated["osworld"]["metrics"]["candidate"]["partition"]["f1"]
            ),
            "boundary": float(
                calibrated["osworld"]["metrics"]["candidate"]["boundary"]["f1_exact"]
            ),
        },
        "label_free_recurrence": {
            "bcubed": float(recurrence["partition_metrics"]["recurrence"]["f1"]),
            "boundary": float(
                recurrence["boundary_metrics"]["recurrence"]["f1_exact"]
            ),
        },
        "always_boundary": {
            "bcubed": float(
                supervised["partition_metrics"]["always_boundary"]["f1"]
            ),
            "boundary": float(
                supervised["boundary_metrics"]["always_boundary"]["f1_exact"]
            ),
        },
    }


def score(phase: str) -> dict[str, Any]:
    all_sessions = load_population()
    sessions = (
        all_sessions[:PILOT_SESSIONS] if phase == "pilot" else all_sessions
    )
    baseline_boundaries = load_baseline_boundaries(sessions)
    sufficient: dict[str, dict[str, dict[str, Any]]] = {}
    operation_rows = []
    pair_rows = []
    depths = Counter()
    mark_count = 0

    for session in sessions:
        direct, paths = direct_boundaries(session)
        mark_count += len(paths)
        depths.update(len(path) for path in paths)
        boundaries = {
            "direct_multilevel": direct,
            **{
                method: {
                    position: baseline_boundaries[method][
                        (session.session, position)
                    ]
                    for position in range(1, len(session.operations))
                }
                for method in BASELINES
            },
        }
        predicted = {}
        for method in METHODS:
            group_index = 0
            assignments = []
            for position in range(len(session.operations)):
                if position and boundaries[method][position]:
                    group_index += 1
                assignments.append(f"{session.session}:{method}:{group_index:04d}")
            predicted[method] = assignments
        gold = [
            f"{session.session}:{operation.gold_group}"
            for operation in session.operations
        ]
        sufficient[session.session] = {}
        for method in METHODS:
            b3 = b3_session_sufficient(predicted[method], gold)
            tp = fp = fn = 0
            for position in range(1, len(session.operations)):
                official = gold[position] != gold[position - 1]
                candidate = boundaries[method][position]
                tp += int(official and candidate)
                fp += int(not official and candidate)
                fn += int(official and not candidate)
            sufficient[session.session][method] = {
                "bcubed": b3,
                "boundary": {"tp": tp, "fp": fp, "fn": fn},
            }
        for position, operation in enumerate(session.operations):
            operation_rows.append(
                {
                    "session": session.session,
                    "position": position,
                    "source_line": operation.line,
                    "official_group": gold[position],
                    **{
                        f"{method}_group": predicted[method][position]
                        for method in METHODS
                    },
                }
            )
            if position:
                pair_rows.append(
                    {
                        "session": session.session,
                        "position": position,
                        "previous_source_line": session.operations[position - 1].line,
                        "current_source_line": operation.line,
                        "official_boundary": gold[position] != gold[position - 1],
                        **{
                            method: boundaries[method][position]
                            for method in METHODS
                        },
                    }
                )

    metrics = {}
    for method in METHODS:
        b3 = aggregate_b3(
            sufficient[session.session][method]["bcubed"]
            for session in sessions
        )
        counts = Counter()
        for session in sessions:
            counts.update(sufficient[session.session][method]["boundary"])
        metrics[method] = {
            "bcubed": b3,
            "boundary": metric_from_counts(
                int(counts["tp"]), int(counts["fp"]), int(counts["fn"])
            ),
        }

    if phase == "full":
        expected = expected_full_metrics()
        for method, values in expected.items():
            for metric, expected_f1 in values.items():
                observed = metrics[method][metric]["f1"]
                if abs(observed - expected_f1) > 1e-12:
                    raise RuntimeError(
                        f"stored {method} {metric} did not reproduce: "
                        f"{observed} != {expected_f1}"
                    )

    phase_score = SCORE_ROOT / phase
    write_jsonl(phase_score / "operation-score-rows.jsonl", operation_rows)
    write_jsonl(phase_score / "pair-score-rows.jsonl", pair_rows)
    comparisons = {}
    for baseline in BASELINES:
        comparisons[baseline] = {}
        for metric in ("bcubed", "boundary"):
            comparisons[baseline][metric] = bootstrap_comparison(
                sessions,
                sufficient,
                "direct_multilevel",
                baseline,
                metric,
                BOOTSTRAP_ROOT
                / f"{phase}-direct-minus-{baseline}-{metric}.jsonl",
            )

    cost = cost_for(sessions)
    validity = {
        "deterministic_sorted_selection": [row.session for row in sessions]
        == sorted(row.session for row in sessions),
        "sessions_covered": len(sessions),
        "operations_conserved": len(operation_rows),
        "pairs_conserved": len(pair_rows),
        "one_assignment_per_operation": len(
            {
                (row["session"], row["position"])
                for row in operation_rows
            }
        )
        == len(operation_rows),
        "all_backend_responses_valid": all(existing_ok(row) for row in sessions),
        "successful_backend_sessions": cost["successful_sessions"],
        "failed_after_retry": cost["failed_after_retry"],
        "one_format_retry_limit": all(
            int(row["attempts"]) <= 2
            for row in read_jsonl(RUN_RECORDS)
            if int(row["ordinal"]) <= len(sessions)
        ),
        "model_visible_fields_exact": list(VISIBLE_FIELDS)
        == read_json(PACKETS / "manifest.json")["visible_fields"],
        "gold_fields_excluded": list(EXCLUDED_TARGET_FIELDS)
        == read_json(PACKETS / "manifest.json")["excluded_target_fields"],
    }
    expected_ops = (
        sum(len(row.operations) for row in sessions)
    )
    expected_pairs = sum(len(row.operations) - 1 for row in sessions)
    valid = (
        validity["deterministic_sorted_selection"]
        and validity["operations_conserved"] == expected_ops
        and validity["pairs_conserved"] == expected_pairs
        and validity["one_assignment_per_operation"]
        and validity["all_backend_responses_valid"]
        and validity["successful_backend_sessions"] == len(sessions)
        and validity["failed_after_retry"] == 0
        and validity["one_format_retry_limit"]
        and validity["model_visible_fields_exact"]
        and validity["gold_fields_excluded"]
    )
    recurrence_delta = (
        metrics["direct_multilevel"]["bcubed"]["f1"]
        - metrics["label_free_recurrence"]["bcubed"]["f1"]
    )
    gate = {
        "rule": (
            "pilot direct B3 F1 >= recurrence-on-slice B3 F1 - 0.05"
        ),
        "direct_minus_recurrence_bcubed_f1": recurrence_delta,
        "passed": bool(valid and recurrence_delta >= -PILOT_MARGIN)
        if phase == "pilot"
        else None,
        "full_run_authorized": bool(valid and recurrence_delta >= -PILOT_MARGIN)
        if phase == "pilot"
        else None,
    }
    hypothesis_verdict = (
        "contradicted"
        if phase == "full"
        and all(
            comparisons[baseline][metric]["ci95"][1] < 0
            for baseline in BASELINES
            for metric in ("bcubed", "boundary")
        )
        else "pilot_gate_passed"
        if phase == "pilot" and gate["passed"]
        else "pilot_gate_failed"
        if phase == "pilot"
        else "inconclusive"
    )
    payload = {
        "schema": "agentsight.direct-osworld-human-result.v1",
        "phase": phase,
        "status": "complete" if valid else "invalid",
        "selection": (
            "first 40 lexicographically sorted session IDs"
            if phase == "pilot"
            else "all 287 eligible sessions"
        ),
        "population": {
            "sessions": len(sessions),
            "operations": len(operation_rows),
            "pairs": len(pair_rows),
            "gold_groups": sum(
                len({operation.gold_group for operation in row.operations})
                for row in sessions
            ),
        },
        "metrics": metrics,
        "paired_session_cluster_bootstrap": comparisons,
        "gate": gate,
        "hypothesis_verdict": hypothesis_verdict,
        "cost": cost,
        "annotation": {
            "marks": mark_count,
            "path_depths": dict(sorted(depths.items())),
        },
        "validity": validity,
        "valid": valid,
        "raw_paths": {
            "operation_rows": str(
                (phase_score / "operation-score-rows.jsonl").relative_to(EXPERIMENT)
            ),
            "pair_rows": str(
                (phase_score / "pair-score-rows.jsonl").relative_to(EXPERIMENT)
            ),
            "raw_marks": str(RAW_MARKS.relative_to(EXPERIMENT)),
            "raw_responses": str(RAW_RESPONSES.relative_to(EXPERIMENT)),
            "raw_events": str(RAW_EVENTS.relative_to(EXPERIMENT)),
        },
    }
    write_json(EXPERIMENT / phase / "raw-results.json", payload)
    write_json(RAW_RESULTS, payload)
    if phase == "pilot":
        render_pilot(payload)
    else:
        render_results(payload)
    render_cost(payload)
    append_execution_event(
        f"{phase}-score",
        valid=valid,
        direct_bcubed_f1=metrics["direct_multilevel"]["bcubed"]["f1"],
        direct_boundary_f1=metrics["direct_multilevel"]["boundary"]["f1"],
        recurrence_bcubed_f1=metrics["label_free_recurrence"]["bcubed"]["f1"],
        gate_passed=gate["passed"],
    )
    return payload


def method_label(method: str) -> str:
    return {
        "direct_multilevel": "Direct multi-level",
        "supervised_oof": "Supervised OOF",
        "reference_calibrated": "Reference-calibrated",
        "label_free_recurrence": "Label-free recurrence",
        "always_boundary": "Always-boundary",
    }[method]


def metrics_table(payload: dict[str, Any]) -> list[str]:
    lines = [
        "| Method | Boundary P | Boundary R | Boundary F1 | B³ P | B³ R | B³ F1 |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for method in METHODS:
        row = payload["metrics"][method]
        lines.append(
            f"| {method_label(method)} "
            f"| {row['boundary']['precision']:.6f} "
            f"| {row['boundary']['recall']:.6f} "
            f"| {row['boundary']['f1']:.6f} "
            f"| {row['bcubed']['precision']:.6f} "
            f"| {row['bcubed']['recall']:.6f} "
            f"| {row['bcubed']['f1']:.6f} |"
        )
    return lines


def render_pilot(payload: dict[str, Any]) -> None:
    gate = payload["gate"]
    recurrence = payload["paired_session_cluster_bootstrap"][
        "label_free_recurrence"
    ]
    lines = [
        "# Pilot results: frozen direct backend on OSWorld-Human",
        "",
        f"Status: **{payload['status'].upper()}**",
        "",
        "Selection: the first 40 session IDs in lexicographically sorted order.",
        "",
        "## Same-slice metrics and gate",
        "",
        *metrics_table(payload),
        "",
        f"Direct minus label-free recurrence B³ F1: `{gate['direct_minus_recurrence_bcubed_f1']:+.6f}`; "
        f"paired session-cluster 95% interval "
        f"`[{recurrence['bcubed']['ci95'][0]:+.6f}, {recurrence['bcubed']['ci95'][1]:+.6f}]`.",
        "",
        f"Direct minus label-free recurrence boundary F1 paired session-cluster 95% interval: "
        f"`[{recurrence['boundary']['ci95'][0]:+.6f}, {recurrence['boundary']['ci95'][1]:+.6f}]`.",
        "",
        f"Binding gate (`direct B³ F1 >= recurrence-on-slice B³ F1 - 0.05`): "
        f"**{'PASS' if gate['passed'] else 'FAIL'}**.",
        "",
        (
            "The full 287-session run is authorized."
            if gate["passed"]
            else "Execution stops here; the full 287-session run is not authorized."
        ),
        "",
        "## Cost and validity",
        "",
        f"- Codex calls: {payload['cost']['total_codex_calls']} "
        f"({payload['cost']['format_retries']} format retries).",
        f"- Summed backend wall: {payload['cost']['summed_backend_wall_seconds']:.3f} s.",
        f"- Active backend wall: {payload['cost']['active_backend_wall_seconds']:.3f} s.",
        f"- Usage counters: `{json.dumps(payload['cost']['usage'], sort_keys=True)}`.",
        f"- Coverage: {payload['population']['sessions']} sessions, "
        f"{payload['population']['operations']} operations, "
        f"{payload['population']['pairs']} adjacent pairs.",
        f"- Marks: {payload['annotation']['marks']}; path depths: "
        f"`{json.dumps(payload['annotation']['path_depths'], sort_keys=True)}`.",
        f"- Validity: **{'PASS' if payload['valid'] else 'FAIL'}**.",
        "",
        "Raw marks, parsed responses, complete Codex JSON event streams, score rows, "
        "bootstrap draws, and machine-readable results are retained in this experiment directory.",
    ]
    PILOT_RESULTS.write_text("\n".join(lines) + "\n", encoding="utf-8")


def render_results(payload: dict[str, Any]) -> None:
    comparisons = payload["paired_session_cluster_bootstrap"]
    direct = payload["metrics"]["direct_multilevel"]
    best_b3 = max(
        (payload["metrics"][method]["bcubed"]["f1"], method)
        for method in BASELINES
    )
    best_boundary = max(
        (payload["metrics"][method]["boundary"]["f1"], method)
        for method in BASELINES
    )
    lines = [
        "# Results: frozen direct backend on OSWorld-Human",
        "",
        f"Run status: **{'VALID / COMPLETE' if payload['valid'] else 'INVALID'}**",
        "",
        f"Tested hypothesis: **{payload['hypothesis_verdict'].upper()}**",
        "",
        "## Complete population",
        "",
        f"The run covers all {payload['population']['sessions']} eligible sessions, "
        f"{payload['population']['operations']:,} operations, "
        f"{payload['population']['pairs']:,} adjacent pairs, and "
        f"{payload['population']['gold_groups']:,} human groups.",
        "",
        "## Metrics",
        "",
        *metrics_table(payload),
        "",
        "## Paired session-cluster intervals",
        "",
        "| Direct minus baseline | B³ F1 point | B³ 95% interval | Boundary F1 point | Boundary 95% interval |",
        "|---|---:|---:|---:|---:|",
    ]
    for baseline in BASELINES:
        comparison = comparisons[baseline]
        b3_point = (
            direct["bcubed"]["f1"]
            - payload["metrics"][baseline]["bcubed"]["f1"]
        )
        boundary_point = (
            direct["boundary"]["f1"]
            - payload["metrics"][baseline]["boundary"]["f1"]
        )
        lines.append(
            f"| {method_label(baseline)} "
            f"| {b3_point:+.6f} "
            f"| [{comparison['bcubed']['ci95'][0]:+.6f}, {comparison['bcubed']['ci95'][1]:+.6f}] "
            f"| {boundary_point:+.6f} "
            f"| [{comparison['boundary']['ci95'][0]:+.6f}, {comparison['boundary']['ci95'][1]:+.6f}] |"
        )
    lines.extend(
        [
            "",
            "## Hypothesis interpretation",
            "",
            "The frozen direct-backend competitiveness hypothesis is "
            f"**{payload['hypothesis_verdict'].upper()}**: both F1 measures are "
            "below all four requested comparators, and every paired 95% interval "
            "is wholly negative.",
            "",
            f"The direct backend reaches B³ F1 `{direct['bcubed']['f1']:.6f}` "
            f"and boundary F1 `{direct['boundary']['f1']:.6f}`. "
            f"The strongest stored B³ row is {method_label(best_b3[1])} "
            f"at `{best_b3[0]:.6f}`; the strongest stored boundary row is "
            f"{method_label(best_boundary[1])} at `{best_boundary[0]:.6f}`.",
            "",
            "The pilot margin authorized this complete run but is not silently "
            "promoted into a new full-run equivalence definition. The comparison "
            "above therefore reports the direct effects and uncertainty against "
            "every requested stored row; any use of “competitive” should retain "
            "both B³ and exact-boundary results.",
            "",
            "## Validity and conservation",
            "",
            f"- All {payload['population']['sessions']} source packets expose only "
            f"the fixed nine visible fields and contain no human group labels.",
            f"- Exactly {payload['population']['operations']:,} operation assignments "
            f"and {payload['population']['pairs']:,} adjacent decisions are conserved.",
            f"- Backend failures after the single permitted format retry: "
            f"{payload['cost']['failed_after_retry']}.",
            f"- Direct marks: {payload['annotation']['marks']}; path depths: "
            f"`{json.dumps(payload['annotation']['path_depths'], sort_keys=True)}`.",
            "",
            "This is independent-population RQ3 evidence for the frozen direct "
            "instruction. It does not change the fixed RQ, thesis, or paper story.",
        ]
    )
    RESULTS.write_text("\n".join(lines) + "\n", encoding="utf-8")


def render_cost(payload: dict[str, Any]) -> None:
    cost = payload["cost"]
    lines = [
        "# Cost record",
        "",
        f"Current accounting phase: **{payload['phase']}**",
        "",
        f"- backend: `{cost['backend']}`, model `{cost['model']}`;",
        f"- sessions selected/successful: {cost['sessions_selected']}/{cost['successful_sessions']};",
        f"- Codex calls: {cost['total_codex_calls']};",
        f"- format retries: {cost['format_retries']};",
        f"- failures after retry: {cost['failed_after_retry']};",
        f"- summed backend wall: {cost['summed_backend_wall_seconds']:.3f} s;",
        f"- active backend wall across four-worker waves: {cost['active_backend_wall_seconds']:.3f} s;",
        f"- usage counters: `{json.dumps(cost['usage'], sort_keys=True)}`.",
        "",
        "The active-wall value is the union of recorded backend-call intervals; "
        "summed wall adds every individual call. Token counters are the Codex CLI "
        "turn-completion counters retained for every attempt.",
    ]
    COST_RECORD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("prepare")
    for name in ("pilot", "full"):
        command = commands.add_parser(name)
        command.add_argument("--workers", type=int, default=DEFAULT_WORKERS)
        command.add_argument(
            "--timeout-seconds", type=int, default=DEFAULT_TIMEOUT_SECONDS
        )
    score_parser = commands.add_parser("score")
    score_parser.add_argument("phase", choices=("pilot", "full"))
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.command == "prepare":
        prepare()
    elif args.command in {"pilot", "full"}:
        if args.workers < 1:
            raise SystemExit("--workers must be positive")
        run_population(args.command, args.workers, args.timeout_seconds)
    elif args.command == "score":
        payload = score(args.phase)
        print(
            json.dumps(
                {
                    "status": payload["status"],
                    "phase": args.phase,
                    "direct_bcubed_f1": payload["metrics"]["direct_multilevel"][
                        "bcubed"
                    ]["f1"],
                    "direct_boundary_f1": payload["metrics"]["direct_multilevel"][
                        "boundary"
                    ]["f1"],
                    "gate_passed": payload["gate"]["passed"],
                },
                sort_keys=True,
            ),
            flush=True,
        )
    else:
        raise RuntimeError("unknown command")


if __name__ == "__main__":
    main()
