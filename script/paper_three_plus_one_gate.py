#!/usr/bin/env python3
"""R376: three-plus-one paper-organization gate.

This guardrail checks that the paper presents three empirical profiling
experiments plus one artifact/reproducibility block. It reads tracked paper
text and existing guardrail artifacts only. It does not download data, relabel
traces, or rerun the profiler.
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
SUBMODULE_ROOT = ROOT / "docs" / "agentpprof-paper"
DEFAULT_OUT_DIR = OUT_ROOT / "paper-three-plus-one-r376"
RUN_ID = "R376"
SCRIPT_PATH = Path(__file__).resolve()

SOURCES = {
    "English paper": SUBMODULE_ROOT / "main.tex",
    "Chinese paper": ROOT / "docs" / "visexp" / "paper" / "main.tex",
    "Chinese user doc": ROOT / "docs" / "agentpprof-zh.md",
    "evaluation ledger": ROOT / "docs" / "evaluation.md",
    "R374 report": OUT_ROOT / "paper-core-experiment-weight-r374" / "core-experiment-weight-report.json",
    "R374 submodule table": SUBMODULE_ROOT / "figures" / "experiment-role-table.tex",
    "R375 report": OUT_ROOT / "paper-core-claim-gate-r375" / "core-claim-gate-report.json",
    "R375 submodule table": SUBMODULE_ROOT / "figures" / "claim-gate-table.tex",
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
    return rows


def add_check(checks: list[dict[str, Any]], name: str, passed: bool, detail: str) -> None:
    checks.append({"check": name, "passed": bool(passed), "detail": detail})


def build_report() -> dict[str, Any]:
    english = read_text(SOURCES["English paper"])
    chinese = read_text(SOURCES["Chinese paper"])
    zh_doc = read_text(SOURCES["Chinese user doc"])
    evaluation = read_text(SOURCES["evaluation ledger"])
    r374 = read_json(SOURCES["R374 report"])
    r374_table = read_text(SOURCES["R374 submodule table"])
    r375 = read_json(SOURCES["R375 report"])
    r375_table = read_text(SOURCES["R375 submodule table"])
    lower_eval = evaluation.lower()
    paper_blob = english + "\n" + chinese
    table_blob = r374_table + "\n" + r375_table
    guardrail_contract_blob = json.dumps(
        {
            "r374_role_rows": r374.get("role_rows", []),
            "r374_summary": r374.get("summary", {}),
            "r375_gate_rows": r375.get("gate_rows", []),
            "r375_summary": r375.get("summary", {}),
        },
        sort_keys=True,
    )
    checks: list[dict[str, Any]] = []
    source_status = source_rows()
    stale_eval_terms = [
        "systems/reproducibility question",
        "rq/core block",
        "four rq/core rows",
        "4 core experiment rows",
        "4 core rows",
        "core experiment row",
        "core-experiment role gate",
        "core experiment sufficiency audit",
        "substantial reviewer-facing experiments",
        "four paper-facing experiments",
        "four substantial rq/core experiments",
        "four main rq/core rows",
        "three-empirical-plus-one-systems",
    ]
    present_stale_eval_terms = [term for term in stale_eval_terms if term in lower_eval]

    add_check(
        checks,
        "upstream_gates_pass",
        r374.get("status") == "pass" and r375.get("status") == "pass",
        f"R374={r374.get('status')}; R375={r375.get('status')}",
    )
    add_check(
        checks,
        "english_three_plus_one",
        "three core empirical profiling experiments" in english
        and "artifact/reproducibility block" in english
        and "fourth empirical profiling experiment" in english,
        "English paper names three empirical profiling experiments plus one artifact/reproducibility block.",
    )
    add_check(
        checks,
        "chinese_three_plus_one",
        "三个核心经验性 profiling 实验" in chinese
        and "artifact/reproducibility block" in chinese
        and "第四个经验性 profiling 实验" in chinese,
        "Chinese paper names three empirical profiling experiments plus one artifact/reproducibility block.",
    )
    add_check(
        checks,
        "main_tables_are_paper_blocks",
        "RQ / paper block" in english and "RQ / paper block" in chinese,
        "Main result tables label rows as paper blocks rather than homogeneous fourth-experiment framing.",
    )
    add_check(
        checks,
        "role_and_claim_tables_are_paper_blocks",
        "Paper block" in table_blob
        and "Core experiment &" not in table_blob
        and "artifact replayability" in table_blob,
        "R374/R375 generated tables use paper-block terminology and label RQ4 as artifact replayability.",
    )
    add_check(
        checks,
        "role_and_claim_json_contracts_are_paper_blocks",
        "paper_block" in guardrail_contract_blob
        and "paper_blocks" in guardrail_contract_blob
        and "core_experiment" not in guardrail_contract_blob
        and "core_experiments" not in guardrail_contract_blob,
        "R374/R375 generated JSON contracts use paper-block keys rather than legacy homogeneous-experiment keys.",
    )
    add_check(
        checks,
        "r375_r374_source_hash_is_fresh",
        sha256(SOURCES["R374 report"])
        in {
            row.get("sha256")
            for row in r375.get("source_status", [])
            if row.get("path") == rel(SOURCES["R374 report"])
        },
        "R375 provenance records the current R374 report hash, preventing stale three-plus-one claim tables.",
    )
    add_check(
        checks,
        "no_four_core_research_question_framing",
        "four core research questions" not in english
        and "四个核心研究问题" not in chinese
        and "four core experiments" not in paper_blob,
        "Current paper text avoids framing E4 as a fourth core empirical experiment.",
    )
    add_check(
        checks,
        "evaluation_top_map_uses_three_plus_one",
        "three substantial empirical profiling experiments plus one artifact/reproducibility block" in evaluation
        and "fourth empirical profiling experiment" in evaluation
        and "| RQ / paper block |" in evaluation,
        "Evaluation ledger top map records the 3+1 structure.",
    )
    add_check(
        checks,
        "evaluation_has_no_stale_four_core_framing",
        not present_stale_eval_terms,
        "No stale homogeneous-experiment ledger terms remain; present="
        + (", ".join(present_stale_eval_terms) if present_stale_eval_terms else "none"),
    )
    add_check(
        checks,
        "chinese_user_doc_deemphasizes_flamegraph",
        zh_doc.startswith("# agentpprof: 用 operation stack 剖析 AI agent 轨迹")
        and "flamegraph 只是序列化形式之一，不是核心抽象" in zh_doc,
        "Chinese user doc no longer frames novelty as flamegraph-only.",
    )
    add_check(
        checks,
        "no_new_data_or_profiler_rerun",
        r374.get("data_sync") is False
        and r375.get("data_sync") is False
        and r374.get("profiler_rerun") is False
        and r375.get("profiler_rerun") is False,
        "R376 reads only paper text and existing guardrails; upstream gates did not sync data or rerun the profiler.",
    )
    add_check(
        checks,
        "source_status_tracked",
        all(row["status"] in {"tracked_clean", "tracked_dirty_allowed"} for row in source_status),
        "All R376 sources are tracked or dirty in this intentional edit.",
    )

    return {
        "run_id": RUN_ID,
        "status": "pass" if all(check["passed"] for check in checks) else "fail",
        "schema": "agentsight.paper_three_plus_one_gate.v1",
        "not_new_empirical_result": True,
        "network_access_required": False,
        "profiler_rerun": False,
        "data_sync": False,
        "checks": checks,
        "source_status": source_status,
        "summary": {
            "checks_passed": sum(1 for check in checks if check["passed"]),
            "checks_total": len(checks),
            "paper_blocks": 4,
            "empirical_profiling_experiments": 3,
            "artifact_reproducibility_blocks": 1,
        },
        "interpretation": "E1-E3 are the scientific profiling experiments; E4 is replayability/artifact evidence and must not be used as hidden-label accuracy evidence.",
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
        "# R376 Three-Plus-One Paper Gate",
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
<title>{RUN_ID} Three-Plus-One Paper Gate</title>
<style>
body {{ font-family: system-ui, sans-serif; margin: 2rem; line-height: 1.45; }}
table {{ border-collapse: collapse; width: 100%; margin: 1rem 0; }}
th, td {{ border: 1px solid #d0d7de; padding: 0.45rem; vertical-align: top; }}
th {{ background: #f6f8fa; }}
.status {{ font-weight: 700; }}
</style>
<h1>{RUN_ID} Three-Plus-One Paper Gate</h1>
<p class="status">Status: {html.escape(report['status'])}; checks {report['summary']['checks_passed']}/{report['summary']['checks_total']}.</p>
<p>{html.escape(report['interpretation'])}</p>
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
    (out_dir / "three-plus-one-report.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (out_dir / "run-result.json").write_text(json.dumps(run_result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_csv(out_dir / "three-plus-one-checks.csv", report["checks"])
    write_csv(out_dir / "source-status.csv", report["source_status"], ["source", "path", "status", "sha256"])
    write_markdown(out_dir / "three-plus-one.md", report)
    write_html(out_dir / "index.html", report)
    print(json.dumps(run_result, indent=2, sort_keys=True))
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
