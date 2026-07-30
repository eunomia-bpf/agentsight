#!/usr/bin/env python3
"""Run paired BEFORE/ID-FIX ToolSandbox cells with identical model seeds."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import time

import run_pairs


HERE = Path(__file__).resolve().parent
PYTHON = HERE / "runtime/.venv/bin/python"
RUNNER = HERE / "run_toolsandbox_compatible.py"
OUTPUT = HERE / "episodes-idfix"
RUN_LOG = HERE / "idfix-run-records.jsonl"
CONDITIONS = ("before", "id-fix")
EXPANDED_PILOT_REPETITIONS = 4


def cells_for_group(group: str) -> list[tuple[str, int, int]]:
    """Return (scenario, seed, repetition) without inspecting any outcome."""

    if group == "preflight":
        return [
            (scenario, run_pairs.seed_for("preflight", index), 0)
            for index, scenario in enumerate(run_pairs.PREFLIGHT)
        ]
    if group == "pilot":
        return [
            (scenario, run_pairs.seed_for("pilot", index), 0)
            for index, scenario in enumerate(run_pairs.PILOT)
        ]
    if group == "pilot-expanded":
        cells = [
            (scenario, run_pairs.seed_for("pilot", index), 0)
            for index, scenario in enumerate(run_pairs.PILOT)
        ]
        for repetition in range(1, EXPANDED_PILOT_REPETITIONS):
            base = 202607500 + (repetition - 1) * 100
            cells.extend(
                (scenario, base + index, repetition)
                for index, scenario in enumerate(run_pairs.PILOT)
            )
        return cells
    if group == "confirmation":
        return [
            (scenario, run_pairs.seed_for("confirmation", index), 0)
            for index, scenario in enumerate(run_pairs.CONFIRMATION)
        ]
    raise ValueError(f"unknown group: {group}")


def episode_path(condition: str, seed: int, scenario: str) -> Path:
    return OUTPUT / condition / f"seed-{seed}" / scenario / "episode.json"


def run_cell(scenario: str, condition: str, seed: int) -> dict[str, object]:
    output = episode_path(condition, seed, scenario)
    if output.is_file():
        return {
            "scenario": scenario,
            "condition": condition,
            "trial_seed": seed,
            "status": "already-complete",
            "episode": str(output.relative_to(HERE)),
        }
    command = [
        str(PYTHON),
        str(RUNNER),
        "--execute",
        "--scenario",
        scenario,
        "--condition",
        "no-policy",
        "--condition-label",
        condition,
        "--trial-seed",
        str(seed),
        "--output-directory",
        str(OUTPUT),
    ]
    if condition == "id-fix":
        command.append("--sanitize-agent-tool-call-ids")
    started = time.monotonic()
    result = subprocess.run(
        command,
        cwd=HERE,
        text=True,
        encoding="utf-8",
        capture_output=True,
        check=False,
    )
    return {
        "scenario": scenario,
        "condition": condition,
        "trial_seed": seed,
        "status": "completed" if result.returncode == 0 else "failed",
        "returncode": result.returncode,
        "wall_seconds": time.monotonic() - started,
        "stdout": result.stdout,
        "stderr": result.stderr,
        "episode": str(output.relative_to(HERE)) if output.is_file() else None,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "group",
        choices=("preflight", "pilot", "pilot-expanded", "confirmation"),
    )
    args = parser.parse_args()
    failures = 0
    for cell_index, (scenario, seed, repetition) in enumerate(
        cells_for_group(args.group)
    ):
        order = (
            CONDITIONS if cell_index % 2 == 0 else tuple(reversed(CONDITIONS))
        )
        for condition in order:
            record = run_cell(scenario, condition, seed)
            record["group"] = args.group
            record["repetition"] = repetition
            with RUN_LOG.open("a", encoding="utf-8") as stream:
                stream.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
            print(
                json.dumps(
                    {
                        key: record.get(key)
                        for key in (
                            "scenario",
                            "condition",
                            "trial_seed",
                            "repetition",
                            "status",
                            "returncode",
                            "wall_seconds",
                        )
                    },
                    sort_keys=True,
                ),
                flush=True,
            )
            failures += int(record["status"] == "failed")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
