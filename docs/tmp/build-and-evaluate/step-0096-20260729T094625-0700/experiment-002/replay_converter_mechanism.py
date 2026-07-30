#!/usr/bin/env python3
"""Replay every profiled ToolSandbox operation from its exact recorded pre-state.

The two arms differ only in the Python source generated for the operation:

* BEFORE passes the original opaque protocol ID to ToolSandbox's official
  ``openai_tool_call_to_python_code`` converter.
* AFTER passes a deterministic safe internal variable name to the same official
  converter while retaining the original protocol ID in the ToolSandbox
  message.

No model is called. This is a mechanism replay, so it reports converter and
execution equivalence only; it does not report token or scenario outcome
effects.
"""

from __future__ import annotations

import ast
import copy
import datetime
import hashlib
import json
from contextlib import ExitStack
from pathlib import Path
import re
from typing import Any
from unittest.mock import patch
import uuid

from openai.types.chat.chat_completion_message_tool_call import (
    ChatCompletionMessageToolCall,
)
from tool_sandbox.common.execution_context import (
    DatabaseNamespace,
    ExecutionContext,
    RoleType,
    get_current_context,
    set_current_context,
)
from tool_sandbox.common.message_conversion import (
    openai_tool_call_to_python_code,
)
from tool_sandbox.roles.execution_environment import ExecutionEnvironment

from run_toolsandbox_compatible import safe_execution_python_code


HERE = Path(__file__).resolve().parent
PROFILE_OPERATIONS = HERE / "before-profile-operations.jsonl"
EPISODES = HERE / "episodes-compatible" / "no-policy"
RESULTS = HERE / "converter-replay-results.json"
SUMMARY = HERE / "converter-replay-summary.json"
IDENTIFIER = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
STATE_NAMESPACES = tuple(
    namespace
    for namespace in DatabaseNamespace
    if namespace != DatabaseNamespace.SANDBOX
)


class FixedDateTime(datetime.datetime):
    """Datetime subclass whose ``now`` value is assigned per replay."""

    timestamp_value = 0.0

    @classmethod
    def now(cls, tz: datetime.tzinfo | None = None) -> FixedDateTime:
        return cls.fromtimestamp(cls.timestamp_value, tz=tz)


def canonical_hash(value: Any) -> str:
    payload = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def load_profile_rows() -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in PROFILE_OPERATIONS.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def trim_serialized_context(
    serialized: dict[str, Any],
    sandbox_message_index: int,
) -> dict[str, Any]:
    """Keep exactly the recorded history available when an operation executed."""

    trimmed = copy.deepcopy(serialized)
    trimmed["interactive_console"] = None
    trimmed["_dbs"] = {
        namespace: [
            row
            for row in rows
            if int(row["sandbox_message_index"]) <= sandbox_message_index
        ]
        for namespace, rows in serialized["_dbs"].items()
    }
    return trimmed


def current_state(context: ExecutionContext) -> dict[str, list[dict[str, Any]]]:
    return {
        str(namespace): context.get_database(namespace).to_dicts()
        for namespace in STATE_NAMESPACES
    }


def state_at(
    serialized: dict[str, Any],
    sandbox_message_index: int,
) -> dict[str, list[dict[str, Any]]]:
    context = ExecutionContext.from_dict(
        {**copy.deepcopy(serialized), "interactive_console": None}
    )
    return {
        str(namespace): context.get_database(
            namespace,
            sandbox_message_index=sandbox_message_index,
        ).to_dicts()
        for namespace in STATE_NAMESPACES
    }


def response_projection(row: dict[str, Any]) -> dict[str, Any]:
    return {
        key: row.get(key)
        for key in (
            "content",
            "openai_tool_call_id",
            "openai_function_name",
            "tool_call_exception",
            "tool_trace",
        )
    }


def parse_literal(content: str | None) -> Any:
    if content is None:
        return None
    try:
        return ast.literal_eval(content)
    except (SyntaxError, ValueError):
        return None


def fixed_timestamp_for(
    tool_name: str,
    response: dict[str, Any],
    recorded_post_state: dict[str, list[dict[str, Any]]],
    pre_state: dict[str, list[dict[str, Any]]],
) -> float:
    """Recover recorded nondeterministic time or choose a stable same-arm anchor."""

    literal = parse_literal(response.get("content"))
    if tool_name == "get_current_timestamp" and isinstance(literal, (int, float)):
        return float(literal)
    id_to_namespace = {
        "add_reminder": ("REMINDER", "reminder_id"),
        "send_message_with_phone_number": ("MESSAGING", "message_id"),
    }
    if tool_name in id_to_namespace and isinstance(literal, str):
        namespace, id_column = id_to_namespace[tool_name]
        for row in recorded_post_state[namespace]:
            if row[id_column] == literal:
                return float(row["creation_timestamp"])
    candidates = []
    for rows in pre_state.values():
        for row in rows:
            for key in ("creation_timestamp", "reminder_timestamp"):
                if isinstance(row.get(key), (int, float)):
                    candidates.append(float(row[key]))
    return max(candidates, default=1785344400.0)


def fixed_uuid_for(
    evidence_id: str,
    response: dict[str, Any],
) -> uuid.UUID:
    literal = parse_literal(response.get("content"))
    if isinstance(literal, str):
        try:
            return uuid.UUID(literal)
        except ValueError:
            pass
    return uuid.uuid5(uuid.NAMESPACE_URL, f"agentsight-replay:{evidence_id}")


def deterministic_execution(
    serialized: dict[str, Any],
    operation_index: int,
    execution_code: str,
    protocol_id: str,
    tool_name: str,
    fixed_timestamp: float,
    fixed_uuid: uuid.UUID,
) -> tuple[dict[str, Any], dict[str, list[dict[str, Any]]]]:
    """Fork a context, initialize its official console, and execute one message."""

    branch = trim_serialized_context(serialized, operation_index)
    # A single model response can contain parallel tool calls. The replay unit
    # is one operation, so retain the selected call but remove its still-pending
    # siblings from the tail of the message history. Completed earlier calls
    # remain because their execution-environment responses delimit the tail.
    sandbox_rows = branch["_dbs"]["SANDBOX"]
    last_completed_position = max(
        (
            position
            for position, row in enumerate(sandbox_rows)
            if row.get("sender") is not None
            and not (
                row.get("sender") == "AGENT"
                and row.get("recipient") == "EXECUTION_ENVIRONMENT"
            )
        ),
        default=-1,
    )
    branch["_dbs"]["SANDBOX"] = [
        row
        for position, row in enumerate(sandbox_rows)
        if not (
            position > last_completed_position
            and row.get("sender") == "AGENT"
            and row.get("recipient") == "EXECUTION_ENVIRONMENT"
            and row.get("openai_tool_call_id") != protocol_id
        )
    ]
    for row in branch["_dbs"]["SANDBOX"]:
        if (
            int(row["sandbox_message_index"]) == operation_index
            and row.get("sender") == "AGENT"
            and row.get("recipient") == "EXECUTION_ENVIRONMENT"
            and row.get("openai_tool_call_id") == protocol_id
        ):
            row["content"] = execution_code
            break
    else:
        raise AssertionError(f"operation message not found at index {operation_index}")

    context = ExecutionContext.from_dict(branch)
    set_current_context(context)
    environment = ExecutionEnvironment()
    FixedDateTime.timestamp_value = fixed_timestamp
    with ExitStack() as stack:
        # ToolSandbox imports uuid4 into each mutating tool module and imports
        # the datetime module in its time-sensitive tool modules. Both arms
        # receive the same recovered values; valid controls therefore reproduce
        # the original trajectory despite UUID/time nondeterminism.
        stack.enter_context(
            patch("tool_sandbox.tools.contact.uuid4", return_value=fixed_uuid)
        )
        stack.enter_context(
            patch("tool_sandbox.tools.reminder.uuid4", return_value=fixed_uuid)
        )
        stack.enter_context(
            patch("tool_sandbox.tools.messaging.uuid4", return_value=fixed_uuid)
        )
        stack.enter_context(
            patch("tool_sandbox.tools.utilities.datetime.datetime", FixedDateTime)
        )
        # The serialized artifact intentionally omits the live console. Replay
        # the recorded official SYSTEM -> EXECUTION_ENVIRONMENT import message.
        environment.respond(ending_index=0)
        environment.respond(ending_index=operation_index)

    # The official parallel-call implementation may switch the context to a
    # deep-copied result branch. Always use the authoritative current context.
    context = get_current_context()
    sandbox = context.get_database(
        DatabaseNamespace.SANDBOX,
        get_all_history_snapshots=True,
        drop_sandbox_message_index=False,
    ).to_dicts()
    response_rows = [
        row
        for row in sandbox
        if int(row["sandbox_message_index"]) > operation_index
        and row.get("sender") == RoleType.EXECUTION_ENVIRONMENT
        and row.get("recipient") == RoleType.AGENT
        and row.get("openai_tool_call_id") == protocol_id
    ]
    if len(response_rows) != 1:
        raise AssertionError(
            f"expected one response for {protocol_id}, found {len(response_rows)}"
        )
    return response_projection(response_rows[0]), current_state(context)


def episode_context_path(source_session: str, scenario: str) -> Path:
    prefix = "toolsandbox-before-"
    if not source_session.startswith(prefix):
        raise AssertionError(f"unexpected source session: {source_session}")
    seed = source_session[len(prefix) :].split("-", 1)[0]
    path = (
        EPISODES
        / f"seed-{seed}"
        / scenario
        / "trajectories"
        / scenario
        / "execution_context.json"
    )
    if not path.is_file():
        raise FileNotFoundError(path)
    return path


def conversation_calls(path: Path) -> list[dict[str, Any]]:
    conversation = json.loads(
        path.with_name("conversation.json").read_text(encoding="utf-8")
    )
    calls = []
    for message in conversation:
        if message.get("role") != "assistant":
            continue
        for call_index, call in enumerate(message.get("tool_calls") or []):
            calls.append({"call_index": call_index, "call": call})
    return calls


def find_recorded_response(
    sandbox: list[dict[str, Any]],
    operation_index: int,
    protocol_id: str,
) -> dict[str, Any]:
    rows = [
        row
        for row in sandbox
        if int(row["sandbox_message_index"]) > operation_index
        and row.get("sender") == "EXECUTION_ENVIRONMENT"
        and row.get("recipient") == "AGENT"
        and row.get("openai_tool_call_id") == protocol_id
    ]
    if len(rows) != 1:
        raise AssertionError(
            f"expected one recorded response for {protocol_id}, found {len(rows)}"
        )
    return rows[0]


def run() -> dict[str, Any]:
    profile_rows = load_profile_rows()
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in profile_rows:
        grouped.setdefault(row["fields"]["scenario"], []).append(row)

    operation_results = []
    for scenario_rows in grouped.values():
        fields0 = scenario_rows[0]["fields"]
        scenario = fields0["scenario"]
        context_path = episode_context_path(fields0["source_session"], scenario)
        serialized = json.loads(context_path.read_text(encoding="utf-8"))
        sandbox = serialized["_dbs"]["SANDBOX"]
        agent_rows = [
            row
            for row in sandbox
            if row.get("sender") == "AGENT"
            and row.get("recipient") == "EXECUTION_ENVIRONMENT"
            and row.get("openai_function_name")
        ]
        calls = conversation_calls(context_path)
        if len(agent_rows) != len(scenario_rows) or len(calls) != len(scenario_rows):
            raise AssertionError(
                f"{scenario}: profile={len(scenario_rows)}, "
                f"context={len(agent_rows)}, conversation={len(calls)}"
            )

        for profile_row, agent_row, call_record in zip(
            scenario_rows, agent_rows, calls
        ):
            fields = profile_row["fields"]
            raw_call = call_record["call"]
            call = ChatCompletionMessageToolCall(**raw_call)
            protocol_id = str(call.id)
            tool_name = call.function.name
            arguments = json.loads(call.function.arguments)
            expected_arguments = json.loads(fields["arguments"])
            if tool_name != fields["tool"] or arguments != expected_arguments:
                raise AssertionError(f"{fields['evidence_id']}: call/profile mismatch")
            if agent_row.get("openai_tool_call_id") != protocol_id:
                raise AssertionError(f"{fields['evidence_id']}: protocol ID mismatch")
            expected_id_class = (
                "valid" if IDENTIFIER.fullmatch(protocol_id) else "invalid"
            )
            if expected_id_class != fields["call_id"]:
                raise AssertionError(f"{fields['evidence_id']}: ID class mismatch")

            operation_index = int(agent_row["sandbox_message_index"])
            pre_state = state_at(serialized, operation_index)
            recorded_response_row = find_recorded_response(
                sandbox, operation_index, protocol_id
            )
            recorded_response = response_projection(recorded_response_row)
            response_index = int(recorded_response_row["sandbox_message_index"])
            recorded_post_state = state_at(serialized, response_index)

            context_for_names = ExecutionContext.from_dict(
                trim_serialized_context(serialized, operation_index)
            )
            available_tool_names = set(
                context_for_names.get_available_tools(scrambling_allowed=True)
            )
            execution_tool_name = (
                context_for_names.get_execution_facing_tool_name(tool_name)
            )
            before_code = openai_tool_call_to_python_code(
                call,
                available_tool_names,
                execution_facing_tool_name=execution_tool_name,
            )
            if before_code != agent_row["content"]:
                raise AssertionError(
                    f"{fields['evidence_id']}: recorded code is not official "
                    "converter output"
                )
            after_code = safe_execution_python_code(
                call,
                available_tool_names,
                execution_tool_name,
                call_record["call_index"],
            )
            compile(after_code, f"<after:{fields['evidence_id']}>", "exec")

            fixed_timestamp = fixed_timestamp_for(
                tool_name, recorded_response, recorded_post_state, pre_state
            )
            fixed_uuid = fixed_uuid_for(fields["evidence_id"], recorded_response)
            before_response, before_state = deterministic_execution(
                serialized,
                operation_index,
                before_code,
                protocol_id,
                tool_name,
                fixed_timestamp,
                fixed_uuid,
            )
            after_response, after_state = deterministic_execution(
                serialized,
                operation_index,
                after_code,
                protocol_id,
                tool_name,
                fixed_timestamp,
                fixed_uuid,
            )

            input_invalid = expected_id_class == "invalid"
            before_invalid_decimal = "SyntaxError: invalid decimal literal" in str(
                before_response.get("tool_call_exception") or ""
            )
            after_invalid_decimal = "SyntaxError: invalid decimal literal" in str(
                after_response.get("tool_call_exception") or ""
            )
            before_matches_recorded_response = before_response == recorded_response
            before_matches_recorded_state = before_state == recorded_post_state
            protocol_preserved_after = (
                after_response.get("openai_tool_call_id") == protocol_id
            )
            valid_control_response_equal = (
                None if input_invalid else before_response == after_response
            )
            valid_control_state_equal = (
                None if input_invalid else before_state == after_state
            )
            operation_results.append(
                {
                    "evidence_id": fields["evidence_id"],
                    "scenario": scenario,
                    "source_execution_context": str(context_path.relative_to(HERE)),
                    "operation_ordinal": int(
                        fields["evidence_id"].rsplit("-", 1)[1]
                    ),
                    "sandbox_message_index": operation_index,
                    "protocol_call_id": protocol_id,
                    "input_id_class": expected_id_class,
                    "tool_name": tool_name,
                    "arguments": arguments,
                    "pre_state": {
                        "sha256": canonical_hash(pre_state),
                        "database_snapshots": pre_state,
                    },
                    "deterministic_replay_values": {
                        "timestamp": fixed_timestamp,
                        "uuid": str(fixed_uuid),
                    },
                    "recorded": {
                        "execution_code": agent_row["content"],
                        "response": recorded_response,
                        "post_state_sha256": canonical_hash(recorded_post_state),
                    },
                    "before": {
                        "execution_code": before_code,
                        "response": before_response,
                        "post_state_sha256": canonical_hash(before_state),
                    },
                    "after": {
                        "execution_code": after_code,
                        "response": after_response,
                        "post_state_sha256": canonical_hash(after_state),
                    },
                    "checks": {
                        "before_code_matches_recorded_official_converter": True,
                        "before_response_matches_recorded": (
                            before_matches_recorded_response
                        ),
                        "before_post_state_matches_recorded": (
                            before_matches_recorded_state
                        ),
                        "before_invalid_decimal": before_invalid_decimal,
                        "after_invalid_decimal": after_invalid_decimal,
                        "after_protocol_id_preserved": protocol_preserved_after,
                        "valid_control_response_equal": (
                            valid_control_response_equal
                        ),
                        "valid_control_state_equal": valid_control_state_equal,
                    },
                }
            )

    invalid = [row for row in operation_results if row["input_id_class"] == "invalid"]
    valid = [row for row in operation_results if row["input_id_class"] == "valid"]
    validation = {
        "profile_operation_count": len(profile_rows),
        "replayed_operation_count": len(operation_results),
        "invalid_input_id_count": len(invalid),
        "valid_input_id_count": len(valid),
        "before_responses_reproduced": sum(
            row["checks"]["before_response_matches_recorded"]
            for row in operation_results
        ),
        "before_post_states_reproduced": sum(
            row["checks"]["before_post_state_matches_recorded"]
            for row in operation_results
        ),
        "before_invalid_decimal_failures": sum(
            row["checks"]["before_invalid_decimal"] for row in operation_results
        ),
        "after_invalid_decimal_failures": sum(
            row["checks"]["after_invalid_decimal"] for row in operation_results
        ),
        "invalid_decimal_failures_eliminated": sum(
            row["checks"]["before_invalid_decimal"]
            and not row["checks"]["after_invalid_decimal"]
            for row in invalid
        ),
        "after_protocol_ids_preserved": sum(
            row["checks"]["after_protocol_id_preserved"]
            for row in operation_results
        ),
        "valid_control_responses_equal": sum(
            bool(row["checks"]["valid_control_response_equal"]) for row in valid
        ),
        "valid_control_post_states_equal": sum(
            bool(row["checks"]["valid_control_state_equal"]) for row in valid
        ),
    }
    required = {
        "all_profile_operations_replayed": (
            validation["profile_operation_count"]
            == validation["replayed_operation_count"]
            == 21
        ),
        "input_population_is_5_invalid_16_valid": (
            validation["invalid_input_id_count"] == 5
            and validation["valid_input_id_count"] == 16
        ),
        "exact_pre_state_recovery_supported": (
            validation["before_responses_reproduced"] == 21
            and validation["before_post_states_reproduced"] == 21
        ),
        "all_invalid_decimal_failures_eliminated": (
            validation["before_invalid_decimal_failures"] == 5
            and validation["after_invalid_decimal_failures"] == 0
            and validation["invalid_decimal_failures_eliminated"] == 5
        ),
        "all_protocol_ids_preserved": (
            validation["after_protocol_ids_preserved"] == 21
        ),
        "all_valid_control_responses_equal": (
            validation["valid_control_responses_equal"] == 16
        ),
        "all_valid_control_post_states_equal": (
            validation["valid_control_post_states_equal"] == 16
        ),
    }
    result = {
        "schema": "agentsight.toolsandbox-converter-mechanism-replay.v1",
        "scope": (
            "converter/execution mechanism only; no model call, token claim, "
            "or scenario-outcome claim"
        ),
        "source_population": (
            "all 21 agent tool operations from the eight no-policy episodes "
            "that formed before-profile.pb.gz; no operation excluded"
        ),
        "method": {
            "pre_state": (
                "versioned execution_context.json databases truncated at the "
                "recorded operation sandbox_message_index"
            ),
            "before": (
                "official openai_tool_call_to_python_code with original opaque ID"
            ),
            "after": (
                "official openai_tool_call_to_python_code with only a "
                "deterministic safe internal variable; original protocol ID retained"
            ),
            "execution": "official ToolSandbox ExecutionEnvironment",
            "nondeterminism_control": (
                "both arms use the same recorded time/UUID for valid operations; "
                "BEFORE must reproduce the recorded response and post-state"
            ),
        },
        "validation": validation,
        "required_checks": required,
        "operations": operation_results,
    }
    if not all(required.values()):
        failed = [name for name, passed in required.items() if not passed]
        raise AssertionError(f"mechanism replay failed: {failed}")
    return result


def main() -> int:
    result = run()
    RESULTS.write_text(
        json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    summary = {
        "schema": "agentsight.toolsandbox-converter-mechanism-replay-summary.v1",
        "scope": result["scope"],
        "source_population": result["source_population"],
        "validation": result["validation"],
        "required_checks": result["required_checks"],
        "results_path": str(RESULTS.relative_to(HERE)),
    }
    SUMMARY.write_text(
        json.dumps(summary, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
