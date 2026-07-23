#!/usr/bin/env python3
"""Produce source-only semantic-operation marks for AgentProcessBench packets.

The helper deliberately consumes only the annotation packets.  It maps the
visible operation stream into a small shared vocabulary, contracts incidental
reasoning/tool alternation, and exposes sustained same-operation runs as
recovery work.  It never reads benchmark labels or localization scores.
"""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ROOTS = {
    ("bfcl", "city"): "Complete messaging workflow",
    ("bfcl", "file"): "Complete file-management workflow",
    ("bfcl", "flight"): "Complete travel workflow",
    ("bfcl", "tire"): "Complete vehicle workflow",
    ("gaia_dev", "american"): "Answer research question",
    ("gaia_dev", "city"): "Answer research question",
    ("gaia_dev", "file"): "Answer research question",
    ("hotpotqa", "american"): "Answer multi-hop question",
    ("hotpotqa", "city"): "Answer multi-hop question",
    ("tau2", "flight"): "Resolve travel-support request",
    ("tau2", "info"): "Resolve order-support request",
    ("tau2", "phone"): "Resolve phone-support request",
}

RESEARCH_FAMILIES = {"gaia_dev", "hotpotqa"}
SUPPORT_FAMILY = "tau2"

WORKSPACE_INSPECTION = {"pwd", "ls", "cd", "find"}
FILE_ANALYSIS = {
    "cat",
    "wc",
    "grep",
    "sort",
    "tail",
    "diff",
    "mean",
    "standard_deviation",
    "round_number",
    "read_file",
}
FILE_MODIFICATION = {"echo", "touch", "cp", "mv", "mkdir", "rm", "rmdir"}
ESCALATION = {"transfer_to_human_agents", "contact_customer_support"}

IDENTITY_WORDS = (
    "find_user",
    "get_user",
    "get_customer",
    "login_status",
    "_login",
    "authenticate_",
    "list_users",
)
RECORD_WORDS = (
    "get_details",
    "get_order",
    "get_product",
    "get_reservation",
    "get_account",
    "get_bills",
    "get_data_usage",
    "get_booking_history",
    "get_credit_card_balance",
    "retrieve_invoice",
    "get_watchlist",
    "get_ticket",
    "view_messages",
)
DIAGNOSTIC_WORDS = (
    "check_",
    "displaycarstatus",
    "run_speed_test",
    "can_send_mms",
)
OPTION_WORDS = (
    "search_direct_flight",
    "search_onestop_flight",
    "get_nearest_airport",
    "list_all_airports",
    "get_available_stocks",
    "get_stock_info",
    "get_symbol_by_name",
    "get_current_time",
    "find_nearest_tire_shop",
    "get_zipcode",
)
COMPUTE_WORDS = ("calculate", "compute_", "estimate_", "_to_", "liter_to", "gallon_to")
VERIFY_WORDS = ("verify_",)
VEHICLE_ACTIONS = {
    "activateparkingbrake",
    "fillfueltank",
    "lockdoors",
    "startengine",
    "pressbrakepedal",
    "releasebrakepedal",
    "set_navigation",
}
COMMUNICATION_ACTIONS = {
    "send_message",
    "send_certificate",
    "send_payment_request",
    "post_tweet",
    "retweet",
    "comment",
    "mention",
}
ACTION_WORDS = (
    "book_",
    "update_",
    "modify_",
    "cancel_",
    "purchase_",
    "register_",
    "return_",
    "exchange_",
    "place_",
    "add_to_",
    "delete_",
    "create_",
    "resolve_",
    "close_",
    "enable_",
    "reset_",
    "resume_",
    "refuel_",
    "toggle_",
    "reboot_",
    "reseat_",
    "set_budget_",
)


@dataclass(frozen=True)
class VisibleOperation:
    operation_id: str
    ordinal: int
    action: str
    intent: str
    phase: str
    repeat_state: str
    target: str


def target_parts(target: str) -> tuple[str, ...]:
    """Recover visible tool names from ordinary and combined target strings."""
    cleaned = target.lower().replace("tool_call_begin-", "+")
    raw = re.split(r"\+|tool_sep", cleaned)
    parts = []
    for item in raw:
        item = item.strip(" :-_")
        if not item or item in {"purpose", "to", "url", "tool_call_end"}:
            continue
        parts.append(item)
    return tuple(parts) or (target.lower(),)


def any_exact(parts: tuple[str, ...], values: set[str]) -> bool:
    return any(part in values for part in parts)


def any_contains(parts: tuple[str, ...], needles: tuple[str, ...]) -> bool:
    return any(needle in part for part in parts for needle in needles)


def root_for(family: str, intent: str) -> str:
    return ROOTS.get((family, intent), "Complete assigned task")


def completion_name(family: str) -> str:
    if family in RESEARCH_FAMILIES:
        return "Deliver supported answer"
    if family == SUPPORT_FAMILY:
        return "Complete customer interaction"
    return "Report task completion"


def reasoning_name(family: str, phase: str) -> str:
    if phase == "open":
        return "Understand request"
    if family in RESEARCH_FAMILIES:
        return "Synthesize gathered evidence"
    if family == SUPPORT_FAMILY:
        return "Work through resolution with customer"
    return "Assess workflow progress"


def tool_stage(family: str, intent: str, target: str) -> str:
    parts = target_parts(target)

    if any_exact(parts, ESCALATION):
        return "Escalate unresolved request"

    if any(part == "search" or part.startswith("search-") for part in parts):
        if family in RESEARCH_FAMILIES:
            return "Gather external evidence"
        return "Search for task information"
    if any(part == "fetch_url" or part.startswith("fetch_url-") for part in parts):
        if family in RESEARCH_FAMILIES:
            return "Gather external evidence"
        return "Inspect external information"

    if intent == "file" and any_exact(parts, WORKSPACE_INSPECTION):
        return "Inspect workspace"
    if intent == "file" and any_exact(parts, FILE_ANALYSIS):
        return "Inspect and analyze files"
    if intent == "file" and any_exact(parts, FILE_MODIFICATION):
        return "Modify files"

    if any_contains(parts, IDENTITY_WORDS):
        return "Identify or authenticate user"
    if any_contains(parts, VERIFY_WORDS):
        return "Verify prerequisites"
    if any_contains(parts, DIAGNOSTIC_WORDS):
        return "Diagnose current state"
    if any_contains(parts, RECORD_WORDS):
        return "Inspect relevant records"
    if any_contains(parts, OPTION_WORDS):
        return "Explore available options"
    if any_contains(parts, COMPUTE_WORDS):
        return "Compute decision inputs"
    if any_exact(parts, VEHICLE_ACTIONS):
        return "Operate vehicle"
    if any_exact(parts, COMMUNICATION_ACTIONS):
        return "Send requested communication"
    if any_contains(parts, ACTION_WORDS):
        if intent == "phone":
            return "Apply service resolution"
        if intent == "flight":
            return "Execute travel action"
        if intent == "info":
            return "Execute order action"
        return "Execute requested action"
    return "Use task-specific tool"


def repeat_name(stage: str, target: str) -> str:
    parts = target_parts(target)
    joined = "+".join(parts)
    if stage == "Understand request":
        return "Continue request analysis"
    if stage == "Synthesize gathered evidence":
        return "Repeat evidence synthesis"
    if stage == "Assess workflow progress":
        return "Reassess workflow"
    if stage == "Work through resolution with customer":
        return "Repeat customer discussion"
    if "search" in joined:
        return "Repeat evidence search"
    if "fetch_url" in joined:
        return "Repeat source inspection"
    if "get_details" in joined:
        return "Repeat record lookup"
    if "startengine" in joined:
        return "Retry vehicle start"
    if stage == "Gather external evidence":
        return "Repeat evidence gathering"
    return "Repeat same operation"


def visible_operations(session: dict[str, Any]) -> list[VisibleOperation]:
    operations = []
    for raw in session["operations"]:
        summary = json.loads(raw["source_summary"])
        allowed = {
            "action",
            "intent",
            "message_index",
            "phase",
            "query_index",
            "repeat_state",
            "target",
        }
        unexpected = set(summary) - allowed
        if unexpected:
            raise ValueError(f"unexpected source-summary fields: {sorted(unexpected)}")
        operations.append(
            VisibleOperation(
                operation_id=raw["operation_id"],
                ordinal=int(raw["ordinal"]),
                action=str(summary["action"]),
                intent=str(summary["intent"]),
                phase=str(summary["phase"]),
                repeat_state=str(summary["repeat_state"]),
                target=str(summary["target"]),
            )
        )
    return operations


def base_stages(family: str, operations: list[VisibleOperation]) -> list[str]:
    stages = []
    for op in operations:
        if op.action == "final_answer" or op.phase == "close":
            stages.append(completion_name(family))
        elif op.action == "reasoning":
            stages.append(reasoning_name(family, op.phase))
        elif op.action == "tool_call":
            stages.append(tool_stage(family, op.intent, op.target))
        else:
            stages.append("Advance assigned task")
    return stages


def normalize_support_investigation(stages: list[str]) -> list[str]:
    """Treat later identity lookups as part of one account-investigation episode.

    Support traces often alternate ``get_customer`` and ``get_*_details`` for
    dozens of turns.  Once record inspection has begun, that alternation is a
    single investigation rather than a sequence of newly invented subtasks.
    The first identity step remains visible.
    """
    result = list(stages)
    investigation_started = False
    for index, stage in enumerate(stages):
        if stage == "Inspect relevant records":
            investigation_started = True
            result[index] = "Investigate customer and records"
        elif stage == "Identify or authenticate user" and investigation_started:
            result[index] = "Investigate customer and records"
    return result


def contract_incidental_reasoning(
    family: str, operations: list[VisibleOperation], stages: list[str]
) -> list[str]:
    """Keep isolated thought turns inside a stable surrounding work episode."""
    if len(stages) < 3:
        return stages
    result = list(stages)
    for index in range(1, len(stages) - 1):
        op = operations[index]
        if op.action != "reasoning" or op.phase == "open":
            continue
        if stages[index - 1] == stages[index + 1]:
            result[index] = stages[index - 1]
        elif (
            family in RESEARCH_FAMILIES
            and stages[index - 1] == "Gather external evidence"
            and stages[index + 1] == "Gather external evidence"
        ):
            result[index] = "Gather external evidence"
    return result


def repeated_run_paths(
    root: str, operations: list[VisibleOperation], stages: list[str]
) -> list[list[str]]:
    paths = [[root, stage] for stage in stages]
    start = 0
    while start < len(operations):
        end = start + 1
        while end < len(operations) and operations[end].target == operations[start].target:
            end += 1
        run = operations[start:end]
        sustained = len(run) >= 3 and any(op.repeat_state == "same-action-run" for op in run[1:])
        if sustained:
            # The first operation is the initial attempt; the repeated episode
            # begins with the second consecutive attempt.
            repeated = repeat_name(stages[start], operations[start].target)
            for index in range(start + 1, end):
                paths[index] = [root, stages[start], repeated]
        start = end
    return paths


def sparse_marks(
    root: str, operations: list[VisibleOperation], paths: list[list[str]]
) -> list[dict[str, Any]]:
    marks = []
    previous: list[str] | None = None
    for op, path in zip(operations, paths, strict=True):
        if path != previous:
            marks.append({"start_operation_id": op.operation_id, "semantic_path": path})
            previous = path
    if not marks or marks[0]["start_operation_id"] != operations[0].operation_id:
        raise AssertionError(f"missing first mark for {operations[0].operation_id}")
    return marks


def findings_for(
    operations: list[VisibleOperation], marks: list[dict[str, Any]]
) -> list[str]:
    segment_lengths = []
    positions = {op.operation_id: index for index, op in enumerate(operations)}
    for index, mark in enumerate(marks):
        begin = positions[mark["start_operation_id"]]
        end = positions[marks[index + 1]["start_operation_id"]] if index + 1 < len(marks) else len(operations)
        segment_lengths.append((end - begin, mark["semantic_path"]))

    findings = []
    longest_length, longest_path = max(segment_lengths, key=lambda item: item[0])
    findings.append(
        f"The longest semantic episode was '{longest_path[-1]}' ({longest_length} operations)."
    )

    repeated = [(length, path[-1]) for length, path in segment_lengths if "Repeat" in path[-1] or "Retry" in path[-1]]
    if repeated:
        total = sum(length for length, _ in repeated)
        labels = ", ".join(dict.fromkeys(label for _, label in repeated))
        findings.append(f"Repeated or recovery work occupied {total} operations: {labels}.")

    leaf_sequence = [mark["semantic_path"][-1] for mark in marks]
    seen = set()
    returns = []
    previous = None
    for leaf in leaf_sequence:
        if leaf in seen and leaf != previous and leaf not in returns:
            returns.append(leaf)
        seen.add(leaf)
        previous = leaf
    if returns:
        findings.append("The workflow returned to earlier work: " + ", ".join(returns) + ".")

    if any("Escalate" in leaf for leaf in leaf_sequence):
        findings.append("The session escalated to human support before completion.")
    elif leaf_sequence[-1] in {
        "Deliver supported answer",
        "Complete customer interaction",
        "Report task completion",
    }:
        findings.append(f"The session ended with '{leaf_sequence[-1]}'.")
    else:
        findings.append("The visible trace ended without an explicit completion operation.")
    return findings[:4]


def annotate_session(session: dict[str, Any]) -> dict[str, Any]:
    operations = visible_operations(session)
    if not operations:
        raise ValueError(f"empty session {session['sequence']}")
    if [op.ordinal for op in operations] != list(range(len(operations))):
        raise ValueError(f"non-contiguous ordinals in {session['sequence']}")
    family = str(session["task_family"])
    intent = operations[0].intent
    root = root_for(family, intent)
    stages = base_stages(family, operations)
    if family == SUPPORT_FAMILY:
        stages = normalize_support_investigation(stages)
    stages = contract_incidental_reasoning(family, operations, stages)
    paths = repeated_run_paths(root, operations, stages)
    marks = sparse_marks(root, operations, paths)
    return {
        "sequence": session["sequence"],
        "marks": marks,
        "findings": findings_for(operations, marks),
    }


def validate_batch(source: dict[str, Any], output: dict[str, Any]) -> tuple[int, int, int]:
    if set(output) != {"batch", "sessions"}:
        raise AssertionError("output must have exactly batch and sessions")
    source_sessions = {session["sequence"]: session for session in source["sessions"]}
    if len(output["sessions"]) != len(source_sessions):
        raise AssertionError("session coverage mismatch")
    operation_count = 0
    mark_count = 0
    for annotated in output["sessions"]:
        if set(annotated) != {"sequence", "marks", "findings"}:
            raise AssertionError("session output has unexpected keys")
        source_session = source_sessions.pop(annotated["sequence"])
        operations = source_session["operations"]
        operation_ids = [op["operation_id"] for op in operations]
        positions = {operation_id: index for index, operation_id in enumerate(operation_ids)}
        marks = annotated["marks"]
        if not marks or marks[0]["start_operation_id"] != operation_ids[0]:
            raise AssertionError(f"invalid first mark in {annotated['sequence']}")
        mark_positions = []
        previous_path = None
        for mark in marks:
            if set(mark) != {"start_operation_id", "semantic_path"}:
                raise AssertionError("mark has unexpected keys")
            path = mark["semantic_path"]
            if not path or not all(isinstance(frame, str) and frame for frame in path):
                raise AssertionError("empty semantic path")
            if path == previous_path:
                raise AssertionError("redundant adjacent mark")
            previous_path = path
            try:
                mark_positions.append(positions[mark["start_operation_id"]])
            except KeyError as error:
                raise AssertionError("mark references unknown operation") from error
        if mark_positions != sorted(set(mark_positions)):
            raise AssertionError("marks are not strictly ordered")
        operation_count += len(operations)
        mark_count += len(marks)
    if source_sessions:
        raise AssertionError("missing source sessions")
    return len(output["sessions"]), operation_count, mark_count


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--packet-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()

    packet_paths = sorted(args.packet_dir.glob("batch-*.json"))
    if not packet_paths:
        raise SystemExit("no packet files found")
    args.output_dir.mkdir(parents=True, exist_ok=True)

    total_sessions = 0
    total_operations = 0
    total_marks = 0
    roots: Counter[str] = Counter()
    for packet_path in packet_paths:
        source = json.loads(packet_path.read_text())
        annotated_sessions = [annotate_session(session) for session in source["sessions"]]
        for session in annotated_sessions:
            roots[session["marks"][0]["semantic_path"][0]] += 1
        output = {"batch": packet_path.stem, "sessions": annotated_sessions}
        sessions, operations, marks = validate_batch(source, output)
        output_path = args.output_dir / packet_path.name
        output_path.write_text(json.dumps(output, indent=2, ensure_ascii=False) + "\n")
        total_sessions += sessions
        total_operations += operations
        total_marks += marks

    summary = {
        "packet_files": len(packet_paths),
        "sessions": total_sessions,
        "operations": total_operations,
        "marks": total_marks,
        "marks_per_operation": total_marks / total_operations,
        "roots": dict(sorted(roots.items())),
    }
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
