#!/usr/bin/env python3
"""Score R124 human adequacy labels for one-word semantic tags.

This script consumes the R122 redacted label packet. It does not infer or
fabricate human labels: blank packet rows produce a machine-readable empty
result so C6 remains partial until real labels are collected.
"""

from __future__ import annotations

import argparse
import csv
import json
import statistics
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_LABELS = SCRIPT_DIR / "out" / "tag-adequacy-label-packet-r122.csv"
DEFAULT_OUT_JSON = SCRIPT_DIR / "out" / "tag-adequacy-results-r124.json"
DEFAULT_OUT_CSV = SCRIPT_DIR / "out" / "tag-adequacy-results-r124.csv"
DEFAULT_OUT_MD = SCRIPT_DIR / "out" / "tag-adequacy-results-r124.md"

CANONICAL_LABELS = ("adequate", "generic_noisy", "misleading")
LABEL_ALIASES = {
    "adequate": "adequate",
    "ok": "adequate",
    "good": "adequate",
    "useful": "adequate",
    "generic": "generic_noisy",
    "noisy": "generic_noisy",
    "generic_noisy": "generic_noisy",
    "generic/noisy": "generic_noisy",
    "generic-noisy": "generic_noisy",
    "generic noisy": "generic_noisy",
    "misleading": "misleading",
    "wrong": "misleading",
    "incorrect": "misleading",
}


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def normalize_label(value: str | None) -> str:
    raw = (value or "").strip().lower()
    if not raw:
        return ""
    canonicalized = raw.replace("-", "_").replace("/", "_")
    label = LABEL_ALIASES.get(raw) or LABEL_ALIASES.get(canonicalized)
    if not label:
        raise AssertionError(
            f"unknown adequacy label {value!r}; expected adequate, generic_noisy, or misleading"
        )
    return label


def pct(part: int | float, whole: int | float) -> float | None:
    if not whole:
        return None
    return round(100.0 * part / whole, 3)


def mean(values: list[float]) -> float | None:
    return round(statistics.fmean(values), 3) if values else None


def cohen_kappa(pairs: list[tuple[str, str]]) -> float | None:
    if not pairs:
        return None
    total = len(pairs)
    observed = sum(1 for left, right in pairs if left == right) / total
    left_counts = Counter(left for left, _ in pairs)
    right_counts = Counter(right for _, right in pairs)
    expected = sum(
        (left_counts[label] / total) * (right_counts[label] / total)
        for label in CANONICAL_LABELS
    )
    if expected >= 1.0:
        return 1.0 if observed >= 1.0 else 0.0
    return round((observed - expected) / (1.0 - expected), 3)


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


def score_rows(rows: list[dict[str, str]]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    scored: list[dict[str, Any]] = []
    final_counts: Counter[str] = Counter()
    state_counts: Counter[str] = Counter()
    final_source_counts: Counter[str] = Counter()
    kind_counts: dict[str, Counter[str]] = defaultdict(Counter)
    source_counts: dict[str, Counter[str]] = defaultdict(Counter)
    pair_labels: list[tuple[str, str]] = []
    candidate_tag_count = 0

    for row in rows:
        candidate_tag = (row.get("candidate_tag") or "").strip()
        candidate_model = (row.get("candidate_model") or "").strip()
        candidate_exact_stable = (row.get("candidate_exact_stable") or "").strip()
        candidate_distinct_tags = (row.get("candidate_distinct_tags") or "").strip()
        labeler_1 = normalize_label(row.get("labeler_1"))
        labeler_2 = normalize_label(row.get("labeler_2"))
        adjudicated = normalize_label(row.get("adjudicated_label"))
        final_label, final_source, label_state = final_label_for(row)
        if candidate_tag:
            candidate_tag_count += 1
        if labeler_1 and labeler_2:
            pair_labels.append((labeler_1, labeler_2))
        if final_label:
            final_counts[final_label] += 1
            kind_counts[row.get("kind", "unknown")][final_label] += 1
            source_counts[row.get("source", "unknown")][final_label] += 1
        state_counts[label_state] += 1
        final_source_counts[final_source] += 1
        scored.append(
            {
                "fragment_index": row.get("fragment_index", ""),
                "fragment_hash": row.get("fragment_hash", ""),
                "kind": row.get("kind", ""),
                "source": row.get("source", ""),
                "candidate_tag": candidate_tag,
                "candidate_model": candidate_model,
                "candidate_exact_stable": candidate_exact_stable,
                "candidate_distinct_tags": candidate_distinct_tags,
                "labeler_1": labeler_1,
                "labeler_2": labeler_2,
                "adjudicated_label": adjudicated,
                "final_label": final_label,
                "final_source": final_source,
                "label_state": label_state,
            }
        )

    final_count = sum(final_counts.values())
    both_labeler_count = len(pair_labels)
    agreement_count = sum(1 for left, right in pair_labels if left == right)
    strong_final_count = final_source_counts.get("consensus", 0) + final_source_counts.get("adjudicated", 0)
    summary = {
        "packet_row_count": len(rows),
        "candidate_tag_count": candidate_tag_count,
        "candidate_tag_coverage_pct": pct(candidate_tag_count, len(rows)),
        "final_label_count": final_count,
        "strong_final_label_count": strong_final_count,
        "unlabeled_count": state_counts.get("unlabeled", 0),
        "single_label_count": state_counts.get("weak_final", 0),
        "unadjudicated_disagreement_count": state_counts.get("needs_adjudication", 0),
        "both_labeler_count": both_labeler_count,
        "paired_label_coverage_pct": pct(both_labeler_count, len(rows)),
        "inter_labeler_agreement_pct": pct(agreement_count, both_labeler_count),
        "cohen_kappa": cohen_kappa(pair_labels),
        "final_source_counts": dict(final_source_counts),
        "label_state_counts": dict(state_counts),
        "final_label_counts": {label: final_counts.get(label, 0) for label in CANONICAL_LABELS},
        "adequate_share_pct": pct(final_counts.get("adequate", 0), final_count),
        "generic_noisy_share_pct": pct(final_counts.get("generic_noisy", 0), final_count),
        "misleading_share_pct": pct(final_counts.get("misleading", 0), final_count),
        "by_kind": {
            kind: {
                "final_label_count": sum(counter.values()),
                "adequate_share_pct": pct(counter.get("adequate", 0), sum(counter.values())),
                "generic_noisy_share_pct": pct(counter.get("generic_noisy", 0), sum(counter.values())),
                "misleading_share_pct": pct(counter.get("misleading", 0), sum(counter.values())),
                "counts": {label: counter.get(label, 0) for label in CANONICAL_LABELS},
            }
            for kind, counter in sorted(kind_counts.items())
        },
        "by_source": {
            source: {
                "final_label_count": sum(counter.values()),
                "adequate_share_pct": pct(counter.get("adequate", 0), sum(counter.values())),
                "counts": {label: counter.get(label, 0) for label in CANONICAL_LABELS},
            }
            for source, counter in sorted(source_counts.items())
        },
    }
    return scored, summary


def claim_gate(summary: dict[str, Any]) -> dict[str, Any]:
    final_count = int(summary["final_label_count"])
    strong_final_count = int(summary["strong_final_label_count"])
    candidate_tag_count = int(summary["candidate_tag_count"])
    both_labeler_count = int(summary["both_labeler_count"])
    packet_count = int(summary["packet_row_count"])
    kappa = summary["cohen_kappa"]
    adequate = summary["adequate_share_pct"]
    generic = summary["generic_noisy_share_pct"]
    misleading = summary["misleading_share_pct"]
    complete = packet_count > 0 and final_count == packet_count
    complete_candidate_tags = packet_count > 0 and candidate_tag_count == packet_count
    complete_strong_final_labels = packet_count > 0 and strong_final_count == packet_count
    complete_paired_labels = packet_count > 0 and both_labeler_count == packet_count
    agreement_ok = kappa is not None and kappa >= 0.6
    adequacy_ok = adequate is not None and adequate >= 80.0
    generic_ok = generic is not None and generic <= 20.0
    misleading_ok = misleading is not None and misleading <= 5.0
    return {
        "adequacy_supported": bool(
            complete_candidate_tags
            and complete
            and complete_strong_final_labels
            and complete_paired_labels
            and agreement_ok
            and adequacy_ok
            and generic_ok
            and misleading_ok
        ),
        "requires_real_human_labels": final_count == 0,
        "complete_candidate_tags": complete_candidate_tags,
        "complete_final_labels": complete,
        "complete_strong_final_labels": complete_strong_final_labels,
        "complete_paired_labels": complete_paired_labels,
        "agreement_ok": agreement_ok,
        "adequacy_ok": adequacy_ok,
        "generic_ok": generic_ok,
        "misleading_ok": misleading_ok,
        "success_criteria": {
            "final_labels": "all packet rows",
            "candidate_tags": "all packet rows",
            "strong_final_labels": "all packet rows must be consensus or adjudicated, not single-label",
            "paired_labels": "all packet rows must have labeler_1 and labeler_2 before adjudication",
            "cohen_kappa": ">=0.6",
            "adequate_share_pct": ">=80",
            "generic_noisy_share_pct": "<=20",
            "misleading_share_pct": "<=5",
        },
    }


def result_status(summary: dict[str, Any]) -> str:
    if summary["final_label_count"] == 0 and summary["both_labeler_count"] == 0:
        return "human_labels_empty"
    if (
        summary["final_label_count"] < summary["packet_row_count"]
        or summary["unadjudicated_disagreement_count"] > 0
        or summary["both_labeler_count"] == 0
    ):
        return "human_labels_partial"
    return "human_labels_scored"


def write_scored_csv(path: Path, scored: list[dict[str, Any]]) -> None:
    fields = [
        "fragment_index",
        "fragment_hash",
        "kind",
        "source",
        "candidate_tag",
        "candidate_model",
        "candidate_exact_stable",
        "candidate_distinct_tags",
        "labeler_1",
        "labeler_2",
        "adjudicated_label",
        "final_label",
        "final_source",
        "label_state",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(scored)


def write_summary_md(path: Path, result: dict[str, Any]) -> None:
    summary = result["summary"]
    gate = result["claim_gate"]
    lines = [
        "# R124 Tag Adequacy Results",
        "",
        "This report scores human labels for C6. Blank labels are preserved as missing evidence.",
        "",
        "## Summary",
        "",
        f"- Status: `{result['status']}`.",
        f"- Packet rows: {summary['packet_row_count']}.",
        f"- Candidate tags: {summary['candidate_tag_count']} ({summary['candidate_tag_coverage_pct'] if summary['candidate_tag_coverage_pct'] is not None else 'n/a'}%).",
        f"- Final labels: {summary['final_label_count']}.",
        f"- Strong final labels: {summary['strong_final_label_count']}.",
        f"- Paired label coverage: {summary['paired_label_coverage_pct'] if summary['paired_label_coverage_pct'] is not None else 'n/a'}%.",
        f"- Adequate: {summary['adequate_share_pct'] if summary['adequate_share_pct'] is not None else 'n/a'}%.",
        f"- Generic/noisy: {summary['generic_noisy_share_pct'] if summary['generic_noisy_share_pct'] is not None else 'n/a'}%.",
        f"- Misleading: {summary['misleading_share_pct'] if summary['misleading_share_pct'] is not None else 'n/a'}%.",
        f"- Cohen's kappa: {summary['cohen_kappa'] if summary['cohen_kappa'] is not None else 'n/a'}.",
        "",
        "## Claim Boundary",
        "",
        f"- Adequacy supported: `{gate['adequacy_supported']}`.",
        "- C6 remains partial until this report contains real human labels that meet the gate.",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run(args: argparse.Namespace) -> dict[str, Any]:
    rows = read_csv_rows(Path(args.labels))
    scored, summary = score_rows(rows)
    gate = claim_gate(summary)
    status = result_status(summary)
    result = {
        "schema_version": 1,
        "run_id": "R124-scoring",
        "claim": "C6",
        "status": status,
        "source": str(Path(args.labels).name),
        "rubric": {
            "adequate": "one-word tag preserves the main intent well enough to navigate a flamegraph bucket",
            "generic_noisy": "grammatical but too broad or visually noisy",
            "misleading": "points to the wrong action, object, or task",
        },
        "summary": summary,
        "claim_gate": gate,
        "scored_rows": scored,
        "claim_boundary": "C6 semantic adequacy requires real human labels and agreement/adjudication",
    }
    Path(args.out_json).write_text(json.dumps(result, indent=2), encoding="utf-8")
    write_scored_csv(Path(args.out_csv), scored)
    write_summary_md(Path(args.out_md), result)
    print(json.dumps({key: result[key] for key in ("status", "source")}, indent=2))
    return result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--labels", default=str(DEFAULT_LABELS), help="R122 CSV after human labels are filled")
    parser.add_argument("--out-json", default=str(DEFAULT_OUT_JSON))
    parser.add_argument("--out-csv", default=str(DEFAULT_OUT_CSV))
    parser.add_argument("--out-md", default=str(DEFAULT_OUT_MD))
    return parser


if __name__ == "__main__":
    run(build_parser().parse_args())
