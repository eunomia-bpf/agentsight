#!/usr/bin/env python3
"""Publish aggregate agreement for a selected mature packet set."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

from reconcile_rq1_annotations import cohen_kappa


def load(path: Path) -> dict:
    with path.open(encoding="utf-8") as source:
        return json.load(source)


def annotation_index(path: Path) -> dict[str, dict]:
    return {row["pair_id"]: row for row in load(path)["annotations"]}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--packet", type=Path, action="append", required=True)
    parser.add_argument("--annotator-a", type=Path, required=True)
    parser.add_argument("--annotator-b", type=Path, required=True)
    parser.add_argument("--adjudication", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    pair_ids = {
        row["pair_id"]
        for packet in args.packet
        for row in load(packet)["pairs"]
    }
    left = annotation_index(args.annotator_a)
    right = annotation_index(args.annotator_b)
    adjudicated = annotation_index(args.adjudication)
    labels_a = [left[pair_id]["label"] for pair_id in sorted(pair_ids)]
    labels_b = [right[pair_id]["label"] for pair_id in sorted(pair_ids)]
    exact = []
    disagreements = []
    final = []
    for pair_id in sorted(pair_ids):
        a = left[pair_id]
        b = right[pair_id]
        same = a["label"] == b["label"] and (
            a["label"] != "target"
            or sorted(a.get("target_commit_ids", []))
            == sorted(b.get("target_commit_ids", []))
        )
        exact.append(same)
        if same:
            final.append(a["label"])
        else:
            disagreements.append(pair_id)
            final.append(adjudicated[pair_id]["label"])
    output = {
        "schema": "agentsight.rq1.annotation-agreement.v2",
        "mature_packet_days": [load(path)["day"] for path in args.packet],
        "pair_count": len(pair_ids),
        "label_agreement": sum(a == b for a, b in zip(labels_a, labels_b, strict=True))
        / len(pair_ids),
        "cohen_kappa": cohen_kappa(labels_a, labels_b),
        "exact_annotation_agreement_count": sum(exact),
        "disagreement_count": len(disagreements),
        "annotator_a_labels": dict(sorted(Counter(labels_a).items())),
        "annotator_b_labels": dict(sorted(Counter(labels_b).items())),
        "adjudicated_labels": dict(sorted(Counter(final).items())),
        "adjudication_policy": "Exhaustive no-change cases are path-level nulls without a line-level claim.",
        "annotator_types": ["independent AI agent", "independent AI agent"],
    }
    args.output.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
