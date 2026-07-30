#!/usr/bin/env python3
"""Run matched FULL and skeleton-first SPLIT semantic annotation cells."""

from __future__ import annotations

import argparse
import concurrent.futures
from collections import defaultdict
import json
import math
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import threading
import time
from typing import Any


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[4]
STEP87 = (
    REPO
    / "docs/tmp/build-and-evaluate/step-0087-20260726T023000-0700"
    / "experiment-001/direct_annotation"
)
sys.path.insert(0, str(STEP87))
import annotate as direct  # noqa: E402


SOURCE_PACKETS = (
    REPO
    / ".agentsight/experiments/rq4-end-to-end-cost-v1/full/source-packets-rep-1"
)
OPERATION_USAGE = (
    REPO
    / ".agentsight/experiments/rq1-codetracebench-token-attribution-v1"
    / "full/operation-usage.jsonl"
)
FULL_SCHEMA = STEP87 / "response-schema.json"
ROUTER_SCHEMA = HERE / "router-schema.json"
REFINE_SCHEMA = HERE / "refine-schema.json"
SELECTION = HERE / "selection.json"
OUTPUT = HERE / "cells"
RUN_RECORDS = HERE / "run-records.jsonl"
MODEL = "gpt-5.6-sol"
LOCK = threading.Lock()


ROUTER_INSTRUCTION = direct.SYSTEM_INSTRUCTION + """

This is the first pass of a skeleton-first annotation. The SOURCE_PACKET omits
tool/command results but retains every turn's intent, planned action, and
progress. Produce complete coarse `marks` for the whole trajectory and choose
only the turns whose omitted `visible_result` is genuinely needed to decide a
semantic transition. Return their zero-based turn numbers in `detail_turns`.
The maximum allowed detail turns is stated in the packet. Spend this limited
evidence budget on uncertain transitions, errors, retries, and verification
results; do not select turns merely to restate an already clear action.
"""

SELECTIVE_INSTRUCTION = direct.SYSTEM_INSTRUCTION + """

This SOURCE_PACKET is a deterministic selective-evidence representation of the
complete trajectory. Every turn and operation is present. Every turn includes
intent, planned action, and progress, while `visible_result` is present only on
turns selected by a source-only mechanical importance rule. Directly produce
the complete sparse marks in one pass. Treat an omitted result as unavailable;
do not infer hidden text, and do not omit coverage for such a turn.
"""

REFINE_INSTRUCTION = """You are the selective refinement pass of an automatic
semantic annotation backend. Use only the SOURCE_PACKET in this request. Do
not invoke tools, inspect files, use the network, or run Git. Return only the
JSON object required by the response schema.

The packet contains validated coarse marks for the complete session and full
visible results only for turns selected by the first pass. Return sparse local
changes, not the complete annotation:
- `updates` may add or replace a mark only at an allowed start operation ID;
- `remove_start_operation_ids` may remove an existing coarse mark only at an
  allowed start operation ID;
- use an empty list when no local change is justified;
- preserve the identical session root in every updated path;
- tags remain lowercase, action-first, and 1--3 meaningful words;
- never mention framework, agent, model, session, score, outcome,
  success/failure label, or official stage in a tag.

Use the detailed results to fix only result-dependent local transitions.
"""


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )


def load_packets() -> list[dict[str, Any]]:
    packets = []
    for path in sorted(SOURCE_PACKETS.glob("batch-*.json")):
        packets.extend(read_json(path)["sessions"])
    packets.sort(key=lambda row: str(row["session"]))
    if len(packets) != 405:
        raise RuntimeError(f"expected 405 packets, got {len(packets)}")
    return packets


def task_names() -> dict[str, str]:
    result: dict[str, str] = {}
    with OPERATION_USAGE.open(encoding="utf-8") as stream:
        for line in stream:
            row = json.loads(line)
            result.setdefault(str(row["session"]), str(row["task_name"]))
    return result


def choose_quantiles(
    candidates: list[dict[str, Any]], count: int, used_tasks: set[str]
) -> list[dict[str, Any]]:
    available = [row for row in candidates if row["_task_name"] not in used_tasks]
    available.sort(key=lambda row: (int(row["turn_count"]), str(row["session"])))
    chosen = []
    for index in range(count):
        target = (index + 0.5) / count
        position = round(target * (len(available) - 1))
        order = sorted(
            range(len(available)),
            key=lambda pos: (abs(pos - position), pos),
        )
        match = next(
            available[pos]
            for pos in order
            if available[pos]["_task_name"] not in used_tasks
        )
        chosen.append(match)
        used_tasks.add(str(match["_task_name"]))
    return chosen


def prepare_selection() -> dict[str, Any]:
    packets = load_packets()
    names = task_names()
    enriched = [{**row, "_task_name": names[str(row["session"])]} for row in packets]
    median_turns = sorted(int(row["turn_count"]) for row in enriched)[len(enriched) // 2]
    preflight = min(
        enriched,
        key=lambda row: (
            abs(int(row["turn_count"]) - max(60, median_turns)),
            str(row["session"]),
        ),
    )
    used = {str(preflight["_task_name"])}
    by_framework: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in enriched:
        by_framework[str(row["framework"])].append(row)
    frameworks = ("OpenHands", "SWE-agent", "Terminus2", "mini-SWE-agent")
    pilot = []
    for framework in frameworks:
        pilot.extend(choose_quantiles(by_framework[framework], 3, used))
    confirmation = []
    for framework in frameworks:
        confirmation.extend(choose_quantiles(by_framework[framework], 8, used))

    def describe(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return [
            {
                "session": row["session"],
                "task_name": row["_task_name"],
                "framework": row["framework"],
                "turns": row["turn_count"],
                "operations": row["operation_count"],
            }
            for row in rows
        ]

    payload = {
        "selection_basis": (
            "packet framework/length and scorer-side task_name only; no stages, "
            "outcomes, scores, annotations, or model results"
        ),
        "preflight": describe([preflight]),
        "pilot": describe(pilot),
        "confirmation": describe(confirmation),
    }
    write_json(SELECTION, payload)
    return payload


def selected_packets(group: str) -> list[dict[str, Any]]:
    selection = read_json(SELECTION) if SELECTION.is_file() else prepare_selection()
    wanted = {row["session"] for row in selection[group]}
    return [row for row in load_packets() if row["session"] in wanted]


def skeleton(packet: dict[str, Any]) -> dict[str, Any]:
    return {
        "session": packet["session"],
        "framework": packet["framework"],
        "task": packet["task"],
        "turn_count": packet["turn_count"],
        "operation_count": packet["operation_count"],
        "turns": [
            {
                "turn": turn["turn"],
                "first_operation_id": turn["first_operation_id"],
                "intent": turn["intent"],
                "planned_action": turn["planned_action"],
                "progress": turn["progress"],
            }
            for turn in packet["turns"]
        ],
    }


def deterministic_detail_turns(packet: dict[str, Any]) -> list[int]:
    """Select high-information results without model calls or scorer fields."""

    turns = packet["turns"]
    budget = max(2, min(10, math.ceil(len(turns) * 0.15)))
    outcome_words = (
        "error",
        "fail",
        "exception",
        "traceback",
        "passed",
        "success",
        "warning",
        "timeout",
        "not found",
        "no such",
    )
    verification_words = (
        "test",
        "pytest",
        "cargo test",
        "npm test",
        "make",
        "build",
        "verify",
        "validate",
        "git diff",
        "git status",
    )
    ranked = []
    for index, turn in enumerate(turns):
        result = str(turn.get("visible_result") or "")
        action = str(turn.get("planned_action") or "").lower()
        progress = str(turn.get("progress") or "").strip().lower()
        previous_progress = (
            str(turns[index - 1].get("progress") or "").strip().lower()
            if index
            else ""
        )
        score = 0
        score += 5 * int(any(word in result.lower() for word in outcome_words))
        score += 3 * int(any(word in action for word in verification_words))
        score += 2 * int(progress not in {"", "none", "unknown"})
        score += int(index > 0 and progress != previous_progress)
        score += min(2, len(result) // 512)
        ranked.append((-score, -len(result), index))
    selected = sorted(index for _score, _length, index in sorted(ranked)[:budget])
    return selected


def selective_packet(
    packet: dict[str, Any], selected: list[int]
) -> dict[str, Any]:
    selected_set = set(selected)
    compact = skeleton(packet)
    compact["evidence_selection"] = {
        "selector": "source-only-important-result-v2",
        "selected_turns": selected,
        "selected_count": len(selected),
    }
    for index, turn in enumerate(compact["turns"]):
        if index in selected_set:
            turn["visible_result"] = packet["turns"][index]["visible_result"]
    return compact


def usage_total(usage: dict[str, Any] | None) -> int:
    usage = usage or {}
    return int(usage.get("input_tokens", 0) or 0) + int(
        usage.get("output_tokens", 0) or 0
    )


def run_codex(
    *,
    prompt: str,
    schema: Path,
    prefix: Path,
    attempt: int,
    timeout_seconds: int,
) -> dict[str, Any]:
    temporary = Path(tempfile.mkdtemp(prefix="split-annotation-"))
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
        str(schema),
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
            input=prompt,
            text=True,
            encoding="utf-8",
            capture_output=True,
            timeout=timeout_seconds,
            check=False,
        )
        response, usage, event_errors = direct.parse_codex_events(result.stdout)
        errors = list(event_errors)
        if result.returncode != 0:
            errors.append(f"codex exit status {result.returncode}")
        if usage is None:
            errors.append("missing Codex usage counters")
    except subprocess.TimeoutExpired as error:
        result = None
        response = None
        usage = None
        errors = [f"backend timeout after {timeout_seconds} seconds"]
        stdout = error.stdout if isinstance(error.stdout, str) else ""
        stderr = error.stderr if isinstance(error.stderr, str) else ""
    finally:
        shutil.rmtree(temporary, ignore_errors=True)
    elapsed = time.monotonic() - started
    if result is not None:
        stdout = result.stdout
        stderr = result.stderr
    prefix.parent.mkdir(parents=True, exist_ok=True)
    prefix.with_name(prefix.name + f"-attempt-{attempt}.jsonl").write_text(
        stdout, encoding="utf-8"
    )
    prefix.with_name(prefix.name + f"-attempt-{attempt}.stderr.txt").write_text(
        stderr, encoding="utf-8"
    )
    return {
        "attempt": attempt,
        "started_unix": started_wall,
        "wall_seconds": elapsed,
        "response": response,
        "usage": usage,
        "errors": errors,
    }


def with_retry(
    *,
    prompt: str,
    schema: Path,
    prefix: Path,
    timeout_seconds: int,
    validator: Any,
) -> tuple[Any, list[dict[str, Any]]]:
    attempts = []
    retry_errors: list[str] = []
    for attempt_number in (1, 2):
        retry = ""
        if retry_errors:
            retry = (
                "\nFORMAT RETRY. Correct these errors and return the complete "
                "required object:\n- "
                + "\n- ".join(retry_errors)
                + "\n"
            )
        attempt = run_codex(
            prompt=prompt + retry,
            schema=schema,
            prefix=prefix,
            attempt=attempt_number,
            timeout_seconds=timeout_seconds,
        )
        errors = list(attempt["errors"])
        if attempt["response"] is not None:
            errors.extend(validator(attempt["response"]))
        attempt["errors"] = errors
        attempts.append(attempt)
        if not errors:
            return attempt["response"], attempts
        retry_errors = errors
    return None, attempts


def validate_router(packet: dict[str, Any], response: Any) -> list[str]:
    if not isinstance(response, dict):
        return ["router response is not an object"]
    errors = direct.validate_response(
        packet, {"session": response.get("session"), "marks": response.get("marks")}
    )
    detail = response.get("detail_turns")
    limit = max(2, min(12, math.ceil(int(packet["turn_count"]) * 0.25)))
    if not isinstance(detail, list) or any(
        not isinstance(item, int) or item < 0 or item >= int(packet["turn_count"])
        for item in detail
    ):
        errors.append("detail_turns contains an invalid turn")
    elif len(detail) != len(set(detail)):
        errors.append("detail_turns is not unique")
    elif len(detail) > limit:
        errors.append(f"detail_turns exceeds maximum {limit}")
    return errors


def refinement_packet(
    packet: dict[str, Any], coarse: dict[str, Any]
) -> tuple[dict[str, Any], set[str]]:
    detail = sorted(int(index) for index in coarse["detail_turns"])
    allowed_indices = sorted(
        {
            index
            for selected in detail
            for index in (selected, selected + 1)
            if 0 <= index < int(packet["turn_count"])
        }
    )
    selected_set = set(detail)
    global_skeleton = []
    selected_full_turns = []
    for index, turn in enumerate(packet["turns"]):
        global_skeleton.append(
            {
                "turn": turn["turn"],
                "first_operation_id": turn["first_operation_id"],
                "planned_action": turn["planned_action"],
                "progress": turn["progress"],
            }
        )
        if index not in selected_set:
            continue
        turn = packet["turns"][index]
        selected_full_turns.append(dict(turn))
    allowed = {
        str(packet["turns"][index]["first_operation_id"]) for index in allowed_indices
    }
    return (
        {
            "session": packet["session"],
            "coarse_marks": coarse["marks"],
            "selected_detail_turns": detail,
            "allowed_start_operation_ids": sorted(allowed),
            "global_skeleton": global_skeleton,
            "selected_full_turns": selected_full_turns,
        },
        allowed,
    )


def validate_refinement(
    packet: dict[str, Any],
    coarse: dict[str, Any],
    allowed: set[str],
    response: Any,
) -> list[str]:
    if not isinstance(response, dict):
        return ["refinement response is not an object"]
    errors = []
    if response.get("session") != packet["session"]:
        errors.append("session does not exactly match")
    updates = response.get("updates")
    removals = response.get("remove_start_operation_ids")
    if not isinstance(updates, list) or not isinstance(removals, list):
        return [*errors, "updates/removals are not lists"]
    starts = []
    root = coarse["marks"][0]["semantic_path"][0]
    for update in updates:
        if not isinstance(update, dict):
            errors.append("update is not an object")
            continue
        start = str(update.get("start_operation_id"))
        starts.append(start)
        if start not in allowed:
            errors.append(f"update start {start} is outside selected windows")
        path = update.get("semantic_path")
        if not isinstance(path, list) or not path or path[0] != root:
            errors.append(f"update start {start} changes or omits the root")
        elif any(
            not isinstance(label, str) or not direct.LABEL_PATTERN.fullmatch(label)
            for label in path
        ):
            errors.append(f"update start {start} has an invalid tag")
    if len(starts) != len(set(starts)):
        errors.append("update starts are not unique")
    if any(str(start) not in allowed for start in removals):
        errors.append("removal is outside selected windows")
    if packet["turns"][0]["first_operation_id"] in removals:
        errors.append("cannot remove the mandatory first mark")
    return errors


def stitch(
    packet: dict[str, Any], coarse: dict[str, Any], refinement: dict[str, Any]
) -> dict[str, Any]:
    by_start = {
        str(mark["start_operation_id"]): dict(mark) for mark in coarse["marks"]
    }
    for start in refinement["remove_start_operation_ids"]:
        by_start.pop(str(start), None)
    for update in refinement["updates"]:
        by_start[str(update["start_operation_id"])] = update
    positions = {
        str(turn["first_operation_id"]): index for index, turn in enumerate(packet["turns"])
    }
    marks = sorted(by_start.values(), key=lambda mark: positions[mark["start_operation_id"]])
    compact = []
    for mark in marks:
        if compact and compact[-1]["semantic_path"] == mark["semantic_path"]:
            continue
        compact.append(mark)
    result = {"session": packet["session"], "marks": compact}
    errors = direct.validate_response(packet, result)
    if errors:
        raise RuntimeError("stitched response invalid: " + "; ".join(errors))
    return result


def run_full(packet: dict[str, Any], prefix: Path, timeout_seconds: int) -> tuple[Any, Any]:
    prompt = direct.prompt_for(packet, None)
    return with_retry(
        prompt=prompt,
        schema=FULL_SCHEMA,
        prefix=prefix,
        timeout_seconds=timeout_seconds,
        validator=lambda response: direct.validate_response(packet, response),
    )


def run_split(packet: dict[str, Any], prefix: Path, timeout_seconds: int) -> tuple[Any, Any]:
    selected = deterministic_detail_turns(packet)
    compact = selective_packet(packet, selected)
    prompt = (
        SELECTIVE_INSTRUCTION
        + "\nSOURCE_PACKET\n"
        + json.dumps(compact, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        + "\n"
    )
    response, attempts = with_retry(
        prompt=prompt,
        schema=FULL_SCHEMA,
        prefix=prefix.with_name(prefix.name + "-selective"),
        timeout_seconds=timeout_seconds,
        validator=lambda candidate: direct.validate_response(packet, candidate),
    )
    return response, {
        "annotation": attempts,
        "detail_turns": selected,
        "max_detail_turns": max(2, min(10, math.ceil(len(packet["turns"]) * 0.15))),
        "selector_version": "source-only-important-result-v2",
    }


def cell_path(group: str, condition: str, session: str) -> Path:
    return OUTPUT / group / condition / session / "marks.json"


def summarize_attempts(payload: Any) -> dict[str, Any]:
    phases = payload if isinstance(payload, dict) else {"full": payload}
    attempts = [
        attempt
        for value in phases.values()
        if isinstance(value, list)
        for attempt in value
        if isinstance(attempt, dict) and "wall_seconds" in attempt
    ]
    return {
        "calls": len(attempts),
        "provider_tokens": sum(usage_total(attempt.get("usage")) for attempt in attempts),
        "input_tokens": sum(
            int((attempt.get("usage") or {}).get("input_tokens", 0) or 0)
            for attempt in attempts
        ),
        "cached_input_tokens": sum(
            int((attempt.get("usage") or {}).get("cached_input_tokens", 0) or 0)
            for attempt in attempts
        ),
        "output_tokens": sum(
            int((attempt.get("usage") or {}).get("output_tokens", 0) or 0)
            for attempt in attempts
        ),
        "reasoning_output_tokens": sum(
            int((attempt.get("usage") or {}).get("reasoning_output_tokens", 0) or 0)
            for attempt in attempts
        ),
        "wall_seconds": sum(float(attempt["wall_seconds"]) for attempt in attempts),
        "attempts": [
            {
                key: attempt.get(key)
                for key in ("attempt", "started_unix", "wall_seconds", "usage", "errors")
            }
            for attempt in attempts
        ],
    }


def run_cell(
    packet: dict[str, Any], group: str, condition: str, timeout_seconds: int
) -> dict[str, Any]:
    session = str(packet["session"])
    output = cell_path(group, condition, session)
    if output.is_file():
        return {
            "group": group,
            "condition": condition,
            "session": session,
            "status": "already-complete",
        }
    directory = output.parent
    directory.mkdir(parents=True, exist_ok=True)
    prefix = directory / "events"
    if condition == "full":
        response, attempts = run_full(packet, prefix, timeout_seconds)
    else:
        response, attempts = run_split(packet, prefix, timeout_seconds)
    summary = summarize_attempts(attempts)
    record = {
        "group": group,
        "condition": condition,
        "session": session,
        "framework": packet["framework"],
        "turns": packet["turn_count"],
        "operations": packet["operation_count"],
        "status": "ok" if response is not None else "failed",
        **summary,
    }
    if isinstance(attempts, dict):
        record["detail_turns"] = attempts.get("detail_turns", [])
        record["max_detail_turns"] = attempts.get("max_detail_turns")
        write_json(directory / "split-detail.json", attempts)
    write_json(directory / "cell.json", record)
    if response is not None:
        write_json(output, response)
    with LOCK:
        with RUN_RECORDS.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
    return record


def run_group(group: str, workers: int, timeout_seconds: int) -> int:
    packets = selected_packets(group)
    jobs = []
    for index, packet in enumerate(packets):
        order = ("full", "split") if index % 2 == 0 else ("split", "full")
        jobs.extend((packet, condition) for condition in order)
    failures = 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {
            executor.submit(run_cell, packet, group, condition, timeout_seconds): (
                packet,
                condition,
            )
            for packet, condition in jobs
        }
        for future in concurrent.futures.as_completed(futures):
            packet, condition = futures[future]
            record = future.result()
            failures += int(record["status"] == "failed")
            print(
                json.dumps(
                    {
                        key: record.get(key)
                        for key in (
                            "group",
                            "condition",
                            "session",
                            "status",
                            "calls",
                            "provider_tokens",
                            "wall_seconds",
                            "detail_turns",
                        )
                    },
                    sort_keys=True,
                ),
                flush=True,
            )
    return failures


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "command", choices=("prepare", "preflight", "pilot", "confirmation")
    )
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--timeout-seconds", type=int, default=1200)
    args = parser.parse_args()
    if args.command == "prepare":
        print(json.dumps(prepare_selection(), indent=2, ensure_ascii=False))
        return 0
    if args.workers < 1:
        raise SystemExit("--workers must be positive")
    return 1 if run_group(args.command, args.workers, args.timeout_seconds) else 0


if __name__ == "__main__":
    raise SystemExit(main())
