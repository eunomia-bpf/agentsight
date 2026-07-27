#!/usr/bin/env python3
"""Recompute the four user-question analyses on the repaired v2 projection.

This reuses the frozen 2026-07-26 estimators except for the artifact-event
mutation collapse.  The v2 projection can legitimately emit more than one
path for one artifact identity in one Tool event (for example, a chained
rename).  Such rows remain one artifact-event episode.  Their source action
ordinals determine order, and the terminal mutation path determines the
episode's path, artifact type, module, and validation outcome.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
BUILD = ROOT / "docs/tmp/build-and-evaluate"
V2_INPUT = BUILD / "rq1-rq4-recompute-v2-20260727/rq1-raw"
LEGACY_PATH = BUILD / "user-questions-20260726/analyze_user_questions.py"
EXPECTED_ARTIFACTS = 5_676
EXPECTED_MUTATIONS = 13_809
EXPECTED_EPISODES = 13_766


def import_legacy() -> Any:
    spec = importlib.util.spec_from_file_location(
        "user_questions_20260726", LEGACY_PATH
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {LEGACY_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


legacy = import_legacy()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def write_rows(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        raise ValueError(f"refusing to write headerless empty output: {path}")
    legacy.write_csv(path, rows, list(rows[0]))


def add_source_action_ordinals(
    input_root: Path,
    projects_payload: list[dict[str, Any]],
    event_metadata: dict[tuple[str, str], dict[str, Any]],
) -> None:
    """Attach ordered confirmed mutation actions used to audit compound rows."""
    for project_row in projects_payload:
        project = str(project_row["project"])
        payload = legacy.read_json(
            legacy.event_path(input_root / "events", project)
        )
        for event in payload["events"]:
            metadata = event_metadata[(project, str(event["id"]))]
            actions = []
            if event.get("status") == "ok":
                for fallback_ordinal, action in enumerate(event.get("actions", [])):
                    if action.get("scope", False):
                        continue
                    operation = str(action.get("access", ""))
                    if operation not in legacy.MUTATION_ACCESSES:
                        continue
                    actions.append(
                        {
                            "action_ordinal": int(
                                action.get("action_ordinal", fallback_ordinal)
                            ),
                            "worktree_id": str(
                                action.get("worktree_id", "")
                            ),
                            "path": str(action.get("path", "")),
                            "operation": operation,
                        }
                    )
            actions.sort(key=lambda row: int(row["action_ordinal"]))
            metadata["ordered_mutation_actions"] = actions


def match_source_ordinals(
    rows: list[dict[str, str]],
    metadata: dict[str, Any],
    key: tuple[str, str, str, str],
) -> list[int]:
    """Match projected mutation rows to source actions without assuming one path."""
    available = list(metadata.get("ordered_mutation_actions", []))
    used: set[int] = set()
    ordinals: list[int] = []
    last_ordinal = -1
    for row in rows:
        matches = [
            (index, action)
            for index, action in enumerate(available)
            if index not in used
            and action["worktree_id"] == row["worktree_id"]
            and action["path"] == row["path"]
            and action["operation"] == row["operation"]
            and int(action["action_ordinal"]) >= last_ordinal
        ]
        if not matches:
            raise ValueError(
                f"cannot match projected mutation to ordered source action: "
                f"{key}: {row['operation']} {row['path']}"
            )
        index, action = matches[0]
        used.add(index)
        last_ordinal = int(action["action_ordinal"])
        ordinals.append(last_ordinal)
    if ordinals != sorted(ordinals):
        raise ValueError(f"non-monotone compound mutation order: {key}")
    return ordinals


def collapse_mutations(
    mutations: list[dict[str, str]],
    event_metadata: dict[tuple[str, str], dict[str, Any]],
) -> list[dict[str, Any]]:
    """Collapse one artifact identity × Tool event using terminal-path semantics."""
    grouped: dict[
        tuple[str, str, str, str], list[tuple[int, dict[str, str]]]
    ] = defaultdict(list)
    for row_index, row in enumerate(mutations):
        grouped[
            (
                row["project"],
                row["worktree_id"],
                row["artifact_id"],
                row["event_id"],
            )
        ].append((row_index, row))

    episodes: list[dict[str, Any]] = []
    for key, indexed_rows in grouped.items():
        project, worktree_id, artifact_id, event_id = key
        rows = [row for _, row in indexed_rows]
        event_indexes = {int(row["event_index"]) for row in rows}
        timestamps = {int(row["ts_ms"]) for row in rows}
        sessions = {row["session_id"] for row in rows}
        if len(event_indexes) != 1 or len(timestamps) != 1 or len(sessions) != 1:
            raise ValueError(f"inconsistent compound mutation episode: {key}")

        metadata = event_metadata.get((project, event_id), {})
        prompt_index = metadata.get("prompt_index", "")
        source_stream_id = metadata.get("source_stream_id", "")
        if prompt_index == "" or source_stream_id == "":
            raise ValueError(f"missing source metadata for mutation event: {key}")
        if metadata.get("session_id") != next(iter(sessions)):
            raise ValueError(f"session join mismatch for mutation event: {key}")

        ordinals = match_source_ordinals(rows, metadata, key)
        ordered_rows = [
            row
            for _, row in sorted(
                zip(ordinals, rows), key=lambda pair: pair[0]
            )
        ]
        ordered_ordinals = sorted(ordinals)
        terminal = ordered_rows[-1]
        paths_in_order = [row["path"] for row in ordered_rows]
        unique_paths = list(dict.fromkeys(paths_in_order))
        types_in_order = [legacy.classify_path(path) for path in paths_in_order]
        artifact_type = types_in_order[-1]

        episodes.append(
            {
                "project": project,
                "worktree_id": worktree_id,
                "artifact_id": artifact_id,
                "event_id": event_id,
                "event_index": next(iter(event_indexes)),
                "ts_ms": next(iter(timestamps)),
                "session_id": next(iter(sessions)),
                "source_stream_id": source_stream_id,
                "prompt_index": prompt_index,
                "path": terminal["path"],
                "paths": ";".join(unique_paths),
                "path_count": len(unique_paths),
                "cross_path_compound": len(unique_paths) > 1,
                "cross_type_compound": len(set(types_in_order)) > 1,
                "source_action_ordinals": ";".join(
                    str(value) for value in ordered_ordinals
                ),
                "artifact_type": artifact_type,
                "module_anchor": legacy.module_anchor(terminal["path"]),
                "operations": ";".join(
                    sorted({row["operation"] for row in ordered_rows})
                ),
                "raw_mutation_rows": len(rows),
                "validation_outcome": terminal["validation_outcome"],
                "validation_associated": (
                    terminal["validation_outcome"] == "observed_validation"
                ),
                "_row_index": indexed_rows[0][0],
            }
        )

    episodes.sort(
        key=lambda row: (
            legacy.PROJECT_ORDER.index(str(row["project"])),
            int(row["event_index"]),
            int(row["_row_index"]),
        )
    )
    by_artifact: dict[
        tuple[str, str, str], list[dict[str, Any]]
    ] = defaultdict(list)
    for row in episodes:
        by_artifact[
            (row["project"], row["worktree_id"], row["artifact_id"])
        ].append(row)
    for rows in by_artifact.values():
        rows.sort(
            key=lambda row: (
                int(row["event_index"]),
                int(row["_row_index"]),
            )
        )
        for ordinal, row in enumerate(rows, 1):
            row["artifact_episode_ordinal"] = ordinal
            row["repeat_episode"] = ordinal > 1
    for row in episodes:
        row.pop("_row_index")
    return episodes


def write_provenance(
    output: Path,
    input_root: Path,
    projects_payload: list[dict[str, Any]],
) -> None:
    inputs = [
        input_root / "projects.json",
        input_root / "rq1-artifacts.csv",
        input_root / "rq1-mutations.csv",
        *[
            legacy.event_path(input_root / "events", str(row["project"]))
            for row in projects_payload
        ],
    ]
    rows = [
        {
            "input": str(path.relative_to(ROOT)),
            "sha256": sha256(path),
            "bytes": path.stat().st_size,
        }
        for path in inputs
    ]
    write_rows(output / "input-provenance.csv", rows)


def run(input_root: Path, output: Path) -> dict[str, Any]:
    legacy.self_test_classification()
    projects_payload = legacy.read_json(input_root / "projects.json")
    if not isinstance(projects_payload, list):
        raise TypeError("projects.json must be a list")
    project_names = tuple(row["project"] for row in projects_payload)
    if project_names != legacy.PROJECT_ORDER:
        raise ValueError(f"unexpected project order/set: {project_names}")

    artifacts = legacy.read_csv(input_root / "rq1-artifacts.csv")
    mutations = legacy.read_csv(input_root / "rq1-mutations.csv")
    if len(artifacts) != EXPECTED_ARTIFACTS:
        raise ValueError(f"unexpected artifact count: {len(artifacts)}")
    if len(mutations) != EXPECTED_MUTATIONS:
        raise ValueError(f"unexpected mutation-row count: {len(mutations)}")

    artifact_details, artifact_summary = legacy.artifact_analysis(artifacts)
    (
        allocation,
        comparisons,
        checks_and_hashes,
        event_metadata,
        classification_audit,
    ) = legacy.action_allocation(input_root, projects_payload)
    add_source_action_ordinals(input_root, projects_payload, event_metadata)
    episodes = collapse_mutations(mutations, event_metadata)
    if len(episodes) != EXPECTED_EPISODES:
        raise ValueError(f"unexpected episode count: {len(episodes)}")
    if sum(int(row["raw_mutation_rows"]) for row in episodes) != len(mutations):
        raise ValueError("mutation episodes do not reconcile to source rows")

    order_details, order_summary = legacy.test_code_order_analysis(episodes)
    churn = legacy.churn_analysis(episodes)
    paired_details, paired_summary = legacy.paired_churn_analysis(episodes)
    outputs = {
        "a-created-artifacts.csv": artifact_details,
        "a-created-revisit-summary.csv": artifact_summary,
        "b-module-session-episodes.csv": order_details,
        "b-order-summary.csv": order_summary,
        "c-action-allocation.csv": allocation,
        "c-paper-vs-code.csv": comparisons,
        "d-mutation-episodes.csv": episodes,
        "d-churn-summary.csv": churn,
        "d-paired-test-blocks.csv": paired_details,
        "d-paired-test-block-summary.csv": paired_summary,
        "classification-audit.csv": classification_audit,
    }
    output.mkdir(parents=True, exist_ok=True)
    for name, rows in outputs.items():
        write_rows(output / name, rows)
    write_provenance(output, input_root, projects_payload)
    reconciliation = [
        row for row in checks_and_hashes if "project" in row
    ]
    write_rows(output / "reconciliation.csv", reconciliation)

    summary = {
        "projects": len(projects_payload),
        "artifacts": len(artifacts),
        "created_artifacts": len(artifact_details),
        "raw_mutation_rows": len(mutations),
        "artifact_mutation_episodes": len(episodes),
        "cross_path_compound_episodes": sum(
            bool(row["cross_path_compound"]) for row in episodes
        ),
        "cross_type_compound_episodes": sum(
            bool(row["cross_type_compound"]) for row in episodes
        ),
        "eligible_test_code_pairs": len(order_details),
        "test_bearing_blocks": len(paired_details),
    }
    (output / "run-summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=V2_INPUT)
    parser.add_argument("--output", type=Path, default=HERE)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    print(json.dumps(run(args.input.resolve(), args.output.resolve()), indent=2))


if __name__ == "__main__":
    main()
