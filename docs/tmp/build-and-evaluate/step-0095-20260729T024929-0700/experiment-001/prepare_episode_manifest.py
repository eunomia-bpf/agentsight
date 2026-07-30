#!/usr/bin/env python3
"""Freeze ToolSandbox scenario, seed, condition-order, and episode manifests."""

from __future__ import annotations

import argparse
import hashlib
import json
import random
from pathlib import Path
from typing import Any

EXPERIMENT = Path(__file__).resolve().parent
CONDITIONS = ("no-policy", "profile-policy", "raw-policy")
TRIAL_SEEDS = tuple(2026072910 + index for index in range(8))
ORDER_SEED = 2026072999
SAMPLING = {"temperature": 0.2, "top_p": 0.95, "max_tokens": 2048,
            "frequency_penalty": 0.0, "presence_penalty": 0.0}


def dump_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def prepare(inventory_path: Path) -> dict[str, Any]:
    inventory = json.loads(inventory_path.read_text(encoding="utf-8"))
    if inventory["counts"] != {
        "declared": 37,
        "offline": 32,
        "outcome_after_preflight_removal": 31,
        "requires_rapidapi": 5,
    }:
        raise ValueError(f"unexpected dependency inventory: {inventory['counts']}")
    output_dir = EXPERIMENT / "toolsandbox"
    offline = inventory["offline_scenarios"]
    outcome = inventory["outcome_scenarios"]
    preflight = inventory["preflight_scenario"]
    dump_json(output_dir / "scenarios-32.json", {
        "scenarios": offline,
        "sha256": inventory["offline_scenarios_sha256"],
    })
    dump_json(output_dir / "scenarios-31.json", {
        "scenarios": outcome,
        "sha256": inventory["outcome_scenarios_sha256"],
    })
    dump_json(output_dir / "trial-seeds.json", {
        "full": list(TRIAL_SEEDS),
        "pilot": list(TRIAL_SEEDS[:4]),
        "sampling": SAMPLING,
    })
    rng = random.Random(ORDER_SEED)
    order_rows: list[dict[str, Any]] = []
    episode_rows: list[dict[str, Any]] = []
    position = 0
    for scenario in outcome:
        for trial_seed in TRIAL_SEEDS:
            order = list(CONDITIONS)
            rng.shuffle(order)
            order_rows.append({
                "scenario": scenario,
                "trial_seed": trial_seed,
                "condition_order": order,
            })
            for condition in order:
                position += 1
                episode_rows.append({
                    "position": position,
                    "scenario": scenario,
                    "trial_seed": trial_seed,
                    "condition": condition,
                    "sampling": SAMPLING,
                    "expected_output": (
                        f"toolsandbox/raw/{condition}/seed-{trial_seed}/"
                        f"{scenario}/episode.json"
                    ),
                })
    if len(episode_rows) != 744:
        raise AssertionError(f"expected 744 episodes, got {len(episode_rows)}")
    dump_json(output_dir / "condition-order.json", {
        "seed": ORDER_SEED,
        "rows": order_rows,
    })
    expected_path = output_dir / "expected-episodes.jsonl"
    expected_path.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in episode_rows),
        encoding="utf-8",
    )
    preflight_rows = [
        {
            "position": index,
            "scenario": preflight,
            "trial_seed": TRIAL_SEEDS[0],
            "condition": condition,
            "sampling": SAMPLING,
        }
        for index, condition in enumerate(CONDITIONS, 1)
    ]
    dump_json(output_dir / "preflight-manifest.json", {"rows": preflight_rows})
    report = {
        "status": "PASS",
        "full_episode_count": len(episode_rows),
        "pilot_episode_count": len(outcome) * 4 * len(CONDITIONS),
        "outcome_scenario_count": len(outcome),
        "condition_count": len(CONDITIONS),
        "full_trial_count": len(TRIAL_SEEDS),
        "hashes": {
            path.name: sha256_file(path)
            for path in [
                output_dir / "scenarios-32.json",
                output_dir / "scenarios-31.json",
                output_dir / "trial-seeds.json",
                output_dir / "condition-order.json",
                expected_path,
                output_dir / "preflight-manifest.json",
            ]
        },
    }
    dump_json(output_dir / "manifest-report.json", report)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--inventory",
        type=Path,
        default=EXPERIMENT / "toolsandbox-inventory.json",
    )
    args = parser.parse_args()
    print(json.dumps(prepare(args.inventory), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
