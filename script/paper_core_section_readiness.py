#!/usr/bin/env python3
"""R362: audit section-level readiness for the E1--E4 paper narrative.

This is a paper-structure gate. It verifies that the Chinese and English result
sections no longer depend on a chronological run log: each E1--E4 section must
state the claim, oracle, baselines, metrics, counterpoint/scope, and supported
wording implied by R361.
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
OUT_ROOT = ROOT / "docs" / "visexp" / "out"
SUBMODULE_ROOT = ROOT / "docs" / "agentpprof-paper"
DEFAULT_OUT_DIR = OUT_ROOT / "paper-core-section-readiness-r362"
RUN_ID = "R362"

R361_PATH = OUT_ROOT / "paper-core-claim-evidence-r361" / "core-claim-evidence.json"
PAPER_SOURCES = {
    "Chinese paper": ROOT / "docs" / "visexp" / "paper" / "main.tex",
    "English paper": SUBMODULE_ROOT / "main.tex",
    "Evaluation ledger": ROOT / "docs" / "evaluation.md",
}

SECTION_IDS = ["E1", "E2", "E3", "E4"]
SECTION_LABELS = {
    "E1": ["generality", "recursive", "folding", "field derivation"],
    "E2": ["hidden-label", "localization", "ranking"],
    "E3": ["mechanism", "actionability"],
    "E4": ["replayability", "cost", "artifact hygiene"],
}
REQUIRED_SECTION_TOKENS = {
    "E1": ["claim-test", "claim", "oracle", "baseline", "metric", "counterpoint", "operation stack"],
    "E2": [
        "claim-test",
        "claim",
        "oracle",
        "baseline",
        "metric",
        "counterpoint",
        "precision@k",
        "recall",
        "F1",
        "nDCG",
        "work-to-first-positive",
    ],
    "E3": ["claim-test", "claim", "oracle", "baseline", "metric", "counterpoint", "actionable", "not automatic"],
    "E4": ["claim-test", "claim", "oracle", "baseline", "metric", "counterpoint", "not live", "not human"],
}
MUST_NOT_SCOPE_TOKENS = [
    "not a human",
    "not human",
    "not automatic",
    "not complete",
    "not live",
    "not metric dominance",
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


def git_commit() -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        check=True,
    )
    return result.stdout.strip()


def source_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = [
        {
            "source": "R361 core claim evidence",
            "path": rel(R361_PATH),
            "status": git_status(R361_PATH),
            "sha256": sha256(R361_PATH),
        }
    ]
    for name, path in PAPER_SOURCES.items():
        rows.append(
            {
                "source": name,
                "path": rel(path),
                "status": git_status(path),
                "sha256": sha256(path),
            }
        )
    return rows


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower())


def section_regex(eid: str, language: str) -> re.Pattern[str]:
    if language == "zh":
        return re.compile(
            rf"\\subsection\{{{eid}：(?P<title>.*?)\}}(?P<body>.*?)(?=\\subsection\{{E[1-4]：|\\section\{{|\\begin\{{table\*\}}|\Z)",
            re.DOTALL,
        )
    return re.compile(
        rf"\\subsection\{{{eid}:(?P<title>.*?)\}}(?P<body>.*?)(?=\\subsection\{{E[1-4]:|\\section\{{|\\begin\{{table\*\}}|\Z)",
        re.DOTALL,
    )


def extract_sections(text: str, language: str) -> dict[str, str]:
    sections: dict[str, str] = {}
    for eid in SECTION_IDS:
        match = section_regex(eid, language).search(text)
        if match:
            sections[eid] = match.group("title") + "\n" + match.group("body")
    return sections


def add_check(checks: list[dict[str, str]], name: str, condition: bool, evidence: str) -> None:
    checks.append({"check": name, "status": "pass" if condition else "fail", "evidence": evidence})


def build_checks(r361: dict[str, Any], zh: str, en: str, eval_text: str) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    checks: list[dict[str, str]] = []
    rows: list[dict[str, str]] = []
    zh_sections = extract_sections(zh, "zh")
    en_sections = extract_sections(en, "en")

    add_check(
        checks,
        "r361_core_claim_ledger_is_current_and_passing",
        r361["status"] == "pass"
        and r361["summary"]["checks_passed"] == r361["summary"]["checks_total"] == 10
        and len(r361["ledger"]) == 4,
        "R361 has 4 ledger rows and 10/10 checks passing.",
    )
    add_check(
        checks,
        "both_papers_have_e1_e4_sections",
        all(eid in zh_sections for eid in SECTION_IDS) and all(eid in en_sections for eid in SECTION_IDS),
        "Chinese and English papers both expose E1-E4 result subsections.",
    )

    for eid in SECTION_IDS:
        for language, sections in [("zh", zh_sections), ("en", en_sections)]:
            body = sections.get(eid, "")
            lowered = normalize(body)
            missing = [token for token in REQUIRED_SECTION_TOKENS[eid] if token.lower() not in lowered]
            rows.append(
                {
                    "experiment": eid,
                    "language": language,
                    "status": "pass" if not missing else "fail",
                    "missing_tokens": ";".join(missing),
                    "required_tokens": ";".join(REQUIRED_SECTION_TOKENS[eid]),
                }
            )
            add_check(
                checks,
                f"{language}_{eid.lower()}_claim_oracle_baseline_metric_scope_tokens",
                not missing,
                f"{language} {eid} has all section-readiness tokens."
                if not missing
                else f"{language} {eid} missing: {', '.join(missing)}.",
            )

    combined = normalize("\n".join([zh, en, eval_text]))
    for eid, tokens in SECTION_LABELS.items():
        add_check(
            checks,
            f"{eid.lower()}_r361_claim_wording_visible_in_papers",
            all(token.lower() in combined for token in tokens),
            f"{eid} ledger labels are visible in paper/evaluation text.",
        )
    add_check(
        checks,
        "must_not_claim_scope_visible",
        all(token in combined for token in MUST_NOT_SCOPE_TOKENS),
        "The combined paper text keeps human/productivity, automatic, complete compatibility, live overhead, and metric-dominance guardrails visible.",
    )
    add_check(
        checks,
        "two_abstraction_boundary_visible",
        "operation stack" in combined
        and "operation fields" in combined
        and "not new profiler objects" in combined,
        "The papers describe prompt/session/tool/process/syscall concepts as operation fields or forms, not profiler objects.",
    )
    return checks, rows


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def write_markdown(path: Path, payload: dict[str, Any]) -> None:
    lines = [
        "# R362 Paper Core Section Readiness",
        "",
        f"- Status: `{payload['status']}`.",
        f"- Checks: {payload['summary']['checks_passed']}/{payload['summary']['checks_total']}.",
        "- This is a paper-structure gate, not a new empirical result.",
        "",
        "## Section Token Matrix",
        "",
        "| Experiment | Language | Status | Missing tokens |",
        "|---|---|---|---|",
    ]
    for row in payload["section_rows"]:
        lines.append(
            f"| {row['experiment']} | {row['language']} | {row['status']} | {row['missing_tokens']} |"
        )
    lines.extend(["", "## Checks", "", "| Check | Status | Evidence |", "|---|---|---|"])
    for check in payload["checks"]:
        lines.append(f"| `{check['check']}` | {check['status']} | {check['evidence']} |")
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def write_html(path: Path, payload: dict[str, Any]) -> None:
    section_rows = "\n".join(
        "<tr>"
        f"<td>{html.escape(row['experiment'])}</td>"
        f"<td>{html.escape(row['language'])}</td>"
        f"<td>{html.escape(row['status'])}</td>"
        f"<td>{html.escape(row['missing_tokens'])}</td>"
        "</tr>"
        for row in payload["section_rows"]
    )
    check_rows = "\n".join(
        "<tr>"
        f"<td>{html.escape(check['check'])}</td>"
        f"<td>{html.escape(check['status'])}</td>"
        f"<td>{html.escape(check['evidence'])}</td>"
        "</tr>"
        for check in payload["checks"]
    )
    path.write_text(
        f"""<!doctype html>
<html>
<head>
<meta charset=\"utf-8\">
<title>R362 Paper Core Section Readiness</title>
<style>
body {{ font-family: system-ui, sans-serif; margin: 2rem; line-height: 1.45; }}
table {{ border-collapse: collapse; width: 100%; margin: 1rem 0; }}
th, td {{ border: 1px solid #ddd; padding: 0.45rem; vertical-align: top; }}
th {{ background: #f5f5f5; text-align: left; }}
</style>
</head>
<body>
<h1>R362 Paper Core Section Readiness</h1>
<p>Status: <code>{html.escape(payload['status'])}</code>;
checks: {payload['summary']['checks_passed']}/{payload['summary']['checks_total']}.</p>
<h2>Section Token Matrix</h2>
<table>
<tr><th>Experiment</th><th>Language</th><th>Status</th><th>Missing tokens</th></tr>
{section_rows}
</table>
<h2>Checks</h2>
<table>
<tr><th>Check</th><th>Status</th><th>Evidence</th></tr>
{check_rows}
</table>
</body>
</html>
""",
        encoding="utf-8",
    )


def main() -> int:
    args = parse_args()
    out_dir = args.out_dir
    start = time.time()
    out_dir.mkdir(parents=True, exist_ok=True)

    r361 = read_json(R361_PATH)
    zh = read_text(PAPER_SOURCES["Chinese paper"])
    en = read_text(PAPER_SOURCES["English paper"])
    eval_text = read_text(PAPER_SOURCES["Evaluation ledger"])
    checks, section_rows = build_checks(r361, zh, en, eval_text)
    status = "pass" if all(check["status"] == "pass" for check in checks) else "fail"
    payload = {
        "run_id": RUN_ID,
        "schema": "agentsight.paper-core-section-readiness.v1",
        "status": status,
        "commit": git_commit(),
        "input_policy": {
            "dataset_creation": "none",
            "dataset_relabeling": "none",
            "dataset_sync": "none",
            "network_access_required": False,
            "profiler_rerun": False,
        },
        "not_new_empirical_result": True,
        "not_a_human_study_result": True,
        "not_an_agent_analyst_task_result": True,
        "profiler_abstractions": ["operation", "operation stack"],
        "summary": {
            "checks_passed": sum(1 for check in checks if check["status"] == "pass"),
            "checks_total": len(checks),
            "section_rows": len(section_rows),
            "status": status,
        },
        "section_rows": section_rows,
        "checks": checks,
        "source_status": source_rows(),
        "elapsed_s": round(time.time() - start, 3),
    }
    write_csv(out_dir / "section-token-matrix.csv", section_rows, ["experiment", "language", "status", "missing_tokens", "required_tokens"])
    write_csv(out_dir / "section-readiness-checks.csv", checks, ["check", "status", "evidence"])
    write_csv(out_dir / "source-status.csv", payload["source_status"], ["source", "path", "status", "sha256"])
    (out_dir / "section-readiness.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    write_markdown(out_dir / "section-readiness.md", payload)
    write_html(out_dir / "index.html", payload)
    run_result = {
        "run_id": RUN_ID,
        "status": status,
        "checks_passed": payload["summary"]["checks_passed"],
        "checks_total": payload["summary"]["checks_total"],
        "report": rel(out_dir / "section-readiness.json"),
    }
    (out_dir / "run-result.json").write_text(json.dumps(run_result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(run_result, indent=2, sort_keys=True))
    return 0 if status == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
