#!/usr/bin/env python3
"""R212: display-compaction ablation over generated semantic stacks.

This run compares raw, alias-only, profile-guarded-candidate, and conservative
R209 display policies for session/prompt labels over the R170 semantic-system
folded stacks. It reads generated artifacts only. It does not read raw
Codex/Claude traces, does not call an LLM, and does not claim merge quality
without human labels.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import json
import subprocess
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[1]
DEFAULT_FOLDED = REPO_ROOT / ".agentsight" / "agentflame" / "r170-full-current" / "semantic-system.folded.txt"
DEFAULT_R196 = SCRIPT_DIR / "out" / "long-tail-governance-r196" / "long-tail-governance-r196.csv"
DEFAULT_R209_CSV = SCRIPT_DIR / "out" / "reversible-display-map-r209" / "active-display-map-r209.csv"
DEFAULT_R209_JSON = SCRIPT_DIR / "out" / "reversible-display-map-r209" / "reversible-display-map-r209.json"
DEFAULT_OUT = SCRIPT_DIR / "out" / "display-compaction-ablation-r212"

VARIANT_FIELDS = [
    "variant",
    "description",
    "total_weight",
    "stack_count",
    "stack_reduction_vs_raw",
    "stack_reduction_vs_raw_pct",
    "unique_session_tags",
    "unique_prompt_tags",
    "active_session_merges",
    "active_prompt_merges",
    "affected_stack_rows",
    "affected_weight",
    "affected_weight_pct",
    "unreviewed_profile_merge_rows_active",
    "unreviewed_profile_merge_weight_active",
    "unreviewed_profile_merge_weight_pct",
]

BEHAVIOR_FIELDS = [
    "variant",
    "rank",
    "behavior_key",
    "total_weight",
    "distinct_prompt_tags",
    "top_prompt",
    "top_prompt_weight",
    "top_prompt_share_pct",
    "ambiguous_weight",
    "ambiguous_share_pct",
    "distinct_prompt_delta_vs_raw",
    "ambiguous_share_delta_vs_raw_pct_points",
    "top_prompt_splits",
]

SELECTED_BEHAVIOR_KEYS = [
    "process:git;effect:read;status:ok",
    "process:cargo;effect:test;status:ok",
    "process:rg;effect:read;status:ok",
    "process:sed;effect:read;status:ok",
]

COMPACTED_TAG_LEVELS = ["session", "prompt"]
EXCLUDED_TAG_LEVELS = ["llm", "token"]


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


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def as_int(value: Any) -> int:
    if value in (None, ""):
        return 0
    return int(float(str(value)))


def pct(part: int | float, whole: int | float) -> float | None:
    if not whole:
        return None
    return round(100.0 * float(part) / float(whole), 3)


def delta_pct_points(new: float | None, old: float | None) -> float | None:
    if new is None or old is None:
        return None
    return round(float(new) - float(old), 3)


def parse_folded_line(line: str) -> tuple[str, int]:
    stack, _, weight = line.rstrip("\n").rpartition(" ")
    if not stack or not weight:
        raise ValueError(f"invalid folded line: {line[:160]}")
    return stack, as_int(weight)


def read_folded(path: Path) -> Counter[str]:
    out: Counter[str] = Counter()
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            stack, weight = parse_folded_line(line)
            out[stack] += weight
    return out


def split_frame(frame: str) -> tuple[str, str] | None:
    if ":" not in frame:
        return None
    key, value = frame.split(":", 1)
    return key, value


def frames_from_stack(stack: str) -> dict[str, list[str]]:
    frames: dict[str, list[str]] = defaultdict(list)
    for frame in stack.split(";"):
        parsed = split_frame(frame)
        if parsed:
            frames[parsed[0]].append(parsed[1])
    return frames


def first_frame(frames: dict[str, list[str]], key: str, default: str = "") -> str:
    values = frames.get(key) or []
    return values[0] if values else default


def process_label(frames: dict[str, list[str]]) -> str:
    process = first_frame(frames, "process")
    if process:
        return process
    call = first_frame(frames, "call")
    if call:
        return call.replace("/", ":")
    return "unknown"


def behavior_key_for(stack: str) -> str:
    frames = frames_from_stack(stack)
    process = process_label(frames)
    effect = first_frame(frames, "effect", "unknown")
    status = first_frame(frames, "status", "unknown")
    return f"process:{process};effect:{effect};status:{status}"


def prompt_for(stack: str) -> str:
    return first_frame(frames_from_stack(stack), "prompt", "unknown")


def session_for(stack: str) -> str:
    return first_frame(frames_from_stack(stack), "session", "unknown")


def compact_counter(counter: Counter[str], limit: int = 8) -> str:
    return "; ".join(f"{key}={value}" for key, value in counter.most_common(limit))


def display_rows_by_dimension(rows: list[dict[str, str]], dimension: str) -> dict[str, dict[str, str]]:
    return {row.get("raw_tag", ""): row for row in rows if row.get("dimension") == dimension}


def build_maps(
    r196_rows: list[dict[str, str]],
    r209_rows: list[dict[str, str]],
) -> tuple[dict[str, dict[str, str]], dict[str, set[str]]]:
    maps = {
        "raw": {"session": {}, "prompt": {}},
        "alias_only": {"session": {}, "prompt": {}},
        "profile_guarded_candidate_applied": {"session": {}, "prompt": {}},
        "r209_conservative_display": {"session": {}, "prompt": {}},
    }
    pending_profile = {"session": set(), "prompt": set()}
    for row in r196_rows:
        dimension = row.get("dimension", "")
        if dimension not in {"session", "prompt"}:
            continue
        raw = row.get("raw_tag", "")
        canonical = row.get("canonical_tag") or raw
        action = row.get("governance_action", "")
        reason = row.get("governance_reasons", "")
        if not raw:
            continue
        if action == "auto_canonicalize_existing" and reason == "r189_alias" and canonical != raw:
            maps["alias_only"][dimension][raw] = canonical
        if action == "auto_canonicalize_existing" and canonical != raw:
            maps["profile_guarded_candidate_applied"][dimension][raw] = canonical
            if reason != "r189_alias":
                pending_profile[dimension].add(raw)

    for row in r209_rows:
        dimension = row.get("dimension", "")
        if dimension not in {"session", "prompt"}:
            continue
        raw = row.get("raw_tag", "")
        active = row.get("active_display_tag") or raw
        if raw and active != raw:
            maps["r209_conservative_display"][dimension][raw] = active

    return maps, pending_profile


def transform_stack(
    stack: str,
    session_map: dict[str, str],
    prompt_map: dict[str, str],
) -> tuple[str, bool]:
    changed = False
    out: list[str] = []
    for frame in stack.split(";"):
        parsed = split_frame(frame)
        if not parsed:
            out.append(frame)
            continue
        key, value = parsed
        if key == "session" and value in session_map:
            out.append(f"session:{session_map[value]}")
            changed = True
        elif key == "prompt" and value in prompt_map:
            out.append(f"prompt:{prompt_map[value]}")
            changed = True
        else:
            out.append(frame)
    return ";".join(out), changed


def apply_variant(
    folded: Counter[str],
    session_map: dict[str, str],
    prompt_map: dict[str, str],
    pending_session: set[str],
    pending_prompt: set[str],
) -> tuple[Counter[str], dict[str, int]]:
    out: Counter[str] = Counter()
    affected_rows = 0
    affected_weight = 0
    pending_rows = 0
    pending_weight = 0
    for stack, weight in folded.items():
        transformed, changed = transform_stack(stack, session_map, prompt_map)
        out[transformed] += weight
        if changed:
            affected_rows += 1
            affected_weight += weight
        frames = frames_from_stack(stack)
        uses_pending = first_frame(frames, "session") in pending_session or first_frame(frames, "prompt") in pending_prompt
        if uses_pending:
            pending_rows += 1
            pending_weight += weight
    return out, {
        "affected_stack_rows": affected_rows,
        "affected_weight": affected_weight,
        "unreviewed_profile_merge_rows_active": pending_rows,
        "unreviewed_profile_merge_weight_active": pending_weight,
    }


def variant_summary_rows(
    folded: Counter[str],
    maps: dict[str, dict[str, dict[str, str]]],
    pending_profile: dict[str, set[str]],
) -> tuple[list[dict[str, Any]], dict[str, Counter[str]], dict[str, dict[str, int]]]:
    raw_total = sum(folded.values())
    raw_stack_count = len(folded)
    summaries: list[dict[str, Any]] = []
    transformed_by_variant: dict[str, Counter[str]] = {}
    stats_by_variant: dict[str, dict[str, int]] = {}
    descriptions = {
        "raw": "original one-word tags",
        "alias_only": "deterministic aliases active; profile merges inactive",
        "profile_guarded_candidate_applied": "hypothetical: apply R189 alias plus lexical/profile merge candidates",
        "r209_conservative_display": "R209 active display map: alias active, profile/regeneration pending",
    }
    for variant in ["raw", "alias_only", "profile_guarded_candidate_applied", "r209_conservative_display"]:
        pending_session = pending_profile["session"] if variant == "profile_guarded_candidate_applied" else set()
        pending_prompt = pending_profile["prompt"] if variant == "profile_guarded_candidate_applied" else set()
        transformed, stats = apply_variant(
            folded,
            maps[variant]["session"],
            maps[variant]["prompt"],
            pending_session,
            pending_prompt,
        )
        transformed_by_variant[variant] = transformed
        stats_by_variant[variant] = stats
        sessions = {session_for(stack) for stack in transformed}
        prompts = {prompt_for(stack) for stack in transformed}
        summaries.append(
            {
                "variant": variant,
                "description": descriptions[variant],
                "total_weight": sum(transformed.values()),
                "stack_count": len(transformed),
                "stack_reduction_vs_raw": raw_stack_count - len(transformed),
                "stack_reduction_vs_raw_pct": pct(raw_stack_count - len(transformed), raw_stack_count),
                "unique_session_tags": len(sessions),
                "unique_prompt_tags": len(prompts),
                "active_session_merges": len(maps[variant]["session"]),
                "active_prompt_merges": len(maps[variant]["prompt"]),
                "affected_stack_rows": stats["affected_stack_rows"],
                "affected_weight": stats["affected_weight"],
                "affected_weight_pct": pct(stats["affected_weight"], raw_total),
                "unreviewed_profile_merge_rows_active": stats["unreviewed_profile_merge_rows_active"],
                "unreviewed_profile_merge_weight_active": stats["unreviewed_profile_merge_weight_active"],
                "unreviewed_profile_merge_weight_pct": pct(
                    stats["unreviewed_profile_merge_weight_active"], raw_total
                ),
            }
        )
    return summaries, transformed_by_variant, stats_by_variant


def behavior_records_for_variant(variant: str, folded: Counter[str]) -> dict[str, dict[str, Any]]:
    groups: dict[str, Counter[str]] = defaultdict(Counter)
    for stack, weight in folded.items():
        groups[behavior_key_for(stack)][prompt_for(stack)] += weight
    out: dict[str, dict[str, Any]] = {}
    for key, prompts in groups.items():
        total = sum(prompts.values())
        top_prompt, top_weight = prompts.most_common(1)[0]
        out[key] = {
            "variant": variant,
            "behavior_key": key,
            "total_weight": total,
            "distinct_prompt_tags": len(prompts),
            "top_prompt": top_prompt,
            "top_prompt_weight": top_weight,
            "top_prompt_share_pct": pct(top_weight, total),
            "ambiguous_weight": total - top_weight,
            "ambiguous_share_pct": pct(total - top_weight, total),
            "top_prompt_splits": compact_counter(prompts),
        }
    return out


def behavior_ambiguity_rows(transformed_by_variant: dict[str, Counter[str]], top_n: int = 16) -> list[dict[str, Any]]:
    by_variant = {
        variant: behavior_records_for_variant(variant, folded)
        for variant, folded in transformed_by_variant.items()
    }
    raw_records = by_variant["raw"]
    top_raw = sorted(raw_records.values(), key=lambda row: (row["ambiguous_weight"], row["total_weight"]), reverse=True)
    keys = list(dict.fromkeys(SELECTED_BEHAVIOR_KEYS + [row["behavior_key"] for row in top_raw[:top_n]]))

    rows: list[dict[str, Any]] = []
    rank = 0
    for key in keys:
        raw = raw_records.get(key)
        for variant in ["raw", "alias_only", "profile_guarded_candidate_applied", "r209_conservative_display"]:
            record = by_variant[variant].get(key)
            if not record:
                continue
            if variant == "raw":
                rank += 1
            baseline = raw or record
            rows.append(
                {
                    **record,
                    "rank": rank,
                    "distinct_prompt_delta_vs_raw": record["distinct_prompt_tags"]
                    - baseline["distinct_prompt_tags"],
                    "ambiguous_share_delta_vs_raw_pct_points": delta_pct_points(
                        record["ambiguous_share_pct"], baseline["ambiguous_share_pct"]
                    ),
                }
            )
    return rows


def summarize(
    folded: Counter[str],
    variant_rows: list[dict[str, Any]],
    behavior_rows: list[dict[str, Any]],
    transformed_by_variant: dict[str, Counter[str]],
    r209_payload: dict[str, Any],
) -> dict[str, Any]:
    total_weight = sum(folded.values())
    variant_by_name = {row["variant"]: row for row in variant_rows}
    selected = [
        row for row in behavior_rows
        if row["behavior_key"] in SELECTED_BEHAVIOR_KEYS and row["variant"] in {"raw", "r209_conservative_display", "profile_guarded_candidate_applied"}
    ]
    return {
        "semantic_system_stacks_raw": len(folded),
        "semantic_system_total_weight": total_weight,
        "variant_count": len(variant_rows),
        "behavior_rows": len(behavior_rows),
        "effect_weight_conserved": all(row["total_weight"] == total_weight for row in variant_rows),
        "r209_alias_only_equivalent": transformed_by_variant["alias_only"]
        == transformed_by_variant["r209_conservative_display"],
        "raw_stack_count": variant_by_name["raw"]["stack_count"],
        "r209_stack_count": variant_by_name["r209_conservative_display"]["stack_count"],
        "profile_guarded_stack_count": variant_by_name["profile_guarded_candidate_applied"]["stack_count"],
        "r209_active_display_labels": (r209_payload.get("summary") or {}).get("active_display_unique_labels"),
        "r209_active_alias_rows": (r209_payload.get("summary") or {}).get("alias_active_rows"),
        "r209_pending_merge_candidate_rows": (r209_payload.get("summary") or {}).get("pending_merge_candidate_rows"),
        "r209_regenerated_candidate_rows": (r209_payload.get("summary") or {}).get("regenerated_candidate_rows"),
        "profile_guarded_unreviewed_weight_pct": variant_by_name[
            "profile_guarded_candidate_applied"
        ]["unreviewed_profile_merge_weight_pct"],
        "selected_behavior_rows": selected,
        "false_merge_rate_pct": None,
        "missed_merge_rate_pct": None,
    }


def write_markdown(path: Path, payload: dict[str, Any], variant_rows: list[dict[str, Any]], behavior_rows: list[dict[str, Any]]) -> None:
    summary = payload["summary"]
    lines = [
        "# R212 Display-Compaction Ablation",
        "",
        f"Status: `{payload['status']}`",
        "",
        "## Boundary",
        "",
        "- Reads generated R170/R196/R209 artifacts only.",
        "- Does not read or mutate raw Codex/Claude traces.",
        "- Does not call an LLM.",
        "- Applies display compaction only to session/prompt tags in semantic-system stacks; LLM/token display compaction is out of scope for this run.",
        "- Reports display-policy mechanics only; false-merge and missed-merge rates remain `n/a` until human labels exist.",
        "",
        "## Variant Summary",
        "",
        "| variant | stacks | session tags | prompt tags | affected weight pct | unreviewed profile weight pct |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for row in variant_rows:
        lines.append(
            f"| `{row['variant']}` | {row['stack_count']} | {row['unique_session_tags']} | "
            f"{row['unique_prompt_tags']} | {row['affected_weight_pct']} | "
            f"{row['unreviewed_profile_merge_weight_pct']} |"
        )
    lines.extend(
        [
            "",
            "## Selected Behavior Ambiguity",
            "",
            "| behavior | variant | distinct prompts | ambiguous share pct | top prompt splits |",
            "|---|---|---:|---:|---|",
        ]
    )
    for row in behavior_rows:
        if row["behavior_key"] not in SELECTED_BEHAVIOR_KEYS:
            continue
        lines.append(
            f"| `{row['behavior_key']}` | `{row['variant']}` | {row['distinct_prompt_tags']} | "
            f"{row['ambiguous_share_pct']} | {row['top_prompt_splits']} |"
        )
    lines.extend(
        [
            "",
            "## Claim Boundary",
            "",
            f"R212 conserves total system-effect weight across all variants: `{summary['effect_weight_conserved']}`. "
            f"The conservative R209 display policy is alias-only equivalent: `{summary['r209_alias_only_equivalent']}`. "
            "The profile-guarded variant is reported as a hypothetical candidate-applied view, not a reviewed default. "
            "R212 cannot support semantic adequacy, merge quality, developer utility, or community adoption.",
            "",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def build_payload(args: argparse.Namespace) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]:
    for path in [args.folded, args.r196_csv, args.r209_csv, args.r209_json]:
        if not path.exists():
            raise FileNotFoundError(f"missing R212 input artifact: {rel(path)}")
    folded = read_folded(args.folded)
    r196_rows = read_csv(args.r196_csv)
    r209_rows = read_csv(args.r209_csv)
    r209_payload = json.loads(args.r209_json.read_text(encoding="utf-8"))

    maps, pending_profile = build_maps(r196_rows, r209_rows)
    variant_rows, transformed_by_variant, _stats = variant_summary_rows(folded, maps, pending_profile)
    behavior_rows = behavior_ambiguity_rows(transformed_by_variant)
    summary = summarize(folded, variant_rows, behavior_rows, transformed_by_variant, r209_payload)
    status = "display_compaction_ablation_ready_no_quality_claims"
    payload = {
        "run_id": "R212",
        "schema_version": 1,
        "generated_at": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),
        "status": status,
        "claim": "C3 mechanism; C6 protocol/gate only",
        "claim_boundary": (
            "R212 compares session/prompt display-compaction policies over generated semantic-system folded stacks. "
            "It verifies weight conservation and the conservative R209 alias-only active policy. "
            "It does not cover LLM/token display compaction and does not support semantic adequacy, "
            "merge quality, developer utility, or community adoption."
        ),
        "input": {
            "folded": rel(args.folded),
            "folded_sha256": sha256_file(args.folded),
            "r196_csv": rel(args.r196_csv),
            "r196_csv_sha256": sha256_file(args.r196_csv),
            "r209_csv": rel(args.r209_csv),
            "r209_csv_sha256": sha256_file(args.r209_csv),
            "r209_json": rel(args.r209_json),
            "r209_json_sha256": sha256_file(args.r209_json),
        },
        "method": {
            "compacted_tag_levels": COMPACTED_TAG_LEVELS,
            "excluded_tag_levels": EXCLUDED_TAG_LEVELS,
            "raw": "no session/prompt display remapping",
            "alias_only": "apply R189 deterministic aliases from R196 only",
            "profile_guarded_candidate_applied": "hypothetically apply all R196 auto_canonicalize_existing session/prompt rows, including unreviewed lexical/profile candidates",
            "r209_conservative_display": "apply active_display_tag from R209; after R209 revision this is alias-only for session/prompt stacks",
            "behavior_key": "process/effect/status, excluding path/domain, to expose baseline-collapse ambiguity",
        },
        "summary": summary,
        "claim_gate": {
            "display_compaction_ablation_supported": bool(summary["effect_weight_conserved"]),
            "effect_weight_conserved": bool(summary["effect_weight_conserved"]),
            "r209_alias_only_active_verified": bool(summary["r209_alias_only_equivalent"]),
            "reads_generated_artifacts_only": True,
            "raw_trace_read": False,
            "llm_called": False,
            "false_merge_rate_supported": False,
            "missed_merge_rate_supported": False,
            "canonicalization_quality_supported": False,
            "semantic_adequacy_supported": False,
            "developer_utility_supported": False,
            "community_adoption_supported": False,
            "llm_token_display_compaction_supported": False,
            "requires_r190_labels_for_merge_quality": True,
            "requires_r203_labels_for_promotion_quality": True,
        },
        "outputs": {
            "summary_json": rel(args.out_dir / "display-compaction-ablation-r212.json"),
            "summary_md": rel(args.out_dir / "display-compaction-ablation-r212.md"),
            "variant_summary_csv": rel(args.out_dir / "variant-summary-r212.csv"),
            "behavior_ambiguity_csv": rel(args.out_dir / "behavior-ambiguity-r212.csv"),
        },
        "provenance": {
            "repo_commit": git(["rev-parse", "HEAD"]),
            "repo_dirty": bool(git(["status", "--short"])),
            "script_sha256": sha256_file(Path(__file__).resolve()),
        },
    }
    return payload, variant_rows, behavior_rows


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--folded", type=Path, default=DEFAULT_FOLDED)
    parser.add_argument("--r196-csv", type=Path, default=DEFAULT_R196)
    parser.add_argument("--r209-csv", type=Path, default=DEFAULT_R209_CSV)
    parser.add_argument("--r209-json", type=Path, default=DEFAULT_R209_JSON)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    payload, variant_rows, behavior_rows = build_payload(args)
    args.out_dir.mkdir(parents=True, exist_ok=True)
    write_json(args.out_dir / "display-compaction-ablation-r212.json", payload)
    write_markdown(args.out_dir / "display-compaction-ablation-r212.md", payload, variant_rows, behavior_rows)
    write_csv(args.out_dir / "variant-summary-r212.csv", variant_rows, VARIANT_FIELDS)
    write_csv(args.out_dir / "behavior-ambiguity-r212.csv", behavior_rows, BEHAVIOR_FIELDS)
    print(json.dumps({"status": payload["status"], "summary_json": payload["outputs"]["summary_json"]}))


if __name__ == "__main__":
    main()
