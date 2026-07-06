#!/usr/bin/env python3
"""R385: RQ section contract focus gate.

This paper-organization guardrail checks that each RQ/E section opens with a
reviewer-facing experiment contract and claim test, not an R-numbered provenance
sentence. It reads the current paper drafts only; it does not fetch data, sync
datasets, relabel traces, rerun the profiler, or add a new empirical result.
"""

from __future__ import annotations

import argparse
import ast
import csv
import hashlib
import json
import re
import subprocess
import time
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OUT_ROOT = ROOT / "docs" / "visexp" / "out"
DEFAULT_OUT_DIR = OUT_ROOT / "paper-rq-contract-focus-r385"
RUN_ID = "R385"
SCRIPT_PATH = Path(__file__).resolve()
PAPER_SUBMODULE = ROOT / "docs" / "agentpprof-paper"
PAPER_SUBMODULE_PATH = "docs/agentpprof-paper"

SOURCES = {
    "English paper": PAPER_SUBMODULE / "main.tex",
    "Chinese paper": ROOT / "docs" / "visexp" / "paper" / "main.tex",
    "evaluation ledger": ROOT / "docs" / "evaluation.md",
}

RQ_LABELS = ["RQ1/E1", "RQ2/E2", "RQ3/E3", "RQ4/E4"]


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


def section_after(text: str, label: str) -> str:
    marker = r"\\subsection\{" + re.escape(label)
    match = re.search(marker, text)
    if not match:
        return ""
    rest = text[match.start() :]
    next_match = re.search(r"\n\\subsection\{", rest[len(match.group(0)) :])
    if not next_match:
        return rest
    return rest[: len(match.group(0)) + next_match.start()]


def first_content_line(section: str) -> str:
    lines = section.splitlines()
    for line in lines[1:]:
        stripped = line.strip()
        if stripped and not stripped.startswith("%"):
            return stripped
    return ""


def contract_rows(english: str, chinese: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for label in RQ_LABELS:
        en_section = section_after(english, label)
        zh_section = section_after(chinese, label)
        rows.append(
            {
                "rq": label,
                "english_first_line": first_content_line(en_section),
                "chinese_first_line": first_content_line(zh_section),
                "english_has_claim_test": "Claim-test:" in en_section,
                "chinese_has_claim_test": "Claim-test：" in zh_section,
            }
        )
    return rows


def subprocess_command_strings(script_text: str) -> list[str]:
    tree = ast.parse(script_text)
    commands: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if not (
            isinstance(func, ast.Attribute)
            and func.attr == "run"
            and isinstance(func.value, ast.Name)
            and func.value.id == "subprocess"
        ):
            continue
        if not node.args or not isinstance(node.args[0], ast.List):
            commands.append("<dynamic>")
            continue
        parts: list[str] = []
        for elt in node.args[0].elts:
            if isinstance(elt, ast.Constant) and isinstance(elt.value, str):
                parts.append(elt.value)
            else:
                parts.append("<dynamic>")
        commands.append(" ".join(parts))
    return commands


def build_report() -> dict[str, Any]:
    english = read_text(SOURCES["English paper"])
    chinese = read_text(SOURCES["Chinese paper"])
    evaluation = read_text(SOURCES["evaluation ledger"])
    script_text = read_text(SCRIPT_PATH)
    rows = contract_rows(english, chinese)
    checks: list[dict[str, Any]] = []
    forbidden_runtime_tokens = [
        "agentpprof --",
        "cargo run",
        "cargo test",
        "curl ",
        "wget ",
        "datasets.load_dataset",
        "hf_hub_download",
    ]
    runtime_commands = subprocess_command_strings(script_text)
    forbidden_runtime_hits = [
        command
        for command in runtime_commands
        for token in forbidden_runtime_tokens
        if token in command
    ]

    add_check(
        checks,
        "english_uses_experiment_contracts",
        english.count("Experiment contract:") == 4 and "Evidence contract:" not in english,
        "English RQ/E sections use four reviewer-facing experiment contracts.",
    )
    add_check(
        checks,
        "chinese_uses_experiment_contracts",
        chinese.count("实验契约：RQ") == 4 and "R361 将本节的 evidence contract 固定为" not in chinese,
        "Chinese RQ/E sections use four experiment contracts and no R361-led section openings.",
    )
    add_check(
        checks,
        "section_openings_are_contracts",
        all(row["english_first_line"].startswith("Experiment contract:") for row in rows)
        and all(row["chinese_first_line"].startswith("实验契约：") for row in rows),
        "The first content line after every RQ/E subsection is the experiment contract.",
    )
    add_check(
        checks,
        "claim_tests_present",
        all(row["english_has_claim_test"] and row["chinese_has_claim_test"] for row in rows),
        "Every RQ/E subsection still states a claim test.",
    )
    add_check(
        checks,
        "ledger_records_r385_as_focus_gate_when_present",
        "R385" not in evaluation or "RQ section contract focus" in evaluation,
        "If R385 is present in the ledger, it is a paper-focus gate, not a profiler experiment.",
    )
    add_check(
        checks,
        "no_data_or_profiler_rerun",
        not forbidden_runtime_hits,
        f"Runtime commands={runtime_commands}; forbidden hits={forbidden_runtime_hits}",
    )

    return {
        "run_id": RUN_ID,
        "status": "pass" if all(check["passed"] for check in checks) else "fail",
        "generated_at_unix": time.time(),
        "claim": (
            "Each RQ/E section opens as a claim-facing experiment contract rather "
            "than an R-numbered provenance paragraph."
        ),
        "checks": checks,
        "contract_rows": rows,
        "source_status": source_rows(),
    }


def write_outputs(report: dict[str, Any], out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "rq-contract-focus-report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    with (out_dir / "rq-contract-focus-checks.csv").open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["check", "passed", "detail"], lineterminator="\n")
        writer.writeheader()
        writer.writerows(report["checks"])
    lines = [
        f"# {RUN_ID} RQ Section Contract Focus Gate",
        "",
        f"Status: **{report['status']}**",
        "",
        report["claim"],
        "",
        "## Section Openings",
        "",
        "| RQ | English first line | Chinese first line | Claim tests |",
        "|---|---|---|---:|",
    ]
    for row in report["contract_rows"]:
        tests = row["english_has_claim_test"] and row["chinese_has_claim_test"]
        lines.append(
            f"| {row['rq']} | {row['english_first_line']} | {row['chinese_first_line']} | {tests} |"
        )
    lines.extend(["", "## Checks", "", "| Check | Passed | Detail |", "|---|---:|---|"])
    for check in report["checks"]:
        lines.append(f"| {check['check']} | {check['passed']} | {check['detail']} |")
    lines.extend(["", "## Sources", "", "| Source | Status | Path |", "|---|---:|---|"])
    for row in report["source_status"]:
        lines.append(f"| {row['source']} | {row['status']} | `{row['path']}` |")
    (out_dir / "rq-contract-focus-report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
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
