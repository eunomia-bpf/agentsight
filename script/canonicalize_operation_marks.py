#!/usr/bin/env python3
"""Canonicalize operation-mark names without changing mark structure.

The default action--object mapping is shared with the complete RQ2 replay.
When two adjacent, structurally different mark paths would become identical,
this tool deterministically retains the source name's leading action and the
smallest useful source tokens that distinguish the two operations. It reads
only existing source operations, operation names, and sparse marks; an
optional accepted source-only prediction file is used only to assert equality
after independent expansion. Target stages and scores are neither accepted nor
opened.
"""

from __future__ import annotations

import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path
from typing import Any, Iterable, Mapping

from assemble_agent_operation_profile import expand_predictions
from rq2_canonical_tag_compare import (
    CONTENT_ALIASES,
    CONTENT_STOPWORDS,
    VERB_RULES,
    canonicalize_tag,
    normalized_words,
)


class CanonicalizationError(RuntimeError):
    """The input cannot be transformed without structural ambiguity."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise CanonicalizationError(message)


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
    with path.open(encoding="utf-8") as stream:
        for line_number, line in enumerate(stream, 1):
            if not line.strip():
                continue
            row = json.loads(line)
            require(isinstance(row, dict), f"{path}:{line_number}: expected object")
            rows.append(row)
    return rows


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )


def write_jsonl(path: Path, rows: Iterable[Mapping[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as stream:
        for row in rows:
            stream.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def mark_skeleton_digest(mark_file: Mapping[str, Any]) -> str:
    structure = {
        "id_field": mark_file["id_field"],
        "sequence_field": mark_file["sequence_field"],
        "marks": [
            {
                "sequence": mark["sequence"],
                "start_operation_id": mark["start_operation_id"],
                "path_depth": len(mark["operation_ids"]),
            }
            for mark in mark_file["marks"]
        ],
    }
    payload = json.dumps(
        structure, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode()
    return hashlib.sha256(payload).hexdigest()


def words_for_disambiguation(value: str) -> tuple[str, list[str]]:
    words = normalized_words(value).split()
    require(bool(words), "blank operation name")
    verb = canonicalize_tag(value).split()[0]
    content = []
    for token in words:
        if token in CONTENT_STOPWORDS or token.isdigit():
            continue
        normalized = CONTENT_ALIASES.get(token, token)
        if normalized != verb and normalized not in content:
            content.append(normalized)
    return verb, content


def specific_tag(value: str) -> str:
    """Keep the source action and up to two content words."""
    verb, content = words_for_disambiguation(value)
    if not content:
        return canonicalize_tag(value)
    return " ".join([verb, *content[:2]])


def distinguishing_tag(value: str, peer_values: Iterable[str]) -> str:
    """Choose a stable source-only token that distinguishes colliding peers."""
    verb, content = words_for_disambiguation(value)
    peer_tokens = []
    for peer in peer_values:
        peer_verb, peer_content = words_for_disambiguation(peer)
        peer_tokens.append({peer_verb, *peer_content})
    unique = [
        token
        for token in content
        if all(token not in tokens for tokens in peer_tokens)
    ]
    require(
        bool(unique) or all(verb not in tokens for tokens in peer_tokens),
        f"cannot meaningfully distinguish adjacent operation name {value!r}",
    )
    chosen = unique[-1] if unique else None
    shared = next((token for token in reversed(content) if token != chosen), None)
    words = [verb]
    if chosen is not None:
        words.append(chosen)
    if shared is not None and len(words) < 3:
        words.append(shared)
    tag = " ".join(words)
    require(1 <= len(tag.split()) <= 3, f"invalid distinguishing tag {tag!r}")
    return tag


def adjacent_collisions(
    marks: Iterable[Mapping[str, Any]], mapping: Mapping[str, str]
) -> list[tuple[str, tuple[str, ...], tuple[str, ...], tuple[str, ...]]]:
    previous: dict[str, tuple[tuple[str, ...], tuple[str, ...]]] = {}
    collisions = []
    for mark in marks:
        sequence = str(mark["sequence"])
        operation_ids = tuple(str(value) for value in mark["operation_ids"])
        path = tuple(mapping[value] for value in operation_ids)
        if sequence in previous and previous[sequence][0] == path:
            collisions.append(
                (sequence, previous[sequence][1], operation_ids, path)
            )
        previous[sequence] = (path, operation_ids)
    return collisions


def canonical_mapping(mark_file: Mapping[str, Any]) -> tuple[dict[str, str], dict[str, Any]]:
    names = {str(key): str(value) for key, value in mark_file["operation_names"].items()}
    mapping = {key: canonicalize_tag(value) for key, value in names.items()}
    initial = adjacent_collisions(mark_file["marks"], mapping)

    first_refinements = {
        operation_id
        for _sequence, left, right, _path in initial
        for left_id, right_id in zip(left, right, strict=True)
        for operation_id in (left_id, right_id)
        if left_id != right_id and mapping[left_id] == mapping[right_id]
    }
    for operation_id in first_refinements:
        mapping[operation_id] = specific_tag(names[operation_id])

    remaining = adjacent_collisions(mark_file["marks"], mapping)
    peers: defaultdict[str, set[str]] = defaultdict(set)
    for _sequence, left, right, _path in remaining:
        for left_id, right_id in zip(left, right, strict=True):
            if left_id != right_id and mapping[left_id] == mapping[right_id]:
                peers[left_id].add(right_id)
                peers[right_id].add(left_id)
    for operation_id, peer_ids in peers.items():
        mapping[operation_id] = distinguishing_tag(
            names[operation_id], (names[peer_id] for peer_id in sorted(peer_ids))
        )

    final = adjacent_collisions(mark_file["marks"], mapping)
    require(
        not final,
        f"{len(final)} adjacent complete-path collisions remain after refinement",
    )
    require(
        all(1 <= len(value.split()) <= 3 for value in mapping.values()),
        "canonical tag word-length contract failed",
    )
    allowed_verbs = {verb for verb, _phrases in VERB_RULES}
    require(
        all(value.split()[0] in allowed_verbs for value in mapping.values()),
        "canonical tag action-first contract failed",
    )
    report = {
        "schema": "agentsight.operation-mark-canonicalization.v1",
        "algorithm": "action-object-lexicon-with-boundary-safe-refinement-v1",
        "inputs_opened": ["operation_names", "sparse marks"],
        "inputs_not_opened": ["target stages", "outcomes", "score rows"],
        "marks": len(mark_file["marks"]),
        "old_unique_names": len(set(names.values())),
        "new_unique_names": len(set(mapping.values())),
        "initial_adjacent_collisions": len(initial),
        "specific_refinements": len(first_refinements),
        "distinguishing_refinements": len(peers),
        "remaining_adjacent_collisions": len(final),
        "one_word_names": sum(len(value.split()) == 1 for value in mapping.values()),
        "two_word_names": sum(len(value.split()) == 2 for value in mapping.values()),
        "three_word_names": sum(len(value.split()) == 3 for value in mapping.values()),
    }
    return mapping, report


def transform(
    mark_file: Mapping[str, Any],
    operations: list[dict[str, Any]],
    reference_predictions: list[dict[str, Any]] | None = None,
) -> tuple[dict[str, Any], list[dict[str, Any]], dict[str, Any]]:
    require(
        set(mark_file) == {"id_field", "sequence_field", "marks", "operation_names"},
        "unexpected operation-mark schema",
    )
    before_digest = mark_skeleton_digest(mark_file)
    mapping, report = canonical_mapping(mark_file)
    canonical_ids = {
        tag: "op-" + hashlib.sha256(tag.casefold().encode()).hexdigest()[:24]
        for tag in sorted(set(mapping.values()))
    }
    transformed_marks = {
        "id_field": mark_file["id_field"],
        "sequence_field": mark_file["sequence_field"],
        "operation_names": {
            canonical_ids[tag]: tag for tag in sorted(canonical_ids)
        },
        "marks": [
            {
                **mark,
                "operation_ids": [
                    canonical_ids[mapping[str(operation_id)]]
                    for operation_id in mark["operation_ids"]
                ],
            }
            for mark in mark_file["marks"]
        ],
    }
    require(
        mark_skeleton_digest(transformed_marks) == before_digest,
        "mark sequence/start/depth skeleton changed during name canonicalization",
    )
    require(
        len(transformed_marks["operation_names"])
        == len(set(transformed_marks["operation_names"].values())),
        "canonical display name is assigned to multiple IDs",
    )
    require(
        not adjacent_collisions(
            transformed_marks["marks"], transformed_marks["operation_names"]
        ),
        "canonical ID projection introduced an adjacent display-path collision",
    )

    transformed_predictions = expand_predictions(
        operations, transformed_marks, len(operations)
    )
    occurrence_rows = [
        (
            str(row["session"]),
            int(row["step_id"]),
            str(row["task_occurrence_instance"]),
            len(row["operation_ids"]),
        )
        for row in transformed_predictions
    ]
    occurrence_digest = hashlib.sha256(
        json.dumps(occurrence_rows, separators=(",", ":")).encode()
    ).hexdigest()
    boundary_rows = []
    previous: dict[str, str] = {}
    for session, step_id, occurrence, _path in occurrence_rows:
        boundary_rows.append(
            (session, step_id, session not in previous or previous[session] != occurrence)
        )
        previous[session] = occurrence
    boundary_digest = hashlib.sha256(
        json.dumps(boundary_rows, separators=(",", ":")).encode()
    ).hexdigest()
    reference_equal = None
    if reference_predictions is not None:
        reference_rows = [
            (
                str(row["session"]),
                int(row["step_id"]),
                str(row["task_occurrence_instance"]),
                len(row["operation_ids"]),
            )
            for row in reference_predictions
        ]
        reference_equal = occurrence_rows == reference_rows
        require(reference_equal, "regenerated temporal occurrence partition drift")
    report.update(
        {
            "inputs_opened": [
                "operation_names",
                "sparse marks",
                "normalized operations",
                *(
                    ["accepted source-only predictions for equality check"]
                    if reference_predictions is not None
                    else []
                ),
            ],
            "structural_sha256_before": before_digest,
            "structural_sha256_after": mark_skeleton_digest(transformed_marks),
            "old_semantic_operation_ids": len(mapping),
            "canonical_semantic_operation_ids": len(canonical_ids),
            "canonical_ids_merge_equal_display_names": True,
            "predictions": len(transformed_predictions),
            "temporal_occurrence_partition_sha256": occurrence_digest,
            "adjacent_boundary_vector_sha256": boundary_digest,
            "reference_temporal_partition_equal": reference_equal,
        }
    )
    return transformed_marks, transformed_predictions, report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--operation-marks", type=Path, required=True)
    parser.add_argument("--operations", type=Path, required=True)
    parser.add_argument("--reference-predictions", type=Path)
    parser.add_argument("--out-dir", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    mark_file = read_json(args.operation_marks)
    operations = read_jsonl(args.operations)
    reference_predictions = (
        read_jsonl(args.reference_predictions) if args.reference_predictions else None
    )
    marks, transformed_predictions, report = transform(
        mark_file, operations, reference_predictions
    )
    write_json(args.out_dir / "operation-marks.json", marks)
    write_jsonl(args.out_dir / "predictions.jsonl", transformed_predictions)
    write_json(args.out_dir / "canonicalization-report.json", report)
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
