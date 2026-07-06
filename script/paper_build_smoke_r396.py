#!/usr/bin/env python3
"""R396: paper build smoke gate.

This reproducibility guard runs the English and Chinese paper builds, checks
that both PDFs are produced, and verifies the final LaTeX logs do not contain
unresolved cross-references/citations. It also checks that the English ACM
draft no longer emits the figure-description accessibility warning. It does not
fetch datasets, relabel traces, rerun the profiler, or run a human/agent
analyst task.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import html
import json
import shutil
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OUT_ROOT = ROOT / "docs" / "visexp" / "out"
DEFAULT_OUT_DIR = OUT_ROOT / "paper-build-smoke-r396"
RUN_ID = "R396"
SCRIPT_PATH = Path(__file__).resolve()
ENGLISH_DIR = ROOT / "docs" / "agentpprof-paper"
CHINESE_DIR = ROOT / "docs" / "visexp" / "paper"
PAPER_SUBMODULE_PATH = "docs/agentpprof-paper"

SOURCES = {
    "English paper tex": ENGLISH_DIR / "main.tex",
    "English paper pdf": ENGLISH_DIR / "main.pdf",
    "Chinese paper tex": CHINESE_DIR / "main.tex",
    "Chinese paper pdf": CHINESE_DIR / "main.pdf",
    "Chinese paper gitignore": CHINESE_DIR / ".gitignore",
    "R395 claim/verdict alignment": OUT_ROOT / "paper-main-claim-verdict-alignment-r395" / "run-result.json",
}

UNRESOLVED_PATTERNS = [
    "undefined references",
    "undefined citations",
    "reference `",
    "citation `",
    "citation(s) may have changed",
    "label(s) may have changed",
    "rerun to get cross-references right",
    "rerun to get citations correct",
]

LATEX_TEMP_PATTERNS = [
    "*.aux",
    "*.log",
    "*.out",
    "*.toc",
    "*.lof",
    "*.lot",
    "*.fls",
    "*.fdb_latexmk",
    "*.synctex.gz",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    return parser.parse_args()


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return str(path.resolve())


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def git_stdout(args: list[str], cwd: Path) -> str:
    result = subprocess.run(args, cwd=cwd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    return result.stdout.strip()


def git_status_display(repo_root: Path, display: str) -> str:
    tracked = subprocess.run(
        ["git", "ls-files", "--error-unmatch", "--", display],
        cwd=repo_root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if tracked.returncode != 0:
        return "untracked_or_missing"
    unstaged = subprocess.run(["git", "diff", "--quiet", "--", display], cwd=repo_root, check=False)
    staged = subprocess.run(["git", "diff", "--cached", "--quiet", "--", display], cwd=repo_root, check=False)
    return "tracked_clean" if unstaged.returncode == 0 and staged.returncode == 0 else "tracked_dirty_allowed"


def git_status(path: Path) -> str:
    repo_root = ROOT
    try:
        path.resolve().relative_to(ENGLISH_DIR)
        repo_root = ENGLISH_DIR
    except ValueError:
        pass
    try:
        display = str(path.resolve().relative_to(repo_root))
    except ValueError:
        display = str(path)
    return git_status_display(repo_root, display)


def paper_submodule_head() -> str:
    return git_stdout(["git", "rev-parse", "HEAD"], ENGLISH_DIR)


def paper_submodule_index_head() -> str:
    line = git_stdout(["git", "ls-files", "-s", "--", PAPER_SUBMODULE_PATH], ROOT)
    parts = line.split()
    return parts[1] if len(parts) >= 2 else ""


def source_rows() -> list[dict[str, str]]:
    rows = []
    for name, path in {"generator script": SCRIPT_PATH, **SOURCES}.items():
        rows.append(
            {
                "source": name,
                "path": rel(path),
                "status": git_status(path),
                "sha256": sha256(path) if path.exists() else "",
            }
        )
    rows.append(
        {
            "source": "English paper submodule gitlink",
            "path": PAPER_SUBMODULE_PATH,
            "status": git_status_display(ROOT, PAPER_SUBMODULE_PATH),
            "sha256": f"submodule_head={paper_submodule_head()};parent_index={paper_submodule_index_head()}",
        }
    )
    return rows


def run_command(name: str, cwd: Path, command: list[str], out_dir: Path) -> dict[str, Any]:
    start = time.time()
    result = subprocess.run(command, cwd=cwd, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False)
    log_path = out_dir / f"{name}.stdout.log"
    write_normalized_log(log_path, result.stdout)
    return {
        "name": name,
        "cwd": rel(cwd),
        "command": " ".join(command),
        "returncode": result.returncode,
        "elapsed_s": round(time.time() - start, 3),
        "stdout_log": rel(log_path),
    }


def write_normalized_log(path: Path, text: str) -> None:
    lines = [line.rstrip() for line in text.splitlines()]
    while lines and not lines[-1]:
        lines.pop()
    path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")


def copy_final_log(src: Path, dst: Path) -> str:
    write_normalized_log(dst, src.read_text(encoding="utf-8", errors="replace"))
    return rel(dst)


def copy_english_paper_to_temp(tmp_root: Path) -> Path:
    temp_paper = tmp_root / "agentpprof-paper"
    shutil.copytree(
        ENGLISH_DIR,
        temp_paper,
        ignore=shutil.ignore_patterns(".git", "main.pdf", *LATEX_TEMP_PATTERNS),
    )
    return temp_paper


def add_check(checks: list[dict[str, Any]], name: str, passed: bool, detail: str) -> None:
    checks.append({"check": name, "passed": bool(passed), "detail": detail})


def log_hits(log_path: Path, patterns: list[str]) -> list[str]:
    text = log_path.read_text(encoding="utf-8", errors="replace").lower()
    return [pattern for pattern in patterns if pattern in text]


def build_report(out_dir: Path) -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="agentsight-r396-paper-") as tmp:
        tmp_root = Path(tmp)
        english_temp_dir = copy_english_paper_to_temp(tmp_root)
        chinese_output_dir = tmp_root / "chinese-build"
        chinese_output_dir.mkdir()
        runs = [
            run_command("english-make", english_temp_dir, ["make"], out_dir),
            run_command(
                "chinese-xelatex-1",
                CHINESE_DIR,
                ["xelatex", f"-output-directory={chinese_output_dir}", "-interaction=nonstopmode", "main.tex"],
                out_dir,
            ),
            run_command(
                "chinese-xelatex-2",
                CHINESE_DIR,
                ["xelatex", f"-output-directory={chinese_output_dir}", "-interaction=nonstopmode", "main.tex"],
                out_dir,
            ),
        ]
        english_pdf = english_temp_dir / "main.pdf"
        chinese_pdf = chinese_output_dir / "main.pdf"
        english_log = english_temp_dir / "main.log"
        chinese_log = chinese_output_dir / "main.log"
        generated = {
            "english_pdf_bytes": english_pdf.stat().st_size if english_pdf.exists() else 0,
            "english_pdf_sha256": sha256(english_pdf) if english_pdf.exists() else "",
            "english_final_log": copy_final_log(english_log, out_dir / "english-main.log") if english_log.exists() else "",
            "chinese_pdf_bytes": chinese_pdf.stat().st_size if chinese_pdf.exists() else 0,
            "chinese_pdf_sha256": sha256(chinese_pdf) if chinese_pdf.exists() else "",
            "chinese_final_log": copy_final_log(chinese_log, out_dir / "chinese-main.log") if chinese_log.exists() else "",
        }
        paper_pdfs_ok = generated["english_pdf_bytes"] > 0 and generated["chinese_pdf_bytes"] > 0
        paper_pdfs_detail = (
            f"English PDF bytes={generated['english_pdf_bytes']}; "
            f"Chinese PDF bytes={generated['chinese_pdf_bytes']}"
        )
        english_unresolved = log_hits(english_log, UNRESOLVED_PATTERNS) if english_log.exists() else ["missing log"]
        chinese_unresolved = log_hits(chinese_log, UNRESOLVED_PATTERNS) if chinese_log.exists() else ["missing log"]
        english_warning_hits = (
            log_hits(english_log, ["possible image without description"]) if english_log.exists() else ["missing log"]
        )
    checks: list[dict[str, Any]] = []

    add_check(
        checks,
        "build_commands_exit_zero",
        all(run["returncode"] == 0 for run in runs),
        f"Return codes={[run['returncode'] for run in runs]}",
    )
    add_check(
        checks,
        "paper_pdfs_exist",
        paper_pdfs_ok,
        paper_pdfs_detail,
    )

    add_check(
        checks,
        "english_log_has_no_unresolved_refs_or_citations",
        not english_unresolved,
        f"Hits={english_unresolved}",
    )
    add_check(
        checks,
        "chinese_log_has_no_unresolved_refs",
        not chinese_unresolved,
        f"Hits={chinese_unresolved}",
    )
    add_check(
        checks,
        "english_acm_image_description_warning_absent",
        not english_warning_hits,
        f"Hits={english_warning_hits}",
    )
    r395 = json.loads((OUT_ROOT / "paper-main-claim-verdict-alignment-r395" / "run-result.json").read_text())
    add_check(
        checks,
        "r395_claim_alignment_still_passes",
        r395.get("status") == "pass",
        f"R395 status={r395.get('status')}",
    )
    add_check(
        checks,
        "source_status_tracked_or_dirty_allowed",
        all(
            row["status"] in {"tracked_clean", "tracked_dirty_allowed"}
            or (
                row["source"] in {"generator script", "Chinese paper gitignore"}
                and row["status"] == "untracked_or_missing"
            )
            for row in source_rows()
        ),
        "All build inputs/outputs are tracked or intentionally dirty while this build gate is generated.",
    )

    source_status = source_rows()
    summary = {
        "checks_passed": sum(1 for check in checks if check["passed"]),
        "checks_total": len(checks),
        "data_sync": False,
        "profiler_rerun": False,
        "human_or_agent_analyst_task": False,
    }
    return {
        "run_id": RUN_ID,
        "status": "pass" if all(check["passed"] for check in checks) else "fail",
        "schema": "agentsight.paper_build_smoke.v1",
        "network_access_required": False,
        "data_sync": False,
        "profiler_rerun": False,
        "human_or_agent_analyst_task": False,
        "commands": runs,
        "checks": checks,
        "source_status": source_status,
        "generated_outputs": generated,
        "summary": summary,
        "interpretation": (
            "Both paper drafts build locally in temporary output locations, "
            "final logs have no unresolved references/citations, and the "
            "English ACM draft has figure description metadata for the "
            "non-flamegraph portfolio figure."
        ),
    }


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str] | None = None) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fieldnames = fields or list(rows[0].keys())
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})


def write_markdown(path: Path, report: dict[str, Any]) -> None:
    lines = [
        "# R396 Paper Build Smoke Gate",
        "",
        f"Status: `{report['status']}`",
        f"Checks: {report['summary']['checks_passed']}/{report['summary']['checks_total']}",
        "",
        report["interpretation"],
        "",
        "## Commands",
        "",
        "| Name | Return Code | Elapsed (s) | Command |",
        "|---|---:|---:|---|",
    ]
    for command in report["commands"]:
        lines.append(
            f"| {command['name']} | {command['returncode']} | {command['elapsed_s']} | `{command['command']}` |"
        )
    lines.extend(["", "## Checks", "", "| Check | Passed | Detail |", "|---|---:|---|"])
    for check in report["checks"]:
        lines.append(f"| {check['check']} | {check['passed']} | {check['detail']} |")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_html(path: Path, report: dict[str, Any]) -> None:
    check_rows = "\n".join(
        f"<tr><td>{html.escape(check['check'])}</td><td>{check['passed']}</td><td>{html.escape(check['detail'])}</td></tr>"
        for check in report["checks"]
    )
    path.write_text(
        f"""<!doctype html>
<meta charset="utf-8">
<title>{RUN_ID} Paper Build Smoke Gate</title>
<style>
body {{ font-family: system-ui, sans-serif; margin: 2rem; line-height: 1.45; }}
table {{ border-collapse: collapse; width: 100%; margin: 1rem 0; }}
th, td {{ border: 1px solid #d0d7de; padding: 0.45rem; vertical-align: top; }}
th {{ background: #f6f8fa; }}
.status {{ font-weight: 700; }}
</style>
<h1>{RUN_ID} Paper Build Smoke Gate</h1>
<p class="status">Status: {html.escape(report['status'])}; checks {report['summary']['checks_passed']}/{report['summary']['checks_total']}.</p>
<p>{html.escape(report['interpretation'])}</p>
<h2>Checks</h2>
<table><tr><th>Check</th><th>Passed</th><th>Detail</th></tr>{check_rows}</table>
""",
        encoding="utf-8",
    )


def main() -> int:
    args = parse_args()
    start = time.time()
    out_dir = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    report = build_report(out_dir)
    run_result = {
        "run_id": RUN_ID,
        "status": report["status"],
        "checks": {
            "checks_passed": report["summary"]["checks_passed"],
            "checks_total": report["summary"]["checks_total"],
        },
        "out_dir": rel(out_dir),
        "elapsed_s": round(time.time() - start, 3),
    }
    (out_dir / "paper-build-smoke-report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (out_dir / "run-result.json").write_text(json.dumps(run_result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_csv(out_dir / "paper-build-smoke-checks.csv", report["checks"])
    write_csv(out_dir / "paper-build-commands.csv", report["commands"])
    write_csv(out_dir / "source-status.csv", report["source_status"], ["source", "path", "status", "sha256"])
    write_markdown(out_dir / "paper-build-smoke.md", report)
    write_html(out_dir / "index.html", report)
    print(json.dumps(run_result, indent=2, sort_keys=True))
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
