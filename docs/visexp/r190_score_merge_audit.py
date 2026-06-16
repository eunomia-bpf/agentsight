#!/usr/bin/env python3
"""Score R190 human audit labels for canonical tag consolidation.

This script never infers merge correctness. With no labeler sheets it emits an
empty, machine-readable gate so canonicalization remains a protocol/mechanism
claim. With two independent sheets it joins labels, writes an adjudication
template for disagreements, and reports over-merge and under-merge rates.
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
DEFAULT_OUT_DIR = SCRIPT_DIR / "out" / "tag-consolidation-audit-r190"
DEFAULT_PACKET = DEFAULT_OUT_DIR / "merge-risk-audit-packet-r190.csv"
DEFAULT_ADJUDICATION_TEMPLATE = DEFAULT_OUT_DIR / "merge-risk-adjudication-template-r190.csv"
DEFAULT_JOINED = DEFAULT_OUT_DIR / "merge-risk-audit-joined-r190.csv"
DEFAULT_RESULT_JSON = DEFAULT_OUT_DIR / "merge-risk-audit-results-r190.json"
DEFAULT_RESULT_CSV = DEFAULT_OUT_DIR / "merge-risk-audit-results-r190.csv"
DEFAULT_RESULT_MD = DEFAULT_OUT_DIR / "merge-risk-audit-results-r190.md"

AUDIT_LABELS = ("acceptable", "overmerge", "undermerge", "unclear")
LABEL_ALIASES = {
    "acceptable": "acceptable",
    "accept": "acceptable",
    "ok": "acceptable",
    "good": "acceptable",
    "correct": "acceptable",
    "overmerge": "overmerge",
    "over_merge": "overmerge",
    "over-merge": "overmerge",
    "wrong_merge": "overmerge",
    "undermerge": "undermerge",
    "under_merge": "undermerge",
    "under-merge": "undermerge",
    "missed_merge": "undermerge",
    "unclear": "unclear",
    "unsure": "unclear",
    "unknown": "unclear",
}
REQUIRED_PACKET_FIELDS = {
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
    "audit_label",
    "audit_notes",
}
IMMUTABLE_FIELDS = ("audit_id", "audit_type", "dimension", "raw_tag", "canonical_tag")
ADJUDICATION_FIELDS = [
    "audit_id",
    "audit_type",
    "dimension",
    "raw_tag",
    "canonical_tag",
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


def sha256_file(path: Path | None) -> str | None:
    if not path or not path.exists():
        return None
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
            f"unknown R190 audit label {value!r}; expected acceptable, overmerge, undermerge, or unclear"
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
    expected = sum(
        (left_counts[label] / total) * (right_counts[label] / total)
        for label in AUDIT_LABELS
    )
    if expected >= 1.0:
        return 1.0 if observed >= 1.0 else 0.0
    return round((observed - expected) / (1.0 - expected), 3)


def validate_packet(rows: list[dict[str, str]], fields: list[str]) -> None:
    missing = sorted(REQUIRED_PACKET_FIELDS - set(fields))
    if missing:
        raise AssertionError(f"R190 audit packet is missing fields: {missing}")
    seen: set[str] = set()
    for row in rows:
        audit_id = row.get("audit_id", "")
        if not audit_id:
            raise AssertionError("R190 audit packet contains a blank audit_id")
        if audit_id in seen:
            raise AssertionError(f"duplicate audit_id {audit_id}")
        seen.add(audit_id)
        if row.get("audit_type") not in {"overmerge_proxy", "undermerge_proxy"}:
            raise AssertionError(f"unexpected audit_type for {audit_id}: {row.get('audit_type')!r}")
        normalize_label(row.get("audit_label"))


def packet_index(rows: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    return {row["audit_id"]: row for row in rows}


def validate_against_packet(packet_rows: list[dict[str, str]], rows: list[dict[str, str]], path: Path) -> None:
    by_id = packet_index(packet_rows)
    if len(rows) != len(packet_rows):
        raise AssertionError(f"{path} row count does not match the R190 packet")
    seen: set[str] = set()
    for row in rows:
        audit_id = row.get("audit_id", "")
        source = by_id.get(audit_id)
        if not source:
            raise AssertionError(f"{path} references unknown audit_id {audit_id!r}")
        if audit_id in seen:
            raise AssertionError(f"{path} contains duplicate audit_id {audit_id}")
        seen.add(audit_id)
        for field in IMMUTABLE_FIELDS:
            if row.get(field) != source.get(field):
                raise AssertionError(f"{path} changes {field} for {audit_id}")


def read_labeler_sheet(path: Path, packet_rows: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    rows, fields = read_csv(path)
    required = set(IMMUTABLE_FIELDS) | {"audit_label", "audit_notes"}
    missing = sorted(required - set(fields))
    if missing:
        raise AssertionError(f"{path} is missing required R190 label fields: {missing}")
    validate_against_packet(packet_rows, rows, path)
    out: dict[str, dict[str, str]] = {}
    for row in rows:
        out[row["audit_id"]] = {
            "label": normalize_label(row.get("audit_label")),
            "notes": row.get("audit_notes", ""),
        }
    return out


def read_adjudication(path: Path | None, packet_rows: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    if not path or not path.exists():
        return {}
    rows, fields = read_csv(path)
    required = set(IMMUTABLE_FIELDS) | {"adjudicated_label", "notes"}
    missing = sorted(required - set(fields))
    if missing:
        raise AssertionError(f"{path} is missing required adjudication fields: {missing}")
    validate_against_packet(packet_rows, rows, path)
    out: dict[str, dict[str, str]] = {}
    for row in rows:
        label = normalize_label(row.get("adjudicated_label"))
        if label:
            out[row["audit_id"]] = {"label": label, "notes": row.get("notes", "")}
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
        audit_id = source["audit_id"]
        left = labeler_1.get(audit_id, {"label": "", "notes": ""})
        right = labeler_2.get(audit_id, {"label": "", "notes": ""})
        adjudication = adjudications.get(audit_id, {"label": "", "notes": ""})
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
        row.update(
            {
                "final_label": final_label,
                "final_source": final_source,
                "label_state": label_state,
            }
        )
        if row["labeler_1"] and row["labeler_2"] and row["labeler_1"] != row["labeler_2"]:
            disagreements.append(
                {
                    "audit_id": audit_id,
                    "audit_type": source.get("audit_type", ""),
                    "dimension": source.get("dimension", ""),
                    "raw_tag": source.get("raw_tag", ""),
                    "canonical_tag": source.get("canonical_tag", ""),
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
    final_counts: Counter[str] = Counter()
    state_counts: Counter[str] = Counter()
    source_counts: Counter[str] = Counter()
    audit_type_counts: Counter[str] = Counter()
    final_by_type: dict[str, Counter[str]] = {
        "overmerge_proxy": Counter(),
        "undermerge_proxy": Counter(),
    }
    pair_labels: list[tuple[str, str]] = []

    for source in rows:
        row = dict(source)
        audit_type = row.get("audit_type", "")
        labeler_1 = normalize_label(row.get("labeler_1"))
        labeler_2 = normalize_label(row.get("labeler_2"))
        adjudicated = normalize_label(row.get("adjudicated_label"))
        row.update({"labeler_1": labeler_1, "labeler_2": labeler_2, "adjudicated_label": adjudicated})
        final_label, final_source, label_state = final_label_for(row)
        row.update({"final_label": final_label, "final_source": final_source, "label_state": label_state})
        audit_type_counts[audit_type] += 1
        state_counts[label_state] += 1
        source_counts[final_source] += 1
        if labeler_1 and labeler_2:
            pair_labels.append((labeler_1, labeler_2))
        if final_label:
            final_counts[final_label] += 1
            final_by_type.setdefault(audit_type, Counter())[final_label] += 1
        scored.append(row)

    final_count = sum(final_counts.values())
    both_labeler_count = len(pair_labels)
    agreement_count = sum(1 for left, right in pair_labels if left == right)
    strong_final_count = source_counts.get("consensus", 0) + source_counts.get("adjudicated", 0)
    overmerge_denominator = (
        final_by_type["overmerge_proxy"].get("acceptable", 0)
        + final_by_type["overmerge_proxy"].get("overmerge", 0)
    )
    undermerge_denominator = (
        final_by_type["undermerge_proxy"].get("acceptable", 0)
        + final_by_type["undermerge_proxy"].get("undermerge", 0)
    )
    summary = {
        "packet_row_count": len(rows),
        "overmerge_proxy_rows": audit_type_counts.get("overmerge_proxy", 0),
        "undermerge_proxy_rows": audit_type_counts.get("undermerge_proxy", 0),
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
        "final_label_counts": {label: final_counts.get(label, 0) for label in AUDIT_LABELS},
        "unclear_share_pct": pct(final_counts.get("unclear", 0), final_count),
        "overmerge_error_rows": final_by_type["overmerge_proxy"].get("overmerge", 0),
        "overmerge_audited_rows": overmerge_denominator,
        "overmerge_rate_pct": pct(final_by_type["overmerge_proxy"].get("overmerge", 0), overmerge_denominator),
        "undermerge_error_rows": final_by_type["undermerge_proxy"].get("undermerge", 0),
        "undermerge_audited_rows": undermerge_denominator,
        "undermerge_rate_pct": pct(final_by_type["undermerge_proxy"].get("undermerge", 0), undermerge_denominator),
        "by_audit_type": {
            audit_type: {
                "final_label_count": sum(counter.values()),
                "counts": {label: counter.get(label, 0) for label in AUDIT_LABELS},
            }
            for audit_type, counter in sorted(final_by_type.items())
        },
    }
    return scored, summary


def claim_gate(summary: dict[str, Any]) -> dict[str, Any]:
    packet_count = int(summary["packet_row_count"])
    final_count = int(summary["final_label_count"])
    strong_final_count = int(summary["strong_final_label_count"])
    paired_count = int(summary["both_labeler_count"])
    kappa = summary["cohen_kappa"]
    unclear = summary["unclear_share_pct"]
    overmerge = summary["overmerge_rate_pct"]
    undermerge = summary["undermerge_rate_pct"]
    complete = packet_count > 0 and final_count == packet_count
    strong_complete = packet_count > 0 and strong_final_count == packet_count
    paired_complete = packet_count > 0 and paired_count == packet_count
    agreement_ok = kappa is not None and kappa >= 0.6
    unclear_ok = unclear is not None and unclear <= 10.0
    overmerge_ok = overmerge is not None and overmerge <= 10.0
    undermerge_ok = undermerge is not None and undermerge <= 20.0
    return {
        "canonicalization_quality_supported": bool(
            complete
            and strong_complete
            and paired_complete
            and agreement_ok
            and unclear_ok
            and overmerge_ok
            and undermerge_ok
        ),
        "requires_real_human_labels": final_count == 0,
        "complete_final_labels": complete,
        "complete_strong_final_labels": strong_complete,
        "complete_paired_labels": paired_complete,
        "agreement_ok": agreement_ok,
        "unclear_ok": unclear_ok,
        "overmerge_ok": overmerge_ok,
        "undermerge_ok": undermerge_ok,
        "success_criteria": {
            "final_labels": "all audit rows",
            "strong_final_labels": "all rows must be consensus or adjudicated, not single-label",
            "paired_labels": "all rows must have labeler_1 and labeler_2 before adjudication",
            "cohen_kappa": ">=0.6",
            "unclear_share_pct": "<=10",
            "overmerge_rate_pct": "<=10 among non-unclear overmerge_proxy labels",
            "undermerge_rate_pct": "<=20 among non-unclear undermerge_proxy labels",
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


def write_summary_md(path: Path, result: dict[str, Any]) -> None:
    summary = result["summary"]
    gate = result["claim_gate"]
    lines = [
        "# R190 Merge-Risk Audit Results",
        "",
        "This report scores human labels for the canonical tag consolidation audit. Blank labels are missing evidence.",
        "",
        "## Summary",
        "",
        f"- Status: `{result['status']}`.",
        f"- Audit rows: {summary['packet_row_count']}.",
        f"- Final labels: {summary['final_label_count']}.",
        f"- Strong final labels: {summary['strong_final_label_count']}.",
        f"- Paired label coverage: {summary['paired_label_coverage_pct'] if summary['paired_label_coverage_pct'] is not None else 'n/a'}%.",
        f"- Cohen's kappa: {summary['cohen_kappa'] if summary['cohen_kappa'] is not None else 'n/a'}.",
        f"- Unclear labels: {summary['unclear_share_pct'] if summary['unclear_share_pct'] is not None else 'n/a'}%.",
        f"- Over-merge rate: {summary['overmerge_rate_pct'] if summary['overmerge_rate_pct'] is not None else 'n/a'}%.",
        f"- Under-merge rate: {summary['undermerge_rate_pct'] if summary['undermerge_rate_pct'] is not None else 'n/a'}%.",
        "",
        "## Claim Boundary",
        "",
        f"- Canonicalization quality supported: `{gate['canonicalization_quality_supported']}`.",
        "- This does not support raw tag adequacy (R124) or developer utility (R142/R151).",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run(args: argparse.Namespace) -> dict[str, Any]:
    packet_rows, packet_fields = read_csv(args.packet)
    validate_packet(packet_rows, packet_fields)
    labeler_paths_present = bool(args.labeler_1 or args.labeler_2)
    if bool(args.labeler_1) != bool(args.labeler_2):
        raise AssertionError("provide both --labeler-1 and --labeler-2, or neither")

    joined_rows: list[dict[str, Any]]
    disagreement_rows: list[dict[str, Any]]
    if labeler_paths_present:
        labeler_1 = read_labeler_sheet(args.labeler_1, packet_rows)
        labeler_2 = read_labeler_sheet(args.labeler_2, packet_rows)
        adjudications = read_adjudication(args.adjudication, packet_rows)
        joined_rows, disagreement_rows = join_rows(packet_rows, labeler_1, labeler_2, adjudications)
        joined_fields = [*packet_fields, "labeler_1", "labeler_2", "adjudicated_label", "labeler_1_notes", "labeler_2_notes", "adjudication_notes", "final_label", "final_source", "label_state"]
        write_csv(args.joined_labels, joined_rows, joined_fields)
        score_input = joined_rows
    else:
        joined_rows = []
        disagreement_rows = []
        score_input = [
            {**row, "labeler_1": "", "labeler_2": "", "adjudicated_label": ""}
            for row in packet_rows
        ]

    write_csv(args.adjudication_template, disagreement_rows, ADJUDICATION_FIELDS)
    scored_rows, summary = score_rows(score_input)
    gate = claim_gate(summary)
    status = result_status(summary)
    result = {
        "schema_version": 1,
        "run_id": "R190-score",
        "claim": "C3/C6-display-layer",
        "status": status,
        "generated_at": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),
        "source_packet": {
            "path": rel(args.packet),
            "sha256": sha256_file(args.packet),
            "row_count": len(packet_rows),
        },
        "labeler_sheets": [
            {"path": rel(path), "sha256": sha256_file(path)}
            for path in (args.labeler_1, args.labeler_2)
            if path
        ],
        "adjudication": {
            "input_path": rel(args.adjudication) if args.adjudication else None,
            "input_sha256": sha256_file(args.adjudication) if args.adjudication else None,
            "template_path": rel(args.adjudication_template),
            "template_sha256": sha256_file(args.adjudication_template),
            "disagreement_rows": len(disagreement_rows),
        },
        "outputs": {
            "joined_labels": rel(args.joined_labels) if labeler_paths_present else None,
            "joined_labels_sha256": sha256_file(args.joined_labels) if labeler_paths_present else None,
            "scored_csv": rel(args.out_csv),
            "summary_md": rel(args.out_md),
            "summary_json": rel(args.out_json),
        },
        "rubric": {
            "acceptable": "current raw-to-canonical decision is semantically acceptable for display aggregation",
            "overmerge": "an applied merge hides a meaningfully distinct tag",
            "undermerge": "a retained/review-only tag should be merged into the proposed canonical tag",
            "unclear": "the row does not provide enough context for a confident judgment",
        },
        "summary": summary,
        "claim_gate": gate,
        "claim_boundary": (
            "R190 scoring estimates canonical display-layer merge risk only. It does not replace "
            "R124 raw tag adequacy labels or R142/R151 developer utility data."
        ),
        "provenance": {
            "repo_commit": git(["rev-parse", "HEAD"]),
            "repo_dirty": bool(git(["status", "--short"])),
            "script_sha256": sha256_file(Path(__file__).resolve()),
        },
    }
    write_csv(args.out_csv, scored_rows, [*packet_fields, "labeler_1", "labeler_2", "adjudicated_label", "final_label", "final_source", "label_state"])
    args.out_json.parent.mkdir(parents=True, exist_ok=True)
    args.out_json.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_summary_md(args.out_md, result)
    print(json.dumps({"status": status, "rows": len(packet_rows), "final_labels": summary["final_label_count"]}, indent=2))
    return result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--packet", type=Path, default=DEFAULT_PACKET)
    parser.add_argument("--labeler-1", type=Path)
    parser.add_argument("--labeler-2", type=Path)
    parser.add_argument("--adjudication", type=Path)
    parser.add_argument("--adjudication-template", type=Path, default=DEFAULT_ADJUDICATION_TEMPLATE)
    parser.add_argument("--joined-labels", type=Path, default=DEFAULT_JOINED)
    parser.add_argument("--out-json", type=Path, default=DEFAULT_RESULT_JSON)
    parser.add_argument("--out-csv", type=Path, default=DEFAULT_RESULT_CSV)
    parser.add_argument("--out-md", type=Path, default=DEFAULT_RESULT_MD)
    return parser


if __name__ == "__main__":
    run(build_parser().parse_args())
