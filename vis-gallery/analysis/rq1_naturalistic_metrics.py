#!/usr/bin/env python3
"""Evaluate frozen controlled calibration on naturalistic RQ1 annotations."""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

from rq1_metrics import (
    Method,
    baseline_prediction,
    bootstrap_difference,
    derived_proposed_prediction,
    gate,
    indexes,
    load_json,
    load_pairs,
    proposed_prediction,
    score,
    select_method,
    summarize,
)


def public_summary(rows: list, truth_document: dict[str, Any]) -> dict[str, Any]:
    summary = summarize(rows)
    disagreement_ids = {
        row["pair_id"]
        for row in truth_document["pairs"]
        if row.get("was_disagreement") and row.get("adjudicable", True)
    }
    ordinary_correct = []
    sensitivity_correct = []
    for row in rows:
        correct = (
            row.prediction in row.raw.pair.targets
            if row.prediction is not None
            else not row.raw.pair.targets
        )
        ordinary_correct.append(correct)
        sensitivity_correct.append(correct and row.raw.pair.case_id not in disagreement_ids)
    summary["classification_accuracy"] = sum(ordinary_correct) / len(ordinary_correct) if rows else None
    summary["disagreement_as_error_accuracy"] = (
        sum(sensitivity_correct) / len(sensitivity_correct) if rows else None
    )
    return summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--controlled-metrics", type=Path, required=True)
    parser.add_argument("--truth", type=Path, required=True)
    parser.add_argument("--artifact", type=Path, action="append", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--bootstrap-seed", type=int, default=1729)
    args = parser.parse_args()

    controlled = load_json(args.controlled_metrics)
    truth_document = load_json(args.truth)
    truth_pairs = load_pairs(truth_document)
    pairs_by_day = defaultdict(list)
    for pair in truth_pairs:
        day = pair.scenario.split(":", 2)[1]
        pairs_by_day[day].append(pair)

    methods: dict[str, Method] = {
        "proposed": proposed_prediction,
        "nearest_literal_path": baseline_prediction,
        "ablation_no_hunk": lambda *values: derived_proposed_prediction(
            *values, use_hunk=False, literal_only=False
        ),
        "ablation_literal_only": lambda *values: derived_proposed_prediction(
            *values, use_hunk=True, literal_only=True
        ),
    }
    scored_by_method = {name: [] for name in methods}
    scored_by_day = {name: defaultdict(list) for name in methods}
    artifact_coverage = []
    for artifact_path in args.artifact:
        artifact = load_json(artifact_path)
        day = artifact["window"]["since"][:10]
        events, associations, changes = indexes(artifact)
        day_pairs = pairs_by_day[day]
        artifact_coverage.append(
            {
                "day": day,
                "sessions": artifact["summary"]["session_count"],
                "events": artifact["summary"]["event_count"],
                "write_event_paths": artifact["summary"]["write_event_path_count"],
                "adjudicable_pairs": len(day_pairs),
            }
        )
        for name, method in methods.items():
            raw = [method(pair, events, associations, changes) for pair in day_pairs]
            rates = controlled["methods"][name]["calibration_confidence"]
            values = score(raw, rates)
            scored_by_method[name].extend(values)
            scored_by_day[name][day].extend(values)

    reports = {}
    for name, rows in scored_by_method.items():
        overall = public_summary(rows, truth_document)
        reports[name] = {
            "overall": overall,
            "gate": gate(overall),
            "by_day": {
                day: public_summary(values, truth_document)
                for day, values in sorted(scored_by_day[name].items())
            },
            "by_vendor": {
                vendor: public_summary(
                    [row for row in rows if row.raw.pair.vendor == vendor], truth_document
                )
                for vendor in sorted({row.raw.pair.vendor for row in rows})
            },
        }
    paired = bootstrap_difference(
        scored_by_method["proposed"],
        scored_by_method["nearest_literal_path"],
        seed=args.bootstrap_seed,
    )
    selection_view = {
        name: {"gate": report["gate"], "primary": report["overall"]}
        for name, report in reports.items()
    }
    output = {
        "schema": "agentsight.rq1.naturalistic-metrics.v1",
        "calibration_source": "controlled held-out experiment; no naturalistic tuning",
        "truth_coverage": truth_document.get("coverage", {}),
        "artifact_coverage": artifact_coverage,
        "methods": reports,
        "paired_bootstrap": paired,
        "selection": select_method(
            selection_view["proposed"], selection_view["nearest_literal_path"], paired
        ),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
