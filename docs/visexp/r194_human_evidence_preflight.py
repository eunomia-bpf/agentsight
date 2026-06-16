#!/usr/bin/env python3
"""R194 preflight gate for human-evidence collection.

This script validates that the R193 collection package is internally
consistent, still contains no outcome evidence, and points to the existing
scorers that must be rerun after real labels/responses are collected.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[1]
DEFAULT_R193_MANIFEST = SCRIPT_DIR / "out" / "human-evidence-r193" / "manifest.json"
DEFAULT_R187_MANIFEST = SCRIPT_DIR / "out" / "user-task-pilot-r142" / "launch" / "manifest.json"
DEFAULT_R124_SCORE = SCRIPT_DIR / "out" / "tag-adequacy-results-r124.json"
DEFAULT_R190_SCORE = SCRIPT_DIR / "out" / "tag-consolidation-audit-r190" / "merge-risk-audit-results-r190.json"
DEFAULT_R203_SCORE = SCRIPT_DIR / "out" / "long-tail-promotion-r203" / "long-tail-promotion-r203.json"
DEFAULT_R142_SCORE = SCRIPT_DIR / "out" / "user-task-results.json"
DEFAULT_OUT_JSON = SCRIPT_DIR / "out" / "human-evidence-preflight-r194.json"
DEFAULT_OUT_MD = SCRIPT_DIR / "out" / "human-evidence-preflight-r194.md"

R124_FIELDS = [
    "row_id",
    "fragment_index",
    "fragment_level",
    "redacted_preview",
    "candidate_tag",
    "rubric",
    "label",
    "notes",
]
R190_FIELDS = [
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
R203_FIELDS = [
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


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT.resolve()))
    except Exception:
        return str(path)


def resolve_repo_path(value: str) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    return REPO_ROOT / path


def sha256_file(path: Path) -> str:
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


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv(path: Path) -> tuple[list[dict[str, str]], list[str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        return list(reader), list(reader.fieldnames or [])


def pct(part: int, whole: int) -> float | None:
    if not whole:
        return None
    return round(100.0 * part / whole, 3)


def check_file(path: Path, expected_sha256: str | None = None) -> dict[str, Any]:
    exists = path.exists()
    actual = sha256_file(path) if exists else None
    return {
        "path": rel(path),
        "exists": exists,
        "sha256": actual,
        "expected_sha256": expected_sha256,
        "sha256_match": bool(exists and (expected_sha256 is None or actual == expected_sha256)),
    }


def csv_blank_summary(
    path: Path,
    expected_fields: list[str],
    blank_fields: tuple[str, ...],
) -> dict[str, Any]:
    rows, fields = read_csv(path)
    nonblank_cells = 0
    rows_with_nonblank = 0
    for row in rows:
        row_nonblank = False
        for field in blank_fields:
            if (row.get(field) or "").strip():
                nonblank_cells += 1
                row_nonblank = True
        if row_nonblank:
            rows_with_nonblank += 1
    return {
        "path": rel(path),
        "row_count": len(rows),
        "fields": fields,
        "fields_match": fields == expected_fields,
        "blank_fields": list(blank_fields),
        "nonblank_label_cells": nonblank_cells,
        "rows_with_nonblank_labels": rows_with_nonblank,
        "blank": nonblank_cells == 0,
    }


def response_template_summary(path: Path) -> dict[str, Any]:
    rows, fields = read_csv(path)
    real_rows = 0
    for row in rows:
        if (
            (row.get("response_json") or "").strip() not in {"", "{}"}
            or (row.get("task_time_seconds") or "").strip()
            or (row.get("confidence") or "").strip()
            or (row.get("notes") or "").strip()
        ):
            real_rows += 1
    return {
        "path": rel(path),
        "row_count": len(rows),
        "fields": fields,
        "real_response_like_rows": real_rows,
        "blank": real_rows == 0,
    }


def package_checks(manifest: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    files: list[dict[str, Any]] = []
    sheet_summaries: dict[str, Any] = {}

    for section in ("r124", "r190", "r203"):
        for item in ("source",):
            payload = manifest[section].get(item, {})
            files.append(check_file(resolve_repo_path(payload["path"]), payload.get("sha256")))
        for labeler_name, payload in manifest[section]["outputs"].items():
            path = resolve_repo_path(payload["path"])
            files.append(check_file(path, payload.get("sha256")))
            if section == "r124":
                sheet_summaries[f"r124_{labeler_name}"] = csv_blank_summary(
                    path,
                    R124_FIELDS,
                    ("label", "notes"),
                )
            elif section == "r190":
                sheet_summaries[f"r190_{labeler_name}"] = csv_blank_summary(
                    path,
                    R190_FIELDS,
                    ("audit_label", "audit_notes"),
                )
            else:
                sheet_summaries[f"r203_{labeler_name}"] = csv_blank_summary(
                    path,
                    R203_FIELDS,
                    ("promotion_label", "promotion_notes"),
                )

    for section, key in (("r142", "manifest"), ("r142", "response_template")):
        payload = manifest[section][key]
        path = resolve_repo_path(payload["path"])
        files.append(check_file(path, payload.get("sha256")))
        if key == "response_template":
            sheet_summaries["r142_response_template"] = response_template_summary(path)

    return files, sheet_summaries


def score_summaries(args: argparse.Namespace) -> dict[str, Any]:
    r124 = read_json(args.r124_score)
    r190 = read_json(args.r190_score)
    r203 = read_json(args.r203_score)
    r142 = read_json(args.r142_score)
    r187 = read_json(args.r187_manifest)
    return {
        "r124": {
            "path": rel(args.r124_score),
            "status": r124.get("status"),
            "final_label_count": r124.get("summary", {}).get("final_label_count"),
            "candidate_tag_count": r124.get("summary", {}).get("candidate_tag_count"),
            "adequacy_supported": r124.get("claim_gate", {}).get("adequacy_supported"),
        },
        "r190": {
            "path": rel(args.r190_score),
            "status": r190.get("status"),
            "final_label_count": r190.get("summary", {}).get("final_label_count"),
            "canonicalization_quality_supported": r190.get("claim_gate", {}).get("canonicalization_quality_supported"),
        },
        "r203": {
            "path": rel(args.r203_score),
            "status": r203.get("status"),
            "final_label_count": r203.get("summary", {}).get("final_label_count"),
            "long_tail_promotion_review_supported": r203.get("claim_gate", {}).get(
                "long_tail_promotion_review_supported"
            ),
            "canonical_map_updated": r203.get("claim_gate", {}).get("canonical_map_updated"),
        },
        "r142": {
            "path": rel(args.r142_score),
            "status": r142.get("status"),
            "participant_count": r142.get("participant_count"),
            "response_count": r142.get("response_count"),
            "c5_supported": r142.get("claim_analysis", {}).get("claim_gate", {}).get("c5_supported"),
        },
        "r187": {
            "path": rel(args.r187_manifest),
            "status": r187.get("status"),
            "launch_ready": r187.get("claim_gate", {}).get("launch_ready"),
            "c5_supported": r187.get("claim_gate", {}).get("c5_supported"),
            "real_response_count": r187.get("real_response_count"),
            "leak_scan": r187.get("leak_scan", {}),
        },
    }


def gate_status(
    manifest: dict[str, Any],
    files: list[dict[str, Any]],
    sheets: dict[str, Any],
    scores: dict[str, Any],
) -> dict[str, Any]:
    files_ok = all(row["exists"] and row["sha256_match"] for row in files)
    r124_blank = all(
        sheets[key]["blank"] and sheets[key]["fields_match"] and sheets[key]["row_count"] == 300
        for key in ("r124_labeler_1", "r124_labeler_2")
    )
    r190_blank = all(
        sheets[key]["blank"] and sheets[key]["fields_match"] and sheets[key]["row_count"] == 160
        for key in ("r190_labeler_1", "r190_labeler_2")
    )
    r203_blank = all(
        sheets[key]["blank"] and sheets[key]["fields_match"] and sheets[key]["row_count"] == 41
        for key in ("r203_labeler_1", "r203_labeler_2")
    )
    r142_blank = sheets["r142_response_template"]["blank"] and sheets["r142_response_template"]["row_count"] == 70
    scores_empty = (
        scores["r124"]["status"] == "human_labels_empty"
        and scores["r124"]["final_label_count"] == 0
        and scores["r190"]["status"] == "human_labels_empty"
        and scores["r190"]["final_label_count"] == 0
        and scores["r203"]["status"] == "human_labels_empty"
        and scores["r203"]["final_label_count"] == 0
        and scores["r142"]["status"] == "participant_results_empty"
        and scores["r142"]["response_count"] == 0
        and scores["r187"]["real_response_count"] == 0
    )
    support_false = (
        manifest.get("claim_gate", {}).get("c5_supported") is False
        and manifest.get("claim_gate", {}).get("c6_adequacy_supported") is False
        and manifest.get("claim_gate", {}).get("canonicalization_quality_supported") is False
        and manifest.get("claim_gate", {}).get("long_tail_promotion_review_supported") is False
        and manifest.get("claim_gate", {}).get("canonical_map_updated") is False
        and scores["r124"]["adequacy_supported"] is False
        and scores["r190"]["canonicalization_quality_supported"] is False
        and scores["r203"]["long_tail_promotion_review_supported"] is False
        and scores["r203"]["canonical_map_updated"] is False
        and scores["r142"]["c5_supported"] is False
    )
    ready = files_ok and r124_blank and r190_blank and r203_blank and r142_blank and scores_empty and support_false
    return {
        "status": "ready_for_human_collection_no_outcomes" if ready else "preflight_failed_or_outcome_present",
        "files_ok": files_ok,
        "r124_blank": r124_blank,
        "r190_blank": r190_blank,
        "r203_blank": r203_blank,
        "r142_response_template_blank": r142_blank,
        "scores_empty": scores_empty,
        "support_gates_false": support_false,
        "ready_for_collection": ready,
        "c5_supported": False,
        "c6_adequacy_supported": False,
        "canonicalization_quality_supported": False,
        "long_tail_promotion_review_supported": False,
        "canonical_map_updated": False,
        "requires_real_human_data": True,
    }


def write_markdown(path: Path, result: dict[str, Any]) -> None:
    gate = result["claim_gate"]
    lines = [
        "# R194 Human Evidence Preflight",
        "",
        f"Status: `{result['status']}`",
        "",
        "## Gate",
        "",
        f"- Files OK: `{gate['files_ok']}`",
        f"- R124 sheets blank: `{gate['r124_blank']}`",
        f"- R190 sheets blank: `{gate['r190_blank']}`",
        f"- R203 sheets blank: `{gate['r203_blank']}`",
        f"- R142 response template blank: `{gate['r142_response_template_blank']}`",
        f"- Existing scorers empty: `{gate['scores_empty']}`",
        f"- Support gates false: `{gate['support_gates_false']}`",
        "",
        "## Current Evidence Counts",
        "",
        f"- R124 final labels: {result['scores']['r124']['final_label_count']}",
        f"- R190 final labels: {result['scores']['r190']['final_label_count']}",
        f"- R203 final labels: {result['scores']['r203']['final_label_count']}",
        f"- R142 real responses: {result['scores']['r142']['response_count']}",
        "",
        "## Next Commands",
        "",
        "After real R124 labels are collected:",
        "",
        "```bash",
        "python3 docs/visexp/r124_join_blinded_labels.py --labeler-1 <r124-labeler-1.csv> --labeler-2 <r124-labeler-2.csv> --adjudication <r124-adjudication.csv>",
        "python3 docs/visexp/score_tag_adequacy.py --labels docs/visexp/out/tag-adequacy-label-packet-r124-joined.csv",
        "```",
        "",
        "After real R142 pilot responses are collected:",
        "",
        "```bash",
        "python3 docs/visexp/score_user_task_results.py --responses <completed-pilot-response.csv> --bundle docs/visexp/out/user-task-benchmark.json --answer-key docs/visexp/out/user-task-answer-key.csv --assignments docs/visexp/out/user-task-assignments.csv --out docs/visexp/out/user-task-pilot-r142",
        "```",
        "",
        "After real R190 merge labels are collected:",
        "",
        "```bash",
        "python3 docs/visexp/r190_score_merge_audit.py --labeler-1 <r190-labeler-1.csv> --labeler-2 <r190-labeler-2.csv> --adjudication <r190-adjudication.csv>",
        "```",
        "",
        "After real R203 promotion labels are collected:",
        "",
        "```bash",
        "python3 docs/visexp/r203_long_tail_promotion_gate.py --labeler-1 <r203-labeler-1.csv> --labeler-2 <r203-labeler-2.csv> --adjudication <r203-adjudication.csv>",
        "```",
        "",
        "Claim impact: R194 is a preflight gate only. It does not support C5, C6, canonicalization quality, or long-tail promotion decisions.",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run(args: argparse.Namespace) -> dict[str, Any]:
    manifest = read_json(args.r193_manifest)
    files, sheets = package_checks(manifest)
    scores = score_summaries(args)
    gate = gate_status(manifest, files, sheets, scores)
    result = {
        "schema_version": 1,
        "run_id": "R194",
        "status": gate["status"],
        "generated_at": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),
        "input": {
            "r193_manifest": rel(args.r193_manifest),
            "r193_manifest_sha256": sha256_file(args.r193_manifest),
        },
        "files": files,
        "sheets": sheets,
        "scores": scores,
        "claim_gate": gate,
        "claim_boundary": (
            "R194 validates collection readiness and empty-outcome boundaries only; "
            "it cannot support C5, C6, canonicalization quality, or long-tail promotion decisions without real human data."
        ),
        "artifacts": {
            "summary_json": rel(args.out_json),
            "summary_md": rel(args.out_md),
        },
        "provenance": {
            "repo_commit": git(["rev-parse", "HEAD"]),
            "repo_dirty": bool(git(["status", "--short"])),
            "script_sha256": sha256_file(Path(__file__).resolve()),
        },
    }
    args.out_json.parent.mkdir(parents=True, exist_ok=True)
    args.out_json.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_markdown(args.out_md, result)
    print(json.dumps({"status": result["status"], "ready": gate["ready_for_collection"]}, indent=2))
    return result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--r193-manifest", type=Path, default=DEFAULT_R193_MANIFEST)
    parser.add_argument("--r187-manifest", type=Path, default=DEFAULT_R187_MANIFEST)
    parser.add_argument("--r124-score", type=Path, default=DEFAULT_R124_SCORE)
    parser.add_argument("--r190-score", type=Path, default=DEFAULT_R190_SCORE)
    parser.add_argument("--r203-score", type=Path, default=DEFAULT_R203_SCORE)
    parser.add_argument("--r142-score", type=Path, default=DEFAULT_R142_SCORE)
    parser.add_argument("--out-json", type=Path, default=DEFAULT_OUT_JSON)
    parser.add_argument("--out-md", type=Path, default=DEFAULT_OUT_MD)
    return parser


if __name__ == "__main__":
    run(build_parser().parse_args())
