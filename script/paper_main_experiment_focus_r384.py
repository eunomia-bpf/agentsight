#!/usr/bin/env python3
"""R384: main-paper experiment focus gate.

This paper-organization guardrail checks that the English and Chinese drafts
present the evaluation as three substantial empirical profiling experiments
plus one artifact/reproducibility block. It intentionally does not fetch data,
sync datasets, relabel traces, rerun the profiler, or add another experiment;
it only audits the current paper text.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import subprocess
import time
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OUT_ROOT = ROOT / "docs" / "visexp" / "out"
DEFAULT_OUT_DIR = OUT_ROOT / "paper-main-experiment-focus-r384"
RUN_ID = "R384"
SCRIPT_PATH = Path(__file__).resolve()
PAPER_SUBMODULE = ROOT / "docs" / "agentpprof-paper"
PAPER_SUBMODULE_PATH = "docs/agentpprof-paper"

SOURCES = {
    "English paper": PAPER_SUBMODULE / "main.tex",
    "Chinese paper": ROOT / "docs" / "visexp" / "paper" / "main.tex",
    "evaluation ledger": ROOT / "docs" / "evaluation.md",
    "R380 experiment-block gate": OUT_ROOT
    / "paper-experiment-block-consolidation-r380"
    / "experiment-block-consolidation-report.json",
    "R382 canonical three-plus-one gate": OUT_ROOT
    / "paper-canonical-three-plus-one-r382"
    / "canonical-three-plus-one-report.json",
}

FORBIDDEN_MAIN_BODY_MARKERS = [
    r"\label{tab:r374-roles}",
    r"\input{figures/experiment-role-table.tex}",
    r"\input{../out/paper-core-experiment-weight-r374/experiment-role-table.tex}",
    r"Table~\ref{tab:r374-roles}",
    r"表~\ref{tab:r374-roles}",
    "R374 three-plus-one role map",
    "R375 keeps the full claim-gate table",
    "R377 then materializes the central profiler claim",
    "R375 把完整 claim-gate 表",
    "R377 进一步把中心 profiling claim",
]

EN_REQUIRED = [
    "three empirical profiling experiments plus one artifact/reproducibility",
    "E2 is the single hidden-label localization/ranking experiment",
    "E3 asks which stack fields, mappings, rankers, and profile specs",
    "E4 is the reproducibility and claim-hygiene block",
    "they are not additional main experiments",
]

ZH_REQUIRED = [
    "三个核心经验性 profiling 实验加一个 artifact/reproducibility block",
    "E2 是唯一的 hidden-label localization/ranking 主实验",
    "E3 解释哪些 stack fields、mappings、rankers 和 profile specs",
    "E4 只负责 reproducibility 和 claim hygiene",
    "不形成额外主实验",
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


def marker_hits(texts: dict[str, str]) -> dict[str, list[str]]:
    hits: dict[str, list[str]] = {}
    for name, text in texts.items():
        found = [marker for marker in FORBIDDEN_MAIN_BODY_MARKERS if marker in text]
        if found:
            hits[name] = found
    return hits


def count_token(text: str, token: str) -> int:
    return text.count(token)


def build_report() -> dict[str, Any]:
    english = read_text(SOURCES["English paper"])
    chinese = read_text(SOURCES["Chinese paper"])
    evaluation = read_text(SOURCES["evaluation ledger"])
    r380 = read_json(SOURCES["R380 experiment-block gate"])
    r382 = read_json(SOURCES["R382 canonical three-plus-one gate"])
    source_status = source_rows()
    checks: list[dict[str, Any]] = []

    add_check(
        checks,
        "upstream_three_plus_one_gates_pass",
        r380["status"] == "pass" and r382["status"] == "pass",
        "R380 and R382 remain passing provenance for the three-plus-one organization.",
    )
    add_check(
        checks,
        "core_result_tables_present",
        r"\label{tab:core-results}" in english and r"\label{tab:results}" in chinese,
        "Both paper drafts keep a single paper-facing core result table.",
    )
    add_check(
        checks,
        "required_english_focus_wording",
        all(fragment in english for fragment in EN_REQUIRED),
        "English draft states E1/E2/E3/E4 roles and says support records are not additional experiments.",
    )
    add_check(
        checks,
        "required_chinese_focus_wording",
        all(fragment in chinese for fragment in ZH_REQUIRED),
        "Chinese draft states E1/E2/E3/E4 roles and says support records do not form extra experiments.",
    )
    hits = marker_hits({"English paper": english, "Chinese paper": chinese})
    add_check(
        checks,
        "no_main_body_role_map_table_or_run_ledger",
        not hits,
        f"Forbidden main-body role-map/run-ledger markers: {hits}",
    )
    add_check(
        checks,
        "four_named_blocks_only",
        all(count_token(english, token) > 0 for token in ["RQ1/E1", "RQ2/E2", "RQ3/E3", "RQ4/E4"])
        and all(count_token(chinese, token) > 0 for token in ["RQ1/E1", "RQ2/E2", "RQ3/E3", "RQ4/E4"]),
        "Both drafts explicitly route the paper through RQ1/E1--RQ4/E4.",
    )
    add_check(
        checks,
        "ledger_records_r384_as_paper_hygiene_when_present",
        "R384" not in evaluation or "main-paper experiment focus" in evaluation.lower(),
        "If R384 is already in the ledger, it is described as paper focus/hygiene, not a new profiler run.",
    )
    add_check(
        checks,
        "no_data_or_profiler_rerun",
        True,
        "This script reads paper text and prior gate reports only; it does not fetch data, relabel traces, or run agentpprof.",
    )

    report = {
        "run_id": RUN_ID,
        "status": "pass" if all(check["passed"] for check in checks) else "fail",
        "generated_at_unix": time.time(),
        "claim": (
            "The main paper is organized as three substantial empirical profiling "
            "experiments plus one artifact/reproducibility block, with R-numbered "
            "artifacts kept as provenance/support rather than main experiments."
        ),
        "checks": checks,
        "source_status": source_status,
        "summary_rows": [
            {
                "paper_block": "E1",
                "role": "Generality, two-abstraction coverage, recursive folding, and field derivation.",
                "main_experiment": "yes",
            },
            {
                "paper_block": "E2",
                "role": "Hidden-label localization/ranking over real labeled traces.",
                "main_experiment": "yes",
            },
            {
                "paper_block": "E3",
                "role": "Mechanism isolation and profile-configuration actionability.",
                "main_experiment": "yes",
            },
            {
                "paper_block": "E4",
                "role": "Artifact replayability, offline cost, and claim hygiene.",
                "main_experiment": "artifact block only",
            },
        ],
    }
    return report


def write_outputs(report: dict[str, Any], out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "main-experiment-focus-report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    with (out_dir / "main-experiment-focus-checks.csv").open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["check", "passed", "detail"], lineterminator="\n")
        writer.writeheader()
        writer.writerows(report["checks"])
    lines = [
        f"# {RUN_ID} Main-Paper Experiment Focus Gate",
        "",
        f"Status: **{report['status']}**",
        "",
        report["claim"],
        "",
        "## Paper Blocks",
        "",
        "| Block | Main experiment? | Role |",
        "|---|---:|---|",
    ]
    for row in report["summary_rows"]:
        lines.append(f"| {row['paper_block']} | {row['main_experiment']} | {row['role']} |")
    lines.extend(["", "## Checks", "", "| Check | Passed | Detail |", "|---|---:|---|"])
    for check in report["checks"]:
        lines.append(f"| {check['check']} | {check['passed']} | {check['detail']} |")
    lines.extend(["", "## Sources", "", "| Source | Status | Path |", "|---|---:|---|"])
    for row in report["source_status"]:
        lines.append(f"| {row['source']} | {row['status']} | `{row['path']}` |")
    (out_dir / "main-experiment-focus-report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (out_dir / "run-result.json").write_text(
        json.dumps(
            {
                "run_id": RUN_ID,
                "status": report["status"],
                "elapsed_s": 0.0,
                "out_dir": rel(out_dir),
                "script": rel(SCRIPT_PATH),
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )


def main() -> int:
    args = parse_args()
    start = time.time()
    report = build_report()
    write_outputs(report, args.out_dir)
    run_result = args.out_dir / "run-result.json"
    result = json.loads(run_result.read_text(encoding="utf-8"))
    result["elapsed_s"] = round(time.time() - start, 6)
    run_result.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"run_id": RUN_ID, "status": report["status"], "out_dir": rel(args.out_dir)}, sort_keys=True))
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
