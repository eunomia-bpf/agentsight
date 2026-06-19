#!/usr/bin/env python3
"""R255: verify the R249 paper-scale C5 package is scoreable through R195.

R249 creates a 12-participant paper-scale response template with a nondefault
assignment file. R195 is the post-collection scoring entry point. R255 checks
that R195 can score the R249 blank response template when given the R249
assignment file, and that the same response template is rejected when R195 is
left on the old R142 pilot assignment. The blank template still records zero
real responses and cannot support C5.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[1]
OUT_ROOT = SCRIPT_DIR / "out"
DEFAULT_OUT_DIR = OUT_ROOT / "human-evidence-paper-bridge-r255"

RUN_ID = "R255"
R249_MANIFEST = OUT_ROOT / "user-task-paper-r249" / "manifest.json"
R249_RESPONSES = OUT_ROOT / "user-task-paper-r249" / "responses" / "user-task-response-template-r249-paper.csv"
R249_ASSIGNMENTS = OUT_ROOT / "user-task-paper-r249" / "user-task-assignments-r249-paper.csv"
R142_ASSIGNMENTS = OUT_ROOT / "user-task-assignments.csv"
R142_BUNDLE = OUT_ROOT / "user-task-benchmark.json"
R142_ANSWER_KEY = OUT_ROOT / "user-task-answer-key.csv"


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT.resolve()))
    except Exception:
        return str(path)


def git(args: list[str]) -> str | None:
    try:
        return subprocess.check_output(["git", *args], cwd=REPO_ROOT, text=True, stderr=subprocess.DEVNULL).strip()
    except Exception:
        return None


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def run_cmd(cmd: list[str]) -> dict[str, Any]:
    proc = subprocess.run(cmd, cwd=REPO_ROOT, text=True, capture_output=True)
    return {
        "cmd": cmd,
        "cwd": rel(REPO_ROOT),
        "returncode": proc.returncode,
        "stdout_tail": proc.stdout[-3000:],
        "stderr_tail": proc.stderr[-3000:],
    }


def file_meta(path: Path) -> dict[str, Any]:
    return {
        "path": rel(path),
        "exists": path.exists(),
        "size_bytes": path.stat().st_size if path.exists() else None,
    }


def run_r195_case(out_dir: Path, case_name: str, assignments: Path) -> dict[str, Any]:
    case_dir = out_dir / "cases" / case_name
    out_json = case_dir / "r195.json"
    out_md = case_dir / "r195.md"
    scored_dir = case_dir / "scored"
    cmd = [
        "python3",
        "docs/visexp/r195_human_evidence_pipeline.py",
        "--r142-responses",
        rel(R249_RESPONSES),
        "--r142-bundle",
        rel(R142_BUNDLE),
        "--r142-answer-key",
        rel(R142_ANSWER_KEY),
        "--r142-assignments",
        rel(assignments),
        "--scored-dir",
        rel(scored_dir),
        "--out-json",
        rel(out_json),
        "--out-md",
        rel(out_md),
    ]
    result = run_cmd(cmd)
    payload = read_json(out_json) if out_json.exists() else {}
    return {
        "name": case_name,
        "assignment_file": rel(assignments),
        "command": result,
        "payload_path": rel(out_json),
        "markdown_path": rel(out_md),
        "payload": payload,
    }


def r142_operation(case: dict[str, Any]) -> dict[str, Any]:
    return ((case.get("payload") or {}).get("operations") or {}).get("r142") or {}


def r142_command(case: dict[str, Any]) -> dict[str, Any]:
    commands = r142_operation(case).get("commands") or []
    return commands[0] if commands else {}


def build_summary(out_dir: Path) -> dict[str, Any]:
    source_commit = git(["rev-parse", "HEAD"])
    source_dirty = bool(git(["status", "--short"]))
    manifest = read_json(R249_MANIFEST)
    paper_case = run_r195_case(out_dir, "paper-scale-blank-with-r249-assignment", R249_ASSIGNMENTS)
    wrong_case = run_r195_case(out_dir, "paper-scale-blank-with-r142-assignment", R142_ASSIGNMENTS)

    paper_payload = paper_case["payload"]
    paper_op = r142_operation(paper_case)
    paper_cmd = r142_command(paper_case)
    wrong_payload = wrong_case["payload"]
    wrong_op = r142_operation(wrong_case)
    wrong_cmd = r142_command(wrong_case)

    gates = {
        "r249_manifest_present": manifest.get("status") == "paper_scale_launch_ready_no_responses",
        "r249_has_12_participant_packets": manifest.get("participant_packet_count") == 12,
        "r249_template_has_168_rows": (manifest.get("response_template") or {}).get("rows") == 168,
        "paper_assignment_case_r195_ok": paper_case["command"]["returncode"] == 0,
        "paper_assignment_case_scored_no_supported_gate": paper_payload.get("status")
        == "scored_human_inputs_no_supported_gate",
        "paper_assignment_r142_empty": paper_op.get("status") == "participant_results_empty",
        "paper_assignment_scorer_ok": paper_cmd.get("returncode") == 0,
        "paper_assignment_uses_r249_assignments": (
            paper_op.get("scoring_inputs") or {}
        ).get("assignments")
        == rel(R249_ASSIGNMENTS),
        "paper_assignment_c5_false": (
            (paper_payload.get("claim_gate") or {}).get("c5_supported") is False
            and (paper_op.get("claim_gate") or {}).get("c5_supported") is False
        ),
        "paper_assignment_blank_not_human_evidence": paper_payload.get("input_contract", {}).get(
            "human_return_content_status"
        )
        == "present_but_blank",
        "wrong_assignment_case_r195_ok": wrong_case["command"]["returncode"] == 0,
        "wrong_assignment_case_failed": wrong_payload.get("status") == "scoring_failed",
        "wrong_assignment_scorer_rejected": wrong_op.get("status") == "failed"
        and wrong_cmd.get("returncode") not in (None, 0),
        "wrong_assignment_uses_r142_assignments": (
            wrong_op.get("scoring_inputs") or {}
        ).get("assignments")
        == rel(R142_ASSIGNMENTS),
        "wrong_assignment_c5_false": (wrong_payload.get("claim_gate") or {}).get("c5_supported") is False,
    }
    required = list(gates)
    status = "passed" if all(gates.values()) else "failed"
    summary = {
        "schema_version": 1,
        "run_id": RUN_ID,
        "status": status,
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "claim": "C5 paper-scale post-collection scoring bridge",
        "source_artifacts": {
            "r249_manifest": file_meta(R249_MANIFEST),
            "r249_responses": file_meta(R249_RESPONSES),
            "r249_assignments": file_meta(R249_ASSIGNMENTS),
            "r142_assignments": file_meta(R142_ASSIGNMENTS),
            "r142_bundle": file_meta(R142_BUNDLE),
            "r142_answer_key": file_meta(R142_ANSWER_KEY),
        },
        "cases": {
            "paper_scale_blank_with_r249_assignment": paper_case,
            "paper_scale_blank_with_r142_assignment": wrong_case,
        },
        "gates": gates,
        "required_gates": required,
        "claim_gate": {
            "paper_scale_r195_bridge_supported": status == "passed",
            "c5_supported": False,
            "weak_accept_supported": False,
            "real_participant_responses_added": 0,
            "requires_real_participants": True,
        },
        "claim_boundary": (
            "R255 proves only that the R249 paper-scale blank response template is "
            "wired to R195 when the R249 assignment file is supplied, and that the "
            "old R142 assignment is rejected. It records zero real participant "
            "responses and cannot support C5 or weak accept."
        ),
        "provenance": {
            "repo_commit": source_commit,
            "repo_dirty": source_dirty,
            "script": rel(Path(__file__).resolve()),
            "raw_trace_read": False,
            "llm_called": False,
            "participant_responses_added": 0,
            "human_labels_added": 0,
        },
    }
    return summary


def write_markdown(path: Path, summary: dict[str, Any]) -> None:
    gates = summary["gates"]
    lines = [
        "# R255 Paper-Scale R195 Bridge",
        "",
        f"Status: `{summary['status']}`",
        "",
        "R255 verifies that the R249 paper-scale blank response template can be",
        "processed by R195 only when the R249 assignment file is supplied. It also",
        "checks that using the older R142 assignment fails instead of silently",
        "scoring the wrong study design.",
        "",
        "## Gates",
        "",
        "| Gate | Passed |",
        "|---|---:|",
    ]
    for name, value in gates.items():
        lines.append(f"| `{name}` | `{value}` |")
    lines.extend(
        [
            "",
            "## Case Summary",
            "",
            f"- Paper assignment case: `{summary['cases']['paper_scale_blank_with_r249_assignment']['payload'].get('status')}`.",
            f"- Wrong assignment case: `{summary['cases']['paper_scale_blank_with_r142_assignment']['payload'].get('status')}`.",
            "",
            "## Boundary",
            "",
            summary["claim_boundary"],
            "",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def run(args: argparse.Namespace) -> dict[str, Any]:
    out_dir = Path(args.out_dir).resolve()
    shutil.rmtree(out_dir, ignore_errors=True)
    out_dir.mkdir(parents=True, exist_ok=True)
    summary = build_summary(out_dir)
    out_json = out_dir / "paper-scale-r195-bridge-r255.json"
    out_md = out_dir / "paper-scale-r195-bridge-r255.md"
    summary["artifacts"] = {
        "summary_json": rel(out_json),
        "summary_md": rel(out_md),
    }
    write_json(out_json, summary)
    write_markdown(out_md, summary)
    print(
        json.dumps(
            {
                "run_id": RUN_ID,
                "status": summary["status"],
                "paper_bridge": summary["claim_gate"]["paper_scale_r195_bridge_supported"],
                "c5_supported": summary["claim_gate"]["c5_supported"],
            },
            sort_keys=True,
        )
    )
    if summary["status"] != "passed":
        raise SystemExit(1)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", default=str(DEFAULT_OUT_DIR))
    run(parser.parse_args())


if __name__ == "__main__":
    main()
