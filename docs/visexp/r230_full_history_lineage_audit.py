#!/usr/bin/env python3
"""R230: full-history projection-lineage audit.

This experiment reads the generated R170 AgentFlame report and folded stacks.
It does not read raw Codex/Claude session files, does not call an LLM, and does
not claim live eBPF exact provenance. The goal is narrower: check whether the
full-history report's system-effect projection carries semantic session/prompt
tag frames plus call/effect frames, and separately report where raw event-local
semantic tags drift from prompt-row tags.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import subprocess
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[1]
DEFAULT_AGENTFLAME = REPO_ROOT / ".agentsight" / "agentflame" / "r170-full-current" / "agentflame.json"
DEFAULT_SEMANTIC_FOLDED = (
    REPO_ROOT / ".agentsight" / "agentflame" / "r170-full-current" / "semantic-system.folded.txt"
)
DEFAULT_R170_JSON = SCRIPT_DIR / "out" / "full-history-r170.json"
DEFAULT_R225_JSON = SCRIPT_DIR / "out" / "prompt-span-duration-r225" / "prompt-span-duration-r225.json"
DEFAULT_OUT_DIR = SCRIPT_DIR / "out" / "full-history-lineage-r230"

REQUIRED_SYSTEM_FRAMES = ("project", "agent", "session", "prompt", "call", "effect", "status")


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


def sha256_file(path: Path) -> str | None:
    if not path.exists():
        return None
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


def pct(part: int | float, whole: int | float) -> float:
    return round(100.0 * float(part) / float(whole), 3) if whole else 0.0


def stable_hash(value: Any) -> str:
    text = "" if value is None else str(value)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:12]


def as_int(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def event_weight(event: dict[str, Any]) -> int:
    return len(event.get("path_groups") or []) or len(event.get("domains") or []) or 1


def parse_folded_line(line: str) -> tuple[str, int]:
    stack, _, weight = line.rstrip("\n").rpartition(" ")
    if not stack or not weight.isdigit():
        raise ValueError(f"invalid folded line: {line[:160]}")
    return stack, int(weight)


def stack_fields(stack: str) -> dict[str, str]:
    fields: dict[str, str] = {}
    for frame in stack.split(";"):
        if ":" in frame:
            key, value = frame.split(":", 1)
            fields[key] = value
    return fields


def audit_folded(path: Path) -> dict[str, Any]:
    total_weight = 0
    unique_stacks = 0
    missing_weight: Counter[str] = Counter()
    effect_weight: Counter[str] = Counter()
    agent_weight: Counter[str] = Counter()
    session_prompt_pairs: set[tuple[str, str]] = set()
    sample_missing: list[dict[str, Any]] = []

    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            stack, weight = parse_folded_line(line)
            unique_stacks += 1
            total_weight += weight
            fields = stack_fields(stack)
            for required in REQUIRED_SYSTEM_FRAMES:
                if not fields.get(required):
                    missing_weight[required] += weight
                    if len(sample_missing) < 10:
                        sample_missing.append(
                            {
                                "missing": required,
                                "weight": weight,
                                "stack_hash": stable_hash(stack),
                            }
                        )
            effect_weight[fields.get("effect", "missing")] += weight
            agent_weight[fields.get("agent", "missing")] += weight
            if fields.get("session") and fields.get("prompt"):
                session_prompt_pairs.add((fields["session"], fields["prompt"]))

    return {
        "unique_stacks": unique_stacks,
        "total_weight": total_weight,
        "required_frames": list(REQUIRED_SYSTEM_FRAMES),
        "missing_weight_by_frame": dict(missing_weight),
        "missing_total_weight": sum(missing_weight.values()),
        "effect_weight": dict(effect_weight),
        "agent_weight": dict(agent_weight),
        "session_prompt_tag_pair_count": len(session_prompt_pairs),
        "sample_missing": sample_missing,
    }


def prompt_index_info(session: dict[str, Any]) -> tuple[dict[int, str], set[int], int]:
    out: dict[int, str] = {}
    counts: Counter[int] = Counter()
    for prompt in session.get("prompts") or []:
        index = as_int(prompt.get("index"))
        if index is not None:
            counts[index] += 1
            out[index] = str(prompt.get("tag") or "unknown")
    duplicates = {index for index, count in counts.items() if count > 1}
    return out, duplicates, len(session.get("prompts") or [])


def sample_row(
    *,
    kind: str,
    session: dict[str, Any],
    event: dict[str, Any],
    prompt_index: Any,
    prompt_row_tag: str,
    reason: str,
    weight: int = 1,
) -> dict[str, Any]:
    return {
        "kind": kind,
        "reason": reason,
        "source": session.get("source") or "unknown",
        "session_id_hash": stable_hash(session.get("session_id")),
        "session_tag": session.get("session_tag") or "unknown",
        "prompt_index": prompt_index,
        "prompt_row_tag": prompt_row_tag,
        "event_prompt_tag": event.get("prompt_tag") or "",
        "tool_name": event.get("tool_name") or "",
        "command_name": event.get("command_name") or "",
        "effect": event.get("effect") or "",
        "status": event.get("status") or "",
        "llm_tag": event.get("llm_tag") or "",
        "model": event.get("model") or "",
        "weight": weight,
    }


def audit_raw_indexes(report: dict[str, Any], sample_limit: int) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    counts: Counter[str] = Counter()
    samples: list[dict[str, Any]] = []
    source_sessions: Counter[str] = Counter()
    sessions_with_prompts = 0
    prompt_total = 0

    for session in report.get("sessions") or []:
        source = str(session.get("source") or "unknown")
        source_sessions[source] += 1
        prompts, duplicate_indexes, prompt_rows = prompt_index_info(session)
        prompt_total += prompt_rows
        counts["unique_prompt_indexes"] += len(prompts)
        duplicate_rows = prompt_rows - len(prompts)
        counts["duplicate_prompt_index_rows"] += duplicate_rows
        if duplicate_indexes:
            counts["sessions_with_duplicate_prompt_indexes"] += 1
        if prompt_rows:
            sessions_with_prompts += 1

        for event in session.get("tool_events") or []:
            weight = event_weight(event)
            counts["tool_events"] += 1
            counts["system_observation_weight_from_raw"] += weight
            index = as_int(event.get("prompt_index"))
            if index is None or index not in prompts:
                counts["tool_invalid_prompt_index_events"] += 1
                counts["tool_invalid_prompt_index_weight"] += weight
                if len(samples) < sample_limit:
                    samples.append(
                        sample_row(
                            kind="tool",
                            session=session,
                            event=event,
                            prompt_index=event.get("prompt_index"),
                            prompt_row_tag="",
                            reason="invalid_prompt_index",
                            weight=weight,
                        )
                    )
                continue
            counts["tool_valid_prompt_index_events"] += 1
            counts["tool_valid_prompt_index_weight"] += weight
            if index in duplicate_indexes:
                counts["tool_ambiguous_prompt_index_events"] += 1
                counts["tool_ambiguous_prompt_index_weight"] += weight
            prompt_tag = prompts[index]
            if str(event.get("prompt_tag") or "unknown") == prompt_tag:
                counts["tool_prompt_tag_consistent_events"] += 1
                counts["tool_prompt_tag_consistent_weight"] += weight
            else:
                counts["tool_prompt_tag_mismatch_events"] += 1
                counts["tool_prompt_tag_mismatch_weight"] += weight
                if len(samples) < sample_limit:
                    samples.append(
                        sample_row(
                            kind="tool",
                            session=session,
                            event=event,
                            prompt_index=index,
                            prompt_row_tag=prompt_tag,
                            reason="prompt_tag_mismatch",
                            weight=weight,
                        )
                    )

        for event in session.get("llm_events") or []:
            counts["llm_events"] += 1
            index = as_int(event.get("prompt_index"))
            if index is None or index not in prompts:
                counts["llm_invalid_prompt_index_events"] += 1
                if len(samples) < sample_limit:
                    samples.append(
                        sample_row(
                            kind="llm",
                            session=session,
                            event=event,
                            prompt_index=event.get("prompt_index"),
                            prompt_row_tag="",
                            reason="invalid_prompt_index",
                        )
                    )
                continue
            counts["llm_valid_prompt_index_events"] += 1
            if index in duplicate_indexes:
                counts["llm_ambiguous_prompt_index_events"] += 1
            prompt_tag = prompts[index]
            if str(event.get("prompt_tag") or "unknown") == prompt_tag:
                counts["llm_prompt_tag_consistent_events"] += 1
            else:
                counts["llm_prompt_tag_mismatch_events"] += 1
                if len(samples) < sample_limit:
                    samples.append(
                        sample_row(
                            kind="llm",
                            session=session,
                            event=event,
                            prompt_index=index,
                            prompt_row_tag=prompt_tag,
                            reason="prompt_tag_mismatch",
                        )
                    )

    tool_events = counts["tool_events"]
    llm_events = counts["llm_events"]
    tool_weight = counts["system_observation_weight_from_raw"]
    summary = {
        "sessions": len(report.get("sessions") or []),
        "sessions_by_source": dict(source_sessions),
        "sessions_with_prompts": sessions_with_prompts,
        "prompt_rows": prompt_total,
        "unique_prompt_indexes": counts["unique_prompt_indexes"],
        "duplicate_prompt_index_rows": counts["duplicate_prompt_index_rows"],
        "sessions_with_duplicate_prompt_indexes": counts["sessions_with_duplicate_prompt_indexes"],
        "tool_events": tool_events,
        "llm_events": llm_events,
        "system_observation_weight_from_raw": tool_weight,
        "tool_valid_prompt_index_events": counts["tool_valid_prompt_index_events"],
        "tool_valid_prompt_index_pct": pct(counts["tool_valid_prompt_index_events"], tool_events),
        "tool_valid_prompt_index_weight": counts["tool_valid_prompt_index_weight"],
        "tool_valid_prompt_index_weight_pct": pct(counts["tool_valid_prompt_index_weight"], tool_weight),
        "tool_ambiguous_prompt_index_events": counts["tool_ambiguous_prompt_index_events"],
        "tool_ambiguous_prompt_index_weight": counts["tool_ambiguous_prompt_index_weight"],
        "tool_ambiguous_prompt_index_weight_pct": pct(counts["tool_ambiguous_prompt_index_weight"], tool_weight),
        "tool_prompt_tag_mismatch_events": counts["tool_prompt_tag_mismatch_events"],
        "tool_prompt_tag_mismatch_event_pct": pct(counts["tool_prompt_tag_mismatch_events"], tool_events),
        "tool_prompt_tag_mismatch_weight": counts["tool_prompt_tag_mismatch_weight"],
        "tool_prompt_tag_mismatch_weight_pct": pct(counts["tool_prompt_tag_mismatch_weight"], tool_weight),
        "llm_valid_prompt_index_events": counts["llm_valid_prompt_index_events"],
        "llm_valid_prompt_index_pct": pct(counts["llm_valid_prompt_index_events"], llm_events),
        "llm_invalid_prompt_index_events": counts["llm_invalid_prompt_index_events"],
        "llm_ambiguous_prompt_index_events": counts["llm_ambiguous_prompt_index_events"],
        "llm_prompt_tag_mismatch_events": counts["llm_prompt_tag_mismatch_events"],
        "llm_prompt_tag_mismatch_event_pct": pct(counts["llm_prompt_tag_mismatch_events"], llm_events),
    }
    return summary, samples


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def build_result(args: argparse.Namespace) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    report = read_json(args.agentflame)
    r170 = read_json(args.r170_json)
    r225 = read_json(args.r225_json) if args.r225_json.exists() else {}
    folded = audit_folded(args.semantic_folded)
    raw, samples = audit_raw_indexes(report, args.sample_limit)

    r170_summary = r170.get("summary") or {}
    folded_total_matches_r170 = folded["total_weight"] == int(r170_summary.get("system_observations") or -1)
    raw_total_matches_folded = raw["system_observation_weight_from_raw"] == folded["total_weight"]
    folded_required_frames_complete = folded["missing_total_weight"] == 0
    tool_prompt_index_complete = raw["tool_valid_prompt_index_weight"] == raw["system_observation_weight_from_raw"]
    prompt_index_unique = raw["duplicate_prompt_index_rows"] == 0
    strict_prompt_tag_consistent = (
        raw["tool_prompt_tag_mismatch_weight"] == 0
        and raw["llm_prompt_tag_mismatch_events"] == 0
        and raw["llm_invalid_prompt_index_events"] == 0
        and prompt_index_unique
    )
    projection_supported = (
        folded_total_matches_r170
        and raw_total_matches_folded
        and folded_required_frames_complete
        and tool_prompt_index_complete
    )
    status = (
        "ok"
        if projection_supported and strict_prompt_tag_consistent
        else "partial_projection_indexed_with_semantic_drift"
        if projection_supported
        else "failed_projection_index_audit"
    )

    result = {
        "schema_version": 1,
        "run_id": "R230",
        "status": status,
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "scope": "generated_full_history_projection_lineage_audit",
        "inputs": {
            "agentflame_json": rel(args.agentflame),
            "agentflame_json_sha256": sha256_file(args.agentflame),
            "semantic_system_folded": rel(args.semantic_folded),
            "semantic_system_folded_sha256": sha256_file(args.semantic_folded),
            "r170_json": rel(args.r170_json),
            "r170_json_sha256": sha256_file(args.r170_json),
            "r225_json": rel(args.r225_json) if args.r225_json.exists() else None,
            "r225_json_sha256": sha256_file(args.r225_json) if args.r225_json.exists() else None,
        },
        "r170_summary": {
            "sessions": r170_summary.get("session_count"),
            "system_observations": r170_summary.get("system_observations"),
            "semantic_system_stacks": r170_summary.get("semantic_system_stacks"),
        },
        "folded_audit": folded,
        "raw_event_index_audit": raw,
        "r225_prompt_span_reference": {
            "prompt_spans_total": r225.get("prompt_spans_total"),
            "covered_effect_total_weight": r225.get("covered_effect_total_weight"),
            "covered_effect_share_pct": r225.get("covered_effect_share_pct"),
            "expanded_effect_total_matches_folded": r225.get("expanded_effect_total_matches_folded"),
            "prompt_span_duration_is_wall_clock_interval": r225.get("prompt_span_duration_is_wall_clock_interval"),
            "true_tool_or_llm_duration_supported": r225.get("true_tool_or_llm_duration_supported"),
        },
        "claim_gate": {
            "reads_generated_artifacts_only": True,
            "llm_called": False,
            "raw_trace_read": False,
            "folded_total_matches_r170": folded_total_matches_r170,
            "raw_total_matches_folded": raw_total_matches_folded,
            "folded_required_frames_complete": folded_required_frames_complete,
            "system_effect_prompt_index_complete": tool_prompt_index_complete,
            "prompt_index_unique_supported": prompt_index_unique,
            "system_effect_history_projection_supported": projection_supported,
            "strict_prompt_tag_consistency_supported": strict_prompt_tag_consistent,
            "strict_full_history_semantic_lineage_supported": False,
            "live_exact_provenance_supported": False,
            "counts_as_c5_or_c6_human_evidence": False,
        },
        "claim_boundary": (
            "R230 audits generated full-history AgentFlame artifacts, not raw agent "
            "sessions and not live eBPF provenance. It can support the weaker claim "
            "that folded system effects carry semantic session/prompt tag frames, "
            "call/effect frames, and match the R170 report totals. Raw event indexes "
            "are audited separately. Because prompt indexes can be duplicated and "
            "event-local prompt tags can drift from prompt-row tags, and because "
            "this is not a live negative-control run, it does not prove strict full-history exact "
            "semantic lineage, C5 developer utility, or C6 tag adequacy."
        ),
        "provenance": {
            "repo_commit": git(["rev-parse", "HEAD"]),
            "repo_dirty": bool(git(["status", "--short"])),
            "script": rel(Path(__file__).resolve()),
            "script_sha256": sha256_file(Path(__file__).resolve()),
        },
    }
    return result, samples


def write_markdown(path: Path, result: dict[str, Any]) -> None:
    raw = result["raw_event_index_audit"]
    folded = result["folded_audit"]
    gate = result["claim_gate"]
    lines = [
        "# R230 Full-History Projection-Lineage Audit",
        "",
        f"Status: `{result['status']}`",
        "",
        "R230 reads generated R170/R225 AgentFlame artifacts only. It checks the",
        "full-history projection/indexing layer; it does not claim live exact",
        "provenance or human evidence.",
        "",
        "## Summary",
        "",
        f"- Sessions/prompts: {raw['sessions']} sessions, {raw['prompt_rows']} prompt rows, {raw['unique_prompt_indexes']} unique per-session prompt indexes.",
        f"- Duplicate prompt-index rows: {raw['duplicate_prompt_index_rows']} across {raw['sessions_with_duplicate_prompt_indexes']} sessions.",
        f"- System folded stacks: {folded['unique_stacks']} unique stacks, {folded['total_weight']} total weight.",
        f"- Required folded frames missing weight: {folded['missing_total_weight']}.",
        f"- Raw system observation weight from tool events: {raw['system_observation_weight_from_raw']}.",
        f"- Tool prompt-index coverage: {raw['tool_valid_prompt_index_weight']}/{raw['system_observation_weight_from_raw']} weight = {raw['tool_valid_prompt_index_weight_pct']}%.",
        f"- Tool ambiguous prompt-index weight: {raw['tool_ambiguous_prompt_index_weight']} ({raw['tool_ambiguous_prompt_index_weight_pct']}%).",
        f"- Tool prompt-tag drift: {raw['tool_prompt_tag_mismatch_weight']} weight ({raw['tool_prompt_tag_mismatch_weight_pct']}%) across {raw['tool_prompt_tag_mismatch_events']} events.",
        f"- LLM prompt-index coverage: {raw['llm_valid_prompt_index_events']}/{raw['llm_events']} events = {raw['llm_valid_prompt_index_pct']}%.",
        f"- LLM prompt-tag drift: {raw['llm_prompt_tag_mismatch_events']} events ({raw['llm_prompt_tag_mismatch_event_pct']}%).",
        "",
        "## Claim Gate",
        "",
        f"- System-effect history projection supported: `{gate['system_effect_history_projection_supported']}`.",
        f"- Strict prompt-tag consistency supported: `{gate['strict_prompt_tag_consistency_supported']}`.",
        f"- Strict full-history semantic lineage supported: `{gate['strict_full_history_semantic_lineage_supported']}`.",
        f"- Live exact provenance supported: `{gate['live_exact_provenance_supported']}`.",
        "",
        "## Boundary",
        "",
        result["claim_boundary"],
        "",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def run(args: argparse.Namespace) -> dict[str, Any]:
    args.out_dir.mkdir(parents=True, exist_ok=True)
    result, samples = build_result(args)
    out_json = args.out_dir / "full-history-lineage-r230.json"
    out_md = args.out_dir / "full-history-lineage-r230.md"
    sample_csv = args.out_dir / "semantic-drift-samples-r230.csv"
    result["outputs"] = {
        "json": rel(out_json),
        "markdown": rel(out_md),
        "semantic_drift_samples_csv": rel(sample_csv),
    }
    write_json(out_json, result)
    write_markdown(out_md, result)
    write_csv(
        sample_csv,
        samples,
        [
            "kind",
            "reason",
            "source",
            "session_id_hash",
            "session_tag",
            "prompt_index",
            "prompt_row_tag",
            "event_prompt_tag",
            "tool_name",
            "command_name",
            "effect",
            "status",
            "llm_tag",
            "model",
            "weight",
        ],
    )
    print(
        json.dumps(
            {
                "status": result["status"],
                "claim_gate": result["claim_gate"],
                "raw_event_index_audit": result["raw_event_index_audit"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--agentflame", type=Path, default=DEFAULT_AGENTFLAME)
    parser.add_argument("--semantic-folded", type=Path, default=DEFAULT_SEMANTIC_FOLDED)
    parser.add_argument("--r170-json", type=Path, default=DEFAULT_R170_JSON)
    parser.add_argument("--r225-json", type=Path, default=DEFAULT_R225_JSON)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--sample-limit", type=int, default=50)
    return parser


if __name__ == "__main__":
    run(build_parser().parse_args())
