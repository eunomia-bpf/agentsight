#!/usr/bin/env python3
"""Re-review RQ2 validation response over the six final-HEAD cases.

The analysis is descriptive.  A "mutation accumulation" is a ledger count of
confirmed mutation rows between recognized validation events; it is not an
estimate of outstanding work, validation coverage, correctness, or progress.
Event distances are counts of strictly intervening worktree-lane events.
"""

from __future__ import annotations

import argparse
import bisect
import csv
import hashlib
import math
import statistics
from collections import Counter, defaultdict
from pathlib import Path
from typing import Iterable


EXPECTED_INPUTS = {
    "rq2-trajectory.csv": "ec8065c8e2ce1f1d3e78d62d3522f5dae4293999238171bb039887371e482a61",
    "rq2-cycles.csv": "dfd7504aab265035fc0872c05de0f03783490ced59e9869d1aa26d86079c13fe",
    "rq2-coverage.csv": "1f8f0275dabe62037b5e270fa2513a0d0d46f146a71ae5af72517bfd2c4525ae",
}

PROJECT_ORDER = [
    "agentsight",
    "ActPlane",
    "bpf-developer-tutorial",
    "eunomia.dev",
    "agentskill-observability-paper",
    "academic-writing-skills",
]

# These are the observable case roles in docs/evaluation.md's corpus table.
PROJECT_TYPES = {
    "agentsight": "systems/research",
    "ActPlane": "systems/research",
    "bpf-developer-tutorial": "tutorial/code/docs",
    "eunomia.dev": "content/software",
    "agentskill-observability-paper": "auto research",
    "academic-writing-skills": "skill/harness development",
}

STATUSES = ("ok", "fail", "observed")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def write_csv(path: Path, rows: list[dict[str, object]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, extrasaction="raise")
        writer.writeheader()
        writer.writerows(rows)


def as_bool(value: str) -> bool:
    return value.lower() == "true"


def optional_int(value: object) -> int | None:
    if value == "" or value is None:
        return None
    return int(value)


def format_number(value: float | int | None, digits: int = 3) -> object:
    if value is None:
        return ""
    if isinstance(value, int):
        return value
    return f"{value:.{digits}f}"


def quantile_type7(values: Iterable[int | float], fraction: float) -> float | None:
    ordered = sorted(values)
    if not ordered:
        return None
    if len(ordered) == 1:
        return float(ordered[0])
    position = (len(ordered) - 1) * fraction
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return float(ordered[lower])
    weight = position - lower
    return float(ordered[lower] * (1 - weight) + ordered[upper] * weight)


def median(values: Iterable[int | float]) -> float | None:
    materialized = list(values)
    return float(statistics.median(materialized)) if materialized else None


def previous_index(indices: list[int], current: int) -> int | None:
    position = bisect.bisect_left(indices, current) - 1
    return indices[position] if position >= 0 else None


def next_index(indices: list[int], current: int) -> int | None:
    position = bisect.bisect_right(indices, current)
    return indices[position] if position < len(indices) else None


def between_sum(prefix: list[int], left: int, right: int) -> int:
    """Sum values at indices strictly between left and right."""
    if right <= left + 1:
        return 0
    return prefix[right] - prefix[left + 1]


def event_order(next_mutation: int | None, next_attempt: int | None) -> str:
    if next_mutation is None and next_attempt is None:
        return "no_relevant_event_before_censor"
    if next_attempt is None:
        return "only_mutation_before_censor"
    if next_mutation is None:
        return "only_validation_before_censor"
    if next_mutation < next_attempt:
        return "mutation_first"
    if next_attempt < next_mutation:
        return "validation_first"
    return "co_observed_mutation_and_validation"


def self_check() -> None:
    values = [2, 0, 3, 0, 5]
    prefix = [0]
    for value in values:
        prefix.append(prefix[-1] + value)
    assert between_sum(prefix, 0, 4) == 3
    assert between_sum(prefix, 1, 3) == 3
    assert between_sum(prefix, 2, 3) == 0
    assert previous_index([0, 2, 4], 2) == 0
    assert next_index([0, 2, 4], 2) == 4
    assert event_order(3, 4) == "mutation_first"
    assert event_order(3, 3) == "co_observed_mutation_and_validation"
    assert quantile_type7([0, 10], 0.9) == 9


def verify_inputs(input_dir: Path) -> list[dict[str, object]]:
    manifest = []
    for filename, expected in EXPECTED_INPUTS.items():
        path = input_dir / filename
        actual = sha256(path)
        if actual != expected:
            raise ValueError(
                f"final-HEAD input hash mismatch for {path}: {actual} != {expected}"
            )
        manifest.append(
            {
                "file": filename,
                "sha256": actual,
                "bytes": path.stat().st_size,
                "verification": "match",
            }
        )
    return manifest


def normalize_trajectory(
    rows: list[dict[str, str]],
) -> tuple[
    dict[tuple[str, str], list[dict[str, object]]],
    Counter[str],
    dict[str, Counter[str]],
]:
    lanes: dict[tuple[str, str], list[dict[str, object]]] = defaultdict(list)
    home_actions: Counter[str] = Counter()
    vendor_actions: dict[str, Counter[str]] = defaultdict(Counter)
    for row in rows:
        project = row["project"]
        normalized: dict[str, object] = {
            "project": project,
            "worktree_id": row["worktree_id"],
            "home_worktree": as_bool(row["home_worktree"]),
            "action_rank": int(row["action_rank"]),
            "event_index": int(row["event_index"]),
            "event_id": row["event_id"],
            "ts_ms": int(row["ts_ms"]),
            "session_id": row["session_id"],
            "vendor": row["vendor"],
            "effect": row["effect"],
            "status": row["status"],
            "mutation_rows": int(row["mutation_rows"]),
            "co_observed_mutation_rows": int(row["co_observed_mutation_rows"]),
        }
        lanes[(project, row["worktree_id"])].append(normalized)
        if normalized["home_worktree"]:
            home_actions[project] += 1
            vendor_actions[project][row["vendor"]] += 1

    for (project, worktree), lane in lanes.items():
        lane.sort(key=lambda row: int(row["action_rank"]))
        ranks = [int(row["action_rank"]) for row in lane]
        if ranks != list(range(1, len(lane) + 1)):
            raise ValueError(f"non-consecutive action ranks in {project}/{worktree}")
        event_ids = [str(row["event_id"]) for row in lane]
        if len(event_ids) != len(set(event_ids)):
            raise ValueError(f"duplicate lane event in {project}/{worktree}")
    return lanes, home_actions, vendor_actions


def derive_validation_events(
    lanes: dict[tuple[str, str], list[dict[str, object]]]
) -> list[dict[str, object]]:
    result: list[dict[str, object]] = []
    for (project, worktree), lane in lanes.items():
        attempt_indices = [
            index for index, row in enumerate(lane) if row["effect"] == "test"
        ]
        success_indices = [
            index
            for index in attempt_indices
            if lane[index]["status"] == "ok"
        ]
        mutation_indices = [
            index
            for index, row in enumerate(lane)
            if int(row["mutation_rows"]) > 0
        ]
        status_indices = {
            status: [
                index
                for index in attempt_indices
                if lane[index]["status"] == status
            ]
            for status in STATUSES
        }
        prefix = [0]
        for row in lane:
            prefix.append(prefix[-1] + int(row["mutation_rows"]))

        for index in attempt_indices:
            row = lane[index]
            status = str(row["status"])
            prev_attempt = previous_index(attempt_indices, index)
            next_attempt = next_index(attempt_indices, index)
            prev_success = previous_index(success_indices, index)
            next_success = next_index(success_indices, index)
            prev_same = previous_index(status_indices[status], index)
            next_mutation = next_index(mutation_indices, index)

            def gap(left: int | None, right: int | None) -> int | str:
                if left is None or right is None:
                    return ""
                return right - left - 1

            def hours(left: int | None, right: int | None) -> float | str:
                if left is None or right is None:
                    return ""
                return (
                    int(lane[right]["ts_ms"]) - int(lane[left]["ts_ms"])
                ) / 3_600_000

            result.append(
                {
                    "project": project,
                    "project_type": PROJECT_TYPES[project],
                    "worktree_id": worktree,
                    "event_id": row["event_id"],
                    "action_rank": row["action_rank"],
                    "ts_ms": row["ts_ms"],
                    "session_id": row["session_id"],
                    "vendor": row["vendor"],
                    "status": status,
                    "same_event_mutation_rows": row["mutation_rows"],
                    "co_observed_mutation_rows": row[
                        "co_observed_mutation_rows"
                    ],
                    "previous_attempt_status": (
                        lane[prev_attempt]["status"]
                        if prev_attempt is not None
                        else ""
                    ),
                    "previous_attempt_gap_events": gap(prev_attempt, index),
                    "previous_attempt_gap_hours": hours(prev_attempt, index),
                    "previous_same_status_gap_events": gap(prev_same, index),
                    "previous_same_status_gap_hours": hours(prev_same, index),
                    "next_attempt_status": (
                        lane[next_attempt]["status"]
                        if next_attempt is not None
                        else ""
                    ),
                    "next_attempt_gap_events": gap(index, next_attempt),
                    "next_attempt_gap_hours": hours(index, next_attempt),
                    "adjacent_pre_mutation_rows": (
                        between_sum(prefix, prev_attempt, index)
                        if prev_attempt is not None
                        else ""
                    ),
                    "adjacent_post_mutation_rows": (
                        between_sum(prefix, index, next_attempt)
                        if next_attempt is not None
                        else ""
                    ),
                    "previous_success_gap_events": gap(prev_success, index),
                    "mutation_rows_since_previous_success": (
                        between_sum(prefix, prev_success, index)
                        if prev_success is not None
                        else ""
                    ),
                    "next_success_gap_events": gap(index, next_success),
                    "mutation_rows_until_next_success": (
                        between_sum(prefix, index, next_success)
                        if next_success is not None
                        else ""
                    ),
                    "next_mutation_gap_events": gap(index, next_mutation),
                    "next_mutation_gap_hours": hours(index, next_mutation),
                    "next_event_order": event_order(next_mutation, next_attempt),
                    "right_censored_next_mutation": next_mutation is None,
                    "right_censored_next_attempt": next_attempt is None,
                    "right_censored_next_success": next_success is None,
                }
            )
    result.sort(
        key=lambda row: (
            PROJECT_ORDER.index(str(row["project"])),
            str(row["worktree_id"]),
            int(row["action_rank"]),
        )
    )
    return result


def values(rows: list[dict[str, object]], field: str) -> list[float]:
    result = []
    for row in rows:
        value = row[field]
        if value != "":
            result.append(float(value))
    return result


def summarize_outcome(
    project: str,
    status: str,
    rows: list[dict[str, object]],
    attributed_actions: int,
    all_attempts: int,
) -> dict[str, object]:
    selected = [row for row in rows if row["status"] == status]
    before = values(selected, "adjacent_pre_mutation_rows")
    after = values(selected, "adjacent_post_mutation_rows")
    paired_deltas = [
        float(row["adjacent_post_mutation_rows"])
        - float(row["adjacent_pre_mutation_rows"])
        for row in selected
        if row["adjacent_pre_mutation_rows"] != ""
        and row["adjacent_post_mutation_rows"] != ""
    ]
    paired_increase = sum(delta > 0 for delta in paired_deltas)
    paired_equal = sum(delta == 0 for delta in paired_deltas)
    paired_decrease = sum(delta < 0 for delta in paired_deltas)
    orders = Counter(str(row["next_event_order"]) for row in selected)
    comparable = orders["mutation_first"] + orders["validation_first"]
    return {
        "project": project,
        "project_type": PROJECT_TYPES[project],
        "status": status,
        "attempt_count": len(selected),
        "attempt_share_pct": format_number(
            100 * len(selected) / all_attempts if all_attempts else None
        ),
        "attempts_per_1000_attributed_actions": format_number(
            1000 * len(selected) / attributed_actions
            if attributed_actions
            else None
        ),
        "previous_attempt_gap_n": len(
            values(selected, "previous_attempt_gap_events")
        ),
        "previous_attempt_gap_events_median": format_number(
            median(values(selected, "previous_attempt_gap_events"))
        ),
        "previous_attempt_gap_events_p90": format_number(
            quantile_type7(values(selected, "previous_attempt_gap_events"), 0.9)
        ),
        "previous_same_status_gap_n": len(
            values(selected, "previous_same_status_gap_events")
        ),
        "previous_same_status_gap_events_median": format_number(
            median(values(selected, "previous_same_status_gap_events"))
        ),
        "previous_same_status_gap_hours_median": format_number(
            median(values(selected, "previous_same_status_gap_hours"))
        ),
        "adjacent_pre_mutation_rows_n": len(before),
        "adjacent_pre_mutation_rows_median": format_number(median(before)),
        "adjacent_pre_mutation_rows_p90": format_number(
            quantile_type7(before, 0.9)
        ),
        "adjacent_post_mutation_rows_n": len(after),
        "adjacent_post_mutation_rows_median": format_number(median(after)),
        "adjacent_post_mutation_rows_p90": format_number(
            quantile_type7(after, 0.9)
        ),
        "paired_post_minus_pre_n": len(paired_deltas),
        "paired_post_minus_pre_mutation_rows_median": format_number(
            median(paired_deltas)
        ),
        "paired_post_gt_pre_n": paired_increase,
        "paired_post_eq_pre_n": paired_equal,
        "paired_post_lt_pre_n": paired_decrease,
        "paired_post_gt_pre_pct": format_number(
            100 * paired_increase / len(paired_deltas)
            if paired_deltas
            else None
        ),
        "paired_post_lt_pre_pct": format_number(
            100 * paired_decrease / len(paired_deltas)
            if paired_deltas
            else None
        ),
        "mutation_rows_since_previous_success_n": len(
            values(selected, "mutation_rows_since_previous_success")
        ),
        "mutation_rows_since_previous_success_median": format_number(
            median(values(selected, "mutation_rows_since_previous_success"))
        ),
        "mutation_rows_until_next_success_n": len(
            values(selected, "mutation_rows_until_next_success")
        ),
        "mutation_rows_until_next_success_median": format_number(
            median(values(selected, "mutation_rows_until_next_success"))
        ),
        "next_mutation_observed_n": len(
            values(selected, "next_mutation_gap_events")
        ),
        "next_mutation_gap_events_median": format_number(
            median(values(selected, "next_mutation_gap_events"))
        ),
        "next_mutation_gap_events_p90": format_number(
            quantile_type7(values(selected, "next_mutation_gap_events"), 0.9)
        ),
        "next_attempt_observed_n": len(
            values(selected, "next_attempt_gap_events")
        ),
        "next_attempt_gap_events_median": format_number(
            median(values(selected, "next_attempt_gap_events"))
        ),
        "next_success_observed_n": len(
            values(selected, "next_success_gap_events")
        ),
        "next_success_gap_events_median": format_number(
            median(values(selected, "next_success_gap_events"))
        ),
        "next_order_mutation_first_n": orders["mutation_first"],
        "next_order_validation_first_n": orders["validation_first"],
        "next_order_co_observed_n": orders[
            "co_observed_mutation_and_validation"
        ],
        "next_order_only_mutation_n": orders["only_mutation_before_censor"],
        "next_order_only_validation_n": orders[
            "only_validation_before_censor"
        ],
        "next_order_no_relevant_n": orders[
            "no_relevant_event_before_censor"
        ],
        "mutation_first_comparable_n": comparable,
        "mutation_first_share_of_distinct_observed_order_pct": format_number(
            100 * orders["mutation_first"] / comparable if comparable else None
        ),
    }


def derive_outcome_summary(
    event_rows: list[dict[str, object]], home_actions: Counter[str]
) -> list[dict[str, object]]:
    by_project: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in event_rows:
        by_project[str(row["project"])].append(row)
    result = []
    for project in PROJECT_ORDER:
        project_rows = by_project[project]
        for status in STATUSES:
            result.append(
                summarize_outcome(
                    project,
                    status,
                    project_rows,
                    home_actions[project],
                    len(project_rows),
                )
            )
    return result


def vendor_profile(counter: Counter[str]) -> tuple[str, str, str]:
    total = sum(counter.values())
    ordered = sorted(counter.items(), key=lambda item: (-item[1], item[0]))
    composition = ";".join(
        f"{vendor}:{count}/{total}({100 * count / total:.1f}%)"
        for vendor, count in ordered
    )
    dominant = ordered[0][0]
    profile = (
        f"pure_{dominant}"
        if len(ordered) == 1
        else f"mixed_{dominant}_dominant"
    )
    return dominant, profile, composition


def derive_vendor_summary(
    event_rows: list[dict[str, object]],
    vendor_actions: dict[str, Counter[str]],
) -> list[dict[str, object]]:
    attempts: dict[tuple[str, str], Counter[str]] = defaultdict(Counter)
    for row in event_rows:
        attempts[(str(row["project"]), str(row["vendor"]))][
            str(row["status"])
        ] += 1
    result = []
    for project in PROJECT_ORDER:
        total_actions = sum(vendor_actions[project].values())
        for vendor, action_count in sorted(
            vendor_actions[project].items(), key=lambda item: (-item[1], item[0])
        ):
            counts = attempts[(project, vendor)]
            attempt_count = sum(counts.values())
            result.append(
                {
                    "project": project,
                    "project_type": PROJECT_TYPES[project],
                    "vendor": vendor,
                    "attributed_actions": action_count,
                    "project_action_share_pct": format_number(
                        100 * action_count / total_actions
                    ),
                    "recognized_attempts": attempt_count,
                    "recognized_success": counts["ok"],
                    "recognized_fail": counts["fail"],
                    "recognized_observed_unknown": counts["observed"],
                    "attempts_per_1000_vendor_actions": format_number(
                        1000 * attempt_count / action_count
                    ),
                }
            )
    return result


def derive_project_summary(
    event_rows: list[dict[str, object]],
    outcome_rows: list[dict[str, object]],
    cycles: list[dict[str, str]],
    home_actions: Counter[str],
    vendor_actions: dict[str, Counter[str]],
) -> list[dict[str, object]]:
    events_by_project: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in event_rows:
        events_by_project[str(row["project"])].append(row)
    outcomes = {
        (str(row["project"]), str(row["status"])): row for row in outcome_rows
    }
    complete_cycles: dict[str, list[int]] = defaultdict(list)
    for row in cycles:
        if row["interval_type"] == "complete":
            complete_cycles[row["project"]].append(int(row["mutation_rows"]))

    result = []
    for project in PROJECT_ORDER:
        rows = events_by_project[project]
        status_counts = Counter(str(row["status"]) for row in rows)
        cycle_values = complete_cycles[project]
        dominant, profile, composition = vendor_profile(vendor_actions[project])
        base: dict[str, object] = {
            "project": project,
            "project_type": PROJECT_TYPES[project],
            "vendor_profile": profile,
            "dominant_vendor": dominant,
            "vendor_action_composition": composition,
            "attributed_actions": home_actions[project],
            "recognized_attempts": len(rows),
            "recognized_success": status_counts["ok"],
            "recognized_fail": status_counts["fail"],
            "recognized_observed_unknown": status_counts["observed"],
            "attempts_per_1000_attributed_actions": format_number(
                1000 * len(rows) / home_actions[project]
            ),
            "complete_inter_success_intervals": len(cycle_values),
            "zero_mutation_intervals_pct": format_number(
                100 * sum(value == 0 for value in cycle_values) / len(cycle_values)
                if cycle_values
                else None
            ),
            "inter_success_mutation_rows_median": format_number(
                median(cycle_values)
            ),
            "inter_success_mutation_rows_p90": format_number(
                quantile_type7(cycle_values, 0.9)
            ),
            "inter_success_mutation_rows_max": (
                max(cycle_values) if cycle_values else ""
            ),
        }
        for status in ("ok", "fail"):
            summary = outcomes[(project, status)]
            prefix = "success" if status == "ok" else "fail"
            for source_field, target_suffix in [
                (
                    "previous_same_status_gap_events_median",
                    "same_outcome_gap_events_median",
                ),
                (
                    "previous_same_status_gap_hours_median",
                    "same_outcome_gap_hours_median",
                ),
                (
                    "adjacent_pre_mutation_rows_median",
                    "adjacent_pre_mutation_rows_median",
                ),
                (
                    "adjacent_post_mutation_rows_median",
                    "adjacent_post_mutation_rows_median",
                ),
                (
                    "paired_post_minus_pre_mutation_rows_median",
                    "paired_post_minus_pre_mutation_rows_median",
                ),
                (
                    "mutation_rows_since_previous_success_median",
                    "mutation_rows_since_previous_success_median",
                ),
                (
                    "mutation_rows_until_next_success_median",
                    "mutation_rows_until_next_success_median",
                ),
                (
                    "next_mutation_gap_events_median",
                    "next_mutation_gap_events_median",
                ),
                (
                    "next_attempt_gap_events_median",
                    "next_attempt_gap_events_median",
                ),
                (
                    "mutation_first_share_of_distinct_observed_order_pct",
                    "mutation_first_share_pct",
                ),
            ]:
                base[f"{prefix}_{target_suffix}"] = summary[source_field]
            base[f"{prefix}_mutation_first_comparable_n"] = summary[
                "mutation_first_comparable_n"
            ]
            base[f"{prefix}_paired_post_gt_pre_n"] = summary[
                "paired_post_gt_pre_n"
            ]
            base[f"{prefix}_paired_post_eq_pre_n"] = summary[
                "paired_post_eq_pre_n"
            ]
            base[f"{prefix}_paired_post_lt_pre_n"] = summary[
                "paired_post_lt_pre_n"
            ]
        result.append(base)
    return result


def derive_lane_summary(
    lanes: dict[tuple[str, str], list[dict[str, object]]],
    event_rows: list[dict[str, object]],
    cycles: list[dict[str, str]],
) -> list[dict[str, object]]:
    events_by_lane: dict[
        tuple[str, str], list[dict[str, object]]
    ] = defaultdict(list)
    for row in event_rows:
        events_by_lane[(str(row["project"]), str(row["worktree_id"]))].append(row)
    complete_cycles: dict[tuple[str, str], list[int]] = defaultdict(list)
    for row in cycles:
        if row["interval_type"] == "complete":
            complete_cycles[(row["project"], row["worktree_id"])].append(
                int(row["mutation_rows"])
            )

    result = []
    for (project, worktree), lane in sorted(
        lanes.items(),
        key=lambda item: (
            PROJECT_ORDER.index(item[0][0]),
            item[0][1],
        ),
    ):
        attempts = events_by_lane[(project, worktree)]
        status_counts = Counter(str(row["status"]) for row in attempts)
        cycle_values = complete_cycles[(project, worktree)]
        base: dict[str, object] = {
            "project": project,
            "project_type": PROJECT_TYPES[project],
            "worktree_id": worktree,
            "lane_events": len(lane),
            "home_events": sum(bool(row["home_worktree"]) for row in lane),
            "mutation_rows": sum(int(row["mutation_rows"]) for row in lane),
            "recognized_success": status_counts["ok"],
            "recognized_fail": status_counts["fail"],
            "recognized_observed_unknown": status_counts["observed"],
            "complete_inter_success_intervals": len(cycle_values),
            "zero_mutation_intervals_pct": format_number(
                100 * sum(value == 0 for value in cycle_values) / len(cycle_values)
                if cycle_values
                else None
            ),
            "inter_success_mutation_rows_median": format_number(
                median(cycle_values)
            ),
            "inter_success_mutation_rows_p90": format_number(
                quantile_type7(cycle_values, 0.9)
            ),
            "inter_success_mutation_rows_max": (
                max(cycle_values) if cycle_values else ""
            ),
        }
        for status in ("ok", "fail"):
            summary = summarize_outcome(
                project,
                status,
                attempts,
                len(lane),
                len(attempts),
            )
            prefix = "success" if status == "ok" else "fail"
            base[f"{prefix}_same_outcome_gap_events_median"] = summary[
                "previous_same_status_gap_events_median"
            ]
            base[f"{prefix}_next_mutation_gap_events_median"] = summary[
                "next_mutation_gap_events_median"
            ]
            base[f"{prefix}_next_attempt_gap_events_median"] = summary[
                "next_attempt_gap_events_median"
            ]
            base[f"{prefix}_mutation_first_share_pct"] = summary[
                "mutation_first_share_of_distinct_observed_order_pct"
            ]
            base[f"{prefix}_mutation_first_comparable_n"] = summary[
                "mutation_first_comparable_n"
            ]
        result.append(base)
    return result


def reconcile_coverage(
    coverage: list[dict[str, str]],
    project_summary: list[dict[str, object]],
) -> None:
    expected = {row["project"]: row for row in coverage}
    for summary in project_summary:
        project = str(summary["project"])
        row = expected[project]
        checks = {
            "attributed_actions": int(row["attributed_actions"]),
            "recognized_success": int(row["recognized_success"]),
            "recognized_fail": int(row["recognized_fail"]),
            "recognized_observed_unknown": int(
                row["recognized_observed_unknown"]
            ),
        }
        for field, value in checks.items():
            if int(summary[field]) != value:
                raise ValueError(
                    f"coverage reconciliation failed for {project}/{field}: "
                    f"{summary[field]} != {value}"
                )
        if row["qualified_with_success"].lower() != "true":
            raise ValueError(f"final-HEAD success coverage is not 6/6: {project}")


def output_manifest(output_dir: Path) -> list[dict[str, object]]:
    names = [
        "input-manifest.csv",
        "validation-events.csv",
        "project-outcome-summary.csv",
        "project-vendor-summary.csv",
        "lane-summary.csv",
        "project-summary.csv",
    ]
    return [
        {
            "file": name,
            "sha256": sha256(output_dir / name),
            "bytes": (output_dir / name).stat().st_size,
        }
        for name in names
    ]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()

    self_check()
    input_manifest = verify_inputs(args.input_dir)
    trajectory = read_csv(args.input_dir / "rq2-trajectory.csv")
    cycles = read_csv(args.input_dir / "rq2-cycles.csv")
    coverage = read_csv(args.input_dir / "rq2-coverage.csv")
    lanes, home_actions, vendor_actions = normalize_trajectory(trajectory)
    event_rows = derive_validation_events(lanes)
    outcome_rows = derive_outcome_summary(event_rows, home_actions)
    vendor_rows = derive_vendor_summary(event_rows, vendor_actions)
    lane_rows = derive_lane_summary(lanes, event_rows, cycles)
    project_rows = derive_project_summary(
        event_rows,
        outcome_rows,
        cycles,
        home_actions,
        vendor_actions,
    )
    reconcile_coverage(coverage, project_rows)

    output_dir = args.output_dir
    write_csv(
        output_dir / "input-manifest.csv",
        input_manifest,
        ["file", "sha256", "bytes", "verification"],
    )
    write_csv(
        output_dir / "validation-events.csv",
        event_rows,
        list(event_rows[0]),
    )
    write_csv(
        output_dir / "project-outcome-summary.csv",
        outcome_rows,
        list(outcome_rows[0]),
    )
    write_csv(
        output_dir / "project-vendor-summary.csv",
        vendor_rows,
        list(vendor_rows[0]),
    )
    write_csv(
        output_dir / "lane-summary.csv",
        lane_rows,
        list(lane_rows[0]),
    )
    write_csv(
        output_dir / "project-summary.csv",
        project_rows,
        list(project_rows[0]),
    )
    outputs = output_manifest(output_dir)
    write_csv(
        output_dir / "output-manifest.csv",
        outputs,
        ["file", "sha256", "bytes"],
    )

    print(
        f"validated {len(trajectory):,} trajectory rows in {len(lanes)} lanes; "
        f"wrote {len(event_rows):,} recognized validation events over "
        f"{len(project_rows)}/6 projects"
    )
    print(
        "recognized successes: "
        + ", ".join(
            f"{row['project']}={row['recognized_success']}"
            for row in project_rows
        )
    )


if __name__ == "__main__":
    main()
