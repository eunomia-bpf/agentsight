#!/usr/bin/env python3
"""R195: ingest and score returned human-evidence files.

Default mode is intentionally conservative. If no real human inputs exist in the
R195 inbox, the script writes an `awaiting_human_inputs` report and does not run
or overwrite any R124/R142/R190/R203 scorer outputs. When completed sheets or
participant responses are supplied, results are written under a separate R195
scored directory so the canonical empty gates remain auditable until promoted.
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
DEFAULT_WORK_DIR = OUT_DIR / "human-evidence-r195"
DEFAULT_INBOX = DEFAULT_WORK_DIR / "inbox"
DEFAULT_SCORED_DIR = DEFAULT_WORK_DIR / "scored"
DEFAULT_OUT_JSON = OUT_DIR / "human-evidence-pipeline-r195.json"
DEFAULT_OUT_MD = OUT_DIR / "human-evidence-pipeline-r195.md"

DEFAULT_R124_LABELER_1 = DEFAULT_INBOX / "r124-labeler-1.csv"
DEFAULT_R124_LABELER_2 = DEFAULT_INBOX / "r124-labeler-2.csv"
DEFAULT_R124_ADJUDICATION = DEFAULT_INBOX / "r124-adjudication.csv"
DEFAULT_R190_LABELER_1 = DEFAULT_INBOX / "r190-labeler-1.csv"
DEFAULT_R190_LABELER_2 = DEFAULT_INBOX / "r190-labeler-2.csv"
DEFAULT_R190_ADJUDICATION = DEFAULT_INBOX / "r190-adjudication.csv"
DEFAULT_R203_LABELER_1 = DEFAULT_INBOX / "r203-labeler-1.csv"
DEFAULT_R203_LABELER_2 = DEFAULT_INBOX / "r203-labeler-2.csv"
DEFAULT_R203_ADJUDICATION = DEFAULT_INBOX / "r203-adjudication.csv"
DEFAULT_R142_RESPONSES = DEFAULT_INBOX / "r142-pilot-responses.csv"

R124_PACKET = OUT_DIR / "tag-adequacy-label-packet-r122.csv"
R124_BLINDED = OUT_DIR / "tag-adequacy-blinded-label-sheet-r124.csv"
R190_PACKET = OUT_DIR / "tag-consolidation-audit-r190" / "merge-risk-audit-packet-r190.csv"
R142_BUNDLE = OUT_DIR / "user-task-benchmark.json"
R142_ANSWER_KEY = OUT_DIR / "user-task-answer-key.csv"
R142_ASSIGNMENTS = OUT_DIR / "user-task-assignments.csv"

INPUT_VALUE_FIELDS = {
    "r124_labeler_1": ["label"],
    "r124_labeler_2": ["label"],
    "r190_labeler_1": ["audit_label"],
    "r190_labeler_2": ["audit_label"],
    "r203_labeler_1": ["promotion_label"],
    "r203_labeler_2": ["promotion_label"],
    "r142_responses": ["task_time_seconds", "confidence", "notes"],
}

FORBIDDEN_RETURN_MARKERS = [
    "r259_export_smoke",
    "r259_synthetic_export_smoke_not_human_evidence",
    "r244-synthetic",
]


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


def csv_row_count(path: Path) -> int | None:
    if not path.exists():
        return None
    with path.open("r", encoding="utf-8", newline="") as handle:
        return sum(1 for _ in csv.DictReader(handle))


def csv_filled_value_count(path: Path, fields: list[str]) -> int | None:
    if not path.exists():
        return None
    count = 0
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            if any((row.get(field) or "").strip() for field in fields):
                count += 1
    return count


def csv_marker_hits(path: Path, markers: list[str], *, max_hits: int = 10) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    hits: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row_index, row in enumerate(reader, start=1):
            for field, value in row.items():
                cell = value or ""
                for marker in markers:
                    if marker in cell:
                        hits.append({"row": row_index, "field": field, "marker": marker})
                        if len(hits) >= max_hits:
                            return hits
    return hits


def default_input_paths() -> dict[str, Path]:
    return {
        "r124_labeler_1": DEFAULT_R124_LABELER_1,
        "r124_labeler_2": DEFAULT_R124_LABELER_2,
        "r124_adjudication": DEFAULT_R124_ADJUDICATION,
        "r190_labeler_1": DEFAULT_R190_LABELER_1,
        "r190_labeler_2": DEFAULT_R190_LABELER_2,
        "r190_adjudication": DEFAULT_R190_ADJUDICATION,
        "r203_labeler_1": DEFAULT_R203_LABELER_1,
        "r203_labeler_2": DEFAULT_R203_LABELER_2,
        "r203_adjudication": DEFAULT_R203_ADJUDICATION,
        "r142_responses": DEFAULT_R142_RESPONSES,
    }


def input_mode(paths: dict[str, Path]) -> str:
    defaults = default_input_paths()
    for name, path in paths.items():
        if path.resolve() != defaults[name].resolve():
            return "explicit_paths"
    return "default_inbox"


def read_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def path_info(path: Path, *, optional: bool = False) -> dict[str, Any]:
    info = {
        "path": rel(path),
        "exists": path.exists(),
        "optional": optional,
        "sha256": sha256_file(path),
    }
    if path.suffix.lower() == ".csv":
        info["row_count"] = csv_row_count(path)
    return info


def input_presence(paths: dict[str, Path]) -> dict[str, bool]:
    return {name: path.exists() for name, path in paths.items()}


def group_readiness(presence: dict[str, bool]) -> dict[str, Any]:
    groups = {
        "r124": ["r124_labeler_1", "r124_labeler_2"],
        "r190": ["r190_labeler_1", "r190_labeler_2"],
        "r203": ["r203_labeler_1", "r203_labeler_2"],
        "r142": ["r142_responses"],
    }
    out: dict[str, Any] = {}
    any_present = False
    any_ready = False
    for group, required in groups.items():
        present = [name for name in required if presence.get(name)]
        missing = [name for name in required if not presence.get(name)]
        ready = not missing
        partial = bool(present) and bool(missing)
        any_present = any_present or bool(present)
        any_ready = any_ready or ready
        out[group] = {
            "required": required,
            "present": present,
            "missing": missing,
            "ready": ready,
            "partial": partial,
        }

    if any_ready:
        status = "ready_to_score"
    elif any_present:
        status = "partial_human_inputs"
    else:
        status = "awaiting_human_inputs"
    out["overall_status"] = status
    out["any_present"] = any_present
    out["any_ready"] = any_ready
    return out


def input_safety(paths: dict[str, Path]) -> dict[str, Any]:
    marker_hits: dict[str, list[dict[str, Any]]] = {}
    for name, path in paths.items():
        hits = csv_marker_hits(path, FORBIDDEN_RETURN_MARKERS)
        if hits:
            marker_hits[name] = hits
    return {
        "status": "unsafe_return_inputs" if marker_hits else "passed",
        "forbidden_markers": FORBIDDEN_RETURN_MARKERS,
        "marker_hits": marker_hits,
        "unsafe": bool(marker_hits),
    }


def command_result(cmd: list[str], *, run: bool) -> dict[str, Any]:
    record: dict[str, Any] = {
        "cmd": cmd,
        "cwd": rel(REPO_ROOT),
        "ran": run,
        "returncode": None,
        "stdout_tail": "",
        "stderr_tail": "",
    }
    if not run:
        return record
    proc = subprocess.run(cmd, cwd=REPO_ROOT, text=True, capture_output=True)
    record["returncode"] = proc.returncode
    record["stdout_tail"] = proc.stdout[-4000:]
    record["stderr_tail"] = proc.stderr[-4000:]
    return record


def command_ok(record: dict[str, Any]) -> bool:
    return bool(record.get("ran")) and record.get("returncode") == 0


def run_r124(paths: dict[str, Path], scored_dir: Path, run_commands: bool) -> dict[str, Any]:
    r124_dir = scored_dir / "r124"
    join_json = r124_dir / "tag-adequacy-label-join-r195.json"
    join_md = r124_dir / "tag-adequacy-label-join-r195.md"
    joined_csv = r124_dir / "tag-adequacy-label-packet-r195-joined.csv"
    adjudication_template = r124_dir / "tag-adequacy-adjudication-template-r195.csv"
    score_json = r124_dir / "tag-adequacy-results-r195.json"
    score_csv = r124_dir / "tag-adequacy-results-r195.csv"
    score_md = r124_dir / "tag-adequacy-results-r195.md"

    cmd = [
        "python3",
        "docs/visexp/r124_join_blinded_labels.py",
        "--packet",
        rel(R124_PACKET),
        "--blinded",
        rel(R124_BLINDED),
        "--labeler-1",
        rel(paths["r124_labeler_1"]),
        "--labeler-2",
        rel(paths["r124_labeler_2"]),
        "--adjudication-template",
        rel(adjudication_template),
        "--joined-labels",
        rel(joined_csv),
        "--out-json",
        rel(join_json),
        "--out-md",
        rel(join_md),
    ]
    if paths["r124_adjudication"].exists():
        cmd.extend(["--adjudication", rel(paths["r124_adjudication"])])

    op: dict[str, Any] = {
        "status": "not_run",
        "commands": [],
        "outputs": {
            "join_json": rel(join_json),
            "joined_csv": rel(joined_csv),
            "score_json": rel(score_json),
        },
    }
    join_cmd = command_result(cmd, run=run_commands)
    op["commands"].append(join_cmd)
    if not command_ok(join_cmd):
        op["status"] = "failed" if run_commands else "ready_no_run"
        return op

    join_result = read_json(join_json) or {}
    op["join_status"] = join_result.get("status")
    if join_result.get("status") != "ready_for_scoring":
        op["status"] = "joined_not_ready_for_scoring"
        op["join_summary"] = join_result.get("summary", {})
        return op

    score_cmd = command_result(
        [
            "python3",
            "docs/visexp/score_tag_adequacy.py",
            "--labels",
            rel(joined_csv),
            "--out-json",
            rel(score_json),
            "--out-csv",
            rel(score_csv),
            "--out-md",
            rel(score_md),
        ],
        run=run_commands,
    )
    op["commands"].append(score_cmd)
    if not command_ok(score_cmd):
        op["status"] = "failed" if run_commands else "ready_no_run"
        return op

    result = read_json(score_json) or {}
    op["status"] = result.get("status", "scored")
    op["claim_gate"] = result.get("claim_gate", {})
    op["summary"] = result.get("summary", {})
    return op


def run_r190(paths: dict[str, Path], scored_dir: Path, run_commands: bool) -> dict[str, Any]:
    r190_dir = scored_dir / "r190"
    result_json = r190_dir / "merge-risk-audit-results-r195.json"
    result_csv = r190_dir / "merge-risk-audit-results-r195.csv"
    result_md = r190_dir / "merge-risk-audit-results-r195.md"
    joined_csv = r190_dir / "merge-risk-audit-joined-r195.csv"
    adjudication_template = r190_dir / "merge-risk-adjudication-template-r195.csv"
    cmd = [
        "python3",
        "docs/visexp/r190_score_merge_audit.py",
        "--packet",
        rel(R190_PACKET),
        "--labeler-1",
        rel(paths["r190_labeler_1"]),
        "--labeler-2",
        rel(paths["r190_labeler_2"]),
        "--adjudication-template",
        rel(adjudication_template),
        "--joined-labels",
        rel(joined_csv),
        "--out-json",
        rel(result_json),
        "--out-csv",
        rel(result_csv),
        "--out-md",
        rel(result_md),
    ]
    if paths["r190_adjudication"].exists():
        cmd.extend(["--adjudication", rel(paths["r190_adjudication"])])
    op: dict[str, Any] = {
        "status": "not_run",
        "commands": [],
        "outputs": {
            "result_json": rel(result_json),
            "joined_csv": rel(joined_csv),
        },
    }
    run_record = command_result(cmd, run=run_commands)
    op["commands"].append(run_record)
    if not command_ok(run_record):
        op["status"] = "failed" if run_commands else "ready_no_run"
        return op
    result = read_json(result_json) or {}
    op["status"] = result.get("status", "scored")
    op["claim_gate"] = result.get("claim_gate", {})
    op["summary"] = result.get("summary", {})
    return op


def run_r142(paths: dict[str, Path], scored_dir: Path, run_commands: bool, scoring: dict[str, Path]) -> dict[str, Any]:
    r142_dir = scored_dir / "r142"
    result_json = r142_dir / "user-task-results.json"
    cmd = [
        "python3",
        "docs/visexp/score_user_task_results.py",
        "--responses",
        rel(paths["r142_responses"]),
        "--bundle",
        rel(scoring["r142_bundle"]),
        "--answer-key",
        rel(scoring["r142_answer_key"]),
        "--assignments",
        rel(scoring["r142_assignments"]),
        "--out",
        rel(r142_dir),
    ]
    op: dict[str, Any] = {
        "status": "not_run",
        "commands": [],
        "outputs": {"result_json": rel(result_json)},
        "scoring_inputs": {
            "bundle": rel(scoring["r142_bundle"]),
            "answer_key": rel(scoring["r142_answer_key"]),
            "assignments": rel(scoring["r142_assignments"]),
        },
    }
    run_record = command_result(cmd, run=run_commands)
    op["commands"].append(run_record)
    if not command_ok(run_record):
        op["status"] = "failed" if run_commands else "ready_no_run"
        return op
    result = read_json(result_json) or {}
    op["status"] = result.get("status", "scored")
    op["claim_gate"] = (result.get("claim_analysis") or {}).get("claim_gate", {})
    op["participant_count"] = result.get("participant_count")
    op["response_count"] = result.get("response_count")
    return op


def run_r203(paths: dict[str, Path], scored_dir: Path, run_commands: bool) -> dict[str, Any]:
    r203_dir = scored_dir / "r203"
    result_json = r203_dir / "long-tail-promotion-r203.json"
    joined_csv = r203_dir / "long-tail-promotion-joined-r203.csv"
    cmd = [
        "python3",
        "docs/visexp/r203_long_tail_promotion_gate.py",
        "--out-dir",
        rel(r203_dir),
        "--labeler-1",
        rel(paths["r203_labeler_1"]),
        "--labeler-2",
        rel(paths["r203_labeler_2"]),
    ]
    if paths["r203_adjudication"].exists():
        cmd.extend(["--adjudication", rel(paths["r203_adjudication"])])
    op: dict[str, Any] = {
        "status": "not_run",
        "commands": [],
        "outputs": {
            "result_json": rel(result_json),
            "joined_csv": rel(joined_csv),
        },
    }
    run_record = command_result(cmd, run=run_commands)
    op["commands"].append(run_record)
    if not command_ok(run_record):
        op["status"] = "failed" if run_commands else "ready_no_run"
        return op
    result = read_json(result_json) or {}
    op["status"] = result.get("status", "scored")
    op["claim_gate"] = result.get("claim_gate", {})
    op["summary"] = result.get("summary", {})
    return op


def gate_summary(operations: dict[str, Any]) -> dict[str, Any]:
    r124_gate = operations.get("r124", {}).get("claim_gate") or {}
    r190_gate = operations.get("r190", {}).get("claim_gate") or {}
    r203_gate = operations.get("r203", {}).get("claim_gate") or {}
    r142_gate = operations.get("r142", {}).get("claim_gate") or {}
    return {
        "c5_supported": bool(r142_gate.get("c5_supported")),
        "c6_adequacy_supported": bool(r124_gate.get("adequacy_supported")),
        "canonicalization_quality_supported": bool(r190_gate.get("canonicalization_quality_supported")),
        "long_tail_promotion_review_supported": bool(r203_gate.get("long_tail_promotion_review_supported")),
        "canonical_map_updated": bool(r203_gate.get("canonical_map_updated")),
        "requires_real_human_data": not (
            bool(r142_gate.get("c5_supported"))
            and bool(r124_gate.get("adequacy_supported"))
        ),
    }


def pipeline_status(
    readiness: dict[str, Any],
    operations: dict[str, Any],
    gates: dict[str, Any],
    safety: dict[str, Any],
) -> str:
    if safety.get("unsafe"):
        return "unsafe_return_inputs"
    if not readiness["any_present"]:
        return "awaiting_human_inputs"
    if not readiness["any_ready"]:
        return "partial_human_inputs"
    if any(op.get("status") == "failed" for op in operations.values()):
        return "scoring_failed"
    if any(op.get("status") == "ready_no_run" for op in operations.values()):
        return "ready_to_score_no_run"
    if any(
        op.get("status") in {"needs_adjudication", "joined_not_ready_for_scoring"}
        or op.get("join_status") == "needs_adjudication"
        for op in operations.values()
    ):
        return "needs_adjudication"
    if any(op.get("status") == "human_labels_partial" for op in operations.values()):
        return "partial_human_inputs"
    if (
        gates["c5_supported"]
        or gates["c6_adequacy_supported"]
        or gates["canonicalization_quality_supported"]
        or gates.get("long_tail_promotion_review_supported")
    ):
        return "scored_human_inputs_with_supported_gate"
    return "scored_human_inputs_no_supported_gate"


def build_payload(args: argparse.Namespace) -> dict[str, Any]:
    source_commit = git(["rev-parse", "HEAD"])
    source_dirty = bool(git(["status", "--short"]))
    paths = {
        "r124_labeler_1": args.r124_labeler_1,
        "r124_labeler_2": args.r124_labeler_2,
        "r124_adjudication": args.r124_adjudication,
        "r190_labeler_1": args.r190_labeler_1,
        "r190_labeler_2": args.r190_labeler_2,
        "r190_adjudication": args.r190_adjudication,
        "r203_labeler_1": args.r203_labeler_1,
        "r203_labeler_2": args.r203_labeler_2,
        "r203_adjudication": args.r203_adjudication,
        "r142_responses": args.r142_responses,
    }
    scoring = {
        "r142_bundle": args.r142_bundle,
        "r142_answer_key": args.r142_answer_key,
        "r142_assignments": args.r142_assignments,
    }
    presence = input_presence(paths)
    readiness = group_readiness(presence)
    safety = input_safety(paths)
    operations: dict[str, Any] = {}
    if safety["unsafe"]:
        operations = {}
    elif readiness["r124"]["ready"]:
        operations["r124"] = run_r124(paths, args.scored_dir, not args.no_run)
    if not safety["unsafe"] and readiness["r190"]["ready"]:
        operations["r190"] = run_r190(paths, args.scored_dir, not args.no_run)
    if not safety["unsafe"] and readiness["r203"]["ready"]:
        operations["r203"] = run_r203(paths, args.scored_dir, not args.no_run)
    if not safety["unsafe"] and readiness["r142"]["ready"]:
        operations["r142"] = run_r142(paths, args.scored_dir, not args.no_run, scoring)

    gates = gate_summary(operations)
    status = pipeline_status(readiness, operations, gates, safety)
    required_inputs = {
        name: path_info(paths[name])
        for name in (
            "r124_labeler_1",
            "r124_labeler_2",
            "r190_labeler_1",
            "r190_labeler_2",
            "r203_labeler_1",
            "r203_labeler_2",
            "r142_responses",
        )
    }
    for name, fields in INPUT_VALUE_FIELDS.items():
        required_inputs[name]["filled_value_count"] = csv_filled_value_count(paths[name], fields)
        required_inputs[name]["value_fields_checked"] = fields
        required_inputs[name]["blank_or_missing"] = not required_inputs[name].get("filled_value_count")
    optional_inputs = {
        name: path_info(paths[name], optional=True)
        for name in ("r124_adjudication", "r190_adjudication", "r203_adjudication")
    }
    if safety["unsafe"]:
        content_status = "known_synthetic_or_forbidden_marker"
    elif any((info.get("filled_value_count") or 0) > 0 for info in required_inputs.values()):
        content_status = "has_filled_values"
    else:
        content_status = "present_but_blank" if readiness["any_present"] else "awaiting_inputs"
    return {
        "schema_version": 1,
        "run_id": "R195",
        "status": status,
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "input_contract": {
            "input_mode": input_mode(paths),
            "default_inbox": rel(DEFAULT_INBOX),
            "required_inputs": required_inputs,
            "optional_inputs": optional_inputs,
            "scoring_inputs": {
                name: path_info(path)
                for name, path in scoring.items()
            },
            "readiness": readiness,
            "safety": safety,
            "human_return_content_status": content_status,
        },
        "operations": operations,
        "claim_gate": gates,
        "artifacts": {
            "scored_dir": rel(args.scored_dir),
            "summary_json": rel(args.out_json),
            "summary_md": rel(args.out_md),
        },
        "claim_boundary": (
            "R195 is an ingestion/scoring pipeline. It does not create human labels or "
            "participant responses. Missing inputs keep C5/C6 unsupported; ready inputs "
            "are scored into an R195-specific directory without overwriting canonical gates. "
            "Known synthetic export markers are rejected before any scorer runs. "
            "R203 promotion labels can support a promotion-review gate only; they do not "
            "update the canonical map or substitute for C5/C6 evidence."
        ),
        "provenance": {
            "repo_commit": source_commit,
            "repo_dirty": source_dirty,
            "script": rel(Path(__file__).resolve()),
            "script_sha256": sha256_file(Path(__file__).resolve()),
        },
    }


def write_markdown(path: Path, payload: dict[str, Any]) -> None:
    readiness = payload["input_contract"]["readiness"]
    gates = payload["claim_gate"]
    lines = [
        "# R195 Human Evidence Pipeline",
        "",
        f"Status: `{payload['status']}`",
        f"Input mode: `{payload['input_contract']['input_mode']}`",
        f"Human return content: `{payload['input_contract']['human_return_content_status']}`",
        "",
        "## Inputs",
        "",
        "| input | exists | rows |",
        "|---|---:|---:|",
    ]
    for name, info in payload["input_contract"]["required_inputs"].items():
        lines.append(f"| `{name}` | {info['exists']} | {info.get('row_count', '')} |")
    lines.extend(
        [
            "",
            "## Readiness",
            "",
            f"- R124 ready: `{readiness['r124']['ready']}`; missing: `{', '.join(readiness['r124']['missing'])}`.",
            f"- R190 ready: `{readiness['r190']['ready']}`; missing: `{', '.join(readiness['r190']['missing'])}`.",
            f"- R203 ready: `{readiness['r203']['ready']}`; missing: `{', '.join(readiness['r203']['missing'])}`.",
            f"- R142 ready: `{readiness['r142']['ready']}`; missing: `{', '.join(readiness['r142']['missing'])}`.",
            f"- Safety status: `{payload['input_contract']['safety']['status']}`.",
            "",
            "## Claim Gates",
            "",
            f"- C5 supported: `{gates['c5_supported']}`.",
            f"- C6 adequacy supported: `{gates['c6_adequacy_supported']}`.",
            f"- Canonicalization quality supported: `{gates['canonicalization_quality_supported']}`.",
            f"- Long-tail promotion review supported: `{gates['long_tail_promotion_review_supported']}`.",
            f"- Canonical map updated: `{gates['canonical_map_updated']}`.",
            "",
            "## Operations",
            "",
        ]
    )
    if not payload["operations"]:
        if payload["input_contract"]["safety"]["unsafe"]:
            lines.append("No scorers ran because forbidden synthetic-return markers were present.")
        else:
            lines.append("No scorers ran because no complete input group was present.")
    else:
        for name, op in sorted(payload["operations"].items()):
            lines.append(f"- `{name}`: `{op.get('status')}`.")
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
    payload = build_payload(args)
    write_json(args.out_json, payload)
    write_markdown(args.out_md, payload)
    print(json.dumps({"status": payload["status"], "claim_gate": payload["claim_gate"]}, indent=2, sort_keys=True))
    return payload


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--r124-labeler-1", type=Path, default=DEFAULT_R124_LABELER_1)
    parser.add_argument("--r124-labeler-2", type=Path, default=DEFAULT_R124_LABELER_2)
    parser.add_argument("--r124-adjudication", type=Path, default=DEFAULT_R124_ADJUDICATION)
    parser.add_argument("--r190-labeler-1", type=Path, default=DEFAULT_R190_LABELER_1)
    parser.add_argument("--r190-labeler-2", type=Path, default=DEFAULT_R190_LABELER_2)
    parser.add_argument("--r190-adjudication", type=Path, default=DEFAULT_R190_ADJUDICATION)
    parser.add_argument("--r203-labeler-1", type=Path, default=DEFAULT_R203_LABELER_1)
    parser.add_argument("--r203-labeler-2", type=Path, default=DEFAULT_R203_LABELER_2)
    parser.add_argument("--r203-adjudication", type=Path, default=DEFAULT_R203_ADJUDICATION)
    parser.add_argument("--r142-responses", type=Path, default=DEFAULT_R142_RESPONSES)
    parser.add_argument("--r142-bundle", type=Path, default=R142_BUNDLE)
    parser.add_argument("--r142-answer-key", type=Path, default=R142_ANSWER_KEY)
    parser.add_argument("--r142-assignments", type=Path, default=R142_ASSIGNMENTS)
    parser.add_argument("--scored-dir", type=Path, default=DEFAULT_SCORED_DIR)
    parser.add_argument("--out-json", type=Path, default=DEFAULT_OUT_JSON)
    parser.add_argument("--out-md", type=Path, default=DEFAULT_OUT_MD)
    parser.add_argument("--no-run", action="store_true", help="Report readiness without running ready scorers")
    return parser


if __name__ == "__main__":
    run(build_parser().parse_args())
