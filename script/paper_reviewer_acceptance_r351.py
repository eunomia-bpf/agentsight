#!/usr/bin/env python3
"""R351: independent reviewer acceptance audit after R350/R338.

This is a paper-readiness artifact. It does not fetch or sync datasets, rerun
the profiler, create labels, or run a human/agent analyst study. It records the
current subagent review closure and mechanically checks that the accepted claim
still rests on the R320-R350 hidden-label profiler evidence, R328 clean
deterministic-output provenance, and guardrails.
"""

from __future__ import annotations

import argparse
import csv
import html
import json
import subprocess
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OUT_ROOT = ROOT / "docs" / "visexp" / "out"
DEFAULT_OUT_DIR = OUT_ROOT / "paper-reviewer-acceptance-r351"

SOURCE_PATHS = {
    "english_paper": ROOT / "docs" / "agentpprof-paper" / "main.tex",
    "chinese_paper": ROOT / "docs" / "visexp" / "paper" / "main.tex",
    "claim_setup": ROOT / "docs" / "visexp" / "paper" / "evaluation-claims-setup.zh-CN.md",
    "evaluation": ROOT / "docs" / "evaluation.md",
    "r320_accuracy": OUT_ROOT / "operation-profile-accuracy-r320" / "profile-accuracy-report.json",
    "r331_negative_control": OUT_ROOT
    / "operation-profile-negative-control-r331"
    / "negative-control-report.json",
    "r328_deterministic_output": OUT_ROOT
    / "operation-profile-deterministic-output-r328"
    / "deterministic-output-report.json",
    "r338_claim_integrity": OUT_ROOT
    / "paper-claim-integrity-r338"
    / "claim-integrity-report.json",
    "r350_evidence_packet": OUT_ROOT
    / "operation-evidence-packet-r350"
    / "evidence-packet-report.json",
}

REVIEW_EVENTS = [
    {
        "reviewer": "Cicero",
        "agent_id": "019f3519-2f5d-7d23-aa45-38bff947ab5a",
        "focus": "OSDI/SOSP systems claim and tradeoff review",
        "final_verdict": "ACCEPT",
        "blocking_issues": [],
        "residual_risks": [
            "Evidence is an offline hidden-label profiler benchmark, not human productivity evidence.",
            "Actionability means objective-level tuning guidance, not automatic action selection.",
            "Fixed-session is a span-tree proxy; real trace ecosystem imports remain future work.",
            "Boundary evidence does not prove automatic intent-boundary discovery.",
        ],
        "rationale": "The current paper scopes the claim as label-scored profiling, defines profiler baselines and metrics, preserves fixed-session and flat counterpoints, and R338/R350 back the bounded packet claim.",
    },
    {
        "reviewer": "James",
        "agent_id": "019f3519-4f14-7811-9e0c-624c8eb03715",
        "focus": "NeurIPS/ML hidden-label evaluation and leakage review",
        "final_verdict": "ACCEPT",
        "blocking_issues": [],
        "residual_risks": [
            "Scope is still six tasks over four oracle-rich families.",
            "No completed human/agent analyst study; paper correctly avoids user-utility claims.",
            "Held-out action transfer is weak as an exact selector and is correctly treated as a guardrail.",
            "Real OpenTelemetry/Phoenix/LangSmith-style import remains future interoperability work.",
        ],
        "rationale": "R320 has named baselines, broad metrics, and a passing leakage check; R331 adds a permutation negative control; R340/R349 keep target labels out of policy selection; R350 narrows actionability to bounded evidence packets.",
    },
    {
        "reviewer": "Galileo",
        "agent_id": "019f3519-6a7c-7770-907d-89126a968e40",
        "focus": "Artifact provenance, reproducibility, and hidden-label discipline",
        "final_verdict": "ACCEPT",
        "blocking_issues": [],
        "residual_risks": [
            "R328 records a dirty worktree at generation time despite tracked-clean source checks.",
            "Some older upstream reports have less uniform provenance schema than R338/R350.",
        ],
        "rationale": "R327/R328 cover deterministic profile specs, R338 source provenance passes, R350 avoids dataset sync/relabeling, hidden labels stay out of visible ranking, and the two-abstraction boundary is preserved.",
    },
    {
        "reviewer": "Herschel",
        "agent_id": "019f3519-8b81-7ea3-bc69-20d08a38b983",
        "focus": "Claim-safety and must-not-claim boundary review",
        "final_verdict": "ACCEPT",
        "blocking_issues": [],
        "residual_risks": [
            "Chinese draft has broad all-profilable-objects language but later caveats scope it.",
            "Accuracy and actionability appear often but are consistently tied to hidden-label profiler scoring.",
        ],
        "rationale": "Human utility, automatic boundary discovery, ecosystem compatibility, universal selector, and third-abstraction claims are guarded in both drafts and R338 reports no blockers.",
    },
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


def load_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as file:
        return json.load(file)


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def git_output(args: list[str]) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip()
        raise SystemExit(f"git {' '.join(args)} failed: {detail}")
    return result.stdout.strip()


def ensure_sources_exist(paths: dict[str, Path]) -> None:
    for key, path in paths.items():
        if not path.exists():
            raise SystemExit(f"missing {key}: {rel(path)}")


def check(condition: bool, name: str, evidence: str, failure: str) -> dict[str, str]:
    return {
        "check": name,
        "status": "pass" if condition else "fail",
        "evidence": evidence if condition else failure,
    }


def build_checks(
    english_paper: str,
    chinese_paper: str,
    r320: dict[str, Any],
    r331: dict[str, Any],
    r328: dict[str, Any],
    r338: dict[str, Any],
    r350: dict[str, Any],
) -> list[dict[str, str]]:
    r338_summary = r338["summary"]
    r350_summary = r350["summary"]
    leakage = r320["leakage_check"]
    r350_input = r350["input_policy"]
    r328_summary = r328["summary"]
    r328_source_status = r328["source_status"]
    return [
        check(
            all(event["final_verdict"] == "ACCEPT" for event in REVIEW_EVENTS),
            "four_independent_reviewers_accept",
            "All four current reviewers returned ACCEPT.",
            "At least one current reviewer did not accept.",
        ),
        check(
            sum(len(event["blocking_issues"]) for event in REVIEW_EVENTS) == 0,
            "no_reviewer_blocking_issues",
            "No reviewer reported a must-fix blocking issue.",
            "One or more reviewers reported blocking issues.",
        ),
        check(
            r338_summary["overall"] == "pass"
            and r338_summary["blocking"] == []
            and r338_summary["warnings"] == []
            and r338_summary["number_checks_passed"] == r338_summary["number_checks_total"]
            and r338_summary["source_policy"] == "pass"
            and r338_summary["guardrails"] == "pass"
            and r338_summary["two_abstraction_boundary"] == "pass",
            "r338_claim_integrity_passes",
            "R338 passes number checks, source policy, guardrails, and two-abstraction boundary with no blockers.",
            "R338 does not fully pass.",
        ),
        check(
            r350_summary["overall"] == "pass"
            and r350_summary["tasks"] == 6
            and r350_summary["datasets"] == 4
            and r350_summary["packets_with_top5_positive"] == 6
            and r350_summary["packets_with_top1_positive"] == 5
            and r350_summary["operation_stack_beats_flat_work_tasks"] == 6
            and r350_summary["operation_stack_beats_fixed_recall_tasks"] == 5
            and r350_summary["operation_stack_fewer_groups_than_fixed_tasks"] == 4,
            "r350_bounded_packet_claim_supported",
            "R350 supports bounded packets over 6 tasks / 4 datasets with positives, flat-work, fixed-recall, and fragmentation tradeoff evidence.",
            "R350 packet support numbers do not match the scoped claim.",
        ),
        check(
            r350_summary["packets_with_30pct_work_budget"] == 4
            and r350_summary["r349_selected_action_exact"] == 7,
            "r350_counterpoints_preserved",
            "R350 preserves strict-budget exceptions and weak exact action transfer as guardrails.",
            "R350 no longer preserves the expected counterpoints.",
        ),
        check(
            leakage["status"] == "pass" and leakage["overlap"] == [],
            "r320_hidden_label_leakage_check_passes",
            "R320 visible rank features do not overlap hidden oracle fields.",
            "R320 hidden-label leakage check does not pass.",
        ),
        check(
            r331["source_check"]["status"] == "pass"
            and r331["source_check"]["tracked_clean_files"] >= 6
            and r331["input_policy"]["dataset_sync"] == "none",
            "r331_negative_control_provenance_passes",
            "R331 negative control reads tracked-clean sources without dataset sync.",
            "R331 negative control provenance is not clean.",
        ),
        check(
            r328["status"] == "pass"
            and r328["source_check"]["status"] == "pass"
            and r328_source_status["git_status_short"] == ""
            and r328_source_status["code_status_short"] == ""
            and r328_summary["semantic_deterministic_specs"] == "76/76"
            and r328_summary["raw_byte_deterministic_specs"] == "76/76",
            "r328_clean_deterministic_output_provenance",
            "R328 clean rerun records empty git/code status and 76/76 semantic/raw-byte deterministic specs.",
            "R328 deterministic-output provenance is dirty or no longer deterministic.",
        ),
        check(
            r350_input["dataset_sync"] == "none"
            and r350_input["dataset_creation"] == "none"
            and r350_input["dataset_relabeling"] == "none"
            and "offline scoring" in r350_input["hidden_label_use"],
            "r350_no_dataset_sync_or_label_leak",
            "R350 records no dataset sync/creation/relabeling and hidden-label use only through offline scoring.",
            "R350 input policy is too broad or label usage is unclear.",
        ),
        check(
            "not a human-productivity claim" in english_paper
            and "automatic action selector" in english_paper
            and "complete compatibility" in english_paper
            and "ecosystem compatibility" in english_paper
            and "human utility" in chinese_paper
            and "automatic action selector" in chinese_paper,
            "paper_must_not_claim_boundaries_visible",
            "English and Chinese drafts visibly guard human utility, automatic selector, and ecosystem-compatibility claims.",
            "One or more must-not-claim boundaries is not visible in paper text.",
        ),
        check(
            r338_summary["profiler_abstractions"] == ["operation", "operation stack"]
            and "operation stack" in english_paper
            and "operation stack" in chinese_paper,
            "two_abstractions_only",
            "R338 and both drafts keep operation and operation stack as the two profiler abstractions.",
            "The two-abstraction boundary is not preserved.",
        ),
    ]


def build_resolved_residuals(r328: dict[str, Any]) -> list[dict[str, str]]:
    r328_summary = r328["summary"]
    r328_source_status = r328["source_status"]
    if (
        r328["status"] == "pass"
        and r328["source_check"]["status"] == "pass"
        and r328_source_status["git_status_short"] == ""
        and r328_source_status["code_status_short"] == ""
        and r328_summary["semantic_deterministic_specs"] == "76/76"
        and r328_summary["raw_byte_deterministic_specs"] == "76/76"
    ):
        return [
            {
                "reviewer": "Galileo",
                "residual_risk": "R328 records a dirty worktree at generation time despite tracked-clean source checks.",
                "resolution": "Current R328 deterministic-output report was rerun from a clean worktree and records empty git/code status with 76/76 semantic and raw-byte deterministic specs.",
            }
        ]
    return []


def write_review_csv(path: Path, events: list[dict[str, Any]]) -> None:
    fields = [
        "reviewer",
        "agent_id",
        "focus",
        "final_verdict",
        "blocking_issue_count",
        "residual_risk_count",
        "rationale",
    ]
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for event in events:
            writer.writerow(
                {
                    "reviewer": event["reviewer"],
                    "agent_id": event["agent_id"],
                    "focus": event["focus"],
                    "final_verdict": event["final_verdict"],
                    "blocking_issue_count": len(event["blocking_issues"]),
                    "residual_risk_count": len(event["residual_risks"]),
                    "rationale": event["rationale"],
                }
            )


def write_markdown(path: Path, payload: dict[str, Any]) -> None:
    lines = [
        "# Paper Reviewer Acceptance R351",
        "",
        "R351 records the independent reviewer closure after the R350 evidence-packet and R338 paper-claim-integrity updates. It is not a new empirical result, not a human/agent analyst study, and not a trace-ecosystem compatibility test.",
        "",
        "## Verdict",
        "",
        f"- Overall: {payload['overall']}.",
        f"- Final reviewer accepts: {payload['summary']['final_accepts']}/{payload['summary']['reviewers']}.",
        f"- Blocking issues: {payload['summary']['blocking_issues']}.",
        f"- Residual risks: {payload['summary']['residual_risks']}.",
        f"- Resolved residual risks: {payload['summary']['resolved_residual_risks']}.",
        "",
        "## Checks",
        "",
        "| Check | Status | Evidence |",
        "|---|---|---|",
    ]
    for row in payload["checks"]:
        lines.append(f"| {row['check']} | {row['status']} | {row['evidence']} |")
    lines.extend(
        [
            "",
            "## Reviewers",
            "",
            "| Reviewer | Focus | Final | Blocking issues | Residual risks |",
            "|---|---|---|---:|---:|",
        ]
    )
    for event in payload["review_events"]:
        lines.append(
            "| {reviewer} | {focus} | {final} | {blocking} | {risks} |".format(
                reviewer=event["reviewer"],
                focus=event["focus"],
                final=event["final_verdict"],
                blocking=len(event["blocking_issues"]),
                risks=len(event["residual_risks"]),
            )
        )
    lines.extend(
        [
            "",
            "## Residual Risks",
            "",
        ]
    )
    for event in payload["review_events"]:
        for risk in event["residual_risks"]:
            lines.append(f"- {event['reviewer']}: {risk}")
    if payload["resolved_residuals"]:
        lines.extend(
            [
                "",
                "## Resolved Residuals",
                "",
            ]
        )
        for row in payload["resolved_residuals"]:
            lines.append(
                f"- {row['reviewer']}: {row['residual_risk']} Resolution: {row['resolution']}"
            )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_html(path: Path, payload: dict[str, Any]) -> None:
    check_rows = []
    for row in payload["checks"]:
        check_rows.append(
            "<tr>"
            f"<td>{html.escape(row['check'])}</td>"
            f"<td>{html.escape(row['status'])}</td>"
            f"<td>{html.escape(row['evidence'])}</td>"
            "</tr>"
        )
    reviewer_rows = []
    for event in payload["review_events"]:
        reviewer_rows.append(
            "<tr>"
            f"<th>{html.escape(event['reviewer'])}</th>"
            f"<td>{html.escape(event['focus'])}</td>"
            f"<td>{html.escape(event['final_verdict'])}</td>"
            f"<td>{len(event['blocking_issues'])}</td>"
            f"<td>{len(event['residual_risks'])}</td>"
            "</tr>"
        )
    resolved_items = []
    for row in payload["resolved_residuals"]:
        resolved_items.append(
            "<li>"
            f"<strong>{html.escape(row['reviewer'])}:</strong> "
            f"{html.escape(row['residual_risk'])} "
            f"Resolution: {html.escape(row['resolution'])}"
            "</li>"
        )
    path.write_text(
        """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Paper Reviewer Acceptance R351</title>
  <style>
    body { font-family: system-ui, sans-serif; margin: 2rem; color: #1f2933; }
    h1 { font-size: 1.6rem; }
    p, li { max-width: 900px; line-height: 1.5; }
    table { border-collapse: collapse; margin-top: 1.5rem; min-width: 920px; }
    th, td { border: 1px solid #d8dee9; padding: 0.5rem 0.65rem; text-align: left; vertical-align: top; }
    th { background: #f6f8fa; }
  </style>
</head>
<body>
  <h1>Paper Reviewer Acceptance R351</h1>
  <p>Independent reviewer closure after R350/R338.</p>
  <h2>Checks</h2>
  <table>
    <tr><th>Check</th><th>Status</th><th>Evidence</th></tr>
"""
        + "\n".join(check_rows)
        + """
  </table>
  <h2>Reviewers</h2>
  <table>
    <tr><th>Reviewer</th><th>Focus</th><th>Final</th><th>Blocking issues</th><th>Residual risks</th></tr>
"""
        + "\n".join(reviewer_rows)
        + """
  </table>
  <h2>Resolved residuals</h2>
  <ul>
"""
        + "\n".join(resolved_items)
        + """
  </ul>
</body>
</html>
""",
        encoding="utf-8",
    )


def main() -> None:
    args = parse_args()
    out_dir = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    ensure_sources_exist(SOURCE_PATHS)

    english_paper = SOURCE_PATHS["english_paper"].read_text(encoding="utf-8")
    chinese_paper = SOURCE_PATHS["chinese_paper"].read_text(encoding="utf-8")
    r320 = load_json(SOURCE_PATHS["r320_accuracy"])
    r331 = load_json(SOURCE_PATHS["r331_negative_control"])
    r328 = load_json(SOURCE_PATHS["r328_deterministic_output"])
    r338 = load_json(SOURCE_PATHS["r338_claim_integrity"])
    r350 = load_json(SOURCE_PATHS["r350_evidence_packet"])
    checks = build_checks(english_paper, chinese_paper, r320, r331, r328, r338, r350)
    resolved_residuals = build_resolved_residuals(r328)
    final_accepts = sum(1 for event in REVIEW_EVENTS if event["final_verdict"] == "ACCEPT")
    blocking_issues = sum(len(event["blocking_issues"]) for event in REVIEW_EVENTS)
    residual_risks = sum(len(event["residual_risks"]) for event in REVIEW_EVENTS)
    overall = "accepted" if all(row["status"] == "pass" for row in checks) else "needs_changes"

    report_json = out_dir / "reviewer-acceptance.json"
    report_md = out_dir / "reviewer-acceptance.md"
    review_csv = out_dir / "reviewer-verdicts.csv"
    index_html = out_dir / "index.html"
    run_result = out_dir / "run-result.json"
    report = {
        "run_id": "R351",
        "schema": "agentsight.paper-reviewer-acceptance.v2",
        "status": "ok" if overall == "accepted" else "needs_changes",
        "overall": overall,
        "commit": git_output(["rev-parse", "HEAD"]),
        "input_policy": "current paper plus tracked R320/R328/R331/R338/R350 artifacts; no dataset sync, no profiler rerun inside R351, no human/agent analyst task",
        "not_new_empirical_result": True,
        "not_a_human_study_result": True,
        "not_an_agent_analyst_task_result": True,
        "network_access_required": False,
        "profiler_abstractions": ["operation", "operation stack"],
        "source": {key: rel(path) for key, path in SOURCE_PATHS.items()},
        "summary": {
            "reviewers": len(REVIEW_EVENTS),
            "final_accepts": final_accepts,
            "blocking_issues": blocking_issues,
            "residual_risks": residual_risks,
            "resolved_residual_risks": len(resolved_residuals),
            "checks_passed": sum(1 for row in checks if row["status"] == "pass"),
            "checks_total": len(checks),
            "r328_semantic_deterministic_specs": r328["summary"]["semantic_deterministic_specs"],
            "r328_raw_byte_deterministic_specs": r328["summary"]["raw_byte_deterministic_specs"],
            "r328_git_status_short": r328["source_status"]["git_status_short"],
            "r328_code_status_short": r328["source_status"]["code_status_short"],
            "r350_tasks": r350["summary"]["tasks"],
            "r350_datasets": r350["summary"]["datasets"],
            "r350_top5_positive_packets": r350["summary"]["packets_with_top5_positive"],
            "r350_strict_30pct_packets": r350["summary"]["packets_with_30pct_work_budget"],
            "r338_number_checks": r338["summary"]["number_checks_total"],
            "r338_source_policy_checks": r338["summary"]["source_policy_checks_total"],
            "r338_guardrail_checks": r338["summary"]["guardrail_checks_total"],
        },
        "checks": checks,
        "resolved_residuals": resolved_residuals,
        "review_events": REVIEW_EVENTS,
        "claim_scope": {
            "supports": [
                "independent reviewer acceptance of the scoped R350/R338 paper state",
                "hidden-label profiler localization/ranking/actionability claim over real labeled traces",
                "bounded operation-stack evidence packets with explicit baseline counterpoints",
            ],
            "does_not_support": [
                "human or agent analyst accuracy/productivity",
                "automatic discovery of all intent boundaries",
                "complete OpenTelemetry/Phoenix/LangSmith/Langfuse/Perfetto compatibility",
                "label-free universal action selector",
                "universal dominance over flat, fixed-session, dataset-native, or raw-action views",
            ],
        },
        "outputs": {
            "json": rel(report_json),
            "markdown": rel(report_md),
            "csv": rel(review_csv),
            "html": rel(index_html),
            "run_result": rel(run_result),
        },
    }
    write_json(report_json, report)
    write_markdown(report_md, report)
    write_review_csv(review_csv, REVIEW_EVENTS)
    write_html(index_html, report)
    write_json(
        run_result,
        {
            "status": report["status"],
            "run_id": "R351",
            "overall": overall,
            "report": rel(report_json),
            "html": rel(index_html),
            "reviewers": report["summary"]["reviewers"],
            "final_accepts": final_accepts,
            "blocking_issues": blocking_issues,
            "resolved_residual_risks": len(resolved_residuals),
            "checks_passed": report["summary"]["checks_passed"],
            "checks_total": report["summary"]["checks_total"],
            "not_new_empirical_result": True,
            "not_a_human_study_result": True,
            "not_an_agent_analyst_task_result": True,
            "network_access_required": False,
        },
    )
    print(json.dumps(load_json(run_result), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
