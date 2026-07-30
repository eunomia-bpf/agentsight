#!/usr/bin/env python3
"""Summarize paired official outcomes for the profile-derived call-ID fix."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import statistics

import run_idfix_pairs
import run_pairs
import summarize


HERE = Path(__file__).resolve().parent
IDENTIFIER = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def load(condition: str, seed: int, scenario: str):
    path = run_idfix_pairs.episode_path(condition, seed, scenario)
    return json.loads(path.read_text(encoding="utf-8")) if path.is_file() else {"status": "missing"}


def raw_invalid_ids(
    record: dict, condition: str, seed: int, scenario: str
) -> int:
    requests = (record.get("agent") or {}).get("requests", [])
    recorded = [
        request.get("invalid_response_tool_call_ids")
        for request in requests
        if "invalid_response_tool_call_ids" in request
    ]
    if recorded:
        return sum(int(value or 0) for value in recorded)
    if condition == "id-fix":
        return sum(
            int(request.get("normalized_tool_call_ids", 0) or 0)
            for request in requests
        )
    conversation = (
        run_idfix_pairs.episode_path(condition, seed, scenario).parent
        / "trajectories"
        / scenario
        / "conversation.json"
    )
    if not conversation.is_file():
        return 0
    messages = json.loads(conversation.read_text(encoding="utf-8"))
    return sum(
        not bool(IDENTIFIER.fullmatch(str(call.get("id") or "")))
        for message in messages
        for call in (message.get("tool_calls") or [])
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "group",
        choices=("preflight", "pilot", "pilot-expanded", "confirmation"),
    )
    args = parser.parse_args()
    rows = []
    invalid = []
    normalized_ids = 0
    invalid_ids = {"before": 0, "id-fix": 0}
    for scenario, seed, repetition in run_idfix_pairs.cells_for_group(args.group):
        before_record = load("before", seed, scenario)
        after_record = load("id-fix", seed, scenario)
        before = summarize.cell_metrics(before_record)
        after = summarize.cell_metrics(after_record)
        rows.append(
            {
                "scenario": scenario,
                "seed": seed,
                "repetition": repetition,
                "before": before,
                "after": after,
            }
        )
        if before["status"] != "ok" or after["status"] != "ok":
            invalid.append(f"{scenario}@{seed}")
        invalid_ids["before"] += raw_invalid_ids(
            before_record, "before", seed, scenario
        )
        invalid_ids["id-fix"] += raw_invalid_ids(
            after_record, "id-fix", seed, scenario
        )
        for request in (after_record.get("agent") or {}).get("requests", []):
            normalized_ids += int(request.get("normalized_tool_call_ids", 0) or 0)
    metrics = (
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
    aggregate = {}
    for metric in metrics:
        before_values = [float(row["before"][metric]) for row in rows]
        after_values = [float(row["after"][metric]) for row in rows]
        item = {
            "before_mean": statistics.fmean(before_values),
            "after_mean": statistics.fmean(after_values),
            "after_minus_before_mean": statistics.fmean(
                after - before
                for after, before in zip(after_values, before_values)
            ),
            "after_minus_before_95ci": summarize.paired_ci(rows, metric),
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
            item["after_over_before_95ci"] = summarize.paired_ratio_ci(rows, metric)
        aggregate[metric] = item
    result = {
        "schema": "agentsight.toolsandbox-profile-derived-id-fix.v1",
        "group": args.group,
        "expected_pairs": len(rows),
        "valid_pairs": len(rows) - len(invalid),
        "invalid_scenarios": invalid,
        "raw_invalid_agent_tool_call_ids": invalid_ids,
        "normalized_agent_tool_call_ids": normalized_ids,
        "rows": rows,
        "aggregate": aggregate,
    }
    output = HERE / f"idfix-{args.group}-summary.json"
    output.write_text(
        json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2))
    return 0 if not invalid else 1


if __name__ == "__main__":
    raise SystemExit(main())
