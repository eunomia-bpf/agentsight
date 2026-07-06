#!/usr/bin/env python3
"""R399: tracked paper PDF freshness gate.

This paper-artifact guard checks that the tracked Chinese and English paper PDFs
contain the same display-path guidance that the TeX sources expose. It reads
only tracked paper sources, tracked PDFs, and prior paper gates. It does not
fetch datasets, relabel traces, rerun the profiler, rebuild the papers, or run a
human/agent analyst task.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import html
import json
import shutil
import subprocess
import time
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OUT_ROOT = ROOT / "docs" / "visexp" / "out"
DEFAULT_OUT_DIR = OUT_ROOT / "paper-pdf-freshness-r399"
RUN_ID = "R399"
SCRIPT_PATH = Path(__file__).resolve()
ENGLISH_DIR = ROOT / "docs" / "agentpprof-paper"
CHINESE_DIR = ROOT / "docs" / "visexp" / "paper"
PAPER_SUBMODULE_PATH = "docs/agentpprof-paper"

SOURCES = {
    "Chinese paper tex": CHINESE_DIR / "main.tex",
    "Chinese paper pdf": CHINESE_DIR / "main.pdf",
    "English paper tex": ENGLISH_DIR / "main.tex",
    "English paper pdf": ENGLISH_DIR / "main.pdf",
    "R396 paper build smoke": OUT_ROOT / "paper-build-smoke-r396" / "run-result.json",
    "R398 current three-plus-one": OUT_ROOT / "paper-current-three-plus-one-r398" / "run-result.json",
}

CHINESE_SOURCE_TOKENS = [
    "主文图表形成一条固定证据路径",
    "表~\\ref{tab:results} 是四个 block 的 claim map",
    "hidden-label fidelity 和 baseline tradeoff",
    "mechanism/actionability",
    "replay/cost 证据",
    "补充的 portfolio、case 和 verdict 视图只用于解释这些主图表的数据来源、反例和适用边界",
]

ENGLISH_SOURCE_TOKENS = [
    "The main-paper displays follow this path",
    "Table~\\ref{tab:core-results} is the four-block claim map",
    "provide hidden-label fidelity and baseline tradeoff evidence",
    "provide mechanism/actionability evidence",
    "provide replay and cost evidence",
    "Supporting materials contain the larger portfolio, case, verdict, and consistency tables",
]

CHINESE_PDF_TOKENS = [
    "主文图表形成一条固定证据路径",
    "四个 block 的 claim map",
    "hidden-label fidelity 和 baseline tradeoff",
    "mechanism/actionability",
    "replay/cost 证据",
    "适用边界",
]

ENGLISH_PDF_TOKENS = [
    "The main-paper displays follow this path",
    "four-block claim map",
    "hidden-label fidelity and baseline",
    "mechanism/actionability evidence",
    "provide replay",
    "Supporting materials",
]

NON_CLAIM_TOKENS = [
    "not a fifth core",
    "not a hidden-label accuracy result",
    "human productivity result",
    "not automatic boundary discovery",
    "complete ecosystem compatibility",
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


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(read_text(path))


def normalize(text: str) -> str:
    return " ".join(text.split())


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


def pdftotext(path: Path) -> tuple[str, str, int]:
    pdftotext_path = shutil.which("pdftotext")
    if pdftotext_path is None:
        return "", "pdftotext missing", 127
    result = subprocess.run(
        [pdftotext_path, str(path), "-"],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    return result.stdout, result.stderr, result.returncode


def token_rows(kind: str, text: str, tokens: list[str]) -> list[dict[str, Any]]:
    normalized = normalize(text)
    return [
        {
            "kind": kind,
            "token": token,
            "present": token in normalized,
        }
        for token in tokens
    ]


def add_check(checks: list[dict[str, Any]], name: str, passed: bool, detail: str) -> None:
    checks.append({"check": name, "passed": bool(passed), "detail": detail})


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str] | None = None) -> None:
    if not rows:
        path.write_text((",".join(fields) + "\n") if fields else "", encoding="utf-8")
        return
    fieldnames = fields or list(rows[0].keys())
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})


def build_report() -> dict[str, Any]:
    pdftotext_path = shutil.which("pdftotext")
    chinese_tex = read_text(SOURCES["Chinese paper tex"])
    english_tex = read_text(SOURCES["English paper tex"])
    chinese_pdf_text, chinese_pdf_stderr, chinese_pdf_rc = pdftotext(SOURCES["Chinese paper pdf"])
    english_pdf_text, english_pdf_stderr, english_pdf_rc = pdftotext(SOURCES["English paper pdf"])
    token_checks = (
        token_rows("chinese_source", chinese_tex, CHINESE_SOURCE_TOKENS)
        + token_rows("english_source", english_tex, ENGLISH_SOURCE_TOKENS)
        + token_rows("chinese_pdf", chinese_pdf_text, CHINESE_PDF_TOKENS)
        + token_rows("english_pdf", english_pdf_text, ENGLISH_PDF_TOKENS)
        + token_rows("english_non_claims", english_pdf_text, NON_CLAIM_TOKENS)
    )
    source_status = source_rows()
    prereqs = {
        "R396 paper build smoke": read_json(SOURCES["R396 paper build smoke"]).get("status", ""),
        "R398 current three-plus-one": read_json(SOURCES["R398 current three-plus-one"]).get("status", ""),
    }
    pdf_sizes = {
        "chinese_pdf_bytes": SOURCES["Chinese paper pdf"].stat().st_size if SOURCES["Chinese paper pdf"].exists() else 0,
        "english_pdf_bytes": SOURCES["English paper pdf"].stat().st_size if SOURCES["English paper pdf"].exists() else 0,
    }

    checks: list[dict[str, Any]] = []
    add_check(
        checks,
        "prerequisite_gates_pass",
        prereqs == {"R396 paper build smoke": "pass", "R398 current three-plus-one": "pass"},
        f"Prerequisite statuses={prereqs}",
    )
    add_check(
        checks,
        "pdftotext_available",
        pdftotext_path is not None,
        f"pdftotext={pdftotext_path or 'missing'}",
    )
    add_check(
        checks,
        "tracked_pdfs_exist",
        pdf_sizes["chinese_pdf_bytes"] > 0 and pdf_sizes["english_pdf_bytes"] > 0,
        f"PDF bytes={pdf_sizes}",
    )
    add_check(
        checks,
        "pdftotext_extraction_succeeds",
        chinese_pdf_rc == 0 and english_pdf_rc == 0,
        f"Chinese rc={chinese_pdf_rc} stderr={chinese_pdf_stderr.strip()[:120]}; "
        f"English rc={english_pdf_rc} stderr={english_pdf_stderr.strip()[:120]}",
    )
    add_check(
        checks,
        "source_display_path_tokens_present",
        all(row["present"] for row in token_checks if row["kind"].endswith("_source")),
        "Chinese and English TeX sources contain the main-display path tokens.",
    )
    add_check(
        checks,
        "tracked_pdfs_contain_display_path",
        all(row["present"] for row in token_checks if row["kind"] in {"chinese_pdf", "english_pdf"}),
        "Tracked Chinese and English PDFs contain the display-path text after PDF text extraction.",
    )
    add_check(
        checks,
        "pdf_non_claim_scope_visible",
        all(row["present"] for row in token_checks if row["kind"] == "english_non_claims"),
        "Tracked English PDF keeps fifth-experiment, accuracy, productivity, boundary, and ecosystem non-claims visible.",
    )
    add_check(
        checks,
        "english_submodule_captured_by_parent",
        paper_submodule_head() == paper_submodule_index_head(),
        f"submodule_head={paper_submodule_head()}; parent_index={paper_submodule_index_head()}",
    )
    add_check(
        checks,
        "source_status_tracked_or_dirty_allowed",
        all(
            row["status"] in {"tracked_clean", "tracked_dirty_allowed"}
            or (row["source"] == "generator script" and row["status"] == "untracked_or_missing")
            for row in source_status
        ),
        "All inputs are tracked or intentionally dirty while this gate is generated.",
    )

    return {
        "run_id": RUN_ID,
        "status": "pass" if all(check["passed"] for check in checks) else "fail",
        "schema": "agentsight.paper_pdf_freshness_gate.v1",
        "network_access_required": False,
        "data_sync": False,
        "profiler_rerun": False,
        "paper_rebuild": False,
        "human_or_agent_analyst_task": False,
        "checks": checks,
        "token_checks": token_checks,
        "source_status": source_status,
        "pdf_sizes": pdf_sizes,
        "summary": {
            "checks_passed": sum(1 for check in checks if check["passed"]),
            "checks_total": len(checks),
            "token_checks_passed": sum(1 for row in token_checks if row["present"]),
            "token_checks_total": len(token_checks),
        },
        "interpretation": (
            "The tracked Chinese and English paper PDFs contain the same "
            "main-display path that the TeX sources expose. This is an E4 "
            "replayability/scope-control check, not a new empirical experiment."
        ),
    }


def write_markdown(path: Path, report: dict[str, Any]) -> None:
    lines = [
        "# R399 Paper PDF Freshness Gate",
        "",
        f"Status: `{report['status']}`",
        f"Checks: {report['summary']['checks_passed']}/{report['summary']['checks_total']}",
        f"Token checks: {report['summary']['token_checks_passed']}/{report['summary']['token_checks_total']}",
        "",
        report["interpretation"],
        "",
        "## Checks",
        "",
        "| Check | Passed | Detail |",
        "|---|---:|---|",
    ]
    for check in report["checks"]:
        lines.append(f"| {check['check']} | {check['passed']} | {check['detail']} |")
    lines.extend(["", "## Token Checks", "", "| Kind | Present | Token |", "|---|---:|---|"])
    for row in report["token_checks"]:
        lines.append(f"| {row['kind']} | {row['present']} | `{row['token']}` |")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_html(path: Path, report: dict[str, Any]) -> None:
    check_rows = "\n".join(
        f"<tr><td>{html.escape(check['check'])}</td><td>{check['passed']}</td><td>{html.escape(check['detail'])}</td></tr>"
        for check in report["checks"]
    )
    token_rows_html = "\n".join(
        f"<tr><td>{html.escape(row['kind'])}</td><td>{row['present']}</td><td><code>{html.escape(row['token'])}</code></td></tr>"
        for row in report["token_checks"]
    )
    path.write_text(
        f"""<!doctype html>
<meta charset="utf-8">
<title>{RUN_ID} Paper PDF Freshness Gate</title>
<style>
body {{ font-family: system-ui, sans-serif; margin: 2rem; line-height: 1.45; }}
table {{ border-collapse: collapse; width: 100%; margin: 1rem 0; }}
th, td {{ border: 1px solid #d0d7de; padding: 0.45rem; vertical-align: top; }}
th {{ background: #f6f8fa; }}
.status {{ font-weight: 700; }}
code {{ white-space: pre-wrap; }}
</style>
<h1>{RUN_ID} Paper PDF Freshness Gate</h1>
<p class="status">Status: {html.escape(report['status'])}; checks {report['summary']['checks_passed']}/{report['summary']['checks_total']}.</p>
<p>{html.escape(report['interpretation'])}</p>
<h2>Checks</h2>
<table><tr><th>Check</th><th>Passed</th><th>Detail</th></tr>{check_rows}</table>
<h2>Token Checks</h2>
<table><tr><th>Kind</th><th>Present</th><th>Token</th></tr>{token_rows_html}</table>
""",
        encoding="utf-8",
    )


def main() -> int:
    args = parse_args()
    start = time.time()
    out_dir = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    report = build_report()
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
    (out_dir / "pdf-freshness-report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (out_dir / "run-result.json").write_text(json.dumps(run_result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_csv(out_dir / "pdf-freshness-checks.csv", report["checks"])
    write_csv(out_dir / "pdf-token-checks.csv", report["token_checks"], ["kind", "token", "present"])
    write_csv(out_dir / "source-status.csv", report["source_status"], ["source", "path", "status", "sha256"])
    write_markdown(out_dir / "pdf-freshness.md", report)
    write_html(out_dir / "index.html", report)
    print(json.dumps(run_result, indent=2, sort_keys=True))
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
