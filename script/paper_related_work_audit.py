#!/usr/bin/env python3
"""R314: audit related-work novelty and baseline grounding.

R314 does not fetch datasets or rerun profilers. It reads the current related
work ledger, the Chinese draft, the evaluation ledger, and the tracked R313
frontier artifact. The audit asks whether the paper now makes the nearest
same-claim threats explicit: LLM observability trace trees, OpenTelemetry-style
semantic conventions, classic flamegraph/pprof stacks, and public agent
trajectory benchmarks.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import html
import json
import re
import subprocess
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OUT_ROOT = ROOT / "docs" / "visexp" / "out"
DEFAULT_OUT_DIR = OUT_ROOT / "paper-related-work-audit-r314"
SOURCE_PATHS = {
    "related_work": ROOT / "docs" / "background-related-work.md",
    "paper_main_tex": ROOT / "docs" / "visexp" / "paper" / "main.tex",
    "claim_ledger": ROOT / "docs" / "visexp" / "paper" / "evaluation-claims-setup.zh-CN.md",
    "evaluation": ROOT / "docs" / "evaluation.md",
    "r313_frontier": OUT_ROOT
    / "operation-view-frontier-r313"
    / "view-frontier-report.json",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    return parser.parse_args()


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def load_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as file:
        return json.load(file)


def git_output(args: list[str]) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip()
        raise SystemExit(f"git {' '.join(args)} failed: {detail}")
    return result.stdout.strip()


def git_check(description: str, args: list[str], path: Path) -> None:
    result = subprocess.run(
        ["git", *args, "--", rel(path)],
        cwd=ROOT,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip()
        suffix = f": {detail}" if detail else ""
        raise SystemExit(f"{rel(path)} failed source check: {description}{suffix}")


def ensure_tracked(path: Path) -> None:
    if not path.exists():
        raise SystemExit(f"missing source file {rel(path)}")
    git_check("source file is not git-tracked", ["ls-files", "--error-unmatch"], path)


def ensure_tracked_clean(path: Path) -> None:
    ensure_tracked(path)
    git_check("source artifact has unstaged changes", ["diff", "--quiet"], path)
    git_check("source artifact has staged changes", ["diff", "--cached", "--quiet"], path)


def text_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def line_hits(text: str, pattern: str) -> list[int]:
    regex = re.compile(pattern, re.IGNORECASE)
    return [index for index, line in enumerate(text.splitlines(), start=1) if regex.search(line)]


def group_status(rows: list[dict[str, Any]]) -> str:
    statuses = {row["status"] for row in rows}
    if "fail" in statuses:
        return "fail"
    if "warn" in statuses:
        return "warn"
    return "pass"


def format_hits(hits: list[int], limit: int = 12) -> str:
    if not hits:
        return "missing"
    shown = ", ".join(map(str, hits[:limit]))
    if len(hits) > limit:
        shown += f", ... ({len(hits)} total)"
    return shown


def keyword_checks(
    text: str, items: list[tuple[str, str, str]], min_hits: int = 1
) -> list[dict[str, Any]]:
    rows = []
    for key, pattern, reason in items:
        hits = line_hits(text, pattern)
        rows.append(
            {
                "key": key,
                "pattern": pattern,
                "reason": reason,
                "hits": hits,
                "status": "pass" if len(hits) >= min_hits else "fail",
            }
        )
    return rows


def closest_work_checks(text: str) -> list[dict[str, Any]]:
    return keyword_checks(
        text,
        [
            (
                "classic_flamegraph_pprof",
                r"Flame Graph|flamegraph|pprof|folded",
                "Classic profilers are the fixed-call-stack baseline for folded stacks.",
            ),
            (
                "opentelemetry_genai",
                r"OpenTelemetry|GenAI semantic conventions",
                "OpenTelemetry-style GenAI semantic conventions are the trace-schema threat.",
            ),
            (
                "openinference",
                r"OpenInference",
                "OpenInference is a current AI-observability semantic convention for spans.",
            ),
            (
                "langsmith",
                r"LangSmith",
                "LangSmith is a production LLM observability and evaluation platform.",
            ),
            (
                "langfuse",
                r"Langfuse",
                "Langfuse is an open LLM tracing, eval, and prompt-management platform.",
            ),
            (
                "phoenix",
                r"Phoenix|Arize",
                "Phoenix is an OpenTelemetry/OpenInference-based tracing/eval platform.",
            ),
            (
                "agentops",
                r"AgentOps",
                "AgentOps is the closest agent-specific observability taxonomy/tooling threat.",
            ),
            (
                "public_labeled_trajectories",
                r"OSWorld-Human|AgentNet|AgentRewardBench|SATraj-OS|WebLINX|ToolBench|tau-bench",
                "The paper must distinguish itself from benchmarks that provide labeled trajectories.",
            ),
        ],
    )


def novelty_delta_checks(text: str) -> list[dict[str, Any]]:
    return keyword_checks(
        text,
        [
            (
                "two_objects_only",
                r"operation.*operation stack|operation stack.*operation|两个核心抽象|two-object",
                "Novelty must stay on the two-abstraction model.",
            ),
            (
                "query_time_projection",
                r"query-time|用户选择|递归折叠|stack 深度|stack depth|view/ranker",
                "The paper must say stacks are selected at query time, not fixed at capture time.",
            ),
            (
                "trace_tree_is_baseline",
                r"trace tree|span tree|fixed trace|固定.*trace|固定.*span",
                "LLM tracing systems should map to a fixed trace/span-tree baseline.",
            ),
            (
                "public_dataset_use_not_benchmark",
                r"不提出新 benchmark|not.*new benchmark|真实标注轨迹|public labeled",
                "The paper should use public labels as evidence rather than claim a new benchmark.",
            ),
            (
                "non_flamegraph_views",
                r"frontier|Pareto|case packet|quality|safety|boundary|transition",
                "The paper must show the profiler is not only a flamegraph renderer.",
            ),
        ],
    )


def baseline_checks(text: str) -> list[dict[str, Any]]:
    return keyword_checks(
        text,
        [
            (
                "dataset_native_sequence",
                r"Dataset-native sequence|dataset-native|原生.*sequence",
                "Reviewers will expect a comparison against the benchmark's native sequence view.",
            ),
            (
                "flat_action_summary",
                r"Flat action|flat summary|flat",
                "Flat counting is the simplest aggregation baseline.",
            ),
            (
                "fixed_session_stack",
                r"fixed prompt/session|fixed-session|固定 session|demo/session",
                "Fixed session or demo stacks test whether operation stacks add value.",
            ),
            (
                "fixed_trace_span_tree",
                r"span/trace|trace/span|trace tree|span tree",
                "LLM observability systems motivate a trace-tree baseline.",
            ),
            (
                "frontier_counterpoints",
                r"flat.*fixed-session|fixed-session.*flat|frontier counterpoint|Pareto frontier",
                "R313 should preserve counterpoints instead of claiming dominance.",
            ),
        ],
    )


def guardrail_checks(text: str) -> list[dict[str, Any]]:
    guards = [
        (
            "not_trace_ecosystem_compatibility",
            r"不证明完整.*OpenTelemetry|不证明完整.*Perfetto|not.*trace-ecosystem|完整.*生态兼容",
        ),
        (
            "not_human_utility",
            r"不是 human study|不能.*开发者|不能.*human utility|not.*human study|not.*productivity",
        ),
        (
            "not_single_view_dominance",
            r"不是唯一最优|不能.*dominance|not.*dominance|counterpoint",
        ),
        (
            "not_universal_detector",
            r"不能.*detector|不是.*detector|not.*detector|无监督.*不",
        ),
    ]
    rows = []
    for key, pattern in guards:
        hits = line_hits(text, pattern)
        rows.append(
            {
                "key": key,
                "pattern": pattern,
                "hits": hits,
                "status": "pass" if hits else "fail",
            }
        )
    return rows


def r313_alignment_checks(text: str, r313: dict[str, Any]) -> list[dict[str, Any]]:
    summary = r313["summary"]
    checks = [
        ("tasks", str(summary["tasks"])),
        ("datasets", str(summary["datasets"])),
        ("operations", f"{summary['operations']:,}"),
        ("positive_operations", f"{summary['positive_operations']:,}"),
        ("candidate_points", str(summary["candidate_points"])),
        ("operation_stack_on_frontier", summary["operation_stack_on_frontier"]),
        ("operation_stack_best_lift", summary["operation_stack_best_lift"]),
        (
            "operation_stack_best_recall_under_30pct_work",
            summary["operation_stack_best_recall_under_30pct_work"],
        ),
        ("flat_on_frontier", summary["flat_on_frontier"]),
        ("fixed_session_on_frontier", summary["fixed_session_on_frontier"]),
    ]
    rows = []
    for key, needle in checks:
        hits = line_hits(text, re.escape(str(needle)))
        rows.append(
            {
                "key": key,
                "expected_text": needle,
                "hits": hits,
                "status": "pass" if hits else "fail",
            }
        )
    return rows


def build_payload() -> dict[str, Any]:
    for key in ["related_work", "paper_main_tex", "claim_ledger", "evaluation"]:
        ensure_tracked(SOURCE_PATHS[key])
    ensure_tracked_clean(SOURCE_PATHS["r313_frontier"])

    related_text = SOURCE_PATHS["related_work"].read_text(encoding="utf-8")
    paper_text = SOURCE_PATHS["paper_main_tex"].read_text(encoding="utf-8")
    claim_text = SOURCE_PATHS["claim_ledger"].read_text(encoding="utf-8")
    evaluation_text = SOURCE_PATHS["evaluation"].read_text(encoding="utf-8")
    r313 = load_json(SOURCE_PATHS["r313_frontier"])
    combined = "\n".join([related_text, paper_text, claim_text, evaluation_text])

    closest_rows = closest_work_checks(combined)
    novelty_rows = novelty_delta_checks(combined)
    baseline_rows = baseline_checks(combined)
    guardrail_rows = guardrail_checks(combined)
    r313_rows = r313_alignment_checks(combined, r313)

    sections = {
        "closest_work_coverage": group_status(closest_rows),
        "novelty_delta": group_status(novelty_rows),
        "baseline_grounding": group_status(baseline_rows),
        "guardrails": group_status(guardrail_rows),
        "r313_alignment": group_status(r313_rows),
    }
    overall = "scoped_related_work_ready" if all(value == "pass" for value in sections.values()) else "needs_work"

    return {
        "schema": "agentsight.paper-related-work-audit.v1",
        "run_id": "R314",
        "commit": git_output(["rev-parse", "HEAD"]),
        "input_policy": {
            "dataset_sync": "none",
            "profiler_rerun": "none",
            "source_artifacts": {key: rel(path) for key, path in SOURCE_PATHS.items()},
            "purpose": "related-work novelty and baseline audit over current docs and paper",
        },
        "profiler_abstractions": ["operation", "operation stack"],
        "document_hashes": {
            "related_work": text_hash(related_text),
            "paper_main_tex": text_hash(paper_text),
            "claim_ledger": text_hash(claim_text),
            "evaluation": text_hash(evaluation_text),
        },
        "closest_work_checks": closest_rows,
        "novelty_delta_checks": novelty_rows,
        "baseline_checks": baseline_rows,
        "guardrail_checks": guardrail_rows,
        "r313_alignment_checks": r313_rows,
        "summary": {
            "overall": overall,
            "sections": sections,
            "position": (
                "The paper is grounded against current trace-tree observability systems, "
                "classic folded-stack profilers, and public labeled agent-trajectory "
                "benchmarks, while preserving the scoped R313 inspectability-tradeoff claim."
            ),
            "r313_frontier_summary": r313["summary"],
        },
    }


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_markdown(path: Path, payload: dict[str, Any]) -> None:
    summary = payload["summary"]
    lines = [
        "# Paper Related Work Audit R314",
        "",
        "R314 audits the current related-work and baseline grounding. It does not sync datasets or rerun profilers.",
        "",
        "## Summary",
        "",
        f"- Overall: {summary['overall']}.",
        f"- Closest-work coverage: {summary['sections']['closest_work_coverage']}.",
        f"- Novelty delta: {summary['sections']['novelty_delta']}.",
        f"- Baseline grounding: {summary['sections']['baseline_grounding']}.",
        f"- Guardrails: {summary['sections']['guardrails']}.",
        f"- R313 alignment: {summary['sections']['r313_alignment']}.",
        f"- Position: {summary['position']}",
        "",
        "## Closest Work Coverage",
        "",
        "| Key | Status | Lines | Reason |",
        "|---|---|---|---|",
    ]
    for row in payload["closest_work_checks"]:
        lines.append(
            f"| {row['key']} | {row['status']} | {format_hits(row['hits'])} | {row['reason']} |"
        )
    lines.extend(
        [
            "",
            "## Baseline Grounding",
            "",
            "| Key | Status | Lines | Reason |",
            "|---|---|---|---|",
        ]
    )
    for row in payload["baseline_checks"]:
        lines.append(
            f"| {row['key']} | {row['status']} | {format_hits(row['hits'])} | {row['reason']} |"
        )
    lines.extend(
        [
            "",
            "## R313 Alignment",
            "",
            "| Key | Expected text | Status | Lines |",
            "|---|---|---|---|",
        ]
    )
    for row in payload["r313_alignment_checks"]:
        lines.append(
            f"| {row['key']} | {row['expected_text']} | {row['status']} | {format_hits(row['hits'])} |"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_csv(path: Path, payload: dict[str, Any]) -> None:
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=["category", "key", "status", "detail"],
            lineterminator="\n",
        )
        writer.writeheader()
        for category, rows in [
            ("closest_work", payload["closest_work_checks"]),
            ("novelty_delta", payload["novelty_delta_checks"]),
            ("baseline", payload["baseline_checks"]),
            ("guardrail", payload["guardrail_checks"]),
            ("r313_alignment", payload["r313_alignment_checks"]),
        ]:
            for row in rows:
                detail = row.get("reason") or row.get("expected_text") or row.get("pattern")
                writer.writerow(
                    {
                        "category": category,
                        "key": row["key"],
                        "status": row["status"],
                        "detail": detail,
                    }
                )


def write_html(path: Path, payload: dict[str, Any]) -> None:
    def table(rows: list[dict[str, Any]], detail_key: str) -> str:
        body = []
        for row in rows:
            detail = row.get(detail_key, "")
            body.append(
                "<tr>"
                f"<th>{html.escape(row['key'])}</th>"
                f"<td>{html.escape(row['status'])}</td>"
                f"<td>{html.escape(format_hits(row['hits']))}</td>"
                f"<td>{html.escape(str(detail))}</td>"
                "</tr>"
            )
        return "\n".join(body)

    summary = payload["summary"]
    path.write_text(
        """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Paper Related Work Audit R314</title>
  <style>
    body { font-family: system-ui, sans-serif; margin: 2rem; color: #1f2933; }
    h1 { font-size: 1.6rem; margin-bottom: 0.25rem; }
    table { border-collapse: collapse; margin-top: 1rem; max-width: 1180px; }
    th, td { border: 1px solid #d8dee9; padding: 0.55rem 0.75rem; text-align: left; vertical-align: top; }
    th { background: #f6f8fa; }
  </style>
</head>
<body>
  <h1>Paper Related Work Audit R314</h1>
"""
        + f"  <p>Overall: {html.escape(summary['overall'])}. {html.escape(summary['position'])}</p>\n"
        + "  <h2>Closest Work</h2>\n"
        + "  <table><tr><th>Key</th><th>Status</th><th>Lines</th><th>Reason</th></tr>\n"
        + table(payload["closest_work_checks"], "reason")
        + "\n  </table>\n  <h2>Baselines</h2>\n"
        + "  <table><tr><th>Key</th><th>Status</th><th>Lines</th><th>Reason</th></tr>\n"
        + table(payload["baseline_checks"], "reason")
        + "\n  </table>\n</body>\n</html>\n",
        encoding="utf-8",
    )


def main() -> None:
    args = parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)
    payload = build_payload()

    json_path = args.out_dir / "related-work-audit.json"
    md_path = args.out_dir / "related-work-audit.md"
    csv_path = args.out_dir / "related-work-audit.csv"
    html_path = args.out_dir / "index.html"
    run_result_path = args.out_dir / "run-result.json"

    payload["outputs"] = {
        "json": rel(json_path),
        "markdown": rel(md_path),
        "csv": rel(csv_path),
        "html": rel(html_path),
        "run_result": rel(run_result_path),
    }
    write_json(json_path, payload)
    write_markdown(md_path, payload)
    write_csv(csv_path, payload)
    write_html(html_path, payload)
    write_json(
        run_result_path,
        {
            "run_id": payload["run_id"],
            "status": "ok",
            "overall": payload["summary"]["overall"],
            "sections": payload["summary"]["sections"],
            "json": rel(json_path),
            "markdown": rel(md_path),
            "csv": rel(csv_path),
            "html": rel(html_path),
        },
    )
    print(json.dumps(load_json(run_result_path), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
