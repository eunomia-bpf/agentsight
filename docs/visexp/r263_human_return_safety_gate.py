#!/usr/bin/env python3
"""R263: verify R195 rejects known synthetic collection exports.

This is an ingestion-safety gate, not outcome evidence. It proves the
paper-scale static-kit smoke CSV cannot be accidentally treated as a real human
return by R195.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[1]
OUT_DIR = SCRIPT_DIR / "out"
DEFAULT_OUT_DIR = OUT_DIR / "human-return-safety-r263"
R259_SYNTHETIC_C5 = (
    OUT_DIR
    / "human-evidence-paper-scale-static-kit-r259"
    / "synthetic-exports"
    / "user-task-response-template-r249-paper.csv"
)
R249_ASSIGNMENTS = OUT_DIR / "user-task-paper-r249" / "user-task-assignments-r249-paper.csv"
R195 = SCRIPT_DIR / "r195_human_evidence_pipeline.py"


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


def sha256_file(path: Path) -> str | None:
    if not path.exists():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def run_case(out_dir: Path, name: str, responses: Path) -> dict[str, Any]:
    case_dir = out_dir / "cases" / name
    out_json = case_dir / "r195.json"
    out_md = case_dir / "r195.md"
    scored_dir = case_dir / "scored"
    cmd = [
        "python3",
        rel(R195),
        "--r142-responses",
        rel(responses),
        "--r142-assignments",
        rel(R249_ASSIGNMENTS),
        "--scored-dir",
        rel(scored_dir),
        "--out-json",
        rel(out_json),
        "--out-md",
        rel(out_md),
    ]
    proc = subprocess.run(cmd, cwd=REPO_ROOT, text=True, capture_output=True)
    payload = load_json(out_json) if out_json.exists() else {}
    return {
        "command": {
            "cmd": cmd,
            "returncode": proc.returncode,
            "stdout_tail": proc.stdout[-2000:],
            "stderr_tail": proc.stderr[-2000:],
        },
        "payload": payload,
        "outputs": {"json": rel(out_json), "md": rel(out_md), "scored_dir": rel(scored_dir)},
    }


def build_report(out_dir: Path) -> dict[str, Any]:
    synthetic_case = run_case(out_dir, "r259-synthetic-c5-export", R259_SYNTHETIC_C5)
    payload = synthetic_case["payload"]
    safety = ((payload.get("input_contract") or {}).get("safety") or {})
    gates = payload.get("claim_gate") or {}
    checks = {
        "r195_command_passed": synthetic_case["command"]["returncode"] == 0,
        "synthetic_status_rejected": payload.get("status") == "unsafe_return_inputs",
        "synthetic_content_status_detected": (
            (payload.get("input_contract") or {}).get("human_return_content_status")
            == "known_synthetic_or_forbidden_marker"
        ),
        "synthetic_marker_hits_present": bool(safety.get("marker_hits")),
        "no_scorer_operations_on_synthetic": payload.get("operations") == {},
        "c5_stays_false": gates.get("c5_supported") is False,
        "c6_stays_false": gates.get("c6_adequacy_supported") is False,
        "requires_real_human_data": gates.get("requires_real_human_data") is True,
    }
    status = "human_return_safety_passed" if all(checks.values()) else "human_return_safety_failed"
    return {
        "schema_version": 1,
        "run_id": "R263",
        "status": status,
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "checks": checks,
        "case": synthetic_case,
        "source_artifacts": {
            "r195_script": {"path": rel(R195), "sha256": sha256_file(R195)},
            "r259_synthetic_c5": {"path": rel(R259_SYNTHETIC_C5), "sha256": sha256_file(R259_SYNTHETIC_C5)},
            "r249_assignments": {"path": rel(R249_ASSIGNMENTS), "sha256": sha256_file(R249_ASSIGNMENTS)},
        },
        "claim_gate": {
            "human_return_safety_supported": status == "human_return_safety_passed",
            "c5_supported": False,
            "c6_supported": False,
            "outcome_evidence_added": False,
            "weak_accept_supported": False,
            "requires_real_human_returns": True,
        },
        "claim_boundary": (
            "R263 is an ingestion-safety negative test. It rejects known synthetic "
            "R259 exports before scoring, but it adds no participant responses, "
            "human labels, tag adequacy evidence, developer utility evidence, or "
            "weak-accept evidence."
        ),
        "provenance": {
            "repo_commit": git(["rev-parse", "HEAD"]),
            "repo_dirty": bool(git(["status", "--short"])),
            "generator": rel(Path(__file__).resolve()),
        },
    }


def write_markdown(path: Path, report: dict[str, Any]) -> None:
    checks = report["checks"]
    lines = [
        "# R263 Human Return Safety Gate",
        "",
        f"Status: `{report['status']}`",
        "",
        "## Checks",
        "",
        "| check | passed |",
        "|---|---:|",
    ]
    for name, passed in checks.items():
        lines.append(f"| `{name}` | `{passed}` |")
    lines.extend(
        [
            "",
            "## Claim Gate",
            "",
            f"- human_return_safety_supported: `{report['claim_gate']['human_return_safety_supported']}`",
            f"- c5_supported: `{report['claim_gate']['c5_supported']}`",
            f"- c6_supported: `{report['claim_gate']['c6_supported']}`",
            f"- weak_accept_supported: `{report['claim_gate']['weak_accept_supported']}`",
            "",
            report["claim_boundary"],
            "",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def run(args: argparse.Namespace) -> dict[str, Any]:
    report = build_report(args.out_dir)
    out_json = args.out_dir / "human-return-safety-r263.json"
    out_md = args.out_dir / "human-return-safety-r263.md"
    write_json(out_json, report)
    write_markdown(out_md, report)
    print(
        f"R263 {report['status']}: "
        f"synthetic_rejected={report['checks']['synthetic_status_rejected']} "
        f"operations_empty={report['checks']['no_scorer_operations_on_synthetic']}"
    )
    if report["status"] != "human_return_safety_passed":
        raise SystemExit(1)
    return report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    return parser


if __name__ == "__main__":
    run(build_parser().parse_args())
