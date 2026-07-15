#!/usr/bin/env python3
"""Join reconciled labels back to score-free packet metadata for evaluation."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def load(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as source:
        return json.load(source)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--packet", type=Path, action="append", required=True)
    parser.add_argument("--reconciliation", type=Path, required=True)
    parser.add_argument("--adjudication", type=Path)
    parser.add_argument("--exclude-day", action="append", default=[])
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    packet_rows = {}
    for path in args.packet:
        packet = load(path)
        for row in packet["pairs"]:
            if row["day"] in args.exclude_day:
                continue
            if row["pair_id"] in packet_rows:
                raise ValueError(f"duplicate packet pair {row['pair_id']}")
            packet_rows[row["pair_id"]] = row

    reconciliation = load(args.reconciliation)
    labels = {
        row["pair_id"]: {**row, "was_disagreement": False}
        for row in reconciliation["agreed_annotations"]
    }
    if args.adjudication:
        adjudication = load(args.adjudication)
        for row in adjudication["annotations"]:
            labels[row["pair_id"]] = {**row, "was_disagreement": True}

    truth = []
    for pair_id, label in sorted(labels.items()):
        if pair_id not in packet_rows:
            continue
        pair = packet_rows[pair_id]
        truth.append(
            {
                "case_id": pair_id,
                "pair_id": pair_id,
                "day": pair["day"],
                "vendor": pair["vendor"],
                "ts_ms": pair["event_ts_ms"],
                "path": pair["path"],
                "target_commit_ids": sorted(label.get("target_commit_ids", [])),
                "label": label["label"],
                "split": "heldout",
                "scenario": f"naturalistic:{pair['day']}:{pair['action']}",
                "adjudicable": label["label"] != "unadjudicable",
                "was_disagreement": label["was_disagreement"],
                "evidence_codes": label.get("evidence_codes", [label.get("evidence_code", "")]),
            }
        )
    missing = sorted(set(packet_rows).difference(labels))
    output = {
        "schema": "agentsight.rq1.truth.v1",
        "pairs": truth,
        "coverage": {
            "packet_pairs": len(packet_rows),
            "labeled_pairs": len(truth),
            "unresolved_pairs": len(missing),
            "adjudicable_pairs": sum(row["adjudicable"] for row in truth),
            "disagreement_pairs": sum(row["was_disagreement"] for row in truth),
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
