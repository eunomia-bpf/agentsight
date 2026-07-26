#!/usr/bin/env python3
"""Read-only sizing inventory for local Codex and Claude Code sessions.

The scanner deliberately never emits paths, prompts, responses, commands, or
tool outputs. Session identities are one-way hashes of source-relative paths,
and project labels are reduced to coarse working-directory basenames.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
import sys
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path, PurePosixPath
from typing import Any, Iterable


OUTPUT_DIR = Path(__file__).resolve().parent
HOME = Path.home()
ROOTS = (
    ("codex", HOME / ".codex" / "sessions"),
    ("claude", HOME / ".claude" / "projects"),
)

# Step 0077 measured 7,229 source operations across 440 sessions.
REFERENCE_OPERATIONS_PER_SESSION = 7_229 / 440
REFERENCE_INPUT_TOKENS_PER_SESSION = 27_362
REFERENCE_WORKER_SECONDS_PER_SESSION = 15.14
RECENT_WEEKS = 8

JSON_STRING = rb'((?:\\.|[^"\\])*)'
TYPE_RE = re.compile(rb'"type"\s*:\s*"' + JSON_STRING + rb'"')
TIMESTAMP_RE = re.compile(rb'"timestamp"\s*:\s*"' + JSON_STRING + rb'"')
CWD_RE = re.compile(rb'"cwd"\s*:\s*"' + JSON_STRING + rb'"')
PAYLOAD_TYPE_RE = re.compile(
    rb'"payload"\s*:\s*\{\s*"type"\s*:\s*"' + JSON_STRING + rb'"'
)
RANDOM_LABEL_RE = re.compile(
    r"^(?:[0-9a-f]{12,}|[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}|tmp[\w.-]*)$",
    re.IGNORECASE,
)


def json_string(raw: bytes | None) -> str | None:
    if raw is None:
        return None
    try:
        return json.loads(b'"' + raw + b'"')
    except (json.JSONDecodeError, UnicodeDecodeError):
        return None


def first_match(pattern: re.Pattern[bytes], line: bytes) -> str:
    match = pattern.search(line)
    return json_string(match.group(1)) if match else ""


def outer_type(source: str, line: bytes) -> str:
    matches = list(TYPE_RE.finditer(line))
    if not matches:
        return ""
    # Codex writes the outer type before payload. Claude writes its top-level
    # type after message content, whose nested blocks may also have type keys.
    match = matches[0] if source == "codex" else matches[-1]
    return json_string(match.group(1)) or ""


def outer_timestamp(source: str, line: bytes) -> str | None:
    matches = list(TIMESTAMP_RE.finditer(line))
    if not matches:
        return None
    # Codex serializes the outer timestamp first; Claude serializes it after
    # message content, so its final unescaped timestamp is the outer field.
    match = matches[0] if source == "codex" else matches[-1]
    return json_string(match.group(1))


def parse_timestamp_ms(value: str | None) -> int | None:
    if not value:
        return None
    try:
        normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
        return int(datetime.fromisoformat(normalized).timestamp() * 1_000)
    except ValueError:
        return None


def normalized_utc(value: str | None) -> str | None:
    millis = parse_timestamp_ms(value)
    if millis is None:
        return None
    dt = datetime.fromtimestamp(millis / 1_000, tz=timezone.utc)
    return dt.isoformat(timespec="milliseconds").replace("+00:00", "Z")


def safe_int(value: Any) -> int:
    if isinstance(value, bool):
        return 0
    if isinstance(value, (int, float)) and value >= 0:
        return int(value)
    return 0


def stable_hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8", errors="replace")).hexdigest()


def content_to_text(value: Any) -> str:
    """Match agent-session's content_to_text closely enough for deduplication."""
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        parts: list[str] = []
        for item in value:
            if isinstance(item, str):
                parts.append(item)
                continue
            if not isinstance(item, dict):
                continue
            kind = item.get("type", "")
            if kind in {"tool_result", "tool_use", "function_call"}:
                continue
            if kind == "thinking":
                text = item.get("thinking")
            else:
                text = item.get("text", item.get("content"))
            if isinstance(text, str) and text:
                parts.append(text)
        return "\n".join(parts)
    if isinstance(value, dict):
        text = value.get("text", value.get("content", ""))
        return text if isinstance(text, str) else ""
    return ""


def collect_local_text(value: Any, output: list[str]) -> None:
    if isinstance(value, str):
        output.append(value)
    elif isinstance(value, list):
        for item in value:
            collect_local_text(item, output)
    elif isinstance(value, dict):
        if value.get("type") in {"tool_use", "function_call", "tool_result"}:
            return
        for key in ("text", "content", "message", "input", "prompt"):
            if key in value:
                collect_local_text(value[key], output)


def local_message_text(value: Any) -> str:
    parts: list[str] = []
    collect_local_text(value, parts)
    return " ".join(parts).strip()


def project_label(cwd: str | None) -> str:
    if not cwd:
        return "unknown"
    cleaned = cwd.rstrip("/")
    if not cleaned:
        return "root"
    if cleaned == str(HOME):
        return "home"
    if cleaned == "/tmp" or cleaned.startswith("/tmp/"):
        return "temporary"
    label = PurePosixPath(cleaned).name.strip()
    if not label:
        return "unknown"
    if label.startswith("."):
        label = label[1:] or "hidden"
    if RANDOM_LABEL_RE.fullmatch(label):
        return "ephemeral"
    # Basenames are the task-specified coarse granularity. Bound their length
    # so generated worktree names cannot turn into detailed path disclosures.
    return label[:80]


def duration_bucket(seconds: float) -> str:
    if seconds < 10 * 60:
        return "<10 min"
    if seconds < 60 * 60:
        return "10-60 min"
    if seconds <= 6 * 60 * 60:
        return "1-6 h"
    return ">6 h"


@dataclass
class ScanState:
    source: str
    session_key: str
    project: str = "unknown"
    cwd: str | None = None
    start_raw: str | None = None
    end_raw: str | None = None
    user_prompts: int = 0
    llm_calls: int = 0
    tool_calls: int = 0
    provider_tokens: int | None = None
    bytes_read: int = 0
    lines_read: int = 0
    decode_errors: int = 0
    fallback_duration_ms: int = 0
    prompt_seen: dict[str, int | None] = field(default_factory=dict)
    last_prompt_hash: str | None = None
    last_llm: tuple[str, int | None] | None = None

    def observe_timestamp(self, raw: str | None) -> None:
        if not raw:
            return
        if self.start_raw is None or raw < self.start_raw:
            self.start_raw = raw
        if self.end_raw is None or raw > self.end_raw:
            self.end_raw = raw

    def set_cwd(self, cwd: str | None) -> None:
        if self.cwd is None and cwd:
            self.cwd = cwd
            self.project = project_label(cwd)

    def add_prompt(self, text: str, ts_ms: int | None) -> None:
        stripped = text.strip()
        if not stripped:
            return
        digest = stable_hash(stripped)
        previous = self.prompt_seen.get(digest)
        duplicate = False
        if digest in self.prompt_seen:
            if previous is not None and ts_ms is not None:
                duplicate = abs(previous - ts_ms) <= 1_000
            elif previous is None and ts_ms is None:
                duplicate = self.last_prompt_hash == digest
        if not duplicate:
            self.user_prompts += 1
            self.prompt_seen[digest] = ts_ms
            self.last_prompt_hash = digest

    def add_llm(self, text_and_usage: str, ts_ms: int | None) -> None:
        digest = stable_hash(text_and_usage)
        duplicate = False
        if self.last_llm is not None and self.last_llm[0] == digest:
            previous_ts = self.last_llm[1]
            duplicate = (
                previous_ts is not None
                and ts_ms is not None
                and abs(previous_ts - ts_ms) <= 1_000
            )
        if not duplicate:
            self.llm_calls += 1
            self.last_llm = (digest, ts_ms)


def load_selected(line: bytes, state: ScanState) -> dict[str, Any] | None:
    try:
        value = json.loads(line)
    except (json.JSONDecodeError, UnicodeDecodeError, MemoryError):
        state.decode_errors += 1
        return None
    return value if isinstance(value, dict) else None


def extract_cwd_from_line(line: bytes) -> str | None:
    match = CWD_RE.search(line)
    return json_string(match.group(1)) if match else None


def update_codex_token_total(obj: dict[str, Any], current: int | None) -> int | None:
    payload = obj.get("payload")
    if not isinstance(payload, dict):
        return current
    info = payload.get("info", payload.get("usage", payload))
    if not isinstance(info, dict):
        return current
    usage = info.get("total_token_usage")
    if not isinstance(usage, dict):
        # Older token_usage records sometimes put a cumulative total directly
        # in info. Do not sum last_token_usage snapshots, which may repeat.
        usage = info if safe_int(info.get("total_tokens")) > 0 else None
    if not isinstance(usage, dict):
        return current
    total = safe_int(usage.get("total_tokens"))
    if total <= 0:
        total = safe_int(usage.get("input_tokens")) + safe_int(
            usage.get("output_tokens")
        )
    if total <= 0:
        return current
    return max(current or 0, total)


def uuid7_seconds(value: str | None) -> float | None:
    if not value:
        return None
    parts = value.split("-")
    if len(parts) < 3 or not parts[2].startswith("7"):
        return None
    try:
        return int(parts[0] + parts[1], 16) / 1_000
    except ValueError:
        return None


def scan_codex(path: Path, session_key: str) -> ScanState:
    state = ScanState(source="codex", session_key=session_key)
    metadata_seen = False
    owns_events = True
    session_started_seconds = 0.0

    with path.open("rb") as handle:
        for line in handle:
            state.bytes_read += len(line)
            state.lines_read += 1
            typ = outer_type("codex", line)
            raw_ts = outer_timestamp("codex", line)

            if typ == "session_meta":
                if not metadata_seen:
                    metadata_seen = True
                    obj = load_selected(line, state)
                    if obj:
                        payload = obj.get("payload", {})
                        if isinstance(payload, dict):
                            parent = (
                                payload.get("parent_thread_id")
                                or payload.get("forked_from_id")
                            )
                            source = payload.get("source")
                            if isinstance(source, dict):
                                parent = parent or (
                                    source.get("subagent", {})
                                    if isinstance(source.get("subagent"), dict)
                                    else {}
                                ).get("thread_spawn", {}).get("parent_thread_id")
                            owns_events = not bool(parent)
                            state.set_cwd(
                                payload.get("cwd")
                                if isinstance(payload.get("cwd"), str)
                                else None
                            )
                            meta_ts = payload.get("timestamp")
                            if not isinstance(meta_ts, str):
                                meta_ts = raw_ts
                            parsed = parse_timestamp_ms(meta_ts)
                            session_started_seconds = (
                                parsed / 1_000 if parsed is not None else 0.0
                            )
                state.observe_timestamp(raw_ts)
                continue

            if not owns_events:
                payload_type = first_match(PAYLOAD_TYPE_RE, line)
                if typ == "event_msg" and payload_type == "task_started":
                    obj = load_selected(line, state)
                    if obj:
                        payload = obj.get("payload", {})
                        started = (
                            payload.get("started_at")
                            if isinstance(payload, dict)
                            else None
                        )
                        source_start = (
                            float(started)
                            if isinstance(started, (int, float)) and started > 0
                            else uuid7_seconds(
                                payload.get("turn_id")
                                if isinstance(payload, dict)
                                and isinstance(payload.get("turn_id"), str)
                                else None
                            )
                        )
                        if source_start and (
                            session_started_seconds == 0.0
                            or source_start >= math.floor(session_started_seconds)
                        ):
                            owns_events = True
                            state.observe_timestamp(raw_ts)
                continue

            state.observe_timestamp(raw_ts)
            if state.cwd is None:
                state.set_cwd(extract_cwd_from_line(line))
            ts_ms = parse_timestamp_ms(raw_ts)

            if typ == "event_msg":
                payload_type = first_match(PAYLOAD_TYPE_RE, line)
                if payload_type not in {
                    "token_count",
                    "token_usage",
                    "user_message",
                    "agent_message",
                }:
                    continue
                obj = load_selected(line, state)
                if not obj:
                    continue
                if payload_type in {"token_count", "token_usage"}:
                    state.provider_tokens = update_codex_token_total(
                        obj, state.provider_tokens
                    )
                    continue
                payload = obj.get("payload", {})
                if not isinstance(payload, dict):
                    continue
                text = payload.get("message", payload.get("content", ""))
                if not isinstance(text, str):
                    text = ""
                if payload_type == "user_message":
                    state.add_prompt(text, ts_ms)
                else:
                    state.add_llm(text, ts_ms)
                continue

            if typ == "response_item":
                payload_type = first_match(PAYLOAD_TYPE_RE, line)
                if payload_type in {"function_call", "custom_tool_call"}:
                    state.tool_calls += 1
                    continue
                if payload_type != "message":
                    continue
                obj = load_selected(line, state)
                if not obj:
                    continue
                payload = obj.get("payload", {})
                if not isinstance(payload, dict):
                    continue
                text_value = payload.get("message")
                text = (
                    text_value
                    if isinstance(text_value, str)
                    else content_to_text(payload.get("content"))
                )
                role = payload.get("role")
                if role == "user":
                    state.add_prompt(text, ts_ms)
                elif role == "assistant" or (
                    role is None
                    and isinstance(payload.get("content"), list)
                    and any(
                        isinstance(item, dict) and item.get("type") == "output_text"
                        for item in payload["content"]
                    )
                ):
                    state.add_llm(text, ts_ms)
                continue

            if typ in {"message", "input", "user"}:
                obj = load_selected(line, state)
                if obj:
                    state.add_prompt(local_message_text(obj), ts_ms)

    return state


def claude_is_tool_result(obj: dict[str, Any]) -> bool:
    if "toolUseResult" in obj or "tool_use_result" in obj:
        return True
    message = obj.get("message")
    content = message.get("content") if isinstance(message, dict) else None
    return isinstance(content, list) and any(
        isinstance(item, dict) and item.get("type") == "tool_result"
        for item in content
    )


def sum_usage(usage: Any) -> int:
    if not isinstance(usage, dict):
        return 0
    return (
        safe_int(usage.get("input_tokens", usage.get("inputTokens")))
        + safe_int(usage.get("output_tokens", usage.get("outputTokens")))
        + safe_int(
            usage.get(
                "cache_creation_input_tokens", usage.get("cacheCreationInputTokens")
            )
        )
        + safe_int(usage.get("cache_read_input_tokens", usage.get("cacheReadInputTokens")))
    )


def scan_claude(path: Path, session_key: str) -> ScanState:
    state = ScanState(source="claude", session_key=session_key)
    message_usage_total = 0
    message_usage_keys: set[str] = set()
    result_usage_total = 0
    result_usage_present = False

    with path.open("rb") as handle:
        for line in handle:
            state.bytes_read += len(line)
            state.lines_read += 1
            typ = outer_type("claude", line)
            raw_ts = outer_timestamp("claude", line)
            state.observe_timestamp(raw_ts)
            if state.cwd is None:
                state.set_cwd(extract_cwd_from_line(line))
            ts_ms = parse_timestamp_ms(raw_ts)

            if typ == "assistant":
                obj = load_selected(line, state)
                if not obj:
                    continue
                message = obj.get("message", {})
                if not isinstance(message, dict):
                    continue
                content = message.get("content")
                usage = message.get("usage")
                if isinstance(content, list):
                    state.tool_calls += sum(
                        1
                        for item in content
                        if isinstance(item, dict) and item.get("type") == "tool_use"
                    )
                text = content_to_text(content)
                if text.strip() or isinstance(usage, dict):
                    usage_fingerprint = json.dumps(
                        usage, sort_keys=True, separators=(",", ":")
                    )
                    state.add_llm(text + usage_fingerprint, ts_ms)
                usage_key = (
                    obj.get("requestId")
                    or message.get("id")
                    or obj.get("uuid")
                    or "usage"
                )
                usage_key = str(usage_key)
                if isinstance(usage, dict) and usage_key not in message_usage_keys:
                    message_usage_keys.add(usage_key)
                    message_usage_total += sum_usage(usage)
                continue

            if typ == "user":
                # Avoid decoding the usually dominant tool-result payloads.
                if (
                    b'"tool_result"' in line
                    or b'"toolUseResult"' in line
                    or b'"tool_use_result"' in line
                ):
                    continue
                obj = load_selected(line, state)
                if not obj or claude_is_tool_result(obj):
                    continue
                message = obj.get("message", {})
                content = message.get("content") if isinstance(message, dict) else message
                state.add_prompt(local_message_text(content), ts_ms)
                continue

            if typ == "result":
                obj = load_selected(line, state)
                if not obj:
                    continue
                state.fallback_duration_ms = max(
                    state.fallback_duration_ms, safe_int(obj.get("duration_ms"))
                )
                model_usage = obj.get("modelUsage")
                if isinstance(model_usage, dict):
                    result_usage_present = True
                    for usage in model_usage.values():
                        result_usage_total += sum_usage(usage)
                continue

            if typ == "queue-operation" and state.user_prompts == 0:
                obj = load_selected(line, state)
                if obj and obj.get("operation") == "enqueue":
                    content = obj.get("content")
                    if isinstance(content, str):
                        state.add_prompt(content, ts_ms)
                continue

            if typ == "last-prompt":
                obj = load_selected(line, state)
                if obj and isinstance(obj.get("lastPrompt"), str):
                    state.add_prompt(obj["lastPrompt"], ts_ms)

    total = result_usage_total if result_usage_present else message_usage_total
    state.provider_tokens = total if total > 0 else None
    return state


def finalize_state(state: ScanState, path: Path) -> dict[str, Any]:
    start_ms = parse_timestamp_ms(state.start_raw)
    end_ms = parse_timestamp_ms(state.end_raw)
    timestamp_source = "records"
    if start_ms is None and end_ms is None:
        timestamp_source = "mtime_fallback"
        modified_ms = int(path.stat().st_mtime * 1_000)
        end_ms = modified_ms
        start_ms = max(0, modified_ms - state.fallback_duration_ms)
    elif start_ms is None:
        start_ms = max(0, end_ms - state.fallback_duration_ms)  # type: ignore[operator]
    elif end_ms is None:
        end_ms = start_ms
    assert start_ms is not None and end_ms is not None
    if end_ms < start_ms:
        start_ms, end_ms = end_ms, start_ms
    duration_seconds = (end_ms - start_ms) / 1_000
    operations = state.llm_calls + state.tool_calls
    bucket = duration_bucket(duration_seconds)
    long_horizon = duration_seconds >= 3_600 or state.tool_calls >= 100
    start_iso = datetime.fromtimestamp(start_ms / 1_000, tz=timezone.utc).isoformat(
        timespec="milliseconds"
    ).replace("+00:00", "Z")
    end_iso = datetime.fromtimestamp(end_ms / 1_000, tz=timezone.utc).isoformat(
        timespec="milliseconds"
    ).replace("+00:00", "Z")
    return {
        "session_key": state.session_key,
        "agent": state.source,
        "project": state.project,
        "start_time_utc": start_iso,
        "end_time_utc": end_iso,
        "duration_seconds": round(duration_seconds, 3),
        "duration_bucket": bucket,
        "user_prompts": state.user_prompts,
        "llm_calls": state.llm_calls,
        "tool_calls": state.tool_calls,
        "operations": operations,
        "provider_reported_tokens": state.provider_tokens,
        "long_horizon_candidate": long_horizon,
        "source_bytes": state.bytes_read,
        "source_lines": state.lines_read,
        "timestamp_source": timestamp_source,
        "decode_errors": state.decode_errors,
    }


def session_paths(root: Path) -> list[Path]:
    return sorted(path for path in root.rglob("*.jsonl") if path.is_file())


def inventory_roots() -> tuple[list[dict[str, Any]], list[str], dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    access_issues: list[str] = []
    scan_meta: dict[str, Any] = {}
    global_start = time.monotonic()

    for source, root in ROOTS:
        source_start = time.monotonic()
        if not root.is_dir():
            access_issues.append(
                f"{source}: session root unavailable or unreadable; no escalation attempted"
            )
            scan_meta[source] = {"files": 0, "bytes": 0, "elapsed_seconds": 0.0}
            continue
        try:
            paths = session_paths(root)
        except OSError:
            access_issues.append(
                f"{source}: session root traversal was blocked; no escalation attempted"
            )
            scan_meta[source] = {"files": 0, "bytes": 0, "elapsed_seconds": 0.0}
            continue

        source_bytes = 0
        for index, path in enumerate(paths, start=1):
            try:
                relative = path.relative_to(root).as_posix()
                key = stable_hash(f"{source}:{relative}")[:16]
                state = (
                    scan_codex(path, key)
                    if source == "codex"
                    else scan_claude(path, key)
                )
                row = finalize_state(state, path)
                rows.append(row)
                source_bytes += state.bytes_read
            except (OSError, PermissionError) as error:
                # Do not expose a source path in the deliverables.
                access_issues.append(
                    f"{source}: one session file could not be read "
                    f"({type(error).__name__}); no escalation attempted"
                )
            if index % 100 == 0 or index == len(paths):
                elapsed = time.monotonic() - source_start
                print(
                    f"{source}: {index}/{len(paths)} files, "
                    f"{source_bytes / (1024 ** 3):.2f} GiB read, {elapsed:.1f}s",
                    flush=True,
                )

        scan_meta[source] = {
            "files_discovered": len(paths),
            "rows_emitted": sum(1 for row in rows if row["agent"] == source),
            "bytes_read": source_bytes,
            "elapsed_seconds": round(time.monotonic() - source_start, 3),
        }

    rows.sort(key=lambda row: (row["start_time_utc"], row["agent"], row["session_key"]))
    scan_meta["total_elapsed_seconds"] = round(time.monotonic() - global_start, 3)
    return rows, access_issues, scan_meta


def aggregate_rows(rows: Iterable[dict[str, Any]]) -> dict[str, Any]:
    selected = list(rows)
    known_tokens = [
        int(row["provider_reported_tokens"])
        for row in selected
        if row["provider_reported_tokens"] is not None
    ]
    durations = sorted(float(row["duration_seconds"]) for row in selected)
    return {
        "sessions": len(selected),
        "user_prompts": sum(int(row["user_prompts"]) for row in selected),
        "llm_calls": sum(int(row["llm_calls"]) for row in selected),
        "tool_calls": sum(int(row["tool_calls"]) for row in selected),
        "operations": sum(int(row["operations"]) for row in selected),
        "provider_tokens_known_sum": sum(known_tokens),
        "provider_token_sessions": len(known_tokens),
        "duration_hours": sum(durations) / 3_600,
        "median_duration_hours": (
            (
                durations[len(durations) // 2]
                if len(durations) % 2
                else (
                    durations[len(durations) // 2 - 1]
                    + durations[len(durations) // 2]
                )
                / 2
            )
            / 3_600
            if durations
            else 0.0
        ),
        "long_horizon_sessions": sum(
            bool(row["long_horizon_candidate"]) for row in selected
        ),
    }


def cost_estimate(stats: dict[str, Any]) -> dict[str, Any]:
    operation_equivalent_sessions = (
        stats["operations"] / REFERENCE_OPERATIONS_PER_SESSION
    )
    estimated_tokens = (
        operation_equivalent_sessions * REFERENCE_INPUT_TOKENS_PER_SESSION
    )
    estimated_seconds = (
        operation_equivalent_sessions * REFERENCE_WORKER_SECONDS_PER_SESSION
    )
    return {
        "operation_equivalent_sessions": operation_equivalent_sessions,
        "estimated_annotation_input_tokens": estimated_tokens,
        "estimated_annotation_worker_seconds": estimated_seconds,
    }


def build_candidates(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    ends = [
        datetime.fromisoformat(row["end_time_utc"].replace("Z", "+00:00"))
        for row in rows
    ]
    latest = max(ends) if ends else datetime.now(timezone.utc)
    threshold = latest - timedelta(weeks=RECENT_WEEKS)
    recent_long = [
        row
        for row, end in zip(rows, ends)
        if row["long_horizon_candidate"] and end >= threshold
    ]

    research_project = "agentsight-research-semantic-flamegraph"
    agentsight_rows = [row for row in rows if row["project"] == research_project]
    if not agentsight_rows:
        # Fail visibly but remain useful if the script is moved to a differently
        # named checkout.
        agentsight_rows = [
            row
            for row in rows
            if "agentsight" in row["project"].lower()
            and "research" in row["project"].lower()
        ]

    by_project: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        if row["project"] not in {"unknown", "home", "root", "temporary", "ephemeral"}:
            by_project[row["project"]].append(row)
    distinct_projects = sorted(
        (
            (project, project_rows)
            for project, project_rows in by_project.items()
            if not any(
                token in project.lower() for token in ("agentsight", "agentpprof")
            )
        ),
        key=lambda item: (
            aggregate_rows(item[1])["operations"],
            len(item[1]),
            item[0],
        ),
        reverse=True,
    )
    if not distinct_projects:
        distinct_projects = sorted(
            by_project.items(),
            key=lambda item: (
                aggregate_rows(item[1])["operations"],
                len(item[1]),
                item[0],
            ),
            reverse=True,
        )
    heavy_name, heavy_rows = (
        distinct_projects[0] if distinct_projects else ("unknown", [])
    )

    definitions = [
        (
            f"Recent long-horizon ({RECENT_WEEKS} weeks)",
            (
                f"All sessions ending since {threshold.date().isoformat()} that last "
                "at least one hour or contain at least 100 tool calls"
            ),
            recent_long,
        ),
        (
            "AgentSight research worktree",
            (
                "All sessions whose coarse project basename is exactly "
                f"{research_project}"
            ),
            agentsight_rows,
        ),
        (
            f"Heavy project: {heavy_name}",
            "The complete session set of the highest-operation non-AgentSight project",
            heavy_rows,
        ),
    ]
    candidates: list[dict[str, Any]] = []
    for name, definition, population in definitions:
        stats = aggregate_rows(population)
        candidates.append(
            {
                "name": name,
                "definition": definition,
                "stats": stats,
                "cost": cost_estimate(stats),
            }
        )
    return candidates


def format_int(value: float | int) -> str:
    return f"{value:,.0f}"


def format_duration(seconds: float) -> str:
    if seconds < 60:
        return f"{seconds:.1f}s"
    if seconds < 3_600:
        return f"{seconds / 60:.1f}m"
    return f"{seconds / 3_600:.2f}h"


def markdown_table(headers: list[str], rows: Iterable[list[str]]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    lines.extend("| " + " | ".join(row) + " |" for row in rows)
    return "\n".join(lines)


def select_recommendation(candidates: list[dict[str, Any]]) -> tuple[str, str]:
    recent = candidates[0]
    agentsight = candidates[1]
    if (
        agentsight["stats"]["long_horizon_sessions"] >= 10
        and agentsight["stats"]["operations"] >= 1_000
    ):
        return (
            agentsight["name"],
            "It combines a coherent real engineering objective with many complete "
            "long-running sessions, directly representing the agents that built the "
            "system and paper. The recent cross-project population is the stronger "
            "robustness population, but its heterogeneous objectives weaken a single "
            "case-study narrative.",
        )
    return (
        recent["name"],
        "It directly selects long-running behavior across multiple real projects, "
        "giving the title the broadest literal support. The project-specific "
        "populations are useful focused follow-ups.",
    )


def render_results(
    rows: list[dict[str, Any]],
    access_issues: list[str],
    scan_meta: dict[str, Any],
    candidates: list[dict[str, Any]],
) -> str:
    total = aggregate_rows(rows)
    project_groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    bucket_groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        project_groups[row["project"]].append(row)
        bucket_groups[row["duration_bucket"]].append(row)

    project_stats = [
        (project, aggregate_rows(group)) for project, group in project_groups.items()
    ]
    project_stats.sort(
        key=lambda item: (
            item[1]["sessions"],
            item[1]["operations"],
            item[0],
        ),
        reverse=True,
    )

    project_table = markdown_table(
        [
            "Project (coarse)",
            "Sessions",
            "Prompts",
            "LLM",
            "Tools",
            "Operations",
            "Known tokens",
            "Token coverage",
            "Duration h",
            "Long-horizon",
        ],
        (
            [
                project,
                format_int(stats["sessions"]),
                format_int(stats["user_prompts"]),
                format_int(stats["llm_calls"]),
                format_int(stats["tool_calls"]),
                format_int(stats["operations"]),
                format_int(stats["provider_tokens_known_sum"]),
                (
                    f"{stats['provider_token_sessions']}/{stats['sessions']}"
                    if stats["sessions"]
                    else "0/0"
                ),
                f"{stats['duration_hours']:,.1f}",
                format_int(stats["long_horizon_sessions"]),
            ]
            for project, stats in project_stats
        ),
    )

    bucket_order = ("<10 min", "10-60 min", "1-6 h", ">6 h")
    bucket_table = markdown_table(
        [
            "Duration bucket",
            "Sessions",
            "Prompts",
            "LLM",
            "Tools",
            "Operations",
            "Known tokens",
            "Token coverage",
        ],
        (
            [
                bucket,
                format_int(stats["sessions"]),
                format_int(stats["user_prompts"]),
                format_int(stats["llm_calls"]),
                format_int(stats["tool_calls"]),
                format_int(stats["operations"]),
                format_int(stats["provider_tokens_known_sum"]),
                (
                    f"{stats['provider_token_sessions']}/{stats['sessions']}"
                    if stats["sessions"]
                    else "0/0"
                ),
            ]
            for bucket in bucket_order
            for stats in (aggregate_rows(bucket_groups.get(bucket, [])),)
        ),
    )

    long_rows = sorted(
        (row for row in rows if row["long_horizon_candidate"]),
        key=lambda row: (
            row["duration_seconds"],
            row["tool_calls"],
            row["operations"],
        ),
        reverse=True,
    )
    long_table = markdown_table(
        [
            "Session key",
            "Agent",
            "Project",
            "Start (UTC)",
            "Duration",
            "Prompts",
            "LLM",
            "Tools",
            "Known tokens",
        ],
        (
            [
                row["session_key"],
                row["agent"],
                row["project"],
                row["start_time_utc"],
                format_duration(float(row["duration_seconds"])),
                format_int(row["user_prompts"]),
                format_int(row["llm_calls"]),
                format_int(row["tool_calls"]),
                (
                    format_int(row["provider_reported_tokens"])
                    if row["provider_reported_tokens"] is not None
                    else "not reported"
                ),
            ]
            for row in long_rows
        ),
    )

    candidate_table = markdown_table(
        [
            "Candidate population",
            "Sessions",
            "Long-horizon",
            "Operations",
            "Known provider tokens",
            "Token coverage",
            "Est. annotation input tokens",
            "Est. worker time",
        ],
        (
            [
                candidate["name"],
                format_int(candidate["stats"]["sessions"]),
                format_int(candidate["stats"]["long_horizon_sessions"]),
                format_int(candidate["stats"]["operations"]),
                format_int(candidate["stats"]["provider_tokens_known_sum"]),
                (
                    f"{candidate['stats']['provider_token_sessions']}/"
                    f"{candidate['stats']['sessions']}"
                ),
                format_int(candidate["cost"]["estimated_annotation_input_tokens"]),
                (
                    f"{candidate['cost']['estimated_annotation_worker_seconds'] / 3_600:,.1f} h"
                ),
            ]
            for candidate in candidates
        ),
    )

    recommendation, recommendation_reason = select_recommendation(candidates)
    issues = (
        "\n".join(f"- {issue}" for issue in access_issues)
        if access_issues
        else "- None. Both requested roots were readable."
    )
    decode_error_count = sum(int(row["decode_errors"]) for row in rows)
    fallback_count = sum(row["timestamp_source"] != "records" for row in rows)
    generated_at = datetime.now(timezone.utc).isoformat(timespec="seconds").replace(
        "+00:00", "Z"
    )

    population_definitions = "\n".join(
        f"- **{candidate['name']}:** {candidate['definition']}."
        for candidate in candidates
    )

    return f"""# Local agent-session sizing inventory

Generated: {generated_at}

## Outcome

The read-only scan inventoried **{format_int(total['sessions'])} session files**
({format_int(sum(row['source_bytes'] for row in rows))} bytes), including
**{format_int(total['long_horizon_sessions'])} long-horizon candidates**. A
session is long-horizon when its recorded duration is at least one hour or it
contains at least 100 source-visible tool calls.

No prompt, response, command, tool-output, absolute path, or raw session ID is
present in this report or `inventory-results.json`. Session keys are one-way
hashes of source-relative filenames; project labels are coarse cwd basenames.
The scan opened session files read-only and wrote only in this experiment
directory.

## Access and scan quality

{issues}

- Selective JSON decode errors on relevant records: {format_int(decode_error_count)}
- Sessions using file-mtime timestamp fallback: {format_int(fallback_count)}
- Codex: {format_int(scan_meta.get('codex', {}).get('rows_emitted', 0))} rows,
  {format_int(scan_meta.get('codex', {}).get('bytes_read', 0))} bytes read.
- Claude: {format_int(scan_meta.get('claude', {}).get('rows_emitted', 0))} rows,
  {format_int(scan_meta.get('claude', {}).get('bytes_read', 0))} bytes read.

## Measurement definitions

- Start and end are the earliest and latest source-record timestamps owned by
  the session. A missing timestamp falls back to file mtime (and a reported
  Claude duration when available).
- User prompts exclude tool-result messages and deduplicate repeated
  source-visible prompt records within one second.
- LLM calls are source-visible assistant-response records, deduplicated within
  one second like `agent-session`; they are not an estimate of hidden provider
  API requests.
- Tool calls are Claude `tool_use` items and Codex `function_call` or
  `custom_tool_call` items. A Codex composite custom call is one source call,
  matching the repository parser.
- Provider tokens use the final Codex cumulative total when present. Claude
  uses the result-level model total when present, otherwise deduplicated
  message-level input, output, cache-creation, and cache-read counters.
- “Known tokens” sums only sessions with provider counters. Coverage is shown
  beside every aggregate; an uncovered session contributes no invented token
  count.

## Aggregate by project

{project_table}

## Aggregate by duration bucket

{bucket_table}

## Long-horizon sessions

The following is the complete identified set, not a sample. The same rows carry
`long_horizon_candidate: true` in `inventory-results.json`.

{long_table}

## Candidate case-study populations

{candidate_table}

Population definitions:

{population_definitions}

### Annotation-cost scaling

Step 0077 measured 27,362 actual annotation-backend input tokens and 15.14
summed worker-seconds per session over 7,229 source operations in 440 sessions,
or {REFERENCE_OPERATIONS_PER_SESSION:.4f} operations/session. Because the
candidate mean session sizes differ materially from that reference, this
inventory applies one transparent linear operation proxy:

`operation-equivalent sessions = population (LLM + tool calls) / {REFERENCE_OPERATIONS_PER_SESSION:.4f}`

It multiplies operation-equivalent sessions by 27,362 input tokens and 15.14
worker-seconds. These are sizing estimates, not measured costs. They assume
annotation input scales linearly with source-visible operations and omit fixed
per-session overhead, batching/cache effects, output tokens, retries, and
provider latency. The reference measurement is
`step-0077-20260723T233616-0700/experiment-001/first-pass-cost-and-aggregate.md`.

## Recommendation

**Use “{recommendation}” as the primary Long Horizon case-study population.**
{recommendation_reason}

Retain the other two populations as sensitivity or scope checks. Before a full
annotation run, freeze the selected session keys from
`inventory-results.json`; do not rescan-and-select after seeing annotations.
"""


def write_outputs(
    rows: list[dict[str, Any]],
    access_issues: list[str],
    scan_meta: dict[str, Any],
    elapsed_seconds: float,
) -> None:
    generated_at = datetime.now(timezone.utc).isoformat(timespec="seconds").replace(
        "+00:00", "Z"
    )
    payload = {
        "schema": "agentsight.local-session-sizing.v1",
        "generated_at_utc": generated_at,
        "privacy": (
            "Coarse project labels and hashed session keys only; no conversation "
            "content, commands, tool output, absolute paths, or raw session IDs."
        ),
        "long_horizon_rule": "duration_seconds >= 3600 OR tool_calls >= 100",
        "access_issues": access_issues,
        "scan_meta": scan_meta,
        "sessions": rows,
    }
    (OUTPUT_DIR / "inventory-results.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    candidates = build_candidates(rows)
    (OUTPUT_DIR / "results.md").write_text(
        render_results(rows, access_issues, scan_meta, candidates), encoding="utf-8"
    )
    command = (
        "/home/yunwei37/workspace/.venv/bin/python3 "
        "docs/tmp/build-and-evaluate/"
        "step-0084-20260725T193000-0700/experiment-001/inventory.py"
    )
    log = f"""# Execution log

All commands were read-only over the session roots. No git command was run.

| Command | Purpose | Wall time |
| --- | --- | ---: |
| `{command}` | Full inventory scan and report generation | {elapsed_seconds:.3f} s |

Scan started and ended in UTC on {generated_at}. Per-source elapsed times and
byte counts are recorded below:

```json
{json.dumps(scan_meta, indent=2, sort_keys=True)}
```
"""
    (OUTPUT_DIR / "execution-log.md").write_text(log, encoding="utf-8")


def render_existing() -> int:
    """Recover report rendering from a completed raw scan without rescanning."""
    started = time.monotonic()
    raw_path = OUTPUT_DIR / "inventory-results.json"
    payload = json.loads(raw_path.read_text(encoding="utf-8"))
    rows = payload.get("sessions")
    if not isinstance(rows, list):
        raise ValueError("inventory-results.json has no session row list")
    access_issues = payload.get("access_issues")
    if not isinstance(access_issues, list):
        access_issues = []
    scan_meta = payload.get("scan_meta")
    if not isinstance(scan_meta, dict):
        scan_meta = {}
        for source in ("codex", "claude"):
            selected = [row for row in rows if row.get("agent") == source]
            scan_meta[source] = {
                "files_discovered": len(selected),
                "rows_emitted": len(selected),
                "bytes_read": sum(safe_int(row.get("source_bytes")) for row in selected),
                "elapsed_seconds": None,
            }
        scan_meta["total_elapsed_seconds"] = None
    candidates = build_candidates(rows)
    (OUTPUT_DIR / "results.md").write_text(
        render_results(rows, access_issues, scan_meta, candidates), encoding="utf-8"
    )
    elapsed = time.monotonic() - started
    scan_command = (
        "/home/yunwei37/workspace/.venv/bin/python3 "
        "docs/tmp/build-and-evaluate/"
        "step-0084-20260725T193000-0700/experiment-001/inventory.py"
    )
    render_command = scan_command + " --render-only"
    log = f"""# Execution log

All commands were read-only over the session roots. No git command was run.

| Command | Purpose | Wall time |
| --- | --- | ---: |
| `{scan_command}` | Full 7,977-file inventory scan; raw JSON completed, then the initial Markdown formatter failed | ~407.0 s |
| `{render_command}` | Render reports from the completed raw JSON; no session rescan | {elapsed:.3f} s |

The first wall time is reconstructed from its terminal per-source progress
markers (402.5 s Codex and 4.5 s Claude), because the formatter failed before
writing its own timer. The failure was a local Markdown-format expression and
did not affect any per-session row. The second pass reused and validated the
completed `inventory-results.json`.

Recovered scan metadata:

```json
{json.dumps(scan_meta, indent=2, sort_keys=True)}
```
"""
    (OUTPUT_DIR / "execution-log.md").write_text(log, encoding="utf-8")
    print(
        f"render-only complete: {len(rows)} rows, {elapsed:.3f}s",
        flush=True,
    )
    return 0


def main() -> int:
    if sys.argv[1:] == ["--render-only"]:
        return render_existing()
    if len(sys.argv) > 1:
        raise SystemExit("usage: inventory.py [--render-only]")
    started = time.monotonic()
    rows, access_issues, scan_meta = inventory_roots()
    elapsed = time.monotonic() - started
    write_outputs(rows, access_issues, scan_meta, elapsed)
    print(
        f"complete: {len(rows)} rows, {elapsed:.3f}s, outputs in experiment directory",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
