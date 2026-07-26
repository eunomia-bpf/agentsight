#!/usr/bin/env python3
"""Recompute the P0 paper-number ledger from released final-HEAD CSV/JSON rows."""

from __future__ import annotations

import csv
import json
import math
from collections import Counter, defaultdict
from pathlib import Path


REPO = Path(__file__).resolve().parents[4]
FINAL = REPO / "docs/tmp/build-and-evaluate/rq1-rq4-recompute-final"
EXTENSIONS = REPO / "docs/tmp/build-and-evaluate/rq-extensions-final-20260726"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def average_ranks(values: list[float]) -> list[float]:
    order = sorted(range(len(values)), key=values.__getitem__)
    ranks = [0.0] * len(values)
    index = 0
    while index < len(order):
        stop = index
        while (
            stop + 1 < len(order)
            and values[order[stop + 1]] == values[order[index]]
        ):
            stop += 1
        rank = (index + stop) / 2 + 1
        for position in range(index, stop + 1):
            ranks[order[position]] = rank
        index = stop + 1
    return ranks


def spearman(left: list[float], right: list[float]) -> float:
    left_ranks = average_ranks(left)
    right_ranks = average_ranks(right)
    left_mean = sum(left_ranks) / len(left_ranks)
    right_mean = sum(right_ranks) / len(right_ranks)
    numerator = sum(
        (x - left_mean) * (y - right_mean)
        for x, y in zip(left_ranks, right_ranks, strict=True)
    )
    denominator = math.sqrt(
        sum((x - left_mean) ** 2 for x in left_ranks)
        * sum((y - right_mean) ** 2 for y in right_ranks)
    )
    return numerator / denominator


def percent_range(values: list[float]) -> str:
    return f"{min(values) * 100:.1f}--{max(values) * 100:.1f}%"


def main() -> None:
    rq1 = read_csv(FINAL / "rq1-raw/rq1-summary.csv")
    artifacts = read_csv(FINAL / "rq1-raw/rq1-artifacts.csv")
    mutations = read_csv(FINAL / "rq1-raw/rq1-mutations.csv")
    rq2_coverage = read_csv(FINAL / "rq2/raw/rq2-coverage.csv")
    rq2_cycles = read_csv(FINAL / "rq2/raw/rq2-cycles.csv")
    rq3 = read_csv(FINAL / "rq3/raw/rq3-summary.csv")
    rq4_components = read_csv(FINAL / "rq4/raw/rq4-components.csv")
    rq4_boundaries = read_csv(FINAL / "rq4/raw/rq4-boundaries.csv")
    extensions = json.loads(
        (EXTENSIONS / "rq-summary.json").read_text(encoding="utf-8")
    )

    sessions = sum(int(row["included_sessions"]) for row in rq1)
    actions = sum(int(row["tool_actions"]) for row in rq1)
    attributed_sessions = sum(int(row["attributed_sessions"]) for row in rq1)
    attributed_actions = sum(int(row["attributed_tool_actions"]) for row in rq1)
    reuse = [
        int(row["reuse_observed"]) / int(row["reuse_eligible"]) for row in rq1
    ]
    rho = spearman(
        [float(row["attributed_tool_actions"]) for row in rq1],
        reuse,
    )

    print("# P0 final-HEAD paper-number ledger")
    print(
        "\nRQ1 corpus: "
        f"{sessions} sessions; {actions} actions; "
        f"{attributed_sessions}/{attributed_actions} attributed; "
        f"{len(artifacts)} artifacts; {len(mutations)} mutations; "
        f"reuse {min(reuse) * 100:.2f}--{max(reuse) * 100:.2f}%; "
        f"Spearman rho={rho:.4f}"
    )
    for row in rq1:
        print(
            f"RQ1 {row['project']}: "
            f"persistence {row['introduced_persisted']}/{row['introduced_eligible']}; "
            f"reuse {row['reuse_observed']}/{row['reuse_eligible']}; "
            f"validation {row['validation_observed']}/{row['validation_eligible']}"
        )

    qualified = sum(
        row["qualified_with_success"].lower() == "true" for row in rq2_coverage
    )
    complete_by_lane: dict[tuple[str, str], list[int]] = defaultdict(list)
    for row in rq2_cycles:
        if row["interval_type"] == "complete":
            complete_by_lane[(row["project"], row["worktree_id"])].append(
                int(row["mutation_rows"])
            )
    zero_rates = [
        sum(value == 0 for value in values) / len(values)
        for values in complete_by_lane.values()
    ]
    lane_maxima = [max(values) for values in complete_by_lane.values()]
    print(
        "\nRQ2: "
        f"{qualified}/{len(rq2_coverage)} recognized-success coverage; "
        f"{len(complete_by_lane)} complete lanes; "
        f"zero-mutation {percent_range(zero_rates)}; "
        f"lane maxima {min(lane_maxima)}--{max(lane_maxima)}"
    )

    repeat_rates = [float(row["repeat_episode_fraction"]) for row in rq3]
    concentration = [float(row["top_10pct_episode_share"]) for row in rq3]
    print(
        "\nRQ3/repeated mutation: "
        f"{sum(int(row['mutation_episodes']) for row in rq3)} episodes/"
        f"{sum(int(row['raw_mutation_rows']) for row in rq3)} source rows; "
        f"repeat {percent_range(repeat_rates)}; "
        f"top-10% share {percent_range(concentration)}"
    )

    component_counts = Counter(row["project"] for row in rq4_components)
    boundary_counts = Counter(row["project"] for row in rq4_boundaries)
    print(
        f"\nRQ4: {len(rq4_components)} components/"
        f"{len(rq4_boundaries)} boundaries"
    )
    for project in component_counts:
        print(
            f"RQ4 {project}: "
            f"{component_counts[project]} components/"
            f"{boundary_counts[project]} boundaries"
        )

    for variant in ("action_gap_gt_100", "time_gap_gt_24h"):
        rows = [row for row in extensions["rq1"] if row["variant"] == variant]
        all_shares = [float(row["revived_share_all_artifacts"]) for row in rows]
        multi_shares = [
            float(row["revived_share_multi_touch_artifacts"]) for row in rows
        ]
        print(
            f"\nRQ1 extension {variant}: "
            f"revived/all {percent_range(all_shares)}; "
            f"revived/multi-touch {percent_range(multi_shares)}; "
            f"{sum(int(row['revival_transitions']) for row in rows)} transitions; "
            f"{sum(int(row['mutation_revivals']) for row in rows)} mutation revivals"
        )

    turnover = {
        (row["pooling"], row["config"], row["entity_type"]): row
        for row in extensions["rq3_turnover_pooled"]
    }
    for pooling, config in (
        ("transition_weighted_micro", "main_100_50"),
        ("project_median", "main_100_50"),
        ("transition_weighted_micro", "sensitivity_100_100"),
    ):
        artifact = turnover[(pooling, config, "artifact")]
        module = turnover[(pooling, config, "module")]
        print(
            f"\nRQ3 extension turnover {pooling}/{config}: "
            f"{artifact['valid_adjacent_pairs']} pairs; "
            f"top-1 {artifact['top1_change_fraction']:.1%}/"
            f"{module['top1_change_fraction']:.1%}; "
            f"any-top-5 {artifact['top5_any_change_fraction']:.1%}/"
            f"{module['top5_any_change_fraction']:.1%}; "
            f"replacement {artifact['mean_top5_replacement_fraction']:.1%}/"
            f"{module['mean_top5_replacement_fraction']:.1%}"
        )

    cooling = {
        (
            row["pooling"],
            row["config"],
            row["entity_type"],
            int(row["lag_windows"]),
        ): row
        for row in extensions["rq3_cooling_pooled"]
    }
    for config, lag in (
        ("main_100_50", 1),
        ("main_100_50", 8),
        ("sensitivity_100_100", 8),
    ):
        artifact = cooling[
            ("membership_weighted_micro", config, "artifact", lag)
        ]
        module = cooling[("membership_weighted_micro", config, "module", lag)]
        print(
            f"\nRQ3 extension cooling {config}/lag-{lag}: "
            f"endpoint {artifact['endpoint_retention_fraction']:.1%}/"
            f"{module['endpoint_retention_fraction']:.1%}; "
            f"continuous {artifact['continuous_retention_fraction']:.1%}/"
            f"{module['continuous_retention_fraction']:.1%}"
        )

    assert (sessions, actions, attributed_sessions, attributed_actions) == (
        551,
        181_303,
        551,
        176_288,
    )
    assert (len(artifacts), len(mutations)) == (5_746, 13_906)
    assert qualified == len(rq2_coverage) == 6
    assert round(max(zero_rates) * 100, 1) == 86.1
    assert (len(rq4_components), len(rq4_boundaries)) == (121, 111)


if __name__ == "__main__":
    main()
