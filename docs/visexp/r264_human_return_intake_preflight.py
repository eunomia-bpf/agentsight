#!/usr/bin/env python3
"""R264: preflight real human-return files before R195 scoring.

This script is intentionally an intake gate, not an outcome scorer. The default
run checks the committed paper-scale handoff contract and confirms that no
private returns are present. When completed private CSVs are supplied, it checks
row coverage, blank/partial responses, label coverage, duplicate keys, and known
synthetic-return markers before producing the exact R195 command to run.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import shlex
import subprocess
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from r195_human_evidence_pipeline import FORBIDDEN_RETURN_MARKERS
from r190_score_merge_audit import normalize_label as normalize_r190_label
from r203_long_tail_promotion_gate import normalize_label as normalize_r203_label
from score_tag_adequacy import normalize_label as normalize_r124_label
from score_user_task_results import (
    REQUIRED_RESPONSE_FIELDS,
    is_placeholder_response,
    parse_response_json,
)


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[1]
OUT_ROOT = SCRIPT_DIR / "out"

DEFAULT_OUT_DIR = OUT_ROOT / "human-return-intake-r264"
DEFAULT_RETURN_CHECKLIST = (
    OUT_ROOT / "human-evidence-paper-scale-bundle-r258" / "return-checklist-r258.csv"
)
DEFAULT_R258_SUMMARY = (
    OUT_ROOT / "human-evidence-paper-scale-bundle-r258" / "human-evidence-paper-scale-bundle-r258.json"
)
DEFAULT_R259_SYNTHETIC_C5 = (
    OUT_ROOT
    / "human-evidence-paper-scale-static-kit-r259"
    / "synthetic-exports"
    / "user-task-response-template-r249-paper.csv"
)

DEFAULT_PRIVATE_ROOT = REPO_ROOT / "private" / "completed-paper-scale-r264"
DEFAULT_C5_RESPONSES = DEFAULT_PRIVATE_ROOT / "c5" / "user-task-response-template-r249-paper.csv"
DEFAULT_C6_ROOT = DEFAULT_PRIVATE_ROOT / "c6"
DEFAULT_R124_LABELER_1 = DEFAULT_C6_ROOT / "L01" / "r124-labeler-1.csv"
DEFAULT_R124_LABELER_2 = DEFAULT_C6_ROOT / "L02" / "r124-labeler-2.csv"
DEFAULT_R190_LABELER_1 = DEFAULT_C6_ROOT / "L01" / "r190-labeler-1.csv"
DEFAULT_R190_LABELER_2 = DEFAULT_C6_ROOT / "L02" / "r190-labeler-2.csv"
DEFAULT_R203_LABELER_1 = DEFAULT_C6_ROOT / "L01" / "r203-labeler-1.csv"
DEFAULT_R203_LABELER_2 = DEFAULT_C6_ROOT / "L02" / "r203-labeler-2.csv"

R249_ASSIGNMENTS = OUT_ROOT / "user-task-paper-r249" / "user-task-assignments-r249-paper.csv"
R142_BUNDLE = OUT_ROOT / "user-task-benchmark.json"
R142_ANSWER_KEY = OUT_ROOT / "user-task-answer-key.csv"
R195_SCRIPT = SCRIPT_DIR / "r195_human_evidence_pipeline.py"

EXPECTED_C5_ROWS = 168
EXPECTED_R124_ROWS = 300
EXPECTED_R190_ROWS = 160
EXPECTED_R203_ROWS = 41

LABEL_SPECS = {
    "r124_labeler_1": {
        "expected_rows": EXPECTED_R124_ROWS,
        "id_field": "row_id",
        "label_field": "label",
        "required_fields": {"row_id", "fragment_index", "fragment_level", "candidate_tag", "label", "notes"},
        "normalizer": normalize_r124_label,
    },
    "r124_labeler_2": {
        "expected_rows": EXPECTED_R124_ROWS,
        "id_field": "row_id",
        "label_field": "label",
        "required_fields": {"row_id", "fragment_index", "fragment_level", "candidate_tag", "label", "notes"},
        "normalizer": normalize_r124_label,
    },
    "r190_labeler_1": {
        "expected_rows": EXPECTED_R190_ROWS,
        "id_field": "audit_id",
        "label_field": "audit_label",
        "required_fields": {
            "audit_id",
            "audit_type",
            "dimension",
            "raw_tag",
            "canonical_tag",
            "audit_label",
            "audit_notes",
        },
        "normalizer": normalize_r190_label,
    },
    "r190_labeler_2": {
        "expected_rows": EXPECTED_R190_ROWS,
        "id_field": "audit_id",
        "label_field": "audit_label",
        "required_fields": {
            "audit_id",
            "audit_type",
            "dimension",
            "raw_tag",
            "canonical_tag",
            "audit_label",
            "audit_notes",
        },
        "normalizer": normalize_r190_label,
    },
    "r203_labeler_1": {
        "expected_rows": EXPECTED_R203_ROWS,
        "id_field": "promotion_id",
        "label_field": "promotion_label",
        "required_fields": {
            "promotion_id",
            "dimension",
            "raw_tag",
            "regenerated_tag",
            "proposed_action",
            "promotion_label",
            "promotion_notes",
        },
        "normalizer": normalize_r203_label,
    },
    "r203_labeler_2": {
        "expected_rows": EXPECTED_R203_ROWS,
        "id_field": "promotion_id",
        "label_field": "promotion_label",
        "required_fields": {
            "promotion_id",
            "dimension",
            "raw_tag",
            "regenerated_tag",
            "proposed_action",
            "promotion_label",
            "promotion_notes",
        },
        "normalizer": normalize_r203_label,
    },
}


def rel(path: Path | None) -> str | None:
    if path is None:
        return None
    try:
        return str(path.resolve().relative_to(REPO_ROOT.resolve()))
    except Exception:
        return str(path)


def sha256_file(path: Path) -> str | None:
    if not path.exists():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def git(args: list[str], *, check: bool = False) -> subprocess.CompletedProcess[str] | None:
    try:
        return subprocess.run(
            ["git", *args],
            cwd=REPO_ROOT,
            text=True,
            capture_output=True,
            check=check,
        )
    except Exception:
        return None


def git_text(args: list[str]) -> str | None:
    proc = git(args)
    if proc is None or proc.returncode != 0:
        return None
    return proc.stdout.strip()


def read_csv(path: Path) -> tuple[list[dict[str, str]], list[str]]:
    if not path.exists():
        return [], []
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        return list(reader), list(reader.fieldnames or [])


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def pct(part: int | float, whole: int | float) -> float | None:
    return round(100.0 * part / whole, 3) if whole else None


def marker_hits(path: Path, *, max_hits: int = 20) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    hits: list[dict[str, Any]] = []
    rows, _fields = read_csv(path)
    for row_index, row in enumerate(rows, start=1):
        for field, value in row.items():
            cell = value or ""
            for marker in FORBIDDEN_RETURN_MARKERS:
                if marker in cell:
                    hits.append({"row": row_index, "field": field, "marker": marker})
                    if len(hits) >= max_hits:
                        return hits
    return hits


def file_info(path: Path) -> dict[str, Any]:
    rows, fields = read_csv(path) if path.suffix.lower() == ".csv" and path.exists() else ([], [])
    return {
        "path": rel(path),
        "exists": path.exists(),
        "sha256": sha256_file(path),
        "row_count": len(rows) if path.suffix.lower() == ".csv" and path.exists() else None,
        "field_count": len(fields) if fields else None,
    }


def validate_return_checklist(path: Path, r258_summary: Path) -> dict[str, Any]:
    rows, fields = read_csv(path)
    required_fields = {
        "return_file",
        "package_path",
        "destination",
        "row_count",
        "claim_gate",
        "required_for_weak_accept",
        "notes",
    }
    missing_fields = sorted(required_fields - set(fields))
    destinations = [row.get("destination", "") for row in rows]
    expected_files = {
        "user-task-response-template-r249-paper.csv",
        "user-task-assignments-r249-paper.csv",
        "r124-labeler-1.csv",
        "r124-labeler-2.csv",
        "r190-labeler-1.csv",
        "r190-labeler-2.csv",
        "r203-labeler-1.csv",
        "r203-labeler-2.csv",
        "r195-inbox-template/*",
    }
    listed_files = {row.get("return_file", "") for row in rows}
    numeric_row_counts = []
    for row in rows:
        try:
            numeric_row_counts.append(int(row.get("row_count", "0")))
        except ValueError:
            numeric_row_counts.append(0)
    summary = json.loads(r258_summary.read_text(encoding="utf-8")) if r258_summary.exists() else {}
    checks = {
        "exists": path.exists(),
        "summary_exists": r258_summary.exists(),
        "field_contract": not missing_fields,
        "expected_row_count": len(rows) == 9,
        "expected_return_files": expected_files <= listed_files,
        "expected_counts_present": sorted(numeric_row_counts) == [41, 41, 160, 160, 168, 168, 300, 300, 1002],
        "private_c5_destination": any("private/completed-paper-scale-c5" in item for item in destinations),
        "r258_claim_gate_false": not bool(((summary.get("claim_gate") or {}).get("weak_accept_supported"))),
    }
    return {
        "path": rel(path),
        "summary_path": rel(r258_summary),
        "row_count": len(rows),
        "missing_fields": missing_fields,
        "listed_files": sorted(listed_files),
        "checks": checks,
        "passed": all(checks.values()),
    }


def assignment_key(row: dict[str, str]) -> tuple[str, str, str, str, str]:
    return (
        row.get("participant_id", ""),
        row.get("order_index", ""),
        row.get("packet_id", ""),
        row.get("task_id", ""),
        row.get("condition", ""),
    )


def parse_finite(value: str) -> float | None:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return parsed if math.isfinite(parsed) else None


def validate_c5(path: Path, assignments_path: Path) -> dict[str, Any]:
    if not path.exists():
        return {
            "status": "missing",
            "path": rel(path),
            "ready_for_r195": False,
            "present": False,
            "errors": [],
            "warnings": [],
        }

    rows, fields = read_csv(path)
    assignment_rows, _assignment_fields = read_csv(assignments_path)
    field_set = set(fields)
    missing_fields = sorted(REQUIRED_RESPONSE_FIELDS - field_set)
    response_key_counts = Counter(assignment_key(row) for row in rows)
    duplicate_keys = [key for key, count in response_key_counts.items() if count > 1]
    assignment_keys = set(assignment_key(row) for row in assignment_rows)
    response_keys = set(response_key_counts)
    missing_assignments = sorted(assignment_keys - response_keys)
    extra_assignments = sorted(response_keys - assignment_keys)
    placeholders = [idx for idx, row in enumerate(rows, start=1) if is_placeholder_response(row)]
    empty_response_json = [
        idx
        for idx, row in enumerate(rows, start=1)
        if (row.get("response_json", "").strip() in {"", "{}"})
    ]
    json_errors = []
    time_errors = []
    confidence_errors = []
    for idx, row in enumerate(rows, start=1):
        _parsed, error = parse_response_json(row.get("response_json", ""))
        if error:
            json_errors.append({"row": idx, "error": error})
        task_time = parse_finite(row.get("task_time_seconds", ""))
        confidence = parse_finite(row.get("confidence", ""))
        if task_time is None or task_time <= 0:
            time_errors.append(idx)
        if confidence is None or confidence < 1 or confidence > 5:
            confidence_errors.append(idx)

    participants = Counter(row.get("participant_id", "") for row in rows if row.get("participant_id", ""))
    hits = marker_hits(path)
    errors: list[str] = []
    warnings: list[str] = []
    if missing_fields:
        errors.append(f"missing fields: {missing_fields}")
    if len(rows) != EXPECTED_C5_ROWS:
        errors.append(f"expected {EXPECTED_C5_ROWS} rows, found {len(rows)}")
    if duplicate_keys:
        errors.append(f"duplicate response assignment keys: {duplicate_keys[:5]}")
    if missing_assignments:
        errors.append(f"missing assignment rows: {missing_assignments[:5]}")
    if extra_assignments:
        errors.append(f"extra rows outside assignment file: {extra_assignments[:5]}")
    if hits:
        errors.append("forbidden synthetic-return markers present")
    if placeholders:
        errors.append(f"{len(placeholders)} placeholder response rows remain")
    if empty_response_json:
        errors.append(f"{len(empty_response_json)} empty response_json cells remain")
    if json_errors:
        errors.append(f"{len(json_errors)} response_json cells are invalid JSON")
    if time_errors:
        errors.append(f"{len(time_errors)} rows have missing/non-positive task_time_seconds")
    if confidence_errors:
        errors.append(f"{len(confidence_errors)} rows have missing/out-of-range confidence")
    if len(participants) != 12:
        warnings.append(f"expected 12 participants, found {len(participants)}")

    ready = not errors
    if ready:
        status = "ready_for_r195"
    elif rows and len(placeholders) == len(rows):
        status = "blank_template"
    else:
        status = "invalid_or_partial"
    return {
        "status": status,
        "path": rel(path),
        "ready_for_r195": ready,
        "present": True,
        "row_count": len(rows),
        "expected_row_count": EXPECTED_C5_ROWS,
        "participant_count": len(participants),
        "rows_per_participant": dict(sorted(participants.items())),
        "placeholder_rows": len(placeholders),
        "empty_response_json_rows": len(empty_response_json),
        "json_error_count": len(json_errors),
        "time_error_count": len(time_errors),
        "confidence_error_count": len(confidence_errors),
        "duplicate_key_count": len(duplicate_keys),
        "missing_assignment_count": len(missing_assignments),
        "extra_assignment_count": len(extra_assignments),
        "marker_hits": hits,
        "errors": errors,
        "warnings": warnings,
    }


def validate_label_file(
    name: str,
    path: Path,
    normalizer: Callable[[str | None], str],
    id_field: str,
    label_field: str,
    required_fields: set[str],
    expected_rows: int,
) -> dict[str, Any]:
    if not path.exists():
        return {
            "status": "missing",
            "path": rel(path),
            "ready_for_r195": False,
            "present": False,
            "errors": [],
        }

    rows, fields = read_csv(path)
    field_set = set(fields)
    missing_fields = sorted(required_fields - field_set)
    ids = [row.get(id_field, "") for row in rows]
    duplicate_ids = [item for item, count in Counter(ids).items() if item and count > 1]
    blank_ids = sum(1 for item in ids if not item)
    label_count = 0
    invalid_labels = []
    for idx, row in enumerate(rows, start=1):
        value = row.get(label_field, "")
        if not value.strip():
            continue
        try:
            normalized = normalizer(value)
        except AssertionError as exc:
            invalid_labels.append({"row": idx, "value": value, "error": str(exc)})
            continue
        if normalized:
            label_count += 1
    hits = marker_hits(path)

    errors = []
    if missing_fields:
        errors.append(f"missing fields: {missing_fields}")
    if len(rows) != expected_rows:
        errors.append(f"expected {expected_rows} rows, found {len(rows)}")
    if duplicate_ids:
        errors.append(f"duplicate {id_field}: {duplicate_ids[:5]}")
    if blank_ids:
        errors.append(f"{blank_ids} blank {id_field} values")
    if invalid_labels:
        errors.append(f"{len(invalid_labels)} invalid {label_field} values")
    if hits:
        errors.append("forbidden synthetic-return markers present")
    if label_count != expected_rows:
        errors.append(f"{expected_rows - label_count} missing {label_field} cells")

    ready = not errors
    if ready:
        status = "ready_for_r195"
    elif rows and label_count == 0 and not hits:
        status = "blank_template"
    else:
        status = "invalid_or_partial"
    return {
        "status": status,
        "path": rel(path),
        "ready_for_r195": ready,
        "present": True,
        "row_count": len(rows),
        "expected_row_count": expected_rows,
        "label_count": label_count,
        "label_coverage_pct": pct(label_count, expected_rows),
        "duplicate_id_count": len(duplicate_ids),
        "invalid_label_count": len(invalid_labels),
        "marker_hits": hits,
        "errors": errors,
    }


def validate_labels(paths: dict[str, Path]) -> dict[str, Any]:
    files: dict[str, Any] = {}
    for name, spec in LABEL_SPECS.items():
        files[name] = validate_label_file(
            name,
            paths[name],
            spec["normalizer"],
            spec["id_field"],
            spec["label_field"],
            spec["required_fields"],
            spec["expected_rows"],
        )
    groups = {
        "r124": ["r124_labeler_1", "r124_labeler_2"],
        "r190": ["r190_labeler_1", "r190_labeler_2"],
        "r203": ["r203_labeler_1", "r203_labeler_2"],
    }
    group_status: dict[str, Any] = {}
    for group, names in groups.items():
        present = [name for name in names if files[name]["present"]]
        ready = [name for name in names if files[name]["ready_for_r195"]]
        invalid = [name for name in names if files[name]["present"] and not files[name]["ready_for_r195"]]
        if len(ready) == len(names):
            status = "ready_for_r195"
        elif not present:
            status = "missing"
        elif invalid:
            status = "invalid_or_partial"
        else:
            status = "missing"
        group_status[group] = {
            "status": status,
            "ready_for_r195": len(ready) == len(names),
            "present": present,
            "ready": ready,
            "invalid_or_partial": invalid,
            "required_files": names,
        }
    return {"files": files, "groups": group_status}


def synthetic_marker_regression(path: Path) -> dict[str, Any]:
    hits = marker_hits(path)
    return {
        "path": rel(path),
        "exists": path.exists(),
        "marker_hits": hits[:5],
        "marker_hit_count": len(hits),
        "passed": path.exists() and bool(hits),
        "purpose": "R259 synthetic exports must remain detectable before R195 scoring.",
    }


def git_ignore_probe(path: str) -> bool:
    proc = git(["check-ignore", path])
    return bool(proc and proc.returncode == 0)


def privacy_guard(paths: dict[str, Path]) -> dict[str, Any]:
    tracked_private = git_text(["ls-files", "private", "docs/visexp/out/human-evidence-r195/inbox"])
    candidate_files = [path for path in paths.values() if path.exists()]
    tracked_candidates = []
    for path in candidate_files:
        proc = git(["ls-files", "--error-unmatch", rel(path) or str(path)])
        if proc and proc.returncode == 0:
            tracked_candidates.append(rel(path))
    checks = {
        "private_root_ignored": git_ignore_probe("private/completed-paper-scale-r264/sentinel.csv"),
        "r195_inbox_ignored": git_ignore_probe(
            "docs/visexp/out/human-evidence-r195/inbox/r124-labeler-1.csv"
        ),
        "r195_scored_ignored": git_ignore_probe(
            "docs/visexp/out/human-evidence-r195/scored/r124/result.csv"
        ),
        "no_tracked_private_return_files": not bool(tracked_private),
        "no_existing_return_file_is_tracked": not tracked_candidates,
    }
    return {
        "checks": checks,
        "tracked_private_matches": tracked_private.splitlines() if tracked_private else [],
        "tracked_candidate_files": tracked_candidates,
        "passed": all(checks.values()),
    }


def build_r195_command(args: argparse.Namespace) -> list[str]:
    scored_dir = args.r195_scored_dir
    out_json = scored_dir / "human-evidence-pipeline-r195.json"
    out_md = scored_dir / "human-evidence-pipeline-r195.md"
    return [
        "python3",
        rel(R195_SCRIPT) or str(R195_SCRIPT),
        "--r142-responses",
        rel(args.c5_responses) or str(args.c5_responses),
        "--r142-bundle",
        rel(args.r142_bundle) or str(args.r142_bundle),
        "--r142-answer-key",
        rel(args.r142_answer_key) or str(args.r142_answer_key),
        "--r142-assignments",
        rel(args.r142_assignments) or str(args.r142_assignments),
        "--r124-labeler-1",
        rel(args.r124_labeler_1) or str(args.r124_labeler_1),
        "--r124-labeler-2",
        rel(args.r124_labeler_2) or str(args.r124_labeler_2),
        "--r190-labeler-1",
        rel(args.r190_labeler_1) or str(args.r190_labeler_1),
        "--r190-labeler-2",
        rel(args.r190_labeler_2) or str(args.r190_labeler_2),
        "--r203-labeler-1",
        rel(args.r203_labeler_1) or str(args.r203_labeler_1),
        "--r203-labeler-2",
        rel(args.r203_labeler_2) or str(args.r203_labeler_2),
        "--scored-dir",
        rel(scored_dir) or str(scored_dir),
        "--out-json",
        rel(out_json) or str(out_json),
        "--out-md",
        rel(out_md) or str(out_md),
    ]


def command_string(cmd: list[str]) -> str:
    return " ".join(shlex.quote(part) for part in cmd)


def overall_status(c5: dict[str, Any], labels: dict[str, Any], safety: dict[str, Any]) -> str:
    any_present = c5["present"] or any(item["present"] for item in labels["files"].values())
    if not safety["all_inputs_safe"]:
        return "unsafe_return_inputs"
    if not any_present:
        return "awaiting_private_returns"
    if c5["status"] == "blank_template" or any(item["status"] == "blank_template" for item in labels["files"].values()):
        return "returns_not_ready_blank_or_partial"
    if c5["errors"] or any(item["errors"] for item in labels["files"].values() if item["present"]):
        return "returns_not_ready_invalid"
    if c5["ready_for_r195"] and labels["groups"]["r124"]["ready_for_r195"]:
        if labels["groups"]["r190"]["ready_for_r195"] and labels["groups"]["r203"]["ready_for_r195"]:
            return "ready_for_r195_full_paper_scale_scoring"
        return "ready_for_r195_c5_c6_scoring"
    return "returns_not_ready_missing_required_groups"


def build_payload(args: argparse.Namespace) -> dict[str, Any]:
    paths = {
        "c5_responses": args.c5_responses,
        "r124_labeler_1": args.r124_labeler_1,
        "r124_labeler_2": args.r124_labeler_2,
        "r190_labeler_1": args.r190_labeler_1,
        "r190_labeler_2": args.r190_labeler_2,
        "r203_labeler_1": args.r203_labeler_1,
        "r203_labeler_2": args.r203_labeler_2,
    }
    c5 = validate_c5(args.c5_responses, args.r142_assignments)
    labels = validate_labels(paths)
    all_marker_hits = {
        name: marker_hits(path)
        for name, path in paths.items()
        if path.exists() and marker_hits(path)
    }
    safety = {
        "forbidden_markers": FORBIDDEN_RETURN_MARKERS,
        "marker_hits_by_input": all_marker_hits,
        "all_inputs_safe": not bool(all_marker_hits),
        "r259_synthetic_marker_regression": synthetic_marker_regression(args.r259_synthetic_c5),
    }
    status = overall_status(c5, labels, safety)
    r195_cmd = build_r195_command(args)
    privacy = privacy_guard(paths)
    checklist = validate_return_checklist(args.return_checklist, args.r258_summary)
    checks = {
        "return_checklist_passed": checklist["passed"],
        "r259_synthetic_marker_regression_passed": safety["r259_synthetic_marker_regression"]["passed"],
        "privacy_guard_passed": privacy["passed"],
        "no_public_outcome_evidence_added": True,
        "claim_gate_stays_false": True,
    }
    return {
        "schema_version": 1,
        "run_id": "R264",
        "status": status,
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "input_paths": {name: file_info(path) for name, path in paths.items()},
        "handoff_contract": checklist,
        "c5_response_preflight": c5,
        "c6_label_preflight": labels,
        "safety": safety,
        "privacy_guard": privacy,
        "r195_command": {
            "argv": r195_cmd,
            "shell": command_string(r195_cmd),
            "write_outputs_under": rel(args.r195_scored_dir),
        },
        "checks": checks,
        "claim_gate": {
            "c5_supported": False,
            "c6_adequacy_supported": False,
            "canonicalization_quality_supported": False,
            "long_tail_promotion_review_supported": False,
            "weak_accept_supported": False,
            "requires_real_human_returns": True,
            "requires_r195_scoring": status.startswith("ready_for_r195"),
        },
        "claim_boundary": (
            "R264 validates whether returned human-study CSVs are complete and safe to pass to R195. "
            "It does not score responses, infer labels, adjudicate disagreements, or upgrade C5/C6."
        ),
        "provenance": {
            "repo_commit": git_text(["rev-parse", "HEAD"]),
            "repo_dirty": bool(git_text(["status", "--short"])),
            "script": rel(Path(__file__).resolve()),
            "script_sha256": sha256_file(Path(__file__).resolve()),
        },
    }


def write_markdown(path: Path, payload: dict[str, Any]) -> None:
    c5 = payload["c5_response_preflight"]
    groups = payload["c6_label_preflight"]["groups"]
    gate = payload["claim_gate"]
    lines = [
        "# R264 Human Return Intake Preflight",
        "",
        f"Status: `{payload['status']}`",
        "",
        "## What This Checks",
        "",
        "- R258 return checklist shape and row counts.",
        "- C5 paper-scale response row coverage against the R249 assignment file.",
        "- R124/R190/R203 paired labeler row counts and nonblank label coverage.",
        "- Known synthetic-return markers from R259/R244 before R195 scoring.",
        "- Ignore rules for private returned CSVs and R195 inbox/scored outputs.",
        "",
        "## C5",
        "",
        f"- Status: `{c5['status']}`.",
        f"- Ready for R195: `{c5['ready_for_r195']}`.",
        f"- Rows: `{c5.get('row_count', 0)}` / `{c5.get('expected_row_count', EXPECTED_C5_ROWS)}`.",
        f"- Placeholder rows: `{c5.get('placeholder_rows', 0)}`.",
        f"- Errors: `{len(c5.get('errors', []))}`.",
        "",
        "## C6 Groups",
        "",
        "| group | status | ready | present files |",
        "|---|---|---:|---|",
    ]
    for name, group in groups.items():
        lines.append(
            f"| `{name}` | `{group['status']}` | `{group['ready_for_r195']}` | "
            f"`{', '.join(group['present'])}` |"
        )
    lines.extend(
        [
            "",
            "## Safety",
            "",
            f"- Input marker safety: `{payload['safety']['all_inputs_safe']}`.",
            f"- R259 synthetic-marker regression: `{payload['safety']['r259_synthetic_marker_regression']['passed']}`.",
            f"- Privacy guard: `{payload['privacy_guard']['passed']}`.",
            "",
            "## R195 Command Template",
            "",
            "```bash",
            payload["r195_command"]["shell"],
            "```",
            "",
            "## Claim Gates",
            "",
            f"- C5 supported: `{gate['c5_supported']}`.",
            f"- C6 adequacy supported: `{gate['c6_adequacy_supported']}`.",
            f"- Weak accept supported: `{gate['weak_accept_supported']}`.",
            "",
            "## Boundary",
            "",
            payload["claim_boundary"],
            "",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def write_command(path: Path, payload: dict[str, Any]) -> None:
    lines = [
        "# R264 R195 command template",
        "# Fill the private input files first; this template is not evidence by itself.",
        payload["r195_command"]["shell"],
        "",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def run(args: argparse.Namespace) -> dict[str, Any]:
    args.out_dir.mkdir(parents=True, exist_ok=True)
    payload = build_payload(args)
    out_json = args.out_dir / "human-return-intake-r264.json"
    out_md = args.out_dir / "human-return-intake-r264.md"
    out_cmd = args.out_dir / "r195-command-template-r264.txt"
    write_json(out_json, payload)
    write_markdown(out_md, payload)
    write_command(out_cmd, payload)
    print(json.dumps({"status": payload["status"], "claim_gate": payload["claim_gate"]}, indent=2, sort_keys=True))
    return payload


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--return-checklist", type=Path, default=DEFAULT_RETURN_CHECKLIST)
    parser.add_argument("--r258-summary", type=Path, default=DEFAULT_R258_SUMMARY)
    parser.add_argument("--r259-synthetic-c5", type=Path, default=DEFAULT_R259_SYNTHETIC_C5)
    parser.add_argument("--c5-responses", type=Path, default=DEFAULT_C5_RESPONSES)
    parser.add_argument("--r124-labeler-1", type=Path, default=DEFAULT_R124_LABELER_1)
    parser.add_argument("--r124-labeler-2", type=Path, default=DEFAULT_R124_LABELER_2)
    parser.add_argument("--r190-labeler-1", type=Path, default=DEFAULT_R190_LABELER_1)
    parser.add_argument("--r190-labeler-2", type=Path, default=DEFAULT_R190_LABELER_2)
    parser.add_argument("--r203-labeler-1", type=Path, default=DEFAULT_R203_LABELER_1)
    parser.add_argument("--r203-labeler-2", type=Path, default=DEFAULT_R203_LABELER_2)
    parser.add_argument("--r142-bundle", type=Path, default=R142_BUNDLE)
    parser.add_argument("--r142-answer-key", type=Path, default=R142_ANSWER_KEY)
    parser.add_argument("--r142-assignments", type=Path, default=R249_ASSIGNMENTS)
    parser.add_argument("--r195-scored-dir", type=Path, default=DEFAULT_PRIVATE_ROOT / "r195-scored")
    return parser


if __name__ == "__main__":
    run(build_parser().parse_args())
