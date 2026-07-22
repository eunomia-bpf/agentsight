#!/usr/bin/env python3
"""Build task-centric profiles from explicit Codex task-control events.

Persistent task frames come only from user task turns, update_plan items, and
uniquely linked child-agent delegations. Model/tool/file/process fields never
create persistent task frames. The script contains two intentionally separate
paths: a normalized-event candidate and a direct raw-event reference replay.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SESSIONS = Path.home() / ".codex" / "sessions"
DEFAULT_OUTPUT = ROOT / ".agentsight" / "experiments" / "source-native-task-stack-v1"

RELEVANT_PREFIXES = (
    '"type":"session_meta"',
    '"type":"event_msg"',
    '"type":"response_item"',
)
CALL_ID_RE = re.compile(r'"call_id"\s*:\s*"([^"]+)"')
CHILD_ID_RE = re.compile(r'(?:agent_id|thread_id)\\?"\s*:\s*\\?"([A-Za-z0-9._:-]{3,})', re.I)
FILE_RE = re.compile(r"(?:^|\s)([/~.]?[^\s'\"]+\.[A-Za-z0-9]{1,8})(?:$|\s)")


@dataclass(frozen=True)
class Frame:
    source_id: str
    kind: str
    label: str


@dataclass
class NormalizedEvent:
    line: int
    timestamp: str
    kind: str
    source_id: str
    name: str = ""
    call_id: str = ""
    text: str = ""
    phase: str = ""
    args: dict[str, Any] = field(default_factory=dict)
    plan: list[dict[str, str]] = field(default_factory=list)
    child_id: str = ""
    result: str = "observed"
    input_tokens: int = 0
    output_tokens: int = 0


@dataclass
class CandidateSession:
    path: Path
    session_id: str
    parent_id: str = ""
    thread_source: str = ""
    depth: int = 0
    cwd: str = ""
    events: list[NormalizedEvent] = field(default_factory=list)
    parse_errors: int = 0
    ownership_boundary_required: bool = False
    ownership_boundary_found: bool = True
    copied_records_skipped: int = 0


@dataclass
class RawEvent:
    line: int
    timestamp: str
    kind: str
    source_id: str
    name: str = ""
    call_id: str = ""
    text: str = ""
    phase: str = ""
    args: dict[str, Any] = field(default_factory=dict)
    plan: list[dict[str, str]] = field(default_factory=list)
    child_id: str = ""
    result: str = "observed"
    input_tokens: int = 0
    output_tokens: int = 0


@dataclass
class ReferenceSession:
    path: Path
    session_id: str
    parent_id: str = ""
    thread_source: str = ""
    depth: int = 0
    cwd: str = ""
    events: list[RawEvent] = field(default_factory=list)
    parse_errors: int = 0
    ownership_boundary_required: bool = False
    ownership_boundary_found: bool = True
    copied_records_skipped: int = 0


@dataclass
class OperationPath:
    operation_id: str
    session_id: str
    line: int
    timestamp: str
    task_ids: tuple[str, ...]
    task_labels: tuple[str, ...]
    operation_kind: str
    phase: str
    action: str
    object: str
    result: str
    event_weight: int
    token_weight: int

    def json(self) -> dict[str, Any]:
        row = asdict(self)
        row["task_ids"] = list(self.task_ids)
        row["task_labels"] = list(self.task_labels)
        return row


@dataclass
class ReplayResult:
    operations: list[OperationPath] = field(default_factory=list)
    task_controls: int = 0
    task_transitions: set[str] = field(default_factory=set)
    spawn_snapshots: dict[str, tuple[Frame, ...]] = field(default_factory=dict)
    spawn_sources: dict[str, str] = field(default_factory=dict)
    unresolved_parent_links: list[str] = field(default_factory=list)
    unresolved_operations: int = 0
    unresolved_operation_sources: list[str] = field(default_factory=list)
    plan_conflicts: int = 0
    plan_conflict_sources: list[str] = field(default_factory=list)
    task_outcomes: Counter[str] = field(default_factory=Counter)
    completion_transitions: set[str] = field(default_factory=set)
    root_by_session: dict[str, str] = field(default_factory=dict)
    session_controls: Counter[str] = field(default_factory=Counter)
    session_structural_controls: Counter[str] = field(default_factory=Counter)
    session_unresolved_operations: Counter[str] = field(default_factory=Counter)
    session_plan_conflicts: Counter[str] = field(default_factory=Counter)
    session_completions: Counter[str] = field(default_factory=Counter)


def parse_json_value(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    if not isinstance(value, str):
        return {}
    try:
        parsed = json.loads(value)
    except (json.JSONDecodeError, TypeError):
        return {}
    return parsed if isinstance(parsed, dict) else {}


def compact_space(value: str, limit: int = 180) -> str:
    cleaned = " ".join(value.replace("\x00", " ").split())
    return cleaned if len(cleaned) <= limit else cleaned[: limit - 1] + "…"


def task_label(value: str, limit: int = 130) -> str:
    text = value.strip()
    marker = "## My request for Codex:"
    if marker in text:
        text = text.rsplit(marker, 1)[-1]
    text = re.sub(r"<environment_context>.*?</environment_context>", " ", text, flags=re.S)
    text = re.sub(r"<recommended_plugins>.*?</recommended_plugins>", " ", text, flags=re.S)
    return compact_space(text.strip("'\""), limit) or "Unnamed task"


def candidate_message_text(payload: dict[str, Any]) -> str:
    content = payload.get("content")
    if isinstance(content, str):
        return content
    if not isinstance(content, list):
        return str(payload.get("message") or "")
    return " ".join(
        str(item.get("text") or "")
        for item in content
        if isinstance(item, dict) and item.get("type") in {"input_text", "text"}
    )


def reference_message_text(payload: dict[str, Any]) -> str:
    raw = payload.get("content")
    if isinstance(raw, list):
        pieces: list[str] = []
        for item in raw:
            if not isinstance(item, dict):
                continue
            if item.get("type") in ("input_text", "text"):
                pieces.append(str(item.get("text") or ""))
        return " ".join(pieces)
    if isinstance(raw, str):
        return raw
    fallback = payload.get("message")
    return fallback if isinstance(fallback, str) else ""


def command_text(value: Any) -> str:
    if isinstance(value, list):
        return " ".join(str(part) for part in value)
    return str(value or "")


def relevant_line(line: str) -> bool:
    prefix = line[:512].replace(" ", "")
    if not any(marker in prefix for marker in RELEVANT_PREFIXES):
        return False
    if '"type":"response_item"' in prefix:
        return any(
            marker in prefix
            for marker in (
                '"type":"function_call"',
                '"type":"function_call_output"',
                '"type":"message"',
            )
        )
    if '"type":"event_msg"' in prefix:
        return any(
            marker in prefix
            for marker in (
                '"type":"user_message"',
                '"type":"agent_message"',
                '"type":"token_count"',
                '"type":"task_started"',
                '"type":"sub_agent_activity"',
            )
        )
    return True


def light_output(line: str) -> tuple[str, str, str]:
    prefix = line[:16_000]
    call_match = CALL_ID_RE.search(prefix)
    call_id = call_match.group(1) if call_match else ""
    child_match = CHILD_ID_RE.search(prefix)
    child_id = child_match.group(1) if child_match else ""
    status = tool_output_status(prefix)
    return call_id, child_id, status


def tool_output_status(output: str) -> str:
    """Use explicit machine outcomes, not words such as 'error' in prose."""

    lowered = output.lower()
    if "process exited with code 0" in lowered or '"success":true' in lowered:
        return "success"
    if (
        re.search(r"process exited with code\s+[1-9][0-9]*", lowered)
        or '"success":false' in lowered
        or '"is_error":true' in lowered
    ):
        return "error"
    return "observed"


def normalize_plan(args: dict[str, Any]) -> list[dict[str, str]]:
    raw = args.get("plan")
    if not isinstance(raw, list):
        return []
    out: list[dict[str, str]] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        step = str(item.get("step") or "")
        status = str(item.get("status") or "")
        if step:
            out.append({"step": step, "status": status})
    return out


def source_depth(meta: dict[str, Any]) -> int:
    try:
        return int(meta.get("source", {}).get("subagent", {}).get("thread_spawn", {}).get("depth") or 0)
    except (AttributeError, TypeError, ValueError):
        return 0


def timestamp_seconds(value: str) -> float:
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp()
    except (TypeError, ValueError):
        return 0.0


def candidate_uuid7_seconds(value: str) -> float:
    parts = value.split("-")
    if len(parts) != 5 or not parts[2].startswith("7"):
        return 0.0
    try:
        return int(parts[0] + parts[1], 16) / 1000.0
    except ValueError:
        return 0.0


def reference_uuid7_seconds(value: str) -> float:
    groups = value.split("-")
    if len(groups) != 5 or not groups[2].startswith("7"):
        return 0.0
    prefix = groups[0] + groups[1]
    try:
        milliseconds = int(prefix, 16)
    except ValueError:
        return 0.0
    return milliseconds / 1000.0


def snapshot_lines(path: Path, max_bytes: int | None = None) -> Iterable[tuple[int, str]]:
    """Yield complete UTF-8-decoded JSONL records from one fixed byte prefix."""

    try:
        handle = path.open("rb")
    except OSError:
        return
    consumed = 0
    line_number = 0
    with handle:
        while True:
            raw = handle.readline()
            if not raw:
                break
            if max_bytes is not None and consumed + len(raw) > max_bytes:
                break
            consumed += len(raw)
            line_number += 1
            yield line_number, raw.decode("utf-8", errors="replace")


def candidate_parse_session(path: Path, max_bytes: int | None = None) -> CandidateSession | None:
    session = CandidateSession(path=path, session_id=path.stem)
    calls: dict[str, NormalizedEvent] = {}
    outputs: dict[str, tuple[str, str]] = {}
    activity_children: dict[str, str] = {}
    canonical_meta_seen = False
    owns_events = True
    session_started_at = 0.0
    for lineno, line in snapshot_lines(path, max_bytes):
        if not relevant_line(line):
            continue
        if '"type":"function_call_output"' in line[:512] and len(line) > 1_000_000:
            call_id, child_id, status = light_output(line)
            if call_id:
                outputs[call_id] = (child_id, status)
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            session.parse_errors += 1
            continue
        payload = row.get("payload") if isinstance(row.get("payload"), dict) else {}
        timestamp = str(row.get("timestamp") or "")
        rtype = str(row.get("type") or "")
        ptype = str(payload.get("type") or "")
        if rtype == "session_meta":
            if not canonical_meta_seen:
                canonical_meta_seen = True
                session.session_id = str(payload.get("id") or session.session_id)
                source = payload.get("source") if isinstance(payload.get("source"), dict) else {}
                subagent = source.get("subagent") if isinstance(source.get("subagent"), dict) else {}
                thread_spawn = (
                    subagent.get("thread_spawn")
                    if isinstance(subagent.get("thread_spawn"), dict)
                    else {}
                )
                session.parent_id = str(
                    payload.get("parent_thread_id")
                    or payload.get("forked_from_id")
                    or thread_spawn.get("parent_thread_id")
                    or ""
                )
                session.thread_source = str(payload.get("thread_source") or "")
                session.depth = source_depth(payload)
                session.cwd = str(payload.get("cwd") or "")
                session_started_at = timestamp_seconds(
                    str(payload.get("timestamp") or timestamp)
                )
                owns_events = not bool(
                    session.parent_id or payload.get("forked_from_id")
                )
                session.ownership_boundary_required = not owns_events
                session.ownership_boundary_found = owns_events
            continue
        if rtype == "event_msg" and ptype == "task_started":
            started_at = float(payload.get("started_at") or 0.0)
            turn_started_at = candidate_uuid7_seconds(str(payload.get("turn_id") or ""))
            source_start = started_at or turn_started_at
            boundary = int(session_started_at) if started_at else session_started_at
            if not owns_events and source_start and (
                session_started_at == 0.0 or source_start >= boundary
            ):
                owns_events = True
                session.ownership_boundary_found = True
            continue
        if not owns_events:
            session.copied_records_skipped += 1
            continue
        source_id = f"{session.session_id}:line:{lineno}"
        if rtype == "event_msg" and ptype == "sub_agent_activity":
            event_id = str(payload.get("event_id") or "")
            child_id = str(payload.get("agent_thread_id") or "")
            if event_id and child_id and str(payload.get("kind") or "") == "started":
                activity_children[event_id] = child_id
        elif rtype == "event_msg" and ptype == "user_message":
            session.events.append(
                NormalizedEvent(lineno, timestamp, "user", source_id, text=str(payload.get("message") or ""))
            )
        elif rtype == "event_msg" and ptype == "agent_message":
            session.events.append(
                NormalizedEvent(
                    lineno,
                    timestamp,
                    "agent",
                    source_id,
                    text=str(payload.get("message") or ""),
                    phase=str(payload.get("phase") or ""),
                )
            )
        elif rtype == "event_msg" and ptype == "token_count":
            info = payload.get("info") if isinstance(payload.get("info"), dict) else {}
            usage = info.get("last_token_usage") if isinstance(info.get("last_token_usage"), dict) else {}
            session.events.append(
                NormalizedEvent(
                    lineno,
                    timestamp,
                    "llm",
                    source_id,
                    input_tokens=int(usage.get("input_tokens") or 0),
                    output_tokens=int(usage.get("output_tokens") or 0),
                )
            )
        elif (
            rtype == "response_item"
            and ptype == "message"
            and str(payload.get("role") or "") == "user"
        ):
            session.events.append(
                NormalizedEvent(
                    lineno,
                    timestamp,
                    "user",
                    source_id,
                    text=candidate_message_text(payload),
                )
            )
        elif rtype == "response_item" and ptype == "function_call":
            args = parse_json_value(payload.get("arguments"))
            name = str(payload.get("name") or "tool")
            call_id = str(payload.get("call_id") or f"line-{lineno}")
            kind = "plan" if name == "update_plan" else "spawn" if name == "spawn_agent" else "tool"
            event = NormalizedEvent(
                lineno,
                timestamp,
                kind,
                source_id,
                name=name,
                call_id=call_id,
                args=args,
                plan=normalize_plan(args) if kind == "plan" else [],
                text=str(args.get("message") or "") if kind == "spawn" else "",
            )
            session.events.append(event)
            calls[call_id] = event
        elif rtype == "response_item" and ptype == "function_call_output":
            call_id = str(payload.get("call_id") or "")
            output = payload.get("output")
            output_text = output if isinstance(output, str) else json.dumps(output, ensure_ascii=False)
            child_match = CHILD_ID_RE.search(output_text[:16_000])
            child_id = child_match.group(1) if child_match else ""
            status = tool_output_status(output_text[:16_000])
            if call_id:
                outputs[call_id] = (child_id, status)
    for call_id, event in calls.items():
        child_id, status = outputs.get(call_id, ("", "observed"))
        event.child_id = child_id or activity_children.get(call_id, "")
        event.result = status
    session.events.sort(key=lambda event: event.line)
    return session if session.session_id else None


def reference_parse_session(path: Path, max_bytes: int | None = None) -> ReferenceSession | None:
    """Direct raw replay parser, intentionally separate from normalization."""

    session = ReferenceSession(path=path, session_id=path.stem)
    calls: dict[str, RawEvent] = {}
    output_by_call: dict[str, tuple[str, str]] = {}
    native_children: dict[str, str] = {}
    first_meta = True
    accepts_records = True
    born_at = 0.0
    for line_number, raw in snapshot_lines(path, max_bytes):
        head = raw[:512]
        if not relevant_line(raw):
            continue
        if '"type":"function_call_output"' in head and len(raw) > 1_000_000:
            cid, child, state = light_output(raw)
            if cid:
                output_by_call[cid] = (child, state)
            continue
        try:
            obj = json.loads(raw)
        except json.JSONDecodeError:
            session.parse_errors += 1
            continue
        body = obj.get("payload")
        if not isinstance(body, dict):
            body = {}
        outer = obj.get("type")
        inner = body.get("type")
        stamp = str(obj.get("timestamp") or "")
        if outer == "session_meta":
            if first_meta:
                first_meta = False
                session.session_id = str(body.get("id") or session.session_id)
                raw_source = body.get("source") if isinstance(body.get("source"), dict) else {}
                raw_subagent = (
                    raw_source.get("subagent")
                    if isinstance(raw_source.get("subagent"), dict)
                    else {}
                )
                raw_spawn = (
                    raw_subagent.get("thread_spawn")
                    if isinstance(raw_subagent.get("thread_spawn"), dict)
                    else {}
                )
                session.parent_id = str(
                    body.get("parent_thread_id")
                    or body.get("forked_from_id")
                    or raw_spawn.get("parent_thread_id")
                    or ""
                )
                session.thread_source = str(body.get("thread_source") or "")
                session.cwd = str(body.get("cwd") or "")
                session.depth = source_depth(body)
                born_at = timestamp_seconds(str(body.get("timestamp") or stamp))
                accepts_records = not bool(
                    session.parent_id or body.get("forked_from_id")
                )
                session.ownership_boundary_required = not accepts_records
                session.ownership_boundary_found = accepts_records
            continue
        if outer == "event_msg" and inner == "task_started":
            turn_start = float(body.get("started_at") or 0.0)
            legacy_start = reference_uuid7_seconds(str(body.get("turn_id") or ""))
            observed_start = turn_start or legacy_start
            cutoff = int(born_at) if turn_start else born_at
            if not accepts_records and observed_start and (
                born_at == 0.0 or observed_start >= cutoff
            ):
                accepts_records = True
                session.ownership_boundary_found = True
            continue
        if not accepts_records:
            session.copied_records_skipped += 1
            continue
        sid = f"{session.session_id}:line:{line_number}"
        if outer == "event_msg" and inner == "sub_agent_activity":
            activity_id = str(body.get("event_id") or "")
            activity_child = str(body.get("agent_thread_id") or "")
            if activity_id and activity_child and str(body.get("kind") or "") == "started":
                native_children[activity_id] = activity_child
            continue
        if outer == "event_msg" and inner == "user_message":
            session.events.append(RawEvent(line_number, stamp, "user", sid, text=str(body.get("message") or "")))
            continue
        if outer == "event_msg" and inner == "agent_message":
            session.events.append(
                RawEvent(
                    line_number,
                    stamp,
                    "agent",
                    sid,
                    text=str(body.get("message") or ""),
                    phase=str(body.get("phase") or ""),
                )
            )
            continue
        if outer == "event_msg" and inner == "token_count":
            information = body.get("info") if isinstance(body.get("info"), dict) else {}
            last = information.get("last_token_usage") if isinstance(information.get("last_token_usage"), dict) else {}
            session.events.append(
                RawEvent(
                    line_number,
                    stamp,
                    "llm",
                    sid,
                    input_tokens=int(last.get("input_tokens") or 0),
                    output_tokens=int(last.get("output_tokens") or 0),
                )
            )
            continue
        if outer == "response_item" and inner == "message" and body.get("role") == "user":
            session.events.append(
                RawEvent(
                    line_number,
                    stamp,
                    "user",
                    sid,
                    text=reference_message_text(body),
                )
            )
            continue
        if outer == "response_item" and inner == "function_call":
            parsed_args = parse_json_value(body.get("arguments"))
            tool_name = str(body.get("name") or "tool")
            cid = str(body.get("call_id") or f"line-{line_number}")
            event_kind = "plan" if tool_name == "update_plan" else "spawn" if tool_name == "spawn_agent" else "tool"
            event = RawEvent(
                line_number,
                stamp,
                event_kind,
                sid,
                name=tool_name,
                call_id=cid,
                args=parsed_args,
                plan=normalize_plan(parsed_args) if event_kind == "plan" else [],
                text=str(parsed_args.get("message") or "") if event_kind == "spawn" else "",
            )
            session.events.append(event)
            calls[cid] = event
            continue
        if outer == "response_item" and inner == "function_call_output":
            cid = str(body.get("call_id") or "")
            value = body.get("output")
            out = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False)
            child = CHILD_ID_RE.search(out[:16_000])
            state = tool_output_status(out[:16_000])
            if cid:
                output_by_call[cid] = (child.group(1) if child else "", state)
    for cid, event in calls.items():
        child_id, event.result = output_by_call.get(cid, ("", "observed"))
        event.child_id = child_id or native_children.get(cid, "")
    session.events.sort(key=lambda item: item.line)
    return session if session.session_id else None


def operation_suffix(name: str, args: dict[str, Any], context: str, phase_hint: str, result: str) -> tuple[str, str, str, str]:
    lowered_name = name.lower()
    command = command_text(args.get("cmd") or args.get("command"))
    lowered_command = command.lower()
    if lowered_name == "update_plan":
        phase = "Plan work"
        action = "Update task plan"
        obj = "Task plan"
    elif lowered_name == "spawn_agent":
        phase = "Coordinate work"
        action = "Delegate subtask"
        obj = task_label(str(args.get("message") or "Delegated task"), 80)
    elif "web" in lowered_name:
        phase = "Collect evidence"
        action = "Search or open source"
        obj = task_label(json.dumps(args, ensure_ascii=False), 80)
    elif lowered_name == "apply_patch" or lowered_name in {"edit", "write", "multiedit"}:
        phase = "Implement change"
        action = "Edit artifact"
        match = re.search(r"\*\*\* (?:Add|Update|Delete) File: ([^\n]+)", str(args))
        obj = compact_space(match.group(1), 80) if match else "Repository artifact"
    elif "test" in lowered_command or "pytest" in lowered_command or "cargo test" in lowered_command:
        phase = "Validate result"
        action = "Run tests"
        obj = compact_space(command, 80)
    elif lowered_name.endswith("exec_command") or lowered_name in {"exec_command", "bash", "shell"}:
        if re.search(r"(^|\s)(rg|sed|head|tail|jq|find|ls)(\s|$)", lowered_command):
            phase = "Inspect evidence"
            action = "Read or search"
        elif lowered_command.startswith("git "):
            phase = "Record progress"
            action = "Update repository"
        else:
            phase = "Execute work"
            action = "Run command"
        file_match = FILE_RE.search(command)
        obj = compact_space(file_match.group(1), 80) if file_match else compact_space(command, 80) or "Shell environment"
    elif lowered_name == "llm":
        phase = "Communicate result" if phase_hint == "final_answer" else "Reason about task"
        action = "Report conclusion" if phase_hint == "final_answer" else "Explain progress"
        obj = "Current task"
    else:
        phase = "Execute work"
        action = compact_space(name.replace("_", " ").title(), 80)
        obj = task_label(json.dumps(args, ensure_ascii=False), 80) if args else "Tool request"
    if lowered_name == "llm":
        result_label = task_label(context, 120) if context else "No source-visible conclusion"
    else:
        result_label = (
            "Call failed"
            if result == "error"
            else "Call completed"
            if result == "success"
            else "No source-visible semantic result"
        )
    return phase, action, obj, result_label


def active_plan_frame(
    session_id: str,
    event_source: str,
    plan: list[dict[str, str]],
    registry: dict[tuple[str, int], Frame],
) -> tuple[Frame | None, bool, list[Frame]]:
    seen: Counter[str] = Counter()
    in_progress: list[Frame] = []
    completed: list[Frame] = []
    for index, item in enumerate(plan):
        raw_step = item.get("step", "")
        ordinal = seen[raw_step]
        seen[raw_step] += 1
        key = (raw_step, ordinal)
        frame = registry.get(key)
        if frame is None:
            frame = Frame(
                source_id=f"plan:{session_id}:{event_source}:item:{index}",
                kind="subtask",
                label=task_label(raw_step),
            )
            registry[key] = frame
        status = item.get("status", "")
        if status == "in_progress":
            in_progress.append(frame)
        elif status == "completed":
            completed.append(frame)
    return (in_progress[0] if len(in_progress) == 1 else None, len(in_progress) > 1, completed)


def root_id_map(sessions: dict[str, Any]) -> dict[str, str]:
    roots: dict[str, str] = {}
    for sid in sessions:
        seen: set[str] = set()
        current = sid
        while current in sessions and sessions[current].parent_id and current not in seen:
            seen.add(current)
            current = sessions[current].parent_id
        roots[sid] = current
    return roots


def exact_spawn_links(sessions: dict[str, Any]) -> tuple[dict[str, tuple[str, Any]], list[str]]:
    candidates: defaultdict[str, list[tuple[str, Any]]] = defaultdict(list)
    for parent_id, session in sessions.items():
        for event in session.events:
            if event.kind == "spawn" and event.child_id:
                candidates[event.child_id].append((parent_id, event))
    links: dict[str, tuple[str, Any]] = {}
    unresolved: list[str] = []
    for child_id, session in sessions.items():
        if not session.parent_id:
            continue
        rows = [row for row in candidates.get(child_id, []) if row[0] == session.parent_id]
        if len(rows) == 1:
            links[child_id] = rows[0]
        else:
            unresolved.append(child_id)
    return links, sorted(unresolved)


def reference_spawn_links(
    sessions: dict[str, ReferenceSession],
) -> tuple[dict[str, tuple[str, RawEvent]], list[str]]:
    """Resolve reference links directly from each child's declared parent."""

    linked: dict[str, tuple[str, RawEvent]] = {}
    missing: list[str] = []
    for child_id, child in sessions.items():
        if not child.parent_id:
            continue
        parent = sessions.get(child.parent_id)
        matches = [] if parent is None else [
            event
            for event in parent.events
            if event.kind == "spawn" and event.child_id == child_id
        ]
        if len(matches) == 1:
            linked[child_id] = (child.parent_id, matches[0])
        else:
            missing.append(child_id)
    return linked, sorted(missing)


def reference_plan_frame(
    session_id: str,
    source_call: str,
    rows: list[dict[str, str]],
    identities: dict[tuple[str, int], Frame],
) -> tuple[Frame | None, bool, list[Frame]]:
    """Replay reference plan state without using the candidate transition helper."""

    duplicate_index: Counter[str] = Counter()
    running: list[Frame] = []
    finished: list[Frame] = []
    for position, row in enumerate(rows):
        label = row.get("step", "")
        occurrence = duplicate_index[label]
        duplicate_index[label] += 1
        identity = (label, occurrence)
        frame = identities.get(identity)
        if frame is None:
            frame = Frame(
                f"plan:{session_id}:{source_call}:item:{position}",
                "subtask",
                task_label(label),
            )
            identities[identity] = frame
        state = row.get("status", "")
        if state == "in_progress":
            running.append(frame)
        if state == "completed":
            finished.append(frame)
    active = running[0] if len(running) == 1 else None
    return active, len(running) > 1, finished


def candidate_replay(sessions: dict[str, CandidateSession]) -> ReplayResult:
    result = ReplayResult()
    links, unresolved = exact_spawn_links(sessions)
    result.unresolved_parent_links.extend(unresolved)
    roots = root_id_map(sessions)
    result.root_by_session.update(roots)
    children: defaultdict[str, list[str]] = defaultdict(list)
    for child, (parent, _) in links.items():
        children[parent].append(child)
    visited: set[str] = set()

    def run(sid: str, inherited: tuple[Frame, ...] = ()) -> None:
        if sid in visited or sid not in sessions:
            return
        visited.add(sid)
        session = sessions[sid]
        path = list(inherited)
        plan_frame: Frame | None = None
        plan_registry: dict[tuple[str, int], Frame] = {}
        last_context = ""
        last_phase = ""
        last_signature: tuple[tuple[str, ...], str, str, str] | None = None
        for event in session.events:
            if event.kind == "user" and not session.parent_id:
                path = [Frame(f"root:{sid}:user-line:{event.line}", "task", task_label(event.text))]
                plan_frame = None
                plan_registry = {}
                result.task_controls += 1
                result.session_controls[sid] += 1
                result.task_transitions.add(event.source_id)
                continue
            if event.kind == "agent":
                last_context = event.text
                last_phase = event.phase
                if event.phase == "final_answer" and session.parent_id:
                    completion_id = f"{sid}:completion:child-final"
                    if completion_id not in result.completion_transitions:
                        result.completion_transitions.add(completion_id)
                        result.task_outcomes["source_declared_completion"] += 1
                        result.session_completions[sid] += 1
                continue
            if event.kind == "plan":
                plan_frame, conflict, completed = active_plan_frame(
                    sid, event.call_id or event.source_id, event.plan, plan_registry
                )
                if conflict:
                    result.plan_conflicts += 1
                    result.session_plan_conflicts[sid] += 1
                    result.plan_conflict_sources.append(event.source_id)
                for frame in completed:
                    completion_id = f"{sid}:completion:{frame.source_id}"
                    if completion_id in result.completion_transitions:
                        continue
                    result.completion_transitions.add(completion_id)
                    result.task_outcomes["source_declared_completion"] += 1
                    result.session_completions[sid] += 1
                result.task_controls += 1
                result.session_controls[sid] += 1
                result.session_structural_controls[sid] += 1
                result.task_transitions.add(event.source_id)
            task_path = tuple(path + ([plan_frame] if plan_frame else []))
            if event.kind == "spawn":
                result.task_controls += 1
                result.session_controls[sid] += 1
                result.session_structural_controls[sid] += 1
                result.task_transitions.add(event.source_id)
                if event.child_id and event.child_id in links and links[event.child_id][0] == sid:
                    delegate = Frame(
                        f"delegate:{event.call_id}:child:{event.child_id}",
                        "subtask",
                        task_label(event.text),
                    )
                    result.spawn_snapshots[event.child_id] = task_path + (delegate,)
                    result.spawn_sources[event.child_id] = event.source_id
            if event.kind not in {"plan", "spawn", "tool", "llm"}:
                continue
            if not task_path:
                result.unresolved_operations += 1
                result.session_unresolved_operations[sid] += 1
                result.unresolved_operation_sources.append(event.source_id)
                continue
            if event.kind == "llm":
                phase, action, obj, outcome = operation_suffix("llm", {}, last_context, last_phase, "observed")
                op_id = f"{sid}:llm-line:{event.line}"
                token_weight = event.input_tokens + event.output_tokens
            else:
                phase, action, obj, outcome = operation_suffix(
                    event.name, event.args, last_context, last_phase, event.result
                )
                op_id = f"{sid}:tool-call:{event.call_id}"
                token_weight = 0
            signature = (tuple(frame.source_id for frame in task_path), action, obj, outcome)
            if last_signature == signature:
                outcome = f"Repeated: {outcome}"
            last_signature = signature
            result.operations.append(
                OperationPath(
                    op_id,
                    sid,
                    event.line,
                    event.timestamp,
                    tuple(frame.source_id for frame in task_path),
                    tuple(frame.label for frame in task_path),
                    event.kind,
                    phase,
                    action,
                    obj,
                    outcome,
                    1,
                    token_weight,
                )
            )
        for child in sorted(children.get(sid, [])):
            snapshot = result.spawn_snapshots.get(child)
            if snapshot:
                run(child, snapshot)

    for sid, session in sorted(sessions.items()):
        if not session.parent_id:
            run(sid)
    for sid in sorted(set(sessions) - visited):
        if sid not in unresolved:
            run(sid)
    return result


def reference_replay(sessions: dict[str, ReferenceSession]) -> ReplayResult:
    """Direct raw-event state replay, independent of candidate normalization."""

    replay = ReplayResult()
    linked, broken = reference_spawn_links(sessions)
    replay.unresolved_parent_links.extend(broken)
    replay.root_by_session.update(root_id_map(sessions))
    child_table: defaultdict[str, list[str]] = defaultdict(list)
    for child_id, pair in linked.items():
        child_table[pair[0]].append(child_id)
    done: set[str] = set()

    def consume(session_id: str, inherited_frames: tuple[Frame, ...]) -> None:
        if session_id in done or session_id not in sessions:
            return
        done.add(session_id)
        source = sessions[session_id]
        base_frames = list(inherited_frames)
        current_plan: Frame | None = None
        known_plan_items: dict[tuple[str, int], Frame] = {}
        recent_text = ""
        recent_phase = ""
        previous: tuple[tuple[str, ...], str, str, str] | None = None
        for raw in source.events:
            if raw.kind == "user" and source.parent_id == "":
                base_frames = [
                    Frame(
                        f"root:{session_id}:user-line:{raw.line}",
                        "task",
                        task_label(raw.text),
                    )
                ]
                current_plan = None
                known_plan_items = {}
                replay.task_controls += 1
                replay.session_controls[session_id] += 1
                replay.task_transitions.add(raw.source_id)
                continue
            if raw.kind == "agent":
                recent_text = raw.text
                recent_phase = raw.phase
                if raw.phase == "final_answer" and source.parent_id:
                    completion_key = f"{session_id}:completion:child-final"
                    if completion_key not in replay.completion_transitions:
                        replay.completion_transitions.add(completion_key)
                        replay.task_outcomes["source_declared_completion"] += 1
                        replay.session_completions[session_id] += 1
                continue
            if raw.kind == "plan":
                current_plan, conflict, finished = reference_plan_frame(
                    session_id,
                    raw.call_id or raw.source_id,
                    raw.plan,
                    known_plan_items,
                )
                replay.plan_conflicts += int(conflict)
                replay.session_plan_conflicts[session_id] += int(conflict)
                if conflict:
                    replay.plan_conflict_sources.append(raw.source_id)
                for frame in finished:
                    completion_key = f"{session_id}:completion:{frame.source_id}"
                    if completion_key in replay.completion_transitions:
                        continue
                    replay.completion_transitions.add(completion_key)
                    replay.task_outcomes["source_declared_completion"] += 1
                    replay.session_completions[session_id] += 1
                replay.task_controls += 1
                replay.session_controls[session_id] += 1
                replay.session_structural_controls[session_id] += 1
                replay.task_transitions.add(raw.source_id)
            active = tuple(base_frames + ([current_plan] if current_plan is not None else []))
            if raw.kind == "spawn":
                replay.task_controls += 1
                replay.session_controls[session_id] += 1
                replay.session_structural_controls[session_id] += 1
                replay.task_transitions.add(raw.source_id)
                if raw.child_id in linked and linked[raw.child_id][0] == session_id:
                    delegated = Frame(
                        f"delegate:{raw.call_id}:child:{raw.child_id}",
                        "subtask",
                        task_label(raw.text),
                    )
                    replay.spawn_snapshots[raw.child_id] = active + (delegated,)
                    replay.spawn_sources[raw.child_id] = raw.source_id
            if raw.kind not in ("plan", "spawn", "tool", "llm"):
                continue
            if len(active) == 0:
                replay.unresolved_operations += 1
                replay.session_unresolved_operations[session_id] += 1
                replay.unresolved_operation_sources.append(raw.source_id)
                continue
            if raw.kind == "llm":
                p, a, o, r = operation_suffix("llm", {}, recent_text, recent_phase, "observed")
                oid = f"{session_id}:llm-line:{raw.line}"
                weight = raw.input_tokens + raw.output_tokens
            else:
                p, a, o, r = operation_suffix(raw.name, raw.args, recent_text, recent_phase, raw.result)
                oid = f"{session_id}:tool-call:{raw.call_id}"
                weight = 0
            sig = (tuple(item.source_id for item in active), a, o, r)
            if previous == sig:
                r = f"Repeated: {r}"
            previous = sig
            replay.operations.append(
                OperationPath(
                    oid,
                    session_id,
                    raw.line,
                    raw.timestamp,
                    tuple(item.source_id for item in active),
                    tuple(item.label for item in active),
                    raw.kind,
                    p,
                    a,
                    o,
                    r,
                    1,
                    weight,
                )
            )
        for child_session in sorted(child_table.get(session_id, [])):
            inherited = replay.spawn_snapshots.get(child_session)
            if inherited is not None:
                consume(child_session, inherited)

    for key, value in sorted(sessions.items()):
        if value.parent_id == "":
            consume(key, ())
    for key in sorted(set(sessions) - done):
        if key not in broken:
            consume(key, ())
    return replay


def eligible_roots(sessions: dict[str, Any], replay: ReplayResult) -> list[str]:
    controls_by_root: Counter[str] = Counter()
    for sid, count in replay.session_structural_controls.items():
        controls_by_root[replay.root_by_session.get(sid, sid)] += count
    child_by_root: Counter[str] = Counter()
    for sid, session in sessions.items():
        if session.parent_id:
            child_by_root[replay.root_by_session.get(sid, sid)] += 1
    return sorted(root for root in set(controls_by_root) | set(child_by_root) if controls_by_root[root] or child_by_root[root])


def filter_replay(replay: ReplayResult, roots: set[str]) -> ReplayResult:
    filtered = ReplayResult()
    filtered.operations = [
        op for op in replay.operations if replay.root_by_session.get(op.session_id, op.session_id) in roots
    ]
    sessions = {
        sid for sid, root in replay.root_by_session.items() if root in roots
    }
    filtered.task_controls = sum(replay.session_controls[sid] for sid in sessions)
    filtered.task_transitions = {
        transition for transition in replay.task_transitions if transition.split(":line:", 1)[0] in sessions
    }
    filtered.spawn_snapshots = {key: value for key, value in replay.spawn_snapshots.items() if key in sessions}
    filtered.spawn_sources = {key: value for key, value in replay.spawn_sources.items() if key in sessions}
    filtered.unresolved_parent_links = [sid for sid in replay.unresolved_parent_links if replay.root_by_session.get(sid, sid) in roots]
    filtered.unresolved_operations = sum(replay.session_unresolved_operations[sid] for sid in sessions)
    filtered.unresolved_operation_sources = [
        source
        for source in replay.unresolved_operation_sources
        if source.split(":line:", 1)[0] in sessions
    ]
    filtered.plan_conflicts = sum(replay.session_plan_conflicts[sid] for sid in sessions)
    filtered.plan_conflict_sources = [
        source
        for source in replay.plan_conflict_sources
        if source.split(":line:", 1)[0] in sessions
    ]
    filtered.task_outcomes["source_declared_completion"] = sum(
        replay.session_completions[sid] for sid in sessions
    )
    filtered.root_by_session = replay.root_by_session.copy()
    filtered.session_controls = Counter({sid: count for sid, count in replay.session_controls.items() if sid in sessions})
    filtered.session_structural_controls = Counter(
        {sid: count for sid, count in replay.session_structural_controls.items() if sid in sessions}
    )
    filtered.session_unresolved_operations = Counter(
        {sid: count for sid, count in replay.session_unresolved_operations.items() if sid in sessions}
    )
    filtered.session_plan_conflicts = Counter(
        {sid: count for sid, count in replay.session_plan_conflicts.items() if sid in sessions}
    )
    filtered.session_completions = Counter(
        {sid: count for sid, count in replay.session_completions.items() if sid in sessions}
    )
    filtered.completion_transitions = {
        transition
        for transition in replay.completion_transitions
        if transition.split(":completion:", 1)[0] in sessions
    }
    return filtered


def score(candidate: ReplayResult, reference: ReplayResult) -> dict[str, Any]:
    cand = {op.operation_id: op for op in candidate.operations}
    ref = {op.operation_id: op for op in reference.operations}
    matched = sum(
        1
        for op_id, expected in ref.items()
        if op_id in cand and cand[op_id].task_ids == expected.task_ids
    )
    missing = sorted(set(ref) - set(cand))
    extra = sorted(set(cand) - set(ref))
    mismatched = sorted(
        op_id for op_id in set(ref) & set(cand) if ref[op_id].task_ids != cand[op_id].task_ids
    )
    tp = len(candidate.task_transitions & reference.task_transitions)
    fp = len(candidate.task_transitions - reference.task_transitions)
    fn = len(reference.task_transitions - candidate.task_transitions)
    precision = tp / (tp + fp) if tp + fp else 1.0
    recall = tp / (tp + fn) if tp + fn else 1.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    cand_events = sum(op.event_weight for op in candidate.operations)
    ref_events = sum(op.event_weight for op in reference.operations)
    cand_tokens = sum(op.token_weight for op in candidate.operations)
    ref_tokens = sum(op.token_weight for op in reference.operations)
    return {
        "primary": {
            "metric": "operation-level exact-path accuracy",
            "matched": matched,
            "reference_operations": len(ref),
            "accuracy": matched / len(ref) if ref else 0.0,
        },
        "operation_alignment": {
            "candidate_operations": len(cand),
            "reference_operations": len(ref),
            "missing_candidate": len(missing),
            "extra_candidate": len(extra),
            "path_mismatch": len(mismatched),
            "missing_examples": missing[:20],
            "extra_examples": extra[:20],
            "mismatch_examples": mismatched[:20],
        },
        "task_transition": {
            "true_positive": tp,
            "false_positive": fp,
            "false_negative": fn,
            "precision": precision,
            "recall": recall,
            "f1": f1,
        },
        "resource_conservation": {
            "candidate_event_weight": cand_events,
            "reference_event_weight": ref_events,
            "event_exact": cand_events == ref_events,
            "candidate_token_weight": cand_tokens,
            "reference_token_weight": ref_tokens,
            "token_exact": cand_tokens == ref_tokens,
        },
    }


def summarize_structure(operations: list[OperationPath]) -> dict[str, Any]:
    depths = Counter(len(op.task_ids) for op in operations)
    delegate_ids = {
        frame
        for op in operations
        for frame in op.task_ids
        if frame.startswith("delegate:")
    }
    root_ids = {
        frame for op in operations for frame in op.task_ids if frame.startswith("root:")
    }
    plan_ids = {
        frame for op in operations for frame in op.task_ids if frame.startswith("plan:")
    }
    delegate_operations = sum(
        any(frame.startswith("delegate:") for frame in op.task_ids)
        for op in operations
    )
    total = len(operations)
    return {
        "operations": total,
        "depth_counts": {str(depth): count for depth, count in sorted(depths.items())},
        "depth_percent": {
            str(depth): count / total if total else 0.0
            for depth, count in sorted(depths.items())
        },
        "delegate_operations": delegate_operations,
        "delegate_operation_fraction": delegate_operations / total if total else 0.0,
        "unique_delegate_frames": len(delegate_ids),
        "unique_root_occurrences": len(root_ids),
        "unique_plan_frames": len(plan_ids),
    }


def operation_id(session_id: str, event: Any) -> str:
    if event.kind == "llm":
        return f"{session_id}:llm-line:{event.line}"
    return f"{session_id}:tool-call:{event.call_id}"


def source_coverage(
    sessions: dict[str, ReferenceSession],
    replay: ReplayResult,
    roots: set[str],
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Account for owned source operations before task-path construction."""

    session_ids = sorted(
        sid for sid in sessions if replay.root_by_session.get(sid, sid) in roots
    )
    resolved_ids = [
        sid
        for sid in session_ids
        if not sessions[sid].ownership_boundary_required
        or sessions[sid].ownership_boundary_found
    ]
    missing_boundaries = [
        {
            "session_id": sid,
            "path": str(sessions[sid].path),
            "parent_id": sessions[sid].parent_id,
        }
        for sid in session_ids
        if sessions[sid].ownership_boundary_required
        and not sessions[sid].ownership_boundary_found
    ]
    parse_errors = [
        {
            "session_id": sid,
            "path": str(sessions[sid].path),
            "count": sessions[sid].parse_errors,
        }
        for sid in session_ids
        if sessions[sid].parse_errors
    ]

    raw_rows: list[dict[str, Any]] = []
    for sid in resolved_ids:
        for event in sessions[sid].events:
            if event.kind not in {"plan", "spawn", "tool", "llm"}:
                continue
            raw_rows.append(
                {
                    "operation_id": operation_id(sid, event),
                    "source_id": event.source_id,
                    "session_id": sid,
                    "kind": event.kind,
                }
            )
    raw_by_id = {row["operation_id"]: row for row in raw_rows}
    raw_duplicates = sorted(
        operation_id
        for operation_id, count in Counter(row["operation_id"] for row in raw_rows).items()
        if count > 1
    )
    scored_ids = {op.operation_id for op in replay.operations}
    raw_ids = set(raw_by_id)
    missing_ids = sorted(raw_ids - scored_ids)
    extra_ids = sorted(scored_ids - raw_ids)
    missing_rows = [raw_by_id[item] for item in missing_ids]
    missing_by_session = Counter(row["session_id"] for row in missing_rows)
    by_kind = Counter(row["kind"] for row in raw_rows)

    coverage = {
        "scope": "eligible root families; ownership-resolved source sessions; before task-path construction",
        "eligible_sessions": len(session_ids),
        "ownership_resolved_sessions": len(resolved_ids),
        "ownership_missing_sessions": len(missing_boundaries),
        "raw_owned_operations": len(raw_ids),
        "scored_operations": len(scored_ids & raw_ids),
        "operation_coverage": len(scored_ids & raw_ids) / len(raw_ids) if raw_ids else 1.0,
        "unscored_raw_operations": len(missing_ids),
        "scored_without_raw_source": len(extra_ids),
        "raw_owned_operations_by_kind": dict(sorted(by_kind.items())),
        "duplicate_raw_operation_ids": len(raw_duplicates),
        "parse_error_records": sum(item["count"] for item in parse_errors),
        "parse_error_sessions": len(parse_errors),
    }
    exceptions = {
        "ownership_missing_sessions": missing_boundaries,
        "parse_errors": parse_errors,
        "unscored_raw_operations": missing_rows,
        "unscored_raw_operations_by_session": dict(sorted(missing_by_session.items())),
        "scored_without_raw_source": extra_ids,
        "duplicate_raw_operation_ids": raw_duplicates,
        "unresolved_parent_session_ids": sorted(replay.unresolved_parent_links),
        "unresolved_operation_source_ids": sorted(set(replay.unresolved_operation_sources)),
        "plan_conflict_source_ids": sorted(set(replay.plan_conflict_sources)),
    }
    return coverage, exceptions


def pprof_operation_record(op: OperationPath) -> dict[str, Any]:
    """Return one normalized record for AgentPProf's standard pprof writer.

    Repeated values of the ``task`` field preserve the variable-depth task path
    in source order. System metadata stays out of the responsibility stack.
    """

    return {
        "value": op.event_weight,
        "fields": {
            "task": list(op.task_labels),
            "phase": op.phase,
            "action": op.action,
            "object": op.object,
            "result": op.result,
            "source_kind": op.operation_kind,
            "evidence_id": hashlib.sha256(op.operation_id.encode()).hexdigest()[:16],
        },
    }


def largest_nested_task_path(operations: list[OperationPath]) -> tuple[tuple[str, ...], list[OperationPath]]:
    """Prefer a delegated/deep path, then choose deterministically by size."""

    all_counts = Counter(op.task_ids for op in operations)
    tiers = (
        [path for path in all_counts if any(frame.startswith("delegate:") for frame in path)],
        [path for path in all_counts if len(path) >= 3],
        [path for path in all_counts if len(path) > 1],
        list(all_counts),
    )
    counts = Counter()
    for paths in tiers:
        if paths:
            counts = Counter({path: all_counts[path] for path in paths})
            break
    if not counts:
        return (), []
    selected = sorted(counts, key=lambda path: (-counts[path], path))[0]
    return selected, [op for op in operations if op.task_ids == selected]


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n")


def report_markdown(
    mode: str,
    population: dict[str, Any],
    metrics: dict[str, Any],
    coverage: dict[str, Any],
    candidate: ReplayResult,
    selected_root: str,
) -> str:
    primary = metrics["primary"]
    alignment = metrics["operation_alignment"]
    transition = metrics["task_transition"]
    conservation = metrics["resource_conservation"]
    return f"""# Source-Native Task Stack — {mode.title()} Report

## Result

- selected root: `{selected_root or 'complete eligible population'}`
- eligible root families: {population['eligible_root_families']:,}
- included sessions: {population['included_sessions']:,}
- included operations: {primary['reference_operations']:,}
- pre-construction operation coverage: {coverage['scored_operations']:,} / {coverage['raw_owned_operations']:,} ({coverage['operation_coverage']:.6f})
- exact task-path accuracy: {primary['accuracy']:.6f}
- task-transition precision/recall/F1: {transition['precision']:.6f} / {transition['recall']:.6f} / {transition['f1']:.6f}
- event weight conserved: `{conservation['event_exact']}`
- token weight conserved: `{conservation['token_exact']}`
- unresolved parent links: {len(candidate.unresolved_parent_links):,}
- unresolved operations: {candidate.unresolved_operations:,}
- plan conflicts: {candidate.plan_conflicts:,}

## Population

- discovered JSONL files: {population['discovered_files']:,}
- parsed candidate sessions: {population['candidate_sessions']:,}
- parsed reference sessions: {population['reference_sessions']:,}
- candidate/reference parse errors: {population['candidate_parse_errors']:,} / {population['reference_parse_errors']:,}
- candidate/reference child-fork ownership boundaries found: {population['ownership_boundaries_found']:,} / {population['ownership_boundaries_required']:,} and {population['reference_ownership_boundaries_found']:,} / {population['reference_ownership_boundaries_required']:,}
- eligible ownership-resolved/missing sessions: {coverage['ownership_resolved_sessions']:,} / {coverage['ownership_missing_sessions']:,}
- candidate/reference copied-context records excluded: {population['copied_context_records_skipped']:,} / {population['reference_copied_context_records_skipped']:,}
- raw bytes: {population['raw_bytes']:,}
- explicit task controls: {candidate.task_controls:,}
- maximum visible task depth: {population['max_task_depth']:,}

## Source-Fidelity Checks

- missing candidate operations: {alignment['missing_candidate']:,}
- extra candidate operations: {alignment['extra_candidate']:,}
- mismatched task paths: {alignment['path_mismatch']:,}
- source-declared completions observed: {candidate.task_outcomes.get('source_declared_completion', 0):,}

The candidate consumes normalized events. The reference independently replays
raw user-task, plan, spawn-result, child-session, and completion records. Task
identity uses raw source coordinates; display cleanup is excluded from scoring.

## Interpretation

This is supporting source-fidelity evidence. It validates the task hierarchy
that Codex explicitly declared and maintained. It does not claim that this is
an ideal human decomposition, infer missing task controls, canonicalize
paraphrases across unrelated runs, or complete all of RQ3.
"""


def parse_all(paths: list[Path], parser: Any, byte_limits: dict[Path, int]) -> dict[str, Any]:
    sessions: dict[str, Any] = {}
    for index, path in enumerate(paths, 1):
        session = parser(path, byte_limits[path])
        if session is not None:
            sessions[session.session_id] = session
        if index % 500 == 0:
            print(f"parsed {index}/{len(paths)} files with {parser.__name__}", file=sys.stderr, flush=True)
    return sessions


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sessions-root", type=Path, default=DEFAULT_SESSIONS)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--mode", choices=("preflight", "full"), default="full")
    parser.add_argument("--root-session", default="")
    args = parser.parse_args()

    paths = sorted(path for path in args.sessions_root.rglob("*.jsonl") if path.is_file())
    if not paths:
        raise SystemExit(f"no JSONL sessions below {args.sessions_root}")
    byte_limits = {path: path.stat().st_size for path in paths}
    candidate_sessions = parse_all(paths, candidate_parse_session, byte_limits)
    reference_sessions = parse_all(paths, reference_parse_session, byte_limits)
    candidate = candidate_replay(candidate_sessions)
    reference = reference_replay(reference_sessions)
    roots = eligible_roots(reference_sessions, reference)
    if not roots:
        raise SystemExit("no eligible root session family")
    selected = args.root_session or roots[0]
    if args.mode == "preflight":
        if selected not in roots:
            raise SystemExit(f"root session is not eligible: {selected}")
        included_roots = {selected}
    else:
        included_roots = set(roots)
        selected = ""
    candidate = filter_replay(candidate, included_roots)
    reference = filter_replay(reference, included_roots)
    metrics = score(candidate, reference)
    structure = summarize_structure(candidate.operations)
    coverage, exceptions = source_coverage(reference_sessions, reference, included_roots)

    session_ids = {op.session_id for op in reference.operations}
    max_depth = max((len(op.task_ids) for op in reference.operations), default=0)
    population = {
        "mode": args.mode,
        "sessions_root": str(args.sessions_root),
        "discovered_files": len(paths),
        "raw_bytes": sum(byte_limits.values()),
        "candidate_sessions": len(candidate_sessions),
        "reference_sessions": len(reference_sessions),
        "candidate_parse_errors": sum(session.parse_errors for session in candidate_sessions.values()),
        "reference_parse_errors": sum(session.parse_errors for session in reference_sessions.values()),
        "ownership_boundaries_required": sum(
            session.ownership_boundary_required for session in candidate_sessions.values()
        ),
        "ownership_boundaries_found": sum(
            session.ownership_boundary_found
            for session in candidate_sessions.values()
            if session.ownership_boundary_required
        ),
        "copied_context_records_skipped": sum(
            session.copied_records_skipped for session in candidate_sessions.values()
        ),
        "reference_ownership_boundaries_required": sum(
            session.ownership_boundary_required for session in reference_sessions.values()
        ),
        "reference_ownership_boundaries_found": sum(
            session.ownership_boundary_found
            for session in reference_sessions.values()
            if session.ownership_boundary_required
        ),
        "reference_copied_context_records_skipped": sum(
            session.copied_records_skipped for session in reference_sessions.values()
        ),
        "eligible_root_families": len(roots),
        "included_root_families": len(included_roots),
        "included_sessions": len(session_ids),
        "max_task_depth": max_depth,
        "selected_root": selected,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    output = args.output / args.mode
    write_json(output / "population.json", population)
    write_json(output / "metrics.json", metrics)
    write_json(output / "structure-summary.json", structure)
    write_json(output / "coverage.json", coverage)
    write_json(output / "exceptions.json", exceptions)
    write_jsonl(output / "candidate-operations.jsonl", (op.json() for op in candidate.operations))
    write_jsonl(output / "reference-operations.jsonl", (op.json() for op in reference.operations))
    write_json(
        output / "controls.json",
        {
            "task_controls": candidate.task_controls,
            "session_controls": candidate.session_controls,
            "unresolved_parent_links": candidate.unresolved_parent_links,
            "unresolved_operations": candidate.unresolved_operations,
            "unresolved_operation_sources": candidate.unresolved_operation_sources,
            "plan_conflicts": candidate.plan_conflicts,
            "plan_conflict_sources": candidate.plan_conflict_sources,
            "task_outcomes": candidate.task_outcomes,
        },
    )
    report = report_markdown(args.mode, population, metrics, coverage, candidate, selected)
    (output / "report.md").write_text(report, encoding="utf-8")

    profile_ops = candidate.operations
    selected_profile_root = selected
    if args.mode == "full":
        controls_by_root: Counter[str] = Counter()
        for sid, count in candidate.session_structural_controls.items():
            controls_by_root[candidate.root_by_session.get(sid, sid)] += count
        selected_profile_root = sorted(roots, key=lambda root: (-controls_by_root[root], root))[0]
        profile_ops = [
            op
            for op in candidate.operations
            if candidate.root_by_session.get(op.session_id, op.session_id) == selected_profile_root
        ]
    write_json(
        output / "profile-selection.json",
        {
            "rule": "eligible root family with most explicit task-control transitions; lexicographic tie-break"
            if args.mode == "full"
            else "explicit preflight root",
            "root_session": selected_profile_root,
            "task_controls": candidate.session_structural_controls.get(selected_profile_root, 0)
            if args.mode == "preflight"
            else controls_by_root[selected_profile_root],
            "operations": len(profile_ops),
            "stack": ["task", "phase", "action", "object", "result"],
            "product_output": "standard pprof only",
        },
    )
    write_jsonl(
        output / "pprof-operations.jsonl",
        (pprof_operation_record(op) for op in profile_ops),
    )
    if args.mode == "full":
        zoom_path, zoom_ops = largest_nested_task_path(profile_ops)
        if zoom_ops:
            write_json(
                output / "zoom-selection.json",
                {
                    "rule": "prefer an exact delegated path, then depth >= 3, then any non-root path; within the first nonempty tier choose most operations with lexicographic tie-break",
                    "task_ids": list(zoom_path),
                    "task_labels": list(zoom_ops[0].task_labels),
                    "operations": len(zoom_ops),
                },
            )
    print(json.dumps({"population": population, "metrics": metrics}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
