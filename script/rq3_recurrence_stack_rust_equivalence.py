#!/usr/bin/env python3
"""Verify exact Rust/Python recurrence-induction equivalence on existing folds."""

from __future__ import annotations

import argparse
import json
import math
import subprocess
from pathlib import Path
from typing import Any

from operation_boundary_backend_eval import (
    group_sequences,
    load_operations,
    parse_requirement,
    sort_sequences,
)
from rq3_recurrence_stack_induction_eval import (
    DEFAULT_BINARY,
    DEFAULT_OPERATION_FILE,
    EXPECTED,
    FOLD_COUNT,
    ROOT,
    candidate_assignments,
    fold_for,
    predict_fold,
    relative,
    visible_action_sequences,
    write_json,
    write_jsonl,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--operation-file", type=Path, default=DEFAULT_OPERATION_FILE)
    parser.add_argument("--binary", type=Path, default=DEFAULT_BINARY)
    return parser.parse_args()


def close(left: float, right: float) -> bool:
    return math.isclose(left, right, rel_tol=1e-12, abs_tol=1e-12)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def minimal_rows(
    groups: dict[str, list[dict[str, Any]]], sequence_ids: list[str]
) -> list[dict[str, Any]]:
    rows = []
    for sequence in sequence_ids:
        for operation in groups[sequence]:
            action = operation["fields"].get("action")
            require(bool(action), f"missing visible action: {sequence}")
            rows.append(
                {
                    "value": int(operation["value"]),
                    "fields": {"session": sequence, "action": str(action)},
                }
            )
    return rows


def run_rust_fold(
    binary: Path,
    fold_dir: Path,
    reference_rows: list[dict[str, Any]],
    target_rows: list[dict[str, Any]],
) -> tuple[dict[str, Any], dict[str, Any]]:
    reference_file = fold_dir / "reference-operations.jsonl"
    target_file = fold_dir / "target-operations.jsonl"
    profile_file = fold_dir / "profile.json"
    write_jsonl(reference_file, reference_rows)
    write_jsonl(target_file, target_rows)
    command = [
        str(binary.resolve()),
        "--operation-file",
        str(target_file.resolve()),
        "--view",
        "operations",
        "--format",
        "json",
        "--output",
        str(profile_file.resolve()),
        "--induce-operation-stack",
        "--induce-reference-operation-file",
        str(reference_file.resolve()),
        "--deterministic-output",
    ]
    completed = subprocess.run(
        command,
        cwd=ROOT,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    write_json(fold_dir / "command.json", command)
    (fold_dir / "stdout.json").write_text(completed.stdout, encoding="utf-8")
    (fold_dir / "stderr.txt").write_text(completed.stderr, encoding="utf-8")
    require(completed.returncode == 0, f"Rust fold failed: {fold_dir.name}")
    status = json.loads(completed.stdout)
    profile = json.loads(profile_file.read_text(encoding="utf-8"))
    return status, profile


def verify_fold(
    fold: int,
    groups: dict[str, list[dict[str, Any]]],
    sequence_ids: list[str],
    visible: dict[str, list[str]],
    binary: Path,
    out_dir: Path,
) -> dict[str, Any]:
    train_ids = [sequence for sequence in sequence_ids if fold_for(sequence) != fold]
    test_ids = [sequence for sequence in sequence_ids if fold_for(sequence) == fold]
    predictions, expected_fold = predict_fold(fold, sequence_ids, visible)
    _, expected_motifs, expected_sessions, _ = candidate_assignments(
        groups, test_ids, predictions
    )
    reference_rows = minimal_rows(groups, train_ids)
    target_rows = minimal_rows(groups, test_ids)
    fold_dir = out_dir / f"fold-{fold}"
    status, profile = run_rust_fold(
        binary, fold_dir, reference_rows, target_rows
    )
    report = profile["profile"]["operation_stack_induction"]

    require(
        report["policy"]
        == "cross-session-action-transition-npmi-operation-stack-induction",
        f"fold {fold} Rust policy mismatch",
    )
    require(report["reference_source"] == "external-operation-records", "wrong source")
    require(report["sequence_field"] == "session", "wrong sequence field")
    require(report["association_field"] == "action", "wrong association field")
    require(report["selected_source_fields"] == ["action"], "extra source field")
    require(report["reference_sessions"] == len(train_ids), "reference sessions mismatch")
    require(
        report["reference_operations"] == len(reference_rows),
        "reference operations mismatch",
    )
    require(
        report["reference_transitions"] == expected_fold["training_transitions"],
        "reference transitions mismatch",
    )
    require(report["target_sessions"] == len(test_ids), "target sessions mismatch")
    require(report["target_operations"] == len(target_rows), "target operations mismatch")
    for key in (
        "global_low_center",
        "global_high_center",
        "global_cutoff",
        "cross_action_low_center",
        "cross_action_high_center",
        "cross_action_cutoff",
    ):
        require(
            close(float(report[key]), float(expected_fold[key])),
            f"fold {fold} {key} mismatch: rust={report[key]} python={expected_fold[key]}",
        )
    require(
        close(
            float(report["cross_action_applied_cutoff"]),
            float(expected_fold["effective_cross_action_cutoff"]),
        ),
        f"fold {fold} effective cross-action cutoff mismatch",
    )
    for key in (
        "global_low_occurrences",
        "global_high_occurrences",
        "cross_action_low_occurrences",
        "cross_action_high_occurrences",
        "same_action_reference_transitions",
        "action_change_reference_transitions",
        "removed_current_boundaries",
        "added_current_boundaries",
    ):
        require(report[key] == expected_fold[key], f"fold {fold} {key} mismatch")
    for legacy, global_key in (
        ("low_center", "global_low_center"),
        ("high_center", "global_high_center"),
        ("cutoff", "global_cutoff"),
        ("low_occurrences", "global_low_occurrences"),
        ("high_occurrences", "global_high_occurrences"),
        ("two_means_iterations", "global_two_means_iterations"),
    ):
        require(report[legacy] == report[global_key], f"fold {fold} legacy alias {legacy}")

    raw_decisions = report["boundary_decisions"]
    require(
        len(raw_decisions) == len(predictions),
        f"fold {fold} raw decision count mismatch",
    )
    rust_decisions = {}
    for row in raw_decisions:
        key = (row["session"], int(row["position"]))
        require(key not in rust_decisions, f"fold {fold} duplicate Rust decision {key}")
        rust_decisions[key] = row
    require(len(rust_decisions) == len(predictions), f"fold {fold} decision count mismatch")
    for key, expected in predictions.items():
        require(key in rust_decisions, f"fold {fold} missing Rust decision {key}")
        actual = rust_decisions[key]
        require(actual["left_action"] == expected["left_action"], f"left action {key}")
        require(actual["right_action"] == expected["right_action"], f"right action {key}")
        require(
            bool(actual["unseen_in_reference"]) == bool(expected["unseen_in_training"]),
            f"unseen decision {key}",
        )
        require(
            actual["calibration_population"]
            == expected["calibration_population"],
            f"calibration population {key}",
        )
        require(
            close(float(actual["applied_cutoff"]), float(expected["applied_cutoff"])),
            f"applied cutoff {key}",
        )
        require(
            bool(actual["current_boundary"]) == bool(expected["current_boundary"]),
            f"current boundary {key}",
        )
        require(bool(actual["boundary"]) == bool(expected["boundary"]), f"boundary {key}")
        if expected["npmi"] is None:
            require(actual["npmi"] is None, f"unseen NPMI {key}")
        else:
            require(
                actual["npmi"] is not None
                and close(float(actual["npmi"]), float(expected["npmi"])),
                f"NPMI {key}",
            )

    expected_segments = {
        row["sequence"]: [
            {
                "session": row["sequence"],
                "start": group["start"],
                "end": group["end"],
                "motif": group["motif"],
            }
            for group in row["groups"]
        ]
        for row in expected_sessions
    }
    rust_segments: dict[str, list[dict[str, Any]]] = {sequence: [] for sequence in test_ids}
    for segment in report["segments"]:
        rust_segments.setdefault(segment["session"], []).append(segment)
    require(rust_segments == expected_segments, f"fold {fold} segment mismatch")

    rust_motifs: dict[int, str] = {}
    for sequence in test_ids:
        for segment in rust_segments[sequence]:
            for position in range(int(segment["start"]), int(segment["end"])):
                line = int(groups[sequence][position]["_line"])
                require(line not in rust_motifs, f"fold {fold} duplicate motif line {line}")
                rust_motifs[line] = segment["motif"]
    require(rust_motifs == expected_motifs, f"fold {fold} motif assignment mismatch")
    require(report["predicted_groups"] == len(report["segments"]), "group count mismatch")
    require(
        report["unique_motifs"] == len({row["motif"] for row in report["segments"]}),
        "unique motif count mismatch",
    )
    require(
        report["unseen_target_transitions"] == expected_fold["unseen_test_pairs"],
        "unseen count mismatch",
    )
    require(status["samples"] == len(target_rows), "status sample mismatch")
    require(
        profile["profile"]["summary"]["total_weight"] == len(target_rows),
        "profile mass mismatch",
    )
    return {
        "fold": fold,
        "train_sessions": len(train_ids),
        "test_sessions": len(test_ids),
        "reference_operations": len(reference_rows),
        "target_operations": len(target_rows),
        "boundaries_verified": len(predictions),
        "segments_verified": len(report["segments"]),
        "motif_assignments_verified": len(rust_motifs),
        "unique_motifs": sorted({row["motif"] for row in report["segments"]}),
        "global_cutoff": report["global_cutoff"],
        "cross_action_cutoff": report["cross_action_cutoff"],
        "cross_action_applied_cutoff": report["cross_action_applied_cutoff"],
        "removed_current_boundaries": report["removed_current_boundaries"],
        "added_current_boundaries": report["added_current_boundaries"],
        "unseen_transitions": report["unseen_target_transitions"],
        "profile_mass": profile["profile"]["summary"]["total_weight"],
        "profile": relative(fold_dir / "profile.json"),
    }


def main() -> None:
    args = parse_args()
    out_dir = args.out_dir if args.out_dir.is_absolute() else ROOT / args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    binary = args.binary if args.binary.is_absolute() else ROOT / args.binary
    require(binary.is_file(), f"missing Rust binary: {binary}")
    version = subprocess.run(
        [str(binary.resolve()), "--version"],
        cwd=ROOT,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    require(version.returncode == 0, "Rust version command failed")
    require(version.stdout.strip() == "agentpprof 0.2.37", "unexpected Rust version")

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
    require(source_counts == EXPECTED, f"source population mismatch: {source_counts}")
    visible = visible_action_sequences(groups, sequence_ids)
    fold_reports = [
        verify_fold(fold, groups, sequence_ids, visible, binary, out_dir)
        for fold in range(FOLD_COUNT)
    ]
    boundaries = sum(row["boundaries_verified"] for row in fold_reports)
    assignments = sum(row["motif_assignments_verified"] for row in fold_reports)
    segments = sum(row["segments_verified"] for row in fold_reports)
    mass = sum(row["profile_mass"] for row in fold_reports)
    motifs = sorted(
        {motif for report in fold_reports for motif in report["unique_motifs"]}
    )
    require(boundaries == EXPECTED["pairs"], "complete boundary equivalence mismatch")
    require(assignments == EXPECTED["operations"], "complete assignment equivalence mismatch")
    require(segments > 0, "no equivalent segments were produced")
    require(len(motifs) > 0, "no equivalent motifs were produced")
    require(mass == EXPECTED["operations"], "complete profile mass mismatch")
    summary = {
        "schema": "agentsight.rq3-recurrence-python-rust-equivalence.v1",
        "status": "pass",
        "role": "mechanical implementation equivalence on existing post-hoc development data",
        "paper_promotion": "none",
        "binary": relative(binary),
        "version": version.stdout.strip(),
        "operation_file": relative(args.operation_file),
        "source_counts": source_counts,
        "folds": fold_reports,
        "totals": {
            "boundaries_verified": boundaries,
            "motif_assignments_verified": assignments,
            "segments_verified": segments,
            "unique_motifs_verified": len(motifs),
            "profile_mass_verified": mass,
        },
        "validity": {
            "same_five_session_folds": True,
            "reference_target_session_disjoint": True,
            "reference_and_target_files_contain_only_session_action": True,
            "all_npmi_and_cutoffs_equal_within_1e_12": True,
            "all_boundary_decisions_exact": True,
            "candidate_boundary_subset_of_current": all(
                report["added_current_boundaries"] == 0 for report in fold_reports
            ),
            "all_segment_boundaries_and_motifs_exact": True,
            "all_operation_motif_assignments_exact": True,
            "all_profile_mass_conserved": True,
        },
        "claim_boundary": "Rust implements the approved Python recurrence candidate exactly on the existing five-fold OSWorld development population; this is not fresh RQ3 confirmation.",
    }
    write_json(out_dir / "summary.json", summary)
    print(json.dumps(summary["totals"] | {"status": "pass"}, indent=2))


if __name__ == "__main__":
    main()
