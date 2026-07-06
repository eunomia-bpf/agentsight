#!/usr/bin/env python3
"""R389: E4 main-display gate.

This paper-organization guardrail checks that RQ4/E4 presents replayability,
deterministic output, offline cost, and artifact hygiene as one
artifact/reproducibility block. It reads current paper drafts and existing
R327/R328 result artifacts only; it does not fetch data, sync datasets, relabel
traces, rerun the profiler, or add a new empirical accuracy result.
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
DEFAULT_OUT_DIR = OUT_ROOT / "paper-e4-main-display-r389"
RUN_ID = "R389"
SCRIPT_PATH = Path(__file__).resolve()
PAPER_SUBMODULE = ROOT / "docs" / "agentpprof-paper"
PAPER_SUBMODULE_PATH = "docs/agentpprof-paper"

SOURCES = {
    "English paper": PAPER_SUBMODULE / "main.tex",
    "Chinese paper": ROOT / "docs" / "visexp" / "paper" / "main.tex",
    "evaluation ledger": ROOT / "docs" / "evaluation.md",
    "R327 report": ROOT / "docs" / "visexp" / "out" / "operation-profile-cost-r327" / "profile-cost-report.md",
    "R327 summary": ROOT / "docs" / "visexp" / "out" / "operation-profile-cost-r327" / "profile-cost-summary.csv",
    "R328 report": ROOT
    / "docs"
    / "visexp"
    / "out"
    / "operation-profile-deterministic-output-r328"
    / "deterministic-output-report.md",
    "R328 summary": ROOT
    / "docs"
    / "visexp"
    / "out"
    / "operation-profile-deterministic-output-r328"
    / "deterministic-output-summary.csv",
}

ENGLISH_LABELS = ["tab:r327", "tab:r328"]
CHINESE_LABELS = ["tab:r327-cost", "tab:r328-determinism"]

REQUIRED_ENGLISH_TABLE_TOKENS = [
    "R300 view specs & 4 & 3.448 & 4.273 & 631.0",
    "R324 rank-feature specs & 12 & 1.539 & 2.692 & 41.0",
    "R326 robustness specs & 60 & 1.542 & 2.640 & 41.0",
    "All specs & 76 & 1.581 & 2.719 & 42.0",
    "R327 & default & 76/76 & 4/76 & 1.581 & 2.719",
    "R328 & deterministic & 76/76 & 76/76 & 1.601 & 2.767",
]

REQUIRED_CHINESE_TABLE_TOKENS = [
    "R300 views & 4 & 3.448 & 4.273 & 631.0",
    "R324 rank & 12 & 1.539 & 2.692 & 41.0",
    "R326 robust & 60 & 1.542 & 2.640 & 41.0",
    "All specs & 76 & 1.581 & 2.719 & 42.0",
    "R327 & default & 76/76 & 4/76 & 1.581 & 2.719",
    "R328 & deterministic & 76/76 & 76/76 & 1.601 & 2.767",
]

REQUIRED_SECTION_TOKENS = [
    "76",
    "152",
    "76/76",
    "4/76",
    "1.581",
    "2.719",
    "1.601",
    "2.767",
]

R327_ARTIFACT_TOKENS = [
    "Specs: 76",
    "Profiler invocations: 152",
    "Deterministic specs: 76/76",
    "Raw-byte deterministic specs: 4/76",
    "Median per-spec runtime: 1581.3334 ms",
    "P95 per-spec runtime: 2719.3206 ms",
    "does not measure live eBPF capture overhead, human utility, or compatibility",
]

R328_ARTIFACT_TOKENS = [
    "Specs: 76",
    "Profiler invocations: 152",
    "Semantic deterministic specs: 76/76",
    "Raw-byte deterministic specs: 76/76",
    "Median runtime: 1601.0827 ms",
    "P95 runtime: 2767.1653 ms",
    "This is not live eBPF capture overhead.",
    "This is not a human or agent analyst productivity study.",
    "This does not claim complete trace-platform ecosystem compatibility.",
    "This is not a detector or boundary-discovery benchmark.",
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
    r327_report = read_text(SOURCES["R327 report"])
    r328_report = read_text(SOURCES["R328 report"])
    r327_summary = read_text(SOURCES["R327 summary"])
    r328_summary = read_text(SOURCES["R328 summary"])
    script_text = read_text(SCRIPT_PATH)

    english_section = section_between(english, r"\\subsection\{RQ4/E4:", r"\n\\section\{Related Work")
    chinese_section = section_between(chinese, r"\\subsection\{RQ4/E4：", r"\n\\section\{哪些数据集")
    english_tables = [table_for_label(english, label) for label in ENGLISH_LABELS]
    chinese_tables = [table_for_label(chinese, label) for label in CHINESE_LABELS]
    english_table_text = "\n".join(english_tables)
    chinese_table_text = "\n".join(chinese_tables)
    english_section_flat = re.sub(r"\s+", " ", english_section)
    chinese_section_flat = re.sub(r"\s+", " ", chinese_section)
    english_tables_flat = re.sub(r"\s+", " ", english_table_text)
    chinese_tables_flat = re.sub(r"\s+", " ", chinese_table_text)

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

    missing_en_table_tokens = [token for token in REQUIRED_ENGLISH_TABLE_TOKENS if token not in english_tables_flat]
    missing_zh_table_tokens = [token for token in REQUIRED_CHINESE_TABLE_TOKENS if token not in chinese_tables_flat]
    missing_en_section_tokens = [token for token in REQUIRED_SECTION_TOKENS if token not in english_section]
    missing_zh_section_tokens = [token for token in REQUIRED_SECTION_TOKENS if token not in chinese_section]
    missing_r327_tokens = [token for token in R327_ARTIFACT_TOKENS if token not in r327_report]
    missing_r328_tokens = [token for token in R328_ARTIFACT_TOKENS if token not in r328_report]

    checks: list[dict[str, Any]] = []
    add_check(
        checks,
        "e4_tables_present_once",
        all(english.count(rf"\label{{{label}}}") == 1 for label in ENGLISH_LABELS)
        and all(chinese.count(rf"\label{{{label}}}") == 1 for label in CHINESE_LABELS)
        and "E4 replayability/cost main display" in english_tables_flat
        and "E4 deterministic-output main display" in english_tables_flat
        and "E4 replayability/cost 主显示" in chinese_tables_flat
        and "E4 deterministic-output 主显示" in chinese_tables_flat,
        "Both drafts expose the R327 cost table and R328 determinism table as E4 main displays.",
    )
    add_check(
        checks,
        "tables_live_inside_rq4_sections",
        all(table and table in english_section for table in english_tables)
        and all(table and table in chinese_section for table in chinese_tables),
        "All E4 main-display tables are located inside RQ4/E4 before related work or the dataset discussion.",
    )
    add_check(
        checks,
        "table_shapes_preserved",
        [table_row_count(table) for table in english_tables] == [4, 2]
        and [table_row_count(table) for table in chinese_tables] == [4, 2],
        (
            "English rows="
            f"{[table_row_count(table) for table in english_tables]}; "
            f"Chinese rows={[table_row_count(table) for table in chinese_tables]}."
        ),
    )
    add_check(
        checks,
        "table_numbers_preserved",
        not missing_en_table_tokens and not missing_zh_table_tokens,
        f"Missing English={missing_en_table_tokens}; missing Chinese={missing_zh_table_tokens}.",
    )
    add_check(
        checks,
        "section_numbers_preserved",
        not missing_en_section_tokens and not missing_zh_section_tokens,
        f"Missing English={missing_en_section_tokens}; missing Chinese={missing_zh_section_tokens}.",
    )
    add_check(
        checks,
        "source_artifacts_match_headline_numbers",
        not missing_r327_tokens
        and not missing_r328_tokens
        and "r300_views" in r327_summary
        and "r324_rank_features" in r327_summary
        and "r326_rank_feature_robustness" in r327_summary
        and "r300_views" in r328_summary
        and "r324_rank_features" in r328_summary
        and "r326_rank_feature_robustness" in r328_summary,
        f"Missing R327={missing_r327_tokens}; missing R328={missing_r328_tokens}.",
    )
    add_check(
        checks,
        "source_artifact_role_visible",
        "R327/R328 remain source artifacts rather than additional accuracy experiments" in english_section_flat
        and "R327/R328 是 source artifacts，不是新的 accuracy 实验" in chinese_section_flat,
        "R327/R328 are framed as provenance for E4 main displays, not additional accuracy experiments.",
    )
    add_check(
        checks,
        "non_claim_boundaries_visible",
        "not live eBPF overhead" in english_section_flat
        and "not human utility" in english_section_flat
        and "not complete ecosystem compatibility" in english_section_flat
        and "not a universal selector" in english_section_flat
        and "not empirical evidence" in english_section_flat
        and "not live eBPF overhead" in chinese_section_flat
        and "not human utility" in chinese_section_flat
        and "not complete ecosystem compatibility" in chinese_section_flat
        and "not universal selector" in chinese_section_flat
        and "不是新的 empirical evidence" in chinese_section_flat,
        "E4 keeps live overhead, human utility, ecosystem compatibility, selector, and empirical-accuracy non-claims visible.",
    )
    add_check(
        checks,
        "ledger_records_r389_as_focus_gate_when_present",
        RUN_ID not in evaluation or "E4 main-display gate" in evaluation,
        "If R389 is present in the ledger, it is a paper-focus gate, not a profiler experiment.",
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
            "RQ4/E4 presents R327/R328 as the replayability/cost and "
            "deterministic-output main displays for the artifact/reproducibility block."
        ),
        "checks": checks,
        "tables": {
            "english_row_counts": [table_row_count(table) for table in english_tables],
            "chinese_row_counts": [table_row_count(table) for table in chinese_tables],
            "required_section_tokens": REQUIRED_SECTION_TOKENS,
            "required_english_table_tokens": REQUIRED_ENGLISH_TABLE_TOKENS,
            "required_chinese_table_tokens": REQUIRED_CHINESE_TABLE_TOKENS,
        },
        "source_status": source_rows(),
    }


def write_outputs(report: dict[str, Any], out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "e4-main-display-report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    with (out_dir / "e4-main-display-checks.csv").open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["check", "passed", "detail"], lineterminator="\n")
        writer.writeheader()
        writer.writerows(report["checks"])
    lines = [
        f"# {RUN_ID} E4 Main-Display Gate",
        "",
        f"Status: **{report['status']}**",
        "",
        report["claim"],
        "",
        "## Table Shape",
        "",
        "| Paper | Replay/cost rows | Determinism rows |",
        "|---|---:|---:|",
        f"| English | {report['tables']['english_row_counts'][0]} | {report['tables']['english_row_counts'][1]} |",
        f"| Chinese | {report['tables']['chinese_row_counts'][0]} | {report['tables']['chinese_row_counts'][1]} |",
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
    (out_dir / "e4-main-display-report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
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
