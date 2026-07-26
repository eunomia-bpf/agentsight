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

import rq3_source_native_task_progress_boundary_eval as source_score  # noqa: E402


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

EXPECTED_SESSIONS = 405
EXPECTED_TURNS = 17_148
EXPECTED_OPERATIONS = 20_866
EXPECTED_TOKENS = 494_862_929
EXPECTED_STAGES = 2_948
EXPECTED_TASKS = 251
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


def filter_preflight_canonical_names(session: str, output: Path) -> Path:
    fixed = read_json(FIXED_CANONICAL_NAMES)
    task_names = {
        str(row["task_name"])
        for row in read_jsonl(OPERATION_USAGE)
        if str(row["session"]) == session
    }
    if len(task_names) != 1:
        raise RuntimeError("preflight task name is not unique")
    task_name = next(iter(task_names))
    write_json(
        output,
        {
            "task_roots": {
                key: value
                for key, value in fixed["task_roots"].items()
                if key == task_name
            },
            "semantic_labels": fixed["semantic_labels"],
        },
    )
    return output


def annotation_cost() -> dict[str, Any]:
    records = read_jsonl(RUN_RECORDS)
    latest: dict[int, dict[str, Any]] = {}
    for row in records:
        if row.get("status") == "ok":
            latest[int(row["ordinal"])] = row
    if len(latest) != EXPECTED_SESSIONS:
        raise RuntimeError(f"expected 405 successful annotation records, got {len(latest)}")
    usage = Counter()
    summed_wall = 0.0
    retries = 0
    call_count = 0
    starts_and_durations: list[tuple[int, float, float]] = []
    retry_reason_counts: Counter[str] = Counter()
    attempt_limit_valid = True
    for ordinal, row in latest.items():
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
    preflight_ordinal = 396
    preflight_wall = sum(
        duration
        for ordinal, _start, duration in starts_and_durations
        if ordinal == preflight_ordinal
    )
    full_wave = [
        (start, duration)
        for ordinal, start, duration in starts_and_durations
        if ordinal != preflight_ordinal
    ]
    full_wave_seconds = max(start + duration for start, duration in full_wave) - min(
        start for start, _duration in full_wave
    )
    return {
        "backend": "codex-cli 0.145.0",
        "model": "gpt-5.6-sol",
        "worker_pattern": "one preflight call, then four parallel isolated one-trajectory calls",
        "successful_trajectories": len(latest),
        "trajectory_calls": EXPECTED_SESSIONS,
        "format_retries": retries,
        "failed_after_retry": 0,
        "attempt_limit_valid": attempt_limit_valid,
        "retry_reason_counts": dict(sorted(retry_reason_counts.items())),
        "total_codex_calls": call_count,
        "summed_backend_wall_seconds": summed_wall,
        "preflight_backend_wall_seconds": preflight_wall,
        "four_worker_wave_seconds": full_wave_seconds,
        "reconstructed_complete_critical_path_seconds": (
            preflight_wall + full_wave_seconds
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
    if set(direct_by_key) != set(a2_by_key):
        raise RuntimeError("direct/A2 operation score populations differ")
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
    if set(direct_pair_by_key) != set(a2_pair_by_key):
        raise RuntimeError("direct/A2 boundary score populations differ")
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
    return {
        "population_equal": True,
        "operation_rows": len(paired_operations),
        "pair_rows": len(paired_pairs),
        "bcubed_f1": b3,
        "boundary_f1": boundary,
    }


def run_pipeline(preflight: bool) -> None:
    root = EXPERIMENT / "preflight" / "pipeline" if preflight else EXPERIMENT
    assembled = root / "assembled"
    canonical = root / "canonical"
    score = root / "score"
    profiles = root / "profiles"
    profiles.mkdir(parents=True, exist_ok=True)
    packet_dir = EXPERIMENT / "preflight" / "packets" if preflight else PACKETS
    annotation_dir = (
        EXPERIMENT / "preflight" / "annotations"
        if preflight
        else EXPERIMENT / "raw-annotations"
    )
    canonical_names = FIXED_CANONICAL_NAMES
    if preflight:
        packet = read_json(packet_dir / "batch-01.json")["sessions"][0]
        canonical_names = filter_preflight_canonical_names(
            str(packet["session"]), EXPERIMENT / "preflight" / "canonical-names.json"
        )

    run_command(
        f"{'preflight-' if preflight else ''}assemble-root-repair",
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
            "preflight" if preflight else "full",
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
        f"{'preflight-' if preflight else ''}fixed-canonicalization",
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
        f"{'preflight-' if preflight else ''}operation-profile",
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
        f"{'preflight-' if preflight else ''}token-profile",
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
        f"{'preflight-' if preflight else ''}pprof-operation-readback",
        ["go", "tool", "pprof", "-top", str(profiles / "direct-operation.pb.gz")],
    )
    run_command(
        f"{'preflight-' if preflight else ''}pprof-token-readback",
        ["go", "tool", "pprof", "-top", str(profiles / "direct-tokens.pb.gz")],
    )
    run_command(
        f"{'preflight-' if preflight else ''}rq3-score",
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
    a2_summary = read_json(A2_SUMMARY)
    assembled_summary = read_json(assembled / "summary.json")
    canonical_report = read_json(canonical / "canonicalization-report.json")
    operation_status = json.loads(operation_profile["stdout"])
    token_status = json.loads(token_profile["stdout"])
    cost = annotation_cost()

    direct_metrics = direct_summary["metrics"]["candidate"]
    a2_metrics = a2_summary["metrics"]["candidate"]
    recurrence_metrics = direct_summary["metrics"]["multires_recurrence"]
    b3_interval = paired["bcubed_f1"]["ci95"]
    boundary_interval = paired["boundary_f1"]["ci95"]
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


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("preflight", "full"))
    return parser.parse_args()


if __name__ == "__main__":
    arguments = parse_args()
    run_pipeline(arguments.mode == "preflight")
