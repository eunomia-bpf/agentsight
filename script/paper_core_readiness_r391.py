#!/usr/bin/env python3
"""R391: core evaluation readiness gate.

This paper-organization gate checks that the current draft reads as a
top-conference profiling evaluation: three empirical profiling experiments
plus one artifact/reproducibility block. It reads current paper text and
tracked gate outputs only. It does not fetch data, sync datasets, relabel
traces, rerun the profiler, or create a new empirical result.
"""

from __future__ import annotations

import argparse
import ast
import csv
import json
import re
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OUT_ROOT = ROOT / "docs" / "visexp" / "out"
DEFAULT_OUT_DIR = OUT_ROOT / "paper-core-readiness-r391"
RUN_ID = "R391"
SCRIPT_PATH = Path(__file__).resolve()

ENGLISH_PAPER = ROOT / "docs" / "agentpprof-paper" / "main.tex"
CHINESE_PAPER = ROOT / "docs" / "visexp" / "paper" / "main.tex"
EVALUATION = ROOT / "docs" / "evaluation.md"

PREREQ_GATES = {
    "R386": OUT_ROOT / "paper-e1-main-display-r386" / "run-result.json",
    "R387": OUT_ROOT / "paper-e2-main-display-r387" / "run-result.json",
    "R388": OUT_ROOT / "paper-e3-main-display-r388" / "run-result.json",
    "R389": OUT_ROOT / "paper-e4-main-display-r389" / "run-result.json",
    "R390": OUT_ROOT / "paper-novelty-positioning-r390" / "run-result.json",
}


BLOCKS = [
    {
        "block": "RQ1/E1",
        "role": "Representation validity and recursive folding",
        "success": "One operation layer covers heterogeneous traces and folds at multiple depths.",
        "failure": "Narrow the abstraction claim or require additional operation-field derivation.",
        "english_tokens": [
            "Experiment contract: claim, the operation/operation stack model covers",
            "Claim-test: RQ1/E1 asks whether one operation layer can be folded recursively",
            "15 public labeled trace families / 47,590 operations",
            "Recursive stack choice",
            "Field derivation before folding",
            "Human-boundary folding",
            "not automatic recovery of all latent intent boundaries",
        ],
        "chinese_tokens": [
            "实验契约：RQ1/E1 的 claim 是两抽象模型能覆盖异构 agent traces",
            "Claim-test：RQ1/E1 问的是",
            "15 个 public labeled trace families / 47,590 operations",
            "递归 stack choice",
            "先派生 fields 再折叠",
            "Human-boundary folding",
            "不是自动恢复所有 latent intent boundary",
        ],
    },
    {
        "block": "RQ2/E2",
        "role": "Primary hidden-label localization and baseline tradeoff",
        "success": "Hot groups match hidden positives with lower flat work and better fixed-session fragmentation tradeoff.",
        "failure": "Narrow to the metrics/tasks where the Pareto condition holds.",
        "english_tokens": [
            "Experiment contract: claim, operation-stack profiling localizes and ranks real",
            "Claim-test: RQ2/E2 asks whether hot stacks and top-ranked groups correspond to hidden positives",
            "precision@k",
            "AUPRC-style AP",
            "nDCG",
            "work-to-first-positive",
            "flat:width",
            "fixed-session:query-aware",
            "dataset-native:query-aware",
            "operation-stack:query-aware",
            "Pareto claim, not universal dominance",
        ],
        "chinese_tokens": [
            "实验契约：RQ2/E2 的 claim 是 operation-stack profiling 能在真实 labeled traces 上 faithful localization 和 ranking",
            "Claim-test：RQ2/E2 问的是",
            "precision@k",
            "AUPRC-style AP",
            "nDCG",
            "work-to-first-positive",
            "flat:width",
            "fixed-session:query-aware",
            "dataset-native:query-aware",
            "operation-stack:query-aware",
            "不是对所有 trace-tree-shaped objectives 的 dominance",
        ],
    },
    {
        "block": "RQ3/E3",
        "role": "Mechanism isolation and profile-configuration actionability",
        "success": "Mechanism ablations and executable profile-spec patches expose concrete tuning actions.",
        "failure": "Keep only descriptive localization and remove actionability wording.",
        "english_tokens": [
            "Experiment contract: claim, the profiler exposes actionable knobs",
            "Claim-test: RQ3/E3 asks which mechanisms explain the localization gains",
            "Hidden labels are used only after profiling",
            "Executable profile-spec patches improve 5/6 tasks",
            "median AP delta 0.0376",
            "boundary-derived fields",
            "not an automatic selector or boundary detector",
        ],
        "chinese_tokens": [
            "实验契约：RQ3/E3 的 claim 是 profiler 通过 stack fields",
            "Claim-test：RQ3/E3 问的是",
            "Hidden labels 只在 profiling 之后用于 scoring",
            "Executable profile-spec patches",
            "median AP delta 为 0.0376",
            "boundary-derived fields",
            "不是自动 learned ranker",
        ],
    },
    {
        "block": "RQ4/E4",
        "role": "Replayability, cost, and claim hygiene",
        "success": "Tracked profile specs replay deterministically and paper claims stay scoped.",
        "failure": "Treat the artifact as exploratory and remove reproducibility wording.",
        "english_tokens": [
            "RQ4/E4 checks replayability, offline cost, and artifact hygiene",
            "Experiment contract: claim, the offline profiler path is replayable",
            "76 tracked profile specs",
            "152 invocations",
            "76/76 semantic and 76/76 raw-byte deterministic",
            "not a hidden-label accuracy result",
            "or analyst productivity",
        ],
        "chinese_tokens": [
            "RQ4/E4 则验证 replayability、offline cost 和 artifact hygiene",
            "实验契约：RQ4/E4 的 claim 是 offline profiler path 可以在 tracked inputs 上低成本 replay",
            "76 个 profile specs",
            "152 次 profiler invocations",
            "76/76",
            "不是新的 empirical evidence",
            "not human utility",
        ],
    },
]


GLOBAL_TOKENS = [
    "three core empirical profiling experiments",
    "rather than a chronological run list",
    "reviewer-facing evidence path",
    "E2 is the only primary hidden-label accuracy and baseline tradeoff comparison",
    "paper claim would narrow rather than adding another R-numbered result",
    "三个核心经验性 profiling 实验",
    "不是论文的小节结构",
    "Reviewer 应该沿着这条 evidence path",
    "E2 是唯一的 hidden-label accuracy 与 baseline tradeoff 主比较",
    "本文应该收窄 claim，而不是再增加一个 R 编号结果",
]

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    return parser.parse_args()


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def normalized(text: str) -> str:
    return re.sub(r"\s+", " ", text)


def missing(tokens: list[str], text: str) -> list[str]:
    return [token for token in tokens if token not in text]


def add_check(checks: list[dict[str, Any]], name: str, passed: bool, detail: str) -> None:
    checks.append({"check": name, "passed": bool(passed), "detail": detail})


def prereq_gate_statuses() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for run_id, path in PREREQ_GATES.items():
        if not path.exists():
            rows.append({"run_id": run_id, "path": rel(path), "status": "missing"})
            continue
        data = json.loads(read_text(path))
        rows.append({"run_id": run_id, "path": rel(path), "status": str(data.get("status", ""))})
    return rows


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return str(path.resolve())


def script_runtime_risk(script_text: str) -> list[str]:
    hits: list[str] = []
    tree = ast.parse(script_text)
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            names = [alias.name for alias in getattr(node, "names", [])]
            module = getattr(node, "module", "") or ""
            for name in [module, *names]:
                if name in {"subprocess", "requests", "urllib.request", "datasets", "huggingface_hub"}:
                    hits.append(f"import:{name}")
        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Attribute) and func.attr in {"system", "popen"}:
                hits.append(f"call:{func.attr}")
            if isinstance(func, ast.Name) and func.id in {"system", "popen"}:
                hits.append(f"call:{func.id}")
    return sorted(set(hits))


def build_report() -> dict[str, Any]:
    english = normalized(read_text(ENGLISH_PAPER))
    chinese = normalized(read_text(CHINESE_PAPER))
    evaluation = normalized(read_text(EVALUATION))
    script_text = read_text(SCRIPT_PATH)

    checks: list[dict[str, Any]] = []
    block_rows: list[dict[str, Any]] = []

    missing_global = missing(GLOBAL_TOKENS, english + "\n" + chinese)
    add_check(
        checks,
        "reviewer_evidence_path_visible",
        not missing_global,
        f"Missing global evidence-path tokens={missing_global}.",
    )

    for block in BLOCKS:
        missing_en = missing(block["english_tokens"], english)
        missing_zh = missing(block["chinese_tokens"], chinese)
        passed = not missing_en and not missing_zh
        add_check(
            checks,
            f"{block['block'].lower().replace('/', '_')}_contract_complete",
            passed,
            f"Missing English tokens={missing_en}; missing Chinese tokens={missing_zh}.",
        )
        block_rows.append(
            {
                "block": block["block"],
                "role": block["role"],
                "success_criterion": block["success"],
                "failure_interpretation": block["failure"],
                "paper_ready": "yes" if passed else "no",
            }
        )

    prereq_rows = prereq_gate_statuses()
    missing_gates = [row for row in prereq_rows if row["status"] != "pass"]
    add_check(
        checks,
        "prereq_display_and_novelty_gates_pass",
        not missing_gates,
        f"Non-pass prerequisite gates={missing_gates}.",
    )

    ledger_token = (
        "Core evaluation readiness gate over RQ1/E1-RQ4/E4 reviewer evidence path"
    )
    add_check(
        checks,
        "ledger_records_r391_when_present",
        RUN_ID not in evaluation or ledger_token in evaluation,
        "If R391 is present in the ledger, it is recorded as core evaluation readiness.",
    )

    runtime_hits = script_runtime_risk(script_text)
    add_check(
        checks,
        "no_data_sync_or_profiler_rerun",
        not runtime_hits,
        f"Forbidden imports or runtime calls={runtime_hits}.",
    )

    status = "pass" if all(row["passed"] for row in checks) else "fail"
    return {
        "run_id": RUN_ID,
        "status": status,
        "claim": (
            "The current evaluation is organized as three empirical profiling "
            "experiments plus one artifact/reproducibility block, with each block "
            "carrying a reviewer-facing success criterion and failure narrowing rule."
        ),
        "checks": checks,
        "blocks": block_rows,
        "prerequisite_gates": prereq_rows,
        "sources": [
            rel(ENGLISH_PAPER),
            rel(CHINESE_PAPER),
            rel(EVALUATION),
            *[rel(path) for path in PREREQ_GATES.values()],
        ],
    }


def write_outputs(report: dict[str, Any], out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "core-readiness-report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    with (out_dir / "core-readiness-checks.csv").open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["check", "passed", "detail"], lineterminator="\n")
        writer.writeheader()
        writer.writerows(report["checks"])

    with (out_dir / "core-readiness-blocks.csv").open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "block",
                "role",
                "success_criterion",
                "failure_interpretation",
                "paper_ready",
            ],
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(report["blocks"])

    lines = [
        "# R391 Core Evaluation Readiness Gate",
        "",
        f"Status: **{report['status']}**",
        "",
        report["claim"],
        "",
        "## Blocks",
        "",
        "| Block | Role | Success Criterion | Failure Interpretation | Ready |",
        "|---|---|---|---|---:|",
    ]
    for row in report["blocks"]:
        lines.append(
            "| {block} | {role} | {success_criterion} | {failure_interpretation} | {paper_ready} |".format(
                **row
            )
        )
    lines.extend(["", "## Checks", "", "| Check | Passed | Detail |", "|---|---:|---|"])
    for row in report["checks"]:
        lines.append(f"| {row['check']} | {row['passed']} | {row['detail']} |")
    lines.extend(["", "## Prerequisite Gates", "", "| Run | Status | Path |", "|---|---:|---|"])
    for row in report["prerequisite_gates"]:
        lines.append(f"| {row['run_id']} | {row['status']} | `{row['path']}` |")
    (out_dir / "core-readiness-report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    (out_dir / "run-result.json").write_text(
        json.dumps(
            {
                "out_dir": rel(out_dir),
                "run_id": RUN_ID,
                "script": rel(SCRIPT_PATH),
                "status": report["status"],
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )


def main() -> int:
    args = parse_args()
    report = build_report()
    write_outputs(report, args.out_dir)
    print(json.dumps({"out_dir": rel(args.out_dir), "run_id": RUN_ID, "status": report["status"]}))
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
