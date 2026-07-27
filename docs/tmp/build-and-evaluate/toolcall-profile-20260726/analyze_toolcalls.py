#!/usr/bin/env python3
"""Profile tool-call patterns and systems optimization opportunities.

The script consumes the six *uncompressed* projected event JSON files under
rq1-rq4-recompute-final.  The adjacent .json.gz files are byte-equivalent
transport copies and are intentionally not counted again.

It optionally enriches projected calls from the native Claude/Codex/Gemini
JSONL files named by each event's ``source_file``.  Native content is never
written to the output directory: only aggregate durations, byte counts,
statuses, hashes, and path-flow tokens are retained.

Run from the repository root:

    python3 docs/tmp/build-and-evaluate/toolcall-profile-20260726/analyze_toolcalls.py
"""

from __future__ import annotations

import argparse
import collections
import csv
import dataclasses
import datetime as dt
import hashlib
import json
import math
import os
import re
import statistics
import sys
from pathlib import Path
from typing import Any, Iterable, Iterator, Sequence


REPO_ROOT = Path(__file__).resolve().parents[4]
DEFAULT_INPUT = (
    REPO_ROOT
    / "docs/tmp/build-and-evaluate/rq1-rq4-recompute-final/rq1-raw/events"
)
DEFAULT_OUTPUT = Path(__file__).resolve().parent

READ_ONLY_OPS = {"navigate", "search", "read", "vcs", "web"}
LOCAL_DISCOVERY_OPS = {"navigate", "search", "read"}
SHELL_NAMES = {"bash", "exec", "exec_command", "run_shell_command"}
WAIT_NAMES = {
    "wait",
    "write_stdin",
    "wait_agent",
    "monitor",
    "read_thread_terminal",
    "send_input",
}
MUTATE_NAMES = {
    "edit",
    "write",
    "apply_patch",
    "notebookedit",
    "write_file",
}
READ_NAMES = {"read", "read_file", "view_image"}
SEARCH_NAMES = {"grep", "glob", "grep_search", "glob_search"}
WEB_NAMES = {"websearch", "webfetch", "_fetch", "web_search", "web_fetch"}
DELEGATE_NAMES = {
    "agent",
    "spawn_agent",
    "send_message",
    "followup_task",
    "list_agents",
    "interrupt_agent",
    "close_agent",
    "resume_agent",
}
CONTROL_NAMES = {
    "update_plan",
    "taskcreate",
    "taskupdate",
    "todowrite",
    "get_goal",
    "create_goal",
    "update_goal",
    "skill",
    "toolsearch",
    "structuredoutput",
    "enterplanmode",
    "exitplanmode",
    "askuserquestion",
}

VALIDATE_RE = re.compile(
    r"""(?ix)
    (?:^|[;&|]\s*|\s)
    (?:
      cargo\s+(?:test|check|clippy|build)
      |pytest(?:\s|$)|python(?:3)?\s+-m\s+pytest
      |(?:npm|pnpm|yarn)\s+(?:run\s+)?(?:test|lint|build|check|typecheck)
      |make\s+(?:test|check|lint|build|debug|experimental)
      |(?:go|zig)\s+test
      |(?:cmake|ninja|meson)\s+(?:--build|test)
      |(?:ruff|mypy|pyright|eslint|prettier)\b
      |(?:latexmk|pdflatex|xelatex|lualatex)\b
      |(?:tsc|next\s+build)\b
      |(?:bash|sh)\s+[^\n;]*(?:test|check|smoke|benchmark)[^\n;]*\.sh
    )
    """
)
SEARCH_RE = re.compile(r"(?i)(?:^|[;&|]\s*|\s)(?:rg|grep|ag|ripgrep)\b")
NAVIGATE_RE = re.compile(
    r"(?i)(?:^|[;&|]\s*|\s)(?:pwd|ls|tree|find|fd)\b|rg\s+--files\b"
)
READ_RE = re.compile(
    r"(?i)(?:^|[;&|]\s*|\s)(?:cat|sed|head|tail|less|more|wc|"
    r"pdftotext|pdfinfo|strings|objdump|readelf|nm)\b"
)
VCS_RE = re.compile(r"(?i)(?:^|[;&|]\s*|\s)git\s+(?:status|diff|log|show|branch|worktree)\b")
MUTATE_SHELL_RE = re.compile(
    r"(?i)(?:^|[;&|]\s*|\s)(?:rm|mv|cp|install|mkdir|touch|perl\s+-[pi]|"
    r"sed\s+-i|git\s+(?:add|commit|push|merge|rebase|cherry-pick))\b|"
    r"(?:apply_patch|tee\s+(?!/dev/null\b))\b"
)
COMPOUND_RE = re.compile(r"\&\&|\|\||;|\n")
PATH_TOKEN_RE = re.compile(
    r"(?<![A-Za-z0-9_])(?:\.{0,2}/|/)?"
    r"[A-Za-z0-9_@.+-]+(?:/[A-Za-z0-9_@.+-]+)+"
    r"|(?<![A-Za-z0-9_])[A-Za-z0-9_@+-]+\."
    r"(?:py|rs|c|h|cc|cpp|hpp|js|jsx|ts|tsx|md|tex|bib|toml|json|jsonl|"
    r"yaml|yml|sh|bash|txt|csv|pdf|html|css|lock|go|java|kt|rb|php)"
)
EXIT_CODE_RE = re.compile(
    r"(?:Process exited with code|exit(?:ed)?(?:\s+with)?(?:\s+code)?[:=]?)\s*(-?\d+)",
    re.I,
)
WALL_TIME_RE = re.compile(r"Wall time:\s*([0-9.]+)\s*seconds", re.I)
NO_PROGRESS_RE = re.compile(
    r"(?i)(?:timed?\s*out|timeout summary|no (?:new )?(?:activity|output|updates?)|"
    r"still running|script running with cell id|session remains|running agents)"
)
PASSIVE_WAIT_NAMES = {"wait", "wait_agent", "monitor", "read_thread_terminal"}


def intern_str(value: Any) -> str:
    return sys.intern("" if value is None else str(value))


def parse_ts_ms(value: Any) -> int | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return int(value)
    text = str(value)
    try:
        return int(dt.datetime.fromisoformat(text.replace("Z", "+00:00")).timestamp() * 1000)
    except (ValueError, OverflowError):
        return None


def to_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, (bytes, bytearray)):
        return bytes(value).decode("utf-8", errors="replace")
    if isinstance(value, list):
        parts: list[str] = []
        for item in value:
            if isinstance(item, dict):
                parts.append(to_text(item.get("text", item.get("content", item))))
            else:
                parts.append(to_text(item))
        return "\n".join(parts)
    if isinstance(value, dict):
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    return str(value)


def q(values: Sequence[float | int], percentile: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(float(v) for v in values)
    if len(ordered) == 1:
        return ordered[0]
    pos = (len(ordered) - 1) * percentile
    lo = math.floor(pos)
    hi = math.ceil(pos)
    if lo == hi:
        return ordered[lo]
    frac = pos - lo
    return ordered[lo] * (1 - frac) + ordered[hi] * frac


def safe_div(num: float, den: float) -> float:
    return num / den if den else 0.0


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def normalize_path(value: str) -> str:
    path = value.strip().strip("'\"`()[]{}:,")
    path = re.sub(r"^file://", "", path)
    path = re.sub(r"/+", "/", path)
    while path.startswith("./"):
        path = path[2:]
    return path


def command_path_tokens(command: str, limit: int = 40) -> tuple[str, ...]:
    found: list[str] = []
    seen: set[str] = set()
    for match in PATH_TOKEN_RE.finditer(command):
        token = normalize_path(match.group(0))
        if token and token not in seen:
            seen.add(token)
            found.append(token)
            if len(found) >= limit:
                break
    return tuple(found)


def output_path_tokens(text: str, limit: int = 160) -> tuple[str, ...]:
    # Results can be many MB.  Path-flow detection needs only a bounded set.
    if len(text) > 2_000_000:
        text = text[:1_000_000] + "\n" + text[-1_000_000:]
    return command_path_tokens(text, limit=limit)


def canonical_command(command: str) -> str:
    return re.sub(r"\s+", " ", command.strip())


def event_targets(event: dict[str, Any]) -> tuple[str, ...]:
    targets: list[str] = []
    seen: set[str] = set()
    for action in event.get("actions") or []:
        path = normalize_path(str(action.get("path") or ""))
        if path and path not in seen:
            seen.add(path)
            targets.append(path)
    if not targets:
        for source_path in event.get("source_paths") or []:
            path = normalize_path(str(source_path.get("path") or ""))
            if path and path not in seen:
                seen.add(path)
                targets.append(path)
    if not targets:
        targets.extend(command_path_tokens(str(event.get("command") or "")))
    return tuple(targets[:40])


def target_aliases(targets: Iterable[str]) -> set[str]:
    aliases: set[str] = set()
    for target in targets:
        norm = normalize_path(target)
        if not norm:
            continue
        aliases.add(norm)
        parts = norm.split("/")
        if len(parts) >= 2:
            aliases.add("/".join(parts[-2:]))
    return aliases


def exact_targets(targets: Iterable[str]) -> set[str]:
    return {normalize_path(target) for target in targets if normalize_path(target)}


def content_line_hashes(text: str, limit: int = 6000) -> tuple[int, ...]:
    """Retain bounded content evidence without writing native text."""
    hashes: list[int] = []
    seen: set[int] = set()
    for line in text.splitlines():
        normalized = re.sub(r"\s+", " ", line.strip())
        if len(normalized) < 8:
            continue
        digest = int.from_bytes(
            hashlib.sha256(normalized.encode("utf-8")).digest()[:8], "big"
        )
        if digest not in seen:
            seen.add(digest)
            hashes.append(digest)
            if len(hashes) >= limit:
                break
    return tuple(hashes)


def mutation_context_line_hashes(input_value: Any) -> tuple[int, ...]:
    value = input_value
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except json.JSONDecodeError:
            value = {"patch": value}
    pieces: list[str] = []
    if isinstance(value, dict):
        for key in ("old_string", "oldText", "old_text"):
            if isinstance(value.get(key), str):
                pieces.append(value[key])
        for key in ("patch", "input"):
            patch = value.get(key)
            if not isinstance(patch, str):
                continue
            context = [
                line[1:]
                for line in patch.splitlines()
                if line.startswith((" ", "-"))
                and not line.startswith(("---", "***"))
            ]
            pieces.extend(context)
    return content_line_hashes("\n".join(pieces), limit=1000)


def wait_metadata(tool_name: str, input_value: Any) -> tuple[str, bool]:
    name = tool_name.lower()
    value = input_value
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except json.JSONDecodeError:
            value = {"value": value}
    if not isinstance(value, dict):
        value = {}
    active_payload = any(
        bool(value.get(key)) for key in ("chars", "input", "text", "message", "data")
    )
    passive = name in PASSIVE_WAIT_NAMES or (
        name in {"write_stdin", "send_input"} and not active_payload
    )
    handle_parts = [
        f"{key}={value[key]}"
        for key in (
            "cell_id",
            "session_id",
            "thread_id",
            "job_id",
            "target",
            "agent_id",
            "process_id",
        )
        if value.get(key) not in (None, "")
    ]
    if not handle_parts and name == "wait_agent":
        handle_parts = ["mailbox=global"]
    return intern_str("|".join(handle_parts)), passive


def normalized_error_signature(text: str) -> str:
    sample = "\n".join(line.strip() for line in text.splitlines() if line.strip())[:1000]
    sample = re.sub(r"\b\d+\b", "<n>", sample.lower())
    sample = re.sub(r"\s+", " ", sample)
    return hashlib.sha256(sample.encode("utf-8")).hexdigest()[:20] if sample else ""


def classify_shell(command: str, has_write_action: bool) -> str:
    if has_write_action or MUTATE_SHELL_RE.search(command):
        return "mutate"
    if VALIDATE_RE.search(command):
        return "validate"
    if SEARCH_RE.search(command):
        if re.search(r"(?i)\brg\s+--files\b", command):
            return "navigate"
        return "search"
    if VCS_RE.search(command):
        return "vcs"
    if READ_RE.search(command):
        return "read"
    if NAVIGATE_RE.search(command):
        return "navigate"
    return "shell"


def classify_operation(
    tool_name: str, category: str, command: str, actions: Sequence[dict[str, Any]]
) -> str:
    name = tool_name.lower()
    has_write_action = any(
        str(action.get("access") or "").lower() in {"write", "create", "delete", "rename"}
        for action in actions
    )
    if category.lower() in {"edit", "write", "mutation"}:
        has_write_action = True
    if name in WAIT_NAMES:
        return "wait"
    if name in MUTATE_NAMES or has_write_action:
        return "mutate"
    if name in READ_NAMES:
        return "read"
    if name in SEARCH_NAMES:
        return "search"
    if name in WEB_NAMES or name.startswith("mcp__") and "search" in name:
        return "web"
    if name in DELEGATE_NAMES:
        return "delegate"
    if name in CONTROL_NAMES or name.startswith("task"):
        return "control"
    if name in SHELL_NAMES or category.lower() == "shell":
        return classify_shell(command, has_write_action)
    if "test" in name or "lint" in name or "build" in name:
        return "validate"
    return "other"


def pattern_op(op: str) -> str:
    if op in {"navigate", "search"}:
        return "explore"
    if op == "mutate":
        return "edit"
    if op == "validate":
        return "test"
    return op


@dataclasses.dataclass(slots=True)
class Call:
    idx: int
    project: str
    vendor: str
    source_file: str
    source_call_id: str
    native_session_id: str
    stream_id: str
    lane_id: str
    prompt_index: int
    source_ordinal: int
    ts_ms: int
    tool_name: str
    category: str
    command: str
    command_norm: str
    command_name: str
    op: str
    pop: str
    targets: tuple[str, ...]
    status: str
    mutation_payload_bytes: int = 0
    raw_input_hash: str = ""
    raw_matched: bool = False
    start_ms: int | None = None
    end_ms: int | None = None
    duration_ms: int | None = None
    output_bytes: int = 0
    output_hash: str = ""
    output_paths: tuple[str, ...] = ()
    output_line_hashes: tuple[int, ...] = ()
    mutation_context_line_hashes: tuple[int, ...] = ()
    exit_code: int | None = None
    is_error: bool = False
    error_signature: str = ""
    no_progress: bool = False
    batch_id: str = ""
    wait_handle: str = ""
    wait_passive: bool = False
    model_gap_ms: int | None = None
    workspace_epoch: int = 0

    @property
    def failed(self) -> bool:
        return (
            self.is_error
            or self.exit_code not in (None, 0)
            or self.status.lower() in {"error", "failed", "failure", "cancelled", "canceled"}
        )

    @property
    def primary_target(self) -> str:
        return self.targets[0] if self.targets else ""


def mutation_payload_size(input_value: Any) -> int:
    value = input_value
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except json.JSONDecodeError:
            return len(value.encode("utf-8"))
    if isinstance(value, dict):
        pieces: list[str] = []
        for key in (
            "new_string",
            "newText",
            "content",
            "patch",
            "input",
            "text",
        ):
            item = value.get(key)
            if isinstance(item, str):
                pieces.append(item)
        if pieces:
            return sum(len(piece.encode("utf-8")) for piece in pieces)
    return len(to_text(value).encode("utf-8"))


def raw_start_records(obj: dict[str, Any]) -> Iterator[tuple[str, str, Any, str]]:
    """Yield (call_id, tool_name, input, batch_id)."""
    timestamp = str(obj.get("timestamp") or "")
    payload = obj.get("payload")
    if isinstance(payload, dict) and payload.get("type") in {
        "function_call",
        "custom_tool_call",
    }:
        call_id = payload.get("call_id") or payload.get("id")
        if call_id:
            yield (
                str(call_id),
                str(payload.get("name") or payload.get("tool_name") or ""),
                payload.get("arguments", payload.get("input")),
                str(payload.get("id") or timestamp),
            )

    message = obj.get("message")
    if isinstance(message, dict):
        content = message.get("content")
        if isinstance(content, list):
            batch_id = str(message.get("id") or obj.get("requestId") or obj.get("uuid") or timestamp)
            for block in content:
                if not isinstance(block, dict):
                    continue
                if block.get("type") in {"tool_use", "function_call"}:
                    call_id = block.get("id") or block.get("call_id")
                    if call_id:
                        yield (
                            str(call_id),
                            str(block.get("name") or ""),
                            block.get("input", block.get("arguments")),
                            batch_id,
                        )


def raw_output_records(obj: dict[str, Any]) -> Iterator[tuple[str, Any, bool, int | None]]:
    """Yield (call_id, output, is_error, explicit_exit_code)."""
    payload = obj.get("payload")
    if isinstance(payload, dict) and payload.get("type") in {
        "function_call_output",
        "custom_tool_call_output",
    }:
        call_id = payload.get("call_id") or payload.get("id")
        if call_id:
            yield (
                str(call_id),
                payload.get("output", payload.get("content")),
                bool(payload.get("is_error", False)),
                payload.get("exit_code"),
            )

    message = obj.get("message")
    if isinstance(message, dict):
        content = message.get("content")
        if isinstance(content, list):
            for block in content:
                if not isinstance(block, dict) or block.get("type") != "tool_result":
                    continue
                call_id = block.get("tool_use_id") or block.get("call_id")
                if call_id:
                    explicit_exit: int | None = None
                    rich = obj.get("toolUseResult")
                    if isinstance(rich, dict):
                        for key in ("exitCode", "exit_code", "code"):
                            if isinstance(rich.get(key), int):
                                explicit_exit = int(rich[key])
                                break
                    yield (
                        str(call_id),
                        block.get("content", rich),
                        bool(block.get("is_error", False)),
                        explicit_exit,
                    )


def load_projected(input_dir: Path) -> tuple[list[Call], list[dict[str, Any]], int]:
    calls: list[Call] = []
    corpus_rows: list[dict[str, Any]] = []
    duplicate_transport_files = len(list(input_dir.glob("*.json.gz")))
    call_keys: set[tuple[str, str]] = set()
    duplicate_calls = 0

    for path in sorted(input_dir.glob("*.json")):
        with path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
        project = intern_str(data.get("repository") or path.stem)
        project_events = data.get("events") or []
        project_start = len(calls)
        for event in project_events:
            source_file = intern_str(event.get("source_file"))
            call_id = intern_str(event.get("source_call_id"))
            key = (source_file, call_id)
            if key in call_keys:
                duplicate_calls += 1
                continue
            call_keys.add(key)
            tool = intern_str(event.get("tool_name"))
            category = intern_str(event.get("category"))
            command = str(event.get("command") or "")
            actions = event.get("actions") or []
            op = intern_str(classify_operation(tool, category, command, actions))
            stream = intern_str(event.get("source_stream_id") or event.get("session_id"))
            source_agent = str(event.get("source_agent_id") or event.get("source_role") or "root")
            lane = intern_str(f"{stream}|{source_agent}")
            calls.append(
                Call(
                    idx=len(calls),
                    project=project,
                    vendor=intern_str(event.get("vendor")),
                    source_file=source_file,
                    source_call_id=call_id,
                    native_session_id=intern_str(
                        event.get("native_session_id") or event.get("session_id")
                    ),
                    stream_id=stream,
                    lane_id=lane,
                    prompt_index=int(event.get("prompt_index") or 0),
                    source_ordinal=int(event.get("source_tool_ordinal") or 0),
                    ts_ms=int(event.get("ts_ms") or 0),
                    tool_name=tool,
                    category=category,
                    command=command,
                    command_norm=canonical_command(command),
                    command_name=intern_str(event.get("command_name")),
                    op=op,
                    pop=intern_str(pattern_op(op)),
                    targets=event_targets(event),
                    status=intern_str(event.get("status")),
                )
            )
        corpus_rows.append(
            {
                "project": project,
                "projected_calls": len(calls) - project_start,
                "native_sessions": data.get("session_count", 0),
                "candidate_sessions": data.get("candidate_session_count", 0),
                "parsed_sessions": data.get("parsed_session_count", 0),
                "source_events": data.get("source_event_count", 0),
                "file_actions": data.get("file_action_count", 0),
                "start_ms": data.get("start_ms", ""),
                "end_ms": data.get("end_ms", ""),
                "projected_json": str(path.relative_to(REPO_ROOT)),
            }
        )
        del data

    if duplicate_calls:
        print(f"warning: suppressed {duplicate_calls} duplicate (source_file, call_id) rows")
    print(
        f"loaded {len(calls):,} unique projected calls from {len(corpus_rows)} projects; "
        f"ignored {duplicate_transport_files} .json.gz transport copies"
    )
    return calls, corpus_rows, duplicate_calls


def enrich_native(calls: list[Call]) -> dict[str, Any]:
    by_key: dict[tuple[str, str], Call] = {
        (call.source_file, call.source_call_id): call for call in calls
    }
    sources = sorted({call.source_file for call in calls})
    existing = [source for source in sources if Path(source).is_file()]
    missing = [source for source in sources if not Path(source).is_file()]
    parse_errors = 0
    starts = 0
    outputs = 0

    for source_no, source in enumerate(existing, 1):
        if source_no % 100 == 0:
            print(f"native enrichment: {source_no}/{len(existing)} source files", flush=True)
        try:
            handle = Path(source).open("r", encoding="utf-8", errors="replace")
        except OSError:
            continue
        with handle:
            for line in handle:
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError:
                    parse_errors += 1
                    continue
                timestamp_ms = parse_ts_ms(obj.get("timestamp"))
                for call_id, _name, input_value, batch_id in raw_start_records(obj):
                    call = by_key.get((source, call_id))
                    if call is None:
                        continue
                    call.raw_matched = True
                    call.start_ms = timestamp_ms if timestamp_ms is not None else call.ts_ms
                    call.batch_id = intern_str(batch_id)
                    normalized_input = to_text(input_value).encode("utf-8")
                    call.raw_input_hash = (
                        hashlib.sha256(normalized_input).hexdigest()[:20]
                        if normalized_input
                        else ""
                    )
                    if call.op == "mutate":
                        call.mutation_payload_bytes = mutation_payload_size(input_value)
                        call.mutation_context_line_hashes = (
                            mutation_context_line_hashes(input_value)
                        )
                    if call.op == "wait":
                        call.wait_handle, call.wait_passive = wait_metadata(
                            call.tool_name, input_value
                        )
                    starts += 1
                for call_id, output_value, is_error, explicit_exit in raw_output_records(obj):
                    call = by_key.get((source, call_id))
                    if call is None:
                        continue
                    text = to_text(output_value)
                    encoded = text.encode("utf-8")
                    call.raw_matched = True
                    call.end_ms = timestamp_ms
                    call.output_bytes = len(encoded)
                    call.output_hash = hashlib.sha256(encoded).hexdigest()[:20] if encoded else ""
                    call.is_error = call.is_error or is_error
                    call.error_signature = normalized_error_signature(text)
                    call.no_progress = bool(NO_PROGRESS_RE.search(text))
                    if call.op in {"search", "navigate", "read"}:
                        call.output_paths = output_path_tokens(text)
                    if call.op == "read":
                        call.output_line_hashes = content_line_hashes(text)
                    exit_code: int | None = None
                    if isinstance(explicit_exit, int):
                        exit_code = explicit_exit
                    if exit_code is None:
                        match = EXIT_CODE_RE.search(text)
                        if match:
                            exit_code = int(match.group(1))
                    call.exit_code = exit_code
                    if call.start_ms is not None and timestamp_ms is not None:
                        call.duration_ms = max(0, timestamp_ms - call.start_ms)
                    elif (wall_match := WALL_TIME_RE.search(text)):
                        call.duration_ms = int(float(wall_match.group(1)) * 1000)
                    outputs += 1

    # Projected ts_ms is the native call timestamp.  Use it if the start record
    # was not found, but never claim a duration without an output timestamp.
    for call in calls:
        if call.start_ms is None:
            call.start_ms = call.ts_ms
        if call.duration_ms is None and call.end_ms is not None:
            call.duration_ms = max(0, call.end_ms - call.start_ms)

    summary = {
        "unique_native_source_files": len(sources),
        "existing_native_source_files": len(existing),
        "missing_native_source_files": len(missing),
        "native_source_bytes": sum(Path(source).stat().st_size for source in existing),
        "jsonl_parse_errors": parse_errors,
        "matched_start_records": starts,
        "matched_output_records": outputs,
        "matched_calls": sum(call.raw_matched for call in calls),
        "duration_calls": sum(call.duration_ms is not None for call in calls),
        "result_byte_calls": sum(call.output_bytes > 0 for call in calls),
    }
    print(
        "native coverage: "
        f"{summary['matched_calls']:,}/{len(calls):,} calls matched, "
        f"{summary['duration_calls']:,} durations, "
        f"{len(existing)}/{len(sources)} source files present"
    )
    return summary


def episode_key(call: Call) -> tuple[str, str, str, int]:
    return (call.project, call.native_session_id, call.lane_id, call.prompt_index)


def build_episodes(calls: list[Call]) -> dict[tuple[str, str, str, int], list[Call]]:
    episodes: dict[tuple[str, str, str, int], list[Call]] = collections.defaultdict(list)
    for call in calls:
        episodes[episode_key(call)].append(call)
    for rows in episodes.values():
        rows.sort(key=lambda call: (call.start_ms or call.ts_ms, call.source_ordinal, call.idx))
        frontier_end: int | None = None
        for call in rows:
            start = call.start_ms or call.ts_ms
            if frontier_end is not None and start >= frontier_end:
                call.model_gap_ms = start - frontier_end
            elif frontier_end is not None:
                call.model_gap_ms = 0
            if call.end_ms is not None:
                frontier_end = max(frontier_end or call.end_ms, call.end_ms)
            else:
                frontier_end = max(frontier_end or start, start)
    return episodes


def path_flow(prev: Call, curr: Call) -> bool:
    if not prev.output_paths or not curr.targets:
        return False
    output_paths = exact_targets(prev.output_paths)
    current_paths = exact_targets(curr.targets)
    if output_paths & current_paths:
        return True
    # Allow rooted-vs-relative agreement only when at least two path
    # components match; never use a basename alone.
    return any(
        ("/" in left and right.endswith("/" + left))
        or ("/" in right and left.endswith("/" + right))
        for left in output_paths
        for right in current_paths
    )


def shared_targets(left: Call, right: Call) -> bool:
    if not left.targets or not right.targets:
        return False
    return bool(exact_targets(left.targets) & exact_targets(right.targets))


def read_to_edit_content_evidence(prev: Call, curr: Call) -> bool:
    if prev.op != "read" or curr.op != "mutate" or not shared_targets(prev, curr):
        return False
    return bool(
        set(prev.output_line_hashes) & set(curr.mutation_context_line_hashes)
    )


def adjacent_dependency(prev: Call, curr: Call) -> str:
    prev_end = prev.end_ms
    curr_start = curr.start_ms or curr.ts_ms
    if prev_end is not None and curr_start < prev_end:
        return "no_dynamic_result_dependency_concurrent"
    if curr.op == "wait" and prev.op in {"wait", "shell", "delegate"}:
        return "strong_control_dependency"
    if path_flow(prev, curr):
        return "strong_result_path_dependency"
    if shared_targets(prev, curr):
        if prev.op == "read" and curr.op == "mutate":
            if read_to_edit_content_evidence(prev, curr):
                return "observed_read_content_in_edit_context"
            return "same_exact_artifact_read_edit_proxy"
        if prev.op == "mutate":
            return "strong_same_artifact_state_dependency"
        if prev.failed and prev.command_norm == curr.command_norm:
            return "strong_retry_feedback_dependency"
    if prev.op == "mutate" and curr.op == "validate":
        return "strong_workspace_state_dependency"
    if prev.failed and (
        prev.command_norm == curr.command_norm or prev.op == curr.op
    ):
        return "strong_retry_feedback_dependency"
    if (
        prev.op == "read"
        and curr.op == "read"
        and prev.targets
        and curr.targets
        and not shared_targets(prev, curr)
        and not path_flow(prev, curr)
    ):
        if prev.batch_id and prev.batch_id == curr.batch_id:
            return "already_batched_disjoint_local_reads"
        return "likely_independent_sequential_local_reads"
    return "unknown_semantic_dependency"


def dependency_is_strong(label: str) -> bool:
    return label.startswith("strong_") or label == "observed_read_content_in_edit_context"


def dependency_is_parallel_candidate(label: str) -> bool:
    return label in {
        "no_dynamic_result_dependency_concurrent",
        "already_batched_disjoint_local_reads",
        "likely_independent_sequential_local_reads",
    }


def observed_serial_depth(rows: Sequence[Call]) -> int:
    if not rows:
        return 0
    # Linear-time longest path for the dependency grammar.  The previous
    # implementation compared every pair and became quadratic in unusually
    # long prompt episodes.
    depth = [1] * len(rows)
    last_read_info: dict[str, tuple[int, frozenset[str]]] = {}
    last_mutation_depth: dict[str, int] = {}
    result_path_depth: dict[str, int] = {}
    last_workspace_mutation_depth = 0
    for j, row in enumerate(rows):
        targets = exact_targets(row.targets)
        if j and dependency_is_strong(adjacent_dependency(rows[j - 1], row)):
            depth[j] = max(depth[j], depth[j - 1] + 1)
        if row.op == "mutate":
            mutation_context = set(row.mutation_context_line_hashes)
            read_predecessors = [
                read_depth
                for target in targets
                if (
                    (info := last_read_info.get(target))
                    and mutation_context
                    and mutation_context & info[1]
                )
                for read_depth in [info[0]]
            ]
            predecessor = max(
                read_predecessors
                + [last_mutation_depth.get(target, 0) for target in targets]
                + [result_path_depth.get(target, 0) for target in targets]
                + [0]
            )
            if predecessor:
                depth[j] = max(depth[j], predecessor + 1)
        elif row.op == "read":
            predecessor = max(
                [last_mutation_depth.get(target, 0) for target in targets]
                + [result_path_depth.get(target, 0) for target in targets]
                + [0]
            )
            if predecessor:
                depth[j] = max(depth[j], predecessor + 1)
        elif row.op == "validate" and last_workspace_mutation_depth:
            depth[j] = max(depth[j], last_workspace_mutation_depth + 1)

        if row.op == "read":
            hashes = frozenset(row.output_line_hashes)
            for target in targets:
                current = last_read_info.get(target)
                if current is None or depth[j] >= current[0]:
                    last_read_info[target] = (depth[j], hashes)
        if row.op == "mutate":
            for target in targets:
                last_mutation_depth[target] = max(
                    last_mutation_depth.get(target, 0), depth[j]
                )
            last_workspace_mutation_depth = max(
                last_workspace_mutation_depth, depth[j]
            )
        for target in exact_targets(row.output_paths):
            result_path_depth[target] = max(
                result_path_depth.get(target, 0), depth[j]
            )
    return max(depth)


def write_csv(path: Path, rows: Sequence[dict[str, Any]], fields: Sequence[str] | None = None) -> None:
    if fields is None:
        ordered: list[str] = []
        seen: set[str] = set()
        for row in rows:
            for key in row:
                if key not in seen:
                    seen.add(key)
                    ordered.append(key)
        fields = ordered
    temp_path = path.with_suffix(path.suffix + ".tmp")
    with temp_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(fields), extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            cleaned = {
                key: (
                    f"{value:.6f}"
                    if isinstance(value, float)
                    else value
                )
                for key, value in row.items()
            }
            writer.writerow(cleaned)
    os.replace(temp_path, path)


def operation_profile(calls: list[Call]) -> list[dict[str, Any]]:
    groups: dict[tuple[str, str, str], list[Call]] = collections.defaultdict(list)
    for call in calls:
        groups[("all", "all", call.op)].append(call)
        groups[(call.project, "all", call.op)].append(call)
        groups[("all", call.vendor, call.op)].append(call)
    rows: list[dict[str, Any]] = []
    total = len(calls)
    for (project, vendor, op), group in sorted(groups.items()):
        durations = [call.duration_ms for call in group if call.duration_ms is not None]
        gaps = [call.model_gap_ms for call in group if call.model_gap_ms is not None]
        rows.append(
            {
                "project": project,
                "vendor": vendor,
                "operation": op,
                "calls": len(group),
                "share_all_calls": safe_div(len(group), total),
                "raw_matched_calls": sum(call.raw_matched for call in group),
                "duration_coverage": safe_div(len(durations), len(group)),
                "tool_runtime_sum_ms": sum(durations),
                "tool_runtime_median_ms": q(durations, 0.5),
                "tool_runtime_p95_ms": q(durations, 0.95),
                "tool_runtime_p99_ms": q(durations, 0.99),
                "tool_runtime_max_ms": max(durations, default=0),
                "model_gap_sum_ms": sum(gaps),
                "model_gap_median_ms": q(gaps, 0.5),
                "model_gap_p95_ms": q(gaps, 0.95),
                "model_gap_p99_ms": q(gaps, 0.99),
                "model_gap_max_ms": max(gaps, default=0),
                "result_bytes": sum(call.output_bytes for call in group),
                "failed_calls": sum(call.failed for call in group),
                "failure_rate": safe_div(sum(call.failed for call in group), len(group)),
                "no_progress_calls": sum(call.no_progress for call in group),
            }
        )
    return rows


def timeline_profile(
    episodes: dict[tuple[str, str, str, int], list[Call]]
) -> list[dict[str, Any]]:
    groups: dict[str, list[list[Call]]] = collections.defaultdict(list)
    for key, rows in episodes.items():
        groups["all"].append(rows)
        groups[key[0]].append(rows)
    result: list[dict[str, Any]] = []
    for project, episode_groups in sorted(groups.items()):
        busy_ms = 0
        gap_ms = 0
        gaps: list[int] = []
        spans = 0
        covered_episodes = 0
        for rows in episode_groups:
            intervals = sorted(
                (call.start_ms, call.end_ms)
                for call in rows
                if call.start_ms is not None
                and call.end_ms is not None
                and call.end_ms >= call.start_ms
            )
            if not intervals:
                continue
            covered_episodes += 1
            cur_start, cur_end = intervals[0]
            first_start = cur_start
            for start, end in intervals[1:]:
                if start <= cur_end:
                    cur_end = max(cur_end, end)
                else:
                    busy_ms += cur_end - cur_start
                    gap = start - cur_end
                    gap_ms += gap
                    gaps.append(gap)
                    cur_start, cur_end = start, end
            busy_ms += cur_end - cur_start
            spans += cur_end - first_start
        result.append(
            {
                "project": project,
                "episodes": len(episode_groups),
                "timing_covered_episodes": covered_episodes,
                "within_episode_span_ms": spans,
                "tool_busy_union_ms": busy_ms,
                "between_tool_model_gap_ms": gap_ms,
                "tool_busy_share": safe_div(busy_ms, spans),
                "model_gap_share": safe_div(gap_ms, spans),
                "gap_count": len(gaps),
                "gap_median_ms": q(gaps, 0.5),
                "gap_p95_ms": q(gaps, 0.95),
                "gap_p99_ms": q(gaps, 0.99),
                "gap_max_ms": max(gaps, default=0),
                "gaps_over_5min": sum(gap > 300_000 for gap in gaps),
                "gaps_over_1h": sum(gap > 3_600_000 for gap in gaps),
                "gap_sum_capped_5min_ms": sum(min(gap, 300_000) for gap in gaps),
                "gap_share_capped_5min": safe_div(
                    sum(min(gap, 300_000) for gap in gaps),
                    busy_ms + sum(min(gap, 300_000) for gap in gaps),
                ),
                "gap_sum_capped_1h_ms": sum(min(gap, 3_600_000) for gap in gaps),
                "gap_share_capped_1h": safe_div(
                    sum(min(gap, 3_600_000) for gap in gaps),
                    busy_ms + sum(min(gap, 3_600_000) for gap in gaps),
                ),
                "note": "raw gaps exclude pre/post episode time and include pauses; capped shares are idle-sensitivity analyses, not pure model latency",
            }
        )
    return result


def dependency_profile(
    episodes: dict[tuple[str, str, str, int], list[Call]]
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    counts: collections.Counter[tuple[str, str, str]] = collections.Counter()
    project_counts: collections.Counter[tuple[str, str, str, str]] = collections.Counter()
    total_edges = 0
    for key, rows in episodes.items():
        for prev, curr in zip(rows, rows[1:]):
            label = adjacent_dependency(prev, curr)
            counts[(prev.op, curr.op, label)] += 1
            project_counts[(key[0], prev.op, curr.op, label)] += 1
            total_edges += 1
    rows: list[dict[str, Any]] = []
    for (prev_op, curr_op, label), count in counts.most_common():
        rows.append(
            {
                "project": "all",
                "previous_operation": prev_op,
                "next_operation": curr_op,
                "dependency_class": label,
                "adjacent_edges": count,
                "share_all_adjacent_edges": safe_div(count, total_edges),
            }
        )
    for (project, prev_op, curr_op, label), count in sorted(project_counts.items()):
        den = sum(
            value for (p, _a, _b, _c), value in project_counts.items() if p == project
        )
        rows.append(
            {
                "project": project,
                "previous_operation": prev_op,
                "next_operation": curr_op,
                "dependency_class": label,
                "adjacent_edges": count,
                "share_all_adjacent_edges": safe_div(count, den),
            }
        )

    summary: list[dict[str, Any]] = []
    for project in ["all"] + sorted({key[0] for key in episodes}):
        local = (
            counts
            if project == "all"
            else collections.Counter(
                {
                    (a, b, label): value
                    for (p, a, b, label), value in project_counts.items()
                    if p == project
                }
            )
        )
        den = sum(local.values())
        classes = collections.Counter()
        for (_a, _b, label), value in local.items():
            if dependency_is_strong(label):
                classes["strong_dependency_proxy"] += value
            elif dependency_is_parallel_candidate(label):
                classes["parallel_candidate"] += value
            else:
                classes["unknown"] += value
        for label, value in classes.items():
            summary.append(
                {
                    "project": project,
                    "dependency_bucket": label,
                    "adjacent_edges": value,
                    "share": safe_div(value, den),
                    "total_adjacent_edges": den,
                }
            )
    return rows, summary


def ilp_profile(
    episodes: dict[tuple[str, str, str, int], list[Call]]
) -> list[dict[str, Any]]:
    aggregates: dict[str, list[dict[str, float]]] = collections.defaultdict(list)
    for key, rows in episodes.items():
        n = len(rows)
        if not n:
            continue
        depth = observed_serial_depth(rows)
        edge_labels = [
            adjacent_dependency(left, right)
            for left, right in zip(rows, rows[1:])
        ]
        parallel_adj = sum(
            dependency_is_parallel_candidate(label) for label in edge_labels
        )
        already_concurrent_adj = sum(
            label == "no_dynamic_result_dependency_concurrent"
            for label in edge_labels
        )
        already_batched_adj = sum(
            label == "already_batched_disjoint_local_reads"
            for label in edge_labels
        )
        sequential_disjoint_adj = sum(
            label == "likely_independent_sequential_local_reads"
            for label in edge_labels
        )
        strong_adj = sum(dependency_is_strong(label) for label in edge_labels)
        metric = {
            "calls": float(n),
            "depth": float(depth),
            "optimistic_parallelism": safe_div(n, depth),
            "parallel_adj": float(parallel_adj),
            "already_concurrent_adj": float(already_concurrent_adj),
            "already_batched_adj": float(already_batched_adj),
            "sequential_disjoint_adj": float(sequential_disjoint_adj),
            "strong_adj": float(strong_adj),
            "edges": float(max(0, n - 1)),
        }
        aggregates["all"].append(metric)
        aggregates[key[0]].append(metric)
    rows: list[dict[str, Any]] = []
    for project, metrics in sorted(aggregates.items()):
        calls = sum(m["calls"] for m in metrics)
        depth = sum(m["depth"] for m in metrics)
        edges = sum(m["edges"] for m in metrics)
        pars = [m["optimistic_parallelism"] for m in metrics]
        rows.append(
            {
                "project": project,
                "episodes": len(metrics),
                "calls": int(calls),
                "observed_strong_dependency_depth_sum": int(depth),
                "work_over_depth_aggregate": safe_div(calls, depth),
                "episode_parallelism_median": q(pars, 0.5),
                "episode_parallelism_p95": q(pars, 0.95),
                "parallel_candidate_adjacent_edges": int(
                    sum(m["parallel_adj"] for m in metrics)
                ),
                "parallel_candidate_edge_share": safe_div(
                    sum(m["parallel_adj"] for m in metrics), edges
                ),
                "already_concurrent_adjacent_edges": int(
                    sum(m["already_concurrent_adj"] for m in metrics)
                ),
                "already_concurrent_edge_share": safe_div(
                    sum(m["already_concurrent_adj"] for m in metrics), edges
                ),
                "already_batched_disjoint_adjacent_edges": int(
                    sum(m["already_batched_adj"] for m in metrics)
                ),
                "already_batched_disjoint_edge_share": safe_div(
                    sum(m["already_batched_adj"] for m in metrics), edges
                ),
                "remaining_sequential_disjoint_adjacent_edges": int(
                    sum(m["sequential_disjoint_adj"] for m in metrics)
                ),
                "remaining_sequential_disjoint_edge_share": safe_div(
                    sum(m["sequential_disjoint_adj"] for m in metrics), edges
                ),
                "strong_dependency_adjacent_edges": int(
                    sum(m["strong_adj"] for m in metrics)
                ),
                "strong_dependency_edge_share": safe_div(
                    sum(m["strong_adj"] for m in metrics), edges
                ),
                "interpretation": "logical optimistic bound under observed/strong dependency proxies; already-concurrent edges are not remaining scheduling opportunity and unknown semantic edges are omitted",
            }
        )
    return rows


@dataclasses.dataclass
class PatternOccurrence:
    name: str
    calls: list[Call]


def maximal_runs(rows: Sequence[Call], predicate: Any) -> Iterator[list[Call]]:
    current: list[Call] = []
    for call in rows:
        if predicate(call):
            current.append(call)
        else:
            if current:
                yield current
            current = []
    if current:
        yield current


def directory_count(rows: Sequence[Call]) -> int:
    dirs: set[str] = set()
    for call in rows:
        for target in call.targets:
            norm = normalize_path(target)
            dirs.add(norm.rsplit("/", 1)[0] if "/" in norm else ".")
    return len(dirs)


def find_named_patterns(
    episodes: dict[tuple[str, str, str, int], list[Call]]
) -> list[PatternOccurrence]:
    occurrences: list[PatternOccurrence] = []
    for rows in episodes.values():
        # Read/read-like bursts and exploratory directory roaming.
        for run in maximal_runs(rows, lambda call: call.op in LOCAL_DISCOVERY_OPS):
            if len(run) >= 2:
                occurrences.append(PatternOccurrence("read_discovery_burst", list(run)))
            if len(run) >= 4 and directory_count(run) >= 3:
                occurrences.append(PatternOccurrence("exploratory_directory_roam", list(run)))

        for run in maximal_runs(rows, lambda call: call.op == "mutate"):
            if len(run) >= 2:
                occurrences.append(PatternOccurrence("edit_burst", list(run)))

        for run in maximal_runs(rows, lambda call: call.op == "wait"):
            if len(run) >= 2:
                occurrences.append(PatternOccurrence("poll_wait_burst", list(run)))

        # Mutation -> validation cycles.
        previous_test = -1
        for j, call in enumerate(rows):
            if call.op != "validate":
                continue
            edits = [i for i in range(previous_test + 1, j) if rows[i].op == "mutate"]
            if edits:
                start = edits[0]
                occurrences.append(
                    PatternOccurrence("edit_to_validation_cycle", list(rows[start : j + 1]))
                )
            previous_test = j

        # Same-artifact read -> edit pairs.
        last_read: dict[str, int] = {}
        for j, call in enumerate(rows):
            if call.op == "read":
                for target in exact_targets(call.targets):
                    last_read[target] = j
            elif call.op == "mutate":
                candidates = [
                    last_read[target]
                    for target in exact_targets(call.targets)
                    if target in last_read
                ]
                if candidates:
                    i = max(candidates)
                    occurrences.append(
                        PatternOccurrence("same_artifact_read_to_edit", [rows[i], rows[j]])
                    )

        # Repeated same-target reads.
        last_target_read: dict[str, int] = {}
        for j, call in enumerate(rows):
            if call.op != "read" or not call.primary_target:
                continue
            target = call.primary_target
            if target in last_target_read:
                i = last_target_read[target]
                occurrences.append(
                    PatternOccurrence("repeat_read_same_target", [rows[i], rows[j]])
                )
            last_target_read[target] = j

        # Validation retry bursts: >=2 tests with no mutation in between.
        last_test_idx: int | None = None
        for j, call in enumerate(rows):
            if call.op == "mutate":
                last_test_idx = None
            elif call.op == "validate":
                if last_test_idx is not None:
                    occurrences.append(
                        PatternOccurrence("validation_retry_no_edit", list(rows[last_test_idx : j + 1]))
                    )
                last_test_idx = j

        # Greedy search -> read -> edit -> test, with bounded intervening calls.
        pos = 0
        while pos < len(rows):
            try:
                i = next(
                    idx for idx in range(pos, len(rows)) if rows[idx].op == "search"
                )
            except StopIteration:
                break
            read_idx = next(
                (idx for idx in range(i + 1, min(len(rows), i + 7)) if rows[idx].op == "read"),
                None,
            )
            edit_idx = (
                next(
                    (
                        idx
                        for idx in range((read_idx or i) + 1, min(len(rows), (read_idx or i) + 10))
                        if rows[idx].op == "mutate"
                    ),
                    None,
                )
                if read_idx is not None
                else None
            )
            test_idx = (
                next(
                    (
                        idx
                        for idx in range((edit_idx or i) + 1, min(len(rows), (edit_idx or i) + 13))
                        if rows[idx].op == "validate"
                    ),
                    None,
                )
                if edit_idx is not None
                else None
            )
            if read_idx is not None and edit_idx is not None and test_idx is not None:
                occurrences.append(
                    PatternOccurrence(
                        "grep_read_edit_test_bounded", list(rows[i : test_idx + 1])
                    )
                )
                pos = test_idx + 1
            else:
                pos = i + 1
    return occurrences


def aggregate_named_patterns(
    occurrences: list[PatternOccurrence], total_calls: int
) -> list[dict[str, Any]]:
    groups: dict[tuple[str, str], list[PatternOccurrence]] = collections.defaultdict(list)
    for occurrence in occurrences:
        project = occurrence.calls[0].project
        groups[("all", occurrence.name)].append(occurrence)
        groups[(project, occurrence.name)].append(occurrence)
    rows: list[dict[str, Any]] = []
    for (project, name), group in sorted(groups.items()):
        covered = {call.idx for occurrence in group for call in occurrence.calls}
        lengths = [len(occurrence.calls) for occurrence in group]
        depths = [observed_serial_depth(occurrence.calls) for occurrence in group]
        strong_edges = 0
        content_evidence_edges = 0
        same_artifact_proxy_edges = 0
        already_concurrent_edges = 0
        already_batched_edges = 0
        sequential_disjoint_edges = 0
        unknown_edges = 0
        runtime_ms = 0
        model_gap_ms = 0
        for occurrence in group:
            runtime_ms += sum(
                call.duration_ms or 0 for call in occurrence.calls
            )
            model_gap_ms += sum(
                call.model_gap_ms or 0 for call in occurrence.calls[1:]
            )
            for left, right in zip(occurrence.calls, occurrence.calls[1:]):
                label = adjacent_dependency(left, right)
                if dependency_is_strong(label):
                    strong_edges += 1
                    content_evidence_edges += int(
                        label == "observed_read_content_in_edit_context"
                    )
                elif label == "same_exact_artifact_read_edit_proxy":
                    same_artifact_proxy_edges += 1
                elif label == "no_dynamic_result_dependency_concurrent":
                    already_concurrent_edges += 1
                elif label == "already_batched_disjoint_local_reads":
                    already_batched_edges += 1
                elif label == "likely_independent_sequential_local_reads":
                    sequential_disjoint_edges += 1
                else:
                    unknown_edges += 1
        rows.append(
            {
                "project": project,
                "pattern": name,
                "occurrences": len(group),
                "unique_calls_covered": len(covered),
                "share_all_calls": safe_div(len(covered), total_calls),
                "calls_per_occurrence_mean": statistics.fmean(lengths),
                "calls_per_occurrence_median": q(lengths, 0.5),
                "calls_per_occurrence_p95": q(lengths, 0.95),
                "observed_serial_depth_mean": statistics.fmean(depths),
                "observed_serial_depth_median": q(depths, 0.5),
                "observed_serial_depth_p95": q(depths, 0.95),
                "work_over_depth_mean": statistics.fmean(
                    safe_div(length, depth) for length, depth in zip(lengths, depths)
                ),
                "strong_dependency_edges": strong_edges,
                "parallel_candidate_edges": (
                    already_concurrent_edges
                    + already_batched_edges
                    + sequential_disjoint_edges
                ),
                "observed_read_content_in_edit_context_edges": content_evidence_edges,
                "same_exact_artifact_read_edit_proxy_edges": same_artifact_proxy_edges,
                "already_concurrent_edges": already_concurrent_edges,
                "already_batched_disjoint_local_read_edges": already_batched_edges,
                "sequential_disjoint_local_read_edges": sequential_disjoint_edges,
                "unknown_dependency_edges": unknown_edges,
                "tool_runtime_sum_ms": runtime_ms,
                "model_gap_sum_ms": model_gap_ms,
            }
        )
    rows.sort(key=lambda row: (row["project"] != "all", -row["occurrences"], row["pattern"]))
    return rows


def ngram_profile(
    episodes: dict[tuple[str, str, str, int], list[Call]], total_calls: int
) -> list[dict[str, Any]]:
    occ: dict[tuple[int, tuple[str, ...]], list[list[Call]]] = collections.defaultdict(list)
    for rows in episodes.values():
        for n in (2, 3, 4):
            for i in range(0, max(0, len(rows) - n + 1)):
                gram_rows = list(rows[i : i + n])
                key = (n, tuple(call.pop for call in gram_rows))
                occ[key].append(gram_rows)
    chosen: list[tuple[tuple[int, tuple[str, ...]], list[list[Call]]]] = []
    for n in (2, 3, 4):
        local = [(key, value) for key, value in occ.items() if key[0] == n]
        local.sort(key=lambda item: (-len(item[1]), item[0][1]))
        chosen.extend(local[:25])
    rows: list[dict[str, Any]] = []
    for (n, gram), occurrences in chosen:
        covered = {call.idx for occurrence in occurrences for call in occurrence}
        depths = [observed_serial_depth(occurrence) for occurrence in occurrences]
        edge_labels = [
            adjacent_dependency(left, right)
            for occurrence in occurrences
            for left, right in zip(occurrence, occurrence[1:])
        ]
        rows.append(
            {
                "n": n,
                "pattern": "→".join(gram),
                "occurrences": len(occurrences),
                "unique_calls_covered": len(covered),
                "share_all_calls": safe_div(len(covered), total_calls),
                "occurrence_call_slots": len(occurrences) * n,
                "observed_serial_depth_mean": statistics.fmean(depths),
                "strong_dependency_edge_share": safe_div(
                    sum(dependency_is_strong(label) for label in edge_labels),
                    len(edge_labels),
                ),
                "parallel_candidate_edge_share": safe_div(
                    sum(dependency_is_parallel_candidate(label) for label in edge_labels),
                    len(edge_labels),
                ),
                "already_concurrent_edge_share": safe_div(
                    sum(
                        label == "no_dynamic_result_dependency_concurrent"
                        for label in edge_labels
                    ),
                    len(edge_labels),
                ),
                "already_batched_disjoint_local_read_edge_share": safe_div(
                    sum(
                        label == "already_batched_disjoint_local_reads"
                        for label in edge_labels
                    ),
                    len(edge_labels),
                ),
                "sequential_disjoint_local_read_edge_share": safe_div(
                    sum(
                        label == "likely_independent_sequential_local_reads"
                        for label in edge_labels
                    ),
                    len(edge_labels),
                ),
                "unknown_dependency_edge_share": safe_div(
                    sum(
                        not dependency_is_strong(label)
                        and not dependency_is_parallel_candidate(label)
                        for label in edge_labels
                    ),
                    len(edge_labels),
                ),
            }
        )
    return rows


def transitions_for_sessions(
    episodes: dict[tuple[str, str, str, int], list[Call]]
) -> dict[str, dict[str, list[tuple[Call, Call]]]]:
    by_project_session: dict[str, dict[str, list[tuple[Call, Call]]]] = collections.defaultdict(
        lambda: collections.defaultdict(list)
    )
    for key, rows in episodes.items():
        for left, right in zip(rows, rows[1:]):
            by_project_session[key[0]][key[1]].append((left, right))
    return by_project_session


def prefetch_profile(
    episodes: dict[tuple[str, str, str, int], list[Call]]
) -> list[dict[str, Any]]:
    by_project_session = transitions_for_sessions(episodes)
    rows: list[dict[str, Any]] = []

    def context(call: Call, kind: str) -> str:
        if kind == "op":
            return call.op
        return f"{call.op}|{call.primary_target or '__NO_TARGET__'}"

    for project in ["all"] + sorted(by_project_session):
        if project == "all":
            train_edges: list[tuple[Call, Call]] = []
            test_edges: list[tuple[Call, Call]] = []
            for project_name, sessions in sorted(by_project_session.items()):
                project_items = list(sessions.items())
                project_items.sort(
                    key=lambda item: min(
                        (edge[0].start_ms or edge[0].ts_ms) for edge in item[1]
                    )
                )
                split = max(1, int(len(project_items) * 0.8))
                train_edges.extend(
                    edge for _sid, edges in project_items[:split] for edge in edges
                )
                test_edges.extend(
                    edge for _sid, edges in project_items[split:] for edge in edges
                )
        else:
            session_items = list(by_project_session[project].items())
            session_items.sort(
                key=lambda item: min(
                    (edge[0].start_ms or edge[0].ts_ms) for edge in item[1]
                )
            )
            split = max(1, int(len(session_items) * 0.8))
            train_edges = [
                edge for _sid, edges in session_items[:split] for edge in edges
            ]
            test_edges = [
                edge for _sid, edges in session_items[split:] for edge in edges
            ]
        full_edges = train_edges + test_edges
        for context_kind in ("op", "op_target"):
            full_read_counts: dict[str, collections.Counter[str]] = collections.defaultdict(
                collections.Counter
            )
            train_read_counts: dict[str, collections.Counter[str]] = collections.defaultdict(
                collections.Counter
            )
            train_next_counts: dict[str, collections.Counter[str]] = collections.defaultdict(
                collections.Counter
            )
            for left, right in full_edges:
                if right.op == "read" and right.primary_target:
                    full_read_counts[context(left, context_kind)][right.primary_target] += 1
            for left, right in train_edges:
                ctx = context(left, context_kind)
                outcome = (
                    f"READ:{right.primary_target}"
                    if right.op == "read" and right.primary_target
                    else "__NONE__"
                )
                train_next_counts[ctx][outcome] += 1
                if right.op == "read" and right.primary_target:
                    train_read_counts[ctx][right.primary_target] += 1

            eligible_full = sum(sum(counter.values()) for counter in full_read_counts.values())
            for top_k in (1, 3):
                ceiling_hits = sum(
                    sum(count for _target, count in counter.most_common(top_k))
                    for counter in full_read_counts.values()
                )
                rows.append(
                    {
                        "project": project,
                        "split": "in_sample_ceiling",
                        "context": context_kind,
                        "top_k": top_k,
                        "policy_threshold": "",
                        "train_transitions": len(full_edges),
                        "test_transitions": len(full_edges),
                        "eligible_next_reads": eligible_full,
                        "contexts_seen": len(full_read_counts),
                        "prefetches_issued": "",
                        "exact_path_hits": ceiling_hits,
                        "hit_rate_over_next_reads": safe_div(ceiling_hits, eligible_full),
                        "precision_per_prefetch": "",
                        "runtime_hidden_upper_ms": "",
                        "roundtrips_eliminated_transparent_cache": 0,
                        "roundtrips_eliminated_fused_upper": ceiling_hits,
                    }
                )

            # Held-out conditional ceiling: oracle says the next call is a read.
            for top_k in (1, 3):
                eligible = 0
                hits = 0
                hidden = 0
                seen = 0
                issued = 0
                for left, right in test_edges:
                    if right.op != "read" or not right.primary_target:
                        continue
                    eligible += 1
                    counter = train_read_counts.get(context(left, context_kind))
                    if not counter:
                        continue
                    seen += 1
                    predictions = [target for target, _n in counter.most_common(top_k)]
                    issued += len(predictions)
                    if right.primary_target in predictions:
                        hits += 1
                        hidden += right.duration_ms or 0
                rows.append(
                    {
                        "project": project,
                        "split": "chronological_80_20_conditional",
                        "context": context_kind,
                        "top_k": top_k,
                        "policy_threshold": "oracle_next_is_read",
                        "train_transitions": len(train_edges),
                        "test_transitions": len(test_edges),
                        "eligible_next_reads": eligible,
                        "contexts_seen": seen,
                        "prefetches_issued": issued,
                        "exact_path_hits": hits,
                        "hit_rate_over_next_reads": safe_div(hits, eligible),
                        "precision_per_prefetch": safe_div(hits, issued),
                        "runtime_hidden_upper_ms": hidden,
                        "roundtrips_eliminated_transparent_cache": 0,
                        "roundtrips_eliminated_fused_upper": hits,
                    }
                )

            # Actionable policy must decide whether a read will happen.
            for threshold in (0.25, 0.5, 0.75):
                eligible = sum(
                    right.op == "read" and bool(right.primary_target)
                    for _left, right in test_edges
                )
                issued = 0
                hits = 0
                hidden = 0
                seen = 0
                for left, right in test_edges:
                    ctx = context(left, context_kind)
                    next_counter = train_next_counts.get(ctx)
                    target_counter = train_read_counts.get(ctx)
                    if not next_counter or not target_counter:
                        continue
                    seen += 1
                    read_n = sum(
                        count
                        for outcome, count in next_counter.items()
                        if outcome.startswith("READ:")
                    )
                    p_read = safe_div(read_n, sum(next_counter.values()))
                    if p_read < threshold:
                        continue
                    issued += 1
                    prediction = target_counter.most_common(1)[0][0]
                    if right.op == "read" and right.primary_target == prediction:
                        hits += 1
                        hidden += right.duration_ms or 0
                rows.append(
                    {
                        "project": project,
                        "split": "chronological_80_20_actionable",
                        "context": context_kind,
                        "top_k": 1,
                        "policy_threshold": threshold,
                        "train_transitions": len(train_edges),
                        "test_transitions": len(test_edges),
                        "eligible_next_reads": eligible,
                        "contexts_seen": seen,
                        "prefetches_issued": issued,
                        "exact_path_hits": hits,
                        "hit_rate_over_next_reads": safe_div(hits, eligible),
                        "precision_per_prefetch": safe_div(hits, issued),
                        "runtime_hidden_upper_ms": hidden,
                        "roundtrips_eliminated_transparent_cache": 0,
                        "roundtrips_eliminated_fused_upper": hits,
                    }
                )
    return rows


def speculation_profile(
    episodes: dict[tuple[str, str, str, int], list[Call]]
) -> list[dict[str, Any]]:
    cycle_rows: list[dict[str, Any]] = []
    last_test_command_by_lane: dict[tuple[str, str], str] = {}
    ordered_episodes = sorted(
        episodes.items(),
        key=lambda item: min(call.start_ms or call.ts_ms for call in item[1]),
    )
    for key, rows in ordered_episodes:
        previous_test = -1
        for j, test in enumerate(rows):
            if test.op != "validate":
                continue
            edits = [call for call in rows[previous_test + 1 : j] if call.op == "mutate"]
            lane_key = (test.project, test.lane_id)
            predicted = last_test_command_by_lane.get(lane_key, "")
            predictor_hit = bool(predicted and predicted == test.command_norm)
            last_test_command_by_lane[lane_key] = test.command_norm
            if edits:
                last_edit = edits[-1]
                if (
                    last_edit.end_ms is not None
                    and test.start_ms is not None
                    and test.duration_ms is not None
                ):
                    launch_gap = max(0, test.start_ms - last_edit.end_ms)
                    saved = min(launch_gap, test.duration_ms)
                else:
                    launch_gap = 0
                    saved = 0
                intervening = rows[rows.index(last_edit) + 1 : j]
                cycle_rows.append(
                    {
                        "project": test.project,
                        "edit_count": len(edits),
                        "intervening_calls_after_last_edit": len(intervening),
                        "test_failed": int(test.failed),
                        "test_duration_ms": test.duration_ms or 0,
                        "launch_gap_ms": launch_gap,
                        "perfect_command_saved_ms": saved,
                        "last_test_command_predictor_hit": int(predictor_hit),
                        "predicted_saved_ms": saved if predictor_hit else 0,
                        "eager_after_every_edit_executions": len(edits),
                        "eager_after_every_edit_wasted_executions": max(0, len(edits) - 1),
                        "eager_wasted_runtime_estimate_ms": max(0, len(edits) - 1)
                        * (test.duration_ms or 0),
                    }
                )
            previous_test = j

    result: list[dict[str, Any]] = []
    for project in ["all"] + sorted({row["project"] for row in cycle_rows}):
        group = (
            cycle_rows
            if project == "all"
            else [row for row in cycle_rows if row["project"] == project]
        )
        if not group:
            continue
        result.append(
            {
                "project": project,
                "mutation_validation_cycles": len(group),
                "tests_failed": sum(row["test_failed"] for row in group),
                "test_failure_rate": safe_div(
                    sum(row["test_failed"] for row in group), len(group)
                ),
                "tests_with_timing": sum(row["test_duration_ms"] > 0 for row in group),
                "test_runtime_sum_ms": sum(row["test_duration_ms"] for row in group),
                "intervening_calls_after_last_edit_sum": sum(
                    row["intervening_calls_after_last_edit"] for row in group
                ),
                "cycles_with_overlap_opportunity": sum(
                    row["perfect_command_saved_ms"] > 0 for row in group
                ),
                "perfect_command_runtime_hidden_ms": sum(
                    row["perfect_command_saved_ms"] for row in group
                ),
                "last_test_command_predictor_hits": sum(
                    row["last_test_command_predictor_hit"] for row in group
                ),
                "last_test_command_predictor_hit_rate": safe_div(
                    sum(row["last_test_command_predictor_hit"] for row in group),
                    len(group),
                ),
                "predictor_weighted_runtime_hidden_ms": sum(
                    row["predicted_saved_ms"] for row in group
                ),
                "eager_after_every_edit_executions": sum(
                    row["eager_after_every_edit_executions"] for row in group
                ),
                "eager_after_every_edit_wasted_executions": sum(
                    row["eager_after_every_edit_wasted_executions"] for row in group
                ),
                "eager_waste_rate": safe_div(
                    sum(row["eager_after_every_edit_wasted_executions"] for row in group),
                    sum(row["eager_after_every_edit_executions"] for row in group),
                ),
                "eager_wasted_runtime_estimate_ms": sum(
                    row["eager_wasted_runtime_estimate_ms"] for row in group
                ),
                "transparent_roundtrips_eliminated": 0,
                "fused_roundtrips_eliminated_upper": sum(
                    row["last_test_command_predictor_hit"]
                    and row["perfect_command_saved_ms"] > 0
                    for row in group
                ),
            }
        )
    return result


def incremental_profile(calls: list[Call]) -> list[dict[str, Any]]:
    metrics: collections.defaultdict[
        tuple[str, str], collections.Counter[str]
    ] = collections.defaultdict(collections.Counter)

    by_project: dict[str, list[Call]] = collections.defaultdict(list)
    for call in calls:
        by_project[call.project].append(call)
    for project, rows in by_project.items():
        rows.sort(key=lambda call: (call.start_ms or call.ts_ms, call.idx))
        workspace_epoch = 0
        path_epoch: collections.Counter[str] = collections.Counter()
        path_payload: collections.Counter[str] = collections.Counter()
        last_read: dict[tuple[str, str], tuple[int, int, int, str]] = {}
        last_command: dict[tuple[str, str, str], tuple[int, str, int]] = {}
        for call in rows:
            call.workspace_epoch = workspace_epoch
            if call.op == "read" and call.primary_target:
                target = call.primary_target
                key = (call.lane_id, target)
                if key in last_read:
                    prev_epoch, prev_payload, prev_bytes, prev_hash = last_read[key]
                    changed = path_epoch[target] != prev_epoch
                    kind = (
                        "read_same_target_after_observed_mutation"
                        if changed
                        else "read_same_target_no_observed_mutation"
                    )
                    for scope in ("all", project):
                        counter = metrics[(scope, kind)]
                        counter["opportunities"] += 1
                        counter["external_executions_avoidable_upper"] += int(not changed)
                        counter["result_bytes_avoidable"] += call.output_bytes if not changed else 0
                        counter["identical_output_repeats"] += int(
                            bool(prev_hash and call.output_hash == prev_hash)
                        )
                        if changed and call.output_bytes:
                            delta_payload = max(0, path_payload[target] - prev_payload)
                            counter["incremental_bytes_upper_saved"] += max(
                                0, call.output_bytes - delta_payload
                            )
                            counter["full_result_bytes"] += call.output_bytes
                            counter["changed_payload_proxy_bytes"] += delta_payload
                last_read[key] = (
                    path_epoch[target],
                    path_payload[target],
                    call.output_bytes,
                    call.output_hash,
                )

            if call.command_norm and call.op not in {"mutate", "delegate", "control", "wait"}:
                invocation_key = call.raw_input_hash or call.command_norm
                key = (call.lane_id, call.op, invocation_key)
                if key in last_command:
                    prev_workspace_epoch, prev_hash, _prev_bytes = last_command[key]
                    unchanged = prev_workspace_epoch == workspace_epoch
                    kind = (
                        f"exact_{call.op}_invocation_no_observed_mutation"
                        if unchanged
                        else f"exact_{call.op}_invocation_after_observed_mutation"
                    )
                    for scope in ("all", project):
                        counter = metrics[(scope, kind)]
                        counter["opportunities"] += 1
                        counter["external_executions_avoidable_upper"] += int(unchanged)
                        counter["result_bytes_avoidable"] += (
                            call.output_bytes if unchanged else 0
                        )
                        counter["identical_output_repeats"] += int(
                            bool(prev_hash and call.output_hash == prev_hash)
                        )
                last_command[key] = (
                    workspace_epoch,
                    call.output_hash,
                    call.output_bytes,
                )

            if call.op == "mutate":
                workspace_epoch += 1
                for target in call.targets:
                    path_epoch[target] += 1
                    path_payload[target] += call.mutation_payload_bytes

    result: list[dict[str, Any]] = []
    for (project, kind), counter in sorted(metrics.items()):
        opportunities = counter["opportunities"]
        result.append(
            {
                "project": project,
                "reuse_class": kind,
                "opportunities": opportunities,
                "external_executions_avoidable_upper": counter[
                    "external_executions_avoidable_upper"
                ],
                "external_execution_avoid_rate_upper": safe_div(
                    counter["external_executions_avoidable_upper"], opportunities
                ),
                "transparent_model_roundtrips_eliminated": 0,
                "fused_model_roundtrips_eliminated_upper": counter[
                    "external_executions_avoidable_upper"
                ],
                "result_bytes_avoidable": counter["result_bytes_avoidable"],
                "identical_output_repeats": counter["identical_output_repeats"],
                "observed_identical_output_reuse_lower": counter[
                    "identical_output_repeats"
                ],
                "incremental_bytes_upper_saved": counter[
                    "incremental_bytes_upper_saved"
                ],
                "full_result_bytes": counter["full_result_bytes"],
                "changed_payload_proxy_bytes": counter[
                    "changed_payload_proxy_bytes"
                ],
                "note": "execution/byte savings are conditional upper bounds requiring a versioned provider; identical-output repeats are the observed reuse lower bound",
            }
        )
    return result


def polling_profile(
    episodes: dict[tuple[str, str, str, int], list[Call]], total_calls: int
) -> list[dict[str, Any]]:
    aggregate: collections.defaultdict[
        tuple[str, str], collections.Counter[str]
    ] = collections.defaultdict(collections.Counter)
    burst_lengths: collections.defaultdict[tuple[str, str], list[int]] = collections.defaultdict(
        list
    )
    qualified_lengths: collections.defaultdict[
        tuple[str, str], list[int]
    ] = collections.defaultdict(list)
    for key, rows in episodes.items():
        for call in rows:
            if call.op != "wait":
                continue
            for scope in ("all", key[0]):
                for tool in (call.tool_name, "__ALL_WAIT_TOOLS__"):
                    counter = aggregate[(scope, tool)]
                    counter["calls"] += 1
                    counter["no_progress"] += int(call.no_progress)
                    counter["runtime_ms"] += call.duration_ms or 0
                    counter["result_bytes"] += call.output_bytes
        for run in maximal_runs(rows, lambda call: call.op == "wait"):
            if len(run) < 2:
                continue
            for scope in ("all", key[0]):
                counter = aggregate[(scope, "__ALL_WAIT_TOOLS__")]
                counter["raw_bursts"] += 1
                counter["raw_structural_saved_upper"] += len(run) - 1
                burst_lengths[(scope, "__ALL_WAIT_TOOLS__")].append(len(run))

        qualified_run: list[Call] = []

        def flush_qualified() -> None:
            nonlocal qualified_run
            if len(qualified_run) >= 2:
                for scope in ("all", key[0]):
                    counter = aggregate[(scope, "__ALL_WAIT_TOOLS__")]
                    counter["qualified_bursts"] += 1
                    counter["qualified_calls"] += len(qualified_run)
                    counter["event_driven_calls_saved"] += len(qualified_run) - 1
                    qualified_lengths[(scope, "__ALL_WAIT_TOOLS__")].append(
                        len(qualified_run)
                    )
            qualified_run = []

        for call in rows:
            qualifies = (
                call.op == "wait"
                and call.wait_passive
                and call.no_progress
                and bool(call.wait_handle)
            )
            if not qualifies:
                flush_qualified()
                continue
            if qualified_run and (
                call.tool_name != qualified_run[-1].tool_name
                or call.wait_handle != qualified_run[-1].wait_handle
            ):
                flush_qualified()
            qualified_run.append(call)
        flush_qualified()
    rows: list[dict[str, Any]] = []
    for (project, tool), counter in sorted(aggregate.items()):
        lengths = burst_lengths[(project, tool)]
        conservative_lengths = qualified_lengths[(project, tool)]
        calls = counter["calls"]
        rows.append(
            {
                "project": project,
                "wait_tool": tool,
                "calls": calls,
                "share_all_calls": safe_div(calls, total_calls),
                "no_progress_results": counter["no_progress"],
                "no_progress_rate": safe_div(
                    counter["no_progress"], calls
                ),
                "runtime_sum_ms": counter["runtime_ms"],
                "result_bytes": counter["result_bytes"],
                "raw_consecutive_wait_family_bursts": counter["raw_bursts"],
                "raw_burst_length_median": q(lengths, 0.5),
                "raw_burst_length_p95": q(lengths, 0.95),
                "raw_structural_calls_saved_upper": counter[
                    "raw_structural_saved_upper"
                ],
                "qualified_same_handle_empty_poll_bursts": counter[
                    "qualified_bursts"
                ],
                "qualified_empty_poll_calls": counter["qualified_calls"],
                "qualified_burst_length_median": q(conservative_lengths, 0.5),
                "qualified_burst_length_p95": q(conservative_lengths, 0.95),
                "event_driven_calls_saved_upper": counter["event_driven_calls_saved"],
                "transparent_roundtrips_eliminated": counter[
                    "event_driven_calls_saved"
                ],
                "note": "qualified upper retains one blocking await per consecutive same-tool, same-handle, passive, no-progress burst; raw structural upper is not actionable",
            }
        )
    return rows


def failure_recovery_profile(
    episodes: dict[tuple[str, str, str, int], list[Call]], total_calls: int
) -> list[dict[str, Any]]:
    aggregate: collections.defaultdict[
        tuple[str, str], collections.Counter[str]
    ] = collections.defaultdict(collections.Counter)
    for key, rows in episodes.items():
        for i, call in enumerate(rows):
            if not call.failed:
                continue
            window = rows[i + 1 : i + 3]
            same_op_retry = next(
                (candidate for candidate in window if candidate.op == call.op), None
            )
            exact_retry = next(
                (
                    candidate
                    for candidate in window
                    if candidate.tool_name == call.tool_name
                    and bool(call.raw_input_hash)
                    and candidate.raw_input_hash == call.raw_input_hash
                ),
                None,
            )
            same_target_retry = next(
                (
                    candidate
                    for candidate in window
                    if bool(exact_targets(call.targets))
                    and bool(
                        exact_targets(call.targets)
                        & exact_targets(candidate.targets)
                    )
                ),
                None,
            )
            for scope in ("all", key[0]):
                counter = aggregate[(scope, call.op)]
                counter["failures"] += 1
                counter["failure_runtime_ms"] += call.duration_ms or 0
                counter["failure_result_bytes"] += call.output_bytes
                if same_op_retry:
                    counter["same_op_retry_within_2"] += 1
                    counter["same_op_retry_succeeded"] += int(
                        not same_op_retry.failed
                    )
                if exact_retry:
                    counter["exact_invocation_retry"] += 1
                    counter["exact_invocation_retry_succeeded"] += int(
                        not exact_retry.failed
                    )
                    counter["same_error_signature_failed_retry"] += int(
                        exact_retry.failed
                        and bool(call.error_signature)
                        and exact_retry.error_signature == call.error_signature
                    )
                if same_target_retry:
                    counter["same_target_retry"] += 1
                    counter["same_target_retry_succeeded"] += int(
                        not same_target_retry.failed
                    )
    rows: list[dict[str, Any]] = []
    for (project, op), counter in sorted(aggregate.items()):
        failures = counter["failures"]
        rows.append(
            {
                "project": project,
                "operation": op,
                "failed_calls": failures,
                "share_all_calls": safe_div(failures, total_calls),
                "same_operation_retry_within_2_calls": counter[
                    "same_op_retry_within_2"
                ],
                "retry_rate": safe_div(counter["same_op_retry_within_2"], failures),
                "same_operation_retry_succeeded": counter[
                    "same_op_retry_succeeded"
                ],
                "same_operation_retry_success_rate": safe_div(
                    counter["same_op_retry_succeeded"],
                    counter["same_op_retry_within_2"],
                ),
                "exact_invocation_retry_within_2_calls": counter[
                    "exact_invocation_retry"
                ],
                "exact_invocation_retry_rate": safe_div(
                    counter["exact_invocation_retry"], failures
                ),
                "exact_invocation_retry_succeeded": counter[
                    "exact_invocation_retry_succeeded"
                ],
                "exact_invocation_retry_success_rate": safe_div(
                    counter["exact_invocation_retry_succeeded"],
                    counter["exact_invocation_retry"],
                ),
                "same_target_retry_within_2_calls": counter["same_target_retry"],
                "same_target_retry_succeeded": counter[
                    "same_target_retry_succeeded"
                ],
                "same_target_retry_success_rate": safe_div(
                    counter["same_target_retry_succeeded"],
                    counter["same_target_retry"],
                ),
                "same_error_signature_failed_exact_retries": counter[
                    "same_error_signature_failed_retry"
                ],
                "failed_tool_runtime_ms": counter["failure_runtime_ms"],
                "failed_result_bytes": counter["failure_result_bytes"],
                "conditional_failure_roundtrips_avoidable_upper": counter[
                    "exact_invocation_retry"
                ],
                "note": "same-operation is descriptive only; conditional upper requires an exact input match and a sound preflight, idempotent retry, or negative cache",
            }
        )
    return rows


def shell_batching_profile(calls: list[Call]) -> list[dict[str, Any]]:
    aggregate: collections.defaultdict[
        tuple[str, str], collections.Counter[str]
    ] = collections.defaultdict(collections.Counter)
    primitive_counts: collections.defaultdict[tuple[str, str], list[int]] = collections.defaultdict(
        list
    )
    for call in calls:
        if call.tool_name.lower() not in SHELL_NAMES and call.category.lower() != "shell":
            continue
        separators = COMPOUND_RE.findall(call.command)
        primitive = 1 + len(separators) if call.command.strip() else 1
        compound = primitive > 1
        for scope in ("all", call.project):
            counter = aggregate[(scope, call.vendor)]
            counter["shell_calls"] += 1
            counter["compound_calls"] += int(compound)
            counter["estimated_primitives"] += primitive
            counter["runtime_ms"] += call.duration_ms or 0
            counter["result_bytes"] += call.output_bytes
            primitive_counts[(scope, call.vendor)].append(primitive)
    rows: list[dict[str, Any]] = []
    for (project, vendor), counter in sorted(aggregate.items()):
        counts = primitive_counts[(project, vendor)]
        rows.append(
            {
                "project": project,
                "vendor": vendor,
                "shell_calls": counter["shell_calls"],
                "compound_shell_calls": counter["compound_calls"],
                "compound_share": safe_div(
                    counter["compound_calls"], counter["shell_calls"]
                ),
                "estimated_shell_primitives": counter["estimated_primitives"],
                "primitives_per_call_mean": safe_div(
                    counter["estimated_primitives"], counter["shell_calls"]
                ),
                "primitives_per_call_median": q(counts, 0.5),
                "primitives_per_call_p95": q(counts, 0.95),
                "runtime_sum_ms": counter["runtime_ms"],
                "result_bytes": counter["result_bytes"],
                "note": "lexical separator count; quoted separators may overcount and pipelines are not split",
            }
        )
    return rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument(
        "--no-native",
        action="store_true",
        help="skip native JSONL enrichment; timing/byte metrics will be unavailable",
    )
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    calls, corpus_rows, duplicate_calls = load_projected(args.input_dir)
    native_summary = (
        {
            "unique_native_source_files": len({call.source_file for call in calls}),
            "existing_native_source_files": 0,
            "missing_native_source_files": 0,
            "native_source_bytes": 0,
            "jsonl_parse_errors": 0,
            "matched_start_records": 0,
            "matched_output_records": 0,
            "matched_calls": 0,
            "duration_calls": 0,
            "result_byte_calls": 0,
        }
        if args.no_native
        else enrich_native(calls)
    )
    episodes = build_episodes(calls)

    total_calls = len(calls)
    for row in corpus_rows:
        project_calls = [call for call in calls if call.project == row["project"]]
        row.update(
            {
                "share_all_calls": safe_div(len(project_calls), total_calls),
                "native_raw_matched_calls": sum(call.raw_matched for call in project_calls),
                "native_duration_calls": sum(
                    call.duration_ms is not None for call in project_calls
                ),
                "native_result_bytes": sum(call.output_bytes for call in project_calls),
                "prompt_episodes": sum(key[0] == row["project"] for key in episodes),
            }
        )
    corpus_rows.append(
        {
            "project": "all",
            "projected_calls": total_calls,
            "native_sessions": sum(int(row["native_sessions"]) for row in corpus_rows),
            "candidate_sessions": sum(int(row["candidate_sessions"]) for row in corpus_rows),
            "parsed_sessions": sum(int(row["parsed_sessions"]) for row in corpus_rows),
            "source_events": sum(int(row["source_events"]) for row in corpus_rows),
            "file_actions": sum(int(row["file_actions"]) for row in corpus_rows),
            "start_ms": min(int(row["start_ms"]) for row in corpus_rows),
            "end_ms": max(int(row["end_ms"]) for row in corpus_rows),
            "projected_json": "six uncompressed .json files; .json.gz copies excluded",
            "share_all_calls": 1.0,
            "native_raw_matched_calls": native_summary["matched_calls"],
            "native_duration_calls": native_summary["duration_calls"],
            "native_result_bytes": sum(call.output_bytes for call in calls),
            "prompt_episodes": len(episodes),
        }
    )

    dep_rows, dep_summary = dependency_profile(episodes)
    named_occurrences = find_named_patterns(episodes)

    outputs: dict[str, list[dict[str, Any]]] = {
        "corpus_summary.csv": corpus_rows,
        "operation_profile.csv": operation_profile(calls),
        "timeline_profile.csv": timeline_profile(episodes),
        "dependency_profile.csv": dep_rows,
        "dependency_summary.csv": dep_summary,
        "ilp_profile.csv": ilp_profile(episodes),
        "transition_patterns.csv": ngram_profile(episodes, total_calls),
        "named_patterns.csv": aggregate_named_patterns(named_occurrences, total_calls),
        "prefetch.csv": prefetch_profile(episodes),
        "speculation.csv": speculation_profile(episodes),
        "incremental.csv": incremental_profile(calls),
        "polling.csv": polling_profile(episodes, total_calls),
        "failure_recovery.csv": failure_recovery_profile(episodes, total_calls),
        "shell_batching.csv": shell_batching_profile(calls),
    }
    for filename, rows in outputs.items():
        write_csv(args.output_dir / filename, rows)
        print(f"wrote {filename}: {len(rows):,} rows")

    input_manifest = []
    for path in sorted(args.input_dir.glob("*.json")):
        stat = path.stat()
        input_manifest.append(
            {
                "path": str(path),
                "size_bytes": stat.st_size,
                "mtime_ns": stat.st_mtime_ns,
                "sha256": file_sha256(path),
            }
        )
    native_manifest_lines = []
    for source in sorted({call.source_file for call in calls}):
        path = Path(source)
        if path.is_file():
            stat = path.stat()
            native_manifest_lines.append(
                f"{source}\0{stat.st_size}\0{stat.st_mtime_ns}"
            )
        else:
            native_manifest_lines.append(f"{source}\0MISSING")
    native_manifest_digest = hashlib.sha256(
        "\n".join(native_manifest_lines).encode("utf-8")
    ).hexdigest()
    csv_manifest = {
        filename: file_sha256(args.output_dir / filename)
        for filename in sorted(outputs)
    }

    metadata = {
        "generated_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "repository_root": str(REPO_ROOT),
        "input_dir": str(args.input_dir),
        "output_dir": str(args.output_dir),
        "projected_json_policy": "read *.json only; ignore duplicate *.json.gz transport copies",
        "total_calls": total_calls,
        "projects": len([row for row in corpus_rows if row["project"] != "all"]),
        "prompt_episodes": len(episodes),
        "suppressed_duplicate_calls": duplicate_calls,
        "native_enrichment": native_summary,
        "reproducibility": {
            "script_sha256": file_sha256(Path(__file__)),
            "input_manifest": input_manifest,
            "native_manifest_digest_sha256": native_manifest_digest,
            "native_manifest_entries": len(native_manifest_lines),
            "csv_sha256": csv_manifest,
            "atomic_csv_replace": True,
        },
        "definitions": {
            "episode": "project × native_session × source lane × prompt_index",
            "model_gap": "gap from the current completed-tool frontier to the next tool start within one prompt episode",
            "strong_dependency": "trace-observed/strong state proxy, not a cognitive semantic gold label",
            "parallel_candidate": "logical union of already-concurrent calls, already-batched disjoint local reads, and still-sequential exact-path-disjoint local reads; only the last is a remaining cross-batch proxy",
            "ilp_bound": "logical work / critical path using strong dependency proxies; includes already-realized concurrency and omits unknown semantic edges, so it is not a remaining speedup claim",
            "roundtrip_accounting": "transparent prefetch/cache saves execution but not model-tool boundary; fused upper bound may remove one boundary per hit",
        },
    }
    metadata_path = args.output_dir / "metadata.json"
    metadata_temp = metadata_path.with_suffix(".json.tmp")
    with metadata_temp.open("w", encoding="utf-8") as handle:
        json.dump(metadata, handle, ensure_ascii=False, indent=2, sort_keys=True)
        handle.write("\n")
    os.replace(metadata_temp, metadata_path)
    print("wrote metadata.json")


if __name__ == "__main__":
    main()
