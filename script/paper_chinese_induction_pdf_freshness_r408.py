#!/usr/bin/env python3
"""R408: Chinese PDF freshness gate for the induction display.

This is a paper-integration freshness check, not a new empirical experiment. It
reads the tracked Chinese paper source/PDF and the existing R407 display
artifact, extracts text from the PDF with pdftotext, and verifies that the final
PDF contains the induction evidence as reader-facing table text rather than a
run-ledger caption. The English paper submodule is not read or modified.
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
DEFAULT_OUT_DIR = OUT_ROOT / "paper-chinese-induction-pdf-r408"
RUN_ID = "R408"
SCRIPT_PATH = Path(__file__).resolve()
CHINESE_TEX = ROOT / "docs" / "visexp" / "paper" / "main.tex"
CHINESE_PDF = ROOT / "docs" / "visexp" / "paper" / "main.pdf"
R407_DIR = OUT_ROOT / "paper-induction-display-r407"
TABLE_INPUT = r"\input{../out/paper-induction-display-r407/induction-claim-table.tex}"

SOURCES = {
    "Chinese paper TeX": CHINESE_TEX,
    "Chinese paper PDF": CHINESE_PDF,
    "R407 run result": R407_DIR / "run-result.json",
    "R407 display JSON": R407_DIR / "induction-display.json",
    "R407 table fragment": R407_DIR / "induction-claim-table.tex",
}

TOKEN_FIELDS = ["token", "source", "required", "present", "detail"]


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


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def git_commit() -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        check=True,
    )
    return result.stdout.strip()


def git_status(path: Path) -> str:
    display = rel(path)
    tracked = subprocess.run(
        ["git", "ls-files", "--error-unmatch", "--", display],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if tracked.returncode != 0:
        return "untracked_or_missing"
    unstaged = subprocess.run(["git", "diff", "--quiet", "--", display], cwd=ROOT, check=False)
    staged = subprocess.run(["git", "diff", "--cached", "--quiet", "--", display], cwd=ROOT, check=False)
    return "tracked_clean" if unstaged.returncode == 0 and staged.returncode == 0 else "tracked_dirty_allowed"


def source_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for name, path in {"generator script": SCRIPT_PATH, **SOURCES}.items():
        rows.append(
            {
                "source": name,
                "path": rel(path),
                "status": git_status(path),
                "sha256": sha256(path) if path.exists() else "",
            }
        )
    return rows


def extract_pdf_text(path: Path) -> tuple[bool, str, str]:
    if shutil.which("pdftotext") is None:
        return False, "", "pdftotext is not available"
    result = subprocess.run(
        ["pdftotext", str(path), "-"],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode != 0:
        return False, result.stdout, result.stderr.strip()
    return True, result.stdout, "ok"


def contains(text: str, token: str) -> bool:
    squashed_text = " ".join(text.split())
    squashed_token = " ".join(token.split())
    return token in text or squashed_token in squashed_text


def token_row(token: str, source: str, required: bool, text: str, detail: str = "") -> dict[str, Any]:
    present = contains(text, token)
    return {
        "token": token,
        "source": source,
        "required": required,
        "present": present,
        "detail": detail or ("present" if present else "missing"),
    }


def build_packet() -> dict[str, Any]:
    tex = read_text(CHINESE_TEX)
    table = read_text(SOURCES["R407 table fragment"])
    r407_run = read_json(SOURCES["R407 run result"])
    r407_display = read_json(SOURCES["R407 display JSON"])
    pdf_ok, pdf_text, pdf_detail = extract_pdf_text(CHINESE_PDF)

    required_pdf_tokens = [
        "自动 operation-stack induction 的 claim-facing 证据",
        "递归形成、hidden-label 定位消融和深度调优",
        "E1 recursive formation",
        "E2 localization ablation",
        "E3 depth actionability",
        "work@5",
        "0.653",
        "depth 3",
        "0.2865",
    ]
    forbidden_pdf_tokens = ["R402", "R403", "R404", "R407", "R408"]
    table_tokens = ["读者问题", "递归形成、hidden-label 定位消融和深度调优"]

    token_rows: list[dict[str, Any]] = [
        token_row(token, "Chinese PDF", True, pdf_text) for token in required_pdf_tokens
    ]
    token_rows.extend(
        {
            "token": token,
            "source": "Chinese PDF",
            "required": False,
            "present": contains(pdf_text, token),
            "detail": "must be absent from reader-facing PDF text",
        }
        for token in forbidden_pdf_tokens
    )
    token_rows.extend(token_row(token, "R407 table fragment", True, table) for token in table_tokens)

    checks = [
        {
            "check": "pdftotext_extracts_chinese_pdf",
            "passed": pdf_ok and bool(pdf_text.strip()),
            "detail": pdf_detail,
        },
        {
            "check": "r407_display_passed",
            "passed": r407_run.get("status") == "pass"
            and all(check.get("passed") for check in r407_display.get("checks", [])),
            "detail": "R407 table-generation checks still pass.",
        },
        {
            "check": "chinese_tex_inputs_r407_table",
            "passed": TABLE_INPUT in tex,
            "detail": "The Chinese TeX source inputs the R407 table fragment.",
        },
        {
            "check": "r407_table_is_reader_facing",
            "passed": all(contains(table, token) for token in table_tokens)
            and not any(contains(table, token) for token in forbidden_pdf_tokens),
            "detail": "The table fragment uses reader-facing labels and no R-run caption.",
        },
        {
            "check": "pdf_contains_required_induction_tokens",
            "passed": pdf_ok and all(contains(pdf_text, token) for token in required_pdf_tokens),
            "detail": "The tracked Chinese PDF contains the induction display rows and headline numbers.",
        },
        {
            "check": "pdf_has_no_induction_run_ledger_tokens",
            "passed": pdf_ok and not any(contains(pdf_text, token) for token in forbidden_pdf_tokens),
            "detail": "The tracked Chinese PDF does not expose R402/R403/R404/R407/R408 in the induction display text.",
        },
        {
            "check": "english_submodule_not_a_source",
            "passed": all("docs/agentpprof-paper" not in row["path"] for row in source_rows()),
            "detail": "This gate reads only outer Chinese paper and R407 artifacts.",
        },
    ]

    return {
        "run_id": RUN_ID,
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "git_commit": git_commit(),
        "scope": "Chinese paper PDF freshness over existing R407 display; no new empirical experiment",
        "pdf_text_chars": len(pdf_text),
        "token_rows": token_rows,
        "checks": checks,
        "source_status": source_rows(),
    }


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_markdown(path: Path, packet: dict[str, Any]) -> None:
    status = "pass" if all(check["passed"] for check in packet["checks"]) else "fail"
    lines = [
        "# R408 Chinese Induction PDF Freshness",
        "",
        "This artifact checks that the tracked Chinese PDF contains the induction display table text.",
        "It is not a new empirical experiment.",
        "",
        f"- Status: {status}",
        f"- Git commit: `{packet['git_commit']}`",
        f"- Extracted PDF characters: {packet['pdf_text_chars']}",
        "",
        "## Token Checks",
        "",
        "| Token | Source | Required | Present | Detail |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in packet["token_rows"]:
        lines.append(
            "| "
            + " | ".join(str(row[field]).replace("|", "\\|") for field in TOKEN_FIELDS)
            + " |"
        )
    lines.extend(["", "## Checks", "", "| Check | Passed | Detail |", "| --- | --- | --- |"])
    for check in packet["checks"]:
        lines.append(f"| {check['check']} | {check['passed']} | {check['detail']} |")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_html(path: Path, packet: dict[str, Any]) -> None:
    status = "pass" if all(check["passed"] for check in packet["checks"]) else "fail"
    token_html = "\n".join(
        "<tr>" + "".join(f"<td>{html.escape(str(row[field]))}</td>" for field in TOKEN_FIELDS) + "</tr>"
        for row in packet["token_rows"]
    )
    check_html = "\n".join(
        f"<tr><td>{html.escape(check['check'])}</td><td>{check['passed']}</td><td>{html.escape(check['detail'])}</td></tr>"
        for check in packet["checks"]
    )
    path.write_text(
        f"""<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>{RUN_ID} Chinese induction PDF freshness</title>
  <style>
    body {{ font-family: sans-serif; margin: 2rem; line-height: 1.45; }}
    table {{ border-collapse: collapse; width: 100%; margin: 1rem 0; }}
    th, td {{ border: 1px solid #ccc; padding: 0.35rem; vertical-align: top; }}
  </style>
</head>
<body>
  <h1>{RUN_ID} Chinese Induction PDF Freshness</h1>
  <p>Status: <strong>{status}</strong>. Existing R407 display only; no new empirical run.</p>
  <table>
    <thead><tr>{''.join(f'<th>{html.escape(field)}</th>' for field in TOKEN_FIELDS)}</tr></thead>
    <tbody>{token_html}</tbody>
  </table>
  <h2>Checks</h2>
  <table>
    <thead><tr><th>Check</th><th>Passed</th><th>Detail</th></tr></thead>
    <tbody>{check_html}</tbody>
  </table>
</body>
</html>
""",
        encoding="utf-8",
    )


def main() -> None:
    args = parse_args()
    out_dir = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    packet = build_packet()
    passed = all(check["passed"] for check in packet["checks"])

    (out_dir / "chinese-induction-pdf-report.json").write_text(
        json.dumps(packet, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    write_csv(out_dir / "induction-pdf-tokens.csv", packet["token_rows"], TOKEN_FIELDS)
    write_csv(out_dir / "induction-pdf-checks.csv", packet["checks"], ["check", "passed", "detail"])
    write_csv(out_dir / "source-status.csv", packet["source_status"], ["source", "path", "status", "sha256"])
    write_markdown(out_dir / "chinese-induction-pdf-report.md", packet)
    write_html(out_dir / "index.html", packet)

    run_result = {
        "run_id": RUN_ID,
        "status": "pass" if passed else "fail",
        "out_dir": rel(out_dir),
        "checks": {
            "checks_passed": sum(1 for check in packet["checks"] if check["passed"]),
            "checks_total": len(packet["checks"]),
        },
    }
    (out_dir / "run-result.json").write_text(json.dumps(run_result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(run_result, indent=2, sort_keys=True))
    if not passed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
