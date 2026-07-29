#!/usr/bin/env python3
"""Run the Step 0087 Codex backend with only a flat-depth contract."""

from __future__ import annotations

import argparse
import difflib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
EXPERIMENT = SCRIPT_DIR.parent
REPO = EXPERIMENT.parents[4]
STEP_0087 = (
    REPO
    / "docs"
    / "tmp"
    / "build-and-evaluate"
    / "step-0087-20260726T023000-0700"
    / "experiment-001"
)
BASE_PATH = STEP_0087 / "direct_annotation" / "annotate.py"
CODEX = (
    Path("/home/yunwei37/.codex/packages/standalone/releases")
    / "0.145.0-x86_64-unknown-linux-musl"
    / "bin"
    / "codex"
)
FORMAT_REPAIRS = EXPERIMENT / "format-repairs.jsonl"


def load_module(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load module: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


base = load_module("step0087_direct_annotate", BASE_PATH)

# Retarget the frozen Step 0087 runner to this experiment. The packets, model,
# schema, request budget, isolation, timeout, worker pattern, and ordinary
# format-retry logic remain in the frozen implementation.
base.EXPERIMENT = EXPERIMENT
base.REPO = REPO
base.SOURCE_PACKETS = (
    REPO
    / ".agentsight"
    / "experiments"
    / "rq4-end-to-end-cost-v1"
    / "full"
    / "source-packets-rep-1"
)
base.SOURCE_MANIFEST = base.SOURCE_PACKETS / "manifest.json"
base.SCHEMA = STEP_0087 / "direct_annotation" / "response-schema.json"
base.INDEX = EXPERIMENT / "packet-index.json"
base.RAW_MARKS = EXPERIMENT / "raw-marks"
base.RAW_EVENTS = EXPERIMENT / "raw-events"
base.RUN_RECORDS = EXPERIMENT / "annotation-run-records.jsonl"
base.RAW_ANNOTATIONS = EXPERIMENT / "raw-annotations"
base.PREFLIGHT = EXPERIMENT / "preflight"
base.PILOT = EXPERIMENT / "unused-pilot"
HIERARCHY_SYSTEM_INSTRUCTION = base.SYSTEM_INSTRUCTION


FLAT_SYSTEM_INSTRUCTION = """You are the automatic semantic annotation backend.
Use only the SOURCE_PACKET in this request. Do not invoke tools, execute shell
commands, inspect files, inspect a repository, use the network, or run Git.
Return only the JSON object required by the response schema.

Read the complete already-finished trajectory and directly write sparse flat
semantic transition marks in one pass. Do not use a STOP/SPLIT protocol, do not
recursively ask yourself binary questions, and do not first generate a
hierarchy and project it to a flat partition afterward.

The output is the A2 sparse complete-path mark format:
- `session` must exactly equal the packet's `session`.
- `marks` are ordered by the packet's turn order.
- every `start_operation_id` must equal a turn's `first_operation_id`;
- the first mark must start at the first turn;
- omit a mark when the complete semantic path is unchanged;
- each mark's `semantic_path` is the complete active path for that span;
- every path contains exactly two labels: the mandatory session root followed
  by exactly one non-root flat semantic interval name;
- the first root label is identical in every mark in this trajectory;
- adjacent spans may change only the single non-root flat semantic name;
- every tag is lowercase, action-first, and contains 1--3 meaningful words;
- the allowed action-first verbs are fixed by the response schema.

Read the complete trajectory and choose contiguous boundaries directly for
persistent changes in what responsibility the agent is trying to accomplish.
Do not create a boundary merely because a command, file, tool, observation,
status, or retry changes. Do not force every turn to become a mark. The
non-root name must directly express the flat task, subtask, strategy, phase, or
semantic-action responsibility for that interval. Prefer stable reusable
wording when the same responsibility recurs. Never mention framework, agent,
model, session, score, outcome, success/failure label, or official stage in a
tag.
"""
base.SYSTEM_INSTRUCTION = FLAT_SYSTEM_INSTRUCTION
BASE_VALIDATE = base.validate_response
BASE_RUN_ATTEMPT = base.run_attempt


def validate_response(packet: dict[str, Any], response: Any) -> list[str]:
    errors = list(BASE_VALIDATE(packet, response))
    if not isinstance(response, dict):
        return errors
    marks = response.get("marks")
    if not isinstance(marks, list):
        return errors
    for index, mark in enumerate(marks):
        if not isinstance(mark, dict):
            continue
        path = mark.get("semantic_path")
        if isinstance(path, list) and len(path) != 2:
            errors.append(
                f"mark {index} must contain exactly root plus one flat name"
            )
    return errors


base.validate_response = validate_response


def run_attempt(
    row: Any,
    attempt: int,
    retry_errors: list[str] | None,
    timeout_seconds: int,
    *,
    exact_session_copy: bool = False,
) -> dict[str, Any]:
    result = BASE_RUN_ATTEMPT(
        row,
        attempt,
        retry_errors,
        timeout_seconds,
        exact_session_copy=exact_session_copy,
    )
    if (
        attempt == 2
        and result.get("errors") == ["session does not exactly match the packet"]
        and isinstance(result.get("response"), dict)
    ):
        normalized = dict(result["response"])
        original_session = normalized.get("session")
        normalized["session"] = row.packet["session"]
        if not validate_response(row.packet, normalized):
            with base.RECORD_LOCK:
                with FORMAT_REPAIRS.open("a", encoding="utf-8") as stream:
                    stream.write(
                        json.dumps(
                            {
                                "ordinal": row.ordinal,
                                "attempt": attempt,
                                "repair": "exact-session-id-replacement",
                                "original_session": original_session,
                                "replacement_session": row.packet["session"],
                                "semantic_marks_unchanged": True,
                            },
                            ensure_ascii=False,
                            sort_keys=True,
                        )
                        + "\n"
                    )
            result["response"] = normalized
            result["errors"] = []
    return result


base.run_attempt = run_attempt


def expanded_paths(
    packet: dict[str, Any], marks: list[dict[str, Any]]
) -> dict[str, tuple[str, ...]]:
    path_by_start = {
        str(mark["start_operation_id"]): tuple(
            str(label) for label in mark["semantic_path"]
        )
        for mark in marks
    }
    current: tuple[str, ...] | None = None
    expanded: dict[str, tuple[str, ...]] = {}
    for turn in packet["turns"]:
        for operation_id in turn["operation_ids"]:
            operation_id = str(operation_id)
            if operation_id in path_by_start:
                current = path_by_start[operation_id]
            if current is None:
                raise RuntimeError("marks do not cover the first operation")
            expanded[operation_id] = current
    return expanded


def repair_redundant_marks(ordinal: int) -> None:
    row = next((row for row in base.load_packets() if row.ordinal == ordinal), None)
    if row is None:
        raise RuntimeError(f"unknown ordinal: {ordinal}")
    records = [
        json.loads(line)
        for line in base.RUN_RECORDS.read_text(encoding="utf-8").splitlines()
        if line.strip() and int(json.loads(line)["ordinal"]) == ordinal
    ]
    if not records or records[-1].get("status") != "failed":
        raise RuntimeError(f"ordinal {ordinal} is not a terminal failed response")
    attempt = int(records[-1]["attempts"])
    event_path = base.RAW_EVENTS / f"{ordinal:04d}-attempt-{attempt}.jsonl"
    response, _, event_errors = base.parse_codex_events(
        event_path.read_text(encoding="utf-8")
    )
    if event_errors or not isinstance(response, dict):
        raise RuntimeError(f"cannot parse terminal response: {event_errors}")
    before_errors = validate_response(row.packet, response)
    if before_errors != ["adjacent marks repeat an unchanged complete path"]:
        raise RuntimeError(f"unexpected terminal errors: {before_errors}")

    normalized = dict(response)
    normalized_marks: list[dict[str, Any]] = []
    removed_starts: list[str] = []
    previous_path: tuple[str, ...] | None = None
    for mark in response["marks"]:
        path = tuple(str(label) for label in mark["semantic_path"])
        if path == previous_path:
            removed_starts.append(str(mark["start_operation_id"]))
            continue
        normalized_marks.append(mark)
        previous_path = path
    normalized["marks"] = normalized_marks
    if not removed_starts:
        raise RuntimeError("no redundant transition marks found")
    if validate_response(row.packet, normalized):
        raise RuntimeError("mechanically normalized response remains invalid")
    if expanded_paths(row.packet, response["marks"]) != expanded_paths(
        row.packet, normalized_marks
    ):
        raise RuntimeError("mechanical normalization changed an operation path")

    base.write_json(row.raw_path, normalized)
    repair = {
        "ordinal": ordinal,
        "attempt": attempt,
        "repair": "delete-redundant-unchanged-transition-marks",
        "removed_start_operation_ids": removed_starts,
        "original_mark_count": len(response["marks"]),
        "normalized_mark_count": len(normalized_marks),
        "per_operation_paths_unchanged": True,
        "removed_noop_mark_boundaries": len(removed_starts),
        "official_stages_or_scores_opened": False,
    }
    with FORMAT_REPAIRS.open("a", encoding="utf-8") as stream:
        stream.write(
            json.dumps(repair, ensure_ascii=False, sort_keys=True) + "\n"
        )
    repaired_record = dict(records[-1])
    repaired_record["status"] = "ok"
    repaired_record["mechanical_repair"] = repair
    with base.RUN_RECORDS.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(repaired_record, sort_keys=True) + "\n")
    print(json.dumps(repair, sort_keys=True), flush=True)


def prepare() -> None:
    rows = base.load_packets()
    version = subprocess.run(
        [str(CODEX), "--version"],
        text=True,
        encoding="utf-8",
        capture_output=True,
        check=True,
    ).stdout.strip()
    base.write_json(
        base.INDEX,
        {
            "schema": "agentsight.same-model-flat-annotation.packet-index.v1",
            "source": str(base.SOURCE_PACKETS.relative_to(REPO)),
            "codex_binary": str(CODEX),
            "codex_version": version,
            "model": base.MODEL,
            "sessions": base.EXPECTED_SESSIONS,
            "turns": base.EXPECTED_TURNS,
            "operations": base.EXPECTED_OPERATIONS,
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
    (EXPERIMENT / "prompt-contract.diff").write_text(
        "".join(
            difflib.unified_diff(
                HIERARCHY_SYSTEM_INSTRUCTION.splitlines(keepends=True),
                FLAT_SYSTEM_INSTRUCTION.splitlines(keepends=True),
                fromfile="step-0087-direct-hierarchy-instruction",
                tofile="step-0092-same-model-flat-instruction",
            )
        ),
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "status": "ok",
                "codex_version": version,
                "sessions": len(rows),
                "turns": base.EXPECTED_TURNS,
                "operations": base.EXPECTED_OPERATIONS,
            },
            sort_keys=True,
        ),
        flush=True,
    )


def main() -> None:
    if not CODEX.is_file():
        raise SystemExit(f"missing pinned Codex binary: {CODEX}")
    os.environ["PATH"] = str(CODEX.parent) + os.pathsep + os.environ.get("PATH", "")

    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("prepare")
    repair = commands.add_parser("repair-redundant")
    repair.add_argument("--ordinal", type=int, required=True)
    preflight = commands.add_parser("preflight")
    preflight.add_argument(
        "--timeout-seconds", type=int, default=base.DEFAULT_TIMEOUT_SECONDS
    )
    full = commands.add_parser("full")
    full.add_argument("--workers", type=int, default=base.DEFAULT_WORKERS)
    full.add_argument(
        "--timeout-seconds", type=int, default=base.DEFAULT_TIMEOUT_SECONDS
    )
    package = commands.add_parser("package")
    package.add_argument("--preflight", action="store_true")
    args = parser.parse_args()

    rows = base.load_packets()
    if args.command == "prepare":
        prepare()
    elif args.command == "repair-redundant":
        repair_redundant_marks(args.ordinal)
    elif args.command == "preflight":
        selected = [
            min(rows, key=lambda row: (int(row.packet["turn_count"]), row.session))
        ]
        base.run_population(selected, 1, args.timeout_seconds)
        base.package_annotations(mode="preflight")
    elif args.command == "full":
        if args.workers < 1:
            raise SystemExit("--workers must be positive")
        started_unix = time.time()
        started = time.monotonic()
        base.run_population(rows, args.workers, args.timeout_seconds)
        base.write_json(
            EXPERIMENT / "full-backend-timing.json",
            {
                "started_unix": started_unix,
                "finished_unix": time.time(),
                "command_wall_seconds": time.monotonic() - started,
                "workers": args.workers,
                "timeout_seconds": args.timeout_seconds,
            },
        )
    else:
        base.package_annotations(mode="preflight" if args.preflight else "full")


if __name__ == "__main__":
    main()
