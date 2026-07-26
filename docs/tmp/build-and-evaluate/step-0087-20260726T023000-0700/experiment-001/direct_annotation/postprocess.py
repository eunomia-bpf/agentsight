#!/usr/bin/env python3
"""Apply the unchanged A2 replay/canonicalization/scoring path and audit it."""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path
import random
import subprocess
import sys
import time
from typing import Any, Iterable


SCRIPT_DIR = Path(__file__).resolve().parent
EXPERIMENT = SCRIPT_DIR.parent
REPO = EXPERIMENT.parents[4]
sys.path.insert(0, str(REPO / "script"))
sys.path.insert(0, str(SCRIPT_DIR))

import rq3_source_native_task_progress_boundary_eval as source_score  # noqa: E402
import annotate as direct_backend  # noqa: E402


PYTHON = Path("/usr/bin/python3")
PACKETS = (
    REPO
    / ".agentsight"
    / "experiments"
    / "rq4-end-to-end-cost-v1"
    / "full"
    / "source-packets-rep-1"
)
TARGET_OPERATIONS = (
    REPO / "docs" / "visexp" / "out" / "codetracebench-rq2" / "full"
    / "target-operations.jsonl"
)
OPERATION_USAGE = (
    REPO / ".agentsight" / "experiments"
    / "rq1-codetracebench-token-attribution-v1" / "full"
    / "operation-usage.jsonl"
)
FIXED_CANONICAL_NAMES = (
    REPO / "docs" / "tmp" / "build-and-evaluate"
    / "step-0067-20260722T135005-0700" / "experiment-001"
    / "canonical-names.json"
)
VERIFIED_MANIFEST = (
    REPO / ".agentsight" / "experiments" / "codetracebench-rq2"
    / "manifests" / "verified.parquet"
)
MULTIRES_ASSIGNMENTS = (
    REPO / ".agentsight" / "experiments"
    / "rq3-multiresolution-recurrence-v1" / "full" / "codetrace"
    / "operation-assignments.jsonl"
)
A2_OPERATION_SCORES = (
    REPO / ".agentsight" / "experiments" / "a2-canonical-v1"
    / "score" / "operation-score-rows.jsonl"
)
A2_PAIR_SCORES = (
    REPO / ".agentsight" / "experiments" / "a2-canonical-v1"
    / "score" / "pair-score-rows.jsonl"
)
A2_SUMMARY = (
    REPO / ".agentsight" / "experiments" / "a2-canonical-v1"
    / "score" / "summary.json"
)
AGENTPPROF = REPO / "agentpprof" / "target" / "release" / "agentpprof"
PIPELINE_RECORDS = EXPERIMENT / "pipeline-records.jsonl"
RAW_RESULTS = EXPERIMENT / "raw-results.json"
RUN_RECORDS = EXPERIMENT / "annotation-run-records.jsonl"
PILOT = EXPERIMENT / "pilot"

EXPECTED_SESSIONS = 405
EXPECTED_TURNS = 17_148
EXPECTED_OPERATIONS = 20_866
EXPECTED_TOKENS = 494_862_929
EXPECTED_STAGES = 2_948
EXPECTED_TASKS = 251
PILOT_SESSIONS = 40
BOOTSTRAP_RESAMPLES = 10_000
BOOTSTRAP_SEED = 20_260_722


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    result = []
    with path.open(encoding="utf-8") as stream:
        for line in stream:
            if line.strip():
                result.append(json.loads(line))
    return result


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as stream:
        for row in rows:
            stream.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def relative(path: Path) -> str:
    return str(path.resolve().relative_to(REPO))


def run_command(name: str, command: list[str], cwd: Path = REPO) -> dict[str, Any]:
    started_unix = time.time()
    started = time.monotonic()
    result = subprocess.run(
        command,
        cwd=cwd,
        text=True,
        encoding="utf-8",
        capture_output=True,
        check=False,
    )
    record = {
        "name": name,
        "command": command,
        "cwd": relative(cwd),
        "started_unix": started_unix,
        "wall_seconds": round(time.monotonic() - started, 6),
        "returncode": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
    }
    with PIPELINE_RECORDS.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(record, sort_keys=True) + "\n")
    if result.returncode != 0:
        raise RuntimeError(
            f"{name} failed with {result.returncode}: {result.stderr[-2000:]}"
        )
    return record


def filter_canonical_names(sessions: set[str], output: Path) -> Path:
    fixed = read_json(FIXED_CANONICAL_NAMES)
    task_names = {
        str(row["task_name"])
        for row in read_jsonl(OPERATION_USAGE)
        if str(row["session"]) in sessions
    }
    if not task_names:
        raise RuntimeError("selected task names are empty")
    write_json(
        output,
        {
            "task_roots": {
                key: value
                for key, value in fixed["task_roots"].items()
                if key in task_names
            },
            "semantic_labels": fixed["semantic_labels"],
        },
    )
    return output


def annotation_cost(selected_ordinals: set[int], configured_workers: int) -> dict[str, Any]:
    records = read_jsonl(RUN_RECORDS)
    latest: dict[int, dict[str, Any]] = {}
    for row in records:
        ordinal = int(row["ordinal"])
        if ordinal in selected_ordinals:
            latest[int(row["ordinal"])] = row
    if set(latest) != selected_ordinals:
        missing = sorted(selected_ordinals - set(latest))
        raise RuntimeError(
            f"expected {len(selected_ordinals)} successful annotation records; "
            f"missing {missing[:5]}"
        )
    usage = Counter()
    summed_wall = 0.0
    retries = 0
    call_count = 0
    starts_and_durations: list[tuple[int, float, float]] = []
    retry_reason_counts: Counter[str] = Counter()
    attempt_limit_valid = True
    successful = 0
    failed_after_retry = 0
    for ordinal, row in latest.items():
        successful += int(row.get("status") == "ok")
        failed_after_retry += int(row.get("status") != "ok")
        retries += int(bool(row["format_retry"]))
        attempt_limit_valid = attempt_limit_valid and 1 <= int(row["attempts"]) <= 2
        for attempt in row["attempt_records"]:
            call_count += 1
            wall = float(attempt["wall_seconds"])
            summed_wall += wall
            starts_and_durations.append(
                (ordinal, float(attempt["started_unix"]), wall)
            )
            for error in attempt.get("errors") or []:
                retry_reason_counts[str(error)] += 1
            for key, value in (attempt.get("usage") or {}).items():
                if isinstance(value, int):
                    usage[key] += value
    intervals = sorted(
        (start, start + duration) for _ordinal, start, duration in starts_and_durations
    )
    active_union_seconds = 0.0
    if intervals:
        current_start, current_end = intervals[0]
        for start, end in intervals[1:]:
            if start <= current_end:
                current_end = max(current_end, end)
            else:
                active_union_seconds += current_end - current_start
                current_start, current_end = start, end
        active_union_seconds += current_end - current_start
    return {
        "backend": "codex-cli 0.145.0",
        "model": "gpt-5.6-sol",
        "worker_pattern": (
            f"isolated one-trajectory calls, up to {configured_workers} parallel workers; "
            "valid interrupted outputs reused"
        ),
        "successful_trajectories": successful,
        "trajectory_calls": len(selected_ordinals),
        "format_retries": retries,
        "failed_after_retry": failed_after_retry,
        "attempt_limit_valid": attempt_limit_valid,
        "retry_reason_counts": dict(sorted(retry_reason_counts.items())),
        "total_codex_calls": call_count,
        "summed_backend_wall_seconds": summed_wall,
        "active_backend_wall_seconds": active_union_seconds,
        "interrupted_elapsed_span_seconds": (
            max(end for _start, end in intervals)
            - min(start for start, _end in intervals)
            if intervals
            else 0.0
        ),
        "usage": dict(usage),
    }


def boundary_metric(rows: list[dict[str, Any]], method: str) -> dict[str, Any]:
    tp = sum(bool(row["official_boundary"]) and bool(row[method]) for row in rows)
    fp = sum(not bool(row["official_boundary"]) and bool(row[method]) for row in rows)
    fn = sum(bool(row["official_boundary"]) and not bool(row[method]) for row in rows)
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = (
        2 * precision * recall / (precision + recall)
        if precision + recall
        else 0.0
    )
    return {
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "precision": precision,
        "recall": recall,
        "f1": f1,
    }


def boundary_task_bootstrap(
    rows: list[dict[str, Any]], candidate: str, baseline: str, output: Path
) -> dict[str, Any]:
    by_task: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_task[str(row["task_name"])].append(row)
    tasks = sorted(by_task)
    sufficient = {
        (task, method): boundary_metric(task_rows, method)
        for task, task_rows in by_task.items()
        for method in (candidate, baseline)
    }

    def f1(draw: list[str], method: str) -> float:
        totals = Counter()
        for task in draw:
            metric = sufficient[(task, method)]
            totals["tp"] += metric["tp"]
            totals["fp"] += metric["fp"]
            totals["fn"] += metric["fn"]
        precision = (
            totals["tp"] / (totals["tp"] + totals["fp"])
            if totals["tp"] + totals["fp"]
            else 0.0
        )
        recall = (
            totals["tp"] / (totals["tp"] + totals["fn"])
            if totals["tp"] + totals["fn"]
            else 0.0
        )
        return (
            2 * precision * recall / (precision + recall)
            if precision + recall
            else 0.0
        )

    generator = random.Random(BOOTSTRAP_SEED)
    draws = []
    for index in range(BOOTSTRAP_RESAMPLES):
        sample = generator.choices(tasks, k=len(tasks))
        draws.append(
            {
                "resample": index,
                "delta": f1(sample, candidate) - f1(sample, baseline),
            }
        )
    write_jsonl(output, draws)
    deltas = [row["delta"] for row in draws]
    return {
        "candidate": candidate,
        "baseline": baseline,
        "resamples": BOOTSTRAP_RESAMPLES,
        "task_clusters": len(tasks),
        "mean_delta": sum(deltas) / len(deltas),
        "ci95": [
            source_score.base.percentile(deltas, 0.025),
            source_score.base.percentile(deltas, 0.975),
        ],
        "positive_fraction": sum(delta > 0 for delta in deltas) / len(deltas),
    }


def paired_a2(score_dir: Path) -> dict[str, Any]:
    direct_operations = read_jsonl(score_dir / "operation-score-rows.jsonl")
    a2_operations = read_jsonl(A2_OPERATION_SCORES)
    direct_by_key = {
        (str(row["session"]), int(row["step_id"])): row for row in direct_operations
    }
    a2_by_key = {
        (str(row["session"]), int(row["step_id"])): row for row in a2_operations
    }
    if not set(direct_by_key) <= set(a2_by_key):
        raise RuntimeError("direct operation score population is not covered by A2")
    paired_operations = []
    for key in sorted(direct_by_key):
        direct = direct_by_key[key]
        a2 = a2_by_key[key]
        if (
            direct["official_stage"] != a2["official_stage"]
            or direct["task_name"] != a2["task_name"]
        ):
            raise RuntimeError(f"direct/A2 operation oracle mismatch: {key}")
        paired_operations.append(
            {
                "session": key[0],
                "step_id": key[1],
                "task_name": direct["task_name"],
                "official_stage": direct["official_stage"],
                "direct": direct["candidate"],
                "a2": a2["candidate"],
            }
        )

    b3 = source_score.bcubed_task_bootstrap(
        paired_operations,
        "direct",
        "a2",
        score_dir / "bootstrap-direct-minus-a2-bcubed.jsonl",
    )

    direct_pairs = read_jsonl(score_dir / "pair-score-rows.jsonl")
    a2_pairs = read_jsonl(A2_PAIR_SCORES)
    direct_pair_by_key = {
        (str(row["session"]), int(row["position"])): row for row in direct_pairs
    }
    a2_pair_by_key = {
        (str(row["session"]), int(row["position"])): row for row in a2_pairs
    }
    if not set(direct_pair_by_key) <= set(a2_pair_by_key):
        raise RuntimeError("direct boundary score population is not covered by A2")
    paired_pairs = []
    for key in sorted(direct_pair_by_key):
        direct = direct_pair_by_key[key]
        a2 = a2_pair_by_key[key]
        if (
            bool(direct["official_boundary"]) != bool(a2["official_boundary"])
            or direct["task_name"] != a2["task_name"]
        ):
            raise RuntimeError(f"direct/A2 boundary oracle mismatch: {key}")
        paired_pairs.append(
            {
                "session": key[0],
                "position": key[1],
                "task_name": direct["task_name"],
                "official_boundary": bool(direct["official_boundary"]),
                "direct": bool(direct["candidate"]),
                "a2": bool(a2["candidate"]),
            }
        )
    boundary = boundary_task_bootstrap(
        paired_pairs,
        "direct",
        "a2",
        score_dir / "bootstrap-direct-minus-a2-boundary.jsonl",
    )
    a2_metrics = {
        "bcubed": source_score.base.bcubed(paired_operations, "a2"),
        "boundary": boundary_metric(paired_pairs, "a2"),
    }
    return {
        "population_equal": True,
        "operation_rows": len(paired_operations),
        "pair_rows": len(paired_pairs),
        "a2_metrics": a2_metrics,
        "bcubed_f1": b3,
        "boundary_f1": boundary,
    }


def run_pipeline(mode: str) -> None:
    preflight = mode == "preflight"
    pilot = mode == "pilot"
    phase_prefix = "preflight-" if preflight else "pilot-" if pilot else ""
    root = (
        EXPERIMENT / "preflight" / "pipeline"
        if preflight
        else PILOT / "pipeline"
        if pilot
        else EXPERIMENT
    )
    assembled = root / "assembled"
    canonical = root / "canonical"
    score = root / "score"
    profiles = root / "profiles"
    profiles.mkdir(parents=True, exist_ok=True)
    packet_dir = (
        EXPERIMENT / "preflight" / "packets"
        if preflight
        else PILOT / "packets"
        if pilot
        else PACKETS
    )
    annotation_dir = (
        EXPERIMENT / "preflight" / "annotations"
        if preflight
        else PILOT / "annotations"
        if pilot
        else EXPERIMENT / "raw-annotations"
    )
    canonical_names = FIXED_CANONICAL_NAMES
    if preflight or pilot:
        selected_sessions = {
            str(packet["session"])
            for packet in read_json(packet_dir / "batch-01.json")["sessions"]
        }
        canonical_names = filter_canonical_names(
            selected_sessions,
            (
                EXPERIMENT / "preflight" / "canonical-names.json"
                if preflight
                else PILOT / "canonical-names.json"
            ),
        )

    run_command(
        f"{phase_prefix}assemble-root-repair",
        [
            str(PYTHON),
            str(REPO / "script" / "assemble_agent_operation_profile.py"),
            "--target-operations",
            str(TARGET_OPERATIONS),
            "--operation-usage",
            str(OPERATION_USAGE),
            "--packet-dir",
            str(packet_dir),
            "--annotation-dir",
            str(annotation_dir),
            "--contract-root-only-prefix",
            "--canonical-names",
            str(canonical_names),
            "--mode",
            "full" if mode == "full" else "preflight",
            "--out",
            str(assembled),
        ],
    )
    inference = read_json(assembled / "inference-summary.json")
    inference.update(
        {
            "algorithm_version": "direct-multilevel-codex-gpt-5.6-sol-v1",
            "annotation_backend": "one isolated direct Codex call per trajectory",
            "configured_depth_or_leaf_cap": False,
            "official_manifest_opened": False,
            "official_stages_opened": False,
        }
    )
    write_json(assembled / "inference-summary.json", inference)

    run_command(
        f"{phase_prefix}fixed-canonicalization",
        [
            str(PYTHON),
            str(REPO / "script" / "canonicalize_operation_marks.py"),
            "--operation-marks",
            str(assembled / "operation-marks.json"),
            "--operations",
            str(assembled / "operations-count.jsonl"),
            "--reference-predictions",
            str(assembled / "predictions.jsonl"),
            "--out-dir",
            str(canonical),
        ],
    )
    operation_profile = run_command(
        f"{phase_prefix}operation-profile",
        [
            str(AGENTPPROF),
            "--operation-file",
            str(assembled / "operations-count.jsonl"),
            "--operation-mark-file",
            str(canonical / "operation-marks.json"),
            "--view",
            "operations",
            "--deterministic-output",
            "--output",
            str(profiles / "direct-operation.pb.gz"),
        ],
    )
    token_profile = run_command(
        f"{phase_prefix}token-profile",
        [
            str(AGENTPPROF),
            "--operation-file",
            str(assembled / "operations-tokens.jsonl"),
            "--operation-mark-file",
            str(canonical / "operation-marks.json"),
            "--view",
            "tokens",
            "--deterministic-output",
            "--output",
            str(profiles / "direct-tokens.pb.gz"),
        ],
    )
    run_command(
        f"{phase_prefix}pprof-operation-readback",
        ["go", "tool", "pprof", "-top", str(profiles / "direct-operation.pb.gz")],
    )
    run_command(
        f"{phase_prefix}pprof-token-readback",
        ["go", "tool", "pprof", "-top", str(profiles / "direct-tokens.pb.gz")],
    )
    run_command(
        f"{phase_prefix}rq3-score",
        [
            str(PYTHON),
            str(REPO / "script" / "rq3_recursive_operation_segmentation_eval.py"),
            "score",
            "--target-operations",
            str(TARGET_OPERATIONS),
            "--predictions",
            str(canonical / "predictions.jsonl"),
            "--inference-summary",
            str(assembled / "inference-summary.json"),
            "--verified-manifest",
            str(VERIFIED_MANIFEST),
            "--multires-assignments",
            str(MULTIRES_ASSIGNMENTS),
            "--out",
            str(score),
        ],
    )

    if preflight:
        print(
            json.dumps(
                {
                    "status": "ok",
                    "mode": "preflight",
                    "sessions": inference["sessions"],
                    "turns": inference["turns"],
                    "operations": inference["operations"],
                    "note": "recipe validation only; not a result",
                },
                sort_keys=True,
            ),
            flush=True,
        )
        return

    paired = paired_a2(score)
    direct_summary = read_json(score / "summary.json")
    assembled_summary = read_json(assembled / "summary.json")
    canonical_report = read_json(canonical / "canonicalization-report.json")
    operation_status = json.loads(operation_profile["stdout"])
    token_status = json.loads(token_profile["stdout"])
    index = read_json(EXPERIMENT / "packet-index.json")
    ordinal_by_session = {
        str(row["session"]): int(row["ordinal"]) for row in index["rows"]
    }
    scored_sessions = {
        str(row["session"]) for row in read_jsonl(score / "operation-score-rows.jsonl")
    }
    selected_ordinals = {ordinal_by_session[session] for session in scored_sessions}
    cost = annotation_cost(
        selected_ordinals,
        configured_workers=4,
    )

    direct_metrics = direct_summary["metrics"]["candidate"]
    a2_metrics = paired["a2_metrics"]
    recurrence_metrics = direct_summary["metrics"]["multires_recurrence"]
    b3_interval = paired["bcubed_f1"]["ci95"]
    boundary_interval = paired["boundary_f1"]["ci95"]

    if pilot:
        expected_manifest = read_json(PILOT / "packets" / "manifest.json")
        gate_delta = (
            float(direct_metrics["bcubed"]["f1"])
            - float(a2_metrics["bcubed"]["f1"])
        )
        gate_passed = gate_delta >= -0.03
        validity = {
            "deterministic_first_40_sorted_ids": selected_ordinals
            == set(range(1, PILOT_SESSIONS + 1)),
            "sessions": int(inference["sessions"]) == PILOT_SESSIONS,
            "turns_covered": int(inference["turns"])
            == int(expected_manifest["turns"]),
            "operations_covered": int(inference["operations"])
            == int(expected_manifest["operations"]),
            "operation_mass_conserved": int(
                assembled_summary["operation_count_mass"]
            )
            == int(expected_manifest["operations"])
            and int(operation_status["samples"]) == int(expected_manifest["operations"]),
            "token_mass_conserved": int(assembled_summary["provider_token_mass"])
            == int(token_status["samples"]),
            "zero_adjacent_display_path_collisions": int(
                canonical_report["remaining_adjacent_collisions"]
            )
            == 0,
            "canonical_prediction_coverage": int(canonical_report["predictions"])
            == int(expected_manifest["operations"]),
            "stock_pprof_operation_load": True,
            "stock_pprof_token_load": True,
            "paired_a2_population_equal": bool(paired["population_equal"]),
            "all_trajectories_successful": int(cost["successful_trajectories"])
            == PILOT_SESSIONS,
            "one_format_retry_limit": bool(cost["attempt_limit_valid"]),
            "zero_failures_after_retry": int(cost["failed_after_retry"]) == 0,
        }
        if not all(validity.values()):
            raise RuntimeError(
                "pilot validity failed: "
                + ", ".join(key for key, value in validity.items() if not value)
            )
        pilot_results = {
            "schema": "agentsight.direct-multilevel-codetrace-pilot.v1",
            "status": "complete",
            "selection": "first 40 trajectory IDs in sorted order",
            "population": direct_summary["population"],
            "methods": {
                "direct_multilevel": direct_metrics,
                "a2_same_slice": a2_metrics,
                "multi_resolution_recurrence": recurrence_metrics,
            },
            "paired_direct_minus_a2": paired,
            "paired_direct_minus_recurrence": direct_summary["bootstrap"][
                "candidate_minus_multires"
            ],
            "gate": {
                "rule": "direct B-cubed F1 >= same-slice A2 B-cubed F1 - 0.03",
                "direct_minus_a2_bcubed_f1": gate_delta,
                "passed": gate_passed,
                "full_run_authorized": gate_passed,
            },
            "cost": cost,
            "validity": validity,
            "annotation": {
                "raw_marks": int(assembled_summary["marks"]),
                "raw_unique_names": int(assembled_summary["semantic_names"]),
                "raw_path_depths": assembled_summary["path_depths"],
                "canonical_unique_names": int(
                    canonical_report["canonical_semantic_operation_ids"]
                ),
            },
        }
        write_json(PILOT / "raw-results.json", pilot_results)
        b3_delta = paired["bcubed_f1"]
        boundary_delta = paired["boundary_f1"]
        report = [
            "# Pilot results: direct multi-level annotation vs A2",
            "",
            "Status: **COMPLETE / VALID**",
            "",
            "## Deterministic slice",
            "",
            f"- first {PILOT_SESSIONS} trajectory IDs in sorted order;",
            f"- {direct_summary['population']['operations']:,} operations, "
            f"{direct_summary['population']['official_stages']:,} official stages, "
            f"and {direct_summary['population']['task_clusters']} task clusters;",
            "- source-only packets; official stages were opened only by the unchanged scorer.",
            "",
            "## Same-slice metrics and gate",
            "",
            "| Method | B³ P | B³ R | B³ F1 | Boundary P | Boundary R | Boundary F1 |",
            "|---|---:|---:|---:|---:|---:|---:|",
        ]
        for label, metrics in (
            ("Direct multi-level", direct_metrics),
            ("A2", a2_metrics),
            ("Multi-resolution recurrence", recurrence_metrics),
        ):
            report.append(
                f"| {label} | {metrics['bcubed']['precision']:.6f} | "
                f"{metrics['bcubed']['recall']:.6f} | "
                f"{metrics['bcubed']['f1']:.6f} | "
                f"{metrics['boundary']['precision']:.6f} | "
                f"{metrics['boundary']['recall']:.6f} | "
                f"{metrics['boundary']['f1']:.6f} |"
            )
        report.extend(
            [
                "",
                f"Direct minus A2 B³ F1: `{gate_delta:+.6f}`; paired task-cluster "
                f"95% interval `[{b3_delta['ci95'][0]:+.6f}, "
                f"{b3_delta['ci95'][1]:+.6f}]`.",
                "",
                "Direct minus A2 boundary F1 paired task-cluster 95% interval: "
                f"`[{boundary_delta['ci95'][0]:+.6f}, "
                f"{boundary_delta['ci95'][1]:+.6f}]`.",
                "",
                f"Binding gate (`direct B³ F1 >= A2 B³ F1 - 0.03`): "
                f"**{'PASS' if gate_passed else 'FAIL'}**.",
                "",
                "## Pilot cost",
                "",
                f"- successful trajectories: {cost['successful_trajectories']}/"
                f"{PILOT_SESSIONS};",
                f"- Codex calls: {cost['total_codex_calls']} "
                f"({cost['format_retries']} format retries);",
                f"- summed backend wall: {cost['summed_backend_wall_seconds']:.3f} s;",
                f"- active backend wall across interrupted/resumed worker waves: "
                f"{cost['active_backend_wall_seconds']:.3f} s;",
                f"- input/output tokens: {cost['usage'].get('input_tokens', 0):,} / "
                f"{cost['usage'].get('output_tokens', 0):,}.",
                "",
                "Context only: adopted A2 retained no model token/time telemetry; its "
                "405-trajectory artifact-time envelope was 3,261.89 s. Step 0086's "
                "42-record automatic pass used 7,740.107 s summed backend wall, "
                "2,674.314 s reconstructed three-worker critical path, 15,231,328 "
                "input tokens, and 311,097 output tokens.",
                "",
                "## Validity",
                "",
                "All 40 trajectories completed; the interrupted cache was reused only "
                "after response validation. The one invalid orphan response consumed "
                "its single format retry. Operation and token mass are conserved, "
                "canonical replay has zero adjacent display-path collisions, and both "
                "profiles load in stock pprof.",
                "",
                "The one-trajectory recipe-check score remains diagnostic only and is "
                "not included in this pilot result.",
                "",
            ]
        )
        (EXPERIMENT / "pilot-results.md").write_text(
            "\n".join(report), encoding="utf-8"
        )
        print(json.dumps(pilot_results, sort_keys=True), flush=True)
        return

    if b3_interval[0] >= 0 and boundary_interval[0] >= 0:
        verdict = "supported"
    elif b3_interval[1] < 0 or boundary_interval[1] < 0:
        verdict = "contradicted"
    else:
        verdict = "inconclusive"

    validity = {
        "sessions": int(inference["sessions"]) == EXPECTED_SESSIONS,
        "turns_covered": int(inference["turns"]) == EXPECTED_TURNS,
        "operations_covered": int(inference["operations"]) == EXPECTED_OPERATIONS,
        "official_stages_scored": int(direct_summary["population"]["official_stages"])
        == EXPECTED_STAGES,
        "task_clusters_scored": int(direct_summary["population"]["task_clusters"])
        == EXPECTED_TASKS,
        "operation_mass_conserved": int(assembled_summary["operation_count_mass"])
        == EXPECTED_OPERATIONS
        and int(operation_status["samples"]) == EXPECTED_OPERATIONS,
        "token_mass_conserved": int(assembled_summary["provider_token_mass"])
        == EXPECTED_TOKENS
        and int(token_status["samples"]) == EXPECTED_TOKENS,
        "zero_adjacent_display_path_collisions": int(
            canonical_report["remaining_adjacent_collisions"]
        )
        == 0,
        "canonical_prediction_coverage": int(canonical_report["predictions"])
        == EXPECTED_OPERATIONS,
        "stock_pprof_operation_load": True,
        "stock_pprof_token_load": True,
        "paired_a2_population_equal": bool(paired["population_equal"]),
        "all_trajectories_successful": int(cost["successful_trajectories"])
        == EXPECTED_SESSIONS,
        "one_format_retry_limit": bool(cost["attempt_limit_valid"]),
        "zero_failures_after_retry": int(cost["failed_after_retry"]) == 0,
    }
    if not all(validity.values()):
        raise RuntimeError(
            "full-run validity failed: "
            + ", ".join(key for key, value in validity.items() if not value)
        )

    raw_results = {
        "schema": "agentsight.direct-multilevel-codetrace-result.v1",
        "status": "complete",
        "hypothesis": (
            "A strong backend that directly writes multi-level transition marks "
            "in one pass per trajectory matches or beats evaluated A2."
        ),
        "hypothesis_verdict": verdict,
        "population": direct_summary["population"],
        "methods": {
            "direct_multilevel": direct_metrics,
            "a2": a2_metrics,
            "multi_resolution_recurrence": recurrence_metrics,
        },
        "paired_direct_minus_a2": paired,
        "paired_direct_minus_recurrence": direct_summary["bootstrap"][
            "candidate_minus_multires"
        ],
        "cost": cost,
        "validity": validity,
        "annotation": {
            "raw_marks": int(assembled_summary["marks"]),
            "raw_unique_names": int(assembled_summary["semantic_names"]),
            "raw_path_depths": assembled_summary["path_depths"],
            "canonical_unique_names": int(
                canonical_report["canonical_semantic_operation_ids"]
            ),
            "canonicalization": canonical_report,
        },
        "artifacts": {
            "raw_marks": relative(EXPERIMENT / "raw-marks"),
            "assembled_marks": relative(assembled / "operation-marks.json"),
            "canonical_marks": relative(canonical / "operation-marks.json"),
            "operation_profile": relative(profiles / "direct-operation.pb.gz"),
            "token_profile": relative(profiles / "direct-tokens.pb.gz"),
            "score": relative(score / "summary.json"),
        },
    }
    write_json(RAW_RESULTS, raw_results)
    print(json.dumps(raw_results, sort_keys=True), flush=True)


def write_incomplete_full_report() -> None:
    packet_rows = direct_backend.load_packets()
    by_ordinal = {row.ordinal: row for row in packet_rows}
    selected_ordinals = set(by_ordinal)
    run_records = read_jsonl(RUN_RECORDS)
    latest_records = {
        int(row["ordinal"]): row
        for row in run_records
        if int(row["ordinal"]) in selected_ordinals
    }
    if set(latest_records) != selected_ordinals:
        raise RuntimeError("not every trajectory reached terminal backend status")

    valid_ordinals: set[int] = set()
    validation_errors: dict[int, list[str]] = {}
    raw_mark_count = 0
    path_depths: Counter[int] = Counter()
    raw_names: set[str] = set()
    for ordinal, packet_row in by_ordinal.items():
        if not packet_row.raw_path.is_file():
            continue
        response = read_json(packet_row.raw_path)
        errors = direct_backend.validate_response(packet_row.packet, response)
        if errors:
            validation_errors[ordinal] = errors
            continue
        valid_ordinals.add(ordinal)
        raw_mark_count += len(response["marks"])
        for mark in response["marks"]:
            path = mark["semantic_path"]
            path_depths[len(path)] += 1
            raw_names.update(str(label) for label in path)

    failed_records = [
        latest_records[ordinal]
        for ordinal in sorted(selected_ordinals)
        if latest_records[ordinal].get("status") != "ok"
    ]
    missing_ordinals = sorted(selected_ordinals - valid_ordinals)
    if len(failed_records) != 1 or missing_ordinals != [53] or validation_errors:
        raise RuntimeError(
            "unexpected incomplete-run shape: "
            f"failures={len(failed_records)}, missing={missing_ordinals}, "
            f"invalid_cached={validation_errors}"
        )

    operation_usage = read_jsonl(OPERATION_USAGE)
    valid_sessions = {by_ordinal[ordinal].session for ordinal in valid_ordinals}
    retained_usage = [
        row for row in operation_usage if str(row["session"]) in valid_sessions
    ]
    retained_tokens = int(
        round(sum(float(row["total_tokens"]) for row in retained_usage))
    )
    retained_operations = sum(
        int(by_ordinal[ordinal].packet["operation_count"])
        for ordinal in valid_ordinals
    )
    retained_turns = sum(
        int(by_ordinal[ordinal].packet["turn_count"]) for ordinal in valid_ordinals
    )
    failed = failed_records[0]
    failed_packet = by_ordinal[int(failed["ordinal"])]
    missing_tokens = EXPECTED_TOKENS - retained_tokens
    cost = annotation_cost(selected_ordinals, configured_workers=4)
    pilot_results = read_json(PILOT / "raw-results.json")

    raw_results = {
        "schema": "agentsight.direct-multilevel-codetrace-result.v1",
        "status": "incomplete",
        "run_status": "invalid_for_full_population_scoring",
        "tested_hypothesis": "not_tested_on_complete_population",
        "research_value": "dependency-only full-run failure record; valid supporting pilot",
        "paper_impact": "none; no full-population number is authorized",
        "next_paper_decision": (
            "Do not use the pilot as the paper result and do not score the "
            "404-trajectory subset. The fixed one-retry backend protocol ended "
            "with one terminal format failure."
        ),
        "pilot": {
            "status": pilot_results["status"],
            "gate": pilot_results["gate"],
            "methods": pilot_results["methods"],
            "paired_direct_minus_a2": pilot_results["paired_direct_minus_a2"],
        },
        "full_backend_run": {
            "planned_trajectories": EXPECTED_SESSIONS,
            "terminal_trajectories": len(latest_records),
            "valid_raw_marks": len(valid_ordinals),
            "failed_after_retry": len(failed_records),
            "retained_turns": retained_turns,
            "expected_turns": EXPECTED_TURNS,
            "retained_operations": retained_operations,
            "expected_operations": EXPECTED_OPERATIONS,
            "retained_tokens": retained_tokens,
            "expected_tokens": EXPECTED_TOKENS,
            "missing_turns": int(failed_packet.packet["turn_count"]),
            "missing_operations": int(failed_packet.packet["operation_count"]),
            "missing_tokens": missing_tokens,
            "raw_marks": raw_mark_count,
            "raw_unique_names": len(raw_names),
            "raw_path_depths": {
                str(depth): count for depth, count in sorted(path_depths.items())
            },
        },
        "terminal_failure": {
            "ordinal": int(failed["ordinal"]),
            "session": failed["session"],
            "framework": failed["framework"],
            "attempts": failed["attempts"],
            "format_retry": failed["format_retry"],
            "errors": [
                attempt["errors"] for attempt in failed["attempt_records"]
            ],
            "raw_events": [
                relative(EXPERIMENT / "raw-events" / "0053-attempt-1.jsonl"),
                relative(EXPERIMENT / "raw-events" / "0053-attempt-2.jsonl"),
            ],
        },
        "cost": cost,
        "validity": {
            "all_405_backend_calls_terminal": len(latest_records)
            == EXPECTED_SESSIONS,
            "one_format_retry_limit": bool(cost["attempt_limit_valid"]),
            "404_cached_marks_individually_valid": len(valid_ordinals) == 404
            and not validation_errors,
            "complete_trajectory_coverage": False,
            "operation_mass_conserved": False,
            "token_mass_conserved": False,
            "full_downstream_pipeline_executed": False,
            "full_score_reported": False,
            "partial_subset_not_reported_as_result": True,
        },
        "artifacts": {
            "raw_marks": relative(EXPERIMENT / "raw-marks"),
            "run_records": relative(RUN_RECORDS),
            "pilot_results": relative(EXPERIMENT / "pilot-results.md"),
            "pilot_raw_results": relative(PILOT / "raw-results.json"),
        },
    }
    write_json(RAW_RESULTS, raw_results)

    cost_report = f"""# Cost record: direct multi-level annotation

## Configuration

- backend: `codex-cli 0.145.0`, model `gpt-5.6-sol`;
- one isolated call per trajectory, up to four workers;
- one format retry permitted per trajectory;
- interrupted valid outputs reused after schema validation.

## Complete backend-call accounting

| Measure | Value |
|---|---:|
| Planned / terminal trajectories | 405 / 405 |
| Valid / failed-after-retry trajectories | {cost['successful_trajectories']} / {cost['failed_after_retry']} |
| Total Codex calls | {cost['total_codex_calls']} |
| Format retries | {cost['format_retries']} |
| Summed backend wall | {cost['summed_backend_wall_seconds']:.3f} s |
| Active backend wall across interrupted/resumed waves | {cost['active_backend_wall_seconds']:.3f} s |
| Elapsed span including interruption | {cost['interrupted_elapsed_span_seconds']:.3f} s |
| Input tokens | {cost['usage'].get('input_tokens', 0):,} |
| Cached input tokens | {cost['usage'].get('cached_input_tokens', 0):,} |
| Output tokens | {cost['usage'].get('output_tokens', 0):,} |
| Reasoning output tokens | {cost['usage'].get('reasoning_output_tokens', 0):,} |

The active-wall value is the union of recorded backend-call intervals, so it
does not count the interruption gap twice or pretend that summed parallel call
time is elapsed wall time. The recovered ordinal-5 attempt uses its raw-event
completion mtime minus the earliest preceding worker completion as its timing
basis; that basis is explicit in `annotation-run-records.jsonl`.

## Context

| Backend/run | Population | Inference/workflow wall evidence | Input / output tokens |
|---|---:|---:|---:|
| Direct multi-level (this run) | 405 terminal, 404 valid | {cost['active_backend_wall_seconds']:.3f} s active backend wall | {cost['usage'].get('input_tokens', 0):,} / {cost['usage'].get('output_tokens', 0):,} |
| A2 historical waves | 405 | 3,261.89 s artifact-time envelope; model time unavailable | unavailable |
| Step 0086 automatic pass | 42 records | 7,740.107 s summed; 2,674.314 s reconstructed three-worker critical path | 15,231,328 / 311,097 |

The A2 envelope mixes inference, scheduling, idle time, and file writing and is
not directly comparable to backend request wall. This run's full pipeline cost
is unavailable because the fixed format policy left one trajectory uncovered,
so assembly, canonicalization, pprof replay, and scoring were correctly not run
on a partial population.
"""
    (EXPERIMENT / "cost-record.md").write_text(cost_report, encoding="utf-8")

    result_report = f"""# Results: direct multi-level annotation vs A2

Status: **FULL RUN INCOMPLETE / INVALID FOR FULL-POPULATION SCORING**

## Pilot gate

The binding first-40 pilot is complete and valid. Direct annotation reaches
B³ F1 `{pilot_results['methods']['direct_multilevel']['bcubed']['f1']:.6f}`
versus same-slice A2
`{pilot_results['methods']['a2_same_slice']['bcubed']['f1']:.6f}`, a point
delta of `{pilot_results['gate']['direct_minus_a2_bcubed_f1']:+.6f}`. The
paired task-cluster 95% interval is
`[{pilot_results['paired_direct_minus_a2']['bcubed_f1']['ci95'][0]:+.6f},
{pilot_results['paired_direct_minus_a2']['bcubed_f1']['ci95'][1]:+.6f}]`.
Boundary F1 is
`{pilot_results['methods']['direct_multilevel']['boundary']['f1']:.6f}` versus
`{pilot_results['methods']['a2_same_slice']['boundary']['f1']:.6f}`. The
binding `within 0.03` B³ gate therefore passed and authorized the full run.
Complete pilot details are in `pilot-results.md`.

## Full backend outcome

All 405 trajectories reached terminal backend status. Exactly 404 produced
valid raw marks. Ordinal 53 failed both allowed calls because each response
copied its long session ID without the final `-f7c2004c` suffix. Its semantic
marks otherwise passed the structural checks, but the exact A2 mark contract
requires the session string to match. The first failed response and its one
format retry are preserved under `raw-events/0053-attempt-{{1,2}}.jsonl`.

The 404 valid outputs cover {retained_turns:,}/{EXPECTED_TURNS:,} turns,
{retained_operations:,}/{EXPECTED_OPERATIONS:,} operations, and
{retained_tokens:,}/{EXPECTED_TOKENS:,} source tokens. The missing trajectory
contains {int(failed_packet.packet['turn_count'])} turns,
{int(failed_packet.packet['operation_count'])} operations, and
{missing_tokens:,} tokens.

## Scientific verdict

The complete-population hypothesis is **not tested**. Per the task
specification and experiment workflow, the 404-trajectory subset was not
packaged, canonicalized, scored, or reported as the full result. No full B³,
boundary, conservation, collision, or pprof claim is authorized. The positive
pilot remains a valid gate result, not a paper result.

```text
run status: incomplete / invalid for full-population scoring
tested hypothesis: inconclusive (complete population not scored)
research value: dependency-only full-run failure record; supporting pilot
paper impact: none
next paper decision: do not promote the pilot or partial population
```

## Validity checks

- all 405 backend trajectories reached terminal status;
- all 404 retained raw-mark files independently pass the fixed response
  validator;
- nine trajectories used the one allowed format retry: eight succeeded and one
  failed;
- no trajectory received a third call;
- the full packager rejected the missing annotation before downstream work;
- no 404-trajectory score or profile was generated.

## Deliverables

- `direct_annotation/`: fixed source-only backend and downstream harness;
- `raw-marks/`: 404 valid raw mark files;
- `raw-events/`: every backend event stream, including both terminal-failure
  attempts;
- `annotation-run-records.jsonl`: complete call, retry, timing, usage, and
  failure record;
- `pilot-results.md` and `pilot/`: valid binding pilot result and raw paths;
- `raw-results.json`: machine-readable terminal disposition;
- `cost-record.md` and `execution-log.md`: complete accounting and commands.
"""
    (EXPERIMENT / "results.md").write_text(result_report, encoding="utf-8")

    execution_log = """# Execution log

Run date: 2026-07-26 (America/Vancouver)

## Constraints

- No Git command was run.
- No file under `docs/paper/` or `docs/agentpprof-paper/` was touched.
- All new experiment deliverables remain in this `experiment-001` directory.
- The backend saw only one source-only packet per call and emitted only the
  response-schema JSON; raw events contain no prohibited tool event.

## Recipe check

The interrupted attempt's ordinal-396 raw mark was reused after validation.
The first replay accidentally used the workspace virtual environment and
stopped at import time because it lacked pandas; no scorer or result ran.
The authoritative replay used:

```text
/usr/bin/python3 direct_annotation/postprocess.py preflight
```

It completed root repair, fixed canonicalization, operation/token pprof
materialization, stock-pprof readback, and the unchanged scorer over one real
trajectory. Its metrics are diagnostic only.

## Pilot

```text
/usr/bin/python3 direct_annotation/annotate.py pilot --workers 4 --timeout-seconds 1200
/usr/bin/python3 direct_annotation/postprocess.py pilot
```

The pilot selected ordinals 1--40 from the packet index's sorted session IDs.
Seven valid cached marks were reused. The interrupted ordinal-5 event was
invalid, consumed its single format retry, and then passed. The complete
40-trajectory pilot passed the binding B³ gate.

## Authorized full backend run

```text
/usr/bin/python3 direct_annotation/annotate.py full --workers 4 --timeout-seconds 1200
```

The full command reused the 40 pilot marks and the valid ordinal-396 recipe
mark. It attempted every remaining trajectory. Terminal status was 404 valid
and one failed after retry.

The required full packager was invoked:

```text
/usr/bin/python3 direct_annotation/annotate.py package
```

It failed closed on ordinal 53's missing exact-session annotation. Therefore
`direct_annotation/postprocess.py full` was not invoked: doing so would either
fail coverage or score an unauthorized partial population.

## Terminal reporting

```text
/usr/bin/python3 direct_annotation/postprocess.py incomplete
```

This command validates all retained raw marks, recomputes call/cost totals, and
writes the terminal machine-readable and Markdown reports. It does not open
official stages or compute a partial scientific score.
"""
    (EXPERIMENT / "execution-log.md").write_text(
        execution_log, encoding="utf-8"
    )
    print(json.dumps(raw_results, sort_keys=True), flush=True)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("preflight", "pilot", "full", "incomplete"))
    return parser.parse_args()


if __name__ == "__main__":
    arguments = parse_args()
    if arguments.mode == "incomplete":
        write_incomplete_full_report()
    else:
        run_pipeline(arguments.mode)
