#!/usr/bin/env python3
"""R390: novelty-positioning gate.

This paper-organization guardrail checks that the paper's novelty is scoped to
the operation/operation-stack profiler claim rather than to flamegraphs,
generic query-time aggregation, generic observability, failure localization by
itself, or trace-ecosystem compatibility. It reads current paper drafts and the
related-work map only; it does not fetch data, sync datasets, relabel traces,
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
DEFAULT_OUT_DIR = OUT_ROOT / "paper-novelty-positioning-r390"
RUN_ID = "R390"
SCRIPT_PATH = Path(__file__).resolve()
PAPER_SUBMODULE = ROOT / "docs" / "agentpprof-paper"
PAPER_SUBMODULE_PATH = "docs/agentpprof-paper"

SOURCES = {
    "English paper": PAPER_SUBMODULE / "main.tex",
    "Chinese paper": ROOT / "docs" / "visexp" / "paper" / "main.tex",
    "related-work map": ROOT / "docs" / "background-related-work.md",
    "idea story": ROOT / "docs" / "idea-story.md",
    "evaluation ledger": ROOT / "docs" / "evaluation.md",
}

ENGLISH_ABSTRACT_TOKENS = [
    "not merely a claim about query-time aggregation",
    "agent-operation record model",
    "recursive multi-field operation-stack projections",
    "hidden-label cross-dataset localization benchmark",
]

ENGLISH_RELATED_TOKENS = [
    "pprof can visualize labels as pseudo stack frames",
    "Perfetto generalizes trace ingestion and SQL analysis",
    "does not claim novelty for query-time aggregation alone",
    "OpenTelemetry GenAI and OpenInference",
    "LangSmith, Langfuse, and Phoenix",
    "AgentRx releases failed trajectories",
    "TELBench/DRIFT builds a deep-research span-localization benchmark",
    "AgentAtlas argues that outcome leaderboards miss trajectory",
    "future oracle/baseline candidates",
]

ENGLISH_CONCLUSION_TOKENS = [
    "not a new renderer, trace schema, or generic query engine",
    "agent-operation records",
    "recursive multi-field stack projections",
    "hidden-label profile-group scoring",
]

CHINESE_ABSTRACT_TOKENS = [
    "不是单纯的 query-time aggregation",
    "flamegraph renderer claim",
    "agent-operation record",
    "recursive multi-field operation-stack projection",
    "hidden-label profile-group scoring",
]

CHINESE_RELATED_TOKENS = [
    "pprof 不只是固定 call stack",
    "Perfetto 则代表系统 trace ingestion",
    "不能把 novelty 写成“只有我们支持 query-time aggregation”",
    "OpenTelemetry GenAI 和 OpenInference",
    "LangSmith、Langfuse、Phoenix 和 AgentOps",
    "AgentRx、TELBench/DRIFT、Holistic Evaluation and Failure Diagnosis 和 AgentAtlas",
    "不能把 novelty 写成 failure localization",
    "Novelty 边界",
]

CHINESE_CONCLUSION_TOKENS = [
    "新意不在单个 flamegraph",
    "不在通用 query-time aggregation",
    "trace schema 或 observability dashboard",
    "pprof、Perfetto、OpenTelemetry/OpenInference",
]

BACKGROUND_TOKENS = [
    "pprof already supports sample tags and tag-derived pseudo frames",
    "Perfetto already supports SQL/derived trace analysis",
    "AgentRx, TELBench/DRIFT, and Holistic Evaluation",
    "agent-operation record model, recursive multi-field operation-stack projection",
    "hidden-label evaluation of profile groups",
    "Overall same-claim risk: medium",
]

NON_CLAIM_TOKENS = [
    "human-productivity gains",
    "automatic discovery of all intent boundaries",
    "metric dominance",
    "complete compatibility",
    "不是 detector",
    "not a label-free automatic selector",
]

CORE_EXPERIMENT_TOKENS = [
    "three core empirical profiling experiments",
    "artifact/reproducibility block",
    "rather than a chronological run list",
    "The rest of the evaluation keeps this structure",
    "E2 is the single hidden-label localization/ranking experiment",
]

CHINESE_CORE_EXPERIMENT_TOKENS = [
    "三个核心经验性 profiling 实验",
    "artifact/reproducibility block",
    "不是论文的小节结构",
    "后续 evaluation 继续保持这个结构",
    "E2 是唯一的 hidden-label localization/ranking 主实验",
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


def normalized(text: str) -> str:
    return re.sub(r"\s+", " ", text)


def missing(tokens: list[str], text: str) -> list[str]:
    return [token for token in tokens if token not in text]


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
    background = read_text(SOURCES["related-work map"])
    idea_story = read_text(SOURCES["idea story"])
    evaluation = read_text(SOURCES["evaluation ledger"])
    script_text = read_text(SCRIPT_PATH)

    english_abstract = section_between(english, r"\\begin\{abstract\}", r"\\end\{abstract\}")
    english_related = section_between(english, r"\\section\{Related Work and Novelty\}", r"\\section\{Discussion\}")
    english_conclusion = section_between(english, r"\\section\{Conclusion\}", r"\\begin\{thebibliography\}")
    chinese_abstract = section_between(chinese, r"\\begin\{abstract\}", r"\\end\{abstract\}")
    chinese_related = section_between(chinese, r"\\section\{相关工作\}", r"\\section\{局限\}")
    chinese_conclusion = section_between(chinese, r"\\section\{结论\}", r"\\vspace")

    english_abstract_flat = normalized(english_abstract)
    english_related_flat = normalized(english_related)
    english_conclusion_flat = normalized(english_conclusion)
    chinese_abstract_flat = normalized(chinese_abstract)
    chinese_related_flat = normalized(chinese_related)
    chinese_conclusion_flat = normalized(chinese_conclusion)
    english_flat = normalized(english)
    chinese_flat = normalized(chinese)
    background_flat = normalized(background)
    full_paper_flat = normalized(english + "\n" + chinese)

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

    missing_en_abs = missing(ENGLISH_ABSTRACT_TOKENS, english_abstract_flat)
    missing_en_related = missing(ENGLISH_RELATED_TOKENS, english_related_flat)
    missing_en_conclusion = missing(ENGLISH_CONCLUSION_TOKENS, english_conclusion_flat)
    missing_zh_abs = missing(CHINESE_ABSTRACT_TOKENS, chinese_abstract_flat)
    missing_zh_related = missing(CHINESE_RELATED_TOKENS, chinese_related_flat)
    missing_zh_conclusion = missing(CHINESE_CONCLUSION_TOKENS, chinese_conclusion_flat)
    missing_background = missing(BACKGROUND_TOKENS, background_flat)

    checks: list[dict[str, Any]] = []
    add_check(
        checks,
        "english_abstract_scopes_novelty",
        not missing_en_abs,
        f"Missing English abstract tokens={missing_en_abs}.",
    )
    add_check(
        checks,
        "english_related_work_names_closest_threats",
        not missing_en_related,
        f"Missing English related-work tokens={missing_en_related}.",
    )
    add_check(
        checks,
        "english_conclusion_restates_scoped_novelty",
        not missing_en_conclusion,
        f"Missing English conclusion tokens={missing_en_conclusion}.",
    )
    add_check(
        checks,
        "chinese_abstract_scopes_novelty",
        not missing_zh_abs,
        f"Missing Chinese abstract tokens={missing_zh_abs}.",
    )
    add_check(
        checks,
        "chinese_related_work_names_closest_threats",
        not missing_zh_related,
        f"Missing Chinese related-work tokens={missing_zh_related}.",
    )
    add_check(
        checks,
        "chinese_conclusion_restates_scoped_novelty",
        not missing_zh_conclusion,
        f"Missing Chinese conclusion tokens={missing_zh_conclusion}.",
    )
    add_check(
        checks,
        "background_map_records_same_claim_risk",
        not missing_background,
        f"Missing background tokens={missing_background}.",
    )
    add_check(
        checks,
        "non_claim_boundaries_visible",
        all(token in full_paper_flat for token in NON_CLAIM_TOKENS),
        f"Missing non-claim tokens={missing(NON_CLAIM_TOKENS, full_paper_flat)}.",
    )
    add_check(
        checks,
        "core_experiment_structure_visible",
        not missing(CORE_EXPERIMENT_TOKENS, english_flat)
        and not missing(CHINESE_CORE_EXPERIMENT_TOKENS, chinese_flat),
        (
            "Missing English core-experiment tokens="
            f"{missing(CORE_EXPERIMENT_TOKENS, english_flat)}; "
            "missing Chinese core-experiment tokens="
            f"{missing(CHINESE_CORE_EXPERIMENT_TOKENS, chinese_flat)}."
        ),
    )
    add_check(
        checks,
        "idea_story_matches_scoped_claim",
        "not generic aggregation" in idea_story
        and "standard trace exchange are containers" in idea_story
        and "operation/operation-stack profiling gives a better inspection-work" in idea_story,
        "Idea story preserves non-generic novelty and scoped profiler claim.",
    )
    add_check(
        checks,
        "ledger_records_r390_as_focus_gate_when_present",
        RUN_ID not in evaluation
        or "Novelty-positioning and core-experiment organization gate" in evaluation,
        "If R390 is present in the ledger, it is a paper-focus gate, not a profiler experiment.",
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
            "The paper scopes novelty to agent-operation records, recursive "
            "operation-stack projections, and hidden-label profile-group scoring, "
            "not to flamegraphs, generic aggregation, generic observability, or "
            "failure localization by itself."
        ),
        "checks": checks,
        "source_status": source_rows(),
    }


def write_outputs(report: dict[str, Any], out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "novelty-positioning-report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    with (out_dir / "novelty-positioning-checks.csv").open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["check", "passed", "detail"], lineterminator="\n")
        writer.writeheader()
        writer.writerows(report["checks"])
    lines = [
        f"# {RUN_ID} Novelty-Positioning Gate",
        "",
        f"Status: **{report['status']}**",
        "",
        report["claim"],
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
    (out_dir / "novelty-positioning-report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
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
