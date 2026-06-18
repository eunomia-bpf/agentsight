#!/usr/bin/env python3
"""R225: timestamp-derived prompt-span duration baseline.

This run reads generated R170 AgentFlame artifacts only. It does not read raw
Codex/Claude traces, call an LLM, or synthesize user-study outcomes. The goal is
to make the span-duration baseline boundary concrete: historical artifacts have
prompt/tool/LLM timestamps, but tool and LLM calls do not carry start/end spans.
Therefore this script reconstructs prompt wall-clock intervals from prompt
timestamps and compares that duration-weighted view with the existing
system-effect folded profile. These intervals may include idle/user-wait time and
must not be interpreted as active tool or LLM runtime.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import subprocess
from collections import Counter, defaultdict
from pathlib import Path
from statistics import median
from typing import Any

from semantic_tag_flamegraph import render_svg, write_folded


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[1]
DEFAULT_AGENTFLAME = REPO_ROOT / ".agentsight" / "agentflame" / "r170-full-current" / "agentflame.json"
DEFAULT_SYSTEM_FOLDED = REPO_ROOT / ".agentsight" / "agentflame" / "r170-full-current" / "semantic-system.folded.txt"
DEFAULT_OUT = SCRIPT_DIR / "out" / "prompt-span-duration-r225"

TOP_LIMIT = 20


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT.resolve()))
    except Exception:
        return str(path)


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


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def pct(part: float | int, whole: float | int) -> float:
    return round(100.0 * float(part) / float(whole), 3) if whole else 0.0


def hours(ms: float | int) -> float:
    return round(float(ms) / 3_600_000.0, 3)


def as_int(value: Any) -> int | None:
    if value in (None, ""):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def parse_folded_line(line: str) -> tuple[str, int]:
    stack, _, weight = line.rstrip("\n").rpartition(" ")
    if not stack or not weight.isdigit():
        raise ValueError(f"invalid folded line: {line[:160]}")
    return stack, int(weight)


def read_effect_weight_by_prompt(path: Path) -> tuple[Counter[str], int, int]:
    by_prompt: Counter[str] = Counter()
    total = 0
    unique = 0
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            stack, weight = parse_folded_line(line)
            unique += 1
            total += weight
            prompt = "unknown"
            for frame in stack.split(";"):
                if frame.startswith("prompt:"):
                    prompt = frame.split(":", 1)[1]
                    break
            by_prompt[prompt] += weight
    return by_prompt, total, unique


def expanded_effect_weights_from_report(
    report: dict[str, Any],
) -> tuple[Counter[str], Counter[str], int, int, int]:
    full: Counter[str] = Counter()
    covered: Counter[str] = Counter()
    full_total = 0
    covered_total = 0
    covered_sessions = 0
    for session in report.get("sessions") or []:
        covered_indices = {
            as_int(prompt.get("index"))
            for prompt in session.get("prompts") or []
            if as_int(prompt.get("index")) is not None and as_int(prompt.get("ts_ms")) is not None
        }
        covered_indices.discard(None)
        if covered_indices:
            covered_sessions += 1
        for event in session.get("tool_events") or []:
            weight = len(event.get("path_groups") or []) or len(event.get("domains") or []) or 1
            prompt_tag = str(event.get("prompt_tag") or "unknown")
            full[prompt_tag] += weight
            full_total += weight
            if as_int(event.get("prompt_index")) in covered_indices:
                covered[prompt_tag] += weight
                covered_total += weight
    return full, covered, full_total, covered_total, covered_sessions


def rank_map(counter: Counter[str]) -> dict[str, int]:
    return {
        key: rank
        for rank, (key, _value) in enumerate(
            sorted(counter.items(), key=lambda item: (-item[1], item[0])), 1
        )
    }


def spearman_by_rank(left: Counter[str], right: Counter[str]) -> float | None:
    keys = sorted(set(left) | set(right))
    if len(keys) < 2:
        return None
    left_rank = rank_map(left)
    right_rank = rank_map(right)
    missing_left = len(left_rank) + 1
    missing_right = len(right_rank) + 1
    xs = [left_rank.get(key, missing_left) for key in keys]
    ys = [right_rank.get(key, missing_right) for key in keys]
    mean_x = sum(xs) / len(xs)
    mean_y = sum(ys) / len(ys)
    num = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys))
    den_x = math.sqrt(sum((x - mean_x) ** 2 for x in xs))
    den_y = math.sqrt(sum((y - mean_y) ** 2 for y in ys))
    if den_x == 0 or den_y == 0:
        return None
    return round(num / (den_x * den_y), 3)


def top_set(counter: Counter[str], limit: int) -> set[str]:
    return {key for key, _value in counter.most_common(limit)}


def session_last_ts(session: dict[str, Any]) -> int | None:
    timestamps: list[int] = []
    for field in ["start_ts_ms"]:
        value = as_int(session.get(field))
        if value is not None:
            timestamps.append(value)
    for prompt in session.get("prompts") or []:
        value = as_int(prompt.get("ts_ms"))
        if value is not None:
            timestamps.append(value)
    for event in session.get("tool_events") or []:
        value = as_int(event.get("ts_ms"))
        if value is not None:
            timestamps.append(value)
    for event in session.get("llm_events") or []:
        value = as_int(event.get("ts_ms"))
        if value is not None:
            timestamps.append(value)
    return max(timestamps) if timestamps else None


def prompt_event_counts(session: dict[str, Any]) -> tuple[Counter[int], Counter[int]]:
    tools: Counter[int] = Counter()
    llms: Counter[int] = Counter()
    for event in session.get("tool_events") or []:
        idx = as_int(event.get("prompt_index"))
        if idx is not None:
            tools[idx] += 1
    for event in session.get("llm_events") or []:
        idx = as_int(event.get("prompt_index"))
        if idx is not None:
            llms[idx] += 1
    return tools, llms


def build_prompt_spans(report: dict[str, Any]) -> tuple[list[dict[str, Any]], Counter[str]]:
    spans: list[dict[str, Any]] = []
    folded: Counter[str] = Counter()

    for session_ordinal, session in enumerate(report.get("sessions") or []):
        prompts = [
            prompt
            for prompt in (session.get("prompts") or [])
            if as_int(prompt.get("ts_ms")) is not None and as_int(prompt.get("index")) is not None
        ]
        prompts.sort(key=lambda item: (as_int(item.get("ts_ms")) or 0, as_int(item.get("index")) or 0))
        if not prompts:
            continue

        last_ts = session_last_ts(session)
        tools_by_prompt, llms_by_prompt = prompt_event_counts(session)
        agent = str(session.get("source") or "unknown")
        session_tag = str(session.get("session_tag") or "unknown")
        session_identity = "|".join(
            [
                str(session.get("source") or ""),
                str(session.get("agent_sight_session_id") or ""),
                str(session.get("session_id") or ""),
                str(session.get("session_file") or ""),
                str(session_ordinal),
            ]
        )
        session_id_hash = hashlib.sha256(session_identity.encode("utf-8")).hexdigest()[:12]

        for pos, prompt in enumerate(prompts):
            start = as_int(prompt.get("ts_ms"))
            idx = as_int(prompt.get("index"))
            if start is None or idx is None:
                continue

            next_start = None
            for later in prompts[pos + 1 :]:
                candidate = as_int(later.get("ts_ms"))
                if candidate is not None and candidate > start:
                    next_start = candidate
                    break
            end = next_start if next_start is not None else last_ts
            if end is None or end < start:
                end = start

            duration_ms = max(0, end - start)
            prompt_tag = str(prompt.get("tag") or "unknown")
            stack = (
                f"project:agentsight;agent:{agent};session:{session_tag};"
                f"prompt:{prompt_tag};span:prompt"
            )
            if duration_ms > 0:
                folded[stack] += duration_ms
            spans.append(
                {
                    "agent": agent,
                    "session_id_hash": session_id_hash,
                    "session_tag": session_tag,
                    "prompt_index": idx,
                    "prompt_tag": prompt_tag,
                    "start_ts_ms": start,
                    "end_ts_ms": end,
                    "duration_ms": duration_ms,
                    "duration_s": round(duration_ms / 1000.0, 3),
                    "tool_events": tools_by_prompt[idx],
                    "llm_events": llms_by_prompt[idx],
                    "span_stack": stack,
                    "end_source": "next_prompt" if next_start is not None else "session_last_event",
                }
            )

    return spans, folded


def project_prompt_only(full: Counter[str]) -> Counter[str]:
    out: Counter[str] = Counter()
    for stack, weight in full.items():
        frames = []
        for frame in stack.split(";"):
            if frame.startswith(("project:", "agent:", "prompt:", "span:")):
                frames.append(frame)
        out[";".join(frames)] += weight
    return out


def project_no_semantic(full: Counter[str]) -> Counter[str]:
    out: Counter[str] = Counter()
    for stack, weight in full.items():
        frames = []
        for frame in stack.split(";"):
            if frame.startswith(("project:", "agent:", "span:")):
                frames.append(frame)
        out[";".join(frames)] += weight
    return out


def prompt_duration_counter(spans: list[dict[str, Any]]) -> Counter[str]:
    out: Counter[str] = Counter()
    for span in spans:
        out[str(span["prompt_tag"])] += int(span["duration_ms"])
    return out


def comparison_rows(duration: Counter[str], effect: Counter[str], limit: int = TOP_LIMIT) -> list[dict[str, Any]]:
    duration_total = sum(duration.values())
    effect_total = sum(effect.values())
    duration_rank = rank_map(duration)
    effect_rank = rank_map(effect)
    keys = sorted(set(duration) | set(effect))
    rows = []
    for key in keys:
        duration_weight = duration.get(key, 0)
        effect_weight = effect.get(key, 0)
        duration_share = pct(duration_weight, duration_total)
        effect_share = pct(effect_weight, effect_total)
        rows.append(
            {
                "prompt_tag": key,
                "duration_rank": duration_rank.get(key, ""),
                "effect_rank": effect_rank.get(key, ""),
                "duration_ms": duration_weight,
                "duration_h": hours(duration_weight),
                "duration_share_pct": duration_share,
                "effect_weight": effect_weight,
                "effect_share_pct": effect_share,
                "abs_share_delta_pct": round(abs(duration_share - effect_share), 3),
            }
        )
    rows.sort(key=lambda row: (-row["abs_share_delta_pct"], str(row["prompt_tag"])))
    return rows[:limit]


def top_rows(
    duration: Counter[str],
    effect: Counter[str],
    primary: str,
    limit: int = TOP_LIMIT,
) -> list[dict[str, Any]]:
    primary_counter = duration if primary == "duration" else effect
    duration_total = sum(duration.values())
    effect_total = sum(effect.values())
    duration_rank = rank_map(duration)
    effect_rank = rank_map(effect)
    rows = []
    for rank, (tag, value) in enumerate(primary_counter.most_common(limit), 1):
        rows.append(
            {
                "rank": rank,
                "prompt_tag": tag,
                "duration_rank": duration_rank.get(tag, ""),
                "effect_rank": effect_rank.get(tag, ""),
                "duration_ms": duration.get(tag, 0),
                "duration_h": hours(duration.get(tag, 0)),
                "duration_share_pct": pct(duration.get(tag, 0), duration_total),
                "effect_weight": effect.get(tag, 0),
                "effect_share_pct": pct(effect.get(tag, 0), effect_total),
                "primary_metric": primary,
                "primary_value": value,
            }
        )
    return rows


def counter_summary(counter: Counter[str], metric: str) -> dict[str, Any]:
    total = sum(counter.values())
    weights = list(counter.values())
    return {
        "metric": metric,
        "total_weight": total,
        "total_hours": hours(total) if metric == "milliseconds" else None,
        "unique_stacks": len(counter),
        "compression_ratio": round(total / len(counter), 3) if counter else 0,
        "max_stack_reuse": max(weights) if weights else 0,
        "median_stack_weight": median(weights) if weights else 0,
    }


def write_markdown(
    path: Path,
    summary: dict[str, Any],
    top_duration: list[dict[str, Any]],
    top_effect: list[dict[str, Any]],
    disagreements: list[dict[str, Any]],
) -> None:
    lines = [
        "# R225 Prompt-Span Duration Baseline",
        "",
        "Status: `done/prompt-span-duration-baseline`",
        "",
        "This artifact reconstructs prompt-level span durations from R170 timestamps. "
        "It is a duration-weighted baseline over generated AgentFlame artifacts only; "
        "it does not provide true tool/LLM start-end spans or user-study outcomes. "
        "The duration is a prompt wall-clock interval and may include idle/user-wait time.",
        "",
        "## Summary",
        "",
        f"- Prompt spans reconstructed: {summary['prompt_spans_total']}",
        f"- Nonzero prompt spans: {summary['prompt_spans_nonzero']}",
        f"- Sessions with prompt spans: {summary['sessions_with_prompt_spans']}/{summary['sessions_total']}",
        f"- Total prompt duration: {summary['total_prompt_duration_h']} h",
        f"- Covered effect observations compared: {summary['covered_effect_total_weight']}/{summary['effect_total_weight']} ({summary['covered_effect_share_pct']}%)",
        f"- Expanded effects match folded prompt totals: {summary['expanded_effect_by_prompt_matches_folded']}",
        f"- Top-10 duration/effect overlap: {summary['top10_overlap_count']}/10",
        f"- Top-20 duration/effect overlap: {summary['top20_overlap_count']}/20",
        f"- Prompt-tag Spearman rank correlation: {summary['spearman_rank_correlation']}",
        "",
        "## Top Duration Tags",
        "",
        "| Rank | Prompt tag | Duration h | Duration % | Effect rank | Effect % |",
        "|---:|---|---:|---:|---:|---:|",
    ]
    for row in top_duration[:10]:
        lines.append(
            f"| {row['rank']} | `{row['prompt_tag']}` | {row['duration_h']} | "
            f"{row['duration_share_pct']} | {row['effect_rank']} | {row['effect_share_pct']} |"
        )

    lines.extend(
        [
            "",
            "## Top Effect Tags",
            "",
            "| Rank | Prompt tag | Effect weight | Effect % | Duration rank | Duration % |",
            "|---:|---|---:|---:|---:|---:|",
        ]
    )
    for row in top_effect[:10]:
        lines.append(
            f"| {row['rank']} | `{row['prompt_tag']}` | {row['effect_weight']} | "
            f"{row['effect_share_pct']} | {row['duration_rank']} | {row['duration_share_pct']} |"
        )

    lines.extend(
        [
            "",
            "## Largest Share Disagreements",
            "",
            "| Prompt tag | Duration % | Effect % | Delta pp | Duration rank | Effect rank |",
            "|---|---:|---:|---:|---:|---:|",
        ]
    )
    for row in disagreements[:10]:
        lines.append(
            f"| `{row['prompt_tag']}` | {row['duration_share_pct']} | {row['effect_share_pct']} | "
            f"{row['abs_share_delta_pct']} | {row['duration_rank']} | {row['effect_rank']} |"
        )

    lines.extend(
        [
            "",
            "## Claim Boundary",
            "",
            "- Supports: a concrete prompt-span duration baseline and evidence that duration-weighted views differ from system-effect-count profiles.",
            "- Does not support: C5 user utility, C6 tag adequacy, active runtime, true tool/LLM duration spans, or replacement of effect-count profiling.",
            "- Next gate: collect R142 participant responses using this baseline only after updating the preregistered packet.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--agentflame", type=Path, default=DEFAULT_AGENTFLAME)
    parser.add_argument("--system-folded", type=Path, default=DEFAULT_SYSTEM_FOLDED)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()

    for path in [args.agentflame, args.system_folded]:
        if not path.exists():
            raise FileNotFoundError(path)

    args.out_dir.mkdir(parents=True, exist_ok=True)
    report = json.loads(args.agentflame.read_text(encoding="utf-8"))
    folded_effect_by_prompt, effect_total, effect_unique = read_effect_weight_by_prompt(args.system_folded)
    (
        expanded_effect_by_prompt,
        covered_effect_by_prompt,
        expanded_effect_total,
        covered_effect_total,
        covered_effect_sessions,
    ) = expanded_effect_weights_from_report(report)
    if expanded_effect_total != effect_total:
        raise AssertionError(
            f"expanded effect total {expanded_effect_total} does not match folded total {effect_total}"
        )
    if expanded_effect_by_prompt != folded_effect_by_prompt:
        raise AssertionError("expanded effect-by-prompt counts do not match folded counts")
    spans, duration_full = build_prompt_spans(report)
    duration_prompt = prompt_duration_counter(spans)
    duration_prompt_only = project_prompt_only(duration_full)
    duration_no_semantic = project_no_semantic(duration_full)

    write_folded(args.out_dir / "prompt-span-duration.folded.txt", duration_full)
    write_folded(args.out_dir / "prompt-span-duration-prompt-only.folded.txt", duration_prompt_only)
    write_folded(args.out_dir / "prompt-span-duration-nosemantic.folded.txt", duration_no_semantic)
    render_svg(
        duration_full,
        "Prompt-Span Duration Flamegraph",
        "R225 timestamp-derived prompt spans; width = reconstructed prompt duration in milliseconds.",
        "ms",
        args.out_dir / "prompt-span-duration.svg",
    )

    top_duration = top_rows(duration_prompt, covered_effect_by_prompt, "duration")
    top_effect = top_rows(duration_prompt, covered_effect_by_prompt, "effect")
    disagreements = comparison_rows(duration_prompt, covered_effect_by_prompt)
    end_source_counts = Counter(str(span["end_source"]) for span in spans)

    duration_top10 = top_set(duration_prompt, 10)
    effect_top10 = top_set(covered_effect_by_prompt, 10)
    duration_top20 = top_set(duration_prompt, 20)
    effect_top20 = top_set(covered_effect_by_prompt, 20)
    span_durations = [int(span["duration_ms"]) for span in spans]
    nonzero = [value for value in span_durations if value > 0]

    summary = {
        "run_id": "R225",
        "status": "done/prompt-span-duration-baseline",
        "git_commit": git(["rev-parse", "HEAD"]),
        "git_branch": git(["branch", "--show-current"]),
        "inputs": {
            "agentflame_json": rel(args.agentflame),
            "agentflame_json_sha256": sha256_file(args.agentflame),
            "semantic_system_folded": rel(args.system_folded),
            "semantic_system_folded_sha256": sha256_file(args.system_folded),
        },
        "prompt_spans_total": len(spans),
        "prompt_spans_nonzero": len(nonzero),
        "prompt_spans_zero_duration": len(spans) - len(nonzero),
        "span_end_policy": "end at next later prompt timestamp, otherwise session last observed event timestamp",
        "span_end_source_counts": dict(sorted(end_source_counts.items())),
        "prompt_span_duration_is_wall_clock_interval": True,
        "prompt_span_may_include_idle_or_user_wait": True,
        "sessions_total": len(report.get("sessions") or []),
        "sessions_with_prompt_spans": len({span["session_id_hash"] for span in spans}),
        "sessions_with_covered_effects": covered_effect_sessions,
        "total_prompt_duration_ms": sum(duration_prompt.values()),
        "total_prompt_duration_h": hours(sum(duration_prompt.values())),
        "median_prompt_duration_s": round(median(span_durations) / 1000.0, 3) if span_durations else 0,
        "median_nonzero_prompt_duration_s": round(median(nonzero) / 1000.0, 3) if nonzero else 0,
        "max_prompt_duration_h": hours(max(nonzero) if nonzero else 0),
        "duration_full": counter_summary(duration_full, "milliseconds"),
        "duration_prompt_only": counter_summary(duration_prompt_only, "milliseconds"),
        "duration_no_semantic": counter_summary(duration_no_semantic, "milliseconds"),
        "effect_total_weight": effect_total,
        "effect_unique_stacks": effect_unique,
        "expanded_effect_total_weight": expanded_effect_total,
        "covered_effect_total_weight": covered_effect_total,
        "covered_effect_share_pct": pct(covered_effect_total, effect_total),
        "expanded_effect_total_matches_folded": expanded_effect_total == effect_total,
        "expanded_effect_by_prompt_matches_folded": expanded_effect_by_prompt == folded_effect_by_prompt,
        "duration_effect_comparison_scope": "prompt spans and covered prompt-index system effects reconstructed from the same R170 agentflame.json; expanded effect totals are checked against semantic-system.folded.txt",
        "top10_overlap_count": len(duration_top10 & effect_top10),
        "top10_duration_only": sorted(duration_top10 - effect_top10),
        "top10_effect_only": sorted(effect_top10 - duration_top10),
        "top20_overlap_count": len(duration_top20 & effect_top20),
        "spearman_rank_correlation": spearman_by_rank(duration_prompt, covered_effect_by_prompt),
        "true_tool_or_llm_duration_supported": False,
        "supports_c5_user_utility": False,
        "supports_c6_tag_adequacy": False,
        "claim_boundary": (
            "R225 reconstructs prompt-span durations from timestamps only. "
            "It is a concrete prompt wall-clock duration baseline artifact, "
            "not active runtime, not a true tool/LLM span-duration trace, and "
            "not a user-outcome result."
        ),
        "outputs": {
            "summary_json": rel(args.out_dir / "prompt-span-duration-r225.json"),
            "summary_md": rel(args.out_dir / "prompt-span-duration-r225.md"),
            "top_duration_csv": rel(args.out_dir / "top-duration-tags-r225.csv"),
            "top_effect_csv": rel(args.out_dir / "top-effect-tags-r225.csv"),
            "disagreement_csv": rel(args.out_dir / "duration-effect-disagreement-r225.csv"),
            "duration_folded": rel(args.out_dir / "prompt-span-duration.folded.txt"),
            "duration_svg": rel(args.out_dir / "prompt-span-duration.svg"),
        },
    }

    fields = [
        "rank",
        "prompt_tag",
        "duration_rank",
        "effect_rank",
        "duration_ms",
        "duration_h",
        "duration_share_pct",
        "effect_weight",
        "effect_share_pct",
        "primary_metric",
        "primary_value",
    ]
    write_csv(args.out_dir / "top-duration-tags-r225.csv", top_duration, fields)
    write_csv(args.out_dir / "top-effect-tags-r225.csv", top_effect, fields)
    write_csv(
        args.out_dir / "duration-effect-disagreement-r225.csv",
        disagreements,
        [
            "prompt_tag",
            "duration_rank",
            "effect_rank",
            "duration_ms",
            "duration_h",
            "duration_share_pct",
            "effect_weight",
            "effect_share_pct",
            "abs_share_delta_pct",
        ],
    )
    write_csv(
        args.out_dir / "prompt-spans-r225.csv",
        spans,
        [
            "agent",
            "session_id_hash",
            "session_tag",
            "prompt_index",
            "prompt_tag",
            "start_ts_ms",
            "end_ts_ms",
            "duration_ms",
            "duration_s",
            "tool_events",
            "llm_events",
            "end_source",
            "span_stack",
        ],
    )
    write_json(args.out_dir / "prompt-span-duration-r225.json", summary)
    write_markdown(
        args.out_dir / "prompt-span-duration-r225.md",
        summary,
        top_duration,
        top_effect,
        disagreements,
    )
    print(
        json.dumps(
            {
                "run_id": "R225",
                "prompt_spans": summary["prompt_spans_total"],
                "duration_hours": summary["total_prompt_duration_h"],
                "top10_overlap": summary["top10_overlap_count"],
                "spearman": summary["spearman_rank_correlation"],
                "true_tool_or_llm_duration_supported": False,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
