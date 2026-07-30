#!/usr/bin/env python3
"""Summarize paired official ToolSandbox outcomes and agent costs."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import random
import statistics
from typing import Any

import run_pairs


HERE = Path(__file__).resolve().parent


def load_episode(condition: str, seed: int, scenario: str) -> dict[str, Any]:
    path = run_pairs.episode_path(condition, seed, scenario)
    if not path.is_file():
        return {"status": "missing"}
    return json.loads(path.read_text(encoding="utf-8"))


def cell_metrics(record: dict[str, Any]) -> dict[str, Any]:
    evaluation = record.get("evaluation") or {}
    agent = record.get("agent") or {}
    usage = agent.get("usage") or {}
    similarity = float(evaluation.get("similarity", 0.0) or 0.0)
    return {
        "status": record.get("status"),
        "similarity": similarity,
        "success": int(similarity == 1.0),
        "milestone_similarity": float(
            evaluation.get("milestone_similarity", 0.0) or 0.0
        ),
        "minefield_similarity": float(
            evaluation.get("minefield_similarity", 0.0) or 0.0
        ),
        "turn_count": int(evaluation.get("turn_count", 0) or 0),
        "agent_total_tokens": int(usage.get("total_tokens", 0) or 0),
        "agent_prompt_tokens": int(usage.get("prompt_tokens", 0) or 0),
        "agent_completion_tokens": int(usage.get("completion_tokens", 0) or 0),
        "agent_model_calls": int(agent.get("model_calls", 0) or 0),
        "agent_tool_calls": int(agent.get("tool_calls", 0) or 0),
    }


def percentile(values: list[float], q: float) -> float:
    ordered = sorted(values)
    if not ordered:
        return float("nan")
    position = q * (len(ordered) - 1)
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    fraction = position - lower
    return ordered[lower] * (1 - fraction) + ordered[upper] * fraction


def paired_ci(rows: list[dict[str, Any]], key: str) -> list[float]:
    if not rows:
        return [float("nan"), float("nan")]
    rng = random.Random(20260729)
    deltas = []
    for _ in range(10_000):
        sample = [rng.choice(rows) for _ in rows]
        deltas.append(
            statistics.fmean(
                float(row["after"][key]) - float(row["before"][key])
                for row in sample
            )
        )
    return [percentile(deltas, 0.025), percentile(deltas, 0.975)]


def paired_ratio_ci(rows: list[dict[str, Any]], key: str) -> list[float]:
    if not rows:
        return [float("nan"), float("nan")]
    rng = random.Random(20260730)
    ratios = []
    for _ in range(10_000):
        sample = [rng.choice(rows) for _ in rows]
        before = sum(float(row["before"][key]) for row in sample)
        after = sum(float(row["after"][key]) for row in sample)
        ratios.append(after / before if before else float("inf"))
    return [percentile(ratios, 0.025), percentile(ratios, 0.975)]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("group", choices=("preflight", "pilot", "confirmation"))
    args = parser.parse_args()
    scenarios = {
        "preflight": run_pairs.PREFLIGHT,
        "pilot": run_pairs.PILOT,
        "confirmation": run_pairs.CONFIRMATION,
    }[args.group]
    rows = []
    invalid = []
    for index, scenario in enumerate(scenarios):
        seed = run_pairs.seed_for(args.group, index)
        before = cell_metrics(load_episode("no-policy", seed, scenario))
        after = cell_metrics(load_episode("profile-policy", seed, scenario))
        row = {"scenario": scenario, "seed": seed, "before": before, "after": after}
        rows.append(row)
        if before["status"] != "ok" or after["status"] != "ok":
            invalid.append(scenario)
    valid = [row for row in rows if row["scenario"] not in set(invalid)]
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
    aggregate: dict[str, Any] = {}
    for metric in metrics:
        before_values = [float(row["before"][metric]) for row in rows]
        after_values = [float(row["after"][metric]) for row in rows]
        metric_summary = {
            "before_mean": statistics.fmean(before_values) if before_values else None,
            "after_mean": statistics.fmean(after_values) if after_values else None,
            "after_minus_before_mean": (
                statistics.fmean(a - b for a, b in zip(after_values, before_values))
                if before_values
                else None
            ),
            "after_minus_before_95ci": paired_ci(rows, metric),
            "before_sum": sum(before_values),
            "after_sum": sum(after_values),
        }
        if metric in {
            "agent_total_tokens",
            "agent_prompt_tokens",
            "agent_completion_tokens",
        }:
            metric_summary["after_over_before_sum_ratio"] = (
                sum(after_values) / sum(before_values)
                if sum(before_values)
                else None
            )
            metric_summary["after_over_before_95ci"] = paired_ratio_ci(rows, metric)
        aggregate[metric] = metric_summary
    result = {
        "schema": "agentsight.toolsandbox.profile-policy-before-after.v1",
        "group": args.group,
        "expected_pairs": len(scenarios),
        "valid_pairs": len(valid),
        "invalid_scenarios": invalid,
        "policy_source": str(run_pairs.POLICY.relative_to(run_pairs.REPO)),
        "rows": rows,
        "aggregate": aggregate,
    }
    output = HERE / f"{args.group}-summary.json"
    output.write_text(
        json.dumps(result, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(result["aggregate"], indent=2, sort_keys=True))
    print(f"valid pairs: {len(valid)}/{len(scenarios)}")
    print(f"wrote {output}")
    return 0 if not invalid else 1


if __name__ == "__main__":
    raise SystemExit(main())
