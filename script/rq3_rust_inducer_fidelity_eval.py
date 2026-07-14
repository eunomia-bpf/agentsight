#!/usr/bin/env python3
"""Evaluate the information-gain Rust inducer on OSWorld-Human.

The scorer reuses the Step 0006 population, binary metrics, B-cubed metric, and
simple controls. Human groups are retained only by this scorer and are removed
from every Rust input. The default comparison retains the old-heuristic path;
the depth-limit comparison runs the current binary at two declared depths.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import tempfile
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
from operation_rust_task_stack_induction_eval import (
    is_oracle_field,
    operation_stack_induction_report,
)
from rq3_osworld_boundary_fidelity_eval import bcubed, exact_f1


ROOT = Path(__file__).resolve().parents[1]
CONTROL_SUMMARY = (
    ROOT
    / ".agentsight"
    / "experiments"
    / "rq3-osworld-boundary-fidelity-v1"
    / "full"
    / "summary.json"
)
EXPECTED = {
    "operations": 3978,
    "sessions": 287,
    "pairs": 3691,
    "human_groups": 2042,
}
SIMPLE_CONTROLS = ("action_change", "phase_change", "always_boundary")
NEW_POLICY = "recursive-information-gain-operation-stack-induction"
OLD_POLICY = "query-conditioned-recursive-boundary-operation-stack-induction"
STEP17_SESSION_RESULTS = (
    ROOT
    / ".agentsight"
    / "experiments"
    / "rq3-rust-inducer-fidelity-v1"
    / "full"
    / "session-results.jsonl"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("preflight", "full"), required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--operation-file", type=Path, default=DEFAULT_OPERATION_FILE)
    parser.add_argument("--baseline-binary", type=Path, required=True)
    parser.add_argument("--candidate-binary", type=Path, required=True)
    parser.add_argument(
        "--comparison",
        choices=("old-heuristic", "depth-limit"),
        default="old-heuristic",
    )
    parser.add_argument("--candidate-max-depth", type=int, default=4)
    parser.add_argument("--baseline-max-depth", type=int, default=4)
    parser.add_argument("--preflight-sequence")
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


def scrub_session(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output = []
    for operation in rows:
        fields = {
            key: value
            for key, value in operation["fields"].items()
            if key not in LEAKAGE_FIELDS
            and not any(key.startswith(prefix) for prefix in LEAKAGE_PREFIXES)
        }
        output.append({"fields": fields, "value": int(operation["value"])})
    return output


def push_path(path: list[str], label: str, deduplicate: bool) -> list[str]:
    child = list(path)
    if not deduplicate or label not in child:
        child.append(label)
    return child


def reconstruct_paths(
    operations: list[dict[str, Any]],
    decisions: list[dict[str, Any]],
    *,
    deduplicate: bool,
) -> list[list[str]]:
    paths: list[list[str] | None] = [None] * len(operations)
    cursor = 0

    def visit(indices: list[int], path: list[str]) -> None:
        nonlocal cursor
        node_weight = sum(int(operations[index]["value"]) for index in indices)
        if (
            cursor < len(decisions)
            and decisions[cursor]["path"] == path
            and int(decisions[cursor]["node_weight"]) == node_weight
        ):
            decision = decisions[cursor]
            cursor += 1
            score = decision["selected_score"]
            cut_after = int(score["cut_after"])
            left = indices[:cut_after]
            right = indices[cut_after:]
            if not left or not right:
                raise SystemExit(f"empty child while replaying {decision}")
            left_path = push_path(path, str(score["left_label"]), deduplicate)
            right_path = push_path(path, str(score["right_label"]), deduplicate)
            if left_path == right_path:
                raise SystemExit(f"split has identical child paths: {decision}")
            if not deduplicate and (
                len(left_path) != len(path) + 1 or len(right_path) != len(path) + 1
            ):
                raise SystemExit(f"candidate split did not append one frame: {decision}")
            visit(left, left_path)
            visit(right, right_path)
            return
        final_path = path or ["all"]
        for index in indices:
            if paths[index] is not None:
                raise SystemExit(f"operation {index} received two terminal paths")
            paths[index] = list(final_path)

    visit(list(range(len(operations))), [])
    if cursor != len(decisions):
        raise SystemExit(f"unconsumed split decisions: {len(decisions) - cursor}")
    if any(path is None for path in paths):
        raise SystemExit("incomplete terminal path assignment")
    return [list(path or ["all"]) for path in paths]


def folded_stack(path: list[str]) -> str:
    return ";".join(safe_frame(label, "operation") for label in path)


def run_binary(
    binary: Path,
    operations: list[dict[str, Any]],
    *,
    deduplicate: bool,
    max_depth: int,
) -> dict[str, Any]:
    if not binary.is_file():
        raise SystemExit(f"missing profiler binary: {relative(binary)}")
    with tempfile.TemporaryDirectory(prefix="rq3-rust-inducer-") as directory:
        temp = Path(directory)
        operation_file = temp / "operations.jsonl"
        profile_file = temp / "profile.json"
        write_jsonl(operation_file, operations)
        command = [
            str(binary.resolve()),
            "--operation-file",
            str(operation_file),
            "--view",
            "operations",
            "--format",
            "json",
            "--output",
            str(profile_file),
            "--induce-operation-stack",
            "--induce-max-depth",
            str(max_depth),
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
        if completed.returncode:
            raise SystemExit(
                f"agentpprof failed ({completed.returncode}): {completed.stderr.strip()}"
            )
        status = json.loads(completed.stdout)
        profile = json.loads(profile_file.read_text(encoding="utf-8"))

    if status.get("status") != "ok" or int(status.get("samples", -1)) != len(operations):
        raise SystemExit(f"invalid profiler status: {status}")
    induction = operation_stack_induction_report(profile["profile"])
    if int(induction["max_depth"]) != max_depth:
        raise SystemExit(
            f"unexpected maximum depth: expected={max_depth} "
            f"actual={induction['max_depth']}"
        )
    selected = induction.get("selected_evidence_fields") or induction["selected_source_fields"]
    leaked = sorted(field for field in selected if is_oracle_field(field))
    if leaked:
        raise SystemExit(f"oracle fields entered induction: {leaked}")
    decisions = induction["split_decisions"]
    paths = reconstruct_paths(operations, decisions, deduplicate=deduplicate)
    reconstructed: Counter[str] = Counter()
    for operation, path in zip(operations, paths):
        reconstructed[folded_stack(path)] += int(operation["value"])
    rust_stacks = Counter(
        {stack: int(weight) for stack, weight in profile["profile"]["stacks"].items()}
    )
    if reconstructed != rust_stacks:
        raise SystemExit("reconstructed stack weights differ from Rust profile")
    total_weight = sum(int(operation["value"]) for operation in operations)
    if sum(reconstructed.values()) != total_weight:
        raise SystemExit("reconstructed stack mass differs from input")
    return {
        "status": status,
        "policy": induction["policy"],
        "max_depth": int(induction["max_depth"]),
        "selected_fields": selected,
        "split_decisions": decisions,
        "stop_reasons": induction["stop_reasons"],
        "paths": paths,
        "stack_weights": dict(sorted(reconstructed.items())),
        "total_weight": total_weight,
    }


def boundaries(paths: list[list[str]]) -> list[bool]:
    return [left != right for left, right in zip(paths, paths[1:])]


def assignments_for(
    sequence: str, rows: list[dict[str, Any]], predicted: list[bool]
) -> dict[int, str]:
    if len(predicted) != len(rows) - 1:
        raise SystemExit("boundary prediction count mismatch")
    group = 0
    assignments = {}
    for index, operation in enumerate(rows):
        if index and predicted[index - 1]:
            group += 1
        assignments[int(operation["_line"])] = f"{sequence}:group-{group:04d}"
    return assignments


def source_counts(
    groups: dict[str, list[dict[str, Any]]], sequence_ids: list[str]
) -> dict[str, int]:
    return {
        "operations": sum(len(groups[sequence]) for sequence in sequence_ids),
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


def aggregate_boundary(rows: list[dict[str, Any]], method: str) -> dict[str, Any]:
    metrics = binary_metrics(
        [bool(row[method]) for row in rows], [bool(row["label"]) for row in rows]
    )
    return {**metrics, "f1_exact": exact_f1(metrics)}


def load_step17_reference() -> dict[str, dict[str, Any]]:
    if not STEP17_SESSION_RESULTS.is_file():
        raise SystemExit(f"missing Step 0017 session reference: {relative(STEP17_SESSION_RESULTS)}")
    references: dict[str, dict[str, Any]] = {}
    with STEP17_SESSION_RESULTS.open(encoding="utf-8") as file:
        for line in file:
            row = json.loads(line)
            if row.get("method") == "candidate":
                references[str(row["sequence"])] = row
    if len(references) != EXPECTED["sessions"]:
        raise SystemExit(
            "Step 0017 candidate reference does not cover the complete population"
        )
    return references


def assert_step17_baseline(row: dict[str, Any], reference: dict[str, Any]) -> None:
    keys = (
        "operations",
        "pairs",
        "policy",
        "splits",
        "max_leaf_depth",
        "selected_fields",
        "stop_reasons",
        "paths",
        "stack_weights",
        "mass",
    )
    changed = [key for key in keys if row.get(key) != reference.get(key)]
    if changed:
        raise SystemExit(
            f"depth-four baseline differs from Step 0017 for {row['sequence']}: {changed}"
        )


def main() -> None:
    args = parse_args()
    if args.candidate_max_depth < 1 or args.baseline_max_depth < 1:
        raise SystemExit("maximum depths must be positive")
    if args.preflight_sequence and args.mode != "preflight":
        raise SystemExit("--preflight-sequence is valid only in preflight mode")

    if args.comparison == "depth-limit":
        if args.candidate_max_depth != 255 or args.baseline_max_depth != 4:
            raise SystemExit(
                "the registered depth-limit comparison requires candidate depth 255 "
                "and baseline depth 4"
            )
        if args.candidate_binary.resolve() != args.baseline_binary.resolve():
            raise SystemExit("depth-limit comparison must use the same binary")
        candidate_method = "depth_unbounded"
        baseline_method = "depth_four"
        method_configs = {
            candidate_method: {
                "binary": args.candidate_binary,
                "policy": NEW_POLICY,
                "max_depth": args.candidate_max_depth,
                "deduplicate": False,
            },
            baseline_method: {
                "binary": args.baseline_binary,
                "policy": NEW_POLICY,
                "max_depth": args.baseline_max_depth,
                "deduplicate": False,
            },
        }
        step17_references = load_step17_reference()
    else:
        candidate_method = "candidate"
        baseline_method = "old_heuristic"
        method_configs = {
            candidate_method: {
                "binary": args.candidate_binary,
                "policy": NEW_POLICY,
                "max_depth": args.candidate_max_depth,
                "deduplicate": False,
            },
            baseline_method: {
                "binary": args.baseline_binary,
                "policy": OLD_POLICY,
                "max_depth": args.baseline_max_depth,
                "deduplicate": True,
            },
        }
        step17_references = {}
    methods = tuple(method_configs)

    out_dir = args.out_dir.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    operations = load_operations(args.operation_file)
    groups = group_sequences(
        operations, "session", "human_group", parse_requirement("group_alignment=exact")
    )
    sort_sequences(groups, "turn")
    all_sequence_ids = sorted(groups)
    counts = source_counts(groups, all_sequence_ids)
    if counts != EXPECTED:
        raise SystemExit(f"eligible source counts changed: expected={EXPECTED} actual={counts}")
    if args.mode == "preflight":
        sequence = args.preflight_sequence or all_sequence_ids[0]
        if sequence not in groups:
            raise SystemExit(f"unknown preflight sequence: {sequence}")
        sequence_ids = [sequence]
    else:
        sequence_ids = all_sequence_ids

    pair_rows: list[dict[str, Any]] = []
    session_rows: list[dict[str, Any]] = []
    predicted_by_method: dict[str, dict[int, str]] = {method: {} for method in methods}
    no_split = Counter()
    depth_cap = Counter()

    for sequence in sequence_ids:
        oracle_rows = groups[sequence]
        profiler_rows = scrub_session(oracle_rows)
        method_boundaries: dict[str, list[bool]] = {}
        for method in methods:
            config = method_configs[method]
            result = run_binary(
                config["binary"],
                profiler_rows,
                deduplicate=bool(config["deduplicate"]),
                max_depth=int(config["max_depth"]),
            )
            if result["policy"] != config["policy"]:
                raise SystemExit(f"unexpected {method} policy: {result['policy']}")
            if result["policy"] == NEW_POLICY:
                unexpected_stops = set(result["stop_reasons"]) - {
                    "max_depth",
                    "no_material_split",
                }
                if unexpected_stops:
                    raise SystemExit(
                        f"candidate retained unapproved stop gates: {sorted(unexpected_stops)}"
                    )
                for decision in result["split_decisions"]:
                    score = decision["selected_score"]
                    if not (
                        float(score["normalized_information_gain"]) > 0.0
                        and float(score["score"]) > float(score["complexity_penalty"])
                        and float(score["accepted_margin"]) > 0.0
                        and score["left_label"] != score["right_label"]
                        and safe_frame(score["left_label"], "operation")
                        != safe_frame(score["right_label"], "operation")
                    ):
                        raise SystemExit(f"invalid accepted candidate split: {decision}")
            if method == "depth_unbounded" and result["stop_reasons"].get(
                "max_depth", 0
            ):
                raise SystemExit("registered depth 255 remained binding")
            predicted = boundaries(result["paths"])
            method_boundaries[method] = predicted
            predicted_by_method[method].update(
                assignments_for(sequence, oracle_rows, predicted)
            )
            if not result["split_decisions"]:
                no_split[method] += 1
            if int(result["stop_reasons"].get("max_depth", 0)) > 0:
                depth_cap[method] += 1
            max_depth = max(len(path) for path in result["paths"])
            session_row = {
                "sequence": sequence,
                "method": method,
                "operations": len(oracle_rows),
                "pairs": len(predicted),
                "policy": result["policy"],
                "configured_max_depth": result["max_depth"],
                "splits": len(result["split_decisions"]),
                "max_leaf_depth": max_depth,
                "selected_fields": result["selected_fields"],
                "stop_reasons": result["stop_reasons"],
                "paths": result["paths"],
                "stack_weights": result["stack_weights"],
                "mass": result["total_weight"],
            }
            if method == "depth_four":
                assert_step17_baseline(session_row, step17_references[sequence])
            session_rows.append(session_row)
        for index, (previous, current) in enumerate(zip(oracle_rows, oracle_rows[1:])):
            pair_rows.append(
                {
                    "sequence": sequence,
                    "previous_line": int(previous["_line"]),
                    "current_line": int(current["_line"]),
                    "label": previous["fields"]["human_group"]
                    != current["fields"]["human_group"],
                    **{method: method_boundaries[method][index] for method in methods},
                }
            )

    expected_operations = sum(len(groups[sequence]) for sequence in sequence_ids)
    expected_pairs = sum(len(groups[sequence]) - 1 for sequence in sequence_ids)
    if len(pair_rows) != expected_pairs:
        raise SystemExit("pair coverage is incomplete")
    for method in methods:
        if len(predicted_by_method[method]) != expected_operations:
            raise SystemExit(f"{method} terminal assignment coverage is incomplete")
    step17_baseline_verified = args.comparison != "depth-limit" or bool(sequence_ids)

    boundary_metrics = {
        method: aggregate_boundary(pair_rows, method) for method in methods
    }
    partition_metrics = {
        method: bcubed(groups, sequence_ids, predicted_by_method[method])
        for method in methods
    }

    controls = json.loads(CONTROL_SUMMARY.read_text(encoding="utf-8"))
    if controls["source_counts"] != EXPECTED:
        raise SystemExit("reused Step 0006 controls have different source counts")
    if args.mode == "full":
        for method in SIMPLE_CONTROLS:
            boundary_metrics[method] = controls["boundary_metrics"][method]
            partition_metrics[method] = controls["partition_metrics"][method]
        boundary_metrics["supervised_upper"] = controls["boundary_metrics"]["learned"]
        partition_metrics["supervised_upper"] = controls["partition_metrics"]["learned"]

    verdict: dict[str, Any] = {"verdict": "preflight_only"}
    if args.mode == "full":
        strongest_boundary = max(
            SIMPLE_CONTROLS,
            key=lambda method: float(boundary_metrics[method]["f1_exact"]),
        )
        strongest_partition = max(
            SIMPLE_CONTROLS,
            key=lambda method: float(partition_metrics[method]["f1"]),
        )
        beats_baseline_boundary = float(
            boundary_metrics[candidate_method]["f1_exact"]
        ) > float(
            boundary_metrics[baseline_method]["f1_exact"]
        )
        beats_baseline_partition = float(
            partition_metrics[candidate_method]["f1"]
        ) > float(
            partition_metrics[baseline_method]["f1"]
        )
        clears_boundary_control = float(
            boundary_metrics[candidate_method]["f1_exact"]
        ) > float(boundary_metrics[strongest_boundary]["f1_exact"])
        clears_partition_control = float(
            partition_metrics[candidate_method]["f1"]
        ) > float(partition_metrics[strongest_partition]["f1"])
        wins_boundary = beats_baseline_boundary and clears_boundary_control
        wins_partition = beats_baseline_partition and clears_partition_control
        if wins_boundary and wins_partition:
            verdict_name = "supported"
        elif (
            not clears_boundary_control
            and not clears_partition_control
        ) or (not beats_baseline_boundary and not beats_baseline_partition):
            verdict_name = "contradicted"
        else:
            verdict_name = "mixed"
        verdict = {
            "verdict": verdict_name,
            "candidate_method": candidate_method,
            "baseline_method": baseline_method,
            "candidate_wins_boundary": wins_boundary,
            "candidate_wins_partition": wins_partition,
            "candidate_beats_baseline_boundary": beats_baseline_boundary,
            "candidate_beats_baseline_partition": beats_baseline_partition,
            "candidate_clears_boundary_control": clears_boundary_control,
            "candidate_clears_partition_control": clears_partition_control,
            "strongest_boundary_control": strongest_boundary,
            "strongest_partition_control": strongest_partition,
        }

    write_jsonl(out_dir / "session-results.jsonl", session_rows)
    write_jsonl(out_dir / "pair-predictions.jsonl", pair_rows)
    summary = {
        "status": "ok",
        "mode": args.mode,
        "comparison": args.comparison,
        "operation_file": relative(args.operation_file),
        "binaries": {
            method: relative(config["binary"])
            for method, config in method_configs.items()
        },
        "methods": {
            method: {
                "binary": relative(config["binary"]),
                "policy": config["policy"],
                "max_depth": config["max_depth"],
            }
            for method, config in method_configs.items()
        },
        "complete_source_counts": counts,
        "evaluated": {
            "sessions": len(sequence_ids),
            "operations": expected_operations,
            "pairs": expected_pairs,
        },
        "boundary_metrics": boundary_metrics,
        "partition_metrics": partition_metrics,
        "diagnostics": {
            "no_split_sessions": dict(no_split),
            "depth_cap_sessions": dict(depth_cap),
            "session_length_histogram": dict(
                sorted(Counter(len(groups[sequence]) for sequence in sequence_ids).items())
            ),
        },
        "tested_hypothesis": verdict,
        "validity": {
            "complete_population_in_full_mode": args.mode != "full"
            or len(sequence_ids) == EXPECTED["sessions"],
            "terminal_assignment_once_per_operation": True,
            "all_decisions_consumed": True,
            "rust_stack_weights_reconstructed": True,
            "mass_conserved_per_session": True,
            "oracle_fields_excluded": True,
            "reported_depths_match_plan": True,
            "same_binary_for_depth_comparison": args.comparison != "depth-limit"
            or args.candidate_binary.resolve() == args.baseline_binary.resolve(),
            "depth_unbounded_nonbinding": args.comparison != "depth-limit"
            or depth_cap[candidate_method] == 0,
            "depth_four_reproduces_step17": step17_baseline_verified,
            "candidate_acceptance_invariant": True,
        },
    }
    write_json(out_dir / "summary.json", summary)
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
