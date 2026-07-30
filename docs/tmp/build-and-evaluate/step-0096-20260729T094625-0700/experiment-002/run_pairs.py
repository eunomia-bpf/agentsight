#!/usr/bin/env python3
"""Run paired no-policy/profile-policy ToolSandbox cells sequentially."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import time


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[4]
SOURCE = (
    REPO
    / "docs/tmp/build-and-evaluate/step-0095-20260729T024929-0700"
    / "experiment-001"
)
PYTHON = HERE / "runtime/.venv/bin/python"
RUNNER = HERE / "run_toolsandbox_compatible.py"
POLICY = SOURCE / "analyst/policies/profile-policy.txt"
OUTPUT = HERE / "episodes-compatible"
RUN_LOG = HERE / "run-records.jsonl"

PREFLIGHT = ["turn_on_location_low_battery_mode"]
PILOT = [
    "add_contact_with_name_and_phone_number",
    "add_reminder_content_and_week_delta_and_time",
    "cellular_off",
    "find_days_till_holiday_wifi_off",
    "modify_contact_with_message_recency",
    "remove_contact_by_phone_no_remove_contact_insufficient_information",
    "search_message_with_recency_latest",
    "send_message_with_contact_content_cellular_off",
]
ALL_OUTCOME = [
    "add_contact_with_name_and_phone_number",
    "add_reminder_content_and_date_and_time",
    "add_reminder_content_and_week_delta_and_time",
    "add_reminder_content_and_weekday_delta_and_time",
    "cellular_off",
    "find_days_till_holiday",
    "find_days_till_holiday_wifi_off",
    "find_thanksgiving_timestamp",
    "get_cellular",
    "get_wifi",
    "modify_contact_with_message_recency",
    "remove_contact_by_phone",
    "remove_contact_by_phone_no_remove_contact_insufficient_information",
    "remove_contact_with_id",
    "search_message_with_recency_latest",
    "search_message_with_recency_oldest",
    "search_name_with_relationship",
    "search_phone_number_with_name",
    "search_relationship_with_phone_number",
    "search_reminder_with_creation_recency_yesterday",
    "search_reminder_with_recency_upcoming",
    "search_reminder_with_recency_yesterday",
    "search_sender_phone_number_with_content",
    "send_message_with_contact_content_cellular_off",
    "send_message_with_phone_number_and_content",
    "turn_on_cellular_low_battery_mode",
    "turn_on_wifi_low_battery_mode",
    "update_contact_relationship_with_relationship",
    "update_contact_relationship_with_relationship_twice_multiple_user_turn",
    "update_contact_with_id_and_phone_number",
    "wifi_off",
]
CONFIRMATION = [name for name in ALL_OUTCOME if name not in set(PILOT)]


def seed_for(group: str, index: int) -> int:
    base = {"preflight": 202607290, "pilot": 202607300, "confirmation": 202607400}
    return base[group] + index


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
        condition,
        "--trial-seed",
        str(seed),
        "--output-directory",
        str(OUTPUT),
    ]
    if condition == "profile-policy":
        command.extend(["--policy-file", str(POLICY)])
    started = time.monotonic()
    result = subprocess.run(
        command,
        cwd=SOURCE,
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
    parser.add_argument("group", choices=("preflight", "pilot", "confirmation"))
    args = parser.parse_args()
    scenarios = {
        "preflight": PREFLIGHT,
        "pilot": PILOT,
        "confirmation": CONFIRMATION,
    }[args.group]
    failures = 0
    for index, scenario in enumerate(scenarios):
        seed = seed_for(args.group, index)
        order = (
            ("no-policy", "profile-policy")
            if index % 2 == 0
            else ("profile-policy", "no-policy")
        )
        for condition in order:
            record = run_cell(scenario, condition, seed)
            RUN_LOG.parent.mkdir(parents=True, exist_ok=True)
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
