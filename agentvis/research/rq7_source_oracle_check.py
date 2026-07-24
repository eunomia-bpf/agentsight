#!/usr/bin/env python3
"""Independent source-direct checker for the RQ7 factual oracle.

This checker intentionally imports neither rq7_measurement nor agent-session.
It reopens every selected native transcript, rebuilds action sequences and
artifact/session relations, reselects P0--P4, and compares all 120 answers.
"""

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
READERS = {"cat", "sed", "head", "tail", "nl", "less", "more"}
MUTATORS = {"touch", "rm", "mv", "cp"}
SHELL_TOOLS = {"bash", "exec", "exec_command", "shell_command", "run_shell_command", "shell"}
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
            fallback = str(payload.get("id") or payload.get("session_id") or fallback)
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
                })
        return events

    cwd = default_cwd
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
            if row.get("type") == "file-history-snapshot":
                events.append({
                    "kind": "tool", "name": "file_snapshot", "args": {},
                    "id": f"snapshot:{record_index}", "cwd": cwd, "atom": "edit",
                    "ts": stamp, "record": record_index, "call": 0,
                })
            if row.get("type") != "assistant" or not isinstance(content, list):
                continue
            call_index = 0
            for block in content:
                if not isinstance(block, dict) or block.get("type") != "tool_use":
                    continue
                args = block.get("input") if isinstance(block.get("input"), dict) else {}
                name = str(block.get("name") or "")
                events.append({
                    "kind": "tool", "name": name, "args": args,
                    "id": str(block.get("id") or f"{record_index}:{call_index}"),
                    "cwd": str(args.get("workdir") or cwd), "atom": atom_for(name, args),
                    "ts": stamp, "record": record_index, "call": call_index,
                })
                call_index += 1
        else:
            payload = row.get("payload") if isinstance(row.get("payload"), dict) else {}
            if row.get("type") in {"session_meta", "turn_context"}:
                cwd = str(payload.get("cwd") or cwd)
            if row.get("type") != "response_item" or payload.get("type") not in {"function_call", "custom_tool_call"}:
                continue
            name = str(payload.get("name") or "")
            args = arguments(payload.get("arguments", payload.get("input")))
            events.append({
                "kind": "tool", "name": name, "args": args,
                "id": str(payload.get("call_id") or payload.get("id") or f"{record_index}:0"),
                "cwd": str(args.get("workdir") or cwd), "atom": atom_for(name, args),
                "ts": stamp, "record": record_index, "call": 0,
            })
    return events


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
    try:
        lexer = shlex.shlex(command, posix=True, punctuation_chars=";&|<>")
        lexer.whitespace_split = True
        tokens = list(lexer)
    except ValueError:
        return []
    commands: list[list[str]] = []
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


def plain_operands(tokens: list[str]) -> list[str]:
    values: list[str] = []
    skip_next = False
    for token in tokens:
        if skip_next:
            skip_next = False
            continue
        if token in {"-n", "--lines", "-c", "--bytes", "-f", "-e"}:
            skip_next = True
        elif token.startswith("-"):
            continue
        else:
            values.append(token)
    return values


def shell_effects(command: str) -> list[tuple[str, str, str | None]]:
    effects: list[tuple[str, str, str | None]] = []
    for tokens in shell_commands(command):
        if not tokens or any(token and set(token) <= {"<", ">"} for token in tokens):
            continue
        name = tokens[0].rsplit("/", 1)[-1].lower()
        if name not in READERS | MUTATORS:
            continue
        values = plain_operands(tokens[1:])
        if name == "sed" and len(values) >= 2:
            values = values[1:]
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
    effects = shell_effects(command) if name in SHELL_TOOLS else []
    if name == "apply_patch" or "*** Begin Patch" in command:
        patch = command or str(args.get("patch") or "")
        for match in PATCH_RE.finditer(patch):
            kind, raw_path = match.groups()
            path = raw_path.strip()
            effects.append((path, {"Add": "create", "Update": "write", "Delete": "delete"}[kind], None))
            if kind == "Update":
                move = MOVE_RE.search(patch, match.end())
                if move:
                    effects.extend([(path, "rename_from", None), (move.group(1).strip(), "rename", path)])
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
    return list(dict.fromkeys(effects))


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
        self.current: dict[str, str] = {}
        self.next_generation: Counter[str] = Counter()
        self.deleted: set[str] = set()
        self.display: dict[str, str] = {}

    def new(self, path: str) -> str:
        identity = f"{path}#{self.next_generation[path]}"
        self.next_generation[path] += 1
        self.display[identity] = path
        return identity

    def resolve(self, path: str, access: str, previous: str | None) -> str:
        if access == "rename" and previous:
            identity = self.current.pop(previous, None) or self.new(previous)
            self.current[path] = identity
            self.display[identity] = path
            self.deleted.discard(path)
            return identity
        if path not in self.current or (path in self.deleted and access in {"create", "write"}):
            self.current[path] = self.new(path)
            self.deleted.discard(path)
        identity = self.current[path]
        if access == "delete":
            self.deleted.add(path)
        self.display[identity] = path
        return identity


def path_id(path: str) -> str:
    key = hashlib.sha256(("rq7-path-salt-" + SEED).encode()).digest()
    return hmac.new(key, path.encode(), hashlib.sha256).hexdigest()[:16]


def recompute_project(private: Path, project: dict[str, Any]) -> tuple[dict[str, str], list[dict[str, Any]]]:
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
        events = events_from_source(source_meta["vendor"], native, str(root))
        first = min((event["ts"] for event in events if event.get("ts") is not None), default=source_meta.get("first_ts_ms") or 0)
        sessions.append({**source_meta, "events": events, "first": first})
    sessions.sort(key=lambda row: (row["first"], row["sha256"]))

    sequences = {row["session_id"]: [event["atom"] for event in row["events"]] for row in sessions}
    ordered = []
    for ordinal, session in enumerate(sessions):
        for event in session["events"]:
            ordered.append((
                event["ts"] if event.get("ts") is not None else session["first"],
                session["sha256"], event["record"], event["call"], ordinal, session, event,
            ))
    ordered.sort(key=lambda row: row[:4])
    identities = Identities()
    edges = []
    pending: dict[tuple[str, str], str] = {}
    for event_ordinal, (_, _, _, _, session_ordinal, session, event) in enumerate(ordered):
        for raw_path, access, old_raw in event_effects(event):
            normalized = repo_path(raw_path, str(event.get("cwd") or root), root)
            if normalized is None:
                continue
            previous = repo_path(old_raw, str(event.get("cwd") or root), root) if old_raw else None
            key = (session["session_id"], str(event["id"]))
            if access == "rename_from":
                pending[key] = normalized
            elif access == "rename" and previous is None:
                previous = pending.get(key)
            identity = identities.resolve(normalized, access, previous)
            edges.append({
                "session_id": session["session_id"],
                "session_ordinal": session_ordinal,
                "call_id": str(event["id"]),
                "event_ordinal": event_ordinal,
                "artifact_id": identity,
                "path": normalized,
                "access": access,
                "action_class": "read" if access == "read" else "mutate",
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
    return answers, edges


def main() -> int:
    if len(sys.argv) != 3:
        raise SystemExit("usage: rq7_source_oracle_check.py FREEZE_JSON OUTPUT_JSON")
    freeze_path = Path(sys.argv[1]).resolve()
    output_path = Path(sys.argv[2]).resolve()
    freeze = json.loads(freeze_path.read_text())
    private = freeze_path.parent
    recomputed: dict[str, str] = {}
    edge_count = 0
    all_edges: list[dict[str, Any]] = []
    for project in freeze["projects"]:
        answers, edges = recompute_project(private, project)
        edge_count += len(edges)
        all_edges.extend(edges)
        for template, answer in answers.items():
            recomputed[f"{project['project']}-{template}"] = answer
    expected = {row["id"]: row["answer"] for row in freeze["questions"]}
    if set(recomputed) != set(expected):
        raise RuntimeError("question ID set mismatch")
    mismatches = {
        key: {"expected": expected[key], "actual": recomputed[key]}
        for key in expected
        if expected[key] != recomputed[key]
    }
    if mismatches:
        raise RuntimeError(f"source-direct answer mismatch: {json.dumps(mismatches, sort_keys=True)}")
    invalid_paths = [
        edge["path"] for edge in all_edges if any(char in edge["path"] for char in "<>")
    ]
    if invalid_paths:
        raise RuntimeError(f"redirection-like artifact survived: {invalid_paths[:5]}")
    answer_lines = "\n".join(f"{key}\t{recomputed[key]}" for key in sorted(recomputed)) + "\n"
    result = {
        "status": "pass",
        "questions": len(recomputed),
        "projects": len(freeze["projects"]),
        "artifact_edges": edge_count,
        "answers_sha256": digest_bytes(answer_lines.encode()),
        "checker_sha256": digest_file(Path(__file__)),
        "source_direct": True,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
