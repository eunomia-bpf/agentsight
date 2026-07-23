#!/usr/bin/env python3
"""Run the lean RQ4 profile-construction scaling matrix.

The experiment reuses four existing normalized public operation files, the
release agentpprof binary, GNU time, and output parsing from R327.  It runs two
fixed stack constructions three times over each file and their exact union.
It does not build the profiler, fetch data, invoke an LLM, or inspect Git.
"""

from __future__ import annotations

import argparse
import csv
import json
import platform
import subprocess
from pathlib import Path
from statistics import median
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BINARY = ROOT / "agentpprof" / "target" / "release" / "agentpprof"
DEFAULT_OUT = ROOT / ".agentsight" / "experiments" / "rq4-cost-scaling-v1"
R160_RESULT = ROOT / "docs" / "visexp" / "out" / "artifact-usability-r160.json"
TIME = Path("/usr/bin/time")

WORKLOADS = [
    (
        "agentreward",
        [
            ROOT
            / "docs/visexp/out/external-agent-trace-agentreward-r288"
            / "agentreward-operations.jsonl"
        ],
    ),
    (
        "satraj",
        [
            ROOT
            / "docs/visexp/out/external-agent-trace-satraj-r289"
            / "satraj-operations.jsonl"
        ],
    ),
    (
        "osworld-human",
        [
            ROOT
            / "docs/visexp/out/external-agent-trace-osworldhuman-r290"
            / "osworld-human-operations.jsonl"
        ],
    ),
    (
        "agentnet",
        [
            ROOT
            / "docs/visexp/out/external-agent-trace-agentnet-r291"
            / "agentnet-operations.jsonl"
        ],
    ),
]
WORKLOADS.append(("union", [path for _, paths in WORKLOADS for path in paths]))

PROFILES = {
    "semantic": "project,agent,task,phase,op,tool,status",
    "raw-action": "project,agent,action,status",
}
REQUIRED_FIELDS = sorted(
    {field for stack in PROFILES.values() for field in stack.split(",")}
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--binary", type=Path, default=DEFAULT_BINARY)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--reps", type=int, default=3)
    return parser.parse_args()


def relative(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return str(path.resolve())


def validate_inputs() -> tuple[dict[str, dict[str, Any]], dict[Path, dict[str, Any]]]:
    by_path: dict[Path, dict[str, Any]] = {}
    for _, paths in WORKLOADS[:-1]:
        for path in paths:
            if not path.is_file():
                raise SystemExit(f"missing operation file: {relative(path)}")
            rows = 0
            sample_total = 0.0
            missing = {field: 0 for field in REQUIRED_FIELDS}
            with path.open(encoding="utf-8") as handle:
                for line_number, line in enumerate(handle, 1):
                    if not line.strip():
                        continue
                    try:
                        operation = json.loads(line)
                    except json.JSONDecodeError as exc:
                        raise SystemExit(
                            f"invalid JSON in {relative(path)}:{line_number}: {exc}"
                        ) from exc
                    fields = operation.get("fields") or {}
                    rows += 1
                    sample_total += float(operation.get("value", 0))
                    for field in REQUIRED_FIELDS:
                        if fields.get(field) is None:
                            missing[field] += 1
            if any(missing.values()):
                raise SystemExit(f"required-field coverage failed for {relative(path)}: {missing}")
            if sample_total != rows:
                raise SystemExit(
                    f"expected unit operation values in {relative(path)}; "
                    f"rows={rows}, samples={sample_total}"
                )
            by_path[path] = {
                "path": relative(path),
                "rows": rows,
                "samples": int(sample_total),
                "missing_fields": missing,
            }

    workloads: dict[str, dict[str, Any]] = {}
    for name, paths in WORKLOADS:
        workloads[name] = {
            "operation_files": [relative(path) for path in paths],
            "operation_rows": sum(by_path[path]["rows"] for path in paths),
            "expected_samples": sum(by_path[path]["samples"] for path in paths),
        }
    return workloads, by_path


def run_one(
    *,
    binary: Path,
    out_dir: Path,
    rep: int,
    workload: str,
    paths: list[Path],
    operation_rows: int,
    profile: str,
) -> dict[str, Any]:
    stem = f"rep-{rep:02d}-{workload}-{profile}"
    run_dir = out_dir / "runs" / stem
    run_dir.mkdir(parents=True, exist_ok=True)
    profile_path = run_dir / "profile.pb.gz"
    timing_path = run_dir / "time.json"
    stdout_path = run_dir / "stdout.json"
    stderr_path = run_dir / "stderr.txt"

    command = [
        str(TIME),
        "-f",
        '{"wall_s":%e,"max_rss_kb":%M,"exit_status":%x}',
        "-o",
        str(timing_path),
        str(binary),
    ]
    for path in paths:
        command.extend(["--operation-file", relative(path)])
    command.extend(
        [
            "--view",
            "operations",
            "--stack",
            PROFILES[profile],
            "--format",
            "pprof",
            "--deterministic-output",
            "-o",
            str(profile_path),
        ]
    )
    result = subprocess.run(
        command,
        cwd=ROOT,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    stdout_path.write_text(result.stdout, encoding="utf-8")
    stderr_path.write_text(result.stderr, encoding="utf-8")
    if result.returncode != 0:
        raise SystemExit(
            f"agentpprof failed: rep={rep} workload={workload} profile={profile}; "
            f"see {relative(stderr_path)}"
        )
    try:
        timing = json.loads(timing_path.read_text(encoding="utf-8"))
        status = json.loads(result.stdout)
    except (json.JSONDecodeError, OSError) as exc:
        raise SystemExit(f"unparseable run output for {stem}: {exc}") from exc
    if status.get("status") != "ok":
        raise SystemExit(f"non-ok profiler status for {stem}: {status}")
    if int(status.get("samples", -1)) != operation_rows:
        raise SystemExit(
            f"sample mismatch for {stem}: expected {operation_rows}, "
            f"got {status.get('samples')}"
        )
    if not profile_path.is_file():
        raise SystemExit(f"missing profile output for {stem}")
    opened = subprocess.run(
        ["go", "tool", "pprof", "-top", str(profile_path)],
        cwd=ROOT,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if opened.returncode != 0:
        raise SystemExit(
            f"stock pprof rejected {stem}: {opened.stderr.strip()}"
        )
    if profile_path.stat().st_size <= 0:
        raise SystemExit(f"empty profile output for {stem}")

    wall_ms = float(timing["wall_s"]) * 1000.0
    return {
        "rep": rep,
        "workload": workload,
        "profile": profile,
        "operation_rows": operation_rows,
        "wall_ms": wall_ms,
        "ms_per_operation": wall_ms / operation_rows,
        "operations_per_second": operation_rows / float(timing["wall_s"])
        if float(timing["wall_s"]) > 0
        else None,
        "max_rss_kb": int(timing["max_rss_kb"]),
        "output_bytes": profile_path.stat().st_size,
        "samples": int(status["samples"]),
        "unique_stacks": int(status["unique_stacks"]),
        "exit_status": int(timing["exit_status"]),
        "profile_output": relative(profile_path),
        "stdout": relative(stdout_path),
        "stderr": relative(stderr_path),
    }


def linear_fit(points: list[tuple[float, float]]) -> dict[str, float | None]:
    xs = [point[0] for point in points]
    ys = [point[1] for point in points]
    x_mean = sum(xs) / len(xs)
    y_mean = sum(ys) / len(ys)
    x_variance = sum((value - x_mean) ** 2 for value in xs)
    slope = sum((x - x_mean) * (y - y_mean) for x, y in points) / x_variance
    intercept = y_mean - slope * x_mean
    residual = sum((y - (intercept + slope * x)) ** 2 for x, y in points)
    total = sum((y - y_mean) ** 2 for y in ys)
    return {
        "slope_ms_per_operation": slope,
        "intercept_ms": intercept,
        "r_squared": 1.0 - residual / total if total > 0 else None,
    }


def summarize(
    rows: list[dict[str, Any]],
    workloads: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    cells = []
    for workload, input_summary in workloads.items():
        for profile in PROFILES:
            selected = [
                row
                for row in rows
                if row["workload"] == workload and row["profile"] == profile
            ]
            wall = [float(row["wall_ms"]) for row in selected]
            rss = [int(row["max_rss_kb"]) for row in selected]
            cell = {
                "workload": workload,
                "profile": profile,
                "operation_rows": input_summary["operation_rows"],
                "reps": len(selected),
                "wall_ms": wall,
                "median_wall_ms": median(wall),
                "median_ms_per_operation": median(
                    [float(row["ms_per_operation"]) for row in selected]
                ),
                "median_operations_per_second": median(
                    [
                        float(row["operations_per_second"])
                        for row in selected
                        if row["operations_per_second"] is not None
                    ]
                ),
                "max_rss_kb": rss,
                "median_max_rss_kb": median(rss),
                "largest_max_rss_kb": max(rss),
                "output_bytes": selected[0]["output_bytes"],
                "samples": selected[0]["samples"],
                "unique_stacks": selected[0]["unique_stacks"],
            }
            cells.append(cell)

    fits = {}
    for profile in PROFILES:
        profile_cells = [cell for cell in cells if cell["profile"] == profile]
        points = [
            (float(cell["operation_rows"]), float(cell["median_wall_ms"]))
            for cell in profile_cells
        ]
        ordered = sorted(points)
        fits[profile] = {
            **linear_fit(points),
            "monotonic_nondecreasing": all(
                right[1] >= left[1] for left, right in zip(ordered, ordered[1:])
            ),
        }

    union_semantic = next(
        cell
        for cell in cells
        if cell["workload"] == "union" and cell["profile"] == "semantic"
    )
    practical = (
        float(union_semantic["median_wall_ms"]) < 10_000
        and int(union_semantic["largest_max_rss_kb"]) < 1024 * 1024
    )

    r160 = json.loads(R160_RESULT.read_text(encoding="utf-8"))
    clean_s = float(r160["run_metadata"]["clean_runtime_seconds"])
    cached_s = float(r160["run_metadata"]["cached_runtime_seconds"])
    cache_evidence = {
        "source": relative(R160_RESULT),
        "predecessor_cli": "AgentFlame",
        "paired_observations": 1,
        "identical_fixed_inputs": bool(r160["clean_cached_input_equality"]["matches"]),
        "clean_runtime_s": clean_s,
        "cached_runtime_s": cached_s,
        "observed_speedup": clean_s / cached_s,
        "clean_llm_calls": int(r160["clean_llm_tagger"]["llm_calls"]),
        "cached_llm_calls": int(r160["cached_llm_tagger"]["llm_calls"]),
        "cached_hits": int(r160["cached_llm_tagger"]["cache_hits"]),
        "cached_requests": int(r160["cached_llm_tagger"]["requests"]),
        "boundary": "cache-mechanism support, not repeated current-binary timing",
    }
    return {
        "status": "complete",
        "valid": len(rows) == len(WORKLOADS) * len(PROFILES) * 3,
        "invocations": len(rows),
        "cells": cells,
        "descriptive_linear_fits": fits,
        "practical_scaling_over_tested_range": practical,
        "practical_thresholds": {
            "union_semantic_median_wall_ms_lt": 10_000,
            "union_semantic_all_reps_peak_rss_kb_lt": 1024 * 1024,
        },
        "prior_cache_mechanism_evidence": cache_evidence,
    }


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    fieldnames = [
        "rep",
        "workload",
        "profile",
        "operation_rows",
        "wall_ms",
        "ms_per_operation",
        "operations_per_second",
        "max_rss_kb",
        "output_bytes",
        "samples",
        "unique_stacks",
        "exit_status",
        "profile_output",
        "stdout",
        "stderr",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    args = parse_args()
    if args.reps != 3:
        raise SystemExit("the approved RQ4 plan requires exactly --reps 3")
    binary = args.binary.resolve()
    out_dir = args.out_dir.resolve()
    if not binary.is_file():
        raise SystemExit(f"missing release binary: {relative(binary)}")
    if not TIME.is_file():
        raise SystemExit(f"missing GNU time: {TIME}")
    workloads, source_files = validate_inputs()
    out_dir.mkdir(parents=True, exist_ok=True)

    rows = []
    for rep in range(1, args.reps + 1):
        profile_order = list(PROFILES) if rep % 2 else list(reversed(PROFILES))
        for workload, paths in WORKLOADS:
            for profile in profile_order:
                rows.append(
                    run_one(
                        binary=binary,
                        out_dir=out_dir,
                        rep=rep,
                        workload=workload,
                        paths=paths,
                        operation_rows=workloads[workload]["operation_rows"],
                        profile=profile,
                    )
                )

    summary = summarize(rows, workloads)
    if not summary["valid"]:
        raise SystemExit("full matrix is incomplete")
    report = {
        "schema_version": 1,
        "run_id": "rq4-cost-scaling-v1",
        "binary": relative(binary),
        "binary_version": subprocess.run(
            [str(binary), "--version"],
            cwd=ROOT,
            check=True,
            text=True,
            stdout=subprocess.PIPE,
        ).stdout.strip(),
        "machine": {
            "platform": platform.platform(),
            "processor": platform.processor(),
        },
        "profiles": PROFILES,
        "workloads": workloads,
        "source_files": [source_files[path] for path in source_files],
        "runs": rows,
        "summary": summary,
    }
    (out_dir / "result.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    write_csv(out_dir / "runs.csv", rows)
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
