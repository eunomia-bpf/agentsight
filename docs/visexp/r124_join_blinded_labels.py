#!/usr/bin/env python3
"""Join frozen R124 blinded human-label sheets back into a scoring packet.

Default mode validates the source packet and writes a join protocol manifest plus
an empty adjudication template. Supplying two completed labeler sheets produces a
joined R122-compatible CSV that can be passed to score_tag_adequacy.py. This
script never infers labels and never treats LLM/subagent output as human labels.
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

from r124_blinded_label_sheet import VISIBLE_FIELDS, row_id
from score_tag_adequacy import CANONICAL_LABELS, normalize_label


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[1]
DEFAULT_PACKET = SCRIPT_DIR / "out" / "tag-adequacy-label-packet-r122.csv"
DEFAULT_BLINDED = SCRIPT_DIR / "out" / "tag-adequacy-blinded-label-sheet-r124.csv"
DEFAULT_ADJUDICATION_TEMPLATE = SCRIPT_DIR / "out" / "tag-adequacy-adjudication-template-r124.csv"
DEFAULT_JOINED_LABELS = SCRIPT_DIR / "out" / "tag-adequacy-label-packet-r124-joined.csv"
DEFAULT_OUT_JSON = SCRIPT_DIR / "out" / "tag-adequacy-label-join-r124.json"
DEFAULT_OUT_MD = SCRIPT_DIR / "out" / "tag-adequacy-label-join-r124.md"

ADJUDICATION_FIELDS = [
    "row_id",
    "fragment_index",
    "fragment_level",
    "candidate_tag",
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


def file_sha256(path: Path) -> str | None:
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


def source_row_id(row: dict[str, str]) -> str:
    return row_id(row.get("fragment_index", ""))


def source_index(rows: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    indexed = {}
    for row in rows:
        rid = source_row_id(row)
        if rid in indexed:
            raise AssertionError(f"duplicate source row_id {rid}")
        indexed[rid] = row
    return indexed


def validate_blinded_against_source(
    source_rows: list[dict[str, str]],
    blinded_rows: list[dict[str, str]],
) -> None:
    by_id = source_index(source_rows)
    if len(blinded_rows) != len(source_rows):
        raise AssertionError("blinded sheet row count does not match source packet")
    for row in blinded_rows:
        rid = row.get("row_id", "")
        source = by_id.get(rid)
        if not source:
            raise AssertionError(f"blinded sheet references unknown row_id {rid!r}")
        if row.get("fragment_index") != source.get("fragment_index"):
            raise AssertionError(f"fragment_index mismatch for {rid}")
        if row.get("fragment_level") != source.get("kind"):
            raise AssertionError(f"fragment_level mismatch for {rid}")
        if row.get("candidate_tag") != source.get("candidate_tag"):
            raise AssertionError(f"candidate_tag mismatch for {rid}")


def read_labeler_sheet(path: Path, source_rows: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    rows, fields = read_csv(path)
    required = {"row_id", "fragment_index", "fragment_level", "candidate_tag", "label", "notes"}
    missing = sorted(required - set(fields))
    if missing:
        raise AssertionError(f"{path} is missing required labeler fields: {missing}")
    forbidden = {"model", "source", "fragment_hash", "candidate_model", "candidate_exact_stable"}
    exposed = sorted(forbidden & set(fields))
    if exposed:
        raise AssertionError(f"{path} exposes hidden fields: {exposed}")
    validate_blinded_against_source(source_rows, rows)
    out = {}
    for row in rows:
        rid = row.get("row_id", "")
        if rid in out:
            raise AssertionError(f"{path} contains duplicate row_id {rid}")
        label = normalize_label(row.get("label"))
        out[rid] = {
            "label": label,
            "notes": row.get("notes", ""),
        }
    return out


def read_adjudication(path: Path | None, source_rows: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    if not path or not path.exists():
        return {}
    rows, fields = read_csv(path)
    required = {"row_id", "fragment_index", "adjudicated_label", "notes"}
    missing = sorted(required - set(fields))
    if missing:
        raise AssertionError(f"{path} is missing required adjudication fields: {missing}")
    by_id = source_index(source_rows)
    out = {}
    for row in rows:
        rid = row.get("row_id", "")
        source = by_id.get(rid)
        if not source:
            raise AssertionError(f"adjudication references unknown row_id {rid!r}")
        if row.get("fragment_index") != source.get("fragment_index"):
            raise AssertionError(f"adjudication fragment_index mismatch for {rid}")
        label = normalize_label(row.get("adjudicated_label"))
        if label:
            out[rid] = {"label": label, "notes": row.get("notes", "")}
    return out


def combined_notes(
    existing: str,
    labeler_1: dict[str, str],
    labeler_2: dict[str, str],
    adjudication: dict[str, str] | None,
) -> str:
    parts = []
    if existing:
        parts.append(existing)
    if labeler_1.get("notes"):
        parts.append(f"labeler_1: {labeler_1['notes']}")
    if labeler_2.get("notes"):
        parts.append(f"labeler_2: {labeler_2['notes']}")
    if adjudication and adjudication.get("notes"):
        parts.append(f"adjudication: {adjudication['notes']}")
    return " | ".join(parts)


def join_rows(
    source_rows: list[dict[str, str]],
    labeler_1: dict[str, dict[str, str]],
    labeler_2: dict[str, dict[str, str]],
    adjudications: dict[str, dict[str, str]],
) -> tuple[list[dict[str, str]], list[dict[str, str]], dict[str, Any]]:
    joined = []
    disagreements = []
    counts: Counter[str] = Counter()
    for row in source_rows:
        rid = source_row_id(row)
        left = labeler_1.get(rid, {"label": "", "notes": ""})
        right = labeler_2.get(rid, {"label": "", "notes": ""})
        adjudication = adjudications.get(rid)
        left_label = left.get("label", "")
        right_label = right.get("label", "")
        adjudicated_label = adjudication.get("label", "") if adjudication else ""
        if left_label:
            counts["labeler_1_count"] += 1
        if right_label:
            counts["labeler_2_count"] += 1
        if left_label and right_label:
            counts["paired_label_count"] += 1
            if left_label == right_label:
                counts["agreement_count"] += 1
            else:
                counts["disagreement_count"] += 1
                if adjudicated_label:
                    counts["adjudicated_disagreement_count"] += 1
                else:
                    counts["missing_adjudication_count"] += 1
                disagreements.append(
                    {
                        "row_id": rid,
                        "fragment_index": row.get("fragment_index", ""),
                        "fragment_level": row.get("kind", ""),
                        "candidate_tag": row.get("candidate_tag", ""),
                        "labeler_1": left_label,
                        "labeler_2": right_label,
                        "adjudicated_label": adjudicated_label,
                        "notes": adjudication.get("notes", "") if adjudication else "",
                    }
                )
        else:
            counts["missing_pair_count"] += 1
        joined.append(
            {
                **row,
                "labeler_1": left_label,
                "labeler_2": right_label,
                "adjudicated_label": adjudicated_label,
                "notes": combined_notes(row.get("notes", ""), left, right, adjudication),
            }
        )
    summary = {
        "row_count": len(source_rows),
        **{key: counts.get(key, 0) for key in sorted(counts)},
    }
    summary["complete_two_labeler_sheets"] = (
        summary.get("labeler_1_count", 0) == len(source_rows)
        and summary.get("labeler_2_count", 0) == len(source_rows)
    )
    summary["complete_adjudication"] = summary.get("missing_adjudication_count", 0) == 0
    return joined, disagreements, summary


def write_csv(path: Path, rows: list[dict[str, str]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n", extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def status_for(labeler_paths_present: bool, summary: dict[str, Any]) -> str:
    if not labeler_paths_present:
        return "ready_for_independent_label_collection"
    if not summary.get("complete_two_labeler_sheets"):
        return "human_labels_incomplete"
    if not summary.get("complete_adjudication"):
        return "needs_adjudication"
    return "ready_for_scoring"


def build_manifest(
    *,
    args: argparse.Namespace,
    source_rows: list[dict[str, str]],
    source_fields: list[str],
    blinded_rows: list[dict[str, str]],
    status: str,
    summary: dict[str, Any],
    wrote_joined: bool,
    disagreement_rows: list[dict[str, str]],
) -> dict[str, Any]:
    labeler_paths = [path for path in (args.labeler_1, args.labeler_2) if path]
    return {
        "schema_version": 1,
        "run_id": "R124-label-join",
        "claim": "C6",
        "status": status,
        "generated_at": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),
        "source_packet": {
            "path": rel(args.packet),
            "sha256": file_sha256(args.packet),
            "row_count": len(source_rows),
            "fields": source_fields,
        },
        "blinded_sheet": {
            "path": rel(args.blinded),
            "sha256": file_sha256(args.blinded),
            "row_count": len(blinded_rows),
        },
        "labeler_sheets": [
            {"path": rel(path), "sha256": file_sha256(path)}
            for path in labeler_paths
        ],
        "adjudication": {
            "input_path": rel(args.adjudication) if args.adjudication else None,
            "input_sha256": file_sha256(args.adjudication) if args.adjudication else None,
            "template_path": rel(args.adjudication_template),
            "template_sha256": file_sha256(args.adjudication_template),
            "disagreement_rows": len(disagreement_rows),
        },
        "outputs": {
            "joined_labels": rel(args.joined_labels) if wrote_joined else None,
            "joined_labels_sha256": file_sha256(args.joined_labels) if wrote_joined else None,
        },
        "summary": summary,
        "protocol": {
            "label_values": list(CANONICAL_LABELS),
            "required_labeler_count": 2,
            "independence_rule": "Use two separately completed blinded sheets; freeze both before joining.",
            "adjudication_rule": "Only rows with disagreeing non-empty labels require adjudicated_label.",
            "scoring_command": (
                "python3 docs/visexp/score_tag_adequacy.py "
                f"--labels {rel(args.joined_labels)}"
            ),
        },
        "claim_boundary": (
            "This join artifact prepares C6 scoring. It does not support tag adequacy unless "
            "two real human labeler sheets are complete, disagreements are adjudicated, and "
            "score_tag_adequacy.py reports adequacy_supported=true."
        ),
        "provenance": {
            "repo_commit": git(["rev-parse", "HEAD"]),
            "repo_dirty": bool(git(["status", "--short"])),
            "script_sha256": file_sha256(Path(__file__).resolve()),
        },
    }


def write_markdown(path: Path, manifest: dict[str, Any]) -> None:
    summary = manifest["summary"]
    lines = [
        "# R124 Label Join Protocol",
        "",
        f"Status: `{manifest['status']}`",
        f"Generated: {manifest['generated_at']}",
        "",
        "## Inputs",
        "",
        f"- Source packet: `{manifest['source_packet']['path']}`.",
        f"- Blinded sheet: `{manifest['blinded_sheet']['path']}`.",
        f"- Labeler sheets: {len(manifest['labeler_sheets'])}.",
        "",
        "## Join Summary",
        "",
        f"- Rows: {summary.get('row_count', 0)}.",
        f"- Labeler 1 labels: {summary.get('labeler_1_count', 0)}.",
        f"- Labeler 2 labels: {summary.get('labeler_2_count', 0)}.",
        f"- Paired labels: {summary.get('paired_label_count', 0)}.",
        f"- Agreements: {summary.get('agreement_count', 0)}.",
        f"- Disagreements: {summary.get('disagreement_count', 0)}.",
        f"- Missing adjudications: {summary.get('missing_adjudication_count', 0)}.",
        "",
        "## Protocol",
        "",
        "1. Give two independent labelers separate copies of the blinded sheet.",
        "2. Ask each labeler to fill only `label` and `notes`.",
        "3. Run this join script with both frozen sheets.",
        "4. If the status is `needs_adjudication`, fill the adjudication template and rerun.",
        "5. Score the joined packet with `score_tag_adequacy.py --labels <joined csv>`.",
        "",
        "Claim impact: this artifact is a protocol/scoring bridge only. C6 remains partial until scored human labels satisfy the gate.",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run(args: argparse.Namespace) -> dict[str, Any]:
    source_rows, source_fields = read_csv(args.packet)
    blinded_rows, blinded_fields = read_csv(args.blinded)
    if blinded_fields != VISIBLE_FIELDS:
        raise AssertionError("blinded sheet fields do not match the R124 visible contract")
    validate_blinded_against_source(source_rows, blinded_rows)

    labeler_paths_present = bool(args.labeler_1 or args.labeler_2)
    if bool(args.labeler_1) != bool(args.labeler_2):
        raise AssertionError("provide both --labeler-1 and --labeler-2, or neither")

    joined_rows: list[dict[str, str]] = []
    disagreement_rows: list[dict[str, str]] = []
    summary: dict[str, Any] = {
        "row_count": len(source_rows),
        "labeler_1_count": 0,
        "labeler_2_count": 0,
        "paired_label_count": 0,
        "agreement_count": 0,
        "disagreement_count": 0,
        "missing_adjudication_count": 0,
        "complete_two_labeler_sheets": False,
        "complete_adjudication": True,
    }
    wrote_joined = False

    if labeler_paths_present:
        labeler_1 = read_labeler_sheet(args.labeler_1, source_rows)
        labeler_2 = read_labeler_sheet(args.labeler_2, source_rows)
        adjudications = read_adjudication(args.adjudication, source_rows)
        joined_rows, disagreement_rows, summary = join_rows(source_rows, labeler_1, labeler_2, adjudications)
        write_csv(args.joined_labels, joined_rows, source_fields)
        wrote_joined = True
    write_csv(args.adjudication_template, disagreement_rows, ADJUDICATION_FIELDS)
    status = status_for(labeler_paths_present, summary)
    manifest = build_manifest(
        args=args,
        source_rows=source_rows,
        source_fields=source_fields,
        blinded_rows=blinded_rows,
        status=status,
        summary=summary,
        wrote_joined=wrote_joined,
        disagreement_rows=disagreement_rows,
    )
    args.out_json.parent.mkdir(parents=True, exist_ok=True)
    args.out_json.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    write_markdown(args.out_md, manifest)
    print(json.dumps({"status": status, "rows": len(source_rows), "disagreements": len(disagreement_rows)}, indent=2))
    return manifest


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--packet", type=Path, default=DEFAULT_PACKET)
    parser.add_argument("--blinded", type=Path, default=DEFAULT_BLINDED)
    parser.add_argument("--labeler-1", type=Path)
    parser.add_argument("--labeler-2", type=Path)
    parser.add_argument("--adjudication", type=Path)
    parser.add_argument("--adjudication-template", type=Path, default=DEFAULT_ADJUDICATION_TEMPLATE)
    parser.add_argument("--joined-labels", type=Path, default=DEFAULT_JOINED_LABELS)
    parser.add_argument("--out-json", type=Path, default=DEFAULT_OUT_JSON)
    parser.add_argument("--out-md", type=Path, default=DEFAULT_OUT_MD)
    return parser


if __name__ == "__main__":
    run(build_parser().parse_args())
