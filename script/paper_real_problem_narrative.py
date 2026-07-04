#!/usr/bin/env python3
"""R317: synthesize claim-first real-problem conclusions for the paper.

This script does not fetch datasets, rerun profilers, or execute a human/agent
study. It reads tracked synthesis artifacts over already-labeled public agent
trajectories and produces a reviewer-facing narrative matrix: what real problem
each task represents, where operation stacks help, what counterpoint remains,
and what the paper may safely claim.
"""

from __future__ import annotations

import argparse
import csv
import html
import json
import math
import subprocess
from pathlib import Path
from statistics import median
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OUT_ROOT = ROOT / "docs" / "visexp" / "out"
DEFAULT_OUT_DIR = OUT_ROOT / "paper-real-problem-narrative-r317"

SOURCE_PATHS = {
    "problem_value": OUT_ROOT / "operation-problem-value-r309" / "problem-value-report.json",
    "view_frontier": OUT_ROOT / "operation-view-frontier-r313" / "view-frontier-report.json",
    "analyst_readout": OUT_ROOT / "analyst-study-readout-r316" / "readout-report.json",
}

TASK_TAKEAWAYS = {
    "agentnet_incorrect_step": {
        "paper_value": "needle-in-haystack step-quality debugging",
        "safe_claim": "operation stacks can surface very high-lift incorrect-step packets at tiny work fractions, but selected recall is low and fixed-session can recover more positives under the same top-k packet count.",
        "counterpoint": "Use this as selective evidence, not as a complete incorrect-step detector.",
    },
    "agentnet_redundant_step": {
        "paper_value": "human desktop redundancy diagnosis",
        "safe_claim": "operation stacks increase recall and lift over fixed-session for redundant-step packets while staying far smaller than flat summaries.",
        "counterpoint": "Fixed-session reaches the first positive earlier on this task, so the result is a recall/aggregation tradeoff.",
    },
    "agentreward_looping": {
        "paper_value": "prevalent web-agent looping diagnosis",
        "safe_claim": "operation stacks recover many looping positives and improve recall over fixed-session, but looping is too prevalent in this sample to create a high-lift top packet.",
        "counterpoint": "This is a prevalence and aggregation result, not enriched anomaly detection.",
    },
    "agentreward_side_effect": {
        "paper_value": "side-effectful web-agent behavior triage",
        "safe_claim": "operation stacks expose positives that fixed-session misses under the same packet policy and can find an early high-lift group, but top-5 packet quality is ranking-depth sensitive.",
        "counterpoint": "The top-5 packet lift falls below prevalence, so the paper should highlight query/ranker choice instead of a universal default.",
    },
    "osworld_group_start": {
        "paper_value": "human grouped-action boundary inspection",
        "safe_claim": "operation stacks recover much more selected recall than fixed-session for human grouped-action starts, showing why recursive depth matters for a single action sequence.",
        "counterpoint": "The work cost is much larger than fixed-session, so this is a boundary-coverage tradeoff, not cheaper inspection.",
    },
    "satraj_unsafe": {
        "paper_value": "desktop safety auditing",
        "safe_claim": "operation stacks produce the clearest selective win: high lift, higher recall than fixed-session, and far less work than flat summaries for unsafe desktop operations.",
        "counterpoint": "Fixed-session still reaches the first positive at lower work, preserving it as a drilldown counterpoint.",
    },
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


def load_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as file:
        return json.load(file)


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


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


def ensure_sources_tracked_clean(paths: list[Path]) -> None:
    for path in paths:
        if not path.exists():
            raise SystemExit(f"missing source artifact {rel(path)}")
        git_check("source artifact is not git-tracked", ["ls-files", "--error-unmatch"], path)
        git_check("source artifact has unstaged changes", ["diff", "--quiet"], path)
        git_check("source artifact has staged changes", ["diff", "--cached", "--quiet"], path)


def as_float(value: Any) -> float:
    if value == "inf":
        return math.inf
    if value is None:
        return math.nan
    return float(value)


def round_value(value: Any) -> Any:
    if isinstance(value, float):
        if math.isnan(value):
            return None
        if math.isinf(value):
            return "inf"
        return round(value, 4)
    if isinstance(value, dict):
        return {key: round_value(child) for key, child in value.items()}
    if isinstance(value, list):
        return [round_value(child) for child in value]
    return value


def require_two_abstractions(payloads: list[dict[str, Any]]) -> None:
    for payload in payloads:
        abstractions = payload.get("profiler_abstractions")
        normalized = [str(item).replace(" ", "_") for item in abstractions or []]
        if normalized and normalized != ["operation", "operation_stack"]:
            raise SystemExit(f"unexpected profiler abstractions {abstractions}")


def build_task_cards(
    problem_value: dict[str, Any],
    view_frontier: dict[str, Any],
) -> list[dict[str, Any]]:
    frontier_by_task = {row["task"]: row for row in view_frontier["task_frontiers"]}
    cards = []
    for source_card in problem_value["problem_cards"]:
        task = source_card["task"]
        if task not in frontier_by_task:
            raise SystemExit(f"missing R313 frontier row for task {task}")
        if task not in TASK_TAKEAWAYS:
            raise SystemExit(f"missing R317 paper takeaway template for task {task}")

        r305 = source_card["r305_case_packet"]
        operation = r305["operation_stack"]
        fixed = r305["fixed_session"]
        flat = r305["flat"]
        r308 = source_card["r308_first_evidence"]
        frontier = frontier_by_task[task]
        takeaway = TASK_TAKEAWAYS[task]

        recall_ratio = as_float(r305["operation_vs_fixed_recall_ratio"])
        work_ratio = as_float(r305["operation_vs_fixed_work_ratio"])
        high_lift = bool(r308["operation_stack_high_lift"])
        best_lift = frontier["best_lift"]
        best_recall = frontier["best_recall_under_30pct_work"]

        if not high_lift:
            evidence_pattern = "prevalent_positive_recall"
        elif operation["recall"] < 0.02:
            evidence_pattern = "high_lift_low_recall"
        elif recall_ratio > 1.0 and work_ratio > 1.0:
            evidence_pattern = "higher_recall_higher_work"
        elif recall_ratio > 1.0 and work_ratio <= 1.0:
            evidence_pattern = "higher_recall_lower_work"
        else:
            evidence_pattern = "selective_counterpoint"

        cards.append(
            {
                "task": task,
                "dataset": source_card["dataset"],
                "query_family": source_card["query_family"],
                "problem": source_card["problem"],
                "paper_value": takeaway["paper_value"],
                "oracle": source_card["oracle"],
                "operation_stack_packet": {
                    "work": operation["work"],
                    "recall": operation["recall"],
                    "lift": operation["lift"],
                    "precision": operation.get("precision"),
                    "first_positive_work": r308["operation_stack_first_positive_work"],
                    "first_high_lift_work": r308["operation_stack_first_high_lift_work"],
                    "has_high_lift_group": high_lift,
                },
                "flat_counterpoint": {
                    "work": flat["work"],
                    "recall": flat["recall"],
                    "lift": flat["lift"],
                    "operation_vs_flat_work_ratio": r305["operation_vs_flat_work_ratio"],
                    "operation_vs_flat_lift_ratio": r305["operation_vs_flat_lift_ratio"],
                },
                "fixed_session_counterpoint": {
                    "work": fixed["work"],
                    "recall": fixed["recall"],
                    "lift": fixed["lift"],
                    "operation_vs_fixed_recall_ratio": r305["operation_vs_fixed_recall_ratio"],
                    "operation_vs_fixed_work_ratio": r305["operation_vs_fixed_work_ratio"],
                    "fixed_session_first_positive_work": r308["fixed_session_first_positive_work"],
                },
                "frontier": {
                    "views_on_frontier": frontier["views_on_frontier"],
                    "operation_stack_on_frontier": frontier["operation_stack_on_frontier"],
                    "best_lift_view": best_lift["view"],
                    "best_lift_ranker": best_lift["ranker"],
                    "best_lift": best_lift["lift"],
                    "best_recall_under_30pct_view": best_recall["view"],
                    "best_recall_under_30pct": best_recall["recall"],
                    "best_recall_under_30pct_lift": best_recall["lift"],
                },
                "evidence_pattern": evidence_pattern,
                "safe_paper_claim": takeaway["safe_claim"],
                "counterpoint": takeaway["counterpoint"],
                "source_counterpoints": source_card["counterpoints"],
            }
        )
    return cards


def summarize(
    problem_value: dict[str, Any],
    view_frontier: dict[str, Any],
    analyst_readout: dict[str, Any],
    cards: list[dict[str, Any]],
) -> dict[str, Any]:
    r309_summary = problem_value["summary"]
    r313_summary = view_frontier["summary"]
    r316_top3 = analyst_readout["summary_by_view"]["3"]
    operation_cards = [card["operation_stack_packet"] for card in cards]
    return {
        "datasets": r309_summary["dataset_count"],
        "tasks": r309_summary["tasks"],
        "operations": r309_summary["operation_count"],
        "positive_operations": r309_summary["positive_operation_count"],
        "operation_stack_more_selective_than_flat": r309_summary["operation_stack"]["tasks_more_selective_than_flat"],
        "operation_stack_high_lift_coverage": r309_summary["operation_stack"]["high_lift_coverage"],
        "operation_stack_higher_recall_than_fixed_session": r309_summary["operation_stack"]["tasks_higher_recall_than_fixed_session"],
        "operation_stack_lower_work_than_fixed_session": r309_summary["operation_stack"]["tasks_less_work_than_fixed_session"],
        "operation_stack_frontier_coverage": r313_summary["operation_stack_on_frontier"],
        "operation_stack_best_lift_tasks": r313_summary["operation_stack_best_lift"],
        "operation_stack_best_recall_under_30pct_work_tasks": r313_summary["operation_stack_best_recall_under_30pct_work"],
        "flat_frontier_counterpoint": r313_summary["flat_on_frontier"],
        "fixed_session_frontier_counterpoint": r313_summary["fixed_session_on_frontier"],
        "r316_top3_operation_stack_positive_high_lift": {
            "positive_hit_rate": r316_top3["operation_stack"]["positive_hit_rate"],
            "high_lift_hit_rate": r316_top3["operation_stack"]["high_lift_hit_rate"],
        },
        "r316_top3_fixed_session_positive_high_lift": {
            "positive_hit_rate": r316_top3["fixed_session"]["positive_hit_rate"],
            "high_lift_hit_rate": r316_top3["fixed_session"]["high_lift_hit_rate"],
        },
        "r316_top3_flat_positive_high_lift": {
            "positive_hit_rate": r316_top3["flat"]["positive_hit_rate"],
            "high_lift_hit_rate": r316_top3["flat"]["high_lift_hit_rate"],
        },
        "median_operation_stack_case_work": median(card["work"] for card in operation_cards),
        "median_operation_stack_case_recall": median(card["recall"] for card in operation_cards),
        "median_operation_stack_case_lift": median(card["lift"] for card in operation_cards),
    }


def paper_takeaways(summary: dict[str, Any], cards: list[dict[str, Any]]) -> list[str]:
    strong = [card for card in cards if card["evidence_pattern"] in {"higher_recall_lower_work", "higher_recall_higher_work"}]
    high_lift = [card for card in cards if card["operation_stack_packet"]["has_high_lift_group"]]
    return [
        (
            "Across {tasks} oracle-backed tasks from {datasets} datasets, operation stacks are a paper-ready "
            "inspectability surface rather than a single winning hierarchy: they are on the non-oracle Pareto "
            "frontier for {frontier} tasks, while flat and fixed-session also remain frontier counterpoints."
        ).format(
            tasks=summary["tasks"],
            datasets=summary["datasets"],
            frontier=summary["operation_stack_frontier_coverage"],
        ),
        (
            "The real-problem value is strongest for safety and step-quality triage: {strong_count}/6 tasks "
            "show higher selected recall than fixed-session, and {high_lift_count}/6 contain a high-lift "
            "operation-stack group under the hidden-key packet policy."
        ).format(
            strong_count=summary["operation_stack_higher_recall_than_fixed_session"],
            high_lift_count=len(high_lift),
        ),
        (
            "The main counterpoint is also stable: operation stacks are lower-work than fixed-session on only "
            f"{summary['operation_stack_lower_work_than_fixed_session']}/6 tasks, so the paper must claim "
            "a configurable tradeoff surface, not baseline dominance."
        ),
        (
            "The R316 assignment readout checks that the controlled-study instrument can recover the same "
            "tradeoff before running analysts: top-3 operation-stack positive/high-lift hit rates are "
            f"{summary['r316_top3_operation_stack_positive_high_lift']['positive_hit_rate']}/"
            f"{summary['r316_top3_operation_stack_positive_high_lift']['high_lift_hit_rate']}, versus "
            f"{summary['r316_top3_fixed_session_positive_high_lift']['positive_hit_rate']}/"
            f"{summary['r316_top3_fixed_session_positive_high_lift']['high_lift_hit_rate']} for fixed-session "
            f"and {summary['r316_top3_flat_positive_high_lift']['positive_hit_rate']}/"
            f"{summary['r316_top3_flat_positive_high_lift']['high_lift_hit_rate']} for flat."
        ),
    ]


def readiness_rubric() -> dict[str, Any]:
    return {
        "mechanism_claims": {
            "level": "level_4_scoped_systems_narrative",
            "reason": "C1/C2 have heterogeneous-trace, recursive-depth, profile-spec, and exchange-trace evidence with explicit two-abstraction guardrails.",
        },
        "inspectability_claims": {
            "level": "level_3_plus_automated_proxy",
            "reason": "C4 has named baselines, real labeled tasks, problem disaggregation, frontier counterpoints, and a controlled-study protocol, but no completed human/agent analyst outcomes.",
        },
        "field_derivation_claims": {
            "level": "level_3_partial",
            "reason": "C3 has deterministic and supervised probes plus calibration failures, but not a general boundary detector.",
        },
        "submission_blockers": [
            "complete controlled human/agent analyst study before claiming accuracy, time-to-answer, or productivity",
            "replicate boundary backend on another suitable boundary oracle before stronger C3 wording",
            "keep trace ecosystem wording scoped to exchange containers and operation conversion, not full platform compatibility",
        ],
    }


def write_task_csv(path: Path, cards: list[dict[str, Any]]) -> None:
    fields = [
        "task",
        "dataset",
        "query_family",
        "paper_value",
        "evidence_pattern",
        "operation_work",
        "operation_recall",
        "operation_lift",
        "operation_high_lift",
        "fixed_recall",
        "fixed_work",
        "operation_vs_fixed_recall_ratio",
        "operation_vs_fixed_work_ratio",
        "best_lift_view",
        "best_recall_under_30pct_view",
        "counterpoint",
    ]
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for card in cards:
            writer.writerow(
                {
                    "task": card["task"],
                    "dataset": card["dataset"],
                    "query_family": card["query_family"],
                    "paper_value": card["paper_value"],
                    "evidence_pattern": card["evidence_pattern"],
                    "operation_work": card["operation_stack_packet"]["work"],
                    "operation_recall": card["operation_stack_packet"]["recall"],
                    "operation_lift": card["operation_stack_packet"]["lift"],
                    "operation_high_lift": card["operation_stack_packet"]["has_high_lift_group"],
                    "fixed_recall": card["fixed_session_counterpoint"]["recall"],
                    "fixed_work": card["fixed_session_counterpoint"]["work"],
                    "operation_vs_fixed_recall_ratio": card["fixed_session_counterpoint"]["operation_vs_fixed_recall_ratio"],
                    "operation_vs_fixed_work_ratio": card["fixed_session_counterpoint"]["operation_vs_fixed_work_ratio"],
                    "best_lift_view": card["frontier"]["best_lift_view"],
                    "best_recall_under_30pct_view": card["frontier"]["best_recall_under_30pct_view"],
                    "counterpoint": card["counterpoint"],
                }
            )


def write_markdown(path: Path, report: dict[str, Any]) -> None:
    lines = [
        "# Paper Real-Problem Narrative R317",
        "",
        "R317 is a synthesis over existing labeled-agent-trajectory artifacts. It is not a new empirical run, not a human or agent study, and not a detector.",
        "",
        "## Claim-First Takeaways",
        "",
    ]
    lines.extend(f"- {finding}" for finding in report["paper_takeaways"])
    lines.extend(
        [
            "",
            "## Task Narrative Matrix",
            "",
            "| Task | Dataset | Value | Evidence pattern | OS work | OS recall | OS lift | Counterpoint |",
            "|---|---|---|---|---:|---:|---:|---|",
        ]
    )
    for card in report["task_cards"]:
        op = card["operation_stack_packet"]
        lines.append(
            "| {task} | {dataset} | {value} | {pattern} | {work} | {recall} | {lift} | {counterpoint} |".format(
                task=card["task"],
                dataset=card["dataset"],
                value=card["paper_value"],
                pattern=card["evidence_pattern"],
                work=op["work"],
                recall=op["recall"],
                lift=op["lift"],
                counterpoint=card["counterpoint"],
            )
        )
    lines.extend(
        [
            "",
            "## Claim Boundary",
            "",
            "Supports: mechanism, novelty, and automated inspectability narrative over existing artifacts.",
            "Does not support: human accuracy, agent accuracy, time-to-answer, productivity, automatic detection, single-view dominance, or full trace-platform compatibility.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_html(path: Path, report: dict[str, Any]) -> None:
    findings = "".join(f"<li>{html.escape(finding)}</li>" for finding in report["paper_takeaways"])
    rows = []
    for card in report["task_cards"]:
        op = card["operation_stack_packet"]
        rows.append(
            "<tr>"
            f"<th>{html.escape(card['task'])}</th>"
            f"<td>{html.escape(card['dataset'])}</td>"
            f"<td>{html.escape(card['paper_value'])}</td>"
            f"<td>{html.escape(card['evidence_pattern'])}</td>"
            f"<td>{op['work']}</td>"
            f"<td>{op['recall']}</td>"
            f"<td>{op['lift']}</td>"
            f"<td>{html.escape(card['counterpoint'])}</td>"
            "</tr>"
        )
    path.write_text(
        """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Paper Real-Problem Narrative R317</title>
  <style>
    body { font-family: system-ui, sans-serif; margin: 2rem; color: #1f2933; }
    h1 { font-size: 1.6rem; }
    p, li { max-width: 900px; line-height: 1.5; }
    table { border-collapse: collapse; margin-top: 1.5rem; min-width: 920px; }
    th, td { border: 1px solid #d8dee9; padding: 0.5rem 0.65rem; text-align: left; vertical-align: top; }
    th { background: #f6f8fa; }
  </style>
</head>
<body>
  <h1>Paper Real-Problem Narrative R317</h1>
  <p>
    This synthesis reads existing tracked artifacts over labeled public agent
    trajectories and turns them into claim-first paper conclusions.
  </p>
  <ul>
"""
        + findings
        + """
  </ul>
  <table>
    <tr><th>Task</th><th>Dataset</th><th>Value</th><th>Pattern</th><th>OS work</th><th>OS recall</th><th>OS lift</th><th>Counterpoint</th></tr>
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
    out_dir = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    ensure_sources_tracked_clean(list(SOURCE_PATHS.values()))
    problem_value = load_json(SOURCE_PATHS["problem_value"])
    view_frontier = load_json(SOURCE_PATHS["view_frontier"])
    analyst_readout = load_json(SOURCE_PATHS["analyst_readout"])
    require_two_abstractions([problem_value, analyst_readout])

    cards = build_task_cards(problem_value, view_frontier)
    summary = summarize(problem_value, view_frontier, analyst_readout, cards)
    report_json = out_dir / "paper-narrative-report.json"
    task_csv = out_dir / "task-narrative.csv"
    report_md = out_dir / "paper-narrative-report.md"
    index_html = out_dir / "index.html"
    run_result = out_dir / "run-result.json"

    report = round_value(
        {
            "run_id": "R317",
            "schema": "agentsight.paper-real-problem-narrative.v1",
            "status": "ok",
            "purpose": "claim-first paper narrative over existing real-problem labeled trajectory artifacts",
            "input_policy": "tracked-clean R309/R313/R316 artifacts only; no dataset sync, no profiler rerun, no human/agent study",
            "source": {key: rel(path) for key, path in SOURCE_PATHS.items()},
            "not_new_empirical_result": True,
            "not_a_human_study_result": True,
            "not_an_agent_study_result": True,
            "profiler_abstractions": ["operation", "operation_stack"],
            "claim_scope": {
                "supports": [
                    "mechanism and novelty narrative",
                    "automated inspectability tradeoff over existing labeled tasks",
                    "real-problem disaggregation and reviewer-facing counterpoints",
                ],
                "does_not_support": [
                    "human analyst accuracy",
                    "agent analyst accuracy",
                    "time-to-answer improvement",
                    "developer productivity improvement",
                    "automatic detection or detector claims",
                    "single-view dominance",
                    "full trace-platform compatibility",
                ],
            },
            "summary": summary,
            "paper_takeaways": paper_takeaways(summary, cards),
            "readiness_rubric": readiness_rubric(),
            "task_cards": cards,
            "outputs": {
                "report_json": rel(report_json),
                "task_csv": rel(task_csv),
                "markdown": rel(report_md),
                "html": rel(index_html),
                "run_result": rel(run_result),
            },
        }
    )
    write_json(report_json, report)
    write_task_csv(task_csv, report["task_cards"])
    write_markdown(report_md, report)
    write_html(index_html, report)
    write_json(
        run_result,
        {
            "status": "ok",
            "run_id": "R317",
            "report": rel(report_json),
            "task_csv": rel(task_csv),
            "html": rel(index_html),
            "tasks": report["summary"]["tasks"],
            "datasets": report["summary"]["datasets"],
            "operations": report["summary"]["operations"],
            "operation_stack_frontier_coverage": report["summary"]["operation_stack_frontier_coverage"],
            "not_new_empirical_result": True,
            "not_a_human_study_result": True,
            "not_an_agent_study_result": True,
        },
    )
    print(json.dumps(load_json(run_result), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
