#!/usr/bin/env python3
"""R381: task diagnosis-card presentation gate.

This paper-integration guardrail checks that the E3 task diagnosis cards expose
label-scored localization signals, concrete profile-configuration actions, and
counterpoints for all six oracle-backed tasks. It reads existing task-card and
verdict artifacts plus current paper text; it does not download data, relabel
traces, or rerun the profiler.
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
DEFAULT_OUT_DIR = OUT_ROOT / "paper-diagnosis-card-r381"
RUN_ID = "R381"
SCRIPT_PATH = Path(__file__).resolve()
PAPER_SUBMODULE = ROOT / "docs" / "agentpprof-paper"
PAPER_SUBMODULE_PATH = "docs/agentpprof-paper"

SOURCES = {
    "R365 headline case studies": OUT_ROOT / "paper-headline-case-studies-r365" / "headline-case-studies.json",
    "R365 task cards": OUT_ROOT / "paper-headline-case-studies-r365" / "task-case-cards.csv",
    "R373 task verdict": OUT_ROOT / "paper-task-claim-verdict-r373" / "task-claim-verdict-report.json",
    "R373 task verdict rows": OUT_ROOT / "paper-task-claim-verdict-r373" / "task-claim-verdict.csv",
    "R380 experiment-block gate": OUT_ROOT / "paper-experiment-block-consolidation-r380" / "experiment-block-consolidation-report.json",
    "English paper": PAPER_SUBMODULE / "main.tex",
    "Chinese paper": ROOT / "docs" / "visexp" / "paper" / "main.tex",
    "evaluation ledger": ROOT / "docs" / "evaluation.md",
}

TASK_TOKENS = {
    "agentreward_looping": ["Looping", "0.4938", "0.6508", "0.1155"],
    "agentreward_side_effect": ["Side-effect", "0.1454", "0.1139", "0.0591"],
    "satraj_unsafe": ["Unsafe operation", "0.0420", "0.2621", "0.5081"],
    "agentnet_incorrect_step": ["Incorrect step", "0.0014", "0.0034", "0.0160"],
    "agentnet_redundant_step": ["Redundant step", "0.0089", "0.0177", "0.0011"],
    "osworld_group_start": ["Group start", "0.4074", "0.3874", "0.2583", "74"],
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


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


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


def build_report() -> dict[str, Any]:
    r365 = read_json(SOURCES["R365 headline case studies"])
    r373 = read_json(SOURCES["R373 task verdict"])
    r380 = read_json(SOURCES["R380 experiment-block gate"])
    task_cards = read_csv(SOURCES["R365 task cards"])
    verdict_rows = read_csv(SOURCES["R373 task verdict rows"])
    english = read_text(SOURCES["English paper"])
    chinese = read_text(SOURCES["Chinese paper"])
    evaluation = read_text(SOURCES["evaluation ledger"])
    combined = english + "\n" + chinese
    source_status = source_rows()
    source_by_name = {row["source"]: row for row in source_status}
    checks: list[dict[str, Any]] = []

    add_check(
        checks,
        "upstream_artifacts_pass",
        r365["status"] == "pass" and r373["status"] == "pass" and r380["status"] == "pass",
        "R365/R373/R380 are passing tracked inputs.",
    )
    add_check(
        checks,
        "six_task_cards_available",
        len(task_cards) == 6 and len(verdict_rows) == 6,
        f"R365 task cards={len(task_cards)}; R373 verdict rows={len(verdict_rows)}.",
    )
    missing_tokens: dict[str, list[str]] = {}
    for task, tokens in TASK_TOKENS.items():
        absent = [token for token in tokens if token not in combined]
        if absent:
            missing_tokens[task] = absent
    add_check(
        checks,
        "paper_cards_preserve_task_numbers",
        not missing_tokens,
        f"Missing task tokens={missing_tokens}",
    )
    add_check(
        checks,
        "paper_cards_have_actions_and_counterpoints",
        all(
            token in combined
            for token in [
                "prevalence-aware ranking",
                "write/input",
                "risky environments",
                "fixed sessions for examples",
                "boundary-derived fields",
                "first-positive work",
                "Fixed-session",
                "Raw-action",
            ]
        ),
        "The cards include profile actions and explicit baseline counterpoints.",
    )
    add_check(
        checks,
        "cards_link_e2_to_e3",
        "Localization signal" in english
        and "Profile action" in english
        and "Counterpoint" in english
        and "Localization signal" in chinese
        and "Profile action" in chinese
        and "Counterpoint" in chinese,
        "The table columns tie localization evidence to actionability and counterpoints.",
    )
    add_check(
        checks,
        "no_new_experiment_language",
        ("not a new empirical result" in (english + evaluation)) and "不是新增实验" in chinese,
        "The diagnosis cards are presented as paper integration, not a new experiment.",
    )
    add_check(
        checks,
        "non_claims_preserved",
        all(token in combined for token in ["automatic patch selection", "automatic boundary discovery", "human-productivity"])
        and all(token in chinese for token in ["automatic patch selector", "human utility", "metric dominance"]),
        "The cards do not introduce automatic selector, human-utility, or metric-dominance claims.",
    )
    add_check(
        checks,
        "evaluation_ledger_mentions_r381",
        "R381" in evaluation and "diagnosis-card" in evaluation,
        "The evaluation ledger records this diagnosis-card gate.",
    )
    add_check(
        checks,
        "english_submodule_input_committed",
        source_by_name["English paper"]["status"] == "tracked_clean"
        and paper_submodule_head() == paper_submodule_index_head()
        and bool(paper_submodule_head()),
        "The English paper input is clean in the submodule and captured by the parent gitlink.",
    )
    add_check(
        checks,
        "source_status_tracked",
        all(row["status"] in {"tracked_clean", "tracked_dirty_allowed"} for row in source_status),
        "All R381 sources are tracked or intentionally dirty/staged.",
    )

    summary = {
        "checks_passed": sum(1 for check in checks if check["passed"]),
        "checks_total": len(checks),
        "tasks": len(task_cards),
        "verdict_rows": len(verdict_rows),
        "paper_facing_blocks": 4,
        "empirical_profiling_experiments": 3,
        "artifact_blocks": 1,
    }
    return {
        "run_id": RUN_ID,
        "status": "pass" if all(check["passed"] for check in checks) else "fail",
        "schema": "agentsight.paper_diagnosis_card_gate.v1",
        "not_new_empirical_result": True,
        "network_access_required": False,
        "profiler_rerun": False,
        "data_sync": False,
        "checks": checks,
        "source_status": source_status,
        "summary": summary,
        "interpretation": (
            "The E3 diagnosis cards now expose per-task localization signals, concrete "
            "profile-configuration actions, and counterpoints while staying inside the 3+1 paper structure."
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
        "# R381 Diagnosis-Card Gate",
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
<title>{RUN_ID} Diagnosis-Card Gate</title>
<style>
body {{ font-family: system-ui, sans-serif; margin: 2rem; line-height: 1.45; }}
table {{ border-collapse: collapse; width: 100%; margin: 1rem 0; }}
th, td {{ border: 1px solid #d0d7de; padding: 0.45rem; vertical-align: top; }}
th {{ background: #f6f8fa; }}
.status {{ font-weight: 700; }}
</style>
<h1>{RUN_ID} Diagnosis-Card Gate</h1>
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
    (out_dir / "diagnosis-card-report.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (out_dir / "run-result.json").write_text(json.dumps(run_result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_csv(out_dir / "diagnosis-card-checks.csv", report["checks"])
    write_csv(out_dir / "source-status.csv", report["source_status"], ["source", "path", "status", "sha256"])
    write_markdown(out_dir / "diagnosis-card.md", report)
    write_html(out_dir / "index.html", report)
    print(json.dumps(run_result, indent=2, sort_keys=True))
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
