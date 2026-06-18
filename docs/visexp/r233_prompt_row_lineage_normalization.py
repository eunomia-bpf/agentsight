#!/usr/bin/env python3
"""R233: normalize prompt-row lineage semantics for duplicate prompt indexes.

R230/R231 showed that the generated R170 report's flamegraph projection is
exact over event-local prompt tags, but prompt rows can contain duplicate
``index`` fields in a small number of Claude sessions. R233 turns that finding
into an explicit contract:

* bare prompt ``index`` is a key only when it is unique inside a session;
* duplicate indexes are non-keyed for row identity;
* semantic prompt lineage is checked with the normalized ``(index, tag)``
  semantic key, while same-tag duplicates remain non-keyed row metadata.

This script reads generated artifacts only. It does not read raw agent
histories, call an LLM, or run live eBPF capture.
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
DEFAULT_R231_JSON = SCRIPT_DIR / "out" / "drift-root-cause-r231" / "drift-root-cause-r231.json"
DEFAULT_OUT_DIR = SCRIPT_DIR / "out" / "prompt-row-lineage-r233"


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


def as_int(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def clean_tag(value: Any) -> str:
    return str(value or "unknown")


def stable_hash(value: Any) -> str:
    return hashlib.sha256(str(value or "").encode("utf-8")).hexdigest()[:12]


def event_weight(event: dict[str, Any], kind: str) -> int:
    if kind == "llm":
        return 1
    return len(event.get("path_groups") or []) or len(event.get("domains") or []) or 1


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


def prompt_groups(session: dict[str, Any]) -> dict[int, list[dict[str, Any]]]:
    groups: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for ordinal, prompt in enumerate(session.get("prompts") or []):
        index = as_int(prompt.get("index"))
        if index is None:
            continue
        groups[index].append(
            {
                "row_ordinal": ordinal,
                "index": index,
                "tag": clean_tag(prompt.get("tag")),
                "hash": str(prompt.get("hash") or ""),
            }
        )
    return dict(groups)


def add_metric(counts: Counter[str], prefix: str, kind: str, weight: int) -> None:
    counts[f"{prefix}_{kind}_events"] += 1
    counts[f"{prefix}_{kind}_weight"] += weight


def audit(report: dict[str, Any], folded_weights: Counter[str], sample_limit: int) -> dict[str, Any]:
    counts: Counter[str] = Counter()
    duplicate_rows: list[dict[str, Any]] = []
    mismatch_samples: list[dict[str, Any]] = []
    event_prompt_weights: Counter[str] = Counter()

    for session in report.get("sessions") or []:
        source = clean_tag(session.get("source"))
        session_tag = clean_tag(session.get("session_tag"))
        session_hash = stable_hash(session.get("session_id"))
        groups = prompt_groups(session)
        prompt_count = len(session.get("prompts") or [])
        duplicate_groups = {index: rows for index, rows in groups.items() if len(rows) > 1}
        duplicate_row_count = sum(len(rows) - 1 for rows in duplicate_groups.values())

        counts["sessions"] += 1
        counts["prompt_rows"] += prompt_count
        counts["unique_prompt_indexes"] += len(groups)
        counts["duplicate_prompt_index_rows"] += duplicate_row_count
        if duplicate_groups:
            counts["sessions_with_duplicate_prompt_indexes"] += 1
        for index, rows in duplicate_groups.items():
            tags = [row["tag"] for row in rows]
            tag_counts = Counter(tags)
            if len(tag_counts) == 1:
                counts["duplicate_same_tag_groups"] += 1
            else:
                counts["duplicate_mixed_tag_groups"] += 1
            duplicate_rows.append(
                {
                    "source": source,
                    "session_id_hash": session_hash,
                    "session_tag": session_tag,
                    "prompt_index": index,
                    "row_count": len(rows),
                    "distinct_tags": len(tag_counts),
                    "tags": "|".join(tags),
                    "semantic_key_status": "same_tag_non_keyed" if len(tag_counts) == 1 else "tag_disambiguatable",
                }
            )

        for kind, events in (("tool", session.get("tool_events") or []), ("llm", session.get("llm_events") or [])):
            for event in events:
                index = as_int(event.get("prompt_index"))
                event_tag = clean_tag(event.get("prompt_tag"))
                weight = event_weight(event, kind)
                counts[f"{kind}_events"] += 1
                counts[f"{kind}_weight"] += weight
                if kind == "tool":
                    event_prompt_weights[event_tag] += weight

                rows = groups.get(index) if index is not None else None
                if not rows:
                    add_metric(counts, "normalized_invalid", kind, weight)
                    if len(mismatch_samples) < sample_limit:
                        mismatch_samples.append(
                            {
                                "kind": kind,
                                "reason": "invalid_prompt_index",
                                "source": source,
                                "session_id_hash": session_hash,
                                "session_tag": session_tag,
                                "prompt_index": event.get("prompt_index"),
                                "event_prompt_tag": event_tag,
                                "row_tags": "",
                                "weight": weight,
                            }
                        )
                    continue

                field_row_tag = rows[-1]["tag"]
                if field_row_tag != event_tag:
                    add_metric(counts, "legacy_field_mismatch", kind, weight)

                tag_counts = Counter(row["tag"] for row in rows)
                if len(rows) > 1:
                    add_metric(counts, "duplicate_index", kind, weight)

                if event_tag not in tag_counts:
                    add_metric(counts, "normalized_mismatch", kind, weight)
                    if len(mismatch_samples) < sample_limit:
                        mismatch_samples.append(
                            {
                                "kind": kind,
                                "reason": "normalized_tag_absent",
                                "source": source,
                                "session_id_hash": session_hash,
                                "session_tag": session_tag,
                                "prompt_index": event.get("prompt_index"),
                                "event_prompt_tag": event_tag,
                                "row_tags": "|".join(row["tag"] for row in rows),
                                "weight": weight,
                            }
                        )
                else:
                    add_metric(counts, "normalized_match", kind, weight)
                    if len(rows) > 1 and tag_counts[event_tag] == 1:
                        add_metric(counts, "duplicate_tag_disambiguated", kind, weight)
                    elif len(rows) > 1:
                        add_metric(counts, "duplicate_same_tag_identity_ambiguous", kind, weight)

    display_diff = {
        "event_total_weight": sum(event_prompt_weights.values()),
        "folded_total_weight": sum(folded_weights.values()),
        "exact_match": event_prompt_weights == folded_weights,
        "diff_tag_count": len(
            [tag for tag in set(event_prompt_weights) | set(folded_weights) if event_prompt_weights[tag] != folded_weights[tag]]
        ),
    }
    return {
        "counts": counts,
        "duplicate_prompt_index_rows": duplicate_rows,
        "mismatch_samples": mismatch_samples,
        "display_projection": display_diff,
    }


def build_summary(audit_result: dict[str, Any]) -> dict[str, Any]:
    counts = audit_result["counts"]
    normalized_tool_mismatch = counts["normalized_mismatch_tool_weight"] + counts["normalized_invalid_tool_weight"]
    normalized_llm_mismatch = counts["normalized_mismatch_llm_events"] + counts["normalized_invalid_llm_events"]
    identity_ambiguous_tool = counts["duplicate_same_tag_identity_ambiguous_tool_weight"]
    identity_ambiguous_llm = counts["duplicate_same_tag_identity_ambiguous_llm_events"]
    return {
        "sessions": counts["sessions"],
        "prompt_rows": counts["prompt_rows"],
        "unique_prompt_indexes": counts["unique_prompt_indexes"],
        "duplicate_prompt_index_rows": counts["duplicate_prompt_index_rows"],
        "sessions_with_duplicate_prompt_indexes": counts["sessions_with_duplicate_prompt_indexes"],
        "duplicate_same_tag_groups": counts["duplicate_same_tag_groups"],
        "duplicate_mixed_tag_groups": counts["duplicate_mixed_tag_groups"],
        "tool_events": counts["tool_events"],
        "tool_weight": counts["tool_weight"],
        "llm_events": counts["llm_events"],
        "legacy_field_tool_mismatch_weight": counts["legacy_field_mismatch_tool_weight"],
        "legacy_field_llm_mismatch_events": counts["legacy_field_mismatch_llm_events"],
        "normalized_tool_mismatch_weight": normalized_tool_mismatch,
        "normalized_tool_mismatch_pct": pct(normalized_tool_mismatch, counts["tool_weight"]),
        "normalized_llm_mismatch_events": normalized_llm_mismatch,
        "normalized_llm_mismatch_pct": pct(normalized_llm_mismatch, counts["llm_events"]),
        "duplicate_index_tool_weight": counts["duplicate_index_tool_weight"],
        "duplicate_index_llm_events": counts["duplicate_index_llm_events"],
        "duplicate_tag_disambiguated_tool_weight": counts["duplicate_tag_disambiguated_tool_weight"],
        "duplicate_tag_disambiguated_llm_events": counts["duplicate_tag_disambiguated_llm_events"],
        "duplicate_same_tag_identity_ambiguous_tool_weight": identity_ambiguous_tool,
        "duplicate_same_tag_identity_ambiguous_llm_events": identity_ambiguous_llm,
    }


def write_markdown(path: Path, result: dict[str, Any]) -> None:
    summary = result["summary"]
    gate = result["claim_gate"]
    lines = [
        "# R233 Prompt-Row Lineage Normalization",
        "",
        f"Status: `{result['status']}`",
        "",
        "R233 reads generated R170/R231 artifacts only. It converts duplicate",
        "prompt indexes from an implicit key bug into an explicit normalized",
        "lineage contract.",
        "",
        "## Summary",
        "",
        f"- Sessions/prompts: {summary['sessions']} sessions, {summary['prompt_rows']} prompt rows.",
        f"- Duplicate prompt-index rows: {summary['duplicate_prompt_index_rows']} across {summary['sessions_with_duplicate_prompt_indexes']} sessions.",
        f"- Duplicate groups: {summary['duplicate_same_tag_groups']} same-tag, {summary['duplicate_mixed_tag_groups']} mixed-tag.",
        f"- Legacy field-index drift reproduced: tool {summary['legacy_field_tool_mismatch_weight']} weight, LLM {summary['legacy_field_llm_mismatch_events']} events.",
        f"- Normalized semantic drift: tool {summary['normalized_tool_mismatch_weight']} weight ({summary['normalized_tool_mismatch_pct']}%), LLM {summary['normalized_llm_mismatch_events']} events ({summary['normalized_llm_mismatch_pct']}%).",
        f"- Duplicate-index events: tool {summary['duplicate_index_tool_weight']} weight, LLM {summary['duplicate_index_llm_events']} events.",
        f"- Tag-disambiguated duplicate-index events: tool {summary['duplicate_tag_disambiguated_tool_weight']} weight, LLM {summary['duplicate_tag_disambiguated_llm_events']} events.",
        f"- Same-tag duplicate row-identity ambiguity: tool {summary['duplicate_same_tag_identity_ambiguous_tool_weight']} weight, LLM {summary['duplicate_same_tag_identity_ambiguous_llm_events']} events.",
        "",
        "## Claim Gate",
        "",
        f"- Display projection matches event-local prompt tags: `{gate['display_projection_matches_event_local_prompt_tags']}`.",
        f"- Normalized semantic prompt-row lineage supported: `{gate['normalized_semantic_prompt_row_lineage_supported']}`.",
        f"- Strict prompt-row identity supported: `{gate['strict_prompt_row_identity_supported']}`.",
        f"- Duplicate prompt indexes explicitly non-keyed: `{gate['duplicate_prompt_indexes_explicitly_non_keyed']}`.",
        "",
        "## Boundary",
        "",
        result["boundary"],
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run(args: argparse.Namespace) -> dict[str, Any]:
    agentflame = Path(args.agentflame)
    folded = Path(args.semantic_folded)
    r231 = Path(args.r231_json)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    report = json.loads(agentflame.read_text(encoding="utf-8"))
    r231_payload = json.loads(r231.read_text(encoding="utf-8"))
    folded_weights = folded_prompt_weights(folded)
    audit_result = audit(report, folded_weights, args.sample_limit)
    summary = build_summary(audit_result)

    normalized_ok = (
        summary["normalized_tool_mismatch_weight"] == 0
        and summary["normalized_llm_mismatch_events"] == 0
        and audit_result["display_projection"]["exact_match"]
    )
    strict_identity_ok = (
        summary["duplicate_prompt_index_rows"] == 0
        and summary["duplicate_same_tag_identity_ambiguous_tool_weight"] == 0
        and summary["duplicate_same_tag_identity_ambiguous_llm_events"] == 0
    )
    status = "ok_normalized_semantic_lineage" if normalized_ok else "partial_normalized_semantic_lineage"
    boundary = (
        "R233 supports strict semantic prompt-row consistency for generated full-history artifacts after "
        "normalizing duplicate prompt indexes as non-keyed row identifiers. It does not prove strict "
        "prompt-row identity for same-tag duplicate rows, live eBPF provenance, arbitrary agents, C5 user "
        "utility, or C6 tag adequacy."
    )

    result = {
        "schema_version": 1,
        "run_id": "R233",
        "status": status,
        "scope": "generated_artifact_prompt_row_semantic_normalization",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "inputs": {
            "agentflame": rel(agentflame),
            "agentflame_sha256": sha256_file(agentflame),
            "semantic_folded": rel(folded),
            "semantic_folded_sha256": sha256_file(folded),
            "r231_json": rel(r231),
            "r231_status": r231_payload.get("status"),
        },
        "git": {
            "commit": git(["rev-parse", "HEAD"]),
            "branch": git(["branch", "--show-current"]),
            "dirty": bool(git(["status", "--porcelain"])),
        },
        "normalization_contract": {
            "bare_prompt_index_key_when_unique": True,
            "duplicate_prompt_index_row_identity": "non_keyed",
            "semantic_prompt_key": "(prompt_index, prompt_tag)",
            "same_tag_duplicate_rows": "semantic_match_but_row_identity_ambiguous",
            "agentpprof_json_fields": ["prompt_key", "prompt_index_status", "row_ordinal"],
        },
        "summary": summary,
        "display_projection": audit_result["display_projection"],
        "claim_gate": {
            "reads_generated_artifacts_only": True,
            "raw_trace_read": False,
            "llm_called": False,
            "counts_as_live_exact_provenance": False,
            "counts_as_c5_or_c6_human_evidence": False,
            "display_projection_matches_event_local_prompt_tags": audit_result["display_projection"]["exact_match"],
            "normalized_semantic_prompt_row_lineage_supported": normalized_ok,
            "strict_prompt_row_identity_supported": strict_identity_ok,
            "duplicate_prompt_indexes_explicitly_non_keyed": summary["duplicate_prompt_index_rows"] > 0,
        },
        "mismatch_samples": audit_result["mismatch_samples"],
        "boundary": boundary,
    }

    duplicate_csv = out_dir / "duplicate-prompt-index-normalization-r233.csv"
    write_csv(
        duplicate_csv,
        audit_result["duplicate_prompt_index_rows"],
        [
            "source",
            "session_id_hash",
            "session_tag",
            "prompt_index",
            "row_count",
            "distinct_tags",
            "tags",
            "semantic_key_status",
        ],
    )
    result["outputs"] = {
        "json": rel(out_dir / "prompt-row-lineage-r233.json"),
        "markdown": rel(out_dir / "prompt-row-lineage-r233.md"),
        "duplicate_prompt_index_csv": rel(duplicate_csv),
    }
    write_json(out_dir / "prompt-row-lineage-r233.json", result)
    write_markdown(out_dir / "prompt-row-lineage-r233.md", result)
    print(json.dumps({"run_id": "R233", "status": status, "summary": summary}, indent=2, sort_keys=True))
    return result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--agentflame", type=Path, default=DEFAULT_AGENTFLAME)
    parser.add_argument("--semantic-folded", type=Path, default=DEFAULT_SEMANTIC_FOLDED)
    parser.add_argument("--r231-json", type=Path, default=DEFAULT_R231_JSON)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--sample-limit", type=int, default=20)
    return parser


if __name__ == "__main__":
    run(build_parser().parse_args())
