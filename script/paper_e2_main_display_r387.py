#!/usr/bin/env python3
"""R387: E2 main-display gate.

This paper-organization guardrail checks that the hidden-label localization
benchmark is presented as the RQ2/E2 main display in both paper drafts. It reads
the current drafts only; it does not fetch data, sync datasets, relabel traces,
rerun the profiler, or add a new empirical result.
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
DEFAULT_OUT_DIR = OUT_ROOT / "paper-e2-main-display-r387"
RUN_ID = "R387"
SCRIPT_PATH = Path(__file__).resolve()
PAPER_SUBMODULE = ROOT / "docs" / "agentpprof-paper"
PAPER_SUBMODULE_PATH = "docs/agentpprof-paper"

SOURCES = {
    "English paper": PAPER_SUBMODULE / "main.tex",
    "Chinese paper": ROOT / "docs" / "visexp" / "paper" / "main.tex",
    "evaluation ledger": ROOT / "docs" / "evaluation.md",
}

REQUIRED_POLICY_ROWS = [
    "flat:width",
    "fixed-session:query-aware",
    "dataset-native:query-aware",
    "raw-action:query-aware",
    "operation-stack:width",
    "operation-stack:query-aware",
    "operation-stack:oracle-upper",
    "label-drilldown:oracle-upper",
]

REQUIRED_E2_TOKENS = [
    "34,539",
    "3,699",
    "0.0937",
    "1.0000",
    "0.3900",
    "0.3559",
    "285.0",
    "157.5",
    "5/6",
    "20/24",
    "22/24",
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

    english_section = section_between(english, r"\\subsection\{RQ2/E2:", r"\n\\subsection\{RQ3/E3:")
    chinese_section = section_between(chinese, r"\\subsection\{RQ2/E2：", r"\n\\subsection\{RQ3/E3：")
    english_table = table_for_label(english, "tab:r320")
    chinese_table = table_for_label(chinese, "tab:r320-accuracy")

    checks: list[dict[str, Any]] = []
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

    missing_english_rows = [row for row in REQUIRED_POLICY_ROWS if row not in english_table]
    missing_chinese_rows = [row for row in REQUIRED_POLICY_ROWS if row not in chinese_table]
    missing_english_tokens = [token for token in REQUIRED_E2_TOKENS if token not in english_section]
    missing_chinese_tokens = [token for token in REQUIRED_E2_TOKENS if token not in chinese_section]

    add_check(
        checks,
        "english_e2_table_present_once",
        english.count(r"\label{tab:r320}") == 1 and "E2 hidden-label localization benchmark" in english_table,
        "English paper has exactly one E2 hidden-label localization benchmark table.",
    )
    add_check(
        checks,
        "chinese_e2_table_present_once",
        chinese.count(r"\label{tab:r320-accuracy}") == 1 and "E2 hidden-label localization benchmark" in chinese_table,
        "Chinese paper has exactly one E2 hidden-label localization benchmark table.",
    )
    add_check(
        checks,
        "tables_live_inside_rq2_sections",
        bool(english_table and english_table in english_section and chinese_table and chinese_table in chinese_section),
        "Both E2 tables are located inside the RQ2/E2 source section before RQ3/E3.",
    )
    add_check(
        checks,
        "policy_rows_preserved",
        not missing_english_rows and not missing_chinese_rows and table_row_count(english_table) == 8 and table_row_count(chinese_table) == 8,
        f"Missing English rows={missing_english_rows}; missing Chinese rows={missing_chinese_rows}.",
    )
    add_check(
        checks,
        "headline_numbers_preserved_in_rq2",
        not missing_english_tokens and not missing_chinese_tokens,
        f"Missing English tokens={missing_english_tokens}; missing Chinese tokens={missing_chinese_tokens}.",
    )
    add_check(
        checks,
        "caption_is_e2_not_run_led",
        "R320 hidden-label profiler benchmark" not in english
        and "R320 hidden-label profiler benchmark" not in chinese
        and "R320 is the source artifact" in english_table
        and "R320 是 source artifact" in chinese_table,
        "Captions make R320 provenance explicit while presenting the table as E2.",
    )
    add_check(
        checks,
        "scope_and_counterpoints_visible",
        "Pareto condition, not a single winning" in english_section
        and "not universal dominance" in english_section
        and "human-productivity claim" in english_section
        and "full OpenTelemetry/Phoenix/LangSmith/Perfetto compatibility" in english_section
        and "Pareto 条件" in chinese_section
        and "不是对所有 trace-tree-shaped objectives 的 dominance" in chinese_section
        and "human/agent analyst productivity" in chinese_section
        and "OpenTelemetry/Phoenix/LangSmith/Perfetto span tree" in chinese_section,
        "E2 keeps flat/fixed-session counterpoints and must-not-claim boundaries visible.",
    )
    add_check(
        checks,
        "ledger_records_r387_as_focus_gate_when_present",
        RUN_ID not in evaluation or "E2 main-display gate" in evaluation,
        "If R387 is present in the ledger, it is a paper-focus gate, not a profiler experiment.",
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
            "RQ2/E2 presents the hidden-label localization/ranking benchmark as "
            "one paper-facing main display with R320 recorded as provenance."
        ),
        "checks": checks,
        "tables": {
            "english_row_count": table_row_count(english_table),
            "chinese_row_count": table_row_count(chinese_table),
            "required_policy_rows": REQUIRED_POLICY_ROWS,
            "required_e2_tokens": REQUIRED_E2_TOKENS,
        },
        "source_status": source_rows(),
    }


def write_outputs(report: dict[str, Any], out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "e2-main-display-report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    with (out_dir / "e2-main-display-checks.csv").open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["check", "passed", "detail"], lineterminator="\n")
        writer.writeheader()
        writer.writerows(report["checks"])
    lines = [
        f"# {RUN_ID} E2 Main-Display Gate",
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
    (out_dir / "e2-main-display-report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
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
