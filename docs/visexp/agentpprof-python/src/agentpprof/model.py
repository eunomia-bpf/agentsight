from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class UserRequest:
    index: int
    ts_ms: int | None
    text_hash: str
    preview: str
    tag: str = "session"


@dataclass
class ToolEvent:
    ts_ms: int | None
    request_index: int
    tool_name: str
    category: str
    command: str
    command_name: str
    effect: str
    tag: str = "tool"
    status: str = "observed"
    path_groups: list[str] = field(default_factory=list)
    domains: list[str] = field(default_factory=list)
    call_id: str | None = None
    source_id: str = ""


@dataclass
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

    def token_components(self) -> list[tuple[str, int]]:
        parts = [
            ("input", self.input_tokens),
            ("output", self.output_tokens),
            ("cache", self.cache_tokens),
            ("estimate", self.estimated_tokens),
        ]
        nonzero = [(kind, value) for kind, value in parts if value > 0]
        return nonzero or [("unknown", 1)]


@dataclass
class SessionRecord:
    source: str
    path: Path
    session_id: str
    cwd: str = ""
    agent_role: str = "agent"
    model: str = ""
    title: str = ""
    start_ts_ms: int | None = None
    user_requests: list[UserRequest] = field(default_factory=list)
    tools: list[ToolEvent] = field(default_factory=list)
    llm_calls: list[LlmEvent] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    session_tag: str = "session"

    def ensure_prompt(self, ts_ms: int | None = None) -> int:
        if not self.user_requests:
            self.user_requests.append(
                UserRequest(
                    index=0,
                    ts_ms=ts_ms,
                    text_hash="bootstrap",
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
