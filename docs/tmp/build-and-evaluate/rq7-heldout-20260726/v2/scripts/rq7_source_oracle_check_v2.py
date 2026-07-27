#!/usr/bin/env python3
"""Independent source-direct checker for the RQ7 P1-v2 factual oracle.

This checker intentionally imports neither rq7_measurement nor agent-session.
It reopens every selected native transcript, rebuilds action sequences and
artifact/session relations, reselects P0--P4, and compares exactly the frozen
proportional question-ID subset while still recomputing all templates.
"""

# Changelog:
# - v4: decode and edit-classify static Codex exec/apply_patch JS wrappers;
#   track lexical inline-cd state for later shell file operands.
# - v3: use native-root identity, result-aware lifecycles, per-command option
#   arity, and explicit sed-program handling.

from __future__ import annotations

import datetime as dt
import hashlib
import hmac
import json
import os
import re
import shlex
import sys
from collections import Counter, defaultdict
from pathlib import Path, PurePosixPath
from typing import Any


SEED = "20260722"
SPEC_VERSION = "native-root-conformance-v4"
READERS = {"cat", "sed", "head", "tail", "nl", "less", "more"}
MUTATORS = {"touch", "rm", "mv", "cp"}
SHELL_TOOLS = {"bash", "exec", "exec_command", "shell_command", "run_shell_command", "shell"}
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
INJECTED = (
    "<task-notification>",
    "<system-reminder>",
    "<command-name>",
    "<command-message>",
    "<command-args>",
    "<local-command-stdout>",
    "<bash-stdout>",
    "<bash-stderr>",
)


def digest_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def digest_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def stream_key(vendor: str, native_session_id: str, source_stem: str) -> str:
    material = "\0".join((vendor, native_session_id, source_stem))
    return digest_bytes(material.encode())[:16]


def classify_output(output: str) -> str:
    lowered = output.lower()
    successes = (
        "process exited with code 0",
        "script completed",
        "command completed",
        '"is_error":false',
    )
    failures = ("process exited with code", '"is_error":true', "error")
    if any(marker in lowered for marker in successes):
        return "ok"
    if any(marker in lowered for marker in failures):
        return "fail"
    return "observed"


def number_tools(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    position = 0
    for event in events:
        if event.get("kind") == "tool":
            event["tool_ordinal"] = position
            event.setdefault("status", "observed")
            position += 1
    return events


def timestamp_ms(value: Any) -> int | None:
    if isinstance(value, (int, float)):
        number = int(value)
        return number * 1000 if number < 10_000_000_000 else number
    if not isinstance(value, str) or not value:
        return None
    try:
        return int(dt.datetime.fromisoformat(value.strip().replace("Z", "+00:00")).timestamp() * 1000)
    except ValueError:
        return None


def load_native(path: Path) -> Any:
    if path.suffix == ".json":
        return json.loads(path.read_text())
    rows = []
    for line in path.read_text(errors="replace").splitlines():
        try:
            value = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            rows.append(value)
    return rows


def arguments(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    if not isinstance(value, str):
        return {}
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        return {"command": value}
    return parsed if isinstance(parsed, dict) else {"command": value}


def command_of(name: str, args: dict[str, Any]) -> str:
    value = args.get("command", args.get("cmd", args.get("input", "")))
    if isinstance(value, list):
        return " ".join(map(str, value))
    return value if isinstance(value, str) else ""


def js_string_literal(text: str, opening: int) -> tuple[str, int] | None:
    """Decode one static double-quoted JS string using its JSON-compatible form."""
    if opening >= len(text) or text[opening] != '"':
        return None
    escaped = False
    for offset in range(opening + 1, len(text)):
        character = text[offset]
        if escaped:
            escaped = False
        elif character == "\\":
            escaped = True
        elif character == '"':
            try:
                value = json.loads(text[opening : offset + 1])
            except json.JSONDecodeError:
                return None
            return (value, offset + 1) if isinstance(value, str) else None
    return None


def wrapped_apply_patch(text: str) -> str | None:
    """Return a statically assigned patch passed to tools.apply_patch()."""
    assignment = re.compile(
        r"\b(?:const|let|var)\s+([A-Za-z_$][A-Za-z0-9_$]*)\s*=\s*"
    )
    for match in assignment.finditer(text):
        decoded = js_string_literal(text, match.end())
        if decoded is None:
            continue
        value, _ = decoded
        variable = re.escape(match.group(1))
        if (
            "*** Begin Patch" in value
            and re.search(rf"\btools\.apply_patch\s*\(\s*{variable}\s*\)", text)
        ):
            return value
    return None


def unwrap_exec(name: str, args: dict[str, Any]) -> dict[str, Any]:
    if name.lower() != "exec":
        return args
    text = command_of(name, args)
    patch = wrapped_apply_patch(text)
    marker = text.find("tools.exec_command(")
    opening = text.find("{", marker + 1) if marker >= 0 else -1
    if opening < 0:
        return {**args, "_wrapped_patch": patch} if patch is not None else args
    depth = 0
    in_string = False
    escaped = False
    closing = -1
    for offset, character in enumerate(text[opening:], start=opening):
        if escaped:
            escaped = False
        elif in_string and character == "\\":
            escaped = True
        elif character == '"':
            in_string = not in_string
        elif not in_string and character == "{":
            depth += 1
        elif not in_string and character == "}":
            depth -= 1
            if depth == 0:
                closing = offset + 1
                break
    if closing < 0:
        return {**args, "_wrapped_patch": patch} if patch is not None else args
    raw = text[opening:closing]
    try:
        nested = json.loads(raw)
    except json.JSONDecodeError:
        raw = re.sub(
            r"([{,]\s*)([A-Za-z_][A-Za-z0-9_-]*)(\s*:)",
            r'\1"\2"\3',
            raw,
        )
        try:
            nested = json.loads(raw)
        except json.JSONDecodeError:
            return {**args, "_wrapped_patch": patch} if patch is not None else args
    if not isinstance(nested, dict):
        nested = args
    return {**nested, "_wrapped_patch": patch} if patch is not None else nested


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
        executable = shlex.split(command)[0].rsplit("/", 1)[-1].lower()
    except (ValueError, IndexError):
        executable = ""
    return "read_file" if executable in READERS else "other"


def atom_for(name: str, args: dict[str, Any]) -> str:
    lower = name.lower()
    if lower in {"read", "notebookread", "read_file"}:
        return "read_file"
    if lower in {"edit", "write", "notebookedit", "multiedit", "apply_patch"}:
        return "edit"
    if lower in {"grep", "glob", "websearch", "webfetch", "search_file_content", "list_directory"}:
        return "search_repo"
    if lower in {"todowrite", "exitplanmode", "update_plan", "write_todos", "exit_plan_mode"}:
        return "think"
    if lower in SHELL_TOOLS:
        if isinstance(args.get("_wrapped_patch"), str):
            return "edit"
        return command_atom(command_of(name, args))
    return "other"


def human_prompt(content: Any) -> bool:
    if isinstance(content, str):
        text = content
    elif isinstance(content, list):
        text_blocks = [
            str(block.get("text") or "")
            for block in content
            if isinstance(block, dict) and block.get("type") == "text"
        ]
        if not text_blocks or any(
            isinstance(block, dict) and block.get("type") == "tool_result" for block in content
        ):
            return False
        text = " ".join(text_blocks)
    else:
        return False
    stripped = text.strip()
    return bool(stripped) and not stripped.startswith(INJECTED)


def codex_root_identity(payload: dict[str, Any], fallback: str) -> str:
    for key in ("session_id", "parent_thread_id", "thread_id", "id"):
        value = payload.get(key)
        if value:
            return str(value)
    return fallback


def native_identity(vendor: str, source: Any, fallback: str) -> str:
    if vendor == "gemini" and isinstance(source, dict):
        return str(source.get("sessionId") or fallback)
    if not isinstance(source, list):
        return fallback
    for row in source:
        if vendor == "claude" and row.get("sessionId"):
            fallback = str(row["sessionId"])
        if vendor == "codex" and row.get("type") == "session_meta":
            payload = row.get("payload") if isinstance(row.get("payload"), dict) else {}
            fallback = codex_root_identity(payload, fallback)
    return fallback


def events_from_source(vendor: str, source: Any, default_cwd: str) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    if vendor == "gemini":
        if not isinstance(source, dict):
            return events
        for record_index, message in enumerate(source.get("messages") or []):
            if not isinstance(message, dict):
                continue
            stamp = timestamp_ms(message.get("timestamp") or message.get("time"))
            if message.get("type") == "user" and human_prompt(message.get("content")):
                events.append({"kind": "prompt", "atom": "prompt_ai", "ts": stamp, "record": record_index, "call": 0})
            if message.get("type") != "gemini":
                continue
            for call_index, call in enumerate(message.get("toolCalls") or []):
                if not isinstance(call, dict):
                    continue
                args = call.get("args") if isinstance(call.get("args"), dict) else {}
                name = str(call.get("name") or "")
                args = unwrap_exec(name, args)
                events.append({
                    "kind": "tool",
                    "name": name,
                    "args": args,
                    "id": str(call.get("id") or call.get("callId") or f"{record_index}:{call_index}"),
                    "cwd": str(args.get("workdir") or default_cwd),
                    "atom": atom_for(name, args),
                    "ts": stamp,
                    "record": record_index,
                    "call": call_index,
                    "status": {
                        "success": "ok",
                        "error": "fail",
                    }.get(str(call.get("status") or "").lower(), "observed"),
                })
        return number_tools(events)

    cwd = default_cwd
    call_position: dict[str, int] = {}
    if not isinstance(source, list):
        return events
    for record_index, row in enumerate(source):
        stamp = timestamp_ms(row.get("timestamp"))
        if vendor == "claude":
            cwd = str(row.get("cwd") or cwd)
            message = row.get("message") if isinstance(row.get("message"), dict) else {}
            content = message.get("content")
            if row.get("type") == "user" and human_prompt(content):
                events.append({"kind": "prompt", "atom": "prompt_ai", "ts": stamp, "record": record_index, "call": 0})
            if row.get("type") == "user" and isinstance(content, list):
                fallback_row = row.get("toolUseResult")
                fallback = bool(
                    fallback_row.get("is_error")
                    if isinstance(fallback_row, dict)
                    else False
                )
                for block in content:
                    if not isinstance(block, dict) or block.get("type") != "tool_result":
                        continue
                    position = call_position.get(str(block.get("tool_use_id") or ""))
                    if position is not None:
                        events[position]["status"] = (
                            "fail" if bool(block.get("is_error", fallback)) else "ok"
                        )
            if row.get("type") != "assistant" or not isinstance(content, list):
                continue
            call_index = 0
            for block in content:
                if not isinstance(block, dict) or block.get("type") != "tool_use":
                    continue
                args = block.get("input") if isinstance(block.get("input"), dict) else {}
                name = str(block.get("name") or "")
                args = unwrap_exec(name, args)
                events.append({
                    "kind": "tool", "name": name, "args": args,
                    "id": str(block.get("id") or f"{record_index}:{call_index}"),
                    "cwd": str(args.get("workdir") or cwd), "atom": atom_for(name, args),
                    "ts": stamp, "record": record_index, "call": call_index,
                    "status": "observed",
                })
                call_position[str(block.get("id") or f"{record_index}:{call_index}")] = len(events) - 1
                call_index += 1
        else:
            payload = row.get("payload") if isinstance(row.get("payload"), dict) else {}
            if row.get("type") in {"session_meta", "turn_context"}:
                cwd = str(payload.get("cwd") or cwd)
            if (
                row.get("type") == "response_item"
                and payload.get("type") in {"function_call", "custom_tool_call"}
            ):
                name = str(payload.get("name") or "")
                args = arguments(payload.get("arguments", payload.get("input")))
                args = unwrap_exec(name, args)
                events.append({
                    "kind": "tool", "name": name, "args": args,
                    "id": str(payload.get("call_id") or payload.get("id") or f"{record_index}:0"),
                    "cwd": str(args.get("workdir") or cwd), "atom": atom_for(name, args),
                    "ts": stamp, "record": record_index, "call": 0,
                    "status": "observed",
                })
                call_position[
                    str(payload.get("call_id") or payload.get("id") or f"{record_index}:0")
                ] = len(events) - 1
            elif (
                row.get("type") == "response_item"
                and payload.get("type") in {"function_call_output", "custom_tool_call_output"}
            ):
                position = call_position.get(str(payload.get("call_id") or ""))
                if position is not None:
                    raw_output = payload.get("output")
                    output = (
                        raw_output
                        if isinstance(raw_output, str)
                        else json.dumps(raw_output, sort_keys=True)
                    )
                    events[position]["status"] = classify_output(output)
    return number_tools(events)


def nested_paths(value: Any) -> list[str]:
    found: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            if key.lower() in PATH_KEYS and isinstance(child, str):
                found.append(child)
            else:
                found.extend(nested_paths(child))
    elif isinstance(value, list):
        for child in value:
            found.extend(nested_paths(child))
    return found


def shell_commands(command: str) -> list[list[str]]:
    commands: list[list[str]] = []
    delimiter: str | None = None
    for line in command.splitlines():
        if delimiter is not None:
            if line.strip() == delimiter:
                delimiter = None
            continue
        marker = re.search(r"<<-?\s*['\"]?([A-Za-z_][A-Za-z0-9_]*)['\"]?", line)
        if marker:
            delimiter = marker.group(1)
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
                    commands.append(current)
                    current = []
            else:
                current.append(token)
        if current:
            commands.append(current)
    return commands


def path_operands(command: str, tokens: list[str]) -> list[str]:
    values: list[str] = []
    skip_next = False
    options_done = False
    explicit_sed_program = False
    arity = {
        "head": {"-n", "--lines", "-c", "--bytes"},
        "tail": {"-n", "--lines", "-c", "--bytes", "-s", "--sleep-interval", "--pid"},
        "sed": {"-e", "--expression", "-f", "--file"},
        "nl": {"-b", "--body-numbering", "-d", "--section-delimiter", "-f", "--footer-numbering",
               "-h", "--header-numbering", "-i", "--line-increment", "-l", "--join-blank-lines",
               "-n", "--number-format", "-s", "--number-separator", "-v", "--starting-line-number",
               "-w", "--number-width"},
    }.get(command, set())
    for token in tokens:
        if skip_next:
            skip_next = False
            continue
        if token == "--":
            options_done = True
            continue
        name = token.split("=", 1)[0]
        if not options_done and name in arity:
            explicit_sed_program |= command == "sed" and name in {
                "-e", "--expression", "-f", "--file"
            }
            skip_next = "=" not in token
        elif not options_done and token.startswith("-"):
            continue
        else:
            values.append(token)
    if command == "sed" and not explicit_sed_program and values:
        values = values[1:]
    return values


def shell_effects(
    command: str,
    cwd: str = "",
) -> list[tuple[str, str, str | None]]:
    effects: list[tuple[str, str, str | None]] = []
    shell_cwd = cwd
    cwd_known = True
    for tokens in shell_commands(command):
        if not tokens or any(token and set(token) <= {"<", ">"} for token in tokens):
            continue
        name = tokens[0].rsplit("/", 1)[-1].lower()
        if name == "cd":
            operands = [
                token
                for token in tokens[1:]
                if token != "--" and not token.startswith("-")
            ]
            if (
                len(operands) != 1
                or any(char in operands[0] for char in "$*?[]{}<>")
                or operands[0].startswith("~")
            ):
                cwd_known = False
                continue
            target = Path(operands[0])
            if not target.is_absolute():
                if not cwd_known:
                    continue
                target = Path(shell_cwd) / target if shell_cwd else target
            shell_cwd = os.path.normpath(str(target))
            cwd_known = True
            continue
        if name not in READERS | MUTATORS:
            continue
        values = path_operands(name, tokens[1:])
        qualified = []
        for value in values:
            if Path(value).is_absolute():
                qualified.append(value)
            elif cwd_known:
                qualified.append(
                    os.path.normpath(str(Path(shell_cwd) / value))
                    if shell_cwd
                    else value
                )
        values = qualified
        if name in {"mv", "cp"}:
            if len(values) < 2:
                continue
            source, destination = values[-2:]
            if name == "mv":
                effects.extend([(source, "rename_from", None), (destination, "rename", source)])
            else:
                effects.extend([(source, "read", None), (destination, "create", None)])
            continue
        access = "read" if name in READERS else ("delete" if name == "rm" else "create")
        effects.extend((value, access, None) for value in values)
    return effects


def event_effects(event: dict[str, Any]) -> list[tuple[str, str, str | None]]:
    if event.get("kind") != "tool":
        return []
    name = str(event.get("name") or "").lower()
    args = event.get("args") if isinstance(event.get("args"), dict) else {}
    command = command_of(name, args)
    wrapped_patch = args.get("_wrapped_patch")
    is_patch = name == "apply_patch" or (
        name in SHELL_TOOLS
        and (
            isinstance(wrapped_patch, str)
            or "*** Begin Patch" in command
        )
    )
    effects = (
        shell_effects(command, str(event.get("cwd") or ""))
        if name in SHELL_TOOLS
        and not (isinstance(wrapped_patch, str) and "tools.apply_patch" in command)
        else []
    )
    if is_patch:
        patch = (
            wrapped_patch
            if isinstance(wrapped_patch, str)
            else command or str(args.get("patch") or "")
        )
        pending_update: str | None = None
        for raw_line in patch.splitlines():
            line = raw_line.strip()
            match = PATCH_RE.fullmatch(line)
            if match:
                kind, raw_path = match.groups()
                path = raw_path.strip()
                effects.append((
                    path,
                    {"Add": "create", "Update": "write", "Delete": "delete"}[kind],
                    None,
                ))
                pending_update = path if kind == "Update" else None
                continue
            move = MOVE_RE.fullmatch(line)
            if move and pending_update:
                effects = [
                    effect
                    for effect in effects
                    if not (effect[0] == pending_update and effect[1] == "write")
                ]
                effects.extend([
                    (pending_update, "rename_from", None),
                    (move.group(1).strip(), "rename", pending_update),
                ])
                pending_update = None
    access = {
        "read": "read",
        "notebookread": "read",
        "read_file": "read",
        "edit": "write",
        "notebookedit": "write",
        "multiedit": "write",
        "write": "create",
        "write_file": "create",
    }.get(name)
    if access:
        effects.extend((path, access, None) for path in nested_paths(args))
    unique = list(dict.fromkeys(effects))
    priority = {"rename_from": 0, "rename": 1}
    return sorted(
        unique,
        key=lambda effect: (
            priority.get(effect[1], 2),
            effect[0],
            effect[1],
            effect[2] or "",
        ),
    )


def repo_path(raw: str, cwd: str, root: Path) -> str | None:
    if not raw or any(char in raw for char in "$*?[]{}<>"):
        return None
    candidate = Path(raw)
    if not candidate.is_absolute():
        candidate = Path(cwd or root) / candidate
    normalized = Path(os.path.normpath(str(candidate)))
    try:
        relative = normalized.relative_to(root)
    except ValueError:
        return None
    result = str(PurePosixPath(relative.as_posix()))
    return result if result not in {"", "."} else None


class Identities:
    def __init__(self) -> None:
        self.current: dict[tuple[str, str], str] = {}
        self.attempted: dict[tuple[str, str], str] = {}
        self.next_generation: Counter[tuple[str, str]] = Counter()
        self.display: dict[str, str] = {}

    def new(self, path: str, worktree: str = "w") -> str:
        key = (worktree, path)
        identity = f"{path}#{self.next_generation[key]}"
        self.next_generation[key] += 1
        self.display[identity] = path
        return identity

    def resolve(
        self,
        path: str,
        access: str,
        previous: str | None,
        confirmed: bool,
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
                or self.new(previous, previous_worktree)
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
                    identity = self.new(path, worktree)
                    self.attempted[key] = identity
            self.display[identity] = path
            return identity
        identity = self.current.get(key)
        if identity is None:
            if access == "create":
                identity = self.new(path, worktree)
            else:
                identity = self.attempted.pop(key, None) or self.new(path, worktree)
            self.current[key] = identity
        self.attempted.pop(key, None)
        if access == "delete":
            self.current.pop(key, None)
        self.display[identity] = path
        return identity


def path_id(path: str) -> str:
    key = hashlib.sha256(("rq7-path-salt-" + SEED).encode()).digest()
    return hmac.new(key, path.encode(), hashlib.sha256).hexdigest()[:16]


def recompute_project(
    private: Path,
    project: dict[str, Any],
) -> tuple[dict[str, str], list[dict[str, Any]], list[dict[str, Any]]]:
    root = Path(project["worktree"])
    sessions = []
    for source_meta in project["sources"]:
        path = private / "frozen-home" / source_meta["home_relative"]
        if path.stat().st_size != source_meta["bytes"] or digest_file(path) != source_meta["sha256"]:
            raise RuntimeError(f"source hash/size mismatch: {source_meta['source_id']}")
        native = load_native(path)
        identity = native_identity(source_meta["vendor"], native, path.stem)
        if identity != source_meta["native_session_id"]:
            raise RuntimeError(f"native session mismatch: {source_meta['source_id']}")
        events = [
            event
            for event in events_from_source(source_meta["vendor"], native, str(root))
            if event.get("ts") is not None
        ]
        if not any(event.get("kind") == "tool" for event in events):
            continue
        first = min(
            event["ts"] for event in events if event.get("kind") == "tool"
        )
        semantic = f"{source_meta['vendor']}:{source_meta['native_session_id']}"
        sessions.append({
            **source_meta,
            "events": events,
            "first": first,
            "semantic_session_id": semantic,
            "source_stream_id": stream_key(
                source_meta["vendor"],
                source_meta["native_session_id"],
                source_meta["source_stem"],
            ),
        })
    sessions.sort(key=lambda row: (row["first"], row["semantic_session_id"]))

    sequences = {
        row["semantic_session_id"]: [event["atom"] for event in row["events"]]
        for row in sessions
    }
    ordered = []
    for ordinal, session in enumerate(sessions):
        for event in session["events"]:
            if event.get("kind") != "tool":
                continue
            ordered.append((
                event["ts"] if event.get("ts") is not None else session["first"],
                session["source_stream_id"],
                event.get("tool_ordinal", -1),
                f"{event['record']}:{event['call']}",
                ordinal,
                session,
                event,
            ))
    ordered.sort(key=lambda row: row[:4])
    identities = Identities()
    edges = []
    calls = []
    pending: dict[tuple[str, str], str] = {}
    for event_ordinal, (_, _, _, _, session_ordinal, session, event) in enumerate(ordered):
        if event.get("kind") == "tool":
            calls.append({
                "project": project["project"],
                "vendor": session["vendor"],
                "native_session_id": session["semantic_session_id"],
                "session_ordinal": session_ordinal,
                "source_stream_id": session["source_stream_id"],
                "source_tool_ordinal": event["tool_ordinal"],
                "call_id": str(event["id"]),
                "status": str(event.get("status") or "observed"),
                "atom": str(event["atom"]),
            })
        normalized_effects = []
        for raw_path, access, old_raw in event_effects(event):
            normalized = repo_path(raw_path, str(event.get("cwd") or root), root)
            if normalized is None:
                continue
            previous = repo_path(old_raw, str(event.get("cwd") or root), root) if old_raw else None
            normalized_effects.append((normalized, access, previous))
        normalized_effects = list(dict.fromkeys(normalized_effects))
        normalized_effects.sort(
            key=lambda effect: (
                {"rename_from": 0, "rename": 1}.get(effect[1], 2),
                effect[0],
                effect[1],
                effect[2] or "",
            )
        )
        for action_ordinal, (normalized, access, previous) in enumerate(normalized_effects):
            key = (session["semantic_session_id"], str(event["id"]))
            if access == "rename_from":
                pending[key] = normalized
            elif access == "rename" and previous is None:
                previous = pending.get(key)
            status = str(event.get("status") or "observed")
            identity = identities.resolve(normalized, access, previous, status == "ok")
            edges.append({
                "session_id": session["semantic_session_id"],
                "native_session_id": session["semantic_session_id"],
                "session_ordinal": session_ordinal,
                "vendor": session["vendor"],
                "source_id": session["source_id"],
                "source_sha256": session["sha256"],
                "source_stream_id": session["source_stream_id"],
                "source_tool_ordinal": event["tool_ordinal"],
                "record_index": event["record"],
                "call_index": event["call"],
                "call_id": str(event["id"]),
                "event_ordinal": event_ordinal,
                "action_ordinal": action_ordinal,
                "artifact_id": identity,
                "path": normalized,
                "access": access,
                "previous_path": previous,
                "action_class": "read" if access == "read" else "mutate",
                "status": status,
                "confirmed_effect": status == "ok",
            })
    for edge in edges:
        edge["display_path"] = identities.display[edge["artifact_id"]]

    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for edge in edges:
        grouped[edge["artifact_id"]].append(edge)
    anchors = []
    for identity, rows in grouped.items():
        anchors.append({
            "artifact_id": identity,
            "path": rows[-1]["display_path"],
            "path_id": path_id(rows[-1]["display_path"]),
            "call_count": len({(row["session_id"], row["call_id"]) for row in rows}),
        })
    anchors.sort(key=lambda row: (-row["call_count"], row["path_id"]))
    anchors = anchors[:5]
    expected_anchors = [
        {key: row[key] for key in ("artifact_id", "path", "path_id", "call_count")}
        for row in project["anchors"]
    ]
    if anchors != expected_anchors:
        raise RuntimeError(f"source-direct anchor mismatch: {project['project']}")

    p0 = anchors[0]["artifact_id"]
    p0_edges = [row for row in edges if row["artifact_id"] == p0]
    p0_calls = {(row["session_id"], row["call_id"]): row for row in p0_edges}
    p0_ordinals = sorted({row["session_ordinal"] for row in p0_edges})
    session_sets = [set() for _ in sessions]
    for edge in edges:
        session_sets[edge["session_ordinal"]].add(edge["artifact_id"])
    prior: set[str] = set()
    revisit = 0
    for current in session_sets:
        revisit += bool(prior & current)
        prior |= current
    presence = [index in p0_ordinals for index in range(len(sessions))]
    seen = gap = False
    returns = 0
    for active in presence:
        if active:
            returns += bool(seen and gap)
            seen, gap = True, False
        elif seen:
            gap = True
    artifact_sessions: dict[str, set[int]] = defaultdict(set)
    for edge in edges:
        artifact_sessions[edge["artifact_id"]].add(edge["session_ordinal"])

    joined = [" ".join(sequence) + " " for sequence in sequences.values()]
    answers: dict[str, str] = {
        "A1": str(sum(sequence.count("read_file") for sequence in sequences.values())),
        "A2": str(sum(sequence.count("edit") for sequence in sequences.values())),
        "A3": str(sum(sequence.count("run_test") for sequence in sequences.values())),
        "A4": str(sum(bool(re.search(r"read_file (?:[a-z_]+ )*edit ", line)) for line in joined)),
        "A5": str(sum(bool(re.search(r"edit (?:[a-z_]+ )*run_test ", line)) for line in joined)),
        "B1": str(len(p0_calls)),
        "B2": str(sum(row["action_class"] == "read" for row in p0_calls.values())),
        "B3": str(sum(row["action_class"] == "mutate" for row in p0_calls.values())),
        "B4": min(p0_edges, key=lambda row: row["event_ordinal"])["action_class"],
        "B5": str(len(p0_ordinals)),
        "C1": str(sum(bool(left & right) for left, right in zip(session_sets, session_sets[1:]))),
        "C2": str(revisit),
        "C3": str(returns),
        "C4": str(p0_ordinals[-1] - p0_ordinals[0]),
        "C5": str(sum(len(ordinals) >= 2 for ordinals in artifact_sessions.values())),
    }
    workspace_dir = private / "workspace" / project["project"]
    for index, row in enumerate(project["workspace"]["paths"], start=1):
        if row["path"] != anchors[index - 1]["path"]:
            raise RuntimeError(f"workspace anchor mismatch: {project['project']} P{index - 1}")
        index_entry = str(row.get("index_entry") or "")
        present = bool(row.get("present"))
        derived_status = "tracked" if index_entry else ("untracked" if present else "absent")
        if derived_status != row.get("status"):
            raise RuntimeError(f"workspace status mismatch: {project['project']} P{index - 1}")
        blob = workspace_dir / f"{row['path_id']}.blob"
        if present:
            if not blob.is_file() or digest_file(blob) != row.get("content_sha256"):
                raise RuntimeError(f"workspace blob mismatch: {project['project']} P{index - 1}")
        elif blob.exists() or row.get("content_sha256"):
            raise RuntimeError(f"unexpected absent-path blob: {project['project']} P{index - 1}")
        if index_entry:
            try:
                header, indexed_path = index_entry.split("\t", 1)
                _, object_id, stage = header.split()
            except ValueError as error:
                raise RuntimeError(
                    f"invalid index entry: {project['project']} P{index - 1}"
                ) from error
            if (
                indexed_path != row["path"]
                or stage != "0"
                or not re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", object_id)
            ):
                raise RuntimeError(f"index path/stage mismatch: {project['project']} P{index - 1}")
        answers[f"D{index}"] = derived_status
    return answers, edges, calls


def main() -> int:
    if len(sys.argv) != 3:
        raise SystemExit("usage: rq7_source_oracle_check.py FREEZE_JSON OUTPUT_JSON")
    freeze_path = Path(sys.argv[1]).resolve()
    output_path = Path(sys.argv[2]).resolve()
    freeze = json.loads(freeze_path.read_text())
    if freeze.get("spec_version") != SPEC_VERSION:
        raise RuntimeError(
            f"specification mismatch: {freeze.get('spec_version')} != {SPEC_VERSION}"
        )
    private = freeze_path.parent
    recomputed: dict[str, str] = {}
    edge_count = 0
    call_count = 0
    all_edges: list[dict[str, Any]] = []
    edge_fields = (
        "native_session_id",
        "source_stream_id",
        "source_tool_ordinal",
        "call_id",
        "event_ordinal",
        "action_ordinal",
        "artifact_id",
        "path",
        "display_path",
        "access",
        "previous_path",
        "status",
        "confirmed_effect",
        "session_ordinal",
    )
    call_fields = (
        "native_session_id",
        "session_ordinal",
        "source_stream_id",
        "source_tool_ordinal",
        "call_id",
        "status",
        "atom",
    )
    for project in freeze["projects"]:
        answers, edges, calls = recompute_project(private, project)
        edge_count += len(edges)
        call_count += len(calls)
        all_edges.extend(edges)
        expected_edges = sorted(
            tuple(row.get(field) for field in edge_fields)
            for row in project.get("oracle_edges") or []
        )
        actual_edges = sorted(
            tuple(row.get(field) for field in edge_fields) for row in edges
        )
        if expected_edges != actual_edges:
            raise RuntimeError(f"complete edge ledger mismatch: {project['project']}")
        expected_calls = sorted(
            tuple(row.get(field) for field in call_fields)
            for row in project.get("oracle_calls") or []
        )
        actual_calls = sorted(
            tuple(row.get(field) for field in call_fields) for row in calls
        )
        if expected_calls != actual_calls:
            raise RuntimeError(f"complete call/status ledger mismatch: {project['project']}")
        for template, answer in answers.items():
            recomputed[f"{project['project']}-{template}"] = answer
    question_rows = freeze["questions"]
    expected = {row["id"]: row["answer"] for row in question_rows}
    contracted = int(
        freeze["question_count_contract"]["total_questions"]
    )
    if len(question_rows) != contracted or len(expected) != len(question_rows):
        raise RuntimeError(
            "frozen question count or ID uniqueness violates the v2 contract"
        )
    if not set(expected).issubset(recomputed):
        raise RuntimeError("frozen question ID is outside the recomputed template set")
    checked = {key: recomputed[key] for key in expected}
    mismatches = {
        key: {"expected": expected[key], "actual": checked[key]}
        for key in expected
        if expected[key] != checked[key]
    }
    if mismatches:
        raise RuntimeError(f"source-direct answer mismatch: {json.dumps(mismatches, sort_keys=True)}")
    invalid_paths = [
        edge["path"] for edge in all_edges if any(char in edge["path"] for char in "<>")
    ]
    if invalid_paths:
        raise RuntimeError(f"redirection-like artifact survived: {invalid_paths[:5]}")
    answer_lines = "\n".join(
        f"{key}\t{checked[key]}" for key in sorted(checked)
    ) + "\n"
    result = {
        "status": "pass",
        "questions": len(checked),
        "recomputed_templates": len(recomputed),
        "projects": len(freeze["projects"]),
        "artifact_edges": edge_count,
        "tool_calls": call_count,
        "complete_edge_ledger_match": True,
        "complete_call_status_ledger_match": True,
        "spec_version": SPEC_VERSION,
        "answers_sha256": digest_bytes(answer_lines.encode()),
        "checker_sha256": digest_file(Path(__file__)),
        "source_direct": True,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
