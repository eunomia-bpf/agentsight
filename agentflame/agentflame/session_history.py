from __future__ import annotations

from pathlib import Path
from typing import Any

from .models import LlmEvent, SessionRecord, ToolEvent, UserRequest
from .util import (
    basename_from_command,
    clean_space,
    command_effect,
    content_to_text,
    extract_domains,
    extract_paths_from_command,
    line_json,
    one_word,
    parse_tool_args,
    parse_ts_ms,
    path_group,
    short_hash,
)

DEFAULT_CODEX_ROOT = Path.home() / ".codex" / "sessions"


def default_claude_root(project_root: Path) -> Path:
    encoded = str(project_root.resolve()).replace("/", "-")
    return Path.home() / ".claude" / "projects" / encoded


def tool_category(name: str, command: str = "") -> str:
    n = (name or "").lower()
    if n.endswith("exec_command") or n == "bash":
        return "shell"
    if n in {"apply_patch", "edit", "write", "multiedit", "notebookedit"}:
        return "edit"
    if n in {"read", "grep", "glob", "ls"}:
        return "read"
    if "web" in n or "browser" in n or "search" in n or "http" in command:
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
) -> list[ToolEvent]:
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
        command = clean_space(str(args), 300)

    path_groups: list[str] = []
    if name == "apply_patch" or "*** " in command:
        import re

        for match in re.finditer(r"\*\*\* (?:Add|Update|Delete) File: ([^\n]+)", command):
            path_groups.append(path_group(match.group(1), project_root))
        effect = "write"
    elif name.lower() in {"write", "edit", "multiedit", "notebookedit"}:
        for key in ("file_path", "path"):
            if args.get(key):
                path_groups.append(path_group(str(args[key]), project_root))
        effect = "write"
    elif name.lower() == "read":
        for key in ("file_path", "path"):
            if args.get(key):
                path_groups.append(path_group(str(args[key]), project_root))
        effect = "read"
    else:
        effect = command_effect(command)
        path_groups.extend(extract_paths_from_command(command, project_root))

    domains = extract_domains(command)
    category = tool_category(name, command)
    command_name = basename_from_command(command) if category == "shell" else one_word(name, "tool")
    if category == "network" and domains:
        command_name = domains[0].split(":", 1)[0]

    event = ToolEvent(
        ts_ms=ts_ms,
        request_index=request_index,
        tool_name=name,
        category=category,
        command=command,
        command_name=command_name,
        effect=effect,
        status="observed",
        path_groups=sorted(set(path_groups)),
        domains=sorted(set(domains)),
        call_id=call_id,
        source_id=source_id,
    )
    session.tools.append(event)
    return [event]


def update_tool_status(events: list[ToolEvent], output: str) -> None:
    lowered = (output or "").lower()
    if "process exited with code 0" in lowered or '"is_error":false' in lowered:
        status = "ok"
    elif "process exited with code" in lowered or '"is_error":true' in lowered or "error" in lowered:
        status = "fail"
    else:
        status = "observed"
    for event in events:
        event.status = status


def add_codex_function_call(
    session: SessionRecord,
    project_root: Path,
    ts_ms: int | None,
    request_index: int,
    payload: dict[str, Any],
    pending: dict[str, list[ToolEvent]],
) -> None:
    name = str(payload.get("name") or payload.get("tool_name") or "tool")
    call_id = payload.get("call_id")
    args = parse_tool_args(payload.get("arguments"))
    if name == "multi_tool_use.parallel":
        uses = args.get("tool_uses", [])
        events: list[ToolEvent] = []
        if isinstance(uses, list):
            for idx, use in enumerate(uses):
                if not isinstance(use, dict):
                    continue
                child_name = str(use.get("recipient_name") or use.get("name") or "tool")
                child_args = parse_tool_args(use.get("parameters"))
                events.extend(
                    add_tool_event(
                        session,
                        project_root,
                        ts_ms,
                        request_index,
                        child_name.split(".")[-1],
                        child_args,
                        call_id=str(call_id) if call_id else None,
                        source_id=f"{call_id}:{idx}" if call_id else "",
                    )
                )
        if call_id and events:
            pending[str(call_id)] = events
        return
    events = add_tool_event(
        session,
        project_root,
        ts_ms,
        request_index,
        name,
        args,
        call_id=str(call_id) if call_id else None,
        source_id=str(call_id or ""),
    )
    if call_id:
        pending[str(call_id)] = events


def parse_codex_session(path: Path, project_root: Path) -> SessionRecord | None:
    session = SessionRecord(source="codex", path=path, session_id=path.stem)
    current_request = -1
    pending: dict[str, list[ToolEvent]] = {}
    saw_project = False
    for _, data in line_json(path):
        ts_ms = parse_ts_ms(data.get("timestamp"))
        dtype = data.get("type")
        payload = data.get("payload") if isinstance(data.get("payload"), dict) else {}
        if dtype == "session_meta":
            meta = payload
            session.session_id = str(meta.get("id") or session.session_id)
            session.cwd = str(meta.get("cwd") or session.cwd)
            session.start_ts_ms = parse_ts_ms(meta.get("timestamp")) or ts_ms or session.start_ts_ms
            session.model = str(meta.get("model") or meta.get("model_provider") or session.model)
            source = meta.get("source")
            if isinstance(source, dict) and "subagent" in source:
                session.source = "codex-subagent"
                session.agent_role = str(meta.get("agent_role") or "subagent")
            else:
                session.agent_role = str(meta.get("agent_role") or "agent")
            if str(project_root) in session.cwd:
                saw_project = True
        elif dtype == "turn_context":
            session.cwd = str(payload.get("cwd") or session.cwd)
            session.model = str(payload.get("model") or session.model)
            if str(project_root) in session.cwd:
                saw_project = True
        elif dtype == "event_msg":
            if payload.get("type") == "user_message":
                text = str(payload.get("message") or "")
                if text.strip():
                    current_request = len(session.user_requests)
                    session.user_requests.append(
                        UserRequest(index=current_request, ts_ms=ts_ms, text_hash=short_hash(text), preview=clean_space(text, 180))
                    )
            elif payload.get("type") in {"token_count", "token_usage"}:
                usage = payload.get("usage") if isinstance(payload.get("usage"), dict) else payload
                total = int(usage.get("total_tokens") or usage.get("tokens") or 0)
                if total:
                    session.llm_calls.append(
                        LlmEvent(
                            ts_ms=ts_ms,
                            request_index=session.ensure_prompt(ts_ms),
                            model=session.model or "codex",
                            text_hash=short_hash(str(usage)),
                            preview="codex token report",
                            estimated_tokens=total,
                        )
                    )
        elif dtype == "response_item":
            ptype = payload.get("type")
            if ptype == "function_call":
                add_codex_function_call(
                    session,
                    project_root,
                    ts_ms,
                    session.ensure_prompt(ts_ms) if current_request < 0 else current_request,
                    payload,
                    pending,
                )
            elif ptype == "function_call_output":
                call_id = str(payload.get("call_id") or "")
                if call_id in pending:
                    update_tool_status(pending[call_id], str(payload.get("output") or ""))
            elif ptype == "message" and payload.get("role") == "assistant":
                text = content_to_text(payload.get("content"))
                if text.strip():
                    session.llm_calls.append(
                        LlmEvent(
                            ts_ms=ts_ms,
                            request_index=session.ensure_prompt(ts_ms),
                            model=session.model or "codex",
                            text_hash=short_hash(text),
                            preview=clean_space(text, 140),
                            estimated_tokens=max(1, len(text) // 4),
                        )
                    )
    if not saw_project and str(project_root) not in session.cwd:
        return None
    if not session.user_requests and not session.tools and not session.llm_calls:
        return None
    session.ensure_prompt(session.start_ts_ms)
    return session


def parse_claude_session(path: Path, project_root: Path) -> SessionRecord | None:
    source = "claude-subagent" if "subagents" in path.parts else "claude"
    session = SessionRecord(source=source, path=path, session_id=path.stem)
    current_request = -1
    pending: dict[str, ToolEvent] = {}
    saw_project = str(project_root) in str(path)
    for _, data in line_json(path):
        ts_ms = parse_ts_ms(data.get("timestamp"))
        dtype = data.get("type")
        cwd = str(data.get("cwd") or "")
        if cwd:
            session.cwd = cwd
            if str(project_root) in cwd:
                saw_project = True
        if data.get("sessionId"):
            session.session_id = str(data.get("sessionId"))
        if data.get("aiTitle"):
            session.title = str(data.get("aiTitle") or "")
        if dtype == "user":
            message = data.get("message") if isinstance(data.get("message"), dict) else {}
            content = message.get("content")
            if isinstance(content, list) and any(isinstance(item, dict) and item.get("type") == "tool_result" for item in content):
                result = data.get("toolUseResult") if isinstance(data.get("toolUseResult"), dict) else {}
                for item in content:
                    if isinstance(item, dict) and item.get("type") == "tool_result":
                        tool_id = str(item.get("tool_use_id") or "")
                        if tool_id and tool_id in pending:
                            pending[tool_id].status = "fail" if item.get("is_error") or result.get("is_error") else "ok"
                continue
            text = content_to_text(content)
            if text.strip():
                current_request = len(session.user_requests)
                session.user_requests.append(
                    UserRequest(index=current_request, ts_ms=ts_ms, text_hash=short_hash(text), preview=clean_space(text, 180))
                )
        elif dtype == "assistant":
            message = data.get("message") if isinstance(data.get("message"), dict) else {}
            session.model = str(message.get("model") or session.model)
            content = message.get("content")
            text = content_to_text(content)
            usage = message.get("usage") if isinstance(message.get("usage"), dict) else {}
            input_tokens = int(usage.get("input_tokens") or 0)
            output_tokens = int(usage.get("output_tokens") or 0)
            cache_tokens = int(usage.get("cache_creation_input_tokens") or 0) + int(usage.get("cache_read_input_tokens") or 0)
            if text.strip() or input_tokens or output_tokens or cache_tokens:
                session.llm_calls.append(
                    LlmEvent(
                        ts_ms=ts_ms,
                        request_index=session.ensure_prompt(ts_ms) if current_request < 0 else current_request,
                        model=session.model or "claude",
                        text_hash=short_hash(text or str(usage)),
                        preview=clean_space(text or "claude response", 140),
                        input_tokens=input_tokens,
                        output_tokens=output_tokens,
                        cache_tokens=cache_tokens,
                    )
                )
            if isinstance(content, list):
                for idx, item in enumerate(content):
                    if not isinstance(item, dict) or item.get("type") != "tool_use":
                        continue
                    events = add_tool_event(
                        session,
                        project_root,
                        ts_ms,
                        session.ensure_prompt(ts_ms) if current_request < 0 else current_request,
                        str(item.get("name") or "tool"),
                        parse_tool_args(item.get("input")),
                        call_id=str(item.get("id") or ""),
                        source_id=f"{path.stem}:{idx}",
                    )
                    if item.get("id") and events:
                        pending[str(item["id"])] = events[0]
        elif dtype == "last-prompt" and data.get("lastPrompt") and not session.user_requests:
            text = str(data.get("lastPrompt") or "")
            current_request = len(session.user_requests)
            session.user_requests.append(
                UserRequest(index=current_request, ts_ms=ts_ms, text_hash=short_hash(text), preview=clean_space(text, 180))
            )
    if not saw_project:
        return None
    if not session.user_requests and not session.tools and not session.llm_calls:
        return None
    session.ensure_prompt(session.start_ts_ms)
    return session


def find_session_files(root: Path, max_files: int | None = None) -> list[Path]:
    if not root.exists():
        return []
    files = sorted(root.rglob("*.jsonl"), key=lambda p: p.stat().st_mtime, reverse=True)
    if max_files is not None and max_files > 0:
        return files[:max_files]
    return files


def discover_sessions(
    project_root: Path,
    codex_root: Path | None = None,
    claude_root: Path | None = None,
    scan_files: int = 160,
    max_sessions: int = 36,
) -> tuple[list[SessionRecord], list[str]]:
    project_root = project_root.resolve()
    codex_root = codex_root or DEFAULT_CODEX_ROOT
    claude_root = claude_root or default_claude_root(project_root)
    warnings: list[str] = []
    sessions: list[SessionRecord] = []
    for path in find_session_files(codex_root, scan_files):
        try:
            record = parse_codex_session(path, project_root)
            if record:
                sessions.append(record)
        except Exception as exc:
            warnings.append(f"codex parse skipped {path}: {type(exc).__name__}: {exc}")
    for path in find_session_files(claude_root, scan_files):
        try:
            record = parse_claude_session(path, project_root)
            if record:
                sessions.append(record)
        except Exception as exc:
            warnings.append(f"claude parse skipped {path}: {type(exc).__name__}: {exc}")
    sessions.sort(key=lambda s: s.start_ts_ms or s.path.stat().st_mtime_ns // 1_000_000, reverse=True)
    if max_sessions and max_sessions > 0:
        sessions = sessions[:max_sessions]
    return sessions, warnings
