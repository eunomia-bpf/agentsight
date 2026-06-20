#!/usr/bin/env python3
"""R268: one-command private C5 return scoring pipeline.

This wrapper is intentionally a logistics/orchestration artifact. It gives the
paper-scale C5 user-task study a single command to run after real participant
responses are returned, while keeping raw private rows and hashes out of public
docs/ outputs.
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

DEFAULT_OUT_DIR = OUT_ROOT / "c5-real-return-pipeline-r268"
DEFAULT_PRIVATE_ROOT = REPO_ROOT / "private" / "completed-paper-scale-r264"
DEFAULT_C5_RESPONSES = DEFAULT_PRIVATE_ROOT / "c5" / "user-task-response-template-r249-paper.csv"
DEFAULT_PRIVATE_R264_DIR = DEFAULT_PRIVATE_ROOT / "r264-intake"
DEFAULT_PRIVATE_R195_DIR = DEFAULT_PRIVATE_ROOT / "r195-scored"
DEFAULT_PUBLIC_R266_DIR = DEFAULT_OUT_DIR / "public-summary-r266"

R264_SCRIPT = SCRIPT_DIR / "r264_human_return_intake_preflight.py"
R195_SCRIPT = SCRIPT_DIR / "r195_human_evidence_pipeline.py"
R266_SCRIPT = SCRIPT_DIR / "r266_real_human_evidence_public_summary_gate.py"
R142_BUNDLE = OUT_ROOT / "user-task-benchmark.json"
R142_ANSWER_KEY = OUT_ROOT / "user-task-answer-key.csv"
R249_ASSIGNMENTS = OUT_ROOT / "user-task-paper-r249" / "user-task-assignments-r249-paper.csv"


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


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def command_string(cmd: list[str]) -> str:
    return " ".join(shlex.quote(part) for part in cmd)


def private_path_status(path: Path) -> dict[str, Any]:
    exists = path.exists()
    is_private = False
    try:
        path.resolve().relative_to((REPO_ROOT / "private").resolve())
        is_private = True
    except Exception:
        is_private = False
    return {
        "path_kind": "private" if is_private else "non_private",
        "exists": exists,
        "safe_to_score": bool(exists and is_private),
        "public_export_policy": "existence_and_aggregate_status_only",
    }


def base_r195_paths(args: argparse.Namespace) -> tuple[Path, Path]:
    return (
        args.r195_scored_dir / "human-evidence-pipeline-r195.json",
        args.r195_scored_dir / "human-evidence-pipeline-r195.md",
    )


def build_r264_cmd(args: argparse.Namespace) -> list[str]:
    return [
        "python3",
        rel(R264_SCRIPT) or str(R264_SCRIPT),
        "--out-dir",
        rel(args.r264_out_dir) or str(args.r264_out_dir),
        "--c5-responses",
        rel(args.c5_responses) or str(args.c5_responses),
        "--r142-bundle",
        rel(args.r142_bundle) or str(args.r142_bundle),
        "--r142-answer-key",
        rel(args.r142_answer_key) or str(args.r142_answer_key),
        "--r142-assignments",
        rel(args.r142_assignments) or str(args.r142_assignments),
        "--r195-scored-dir",
        rel(args.r195_scored_dir) or str(args.r195_scored_dir),
    ]


def build_r195_cmd(args: argparse.Namespace) -> list[str]:
    out_json, out_md = base_r195_paths(args)
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
        "--scored-dir",
        rel(args.r195_scored_dir) or str(args.r195_scored_dir),
        "--out-json",
        rel(out_json) or str(out_json),
        "--out-md",
        rel(out_md) or str(out_md),
    ]


def build_r266_cmd(args: argparse.Namespace) -> list[str]:
    out_json, _out_md = base_r195_paths(args)
    return [
        "python3",
        rel(R266_SCRIPT) or str(R266_SCRIPT),
        "--r195-json",
        rel(out_json) or str(out_json),
        "--out-dir",
        rel(args.r266_out_dir) or str(args.r266_out_dir),
    ]


def run_cmd(cmd: list[str]) -> dict[str, Any]:
    proc = subprocess.run(cmd, cwd=REPO_ROOT, text=True, capture_output=True, check=False)
    return {
        "returncode": proc.returncode,
        "ok": proc.returncode == 0,
        "stdout_line_count": len(proc.stdout.splitlines()),
        "stderr_line_count": len(proc.stderr.splitlines()),
    }


def summarize_r264(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"exists": False}
    payload = read_json(path)
    c5 = payload.get("c5_response_preflight") or {}
    labels = payload.get("c6_label_preflight") or {}
    groups = labels.get("groups") or {}
    return {
        "exists": True,
        "status": payload.get("status"),
        "c5": {
            "status": c5.get("status"),
            "ready_for_r195": c5.get("ready_for_r195"),
            "row_count": c5.get("row_count"),
            "expected_row_count": c5.get("expected_row_count"),
            "placeholder_rows": c5.get("placeholder_rows"),
            "error_count": len(c5.get("errors") or []),
        },
        "c6_groups": {
            name: {
                "status": group.get("status"),
                "ready_for_r195": group.get("ready_for_r195"),
                "present_count": len(group.get("present") or []),
            }
            for name, group in sorted(groups.items())
        },
        "safety_all_inputs_safe": (payload.get("safety") or {}).get("all_inputs_safe"),
        "privacy_guard_passed": (payload.get("privacy_guard") or {}).get("passed"),
        "claim_gate": payload.get("claim_gate") or {},
    }


def summarize_r195(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"exists": False}
    payload = read_json(path)
    contract = payload.get("input_contract") or {}
    readiness = contract.get("readiness") or {}
    operations = payload.get("operations") or {}
    return {
        "exists": True,
        "status": payload.get("status"),
        "input_mode": contract.get("input_mode"),
        "human_return_content_status": contract.get("human_return_content_status"),
        "readiness": {
            name: {"ready": group.get("ready"), "missing_count": len(group.get("missing") or [])}
            for name, group in readiness.items()
            if isinstance(group, dict)
        },
        "operation_statuses": {
            name: op.get("status")
            for name, op in sorted(operations.items())
            if isinstance(op, dict)
        },
        "claim_gate": payload.get("claim_gate") or {},
    }


def summarize_r266(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"exists": False}
    payload = read_json(path)
    return {
        "exists": True,
        "status": payload.get("status"),
        "claim_gate": payload.get("claim_gate") or {},
        "source": {
            "r195_status": ((payload.get("source") or {}).get("r195_status")),
            "r195_path_kind": ((payload.get("source") or {}).get("r195_path_kind")),
        },
    }


def empty_gate() -> dict[str, bool]:
    return {
        "c5_supported": False,
        "c6_adequacy_supported": False,
        "canonicalization_quality_supported": False,
        "long_tail_promotion_review_supported": False,
        "weak_accept_supported": False,
        "public_claim_update_allowed": False,
        "requires_real_human_returns": True,
    }


def status_for(
    private_status: dict[str, Any],
    executed: bool,
    r264_summary: dict[str, Any],
    r195_summary: dict[str, Any],
    r266_summary: dict[str, Any],
    command_results: dict[str, Any],
) -> str:
    if not private_status["exists"]:
        return "awaiting_private_c5_returns"
    if not private_status["safe_to_score"]:
        return "unsafe_non_private_c5_input"
    if not executed:
        return "ready_for_c5_scoring_not_executed"
    for step in ("r264", "r195", "r266"):
        result = command_results.get(step)
        if result and not result.get("ok"):
            return f"pipeline_failed_at_{step}"
    c5 = r264_summary.get("c5") or {}
    if c5.get("ready_for_r195") is not True:
        return "c5_return_not_ready_for_r195"
    if r195_summary.get("exists") and not r266_summary.get("exists"):
        return "r195_scored_without_public_summary"
    gate = r266_summary.get("claim_gate") or {}
    if gate.get("c5_supported"):
        return "c5_public_summary_ready"
    if r195_summary.get("exists"):
        return "c5_scored_no_supported_gate"
    return "c5_pipeline_no_score"


def build_payload(args: argparse.Namespace) -> dict[str, Any]:
    args.out_dir.mkdir(parents=True, exist_ok=True)
    private_status = private_path_status(args.c5_responses)
    r264_cmd = build_r264_cmd(args)
    r195_cmd = build_r195_cmd(args)
    r266_cmd = build_r266_cmd(args)

    command_results: dict[str, Any] = {}
    executed = bool(private_status["safe_to_score"] and not args.no_execute)
    if executed:
        command_results["r264"] = run_cmd(r264_cmd)
        r264_json = args.r264_out_dir / "human-return-intake-r264.json"
        r264_summary = summarize_r264(r264_json)
        c5_ready = (r264_summary.get("c5") or {}).get("ready_for_r195") is True
        preflight_safe = bool(
            r264_summary.get("safety_all_inputs_safe")
            and r264_summary.get("privacy_guard_passed")
        )
        if command_results["r264"]["ok"] and c5_ready and preflight_safe:
            command_results["r195"] = run_cmd(r195_cmd)
            if command_results["r195"]["ok"]:
                command_results["r266"] = run_cmd(r266_cmd)
    else:
        r264_json = args.r264_out_dir / "human-return-intake-r264.json"

    r195_json, _r195_md = base_r195_paths(args)
    r266_json = args.r266_out_dir / "human-evidence-public-summary-r266.json"
    r264_summary = summarize_r264(r264_json)
    r195_summary = summarize_r195(r195_json)
    r266_summary = summarize_r266(r266_json)
    status = status_for(private_status, executed, r264_summary, r195_summary, r266_summary, command_results)
    promoted_gate = r266_summary.get("claim_gate") if r266_summary.get("exists") else None
    claim_gate = {
        **empty_gate(),
        **(promoted_gate or {}),
    }
    claim_gate["weak_accept_supported"] = bool(
        claim_gate.get("c5_supported") and claim_gate.get("c6_adequacy_supported")
    )
    return {
        "schema_version": 1,
        "run_id": "R268",
        "status": status,
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "private_input": private_status,
        "execution": {
            "executed": executed,
            "no_execute": args.no_execute,
            "command_results": command_results,
            "raw_private_rows_exported": False,
            "private_hashes_exported": False,
        },
        "commands": {
            "r264_preflight": {"argv": r264_cmd, "shell": command_string(r264_cmd)},
            "r195_score": {"argv": r195_cmd, "shell": command_string(r195_cmd)},
            "r266_public_summary": {"argv": r266_cmd, "shell": command_string(r266_cmd)},
        },
        "step_summaries": {
            "r264_preflight": r264_summary,
            "r195_score": r195_summary,
            "r266_public_summary": r266_summary,
        },
        "claim_gate": claim_gate,
        "claim_boundary": (
            "R268 orchestrates private C5 user-task returns through R264, R195, and R266. "
            "It can support a public C5 summary only when real private C5 responses exist "
            "and R195 scores them. It never supports C6 or weak accept by itself."
        ),
        "next_action": (
            "Collect the 168-row paper-scale C5 response CSV under the private return path, "
            "then rerun this script. C6 label evidence must still be collected and scored "
            "separately for weak-accept support."
        ),
        "provenance": {
            "repo_commit": git(["rev-parse", "HEAD"]),
            "repo_dirty": bool(git(["status", "--short"])),
            "script": rel(Path(__file__).resolve()),
        },
    }


def write_markdown(path: Path, payload: dict[str, Any]) -> None:
    gate = payload["claim_gate"]
    private_input = payload["private_input"]
    lines = [
        "# R268 C5 Real Return Scoring Pipeline",
        "",
        f"Status: `{payload['status']}`",
        "",
        "## Private Input",
        "",
        f"- Exists: `{private_input['exists']}`.",
        f"- Path kind: `{private_input['path_kind']}`.",
        f"- Safe to score: `{private_input['safe_to_score']}`.",
        f"- Public export policy: `{private_input['public_export_policy']}`.",
        "",
        "## Commands",
        "",
        "```bash",
        payload["commands"]["r264_preflight"]["shell"],
        payload["commands"]["r195_score"]["shell"],
        payload["commands"]["r266_public_summary"]["shell"],
        "```",
        "",
        "## Step Summaries",
        "",
    ]
    for name, summary in payload["step_summaries"].items():
        lines.append(f"- `{name}`: exists=`{summary.get('exists')}`, status=`{summary.get('status')}`.")
    lines.extend(
        [
            "",
            "## Claim Gates",
            "",
            f"- C5 supported: `{gate['c5_supported']}`.",
            f"- C6 adequacy supported: `{gate['c6_adequacy_supported']}`.",
            f"- Weak accept supported: `{gate['weak_accept_supported']}`.",
            f"- Public claim update allowed: `{gate['public_claim_update_allowed']}`.",
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
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def write_command_file(path: Path, payload: dict[str, Any]) -> None:
    lines = [
        "# R268 one-command C5 return scoring pipeline",
        "# Place real private C5 returns first; this file is a command template, not evidence.",
        "python3 docs/visexp/r268_c5_real_return_scoring_pipeline.py",
        "",
        "# Expanded steps, for debugging only:",
        payload["commands"]["r264_preflight"]["shell"],
        payload["commands"]["r195_score"]["shell"],
        payload["commands"]["r266_public_summary"]["shell"],
        "",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def run(args: argparse.Namespace) -> dict[str, Any]:
    payload = build_payload(args)
    out_json = args.out_dir / "c5-real-return-pipeline-r268.json"
    out_md = args.out_dir / "c5-real-return-pipeline-r268.md"
    out_cmd = args.out_dir / "c5-return-scoring-command-r268.txt"
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
    parser.add_argument("--c5-responses", type=Path, default=DEFAULT_C5_RESPONSES)
    parser.add_argument("--r264-out-dir", type=Path, default=DEFAULT_PRIVATE_R264_DIR)
    parser.add_argument("--r195-scored-dir", type=Path, default=DEFAULT_PRIVATE_R195_DIR)
    parser.add_argument("--r266-out-dir", type=Path, default=DEFAULT_PUBLIC_R266_DIR)
    parser.add_argument("--r142-bundle", type=Path, default=R142_BUNDLE)
    parser.add_argument("--r142-answer-key", type=Path, default=R142_ANSWER_KEY)
    parser.add_argument("--r142-assignments", type=Path, default=R249_ASSIGNMENTS)
    parser.add_argument("--no-execute", action="store_true", help="Emit commands without running the scoring chain")
    return parser


if __name__ == "__main__":
    run(build_parser().parse_args())
