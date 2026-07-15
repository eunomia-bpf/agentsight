#!/usr/bin/env python3
"""Evaluate preregistered RQ1 event-to-Git association methods."""

from __future__ import annotations

import argparse
import json
import math
import random
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable


RETRIEVAL_BEFORE_MS = 15 * 60 * 1_000
RETRIEVAL_AFTER_MS = 24 * 60 * 60 * 1_000
PROPOSED_BINS = [
    "exact_hunk_unique",
    "unique_direct_lifetime",
    "unique_rename_or_prebirth",
    "multi_close_top",
    "multi_other",
]
BASELINE_BINS = ["distance_15m", "distance_1h", "distance_6h", "distance_24h"]


@dataclass(frozen=True)
class Pair:
    case_id: str
    vendor: str
    ts_ms: int
    path: str
    targets: frozenset[str]
    label: str
    split: str
    scenario: str


@dataclass
class RawPrediction:
    pair: Pair
    top: str | None
    candidates: tuple[str, ...]
    evidence_bin: str | None


@dataclass
class ScoredPrediction:
    raw: RawPrediction
    confidence: float
    prediction: str | None

    @property
    def top_correct(self) -> bool:
        return self.raw.top is not None and self.raw.top in self.raw.pair.targets

    @property
    def set_correct(self) -> bool:
        return bool(self.raw.pair.targets.intersection(self.raw.candidates))


def load_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as source:
        return json.load(source)


def load_pairs(
    document: dict[str, Any], *, include_unadjudicable: bool = False
) -> list[Pair]:
    return [
        Pair(
            case_id=row["case_id"],
            vendor=row["vendor"],
            ts_ms=int(row["ts_ms"]),
            path=row["path"],
            targets=frozenset(row.get("target_commit_ids", [])),
            label=row["label"],
            split=row["split"],
            scenario=row["scenario"],
        )
        for row in document["pairs"]
        if include_unadjudicable or row.get("adjudicable", True)
    ]


def pair_key(vendor: str, ts_ms: int, path: str) -> tuple[str, int, str]:
    return vendor, ts_ms, path


def indexes(artifact: dict[str, Any]) -> tuple[dict[str, dict], dict[str, dict], list[dict]]:
    events = {row["id"]: row for row in artifact["events"]}
    associations = {row["event_id"] + "\0" + row["path"]: row for row in artifact["associations"]}
    return events, associations, artifact["changes"]


def find_association(
    pair: Pair,
    events: dict[str, dict],
    associations: dict[str, dict],
) -> dict | None:
    matches: list[tuple[int, str, dict]] = []
    for event in events.values():
        if event["vendor"] != pair.vendor or pair.path not in event["paths"]:
            continue
        distance = abs(int(event["ts_ms"]) - pair.ts_ms)
        if distance > 1_000:
            continue
        association = associations.get(event["id"] + "\0" + pair.path)
        if association is not None:
            matches.append((distance, event["id"], association))
    if not matches:
        return None
    matches.sort(key=lambda item: (item[0], item[1]))
    return matches[0][2]


def proposed_prediction(
    pair: Pair,
    events: dict[str, dict],
    associations: dict[str, dict],
    _changes: list[dict],
) -> RawPrediction:
    association = find_association(pair, events, associations)
    candidates = [] if association is None else sorted(
        association["candidates"], key=lambda row: (int(row["rank"]), row["commit_id"])
    )
    return RawPrediction(
        pair=pair,
        top=candidates[0]["commit_id"] if candidates else None,
        candidates=tuple(row["commit_id"] for row in candidates),
        evidence_bin=candidates[0]["evidence_bin"] if candidates else None,
    )


def candidate_rank(candidate: dict, *, use_hunk: bool) -> tuple:
    match_rank = {"direct_path": 0, "prebirth": 1, "rename_lifetime": 1}.get(
        candidate["match_kind"], 3
    )
    delta = int(candidate["delta_ms"])
    return (
        int(use_hunk and not candidate["exact_hunk_match"]),
        match_rank,
        int(delta < 0),
        abs(delta),
        candidate["commit_id"],
    )


def derived_proposed_prediction(
    pair: Pair,
    events: dict[str, dict],
    associations: dict[str, dict],
    _changes: list[dict],
    *,
    use_hunk: bool,
    literal_only: bool,
) -> RawPrediction:
    association = find_association(pair, events, associations)
    candidates = list(association["candidates"]) if association else []
    if literal_only:
        candidates = [
            row for row in candidates if row["match_kind"] in {"direct_path", "prebirth"}
        ]
    candidates.sort(key=lambda row: candidate_rank(row, use_hunk=use_hunk))
    evidence_bin = None
    if candidates:
        top = candidates[0]
        if use_hunk and len(candidates) == 1 and top["exact_hunk_match"]:
            evidence_bin = "exact_hunk_unique"
        elif len(candidates) == 1 and top["match_kind"] == "direct_path":
            evidence_bin = "unique_direct_lifetime"
        elif len(candidates) == 1:
            evidence_bin = "unique_rename_or_prebirth"
        elif abs(int(top["delta_ms"])) * 4 <= abs(int(candidates[1]["delta_ms"])):
            evidence_bin = "multi_close_top"
        else:
            evidence_bin = "multi_other"
    return RawPrediction(
        pair=pair,
        top=candidates[0]["commit_id"] if candidates else None,
        candidates=tuple(row["commit_id"] for row in candidates),
        evidence_bin=evidence_bin,
    )


def baseline_prediction(
    pair: Pair,
    _events: dict[str, dict],
    _associations: dict[str, dict],
    changes: list[dict],
) -> RawPrediction:
    candidates = []
    for change in changes:
        if change["is_merge"]:
            continue
        if change["path"] != pair.path and change.get("old_path") != pair.path:
            continue
        delta = int(change["committed_at_ms"]) - pair.ts_ms
        if -RETRIEVAL_BEFORE_MS <= delta <= RETRIEVAL_AFTER_MS:
            candidates.append((abs(delta), change["commit_id"], change))
    candidates.sort(key=lambda item: (item[0], item[1]))
    top = candidates[0] if candidates else None
    evidence_bin = None
    if top:
        distance = top[0]
        if distance <= 15 * 60 * 1_000:
            evidence_bin = "distance_15m"
        elif distance <= 60 * 60 * 1_000:
            evidence_bin = "distance_1h"
        elif distance <= 6 * 60 * 60 * 1_000:
            evidence_bin = "distance_6h"
        else:
            evidence_bin = "distance_24h"
    return RawPrediction(
        pair=pair,
        top=top[1] if top else None,
        candidates=(top[1],) if top else (),
        evidence_bin=evidence_bin,
    )


def calibrate(rows: list[RawPrediction]) -> dict[str, float]:
    observed = [row for row in rows if row.top is not None]
    method_correct = sum(row.top in row.pair.targets for row in observed)
    method_rate = (method_correct + 1) / (len(observed) + 2)
    grouped: dict[str, list[RawPrediction]] = defaultdict(list)
    for row in observed:
        if row.evidence_bin:
            grouped[row.evidence_bin].append(row)
    rates = {"__fallback__": method_rate}
    for name, values in grouped.items():
        correct = sum(row.top in row.pair.targets for row in values)
        rates[name] = (correct + 1) / (len(values) + 2)
    return rates


def score(rows: list[RawPrediction], rates: dict[str, float]) -> list[ScoredPrediction]:
    output = []
    for row in rows:
        confidence = 0.0 if row.top is None else rates.get(
            row.evidence_bin or "", rates["__fallback__"]
        )
        output.append(
            ScoredPrediction(
                raw=row,
                confidence=confidence,
                prediction=row.top if row.top is not None and confidence >= 0.5 else None,
            )
        )
    return output


def safe_ratio(numerator: int | float, denominator: int) -> float | None:
    return numerator / denominator if denominator else None


def wilson(successes: int, total: int, z: float = 1.959963984540054) -> dict[str, float | int | None]:
    if total == 0:
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


def ece(rows: list[ScoredPrediction]) -> tuple[float, list[dict[str, Any]]]:
    bins: list[list[ScoredPrediction]] = [[] for _ in range(10)]
    for row in rows:
        index = min(9, int(row.confidence * 10))
        bins[index].append(row)
    total = len(rows)
    value = 0.0
    detail = []
    for index, values in enumerate(bins):
        confidence = safe_ratio(sum(row.confidence for row in values), len(values))
        accuracy = safe_ratio(sum(row.top_correct for row in values), len(values))
        if values:
            value += len(values) / total * abs(float(accuracy) - float(confidence))
        detail.append(
            {
                "bin": index,
                "low": index / 10,
                "high": (index + 1) / 10,
                "count": len(values),
                "mean_confidence": confidence,
                "accuracy": accuracy,
            }
        )
    return value, detail


def summarize(rows: list[ScoredPrediction]) -> dict[str, Any]:
    positives = [row for row in rows if row.raw.pair.targets]
    nulls = [row for row in rows if not row.raw.pair.targets]
    nonnull_predictions = [row for row in rows if row.prediction is not None]
    top_correct = sum(row.prediction in row.raw.pair.targets for row in nonnull_predictions)
    positive_correct = sum(
        row.prediction is not None and row.prediction in row.raw.pair.targets for row in positives
    )
    null_correct = sum(row.prediction is None for row in nulls)
    set_correct = sum(row.set_correct for row in positives)
    brier = safe_ratio(
        sum((row.confidence - float(row.top_correct)) ** 2 for row in rows), len(rows)
    )
    ece_value, calibration_bins = ece(rows)
    precision_ci = wilson(top_correct, len(nonnull_predictions))
    positive_ci = wilson(positive_correct, len(positives))
    null_ci = wilson(null_correct, len(nulls))
    positive_recall = positive_ci["estimate"]
    null_specificity = null_ci["estimate"]
    balanced = (
        (float(positive_recall) + float(null_specificity)) / 2
        if positive_recall is not None and null_specificity is not None
        else None
    )
    return {
        "support": {
            "pairs": len(rows),
            "positive": len(positives),
            "null": len(nulls),
            "nonnull_predictions": len(nonnull_predictions),
        },
        "top1_precision": precision_ci,
        "candidate_set_recall": safe_ratio(set_correct, len(positives)),
        "positive_target_recall": positive_ci,
        "null_target_specificity": null_ci,
        "balanced_accuracy": balanced,
        "mean_candidate_set_size": safe_ratio(
            sum(len(row.raw.candidates) for row in rows), len(rows)
        ),
        "ambiguous_pair_fraction": safe_ratio(
            sum(len(row.raw.candidates) > 1 for row in rows), len(rows)
        ),
        "brier_score": brier,
        "ece_10": ece_value,
        "calibration_bins": calibration_bins,
    }


def gate(summary: dict[str, Any]) -> dict[str, Any]:
    support = summary["support"]
    checks = {
        "positive_support_at_least_50": support["positive"] >= 50,
        "null_support_at_least_50": support["null"] >= 50,
        "precision_wilson_low_at_least_0_90": (summary["top1_precision"]["low"] or 0) >= 0.90,
        "positive_recall_wilson_low_at_least_0_85": (summary["positive_target_recall"]["low"] or 0) >= 0.85,
        "null_specificity_wilson_low_at_least_0_85": (summary["null_target_specificity"]["low"] or 0) >= 0.85,
        "ece_at_most_0_10": summary["ece_10"] <= 0.10,
    }
    return {"passes": all(checks.values()), "checks": checks}


def quantile(values: list[float], probability: float) -> float:
    ordered = sorted(values)
    point = (len(ordered) - 1) * probability
    low = math.floor(point)
    high = math.ceil(point)
    if low == high:
        return ordered[low]
    return ordered[low] * (high - point) + ordered[high] * (point - low)


def bootstrap_difference(
    proposed: list[ScoredPrediction],
    baseline: list[ScoredPrediction],
    *,
    seed: int,
    repetitions: int = 10_000,
) -> dict[str, Any]:
    if len(proposed) != len(baseline):
        raise ValueError("paired methods have different sample sizes")
    rng = random.Random(seed)
    brier_differences = []
    recall_differences = []
    for _ in range(repetitions):
        sample = [rng.randrange(len(proposed)) for _ in proposed]
        proposed_rows = [proposed[index] for index in sample]
        baseline_rows = [baseline[index] for index in sample]
        proposed_brier = sum(
            (row.confidence - float(row.top_correct)) ** 2 for row in proposed_rows
        ) / len(proposed_rows)
        baseline_brier = sum(
            (row.confidence - float(row.top_correct)) ** 2 for row in baseline_rows
        ) / len(baseline_rows)
        brier_differences.append(proposed_brier - baseline_brier)
        proposed_positive = [row for row in proposed_rows if row.raw.pair.targets]
        baseline_positive = [row for row in baseline_rows if row.raw.pair.targets]
        if proposed_positive:
            recall_differences.append(
                sum(row.set_correct for row in proposed_positive) / len(proposed_positive)
                - sum(row.set_correct for row in baseline_positive) / len(baseline_positive)
            )
    return {
        "repetitions": repetitions,
        "seed": seed,
        "proposed_minus_baseline_brier": {
            "low": quantile(brier_differences, 0.025),
            "high": quantile(brier_differences, 0.975),
        },
        "proposed_minus_baseline_candidate_set_recall": {
            "low": quantile(recall_differences, 0.025),
            "high": quantile(recall_differences, 0.975),
        },
    }


def scenario_summary(rows: list[ScoredPrediction]) -> dict[str, Any]:
    grouped: dict[str, list[ScoredPrediction]] = defaultdict(list)
    for row in rows:
        grouped[row.raw.pair.scenario].append(row)
    return {
        name: {
            "pairs": len(values),
            "top_correct": sum(row.top_correct for row in values),
            "set_contains_target": sum(row.set_correct for row in values),
            "predicted_null": sum(row.prediction is None for row in values),
            "candidate_sizes": dict(sorted(Counter(len(row.raw.candidates) for row in values).items())),
        }
        for name, values in sorted(grouped.items())
    }


Method = Callable[[Pair, dict[str, dict], dict[str, dict], list[dict]], RawPrediction]


def evaluate_method(
    name: str,
    method: Method,
    calibration_pairs: list[Pair],
    truth_pairs: list[Pair],
    events: dict[str, dict],
    associations: dict[str, dict],
    changes: list[dict],
) -> tuple[dict[str, Any], list[ScoredPrediction]]:
    calibration_raw = [method(pair, events, associations, changes) for pair in calibration_pairs]
    rates = calibrate(calibration_raw)
    truth_raw = [method(pair, events, associations, changes) for pair in truth_pairs]
    scored = score(truth_raw, rates)
    primary = [row for row in scored if row.raw.pair.split == "heldout"]
    diagnostics = [row for row in scored if row.raw.pair.split == "diagnostic"]
    primary_summary = summarize(primary)
    return (
        {
            "name": name,
            "calibration_confidence": dict(sorted(rates.items())),
            "primary": primary_summary,
            "gate": gate(primary_summary),
            "diagnostics": scenario_summary(diagnostics),
            "by_vendor": {
                vendor: summarize([row for row in primary if row.raw.pair.vendor == vendor])
                for vendor in sorted({row.raw.pair.vendor for row in primary})
            },
        },
        primary,
    )


def select_method(
    proposed: dict[str, Any],
    baseline: dict[str, Any],
    bootstrap: dict[str, Any],
) -> dict[str, str]:
    proposed_passes = proposed["gate"]["passes"]
    baseline_passes = baseline["gate"]["passes"]
    if proposed_passes and not baseline_passes:
        return {"method": "proposed", "reason": "only proposed passed every absolute gate"}
    if baseline_passes and not proposed_passes:
        return {"method": "nearest_literal_path", "reason": "only baseline passed every absolute gate"}
    if not proposed_passes and not baseline_passes:
        return {"method": "descriptive_only", "reason": "neither method passed every absolute gate"}
    brier_ci = bootstrap["proposed_minus_baseline_brier"]
    recall_ci = bootstrap["proposed_minus_baseline_candidate_set_recall"]
    precision_ok = proposed["primary"]["top1_precision"]["low"] >= 0.90
    if precision_ok and (brier_ci["high"] < 0 or recall_ci["low"] > 0):
        return {"method": "proposed", "reason": "paired interval favors proposed without precision violation"}
    return {"method": "nearest_literal_path", "reason": "both passed without decisive paired advantage; prefer simpler method"}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--predictions", type=Path, required=True)
    parser.add_argument("--truth", type=Path, required=True)
    parser.add_argument("--calibration", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--bootstrap-seed", type=int, default=1729)
    args = parser.parse_args()

    artifact = load_json(args.predictions)
    if artifact.get("schema") != "agentsight.longitudinal.v1":
        raise ValueError("unsupported longitudinal artifact schema")
    truth_pairs = load_pairs(load_json(args.truth))
    calibration_pairs = load_pairs(load_json(args.calibration))
    events, associations, changes = indexes(artifact)

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
    reports = {}
    primary_rows = {}
    for name, method in methods.items():
        reports[name], primary_rows[name] = evaluate_method(
            name,
            method,
            calibration_pairs,
            truth_pairs,
            events,
            associations,
            changes,
        )
    paired = bootstrap_difference(
        primary_rows["proposed"],
        primary_rows["nearest_literal_path"],
        seed=args.bootstrap_seed,
    )
    selection = select_method(reports["proposed"], reports["nearest_literal_path"], paired)
    output = {
        "schema": "agentsight.rq1.metrics.v1",
        "protocol": {
            "retrieval_before_ms": RETRIEVAL_BEFORE_MS,
            "retrieval_after_ms": RETRIEVAL_AFTER_MS,
            "bootstrap_seed": args.bootstrap_seed,
            "bootstrap_repetitions": 10_000,
            "ece_bins": 10,
            "confidence": "Laplace-smoothed empirical calibration; null below 0.5",
            "primary_split": "heldout",
        },
        "coverage": {
            "calibration_pairs": len(calibration_pairs),
            "truth_pairs": len(truth_pairs),
            "heldout_pairs": sum(pair.split == "heldout" for pair in truth_pairs),
            "diagnostic_pairs": sum(pair.split == "diagnostic" for pair in truth_pairs),
            "artifact_sessions": artifact["summary"]["session_count"],
            "artifact_events": artifact["summary"]["event_count"],
            "artifact_associations": len(artifact["associations"]),
            "pathless_tool_events_by_vendor": dict(
                sorted(
                    Counter(
                        event["vendor"]
                        for event in artifact["events"]
                        if event["kind"] == "tool" and not event["paths"]
                    ).items()
                )
            ),
        },
        "methods": reports,
        "paired_bootstrap": paired,
        "selection": selection,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
