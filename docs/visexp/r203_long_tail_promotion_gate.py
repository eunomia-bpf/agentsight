#!/usr/bin/env python3
"""R203: human-gated promotion protocol for regenerated long-tail tags.

This script consumes the public-oriented R202 attempts CSV only. It creates a
promotion review packet, blank reviewer sheets, an adjudication template, and an
empty-evidence gate. It never updates the canonical tag map; accepted promotion
labels are future inputs to a separate, reviewable display-map update.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import json
import subprocess
from collections import Counter
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[1]
DEFAULT_R202_DIR = SCRIPT_DIR / "out" / "long-tail-regeneration-r202"
DEFAULT_OUT_DIR = SCRIPT_DIR / "out" / "long-tail-promotion-r203"
DEFAULT_ATTEMPTS = DEFAULT_R202_DIR / "long-tail-regeneration-attempts-r202.csv"

PROMOTION_LABELS = ("promote", "keep_raw", "reject", "split", "unclear")
LABEL_ALIASES = {
    "promote": "promote",
    "accept": "promote",
    "accepted": "promote",
    "use_candidate": "promote",
    "candidate": "promote",
    "keep_raw": "keep_raw",
    "keep": "keep_raw",
    "raw": "keep_raw",
    "same": "keep_raw",
    "reject": "reject",
    "bad": "reject",
    "worse": "reject",
    "misleading": "reject",
    "split": "split",
    "split_needed": "split",
    "contextual_split": "split",
    "unclear": "unclear",
    "unsure": "unclear",
    "unknown": "unclear",
}

PACKET_FIELDS = [
    "promotion_id",
    "dimension",
    "raw_tag",
    "canonical_tag",
    "governance_action",
    "governance_reasons",
    "support",
    "top_processes",
    "top_effects",
    "top_context_tags",
    "regeneration_context_hash",
    "regenerated_tag",
    "grammar_valid",
    "changed_from_raw",
    "proposed_action",
    "promotion_label",
    "promotion_notes",
]
IMMUTABLE_FIELDS = tuple(field for field in PACKET_FIELDS if field not in {"promotion_label", "promotion_notes"})
ADJUDICATION_FIELDS = [
    "promotion_id",
    "dimension",
    "raw_tag",
    "regenerated_tag",
    "proposed_action",
    "labeler_1",
    "labeler_2",
    "adjudicated_label",
    "notes",
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


def sha256_file(path: Path | None) -> str | None:
    if not path or not path.exists():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_csv(path: Path) -> tuple[list[dict[str, str]], list[str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        return list(reader), list(reader.fieldnames or [])


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n", extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def normalize_label(value: str | None) -> str:
    raw = (value or "").strip().lower()
    if not raw:
        return ""
    canonicalized = raw.replace("-", "_").replace("/", "_").replace(" ", "_")
    label = LABEL_ALIASES.get(raw) or LABEL_ALIASES.get(canonicalized)
    if not label:
        raise AssertionError(
            f"unknown R203 promotion label {value!r}; expected promote, keep_raw, reject, split, or unclear"
        )
    return label


def pct(part: int | float, whole: int | float) -> float | None:
    if not whole:
        return None
    return round(100.0 * part / whole, 3)


def cohen_kappa(pairs: list[tuple[str, str]]) -> float | None:
    if not pairs:
        return None
    total = len(pairs)
    observed = sum(1 for left, right in pairs if left == right) / total
    left_counts = Counter(left for left, _ in pairs)
    right_counts = Counter(right for _, right in pairs)
    expected = sum((left_counts[label] / total) * (right_counts[label] / total) for label in PROMOTION_LABELS)
    if expected >= 1.0:
        return 1.0 if observed >= 1.0 else 0.0
    return round((observed - expected) / (1.0 - expected), 3)


def proposed_action(row: dict[str, str]) -> str:
    valid = row.get("regenerated_valid") == "True"
    if not valid:
        return "reject_invalid"
    if row.get("governance_action") == "contextual_split_candidate":
        return "review_split_candidate"
    if row.get("regenerated_tag") == row.get("raw_tag"):
        return "review_keep_raw"
    return "review_promote_candidate"


def packet_rows_from_attempts(rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    packet: list[dict[str, Any]] = []
    for index, source in enumerate(rows, start=1):
        valid = source.get("regenerated_valid") == "True"
        changed = valid and source.get("regenerated_tag", "") != source.get("raw_tag", "")
        packet.append(
            {
                "promotion_id": f"r203-{index:04d}",
                "dimension": source.get("dimension", ""),
                "raw_tag": source.get("raw_tag", ""),
                "canonical_tag": source.get("canonical_tag", ""),
                "governance_action": source.get("governance_action", ""),
                "governance_reasons": source.get("governance_reasons", ""),
                "support": source.get("support", ""),
                "top_processes": source.get("top_processes", ""),
                "top_effects": source.get("top_effects", ""),
                "top_context_tags": source.get("top_context_tags", ""),
                "regeneration_context_hash": source.get("regeneration_context_hash", ""),
                "regenerated_tag": source.get("regenerated_tag", ""),
                "grammar_valid": str(valid),
                "changed_from_raw": str(changed),
                "proposed_action": proposed_action(source),
                "promotion_label": "",
                "promotion_notes": "",
            }
        )
    return packet


def packet_index(rows: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    return {row["promotion_id"]: row for row in rows}


def validate_packet(rows: list[dict[str, str]], fields: list[str]) -> None:
    missing = sorted(set(PACKET_FIELDS) - set(fields))
    if missing:
        raise AssertionError(f"R203 promotion packet is missing fields: {missing}")
    seen: set[str] = set()
    for row in rows:
        promotion_id = row.get("promotion_id", "")
        if not promotion_id:
            raise AssertionError("R203 promotion packet contains a blank promotion_id")
        if promotion_id in seen:
            raise AssertionError(f"duplicate promotion_id {promotion_id}")
        seen.add(promotion_id)
        normalize_label(row.get("promotion_label"))


def validate_against_packet(packet_rows: list[dict[str, str]], rows: list[dict[str, str]], path: Path) -> None:
    by_id = packet_index(packet_rows)
    if len(rows) != len(packet_rows):
        raise AssertionError(f"{path} row count does not match the R203 packet")
    seen: set[str] = set()
    for row in rows:
        promotion_id = row.get("promotion_id", "")
        source = by_id.get(promotion_id)
        if not source:
            raise AssertionError(f"{path} references unknown promotion_id {promotion_id!r}")
        if promotion_id in seen:
            raise AssertionError(f"{path} contains duplicate promotion_id {promotion_id}")
        seen.add(promotion_id)
        for field in IMMUTABLE_FIELDS:
            if row.get(field) != source.get(field):
                raise AssertionError(f"{path} changes {field} for {promotion_id}")


def read_labeler_sheet(path: Path, packet_rows: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    rows, fields = read_csv(path)
    required = set(IMMUTABLE_FIELDS) | {"promotion_label", "promotion_notes"}
    missing = sorted(required - set(fields))
    if missing:
        raise AssertionError(f"{path} is missing required R203 label fields: {missing}")
    validate_against_packet(packet_rows, rows, path)
    return {
        row["promotion_id"]: {
            "label": normalize_label(row.get("promotion_label")),
            "notes": row.get("promotion_notes", ""),
        }
        for row in rows
    }


def read_adjudication(path: Path | None, packet_rows: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    if not path or not path.exists():
        return {}
    rows, fields = read_csv(path)
    required = {"promotion_id", "adjudicated_label", "notes"}
    missing = sorted(required - set(fields))
    if missing:
        raise AssertionError(f"{path} is missing required adjudication fields: {missing}")
    by_id = packet_index(packet_rows)
    out: dict[str, dict[str, str]] = {}
    for row in rows:
        promotion_id = row.get("promotion_id", "")
        if promotion_id not in by_id:
            raise AssertionError(f"{path} references unknown promotion_id {promotion_id!r}")
        label = normalize_label(row.get("adjudicated_label"))
        if label:
            out[promotion_id] = {"label": label, "notes": row.get("notes", "")}
    return out


def final_label_for(row: dict[str, str]) -> tuple[str, str, str]:
    labeler_1 = normalize_label(row.get("labeler_1"))
    labeler_2 = normalize_label(row.get("labeler_2"))
    adjudicated = normalize_label(row.get("adjudicated_label"))
    if adjudicated:
        return adjudicated, "adjudicated", "final"
    if labeler_1 and labeler_2 and labeler_1 == labeler_2:
        return labeler_1, "consensus", "final"
    if labeler_1 and labeler_2:
        return "", "disagreement_unadjudicated", "needs_adjudication"
    if labeler_1 or labeler_2:
        return labeler_1 or labeler_2, "single_label", "weak_final"
    return "", "empty", "unlabeled"


def join_rows(
    packet_rows: list[dict[str, str]],
    labeler_1: dict[str, dict[str, str]],
    labeler_2: dict[str, dict[str, str]],
    adjudications: dict[str, dict[str, str]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    joined: list[dict[str, Any]] = []
    disagreements: list[dict[str, Any]] = []
    for source in packet_rows:
        promotion_id = source["promotion_id"]
        left = labeler_1.get(promotion_id, {"label": "", "notes": ""})
        right = labeler_2.get(promotion_id, {"label": "", "notes": ""})
        adjudication = adjudications.get(promotion_id, {"label": "", "notes": ""})
        row = {
            **source,
            "labeler_1": left.get("label", ""),
            "labeler_2": right.get("label", ""),
            "adjudicated_label": adjudication.get("label", ""),
            "labeler_1_notes": left.get("notes", ""),
            "labeler_2_notes": right.get("notes", ""),
            "adjudication_notes": adjudication.get("notes", ""),
        }
        final_label, final_source, label_state = final_label_for(row)
        row.update({"final_label": final_label, "final_source": final_source, "label_state": label_state})
        if row["labeler_1"] and row["labeler_2"] and row["labeler_1"] != row["labeler_2"]:
            disagreements.append(
                {
                    "promotion_id": promotion_id,
                    "dimension": source.get("dimension", ""),
                    "raw_tag": source.get("raw_tag", ""),
                    "regenerated_tag": source.get("regenerated_tag", ""),
                    "proposed_action": source.get("proposed_action", ""),
                    "labeler_1": row["labeler_1"],
                    "labeler_2": row["labeler_2"],
                    "adjudicated_label": row["adjudicated_label"],
                    "notes": row["adjudication_notes"],
                }
            )
        joined.append(row)
    return joined, disagreements


def score_rows(rows: list[dict[str, str]]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    scored: list[dict[str, Any]] = []
    label_counts: Counter[str] = Counter()
    state_counts: Counter[str] = Counter()
    source_counts: Counter[str] = Counter()
    proposed_counts: Counter[str] = Counter()
    pair_labels: list[tuple[str, str]] = []

    for source in rows:
        row = dict(source)
        labeler_1 = normalize_label(row.get("labeler_1"))
        labeler_2 = normalize_label(row.get("labeler_2"))
        adjudicated = normalize_label(row.get("adjudicated_label"))
        row.update({"labeler_1": labeler_1, "labeler_2": labeler_2, "adjudicated_label": adjudicated})
        final_label, final_source, label_state = final_label_for(row)
        row.update({"final_label": final_label, "final_source": final_source, "label_state": label_state})
        proposed_counts[row.get("proposed_action", "")] += 1
        state_counts[label_state] += 1
        source_counts[final_source] += 1
        if labeler_1 and labeler_2:
            pair_labels.append((labeler_1, labeler_2))
        if final_label:
            label_counts[final_label] += 1
        scored.append(row)

    final_count = sum(label_counts.values())
    both_labeler_count = len(pair_labels)
    agreement_count = sum(1 for left, right in pair_labels if left == right)
    strong_final_count = source_counts.get("consensus", 0) + source_counts.get("adjudicated", 0)
    promote_count = label_counts.get("promote", 0)
    return scored, {
        "packet_row_count": len(rows),
        "grammar_valid_rows": sum(1 for row in rows if row.get("grammar_valid") == "True"),
        "changed_from_raw_rows": sum(1 for row in rows if row.get("changed_from_raw") == "True"),
        "final_label_count": final_count,
        "strong_final_label_count": strong_final_count,
        "unlabeled_count": state_counts.get("unlabeled", 0),
        "single_label_count": state_counts.get("weak_final", 0),
        "unadjudicated_disagreement_count": state_counts.get("needs_adjudication", 0),
        "both_labeler_count": both_labeler_count,
        "paired_label_coverage_pct": pct(both_labeler_count, len(rows)),
        "inter_labeler_agreement_pct": pct(agreement_count, both_labeler_count),
        "cohen_kappa": cohen_kappa(pair_labels),
        "final_source_counts": dict(source_counts),
        "label_state_counts": dict(state_counts),
        "final_label_counts": {label: label_counts.get(label, 0) for label in PROMOTION_LABELS},
        "proposed_action_counts": dict(sorted(proposed_counts.items())),
        "unclear_share_pct": pct(label_counts.get("unclear", 0), final_count),
        "promotion_acceptance_pct": pct(promote_count, final_count),
        "non_promoted_final_rows": final_count - promote_count,
    }


def claim_gate(summary: dict[str, Any]) -> dict[str, Any]:
    packet_count = int(summary["packet_row_count"])
    final_count = int(summary["final_label_count"])
    strong_final_count = int(summary["strong_final_label_count"])
    paired_count = int(summary["both_labeler_count"])
    kappa = summary["cohen_kappa"]
    unclear = summary["unclear_share_pct"]
    complete = packet_count > 0 and final_count == packet_count
    strong_complete = packet_count > 0 and strong_final_count == packet_count
    paired_complete = packet_count > 0 and paired_count == packet_count
    agreement_ok = kappa is not None and kappa >= 0.6
    unclear_ok = unclear is not None and unclear <= 10.0
    decision_ready = bool(complete and strong_complete and paired_complete and agreement_ok and unclear_ok)
    return {
        "long_tail_promotion_review_supported": decision_ready,
        "promotion_decisions_ready": decision_ready,
        "canonical_map_updated": False,
        "canonical_map_update_allowed_by_this_script": False,
        "semantic_adequacy_supported": False,
        "canonicalization_quality_supported": False,
        "developer_utility_supported": False,
        "community_adoption_supported": False,
        "requires_real_human_labels": final_count == 0,
        "complete_final_labels": complete,
        "complete_strong_final_labels": strong_complete,
        "complete_paired_labels": paired_complete,
        "agreement_ok": agreement_ok,
        "unclear_ok": unclear_ok,
        "success_criteria": {
            "final_labels": "all promotion rows",
            "strong_final_labels": "all rows must be consensus or adjudicated, not single-label",
            "paired_labels": "all rows must have labeler_1 and labeler_2 before adjudication",
            "cohen_kappa": ">=0.6",
            "unclear_share_pct": "<=10",
            "canonical_map_update": "not performed by R203; a later reviewed display-map diff is required",
        },
    }


def result_status(summary: dict[str, Any]) -> str:
    if summary["final_label_count"] == 0 and summary["both_labeler_count"] == 0:
        return "human_labels_empty"
    if summary["unadjudicated_disagreement_count"] > 0:
        return "needs_adjudication"
    if (
        summary["final_label_count"] < summary["packet_row_count"]
        or summary["single_label_count"] > 0
        or summary["both_labeler_count"] < summary["packet_row_count"]
    ):
        return "human_labels_partial"
    return "human_labels_scored"


def write_markdown(path: Path, result: dict[str, Any]) -> None:
    summary = result["summary"]
    gate = result["claim_gate"]
    lines = [
        "# R203 Long-Tail Promotion Gate",
        "",
        "R203 turns R202 regenerated long-tail tags into a human-review protocol. Blank labels are missing evidence.",
        "",
        "## Summary",
        "",
        f"- Status: `{result['status']}`.",
        f"- Promotion rows: {summary['packet_row_count']}.",
        f"- Grammar-valid regenerated candidates: {summary['grammar_valid_rows']}.",
        f"- Changed-from-raw candidates: {summary['changed_from_raw_rows']}.",
        f"- Final labels: {summary['final_label_count']}.",
        f"- Paired label coverage: {summary['paired_label_coverage_pct'] if summary['paired_label_coverage_pct'] is not None else 'n/a'}%.",
        f"- Cohen's kappa: {summary['cohen_kappa'] if summary['cohen_kappa'] is not None else 'n/a'}.",
        "",
        "## Claim Boundary",
        "",
        f"- Promotion review supported: `{gate['long_tail_promotion_review_supported']}`.",
        f"- Canonical map updated: `{gate['canonical_map_updated']}`.",
        "- R203 does not support C5 user utility, C6 tag adequacy, canonicalization quality, or community adoption.",
        "- Accepted labels would still require a separate reviewed display-map diff before any canonical map update.",
        "",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def run(args: argparse.Namespace) -> dict[str, Any]:
    attempt_rows, _ = read_csv(args.r202_attempts)
    packet_rows = packet_rows_from_attempts(attempt_rows)
    write_csv(args.packet, packet_rows, PACKET_FIELDS)
    write_csv(args.labeler_1_template, packet_rows, PACKET_FIELDS)
    write_csv(args.labeler_2_template, packet_rows, PACKET_FIELDS)
    packet_rows_read, packet_fields = read_csv(args.packet)
    validate_packet(packet_rows_read, packet_fields)

    labeler_paths_present = bool(args.labeler_1 or args.labeler_2)
    if bool(args.labeler_1) != bool(args.labeler_2):
        raise AssertionError("provide both --labeler-1 and --labeler-2, or neither")

    if labeler_paths_present:
        labeler_1 = read_labeler_sheet(args.labeler_1, packet_rows_read)
        labeler_2 = read_labeler_sheet(args.labeler_2, packet_rows_read)
        adjudications = read_adjudication(args.adjudication, packet_rows_read)
        joined_rows, disagreement_rows = join_rows(packet_rows_read, labeler_1, labeler_2, adjudications)
        joined_fields = [
            *PACKET_FIELDS,
            "labeler_1",
            "labeler_2",
            "adjudicated_label",
            "labeler_1_notes",
            "labeler_2_notes",
            "adjudication_notes",
            "final_label",
            "final_source",
            "label_state",
        ]
        write_csv(args.joined_labels, joined_rows, joined_fields)
        score_input = joined_rows
    else:
        joined_rows = []
        disagreement_rows = []
        score_input = [
            {**row, "labeler_1": "", "labeler_2": "", "adjudicated_label": ""}
            for row in packet_rows_read
        ]

    write_csv(args.adjudication_template, disagreement_rows, ADJUDICATION_FIELDS)
    scored_rows, summary = score_rows(score_input)
    gate = claim_gate(summary)
    status = result_status(summary)
    result = {
        "schema_version": 1,
        "run_id": "R203",
        "claim": "C3; C6 protocol/gate only",
        "status": status,
        "generated_at": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),
        "source": {
            "r202_attempts": rel(args.r202_attempts),
            "r202_attempts_sha256": sha256_file(args.r202_attempts),
            "reads_raw_traces": False,
            "raw_trace_policy": "consume public-oriented R202 attempts CSV only",
        },
        "outputs": {
            "packet": rel(args.packet),
            "labeler_1_template": rel(args.labeler_1_template),
            "labeler_2_template": rel(args.labeler_2_template),
            "adjudication_template": rel(args.adjudication_template),
            "joined_labels": rel(args.joined_labels) if labeler_paths_present else None,
            "scored_csv": rel(args.out_csv),
            "summary_md": rel(args.out_md),
            "summary_json": rel(args.out_json),
        },
        "labeler_sheets": [
            {"path": rel(path), "sha256": sha256_file(path)}
            for path in (args.labeler_1, args.labeler_2)
            if path
        ],
        "rubric": {
            "promote": "regenerated tag is better than the raw tag for display aggregation",
            "keep_raw": "raw tag should remain the display label",
            "reject": "regenerated tag is misleading or worse",
            "split": "row needs contextual split instead of a single replacement label",
            "unclear": "profile context is insufficient for confident promotion",
        },
        "summary": summary,
        "claim_gate": gate,
        "claim_boundary": (
            "R203 is a promotion protocol for R202 candidates. It never mutates raw traces or "
            "the canonical map, and empty/default labels cannot support tag adequacy, merge "
            "quality, developer utility, or community adoption."
        ),
        "provenance": {
            "repo_commit": git(["rev-parse", "HEAD"]),
            "repo_dirty": bool(git(["status", "--short"])),
            "script_sha256": sha256_file(Path(__file__).resolve()),
        },
    }
    write_csv(
        args.out_csv,
        scored_rows,
        [*PACKET_FIELDS, "labeler_1", "labeler_2", "adjudicated_label", "final_label", "final_source", "label_state"],
    )
    args.out_json.parent.mkdir(parents=True, exist_ok=True)
    args.out_json.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_markdown(args.out_md, result)
    print(
        json.dumps(
            {
                "status": status,
                "rows": summary["packet_row_count"],
                "final_labels": summary["final_label_count"],
                "promotion_review_supported": gate["long_tail_promotion_review_supported"],
            },
            indent=2,
        )
    )
    return result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--r202-attempts", type=Path, default=DEFAULT_ATTEMPTS)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--packet", type=Path)
    parser.add_argument("--labeler-1-template", type=Path)
    parser.add_argument("--labeler-2-template", type=Path)
    parser.add_argument("--labeler-1", type=Path)
    parser.add_argument("--labeler-2", type=Path)
    parser.add_argument("--adjudication", type=Path)
    parser.add_argument("--adjudication-template", type=Path)
    parser.add_argument("--joined-labels", type=Path)
    parser.add_argument("--out-json", type=Path)
    parser.add_argument("--out-csv", type=Path)
    parser.add_argument("--out-md", type=Path)
    return parser


def parse_args() -> argparse.Namespace:
    args = build_parser().parse_args()
    defaults = {
        "packet": "long-tail-promotion-packet-r203.csv",
        "labeler_1_template": "long-tail-promotion-labeler-1-r203.csv",
        "labeler_2_template": "long-tail-promotion-labeler-2-r203.csv",
        "adjudication_template": "long-tail-promotion-adjudication-template-r203.csv",
        "joined_labels": "long-tail-promotion-joined-r203.csv",
        "out_json": "long-tail-promotion-r203.json",
        "out_csv": "long-tail-promotion-results-r203.csv",
        "out_md": "long-tail-promotion-r203.md",
    }
    for field, name in defaults.items():
        if getattr(args, field) is None:
            setattr(args, field, args.out_dir / name)
    return args


if __name__ == "__main__":
    run(parse_args())
