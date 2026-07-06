#!/usr/bin/env python3
"""R382: canonical three-plus-one consistency gate.

This paper-integration guardrail checks that canonical project docs and the
paper drafts describe the evaluation as three empirical profiling experiments
plus one artifact/reproducibility block. It reads current docs and existing
R380/R381 paper-organization artifacts; it does not fetch data, relabel traces,
or rerun the profiler.
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
DEFAULT_OUT_DIR = OUT_ROOT / "paper-canonical-three-plus-one-r382"
RUN_ID = "R382"
SCRIPT_PATH = Path(__file__).resolve()
PAPER_SUBMODULE = ROOT / "docs" / "agentpprof-paper"
PAPER_SUBMODULE_PATH = "docs/agentpprof-paper"

SOURCES = {
    "R380 experiment-block gate": OUT_ROOT / "paper-experiment-block-consolidation-r380" / "experiment-block-consolidation-report.json",
    "R381 diagnosis-card gate": OUT_ROOT / "paper-diagnosis-card-r381" / "diagnosis-card-report.json",
    "idea story": ROOT / "docs" / "idea-story.md",
    "design": ROOT / "docs" / "design.md",
    "evaluation ledger": ROOT / "docs" / "evaluation.md",
    "English paper": PAPER_SUBMODULE / "main.tex",
    "Chinese paper": ROOT / "docs" / "visexp" / "paper" / "main.tex",
}

FORBIDDEN_EXPERIMENT_PHRASES = [
    "four core experiments",
    "four empirical profiling experiments",
    "fourth empirical profiling experiment",
    "one replayability/overhead experiment",
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


def forbidden_hits(text_by_name: dict[str, str]) -> dict[str, list[str]]:
    hits: dict[str, list[str]] = {}
    for name, text in text_by_name.items():
        lowered = text.lower()
        matched = [phrase for phrase in FORBIDDEN_EXPERIMENT_PHRASES if phrase in lowered]
        if matched:
            hits[name] = matched
    return hits


def one_line(text: str) -> str:
    return " ".join(text.split())


def build_report() -> dict[str, Any]:
    r380 = read_json(SOURCES["R380 experiment-block gate"])
    r381 = read_json(SOURCES["R381 diagnosis-card gate"])
    texts = {name: read_text(path) for name, path in SOURCES.items() if path.suffix in {".md", ".tex"}}
    idea = texts["idea story"]
    design = texts["design"]
    evaluation = texts["evaluation ledger"]
    english = texts["English paper"]
    chinese = texts["Chinese paper"]
    idea_line = one_line(idea)
    design_line = one_line(design)
    evaluation_line = one_line(evaluation)
    english_line = one_line(english)
    source_status = source_rows()
    source_by_name = {row["source"]: row for row in source_status}
    checks: list[dict[str, Any]] = []

    add_check(
        checks,
        "upstream_organization_gates_pass",
        r380["status"] == "pass" and r381["status"] == "pass",
        "R380/R381 organization and diagnosis-card gates pass.",
    )
    add_check(
        checks,
        "canonical_docs_use_three_plus_one",
        "three empirical profiling experiments plus one artifact/reproducibility block" in idea
        and "three empirical profiling\nexperiments plus one artifact/reproducibility block" in design,
        "Idea story and design use the three-plus-one wording.",
    )
    add_check(
        checks,
        "papers_use_three_plus_one",
        "three core empirical profiling experiments" in english
        and "artifact/reproducibility block" in english
        and "三个核心经验性 profiling 实验" in chinese
        and "artifact/reproducibility block" in chinese,
        "English and Chinese papers present E1-E3 plus E4 artifact block.",
    )
    hits = forbidden_hits({"idea story": idea, "design": design})
    add_check(
        checks,
        "no_stale_four_experiment_wording",
        not hits,
        f"Forbidden stale wording hits={hits}",
    )
    add_check(
        checks,
        "e4_not_accuracy_result",
        "artifact hygiene rather than empirical profiler evidence" in idea_line
        and "not another profiler abstraction" in design_line
        and "fourth accuracy result" in evaluation_line
        and "not treated as a fourth hidden-label accuracy result" in english_line
        and "fourth empirical profiling experiment" in english_line,
        "E4 remains artifact/repro/hygiene, not empirical accuracy evidence.",
    )
    add_check(
        checks,
        "r382_ledger_registered",
        "R382" in evaluation and "canonical three-plus-one" in evaluation,
        "Evaluation ledger records this canonical consistency gate.",
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
        "All R382 inputs are tracked or intentionally staged/dirty.",
    )

    summary = {
        "checks_passed": sum(1 for check in checks if check["passed"]),
        "checks_total": len(checks),
        "empirical_profiling_experiments": 3,
        "artifact_reproducibility_blocks": 1,
        "data_sync": False,
        "profiler_rerun": False,
    }
    return {
        "run_id": RUN_ID,
        "status": "pass" if all(check["passed"] for check in checks) else "fail",
        "schema": "agentsight.paper_canonical_three_plus_one_gate.v1",
        "network_access_required": False,
        "data_sync": False,
        "profiler_rerun": False,
        "checks": checks,
        "source_status": source_status,
        "summary": summary,
        "interpretation": (
            "Canonical docs and paper drafts consistently present the evaluation as "
            "three empirical profiling experiments plus one artifact/reproducibility block."
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
        "# R382 Canonical Three-Plus-One Gate",
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
<title>{RUN_ID} Canonical Three-Plus-One Gate</title>
<style>
body {{ font-family: system-ui, sans-serif; margin: 2rem; line-height: 1.45; }}
table {{ border-collapse: collapse; width: 100%; margin: 1rem 0; }}
th, td {{ border: 1px solid #d0d7de; padding: 0.45rem; vertical-align: top; }}
th {{ background: #f6f8fa; }}
.status {{ font-weight: 700; }}
</style>
<h1>{RUN_ID} Canonical Three-Plus-One Gate</h1>
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
    (out_dir / "canonical-three-plus-one-report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (out_dir / "run-result.json").write_text(json.dumps(run_result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_csv(out_dir / "canonical-three-plus-one-checks.csv", report["checks"])
    write_csv(out_dir / "source-status.csv", report["source_status"], ["source", "path", "status", "sha256"])
    write_markdown(out_dir / "canonical-three-plus-one.md", report)
    write_html(out_dir / "index.html", report)
    print(json.dumps(run_result, indent=2, sort_keys=True))
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
