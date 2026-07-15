#!/usr/bin/env python3
"""Apply the frozen path-level null rule to RQ1 annotation disagreements."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def load(path: Path) -> dict:
    with path.open(encoding="utf-8") as source:
        return json.load(source)


def adjudicate_null_disagreement(pair: dict) -> dict:
    if pair["audit_candidates"]:
        return {
            "label": "unadjudicable",
            "target_commit_ids": [],
            "evidence_code": "candidate_without_content_fingerprint",
        }
    return {
        "label": "null",
        "target_commit_ids": [],
        "evidence_code": "exhaustive_path_audit_no_candidate",
    }


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
        annotations.append({"pair_id": pair_id, **adjudicate_null_disagreement(pair)})
    output = {
        "schema": "agentsight.rq1.adjudication.v1",
        "policy": "A successful recorded write with no literal or rename-connected Git change in the independent seven-day audit is a path-level null. If candidates exist but privacy-safe content evidence cannot distinguish them, the pair remains unadjudicable. Neither rule asserts line-level evidence.",
        "annotations": annotations,
    }
    args.output.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
