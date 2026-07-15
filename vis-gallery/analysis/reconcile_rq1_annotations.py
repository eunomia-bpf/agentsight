#!/usr/bin/env python3
"""Measure agreement and reconcile two independent RQ1 annotations."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any


def load(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as source:
        return json.load(source)


def index(document: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {row["pair_id"]: row for row in document["annotations"]}


def cohen_kappa(labels_a: list[str], labels_b: list[str]) -> float | None:
    if not labels_a:
        return None
    categories = sorted(set(labels_a).union(labels_b))
    observed = sum(a == b for a, b in zip(labels_a, labels_b, strict=True)) / len(labels_a)
    counts_a = Counter(labels_a)
    counts_b = Counter(labels_b)
    expected = sum(
        counts_a[label] / len(labels_a) * counts_b[label] / len(labels_b)
        for label in categories
    )
    return (observed - expected) / (1 - expected) if expected < 1 else 1.0


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--annotator-a", type=Path, required=True)
    parser.add_argument("--annotator-b", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--disagreements", type=Path, required=True)
    args = parser.parse_args()
    document_a = load(args.annotator_a)
    document_b = load(args.annotator_b)
    rows_a = index(document_a)
    rows_b = index(document_b)
    if set(rows_a) != set(rows_b):
        raise ValueError("annotators labeled different pair sets")
    labels_a = []
    labels_b = []
    agreed = []
    disagreements = []
    for pair_id in sorted(rows_a):
        left = rows_a[pair_id]
        right = rows_b[pair_id]
        labels_a.append(left["label"])
        labels_b.append(right["label"])
        same_target = sorted(left.get("target_commit_ids", [])) == sorted(
            right.get("target_commit_ids", [])
        )
        if left["label"] == right["label"] and (
            left["label"] != "target" or same_target
        ):
            agreed.append(
                {
                    "pair_id": pair_id,
                    "label": left["label"],
                    "target_commit_ids": sorted(left.get("target_commit_ids", [])),
                    "evidence_codes": sorted(
                        {left.get("evidence_code", ""), right.get("evidence_code", "")}
                    ),
                }
            )
        else:
            disagreements.append(
                {
                    "pair_id": pair_id,
                    "annotator_a": left,
                    "annotator_b": right,
                }
            )
    result = {
        "schema": "agentsight.rq1.reconciliation.v1",
        "annotator_types": [
            document_a.get("annotator_type", "unspecified"),
            document_b.get("annotator_type", "unspecified"),
        ],
        "pair_count": len(labels_a),
        "label_agreement": sum(a == b for a, b in zip(labels_a, labels_b, strict=True))
        / len(labels_a)
        if labels_a
        else None,
        "cohen_kappa": cohen_kappa(labels_a, labels_b),
        "target_set_exact_agreement_count": len(agreed),
        "disagreement_count": len(disagreements),
        "agreed_annotations": agreed,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    args.disagreements.write_text(
        json.dumps(
            {"schema": "agentsight.rq1.disagreements.v1", "rows": disagreements},
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
