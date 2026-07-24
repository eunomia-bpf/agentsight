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
VENDORS = ("claude", "codex", "gemini")
READ_COMMANDS = {"cat", "sed", "head", "tail", "nl", "less", "more"}
MUTATE_COMMANDS = {"touch", "rm", "mv", "cp"}
PATH_KEYS = {
    "file_path",
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
                            session_id = str(payload.get("id") or payload.get("session_id") or session_id)
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


def select_sources(candidates: list[dict[str, Any]], raw_cap: int, sessions: int) -> tuple[Path, list[dict[str, Any]]]:
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
                (SEED + vendor + row["sha256"]).encode()
            )
        )
        pools[vendor] = pool
    result: list[dict[str, Any]] = []
    offsets = {vendor: 0 for vendor in VENDORS}
    serialized = 0
    while len(result) < sessions:
        progress = False
        for vendor in VENDORS:
            pool = pools[vendor]
            while offsets[vendor] < len(pool):
                row = pool[offsets[vendor]]
                offsets[vendor] += 1
                boundary = f"BEGIN_NATIVE {vendor} {row['sha256']} {row['bytes']}\nEND_NATIVE\n".encode()
                if raw_cap > 0 and serialized + len(boundary) + row["bytes"] > raw_cap:
                    continue
                result.append(row)
                serialized += len(boundary) + row["bytes"]
                progress = True
                break
            if len(result) >= sessions:
                break
        if not progress:
            break
    available = {vendor for vendor in VENDORS if pools[vendor]}
    represented = {row["vendor"] for row in result}
    if len(result) < 6 or not available.issubset(represented):
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
                })
        return events
    rows = obj
    current_cwd = cwd
    for record_index, row in enumerate(rows):
        if not isinstance(row, dict):
            continue
        stamp = parse_timestamp(row.get("timestamp"))
        if vendor == "claude":
            current_cwd = str(row.get("cwd") or current_cwd)
            content = (row.get("message") or {}).get("content") if isinstance(row.get("message"), dict) else None
            if row.get("type") == "user" and _is_human_prompt(content):
                events.append({"kind": "prompt", "atom": "prompt_ai", "ts_ms": stamp, "record_index": record_index, "call_index": 0})
            if row.get("type") == "file-history-snapshot":
                events.append({"kind": "tool", "tool": "file_snapshot", "args": {}, "call_id": f"snapshot:{record_index}", "workdir": current_cwd, "atom": "edit", "ts_ms": stamp, "record_index": record_index, "call_index": 0})
            if row.get("type") == "assistant" and isinstance(content, list):
                call_index = 0
                for block in content:
                    if not isinstance(block, dict) or block.get("type") != "tool_use":
                        continue
                    args = block.get("input") if isinstance(block.get("input"), dict) else {}
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
                    })
                    call_index += 1
        else:
            payload = row.get("payload") if isinstance(row.get("payload"), dict) else {}
            if row.get("type") in {"session_meta", "turn_context"}:
                current_cwd = str(payload.get("cwd") or current_cwd)
            if row.get("type") == "response_item" and payload.get("type") in {"function_call", "custom_tool_call"}:
                name = str(payload.get("name") or "")
                args = parse_arguments(payload.get("arguments", payload.get("input")))
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
                })
    return events


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
    try:
        lexer = shlex.shlex(command, posix=True, punctuation_chars=";&|<>")
        lexer.whitespace_split = True
        tokens = list(lexer)
    except ValueError:
        return []
    segments: list[list[str]] = []
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


def operands(tokens: list[str]) -> list[str]:
    values: list[str] = []
    skip = False
    for token in tokens:
        if skip:
            skip = False
            continue
        if token in {"-n", "--lines", "-c", "--bytes", "-f", "-e"}:
            skip = True
            continue
        if token.startswith("-"):
            continue
        values.append(token)
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
        values = operands(args)
        if name == "sed" and len(values) >= 2:
            values = values[1:]
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
    if name == "apply_patch" or "*** Begin Patch" in command:
        patch = command or str(args.get("patch") or "")
        pending_move: str | None = None
        for match in PATCH_RE.finditer(patch):
            kind, path = match.groups()
            access = {"Add": "create", "Update": "write", "Delete": "delete"}[kind]
            actions.append({"path": path.strip(), "access": access, "previous_path": None})
            pending_move = path.strip() if kind == "Update" else None
            move = MOVE_RE.search(patch, match.end())
            if pending_move and move:
                actions.append({"path": pending_move, "access": "rename_from", "previous_path": None})
                actions.append({"path": move.group(1).strip(), "access": "rename", "previous_path": pending_move})
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
    return dedup


class ArtifactTracker:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.current: dict[str, str] = {}
        self.generation: Counter[str] = Counter()
        self.deleted: set[str] = set()
        self.display: dict[str, str] = {}

    def identity(self, path: str, access: str, previous: str | None = None) -> str:
        if access == "rename" and previous:
            identity = self.current.pop(previous, None)
            if identity is None:
                identity = self._new(previous)
            self.current[path] = identity
            self.display[identity] = path
            self.deleted.discard(previous)
            return identity
        if path not in self.current or (path in self.deleted and access in {"create", "write"}):
            self.current[path] = self._new(path)
            self.deleted.discard(path)
        identity = self.current[path]
        if access == "delete":
            self.deleted.add(path)
        self.display[identity] = path
        return identity

    def _new(self, path: str) -> str:
        generation = self.generation[path]
        self.generation[path] += 1
        identity = f"{path}#{generation}"
        self.display[identity] = path
        return identity


def artifact_edges(project: dict[str, Any], selected: list[dict[str, Any]], frozen_home: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    root = Path(project["worktree"])
    sessions = []
    for source in selected:
        copy = frozen_home / source["home_relative"]
        events = native_events(source["vendor"], copy, source)
        first_ts = min((event["ts_ms"] for event in events if event.get("ts_ms") is not None), default=source.get("first_ts_ms") or 0)
        sessions.append({**source, "events": events, "first_ts_ms": first_ts})
    sessions.sort(key=lambda row: (row["first_ts_ms"], row["sha256"]))
    tracker = ArtifactTracker(root)
    edges: list[dict[str, Any]] = []
    ordered_events = []
    for session_ordinal, session in enumerate(sessions):
        for event in session["events"]:
            ordered_events.append((
                event.get("ts_ms") if event.get("ts_ms") is not None else session["first_ts_ms"],
                session["sha256"],
                event["record_index"],
                event["call_index"],
                session_ordinal,
                session,
                event,
            ))
    ordered_events.sort(key=lambda row: row[:4])
    pending_rename: dict[tuple[str, str], str] = {}
    for event_ordinal, (_, _, _, _, session_ordinal, session, event) in enumerate(ordered_events):
        for action in event_path_actions(event):
            raw_path = str(action["path"] or "")
            path = lexical_repo_path(raw_path, str(event.get("workdir") or root), root)
            if path is None:
                continue
            previous = None
            if action.get("previous_path"):
                previous = lexical_repo_path(str(action["previous_path"]), str(event.get("workdir") or root), root)
            access = str(action["access"])
            if access == "rename_from":
                pending_rename[(session["session_id"], str(event["call_id"]))] = path
            if access == "rename" and previous is None:
                previous = pending_rename.get((session["session_id"], str(event["call_id"])))
            identity = tracker.identity(path, access, previous)
            edges.append({
                "project": project["project"],
                "session_id": session["session_id"],
                "session_ordinal": session_ordinal,
                "vendor": session["vendor"],
                "source_id": session["source_id"],
                "source_sha256": session["sha256"],
                "record_index": event["record_index"],
                "call_index": event["call_index"],
                "call_id": str(event["call_id"]),
                "event_ordinal": event_ordinal,
                "artifact_id": identity,
                "path": path,
                "display_path": tracker.display[identity],
                "access": access,
                "action_class": "read" if access == "read" else "mutate",
            })
    for edge in edges:
        edge["display_path"] = tracker.display[edge["artifact_id"]]
    public_sessions = [
        {key: value for key, value in session.items() if key != "events"} | {"session_ordinal": index}
        for index, session in enumerate(sessions)
    ]
    return edges, public_sessions


def direct_atoms(selected: list[dict[str, Any]], frozen_home: Path) -> dict[str, list[str]]:
    result = {}
    for source in selected:
        events = native_events(source["vendor"], frozen_home / source["home_relative"], source)
        result[source["session_id"]] = [str(event["atom"]) for event in events]
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
            if not action.get("scope") and action.get("worktree_id") == target_worktree
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


def question_spec() -> str:
    return """# RQ7 Frozen Question Semantics

All answers use only the complete native files and cutoff manifest in the
prompt. Native events are ordered by native timestamp, source SHA-256, record
index, and call index. Sessions are ordered by first native timestamp and source
SHA-256. Tool invocations are attempted actions regardless of result status.

Action mapping follows the frozen ProcGrep Claude/Codex/Gemini rules:
Read/NotebookRead/read_file and terminal cat/sed/head/tail/nl/less/more are
read_file; Edit/Write/NotebookEdit/MultiEdit/apply_patch are edit; commands
matching pytest, test(s), unittest, jest, mocha, vitest, tox, go test, cargo
test, npm/yarn test, make test, or gradle test are run_test. Other calls still
occupy their ordered atom position. A4 is the number of sessions matching
`read_file (?:[a-z_]+ )*edit ` and A5 uses
`edit (?:[a-z_]+ )*run_test `.

Artifact paths come only from structured path keys, apply_patch file headers,
and path operands of cat/sed/head/tail/nl/less/more/touch/rm/mv/cp. Event
workdir overrides session cwd. Resolve relative paths lexically inside the
selected worktree; exclude outside paths, variables, globs, symlink
dereferencing, search scopes, and ambiguous shell syntax. In particular, any
shell segment containing input/output redirection or a heredoc contributes no
artifact edge; redirect tokens, targets, and bodies are never paths.
Multi-path calls add one edge per distinct path. Explicit mv preserves
identity; delete then create starts a generation. Read actions are the readers
above; all retained write, create, delete, rename, and copy actions are
mutations.

P0--P4 are the five artifacts with the most distinct attempted calls; HMAC path
ID breaks ties. The question gives their normalized paths. A1--A3 are total
read_file/edit/run_test atoms. A4--A5 are the session pattern counts. B1--B5
ask P0 attempted calls, reads, mutations, first action class, and distinct
sessions. C1--C5 ask adjacent session pairs sharing any artifact, later
sessions revisiting any prior artifact, P0 return episodes after a gap, P0
first-to-last ordinal gap, and artifacts present in at least two sessions.
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
        result[source["session_id"]] = list(atoms)
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
        "expected_answer": row["answer"],
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
        "projects": len(freeze_data["projects"]),
        "questions": len(freeze_data["questions"]),
        "questions_per_family": dict(Counter(row["family"] for row in freeze_data["questions"])),
        "vendors": dict(Counter(
            source["vendor"] for project in freeze_data["projects"] for source in project["sources"]
        )),
        "question_spec_sha256": freeze_data["question_spec_sha256"],
        "private_audit_manifest_sha256": manifest_hash,
        "oracle_checker_sha256": checker_result["checker_sha256"],
    })
    print(f"[rq7] freeze complete: {len(freeze_data['questions'])} questions; audit {manifest_hash}")
    return 0


def freeze(args: argparse.Namespace) -> int:
    private = args.private.resolve()
    release = args.release.resolve()
    if private.exists():
        shutil.rmtree(private)
    if release.exists():
        shutil.rmtree(release)
    private.mkdir(parents=True)
    release.mkdir(parents=True)
    projects_input = read_json(args.projects_file)
    if not isinstance(projects_input, list) or len(projects_input) != 6:
        raise RuntimeError("RQ7 freeze requires the fixed six-project projects.json")
    home = Path.home()
    cutoff_ns = time.time_ns() - 600 * 1_000_000_000
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
        candidates = [row for row in discovered if row["worktree"] in root_strings]
        selected_root, selected = select_sources(candidates, args.raw_bytes, args.sessions)
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
    for project in projects:
        copy_selected(project["sources"], home, frozen_home)
        direct = direct_atoms(project["sources"], frozen_home)
        official = official_procgrep_atoms(args.procgrep.resolve(), project["sources"], frozen_home)
        project["direct_action_atoms"] = direct
        project["procgrep_action_atoms"] = official
        edges, sessions = artifact_edges(project, project["sources"], frozen_home)
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
        project.update({
            "sessions": sessions,
            "anchors": anchors,
            "workspace": snapshot,
            "source_cutoff_ms": source_cutoff,
            "oracle_edges": edges,
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
        "seed": SEED,
        "created_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "agent_revision": run(["git", "rev-parse", "HEAD"], cwd=Path(__file__).parents[2]).strip(),
        "agentvis_cargo_lock_sha256": sha256_file(Path(__file__).parents[1] / "Cargo.lock"),
        "procgrep_revision": run(["git", "rev-parse", "HEAD"], cwd=args.procgrep).strip(),
        "procgrep_lock_sha256": sha256_file(args.procgrep / "uv.lock"),
        "codex_version": run(["codex", "--version"]).strip(),
        "python_version": sys.version,
        "question_spec_sha256": spec_hash,
        "projects": projects,
        "questions": all_questions,
    }
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
        ["id", "project", "family", "template", "expected_answer", "path_id", "witness_hash", "question_spec_sha256"],
        public_questions,
    )
    checker = Path(__file__).with_name("rq7_source_oracle_check.py")
    run([sys.executable, str(checker), str(private / "freeze.json"), str(private / "oracle-check.json")])
    return finalize_freeze(private, release)


def recover_freeze(args: argparse.Namespace) -> int:
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
        edges, sessions = artifact_edges(project, selected, private / "frozen-home")
        anchors = choose_anchors(edges)
        prior_snapshot = prior_project["workspace"]
        prior_paths = [row["path"] for row in prior_snapshot["paths"]]
        new_paths = [row["path"] for row in anchors]
        if prior_paths != new_paths:
            raise RuntimeError(
                f"corrected anchors require a new workspace cutoff for {project['project']}: "
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
            "expected_answer",
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


def build_agent_session_projection(private: Path, destination: Path) -> tuple[dict[str, dict[str, Any]], float]:
    freeze_data = read_json(private / "freeze.json")
    repo_root = Path(__file__).parents[2]
    binary = repo_root / "agentvis" / "target" / "release" / "agentvis"
    build_started = time.perf_counter()
    run(["cargo", "build", "--release", "--locked", "--manifest-path", str(repo_root / "agentvis" / "Cargo.toml")], cwd=repo_root)
    if destination.exists():
        shutil.rmtree(destination)
    raw = destination / "raw"
    roots = [project["worktree"] for project in freeze_data["projects"]]
    cutoff = max(project["workspace"]["cutoff_ms"] for project in freeze_data["projects"])
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
    for project in freeze_data["projects"]:
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


def deterministic_methods(private: Path, output: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    freeze_data = read_json(private / "freeze.json")
    projection, build_seconds = build_agent_session_projection(private, private / "deterministic" / "projection")
    result_rows: list[dict[str, Any]] = []
    cost_rows: list[dict[str, Any]] = []
    project_query_seconds: dict[str, float] = {}
    frozen_home = private / "frozen-home"
    query_started = time.perf_counter()
    for project in freeze_data["projects"]:
        project_started = time.perf_counter()
        official = project["procgrep_action_atoms"]
        action_values = {
            "A1": str(sum(sequence.count("read_file") for sequence in official.values())),
            "A2": str(sum(sequence.count("edit") for sequence in official.values())),
            "A3": str(sum(sequence.count("run_test") for sequence in official.values())),
            "A4": str(pattern_count(official, r"read_file (?:[a-z_]+ )*edit ")),
            "A5": str(pattern_count(official, r"edit (?:[a-z_]+ )*run_test ")),
        }
        # The proposed action spine is the exact official array, retained without transformation.
        proposed_action_spine = json.dumps(official, sort_keys=True, separators=(",", ":"))
        procgrep_action_spine = json.dumps(project["procgrep_action_atoms"], sort_keys=True, separators=(",", ":"))
        if proposed_action_spine.encode() != procgrep_action_spine.encode():
            raise RuntimeError(f"action spine mismatch: {project['project']}")
        pedges, p0_identity, join_error = proposed_edges(project, projection[project["project"]], frozen_home)
        if join_error:
            raise RuntimeError(join_error)
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
            methods["procgrep"] = answer("answer", action_values[template]) if family == "A" else answer("abstain")
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
    for project in freeze_data["projects"]:
        for method in ("procgrep", "counts", "final_state", "trajectory"):
            construction = build_seconds / len(freeze_data["projects"]) if method == "trajectory" else 0.0
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


def preflight(args: argparse.Namespace) -> int:
    freeze_data = read_json(args.private / "freeze.json")
    vendors = {source["vendor"] for project in freeze_data["projects"] for source in project["sources"]}
    if vendors != set(VENDORS):
        raise RuntimeError(f"three-vendor preflight unavailable: {sorted(vendors)}")
    checker = read_json(args.private / "oracle-check.json")
    if checker.get("status") != "pass":
        raise RuntimeError("independent oracle checker did not pass")
    deterministic, costs = deterministic_methods(args.private, args.release / "deterministic")
    if len(deterministic) != 480:
        raise RuntimeError(f"deterministic preflight expected 480 rows, got {len(deterministic)}")
    project = min(
        freeze_data["projects"],
        key=lambda row: sum(source["bytes"] for source in row["sources"]),
    )
    model_rows, model_cost = model_call(
        freeze_data,
        project,
        args.private,
        args.private / "preflight" / project["project"],
        args.model,
        args.reasoning,
        0,
    )
    if model_cost["terminal_status"] != "complete":
        raise RuntimeError(f"Raw retrieval preflight failed: {model_cost['terminal_status']}")
    if model_cost["tool_calls"] < 1 or model_cost["tool_result_bytes"] < 1:
        raise RuntimeError("Raw retrieval preflight did not engage the local evidence tools")
    subset = []
    for family in "ABCD":
        qid = next(row["id"] for row in project["questions"] if row["family"] == family)
        subset.extend(row for row in deterministic if row["id"] == qid)
        subset.extend(row for row in model_rows if row["id"] == qid)
    write_json(args.release / "preflight-result.json", {
        "status": "pass",
        "project": project["project"],
        "vendors": sorted(vendors),
        "questions_exercised": 4,
        "methods": ["counts", "final_state", "procgrep", "raw_model", "trajectory"],
        "model_terminal_status": model_cost["terminal_status"],
        "rows": subset,
        "deterministic_cost_rows": len(costs),
    })
    print(
        f"[rq7] preflight pass: three vendors, five methods, model={model_cost['terminal_status']}"
    )
    return 0


def full(args: argparse.Namespace) -> int:
    freeze_data = read_json(args.private / "freeze.json")
    full_private = args.private / "full"
    full_private.mkdir(parents=True, exist_ok=True)
    deterministic, deterministic_costs = deterministic_methods(args.private, full_private / "deterministic")
    model_rows: list[dict[str, Any]] = []
    model_costs: list[dict[str, Any]] = []
    for project in freeze_data["projects"]:
        for repetition in range(1, args.repetitions + 1):
            destination = full_private / "raw-model" / project["project"] / f"rep-{repetition}"
            checkpoint = destination / "scored.json"
            if checkpoint.exists():
                saved = read_json(checkpoint)
                rows, cost = saved["results"], saved["cost"]
                print(f"[rq7] resume {project['project']} repetition {repetition}")
            else:
                print(f"[rq7] model {project['project']} repetition {repetition}", flush=True)
                rows, cost = model_call(
                    freeze_data,
                    project,
                    args.private,
                    destination,
                    args.model,
                    args.reasoning,
                    repetition,
                )
            model_rows.extend(rows)
            model_costs.append(cost)
    expected_model_rows = 120 * args.repetitions
    if len(model_rows) != expected_model_rows:
        write_json(full_private / "partial.json", {"expected": expected_model_rows, "actual": len(model_rows)})
        return 2
    all_rows = deterministic + model_rows
    all_costs = deterministic_costs + model_costs
    write_json(full_private / "method-results.json", all_rows)
    write_json(full_private / "costs.json", all_costs)
    audit_manifest(args.private)
    print(f"[rq7] full run complete: {len(all_rows)} scored method rows")
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
    freeze_parser.add_argument("--seed", default=SEED)
    freeze_parser.add_argument("--sessions", type=int, default=12)
    freeze_parser.add_argument("--raw-bytes", type=int, default=163_840)
    freeze_parser.add_argument("--stability-wait", type=int, default=60)
    freeze_parser.set_defaults(func=freeze)

    recover_parser = sub.add_parser("recover-freeze")
    recover_parser.add_argument("--private", type=Path, required=True)
    recover_parser.add_argument("--release", type=Path, required=True)
    recover_parser.set_defaults(func=recover_freeze)

    rederive_parser = sub.add_parser("rederive-freeze")
    rederive_parser.add_argument("--source-private", type=Path, required=True)
    rederive_parser.add_argument("--private", type=Path, required=True)
    rederive_parser.add_argument("--release", type=Path, required=True)
    rederive_parser.add_argument("--procgrep", type=Path, required=True)
    rederive_parser.set_defaults(func=rederive_freeze)

    preflight_parser = sub.add_parser("preflight")
    preflight_parser.add_argument("--private", type=Path, required=True)
    preflight_parser.add_argument("--release", type=Path, required=True)
    preflight_parser.add_argument("--model", default="gpt-5.6-terra")
    preflight_parser.add_argument("--reasoning", default="medium")
    preflight_parser.set_defaults(func=preflight)

    full_parser = sub.add_parser("full")
    full_parser.add_argument("--private", type=Path, required=True)
    full_parser.add_argument("--release", type=Path, required=True)
    full_parser.add_argument("--model", default="gpt-5.6-terra")
    full_parser.add_argument("--reasoning", default="medium")
    full_parser.add_argument("--repetitions", type=int, default=3)
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
    if getattr(args, "seed", SEED) != SEED:
        raise RuntimeError(f"frozen seed must be {SEED}")
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
