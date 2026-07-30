#!/usr/bin/env python3
"""Summarize fixed-budget converter trials with scenario-cluster uncertainty."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import random
import statistics
from typing import Any

import run_converter_pairs
import summarize


HERE = Path(__file__).resolve().parent
METRICS = (
    "similarity",
    "success",
    "milestone_similarity",
    "minefield_similarity",
    "turn_count",
    "agent_total_tokens",
    "agent_prompt_tokens",
    "agent_completion_tokens",
    "agent_model_calls",
    "agent_tool_calls",
)


def load(condition: str, seed: int, scenario: str) -> dict[str, Any]:
    path = run_converter_pairs.episode_path(condition, seed, scenario)
    if not path.is_file():
        return {"status": "missing"}
    return json.loads(path.read_text(encoding="utf-8"))


def invalid_id_counts(record: dict[str, Any]) -> tuple[int, int]:
    raw = 0
    for request in (record.get("agent") or {}).get("requests", []):
        raw += int(request.get("invalid_response_tool_call_ids", 0) or 0)
    syntax = 0
    scenario = str(record.get("scenario") or "")
    condition = str(record.get("condition") or "")
    seed = int(record.get("trial_seed", -1))
    if scenario and condition and seed >= 0:
        conversation = (
            run_converter_pairs.episode_path(condition, seed, scenario).parent
            / "trajectories"
            / scenario
            / "conversation.json"
        )
        if conversation.is_file():
            messages = json.loads(conversation.read_text(encoding="utf-8"))
            syntax = sum(
                "syntaxerror:"
                in str(message.get("content") or "").lower()
                for message in messages
                if message.get("role") == "tool"
            )
    return raw, syntax


def cluster_bootstrap(
    rows: list[dict[str, Any]], metric: str, ratio: bool
) -> list[float]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        grouped.setdefault(str(row["scenario"]), []).append(row)
    clusters = sorted(grouped)
    rng = random.Random(20260731 if ratio else 20260730)
    values = []
    for _ in range(10_000):
        sample = [
            row
            for _ in clusters
            for row in grouped[rng.choice(clusters)]
        ]
        before = [float(row["before"][metric]) for row in sample]
        after = [float(row["after"][metric]) for row in sample]
        if ratio:
            denominator = sum(before)
            values.append(sum(after) / denominator if denominator else float("inf"))
        else:
            values.append(
                statistics.fmean(a - b for a, b in zip(after, before))
            )
    return [
        summarize.percentile(values, 0.025),
        summarize.percentile(values, 0.975),
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "group",
        choices=("preflight", "preflight-mechanism", "pilot", "confirmation"),
    )
    args = parser.parse_args()
    rows = []
    invalid_cells = []
    id_counts = {
        "before": {
            "raw_invalid": 0,
            "syntax_failures": 0,
            "protocol_history_id_mismatches": 0,
        },
        "converter-fix": {
            "raw_invalid": 0,
            "syntax_failures": 0,
            "protocol_history_id_mismatches": 0,
        },
    }
    for scenario, seed, repetition in run_converter_pairs.cells_for_group(
        args.group
    ):
        before_record = load("before", seed, scenario)
        after_record = load("converter-fix", seed, scenario)
        before = summarize.cell_metrics(before_record)
        after = summarize.cell_metrics(after_record)
        row = {
            "scenario": scenario,
            "seed": seed,
            "repetition": repetition,
            "before": before,
            "after": after,
        }
        rows.append(row)
        if before["status"] != "ok" or after["status"] != "ok":
            invalid_cells.append(f"{scenario}@{seed}")
        for condition, record in (
            ("before", before_record),
            ("converter-fix", after_record),
        ):
            raw, syntax = invalid_id_counts(record)
            id_counts[condition]["raw_invalid"] += raw
            id_counts[condition]["syntax_failures"] += syntax
            id_counts[condition]["protocol_history_id_mismatches"] += sum(
                int(request.get("protocol_history_id_mismatches", 0) or 0)
                for request in (record.get("agent") or {}).get("requests", [])
            )

    aggregate: dict[str, Any] = {}
    for metric in METRICS:
        before_values = [float(row["before"][metric]) for row in rows]
        after_values = [float(row["after"][metric]) for row in rows]
        item = {
            "before_mean": statistics.fmean(before_values),
            "after_mean": statistics.fmean(after_values),
            "after_minus_before_mean": statistics.fmean(
                after - before
                for after, before in zip(after_values, before_values)
            ),
            "scenario_cluster_after_minus_before_95ci": cluster_bootstrap(
                rows, metric, False
            ),
            "before_sum": sum(before_values),
            "after_sum": sum(after_values),
        }
        if metric in {
            "agent_total_tokens",
            "agent_prompt_tokens",
            "agent_completion_tokens",
        }:
            item["after_over_before_sum_ratio"] = (
                sum(after_values) / sum(before_values)
            )
            item["scenario_cluster_after_over_before_95ci"] = cluster_bootstrap(
                rows, metric, True
            )
        aggregate[metric] = item

    similarity = aggregate["similarity"]
    tokens = aggregate["agent_total_tokens"]
    all_cells_valid = not invalid_cells
    mechanism_engaged = (
        id_counts["before"]["syntax_failures"] > 0
        and id_counts["converter-fix"]["raw_invalid"] > 0
        and id_counts["converter-fix"]["syntax_failures"] == 0
        and id_counts["before"]["protocol_history_id_mismatches"] == 0
        and id_counts["converter-fix"]["protocol_history_id_mismatches"] == 0
    )
    outcome_improved = (
        similarity["scenario_cluster_after_minus_before_95ci"][0] > 0
    )
    efficient_noninferior = (
        tokens["scenario_cluster_after_over_before_95ci"][1] < 1
        and similarity["scenario_cluster_after_minus_before_95ci"][0] >= -0.05
    )
    result = {
        "schema": "agentsight.toolsandbox-converter-fix.v1",
        "group": args.group,
        "expected_pairs": len(rows),
        "valid_pairs": len(rows) - len(invalid_cells),
        "scenario_count": len({row["scenario"] for row in rows}),
        "repetitions_per_scenario": (
            1
            if args.group == "preflight"
            else (
                5
                if args.group == "preflight-mechanism"
                else run_converter_pairs.REPETITIONS
            )
        ),
        "invalid_cells": invalid_cells,
        "id_mechanism": id_counts,
        "rows": rows,
        "aggregate": aggregate,
        "support": {
            "all_cells_valid": all_cells_valid,
            "mechanism_engaged_in_both_arms": mechanism_engaged,
            "official_similarity_improvement_interval_above_zero": (
                outcome_improved
            ),
            "token_reduction_with_similarity_noninferiority": efficient_noninferior,
            "pilot_or_confirmation_gate": (
                all_cells_valid
                and mechanism_engaged
                and (outcome_improved or efficient_noninferior)
            ),
        },
    }
    output = HERE / f"converter-{args.group}-summary.json"
    output.write_text(
        json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "group": args.group,
                "pairs": len(rows),
                "id_mechanism": id_counts,
                "similarity": aggregate["similarity"],
                "agent_total_tokens": aggregate["agent_total_tokens"],
                "support": result["support"],
            },
            ensure_ascii=False,
            sort_keys=True,
            indent=2,
        )
    )
    return 0 if not invalid_cells else 1


if __name__ == "__main__":
    raise SystemExit(main())
