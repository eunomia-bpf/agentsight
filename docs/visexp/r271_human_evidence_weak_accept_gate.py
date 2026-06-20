#!/usr/bin/env python3
"""R271: combined human-evidence gate for weak-accept review.

R268 handles C5 participant returns; R270 handles C6 human-label returns. This
gate runs both public-safe orchestrators, joins their aggregate claim gates, and
reports whether the human-evidence portion is ready for an independent OSDI
weak-accept review. It never reads or exports raw private rows.
"""

from __future__ import annotations

import argparse
import json
import shlex
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[1]
OUT_ROOT = SCRIPT_DIR / "out"

RUN_ID = "R271"
DEFAULT_OUT_DIR = OUT_ROOT / "human-evidence-weak-accept-gate-r271"
R268_SCRIPT = SCRIPT_DIR / "r268_c5_real_return_scoring_pipeline.py"
R270_SCRIPT = SCRIPT_DIR / "r270_c6_real_label_scoring_pipeline.py"
R268_JSON = OUT_ROOT / "c5-real-return-pipeline-r268" / "c5-real-return-pipeline-r268.json"
R270_JSON = OUT_ROOT / "c6-real-label-pipeline-r270" / "c6-real-label-pipeline-r270.json"


def rel(path: Path | None) -> str | None:
    if path is None:
        return None
    try:
        return str(path.resolve().relative_to(REPO_ROOT.resolve()))
    except Exception:
        return str(path)


def git(args: list[str]) -> str | None:
    try:
        proc = subprocess.run(
            ["git", *args],
            cwd=REPO_ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
    except Exception:
        return None
    if proc.returncode != 0:
        return None
    return proc.stdout.strip()


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def command_string(cmd: list[str]) -> str:
    return " ".join(shlex.quote(part) for part in cmd)


def run_cmd(cmd: list[str]) -> dict[str, Any]:
    proc = subprocess.run(cmd, cwd=REPO_ROOT, text=True, capture_output=True, check=False)
    return {
        "returncode": proc.returncode,
        "ok": proc.returncode == 0,
        "stdout_line_count": len(proc.stdout.splitlines()),
        "stderr_line_count": len(proc.stderr.splitlines()),
    }


def build_r268_cmd(args: argparse.Namespace) -> list[str]:
    cmd = ["python3", rel(R268_SCRIPT) or str(R268_SCRIPT)]
    if args.no_execute_pipelines:
        cmd.append("--no-execute")
    return cmd


def build_r270_cmd(args: argparse.Namespace) -> list[str]:
    cmd = ["python3", rel(R270_SCRIPT) or str(R270_SCRIPT)]
    if args.no_execute_pipelines:
        cmd.append("--no-execute")
    return cmd


def summarize_c5(payload: dict[str, Any]) -> dict[str, Any]:
    gate = payload.get("claim_gate") or {}
    private_input = payload.get("private_input") or {}
    execution = payload.get("execution") or {}
    return {
        "exists": bool(payload),
        "run_id": payload.get("run_id"),
        "status": payload.get("status"),
        "private_input_exists": private_input.get("exists"),
        "private_path_kind": private_input.get("path_kind"),
        "raw_private_rows_exported": execution.get("raw_private_rows_exported"),
        "private_hashes_exported": execution.get("private_hashes_exported"),
        "c5_supported": bool(gate.get("c5_supported")),
        "weak_accept_supported": bool(gate.get("weak_accept_supported")),
        "claim_gate": gate,
    }


def summarize_c6(payload: dict[str, Any]) -> dict[str, Any]:
    gate = payload.get("claim_gate") or {}
    private_input = payload.get("private_input") or {}
    execution = payload.get("execution") or {}
    return {
        "exists": bool(payload),
        "run_id": payload.get("run_id"),
        "status": payload.get("status"),
        "required_existing_count": private_input.get("required_existing_count"),
        "all_required_exist": private_input.get("all_required_exist"),
        "all_inputs_private_or_absent": private_input.get("all_inputs_private_or_absent"),
        "raw_private_rows_exported": execution.get("raw_private_rows_exported"),
        "private_hashes_exported": execution.get("private_hashes_exported"),
        "c6_adequacy_supported": bool(gate.get("c6_adequacy_supported")),
        "canonicalization_quality_supported": bool(gate.get("canonicalization_quality_supported")),
        "long_tail_promotion_review_supported": bool(gate.get("long_tail_promotion_review_supported")),
        "weak_accept_supported": bool(gate.get("weak_accept_supported")),
        "claim_gate": gate,
    }


def status_for(command_results: dict[str, Any], c5: dict[str, Any], c6: dict[str, Any]) -> str:
    for step in ("r268_c5", "r270_c6"):
        result = command_results.get(step)
        if result and not result.get("ok"):
            return f"pipeline_failed_at_{step}"
    if c5.get("c5_supported") and c6.get("c6_adequacy_supported"):
        return "human_evidence_ready_for_osdi_review"
    if c5.get("status") == "awaiting_private_c5_returns" and c6.get("status") == "awaiting_private_c6_labels":
        return "awaiting_private_c5_and_c6_returns"
    if c5.get("status") == "awaiting_private_c5_returns":
        return "awaiting_private_c5_returns"
    if c6.get("status") == "awaiting_private_c6_labels":
        return "awaiting_private_c6_labels"
    if c6.get("status") == "c6_needs_adjudication":
        return "awaiting_private_c6_adjudication"
    if c5.get("exists") or c6.get("exists"):
        return "human_evidence_present_but_not_supporting_gate"
    return "human_evidence_gate_not_run"


def build_payload(args: argparse.Namespace) -> dict[str, Any]:
    args.out_dir.mkdir(parents=True, exist_ok=True)
    r268_cmd = build_r268_cmd(args)
    r270_cmd = build_r270_cmd(args)
    command_results: dict[str, Any] = {}
    if not args.no_run_pipelines:
        command_results["r268_c5"] = run_cmd(r268_cmd)
        command_results["r270_c6"] = run_cmd(r270_cmd)

    r268_payload = read_json(R268_JSON)
    r270_payload = read_json(R270_JSON)
    c5 = summarize_c5(r268_payload)
    c6 = summarize_c6(r270_payload)
    status = status_for(command_results, c5, c6)
    human_evidence_ready = bool(c5.get("c5_supported") and c6.get("c6_adequacy_supported"))
    claim_gate = {
        "c5_supported": bool(c5.get("c5_supported")),
        "c6_adequacy_supported": bool(c6.get("c6_adequacy_supported")),
        "canonicalization_quality_supported": bool(c6.get("canonicalization_quality_supported")),
        "long_tail_promotion_review_supported": bool(c6.get("long_tail_promotion_review_supported")),
        "human_evidence_ready_for_osdi_review": human_evidence_ready,
        "weak_accept_supported": False,
        "requires_independent_osdi_review": human_evidence_ready,
        "requires_real_human_returns": not human_evidence_ready,
    }
    return {
        "schema_version": 1,
        "run_id": RUN_ID,
        "status": status,
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "execution": {
            "ran_pipelines": not args.no_run_pipelines,
            "no_execute_pipelines": args.no_execute_pipelines,
            "command_results": command_results,
            "raw_private_rows_exported": False,
            "private_hashes_exported": False,
        },
        "commands": {
            "r268_c5": {"argv": r268_cmd, "shell": command_string(r268_cmd)},
            "r270_c6": {"argv": r270_cmd, "shell": command_string(r270_cmd)},
        },
        "component_summaries": {
            "c5_r268": c5,
            "c6_r270": c6,
        },
        "claim_gate": claim_gate,
        "review_gate": {
            "next_review_command": None,
            "next_review_action": (
                "Run an independent OSDI subagent review over R271 and the updated "
                "public aggregate evidence after human_evidence_ready_for_osdi_review is true."
            ),
            "must_run_independent_subagent_after_real_results": human_evidence_ready,
            "review_is_not_replaced_by_this_gate": True,
        },
        "claim_boundary": (
            "R271 only joins public-safe aggregate gates from R268 and R270. It does not "
            "read or export raw private rows, create participant responses, create human labels, "
            "or replace the final independent OSDI review. Global weak-accept support remains "
            "false until real C5/C6 evidence is present and reviewed."
        ),
        "next_action": (
            "Collect private C5 responses and private C6 labels, run this script, resolve any "
            "C6 adjudication reported by R270, then run an independent OSDI review before "
            "updating public paper claims."
        ),
        "provenance": {
            "repo_commit": git(["rev-parse", "HEAD"]),
            "repo_dirty": bool(git(["status", "--short"])),
            "script": rel(Path(__file__).resolve()),
            "source_json": {
                "r268": rel(R268_JSON),
                "r270": rel(R270_JSON),
            },
        },
    }


def write_markdown(path: Path, payload: dict[str, Any]) -> None:
    gate = payload["claim_gate"]
    components = payload["component_summaries"]
    lines = [
        "# R271 Human Evidence Weak-Accept Gate",
        "",
        f"Status: `{payload['status']}`",
        "",
        "## Component Status",
        "",
        f"- C5/R268: `{components['c5_r268'].get('status')}`; supported=`{components['c5_r268'].get('c5_supported')}`.",
        f"- C6/R270: `{components['c6_r270'].get('status')}`; supported=`{components['c6_r270'].get('c6_adequacy_supported')}`.",
        "",
        "## Commands",
        "",
        "```bash",
        payload["commands"]["r268_c5"]["shell"],
        payload["commands"]["r270_c6"]["shell"],
        "```",
        "",
        "## Claim Gates",
        "",
        f"- C5 supported: `{gate['c5_supported']}`.",
        f"- C6 adequacy supported: `{gate['c6_adequacy_supported']}`.",
        f"- Human evidence ready for OSDI review: `{gate['human_evidence_ready_for_osdi_review']}`.",
        f"- Weak accept supported: `{gate['weak_accept_supported']}`.",
        f"- Requires independent OSDI review: `{gate['requires_independent_osdi_review']}`.",
        "",
        "## Boundary",
        "",
        payload["claim_boundary"],
        "",
        "## Next Action",
        "",
        payload["next_action"],
        "",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def write_command_file(path: Path, payload: dict[str, Any]) -> None:
    lines = [
        "# R271 combined human-evidence gate",
        "# This is the public-safe command to run after private C5/C6 returns are available.",
        "python3 docs/visexp/r271_human_evidence_weak_accept_gate.py",
        "",
        "# Component commands:",
        payload["commands"]["r268_c5"]["shell"],
        payload["commands"]["r270_c6"]["shell"],
        "",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def run(args: argparse.Namespace) -> dict[str, Any]:
    payload = build_payload(args)
    out_json = args.out_dir / "human-evidence-weak-accept-gate-r271.json"
    out_md = args.out_dir / "human-evidence-weak-accept-gate-r271.md"
    out_cmd = args.out_dir / "human-evidence-weak-accept-command-r271.txt"
    write_json(out_json, payload)
    write_markdown(out_md, payload)
    write_command_file(out_cmd, payload)
    print(
        json.dumps(
            {
                "status": payload["status"],
                "claim_gate": payload["claim_gate"],
                "out_json": rel(out_json),
            },
            indent=2,
            sort_keys=True,
        )
    )
    return payload


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--no-run-pipelines", action="store_true", help="Read existing R268/R270 outputs without rerunning them")
    parser.add_argument("--no-execute-pipelines", action="store_true", help="Ask R268/R270 to emit commands without scoring ready private inputs")
    return parser


if __name__ == "__main__":
    run(build_parser().parse_args())
