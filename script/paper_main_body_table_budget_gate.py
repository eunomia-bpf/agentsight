#!/usr/bin/env python3
"""R378: main-body table-budget gate.

This paper-integration guardrail checks that the current papers present the
evaluation as a small set of core E1-E4 result displays rather than as a run-ID
table ledger. It reads paper text and the R377 evidence packet only; it does
not download data, relabel traces, or rerun the profiler.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import html
import json
import subprocess
import time
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OUT_ROOT = ROOT / "docs" / "visexp" / "out"
DEFAULT_OUT_DIR = OUT_ROOT / "paper-main-body-table-budget-r378"
RUN_ID = "R378"
SCRIPT_PATH = Path(__file__).resolve()
PAPER_SUBMODULE = ROOT / "docs" / "agentpprof-paper"
PAPER_SUBMODULE_PATH = "docs/agentpprof-paper"

SOURCES = {
    "R377 claim evidence": OUT_ROOT / "paper-main-claim-evidence-r377" / "main-claim-evidence-report.json",
    "English paper": PAPER_SUBMODULE / "main.tex",
    "Chinese paper": ROOT / "docs" / "visexp" / "paper" / "main.tex",
    "evaluation ledger": ROOT / "docs" / "evaluation.md",
}

ABSENT_MAIN_BODY_LABELS = [
    "tab:visualization-portfolio",
    "tab:r365-headlines",
    "tab:r365-cases",
    "tab:r373-verdict",
]

ENGLISH_REQUIRED = [
    "tab:core-results",
    "tab:r374-roles",
    "tab:r320",
    "fig:r363-portfolio",
    "tab:actionability",
    "tab:r327",
    "tab:r328",
]

CHINESE_REQUIRED = [
    "tab:results",
    "tab:r374-roles",
    "tab:r320-accuracy",
    "fig:r363-portfolio",
    "tab:r327-cost",
    "tab:r328-determinism",
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
        path.resolve().relative_to(PAPER_SUBMODULE)
        repo_root = PAPER_SUBMODULE
    except ValueError:
        pass
    try:
        display = str(path.resolve().relative_to(repo_root))
    except ValueError:
        display = str(path)
    return git_status_display(repo_root, display)


def paper_submodule_head() -> str:
    return git_stdout(["git", "rev-parse", "HEAD"], PAPER_SUBMODULE)


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


def add_check(checks: list[dict[str, Any]], name: str, passed: bool, detail: str) -> None:
    checks.append({"check": name, "passed": bool(passed), "detail": detail})


def count_tables(text: str) -> int:
    return text.count("\\begin{table") + text.count("\\begin{sidewaystable")


def build_report() -> dict[str, Any]:
    r377 = read_json(SOURCES["R377 claim evidence"])
    english = read_text(SOURCES["English paper"])
    chinese = read_text(SOURCES["Chinese paper"])
    evaluation = read_text(SOURCES["evaluation ledger"])
    source_status = source_rows()
    source_by_name = {row["source"]: row for row in source_status}
    combined = english + "\n" + chinese
    checks: list[dict[str, Any]] = []

    missing_english = [label for label in ENGLISH_REQUIRED if label not in english]
    missing_chinese = [label for label in CHINESE_REQUIRED if label not in chinese]
    still_main_tables = [label for label in ABSENT_MAIN_BODY_LABELS if label in combined]

    add_check(
        checks,
        "core_displays_preserved",
        not missing_english and not missing_chinese,
        f"English missing={missing_english}; Chinese missing={missing_chinese}",
    )
    add_check(
        checks,
        "support_artifact_tables_demoted",
        not still_main_tables,
        f"Demoted labels absent from main paper text: {ABSENT_MAIN_BODY_LABELS}; still_present={still_main_tables}",
    )
    add_check(
        checks,
        "non_flamegraph_view_retained",
        "fig:r363-portfolio" in english
        and "fig:r363-portfolio" in chinese
        and "flamegraph" in combined
        and "profile-configuration knobs" in combined,
        "The main body keeps one non-flamegraph E2/E3 figure while demoting the full portfolio table.",
    )
    add_check(
        checks,
        "task_level_evidence_retained_as_prose",
        "all six labeled tasks improve AP" in english
        and "top-five inspected" in english
        and "6/6 tasks 相比 flat summary 改善 AP" in chinese
        and "fixed-session remains the first-positive" in english
        and "fixed-session 在若干任务上仍然是 first-positive" in chinese,
        "Task-level case/verdict evidence remains in prose with positive and counterpoint counts.",
    )
    add_check(
        checks,
        "r377_claim_facets_unchanged",
        r377["status"] == "pass"
        and r377["summary"]["empirical_profiling_experiments"] == 3
        and r377["summary"]["artifact_blocks"] == 1
        and r377["summary"]["claim_elements"] == 5,
        "R378 consumes the passing R377 claim-facet packet rather than changing the evidence basis.",
    )
    add_check(
        checks,
        "main_body_table_budget_reduced",
        count_tables(english) <= 8 and count_tables(chinese) <= 7,
        f"English table environments={count_tables(english)}; Chinese table environments={count_tables(chinese)}.",
    )
    add_check(
        checks,
        "evaluation_ledger_mentions_r378",
        "R378" in evaluation and "table-budget" in evaluation,
        "The evaluation ledger records this paper-presentation guardrail.",
    )
    add_check(
        checks,
        "english_submodule_input_committed",
        source_by_name["English paper"]["status"] == "tracked_clean"
        and paper_submodule_head() == paper_submodule_index_head()
        and bool(paper_submodule_head()),
        "The English paper input is clean in the submodule and captured by the parent gitlink.",
    )
    add_check(
        checks,
        "source_status_tracked",
        all(row["status"] in {"tracked_clean", "tracked_dirty_allowed"} for row in source_status),
        "All R378 sources are tracked or intentionally dirty/staged.",
    )

    summary = {
        "checks_passed": sum(1 for check in checks if check["passed"]),
        "checks_total": len(checks),
        "english_table_environments": count_tables(english),
        "chinese_table_environments": count_tables(chinese),
        "demoted_labels": ABSENT_MAIN_BODY_LABELS,
        "paper_facing_blocks": 4,
        "empirical_profiling_experiments": 3,
        "artifact_blocks": 1,
    }
    return {
        "run_id": RUN_ID,
        "status": "pass" if all(check["passed"] for check in checks) else "fail",
        "schema": "agentsight.paper_main_body_table_budget_gate.v1",
        "not_new_empirical_result": True,
        "network_access_required": False,
        "profiler_rerun": False,
        "data_sync": False,
        "checks": checks,
        "source_status": source_status,
        "summary": summary,
        "interpretation": (
            "The main papers now reserve table/figure weight for the core E1-E4 evidence, "
            "while R363/R365/R373 support artifacts remain provenance and checks rather than "
            "additional main-body experiments."
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
        "# R378 Main-Body Table-Budget Gate",
        "",
        f"Status: `{report['status']}`",
        f"Checks: {report['summary']['checks_passed']}/{report['summary']['checks_total']}",
        (
            "Paper-facing organization: "
            f"{report['summary']['empirical_profiling_experiments']} empirical profiling experiments "
            f"+ {report['summary']['artifact_blocks']} artifact/reproducibility block."
        ),
        f"English table environments: {report['summary']['english_table_environments']}",
        f"Chinese table environments: {report['summary']['chinese_table_environments']}",
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
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_html(path: Path, report: dict[str, Any]) -> None:
    check_rows = "\n".join(
        f"<tr><td>{html.escape(check['check'])}</td><td>{check['passed']}</td><td>{html.escape(check['detail'])}</td></tr>"
        for check in report["checks"]
    )
    path.write_text(
        f"""<!doctype html>
<meta charset="utf-8">
<title>{RUN_ID} Main-Body Table-Budget Gate</title>
<style>
body {{ font-family: system-ui, sans-serif; margin: 2rem; line-height: 1.45; }}
table {{ border-collapse: collapse; width: 100%; margin: 1rem 0; }}
th, td {{ border: 1px solid #d0d7de; padding: 0.45rem; vertical-align: top; }}
th {{ background: #f6f8fa; }}
.status {{ font-weight: 700; }}
</style>
<h1>{RUN_ID} Main-Body Table-Budget Gate</h1>
<p class="status">Status: {html.escape(report['status'])}; checks {report['summary']['checks_passed']}/{report['summary']['checks_total']}.</p>
<p>Paper-facing organization: {report['summary']['empirical_profiling_experiments']} empirical profiling experiments + {report['summary']['artifact_blocks']} artifact/reproducibility block.</p>
<p>English table environments: {report['summary']['english_table_environments']}; Chinese table environments: {report['summary']['chinese_table_environments']}.</p>
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
    (out_dir / "main-body-table-budget-report.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (out_dir / "run-result.json").write_text(json.dumps(run_result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_csv(out_dir / "main-body-table-budget-checks.csv", report["checks"])
    write_csv(out_dir / "source-status.csv", report["source_status"], ["source", "path", "status", "sha256"])
    write_markdown(out_dir / "main-body-table-budget.md", report)
    write_html(out_dir / "index.html", report)
    print(json.dumps(run_result, indent=2, sort_keys=True))
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
