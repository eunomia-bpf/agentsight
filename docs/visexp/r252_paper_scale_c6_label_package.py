#!/usr/bin/env python3
"""R252: build a paper-scale C6 semantic-label collection package.

R124/R190/R203 already define the tag adequacy, merge-risk, and long-tail
promotion label tasks. R252 packages those sheets as one C6 collection handoff
and runs an isolated R195 blank-input check. It records zero human labels and
therefore cannot support C6 by itself.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[1]
OUT_DIR = SCRIPT_DIR / "out"
DEFAULT_OUT = OUT_DIR / "tag-adequacy-paper-r252"
RUN_ID = "R252"

SOURCE_FILES = {
    "r124_labeler_1": OUT_DIR / "human-evidence-r193" / "r124" / "r124-tag-adequacy-labeler-1.csv",
    "r124_labeler_2": OUT_DIR / "human-evidence-r193" / "r124" / "r124-tag-adequacy-labeler-2.csv",
    "r190_labeler_1": OUT_DIR / "human-evidence-r193" / "r190" / "r190-merge-risk-labeler-1.csv",
    "r190_labeler_2": OUT_DIR / "human-evidence-r193" / "r190" / "r190-merge-risk-labeler-2.csv",
    "r203_labeler_1": OUT_DIR / "human-evidence-r193" / "r203" / "r203-long-tail-promotion-labeler-1.csv",
    "r203_labeler_2": OUT_DIR / "human-evidence-r193" / "r203" / "r203-long-tail-promotion-labeler-2.csv",
}

R195_NAMES = {
    "r124_labeler_1": "r124-labeler-1.csv",
    "r124_labeler_2": "r124-labeler-2.csv",
    "r190_labeler_1": "r190-labeler-1.csv",
    "r190_labeler_2": "r190-labeler-2.csv",
    "r203_labeler_1": "r203-labeler-1.csv",
    "r203_labeler_2": "r203-labeler-2.csv",
}

EXPECTED_ROWS = {
    "r124_labeler_1": 300,
    "r124_labeler_2": 300,
    "r190_labeler_1": 160,
    "r190_labeler_2": 160,
    "r203_labeler_1": 41,
    "r203_labeler_2": 41,
}

LABEL_FIELDS = {
    "r124_labeler_1": "label",
    "r124_labeler_2": "label",
    "r190_labeler_1": "audit_label",
    "r190_labeler_2": "audit_label",
    "r203_labeler_1": "promotion_label",
    "r203_labeler_2": "promotion_label",
}

FORBIDDEN_TEXT = [
    "/home/",
    "/tmp/",
    "ANTHROPIC_API",
    "OPENAI_API",
    "user-task-answer-key.csv",
    "score_user_task_results.py",
    "r244-synthetic",
]
FORBIDDEN_PATTERNS = [
    re.compile(r"sk-[A-Za-z0-9]{20,}", re.IGNORECASE),
    re.compile(r"/(?:var/)?tmp/[^\s,;\"'<>)]*", re.IGNORECASE),
    re.compile(r"/private/tmp/[^\s,;\"'<>)]*", re.IGNORECASE),
]

SANITIZE_PATTERNS = [
    (re.compile(r"/home/[A-Za-z0-9._-]+"), "$HOME"),
    (re.compile(r"/(?:var/)?tmp/[^\s,;\"'<>)]*", re.IGNORECASE), "$TMP/<redacted>"),
    (re.compile(r"/private/tmp/[^\s,;\"'<>)]*", re.IGNORECASE), "$TMP/<redacted>"),
]


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT.resolve()))
    except ValueError:
        return str(path)


def git(args: list[str]) -> str | None:
    try:
        return subprocess.check_output(["git", *args], cwd=REPO_ROOT, text=True, stderr=subprocess.DEVNULL).strip()
    except Exception:
        return None


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_csv(path: Path) -> tuple[list[dict[str, str]], list[str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        return list(reader), list(reader.fieldnames or [])


def write_csv(path: Path, rows: list[dict[str, str]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n", extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def sanitize_cell(value: str) -> str:
    sanitized = value
    for pattern, replacement in SANITIZE_PATTERNS:
        sanitized = pattern.sub(replacement, sanitized)
    return sanitized


def sanitize_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    return [{key: sanitize_cell(value or "") for key, value in row.items()} for row in rows]


def copy_sources(out_dir: Path) -> tuple[dict[str, Path], dict[str, Path]]:
    inbox_dir = out_dir / "blank-r195-inbox-template"
    labeler_dir = out_dir / "labeler-packets"
    templates: dict[str, Path] = {}
    labeler_packets: dict[str, Path] = {}
    for key, source in SOURCE_FILES.items():
        if not source.exists():
            raise FileNotFoundError(source)
        rows, fields = read_csv(source)
        sanitized_rows = sanitize_rows(rows)
        target = inbox_dir / R195_NAMES[key]
        write_csv(target, sanitized_rows, fields)
        templates[key] = target

        labeler_id = "L01" if key.endswith("_1") else "L02"
        public_target = labeler_dir / labeler_id / R195_NAMES[key]
        write_csv(public_target, sanitized_rows, fields)
        labeler_packets[key] = public_target
    return templates, labeler_packets


def count_blank_labels(path: Path, field: str) -> tuple[int, int]:
    rows, fields = read_csv(path)
    if field not in fields:
        raise AssertionError(f"{path} is missing label field {field}")
    filled = sum(1 for row in rows if (row.get(field) or "").strip())
    return len(rows), filled


def validate_sheets(copied: dict[str, Path]) -> dict[str, Any]:
    per_sheet: dict[str, Any] = {}
    errors: list[str] = []
    for key, path in copied.items():
        rows, filled = count_blank_labels(path, LABEL_FIELDS[key])
        expected = EXPECTED_ROWS[key]
        if rows != expected:
            errors.append(f"{key} expected {expected} rows, saw {rows}")
        if filled != 0:
            errors.append(f"{key} should be blank, saw {filled} filled labels")
        per_sheet[key] = {
            "path": rel(path),
            "sha256": sha256_file(path),
            "row_count": rows,
            "filled_label_count": filled,
            "expected_row_count": expected,
            "label_field": LABEL_FIELDS[key],
        }
    if errors:
        raise AssertionError("; ".join(errors))
    return per_sheet


def validate_packet_mirror(templates: dict[str, Path], labeler_packets: dict[str, Path]) -> dict[str, Any]:
    metrics: dict[str, Any] = {}
    errors: list[str] = []
    for key, template_path in templates.items():
        packet_path = labeler_packets[key]
        template_rows, template_filled = count_blank_labels(template_path, LABEL_FIELDS[key])
        packet_rows, packet_filled = count_blank_labels(packet_path, LABEL_FIELDS[key])
        template_hash = sha256_file(template_path)
        packet_hash = sha256_file(packet_path)
        if template_hash != packet_hash:
            errors.append(f"{key} labeler packet hash does not match template")
        metrics[key] = {
            "path": rel(packet_path),
            "sha256": packet_hash,
            "row_count": packet_rows,
            "filled_label_count": packet_filled,
            "matches_blank_template_sha256": packet_hash == template_hash,
            "blank_template_path": rel(template_path),
            "blank_template_sha256": template_hash,
            "blank_template_row_count": template_rows,
            "blank_template_filled_label_count": template_filled,
        }
    if errors:
        raise AssertionError("; ".join(errors))
    return metrics


def scan_paths(paths: list[Path]) -> dict[str, Any]:
    hits: list[dict[str, str]] = []
    for path in paths:
        text = path.read_text(encoding="utf-8", errors="replace")
        for needle in FORBIDDEN_TEXT:
            if needle.lower() in text.lower():
                hits.append({"path": rel(path), "needle": needle})
        for pattern in FORBIDDEN_PATTERNS:
            if pattern.search(text):
                hits.append({"path": rel(path), "pattern": pattern.pattern})
    return {
        "forbidden_text": FORBIDDEN_TEXT,
        "forbidden_patterns": [pattern.pattern for pattern in FORBIDDEN_PATTERNS],
        "hits": hits,
        "passed": not hits,
    }


def run_blank_r195_check(copied: dict[str, Path], out_dir: Path) -> dict[str, Any]:
    scored_dir = out_dir / "r195-blank-check" / "scored"
    result_json = out_dir / "r195-blank-check" / "human-evidence-pipeline-r252-blank.json"
    result_md = out_dir / "r195-blank-check" / "human-evidence-pipeline-r252-blank.md"
    missing_r142 = out_dir / "r195-blank-check" / "missing-r142-responses.csv"
    cmd = [
        "python3",
        "docs/visexp/r195_human_evidence_pipeline.py",
        "--r124-labeler-1",
        rel(copied["r124_labeler_1"]),
        "--r124-labeler-2",
        rel(copied["r124_labeler_2"]),
        "--r190-labeler-1",
        rel(copied["r190_labeler_1"]),
        "--r190-labeler-2",
        rel(copied["r190_labeler_2"]),
        "--r203-labeler-1",
        rel(copied["r203_labeler_1"]),
        "--r203-labeler-2",
        rel(copied["r203_labeler_2"]),
        "--r142-responses",
        rel(missing_r142),
        "--scored-dir",
        rel(scored_dir),
        "--out-json",
        rel(result_json),
        "--out-md",
        rel(result_md),
    ]
    proc = subprocess.run(cmd, cwd=REPO_ROOT, text=True, capture_output=True)
    if proc.returncode != 0:
        raise AssertionError(f"R195 blank check failed: {proc.stderr[-2000:]}")
    result = json.loads(result_json.read_text(encoding="utf-8"))
    gates = result.get("claim_gate") or {}
    if any(
        gates.get(name)
        for name in (
            "c5_supported",
            "c6_adequacy_supported",
            "canonicalization_quality_supported",
            "long_tail_promotion_review_supported",
            "canonical_map_updated",
        )
    ):
        raise AssertionError(f"blank R195 check unexpectedly supported a gate: {gates}")
    scored_files = sorted(path for path in scored_dir.rglob("*") if path.is_file()) if scored_dir.exists() else []
    scored_file_count = len(scored_files)
    shutil.rmtree(scored_dir, ignore_errors=True)
    return {
        "cmd": cmd,
        "returncode": proc.returncode,
        "stdout_tail": proc.stdout[-1200:],
        "stderr_tail": proc.stderr[-1200:],
        "result_json": rel(result_json),
        "result_json_sha256": sha256_file(result_json),
        "result_md": rel(result_md),
        "result_md_sha256": sha256_file(result_md),
        "status": result.get("status"),
        "claim_gate": gates,
        "operations": {
            name: (op.get("status") if isinstance(op, dict) else None)
            for name, op in (result.get("operations") or {}).items()
        },
        "intermediate_scored_dir": rel(scored_dir),
        "intermediate_scored_file_count": scored_file_count,
        "intermediate_scored_dir_retained": False,
    }


def write_readme(path: Path, manifest: dict[str, Any]) -> None:
    path.write_text(
        f"""# R252 Paper-Scale C6 Label Package

Status: `{manifest["status"]}`

This package collects the C6 human-label tasks into one handoff:

- R124 tag adequacy: 300 redacted session/prompt/LLM fragments per labeler.
- R190 merge-risk audit: 160 canonicalization-risk rows per labeler.
- R203 regenerated long-tail promotion review: 41 candidate rows per labeler.

Two independent labelers should fill the files under `labeler-packets/L01` and
`labeler-packets/L02`. The coordinator should copy completed files into the
R195 inbox names listed under `blank-r195-inbox-template`, keeping completed
returns private until review/adjudication is finished.

Required R195 return filenames:

```text
r124-labeler-1.csv
r124-labeler-2.csv
r190-labeler-1.csv
r190-labeler-2.csv
r203-labeler-1.csv
r203-labeler-2.csv
```

Do not run the default R195 command unless you intentionally copied completed
files into the default R195 inbox. The package-specific scoring command is:

```bash
python3 docs/visexp/r195_human_evidence_pipeline.py \\
  --r124-labeler-1 <completed-r124-labeler-1.csv> \\
  --r124-labeler-2 <completed-r124-labeler-2.csv> \\
  --r190-labeler-1 <completed-r190-labeler-1.csv> \\
  --r190-labeler-2 <completed-r190-labeler-2.csv> \\
  --r203-labeler-1 <completed-r203-labeler-1.csv> \\
  --r203-labeler-2 <completed-r203-labeler-2.csv> \\
  --r142-responses <missing-or-private-r142-responses.csv> \\
  --scored-dir <private-scored-output-dir>
```

Optional adjudication files are `r124-adjudication.csv`,
`r190-adjudication.csv`, and `r203-adjudication.csv`.

Claim boundary: {manifest["claim_boundary"]}
""",
        encoding="utf-8",
    )


def run(args: argparse.Namespace) -> dict[str, Any]:
    source_commit = git(["rev-parse", "HEAD"])
    source_dirty = bool(git(["status", "--short"]))
    out_dir = Path(args.out).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    copied, labeler_packets = copy_sources(out_dir)
    sheet_metrics = validate_sheets(copied)
    labeler_packet_metrics = validate_packet_mirror(copied, labeler_packets)
    scan = scan_paths([*copied.values(), *labeler_packets.values()])
    if not scan["passed"]:
        raise AssertionError(f"R252 privacy/leak scan failed: {scan['hits']}")
    blank_check = run_blank_r195_check(copied, out_dir)

    rows_per_labeler = EXPECTED_ROWS["r124_labeler_1"] + EXPECTED_ROWS["r190_labeler_1"] + EXPECTED_ROWS["r203_labeler_1"]
    manifest = {
        "schema_version": 1,
        "run_id": RUN_ID,
        "claim": "C6 label-collection logistics for tag adequacy and display-governance review",
        "status": "paper_scale_label_collection_ready_no_labels",
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "source_artifacts": {
            key: {
                "path": rel(path),
                "sha256": sha256_file(path),
            }
            for key, path in SOURCE_FILES.items()
        },
        "sheet_metrics": sheet_metrics,
        "labeler_packet_metrics": labeler_packet_metrics,
        "labeler_packet_count": 2,
        "rows_per_labeler": rows_per_labeler,
        "total_independent_label_decisions_required": rows_per_labeler * 2,
        "actual_human_final_labels": 0,
        "privacy_scan": scan,
        "blank_r195_check": blank_check,
        "readiness": {
            "paper_scale_label_collection_ready": True,
            "blank_inputs_only": True,
            "labeler_packets_match_blank_templates": all(
                row["matches_blank_template_sha256"] for row in labeler_packet_metrics.values()
            ),
        },
        "claim_gate": {
            "c6_adequacy_supported": False,
            "canonicalization_quality_supported": False,
            "long_tail_promotion_review_supported": False,
            "canonical_map_updated": False,
            "weak_accept_supported": False,
            "requires_real_human_labels": True,
            "disallowed_evidence": [
                "blank label sheets",
                "author-filled mock labels",
                "subagent review",
                "LLM-filled labels",
                "R251 behavior-association proxy",
            ],
        },
        "scoring_entrypoint": {
            "default_pipeline": "python3 docs/visexp/r195_human_evidence_pipeline.py",
            "r195_return_name_map": R195_NAMES,
            "optional_adjudication_files": [
                "r124-adjudication.csv",
                "r190-adjudication.csv",
                "r203-adjudication.csv",
            ],
        },
        "claim_boundary": (
            "R252 fixes C6 label-collection logistics and verifies that blank R195 inputs "
            "do not upgrade any support gate. It adds no human labels and cannot support "
            "tag adequacy, merge quality, promotion quality, or weak accept."
        ),
        "provenance": {
            "repo_commit": source_commit,
            "repo_dirty": source_dirty,
            "script": rel(Path(__file__).resolve()),
            "script_sha256": sha256_file(Path(__file__).resolve()),
            "llm_called": False,
            "raw_trace_read": False,
            "human_labels_added": 0,
        },
    }
    write_json(out_dir / "manifest.json", manifest)
    write_readme(out_dir / "README.md", manifest)
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default=str(DEFAULT_OUT))
    args = parser.parse_args()
    result = run(args)
    print(
        json.dumps(
            {
                "run_id": result["run_id"],
                "status": result["status"],
                "rows_per_labeler": result["rows_per_labeler"],
                "blank_r195_status": result["blank_r195_check"]["status"],
                "c6_adequacy_supported": result["claim_gate"]["c6_adequacy_supported"],
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
