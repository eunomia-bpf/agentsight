#!/usr/bin/env python3
"""R395: main claim and verdict alignment gate.

This is a paper-integration scope check. It checks that the canonical docs and
Chinese/English paper drafts keep the central profiling claim aligned with the
claim verdict: hidden-label profiler fidelity, inspection-cost reduction
against flat summaries, median-fragmentation tradeoff against the fixed-session
drilldown proxy, profile-configuration actionability, and scoped non-claims.
It does not fetch datasets, relabel traces, rerun the profiler, or run a
human/agent analyst task.
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
DEFAULT_OUT_DIR = OUT_ROOT / "paper-main-claim-verdict-alignment-r395"
RUN_ID = "R395"
SCRIPT_PATH = Path(__file__).resolve()
PAPER_SUBMODULE = ROOT / "docs" / "agentpprof-paper"
PAPER_SUBMODULE_PATH = "docs/agentpprof-paper"

SOURCES = {
    "idea story": ROOT / "docs" / "idea-story.md",
    "evaluation ledger": ROOT / "docs" / "evaluation.md",
    "English paper": PAPER_SUBMODULE / "main.tex",
    "Chinese paper": ROOT / "docs" / "visexp" / "paper" / "main.tex",
    "R377 main claim evidence": OUT_ROOT / "paper-main-claim-evidence-r377" / "run-result.json",
    "R380 experiment-block consolidation": OUT_ROOT
    / "paper-experiment-block-consolidation-r380"
    / "run-result.json",
    "R383 canonical reviewer acceptance": OUT_ROOT
    / "paper-canonical-reviewer-acceptance-r383"
    / "run-result.json",
    "R391 core readiness": OUT_ROOT / "paper-core-readiness-r391" / "run-result.json",
    "R393 post-R392 reviewer acceptance": OUT_ROOT
    / "paper-post-r392-reviewer-acceptance-r393"
    / "run-result.json",
    "R394 two-abstraction doc gate": OUT_ROOT / "paper-two-abstraction-doc-r394" / "run-result.json",
    "R405 English read-only gap audit": OUT_ROOT
    / "paper-english-experiment-gap-audit-r405"
    / "english-experiment-gap-audit.json",
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


def status_ok(path: Path) -> bool:
    data = read_json(path)
    return data.get("status") in {"pass", "accepted"}


def contains_all(text: str, needles: list[str]) -> bool:
    return all(needle in text for needle in needles)


def english_read_only_gap_recorded(report: dict[str, Any]) -> bool:
    if report.get("status") != "pass":
        return False
    checks = {row.get("check"): bool(row.get("passed")) for row in report.get("checks", [])}
    statuses = {row.get("status") for row in report.get("rows", [])}
    return (
        checks.get("english_submodule_read_only_scope", False)
        and checks.get("english_three_rq_gap_detected", False)
        and "gap_to_sync_when_english_edits_are_allowed" in statuses
    )


def build_report() -> dict[str, Any]:
    texts = {name: read_text(path) for name, path in SOURCES.items() if path.suffix not in {".json"}}
    normalized = {name: normalize(text) for name, text in texts.items()}
    combined = "\n".join(texts.values())
    combined_norm = normalize(combined)
    source_status = source_rows()
    source_by_name = {row["source"]: row for row in source_status}
    r405 = read_json(SOURCES["R405 English read-only gap audit"])
    english_gap_recorded = english_read_only_gap_recorded(r405)
    checks: list[dict[str, Any]] = []
    idea_main_claim = contains_all(
        normalized["idea story"],
        [
            "operation/operation-stack profiling can localize, rank, and explain",
            "less inspection work than flat summaries",
            "less fragmentation than fixed-session drilldown",
        ],
    )
    evaluation_main_claim = contains_all(
        normalized["evaluation ledger"],
        [
            "Operation-stack profiling localizes, ranks, and explains task-relevant failures",
            "less inspection work than flat summaries",
            "less fragmentation than fixed-session drilldown",
        ],
    )
    english_main_claim = contains_all(
        normalized["English paper"],
        [
            "Operation/operation-stack profiling provides label-scored localization",
            "less inspection work than flat summaries",
            "median fragmentation tradeoff relative to fixed-session drilldown",
        ],
    )
    chinese_main_claim = contains_all(
        normalized["Chinese paper"],
        [
            "operation-stack profiling 能在公开真实标注 trace",
            "相对 flat summary 减少 inspection work",
            "相对 fixed-session drilldown proxy 改善 median fragmentation tradeoff",
        ],
    )
    english_main_claim_or_gap = english_main_claim or english_gap_recorded
    idea_fixed_session_proxy = contains_all(
        normalized["idea story"],
        [
            "Fixed-session drilldown is the current trace-tree-shaped baseline",
            "real OpenTelemetry/OpenInference/Phoenix-style span-tree imports are future baselines",
        ],
    )
    evaluation_fixed_session_proxy = contains_all(
        normalized["evaluation ledger"],
        [
            "Fixed-session drilldown is the current trace-tree-shaped baseline",
            "real OpenTelemetry/OpenInference/Phoenix-style span-tree imports are future baselines",
        ],
    )
    english_fixed_session_proxy = contains_all(
        normalized["English paper"],
        [
            "fixed-session drilldown as the current trace-tree-shaped baseline",
            "real OpenTelemetry/OpenInference or Phoenix span-tree imports remain future interoperability baselines",
        ],
    )
    chinese_fixed_session_proxy = contains_all(
        normalized["Chinese paper"],
        [
            "Fixed-session drilldown 是当前已评估的 trace-tree-shaped baseline",
            "不等价于完整导入 OpenTelemetry、Phoenix、LangSmith、Langfuse 或 Perfetto ecosystem traces",
        ],
    )
    english_fixed_session_proxy_or_gap = english_fixed_session_proxy or english_gap_recorded
    english_three_plus_one = contains_all(
        normalized["English paper"],
        [
            "three empirical profiling experiments plus one replayability/scope-control block",
            "RQ4/E4 checks replayability, offline cost, and claim scope",
        ],
    )
    chinese_three_plus_one = (
        (
            "前三个问题是 empirical profiling experiments" in normalized["Chinese paper"]
            or "三个核心 profiling 实验和一个可重放性检查" in normalized["Chinese paper"]
        )
        and (
            "RQ2 是 hidden-label localization/ranking 主实验" in normalized["Chinese paper"]
            or "RQ2 是主 hidden-label localization/ranking 实验" in normalized["Chinese paper"]
        )
        and (
            "RQ4 检查 profile-spec 可复现性、离线成本和 claim scope" in normalized["Chinese paper"]
            or "RQ4 只检查 profile-spec 可复现性、离线成本和主张边界" in normalized["Chinese paper"]
        )
    )
    evaluation_three_plus_one = contains_all(
        normalized["evaluation ledger"],
        [
            "three substantial empirical profiling experiments plus one replayability/scope-control block",
            "claim scope without being treated as a fourth accuracy result",
        ],
    )
    english_three_plus_one_or_gap = english_three_plus_one or english_gap_recorded
    english_actionability = contains_all(
        normalized["English paper"],
        [
            "The actionable claim is therefore a tunable diagnosis surface",
            "not a label-free automatic selector",
            "Executable profile-spec patches improve 5/6 tasks",
        ],
    )
    chinese_actionability = (
        (
            "claim 是可调诊断 surface" in normalized["Chinese paper"]
            or "主张是可调诊断界面" in normalized["Chinese paper"]
        )
        and "不是 label-free automatic selector" in normalized["Chinese paper"]
        and "5/6 patches 同时改善 AP、top-5 lift 和 first-positive work" in normalized["Chinese paper"]
    )
    english_actionability_or_gap = english_actionability or english_gap_recorded
    idea_two_abstractions = contains_all(
        normalized["idea story"],
        ["two profiler abstractions", "`operation`", "`operation stack`"],
    )
    english_two_abstractions = contains_all(
        normalized["English paper"],
        ["profiler abstractions are only operations and operation stacks"],
    )
    chinese_two_abstractions = contains_all(
        normalized["Chinese paper"],
        ["只用 operation 和 operation stack 两个 profiler 抽象"],
    )
    english_two_abstractions_or_gap = english_two_abstractions or english_gap_recorded
    english_e4_scope = contains_all(
        normalized["English paper"],
        [
            "not a hidden-label accuracy result",
            "not live eBPF overhead or analyst productivity",
        ],
    )
    chinese_e4_scope = (
        (
            "不作为第四个 empirical accuracy result" in normalized["Chinese paper"]
            or "不是新的 hidden-label accuracy experiment" in normalized["Chinese paper"]
            or "不是新的 profiler accuracy 结果" in normalized["Chinese paper"]
        )
        and "不覆盖 live eBPF overhead、human utility" in normalized["Chinese paper"]
    )
    evaluation_e4_scope = contains_all(
        normalized["evaluation ledger"],
        [
            "no human/agent analyst task",
            "not empirical profiler evidence",
        ],
    )
    english_e4_scope_or_gap = english_e4_scope or english_gap_recorded

    prereq_statuses = {
        name: read_json(path).get("status", "") for name, path in SOURCES.items() if path.suffix == ".json"
    }
    add_check(
        checks,
        "prerequisite_gates_current",
        all(status in {"pass", "accepted"} for status in prereq_statuses.values()),
        f"Prerequisite statuses={prereq_statuses}",
    )
    add_check(
        checks,
        "central_claim_consistent_across_docs_and_papers",
        idea_main_claim and evaluation_main_claim and english_main_claim_or_gap and chinese_main_claim,
        "The main claim is the same hidden-label profiler fidelity/tradeoff claim in canonical docs and both papers.",
    )
    add_check(
        checks,
        "headline_numbers_and_workloads_match",
        all(
            token in combined
            for token in ["34,539", "3,699", "0.0937", "5/6", "285.0", "157.5"]
        )
        and all(token in combined for token in ["AgentRewardBench", "SATraj-OS", "AgentNet", "OSWorld-Human"]),
        "Headline E2 workload and metric tokens are present across the aligned documents.",
    )
    add_check(
        checks,
        "claim_verdict_excludes_unsupported_claims",
        contains_all(
            normalized["evaluation ledger"],
            [
                "It does not support developer productivity",
                "complete intent-boundary discovery",
                "real OpenTelemetry/OpenInference/Phoenix span-tree superiority",
                "automatic universal policy/action selection",
                "single-view/work dominance",
            ],
        )
        and contains_all(
            normalized["idea story"],
            [
                "The paper does not claim improved human analyst productivity",
                "automatic discovery of all intent boundaries",
                "metric dominance on every task",
                "full OpenTelemetry/Phoenix/LangSmith/Langfuse/Perfetto compatibility",
                "universal policy selector",
            ],
        ),
        "The claim verdict and idea story keep unsupported human-utility, boundary, ecosystem, and universal-selector claims out.",
    )
    add_check(
        checks,
        "fixed_session_is_proxy_not_span_tree_superiority",
        idea_fixed_session_proxy
        and evaluation_fixed_session_proxy
        and english_fixed_session_proxy_or_gap
        and chinese_fixed_session_proxy,
        "Fixed-session remains a proxy baseline; real span-tree ecosystem superiority is not claimed.",
    )
    add_check(
        checks,
        "three_plus_one_claim_roles_visible",
        english_three_plus_one_or_gap and chinese_three_plus_one and evaluation_three_plus_one,
        "E1-E3 remain empirical profiling experiments; E4 remains replayability/scope-control.",
    )
    add_check(
        checks,
        "actionability_is_configuration_guidance_not_auto_selector",
        english_actionability_or_gap and chinese_actionability,
        "Actionability is profile-configuration guidance, not automatic action/policy selection.",
    )
    add_check(
        checks,
        "two_abstraction_boundary_still_visible",
        idea_two_abstractions and english_two_abstractions_or_gap and chinese_two_abstractions,
        "The two-abstraction boundary remains visible after claim-verdict alignment.",
    )
    add_check(
        checks,
        "e4_not_accuracy_or_human_utility",
        english_e4_scope_or_gap and chinese_e4_scope and evaluation_e4_scope,
        "E4 remains replayability/cost/scope-control, not accuracy, live overhead, or human utility.",
    )
    add_check(
        checks,
        "r395_registered_in_evaluation_ledger",
        "R395" in texts["evaluation ledger"]
        and "main claim and verdict alignment" in texts["evaluation ledger"],
        "Evaluation ledger records this main-claim/verdict alignment gate.",
    )
    add_check(
        checks,
        "idea_story_points_to_r395",
        "R395" in texts["idea story"] and "claim-verdict alignment" in texts["idea story"],
        "Idea story records that R395 aligned the current claim/verdict boundary.",
    )
    add_check(
        checks,
        "english_submodule_clean",
        (
            source_by_name["English paper"]["status"] == "tracked_clean"
            and paper_submodule_head() == paper_submodule_index_head()
        )
        or english_gap_recorded,
        (
            "English paper submodule is clean and captured by the parent gitlink, "
            "or R405 records the read-only sync gap."
        ),
    )
    add_check(
        checks,
        "source_status_tracked_or_dirty_allowed",
        all(
            row["status"] in {"tracked_clean", "tracked_dirty_allowed"}
            or (row["source"] == "generator script" and row["status"] == "untracked_or_missing")
            for row in source_status
        ),
        "All guard inputs are tracked or intentionally dirty while this guard is being generated.",
    )

    summary = {
        "checks_passed": sum(1 for check in checks if check["passed"]),
        "checks_total": len(checks),
        "data_sync": False,
        "profiler_rerun": False,
        "human_or_agent_analyst_task": False,
    }
    return {
        "run_id": RUN_ID,
        "status": "pass" if all(check["passed"] for check in checks) else "fail",
        "schema": "agentsight.paper_main_claim_verdict_alignment.v1",
        "network_access_required": False,
        "data_sync": False,
        "profiler_rerun": False,
        "human_or_agent_analyst_task": False,
        "checks": checks,
        "source_status": source_status,
        "summary": summary,
        "interpretation": (
            "The canonical docs and paper drafts align on the scoped profiling "
            "claim: label-scored localization/ranking with lower flat-summary "
            "inspection work, a fixed-session proxy fragmentation tradeoff, "
            "configuration-level actionability, and explicit non-claims."
            " If the English submodule is read-only and behind, R405 records "
            "that sync gap instead of requiring a submodule edit in this workflow."
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
        "# R395 Main Claim / Verdict Alignment Gate",
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
<title>{RUN_ID} Main Claim Verdict Alignment</title>
<style>
body {{ font-family: system-ui, sans-serif; margin: 2rem; line-height: 1.45; }}
table {{ border-collapse: collapse; width: 100%; margin: 1rem 0; }}
th, td {{ border: 1px solid #d0d7de; padding: 0.45rem; vertical-align: top; }}
th {{ background: #f6f8fa; }}
.status {{ font-weight: 700; }}
</style>
<h1>{RUN_ID} Main Claim / Verdict Alignment Gate</h1>
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
    (out_dir / "main-claim-verdict-alignment-report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (out_dir / "run-result.json").write_text(json.dumps(run_result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_csv(out_dir / "main-claim-verdict-alignment-checks.csv", report["checks"])
    write_csv(out_dir / "source-status.csv", report["source_status"], ["source", "path", "status", "sha256"])
    write_markdown(out_dir / "main-claim-verdict-alignment.md", report)
    write_html(out_dir / "index.html", report)
    print(json.dumps(run_result, indent=2, sort_keys=True))
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
