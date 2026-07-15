#!/usr/bin/env python3
"""Apply the frozen path-level null rule to RQ1 annotation disagreements."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def load(path: Path) -> dict:
    with path.open(encoding="utf-8") as source:
        return json.load(source)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--packet", type=Path, action="append", required=True)
    parser.add_argument("--disagreements", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    pairs = {}
    for path in args.packet:
        for row in load(path)["pairs"]:
            pairs[row["pair_id"]] = row
    annotations = []
    for disagreement in load(args.disagreements)["rows"]:
        pair_id = disagreement["pair_id"]
        if pair_id not in pairs:
            continue
        pair = pairs[pair_id]
        labels = {
            disagreement["annotator_a"]["label"],
            disagreement["annotator_b"]["label"],
        }
        if labels != {"null", "unadjudicable"}:
            raise ValueError(f"unsupported label disagreement for {pair_id}: {labels}")
        if pair["audit_candidates"]:
            raise ValueError(f"cannot apply no-candidate null rule to {pair_id}")
        annotations.append(
            {
                "pair_id": pair_id,
                "label": "null",
                "target_commit_ids": [],
                "evidence_code": "exhaustive_path_audit_no_candidate",
            }
        )
    output = {
        "schema": "agentsight.rq1.adjudication.v1",
        "policy": "A successful recorded write with no literal or rename-connected Git change in the independent seven-day audit is a path-level null; this does not assert line-level evidence.",
        "annotations": annotations,
    }
    args.output.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
