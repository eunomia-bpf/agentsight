#!/usr/bin/env python3
"""Evaluate source-native task-progress boundaries on CodeTraceBench.

Inference reads only public trajectory source.  Each adjacent decision sees the
concrete task and two completed operations represented by the agent's own
intent/progress, source action, and uniquely attributable result.  Official
workflow stages are opened only by the separate score command.
"""

from __future__ import annotations

import argparse
import ast
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import json
from pathlib import Path
import random
import re
import sys
import time
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "script"))

import rq1_codetracebench_token_attribution_eval as usage_adapter  # noqa: E402
import rq3_task_rooted_stage_alignment_eval as base  # noqa: E402
import codetracebench_agentprof_eval as trace_source  # noqa: E402


ALGORITHM_VERSION = "source-native-task-progress-boundary-v1"
SCHEMA = "agentsight.rq3-source-native-task-progress-boundary"
EXPECTED_SESSIONS = 405
EXPECTED_OPERATIONS = 20_866
EXPECTED_PAIRS = 20_461
EXPECTED_STAGES = 2_948
EXPECTED_TASKS = 251
EXPECTED_FRAMEWORKS = base.EXPECTED_FRAMEWORKS
EXPECTED_LAYOUTS = {
    "miniswe-message-trajectory",
    "sweagent-trajectory-elements",
    "terminus2-commands-txt-strings",
    "openhands-agent-actions",
    "openhands-maximal-visible-action-context",
}
MAX_REQUEST_TOKENS = base.MAX_REQUEST_TOKENS
PROJECTION_LIMIT = 8_000
OUTPUT_TOKENS = 32
TASK_CHARS = 6_000
FIELD_CHARS = 2_400
MIN_TASK_CHARS = 512
MIN_FIELD_CHARS = 96
SEED = 20_260_720
BOOTSTRAP_RESAMPLES = 10_000

SYSTEM_PROMPT = """Decide whether the boundary between two adjacent completed
agent operations crosses into a different concrete subtask or workflow
responsibility. Use the concrete task and the agent's source-native intent,
progress, action, and result. A change in tool, command, file, path, status, or
low-level action does not by itself create a subtask boundary. Return continue
when the right operation advances, checks, retries, or repairs the same
concrete work as the left operation. Return boundary only when the purpose of
the work changes to a distinct subtask or workflow stage. Return only the
required JSON."""

DECISION_GRAMMAR = (
    'root ::= continue | boundary\n'
    'continue ::= "{\\\"decision\\\":\\\"continue\\\"}"\n'
    'boundary ::= "{\\\"decision\\\":\\\"boundary\\\"}"\n'
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)

    infer = commands.add_parser("infer")
    infer.add_argument("mode", choices=("preflight", "full"))
    infer.add_argument("--target-operations", type=Path, required=True)
    infer.add_argument("--raw-root", type=Path, required=True)
    infer.add_argument("--llama-url", required=True)
    infer.add_argument("--workers", type=int, default=4)
    infer.add_argument("--timeout-seconds", type=int, default=600)
    infer.add_argument("--out", type=Path, required=True)

    score = commands.add_parser("score")
    score.add_argument("--target-operations", type=Path, required=True)
    score.add_argument("--predictions", type=Path, required=True)
    score.add_argument("--verified-manifest", type=Path, required=True)
    score.add_argument("--multires-assignments", type=Path, required=True)
    score.add_argument("--out", type=Path, required=True)
    return parser.parse_args()


def absolute(path: Path) -> Path:
    return path if path.is_absolute() else ROOT / path


def relative(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return str(path.resolve())


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def write_json_atomic(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    write_json(temporary, payload)
    temporary.replace(path)


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as output:
        for row in rows:
            output.write(json.dumps(row, sort_keys=True, ensure_ascii=False) + "\n")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        while chunk := source.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def cache_name(session: str) -> str:
    return hashlib.sha256(session.encode()).hexdigest()[:24] + ".json"


def content_text(value: Any) -> str:
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return "\n".join(
            str(block.get("text") or "").strip()
            for block in value
            if isinstance(block, dict) and str(block.get("text") or "").strip()
        )
    return ""


def archive_path(raw_root: Path, session: str) -> Path:
    path = raw_root / "bench_artifacts" / "full" / f"{session}.tar.zst"
    require(path.is_file(), f"missing public archive: {path}")
    return path


def layout_from_members(framework: str, members: list[str]) -> str:
    if framework == "mini-SWE-agent":
        return "miniswe-message-trajectory"
    if framework == "SWE-agent":
        return "sweagent-trajectory-elements"
    if framework == "Terminus2":
        return "terminus2-commands-txt-strings"
    require(framework == "OpenHands", f"unsupported framework: {framework}")
    if any(
        member.endswith(".json")
        and (
            "/swe_raw/openhands" in f"/{member}"
            or member.startswith("swe_raw/openhands")
        )
        and not member.endswith("/openhands_output.json")
        for member in members
    ):
        return "openhands-maximal-visible-action-context"
    return "openhands-agent-actions"


def select_preflight(
    grouped: dict[str, list[dict[str, Any]]], raw_root: Path
) -> list[str]:
    choices: dict[str, tuple[int, str]] = {}
    for session, rows in grouped.items():
        framework = base.framework_for_session(session)
        members = base.tar_members(archive_path(raw_root, session))
        layout = layout_from_members(framework, members)
        candidate = (len(rows), session)
        if layout not in choices or candidate < choices[layout]:
            choices[layout] = candidate
    require(set(choices) == EXPECTED_LAYOUTS, "preflight layout coverage")
    return sorted(session for _, session in choices.values())


def validate_raw_steps(
    session: str,
    rows: list[dict[str, Any]],
    raw_steps: list[Any],
) -> None:
    require(len(raw_steps) == len(rows), f"{session}: raw operation count")
    for row, raw in zip(rows, raw_steps, strict=True):
        require(raw.step_id == int(row["step_id"]), f"{session}: raw step id")
        require(raw.source_ref == row["source_ref"], f"{session}: source_ref")


def mini_evidence(
    archive: Path,
    members: list[str],
    rows: list[dict[str, Any]],
    raw_steps: list[Any],
) -> list[dict[str, Any]]:
    member = next((name for name in members if name.endswith(".traj.json")), None)
    require(member is not None, "MiniSWE trajectory missing")
    payload = base.load_json(archive, member)
    messages = payload.get("messages") if isinstance(payload, dict) else None
    require(isinstance(messages, list), "MiniSWE messages missing")
    output = []
    for row, raw in zip(rows, raw_steps, strict=True):
        source_member, marker, fragment = row["source_ref"].partition("#message-")
        require(marker and source_member == member, "MiniSWE source_ref layout")
        index = int(fragment)
        require(index < len(messages), "MiniSWE source message missing")
        message = messages[index]
        require(
            isinstance(message, dict)
            and message.get("role") == "assistant"
            and isinstance(message.get("content"), str),
            "MiniSWE source assistant message",
        )
        match = trace_source.BASH_FENCE_RE.search(message["content"])
        require(match is not None, "MiniSWE source action fence")
        action = match.group(1).strip()
        require(action == raw.action, "MiniSWE source action mismatch")
        intent = (message["content"][: match.start()] + message["content"][match.end() :]).strip()
        output.append(
            {
                "step": int(row["step_id"]),
                "source_ref": row["source_ref"],
                "intent": intent,
                "progress": "",
                "action": raw.action,
                "result": str(raw.observation or ""),
            }
        )
    return output


def sweagent_evidence(
    archive: Path,
    members: list[str],
    rows: list[dict[str, Any]],
    raw_steps: list[Any],
) -> list[dict[str, Any]]:
    member = next((name for name in members if name.endswith(".traj")), None)
    require(member is not None, "SWE-agent trajectory missing")
    payload = base.load_json(archive, member)
    trajectory = payload.get("trajectory") if isinstance(payload, dict) else None
    require(isinstance(trajectory, list), "SWE-agent trajectory[] missing")
    output = []
    for row, raw in zip(rows, raw_steps, strict=True):
        source_member, marker, fragment = row["source_ref"].partition("#trajectory-")
        require(marker and source_member == member, "SWE-agent source_ref layout")
        index = int(fragment)
        require(index < len(trajectory), "SWE-agent source element missing")
        item = trajectory[index]
        require(isinstance(item, dict), "SWE-agent source element type")
        action = item.get("action")
        if isinstance(action, dict):
            action_text = json.dumps(action, ensure_ascii=False, sort_keys=True)
        elif action is None:
            action_text = ""
        else:
            action_text = str(action)
        require(action_text == raw.action, "SWE-agent source action mismatch")
        output.append(
            {
                "step": int(row["step_id"]),
                "source_ref": row["source_ref"],
                "intent": str(item.get("thought") or item.get("response") or ""),
                "progress": "",
                "action": raw.action,
                "result": str(raw.observation or ""),
            }
        )
    return output


def openhands_event_evidence(
    archive: Path,
    members: list[str],
    rows: list[dict[str, Any]],
    raw_steps: list[Any],
) -> list[dict[str, Any]]:
    events = base.load_openhands_events(archive, members)
    selected = [
        (member, event)
        for member, event in events
        if event.get("source") == "agent"
        and event.get("action")
        and event.get("action") not in {"system", "message"}
    ]
    require(len(selected) == len(rows), "OpenHands native selected action count")
    output = []
    for row, raw, (member, event) in zip(rows, raw_steps, selected, strict=True):
        require(member == raw.source_ref, "OpenHands native event source_ref")
        action = trace_source.openhands_event_action(event)
        require(action == raw.action, "OpenHands native source action mismatch")
        args = event.get("args") if isinstance(event.get("args"), dict) else {}
        metadata = (
            event.get("tool_call_metadata")
            if isinstance(event.get("tool_call_metadata"), dict)
            else {}
        )
        model_response = (
            metadata.get("model_response")
            if isinstance(metadata.get("model_response"), dict)
            else {}
        )
        choices = model_response.get("choices")
        response_intent = ""
        if isinstance(choices, list) and choices and isinstance(choices[0], dict):
            response_message = choices[0].get("message")
            if isinstance(response_message, dict):
                response_intent = content_text(response_message.get("content"))
        intent_parts = []
        for value in (str(args.get("thought") or ""), response_intent):
            if value.strip() and value.strip() not in intent_parts:
                intent_parts.append(value.strip())
        intent = "\n".join(intent_parts)
        if event.get("action") == "think":
            intent = intent or str(args.get("content") or event.get("message") or "")
        progress = (
            json.dumps(args.get("task_list"), ensure_ascii=False, sort_keys=True)
            if args.get("task_list")
            else ""
        )
        output.append(
            {
                "step": int(row["step_id"]),
                "source_ref": row["source_ref"],
                "intent": intent,
                "progress": progress,
                "action": raw.action,
                "result": str(raw.observation or ""),
            }
        )
    return output


def openhands_history_evidence(
    archive: Path,
    members: list[str],
    rows: list[dict[str, Any]],
    raw_steps: list[Any],
) -> list[dict[str, Any]]:
    source_members = {str(row["source_ref"]).split("#", 1)[0] for row in rows}
    require(len(source_members) == 1, "OpenHands history source member count")
    member = source_members.pop()
    require(member in members, "OpenHands history source member missing")
    payload = base.load_json(archive, member)
    messages = payload.get("messages") if isinstance(payload, dict) else None
    require(isinstance(messages, list), "OpenHands history messages missing")
    tool_results: dict[str, str] = {}
    for message in messages:
        if not isinstance(message, dict) or message.get("role") != "tool":
            continue
        call_id = message.get("tool_call_id")
        if isinstance(call_id, str):
            require(call_id not in tool_results, "duplicate OpenHands tool result")
            tool_results[call_id] = content_text(message.get("content"))

    evidence: dict[tuple[int, int], dict[str, str]] = {}
    progress = ""
    for message_index, message in enumerate(messages):
        if not isinstance(message, dict) or message.get("role") != "assistant":
            continue
        base_intent = content_text(message.get("content"))
        calls = message.get("tool_calls")
        if not isinstance(calls, list):
            continue
        for tool_index, call in enumerate(calls):
            function = call.get("function") if isinstance(call, dict) else None
            require(isinstance(function, dict), "OpenHands tool function missing")
            try:
                arguments = json.loads(function.get("arguments") or "{}")
            except json.JSONDecodeError:
                arguments = {}
            if not isinstance(arguments, dict):
                arguments = {}
            if function.get("name") == "task_tracker" and arguments.get("task_list"):
                progress = json.dumps(
                    arguments["task_list"], ensure_ascii=False, sort_keys=True
                )
            call_id = call.get("id") if isinstance(call, dict) else None
            require(isinstance(call_id, str), "OpenHands tool call id missing")
            evidence[(message_index, tool_index)] = {
                "intent": "\n".join(
                    value
                    for value in (base_intent, str(arguments.get("thought") or ""))
                    if value.strip()
                ),
                "progress": progress,
                "action": trace_source.render_tool_action(
                    str(function.get("name") or "tool"), function.get("arguments")
                ),
                "result": tool_results.get(call_id, ""),
            }

    output = []
    for row, raw in zip(rows, raw_steps, strict=True):
        source_member, marker, fragment = row["source_ref"].partition("#message-")
        require(marker and source_member == member, "OpenHands history source_ref")
        match = re.fullmatch(r"(\d+)-tool-(\d+)", fragment)
        require(match is not None, "OpenHands history source fragment")
        key = tuple(map(int, match.groups()))
        require(key in evidence, "OpenHands referenced tool call missing")
        item = evidence[key]
        require(item["action"] == raw.action, "OpenHands history action mismatch")
        output.append(
            {
                "step": int(row["step_id"]),
                "source_ref": row["source_ref"],
                **item,
            }
        )
    return output


def terminus_evidence(
    archive: Path,
    members: list[str],
    rows: list[dict[str, Any]],
    raw_steps: list[Any],
) -> list[dict[str, Any]]:
    command_members = {str(row["source_ref"]).split("#", 1)[0] for row in rows}
    require(len(command_members) == 1, "Terminus command member count")
    command_member = command_members.pop()
    require(command_member in members, "Terminus commands.txt missing")
    command_lines = base.tar_text(archive, command_member).splitlines()
    official = []
    for row, raw in zip(rows, raw_steps, strict=True):
        source_member, marker, fragment = row["source_ref"].partition("#line-")
        require(marker and source_member == command_member, "Terminus source_ref")
        line_number = int(fragment)
        value = ast.literal_eval(command_lines[line_number - 1])
        require(isinstance(value, str), "Terminus official command type")
        source_action = value.replace("\r\n", "\n").replace("\r", "\n")
        if source_action.endswith("\n"):
            source_action = source_action[:-1]
        require(raw.action == source_action, "Terminus source action mismatch")
        official.append(usage_adapter.normalize_command(value))

    responses: dict[int, list[str]] = {}
    payloads: dict[int, dict[str, Any]] = {}
    for member in members:
        if not member.endswith("/response.txt"):
            continue
        episode = usage_adapter.episode_number(member)
        text = base.tar_text(archive, member)
        responses[episode] = usage_adapter.parse_terminus_commands(text)
        try:
            payload = json.loads(text)
        except json.JSONDecodeError:
            payload = {}
        payloads[episode] = payload if isinstance(payload, dict) else {}
    stream = [
        (command, episode)
        for episode in sorted(responses)
        for command in responses[episode]
    ]
    output = []
    cursor = skipped = 0
    for row, raw, command in zip(rows, raw_steps, official, strict=True):
        while cursor < len(stream) and stream[cursor][0] != command:
            cursor += 1
            skipped += 1
        require(cursor < len(stream), "Terminus command absent from response stream")
        _, episode = stream[cursor]
        cursor += 1
        payload = payloads.get(episode, {})
        output.append(
            {
                "step": int(row["step_id"]),
                "source_ref": row["source_ref"],
                "intent": str(payload.get("analysis") or ""),
                "progress": str(payload.get("plan") or ""),
                "action": raw.action,
                "result": "",
            }
        )
    skipped += len(stream) - cursor
    require(skipped <= 2, f"Terminus unexpected extra response commands: {skipped}")
    return output


def reconstruct_source(
    raw_root: Path, session: str, rows: list[dict[str, Any]]
) -> dict[str, Any]:
    framework = base.framework_for_session(session)
    archive = archive_path(raw_root, session)
    members = base.tar_members(archive)
    raw_steps, adapter = base.ADAPTERS[framework](archive, members, len(rows))
    validate_raw_steps(session, rows, raw_steps)
    layout = layout_from_members(framework, members)
    require(adapter == layout, f"{session}: detected/parsed layout mismatch")
    task, task_source = base.extract_task_text(archive, members, framework)
    if layout == "miniswe-message-trajectory":
        operations = mini_evidence(archive, members, rows, raw_steps)
    elif layout == "sweagent-trajectory-elements":
        operations = sweagent_evidence(archive, members, rows, raw_steps)
    elif layout == "openhands-agent-actions":
        operations = openhands_event_evidence(archive, members, rows, raw_steps)
    elif layout == "openhands-maximal-visible-action-context":
        operations = openhands_history_evidence(archive, members, rows, raw_steps)
    else:
        require(layout == "terminus2-commands-txt-strings", "unknown layout")
        operations = terminus_evidence(archive, members, rows, raw_steps)
    require(len(operations) == len(rows), f"{session}: evidence coverage")
    require(
        [int(row["step"]) for row in operations] == list(range(1, len(rows) + 1)),
        f"{session}: evidence step sequence",
    )
    return {
        "session": session,
        "framework": framework,
        "adapter": layout,
        "archive": relative(archive),
        "archive_sha256": sha256_file(archive),
        "task": task,
        "task_source": task_source,
        "operations": operations,
    }


def projected_operation(operation: dict[str, Any], budget: int) -> dict[str, Any]:
    return {
        "step": int(operation["step"]),
        "native_intent": base.clip_text(str(operation["intent"]), budget),
        "native_progress": base.clip_text(str(operation["progress"]), budget),
        "source_action": base.clip_text(str(operation["action"]), budget),
        "result": base.clip_text(str(operation["result"]), budget),
    }


def pair_prompt(task: str, left: dict[str, Any], right: dict[str, Any]) -> str:
    return (
        "CONCRETE TASK\n"
        + task
        + "\n\nLEFT COMPLETED OPERATION\n"
        + json.dumps(left, ensure_ascii=False, separators=(",", ":"))
        + "\n\nRIGHT COMPLETED OPERATION\n"
        + json.dumps(right, ensure_ascii=False, separators=(",", ":"))
    )


def project_pair(
    source: dict[str, Any],
    left: dict[str, Any],
    right: dict[str, Any],
    llama_url: str,
    timeout_seconds: int,
) -> tuple[str, int, int, int]:
    task_budget = min(len(str(source["task"])), TASK_CHARS)
    field_budget = FIELD_CHARS
    while True:
        task = base.clip_text(str(source["task"]), task_budget)
        user = pair_prompt(
            task,
            projected_operation(left, field_budget),
            projected_operation(right, field_budget),
        )
        tokens = base.token_count(
            llama_url, SYSTEM_PROMPT + "\n" + user, timeout_seconds
        )
        if tokens <= PROJECTION_LIMIT:
            return user, tokens, task_budget, field_budget
        if field_budget > MIN_FIELD_CHARS:
            field_budget = max(MIN_FIELD_CHARS, field_budget // 2)
        elif task_budget > MIN_TASK_CHARS:
            task_budget = max(MIN_TASK_CHARS, task_budget // 2)
        else:
            raise RuntimeError(f"{source['session']}: pair cannot fit model context")


def parse_decision(raw: str) -> str:
    value = json.loads(raw)
    require(isinstance(value, dict) and set(value) == {"decision"}, "decision keys")
    decision = value["decision"]
    require(decision in {"continue", "boundary"}, "decision value")
    return str(decision)


def call_boundary(
    llama_url: str, user: str, timeout_seconds: int
) -> dict[str, Any]:
    raw, response, attempts = base.call_model(
        llama_url,
        SYSTEM_PROMPT,
        user,
        DECISION_GRAMMAR,
        timeout_seconds,
        OUTPUT_TOKENS,
    )
    usage = response.get("usage") or {}
    request_tokens = int(usage.get("prompt_tokens", 0))
    require(0 < request_tokens <= MAX_REQUEST_TOKENS, "model request token limit")
    return {
        "decision": parse_decision(raw),
        "raw": raw,
        "usage": usage,
        "attempts": attempts,
        "request_tokens": request_tokens,
    }


def availability(operation: dict[str, Any]) -> dict[str, bool]:
    return {
        "intent": bool(str(operation["intent"]).strip()),
        "progress": bool(str(operation["progress"]).strip()),
        "result": bool(str(operation["result"]).strip()),
    }


def infer_session(
    session: str,
    rows: list[dict[str, Any]],
    raw_root: Path,
    llama_url: str,
    timeout_seconds: int,
    cache_dir: Path,
) -> dict[str, Any]:
    source = reconstruct_source(raw_root, session, rows)
    path = cache_dir / cache_name(session)
    if path.is_file():
        result = json.loads(path.read_text(encoding="utf-8"))
        require(result.get("algorithm_version") == ALGORITHM_VERSION, "cache version")
        require(result.get("session") == session, "cache session")
        require(result.get("archive_sha256") == source["archive_sha256"], "cache archive")
        require(result.get("adapter") == source["adapter"], "cache adapter")
        require(result.get("model") == base.MODEL, "cache model")
        require(result.get("model_sha256") == base.MODEL_SHA256, "cache model hash")
        require(result.get("seed") == SEED, "cache seed")
        require(
            result.get("system_prompt_sha256")
            == hashlib.sha256(SYSTEM_PROMPT.encode()).hexdigest(),
            "cache system prompt",
        )
        require(
            result.get("grammar_sha256")
            == hashlib.sha256(DECISION_GRAMMAR.encode()).hexdigest(),
            "cache grammar",
        )
    else:
        result = {
            "schema": SCHEMA + ".session.v1",
            "algorithm_version": ALGORITHM_VERSION,
            "session": session,
            "framework": source["framework"],
            "adapter": source["adapter"],
            "archive": source["archive"],
            "archive_sha256": source["archive_sha256"],
            "task_source": source["task_source"],
            "model": base.MODEL,
            "model_sha256": base.MODEL_SHA256,
            "seed": SEED,
            "system_prompt_sha256": hashlib.sha256(SYSTEM_PROMPT.encode()).hexdigest(),
            "grammar_sha256": hashlib.sha256(DECISION_GRAMMAR.encode()).hexdigest(),
            "decisions": [],
        }
        write_json_atomic(path, result)

    operations = source["operations"]
    decisions = result["decisions"]
    require(len(decisions) <= max(0, len(operations) - 1), "excess cached decisions")
    projected = []
    for index in range(len(operations) - 1):
        user, projected_tokens, task_budget, field_budget = project_pair(
            source,
            operations[index],
            operations[index + 1],
            llama_url,
            timeout_seconds,
        )
        request_hash = hashlib.sha256(
            json.dumps(
                {
                    "model": base.MODEL,
                    "model_sha256": base.MODEL_SHA256,
                    "seed": SEED,
                    "temperature": 0,
                    "system": SYSTEM_PROMPT,
                    "grammar": DECISION_GRAMMAR,
                    "user": user,
                },
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ).encode()
        ).hexdigest()
        if index < len(decisions):
            require(decisions[index]["request_sha256"] == request_hash, "cached request drift")
        else:
            call = call_boundary(llama_url, user, timeout_seconds)
            decisions.append(
                {
                    "left_step": int(operations[index]["step"]),
                    "right_step": int(operations[index + 1]["step"]),
                    "decision": call["decision"],
                    "request_sha256": request_hash,
                    "projected_tokens": projected_tokens,
                    "task_char_budget": task_budget,
                    "field_char_budget": field_budget,
                    "left_availability": availability(operations[index]),
                    "right_availability": availability(operations[index + 1]),
                    "user": user,
                    "call": call,
                }
            )
            write_json_atomic(path, result)
        projected.append((user, projected_tokens))

    group = 0
    predictions = []
    for index, operation in enumerate(operations):
        if index and decisions[index - 1]["decision"] == "boundary":
            group += 1
        predictions.append(
            {
                "session": session,
                "framework": source["framework"],
                "adapter": source["adapter"],
                "step_id": int(operation["step"]),
                "candidate_index": group,
                "candidate_decision": (
                    "initialize" if index == 0 else decisions[index - 1]["decision"]
                ),
                "intent_available": availability(operation)["intent"],
                "progress_available": availability(operation)["progress"],
                "result_available": availability(operation)["result"],
            }
        )
    calls = [decision["call"] for decision in decisions]
    summary = {
        "session": session,
        "framework": source["framework"],
        "adapter": source["adapter"],
        "operations": len(operations),
        "pairs": len(decisions),
        "boundaries": sum(item["decision"] == "boundary" for item in decisions),
        "continues": sum(item["decision"] == "continue" for item in decisions),
        "intent_operations": sum(row["intent_available"] for row in predictions),
        "progress_operations": sum(row["progress_available"] for row in predictions),
        "result_operations": sum(row["result_available"] for row in predictions),
        "request_token_min": min((int(call["request_tokens"]) for call in calls), default=0),
        "request_token_max": max((int(call["request_tokens"]) for call in calls), default=0),
        "usage": dict(
            sum(
                (
                    Counter(
                        {
                            key: value
                            for key, value in (call.get("usage") or {}).items()
                            if isinstance(value, int)
                        }
                    )
                    for call in calls
                ),
                Counter(),
            )
        ),
    }
    return {"summary": summary, "predictions": predictions}


def run_inference(args: argparse.Namespace) -> None:
    started = time.monotonic()
    target_path = absolute(args.target_operations)
    raw_root = absolute(args.raw_root)
    out_dir = absolute(args.out)
    grouped = base.load_visible_operations(target_path)
    require(len(grouped) == EXPECTED_SESSIONS, "target session count")
    require(sum(map(len, grouped.values())) == EXPECTED_OPERATIONS, "target operation count")
    selected = (
        select_preflight(grouped, raw_root)
        if args.mode == "preflight"
        else sorted(grouped)
    )
    cache_dir = out_dir / "sessions"
    cache_dir.mkdir(parents=True, exist_ok=True)
    results: dict[str, dict[str, Any]] = {}

    def infer(session: str) -> dict[str, Any]:
        return infer_session(
            session,
            grouped[session],
            raw_root,
            args.llama_url,
            args.timeout_seconds,
            cache_dir,
        )

    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = {executor.submit(infer, session): session for session in selected}
        for future in as_completed(futures):
            session = futures[future]
            results[session] = future.result()
            print(f"inferred {len(results)}/{len(selected)} {session}", flush=True)

    predictions = [
        row
        for session in sorted(results)
        for row in results[session]["predictions"]
    ]
    summaries = [results[session]["summary"] for session in sorted(results)]
    expected_operations = sum(len(grouped[session]) for session in selected)
    expected_pairs = expected_operations - len(selected)
    require(len(predictions) == expected_operations, "prediction coverage")
    require(sum(row["pairs"] for row in summaries) == expected_pairs, "pair coverage")
    require(
        len({(row["session"], row["step_id"]) for row in predictions})
        == expected_operations,
        "prediction uniqueness",
    )
    frameworks = Counter(row["framework"] for row in summaries)
    layouts = Counter(row["adapter"] for row in summaries)
    require(set(layouts) == EXPECTED_LAYOUTS, "inference layout coverage")
    write_jsonl(out_dir / "predictions.jsonl", predictions)
    usage = sum((Counter(row["usage"]) for row in summaries), Counter())
    summary = {
        "schema": SCHEMA + ".inference.v1",
        "algorithm_version": ALGORITHM_VERSION,
        "status": "complete",
        "mode": args.mode,
        "model": base.MODEL,
        "model_sha256": base.MODEL_SHA256,
        "seed": SEED,
        "sessions": len(selected),
        "operations": expected_operations,
        "pairs": expected_pairs,
        "frameworks": dict(frameworks),
        "adapter_layouts": dict(layouts),
        "boundaries": sum(row["boundaries"] for row in summaries),
        "continues": sum(row["continues"] for row in summaries),
        "predicted_groups": len(selected) + sum(row["boundaries"] for row in summaries),
        "boundary_rate": sum(row["boundaries"] for row in summaries) / max(1, expected_pairs),
        "intent_operations": sum(row["intent_operations"] for row in summaries),
        "progress_operations": sum(row["progress_operations"] for row in summaries),
        "result_operations": sum(row["result_operations"] for row in summaries),
        "request_token_min": min(
            (row["request_token_min"] for row in summaries if row["pairs"]), default=0
        ),
        "request_token_max": max(
            (row["request_token_max"] for row in summaries), default=0
        ),
        "model_usage": dict(usage),
        "wall_seconds": time.monotonic() - started,
        "selected_sessions": selected,
        "predictions": relative(out_dir / "predictions.jsonl"),
        "isolation": {
            "official_manifest_opened": False,
            "official_stages_opened": False,
            "model_visible_fields": [
                "concrete_task",
                "native_intent",
                "native_progress",
                "source_action",
                "uniquely_attributable_result",
            ],
            "phase_or_action_kind_visible": False,
            "agent_model_session_status_visible": False,
            "all_operations_retained": True,
        },
    }
    if args.mode == "full":
        require(summary["sessions"] == EXPECTED_SESSIONS, "full sessions")
        require(summary["operations"] == EXPECTED_OPERATIONS, "full operations")
        require(summary["pairs"] == EXPECTED_PAIRS, "full pairs")
        require(set(frameworks) == EXPECTED_FRAMEWORKS, "full frameworks")
    write_json(out_dir / "inference-summary.json", summary)
    print(json.dumps(summary, sort_keys=True), flush=True)


def build_score_rows(
    grouped: dict[str, list[dict[str, Any]]],
    selected: list[str],
    predictions: dict[tuple[str, int], dict[str, Any]],
    baselines: dict[tuple[str, int], dict[str, str]],
    official: dict[tuple[str, int], str],
    frameworks: dict[str, str],
    tasks: dict[str, str],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    operations = []
    pairs = []
    methods = (
        "candidate",
        "multires_recurrence",
        "current_recurrence",
        "phase",
        "raw_action",
        "action",
        "one_span",
    )
    for session in selected:
        previous = None
        for row in grouped[session]:
            key = (session, int(row["step_id"]))
            require(key in predictions, f"missing prediction: {key}")
            require(key in baselines, f"missing baseline: {key}")
            prediction = predictions[key]
            operation = {
                "session": session,
                "framework": frameworks[session],
                "task_name": tasks[session],
                "step_id": int(row["step_id"]),
                "official_stage": official[key],
                "candidate": f"{session}:candidate-{int(prediction['candidate_index']):04d}",
                **baselines[key],
            }
            operations.append(operation)
            if previous is not None:
                pair = {
                    "session": session,
                    "framework": frameworks[session],
                    "task_name": tasks[session],
                    "position": int(row["step_id"]) - 1,
                    "official_boundary": previous["official_stage"]
                    != operation["official_stage"],
                }
                for method in methods:
                    pair[method] = previous[method] != operation[method]
                pairs.append(pair)
            previous = operation
    return pairs, operations


def bcubed_task_bootstrap(
    rows: list[dict[str, Any]], candidate: str, baseline: str, output: Path
) -> dict[str, Any]:
    by_task: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_task[str(row["task_name"])].append(row)
    tasks = sorted(by_task)
    sufficient = {}
    for task, task_rows in by_task.items():
        for method in (candidate, baseline):
            metric = base.bcubed(task_rows, method)
            sufficient[(task, method)] = (
                len(task_rows),
                float(metric["precision"]) * len(task_rows),
                float(metric["recall"]) * len(task_rows),
            )

    def f1(draw: list[str], method: str) -> float:
        count = precision_sum = recall_sum = 0.0
        for task in draw:
            local_count, local_precision, local_recall = sufficient[(task, method)]
            count += local_count
            precision_sum += local_precision
            recall_sum += local_recall
        precision = precision_sum / count
        recall = recall_sum / count
        return 2 * precision * recall / (precision + recall) if precision + recall else 0.0

    generator = random.Random(SEED)
    deltas = []
    for index in range(BOOTSTRAP_RESAMPLES):
        draw = generator.choices(tasks, k=len(tasks))
        delta = f1(draw, candidate) - f1(draw, baseline)
        deltas.append(delta)
    write_jsonl(
        output,
        ({"resample": index, "delta": delta} for index, delta in enumerate(deltas)),
    )
    return {
        "candidate": candidate,
        "baseline": baseline,
        "resamples": BOOTSTRAP_RESAMPLES,
        "task_clusters": len(tasks),
        "mean_delta": sum(deltas) / len(deltas),
        "ci95": [base.percentile(deltas, 0.025), base.percentile(deltas, 0.975)],
        "positive_fraction": sum(delta > 0 for delta in deltas) / len(deltas),
    }


def report(summary: dict[str, Any]) -> str:
    lines = [
        "# Source-Native Task-Progress Boundaries — Result",
        "",
        f"- mode: {summary['mode']}",
        f"- status: {summary['status']}",
        f"- registered interpretation: **{summary['registered_interpretation']}**",
        "",
        "## Standard metrics",
        "",
        "| Method | B³ P | B³ R | B³ F1 | Span F1 | Boundary F1 |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for method, values in summary["metrics"].items():
        lines.append(
            f"| {method} | {values['bcubed']['precision']:.6f} | "
            f"{values['bcubed']['recall']:.6f} | {values['bcubed']['f1']:.6f} | "
            f"{values['span']['f1']:.6f} | {values['boundary']['f1']:.6f} |"
        )
    bootstrap = summary["bootstrap"]
    lines.extend(
        [
            "",
            "## Paired task-cluster uncertainty",
            "",
            f"Candidate minus incumbent multi-resolution recurrence: mean "
            f"{bootstrap['mean_delta']:.6f}, 95% CI "
            f"[{bootstrap['ci95'][0]:.6f}, {bootstrap['ci95'][1]:.6f}], "
            f"positive fraction {bootstrap['positive_fraction']:.4f}.",
            "",
            "## Interpretation boundary",
            "",
            "This experiment scores one flat human workflow-stage partition. "
            "It does not score generated subtask names, recursive depth, the "
            "complete task-semantic hierarchy, diagnosis quality, or the paper thesis.",
        ]
    )
    return "\n".join(lines) + "\n"


def run_scoring(args: argparse.Namespace) -> None:
    target_path = absolute(args.target_operations)
    prediction_dir = absolute(args.predictions)
    manifest_path = absolute(args.verified_manifest)
    baseline_path = absolute(args.multires_assignments)
    out_dir = absolute(args.out)
    summary_path = prediction_dir / "inference-summary.json"
    prediction_path = prediction_dir / "predictions.jsonl"
    for path in (target_path, summary_path, prediction_path, manifest_path, baseline_path):
        require(path.is_file(), f"missing score input: {path}")
    inference = json.loads(summary_path.read_text(encoding="utf-8"))
    require(inference.get("status") == "complete", "inference incomplete")
    mode = str(inference["mode"])
    grouped = base.load_visible_operations(target_path)
    predictions = base.load_prediction_rows(prediction_path)
    selected = sorted({session for session, _ in predictions})
    expected = {
        (session, int(row["step_id"]))
        for session in selected
        for row in grouped[session]
    }
    require(set(predictions) == expected, "prediction coverage")
    baselines = base.load_baselines(baseline_path)
    require(expected <= set(baselines), "baseline coverage")
    official, frameworks, tasks = base.load_stages_after_prediction(
        manifest_path, grouped, selected
    )
    pairs, operations = build_score_rows(
        grouped, selected, predictions, baselines, official, frameworks, tasks
    )
    require(len(operations) == int(inference["operations"]), "scored operations")
    require(len(pairs) == int(inference["pairs"]), "scored pairs")
    methods = (
        "candidate",
        "multires_recurrence",
        "current_recurrence",
        "phase",
        "raw_action",
        "action",
        "one_span",
    )
    metrics = {
        method: {
            "bcubed": base.bcubed(operations, method),
            "span": base.span_metrics(operations, method),
            "boundary": base.boundary_metrics(pairs, method),
        }
        for method in methods
    }
    out_dir.mkdir(parents=True, exist_ok=True)
    bootstrap = bcubed_task_bootstrap(
        operations,
        "candidate",
        "multires_recurrence",
        out_dir / "bootstrap-candidate-minus-multires_recurrence.jsonl",
    )
    candidate_f1 = metrics["candidate"]["bcubed"]["f1"]
    incumbent_f1 = metrics["multires_recurrence"]["bcubed"]["f1"]
    supported = candidate_f1 > incumbent_f1 and bootstrap["ci95"][0] > 0
    contradicted = bootstrap["ci95"][1] <= 0
    interpretation = (
        "supported-and-adopted"
        if supported
        else "contradicted-not-adopted"
        if contradicted
        else "inconclusive-not-adopted"
    )
    per_framework = {}
    for framework in sorted(set(frameworks.values())):
        operation_slice = [row for row in operations if row["framework"] == framework]
        pair_slice = [row for row in pairs if row["framework"] == framework]
        per_framework[framework] = {
            method: {
                "bcubed": base.bcubed(operation_slice, method),
                "span": base.span_metrics(operation_slice, method),
                "boundary": base.boundary_metrics(pair_slice, method),
            }
            for method in ("candidate", "multires_recurrence")
        }
    summary = {
        "schema": SCHEMA + ".score.v1",
        "mode": mode,
        "status": "complete",
        "registered_interpretation": interpretation,
        "population": {
            "sessions": len(selected),
            "operations": len(operations),
            "pairs": len(pairs),
            "official_stages": len(set(official.values())),
            "tasks": len(set(tasks.values())),
            "frameworks": dict(Counter(frameworks.values())),
            "adapter_layouts": inference["adapter_layouts"],
        },
        "source_evidence": {
            "intent_operations": inference["intent_operations"],
            "progress_operations": inference["progress_operations"],
            "result_operations": inference["result_operations"],
        },
        "metrics": metrics,
        "bootstrap": bootstrap,
        "per_framework": per_framework,
        "decision": {
            "primary_metric": "ordinary operation-level B-cubed F1",
            "incumbent": "multires_recurrence",
            "candidate_point_higher": candidate_f1 > incumbent_f1,
            "candidate_interval_wholly_positive": bootstrap["ci95"][0] > 0,
            "candidate_interval_wholly_nonpositive": contradicted,
        },
        "claim_boundary": (
            "one flat completed-trajectory workflow-stage partition only; "
            "source-native evidence is composite and nested task-stack depth "
            "and label wording remain unscored"
        ),
    }
    if mode == "full":
        require(len(selected) == EXPECTED_SESSIONS, "full scored sessions")
        require(len(operations) == EXPECTED_OPERATIONS, "full scored operations")
        require(len(pairs) == EXPECTED_PAIRS, "full scored pairs")
        require(len(set(official.values())) == EXPECTED_STAGES, "full official stages")
        require(len(set(tasks.values())) == EXPECTED_TASKS, "full task count")
    write_jsonl(out_dir / "operation-score-rows.jsonl", operations)
    write_jsonl(out_dir / "boundary-score-rows.jsonl", pairs)
    write_json(out_dir / "summary.json", summary)
    (out_dir / "report.md").write_text(report(summary), encoding="utf-8")
    print(json.dumps(summary, sort_keys=True), flush=True)


def main() -> None:
    args = parse_args()
    if args.command == "infer":
        run_inference(args)
    else:
        run_scoring(args)


if __name__ == "__main__":
    main()
