#!/usr/bin/env python3
"""Run one fixed ToolSandbox cell through the unchanged official evaluator.

The command is fail-safe: callers must choose exactly one of ``--list-scenarios``,
``--dry-run``, or ``--execute``.  The first two modes make no model request and
never call ``Scenario.play_and_evaluate``.
"""

from __future__ import annotations

import argparse
import copy
import datetime as dt
import hashlib
import json
import random
import time
import traceback
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence, cast

from openai import NOT_GIVEN, OpenAI
from requests.exceptions import HTTPError
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_random_exponential,
)
from tool_sandbox.common.execution_context import RoleType
from tool_sandbox.common.scenario import Scenario
from tool_sandbox.common.tool_discovery import ToolBackend
from tool_sandbox.roles.execution_environment import ExecutionEnvironment
from tool_sandbox.roles.openai_api_agent import OpenAIAPIAgent
from tool_sandbox.roles.openai_api_user import OpenAIAPIUser

from inventory_toolsandbox import (
    PREFLIGHT_SCENARIO,
    TOOL_SANDBOX_COMMIT,
    build_inventory,
    default_checkout,
)

DEFAULT_BASE_URL = "http://127.0.0.1:18185/v1"
DEFAULT_MODEL = (
    "/home/yunwei37/.cache/huggingface/hub/"
    "models--DevQuasar--Qwen.Qwen3.6-27B-GGUF/snapshots/"
    "b19fa7e8538a1a5f66452eb3b3167e026177be1d/"
    "Qwen.Qwen3.6-27B.f16.gguf.Q4_K_M.gguf"
)
CONDITIONS = ("no-policy", "profile-policy", "raw-policy")
POLICY_SEPARATOR = "\n\nAdditional frozen system policy:\n"


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def derive_request_seed(trial_seed: int, role: str, request_index: int) -> int:
    """Derive a stable signed-31-bit seed shared across conditions."""

    payload = f"{trial_seed}:{role}:{request_index}".encode("utf-8")
    return int.from_bytes(hashlib.sha256(payload).digest()[:8], "big") % (2**31)


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


@dataclass(frozen=True)
class SamplingConfig:
    temperature: float
    top_p: float
    max_tokens: int
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0

    def request_kwargs(self) -> dict[str, Any]:
        return asdict(self)


def _jsonable(value: Any) -> Any:
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, Mapping):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return [_jsonable(item) for item in value]
    if hasattr(value, "model_dump"):
        return _jsonable(value.model_dump())
    if hasattr(value, "__dict__"):
        return {
            str(key): _jsonable(item)
            for key, item in vars(value).items()
            if not str(key).startswith("_")
        }
    return str(value)


def _usage_payload(response: Any) -> dict[str, Any]:
    usage = getattr(response, "usage", None)
    payload = _jsonable(usage)
    return payload if isinstance(payload, dict) else {}


def _response_tool_call_count(response: Any) -> int:
    choices = getattr(response, "choices", None) or []
    if not choices:
        return 0
    message = getattr(choices[0], "message", None)
    tool_calls = getattr(message, "tool_calls", None)
    return len(tool_calls or [])


def append_policy_to_system_input(
    messages: list[dict[str, Any]], policy: str | None
) -> list[dict[str, Any]]:
    """Copy model input and append policy without changing official messages."""

    if policy is None:
        return messages
    system_indices = [
        index for index, message in enumerate(messages) if message.get("role") == "system"
    ]
    if not system_indices:
        raise RuntimeError("official agent input has no system message for policy")
    copied = copy.deepcopy(messages)
    system_index = system_indices[0]
    content = copied[system_index].get("content")
    if not isinstance(content, str):
        raise TypeError("official agent system content is not text")
    copied[system_index]["content"] = content + POLICY_SEPARATOR + policy
    return copied


class _InstrumentedOpenAIRole:
    """Shared request instrumentation; not a ToolSandbox role on its own."""

    telemetry_role: str

    def _configure(
        self,
        *,
        model_name: str,
        base_url: str,
        trial_seed: int,
        sampling: SamplingConfig,
        client: Any | None,
        api_key: str,
    ) -> None:
        self.model_name = model_name
        self.base_url = base_url
        self.trial_seed = trial_seed
        self.sampling = sampling
        # Disable SDK-level hidden retries. The official role-level tenacity retry
        # decorators below remain in force and every actual request is recorded.
        self.openai_client = client or OpenAI(
            base_url=base_url,
            api_key=api_key,
            max_retries=0,
        )
        self.request_records: list[dict[str, Any]] = []

    def _completion(
        self,
        *,
        openai_messages: list[dict[str, Any]],
        openai_tools: Any,
    ) -> Any:
        request_index = len(self.request_records)
        request_seed = derive_request_seed(
            self.trial_seed, self.telemetry_role, request_index
        )
        sampling = self.sampling.request_kwargs()
        record: dict[str, Any] = {
            "request_index": request_index,
            "role": self.telemetry_role,
            "seed": request_seed,
            "sampling": sampling,
            "model": self.model_name,
            "base_url": self.base_url,
            "message_count": len(openai_messages),
            "available_tool_count": (
                None if openai_tools is NOT_GIVEN else len(cast(Sequence[Any], openai_tools))
            ),
            "started_at": utc_now(),
        }
        started = time.monotonic()
        try:
            response = self.openai_client.chat.completions.create(
                model=self.model_name,
                messages=openai_messages,
                tools=openai_tools,
                seed=request_seed,
                **sampling,
            )
            record.update(
                {
                    "status": "ok",
                    "usage": _usage_payload(response),
                    "tool_calls": _response_tool_call_count(response),
                    "exception": None,
                }
            )
            return response
        except Exception as error:
            record.update(
                {
                    "status": "exception",
                    "usage": {},
                    "tool_calls": 0,
                    "exception": {
                        "type": type(error).__name__,
                        "message": str(error),
                        "traceback": traceback.format_exc(),
                    },
                }
            )
            raise
        finally:
            record["finished_at"] = utc_now()
            record["wall_seconds"] = time.monotonic() - started
            self.request_records.append(record)

    def telemetry(self) -> dict[str, Any]:
        token_fields = ("prompt_tokens", "completion_tokens", "total_tokens")
        usage_totals = {
            field: sum(
                int(record.get("usage", {}).get(field, 0) or 0)
                for record in self.request_records
            )
            for field in token_fields
        }
        return {
            "role": self.telemetry_role,
            "model_calls": len(self.request_records),
            "tool_calls": sum(
                int(record.get("tool_calls", 0)) for record in self.request_records
            ),
            "usage": usage_totals,
            "wall_seconds": sum(
                float(record.get("wall_seconds", 0.0))
                for record in self.request_records
            ),
            "requests": self.request_records,
        }


class LocalInstrumentedAgent(_InstrumentedOpenAIRole, OpenAIAPIAgent):
    """Official OpenAI agent with local endpoint, frozen policy, and telemetry."""

    telemetry_role = "agent"

    def __init__(
        self,
        *,
        model_name: str,
        base_url: str,
        trial_seed: int,
        sampling: SamplingConfig,
        policy: str | None,
        client: Any | None = None,
        api_key: str = "local-not-used",
    ) -> None:
        self.policy = policy
        self._configure(
            model_name=model_name,
            base_url=base_url,
            trial_seed=trial_seed,
            sampling=sampling,
            client=client,
            api_key=api_key,
        )

    @retry(
        wait=wait_random_exponential(multiplier=1, max=40),
        stop=stop_after_attempt(3),
        retry=retry_if_exception_type(HTTPError),
    )
    def model_inference(self, openai_messages: list[dict[str, Any]], openai_tools: Any) -> Any:
        model_messages = append_policy_to_system_input(openai_messages, self.policy)
        return self._completion(
            openai_messages=model_messages,
            openai_tools=openai_tools,
        )


class LocalInstrumentedUser(_InstrumentedOpenAIRole, OpenAIAPIUser):
    """Official simulated user with local endpoint and separate telemetry."""

    telemetry_role = "user"

    def __init__(
        self,
        *,
        model_name: str,
        base_url: str,
        trial_seed: int,
        sampling: SamplingConfig,
        client: Any | None = None,
        api_key: str = "local-not-used",
    ) -> None:
        self._configure(
            model_name=model_name,
            base_url=base_url,
            trial_seed=trial_seed,
            sampling=sampling,
            client=client,
            api_key=api_key,
        )

    @retry(
        wait=wait_random_exponential(multiplier=1, max=40),
        stop=stop_after_attempt(3),
    )
    def model_inference(self, openai_messages: list[dict[str, Any]], openai_tools: Any) -> Any:
        return self._completion(
            openai_messages=openai_messages,
            openai_tools=openai_tools,
        )


def load_policy(condition: str, policy_file: Path | None) -> tuple[str | None, dict[str, Any]]:
    if condition not in CONDITIONS:
        raise ValueError(f"unknown condition: {condition}")
    if condition == "no-policy":
        if policy_file is not None:
            raise ValueError("no-policy condition must not receive --policy-file")
        payload = b""
        return None, {
            "file": None,
            "sha256": sha256_bytes(payload),
            "bytes": 0,
            "words": 0,
        }
    if policy_file is None:
        raise ValueError(f"{condition} requires --policy-file")
    payload = policy_file.read_bytes()
    policy = payload.decode("utf-8")
    word_count = len(policy.split())
    if word_count > 60:
        raise ValueError(f"policy exceeds 60 words: {word_count}")
    return policy, {
        "file": str(policy_file.resolve()),
        "sha256": sha256_bytes(payload),
        "bytes": len(payload),
        "words": word_count,
    }


def cell_metadata(
    *,
    scenario_name: str,
    condition: str,
    trial_seed: int,
    base_url: str,
    model_name: str,
    sampling: SamplingConfig,
    policy_metadata: dict[str, Any],
    inventory: dict[str, Any],
) -> dict[str, Any]:
    offline = inventory["offline_scenarios"]
    if scenario_name not in offline:
        raise ValueError(f"scenario is not in dependency-screened offline set: {scenario_name}")
    return {
        "schema": "agentsight.toolsandbox.episode.v1",
        "tool_sandbox_commit": TOOL_SANDBOX_COMMIT,
        "scenario": scenario_name,
        "condition": condition,
        "trial_seed": trial_seed,
        "scenario_construction_seed": trial_seed,
        "request_seed_derivation": "sha256(f'{trial_seed}:{role}:{request_index}') mod 2^31",
        "base_url": base_url,
        "model": model_name,
        "sampling": asdict(sampling),
        "policy": policy_metadata,
        "official_entrypoint": inventory["evaluator_mapping"]["entrypoint"],
        "official_evaluator": inventory["evaluator_mapping"]["evaluator"],
        "inventory_offline_scenarios_sha256": inventory[
            "offline_scenarios_sha256"
        ],
    }


def run_episode(
    *,
    scenario: Scenario,
    metadata: dict[str, Any],
    output_directory: Path,
    agent: LocalInstrumentedAgent,
    user: LocalInstrumentedUser,
) -> dict[str, Any]:
    """Execute exactly one official cell. Tests in this step do not call it."""

    scenario_name = str(metadata["scenario"])
    condition = str(metadata["condition"])
    trial_seed = int(metadata["trial_seed"])
    cell_directory = (
        output_directory
        / condition
        / f"seed-{trial_seed}"
        / scenario_name
    )
    cell_directory.mkdir(parents=True, exist_ok=False)
    record = dict(metadata)
    record.update(
        {
            "status": "running",
            "started_at": utc_now(),
            "evaluation": None,
            "exception": None,
        }
    )
    roles = {
        RoleType.USER: user,
        RoleType.EXECUTION_ENVIRONMENT: ExecutionEnvironment(),
        RoleType.AGENT: agent,
    }
    started = time.monotonic()
    try:
        # This is intentionally the unmodified official entrypoint and evaluator.
        result = scenario.play_and_evaluate(
            roles=roles,
            output_directory=cell_directory,
            scenario_name=scenario_name,
        )
        evaluation = result.evaluation_result
        record["status"] = "ok"
        record["evaluation"] = {
            "similarity": evaluation.similarity,
            "milestone_similarity": evaluation.milestone_similarity,
            "minefield_similarity": evaluation.minefield_similarity,
            "turn_count": evaluation.turn_count,
            "milestone_mapping": _jsonable(evaluation.milestone_mapping),
            "minefield_mapping": _jsonable(evaluation.minefield_mapping),
        }
    except Exception as error:
        record["status"] = "exception"
        record["exception"] = {
            "type": type(error).__name__,
            "message": str(error),
            "traceback": traceback.format_exc(),
        }
    finally:
        record["finished_at"] = utc_now()
        record["wall_seconds"] = time.monotonic() - started
        record["agent"] = agent.telemetry()
        record["user"] = user.telemetry()
        for role in roles.values():
            role.teardown()
        (cell_directory / "episode.json").write_text(
            json.dumps(record, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    return record


def _load_scenario(checkout: Path, scenario_name: str, trial_seed: int) -> Scenario:
    # named_scenarios shuffles declared tool lists. Re-seeding before construction
    # makes this official behavior identical for all conditions of a trial.
    random.seed(trial_seed)
    from tool_sandbox.scenarios import named_scenarios

    return named_scenarios(
        preferred_tool_backend=ToolBackend.DEFAULT
    )[scenario_name]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--list-scenarios", action="store_true")
    action.add_argument("--dry-run", action="store_true")
    action.add_argument("--execute", action="store_true")
    parser.add_argument("--checkout", type=Path, default=default_checkout())
    parser.add_argument("--scenario")
    parser.add_argument("--condition", choices=CONDITIONS)
    parser.add_argument("--trial-seed", type=int)
    parser.add_argument("--policy-file", type=Path)
    parser.add_argument("--output-directory", type=Path)
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--top-p", type=float, default=1.0)
    parser.add_argument("--max-tokens", type=int, default=2048)
    parser.add_argument("--frequency-penalty", type=float, default=0.0)
    parser.add_argument("--presence-penalty", type=float, default=0.0)
    parser.add_argument("--api-key", default="local-not-used")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    inventory = build_inventory(args.checkout)
    if args.list_scenarios:
        print(
            json.dumps(
                {
                    "counts": inventory["counts"],
                    "offline_scenarios": inventory["offline_scenarios"],
                    "rapidapi_scenarios": inventory["rapidapi_scenarios"],
                    "preflight_scenario": PREFLIGHT_SCENARIO,
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

    sampling = SamplingConfig(
        temperature=args.temperature,
        top_p=args.top_p,
        max_tokens=args.max_tokens,
        frequency_penalty=args.frequency_penalty,
        presence_penalty=args.presence_penalty,
    )
    policy, policy_metadata = load_policy(args.condition, args.policy_file)
    metadata = cell_metadata(
        scenario_name=args.scenario,
        condition=args.condition,
        trial_seed=args.trial_seed,
        base_url=args.base_url,
        model_name=args.model,
        sampling=sampling,
        policy_metadata=policy_metadata,
        inventory=inventory,
    )
    if args.dry_run:
        print(json.dumps(metadata, indent=2, ensure_ascii=False, sort_keys=True))
        return 0

    if args.output_directory is None:
        raise SystemExit("--execute requires --output-directory")
    scenario = _load_scenario(args.checkout, args.scenario, args.trial_seed)
    agent = LocalInstrumentedAgent(
        model_name=args.model,
        base_url=args.base_url,
        trial_seed=args.trial_seed,
        sampling=sampling,
        policy=policy,
        api_key=args.api_key,
    )
    user = LocalInstrumentedUser(
        model_name=args.model,
        base_url=args.base_url,
        trial_seed=args.trial_seed,
        sampling=sampling,
        api_key=args.api_key,
    )
    record = run_episode(
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
