#!/usr/bin/env python3
"""R318: record independent reviewer acceptance after R317 paper polish.

This script is a paper-gate artifact. It does not fetch datasets, rerun the
profiler, or execute a human/agent analyst task. It records the independent
subagent-review closure for the current paper draft and verifies that the
current artifacts still preserve the scoped two-abstraction claim boundary.
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
DEFAULT_OUT_DIR = OUT_ROOT / "paper-reviewer-acceptance-r318"

SOURCE_PATHS = {
    "paper_main_tex": ROOT / "docs" / "visexp" / "paper" / "main.tex",
    "claim_setup": ROOT / "docs" / "visexp" / "paper" / "evaluation-claims-setup.zh-CN.md",
    "evaluation": ROOT / "docs" / "evaluation.md",
    "submission_audit": OUT_ROOT / "paper-submission-audit-r312" / "submission-audit.json",
    "related_work_audit": OUT_ROOT / "paper-related-work-audit-r314" / "related-work-audit.json",
    "real_problem_narrative": OUT_ROOT
    / "paper-real-problem-narrative-r317"
    / "paper-narrative-report.json",
}

REVIEW_EVENTS = [
    {
        "reviewer": "Volta",
        "agent_id": "019f2ea0-a261-7102-836e-ddbd51bd59b7",
        "focus": "overall R317 paper update",
        "initial_verdict": "ACCEPT",
        "final_verdict": "ACCEPT",
        "blocking_issues": [],
        "residual_risks": [
            "JSON uses operation_stack while paper prose uses operation stack",
            "submission polish should continue moving run IDs out of prose",
            "R312/R314 provenance commit metadata can drift when regenerated before commit",
        ],
    },
    {
        "reviewer": "Newton",
        "agent_id": "019f2ea0-f154-7893-866f-cd94f956a3b5",
        "focus": "claim/evidence validity",
        "initial_verdict": "ACCEPT",
        "final_verdict": "ACCEPT",
        "blocking_issues": [],
        "residual_risks": [],
    },
    {
        "reviewer": "Mendel",
        "agent_id": "019f2ea0-f501-7341-94ed-c4bc3fad01dc",
        "focus": "artifact provenance and reproducibility",
        "initial_verdict": "ACCEPT",
        "final_verdict": "ACCEPT",
        "blocking_issues": [],
        "residual_risks": [],
    },
    {
        "reviewer": "Linnaeus",
        "agent_id": "019f2ea0-f322-7343-806e-f242fcf74887",
        "focus": "paper prose and structure",
        "initial_verdict": "NEEDS_CHANGES",
        "final_verdict": "ACCEPT",
        "blocking_issues": [
            "RQ2 mechanism narrative read like a claim-synthesis artifact ledger",
            "main result table was dominated by R277-R317 run IDs",
            "Paper-Ready Wording section listed R307-R317 artifacts sequentially",
        ],
        "resolved_by": [
            "main.tex reframes the former artifact material as mechanism verification",
            "main.tex replaces the run-ID inventory table with a claim-centered result table",
            "evaluation-claims-setup.zh-CN.md now gives paper-facing prose guidance",
        ],
        "residual_risks": [
            "internal Chinese draft still uses run IDs in some ordinary prose; final submission should move most to appendix or artifact ledger",
        ],
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


def normalize_abstractions(values: list[Any] | None) -> list[str]:
    return [str(value).replace(" ", "_") for value in values or []]


def check(condition: bool, name: str, evidence: str, failure: str) -> dict[str, Any]:
    return {
        "check": name,
        "status": "pass" if condition else "fail",
        "evidence": evidence if condition else failure,
    }


def build_checks(
    paper_text: str,
    claim_setup_text: str,
    submission_audit: dict[str, Any],
    related_work_audit: dict[str, Any],
    narrative: dict[str, Any],
) -> list[dict[str, Any]]:
    r312_checks = submission_audit["readiness_summary"]["checks"]
    r314_summary = related_work_audit["summary"]
    return [
        check(
            "Claim-centered result summary" in paper_text
            and "Paper question & Workload / oracle" in paper_text,
            "paper_table_claim_centered",
            "main.tex contains the claim-centered result table header and caption.",
            "main.tex does not contain the claim-centered result table.",
        ),
        check(
            "Claim synthesis 和 reviewer evidence packet" not in paper_text,
            "rq2_artifact_log_phrase_removed",
            "The former artifact-log phrase is absent from main.tex.",
            "main.tex still contains the former artifact-log phrase.",
        ),
        check(
            "真实问题结果应按任务讲" in claim_setup_text
            and "R307 把 R300-R306" not in claim_setup_text,
            "paper_ready_wording_is_prose_guidance",
            "claim setup now directs authors to write by task/problem rather than artifact number.",
            "claim setup still appears to list R307-R317 artifact notes.",
        ),
        check(
            submission_audit["readiness_summary"]["overall"] == "scoped_claim_ready"
            and all(value == "pass" for value in r312_checks.values()),
            "submission_audit_passes",
            "R312 overall is scoped_claim_ready with all checks passing.",
            "R312 submission audit is not fully passing.",
        ),
        check(
            r314_summary["overall"] == "scoped_related_work_ready"
            and all(value == "pass" for value in r314_summary["sections"].values()),
            "related_work_audit_passes",
            "R314 overall is scoped_related_work_ready with all sections passing.",
            "R314 related-work audit is not fully passing.",
        ),
        check(
            narrative["status"] == "ok"
            and normalize_abstractions(narrative.get("profiler_abstractions")) == [
                "operation",
                "operation_stack",
            ],
            "r317_two_abstraction_boundary",
            "R317 emits only operation and operation_stack.",
            "R317 profiler abstraction list is not exactly operation plus operation_stack.",
        ),
        check(
            narrative["not_new_empirical_result"]
            and narrative["not_a_human_study_result"]
            and narrative["not_an_agent_study_result"],
            "r317_not_empirical_or_analyst_study",
            "R317 is explicitly marked as synthesis, not empirical or analyst-study evidence.",
            "R317 is not clearly marked as synthesis-only.",
        ),
        check(
            all(event["final_verdict"] == "ACCEPT" for event in REVIEW_EVENTS),
            "all_reviewers_final_accept",
            "All four independent reviewers ended with ACCEPT.",
            "At least one independent reviewer has not accepted.",
        ),
        check(
            any(event["initial_verdict"] == "NEEDS_CHANGES" for event in REVIEW_EVENTS)
            and all(
                event["final_verdict"] == "ACCEPT"
                for event in REVIEW_EVENTS
                if event["initial_verdict"] == "NEEDS_CHANGES"
            ),
            "needs_changes_round_closed",
            "The reviewer who requested changes re-reviewed and accepted the fixes.",
            "A NEEDS_CHANGES review was not closed by a final ACCEPT.",
        ),
    ]


def write_review_csv(path: Path, events: list[dict[str, Any]]) -> None:
    fields = [
        "reviewer",
        "agent_id",
        "focus",
        "initial_verdict",
        "final_verdict",
        "blocking_issue_count",
        "residual_risk_count",
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
                    "initial_verdict": event["initial_verdict"],
                    "final_verdict": event["final_verdict"],
                    "blocking_issue_count": len(event["blocking_issues"]),
                    "residual_risk_count": len(event["residual_risks"]),
                }
            )


def write_markdown(path: Path, payload: dict[str, Any]) -> None:
    lines = [
        "# Paper Reviewer Acceptance R318",
        "",
        "R318 records independent subagent-review closure for the R317 paper update. It is not a new empirical run, not a detector, and not a human/agent analyst-task result.",
        "",
        "## Verdict",
        "",
        f"- Overall: {payload['overall']}.",
        f"- Final reviewer accepts: {payload['summary']['final_accepts']}/{payload['summary']['reviewers']}.",
        f"- Closed NEEDS_CHANGES rounds: {payload['summary']['closed_needs_changes_rounds']}.",
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
            "| Reviewer | Focus | Initial | Final | Blocking issues | Residual risks |",
            "|---|---|---|---|---:|---:|",
        ]
    )
    for event in payload["review_events"]:
        lines.append(
            "| {reviewer} | {focus} | {initial} | {final} | {blocking} | {risks} |".format(
                reviewer=event["reviewer"],
                focus=event["focus"],
                initial=event["initial_verdict"],
                final=event["final_verdict"],
                blocking=len(event["blocking_issues"]),
                risks=len(event["residual_risks"]),
            )
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
            f"<td>{html.escape(event['initial_verdict'])}</td>"
            f"<td>{html.escape(event['final_verdict'])}</td>"
            f"<td>{len(event['blocking_issues'])}</td>"
            f"<td>{len(event['residual_risks'])}</td>"
            "</tr>"
        )
    path.write_text(
        """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Paper Reviewer Acceptance R318</title>
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
  <h1>Paper Reviewer Acceptance R318</h1>
  <p>Independent subagent-review closure for the R317 paper update.</p>
  <h2>Checks</h2>
  <table>
    <tr><th>Check</th><th>Status</th><th>Evidence</th></tr>
"""
        + "\n".join(check_rows)
        + """
  </table>
  <h2>Reviewers</h2>
  <table>
    <tr><th>Reviewer</th><th>Focus</th><th>Initial</th><th>Final</th><th>Blocking issues</th><th>Residual risks</th></tr>
"""
        + "\n".join(reviewer_rows)
        + """
  </table>
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

    paper_text = SOURCE_PATHS["paper_main_tex"].read_text(encoding="utf-8")
    claim_setup_text = SOURCE_PATHS["claim_setup"].read_text(encoding="utf-8")
    submission_audit = load_json(SOURCE_PATHS["submission_audit"])
    related_work_audit = load_json(SOURCE_PATHS["related_work_audit"])
    narrative = load_json(SOURCE_PATHS["real_problem_narrative"])
    checks = build_checks(
        paper_text,
        claim_setup_text,
        submission_audit,
        related_work_audit,
        narrative,
    )
    overall = "accepted" if all(row["status"] == "pass" for row in checks) else "needs_changes"
    report_json = out_dir / "reviewer-acceptance.json"
    report_md = out_dir / "reviewer-acceptance.md"
    review_csv = out_dir / "reviewer-verdicts.csv"
    index_html = out_dir / "index.html"
    run_result = out_dir / "run-result.json"
    needs_changes_rounds = [
        event for event in REVIEW_EVENTS if event["initial_verdict"] == "NEEDS_CHANGES"
    ]
    report = {
        "run_id": "R318",
        "schema": "agentsight.paper-reviewer-acceptance.v1",
        "status": "ok" if overall == "accepted" else "needs_changes",
        "overall": overall,
        "commit": git_output(["rev-parse", "HEAD"]),
        "input_policy": "current-worktree paper and generated R312/R314/R317 artifacts; no dataset sync, no profiler rerun, no human/agent analyst task",
        "not_new_empirical_result": True,
        "not_a_human_study_result": True,
        "not_an_agent_analyst_task_result": True,
        "profiler_abstractions": ["operation", "operation_stack"],
        "source": {key: rel(path) for key, path in SOURCE_PATHS.items()},
        "summary": {
            "reviewers": len(REVIEW_EVENTS),
            "final_accepts": sum(1 for event in REVIEW_EVENTS if event["final_verdict"] == "ACCEPT"),
            "initial_needs_changes_rounds": len(needs_changes_rounds),
            "closed_needs_changes_rounds": sum(
                1 for event in needs_changes_rounds if event["final_verdict"] == "ACCEPT"
            ),
            "blocking_issues_resolved": sum(len(event["blocking_issues"]) for event in needs_changes_rounds),
        },
        "checks": checks,
        "review_events": REVIEW_EVENTS,
        "claim_scope": {
            "supports": [
                "independent reviewer acceptance of scoped R317 paper wording",
                "paper-structure closure for the artifact-log blocker",
                "continued two-abstraction and must-not-claim guardrail alignment",
            ],
            "does_not_support": [
                "human analyst accuracy",
                "agent analyst task accuracy",
                "time-to-answer improvement",
                "developer productivity improvement",
                "automatic detection",
                "single-view dominance",
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
            "run_id": "R318",
            "overall": overall,
            "report": rel(report_json),
            "html": rel(index_html),
            "reviewers": report["summary"]["reviewers"],
            "final_accepts": report["summary"]["final_accepts"],
            "closed_needs_changes_rounds": report["summary"]["closed_needs_changes_rounds"],
            "not_new_empirical_result": True,
            "not_a_human_study_result": True,
            "not_an_agent_analyst_task_result": True,
        },
    )
    print(json.dumps(load_json(run_result), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
