#!/usr/bin/env python3
"""R231: root-cause audit for R230 prompt-tag drift.

R230 found that every generated system-observation row has a prompt index, but
some event-local prompt tags do not match prompt-row tags when the prompt
``index`` field is treated as the unique join key. R231 narrows that finding:
it compares three projections over the same generated R170 artifacts.

1. Folded display projection: semantic-system.folded prompt frames.
2. Event-local projection: prompt tags stored on generated tool/LLM events.
3. Prompt-row lineage projection: event prompt indexes joined back to prompt
   rows by either prompt ``index`` field or list position.

The experiment is intentionally read-only over generated artifacts. It does not
read raw agent session histories, call an LLM, or claim external cross-repo live
lineage.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import subprocess
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[1]
DEFAULT_AGENTFLAME = REPO_ROOT / ".agentsight" / "agentflame" / "r170-full-current" / "agentflame.json"
DEFAULT_SEMANTIC_FOLDED = (
    REPO_ROOT / ".agentsight" / "agentflame" / "r170-full-current" / "semantic-system.folded.txt"
)
DEFAULT_R230_JSON = SCRIPT_DIR / "out" / "full-history-lineage-r230" / "full-history-lineage-r230.json"
DEFAULT_OUT_DIR = SCRIPT_DIR / "out" / "drift-root-cause-r231"


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


def clean_tag(value: Any) -> str:
    return str(value or "unknown")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def folded_prompt_weights(path: Path) -> Counter[str]:
    weights: Counter[str] = Counter()
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            stack, _, weight_text = line.rstrip("\n").rpartition(" ")
            if not stack or not weight_text.isdigit():
                raise ValueError(f"invalid folded line: {line[:160]}")
            prompt_tag = "unknown"
            for frame in stack.split(";"):
                if frame.startswith("prompt:"):
                    prompt_tag = frame.split(":", 1)[1]
                    break
            weights[prompt_tag] += int(weight_text)
    return weights


def prompt_indexes(session: dict[str, Any]) -> tuple[dict[int, str], set[int], Counter[int]]:
    counts: Counter[int] = Counter()
    field_tag: dict[int, str] = {}
    for prompt in session.get("prompts") or []:
        index = as_int(prompt.get("index"))
        if index is None:
            continue
        counts[index] += 1
        field_tag[index] = clean_tag(prompt.get("tag"))
    duplicate_indexes = {index for index, count in counts.items() if count > 1}
    return field_tag, duplicate_indexes, counts


def add_mismatch_sample(
    samples: list[dict[str, Any]],
    *,
    sample_limit: int,
    semantics: str,
    kind: str,
    source: str,
    session_id: Any,
    session_tag: str,
    prompt_index: Any,
    row_tag: str,
    event_tag: str,
    effect: str,
    command_name: str,
    tool_name: str,
    llm_tag: str,
    weight: int,
    duplicate_index: bool,
) -> None:
    if len(samples) >= sample_limit:
        return
    samples.append(
        {
            "semantics": semantics,
            "kind": kind,
            "source": source,
            "session_id_hash": stable_hash(session_id),
            "session_tag": session_tag,
            "prompt_index": prompt_index,
            "row_tag": row_tag,
            "event_prompt_tag": event_tag,
            "effect": effect,
            "command_name": command_name,
            "tool_name": tool_name,
            "llm_tag": llm_tag,
            "weight": weight,
            "duplicate_index": duplicate_index,
        }
    )


def compare_projection(weights_a: Counter[str], weights_b: Counter[str]) -> dict[str, Any]:
    diff_rows = []
    for tag in sorted(set(weights_a) | set(weights_b)):
        left = weights_a[tag]
        right = weights_b[tag]
        if left != right:
            diff_rows.append({"tag": tag, "event_weight": left, "folded_weight": right, "delta": left - right})
    return {
        "event_total_weight": sum(weights_a.values()),
        "folded_total_weight": sum(weights_b.values()),
        "exact_match": weights_a == weights_b,
        "diff_tag_count": len(diff_rows),
        "diff_sample": diff_rows[:20],
    }


def audit_report(report: dict[str, Any], folded_weights: Counter[str], sample_limit: int) -> dict[str, Any]:
    counts: Counter[str] = Counter()
    event_prompt_weights: Counter[str] = Counter()
    mismatch_pairs: Counter[tuple[str, str, str, str]] = Counter()
    mismatch_by_source: Counter[tuple[str, str, str]] = Counter()
    mismatch_by_duplicate_session: Counter[tuple[str, str, str]] = Counter()
    duplicate_rows: list[dict[str, Any]] = []
    samples: list[dict[str, Any]] = []
    sessions_with_field_mismatch: set[str] = set()
    sessions_with_position_mismatch: set[str] = set()

    for session in report.get("sessions") or []:
        source = clean_tag(session.get("source"))
        session_tag = clean_tag(session.get("session_tag"))
        session_id = session.get("session_id")
        session_hash = stable_hash(session_id)
        prompts = session.get("prompts") or []
        field_tag, duplicate_indexes, index_counts = prompt_indexes(session)
        duplicate_row_count = len(prompts) - len(field_tag)
        has_duplicate_index = bool(duplicate_indexes)
        if prompts:
            counts["sessions_with_prompts"] += 1
        counts["sessions"] += 1
        counts["prompt_rows"] += len(prompts)
        counts["unique_prompt_indexes"] += len(field_tag)
        counts["duplicate_prompt_index_rows"] += duplicate_row_count
        if has_duplicate_index:
            counts["sessions_with_duplicate_prompt_indexes"] += 1
            duplicate_rows.append(
                {
                    "source": source,
                    "session_id_hash": session_hash,
                    "session_tag": session_tag,
                    "prompt_rows": len(prompts),
                    "unique_prompt_indexes": len(field_tag),
                    "duplicate_prompt_index_rows": duplicate_row_count,
                    "duplicate_indexes": ",".join(str(index) for index in sorted(duplicate_indexes)),
                }
            )

        for kind, events in (("tool", session.get("tool_events") or []), ("llm", session.get("llm_events") or [])):
            for event in events:
                index = as_int(event.get("prompt_index"))
                event_tag = clean_tag(event.get("prompt_tag"))
                weight = event_weight(event) if kind == "tool" else 1
                counts[f"{kind}_events"] += 1
                counts[f"{kind}_weight"] += weight
                if kind == "tool":
                    event_prompt_weights[event_tag] += weight
                duplicate_index = index in duplicate_indexes if index is not None else False
                if duplicate_index:
                    add_metric_and_event(counts, f"{kind}_ambiguous", kind, weight)

                field_row_tag = field_tag.get(index) if index is not None else None
                if field_row_tag is None:
                    add_metric_and_event(counts, f"{kind}_field_invalid", kind, weight)
                elif field_row_tag == event_tag:
                    add_metric_and_event(counts, f"{kind}_field_match", kind, weight)
                else:
                    add_metric_and_event(counts, f"{kind}_field_mismatch", kind, weight)
                    sessions_with_field_mismatch.add(session_hash)
                    mismatch_pairs[(kind, "field", field_row_tag, event_tag)] += weight
                    mismatch_by_source[(kind, "field", source)] += weight
                    mismatch_by_duplicate_session[
                        (kind, "field", "duplicate_session" if has_duplicate_index else "unique_session")
                    ] += weight
                    add_mismatch_sample(
                        samples,
                        sample_limit=sample_limit,
                        semantics="field",
                        kind=kind,
                        source=source,
                        session_id=session_id,
                        session_tag=session_tag,
                        prompt_index=index,
                        row_tag=field_row_tag,
                        event_tag=event_tag,
                        effect=clean_tag(event.get("effect")),
                        command_name=clean_tag(event.get("command_name")),
                        tool_name=clean_tag(event.get("tool_name")),
                        llm_tag=clean_tag(event.get("llm_tag")),
                        weight=weight,
                        duplicate_index=duplicate_index,
                    )

                position_row_tag = None
                if index is not None and 0 <= index < len(prompts):
                    position_row_tag = clean_tag(prompts[index].get("tag"))
                if position_row_tag is None:
                    add_metric_and_event(counts, f"{kind}_position_invalid", kind, weight)
                elif position_row_tag == event_tag:
                    add_metric_and_event(counts, f"{kind}_position_match", kind, weight)
                else:
                    add_metric_and_event(counts, f"{kind}_position_mismatch", kind, weight)
                    sessions_with_position_mismatch.add(session_hash)
                    mismatch_pairs[(kind, "position", position_row_tag, event_tag)] += weight
                    mismatch_by_source[(kind, "position", source)] += weight
                    mismatch_by_duplicate_session[
                        (kind, "position", "duplicate_session" if has_duplicate_index else "unique_session")
                    ] += weight
                    add_mismatch_sample(
                        samples,
                        sample_limit=sample_limit,
                        semantics="position",
                        kind=kind,
                        source=source,
                        session_id=session_id,
                        session_tag=session_tag,
                        prompt_index=index,
                        row_tag=position_row_tag,
                        event_tag=event_tag,
                        effect=clean_tag(event.get("effect")),
                        command_name=clean_tag(event.get("command_name")),
                        tool_name=clean_tag(event.get("tool_name")),
                        llm_tag=clean_tag(event.get("llm_tag")),
                        weight=weight,
                        duplicate_index=duplicate_index,
                    )

    display_projection = compare_projection(event_prompt_weights, folded_weights)
    return {
        "counts": counts,
        "display_projection": display_projection,
        "duplicate_sessions": duplicate_rows,
        "mismatch_pairs": mismatch_pairs,
        "mismatch_by_source": mismatch_by_source,
        "mismatch_by_duplicate_session": mismatch_by_duplicate_session,
        "samples": samples,
        "sessions_with_field_mismatch": len(sessions_with_field_mismatch),
        "sessions_with_position_mismatch": len(sessions_with_position_mismatch),
    }


def kind_metric(kind: str) -> str:
    return "weight" if kind == "tool" else "events"


def add_metric_and_event(counts: Counter[str], key_prefix: str, kind: str, value: int) -> None:
    metric = kind_metric(kind)
    counts[f"{key_prefix}_{metric}"] += value
    if metric != "events":
        counts[f"{key_prefix}_events"] += 1


def metric_denominator(counts: Counter[str], kind: str) -> int:
    return counts[f"{kind}_weight"] if kind == "tool" else counts[f"{kind}_events"]


def projection_summary(counts: Counter[str], kind: str, semantics: str) -> dict[str, Any]:
    metric = kind_metric(kind)
    total = metric_denominator(counts, kind)
    mismatch = counts[f"{kind}_{semantics}_mismatch_{metric}"]
    invalid = counts[f"{kind}_{semantics}_invalid_{metric}"]
    return {
        "kind": kind,
        "semantics": semantics,
        "metric": metric,
        "total": total,
        "match": counts[f"{kind}_{semantics}_match_{metric}"],
        "mismatch": mismatch,
        "invalid": invalid,
        "mismatch_pct": pct(mismatch, total),
        "invalid_pct": pct(invalid, total),
        "strict_consistency_supported": mismatch == 0 and invalid == 0,
    }


def counter_rows(counter: Counter[tuple[str, ...]], fields: list[str], value_name: str) -> list[dict[str, Any]]:
    rows = []
    for key, value in counter.most_common():
        row = {field: key[index] for index, field in enumerate(fields)}
        row[value_name] = value
        rows.append(row)
    return rows


def validate_r230_reproduction(r230: dict[str, Any], counts: Counter[str]) -> dict[str, Any]:
    raw = r230.get("raw_event_index_audit") or {}
    expected = {
        "tool_field_mismatch_weight": raw.get("tool_prompt_tag_mismatch_weight"),
        "tool_field_mismatch_events": raw.get("tool_prompt_tag_mismatch_events"),
        "llm_field_mismatch_events": raw.get("llm_prompt_tag_mismatch_events"),
        "duplicate_prompt_index_rows": raw.get("duplicate_prompt_index_rows"),
        "tool_ambiguous_weight": raw.get("tool_ambiguous_prompt_index_weight"),
        "llm_ambiguous_events": raw.get("llm_ambiguous_prompt_index_events"),
    }
    observed = {
        "tool_field_mismatch_weight": counts["tool_field_mismatch_weight"],
        "tool_field_mismatch_events": counts["tool_field_mismatch_events"],
        "llm_field_mismatch_events": counts["llm_field_mismatch_events"],
        "duplicate_prompt_index_rows": counts["duplicate_prompt_index_rows"],
        "tool_ambiguous_weight": counts["tool_ambiguous_weight"],
        "llm_ambiguous_events": counts["llm_ambiguous_events"],
    }
    return {
        "matches_r230": expected == observed,
        "expected_from_r230": expected,
        "observed_by_r231": observed,
    }


def build_result(args: argparse.Namespace) -> dict[str, Any]:
    report = read_json(args.agentflame)
    r230 = read_json(args.r230_json)
    folded_weights = folded_prompt_weights(args.semantic_folded)
    audit = audit_report(report, folded_weights, args.sample_limit)
    counts = audit["counts"]
    r230_reproduction = validate_r230_reproduction(r230, counts)

    field_tool = projection_summary(counts, "tool", "field")
    field_llm = projection_summary(counts, "llm", "field")
    position_tool = projection_summary(counts, "tool", "position")
    position_llm = projection_summary(counts, "llm", "position")
    duplicate_field_tool = audit["mismatch_by_duplicate_session"].get(("tool", "field", "duplicate_session"), 0)
    duplicate_field_llm = audit["mismatch_by_duplicate_session"].get(("llm", "field", "duplicate_session"), 0)
    unique_field_tool = audit["mismatch_by_duplicate_session"].get(("tool", "field", "unique_session"), 0)
    unique_field_llm = audit["mismatch_by_duplicate_session"].get(("llm", "field", "unique_session"), 0)
    field_drift_localized = (
        field_tool["mismatch"] > 0
        and field_llm["mismatch"] > 0
        and unique_field_tool == 0
        and unique_field_llm == 0
    )

    status = (
        "ok_drift_root_cause_localized"
        if audit["display_projection"]["exact_match"]
        and r230_reproduction["matches_r230"]
        and field_drift_localized
        else "partial_drift_root_cause"
    )
    result = {
        "schema_version": 1,
        "run_id": "R231",
        "status": status,
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "scope": "generated_artifact_prompt_tag_drift_root_cause_audit",
        "inputs": {
            "agentflame_json": rel(args.agentflame),
            "agentflame_json_sha256": sha256_file(args.agentflame),
            "semantic_system_folded": rel(args.semantic_folded),
            "semantic_system_folded_sha256": sha256_file(args.semantic_folded),
            "r230_json": rel(args.r230_json),
            "r230_json_sha256": sha256_file(args.r230_json),
        },
        "summary": {
            "sessions": counts["sessions"],
            "prompt_rows": counts["prompt_rows"],
            "unique_prompt_indexes": counts["unique_prompt_indexes"],
            "duplicate_prompt_index_rows": counts["duplicate_prompt_index_rows"],
            "sessions_with_duplicate_prompt_indexes": counts["sessions_with_duplicate_prompt_indexes"],
            "tool_events": counts["tool_events"],
            "tool_weight": counts["tool_weight"],
            "llm_events": counts["llm_events"],
            "field_tool_mismatch_weight": field_tool["mismatch"],
            "field_tool_mismatch_pct": field_tool["mismatch_pct"],
            "field_llm_mismatch_events": field_llm["mismatch"],
            "field_llm_mismatch_pct": field_llm["mismatch_pct"],
            "position_tool_mismatch_weight": position_tool["mismatch"],
            "position_tool_mismatch_pct": position_tool["mismatch_pct"],
            "position_llm_mismatch_events": position_llm["mismatch"],
            "position_llm_mismatch_pct": position_llm["mismatch_pct"],
            "field_mismatch_sessions": audit["sessions_with_field_mismatch"],
            "position_mismatch_sessions": audit["sessions_with_position_mismatch"],
            "field_mismatch_unique_session_tool_weight": unique_field_tool,
            "field_mismatch_unique_session_llm_events": unique_field_llm,
            "field_mismatch_duplicate_session_tool_weight": duplicate_field_tool,
            "field_mismatch_duplicate_session_llm_events": duplicate_field_llm,
        },
        "display_projection": audit["display_projection"],
        "prompt_row_lineage_projections": {
            "field_index": {
                "tool": field_tool,
                "llm": field_llm,
                "description": "Join event prompt_index to prompt rows by the prompt row's index field, using the last row for duplicate indexes.",
            },
            "list_position": {
                "tool": position_tool,
                "llm": position_llm,
                "description": "Interpret event prompt_index as a zero-based position in the prompt row list.",
            },
        },
        "r230_reproduction": r230_reproduction,
        "claim_gate": {
            "reads_generated_artifacts_only": True,
            "raw_trace_read": False,
            "llm_called": False,
            "display_projection_matches_event_local_prompt_tags": audit["display_projection"]["exact_match"],
            "r230_field_index_drift_reproduced": r230_reproduction["matches_r230"],
            "field_index_drift_localized_to_duplicate_index_sessions": field_drift_localized,
            "strict_prompt_row_lineage_supported": False,
            "external_crossrepo_live_lineage_supported": False,
            "counts_as_c5_or_c6_human_evidence": False,
        },
        "top_mismatch_pairs": counter_rows(
            audit["mismatch_pairs"],
            ["kind", "semantics", "row_tag", "event_prompt_tag"],
            "weight",
        )[:40],
        "mismatch_by_source": counter_rows(
            audit["mismatch_by_source"],
            ["kind", "semantics", "source"],
            "weight",
        ),
        "mismatch_by_duplicate_session": counter_rows(
            audit["mismatch_by_duplicate_session"],
            ["kind", "semantics", "session_index_class"],
            "weight",
        ),
        "duplicate_prompt_index_sessions": audit["duplicate_sessions"],
        "claim_boundary": (
            "R231 explains the R230 drift at the generated-artifact layer. The "
            "semantic flamegraph display projection exactly matches event-local "
            "tool prompt tags, but raw prompt-row lineage is not strict because "
            "a small set of Claude sessions contains duplicate prompt indexes and "
            "event-local tags can differ from prompt-row tags. R231 does not run "
            "fresh live eBPF capture, does not prove external cross-repo lineage, "
            "and does not provide C5/C6 human evidence."
        ),
        "provenance": {
            "repo_commit": git(["rev-parse", "HEAD"]),
            "repo_dirty": bool(git(["status", "--short"])),
            "script": rel(Path(__file__).resolve()),
            "script_sha256": sha256_file(Path(__file__).resolve()),
        },
        "_samples": audit["samples"],
    }
    return result


def write_markdown(path: Path, result: dict[str, Any]) -> None:
    summary = result["summary"]
    display = result["display_projection"]
    gate = result["claim_gate"]
    field = result["prompt_row_lineage_projections"]["field_index"]
    position = result["prompt_row_lineage_projections"]["list_position"]
    lines = [
        "# R231 Drift Root-Cause Audit",
        "",
        f"Status: `{result['status']}`",
        "",
        "R231 reads generated R170/R230 artifacts only. It separates the display",
        "projection used by flamegraphs from raw prompt-row lineage joins.",
        "",
        "## Summary",
        "",
        f"- Sessions/prompts: {summary['sessions']} sessions, {summary['prompt_rows']} prompt rows.",
        f"- Duplicate prompt-index rows: {summary['duplicate_prompt_index_rows']} across {summary['sessions_with_duplicate_prompt_indexes']} sessions.",
        f"- Display projection: event-local prompt-tag weights {display['event_total_weight']} vs folded prompt-frame weights {display['folded_total_weight']}; exact match `{display['exact_match']}`.",
        f"- Field-index prompt-row drift: tool {field['tool']['mismatch']} weight ({field['tool']['mismatch_pct']}%), LLM {field['llm']['mismatch']} events ({field['llm']['mismatch_pct']}%).",
        f"- List-position prompt-row drift: tool {position['tool']['mismatch']} weight ({position['tool']['mismatch_pct']}%), LLM {position['llm']['mismatch']} events ({position['llm']['mismatch_pct']}%).",
        f"- Field-index drift in unique-index sessions: tool {summary['field_mismatch_unique_session_tool_weight']} weight, LLM {summary['field_mismatch_unique_session_llm_events']} events.",
        f"- Field-index drift in duplicate-index sessions: tool {summary['field_mismatch_duplicate_session_tool_weight']} weight, LLM {summary['field_mismatch_duplicate_session_llm_events']} events.",
        "",
        "## Claim Gate",
        "",
        f"- Display projection matches event-local prompt tags: `{gate['display_projection_matches_event_local_prompt_tags']}`.",
        f"- R230 field-index drift reproduced: `{gate['r230_field_index_drift_reproduced']}`.",
        f"- Field-index drift localized to duplicate-index sessions: `{gate['field_index_drift_localized_to_duplicate_index_sessions']}`.",
        f"- Strict prompt-row lineage supported: `{gate['strict_prompt_row_lineage_supported']}`.",
        f"- External cross-repo live lineage supported: `{gate['external_crossrepo_live_lineage_supported']}`.",
        "",
        "## Top Mismatch Pairs",
        "",
        "| Kind | Semantics | Row tag | Event tag | Weight |",
        "|------|-----------|---------|-----------|-------:|",
    ]
    for row in result["top_mismatch_pairs"][:12]:
        lines.append(
            f"| {row['kind']} | {row['semantics']} | `{row['row_tag']}` | `{row['event_prompt_tag']}` | {row['weight']} |"
        )
    lines.extend(["", "## Boundary", "", result["claim_boundary"], ""])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def run(args: argparse.Namespace) -> dict[str, Any]:
    args.out_dir.mkdir(parents=True, exist_ok=True)
    result = build_result(args)
    samples = result.pop("_samples")

    json_path = args.out_dir / "drift-root-cause-r231.json"
    md_path = args.out_dir / "drift-root-cause-r231.md"
    sample_path = args.out_dir / "drift-samples-r231.csv"
    duplicate_path = args.out_dir / "duplicate-prompt-index-sessions-r231.csv"
    pair_path = args.out_dir / "mismatch-pairs-r231.csv"
    result["outputs"] = {
        "json": rel(json_path),
        "markdown": rel(md_path),
        "drift_samples_csv": rel(sample_path),
        "duplicate_prompt_index_sessions_csv": rel(duplicate_path),
        "mismatch_pairs_csv": rel(pair_path),
    }

    write_json(json_path, result)
    write_markdown(md_path, result)
    write_csv(
        sample_path,
        samples,
        [
            "semantics",
            "kind",
            "source",
            "session_id_hash",
            "session_tag",
            "prompt_index",
            "row_tag",
            "event_prompt_tag",
            "effect",
            "command_name",
            "tool_name",
            "llm_tag",
            "weight",
            "duplicate_index",
        ],
    )
    write_csv(
        duplicate_path,
        result["duplicate_prompt_index_sessions"],
        [
            "source",
            "session_id_hash",
            "session_tag",
            "prompt_rows",
            "unique_prompt_indexes",
            "duplicate_prompt_index_rows",
            "duplicate_indexes",
        ],
    )
    write_csv(
        pair_path,
        result["top_mismatch_pairs"],
        ["kind", "semantics", "row_tag", "event_prompt_tag", "weight"],
    )
    print(
        json.dumps(
            {
                "status": result["status"],
                "summary": result["summary"],
                "claim_gate": result["claim_gate"],
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
    parser.add_argument("--r230-json", type=Path, default=DEFAULT_R230_JSON)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--sample-limit", type=int, default=80)
    return parser


if __name__ == "__main__":
    run(build_parser().parse_args())
