#!/usr/bin/env python3
"""R242: synthetic contract smoke for the human-evidence ingestion pipeline.

This script does not create C5/C6 evidence. It generates clearly synthetic
returned files to exercise the R195 ingestion/scoring path, then verifies that
canonical empty gates remain untouched. The value is contract coverage: real
human files should be scoreable by the same path, while partial or malformed
returns should not silently upgrade any claim.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[1]
OUT_DIR = SCRIPT_DIR / "out"
DEFAULT_OUT_DIR = OUT_DIR / "human-evidence-contract-r242"

R124_BLINDED = OUT_DIR / "tag-adequacy-blinded-label-sheet-r124.csv"
R190_PACKET = OUT_DIR / "tag-consolidation-audit-r190" / "merge-risk-audit-packet-r190.csv"
R203_LABELER_TEMPLATE = OUT_DIR / "long-tail-promotion-r203" / "long-tail-promotion-labeler-1-r203.csv"
R142_ASSIGNMENTS = OUT_DIR / "user-task-assignments.csv"
R142_ANSWER_KEY = OUT_DIR / "user-task-answer-key.csv"

CANONICAL_R124 = OUT_DIR / "tag-adequacy-results-r124.json"
CANONICAL_R142 = OUT_DIR / "user-task-results.json"
CANONICAL_R190 = OUT_DIR / "tag-consolidation-audit-r190" / "merge-risk-audit-results-r190.json"
CANONICAL_R203 = OUT_DIR / "long-tail-promotion-r203" / "long-tail-promotion-r203.json"

RESPONSE_FIELDS = [
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


def rel(path: Path | None) -> str | None:
    if path is None:
        return None
    try:
        return str(path.resolve().relative_to(REPO_ROOT.resolve()))
    except Exception:
        return str(path)


def sha256_file(path: Path | None) -> str | None:
    if path is None or not path.exists():
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


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def command_result(cmd: list[str]) -> dict[str, Any]:
    proc = subprocess.run(cmd, cwd=REPO_ROOT, text=True, capture_output=True)
    return {
        "cmd": cmd,
        "cwd": rel(REPO_ROOT),
        "returncode": proc.returncode,
        "stdout_tail": proc.stdout[-3000:],
        "stderr_tail": proc.stderr[-3000:],
    }


def run_r195(
    *,
    case_dir: Path,
    r124_l1: Path | None = None,
    r124_l2: Path | None = None,
    r190_l1: Path | None = None,
    r190_l2: Path | None = None,
    r203_l1: Path | None = None,
    r203_l2: Path | None = None,
    r142_responses: Path | None = None,
) -> dict[str, Any]:
    inbox = case_dir / "inbox"
    scored = case_dir / "scored"
    out_json = case_dir / "r195.json"
    out_md = case_dir / "r195.md"

    def existing_or_missing(path: Path | None, name: str) -> Path:
        return path if path is not None else inbox / name

    cmd = [
        "python3",
        "docs/visexp/r195_human_evidence_pipeline.py",
        "--r124-labeler-1",
        str(existing_or_missing(r124_l1, "r124-labeler-1.csv")),
        "--r124-labeler-2",
        str(existing_or_missing(r124_l2, "r124-labeler-2.csv")),
        "--r124-adjudication",
        str(inbox / "r124-adjudication.csv"),
        "--r190-labeler-1",
        str(existing_or_missing(r190_l1, "r190-labeler-1.csv")),
        "--r190-labeler-2",
        str(existing_or_missing(r190_l2, "r190-labeler-2.csv")),
        "--r190-adjudication",
        str(inbox / "r190-adjudication.csv"),
        "--r203-labeler-1",
        str(existing_or_missing(r203_l1, "r203-labeler-1.csv")),
        "--r203-labeler-2",
        str(existing_or_missing(r203_l2, "r203-labeler-2.csv")),
        "--r203-adjudication",
        str(inbox / "r203-adjudication.csv"),
        "--r142-responses",
        str(existing_or_missing(r142_responses, "r142-pilot-responses.csv")),
        "--scored-dir",
        str(scored),
        "--out-json",
        str(out_json),
        "--out-md",
        str(out_md),
    ]
    result = command_result(cmd)
    payload = read_json(out_json) if out_json.exists() else None
    return {
        "command": result,
        "payload_path": rel(out_json) if out_json.exists() else None,
        "payload_sha256": sha256_file(out_json),
        "payload": payload,
    }


def write_synthetic_r124(blinded: Path, labeler_1: Path, labeler_2: Path) -> dict[str, Any]:
    rows, fields = read_csv(blinded)
    out_rows = []
    labels = {"adequate": 0, "generic_noisy": 0}
    for index, row in enumerate(rows):
        label = "adequate" if index % 2 == 0 else "generic_noisy"
        labels[label] += 1
        out_rows.append({**row, "label": label, "notes": "synthetic_contract_control"})
    write_csv(labeler_1, out_rows, fields)
    write_csv(labeler_2, out_rows, fields)
    return {"rows": len(out_rows), "label_counts": labels}


def write_synthetic_r190(packet: Path, labeler_1: Path, labeler_2: Path) -> dict[str, Any]:
    rows, fields = read_csv(packet)
    out_rows = [
        {**row, "audit_label": "unclear", "audit_notes": "synthetic_contract_control"}
        for row in rows
    ]
    write_csv(labeler_1, out_rows, fields)
    write_csv(labeler_2, out_rows, fields)
    return {"rows": len(out_rows), "label_counts": {"unclear": len(out_rows)}}


def write_synthetic_r203(template: Path, labeler_1: Path, labeler_2: Path) -> dict[str, Any]:
    rows, fields = read_csv(template)
    out_rows = [
        {**row, "promotion_label": "unclear", "promotion_notes": "synthetic_contract_control"}
        for row in rows
    ]
    write_csv(labeler_1, out_rows, fields)
    write_csv(labeler_2, out_rows, fields)
    return {"rows": len(out_rows), "label_counts": {"unclear": len(out_rows)}}


def load_answer_key(path: Path) -> dict[str, dict[str, Any]]:
    rows, _ = read_csv(path)
    return {
        row["task_id"]: json.loads(row.get("answer_json") or "{}")
        for row in rows
        if row.get("task_id")
    }


def write_synthetic_r142(assignments: Path, answer_key: Path, out_csv: Path) -> dict[str, Any]:
    assignment_rows, _ = read_csv(assignments)
    answers = load_answer_key(answer_key)
    rows = []
    condition_counts: dict[str, int] = {}
    for row in assignment_rows:
        condition = row["condition"]
        condition_counts[condition] = condition_counts.get(condition, 0) + 1
        task_id = row["task_id"]
        rows.append(
            {
                "participant_id": row["participant_id"],
                "order_index": row["order_index"],
                "packet_id": row["packet_id"],
                "task_id": task_id,
                "condition": condition,
                "response_json": json.dumps(answers[task_id], sort_keys=True),
                "task_time_seconds": "25.0" if condition == "semantic-stack" else "50.0",
                "confidence": "4",
                "notes": "synthetic_contract_control",
            }
        )
    write_csv(out_csv, rows, RESPONSE_FIELDS)
    return {
        "rows": len(rows),
        "participants": len({row["participant_id"] for row in rows}),
        "condition_counts": condition_counts,
    }


def write_invalid_r142_duplicate(assignments: Path, answer_key: Path, out_csv: Path) -> dict[str, Any]:
    assignment_rows, _ = read_csv(assignments)
    answers = load_answer_key(answer_key)
    first = assignment_rows[0]
    row = {
        "participant_id": first["participant_id"],
        "order_index": first["order_index"],
        "packet_id": first["packet_id"],
        "task_id": first["task_id"],
        "condition": first["condition"],
        "response_json": json.dumps(answers[first["task_id"]], sort_keys=True),
        "task_time_seconds": "10.0",
        "confidence": "4",
        "notes": "synthetic_invalid_duplicate",
    }
    write_csv(out_csv, [row, dict(row)], RESPONSE_FIELDS)
    return {"rows": 2, "duplicated_assignment": [first["participant_id"], first["task_id"], first["condition"]]}


def canonical_gate_snapshot() -> dict[str, Any]:
    r124 = read_json(CANONICAL_R124)
    r142 = read_json(CANONICAL_R142)
    r190 = read_json(CANONICAL_R190)
    r203 = read_json(CANONICAL_R203)
    return {
        "r124": {
            "path": rel(CANONICAL_R124),
            "status": r124.get("status"),
            "adequacy_supported": (r124.get("claim_gate") or {}).get("adequacy_supported"),
        },
        "r142": {
            "path": rel(CANONICAL_R142),
            "status": r142.get("status"),
            "c5_supported": ((r142.get("claim_analysis") or {}).get("claim_gate") or {}).get("c5_supported"),
        },
        "r190": {
            "path": rel(CANONICAL_R190),
            "status": r190.get("status"),
            "canonicalization_quality_supported": (r190.get("claim_gate") or {}).get(
                "canonicalization_quality_supported"
            ),
        },
        "r203": {
            "path": rel(CANONICAL_R203),
            "status": r203.get("status"),
            "long_tail_promotion_review_supported": (r203.get("claim_gate") or {}).get(
                "long_tail_promotion_review_supported"
            ),
            "canonical_map_updated": (r203.get("claim_gate") or {}).get("canonical_map_updated"),
        },
    }


def canonical_empty_gates_preserved(snapshot: dict[str, Any]) -> bool:
    return (
        snapshot["r124"]["status"] == "human_labels_empty"
        and snapshot["r124"]["adequacy_supported"] is False
        and snapshot["r142"]["status"] == "participant_results_empty"
        and snapshot["r142"]["c5_supported"] is False
        and snapshot["r190"]["status"] == "human_labels_empty"
        and snapshot["r190"]["canonicalization_quality_supported"] is False
        and snapshot["r203"]["status"] == "human_labels_empty"
        and snapshot["r203"]["long_tail_promotion_review_supported"] is False
        and snapshot["r203"]["canonical_map_updated"] is False
    )


def build_payload(out_dir: Path, initial_provenance: dict[str, Any]) -> dict[str, Any]:
    synthetic_dir = out_dir / "synthetic-ready" / "inbox"
    partial_dir = out_dir / "partial-r124"
    invalid_dir = out_dir / "invalid-r142"
    no_input_dir = out_dir / "no-input"

    r124_l1 = synthetic_dir / "r124-labeler-1.csv"
    r124_l2 = synthetic_dir / "r124-labeler-2.csv"
    r190_l1 = synthetic_dir / "r190-labeler-1.csv"
    r190_l2 = synthetic_dir / "r190-labeler-2.csv"
    r203_l1 = synthetic_dir / "r203-labeler-1.csv"
    r203_l2 = synthetic_dir / "r203-labeler-2.csv"
    r142_responses = synthetic_dir / "r142-pilot-responses.csv"

    generated_inputs = {
        "r124": write_synthetic_r124(R124_BLINDED, r124_l1, r124_l2),
        "r190": write_synthetic_r190(R190_PACKET, r190_l1, r190_l2),
        "r203": write_synthetic_r203(R203_LABELER_TEMPLATE, r203_l1, r203_l2),
        "r142": write_synthetic_r142(R142_ASSIGNMENTS, R142_ANSWER_KEY, r142_responses),
    }
    ready = run_r195(
        case_dir=out_dir / "synthetic-ready",
        r124_l1=r124_l1,
        r124_l2=r124_l2,
        r190_l1=r190_l1,
        r190_l2=r190_l2,
        r203_l1=r203_l1,
        r203_l2=r203_l2,
        r142_responses=r142_responses,
    )

    partial_l1 = partial_dir / "inbox" / "r124-labeler-1.csv"
    write_synthetic_r124(R124_BLINDED, partial_l1, partial_dir / "unused-labeler-2.csv")
    partial = run_r195(case_dir=partial_dir, r124_l1=partial_l1)

    invalid_responses = invalid_dir / "inbox" / "r142-pilot-responses.csv"
    invalid_input = write_invalid_r142_duplicate(R142_ASSIGNMENTS, R142_ANSWER_KEY, invalid_responses)
    invalid = run_r195(case_dir=invalid_dir, r142_responses=invalid_responses)

    no_input = run_r195(case_dir=no_input_dir)
    canonical_snapshot = canonical_gate_snapshot()

    ready_payload = ready.get("payload") or {}
    partial_payload = partial.get("payload") or {}
    invalid_payload = invalid.get("payload") or {}
    no_input_payload = no_input.get("payload") or {}
    operations = ready_payload.get("operations") or {}
    gates = ready_payload.get("claim_gate") or {}

    checks = {
        "synthetic_ready_r195_command_passed": ready["command"]["returncode"] == 0,
        "synthetic_ready_status_scored_no_supported_gate": ready_payload.get("status")
        == "scored_human_inputs_no_supported_gate",
        "synthetic_ready_all_operations_scored": {
            "r124": operations.get("r124", {}).get("status") == "human_labels_scored",
            "r142": operations.get("r142", {}).get("status") == "participant_results_scored",
            "r190": operations.get("r190", {}).get("status") == "human_labels_scored",
            "r203": operations.get("r203", {}).get("status") == "human_labels_scored",
        },
        "synthetic_ready_claim_gates_remain_false": {
            "not_c5_supported": gates.get("c5_supported") is False,
            "not_c6_adequacy_supported": gates.get("c6_adequacy_supported") is False,
            "not_canonicalization_quality_supported": gates.get("canonicalization_quality_supported") is False,
            "not_long_tail_promotion_review_supported": gates.get("long_tail_promotion_review_supported") is False,
            "not_canonical_map_updated": gates.get("canonical_map_updated") is False,
        },
        "partial_r124_detected": partial_payload.get("status") == "partial_human_inputs",
        "invalid_r142_rejected": invalid_payload.get("status") == "scoring_failed",
        "no_input_awaiting": no_input_payload.get("status") == "awaiting_human_inputs",
        "canonical_empty_gates_preserved": canonical_empty_gates_preserved(canonical_snapshot),
    }
    flat_checks = []
    for value in checks.values():
        if isinstance(value, dict):
            flat_checks.extend(bool(inner) for inner in value.values())
        else:
            flat_checks.append(bool(value))

    return {
        "schema_version": 1,
        "run_id": "R242",
        "status": "passed" if all(flat_checks) else "failed",
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "synthetic_inputs": {
            "directory": rel(synthetic_dir),
            "generated": generated_inputs,
            "boundary": "synthetic contract controls; not participant responses or human adequacy labels",
        },
        "cases": {
            "synthetic_ready": {
                "r195_status": ready_payload.get("status"),
                "payload_path": ready["payload_path"],
                "payload_sha256": ready["payload_sha256"],
                "operation_statuses": {
                    name: op.get("status") for name, op in sorted(operations.items())
                },
                "claim_gate": gates,
            },
            "partial_r124": {
                "r195_status": partial_payload.get("status"),
                "payload_path": partial["payload_path"],
                "payload_sha256": partial["payload_sha256"],
            },
            "invalid_r142": {
                "input_summary": invalid_input,
                "r195_status": invalid_payload.get("status"),
                "payload_path": invalid["payload_path"],
                "payload_sha256": invalid["payload_sha256"],
                "operation_status": (invalid_payload.get("operations") or {}).get("r142", {}).get("status"),
            },
            "no_input": {
                "r195_status": no_input_payload.get("status"),
                "payload_path": no_input["payload_path"],
                "payload_sha256": no_input["payload_sha256"],
            },
        },
        "canonical_gate_snapshot": canonical_snapshot,
        "checks": checks,
        "claim_boundary": (
            "R242 proves only the R195 ingestion/scoring contract. It uses synthetic returned "
            "files, does not count as C5 participant evidence, does not count as C6 human "
            "adequacy evidence, and must not be used to upgrade claim verdicts."
        ),
        "provenance": {
            "repo_commit": initial_provenance["repo_commit"],
            "repo_dirty": initial_provenance["repo_dirty"],
            "repo_dirty_semantics": "captured before R242 writes synthetic inputs or scored outputs",
            "script": rel(Path(__file__).resolve()),
            "script_sha256": sha256_file(Path(__file__).resolve()),
        },
    }


def write_markdown(path: Path, payload: dict[str, Any]) -> None:
    checks = payload["checks"]
    lines = [
        "# R242 Human-Evidence Contract Smoke",
        "",
        f"Status: `{payload['status']}`",
        "",
        "R242 uses synthetic returned files to test the R195 contract. It is not C5/C6 outcome evidence.",
        "",
        "## Cases",
        "",
        "| case | status | purpose |",
        "|---|---|---|",
        f"| synthetic-ready | `{payload['cases']['synthetic_ready']['r195_status']}` | Complete synthetic files score end-to-end without claim support. |",
        f"| partial-r124 | `{payload['cases']['partial_r124']['r195_status']}` | One missing labeler sheet is detected as partial input. |",
        f"| invalid-r142 | `{payload['cases']['invalid_r142']['r195_status']}` | Duplicate/incomplete response CSV is rejected. |",
        f"| no-input | `{payload['cases']['no_input']['r195_status']}` | Empty inbox remains awaiting human inputs. |",
        "",
        "## Checks",
        "",
    ]
    for name, value in checks.items():
        if isinstance(value, dict):
            inner = ", ".join(f"{key}={item}" for key, item in sorted(value.items()))
            lines.append(f"- `{name}`: {inner}.")
        else:
            lines.append(f"- `{name}`: `{value}`.")
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            payload["claim_boundary"],
            "",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def run(args: argparse.Namespace) -> dict[str, Any]:
    args.out_dir.mkdir(parents=True, exist_ok=True)
    initial_provenance = {
        "repo_commit": git(["rev-parse", "HEAD"]),
        "repo_dirty": bool(git(["status", "--short"])),
    }
    payload = build_payload(args.out_dir, initial_provenance)
    out_json = args.out_dir / "human-evidence-contract-r242.json"
    out_md = args.out_dir / "human-evidence-contract-r242.md"
    write_json(out_json, payload)
    write_markdown(out_md, payload)
    print(json.dumps({"status": payload["status"], "checks": payload["checks"]}, indent=2, sort_keys=True))
    if payload["status"] != "passed":
        raise SystemExit(1)
    return payload


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    return parser


if __name__ == "__main__":
    run(build_parser().parse_args())
