#!/usr/bin/env python3
"""Mechanical weak-accept human-evidence gate for AgentFlame.

This script does not collect or infer human data. It reads the existing R124
tag-adequacy artifacts and R142 user-task artifacts, then records whether the
paper can honestly claim C5/C6 support. LLM, subagent, author-filled mock, or
placeholder rows are never counted as human evidence.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_OUT_DIR = SCRIPT_DIR / "out"


def read_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(SCRIPT_DIR.parent.parent))
    except ValueError:
        return str(path)


def c6_gate(join_artifact: dict[str, Any] | None, score_artifact: dict[str, Any] | None) -> dict[str, Any]:
    blockers: list[str] = []
    next_inputs: list[str] = []
    if not join_artifact:
        blockers.append("missing R124 label-join artifact")
    if not score_artifact:
        blockers.append("missing R124 tag-adequacy scoring artifact")

    join_summary = (join_artifact or {}).get("summary") or {}
    score_summary = (score_artifact or {}).get("summary") or {}
    score_gate = (score_artifact or {}).get("claim_gate") or {}
    row_count = int(join_summary.get("row_count") or score_summary.get("packet_row_count") or 0)
    labeler_1 = int(join_summary.get("labeler_1_count") or 0)
    labeler_2 = int(join_summary.get("labeler_2_count") or 0)
    paired = int(join_summary.get("paired_label_count") or score_summary.get("both_labeler_count") or 0)
    final_labels = int(score_summary.get("final_label_count") or 0)

    complete_two_labelers = bool(join_summary.get("complete_two_labeler_sheets"))
    complete_adjudication = bool(join_summary.get("complete_adjudication", False))
    adequacy_supported = bool(score_gate.get("adequacy_supported"))

    if row_count == 0:
        blockers.append("R124 source packet has no rows")
    if not complete_two_labelers:
        blockers.append("two complete independent human labeler sheets are missing")
        next_inputs.append("two completed copies of docs/visexp/out/tag-adequacy-blinded-label-sheet-r124.csv")
    if complete_two_labelers and not complete_adjudication:
        blockers.append("R124 disagreements still need adjudication")
        next_inputs.append("completed docs/visexp/out/tag-adequacy-adjudication-template-r124.csv")
    if not adequacy_supported:
        blockers.append("score_tag_adequacy.py has not reported adequacy_supported=true")

    if adequacy_supported:
        status = "c6_supported"
    elif final_labels > 0 or paired > 0:
        status = "human_labels_present_but_not_supported"
    else:
        status = "ready_for_independent_label_collection"

    return {
        "claim": "C6",
        "status": status,
        "supported": adequacy_supported,
        "row_count": row_count,
        "labeler_1_count": labeler_1,
        "labeler_2_count": labeler_2,
        "paired_label_count": paired,
        "final_label_count": final_labels,
        "complete_two_labeler_sheets": complete_two_labelers,
        "complete_adjudication": complete_adjudication,
        "adequacy_supported": adequacy_supported,
        "blockers": blockers,
        "next_inputs": next_inputs,
        "commands_after_human_input": [
            (
                "python3 docs/visexp/r124_join_blinded_labels.py "
                "--labeler-1 <labeler1.csv> --labeler-2 <labeler2.csv>"
            ),
            (
                "python3 docs/visexp/r124_join_blinded_labels.py "
                "--labeler-1 <labeler1.csv> --labeler-2 <labeler2.csv> "
                "--adjudication docs/visexp/out/tag-adequacy-adjudication-template-r124.csv"
            ),
            (
                "python3 docs/visexp/score_tag_adequacy.py "
                "--labels docs/visexp/out/tag-adequacy-label-packet-r124-joined.csv"
            ),
        ],
    }


def c5_gate(preregistration: dict[str, Any] | None, results: dict[str, Any] | None) -> dict[str, Any]:
    blockers: list[str] = []
    next_inputs: list[str] = []
    if not preregistration:
        blockers.append("missing R142 preregistration artifact")
    if not results:
        blockers.append("missing R142 user-task results artifact")

    validation = (preregistration or {}).get("validation") or {}
    prereg_frozen = (preregistration or {}).get("status") == "frozen_before_collection"
    validation_ok = validation.get("status") == "ok"
    analysis = (results or {}).get("claim_analysis") or {}
    gate = analysis.get("claim_gate") or {}
    participant_count = int((results or {}).get("participant_count") or analysis.get("participant_count") or 0)
    response_count = int((results or {}).get("response_count") or analysis.get("response_count") or 0)
    c5_supported = bool(gate.get("c5_supported"))
    pilot_ready = bool(gate.get("pilot_ready"))
    paper_model_ready = bool(gate.get("paper_model_ready", False))

    if not prereg_frozen:
        blockers.append("R142 preregistration is not frozen")
    if not validation_ok:
        blockers.append("R142 preregistration validation is not ok")
    if participant_count == 0 or response_count == 0:
        blockers.append("real participant response CSV has not been collected")
        next_inputs.append("completed copy of docs/visexp/out/user-task-response-template.csv")
    if not c5_supported:
        blockers.append("score_user_task_results.py has not reported c5_supported=true")

    if c5_supported:
        status = "c5_supported"
    elif participant_count > 0:
        status = "participant_results_present_but_not_supported"
    else:
        status = "ready_for_participant_collection"

    return {
        "claim": "C5",
        "status": status,
        "supported": c5_supported,
        "preregistration_frozen": prereg_frozen,
        "preregistration_validation_ok": validation_ok,
        "participant_count": participant_count,
        "response_count": response_count,
        "pilot_ready": pilot_ready,
        "paper_model_ready": paper_model_ready,
        "c5_supported": c5_supported,
        "blockers": blockers,
        "next_inputs": next_inputs,
        "commands_after_human_input": [
            "python3 docs/visexp/score_user_task_results.py --responses <completed-responses.csv>",
        ],
    }


def overall_gate(c5: dict[str, Any], c6: dict[str, Any]) -> dict[str, Any]:
    human_evidence_supported = bool(c5["supported"] and c6["supported"])
    blockers = []
    if not c5["supported"]:
        blockers.append("C5 developer utility lacks supported human participant results")
    if not c6["supported"]:
        blockers.append("C6 tag adequacy lacks supported independent human labels")
    status = "human_evidence_ready_for_osdi_claim_audit" if human_evidence_supported else "not_weak_accept"
    return {
        "status": status,
        "human_evidence_supported": human_evidence_supported,
        "weak_accept_supported": False,
        "weak_accept_note": (
            "Even if C5 and C6 pass, final weak-accept wording still requires a claim-verdict and paper audit. "
            "With either C5 or C6 missing, weak accept is not supportable."
        ),
        "blockers": blockers,
        "disallowed_evidence": [
            "subagent review",
            "LLM-filled labels",
            "author-filled mock responses",
            "placeholder response rows",
            "syntax-only tag validity",
        ],
    }


def build_result(args: argparse.Namespace) -> dict[str, Any]:
    out_dir = Path(args.out_dir)
    join_path = Path(args.label_join)
    adequacy_path = Path(args.tag_adequacy)
    prereg_path = Path(args.user_preregistration)
    user_results_path = Path(args.user_results)
    c6 = c6_gate(read_json(join_path), read_json(adequacy_path))
    c5 = c5_gate(read_json(prereg_path), read_json(user_results_path))
    overall = overall_gate(c5, c6)
    return {
        "schema_version": 1,
        "run_id": "R184",
        "claim": "C5,C6 weak-accept human evidence gate",
        "status": overall["status"],
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source_artifacts": {
            "tag_adequacy_label_join": rel(join_path),
            "tag_adequacy_scoring": rel(adequacy_path),
            "user_task_preregistration": rel(prereg_path),
            "user_task_results": rel(user_results_path),
        },
        "c5_user_utility": c5,
        "c6_tag_adequacy": c6,
        "overall": overall,
        "claim_boundary": (
            "R184 is a gate/checklist artifact only. It does not strengthen C5 or C6 until real human "
            "participant responses and independent human tag labels satisfy their existing scorers."
        ),
        "output_dir": rel(out_dir),
    }


def write_markdown(path: Path, result: dict[str, Any]) -> None:
    c5 = result["c5_user_utility"]
    c6 = result["c6_tag_adequacy"]
    overall = result["overall"]
    lines = [
        "# R184 Weak-Accept Human Evidence Gate",
        "",
        f"Status: `{result['status']}`",
        f"Generated: {result['generated_at']}",
        "",
        "## Verdict",
        "",
        f"- Human evidence supported: `{overall['human_evidence_supported']}`.",
        f"- Weak accept supported now: `{overall['weak_accept_supported']}`.",
        f"- Boundary: {result['claim_boundary']}",
        "",
        "## C5 Developer Utility",
        "",
        f"- Status: `{c5['status']}`.",
        f"- Participants: {c5['participant_count']}.",
        f"- Responses: {c5['response_count']}.",
        f"- Pilot ready: `{c5['pilot_ready']}`.",
        f"- C5 supported: `{c5['c5_supported']}`.",
        f"- Blockers: {c5['blockers']}.",
        "",
        "## C6 Tag Adequacy",
        "",
        f"- Status: `{c6['status']}`.",
        f"- Rows: {c6['row_count']}.",
        f"- Labeler 1 labels: {c6['labeler_1_count']}.",
        f"- Labeler 2 labels: {c6['labeler_2_count']}.",
        f"- Final labels: {c6['final_label_count']}.",
        f"- Adequacy supported: `{c6['adequacy_supported']}`.",
        f"- Blockers: {c6['blockers']}.",
        "",
        "## Required Human Inputs",
        "",
        "- C5: " + (", ".join(c5["next_inputs"]) if c5["next_inputs"] else "none"),
        "- C6: " + (", ".join(c6["next_inputs"]) if c6["next_inputs"] else "none"),
        "",
        "## Commands After Human Input",
        "",
    ]
    for command in c6["commands_after_human_input"] + c5["commands_after_human_input"]:
        lines.append(f"- `{command}`")
    lines.extend(
        [
            "",
            "## Disallowed Evidence",
            "",
        ]
    )
    for item in overall["disallowed_evidence"]:
        lines.append(f"- {item}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run(args: argparse.Namespace) -> dict[str, Any]:
    result = build_result(args)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / "weak-accept-gate-r184.json"
    md_path = out_dir / "weak-accept-gate-r184.md"
    json_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    write_markdown(md_path, result)
    print(json.dumps({"status": result["status"], "c5": result["c5_user_utility"]["status"], "c6": result["c6_tag_adequacy"]["status"]}, indent=2))
    return result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", default=str(DEFAULT_OUT_DIR))
    parser.add_argument("--label-join", default=str(DEFAULT_OUT_DIR / "tag-adequacy-label-join-r124.json"))
    parser.add_argument("--tag-adequacy", default=str(DEFAULT_OUT_DIR / "tag-adequacy-results-r124.json"))
    parser.add_argument("--user-preregistration", default=str(DEFAULT_OUT_DIR / "user-task-preregistration-r142.json"))
    parser.add_argument("--user-results", default=str(DEFAULT_OUT_DIR / "user-task-results.json"))
    return parser


if __name__ == "__main__":
    run(build_parser().parse_args())
