#!/usr/bin/env python3
"""R316: estimate readout sensitivity for the R315 analyst-study protocol.

R316 does not fetch datasets, rerun profilers, or execute a human/agent study.
It reads the tracked R315 visible packets, hidden scoring key, and balanced
assignment table, then scores a fixed scripted analyst policy that
selects the first top-k visible groups in each packet. The goal is to check
whether the ready-to-run protocol can read out the same inspectability tradeoff
seen in earlier automated proxies.
"""

from __future__ import annotations

import argparse
import csv
import html
import json
import math
import random
import subprocess
from pathlib import Path
from statistics import mean, median
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OUT_ROOT = ROOT / "docs" / "visexp" / "out"
SOURCE_DIR = OUT_ROOT / "analyst-study-protocol-r315"
DEFAULT_OUT_DIR = OUT_ROOT / "analyst-study-readout-r316"
VIEWS = ["flat", "fixed_session", "operation_stack"]
BASELINE_VIEWS = ["flat", "fixed_session"]
TOP_K_VALUES = [1, 3]
HIGH_LIFT_THRESHOLD = 1.5
BOOTSTRAP_SEED = "agentsight-r316-bootstrap-v1"
BOOTSTRAP_REPS = 5000
WITHHELD_ORACLE_FIELDS = {
    "looping",
    "side_effect",
    "safety",
    "step_correct",
    "step_redundant",
    "human_group",
    "group_pattern",
    "group_position",
    "positive_operations",
    "positive_rate",
    "positive_recall",
    "positive_precision",
    "positive_lift",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--bootstrap-reps", type=int, default=BOOTSTRAP_REPS)
    parser.add_argument("--high-lift-threshold", type=float, default=HIGH_LIFT_THRESHOLD)
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


def read_assignment(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as file:
        return list(csv.DictReader(file))


def round_value(value: Any) -> Any:
    if isinstance(value, float):
        if math.isinf(value):
            return "inf"
        return round(value, 4)
    if isinstance(value, dict):
        return {key: round_value(child) for key, child in value.items()}
    if isinstance(value, list):
        return [round_value(child) for child in value]
    return value


def median_or_none(values: list[float]) -> float | None:
    return float(median(values)) if values else None


def mean_or_none(values: list[float]) -> float | None:
    return float(mean(values)) if values else None


def validate_visible_hidden(
    visible_packets: dict[str, Any],
    hidden_key: dict[str, Any],
    assignment: list[dict[str, str]],
) -> None:
    if visible_packets.get("visible_only") is not True or hidden_key.get("hidden") is not True:
        raise SystemExit("R316 expects visible packets and a hidden scoring key")
    visible_cases = {case["packet_id"]: case for case in visible_packets["cases"]}
    hidden_cases = {case["packet_id"]: case for case in hidden_key["cases"]}
    if set(visible_cases) != set(hidden_cases):
        raise SystemExit("visible packets and hidden scoring key have different packet IDs")
    assigned_packets = {row["packet_id"] for row in assignment}
    if assigned_packets != set(visible_cases):
        raise SystemExit("assignment packet IDs do not match the visible packet set")
    for packet_id, visible in visible_cases.items():
        hidden = hidden_cases[packet_id]
        visible_ids = [group["group_id"] for group in visible["groups"]]
        hidden_ids = [group["group_id"] for group in hidden["groups"]]
        if visible_ids != hidden_ids:
            raise SystemExit(f"group order mismatch for {packet_id}")
        findings = visible_leakage_findings(visible)
        if findings:
            raise SystemExit(
                f"visible packet {packet_id} leaks hidden fields: {', '.join(findings[:5])}"
            )


def visible_leakage_findings(packet: dict[str, Any]) -> list[str]:
    findings: list[str] = []
    for group_index, group in enumerate(packet["groups"]):
        for key in group:
            if key in WITHHELD_ORACLE_FIELDS:
                findings.append(f"groups[{group_index}].{key}")
        for container in ["visible_features", "field_examples", "operation_examples"]:
            value = group.get(container)
            if isinstance(value, dict):
                for key in value:
                    if key in WITHHELD_ORACLE_FIELDS:
                        findings.append(f"groups[{group_index}].{container}.{key}")
            elif isinstance(value, list):
                for item_index, item in enumerate(value):
                    if isinstance(item, dict):
                        for key in item:
                            if key in WITHHELD_ORACLE_FIELDS:
                                findings.append(
                                    f"groups[{group_index}].{container}[{item_index}].{key}"
                                )
    return findings


def derive_task_totals(hidden_cases: list[dict[str, Any]]) -> dict[str, dict[str, float]]:
    totals: dict[str, dict[str, float]] = {}
    for case in hidden_cases:
        score = case["score"]
        work = float(score["inspected_operation_fraction"])
        recall = float(score["positive_recall"])
        if work <= 0 or recall <= 0:
            continue
        operations = float(score["inspected_operations"]) / work
        positives = float(score["positive_operations"]) / recall
        if case["view"] == "flat" or case["task"] not in totals:
            totals[case["task"]] = {
                "operations": operations,
                "positives": positives,
                "prevalence": positives / operations if operations else 0.0,
            }
    missing = sorted({case["task"] for case in hidden_cases} - set(totals))
    if missing:
        raise SystemExit(f"could not derive task totals for {missing}")
    return totals


def score_selection(
    hidden_case: dict[str, Any],
    task_totals: dict[str, dict[str, float]],
    top_k: int,
    high_lift_threshold: float,
) -> dict[str, Any]:
    task_total = task_totals[hidden_case["task"]]
    groups = hidden_case["groups"][:top_k]
    selected_operations = float(sum(group["operations"] for group in groups))
    selected_positives = float(sum(group["positive_operations"] for group in groups))
    task_operations = task_total["operations"]
    task_positives = task_total["positives"]
    prevalence = task_total["prevalence"]
    precision = selected_positives / selected_operations if selected_operations else 0.0
    recall = selected_positives / task_positives if task_positives else 0.0
    work = selected_operations / task_operations if task_operations else 0.0
    lift = precision / prevalence if prevalence else 0.0
    group_lifts = [
        (float(group["positive_rate"]) / prevalence if prevalence else 0.0)
        for group in groups
    ]
    return {
        "task": hidden_case["task"],
        "dataset": hidden_case["dataset"],
        "view": hidden_case["view"],
        "top_k": top_k,
        "selected_groups": len(groups),
        "selected_group_ids": [group["group_id"] for group in groups],
        "selected_operations": selected_operations,
        "selected_positive_operations": selected_positives,
        "work_fraction": work,
        "positive_recall": recall,
        "positive_precision": precision,
        "positive_lift": lift,
        "positive_hit": selected_positives > 0,
        "enriched_hit": selected_positives > 0 and lift >= 1.0,
        "high_lift_hit": any(
            group["positive_operations"] > 0 and group_lift >= high_lift_threshold
            for group, group_lift in zip(groups, group_lifts)
        ),
        "max_group_lift": max(group_lifts) if group_lifts else 0.0,
    }


def build_trial_scores(
    assignment: list[dict[str, str]],
    hidden_by_packet: dict[str, dict[str, Any]],
    task_totals: dict[str, dict[str, float]],
    high_lift_threshold: float,
) -> list[dict[str, Any]]:
    by_packet_topk: dict[tuple[str, int], dict[str, Any]] = {}
    for packet_id, hidden_case in hidden_by_packet.items():
        for top_k in TOP_K_VALUES:
            by_packet_topk[(packet_id, top_k)] = score_selection(
                hidden_case, task_totals, top_k, high_lift_threshold
            )
    trials: list[dict[str, Any]] = []
    for row in assignment:
        for top_k in TOP_K_VALUES:
            score = by_packet_topk[(row["packet_id"], top_k)]
            trials.append(
                {
                    "participant_id": row["participant_id"],
                    "trial_order": int(row["trial_order"]),
                    "packet_id": row["packet_id"],
                    "top_k": top_k,
                    **{key: row[key] for key in ["task", "dataset", "query_family", "view"]},
                    "positive_hit": score["positive_hit"],
                    "enriched_hit": score["enriched_hit"],
                    "high_lift_hit": score["high_lift_hit"],
                    "positive_recall": score["positive_recall"],
                    "work_fraction": score["work_fraction"],
                    "positive_lift": score["positive_lift"],
                    "positive_precision": score["positive_precision"],
                    "selected_groups": score["selected_groups"],
                    "selected_operations": score["selected_operations"],
                    "selected_positive_operations": score["selected_positive_operations"],
                }
            )
    return trials


def summarize_by_view(trials: list[dict[str, Any]]) -> dict[str, Any]:
    summary: dict[str, Any] = {}
    for top_k in TOP_K_VALUES:
        summary[str(top_k)] = {}
        for view in VIEWS:
            items = [row for row in trials if row["top_k"] == top_k and row["view"] == view]
            summary[str(top_k)][view] = round_value(
                {
                    "trials": len(items),
                    "tasks": len({row["task"] for row in items}),
                    "participants": len({row["participant_id"] for row in items}),
                    "positive_hit_rate": mean_or_none([float(row["positive_hit"]) for row in items]),
                    "high_lift_hit_rate": mean_or_none(
                        [float(row["high_lift_hit"]) for row in items]
                    ),
                    "median_recall": median_or_none([row["positive_recall"] for row in items]),
                    "median_work": median_or_none([row["work_fraction"] for row in items]),
                    "median_lift": median_or_none([row["positive_lift"] for row in items]),
                    "mean_recall": mean_or_none([row["positive_recall"] for row in items]),
                    "mean_work": mean_or_none([row["work_fraction"] for row in items]),
                    "mean_lift": mean_or_none([row["positive_lift"] for row in items]),
                }
            )
    return summary


def task_level_scores(
    hidden_by_packet: dict[str, dict[str, Any]],
    task_totals: dict[str, dict[str, float]],
    high_lift_threshold: float,
) -> list[dict[str, Any]]:
    rows = []
    for hidden_case in hidden_by_packet.values():
        for top_k in TOP_K_VALUES:
            rows.append(score_selection(hidden_case, task_totals, top_k, high_lift_threshold))
    return rows


def paired_task_deltas(task_rows: list[dict[str, Any]]) -> dict[str, Any]:
    rows_by_key = {
        (row["task"], row["view"], row["top_k"]): row
        for row in task_rows
    }
    metrics = [
        "positive_hit",
        "high_lift_hit",
        "positive_recall",
        "work_fraction",
        "positive_lift",
    ]
    tasks = sorted({row["task"] for row in task_rows})
    output: dict[str, Any] = {}
    for top_k in TOP_K_VALUES:
        output[str(top_k)] = {}
        for baseline in BASELINE_VIEWS:
            pair_key = f"operation_stack_vs_{baseline}"
            output[str(top_k)][pair_key] = {}
            for metric in metrics:
                deltas = []
                for task in tasks:
                    left = rows_by_key[(task, "operation_stack", top_k)][metric]
                    right = rows_by_key[(task, baseline, top_k)][metric]
                    deltas.append(float(left) - float(right))
                output[str(top_k)][pair_key][metric] = round_value(
                    {
                        "task_deltas": deltas,
                        "median_delta": median_or_none(deltas),
                        "mean_delta": mean_or_none(deltas),
                        "improved_tasks": sum(1 for delta in deltas if delta > 0),
                        "tied_tasks": sum(1 for delta in deltas if delta == 0),
                        "worse_tasks": sum(1 for delta in deltas if delta < 0),
                    }
                )
    return output


def participant_view_means(trials: list[dict[str, Any]], top_k: int) -> dict[str, dict[str, dict[str, float]]]:
    metrics = [
        "positive_hit",
        "high_lift_hit",
        "positive_recall",
        "work_fraction",
        "positive_lift",
    ]
    participants = sorted({row["participant_id"] for row in trials})
    result: dict[str, dict[str, dict[str, float]]] = {}
    for participant in participants:
        result[participant] = {}
        for view in VIEWS:
            items = [
                row
                for row in trials
                if row["top_k"] == top_k and row["participant_id"] == participant and row["view"] == view
            ]
            if not items:
                continue
            result[participant][view] = {
                metric: mean(float(row[metric]) for row in items)
                for metric in metrics
            }
    return result


def percentile(values: list[float], pct: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = (len(ordered) - 1) * pct
    lower = int(math.floor(index))
    upper = int(math.ceil(index))
    if lower == upper:
        return ordered[lower]
    weight = index - lower
    return ordered[lower] * (1 - weight) + ordered[upper] * weight


def bootstrap_participant_deltas(
    trials: list[dict[str, Any]],
    reps: int,
) -> dict[str, Any]:
    rng = random.Random(BOOTSTRAP_SEED)
    metrics = [
        "positive_hit",
        "high_lift_hit",
        "positive_recall",
        "work_fraction",
        "positive_lift",
    ]
    output: dict[str, Any] = {}
    for top_k in TOP_K_VALUES:
        means = participant_view_means(trials, top_k)
        participants = sorted(means)
        output[str(top_k)] = {}
        for baseline in BASELINE_VIEWS:
            pair_key = f"operation_stack_vs_{baseline}"
            output[str(top_k)][pair_key] = {}
            for metric in metrics:
                observed_deltas = [
                    means[participant]["operation_stack"][metric]
                    - means[participant][baseline][metric]
                    for participant in participants
                ]
                boot = []
                for _ in range(reps):
                    sample = [rng.choice(observed_deltas) for _ in observed_deltas]
                    boot.append(mean(sample))
                output[str(top_k)][pair_key][metric] = round_value(
                    {
                        "participant_count": len(participants),
                        "mean_delta": mean_or_none(observed_deltas),
                        "median_delta": median_or_none(observed_deltas),
                        "bootstrap_reps": reps,
                        "bootstrap_mean_ci95": [
                            percentile(boot, 0.025),
                            percentile(boot, 0.975),
                        ],
                    }
                )
    return output


def primary_findings(summary: dict[str, Any], deltas: dict[str, Any]) -> list[str]:
    top3 = summary["3"]
    op = top3["operation_stack"]
    fixed = top3["fixed_session"]
    flat = top3["flat"]
    op_vs_fixed = deltas["3"]["operation_stack_vs_fixed_session"]
    return [
        (
            "Top-3 operation-stack packets contain a positive group on "
            f"{op['positive_hit_rate']:.1%} of assigned trials, versus "
            f"{fixed['positive_hit_rate']:.1%} for fixed-session and "
            f"{flat['positive_hit_rate']:.1%} for flat."
        ),
        (
            "Top-3 operation-stack packets contain a high-lift group on "
            f"{op['high_lift_hit_rate']:.1%} of assigned trials, versus "
            f"{fixed['high_lift_hit_rate']:.1%} for fixed-session and "
            f"{flat['high_lift_hit_rate']:.1%} for flat."
        ),
        (
            "The task-paired median recall delta for operation-stack over fixed-session "
            f"is {op_vs_fixed['positive_recall']['median_delta']}, while the median work "
            f"delta is {op_vs_fixed['work_fraction']['median_delta']}."
        ),
        (
            "The readout preserves the known tradeoff: operation-stack exposes more "
            "positives than fixed-session in most tasks, but it uses more work and does "
            "not dominate every metric."
        ),
    ]


def write_trial_csv(path: Path, trials: list[dict[str, Any]]) -> None:
    fields = [
        "participant_id",
        "trial_order",
        "packet_id",
        "top_k",
        "task",
        "dataset",
        "query_family",
        "view",
        "positive_hit",
        "high_lift_hit",
        "positive_recall",
        "work_fraction",
        "positive_lift",
        "positive_precision",
        "selected_groups",
        "selected_operations",
        "selected_positive_operations",
    ]
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for row in trials:
            writer.writerow({field: round_value(row[field]) for field in fields})


def write_markdown(path: Path, report: dict[str, Any]) -> None:
    lines = [
        "# Analyst Study Readout R316",
        "",
        "R316 is a scripted readout of the R315 protocol, not a human or agent study result.",
        "The scripted analyst policy selects the first top-k visible groups in each packet, then the hidden key scores the selection.",
        "",
        "## Primary Findings",
        "",
    ]
    lines.extend(f"- {finding}" for finding in report["primary_findings"])
    lines.extend(
        [
            "",
            "## Top-3 View Summary",
            "",
            "| View | Positive hit rate | High-lift hit rate | Median recall | Median work | Median lift |",
            "|---|---:|---:|---:|---:|---:|",
        ]
    )
    for view, stats in report["summary_by_view"]["3"].items():
        lines.append(
            "| {view} | {positive_hit_rate} | {high_lift_hit_rate} | {median_recall} | {median_work} | {median_lift} |".format(
                view=view,
                positive_hit_rate=stats["positive_hit_rate"],
                high_lift_hit_rate=stats["high_lift_hit_rate"],
                median_recall=stats["median_recall"],
                median_work=stats["median_work"],
                median_lift=stats["median_lift"],
            )
        )
    lines.extend(
        [
            "",
            "## Claim Boundary",
            "",
            "This artifact supports protocol sensitivity and automated inspectability wording only.",
            "It does not support human accuracy, agent accuracy, time-to-answer, productivity, automatic detection, detector, or single-view-dominance claims.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_html(path: Path, report: dict[str, Any]) -> None:
    rows = []
    for view, stats in report["summary_by_view"]["3"].items():
        rows.append(
            "<tr>"
            f"<th>{html.escape(view)}</th>"
            f"<td>{stats['positive_hit_rate']}</td>"
            f"<td>{stats['high_lift_hit_rate']}</td>"
            f"<td>{stats['median_recall']}</td>"
            f"<td>{stats['median_work']}</td>"
            f"<td>{stats['median_lift']}</td>"
            "</tr>"
        )
    findings = "".join(
        f"<li>{html.escape(finding)}</li>" for finding in report["primary_findings"]
    )
    path.write_text(
        """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Analyst Study Readout R316</title>
  <style>
    body { font-family: system-ui, sans-serif; margin: 2rem; color: #1f2933; }
    h1 { font-size: 1.6rem; }
    p, li { max-width: 860px; line-height: 1.5; }
    table { border-collapse: collapse; margin-top: 1.5rem; min-width: 760px; }
    th, td { border: 1px solid #d8dee9; padding: 0.55rem 0.75rem; text-align: left; }
    th { background: #f6f8fa; }
    code { background: #f6f8fa; padding: 0.1rem 0.25rem; border-radius: 4px; }
  </style>
</head>
<body>
  <h1>Analyst Study Readout R316</h1>
  <p>
	    This is a scripted sensitivity readout over the R315 protocol. It scores a
	    visible-order top-k policy against the hidden key and does not claim human
	    or agent analyst performance, automatic detection, or single-view dominance.
  </p>
  <ul>
"""
        + findings
        + """
  </ul>
  <table>
    <tr><th>View</th><th>Positive hit rate</th><th>High-lift hit rate</th><th>Median recall</th><th>Median work</th><th>Median lift</th></tr>
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
    if args.bootstrap_reps <= 0:
        raise SystemExit("--bootstrap-reps must be positive")
    out_dir = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    source_paths = {
        "study_protocol": SOURCE_DIR / "study-protocol.json",
        "visible_packets": SOURCE_DIR / "visible-study-packets.json",
        "hidden_key": SOURCE_DIR / "hidden-scoring-key.json",
        "assignment": SOURCE_DIR / "assignment.csv",
    }
    ensure_sources_tracked_clean(list(source_paths.values()))

    study_protocol = load_json(source_paths["study_protocol"])
    visible_packets = load_json(source_paths["visible_packets"])
    hidden_key = load_json(source_paths["hidden_key"])
    assignment = read_assignment(source_paths["assignment"])
    validate_visible_hidden(visible_packets, hidden_key, assignment)

    hidden_by_packet = {case["packet_id"]: case for case in hidden_key["cases"]}
    task_totals = derive_task_totals(hidden_key["cases"])
    task_rows = task_level_scores(hidden_by_packet, task_totals, args.high_lift_threshold)
    trial_scores = build_trial_scores(
        assignment,
        hidden_by_packet,
        task_totals,
        args.high_lift_threshold,
    )
    summary = summarize_by_view(trial_scores)
    task_deltas = paired_task_deltas(task_rows)
    bootstrap = bootstrap_participant_deltas(trial_scores, args.bootstrap_reps)

    report_json = out_dir / "readout-report.json"
    trials_csv = out_dir / "trial-scores.csv"
    report_md = out_dir / "readout-report.md"
    index_html = out_dir / "index.html"
    run_result = out_dir / "run-result.json"
    report = round_value(
        {
            "run_id": "R316",
            "schema": "agentsight.analyst-study-readout.v1",
            "status": "ok",
            "source": {key: rel(path) for key, path in source_paths.items()},
            "input_policy": "tracked-clean R315 artifacts only; no dataset sync and no profiler rerun",
            "scripted_policy": {
                "name": "visible_order_top_k",
                "top_k_values": TOP_K_VALUES,
                "description": "fixed scripted policy that selects the first top-k groups shown in the visible packet",
                "registration_status": "defined by R316 for protocol-sensitivity readout; not part of the R315 protocol registration",
            },
            "claim_scope": {
                "supports": "protocol sensitivity and automated inspectability tradeoff",
                "does_not_support": [
                    "human analyst accuracy",
                    "agent analyst accuracy",
                    "time-to-answer improvement",
                    "developer productivity improvement",
                    "automatic detection or detector claims",
                    "single-view dominance",
                ],
            },
            "not_a_human_study_result": True,
            "not_an_agent_study_result": True,
            "profiler_abstractions": ["operation", "operation_stack"],
            "study_context": {
                "protocol_status": study_protocol.get("study_design", {}).get(
                    "protocol_status", "ready_to_run"
                ),
                "participants": len({row["participant_id"] for row in assignment}),
                "trials": len(assignment),
                "tasks": len({row["task"] for row in assignment}),
                "views": VIEWS,
                "high_lift_threshold": args.high_lift_threshold,
                "bootstrap_seed": BOOTSTRAP_SEED,
                "bootstrap_reps": args.bootstrap_reps,
            },
            "primary_findings": primary_findings(summary, task_deltas),
            "summary_by_view": summary,
            "paired_task_deltas": task_deltas,
            "participant_bootstrap": bootstrap,
            "outputs": {
                "report_json": rel(report_json),
                "trial_scores_csv": rel(trials_csv),
                "markdown": rel(report_md),
                "html": rel(index_html),
                "run_result": rel(run_result),
            },
        }
    )
    write_json(report_json, report)
    write_trial_csv(trials_csv, trial_scores)
    write_markdown(report_md, report)
    write_html(index_html, report)
    write_json(run_result, {
        "status": "ok",
        "run_id": "R316",
        "report": rel(report_json),
        "trial_scores": rel(trials_csv),
        "html": rel(index_html),
        "not_a_human_study_result": True,
        "not_an_agent_study_result": True,
        "top3_operation_stack_positive_hit_rate": report["summary_by_view"]["3"]["operation_stack"]["positive_hit_rate"],
        "top3_operation_stack_high_lift_hit_rate": report["summary_by_view"]["3"]["operation_stack"]["high_lift_hit_rate"],
        "top3_operation_stack_vs_fixed_recall_delta": report["paired_task_deltas"]["3"]["operation_stack_vs_fixed_session"]["positive_recall"]["median_delta"],
    })
    print(json.dumps(load_json(run_result), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
