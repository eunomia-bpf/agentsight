#!/usr/bin/env python3
"""R397: main-body run-ledger suppression gate.

This paper-integration guard checks that the Chinese and English main paper
drafts present the evaluation as RQ1/E1 through RQ4/E4 rather than as a
chronological list of R-numbered runs. R-numbered runs remain valid provenance
inside docs/evaluation.md and result artifacts; this gate only applies to the
main paper bodies. It does not fetch datasets, relabel traces, rerun the
profiler, or run a human/agent analyst task.
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
DEFAULT_OUT_DIR = OUT_ROOT / "paper-main-body-run-ledger-r397"
RUN_ID = "R397"
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
}

RUN_ID_RE = re.compile(r"\bR\d{3}\b")
INTERNAL_STYLE_PATTERNS = [
    "Claim synthesis",
    "reviewer evidence packet",
    "reviewer evidence packets",
    "paper value/novelty synthesis",
    "paper evidence matrix",
    "submission audit",
    "Claim test",
    "Claim-test",
    "Experiment contract",
    "实验契约",
    "artifact ledger",
    "paper gates",
    "Gate / counterpoint",
    "supports-with-counterpoints",
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


def normalize(text: str) -> str:
    return " ".join(text.split())


def run_id_hits(path: Path) -> list[dict[str, Any]]:
    rows = []
    for line_no, line in enumerate(read_text(path).splitlines(), start=1):
        matches = sorted(set(RUN_ID_RE.findall(line)))
        if matches:
            rows.append({"path": rel(path), "line": line_no, "run_ids": ",".join(matches), "text": line.strip()})
    return rows


def internal_style_hits(path: Path) -> list[dict[str, Any]]:
    rows = []
    for line_no, line in enumerate(read_text(path).splitlines(), start=1):
        matches = [pattern for pattern in INTERNAL_STYLE_PATTERNS if pattern in line]
        if matches:
            rows.append({"path": rel(path), "line": line_no, "patterns": " | ".join(matches), "text": line.strip()})
    return rows


def add_check(checks: list[dict[str, Any]], name: str, passed: bool, detail: str) -> None:
    checks.append({"check": name, "passed": bool(passed), "detail": detail})


def build_report() -> dict[str, Any]:
    chinese = read_text(SOURCES["Chinese paper"])
    english = read_text(SOURCES["English paper"])
    evaluation = read_text(SOURCES["evaluation ledger"])
    idea = read_text(SOURCES["idea story"])
    chinese_norm = normalize(chinese)
    english_l = normalize(english).lower()
    evaluation_l = normalize(evaluation).lower()
    idea_l = normalize(idea).lower()
    r395 = read_json(SOURCES["R395 claim/verdict alignment"])
    r396 = read_json(SOURCES["R396 paper build smoke"])

    hits = run_id_hits(SOURCES["Chinese paper"]) + run_id_hits(SOURCES["English paper"])
    chinese_internal_style_hits = internal_style_hits(SOURCES["Chinese paper"])
    main_paper_internal_style_hits = chinese_internal_style_hits + internal_style_hits(SOURCES["English paper"])
    checks: list[dict[str, Any]] = []
    add_check(
        checks,
        "main_papers_have_no_run_ids",
        not hits,
        f"Found {len(hits)} R-numbered run-id mentions in main papers.",
    )
    add_check(
        checks,
        "main_papers_avoid_internal_checklist_terms",
        not main_paper_internal_style_hits,
        f"Found {len(main_paper_internal_style_hits)} internal checklist-style terms in the Chinese/English main papers.",
    )
    add_check(
        checks,
        "english_three_plus_one_visible",
        "three core empirical profiling experiments" in english_l
        and "artifact/reproducibility block" in english_l
        and "not additional main experiments" in english_l,
        "English draft frames E1-E3 plus E4 and demotes support artifacts from main experiments.",
    )
    add_check(
        checks,
        "chinese_three_plus_one_visible",
        ("三个核心经验性 profiling 实验" in chinese_norm or "前三个问题是 empirical profiling experiments" in chinese_norm)
        and "artifact/reproducibility block" in chinese_norm
        and "不会形成额外主实验" in chinese_norm,
        "Chinese draft frames E1-E3 plus E4 and demotes support artifacts from main experiments.",
    )
    for label in ["RQ1/E1", "RQ2/E2", "RQ3/E3", "RQ4/E4"]:
        add_check(
            checks,
            f"{label.lower().replace('/', '_')}_present_in_both_papers",
            label in english and label in chinese,
            f"{label} appears in both paper drafts.",
        )
    add_check(
        checks,
        "e4_not_accuracy_or_fifth_experiment",
        (
            "not treated as a fourth hidden-label accuracy result" in english_l
            or "do not add a new accuracy experiment" in english_l
        )
        and (
            "不是第四个经验性 profiling 实验" in chinese_norm
            or "不作为第四个经验性 profiling 实验" in chinese_norm
            or "不作为第四个 empirical accuracy result" in chinese_norm
        )
        and "not a fifth" in evaluation_l,
        "E4 is artifact/reproducibility hygiene, not another hidden-label accuracy experiment.",
    )
    add_check(
        checks,
        "ledger_keeps_run_ids_as_provenance",
        "r-numbered runs are provenance" in evaluation_l
        and "not the paper's evaluation structure" in evaluation_l,
        "Evaluation ledger keeps run IDs as provenance rather than main-paper structure.",
    )
    add_check(
        checks,
        "idea_story_next_action_matches",
        "do not add another empirical block" in idea_l and "three-plus-one paper structure" in idea_l,
        "Idea story preserves the next-action constraint against more small empirical blocks.",
    )
    add_check(
        checks,
        "r395_and_r396_still_pass",
        r395.get("status") == "pass" and r396.get("status") == "pass",
        f"R395 status={r395.get('status')}; R396 status={r396.get('status')}",
    )
    source_status = source_rows()
    add_check(
        checks,
        "source_status_tracked_or_dirty_allowed",
        all(
            row["status"] in {"tracked_clean", "tracked_dirty_allowed"}
            or (row["source"] == "generator script" and row["status"] == "untracked_or_missing")
            for row in source_status
        ),
        "All R397 inputs are tracked or intentionally dirty while this gate is generated.",
    )

    return {
        "run_id": RUN_ID,
        "status": "pass" if all(check["passed"] for check in checks) else "fail",
        "schema": "agentsight.paper_main_body_run_ledger_gate.v1",
        "network_access_required": False,
        "data_sync": False,
        "profiler_rerun": False,
        "human_or_agent_analyst_task": False,
        "run_id_hits": hits,
        "chinese_internal_style_hits": chinese_internal_style_hits,
        "main_paper_internal_style_hits": main_paper_internal_style_hits,
        "checks": checks,
        "source_status": source_status,
        "summary": {
            "checks_passed": sum(1 for check in checks if check["passed"]),
            "checks_total": len(checks),
            "main_paper_run_id_hits": len(hits),
            "chinese_internal_style_hits": len(chinese_internal_style_hits),
            "main_paper_internal_style_hits": len(main_paper_internal_style_hits),
        },
        "interpretation": (
            "The main paper bodies now present E1/E2/E3/E4 as the reviewer-facing "
            "evaluation path; R-numbered runs remain provenance in the ledger and "
            "artifacts rather than main experiments."
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
        "# R397 Main-Body Run-Ledger Suppression Gate",
        "",
        f"Status: `{report['status']}`",
        f"Checks: {report['summary']['checks_passed']}/{report['summary']['checks_total']}",
        f"Main-paper run-id hits: {report['summary']['main_paper_run_id_hits']}",
        f"Main-paper internal-style hits: {report['summary']['main_paper_internal_style_hits']}",
        f"Chinese internal-style hits: {report['summary']['chinese_internal_style_hits']}",
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
<title>{RUN_ID} Main-Body Run-Ledger Gate</title>
<style>
body {{ font-family: system-ui, sans-serif; margin: 2rem; line-height: 1.45; }}
table {{ border-collapse: collapse; width: 100%; margin: 1rem 0; }}
th, td {{ border: 1px solid #d0d7de; padding: 0.45rem; vertical-align: top; }}
th {{ background: #f6f8fa; }}
.status {{ font-weight: 700; }}
</style>
<h1>{RUN_ID} Main-Body Run-Ledger Suppression Gate</h1>
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
    (out_dir / "main-body-run-ledger-report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (out_dir / "run-result.json").write_text(json.dumps(run_result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_csv(out_dir / "main-body-run-ledger-checks.csv", report["checks"])
    write_csv(out_dir / "run-id-hits.csv", report["run_id_hits"], ["path", "line", "run_ids", "text"])
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
    write_csv(out_dir / "source-status.csv", report["source_status"], ["source", "path", "status", "sha256"])
    write_markdown(out_dir / "main-body-run-ledger.md", report)
    write_html(out_dir / "index.html", report)
    print(json.dumps(run_result, indent=2, sort_keys=True))
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
