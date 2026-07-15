#!/usr/bin/env python3
"""Evaluate conservative Git-hunk-to-current-line links for RQ1."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import subprocess
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


HEADER = re.compile(r"^([0-9a-f]{40})\s+\d+\s+\d+(?:\s+\d+)?$")


def load(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as source:
        return json.load(source)


def run(repo: Path, *args: str) -> bytes:
    result = subprocess.run(
        ["git", "-C", str(repo), *args], check=True, capture_output=True
    )
    return result.stdout


def fingerprint(lines: list[str]) -> str:
    text = "\n".join(lines).rstrip("\n")
    return hashlib.sha256(text.encode()).hexdigest()[:24]


def hunk_matches(edit: dict[str, Any], hunk: dict[str, Any]) -> bool:
    before = edit.get("before_hash")
    after = edit.get("after_hash")
    return (before is not None or after is not None) and (
        before is None or before == hunk.get("before_hash")
    ) and (after is None or after == hunk.get("after_hash"))


def wilson(successes: int, total: int, z: float = 1.959963984540054) -> dict[str, Any]:
    if not total:
        return {"successes": successes, "total": total, "estimate": None, "low": None, "high": None}
    estimate = successes / total
    denominator = 1 + z * z / total
    center = (estimate + z * z / (2 * total)) / denominator
    margin = z * math.sqrt(estimate * (1 - estimate) / total + z * z / (4 * total * total)) / denominator
    return {
        "successes": successes,
        "total": total,
        "estimate": estimate,
        "low": max(0.0, center - margin),
        "high": min(1.0, center + margin),
    }


def blame_origins(repo: Path, head: str, path: str, start: int, end: int) -> list[str]:
    output = run(
        repo,
        "blame",
        "-M",
        "--line-porcelain",
        f"-L{start},{end}",
        head,
        "--",
        path,
    ).decode("utf-8", errors="replace")
    origins = []
    for line in output.splitlines():
        match = HEADER.match(line)
        if match:
            origins.append(match.group(1))
    return origins


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--truth", type=Path, required=True)
    parser.add_argument("--artifact", type=Path, action="append", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--private-output", type=Path, required=True)
    args = parser.parse_args()

    truth = load(args.truth)
    truth_rows = {
        row["pair_id"]: row
        for row in truth["pairs"]
        if row.get("adjudicable", True) and row["label"] == "target"
    }
    artifacts = {}
    for path in args.artifact:
        artifact = load(path)
        artifacts[artifact["window"]["since"][:10]] = artifact
    heads = {artifact["repository"]["head"] for artifact in artifacts.values()}
    if len(heads) != 1:
        raise ValueError("lineage evaluation requires one frozen endpoint revision")
    head = next(iter(heads))

    file_cache: dict[str, list[str] | None] = {}
    rows = []
    for pair_id, truth_row in sorted(truth_rows.items()):
        base_row = {
            "pair_id": pair_id,
            "day": truth_row["day"],
            "vendor": truth_row["vendor"],
        }
        artifact = artifacts[truth_row["day"]]
        event = next(
            (
                row
                for row in artifact["events"]
                if row["vendor"] == truth_row["vendor"]
                and truth_row["path"] in row["paths"]
                and abs(int(row["ts_ms"]) - int(truth_row["ts_ms"])) <= 1_000
            ),
            None,
        )
        if event is None or event.get("edit_summary") is None:
            rows.append({**base_row, "outcome": "missing_event_edit", "predicted": False})
            continue
        changes = [
            change
            for change in artifact["changes"]
            if change["commit_id"] in truth_row["target_commit_ids"]
            and (change["path"] == truth_row["path"] or change.get("old_path") == truth_row["path"])
        ]
        matched = [
            (change, hunk)
            for change in changes
            for hunk in change["hunks"]
            if hunk_matches(event["edit_summary"], hunk)
            and hunk.get("after_hash")
            and int(hunk["added_lines"]) > 0
        ]
        if not matched:
            rows.append({**base_row, "outcome": "no_added_hunk", "predicted": False})
            continue
        lifetime_by_id = {row["id"]: row for row in artifact["file_lifetimes"]}
        predictions = []
        for change, hunk in matched:
            lifetime = lifetime_by_id[change["lifetime_id"]]
            current_path = lifetime.get("current_path") if lifetime["survives_to_head"] else None
            if current_path is None:
                continue
            if current_path not in file_cache:
                try:
                    content = run(args.repo, "show", f"{head}:{current_path}").decode(
                        "utf-8", errors="strict"
                    )
                    file_cache[current_path] = content.splitlines()
                except (subprocess.CalledProcessError, UnicodeDecodeError):
                    file_cache[current_path] = None
            lines = file_cache[current_path]
            if lines is None:
                continue
            width = int(hunk["added_lines"])
            positions = [
                index + 1
                for index in range(0, len(lines) - width + 1)
                if fingerprint(lines[index : index + width]) == hunk["after_hash"]
            ]
            if len(positions) == 1:
                start = positions[0]
                origins = blame_origins(args.repo, head, current_path, start, start + width - 1)
                predictions.append(
                    {
                        "commit_id": change["commit_id"],
                        "current_path": current_path,
                        "start": start,
                        "end": start + width - 1,
                        "origin_commits": origins,
                        "correct": len(origins) == width
                        and all(origin == change["commit_id"] for origin in origins),
                    }
                )
        if len(predictions) == 1:
            prediction = predictions[0]
            rows.append(
                {
                    **base_row,
                    "outcome": "linked" if prediction["correct"] else "blame_mismatch",
                    "predicted": True,
                    **prediction,
                }
            )
        elif len(predictions) > 1:
            rows.append({**base_row, "outcome": "ambiguous_current_ranges", "predicted": False})
        else:
            rows.append({**base_row, "outcome": "not_unique_at_endpoint", "predicted": False})

    predicted = [row for row in rows if row["predicted"]]
    correct = sum(row.get("correct", False) for row in predicted)
    precision = wilson(correct, len(predicted))
    output = {
        "schema": "agentsight.rq1.lineage-metrics.v1",
        "endpoint_revision": head,
        "target_pairs": len(rows),
        "predicted_line_links": len(predicted),
        "joint_precision": precision,
        "target_link_coverage": len(predicted) / len(rows) if rows else None,
        "outcomes": dict(sorted(Counter(row["outcome"] for row in rows).items())),
        "by_day": {
            day: {
                "target_pairs": sum(row.get("day") == day for row in rows),
                "predicted": sum(row.get("day") == day and row["predicted"] for row in rows),
                "correct": sum(row.get("day") == day and row.get("correct", False) for row in rows),
            }
            for day in sorted(artifacts)
        },
        "by_vendor": {
            vendor: {
                "target_pairs": sum(row.get("vendor") == vendor for row in rows),
                "predicted": sum(row.get("vendor") == vendor and row["predicted"] for row in rows),
                "correct": sum(row.get("vendor") == vendor and row.get("correct", False) for row in rows),
            }
            for vendor in sorted({row.get("vendor") for row in rows if row.get("vendor")})
        },
        "gate": {
            "passes": len(predicted) >= 100 and (precision["low"] or 0) >= 0.95,
            "support_at_least_100": len(predicted) >= 100,
            "precision_wilson_low_at_least_0_95": (precision["low"] or 0) >= 0.95,
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    args.private_output.write_text(
        json.dumps({"schema": "agentsight.rq1.lineage-rows.v1", "rows": rows}, indent=2)
        + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
