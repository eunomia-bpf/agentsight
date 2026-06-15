#!/usr/bin/env python3
"""Generate the blinded R124 human-label sheet for tag adequacy review."""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import json
import re
import subprocess
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[1]
DEFAULT_PACKET = SCRIPT_DIR / "out" / "tag-adequacy-label-packet-r122.csv"
DEFAULT_OUT_CSV = SCRIPT_DIR / "out" / "tag-adequacy-blinded-label-sheet-r124.csv"
DEFAULT_OUT_JSON = SCRIPT_DIR / "out" / "tag-adequacy-blinded-label-sheet-r124.json"
DEFAULT_OUT_MD = SCRIPT_DIR / "out" / "tag-adequacy-blinded-label-sheet-r124.md"

VISIBLE_FIELDS = [
    "row_id",
    "fragment_index",
    "fragment_level",
    "redacted_preview",
    "candidate_tag",
    "rubric",
    "label",
    "notes",
]
HIDDEN_SOURCE_FIELDS = {
    "fragment_hash",
    "source",
    "model",
    "candidate_model",
    "candidate_exact_stable",
    "candidate_distinct_tags",
    "text_chars",
    "labeler_1",
    "labeler_2",
    "adjudicated_label",
}
LABEL_VALUES = ["adequate", "generic_noisy", "misleading"]
RUBRIC = (
    "adequate=tag preserves the main intent; "
    "generic_noisy=tag is vague or low-value; "
    "misleading=tag points to the wrong task"
)
SENSITIVE_RE = re.compile(
    r"/home/[A-Za-z0-9._-]+|Bearer|api_key|sk-[A-Za-z0-9]{20,}|ANTHROPIC_API|OPENAI_API",
    re.IGNORECASE,
)


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT.resolve()))
    except Exception:
        return str(path)


def file_sha256(path: Path) -> str:
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


def read_rows(path: Path) -> tuple[list[dict[str, str]], list[str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        return list(reader), list(reader.fieldnames or [])


def row_id(fragment_index: str) -> str:
    try:
        index = int(fragment_index)
    except ValueError:
        index = 0
    return f"R124-{index:03d}"


def blinded_row(row: dict[str, str]) -> dict[str, str]:
    return {
        "row_id": row_id(row.get("fragment_index", "")),
        "fragment_index": row.get("fragment_index", ""),
        "fragment_level": row.get("kind", ""),
        "redacted_preview": row.get("preview", ""),
        "candidate_tag": row.get("candidate_tag", ""),
        "rubric": RUBRIC,
        "label": "",
        "notes": "",
    }


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=VISIBLE_FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def scan_public_sheet(path: Path) -> dict[str, Any]:
    findings = []
    for line_no, line in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), start=1):
        match = SENSITIVE_RE.search(line)
        if match:
            findings.append({"line": line_no, "match": match.group(0)})
    return {
        "status": "ok" if not findings else "fail",
        "findings": findings[:20],
    }


def build_manifest(
    *,
    packet_path: Path,
    packet_fields: list[str],
    source_rows: list[dict[str, str]],
    blinded_rows: list[dict[str, str]],
    out_csv: Path,
    scan: dict[str, Any],
) -> dict[str, Any]:
    candidate_count = sum(1 for row in blinded_rows if row.get("candidate_tag"))
    return {
        "schema_version": 1,
        "run_id": "R124-blinded-label-sheet",
        "status": "ready_for_independent_labeling",
        "generated_at": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),
        "source_packet": {
            "path": rel(packet_path),
            "sha256": file_sha256(packet_path),
            "row_count": len(source_rows),
            "fields": packet_fields,
        },
        "outputs": {
            "blinded_csv": rel(out_csv),
        },
        "blinding_contract": {
            "visible_fields": VISIBLE_FIELDS,
            "hidden_source_fields": sorted(HIDDEN_SOURCE_FIELDS & set(packet_fields)),
            "label_values": LABEL_VALUES,
            "single_labeler_template": True,
            "independence_rule": (
                "Give a separate blank copy to each labeler; do not combine labels until both copies are frozen."
            ),
        },
        "row_count": len(blinded_rows),
        "candidate_tag_count": candidate_count,
        "candidate_tag_coverage_pct": round(100.0 * candidate_count / len(blinded_rows), 3) if blinded_rows else 0.0,
        "privacy": {
            "raw_trace_files_modified": False,
            "raw_prompt_text_included": False,
            "redacted_preview_only": True,
            "public_sheet_scan": scan,
        },
        "provenance": {
            "repo_commit": git(["rev-parse", "HEAD"]),
            "repo_dirty": bool(git(["status", "--short"])),
            "script_sha256": file_sha256(Path(__file__).resolve()),
        },
        "claim_boundary": (
            "This artifact prepares R124 human labeling but does not itself provide human adequacy evidence."
        ),
    }


def write_json(path: Path, manifest: dict[str, Any]) -> None:
    path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_markdown(path: Path, manifest: dict[str, Any]) -> None:
    contract = manifest["blinding_contract"]
    text = f"""# R124 Blinded Label Sheet

Date: {manifest['generated_at']}

This artifact is the participant-facing sheet for independent human adequacy
labels. It is derived from the R122 packet but hides model identity, model size,
stability metadata, source agent, fragment hash, and downstream result columns.

Rows: {manifest['row_count']}
Candidate tags: {manifest['candidate_tag_count']} ({manifest['candidate_tag_coverage_pct']}%)

Visible fields:

{chr(10).join(f"- `{field}`" for field in contract['visible_fields'])}

Hidden source fields:

{chr(10).join(f"- `{field}`" for field in contract['hidden_source_fields'])}

Label values:

- `adequate`
- `generic_noisy`
- `misleading`

Protocol:

1. Give a separate blank copy of `{manifest['outputs']['blinded_csv']}` to each
   labeler.
2. Ask labelers to fill only `label` and `notes`.
3. Freeze both completed sheets before joining labels back into the scoring
   packet.
4. Do not expose model identity, stability metadata, raw traces, or answer
   summaries during labeling.

Claim impact: this clears the R124 blinding protocol blocker, but C6 remains
partial until real labels are collected, adjudicated, and scored.
"""
    path.write_text(text, encoding="utf-8")


def run(args: argparse.Namespace) -> dict[str, Any]:
    source_rows, packet_fields = read_rows(args.packet)
    missing_fields = {"fragment_index", "kind", "preview", "candidate_tag"} - set(packet_fields)
    if missing_fields:
        raise AssertionError(f"source packet is missing required fields: {sorted(missing_fields)}")
    blinded_rows = [blinded_row(row) for row in source_rows]
    write_csv(args.out_csv, blinded_rows)
    scan = scan_public_sheet(args.out_csv)
    if scan["status"] != "ok":
        raise AssertionError(f"blinded sheet contains sensitive/model-looking text: {scan['findings']}")
    manifest = build_manifest(
        packet_path=args.packet,
        packet_fields=packet_fields,
        source_rows=source_rows,
        blinded_rows=blinded_rows,
        out_csv=args.out_csv,
        scan=scan,
    )
    write_json(args.out_json, manifest)
    write_markdown(args.out_md, manifest)
    print(json.dumps({"status": manifest["status"], "rows": manifest["row_count"], "out": rel(args.out_csv)}, indent=2))
    return manifest


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--packet", type=Path, default=DEFAULT_PACKET)
    parser.add_argument("--out-csv", type=Path, default=DEFAULT_OUT_CSV)
    parser.add_argument("--out-json", type=Path, default=DEFAULT_OUT_JSON)
    parser.add_argument("--out-md", type=Path, default=DEFAULT_OUT_MD)
    return parser


if __name__ == "__main__":
    run(build_parser().parse_args())
