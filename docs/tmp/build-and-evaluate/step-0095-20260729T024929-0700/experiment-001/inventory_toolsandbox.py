#!/usr/bin/env python3
"""Inventory the fixed ToolSandbox population without playing any scenario.

The screen is deliberately mechanical: a scenario is unavailable offline only
when one of the tools in its declared ``tool_allow_list`` resolves to the
official RapidAPI module.  No trajectory or benchmark outcome is read.
"""

from __future__ import annotations

import argparse
import hashlib
import inspect
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Sequence

TOOL_SANDBOX_COMMIT = "165848b9a78cead7ca7fe7c89c688b58e6501219"
RAPID_API_MODULE = "tool_sandbox.tools.rapid_api_search_tools"
PREFLIGHT_SCENARIO = "turn_on_location_low_battery_mode"

# This is the fixed 37-scenario population declared by the experiment plan.
# It is copied here so inventory never has to inspect prior result contents.
DECLARED_SCENARIOS: tuple[str, ...] = (
    "add_contact_with_name_and_phone_number",
    "add_reminder_content_and_date_and_time",
    "add_reminder_content_and_week_delta_and_time",
    "add_reminder_content_and_weekday_delta_and_time",
    "cellular_off",
    "convert_currency",
    "find_address_with_lat_lon",
    "find_current_city_low_battery_mode",
    "find_days_till_holiday",
    "find_days_till_holiday_wifi_off",
    "find_stock_symbol_with_company_name",
    "find_stock_symbol_with_company_name_low_battery_mode",
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
    "turn_on_location_low_battery_mode",
    "turn_on_wifi_low_battery_mode",
    "update_contact_relationship_with_relationship",
    "update_contact_relationship_with_relationship_twice_multiple_user_turn",
    "update_contact_with_id_and_phone_number",
    "wifi_off",
)


def repository_root() -> Path:
    """Find the repository containing the experiment and official checkout."""

    candidates = [Path.cwd().resolve(), *Path(__file__).resolve().parents]
    for candidate in candidates:
        if (candidate / ".agentsight/external/ToolSandbox").is_dir():
            return candidate
    raise FileNotFoundError("cannot locate .agentsight/external/ToolSandbox")


def default_checkout() -> Path:
    return repository_root() / ".agentsight/external/ToolSandbox"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def list_sha256(items: Sequence[str]) -> str:
    """Hash a sorted, newline-terminated list."""

    payload = "".join(f"{item}\n" for item in sorted(items)).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _git(checkout: Path, *args: str) -> str:
    return subprocess.check_output(
        ["git", "-C", str(checkout), *args],
        text=True,
    ).strip()


def verify_checkout(checkout: Path) -> dict[str, Any]:
    """Fail unless the official checkout is at the exact clean commit."""

    checkout = checkout.resolve()
    commit = _git(checkout, "rev-parse", "HEAD")
    status = _git(checkout, "status", "--porcelain")
    if commit != TOOL_SANDBOX_COMMIT:
        raise RuntimeError(
            f"ToolSandbox commit mismatch: expected {TOOL_SANDBOX_COMMIT}, got {commit}"
        )
    if status:
        raise RuntimeError(f"ToolSandbox checkout is modified:\n{status}")
    return {
        "path": str(checkout),
        "commit": commit,
        "clean": True,
        "pyproject_sha256": sha256_file(checkout / "pyproject.toml"),
    }


def _load_official(checkout: Path) -> tuple[Any, Any, Any]:
    checkout_string = str(checkout.resolve())
    if checkout_string not in sys.path:
        sys.path.insert(0, checkout_string)
    from tool_sandbox.common.tool_discovery import ToolBackend, get_all_tools
    from tool_sandbox.scenarios import named_scenarios

    return ToolBackend, get_all_tools, named_scenarios


def _evaluator_metadata() -> dict[str, Any]:
    from tool_sandbox.common.evaluation import Evaluation, EvaluationResult
    from tool_sandbox.common.scenario import Scenario

    play_source = Path(inspect.getsourcefile(Scenario.play_and_evaluate) or "")
    evaluate_source = Path(inspect.getsourcefile(Evaluation.evaluate) or "")
    return {
        "entrypoint": (
            "tool_sandbox.common.scenario.Scenario.play_and_evaluate"
        ),
        "evaluator": "tool_sandbox.common.evaluation.Evaluation.evaluate",
        "call_mapping": (
            "Scenario.play_and_evaluate -> self.evaluation.evaluate("
            "execution_context=execution_context, max_turn_count=self.max_messages)"
        ),
        "result_type": (
            "tool_sandbox.common.evaluation.EvaluationResult"
        ),
        "result_fields": [
            field.name for field in EvaluationResult.__attrs_attrs__
        ],
        "combined_similarity": (
            "int(minefield_similarity == 0) * milestone_similarity"
        ),
        "exact_success": "similarity == 1",
        "source": {
            "scenario_file": str(play_source),
            "scenario_file_sha256": sha256_file(play_source),
            "scenario_first_line": inspect.getsourcelines(
                Scenario.play_and_evaluate
            )[1],
            "evaluation_file": str(evaluate_source),
            "evaluation_file_sha256": sha256_file(evaluate_source),
            "evaluation_first_line": inspect.getsourcelines(Evaluation.evaluate)[
                1
            ],
        },
    }


def build_inventory(checkout: Path | None = None) -> dict[str, Any]:
    """Build the dependency-only scenario and evaluator inventory."""

    checkout = (checkout or default_checkout()).resolve()
    checkout_metadata = verify_checkout(checkout)
    ToolBackend, get_all_tools, named_scenarios = _load_official(checkout)
    scenarios = named_scenarios(preferred_tool_backend=ToolBackend.DEFAULT)
    tools = get_all_tools(preferred_tool_backend=ToolBackend.DEFAULT)

    missing = sorted(set(DECLARED_SCENARIOS) - set(scenarios))
    if missing:
        raise KeyError(f"declared scenarios missing from official checkout: {missing}")

    scenario_rows: list[dict[str, Any]] = []
    for scenario_name in sorted(DECLARED_SCENARIOS):
        scenario = scenarios[scenario_name]
        declared_tools = sorted(scenario.starting_context.tool_allow_list or tools)
        dependencies = []
        for tool_name in declared_tools:
            if tool_name not in tools:
                raise KeyError(
                    f"{scenario_name}: declared tool {tool_name!r} is unresolved"
                )
            tool = tools[tool_name]
            dependencies.append(
                {
                    "tool": tool_name,
                    "module": tool.__module__,
                    "source_file": str(Path(inspect.getsourcefile(tool) or "")),
                }
            )
        unavailable = [
            dependency
            for dependency in dependencies
            if dependency["module"] == RAPID_API_MODULE
        ]
        scenario_rows.append(
            {
                "name": scenario_name,
                "availability": "requires_rapidapi" if unavailable else "offline",
                "declared_tools": dependencies,
                "unavailable_declared_tools": unavailable,
                "categories": sorted(str(category) for category in scenario.categories),
                "max_messages": scenario.max_messages,
                "evaluator": {
                    "milestone_count": len(
                        scenario.evaluation.milestone_matcher.milestones
                    ),
                    "minefield_count": len(
                        scenario.evaluation.minefield_matcher.milestones
                    ),
                },
            }
        )

    offline = [
        row["name"] for row in scenario_rows if row["availability"] == "offline"
    ]
    excluded = [
        row["name"]
        for row in scenario_rows
        if row["availability"] == "requires_rapidapi"
    ]
    outcome = [name for name in offline if name != PREFLIGHT_SCENARIO]
    if PREFLIGHT_SCENARIO not in offline:
        raise RuntimeError(f"preflight scenario is not offline: {PREFLIGHT_SCENARIO}")

    return {
        "schema": "agentsight.toolsandbox.dependency-inventory.v1",
        "checkout": checkout_metadata,
        "screen": {
            "basis": (
                "official Scenario.starting_context.tool_allow_list resolved "
                "through tool_sandbox.common.tool_discovery.get_all_tools"
            ),
            "unavailable_module": RAPID_API_MODULE,
            "uses_outcomes": False,
        },
        "counts": {
            "declared": len(DECLARED_SCENARIOS),
            "offline": len(offline),
            "requires_rapidapi": len(excluded),
            "outcome_after_preflight_removal": len(outcome),
        },
        "declared_scenarios": list(sorted(DECLARED_SCENARIOS)),
        "declared_scenarios_sha256": list_sha256(DECLARED_SCENARIOS),
        "offline_scenarios": offline,
        "offline_scenarios_sha256": list_sha256(offline),
        "rapidapi_scenarios": excluded,
        "rapidapi_scenarios_sha256": list_sha256(excluded),
        "preflight_scenario": PREFLIGHT_SCENARIO,
        "outcome_scenarios": outcome,
        "outcome_scenarios_sha256": list_sha256(outcome),
        "evaluator_mapping": _evaluator_metadata(),
        "scenarios": scenario_rows,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkout", type=Path, default=default_checkout())
    parser.add_argument("--output", type=Path)
    parser.add_argument(
        "--names-only",
        choices=("declared", "offline", "rapidapi", "outcome"),
    )
    args = parser.parse_args()

    inventory = build_inventory(args.checkout)
    if args.names_only:
        key = f"{args.names_only}_scenarios"
        print("\n".join(inventory[key]))
        return 0

    payload = json.dumps(inventory, indent=2, ensure_ascii=False, sort_keys=True)
    if args.output is None:
        print(payload)
    else:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
