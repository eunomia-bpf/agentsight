#!/usr/bin/env python3
"""R379: RQ2/RQ3 claim-flow gate.

This paper-integration guardrail checks that the RQ2/RQ3 prose reads like a
profiling-paper claim test: primary comparison, success criterion, baseline
scope, failure interpretation, mechanism/actionability, and non-claims are
visible before support-run details. It reads paper text and prior paper gates
only; it does not download data, relabel traces, or rerun the profiler.
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
DEFAULT_OUT_DIR = OUT_ROOT / "paper-rq2-rq3-claim-flow-r379"
RUN_ID = "R379"
SCRIPT_PATH = Path(__file__).resolve()
PAPER_SUBMODULE = ROOT / "docs" / "agentpprof-paper"
PAPER_SUBMODULE_PATH = "docs/agentpprof-paper"

SOURCES = {
    "R377 claim evidence": OUT_ROOT / "paper-main-claim-evidence-r377" / "main-claim-evidence-report.json",
    "R378 table budget": OUT_ROOT / "paper-main-body-table-budget-r378" / "main-body-table-budget-report.json",
    "English paper": PAPER_SUBMODULE / "main.tex",
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


def section_between(text: str, start: str, end: str) -> str:
    start_i = text.index(start)
    end_i = text.index(end, start_i)
    return text[start_i:end_i]


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


def has_all(text: str, tokens: list[str]) -> bool:
    return all(token in text for token in tokens)


def squish(text: str) -> str:
    return " ".join(text.split())


def ordered(text: str, tokens: list[str]) -> bool:
    cursor = -1
    for token in tokens:
        idx = text.find(token, cursor + 1)
        if idx < 0:
            return False
        cursor = idx
    return True


def build_report() -> dict[str, Any]:
    r377 = read_json(SOURCES["R377 claim evidence"])
    r378 = read_json(SOURCES["R378 table budget"])
    english = read_text(SOURCES["English paper"])
    chinese = read_text(SOURCES["Chinese paper"])
    evaluation = read_text(SOURCES["evaluation ledger"])
    source_status = source_rows()
    source_by_name = {row["source"]: row for row in source_status}

    english_rq2 = section_between(english, "\\subsection{RQ2/E2", "\\subsection{RQ3/E3")
    english_rq3 = section_between(english, "\\subsection{RQ3/E3", "\\subsection{RQ4/E4")
    chinese_rq2 = section_between(chinese, "\\subsection{RQ2/E2", "\\subsection{RQ3/E3")
    chinese_rq3 = section_between(chinese, "\\subsection{RQ3/E3", "\\subsection{RQ4/E4")
    combined = english_rq2 + english_rq3 + chinese_rq2 + chinese_rq3
    english_rq2_flat = squish(english_rq2)
    english_rq3_flat = squish(english_rq3)
    chinese_rq2_flat = squish(chinese_rq2)
    chinese_rq3_flat = squish(chinese_rq3)

    checks: list[dict[str, Any]] = []
    add_check(
        checks,
        "rq2_primary_comparison_visible",
        has_all(
            english_rq2_flat,
            ["Primary comparison", "success criterion", "Pareto condition", "Table~\\ref{tab:r320}"],
        )
        and has_all(chinese_rq2_flat, ["Primary comparison", "success criterion", "Pareto 条件", "表~\\ref{tab:r320-accuracy}"]),
        "RQ2 opens with primary comparison, success criterion, and the R320 table route.",
    )
    add_check(
        checks,
        "rq2_baselines_and_failure_interpretation_visible",
        has_all(english_rq2_flat, ["Flat summaries", "Fixed-session drilldown", "Failure interpretation", "baseline scope"])
        and has_all(chinese_rq2_flat, ["flat summary", "fixed-session", "Failure interpretation", "baseline scope"]),
        "RQ2 names flat/fixed-session baselines and explains failure interpretation before support-run details.",
    )
    add_check(
        checks,
        "rq2_claim_flow_precedes_support_runs",
        ordered(english_rq2_flat, ["Primary comparison", "Failure interpretation", "R363"])
        and ordered(chinese_rq2_flat, ["Primary comparison", "Failure interpretation", "R300--R305"])
        and ordered(chinese_rq2_flat, ["Failure interpretation", "R330--R334"]),
        "RQ2 claim-flow opener and failure interpretation appear before support/provenance run details.",
    )
    add_check(
        checks,
        "rq2_non_dominance_preserved",
        has_all(english_rq2_flat, ["not universal dominance", "human-productivity claim", "not dominance over every"])
        and has_all(chinese_rq2_flat, ["不是 metric dominance", "不是对所有", "不能写成 automatic detector"]),
        "RQ2 remains a scoped Pareto tradeoff, not metric dominance or human utility.",
    )
    add_check(
        checks,
        "rq3_mechanism_question_visible",
        has_all(
            english_rq3_flat,
            ["Primary mechanism question", "Hidden labels are used only after profiling", "success criterion"],
        )
        and has_all(chinese_rq3_flat, ["Primary mechanism question", "Hidden labels 只在 profiling 之后", "成功条件"]),
        "RQ3 starts from mechanism/actionability, not another leaderboard.",
    )
    add_check(
        checks,
        "rq3_actionability_loop_visible",
        has_all(english_rq3_flat, ["Table~\\ref{tab:actionability}", "profile-spec", "Five of six patches improve"])
        and has_all(chinese_rq3_flat, ["profile specs", "5/6 patches", "median AP delta"]),
        "RQ3 connects diagnosis to executable profile-spec patches.",
    )
    add_check(
        checks,
        "rq3_failure_and_non_claims_visible",
        has_all(english_rq3_flat, ["failure interpretation", "not automatic boundary discovery", "not automatic patch selection"])
        and has_all(chinese_rq3_flat, ["failure interpretation", "不支持 automatic boundary discovery", "automatic patch selector"]),
        "RQ3 preserves OSWorld-Human failure interpretation and automatic-selector non-claims.",
    )
    add_check(
        checks,
        "support_runs_stay_supporting",
        all(token in combined for token in ["R330--R334", "R355", "R354", "R358"])
        and "fifth core experiment" in english_rq3
        and "额外小实验" in chinese_rq2,
        "Support runs remain support/ablation/repair evidence inside E2/E3.",
    )
    add_check(
        checks,
        "prior_gates_remain_passing",
        r377["status"] == "pass" and r378["status"] == "pass",
        "R379 builds on passing R377 main-claim and R378 table-budget gates.",
    )
    add_check(
        checks,
        "evaluation_ledger_mentions_r379",
        "R379" in evaluation and "claim-flow" in evaluation,
        "The evaluation ledger records this RQ2/RQ3 claim-flow guardrail.",
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
        "All R379 sources are tracked or intentionally dirty/staged.",
    )

    summary = {
        "checks_passed": sum(1 for check in checks if check["passed"]),
        "checks_total": len(checks),
        "rq_sections": 4,
        "paper_facing_blocks": 4,
        "empirical_profiling_experiments": 3,
        "artifact_blocks": 1,
    }
    return {
        "run_id": RUN_ID,
        "status": "pass" if all(check["passed"] for check in checks) else "fail",
        "schema": "agentsight.paper_rq2_rq3_claim_flow_gate.v1",
        "not_new_empirical_result": True,
        "network_access_required": False,
        "profiler_rerun": False,
        "data_sync": False,
        "checks": checks,
        "source_status": source_status,
        "summary": summary,
        "interpretation": (
            "RQ2/RQ3 now expose the profiling-paper claim flow before support-run details: "
            "comparison, success criterion, failure interpretation, mechanism, actionability, and non-claims."
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
        "# R379 RQ2/RQ3 Claim-Flow Gate",
        "",
        f"Status: `{report['status']}`",
        f"Checks: {report['summary']['checks_passed']}/{report['summary']['checks_total']}",
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
<title>{RUN_ID} RQ2/RQ3 Claim-Flow Gate</title>
<style>
body {{ font-family: system-ui, sans-serif; margin: 2rem; line-height: 1.45; }}
table {{ border-collapse: collapse; width: 100%; margin: 1rem 0; }}
th, td {{ border: 1px solid #d0d7de; padding: 0.45rem; vertical-align: top; }}
th {{ background: #f6f8fa; }}
.status {{ font-weight: 700; }}
</style>
<h1>{RUN_ID} RQ2/RQ3 Claim-Flow Gate</h1>
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
    (out_dir / "rq2-rq3-claim-flow-report.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (out_dir / "run-result.json").write_text(json.dumps(run_result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_csv(out_dir / "rq2-rq3-claim-flow-checks.csv", report["checks"])
    write_csv(out_dir / "source-status.csv", report["source_status"], ["source", "path", "status", "sha256"])
    write_markdown(out_dir / "rq2-rq3-claim-flow.md", report)
    write_html(out_dir / "index.html", report)
    print(json.dumps(run_result, indent=2, sort_keys=True))
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
