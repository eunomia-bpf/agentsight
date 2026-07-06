#!/usr/bin/env python3
"""R383: reviewer acceptance after the canonical three-plus-one cleanup.

This submission-readiness guardrail records the four independent read-only
reviewer ACCEPT verdicts after R382 and checks that the accepted state still
rests on tracked R380/R381/R382 paper-organization artifacts. It does not fetch
data, relabel traces, rerun profiler experiments, or run a human/agent analyst
task.
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
DEFAULT_OUT_DIR = OUT_ROOT / "paper-canonical-reviewer-acceptance-r383"
RUN_ID = "R383"
SCRIPT_PATH = Path(__file__).resolve()
PAPER_SUBMODULE = ROOT / "docs" / "agentpprof-paper"
PAPER_SUBMODULE_PATH = "docs/agentpprof-paper"

SOURCES = {
    "R380 experiment-block gate": OUT_ROOT / "paper-experiment-block-consolidation-r380" / "experiment-block-consolidation-report.json",
    "R381 diagnosis-card gate": OUT_ROOT / "paper-diagnosis-card-r381" / "diagnosis-card-report.json",
    "R382 canonical three-plus-one gate": OUT_ROOT
    / "paper-canonical-three-plus-one-r382"
    / "canonical-three-plus-one-report.json",
    "idea story": ROOT / "docs" / "idea-story.md",
    "design": ROOT / "docs" / "design.md",
    "evaluation ledger": ROOT / "docs" / "evaluation.md",
    "English paper": PAPER_SUBMODULE / "main.tex",
    "Chinese paper": ROOT / "docs" / "visexp" / "paper" / "main.tex",
}

REVIEW_EVENTS = [
    {
        "reviewer": "Singer",
        "agent_id": "019f3851-1c4a-7862-9dbf-d8a5389007b5",
        "focus": "canonical-doc experiment organization",
        "final_verdict": "ACCEPT",
        "blocking_issues": [],
        "non_blocking_notes": [],
        "rationale": (
            "Canonical docs, design text, and evaluation ledger align on three "
            "empirical profiling experiments plus one artifact/reproducibility block; "
            "R382 is registered as a consistency gate rather than a new experiment."
        ),
    },
    {
        "reviewer": "Dirac",
        "agent_id": "019f3851-349a-7f63-a05d-f6f4a2aed1d4",
        "focus": "claim-safety and non-claim boundary review",
        "final_verdict": "ACCEPT",
        "blocking_issues": [],
        "non_blocking_notes": [],
        "rationale": (
            "The cleanup keeps human/agent analyst productivity, automatic boundary "
            "discovery, metric dominance, complete ecosystem compatibility, and E4 "
            "accuracy evidence out of scope."
        ),
    },
    {
        "reviewer": "Erdos",
        "agent_id": "019f3851-794b-7222-9a81-5d84bcab27b0",
        "focus": "artifact provenance and reproducibility hygiene",
        "final_verdict": "ACCEPT",
        "blocking_issues": [],
        "non_blocking_notes": [
            "A prior local rerun changed only the elapsed_s field in the R382 run-result; the staged output was refreshed afterward.",
        ],
        "rationale": (
            "R382 is local-doc only, records no data sync and no profiler rerun, keeps "
            "small documentation artifacts, and has a clean English-paper submodule."
        ),
    },
    {
        "reviewer": "Cicero",
        "agent_id": "019f3851-9330-7352-afb2-d4aff59c0466",
        "focus": "paper and ledger consistency review",
        "final_verdict": "ACCEPT",
        "blocking_issues": [],
        "non_blocking_notes": [],
        "rationale": (
            "R382 wording matches the English and Chinese papers, R380/R381 remain "
            "passing, and the ledger scopes R382 as documentation consistency rather "
            "than a new empirical result."
        ),
    },
]

MUST_NOT_TOKENS = [
    "human-productivity",
    "automatic boundary discovery",
    "automatic patch selection",
    "metric dominance",
    "ecosystem compatibility",
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


def one_line(text: str) -> str:
    return " ".join(text.split())


def build_report() -> dict[str, Any]:
    r380 = read_json(SOURCES["R380 experiment-block gate"])
    r381 = read_json(SOURCES["R381 diagnosis-card gate"])
    r382 = read_json(SOURCES["R382 canonical three-plus-one gate"])
    texts = {name: read_text(path) for name, path in SOURCES.items() if path.suffix in {".md", ".tex"}}
    combined = "\n".join(texts.values()).lower()
    idea = texts["idea story"]
    design = texts["design"]
    evaluation = texts["evaluation ledger"]
    english = one_line(texts["English paper"])
    chinese = one_line(texts["Chinese paper"])
    source_status = source_rows()
    source_by_name = {row["source"]: row for row in source_status}
    r382_checks = {check["check"]: check for check in r382["checks"]}
    checks: list[dict[str, Any]] = []

    final_accepts = sum(event["final_verdict"] == "ACCEPT" for event in REVIEW_EVENTS)
    blocking_issues = sum(len(event["blocking_issues"]) for event in REVIEW_EVENTS)
    non_blocking_notes = sum(len(event["non_blocking_notes"]) for event in REVIEW_EVENTS)
    add_check(
        checks,
        "four_reviewers_accept",
        final_accepts == 4,
        f"Final ACCEPT verdicts={final_accepts}/4.",
    )
    add_check(
        checks,
        "zero_blocking_issues",
        blocking_issues == 0,
        f"Blocking issue count={blocking_issues}.",
    )
    add_check(
        checks,
        "review_notes_recorded",
        non_blocking_notes == 1,
        f"Non-blocking notes recorded={non_blocking_notes}; R382 elapsed_s drift was refreshed before commit.",
    )
    add_check(
        checks,
        "upstream_gates_pass",
        r380["status"] == "pass" and r381["status"] == "pass" and r382["status"] == "pass",
        "R380/R381/R382 all pass.",
    )
    add_check(
        checks,
        "r382_shape_preserved",
        r382["summary"]["empirical_profiling_experiments"] == 3
        and r382["summary"]["artifact_reproducibility_blocks"] == 1
        and r382["summary"]["checks_passed"] == r382["summary"]["checks_total"] == 8,
        "R382 records 3 empirical profiling experiments, 1 artifact block, and 8/8 checks.",
    )
    add_check(
        checks,
        "canonical_docs_and_papers_match",
        "three empirical profiling experiments plus one artifact/reproducibility block" in idea
        and "three empirical profiling\nexperiments plus one artifact/reproducibility block" in design
        and "three core empirical profiling experiments" in english
        and "artifact/reproducibility block" in english
        and "三个核心经验性 profiling 实验" in chinese
        and "artifact/reproducibility block" in chinese,
        "Canonical docs and both paper drafts use the current three-plus-one wording.",
    )
    add_check(
        checks,
        "e4_not_empirical_accuracy",
        "artifact hygiene rather than empirical profiler evidence" in one_line(idea)
        and "fourth accuracy result" in one_line(evaluation)
        and "not treated as a fourth hidden-label accuracy result" in english
        and r382_checks.get("e4_not_accuracy_result", {}).get("passed") is True,
        "E4 remains artifact/reproducibility/hygiene, not empirical accuracy evidence; R382 also checks the fourth-experiment wording.",
    )
    add_check(
        checks,
        "must_not_claims_visible",
        all(token in combined for token in MUST_NOT_TOKENS),
        "Must-not-claim guardrails remain visible in current docs/papers.",
    )
    add_check(
        checks,
        "r383_ledger_registered",
        "R383" in evaluation and "canonical reviewer acceptance" in evaluation,
        "Evaluation ledger records this reviewer-acceptance closure.",
    )
    add_check(
        checks,
        "english_submodule_clean",
        source_by_name["English paper"]["status"] == "tracked_clean"
        and paper_submodule_head() == paper_submodule_index_head(),
        "English paper submodule is clean and parent gitlink is current.",
    )
    add_check(
        checks,
        "source_status_tracked",
        all(row["status"] in {"tracked_clean", "tracked_dirty_allowed"} for row in source_status),
        "All R383 inputs are tracked or intentionally staged/dirty.",
    )

    summary = {
        "reviewers": len(REVIEW_EVENTS),
        "final_accepts": final_accepts,
        "blocking_issues": blocking_issues,
        "non_blocking_notes": non_blocking_notes,
        "checks_passed": sum(1 for check in checks if check["passed"]),
        "checks_total": len(checks),
        "empirical_profiling_experiments": 3,
        "artifact_reproducibility_blocks": 1,
    }
    return {
        "run_id": RUN_ID,
        "status": "accepted" if all(check["passed"] for check in checks) else "needs_changes",
        "schema": "agentsight.paper_canonical_reviewer_acceptance.v1",
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
                "independent reviewer acceptance of the R382 canonical-doc three-plus-one cleanup",
                "paper-organization readiness for the scoped hidden-label profiling claim",
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
        "# R383 Canonical Reviewer Acceptance",
        "",
        f"Status: `{report['status']}`",
        f"Reviewer accepts: {report['summary']['final_accepts']}/{report['summary']['reviewers']}",
        f"Checks: {report['summary']['checks_passed']}/{report['summary']['checks_total']}",
        "",
        "R383 records independent reviewer acceptance after R382. It is a paper-integration guardrail, not a new empirical result.",
        "",
        "## Checks",
        "",
        "| Check | Passed | Detail |",
        "|---|---:|---|",
    ]
    for check in report["checks"]:
        lines.append(f"| {check['check']} | {check['passed']} | {check['detail']} |")
    lines.extend(["", "## Reviewers", "", "| Reviewer | Focus | Verdict | Blocking | Notes |", "|---|---|---|---:|---:|"])
    for event in report["review_events"]:
        lines.append(
            f"| {event['reviewer']} | {event['focus']} | {event['final_verdict']} | {len(event['blocking_issues'])} | {len(event['non_blocking_notes'])} |"
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
        f"<td>{html.escape(event['final_verdict'])}</td>"
        f"<td>{len(event['blocking_issues'])}</td>"
        f"<td>{len(event['non_blocking_notes'])}</td>"
        "</tr>"
        for event in report["review_events"]
    )
    path.write_text(
        f"""<!doctype html>
<meta charset="utf-8">
<title>{RUN_ID} Canonical Reviewer Acceptance</title>
<style>
body {{ font-family: system-ui, sans-serif; margin: 2rem; line-height: 1.45; }}
table {{ border-collapse: collapse; width: 100%; margin: 1rem 0; }}
th, td {{ border: 1px solid #d0d7de; padding: 0.45rem; vertical-align: top; }}
th {{ background: #f6f8fa; }}
.status {{ font-weight: 700; }}
</style>
<h1>{RUN_ID} Canonical Reviewer Acceptance</h1>
<p class="status">Status: {html.escape(report['status'])}; reviewers {report['summary']['final_accepts']}/{report['summary']['reviewers']}; checks {report['summary']['checks_passed']}/{report['summary']['checks_total']}.</p>
<p>This is a paper-integration guardrail, not a new empirical result.</p>
<h2>Checks</h2>
<table><tr><th>Check</th><th>Passed</th><th>Detail</th></tr>{check_rows}</table>
<h2>Reviewers</h2>
<table><tr><th>Reviewer</th><th>Focus</th><th>Verdict</th><th>Blocking</th><th>Notes</th></tr>{reviewer_rows}</table>
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
    (out_dir / "reviewer-acceptance-r383.json").write_text(
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
                "final_verdict": event["final_verdict"],
                "blocking_issue_count": len(event["blocking_issues"]),
                "non_blocking_note_count": len(event["non_blocking_notes"]),
                "rationale": event["rationale"],
            }
            for event in report["review_events"]
        ],
        [
            "reviewer",
            "agent_id",
            "focus",
            "final_verdict",
            "blocking_issue_count",
            "non_blocking_note_count",
            "rationale",
        ],
    )
    write_csv(out_dir / "source-status.csv", report["source_status"], ["source", "path", "status", "sha256"])
    write_markdown(out_dir / "reviewer-acceptance-r383.md", report)
    write_html(out_dir / "index.html", report)
    print(json.dumps(run_result, indent=2, sort_keys=True))
    return 0 if report["status"] == "accepted" else 1


if __name__ == "__main__":
    raise SystemExit(main())
