#!/usr/bin/env python3
"""Run the fixed RQ3 OSWorld-Human out-of-fold boundary evaluation.

This is a thin composition runner over operation_boundary_backend_eval.py. It
does not define a new tagger, feature set, dataset, or profiler mechanism.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from operation_boundary_backend_eval import (
    DEFAULT_FEATURE_FIELDS,
    DEFAULT_OPERATION_FILE,
    LEAKAGE_FIELDS,
    LEAKAGE_PREFIXES,
    BernoulliBoundaryModel,
    binary_metrics,
    build_examples,
    field_changed,
    group_sequences,
    load_operations,
    parse_requirement,
    sort_sequences,
)


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BINARY = ROOT / "agentpprof" / "target" / "release" / "agentpprof"
FOLD_SEED = "r297-oof-v1"
FOLD_COUNT = 5
METHODS = ("learned", "action_change", "phase_change", "always_boundary")
SIMPLE_CONTROLS = METHODS[1:]
EXPECTED = {
    "operations": 3978,
    "sessions": 287,
    "pairs": 3691,
    "human_groups": 2042,
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("preflight", "full"), required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--operation-file", type=Path, default=DEFAULT_OPERATION_FILE)
    parser.add_argument("--binary", type=Path, default=DEFAULT_BINARY)
    return parser.parse_args()


def relative(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return str(path.resolve())


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        for row in rows:
            file.write(json.dumps(row, sort_keys=True) + "\n")


def fold_for(sequence_id: str) -> int:
    digest = hashlib.sha256(f"{FOLD_SEED}:{sequence_id}".encode()).hexdigest()
    return int(digest, 16) % FOLD_COUNT


def predictions_for(
    model: BernoulliBoundaryModel, examples: list[dict[str, Any]]
) -> dict[str, list[bool]]:
    return {
        "learned": [model.predict(example["features"]) for example in examples],
        "action_change": [field_changed(example, "action") for example in examples],
        "phase_change": [field_changed(example, "phase") for example in examples],
        "always_boundary": [True for _ in examples],
    }


def exact_f1(metrics: dict[str, Any]) -> float:
    numerator = 2 * int(metrics["true_positive"])
    denominator = numerator + int(metrics["false_positive"]) + int(metrics["false_negative"])
    return numerator / denominator if denominator else 0.0


def evaluate_fold(
    groups: dict[str, list[dict[str, Any]]], sequence_ids: list[str], fold: int
) -> tuple[dict[str, Any], list[dict[str, Any]], dict[str, dict[tuple[str, int], bool]]]:
    train_ids = [sequence for sequence in sequence_ids if fold_for(sequence) != fold]
    test_ids = [sequence for sequence in sequence_ids if fold_for(sequence) == fold]
    if not train_ids or not test_ids:
        raise SystemExit(f"fold {fold} has an empty train or test partition")
    if set(train_ids) & set(test_ids):
        raise SystemExit(f"fold {fold} has train/test session overlap")

    train_examples = build_examples(
        groups, train_ids, DEFAULT_FEATURE_FIELDS, "human_group", "turn"
    )
    test_examples = build_examples(
        groups, test_ids, DEFAULT_FEATURE_FIELDS, "human_group", "turn"
    )
    model = BernoulliBoundaryModel()
    model.fit(train_examples)
    predicted = predictions_for(model, test_examples)
    labels = [bool(example["label"]) for example in test_examples]

    by_pair: dict[str, dict[tuple[str, int], bool]] = {
        method: {} for method in METHODS
    }
    raw_rows = []
    scores = [model.score(example["features"]) for example in test_examples]
    for index, example in enumerate(test_examples):
        key = (example["sequence"], int(example["current"]["_line"]))
        row = {
            "fold": fold,
            "sequence": example["sequence"],
            "previous_line": int(example["previous"]["_line"]),
            "current_line": int(example["current"]["_line"]),
            "label": labels[index],
            "learned_score": scores[index],
        }
        for method in METHODS:
            value = bool(predicted[method][index])
            by_pair[method][key] = value
            row[method] = value
        raw_rows.append(row)

    method_metrics = {}
    for method in METHODS:
        metrics = binary_metrics(predicted[method], labels)
        method_metrics[method] = {**metrics, "f1_exact": exact_f1(metrics)}

    return (
        {
            "fold": fold,
            "train_sessions": len(train_ids),
            "test_sessions": len(test_ids),
            "train_pairs": len(train_examples),
            "test_pairs": len(test_examples),
            "threshold": model.threshold,
            "metrics": method_metrics,
        },
        raw_rows,
        by_pair,
    )


def assign_groups(
    groups: dict[str, list[dict[str, Any]]],
    sequence_ids: list[str],
    by_pair: dict[str, dict[tuple[str, int], bool]],
) -> dict[str, dict[int, str]]:
    assignments: dict[str, dict[int, str]] = {method: {} for method in METHODS}
    for sequence in sequence_ids:
        rows = groups[sequence]
        group_numbers = {method: 0 for method in METHODS}
        for index, operation in enumerate(rows):
            if index:
                key = (sequence, int(operation["_line"]))
                for method in METHODS:
                    if key not in by_pair[method]:
                        raise SystemExit(f"missing {method} prediction for {key}")
                    if by_pair[method][key]:
                        group_numbers[method] += 1
            for method in METHODS:
                assignments[method][int(operation["_line"])] = (
                    f"{sequence}:group-{group_numbers[method]:04d}"
                )
    return assignments


def bcubed(
    groups: dict[str, list[dict[str, Any]]],
    sequence_ids: list[str],
    predicted_group: dict[int, str],
) -> dict[str, float | int]:
    predicted_totals: Counter[str] = Counter()
    oracle_totals: Counter[str] = Counter()
    intersections: Counter[tuple[str, str]] = Counter()
    items: list[tuple[str, str, int]] = []
    for sequence in sequence_ids:
        for operation in groups[sequence]:
            weight = int(operation["value"])
            if weight != 1:
                raise SystemExit("the approved B-cubed evaluation requires unit weights")
            predicted = predicted_group[int(operation["_line"])]
            oracle = f"{sequence}:{operation['fields']['human_group']}"
            predicted_totals[predicted] += weight
            oracle_totals[oracle] += weight
            intersections[(predicted, oracle)] += weight
            items.append((predicted, oracle, weight))

    total_weight = sum(weight for _, _, weight in items)
    precision_sum = 0.0
    recall_sum = 0.0
    for predicted, oracle, weight in items:
        overlap = intersections[(predicted, oracle)]
        precision_sum += weight * overlap / predicted_totals[predicted]
        recall_sum += weight * overlap / oracle_totals[oracle]
    precision = precision_sum / total_weight
    recall = recall_sum / total_weight
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {
        "items": len(items),
        "weight": total_weight,
        "predicted_groups": len(predicted_totals),
        "oracle_groups": len(oracle_totals),
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "distortion": 1.0 - f1,
    }


def scrubbed_operations(
    groups: dict[str, list[dict[str, Any]]],
    sequence_ids: list[str],
    learned_groups: dict[int, str],
) -> list[dict[str, Any]]:
    output = []
    for sequence in sequence_ids:
        for operation in groups[sequence]:
            fields = {
                key: value
                for key, value in operation["fields"].items()
                if key not in LEAKAGE_FIELDS
                and not any(key.startswith(prefix) for prefix in LEAKAGE_PREFIXES)
            }
            fields["learned_group"] = learned_groups[int(operation["_line"])]
            output.append({"fields": fields, "value": int(operation["value"])})
    return output


def run_profiler(
    binary: Path, operation_file: Path, output_path: Path, expected_samples: int
) -> dict[str, Any]:
    if not binary.is_file():
        raise SystemExit(f"missing current release profiler: {relative(binary)}")
    command = [
        str(binary.resolve()),
        "--operation-file",
        str(operation_file.resolve()),
        "--view",
        "operations",
        "--stack",
        "project,dataset,session,learned_group",
        "--format",
        "json",
        "--deterministic-output",
        "-o",
        str(output_path.resolve()),
    ]
    result = subprocess.run(
        command,
        cwd=ROOT,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    write_json(output_path.parent / "profile-command.json", command)
    (output_path.parent / "profile-stdout.json").write_text(result.stdout, encoding="utf-8")
    (output_path.parent / "profile-stderr.txt").write_text(result.stderr, encoding="utf-8")
    if result.returncode:
        raise SystemExit(f"agentpprof failed with exit {result.returncode}")
    try:
        status = json.loads(result.stdout)
        profile = json.loads(output_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        raise SystemExit(f"agentpprof output is not parseable: {exc}") from exc
    samples = int(status.get("samples", -1))
    total_weight = int(profile["profile"]["summary"]["total_weight"])
    if status.get("status") != "ok" or samples != expected_samples:
        raise SystemExit(
            f"agentpprof sample mismatch: status={status.get('status')} "
            f"expected={expected_samples} actual={samples}"
        )
    if total_weight != expected_samples:
        raise SystemExit(
            f"agentpprof mass mismatch: expected={expected_samples} actual={total_weight}"
        )
    return {
        "command": command,
        "status": status.get("status"),
        "samples": samples,
        "total_weight": total_weight,
        "unique_stacks": int(status["unique_stacks"]),
        "profile": relative(output_path),
    }


def merge_pair_predictions(
    destination: dict[str, dict[tuple[str, int], bool]],
    source: dict[str, dict[tuple[str, int], bool]],
) -> None:
    for method in METHODS:
        overlap = set(destination[method]) & set(source[method])
        if overlap:
            raise SystemExit(f"duplicate OOF predictions for {method}: {len(overlap)}")
        destination[method].update(source[method])


def aggregate_metrics(raw_rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    labels = [bool(row["label"]) for row in raw_rows]
    output = {}
    for method in METHODS:
        metrics = binary_metrics([bool(row[method]) for row in raw_rows], labels)
        output[method] = {**metrics, "f1_exact": exact_f1(metrics)}
    return output


def joint_verdict(
    boundary: dict[str, dict[str, Any]], partitions: dict[str, dict[str, Any]]
) -> dict[str, Any]:
    strongest_boundary = max(
        SIMPLE_CONTROLS, key=lambda method: float(boundary[method]["f1_exact"])
    )
    strongest_partition = max(
        SIMPLE_CONTROLS, key=lambda method: float(partitions[method]["f1"])
    )
    boundary_positive = float(boundary["learned"]["f1_exact"]) > float(
        boundary[strongest_boundary]["f1_exact"]
    )
    partition_positive = float(partitions["learned"]["f1"]) > float(
        partitions[strongest_partition]["f1"]
    )
    if boundary_positive and partition_positive:
        verdict = "supported"
    elif boundary_positive or partition_positive:
        verdict = "mixed"
    else:
        verdict = "contradicted"
    return {
        "verdict": verdict,
        "boundary_positive": boundary_positive,
        "boundary_strongest_control": strongest_boundary,
        "boundary_f1_delta": float(boundary["learned"]["f1_exact"])
        - float(boundary[strongest_boundary]["f1_exact"]),
        "partition_positive": partition_positive,
        "partition_strongest_control": strongest_partition,
        "partition_f1_delta": float(partitions["learned"]["f1"])
        - float(partitions[strongest_partition]["f1"]),
    }


def main() -> None:
    args = parse_args()
    out_dir = args.out_dir.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    operations = load_operations(args.operation_file)
    groups = group_sequences(
        operations, "session", "human_group", parse_requirement("group_alignment=exact")
    )
    sort_sequences(groups, "turn")
    sequence_ids = sorted(groups)
    eligible_operations = [operation for sequence in sequence_ids for operation in groups[sequence]]
    source_counts = {
        "operations": len(eligible_operations),
        "sessions": len(sequence_ids),
        "pairs": sum(len(groups[sequence]) - 1 for sequence in sequence_ids),
        "human_groups": len(
            {
                (sequence, operation["fields"]["human_group"])
                for sequence in sequence_ids
                for operation in groups[sequence]
            }
        ),
    }
    if source_counts != EXPECTED:
        raise SystemExit(f"eligible source counts changed: expected={EXPECTED} actual={source_counts}")
    missing_features = sum(
        1
        for operation in eligible_operations
        for field in DEFAULT_FEATURE_FIELDS
        if field not in operation["fields"]
    )
    if missing_features:
        raise SystemExit(f"fixed R297 feature fields have {missing_features} missing values")
    fold_counts = Counter(fold_for(sequence) for sequence in sequence_ids)
    if set(fold_counts) != set(range(FOLD_COUNT)):
        raise SystemExit(f"fold assignment does not cover all folds: {fold_counts}")

    selected_folds = [0] if args.mode == "preflight" else list(range(FOLD_COUNT))
    fold_summaries = []
    raw_rows: list[dict[str, Any]] = []
    all_predictions = {method: {} for method in METHODS}
    for fold in selected_folds:
        fold_summary, fold_rows, fold_predictions = evaluate_fold(groups, sequence_ids, fold)
        fold_summaries.append(fold_summary)
        raw_rows.extend(fold_rows)
        merge_pair_predictions(all_predictions, fold_predictions)
        write_jsonl(out_dir / f"fold-{fold}-predictions.jsonl", fold_rows)

    selected_sequences = [
        sequence for sequence in sequence_ids if fold_for(sequence) in selected_folds
    ]
    expected_pairs = sum(len(groups[sequence]) - 1 for sequence in selected_sequences)
    if len(raw_rows) != expected_pairs:
        raise SystemExit(f"OOF pair mismatch: expected={expected_pairs} actual={len(raw_rows)}")
    for method in METHODS:
        if len(all_predictions[method]) != expected_pairs:
            raise SystemExit(f"{method} prediction coverage is incomplete")

    write_jsonl(out_dir / "oof-predictions.jsonl", raw_rows)
    assignments = assign_groups(groups, selected_sequences, all_predictions)
    partitions = {
        method: bcubed(groups, selected_sequences, assignments[method]) for method in METHODS
    }
    boundary = aggregate_metrics(raw_rows)
    verdict = joint_verdict(boundary, partitions)

    profile_operations = scrubbed_operations(
        groups, selected_sequences, assignments["learned"]
    )
    operation_path = out_dir / "learned-group-operations.jsonl"
    write_jsonl(operation_path, profile_operations)
    profiler = run_profiler(
        args.binary,
        operation_path,
        out_dir / "learned-group-profile.json",
        len(profile_operations),
    )

    summary = {
        "status": "ok",
        "mode": args.mode,
        "operation_file": relative(args.operation_file),
        "binary": relative(args.binary),
        "fold_seed": FOLD_SEED,
        "fold_count": FOLD_COUNT,
        "selected_folds": selected_folds,
        "source_counts": source_counts,
        "fold_session_counts": {str(key): fold_counts[key] for key in sorted(fold_counts)},
        "evaluated": {
            "sessions": len(selected_sequences),
            "operations": len(profile_operations),
            "pairs": len(raw_rows),
        },
        "folds": fold_summaries,
        "boundary_metrics": boundary,
        "partition_metrics": partitions,
        "joint_tested_hypothesis": verdict,
        "profiler": profiler,
        "validity": {
            "expected_source_counts": True,
            "all_folds_nonempty": True,
            "missing_fixed_feature_values": 0,
            "selected_oof_pairs_complete_once": True,
            "profiler_mass_conserved": True,
        },
    }
    write_json(out_dir / "summary.json", summary)
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
