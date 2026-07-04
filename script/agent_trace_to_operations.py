#!/usr/bin/env python3
"""Convert portable agent-session traces into AgentSight operation JSONL."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Iterable


TRACE_SCHEMA = "agentsight.agent-session.trace.v1"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Convert agent-session trace JSON to normalized operation JSONL."
    )
    parser.add_argument("--trace-file", action="append", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--project-name", default="agent-session-trace")
    parser.add_argument(
        "--include-previews",
        action="store_true",
        help="Include prompt/LLM previews in operation fields.",
    )
    return parser.parse_args()


def load_sessions(path: Path) -> list[dict[str, Any]]:
    data = json.loads(path.read_text())
    if isinstance(data, dict) and "sessions" in data:
        schema = data.get("schema")
        if schema != TRACE_SCHEMA:
            raise SystemExit(f"unsupported trace schema {schema!r} in {path}")
        sessions = data["sessions"]
    elif isinstance(data, list):
        sessions = data
    elif isinstance(data, dict):
        sessions = [data]
    else:
        raise SystemExit(f"invalid trace JSON in {path}")
    if not all(isinstance(item, dict) for item in sessions):
        raise SystemExit(f"trace sessions must be JSON objects in {path}")
    return sessions


def clean_fields(fields: dict[str, Any]) -> dict[str, Any]:
    return {
        key: value
        for key, value in fields.items()
        if value is not None and value != "" and value != [] and value != {}
    }


def short_hash(value: str, length: int = 12) -> str:
    return hashlib.sha256(value.encode("utf-8", errors="replace")).hexdigest()[:length]


def nonnegative_int(value: Any) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return 0
    return max(parsed, 0)


def tool_category(name: str, command: str = "") -> str:
    lowered = name.lower()
    if lowered.endswith("exec_command") or lowered == "bash":
        return "shell"
    if lowered in {"apply_patch", "edit", "write", "multiedit", "notebookedit"}:
        return "edit"
    if lowered in {"read", "grep", "glob", "ls"}:
        return "read"
    if (
        "web" in lowered
        or "browser" in lowered
        or "search" in lowered
        or "http" in command
    ):
        return "network"
    if "plan" in lowered or "todo" in lowered:
        return "plan"
    if "task" in lowered or "agent" in lowered:
        return "subagent"
    return "tool"


def path_parts(raw: str) -> list[str]:
    normalized = raw.replace("\\", "/")
    return [
        part
        for part in normalized.split("/")
        if part and part != "." and part != "/"
    ]


def truncate_path_component(part: str) -> str:
    return f"{part[:45]}..." if len(part) > 48 else part


def collapse_project_path(parts: list[str]) -> str:
    collapsed = [truncate_path_component(part) for part in parts if part and part != "."]
    if not collapsed:
        return "repo"
    if collapsed[0] in {
        "collector",
        "frontend",
        "docs",
        "bpf",
        "agentpprof",
        "agent-session",
    }:
        return "/".join(collapsed[:3])
    return "/".join(collapsed[:2])


def sensitive_path_group(raw: str, parts: list[str]) -> str | None:
    lowered = raw.lower()
    lower_parts = [part.lower() for part in parts]
    if ".codex" in lower_parts:
        return "external/codex"
    if ".claude" in lower_parts:
        return "external/claude"
    if (
        (lower_parts and lower_parts[0] == "tmp")
        or "/tmp" in lowered
        or "_/tmp" in lowered
        or any(left == "var" and right == "tmp" for left, right in zip(lower_parts, lower_parts[1:]))
    ):
        return "external/tmp"
    if (
        lowered.startswith("~/")
        or lowered == "~"
        or "/home" in lowered
        or "_/home" in lowered
        or "-home-" in lowered
        or "/users" in lowered
        or "_/users" in lowered
        or (lower_parts and lower_parts[0] in {"home", "users"})
        or "private" in lowered
        or "secret" in lowered
    ):
        return "external/home"
    return None


def path_group(raw: str, cwd: str = "") -> str:
    path = raw.strip().strip("\"'")
    if not path:
        return "none"
    cwd = cwd.rstrip("/")
    if cwd and path == cwd:
        return "repo"
    if cwd and path.startswith(f"{cwd}/"):
        return collapse_project_path(path_parts(path[len(cwd) :].lstrip("/")))
    parts = path_parts(path)
    sensitive = sensitive_path_group(path, parts)
    if sensitive:
        return sensitive
    if path.startswith("/"):
        return "external/path"
    return collapse_project_path(parts)


def fallback_path_groups(session: dict[str, Any]) -> list[str]:
    files = session.get("files", {})
    if not isinstance(files, dict):
        return []
    cwd = str(session.get("cwd") or "")
    groups = {
        path_group(path, cwd)
        for path in files.keys()
        if isinstance(path, str)
    }
    return sorted(group for group in groups if group != "none")


def prompt_rows_for_session(session: dict[str, Any]) -> list[dict[str, Any]]:
    prompts = session.get("events", {}).get("prompts", [])
    rows = [prompt for prompt in prompts if isinstance(prompt, dict)]
    if rows:
        return rows
    prompt_preview = session.get("prompt_preview")
    if isinstance(prompt_preview, str) and prompt_preview:
        return [
            {
                "index": 0,
                "text_hash": short_hash(prompt_preview),
                "tag": "",
                "preview": prompt_preview,
            }
        ]
    return [
        {
            "index": 0,
            "text_hash": "bootstrap",
            "tag": "",
            "preview": "session bootstrap",
        }
    ]


def prompt_by_index(prompts: list[dict[str, Any]], index: int) -> dict[str, Any]:
    if 0 <= index < len(prompts):
        prompt = prompts[index]
        return prompt
    if prompts and isinstance(prompts[-1], dict):
        return prompts[-1]
    return {"index": index, "text_hash": "bootstrap", "tag": ""}


def base_fields(
    session: dict[str, Any],
    prompts: list[dict[str, Any]],
    project_name: str,
    prompt_index: int,
    include_previews: bool,
) -> dict[str, Any]:
    prompt = prompt_by_index(prompts, prompt_index)
    fields: dict[str, Any] = {
        "project": project_name,
        "agent": session.get("agent_type", "agent"),
        "session": session.get("session_id", "unknown"),
        "session_id": session.get("session_id", "unknown"),
        "prompt_index": prompt.get("index", prompt_index),
        "prompt": prompt.get("tag", ""),
        "prompt_hash": prompt.get("text_hash", ""),
    }
    if include_previews:
        fields["prompt_preview"] = prompt.get("preview", "")
    return fields


def tool_phase(event: dict[str, Any]) -> str:
    effect = event.get("effect", "")
    if effect and effect != "process":
        return effect
    category = event.get("category", "")
    if category and category != "tool":
        return category
    command_name = event.get("command_name", "")
    if command_name and command_name != "none":
        return command_name
    return event.get("tool_name", "tool")


def command_preview(event: dict[str, Any]) -> str:
    command_name = event.get("command_name", "")
    if isinstance(command_name, str) and command_name and command_name != "none":
        return command_name
    return ""


def llm_phase(call: dict[str, Any]) -> str:
    tag = call.get("tag", "")
    if tag and tag != "unmatched":
        return tag
    return "llm"


def event_tool_rows(session: dict[str, Any]) -> list[dict[str, Any]]:
    tools = session.get("events", {}).get("tools", [])
    rows = [event for event in tools if isinstance(event, dict)]
    if rows:
        return rows
    tool_counts = session.get("tools", {})
    if not isinstance(tool_counts, dict):
        return []
    paths = fallback_path_groups(session)
    fallback_rows: list[dict[str, Any]] = []
    for tool, count in tool_counts.items():
        if not isinstance(tool, str):
            continue
        for _ in range(nonnegative_int(count)):
            fallback_rows.append(
                {
                    "prompt_index": 0,
                    "tool_name": tool,
                    "category": tool_category(tool),
                    "command": "",
                    "command_name": "none",
                    "effect": "process",
                    "process_chain": [],
                    "status": "observed",
                    "path_groups": paths,
                    "domains": [],
                }
            )
    return fallback_rows


def llm_rows_for_session(session: dict[str, Any]) -> list[dict[str, Any]]:
    llm_responses = session.get("events", {}).get("llm_responses", [])
    rows = [call for call in llm_responses if isinstance(call, dict)]
    if rows:
        return rows
    model_usage = session.get("model_usage", {})
    if not isinstance(model_usage, dict):
        return []
    fallback_rows: list[dict[str, Any]] = []
    session_id = str(session.get("session_id", "unknown"))
    for model, usage in model_usage.items():
        if not isinstance(usage, dict):
            continue
        total_tokens = nonnegative_int(usage.get("total_tokens"))
        if total_tokens <= 0:
            continue
        cache_tokens = nonnegative_int(usage.get("cache_creation_tokens")) + nonnegative_int(
            usage.get("cache_read_tokens")
        )
        fallback_rows.append(
            {
                "prompt_index": 0,
                "model": str(model),
                "text_hash": short_hash(f"{session_id}:{model}:{total_tokens}"),
                "preview": "session token summary",
                "input_tokens": nonnegative_int(usage.get("input_tokens")),
                "output_tokens": nonnegative_int(usage.get("output_tokens")),
                "cache_tokens": cache_tokens,
                "total_tokens": total_tokens,
                "tag": "",
            }
        )
    return fallback_rows


def operations_for_session(
    session: dict[str, Any],
    project_name: str,
    include_previews: bool,
) -> Iterable[dict[str, Any]]:
    for event in operation_events_for_session(session, project_name, include_previews):
        yield event["operation"]


def operation_events_for_session(
    session: dict[str, Any],
    project_name: str,
    include_previews: bool,
) -> Iterable[dict[str, Any]]:
    prompts = prompt_rows_for_session(session)
    tools = event_tool_rows(session)
    llm_responses = llm_rows_for_session(session)

    for idx, prompt in enumerate(prompts):
        fields = base_fields(session, prompts, project_name, idx, include_previews)
        fields.update(
            {
                "op": "prompt",
                "phase": "prompt",
                "status": "observed",
                "prompt_hash": prompt.get("text_hash", fields.get("prompt_hash", "")),
            }
        )
        yield {
            "operation": {"value": 1, "fields": clean_fields(fields)},
            "ts_ms": prompt.get("ts_ms"),
            "event": "prompt",
        }

    for event in tools:
        prompt_index = nonnegative_int(event.get("prompt_index"))
        fields = base_fields(session, prompts, project_name, prompt_index, include_previews)
        fields.update(
            {
                "op": "tool",
                "phase": tool_phase(event),
                "tool": event.get("tool_name", ""),
                "category": event.get("category", ""),
                "command": command_preview(event),
                "cmd": event.get("command_name", ""),
                "effect": event.get("effect", ""),
                "status": event.get("status", "observed"),
                "path": event.get("path_groups", []),
                "domain": event.get("domains", []),
                "process": event.get("process_chain", []),
            }
        )
        yield {
            "operation": {"value": 1, "fields": clean_fields(fields)},
            "ts_ms": event.get("ts_ms"),
            "event": "tool",
        }

    for call in llm_responses:
        prompt_index = nonnegative_int(call.get("prompt_index"))
        tag = call.get("tag", "")
        fields = base_fields(session, prompts, project_name, prompt_index, include_previews)
        fields.update(
            {
                "op": "llm",
                "phase": llm_phase(call),
                "call": f"llm/{tag}",
                "llm": tag,
                "model": str(call.get("model", "")).split("/")[-1],
                "status": "observed",
                "input_tokens": nonnegative_int(call.get("input_tokens")),
                "output_tokens": nonnegative_int(call.get("output_tokens")),
                "cache_tokens": nonnegative_int(call.get("cache_tokens")),
                "total_tokens": nonnegative_int(call.get("total_tokens")),
            }
        )
        if include_previews:
            fields["llm_preview"] = call.get("preview", "")
        yield {
            "operation": {"value": 1, "fields": clean_fields(fields)},
            "ts_ms": call.get("ts_ms"),
            "event": "llm",
        }


def main() -> None:
    args = parse_args()
    operations = []
    for trace_file in args.trace_file:
        for session in load_sessions(trace_file):
            operations.extend(
                operations_for_session(session, args.project_name, args.include_previews)
            )
    if not operations:
        raise SystemExit("trace produced zero operations")

    if args.out.parent and str(args.out.parent) != ".":
        args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w") as out:
        for operation in operations:
            out.write(json.dumps(operation, sort_keys=True) + "\n")

    print(
        json.dumps(
            {
                "status": "ok",
                "trace_files": [str(path) for path in args.trace_file],
                "output": str(args.out),
                "operations": len(operations),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
