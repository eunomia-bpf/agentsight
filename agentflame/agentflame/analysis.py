from __future__ import annotations

import dataclasses
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Protocol

from .models import SessionRecord
from .session_history import discover_sessions
from .util import agent_sight_session_id, clean_space, now_iso, safe_frame, short_hash


class Tagger(Protocol):
    def tag(self, kind: str, text: str, hints: list[str] = ...) -> str:
        ...

    def save(self) -> None:
        ...

    def stats(self) -> dict[str, Any]:
        ...


@dataclasses.dataclass
class AnalysisConfig:
    project_root: Path
    out_dir: Path
    project_name: str = "agentsight"
    codex_root: Path | None = None
    claude_root: Path | None = None
    scan_files: int = 160
    max_sessions: int = 36
    include_previews: bool = False
    tag_llm_calls: bool = False


DIMENSION_SPECS: dict[str, dict[str, Any]] = {
    "session-system": {
        "source": "system",
        "keep": ("project:", "agent:", "session:", "tool:", "cmd:", "effect:", "path:", "domain:", "status:"),
        "metric": "events",
    },
    "prompt-system": {
        "source": "system",
        "keep": ("project:", "agent:", "prompt:", "tool:", "cmd:", "effect:", "path:", "domain:", "status:"),
        "metric": "events",
    },
    "session-token": {
        "source": "token",
        "keep": ("project:", "agent:", "session:", "model:", "kind:"),
        "metric": "tokens",
    },
    "prompt-token": {
        "source": "token",
        "keep": ("project:", "agent:", "prompt:", "model:", "kind:"),
        "metric": "tokens",
    },
    "llm-token": {
        "source": "token",
        "keep": ("project:", "agent:", "llm:", "model:", "kind:"),
        "metric": "tokens",
    },
}


def annotate_sessions(sessions: list[SessionRecord], tagger: Tagger, tag_llm_calls: bool = False) -> None:
    for session in sessions:
        prompt_text = " ".join(req.preview for req in session.user_requests[:8])
        session.session_tag = tagger.tag(
            "session",
            clean_space(f"{session.title} {session.cwd} {prompt_text}", 1500),
            hints=[session.source, session.model],
        )
        for req in session.user_requests:
            req.tag = tagger.tag("prompt", req.preview, hints=[session.session_tag, session.source])
        for llm in session.llm_calls:
            if tag_llm_calls:
                llm.tag = tagger.tag("llm", llm.preview, hints=[session.session_tag, session.source, llm.model])
            else:
                # Default token views inherit prompt semantics to avoid one LLM
                # request per assistant event. Explicit --tag-llm-calls enables
                # fully LLM-tagged call frames.
                llm.tag = session.request_by_index(llm.request_index).tag


def folded_add(counter: Counter[str], frames: list[str], weight: int = 1) -> None:
    cleaned = [safe_frame(frame) for frame in frames if frame]
    if cleaned:
        counter[";".join(cleaned)] += max(int(weight), 1)


def build_folded_stacks(sessions: list[SessionRecord], project_name: str) -> tuple[Counter[str], Counter[str], list[dict[str, Any]]]:
    system: Counter[str] = Counter()
    token: Counter[str] = Counter()
    prompt_rows: list[dict[str, Any]] = []
    for session in sessions:
        agent_frame = safe_frame(session.source, "agent")
        session_frame = safe_frame(session.session_tag, "session")
        for req in session.user_requests:
            prompt_rows.append(
                {
                    "source": session.source,
                    "session_id": session.session_id,
                    "agent_sight_session_id": agent_sight_session_id(session.source, session.session_id),
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


def build_nonsemantic_system(system: Counter[str]) -> Counter[str]:
    baseline: Counter[str] = Counter()
    for stack, weight in system.items():
        frames = [frame for frame in stack.split(";") if not frame.startswith(("session:", "prompt:"))]
        baseline[";".join(frames)] += weight
    return baseline


def project_folded(stacks: Counter[str], keep_prefixes: tuple[str, ...]) -> Counter[str]:
    projected: Counter[str] = Counter()
    for stack, weight in stacks.items():
        frames = [frame for frame in stack.split(";") if frame.startswith(keep_prefixes)]
        if frames:
            projected[";".join(frames)] += weight
    return projected


def build_dimension_views(system: Counter[str], token: Counter[str]) -> dict[str, Counter[str]]:
    views: dict[str, Counter[str]] = {}
    for name, spec in DIMENSION_SPECS.items():
        source = system if spec["source"] == "system" else token
        views[name] = project_folded(source, spec["keep"])
    return views


def summarize_counter(counter: Counter[str], limit: int = 12) -> dict[str, Any]:
    total = sum(counter.values())
    unique = len(counter)
    return {
        "total_weight": total,
        "unique_stacks": unique,
        "compression_ratio": round(total / unique, 3) if unique else 0,
        "max_stack_reuse": max(counter.values()) if counter else 0,
        "top": [{"stack": stack, "weight": weight} for stack, weight in counter.most_common(limit)],
    }


def command_summary(sessions: list[SessionRecord]) -> list[dict[str, Any]]:
    counter: Counter[tuple[str, str, str, str, str, str]] = Counter()
    for session in sessions:
        cohort = "subagent" if "subagent" in session.source else "top"
        family = "codex" if session.source.startswith("codex") else "claude" if session.source.startswith("claude") else session.source
        for event in session.tools:
            counter[(family, cohort, event.category, event.command_name, event.effect, event.status)] += 1
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
    rows.sort(key=lambda row: (-row["count"], row["agent"], row["cmd"]))
    return rows


def timeline_summary(sessions: list[SessionRecord]) -> list[dict[str, Any]]:
    buckets: Counter[str] = Counter()
    for session in sessions:
        if not session.start_ts_ms:
            buckets["unknown"] += 1
            continue
        import datetime as dt

        day = dt.datetime.fromtimestamp(session.start_ts_ms / 1000, tz=dt.timezone.utc).strftime("%Y-%m-%d")
        buckets[day] += 1
    return [{"date": key, "sessions": value} for key, value in sorted(buckets.items())]


def semantic_mixing(system: Counter[str], limit: int = 20) -> dict[str, Any]:
    groups: dict[str, Counter[str]] = defaultdict(Counter)
    flat_groups: dict[str, Counter[str]] = defaultdict(Counter)
    for stack, weight in system.items():
        frames = stack.split(";")
        semantic = "/".join(frame for frame in frames if frame.startswith(("session:", "prompt:")))
        nonsemantic = ";".join(frame for frame in frames if not frame.startswith(("session:", "prompt:")))
        flat = ";".join(frame for frame in frames if not frame.startswith(("project:", "agent:", "session:", "prompt:")))
        groups[nonsemantic][semantic] += weight
        flat_groups[flat][semantic] += weight

    def rows(source: dict[str, Counter[str]], kind: str) -> list[dict[str, Any]]:
        out = []
        for stack, variants in source.items():
            if len(variants) < 2:
                continue
            weight = sum(variants.values())
            out.append(
                {
                    "kind": kind,
                    "baseline_stack": stack,
                    "weight": weight,
                    "semantic_variant_count": len(variants),
                    "top_semantic_variants": [
                        {"semantic": sem, "weight": sem_weight}
                        for sem, sem_weight in variants.most_common(8)
                    ],
                }
            )
        out.sort(key=lambda row: (-row["weight"], -row["semantic_variant_count"], row["baseline_stack"]))
        return out[:limit]

    nonsemantic_rows = rows(groups, "nonsemantic_without_session_prompt")
    flat_rows = rows(flat_groups, "flat_effect_without_project_agent_session_prompt")
    total = sum(system.values())
    return {
        "nonsemantic": {
            "mixed_buckets": len([1 for variants in groups.values() if len(variants) > 1]),
            "mixed_weight": sum(sum(v.values()) for v in groups.values() if len(v) > 1),
            "mixed_weight_pct": round(100 * sum(sum(v.values()) for v in groups.values() if len(v) > 1) / total, 3) if total else 0,
            "examples": nonsemantic_rows,
        },
        "flat": {
            "mixed_buckets": len([1 for variants in flat_groups.values() if len(variants) > 1]),
            "mixed_weight": sum(sum(v.values()) for v in flat_groups.values() if len(v) > 1),
            "mixed_weight_pct": round(100 * sum(sum(v.values()) for v in flat_groups.values() if len(v) > 1) / total, 3) if total else 0,
            "examples": flat_rows,
        },
    }


def session_to_json(session: SessionRecord, include_previews: bool) -> dict[str, Any]:
    return {
        "source": session.source,
        "session_id": session.session_id,
        "agent_sight_session_id": agent_sight_session_id(session.source, session.session_id),
        "session_file": session.path.name,
        "cwd_hash": short_hash(session.cwd, 16) if session.cwd else "",
        "agent_role": session.agent_role,
        "model": session.model,
        "session_tag": session.session_tag,
        "start_ts_ms": session.start_ts_ms,
        "prompt_count": len(session.user_requests),
        "tool_count": len(session.tools),
        "llm_count": len(session.llm_calls),
        "prompts": [
            {
                "index": req.index,
                "ts_ms": req.ts_ms,
                "hash": req.text_hash,
                "tag": req.tag,
                "preview": req.preview if include_previews else "redacted",
            }
            for req in session.user_requests
        ],
    }


def write_folded(path: Path, stacks: Counter[str]) -> None:
    path.write_text("".join(f"{stack} {weight}\n" for stack, weight in sorted(stacks.items())), encoding="utf-8")


def run_analysis(config: AnalysisConfig, tagger: Tagger) -> dict[str, Any]:
    config.out_dir.mkdir(parents=True, exist_ok=True)
    sessions, warnings = discover_sessions(
        project_root=config.project_root,
        codex_root=config.codex_root,
        claude_root=config.claude_root,
        scan_files=config.scan_files,
        max_sessions=config.max_sessions,
    )
    annotate_sessions(sessions, tagger, tag_llm_calls=config.tag_llm_calls)
    tagger.save()

    system, token, prompt_rows = build_folded_stacks(sessions, config.project_name)
    nonsemantic = build_nonsemantic_system(system)
    dimensions = build_dimension_views(system, token)
    mixing = semantic_mixing(system)
    commands = command_summary(sessions)
    timeline = timeline_summary(sessions)

    write_folded(config.out_dir / "semantic-system.folded.txt", system)
    write_folded(config.out_dir / "semantic-token.folded.txt", token)
    write_folded(config.out_dir / "nonsemantic-system.folded.txt", nonsemantic)
    for name, stacks in dimensions.items():
        write_folded(config.out_dir / f"{name}.folded.txt", stacks)

    tag_counts = Counter(row["prompt_tag"] for row in prompt_rows)
    source_counts = Counter(session.source for session in sessions)
    payload = {
        "schema_version": 1,
        "generated_at": now_iso(),
        "project": {
            "name": config.project_name,
            "root": str(config.project_root.resolve()),
        },
        "inputs": {
            "scan_files": config.scan_files,
            "max_sessions": config.max_sessions,
            "tag_llm_calls": config.tag_llm_calls,
            "codex_root": str(config.codex_root) if config.codex_root else None,
            "claude_root": str(config.claude_root) if config.claude_root else None,
        },
        "llm_tagger": tagger.stats(),
        "warnings": warnings[:100],
        "sessions": [session_to_json(session, config.include_previews) for session in sessions],
        "summary": {
            "session_count": len(sessions),
            "source_counts": dict(source_counts),
            "raw_tool_events": sum(len(session.tools) for session in sessions),
            "raw_llm_events": sum(len(session.llm_calls) for session in sessions),
            "system": summarize_counter(system),
            "nonsemantic_system": summarize_counter(nonsemantic),
            "token": summarize_counter(token),
            "dimensions": {name: summarize_counter(stacks, 8) for name, stacks in dimensions.items()},
            "top_prompt_tags": [{"tag": tag, "count": count} for tag, count in tag_counts.most_common(20)],
            "command_summary": commands[:40],
            "timeline": timeline,
            "semantic_mixing": mixing,
        },
        "prompt_tags": [
            {
                **{k: v for k, v in row.items() if k != "preview"},
                "preview": row["preview"] if config.include_previews else "redacted",
            }
            for row in prompt_rows
        ],
        "artifacts": {
            "tag_cache": "tags.json",
            "semantic_system_folded": "semantic-system.folded.txt",
            "semantic_token_folded": "semantic-token.folded.txt",
            "nonsemantic_system_folded": "nonsemantic-system.folded.txt",
            "session_system_folded": "session-system.folded.txt",
            "prompt_system_folded": "prompt-system.folded.txt",
            "session_token_folded": "session-token.folded.txt",
            "prompt_token_folded": "prompt-token.folded.txt",
            "llm_token_folded": "llm-token.folded.txt",
            "dashboard": "index.html",
            "system_flamegraph": "system-flamegraph.svg",
            "token_flamegraph": "token-flamegraph.svg",
            "session_system": "session-system.svg",
            "prompt_system": "prompt-system.svg",
            "session_token": "session-token.svg",
            "prompt_token": "prompt-token.svg",
            "llm_token": "llm-token.svg",
            "tag_bars": "tag-bars.svg",
            "command_bars": "command-bars.svg",
            "timeline": "timeline.svg",
        },
    }
    (config.out_dir / "agentflame.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload
