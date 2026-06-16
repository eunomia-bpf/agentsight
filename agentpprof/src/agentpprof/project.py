from __future__ import annotations

from collections import Counter
from pathlib import Path

from .model import SessionRecord
from .pprof import SemanticSample
from .util import safe_frame


def token_samples(project_name: str, sessions: list[SessionRecord]) -> list[SemanticSample]:
    out: list[SemanticSample] = []
    for session in sessions:
        for call in session.llm_calls:
            request = session.request_by_index(call.request_index)
            for token_kind, value in call.token_components():
                stack = (
                    safe_frame(project_name, "project"),
                    safe_frame(session.source, "agent"),
                    safe_frame(session.session_tag, "session"),
                    safe_frame(request.tag, "prompt"),
                    safe_frame(call.tag, "call:llm"),
                    safe_frame(call.model or session.model or session.source, "model"),
                    safe_frame(token_kind, "token"),
                )
                out.append(
                    SemanticSample(
                        stack=stack,
                        value=value,
                        labels=(
                            ("source", session.source),
                            ("session", session.session_id),
                            ("prompt", request.text_hash),
                            ("kind", token_kind),
                        ),
                    )
                )
    return out


def tool_samples(project_name: str, sessions: list[SessionRecord]) -> list[SemanticSample]:
    out: list[SemanticSample] = []
    for session in sessions:
        for tool in session.tools:
            request = session.request_by_index(tool.request_index)
            targets = tool.path_groups or tool.domains or ["none"]
            for target in targets:
                frames = [
                    safe_frame(project_name, "project"),
                    safe_frame(session.source, "agent"),
                    safe_frame(session.session_tag, "session"),
                    safe_frame(request.tag, "prompt"),
                    safe_frame(tool.tag, "call:tool"),
                    safe_frame(tool.effect, "effect"),
                    safe_frame(target, "target"),
                    safe_frame(tool.category, "tool"),
                ]
                if tool.status != "observed":
                    frames.append(safe_frame(tool.status, "status"))
                frames.append(safe_frame(tool.command_name, "process"))
                out.append(
                    SemanticSample(
                        stack=tuple(frames),
                        value=1,
                        labels=(
                            ("source", session.source),
                            ("session", session.session_id),
                            ("prompt", request.text_hash),
                            ("effect", tool.effect),
                            ("tool", tool.tool_name),
                        ),
                    )
                )
    return out


def file_samples(project_name: str, sessions: list[SessionRecord]) -> list[SemanticSample]:
    out: list[SemanticSample] = []
    for session in sessions:
        for tool in session.tools:
            if not tool.path_groups:
                continue
            request = session.request_by_index(tool.request_index)
            for path_group in tool.path_groups:
                stack = (
                    safe_frame(project_name, "project"),
                    safe_frame(session.source, "agent"),
                    safe_frame(session.session_tag, "session"),
                    safe_frame(request.tag, "prompt"),
                    safe_frame(tool.effect, "effect"),
                    safe_frame(tool.command_name, "process"),
                    safe_frame(path_group, "file"),
                )
                out.append(
                    SemanticSample(
                        stack=stack,
                        value=1,
                        labels=(
                            ("source", session.source),
                            ("session", session.session_id),
                            ("prompt", request.text_hash),
                            ("effect", tool.effect),
                            ("file", path_group),
                        ),
                    )
                )
    return out


def network_samples(project_name: str, sessions: list[SessionRecord]) -> list[SemanticSample]:
    out: list[SemanticSample] = []
    for session in sessions:
        for tool in session.tools:
            if not tool.domains:
                continue
            request = session.request_by_index(tool.request_index)
            for domain in tool.domains:
                stack = (
                    safe_frame(project_name, "project"),
                    safe_frame(session.source, "agent"),
                    safe_frame(session.session_tag, "session"),
                    safe_frame(request.tag, "prompt"),
                    safe_frame(tool.effect, "effect"),
                    safe_frame(tool.command_name, "process"),
                    safe_frame(domain, "domain"),
                )
                out.append(
                    SemanticSample(
                        stack=stack,
                        value=1,
                        labels=(
                            ("source", session.source),
                            ("session", session.session_id),
                            ("prompt", request.text_hash),
                            ("domain", domain),
                        ),
                    )
                )
    return out


PROFILE_BUILDERS = {
    "tokens": ("tokens", "count", token_samples),
    "tools": ("tool_events", "count", tool_samples),
    "files": ("file_events", "count", file_samples),
    "network": ("network_events", "count", network_samples),
}


def folded_lines(samples: list[SemanticSample]) -> list[str]:
    counter: Counter[tuple[str, ...]] = Counter()
    for sample in samples:
        counter[sample.stack] += sample.value
    return [f"{';'.join(stack)} {value}" for stack, value in counter.most_common()]


def summarize_sessions(sessions: list[SessionRecord]) -> dict[str, object]:
    prompt_tags = Counter(req.tag for session in sessions for req in session.user_requests)
    session_tags = Counter(session.session_tag for session in sessions)
    tool_effects = Counter(tool.effect for session in sessions for tool in session.tools)
    return {
        "session_count": len(sessions),
        "prompt_count": sum(len(session.user_requests) for session in sessions),
        "llm_call_count": sum(len(session.llm_calls) for session in sessions),
        "tool_call_count": sum(len(session.tools) for session in sessions),
        "top_session_tags": session_tags.most_common(20),
        "top_prompt_tags": prompt_tags.most_common(30),
        "top_tool_effects": tool_effects.most_common(20),
    }


def project_name_from_root(project_root: Path) -> str:
    return project_root.resolve().name or "project"
