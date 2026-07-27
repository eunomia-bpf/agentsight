#!/usr/bin/env python3
"""Resumable P2 bounded-Raw reader runner.

All writes are confined to this script's directory. The model sees only one
project sandbox mounted at /work and its cell output directory at /out.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import math
import os
import random
import re
import shutil
import statistics
import subprocess
import sys
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[3]
SOURCE_EXPERIMENT = (
    REPO
    / "docs/tmp/build-and-evaluate/step-0004-20260723T181008-0700/experiment-001"
)
SOURCE_PRIVATE = SOURCE_EXPERIMENT / "private"
CORRECTED_ANSWERS = (
    REPO
    / "docs/tmp/build-and-evaluate/rq7-error-taxonomy-20260725/"
    "corrected-oracle/corrected-answers.csv"
)
CORRECTED_METHOD_RESULTS = (
    REPO
    / "docs/tmp/build-and-evaluate/rq7-error-taxonomy-20260725/"
    "corrected-oracle/method-results.csv"
)
REPAIRED_TRAJECTORY = (
    REPO
    / "docs/tmp/build-and-evaluate/rq7-error-taxonomy-20260725/"
    "workdir-fix/trajectory-vs-v4.csv"
)
SOURCE_MODULE = REPO / "agentvis/research/rq7_measurement.py"
VENDORED_MODULE = ROOT / "vendor/rq7_measurement_frozen.py"
PRIVATE = ROOT / "private"
FULL = PRIVATE / "full/raw-model"
PREFLIGHT = PRIVATE / "preflight"
RAW = ROOT / "raw"

EXPECTED_HASHES = {
    "freeze.json": "838b814a31be1be48d28040d12235ee16489081f1d7214e8c7e814f8da057e35",
    "question-spec.md": "484d1c9af3b07511d2c0892166110387642d889f88b80bfc6927a7dc324de83e",
    "corrected-answers.csv": "bea810e09cd3925707714145c9a50d8804e57e26d99b6b1c308e9ec778e7e254",
    "trajectory-vs-v4.csv": "dd89048d5ba080066be2598d7582c65736c005fad9a1fdaa9c0e1d17b0ea8eac",
    "rq7_measurement.py": "e50adb5cb3882e8eca83295a80716f9db4a73290de7fe648aeef5d79ed1f9240",
}
MODEL = "gpt-5.6-terra"
REASONING = "medium"
REPETITIONS = 3
BOOTSTRAP_SEED = 20260722


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while block := handle.read(1024 * 1024):
            digest.update(block)
    return digest.hexdigest()


def read_json(path: Path) -> Any:
    return json.loads(path.read_text())


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")
    os.replace(temporary, path)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    os.replace(temporary, path)


def load_module() -> Any:
    path = VENDORED_MODULE if VENDORED_MODULE.is_file() else SOURCE_MODULE
    expected = EXPECTED_HASHES["rq7_measurement.py"]
    if sha256_file(path) != expected:
        raise RuntimeError(f"RQ7 source module hash changed: {path}")
    spec = importlib.util.spec_from_file_location("rq7_frozen", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load frozen RQ7 module")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.command_access_violation = command_access_violation
    return module


def command_access_violation(command: str, _sandbox: Path) -> str | None:
    """Deny actual remote-command invocations, not inert path/URL literals."""

    command_position = r"(?:^|[;&|()]|&&|\|\|)\s*"
    optional_prefix = r"(?:(?:command|sudo)\s+)?(?:env(?:\s+\S+=\S+)*\s+)?"
    remote = re.compile(
        command_position
        + optional_prefix
        + r"(?:/[A-Za-z0-9_./+@=-]+/)?(curl|wget|ssh|scp|rsync)\b",
        re.IGNORECASE,
    )
    git_remote = re.compile(
        command_position
        + optional_prefix
        + r"(?:/[A-Za-z0-9_./+@=-]+/)?git\s+(clone|fetch|pull)\b",
        re.IGNORECASE,
    )
    if remote.search(command) or git_remote.search(command):
        return "network_or_remote_command"
    return None


def ensure_hash(path: Path, expected: str) -> None:
    actual = sha256_file(path)
    if actual != expected:
        raise RuntimeError(f"hash mismatch for {path}: {actual} != {expected}")


def prepare() -> int:
    ensure_hash(SOURCE_PRIVATE / "freeze.json", EXPECTED_HASHES["freeze.json"])
    ensure_hash(
        SOURCE_PRIVATE / "question-spec.md", EXPECTED_HASHES["question-spec.md"]
    )
    ensure_hash(CORRECTED_ANSWERS, EXPECTED_HASHES["corrected-answers.csv"])
    ensure_hash(REPAIRED_TRAJECTORY, EXPECTED_HASHES["trajectory-vs-v4.csv"])
    ensure_hash(SOURCE_MODULE, EXPECTED_HASHES["rq7_measurement.py"])

    (ROOT / "vendor").mkdir(parents=True, exist_ok=True)
    if not VENDORED_MODULE.exists():
        shutil.copyfile(SOURCE_MODULE, VENDORED_MODULE)
    ensure_hash(VENDORED_MODULE, EXPECTED_HASHES["rq7_measurement.py"])

    PRIVATE.mkdir(parents=True, exist_ok=True)
    for source, destination in (
        (SOURCE_PRIVATE / "freeze.json", PRIVATE / "freeze.json"),
        (SOURCE_PRIVATE / "question-spec.md", PRIVATE / "question-spec.md"),
        (CORRECTED_ANSWERS, PRIVATE / "gold/corrected-answers.csv"),
        (CORRECTED_METHOD_RESULTS, PRIVATE / "gold/corrected-method-results.csv"),
        (REPAIRED_TRAJECTORY, PRIVATE / "gold/trajectory-vs-v4.csv"),
    ):
        destination.parent.mkdir(parents=True, exist_ok=True)
        if destination.exists():
            ensure_hash(destination, sha256_file(source))
        else:
            shutil.copyfile(source, destination)

    freeze = read_json(PRIVATE / "freeze.json")
    linked = []
    for project in freeze["projects"]:
        for source in project["sources"]:
            origin = SOURCE_PRIVATE / "frozen-home" / source["home_relative"]
            destination = PRIVATE / "frozen-home" / source["home_relative"]
            if sha256_file(origin) != source["sha256"]:
                raise RuntimeError(f"source hash mismatch: {origin}")
            destination.parent.mkdir(parents=True, exist_ok=True)
            if not destination.exists():
                try:
                    os.link(origin, destination)
                except OSError:
                    shutil.copyfile(origin, destination)
            if sha256_file(destination) != source["sha256"]:
                raise RuntimeError(f"prepared source hash mismatch: {destination}")
            linked.append(
                {
                    "project": project["project"],
                    "source_id": source["source_id"],
                    "sha256": source["sha256"],
                    "bytes": source["bytes"],
                    "path": str(destination.relative_to(ROOT)),
                }
            )

    runtime = {
        "model": MODEL,
        "reasoning": REASONING,
        "repetitions": REPETITIONS,
        "codex_version": subprocess.run(
            ["codex", "--version"], check=True, text=True, capture_output=True
        ).stdout.strip(),
        "bubblewrap_version": subprocess.run(
            ["bwrap", "--version"], check=True, text=True, capture_output=True
        ).stdout.strip(),
        "runner_sha256": sha256_file(Path(__file__)),
        "vendored_rq7_sha256": sha256_file(VENDORED_MODULE),
        "freeze_sha256": sha256_file(PRIVATE / "freeze.json"),
        "question_spec_sha256": sha256_file(PRIVATE / "question-spec.md"),
        "corrected_answers_sha256": sha256_file(
            PRIVATE / "gold/corrected-answers.csv"
        ),
        "repaired_trajectory_sha256": sha256_file(
            PRIVATE / "gold/trajectory-vs-v4.csv"
        ),
        "sources": linked,
    }
    write_json(ROOT / "runtime-freeze.json", runtime)
    print(f"prepared {len(linked)} frozen source files")
    return 0


def bwrap_control_command(work: Path, output: Path) -> list[str]:
    return [
        "bwrap",
        "--die-with-parent",
        "--unshare-pid",
        "--clearenv",
        "--ro-bind",
        "/usr",
        "/usr",
        "--ro-bind",
        "/bin",
        "/bin",
        "--ro-bind",
        "/lib",
        "/lib",
        "--ro-bind",
        "/lib64",
        "/lib64",
        "--proc",
        "/proc",
        "--dev",
        "/dev",
        "--tmpfs",
        "/tmp",
        "--tmpfs",
        "/home",
        "--ro-bind",
        str(work),
        "/work",
        "--bind",
        str(output),
        "/out",
        "--chdir",
        "/work",
        "--",
        "/bin/bash",
        "-lc",
        (
            "printf '%s\\n' "
            "'/home/yunwei37/workspace/agentsight-agent-nebula-research/"
            "docs/tmp/build-and-evaluate/"
            "rq7-error-taxonomy-20260725/corrected-oracle/corrected-answers.csv'; "
            "test ! -e "
            "/home/yunwei37/workspace/agentsight-agent-nebula-research/"
            "docs/tmp/build-and-evaluate/"
            "rq7-error-taxonomy-20260725/corrected-oracle/corrected-answers.csv"
        ),
    ]


def controls() -> int:
    prepare()
    module = load_module()
    project = min(
        read_json(PRIVATE / "freeze.json")["projects"],
        key=lambda row: sum(source["bytes"] for source in row["sources"]),
    )
    sandbox = module.prepare_model_sandbox(
        read_json(PRIVATE / "freeze.json"), project, PRIVATE
    )
    control_dir = ROOT / "controls"
    control_dir.mkdir(parents=True, exist_ok=True)
    inert_command = (
        "rg -n '/home/yunwei37/workspace/example/docs/paper/paper.tex' sources/"
    )
    inert_result = command_access_violation(inert_command, sandbox)
    deny_results = {
        command: command_access_violation(command, sandbox)
        for command in (
            "curl https://example.com",
            "git fetch origin",
            "printf '%s' 'https://example.com'",
        )
    }
    command = bwrap_control_command(sandbox, control_dir)
    completed = subprocess.run(command, text=True, capture_output=True)
    isolation_pass = (
        completed.returncode == 0
        and "corrected-answers.csv" in completed.stdout
    )
    result = {
        "status": "pass"
        if (
            inert_result is None
            and deny_results["curl https://example.com"]
            == "network_or_remote_command"
            and deny_results["git fetch origin"] == "network_or_remote_command"
            and deny_results["printf '%s' 'https://example.com'"] is None
            and isolation_pass
        )
        else "fail",
        "inert_absolute_path_command": inert_command,
        "inert_absolute_path_monitor_result": inert_result,
        "remote_command_monitor_results": deny_results,
        "outside_read_path_visible": not isolation_pass,
        "bwrap_returncode": completed.returncode,
        "bwrap_stdout": completed.stdout,
        "bwrap_stderr": completed.stderr,
        "bwrap_command": command,
    }
    write_json(control_dir / "boundary-controls.json", result)
    if result["status"] != "pass":
        raise RuntimeError("boundary controls failed")
    print("boundary controls pass")
    return 0


def corrected_gold() -> dict[str, str]:
    rows = read_csv(PRIVATE / "gold/corrected-answers.csv")
    return {row["id"]: row["corrected_expected"] for row in rows}


def normalize_checkpoint(path: Path, rows: list[dict[str, Any]], cost: dict[str, Any]) -> None:
    gold = corrected_gold()
    valid = cost["terminal_status"] == "complete"
    normalized = []
    for row in rows:
        expected = gold[row["id"]]
        status = row["status"] if valid else "abstain"
        answer = str(row["answer"]).strip() if status == "answer" else ""
        normalized.append(
            {
                **row,
                "original_frozen_expected": row["expected"],
                "expected": expected,
                "status": status,
                "answer": answer,
                "correct": int(status == "answer" and answer == expected),
                "wrong": int(status == "answer" and answer != expected),
                "scoreable": int(valid),
                "cell_terminal_status": cost["terminal_status"],
            }
        )
    write_json(
        path,
        {
            "scoring_protocol": "corrected-v4",
            "corrected_answers_sha256": EXPECTED_HASHES["corrected-answers.csv"],
            "results": normalized,
            "cost": cost,
        },
    )


def validate_checkpoint(path: Path) -> dict[str, Any]:
    saved = read_json(path)
    if (
        saved.get("scoring_protocol") != "corrected-v4"
        or saved.get("corrected_answers_sha256")
        != EXPECTED_HASHES["corrected-answers.csv"]
        or len(saved.get("results", [])) != 20
    ):
        raise RuntimeError(f"checkpoint is not an atomic corrected-v4 result: {path}")
    return saved


def call_cell(project: dict[str, Any], repetition: int, destination: Path) -> dict[str, Any]:
    checkpoint = destination / "scored.json"
    if checkpoint.exists():
        saved = validate_checkpoint(checkpoint)
        print(f"resume {project['project']} rep {repetition}", flush=True)
        return saved
    attempt = destination / "attempt-1"
    unscored_checkpoint = attempt / "scored.json"
    module = load_module()
    freeze = read_json(PRIVATE / "freeze.json")
    if unscored_checkpoint.exists():
        unscored = read_json(unscored_checkpoint)
        rows, cost = unscored["results"], unscored["cost"]
        print(
            f"recover unscored output {project['project']} rep {repetition}",
            flush=True,
        )
    else:
        print(f"model {project['project']} rep {repetition}", flush=True)
        rows, cost = module.model_call(
            freeze,
            project,
            PRIVATE,
            attempt,
            MODEL,
            REASONING,
            repetition,
        )
    normalize_checkpoint(checkpoint, rows, cost)
    saved = validate_checkpoint(checkpoint)
    print(
        f"done {project['project']} rep {repetition}: "
        f"{cost['terminal_status']} "
        f"{sum(row['correct'] for row in saved['results'])}/20",
        flush=True,
    )
    return saved


def preflight(repair_note: str | None) -> int:
    controls_result = read_json(ROOT / "controls/boundary-controls.json")
    if controls_result.get("status") != "pass":
        raise RuntimeError("preflight requires passing boundary controls")
    freeze = read_json(PRIVATE / "freeze.json")
    project = min(
        freeze["projects"],
        key=lambda row: (
            sum(source["bytes"] for source in row["sources"]),
            row["project"],
        ),
    )
    passed = ROOT / "preflight-result.json"
    if passed.exists() and read_json(passed).get("status") == "pass":
        print("resume passing real preflight")
        return 0
    attempts_path = ROOT / "preflight-attempts.json"
    attempts = read_json(attempts_path) if attempts_path.exists() else []
    attempt_number = len(attempts) + 1
    if attempt_number > 3:
        raise RuntimeError("three real preflight attempts exhausted")
    if attempt_number > 1 and not repair_note:
        raise RuntimeError(
            "a repeated preflight requires --repair-note describing the "
            "demonstrated infrastructure repair"
        )
    destination = PREFLIGHT / f"attempt-{attempt_number}" / project["project"]
    saved = call_cell(project, 0, destination)
    cost = saved["cost"]
    scoreable = sum(int(row["scoreable"]) for row in saved["results"])
    result = {
        "status": "pass"
        if (
            cost["terminal_status"] == "complete"
            and scoreable == 20
            and int(cost["tool_calls"]) >= 1
            and int(cost["tool_result_bytes"]) >= 1
        )
        else "fail",
        "project": project["project"],
        "attempt": attempt_number,
        "repair_note": repair_note or "",
        "model": MODEL,
        "reasoning": REASONING,
        "terminal_status": cost["terminal_status"],
        "scoreable_rows": scoreable,
        "tool_calls": cost["tool_calls"],
        "tool_result_bytes": cost["tool_result_bytes"],
        "wall_seconds": cost["wall_seconds"],
        "checkpoint": str(
            (destination / "scored.json").relative_to(ROOT)
        ),
    }
    attempts.append(result)
    write_json(attempts_path, attempts)
    write_json(ROOT / f"preflight-result-attempt-{attempt_number}.json", result)
    if result["status"] != "pass":
        raise RuntimeError(f"real preflight failed: {result}")
    write_json(passed, result)
    print(f"real preflight pass: {project['project']}")
    return 0


def full(workers: int) -> int:
    preflight_result = read_json(ROOT / "preflight-result.json")
    if preflight_result.get("status") != "pass":
        raise RuntimeError("full matrix requires a passing real preflight")
    if workers not in (1, 2):
        raise RuntimeError("protocol allows one or two workers")
    freeze = read_json(PRIVATE / "freeze.json")

    # Repetition-major scheduling ensures that concurrent calls never rebuild
    # the same project's shared sandbox.
    for repetition in range(1, REPETITIONS + 1):
        jobs = []
        with ThreadPoolExecutor(max_workers=workers) as pool:
            for project in freeze["projects"]:
                destination = FULL / project["project"] / f"rep-{repetition}"
                jobs.append(
                    pool.submit(call_cell, project, repetition, destination)
                )
            for job in as_completed(jobs):
                job.result()
    checkpoints = list(FULL.glob("*/rep-*/scored.json"))
    write_json(
        PRIVATE / "full/matrix-status.json",
        {
            "expected_cells": 18,
            "completed_checkpoints": len(checkpoints),
            "status": "complete" if len(checkpoints) == 18 else "incomplete",
        },
    )
    if len(checkpoints) != 18:
        raise RuntimeError(f"incomplete matrix: {len(checkpoints)}/18")
    print("full matrix complete: 18/18 checkpoints")
    return 0


def percentile(values: list[float], probability: float) -> float:
    ordered = sorted(values)
    position = (len(ordered) - 1) * probability
    low = int(position)
    high = min(low + 1, len(ordered) - 1)
    fraction = position - low
    return ordered[low] * (1 - fraction) + ordered[high] * fraction


def summarize(selected: list[dict[str, Any]]) -> dict[str, Any]:
    correct = sum(int(row["correct"]) for row in selected)
    wrong = sum(int(row["wrong"]) for row in selected)
    denominator = len(selected)
    abstain = denominator - correct - wrong
    answered = correct + wrong
    scoreable = sum(int(row.get("scoreable", 1)) for row in selected)
    return {
        "rows": denominator,
        "scoreable": scoreable,
        "correct": correct,
        "wrong": wrong,
        "abstain": abstain,
        "correct_coverage": correct / denominator if denominator else 0.0,
        "conditional_accuracy": correct / answered if answered else 0.0,
        "scoreable_rate": scoreable / denominator if denominator else 0.0,
    }


def score() -> int:
    freeze = read_json(PRIVATE / "freeze.json")
    projects = [project["project"] for project in freeze["projects"]]
    rows = []
    costs = []
    cells = []
    for project in projects:
        for repetition in range(1, REPETITIONS + 1):
            checkpoint = FULL / project / f"rep-{repetition}/scored.json"
            if not checkpoint.exists():
                raise RuntimeError(f"missing checkpoint: {checkpoint}")
            saved = read_json(checkpoint)
            rows.extend(saved["results"])
            costs.append(saved["cost"])
            cells.append(
                {
                    "project": project,
                    "repetition": repetition,
                    "terminal_status": saved["cost"]["terminal_status"],
                    **summarize(saved["results"]),
                    "wall_seconds": saved["cost"]["wall_seconds"],
                    "tool_calls": saved["cost"]["tool_calls"],
                    "tool_result_bytes": saved["cost"]["tool_result_bytes"],
                    "input_tokens": saved["cost"]["input_tokens"],
                    "cached_input_tokens": saved["cost"]["cached_input_tokens"],
                    "output_tokens": saved["cost"]["output_tokens"],
                    "reasoning_tokens": saved["cost"]["reasoning_tokens"],
                }
            )
    if len(rows) != 360 or len(costs) != 18:
        raise RuntimeError(f"expected 360 rows/18 costs, got {len(rows)}/{len(costs)}")

    aggregates = []
    for family in ("A", "B", "C", "D"):
        aggregates.append(
            {"method": "raw_model", "family": family, **summarize(
                [row for row in rows if row["family"] == family]
            )}
        )
    aggregates.append({"method": "raw_model", "family": "ALL", **summarize(rows)})
    aggregates.append(
        {
            "method": "raw_model",
            "family": "B+C",
            **summarize([row for row in rows if row["family"] in {"B", "C"}]),
        }
    )

    project_family = []
    for project in projects:
        for family in ("A", "B", "C", "D", "B+C", "ALL"):
            families = set("ABCD") if family == "ALL" else (
                {"B", "C"} if family == "B+C" else {family}
            )
            selected = [
                row
                for row in rows
                if row["project"] == project and row["family"] in families
            ]
            project_family.append(
                {"project": project, "family": family, **summarize(selected)}
            )

    raw_project_repetitions: dict[str, list[float]] = defaultdict(list)
    for project in projects:
        for repetition in range(1, REPETITIONS + 1):
            selected = [
                row
                for row in rows
                if row["project"] == project
                and row["repetition"] == repetition
                and row["family"] in {"B", "C"}
            ]
            raw_project_repetitions[project].append(
                sum(int(row["correct"]) for row in selected) / len(selected)
            )
    estimate = statistics.mean(
        1.0 - statistics.mean(raw_project_repetitions[project])
        for project in projects
    )
    rng = random.Random(BOOTSTRAP_SEED)
    draws = []
    for _ in range(10_000):
        sampled_projects = [rng.choice(projects) for _ in projects]
        effects = []
        for project in sampled_projects:
            repetitions = raw_project_repetitions[project]
            raw_mean = statistics.mean(
                rng.choice(repetitions) for _ in repetitions
            )
            effects.append(1.0 - raw_mean)
        draws.append(statistics.mean(effects))
    effect = {
        "contrast": "repaired_trajectory_minus_raw_bc_correct_coverage",
        "estimate": estimate,
        "ci_low": percentile(draws, 0.025),
        "ci_high": percentile(draws, 0.975),
        "draws": 10_000,
        "seed": BOOTSTRAP_SEED,
        "project_effects": {
            project: 1.0 - statistics.mean(raw_project_repetitions[project])
            for project in projects
        },
        "raw_project_repetitions": raw_project_repetitions,
    }
    invalid_cells = [
        cell for cell in cells if cell["terminal_status"] != "complete"
    ]
    effect["invalid_cells"] = [
        {
            "project": cell["project"],
            "repetition": cell["repetition"],
            "terminal_status": cell["terminal_status"],
        }
        for cell in invalid_cells
    ]
    effect["decision"] = (
        "mixed_or_inconclusive"
        if invalid_cells
        else (
            "trajectory_accuracy_superior"
            if effect["ci_low"] > 0
            else (
                "accuracy_parity"
                if effect["ci_low"] >= -0.05 and effect["ci_high"] <= 0.05
                else (
                    "raw_wins"
                    if effect["ci_high"] < -0.05
                    else "mixed_or_inconclusive"
                )
            )
        )
    )

    baseline_rows = read_csv(PRIVATE / "gold/corrected-method-results.csv")
    baseline_rows = [row for row in baseline_rows if row["method"] != "trajectory"]
    for row in read_csv(PRIVATE / "gold/trajectory-vs-v4.csv"):
        baseline_rows.append({**row, "method": "trajectory"})
    comparison = []
    for method in ("final_state", "counts", "procgrep", "trajectory"):
        for family, families in (
            ("ALL", set("ABCD")),
            ("B+C", {"B", "C"}),
        ):
            selected = [
                row
                for row in baseline_rows
                if row["method"] == method and row["family"] in families
            ]
            summary = summarize(selected)
            comparison.append({"method": method, "family": family, **summary})
    for aggregate in aggregates:
        if aggregate["family"] in {"ALL", "B+C"}:
            comparison.append(dict(aggregate))

    result_fields = [
        "id",
        "project",
        "family",
        "template",
        "method",
        "repetition",
        "status",
        "answer",
        "expected",
        "original_frozen_expected",
        "correct",
        "wrong",
        "scoreable",
        "cell_terminal_status",
        "question_spec_sha256",
    ]
    cost_fields = [
        "project",
        "method",
        "repetition",
        "source_bytes",
        "input_bytes",
        "output_bytes",
        "tool_result_bytes",
        "input_tokens",
        "cached_input_tokens",
        "output_tokens",
        "reasoning_tokens",
        "model_calls",
        "tool_calls",
        "build_seconds",
        "query_seconds",
        "wall_seconds",
        "peak_rss_kib",
        "terminal_status",
    ]
    summary_fields = [
        "project",
        "repetition",
        "terminal_status",
        "rows",
        "scoreable",
        "correct",
        "wrong",
        "abstain",
        "correct_coverage",
        "conditional_accuracy",
        "scoreable_rate",
        "wall_seconds",
        "tool_calls",
        "tool_result_bytes",
        "input_tokens",
        "cached_input_tokens",
        "output_tokens",
        "reasoning_tokens",
    ]
    aggregate_fields = [
        "method",
        "family",
        "rows",
        "scoreable",
        "correct",
        "wrong",
        "abstain",
        "correct_coverage",
        "conditional_accuracy",
        "scoreable_rate",
    ]
    project_fields = ["project", "family", *aggregate_fields[2:]]
    write_csv(RAW / "method-results.csv", rows, result_fields)
    write_csv(RAW / "costs.csv", costs, cost_fields)
    write_csv(RAW / "cell-summary.csv", cells, summary_fields)
    write_csv(RAW / "aggregate.csv", aggregates, aggregate_fields)
    write_csv(RAW / "project-family.csv", project_family, project_fields)
    write_csv(RAW / "baseline-comparison.csv", comparison, aggregate_fields)
    write_json(RAW / "effects.json", effect)

    all_summary = next(row for row in aggregates if row["family"] == "ALL")
    bc_summary = next(row for row in aggregates if row["family"] == "B+C")
    run_summary = {
        "status": "complete",
        "model": MODEL,
        "reasoning": REASONING,
        "matrix_cells": len(cells),
        "registered_rows": len(rows),
        "terminal_statuses": dict(
            (status, sum(cell["terminal_status"] == status for cell in cells))
            for status in sorted({cell["terminal_status"] for cell in cells})
        ),
        "all": all_summary,
        "bc": bc_summary,
        "effect": effect,
        "total_wall_seconds_sum": sum(float(row["wall_seconds"]) for row in costs),
        "total_tool_calls": sum(int(row["tool_calls"]) for row in costs),
        "total_tool_result_bytes": sum(
            int(row["tool_result_bytes"]) for row in costs
        ),
        "total_input_tokens": sum(int(row["input_tokens"]) for row in costs),
        "total_cached_input_tokens": sum(
            int(row["cached_input_tokens"]) for row in costs
        ),
        "total_output_tokens": sum(int(row["output_tokens"]) for row in costs),
        "total_reasoning_tokens": sum(
            int(row["reasoning_tokens"]) for row in costs
        ),
    }
    write_json(RAW / "run-summary.json", run_summary)
    print(json.dumps(run_summary, indent=2))
    return 0


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser()
    subparsers = result.add_subparsers(dest="command", required=True)
    subparsers.add_parser("prepare")
    subparsers.add_parser("controls")
    preflight_parser = subparsers.add_parser("preflight")
    preflight_parser.add_argument("--repair-note")
    full_parser = subparsers.add_parser("full")
    full_parser.add_argument("--workers", type=int, default=1)
    subparsers.add_parser("score")
    return result


def main() -> int:
    args = parser().parse_args()
    if args.command == "prepare":
        return prepare()
    if args.command == "controls":
        return controls()
    if args.command == "preflight":
        return preflight(args.repair_note)
    if args.command == "full":
        return full(args.workers)
    if args.command == "score":
        return score()
    raise AssertionError(args.command)


if __name__ == "__main__":
    raise SystemExit(main())
