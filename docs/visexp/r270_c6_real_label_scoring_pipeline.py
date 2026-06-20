#!/usr/bin/env python3
"""R270: one-command private C6 label scoring pipeline.

This wrapper orchestrates completed private R124/R190/R203 human-label returns
through R264, R195, and R266. It is a logistics artifact until real labeler CSVs
exist; public outputs expose only readiness, aggregate statuses, and command
templates.
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

DEFAULT_OUT_DIR = OUT_ROOT / "c6-real-label-pipeline-r270"
DEFAULT_PRIVATE_ROOT = REPO_ROOT / "private" / "completed-paper-scale-r264"
DEFAULT_C5_RESPONSES = DEFAULT_PRIVATE_ROOT / "c5" / "user-task-response-template-r249-paper.csv"
DEFAULT_C6_ROOT = DEFAULT_PRIVATE_ROOT / "c6"
DEFAULT_R124_LABELER_1 = DEFAULT_C6_ROOT / "L01" / "r124-labeler-1.csv"
DEFAULT_R124_LABELER_2 = DEFAULT_C6_ROOT / "L02" / "r124-labeler-2.csv"
DEFAULT_R190_LABELER_1 = DEFAULT_C6_ROOT / "L01" / "r190-labeler-1.csv"
DEFAULT_R190_LABELER_2 = DEFAULT_C6_ROOT / "L02" / "r190-labeler-2.csv"
DEFAULT_R203_LABELER_1 = DEFAULT_C6_ROOT / "L01" / "r203-labeler-1.csv"
DEFAULT_R203_LABELER_2 = DEFAULT_C6_ROOT / "L02" / "r203-labeler-2.csv"
DEFAULT_R124_ADJUDICATION = DEFAULT_C6_ROOT / "adjudication" / "r124-adjudication.csv"
DEFAULT_R190_ADJUDICATION = DEFAULT_C6_ROOT / "adjudication" / "r190-adjudication.csv"
DEFAULT_R203_ADJUDICATION = DEFAULT_C6_ROOT / "adjudication" / "r203-adjudication.csv"
DEFAULT_PRIVATE_R264_DIR = DEFAULT_PRIVATE_ROOT / "r264-c6-intake"
DEFAULT_PRIVATE_R195_DIR = DEFAULT_PRIVATE_ROOT / "r195-scored"
DEFAULT_PUBLIC_R266_DIR = DEFAULT_OUT_DIR / "public-summary-r266"

R264_SCRIPT = SCRIPT_DIR / "r264_human_return_intake_preflight.py"
R195_SCRIPT = SCRIPT_DIR / "r195_human_evidence_pipeline.py"
R266_SCRIPT = SCRIPT_DIR / "r266_real_human_evidence_public_summary_gate.py"
R142_BUNDLE = OUT_ROOT / "user-task-benchmark.json"
R142_ANSWER_KEY = OUT_ROOT / "user-task-answer-key.csv"
R249_ASSIGNMENTS = OUT_ROOT / "user-task-paper-r249" / "user-task-assignments-r249-paper.csv"

REQUIRED_LABEL_ARGS = (
    "r124_labeler_1",
    "r124_labeler_2",
    "r190_labeler_1",
    "r190_labeler_2",
    "r203_labeler_1",
    "r203_labeler_2",
)
OPTIONAL_ADJUDICATION_ARGS = (
    "r124_adjudication",
    "r190_adjudication",
    "r203_adjudication",
)


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


def path_kind(path: Path) -> str:
    try:
        path.resolve().relative_to((REPO_ROOT / "private").resolve())
        return "private"
    except Exception:
        return "non_private"


def input_paths(args: argparse.Namespace) -> dict[str, Path]:
    return {name: getattr(args, name) for name in REQUIRED_LABEL_ARGS + OPTIONAL_ADJUDICATION_ARGS}


def private_input_status(args: argparse.Namespace) -> dict[str, Any]:
    paths = input_paths(args)
    required = {
        name: {
            "path_kind": path_kind(path),
            "exists": path.exists(),
            "safe_to_score": bool(path.exists() and path_kind(path) == "private"),
        }
        for name, path in paths.items()
        if name in REQUIRED_LABEL_ARGS
    }
    optional = {
        name: {
            "path_kind": path_kind(path),
            "exists": path.exists(),
            "safe_to_score": bool((not path.exists()) or path_kind(path) == "private"),
        }
        for name, path in paths.items()
        if name in OPTIONAL_ADJUDICATION_ARGS
    }
    required_existing = [name for name, info in required.items() if info["exists"]]
    required_missing = [name for name, info in required.items() if not info["exists"]]
    unsafe_required = [name for name, info in required.items() if info["exists"] and info["path_kind"] != "private"]
    unsafe_optional = [name for name, info in optional.items() if info["exists"] and info["path_kind"] != "private"]
    return {
        "required": required,
        "optional_adjudication": optional,
        "required_existing_count": len(required_existing),
        "required_missing": required_missing,
        "all_required_exist": not required_missing,
        "all_inputs_private_or_absent": not unsafe_required and not unsafe_optional,
        "safe_to_score": bool((not required_missing) and not unsafe_required and not unsafe_optional),
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
        "--r124-labeler-1",
        rel(args.r124_labeler_1) or str(args.r124_labeler_1),
        "--r124-labeler-2",
        rel(args.r124_labeler_2) or str(args.r124_labeler_2),
        "--r124-adjudication",
        rel(args.r124_adjudication) or str(args.r124_adjudication),
        "--r190-labeler-1",
        rel(args.r190_labeler_1) or str(args.r190_labeler_1),
        "--r190-labeler-2",
        rel(args.r190_labeler_2) or str(args.r190_labeler_2),
        "--r190-adjudication",
        rel(args.r190_adjudication) or str(args.r190_adjudication),
        "--r203-labeler-1",
        rel(args.r203_labeler_1) or str(args.r203_labeler_1),
        "--r203-labeler-2",
        rel(args.r203_labeler_2) or str(args.r203_labeler_2),
        "--r203-adjudication",
        rel(args.r203_adjudication) or str(args.r203_adjudication),
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
    labels = payload.get("c6_label_preflight") or {}
    groups = labels.get("groups") or {}
    return {
        "exists": True,
        "status": payload.get("status"),
        "c6_groups": {
            name: {
                "status": group.get("status"),
                "ready_for_r195": group.get("ready_for_r195"),
                "present_count": len(group.get("present") or []),
                "invalid_or_partial_count": len(group.get("invalid_or_partial") or []),
            }
            for name, group in sorted(groups.items())
        },
        "all_c6_groups_ready": all((group.get("ready_for_r195") is True) for group in groups.values()),
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
        "join_statuses": {
            name: op.get("join_status")
            for name, op in sorted(operations.items())
            if isinstance(op, dict) and op.get("join_status") is not None
        },
        "adjudication_templates": {
            "r124": rel(args_path(path, "r124", "tag-adequacy-adjudication-template-r195.csv")),
            "r190": rel(args_path(path, "r190", "merge-risk-adjudication-template-r195.csv")),
        },
        "claim_gate": payload.get("claim_gate") or {},
    }


def args_path(r195_json: Path, subdir: str, filename: str) -> Path:
    return r195_json.parent / subdir / filename


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
    if private_status["required_existing_count"] == 0:
        return "awaiting_private_c6_labels"
    if not private_status["all_inputs_private_or_absent"]:
        return "unsafe_non_private_c6_input"
    if not private_status["all_required_exist"]:
        return "partial_private_c6_labels"
    if not executed:
        return "ready_for_c6_scoring_not_executed"
    for step in ("r264", "r195", "r266"):
        result = command_results.get(step)
        if result and not result.get("ok"):
            return f"pipeline_failed_at_{step}"
    if r264_summary.get("all_c6_groups_ready") is not True:
        return "c6_labels_not_ready_for_r195"
    if not r264_summary.get("safety_all_inputs_safe") or not r264_summary.get("privacy_guard_passed"):
        return "c6_labels_failed_safety_or_privacy_preflight"
    if r195_summary.get("status") == "needs_adjudication":
        return "c6_needs_adjudication"
    if r195_summary.get("exists") and not r266_summary.get("exists"):
        return "r195_scored_without_public_summary"
    gate = r266_summary.get("claim_gate") or {}
    if gate.get("c6_adequacy_supported"):
        return "c6_public_summary_ready"
    if r195_summary.get("exists"):
        return "c6_scored_no_supported_gate"
    return "c6_pipeline_no_score"


def build_payload(args: argparse.Namespace) -> dict[str, Any]:
    args.out_dir.mkdir(parents=True, exist_ok=True)
    private_status = private_input_status(args)
    r264_cmd = build_r264_cmd(args)
    r195_cmd = build_r195_cmd(args)
    r266_cmd = build_r266_cmd(args)

    command_results: dict[str, Any] = {}
    executed = bool(private_status["safe_to_score"] and not args.no_execute)
    r264_json = args.r264_out_dir / "human-return-intake-r264.json"
    r195_json, _r195_md = base_r195_paths(args)
    r266_json = args.r266_out_dir / "human-evidence-public-summary-r266.json"

    if executed:
        command_results["r264"] = run_cmd(r264_cmd)
        r264_summary = summarize_r264(r264_json)
        preflight_ready = bool(
            command_results["r264"]["ok"]
            and r264_summary.get("all_c6_groups_ready")
            and r264_summary.get("safety_all_inputs_safe")
            and r264_summary.get("privacy_guard_passed")
        )
        if preflight_ready:
            command_results["r195"] = run_cmd(r195_cmd)
            r195_summary = summarize_r195(r195_json)
            if command_results["r195"]["ok"] and r195_summary.get("status") != "needs_adjudication":
                command_results["r266"] = run_cmd(r266_cmd)

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
        "run_id": "R270",
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
            "R270 orchestrates private C6 human-label returns through R264, R195, and R266. "
            "It can support public C6 aggregate claims only after real private labeler CSVs "
            "exist and any R195 adjudication requirement is resolved. It never creates labels "
            "and cannot support weak accept without C5."
        ),
        "next_action": (
            "Collect completed private R124/R190/R203 paired labeler CSVs, then rerun this script. "
            "If it reports c6_needs_adjudication, fill the private adjudication CSVs generated from "
            "the R195 templates and rerun before publishing aggregate C6 numbers."
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
        "# R270 C6 Real Label Scoring Pipeline",
        "",
        f"Status: `{payload['status']}`",
        "",
        "## Private Inputs",
        "",
        f"- Required existing: `{private_input['required_existing_count']}` / `{len(REQUIRED_LABEL_ARGS)}`.",
        f"- All required exist: `{private_input['all_required_exist']}`.",
        f"- All inputs private or absent: `{private_input['all_inputs_private_or_absent']}`.",
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
            f"- Canonicalization quality supported: `{gate['canonicalization_quality_supported']}`.",
            f"- Long-tail promotion review supported: `{gate['long_tail_promotion_review_supported']}`.",
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
        "# R270 one-command C6 label scoring pipeline",
        "# Place real private C6 label returns first; this file is a command template, not evidence.",
        "python3 docs/visexp/r270_c6_real_label_scoring_pipeline.py",
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
    out_json = args.out_dir / "c6-real-label-pipeline-r270.json"
    out_md = args.out_dir / "c6-real-label-pipeline-r270.md"
    out_cmd = args.out_dir / "c6-label-scoring-command-r270.txt"
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
    parser.add_argument("--r124-labeler-1", type=Path, default=DEFAULT_R124_LABELER_1)
    parser.add_argument("--r124-labeler-2", type=Path, default=DEFAULT_R124_LABELER_2)
    parser.add_argument("--r124-adjudication", type=Path, default=DEFAULT_R124_ADJUDICATION)
    parser.add_argument("--r190-labeler-1", type=Path, default=DEFAULT_R190_LABELER_1)
    parser.add_argument("--r190-labeler-2", type=Path, default=DEFAULT_R190_LABELER_2)
    parser.add_argument("--r190-adjudication", type=Path, default=DEFAULT_R190_ADJUDICATION)
    parser.add_argument("--r203-labeler-1", type=Path, default=DEFAULT_R203_LABELER_1)
    parser.add_argument("--r203-labeler-2", type=Path, default=DEFAULT_R203_LABELER_2)
    parser.add_argument("--r203-adjudication", type=Path, default=DEFAULT_R203_ADJUDICATION)
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
