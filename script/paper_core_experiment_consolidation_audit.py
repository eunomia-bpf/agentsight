#!/usr/bin/env python3
"""R359: paper-facing core experiment consolidation audit.

This is a paper-organization gate, not a new empirical result. It verifies that
the current paper presents the evaluation as four core experiments, while the
R-numbered runs remain provenance, ablations, counterpoints, or audit gates.
It also checks that R358 is positioned as an E3 mechanism/actionability
ablation rather than a fifth main experiment.
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
DEFAULT_OUT_DIR = OUT_ROOT / "paper-core-experiments-r359"
RUN_ID = "R359"

SOURCE_PATHS = {
    "evaluation_ledger": ROOT / "docs" / "evaluation.md",
    "chinese_claim_setup": ROOT / "docs" / "visexp" / "paper" / "evaluation-claims-setup.zh-CN.md",
    "chinese_paper": ROOT / "docs" / "visexp" / "paper" / "main.tex",
    "english_paper": SUBMODULE_ROOT / "main.tex",
    "r358_report": OUT_ROOT / "operation-boundary-profile-patch-r358" / "boundary-profile-patch-report.json",
    "r358_run_result": OUT_ROOT / "operation-boundary-profile-patch-r358" / "run-result.json",
}

CORE_TOKENS = {
    "E1": ["E1", "Coverage", "coverage", "recursive", "folding", "递归"],
    "E2": ["E2", "Hidden-Label", "hidden-label", "localization", "ranking"],
    "E3": ["E3", "Mechanism", "mechanism", "actionability"],
    "E4": ["E4", "Reproducibility", "reproducibility", "claim integrity", "claim-integrity"],
}

MUST_NOT_CLAIM = [
    "automatic boundary discovery",
    "automatic patch selector",
    "automatic action selector",
    "human utility",
    "human/agent analyst",
    "complete trace-ecosystem compatibility",
    "完整 trace ecosystem",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    return parser.parse_args()


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
    try:
        rel = path.relative_to(ROOT)
    except ValueError:
        rel = path
    tracked = subprocess.run(
        ["git", "ls-files", "--error-unmatch", str(rel)],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if tracked.returncode != 0:
        return "untracked"
    dirty = subprocess.run(
        ["git", "diff", "--quiet", "--", str(rel)],
        cwd=ROOT,
        check=False,
    )
    if dirty.returncode != 0:
        return "tracked_hashed_dirty"
    return "tracked_hashed"


def add_check(
    rows: list[dict[str, Any]],
    check: str,
    condition: bool,
    evidence: str,
    *,
    expected: str = "pass",
) -> None:
    rows.append(
        {
            "check": check,
            "status": "pass" if condition else "fail",
            "expected": expected,
            "evidence": evidence,
        }
    )


def contains_all(text: str, tokens: list[str]) -> bool:
    return all(token in text for token in tokens)


def has_any(text: str, tokens: list[str]) -> bool:
    return any(token in text for token in tokens)


def count_regex(text: str, pattern: str) -> int:
    return len(re.findall(pattern, text, flags=re.MULTILINE))


def source_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for name, path in SOURCE_PATHS.items():
        rows.append(
            {
                "source": name,
                "path": str(path.relative_to(ROOT)),
                "status": git_status(path),
                "sha256": sha256(path),
            }
        )
    return rows


def build_checks(texts: dict[str, str], r358: dict[str, Any], r358_run: dict[str, Any]) -> list[dict[str, Any]]:
    checks: list[dict[str, Any]] = []
    evaluation = texts["evaluation_ledger"]
    claim_setup = texts["chinese_claim_setup"]
    zh = texts["chinese_paper"]
    en = texts["english_paper"]

    add_check(
        checks,
        "evaluation_has_four_core_experiment_table",
        "## Paper-Facing Core Experiments" in evaluation
        and all(f"| {eid}:" in evaluation for eid in CORE_TOKENS),
        "docs/evaluation.md has the paper-facing E1-E4 table.",
    )
    add_check(
        checks,
        "claim_setup_has_four_core_experiment_table",
        "## Paper-Facing Core Experiments" in claim_setup
        and "## Run/Artifact Provenance Map" in claim_setup
        and all(f"| {eid}：" in claim_setup for eid in CORE_TOKENS),
        "Chinese claim setup separates E1-E4 from the run/artifact provenance map.",
    )
    add_check(
        checks,
        "english_results_use_e1_e4_subsections",
        all(f"\\subsection{{{eid}:" in en for eid in CORE_TOKENS),
        "English paper has E1-E4 result subsections.",
    )
    add_check(
        checks,
        "chinese_results_use_e1_e4_subsections",
        all(f"\\subsection{{{eid}：" in zh for eid in CORE_TOKENS),
        "Chinese paper has E1-E4 result subsections.",
    )
    add_check(
        checks,
        "legacy_rq_structure_removed_from_papers",
        "\\subsection{RQ" not in zh
        and "\\subsection{RQ" not in en
        and "seven research questions" not in en,
        "No paper-facing RQ subsection or seven-research-question framing remains.",
    )
    add_check(
        checks,
        "chinese_main_result_table_is_core_experiment_table",
        "Core experiment & Workload / oracle & Main evidence & Scoped conclusion" in zh
        and "Paper question &" not in zh
        and count_regex(zh, r"^\s+E[1-4]:",) >= 4,
        "Chinese tab:results is now a four-row core-experiment table.",
    )
    add_check(
        checks,
        "r_runs_are_provenance_not_main_structure",
        "R-numbered runs are provenance" in evaluation
        and has_any(claim_setup, ["R 编号只作为 provenance", "R 编号保留为 artifact provenance"])
        and has_any(zh, ["R 编号只作为 provenance", "R 编号保留为 artifact provenance"])
        and has_any(en, ["Individual R-runs\nare provenance", "Individual R-runs are provenance"]),
        "Evaluation ledger, claim setup, Chinese paper, and English paper state that R runs are provenance.",
    )
    add_check(
        checks,
        "r358_is_e3_mechanism_not_fifth_experiment",
        "R358 is a mechanism ablation" in evaluation
        and "R358 是 R354 OSWorld-Human reject" in claim_setup
        and has_any(zh, ["R358 supports boundary-derived fields", "R358 支持 boundary-derived fields"])
        and "The result belongs to mechanism/actionability" in en
        and "E5" not in evaluation
        and "E5" not in claim_setup
        and "E5" not in zh
        and "E5" not in en,
        "R358 is described as an E3 mechanism/actionability ablation and no E5 core experiment exists.",
    )
    add_check(
        checks,
        "r358_artifact_numbers_match_paper_tokens",
        r358.get("status") == "pass"
        and r358_run.get("status") == "pass"
        and r358["summary"]["learned_boundary_ap"] == 0.2583
        and r358["summary"]["semantic_width_ap"] == 0.2402
        and r358["summary"]["learned_boundary_groups"] == 74
        and all(token in evaluation + claim_setup + zh + en for token in ["0.2583", "0.2402", "74"]),
        "R358 report/run-result pass and paper-facing texts include the AP/group tokens.",
    )
    add_check(
        checks,
        "r358_counterpoints_are_visible",
        r358["summary"]["learned_boundary_delta_top5_work_vs_semantic"] > 0
        and r358["summary"]["learned_boundary_delta_first_positive_work_vs_semantic"] > 0
        and has_any(evaluation, ["top-5 operation work increases", "top-5 work"])
        and has_any(claim_setup, ["top-5 operation work", "first-positive work"])
        and has_any(zh, ["top-5 operation work", "first-positive work"])
        and has_any(en, ["top-five operation work", "first-positive work"]),
        "R358 AP/group improvements and work counterpoints are both represented.",
    )
    add_check(
        checks,
        "two_abstraction_boundary_preserved",
        all("operation" in text and "operation stack" in text for text in [evaluation, claim_setup, zh, en])
        and "third profiler object" in en
        and "第三个 profiler 抽象" in zh,
        "All paper-facing texts keep operation and operation stack as the core abstractions.",
    )
    add_check(
        checks,
        "must_not_claim_guardrails_visible",
        all(
            has_any(
                evaluation + claim_setup + zh + en,
                [marker, marker.replace("-", " "), marker.replace("complete ", "full ")],
            )
            for marker in MUST_NOT_CLAIM
        ),
        "The four-experiment framing preserves must-not-claim guardrails.",
    )
    add_check(
        checks,
        "source_policy_visible",
        "no dataset sync" in evaluation
        and "不下载、不同步、不创建、不重标" in claim_setup
        and "不下载、不同步、不创建、不重标" in zh
        and "does not fetch, sync, or create data" in en,
        "The paper keeps the no-new-dataset/no-resync source policy visible.",
    )
    return checks


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def write_markdown(path: Path, payload: dict[str, Any]) -> None:
    lines = [
        "# R359 Core Experiment Consolidation Audit",
        "",
        f"- Status: `{payload['status']}`.",
        f"- Checks: {payload['summary']['checks_passed']}/{payload['summary']['checks_total']}.",
        f"- Core experiments: {', '.join(payload['summary']['core_experiments'])}.",
        f"- R358 learned-boundary AP/group result: {payload['summary']['r358_learned_boundary_ap']} AP, {payload['summary']['r358_learned_boundary_groups']} groups.",
        f"- R358 counterpoint: top-5 work delta {payload['summary']['r358_delta_top5_work_vs_semantic']}, first-positive-work delta {payload['summary']['r358_delta_first_positive_work_vs_semantic']}.",
        "",
        "## Checks",
        "",
        "| Check | Status | Evidence |",
        "|---|---|---|",
    ]
    for row in payload["checks"]:
        lines.append(f"| `{row['check']}` | {row['status']} | {row['evidence']} |")
    lines.extend(
        [
            "",
            "## Non-Claims",
            "",
            "- This is not a new empirical result.",
            "- This is not a human/agent analyst study.",
            "- This does not add a fifth core experiment.",
            "- This does not support automatic boundary discovery or an automatic selector.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def write_html(path: Path, payload: dict[str, Any]) -> None:
    rows = "\n".join(
        "<tr>"
        f"<td>{html.escape(row['check'])}</td>"
        f"<td>{html.escape(row['status'])}</td>"
        f"<td>{html.escape(row['evidence'])}</td>"
        "</tr>"
        for row in payload["checks"]
    )
    page = f"""<!doctype html>
<meta charset=\"utf-8\">
<title>R359 Core Experiment Consolidation Audit</title>
<style>
body {{ font-family: system-ui, sans-serif; margin: 2rem; line-height: 1.45; }}
table {{ border-collapse: collapse; width: 100%; }}
th, td {{ border: 1px solid #ddd; padding: 0.4rem; vertical-align: top; }}
th {{ background: #f6f6f6; }}
code {{ background: #f3f3f3; padding: 0.1rem 0.2rem; }}
</style>
<h1>R359 Core Experiment Consolidation Audit</h1>
<p>Status: <code>{html.escape(payload['status'])}</code></p>
<p>Checks: {payload['summary']['checks_passed']}/{payload['summary']['checks_total']}</p>
<table>
<thead><tr><th>Check</th><th>Status</th><th>Evidence</th></tr></thead>
<tbody>{rows}</tbody>
</table>
"""
    path.write_text(page, encoding="utf-8")


def main() -> None:
    args = parse_args()
    out_dir = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    start = time.time()
    texts = {
        name: read_text(path)
        for name, path in SOURCE_PATHS.items()
        if name not in {"r358_report", "r358_run_result"}
    }
    r358 = read_json(SOURCE_PATHS["r358_report"])
    r358_run = read_json(SOURCE_PATHS["r358_run_result"])
    checks = build_checks(texts, r358, r358_run)
    sources = source_rows()
    checks_passed = sum(row["status"] == "pass" for row in checks)
    status = "pass" if checks_passed == len(checks) else "fail"

    summary = {
        "checks_passed": checks_passed,
        "checks_total": len(checks),
        "core_experiments": ["E1", "E2", "E3", "E4"],
        "network_access_required": False,
        "not_new_empirical_result": True,
        "not_a_human_study_result": True,
        "not_an_agent_analyst_task_result": True,
        "not_new_dataset": True,
        "r358_learned_boundary_ap": r358["summary"]["learned_boundary_ap"],
        "r358_semantic_width_ap": r358["summary"]["semantic_width_ap"],
        "r358_learned_boundary_groups": r358["summary"]["learned_boundary_groups"],
        "r358_delta_top5_work_vs_semantic": r358["summary"]["learned_boundary_delta_top5_work_vs_semantic"],
        "r358_delta_first_positive_work_vs_semantic": r358["summary"]["learned_boundary_delta_first_positive_work_vs_semantic"],
    }
    payload = {
        "run_id": RUN_ID,
        "schema": "agentsight.paper_core_experiments.v1",
        "status": status,
        "elapsed_s": round(time.time() - start, 4),
        "claim": "paper evaluation is organized around four core experiments, not chronological R-run history",
        "summary": summary,
        "checks": checks,
        "source_status": sources,
        "non_claims": [
            "not a new empirical result",
            "not a human or agent analyst study",
            "not a fifth core experiment",
            "not automatic boundary discovery",
            "not an automatic action or patch selector",
        ],
    }

    report_json = out_dir / "core-experiment-report.json"
    report_md = out_dir / "core-experiment-report.md"
    checks_csv = out_dir / "core-experiment-checks.csv"
    source_csv = out_dir / "source-status.csv"
    html_path = out_dir / "index.html"
    run_result = out_dir / "run-result.json"

    report_json.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_markdown(report_md, payload)
    write_csv(checks_csv, checks, ["check", "status", "expected", "evidence"])
    write_csv(source_csv, sources, ["source", "path", "status", "sha256"])
    write_html(html_path, payload)
    run_result.write_text(
        json.dumps(
            {
                "run_id": RUN_ID,
                "status": status,
                "report": str(report_json.relative_to(ROOT)),
                "checks_passed": checks_passed,
                "checks_total": len(checks),
                "network_access_required": False,
                "not_new_empirical_result": True,
                "not_a_human_study_result": True,
                "not_new_dataset": True,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    print(
        json.dumps(
            {
                "run_id": RUN_ID,
                "status": status,
                "checks_passed": checks_passed,
                "checks_total": len(checks),
                "report": str(report_json.relative_to(ROOT)),
            },
            indent=2,
            sort_keys=True,
        )
    )
    if status != "pass":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
