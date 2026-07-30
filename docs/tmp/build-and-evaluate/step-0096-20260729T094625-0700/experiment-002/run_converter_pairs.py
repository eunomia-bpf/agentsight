#!/usr/bin/env python3
"""Run fixed-budget BEFORE/converter-fix ToolSandbox trials."""

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
OUTPUT = HERE / "episodes-converter"
RUN_LOG = HERE / "converter-run-records.jsonl"
CONDITIONS = ("before", "converter-fix")
REPETITIONS = 3


def cells_for_group(group: str) -> list[tuple[str, int, int]]:
    """Return a complete outcome-blind (scenario, seed, repetition) manifest."""

    if group == "preflight":
        return [(run_pairs.PREFLIGHT[0], 202607800, 0)]
    if group == "preflight-mechanism":
        return [
            (run_pairs.PREFLIGHT[0], 202607801 + repetition, repetition)
            for repetition in range(5)
        ]
    populations = {
        "pilot": (run_pairs.PILOT, 202607900),
        "confirmation": (run_pairs.CONFIRMATION, 202608300),
    }
    if group not in populations:
        raise ValueError(f"unknown group: {group}")
    scenarios, initial_seed = populations[group]
    return [
        (scenario, initial_seed + repetition * 100 + index, repetition)
        for repetition in range(REPETITIONS)
        for index, scenario in enumerate(scenarios)
    ]


def episode_path(condition: str, seed: int, scenario: str) -> Path:
    return OUTPUT / condition / f"seed-{seed}" / scenario / "episode.json"


def run_cell(
    scenario: str,
    condition: str,
    seed: int,
    group: str,
    repetition: int,
) -> dict[str, object]:
    output = episode_path(condition, seed, scenario)
    if output.is_file():
        return {
            "scenario": scenario,
            "condition": condition,
            "trial_seed": seed,
            "group": group,
            "repetition": repetition,
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
    if condition == "converter-fix":
        command.append("--safe-execution-tool-call-ids")
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
        "group": group,
        "repetition": repetition,
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
        choices=("preflight", "preflight-mechanism", "pilot", "confirmation"),
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
            record = run_cell(
                scenario,
                condition,
                seed,
                args.group,
                repetition,
            )
            with RUN_LOG.open("a", encoding="utf-8") as stream:
                stream.write(
                    json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n"
                )
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
