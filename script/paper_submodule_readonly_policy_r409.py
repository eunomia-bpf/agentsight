#!/usr/bin/env python3
"""R409: English paper submodule read-only policy gate.

This paper-integration guard records the current collaboration constraint:
outer-repo Chinese paper and evidence may continue to evolve, while the English
paper submodule under docs/agentpprof-paper is read-only unless explicitly
requested. The gate reads git status and existing outer R397/R398/R399/R405
artifacts only; it does not read, edit, restore, update, commit, push, or build
the submodule.
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
EXPECTED_ROOT = Path("/home/yunwei37/workspace/agentsight-research-semantic-flamegraph")
OUT_ROOT = ROOT / "docs" / "visexp" / "out"
DEFAULT_OUT_DIR = OUT_ROOT / "paper-submodule-readonly-policy-r409"
RUN_ID = "R409"
SCRIPT_PATH = Path(__file__).resolve()
SUBMODULE_PATH = "docs/agentpprof-paper"

SOURCES = {
    "AGENTS instructions": ROOT / "AGENTS.md",
    "CLAUDE instructions": ROOT / "CLAUDE.md",
    "idea story": ROOT / "docs" / "idea-story.md",
    "evaluation ledger": ROOT / "docs" / "evaluation.md",
    "implementation ledger": ROOT / "docs" / "implementation.md",
    "R397 anti-run-ledger report": OUT_ROOT
    / "paper-main-body-run-ledger-r397"
    / "main-body-run-ledger-report.json",
    "R397 run result": OUT_ROOT / "paper-main-body-run-ledger-r397" / "run-result.json",
    "R398 current organization report": OUT_ROOT
    / "paper-current-three-plus-one-r398"
    / "current-three-plus-one-report.json",
    "R398 run result": OUT_ROOT / "paper-current-three-plus-one-r398" / "run-result.json",
    "R399 PDF freshness report": OUT_ROOT / "paper-pdf-freshness-r399" / "pdf-freshness-report.json",
    "R399 run result": OUT_ROOT / "paper-pdf-freshness-r399" / "run-result.json",
    "R405 English gap audit": OUT_ROOT
    / "paper-english-experiment-gap-audit-r405"
    / "english-experiment-gap-audit.json",
    "R405 run result": OUT_ROOT / "paper-english-experiment-gap-audit-r405" / "run-result.json",
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


def git(args: list[str], check: bool = False) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=check,
    )


def git_stdout(args: list[str]) -> str:
    return git(args, check=True).stdout.strip()


def git_status_display(display: str) -> str:
    tracked = git(["ls-files", "--error-unmatch", "--", display])
    if tracked.returncode != 0:
        return "untracked_or_missing"
    unstaged = git(["diff", "--quiet", "--", display])
    staged = git(["diff", "--cached", "--quiet", "--", display])
    return "tracked_clean" if unstaged.returncode == 0 and staged.returncode == 0 else "tracked_dirty_allowed"


def source_rows() -> list[dict[str, str]]:
    rows = []
    for name, path in {"generator script": SCRIPT_PATH, **SOURCES}.items():
        rows.append(
            {
                "source": name,
                "path": rel(path),
                "status": git_status_display(rel(path)) if path.exists() else "missing",
                "sha256": sha256(path) if path.exists() else "",
            }
        )
    rows.append(
        {
            "source": "English paper submodule gitlink",
            "path": SUBMODULE_PATH,
            "status": git_status_display(SUBMODULE_PATH),
            "sha256": submodule_state()["summary"],
        }
    )
    return rows


def current_branch() -> str:
    return git_stdout(["rev-parse", "--abbrev-ref", "HEAD"])


def upstream_ref() -> str:
    result = git(["rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}"])
    return result.stdout.strip() if result.returncode == 0 else ""


def submodule_state() -> dict[str, Any]:
    parent_line = git_stdout(["ls-files", "-s", "--", SUBMODULE_PATH])
    parent_parts = parent_line.split()
    parent_index = parent_parts[1] if len(parent_parts) >= 2 else ""
    head_result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=ROOT / SUBMODULE_PATH,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    submodule_head = head_result.stdout.strip() if head_result.returncode == 0 else ""
    worktree_status = subprocess.run(
        ["git", "status", "--short", "--untracked-files=all"],
        cwd=ROOT / SUBMODULE_PATH,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    cached_diff = git(["diff", "--cached", "--quiet", "--", SUBMODULE_PATH])
    unstaged_diff = git(["diff", "--quiet", "--", SUBMODULE_PATH])
    upstream = upstream_ref()
    ahead_diff = None
    if upstream:
        ahead = git(["diff", "--quiet", f"{upstream}..HEAD", "--", SUBMODULE_PATH])
        ahead_diff = ahead.returncode != 0
    return {
        "parent_index": parent_index,
        "submodule_head": submodule_head,
        "worktree_status": worktree_status.stdout.strip().splitlines(),
        "cached_dirty": cached_diff.returncode != 0,
        "unstaged_dirty": unstaged_diff.returncode != 0,
        "upstream": upstream,
        "ahead_history_changes_submodule": ahead_diff,
        "push_safety": "unsafe_due_to_ahead_submodule_gitlink" if ahead_diff else "no_ahead_submodule_gitlink",
        "summary": f"submodule_head={submodule_head};parent_index={parent_index}",
    }


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


def check_row(name: str, passed: bool, detail: str) -> dict[str, Any]:
    return {"check": name, "passed": bool(passed), "detail": detail}


def build_report() -> dict[str, Any]:
    agents_text = read_text(SOURCES["AGENTS instructions"])
    claude_text = read_text(SOURCES["CLAUDE instructions"])
    agents_norm = normalize(agents_text)
    claude_norm = normalize(claude_text)
    idea_text = read_text(SOURCES["idea story"])
    evaluation_text = read_text(SOURCES["evaluation ledger"])
    implementation_text = read_text(SOURCES["implementation ledger"])
    r397 = read_json(SOURCES["R397 anti-run-ledger report"])
    r397_run = read_json(SOURCES["R397 run result"])
    r398 = read_json(SOURCES["R398 current organization report"])
    r398_run = read_json(SOURCES["R398 run result"])
    r399 = read_json(SOURCES["R399 PDF freshness report"])
    r399_run = read_json(SOURCES["R399 run result"])
    r405 = read_json(SOURCES["R405 English gap audit"])
    r405_run = read_json(SOURCES["R405 run result"])
    submodule = submodule_state()
    branch = current_branch()
    sources = source_rows()

    policy_tokens = [
        "Do not touch the paper submodule under `docs/agentpprof-paper/`",
        "unless the user explicitly asks to operate on that submodule",
        "The outer `main.tex` is the Chinese paper",
        "Do not commit, restore, or update submodule contents",
    ]
    doc_gap_tokens = [
        "R405 records the English submodule read-only sync gap",
        "do not edit the English submodule unless explicitly allowed",
        "R405 English read-only gap handling",
        "records English drift through R405 instead of editing the submodule",
    ]

    r397_checks = {row.get("check"): bool(row.get("passed")) for row in r397.get("checks", [])}
    r398_checks = {row.get("check"): bool(row.get("passed")) for row in r398.get("checks", [])}
    r399_checks = {row.get("check"): bool(row.get("passed")) for row in r399.get("checks", [])}

    checks = [
        check_row(
            "root_matches_requested_worktree",
            ROOT.resolve() == EXPECTED_ROOT,
            f"ROOT={ROOT.resolve()} expected={EXPECTED_ROOT}",
        ),
        check_row(
            "branch_is_research_v2",
            branch == "research/semantic-flamegraph-artifacts-v2",
            f"branch={branch}",
        ),
        check_row(
            "agents_policy_forbids_submodule_edits",
            all(token in agents_norm for token in policy_tokens) and all(token in claude_norm for token in policy_tokens),
            "AGENTS/CLAUDE contain the read-only submodule policy and Chinese-paper separation rule.",
        ),
        check_row(
            "submodule_not_staged",
            not submodule["cached_dirty"],
            "No staged parent-index change for docs/agentpprof-paper.",
        ),
        check_row(
            "submodule_dirty_state_recorded_not_cleaned",
            submodule["unstaged_dirty"] or bool(submodule["worktree_status"]),
            f"Submodule dirty status is recorded and intentionally left alone: {submodule['worktree_status']}",
        ),
        check_row(
            "r405_gap_audit_passes",
            r405_run.get("status") == "pass" and english_read_only_gap_recorded(r405),
            "R405 records read-only English submodule scope and the current 3+1 sync gap.",
        ),
        check_row(
            "r397_uses_gap_aware_policy",
            r397_run.get("status") == "pass"
            and r397_checks.get("english_three_plus_one_visible_or_gap_recorded", False),
            "R397 passes with English synced or R405-recorded read-only gap.",
        ),
        check_row(
            "r398_uses_gap_aware_policy",
            r398_run.get("status") == "pass"
            and r398.get("summary", {}).get("english_read_only_gap_recorded") is True
            and r398_checks.get("three_plus_one_stated_in_chinese_and_english_synced_or_gap_recorded", False),
            "R398 treats Chinese as writable authority and English as synced or R405-recorded gap.",
        ),
        check_row(
            "r399_uses_gap_aware_policy",
            r399_run.get("status") == "pass"
            and r399.get("summary", {}).get("english_read_only_gap_recorded") is True
            and r399_checks.get("tracked_pdfs_contain_display_path", False),
            "R399 checks Chinese PDF freshness and routes English drift through R405.",
        ),
        check_row(
            "canonical_docs_record_readonly_policy",
            all(token in (idea_text + "\n" + evaluation_text + "\n" + implementation_text) for token in doc_gap_tokens),
            "Canonical docs describe R405 English read-only gap handling and avoid submodule edits.",
        ),
        check_row(
            "direct_push_safety_explicit",
            submodule["push_safety"] in {"unsafe_due_to_ahead_submodule_gitlink", "no_ahead_submodule_gitlink"},
            f"push_safety={submodule['push_safety']}; upstream={submodule['upstream']}",
        ),
        check_row(
            "source_status_tracked_or_dirty_allowed",
            all(
                row["status"] in {"tracked_clean", "tracked_dirty_allowed"}
                or (row["source"] == "generator script" and row["status"] == "untracked_or_missing")
                for row in sources
            ),
            "All R409 sources are tracked or intentionally dirty while the gate is generated.",
        ),
    ]

    return {
        "run_id": RUN_ID,
        "status": "pass" if all(row["passed"] for row in checks) else "fail",
        "schema": "agentsight.paper_submodule_readonly_policy_gate.v1",
        "network_access_required": False,
        "data_sync": False,
        "profiler_rerun": False,
        "paper_rebuild": False,
        "submodule_read_only": True,
        "submodule_edit": False,
        "submodule": submodule,
        "checks": checks,
        "source_status": sources,
        "summary": {
            "checks_passed": sum(1 for row in checks if row["passed"]),
            "checks_total": len(checks),
            "branch": branch,
            "push_safety": submodule["push_safety"],
        },
        "interpretation": (
            "The current outer-repo workflow can continue Chinese-paper and evidence "
            "work while treating docs/agentpprof-paper as read-only. English-paper "
            "sync gaps are recorded by R405/R397/R398/R399, not repaired by editing "
            "the submodule. A direct push remains unsafe when the ahead history "
            "contains a submodule gitlink update."
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
        "# R409 English Submodule Read-Only Policy Gate",
        "",
        f"Status: `{report['status']}`",
        f"Checks: {report['summary']['checks_passed']}/{report['summary']['checks_total']}",
        f"Push safety: `{report['summary']['push_safety']}`",
        "",
        report["interpretation"],
        "",
        "## Checks",
        "",
        "| Check | Passed | Detail |",
        "|---|---:|---|",
    ]
    for check in report["checks"]:
        lines.append(f"| {check['check']} | {check['passed']} | {str(check['detail']).replace('|', '\\|')} |")
    lines.extend(["", "## Submodule", "", "```json", json.dumps(report["submodule"], indent=2, sort_keys=True), "```"])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_html(path: Path, report: dict[str, Any]) -> None:
    check_rows = "\n".join(
        f"<tr><td>{html.escape(check['check'])}</td><td>{check['passed']}</td><td>{html.escape(str(check['detail']))}</td></tr>"
        for check in report["checks"]
    )
    path.write_text(
        f"""<!doctype html>
<meta charset="utf-8">
<title>{RUN_ID} English Submodule Read-Only Policy Gate</title>
<style>
body {{ font-family: system-ui, sans-serif; margin: 2rem; line-height: 1.45; }}
table {{ border-collapse: collapse; width: 100%; margin: 1rem 0; }}
th, td {{ border: 1px solid #d0d7de; padding: 0.45rem; vertical-align: top; }}
th {{ background: #f6f8fa; }}
.status {{ font-weight: 700; }}
pre {{ white-space: pre-wrap; background: #f6f8fa; padding: 1rem; }}
</style>
<h1>{RUN_ID} English Submodule Read-Only Policy Gate</h1>
<p class="status">Status: {html.escape(report['status'])}; checks {report['summary']['checks_passed']}/{report['summary']['checks_total']}.</p>
<p>{html.escape(report['interpretation'])}</p>
<h2>Checks</h2>
<table><tr><th>Check</th><th>Passed</th><th>Detail</th></tr>{check_rows}</table>
<h2>Submodule</h2>
<pre>{html.escape(json.dumps(report['submodule'], indent=2, sort_keys=True))}</pre>
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
    (out_dir / "submodule-readonly-policy-report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (out_dir / "run-result.json").write_text(json.dumps(run_result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_csv(out_dir / "submodule-readonly-policy-checks.csv", report["checks"])
    write_csv(out_dir / "source-status.csv", report["source_status"], ["source", "path", "status", "sha256"])
    write_markdown(out_dir / "submodule-readonly-policy.md", report)
    write_html(out_dir / "index.html", report)
    print(json.dumps(run_result, indent=2, sort_keys=True))
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
