#!/usr/bin/env python3
"""Evaluate recurrence-based operation-stack induction on existing OSWorld data.

The candidate learns normalized pointwise mutual information (NPMI) for visible
adjacent action pairs from four session folds and predicts groups only in the
held-out fold. Official human groups are loaded by the scorer but never passed
to the candidate. The run reuses the exact Step 0006 population, folds,
controls, B-cubed scorer, and Step 0018 cap-free Rust baseline.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import statistics
import subprocess
from collections import Counter
from pathlib import Path
from typing import Any

from operation_boundary_backend_eval import (
    DEFAULT_OPERATION_FILE,
    LEAKAGE_FIELDS,
    LEAKAGE_PREFIXES,
    binary_metrics,
    group_sequences,
    load_operations,
    parse_requirement,
    sort_sequences,
)
from operation_induced_stack_scoring_eval import safe_frame
from rq3_osworld_boundary_fidelity_eval import bcubed, exact_f1


ROOT = Path(__file__).resolve().parents[1]
FOLD_COUNT = 5
FOLD_SEED = "r297-oof-v1"
EXPECTED = {
    "operations": 3978,
    "sessions": 287,
    "pairs": 3691,
    "human_groups": 2042,
}
DEFAULT_BINARY = ROOT / "agentpprof" / "target" / "release" / "agentpprof"
DEFAULT_STEP18 = (
    ROOT
    / ".agentsight"
    / "experiments"
    / "rq3-rust-inducer-depth-v1"
    / "full"
)
DEFAULT_STEP6_SUMMARY = (
    ROOT
    / ".agentsight"
    / "experiments"
    / "rq3-osworld-boundary-fidelity-v1"
    / "full"
    / "summary.json"
)
SIMPLE_CONTROLS = ("action_change", "phase_change", "always_boundary")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("preflight", "full"), required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--operation-file", type=Path, default=DEFAULT_OPERATION_FILE)
    parser.add_argument("--binary", type=Path, default=DEFAULT_BINARY)
    parser.add_argument("--step18-dir", type=Path, default=DEFAULT_STEP18)
    parser.add_argument("--step6-summary", type=Path, default=DEFAULT_STEP6_SUMMARY)
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
    with path.open("w", encoding="utf-8") as output:
        for row in rows:
            output.write(json.dumps(row, sort_keys=True) + "\n")


def fold_for(sequence: str) -> int:
    digest = hashlib.sha256(f"{FOLD_SEED}:{sequence}".encode()).hexdigest()
    return int(digest, 16) % FOLD_COUNT


def visible_action_sequences(
    groups: dict[str, list[dict[str, Any]]], sequence_ids: list[str]
) -> dict[str, list[str]]:
    """Return the candidate's complete input; no scorer label enters this object."""
    output: dict[str, list[str]] = {}
    for sequence in sequence_ids:
        actions = []
        for operation in groups[sequence]:
            action = operation["fields"].get("action")
            if not action:
                raise SystemExit(f"missing visible action in session {sequence}")
            actions.append(str(action))
        if len(actions) < 2:
            raise SystemExit(f"eligible session has fewer than two actions: {sequence}")
        output[sequence] = actions
    return output


def transition_npmi(
    train_ids: list[str], visible: dict[str, list[str]]
) -> tuple[dict[tuple[str, str], float], list[float], dict[str, Any]]:
    left_counts: Counter[str] = Counter()
    right_counts: Counter[str] = Counter()
    pair_counts: Counter[tuple[str, str]] = Counter()
    for sequence in train_ids:
        actions = visible[sequence]
        left_counts.update(actions[:-1])
        right_counts.update(actions[1:])
        pair_counts.update(zip(actions, actions[1:]))
    transitions = sum(pair_counts.values())
    if transitions <= 0:
        raise SystemExit("NPMI training fold has zero transitions")

    scores: dict[tuple[str, str], float] = {}
    for (left, right), count in sorted(pair_counts.items()):
        p_pair = count / transitions
        p_left = left_counts[left] / transitions
        p_right = right_counts[right] / transitions
        if p_pair == 1.0:
            score = 1.0
        else:
            denominator = -math.log(p_pair)
            if denominator <= 0.0:
                raise SystemExit(f"non-positive NPMI denominator for {(left, right)}")
            score = math.log(p_pair / (p_left * p_right)) / denominator
        if not math.isfinite(score):
            raise SystemExit(f"non-finite NPMI for {(left, right)}")
        scores[(left, right)] = score

    occurrence_scores = [
        scores[(left, right)]
        for sequence in train_ids
        for left, right in zip(visible[sequence], visible[sequence][1:])
    ]
    if len(occurrence_scores) != transitions:
        raise SystemExit("transition-score coverage differs from training transitions")
    return (
        scores,
        occurrence_scores,
        {
            "training_transitions": transitions,
            "unique_left_actions": len(left_counts),
            "unique_right_actions": len(right_counts),
            "unique_action_pairs": len(pair_counts),
        },
    )


def deterministic_two_means(scores: list[float]) -> dict[str, Any]:
    if not scores or any(not math.isfinite(score) for score in scores):
        raise SystemExit("two-means requires finite transition scores")
    low = min(scores)
    high = max(scores)
    if low == high:
        raise SystemExit("two-means requires at least two distinct transition scores")

    converged = False
    iterations = 0
    low_count = high_count = 0
    for iteration in range(1, 101):
        low_cluster = []
        high_cluster = []
        for score in scores:
            if abs(score - low) <= abs(score - high):
                low_cluster.append(score)
            else:
                high_cluster.append(score)
        if not low_cluster or not high_cluster:
            raise SystemExit("two-means produced an empty cluster")
        next_low = statistics.fmean(low_cluster)
        next_high = statistics.fmean(high_cluster)
        if next_low > next_high:
            next_low, next_high = next_high, next_low
        iterations = iteration
        low_count = len(low_cluster)
        high_count = len(high_cluster)
        if next_low == low and next_high == high:
            converged = True
            low, high = next_low, next_high
            break
        low, high = next_low, next_high
    if not converged:
        raise SystemExit("two-means did not converge within 100 iterations")
    cutoff = (low + high) / 2.0
    if not all(math.isfinite(value) for value in (low, high, cutoff)):
        raise SystemExit("two-means emitted a non-finite center or cutoff")
    return {
        "low_center": low,
        "high_center": high,
        "cutoff": cutoff,
        "iterations": iterations,
        "low_occurrences": low_count,
        "high_occurrences": high_count,
    }


def predict_fold(
    fold: int,
    sequence_ids: list[str],
    visible: dict[str, list[str]],
) -> tuple[dict[tuple[str, int], dict[str, Any]], dict[str, Any]]:
    train_ids = [sequence for sequence in sequence_ids if fold_for(sequence) != fold]
    test_ids = [sequence for sequence in sequence_ids if fold_for(sequence) == fold]
    if not train_ids or not test_ids or set(train_ids) & set(test_ids):
        raise SystemExit(f"fold {fold} does not have a disjoint nonempty split")
    association, occurrence_scores, counts = transition_npmi(train_ids, visible)
    clusters = deterministic_two_means(occurrence_scores)

    predictions: dict[tuple[str, int], dict[str, Any]] = {}
    unseen = 0
    for sequence in test_ids:
        actions = visible[sequence]
        for position, (left, right) in enumerate(zip(actions, actions[1:]), 1):
            score = association.get((left, right))
            boundary = score is None or score < clusters["cutoff"]
            if score is None:
                unseen += 1
            key = (sequence, position)
            if key in predictions:
                raise SystemExit(f"duplicate fold prediction: {key}")
            predictions[key] = {
                "boundary": boundary,
                "npmi": score,
                "left_action": left,
                "right_action": right,
                "unseen_in_training": score is None,
            }
    return predictions, {
        "fold": fold,
        "train_sessions": len(train_ids),
        "test_sessions": len(test_ids),
        "test_pairs": len(predictions),
        "unseen_test_pairs": unseen,
        **counts,
        **clusters,
    }


def run_length_motif(actions: list[str]) -> str:
    compact = []
    for action in actions:
        if not compact or compact[-1] != action:
            compact.append(action)
    if not compact:
        raise SystemExit("cannot name an empty operation motif")
    raw = "action=" + "-then-".join(compact)
    if not safe_frame(raw, "operation"):
        raise SystemExit(f"motif produced an empty safe frame: {raw}")
    return raw


def candidate_assignments(
    groups: dict[str, list[dict[str, Any]]],
    selected_ids: list[str],
    fold_predictions: dict[tuple[str, int], dict[str, Any]],
) -> tuple[dict[int, str], dict[int, str], list[dict[str, Any]], list[int]]:
    predicted_groups: dict[int, str] = {}
    motifs: dict[int, str] = {}
    sessions = []
    lengths = []
    for sequence in selected_ids:
        rows = groups[sequence]
        boundaries = [0]
        for position in range(1, len(rows)):
            key = (sequence, position)
            if key not in fold_predictions:
                raise SystemExit(f"missing candidate prediction: {key}")
            if fold_predictions[key]["boundary"]:
                boundaries.append(position)
        boundaries.append(len(rows))
        group_rows = []
        for group_number, (start, end) in enumerate(zip(boundaries, boundaries[1:])):
            actions = [row["fields"]["action"] for row in rows[start:end]]
            motif = run_length_motif(actions)
            lengths.append(end - start)
            for row in rows[start:end]:
                line = int(row["_line"])
                predicted_groups[line] = f"{sequence}:group-{group_number:04d}"
                motifs[line] = motif
            group_rows.append(
                {
                    "group": group_number,
                    "start": start,
                    "end": end,
                    "length": end - start,
                    "motif": motif,
                }
            )
        sessions.append(
            {
                "sequence": sequence,
                "fold": fold_for(sequence),
                "operations": len(rows),
                "predicted_groups": len(group_rows),
                "groups": group_rows,
            }
        )
    return predicted_groups, motifs, sessions, lengths


def scorer_pair_rows(
    groups: dict[str, list[dict[str, Any]]],
    selected_ids: list[str],
    fold_predictions: dict[tuple[str, int], dict[str, Any]],
) -> list[dict[str, Any]]:
    rows = []
    for sequence in selected_ids:
        operations = groups[sequence]
        for position, (previous, current) in enumerate(zip(operations, operations[1:]), 1):
            prediction = fold_predictions[(sequence, position)]
            label = previous["fields"]["human_group"] != current["fields"]["human_group"]
            rows.append(
                {
                    "sequence": sequence,
                    "fold": fold_for(sequence),
                    "previous_line": int(previous["_line"]),
                    "current_line": int(current["_line"]),
                    "left_action": prediction["left_action"],
                    "right_action": prediction["right_action"],
                    "npmi": prediction["npmi"],
                    "unseen_in_training": prediction["unseen_in_training"],
                    "recurrence": bool(prediction["boundary"]),
                    "action_change": previous["fields"].get("action")
                    != current["fields"].get("action"),
                    "phase_change": previous["fields"].get("phase")
                    != current["fields"].get("phase"),
                    "always_boundary": True,
                    "label": label,
                }
            )
    return rows


def aggregate_binary(rows: list[dict[str, Any]], method: str) -> dict[str, Any]:
    metrics = binary_metrics(
        [bool(row[method]) for row in rows], [bool(row["label"]) for row in rows]
    )
    return {**metrics, "f1_exact": exact_f1(metrics)}


def assignments_from_pair_method(
    groups: dict[str, list[dict[str, Any]]],
    selected_ids: list[str],
    rows: list[dict[str, Any]],
    method: str,
) -> dict[int, str]:
    by_key = {(row["sequence"], int(row["current_line"])): bool(row[method]) for row in rows}
    assignments = {}
    for sequence in selected_ids:
        group_number = 0
        for position, operation in enumerate(groups[sequence]):
            if position:
                key = (sequence, int(operation["_line"]))
                if key not in by_key:
                    raise SystemExit(f"missing {method} pair assignment: {key}")
                if by_key[key]:
                    group_number += 1
            assignments[int(operation["_line"])] = f"{sequence}:group-{group_number:04d}"
    return assignments


def load_step18_baseline(
    step18_dir: Path,
    groups: dict[str, list[dict[str, Any]]],
    selected_ids: list[str],
    operation_file: Path,
) -> tuple[dict[str, Any], dict[int, str]]:
    pair_file = step18_dir / "pair-predictions.jsonl"
    session_file = step18_dir / "session-results.jsonl"
    summary_file = step18_dir / "summary.json"
    if not pair_file.is_file() or not session_file.is_file() or not summary_file.is_file():
        raise SystemExit(f"missing Step 0018 baseline artifacts: {relative(step18_dir)}")

    summary = json.loads(summary_file.read_text(encoding="utf-8"))
    method = summary.get("methods", {}).get("depth_unbounded", {})
    validity = summary.get("validity", {})
    expected_evaluated = {key: EXPECTED[key] for key in ("operations", "pairs", "sessions")}
    if (
        summary.get("status") != "ok"
        or summary.get("mode") != "full"
        or summary.get("operation_file") != relative(operation_file)
        or summary.get("complete_source_counts") != EXPECTED
        or summary.get("evaluated") != expected_evaluated
        or method.get("policy") != "recursive-information-gain-operation-stack-induction"
        or method.get("max_depth") != 255
        or validity.get("complete_population_in_full_mode") is not True
        or validity.get("depth_unbounded_nonbinding") is not True
        or validity.get("all_decisions_consumed") is not True
        or validity.get("terminal_assignment_once_per_operation") is not True
    ):
        raise SystemExit("Step 0018 summary does not match the registered full cap-free baseline")

    selected = set(selected_ids)
    expected_pairs: dict[tuple[str, int], dict[str, Any]] = {}
    for sequence in selected_ids:
        for previous, current in zip(groups[sequence], groups[sequence][1:]):
            key = (sequence, int(current["_line"]))
            if key in expected_pairs:
                raise SystemExit(f"duplicate current-source pair key: {key}")
            expected_pairs[key] = {
                "previous_line": int(previous["_line"]),
                "label": previous["fields"]["human_group"]
                != current["fields"]["human_group"],
            }

    pair_rows: dict[tuple[str, int], dict[str, Any]] = {}
    with pair_file.open(encoding="utf-8") as source:
        for line in source:
            row = json.loads(line)
            if row["sequence"] in selected:
                key = (row["sequence"], int(row["current_line"]))
                if key in pair_rows:
                    raise SystemExit(f"duplicate Step 0018 pair key: {key}")
                expected = expected_pairs.get(key)
                if expected is None:
                    raise SystemExit(f"unexpected Step 0018 pair key: {key}")
                if (
                    int(row["previous_line"]) != expected["previous_line"]
                    or bool(row["label"]) != expected["label"]
                ):
                    raise SystemExit(f"Step 0018 pair differs from current source: {key}")
                pair_rows[key] = row
    if set(pair_rows) != set(expected_pairs):
        raise SystemExit("Step 0018 selected pair keys do not exactly cover current source")
    metrics = binary_metrics(
        [bool(pair_rows[key]["depth_unbounded"]) for key in sorted(expected_pairs)],
        [bool(expected_pairs[key]["label"]) for key in sorted(expected_pairs)],
    )
    metrics = {**metrics, "f1_exact": exact_f1(metrics)}

    by_session = {}
    with session_file.open(encoding="utf-8") as source:
        for line in source:
            row = json.loads(line)
            if row.get("method") == "depth_unbounded" and row["sequence"] in selected:
                if row["sequence"] in by_session:
                    raise SystemExit(f"duplicate Step 0018 session: {row['sequence']}")
                by_session[row["sequence"]] = row
    if set(by_session) != selected:
        raise SystemExit("Step 0018 selected session coverage mismatch")

    assignments = {}
    for sequence in selected_ids:
        session = by_session[sequence]
        paths = session["paths"]
        operations = groups[sequence]
        if (
            session.get("policy") != "recursive-information-gain-operation-stack-induction"
            or int(session.get("configured_max_depth", -1)) != 255
            or int(session.get("operations", -1)) != len(operations)
            or int(session.get("pairs", -1)) != len(operations) - 1
            or int(session.get("mass", -1)) != len(operations)
            or len(paths) != len(operations)
            or "max_depth" in session.get("stop_reasons", {})
        ):
            raise SystemExit(f"Step 0018 session metadata or coverage mismatch: {sequence}")
        group_number = 0
        for position, (operation, path) in enumerate(zip(operations, paths)):
            if position:
                key = (sequence, int(operation["_line"]))
                path_boundary = path != paths[position - 1]
                if path_boundary != bool(pair_rows[key]["depth_unbounded"]):
                    raise SystemExit(f"Step 0018 path/pair decision mismatch: {key}")
                if path_boundary:
                    group_number += 1
            assignments[int(operation["_line"])] = f"{sequence}:group-{group_number:04d}"
    return metrics, assignments


def candidate_operation_rows(
    groups: dict[str, list[dict[str, Any]]],
    selected_ids: list[str],
    motifs: dict[int, str],
) -> list[dict[str, Any]]:
    output = []
    for sequence in selected_ids:
        for operation in groups[sequence]:
            fields = {
                key: value
                for key, value in operation["fields"].items()
                if key not in LEAKAGE_FIELDS
                and not any(key.startswith(prefix) for prefix in LEAKAGE_PREFIXES)
            }
            fields["operation"] = motifs[int(operation["_line"])]
            if any(
                key in LEAKAGE_FIELDS or any(key.startswith(prefix) for prefix in LEAKAGE_PREFIXES)
                for key in fields
            ):
                raise SystemExit("scorer field survived candidate-operation scrubbing")
            output.append({"fields": fields, "value": int(operation["value"])})
    return output


def run_profiler(
    binary: Path, operation_file: Path, profile_file: Path, expected_samples: int
) -> dict[str, Any]:
    if not binary.is_file():
        raise SystemExit(f"missing current profiler: {relative(binary)}")
    version = subprocess.run(
        [str(binary.resolve()), "--version"],
        cwd=ROOT,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    version_text = (version.stdout or version.stderr).strip()
    if version.returncode or version_text != "agentpprof 0.2.37":
        raise SystemExit(f"unexpected profiler version: {version_text!r}")
    command = [
        str(binary.resolve()),
        "--operation-file",
        str(operation_file.resolve()),
        "--view",
        "operations",
        "--stack",
        "project,dataset,operation",
        "--format",
        "json",
        "--deterministic-output",
        "-o",
        str(profile_file.resolve()),
    ]
    completed = subprocess.run(
        command,
        cwd=ROOT,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    write_json(profile_file.parent / "profile-command.json", command)
    (profile_file.parent / "profile-stdout.json").write_text(
        completed.stdout, encoding="utf-8"
    )
    (profile_file.parent / "profile-stderr.txt").write_text(
        completed.stderr, encoding="utf-8"
    )
    if completed.returncode:
        raise SystemExit(f"agentpprof failed with exit {completed.returncode}")
    status = json.loads(completed.stdout)
    profile = json.loads(profile_file.read_text(encoding="utf-8"))
    samples = int(status.get("samples", -1))
    total_weight = int(profile["profile"]["summary"]["total_weight"])
    if status.get("status") != "ok" or samples != expected_samples:
        raise SystemExit(
            f"agentpprof sample mismatch: expected={expected_samples} actual={samples}"
        )
    if total_weight != expected_samples:
        raise SystemExit(
            f"agentpprof mass mismatch: expected={expected_samples} actual={total_weight}"
        )
    return {
        "version": version_text,
        "command": command,
        "status": status["status"],
        "samples": samples,
        "total_weight": total_weight,
        "unique_stacks": int(status["unique_stacks"]),
        "profile": relative(profile_file),
    }


def verdict(
    boundary: dict[str, dict[str, Any]], partition: dict[str, dict[str, Any]]
) -> dict[str, Any]:
    strongest_boundary = max(
        SIMPLE_CONTROLS, key=lambda method: float(boundary[method]["f1_exact"])
    )
    strongest_partition = max(
        SIMPLE_CONTROLS, key=lambda method: float(partition[method]["f1"])
    )
    candidate_boundary = float(boundary["recurrence"]["f1_exact"])
    candidate_partition = float(partition["recurrence"]["f1"])
    current_boundary = float(boundary["current_information_gain"]["f1_exact"])
    current_partition = float(partition["current_information_gain"]["f1"])
    improves_current = (
        candidate_boundary > current_boundary and candidate_partition > current_partition
    )
    clears_simple = (
        candidate_boundary > float(boundary[strongest_boundary]["f1_exact"])
        and candidate_partition > float(partition[strongest_partition]["f1"])
    )
    improves_neither = (
        candidate_boundary <= current_boundary and candidate_partition <= current_partition
    )
    clears_neither = (
        candidate_boundary <= float(boundary[strongest_boundary]["f1_exact"])
        and candidate_partition <= float(partition[strongest_partition]["f1"])
    )
    if improves_current and clears_simple:
        result = "supported"
    elif improves_neither or clears_neither:
        result = "contradicted"
    else:
        result = "mixed"
    return {
        "verdict": result,
        "strongest_boundary_control": strongest_boundary,
        "strongest_partition_control": strongest_partition,
        "improves_current_on_both": improves_current,
        "clears_strongest_simple_on_both": clears_simple,
        "boundary_delta_vs_current": candidate_boundary - current_boundary,
        "partition_delta_vs_current": candidate_partition - current_partition,
        "boundary_delta_vs_strongest_simple": candidate_boundary
        - float(boundary[strongest_boundary]["f1_exact"]),
        "partition_delta_vs_strongest_simple": candidate_partition
        - float(partition[strongest_partition]["f1"]),
    }


def main() -> None:
    args = parse_args()
    out_dir = args.out_dir if args.out_dir.is_absolute() else ROOT / args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    operations = load_operations(args.operation_file)
    groups = group_sequences(
        operations, "session", "human_group", parse_requirement("group_alignment=exact")
    )
    sort_sequences(groups, "turn")
    sequence_ids = sorted(groups)
    source_counts = {
        "operations": sum(len(rows) for rows in groups.values()),
        "sessions": len(groups),
        "pairs": sum(len(rows) - 1 for rows in groups.values()),
        "human_groups": len(
            {
                (sequence, operation["fields"]["human_group"])
                for sequence, rows in groups.items()
                for operation in rows
            }
        ),
    }
    if source_counts != EXPECTED:
        raise SystemExit(f"source population mismatch: {source_counts}")

    visible = visible_action_sequences(groups, sequence_ids)
    selected_folds = [0] if args.mode == "preflight" else list(range(FOLD_COUNT))
    selected_ids = [sequence for sequence in sequence_ids if fold_for(sequence) in selected_folds]
    all_predictions: dict[tuple[str, int], dict[str, Any]] = {}
    fold_reports = []
    for fold in selected_folds:
        predictions, report = predict_fold(fold, sequence_ids, visible)
        overlap = set(all_predictions) & set(predictions)
        if overlap:
            raise SystemExit(f"duplicate out-of-fold candidate predictions: {len(overlap)}")
        all_predictions.update(predictions)
        fold_reports.append(report)

    expected_selected_pairs = sum(len(groups[sequence]) - 1 for sequence in selected_ids)
    if len(all_predictions) != expected_selected_pairs:
        raise SystemExit("selected out-of-fold candidate predictions are incomplete")

    candidate_groups, motifs, session_rows, group_lengths = candidate_assignments(
        groups, selected_ids, all_predictions
    )
    pair_rows = scorer_pair_rows(groups, selected_ids, all_predictions)
    if len(pair_rows) != expected_selected_pairs:
        raise SystemExit("scorer pair rows are incomplete")

    boundary = {
        method: aggregate_binary(pair_rows, method)
        for method in ("recurrence", *SIMPLE_CONTROLS)
    }
    partition = {}
    partition["recurrence"] = bcubed(groups, selected_ids, candidate_groups)
    for method in SIMPLE_CONTROLS:
        assignments = assignments_from_pair_method(groups, selected_ids, pair_rows, method)
        partition[method] = bcubed(groups, selected_ids, assignments)

    step18_boundary, step18_groups = load_step18_baseline(
        args.step18_dir, groups, selected_ids, args.operation_file
    )
    boundary["current_information_gain"] = step18_boundary
    partition["current_information_gain"] = bcubed(groups, selected_ids, step18_groups)

    step6 = json.loads(args.step6_summary.read_text(encoding="utf-8"))
    if args.mode == "full":
        boundary["supervised_oof"] = step6["boundary_metrics"]["learned"]
        partition["supervised_oof"] = step6["partition_metrics"]["learned"]

    candidate_rows = candidate_operation_rows(groups, selected_ids, motifs)
    operation_file = out_dir / "candidate-operations.jsonl"
    profile_file = out_dir / "candidate-profile.json"
    write_jsonl(operation_file, candidate_rows)
    profiler = run_profiler(args.binary, operation_file, profile_file, len(candidate_rows))

    write_jsonl(out_dir / "pair-predictions.jsonl", pair_rows)
    write_jsonl(out_dir / "session-results.jsonl", session_rows)
    summary = {
        "schema": "agentsight.rq3-recurrence-stack-induction.v1",
        "mode": args.mode,
        "scientific_role": "post-hoc mechanism development on an already observed population",
        "paper_promotion": "prohibited as fresh confirmatory RQ3 evidence",
        "operation_file": relative(args.operation_file),
        "step18_baseline": relative(args.step18_dir),
        "step18_commit": "7218564980d12fe3f493eed245fac03f0980cf2d",
        "source_counts": source_counts,
        "selected_folds": selected_folds,
        "selected_sessions": len(selected_ids),
        "selected_operations": len(candidate_rows),
        "selected_pairs": len(pair_rows),
        "fold_seed": FOLD_SEED,
        "algorithm": {
            "policy": "cross-session-action-transition-npmi-segmentation",
            "visible_field": "action",
            "association": "NPMI with left/right marginals over the training transition population",
            "cutoff": "deterministic occurrence-weighted one-dimensional two-means midpoint",
            "unseen_pair": "boundary",
            "motif": "run-length-compressed action sequence",
            "label_access": "none during association, cutoff, prediction, or motif construction",
            "information_budget": "other-fold unlabeled action-transition statistics",
        },
        "folds": fold_reports,
        "boundary_metrics": boundary,
        "partition_metrics": partition,
        "diagnostics": {
            "predicted_groups": len(set(candidate_groups.values())),
            "unique_motifs": len(set(motifs.values())),
            "minimum_group_length": min(group_lengths),
            "median_group_length": statistics.median(group_lengths),
            "maximum_group_length": max(group_lengths),
            "unseen_test_pairs": sum(int(row["unseen_test_pairs"]) for row in fold_reports),
        },
        "profiler": profiler,
        "validity": {
            "expected_full_source_counts": source_counts == EXPECTED,
            "selected_folds_nonempty": all(
                any(fold_for(sequence) == fold for sequence in selected_ids)
                for fold in selected_folds
            ),
            "candidate_predictions_complete_once": len(all_predictions)
            == expected_selected_pairs,
            "candidate_assignment_complete_once": len(candidate_groups)
            == len(candidate_rows),
            "candidate_inputs_exclude_scorer_fields": True,
            "all_scores_and_clusters_finite": True,
            "profiler_mass_conserved": profiler["total_weight"] == len(candidate_rows),
            "step18_baseline_complete": len(step18_groups) == len(candidate_rows),
        },
        "registered_verdict": verdict(boundary, partition)
        if args.mode == "full"
        else "preflight-only; no scientific verdict",
        "claim_boundary": {
            "supported_if_full_passes": "A cross-session label-free-at-prediction transition-association rule is a better post-hoc development candidate for session-local operation-group segmentation on this existing OSWorld-Human population.",
            "not_supported": "Fresh RQ3 confirmation, motif-name correctness, phase/action identity, cross-family generalization, or a whole-RQ answer.",
        },
        "outputs": {
            "candidate_operations": relative(operation_file),
            "candidate_profile": relative(profile_file),
            "pair_predictions": relative(out_dir / "pair-predictions.jsonl"),
            "session_results": relative(out_dir / "session-results.jsonl"),
        },
    }
    write_json(out_dir / "summary.json", summary)
    print(
        json.dumps(
            {
                "status": "ok",
                "mode": args.mode,
                "summary": relative(out_dir / "summary.json"),
                "selected_sessions": len(selected_ids),
                "selected_operations": len(candidate_rows),
                "selected_pairs": len(pair_rows),
                "boundary_f1": boundary["recurrence"]["f1_exact"],
                "partition_f1": partition["recurrence"]["f1"],
                "verdict": summary["registered_verdict"],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
