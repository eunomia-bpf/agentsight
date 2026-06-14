#!/usr/bin/env python3
"""Build semantic flamegraphs from local Codex and Claude session histories.

The experiment intentionally keeps the semantic layer narrow: a local small LLM
or fallback tagger emits one lowercase word per session, prompt, and LLM call.
Those words become stack frames. Identical stack paths are then collapsed before
rendering, which is the part that makes the output a flamegraph rather than a
pretty trace tree.
"""

from __future__ import annotations

import argparse
import csv
import dataclasses
import datetime as dt
import hashlib
import html
import json
import os
import re
import shlex
import subprocess
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CODEX_ROOT = Path.home() / ".codex" / "sessions"
DEFAULT_CLAUDE_ROOT = (
    Path.home() / ".claude" / "projects" / "-home-yunwei37-workspace-agentsight"
)
DEFAULT_LLAMA_CLI = REPO_ROOT.parent / "llama.cpp-latest" / "build" / "bin" / "llama-cli"


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


def short_hash(text: str, n: int = 10) -> str:
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
    if prefix:
        return f"{prefix}:{text}"
    return text


def one_word(text: str, default: str = "work") -> str:
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
    read_cmds = {
        "rg",
        "grep",
        "sed",
        "cat",
        "head",
        "tail",
        "find",
        "ls",
        "nl",
        "wc",
        "jq",
        "git",
    }
    write_cmds = {"tee", "cp", "mv", "rm", "mkdir", "touch", "python", "python3", "node", "npm", "cargo"}
    net_cmds = {"curl", "wget", "ssh", "scp", "git"}
    if cmd in {"cargo", "pytest", "npm", "pnpm", "yarn", "go", "make"} and re.search(
        r"\b(test|check|build|clippy)\b", text
    ):
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
    if parts[0] in {"collector", "frontend", "docs", "bpf"}:
        return "/".join(parts[:3])
    group = "/".join(parts[:2])
    if len(group) > 80:
        return "complex"
    return group


def redact_path_segment(segment: str) -> str:
    if re.fullmatch(r"[0-9a-f]{8,}(-[0-9a-f]{4,})*", segment.lower()):
        return "session"
    if len(segment) > 48:
        return segment[:45] + "..."
    return segment


def plausible_path_token(part: str) -> bool:
    part = part.strip("'\"")
    if not part or part.startswith("-") or part.startswith("$"):
        return False
    if part.startswith(("http://", "https://")):
        return False
    if len(part) > 140:
        return False
    if re.search(r"[{}()=;<>|`]", part):
        return False
    if re.search(r"\s", part):
        return False
    if part.count("/") > 8:
        return False
    suffix = Path(part).suffix.lower()
    has_known_suffix = suffix in {
        ".rs",
        ".py",
        ".md",
        ".json",
        ".ts",
        ".tsx",
        ".toml",
        ".lock",
        ".js",
        ".mjs",
        ".c",
        ".h",
        ".svg",
        ".html",
        ".css",
    }
    return "/" in part or has_known_suffix


def extract_paths_from_command(command: str, project_root: Path) -> list[str]:
    if not command:
        return []
    try:
        parts = shlex.split(command, posix=True)
    except ValueError:
        parts = command.split()
    paths: list[str] = []
    for part in parts:
        if plausible_path_token(part):
            group = path_group(part, project_root)
            if group and group != "none":
                paths.append(group)
    return sorted(set(paths))[:6]


def extract_domains(text: str) -> list[str]:
    domains = re.findall(r"https?://([^/\s)\"']+)", text or "")
    bare = re.findall(r"\b((?:github|crates|huggingface|hf|openai|anthropic)\.[a-z.]+)\b", text or "")
    return sorted(set(d.lower() for d in domains + bare))[:6]


@dataclasses.dataclass
class UserRequest:
    index: int
    ts_ms: int | None
    text_hash: str
    preview: str
    tag: str = "session"


@dataclasses.dataclass
class ToolEvent:
    ts_ms: int | None
    request_index: int
    tool_name: str
    category: str
    command: str
    command_name: str
    effect: str
    status: str = "observed"
    path_groups: list[str] = dataclasses.field(default_factory=list)
    domains: list[str] = dataclasses.field(default_factory=list)
    call_id: str | None = None
    source_id: str = ""


@dataclasses.dataclass
class LlmEvent:
    ts_ms: int | None
    request_index: int
    model: str
    text_hash: str
    preview: str
    input_tokens: int = 0
    output_tokens: int = 0
    cache_tokens: int = 0
    estimated_tokens: int = 0
    tag: str = "response"

    @property
    def token_weight(self) -> int:
        total = self.input_tokens + self.output_tokens + self.cache_tokens + self.estimated_tokens
        return max(total, 1)

    def token_components(self) -> list[tuple[str, int]]:
        parts = [
            ("input", self.input_tokens),
            ("output", self.output_tokens),
            ("cache", self.cache_tokens),
            ("estimate", self.estimated_tokens),
        ]
        return [(kind, value) for kind, value in parts if value > 0] or [("unknown", 1)]


@dataclasses.dataclass
class SessionRecord:
    source: str
    path: Path
    session_id: str
    cwd: str = ""
    agent_role: str = "agent"
    model: str = ""
    title: str = ""
    start_ts_ms: int | None = None
    user_requests: list[UserRequest] = dataclasses.field(default_factory=list)
    tools: list[ToolEvent] = dataclasses.field(default_factory=list)
    llm_calls: list[LlmEvent] = dataclasses.field(default_factory=list)
    warnings: list[str] = dataclasses.field(default_factory=list)
    session_tag: str = "session"

    def ensure_prompt(self, ts_ms: int | None = None) -> int:
        if not self.user_requests:
            self.user_requests.append(
                UserRequest(
                    index=0,
                    ts_ms=ts_ms,
                    text_hash=short_hash(f"{self.session_id}:session"),
                    preview="session bootstrap",
                    tag="session",
                )
            )
        return self.user_requests[-1].index

    def request_by_index(self, index: int) -> UserRequest:
        if not self.user_requests:
            self.ensure_prompt()
        if 0 <= index < len(self.user_requests):
            return self.user_requests[index]
        return self.user_requests[-1]


class OneWordTagger:
    def __init__(
        self,
        cache_path: Path,
        llama_cli: Path | None = None,
        model: Path | None = None,
        llama_limit: int = 0,
        timeout_s: int = 20,
    ) -> None:
        self.cache_path = cache_path
        self.llama_cli = llama_cli
        self.model = model
        self.llama_limit = llama_limit
        self.timeout_s = timeout_s
        self.llama_calls = 0
        self.llama_successes = 0
        self.fallback_uses = 0
        self.cache_hits = 0
        self.requests = 0
        self.llama_failures: list[str] = []
        self.cache: dict[str, str] = {}
        if cache_path.exists():
            try:
                loaded = json.loads(cache_path.read_text(encoding="utf-8"))
                if isinstance(loaded, dict):
                    self.cache = {str(k): str(v) for k, v in loaded.items()}
            except Exception:
                self.cache = {}

    @property
    def mode(self) -> str:
        if (
            self.llama_cli
            and self.model
            and self.llama_cli.exists()
            and self.model.exists()
            and self.llama_limit != 0
        ):
            return "llama"
        return "fallback"

    def save(self) -> None:
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        self.cache_path.write_text(json.dumps(self.cache, indent=2, sort_keys=True), encoding="utf-8")

    def cache_namespace(self) -> str:
        if self.mode == "llama" and self.model:
            return f"llama:{self.model.name}"
        return "fallback"

    def tag(self, kind: str, text: str, hints: Iterable[str] = ()) -> str:
        self.requests += 1
        joined_hints = " ".join(hints)
        source = clean_space(f"{joined_hints} {text}", limit=1800)
        key = short_hash(f"v2\n{self.cache_namespace()}\n{kind}\n{source}", 24)
        if key in self.cache:
            self.cache_hits += 1
            return self.cache[key]
        tag = ""
        if self.mode == "llama" and (self.llama_limit < 0 or self.llama_calls < self.llama_limit):
            tag = self._llama_tag(kind, source)
            if tag:
                self.llama_successes += 1
        if not tag:
            tag = self._fallback_tag(kind, source)
            self.fallback_uses += 1
        tag = self._sanitize(tag)
        self.cache[key] = tag
        return tag

    def _sanitize(self, tag: str) -> str:
        tag = (tag or "").lower().strip()
        tag = re.sub(r"[^a-z0-9]+", "", tag)
        if not re.fullmatch(r"[a-z][a-z0-9]{1,15}", tag or ""):
            return "work"
        return tag[:16]

    def _llama_tag(self, kind: str, text: str) -> str:
        assert self.llama_cli is not None
        assert self.model is not None
        self.llama_calls += 1
        prompt = (
            "You label coding-agent session fragments.\n"
            "Return exactly one lowercase English word, 3 to 14 letters.\n"
            "No spaces, punctuation, quotes, markdown, or explanation.\n"
            "Choose the most specific action or topic word.\n\n"
            f"Fragment kind: {kind}\n"
            f"Fragment:\n{text[:1600]}\n\n"
            "Tag:"
        )
        cmd = [
            str(self.llama_cli),
            "-m",
            str(self.model),
            "--no-display-prompt",
            "--log-disable",
            "--simple-io",
            "--single-turn",
            "--no-warmup",
            "--no-perf",
            "--temp",
            "0",
            "-n",
            "6",
            "--grammar",
            "root ::= [a-z] [a-z] [a-z] [a-z]*",
            "-p",
            prompt,
        ]
        try:
            proc = subprocess.run(
                cmd,
                check=False,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=self.timeout_s,
            )
        except Exception as exc:
            self.llama_failures.append(f"{type(exc).__name__}: {exc}")
            return ""
        out = proc.stdout.strip().splitlines()
        candidates: list[str] = []
        filtered: list[str] = []
        for line in out:
            cleaned = line.strip().lower()
            if not cleaned or cleaned.startswith(("ggml_", "loading ", "build ", "model ", "modalities ", "available ")):
                continue
            if cleaned.startswith(("/", ">", "[", "exiting", "device ")):
                continue
            filtered.append(cleaned)
            if re.fullmatch(r"[a-z][a-z0-9]{2,15}", cleaned):
                candidates.append(cleaned)
        match = re.search(r"\b[a-z][a-z0-9]{2,15}\b", " ".join(filtered).lower())
        if proc.returncode != 0 or not match:
            detail = clean_space(proc.stderr or proc.stdout, 200)
            self.llama_failures.append(f"returncode={proc.returncode} output={detail}")
            return ""
        return candidates[-1] if candidates else match.group(0)

    def _fallback_tag(self, kind: str, text: str) -> str:
        t = text.lower()
        pairs = [
            (r"火焰图|flamegraph|folded|icicle", "flamegraph"),
            (r"osdi|sosp|nsdi|eurosys|paper|论文|学术|review", "paper"),
            (r"可视化|visual|svg|html|render|dashboard|图怎么画", "visual"),
            (r"聚合|aggregate|collapse|collapsed|sum", "aggregate"),
            (r"semantic|tag|标签|one.word|一个词|单词", "tagging"),
            (r"llama|gguf|qwen|tinyllama|model|模型|haiku", "model"),
            (r"session|history|prompt|conversation|上下文", "session"),
            (r"subagent|multi.agent|spawn", "subagent"),
            (r"test|cargo test|pytest|验证|check", "test"),
            (r"debug|bug|failed|error|修复|fix", "debug"),
            (r"implement|实现|patch|edit|write|新增|修改", "implement"),
            (r"commit|push|git add|git commit", "commit"),
            (r"cleanup|clean|delete|清理|archive", "cleanup"),
            (r"design|设计|doc|文档|readme", "design"),
            (r"network|github|crates|download|hf\.co|huggingface", "network"),
            (r"collector|ebpf|kernel|process|syscall|system effect", "collector"),
            (r"frontend|react|next|ui|css", "frontend"),
            (r"read|inspect|search|rg|sed|grep|查看|分析", "inspect"),
            (r"claim|mismatch|verdict|validation", "claim"),
            (r"token|cost|usage", "token"),
            (r"schema|jsonl|parse|parser", "parse"),
            (r"compare|diff|baseline", "diff"),
        ]
        for pattern, tag in pairs:
            if re.search(pattern, t):
                return tag
        if kind == "tool":
            return one_word(t, "tool")
        if kind == "llm":
            return "response"
        return one_word(t, "work")


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
        pieces: list[str] = []
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


def tool_category(name: str, command: str = "") -> str:
    n = (name or "").lower()
    if n.endswith("exec_command") or n == "bash":
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
) -> list[ToolEvent]:
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

    if name == "apply_patch" or "*** " in command:
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
    domains.extend(extract_domains(command))
    cat = tool_category(name, command)
    cmd_name = basename_from_command(command) if cat == "shell" else one_word(name, "tool")
    if cat == "network" and domains:
        cmd_name = domains[0].split(":")[0]
    event = ToolEvent(
        ts_ms=ts_ms,
        request_index=request_index,
        tool_name=name,
        category=cat,
        command=command,
        command_name=cmd_name,
        effect=effect,
        status="observed",
        path_groups=sorted(set(path_groups)),
        domains=sorted(set(domains)),
        call_id=call_id,
        source_id=source_id,
    )
    session.tools.append(event)
    return [event]


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
                        UserRequest(
                            index=current_request,
                            ts_ms=ts_ms,
                            text_hash=short_hash(text),
                            preview=clean_space(text, 180),
                        )
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
                            text_hash=short_hash(json.dumps(usage, sort_keys=True)),
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
                output = str(payload.get("output") or "")
                if call_id in pending:
                    update_tool_status(pending[call_id], output)
            elif ptype == "message" and payload.get("role") == "assistant":
                text = content_to_text(payload.get("content"))
                if text.strip():
                    est = max(1, len(text) // 4)
                    session.llm_calls.append(
                        LlmEvent(
                            ts_ms=ts_ms,
                            request_index=session.ensure_prompt(ts_ms),
                            model=session.model or "codex",
                            text_hash=short_hash(text),
                            preview=clean_space(text, 140),
                            estimated_tokens=est,
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
        if data.get("gitBranch"):
            pass
        if data.get("aiTitle"):
            session.title = str(data.get("aiTitle") or "")
        if dtype == "user":
            message = data.get("message") if isinstance(data.get("message"), dict) else {}
            content = message.get("content")
            if isinstance(content, list) and any(
                isinstance(item, dict) and item.get("type") == "tool_result" for item in content
            ):
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
                    UserRequest(
                        index=current_request,
                        ts_ms=ts_ms,
                        text_hash=short_hash(text),
                        preview=clean_space(text, 180),
                    )
                )
        elif dtype == "assistant":
            message = data.get("message") if isinstance(data.get("message"), dict) else {}
            session.model = str(message.get("model") or session.model)
            content = message.get("content")
            text = content_to_text(content)
            usage = message.get("usage") if isinstance(message.get("usage"), dict) else {}
            input_tokens = int(usage.get("input_tokens") or 0)
            output_tokens = int(usage.get("output_tokens") or 0)
            cache_tokens = int(usage.get("cache_creation_input_tokens") or 0) + int(
                usage.get("cache_read_input_tokens") or 0
            )
            if text.strip() or input_tokens or output_tokens or cache_tokens:
                session.llm_calls.append(
                    LlmEvent(
                        ts_ms=ts_ms,
                        request_index=session.ensure_prompt(ts_ms) if current_request < 0 else current_request,
                        model=session.model or "claude",
                        text_hash=short_hash(text or json.dumps(usage, sort_keys=True)),
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
                    name = str(item.get("name") or "tool")
                    args = parse_tool_args(item.get("input"))
                    events = add_tool_event(
                        session,
                        project_root,
                        ts_ms,
                        session.ensure_prompt(ts_ms) if current_request < 0 else current_request,
                        name,
                        args,
                        call_id=str(item.get("id") or ""),
                        source_id=f"{path.stem}:{idx}",
                    )
                    if item.get("id") and events:
                        pending[str(item["id"])] = events[0]
        elif dtype == "last-prompt" and data.get("lastPrompt") and not session.user_requests:
            text = str(data.get("lastPrompt") or "")
            current_request = len(session.user_requests)
            session.user_requests.append(
                UserRequest(
                    index=current_request,
                    ts_ms=ts_ms,
                    text_hash=short_hash(text),
                    preview=clean_space(text, 180),
                )
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


def parse_sessions(args: argparse.Namespace) -> tuple[list[SessionRecord], list[str]]:
    project_root = Path(args.project_root).resolve()
    warnings: list[str] = []
    sessions: list[SessionRecord] = []
    codex_files = find_session_files(Path(args.codex_root), args.scan_files)
    claude_files = find_session_files(Path(args.claude_root), args.scan_files)
    for path in codex_files:
        try:
            record = parse_codex_session(path, project_root)
            if record:
                sessions.append(record)
        except Exception as exc:
            warnings.append(f"codex parse skipped {path}: {type(exc).__name__}: {exc}")
    for path in claude_files:
        try:
            record = parse_claude_session(path, project_root)
            if record:
                sessions.append(record)
        except Exception as exc:
            warnings.append(f"claude parse skipped {path}: {type(exc).__name__}: {exc}")
    sessions.sort(key=lambda s: s.start_ts_ms or s.path.stat().st_mtime_ns // 1_000_000, reverse=True)
    if args.max_sessions and args.max_sessions > 0:
        sessions = sessions[: args.max_sessions]
    return sessions, warnings


def annotate_sessions(sessions: list[SessionRecord], tagger: OneWordTagger) -> None:
    for session in sessions:
        prompt_text = " ".join(req.preview for req in session.user_requests[:6])
        session.session_tag = tagger.tag(
            "session",
            clean_space(f"{session.title} {session.cwd} {prompt_text}", 1500),
            hints=[session.source, session.model],
        )
        for req in session.user_requests:
            req.tag = tagger.tag("prompt", req.preview)
        for llm in session.llm_calls:
            llm.tag = tagger.tag("llm", llm.preview, hints=[session.session_tag, session.source, llm.model])


def folded_add(counter: Counter[str], frames: list[str], weight: int = 1) -> None:
    cleaned = [safe_frame(frame) for frame in frames if frame]
    if not cleaned:
        return
    counter[";".join(cleaned)] += max(int(weight), 1)


def build_folded_stacks(
    sessions: list[SessionRecord], project_name: str
) -> tuple[Counter[str], Counter[str], list[dict[str, Any]]]:
    system = Counter()
    token = Counter()
    prompt_rows: list[dict[str, Any]] = []
    for session in sessions:
        agent_frame = safe_frame(session.source, "agent")
        session_frame = safe_frame(session.session_tag, "session")
        for req in session.user_requests:
            prompt_rows.append(
                {
                    "source": session.source,
                    "session_id": session.session_id,
                    "session_tag": session.session_tag,
                    "prompt_index": req.index,
                    "prompt_tag": req.tag,
                    "prompt_hash": req.text_hash,
                    "preview": req.preview,
                }
            )
        for event in session.tools:
            req = session.request_by_index(event.request_index)
            base = [
                safe_frame(project_name, "project"),
                agent_frame,
                session_frame,
                safe_frame(req.tag, "prompt"),
                safe_frame(event.category, "tool"),
                safe_frame(event.command_name, "cmd"),
                safe_frame(event.effect, "effect"),
            ]
            if event.path_groups:
                for group in event.path_groups:
                    folded_add(system, base + [safe_frame(group, "path"), safe_frame(event.status, "status")])
            elif event.domains:
                for domain in event.domains:
                    folded_add(system, base + [safe_frame(domain, "domain"), safe_frame(event.status, "status")])
            else:
                folded_add(system, base + [safe_frame(event.status, "status")])
        for call in session.llm_calls:
            req = session.request_by_index(call.request_index)
            for kind, value in call.token_components():
                folded_add(
                    token,
                    [
                        safe_frame(project_name, "project"),
                        agent_frame,
                        session_frame,
                        safe_frame(req.tag, "prompt"),
                        safe_frame(call.tag, "llm"),
                        safe_frame((call.model or "model").split("/")[-1], "model"),
                        safe_frame(kind, "kind"),
                    ],
                    value,
                )
    return system, token, prompt_rows


def build_agent_diff(system: Counter[str]) -> list[dict[str, Any]]:
    by_stack: dict[tuple[str, str], Counter[str]] = defaultdict(Counter)
    totals: Counter[tuple[str, str]] = Counter()
    for stack, weight in system.items():
        frames = stack.split(";")
        family = "other"
        cohort = "top"
        normalized: list[str] = []
        for frame in frames:
            if frame.startswith("agent:"):
                value = frame.split(":", 1)[1]
                if value.startswith("codex"):
                    family = "codex"
                elif value.startswith("claude"):
                    family = "claude"
                else:
                    family = value
                if "subagent" in value:
                    cohort = "subagent"
                continue
            normalized.append(frame)
        normalized_stack = ";".join(normalized)
        for bucket in (cohort, "all"):
            by_stack[(bucket, normalized_stack)][family] += weight
            totals[(bucket, family)] += weight
    rows: list[dict[str, Any]] = []
    for (cohort, stack), counts in by_stack.items():
        codex = counts.get("codex", 0)
        claude = counts.get("claude", 0)
        if not codex and not claude:
            continue
        codex_total = totals.get((cohort, "codex"), 0)
        claude_total = totals.get((cohort, "claude"), 0)
        codex_rate = 1000.0 * codex / codex_total if codex_total else 0.0
        claude_rate = 1000.0 * claude / claude_total if claude_total else 0.0
        delta = codex_rate - claude_rate
        total = codex + claude
        rows.append(
            {
                "cohort": cohort,
                "stack": stack,
                "codex": codex,
                "claude": claude,
                "codex_rate_per_1k": round(codex_rate, 3),
                "claude_rate_per_1k": round(claude_rate, 3),
                "rate_delta_per_1k": round(delta, 3),
                "abs_delta": abs(delta),
                "total": total,
                "winner": "codex" if delta > 0 else "claude" if delta < 0 else "tie",
                "one_sided": bool(codex == 0 or claude == 0),
            }
        )
    rows.sort(key=lambda row: (-row["abs_delta"], -row["total"], row["stack"]))
    return rows


def build_nonsemantic_system(system: Counter[str]) -> Counter[str]:
    baseline = Counter()
    for stack, weight in system.items():
        frames = [
            frame
            for frame in stack.split(";")
            if not frame.startswith("session:") and not frame.startswith("prompt:")
        ]
        baseline[";".join(frames)] += weight
    return baseline


DIMENSION_VIEW_SPECS: dict[str, dict[str, Any]] = {
    "session-system": {
        "source": "system",
        "keep": ("project:", "agent:", "session:", "tool:", "cmd:", "effect:", "path:", "domain:", "status:"),
        "title": "Session System Footprint",
        "subtitle": "Prompt frames removed; width shows system behavior aggregated by one-word session tags.",
        "metric": "events",
    },
    "prompt-system": {
        "source": "system",
        "keep": ("project:", "agent:", "prompt:", "tool:", "cmd:", "effect:", "path:", "domain:", "status:"),
        "title": "Prompt System Footprint",
        "subtitle": "Session frames removed; width shows repeated system behavior aggregated by prompt tags.",
        "metric": "events",
    },
    "session-token": {
        "source": "token",
        "keep": ("project:", "agent:", "session:", "model:", "kind:"),
        "title": "Session Token Footprint",
        "subtitle": "Prompt and LLM-call frames removed; width shows token mass aggregated by session tags.",
        "metric": "tokens",
    },
    "prompt-token": {
        "source": "token",
        "keep": ("project:", "agent:", "prompt:", "model:", "kind:"),
        "title": "Prompt Token Footprint",
        "subtitle": "Session and LLM-call frames removed; width shows token mass aggregated by prompt tags.",
        "metric": "tokens",
    },
    "llm-token": {
        "source": "token",
        "keep": ("project:", "agent:", "llm:", "model:", "kind:"),
        "title": "LLM-Call Token Footprint",
        "subtitle": "Session and prompt frames removed; width shows token mass aggregated by LLM-call tags.",
        "metric": "tokens",
    },
}


def project_folded(stacks: Counter[str], keep_prefixes: tuple[str, ...]) -> Counter[str]:
    projected: Counter[str] = Counter()
    for stack, weight in stacks.items():
        frames = [
            frame
            for frame in stack.split(";")
            if frame.startswith(keep_prefixes)
        ]
        if frames:
            projected[";".join(frames)] += weight
    return projected


def build_dimension_views(system: Counter[str], token: Counter[str]) -> dict[str, Counter[str]]:
    views: dict[str, Counter[str]] = {}
    for name, spec in DIMENSION_VIEW_SPECS.items():
        source = system if spec["source"] == "system" else token
        views[name] = project_folded(source, spec["keep"])
    return views


def dimension_summary(name: str, stacks: Counter[str]) -> dict[str, Any]:
    total = sum(stacks.values())
    unique = len(stacks)
    return {
        "view": name,
        "source": DIMENSION_VIEW_SPECS[name]["source"],
        "total_weight": total,
        "unique_stacks": unique,
        "compression_ratio": round(total / unique, 3) if unique else 0,
        "max_stack_reuse": max(stacks.values()) if stacks else 0,
        "top_stacks": [
            {"stack": stack, "weight": weight}
            for stack, weight in stacks.most_common(8)
        ],
    }


def write_dimension_summary(path: Path, views: dict[str, Counter[str]]) -> None:
    payload = {
        "schema_version": 1,
        "views": [
            dimension_summary(name, stacks)
            for name, stacks in sorted(views.items())
        ],
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def write_dimension_csv(path: Path, views: dict[str, Counter[str]]) -> None:
    fields = [
        "view",
        "source",
        "total_weight",
        "unique_stacks",
        "compression_ratio",
        "max_stack_reuse",
        "top_stack",
        "top_weight",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for name, stacks in sorted(views.items()):
            summary = dimension_summary(name, stacks)
            top = summary["top_stacks"][0] if summary["top_stacks"] else {"stack": "", "weight": 0}
            writer.writerow(
                {
                    "view": name,
                    "source": summary["source"],
                    "total_weight": summary["total_weight"],
                    "unique_stacks": summary["unique_stacks"],
                    "compression_ratio": summary["compression_ratio"],
                    "max_stack_reuse": summary["max_stack_reuse"],
                    "top_stack": top["stack"],
                    "top_weight": top["weight"],
                }
            )


def build_command_summary(sessions: list[SessionRecord]) -> list[dict[str, Any]]:
    counter: Counter[tuple[str, str, str, str, str, str]] = Counter()
    for session in sessions:
        cohort = "subagent" if "subagent" in session.source else "top"
        family = "codex" if session.source.startswith("codex") else "claude" if session.source.startswith("claude") else session.source
        for event in session.tools:
            counter[
                (
                    family,
                    cohort,
                    event.category,
                    event.command_name,
                    event.effect,
                    event.status,
                )
            ] += 1
    rows = [
        {
            "agent": key[0],
            "cohort": key[1],
            "tool": key[2],
            "cmd": key[3],
            "effect": key[4],
            "status": key[5],
            "count": value,
        }
        for key, value in counter.items()
    ]
    rows.sort(key=lambda row: (-row["count"], row["agent"], row["cohort"], row["cmd"]))
    return rows


def write_folded(path: Path, stacks: Counter[str]) -> None:
    lines = [f"{stack} {weight}" for stack, weight in stacks.most_common()]
    path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")


@dataclasses.dataclass
class TrieNode:
    name: str
    value: int = 0
    children: dict[str, "TrieNode"] = dataclasses.field(default_factory=dict)


def trie_from_folded(stacks: Counter[str]) -> TrieNode:
    root = TrieNode("root")
    for stack, value in stacks.items():
        root.value += value
        node = root
        for frame in stack.split(";"):
            node = node.children.setdefault(frame, TrieNode(frame))
            node.value += value
    return root


def max_depth(node: TrieNode, depth: int = 0) -> int:
    if not node.children:
        return depth
    return max(max_depth(child, depth + 1) for child in node.children.values())


def frame_color(frame: str) -> str:
    digest = hashlib.sha256(frame.encode()).digest()
    hue = digest[0] % 360
    sat = 46 + digest[1] % 28
    light = 58 + digest[2] % 18
    return f"hsl({hue} {sat}% {light}%)"


def render_svg(stacks: Counter[str], title: str, subtitle: str, metric: str, path: Path) -> None:
    root = trie_from_folded(stacks)
    width = 1400
    row_h = 24
    left = 16
    top = 56
    usable = width - left * 2
    depth = max_depth(root)
    height = top + (depth + 1) * row_h + 48
    elements: list[str] = []
    elements.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" role="img" aria-label="{html.escape(title)}">'
    )
    elements.append(
        "<style>"
        "text{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;font-size:12px;fill:#1d2329}"
        ".title{font-size:18px;font-weight:700}.sub{font-size:12px;fill:#59636e}"
        ".frame{stroke:#fff;stroke-width:1}.label{pointer-events:none}"
        "</style>"
    )
    elements.append(f'<rect x="0" y="0" width="{width}" height="{height}" fill="#f7f8f4"/>')
    elements.append(f'<text class="title" x="{left}" y="26">{html.escape(title)}</text>')
    elements.append(f'<text class="sub" x="{left}" y="44">{html.escape(subtitle)}</text>')

    clip_id = 0

    def draw(node: TrieNode, x: float, y: float, w: float, level: int) -> None:
        nonlocal clip_id
        if not node.children:
            return
        cur_x = x
        children = sorted(node.children.values(), key=lambda child: (-child.value, child.name))
        for child in children:
            child_w = 0 if node.value == 0 else w * child.value / node.value
            if child_w < 0.5:
                continue
            color = frame_color(child.name)
            label = child.name
            pct = 100.0 * child.value / root.value if root.value else 0
            elements.append(
                f'<rect class="frame" x="{cur_x:.2f}" y="{y:.2f}" width="{child_w:.2f}" '
                f'height="{row_h - 1}" fill="{color}">'
                f"<title>{html.escape(label)} | {child.value} {html.escape(metric)} | {pct:.1f}%</title>"
                "</rect>"
            )
            if child_w > 48:
                cid = f"clip{clip_id}"
                clip_id += 1
                elements.append(
                    f'<clipPath id="{cid}"><rect x="{cur_x + 3:.2f}" y="{y:.2f}" '
                    f'width="{max(child_w - 6, 0):.2f}" height="{row_h - 1}"/></clipPath>'
                )
                text = label if len(label) <= 34 else label[:33] + "."
                elements.append(
                    f'<text class="label" clip-path="url(#{cid})" x="{cur_x + 5:.2f}" '
                    f'y="{y + 16:.2f}">{html.escape(text)}</text>'
                )
            draw(child, cur_x, y + row_h, child_w, level + 1)
            cur_x += child_w

    draw(root, left, top, usable, 0)
    elements.append(f'<text class="sub" x="{left}" y="{height - 18}">total: {root.value} {html.escape(metric)}</text>')
    elements.append("</svg>")
    path.write_text("\n".join(elements), encoding="utf-8")


def summarize(
    sessions: list[SessionRecord],
    system: Counter[str],
    nonsemantic: Counter[str],
    token: Counter[str],
    dimension_views: dict[str, Counter[str]],
    warnings: list[str],
    tagger: OneWordTagger,
    args: argparse.Namespace,
) -> dict[str, Any]:
    raw_tool = sum(len(s.tools) for s in sessions)
    raw_llm = sum(len(s.llm_calls) for s in sessions)
    system_weights = list(system.values())
    token_weights = list(token.values())
    nonsemantic_weights = list(nonsemantic.values())
    source_counts = Counter(s.source for s in sessions)
    prompt_counts = Counter(req.tag for s in sessions for req in s.user_requests)
    session_tags = Counter(s.session_tag for s in sessions)
    token_kind_counts: Counter[str] = Counter()
    for stack, weight in token.items():
        for frame in stack.split(";"):
            if frame.startswith("kind:"):
                token_kind_counts[frame.split(":", 1)[1]] += weight
    all_tags = [s.session_tag for s in sessions]
    all_tags.extend(req.tag for s in sessions for req in s.user_requests)
    all_tags.extend(call.tag for s in sessions for call in s.llm_calls)
    invalid_tags = [tag for tag in all_tags if not re.fullmatch(r"[a-z][a-z0-9]{1,15}", tag)]
    session_fingerprint = short_hash(
        "\n".join(
            f"{s.source}:{s.session_id}:{len(s.user_requests)}:{len(s.tools)}:{len(s.llm_calls)}"
            for s in sessions
        ),
        16,
    )
    return {
        "generated_at": now_iso(),
        "project": args.project_name,
        "config": {
            "scan_files": args.scan_files,
            "max_sessions": args.max_sessions,
            "llama_limit": args.llama_limit,
            "include_previews": args.include_previews,
        },
        "session_fingerprint": session_fingerprint,
        "session_count": len(sessions),
        "source_counts": dict(source_counts),
        "raw_tool_events": raw_tool,
        "raw_llm_events": raw_llm,
        "expanded_system_observations": sum(system_weights),
        "system_unique_stacks": len(system),
        "nonsemantic_system_unique_stacks": len(nonsemantic),
        "token_unique_stacks": len(token),
        "system_total_weight": sum(system_weights),
        "nonsemantic_system_total_weight": sum(nonsemantic_weights),
        "token_total_weight": sum(token_weights),
        "system_collapsed_observations": max(sum(system_weights) - len(system), 0),
        "system_observation_expansion": max(sum(system_weights) - raw_tool, 0),
        "nonsemantic_collapsed_observations": max(sum(nonsemantic_weights) - len(nonsemantic), 0),
        "token_collapsed_observations": max(sum(token_weights) - len(token), 0),
        "system_max_stack_reuse": max(system_weights) if system_weights else 0,
        "nonsemantic_max_stack_reuse": max(nonsemantic_weights) if nonsemantic_weights else 0,
        "token_max_stack_reuse": max(token_weights) if token_weights else 0,
        "top_system_stacks": [{"stack": k, "weight": v} for k, v in system.most_common(12)],
        "top_nonsemantic_stacks": [{"stack": k, "weight": v} for k, v in nonsemantic.most_common(12)],
        "top_token_stacks": [{"stack": k, "weight": v} for k, v in token.most_common(12)],
        "dimension_views": [
            dimension_summary(name, stacks)
            for name, stacks in sorted(dimension_views.items())
        ],
        "token_weight_by_kind": dict(token_kind_counts),
        "top_prompt_tags": prompt_counts.most_common(20),
        "top_session_tags": session_tags.most_common(20),
        "tag_contract": {
            "total_tags": len(all_tags),
            "unique_tags": len(set(all_tags)),
            "invalid_tags": invalid_tags[:20],
            "invalid_count": len(invalid_tags),
            "requests": tagger.requests,
            "cache_hits": tagger.cache_hits,
            "llama_successes": tagger.llama_successes,
            "fallback_uses": tagger.fallback_uses,
        },
        "tagger": {
            "mode": tagger.mode,
            "llama_cli": Path(tagger.llama_cli).name if tagger.llama_cli else None,
            "model": Path(tagger.model).name if tagger.model else None,
            "llama_calls": tagger.llama_calls,
            "llama_successes": tagger.llama_successes,
            "fallback_uses": tagger.fallback_uses,
            "llama_failures": tagger.llama_failures[:8],
        },
        "warnings": warnings[:50],
    }


def write_prompt_csv(path: Path, rows: list[dict[str, Any]], include_previews: bool = False) -> None:
    fields = ["source", "session_id", "session_tag", "prompt_index", "prompt_tag", "prompt_hash", "preview"]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            safe_row = dict(row)
            safe_row["preview"] = (
                clean_space(str(safe_row.get("preview") or ""), 180) if include_previews else "redacted"
            )
            writer.writerow(safe_row)


def write_agent_diff_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    fields = [
        "cohort",
        "winner",
        "rate_delta_per_1k",
        "codex_rate_per_1k",
        "claude_rate_per_1k",
        "codex",
        "claude",
        "total",
        "one_sided",
        "stack",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row[field] for field in fields})


def write_command_summary_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    fields = ["agent", "cohort", "tool", "cmd", "effect", "status", "count"]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row[field] for field in fields})


def write_sessions_json(path: Path, sessions: list[SessionRecord]) -> None:
    payload = []
    for s in sessions:
        payload.append(
            {
                "source": s.source,
                "session_id": s.session_id,
                "session_tag": s.session_tag,
                "session_file": s.path.name,
                "cwd_group": path_group(s.cwd, REPO_ROOT),
                "model": s.model,
                "prompt_count": len(s.user_requests),
                "tool_count": len(s.tools),
                "llm_count": len(s.llm_calls),
                "prompt_tags": Counter(req.tag for req in s.user_requests).most_common(),
                "tool_categories": Counter(t.category for t in s.tools).most_common(),
                "tool_effects": Counter(t.effect for t in s.tools).most_common(),
            }
        )
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def file_sha256(path: Path) -> str | None:
    try:
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()
    except OSError:
        return None


def command_text(cmd: list[str], cwd: Path) -> str | None:
    try:
        proc = subprocess.run(
            cmd,
            cwd=str(cwd),
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=5,
        )
    except Exception:
        return None
    if proc.returncode != 0:
        return None
    return proc.stdout.strip()


def build_input_manifest(
    sessions: list[SessionRecord],
    args: argparse.Namespace,
    script_path: Path,
) -> dict[str, Any]:
    repo_root = Path(args.project_root).resolve()
    model_path = Path(args.model).resolve() if args.model else None
    llama_cli = Path(args.llama_cli).resolve() if args.llama_cli else None
    session_entries = []
    for session in sessions:
        session_entries.append(
            {
                "source": session.source,
                "session_id": session.session_id,
                "session_file": session.path.name,
                "content_sha256": file_sha256(session.path),
                "prompt_count": len(session.user_requests),
                "tool_count": len(session.tools),
                "llm_count": len(session.llm_calls),
            }
        )
    return {
        "generated_at": now_iso(),
        "argv": sys.argv,
        "project": args.project_name,
        "repo_commit": command_text(["git", "rev-parse", "HEAD"], repo_root),
        "repo_dirty": bool(command_text(["git", "status", "--short"], repo_root)),
        "script_file": script_path.name,
        "script_sha256": file_sha256(script_path),
        "llama_cpp_commit": command_text(["git", "rev-parse", "HEAD"], repo_root.parent / "llama.cpp-latest")
        if (repo_root.parent / "llama.cpp-latest" / ".git").exists()
        else None,
        "llama_cli": llama_cli.name if llama_cli else None,
        "llama_cli_sha256": file_sha256(llama_cli) if llama_cli and llama_cli.exists() else None,
        "model": model_path.name if model_path else None,
        "model_size_bytes": model_path.stat().st_size if model_path and model_path.exists() else None,
        "model_sha256": file_sha256(model_path) if model_path and model_path.exists() else None,
        "selection": {
            "scan_files": args.scan_files,
            "max_sessions": args.max_sessions,
            "codex_root_kind": "codex_sessions",
            "claude_root_kind": "claude_project_sessions",
        },
        "sessions": session_entries,
    }


def write_html(out_dir: Path, summary: dict[str, Any], agent_diff: list[dict[str, Any]]) -> None:
    def table_rows(items: list[dict[str, Any]], key: str = "stack") -> str:
        rows = []
        for item in items[:10]:
            label = html.escape(str(item.get(key, "")))
            weight = html.escape(str(item.get("weight", "")))
            rows.append(f"<tr><td>{label}</td><td>{weight}</td></tr>")
        return "\n".join(rows)

    prompt_rows = "\n".join(
        f"<tr><td>{html.escape(str(tag))}</td><td>{count}</td></tr>"
        for tag, count in summary.get("top_prompt_tags", [])[:12]
    )
    diff_rows = "\n".join(
        f"<tr><td>{html.escape(row['cohort'])}</td><td>{html.escape(row['winner'])}</td>"
        f"<td>{row['rate_delta_per_1k']}</td><td>{row['codex_rate_per_1k']}</td>"
        f"<td>{row['claude_rate_per_1k']}</td><td>{row['codex']}</td><td>{row['claude']}</td>"
        f"<td>{html.escape(row['stack'])}</td></tr>"
        for row in agent_diff[:12]
    )
    baseline_rows = table_rows(summary["top_nonsemantic_stacks"])
    dimension_figures = "\n".join(
        f"""    <section>
      <h2>{html.escape(spec["title"])}</h2>
      <p>{html.escape(spec["subtitle"])}</p>
      <div class="figure"><img src="{html.escape(name)}.svg" width="1400" alt="{html.escape(spec["title"])}"></div>
    </section>"""
        for name, spec in sorted(DIMENSION_VIEW_SPECS.items())
    )
    html_text = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>AgentSight Semantic Flamegraph Experiment</title>
  <style>
    :root {{
      --bg: #f7f8f4;
      --ink: #1d2329;
      --muted: #59636e;
      --line: #d8ded2;
      --panel: #ffffff;
      --accent: #0f766e;
    }}
    body {{
      margin: 0;
      background: var(--bg);
      color: var(--ink);
      font-family: ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      line-height: 1.45;
    }}
    main {{ max-width: 1440px; margin: 0 auto; padding: 24px; }}
    h1 {{ font-size: 24px; margin: 0 0 6px; letter-spacing: 0; }}
    h2 {{ font-size: 17px; margin: 28px 0 10px; letter-spacing: 0; }}
    p {{ color: var(--muted); margin: 0 0 14px; max-width: 960px; }}
    .stats {{ display: grid; grid-template-columns: repeat(6, minmax(120px, 1fr)); gap: 10px; margin: 18px 0; }}
    .stat {{ background: var(--panel); border: 1px solid var(--line); border-radius: 8px; padding: 12px; }}
    .stat b {{ display: block; font-size: 22px; }}
    .stat span {{ color: var(--muted); font-size: 12px; }}
    .figure {{ background: var(--panel); border: 1px solid var(--line); border-radius: 8px; padding: 10px; overflow-x: auto; }}
    img {{ display: block; max-width: none; }}
    table {{ width: 100%; border-collapse: collapse; background: var(--panel); border: 1px solid var(--line); border-radius: 8px; overflow: hidden; }}
    th, td {{ text-align: left; border-bottom: 1px solid var(--line); padding: 8px 10px; font-size: 13px; vertical-align: top; }}
    th {{ color: var(--muted); font-weight: 600; }}
    code {{ font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; }}
    .grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 14px; }}
    @media (max-width: 900px) {{
      main {{ padding: 14px; }}
      .stats {{ grid-template-columns: repeat(2, minmax(120px, 1fr)); }}
      .grid {{ grid-template-columns: 1fr; }}
    }}
  </style>
</head>
<body>
<main>
  <h1>AgentSight Semantic Flamegraph Experiment</h1>
  <p>Real local Codex and Claude sessions are reduced to one-word tags, then converted to folded stacks before rendering. The important artifact is the folded stack, not the tree drawing.</p>
  <div class="stats">
    <div class="stat"><b>{summary["session_count"]}</b><span>sessions</span></div>
    <div class="stat"><b>{summary["raw_tool_events"]}</b><span>tool events</span></div>
    <div class="stat"><b>{summary["expanded_system_observations"]}</b><span>stack observations</span></div>
    <div class="stat"><b>{summary["system_unique_stacks"]}</b><span>system stacks</span></div>
    <div class="stat"><b>{summary["system_collapsed_observations"]}</b><span>collapsed observations</span></div>
    <div class="stat"><b>{summary["system_max_stack_reuse"]}</b><span>max stack reuse</span></div>
  </div>
  <p>Tagger mode: <code>{html.escape(summary["tagger"]["mode"])}</code>. Model successes: <code>{summary["tag_contract"]["llama_successes"]}</code>. Fallback tags: <code>{summary["tag_contract"]["fallback_uses"]}</code>. Generated at <code>{html.escape(summary["generated_at"])}</code>.</p>

  <h2>System Footprint</h2>
  <p>Width is aggregated stack-observation count. One tool event may expand to multiple path/domain observations. Stack grammar: <code>project;agent;session-tag;prompt-tag;tool;cmd;effect;path/domain/status</code>.</p>
  <div class="figure"><img src="system-flamegraph.svg" width="1400" alt="System semantic flamegraph"></div>

  <h2>Token Footprint</h2>
  <p>Width is token count split by provenance kind: input, output, cache, or estimate. Treat this as source-local accounting, not a cross-agent cost benchmark. Stack grammar: <code>project;agent;session-tag;prompt-tag;llm-tag;model;kind</code>.</p>
  <div class="figure"><img src="token-flamegraph.svg" width="1400" alt="Token semantic flamegraph"></div>

  <h2>Dimension Flamegraphs</h2>
  <p>These projections keep the same underlying observations but remove one semantic axis at a time. They test whether session, prompt, and LLM-call tags remain useful as independent aggregation keys.</p>
{dimension_figures}

  <div class="grid">
    <section>
      <h2>Top Prompt Tags</h2>
      <table><thead><tr><th>tag</th><th>count</th></tr></thead><tbody>{prompt_rows}</tbody></table>
    </section>
    <section>
      <h2>Repeated System Stacks</h2>
      <table><thead><tr><th>stack</th><th>weight</th></tr></thead><tbody>{table_rows(summary["top_system_stacks"])}</tbody></table>
    </section>
  </div>

  <h2>Nonsemantic Baseline</h2>
  <p>The baseline removes session and prompt tags before folding. It shows what a process/tool summary can find without semantic attribution.</p>
  <table><thead><tr><th>stack</th><th>weight</th></tr></thead><tbody>{baseline_rows}</tbody></table>

  <h2>Behavior Diff</h2>
  <p>Normalized system stacks are compared after removing the agent frame and normalizing by each cohort's total observations. This is a diagnostic, not a causal claim.</p>
  <table><thead><tr><th>cohort</th><th>winner</th><th>delta/1k</th><th>codex/1k</th><th>claude/1k</th><th>codex</th><th>claude</th><th>normalized stack</th></tr></thead><tbody>{diff_rows}</tbody></table>

  <h2>Artifacts</h2>
  <p><code>semantic-system.folded.txt</code>, <code>nonsemantic-system.folded.txt</code>, <code>semantic-token.folded.txt</code>, <code>tag-dimensions.json</code>, <code>aggregation.json</code>, <code>agent-diff.csv</code>, <code>command-summary.csv</code>, <code>prompt-tags.csv</code>, and <code>sessions.json</code> are generated by the flamegraph builder. <code>evaluate_artifacts.py</code> adds <code>evaluation.json</code>, <code>semantic-mixing.csv</code>, <code>claim-gates.csv</code>, and <code>evaluation-summary.md</code>.</p>
</main>
</body>
</html>
"""
    (out_dir / "index.html").write_text(html_text, encoding="utf-8")


def run(args: argparse.Namespace) -> int:
    out_dir = Path(args.out).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    sessions, warnings = parse_sessions(args)
    tagger = OneWordTagger(
        cache_path=Path(args.tag_cache) if args.tag_cache else out_dir / "tag-cache.json",
        llama_cli=Path(args.llama_cli) if args.llama_cli else None,
        model=Path(args.model) if args.model else None,
        llama_limit=args.llama_limit,
        timeout_s=args.llama_timeout,
    )
    annotate_sessions(sessions, tagger)
    system, token, prompt_rows = build_folded_stacks(sessions, args.project_name)
    nonsemantic = build_nonsemantic_system(system)
    dimension_views = build_dimension_views(system, token)
    agent_diff = build_agent_diff(system)
    command_summary = build_command_summary(sessions)

    write_folded(out_dir / "semantic-system.folded.txt", system)
    write_folded(out_dir / "nonsemantic-system.folded.txt", nonsemantic)
    write_folded(out_dir / "semantic-token.folded.txt", token)
    for name, stacks in sorted(dimension_views.items()):
        write_folded(out_dir / f"{name}.folded.txt", stacks)
        spec = DIMENSION_VIEW_SPECS[name]
        render_svg(
            stacks,
            spec["title"],
            spec["subtitle"],
            spec["metric"],
            out_dir / f"{name}.svg",
        )
    write_dimension_summary(out_dir / "tag-dimensions.json", dimension_views)
    write_dimension_csv(out_dir / "tag-dimensions.csv", dimension_views)
    render_svg(
        system,
        "System Footprint Semantic Flamegraph",
        "Collapsed by one-word session and prompt tags; width = expanded stack observations.",
        "events",
        out_dir / "system-flamegraph.svg",
    )
    render_svg(
        token,
        "Token Footprint Semantic Flamegraph",
        "Collapsed by one-word session, prompt, and LLM-call tags; width = tokens.",
        "tokens",
        out_dir / "token-flamegraph.svg",
    )
    write_agent_diff_csv(out_dir / "agent-diff.csv", agent_diff)
    write_command_summary_csv(out_dir / "command-summary.csv", command_summary)
    write_prompt_csv(out_dir / "prompt-tags.csv", prompt_rows, include_previews=args.include_previews)
    write_sessions_json(out_dir / "sessions.json", sessions)
    manifest = build_input_manifest(sessions, args, Path(__file__).resolve())
    manifest_path = out_dir / "input-manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    summary = summarize(sessions, system, nonsemantic, token, dimension_views, warnings, tagger, args)
    summary["input_manifest_sha256"] = file_sha256(manifest_path)
    summary["top_agent_diffs"] = agent_diff[:20]
    summary["top_command_summary"] = command_summary[:20]
    (out_dir / "aggregation.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    write_html(out_dir, summary, agent_diff)
    tagger.save()

    print(
        json.dumps(
            {
                "out": str(out_dir),
                "sessions": len(sessions),
                "system_unique_stacks": len(system),
                "token_unique_stacks": len(token),
                "tagger": summary["tagger"],
            },
            indent=2,
        )
    )
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", default=str(REPO_ROOT))
    parser.add_argument("--project-name", default="agentsight")
    parser.add_argument("--codex-root", default=str(DEFAULT_CODEX_ROOT))
    parser.add_argument("--claude-root", default=str(DEFAULT_CLAUDE_ROOT))
    parser.add_argument("--out", default=str(REPO_ROOT / "docs" / "visexp" / "out"))
    parser.add_argument("--scan-files", type=int, default=160, help="Most recent JSONL files to scan per source.")
    parser.add_argument("--max-sessions", type=int, default=36, help="Maximum matching sessions to include.")
    parser.add_argument("--tag-cache", default="")
    parser.add_argument("--llama-cli", default=str(DEFAULT_LLAMA_CLI) if DEFAULT_LLAMA_CLI.exists() else "")
    parser.add_argument("--model", default="", help="GGUF model for llama.cpp one-word annotation.")
    parser.add_argument(
        "--llama-limit",
        type=int,
        default=0,
        help="Maximum tags to request from llama.cpp. 0 disables model calls, -1 means no limit.",
    )
    parser.add_argument("--llama-timeout", type=int, default=20)
    parser.add_argument(
        "--include-previews",
        action="store_true",
        help="Include sanitized prompt previews in CSV output. Default keeps committed artifacts redacted.",
    )
    return parser


if __name__ == "__main__":
    raise SystemExit(run(build_parser().parse_args()))
