from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Iterable

from .model import LlmEvent, SessionRecord, ToolEvent, UserRequest
from .tagger import SimpleTagger
from .util import (
    basename_from_command,
    clean_space,
    command_effect,
    content_to_text,
    extract_domains,
    extract_paths_from_command,
    parse_tool_args,
    parse_ts_ms,
    path_group,
    short_hash,
)


def line_json(path: Path) -> Iterable[tuple[int, dict[str, Any]]]:
    try:
        with path.open("r", encoding="utf-8", errors="replace") as handle:
            for lineno, line in enumerate(handle, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if isinstance(data, dict):
                    yield lineno, data
    except OSError:
        return


def source_from_path(path: Path) -> str | None:
    text = str(path)
    if "/.codex/" in text:
        return "codex"
    if "/.claude/" in text:
        return "claude"
    if path.name.startswith("rollout-"):
        return "codex"
    return None


def default_claude_root(project_root: Path) -> Path:
    encoded = str(project_root.resolve()).replace("/", "-")
    return Path.home() / ".claude" / "projects" / encoded


def find_jsonl(root: Path, limit: int) -> list[Path]:
    if not root.exists():
        return []
    files = [path for path in root.rglob("*.jsonl") if path.is_file()]
    files.sort(key=lambda path: path.stat().st_mtime if path.exists() else 0, reverse=True)
    return files[:limit]


def raw_mentions_project(path: Path, project_root: Path) -> bool:
    needle_abs = str(project_root.resolve())
    needle_name = project_root.resolve().name
    try:
        with path.open("r", encoding="utf-8", errors="replace") as handle:
            head = handle.read(400_000)
    except OSError:
        return False
    return needle_abs in head or f"/{needle_name}" in head or needle_name in head[:20_000]


def discover_sessions(
    project_root: Path,
    codex_root: Path | None = None,
    claude_root: Path | None = None,
    session_files: list[Path] | None = None,
    scan_files: int = 160,
    max_sessions: int = 36,
) -> tuple[list[SessionRecord], list[str]]:
    project_root = project_root.resolve()
    codex_root = codex_root or (Path.home() / ".codex" / "sessions")
    claude_root = claude_root or default_claude_root(project_root)
    explicit = bool(session_files)
    candidates = list(session_files or [])
    if not candidates:
        candidates.extend(find_jsonl(claude_root, scan_files))
        candidates.extend(find_jsonl(codex_root, scan_files))
        candidates.sort(key=lambda path: path.stat().st_mtime if path.exists() else 0, reverse=True)
    sessions: list[SessionRecord] = []
    warnings: list[str] = []
    for path in candidates[:scan_files]:
        source = source_from_path(path)
        if not source:
            continue
        if not explicit and source == "codex" and not raw_mentions_project(path, project_root):
            continue
        try:
            session = parse_codex_session(path, project_root) if source == "codex" else parse_claude_session(path, project_root)
        except Exception as exc:  # pragma: no cover - defensive for evolving vendor logs.
            warnings.append(f"skip {path}: {type(exc).__name__}: {exc}")
            continue
        if not session:
            continue
        session.ensure_prompt(session.start_ts_ms)
        if session.user_requests or session.tools or session.llm_calls:
            sessions.append(session)
        if len(sessions) >= max_sessions:
            break
    return sessions, warnings


def tool_category(name: str, command: str = "") -> str:
    n = (name or "").lower()
    if n.endswith("exec_command") or n in {"bash", "shell"}:
        return "shell"
    if n in {"apply_patch", "edit", "write", "multiedit", "notebookedit"}:
        return "edit"
    if n in {"read", "grep", "glob", "ls"}:
        return "read"
    if "web" in n or re.search(r"https?://", command):
        return "network"
    if "plan" in n or "todo" in n:
        return "plan"
    if "task" in n or "agent" in n:
        return "subagent"
    return "tool"


def add_tool_event(
    session: SessionRecord,
    project_root: Path,
    ts_ms: int | None,
    request_index: int,
    name: str,
    args: dict[str, Any],
    call_id: str | None = None,
    source_id: str = "",
) -> None:
    command = ""
    path_groups: list[str] = []
    domains: list[str] = []
    if "cmd" in args:
        command = str(args.get("cmd") or "")
    elif "command" in args:
        command = str(args.get("command") or "")
    elif "pattern" in args:
        command = f"search {args.get('pattern')}"
    elif "file_path" in args:
        command = str(args.get("file_path") or "")
    elif "path" in args:
        command = str(args.get("path") or "")
    elif "text" in args:
        command = clean_space(str(args.get("text") or ""), 300)
    else:
        command = clean_space(json.dumps(args, sort_keys=True, ensure_ascii=False), 300)

    lname = name.lower()
    if lname == "apply_patch" or "*** " in command:
        for match in re.finditer(r"\*\*\* (?:Add|Update|Delete) File: ([^\n]+)", command):
            path_groups.append(path_group(match.group(1), project_root))
        effect = "write"
    elif lname in {"write", "edit", "multiedit", "notebookedit"}:
        for key in ("file_path", "path"):
            if args.get(key):
                path_groups.append(path_group(str(args[key]), project_root))
        effect = "write"
    elif lname == "read":
        for key in ("file_path", "path"):
            if args.get(key):
                path_groups.append(path_group(str(args[key]), project_root))
        effect = "read"
    else:
        effect = command_effect(command)
        path_groups.extend(extract_paths_from_command(command, project_root))
    domains.extend(extract_domains(command))
    category = tool_category(name, command)
    command_name = basename_from_command(command) if category == "shell" else re.sub(r"[^a-z0-9]+", "_", lname).strip("_")
    session.tools.append(
        ToolEvent(
            ts_ms=ts_ms,
            request_index=request_index,
            tool_name=name,
            category=category,
            command=command,
            command_name=command_name or "tool",
            effect=effect,
            status="observed",
            path_groups=sorted(set(path_groups))[:8],
            domains=sorted(set(domains))[:8],
            call_id=call_id,
            source_id=source_id,
        )
    )


def parse_codex_session(path: Path, project_root: Path) -> SessionRecord | None:
    session = SessionRecord(source="codex", path=path, session_id=path.stem)
    current_prompt = 0
    saw_relevant = False
    last_agent_text = ""
    for lineno, row in line_json(path):
        ts_ms = parse_ts_ms(row.get("timestamp"))
        payload = row.get("payload") if isinstance(row.get("payload"), dict) else {}
        kind = row.get("type")
        ptype = payload.get("type")
        if kind == "session_meta":
            meta = payload
            session.session_id = str(meta.get("id") or session.session_id)
            session.cwd = str(meta.get("cwd") or session.cwd)
            session.model = str(meta.get("model") or meta.get("model_provider") or session.model)
            session.start_ts_ms = parse_ts_ms(meta.get("timestamp")) or ts_ms or session.start_ts_ms
            if session.cwd and (project_root.name in session.cwd or str(project_root) in session.cwd):
                saw_relevant = True
        elif kind == "turn_context":
            session.cwd = str(payload.get("cwd") or session.cwd)
            session.model = str(payload.get("model") or session.model)
            if session.cwd and project_root.name in session.cwd:
                saw_relevant = True
        elif kind == "event_msg" and ptype == "user_message":
            text = clean_space(str(payload.get("message") or ""), 900)
            if text and not text.startswith("<environment_context>"):
                current_prompt = len(session.user_requests)
                session.user_requests.append(UserRequest(current_prompt, ts_ms, short_hash(text), text))
                saw_relevant = True
        elif kind == "event_msg" and ptype == "agent_message":
            last_agent_text = clean_space(str(payload.get("message") or ""), 900)
        elif kind == "event_msg" and ptype == "token_count":
            info = payload.get("info") if isinstance(payload.get("info"), dict) else {}
            usage = info.get("last_token_usage") if isinstance(info.get("last_token_usage"), dict) else {}
            if usage:
                session.llm_calls.append(
                    LlmEvent(
                        ts_ms=ts_ms,
                        request_index=current_prompt,
                        model=session.model or "codex",
                        text_hash=short_hash(last_agent_text or json.dumps(usage, sort_keys=True)),
                        preview=last_agent_text,
                        input_tokens=int(usage.get("input_tokens") or 0),
                        output_tokens=int(usage.get("output_tokens") or 0),
                        cache_tokens=int(usage.get("cached_input_tokens") or 0),
                    )
                )
        elif kind == "response_item" and ptype == "function_call":
            add_tool_event(
                session,
                project_root,
                ts_ms,
                current_prompt,
                str(payload.get("name") or "tool"),
                parse_tool_args(payload.get("arguments")),
                call_id=payload.get("call_id"),
                source_id=f"{path.name}:{lineno}",
            )
            saw_relevant = True
        elif kind == "response_item" and ptype == "message" and payload.get("role") == "assistant":
            text = content_to_text(payload.get("content"))
            if text:
                last_agent_text = clean_space(text, 900)
    if not saw_relevant and not raw_mentions_project(path, project_root):
        return None
    return session


def parse_claude_session(path: Path, project_root: Path) -> SessionRecord | None:
    session = SessionRecord(source="claude", path=path, session_id=path.stem)
    current_prompt = 0
    saw_relevant = False
    for lineno, row in line_json(path):
        ts_ms = parse_ts_ms(row.get("timestamp"))
        rtype = row.get("type")
        if row.get("sessionId"):
            session.session_id = str(row.get("sessionId"))
        if row.get("cwd"):
            session.cwd = str(row.get("cwd"))
            if project_root.name in session.cwd or str(project_root) in session.cwd:
                saw_relevant = True
        if rtype == "ai-title":
            session.title = str(row.get("aiTitle") or "")
            continue
        message = row.get("message") if isinstance(row.get("message"), dict) else {}
        role = message.get("role")
        if rtype == "user" and role == "user" and not row.get("isMeta"):
            text = clean_space(content_to_text(message.get("content")), 900)
            if not text or text.startswith(("<local-command", "<command-name>")):
                continue
            current_prompt = len(session.user_requests)
            session.user_requests.append(UserRequest(current_prompt, ts_ms, short_hash(text), text))
            saw_relevant = True
        elif role == "assistant":
            model = str(message.get("model") or session.model or "claude")
            session.model = model
            usage = message.get("usage") if isinstance(message.get("usage"), dict) else {}
            text_parts: list[str] = []
            for block in message.get("content") or []:
                if not isinstance(block, dict):
                    continue
                if block.get("type") == "text":
                    text_parts.append(str(block.get("text") or ""))
                elif block.get("type") == "tool_use":
                    add_tool_event(
                        session,
                        project_root,
                        ts_ms,
                        current_prompt,
                        str(block.get("name") or "tool"),
                        parse_tool_args(block.get("input")),
                        call_id=block.get("id"),
                        source_id=f"{path.name}:{lineno}",
                    )
                    saw_relevant = True
            text = clean_space("\n".join(text_parts), 900)
            if usage or text:
                session.llm_calls.append(
                    LlmEvent(
                        ts_ms=ts_ms,
                        request_index=current_prompt,
                        model=model,
                        text_hash=short_hash(text or json.dumps(usage, sort_keys=True)),
                        preview=text,
                        input_tokens=int(usage.get("input_tokens") or 0),
                        output_tokens=int(usage.get("output_tokens") or 0),
                        cache_tokens=int(usage.get("cache_read_input_tokens") or 0)
                        + int(usage.get("cache_creation_input_tokens") or 0),
                    )
                )
    if not saw_relevant and not raw_mentions_project(path, project_root):
        return None
    return session


def annotate_sessions(sessions: list[SessionRecord], tagger: SimpleTagger | None = None) -> None:
    tagger = tagger or SimpleTagger()
    for session in sessions:
        prompt_text = " ".join(req.preview for req in session.user_requests[:4])
        session.session_tag = tagger.tag("session", f"{session.title} {prompt_text}", [session.source])
        for request in session.user_requests:
            request.tag = tagger.tag("prompt", request.preview)
        for call in session.llm_calls:
            call.tag = tagger.tag("llm", call.preview, [call.model])
        for tool in session.tools:
            if tool.effect in {"read", "write", "test", "network", "repo"}:
                tool.tag = tool.effect
            else:
                tool.tag = tagger.tag("tool", f"{tool.tool_name} {tool.command}", [tool.category])
