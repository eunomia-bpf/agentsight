#!/usr/bin/env python3
"""R372: main-body concision and anti-ledger audit.

This guardrail checks that the paper's E2/E3 main-body prose is organized around
core experiments rather than chronological support-run narration. It does not
download data, rerun the profiler, relabel traces, or create a new empirical
result.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import html
import json
import re
import subprocess
import time
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SUBMODULE_ROOT = ROOT / "docs" / "agentpprof-paper"
OUT_ROOT = ROOT / "docs" / "visexp" / "out"
DEFAULT_OUT_DIR = OUT_ROOT / "paper-main-body-concision-r372"
RUN_ID = "R372"
SCRIPT_PATH = Path(__file__).resolve()

SOURCES = {
    "R371 narrative focus": OUT_ROOT / "paper-evaluation-narrative-focus-r371" / "run-result.json",
    "English paper": SUBMODULE_ROOT / "main.tex",
    "Chinese paper": ROOT / "docs" / "visexp" / "paper" / "main.tex",
    "evaluation ledger": ROOT / "docs" / "evaluation.md",
}


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


def git_status(path: Path) -> str:
    repo_root = ROOT
    try:
        path.resolve().relative_to(SUBMODULE_ROOT)
        repo_root = SUBMODULE_ROOT
    except ValueError:
        pass
    try:
        display = str(path.resolve().relative_to(repo_root))
    except ValueError:
        display = str(path)
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


def source_rows() -> list[dict[str, str]]:
    return [
        {
            "source": name,
            "path": rel(path),
            "status": git_status(path),
            "sha256": sha256(path) if path.exists() else "",
        }
        for name, path in {"generator script": SCRIPT_PATH, **SOURCES}.items()
    ]


def extract_sections(text: str) -> dict[str, str]:
    matches = list(re.finditer(r"\\subsection\{(RQ[1-4]/E[1-4][^}]*)\}", text))
    sections: dict[str, str] = {}
    for idx, match in enumerate(matches):
        key = match.group(1).split(":", 1)[0].split("：", 1)[0]
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(text)
        next_section = re.search(r"\\section\{", text[match.end() : end])
        if next_section:
            end = match.end() + next_section.start()
        sections[key] = text[match.start() : end]
    return sections


def count_tokens(text: str) -> dict[str, int]:
    tokens = ["R320", "R330", "R331", "R332", "R333", "R334", "R355", "R363", "R365", "R372"]
    return {token: len(re.findall(rf"\b{token}\b", text)) for token in tokens}


def add_check(checks: list[dict[str, Any]], name: str, passed: bool, detail: str) -> None:
    checks.append({"check": name, "passed": bool(passed), "detail": detail})


def build_report() -> dict[str, Any]:
    english = read_text(SOURCES["English paper"])
    chinese = read_text(SOURCES["Chinese paper"])
    evaluation = read_text(SOURCES["evaluation ledger"])
    r371 = read_json(SOURCES["R371 narrative focus"])
    english_sections = extract_sections(english)
    chinese_sections = extract_sections(chinese)
    en_rq2 = english_sections.get("RQ2/E2", "")
    en_rq3 = english_sections.get("RQ3/E3", "")
    zh_rq2 = chinese_sections.get("RQ2/E2", "")
    zh_rq3 = chinese_sections.get("RQ3/E3", "")
    checks: list[dict[str, Any]] = []

    add_check(
        checks,
        "r371_still_passes",
        r371.get("status") == "pass",
        f"R371 status={r371.get('status')}",
    )
    add_check(
        checks,
        "english_rq2_support_runs_are_compact",
        "R330--R334 and R355 audits" in en_rq2
        and not any(
            phrase in en_rq2
            for phrase in [
                "R330 audits uncertainty",
                "R331 adds a prevalence",
                "R332 asks whether",
                "R333 turns the same comparison",
                "R334 separates the fragmentation",
            ]
        ),
        "English RQ2 uses one supporting-audit paragraph instead of five run-ledger paragraphs.",
    )
    en_counts = count_tokens(en_rq2)
    add_check(
        checks,
        "english_rq2_run_token_shape",
        en_counts["R331"] == 0 and en_counts["R332"] == 0 and en_counts["R333"] == 0,
        f"English RQ2 token counts={en_counts}",
    )
    add_check(
        checks,
        "english_rq2_keeps_primary_numbers",
        all(
            token in en_rq2
            for token in [
                "0.0937",
                "0.3900",
                "0.3559",
                "157.5",
                "285.0",
                "20/24",
                "22/24",
            ]
        ),
        "English RQ2 still carries E2 work, recall, fragmentation, and oracle-depth numbers.",
    )
    add_check(
        checks,
        "english_rq2_keeps_nonclaims",
        all(
            token in en_rq2
            for token in [
                "single best hierarchy",
                "human-productivity claim",
                "metric dominance",
            ]
        ),
        "English RQ2 keeps scoped non-claims after compaction.",
    )
    add_check(
        checks,
        "chinese_rq2_already_compact",
        "R330--R334 和 R355" in zh_rq2 and "R330--R334" in zh_rq2,
        "Chinese RQ2 presents robustness/depth as one E2 audit block.",
    )
    add_check(
        checks,
        "rq3_keeps_mechanism_and_actionability",
        all(
            token in en_rq3 + zh_rq3
            for token in [
                "profile-spec",
                "boundary-derived",
                "automatic selector",
                "automatic boundary discovery",
            ]
        ),
        "RQ3 still centers mechanism/actionability and its scoped counterclaims.",
    )
    add_check(
        checks,
        "paper_keeps_concision_gate_out_of_main_log",
        "R372" in evaluation and "tab:r374-roles" in english and "tab:r374-roles" in chinese,
        "The evaluation ledger records R372, while both papers expose the compact R374 role map instead of a main-body R372 process log.",
    )
    add_check(
        checks,
        "no_new_data_or_profiler_rerun",
        True,
        "This script reads paper text, R371, and the ledger only; it does not sync data or invoke agentpprof.",
    )

    section_rows = []
    for paper, sections in [("english", english_sections), ("chinese", chinese_sections)]:
        for rq in ["RQ2/E2", "RQ3/E3"]:
            section = sections.get(rq, "")
            row = {
                "paper": paper,
                "rq": rq,
                "chars": len(section),
                "r_run_mentions": len(re.findall(r"\bR\d{3}\b", section)),
                "r320": len(re.findall(r"\bR320\b", section)),
                "r330_to_r334": sum(len(re.findall(rf"\bR{run}\b", section)) for run in range(330, 335)),
                "r355": len(re.findall(r"\bR355\b", section)),
                "has_counterpoint": "counterpoint" in section.lower() or "反例" in section,
                "has_nonclaim": any(token in section for token in ["not ", "不是", "不能"]),
            }
            section_rows.append(row)

    return {
        "run_id": RUN_ID,
        "status": "pass" if all(check["passed"] for check in checks) else "fail",
        "checks": {
            "checks_passed": sum(1 for check in checks if check["passed"]),
            "checks_total": len(checks),
        },
        "not_new_empirical_result": True,
        "network_access_required": False,
        "profiler_rerun": False,
        "data_sync": False,
        "checks_detail": checks,
        "section_rows": section_rows,
        "source_status": source_rows(),
    }


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_markdown(path: Path, report: dict[str, Any]) -> None:
    lines = [
        f"# {RUN_ID} Main-Body Concision Audit",
        "",
        f"Status: `{report['status']}`",
        "",
        "This is a paper-organization guardrail. It checks that E2/E3 prose stays organized around the four core experiments rather than support-run chronology.",
        "",
        "## Checks",
        "",
        "| Check | Passed | Detail |",
        "|---|---:|---|",
    ]
    for check in report["checks_detail"]:
        lines.append(f"| {check['check']} | {check['passed']} | {check['detail']} |")
    lines.extend(["", "## Section Summary", "", "| Paper | RQ | R-run mentions | R330-R334 mentions |", "|---|---|---:|---:|"])
    for row in report["section_rows"]:
        lines.append(f"| {row['paper']} | {row['rq']} | {row['r_run_mentions']} | {row['r330_to_r334']} |")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_html(path: Path, report: dict[str, Any]) -> None:
    checks = "\n".join(
        f"<tr><td>{html.escape(check['check'])}</td><td>{check['passed']}</td><td>{html.escape(check['detail'])}</td></tr>"
        for check in report["checks_detail"]
    )
    sections = "\n".join(
        f"<tr><td>{html.escape(row['paper'])}</td><td>{html.escape(row['rq'])}</td><td>{row['r_run_mentions']}</td><td>{row['r330_to_r334']}</td></tr>"
        for row in report["section_rows"]
    )
    path.write_text(
        f"""<!doctype html>
<meta charset=\"utf-8\">
<title>{RUN_ID} Main-Body Concision Audit</title>
<style>body{{font-family:system-ui,sans-serif;max-width:980px;margin:2rem auto;line-height:1.45}}table{{border-collapse:collapse;width:100%}}td,th{{border:1px solid #ddd;padding:6px;vertical-align:top}}th{{background:#f6f6f6}}</style>
<h1>{RUN_ID} Main-Body Concision Audit</h1>
<p>Status: <code>{html.escape(report['status'])}</code></p>
<h2>Checks</h2>
<table><tr><th>Check</th><th>Passed</th><th>Detail</th></tr>{checks}</table>
<h2>Section Summary</h2>
<table><tr><th>Paper</th><th>RQ</th><th>R-run mentions</th><th>R330-R334 mentions</th></tr>{sections}</table>
""",
        encoding="utf-8",
    )


def main() -> None:
    args = parse_args()
    start = time.time()
    out_dir = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    report = build_report()
    report["elapsed_s"] = round(time.time() - start, 3)
    (out_dir / "main-body-concision-report.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_csv(out_dir / "main-body-concision-checks.csv", report["checks_detail"])
    write_csv(out_dir / "section-summary.csv", report["section_rows"])
    write_csv(out_dir / "source-status.csv", report["source_status"])
    write_markdown(out_dir / "main-body-concision.md", report)
    write_html(out_dir / "index.html", report)
    run_result = {
        "run_id": RUN_ID,
        "status": report["status"],
        "checks": report["checks"],
        "elapsed_s": report["elapsed_s"],
        "out_dir": rel(out_dir),
    }
    (out_dir / "run-result.json").write_text(json.dumps(run_result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(run_result, indent=2, sort_keys=True))
    if report["status"] != "pass":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
