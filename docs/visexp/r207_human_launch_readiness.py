#!/usr/bin/env python3
"""R207: audit whether human-evidence materials are launch-ready.

This audit is intentionally not outcome evidence. It reads the existing R187
pilot launch package, R193 human-evidence package, and R195 ingestion defaults,
then checks whether collection files are sendable and whether returned files
have unambiguous inbox names. It does not read raw agent traces and does not
fill labels or participant responses.
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
OUT_DIR = SCRIPT_DIR / "out"
DEFAULT_R193_DIR = OUT_DIR / "human-evidence-r193"
DEFAULT_R187_DIR = OUT_DIR / "user-task-pilot-r142" / "launch"
DEFAULT_R195_JSON = OUT_DIR / "human-evidence-pipeline-r195.json"
DEFAULT_OUT_DIR = OUT_DIR / "human-evidence-launch-r207"

EXPECTED_R124_FIELDS = [
    "row_id",
    "fragment_index",
    "fragment_level",
    "redacted_preview",
    "candidate_tag",
    "rubric",
    "label",
    "notes",
]
EXPECTED_R190_FIELDS = [
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
EXPECTED_R203_FIELDS = [
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
EXPECTED_R142_RESPONSE_FIELDS = [
    "participant_id",
    "order_index",
    "packet_id",
    "task_id",
    "condition",
    "response_json",
    "task_time_seconds",
    "confidence",
    "notes",
]

RETURN_FILE_METADATA = {
    "r142_responses": {
        "group": "r142",
        "human_file": "completed copy of user-task-response-template-r142-pilot.csv",
        "claim": "C5 developer utility",
        "counts_as_evidence_when": "real participant responses pass the R142/R195 response contract",
    },
    "r124_labeler_1": {
        "group": "r124",
        "human_file": "completed r124-tag-adequacy-labeler-1.csv",
        "claim": "C6 tag adequacy",
        "counts_as_evidence_when": "paired labeler sheets and adjudication pass R124 scoring",
    },
    "r124_labeler_2": {
        "group": "r124",
        "human_file": "completed r124-tag-adequacy-labeler-2.csv",
        "claim": "C6 tag adequacy",
        "counts_as_evidence_when": "paired labeler sheets and adjudication pass R124 scoring",
    },
    "r190_labeler_1": {
        "group": "r190",
        "human_file": "completed r190-merge-risk-labeler-1.csv",
        "claim": "canonical merge quality",
        "counts_as_evidence_when": "paired merge-risk labels pass R190 scoring",
    },
    "r190_labeler_2": {
        "group": "r190",
        "human_file": "completed r190-merge-risk-labeler-2.csv",
        "claim": "canonical merge quality",
        "counts_as_evidence_when": "paired merge-risk labels pass R190 scoring",
    },
    "r203_labeler_1": {
        "group": "r203",
        "human_file": "completed r203-long-tail-promotion-labeler-1.csv",
        "claim": "long-tail promotion review",
        "counts_as_evidence_when": "paired promotion labels pass R203 scoring",
    },
    "r203_labeler_2": {
        "group": "r203",
        "human_file": "completed r203-long-tail-promotion-labeler-2.csv",
        "claim": "long-tail promotion review",
        "counts_as_evidence_when": "paired promotion labels pass R203 scoring",
    },
}

RETURN_FILE_ORDER = [
    "r142_responses",
    "r124_labeler_1",
    "r124_labeler_2",
    "r190_labeler_1",
    "r190_labeler_2",
    "r203_labeler_1",
    "r203_labeler_2",
]


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT.resolve()))
    except Exception:
        return str(path)


def repo_path(value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else REPO_ROOT / path


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


def sha256_file(path: Path) -> str | None:
    if not path.exists():
        return None
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


def read_csv(path: Path) -> tuple[list[dict[str, str]], list[str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        return list(reader), list(reader.fieldnames or [])


def count_nonblank(rows: list[dict[str, str]], fields: list[str]) -> tuple[int, int]:
    cells = 0
    rows_with_values = 0
    for row in rows:
        row_has_value = False
        for field in fields:
            if (row.get(field) or "").strip():
                cells += 1
                row_has_value = True
        if row_has_value:
            rows_with_values += 1
    return cells, rows_with_values


def csv_audit(
    path: Path,
    expected_fields: list[str],
    blank_fields: list[str],
    allowed_values: dict[str, set[str]] | None = None,
) -> dict[str, Any]:
    rows, fields = read_csv(path)
    nonblank_cells, rows_with_values = count_nonblank(rows, blank_fields)
    invalid_values: list[dict[str, str]] = []
    for idx, row in enumerate(rows):
        for field, allowed in (allowed_values or {}).items():
            value = (row.get(field) or "").strip()
            if value and value not in allowed:
                invalid_values.append({"row": str(idx), "field": field, "value": value})
    return {
        "path": rel(path),
        "exists": path.exists(),
        "sha256": sha256_file(path),
        "row_count": len(rows),
        "fields": fields,
        "fields_match": fields == expected_fields,
        "blank_fields": blank_fields,
        "nonblank_label_cells": nonblank_cells,
        "rows_with_nonblank_labels": rows_with_values,
        "blank": nonblank_cells == 0,
        "invalid_values": invalid_values[:10],
        "invalid_value_count": len(invalid_values),
    }


def response_template_audit(path: Path) -> dict[str, Any]:
    rows, fields = read_csv(path)
    real_like = 0
    participant_ids = set()
    task_ids = set()
    conditions = set()
    for row in rows:
        participant_ids.add(row.get("participant_id", ""))
        task_ids.add(row.get("task_id", ""))
        conditions.add(row.get("condition", ""))
        if (
            (row.get("response_json") or "").strip() not in {"", "{}"}
            or (row.get("task_time_seconds") or "").strip()
            or (row.get("confidence") or "").strip()
            or (row.get("notes") or "").strip()
        ):
            real_like += 1
    return {
        "path": rel(path),
        "exists": path.exists(),
        "sha256": sha256_file(path),
        "row_count": len(rows),
        "fields": fields,
        "fields_match": fields == EXPECTED_R142_RESPONSE_FIELDS,
        "participant_ids": sorted(participant_ids),
        "participant_count": len(participant_ids),
        "task_count": len(task_ids),
        "conditions": sorted(conditions),
        "real_response_like_rows": real_like,
        "blank": real_like == 0,
    }


def file_info(path: Path, expected_sha: str | None = None) -> dict[str, Any]:
    actual = sha256_file(path)
    return {
        "path": rel(path),
        "exists": path.exists(),
        "sha256": actual,
        "expected_sha256": expected_sha,
        "sha256_match": bool(path.exists() and (expected_sha is None or actual == expected_sha)),
    }


def readme_check(path: Path, required_phrases: list[str]) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8") if path.exists() else ""
    missing = [phrase for phrase in required_phrases if phrase not in text]
    return {
        "path": rel(path),
        "exists": path.exists(),
        "missing_required_phrases": missing,
        "ok": path.exists() and not missing,
    }


def participant_packet_audit(launch_dir: Path, manifest: dict[str, Any]) -> dict[str, Any]:
    participants_dir = launch_dir / "participants"
    participant_ids = manifest.get("participant_ids") or []
    packets = []
    forbidden_keys = {
        "answer_key",
        "answer_json",
        "answer_format",
        "oracle",
        "oracle_sources",
        "scoring",
        "projected_stack_hash",
    }

    def scan(value: Any, path: str = "$") -> list[str]:
        hits: list[str] = []
        if isinstance(value, dict):
            for key, child in value.items():
                child_path = f"{path}.{key}"
                if key in forbidden_keys:
                    hits.append(child_path)
                hits.extend(scan(child, child_path))
        elif isinstance(value, list):
            for idx, child in enumerate(value):
                hits.extend(scan(child, f"{path}[{idx}]"))
        return hits

    forbidden_hits: list[str] = []
    for participant_id in participant_ids:
        json_path = participants_dir / f"{participant_id}.json"
        md_path = participants_dir / f"{participant_id}.md"
        packet = read_json(json_path) if json_path.exists() else {}
        hits = scan(packet)
        forbidden_hits.extend([f"{participant_id}:{hit}" for hit in hits])
        packets.append(
            {
                "participant_id": participant_id,
                "json": file_info(json_path),
                "md": file_info(md_path),
                "assignment_count": packet.get("assignment_count"),
                "task_count": len(packet.get("tasks") or []),
                "forbidden_key_hits": hits[:10],
            }
        )
    return {
        "participant_ids": participant_ids,
        "packet_count": len(packets),
        "packets": packets,
        "forbidden_key_hit_count": len(forbidden_hits),
        "forbidden_key_hits": forbidden_hits[:10],
        "ready": len(packets) == len(participant_ids) and len(forbidden_hits) == 0,
    }


def build_return_plan(required_inputs: dict[str, Any]) -> list[dict[str, str]]:
    plan: list[dict[str, str]] = []
    missing = [key for key in RETURN_FILE_ORDER if key not in required_inputs]
    if missing:
        raise KeyError(f"R195 required_inputs missing keys for R207 return plan: {missing}")

    for key in RETURN_FILE_ORDER:
        input_record = required_inputs[key]
        input_path = input_record.get("path")
        if not input_path:
            raise KeyError(f"R195 required_inputs.{key}.path is missing")
        metadata = RETURN_FILE_METADATA[key]
        plan.append(
            {
                "r195_input_key": key,
                "group": metadata["group"],
                "human_file": metadata["human_file"],
                "r195_inbox_path": input_path,
                "r195_inbox_name": Path(input_path).name,
                "claim": metadata["claim"],
                "counts_as_evidence_when": metadata["counts_as_evidence_when"],
            }
        )
    return plan


def build_payload(args: argparse.Namespace) -> dict[str, Any]:
    r193_manifest_path = args.r193_dir / "manifest.json"
    r187_manifest_path = args.r187_dir / "manifest.json"
    r193 = read_json(r193_manifest_path)
    r187 = read_json(r187_manifest_path)
    r195 = read_json(args.r195_json)
    r195_required_inputs = (r195.get("input_contract") or {}).get("required_inputs") or {}

    r124_sheets = {
        name: csv_audit(
            repo_path(payload["path"]),
            EXPECTED_R124_FIELDS,
            ["label", "notes"],
            {"label": {"adequate", "generic_noisy", "misleading"}},
        )
        for name, payload in r193["r124"]["outputs"].items()
    }
    r190_sheets = {
        name: csv_audit(
            repo_path(payload["path"]),
            EXPECTED_R190_FIELDS,
            ["audit_label", "audit_notes"],
            {"audit_label": {"acceptable", "overmerge", "undermerge", "unclear"}},
        )
        for name, payload in r193["r190"]["outputs"].items()
    }
    r203_sheets = {
        name: csv_audit(
            repo_path(payload["path"]),
            EXPECTED_R203_FIELDS,
            ["promotion_label", "promotion_notes"],
            {"promotion_label": {"promote", "keep_raw", "reject", "split", "unclear"}},
        )
        for name, payload in r193["r203"]["outputs"].items()
    }

    response_template = response_template_audit(
        repo_path(r193["r142"]["response_template"]["path"])
    )
    participant_packets = participant_packet_audit(args.r187_dir, r187)
    readmes = {
        "r193": readme_check(args.r193_dir / "README.md", ["blank collection materials", "does not support C5 or C6"]),
        "r142": readme_check(args.r193_dir / "r142" / "README.md", ["Do not distribute answer keys"]),
        "r124": readme_check(args.r193_dir / "r124" / "README.md", ["two independent labelers", "Allowed labels"]),
        "r190": readme_check(args.r193_dir / "r190" / "README.md", ["two independent labelers", "Allowed labels"]),
        "r203": readme_check(args.r193_dir / "r203" / "README.md", ["two independent labelers", "Accepted promotion labels still do not update"]),
    }
    source_files = {
        "r193_manifest": file_info(r193_manifest_path),
        "r187_manifest": file_info(r187_manifest_path, r193["r142"]["manifest"].get("sha256")),
        "r195_pipeline": file_info(args.r195_json),
        "r124_source": file_info(repo_path(r193["r124"]["source"]["path"]), r193["r124"]["source"].get("sha256")),
        "r190_source": file_info(repo_path(r193["r190"]["source"]["path"]), r193["r190"]["source"].get("sha256")),
        "r203_source": file_info(repo_path(r193["r203"]["source"]["path"]), r193["r203"]["source"].get("sha256")),
        "r142_response_template": file_info(
            repo_path(r193["r142"]["response_template"]["path"]),
            r193["r142"]["response_template"].get("sha256"),
        ),
    }

    sheet_groups = {
        "r124": r124_sheets,
        "r190": r190_sheets,
        "r203": r203_sheets,
    }
    all_sheet_audits = [sheet for group in sheet_groups.values() for sheet in group.values()]
    sheet_rows_ok = (
        all(sheet["exists"] and sheet["fields_match"] and sheet["blank"] for sheet in all_sheet_audits)
        and r124_sheets["labeler_1"]["row_count"] == 300
        and r124_sheets["labeler_2"]["row_count"] == 300
        and r190_sheets["labeler_1"]["row_count"] == 160
        and r190_sheets["labeler_2"]["row_count"] == 160
        and r203_sheets["labeler_1"]["row_count"] == 41
        and r203_sheets["labeler_2"]["row_count"] == 41
    )
    files_ok = all(info["exists"] and info["sha256_match"] for info in source_files.values())
    readmes_ok = all(item["ok"] for item in readmes.values())
    response_template_ok = response_template["fields_match"] and response_template["blank"] and response_template["row_count"] == 70
    r195_status_ok = r195.get("status") == "awaiting_human_inputs"
    launch_ready = bool(
        files_ok
        and sheet_rows_ok
        and response_template_ok
        and participant_packets["ready"]
        and readmes_ok
        and r187.get("real_response_count") == 0
        and not (r187.get("claim_gate") or {}).get("c5_supported")
        and r195_status_ok
    )

    claim_gate = {
        "launch_readiness_supported": launch_ready,
        "c5_supported": False,
        "c6_adequacy_supported": False,
        "canonicalization_quality_supported": False,
        "long_tail_promotion_review_supported": False,
        "canonical_map_updated": False,
        "requires_real_participants": True,
        "requires_real_human_labels": True,
        "subagent_or_llm_outputs_count_as_evidence": False,
    }
    status = "launch_ready_no_outcomes" if launch_ready else "launch_readiness_failed"

    return {
        "run_id": "R207",
        "schema_version": 1,
        "generated_at": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),
        "status": status,
        "claim": "C5/C6 logistics only",
        "claim_boundary": (
            "R207 audits whether human-evidence collection files are sendable and "
            "whether returned files have an unambiguous R195 inbox mapping. It does "
            "not collect, infer, or score participant responses or human labels."
        ),
        "source_files": source_files,
        "launch_units": {
            "r142_participants": participant_packets,
            "r142_response_template": response_template,
            "r124_sheets": r124_sheets,
            "r190_sheets": r190_sheets,
            "r203_sheets": r203_sheets,
            "readmes": readmes,
        },
        "return_file_plan": build_return_plan(r195_required_inputs),
        "r195_required_input_keys": sorted(r195_required_inputs),
        "r195_status": {
            "path": rel(args.r195_json),
            "status": r195.get("status"),
            "operations": r195.get("operations", []),
            "claim_gate": r195.get("claim_gate", {}),
        },
        "checks": {
            "source_files_ok": files_ok,
            "sheet_rows_blank_and_valid": sheet_rows_ok,
            "response_template_blank_and_valid": response_template_ok,
            "participant_packets_ready": participant_packets["ready"],
            "readmes_ok": readmes_ok,
            "r195_awaiting_inputs": r195_status_ok,
        },
        "claim_gate": claim_gate,
        "next_action": (
            "Distribute P01-P05 R142 packets and the R124/R190/R203 paired sheets; "
            "place completed returns into docs/visexp/out/human-evidence-r195/inbox "
            "using the R207 return_file_plan names, then run "
            "python3 docs/visexp/r195_human_evidence_pipeline.py."
        ),
        "provenance": {
            "repo_commit": git(["rev-parse", "HEAD"]),
            "repo_dirty": bool(git(["status", "--short"])),
            "script_sha256": sha256_file(Path(__file__)),
        },
    }


def write_markdown(path: Path, payload: dict[str, Any]) -> None:
    lines = [
        "# R207 Human Evidence Launch Readiness",
        "",
        f"Status: `{payload['status']}`",
        "",
        "## Scope",
        "",
        "- Reads R187/R193/R195 generated artifacts only.",
        "- Does not read raw agent traces.",
        "- Does not fill labels or participant responses.",
        "- Does not support C5/C6 outcome claims.",
        "",
        "## Checks",
        "",
        "| check | value |",
        "|---|---:|",
    ]
    for key, value in payload["checks"].items():
        lines.append(f"| {key} | {value} |")
    lines.extend(
        [
            "",
            "## Launch Units",
            "",
            f"- R142 participant packets: `{payload['launch_units']['r142_participants']['packet_count']}`.",
            f"- R142 response template rows: `{payload['launch_units']['r142_response_template']['row_count']}`.",
            f"- R124 labeler rows: `{payload['launch_units']['r124_sheets']['labeler_1']['row_count']}` per sheet.",
            f"- R190 labeler rows: `{payload['launch_units']['r190_sheets']['labeler_1']['row_count']}` per sheet.",
            f"- R203 labeler rows: `{payload['launch_units']['r203_sheets']['labeler_1']['row_count']}` per sheet.",
            "",
            "## Return File Plan",
            "",
            "| R195 key | group | human file | R195 inbox name |",
            "|---|---|---|---|",
        ]
    )
    for row in payload["return_file_plan"]:
        lines.append(
            f"| `{row['r195_input_key']}` | {row['group']} | "
            f"{row['human_file']} | `{row['r195_inbox_name']}` |"
        )
    lines.extend(
        [
            "",
            "## Claim Boundary",
            "",
            payload["claim_boundary"],
            "",
            "Next action: " + payload["next_action"],
            "",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--r193-dir", type=Path, default=DEFAULT_R193_DIR)
    parser.add_argument("--r187-dir", type=Path, default=DEFAULT_R187_DIR)
    parser.add_argument("--r195-json", type=Path, default=DEFAULT_R195_JSON)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    payload = build_payload(args)
    out_json = args.out_dir / "human-evidence-launch-r207.json"
    out_md = args.out_dir / "human-evidence-launch-r207.md"
    payload["outputs"] = {
        "summary_json": rel(out_json),
        "summary_md": rel(out_md),
    }
    write_json(out_json, payload)
    write_markdown(out_md, payload)
    print(json.dumps({"status": payload["status"], "summary_json": rel(out_json)}, sort_keys=True))


if __name__ == "__main__":
    main()
