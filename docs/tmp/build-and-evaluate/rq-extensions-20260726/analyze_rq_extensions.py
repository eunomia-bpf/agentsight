#!/usr/bin/env python3
"""Recompute the dormant/revival and rank-turnover RQ extensions.

The script consumes only the frozen RQ1 export. It deliberately keeps the
estimands descriptive: confirmed artifact touches, action/time gaps, rank
membership, and conditional hot-set retention.
"""

from __future__ import annotations

import argparse
import csv
import gzip
import json
import math
import statistics
from collections import Counter, defaultdict
from pathlib import Path, PurePosixPath
from typing import Any, Iterable


ACTION_GAP_THRESHOLD = 100
TIME_GAP_THRESHOLD_HOURS = 24.0
MUTATION_ACCESSES = {"create", "write", "rename", "delete"}
WINDOW_CONFIGS = (
    ("main_100_50", 100, 50),
    ("sensitivity_100_100", 100, 100),
)
COOLING_LAGS = (1, 2, 4, 8)


def read_json(path: Path) -> dict[str, Any]:
    if path.suffix == ".gz":
        with gzip.open(path, "rt", encoding="utf-8") as stream:
            return json.load(stream)
    with path.open(encoding="utf-8") as stream:
        return json.load(stream)


def event_path(events_dir: Path, project: str) -> Path:
    names = [project]
    if project == "eunomia.dev":
        names.append("eunomia-dev")
    for name in names:
        for suffix in (".json.gz", ".json"):
            candidate = events_dir / f"{name}{suffix}"
            if candidate.is_file():
                return candidate
    raise FileNotFoundError(f"no frozen event export for {project}")


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def percentile_type7(values: Iterable[float], probability: float) -> float | None:
    """R/NumPy default linear percentile (Hyndman-Fan type 7)."""
    ordered = sorted(values)
    if not ordered:
        return None
    if len(ordered) == 1:
        return float(ordered[0])
    position = (len(ordered) - 1) * probability
    lower = math.floor(position)
    upper = math.ceil(position)
    fraction = position - lower
    return float(ordered[lower] * (1 - fraction) + ordered[upper] * fraction)


def ratio(numerator: int, denominator: int) -> float | None:
    return numerator / denominator if denominator else None


def artifact_key(action: dict[str, Any]) -> str:
    return f"{action['worktree_id']}\x1f{action['artifact_id']}"


def module_for(path: str) -> str:
    parts = PurePosixPath(path).parts
    return parts[0] if len(parts) > 1 else "repo-root-files"


def preferred_action(actions: list[dict[str, Any]]) -> dict[str, Any]:
    priority = {
        "rename": 0,
        "create": 1,
        "write": 2,
        "delete": 3,
        "read": 4,
        "rename_from": 5,
    }
    return min(
        actions,
        key=lambda row: (
            priority.get(str(row.get("access", "")), 99),
            str(row.get("path", "")),
        ),
    )


def confirmed_touches(
    events: list[dict[str, Any]],
    expected_artifacts: list[dict[str, str]],
) -> tuple[dict[str, list[dict[str, Any]]], list[list[dict[str, Any]]]]:
    """Replay RQ1 identity and collapse compound actions per event/artifact."""
    by_artifact: dict[str, list[dict[str, Any]]] = defaultdict(list)
    by_event: list[list[dict[str, Any]]] = []
    expected_artifacts = sorted(
        expected_artifacts,
        key=lambda row: int(row["artifact_id"].rsplit("a", 1)[1]),
    )
    artifact_cursor = 0
    live: dict[str, dict[str, str]] = defaultdict(dict)

    def new_identity(event_index: int, path: str) -> str:
        nonlocal artifact_cursor
        if artifact_cursor >= len(expected_artifacts):
            raise ValueError("identity replay created an extra artifact")
        artifact = expected_artifacts[artifact_cursor]
        artifact_cursor += 1
        if (
            int(artifact["first_event_index"]) != event_index
            or artifact["first_path"] != path
        ):
            raise ValueError(
                "identity replay diverged: expected "
                f"{artifact['artifact_id']}@{artifact['first_event_index']}:"
                f"{artifact['first_path']}, got {event_index}:{path}"
            )
        return artifact["artifact_id"]

    for event_index, event in enumerate(events):
        grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
        if event.get("status") == "ok":
            for action in event.get("actions", []):
                if action.get("scope", False):
                    continue
                worktree = str(action.get("worktree_id", ""))
                path = str(action.get("path", ""))
                if not worktree or not path:
                    continue
                operation = str(action.get("access", "read"))
                if operation == "rename":
                    live[worktree].pop(path, None)
                    previous_path = str(action.get("previous_path", ""))
                    previous_worktree = str(action.get("previous_worktree_id", ""))
                    source = ""
                    if previous_path and previous_worktree == worktree:
                        source = live[worktree].pop(previous_path, "")
                    identity = source or new_identity(event_index, path)
                    live[worktree][path] = identity
                else:
                    identity = live[worktree].get(path, "")
                    if not identity:
                        identity = new_identity(event_index, path)
                        live[worktree][path] = identity
                    if operation == "delete":
                        live[worktree].pop(path, None)
                replayed = dict(action)
                replayed["artifact_id"] = identity
                grouped[f"{worktree}\x1f{identity}"].append(replayed)
        event_rows = []
        for key, actions in sorted(grouped.items()):
            selected = preferred_action(actions)
            accesses = sorted({str(action["access"]) for action in actions})
            row = {
                "artifact_key": key,
                "worktree_id": selected["worktree_id"],
                "artifact_id": selected["artifact_id"],
                "event_index": event_index,
                "event_id": event["id"],
                "ts_ms": int(event["ts_ms"]),
                "session_id": event["session_id"],
                "path": selected["path"],
                "module": module_for(selected["path"]),
                "accesses": ";".join(accesses),
                "mutation": bool(MUTATION_ACCESSES & set(accesses)),
            }
            by_artifact[key].append(row)
            event_rows.append(row)
        by_event.append(event_rows)
    if artifact_cursor != len(expected_artifacts):
        raise ValueError(
            "identity replay did not consume all artifacts: "
            f"{artifact_cursor}/{len(expected_artifacts)}"
        )
    return by_artifact, by_event


def lifecycle_variant(
    project: str,
    by_artifact: dict[str, list[dict[str, Any]]],
    variant: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    if variant == "action_gap_gt_100":
        qualifies = (
            lambda previous, current: int(current["event_index"])
            - int(previous["event_index"])
            - 1
            > ACTION_GAP_THRESHOLD
        )
        threshold_value = ACTION_GAP_THRESHOLD
        threshold_unit = "intervening_tool_actions"
    elif variant == "time_gap_gt_24h":
        threshold_ms = int(TIME_GAP_THRESHOLD_HOURS * 3_600_000)
        qualifies = (
            lambda previous, current: int(current["ts_ms"]) - int(previous["ts_ms"])
            > threshold_ms
        )
        threshold_value = TIME_GAP_THRESHOLD_HOURS
        threshold_unit = "elapsed_hours"
    else:
        raise ValueError(variant)

    episodes: list[dict[str, Any]] = []
    revivals: list[dict[str, Any]] = []
    revived_artifacts: set[str] = set()
    multi_touch_artifacts = 0

    for key, touches in sorted(by_artifact.items()):
        touches = sorted(touches, key=lambda row: (row["event_index"], row["event_id"]))
        if len(touches) >= 2:
            multi_touch_artifacts += 1
        groups: list[list[dict[str, Any]]] = [[]]
        for touch in touches:
            if groups[-1] and qualifies(groups[-1][-1], touch):
                previous = groups[-1][-1]
                gap_actions = int(touch["event_index"]) - int(previous["event_index"]) - 1
                gap_ms = int(touch["ts_ms"]) - int(previous["ts_ms"])
                groups.append([])
                revived_artifacts.add(key)
                revivals.append(
                    {
                        "project": project,
                        "variant": variant,
                        "threshold_value": threshold_value,
                        "threshold_unit": threshold_unit,
                        "worktree_id": touch["worktree_id"],
                        "artifact_id": touch["artifact_id"],
                        "artifact_key": key,
                        "previous_touch_event_index": previous["event_index"],
                        "previous_touch_ts_ms": previous["ts_ms"],
                        "revival_event_index": touch["event_index"],
                        "revival_ts_ms": touch["ts_ms"],
                        "gap_intervening_actions": gap_actions,
                        "gap_elapsed_ms": gap_ms,
                        "gap_elapsed_hours": gap_ms / 3_600_000,
                        "revival_accesses": touch["accesses"],
                        "revival_is_mutation": touch["mutation"],
                        "cross_session": previous["session_id"] != touch["session_id"],
                    }
                )
            groups[-1].append(touch)

        for episode_ordinal, group in enumerate(groups, 1):
            mutations = [row for row in group if row["mutation"]]
            first_mutation = mutations[0] if mutations else None
            last_mutation = mutations[-1] if mutations else None
            episodes.append(
                {
                    "project": project,
                    "variant": variant,
                    "threshold_value": threshold_value,
                    "threshold_unit": threshold_unit,
                    "worktree_id": group[0]["worktree_id"],
                    "artifact_id": group[0]["artifact_id"],
                    "artifact_key": key,
                    "episode_ordinal": episode_ordinal,
                    "touch_count": len(group),
                    "mutation_touch_count": len(mutations),
                    "first_touch_event_index": group[0]["event_index"],
                    "last_touch_event_index": group[-1]["event_index"],
                    "first_touch_ts_ms": group[0]["ts_ms"],
                    "last_touch_ts_ms": group[-1]["ts_ms"],
                    "first_mutation_event_index": (
                        first_mutation["event_index"] if first_mutation else ""
                    ),
                    "last_mutation_event_index": (
                        last_mutation["event_index"] if last_mutation else ""
                    ),
                    "active_mutation_span_actions": (
                        int(last_mutation["event_index"])
                        - int(first_mutation["event_index"])
                        + 1
                        if first_mutation and last_mutation
                        else ""
                    ),
                    "active_mutation_span_hours": (
                        (int(last_mutation["ts_ms"]) - int(first_mutation["ts_ms"]))
                        / 3_600_000
                        if first_mutation and last_mutation
                        else ""
                    ),
                    "first_path": group[0]["path"],
                    "last_path": group[-1]["path"],
                }
            )

    gaps_actions = [int(row["gap_intervening_actions"]) for row in revivals]
    gaps_hours = [float(row["gap_elapsed_hours"]) for row in revivals]
    mutation_episodes = [
        row for row in episodes if int(row["mutation_touch_count"]) > 0
    ]
    active_spans_actions = [
        int(row["active_mutation_span_actions"]) for row in mutation_episodes
    ]
    active_spans_hours = [
        float(row["active_mutation_span_hours"]) for row in mutation_episodes
    ]
    total_artifacts = len(by_artifact)
    summary = {
        "project": project,
        "variant": variant,
        "threshold_value": threshold_value,
        "threshold_unit": threshold_unit,
        "observed_artifacts": total_artifacts,
        "multi_touch_artifacts": multi_touch_artifacts,
        "revived_artifacts": len(revived_artifacts),
        "revived_share_all_artifacts": ratio(len(revived_artifacts), total_artifacts),
        "revived_share_multi_touch_artifacts": ratio(
            len(revived_artifacts), multi_touch_artifacts
        ),
        "revival_transitions": len(revivals),
        "lifecycle_episodes": len(episodes),
        "mutation_bearing_episodes": len(mutation_episodes),
        "median_active_mutation_span_actions": percentile_type7(
            active_spans_actions, 0.5
        ),
        "p90_active_mutation_span_actions": percentile_type7(
            active_spans_actions, 0.9
        ),
        "median_active_mutation_span_hours": percentile_type7(
            active_spans_hours, 0.5
        ),
        "p90_active_mutation_span_hours": percentile_type7(
            active_spans_hours, 0.9
        ),
        "median_gap_intervening_actions": percentile_type7(gaps_actions, 0.5),
        "p90_gap_intervening_actions": percentile_type7(gaps_actions, 0.9),
        "median_gap_elapsed_hours": percentile_type7(gaps_hours, 0.5),
        "p90_gap_elapsed_hours": percentile_type7(gaps_hours, 0.9),
        "cross_session_revivals": sum(bool(row["cross_session"]) for row in revivals),
        "mutation_revivals": sum(bool(row["revival_is_mutation"]) for row in revivals),
    }
    return episodes, revivals, summary


def top_rank(counter: Counter[str], k: int) -> tuple[list[str], list[int], bool]:
    ranked = sorted(counter.items(), key=lambda pair: (-pair[1], pair[0]))[:k]
    tied_top1 = len(counter) >= 2 and len(ranked) >= 2 and ranked[0][1] == ranked[1][1]
    return [key for key, _ in ranked], [count for _, count in ranked], tied_top1


def derive_windows(
    project: str,
    events: list[dict[str, Any]],
    by_event: list[list[dict[str, Any]]],
    config: str,
    width: int,
    stride: int,
) -> tuple[list[dict[str, Any]], dict[str, list[set[str]]]]:
    rows: list[dict[str, Any]] = []
    top_sets = {"artifact": [], "module": []}
    if len(events) < width:
        return rows, top_sets
    for window_index, start in enumerate(range(0, len(events) - width + 1, stride)):
        stop = start + width
        artifact_counts: Counter[str] = Counter()
        module_counts: Counter[str] = Counter()
        for event_rows in by_event[start:stop]:
            for touch in event_rows:
                artifact_counts[touch["artifact_key"]] += 1
                module_counts[touch["module"]] += 1
        for entity_type, counts in (
            ("artifact", artifact_counts),
            ("module", module_counts),
        ):
            top5, top5_counts, tied = top_rank(counts, 5)
            top_sets[entity_type].append(set(top5))
            rows.append(
                {
                    "project": project,
                    "config": config,
                    "window_width_actions": width,
                    "window_stride_actions": stride,
                    "window_index": window_index,
                    "start_event_index": start,
                    "end_event_index_exclusive": stop,
                    "start_ts_ms": events[start]["ts_ms"],
                    "end_ts_ms": events[stop - 1]["ts_ms"],
                    "entity_type": entity_type,
                    "touches": sum(counts.values()),
                    "distinct_entities": len(counts),
                    "top1": top5[0] if top5 else "",
                    "top1_count": top5_counts[0] if top5_counts else 0,
                    "top1_tied": tied,
                    "top5_members": ";".join(top5),
                    "top5_counts": ";".join(map(str, top5_counts)),
                }
            )
    return rows, top_sets


def turnover_summary(
    project: str,
    config: str,
    entity_type: str,
    sets: list[set[str]],
    window_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    rows = [row for row in window_rows if row["entity_type"] == entity_type]
    top1 = [str(row["top1"]) for row in rows]
    valid_pairs = [
        index
        for index in range(len(sets) - 1)
        if sets[index] and sets[index + 1]
    ]
    top1_changes = sum(top1[index] != top1[index + 1] for index in valid_pairs)
    top5_any_changes = sum(sets[index] != sets[index + 1] for index in valid_pairs)
    replacements = [
        1
        - len(sets[index] & sets[index + 1])
        / max(len(sets[index]), len(sets[index + 1]))
        for index in valid_pairs
    ]
    jaccard_turnover = [
        1
        - len(sets[index] & sets[index + 1])
        / len(sets[index] | sets[index + 1])
        for index in valid_pairs
    ]
    return {
        "project": project,
        "config": config,
        "entity_type": entity_type,
        "windows": len(sets),
        "nonempty_windows": sum(bool(value) for value in sets),
        "valid_adjacent_pairs": len(valid_pairs),
        "top1_changes": top1_changes,
        "top1_change_fraction": ratio(top1_changes, len(valid_pairs)),
        "top5_membership_changes": top5_any_changes,
        "top5_any_change_fraction": ratio(top5_any_changes, len(valid_pairs)),
        "mean_top5_replacement_fraction": (
            statistics.fmean(replacements) if replacements else None
        ),
        "mean_top5_jaccard_turnover": (
            statistics.fmean(jaccard_turnover) if jaccard_turnover else None
        ),
        "top1_tied_windows": sum(bool(row["top1_tied"]) for row in rows),
    }


def cooling_rows(
    project: str,
    config: str,
    entity_type: str,
    sets: list[set[str]],
) -> list[dict[str, Any]]:
    output = []
    for lag in COOLING_LAGS:
        origins = endpoint = continuous = 0
        for index in range(max(0, len(sets) - lag)):
            for entity in sets[index]:
                origins += 1
                endpoint += int(entity in sets[index + lag])
                continuous += int(
                    all(entity in sets[offset] for offset in range(index + 1, index + lag + 1))
                )
        output.append(
            {
                "project": project,
                "config": config,
                "entity_type": entity_type,
                "lag_windows": lag,
                "origin_hot_memberships": origins,
                "endpoint_hot_memberships": endpoint,
                "continuous_hot_memberships": continuous,
                "endpoint_retention_fraction": ratio(endpoint, origins),
                "continuous_retention_fraction": ratio(continuous, origins),
            }
        )
    return output


def pooled_turnover(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output = []
    for config in sorted({str(row["config"]) for row in rows}):
        for entity_type in ("artifact", "module"):
            group = [
                row
                for row in rows
                if row["config"] == config and row["entity_type"] == entity_type
            ]
            valid = sum(int(row["valid_adjacent_pairs"]) for row in group)
            top1 = sum(int(row["top1_changes"]) for row in group)
            top5 = sum(int(row["top5_membership_changes"]) for row in group)
            for pooling in ("transition_weighted_micro", "project_median"):
                if pooling == "transition_weighted_micro":
                    top1_fraction = ratio(top1, valid)
                    top5_fraction = ratio(top5, valid)
                    replacement = (
                        sum(
                            float(row["mean_top5_replacement_fraction"])
                            * int(row["valid_adjacent_pairs"])
                            for row in group
                            if row["mean_top5_replacement_fraction"] is not None
                        )
                        / valid
                        if valid
                        else None
                    )
                else:
                    top1_fraction = percentile_type7(
                        [
                            float(row["top1_change_fraction"])
                            for row in group
                            if row["top1_change_fraction"] is not None
                        ],
                        0.5,
                    )
                    top5_fraction = percentile_type7(
                        [
                            float(row["top5_any_change_fraction"])
                            for row in group
                            if row["top5_any_change_fraction"] is not None
                        ],
                        0.5,
                    )
                    replacement = percentile_type7(
                        [
                            float(row["mean_top5_replacement_fraction"])
                            for row in group
                            if row["mean_top5_replacement_fraction"] is not None
                        ],
                        0.5,
                    )
                output.append(
                    {
                        "pooling": pooling,
                        "config": config,
                        "entity_type": entity_type,
                        "projects": len(group),
                        "valid_adjacent_pairs": valid,
                        "top1_changes": top1,
                        "top1_change_fraction": top1_fraction,
                        "top5_membership_changes": top5,
                        "top5_any_change_fraction": top5_fraction,
                        "mean_top5_replacement_fraction": replacement,
                    }
                )
    return output


def pooled_cooling(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output = []
    keys = sorted(
        {
            (str(row["config"]), str(row["entity_type"]), int(row["lag_windows"]))
            for row in rows
        }
    )
    for config, entity_type, lag in keys:
        group = [
            row
            for row in rows
            if row["config"] == config
            and row["entity_type"] == entity_type
            and int(row["lag_windows"]) == lag
        ]
        origins = sum(int(row["origin_hot_memberships"]) for row in group)
        endpoint = sum(int(row["endpoint_hot_memberships"]) for row in group)
        continuous = sum(int(row["continuous_hot_memberships"]) for row in group)
        for pooling in ("membership_weighted_micro", "project_median"):
            if pooling == "membership_weighted_micro":
                endpoint_fraction = ratio(endpoint, origins)
                continuous_fraction = ratio(continuous, origins)
            else:
                endpoint_fraction = percentile_type7(
                    [
                        float(row["endpoint_retention_fraction"])
                        for row in group
                        if row["endpoint_retention_fraction"] is not None
                    ],
                    0.5,
                )
                continuous_fraction = percentile_type7(
                    [
                        float(row["continuous_retention_fraction"])
                        for row in group
                        if row["continuous_retention_fraction"] is not None
                    ],
                    0.5,
                )
            output.append(
                {
                    "pooling": pooling,
                    "config": config,
                    "entity_type": entity_type,
                    "lag_windows": lag,
                    "projects": len(group),
                    "origin_hot_memberships": origins,
                    "endpoint_hot_memberships": endpoint,
                    "continuous_hot_memberships": continuous,
                    "endpoint_retention_fraction": endpoint_fraction,
                    "continuous_retention_fraction": continuous_fraction,
                }
            )
    return output


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--rq1-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)

    projects_payload = read_json(args.rq1_root / "projects.json")
    project_names = [str(row["project"]) for row in projects_payload]

    lifecycle_episodes: list[dict[str, Any]] = []
    revival_rows: list[dict[str, Any]] = []
    dormancy_summaries: list[dict[str, Any]] = []
    window_rows: list[dict[str, Any]] = []
    turnover_rows: list[dict[str, Any]] = []
    cooling: list[dict[str, Any]] = []
    reconciliation: list[dict[str, Any]] = []

    artifacts_by_project: dict[str, list[dict[str, str]]] = defaultdict(list)
    with (args.rq1_root / "rq1-artifacts.csv").open(
        newline="", encoding="utf-8"
    ) as stream:
        for row in csv.DictReader(stream):
            artifacts_by_project[row["project"]].append(row)

    for project in project_names:
        payload = read_json(event_path(args.rq1_root / "events", project))
        events = payload["events"]
        ids = [str(event["id"]) for event in events]
        if len(ids) != len(set(ids)):
            raise ValueError(f"duplicate frozen event IDs for {project}")
        by_artifact, by_event = confirmed_touches(
            events, artifacts_by_project[project]
        )
        reconciliation.append(
            {
                "project": project,
                "tool_actions": len(events),
                "confirmed_touch_events": sum(bool(rows) for rows in by_event),
                "confirmed_artifact_touches": sum(len(rows) for rows in by_event),
                "event_identity_count": len(by_artifact),
                "rq1_artifact_export_count": len(artifacts_by_project[project]),
                "identity_count_matches": (
                    len(by_artifact) == len(artifacts_by_project[project])
                ),
            }
        )
        if len(by_artifact) != len(artifacts_by_project[project]):
            raise ValueError(
                f"identity replay mismatch for {project}: "
                f"{len(by_artifact)} != {len(artifacts_by_project[project])}"
            )

        for variant in ("action_gap_gt_100", "time_gap_gt_24h"):
            episodes, revivals, summary = lifecycle_variant(
                project, by_artifact, variant
            )
            lifecycle_episodes.extend(episodes)
            revival_rows.extend(revivals)
            dormancy_summaries.append(summary)

        for config, width, stride in WINDOW_CONFIGS:
            project_windows, top_sets = derive_windows(
                project, events, by_event, config, width, stride
            )
            window_rows.extend(project_windows)
            for entity_type in ("artifact", "module"):
                turnover_rows.append(
                    turnover_summary(
                        project,
                        config,
                        entity_type,
                        top_sets[entity_type],
                        project_windows,
                    )
                )
                cooling.extend(
                    cooling_rows(project, config, entity_type, top_sets[entity_type])
                )

    turnover_pooled = pooled_turnover(turnover_rows)
    cooling_pooled = pooled_cooling(cooling)

    write_csv(
        args.output / "rq1-lifecycle-episodes.csv",
        lifecycle_episodes,
        [
            "project",
            "variant",
            "threshold_value",
            "threshold_unit",
            "worktree_id",
            "artifact_id",
            "artifact_key",
            "episode_ordinal",
            "touch_count",
            "mutation_touch_count",
            "first_touch_event_index",
            "last_touch_event_index",
            "first_touch_ts_ms",
            "last_touch_ts_ms",
            "first_mutation_event_index",
            "last_mutation_event_index",
            "active_mutation_span_actions",
            "active_mutation_span_hours",
            "first_path",
            "last_path",
        ],
    )
    write_csv(
        args.output / "rq1-revivals.csv",
        revival_rows,
        [
            "project",
            "variant",
            "threshold_value",
            "threshold_unit",
            "worktree_id",
            "artifact_id",
            "artifact_key",
            "previous_touch_event_index",
            "previous_touch_ts_ms",
            "revival_event_index",
            "revival_ts_ms",
            "gap_intervening_actions",
            "gap_elapsed_ms",
            "gap_elapsed_hours",
            "revival_accesses",
            "revival_is_mutation",
            "cross_session",
        ],
    )
    write_csv(
        args.output / "rq1-dormancy-summary.csv",
        dormancy_summaries,
        list(dormancy_summaries[0]),
    )
    write_csv(
        args.output / "rq3-windows.csv",
        window_rows,
        list(window_rows[0]),
    )
    write_csv(
        args.output / "rq3-turnover-summary.csv",
        turnover_rows,
        list(turnover_rows[0]),
    )
    write_csv(
        args.output / "rq3-turnover-pooled.csv",
        turnover_pooled,
        list(turnover_pooled[0]),
    )
    write_csv(
        args.output / "rq3-cooling.csv",
        cooling,
        list(cooling[0]),
    )
    write_csv(
        args.output / "rq3-cooling-pooled.csv",
        cooling_pooled,
        list(cooling_pooled[0]),
    )
    write_csv(
        args.output / "reconciliation.csv",
        reconciliation,
        list(reconciliation[0]),
    )

    summary = {
        "parameters": {
            "action_gap_threshold_strictly_greater_than": ACTION_GAP_THRESHOLD,
            "time_gap_threshold_hours_strictly_greater_than": TIME_GAP_THRESHOLD_HOURS,
            "window_configs": [
                {"name": name, "width_actions": width, "stride_actions": stride}
                for name, width, stride in WINDOW_CONFIGS
            ],
            "cooling_lags_windows": list(COOLING_LAGS),
            "percentile_definition": "Hyndman-Fan type 7 linear interpolation",
        },
        "rq1": dormancy_summaries,
        "rq3_turnover": turnover_rows,
        "rq3_turnover_pooled": turnover_pooled,
        "rq3_cooling": cooling,
        "rq3_cooling_pooled": cooling_pooled,
        "reconciliation": reconciliation,
    }
    (args.output / "rq-summary.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
