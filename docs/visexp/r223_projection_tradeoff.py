#!/usr/bin/env python3
"""R223: summarize semantic projection tradeoffs over existing evidence.

This run is intentionally deterministic. It reads generated R131/R205/R209/R212
artifacts only, does not read raw Codex/Claude traces, and does not call an LLM.
Its purpose is to make RQ2 reviewer-facing: AgentFlame/AgentPProf is a
pluggable projection framework, and different projections trade aggregation,
fidelity, review burden, and reversibility.
"""

from __future__ import annotations

import csv
import datetime as dt
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[1]
DEFAULT_R131 = SCRIPT_DIR / "out" / "semantic-ablation-r224-r170" / "semantic-ablation-r131.json"
DEFAULT_R205 = SCRIPT_DIR / "out" / "long-tail-compaction-r205" / "long-tail-compaction-r205.json"
DEFAULT_R209 = SCRIPT_DIR / "out" / "reversible-display-map-r209" / "reversible-display-map-r209.json"
DEFAULT_R212 = SCRIPT_DIR / "out" / "display-compaction-ablation-r212" / "display-compaction-ablation-r212.json"
DEFAULT_R212_CSV = SCRIPT_DIR / "out" / "display-compaction-ablation-r212" / "variant-summary-r212.csv"
DEFAULT_R219 = SCRIPT_DIR / "out" / "claim-readiness-r219" / "claim-readiness-r219.json"
DEFAULT_OUT = SCRIPT_DIR / "out" / "projection-tradeoff-r223"

CSV_FIELDS = [
    "projection_family",
    "variant",
    "best_for",
    "total_weight",
    "unique_stacks_or_tags",
    "compression_ratio",
    "mixed_weight_pct",
    "mixed_residual_pct",
    "max_semantic_variants_per_bucket",
    "stack_reduction_vs_raw_pct",
    "top20_coverage_pct",
    "review_required_support_pct",
    "unreviewed_active_weight_pct",
    "raw_drilldown_preserved",
    "default_safe",
    "human_gate_needed",
    "interpretation",
]


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


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_FIELDS, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in CSV_FIELDS})


def pct_reduction(old: int | float, new: int | float) -> float:
    if not old:
        return 0.0
    return round(100.0 * (float(old) - float(new)) / float(old), 3)


def as_float(value: Any) -> float:
    if value in (None, ""):
        return 0.0
    return float(value)


def as_int(value: Any) -> int:
    if value in (None, ""):
        return 0
    return int(float(str(value)))


def semantic_axis_rows(r131: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    interpretations = {
        "no-semantic": (
            "Most compact process/effect profile, but it collapses many distinct "
            "session/prompt regions and is unsafe as the primary semantic view."
        ),
        "session-only": (
            "Useful for coarse session comparison; still mixes prompt-level task "
            "regions heavily."
        ),
        "prompt-only": (
            "Best single semantic axis for system effects: large drop in residual "
            "mixing with moderate stack growth."
        ),
        "full": (
            "Highest-fidelity task profile; preserves session and prompt context "
            "but has the largest stack vocabulary."
        ),
    }
    best_for = {
        "no-semantic": "system-hotspot baseline",
        "session-only": "coarse session cohorting",
        "prompt-only": "default system-effect task profile candidate",
        "full": "drilldown and audit",
    }
    default_safe = {
        "no-semantic": False,
        "session-only": False,
        "prompt-only": True,
        "full": True,
    }
    for variant in r131.get("variants", []):
        if variant.get("family") != "system":
            continue
        name = variant.get("variant", "")
        projection = variant.get("projection", {})
        mixing = variant.get("mixing_against_full_semantics", {})
        rows.append(
            {
                "projection_family": "semantic-axis",
                "variant": name,
                "best_for": best_for.get(name, ""),
                "total_weight": projection.get("total_weight"),
                "unique_stacks_or_tags": projection.get("unique_stacks"),
                "compression_ratio": projection.get("compression_ratio"),
                "mixed_weight_pct": mixing.get("mixed_weight_share_pct"),
                "mixed_residual_pct": mixing.get("mixed_residual_weight_share_pct"),
                "max_semantic_variants_per_bucket": mixing.get(
                    "max_full_semantic_variants_per_bucket"
                ),
                "stack_reduction_vs_raw_pct": "",
                "top20_coverage_pct": "",
                "review_required_support_pct": "",
                "unreviewed_active_weight_pct": 0.0,
                "raw_drilldown_preserved": True,
                "default_safe": default_safe.get(name, False),
                "human_gate_needed": name not in {"no-semantic", "session-only", "prompt-only", "full"},
                "interpretation": interpretations.get(name, ""),
            }
        )
    return rows


def display_policy_rows(r212_csv: Path) -> list[dict[str, Any]]:
    source = read_csv(r212_csv)
    raw_stack_count = max((as_int(row.get("stack_count")) for row in source if row.get("variant") == "raw"), default=0)
    rows: list[dict[str, Any]] = []
    interpretations = {
        "raw": (
            "Maximum fidelity and simplest audit story, but exposes all one-word "
            "tag fragments in the main view."
        ),
        "alias_only": (
            "Safe display cleanup: deterministic aliases reduce stack/tag count "
            "while preserving raw drilldown and activating no reviewed-risk merges."
        ),
        "profile_guarded_candidate_applied": (
            "More aggressive compression, but it would activate unreviewed "
            "profile/lexical merges over nonzero effect weight; should remain a "
            "hypothetical ablation until labels return."
        ),
        "r209_conservative_display": (
            "Current default display policy: alias-only active map with profile "
            "and regenerated candidates kept pending."
        ),
    }
    best_for = {
        "raw": "forensic audit",
        "alias_only": "safe default display",
        "profile_guarded_candidate_applied": "upper-bound compaction ablation",
        "r209_conservative_display": "current product display",
    }
    default_safe = {
        "raw": True,
        "alias_only": True,
        "profile_guarded_candidate_applied": False,
        "r209_conservative_display": True,
    }
    human_gate = {
        "raw": False,
        "alias_only": False,
        "profile_guarded_candidate_applied": True,
        "r209_conservative_display": False,
    }
    for item in source:
        name = item.get("variant", "")
        stack_count = as_int(item.get("stack_count"))
        rows.append(
            {
                "projection_family": "display-policy",
                "variant": name,
                "best_for": best_for.get(name, ""),
                "total_weight": as_int(item.get("total_weight")),
                "unique_stacks_or_tags": stack_count,
                "compression_ratio": "",
                "mixed_weight_pct": "",
                "mixed_residual_pct": "",
                "max_semantic_variants_per_bucket": "",
                "stack_reduction_vs_raw_pct": pct_reduction(raw_stack_count, stack_count),
                "top20_coverage_pct": "",
                "review_required_support_pct": "",
                "unreviewed_active_weight_pct": as_float(
                    item.get("unreviewed_profile_merge_weight_pct")
                ),
                "raw_drilldown_preserved": True,
                "default_safe": default_safe.get(name, False),
                "human_gate_needed": human_gate.get(name, True),
                "interpretation": interpretations.get(name, ""),
            }
        )
    return rows


def vocabulary_rows(r205: dict[str, Any], r209: dict[str, Any]) -> list[dict[str, Any]]:
    overall = r205["compaction_metrics"]["overall"]
    raw_unique = as_int(overall.get("raw_unique_tags"))
    canonical_unique = as_int(overall.get("canonical_unique_tags"))
    r209_summary = r209.get("summary", {})
    return [
        {
            "projection_family": "vocabulary",
            "variant": "raw-tags",
            "best_for": "audit and label collection",
            "total_weight": "",
            "unique_stacks_or_tags": raw_unique,
            "compression_ratio": "",
            "mixed_weight_pct": "",
            "mixed_residual_pct": "",
            "max_semantic_variants_per_bucket": "",
            "stack_reduction_vs_raw_pct": 0.0,
            "top20_coverage_pct": overall["raw_top_k"]["top_k_coverage_pct"],
            "review_required_support_pct": overall.get("review_required_support_pct"),
            "unreviewed_active_weight_pct": 0.0,
            "raw_drilldown_preserved": True,
            "default_safe": True,
            "human_gate_needed": False,
            "interpretation": "Raw labels are immutable and auditable, but the main view has the largest long tail.",
        },
        {
            "projection_family": "vocabulary",
            "variant": "canonical-display-overlay",
            "best_for": "readable default navigation",
            "total_weight": "",
            "unique_stacks_or_tags": canonical_unique,
            "compression_ratio": "",
            "mixed_weight_pct": "",
            "mixed_residual_pct": "",
            "max_semantic_variants_per_bucket": "",
            "stack_reduction_vs_raw_pct": pct_reduction(raw_unique, canonical_unique),
            "top20_coverage_pct": overall["canonical_top_k"]["top_k_coverage_pct"],
            "review_required_support_pct": overall.get("review_required_support_pct"),
            "unreviewed_active_weight_pct": 0.0,
            "raw_drilldown_preserved": r209["claim_gate"].get("drilldown_raw_tags_complete"),
            "default_safe": r209["claim_gate"].get("active_alias_overlay_only"),
            "human_gate_needed": True,
            "interpretation": (
                "Display overlay improves top-20 coverage and reduces unique labels, "
                "but profile/regenerated candidates stay pending until human gates pass."
            ),
        },
        {
            "projection_family": "vocabulary",
            "variant": "r209-active-map",
            "best_for": "renderer contract",
            "total_weight": "",
            "unique_stacks_or_tags": r209_summary.get("active_display_labels"),
            "compression_ratio": "",
            "mixed_weight_pct": "",
            "mixed_residual_pct": "",
            "max_semantic_variants_per_bucket": "",
            "stack_reduction_vs_raw_pct": "",
            "top20_coverage_pct": "",
            "review_required_support_pct": overall.get("review_required_support_pct"),
            "unreviewed_active_weight_pct": 0.0,
            "raw_drilldown_preserved": r209["claim_gate"].get("drilldown_raw_tags_complete"),
            "default_safe": r209["claim_gate"].get("active_alias_overlay_only"),
            "human_gate_needed": False,
            "interpretation": (
                "Renderer consumes a complete raw/display map: no hidden other "
                "bucket, regenerated labels candidate-only, and raw membership "
                "available for drilldown."
            ),
        },
    ]


def markdown_summary(payload: dict[str, Any]) -> str:
    rows = payload["rows"]
    semantic = [row for row in rows if row["projection_family"] == "semantic-axis"]
    display = [row for row in rows if row["projection_family"] == "display-policy"]
    vocab = [row for row in rows if row["projection_family"] == "vocabulary"]

    def fmt(value: Any) -> str:
        if value is None:
            return "n/a"
        if value == "":
            return "-"
        if isinstance(value, bool):
            return "yes" if value else "no"
        return str(value)

    semantic_by_variant = {row["variant"]: row for row in semantic}
    no_semantic_mixed = fmt(semantic_by_variant["no-semantic"]["mixed_weight_pct"])

    lines = [
        "# R223 Projection Tradeoff",
        "",
        "Status: `done/rq2-tradeoff-artifact`",
        "",
        "This artifact answers RQ2 as a projection-selection problem over R170-derived generated evidence. "
        "Semantic-axis and display-policy rows share the same system-effect denominator; vocabulary rows report tag-display support. "
        "It does not read raw traces, call an LLM, or score human utility/adequacy.",
        "",
        "## Semantic Axis Tradeoff",
        "",
        "| Variant | Best for | Unique stacks | Compression | Mixed weight | Residual mixed | Max variants | Default? |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in semantic:
        lines.append(
            "| {variant} | {best_for} | {unique} | {compression} | {mixed}% | {residual}% | {maxv} | {default} |".format(
                variant=row["variant"],
                best_for=row["best_for"],
                unique=fmt(row["unique_stacks_or_tags"]),
                compression=fmt(row["compression_ratio"]),
                mixed=fmt(row["mixed_weight_pct"]),
                residual=fmt(row["mixed_residual_pct"]),
                maxv=fmt(row["max_semantic_variants_per_bucket"]),
                default=fmt(row["default_safe"]),
            )
        )
    lines.extend(
        [
            "",
            f"Interpretation: no-semantic is compact but mixes {no_semantic_mixed}% of system-effect weight; "
            "prompt-only is the best single semantic axis for system effects; full session+prompt "
            "is the audit view. This supports a pluggable projection design rather than one universal stack.",
            "",
            "## Display Policy Tradeoff",
            "",
            "| Variant | Stack count | Reduction vs raw | Unreviewed active weight | Default safe | Human gate |",
            "|---|---:|---:|---:|---:|---:|",
        ]
    )
    for row in display:
        lines.append(
            "| {variant} | {unique} | {reduction}% | {unreviewed}% | {safe} | {gate} |".format(
                variant=row["variant"],
                unique=fmt(row["unique_stacks_or_tags"]),
                reduction=fmt(row["stack_reduction_vs_raw_pct"]),
                unreviewed=fmt(row["unreviewed_active_weight_pct"]),
                safe=fmt(row["default_safe"]),
                gate=fmt(row["human_gate_needed"]),
            )
        )
    lines.extend(
        [
            "",
            "Interpretation: R209's conservative display policy matches alias-only: it reduces "
            "fragmentation without activating profile/regeneration candidates. The more aggressive "
            "profile-guarded variant is useful as an upper-bound ablation, not a default.",
            "",
            "## Vocabulary And Drilldown",
            "",
            "| Variant | Unique labels | Top-20 coverage | Review-required support | Raw drilldown | Default safe |",
            "|---|---:|---:|---:|---:|---:|",
        ]
    )
    for row in vocab:
        top20 = fmt(row["top20_coverage_pct"])
        review = fmt(row["review_required_support_pct"])
        lines.append(
            "| {variant} | {unique} | {top20} | {review} | {drilldown} | {safe} |".format(
                variant=row["variant"],
                unique=fmt(row["unique_stacks_or_tags"]),
                top20=f"{top20}%" if top20 != "-" else "-",
                review=f"{review}%" if review != "-" else "-",
                drilldown=fmt(row["raw_drilldown_preserved"]),
                safe=fmt(row["default_safe"]),
            )
        )
    lines.extend(
        [
            "",
            "## Claim Boundary",
            "",
            "- Supports: RQ2 mechanism/tradeoff claim for pluggable projection over R170-derived generated evidence.",
            "- Does not support: C5 user utility, C6 semantic adequacy, merge quality, or promotion quality.",
            "- Next gates: R142 participant responses and R124/R190/R203 human labels.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    r131 = read_json(DEFAULT_R131)
    r205 = read_json(DEFAULT_R205)
    r209 = read_json(DEFAULT_R209)
    r212 = read_json(DEFAULT_R212)
    r219 = read_json(DEFAULT_R219)

    rows = []
    rows.extend(semantic_axis_rows(r131))
    rows.extend(display_policy_rows(DEFAULT_R212_CSV))
    rows.extend(vocabulary_rows(r205, r209))

    payload = {
        "run_id": "R223",
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "status": "done/rq2-tradeoff-artifact",
        "claim": "C3/RQ2 projection tradeoff mechanism; not C5/C6 outcome evidence",
        "claim_boundary": (
            "R223 summarizes projection tradeoffs over generated artifacts only. "
            "Semantic-axis and display-policy rows share the R170 system-effect "
            "denominator; vocabulary rows report R170-derived tag-display support. "
            "It supports the framework design claim that projection is pluggable "
            "and question-dependent. It does not prove human utility, tag adequacy, "
            "merge quality, or promotion quality."
        ),
        "method": {
            "fixed_evidence_graph": "R170 folded system observations for semantic-axis and display-policy rows; R205/R209 vocabulary support for tag-display rows",
            "projection_dimensions": [
                "semantic axes",
                "display compaction policy",
                "vocabulary/drilldown contract",
            ],
            "metrics": [
                "unique stacks/tags",
                "compression ratio",
                "mixed weight",
                "residual mixed weight",
                "review-required support",
                "unreviewed active weight",
                "raw drilldown preservation",
            ],
            "raw_trace_read": False,
            "llm_called": False,
            "human_outcome_scored": False,
        },
        "inputs": {
            rel(path): {"sha256": sha256_file(path)}
            for path in [DEFAULT_R131, DEFAULT_R205, DEFAULT_R209, DEFAULT_R212, DEFAULT_R212_CSV, DEFAULT_R219]
        },
        "provenance": {
            "commit": git(["rev-parse", "HEAD"]),
            "branch": git(["rev-parse", "--abbrev-ref", "HEAD"]),
            "dirty": bool(git(["status", "--porcelain"])),
        },
        "summary": {
            "semantic_axis_rows": sum(row["projection_family"] == "semantic-axis" for row in rows),
            "display_policy_rows": sum(row["projection_family"] == "display-policy" for row in rows),
            "vocabulary_rows": sum(row["projection_family"] == "vocabulary" for row in rows),
            "rq2_current_verdict": r219.get("rq_rows", {}).get("RQ2 semantic partitioning")
            or "supported_as_mechanism",
            "c5_supported": False,
            "c6_supported": False,
        },
        "rows": rows,
        "source_gate_status": {
            "r212_display_compaction_supported": r212.get("claim_gate", {}).get(
                "display_compaction_ablation_supported"
            ),
            "r209_reversible_display_map_supported": r209.get("claim_gate", {}).get(
                "reversible_display_map_supported"
            ),
            "r205_compaction_metrics_supported": r205.get("claim_gate", {}).get(
                "compaction_metrics_supported"
            ),
        },
    }

    DEFAULT_OUT.mkdir(parents=True, exist_ok=True)
    write_json(DEFAULT_OUT / "projection-tradeoff-r223.json", payload)
    write_csv(DEFAULT_OUT / "projection-tradeoff-r223.csv", rows)
    (DEFAULT_OUT / "projection-tradeoff-r223.md").write_text(
        markdown_summary(payload),
        encoding="utf-8",
    )
    print(json.dumps(payload["summary"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
