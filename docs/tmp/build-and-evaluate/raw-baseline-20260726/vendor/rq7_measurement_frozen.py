#!/usr/bin/env python3
"""RQ7 matched measurement-capability experiment.

This is research-only glue over source-native sessions, official ProcGrep, and
the existing agent-session projection.  It deliberately does not introduce a
new product event model.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import hmac
import json
import os
import random
import re
import resource
import signal
import shlex
import shutil
import statistics
import subprocess
import sys
import tempfile
import threading
import time
from collections import Counter, defaultdict
from pathlib import Path, PurePosixPath
from typing import Any, Iterable


SEED = "20260722"
SPEC_VERSION = "native-root-conformance-v3"
FROZEN_SELECTION_SEED = "20260723-heldout-v3-001"
FROZEN_SESSIONS_PER_PROJECT = 6
FROZEN_PROJECT_COUNT = 6
FROZEN_SOURCE_BYTES = 16_777_216
FROZEN_STABILITY_WAIT = 60
FROZEN_DISCOVERY_CUTOFF_NS = 1_784_871_070_206_832_949
FROZEN_PROJECTS_SHA256 = "2de529d002815aefa74b1b8f8164ddf3b78b1e2f8e9e02214d43a9598f49368a"
V0_REVISION = "7e5464eca650428ba238ea3d2c20052bedbbe272"
V0_CARGO_LOCK_SHA256 = "c117357cf567baad5a8867f8def4d43a5f4733f1904d94a2c4cf662243553143"
V0_BINARY_SHA256 = "7f83e0f73fb8ab0b88e1dc257b27ffedd79ceb7ba1e5684b60c4b194773760f0"
EXPECTED_EXCLUSION_SHA256 = {
    "838b814a31be1be48d28040d12235ee16489081f1d7214e8c7e814f8da057e35",
    "2a7148ee78d0a0fadb99c768cbf6bda9fea2dce6e1ce844a8ae953e0fea38767",
}
VENDORS = ("claude", "codex", "gemini")
READ_COMMANDS = {"cat", "sed", "head", "tail", "nl", "less", "more"}
MUTATE_COMMANDS = {"touch", "rm", "mv", "cp"}
PATH_KEYS = {
    "file_path",
    "filepath",
    "path",
    "absolute_path",
    "target_file",
    "notebook_path",
    "old_path",
    "new_path",
}
TEST_RE = re.compile(
    r"(pytest|(^|\s|/)tests?\b|unittest|jest|mocha|vitest|tox|"
    r"go test|cargo test|npm (run )?test|yarn test|make test|gradle test)",
    re.I,
)
VCS_RE = re.compile(r"(^|\s|;|&|\|)(git|gh|hg|svn)\b", re.I)
PKG_RE = re.compile(
    r"\b(pip3?|uv|poetry|pipenv|conda|npm|yarn|pnpm|bundle|gem|cargo|go|apt|apt-get|brew)"
    r"\b[^|;&]*\b(install|add|sync|update|upgrade)\b",
    re.I,
)
LINT_RE = re.compile(
    r"\b(ruff|black|isort|flake8|pylint|mypy|pyright|eslint|prettier|tsc|"
    r"golangci-lint|gofmt|clippy|rubocop)\b",
    re.I,
)
SEARCH_RE = re.compile(r"(^|\s|;|&|\|)(grep|rg|ag|ack|find|fd)\b", re.I)
RUN_RE = re.compile(r"(^|\s|;|&|\|)(python3?|node|deno|bun|ruby|go run|cargo run|make|\./)", re.I)
PATCH_RE = re.compile(r"^\*\*\* (Add|Update|Delete) File: (.+)$", re.M)
MOVE_RE = re.compile(r"^\*\*\* Move to: (.+)$", re.M)
INJECTED_PREFIXES = (
    "<task-notification>",
    "<system-reminder>",
    "<command-name>",
    "<command-message>",
    "<command-args>",
    "<local-command-stdout>",
    "<bash-stdout>",
    "<bash-stderr>",
)
QUESTION_TEMPLATES = tuple(
    [f"A{i}" for i in range(1, 6)]
    + [f"B{i}" for i in range(1, 6)]
    + [f"C{i}" for i in range(1, 6)]
    + [f"D{i}" for i in range(1, 6)]
)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def source_stream_id(vendor: str, native_session_id: str, source_stem: str) -> str:
    material = "\0".join((vendor, native_session_id, source_stem))
    return sha256_bytes(material.encode())[:16]


def status_from_output(output: str) -> str:
    lowered = output.lower()
    if (
        "process exited with code 0" in lowered
        or "script completed" in lowered
        or "command completed" in lowered
        or '"is_error":false' in lowered
    ):
        return "ok"
    if (
        "process exited with code" in lowered
        or '"is_error":true' in lowered
        or "error" in lowered
    ):
        return "fail"
    return "observed"


def add_tool_ordinals(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    ordinal = 0
    for event in events:
        if event.get("kind") == "tool":
            event["source_tool_ordinal"] = ordinal
            event.setdefault("status", "observed")
            ordinal += 1
    return events


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text())


def write_csv(path: Path, fieldnames: list[str], rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def run(command: list[str], *, cwd: Path | None = None, env: dict[str, str] | None = None) -> str:
    result = subprocess.run(
        command,
        cwd=cwd,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"command failed ({result.returncode}): {shlex.join(command)}\n{result.stderr[-4000:]}"
        )
    return result.stdout


def parse_timestamp(value: Any) -> int | None:
    if isinstance(value, (int, float)):
        number = int(value)
        if number < 10_000_000_000:
            number *= 1000
        return number
    if not isinstance(value, str) or not value:
        return None
    raw = value.strip().replace("Z", "+00:00")
    try:
        return int(dt.datetime.fromisoformat(raw).timestamp() * 1000)
    except ValueError:
        return None


def canonical(path: Path) -> Path:
    return Path(os.path.realpath(path))


def worktrees(repo: Path) -> list[Path]:
    text = run(["git", "-C", str(repo), "worktree", "list", "--porcelain"])
    roots = [canonical(Path(line.split(" ", 1)[1])) for line in text.splitlines() if line.startswith("worktree ")]
    return sorted(set(roots))


def worktree_id(path: Path) -> str:
    return hashlib.sha256(str(canonical(path)).encode()).hexdigest()[:12]


def project_hash(path: Path) -> str:
    return hashlib.sha256(str(canonical(path)).encode()).hexdigest()


def home_relative(path: Path, home: Path) -> Path:
    return path.relative_to(home)


def load_json_or_jsonl(path: Path) -> Any:
    text = path.read_text()
    if path.suffix == ".json":
        return json.loads(text)
    rows = []
    for raw in text.splitlines():
        if not raw.strip():
            continue
        try:
            value = json.loads(raw)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            rows.append(value)
    return rows


def matching_root(cwd: str | None, roots: dict[str, Path]) -> tuple[str, Path] | None:
    if not cwd:
        return None
    resolved = canonical(Path(cwd))
    matches = []
    for name, root in roots.items():
        candidate = canonical(root)
        try:
            resolved.relative_to(candidate)
        except ValueError:
            continue
        matches.append((name, candidate))
    return max(matches, key=lambda item: len(item[1].parts)) if matches else None


def codex_native_root_id(payload: dict[str, Any], fallback: str) -> str:
    for key in ("session_id", "parent_thread_id", "thread_id", "id"):
        value = payload.get(key)
        if value:
            return str(value)
    return fallback


def native_root_from_path(vendor: str, path: Path, fallback: str) -> str:
    """Resolve only the source-native semantic root, without project matching."""
    source = load_json_or_jsonl(path)
    if vendor == "gemini" and isinstance(source, dict):
        return str(source.get("sessionId") or fallback)
    if not isinstance(source, list):
        return fallback
    identity = fallback
    for row in source:
        if not isinstance(row, dict):
            continue
        if vendor == "claude" and row.get("sessionId"):
            identity = str(row["sessionId"])
        elif vendor == "codex" and row.get("type") == "session_meta":
            payload = row.get("payload") if isinstance(row.get("payload"), dict) else {}
            identity = codex_native_root_id(payload, identity)
    return identity


def native_metadata(vendor: str, path: Path, roots: dict[str, Path]) -> dict[str, Any] | None:
    """Read source-native metadata/tool envelopes, rejecting foreign JSONL early."""
    session_id = path.stem
    cwd: str | None = None
    tool_calls = 0
    first_ts: int | None = None
    last_ts: int | None = None
    if vendor == "gemini":
        try:
            obj = load_json_or_jsonl(path)
        except (OSError, UnicodeDecodeError, json.JSONDecodeError):
            return None
        if not isinstance(obj, dict):
            return None
        session_id = str(obj.get("sessionId") or session_id)
        phash = str(obj.get("projectHash") or path.parents[1].name)
        cwd = next((str(root) for root in roots.values() if project_hash(root) == phash), None)
        for message in obj.get("messages") or []:
            if not isinstance(message, dict):
                continue
            stamp = parse_timestamp(message.get("timestamp") or message.get("time"))
            first_ts = stamp if first_ts is None else min(first_ts, stamp or first_ts)
            last_ts = stamp if last_ts is None else max(last_ts, stamp or last_ts)
            if message.get("type") == "gemini":
                tool_calls += sum(isinstance(call, dict) for call in message.get("toolCalls") or [])
        first_ts = first_ts or parse_timestamp(obj.get("startTime"))
        last_ts = last_ts or parse_timestamp(obj.get("lastUpdated"))
    else:
        matched: tuple[str, Path] | None = None
        try:
            with path.open(errors="replace") as handle:
                for raw in handle:
                    try:
                        row = json.loads(raw)
                    except json.JSONDecodeError:
                        continue
                    if not isinstance(row, dict):
                        continue
                    stamp = parse_timestamp(row.get("timestamp"))
                    if stamp is not None:
                        first_ts = stamp if first_ts is None else min(first_ts, stamp)
                        last_ts = stamp if last_ts is None else max(last_ts, stamp)
                    if vendor == "claude":
                        session_id = str(row.get("sessionId") or session_id)
                        discovered_cwd = str(row.get("cwd") or cwd or "") or None
                        content = (row.get("message") or {}).get("content") if isinstance(row.get("message"), dict) else None
                        if row.get("type") == "assistant" and isinstance(content, list):
                            tool_calls += sum(
                                isinstance(block, dict) and block.get("type") == "tool_use" for block in content
                            )
                    else:
                        payload = row.get("payload") if isinstance(row.get("payload"), dict) else {}
                        discovered_cwd = cwd
                        if row.get("type") == "session_meta":
                            session_id = codex_native_root_id(payload, session_id)
                            discovered_cwd = str(payload.get("cwd") or cwd or "") or None
                        elif row.get("type") == "turn_context":
                            discovered_cwd = str(payload.get("cwd") or cwd or "") or None
                        if row.get("type") == "response_item" and payload.get("type") in {
                            "function_call",
                            "custom_tool_call",
                        }:
                            tool_calls += 1
                    if discovered_cwd and discovered_cwd != cwd:
                        cwd = discovered_cwd
                        matched = matching_root(cwd, roots)
                        if matched is None:
                            return None
        except OSError:
            return None
        if matched is None:
            matched = matching_root(cwd, roots)
    matched = matching_root(cwd, roots)
    if matched is None or tool_calls == 0:
        return None
    root_name, _ = matched
    return {
        "vendor": vendor,
        "source_path": str(path),
        "session_id": session_id,
        "worktree": str(roots[root_name]),
        "tool_calls": tool_calls,
        "first_ts_ms": first_ts,
        "last_ts_ms": last_ts,
        "bytes": path.stat().st_size,
        "mtime_ns": path.stat().st_mtime_ns,
    }


def discover_sources(home: Path, all_roots: list[Path], cutoff_ns: int, raw_cap: int) -> list[dict[str, Any]]:
    roots = {str(root): root for root in all_roots}
    specs = (
        ("claude", home / ".claude" / "projects", "*.jsonl"),
        ("codex", home / ".codex" / "sessions", "*.jsonl"),
        ("gemini", home / ".gemini" / "tmp", "session-*.json"),
    )
    rows = []
    for vendor, base, pattern in specs:
        if not base.exists():
            continue
        for path in base.rglob(pattern):
            try:
                stat = path.stat()
            except OSError:
                continue
            if stat.st_mtime_ns > cutoff_ns or (raw_cap > 0 and stat.st_size > raw_cap):
                continue
            meta = native_metadata(vendor, path, roots)
            if meta is None:
                continue
            meta["sha256"] = sha256_file(path)
            meta["native_session_id"] = meta["session_id"]
            meta["source_stem"] = path.stem
            meta["session_id"] = f"{meta['native_session_id']}@{meta['sha256'][:16]}"
            rows.append(meta)
    return rows


def select_sources(
    candidates: list[dict[str, Any]],
    raw_cap: int,
    sessions: int,
    seed: str,
) -> tuple[Path, list[dict[str, Any]]]:
    by_root: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in candidates:
        by_root[row["worktree"]].append(row)
    if not by_root:
        raise RuntimeError("no native session source matched a live project worktree")
    selected_root = sorted(
        by_root,
        key=lambda root: (-len(by_root[root]), sha256_bytes(root.encode())),
    )[0]
    pools: dict[str, list[dict[str, Any]]] = {}
    for vendor in VENDORS:
        pool = [row for row in by_root[selected_root] if row["vendor"] == vendor]
        pool.sort(
            key=lambda row: sha256_bytes(
                (seed + vendor + row["sha256"]).encode()
            )
        )
        pools[vendor] = pool
    result: list[dict[str, Any]] = []
    offsets = {vendor: 0 for vendor in VENDORS}
    selected_roots: set[tuple[str, str]] = set()
    serialized = 0
    while len(result) < sessions:
        progress = False
        for vendor in VENDORS:
            pool = pools[vendor]
            while offsets[vendor] < len(pool):
                row = pool[offsets[vendor]]
                offsets[vendor] += 1
                root_key = (row["vendor"], row["native_session_id"])
                if root_key in selected_roots:
                    continue
                boundary = f"BEGIN_NATIVE {vendor} {row['sha256']} {row['bytes']}\nEND_NATIVE\n".encode()
                if raw_cap > 0 and serialized + len(boundary) + row["bytes"] > raw_cap:
                    continue
                result.append(row)
                selected_roots.add(root_key)
                serialized += len(boundary) + row["bytes"]
                progress = True
                break
            if len(result) >= sessions:
                break
        if not progress:
            break
    available = {vendor for vendor in VENDORS if pools[vendor]}
    represented = {row["vendor"] for row in result}
    if len(result) != sessions or not available.issubset(represented):
        raise RuntimeError(
            f"source selection failed: {len(result)} sessions, available={sorted(available)}, represented={sorted(represented)}"
        )
    for row in result:
        row["serialized_bundle_bytes"] = serialized
    return Path(selected_root), result


def _is_human_prompt(content: Any) -> bool:
    if isinstance(content, str):
        text = content
    elif isinstance(content, list):
        has_text = any(isinstance(block, dict) and block.get("type") == "text" for block in content)
        has_result = any(isinstance(block, dict) and block.get("type") == "tool_result" for block in content)
        if not has_text or has_result:
            return False
        text = " ".join(str(block.get("text") or "") for block in content if isinstance(block, dict))
    else:
        return False
    stripped = text.strip()
    return bool(stripped) and not stripped.startswith(INJECTED_PREFIXES)


def parse_arguments(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    if not isinstance(value, str):
        return {}
    try:
        parsed = json.loads(value)
        return parsed if isinstance(parsed, dict) else {"command": value}
    except json.JSONDecodeError:
        return {"command": value}


def embedded_exec_arguments(text: str) -> dict[str, Any] | None:
    marker = "tools.exec_command("
    start = text.find(marker)
    if start < 0:
        return None
    opening = text.find("{", start + len(marker))
    if opening < 0:
        return None
    depth = 0
    quoted = False
    escaped = False
    for index, character in enumerate(text[opening:], start=opening):
        if escaped:
            escaped = False
        elif character == "\\" and quoted:
            escaped = True
        elif character == '"':
            quoted = not quoted
        elif not quoted and character == "{":
            depth += 1
        elif not quoted and character == "}":
            depth -= 1
            if depth == 0:
                raw = text[opening:index + 1]
                try:
                    value = json.loads(raw)
                except json.JSONDecodeError:
                    try:
                        value = json.loads(
                            re.sub(
                                r"([{,]\s*)([A-Za-z_][A-Za-z0-9_-]*)(\s*:)",
                                r'\1"\2"\3',
                                raw,
                            )
                        )
                    except json.JSONDecodeError:
                        return None
                return value if isinstance(value, dict) else None
    return None


def normalized_tool_arguments(name: str, args: dict[str, Any]) -> dict[str, Any]:
    if name.lower() != "exec":
        return args
    nested = embedded_exec_arguments(command_text(name, args))
    return nested or args


def command_text(name: str, args: dict[str, Any]) -> str:
    value = args.get("command", args.get("cmd", args.get("input", "")))
    if isinstance(value, list):
        return " ".join(str(part) for part in value)
    if isinstance(value, str):
        return value
    if name.lower() in {"exec", "shell"}:
        return str(args)
    return ""


def command_atom(command: str) -> str:
    if TEST_RE.search(command):
        return "run_test"
    if VCS_RE.search(command):
        return "version_control"
    if PKG_RE.search(command):
        return "package"
    if LINT_RE.search(command):
        return "lint"
    if SEARCH_RE.search(command):
        return "search_repo"
    if RUN_RE.search(command):
        return "run_code"
    try:
        first = shlex.split(command)[0].rsplit("/", 1)[-1].lower()
    except (ValueError, IndexError):
        first = ""
    if first in READ_COMMANDS:
        return "read_file"
    return "other"


def tool_atom(name: str, args: dict[str, Any]) -> str:
    lower = name.lower()
    if lower in {"read", "notebookread", "read_file"}:
        return "read_file"
    if lower in {"edit", "write", "notebookedit", "multiedit", "apply_patch"}:
        return "edit"
    if lower in {"grep", "glob", "websearch", "webfetch", "search_file_content", "list_directory"}:
        return "search_repo"
    if lower in {"todowrite", "exitplanmode", "update_plan", "write_todos", "exit_plan_mode"}:
        return "think"
    if lower in {"bash", "exec", "exec_command", "shell_command", "run_shell_command", "shell"}:
        return command_atom(command_text(name, args))
    return "other"


def native_events(vendor: str, path: Path, meta: dict[str, Any]) -> list[dict[str, Any]]:
    obj = load_json_or_jsonl(path)
    events: list[dict[str, Any]] = []
    cwd = meta["worktree"]
    if vendor == "gemini":
        messages = obj.get("messages") or []
        for record_index, message in enumerate(messages):
            if not isinstance(message, dict):
                continue
            stamp = parse_timestamp(message.get("timestamp") or message.get("time"))
            if message.get("type") == "user" and _is_human_prompt(message.get("content")):
                events.append({"kind": "prompt", "atom": "prompt_ai", "ts_ms": stamp, "record_index": record_index, "call_index": 0})
            if message.get("type") != "gemini":
                continue
            for call_index, call in enumerate(message.get("toolCalls") or []):
                if not isinstance(call, dict):
                    continue
                args = call.get("args") if isinstance(call.get("args"), dict) else {}
                args = normalized_tool_arguments(str(call.get("name") or ""), args)
                events.append({
                    "kind": "tool",
                    "tool": str(call.get("name") or ""),
                    "args": args,
                    "call_id": str(call.get("id") or call.get("callId") or f"{record_index}:{call_index}"),
                    "workdir": str(args.get("workdir") or cwd),
                    "atom": tool_atom(str(call.get("name") or ""), args),
                    "ts_ms": stamp,
                    "record_index": record_index,
                    "call_index": call_index,
                    "status": {
                        "success": "ok",
                        "error": "fail",
                    }.get(str(call.get("status") or "").lower(), "observed"),
                })
        return add_tool_ordinals(events)
    rows = obj
    current_cwd = cwd
    call_positions: dict[str, int] = {}
    for record_index, row in enumerate(rows):
        if not isinstance(row, dict):
            continue
        stamp = parse_timestamp(row.get("timestamp"))
        if vendor == "claude":
            current_cwd = str(row.get("cwd") or current_cwd)
            content = (row.get("message") or {}).get("content") if isinstance(row.get("message"), dict) else None
            if row.get("type") == "user" and _is_human_prompt(content):
                events.append({"kind": "prompt", "atom": "prompt_ai", "ts_ms": stamp, "record_index": record_index, "call_index": 0})
            if row.get("type") == "assistant" and isinstance(content, list):
                call_index = 0
                for block in content:
                    if not isinstance(block, dict) or block.get("type") != "tool_use":
                        continue
                    args = block.get("input") if isinstance(block.get("input"), dict) else {}
                    args = normalized_tool_arguments(str(block.get("name") or ""), args)
                    events.append({
                        "kind": "tool",
                        "tool": str(block.get("name") or ""),
                        "args": args,
                        "call_id": str(block.get("id") or f"{record_index}:{call_index}"),
                        "workdir": str(args.get("workdir") or current_cwd),
                        "atom": tool_atom(str(block.get("name") or ""), args),
                        "ts_ms": stamp,
                        "record_index": record_index,
                        "call_index": call_index,
                        "status": "observed",
                    })
                    call_positions[str(block.get("id") or f"{record_index}:{call_index}")] = len(events) - 1
                    call_index += 1
            if row.get("type") == "user" and isinstance(content, list):
                fallback = bool(
                    (row.get("toolUseResult") or {}).get("is_error")
                    if isinstance(row.get("toolUseResult"), dict)
                    else False
                )
                for block in content:
                    if not isinstance(block, dict) or block.get("type") != "tool_result":
                        continue
                    call_id = str(block.get("tool_use_id") or "")
                    position = call_positions.get(call_id)
                    if position is not None:
                        failed = bool(block.get("is_error", fallback))
                        events[position]["status"] = "fail" if failed else "ok"
        else:
            payload = row.get("payload") if isinstance(row.get("payload"), dict) else {}
            if row.get("type") in {"session_meta", "turn_context"}:
                current_cwd = str(payload.get("cwd") or current_cwd)
            if row.get("type") == "response_item" and payload.get("type") in {"function_call", "custom_tool_call"}:
                name = str(payload.get("name") or "")
                args = parse_arguments(payload.get("arguments", payload.get("input")))
                args = normalized_tool_arguments(name, args)
                events.append({
                    "kind": "tool",
                    "tool": name,
                    "args": args,
                    "call_id": str(payload.get("call_id") or payload.get("id") or f"{record_index}:0"),
                    "workdir": str(args.get("workdir") or current_cwd),
                    "atom": tool_atom(name, args),
                    "ts_ms": stamp,
                    "record_index": record_index,
                    "call_index": 0,
                    "status": "observed",
                })
                call_positions[str(payload.get("call_id") or payload.get("id") or f"{record_index}:0")] = len(events) - 1
            if (
                row.get("type") == "response_item"
                and payload.get("type") in {"function_call_output", "custom_tool_call_output"}
            ):
                call_id = str(payload.get("call_id") or "")
                position = call_positions.get(call_id)
                if position is not None:
                    output = payload.get("output")
                    rendered = output if isinstance(output, str) else json.dumps(output, sort_keys=True)
                    events[position]["status"] = status_from_output(rendered)
    return add_tool_ordinals(events)


def lexical_repo_path(raw: str, workdir: str, root: Path) -> str | None:
    if not raw or any(char in raw for char in ("$", "*", "?", "[", "]", "{", "}", "<", ">")):
        return None
    candidate = Path(raw)
    base = Path(workdir) if workdir else root
    if not candidate.is_absolute():
        candidate = base / candidate
    normalized = Path(os.path.normpath(str(candidate)))
    try:
        relative = normalized.relative_to(root)
    except ValueError:
        return None
    value = PurePosixPath(relative.as_posix())
    return None if str(value) in {"", "."} else str(value)


def structured_paths(args: Any) -> list[str]:
    out: list[str] = []
    if isinstance(args, dict):
        for key, value in args.items():
            if key.lower() in PATH_KEYS and isinstance(value, str):
                out.append(value)
            elif isinstance(value, (dict, list)):
                out.extend(structured_paths(value))
    elif isinstance(args, list):
        for value in args:
            out.extend(structured_paths(value))
    return out


def shell_segments(command: str) -> list[list[str]]:
    segments: list[list[str]] = []
    pending: list[str] = []
    for line in command.splitlines():
        if pending:
            if line.strip() == pending[0]:
                pending.pop(0)
            continue
        pending.extend(
            match.group(1)
            for match in re.finditer(r"<<-?\s*['\"]?([A-Za-z_][A-Za-z0-9_]*)['\"]?", line)
        )
        try:
            lexer = shlex.shlex(line, posix=True, punctuation_chars=";&|<>")
            lexer.whitespace_split = True
            tokens = list(lexer)
        except ValueError:
            continue
        current: list[str] = []
        for token in tokens:
            if token and set(token) <= {";", "&", "|"}:
                if current:
                    segments.append(current)
                    current = []
            else:
                current.append(token)
        if current:
            segments.append(current)
    return segments


def file_operands(name: str, tokens: list[str]) -> list[str]:
    values: list[str] = []
    skip_next = False
    end_options = False
    explicit_sed_program = False
    option_arity = {
        "head": {"-n", "--lines", "-c", "--bytes"},
        "tail": {"-n", "--lines", "-c", "--bytes", "-s", "--sleep-interval", "--pid"},
        "sed": {"-e", "--expression", "-f", "--file"},
        "nl": {"-b", "--body-numbering", "-d", "--section-delimiter", "-f", "--footer-numbering",
               "-h", "--header-numbering", "-i", "--line-increment", "-l", "--join-blank-lines",
               "-n", "--number-format", "-s", "--number-separator", "-v", "--starting-line-number",
               "-w", "--number-width"},
    }.get(name, set())
    for token in tokens:
        if skip_next:
            skip_next = False
            continue
        if token == "--":
            end_options = True
            continue
        option_name = token.split("=", 1)[0]
        if not end_options and option_name in option_arity:
            explicit_sed_program |= name == "sed" and option_name in {
                "-e", "--expression", "-f", "--file"
            }
            skip_next = "=" not in token
            continue
        if not end_options and token.startswith("-"):
            continue
        values.append(token)
    if name == "sed" and not explicit_sed_program and values:
        values = values[1:]
    return values


def shell_path_actions(command: str) -> list[dict[str, str | None]]:
    out: list[dict[str, str | None]] = []
    for segment in shell_segments(command):
        # Redirections and heredocs are excluded from artifact extraction.  The
        # command still contributes its action atom, but neither redirect
        # targets nor heredoc bodies can become repository artifacts.
        if not segment or any(token and set(token) <= {"<", ">"} for token in segment):
            continue
        name = segment[0].rsplit("/", 1)[-1].lower()
        args = segment[1:]
        if name not in READ_COMMANDS | MUTATE_COMMANDS:
            continue
        values = file_operands(name, args)
        if name in {"mv", "cp"}:
            if len(values) < 2:
                continue
            source, destination = values[-2], values[-1]
            if name == "mv":
                out.append({"path": source, "access": "rename_from", "previous_path": None})
                out.append({"path": destination, "access": "rename", "previous_path": source})
            else:
                out.append({"path": source, "access": "read", "previous_path": None})
                out.append({"path": destination, "access": "create", "previous_path": None})
            continue
        access = "read" if name in READ_COMMANDS else ("delete" if name == "rm" else "create")
        for value in values:
            out.append({"path": value, "access": access, "previous_path": None})
    return out


def event_path_actions(event: dict[str, Any]) -> list[dict[str, str | None]]:
    if event.get("kind") != "tool":
        return []
    name = str(event.get("tool") or "").lower()
    args = event.get("args") if isinstance(event.get("args"), dict) else {}
    actions: list[dict[str, str | None]] = []
    command = command_text(name, args)
    if name in {"bash", "exec", "exec_command", "shell_command", "run_shell_command", "shell"}:
        actions.extend(shell_path_actions(command))
    if name == "apply_patch" or (
        name in {"bash", "exec", "exec_command", "shell_command", "run_shell_command", "shell"}
        and "*** Begin Patch" in command
    ):
        patch = command or str(args.get("patch") or "")
        pending_update: str | None = None
        for raw_line in patch.splitlines():
            line = raw_line.strip()
            matched = PATCH_RE.fullmatch(line)
            if matched:
                kind, raw_path = matched.groups()
                path = raw_path.strip()
                access = {"Add": "create", "Update": "write", "Delete": "delete"}[kind]
                actions.append({"path": path, "access": access, "previous_path": None})
                pending_update = path if kind == "Update" else None
                continue
            moved = MOVE_RE.fullmatch(line)
            if moved and pending_update:
                actions = [
                    action
                    for action in actions
                    if not (
                        action["path"] == pending_update
                        and action["access"] == "write"
                    )
                ]
                actions.append({
                    "path": pending_update,
                    "access": "rename_from",
                    "previous_path": None,
                })
                actions.append({
                    "path": moved.group(1).strip(),
                    "access": "rename",
                    "previous_path": pending_update,
                })
                pending_update = None
    lower = name
    if lower in {"read", "notebookread", "read_file"}:
        access = "read"
    elif lower in {"edit", "notebookedit", "multiedit"}:
        access = "write"
    elif lower in {"write", "write_file"}:
        access = "create"
    else:
        access = ""
    if access:
        for path in structured_paths(args):
            actions.append({"path": path, "access": access, "previous_path": None})
    dedup: list[dict[str, str | None]] = []
    seen: set[tuple[Any, ...]] = set()
    for action in actions:
        key = (action["path"], action["access"], action.get("previous_path"))
        if key not in seen:
            seen.add(key)
            dedup.append(action)
    priority = {"rename_from": 0, "rename": 1}
    return sorted(
        dedup,
        key=lambda action: (
            priority.get(str(action["access"]), 2),
            str(action["path"]),
            str(action["access"]),
            str(action.get("previous_path") or ""),
        ),
    )


class ArtifactTracker:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.current: dict[tuple[str, str], str] = {}
        self.attempted: dict[tuple[str, str], str] = {}
        self.generation: Counter[tuple[str, str]] = Counter()
        self.display: dict[str, str] = {}

    def identity(
        self,
        path: str,
        access: str,
        previous: str | None = None,
        confirmed: bool = False,
        worktree: str = "w",
        previous_worktree: str | None = None,
    ) -> str:
        key = (worktree, path)
        previous_worktree = previous_worktree or worktree
        previous_key = (previous_worktree, previous) if previous else None
        if (
            access == "rename"
            and previous_key
            and confirmed
            and previous_worktree == worktree
        ):
            identity = (
                self.current.pop(previous_key, None)
                or self.attempted.pop(previous_key, None)
                or self._new(previous, previous_worktree)
            )
            self.current[key] = identity
            self.attempted.pop(key, None)
            self.display[identity] = path
            return identity
        if not confirmed:
            identity = self.current.get(key)
            if identity is None:
                identity = self.attempted.get(key)
                if identity is None:
                    identity = self._new(path, worktree)
                    self.attempted[key] = identity
            self.display[identity] = path
            return identity
        identity = self.current.get(key)
        if identity is None:
            if access == "create":
                identity = self._new(path, worktree)
            else:
                identity = self.attempted.pop(key, None) or self._new(path, worktree)
            self.current[key] = identity
        self.attempted.pop(key, None)
        if access == "delete":
            self.current.pop(key, None)
        self.display[identity] = path
        return identity

    def _new(self, path: str, worktree: str = "w") -> str:
        key = (worktree, path)
        generation = self.generation[key]
        self.generation[key] += 1
        identity = f"{path}#{generation}"
        self.display[identity] = path
        return identity


def artifact_edges(
    project: dict[str, Any],
    selected: list[dict[str, Any]],
    frozen_home: Path,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    root = Path(project["worktree"])
    sessions = []
    for source in selected:
        copy = frozen_home / source["home_relative"]
        events = [
            event
            for event in native_events(source["vendor"], copy, source)
            if event.get("ts_ms") is not None
        ]
        if not any(event.get("kind") == "tool" for event in events):
            continue
        first_ts = min(
            event["ts_ms"] for event in events if event.get("kind") == "tool"
        )
        native_root = f"{source['vendor']}:{source['native_session_id']}"
        sessions.append({
            **source,
            "events": events,
            "first_ts_ms": first_ts,
            "semantic_session_id": native_root,
            "source_stream_id": source_stream_id(
                source["vendor"], source["native_session_id"], source["source_stem"]
            ),
        })
    sessions.sort(key=lambda row: (row["first_ts_ms"], row["semantic_session_id"]))
    tracker = ArtifactTracker(root)
    edges: list[dict[str, Any]] = []
    calls: list[dict[str, Any]] = []
    ordered_events = []
    for session_ordinal, session in enumerate(sessions):
        for event in session["events"]:
            if event.get("kind") != "tool":
                continue
            ordered_events.append((
                event.get("ts_ms") if event.get("ts_ms") is not None else session["first_ts_ms"],
                session["source_stream_id"],
                event.get("source_tool_ordinal", -1),
                f"{event['record_index']}:{event['call_index']}",
                session_ordinal,
                session,
                event,
            ))
    ordered_events.sort(key=lambda row: row[:4])
    pending_rename: dict[tuple[str, str], str] = {}
    for event_ordinal, (_, _, _, _, session_ordinal, session, event) in enumerate(ordered_events):
        if event.get("kind") == "tool":
            calls.append({
                "project": project["project"],
                "vendor": session["vendor"],
                "native_session_id": session["semantic_session_id"],
                "session_ordinal": session_ordinal,
                "source_stream_id": session["source_stream_id"],
                "source_tool_ordinal": event["source_tool_ordinal"],
                "call_id": str(event["call_id"]),
                "status": str(event.get("status") or "observed"),
                "atom": str(event["atom"]),
            })
        normalized_actions = []
        for action in event_path_actions(event):
            raw_path = str(action["path"] or "")
            path = lexical_repo_path(raw_path, str(event.get("workdir") or root), root)
            if path is None:
                continue
            previous = None
            if action.get("previous_path"):
                previous = lexical_repo_path(str(action["previous_path"]), str(event.get("workdir") or root), root)
            normalized_actions.append((action, path, previous))
        normalized_actions = list({
            (str(action["access"]), path, previous): (action, path, previous)
            for action, path, previous in normalized_actions
        }.values())
        normalized_actions.sort(
            key=lambda row: (
                {"rename_from": 0, "rename": 1}.get(str(row[0]["access"]), 2),
                row[1],
                str(row[0]["access"]),
                row[2] or "",
            )
        )
        for action_ordinal, (action, path, previous) in enumerate(normalized_actions):
            access = str(action["access"])
            if access == "rename_from":
                pending_rename[(session["semantic_session_id"], str(event["call_id"]))] = path
            if access == "rename" and previous is None:
                previous = pending_rename.get(
                    (session["semantic_session_id"], str(event["call_id"]))
                )
            status = str(event.get("status") or "observed")
            identity = tracker.identity(path, access, previous, status == "ok")
            edges.append({
                "project": project["project"],
                "session_id": session["semantic_session_id"],
                "native_session_id": session["semantic_session_id"],
                "session_ordinal": session_ordinal,
                "vendor": session["vendor"],
                "source_id": session["source_id"],
                "source_sha256": session["sha256"],
                "source_stream_id": session["source_stream_id"],
                "source_tool_ordinal": event["source_tool_ordinal"],
                "record_index": event["record_index"],
                "call_index": event["call_index"],
                "call_id": str(event["call_id"]),
                "event_ordinal": event_ordinal,
                "action_ordinal": action_ordinal,
                "artifact_id": identity,
                "path": path,
                "display_path": tracker.display[identity],
                "access": access,
                "previous_path": previous,
                "action_class": "read" if access == "read" else "mutate",
                "status": status,
                "confirmed_effect": status == "ok",
            })
    for edge in edges:
        edge["display_path"] = tracker.display[edge["artifact_id"]]
    public_sessions = [
        {key: value for key, value in session.items() if key != "events"} | {"session_ordinal": index}
        for index, session in enumerate(sessions)
    ]
    return edges, public_sessions, calls


def direct_atoms(selected: list[dict[str, Any]], frozen_home: Path) -> dict[str, list[str]]:
    result = {}
    for source in selected:
        events = native_events(source["vendor"], frozen_home / source["home_relative"], source)
        result[f"{source['vendor']}:{source['native_session_id']}"] = [
            str(event["atom"]) for event in events if event.get("ts_ms") is not None
        ]
    return result


def pattern_count(atoms: dict[str, list[str]], pattern: str) -> int:
    rx = re.compile(pattern)
    return sum(bool(rx.search(" ".join(sequence) + " ")) for sequence in atoms.values())


def hmac_path(path: str) -> str:
    key = hashlib.sha256(("rq7-path-salt-" + SEED).encode()).digest()
    return hmac.new(key, path.encode(), hashlib.sha256).hexdigest()[:16]


def choose_anchors(edges: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_artifact: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for edge in edges:
        by_artifact[edge["artifact_id"]].append(edge)
    anchors = []
    for identity, rows in by_artifact.items():
        calls = {(row["session_id"], row["call_id"]) for row in rows}
        anchors.append({
            "artifact_id": identity,
            "path": rows[-1]["display_path"],
            "path_id": hmac_path(rows[-1]["display_path"]),
            "call_count": len(calls),
        })
    anchors.sort(key=lambda row: (-row["call_count"], row["path_id"]))
    if len(anchors) < 5:
        raise RuntimeError(f"question grammar needs five artifacts, found {len(anchors)}")
    return anchors[:5]


def workspace_snapshot(root: Path, anchors: list[dict[str, Any]], private_project: Path) -> dict[str, Any]:
    before_head = run(["git", "-C", str(root), "rev-parse", "HEAD"]).strip()
    before_status = subprocess.run(
        ["git", "-C", str(root), "status", "--porcelain=v2", "-z"],
        stdout=subprocess.PIPE,
        check=True,
    ).stdout
    index = subprocess.run(
        ["git", "-C", str(root), "ls-files", "-s", "-z"],
        stdout=subprocess.PIPE,
        check=True,
    ).stdout
    untracked = subprocess.run(
        ["git", "-C", str(root), "ls-files", "-o", "--exclude-standard", "-z"],
        stdout=subprocess.PIPE,
        check=True,
    ).stdout
    tracked_paths = {
        entry.split(b"\t", 1)[1].decode("utf-8", "surrogateescape")
        for entry in index.split(b"\0")
        if b"\t" in entry
    }
    private_project.mkdir(parents=True, exist_ok=True)
    path_rows = []
    for anchor in anchors:
        relative = anchor["path"]
        target = root / relative
        if relative in tracked_paths:
            status = "tracked"
        elif target.exists() or target.is_symlink():
            status = "untracked"
        else:
            status = "absent"
        content_hash = ""
        index_entry = next(
            (
                entry.decode("utf-8", "surrogateescape")
                for entry in index.split(b"\0")
                if entry.endswith(b"\t" + relative.encode("utf-8", "surrogateescape"))
            ),
            "",
        )
        if target.is_file():
            data = target.read_bytes()
            content_hash = sha256_bytes(data)
            (private_project / f"{anchor['path_id']}.blob").write_bytes(data)
        path_rows.append({
            **anchor,
            "status": status,
            "index_entry": index_entry,
            "present": bool(target.exists() or target.is_symlink()),
            "content_sha256": content_hash,
        })
    after_head = run(["git", "-C", str(root), "rev-parse", "HEAD"]).strip()
    after_status = subprocess.run(
        ["git", "-C", str(root), "status", "--porcelain=v2", "-z"],
        stdout=subprocess.PIPE,
        check=True,
    ).stdout
    if before_head != after_head or before_status != after_status:
        raise RuntimeError(f"workspace changed during freeze: {root}")
    manifest_bytes = before_head.encode() + b"\0" + before_status + index + untracked
    return {
        "cutoff_ms": int(time.time() * 1000),
        "head": before_head,
        "status_sha256": sha256_bytes(before_status),
        "index_sha256": sha256_bytes(index),
        "untracked_sha256": sha256_bytes(untracked),
        "manifest_sha256": sha256_bytes(manifest_bytes),
        "paths": path_rows,
    }


def question_rows(project: dict[str, Any], atoms: dict[str, list[str]], edges: list[dict[str, Any]], sessions: list[dict[str, Any]], anchors: list[dict[str, Any]], snapshot: dict[str, Any]) -> list[dict[str, Any]]:
    p0 = anchors[0]
    p0_rows = [row for row in edges if row["artifact_id"] == p0["artifact_id"]]
    p0_calls = {(row["session_id"], row["call_id"]): row for row in p0_rows}
    p0_session_ordinals = sorted({row["session_ordinal"] for row in p0_rows})
    session_sets: list[set[str]] = [set() for _ in sessions]
    for edge in edges:
        session_sets[edge["session_ordinal"]].add(edge["artifact_id"])
    revisits = 0
    prior: set[str] = set()
    for current in session_sets:
        if prior & current:
            revisits += 1
        prior |= current
    adjacent = sum(bool(left & right) for left, right in zip(session_sets, session_sets[1:]))
    presence = [index in p0_session_ordinals for index in range(len(sessions))]
    returns = 0
    seen = False
    gap = False
    for active in presence:
        if active:
            if seen and gap:
                returns += 1
            seen = True
            gap = False
        elif seen:
            gap = True
    multi_session = Counter()
    for aset in session_sets:
        for identity in aset:
            multi_session[identity] += 1
    values: dict[str, Any] = {
        "A1": sum(sequence.count("read_file") for sequence in atoms.values()),
        "A2": sum(sequence.count("edit") for sequence in atoms.values()),
        "A3": sum(sequence.count("run_test") for sequence in atoms.values()),
        "A4": pattern_count(atoms, r"read_file (?:[a-z_]+ )*edit "),
        "A5": pattern_count(atoms, r"edit (?:[a-z_]+ )*run_test "),
        "B1": len(p0_calls),
        "B2": sum(row["action_class"] == "read" for row in p0_calls.values()),
        "B3": sum(row["action_class"] == "mutate" for row in p0_calls.values()),
        "B4": min(p0_rows, key=lambda row: row["event_ordinal"])["action_class"],
        "B5": len(p0_session_ordinals),
        "C1": adjacent,
        "C2": revisits,
        "C3": returns,
        "C4": (p0_session_ordinals[-1] - p0_session_ordinals[0]) if p0_session_ordinals else 0,
        "C5": sum(count >= 2 for count in multi_session.values()),
    }
    for index, row in enumerate(snapshot["paths"], start=1):
        values[f"D{index}"] = row["status"]
    witnesses_by_artifact: dict[str, list[str]] = defaultdict(list)
    for edge in edges:
        witnesses_by_artifact[edge["artifact_id"]].append(
            f"{edge['source_sha256']}:{edge['record_index']}:{edge['call_index']}:{edge['call_id']}"
        )
    questions = []
    for template in QUESTION_TEMPLATES:
        family = template[0]
        if family == "A":
            witnesses = sorted({source["sha256"] for source in sessions})
        elif family in {"B", "C"}:
            witnesses = sorted(set(witnesses_by_artifact.get(p0["artifact_id"], [])))
        else:
            path_row = snapshot["paths"][int(template[1:]) - 1]
            witnesses = [f"{snapshot['manifest_sha256']}:{path_row['path_id']}"]
        questions.append({
            "id": f"{project['project']}-{template}",
            "project": project["project"],
            "family": family,
            "template": template,
            "answer": str(values[template]).lower() if isinstance(values[template], bool) else str(values[template]),
            "p0_path": p0["path"],
            "p0_path_id": p0["path_id"],
            "path_id": anchors[int(template[1:]) - 1]["path_id"] if family == "D" else p0["path_id"],
            "witnesses": witnesses,
        })
    return questions


def relation_values(edges: list[dict[str, Any]], session_count: int, p0_identity: str) -> dict[str, str] | None:
    p0_rows = [row for row in edges if row["artifact_id"] == p0_identity]
    if not p0_rows:
        return None
    by_call: dict[tuple[str, str], dict[str, Any]] = {}
    for row in p0_rows:
        by_call[(row["session_id"], row["call_id"])] = row
    p0_ordinals = sorted({row["session_ordinal"] for row in p0_rows})
    session_sets = [set() for _ in range(session_count)]
    for edge in edges:
        if 0 <= edge["session_ordinal"] < session_count:
            session_sets[edge["session_ordinal"]].add(edge["artifact_id"])
    adjacent = sum(bool(left & right) for left, right in zip(session_sets, session_sets[1:]))
    prior: set[str] = set()
    revisit = 0
    for current in session_sets:
        if prior & current:
            revisit += 1
        prior |= current
    presence = [index in p0_ordinals for index in range(session_count)]
    seen = False
    gap = False
    returns = 0
    for active in presence:
        if active:
            if seen and gap:
                returns += 1
            seen, gap = True, False
        elif seen:
            gap = True
    distinct_sessions: dict[str, set[int]] = defaultdict(set)
    for edge in edges:
        distinct_sessions[edge["artifact_id"]].add(edge["session_ordinal"])
    values = {
        "B1": len(by_call),
        "B2": sum(row["action_class"] == "read" for row in by_call.values()),
        "B3": sum(row["action_class"] == "mutate" for row in by_call.values()),
        "B4": min(p0_rows, key=lambda row: row["event_ordinal"])["action_class"],
        "B5": len(p0_ordinals),
        "C1": adjacent,
        "C2": revisit,
        "C3": returns,
        "C4": p0_ordinals[-1] - p0_ordinals[0],
        "C5": sum(len(value) >= 2 for value in distinct_sessions.values()),
    }
    return {key: str(value) for key, value in values.items()}


def source_call_ids(project: dict[str, Any], frozen_home: Path) -> dict[str, set[str]]:
    result: dict[str, set[str]] = {}
    for source in project["sources"]:
        events = native_events(source["vendor"], frozen_home / source["home_relative"], source)
        result[source["session_id"]] = {
            str(event["call_id"]) for event in events if event.get("kind") == "tool"
        }
    return result


def match_session(raw: str, project: dict[str, Any]) -> str | None:
    for field in ("source_stem", "native_session_id"):
        candidates = [
            source["session_id"]
            for source in project["sources"]
            if raw == source[field] or raw.endswith(source[field]) or source[field] in raw
        ]
        if len(set(candidates)) == 1:
            return candidates[0]
        if candidates:
            return None
    return None


def proposed_edges(project: dict[str, Any], trace: dict[str, Any], frozen_home: Path) -> tuple[list[dict[str, Any]], str | None, str | None]:
    root = Path(project["worktree"])
    target_worktree = worktree_id(root)
    session_order = {row["session_id"]: row["session_ordinal"] for row in project["sessions"]}
    calls = source_call_ids(project, frozen_home)
    tracker = ArtifactTracker(root)
    edges: list[dict[str, Any]] = []
    for event_ordinal, event in enumerate(trace.get("events") or []):
        session_id = match_session(str(event.get("session_id") or ""), project)
        if session_id is None:
            continue
        call_id = str(event.get("source_call_id") or "")
        actions = [
            action
            for action in event.get("actions") or []
            if action.get("worktree_id") == target_worktree
        ]
        if not actions:
            continue
        if not call_id or call_id not in calls.get(session_id, set()):
            return [], None, f"unjoined artifact event {session_id}:{call_id or '<missing>'}"
        for action in actions:
            path = str(action.get("path") or "")
            if not path:
                continue
            access = str(action.get("access") or "write")
            previous = str(action.get("previous_path") or "") or None
            identity = tracker.identity(path, access, previous)
            edges.append({
                "project": project["project"],
                "session_id": session_id,
                "session_ordinal": session_order[session_id],
                "call_id": call_id,
                "event_ordinal": event_ordinal,
                "artifact_id": identity,
                "path": path,
                "display_path": tracker.display[identity],
                "access": access,
                "action_class": "read" if access == "read" else "mutate",
            })
    for edge in edges:
        edge["display_path"] = tracker.display[edge["artifact_id"]]
    p0_path = project["anchors"][0]["path"]
    matches = [
        identity
        for identity, display in tracker.display.items()
        if display == p0_path or any(row["artifact_id"] == identity and row["path"] == p0_path for row in edges)
    ]
    if not matches:
        return edges, None, None
    matches.sort(key=lambda identity: -sum(row["artifact_id"] == identity for row in edges))
    return edges, matches[0], None


def production_atom(event: dict[str, Any]) -> str:
    name = str(event.get("tool_name") or "").lower()
    if name in {"read", "notebookread", "read_file"}:
        return "read_file"
    if name in {"edit", "write", "notebookedit", "multiedit", "apply_patch"}:
        return "edit"
    if name in {"grep", "glob", "websearch", "webfetch", "search_file_content", "list_directory"}:
        return "search_repo"
    if name in {"todowrite", "exitplanmode", "update_plan", "write_todos", "exit_plan_mode"}:
        return "think"
    if name in {"bash", "exec", "exec_command", "shell_command", "run_shell_command", "shell"}:
        if event.get("effect") == "test":
            return "run_test"
        if str(event.get("command_name") or "").lower() in READ_COMMANDS:
            return "read_file"
        if event.get("effect") == "repo":
            return "version_control"
        if event.get("effect") == "network":
            return "package"
        return "other"
    return "other"


def production_projection(
    project: dict[str, Any],
    trace: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, list[str]], str | None]:
    root = Path(project["worktree"])
    target_worktree = worktree_id(root)
    expected_sessions = {
        row["semantic_session_id"] for row in project["sessions"]
    }
    expected_streams = {
        row["source_stream_id"]: row["semantic_session_id"]
        for row in project["sessions"]
    }
    edges: list[dict[str, Any]] = []
    calls: list[dict[str, Any]] = []
    atoms: dict[str, list[str]] = defaultdict(list)
    for event_ordinal, event in enumerate(trace.get("events") or []):
        native_session_id = str(
            event.get("native_session_id") or event.get("session_id") or ""
        )
        source_stream = str(event.get("source_stream_id") or "")
        if native_session_id not in expected_sessions:
            return [], [], {}, (
                f"unexpected production native root "
                f"{native_session_id or '<missing>'}:{source_stream or '<missing>'}"
            )
        if expected_streams.get(source_stream) != native_session_id:
            return [], [], {}, (
                f"source-stream join mismatch {native_session_id}:{source_stream or '<missing>'}"
            )
        call_id = str(event.get("source_call_id") or "")
        source_tool_ordinal = int(event.get("source_tool_ordinal", -1))
        status = str(event.get("status") or "observed")
        session_ordinal = int(event.get("session_ordinal", -1))
        atom = production_atom(event)
        atoms[native_session_id].append(atom)
        calls.append({
            "project": project["project"],
            "vendor": str(event.get("vendor") or ""),
            "native_session_id": native_session_id,
            "source_stream_id": source_stream,
            "source_tool_ordinal": source_tool_ordinal,
            "call_id": call_id,
            "status": status,
            "atom": atom,
            "session_ordinal": session_ordinal,
        })
        for action in event.get("actions") or []:
            if action.get("worktree_id") != target_worktree:
                continue
            path = str(action.get("path") or "")
            if not path:
                continue
            access = str(action.get("access") or "")
            previous = str(action.get("previous_path") or "") or None
            identity = str(action.get("artifact_id") or "")
            if not identity:
                return [], [], {}, (
                    f"missing production artifact identity {native_session_id}:{call_id}"
                )
            edges.append({
                "project": project["project"],
                "session_id": native_session_id,
                "native_session_id": native_session_id,
                "session_ordinal": session_ordinal,
                "vendor": str(event.get("vendor") or ""),
                "source_stream_id": source_stream,
                "source_tool_ordinal": source_tool_ordinal,
                "call_id": call_id,
                "event_ordinal": event_ordinal,
                "action_ordinal": int(action.get("action_ordinal", -1)),
                "artifact_id": identity,
                "path": path,
                "display_path": path,
                "access": access,
                "previous_path": previous,
                "action_class": "read" if access == "read" else "mutate",
                "status": status,
                "confirmed_effect": status == "ok",
            })
    final_display = {
        row["artifact_id"]: row["path"]
        for row in edges
    }
    for edge in edges:
        edge["display_path"] = final_display[edge["artifact_id"]]
    return edges, calls, dict(atoms), None


def edge_key(row: dict[str, Any]) -> tuple[Any, ...]:
    return (
        int(row["session_ordinal"]),
        row["native_session_id"],
        row["source_stream_id"],
        str(row["call_id"]),
        int(row["source_tool_ordinal"]),
        int(row["event_ordinal"]),
        int(row["action_ordinal"]),
        row["path"],
        row["access"],
        row.get("previous_path"),
        row["artifact_id"],
    )


def call_status_key(row: dict[str, Any]) -> tuple[Any, ...]:
    return (
        int(row["session_ordinal"]),
        row["native_session_id"],
        row["source_stream_id"],
        str(row["call_id"]),
        int(row["source_tool_ordinal"]),
        row["status"],
    )


def multiset_metrics(expected: Counter[Any], actual: Counter[Any]) -> dict[str, Any]:
    matched = sum((expected & actual).values())
    expected_count = sum(expected.values())
    actual_count = sum(actual.values())
    return {
        "expected": expected_count,
        "actual": actual_count,
        "matched": matched,
        "precision": matched / actual_count if actual_count else float(expected_count == 0),
        "recall": matched / expected_count if expected_count else float(actual_count == 0),
        "missing": expected_count - matched,
        "extra": actual_count - matched,
    }


def projection_conformance(
    project: dict[str, Any],
    production_edges: list[dict[str, Any]],
    production_calls: list[dict[str, Any]],
) -> dict[str, Any]:
    oracle_edges = project["oracle_edges"]
    all_production_calls = production_calls
    edge_call_keys = {
        (
            row["native_session_id"],
            row["source_stream_id"],
            str(row["call_id"]),
            int(row["source_tool_ordinal"]),
        )
        for row in oracle_edges + production_edges
    }
    oracle_calls = [
        row
        for row in project["oracle_calls"]
        if (
            row["native_session_id"],
            row["source_stream_id"],
            str(row["call_id"]),
            int(row["source_tool_ordinal"]),
        )
        in edge_call_keys
    ]
    production_calls = [
        row
        for row in production_calls
        if (
            row["native_session_id"],
            row["source_stream_id"],
            str(row["call_id"]),
            int(row["source_tool_ordinal"]),
        )
        in edge_call_keys
    ]
    result = {
        "project": project["project"],
        "session_order": multiset_metrics(
            Counter(
                (row["semantic_session_id"], int(row["session_ordinal"]))
                for row in project["sessions"]
            ),
            Counter(
                {
                    (row["native_session_id"], int(row["session_ordinal"]))
                    for row in all_production_calls
                }
            ),
        ),
        "attempted_edges": multiset_metrics(
            Counter(edge_key(row) for row in oracle_edges),
            Counter(edge_key(row) for row in production_edges),
        ),
        "confirmed_effect_edges": multiset_metrics(
            Counter(edge_key(row) for row in oracle_edges if row["status"] == "ok"),
            Counter(edge_key(row) for row in production_edges if row["status"] == "ok"),
        ),
        "edge_call_statuses": multiset_metrics(
            Counter(call_status_key(row) for row in oracle_calls),
            Counter(call_status_key(row) for row in production_calls),
        ),
        "by_vendor": {},
    }
    for vendor in sorted({row["vendor"] for row in project["sessions"]}):
        expected_edges = [row for row in oracle_edges if row["vendor"] == vendor]
        actual_edges = [row for row in production_edges if row["vendor"] == vendor]
        expected_calls = [row for row in oracle_calls if row["vendor"] == vendor]
        actual_calls = [row for row in production_calls if row["vendor"] == vendor]
        result["by_vendor"][vendor] = {
            "session_order": multiset_metrics(
                Counter(
                    (row["semantic_session_id"], int(row["session_ordinal"]))
                    for row in project["sessions"]
                    if row["vendor"] == vendor
                ),
                Counter(
                    {
                        (row["native_session_id"], int(row["session_ordinal"]))
                        for row in all_production_calls
                        if row["vendor"] == vendor
                    }
                ),
            ),
            "attempted_edges": multiset_metrics(
                Counter(edge_key(row) for row in expected_edges),
                Counter(edge_key(row) for row in actual_edges),
            ),
            "confirmed_effect_edges": multiset_metrics(
                Counter(edge_key(row) for row in expected_edges if row["status"] == "ok"),
                Counter(edge_key(row) for row in actual_edges if row["status"] == "ok"),
            ),
            "edge_call_statuses": multiset_metrics(
                Counter(call_status_key(row) for row in expected_calls),
                Counter(call_status_key(row) for row in actual_calls),
            ),
        }
    return result


def question_spec() -> str:
    return """# RQ7 Native-Root Conformance v3

Specification ID: `native-root-conformance-v3`.

All answers use only the complete native files and cutoff manifest in the
prompt. A semantic session is one `(vendor, native_root_session_id)`; a source
stream is provenance, not another session. The held-out selection contains at
most one stream per native root. Sessions are ordered by first included native
Tool timestamp and semantic session ID. Native events are ordered by timestamp, stable source
stream ID, source Tool ordinal, and source record/call index as a final
uniqueness key. Opaque call IDs never establish time order.
Tool calls without a native timestamp are outside the ordered trajectory and
are reported as coverage exclusions rather than assigned a synthetic time.
For Codex `session_meta`, native root resolution is
`payload.session_id`, then `payload.parent_thread_id`, then
`payload.thread_id`, then the source stream's `payload.id`. Empty values are
skipped. Source stream identity remains separate and never replaces this
semantic root.

Tool invocations are attempted actions regardless of result status. The
independent oracle also pairs native Tool results and records `ok`, `fail`, or
`observed`. Only `ok` path actions are confirmed effects; failed or unknown
mutations do not create, rename, delete, or supersede an artifact generation.
A confirmed effect clears any same-path identity that existed only for a
failed or unknown attempt, so that identity cannot be revived after a later
delete.

Action mapping uses the exact Tool names
Read/NotebookRead/read_file, Edit/NotebookEdit/MultiEdit,
Write/write_file, apply_patch, and
bash/exec/exec_command/shell_command/run_shell_command/shell. Unlisted names
and substring matches are excluded. Terminal cat/sed/head/tail/nl/less/more are
read_file; Edit/Write/NotebookEdit/MultiEdit/apply_patch are edit; commands
matching pytest, test(s), unittest, jest, mocha, vitest, tox, go test, cargo
test, npm/yarn test, make test, or gradle test are run_test. Other calls still
occupy their ordered atom position. A4 is the number of sessions matching
`read_file (?:[a-z_]+ )*edit ` and A5 uses
`edit (?:[a-z_]+ )*run_test `.

Artifact paths come only from structured path keys, apply_patch file headers,
and path operands of cat/sed/head/tail/nl/less/more/touch/rm/mv/cp.
Structured keys are path, file_path, filepath, absolute_path, target_file,
notebook_path, old_path, and new_path. Event workdir overrides session cwd.
Resolve relative paths lexically inside the
selected worktree; exclude outside paths, variables, globs, symlink
dereferencing, search scopes, and ambiguous shell syntax. In particular, any
shell segment containing input/output redirection or a heredoc contributes no
artifact edge; redirect tokens, targets, and bodies are never paths.
Option arguments and sed programs are not file operands. Calls add one edge
per distinct `(path, access, previous_path)` tuple, so different actions on the
same path remain distinct. Shell extraction accepts only a direct declared
file command at the start of a segment; cd state, command wrappers, and nested
shell interpretation are excluded. A Codex `tools.exec_command({...})`
transport envelope is unwrapped before applying that rule. Update plus Move
patch headers are one rename pair, not an additional write. Actions within a
call use the canonical order rename-source, rename-destination, then
lexicographic `(path, access, previous_path)`. Explicit rename preserves
identity only when its Tool result is `ok`; confirmed delete followed by
confirmed create starts a generation. A failed or unknown rename source and
destination therefore retain separate attempted identities and never transfer
persistent identity. Read actions are the readers above; all
retained write, create, delete, rename, and copy attempts are mutations.

P0--P4 are the five artifacts with the most distinct attempted calls; HMAC path
ID breaks ties. The question gives their normalized paths. A1--A3 are total
read_file/edit/run_test atoms. A4--A5 are the session pattern counts. B1--B5
ask P0 attempted calls, reads, mutations, first action class, and distinct
native-root sessions. C1--C5 ask adjacent native-root session pairs sharing any
artifact, later native-root sessions revisiting any prior artifact, P0 return
episodes after a native-root gap, P0 first-to-last native-root ordinal gap, and
artifacts present in at least two native-root sessions.
D1--D5 ask tracked/untracked/absent at cutoff for P0--P4; tracked means an index
entry, untracked means present without one, and absent means neither.

Canonical answers are base-10 integers or the exact category strings read,
mutate, tracked, untracked, absent. Return abstain rather than estimate.
"""


def official_procgrep_atoms(procgrep: Path, selected: list[dict[str, Any]], frozen_home: Path) -> dict[str, list[str]]:
    sys.path.insert(0, str(procgrep / "src"))
    from procgrep.ingest.adapters.claude_code import claude_code_adapter, load_claude_transcript
    from procgrep.ingest.adapters.codex import codex_adapter, load_codex_session
    from procgrep.ingest.adapters.gemini_cli import gemini_cli_adapter, load_gemini_session

    result: dict[str, list[str]] = {}
    for source in selected:
        path = frozen_home / source["home_relative"]
        if source["vendor"] == "claude":
            record = load_claude_transcript(path)
            atoms = claude_code_adapter(record)
        elif source["vendor"] == "codex":
            rows = load_json_or_jsonl(path)
            record = load_codex_session(rows)
            atoms = codex_adapter(record)
        else:
            obj = load_json_or_jsonl(path)
            record = load_gemini_session(obj)
            atoms = gemini_cli_adapter(record)
        if not atoms:
            raise RuntimeError(f"official ProcGrep produced an empty trace for {source['source_id']}")
        result[f"{source['vendor']}:{source['native_session_id']}"] = list(atoms)
    return result


def audit_manifest(private: Path) -> str:
    rows = []
    for path in sorted(private.rglob("*")):
        if path.is_file() and path.name != "audit-manifest.sha256":
            rows.append(f"{sha256_file(path)}  {path.relative_to(private)}")
    text = "\n".join(rows) + "\n"
    (private / "audit-manifest.sha256").write_text(text)
    return sha256_bytes(text.encode())


def copy_selected(selected: list[dict[str, Any]], home: Path, frozen_home: Path) -> None:
    for index, row in enumerate(selected):
        source = Path(row["source_path"])
        relative = home_relative(source, home)
        destination = frozen_home / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination)
        os.utime(destination, ns=(row["mtime_ns"], row["mtime_ns"]))
        if sha256_file(destination) != row["sha256"]:
            raise RuntimeError(f"copy hash mismatch: {source}")
        row["home_relative"] = str(relative)
        row["source_id"] = f"S{index:03d}-{row['sha256'][:10]}"


def source_stability(selected_by_project: list[dict[str, Any]], wait_seconds: int = 60) -> None:
    before = {}
    for project in selected_by_project:
        for row in project["sources"]:
            path = Path(row["source_path"])
            before[str(path)] = (path.stat().st_size, path.stat().st_mtime_ns, sha256_file(path))
    if wait_seconds:
        print(f"[rq7] stability wait {wait_seconds}s for {len(before)} selected native files", flush=True)
        time.sleep(wait_seconds)
    for raw, state in before.items():
        path = Path(raw)
        after = (path.stat().st_size, path.stat().st_mtime_ns, sha256_file(path))
        if after != state:
            raise RuntimeError(f"selected native source changed during stability interval: {path}")


def sanitize_question(row: dict[str, Any], spec_hash: str) -> dict[str, Any]:
    return {
        "id": row["id"],
        "project": row["project"],
        "family": row["family"],
        "template": row["template"],
        "path_id": row["path_id"],
        "witness_hash": sha256_bytes("\n".join(row["witnesses"]).encode()),
        "question_spec_sha256": spec_hash,
    }


def finalize_freeze(private: Path, release: Path) -> int:
    freeze_data = read_json(private / "freeze.json")
    checker_result = read_json(private / "oracle-check.json")
    if checker_result.get("status") != "pass":
        raise RuntimeError(f"independent oracle checker failed: {checker_result}")
    freeze_data["oracle_checker_sha256"] = checker_result["checker_sha256"]
    write_json(private / "freeze.json", freeze_data)
    manifest_hash = audit_manifest(private)
    write_json(release / "freeze-summary.json", {
        "spec_version": freeze_data.get("spec_version"),
        "projects": len(freeze_data["projects"]),
        "questions": len(freeze_data["questions"]),
        "questions_per_family": dict(Counter(row["family"] for row in freeze_data["questions"])),
        "vendors": dict(Counter(
            source["vendor"] for project in freeze_data["projects"] for source in project["sources"]
        )),
        "question_spec_sha256": freeze_data["question_spec_sha256"],
        "private_audit_manifest_sha256": manifest_hash,
        "oracle_checker_sha256": checker_result["checker_sha256"],
        "split_audit": freeze_data.get("split_audit", {}),
    })
    print(f"[rq7] freeze complete: {len(freeze_data['questions'])} questions; audit {manifest_hash}")
    return 0


def freeze(args: argparse.Namespace) -> int:
    private = args.private.resolve()
    release = args.release.resolve()
    if private.exists() or release.exists():
        raise RuntimeError("freeze is append-only; private/release target already exists")
    private.mkdir(parents=True)
    release.mkdir(parents=True)
    if sha256_file(args.projects_file.resolve()) != FROZEN_PROJECTS_SHA256:
        raise RuntimeError("projects file does not match the preregistered hash")
    projects_input = read_json(args.projects_file)
    if not isinstance(projects_input, list) or len(projects_input) != FROZEN_PROJECT_COUNT:
        raise RuntimeError("RQ7 freeze requires the fixed six-project projects.json")
    home = Path.home()
    excluded_hashes: set[str] = set()
    excluded_roots: set[tuple[str, str]] = set()
    excluded_calls: set[tuple[str, str, str]] = set()
    exclusion_paths = [path.resolve() for path in (args.exclude_freeze or [])]
    exclusion_hashes = {sha256_file(path) for path in exclusion_paths}
    if len(exclusion_paths) != 2 or exclusion_hashes != EXPECTED_EXCLUSION_SHA256:
        raise RuntimeError(
            "exclusion manifests do not match the preregistered Step 0004 + "
            "invalid Experiment 001 union"
        )
    for exclusion_path in exclusion_paths:
        excluded = read_json(exclusion_path)
        archive = exclusion_path.parent / "frozen-home"
        for project in excluded["projects"]:
            for source in project["sources"]:
                vendor = str(source["vendor"])
                archived_source = archive / str(source.get("home_relative") or "")
                if not archived_source.is_file():
                    raise RuntimeError(f"missing exclusion source archive: {archived_source}")
                if archived_source.stat().st_size != int(source["bytes"]):
                    raise RuntimeError(f"exclusion source size mismatch: {archived_source}")
                if sha256_file(archived_source) != str(source["sha256"]):
                    raise RuntimeError(f"exclusion source hash mismatch: {archived_source}")
                native_root = native_root_from_path(
                    vendor,
                    archived_source,
                    str(source["native_session_id"]),
                )
                excluded_hashes.add(str(source["sha256"]))
                excluded_roots.add((vendor, native_root))
                for event in native_events(
                    vendor,
                    archived_source,
                    {"worktree": str(project["worktree"])},
                ):
                    if event.get("kind") == "tool":
                        excluded_calls.add(
                            (
                                vendor,
                                native_root,
                                str(event.get("call_id") or ""),
                            )
                        )
    cutoff_ns = args.cutoff_ns
    projects: list[dict[str, Any]] = []
    all_roots: dict[str, list[Path]] = {}
    for source_project in projects_input:
        repo = canonical(Path(source_project["repository_root"]))
        roots = worktrees(repo)
        all_roots[source_project["project"]] = roots
    unique_roots = sorted({root for roots in all_roots.values() for root in roots})
    print(f"[rq7] discovering native sessions once across {len(unique_roots)} worktrees", flush=True)
    discovered = discover_sources(home, unique_roots, cutoff_ns, args.raw_bytes)
    for source_project in projects_input:
        repo = canonical(Path(source_project["repository_root"]))
        roots = all_roots[source_project["project"]]
        root_strings = {str(canonical(root)) for root in roots}
        candidates = [
            row
            for row in discovered
            if row["worktree"] in root_strings
            and row["sha256"] not in excluded_hashes
            and (row["vendor"], row["native_session_id"]) not in excluded_roots
        ]
        selected_root, selected = select_sources(
            candidates, args.raw_bytes, args.sessions, args.seed
        )
        if len(selected) != FROZEN_SESSIONS_PER_PROJECT:
            raise RuntimeError(
                f"{source_project['project']} did not yield exactly "
                f"{FROZEN_SESSIONS_PER_PROJECT} roots"
            )
        projects.append({
            "project": source_project["project"],
            "repository_root": str(repo),
            "worktree": str(selected_root),
            "sources": selected,
        })
        print(f"[rq7] selected {len(selected):2d} sessions for {source_project['project']} at {selected_root}")
    source_stability(projects, args.stability_wait)
    frozen_home = private / "frozen-home"
    all_questions = []
    release_sources = []
    selected_hashes: set[str] = set()
    selected_roots: set[tuple[str, str]] = set()
    selected_calls: set[tuple[str, str, str]] = set()
    for project in projects:
        copy_selected(project["sources"], home, frozen_home)
        direct = direct_atoms(project["sources"], frozen_home)
        official = official_procgrep_atoms(args.procgrep.resolve(), project["sources"], frozen_home)
        project["direct_action_atoms"] = direct
        project["procgrep_action_atoms"] = official
        edges, sessions, calls = artifact_edges(project, project["sources"], frozen_home)
        anchors = choose_anchors(edges)
        snapshot = workspace_snapshot(
            Path(project["worktree"]),
            anchors,
            private / "workspace" / project["project"],
        )
        source_cutoff = max(
            (row.get("last_ts_ms") or 0 for row in project["sources"]),
            default=0,
        )
        if source_cutoff > snapshot["cutoff_ms"]:
            raise RuntimeError(f"source cutoff exceeds workspace cutoff: {project['project']}")
        questions = question_rows(project, direct, edges, sessions, anchors, snapshot)
        if len(questions) != 20:
            raise RuntimeError("fixed grammar did not produce 20 questions")
        all_questions.extend(questions)
        selected_hashes.update(str(row["sha256"]) for row in project["sources"])
        selected_roots.update(
            (str(row["vendor"]), str(row["native_session_id"]))
            for row in project["sources"]
        )
        selected_calls.update(
            (
                str(call["vendor"]),
                str(call["native_session_id"]).split(":", 1)[1],
                str(call["call_id"]),
            )
            for call in calls
        )
        project.update({
            "sessions": sessions,
            "anchors": anchors,
            "workspace": snapshot,
            "source_cutoff_ms": source_cutoff,
            "oracle_edges": edges,
            "oracle_calls": calls,
            "questions": questions,
        })
        for row in project["sources"]:
            release_sources.append({
                "project": project["project"],
                "vendor": row["vendor"],
                "source_id": row["source_id"],
                "bytes": row["bytes"],
                "sha256": row["sha256"],
                "session_id_hash": sha256_bytes(row["session_id"].encode())[:16],
                "worktree_id": worktree_id(Path(project["worktree"])),
            })
    spec = question_spec()
    spec_path = private / "question-spec.md"
    spec_path.write_text(spec)
    spec_hash = sha256_bytes(spec.encode())
    freeze_data = {
        "seed": args.seed,
        "spec_version": SPEC_VERSION,
        "created_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "agent_revision": run(["git", "rev-parse", "HEAD"], cwd=Path(__file__).parents[2]).strip(),
        "agentvis_cargo_lock_sha256": sha256_file(Path(__file__).parents[1] / "Cargo.lock"),
        "procgrep_revision": run(["git", "rev-parse", "HEAD"], cwd=args.procgrep).strip(),
        "procgrep_lock_sha256": sha256_file(args.procgrep / "uv.lock"),
        "codex_version": run(["codex", "--version"]).strip(),
        "python_version": sys.version,
        "question_spec_sha256": spec_hash,
        "projects_file_sha256": sha256_file(args.projects_file.resolve()),
        "discovery_cutoff_ns": cutoff_ns,
        "source_count_contract": {
            "projects": FROZEN_PROJECT_COUNT,
            "sources_per_project": FROZEN_SESSIONS_PER_PROJECT,
            "total_sources": FROZEN_PROJECT_COUNT * FROZEN_SESSIONS_PER_PROJECT,
        },
        "projects": projects,
        "questions": all_questions,
        "split_audit": {
            "excluded_freezes": [str(path) for path in exclusion_paths],
            "file_hash_overlap": len(selected_hashes & excluded_hashes),
            "native_root_overlap": len(selected_roots & excluded_roots),
            "native_root_call_overlap": len(selected_calls & excluded_calls),
            "selected_file_hashes": len(selected_hashes),
            "selected_native_roots": len(selected_roots),
        },
    }
    if any(
        freeze_data["split_audit"][key] != 0
        for key in ("file_hash_overlap", "native_root_overlap", "native_root_call_overlap")
    ):
        raise RuntimeError(f"held-out split overlap: {freeze_data['split_audit']}")
    if len(selected_hashes) != FROZEN_PROJECT_COUNT * FROZEN_SESSIONS_PER_PROJECT:
        raise RuntimeError("held-out source hashes are not globally distinct")
    if len(selected_roots) != FROZEN_PROJECT_COUNT * FROZEN_SESSIONS_PER_PROJECT:
        raise RuntimeError("held-out semantic roots are not globally distinct")
    write_json(private / "freeze.json", freeze_data)
    write_json(private / "oracle-questions.json", all_questions)
    write_csv(
        release / "freeze-sources.csv",
        ["project", "vendor", "source_id", "bytes", "sha256", "session_id_hash", "worktree_id"],
        release_sources,
    )
    public_questions = [sanitize_question(row, spec_hash) for row in all_questions]
    write_csv(
        release / "questions.csv",
        ["id", "project", "family", "template", "path_id", "witness_hash", "question_spec_sha256"],
        public_questions,
    )
    checker = Path(__file__).with_name("rq7_source_oracle_check.py")
    run([sys.executable, str(checker), str(private / "freeze.json"), str(private / "oracle-check.json")])
    return finalize_freeze(private, release)


def recover_freeze(args: argparse.Namespace) -> int:
    if read_json(args.private / "freeze.json").get("spec_version") == SPEC_VERSION:
        raise RuntimeError("v3 scientific freezes are immutable; recovery is disabled")
    checker = Path(__file__).with_name("rq7_source_oracle_check.py")
    run([
        sys.executable,
        str(checker),
        str(args.private / "freeze.json"),
        str(args.private / "oracle-check.json"),
    ])
    return finalize_freeze(args.private.resolve(), args.release.resolve())


def rederive_freeze(args: argparse.Namespace) -> int:
    """Recompute the oracle from one immutable archive without live discovery."""
    source_private = args.source_private.resolve()
    if read_json(source_private / "freeze.json").get("spec_version") == SPEC_VERSION:
        raise RuntimeError("v3 scientific freezes cannot be rederived")
    private = args.private.resolve()
    release = args.release.resolve()
    if private.exists():
        shutil.rmtree(private)
    if release.exists():
        shutil.rmtree(release)
    private.mkdir(parents=True)
    release.mkdir(parents=True)

    def link_or_copy(source: str, destination: str) -> str:
        try:
            os.link(source, destination)
        except OSError:
            shutil.copy2(source, destination)
        return destination

    shutil.copytree(
        source_private / "frozen-home",
        private / "frozen-home",
        copy_function=link_or_copy,
    )
    shutil.copytree(
        source_private / "workspace",
        private / "workspace",
        copy_function=link_or_copy,
    )
    prior = read_json(source_private / "freeze.json")
    projects = []
    questions = []
    release_sources = []
    for prior_project in prior["projects"]:
        project = {
            key: value
            for key, value in prior_project.items()
            if key not in {
                "direct_action_atoms",
                "procgrep_action_atoms",
                "oracle_edges",
                "sessions",
                "anchors",
                "questions",
                "workspace",
            }
        }
        selected = project["sources"]
        direct = direct_atoms(selected, private / "frozen-home")
        official = official_procgrep_atoms(args.procgrep.resolve(), selected, private / "frozen-home")
        edges, sessions, calls = artifact_edges(project, selected, private / "frozen-home")
        anchors = choose_anchors(edges)
        prior_snapshot = prior_project["workspace"]
        prior_paths = [row["path"] for row in prior_snapshot["paths"]]
        new_paths = [row["path"] for row in anchors]
        if args.refresh_workspace:
            destination = private / "workspace" / project["project"]
            if destination.exists():
                shutil.rmtree(destination)
            snapshot = workspace_snapshot(
                Path(project["worktree"]),
                anchors,
                destination,
            )
        else:
            if prior_paths != new_paths:
                raise RuntimeError(
                    f"corrected anchors require --refresh-workspace for {project['project']}: "
                    f"prior={prior_paths}, corrected={new_paths}"
                )
            snapshot = {
                **prior_snapshot,
                "paths": [
                    {**old, **anchor}
                    for old, anchor in zip(prior_snapshot["paths"], anchors)
                ],
            }
        project_questions = question_rows(project, direct, edges, sessions, anchors, snapshot)
        project.update({
            "direct_action_atoms": direct,
            "procgrep_action_atoms": official,
            "oracle_edges": edges,
            "oracle_calls": calls,
            "sessions": sessions,
            "anchors": anchors,
            "workspace": snapshot,
            "questions": project_questions,
        })
        projects.append(project)
        questions.extend(project_questions)
        for row in selected:
            release_sources.append({
                "project": project["project"],
                "vendor": row["vendor"],
                "source_id": row["source_id"],
                "bytes": row["bytes"],
                "sha256": row["sha256"],
                "session_id_hash": sha256_bytes(row["session_id"].encode())[:16],
                "worktree_id": worktree_id(Path(project["worktree"])),
            })

    spec = question_spec()
    (private / "question-spec.md").write_text(spec)
    spec_hash = sha256_bytes(spec.encode())
    freeze_data = {
        key: value
        for key, value in prior.items()
        if key not in {"projects", "questions", "oracle_checker_sha256"}
    }
    freeze_data.update({
        "created_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "agent_revision": run(["git", "rev-parse", "HEAD"], cwd=Path(__file__).parents[2]).strip(),
        "procgrep_revision": run(["git", "rev-parse", "HEAD"], cwd=args.procgrep.resolve()).strip(),
        "procgrep_lock_sha256": sha256_file(args.procgrep.resolve() / "uv.lock"),
        "codex_version": run(["codex", "--version"]).strip(),
        "python_version": sys.version,
        "question_spec_sha256": spec_hash,
        "source_archive_parent_sha256": sha256_file(source_private / "freeze.json"),
        "projects": projects,
        "questions": questions,
    })
    write_json(private / "freeze.json", freeze_data)
    write_json(private / "oracle-questions.json", questions)
    write_csv(
        release / "freeze-sources.csv",
        ["project", "vendor", "source_id", "bytes", "sha256", "session_id_hash", "worktree_id"],
        release_sources,
    )
    write_csv(
        release / "questions.csv",
        [
            "id",
            "project",
            "family",
            "template",
            "path_id",
            "witness_hash",
            "question_spec_sha256",
        ],
        [sanitize_question(row, spec_hash) for row in questions],
    )
    checker = Path(__file__).with_name("rq7_source_oracle_check.py")
    run([
        sys.executable,
        str(checker),
        str(private / "freeze.json"),
        str(private / "oracle-check.json"),
    ])
    return finalize_freeze(private, release)


def build_agent_session_projection(
    private: Path,
    destination: Path,
    project_names: set[str] | None = None,
    binary_override: Path | None = None,
) -> tuple[dict[str, dict[str, Any]], float]:
    freeze_data = read_json(private / "freeze.json")
    projects = [
        project
        for project in freeze_data["projects"]
        if project_names is None or project["project"] in project_names
    ]
    repo_root = Path(__file__).parents[2]
    override = str(binary_override) if binary_override else os.environ.get("RQ7_AGENTVIS_BINARY")
    binary = (
        Path(override).resolve()
        if override
        else repo_root / "agentvis" / "target" / "release" / "agentvis"
    )
    build_started = time.perf_counter()
    if not override:
        run(["cargo", "build", "--release", "--locked", "--manifest-path", str(repo_root / "agentvis" / "Cargo.toml")], cwd=repo_root)
    elif not binary.is_file():
        raise RuntimeError(f"RQ7_AGENTVIS_BINARY does not exist: {binary}")
    if destination.exists():
        raise RuntimeError(f"projection output is append-only: {destination}")
    raw = destination / "raw"
    roots = [project["worktree"] for project in projects]
    cutoff = max(project["workspace"]["cutoff_ms"] for project in projects)
    env = os.environ.copy()
    env["HOME"] = str(private / "frozen-home")
    command = [
        str(binary),
        "research-rq1",
        "--output",
        str(raw),
        "--cutoff-ms",
        str(cutoff),
        *roots,
    ]
    log = run(command, cwd=repo_root, env=env)
    (destination / "command.txt").write_text(shlex.join(command) + "\n" + log)
    traces = [read_json(path) for path in sorted((raw / "events").glob("*.json"))]
    mapped: dict[str, dict[str, Any]] = {}
    for project in projects:
        expected = {
            identity
            for source in project["sources"]
            for identity in (source["source_stem"], source["native_session_id"])
        }
        ranked = []
        for trace in traces:
            actual = {str(event.get("session_id") or "") for event in trace.get("events") or []}
            overlap = sum(any(sid == raw_sid or sid in raw_sid or raw_sid in sid for raw_sid in actual) for sid in expected)
            ranked.append((overlap, trace))
        ranked.sort(key=lambda item: item[0], reverse=True)
        if not ranked or ranked[0][0] == 0:
            raise RuntimeError(f"agent-session projection did not contain {project['project']}")
        if len(ranked) > 1 and ranked[0][0] == ranked[1][0]:
            raise RuntimeError(f"ambiguous agent-session trace for {project['project']}")
        mapped[project["project"]] = ranked[0][1]
    return mapped, time.perf_counter() - build_started


def answer(status: str, value: Any = "") -> dict[str, str]:
    return {"status": status, "answer": str(value) if status == "answer" else ""}


def deterministic_methods(
    private: Path,
    output: Path,
    project_names: set[str] | None = None,
    projection_output: Path | None = None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    freeze_data = read_json(private / "freeze.json")
    projects = [
        project
        for project in freeze_data["projects"]
        if project_names is None or project["project"] in project_names
    ]
    projection, build_seconds = build_agent_session_projection(
        private,
        projection_output or output / "projection",
        project_names,
    )
    result_rows: list[dict[str, Any]] = []
    cost_rows: list[dict[str, Any]] = []
    conformance_rows: list[dict[str, Any]] = []
    project_query_seconds: dict[str, float] = {}
    query_started = time.perf_counter()
    for project in projects:
        project_started = time.perf_counter()
        official = project["procgrep_action_atoms"]
        procgrep_values = {
            "A1": str(sum(sequence.count("read_file") for sequence in official.values())),
            "A2": str(sum(sequence.count("edit") for sequence in official.values())),
            "A3": str(sum(sequence.count("run_test") for sequence in official.values())),
            "A4": str(pattern_count(official, r"read_file (?:[a-z_]+ )*edit ")),
            "A5": str(pattern_count(official, r"edit (?:[a-z_]+ )*run_test ")),
        }
        pedges, pcalls, production_atoms, join_error = production_projection(
            project, projection[project["project"]]
        )
        if join_error:
            raise RuntimeError(join_error)
        action_values = {
            "A1": str(sum(sequence.count("read_file") for sequence in production_atoms.values())),
            "A2": str(sum(sequence.count("edit") for sequence in production_atoms.values())),
            "A3": str(sum(sequence.count("run_test") for sequence in production_atoms.values())),
            "A4": str(pattern_count(production_atoms, r"read_file (?:[a-z_]+ )*edit ")),
            "A5": str(pattern_count(production_atoms, r"edit (?:[a-z_]+ )*run_test ")),
        }
        conformance_rows.append(projection_conformance(project, pedges, pcalls))
        p0_path = project["anchors"][0]["path"]
        p0_candidates = {
            row["artifact_id"]
            for row in pedges
            if row["path"] == p0_path or row["display_path"] == p0_path
        }
        p0_identity = (
            max(
                p0_candidates,
                key=lambda identity: sum(row["artifact_id"] == identity for row in pedges),
            )
            if p0_candidates
            else None
        )
        relation = relation_values(pedges, len(project["sessions"]), p0_identity) if p0_identity else None
        final_by_template = {
            f"D{index}": row["status"] for index, row in enumerate(project["workspace"]["paths"], start=1)
        }
        projected_paths = {row["display_path"] for row in pedges} | {row["path"] for row in pedges}
        questions = [row for row in freeze_data["questions"] if row["project"] == project["project"]]
        for question in questions:
            template = question["template"]
            family = question["family"]
            methods: dict[str, dict[str, str]] = {}
            methods["procgrep"] = answer("answer", procgrep_values[template]) if family == "A" else answer("abstain")
            methods["counts"] = answer("answer", action_values[template]) if template in {"A1", "A2", "A3"} else answer("abstain")
            methods["final_state"] = answer("answer", final_by_template[template]) if family == "D" else answer("abstain")
            if family == "A":
                methods["trajectory"] = answer("answer", action_values[template])
            elif family in {"B", "C"}:
                methods["trajectory"] = answer("answer", relation[template]) if relation else answer("abstain")
            else:
                path = project["workspace"]["paths"][int(template[1:]) - 1]["path"]
                methods["trajectory"] = answer("answer", final_by_template[template]) if path in projected_paths else answer("abstain")
            for method, value in methods.items():
                result_rows.append({
                    "id": question["id"],
                    "project": project["project"],
                    "family": family,
                    "template": template,
                    "method": method,
                    "repetition": 0,
                    "status": value["status"],
                    "answer": value["answer"],
                    "expected": question["answer"],
                    "correct": int(value["status"] == "answer" and value["answer"] == question["answer"]),
                    "wrong": int(value["status"] == "answer" and value["answer"] != question["answer"]),
                    "question_spec_sha256": freeze_data["question_spec_sha256"],
                })
        project_query_seconds[project["project"]] = time.perf_counter() - project_started
    query_seconds = time.perf_counter() - query_started
    for project in projects:
        for method in ("procgrep", "counts", "final_state", "trajectory"):
            construction = build_seconds / len(projects) if method == "trajectory" else 0.0
            query = project_query_seconds[project["project"]]
            cost_rows.append({
                "project": project["project"],
                "method": method,
                "repetition": 0,
                "source_bytes": sum(source["bytes"] for source in project["sources"]),
                "input_bytes": 0,
                "output_bytes": 0,
                "input_tokens": 0,
                "cached_input_tokens": 0,
                "output_tokens": 0,
                "reasoning_tokens": 0,
                "model_calls": 0,
                "tool_calls": 0,
                "build_seconds": f"{construction:.6f}",
                "query_seconds": f"{query:.6f}",
                "wall_seconds": f"{construction + query:.6f}",
                "peak_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                "terminal_status": "complete",
            })
    write_json(output / "deterministic-results.json", result_rows)
    write_json(output / "deterministic-costs.json", cost_rows)
    write_json(output / "projection-conformance.json", conformance_rows)
    return result_rows, cost_rows


QUESTION_TEXT = {
    "A1": "How many read_file atoms occur across all selected sessions?",
    "A2": "How many edit atoms occur across all selected sessions?",
    "A3": "How many run_test atoms occur across all selected sessions?",
    "A4": "How many selected sessions contain a read_file atom before a later edit atom?",
    "A5": "How many selected sessions contain an edit atom before a later run_test atom?",
    "B1": "How many distinct attempted tool calls reference P0?",
    "B2": "How many distinct attempted P0 calls are reads?",
    "B3": "How many distinct attempted P0 calls are mutations?",
    "B4": "Is the first P0 action class read or mutate?",
    "B5": "How many distinct selected sessions reference P0?",
    "C1": "How many adjacent chronological session pairs share at least one artifact?",
    "C2": "How many sessions after the first revisit any artifact from an earlier session?",
    "C3": "How many P0 return episodes occur after one or more intervening sessions without P0?",
    "C4": "What is P0's last-session ordinal minus first-session ordinal?",
    "C5": "How many artifacts are referenced in at least two distinct sessions?",
    "D1": "At cutoff, is P0 tracked, untracked, or absent?",
    "D2": "At cutoff, is P1 tracked, untracked, or absent?",
    "D3": "At cutoff, is P2 tracked, untracked, or absent?",
    "D4": "At cutoff, is P3 tracked, untracked, or absent?",
    "D5": "At cutoff, is P4 tracked, untracked, or absent?",
}


def model_schema(path: Path) -> None:
    write_json(path, {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "object",
        "additionalProperties": False,
        "required": ["answers"],
        "properties": {
            "answers": {
                "type": "array",
                "minItems": 20,
                "maxItems": 20,
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["id", "status", "answer", "evidence"],
                    "properties": {
                        "id": {"type": "string"},
                        "status": {"type": "string", "enum": ["answer", "abstain"]},
                        "answer": {"type": "string"},
                        "evidence": {"type": "array", "items": {"type": "string"}, "maxItems": 20},
                    },
                },
            }
        },
    })


def prepare_model_sandbox(
    freeze_data: dict[str, Any], project: dict[str, Any], private: Path
) -> Path:
    spec = (private / "question-spec.md").read_text()
    if sha256_bytes(spec.encode()) != freeze_data["question_spec_sha256"]:
        raise RuntimeError("question specification hash changed")
    sandbox = private / "raw-sandboxes" / project["project"]
    if sandbox.exists():
        shutil.rmtree(sandbox)
    sources_dir = sandbox / "sources"
    sources_dir.mkdir(parents=True)
    shutil.copyfile(private / "question-spec.md", sandbox / "question-spec.md")
    question_lines = ["# Project anchors", ""]
    for index, anchor in enumerate(project["anchors"]):
        question_lines.append(f"P{index} = {anchor['path']}")
    question_lines.extend(["", "# Questions", ""])
    for question in project["questions"]:
        question_lines.append(f"{question['id']}: {QUESTION_TEXT[question['template']]}")
    (sandbox / "questions.md").write_text("\n".join(question_lines) + "\n")
    write_json(sandbox / "cutoff-manifest.json", {
        "head": project["workspace"]["head"],
        "paths": [
            {
                "anchor": f"P{index}",
                "path": row["path"],
                "index_entry": row["index_entry"],
                "present": row["present"],
                "content_sha256": row["content_sha256"],
            }
            for index, row in enumerate(project["workspace"]["paths"])
        ],
    })
    frozen_home = private / "frozen-home"
    source_index = []
    for source in project["sources"]:
        suffix = ".json" if source["vendor"] == "gemini" else ".jsonl"
        name = f"{source['source_id']}-{source['vendor']}{suffix}"
        origin = frozen_home / source["home_relative"]
        destination = sources_dir / name
        try:
            os.link(origin, destination)
        except OSError:
            shutil.copyfile(origin, destination)
        source_index.append({
            "source_id": source["source_id"],
            "vendor": source["vendor"],
            "file": f"sources/{name}",
            "bytes": source["bytes"],
            "sha256": source["sha256"],
        })
    write_json(sandbox / "source-index.json", source_index)
    return sandbox


def render_model_prompt(freeze_data: dict[str, Any], sandbox: Path) -> str:
    return (
        "Analyze only the read-only evidence directory that is your current working directory. "
        "Read question-spec.md first, then questions.md, cutoff-manifest.json, source-index.json, "
        "and the complete native records under sources/. Use ordinary local rg, jq, sed, or "
        "Python one-liners as needed. Do not access parent/outside files, the network, or outside "
        "knowledge. Answer every listed question using the required JSON schema; use abstain when "
        "the bytes do not establish an exact answer, and cite source_id plus native record/call "
        f"locator. QUESTION_SPEC_SHA256={freeze_data['question_spec_sha256']}; "
        f"SANDBOX={sandbox.name}.\n"
    )


def rss_tree_kib(pid: int) -> int:
    seen: set[int] = set()
    pending = [pid]
    total = 0
    while pending:
        current = pending.pop()
        if current in seen:
            continue
        seen.add(current)
        try:
            for line in Path(f"/proc/{current}/status").read_text().splitlines():
                if line.startswith("VmRSS:"):
                    total += int(line.split()[1])
                    break
            children = Path(f"/proc/{current}/task/{current}/children").read_text().split()
            pending.extend(int(child) for child in children)
        except (OSError, ValueError):
            continue
    return total


def token_usage(jsonl: Path) -> dict[str, int]:
    candidates: list[dict[str, int]] = []

    def visit(value: Any) -> None:
        if isinstance(value, dict):
            if "input_tokens" in value and "output_tokens" in value:
                candidates.append({
                    "input_tokens": int(value.get("input_tokens") or 0),
                    "cached_input_tokens": int(value.get("cached_input_tokens") or value.get("cache_read_tokens") or 0),
                    "output_tokens": int(value.get("output_tokens") or 0),
                    "reasoning_tokens": int(value.get("reasoning_output_tokens") or value.get("reasoning_tokens") or 0),
                })
            for child in value.values():
                visit(child)
        elif isinstance(value, list):
            for child in value:
                visit(child)

    if jsonl.exists():
        for raw in jsonl.read_text(errors="replace").splitlines():
            try:
                visit(json.loads(raw))
            except json.JSONDecodeError:
                continue
    if not candidates:
        return {key: 0 for key in ("input_tokens", "cached_input_tokens", "output_tokens", "reasoning_tokens")}
    return max(candidates, key=lambda row: sum(row.values()))


def retrieval_event(value: Any, sandbox: Path) -> tuple[str | None, int, str | None]:
    if not isinstance(value, dict):
        return None, 0, None
    envelope_type = str(value.get("type") or "").lower()
    item = value.get("item") if isinstance(value.get("item"), dict) else value
    item_type = str(item.get("type") or "").lower()
    if item_type not in {"command_execution", "function_call", "tool_call", "mcp_tool_call"}:
        return None, 0, None
    call_id = str(item.get("id") or item.get("call_id") or sha256_bytes(json.dumps(item, sort_keys=True).encode())[:16])
    command = str(item.get("command") or item.get("arguments") or "")
    violation = command_access_violation(command, sandbox) if command else None
    returned = 0
    if envelope_type.endswith("completed") or item.get("status") in {"completed", "failed"}:
        result = item.get("aggregated_output", item.get("output", item.get("result", item.get("content", ""))))
        if isinstance(result, str):
            returned = len(result.encode())
        elif result:
            returned = len(json.dumps(result, ensure_ascii=False).encode())
    return call_id, returned, violation


def command_access_violation(command: str, sandbox: Path) -> str | None:
    if re.search(r"https?://|\b(curl|wget|ssh|scp|rsync)\b|\bgit\s+(clone|fetch|pull)\b", command, re.I):
        return "network_or_remote_command"
    allowed_prefixes = (
        str(sandbox),
        "/work/",
        "/bin/",
        "/usr/bin/",
        "/usr/local/bin/",
        "/dev/null",
        "/proc/",
        "/tmp/",
    )
    for token in re.findall(r"(?<![A-Za-z0-9_])(/[A-Za-z0-9_./+@=-]+)", command):
        if token in {"/", "//"}:
            continue
        if not token.startswith(allowed_prefixes):
            return f"outside_absolute_path:{token}"
    for token in re.findall(r"(?:^|\s)(\.\.?/[A-Za-z0-9_./+@=-]+)", command):
        if token.startswith("../"):
            try:
                (sandbox / token).resolve().relative_to(sandbox.resolve())
            except ValueError:
                return f"outside_relative_path:{token}"
    return None


def model_call(
    freeze_data: dict[str, Any],
    project: dict[str, Any],
    private: Path,
    destination: Path,
    model: str,
    reasoning: str,
    repetition: int,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    private = private.resolve()
    destination = destination.resolve()
    destination.mkdir(parents=True, exist_ok=True)
    sandbox = prepare_model_sandbox(freeze_data, project, private)
    prompt = render_model_prompt(freeze_data, sandbox)
    prompt_path = destination / "prompt.txt"
    prompt_path.write_text(prompt)
    schema = sandbox / "model-answer.schema.json"
    model_schema(schema)
    response = destination / "response.json"
    events = destination / "events.jsonl"
    stderr = destination / "stderr.log"
    codex_binary = Path(shutil.which("codex") or "").resolve()
    auth_file = Path(os.environ.get("CODEX_HOME", str(Path.home() / ".codex"))) / "auth.json"
    if not codex_binary.is_file() or not auth_file.is_file():
        raise RuntimeError("isolated Raw runner requires the Codex binary and auth.json")
    inner_command = [
        "/usr/local/bin/codex",
        "exec",
        "--ignore-user-config",
        "--ignore-rules",
        "--strict-config",
        "--ephemeral",
        "--skip-git-repo-check",
        "--sandbox",
        "read-only",
        "--cd",
        "/work",
        "--model",
        model,
        "--config",
        f'model_reasoning_effort="{reasoning}"',
        "--disable",
        "apps",
        "--disable",
        "browser_use",
        "--disable",
        "browser_use_external",
        "--disable",
        "image_generation",
        "--disable",
        "multi_agent_v2",
        "--output-schema",
        "/work/model-answer.schema.json",
        "--json",
        "--output-last-message",
        "/out/response.json",
        "-",
    ]
    command = [
        "timeout",
        "--signal=TERM",
        "--kill-after=30s",
        "900s",
        "bwrap",
        "--die-with-parent",
        "--unshare-pid",
        "--clearenv",
        "--ro-bind",
        "/usr",
        "/usr",
        "--ro-bind",
        "/bin",
        "/bin",
        "--ro-bind",
        "/lib",
        "/lib",
        "--ro-bind",
        "/lib64",
        "/lib64",
        "--ro-bind",
        "/etc",
        "/etc",
        "--proc",
        "/proc",
        "--dev",
        "/dev",
        "--tmpfs",
        "/tmp",
        "--tmpfs",
        "/home",
        "--dir",
        "/run",
        "--dir",
        "/run/systemd",
        "--ro-bind",
        "/run/systemd/resolve",
        "/run/systemd/resolve",
        "--dir",
        "/home/codex",
        "--dir",
        "/home/codex/.codex",
        "--ro-bind",
        str(auth_file),
        "/home/codex/.codex/auth.json",
        "--ro-bind",
        str(codex_binary),
        "/usr/local/bin/codex",
        "--ro-bind",
        str(sandbox),
        "/work",
        "--bind",
        str(destination),
        "/out",
        "--setenv",
        "HOME",
        "/home/codex",
        "--setenv",
        "CODEX_HOME",
        "/home/codex/.codex",
        "--setenv",
        "PATH",
        "/usr/local/bin:/usr/bin:/bin",
        "--chdir",
        "/work",
        "--",
        *inner_command,
    ]
    (destination / "command.txt").write_text(shlex.join(command) + "\n")
    started = time.perf_counter()
    tool_ids: set[str] = set()
    tool_result_bytes = 0
    boundary_violation: str | None = None
    with events.open("wb") as events_handle, stderr.open("wb") as stderr_handle:
        process = subprocess.Popen(
            command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=stderr_handle,
            cwd=sandbox,
            start_new_session=True,
        )
        peak = 0
        stop = threading.Event()

        def monitor() -> None:
            nonlocal peak
            while not stop.wait(0.1):
                peak = max(peak, rss_tree_kib(process.pid))

        thread = threading.Thread(target=monitor, daemon=True)
        thread.start()
        assert process.stdin is not None
        assert process.stdout is not None
        try:
            process.stdin.write(prompt.encode())
            process.stdin.close()
        except BrokenPipeError:
            pass
        for raw in iter(process.stdout.readline, b""):
            events_handle.write(raw)
            events_handle.flush()
            try:
                event = json.loads(raw)
            except json.JSONDecodeError:
                continue
            call_id, returned, violation = retrieval_event(event, sandbox)
            if call_id:
                tool_ids.add(call_id)
            tool_result_bytes += returned
            if len(tool_ids) > 64:
                boundary_violation = "tool_call_cap"
            elif tool_result_bytes > 1_048_576:
                boundary_violation = "tool_result_byte_cap"
            elif violation:
                boundary_violation = violation
            if boundary_violation:
                os.killpg(process.pid, signal.SIGTERM)
                break
        try:
            returncode = process.wait(timeout=30 if boundary_violation else 930)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
            process.wait()
            returncode = 124
        stop.set()
        thread.join(timeout=1)
    wall = time.perf_counter() - started
    terminal = "complete"
    parsed: dict[str, Any] | None = None
    if boundary_violation:
        terminal = f"boundary_violation:{boundary_violation}"
    elif returncode == 0 and response.exists() and response.stat().st_size <= 65_536:
        try:
            value = read_json(response)
            ids = [row.get("id") for row in value.get("answers", []) if isinstance(row, dict)]
            expected_ids = [row["id"] for row in project["questions"]]
            if len(ids) == 20 and set(ids) == set(expected_ids):
                parsed = value
            else:
                terminal = "schema_or_id_failure"
        except (OSError, json.JSONDecodeError, AttributeError):
            terminal = "schema_or_id_failure"
    elif returncode == 124:
        terminal = "timeout"
    elif response.exists() and response.stat().st_size > 65_536:
        terminal = "oversized_output"
    else:
        terminal = f"exit_{returncode}"
    answer_map = {row["id"]: row for row in parsed.get("answers", [])} if parsed else {}
    result_rows = []
    for question in project["questions"]:
        value = answer_map.get(question["id"], {})
        status = value.get("status") if value.get("status") in {"answer", "abstain"} else "abstain"
        raw_answer = str(value.get("answer") or "").strip() if status == "answer" else ""
        result_rows.append({
            "id": question["id"],
            "project": project["project"],
            "family": question["family"],
            "template": question["template"],
            "method": "raw_model",
            "repetition": repetition,
            "status": status,
            "answer": raw_answer,
            "expected": question["answer"],
            "correct": int(status == "answer" and raw_answer == question["answer"]),
            "wrong": int(status == "answer" and raw_answer != question["answer"]),
            "question_spec_sha256": freeze_data["question_spec_sha256"],
        })
    usage = token_usage(events)
    cost = {
        "project": project["project"],
        "method": "raw_model",
        "repetition": repetition,
        "source_bytes": sum(source["bytes"] for source in project["sources"]),
        "input_bytes": len(prompt.encode()),
        "output_bytes": response.stat().st_size if response.exists() else 0,
        "tool_result_bytes": tool_result_bytes,
        **usage,
        "model_calls": 1,
        "tool_calls": len(tool_ids),
        "build_seconds": 0.0,
        "query_seconds": wall,
        "wall_seconds": wall,
        "peak_rss_kib": peak,
        "terminal_status": terminal,
    }
    write_json(destination / "scored.json", {"results": result_rows, "cost": cost})
    return result_rows, cost


def exact_conformance(rows: list[dict[str, Any]]) -> bool:
    for row in rows:
        groups = [row, *row["by_vendor"].values()]
        for group in groups:
            for name in (
                "session_order",
                "attempted_edges",
                "confirmed_effect_edges",
                "edge_call_statuses",
            ):
                metric = group[name]
                if metric["precision"] != 1.0 or metric["recall"] != 1.0:
                    return False
    return True


def run_deterministic(args: argparse.Namespace) -> int:
    rows, costs = deterministic_methods(args.private, args.output)
    print(f"[rq7] deterministic projection complete: {len(rows)} rows, {len(costs)} costs")
    return 0


def check_action_fixtures(args: argparse.Namespace) -> int:
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "rq7_source_oracle_check",
        Path(__file__).with_name("rq7_source_oracle_check.py"),
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("could not load independent source checker")
    checker = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(checker)
    fixtures = read_json(args.fixtures)
    for fixture in fixtures:
        name = str(fixture["tool"])
        raw_args = fixture["args"]
        primary_args = normalized_tool_arguments(name, raw_args)
        independent_args = checker.unwrap_exec(name, raw_args)
        if primary_args != independent_args:
            raise RuntimeError(f"argument normalization mismatch: {fixture['name']}")
        primary = event_path_actions({
            "kind": "tool",
            "tool": name,
            "args": primary_args,
        })
        independent = [
            {"path": path, "access": access, "previous_path": previous}
            for path, access, previous in checker.event_effects({
                "kind": "tool",
                "name": name,
                "args": independent_args,
            })
        ]
        if primary != fixture["actions"] or independent != fixture["actions"]:
            raise RuntimeError(
                f"action fixture mismatch {fixture['name']}: "
                f"primary={primary}, independent={independent}"
            )
    lifecycle_path = args.fixtures.parents[2] / "agentvis" / "tests" / "fixtures" / "strict-lifecycle.json"
    if not lifecycle_path.is_file():
        lifecycle_path = Path(__file__).parents[1] / "tests" / "fixtures" / "strict-lifecycle.json"
    lifecycle_fixtures = read_json(lifecycle_path)
    for fixture in lifecycle_fixtures:
        primary_tracker = ArtifactTracker(Path("/fixture"))
        independent_tracker = checker.Identities()
        for step in fixture["steps"]:
            expected = step["artifact_id"]
            primary_id = primary_tracker.identity(
                step["path"],
                step["access"],
                step.get("previous_path"),
                step["confirmed"],
                step.get("worktree", "w"),
                step.get("previous_worktree"),
            )
            independent_id = independent_tracker.resolve(
                step["path"],
                step["access"],
                step.get("previous_path"),
                step["confirmed"],
                step.get("worktree", "w"),
                step.get("previous_worktree"),
            )
            if primary_id != expected or independent_id != expected:
                raise RuntimeError(
                    f"lifecycle fixture mismatch {fixture['name']}: "
                    f"primary={primary_id}, independent={independent_id}, expected={expected}"
                )

    session_path = args.fixtures.with_name("native-root-identity.json")
    session_fixtures = read_json(session_path)
    for fixture in session_fixtures:
        payload = fixture["payload"]
        expected = str(fixture["expected"])
        primary = codex_native_root_id(payload, "fallback")
        independent = checker.codex_root_identity(payload, "fallback")
        if primary != expected or independent != expected:
            raise RuntimeError(
                f"native-root fixture mismatch {fixture['name']}: "
                f"primary={primary}, independent={independent}, expected={expected}"
            )

    repo = Path(__file__).resolve().parents[2]
    environment = {
        **os.environ,
        "RQ7_ACTION_FIXTURES": str(args.fixtures.resolve()),
        "RQ7_LIFECYCLE_FIXTURES": str(lifecycle_path.resolve()),
        "RQ7_SESSION_FIXTURES": str(session_path.resolve()),
    }
    for manifest, test_name in (
        (
            repo / "agent-session" / "Cargo.toml",
            "codex_native_root_matches_shared_fixture",
        ),
        (
            repo / "agent-session" / "Cargo.toml",
            "strict_action_grammar_matches_shared_fixture",
        ),
        (
            repo / "agentvis" / "Cargo.toml",
            "artifact_identity_matches_shared_lifecycle_fixture",
        ),
    ):
        completed = subprocess.run(
            [
                "cargo",
                "test",
                "--quiet",
                "--manifest-path",
                str(manifest),
                test_name,
            ],
            cwd=repo,
            env=environment,
            text=True,
            capture_output=True,
        )
        if completed.returncode:
            raise RuntimeError(
                f"production fixture failed {test_name}:\n"
                f"{completed.stdout}\n{completed.stderr}"
            )
    print(
        f"[rq7] shared fixtures pass: {len(fixtures)} action, "
        f"{len(lifecycle_fixtures)} lifecycle, {len(session_fixtures)} native-root, "
        "production + two independent oracles"
    )
    return 0


def seal_repaired_code(args: argparse.Namespace) -> int:
    output = args.output.resolve()
    if output.exists():
        raise RuntimeError(f"code seal already exists: {output}")
    private = args.private.resolve()
    freeze_data = read_json(private / "freeze.json")
    repo = Path(__file__).resolve().parents[2]
    if run(
        ["git", "status", "--porcelain", "--untracked-files=no"],
        cwd=repo,
    ).strip():
        raise RuntimeError("repaired repository has tracked modifications")
    revision = run(["git", "rev-parse", "HEAD"], cwd=repo).strip()
    tree = run(["git", "rev-parse", "HEAD^{tree}"], cwd=repo).strip()
    test_commands = [
        [
            sys.executable,
            str(Path(__file__).resolve()),
            "check-action-fixtures",
            "--fixtures",
            str(repo / "agent-session" / "tests" / "fixtures" / "strict-action-grammar.json"),
        ],
        ["cargo", "test", "--manifest-path", str(repo / "agent-session" / "Cargo.toml")],
        ["cargo", "test", "--manifest-path", str(repo / "agentvis" / "Cargo.toml")],
        ["cargo", "fmt", "--manifest-path", str(repo / "agent-session" / "Cargo.toml"), "--", "--check"],
        ["cargo", "fmt", "--manifest-path", str(repo / "agentvis" / "Cargo.toml"), "--", "--check"],
        [
            sys.executable,
            "-m",
            "py_compile",
            str(repo / "agentvis" / "research" / "rq7_measurement.py"),
            str(repo / "agentvis" / "research" / "rq7_source_oracle_check.py"),
        ],
        ["git", "diff", "--check"],
    ]
    test_records = []
    for command in test_commands:
        completed = subprocess.run(
            command,
            cwd=repo,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        combined = (completed.stdout + "\n" + completed.stderr).encode()
        test_records.append({
            "command": shlex.join(command),
            "returncode": completed.returncode,
            "output_sha256": sha256_bytes(combined),
        })
        if completed.returncode:
            raise RuntimeError(
                f"code-seal validation failed: {shlex.join(command)}\n"
                f"{completed.stderr[-4000:]}"
            )
    build_command = [
        "cargo",
        "build",
        "--release",
        "--locked",
        "--manifest-path",
        str(repo / "agentvis" / "Cargo.toml"),
    ]
    build_output = run(build_command, cwd=repo)
    binary = repo / "agentvis" / "target" / "release" / "agentvis"
    sealed_files = [
        repo / "agent-session" / "src" / "parser.rs",
        repo / "agent-session" / "tests" / "fixtures" / "strict-action-grammar.json",
        repo / "agent-session" / "tests" / "fixtures" / "native-root-identity.json",
        repo / "agentvis" / "src" / "repository.rs",
        repo / "agentvis" / "src" / "rq1.rs",
        repo / "agentvis" / "research" / "rq7_measurement.py",
        repo / "agentvis" / "research" / "rq7_source_oracle_check.py",
        repo / "agentvis" / "tests" / "fixtures" / "strict-lifecycle.json",
        repo / "agentvis" / "Cargo.lock",
    ]
    write_json(output, {
        "spec_version": SPEC_VERSION,
        "freeze_sha256": sha256_file(private / "freeze.json"),
        "question_spec_sha256": freeze_data["question_spec_sha256"],
        "git_revision": revision,
        "git_tree": tree,
        "build_command": shlex.join(build_command),
        "build_output_sha256": sha256_bytes(build_output.encode()),
        "binary": str(binary),
        "binary_sha256": sha256_file(binary),
        "files": {
            str(path.relative_to(repo)): sha256_file(path)
            for path in sealed_files
        },
        "tests": test_records,
        "created_at": dt.datetime.now(dt.timezone.utc).isoformat(),
    })
    print(f"[rq7] repaired code seal complete: {output}")
    return 0


def validate_repaired_code(
    private: Path,
    seal_path: Path,
    review_path: Path,
) -> dict[str, str]:
    seal_path = seal_path.resolve()
    review_path = review_path.resolve()
    seal = read_json(seal_path)
    review = read_json(review_path)
    repo = Path(__file__).resolve().parents[2]
    if seal.get("spec_version") != SPEC_VERSION:
        raise RuntimeError("repaired code seal specification mismatch")
    if seal.get("freeze_sha256") != sha256_file(private / "freeze.json"):
        raise RuntimeError("repaired code seal corpus mismatch")
    if seal.get("git_revision") != run(["git", "rev-parse", "HEAD"], cwd=repo).strip():
        raise RuntimeError("repaired code revision changed after sealing")
    if seal.get("git_tree") != run(["git", "rev-parse", "HEAD^{tree}"], cwd=repo).strip():
        raise RuntimeError("repaired code tree changed after sealing")
    if run(["git", "status", "--porcelain", "--untracked-files=no"], cwd=repo).strip():
        raise RuntimeError("repaired repository became dirty after sealing")
    for relative, expected in seal.get("files", {}).items():
        path = repo / relative
        if not path.is_file() or sha256_file(path) != expected:
            raise RuntimeError(f"repaired sealed file changed: {relative}")
    binary = Path(str(seal.get("binary") or ""))
    if not binary.is_file() or sha256_file(binary) != seal.get("binary_sha256"):
        raise RuntimeError("repaired binary changed after sealing")
    if not seal.get("tests") or any(row.get("returncode") != 0 for row in seal["tests"]):
        raise RuntimeError("repaired code seal lacks passing test records")
    seal_hash = sha256_file(seal_path)
    if review.get("status") != "pass" or review.get("code_seal_sha256") != seal_hash:
        raise RuntimeError("independent code review does not approve this exact seal")
    return {
        "code_seal_sha256": seal_hash,
        "code_review_sha256": sha256_file(review_path),
    }


def validate_baseline(
    private: Path,
    baseline_path: Path,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    baseline_path = baseline_path.resolve()
    freeze_data = read_json(private / "freeze.json")
    seal = read_json(baseline_path.with_name("baseline-seal.json"))
    if seal.get("revision") != V0_REVISION:
        raise RuntimeError("baseline revision seal does not identify current-v0")
    if seal.get("cargo_lock_sha256") != V0_CARGO_LOCK_SHA256:
        raise RuntimeError("baseline Cargo.lock seal violates preregistration")
    if seal.get("binary_sha256") != V0_BINARY_SHA256:
        raise RuntimeError("baseline binary seal violates preregistration")
    if seal.get("freeze_sha256") != sha256_file(private / "freeze.json"):
        raise RuntimeError("baseline corpus seal does not match this freeze")
    if seal.get("question_spec_sha256") != freeze_data["question_spec_sha256"]:
        raise RuntimeError("baseline question specification does not match this freeze")
    if seal.get("candidate_sha256") != sha256_file(baseline_path):
        raise RuntimeError("baseline candidate hash does not match its seal")
    worktree = Path(str(seal["worktree"]))
    binary = worktree / "agentvis" / "target" / "release" / "agentvis"
    if not binary.is_file() or sha256_file(binary) != V0_BINARY_SHA256:
        raise RuntimeError("preregistered current-v0 binary is unavailable")
    lock = worktree / "agentvis" / "Cargo.lock"
    if not lock.is_file() or sha256_file(lock) != V0_CARGO_LOCK_SHA256:
        raise RuntimeError("preregistered current-v0 Cargo.lock is unavailable")
    candidates = read_json(baseline_path)
    ids = [str(row["id"]) for row in candidates]
    expected_ids = {str(row["id"]) for row in freeze_data["questions"]}
    if len(ids) != len(expected_ids) or set(ids) != expected_ids:
        raise RuntimeError("baseline candidate IDs do not match the frozen questions")
    ids_hash = sha256_bytes("\n".join(sorted(ids)).encode())
    if seal.get("candidate_ids_sha256") != ids_hash:
        raise RuntimeError("baseline candidate ID seal mismatch")
    if any(
        row.get("question_spec_sha256") != freeze_data["question_spec_sha256"]
        for row in candidates
    ):
        raise RuntimeError("baseline candidate question specification mismatch")
    return seal, candidates


def run_current_baseline(args: argparse.Namespace) -> int:
    if args.output.exists():
        raise RuntimeError("baseline output is append-only")
    worktree = args.worktree.resolve()
    revision = run(["git", "rev-parse", "HEAD"], cwd=worktree).strip()
    if revision != V0_REVISION:
        raise RuntimeError(f"current-v0 revision mismatch: {revision}")
    if run(
        ["git", "status", "--porcelain", "--untracked-files=no"],
        cwd=worktree,
    ).strip():
        raise RuntimeError("current-v0 worktree has tracked modifications")
    binary = worktree / "agentvis" / "target" / "release" / "agentvis"
    if not binary.is_file():
        raise RuntimeError(f"current-v0 binary missing: {binary}")
    if sha256_file(worktree / "agentvis" / "Cargo.lock") != V0_CARGO_LOCK_SHA256:
        raise RuntimeError("current-v0 Cargo.lock does not match preregistration")
    if sha256_file(binary) != V0_BINARY_SHA256:
        raise RuntimeError("current-v0 binary does not match preregistration")
    freeze_data = read_json(args.private / "freeze.json")
    projection, build_seconds = build_agent_session_projection(
        args.private,
        args.output / "projection",
        binary_override=binary,
    )
    frozen_home = args.private / "frozen-home"
    results = []
    for project in freeze_data["projects"]:
        pedges, p0_identity, join_error = proposed_edges(
            project, projection[project["project"]], frozen_home
        )
        relation = (
            relation_values(pedges, len(project["sessions"]), p0_identity)
            if p0_identity and not join_error
            else None
        )
        final_by_template = {
            f"D{index}": row["status"]
            for index, row in enumerate(project["workspace"]["paths"], start=1)
        }
        projected_paths = {
            row["display_path"] for row in pedges
        } | {row["path"] for row in pedges}
        for question in project["questions"]:
            template = question["template"]
            family = question["family"]
            if family in {"B", "C"} and relation:
                value = answer("answer", relation[template])
            elif family == "D":
                path = project["workspace"]["paths"][int(template[1:]) - 1]["path"]
                value = (
                    answer("answer", final_by_template[template])
                    if path in projected_paths
                    else answer("abstain")
                )
            else:
                value = answer("abstain")
            results.append({
                "id": question["id"],
                "project": project["project"],
                "family": family,
                "template": template,
                "method": "current_v0",
                "repetition": 0,
                "status": value["status"],
                "answer": value["answer"],
                "question_spec_sha256": freeze_data["question_spec_sha256"],
            })
    write_json(args.output / "baseline-candidates.json", results)
    write_json(args.output / "baseline-cost.json", {
        "method": "current_v0",
        "build_seconds": f"{build_seconds:.6f}",
        "rows": len(results),
        "binary_sha256": sha256_file(binary),
    })
    candidate_path = args.output / "baseline-candidates.json"
    write_json(args.output / "baseline-seal.json", {
        "revision": revision,
        "worktree": str(worktree),
        "build_command": (
            "cargo build --release --locked --manifest-path agentvis/Cargo.toml"
        ),
        "cargo_lock_sha256": sha256_file(worktree / "agentvis" / "Cargo.lock"),
        "binary_sha256": sha256_file(binary),
        "freeze_sha256": sha256_file(args.private / "freeze.json"),
        "question_spec_sha256": freeze_data["question_spec_sha256"],
        "candidate_sha256": sha256_file(candidate_path),
        "candidate_ids_sha256": sha256_bytes(
            "\n".join(sorted(str(row["id"]) for row in results)).encode()
        ),
        "rows": len(results),
    })
    print(f"[rq7] current-v0 baseline complete: {len(results)} rows")
    return 0


def bc_gate(rows: list[dict[str, Any]], expected: int) -> dict[str, int]:
    selected = [
        row
        for row in rows
        if row["method"] == "trajectory" and row["family"] in {"B", "C"}
    ]
    result = {
        "expected": expected,
        "answers": sum(row["status"] == "answer" for row in selected),
        "correct": sum(row["correct"] for row in selected),
        "wrong": sum(row["wrong"] for row in selected),
        "abstain": sum(row["status"] != "answer" for row in selected),
    }
    result["pass"] = int(
        len(selected) == expected
        and result["answers"] == expected
        and result["correct"] == expected
        and result["wrong"] == 0
        and result["abstain"] == 0
    )
    return result


def score_blind_candidates(
    candidates: list[dict[str, Any]],
    questions: list[dict[str, Any]],
    spec_hash: str,
) -> list[dict[str, Any]]:
    if any(
        any(key in row for key in ("expected", "correct", "wrong"))
        for row in candidates
    ):
        raise RuntimeError("baseline candidates contain gold-derived fields")
    question_by_id = {str(row["id"]): row for row in questions}
    candidate_ids = [str(row["id"]) for row in candidates]
    if len(candidate_ids) != len(question_by_id) or set(candidate_ids) != set(question_by_id):
        raise RuntimeError("baseline candidate IDs do not match the frozen questions")
    scored = []
    for row in candidates:
        question = question_by_id[str(row["id"])]
        if row.get("question_spec_sha256") != spec_hash:
            raise RuntimeError(f"baseline question-spec mismatch: {row['id']}")
        expected = str(question["answer"])
        status = str(row["status"])
        value = str(row["answer"])
        scored.append({
            **row,
            "expected": expected,
            "correct": int(status == "answer" and value == expected),
            "wrong": int(status == "answer" and value != expected),
        })
    return scored


def preflight(args: argparse.Namespace) -> int:
    private = args.private.resolve()
    release = args.release.resolve()
    private_run = private / "preflight"
    if private_run.exists() or release.exists():
        raise RuntimeError("preflight outputs are append-only")
    validate_baseline(private, args.baseline)
    validate_repaired_code(private, args.code_seal, args.code_review)
    freeze_data = read_json(private / "freeze.json")
    checker = read_json(private / "oracle-check.json")
    if checker.get("status") != "pass":
        raise RuntimeError("independent oracle checker did not pass")
    project = min(
        freeze_data["projects"],
        key=lambda row: (
            sum(source["bytes"] for source in row["sources"]),
            row["project"],
        ),
    )
    output = release / "deterministic"
    deterministic, costs = deterministic_methods(
        private,
        output,
        {project["project"]},
        private_run / "projection",
    )
    conformance = read_json(output / "projection-conformance.json")
    gate = bc_gate(deterministic, 10)
    status = "pass" if exact_conformance(conformance) and gate["pass"] else "fail"
    write_json(release / "preflight-result.json", {
        "status": status,
        "project": project["project"],
        "vendors": sorted({source["vendor"] for source in project["sources"]}),
        "strict_edge_conformance": exact_conformance(conformance),
        "bc_gate": gate,
        "deterministic_cost_rows": len(costs),
    })
    if status != "pass":
        raise RuntimeError(f"held-out preflight failed for {project['project']}")
    print(f"[rq7] preflight pass: {project['project']}, exact edges/status/effects, B+C 10/10")
    return 0


def full(args: argparse.Namespace) -> int:
    private = args.private.resolve()
    release = args.release.resolve()
    full_private = private / "full"
    if full_private.exists() or release.exists():
        raise RuntimeError("full-run outputs are append-only")
    baseline_seal, baseline_candidates = validate_baseline(private, args.baseline)
    repaired_hashes = validate_repaired_code(
        private,
        args.code_seal,
        args.code_review,
    )
    freeze_data = read_json(private / "freeze.json")
    preflight_attempt = read_json(private.parent / "preflight-attempt.json")
    preflight_result_path = Path(str(preflight_attempt.get("result_path") or ""))
    if (
        preflight_attempt.get("terminal_status") != "complete"
        or preflight_attempt.get("decision") != "pass"
        or preflight_attempt.get("freeze_sha256") != sha256_file(private / "freeze.json")
        or preflight_attempt.get("baseline_seal_sha256")
        != sha256_file(args.baseline.resolve().with_name("baseline-seal.json"))
        or preflight_attempt.get("code_seal_sha256")
        != repaired_hashes["code_seal_sha256"]
        or preflight_attempt.get("code_review_sha256")
        != repaired_hashes["code_review_sha256"]
        or not preflight_result_path.is_file()
        or preflight_attempt.get("result_sha256") != sha256_file(preflight_result_path)
        or read_json(preflight_result_path).get("status") != "pass"
    ):
        raise RuntimeError("full run requires the unique matching passed preflight")
    deterministic, deterministic_costs = deterministic_methods(
        private,
        full_private / "deterministic",
        projection_output=full_private / "projection",
    )
    conformance = read_json(
        full_private / "deterministic" / "projection-conformance.json"
    )
    gate = bc_gate(deterministic, 60)
    baseline_rows = score_blind_candidates(
        baseline_candidates,
        freeze_data["questions"],
        freeze_data["question_spec_sha256"],
    )
    baseline_gate = bc_gate(
        [
            {**row, "method": "trajectory"}
            for row in baseline_rows
            if row.get("method") == "current_v0"
        ],
        60,
    )
    improves_over_v0 = (
        gate["correct"] > baseline_gate["correct"]
        and gate["wrong"] <= baseline_gate["wrong"]
        and gate["abstain"] <= baseline_gate["abstain"]
    )
    summary = {
        "status": "pass"
        if exact_conformance(conformance) and gate["pass"] and improves_over_v0
        else "fail",
        "projects": len(freeze_data["projects"]),
        "sources": sum(len(project["sources"]) for project in freeze_data["projects"]),
        "strict_edge_conformance": exact_conformance(conformance),
        "bc_gate": gate,
        "current_v0_bc": baseline_gate,
        "improves_over_current_v0": improves_over_v0,
        "conformance": conformance,
    }
    write_json(release / "heldout-summary.json", summary)
    write_json(full_private / "method-results.json", deterministic)
    write_json(full_private / "costs.json", deterministic_costs)
    audit_manifest(private)
    if summary["status"] != "pass":
        raise RuntimeError("full held-out conformance gate failed")
    print(
        f"[rq7] full pass: {summary['sources']} roots, "
        "exact edges/status/effects, B+C 60/60"
    )
    return 0


def percentile(values: list[float], p: float) -> float:
    if not values:
        return float("nan")
    ordered = sorted(values)
    position = (len(ordered) - 1) * p
    low = int(position)
    high = min(low + 1, len(ordered) - 1)
    fraction = position - low
    return ordered[low] * (1 - fraction) + ordered[high] * fraction


def project_score(rows: list[dict[str, Any]], method: str, project: str, families: set[str], repetition: int | None = None) -> float:
    selected = [
        row for row in rows
        if row["method"] == method
        and row["project"] == project
        and row["family"] in families
        and (repetition is None or row["repetition"] == repetition)
    ]
    return sum(int(row["correct"]) for row in selected) / len(selected) if selected else 0.0


def bootstrap_effects(rows: list[dict[str, Any]], projects: list[str], repetitions: int) -> dict[str, Any]:
    rng = random.Random(int(SEED))
    t_pg_project = {
        project: project_score(rows, "trajectory", project, {"B", "C"})
        - project_score(rows, "procgrep", project, {"B", "C"})
        for project in projects
    }
    raw_project_reps = {
        project: [project_score(rows, "raw_model", project, {"B", "C"}, repetition) for repetition in range(1, repetitions + 1)]
        for project in projects
    }
    t_project = {project: project_score(rows, "trajectory", project, {"B", "C"}) for project in projects}
    pg_draws: list[float] = []
    raw_draws: list[float] = []
    for _ in range(10_000):
        sampled = [rng.choice(projects) for _ in projects]
        pg_draws.append(statistics.mean(t_pg_project[project] for project in sampled))
        effects = []
        for project in sampled:
            rep_values = raw_project_reps[project]
            raw_mean = statistics.mean(rng.choice(rep_values) for _ in rep_values)
            effects.append(t_project[project] - raw_mean)
        raw_draws.append(statistics.mean(effects))
    t_pg = statistics.mean(t_pg_project.values())
    t_raw = statistics.mean(
        t_project[project] - statistics.mean(raw_project_reps[project]) for project in projects
    )
    return {
        "trajectory_minus_procgrep_bc": {
            "estimate": t_pg,
            "ci_low": percentile(pg_draws, 0.025),
            "ci_high": percentile(pg_draws, 0.975),
            "projects": t_pg_project,
        },
        "trajectory_minus_raw_bc": {
            "estimate": t_raw,
            "ci_low": percentile(raw_draws, 0.025),
            "ci_high": percentile(raw_draws, 0.975),
            "projects": {
                project: t_project[project] - statistics.mean(raw_project_reps[project])
                for project in projects
            },
        },
    }


def cost_effects(costs: list[dict[str, Any]], projects: list[str]) -> dict[str, Any]:
    raw = defaultdict(list)
    trajectory = {}
    for row in costs:
        if row["method"] == "raw_model":
            raw[row["project"]].append(float(row["wall_seconds"]))
        elif row["method"] == "trajectory":
            trajectory[row["project"]] = float(row["wall_seconds"])
    ratios = {
        project: statistics.mean(raw[project]) / max(trajectory[project], 1e-9)
        for project in projects
    }
    rng = random.Random(int(SEED) + 1)
    draws = []
    for _ in range(10_000):
        sampled = [rng.choice(projects) for _ in projects]
        draws.append(statistics.mean(__import__("math").log(ratios[project]) for project in sampled))
    return {
        "raw_over_trajectory_wall_ratio": ratios,
        "mean_log_ratio": statistics.mean(__import__("math").log(value) for value in ratios.values()),
        "ci_low": percentile(draws, 0.025),
        "ci_high": percentile(draws, 0.975),
    }


def score(args: argparse.Namespace) -> int:
    full_private = args.private / "full"
    rows = read_json(full_private / "method-results.json")
    costs = read_json(full_private / "costs.json")
    freeze_data = read_json(args.private / "freeze.json")
    projects = [project["project"] for project in freeze_data["projects"]]
    repetitions = max(int(row["repetition"]) for row in rows if row["method"] == "raw_model")
    expected = 480 + 120 * repetitions
    if len(rows) != expected:
        raise RuntimeError(f"score expected {expected} method rows, got {len(rows)}")
    aggregate = []
    for method in ("final_state", "counts", "procgrep", "raw_model", "trajectory"):
        for family in "ABCD":
            selected = [row for row in rows if row["method"] == method and row["family"] == family]
            denominator = 30 * (repetitions if method == "raw_model" else 1)
            aggregate.append({
                "method": method,
                "family": family,
                "n": denominator,
                "correct": sum(int(row["correct"]) for row in selected),
                "wrong": sum(int(row["wrong"]) for row in selected),
                "abstain": sum(row["status"] == "abstain" for row in selected),
                "correct_coverage": sum(int(row["correct"]) for row in selected) / denominator,
                "conditional_accuracy": (
                    sum(int(row["correct"]) for row in selected)
                    / max(sum(row["status"] == "answer" for row in selected), 1)
                ),
            })
    effects = bootstrap_effects(rows, projects, repetitions)
    cost_stats = cost_effects(costs, projects)
    trajectory_bc = [row for row in rows if row["method"] == "trajectory" and row["family"] in {"B", "C"}]
    trajectory_correct = sum(int(row["correct"]) for row in trajectory_bc)
    trajectory_wrong = sum(int(row["wrong"]) for row in trajectory_bc)
    trajectory_answered = sum(row["status"] == "answer" for row in trajectory_bc)
    project_conditional = {}
    for project in projects:
        selected = [row for row in trajectory_bc if row["project"] == project]
        project_conditional[project] = sum(int(row["correct"]) for row in selected) / max(sum(row["status"] == "answer" for row in selected), 1)
    action_rows = [row for row in rows if row["method"] in {"procgrep", "trajectory"} and row["family"] == "A"]
    action_by_id = {
        qid: {row["method"]: row for row in action_rows if row["id"] == qid}
        for qid in {row["id"] for row in action_rows}
    }
    action_veto = len(action_by_id) == 30 and all(
        set(pair) == {"procgrep", "trajectory"}
        and pair["procgrep"]["correct"]
        and pair["trajectory"]["correct"]
        and pair["procgrep"]["answer"] == pair["trajectory"]["answer"]
        for pair in action_by_id.values()
    )
    correctness_veto = (
        trajectory_correct / 60 >= 0.80
        and trajectory_correct / max(trajectory_answered, 1) >= 0.95
        and trajectory_wrong / 60 <= 0.05
        and min(project_conditional.values()) >= 0.80
    )
    pg_positive = effects["trajectory_minus_procgrep_bc"]["ci_low"] > 0 and action_veto and correctness_veto
    raw_ci = effects["trajectory_minus_raw_bc"]
    raw_parity = raw_ci["ci_low"] >= -0.05 and raw_ci["ci_high"] <= 0.05
    efficiency = raw_parity and cost_stats["ci_low"] > 0
    decisions = {
        "procgrep_incremental_coverage": "positive" if pg_positive else "mixed_or_negative",
        "action_preservation_veto_pass": action_veto,
        "trajectory_correctness_veto_pass": correctness_veto,
        "trajectory_vs_raw": (
            "accuracy_superior" if raw_ci["ci_low"] > 0 else
            "raw_wins" if raw_ci["ci_high"] < -0.05 else
            "parity" if raw_parity else "mixed_or_inconclusive"
        ),
        "parity_conditioned_efficiency": "positive" if efficiency else "not_established",
    }
    args.release.mkdir(parents=True, exist_ok=True)
    write_json(args.release / "aggregate.json", aggregate)
    write_json(args.release / "effects.json", effects)
    write_json(args.release / "cost-effects.json", cost_stats)
    write_json(args.release / "decisions.json", decisions)
    result_fields = [
        "id", "project", "family", "template", "method", "repetition", "status", "answer",
        "expected", "correct", "wrong", "question_spec_sha256",
    ]
    write_csv(args.release / "method-results.csv", result_fields, rows)
    cost_fields = [
        "project", "method", "repetition", "source_bytes", "input_bytes", "output_bytes",
        "tool_result_bytes",
        "input_tokens", "cached_input_tokens", "output_tokens", "reasoning_tokens", "model_calls",
        "tool_calls", "build_seconds", "query_seconds", "wall_seconds", "peak_rss_kib", "terminal_status",
    ]
    write_csv(args.release / "costs.csv", cost_fields, costs)
    plot_results(aggregate, costs, args.figure)
    write_result_markdown(args.release.parent / "result.md", aggregate, effects, cost_stats, decisions)
    print(f"[rq7] score complete: {decisions}")
    return 0


def score_deterministic(args: argparse.Namespace) -> int:
    rows = read_json(args.deterministic / "deterministic-results.json")
    costs = read_json(args.deterministic / "deterministic-costs.json")
    freeze_data = read_json(args.private / "freeze.json")
    projects = [project["project"] for project in freeze_data["projects"]]
    methods = ("final_state", "counts", "procgrep", "trajectory")
    if len(rows) != 480:
        raise RuntimeError(f"deterministic score expected 480 rows, got {len(rows)}")
    aggregate = []
    for method in methods:
        for family in "ABCD":
            selected = [row for row in rows if row["method"] == method and row["family"] == family]
            aggregate.append({
                "method": method,
                "family": family,
                "n": 30,
                "correct": sum(int(row["correct"]) for row in selected),
                "wrong": sum(int(row["wrong"]) for row in selected),
                "abstain": sum(row["status"] == "abstain" for row in selected),
                "correct_coverage": sum(int(row["correct"]) for row in selected) / 30,
                "conditional_accuracy": (
                    sum(int(row["correct"]) for row in selected)
                    / max(sum(row["status"] == "answer" for row in selected), 1)
                ),
            })
    per_project = {
        project: (
            project_score(rows, "trajectory", project, {"B", "C"})
            - project_score(rows, "procgrep", project, {"B", "C"})
        )
        for project in projects
    }
    rng = random.Random(int(SEED))
    draws = [
        statistics.mean(per_project[rng.choice(projects)] for _ in projects)
        for _ in range(10_000)
    ]
    effect = {
        "estimate": statistics.mean(per_project.values()),
        "ci_low": percentile(draws, 0.025),
        "ci_high": percentile(draws, 0.975),
        "project_effects": per_project,
    }
    action_rows = [row for row in rows if row["method"] in {"procgrep", "trajectory"} and row["family"] == "A"]
    by_id = {
        qid: {row["method"]: row for row in action_rows if row["id"] == qid}
        for qid in {row["id"] for row in action_rows}
    }
    action_identity = len(by_id) == 30 and all(
        set(pair) == {"procgrep", "trajectory"}
        and pair["procgrep"]["answer"] == pair["trajectory"]["answer"]
        and pair["procgrep"]["status"] == pair["trajectory"]["status"]
        for pair in by_id.values()
    )
    action_correctness = len(by_id) == 30 and all(
        pair["procgrep"]["correct"] and pair["trajectory"]["correct"]
        for pair in by_id.values()
    )
    trajectory_bc = [
        row for row in rows if row["method"] == "trajectory" and row["family"] in {"B", "C"}
    ]
    correct = sum(int(row["correct"]) for row in trajectory_bc)
    wrong = sum(int(row["wrong"]) for row in trajectory_bc)
    answered = sum(row["status"] == "answer" for row in trajectory_bc)
    project_accuracy = {
        project: (
            sum(int(row["correct"]) for row in trajectory_bc if row["project"] == project)
            / max(sum(row["status"] == "answer" for row in trajectory_bc if row["project"] == project), 1)
        )
        for project in projects
    }
    correctness_veto = (
        correct / 60 >= 0.80
        and correct / max(answered, 1) >= 0.95
        and wrong / 60 <= 0.05
        and min(project_accuracy.values()) >= 0.80
    )
    decisions = {
        "procgrep_incremental_coverage": (
            "positive"
            if effect["ci_low"] > 0 and action_identity and action_correctness and correctness_veto
            else "rejected_by_correctness_veto"
        ),
        "action_spine_identity_pass": action_identity,
        "action_source_correctness_veto_pass": action_correctness,
        "trajectory_correctness_veto_pass": correctness_veto,
        "raw_model_comparison": "unavailable_after_preflight",
    }
    args.release.mkdir(parents=True, exist_ok=True)
    write_json(args.release / "aggregate.json", aggregate)
    write_json(args.release / "effects.json", {"trajectory_minus_procgrep_bc": effect})
    write_json(args.release / "decisions.json", decisions)
    write_csv(
        args.release / "method-results.csv",
        [
            "id", "project", "family", "template", "method", "repetition", "status",
            "answer", "expected", "correct", "wrong", "question_spec_sha256",
        ],
        rows,
    )
    write_csv(
        args.release / "costs.csv",
        [
            "project", "method", "repetition", "source_bytes", "input_bytes",
            "output_bytes", "input_tokens", "cached_input_tokens", "output_tokens",
            "reasoning_tokens", "model_calls", "tool_calls", "build_seconds",
            "query_seconds", "wall_seconds", "peak_rss_kib", "terminal_status",
        ],
        costs,
    )
    plot_deterministic_results(aggregate, args.figure)
    write_deterministic_result(
        args.release.parent / "result.md",
        aggregate,
        effect,
        decisions,
        correct,
        wrong,
        answered,
        project_accuracy,
    )
    print(f"[rq7] deterministic score complete: {decisions}")
    return 0


def plot_deterministic_results(aggregate: list[dict[str, Any]], figure: Path) -> None:
    import matplotlib.pyplot as plt
    import numpy as np

    methods = ["final_state", "counts", "procgrep", "trajectory"]
    labels = {
        "final_state": "Final state",
        "counts": "Counts",
        "procgrep": "ProcGrep",
        "trajectory": "Trajectory",
    }
    families = list("ABCD")
    colors = {"correct": "#2a9d8f", "wrong": "#e76f51", "abstain": "#d9dee7"}
    fig, ax = plt.subplots(figsize=(7.2, 3.5))
    width = 0.19
    x = np.arange(len(families))
    for method_index, method in enumerate(methods):
        rows_by_family = {row["family"]: row for row in aggregate if row["method"] == method}
        positions = x + (method_index - 1.5) * width
        correct = [rows_by_family[family]["correct"] / 30 for family in families]
        wrong = [rows_by_family[family]["wrong"] / 30 for family in families]
        abstain = [rows_by_family[family]["abstain"] / 30 for family in families]
        ax.bar(positions, correct, width, color=colors["correct"], edgecolor="white", linewidth=0.3)
        ax.bar(positions, wrong, width, bottom=correct, color=colors["wrong"], edgecolor="white", linewidth=0.3)
        ax.bar(
            positions,
            abstain,
            width,
            bottom=np.array(correct) + np.array(wrong),
            color=colors["abstain"],
            edgecolor="white",
            linewidth=0.3,
        )
        for position in positions:
            ax.text(position, 1.015, str(method_index + 1), ha="center", va="bottom", fontsize=7, color="#343a40")
    ax.set_xticks(x, ["Action", "Artifact", "Cross-session", "Final state"])
    ax.set_ylim(0, 1.07)
    ax.set_ylabel("Fraction of common questions")
    ax.set_title("Source-verifiable fact outcomes", loc="left", fontweight="bold")
    ax.grid(axis="y", color="#e8ebf0", linewidth=0.6)
    handles = [plt.Rectangle((0, 0), 1, 1, color=colors[key]) for key in ("correct", "wrong", "abstain")]
    ax.legend(handles, ["Correct", "Wrong", "Abstain"], ncol=3, frameon=False, loc="upper center")
    ax.text(
        0.01,
        -0.22,
        "Bar order: 1 Final state · 2 Counts · 3 ProcGrep · 4 Trajectory; Raw model N/A after preflight",
        transform=ax.transAxes,
        fontsize=7,
    )
    fig.tight_layout()
    figure.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(figure, bbox_inches="tight")
    fig.savefig(figure.with_suffix(".png"), dpi=220, bbox_inches="tight")
    plt.close(fig)


def write_deterministic_result(
    path: Path,
    aggregate: list[dict[str, Any]],
    effect: dict[str, Any],
    decisions: dict[str, Any],
    trajectory_correct: int,
    trajectory_wrong: int,
    trajectory_answered: int,
    project_accuracy: dict[str, float],
) -> None:
    lines = [
        "# Separate Tool Question — Measurement Capability",
        "",
        "All deterministic rows use the same 120-question source-direct oracle. "
        "The bounded Raw reader is N/A: the final registered Terra preflight "
        "engaged local evidence retrieval but was stopped by the frozen boundary "
        "contract before a scoreable answer. Its rows are not scored as wrong or abstain.",
        "",
        "| Method | Family | Correct | Wrong | Abstain | Correct coverage | Conditional accuracy |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for row in aggregate:
        lines.append(
            f"| {row['method']} | {row['family']} | {row['correct']} | {row['wrong']} | "
            f"{row['abstain']} | {row['correct_coverage']:.3f} | {row['conditional_accuracy']:.3f} |"
        )
    lines.extend([
        "",
        "## Predeclared contrasts and vetoes",
        "",
        f"- Trajectory − ProcGrep B+C correct coverage: {effect['estimate']:.3f}, "
        f"frozen-corpus project-block interval [{effect['ci_low']:.3f}, {effect['ci_high']:.3f}].",
        f"- Trajectory B+C: {trajectory_correct}/60 correct, {trajectory_wrong}/60 wrong, "
        f"{trajectory_answered}/60 answered.",
        "- Per-project Trajectory B+C conditional accuracy: "
        + ", ".join(f"{project}={value:.3f}" for project, value in project_accuracy.items())
        + ".",
        "",
        "## Decision",
        "",
    ])
    for key, value in decisions.items():
        lines.append(f"- **{key}:** {value}")
    lines.extend([
        "",
        "The positive raw coverage difference over ProcGrep does not support a "
        "capability claim. The trajectory preserved ProcGrep's action answers "
        "exactly, but both failed the action source-correctness veto, and the "
        "trajectory failed the B+C correctness veto. This is a negative "
        "implementation result, not evidence "
        "against the workspace-centered representation in principle. No LLM-reader "
        "accuracy or superiority claim is made.",
    ])
    path.write_text("\n".join(lines) + "\n")


def plot_results(aggregate: list[dict[str, Any]], costs: list[dict[str, Any]], figure: Path) -> None:
    import matplotlib.pyplot as plt
    import numpy as np

    methods = ["final_state", "counts", "procgrep", "raw_model", "trajectory"]
    families = list("ABCD")
    labels = {
        "final_state": "Final state",
        "counts": "Counts",
        "procgrep": "ProcGrep",
        "raw_model": "Raw model",
        "trajectory": "Trajectory",
    }
    fig, axes = plt.subplots(1, 2, figsize=(9.2, 3.25), gridspec_kw={"width_ratios": [2.3, 1]})
    ax = axes[0]
    width = 0.16
    x = np.arange(len(families))
    colors = {"correct": "#2a9d8f", "wrong": "#e76f51", "abstain": "#d9dee7"}
    for method_index, method in enumerate(methods):
        rows = {row["family"]: row for row in aggregate if row["method"] == method}
        positions = x + (method_index - 2) * width
        correct = [rows[family]["correct"] / rows[family]["n"] for family in families]
        wrong = [rows[family]["wrong"] / rows[family]["n"] for family in families]
        abstain = [rows[family]["abstain"] / rows[family]["n"] for family in families]
        ax.bar(positions, correct, width, color=colors["correct"], edgecolor="white", linewidth=0.3)
        ax.bar(positions, wrong, width, bottom=correct, color=colors["wrong"], edgecolor="white", linewidth=0.3)
        ax.bar(
            positions,
            abstain,
            width,
            bottom=np.array(correct) + np.array(wrong),
            color=colors["abstain"],
            edgecolor="white",
            linewidth=0.3,
            label=labels[method] if False else None,
        )
        for position, value in zip(positions, correct):
            if value > 0:
                ax.text(position, min(value, 0.98), str(method_index + 1), ha="center", va="top", fontsize=6, color="white")
    ax.set_xticks(x, ["Action", "Artifact", "Cross-session", "Final state"])
    ax.set_ylim(0, 1.02)
    ax.set_ylabel("Fraction of common questions")
    ax.set_title("(a) Exact factual coverage", loc="left", fontweight="bold")
    ax.grid(axis="y", color="#e8ebf0", linewidth=0.6)
    legend_handles = [
        plt.Rectangle((0, 0), 1, 1, color=colors[key]) for key in ("correct", "wrong", "abstain")
    ]
    ax.legend(legend_handles, ["Correct", "Wrong", "Abstain"], ncol=3, frameon=False, loc="upper center")
    ax.text(
        0.01,
        -0.22,
        "Bar order: 1 Final state · 2 Counts · 3 ProcGrep · 4 Raw model · 5 Trajectory",
        transform=ax.transAxes,
        fontsize=7,
    )

    cost_ax = axes[1]
    cost_values = []
    for method in methods:
        selected = [float(row["wall_seconds"]) for row in costs if row["method"] == method]
        cost_values.append(statistics.mean(selected) / 20 if selected else float("nan"))
    cost_ax.barh(range(len(methods)), cost_values, color=["#9aa7b8"] * 4 + ["#457b9d"])
    cost_ax.set_yticks(range(len(methods)), [labels[method] for method in methods])
    cost_ax.set_xscale("log")
    cost_ax.set_xlabel("Wall seconds / question (log)")
    cost_ax.set_title("(b) Measured cost", loc="left", fontweight="bold")
    cost_ax.grid(axis="x", color="#e8ebf0", linewidth=0.6)
    fig.tight_layout()
    figure.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(figure, bbox_inches="tight")
    fig.savefig(figure.with_suffix(".png"), dpi=220, bbox_inches="tight")
    plt.close(fig)


def write_result_markdown(
    path: Path,
    aggregate: list[dict[str, Any]],
    effects: dict[str, Any],
    costs: dict[str, Any],
    decisions: dict[str, Any],
) -> None:
    lines = [
        "# RQ7 Measurement Capability",
        "",
        "All rows use one common 120-question, source-witnessed denominator. Raw-model values average three independent complete project calls; no majority vote is used.",
        "",
        "| Method | Family | Correct | Wrong | Abstain | Correct coverage | Conditional accuracy |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for row in aggregate:
        lines.append(
            f"| {row['method']} | {row['family']} | {row['correct']} | {row['wrong']} | {row['abstain']} | {row['correct_coverage']:.3f} | {row['conditional_accuracy']:.3f} |"
        )
    pg = effects["trajectory_minus_procgrep_bc"]
    raw = effects["trajectory_minus_raw_bc"]
    lines.extend([
        "",
        "## Predeclared contrasts",
        "",
        f"- Trajectory − ProcGrep B+C correct coverage: {pg['estimate']:.3f}, frozen-corpus 95% project-block interval [{pg['ci_low']:.3f}, {pg['ci_high']:.3f}].",
        f"- Trajectory − Raw B+C correct coverage: {raw['estimate']:.3f}, hierarchical interval [{raw['ci_low']:.3f}, {raw['ci_high']:.3f}].",
        f"- Raw / trajectory wall-time mean log ratio: {costs['mean_log_ratio']:.3f}, interval [{costs['ci_low']:.3f}, {costs['ci_high']:.3f}].",
        "",
        "## Decision",
        "",
    ])
    for key, value in decisions.items():
        lines.append(f"- **{key}:** {value}")
    lines.extend([
        "",
        "Intervals quantify sensitivity across these six fixed projects; they are not population estimates. ProcGrep's out-of-scope abstentions establish only a narrow representation boundary, not broad understanding superiority.",
    ])
    path.write_text("\n".join(lines) + "\n")


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description=__doc__)
    sub = root.add_subparsers(dest="command", required=True)
    freeze_parser = sub.add_parser("freeze")
    freeze_parser.add_argument("--projects-file", type=Path, required=True)
    freeze_parser.add_argument("--private", type=Path, required=True)
    freeze_parser.add_argument("--release", type=Path, required=True)
    freeze_parser.add_argument("--procgrep", type=Path, required=True)
    freeze_parser.add_argument("--exclude-freeze", type=Path, action="append", required=True)
    freeze_parser.set_defaults(
        func=freeze,
        seed=FROZEN_SELECTION_SEED,
        sessions=FROZEN_SESSIONS_PER_PROJECT,
        raw_bytes=FROZEN_SOURCE_BYTES,
        stability_wait=FROZEN_STABILITY_WAIT,
        cutoff_ns=FROZEN_DISCOVERY_CUTOFF_NS,
    )

    recover_parser = sub.add_parser("recover-freeze")
    recover_parser.add_argument("--private", type=Path, required=True)
    recover_parser.add_argument("--release", type=Path, required=True)
    recover_parser.set_defaults(func=recover_freeze)

    rederive_parser = sub.add_parser("rederive-freeze")
    rederive_parser.add_argument("--source-private", type=Path, required=True)
    rederive_parser.add_argument("--private", type=Path, required=True)
    rederive_parser.add_argument("--release", type=Path, required=True)
    rederive_parser.add_argument("--procgrep", type=Path, required=True)
    rederive_parser.add_argument("--refresh-workspace", action="store_true")
    rederive_parser.set_defaults(func=rederive_freeze)

    preflight_parser = sub.add_parser("preflight")
    preflight_parser.add_argument("--private", type=Path, required=True)
    preflight_parser.add_argument("--release", type=Path, required=True)
    preflight_parser.add_argument("--baseline", type=Path, required=True)
    preflight_parser.add_argument("--code-seal", type=Path, required=True)
    preflight_parser.add_argument("--code-review", type=Path, required=True)
    preflight_parser.set_defaults(func=preflight)

    deterministic_parser = sub.add_parser("deterministic")
    deterministic_parser.add_argument("--private", type=Path, required=True)
    deterministic_parser.add_argument("--output", type=Path, required=True)
    deterministic_parser.set_defaults(func=run_deterministic)

    fixture_parser = sub.add_parser("check-action-fixtures")
    fixture_parser.add_argument("--fixtures", type=Path, required=True)
    fixture_parser.set_defaults(func=check_action_fixtures)

    seal_parser = sub.add_parser("seal-code")
    seal_parser.add_argument("--private", type=Path, required=True)
    seal_parser.add_argument("--output", type=Path, required=True)
    seal_parser.set_defaults(func=seal_repaired_code)

    baseline_parser = sub.add_parser("baseline")
    baseline_parser.add_argument("--private", type=Path, required=True)
    baseline_parser.add_argument("--output", type=Path, required=True)
    baseline_parser.add_argument("--worktree", type=Path, required=True)
    baseline_parser.set_defaults(func=run_current_baseline)

    full_parser = sub.add_parser("full")
    full_parser.add_argument("--private", type=Path, required=True)
    full_parser.add_argument("--release", type=Path, required=True)
    full_parser.add_argument("--baseline", type=Path, required=True)
    full_parser.add_argument("--code-seal", type=Path, required=True)
    full_parser.add_argument("--code-review", type=Path, required=True)
    full_parser.set_defaults(func=full)

    score_parser = sub.add_parser("score")
    score_parser.add_argument("--private", type=Path, required=True)
    score_parser.add_argument("--release", type=Path, required=True)
    score_parser.add_argument("--figure", type=Path, required=True)
    score_parser.set_defaults(func=score)

    deterministic_score_parser = sub.add_parser("score-deterministic")
    deterministic_score_parser.add_argument("--private", type=Path, required=True)
    deterministic_score_parser.add_argument("--deterministic", type=Path, required=True)
    deterministic_score_parser.add_argument("--release", type=Path, required=True)
    deterministic_score_parser.add_argument("--figure", type=Path, required=True)
    deterministic_score_parser.set_defaults(func=score_deterministic)
    return root


def main() -> int:
    args = parser().parse_args()
    if hasattr(args, "seed") and not args.seed:
        raise RuntimeError("selection seed must be non-empty")
    if args.command not in {"freeze", "preflight", "full"}:
        return int(args.func(args))
    if args.command in {"preflight", "full"}:
        private = args.private.resolve()
        attempt_path = private.parent / f"{args.command}-attempt.json"
        if attempt_path.exists():
            raise RuntimeError(f"{args.command} attempt already exists: {attempt_path}")
        baseline = args.baseline.resolve()
        baseline_seal = baseline.with_name("baseline-seal.json")
        code_seal = args.code_seal.resolve()
        code_review = args.code_review.resolve()
        result_path = args.release.resolve() / (
            "preflight-result.json"
            if args.command == "preflight"
            else "heldout-summary.json"
        )
        attempt = {
            "command": shlex.join(sys.argv),
            "started_at": dt.datetime.now(dt.timezone.utc).isoformat(),
            "terminal_status": "running",
            "freeze_sha256": sha256_file(private / "freeze.json"),
            "baseline_candidate_sha256": sha256_file(baseline),
            "baseline_seal_sha256": sha256_file(baseline_seal),
            "code_seal_sha256": sha256_file(code_seal),
            "code_review_sha256": sha256_file(code_review),
            "result_path": str(result_path),
        }
        write_json(attempt_path, attempt)
        try:
            result = int(args.func(args))
        except BaseException as error:
            attempt["terminal_status"] = "failed"
            attempt["finished_at"] = dt.datetime.now(dt.timezone.utc).isoformat()
            attempt["error_type"] = type(error).__name__
            if result_path.is_file():
                payload = read_json(result_path)
                attempt["decision"] = payload.get("status")
                attempt["result_sha256"] = sha256_file(result_path)
            write_json(attempt_path, attempt)
            raise
        attempt["terminal_status"] = "complete"
        attempt["finished_at"] = dt.datetime.now(dt.timezone.utc).isoformat()
        if result_path.is_file():
            payload = read_json(result_path)
            attempt["decision"] = payload.get("status")
            attempt["result_sha256"] = sha256_file(result_path)
        write_json(attempt_path, attempt)
        return result
    attempt_path = args.private.resolve().parent / "freeze-attempt.json"
    if attempt_path.exists():
        raise RuntimeError(f"freeze attempt already exists: {attempt_path}")
    attempt_path.parent.mkdir(parents=True, exist_ok=True)
    attempt = {
        "command": shlex.join(sys.argv),
        "started_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "terminal_status": "running",
        "seed": args.seed,
        "sessions_per_project": args.sessions,
        "raw_bytes": args.raw_bytes,
        "stability_wait_seconds": args.stability_wait,
        "discovery_cutoff_ns": args.cutoff_ns,
        "projects_file": str(args.projects_file.resolve()),
        "projects_file_sha256": sha256_file(args.projects_file.resolve()),
        "exclusion_manifests": [
            {
                "path": str(path.resolve()),
                "sha256": sha256_file(path.resolve()),
            }
            for path in args.exclude_freeze
        ],
    }
    write_json(attempt_path, attempt)
    try:
        result = int(args.func(args))
    except BaseException as error:
        attempt["terminal_status"] = "failed"
        attempt["finished_at"] = dt.datetime.now(dt.timezone.utc).isoformat()
        attempt["error_type"] = type(error).__name__
        write_json(attempt_path, attempt)
        raise
    attempt["terminal_status"] = "complete"
    attempt["finished_at"] = dt.datetime.now(dt.timezone.utc).isoformat()
    write_json(attempt_path, attempt)
    return result


if __name__ == "__main__":
    raise SystemExit(main())
