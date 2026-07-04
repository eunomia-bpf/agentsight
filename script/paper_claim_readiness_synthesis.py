#!/usr/bin/env python3
"""R307: synthesize paper-readiness evidence after R300-R306.

This script does not fetch data or create new profiler abstractions. It reads
tracked experiment artifacts and updates the claim gate for the current paper
story: operations are the common record, operation stacks are the recursive
query, and trace/case/report artifacts are exchange or review surfaces. R303 is
listed explicitly because the paper cites the scripted agent-session exchange
reproducer as direct C1 evidence.
"""

from __future__ import annotations

import argparse
import html
import json
import subprocess
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OUT_ROOT = ROOT / "docs" / "visexp" / "out"
DEFAULT_OUT_DIR = OUT_ROOT / "paper-claim-readiness-r307"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    return parser.parse_args()


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def load_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as file:
        return json.load(file)


def require(data: dict[str, Any], key: str, path: Path) -> Any:
    if key not in data:
        raise SystemExit(f"{rel(path)} missing key {key!r}")
    return data[key]


def git_output(args: list[str]) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip()
        raise SystemExit(f"git {' '.join(args)} failed: {detail}")
    return result.stdout.strip()


def run_git_check(description: str, args: list[str], path: Path) -> None:
    result = subprocess.run(
        ["git", *args, "--", rel(path)],
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip()
        suffix = f": {detail}" if detail else ""
        raise SystemExit(f"{rel(path)} failed provenance check: {description}{suffix}")


def ensure_sources_tracked_clean(paths: list[Path]) -> None:
    for path in paths:
        if not path.exists():
            raise SystemExit(f"missing source artifact {rel(path)}")
        run_git_check("source artifact is not git-tracked", ["ls-files", "--error-unmatch"], path)
        run_git_check("source artifact has unstaged changes", ["diff", "--quiet"], path)
        run_git_check("source artifact has staged changes", ["diff", "--cached", "--quiet"], path)


def num(value: Any) -> int | float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise SystemExit(f"expected numeric value, got {value!r}")
    return value


def build_synthesis() -> dict[str, Any]:
    paths = {
        "r295_claim": OUT_ROOT / "paper-claim-synthesis-r295" / "claim-synthesis.json",
        "r298_value": OUT_ROOT / "paper-value-novelty-r298" / "value-novelty-synthesis.json",
        "r300_query": OUT_ROOT / "operation-query-utility-r300" / "query-utility-report.json",
        "r301_task": OUT_ROOT / "operation-analyst-task-r301" / "analyst-task-report.json",
        "r302_ranking": OUT_ROOT / "operation-analyst-ranking-r302" / "ranking-report.json",
        "r303_agent_session_exchange": OUT_ROOT
        / "agent-trace-exchange-r303"
        / "exchange-report.json",
        "r304_case": OUT_ROOT / "operation-case-study-r304" / "case-study-report.json",
        "r305_baseline": OUT_ROOT
        / "operation-case-baseline-r305"
        / "case-baseline-report.json",
        "r306_chrome": OUT_ROOT
        / "agent-trace-chrome-exchange-r306"
        / "chrome-exchange-report.json",
    }
    ensure_sources_tracked_clean(list(paths.values()))

    r295 = load_json(paths["r295_claim"])
    r298 = load_json(paths["r298_value"])
    r300 = load_json(paths["r300_query"])
    r301 = load_json(paths["r301_task"])
    r302 = load_json(paths["r302_ranking"])
    r303 = load_json(paths["r303_agent_session_exchange"])
    r304 = load_json(paths["r304_case"])
    r305 = load_json(paths["r305_baseline"])
    r306 = load_json(paths["r306_chrome"])

    heterogeneous = require(require(r295, "evidence", paths["r295_claim"]), "heterogeneous_coverage", paths["r295_claim"])
    r300_summary = require(r300, "summary", paths["r300_query"])
    r300_views = require(r300_summary, "views", paths["r300_query"])
    r300_comparisons = r300_summary
    r301_view_budget = require(require(r301, "summary", paths["r301_task"]), "view_budget_summary", paths["r301_task"])
    r302_summary = require(r302, "summary", paths["r302_ranking"])
    r302_medians = require(r302_summary, "medians", paths["r302_ranking"])
    r302_comparisons = require(r302_summary, "comparisons", paths["r302_ranking"])
    r304_summary = require(r304, "summary", paths["r304_case"])
    r305_summary = require(r305, "summary", paths["r305_baseline"])
    r305_by_view = require(r305_summary, "by_view", paths["r305_baseline"])
    r306_trace = require(r306, "chrome_trace", paths["r306_chrome"])

    task_count = len(require(r300, "tasks", paths["r300_query"]))
    operation_count = sum(num(task["operations"]) for task in r300["tasks"])
    old_readiness = require(r298, "paper_readiness", paths["r298_value"])

    decision_metrics = {
        "heterogeneous_sources": {
            "datasets": heterogeneous["supplemental_datasets"],
            "operations": heterogeneous["supplemental_operations"],
            "unique_stacks": heterogeneous["supplemental_unique_stacks"],
        },
        "trace_exchange": {
            "agent_session_schema": r303["trace_schema"],
            "agent_session_sessions": r303["sessions"],
            "agent_session_operations": r303["operations"],
            "agent_session_filesystem_portable": r303["trace_filesystem_portable"],
            "agent_session_folded_outputs_identical": r303["folded_outputs_identical"],
            "agent_session_trace_import_samples": r303["trace_import"]["samples"],
            "agent_session_trace_import_unique_stacks": r303["trace_import"][
                "unique_stacks"
            ],
            "agent_session_operation_import_samples": r303["operation_import"][
                "samples"
            ],
            "agent_session_operation_import_unique_stacks": r303["operation_import"][
                "unique_stacks"
            ],
            "chrome_events": r306_trace["events"],
            "direct_operations": r306["direct_operations"],
            "chrome_operations": r306["chrome_operations"],
            "direct_trace_equals_direct_operations": r306["direct_trace_equals_direct_operations"],
            "chrome_operations_equal_direct_operations": r306[
                "chrome_operations_equal_direct_operations"
            ],
            "direct_operations_byte_identical": r306["direct_operations_byte_identical"],
        },
        "analysis_task_suite": {
            "tasks": task_count,
            "operations": operation_count,
            "datasets": sorted({task["dataset"] for task in r300["tasks"]}),
            "problems": [task["problem"] for task in r300["tasks"]],
        },
        "r300_oracle_sorted": {
            "operation_stack_vs_flat_lift": r300_comparisons[
                "operation_stack_vs_flat"
            ]["median_top_positive_lift_ratio"],
            "operation_stack_vs_flat_inspection_fraction": r300_comparisons[
                "operation_stack_vs_flat"
            ]["median_inspection_fraction_ratio"],
            "operation_stack_vs_fixed_group_ratio": r300_comparisons[
                "operation_stack_vs_fixed_session"
            ]["median_group_count_ratio"],
            "operation_stack_vs_fixed_session_support": r300_comparisons[
                "operation_stack_vs_fixed_session"
            ]["median_top_group_session_ratio"],
            "operation_stack_inspection_fraction_for_50pct_positives": r300_views[
                "operation_stack"
            ]["median_inspection_fraction_for_50pct_positives"],
        },
        "r301_label_hidden_width": {
            "operation_stack_30pct_recall": r301_view_budget[
                "operation_stack:budget_30pct_operations"
            ]["median_positive_recall"],
            "operation_stack_30pct_groups": r301_view_budget[
                "operation_stack:budget_30pct_operations"
            ]["median_groups_inspected"],
            "fixed_session_30pct_recall": r301_view_budget[
                "fixed_session:budget_30pct_operations"
            ]["median_positive_recall"],
            "fixed_session_30pct_groups": r301_view_budget[
                "fixed_session:budget_30pct_operations"
            ]["median_groups_inspected"],
            "operation_stack_top10_recall": r301_view_budget[
                "operation_stack:top_10_groups"
            ]["median_positive_recall"],
            "fixed_session_top10_recall": r301_view_budget[
                "fixed_session:top_10_groups"
            ]["median_positive_recall"],
        },
        "r302_label_hidden_ranking": {
            "query_aware_top10_work": r302_medians[
                "operation_stack:query_aware:top_10_groups"
            ]["median_inspected_operation_fraction"],
            "query_aware_top10_lift": r302_medians[
                "operation_stack:query_aware:top_10_groups"
            ]["median_positive_lift"],
            "width_top10_work": r302_medians[
                "operation_stack:width:top_10_groups"
            ]["median_inspected_operation_fraction"],
            "width_top10_lift": r302_medians[
                "operation_stack:width:top_10_groups"
            ]["median_positive_lift"],
            "query_aware_budget30_recall": r302_medians[
                "operation_stack:query_aware:budget_30pct_operations"
            ]["median_positive_recall"],
            "width_budget30_recall": r302_medians[
                "operation_stack:width:budget_30pct_operations"
            ]["median_positive_recall"],
            "top10_work_ratio_vs_width": r302_comparisons[
                "operation_stack_query_aware_vs_width"
            ]["top_10_groups"]["median_inspected_operation_fraction_ratio"],
            "top10_lift_ratio_vs_width": r302_comparisons[
                "operation_stack_query_aware_vs_width"
            ]["top_10_groups"]["median_positive_lift_ratio"],
        },
        "r304_case_packet": {
            "case_groups": r304_summary["total_case_groups"],
            "median_work": r304_summary["median_inspected_operation_fraction"],
            "median_recall": r304_summary["median_positive_recall"],
            "median_lift": r304_summary["median_positive_lift"],
            "tasks_with_lift_ge_1": r304_summary["tasks_with_lift_ge_1"],
        },
        "r305_cross_view_case_baseline": {
            "flat_work": r305_by_view["flat"]["median_inspected_operation_fraction"],
            "flat_recall": r305_by_view["flat"]["median_positive_recall"],
            "fixed_work": r305_by_view["fixed_session"][
                "median_inspected_operation_fraction"
            ],
            "fixed_recall": r305_by_view["fixed_session"]["median_positive_recall"],
            "fixed_lift": r305_by_view["fixed_session"]["median_positive_lift"],
            "operation_stack_work": r305_by_view["operation_stack"][
                "median_inspected_operation_fraction"
            ],
            "operation_stack_recall": r305_by_view["operation_stack"][
                "median_positive_recall"
            ],
            "operation_stack_lift": r305_by_view["operation_stack"][
                "median_positive_lift"
            ],
            "operation_vs_fixed_recall_ratio": r305_summary[
                "operation_stack_vs_fixed_session"
            ]["median_positive_recall_ratio"],
            "operation_vs_fixed_lift_ratio": r305_summary[
                "operation_stack_vs_fixed_session"
            ]["median_positive_lift_ratio"],
            "operation_vs_fixed_work_ratio": r305_summary[
                "operation_stack_vs_fixed_session"
            ]["median_inspected_operation_fraction_ratio"],
            "operation_vs_flat_work_ratio": r305_summary["operation_stack_vs_flat"][
                "median_inspected_operation_fraction_ratio"
            ],
        },
    }

    claim_verdicts = [
        {
            "claim": "C1",
            "verdict": "supported",
            "current_supported_wording": (
                "AgentSight represents heterogeneous public agent trajectories and "
                "local agent-session traces as operations, then profiles them with "
                "user-selected operation stacks. Chrome Trace Event JSON is supported "
                "as an exchange container that imports back to operation JSONL."
            ),
            "evidence": [
                f"{decision_metrics['heterogeneous_sources']['datasets']} sampled public datasets / {decision_metrics['heterogeneous_sources']['operations']} operations",
                "R293 profile-spec replay and stack override",
                "R294 claim-gated exchange plus R303 scripted agent-session exchange with 1 session / 6 operations and folded equality",
                "R306 Chrome Trace Event JSON round trip with 6 samples / 5 stacks on all paths",
            ],
            "must_not_claim": [
                "all public agent datasets are fully converted at full scale",
                "Chrome/OpenTelemetry ecosystem compatibility is complete",
                "trace exchange is a third profiler abstraction",
            ],
            "maximal_plausible_wording": (
                "The operation/operation-stack model can serve as an interchange "
                "layer across common agent trace containers."
            ),
            "expansion_experiments": [
                "import one real OpenTelemetry GenAI span export or Perfetto trace from another agent tool and verify operation-stack parity",
                "run the trace bridge on a multi-session public trace bundle rather than a fixture",
            ],
        },
        {
            "claim": "C2",
            "verdict": "supported with scoped limits",
            "current_supported_wording": (
                "Recursive operation stacks recover useful task, phase, action, "
                "human-group, safety, and quality-label views on sampled labeled "
                "trajectories, and the same operations can be folded at different "
                "depths by changing stack fields."
            ),
            "evidence": [
                "R286 recursive depth sweep",
                "R290 OSWorld-Human grouped boundary evidence",
                "R291 AgentNet step-quality fields",
                "R299 boundary-family calibration",
            ],
            "must_not_claim": [
                "perfect intent recovery",
                "one universal stack depth",
                "unsupervised boundary discovery",
            ],
            "maximal_plausible_wording": (
                "Operation stacks are a general query-time boundary language for "
                "agent trajectories when adequate operation fields or learned field "
                "derivation are available."
            ),
            "expansion_experiments": [
                "calibrate the learned boundary backend on AgentNet step-quality boundaries",
                "compare learned operation-boundary fields against an LLM boundary-labeling baseline on one held-out family",
            ],
        },
        {
            "claim": "C3",
            "verdict": "partial",
            "current_supported_wording": (
                "Deterministic mappings and supervised boundary backends improve "
                "semantic aggregation by deriving operation fields before folding."
            ),
            "evidence": [
                "R282 held-out mapping",
                "R285 leave-dataset-out mapping",
                "R297 OSWorld-Human supervised boundary backend",
                "R299 family calibration with negative controls",
            ],
            "must_not_claim": [
                "field derivation is unsupervised",
                "one learned backend generalizes across all families",
                "AgentRewardBench looping requires learned boundaries when repeat_signal_change is sufficient",
            ],
            "maximal_plausible_wording": (
                "Field derivation is a reusable extension point that can host "
                "regex, learned, and model-backed mapping backends under one "
                "operation-stack contract."
            ),
            "expansion_experiments": [
                "add a calibrated learned backend on AgentNet and report precision/recall/error cases",
                "add one model-backed mapping baseline that writes ordinary operation fields and compare it with regex mappings",
            ],
        },
        {
            "claim": "C4",
            "verdict": "supported as automated proxy, not user utility",
            "current_supported_wording": (
                "On six oracle-backed analysis tasks over existing labeled operations, "
                "operation-stack views provide a useful inspectability tradeoff: they "
                "are far more selective than flat summaries and higher-recall than "
                "fixed-session case packets at the same top-k packet count, but they "
                "are not uniformly cheaper than fixed-session drilldown."
            ),
            "evidence": [
                f"R300 operation-stack vs flat lift {decision_metrics['r300_oracle_sorted']['operation_stack_vs_flat_lift']}x with inspection ratio {decision_metrics['r300_oracle_sorted']['operation_stack_vs_flat_inspection_fraction']}",
                f"R301 label-hidden 30% budget recall {decision_metrics['r301_label_hidden_width']['operation_stack_30pct_recall']} vs {decision_metrics['r301_label_hidden_width']['fixed_session_30pct_recall']}",
                f"R302 top-10 query-aware work {decision_metrics['r302_label_hidden_ranking']['query_aware_top10_work']} with lift {decision_metrics['r302_label_hidden_ranking']['query_aware_top10_lift']}",
                f"R305 operation-stack vs fixed-session recall ratio {decision_metrics['r305_cross_view_case_baseline']['operation_vs_fixed_recall_ratio']} and work ratio {decision_metrics['r305_cross_view_case_baseline']['operation_vs_fixed_work_ratio']}",
            ],
            "must_not_claim": [
                "human productivity improvement",
                "automatic anomaly detection",
                "operation stacks dominate fixed-session views on every work metric",
            ],
            "maximal_plausible_wording": (
                "Current evidence supports automated inspectability proxy metrics; "
                "human analyst accuracy or time improvement remains a hypothesis "
                "for the next controlled study."
            ),
            "expansion_experiments": [
                "run a controlled human/agent analyst study using R301/R302/R304/R305 visible packets and hidden answer keys",
                "measure answer accuracy, time-to-first-positive, inspected operations, and confidence for flat, fixed-session, and operation-stack packets",
            ],
        },
    ]

    paper_readiness = {
        "stage": "stage 6 claim gate / stage 9 paper integration",
        "mechanism_claim_level": "OSDI/NeurIPS-ready if scoped to sampled public trajectories and fixture-level exchange",
        "value_claim_level": "automated proxy only; needs analyst study for user-utility wording",
        "novelty_claims": require(r298, "novelty_claims", paths["r298_value"]),
        "must_not_claim": sorted(
            set(old_readiness["must_not_claim"])
            | {
                "R300-R305 prove human productivity",
                "R306 proves full OpenTelemetry/Chrome ecosystem compatibility",
                "case packets are a new profiler abstraction",
            }
        ),
        "next_gate": (
            "Use the existing R301/R302/R304/R305 visible packets and answer keys "
            "for a controlled analyst study before claiming user utility."
        ),
    }

    return {
        "schema": "agentsight.paper-claim-readiness.v1",
        "run_id": "R307",
        "commit": git_output(["rev-parse", "HEAD"]),
        "generated_from": {key: rel(path) for key, path in paths.items()},
        "decision_metrics": decision_metrics,
        "claim_verdicts": claim_verdicts,
        "paper_readiness": paper_readiness,
    }


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_markdown(path: Path, payload: dict[str, Any]) -> None:
    metrics = payload["decision_metrics"]
    lines = [
        "# Paper Claim Readiness R307",
        "",
        "R307 refreshes the paper claim gate after R300-R306, with R303 explicitly included for scripted agent-session exchange evidence. It uses tracked artifacts only and treats trace, case-packet, and synthesis files as exchange or review surfaces rather than profiler abstractions.",
        "",
        "## Headline",
        "",
        f"- Public-operation coverage: {metrics['heterogeneous_sources']['datasets']} datasets / {metrics['heterogeneous_sources']['operations']} operations.",
        f"- Analysis task suite: {metrics['analysis_task_suite']['tasks']} tasks / {metrics['analysis_task_suite']['operations']} operations.",
        f"- R303 agent-session exchange: {metrics['trace_exchange']['agent_session_sessions']} session / {metrics['trace_exchange']['agent_session_operations']} operations, folded equality `{metrics['trace_exchange']['agent_session_folded_outputs_identical']}`.",
        f"- R305 operation-stack case packets: work {metrics['r305_cross_view_case_baseline']['operation_stack_work']}, recall {metrics['r305_cross_view_case_baseline']['operation_stack_recall']}, lift {metrics['r305_cross_view_case_baseline']['operation_stack_lift']}.",
        f"- R305 vs fixed-session: recall ratio {metrics['r305_cross_view_case_baseline']['operation_vs_fixed_recall_ratio']}, lift ratio {metrics['r305_cross_view_case_baseline']['operation_vs_fixed_lift_ratio']}, work ratio {metrics['r305_cross_view_case_baseline']['operation_vs_fixed_work_ratio']}.",
        f"- R306 Chrome trace bridge: {metrics['trace_exchange']['chrome_events']} events, folded equality `{metrics['trace_exchange']['chrome_operations_equal_direct_operations']}`.",
        "",
        "## Claim Verdicts",
        "",
    ]
    for row in payload["claim_verdicts"]:
        lines.extend(
            [
                f"### {row['claim']} - {row['verdict']}",
                "",
                row["current_supported_wording"],
                "",
                "Evidence:",
            ]
        )
        lines.extend(f"- {item}" for item in row["evidence"])
        lines.append("")
        lines.append("Must not claim:")
        lines.extend(f"- {item}" for item in row["must_not_claim"])
        lines.append("")
        lines.append(f"Maximal plausible wording: {row['maximal_plausible_wording']}")
        lines.append("")
        lines.append("Expansion experiments:")
        lines.extend(f"- {item}" for item in row["expansion_experiments"])
        lines.append("")

    lines.extend(
        [
            "## Next Gate",
            "",
            payload["paper_readiness"]["next_gate"],
            "",
            "## Source Artifacts",
            "",
        ]
    )
    lines.extend(f"- `{key}`: `{path}`" for key, path in payload["generated_from"].items())
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_html(path: Path, payload: dict[str, Any]) -> None:
    rows = []
    for row in payload["claim_verdicts"]:
        rows.append(
            "<tr>"
            f"<th>{html.escape(row['claim'])}</th>"
            f"<td>{html.escape(row['verdict'])}</td>"
            f"<td>{html.escape(row['current_supported_wording'])}</td>"
            "</tr>"
        )
    path.write_text(
        """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Paper Claim Readiness R307</title>
  <style>
    body { font-family: system-ui, sans-serif; margin: 2rem; color: #1f2933; }
    h1 { font-size: 1.6rem; margin-bottom: 0.25rem; }
    p { max-width: 860px; line-height: 1.5; }
    table { border-collapse: collapse; margin-top: 1.5rem; max-width: 1100px; }
    th, td { border: 1px solid #d8dee9; padding: 0.55rem 0.75rem; text-align: left; vertical-align: top; }
    th { background: #f6f8fa; width: 90px; }
    code { background: #f6f8fa; padding: 0.1rem 0.25rem; border-radius: 4px; }
  </style>
</head>
<body>
  <h1>Paper Claim Readiness R307</h1>
  <p>
    R307 refreshes the claim gate after R300-R306. It keeps the profiler model
    to two abstractions: operations and operation stacks.
  </p>
  <table>
    <tr><th>Claim</th><th>Verdict</th><th>Supported wording</th></tr>
"""
        + "\n".join(rows)
        + """
  </table>
</body>
</html>
""",
        encoding="utf-8",
    )


def main() -> None:
    args = parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)
    payload = build_synthesis()

    json_path = args.out_dir / "paper-readiness-synthesis.json"
    md_path = args.out_dir / "paper-readiness-synthesis.md"
    html_path = args.out_dir / "index.html"
    run_result_path = args.out_dir / "run-result.json"

    payload["outputs"] = {
        "json": rel(json_path),
        "markdown": rel(md_path),
        "html": rel(html_path),
        "run_result": rel(run_result_path),
    }
    write_json(json_path, payload)
    write_markdown(md_path, payload)
    write_html(html_path, payload)
    write_json(
        run_result_path,
        {
            "run_id": payload["run_id"],
            "status": "ok",
            "json": rel(json_path),
            "markdown": rel(md_path),
            "html": rel(html_path),
            "claims": len(payload["claim_verdicts"]),
        },
    )
    print(json.dumps(load_json(run_result_path), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
