#!/usr/bin/env python3
"""R388: E3 main-display gate.

This paper-organization guardrail checks that RQ3/E3 presents the task
diagnosis cards as the main mechanism/actionability display. It reads the
current paper drafts only; it does not fetch data, sync datasets, relabel
traces, rerun the profiler, or add a new empirical result.
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
DEFAULT_OUT_DIR = OUT_ROOT / "paper-e3-main-display-r388"
RUN_ID = "R388"
SCRIPT_PATH = Path(__file__).resolve()
PAPER_SUBMODULE = ROOT / "docs" / "agentpprof-paper"
PAPER_SUBMODULE_PATH = "docs/agentpprof-paper"
TABLE_LABEL = "tab:actionability"

SOURCES = {
    "English paper": PAPER_SUBMODULE / "main.tex",
    "Chinese paper": ROOT / "docs" / "visexp" / "paper" / "main.tex",
    "evaluation ledger": ROOT / "docs" / "evaluation.md",
}

REQUIRED_TASK_ROWS = [
    "Looping",
    "Side-effect",
    "Unsafe operation",
    "Incorrect step",
    "Redundant step",
    "Group start",
]

REQUIRED_TABLE_TOKENS = [
    "Work@5 0.4938",
    "R@5 0.6508",
    "patch AP +0.1155",
    "patch AP +0.0591",
    "patch AP +0.5081",
    "patch AP +0.0160",
    "patch AP +0.0011",
    "boundary AP 0.2583",
    "groups to 74",
]

REQUIRED_SECTION_TOKENS = [
    "5/6",
    "36/36",
    "27/36",
    "25/36",
    "35/60",
    "7/60",
    "2/42",
    "0.0376",
    "0.5750",
    "0.2402",
    "0.2583",
    "108",
    "74",
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


def section_between(text: str, start_regex: str, end_regex: str) -> str:
    start = re.search(start_regex, text)
    if not start:
        return ""
    rest = text[start.start() :]
    end = re.search(end_regex, rest[len(start.group(0)) :])
    if not end:
        return rest
    return rest[: len(start.group(0)) + end.start()]


def table_for_label(text: str, label: str) -> str:
    label_marker = rf"\label{{{label}}}"
    label_match = re.search(re.escape(label_marker), text)
    if not label_match:
        return ""
    before = text.rfind(r"\begin{table", 0, label_match.start())
    after = text.find(r"\end{table", label_match.end())
    if before == -1 or after == -1:
        return ""
    end_line = text.find("\n", after)
    if end_line == -1:
        end_line = len(text)
    return text[before:end_line]


def table_row_count(table_text: str) -> int:
    body_match = re.search(r"\\midrule(?P<body>.*?)\\bottomrule", table_text, flags=re.S)
    if not body_match:
        return 0
    return body_match.group("body").count(r"\\")


def subprocess_command_strings(script_text: str) -> list[str]:
    tree = ast.parse(script_text)
    parent_by_id: dict[int, ast.AST] = {}
    for parent in ast.walk(tree):
        for child in ast.iter_child_nodes(parent):
            parent_by_id[id(child)] = parent

    def enclosing_function_name(node: ast.AST) -> str:
        current = node
        while id(current) in parent_by_id:
            current = parent_by_id[id(current)]
            if isinstance(current, ast.FunctionDef):
                return current.name
        return "<module>"

    def list_command(list_node: ast.List) -> str:
        parts: list[str] = []
        for elt in list_node.elts:
            if isinstance(elt, ast.Constant) and isinstance(elt.value, str):
                parts.append(elt.value)
            else:
                parts.append("<dynamic>")
        return " ".join(parts)

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
        enclosing_function = enclosing_function_name(node)
        if (
            node.args
            and isinstance(node.args[0], ast.Name)
            and node.args[0].id == "args"
            and enclosing_function == "git_stdout"
        ):
            commands.append("git_stdout(args)")
            continue
        if not node.args or not isinstance(node.args[0], ast.List):
            commands.append(f"{enclosing_function}:<dynamic>")
            continue
        commands.append(list_command(node.args[0]))
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "git_stdout":
            if node.args and isinstance(node.args[0], ast.List):
                commands.append("git_stdout call: " + list_command(node.args[0]))
            else:
                commands.append("git_stdout call: <dynamic>")
    return commands


def build_report() -> dict[str, Any]:
    english = read_text(SOURCES["English paper"])
    chinese = read_text(SOURCES["Chinese paper"])
    evaluation = read_text(SOURCES["evaluation ledger"])
    script_text = read_text(SCRIPT_PATH)

    english_section = section_between(english, r"\\subsection\{RQ3/E3:", r"\n\\subsection\{RQ4/E4:")
    chinese_section = section_between(chinese, r"\\subsection\{RQ3/E3：", r"\n\\subsection\{RQ4/E4：")
    english_table = table_for_label(english, TABLE_LABEL)
    chinese_table = table_for_label(chinese, TABLE_LABEL)
    combined_table = english_table + "\n" + chinese_table
    english_section_flat = re.sub(r"\s+", " ", english_section)
    chinese_section_flat = re.sub(r"\s+", " ", chinese_section)
    english_table_flat = re.sub(r"\s+", " ", english_table)
    chinese_table_flat = re.sub(r"\s+", " ", chinese_table)

    runtime_commands = subprocess_command_strings(script_text)
    forbidden_runtime_tokens = [
        "agentpprof --",
        "cargo run",
        "cargo test",
        "curl ",
        "wget ",
        "datasets.load_dataset",
        "hf_hub_download",
    ]
    forbidden_runtime_hits = [
        command for command in runtime_commands for token in forbidden_runtime_tokens if token in command
    ]
    non_git_runtime_commands = [
        command for command in runtime_commands if not (command.startswith("git ") or command.startswith("git_stdout"))
    ]

    checks: list[dict[str, Any]] = []
    missing_rows = [row for row in REQUIRED_TASK_ROWS if row not in combined_table]
    missing_table_tokens = [token for token in REQUIRED_TABLE_TOKENS if token not in combined_table]
    missing_en_section_tokens = [token for token in REQUIRED_SECTION_TOKENS if token not in english_section]
    missing_zh_section_tokens = [token for token in REQUIRED_SECTION_TOKENS if token not in chinese_section]

    add_check(
        checks,
        "e3_tables_present_once",
        english.count(rf"\label{{{TABLE_LABEL}}}") == 1
        and chinese.count(rf"\label{{{TABLE_LABEL}}}") == 1
        and "E3 task diagnosis cards" in english_table
        and "E3 task diagnosis cards" in chinese_table,
        "Both drafts have exactly one E3 task diagnosis-card table.",
    )
    add_check(
        checks,
        "tables_live_inside_rq3_sections",
        bool(english_table and english_table in english_section and chinese_table and chinese_table in chinese_section),
        "Both actionability tables are located inside RQ3/E3 before RQ4/E4.",
    )
    add_check(
        checks,
        "six_task_rows_preserved",
        not missing_rows and table_row_count(english_table) == 6 and table_row_count(chinese_table) == 6,
        f"Missing task rows={missing_rows}; English rows={table_row_count(english_table)}; Chinese rows={table_row_count(chinese_table)}.",
    )
    add_check(
        checks,
        "task_card_numbers_preserved",
        not missing_table_tokens,
        f"Missing table tokens={missing_table_tokens}.",
    )
    add_check(
        checks,
        "section_actionability_numbers_preserved",
        not missing_en_section_tokens and not missing_zh_section_tokens,
        f"Missing English={missing_en_section_tokens}; missing Chinese={missing_zh_section_tokens}.",
    )
    add_check(
        checks,
        "source_artifact_role_visible",
        "R365/R373 are source artifacts" in english_table_flat
        and "not a new empirical experiment" in english_table_flat
        and "R365/R373 task-card evidence" in chinese_section_flat
        and "不新增主实验" in chinese_section,
        "R365/R373 are framed as provenance for the E3 main display, not new main experiments.",
    )
    add_check(
        checks,
        "no_hidden_label_leakage_or_auto_selector_claim",
        "Hidden labels are used only after profiling" in english_section_flat
        and "not a label-free automatic selector" in english_section_flat
        and "not automatic boundary discovery" in english_section_flat
        and "not automatic patch selection" in english_section_flat
        and "Hidden labels 只在 profiling 之后用于 scoring" in chinese_section_flat
        and "不是 label-free automatic selector" in chinese_section_flat
        and "不支持 automatic boundary discovery" in chinese_section_flat
        and "automatic patch selector" in chinese_section_flat,
        "E3 keeps hidden-label no-leakage and automatic-selector/boundary/patch non-claims visible.",
    )
    add_check(
        checks,
        "ledger_records_r388_as_focus_gate_when_present",
        RUN_ID not in evaluation or "E3 main-display gate" in evaluation,
        "If R388 is present in the ledger, it is a paper-focus gate, not a profiler experiment.",
    )
    add_check(
        checks,
        "no_data_or_profiler_rerun",
        not forbidden_runtime_hits and not non_git_runtime_commands,
        (
            f"Runtime commands={runtime_commands}; forbidden hits={forbidden_runtime_hits}; "
            f"non-git commands={non_git_runtime_commands}."
        ),
    )

    return {
        "run_id": RUN_ID,
        "status": "pass" if all(check["passed"] for check in checks) else "fail",
        "generated_at_unix": time.time(),
        "claim": (
            "RQ3/E3 presents task diagnosis cards as the main "
            "mechanism/actionability display with R365/R373 recorded as provenance."
        ),
        "checks": checks,
        "tables": {
            "english_row_count": table_row_count(english_table),
            "chinese_row_count": table_row_count(chinese_table),
            "required_task_rows": REQUIRED_TASK_ROWS,
            "required_table_tokens": REQUIRED_TABLE_TOKENS,
            "required_section_tokens": REQUIRED_SECTION_TOKENS,
        },
        "source_status": source_rows(),
    }


def write_outputs(report: dict[str, Any], out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "e3-main-display-report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    with (out_dir / "e3-main-display-checks.csv").open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["check", "passed", "detail"], lineterminator="\n")
        writer.writeheader()
        writer.writerows(report["checks"])
    lines = [
        f"# {RUN_ID} E3 Main-Display Gate",
        "",
        f"Status: **{report['status']}**",
        "",
        report["claim"],
        "",
        "## Table Shape",
        "",
        "| Paper | Rows |",
        "|---|---:|",
        f"| English | {report['tables']['english_row_count']} |",
        f"| Chinese | {report['tables']['chinese_row_count']} |",
        "",
        "## Checks",
        "",
        "| Check | Passed | Detail |",
        "|---|---:|---|",
    ]
    for check in report["checks"]:
        lines.append(f"| {check['check']} | {check['passed']} | {check['detail']} |")
    lines.extend(["", "## Sources", "", "| Source | Status | Path |", "|---|---:|---|"])
    for row in report["source_status"]:
        lines.append(f"| {row['source']} | {row['status']} | `{row['path']}` |")
    (out_dir / "e3-main-display-report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
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
