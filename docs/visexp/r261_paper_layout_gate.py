#!/usr/bin/env python3
"""R261: paper layout gate after compacting the claim-gate table.

This run is paper hygiene only. It compiles the Chinese draft, parses the LaTeX
log, and records whether the oversized claim-gate float has been removed. It
does not add participant responses, human labels, raw traces, or new model
outputs.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[1]
PAPER_DIR = SCRIPT_DIR / "paper"
MAIN_TEX = PAPER_DIR / "main.tex"
MAIN_PDF = PAPER_DIR / "main.pdf"
MAIN_LOG = PAPER_DIR / "main.log"
DEFAULT_OUT_DIR = SCRIPT_DIR / "out" / "paper-layout-gate-r261"


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT.resolve()))
    except Exception:
        return str(path)


def git(args: list[str]) -> str | None:
    try:
        return subprocess.check_output(
            ["git", *args],
            cwd=REPO_ROOT,
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip()
    except Exception:
        return None


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def run_xelatex() -> list[dict[str, Any]]:
    runs: list[dict[str, Any]] = []
    for index in range(2):
        proc = subprocess.run(
            ["xelatex", "-interaction=nonstopmode", "-halt-on-error", "main.tex"],
            cwd=PAPER_DIR,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
        )
        runs.append(
            {
                "run": index + 1,
                "returncode": proc.returncode,
                "stdout_tail": proc.stdout[-4000:],
            }
        )
        if proc.returncode != 0:
            break
    return runs


def parse_log(text: str) -> dict[str, Any]:
    page_match = re.search(r"Output written on main\.pdf \((\d+) pages?\)", text)
    overfull_values = [float(value) for value in re.findall(r"Overfull \\hbox \(([0-9.]+)pt too wide\)", text)]
    float_hits = re.findall(r"Float too large for page by ([0-9.]+)pt", text)
    undefined_reference_lines = [
        line
        for line in text.splitlines()
        if "undefined" in line.lower() or "Rerun to get cross-references right" in line
    ]
    return {
        "page_count": int(page_match.group(1)) if page_match else None,
        "float_too_large_count": len(float_hits),
        "float_too_large_points": [float(value) for value in float_hits],
        "overfull_hbox_count": len(overfull_values),
        "max_overfull_hbox_pt": max(overfull_values) if overfull_values else 0.0,
        "undefined_reference_lines": undefined_reference_lines,
    }


def build_report(out_dir: Path, skip_compile: bool) -> dict[str, Any]:
    compile_runs = [] if skip_compile else run_xelatex()
    compile_ok = all(run["returncode"] == 0 for run in compile_runs) if compile_runs else True
    if not MAIN_LOG.exists():
        raise FileNotFoundError(f"missing LaTeX log: {rel(MAIN_LOG)}")
    log_text = MAIN_LOG.read_text(encoding="utf-8", errors="replace")
    parsed = parse_log(log_text)

    checks = {
        "latex_compile_passed": compile_ok,
        "pdf_exists": MAIN_PDF.exists() and MAIN_PDF.stat().st_size > 0,
        "page_count_extracted": parsed["page_count"] is not None,
        "no_float_too_large": parsed["float_too_large_count"] == 0,
        "no_undefined_references": len(parsed["undefined_reference_lines"]) == 0,
        "page_count_at_most_11": parsed["page_count"] is not None and parsed["page_count"] <= 11,
        "six_page_target_met": parsed["page_count"] is not None and parsed["page_count"] <= 6,
    }

    source_paths = [MAIN_TEX, MAIN_PDF, MAIN_LOG]
    report = {
        "run_id": "R261",
        "status": "paper_layout_hygiene_passed"
        if all(
            checks[key]
            for key in [
                "latex_compile_passed",
                "pdf_exists",
                "page_count_extracted",
                "no_float_too_large",
                "no_undefined_references",
                "page_count_at_most_11",
            ]
        )
        else "paper_layout_hygiene_failed",
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "paper_layout": parsed,
        "checks": checks,
        "claim_gate": {
            "paper_layout_hygiene_supported": all(
                checks[key]
                for key in [
                    "latex_compile_passed",
                    "pdf_exists",
                    "page_count_extracted",
                    "no_float_too_large",
                    "no_undefined_references",
                    "page_count_at_most_11",
                ]
            ),
            "six_page_target_supported": checks["six_page_target_met"],
            "c5_supported": False,
            "c6_supported": False,
            "weak_accept_supported": False,
            "outcome_evidence_added": False,
            "requires_real_human_returns": True,
        },
        "provenance": {
            "generator": rel(Path(__file__)),
            "repo_commit": git(["rev-parse", "HEAD"]),
            "repo_dirty": bool(git(["status", "--porcelain"])),
            "raw_trace_read": False,
            "llm_called": False,
            "participant_responses_added": 0,
            "human_labels_added": 0,
            "source_hashes": {rel(path): sha256_file(path) for path in source_paths if path.exists()},
        },
        "compile_runs": compile_runs,
        "claim_boundary": "R261 is a paper-layout gate only. It removes the oversized claim-gate float from the main paper view and records the remaining page budget gap. It adds no C5/C6 outcome evidence.",
    }

    write_json(out_dir / "paper-layout-gate-r261.json", report)
    lines = [
        "# R261 Paper Layout Gate",
        "",
        f"Status: `{report['status']}`",
        "",
        "## Layout",
        "",
        f"- pages: `{parsed['page_count']}`",
        f"- float_too_large_count: `{parsed['float_too_large_count']}`",
        f"- undefined_reference_lines: `{len(parsed['undefined_reference_lines'])}`",
        f"- overfull_hbox_count: `{parsed['overfull_hbox_count']}`",
        f"- max_overfull_hbox_pt: `{parsed['max_overfull_hbox_pt']}`",
        "",
        "## Claim Gate",
        "",
        f"- paper_layout_hygiene_supported: `{report['claim_gate']['paper_layout_hygiene_supported']}`",
        f"- six_page_target_supported: `{report['claim_gate']['six_page_target_supported']}`",
        f"- weak_accept_supported: `{report['claim_gate']['weak_accept_supported']}`",
        f"- outcome_evidence_added: `{report['claim_gate']['outcome_evidence_added']}`",
        "",
        "R261 is layout hygiene only; C5/C6 still require real human returns.",
        "",
    ]
    write_text(out_dir / "paper-layout-gate-r261.md", "\n".join(lines))
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--skip-compile", action="store_true")
    args = parser.parse_args()

    report = build_report(args.out_dir, args.skip_compile)
    print(
        f"R261 {report['status']}: pages={report['paper_layout']['page_count']} "
        f"float_too_large={report['paper_layout']['float_too_large_count']} "
        f"six_page={report['claim_gate']['six_page_target_supported']}"
    )
    return 0 if report["status"] == "paper_layout_hygiene_passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
