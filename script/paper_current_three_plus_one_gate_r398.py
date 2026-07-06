#!/usr/bin/env python3
"""R398: current three-plus-one experiment organization gate.

This is a paper-organization regression guard for the current drafts. It checks
that the Chinese and English papers still present the evaluation as three core
empirical profiling experiments plus one replayability/scope-control block, with
R-numbered runs confined to the evaluation ledger and artifacts. It reads only
tracked paper/docs/gate outputs; it does not fetch datasets, relabel traces,
rerun the profiler, or run a human/agent analyst task.
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
DEFAULT_OUT_DIR = OUT_ROOT / "paper-current-three-plus-one-r398"
RUN_ID = "R398"
SCRIPT_PATH = Path(__file__).resolve()
PAPER_SUBMODULE = ROOT / "docs" / "agentpprof-paper"
PAPER_SUBMODULE_PATH = "docs/agentpprof-paper"

SOURCES = {
    "Chinese paper": ROOT / "docs" / "visexp" / "paper" / "main.tex",
    "English paper": PAPER_SUBMODULE / "main.tex",
    "evaluation ledger": ROOT / "docs" / "evaluation.md",
    "idea story": ROOT / "docs" / "idea-story.md",
    "R395 claim/verdict alignment": OUT_ROOT / "paper-main-claim-verdict-alignment-r395" / "run-result.json",
    "R396 paper build smoke": OUT_ROOT / "paper-build-smoke-r396" / "run-result.json",
    "R397 anti-run-ledger": OUT_ROOT / "paper-main-body-run-ledger-r397" / "run-result.json",
}

RQ_RE = re.compile(r"\\subsection\{(RQ\d+/E\d+)")
RUN_ID_RE = re.compile(r"\bR\d{3}\b")
EXPECTED_RQS = ["RQ1/E1", "RQ2/E2", "RQ3/E3", "RQ4/E4"]
INTERNAL_STYLE_PATTERNS = [
    "Claim synthesis",
    "reviewer evidence packet",
    "reviewer evidence packets",
    "paper value/novelty synthesis",
    "paper evidence matrix",
    "submission audit",
    "RQ setup",
    "Claim test",
    "Claim-test",
    "claim gate",
    "determinism gate",
    "reproducibility gate",
    "reproducibility gates",
    "Experiment contract",
    "实验契约",
    "artifact ledger",
    "case and verdict artifacts",
    "generated case",
    "case 和 verdict outputs",
    "生成的 case",
    "run ledger",
    "run-role map",
    "R-numbered",
    "source-status",
    "claim-integrity",
    "reviewer-style",
    "paper gates",
    "Gate / counterpoint",
    "supports-with-counterpoints",
    "artifact/reproducibility",
    "supporting artifact index",
    "artifact hygiene",
    "claim hygiene",
    "claim-hygiene",
    "guardrail",
    "guardrails",
    "audit gates",
    "table-provenance gate",
]
SELF_UNDERCUT_PATTERNS = [
    re.compile(r"不是\s*(?:OSDI|NeurIPS|NIPS)[^。\\]*(?:最终接收|接受级|完整证据)"),
    re.compile(r"证据不足[^。\\]*(?:OSDI|NeurIPS|NIPS|接收|接受)"),
    re.compile(r"not [^.\\]*(?:OSDI|NeurIPS|NIPS)[^.\\]*(?:accepted|complete evidence|submission-ready)"),
    re.compile(r"insufficient [^.\\]*(?:evidence|support)[^.\\]*(?:OSDI|NeurIPS|NIPS|acceptance|accepted)"),
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


def subsection_rqs(text: str) -> list[str]:
    return RQ_RE.findall(text)


def run_id_hits(path: Path) -> list[dict[str, Any]]:
    hits = []
    for line_no, line in enumerate(read_text(path).splitlines(), start=1):
        matches = sorted(set(RUN_ID_RE.findall(line)))
        if matches:
            hits.append({"path": rel(path), "line": line_no, "run_ids": ",".join(matches), "text": line.strip()})
    return hits


def internal_style_hits(path: Path) -> list[dict[str, Any]]:
    hits = []
    for line_no, line in enumerate(read_text(path).splitlines(), start=1):
        line_l = line.lower()
        matches = [
            pattern
            for pattern in INTERNAL_STYLE_PATTERNS
            if pattern in line or pattern.lower() in line_l
        ]
        if matches:
            hits.append({"path": rel(path), "line": line_no, "patterns": " | ".join(matches), "text": line.strip()})
    return hits


def self_undercut_hits(path: Path) -> list[dict[str, Any]]:
    hits = []
    for line_no, line in enumerate(read_text(path).splitlines(), start=1):
        matched = [pattern.pattern for pattern in SELF_UNDERCUT_PATTERNS if pattern.search(line)]
        if matched:
            hits.append({"path": rel(path), "line": line_no, "patterns": " | ".join(matched), "text": line.strip()})
    return hits


def build_report() -> dict[str, Any]:
    chinese = read_text(SOURCES["Chinese paper"])
    english = read_text(SOURCES["English paper"])
    evaluation = read_text(SOURCES["evaluation ledger"])
    idea = read_text(SOURCES["idea story"])
    chinese_norm = normalize(chinese)
    english_norm = normalize(english)
    evaluation_norm = normalize(evaluation)
    idea_norm = normalize(idea)
    english_l = english_norm.lower()
    evaluation_l = evaluation_norm.lower()
    idea_l = idea_norm.lower()
    prereqs = {
        name: read_json(path).get("status", "")
        for name, path in SOURCES.items()
        if path.suffix == ".json"
    }
    chinese_rqs = subsection_rqs(chinese)
    english_rqs = subsection_rqs(english)
    paper_run_hits = run_id_hits(SOURCES["Chinese paper"]) + run_id_hits(SOURCES["English paper"])
    chinese_internal_style_hits = internal_style_hits(SOURCES["Chinese paper"])
    main_paper_internal_style_hits = chinese_internal_style_hits + internal_style_hits(SOURCES["English paper"])
    paper_self_undercut_hits = self_undercut_hits(SOURCES["Chinese paper"]) + self_undercut_hits(
        SOURCES["English paper"]
    )
    source_status = source_rows()

    checks: list[dict[str, Any]] = []
    add_check(
        checks,
        "prerequisite_gates_pass",
        prereqs == {
            "R395 claim/verdict alignment": "pass",
            "R396 paper build smoke": "pass",
            "R397 anti-run-ledger": "pass",
        },
        f"Prerequisite statuses={prereqs}",
    )
    add_check(
        checks,
        "papers_have_exactly_four_rq_subsections",
        chinese_rqs == EXPECTED_RQS and english_rqs == EXPECTED_RQS,
        f"Chinese RQs={chinese_rqs}; English RQs={english_rqs}",
    )
    add_check(
        checks,
        "three_plus_one_stated_in_both_papers",
        "three core empirical profiling experiments" in english_l
        and "replayability/scope-control block" in english_l
        and "not additional main experiments" in english_l
        and (
            "三个核心经验性 profiling 实验" in chinese_norm
            or "前三个问题是 empirical profiling experiments" in chinese_norm
        )
        and "replayability/scope-control block" in chinese_norm
        and "不会形成额外主实验" in chinese_norm,
        "Both drafts state E1-E3 as core empirical profiling experiments and E4 as replayability/scope-control.",
    )
    add_check(
        checks,
        "e2_is_single_hidden_label_accuracy_block",
        "e2 is the single hidden-label localization/ranking experiment" in english_l
        and "e2 is the only primary hidden-label accuracy" in english_l
        and (
            "E2 是唯一的 hidden-label localization/ranking 主实验" in chinese_norm
            or "RQ2 是 hidden-label localization/ranking 主实验" in chinese_norm
        )
        and (
            "E2 是唯一的 hidden-label accuracy" in chinese_norm
            or "主 accuracy claim 仍然来自统一的 hidden-label scoring" in chinese_norm
        ),
        "Hidden-label profiler accuracy is concentrated in E2 rather than split into many small experiments.",
    )
    add_check(
        checks,
        "e3_is_mechanism_actionability_not_fifth_experiment",
        "which stack fields, mappings, rankers, and profile specs explain or repair the e2 results" in english_l
        and "not a fifth core experiment" in english_l
        and (
            "哪些 stack fields、mappings、rankers 和 profile specs 造成或修复 E2 的结果" in chinese_norm
            or "Rank-feature、mapping、stack-depth、boundary-field、profile-spec patch" in chinese_norm
        )
        and ("不是第五个核心实验" in chinese_norm or "不是新增实验" in chinese_norm),
        "Mechanism, actionability, patches, and boundary-field evidence remain inside E3.",
    )
    add_check(
        checks,
        "e4_is_replay_scope_not_accuracy_or_ecosystem_claim",
        "e4 is the replayability, offline-cost, and scope-control block" in english_l
        and "not treated as a fourth hidden-label accuracy result" in english_l
        and "not a human-productivity claim" in english_l
        and re.search(r"not [^.\\]*trace-ecosystem compatibility result", english_l) is not None
        and (
            "RQ4 检查 offline profiler path 能否在 tracked inputs 上低成本 replay" in chinese_norm
            or "replayability/scope-control claim" in chinese_norm
        )
        and (
            "不是新的 accuracy benchmark" in chinese_norm
            or "不是新的 hidden-label accuracy experiment" in chinese_norm
        )
        and "不是人工 analyst" in chinese_norm
        and re.search(r"不是[^。\\]*trace-ecosystem compatibility claim", chinese_norm) is not None,
        "E4 remains a replayability/scope-control block with explicit non-claims.",
    )
    add_check(
        checks,
        "main_papers_stay_free_of_run_ids",
        not paper_run_hits,
        f"Found {len(paper_run_hits)} R-numbered run-id mentions in main paper bodies.",
    )
    add_check(
        checks,
        "main_papers_avoid_internal_checklist_terms",
        not main_paper_internal_style_hits,
        f"Found {len(main_paper_internal_style_hits)} internal checklist-style terms in the Chinese/English main papers.",
    )
    add_check(
        checks,
        "main_papers_avoid_venue_self_undercut",
        not paper_self_undercut_hits,
        (
            "Found "
            f"{len(paper_self_undercut_hits)} paper-facing venue-readiness self-undercut phrases; "
            "limitations should bound the scoped profiling claim rather than disclaiming top-tier evidence."
        ),
    )
    add_check(
        checks,
        "ledger_keeps_runs_as_provenance",
        "r-numbered runs are provenance, not the paper's evaluation structure" in evaluation_l
        and "not part of the hidden-label accuracy comparison" in evaluation_l
        and "not a fifth experiment" in evaluation_l
        and "source/command` lines below are provenance inventories" in evaluation_l
        and "main-body run-ledger suppression gate" in evaluation_l,
        "The evaluation ledger records run IDs as provenance/support/scope checks rather than main-paper structure.",
    )
    add_check(
        checks,
        "new_runs_must_strengthen_core_blocks",
        "new runs are allowed only when they strengthen one of these blocks" in evaluation_l
        and "primary comparison, ablation, stress/counterpoint, provenance check, or scope check" in evaluation_l
        and "additional analyses enter the paper only when they strengthen one of these four blocks" in english_l
        and "primary comparison, ablation, counterpoint, provenance check, or scope check" in english_l
        and (
            "只保留能够支撑 claim 的比较、消融、反例和复现实验" in chinese_norm
            and "其他分析只作为补充材料中的证据来源" in chinese_norm
        ),
        "New runs must be assigned a role inside E1-E4 instead of becoming scattered paper experiments.",
    )
    add_check(
        checks,
        "main_display_path_visible",
        "the main-paper displays follow this path" in english_l
        and "table~\\ref{tab:core-results} is the four-block claim map" in english_l
        and "provide hidden-label fidelity and baseline tradeoff evidence" in english_l
        and "provide mechanism/actionability evidence" in english_l
        and "supporting materials contain the larger portfolio, case, verdict, and consistency tables" in english_l
        and ("主文图表按这条路径阅读" in chinese_norm or "主文图表形成一条固定证据路径" in chinese_norm)
        and "表~\\ref{tab:results} 是四个 block 的 claim map" in chinese_norm
        and "hidden-label fidelity 和 baseline tradeoff" in chinese_norm
        and "mechanism/actionability" in chinese_norm
        and "补充的 portfolio、case 和 verdict 视图只用于解释这些主图表的数据来源、反例和适用边界" in chinese_norm,
        "The papers expose a compact display path from workload provenance through E1-E4 main displays.",
    )
    add_check(
        checks,
        "canonical_next_action_rejects_small_experiment_sprawl",
        "the next gate is prose and figure/table polish, not more small experiments" in idea_l
        and "do not add another empirical block unless it strengthens e1, e2, e3, or e4 directly" in idea_l
        and (
            "keep r-numbered provenance in the ledger rather than the main paper bodies" in idea_l
            or "keep r-numbered provenance and internal process vocabulary out of the main paper bodies" in idea_l
        ),
        "The idea story preserves the next-action rule against scattered new empirical blocks.",
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
        "schema": "agentsight.paper_current_three_plus_one_gate.v1",
        "network_access_required": False,
        "data_sync": False,
        "profiler_rerun": False,
        "human_or_agent_analyst_task": False,
        "paper_run_id_hits": paper_run_hits,
        "chinese_internal_style_hits": chinese_internal_style_hits,
        "main_paper_internal_style_hits": main_paper_internal_style_hits,
        "paper_self_undercut_hits": paper_self_undercut_hits,
        "checks": checks,
        "source_status": source_status,
        "summary": {
            "checks_passed": sum(1 for check in checks if check["passed"]),
            "checks_total": len(checks),
            "chinese_rq_subsections": chinese_rqs,
            "english_rq_subsections": english_rqs,
            "main_paper_run_id_hits": len(paper_run_hits),
            "chinese_internal_style_hits": len(chinese_internal_style_hits),
            "main_paper_internal_style_hits": len(main_paper_internal_style_hits),
            "paper_self_undercut_hits": len(paper_self_undercut_hits),
        },
        "interpretation": (
            "The current paper organization remains three empirical profiling "
            "experiments plus one replayability/scope-control block. R-numbered "
            "runs are ledger provenance, support, ablations, counterpoints, or "
            "scope checks, not main-paper mini-experiments."
        ),
    }


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


def write_markdown(path: Path, report: dict[str, Any]) -> None:
    lines = [
        "# R398 Current Three-Plus-One Organization Gate",
        "",
        f"Status: `{report['status']}`",
        f"Checks: {report['summary']['checks_passed']}/{report['summary']['checks_total']}",
        f"Main-paper run-id hits: {report['summary']['main_paper_run_id_hits']}",
        f"Main-paper internal-style hits: {report['summary']['main_paper_internal_style_hits']}",
        f"Chinese internal-style hits: {report['summary']['chinese_internal_style_hits']}",
        f"Paper-facing self-undercut hits: {report['summary']['paper_self_undercut_hits']}",
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
<title>{RUN_ID} Current Three-Plus-One Gate</title>
<style>
body {{ font-family: system-ui, sans-serif; margin: 2rem; line-height: 1.45; }}
table {{ border-collapse: collapse; width: 100%; margin: 1rem 0; }}
th, td {{ border: 1px solid #d0d7de; padding: 0.45rem; vertical-align: top; }}
th {{ background: #f6f8fa; }}
.status {{ font-weight: 700; }}
</style>
<h1>{RUN_ID} Current Three-Plus-One Organization Gate</h1>
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
    (out_dir / "current-three-plus-one-report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (out_dir / "run-result.json").write_text(json.dumps(run_result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_csv(out_dir / "current-three-plus-one-checks.csv", report["checks"])
    write_csv(out_dir / "paper-run-id-hits.csv", report["paper_run_id_hits"], ["path", "line", "run_ids", "text"])
    write_csv(
        out_dir / "chinese-internal-style-hits.csv",
        report["chinese_internal_style_hits"],
        ["path", "line", "patterns", "text"],
    )
    write_csv(
        out_dir / "main-paper-internal-style-hits.csv",
        report["main_paper_internal_style_hits"],
        ["path", "line", "patterns", "text"],
    )
    write_csv(
        out_dir / "paper-self-undercut-hits.csv",
        report["paper_self_undercut_hits"],
        ["path", "line", "patterns", "text"],
    )
    write_csv(out_dir / "source-status.csv", report["source_status"], ["source", "path", "status", "sha256"])
    write_markdown(out_dir / "current-three-plus-one.md", report)
    write_html(out_dir / "index.html", report)
    print(json.dumps(run_result, indent=2, sort_keys=True))
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
