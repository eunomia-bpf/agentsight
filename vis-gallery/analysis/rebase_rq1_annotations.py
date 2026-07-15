#!/usr/bin/env python3
"""Carry blinded RQ1 labels onto a repaired, explicitly re-frozen universe."""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Any


def load(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as source:
        return json.load(source)


def candidate_commit_ids(pair: dict[str, Any]) -> tuple[str, ...]:
    return tuple(sorted({row["commit_id"] for row in pair["audit_candidates"]}))


def carry_mapping(
    old_packets: list[dict[str, Any]],
    current_packets: list[dict[str, Any]],
    tolerance_ms: int = 1_000,
) -> tuple[dict[str, str], list[dict[str, Any]], list[dict[str, Any]]]:
    """Map old pairs by semantic event identity, never by parser-derived ID."""
    current_pairs = [pair for packet in current_packets for pair in packet["pairs"]]
    index: dict[tuple[str, str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for pair in current_pairs:
        index[(pair["day"], pair["vendor"], pair["action"], pair["path"])].append(pair)

    mapping = {}
    used_current_ids = set()
    removed = []
    for old in [pair for packet in old_packets for pair in packet["pairs"]]:
        key = (old["day"], old["vendor"], old["action"], old["path"])
        matches = [
            pair
            for pair in index[key]
            if abs(int(pair["event_ts_ms"]) - int(old["event_ts_ms"]))
            <= tolerance_ms
            and candidate_commit_ids(pair) == candidate_commit_ids(old)
        ]
        if not matches:
            removed.append(old)
            continue
        matches.sort(
            key=lambda pair: (
                abs(int(pair["event_ts_ms"]) - int(old["event_ts_ms"])),
                pair["pair_id"],
            )
        )
        best_distance = abs(
            int(matches[0]["event_ts_ms"]) - int(old["event_ts_ms"])
        )
        if len(matches) > 1 and abs(
            int(matches[1]["event_ts_ms"]) - int(old["event_ts_ms"])
        ) == best_distance:
            raise ValueError(f"ambiguous carry mapping for {old['pair_id']}")
        current_id = matches[0]["pair_id"]
        if current_id in used_current_ids:
            raise ValueError(f"non-injective carry mapping to {current_id}")
        mapping[old["pair_id"]] = current_id
        used_current_ids.add(current_id)

    new_pairs = [
        pair for pair in current_pairs if pair["pair_id"] not in used_current_ids
    ]
    return mapping, new_pairs, removed


def rebase_annotations(
    document: dict[str, Any],
    mapping: dict[str, str],
    new_pairs: list[dict[str, Any]],
    delta_document: dict[str, Any] | None = None,
) -> dict[str, Any]:
    old_annotations = {row["pair_id"]: row for row in document["annotations"]}
    missing_old = sorted(set(mapping).difference(old_annotations))
    if missing_old:
        raise ValueError(f"old annotation is incomplete: {missing_old[:5]}")

    annotations = []
    for old_id, current_id in sorted(mapping.items()):
        row = {**old_annotations[old_id], "pair_id": current_id}
        row["carried_from_pair_id"] = old_id
        annotations.append(row)

    new_ids = {pair["pair_id"] for pair in new_pairs}
    if delta_document is not None:
        delta_annotations = {
            row["pair_id"]: row for row in delta_document["annotations"]
        }
        if set(delta_annotations) != new_ids:
            missing = sorted(new_ids.difference(delta_annotations))
            extra = sorted(set(delta_annotations).difference(new_ids))
            raise ValueError(
                f"delta annotation universe mismatch: missing={missing[:5]} extra={extra[:5]}"
            )
        annotations.extend(delta_annotations.values())

    return {
        "schema": "agentsight.rq1.annotation.rebased.v1",
        "annotator_type": document.get("annotator_type", "unspecified"),
        "rebase": {
            "carried_pairs": len(mapping),
            "new_pairs": len(new_pairs),
            "new_pairs_labeled": len(new_ids) if delta_document is not None else 0,
            "matching_key": "day, vendor, action, path, nearest timestamp within tolerance",
        },
        "annotations": sorted(annotations, key=lambda row: row["pair_id"]),
    }


def delta_packet(
    current_packets: list[dict[str, Any]], new_pairs: list[dict[str, Any]]
) -> dict[str, Any]:
    instructions = current_packets[0].get("instructions", {}) if current_packets else {}
    return {
        "schema": "agentsight.rq1.annotation-delta.v1",
        "days": sorted({pair["day"] for pair in new_pairs}),
        "instructions": instructions,
        "pairs": sorted(new_pairs, key=lambda row: row["pair_id"]),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--old-packet", type=Path, action="append", required=True)
    parser.add_argument("--current-packet", type=Path, action="append", required=True)
    parser.add_argument("--annotation", type=Path, required=True)
    parser.add_argument("--delta-annotation", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--delta-output", type=Path, required=True)
    parser.add_argument("--mapping-output", type=Path, required=True)
    parser.add_argument("--tolerance-ms", type=int, default=1_000)
    args = parser.parse_args()

    old_packets = [load(path) for path in args.old_packet]
    current_packets = [load(path) for path in args.current_packet]
    mapping, new_pairs, removed = carry_mapping(
        old_packets, current_packets, args.tolerance_ms
    )
    rebased = rebase_annotations(
        load(args.annotation),
        mapping,
        new_pairs,
        load(args.delta_annotation) if args.delta_annotation else None,
    )
    report = {
        "schema": "agentsight.rq1.annotation-rebase-map.v1",
        "tolerance_ms": args.tolerance_ms,
        "mapping": mapping,
        "counts": {
            "old_pairs": sum(len(packet["pairs"]) for packet in old_packets),
            "current_pairs": sum(len(packet["pairs"]) for packet in current_packets),
            "carried_pairs": len(mapping),
            "new_pairs": len(new_pairs),
            "removed_pairs": len(removed),
        },
        "removed_pair_ids": sorted(pair["pair_id"] for pair in removed),
    }

    for path in [args.output, args.delta_output, args.mapping_output]:
        path.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(rebased, indent=2, sort_keys=True) + "\n")
    args.delta_output.write_text(
        json.dumps(delta_packet(current_packets, new_pairs), indent=2, sort_keys=True)
        + "\n"
    )
    args.mapping_output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()
