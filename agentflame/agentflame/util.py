from __future__ import annotations

import datetime as dt
import hashlib
import json
import re
import shlex
from pathlib import Path
from typing import Any, Iterable


def now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def parse_ts_ms(value: Any) -> int | None:
    if not value:
        return None
    if isinstance(value, (int, float)):
        if value > 10_000_000_000:
            return int(value)
        return int(value * 1000)
    if not isinstance(value, str):
        return None
    text = value.strip()
    if not text:
        return None
    try:
        if text.endswith("Z"):
            text = text[:-1] + "+00:00"
        return int(dt.datetime.fromisoformat(text).timestamp() * 1000)
    except ValueError:
        return None


def short_hash(text: str, n: int = 12) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="ignore")).hexdigest()[:n]


def short_session_id(session_id: str) -> str:
    compact = (session_id or "").strip().rsplit("/", 1)[-1].removesuffix(".jsonl")
    if not compact:
        return "session"
    if len(compact) <= 12:
        return compact
    return f"{compact[:6]}.{compact[-5:]}"


def agent_family(source: str) -> str:
    source = (source or "").lower()
    if source.startswith("codex"):
        return "codex"
    if source.startswith("claude"):
        return "claude"
    return source or "agent"


def agent_sight_session_id(source: str, session_id: str) -> str:
    family = agent_family(source)
    return f"local:{family}:{family}:{short_session_id(session_id)}"


def clean_space(text: str, limit: int = 500) -> str:
    text = re.sub(r"\s+", " ", text or "").strip()
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "."


def safe_frame(text: str, prefix: str | None = None) -> str:
    text = (text or "unknown").lower()
    text = re.sub(r"[^a-z0-9._:/+-]+", "_", text)
    text = text.strip("_;") or "unknown"
    if prefix:
        return f"{prefix}:{text}"
    return text


def one_word(text: str, default: str = "tool") -> str:
    match = re.search(r"[a-z][a-z0-9]{1,15}", (text or "").lower())
    return match.group(0) if match else default


def basename_from_command(command: str) -> str:
    if not command:
        return "none"
    try:
        parts = shlex.split(command, posix=True)
    except ValueError:
        parts = command.split()
    if not parts:
        return "none"
    first = parts[0]
    if first in {"sudo", "env", "command", "time", "timeout", "nice", "nohup"} and len(parts) > 1:
        first = parts[1]
    return Path(first).name or first


def command_effect(command: str) -> str:
    cmd = basename_from_command(command)
    text = command.lower()
    read_cmds = {"rg", "grep", "sed", "cat", "head", "tail", "find", "ls", "nl", "wc", "jq", "git"}
    write_cmds = {"tee", "cp", "mv", "rm", "mkdir", "touch", "python", "python3", "node", "npm", "cargo"}
    net_cmds = {"curl", "wget", "ssh", "scp", "git"}
    if cmd in {"cargo", "pytest", "npm", "pnpm", "yarn", "go", "make"} and re.search(r"\b(test|check|build|clippy)\b", text):
        return "test"
    if cmd == "git" and re.search(r"\b(commit|push|add|checkout|merge|rebase)\b", text):
        return "repo"
    if cmd in net_cmds and re.search(r"\b(clone|fetch|pull|push|curl|wget|ssh|https?://)\b", text):
        return "network"
    if cmd in write_cmds and re.search(r">\s*|--write|--fix|-w\b|rm\s|mkdir\s|touch\s|cp\s|mv\s", text):
        return "write"
    if cmd in read_cmds:
        return "read"
    if re.search(r"https?://|crates\.io|github\.com|huggingface\.co|hf\.co", text):
        return "network"
    return "process"


def redact_path_segment(segment: str) -> str:
    if re.fullmatch(r"[0-9a-f]{8,}(-[0-9a-f]{4,})*", segment.lower()):
        return "session"
    if len(segment) > 48:
        return segment[:45] + "..."
    return segment


def path_group(path: str, project_root: Path) -> str:
    if not path:
        return "none"
    path = path.strip("'\"")
    try:
        p = Path(path)
        if p.is_absolute():
            try:
                rel = p.resolve().relative_to(project_root.resolve())
                parts = rel.parts
            except Exception:
                parts = p.parts[-3:]
        else:
            parts = p.parts
    except Exception:
        parts = tuple(path.split("/"))
    parts = [redact_path_segment(part) for part in parts if part not in {"", "."}]
    if not parts:
        return "repo"
    if parts[0] in {"collector", "frontend", "docs", "bpf", "agentflame"}:
        return "/".join(parts[:3])
    group = "/".join(parts[:2])
    if len(group) > 80:
        return "complex"
    return group


def plausible_path_token(part: str) -> bool:
    part = part.strip("'\"")
    if not part or part.startswith("-") or part.startswith("$"):
        return False
    if part.startswith(("http://", "https://")):
        return False
    if len(part) > 140 or re.search(r"[{}()=;<>|`]", part) or re.search(r"\s", part):
        return False
    suffix = Path(part).suffix.lower()
    return "/" in part or suffix in {".rs", ".py", ".md", ".json", ".ts", ".tsx", ".toml", ".lock", ".js", ".c", ".h", ".svg", ".html", ".css"}


def extract_paths_from_command(command: str, project_root: Path) -> list[str]:
    if not command:
        return []
    try:
        parts = shlex.split(command, posix=True)
    except ValueError:
        parts = command.split()
    paths = []
    for part in parts:
        if plausible_path_token(part):
            group = path_group(part, project_root)
            if group and group != "none":
                paths.append(group)
    return sorted(set(paths))[:8]


def extract_domains(text: str) -> list[str]:
    domains = re.findall(r"https?://([^/\s)\"']+)", text or "")
    bare = re.findall(r"\b((?:github|crates|huggingface|hf|openai|anthropic)\.[a-z.]+)\b", text or "")
    return sorted(set(d.lower() for d in domains + bare))[:8]


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


def content_to_text(content: Any) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        pieces = []
        for item in content:
            if isinstance(item, str):
                pieces.append(item)
            elif isinstance(item, dict):
                if item.get("type") in {"text", "input_text", "output_text"}:
                    pieces.append(str(item.get("text", "")))
                elif item.get("type") == "tool_result":
                    continue
                elif "text" in item:
                    pieces.append(str(item.get("text", "")))
        return "\n".join(p for p in pieces if p)
    if isinstance(content, dict):
        return str(content.get("text", ""))
    return ""


def parse_tool_args(arguments: Any) -> dict[str, Any]:
    if isinstance(arguments, dict):
        return arguments
    if isinstance(arguments, str):
        try:
            value = json.loads(arguments)
            if isinstance(value, dict):
                return value
        except json.JSONDecodeError:
            return {"text": arguments}
    return {}
