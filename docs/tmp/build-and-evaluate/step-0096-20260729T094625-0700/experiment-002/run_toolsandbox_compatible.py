#!/usr/bin/env python3
"""Run the official ToolSandbox evaluator through a Qwen chat-template adapter."""

from __future__ import annotations

import json
import hashlib
import copy
from pathlib import Path
import re
import sys
from typing import Any

from openai import NOT_GIVEN
from requests.exceptions import HTTPError
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_random_exponential,
)


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[4]
SOURCE = (
    REPO
    / "docs/tmp/build-and-evaluate/step-0095-20260729T024929-0700"
    / "experiment-001"
)
sys.path.insert(0, str(SOURCE))
import run_toolsandbox as base  # noqa: E402
from tool_sandbox.common.execution_context import (  # noqa: E402
    RoleType,
    get_current_context,
)
from tool_sandbox.common.message_conversion import (  # noqa: E402
    Message,
    openai_tool_call_to_python_code,
    to_openai_messages,
)
from tool_sandbox.common.tool_conversion import convert_to_openai_tools  # noqa: E402


VALID_TOOL_CALL_ID = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def system_first(messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Merge system messages at position zero as required by Qwen's template."""

    systems = [
        str(message.get("content") or "")
        for message in messages
        if message.get("role") == "system"
    ]
    non_system = [
        message.copy() for message in messages if message.get("role") != "system"
    ]
    if not systems:
        return non_system
    return [
        {
            "role": "system",
            "content": "\n\n".join(systems),
        },
        *non_system,
    ]


def safe_tool_call_id(original: str) -> str:
    """Return a deterministic, unique Python-identifier-compatible opaque ID."""

    if VALID_TOOL_CALL_ID.fullmatch(original):
        return original
    digest = hashlib.sha256(original.encode("utf-8")).hexdigest()[:24]
    return f"call_{digest}"


def count_invalid_response_tool_call_ids(response: Any) -> int:
    choices = getattr(response, "choices", None) or []
    if not choices:
        return 0
    message = getattr(choices[0], "message", None)
    calls = getattr(message, "tool_calls", None) or []
    return sum(
        not bool(VALID_TOOL_CALL_ID.fullmatch(str(call.id))) for call in calls
    )


def normalize_response_tool_call_ids(response: Any) -> int:
    choices = getattr(response, "choices", None) or []
    if not choices:
        return 0
    message = getattr(choices[0], "message", None)
    calls = getattr(message, "tool_calls", None) or []
    changed = 0
    observed = set()
    for index, call in enumerate(calls):
        original = str(call.id)
        normalized = safe_tool_call_id(original)
        while normalized in observed:
            normalized = f"{normalized}_{index}"
        observed.add(normalized)
        if normalized != original:
            call.id = normalized
            changed += 1
    return changed


def safe_execution_python_code(
    tool_call: Any,
    available_tool_names: set[str],
    execution_facing_tool_name: str | None,
    call_index: int,
) -> str:
    """Build executable code without using an opaque protocol ID as an identifier."""

    executable_call = copy.deepcopy(tool_call)
    executable_call.id = f"{safe_tool_call_id(str(tool_call.id))}_{call_index}"
    return openai_tool_call_to_python_code(
        executable_call,
        available_tool_names,
        execution_facing_tool_name=execution_facing_tool_name,
    )


def restore_protocol_tool_call_ids(
    openai_messages: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Restore original protocol IDs hidden behind safe execution variables."""

    restored = copy.deepcopy(openai_messages)
    for index, message in enumerate(restored):
        calls = message.get("tool_calls") or []
        if message.get("role") != "assistant" or not calls:
            continue
        result_ids = []
        for following in restored[index + 1 :]:
            if following.get("role") != "tool":
                break
            result_ids.append(str(following.get("tool_call_id") or ""))
        if len(result_ids) < len(calls):
            continue
        for call, original_id in zip(calls, result_ids):
            call["id"] = original_id
    return restored


def protocol_tool_call_id_mismatches(
    openai_messages: list[dict[str, Any]],
) -> int:
    mismatches = 0
    for index, message in enumerate(openai_messages):
        calls = message.get("tool_calls") or []
        if message.get("role") != "assistant" or not calls:
            continue
        result_ids = []
        for following in openai_messages[index + 1 :]:
            if following.get("role") != "tool":
                break
            result_ids.append(str(following.get("tool_call_id") or ""))
        if len(result_ids) != len(calls):
            mismatches += abs(len(result_ids) - len(calls))
        mismatches += sum(
            str(call.get("id") or "") != result_id
            for call, result_id in zip(calls, result_ids)
        )
    return mismatches


class CompatibleAgent(base.LocalInstrumentedAgent):
    def respond(self, ending_index: int | None = None) -> None:
        if not getattr(self, "safe_execution_tool_call_ids", False):
            return super().respond(ending_index=ending_index)

        messages = self.get_messages(ending_index=ending_index)
        self.messages_validation(messages=messages)
        messages = self.filter_messages(messages=messages)
        if messages[-1].sender == RoleType.SYSTEM:
            return
        available_tools = self.get_available_tools()
        available_tool_names = set(available_tools)
        openai_tools = (
            convert_to_openai_tools(available_tools)
            if messages[-1].sender
            in (RoleType.USER, RoleType.EXECUTION_ENVIRONMENT)
            else NOT_GIVEN
        )
        openai_messages, _ = to_openai_messages(messages)
        response = self.model_inference(
            openai_messages=openai_messages,
            openai_tools=openai_tools,
        )
        response_message = response.choices[0].message
        if response_message.tool_calls is None:
            assert response_message.content is not None
            response_messages = [
                Message(
                    sender=self.role_type,
                    recipient=RoleType.USER,
                    content=response_message.content,
                )
            ]
        else:
            assert openai_tools is not NOT_GIVEN
            current_context = get_current_context()
            response_messages = []
            for call_index, tool_call in enumerate(response_message.tool_calls):
                execution_name = current_context.get_execution_facing_tool_name(
                    tool_call.function.name
                )
                response_messages.append(
                    Message(
                        sender=self.role_type,
                        recipient=RoleType.EXECUTION_ENVIRONMENT,
                        content=safe_execution_python_code(
                            tool_call,
                            available_tool_names,
                            execution_name,
                            call_index,
                        ),
                        openai_tool_call_id=tool_call.id,
                        openai_function_name=tool_call.function.name,
                    )
                )
        self.add_messages(response_messages)

    @retry(
        wait=wait_random_exponential(multiplier=1, max=40),
        stop=stop_after_attempt(3),
        retry=retry_if_exception_type(HTTPError),
    )
    def model_inference(
        self, openai_messages: list[dict[str, Any]], openai_tools: Any
    ) -> Any:
        with_policy = base.append_policy_to_system_input(
            openai_messages, self.policy
        )
        if getattr(self, "safe_execution_tool_call_ids", False):
            with_policy = restore_protocol_tool_call_ids(with_policy)
        response = self._completion(
            openai_messages=system_first(with_policy),
            openai_tools=openai_tools,
        )
        invalid = count_invalid_response_tool_call_ids(response)
        changed = (
            normalize_response_tool_call_ids(response)
            if getattr(self, "sanitize_tool_call_ids", False)
            else 0
        )
        if self.request_records:
            self.request_records[-1]["protocol_history_id_mismatches"] = (
                protocol_tool_call_id_mismatches(with_policy)
            )
            self.request_records[-1]["invalid_response_tool_call_ids"] = invalid
            self.request_records[-1]["normalized_tool_call_ids"] = changed
        return response


class CompatibleUser(base.LocalInstrumentedUser):
    @retry(
        wait=wait_random_exponential(multiplier=1, max=40),
        stop=stop_after_attempt(3),
    )
    def model_inference(
        self, openai_messages: list[dict[str, Any]], openai_tools: Any
    ) -> Any:
        return self._completion(
            openai_messages=system_first(openai_messages),
            openai_tools=openai_tools,
        )


def main() -> int:
    parser = base.build_parser()
    parser.add_argument("--condition-label")
    parser.add_argument("--sanitize-agent-tool-call-ids", action="store_true")
    parser.add_argument("--safe-execution-tool-call-ids", action="store_true")
    args = parser.parse_args()
    if args.sanitize_agent_tool_call_ids and args.safe_execution_tool_call_ids:
        raise SystemExit(
            "choose response-ID normalization or safe execution variables, not both"
        )
    inventory = base.build_inventory(args.checkout)
    if args.list_scenarios:
        print(
            json.dumps(
                {
                    "counts": inventory["counts"],
                    "offline_scenarios": inventory["offline_scenarios"],
                    "rapidapi_scenarios": inventory["rapidapi_scenarios"],
                    "preflight_scenario": base.PREFLIGHT_SCENARIO,
                    "outcome_scenarios": inventory["outcome_scenarios"],
                },
                indent=2,
                ensure_ascii=False,
                sort_keys=True,
            )
        )
        return 0
    required = {
        "--scenario": args.scenario,
        "--condition": args.condition,
        "--trial-seed": args.trial_seed,
    }
    missing = [flag for flag, value in required.items() if value is None]
    if missing:
        raise SystemExit(f"missing required cell arguments: {', '.join(missing)}")
    if args.trial_seed < 0:
        raise SystemExit("--trial-seed must be non-negative")
    sampling = base.SamplingConfig(
        temperature=args.temperature,
        top_p=args.top_p,
        max_tokens=args.max_tokens,
        frequency_penalty=args.frequency_penalty,
        presence_penalty=args.presence_penalty,
    )
    policy, policy_metadata = base.load_policy(args.condition, args.policy_file)
    metadata = base.cell_metadata(
        scenario_name=args.scenario,
        condition=args.condition,
        trial_seed=args.trial_seed,
        base_url=args.base_url,
        model_name=args.model,
        sampling=sampling,
        policy_metadata=policy_metadata,
        inventory=inventory,
    )
    metadata["chat_template_adapter"] = (
        "merge all official system messages in source order at position zero; "
        "identical in both conditions"
    )
    if args.condition_label:
        metadata["condition"] = args.condition_label
    metadata["agent_tool_call_id_adapter"] = {
        "response_id_normalization": bool(args.sanitize_agent_tool_call_ids),
        "safe_execution_variables": bool(args.safe_execution_tool_call_ids),
        "protocol_id_preserved": bool(args.safe_execution_tool_call_ids),
        "rule": (
            "safe execution mode retains the opaque protocol ID and derives only "
            "an internal Python identifier from its SHA-256 digest"
        ),
    }
    if args.dry_run:
        print(json.dumps(metadata, indent=2, ensure_ascii=False, sort_keys=True))
        return 0
    if args.output_directory is None:
        raise SystemExit("--execute requires --output-directory")
    scenario = base._load_scenario(args.checkout, args.scenario, args.trial_seed)
    agent = CompatibleAgent(
        model_name=args.model,
        base_url=args.base_url,
        trial_seed=args.trial_seed,
        sampling=sampling,
        policy=policy,
        api_key=args.api_key,
    )
    agent.sanitize_tool_call_ids = bool(args.sanitize_agent_tool_call_ids)
    agent.safe_execution_tool_call_ids = bool(
        args.safe_execution_tool_call_ids
    )
    user = CompatibleUser(
        model_name=args.model,
        base_url=args.base_url,
        trial_seed=args.trial_seed,
        sampling=sampling,
        api_key=args.api_key,
    )
    record = base.run_episode(
        scenario=scenario,
        metadata=metadata,
        output_directory=args.output_directory,
        agent=agent,
        user=user,
    )
    print(json.dumps(record, ensure_ascii=False, sort_keys=True))
    return 0 if record["status"] == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
