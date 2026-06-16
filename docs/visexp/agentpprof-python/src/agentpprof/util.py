from __future__ import annotations

import datetime as dt
import hashlib
import json
import re
import shlex
from pathlib import Path
from typing import Any


def parse_ts_ms(value: Any) -> int | None:
    if value is None or value == "":
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


def clean_space(text: str, limit: int = 500) -> str:
    text = re.sub(r"\s+", " ", text or "").strip()
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "."


def safe_frame(text: str, prefix: str | None = None) -> str:
    text = (text or "unknown").lower()
    text = re.sub(r"[^a-z0-9._:/+-]+", "_", text)
    text = text.strip("_;") or "unknown"
    return f"{prefix}:{text}" if prefix else text


def one_word(text: str, default: str = "work") -> str:
    match = re.search(r"[a-z][a-z0-9]{1,15}", (text or "").lower())
    return match.group(0) if match else default


def content_to_text(content: Any) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        pieces: list[str] = []
        for item in content:
            if isinstance(item, str):
                pieces.append(item)
            elif isinstance(item, dict):
                if item.get("type") in {"text", "input_text", "output_text"}:
                    pieces.append(str(item.get("text", "")))
                elif "text" in item:
                    pieces.append(str(item.get("text", "")))
        return "\n".join(piece for piece in pieces if piece)
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
    if cmd in {"cargo", "pytest", "npm", "pnpm", "yarn", "go", "make"} and re.search(
        r"\b(test|check|build|clippy|bench)\b", text
    ):
        return "test"
    if cmd == "git" and re.search(r"\b(commit|push|add|checkout|merge|rebase)\b", text):
        return "repo"
    if cmd in {"curl", "wget", "ssh", "scp", "git"} and re.search(
        r"\b(clone|fetch|pull|push|curl|wget|ssh|https?://)\b", text
    ):
        return "network"
    if re.search(r">\s*|--write|--fix|-w\b|rm\s|mkdir\s|touch\s|cp\s|mv\s", text):
        return "write"
    if cmd in {"rg", "grep", "sed", "cat", "head", "tail", "find", "ls", "nl", "wc", "jq", "git"}:
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
    if parts[0] in {"agentpprof", "agentflame", "collector", "frontend", "docs", "bpf"}:
        return "/".join(parts[:3])
    group = "/".join(parts[:2])
    return group[:80] if group else "repo"


def plausible_path_token(part: str) -> bool:
    part = part.strip("'\"")
    if not part or part.startswith("-") or part.startswith("$"):
        return False
    if part.startswith(("http://", "https://")):
        return False
    if len(part) > 140 or re.search(r"[{}()=;<>|`]", part) or re.search(r"\s", part):
        return False
    suffix = Path(part).suffix.lower()
    return "/" in part or suffix in {
        ".rs",
        ".py",
        ".md",
        ".json",
        ".ts",
        ".tsx",
        ".toml",
        ".lock",
        ".js",
        ".c",
        ".h",
        ".svg",
        ".html",
        ".css",
        ".tex",
    }


def extract_paths_from_command(command: str, project_root: Path) -> list[str]:
    try:
        parts = shlex.split(command, posix=True)
    except ValueError:
        parts = command.split()
    paths = [path_group(part, project_root) for part in parts if plausible_path_token(part)]
    return sorted({path for path in paths if path and path != "none"})[:8]


def extract_domains(text: str) -> list[str]:
    domains = re.findall(r"https?://([^/\s)\"']+)", text or "")
    bare = re.findall(r"\b((?:github|crates|huggingface|hf|openai|anthropic)\.[a-z.]+)\b", text or "")
    return sorted({domain.lower() for domain in domains + bare})[:8]
