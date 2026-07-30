#!/usr/bin/env python3
"""Summarize paired FULL/SPLIT token volume and unchanged scorer metrics."""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path
import random
import statistics
from typing import Any

import run_annotation


HERE = Path(__file__).resolve().parent


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as stream:
        return [json.loads(line) for line in stream if line.strip()]


def percentile(values: list[float], q: float) -> float:
    values = sorted(values)
    position = q * (len(values) - 1)
    lower = int(position)
    upper = min(lower + 1, len(values) - 1)
    weight = position - lower
    return values[lower] * (1 - weight) + values[upper] * weight


def bcubed(rows: list[dict[str, Any]]) -> float:
    pred_sizes = Counter(str(row["candidate"]) for row in rows)
    truth_sizes = Counter(str(row["official_stage"]) for row in rows)
    intersections = Counter(
        (str(row["candidate"]), str(row["official_stage"])) for row in rows
    )
    precision = statistics.fmean(
        intersections[(str(row["candidate"]), str(row["official_stage"]))]
        / pred_sizes[str(row["candidate"])]
        for row in rows
    )
    recall = statistics.fmean(
        intersections[(str(row["candidate"]), str(row["official_stage"]))]
        / truth_sizes[str(row["official_stage"])]
        for row in rows
    )
    return 2 * precision * recall / (precision + recall) if precision + recall else 0.0


def boundary(rows: list[dict[str, Any]]) -> float:
    true_positive = sum(
        int(bool(row["candidate"]) and bool(row["official_boundary"])) for row in rows
    )
    predicted = sum(int(bool(row["candidate"])) for row in rows)
    official = sum(int(bool(row["official_boundary"])) for row in rows)
    precision = true_positive / predicted if predicted else 0.0
    recall = true_positive / official if official else 0.0
    return 2 * precision * recall / (precision + recall) if precision + recall else 0.0


def bootstrap(
    task_names: list[str],
    cost_by_task: dict[str, dict[str, int]],
    operation_by_condition_task: dict[str, dict[str, list[dict[str, Any]]]],
    pair_by_condition_task: dict[str, dict[str, list[dict[str, Any]]]],
) -> dict[str, list[float]]:
    rng = random.Random(20260729)
    token_ratios = []
    b3_deltas = []
    boundary_deltas = []
    for _ in range(10_000):
        sampled = [rng.choice(task_names) for _ in task_names]
        full_tokens = sum(cost_by_task[task]["full"] for task in sampled)
        split_tokens = sum(cost_by_task[task]["split"] for task in sampled)
        token_ratios.append(split_tokens / full_tokens)
        operation_rows = {
            condition: [
                row
                for task in sampled
                for row in operation_by_condition_task[condition][task]
            ]
            for condition in ("full", "split")
        }
        pair_rows = {
            condition: [
                row
                for task in sampled
                for row in pair_by_condition_task[condition][task]
            ]
            for condition in ("full", "split")
        }
        b3_deltas.append(bcubed(operation_rows["split"]) - bcubed(operation_rows["full"]))
        boundary_deltas.append(
            boundary(pair_rows["split"]) - boundary(pair_rows["full"])
        )
    return {
        "split_over_full_provider_tokens": [
            percentile(token_ratios, 0.025),
            percentile(token_ratios, 0.975),
        ],
        "split_minus_full_bcubed_f1": [
            percentile(b3_deltas, 0.025),
            percentile(b3_deltas, 0.975),
        ],
        "split_minus_full_boundary_f1": [
            percentile(boundary_deltas, 0.025),
            percentile(boundary_deltas, 0.975),
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("group", choices=("preflight", "pilot", "confirmation"))
    args = parser.parse_args()
    selection = read_json(run_annotation.SELECTION)
    task_by_session = {
        str(row["session"]): str(row["task_name"]) for row in selection[args.group]
    }
    cell_rows: list[dict[str, Any]] = []
    cost_by_task: dict[str, dict[str, int]] = defaultdict(dict)
    for session, task_name in task_by_session.items():
        row = {"session": session, "task_name": task_name}
        for condition in ("full", "split"):
            cell = read_json(
                run_annotation.cell_path(args.group, condition, session).parent
                / "cell.json"
            )
            row[condition] = {
                key: cell.get(key)
                for key in (
                    "status",
                    "provider_tokens",
                    "input_tokens",
                    "output_tokens",
                    "cached_input_tokens",
                    "reasoning_output_tokens",
                    "calls",
                    "wall_seconds",
                    "detail_turns",
                )
            }
            cost_by_task[task_name][condition] = int(cell["provider_tokens"])
        cell_rows.append(row)
    score_summaries = {
        condition: read_json(
            HERE
            / "pipeline"
            / args.group
            / condition
            / "score/summary.json"
        )
        for condition in ("full", "split")
    }
    operations: dict[str, dict[str, list[dict[str, Any]]]] = {}
    pairs: dict[str, dict[str, list[dict[str, Any]]]] = {}
    for condition in ("full", "split"):
        operations[condition] = defaultdict(list)
        for row in read_jsonl(
            HERE
            / "pipeline"
            / args.group
            / condition
            / "score/operation-score-rows.jsonl"
        ):
            operations[condition][str(row["task_name"])].append(row)
        pairs[condition] = defaultdict(list)
        for row in read_jsonl(
            HERE
            / "pipeline"
            / args.group
            / condition
            / "score/pair-score-rows.jsonl"
        ):
            pairs[condition][str(row["task_name"])].append(row)
    tasks = sorted(task_by_session.values())
    total_tokens = {
        condition: sum(int(row[condition]["provider_tokens"]) for row in cell_rows)
        for condition in ("full", "split")
    }
    metrics = {
        condition: score_summaries[condition]["metrics"]["candidate"]
        for condition in ("full", "split")
    }
    intervals = (
        bootstrap(tasks, cost_by_task, operations, pairs)
        if len(tasks) > 1
        else None
    )
    result = {
        "schema": "agentsight.split-vs-full-annotation.v1",
        "group": args.group,
        "sessions": len(cell_rows),
        "rows": cell_rows,
        "provider_token_volume": {
            **total_tokens,
            "split_over_full": total_tokens["split"] / total_tokens["full"],
            "split_saving_fraction": 1
            - total_tokens["split"] / total_tokens["full"],
        },
        "metrics": metrics,
        "delta": {
            "bcubed_f1": float(metrics["split"]["bcubed"]["f1"])
            - float(metrics["full"]["bcubed"]["f1"]),
            "boundary_f1": float(metrics["split"]["boundary"]["f1"])
            - float(metrics["full"]["boundary"]["f1"]),
        },
        "task_family_bootstrap_95ci": intervals,
        "coverage": {
            condition: read_json(
                HERE
                / "pipeline"
                / args.group
                / condition
                / "pipeline-summary.json"
            )["operations"]
            for condition in ("full", "split")
        },
    }
    if intervals is not None:
        result["confirmation_support"] = {
            "token_ratio_upper_below_one": intervals[
                "split_over_full_provider_tokens"
            ][1]
            < 1,
            "bcubed_delta_lower_at_least_minus_003": intervals[
                "split_minus_full_bcubed_f1"
            ][0]
            >= -0.03,
            "boundary_delta_lower_at_least_minus_003": intervals[
                "split_minus_full_boundary_f1"
            ][0]
            >= -0.03,
            "complete_operation_coverage": len(set(result["coverage"].values())) == 1,
        }
    output = HERE / f"{args.group}-summary.json"
    output.write_text(
        json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
