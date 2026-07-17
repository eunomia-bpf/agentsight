#!/usr/bin/env python3
"""Evaluate RQ1 stage and token-mass attribution on released trajectories.

This scorer reuses the fixed Step 0024 operation assignments.  It never changes
the recurrence constructor and never exposes target stages or token usage to it.
"""

from __future__ import annotations

import argparse
import ast
from collections import Counter, defaultdict
from dataclasses import dataclass
import json
import math
from pathlib import Path
import random
import re
import subprocess
import tarfile
from typing import Any, Callable, Iterable

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / ".agentsight/experiments/codetracebench-rq2/manifests/verified.parquet"
DEFAULT_HUB = ROOT / ".agentsight/experiments/codetracebench-rq2/hub"
DEFAULT_TARGETS = ROOT / "docs/visexp/out/codetracebench-rq2/full/target-operations.jsonl"
DEFAULT_ASSIGNMENTS = ROOT / ".agentsight/experiments/rq3-monotone-recurrence-codetracebench-v1/full/operation-assignments.jsonl"
DEFAULT_STEP0024_SUMMARY = ROOT / ".agentsight/experiments/rq3-monotone-recurrence-codetracebench-v1/full/summary.json"
DEFAULT_OUTPUT_ROOT = ROOT / ".agentsight/experiments/rq1-codetracebench-token-attribution-v1"

METHODS = (
    "recurrence",
    "raw_action_key_change",
    "action_change",
    "phase_change",
    "session_one_block",
    "always_boundary",
)
METHOD_LABELS = {"action_change": "action_kind_change"}
EXISTING_METHODS = tuple(method for method in METHODS if method != "raw_action_key_change")
USAGE_FIELDS = ("prompt_tokens", "completion_tokens", "total_tokens")


class EvaluationError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise EvaluationError(message)


@dataclass(frozen=True)
class Usage:
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int

    def __add__(self, other: "Usage") -> "Usage":
        return Usage(
            self.prompt_tokens + other.prompt_tokens,
            self.completion_tokens + other.completion_tokens,
            self.total_tokens + other.total_tokens,
        )


@dataclass(frozen=True)
class UsageAssignment:
    response_id: str
    usage: Usage
    source: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("preflight", "full"), required=True)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--hub-root", type=Path, default=DEFAULT_HUB)
    parser.add_argument("--target-operations", type=Path, default=DEFAULT_TARGETS)
    parser.add_argument("--assignments", type=Path, default=DEFAULT_ASSIGNMENTS)
    parser.add_argument("--step0024-summary", type=Path, default=DEFAULT_STEP0024_SUMMARY)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--bootstrap-resamples", type=int, default=10_000)
    parser.add_argument("--bootstrap-seed", type=int, default=20_260_716)
    return parser.parse_args()


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as source:
        return [json.loads(line) for line in source if line.strip()]


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as output:
        json.dump(value, output, ensure_ascii=False, indent=2, sort_keys=True)
        output.write("\n")


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as output:
        for row in rows:
            output.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def source_form(agent: str, source_ref: str) -> str:
    if agent == "OpenHands":
        return "openhands-swe-raw" if source_ref.startswith("swe_raw/") else "openhands-native"
    if agent == "mini-SWE-agent":
        return "mini-swe-raw" if source_ref.startswith("swe_raw/") else "mini-native"
    if agent == "SWE-agent":
        return "swe-agent"
    if agent == "Terminus2":
        return "terminus2"
    raise EvaluationError(f"unsupported agent: {agent}")


def normalize_command(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    return text[:-1] if text.endswith("\n") else text


def split_source_ref(source_ref: str) -> tuple[str, str | None]:
    if "#" not in source_ref:
        return source_ref, None
    return tuple(source_ref.rsplit("#", 1))  # type: ignore[return-value]


def load_inputs(
    args: argparse.Namespace,
) -> tuple[list[dict[str, Any]], pd.DataFrame, dict[str, list[dict[str, Any]]], list[str]]:
    manifest = pd.read_parquet(args.manifest)
    require(manifest["traj_id"].is_unique, "manifest traj_id is not unique")
    manifest = manifest.set_index("traj_id", drop=False)

    targets: dict[str, list[dict[str, Any]]] = defaultdict(list)
    target_session_order: list[str] = []
    for record in load_jsonl(args.target_operations):
        fields = record["fields"]
        session = str(fields["traj_id"])
        if session not in targets:
            target_session_order.append(session)
        targets[session].append(
            {
                "session": session,
                "step_id": int(fields["step_id"]),
                "raw_action_key": str(fields["raw_action_key"]),
                "source_ref": str(fields["source_ref"]),
            }
        )
    for session, rows in targets.items():
        rows.sort(key=lambda row: row["step_id"])
        require(
            [row["step_id"] for row in rows] == list(range(1, len(rows) + 1)),
            f"non-contiguous target steps: {session}",
        )
        require(session in manifest.index, f"target absent from manifest: {session}")

    if args.mode == "full":
        selected = list(target_session_order)
    else:
        selected_by_form: dict[str, str] = {}
        for session in target_session_order:
            first = targets[session][0]
            agent = str(manifest.at[session, "agent"])
            selected_by_form.setdefault(source_form(agent, first["source_ref"]), session)
        required_forms = {
            "openhands-swe-raw",
            "openhands-native",
            "mini-swe-raw",
            "mini-native",
            "swe-agent",
            "terminus2",
        }
        require(set(selected_by_form) == required_forms, "preflight lacks a source form")
        selected = [selected_by_form[form] for form in sorted(required_forms)]

    assignments_by_key = {
        (str(row["session"]), int(row["step_id"])): row
        for row in load_jsonl(args.assignments)
    }
    rows: list[dict[str, Any]] = []
    for session in selected:
        manifest_row = manifest.loc[session]
        group_number = 0
        previous_raw: str | None = None
        for target in targets[session]:
            key = (session, int(target["step_id"]))
            require(key in assignments_by_key, f"missing Step 0024 assignment: {key}")
            existing = assignments_by_key[key]
            raw = str(target["raw_action_key"])
            require(bool(raw), f"empty raw_action_key: {key}")
            if previous_raw is not None and raw != previous_raw:
                group_number += 1
            previous_raw = raw
            row = dict(existing)
            official_stage = None
            stages = manifest_row["stages"]
            require(stages is not None, f"manifest stages missing: {session}")
            for stage in stages:
                if int(stage["start_step_id"]) <= key[1] <= int(stage["end_step_id"]):
                    official_stage = f"{session}:stage-{int(stage['stage_id']):04d}"
                    break
            require(official_stage is not None, f"manifest stage missing: {key}")
            require(existing["official_stage"] == official_stage, f"assignment/manifest stage mismatch: {key}")
            row.update(
                {
                    "task_name": str(manifest_row["task_name"]),
                    "raw_action_key": raw,
                    "raw_action_key_change": f"{session}:raw_action_key_change-{group_number:04d}",
                    "source_ref": target["source_ref"],
                    "source_form": source_form(str(manifest_row["agent"]), target["source_ref"]),
                }
            )
            rows.append(row)

    require(len({(row["session"], row["step_id"]) for row in rows}) == len(rows), "duplicate joined operation")
    if args.mode == "full":
        require(len(rows) == 20_866, "full operation population changed")
        require(len({row["official_stage"] for row in rows}) == 2_948, "official stage population changed")
        require(len({row["task_name"] for row in rows}) == 251, "target task population changed")
        require(len({row["raw_action_key_change"] for row in rows}) == 12_231, "raw-action-key group count changed")
    return rows, manifest, targets, selected


def archive_members(
    archive: Path, wanted: Callable[[str], bool]
) -> dict[str, bytes]:
    require(archive.is_file(), f"archive missing: {archive}")
    process = subprocess.Popen(
        ["zstd", "-q", "-d", "-c", str(archive)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    require(process.stdout is not None and process.stderr is not None, "cannot start zstd")
    result: dict[str, bytes] = {}
    try:
        with tarfile.open(fileobj=process.stdout, mode="r|") as tar:
            for member in tar:
                if not member.isfile() or not wanted(member.name):
                    continue
                extracted = tar.extractfile(member)
                require(extracted is not None, f"cannot read archive member: {member.name}")
                result[member.name] = extracted.read()
    except Exception:
        process.terminate()
        process.wait()
        raise
    finally:
        process.stdout.close()
    stderr = process.stderr.read().decode(errors="replace")
    return_code = process.wait()
    require(return_code == 0, f"zstd failed for {archive}: {stderr.strip()}")
    return result


def json_bytes(data: bytes, source: str) -> Any:
    try:
        return json.loads(data)
    except json.JSONDecodeError as error:
        raise EvaluationError(f"invalid JSON in {source}: {error}") from error


def usage_from_mapping(value: Any, source: str) -> Usage:
    require(isinstance(value, dict), f"missing usage mapping: {source}")
    prompt = value.get("prompt_tokens", value.get("input_tokens"))
    completion = value.get("completion_tokens", value.get("output_tokens"))
    total = value.get("total_tokens")
    require(prompt is not None and completion is not None, f"incomplete usage: {source}")
    prompt_i = int(prompt)
    completion_i = int(completion)
    total_i = int(total) if total is not None else prompt_i + completion_i
    require(prompt_i >= 0 and completion_i >= 0 and total_i > 0, f"nonpositive usage: {source}")
    require(total_i == prompt_i + completion_i, f"token total mismatch: {source}")
    return Usage(prompt_i, completion_i, total_i)


def register_assignment(
    result: dict[int, UsageAssignment], step_id: int, assignment: UsageAssignment
) -> None:
    require(step_id not in result, f"duplicate usage assignment for step {step_id}")
    result[step_id] = assignment


def extract_miniswe_usage(
    session: str, archive: Path, operations: list[dict[str, Any]]
) -> dict[int, UsageAssignment]:
    wanted_members = {split_source_ref(row["source_ref"])[0] for row in operations}
    members = archive_members(archive, wanted_members.__contains__)
    require(set(members) == wanted_members, f"{session}: missing mini trajectory member")
    decoded = {name: json_bytes(data, name) for name, data in members.items()}
    result: dict[int, UsageAssignment] = {}
    for row in operations:
        member, fragment = split_source_ref(row["source_ref"])
        match = re.fullmatch(r"message-(\d+)", fragment or "")
        require(match is not None, f"{session}: invalid mini source_ref {row['source_ref']}")
        message_index = int(match.group(1))
        data = decoded[member]
        messages = data.get("messages") if isinstance(data, dict) else None
        require(isinstance(messages, list) and message_index < len(messages), f"{session}: mini message missing")
        message = messages[message_index]
        response = message.get("extra", {}).get("response", {}) if isinstance(message, dict) else {}
        usage = usage_from_mapping(response.get("usage"), f"{member}#{fragment}")
        response_id = str(response.get("id") or f"{member}#{fragment}")
        register_assignment(
            result,
            int(row["step_id"]),
            UsageAssignment(f"{session}:mini:{response_id}", usage, f"{member}#{fragment}"),
        )
    return result


def is_openhands_action(event: Any) -> bool:
    return bool(
        isinstance(event, dict)
        and event.get("source") == "agent"
        and event.get("action")
        and event.get("action") not in {"system", "message"}
    )


def extract_openhands_native_usage(
    session: str, archive: Path, operations: list[dict[str, Any]]
) -> dict[int, UsageAssignment]:
    wanted_members = {split_source_ref(row["source_ref"])[0] for row in operations}
    members = archive_members(archive, wanted_members.__contains__)
    require(set(members) == wanted_members, f"{session}: missing OpenHands session member")
    candidates: dict[str, list[dict[str, Any]]] = {}
    for member, raw in members.items():
        data = json_bytes(raw, member)
        events = data if isinstance(data, list) else [data]
        candidates[member] = [event for event in events if is_openhands_action(event)]
    cursors: Counter[str] = Counter()
    result: dict[int, UsageAssignment] = {}
    for row in operations:
        member, fragment = split_source_ref(row["source_ref"])
        require(fragment is None, f"{session}: unexpected native OpenHands fragment")
        cursor = cursors[member]
        require(cursor < len(candidates[member]), f"{session}: OpenHands action underflow in {member}")
        event = candidates[member][cursor]
        cursors[member] += 1
        metadata = event.get("tool_call_metadata")
        require(isinstance(metadata, dict), f"{session}: action lacks tool_call_metadata")
        response = metadata.get("model_response")
        require(isinstance(response, dict), f"{session}: action lacks model_response")
        usage = usage_from_mapping(response.get("usage"), f"{member}:event-{event.get('id')}")
        response_id = str(response.get("id") or metadata.get("tool_call_id") or event.get("id"))
        register_assignment(
            result,
            int(row["step_id"]),
            UsageAssignment(f"{session}:openhands:{response_id}", usage, f"{member}:event-{event.get('id')}"),
        )
    for member, cursor in cursors.items():
        require(cursor == len(candidates[member]), f"{session}: unused OpenHands actions in {member}")
    return result


def response_tool_calls(response: Any) -> list[dict[str, Any]]:
    if not isinstance(response, dict):
        return []
    choices = response.get("choices")
    if not isinstance(choices, list) or not choices:
        return []
    message = choices[0].get("message") if isinstance(choices[0], dict) else None
    calls = message.get("tool_calls") if isinstance(message, dict) else None
    return [call for call in calls or [] if isinstance(call, dict)]


def extract_openhands_swe_usage(
    session: str, archive: Path, operations: list[dict[str, Any]], source_relpath: str
) -> dict[int, UsageAssignment]:
    prefix = source_relpath.rstrip("/") + "/"
    members = archive_members(archive, lambda name: name.startswith(prefix) and name.endswith(".json"))
    decoded = {name: json_bytes(data, name) for name, data in members.items()}
    by_tool_call: dict[str, UsageAssignment] = {}
    for member, record in decoded.items():
        if not isinstance(record, dict) or "response" not in record:
            continue
        response = record["response"]
        if isinstance(response, str):
            try:
                response = json.loads(response)
            except json.JSONDecodeError:
                continue
        calls = response_tool_calls(response)
        if not calls:
            continue
        usage = usage_from_mapping(response.get("usage"), f"{member}:response")
        response_id = str(response.get("id") or member)
        assignment = UsageAssignment(f"{session}:openhands-swe:{response_id}", usage, member)
        for call in calls:
            call_id = call.get("id")
            require(isinstance(call_id, str), f"{member}: tool call lacks id")
            previous = by_tool_call.setdefault(call_id, assignment)
            require(previous == assignment, f"{session}: conflicting tool call response {call_id}")

    result: dict[int, UsageAssignment] = {}
    for row in operations:
        member, fragment = split_source_ref(row["source_ref"])
        match = re.fullmatch(r"message-(\d+)-tool-(\d+)", fragment or "")
        require(match is not None and member in decoded, f"{session}: invalid OpenHands SWE source_ref")
        record = decoded[member]
        messages = record.get("messages") if isinstance(record, dict) else None
        message_index, tool_index = map(int, match.groups())
        require(isinstance(messages, list) and message_index < len(messages), f"{session}: selected request message missing")
        message = messages[message_index]
        calls = message.get("tool_calls") if isinstance(message, dict) else None
        require(isinstance(calls, list) and tool_index < len(calls), f"{session}: selected tool call missing")
        call_id = calls[tool_index].get("id") if isinstance(calls[tool_index], dict) else None
        require(isinstance(call_id, str) and call_id in by_tool_call, f"{session}: usage missing for tool call {call_id}")
        register_assignment(result, int(row["step_id"]), by_tool_call[call_id])
    return result


def parse_terminus_commands(text: str) -> list[str]:
    try:
        value = json.loads(text)
    except json.JSONDecodeError:
        value = None
    if isinstance(value, dict) and isinstance(value.get("commands"), list):
        commands = []
        for command in value["commands"]:
            if isinstance(command, dict) and isinstance(command.get("keystrokes"), str):
                commands.append(normalize_command(command["keystrokes"]))
            elif isinstance(command, str):
                commands.append(normalize_command(command))
        return commands

    commands = []
    decoder = json.JSONDecoder()
    for match in re.finditer(r'"keystrokes"\s*:\s*', text):
        try:
            value, _ = decoder.raw_decode(text, match.end())
        except json.JSONDecodeError:
            continue
        if isinstance(value, str):
            commands.append(normalize_command(value))
    return commands


def episode_number(member: str) -> int:
    match = re.search(r"/episode-(\d+)/", member)
    return int(match.group(1)) if match else -1


def extract_terminus_usage(
    session: str, archive: Path, operations: list[dict[str, Any]], source_relpath: str
) -> dict[int, UsageAssignment]:
    command_member = split_source_ref(operations[0]["source_ref"])[0]
    prefix = source_relpath.rstrip("/") + "/"
    members = archive_members(
        archive,
        lambda name: name == command_member
        or (
            name.startswith(prefix)
            and (name.endswith("/response.txt") or name.endswith("/debug.json"))
        ),
    )
    require(command_member in members, f"{session}: commands.txt missing")
    command_lines = members[command_member].decode(errors="replace").splitlines()
    official: list[tuple[int, str]] = []
    for row in operations:
        member, fragment = split_source_ref(row["source_ref"])
        match = re.fullmatch(r"line-(\d+)", fragment or "")
        require(member == command_member and match is not None, f"{session}: invalid Terminus source_ref")
        line_number = int(match.group(1))
        value = ast.literal_eval(command_lines[line_number - 1])
        require(isinstance(value, str), f"{session}: official command is not a string")
        official.append((int(row["step_id"]), normalize_command(value)))

    responses: dict[int, list[str]] = {}
    usages: dict[int, Usage] = {}
    sources: dict[int, str] = {}
    for member, raw in members.items():
        episode = episode_number(member)
        if episode < 0:
            continue
        if member.endswith("/response.txt"):
            responses[episode] = parse_terminus_commands(raw.decode(errors="replace"))
        elif member.endswith("/debug.json"):
            debug = json_bytes(raw, member)
            original = debug.get("original_response") if isinstance(debug, dict) else None
            if isinstance(original, str):
                try:
                    original = json.loads(original)
                except json.JSONDecodeError:
                    original = None
            if isinstance(original, dict) and isinstance(original.get("usage"), dict):
                usages[episode] = usage_from_mapping(original["usage"], member)
                sources[episode] = member

    response_stream: list[tuple[str, int]] = []
    for episode in sorted(responses):
        response_stream.extend((command, episode) for command in responses[episode])

    result: dict[int, UsageAssignment] = {}
    cursor = 0
    skipped = 0
    for step_id, command in official:
        while cursor < len(response_stream) and response_stream[cursor][0] != command:
            cursor += 1
            skipped += 1
        require(cursor < len(response_stream), f"{session}: official command absent from response stream at step {step_id}")
        _, episode = response_stream[cursor]
        require(episode in usages, f"{session}: usage absent for operation-producing episode {episode}")
        register_assignment(
            result,
            step_id,
            UsageAssignment(f"{session}:terminus2:episode-{episode}", usages[episode], sources[episode]),
        )
        cursor += 1
    skipped += len(response_stream) - cursor
    require(skipped <= 2, f"{session}: unexpected {skipped} extra Terminus response commands")
    return result


_USAGE_RE = re.compile(
    r"usage=Usage\(completion_tokens=(\d+), prompt_tokens=(\d+), total_tokens=(\d+)"
)


def extract_sweagent_usage(
    session: str, archive: Path, operations: list[dict[str, Any]]
) -> dict[int, UsageAssignment]:
    trajectory_member = split_source_ref(operations[0]["source_ref"])[0]
    debug_member = trajectory_member.rsplit(".traj", 1)[0] + ".debug.log"
    members = archive_members(archive, lambda name: name in {trajectory_member, debug_member})
    require(set(members) == {trajectory_member, debug_member}, f"{session}: SWE-agent members missing")
    trajectory_data = json_bytes(members[trajectory_member], trajectory_member)
    trajectory = trajectory_data.get("trajectory") if isinstance(trajectory_data, dict) else None
    history = trajectory_data.get("history") if isinstance(trajectory_data, dict) else None
    require(isinstance(trajectory, list) and isinstance(history, list), f"{session}: invalid SWE-agent trajectory")
    require(len(trajectory) == len(operations), f"{session}: SWE-agent trajectory count mismatch")

    response_records: list[tuple[str, Usage, set[str]]] = []
    for line in members[debug_member].decode(errors="replace").splitlines():
        if "Response: ModelResponse(" not in line or "usage=Usage(" not in line:
            continue
        usage_match = _USAGE_RE.search(line)
        require(usage_match is not None, f"{session}: cannot parse SWE-agent usage line")
        completion, prompt, total = map(int, usage_match.groups())
        usage = Usage(prompt, completion, total)
        require(total == prompt + completion and total > 0, f"{session}: invalid SWE-agent usage")
        response_match = re.search(r"ModelResponse\(id='([^']+)'", line)
        response_id = response_match.group(1) if response_match else f"line-{len(response_records)}"
        tool_ids = set(re.findall(r"id='(call_[^']+)'", line))
        response_records.append((response_id, usage, tool_ids))
    require(response_records, f"{session}: no SWE-agent response usage")
    by_tool_id: dict[str, int] = {}
    for index, (_, _, tool_ids) in enumerate(response_records):
        for tool_id in tool_ids:
            by_tool_id[tool_id] = index

    assistant_actions = [
        message
        for message in history
        if isinstance(message, dict)
        and message.get("role") == "assistant"
        and message.get("message_type") == "action"
    ]
    trajectory_actions = [
        json.dumps(item.get("action"), ensure_ascii=False, sort_keys=True)
        if isinstance(item, dict) and isinstance(item.get("action"), dict)
        else str(item.get("action") or "")
        for item in trajectory
    ]
    matched: list[tuple[int, int]] = []
    trajectory_cursor = 0
    for message in assistant_actions:
        action = str(message.get("action") or "")
        while trajectory_cursor < len(trajectory_actions) and trajectory_actions[trajectory_cursor] != action:
            trajectory_cursor += 1
        require(trajectory_cursor < len(trajectory_actions), f"{session}: history action absent from final trajectory")
        calls = message.get("tool_calls")
        tool_ids = [call.get("id") for call in calls or [] if isinstance(call, dict) and isinstance(call.get("id"), str)]
        require(tool_ids and all(tool_id in by_tool_id for tool_id in tool_ids), f"{session}: accepted tool response absent from debug log")
        indexes = {by_tool_id[tool_id] for tool_id in tool_ids}
        require(len(indexes) == 1, f"{session}: one action spans accepted responses")
        matched.append((trajectory_cursor, indexes.pop()))
        trajectory_cursor += 1

    result: dict[int, UsageAssignment] = {}
    used_response_indexes: set[int] = set()
    for trajectory_index, response_index in matched:
        response_id, usage, _ = response_records[response_index]
        used_response_indexes.add(response_index)
        register_assignment(
            result,
            trajectory_index + 1,
            UsageAssignment(f"{session}:sweagent:{response_id}", usage, debug_member),
        )

    matched_by_trajectory = dict(matched)
    unmatched = [index for index in range(len(trajectory)) if index not in matched_by_trajectory]
    used_retry_indexes: set[int] = set()
    for trajectory_index in unmatched:
        require(trajectory_actions[trajectory_index] == "", f"{session}: unmatched nonempty SWE-agent action")
        previous = max((response for traj, response in matched if traj < trajectory_index), default=-1)
        following = min((response for traj, response in matched if traj > trajectory_index), default=len(response_records))
        require(previous >= 0 and following < len(response_records), f"{session}: empty SWE-agent operation lacks two accepted anchors")
        candidates = [
            index
            for index in range(previous + 1, following)
            if index not in used_response_indexes and index not in used_retry_indexes
        ]
        require(candidates, f"{session}: unmatched retry operation has no response usage")
        usage = Usage(0, 0, 0)
        response_ids = []
        for index in candidates:
            response_id, item_usage, _ = response_records[index]
            response_ids.append(response_id)
            usage = usage + item_usage
            used_retry_indexes.add(index)
        register_assignment(
            result,
            trajectory_index + 1,
            UsageAssignment(f"{session}:sweagent:retry:{'+'.join(response_ids)}", usage, debug_member),
        )
    return result


def extract_usage_for_session(
    session: str,
    manifest_row: pd.Series,
    operations: list[dict[str, Any]],
    hub_root: Path,
) -> dict[int, UsageAssignment]:
    archive = hub_root / str(manifest_row["artifact_path"])
    form = source_form(str(manifest_row["agent"]), operations[0]["source_ref"])
    if form in {"mini-native", "mini-swe-raw"}:
        result = extract_miniswe_usage(session, archive, operations)
    elif form == "openhands-native":
        result = extract_openhands_native_usage(session, archive, operations)
    elif form == "openhands-swe-raw":
        result = extract_openhands_swe_usage(session, archive, operations, str(manifest_row["source_relpath"]))
    elif form == "terminus2":
        result = extract_terminus_usage(session, archive, operations, str(manifest_row["source_relpath"]))
    elif form == "swe-agent":
        result = extract_sweagent_usage(session, archive, operations)
    else:
        raise EvaluationError(f"unsupported source form: {form}")
    require(set(result) == {int(row["step_id"]) for row in operations}, f"{session}: incomplete usage mapping")
    return result


def attach_usage(
    rows: list[dict[str, Any]], manifest: pd.DataFrame, hub_root: Path
) -> tuple[dict[tuple[str, int], UsageAssignment], dict[str, Any]]:
    operations_by_session: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        operations_by_session[str(row["session"])].append(row)
    assignments: dict[tuple[str, int], UsageAssignment] = {}
    forms: Counter[str] = Counter()
    form_operations: Counter[str] = Counter()
    for index, (session, operations) in enumerate(operations_by_session.items(), 1):
        operations.sort(key=lambda row: int(row["step_id"]))
        mapping = extract_usage_for_session(session, manifest.loc[session], operations, hub_root)
        form = operations[0]["source_form"]
        forms[form] += 1
        form_operations[form] += len(operations)
        for step_id, assignment in mapping.items():
            assignments[(session, step_id)] = assignment
        if index % 25 == 0 or index == len(operations_by_session):
            print(f"usage recovery: {index}/{len(operations_by_session)} sessions", flush=True)
    require(len(assignments) == len(rows), "usage assignment coverage mismatch")
    return assignments, {
        "sessions_by_source_form": dict(sorted(forms.items())),
        "operations_by_source_form": dict(sorted(form_operations.items())),
    }


def weighted_bcubed(
    rows: list[dict[str, Any]], method: str, weights: dict[tuple[str, int], float] | None = None
) -> dict[str, Any]:
    if weights is None:
        weights = {(str(row["session"]), int(row["step_id"])): 1.0 for row in rows}
    predicted_totals: Counter[str] = Counter()
    official_totals: Counter[str] = Counter()
    overlaps: Counter[tuple[str, str]] = Counter()
    total_weight = 0.0
    for row in rows:
        key = (str(row["session"]), int(row["step_id"]))
        weight = float(weights[key])
        require(weight >= 0 and math.isfinite(weight), f"invalid object weight: {key}")
        predicted = str(row[method])
        official = str(row["official_stage"])
        predicted_totals[predicted] += weight
        official_totals[official] += weight
        overlaps[(predicted, official)] += weight
        total_weight += weight
    require(total_weight > 0, f"zero total weight for {method}")
    precision_numerator = 0.0
    recall_numerator = 0.0
    for row in rows:
        key = (str(row["session"]), int(row["step_id"]))
        weight = float(weights[key])
        if weight == 0:
            continue
        predicted = str(row[method])
        official = str(row["official_stage"])
        overlap = overlaps[(predicted, official)]
        precision_numerator += weight * overlap / predicted_totals[predicted]
        recall_numerator += weight * overlap / official_totals[official]
    precision = precision_numerator / total_weight
    recall = recall_numerator / total_weight
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {
        "operations": len(rows),
        "positive_weight_operations": sum(weights[(str(row["session"]), int(row["step_id"]))] > 0 for row in rows),
        "total_weight": total_weight,
        "predicted_groups": len(predicted_totals),
        "official_groups": len(official_totals),
        "precision": precision,
        "recall": recall,
        "f1": f1,
    }


def all_method_metrics(
    rows: list[dict[str, Any]], weights: dict[tuple[str, int], float] | None = None
) -> dict[str, Any]:
    return {method: weighted_bcubed(rows, method, weights) for method in METHODS}


def operation_weights(
    rows: list[dict[str, Any]],
    usage_assignments: dict[tuple[str, int], UsageAssignment],
    field: str,
    scheme: str,
) -> dict[tuple[str, int], float]:
    grouped: dict[str, list[tuple[str, int]]] = defaultdict(list)
    usage_by_group: dict[str, Usage] = {}
    for row in rows:
        key = (str(row["session"]), int(row["step_id"]))
        assignment = usage_assignments[key]
        grouped[assignment.response_id].append(key)
        previous = usage_by_group.setdefault(assignment.response_id, assignment.usage)
        require(previous == assignment.usage, f"conflicting usage for {assignment.response_id}")
    weights = {key: 0.0 for keys in grouped.values() for key in keys}
    for group_id, keys in grouped.items():
        value = float(getattr(usage_by_group[group_id], field))
        if scheme == "equal":
            for key in keys:
                weights[key] = value / len(keys)
        elif scheme == "first":
            weights[keys[0]] = value
        elif scheme == "last":
            weights[keys[-1]] = value
        else:
            raise EvaluationError(f"unknown allocation scheme: {scheme}")
    return weights


def usage_validity(
    rows: list[dict[str, Any]], usage_assignments: dict[tuple[str, int], UsageAssignment]
) -> dict[str, Any]:
    rows_by_key = {(str(row["session"]), int(row["step_id"])): row for row in rows}
    groups: dict[str, list[tuple[str, int]]] = defaultdict(list)
    usage_by_group: dict[str, Usage] = {}
    for key, assignment in usage_assignments.items():
        groups[assignment.response_id].append(key)
        previous = usage_by_group.setdefault(assignment.response_id, assignment.usage)
        require(previous == assignment.usage, f"usage conflict in {assignment.response_id}")
    multi = {group: keys for group, keys in groups.items() if len(keys) > 1}
    crossing = {field: 0 for field in ("official_stage", "recurrence", "raw_action_key_change")}
    crossing_mass = {field: 0 for field in crossing}
    for group, keys in multi.items():
        for field in crossing:
            if len({rows_by_key[key][field] for key in keys}) > 1:
                crossing[field] += 1
                crossing_mass[field] += usage_by_group[group].total_tokens
    unique_totals = {
        field: sum(getattr(usage, field) for usage in usage_by_group.values())
        for field in USAGE_FIELDS
    }
    equal_totals = {
        field: sum(operation_weights(rows, usage_assignments, field, "equal").values())
        for field in USAGE_FIELDS
    }
    for field in USAGE_FIELDS:
        require(math.isclose(unique_totals[field], equal_totals[field], rel_tol=0, abs_tol=1e-6), f"{field} mass not conserved")
    return {
        "response_groups": len(groups),
        "multi_operation_responses": len(multi),
        "multi_operation_operations": sum(len(keys) for keys in multi.values()),
        "multi_operation_total_tokens": sum(usage_by_group[group].total_tokens for group in multi),
        "crossing_response_counts": crossing,
        "crossing_total_tokens": crossing_mass,
        "provider_totals": unique_totals,
        "allocated_equal_totals": equal_totals,
    }


def reproduce_step0024(
    rows: list[dict[str, Any]], metrics: dict[str, Any], path: Path, mode: str
) -> dict[str, Any]:
    if mode != "full":
        return {"status": "not_applicable_preflight"}
    existing = json.loads(path.read_text(encoding="utf-8"))["metrics"]
    differences: dict[str, Any] = {}
    for method in EXISTING_METHODS:
        differences[method] = {}
        for metric in ("precision", "recall", "f1"):
            actual = float(metrics[method][metric])
            expected = float(existing[method]["partition"][metric])
            differences[method][metric] = actual - expected
            require(abs(actual - expected) <= 1e-12, f"Step 0024 reproduction failed: {method}.{metric}")
    require(len(rows) == int(existing["recurrence"]["partition"]["operations"]), "Step 0024 operation count changed")
    return {"status": "pass", "tolerance": 1e-12, "differences": differences}


def task_cluster_bootstrap(
    rows: list[dict[str, Any]], resamples: int, seed: int
) -> dict[str, Any]:
    rows_by_session: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        rows_by_session[str(row["session"])].append(row)
    sufficient: dict[tuple[str, str], tuple[float, float, int]] = {}
    task_sessions: dict[str, list[str]] = defaultdict(list)
    for session, session_rows in rows_by_session.items():
        task = str(session_rows[0]["task_name"])
        task_sessions[task].append(session)
        for method in ("recurrence", "raw_action_key_change"):
            metric = weighted_bcubed(session_rows, method)
            count = len(session_rows)
            sufficient[(session, method)] = (metric["precision"] * count, metric["recall"] * count, count)

    def f1_for(draw: list[str], method: str) -> float:
        precision_sum = recall_sum = 0.0
        count = 0
        for task in draw:
            for session in task_sessions[task]:
                p_sum, r_sum, n = sufficient[(session, method)]
                precision_sum += p_sum
                recall_sum += r_sum
                count += n
        precision = precision_sum / count
        recall = recall_sum / count
        return 2 * precision * recall / (precision + recall) if precision + recall else 0.0

    tasks = sorted(task_sessions)
    require(len(tasks) == 251, f"expected 251 task clusters, got {len(tasks)}")
    generator = random.Random(seed)
    deltas = []
    for _ in range(resamples):
        draw = generator.choices(tasks, k=len(tasks))
        deltas.append(f1_for(draw, "recurrence") - f1_for(draw, "raw_action_key_change"))
    return {
        "unit": "task_name",
        "clusters": len(tasks),
        "resamples": resamples,
        "seed": seed,
        "mean_delta": float(np.mean(deltas)),
        "median_delta": float(np.median(deltas)),
        "ci95": [float(np.percentile(deltas, 2.5)), float(np.percentile(deltas, 97.5))],
        "positive_fraction": sum(delta > 0 for delta in deltas) / len(deltas),
    }


def selection_audit(manifest: pd.DataFrame, selected: set[str]) -> dict[str, Any]:
    failed = manifest[manifest["solved"] == False]  # noqa: E712
    included = failed[failed.index.isin(selected)]
    excluded = failed[~failed.index.isin(selected)]
    require(len(failed) == 468 and len(included) == 405 and len(excluded) == 63, "selection population changed")

    def describe(frame: pd.DataFrame) -> dict[str, Any]:
        steps = frame["step_count"].astype(int)
        return {
            "sessions": len(frame),
            "distinct_tasks": int(frame["task_name"].nunique()),
            "framework_sessions": {str(key): int(value) for key, value in frame["agent"].value_counts().sort_index().items()},
            "steps_total": int(steps.sum()),
            "steps_min": int(steps.min()),
            "steps_median": float(steps.median()),
            "steps_mean": float(steps.mean()),
            "steps_max": int(steps.max()),
        }

    return {"failed_release": describe(failed), "included": describe(included), "excluded": describe(excluded)}


def per_session_rows(
    rows: list[dict[str, Any]], usage_assignments: dict[tuple[str, int], UsageAssignment]
) -> list[dict[str, Any]]:
    by_session: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_session[str(row["session"])].append(row)
    result = []
    total_weights = operation_weights(rows, usage_assignments, "total_tokens", "equal")
    for session, session_rows in by_session.items():
        session_weights = {
            (str(row["session"]), int(row["step_id"])): total_weights[(str(row["session"]), int(row["step_id"]))]
            for row in session_rows
        }
        result.append(
            {
                "session": session,
                "framework": session_rows[0]["framework"],
                "task_name": session_rows[0]["task_name"],
                "source_form": session_rows[0]["source_form"],
                "operations": len(session_rows),
                "ordinary": all_method_metrics(session_rows),
                "token_weighted": all_method_metrics(session_rows, session_weights),
            }
        )
    return result


def framework_metrics(
    rows: list[dict[str, Any]], usage_assignments: dict[tuple[str, int], UsageAssignment]
) -> dict[str, Any]:
    result: dict[str, Any] = {}
    by_framework: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_framework[str(row["framework"])].append(row)
    all_weights = operation_weights(rows, usage_assignments, "total_tokens", "equal")
    for framework, framework_rows in sorted(by_framework.items()):
        weights = {
            (str(row["session"]), int(row["step_id"])): all_weights[(str(row["session"]), int(row["step_id"]))]
            for row in framework_rows
        }
        result[framework] = {
            "operations": len(framework_rows),
            "ordinary": all_method_metrics(framework_rows),
            "token_weighted": all_method_metrics(framework_rows, weights),
        }
    return result


def classify_result(
    ordinary: dict[str, Any], bootstrap: dict[str, Any] | None, sensitivity: dict[str, Any], mode: str
) -> dict[str, Any]:
    ordinary_delta = ordinary["recurrence"]["f1"] - ordinary["raw_action_key_change"]["f1"]
    weighted_deltas = {
        scheme: values["recurrence"]["f1"] - values["raw_action_key_change"]["f1"]
        for scheme, values in sensitivity.items()
    }
    if mode == "preflight":
        verdict = "preflight_only"
    elif ordinary_delta <= 0:
        verdict = "contradicted"
    elif bootstrap is None or bootstrap["ci95"][0] <= 0:
        verdict = "inconclusive"
    elif all(delta > 0 for delta in weighted_deltas.values()):
        verdict = "supported"
    elif any(delta > 0 for delta in weighted_deltas.values()) and any(delta <= 0 for delta in weighted_deltas.values()):
        verdict = "inconclusive"
    else:
        verdict = "mixed"
    return {
        "verdict": verdict,
        "ordinary_f1_delta": ordinary_delta,
        "total_token_weighted_f1_deltas": weighted_deltas,
        "resource_statement_authorized": verdict == "supported",
    }


def markdown_report(summary: dict[str, Any]) -> str:
    lines = [
        "# RQ1 CodeTraceBench Stage And Token Attribution Result",
        "",
        f"**Mode:** `{summary['mode']}`",
        "",
        f"**Verdict:** **{summary['decision']['verdict'].upper()}**",
        "",
        "## Population",
        "",
        f"- sessions: {summary['population']['sessions']}",
        f"- operations: {summary['population']['operations']}",
        f"- official stages: {summary['population']['official_stages']}",
        f"- source forms: `{json.dumps(summary['usage_recovery']['sessions_by_source_form'], sort_keys=True)}`",
        "",
        "## Standard Ordinary B-cubed",
        "",
        "| View | Precision | Recall | F1 |",
        "|---|---:|---:|---:|",
    ]
    for method in METHODS:
        metric = summary["ordinary_bcubed"][method]
        label = METHOD_LABELS.get(method, method)
        lines.append(f"| {label} | {metric['precision']:.6f} | {metric['recall']:.6f} | {metric['f1']:.6f} |")
    lines.extend(
        [
            "",
            "## Total-token-weighted B-cubed (equal allocation)",
            "",
            "| View | Precision | Recall | F1 |",
            "|---|---:|---:|---:|",
        ]
    )
    for method in METHODS:
        metric = summary["weighted_bcubed"]["total_tokens"]["equal"][method]
        label = METHOD_LABELS.get(method, method)
        lines.append(f"| {label} | {metric['precision']:.6f} | {metric['recall']:.6f} | {metric['f1']:.6f} |")
    lines.extend(
        [
            "",
            "## Diagnostic Only" if summary["mode"] == "preflight" else "## Decision",
            "",
            f"- ordinary recurrence-minus-raw-action-key F1: `{summary['decision']['ordinary_f1_delta']:.6f}`",
            f"- token-weighted allocation deltas: `{json.dumps(summary['decision']['total_token_weighted_f1_deltas'], sort_keys=True)}`",
            f"- resource-attribution statement authorized: `{str(summary['decision']['resource_statement_authorized']).lower()}`",
            "",
            "## Validity",
            "",
            f"- Step 0024 reproduction: `{summary['step0024_reproduction']['status']}`",
            f"- response groups: {summary['usage_validity']['response_groups']}",
            f"- multi-operation responses: {summary['usage_validity']['multi_operation_responses']}",
            f"- crossing counts: `{json.dumps(summary['usage_validity']['crossing_response_counts'], sort_keys=True)}`",
            f"- provider token totals: `{json.dumps(summary['usage_validity']['provider_totals'], sort_keys=True)}`",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    output = args.output or DEFAULT_OUTPUT_ROOT / args.mode
    output.mkdir(parents=True, exist_ok=True)
    rows, manifest, target_rows, selected = load_inputs(args)

    operations_by_session: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for session in selected:
        operations_by_session[session] = target_rows[session]
    usage_assignments, recovery = attach_usage(rows, manifest, args.hub_root)
    ordinary = all_method_metrics(rows)
    reproduction = reproduce_step0024(rows, ordinary, args.step0024_summary, args.mode)
    validity = usage_validity(rows, usage_assignments)

    weighted: dict[str, Any] = {}
    for field in USAGE_FIELDS:
        weighted[field] = {}
        schemes = ("equal", "first", "last") if field == "total_tokens" else ("equal",)
        for scheme in schemes:
            weighted[field][scheme] = all_method_metrics(
                rows, operation_weights(rows, usage_assignments, field, scheme)
            )
    sensitivity = weighted["total_tokens"]
    bootstrap = (
        task_cluster_bootstrap(rows, args.bootstrap_resamples, args.bootstrap_seed)
        if args.mode == "full"
        else None
    )
    decision = classify_result(ordinary, bootstrap, sensitivity, args.mode)

    selected_set = set(selected)
    selection = selection_audit(manifest, selected_set) if args.mode == "full" else None
    summary = {
        "mode": args.mode,
        "population": {
            "sessions": len(selected),
            "operations": len(rows),
            "official_stages": len({row["official_stage"] for row in rows}),
            "distinct_tasks": len({row["task_name"] for row in rows}),
            "framework_operations": dict(sorted(Counter(str(row["framework"]) for row in rows).items())),
        },
        "usage_recovery": recovery,
        "ordinary_bcubed": ordinary,
        "weighted_bcubed": weighted,
        "usage_validity": validity,
        "task_cluster_bootstrap": bootstrap,
        "selection_audit": selection,
        "step0024_reproduction": reproduction,
        "decision": decision,
        "inputs": {
            "manifest": str(args.manifest),
            "target_operations": str(args.target_operations),
            "assignments": str(args.assignments),
            "hub_root": str(args.hub_root),
        },
    }

    usage_rows = []
    equal_weights = {
        field: operation_weights(rows, usage_assignments, field, "equal")
        for field in USAGE_FIELDS
    }
    group_sizes = Counter(assignment.response_id for assignment in usage_assignments.values())
    for row in rows:
        key = (str(row["session"]), int(row["step_id"]))
        assignment = usage_assignments[key]
        usage_rows.append(
            {
                **row,
                "response_id": assignment.response_id,
                "response_source": assignment.source,
                "response_operation_count": group_sizes[assignment.response_id],
                "response_prompt_tokens": assignment.usage.prompt_tokens,
                "response_completion_tokens": assignment.usage.completion_tokens,
                "response_total_tokens": assignment.usage.total_tokens,
                **{field: equal_weights[field][key] for field in USAGE_FIELDS},
            }
        )
    write_jsonl(output / "operation-usage.jsonl", usage_rows)
    write_jsonl(output / "per-session.jsonl", per_session_rows(rows, usage_assignments))
    write_json(output / "framework-metrics.json", framework_metrics(rows, usage_assignments))
    write_json(output / "summary.json", summary)
    (output / "report.md").write_text(markdown_report(summary), encoding="utf-8")
    print(json.dumps({"output": str(output), "decision": decision, "population": summary["population"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
