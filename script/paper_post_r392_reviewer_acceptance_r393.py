#!/usr/bin/env python3
"""R393: reviewer acceptance after the R392 E4 input-source replay update.

This paper-integration guardrail records the post-R392 read-only reviewer
verdicts and checks that R392 remains scoped to E4 replay/artifact hygiene. It
does not fetch data, relabel traces, rerun profiler experiments, or run a
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
DEFAULT_OUT_DIR = OUT_ROOT / "paper-post-r392-reviewer-acceptance-r393"
RUN_ID = "R393"
SCRIPT_PATH = Path(__file__).resolve()
PAPER_SUBMODULE = ROOT / "docs" / "agentpprof-paper"
PAPER_SUBMODULE_PATH = "docs/agentpprof-paper"

SOURCES = {
    "R383 canonical reviewer acceptance": OUT_ROOT
    / "paper-canonical-reviewer-acceptance-r383"
    / "reviewer-acceptance-r383.json",
    "idea story": ROOT / "docs" / "idea-story.md",
    "evaluation ledger": ROOT / "docs" / "evaluation.md",
    "English paper": PAPER_SUBMODULE / "main.tex",
    "Chinese paper": ROOT / "docs" / "visexp" / "paper" / "main.tex",
}

REVIEW_EVENTS = [
    {
        "reviewer": "Jason",
        "agent_id": "019f38bc-924e-79e0-9bdf-905d830edabd",
        "focus": "post-R392 claim-scope and E4 scoping",
        "initial_verdict": "ACCEPT",
        "final_verdict": "ACCEPT",
        "resolved_blockers": [],
        "blocking_issues": [],
        "rationale": "R392 is correctly scoped as E4 input-source replay hygiene, and the main claim remains profiler fidelity rather than human utility.",
    },
    {
        "reviewer": "Franklin",
        "agent_id": "019f38bc-61be-7400-930f-56b829e26f84",
        "focus": "three-plus-one paper and canonical-doc consistency",
        "initial_verdict": "ACCEPT",
        "final_verdict": "ACCEPT",
        "resolved_blockers": [],
        "blocking_issues": [],
        "rationale": "The current papers and docs keep E1-E3 empirical and E4 artifact/reproducibility, with R-runs as provenance.",
    },
    {
        "reviewer": "McClintock",
        "agent_id": "019f38bc-7958-7dc0-88d1-23a23c07d2a8",
        "focus": "abstraction boundary and anti-ledger organization",
        "initial_verdict": "ACCEPT",
        "final_verdict": "ACCEPT",
        "resolved_blockers": [],
        "blocking_issues": [],
        "rationale": "Mapping, tagging, profile specs, and trace import remain mechanisms over operation fields and operation-stack folding, not extra profiler abstractions.",
    },
    {
        "reviewer": "Kant",
        "agent_id": "019f38bc-ad73-7b50-8ca3-8872653d3959",
        "focus": "dataset-scope wording and top-conference profiling readiness",
        "initial_verdict": "BLOCK",
        "final_verdict": "ACCEPT",
        "resolved_blockers": [
            "docs/visexp/paper/main.tex caption now distinguishes E1's 15 public labeled sources from RQ2's four oracle-rich hidden-label families.",
        ],
        "blocking_issues": [],
        "rationale": "The prior caption blocker was fixed; the current text no longer says the first 14 sources are oracle-rich and introduces no new blocker.",
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


def one_line(text: str) -> str:
    return " ".join(text.split())


def add_check(checks: list[dict[str, Any]], name: str, passed: bool, detail: str) -> None:
    checks.append({"check": name, "passed": bool(passed), "detail": detail})


def build_report() -> dict[str, Any]:
    r383 = read_json(SOURCES["R383 canonical reviewer acceptance"])
    idea = read_text(SOURCES["idea story"])
    evaluation = read_text(SOURCES["evaluation ledger"])
    english = one_line(read_text(SOURCES["English paper"]))
    chinese = one_line(read_text(SOURCES["Chinese paper"]))
    evaluation_l = evaluation.lower()
    english_l = english.lower()
    combined = "\n".join([idea, evaluation, english, chinese]).lower()
    source_status = source_rows()

    final_accepts = sum(event["final_verdict"] == "ACCEPT" for event in REVIEW_EVENTS)
    unresolved_blockers = sum(len(event["blocking_issues"]) for event in REVIEW_EVENTS)
    resolved_blockers = sum(len(event["resolved_blockers"]) for event in REVIEW_EVENTS)
    checks: list[dict[str, Any]] = []

    add_check(checks, "four_final_accepts", final_accepts == 4, f"Final ACCEPT verdicts={final_accepts}/4.")
    add_check(checks, "zero_unresolved_blockers", unresolved_blockers == 0, f"Unresolved blocking issues={unresolved_blockers}.")
    add_check(checks, "caption_blocker_resolved", resolved_blockers == 1 and "前 14" not in chinese and "14 个 oracle" not in chinese, "Chinese dataset caption no longer misstates the oracle-rich source count.")
    add_check(checks, "r383_prior_gate_accepted", r383["status"] == "accepted" and r383["summary"]["final_accepts"] == 4, "R383 prior canonical reviewer gate remains accepted.")
    add_check(
        checks,
        "r392_registered_as_e4",
        "r392" in evaluation_l and "profile-spec input-source replay" in evaluation_l and "rq4 / e4" in evaluation_l,
        "Evaluation ledger registers R392 as profile-spec input-source replay under E4.",
    )
    add_check(
        checks,
        "r392_not_accuracy_experiment",
        "do not add a new accuracy experiment" in english_l and "不是新的 hidden-label accuracy experiment" in chinese,
        "Both papers state that R392 is not a new accuracy experiment.",
    )
    add_check(checks, "two_abstractions_preserved", "two profiler abstractions" in idea and "third profiler object" in english and "第三个 profiler object" in chinese, "Current docs/papers preserve operation and operation stack as the only profiler abstractions.")
    add_check(checks, "three_plus_one_preserved", "three empirical profiling experiments plus one artifact/reproducibility block" in english and "三个核心经验性 profiling 实验" in chinese, "English and Chinese papers preserve the 3+1 organization.")
    add_check(checks, "must_not_claims_visible", all(token in combined for token in ["human", "automatic", "ecosystem", "metric dominance"]), "Must-not-claim guardrails remain visible.")
    add_check(checks, "r393_ledger_registered", "r393" in evaluation_l and "post-r392 reviewer acceptance" in evaluation_l, "Evaluation ledger records this post-R392 reviewer-acceptance closure.")
    add_check(checks, "idea_story_gate_closed", "r393" in idea.lower() and "independent reviewer pass" in idea.lower() and "done" in idea.lower(), "Idea story records the independent reviewer pass as done after R393.")
    add_check(checks, "source_status_tracked", all(row["status"] in {"tracked_clean", "tracked_dirty_allowed"} for row in source_status), "All R393 inputs are tracked or intentionally staged/dirty.")

    summary = {
        "reviewers": len(REVIEW_EVENTS),
        "final_accepts": final_accepts,
        "resolved_blockers": resolved_blockers,
        "unresolved_blockers": unresolved_blockers,
        "checks_passed": sum(1 for check in checks if check["passed"]),
        "checks_total": len(checks),
    }
    return {
        "run_id": RUN_ID,
        "status": "accepted" if all(check["passed"] for check in checks) else "needs_changes",
        "schema": "agentsight.paper_post_r392_reviewer_acceptance.v1",
        "not_new_empirical_result": True,
        "not_human_or_agent_analyst_study": True,
        "network_access_required": False,
        "data_sync": False,
        "profiler_rerun": False,
        "checks": checks,
        "source_status": source_status,
        "review_events": REVIEW_EVENTS,
        "summary": summary,
        "claim_scope": {
            "supports": [
                "independent reviewer acceptance of the post-R392 paper state",
                "R392 remains E4 input-source replay hygiene",
            ],
            "does_not_support": [
                "new empirical profiler accuracy evidence",
                "human or agent analyst productivity",
                "automatic discovery of all intent boundaries",
                "complete trace-ecosystem compatibility",
                "metric dominance over every baseline and task",
            ],
        },
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
        "# R393 Post-R392 Reviewer Acceptance",
        "",
        f"Status: `{report['status']}`",
        f"Reviewer accepts: {report['summary']['final_accepts']}/{report['summary']['reviewers']}",
        f"Checks: {report['summary']['checks_passed']}/{report['summary']['checks_total']}",
        "",
        "R393 records independent reviewer acceptance after the R392 E4 input-source replay update. It is a paper-integration guardrail, not a new empirical result.",
        "",
        "## Checks",
        "",
        "| Check | Passed | Detail |",
        "|---|---:|---|",
    ]
    for check in report["checks"]:
        lines.append(f"| {check['check']} | {check['passed']} | {check['detail']} |")
    lines.extend(["", "## Reviewers", "", "| Reviewer | Focus | Initial | Final | Resolved | Blocking |", "|---|---|---|---|---:|---:|"])
    for event in report["review_events"]:
        lines.append(
            f"| {event['reviewer']} | {event['focus']} | {event['initial_verdict']} | {event['final_verdict']} | {len(event['resolved_blockers'])} | {len(event['blocking_issues'])} |"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_html(path: Path, report: dict[str, Any]) -> None:
    check_rows = "\n".join(
        f"<tr><td>{html.escape(check['check'])}</td><td>{check['passed']}</td><td>{html.escape(check['detail'])}</td></tr>"
        for check in report["checks"]
    )
    reviewer_rows = "\n".join(
        "<tr>"
        f"<th>{html.escape(event['reviewer'])}</th>"
        f"<td>{html.escape(event['focus'])}</td>"
        f"<td>{html.escape(event['initial_verdict'])}</td>"
        f"<td>{html.escape(event['final_verdict'])}</td>"
        f"<td>{len(event['resolved_blockers'])}</td>"
        f"<td>{len(event['blocking_issues'])}</td>"
        "</tr>"
        for event in report["review_events"]
    )
    path.write_text(
        f"""<!doctype html>
<meta charset="utf-8">
<title>{RUN_ID} Post-R392 Reviewer Acceptance</title>
<style>
body {{ font-family: system-ui, sans-serif; margin: 2rem; line-height: 1.45; }}
table {{ border-collapse: collapse; width: 100%; margin: 1rem 0; }}
th, td {{ border: 1px solid #d0d7de; padding: 0.45rem; vertical-align: top; }}
th {{ background: #f6f8fa; }}
.status {{ font-weight: 700; }}
</style>
<h1>{RUN_ID} Post-R392 Reviewer Acceptance</h1>
<p class="status">Status: {html.escape(report['status'])}; reviewers {report['summary']['final_accepts']}/{report['summary']['reviewers']}; checks {report['summary']['checks_passed']}/{report['summary']['checks_total']}.</p>
<p>This is a paper-integration guardrail, not a new empirical result.</p>
<h2>Checks</h2>
<table><tr><th>Check</th><th>Passed</th><th>Detail</th></tr>{check_rows}</table>
<h2>Reviewers</h2>
<table><tr><th>Reviewer</th><th>Focus</th><th>Initial</th><th>Final</th><th>Resolved</th><th>Blocking</th></tr>{reviewer_rows}</table>
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
        "reviewers": {
            "final_accepts": report["summary"]["final_accepts"],
            "total": report["summary"]["reviewers"],
        },
        "out_dir": rel(out_dir),
        "elapsed_s": round(time.time() - start, 3),
    }
    (out_dir / "reviewer-acceptance-r393.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (out_dir / "run-result.json").write_text(json.dumps(run_result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_csv(out_dir / "acceptance-checks.csv", report["checks"])
    write_csv(
        out_dir / "reviewer-verdicts.csv",
        [
            {
                "reviewer": event["reviewer"],
                "agent_id": event["agent_id"],
                "focus": event["focus"],
                "initial_verdict": event["initial_verdict"],
                "final_verdict": event["final_verdict"],
                "resolved_blocker_count": len(event["resolved_blockers"]),
                "blocking_issue_count": len(event["blocking_issues"]),
                "rationale": event["rationale"],
            }
            for event in report["review_events"]
        ],
        [
            "reviewer",
            "agent_id",
            "focus",
            "initial_verdict",
            "final_verdict",
            "resolved_blocker_count",
            "blocking_issue_count",
            "rationale",
        ],
    )
    write_csv(out_dir / "source-status.csv", report["source_status"], ["source", "path", "status", "sha256"])
    write_markdown(out_dir / "reviewer-acceptance-r393.md", report)
    write_html(out_dir / "index.html", report)
    print(json.dumps(run_result, indent=2, sort_keys=True))
    return 0 if report["status"] == "accepted" else 1


if __name__ == "__main__":
    raise SystemExit(main())
