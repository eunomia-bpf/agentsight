#!/usr/bin/env python3
"""R380: experiment-block consolidation gate.

This paper-integration guardrail checks that the current papers present the
evaluation as three substantial empirical profiling experiments plus one
artifact/reproducibility block. R-numbered runs may appear as provenance,
ablations, counterpoints, or hygiene gates, but they must not define the main
paper organization or reintroduce a chronological run ledger.
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
DEFAULT_OUT_DIR = OUT_ROOT / "paper-experiment-block-consolidation-r380"
RUN_ID = "R380"
SCRIPT_PATH = Path(__file__).resolve()
PAPER_SUBMODULE = ROOT / "docs" / "agentpprof-paper"
PAPER_SUBMODULE_PATH = "docs/agentpprof-paper"

SOURCES = {
    "R377 claim evidence": OUT_ROOT / "paper-main-claim-evidence-r377" / "main-claim-evidence-report.json",
    "R378 table budget": OUT_ROOT / "paper-main-body-table-budget-r378" / "main-body-table-budget-report.json",
    "R379 claim flow": OUT_ROOT / "paper-rq2-rq3-claim-flow-r379" / "rq2-rq3-claim-flow-report.json",
    "English paper": PAPER_SUBMODULE / "main.tex",
    "Chinese paper": ROOT / "docs" / "visexp" / "paper" / "main.tex",
    "evaluation ledger": ROOT / "docs" / "evaluation.md",
}

STALE_CHINESE_LEDGER_SNIPPETS = [
    "R321 用同一份 R300",
    "R322 进一步让 Rust JSON profile",
    "R323 把该反例转化为 rank-mode",
    "R324 把 per-operation visible feature density",
    "R325 在同一 Rust profile-spec 路径",
    "R326 进一步测试 rank-policy robustness",
    "R329 再做 target-held-out transfer",
    "R327 再把这些可提交 profile specs",
    "R328 在同一 76 个 specs 上启用",
]

STALE_ENGLISH_LEDGER_SNIPPETS = [
    "The Rust mechanism ablations isolate where those diagnoses come from. Stack-text",
    "R345/R346/R347 present the same evidence",
    "R350 packages this into bounded evidence packets",
    "R327/R328 are the empirical content of this subsection",
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


def squish(text: str) -> str:
    return " ".join(text.split())


def count_r_run_refs(text: str) -> int:
    return len(re.findall(r"\bR3[0-9]{2}\b", text))


def section_between(text: str, start: str, end: str) -> str:
    start_i = text.index(start)
    end_i = text.index(end, start_i)
    return text[start_i:end_i]


def build_report() -> dict[str, Any]:
    prior_reports = {name: read_json(path) for name, path in SOURCES.items() if name.startswith("R")}
    english = read_text(SOURCES["English paper"])
    chinese = read_text(SOURCES["Chinese paper"])
    evaluation = read_text(SOURCES["evaluation ledger"])
    source_status = source_rows()
    source_by_name = {row["source"]: row for row in source_status}
    combined = english + "\n" + chinese
    english_results = section_between(english, "\\section{Results}", "\\section{Related Work")
    chinese_results = section_between(chinese, "\\section{结果}", "\\section{哪些数据集最适合}")
    chinese_impl = section_between(chinese, "\\section{实现}", "\\section{实验方法}")
    english_rq3 = section_between(english, "\\subsection{RQ3/E3", "\\subsection{RQ4/E4")
    chinese_rq3 = section_between(chinese, "\\subsection{RQ3/E3", "\\subsection{RQ4/E4")

    checks: list[dict[str, Any]] = []
    add_check(
        checks,
        "three_plus_one_structure_visible",
        "three core empirical profiling experiments" in english
        and "artifact/reproducibility block" in english
        and "三个核心经验性 profiling 实验" in chinese
        and "artifact/reproducibility block" in chinese,
        "Both papers state the 3 empirical + 1 artifact/reproducibility organization.",
    )
    add_check(
        checks,
        "paper_blocks_have_subsections",
        all(token in english_results for token in ["RQ1/E1", "RQ2/E2", "RQ3/E3", "RQ4/E4"])
        and all(token in chinese_results for token in ["RQ1/E1", "RQ2/E2", "RQ3/E3", "RQ4/E4"]),
        "The results sections expose RQ1/E1 through RQ4/E4 as the paper-facing blocks.",
    )
    add_check(
        checks,
        "run_ids_are_provenance_not_structure",
        "R-numbered runs are provenance" in english
        and "Individual R-runs are provenance" in english
        and "R 编号只作为 provenance" in chinese
        and "不是按 R 编号罗列小实验" in chinese,
        "Run IDs are explicitly demoted to provenance/support roles.",
    )
    add_check(
        checks,
        "stale_chinese_implementation_ledger_removed",
        not any(snippet in chinese_impl for snippet in STALE_CHINESE_LEDGER_SNIPPETS)
        and all(token in chinese_impl for token in ["接口验证", "E3 mechanism/actionability block", "归入 E4"]),
        "The Chinese implementation section no longer narrates R321-R329/R327-R328 chronologically.",
    )
    add_check(
        checks,
        "stale_english_rq3_ledger_removed",
        not any(snippet in english_rq3 for snippet in STALE_ENGLISH_LEDGER_SNIPPETS)
        and all(token in english_rq3 for token in ["single E3 mechanism block", "one E3 actionability block", "not a fifth core experiment"]),
        "The English RQ3 section presents mechanism/actionability blocks rather than chronological support-run paragraphs.",
    )
    add_check(
        checks,
        "chinese_rq3_block_language_visible",
        all(token in chinese_rq3 for token in ["E3 mechanism block", "E3 actionability block", "不是第五个核心实验"]),
        "The Chinese RQ3 section names the mechanism/actionability blocks and keeps the fifth-experiment guardrail.",
    )
    add_check(
        checks,
        "main_tables_remain_budgeted",
        all(
            label in combined
            for label in [
                "tab:core-results",
                "tab:e2-localization",
                "fig:e2e3-portfolio",
                "tab:actionability",
            ]
        )
        and "tab:visualization-portfolio" not in combined
        and "tab:r373-verdict" not in combined,
        "Current core displays remain; demoted support-artifact tables do not return to the main body.",
    )
    add_check(
        checks,
        "claim_facets_remain_inside_blocks",
        all(
            token in combined
            for token in [
                "hidden-label localization",
                "less inspection work",
                "fragmentation tradeoff",
                "profile-configuration actionability",
                "mechanism isolation",
            ]
        ),
        "The five claim facets remain routed through E2/E3 instead of becoming five experiments.",
    )
    add_check(
        checks,
        "non_claims_preserved",
        all(
            token in combined
            for token in [
                "human-productivity",
                "automatic boundary discovery",
                "automatic patch selection",
                "complete compatibility",
            ]
        )
        and all(
            token in chinese
            for token in ["human productivity", "automatic boundary discovery", "metric dominance", "trace ecosystem"]
        ),
        "Both papers preserve the non-claims needed for scoped profiling-paper wording.",
    )
    add_check(
        checks,
        "support_run_density_bounded",
        count_r_run_refs(english_results) <= 45
        and count_r_run_refs(chinese_results) <= 90
        and all(token in chinese_results for token in ["同一个 E2 主实验", "E3 actionability block", "E4 replayability block"])
        and all(token in english_results for token in ["single E3 mechanism block", "one E3 actionability block", "provenance for this E4 block"]),
        (
            "R-run references are bounded and explicitly labeled as support/provenance inside "
            f"E1-E4: English={count_r_run_refs(english_results)}, Chinese={count_r_run_refs(chinese_results)}."
        ),
    )
    add_check(
        checks,
        "prior_gates_remain_passing",
        all(report["status"] == "pass" for report in prior_reports.values()),
        "R377/R378/R379 remain passing inputs for this consolidation gate.",
    )
    add_check(
        checks,
        "evaluation_ledger_mentions_r380",
        "R380" in evaluation and "experiment-block consolidation" in evaluation,
        "The evaluation ledger records this consolidation gate.",
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
        "All R380 sources are tracked or intentionally dirty/staged.",
    )

    summary = {
        "checks_passed": sum(1 for check in checks if check["passed"]),
        "checks_total": len(checks),
        "paper_facing_blocks": 4,
        "empirical_profiling_experiments": 3,
        "artifact_blocks": 1,
        "english_results_r_run_refs": count_r_run_refs(english_results),
        "chinese_results_r_run_refs": count_r_run_refs(chinese_results),
    }
    return {
        "run_id": RUN_ID,
        "status": "pass" if all(check["passed"] for check in checks) else "fail",
        "schema": "agentsight.paper_experiment_block_consolidation_gate.v1",
        "not_new_empirical_result": True,
        "network_access_required": False,
        "profiler_rerun": False,
        "data_sync": False,
        "checks": checks,
        "source_status": source_status,
        "summary": summary,
        "interpretation": (
            "The paper-facing evaluation remains three empirical profiling experiments plus one "
            "artifact/reproducibility block; support runs are provenance inside those blocks rather "
            "than chronological main experiments."
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
        "# R380 Experiment-Block Consolidation Gate",
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
<title>{RUN_ID} Experiment-Block Consolidation Gate</title>
<style>
body {{ font-family: system-ui, sans-serif; margin: 2rem; line-height: 1.45; }}
table {{ border-collapse: collapse; width: 100%; margin: 1rem 0; }}
th, td {{ border: 1px solid #d0d7de; padding: 0.45rem; vertical-align: top; }}
th {{ background: #f6f8fa; }}
.status {{ font-weight: 700; }}
</style>
<h1>{RUN_ID} Experiment-Block Consolidation Gate</h1>
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
    (out_dir / "experiment-block-consolidation-report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (out_dir / "run-result.json").write_text(json.dumps(run_result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_csv(out_dir / "experiment-block-consolidation-checks.csv", report["checks"])
    write_csv(out_dir / "source-status.csv", report["source_status"], ["source", "path", "status", "sha256"])
    write_markdown(out_dir / "experiment-block-consolidation.md", report)
    write_html(out_dir / "index.html", report)
    print(json.dumps(run_result, indent=2, sort_keys=True))
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
