#!/usr/bin/env python3
"""Create score-free naturalistic RQ1 annotation packets."""

from __future__ import annotations

import argparse
import hashlib
import json
import random
from pathlib import Path
from typing import Any


def load_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as source:
        return json.load(source)


def stable_id(*values: str) -> str:
    digest = hashlib.sha256("\0".join(values).encode()).hexdigest()[:20]
    return f"oracle-{digest}"


def connected_changes(
    event: dict[str, Any],
    path: str,
    changes: list[dict[str, Any]],
    lifetime_paths: dict[str, set[str]],
) -> list[dict[str, Any]]:
    candidates = []
    for change in changes:
        paths = lifetime_paths.get(change["lifetime_id"], set())
        connected = (
            change["path"] == path
            or change.get("old_path") == path
            or path in paths
        )
        if not connected:
            continue
        candidates.append(
            {
                "change_id": change["id"],
                "commit_id": change["commit_id"],
                "committed_at_ms": change["committed_at_ms"],
                "status": change["status"],
                "old_path": change.get("old_path"),
                "path": change["path"],
                "additions": change["additions"],
                "deletions": change["deletions"],
                "is_merge": change["is_merge"],
                "hunks": change["hunks"],
            }
        )
    return candidates


def prepare(artifact: dict[str, Any], day: str, seed: int) -> dict[str, Any]:
    events = {event["id"]: event for event in artifact["events"]}
    lifetime_paths = {
        lifetime["id"]: set(lifetime["paths"])
        for lifetime in artifact["file_lifetimes"]
    }
    rng = random.Random(seed)
    pairs = []
    for association in artifact["associations"]:
        event = events[association["event_id"]]
        path = association["path"]
        candidates = connected_changes(
            event, path, artifact["changes"], lifetime_paths
        )
        rng.shuffle(candidates)
        pairs.append(
            {
                "pair_id": stable_id(event["id"], path),
                "day": day,
                "vendor": event["vendor"],
                "event_ts_ms": event["ts_ms"],
                "action": event["action"],
                "status": event["status"],
                "path": path,
                "edit_summary": event.get("edit_summary"),
                "audit_candidates": candidates,
            }
        )
    rng.shuffle(pairs)
    return {
        "schema": "agentsight.rq1.annotation-packet.v1",
        "day": day,
        "seed": seed,
        "instructions": {
            "labels": ["target", "null", "unadjudicable"],
            "target": "one or more listed commit IDs durably contain the recorded edit",
            "null": "the recorded write has no durable counterpart among the exhaustive seven-day candidates",
            "unadjudicable": "the privacy-safe evidence cannot distinguish target from null",
            "merge_policy": "merge rows are a separate stratum; do not infer a primary link from merge timing alone",
            "causality_warning": "temporal order, path equality, and agent identity do not prove authorship",
            "output": "preserve pair_id; add label, target_commit_ids, and a short evidence_code; do not copy paths into the annotation output",
        },
        "pairs": pairs,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact", type=Path, required=True)
    parser.add_argument("--day", required=True)
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    artifact = load_json(args.artifact)
    packet = prepare(artifact, args.day, args.seed)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(packet, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
