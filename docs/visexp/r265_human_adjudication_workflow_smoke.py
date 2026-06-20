#!/usr/bin/env python3
"""R265: synthetic smoke for R195 C6 adjudication workflow.

R265 does not create human evidence. It creates clearly synthetic disagreement
fixtures for R124, R190, and R203, verifies that unresolved disagreements bubble
up as a top-level R195 `needs_adjudication` status, then verifies that explicit
synthetic adjudication files let the same path run without upgrading C5/C6.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[1]
OUT_DIR = SCRIPT_DIR / "out"
DEFAULT_OUT_DIR = OUT_DIR / "human-adjudication-r265"

R124_BLINDED = OUT_DIR / "tag-adequacy-blinded-label-sheet-r124.csv"
R190_PACKET = OUT_DIR / "tag-consolidation-audit-r190" / "merge-risk-audit-packet-r190.csv"
R203_TEMPLATE = OUT_DIR / "long-tail-promotion-r203" / "long-tail-promotion-labeler-1-r203.csv"


R124_ADJ_FIELDS = [
    "row_id",
    "fragment_index",
    "fragment_level",
    "candidate_tag",
    "labeler_1",
    "labeler_2",
    "adjudicated_label",
    "notes",
]
R190_ADJ_FIELDS = [
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
R203_ADJ_FIELDS = [
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


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def command_result(cmd: list[str]) -> dict[str, Any]:
    proc = subprocess.run(cmd, cwd=REPO_ROOT, text=True, capture_output=True)
    return {
        "cmd": cmd,
        "cwd": rel(REPO_ROOT),
        "returncode": proc.returncode,
        "stdout_tail": proc.stdout[-4000:],
        "stderr_tail": proc.stderr[-4000:],
    }


def run_r195(case_dir: Path, inputs: dict[str, Path], adjudications: dict[str, Path] | None = None) -> dict[str, Any]:
    adjudications = adjudications or {}
    scored = case_dir / "scored"
    out_json = case_dir / "r195.json"
    out_md = case_dir / "r195.md"
    missing = case_dir / "missing"
    cmd = [
        "python3",
        "docs/visexp/r195_human_evidence_pipeline.py",
        "--r124-labeler-1",
        str(inputs["r124_l1"]),
        "--r124-labeler-2",
        str(inputs["r124_l2"]),
        "--r124-adjudication",
        str(adjudications.get("r124", missing / "r124-adjudication.csv")),
        "--r190-labeler-1",
        str(inputs["r190_l1"]),
        "--r190-labeler-2",
        str(inputs["r190_l2"]),
        "--r190-adjudication",
        str(adjudications.get("r190", missing / "r190-adjudication.csv")),
        "--r203-labeler-1",
        str(inputs["r203_l1"]),
        "--r203-labeler-2",
        str(inputs["r203_l2"]),
        "--r203-adjudication",
        str(adjudications.get("r203", missing / "r203-adjudication.csv")),
        "--r142-responses",
        str(missing / "r142-pilot-responses.csv"),
        "--scored-dir",
        str(scored),
        "--out-json",
        str(out_json),
        "--out-md",
        str(out_md),
    ]
    result = command_result(cmd)
    payload = read_json(out_json) if out_json.exists() else {}
    return {
        "command": result,
        "payload": payload,
        "payload_path": rel(out_json) if out_json.exists() else None,
        "payload_sha256": sha256_file(out_json),
        "scored_dir": scored,
    }


def make_r124(out_dir: Path) -> tuple[dict[str, Path], Path, dict[str, int]]:
    rows, fields = read_csv(R124_BLINDED)
    left_rows = []
    right_rows = []
    adj_rows = []
    counts = {"rows": len(rows), "disagreements": 0}
    for idx, row in enumerate(rows):
        left = "adequate"
        right = "generic_noisy" if idx % 3 == 0 else "adequate"
        left_rows.append({**row, "label": left, "notes": "r265_synthetic_disagreement"})
        right_rows.append({**row, "label": right, "notes": "r265_synthetic_disagreement"})
        if left != right:
            counts["disagreements"] += 1
            adj_rows.append(
                {
                    "row_id": row["row_id"],
                    "fragment_index": row["fragment_index"],
                    "fragment_level": row["fragment_level"],
                    "candidate_tag": row["candidate_tag"],
                    "labeler_1": left,
                    "labeler_2": right,
                    "adjudicated_label": "generic_noisy",
                    "notes": "r265_synthetic_adjudication_not_human_evidence",
                }
            )
    paths = {
        "r124_l1": out_dir / "inputs" / "r124-labeler-1.csv",
        "r124_l2": out_dir / "inputs" / "r124-labeler-2.csv",
    }
    adj = out_dir / "adjudication" / "r124-adjudication.csv"
    write_csv(paths["r124_l1"], left_rows, fields)
    write_csv(paths["r124_l2"], right_rows, fields)
    write_csv(adj, adj_rows, R124_ADJ_FIELDS)
    return paths, adj, counts


def make_r190(out_dir: Path) -> tuple[dict[str, Path], Path, dict[str, int]]:
    rows, fields = read_csv(R190_PACKET)
    left_rows = []
    right_rows = []
    adj_rows = []
    counts = {"rows": len(rows), "disagreements": 0}
    for idx, row in enumerate(rows):
        left = "acceptable"
        right = "overmerge" if row.get("audit_type") == "overmerge_proxy" and idx % 2 == 0 else "acceptable"
        left_rows.append({**row, "audit_label": left, "audit_notes": "r265_synthetic_disagreement"})
        right_rows.append({**row, "audit_label": right, "audit_notes": "r265_synthetic_disagreement"})
        if left != right:
            counts["disagreements"] += 1
        adj_rows.append(
            {
                "audit_id": row["audit_id"],
                "audit_type": row["audit_type"],
                "dimension": row["dimension"],
                "raw_tag": row["raw_tag"],
                "canonical_tag": row["canonical_tag"],
                "labeler_1": left,
                "labeler_2": right,
                "adjudicated_label": "overmerge" if left != right else "",
                "notes": "r265_synthetic_adjudication_not_human_evidence" if left != right else "",
            }
        )
    paths = {
        "r190_l1": out_dir / "inputs" / "r190-labeler-1.csv",
        "r190_l2": out_dir / "inputs" / "r190-labeler-2.csv",
    }
    adj = out_dir / "adjudication" / "r190-adjudication.csv"
    write_csv(paths["r190_l1"], left_rows, fields)
    write_csv(paths["r190_l2"], right_rows, fields)
    write_csv(adj, adj_rows, R190_ADJ_FIELDS)
    return paths, adj, counts


def make_r203(out_dir: Path) -> tuple[dict[str, Path], Path, dict[str, int]]:
    rows, fields = read_csv(R203_TEMPLATE)
    left_rows = []
    right_rows = []
    adj_rows = []
    counts = {"rows": len(rows), "disagreements": 0}
    for idx, row in enumerate(rows):
        left = "promote"
        right = "reject" if idx % 3 == 0 else "promote"
        left_rows.append({**row, "promotion_label": left, "promotion_notes": "r265_synthetic_disagreement"})
        right_rows.append({**row, "promotion_label": right, "promotion_notes": "r265_synthetic_disagreement"})
        if left != right:
            counts["disagreements"] += 1
        adj_rows.append(
            {
                "promotion_id": row["promotion_id"],
                "dimension": row["dimension"],
                "raw_tag": row["raw_tag"],
                "regenerated_tag": row["regenerated_tag"],
                "proposed_action": row["proposed_action"],
                "labeler_1": left,
                "labeler_2": right,
                "adjudicated_label": "reject" if left != right else "",
                "notes": "r265_synthetic_adjudication_not_human_evidence" if left != right else "",
            }
        )
    paths = {
        "r203_l1": out_dir / "inputs" / "r203-labeler-1.csv",
        "r203_l2": out_dir / "inputs" / "r203-labeler-2.csv",
    }
    adj = out_dir / "adjudication" / "r203-adjudication.csv"
    write_csv(paths["r203_l1"], left_rows, fields)
    write_csv(paths["r203_l2"], right_rows, fields)
    write_csv(adj, adj_rows, R203_ADJ_FIELDS)
    return paths, adj, counts


def op_statuses(payload: dict[str, Any]) -> dict[str, str | None]:
    return {
        name: op.get("status")
        for name, op in sorted((payload.get("operations") or {}).items())
    }


def template_row_count(path: Path) -> int:
    if not path.exists():
        return -1
    rows, _ = read_csv(path)
    return len(rows)


def gate_false(payload: dict[str, Any]) -> bool:
    gate = payload.get("claim_gate") or {}
    return not any(
        bool(gate.get(name))
        for name in (
            "c5_supported",
            "c6_adequacy_supported",
            "canonicalization_quality_supported",
            "long_tail_promotion_review_supported",
            "canonical_map_updated",
        )
    )


def build_payload(work_dir: Path, initial_provenance: dict[str, Any], *, keep_work_dir: bool) -> dict[str, Any]:
    r124_paths, r124_adj, r124_counts = make_r124(work_dir)
    r190_paths, r190_adj, r190_counts = make_r190(work_dir)
    r203_paths, r203_adj, r203_counts = make_r203(work_dir)
    inputs = {**r124_paths, **r190_paths, **r203_paths}
    unresolved = run_r195(work_dir / "unresolved-disagreements", inputs)
    adjudicated = run_r195(
        work_dir / "adjudicated-synthetic",
        inputs,
        {"r124": r124_adj, "r190": r190_adj, "r203": r203_adj},
    )
    unresolved_payload = unresolved["payload"]
    adjudicated_payload = adjudicated["payload"]
    unresolved_scored = unresolved["scored_dir"]
    templates = {
        "r124": unresolved_scored / "r124" / "tag-adequacy-adjudication-template-r195.csv",
        "r190": unresolved_scored / "r190" / "merge-risk-adjudication-template-r195.csv",
        "r203": unresolved_scored / "r203" / "long-tail-promotion-adjudication-template-r203.csv",
    }
    template_rows = {name: template_row_count(path) for name, path in templates.items()}
    checks = {
        "unresolved_r195_command_passed": unresolved["command"]["returncode"] == 0,
        "unresolved_top_level_needs_adjudication": unresolved_payload.get("status") == "needs_adjudication",
        "unresolved_operation_statuses": {
            "r124": (unresolved_payload.get("operations") or {}).get("r124", {}).get("status")
            == "joined_not_ready_for_scoring",
            "r190": (unresolved_payload.get("operations") or {}).get("r190", {}).get("status")
            == "needs_adjudication",
            "r203": (unresolved_payload.get("operations") or {}).get("r203", {}).get("status")
            == "needs_adjudication",
        },
        "unresolved_adjudication_templates_match_disagreements": {
            "r124": template_rows["r124"] == r124_counts["disagreements"],
            "r190": template_rows["r190"] == r190_counts["disagreements"],
            "r203": template_rows["r203"] == r203_counts["disagreements"],
        },
        "unresolved_claim_gates_false": gate_false(unresolved_payload),
        "adjudicated_r195_command_passed": adjudicated["command"]["returncode"] == 0,
        "adjudicated_runs_without_support": adjudicated_payload.get("status")
        == "scored_human_inputs_no_supported_gate",
        "adjudicated_claim_gates_false": gate_false(adjudicated_payload),
    }
    flat_checks = []
    for value in checks.values():
        if isinstance(value, dict):
            flat_checks.extend(bool(item) for item in value.values())
        else:
            flat_checks.append(bool(value))
    return {
        "schema_version": 1,
        "run_id": "R265",
        "status": "passed" if all(flat_checks) else "failed",
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "synthetic_inputs": {
            "work_dir": rel(work_dir),
            "work_dir_retained": keep_work_dir,
            "boundary": "synthetic disagreement and adjudication fixtures; not participant responses or human labels",
            "r124": r124_counts,
            "r190": r190_counts,
            "r203": r203_counts,
        },
        "cases": {
            "unresolved_disagreements": {
                "r195_status": unresolved_payload.get("status"),
                "operation_statuses": op_statuses(unresolved_payload),
                "payload_path": unresolved["payload_path"],
                "payload_sha256": unresolved["payload_sha256"],
                "adjudication_template_rows": template_rows,
                "claim_gate": unresolved_payload.get("claim_gate"),
            },
            "adjudicated_synthetic": {
                "r195_status": adjudicated_payload.get("status"),
                "operation_statuses": op_statuses(adjudicated_payload),
                "payload_path": adjudicated["payload_path"],
                "payload_sha256": adjudicated["payload_sha256"],
                "claim_gate": adjudicated_payload.get("claim_gate"),
            },
        },
        "checks": checks,
        "claim_boundary": (
            "R265 proves only that R195 surfaces unresolved C6 disagreements and accepts explicit "
            "adjudication files. All rows are synthetic controls, so C5, C6, canonicalization, "
            "promotion, and weak-accept gates must remain false."
        ),
        "provenance": {
            "repo_commit": initial_provenance["repo_commit"],
            "repo_dirty": initial_provenance["repo_dirty"],
            "repo_dirty_semantics": "captured before R265 writes synthetic fixtures or R195 outputs",
            "script": rel(Path(__file__).resolve()),
            "script_sha256": sha256_file(Path(__file__).resolve()),
        },
    }


def write_markdown(path: Path, payload: dict[str, Any]) -> None:
    lines = [
        "# R265 Human Adjudication Workflow Smoke",
        "",
        f"Status: `{payload['status']}`",
        "",
        "R265 uses synthetic disagreement fixtures to test the R195 adjudication path. It is not human evidence.",
        "",
        "## Cases",
        "",
        "| case | R195 status | operation statuses |",
        "|---|---|---|",
    ]
    for name, case in payload["cases"].items():
        ops = ", ".join(f"{key}={value}" for key, value in sorted(case["operation_statuses"].items()))
        lines.append(f"| `{name}` | `{case['r195_status']}` | `{ops}` |")
    lines.extend(["", "## Checks", ""])
    for name, value in payload["checks"].items():
        if isinstance(value, dict):
            inner = ", ".join(f"{key}={item}" for key, item in sorted(value.items()))
            lines.append(f"- `{name}`: {inner}.")
        else:
            lines.append(f"- `{name}`: `{value}`.")
    lines.extend(["", "## Boundary", "", payload["claim_boundary"], ""])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def run(args: argparse.Namespace) -> dict[str, Any]:
    args.out_dir.mkdir(parents=True, exist_ok=True)
    work_dir = args.out_dir / "work"
    if work_dir.exists():
        shutil.rmtree(work_dir)
    work_dir.mkdir(parents=True, exist_ok=True)
    initial_provenance = {
        "repo_commit": git(["rev-parse", "HEAD"]),
        "repo_dirty": bool(git(["status", "--short"])),
    }
    payload = build_payload(work_dir, initial_provenance, keep_work_dir=args.keep_work_dir)
    out_json = args.out_dir / "human-adjudication-r265.json"
    out_md = args.out_dir / "human-adjudication-r265.md"
    write_json(out_json, payload)
    write_markdown(out_md, payload)
    if not args.keep_work_dir:
        shutil.rmtree(work_dir)
    print(json.dumps({"status": payload["status"], "checks": payload["checks"]}, indent=2, sort_keys=True))
    if payload["status"] != "passed":
        raise SystemExit(1)
    return payload


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--keep-work-dir", action="store_true")
    return parser


if __name__ == "__main__":
    run(build_parser().parse_args())
