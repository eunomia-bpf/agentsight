#!/usr/bin/env python3
"""R190: audit R189 canonical tag consolidation risks and ablations.

This is a deterministic audit/protocol artifact. It does not label merges as
correct. It identifies high-risk auto-merges, likely under-merge candidates, and
how much each consolidation rule contributes.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import subprocess
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[1]
DEFAULT_AGENTFLAME_DIR = REPO_ROOT / ".agentsight" / "agentflame" / "r170-full-current"
DEFAULT_OUT_DIR = SCRIPT_DIR / "out" / "tag-consolidation-audit-r190"
R189_PATH = SCRIPT_DIR / "r189_tag_consolidation.py"


def load_r189():
    spec = importlib.util.spec_from_file_location("r189_tag_consolidation", R189_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {R189_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


r189 = load_r189()


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


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


def primary_support(profile: Any, dimension: str) -> int:
    if dimension == "llm":
        return int(profile.event_count)
    if dimension in {"session", "prompt"}:
        return int(profile.effect_weight or profile.row_count)
    return int(profile.support(dimension))


def identity_maps(profiles_by_dim: dict[str, dict[str, Any]]) -> dict[str, dict[str, str]]:
    return {
        dimension: {tag: tag for tag in profiles}
        for dimension, profiles in profiles_by_dim.items()
    }


def alias_only_maps(
    profiles_by_dim: dict[str, dict[str, Any]],
    heads_by_dim: dict[str, set[str]],
) -> dict[str, dict[str, str]]:
    maps = identity_maps(profiles_by_dim)
    for dimension, profiles in profiles_by_dim.items():
        heads = heads_by_dim[dimension]
        for tag in profiles:
            canonical = r189.normalize_tag(tag)
            if canonical != tag and canonical in heads:
                maps[dimension][tag] = canonical
    return maps


def lexical_only_maps(
    profiles_by_dim: dict[str, dict[str, Any]],
    heads_by_dim: dict[str, set[str]],
    min_confidence: float,
) -> dict[str, dict[str, str]]:
    maps = alias_only_maps(profiles_by_dim, heads_by_dim)
    for dimension, profiles in profiles_by_dim.items():
        heads = sorted(heads_by_dim[dimension])
        for tag, profile in profiles.items():
            if maps[dimension][tag] != tag:
                continue
            if tag in heads and not r189.looks_compound_or_noisy(tag):
                continue
            best: tuple[float, str] | None = None
            for candidate in heads:
                if candidate == tag:
                    continue
                lex = r189.lexical_score(tag, candidate)
                if not lex:
                    continue
                cand_profile = profiles.get(candidate)
                support_ratio = 0.0
                if cand_profile is not None:
                    support_ratio = min(1.0, r189.math.log1p(cand_profile.support(dimension)) / 10.0)
                score = 0.85 * lex + 0.15 * support_ratio
                if best is None or score > best[0]:
                    best = (score, candidate)
            if best is not None and best[0] >= min_confidence:
                maps[dimension][tag] = best[1]
    return maps


def variant_stack_summaries(
    system: Counter[str],
    token: Counter[str],
    maps: dict[str, dict[str, str]],
) -> tuple[dict[str, Any], dict[str, Any]]:
    canonical_system = r189.canonicalize_counter(
        system,
        lambda stack: r189.canonicalize_system_stack(stack, maps),
    )
    canonical_token = r189.canonicalize_counter(
        token,
        lambda stack: r189.canonicalize_token_stack(stack, maps),
    )
    return r189.stack_summary(system, canonical_system), r189.stack_summary(token, canonical_token)


def dimension_variant_summary(
    profiles_by_dim: dict[str, dict[str, Any]],
    maps: dict[str, dict[str, str]],
) -> dict[str, Any]:
    specs = {
        "session_effect": ("session", "effect_weight", 100),
        "prompt_effect": ("prompt", "effect_weight", 100),
        "prompt_rows": ("prompt", "row_count", 3),
        "llm_events": ("llm", "event_count", 10),
        "llm_tokens": ("llm", "token_weight", 10_000),
    }
    out: dict[str, Any] = {}
    for name, (dimension, field, tail_threshold) in specs.items():
        profiles = profiles_by_dim[dimension]
        raw, canonical = r189.tag_counter_for_dimension(profiles, dimension, maps, field)
        total = sum(raw.values())
        raw_tail = sum(value for value in raw.values() if value < tail_threshold)
        canonical_tail = sum(value for value in canonical.values() if value < tail_threshold)
        changed_tags = sum(1 for tag, canonical_tag in maps[dimension].items() if tag != canonical_tag)
        out[name] = {
            "raw_unique_tags": len(raw),
            "canonical_unique_tags": len(canonical),
            "unique_tag_reduction": len(raw) - len(canonical),
            "unique_tag_reduction_pct": r189.pct(len(raw) - len(canonical), len(raw)),
            "changed_tags": changed_tags,
            "total_weight": total,
            "total_preserved": sum(raw.values()) == sum(canonical.values()),
            "raw_top20_coverage_pct": r189.top_coverage(raw, 20),
            "canonical_top20_coverage_pct": r189.top_coverage(canonical, 20),
            "raw_long_tail_weight_pct": r189.pct(raw_tail, total),
            "canonical_long_tail_weight_pct": r189.pct(canonical_tail, total),
        }
    return out


def summarize_variants(
    profiles_by_dim: dict[str, dict[str, Any]],
    system: Counter[str],
    token: Counter[str],
    current_maps: dict[str, dict[str, str]],
    heads_by_dim: dict[str, set[str]],
    min_confidence: float,
) -> dict[str, Any]:
    variants = {
        "raw": identity_maps(profiles_by_dim),
        "alias_only": alias_only_maps(profiles_by_dim, heads_by_dim),
        "lexical_only": lexical_only_maps(profiles_by_dim, heads_by_dim, min_confidence),
        "profile_guarded_current": current_maps,
    }
    out: dict[str, Any] = {}
    for name, maps in variants.items():
        system_summary, token_summary = variant_stack_summaries(system, token, maps)
        out[name] = {
            "dimensions": dimension_variant_summary(profiles_by_dim, maps),
            "system_stack_consolidation": system_summary,
            "token_stack_consolidation": token_summary,
        }
    return out


def counter_top(counter: Counter[str], limit: int = 6) -> str:
    return "; ".join(f"{key}={value}" for key, value in counter.most_common(limit))


def build_lookup(mapping_rows: list[dict[str, Any]]) -> dict[tuple[str, str], dict[str, Any]]:
    return {(str(row["dimension"]), str(row["raw_tag"])): row for row in mapping_rows}


def risk_rows(
    profiles_by_dim: dict[str, dict[str, Any]],
    mapping_rows: list[dict[str, Any]],
    limit: int,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    by_key = build_lookup(mapping_rows)
    overmerge: list[dict[str, Any]] = []
    undermerge: list[dict[str, Any]] = []

    for row in mapping_rows:
        dimension = str(row["dimension"])
        action = str(row["action"])
        profile = profiles_by_dim[dimension][str(row["raw_tag"])]
        support = int(row["support"])
        sim = float(row["profile_similarity"])
        confidence = float(row["confidence"])
        risk_reasons: list[str] = []
        if action == "merge":
            if row["reason"] == "alias":
                risk_reasons.append("dictionary_alias_needs_human_check")
            if row["reason"] == "lexical+profile" and sim < 0.55:
                risk_reasons.append("low_profile_similarity")
            if confidence < 0.76:
                risk_reasons.append("near_threshold_confidence")
            if support >= 100:
                risk_reasons.append("high_support_merge")
            if risk_reasons:
                overmerge.append(
                    {
                        "audit_type": "overmerge_proxy",
                        "dimension": dimension,
                        "raw_tag": row["raw_tag"],
                        "canonical_tag": row["canonical_tag"],
                        "reason": row["reason"],
                        "confidence": row["confidence"],
                        "profile_similarity": row["profile_similarity"],
                        "support": support,
                        "risk_reasons": ";".join(risk_reasons),
                        "raw_top_processes": counter_top(profile.processes),
                        "raw_top_effects": counter_top(profile.effects),
                        "raw_top_paths": counter_top(profile.paths),
                        "raw_top_prompts": counter_top(profile.prompts),
                        "raw_top_sessions": counter_top(profile.sessions),
                        "audit_label": "",
                        "audit_notes": "",
                    }
                )
        elif action == "review":
            undermerge.append(
                {
                    "audit_type": "undermerge_proxy",
                    "dimension": dimension,
                    "raw_tag": row["raw_tag"],
                    "canonical_tag": row["suggested_tag"],
                    "reason": row["reason"],
                    "confidence": row["confidence"],
                    "profile_similarity": row["profile_similarity"],
                    "support": support,
                    "risk_reasons": "review_suggestion_not_applied",
                    "raw_top_processes": counter_top(profile.processes),
                    "raw_top_effects": counter_top(profile.effects),
                    "raw_top_paths": counter_top(profile.paths),
                    "raw_top_prompts": counter_top(profile.prompts),
                    "raw_top_sessions": counter_top(profile.sessions),
                    "audit_label": "",
                    "audit_notes": "",
                }
            )

    # Add unmerged noisy tags with moderate support as possible under-merges.
    for dimension, profiles in profiles_by_dim.items():
        for tag, profile in profiles.items():
            row = by_key.get((dimension, tag))
            if row is None or row["action"] != "keep":
                continue
            support = primary_support(profile, dimension)
            if support < 25 or not r189.looks_compound_or_noisy(tag):
                continue
            undermerge.append(
                {
                    "audit_type": "undermerge_proxy",
                    "dimension": dimension,
                    "raw_tag": tag,
                    "canonical_tag": tag,
                    "reason": "no_merge_noisy_supported_tag",
                    "confidence": 0,
                    "profile_similarity": 0,
                    "support": support,
                    "risk_reasons": "noisy_tag_retained",
                    "raw_top_processes": counter_top(profile.processes),
                    "raw_top_effects": counter_top(profile.effects),
                    "raw_top_paths": counter_top(profile.paths),
                    "raw_top_prompts": counter_top(profile.prompts),
                    "raw_top_sessions": counter_top(profile.sessions),
                    "audit_label": "",
                    "audit_notes": "",
                }
            )

    overmerge.sort(key=lambda row: (-int(row["support"]), str(row["dimension"]), str(row["raw_tag"])))
    undermerge.sort(key=lambda row: (-int(row["support"]), str(row["dimension"]), str(row["raw_tag"])))
    return overmerge[:limit], undermerge[:limit]


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def write_variant_csv(path: Path, variants: dict[str, Any]) -> None:
    rows: list[dict[str, Any]] = []
    for variant, payload in variants.items():
        for dimension, summary in payload["dimensions"].items():
            rows.append(
                {
                    "variant": variant,
                    "view": dimension,
                    "raw_unique": summary["raw_unique_tags"],
                    "canonical_unique": summary["canonical_unique_tags"],
                    "unique_reduction_pct": summary["unique_tag_reduction_pct"],
                    "changed_tags": summary["changed_tags"],
                    "raw_top20_coverage_pct": summary["raw_top20_coverage_pct"],
                    "canonical_top20_coverage_pct": summary["canonical_top20_coverage_pct"],
                    "raw_long_tail_weight_pct": summary["raw_long_tail_weight_pct"],
                    "canonical_long_tail_weight_pct": summary["canonical_long_tail_weight_pct"],
                }
            )
        for stack_name in ("system_stack_consolidation", "token_stack_consolidation"):
            summary = payload[stack_name]
            rows.append(
                {
                    "variant": variant,
                    "view": stack_name,
                    "raw_unique": summary["raw_unique_stacks"],
                    "canonical_unique": summary["canonical_unique_stacks"],
                    "unique_reduction_pct": summary["unique_stack_reduction_pct"],
                    "changed_tags": "",
                    "raw_top20_coverage_pct": summary["raw_top20_coverage_pct"],
                    "canonical_top20_coverage_pct": summary["canonical_top20_coverage_pct"],
                    "raw_long_tail_weight_pct": "",
                    "canonical_long_tail_weight_pct": "",
                }
            )
    write_csv(
        path,
        rows,
        [
            "variant",
            "view",
            "raw_unique",
            "canonical_unique",
            "unique_reduction_pct",
            "changed_tags",
            "raw_top20_coverage_pct",
            "canonical_top20_coverage_pct",
            "raw_long_tail_weight_pct",
            "canonical_long_tail_weight_pct",
        ],
    )


def write_markdown(path: Path, payload: dict[str, Any]) -> None:
    current = payload["variants"]["profile_guarded_current"]
    alias = payload["variants"]["alias_only"]
    lexical = payload["variants"]["lexical_only"]
    lines = [
        "# R190 Tag Consolidation Audit",
        "",
        f"Status: `{payload['status']}`",
        "",
        "## Scope",
        "",
        "- Reads generated R170/R189-style artifacts only; raw traces are not read or mutated.",
        "- Produces risk proxies and a blank audit packet; it is not human adequacy evidence.",
        "",
        "## Ablation Summary",
        "",
        "| variant | prompt-effect tags | llm-event tags | system stacks | token stacks |",
        "|---|---:|---:|---:|---:|",
    ]
    for name, variant in (
        ("raw", payload["variants"]["raw"]),
        ("alias_only", alias),
        ("lexical_only", lexical),
        ("profile_guarded_current", current),
    ):
        lines.append(
            f"| {name} | "
            f"{variant['dimensions']['prompt_effect']['canonical_unique_tags']} | "
            f"{variant['dimensions']['llm_events']['canonical_unique_tags']} | "
            f"{variant['system_stack_consolidation']['canonical_unique_stacks']} | "
            f"{variant['token_stack_consolidation']['canonical_unique_stacks']} |"
        )
    lines.extend(
        [
            "",
            "## Risk Proxies",
            "",
            f"- Over-merge proxy rows exported: {payload['risk_summary']['overmerge_proxy_rows']}.",
            f"- Under-merge proxy rows exported: {payload['risk_summary']['undermerge_proxy_rows']}.",
            f"- Applied merges by reason: `{payload['merge_diagnostics']}`.",
            "- Scoring command after two independent labeler sheets: "
            "`python3 docs/visexp/r190_score_merge_audit.py --labeler-1 <sheet1> --labeler-2 <sheet2> --adjudication <adjudication.csv>`.",
            "",
            "## Interpretation Boundary",
            "",
            "R190 can say which consolidation rules account for tag-count reductions and which rows need human audit. "
            "It cannot say the merges are semantically correct until the audit labels are collected.",
            "",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def run(agentflame_dir: Path, out_dir: Path, min_confidence: float, risk_limit: int) -> dict[str, Any]:
    report_path = agentflame_dir / "agentflame.json"
    system_path = agentflame_dir / "semantic-system.folded.txt"
    token_path = agentflame_dir / "semantic-token.folded.txt"
    report = r189.read_json(report_path)
    system = r189.read_folded(system_path)
    token = r189.read_folded(token_path)
    profiles = r189.collect_profiles(report, system, token)
    current_maps, mapping_rows, heads_by_dim = r189.build_maps(profiles, min_confidence)
    variants = summarize_variants(profiles, system, token, current_maps, heads_by_dim, min_confidence)
    overmerge, undermerge = risk_rows(profiles, mapping_rows, risk_limit)
    audit_rows = []
    for idx, row in enumerate([*overmerge, *undermerge], 1):
        audit_rows.append({"audit_id": f"R190-{idx:04d}", **row})

    out_dir.mkdir(parents=True, exist_ok=True)
    packet_fields = [
        "audit_id",
        "audit_type",
        "dimension",
        "raw_tag",
        "canonical_tag",
        "reason",
        "confidence",
        "profile_similarity",
        "support",
        "risk_reasons",
        "raw_top_processes",
        "raw_top_effects",
        "raw_top_paths",
        "raw_top_prompts",
        "raw_top_sessions",
        "audit_label",
        "audit_notes",
    ]
    write_csv(out_dir / "merge-risk-audit-packet-r190.csv", audit_rows, packet_fields)
    write_variant_csv(out_dir / "consolidation-ablation-r190.csv", variants)

    merge_diagnostics = r189.merge_diagnostics(mapping_rows)
    payload = {
        "schema_version": 1,
        "run_id": "R190",
        "status": "tag_consolidation_audit_packet_ready",
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "input": {
            "agentflame_dir": rel(agentflame_dir),
            "report_sha256": sha256_file(report_path),
            "system_folded_sha256": sha256_file(system_path),
            "token_folded_sha256": sha256_file(token_path),
            "raw_trace_policy": "read generated AgentFlame artifacts only; do not mutate raw traces",
        },
        "method": {
            "min_confidence": min_confidence,
            "risk_limit_per_class": risk_limit,
            "variants": ["raw", "alias_only", "lexical_only", "profile_guarded_current"],
            "risk_proxy_only": True,
            "human_labels_collected": 0,
        },
        "merge_diagnostics": merge_diagnostics,
        "variants": variants,
        "risk_summary": {
            "overmerge_proxy_rows": len(overmerge),
            "undermerge_proxy_rows": len(undermerge),
            "audit_packet_rows": len(audit_rows),
            "human_labels_collected": 0,
        },
        "artifacts": {
            "summary_md": rel(out_dir / "tag-consolidation-audit-r190.md"),
            "summary_json": rel(out_dir / "tag-consolidation-audit-r190.json"),
            "audit_packet_csv": rel(out_dir / "merge-risk-audit-packet-r190.csv"),
            "ablation_csv": rel(out_dir / "consolidation-ablation-r190.csv"),
        },
        "claim_boundary": (
            "R190 is an audit protocol and deterministic risk analysis. It does not prove "
            "merge correctness, tag adequacy, or developer utility without human audit labels."
        ),
        "provenance": {
            "repo_commit": git(["rev-parse", "HEAD"]),
            "repo_dirty": bool(git(["status", "--short"])),
            "script_sha256": sha256_file(Path(__file__).resolve()),
            "r189_script_sha256": sha256_file(R189_PATH),
        },
    }
    write_json(out_dir / "tag-consolidation-audit-r190.json", payload)
    write_markdown(out_dir / "tag-consolidation-audit-r190.md", payload)
    return payload


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--agentflame-dir", type=Path, default=DEFAULT_AGENTFLAME_DIR)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--min-confidence", type=float, default=0.72)
    parser.add_argument("--risk-limit", type=int, default=80)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    payload = run(args.agentflame_dir, args.out_dir, args.min_confidence, args.risk_limit)
    print(args.out_dir)
    print(payload["status"])
    print("audit_packet_rows", payload["risk_summary"]["audit_packet_rows"])
    current = payload["variants"]["profile_guarded_current"]
    print(
        "current prompt_effect",
        current["dimensions"]["prompt_effect"]["raw_unique_tags"],
        "->",
        current["dimensions"]["prompt_effect"]["canonical_unique_tags"],
    )
    print(
        "current system_stacks",
        current["system_stack_consolidation"]["raw_unique_stacks"],
        "->",
        current["system_stack_consolidation"]["canonical_unique_stacks"],
    )


if __name__ == "__main__":
    main()
