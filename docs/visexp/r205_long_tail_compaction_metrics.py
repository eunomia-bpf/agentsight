#!/usr/bin/env python3
"""R205: summarize long-tail semantic compaction metrics.

This script reads generated R189/R196/R201/R202/R203/R190 artifacts only. It
does not read or mutate raw Codex/Claude traces, and it does not update the
canonical tag map. The output is a mechanism/readiness artifact: it quantifies
raw-vs-canonical coverage, long-tail mass, review burden, regeneration status,
and empty human gates without claiming semantic adequacy.
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
DEFAULT_R189_DIR = SCRIPT_DIR / "out" / "tag-consolidation-r189"
DEFAULT_R190_DIR = SCRIPT_DIR / "out" / "tag-consolidation-audit-r190"
DEFAULT_R196_DIR = SCRIPT_DIR / "out" / "long-tail-governance-r196"
DEFAULT_R201_DIR = SCRIPT_DIR / "out" / "long-tail-sensitivity-r201"
DEFAULT_R202_DIR = SCRIPT_DIR / "out" / "long-tail-regeneration-r202"
DEFAULT_R203_DIR = SCRIPT_DIR / "out" / "long-tail-promotion-r203"
DEFAULT_OUT_DIR = SCRIPT_DIR / "out" / "long-tail-compaction-r205"


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


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def as_int(value: Any) -> int:
    if value in (None, ""):
        return 0
    return int(float(value))


def as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"true", "1", "yes", "y"}


def pct(part: int | float, whole: int | float) -> float | None:
    if not whole:
        return None
    return round(100.0 * float(part) / float(whole), 3)


def top_k_coverage(rows: list[dict[str, str]], key: str, top_k: int) -> dict[str, Any]:
    support_by_label: Counter[str] = Counter()
    for row in rows:
        label = str(row.get(key) or "")
        if not label:
            continue
        support_by_label[label] += as_int(row.get("support"))
    total_support = sum(support_by_label.values())
    top = support_by_label.most_common(top_k)
    top_support = sum(count for _, count in top)
    return {
        "key": key,
        "top_k": top_k,
        "unique_labels": len(support_by_label),
        "total_support": total_support,
        "top_k_support": top_support,
        "top_k_coverage_pct": pct(top_support, total_support),
        "top_labels": [{"label": label, "support": count} for label, count in top],
    }


def summarize_actions(rows: list[dict[str, str]]) -> dict[str, Any]:
    counts: Counter[str] = Counter()
    support: Counter[str] = Counter()
    total_support = 0
    for row in rows:
        action = row.get("governance_action", "unknown") or "unknown"
        row_support = as_int(row.get("support"))
        counts[action] += 1
        support[action] += row_support
        total_support += row_support
    return {
        action: {
            "rows": counts[action],
            "support": support[action],
            "support_pct": pct(support[action], total_support),
        }
        for action in sorted(counts)
    }


def dimension_metrics(rows: list[dict[str, str]], top_k: int = 20) -> dict[str, Any]:
    total_support = sum(as_int(row.get("support")) for row in rows)
    raw = top_k_coverage(rows, "raw_tag", top_k)
    canonical = top_k_coverage(rows, "canonical_tag", top_k)
    long_tail_rows = [row for row in rows if as_bool(row.get("is_long_tail"))]
    review_rows = [row for row in rows if as_bool(row.get("requires_review"))]
    generic_rows = [row for row in rows if as_bool(row.get("is_generic_or_noisy"))]
    multimodal_rows = [row for row in rows if as_bool(row.get("is_multimodal"))]
    merged_rows = [row for row in rows if (row.get("raw_tag") or "") != (row.get("canonical_tag") or "")]
    canonical_reduction = raw["unique_labels"] - canonical["unique_labels"]
    return {
        "row_count": len(rows),
        "support_total": total_support,
        "raw_unique_tags": raw["unique_labels"],
        "canonical_unique_tags": canonical["unique_labels"],
        "canonical_unique_reduction": canonical_reduction,
        "canonical_unique_reduction_pct": pct(canonical_reduction, raw["unique_labels"]),
        "current_map_merge_rows": len(merged_rows),
        "current_map_merge_support": sum(as_int(row.get("support")) for row in merged_rows),
        "raw_top_k": raw,
        "canonical_top_k": canonical,
        "top_k_coverage_gain_pct_points": (
            round(canonical["top_k_coverage_pct"] - raw["top_k_coverage_pct"], 3)
            if raw["top_k_coverage_pct"] is not None and canonical["top_k_coverage_pct"] is not None
            else None
        ),
        "long_tail_rows": len(long_tail_rows),
        "long_tail_support": sum(as_int(row.get("support")) for row in long_tail_rows),
        "long_tail_support_pct": pct(
            sum(as_int(row.get("support")) for row in long_tail_rows),
            total_support,
        ),
        "review_required_rows": len(review_rows),
        "review_required_support": sum(as_int(row.get("support")) for row in review_rows),
        "review_required_support_pct": pct(
            sum(as_int(row.get("support")) for row in review_rows),
            total_support,
        ),
        "generic_or_noisy_rows": len(generic_rows),
        "generic_or_noisy_support": sum(as_int(row.get("support")) for row in generic_rows),
        "multimodal_rows": len(multimodal_rows),
        "multimodal_support": sum(as_int(row.get("support")) for row in multimodal_rows),
        "actions": summarize_actions(rows),
    }


def summarize_by_dimension(rows: list[dict[str, str]], top_k: int = 20) -> dict[str, Any]:
    by_dimension: defaultdict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        by_dimension[row.get("dimension", "unknown") or "unknown"].append(row)
    dimensions = {dimension: dimension_metrics(group, top_k) for dimension, group in sorted(by_dimension.items())}
    return {"overall": dimension_metrics(rows, top_k), "dimensions": dimensions}


def summarize_regeneration(rows: list[dict[str, str]]) -> dict[str, Any]:
    attempted = [
        row
        for row in rows
        if row.get("regenerated_tag") or row.get("regeneration_error") or row.get("regenerated_valid")
    ]
    valid = [row for row in attempted if as_bool(row.get("regenerated_valid"))]
    changed = [row for row in valid if row.get("regenerated_tag") != row.get("raw_tag")]
    by_dimension = Counter(row.get("dimension", "unknown") or "unknown" for row in attempted)
    return {
        "attempted_rows": len(attempted),
        "valid_rows": len(valid),
        "invalid_rows": len(attempted) - len(valid),
        "grammar_valid_pct": pct(len(valid), len(attempted)),
        "changed_valid_rows": len(changed),
        "changed_valid_pct": pct(len(changed), len(valid)),
        "unique_regenerated_tags": len({row.get("regenerated_tag", "") for row in valid if row.get("regenerated_tag")}),
        "by_dimension": dict(sorted(by_dimension.items())),
    }


def canonical_map_consistency(
    r189_rows: list[dict[str, str]],
    governance_rows: list[dict[str, str]],
) -> dict[str, Any]:
    r189_by_key: dict[tuple[str, str], dict[str, str]] = {}
    duplicate_keys = 0
    for row in r189_rows:
        key = (row.get("dimension", ""), row.get("raw_tag", ""))
        if key in r189_by_key:
            duplicate_keys += 1
        r189_by_key[key] = row

    missing: list[dict[str, str]] = []
    mismatches: list[dict[str, str]] = []
    auto_total = 0
    auto_from_r189_merge = 0
    auto_bad: list[dict[str, str]] = []
    for row in governance_rows:
        key = (row.get("dimension", ""), row.get("raw_tag", ""))
        source = r189_by_key.get(key)
        if source is None:
            missing.append({"dimension": key[0], "raw_tag": key[1]})
            continue
        if source.get("canonical_tag") != row.get("canonical_tag"):
            mismatches.append(
                {
                    "dimension": key[0],
                    "raw_tag": key[1],
                    "r189_canonical_tag": source.get("canonical_tag", ""),
                    "r196_canonical_tag": row.get("canonical_tag", ""),
                }
            )
        if row.get("governance_action") == "auto_canonicalize_existing":
            auto_total += 1
            if source.get("action") == "merge":
                auto_from_r189_merge += 1
            else:
                auto_bad.append(
                    {
                        "dimension": key[0],
                        "raw_tag": key[1],
                        "r189_action": source.get("action", ""),
                        "r196_governance_action": row.get("governance_action", ""),
                    }
                )

    consistent = (
        duplicate_keys == 0
        and not missing
        and not mismatches
        and auto_from_r189_merge == auto_total
        and len(r189_rows) == len(governance_rows)
    )
    return {
        "r189_rows": len(r189_rows),
        "r196_rows": len(governance_rows),
        "r189_duplicate_keys": duplicate_keys,
        "r196_rows_missing_from_r189": len(missing),
        "canonical_mismatch_rows": len(mismatches),
        "auto_canonicalize_existing_rows": auto_total,
        "auto_canonicalize_existing_from_r189_merge_rows": auto_from_r189_merge,
        "auto_canonicalize_existing_bad_rows": len(auto_bad),
        "consistent": consistent,
        "sample_missing": missing[:5],
        "sample_canonical_mismatches": mismatches[:5],
        "sample_auto_canonicalize_bad_rows": auto_bad[:5],
    }


def summary_rows(metrics: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for dimension, data in {"overall": metrics["overall"], **metrics["dimensions"]}.items():
        rows.append(
            {
                "dimension": dimension,
                "row_count": data["row_count"],
                "support_total": data["support_total"],
                "raw_unique_tags": data["raw_unique_tags"],
                "canonical_unique_tags": data["canonical_unique_tags"],
                "canonical_unique_reduction": data["canonical_unique_reduction"],
                "canonical_unique_reduction_pct": data["canonical_unique_reduction_pct"],
                "raw_top20_coverage_pct": data["raw_top_k"]["top_k_coverage_pct"],
                "canonical_top20_coverage_pct": data["canonical_top_k"]["top_k_coverage_pct"],
                "top20_coverage_gain_pct_points": data["top_k_coverage_gain_pct_points"],
                "long_tail_rows": data["long_tail_rows"],
                "long_tail_support_pct": data["long_tail_support_pct"],
                "review_required_rows": data["review_required_rows"],
                "review_required_support_pct": data["review_required_support_pct"],
            }
        )
    return rows


def md_value(value: Any) -> str:
    return "n/a" if value is None else str(value)


def write_markdown(path: Path, payload: dict[str, Any]) -> None:
    overall = payload["compaction_metrics"]["overall"]
    consistency = payload["input_consistency"]["r189_r196_canonical_overlay"]
    regeneration = payload["regeneration"]
    promotion = payload["promotion"]
    r190 = payload["merge_quality"]
    sensitivity = payload["sensitivity"]
    lines = [
        "# R205 Long-Tail Compaction Metrics",
        "",
        f"Status: `{payload['status']}`",
        "",
        "## Scope",
        "",
        "- Reads generated R189/R190/R196/R201/R202/R203 artifacts only.",
        "- Does not read or mutate raw Codex/Claude traces.",
        "- Does not update the canonical tag map.",
        "- Quantifies display compaction mechanics, not semantic adequacy or developer utility.",
        "",
        "## Input Consistency",
        "",
        "| check | value |",
        "|---|---:|",
        f"| R189 rows | {consistency['r189_rows']} |",
        f"| R196 rows | {consistency['r196_rows']} |",
        f"| R189 duplicate keys | {consistency['r189_duplicate_keys']} |",
        f"| R196 rows missing from R189 | {consistency['r196_rows_missing_from_r189']} |",
        f"| canonical mismatch rows | {consistency['canonical_mismatch_rows']} |",
        f"| auto-canonicalize rows | {consistency['auto_canonicalize_existing_rows']} |",
        f"| auto-canonicalize rows from R189 merge | {consistency['auto_canonicalize_existing_from_r189_merge_rows']} |",
        f"| consistency passed | {consistency['consistent']} |",
        "",
        "## Overall Compaction",
        "",
        "| metric | value |",
        "|---|---:|",
        f"| raw unique tags | {overall['raw_unique_tags']} |",
        f"| canonical unique tags | {overall['canonical_unique_tags']} |",
        f"| canonical unique reduction | {overall['canonical_unique_reduction']} |",
        f"| canonical unique reduction pct | {md_value(overall['canonical_unique_reduction_pct'])} |",
        f"| raw top-20 support coverage pct | {md_value(overall['raw_top_k']['top_k_coverage_pct'])} |",
        f"| canonical top-20 support coverage pct | {md_value(overall['canonical_top_k']['top_k_coverage_pct'])} |",
        f"| top-20 coverage gain pct points | {md_value(overall['top_k_coverage_gain_pct_points'])} |",
        f"| long-tail support pct | {md_value(overall['long_tail_support_pct'])} |",
        f"| review-required support pct | {md_value(overall['review_required_support_pct'])} |",
        "",
        "## Per-Dimension Metrics",
        "",
        "| dimension | raw tags | canonical tags | top-20 raw pct | top-20 canonical pct | review support pct |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for dimension, data in payload["compaction_metrics"]["dimensions"].items():
        lines.append(
            "| "
            + " | ".join(
                [
                    dimension,
                    str(data["raw_unique_tags"]),
                    str(data["canonical_unique_tags"]),
                    md_value(data["raw_top_k"]["top_k_coverage_pct"]),
                    md_value(data["canonical_top_k"]["top_k_coverage_pct"]),
                    md_value(data["review_required_support_pct"]),
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Regeneration And Review Gates",
            "",
            f"- R202 attempted rows: `{regeneration['attempted_rows']}`.",
            f"- Grammar-valid regenerated candidates: `{regeneration['valid_rows']}` / `{regeneration['attempted_rows']}`.",
            f"- Changed valid candidates: `{regeneration['changed_valid_rows']}`.",
            f"- R203 promotion packet rows: `{promotion['packet_row_count']}`.",
            f"- R203 final promotion labels: `{promotion['final_label_count']}`.",
            f"- R203 paired label coverage pct: `{md_value(promotion['paired_label_coverage_pct'])}`.",
            f"- R190 overmerge rate pct: `{md_value(r190['overmerge_rate_pct'])}`.",
            f"- R190 undermerge rate pct: `{md_value(r190['undermerge_rate_pct'])}`.",
            f"- R201 baseline review-required support pct: `{md_value(sensitivity['baseline_review_required_support_pct'])}`.",
            f"- R201 minimum head stability pct: `{md_value(sensitivity['min_head_stability_pct'])}`.",
            "",
            "## Claim Boundary",
            "",
            "R205 supports only the existence of a measurable semantic compaction "
            "mechanism over existing artifacts. It does not prove that canonical "
            "tags are semantically correct, that regenerated tags should be promoted, "
            "or that developers answer forensic questions faster or more accurately. "
            "Those claims still require the existing R124/R190/R203 human-label gates "
            "and the R142/R151 developer-task gates.",
            "",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def build_payload(args: argparse.Namespace) -> dict[str, Any]:
    r189_map = args.r189_dir / "canonical-tag-map-r189.csv"
    r190_score = args.r190_dir / "merge-risk-audit-results-r190.json"
    r196_csv = args.r196_dir / "long-tail-governance-r196.csv"
    r196_json = args.r196_dir / "long-tail-governance-r196.json"
    r201_json = args.r201_dir / "long-tail-sensitivity-r201.json"
    r202_attempts = args.r202_dir / "long-tail-regeneration-attempts-r202.csv"
    r202_json = args.r202_dir / "long-tail-regeneration-r202.json"
    r203_json = args.r203_dir / "long-tail-promotion-r203.json"
    r203_packet = args.r203_dir / "long-tail-promotion-packet-r203.csv"

    paths = [r189_map, r190_score, r196_csv, r196_json, r201_json, r202_attempts, r202_json, r203_json, r203_packet]
    missing = [rel(path) for path in paths if not path.exists()]
    if missing:
        raise FileNotFoundError(f"missing required R205 input artifacts: {missing}")

    r189_rows = read_csv(r189_map)
    governance_rows = read_csv(r196_csv)
    r190_payload = read_json(r190_score)
    r196_payload = read_json(r196_json)
    r201_payload = read_json(r201_json)
    r202_payload = read_json(r202_json)
    r203_payload = read_json(r203_json)
    r202_rows = read_csv(r202_attempts)
    r203_rows = read_csv(r203_packet)

    metrics = summarize_by_dimension(governance_rows, args.top_k)
    input_consistency = canonical_map_consistency(r189_rows, governance_rows)
    regeneration = summarize_regeneration(r202_rows)
    r190_summary = r190_payload.get("summary", {})
    r190_gate = r190_payload.get("claim_gate", {})
    r203_summary = r203_payload.get("summary", {})
    r203_gate = r203_payload.get("claim_gate", {})
    sensitivity_baseline = r201_payload.get("baseline", {})
    sensitivity_extremes = r201_payload.get("extremes", {})
    min_head_stability = sensitivity_extremes.get("min_head_stability_pct", {}).get("baseline_head_stability_pct")

    claim_gate = {
        "compaction_metrics_supported": True,
        "canonical_overlay_only": True,
        "raw_tags_preserved": True,
        "canonical_map_updated": bool(r203_gate.get("canonical_map_updated", False)),
        "canonicalization_quality_supported": bool(r190_gate.get("canonicalization_quality_supported", False)),
        "long_tail_promotion_review_supported": bool(
            r203_gate.get("long_tail_promotion_review_supported", False)
        ),
        "semantic_adequacy_supported": False,
        "developer_utility_supported": False,
        "community_adoption_supported": False,
        "requires_r124_labels_for_adequacy": True,
        "requires_r190_labels_for_merge_quality": True,
        "requires_r203_labels_for_promotion_quality": True,
    }

    status = "compaction_metrics_ready_no_quality_claims"
    if claim_gate["canonicalization_quality_supported"] or claim_gate["long_tail_promotion_review_supported"]:
        status = "compaction_metrics_with_human_review_signals"

    return {
        "run_id": "R205",
        "schema_version": 1,
        "generated_at": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),
        "status": status,
        "claim": "C3; C6 protocol/gate only",
        "claim_boundary": (
            "R205 measures semantic compaction coverage and review burden over existing generated artifacts. "
            "It does not update raw tags, mutate the canonical map, or support tag adequacy, merge quality, "
            "developer utility, or community adoption without the existing human gates."
        ),
        "input": {
            "r189_map": rel(r189_map),
            "r189_map_sha256": sha256_file(r189_map),
            "r190_score": rel(r190_score),
            "r190_score_sha256": sha256_file(r190_score),
            "r196_csv": rel(r196_csv),
            "r196_csv_sha256": sha256_file(r196_csv),
            "r196_json": rel(r196_json),
            "r196_json_sha256": sha256_file(r196_json),
            "r201_json": rel(r201_json),
            "r201_json_sha256": sha256_file(r201_json),
            "r202_json": rel(r202_json),
            "r202_json_sha256": sha256_file(r202_json),
            "r202_attempts": rel(r202_attempts),
            "r202_attempts_sha256": sha256_file(r202_attempts),
            "r203_json": rel(r203_json),
            "r203_json_sha256": sha256_file(r203_json),
            "r203_packet": rel(r203_packet),
            "r203_packet_sha256": sha256_file(r203_packet),
        },
        "method": {
            "top_k": args.top_k,
            "raw_trace_policy": "read generated public-oriented or local-audit summary artifacts only; do not mutate raw traces",
            "canonical_map_policy": "metrics only; no map update",
            "promotion_policy": "R203 review labels are required before any regenerated candidate can be promoted",
        },
        "input_consistency": {
            "r189_r196_canonical_overlay": input_consistency,
        },
        "compaction_metrics": metrics,
        "regeneration": regeneration,
        "promotion": {
            "packet_row_count": int(r203_summary.get("packet_row_count", len(r203_rows))),
            "grammar_valid_rows": int(r203_summary.get("grammar_valid_rows", 0)),
            "changed_from_raw_rows": int(r203_summary.get("changed_from_raw_rows", 0)),
            "final_label_count": int(r203_summary.get("final_label_count", 0)),
            "paired_label_coverage_pct": r203_summary.get("paired_label_coverage_pct"),
            "promotion_acceptance_pct": r203_summary.get("promotion_acceptance_pct"),
            "long_tail_promotion_review_supported": bool(
                r203_gate.get("long_tail_promotion_review_supported", False)
            ),
            "canonical_map_updated": bool(r203_gate.get("canonical_map_updated", False)),
        },
        "merge_quality": {
            "packet_row_count": int(r190_summary.get("packet_row_count", 0)),
            "final_label_count": int(r190_summary.get("final_label_count", 0)),
            "paired_label_coverage_pct": r190_summary.get("paired_label_coverage_pct"),
            "overmerge_rate_pct": r190_summary.get("overmerge_rate_pct"),
            "undermerge_rate_pct": r190_summary.get("undermerge_rate_pct"),
            "canonicalization_quality_supported": bool(
                r190_gate.get("canonicalization_quality_supported", False)
            ),
        },
        "sensitivity": {
            "baseline_review_required_support_pct": sensitivity_baseline.get("review_required_support_pct"),
            "baseline_long_tail_support_pct": sensitivity_baseline.get("long_tail_support_pct"),
            "max_review_support_pct": sensitivity_extremes.get("max_review_support_pct", {}).get(
                "review_required_support_pct"
            ),
            "min_head_stability_pct": min_head_stability,
            "variant_count": r201_payload.get("method", {}).get("variant_count"),
        },
        "source_gate_status": {
            "r196_status": r196_payload.get("summary", {}).get("status"),
            "r202_status": r202_payload.get("status"),
            "r203_status": r203_payload.get("status"),
            "r190_status": r190_payload.get("status"),
        },
        "claim_gate": claim_gate,
        "provenance": {
            "repo_commit": git(["rev-parse", "HEAD"]),
            "repo_dirty": bool(git(["status", "--short"])),
            "script_sha256": sha256_file(Path(__file__)),
        },
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--r189-dir", type=Path, default=DEFAULT_R189_DIR)
    parser.add_argument("--r190-dir", type=Path, default=DEFAULT_R190_DIR)
    parser.add_argument("--r196-dir", type=Path, default=DEFAULT_R196_DIR)
    parser.add_argument("--r201-dir", type=Path, default=DEFAULT_R201_DIR)
    parser.add_argument("--r202-dir", type=Path, default=DEFAULT_R202_DIR)
    parser.add_argument("--r203-dir", type=Path, default=DEFAULT_R203_DIR)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--top-k", type=int, default=20)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    payload = build_payload(args)
    out_dir = args.out_dir
    summary_json = out_dir / "long-tail-compaction-r205.json"
    summary_md = out_dir / "long-tail-compaction-r205.md"
    dimensions_csv = out_dir / "long-tail-compaction-dimensions-r205.csv"
    payload["outputs"] = {
        "summary_json": rel(summary_json),
        "summary_md": rel(summary_md),
        "dimensions_csv": rel(dimensions_csv),
    }
    write_json(summary_json, payload)
    write_markdown(summary_md, payload)
    write_csv(
        dimensions_csv,
        summary_rows(payload["compaction_metrics"]),
        [
            "dimension",
            "row_count",
            "support_total",
            "raw_unique_tags",
            "canonical_unique_tags",
            "canonical_unique_reduction",
            "canonical_unique_reduction_pct",
            "raw_top20_coverage_pct",
            "canonical_top20_coverage_pct",
            "top20_coverage_gain_pct_points",
            "long_tail_rows",
            "long_tail_support_pct",
            "review_required_rows",
            "review_required_support_pct",
        ],
    )
    print(json.dumps({"status": payload["status"], "summary_json": rel(summary_json)}, sort_keys=True))


if __name__ == "__main__":
    main()
