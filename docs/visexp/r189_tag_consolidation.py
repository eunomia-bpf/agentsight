#!/usr/bin/env python3
"""R189: consolidate noisy one-word tags into auditable canonical tags.

This script reads an existing AgentFlame report. It does not rescan or mutate raw
agent traces. The goal is to evaluate whether a display-time canonical tag layer
can reduce long-tail label fragmentation while preserving the original raw tag
for audit.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import re
import subprocess
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[1]
DEFAULT_INPUT = REPO_ROOT / ".agentsight" / "agentflame" / "r170-full-current"
DEFAULT_OUT_DIR = SCRIPT_DIR / "out" / "tag-consolidation-r189"

NOISE_SUBSTRINGS = (
    "agentfl",
    "agentsight",
    "codex",
    "claude",
    "jsonok",
    "rootpid",
    "rawssl",
    "ssl",
)

GENERIC_SUFFIXES = (
    "check",
    "fix",
    "run",
    "update",
    "updates",
    "write",
    "rewrite",
    "review",
    "analyze",
    "analysis",
    "design",
    "build",
    "docs",
    "doc",
    "test",
    "tests",
    "report",
    "stage",
    "sync",
)

CANONICAL_ALIASES = {
    "bench": "benchmark",
    "benchmarks": "benchmark",
    "doc": "docs",
    "docu": "docs",
    "document": "docs",
    "writedocs": "docs",
    "updatedocs": "docs",
    "docupdate": "docs",
    "docsupdate": "docs",
    "docsfix": "docs",
    "docsorganize": "docs",
    "docwrite": "docs",
    "docrewrite": "docs",
    "docsreview": "docs",
    "docsanalyze": "docs",
    "docszh": "docs",
    "testdocs": "docs",
    "testcase": "test",
    "testcases": "test",
    "smoketest": "test",
    "eval": "evaluate",
    "metrics": "measure",
    "stats": "measure",
    "countlines": "measure",
    "rqanalyze": "analyze",
    "rqrewrite": "docs",
    "updateplan": "plan",
    "fix": "debug",
    "fixes": "debug",
    "fixwarn": "debug",
    "warnfix": "debug",
    "designfix": "design",
    "benchfix": "benchmark",
    "rmarkdownfix": "docs",
    "paperagentfl": "paper",
    "paperupdate": "paper",
    "rootpidrefs": "trace",
    "rootpidrefsc": "trace",
    "jsonokno": "verify",
    "rawsslok": "verify",
    "sslverify": "verify",
    "sslcountchk": "verify",
    "verifyimport": "verify",
    "bashoutput": "shell",
}


@dataclass
class TagProfile:
    tag: str
    row_count: int = 0
    effect_weight: int = 0
    event_count: int = 0
    token_weight: int = 0
    sessions: Counter[str] = field(default_factory=Counter)
    prompts: Counter[str] = field(default_factory=Counter)
    llm_tags: Counter[str] = field(default_factory=Counter)
    processes: Counter[str] = field(default_factory=Counter)
    effects: Counter[str] = field(default_factory=Counter)
    paths: Counter[str] = field(default_factory=Counter)
    agents: Counter[str] = field(default_factory=Counter)
    models: Counter[str] = field(default_factory=Counter)
    kinds: Counter[str] = field(default_factory=Counter)

    def support(self, dimension: str) -> int:
        if dimension == "llm":
            return max(self.event_count, self.token_weight)
        if dimension in {"session", "prompt"}:
            return max(self.effect_weight, self.row_count)
        return max(self.effect_weight, self.row_count, self.event_count, self.token_weight)


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def git(args: list[str]) -> str | None:
    try:
        return subprocess.check_output(
            ["git", *args],
            cwd=REPO_ROOT,
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except Exception:
        return None


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT.resolve()))
    except Exception:
        return str(path)


def read_folded(path: Path) -> Counter[str]:
    stacks: Counter[str] = Counter()
    with path.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, 1):
            line = line.rstrip("\n")
            if not line:
                continue
            stack, _, weight = line.rpartition(" ")
            if not stack or not weight.isdigit():
                raise ValueError(f"invalid folded line {path}:{line_no}: {line[:160]}")
            stacks[stack] += int(weight)
    return stacks


def write_folded(path: Path, stacks: Counter[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [f"{stack} {weight}" for stack, weight in sorted(stacks.items())]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def pct(part: float | int, whole: float | int) -> float:
    return round(100.0 * float(part) / float(whole), 3) if whole else 0.0


def parse_frames(stack: str) -> list[tuple[str, str]]:
    frames: list[tuple[str, str]] = []
    for frame in stack.split(";"):
        if ":" not in frame:
            frames.append((frame, ""))
            continue
        key, value = frame.split(":", 1)
        frames.append((key, value))
    return frames


def frame_value(frames: Iterable[tuple[str, str]], key: str, default: str = "unknown") -> str:
    for k, value in frames:
        if k == key:
            return value
    return default


def path_bucket(path: str) -> str:
    if not path or path == "unknown":
        return "none"
    bits = [bit for bit in path.split("/") if bit]
    if not bits:
        return path
    if bits[0] in {".agentsight", ".github", "docs", "frontend", "collector", "agentflame", "tests"}:
        return bits[0] if len(bits) == 1 else f"{bits[0]}/{bits[1]}"
    return bits[0]


def clean_tag(tag: str) -> str:
    return re.sub(r"[^a-z0-9]", "", tag.lower()) or "unknown"


def normalize_tag(tag: str) -> str:
    normalized = clean_tag(tag)
    if normalized.endswith("s") and normalized[:-1] in CANONICAL_ALIASES:
        normalized = normalized[:-1]
    return CANONICAL_ALIASES.get(normalized, normalized)


def looks_compound_or_noisy(tag: str) -> bool:
    if len(tag) > 12:
        return True
    if any(piece in tag for piece in NOISE_SUBSTRINGS):
        return True
    return any(
        tag != suffix and (tag.startswith(suffix) or tag.endswith(suffix))
        for suffix in GENERIC_SUFFIXES
        if len(suffix) >= 4
    )


def add_profile(profiles: dict[str, TagProfile], tag: str) -> TagProfile:
    if tag not in profiles:
        profiles[tag] = TagProfile(tag=tag)
    return profiles[tag]


def collect_profiles(report: dict[str, Any], system: Counter[str], token: Counter[str]) -> dict[str, dict[str, TagProfile]]:
    profiles = {"session": {}, "prompt": {}, "llm": {}}

    for session in report.get("sessions") or []:
        session_tag = clean_tag(str(session.get("session_tag") or "unknown"))
        profile = add_profile(profiles["session"], session_tag)
        profile.row_count += 1
        profile.agents[str(session.get("source") or "unknown")] += 1
        for event in session.get("llm_events") or []:
            llm_tag = clean_tag(str(event.get("llm_tag") or "unknown"))
            prompt_tag = clean_tag(str(event.get("prompt_tag") or "unknown"))
            l_profile = add_profile(profiles["llm"], llm_tag)
            l_profile.event_count += 1
            l_profile.token_weight += int(event.get("estimated_tokens") or 0)
            l_profile.sessions[session_tag] += 1
            l_profile.prompts[prompt_tag] += 1
            l_profile.models[str(event.get("model") or "unknown")] += 1

    for prompt in report.get("prompt_tags") or []:
        session_tag = clean_tag(str(prompt.get("session_tag") or "unknown"))
        prompt_tag = clean_tag(str(prompt.get("prompt_tag") or "unknown"))
        p_profile = add_profile(profiles["prompt"], prompt_tag)
        p_profile.row_count += 1
        p_profile.sessions[session_tag] += 1
        p_profile.agents[str(prompt.get("source") or "unknown")] += 1

    for stack, weight in system.items():
        frames = parse_frames(stack)
        session_tag = clean_tag(frame_value(frames, "session"))
        prompt_tag = clean_tag(frame_value(frames, "prompt"))
        process = frame_value(frames, "process", frame_value(frames, "call", "unknown"))
        effect = frame_value(frames, "effect")
        path = path_bucket(frame_value(frames, "path"))
        agent = frame_value(frames, "agent")
        for dimension, tag, other in (
            ("session", session_tag, prompt_tag),
            ("prompt", prompt_tag, session_tag),
        ):
            profile = add_profile(profiles[dimension], tag)
            profile.effect_weight += weight
            profile.processes[process] += weight
            profile.effects[effect] += weight
            profile.paths[path] += weight
            profile.agents[agent] += weight
            if dimension == "session":
                profile.prompts[other] += weight
            else:
                profile.sessions[other] += weight

    for stack, weight in token.items():
        frames = parse_frames(stack)
        call = frame_value(frames, "call")
        if not call.startswith("llm/"):
            continue
        llm_tag = clean_tag(call.split("/", 1)[1])
        profile = add_profile(profiles["llm"], llm_tag)
        profile.token_weight += weight
        profile.sessions[clean_tag(frame_value(frames, "session"))] += weight
        profile.prompts[clean_tag(frame_value(frames, "prompt"))] += weight
        profile.models[frame_value(frames, "model")] += weight
        profile.kinds[frame_value(frames, "kind")] += weight

    return profiles


def cosine(left: Counter[str], right: Counter[str]) -> float:
    if not left or not right:
        return 0.0
    keys = set(left) | set(right)
    dot = sum(left.get(k, 0) * right.get(k, 0) for k in keys)
    norm_left = math.sqrt(sum(v * v for v in left.values()))
    norm_right = math.sqrt(sum(v * v for v in right.values()))
    if not norm_left or not norm_right:
        return 0.0
    return dot / (norm_left * norm_right)


def profile_similarity(left: TagProfile, right: TagProfile, dimension: str) -> float:
    if dimension == "llm":
        parts = [
            (cosine(left.prompts, right.prompts), 0.40),
            (cosine(left.sessions, right.sessions), 0.25),
            (cosine(left.models, right.models), 0.20),
            (cosine(left.kinds, right.kinds), 0.15),
        ]
    else:
        parts = [
            (cosine(left.processes, right.processes), 0.35),
            (cosine(left.effects, right.effects), 0.20),
            (cosine(left.paths, right.paths), 0.25),
            (cosine(left.sessions if dimension == "prompt" else left.prompts,
                    right.sessions if dimension == "prompt" else right.prompts), 0.20),
        ]
    return sum(score * weight for score, weight in parts)


def lexical_score(raw: str, candidate: str) -> float:
    if raw == candidate:
        return 1.0
    if raw.startswith(candidate) or raw.endswith(candidate):
        return 0.86
    if candidate in raw and len(candidate) >= 4:
        return 0.72
    if raw.startswith(candidate[:4]) and len(candidate) >= 5:
        return 0.48
    return 0.0


def discover_heads(profiles: dict[str, TagProfile], dimension: str) -> set[str]:
    total_effect = sum(p.effect_weight for p in profiles.values())
    total_events = sum(p.event_count for p in profiles.values())
    heads: set[str] = set()
    for tag, profile in profiles.items():
        support = profile.support(dimension)
        noisy = looks_compound_or_noisy(tag)
        if dimension == "llm":
            enough = profile.event_count >= max(100, int(total_events * 0.0008)) or profile.token_weight >= 100_000
        elif dimension == "prompt":
            enough = profile.effect_weight >= max(350, int(total_effect * 0.002)) or (
                profile.row_count >= 15 and profile.effect_weight >= 100
            )
        else:
            enough = profile.effect_weight >= max(250, int(total_effect * 0.0015)) or (
                profile.row_count >= 8 and profile.effect_weight >= 100
            )
        if enough and not noisy:
            heads.add(tag)
        if tag in {"refactor", "review", "design", "analyze", "test", "docs", "research"}:
            heads.add(tag)
    for alias_target in CANONICAL_ALIASES.values():
        if alias_target in profiles:
            heads.add(alias_target)
    return heads


def choose_canonical(
    tag: str,
    profile: TagProfile,
    profiles: dict[str, TagProfile],
    heads: set[str],
    dimension: str,
    min_confidence: float,
) -> dict[str, Any]:
    raw_tag = tag
    normalized = normalize_tag(tag)
    if normalized in CANONICAL_ALIASES.values() and normalized in heads and raw_tag != normalized:
        return {
            "raw_tag": raw_tag,
            "canonical_tag": normalized,
            "action": "merge",
            "reason": "alias",
            "confidence": 0.96,
            "profile_similarity": 0.0,
        }

    if raw_tag in heads and not looks_compound_or_noisy(raw_tag):
        return {
            "raw_tag": raw_tag,
            "canonical_tag": raw_tag,
            "action": "keep",
            "reason": "head",
            "confidence": 1.0,
            "profile_similarity": 1.0,
        }

    candidates = sorted(heads)
    best: tuple[float, float, str, str] | None = None
    for candidate in candidates:
        if candidate == raw_tag:
            continue
        cand_profile = profiles.get(candidate)
        if not cand_profile:
            continue
        lex = lexical_score(raw_tag, candidate)
        sim = profile_similarity(profile, cand_profile, dimension)
        support_ratio = min(1.0, math.log1p(cand_profile.support(dimension)) / 10.0)
        score = 0.55 * lex + 0.35 * sim + 0.10 * support_ratio
        if normalized in CANONICAL_ALIASES and CANONICAL_ALIASES[normalized] == candidate:
            score = max(score, 0.95)
        if best is None or score > best[0]:
            reason = "lexical+profile" if lex else "profile"
            best = (score, sim, candidate, reason)

    if best is None:
        return {
            "raw_tag": raw_tag,
            "canonical_tag": raw_tag,
            "action": "keep",
            "reason": "no_candidate",
            "confidence": 0.0,
            "profile_similarity": 0.0,
        }

    score, sim, candidate, reason = best
    if score >= min_confidence:
        action = "merge"
        canonical = candidate
    elif looks_compound_or_noisy(raw_tag) and score >= min_confidence - 0.10:
        action = "review"
        canonical = candidate
    else:
        action = "keep"
        canonical = raw_tag
        reason = "low_confidence"

    return {
        "raw_tag": raw_tag,
        "canonical_tag": canonical,
        "action": action,
        "reason": reason,
        "confidence": round(score, 3),
        "profile_similarity": round(sim, 3),
    }


def build_maps(
    profiles_by_dim: dict[str, dict[str, TagProfile]],
    min_confidence: float,
) -> tuple[dict[str, dict[str, str]], list[dict[str, Any]], dict[str, set[str]]]:
    mappings: dict[str, dict[str, str]] = {}
    rows: list[dict[str, Any]] = []
    heads_by_dim: dict[str, set[str]] = {}
    for dimension, profiles in profiles_by_dim.items():
        heads = discover_heads(profiles, dimension)
        heads_by_dim[dimension] = heads
        mappings[dimension] = {}
        for tag in sorted(profiles):
            decision = choose_canonical(tag, profiles[tag], profiles, heads, dimension, min_confidence)
            canonical = decision["canonical_tag"]
            mappings[dimension][tag] = canonical if decision["action"] == "merge" else tag
            profile = profiles[tag]
            if dimension == "llm":
                primary_support = profile.event_count
            elif dimension in {"session", "prompt"}:
                primary_support = profile.effect_weight or profile.row_count
            else:
                primary_support = profile.support(dimension)
            rows.append(
                {
                    "dimension": dimension,
                    "raw_tag": tag,
                    "canonical_tag": mappings[dimension][tag],
                    "suggested_tag": canonical,
                    "action": decision["action"],
                    "reason": decision["reason"],
                    "confidence": decision["confidence"],
                    "profile_similarity": decision["profile_similarity"],
                    "row_count": profile.row_count,
                    "effect_weight": profile.effect_weight,
                    "event_count": profile.event_count,
                    "token_weight": profile.token_weight,
                    "support": primary_support,
                    "is_head": tag in heads,
                }
            )
    return mappings, rows, heads_by_dim


def canonicalize_system_stack(stack: str, maps: dict[str, dict[str, str]]) -> str:
    out: list[str] = []
    for key, value in parse_frames(stack):
        if key == "session":
            value = maps.get("session", {}).get(clean_tag(value), clean_tag(value))
        elif key == "prompt":
            value = maps.get("prompt", {}).get(clean_tag(value), clean_tag(value))
        out.append(f"{key}:{value}" if value else key)
    return ";".join(out)


def canonicalize_token_stack(stack: str, maps: dict[str, dict[str, str]]) -> str:
    out: list[str] = []
    for key, value in parse_frames(stack):
        if key == "session":
            value = maps.get("session", {}).get(clean_tag(value), clean_tag(value))
        elif key == "prompt":
            value = maps.get("prompt", {}).get(clean_tag(value), clean_tag(value))
        elif key == "call" and value.startswith("llm/"):
            llm_tag = clean_tag(value.split("/", 1)[1])
            value = "llm/" + maps.get("llm", {}).get(llm_tag, llm_tag)
        out.append(f"{key}:{value}" if value else key)
    return ";".join(out)


def canonicalize_counter(source: Counter[str], fn) -> Counter[str]:
    out: Counter[str] = Counter()
    for stack, weight in source.items():
        out[fn(stack)] += weight
    return out


def top_coverage(counter: Counter[str], top_n: int) -> float:
    total = sum(counter.values())
    return pct(sum(v for _, v in counter.most_common(top_n)), total)


def tag_counter_for_dimension(
    profiles: dict[str, TagProfile],
    dimension: str,
    maps: dict[str, dict[str, str]],
    weight_field: str,
) -> tuple[Counter[str], Counter[str]]:
    raw: Counter[str] = Counter()
    canonical: Counter[str] = Counter()
    for tag, profile in profiles.items():
        value = int(getattr(profile, weight_field))
        if not value:
            continue
        raw[tag] += value
        canonical[maps[dimension].get(tag, tag)] += value
    return raw, canonical


def stack_summary(raw: Counter[str], canonical: Counter[str]) -> dict[str, Any]:
    total = sum(raw.values())
    return {
        "raw_unique_stacks": len(raw),
        "canonical_unique_stacks": len(canonical),
        "unique_stack_reduction": len(raw) - len(canonical),
        "unique_stack_reduction_pct": pct(len(raw) - len(canonical), len(raw)),
        "total_weight": total,
        "total_preserved": total == sum(canonical.values()),
        "raw_compression": round(total / len(raw), 3) if raw else 0,
        "canonical_compression": round(total / len(canonical), 3) if canonical else 0,
        "raw_top20_coverage_pct": top_coverage(raw, 20),
        "canonical_top20_coverage_pct": top_coverage(canonical, 20),
    }


def merge_diagnostics(mapping_rows: list[dict[str, Any]]) -> dict[str, Any]:
    diagnostics: dict[str, Any] = {}
    for dimension in sorted({str(row["dimension"]) for row in mapping_rows}):
        dim_rows = [row for row in mapping_rows if row["dimension"] == dimension]
        applied = [row for row in dim_rows if row["action"] == "merge"]
        review = [row for row in dim_rows if row["action"] == "review"]
        by_reason: Counter[str] = Counter(str(row["reason"]) for row in applied)
        support_by_reason: Counter[str] = Counter()
        for row in applied:
            support_by_reason[str(row["reason"])] += int(row["support"])
        profile_sims = sorted(
            float(row["profile_similarity"])
            for row in applied
            if str(row["reason"]) != "alias"
        )
        alias_count = by_reason.get("alias", 0)
        lexical_count = by_reason.get("lexical+profile", 0)
        profile_count = by_reason.get("profile", 0)
        diagnostics[dimension] = {
            "applied_merges": len(applied),
            "review_suggestions": len(review),
            "applied_merges_by_reason": dict(sorted(by_reason.items())),
            "applied_support_by_reason": dict(sorted(support_by_reason.items())),
            "dictionary_alias_merges": alias_count,
            "lexical_profile_merges": lexical_count,
            "profile_only_merges": profile_count,
            "non_alias_profile_similarity": {
                "count": len(profile_sims),
                "min": round(profile_sims[0], 3) if profile_sims else None,
                "p50": round(profile_sims[len(profile_sims) // 2], 3) if profile_sims else None,
                "p90": round(profile_sims[int((len(profile_sims) - 1) * 0.90)], 3) if profile_sims else None,
                "max": round(profile_sims[-1], 3) if profile_sims else None,
            },
        }
    return diagnostics


def dimension_summary(
    dimension: str,
    profiles: dict[str, TagProfile],
    maps: dict[str, dict[str, str]],
    mapping_rows: list[dict[str, Any]],
    weight_field: str,
    long_tail_threshold: int,
) -> dict[str, Any]:
    raw, canonical = tag_counter_for_dimension(profiles, dimension, maps, weight_field)
    dim_rows = [row for row in mapping_rows if row["dimension"] == dimension]
    merged = [row for row in dim_rows if row["action"] == "merge"]
    review = [row for row in dim_rows if row["action"] == "review"]
    raw_tail = sum(v for _, v in raw.items() if v < long_tail_threshold)
    canonical_tail = sum(v for _, v in canonical.items() if v < long_tail_threshold)
    return {
        "dimension": dimension,
        "weight_field": weight_field,
        "raw_unique_tags": len(raw),
        "canonical_unique_tags": len(canonical),
        "unique_tag_reduction": len(raw) - len(canonical),
        "unique_tag_reduction_pct": pct(len(raw) - len(canonical), len(raw)),
        "auto_merged_tags": len(merged),
        "review_suggested_tags": len(review),
        "total_weight": sum(raw.values()),
        "total_preserved": sum(raw.values()) == sum(canonical.values()),
        "raw_top20_coverage_pct": top_coverage(raw, 20),
        "canonical_top20_coverage_pct": top_coverage(canonical, 20),
        "raw_long_tail_weight": raw_tail,
        "canonical_long_tail_weight": canonical_tail,
        "raw_long_tail_weight_pct": pct(raw_tail, sum(raw.values())),
        "canonical_long_tail_weight_pct": pct(canonical_tail, sum(canonical.values())),
        "top_raw": raw.most_common(20),
        "top_canonical": canonical.most_common(20),
    }


def write_mapping_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "dimension",
        "raw_tag",
        "canonical_tag",
        "suggested_tag",
        "action",
        "reason",
        "confidence",
        "profile_similarity",
        "row_count",
        "effect_weight",
        "event_count",
        "token_weight",
        "support",
        "is_head",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def write_counts_csv(path: Path, summaries: dict[str, dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = ["dimension", "kind", "rank", "tag", "count", "share_pct", "unit"]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for dimension, summary in summaries.items():
            total = summary["total_weight"]
            for kind, rows in (("raw", summary["top_raw"]), ("canonical", summary["top_canonical"])):
                for rank, (tag, count) in enumerate(rows, 1):
                    writer.writerow(
                        {
                            "dimension": dimension,
                            "kind": kind,
                            "rank": rank,
                            "tag": tag,
                            "count": count,
                            "share_pct": pct(count, total),
                            "unit": summary["weight_field"],
                        }
                    )


def maybe_write_plots(out_dir: Path, summaries: dict[str, dict[str, Any]], system_summary: dict[str, Any]) -> None:
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except Exception:
        return

    for dimension in ("prompt_effect", "llm_events"):
        summary = summaries[dimension]
        raw = dict(summary["top_raw"][:12])
        canonical = dict(summary["top_canonical"][:12])
        labels = list(dict.fromkeys([*canonical.keys(), *raw.keys()]))[:14]
        raw_values = [raw.get(label, 0) for label in labels]
        canonical_values = [canonical.get(label, 0) for label in labels]
        y = list(range(len(labels)))
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.barh([i + 0.2 for i in y], raw_values, height=0.35, label="raw", color="#9aa0a6")
        ax.barh([i - 0.2 for i in y], canonical_values, height=0.35, label="canonical", color="#3b82f6")
        ax.set_yticks(y)
        ax.set_yticklabels(labels)
        ax.invert_yaxis()
        ax.set_xlabel(summary["weight_field"])
        ax.set_title(f"{dimension}: raw vs canonical top tags")
        ax.legend()
        fig.tight_layout()
        fig.savefig(out_dir / f"{dimension}-raw-vs-canonical.png", dpi=180)
        plt.close(fig)

    fig, ax = plt.subplots(figsize=(7, 4))
    names = ["raw", "canonical"]
    values = [system_summary["raw_unique_stacks"], system_summary["canonical_unique_stacks"]]
    ax.bar(names, values, color=["#9aa0a6", "#16a34a"])
    ax.set_ylabel("unique system stacks")
    ax.set_title("Semantic stack count after canonical tag consolidation")
    for i, value in enumerate(values):
        ax.text(i, value + max(values) * 0.01, f"{value:,}", ha="center")
    fig.tight_layout()
    fig.savefig(out_dir / "system-stack-reduction.png", dpi=180)
    plt.close(fig)


def write_markdown(
    path: Path,
    payload: dict[str, Any],
    mapping_rows: list[dict[str, Any]],
) -> None:
    lines = [
        "# R189 Tag Consolidation",
        "",
        f"Status: `{payload['status']}`",
        "",
        "## Scope",
        "",
        f"- Input: `{payload['input']['agentflame_dir']}`.",
        "- Raw agent traces are not read directly or modified.",
        "- Raw one-word tags are preserved; canonical tags are a display/aggregation layer.",
        "",
        "## Headline Metrics",
        "",
    ]
    for name, summary in payload["dimensions"].items():
        lines.extend(
            [
                f"### {name}",
                "",
                f"- Unique tags: {summary['raw_unique_tags']} -> {summary['canonical_unique_tags']} "
                f"({summary['unique_tag_reduction_pct']}% reduction).",
                f"- Top-20 coverage: {summary['raw_top20_coverage_pct']}% -> "
                f"{summary['canonical_top20_coverage_pct']}%.",
                f"- Long-tail weight: {summary['raw_long_tail_weight_pct']}% -> "
                f"{summary['canonical_long_tail_weight_pct']}%.",
                f"- Auto-merged tags: {summary['auto_merged_tags']}; review suggestions: "
                f"{summary['review_suggested_tags']}.",
                "",
            ]
        )
    system = payload["system_stack_consolidation"]
    token = payload["token_stack_consolidation"]
    lines.extend(
        [
            "## Stack Aggregation",
            "",
            f"- System stacks: {system['raw_unique_stacks']} -> {system['canonical_unique_stacks']} "
            f"({system['unique_stack_reduction_pct']}% reduction), total preserved: "
            f"{system['total_preserved']}.",
            f"- Token stacks: {token['raw_unique_stacks']} -> {token['canonical_unique_stacks']} "
            f"({token['unique_stack_reduction_pct']}% reduction), total preserved: "
            f"{token['total_preserved']}.",
            "",
            "## Merge Mechanism",
            "",
            "| dimension | dictionary aliases | lexical+profile | profile-only | review suggestions | non-alias profile sim p50/p90 |",
            "|---|---:|---:|---:|---:|---:|",
        ]
    )
    for dimension, diag in sorted(payload["merge_diagnostics"].items()):
        sims = diag["non_alias_profile_similarity"]
        lines.append(
            f"| {dimension} | {diag['dictionary_alias_merges']} | "
            f"{diag['lexical_profile_merges']} | {diag['profile_only_merges']} | "
            f"{diag['review_suggestions']} | {sims['p50']}/{sims['p90']} |"
        )
    lines.extend(
        [
            "",
            "## High-Confidence Example Merges",
            "",
            "| dimension | raw | canonical | reason | confidence | support |",
            "|---|---|---|---|---:|---:|",
        ]
    )
    examples = [
        row
        for row in mapping_rows
        if row["action"] == "merge" and row["raw_tag"] != row["canonical_tag"]
    ]
    examples.sort(key=lambda row: (-int(row["support"]), str(row["dimension"]), str(row["raw_tag"])))
    for row in examples[:30]:
        lines.append(
            f"| {row['dimension']} | `{row['raw_tag']}` | `{row['canonical_tag']}` | "
            f"{row['reason']} | {row['confidence']} | {row['support']} |"
        )
    lines.extend(
        [
            "",
            "## Review Boundary",
            "",
            "R189 is not human tag adequacy evidence. It shows whether noisy raw tags can be "
            "consolidated into a more stable profiling vocabulary while keeping raw tags auditable. "
            "Human C6 labels are still required before claiming semantic correctness.",
            "",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def run(agentflame_dir: Path, out_dir: Path, min_confidence: float) -> dict[str, Any]:
    report_path = agentflame_dir / "agentflame.json"
    system_path = agentflame_dir / "semantic-system.folded.txt"
    token_path = agentflame_dir / "semantic-token.folded.txt"
    report = read_json(report_path)
    system = read_folded(system_path)
    token = read_folded(token_path)
    profiles = collect_profiles(report, system, token)
    maps, mapping_rows, heads = build_maps(profiles, min_confidence)

    canonical_system = canonicalize_counter(
        system,
        lambda stack: canonicalize_system_stack(stack, maps),
    )
    canonical_token = canonicalize_counter(
        token,
        lambda stack: canonicalize_token_stack(stack, maps),
    )

    out_dir.mkdir(parents=True, exist_ok=True)
    write_folded(out_dir / "canonical-semantic-system.folded.txt", canonical_system)
    write_folded(out_dir / "canonical-semantic-token.folded.txt", canonical_token)
    write_mapping_csv(out_dir / "canonical-tag-map-r189.csv", mapping_rows)

    dimensions = {
        "session_effect": dimension_summary(
            "session", profiles["session"], maps, mapping_rows, "effect_weight", 100
        ),
        "prompt_effect": dimension_summary(
            "prompt", profiles["prompt"], maps, mapping_rows, "effect_weight", 100
        ),
        "prompt_rows": dimension_summary(
            "prompt", profiles["prompt"], maps, mapping_rows, "row_count", 3
        ),
        "llm_events": dimension_summary(
            "llm", profiles["llm"], maps, mapping_rows, "event_count", 10
        ),
        "llm_tokens": dimension_summary(
            "llm", profiles["llm"], maps, mapping_rows, "token_weight", 10_000
        ),
    }
    write_counts_csv(out_dir / "canonical-tag-counts-r189.csv", dimensions)

    payload = {
        "schema_version": 1,
        "run_id": "R189",
        "status": "tag_consolidation_completed",
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "input": {
            "agentflame_dir": rel(agentflame_dir),
            "report": rel(report_path),
            "report_sha256": sha256_file(report_path),
            "system_folded": rel(system_path),
            "system_folded_sha256": sha256_file(system_path),
            "token_folded": rel(token_path),
            "token_folded_sha256": sha256_file(token_path),
            "raw_trace_policy": "read existing generated AgentFlame artifacts only; do not mutate raw traces",
        },
        "method": {
            "raw_tags_preserved": True,
            "canonical_layer_only": True,
            "head_tag_discovery": "high-support tags become dimension-local canonical candidates",
            "merge_rule": "auto-merge only when alias/lexical/profile confidence passes threshold",
            "min_confidence": min_confidence,
            "review_rows_are_not_auto_applied": True,
        },
        "heads": {dimension: sorted(values) for dimension, values in heads.items()},
        "dimensions": dimensions,
        "system_stack_consolidation": stack_summary(system, canonical_system),
        "token_stack_consolidation": stack_summary(token, canonical_token),
        "merge_diagnostics": merge_diagnostics(mapping_rows),
        "artifacts": {
            "canonical_system_folded": rel(out_dir / "canonical-semantic-system.folded.txt"),
            "canonical_token_folded": rel(out_dir / "canonical-semantic-token.folded.txt"),
            "mapping_csv": rel(out_dir / "canonical-tag-map-r189.csv"),
            "counts_csv": rel(out_dir / "canonical-tag-counts-r189.csv"),
            "summary_md": rel(out_dir / "tag-consolidation-r189.md"),
        },
        "claim_boundary": (
            "R189 supports a tag-noise and aggregation mechanism claim only. It does not "
            "replace R124 human adequacy labels and must not be cited as semantic correctness."
        ),
        "provenance": {
            "repo_commit": git(["rev-parse", "HEAD"]),
            "repo_dirty": bool(git(["status", "--short"])),
            "script_sha256": sha256_file(Path(__file__).resolve()),
        },
    }

    write_json(out_dir / "tag-consolidation-r189.json", payload)
    write_markdown(out_dir / "tag-consolidation-r189.md", payload, mapping_rows)
    maybe_write_plots(out_dir, dimensions, payload["system_stack_consolidation"])
    return payload


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--agentflame-dir", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--min-confidence", type=float, default=0.72)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    payload = run(args.agentflame_dir, args.out_dir, args.min_confidence)
    print(args.out_dir)
    print(
        "prompt_effect",
        payload["dimensions"]["prompt_effect"]["raw_unique_tags"],
        "->",
        payload["dimensions"]["prompt_effect"]["canonical_unique_tags"],
    )
    print(
        "llm_events",
        payload["dimensions"]["llm_events"]["raw_unique_tags"],
        "->",
        payload["dimensions"]["llm_events"]["canonical_unique_tags"],
    )
    print(
        "system_stacks",
        payload["system_stack_consolidation"]["raw_unique_stacks"],
        "->",
        payload["system_stack_consolidation"]["canonical_unique_stacks"],
    )


if __name__ == "__main__":
    main()
