#!/usr/bin/env python3
"""Freeze the path-compatible six-case anchor used by external RQ6."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import statistics
from collections import defaultdict
from pathlib import Path


EXPECTED_INPUT_SHA256 = "26466eb3a343ee6eb9a459a6c4690b8ae072b0317a775f6636093f0d3eb344cf"
PROJECTION_VERSION = "rq6-path-target-v1"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def percentile(values: list[int], quantile: float) -> float:
    if not values:
        return math.nan
    ordered = sorted(values)
    rank = (len(ordered) - 1) * quantile
    lower = math.floor(rank)
    upper = math.ceil(rank)
    if lower == upper:
        return float(ordered[lower])
    return ordered[lower] * (upper - rank) + ordered[upper] * (rank - lower)


def derive(input_path: Path) -> list[dict[str, object]]:
    calls: dict[tuple[str, str, str], dict[str, object]] = {}
    with input_path.open(encoding="utf-8", newline="") as stream:
        for row in csv.DictReader(stream):
            path = row["path"].strip()
            if not path:
                continue
            key = (row["project"], row["worktree_id"], row["event_id"])
            call = calls.setdefault(
                key,
                {
                    "project": row["project"],
                    "worktree_id": row["worktree_id"],
                    "event_id": row["event_id"],
                    "event_index": int(row["event_index"]),
                    "paths": set(),
                    "modules": set(),
                },
            )
            call["paths"].add(path)
            call["modules"].add(row["module"] or "repo-root-files")

    lanes: dict[tuple[str, str], list[dict[str, object]]] = defaultdict(list)
    for call in calls.values():
        lanes[(str(call["project"]), str(call["worktree_id"]))].append(call)

    by_project: dict[str, dict[str, object]] = defaultdict(
        lambda: {
            "path_calls": 0,
            "transitions": defaultdict(int),
            "observed_return_gaps": [],
            "right_censored_returns": 0,
        }
    )
    for (project, _worktree), lane in lanes.items():
        lane.sort(key=lambda row: (int(row["event_index"]), str(row["event_id"])))
        result = by_project[project]
        result["path_calls"] += len(lane)
        for previous, current in zip(lane, lane[1:]):
            if previous["paths"] & current["paths"]:
                kind = "same_path"
            elif previous["modules"] & current["modules"]:
                kind = "same_module"
            else:
                kind = "cross_module"
            result["transitions"][kind] += 1

        state: dict[str, dict[str, int | bool]] = {}
        for index, call in enumerate(lane):
            present = set(call["modules"])
            for module in state:
                if module not in present:
                    state[module]["left"] = True
            for module in present:
                previous = state.get(module)
                if previous and bool(previous["left"]):
                    # Count only calls strictly between departure and return.
                    # For A, B, A the return gap is one intervening call.
                    result["observed_return_gaps"].append(index - int(previous["index"]) - 1)
                state[module] = {"index": index, "left": False}
        result["right_censored_returns"] += sum(bool(value["left"]) for value in state.values())

    rows = []
    for project in sorted(by_project):
        result = by_project[project]
        transitions = result["transitions"]
        total = sum(transitions.values())
        gaps = list(result["observed_return_gaps"])
        rows.append(
            {
                "projection_version": PROJECTION_VERSION,
                "input_sha256": EXPECTED_INPUT_SHA256,
                "project": project,
                "path_resolved_tool_calls": result["path_calls"],
                "eligible_transitions": total,
                "same_path": transitions["same_path"],
                "same_module": transitions["same_module"],
                "cross_module": transitions["cross_module"],
                "same_path_share": transitions["same_path"] / total if total else "",
                "same_module_share": transitions["same_module"] / total if total else "",
                "cross_module_share": transitions["cross_module"] / total if total else "",
                "observed_module_returns": len(gaps),
                "right_censored_modules": result["right_censored_returns"],
                "return_gap_median_calls": statistics.median(gaps) if gaps else "",
                "return_gap_p90_calls": percentile(gaps, 0.9) if gaps else "",
            }
        )
    return rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--metadata", type=Path, required=True)
    args = parser.parse_args()
    actual = sha256(args.input)
    if actual != EXPECTED_INPUT_SHA256:
        raise ValueError(f"frozen input SHA-256 mismatch: {actual}")
    rows = derive(args.input)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    metadata = {
        "projection_version": PROJECTION_VERSION,
        "input_sha256": actual,
        "projects": len(rows),
        "path_resolved_tool_calls": sum(int(row["path_resolved_tool_calls"]) for row in rows),
        "eligible_transitions": sum(int(row["eligible_transitions"]) for row in rows),
        "output_sha256": sha256(args.output),
    }
    args.metadata.write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
