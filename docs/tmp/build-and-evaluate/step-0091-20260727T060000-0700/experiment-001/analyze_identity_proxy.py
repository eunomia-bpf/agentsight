#!/usr/bin/env python3
"""Deterministically audit CodeTrace gold and cross-run canonical-ID reuse."""

from __future__ import annotations

from collections import Counter, defaultdict
import itertools
import json
from pathlib import Path
import subprocess
from typing import Any

import pyarrow.parquet as pq


ROOT = Path(__file__).resolve().parents[5]
EXPERIMENT = Path(__file__).resolve().parent
STEP_0087 = (
    ROOT
    / "docs/tmp/build-and-evaluate"
    / "step-0087-20260726T023000-0700"
    / "experiment-001"
)
CANONICAL_PREDICTIONS = STEP_0087 / "canonical/predictions.jsonl"
ORIGINAL_PREDICTIONS = STEP_0087 / "assembled/predictions.jsonl"
OPERATIONS = STEP_0087 / "assembled/operations-count.jsonl"
CANONICAL_REPORT = STEP_0087 / "canonical/canonicalization-report.json"
MANIFEST = (
    ROOT
    / ".agentsight/experiments/codetracebench-rq2/manifests/verified.parquet"
)
PACKETS = (
    ROOT
    / ".agentsight/experiments/rq4-end-to-end-cost-v1/full"
    / "source-packets-rep-1"
)
ARCHIVE_ROOT = ROOT / ".agentsight/experiments/codetracebench-rq2/hub"
OUTPUT = EXPERIMENT / "raw-results.json"

EXPECTED_SESSIONS = 405
EXPECTED_OPERATIONS = 20_866
EXPECTED_STAGES = 2_948
EXPECTED_CANONICAL_IDS = 783
EXPECTED_MARKS = 4_496
FRAMEWORKS = ("OpenHands", "SWE-agent", "Terminus2", "mini-SWE-agent")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as source:
        return [json.loads(line) for line in source if line.strip()]


def relative(path: Path) -> str:
    return str(path.relative_to(ROOT))


def sorted_counter(counter: Counter[Any]) -> dict[str, int]:
    return {
        str(key): int(counter[key])
        for key in sorted(counter, key=lambda value: str(value))
    }


def most_common(counter: Counter[Any], limit: int = 20) -> list[dict[str, Any]]:
    return [
        {"value": str(value), "count": int(count)}
        for value, count in sorted(
            counter.items(), key=lambda item: (-item[1], str(item[0]))
        )[:limit]
    ]


def new_accumulator(label: str) -> dict[str, Any]:
    return {
        "label": label,
        "frame_instances": 0,
        "operation_keys": set(),
        "occurrence_instances": set(),
        "sessions": set(),
        "frameworks": set(),
        "tasks": set(),
        "depths": Counter(),
        "stage_ordinals": Counter(),
        "original_labels": Counter(),
        "action_kinds": Counter(),
        "raw_action_keys": Counter(),
        "complete_paths": set(),
        "examples": set(),
    }


def observe(
    accumulator: dict[str, Any],
    *,
    key: tuple[str, int],
    occurrence: str,
    framework: str,
    task: str,
    depth: int,
    stage_ordinal: int,
    original_label: str,
    action_kind: str,
    raw_action_key: str,
    complete_path: tuple[str, ...],
    source_ref: str,
) -> None:
    accumulator["frame_instances"] += 1
    accumulator["operation_keys"].add(key)
    accumulator["occurrence_instances"].add(occurrence)
    accumulator["sessions"].add(key[0])
    accumulator["frameworks"].add(framework)
    accumulator["tasks"].add(task)
    accumulator["depths"][depth] += 1
    accumulator["stage_ordinals"][stage_ordinal] += 1
    accumulator["original_labels"][original_label] += 1
    accumulator["action_kinds"][action_kind] += 1
    accumulator["raw_action_keys"][raw_action_key] += 1
    accumulator["complete_paths"].add(complete_path)
    accumulator["examples"].add(
        (
            framework,
            task,
            key[0],
            key[1],
            stage_ordinal,
            original_label,
            action_kind,
            raw_action_key,
            source_ref,
        )
    )


def select_examples(values: set[tuple[Any, ...]], limit: int = 8) -> list[dict[str, Any]]:
    """Choose deterministic examples while covering frameworks before repeats."""
    ordered = sorted(values)
    chosen: list[tuple[Any, ...]] = []
    seen_frameworks: set[str] = set()
    for value in ordered:
        framework = str(value[0])
        if framework not in seen_frameworks:
            chosen.append(value)
            seen_frameworks.add(framework)
        if len(chosen) == limit:
            break
    for value in ordered:
        if value not in chosen:
            chosen.append(value)
        if len(chosen) == limit:
            break
    return [
        {
            "framework": value[0],
            "task_name": value[1],
            "session": value[2],
            "step_id": value[3],
            "stage_ordinal": value[4],
            "original_label": value[5],
            "action_kind": value[6],
            "raw_action_key": value[7],
            "source_ref": value[8],
        }
        for value in chosen
    ]


def serialize_accumulator(
    operation_id: str, accumulator: dict[str, Any]
) -> dict[str, Any]:
    stage_total = sum(accumulator["stage_ordinals"].values())
    majority_stage, majority_count = sorted(
        accumulator["stage_ordinals"].items(),
        key=lambda item: (-item[1], int(item[0])),
    )[0]
    return {
        "operation_id": operation_id,
        "label": accumulator["label"],
        "frame_instances": int(accumulator["frame_instances"]),
        "operation_rows": len(accumulator["operation_keys"]),
        "occurrence_instances": len(accumulator["occurrence_instances"]),
        "sessions": len(accumulator["sessions"]),
        "frameworks": sorted(accumulator["frameworks"]),
        "tasks": len(accumulator["tasks"]),
        "depth_counts": sorted_counter(accumulator["depths"]),
        "stage_ordinal_counts": sorted_counter(accumulator["stage_ordinals"]),
        "majority_stage_ordinal": int(majority_stage),
        "majority_stage_ordinal_share": majority_count / stage_total,
        "original_label_vocabulary": len(accumulator["original_labels"]),
        "original_label_counts": sorted_counter(accumulator["original_labels"]),
        "top_original_labels": most_common(accumulator["original_labels"]),
        "action_kind_vocabulary": len(accumulator["action_kinds"]),
        "action_kind_counts": sorted_counter(accumulator["action_kinds"]),
        "raw_action_key_vocabulary": len(accumulator["raw_action_keys"]),
        "top_raw_action_keys": most_common(accumulator["raw_action_keys"]),
        "complete_paths": len(accumulator["complete_paths"]),
        "examples": select_examples(accumulator["examples"]),
    }


def identity_summary(
    rows: list[dict[str, Any]], operation_coverage: int
) -> dict[str, Any]:
    framework_set_distribution = Counter(
        ",".join(row["frameworks"]) for row in rows
    )
    session_count_distribution = Counter(row["sessions"] for row in rows)
    task_count_distribution = Counter(row["tasks"] for row in rows)
    framework_pairs = {}
    for left, right in itertools.combinations(FRAMEWORKS, 2):
        framework_pairs[f"{left} + {right}"] = sum(
            left in row["frameworks"] and right in row["frameworks"] for row in rows
        )
    return {
        "unique_ids": len(rows),
        "single_session_ids": sum(row["sessions"] == 1 for row in rows),
        "cross_session_ids": sum(row["sessions"] > 1 for row in rows),
        "cross_task_ids": sum(row["tasks"] > 1 for row in rows),
        "cross_framework_ids": sum(len(row["frameworks"]) > 1 for row in rows),
        "all_four_framework_ids": sum(len(row["frameworks"]) == 4 for row in rows),
        "operation_rows_covered": operation_coverage,
        "session_count_distribution": sorted_counter(session_count_distribution),
        "task_count_distribution": sorted_counter(task_count_distribution),
        "framework_set_distribution": sorted_counter(framework_set_distribution),
        "framework_pair_shared_id_counts": framework_pairs,
    }


def audit_archives(
    manifest_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    missing = []
    member_count_distribution: Counter[int] = Counter()
    source_prefix_misses = []
    annotation_path_hits = []
    goldish_member_hits = []
    total_files = 0
    for row in sorted(manifest_rows, key=lambda item: str(item["traj_id"])):
        archive = ARCHIVE_ROOT / str(row["artifact_path"])
        if not archive.is_file():
            missing.append(relative(archive))
            continue
        completed = subprocess.run(
            ["tar", "--zstd", "-tf", str(archive)],
            check=True,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        members = [
            member
            for member in completed.stdout.splitlines()
            if member and not member.endswith("/")
        ]
        total_files += len(members)
        member_count_distribution[len(members)] += 1
        source_prefix = str(row["source_relpath"]).rstrip("/")
        if not any(
            member == source_prefix or member.startswith(source_prefix + "/")
            for member in members
        ):
            source_prefix_misses.append(str(row["traj_id"]))
        annotation_prefix = str(row["annotation_relpath"]).rstrip("/")
        annotation_matches = [
            member
            for member in members
            if member == annotation_prefix
            or member.startswith(annotation_prefix + "/")
            or "merged_cleaned_step25" in member
        ]
        if annotation_matches:
            annotation_path_hits.append(
                {"session": str(row["traj_id"]), "members": annotation_matches}
            )
        suspicious = [
            member
            for member in members
            if any(
                token in Path(member).name.lower()
                for token in ("annotation", "label", "stage", "gold")
            )
        ]
        if suspicious:
            goldish_member_hits.append(
                {"session": str(row["traj_id"]), "members": suspicious}
            )
    return {
        "archives": len(manifest_rows),
        "missing_archives": missing,
        "total_file_members": total_files,
        "member_count_distribution": sorted_counter(member_count_distribution),
        "source_relpath_misses": source_prefix_misses,
        "annotation_relpath_hits": annotation_path_hits,
        "goldish_basename_hits": goldish_member_hits,
    }


def main() -> None:
    for path in (
        CANONICAL_PREDICTIONS,
        ORIGINAL_PREDICTIONS,
        OPERATIONS,
        CANONICAL_REPORT,
        MANIFEST,
        PACKETS,
        ARCHIVE_ROOT,
    ):
        require(path.exists(), f"missing input: {path}")

    canonical_rows = read_jsonl(CANONICAL_PREDICTIONS)
    original_rows = read_jsonl(ORIGINAL_PREDICTIONS)
    operation_rows = read_jsonl(OPERATIONS)
    canonical_report = read_json(CANONICAL_REPORT)
    require(len(canonical_rows) == EXPECTED_OPERATIONS, "canonical prediction count")
    require(len(original_rows) == EXPECTED_OPERATIONS, "original prediction count")
    require(len(operation_rows) == EXPECTED_OPERATIONS, "operation count")
    require(
        int(canonical_report["canonical_semantic_operation_ids"])
        == EXPECTED_CANONICAL_IDS,
        "canonical ID count",
    )
    require(int(canonical_report["marks"]) == EXPECTED_MARKS, "mark count")

    def prediction_map(rows: list[dict[str, Any]]) -> dict[tuple[str, int], dict[str, Any]]:
        result = {}
        for row in rows:
            key = (str(row["session"]), int(row["step_id"]))
            require(key not in result, f"duplicate prediction: {key}")
            result[key] = row
        return result

    canonical = prediction_map(canonical_rows)
    original = prediction_map(original_rows)
    operations = {}
    for record in operation_rows:
        fields = record["fields"]
        key = (str(fields["session"]), int(fields["step_id"]))
        require(key not in operations, f"duplicate operation: {key}")
        require(int(record["value"]) == 1, f"non-unit operation: {key}")
        operations[key] = fields
    require(set(canonical) == set(original) == set(operations), "input key mismatch")
    sessions = sorted({key[0] for key in canonical})
    require(len(sessions) == EXPECTED_SESSIONS, "session count")

    table = pq.read_table(MANIFEST)
    all_manifest_rows = table.to_pylist()
    manifest_rows = [
        row for row in all_manifest_rows if str(row["traj_id"]) in set(sessions)
    ]
    require(len(manifest_rows) == EXPECTED_SESSIONS, "manifest session coverage")
    manifest_by_session = {str(row["traj_id"]): row for row in manifest_rows}
    require(set(manifest_by_session) == set(sessions), "manifest key mismatch")

    stage_by_key: dict[tuple[str, int], int] = {}
    for session in sessions:
        row = manifest_by_session[session]
        require(row["solved"] is False, f"non-failed selected session: {session}")
        stage_ids = [int(stage["stage_id"]) for stage in row["stages"]]
        require(
            stage_ids == list(range(1, int(row["stage_count"]) + 1)),
            f"non-ordinal stage IDs: {session}",
        )
        cursor = 1
        for stage in row["stages"]:
            start = int(stage["start_step_id"])
            end = int(stage["end_step_id"])
            require(start == cursor and end >= start, f"stage range gap: {session}")
            for step_id in range(start, end + 1):
                key = (session, step_id)
                require(key not in stage_by_key, f"duplicate stage step: {key}")
                stage_by_key[key] = int(stage["stage_id"])
            cursor = end + 1
        require(
            cursor == int(row["step_count"]) + 1,
            f"incomplete stage ranges: {session}",
        )
    require(set(stage_by_key) == set(canonical), "stage operation coverage")
    require(
        sum(len(row["stages"]) for row in manifest_rows) == EXPECTED_STAGES,
        "stage count",
    )

    packet_top_keys: set[str] = set()
    packet_session_keys: set[str] = set()
    packet_turn_keys: set[str] = set()
    packet_sessions = packet_turns = packet_operations = 0
    packet_files = sorted(PACKETS.glob("batch-*.json"))
    for packet_file in packet_files:
        payload = read_json(packet_file)
        packet_top_keys.update(payload)
        packet_sessions += len(payload["sessions"])
        for session_row in payload["sessions"]:
            packet_session_keys.update(session_row)
            packet_turns += len(session_row["turns"])
            packet_operations += int(session_row["operation_count"])
            for turn in session_row["turns"]:
                packet_turn_keys.update(turn)
    require(packet_sessions == EXPECTED_SESSIONS, "packet session count")
    require(packet_turns == 17_148, "packet turn count")
    require(packet_operations == EXPECTED_OPERATIONS, "packet operation count")

    all_ids: dict[str, dict[str, Any]] = {}
    leaf_ids: dict[str, dict[str, Any]] = {}
    root_ids: dict[str, dict[str, Any]] = {}
    id_to_label: dict[str, str] = {}
    operation_paths: dict[tuple[str, ...], dict[str, set[str] | int]] = {}
    original_labels_global: set[str] = set()

    for key in sorted(canonical):
        candidate = canonical[key]
        predecessor = original[key]
        fields = operations[key]
        candidate_stack = candidate["semantic_stack"]
        predecessor_stack = predecessor["semantic_stack"]
        require(
            len(candidate_stack) == len(predecessor_stack),
            f"path depth changed: {key}",
        )
        path_ids = tuple(str(frame["operation_id"]) for frame in candidate_stack)
        path_labels = tuple(str(frame["label"]) for frame in candidate_stack)
        require(
            path_ids == tuple(str(value) for value in candidate["operation_ids"]),
            f"candidate ID path mismatch: {key}",
        )
        for operation_id, label in zip(path_ids, path_labels):
            if operation_id in id_to_label:
                require(id_to_label[operation_id] == label, "one ID has multiple labels")
            else:
                id_to_label[operation_id] = label
        path_row = operation_paths.setdefault(
            path_ids,
            {
                "operation_rows": 0,
                "sessions": set(),
                "frameworks": set(),
                "tasks": set(),
            },
        )
        path_row["operation_rows"] = int(path_row["operation_rows"]) + 1
        path_row["sessions"].add(key[0])
        path_row["frameworks"].add(str(candidate["framework"]))
        task_name = str(manifest_by_session[key[0]]["task_name"])
        path_row["tasks"].add(task_name)

        for depth, (candidate_frame, predecessor_frame) in enumerate(
            zip(candidate_stack, predecessor_stack), 1
        ):
            operation_id = str(candidate_frame["operation_id"])
            label = str(candidate_frame["label"])
            original_label = str(predecessor_frame["label"])
            original_labels_global.add(original_label)
            accumulator = all_ids.setdefault(
                operation_id, new_accumulator(label)
            )
            observe(
                accumulator,
                key=key,
                occurrence=str(candidate["task_occurrence_instance"]),
                framework=str(candidate["framework"]),
                task=task_name,
                depth=depth,
                stage_ordinal=stage_by_key[key],
                original_label=original_label,
                action_kind=str(fields["action_kind"]),
                raw_action_key=str(fields["raw_action_key"]),
                complete_path=path_labels,
                source_ref=str(candidate["source_ref"]),
            )
            if depth == 1:
                root_accumulator = root_ids.setdefault(
                    operation_id, new_accumulator(label)
                )
                observe(
                    root_accumulator,
                    key=key,
                    occurrence=str(candidate["task_occurrence_instance"]),
                    framework=str(candidate["framework"]),
                    task=task_name,
                    depth=depth,
                    stage_ordinal=stage_by_key[key],
                    original_label=original_label,
                    action_kind=str(fields["action_kind"]),
                    raw_action_key=str(fields["raw_action_key"]),
                    complete_path=path_labels,
                    source_ref=str(candidate["source_ref"]),
                )
            if depth == len(candidate_stack):
                leaf_accumulator = leaf_ids.setdefault(
                    operation_id, new_accumulator(label)
                )
                observe(
                    leaf_accumulator,
                    key=key,
                    occurrence=str(candidate["task_occurrence_instance"]),
                    framework=str(candidate["framework"]),
                    task=task_name,
                    depth=depth,
                    stage_ordinal=stage_by_key[key],
                    original_label=original_label,
                    action_kind=str(fields["action_kind"]),
                    raw_action_key=str(fields["raw_action_key"]),
                    complete_path=path_labels,
                    source_ref=str(candidate["source_ref"]),
                )

    require(len(all_ids) == EXPECTED_CANONICAL_IDS, "observed canonical ID count")
    require(
        len(original_labels_global) == int(canonical_report["old_unique_names"]),
        "original semantic label vocabulary",
    )

    all_rows = [
        serialize_accumulator(operation_id, all_ids[operation_id])
        for operation_id in sorted(all_ids)
    ]
    leaf_rows = [
        serialize_accumulator(operation_id, leaf_ids[operation_id])
        for operation_id in sorted(leaf_ids)
    ]
    root_rows = [
        serialize_accumulator(operation_id, root_ids[operation_id])
        for operation_id in sorted(root_ids)
    ]

    cross_session_all = {
        row["operation_id"] for row in all_rows if row["sessions"] > 1
    }
    cross_session_leaf = {
        row["operation_id"] for row in leaf_rows if row["sessions"] > 1
    }
    all_coverage = sum(
        any(operation_id in cross_session_all for operation_id in row["operation_ids"])
        for row in canonical_rows
    )
    leaf_coverage = sum(
        str(row["operation_ids"][-1]) in cross_session_leaf for row in canonical_rows
    )

    complete_path_rows = []
    for path_ids, values in sorted(operation_paths.items()):
        complete_path_rows.append(
            {
                "operation_ids": list(path_ids),
                "labels": [id_to_label[operation_id] for operation_id in path_ids],
                "depth": len(path_ids),
                "operation_rows": int(values["operation_rows"]),
                "sessions": len(values["sessions"]),
                "frameworks": sorted(values["frameworks"]),
                "tasks": len(values["tasks"]),
            }
        )

    cross_session_leaf_rows = [
        row for row in leaf_rows if row["sessions"] > 1
    ]
    stage_span_distribution = Counter(
        len(row["stage_ordinal_counts"]) for row in cross_session_leaf_rows
    )

    def by_sessions(row: dict[str, Any]) -> tuple[Any, ...]:
        return (
            -row["sessions"],
            -len(row["frameworks"]),
            -row["tasks"],
            -row["operation_rows"],
            row["label"],
            row["operation_id"],
        )

    def by_original_diversity(row: dict[str, Any]) -> tuple[Any, ...]:
        return (
            -row["original_label_vocabulary"],
            -row["sessions"],
            -row["operation_rows"],
            row["label"],
            row["operation_id"],
        )

    label_fields = {}
    for field in (
        "agent",
        "model",
        "task_name",
        "task_slug",
        "difficulty",
        "category",
        "solved",
    ):
        sessions_by_value: dict[str, set[str]] = defaultdict(set)
        for row in manifest_rows:
            sessions_by_value[str(row[field])].add(str(row["traj_id"]))
        label_fields[field] = {
            "vocabulary": len(sessions_by_value),
            "recurrent_values": sum(
                len(value_sessions) > 1
                for value_sessions in sessions_by_value.values()
            ),
            "maximum_session_recurrence": max(
                len(value_sessions) for value_sessions in sessions_by_value.values()
            ),
            "values": sorted(sessions_by_value),
        }
    tags_by_session: dict[str, set[str]] = defaultdict(set)
    for row in manifest_rows:
        for tag in row["tags"] or []:
            tags_by_session[str(tag)].add(str(row["traj_id"]))
    label_fields["tags"] = {
        "vocabulary": len(tags_by_session),
        "recurrent_values": sum(
            len(value_sessions) > 1 for value_sessions in tags_by_session.values()
        ),
        "maximum_session_recurrence": max(
            len(value_sessions) for value_sessions in tags_by_session.values()
        ),
        "values": sorted(tags_by_session),
    }

    visible_operation_fields = {}
    for field in (
        "action_kind",
        "phase",
        "raw_action_key",
        "source_kind",
        "agent",
        "project",
    ):
        sessions_by_value = defaultdict(set)
        for (session, _), values in operations.items():
            sessions_by_value[str(values[field])].add(session)
        visible_operation_fields[field] = {
            "vocabulary": len(sessions_by_value),
            "recurrent_values": sum(
                len(value_sessions) > 1
                for value_sessions in sessions_by_value.values()
            ),
            "maximum_session_recurrence": max(
                len(value_sessions) for value_sessions in sessions_by_value.values()
            ),
            "values": sorted(sessions_by_value),
            "gold_stage_identity": False,
        }

    incorrect_labels: Counter[str] = Counter()
    incorrect_label_sessions: dict[str, set[str]] = defaultdict(set)
    incorrect_stage_instances = 0
    incorrect_step_records = 0
    for row in manifest_rows:
        for stage in row["incorrect_stages"] or []:
            incorrect_stage_instances += 1
            for step in stage["steps"] or []:
                incorrect_step_records += 1
                for label in step["labels"] or []:
                    incorrect_labels[str(label)] += 1
                    incorrect_label_sessions[str(label)].add(str(row["traj_id"]))

    stage_id_counts = Counter(
        int(stage["stage_id"])
        for row in manifest_rows
        for stage in row["stages"]
    )
    packet_forbidden = {
        "stage",
        "stages",
        "stage_id",
        "stage_name",
        "stage_type",
        "label",
        "labels",
        "outcome",
        "score",
        "reward",
    }
    packet_all_keys = packet_top_keys | packet_session_keys | packet_turn_keys

    result = {
        "schema": "agentsight.cross-run-identity-gold-and-proxy.v1",
        "branch": "2B",
        "deterministic": True,
        "inputs": {
            "canonical_predictions": relative(CANONICAL_PREDICTIONS),
            "original_predictions": relative(ORIGINAL_PREDICTIONS),
            "operations": relative(OPERATIONS),
            "canonicalization_report": relative(CANONICAL_REPORT),
            "verified_manifest": relative(MANIFEST),
            "source_packets": relative(PACKETS),
            "archive_root": relative(ARCHIVE_ROOT),
        },
        "population": {
            "sessions": len(sessions),
            "operations": len(canonical_rows),
            "human_stage_occurrences": sum(
                len(row["stages"]) for row in manifest_rows
            ),
            "frameworks": sorted(
                {str(row["agent"]) for row in manifest_rows}
            ),
            "task_names": len(
                {str(row["task_name"]) for row in manifest_rows}
            ),
            "semantic_occurrence_instances": len(
                {str(row["task_occurrence_instance"]) for row in canonical_rows}
            ),
        },
        "phase1_gold_audit": {
            "cross_run_stage_identity_available": False,
            "branch_decision": "Phase 2B",
            "manifest_arrow_schema": str(table.schema),
            "stage_object_fields": ["end_step_id", "stage_id", "start_step_id"],
            "stage_name_fields": [],
            "stage_type_fields": [],
            "stage_id_vocabulary": sorted(stage_id_counts),
            "stage_id_counts": sorted_counter(stage_id_counts),
            "stage_ids_are_one_based_sequential_per_trajectory": True,
            "stage_ranges_are_complete_contiguous_partitions": True,
            "other_label_fields": label_fields,
            "visible_non_gold_operation_fields": visible_operation_fields,
            "incorrect_annotations": {
                "stage_fields": [
                    "incorrect_step_ids",
                    "stage_id",
                    "steps",
                    "unuseful_step_ids",
                ],
                "step_fields": [
                    "action_ref",
                    "labels",
                    "observation_ref",
                    "step_id",
                ],
                "label_vocabulary": sorted(incorrect_labels),
                "label_counts": sorted_counter(incorrect_labels),
                "label_session_recurrence": {
                    label: len(incorrect_label_sessions[label])
                    for label in sorted(incorrect_label_sessions)
                },
                "stage_instances": incorrect_stage_instances,
                "step_records": incorrect_step_records,
                "semantic_stage_identity": False,
            },
            "scorer_manifest_columns_opened": [
                "traj_id",
                "agent",
                "task_name",
                "solved",
                "step_count",
                "stages",
            ],
            "scorer_official_identity_construction": (
                "<session>:stage-<one-based local stage_id>"
            ),
            "packets": {
                "batches": len(packet_files),
                "sessions": packet_sessions,
                "turns": packet_turns,
                "operations": packet_operations,
                "top_level_keys": sorted(packet_top_keys),
                "session_keys": sorted(packet_session_keys),
                "turn_keys": sorted(packet_turn_keys),
                "gold_or_label_key_intersection": sorted(
                    packet_all_keys & packet_forbidden
                ),
            },
            "archives": audit_archives(manifest_rows),
        },
        "phase2b_proxy": {
            "scope": (
                "Descriptive cross-run name reuse and local stage-position "
                "contingencies; not a gold accuracy metric."
            ),
            "canonicalization": {
                "algorithm": canonical_report["algorithm"],
                "canonical_ids": len(all_rows),
                "original_open_labels": len(original_labels_global),
                "temporal_partition_preserved": bool(
                    canonical_report["reference_temporal_partition_equal"]
                ),
                "remaining_adjacent_collisions": int(
                    canonical_report["remaining_adjacent_collisions"]
                ),
            },
            "all_stack_frames": {
                "summary": identity_summary(all_rows, all_coverage),
                "top_by_session_reuse": sorted(all_rows, key=by_sessions)[:20],
                "top_by_original_label_diversity": sorted(
                    [row for row in all_rows if row["sessions"] > 1],
                    key=by_original_diversity,
                )[:20],
            },
            "leaf_frames": {
                "summary": identity_summary(leaf_rows, leaf_coverage),
                "top_by_session_reuse": sorted(leaf_rows, key=by_sessions)[:20],
                "top_by_original_label_diversity": sorted(
                    [row for row in leaf_rows if row["sessions"] > 1],
                    key=by_original_diversity,
                )[:20],
            },
            "root_frames": {
                "summary": identity_summary(root_rows, EXPECTED_OPERATIONS),
                "top_by_session_reuse": sorted(root_rows, key=by_sessions)[:20],
            },
            "complete_paths": {
                "unique_paths": len(complete_path_rows),
                "single_session_paths": sum(
                    row["sessions"] == 1 for row in complete_path_rows
                ),
                "cross_session_paths": sum(
                    row["sessions"] > 1 for row in complete_path_rows
                ),
                "cross_framework_paths": sum(
                    len(row["frameworks"]) > 1 for row in complete_path_rows
                ),
                "top_by_session_reuse": sorted(
                    complete_path_rows,
                    key=lambda row: (
                        -row["sessions"],
                        -len(row["frameworks"]),
                        -row["tasks"],
                        -row["operation_rows"],
                        row["labels"],
                    ),
                )[:20],
            },
            "stage_position_proxy": {
                "warning": (
                    "Stage ordinals are local positions, not semantic types. "
                    "These counts cannot identify false merges or false splits."
                ),
                "cross_session_leaf_ids": len(cross_session_leaf_rows),
                "unique_stage_ordinal_count_distribution": sorted_counter(
                    stage_span_distribution
                ),
                "leaf_ids_spanning_multiple_stage_ordinals": sum(
                    len(row["stage_ordinal_counts"]) > 1
                    for row in cross_session_leaf_rows
                ),
                "leaf_ids_confined_to_one_stage_ordinal": sum(
                    len(row["stage_ordinal_counts"]) == 1
                    for row in cross_session_leaf_rows
                ),
                "top_cross_session_leaf_ids": sorted(
                    cross_session_leaf_rows, key=by_sessions
                )[:20],
            },
            "all_canonical_id_rows": all_rows,
            "all_leaf_id_rows": leaf_rows,
            "all_complete_path_rows": complete_path_rows,
        },
        "limitations": [
            (
                "No released relation states whether two stages from different "
                "trajectories are semantically the same."
            ),
            (
                "Task/category/tag recurrence is trajectory-level metadata, not "
                "stage identity."
            ),
            (
                "Local stage-ordinal overlap is a position contingency only and "
                "must not be reported as pairwise identity accuracy."
            ),
            (
                "Cross-framework reuse and original-label diversity support "
                "qualitative audit but cannot prove a merge correct or a split wrong."
            ),
        ],
    }

    OUTPUT.write_text(
        json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "status": "complete",
                "branch": "2B",
                "output": relative(OUTPUT),
                "sessions": len(sessions),
                "operations": len(canonical_rows),
                "canonical_ids": len(all_rows),
                "leaf_ids": len(leaf_rows),
                "complete_paths": len(complete_path_rows),
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
