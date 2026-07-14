#!/usr/bin/env python3
"""Reviewed TraceElephant experiment for AgentProf RQ2.

The builder path never reads TraceElephant's mistake_* annotations.  It creates
visible source projections, calls the released response-only All-at-Once prompt,
derives target-blind profiling fields, invokes the real AgentProf binary, and
materializes target-independent controls.  A separate scorer subprocess reads
the annotations only after every builder artifact is terminal.
"""

from __future__ import annotations

import argparse
import collections
import dataclasses
import gzip
import hashlib
import importlib.util
import json
import math
import multiprocessing as mp
import os
import random
import re
import shutil
import subprocess
import sys
import time
import unicodedata
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence


EXPECTED_CELLS: dict[str, tuple[str, str, int, int]] = {
    "captain-runs-assistantbench": ("Captain-Agent", "AssistantBench", 12, 187),
    "captain-runs-gaia": ("Captain-Agent", "GAIA", 73, 1559),
    "magentic-runs-assistant-bench": ("Magentic-One", "AssistantBench", 17, 603),
    "magentic-runs-gaia": ("Magentic-One", "GAIA", 74, 2060),
    "swe-agent-runs-swe-bench": ("SWE-Agent", "SWE-Bench", 44, 1551),
}
EXPECTED_TRACES = 220
EXPECTED_STEPS = 5960
CONTEXT_WINDOW = 32768
Z_975 = 1.959963984540054
AGENTPROF_VERSION = "agentpprof 0.2.37"
PROPOSED_STACK = ("system", "role", "intent", "component", "raw_action", "status")
RAW_STACK = ("system", "component", "raw_action")
SESSION_STACK = ("system", "trace_id")
SOURCE_NATIVE_STACK = ("system", "trace_id", "component")
ROLES = frozenset(
    ("coordination", "information", "artifact", "execution", "verification", "response", "unknown")
)
INTENTS = frozenset(("plan", "inspect", "transform", "act", "verify", "recover", "report", "unknown"))
STATUSES = frozenset(("progress", "success", "failure", "blocked", "unclear"))
EDITOR_COMMANDS = frozenset(("view", "create", "str_replace", "insert", "undo_edit"))
SCORER_KEYS = frozenset(("mistake_agent", "mistake_step", "mistake_reason"))
VISIBLE_META_KEYS = (
    "task_id",
    "task_instruction",
    "system_name",
    "agent_configuration",
    "run_id",
    "ground_truth",
    "tests_status",
    "agent_system_intro",
)
TAG_INSTRUCTION = """You assign ordinary profiling fields to target-blind agent execution steps.
Do not diagnose a failure and do not predict a mistake.
Choose exactly one role from: coordination, information, artifact, execution, verification, response, unknown.
Choose exactly one intent from: plan, inspect, transform, act, verify, recover, report, unknown.
Choose exactly one status from: progress, success, failure, blocked, unclear.
Role means the component's primary responsibility in this step. Intent means what the step is trying to accomplish. Status means only the outcome visibly present in the current step.
Return one JSON object with key steps, whose value is an array in input order.
Every item must contain exactly integer step, string role, string intent, and string status. No explanation."""


class ExperimentError(RuntimeError):
    pass


class RetryableResponseError(RuntimeError):
    pass


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")


def read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ExperimentError(f"failed to read {path}: {error}") from error


def write_jsonl(path: Path, rows: Iterable[Mapping[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as output:
        for row in rows:
            output.write(canonical_json(dict(row)) + "\n")


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    try:
        with path.open("r", encoding="utf-8") as source:
            for line_number, line in enumerate(source, start=1):
                if not line.strip():
                    continue
                value = json.loads(line)
                if not isinstance(value, dict):
                    raise ExperimentError(f"{path}:{line_number}: expected object")
                rows.append(value)
    except (OSError, json.JSONDecodeError) as error:
        raise ExperimentError(f"failed to read {path}: {error}") from error
    return rows


def normalize_text(value: str) -> str:
    return unicodedata.normalize("NFKC", value).strip().casefold()


def hex_encode(value: str) -> str:
    return "hex:" + value.encode("utf-8").hex()


def hex_decode(value: str) -> str:
    if not value.startswith("hex:"):
        raise ExperimentError(f"not a hex frame: {value!r}")
    try:
        return bytes.fromhex(value[4:]).decode("utf-8")
    except (ValueError, UnicodeDecodeError) as error:
        raise ExperimentError(f"invalid hex frame: {value!r}") from error


def head_tail(value: str, each: int) -> str:
    if len(value) <= each * 2:
        return value
    return value[:each] + "\n...[fixed middle excerpt omitted]...\n" + value[-each:]


def _load_json_object(path: Path) -> dict[str, Any]:
    value = read_json(path)
    if not isinstance(value, dict):
        raise ExperimentError(f"{path}: expected object")
    return value


def _load_json_array(path: Path) -> list[dict[str, Any]]:
    value = read_json(path)
    if not isinstance(value, list) or not all(isinstance(row, dict) for row in value):
        raise ExperimentError(f"{path}: expected array of objects")
    return [dict(row) for row in value]


def project_visible_source(data_root: Path, out: Path) -> dict[str, Any]:
    """Run in an isolator process; never writes scorer-only metadata values."""
    rows: list[dict[str, Any]] = []
    observed: dict[str, dict[str, int]] = {}
    trace_ids: set[str] = set()
    for dirname, (expected_system, benchmark, expected_traces, expected_steps) in EXPECTED_CELLS.items():
        cell_dir = data_root / dirname
        if not cell_dir.is_dir():
            raise ExperimentError(f"missing official cell {cell_dir}")
        trace_count = 0
        step_count = 0
        for trace_dir in sorted(path for path in cell_dir.iterdir() if path.is_dir()):
            metadata_path = trace_dir / "trace_metadata.json"
            steps_path = trace_dir / "step_records.json"
            if not metadata_path.is_file() or not steps_path.is_file():
                raise ExperimentError(f"{trace_dir}: missing trace_metadata.json or step_records.json")
            metadata = _load_json_object(metadata_path)
            steps = _load_json_array(steps_path)
            task_id = metadata.get("task_id")
            if not isinstance(task_id, str) or not task_id:
                raise ExperimentError(f"{metadata_path}: invalid task_id")
            trace_id = f"{dirname}/{trace_dir.name}"
            if trace_id in trace_ids:
                raise ExperimentError(f"duplicate trace_id {trace_id!r}")
            trace_ids.add(trace_id)
            released_system_name = metadata.get("system_name")
            if not isinstance(released_system_name, str) or normalize_text(released_system_name) != normalize_text(expected_system):
                raise ExperimentError(
                    f"{trace_id}: system {released_system_name!r} does not match {expected_system!r}"
                )
            step_ids = [step.get("step_id") for step in steps]
            if any(isinstance(value, bool) or not isinstance(value, int) for value in step_ids):
                raise ExperimentError(f"{trace_id}: non-integer step_id")
            if step_ids != list(range(1, len(steps) + 1)):
                raise ExperimentError(f"{trace_id}: step ids are not exactly 1..N")
            for step in steps:
                if SCORER_KEYS.intersection(step):
                    raise ExperimentError(f"{trace_id}: scorer key leaked into step record")
                if not isinstance(step.get("agent_name"), str):
                    raise ExperimentError(f"{trace_id}: step lacks string agent_name")
            visible = {key: metadata.get(key) for key in VISIBLE_META_KEYS}
            visible["system_name"] = expected_system
            rows.append(
                {
                    "trace_id": trace_id,
                    "cell": f"{expected_system}/{benchmark}",
                    "source_dir": dirname,
                    "trace_dir": trace_dir.name,
                    "released_system_name": released_system_name,
                    "metadata_relpath": str(metadata_path.relative_to(data_root)),
                    "steps_relpath": str(steps_path.relative_to(data_root)),
                    "step_count": len(steps),
                    **visible,
                }
            )
            trace_count += 1
            step_count += len(steps)
        observed[dirname] = {"traces": trace_count, "steps": step_count}
        if (trace_count, step_count) != (expected_traces, expected_steps):
            raise ExperimentError(
                f"{dirname}: {(trace_count, step_count)} != {(expected_traces, expected_steps)}"
            )
    rows.sort(key=lambda row: str(row["trace_id"]))
    if len(rows) != EXPECTED_TRACES or sum(int(row["step_count"]) for row in rows) != EXPECTED_STEPS:
        raise ExperimentError("official TraceElephant population total changed")
    manifest = out / "sources" / "visible-manifest.jsonl"
    write_jsonl(manifest, rows)
    summary = {
        "status": "ok",
        "traces": len(rows),
        "steps": sum(int(row["step_count"]) for row in rows),
        "cells": observed,
        "manifest": str(manifest),
        "manifest_sha256": hashlib.sha256(manifest.read_bytes()).hexdigest(),
        "scorer_keys_written": False,
    }
    write_json(out / "sources" / "visible-source-summary.json", summary)
    return summary


@dataclasses.dataclass
class TraceRecord:
    metadata: dict[str, Any]
    steps: list[dict[str, Any]]

    @property
    def trace_id(self) -> str:
        return str(self.metadata["trace_id"])

    @property
    def cell(self) -> str:
        return str(self.metadata["cell"])


def load_visible_traces(data_root: Path, out: Path) -> list[TraceRecord]:
    rows = read_jsonl(out / "sources" / "visible-manifest.jsonl")
    traces: list[TraceRecord] = []
    for row in rows:
        if SCORER_KEYS.intersection(row):
            raise ExperimentError("visible manifest contains scorer-only key")
        steps = _load_json_array(data_root / str(row["steps_relpath"]))
        if len(steps) != int(row["step_count"]):
            raise ExperimentError(f"{row['trace_id']}: step count changed")
        traces.append(TraceRecord(dict(row), steps))
    if len(traces) != EXPECTED_TRACES:
        raise ExperimentError(f"visible manifest has {len(traces)} traces")
    return traces


def choose_scope(traces: Sequence[TraceRecord], mode: str) -> list[TraceRecord]:
    if mode == "full":
        return list(traces)
    candidates = [trace for trace in traces if trace.cell == "Captain-Agent/AssistantBench"]
    if not candidates:
        raise ExperimentError("no Captain-Agent/AssistantBench preflight trace")
    return [min(candidates, key=lambda trace: trace.trace_id)]


def load_official_utils(official_code: Path) -> Any:
    path = official_code / "lib" / "utils.py"
    if not path.is_file():
        raise ExperimentError(f"missing official TraceElephant utils.py at {path}")
    spec = importlib.util.spec_from_file_location("traceelephant_official_utils", path)
    if spec is None or spec.loader is None:
        raise ExperimentError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def official_localizer_messages(trace: TraceRecord, official: Any) -> list[dict[str, str]]:
    history = []
    for step in trace.steps:
        history.append(
            {
                "name": step.get("agent_name", "Unknown"),
                "request": step.get("input", {}),
                "response": {"raw_output": step.get("output", "")},
            }
        )
    chat_content = official._format_chat_history(history, "name", 0, "response_only")
    prompt = official._build_all_at_once_prompt(
        trace.metadata.get("task_instruction", ""),
        trace.metadata.get("ground_truth", ""),
        chat_content,
        trace.metadata.get("tests_status"),
        trace.metadata.get("agent_system_intro", ""),
    )
    return [
        {"role": "system", "content": "You are a helpful assistant skilled in analyzing conversations."},
        {"role": "user", "content": prompt},
    ]


def _last_input_message(step: Mapping[str, Any]) -> str:
    value = step.get("input")
    if not isinstance(value, dict):
        return ""
    messages = value.get("messages")
    if not isinstance(messages, list) or not messages:
        return ""
    return canonical_json(messages[-1])


def _response_content(step: Mapping[str, Any]) -> str:
    output = step.get("output")
    if not isinstance(output, dict):
        return ""
    choices = output.get("choices")
    if not isinstance(choices, list):
        return ""
    for choice in choices:
        if not isinstance(choice, dict) or not isinstance(choice.get("message"), dict):
            continue
        content = choice["message"].get("content")
        if isinstance(content, str):
            return content
    return ""


def _output_tool_calls(step: Mapping[str, Any]) -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    output = step.get("output")
    choices = output.get("choices") if isinstance(output, dict) else None
    if not isinstance(choices, list):
        return selected
    for choice in choices:
        message = choice.get("message") if isinstance(choice, dict) else None
        calls = message.get("tool_calls") if isinstance(message, dict) else None
        if isinstance(calls, list):
            selected.extend(dict(call) for call in calls if isinstance(call, dict))
    return selected


def tag_messages(trace: TraceRecord, batch: Sequence[Mapping[str, Any]]) -> list[dict[str, str]]:
    rows = []
    for step in batch:
        rows.append(
            {
                "step": step["step_id"],
                "agent_name": step.get("agent_name", ""),
                "last_input": head_tail(_last_input_message(step), 600),
                "response": head_tail(_response_content(step), 600),
                "tool_calls": head_tail(canonical_json(_output_tool_calls(step)), 400),
                "tool_logs": head_tail(canonical_json(step.get("tool_logs")), 400),
            }
        )
    prompt = (
        TAG_INSTRUCTION
        + "\nTask instruction: "
        + head_tail(str(trace.metadata.get("task_instruction") or ""), 2000)
        + "\nAgent system introduction: "
        + head_tail(str(trace.metadata.get("agent_system_intro") or ""), 2000)
        + "\nAgent configuration: "
        + head_tail(canonical_json(trace.metadata.get("agent_configuration")), 2000)
        + "\nSteps: "
        + canonical_json(rows)
    )
    return [{"role": "user", "content": prompt}]


def chat_payload(messages: Sequence[Mapping[str, str]], model: str, max_tokens: int, seed: int) -> dict[str, Any]:
    return {
        "model": model,
        "messages": [dict(message) for message in messages],
        "temperature": 0.0,
        "top_p": 1.0,
        "max_tokens": max_tokens,
        "seed": seed,
        "stream": False,
        "reasoning_format": "none",
        "chat_template_kwargs": {"enable_thinking": False},
    }


def materialize_requests(
    traces: Sequence[TraceRecord], official: Any, model: str, seed: int, out: Path
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    localizer: list[dict[str, Any]] = []
    tags: list[dict[str, Any]] = []
    for trace in traces:
        payload = chat_payload(official_localizer_messages(trace, official), model, 1024, seed)
        localizer.append(
            {
                "kind": "localizer",
                "request_id": trace.trace_id,
                "trace_id": trace.trace_id,
                "expected_steps": [int(step["step_id"]) for step in trace.steps],
                "request_sha256": sha256_text(canonical_json(payload)),
                "payload": payload,
            }
        )
        for batch_index, start in enumerate(range(0, len(trace.steps), 20)):
            batch = trace.steps[start : start + 20]
            payload = chat_payload(tag_messages(trace, batch), model, 2048, seed)
            tags.append(
                {
                    "kind": "tagger",
                    "request_id": f"{trace.trace_id}:batch-{batch_index:03d}",
                    "trace_id": trace.trace_id,
                    "batch_index": batch_index,
                    "expected_steps": [int(step["step_id"]) for step in batch],
                    "request_sha256": sha256_text(canonical_json(payload)),
                    "payload": payload,
                }
            )
    write_jsonl(out / "requests" / "localizer.jsonl", localizer)
    write_jsonl(out / "requests" / "tagger.jsonl", tags)
    return localizer, tags


def _native_base(base_url: str) -> str:
    value = base_url.rstrip("/")
    return value[:-3] if value.endswith("/v1") else value


def _post_json(url: str, body: Mapping[str, Any], timeout: float) -> dict[str, Any]:
    request = urllib.request.Request(
        url,
        data=canonical_json(dict(body)).encode("utf-8"),
        headers={"Content-Type": "application/json", "User-Agent": "AgentProf-TraceElephant/1"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            value = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        detail = error.read().decode("utf-8", errors="replace")
        raise RetryableResponseError(f"HTTP {error.code} from {url}: {detail}") from error
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as error:
        raise RetryableResponseError(f"request failed for {url}: {error}") from error
    if not isinstance(value, dict):
        raise RetryableResponseError(f"{url}: expected object response")
    return value


def _get_json(url: str, timeout: float) -> dict[str, Any]:
    request = urllib.request.Request(url, headers={"User-Agent": "AgentProf-TraceElephant/1"})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            value = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as error:
        raise ExperimentError(f"failed to read {url}: {error}") from error
    if not isinstance(value, dict):
        raise ExperimentError(f"{url}: expected object response")
    return value


def validate_server(base_url: str, timeout: float, out: Path) -> dict[str, Any]:
    models = _get_json(base_url.rstrip("/") + "/models", timeout)
    props = _get_json(_native_base(base_url) + "/props", timeout)
    settings = props.get("default_generation_settings")
    props_ctx = settings.get("n_ctx") if isinstance(settings, dict) else None
    data = models.get("data")
    model_ctx = None
    if isinstance(data, list) and data and isinstance(data[0], dict):
        meta = data[0].get("meta")
        model_ctx = meta.get("n_ctx") if isinstance(meta, dict) else None
    if props_ctx != CONTEXT_WINDOW or model_ctx != CONTEXT_WINDOW:
        raise ExperimentError(f"llama.cpp context changed: props={props_ctx}, model={model_ctx}")
    write_json(out / "sources" / "model-metadata.json", models)
    write_json(out / "sources" / "server-properties.json", props)
    return {"props_n_ctx": props_ctx, "model_n_ctx": model_ctx, "expected": CONTEXT_WINDOW}


def tokenize_requests(
    requests: Sequence[Mapping[str, Any]], base_url: str, timeout: float, out: Path, name: str
) -> dict[str, Any]:
    apply_url = _native_base(base_url) + "/apply-template"
    tokenize_url = _native_base(base_url) + "/tokenize"
    rows: list[dict[str, Any]] = []
    for request in requests:
        payload = request["payload"]
        templated = _post_json(apply_url, payload, timeout)
        prompt = templated.get("prompt")
        if not isinstance(prompt, str):
            raise ExperimentError(f"{request['request_id']}: apply-template omitted prompt")
        tokenized = _post_json(
            tokenize_url, {"content": prompt, "add_special": True, "parse_special": True}, timeout
        )
        tokens = tokenized.get("tokens")
        if not isinstance(tokens, list) or any(isinstance(item, bool) or not isinstance(item, int) for item in tokens):
            raise ExperimentError(f"{request['request_id']}: tokenize omitted integer tokens")
        reserve = int(payload["max_tokens"])
        row = {
            "request_id": request["request_id"],
            "prompt_tokens": len(tokens),
            "output_reserve": reserve,
            "total_tokens": len(tokens) + reserve,
            "fits": len(tokens) + reserve <= CONTEXT_WINDOW,
            "templated_prompt_sha256": sha256_text(prompt),
            "request_sha256": request["request_sha256"],
        }
        rows.append(row)
    write_jsonl(out / "requests" / f"{name}-tokenization.jsonl", rows)
    failures = [row for row in rows if not row["fits"]]
    summary = {
        "requests": len(rows),
        "all_fit": not failures,
        "max_prompt_tokens": max((int(row["prompt_tokens"]) for row in rows), default=0),
        "context": CONTEXT_WINDOW,
    }
    write_json(out / "requests" / f"{name}-tokenization-summary.json", summary)
    if failures:
        raise ExperimentError(f"{name}: {len(failures)} approved requests exceed context")
    return summary


def assistant_content(response: Mapping[str, Any]) -> str:
    choices = response.get("choices")
    if not isinstance(choices, list) or not choices or not isinstance(choices[0], dict):
        raise RetryableResponseError("chat response omitted choices[0]")
    message = choices[0].get("message")
    content = message.get("content") if isinstance(message, dict) else None
    if not isinstance(content, str) or not content.strip():
        raise RetryableResponseError("chat response omitted assistant content")
    return content


def parse_json_object(text: str) -> dict[str, Any]:
    candidates = [text.strip()]
    candidates.extend(match.group(1).strip() for match in re.finditer(r"```(?:json)?\s*(.*?)```", text, re.S | re.I))
    decoder = json.JSONDecoder()
    for candidate in candidates:
        try:
            value = json.loads(candidate)
        except json.JSONDecodeError:
            start = candidate.find("{")
            if start < 0:
                continue
            try:
                value, _ = decoder.raw_decode(candidate[start:])
            except json.JSONDecodeError:
                continue
        if isinstance(value, dict):
            return value
    raise RetryableResponseError("assistant content contained no JSON object")


def parse_localizer(text: str) -> dict[str, Any]:
    value = parse_json_object(text)
    agent = value.get("agent_name")
    step = value.get("step_number")
    reason = value.get("reason")
    if not isinstance(agent, str) or not agent.strip():
        raise RetryableResponseError("localizer agent_name is invalid")
    if isinstance(step, bool) or not isinstance(step, int):
        raise RetryableResponseError("localizer step_number is not an integer")
    if not isinstance(reason, str):
        raise RetryableResponseError("localizer reason is not a string")
    return {"predicted_agent": agent, "predicted_step": step, "reason": reason}


def parse_tags(text: str, expected_steps: Sequence[int]) -> list[dict[str, Any]]:
    value = parse_json_object(text)
    if set(value) != {"steps"} or not isinstance(value["steps"], list):
        raise RetryableResponseError("tagger output must contain only array key steps")
    rows = value["steps"]
    if len(rows) != len(expected_steps):
        raise RetryableResponseError("tagger output length mismatch")
    parsed: list[dict[str, Any]] = []
    for expected, row in zip(expected_steps, rows, strict=True):
        if not isinstance(row, dict) or set(row) != {"step", "role", "intent", "status"}:
            raise RetryableResponseError("tagger item schema mismatch")
        if row["step"] != expected or isinstance(row["step"], bool):
            raise RetryableResponseError("tagger step order mismatch")
        if not all(isinstance(row[field], str) for field in ("role", "intent", "status")):
            raise RetryableResponseError("tagger enum values must be strings")
        if row["role"] not in ROLES or row["intent"] not in INTENTS or row["status"] not in STATUSES:
            raise RetryableResponseError("tagger enum mismatch")
        parsed.append(dict(row))
    return parsed


def response_path(out: Path, kind: str, request_id: str) -> Path:
    digest = sha256_text(request_id)[:24]
    return out / "responses" / kind / f"{digest}.json"


def collect_request(
    request: Mapping[str, Any], base_url: str, timeout: float, attempts: int, out: Path, resume: bool
) -> dict[str, Any]:
    kind = str(request["kind"])
    path = response_path(out, kind, str(request["request_id"]))
    if resume and path.is_file():
        cached = read_json(path)
        if (
            isinstance(cached, dict)
            and cached.get("terminal") is True
            and cached.get("request_sha256") == request["request_sha256"]
            and cached.get("request_id") == request["request_id"]
        ):
            return cached
        raise ExperimentError(f"stale or malformed terminal cache {path}")
    errors: list[str] = []
    raw_attempts: list[dict[str, Any]] = []
    parsed: Any = None
    for attempt in range(1, attempts + 1):
        try:
            response = _post_json(base_url.rstrip("/") + "/chat/completions", request["payload"], timeout)
            content = assistant_content(response)
            parsed = parse_localizer(content) if kind == "localizer" else parse_tags(content, request["expected_steps"])
            raw_attempts.append({"attempt": attempt, "response": response, "content": content, "success": True})
            break
        except (RetryableResponseError, OSError) as error:
            errors.append(str(error))
            raw_attempts.append({"attempt": attempt, "error": str(error), "success": False})
    if parsed is None:
        if kind == "localizer":
            parsed = {"predicted_agent": "", "predicted_step": None, "reason": ""}
            status = "terminal_no_hit"
        else:
            parsed = [
                {"step": int(step), "role": "unknown", "intent": "unknown", "status": "unclear"}
                for step in request["expected_steps"]
            ]
            status = "terminal_fallback"
    else:
        status = "success"
    record = {
        "request_id": request["request_id"],
        "trace_id": request["trace_id"],
        "kind": kind,
        "request_sha256": request["request_sha256"],
        "terminal": True,
        "status": status,
        "parsed": parsed,
        "errors": errors,
        "attempts": raw_attempts,
    }
    write_json(path, record)
    return record


def collect_all_requests(
    requests: Sequence[Mapping[str, Any]], base_url: str, timeout: float, attempts: int, out: Path, resume: bool
) -> list[dict[str, Any]]:
    return [collect_request(request, base_url, timeout, attempts, out, resume) for request in requests]


def _valid_calls(value: Any) -> list[dict[str, Any]]:
    calls: list[dict[str, Any]] = []
    if not isinstance(value, list):
        return calls
    for call in value:
        function = call.get("function") if isinstance(call, dict) else None
        name = function.get("name") if isinstance(function, dict) else None
        if isinstance(name, str) and normalize_text(name):
            calls.append(dict(call))
    return calls


def selected_raw_calls(step: Mapping[str, Any]) -> list[dict[str, Any]]:
    output_calls: list[dict[str, Any]] = []
    output = step.get("output")
    choices = output.get("choices") if isinstance(output, dict) else None
    if isinstance(choices, list):
        for choice in choices:
            message = choice.get("message") if isinstance(choice, dict) else None
            output_calls.extend(_valid_calls(message.get("tool_calls") if isinstance(message, dict) else None))
    if output_calls:
        return output_calls
    return _valid_calls(step.get("tool_logs"))


def _parse_argument_object(value: Any) -> dict[str, Any] | None:
    if isinstance(value, dict):
        return dict(value)
    if isinstance(value, str):
        try:
            decoded = json.loads(value)
        except json.JSONDecodeError:
            return None
        return dict(decoded) if isinstance(decoded, dict) else None
    return None


def raw_action(step: Mapping[str, Any]) -> str:
    identities: list[str] = []
    for call in selected_raw_calls(step):
        function = call["function"]
        normalized = normalize_text(str(function["name"]))
        encoded = normalized.replace("%", "%25").replace("+", "%2B").replace(":", "%3A")
        if normalized == "str_replace_editor":
            arguments = _parse_argument_object(function.get("arguments"))
            command = arguments.get("command") if isinstance(arguments, dict) else None
            command = normalize_text(command) if isinstance(command, str) else ""
            if command in EDITOR_COMMANDS:
                encoded += ":" + command
        identities.append(encoded)
    if identities:
        return "+".join(identities)
    output = step.get("output")
    choices = output.get("choices") if isinstance(output, dict) else None
    if isinstance(choices, list):
        for choice in choices:
            finish = choice.get("finish_reason") if isinstance(choice, dict) else None
            if isinstance(finish, str):
                normalized = normalize_text(finish)
                if normalized:
                    return "response:" + normalized
    return "response:unknown"


def derive_operations(
    traces: Sequence[TraceRecord],
    localizer_records: Sequence[Mapping[str, Any]],
    tag_records: Sequence[Mapping[str, Any]],
    out: Path,
) -> list[dict[str, Any]]:
    localizers = {str(row["trace_id"]): row for row in localizer_records}
    tags: dict[tuple[str, int], dict[str, Any]] = {}
    for record in tag_records:
        for row in record["parsed"]:
            key = (str(record["trace_id"]), int(row["step"]))
            if key in tags:
                raise ExperimentError(f"duplicate tag row {key}")
            tags[key] = dict(row)
    operations: list[dict[str, Any]] = []
    for trace in sorted(traces, key=lambda item: item.trace_id):
        localizer = localizers.get(trace.trace_id)
        if localizer is None:
            raise ExperimentError(f"{trace.trace_id}: missing terminal localizer")
        predicted = localizer["parsed"].get("predicted_step")
        valid_prediction = isinstance(predicted, int) and not isinstance(predicted, bool) and 1 <= predicted <= len(trace.steps)
        for step in trace.steps:
            step_id = int(step["step_id"])
            tag = tags.get((trace.trace_id, step_id))
            if tag is None:
                raise ExperimentError(f"{trace.trace_id}:{step_id}: missing terminal tag")
            raw_fields = {
                "system": str(trace.metadata["system_name"]),
                "role": str(tag["role"]),
                "intent": str(tag["intent"]),
                "component": str(step["agent_name"]),
                "raw_action": raw_action(step),
                "status": str(tag["status"]),
                "trace_id": trace.trace_id,
            }
            encoded_fields = {key: hex_encode(value) for key, value in raw_fields.items()}
            if any(hex_decode(encoded_fields[key]) != value for key, value in raw_fields.items()):
                raise ExperimentError(f"{trace.trace_id}:{step_id}: field encoding round-trip failed")
            operations.append(
                {
                    "operation_id": f"{trace.trace_id}#step-{step_id}",
                    "trace_id": trace.trace_id,
                    "cell": trace.cell,
                    "step_id": step_id,
                    "localizer_hit": int(valid_prediction and predicted == step_id),
                    "raw_fields": raw_fields,
                    "encoded_fields": encoded_fields,
                }
            )
    if len(operations) != sum(len(trace.steps) for trace in traces):
        raise ExperimentError("operation count mismatch")
    operation_ids = [str(row["operation_id"]) for row in operations]
    if len(operation_ids) != len(set(operation_ids)):
        raise ExperimentError("duplicate operation id")
    write_jsonl(out / "operations" / "projection.jsonl", operations)
    return operations


def write_operation_files(
    operations: Sequence[Mapping[str, Any]], count_path: Path, shifted_path: Path
) -> None:
    write_jsonl(
        count_path,
        ({"value": 1, "fields": dict(operation["encoded_fields"])} for operation in operations),
    )
    write_jsonl(
        shifted_path,
        (
            {"value": 1 + int(operation["localizer_hit"]), "fields": dict(operation["encoded_fields"])}
            for operation in operations
        ),
    )


def stack_key(operation: Mapping[str, Any], fields: Sequence[str]) -> str:
    return ";".join(f"{field}:{operation['encoded_fields'][field]}" for field in fields)


def agentprof_version(binary: Path) -> str:
    try:
        completed = subprocess.run(
            [str(binary), "--version"], check=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
    except (OSError, subprocess.CalledProcessError) as error:
        raise ExperimentError(f"failed to execute AgentProf: {error}") from error
    version = completed.stdout.strip()
    if version != AGENTPROF_VERSION:
        raise ExperimentError(f"expected {AGENTPROF_VERSION!r}, got {version!r}")
    return version


def invoke_agentprof(
    binary: Path, operation_path: Path, output_path: Path, fields: Sequence[str]
) -> collections.Counter[str]:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    command = [
        str(binary),
        "--operation-file",
        str(operation_path),
        "--view",
        "operations",
        "--format",
        "json",
        "--output",
        str(output_path),
        "--stack",
        ",".join(fields),
        "--deterministic-output",
    ]
    try:
        completed = subprocess.run(
            command, check=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        status = json.loads(completed.stdout)
    except (OSError, subprocess.CalledProcessError, json.JSONDecodeError) as error:
        detail = error.stderr if isinstance(error, subprocess.CalledProcessError) else str(error)
        raise ExperimentError(f"AgentProf failed: {detail}") from error
    if not isinstance(status, dict) or status.get("status") != "ok":
        raise ExperimentError(f"AgentProf returned non-ok status: {status}")
    profile = read_json(output_path)
    stacks = profile.get("profile", {}).get("stacks") if isinstance(profile, dict) else None
    if not isinstance(stacks, dict):
        raise ExperimentError(f"{output_path}: missing profile.stacks")
    result: collections.Counter[str] = collections.Counter()
    for key, value in stacks.items():
        if not isinstance(key, str) or isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise ExperimentError(f"{output_path}: invalid stack counter")
        result[key] = value
    return result


def prefix_counters_from_leaves(
    leaves: Mapping[str, int], depth: int
) -> list[collections.Counter[str]]:
    counters = [collections.Counter() for _ in range(depth)]
    for leaf, value in leaves.items():
        frames = leaf.split(";")
        if len(frames) != depth:
            raise ExperimentError(f"AgentProf leaf has {len(frames)} frames, expected {depth}: {leaf}")
        for index in range(depth):
            counters[index][";".join(frames[: index + 1])] += int(value)
    return counters


def independent_prefix_counters(
    operations: Sequence[Mapping[str, Any]], fields: Sequence[str]
) -> tuple[list[collections.Counter[str]], list[collections.Counter[str]]]:
    counts = [collections.Counter() for _ in fields]
    hits = [collections.Counter() for _ in fields]
    for operation in operations:
        frames = stack_key(operation, fields).split(";")
        for index in range(len(fields)):
            prefix = ";".join(frames[: index + 1])
            counts[index][prefix] += 1
            hits[index][prefix] += int(operation["localizer_hit"])
    return counts, hits


def wilson_lower(hits: int, count: int) -> float:
    if count <= 0 or hits < 0 or hits > count:
        raise ExperimentError(f"invalid Wilson inputs h={hits}, n={count}")
    if hits == 0:
        return +0.0
    proportion = hits / count
    z2 = Z_975 * Z_975
    return (
        proportion
        + z2 / (2.0 * count)
        - Z_975 * math.sqrt((proportion * (1.0 - proportion) + z2 / (4.0 * count)) / count)
    ) / (1.0 + z2 / count)


def build_binary_profile(
    name: str,
    operations: Sequence[Mapping[str, Any]],
    fields: Sequence[str],
    count_path: Path,
    shifted_path: Path,
    binary: Path,
    profile_dir: Path,
) -> dict[str, Any]:
    count_leaves = invoke_agentprof(binary, count_path, profile_dir / "count.json", fields)
    shifted_leaves = invoke_agentprof(binary, shifted_path, profile_dir / "shifted.json", fields)
    expected_counts, expected_hits = independent_prefix_counters(operations, fields)
    observed_counts = prefix_counters_from_leaves(count_leaves, len(fields))
    observed_shifted = prefix_counters_from_leaves(shifted_leaves, len(fields))
    observed_hits = [collections.Counter() for _ in fields]
    for depth in range(len(fields)):
        unexpected = set(observed_shifted[depth]) - set(observed_counts[depth])
        if unexpected:
            raise ExperimentError(f"{name}: shifted profile has unexpected prefixes")
        for prefix, count in observed_counts[depth].items():
            shifted = int(observed_shifted[depth].get(prefix, 0))
            if shifted < count:
                raise ExperimentError(f"{name}: shifted value below count")
            observed_hits[depth][prefix] = shifted - count
        if observed_counts[depth] != expected_counts[depth] or observed_hits[depth] != expected_hits[depth]:
            raise ExperimentError(f"{name}: real binary prefix reconstruction mismatch at depth {depth + 1}")
    expected_leaves = collections.Counter(stack_key(operation, fields) for operation in operations)
    if count_leaves != expected_leaves:
        raise ExperimentError(f"{name}: real binary leaf assignment mismatch")
    if sum(count_leaves.values()) != len(operations):
        raise ExperimentError(f"{name}: sample conservation failed")
    leaf_scores: dict[str, str] = {}
    for leaf in sorted(count_leaves):
        frames = leaf.split(";")
        scores = []
        for depth in range(len(fields)):
            prefix = ";".join(frames[: depth + 1])
            scores.append(wilson_lower(observed_hits[depth][prefix], observed_counts[depth][prefix]))
        leaf_scores[leaf] = max(scores).hex()
    operation_leaves = [stack_key(operation, fields) for operation in operations]
    return {
        "name": name,
        "fields": list(fields),
        "operations": len(operations),
        "groups": len(count_leaves),
        "operation_leaves": operation_leaves,
        "leaf_scores": leaf_scores,
        "count_total": sum(count_leaves.values()),
        "shifted_total": sum(shifted_leaves.values()),
        "localizer_hits": sum(int(row["localizer_hit"]) for row in operations),
        "real_binary_exact": True,
    }


def gzip_and_remove(path: Path) -> Path:
    target = path.with_suffix(path.suffix + ".gz")
    with path.open("rb") as source, gzip.open(target, "wb") as output:
        while chunk := source.read(1024 * 1024):
            output.write(chunk)
    path.unlink()
    return target


def _prefix_count_signature(
    operations: Sequence[Mapping[str, Any]], fields: Sequence[str]
) -> list[dict[str, int]]:
    counts, _ = independent_prefix_counters(operations, fields)
    return [{key: int(value) for key, value in sorted(counter.items())} for counter in counts]


def permuted_operations(
    operations: Sequence[Mapping[str, Any]], index: int, base_seed: int
) -> list[dict[str, Any]]:
    result = [
        {
            **dict(operation),
            "raw_fields": dict(operation["raw_fields"]),
            "encoded_fields": dict(operation["encoded_fields"]),
        }
        for operation in operations
    ]
    leaves: dict[str, list[int]] = collections.defaultdict(list)
    for offset, operation in enumerate(result):
        raw_leaf = canonical_json(
            [operation["raw_fields"][field] for field in ("system", "component", "raw_action")]
        )
        leaves[raw_leaf].append(offset)
    for raw_leaf in sorted(leaves):
        offsets = leaves[raw_leaf]
        tuples = [
            tuple(result[offset]["raw_fields"][field] for field in ("role", "intent", "status"))
            for offset in offsets
        ]
        material = f"{base_seed}\0{index}\0{raw_leaf}".encode("utf-8")
        derived = int.from_bytes(hashlib.sha256(material).digest()[:8], "big", signed=False)
        random.Random(derived).shuffle(tuples)
        for offset, values in zip(offsets, tuples, strict=True):
            for field, value in zip(("role", "intent", "status"), values, strict=True):
                result[offset]["raw_fields"][field] = value
                result[offset]["encoded_fields"][field] = hex_encode(value)
    return result


def materialize_profiles_and_controls(
    operations: Sequence[Mapping[str, Any]], binary: Path, out: Path, seed: int
) -> dict[str, Any]:
    operation_dir = out / "operations"
    count_path = operation_dir / "count.jsonl"
    shifted_path = operation_dir / "shifted.jsonl"
    write_operation_files(operations, count_path, shifted_path)
    proposed = build_binary_profile(
        "agentprof", operations, PROPOSED_STACK, count_path, shifted_path, binary, out / "profiles" / "agentprof"
    )
    raw = build_binary_profile(
        "raw", operations, RAW_STACK, count_path, shifted_path, binary, out / "profiles" / "raw"
    )
    session = build_binary_profile(
        "session", operations, SESSION_STACK, count_path, shifted_path, binary, out / "profiles" / "session"
    )
    source_native = build_binary_profile(
        "source_native",
        operations,
        SOURCE_NATIVE_STACK,
        count_path,
        shifted_path,
        binary,
        out / "profiles" / "source-native",
    )
    independent = {
        "name": "independent_step",
        "fields": ["operation_id"],
        "operations": len(operations),
        "groups": len(operations),
        "operation_leaves": [str(row["operation_id"]) for row in operations],
        "leaf_scores": {
            str(row["operation_id"]): float(int(row["localizer_hit"])).hex() for row in operations
        },
    }
    flat_score = wilson_lower(sum(int(row["localizer_hit"]) for row in operations), len(operations))
    flat = {
        "name": "flat",
        "fields": [],
        "operations": len(operations),
        "groups": 1,
        "operation_leaves": ["all"] * len(operations),
        "leaf_scores": {"all": flat_score.hex()},
    }
    leaf_widths = collections.Counter(proposed["operation_leaves"])
    width_only = {
        "name": "width_only",
        "fields": list(PROPOSED_STACK),
        "operations": len(operations),
        "groups": len(leaf_widths),
        "operation_leaves": list(proposed["operation_leaves"]),
        "leaf_scores": {leaf: (1.0 / width).hex() for leaf, width in leaf_widths.items()},
    }
    methods = {
        "agentprof": proposed,
        "raw": raw,
        "session": session,
        "source_native": source_native,
        "independent_step": independent,
        "flat": flat,
        "width_only": width_only,
    }
    original_leaf_counter = collections.Counter(proposed["operation_leaves"])
    original_prefix_signature = _prefix_count_signature(operations, PROPOSED_STACK)
    permutation_path = out / "permutations" / "profile-index.jsonl.gz"
    permutation_path.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(permutation_path, "wt", encoding="utf-8") as output:
        for index in range(1, 201):
            permuted = permuted_operations(operations, index, seed)
            if collections.Counter(stack_key(row, PROPOSED_STACK) for row in permuted) != original_leaf_counter:
                raise ExperimentError(f"permutation {index}: leaf-size invariant failed")
            if _prefix_count_signature(permuted, PROPOSED_STACK) != original_prefix_signature:
                raise ExperimentError(f"permutation {index}: prefix-topology/count invariant failed")
            working = out / "permutations" / "working"
            perm_count = working / "count.jsonl"
            perm_shifted = working / "shifted.jsonl"
            write_operation_files(permuted, perm_count, perm_shifted)
            profile_dir = out / "profiles" / "permutations" / f"perm-{index:03d}"
            profile = build_binary_profile(
                f"permutation_{index}", permuted, PROPOSED_STACK, perm_count, perm_shifted, binary, profile_dir
            )
            count_gz = gzip_and_remove(profile_dir / "count.json")
            shifted_gz = gzip_and_remove(profile_dir / "shifted.json")
            output.write(
                canonical_json(
                    {
                        "index": index,
                        "operation_leaves": profile["operation_leaves"],
                        "leaf_scores": profile["leaf_scores"],
                        "groups": profile["groups"],
                        "count_profile": str(count_gz),
                        "shifted_profile": str(shifted_gz),
                        "leaf_size_invariant": True,
                        "prefix_topology_count_invariant": True,
                    }
                )
                + "\n"
            )
            perm_count.unlink()
            perm_shifted.unlink()
    try:
        (out / "permutations" / "working").rmdir()
    except OSError:
        pass
    index = {
        "agentprof_version": agentprof_version(binary),
        "operations": [str(row["operation_id"]) for row in operations],
        "methods": methods,
        "exact_reconstruction": {
            "agentprof": proposed["real_binary_exact"],
            "raw": raw["real_binary_exact"],
        },
        "permutations": 200,
        "permutation_index": str(permutation_path),
    }
    write_json(out / "profiles" / "method-index.json", index)
    return index


def normalize_official_target_step(trace_id: str, step_raw: Any, reason_raw: Any) -> tuple[int, str]:
    if isinstance(step_raw, bool):
        raise ExperimentError(f"{trace_id}: invalid mistake_step")
    if isinstance(step_raw, int):
        return step_raw, "direct_integer"
    if not isinstance(step_raw, str):
        raise ExperimentError(f"{trace_id}: invalid mistake_step {step_raw!r}")
    normalized = normalize_text(step_raw)
    if re.fullmatch(r"[0-9]+", normalized):
        return int(normalized), "direct_digit_string"
    prefixed = re.fullmatch(r"step\s+([0-9]+)", normalized)
    if prefixed is not None:
        return int(prefixed.group(1)), "mistake_step_step_prefix"
    if normalized != "none" or not isinstance(reason_raw, str):
        raise ExperimentError(f"{trace_id}: invalid mistake_step {step_raw!r}")
    reason_steps = {
        int(value)
        for value in re.findall(
            r"\bstep\s+([0-9]+)\b", unicodedata.normalize("NFKC", reason_raw).casefold()
        )
    }
    if len(reason_steps) != 1:
        raise ExperimentError(
            f"{trace_id}: mistake_step is 'none' and mistake_reason has "
            f"{len(reason_steps)} unique Step N targets"
        )
    return next(iter(reason_steps)), "mistake_reason_unique_step"


def load_targets(
    data_root: Path, out: Path, selected_trace_ids: set[str]
) -> dict[str, dict[str, Any]]:
    manifest = read_jsonl(out / "sources" / "visible-manifest.jsonl")
    targets: dict[str, dict[str, Any]] = {}
    for row in manifest:
        trace_id = str(row["trace_id"])
        if trace_id not in selected_trace_ids:
            continue
        metadata = _load_json_object(data_root / str(row["metadata_relpath"]))
        agent = metadata.get("mistake_agent")
        step_raw = metadata.get("mistake_step")
        reason_raw = metadata.get("mistake_reason")
        if not isinstance(agent, str) or not agent.strip():
            raise ExperimentError(f"{trace_id}: invalid mistake_agent")
        step, normalization = normalize_official_target_step(trace_id, step_raw, reason_raw)
        if not 1 <= step <= int(row["step_count"]):
            raise ExperimentError(f"{trace_id}: target step {step} out of range")
        targets[trace_id] = {
            "trace_id": trace_id,
            "cell": row["cell"],
            "mistake_agent": agent,
            "mistake_step": step,
            "mistake_step_raw": step_raw,
            "mistake_step_normalization": normalization,
            "mistake_reason": reason_raw if isinstance(reason_raw, str) else None,
        }
    if set(targets) != selected_trace_ids:
        raise ExperimentError("scorer target population mismatch")
    write_jsonl(out / "scorer" / "targets.jsonl", (targets[key] for key in sorted(targets)))
    return targets


def validate_target_mapping(
    operations: Sequence[Mapping[str, Any]], targets: Mapping[str, Mapping[str, Any]], out: Path
) -> dict[str, Any]:
    by_trace_step: dict[tuple[str, int], list[Mapping[str, Any]]] = collections.defaultdict(list)
    for operation in operations:
        by_trace_step[(str(operation["trace_id"]), int(operation["step_id"]))].append(operation)
    rows: list[dict[str, Any]] = []
    for trace_id in sorted(targets):
        target = targets[trace_id]
        matches = by_trace_step.get((trace_id, int(target["mistake_step"])), [])
        operation_component = None
        if len(matches) == 1:
            raw_fields = matches[0].get("raw_fields")
            operation_component = raw_fields.get("component") if isinstance(raw_fields, dict) else None
        component_matches = (
            isinstance(operation_component, str)
            and normalize_text(operation_component) == normalize_text(str(target["mistake_agent"]))
        )
        step_mapping_valid = len(matches) == 1
        rows.append(
            {
                "trace_id": trace_id,
                "mistake_step": int(target["mistake_step"]),
                "mistake_step_raw": target["mistake_step_raw"],
                "mistake_step_normalization": target["mistake_step_normalization"],
                "mistake_reason": target["mistake_reason"],
                "mistake_agent": str(target["mistake_agent"]),
                "operation_count_at_step": len(matches),
                "operation_component": operation_component,
                "step_mapping_valid": step_mapping_valid,
                "component_annotation_consistent": component_matches,
                "normalized_component_matches_agent": component_matches,
                "valid": step_mapping_valid,
            }
        )
    normalization_counts = collections.Counter(
        str(row["mistake_step_normalization"]) for row in rows
    )
    component_mismatches = [row for row in rows if not row["component_annotation_consistent"]]
    report = {
        "traces": len(rows),
        "valid_traces": sum(bool(row["valid"]) for row in rows),
        "all_valid": all(bool(row["valid"]) for row in rows),
        "normalization_counts": dict(sorted(normalization_counts.items())),
        "component_consistent_traces": len(rows) - len(component_mismatches),
        "component_mismatch_traces": len(component_mismatches),
        "component_mismatch_rows": component_mismatches,
        "rows": rows,
    }
    write_json(out / "scorer" / "target-mapping.json", report)
    return report


def _method_operation_scores(method: Mapping[str, Any]) -> list[str]:
    leaves = method.get("operation_leaves")
    scores = method.get("leaf_scores")
    if not isinstance(leaves, list) or not isinstance(scores, dict):
        raise ExperimentError(f"method {method.get('name')}: invalid index")
    result = []
    for leaf in leaves:
        score = scores.get(leaf)
        if not isinstance(score, str):
            raise ExperimentError(f"method {method.get('name')}: missing leaf score")
        try:
            float.fromhex(score)
        except ValueError as error:
            raise ExperimentError(f"method {method.get('name')}: invalid score {score}") from error
        result.append(score)
    return result


def evaluate_scores(
    operations: Sequence[Mapping[str, Any]], score_hexes: Sequence[str], targets: Mapping[str, Mapping[str, Any]]
) -> dict[str, Any]:
    if len(operations) != len(score_hexes):
        raise ExperimentError("operation/score length mismatch")
    target_indices: dict[int, str] = {}
    seen_targets: set[str] = set()
    cell_totals = collections.Counter(str(target["cell"]) for target in targets.values())
    tiers: dict[str, list[int]] = collections.defaultdict(list)
    for index, (operation, score) in enumerate(zip(operations, score_hexes, strict=True)):
        tiers[score].append(index)
        target = targets.get(str(operation["trace_id"]))
        if target is not None and int(operation["step_id"]) == int(target["mistake_step"]):
            if str(operation["trace_id"]) in seen_targets:
                raise ExperimentError(f"duplicate target operation for {operation['trace_id']}")
            seen_targets.add(str(operation["trace_id"]))
            target_indices[index] = str(target["cell"])
    if seen_targets != set(targets):
        raise ExperimentError("one or more scorer targets do not map to an operation")
    ordered = sorted(tiers, key=lambda item: float.fromhex(item), reverse=True)
    selected = 0
    found = collections.Counter()
    curve: list[dict[str, Any]] = []
    for score in ordered:
        indices = tiers[score]
        selected += len(indices)
        for index in indices:
            if index in target_indices:
                found[target_indices[index]] += 1
        per_cell = {
            cell: found[cell] / cell_totals[cell] for cell in sorted(cell_totals)
        }
        macro = sum(per_cell.values()) / len(per_cell)
        micro = sum(found.values()) / sum(cell_totals.values())
        curve.append(
            {
                "score_hex": score,
                "score": float.fromhex(score),
                "work_count": selected,
                "work_fraction": selected / len(operations),
                "macro_recall": macro,
                "micro_recall": micro,
                "per_cell_recall": per_cell,
            }
        )
    if not curve or curve[-1]["work_count"] != len(operations) or curve[-1]["macro_recall"] != 1.0:
        raise ExperimentError("method curve does not terminate at full work/full recall")

    def first_at_recall(threshold: float) -> dict[str, Any]:
        for row in curve:
            if float(row["macro_recall"]) >= threshold:
                return dict(row)
        return dict(curve[-1])

    def recall_at_budget(budget: float) -> dict[str, Any]:
        eligible = [row for row in curve if float(row["work_fraction"]) <= budget]
        return dict(eligible[-1]) if eligible else {
            "work_count": 0,
            "work_fraction": 0.0,
            "macro_recall": 0.0,
            "micro_recall": 0.0,
            "per_cell_recall": {cell: 0.0 for cell in sorted(cell_totals)},
        }

    return {
        "operations": len(operations),
        "groups": len(set(score_hexes)),
        "score_tiers": len(ordered),
        "work_at_macro_recall": {
            "0.5": first_at_recall(0.5),
            "0.8": first_at_recall(0.8),
            "0.9": first_at_recall(0.9),
        },
        "recall_at_work": {
            "0.1": recall_at_budget(0.1),
            "0.2": recall_at_budget(0.2),
            "0.3": recall_at_budget(0.3),
        },
        "curve": curve,
    }


def evaluate_methods(
    operations: Sequence[Mapping[str, Any]], method_index: Mapping[str, Any], targets: Mapping[str, Mapping[str, Any]]
) -> dict[str, Any]:
    methods = method_index.get("methods")
    if not isinstance(methods, dict):
        raise ExperimentError("method index omitted methods")
    results: dict[str, Any] = {}
    for name, method in methods.items():
        if not isinstance(method, dict):
            raise ExperimentError(f"invalid method index {name}")
        results[str(name)] = evaluate_scores(operations, _method_operation_scores(method), targets)
    oracle_scores = []
    for operation in operations:
        target = targets.get(str(operation["trace_id"]))
        is_target = target is not None and int(operation["step_id"]) == int(target["mistake_step"])
        oracle_scores.append(float(int(is_target)).hex())
    results["oracle"] = evaluate_scores(operations, oracle_scores, targets)
    return results


def evaluate_permutations(
    operations: Sequence[Mapping[str, Any]], targets: Mapping[str, Mapping[str, Any]], method_index: Mapping[str, Any], out: Path
) -> dict[str, Any]:
    actual = evaluate_scores(
        operations, _method_operation_scores(method_index["methods"]["agentprof"]), targets
    )["work_at_macro_recall"]["0.8"]["work_fraction"]
    path = Path(str(method_index["permutation_index"]))
    rows: list[dict[str, Any]] = []
    with gzip.open(path, "rt", encoding="utf-8") as source:
        for line in source:
            record = json.loads(line)
            scores = [record["leaf_scores"][leaf] for leaf in record["operation_leaves"]]
            metric = evaluate_scores(operations, scores, targets)
            rows.append(
                {
                    "index": int(record["index"]),
                    "work_fraction": metric["work_at_macro_recall"]["0.8"]["work_fraction"],
                }
            )
    if len(rows) != 200:
        raise ExperimentError(f"completed {len(rows)} matched permutations, expected 200")
    result_path = out / "metrics" / "permutation-work.jsonl.gz"
    result_path.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(result_path, "wt", encoding="utf-8") as output:
        for row in rows:
            output.write(canonical_json(row) + "\n")
    at_least_as_good = sum(float(row["work_fraction"]) <= float(actual) for row in rows)
    return {
        "actual_work_fraction": actual,
        "permutations": 200,
        "permutation_work_le_actual": at_least_as_good,
        "p": (1 + at_least_as_good) / 201,
        "engaged": at_least_as_good == 0,
        "raw_path": str(result_path),
    }


def localizer_accuracy(
    operations: Sequence[Mapping[str, Any]], targets: Mapping[str, Mapping[str, Any]], out: Path
) -> dict[str, Any]:
    by_trace: dict[str, Mapping[str, Any]] = {}
    for operation in operations:
        trace_id = str(operation["trace_id"])
        if trace_id in by_trace:
            continue
        record = read_json(response_path(out, "localizer", trace_id))
        if not isinstance(record, dict):
            raise ExperimentError(f"{trace_id}: invalid localizer record")
        by_trace[trace_id] = record
    agent_correct = 0
    step_correct = 0
    joint_correct = 0
    valid_step = 0
    for trace_id, target in targets.items():
        parsed = by_trace[trace_id]["parsed"]
        predicted_step = parsed.get("predicted_step")
        predicted_agent = parsed.get("predicted_agent")
        agent_match = isinstance(predicted_agent, str) and normalize_text(predicted_agent) == normalize_text(str(target["mistake_agent"]))
        step_match = isinstance(predicted_step, int) and not isinstance(predicted_step, bool) and predicted_step == target["mistake_step"]
        agent_correct += int(agent_match)
        step_correct += int(step_match)
        joint_correct += int(agent_match and step_match)
        valid_step += int(isinstance(predicted_step, int) and not isinstance(predicted_step, bool))
    total = len(targets)
    return {
        "traces": total,
        "valid_integer_step": valid_step,
        "agent_accuracy": agent_correct / total,
        "step_accuracy": step_correct / total,
        "joint_accuracy": joint_correct / total,
        "matching": "exact normalized agent and exact integer step",
    }


_BOOTSTRAP_STATE: dict[str, Any] | None = None
_BOOTSTRAP_SEED = 0


def _bootstrap_method_work(
    method: Mapping[str, Any], operations: Sequence[Mapping[str, Any]], multiplicity: Mapping[str, int],
    targets: Mapping[str, Mapping[str, Any]], cell_totals: Mapping[str, int]
) -> float:
    fields = tuple(str(field) for field in method["fields"])
    counts = [collections.Counter() for _ in fields]
    hits = [collections.Counter() for _ in fields]
    leaf_work = collections.Counter()
    for operation in operations:
        weight = int(multiplicity.get(str(operation["trace_id"]), 0))
        if not weight:
            continue
        frames = stack_key(operation, fields).split(";")
        leaf = ";".join(frames)
        leaf_work[leaf] += weight
        for depth in range(len(fields)):
            prefix = ";".join(frames[: depth + 1])
            counts[depth][prefix] += weight
            hits[depth][prefix] += weight * int(operation["localizer_hit"])
    score_cache: dict[tuple[int, int], float] = {}
    leaf_scores: dict[str, str] = {}
    for leaf in leaf_work:
        frames = leaf.split(";")
        path_scores = []
        for depth in range(len(fields)):
            prefix = ";".join(frames[: depth + 1])
            pair = (hits[depth][prefix], counts[depth][prefix])
            if pair not in score_cache:
                score_cache[pair] = wilson_lower(*pair)
            path_scores.append(score_cache[pair])
        leaf_scores[leaf] = max(path_scores).hex()
    work_by_score = collections.Counter()
    for leaf, weight in leaf_work.items():
        work_by_score[leaf_scores[leaf]] += weight
    target_by_score: dict[str, collections.Counter[str]] = collections.defaultdict(collections.Counter)
    operation_by_target = {
        (str(operation["trace_id"]), int(operation["step_id"])): operation for operation in operations
    }
    for trace_id, weight in multiplicity.items():
        if not weight:
            continue
        target = targets[trace_id]
        operation = operation_by_target[(trace_id, int(target["mistake_step"]))]
        leaf = stack_key(operation, fields)
        target_by_score[leaf_scores[leaf]][str(target["cell"])] += weight
    selected = 0
    found = collections.Counter()
    denominator = sum(int(multiplicity[str(operation["trace_id"])]) for operation in operations)
    for score in sorted(work_by_score, key=lambda item: float.fromhex(item), reverse=True):
        selected += work_by_score[score]
        found.update(target_by_score.get(score, {}))
        macro = sum(found[cell] / cell_totals[cell] for cell in sorted(cell_totals)) / len(cell_totals)
        if macro >= 0.8:
            return selected / denominator
    return 1.0


def _bootstrap_attempt(attempt: int) -> dict[str, Any]:
    if _BOOTSTRAP_STATE is None:
        raise ExperimentError("bootstrap state is not initialized")
    state = _BOOTSTRAP_STATE
    rng = random.Random(_BOOTSTRAP_SEED + attempt)
    multiplicity = collections.Counter()
    cell_totals: dict[str, int] = {}
    for cell in sorted(state["traces_by_cell"]):
        traces = state["traces_by_cell"][cell]
        cell_totals[cell] = len(traces)
        for _ in traces:
            multiplicity[rng.choice(traces)] += 1
    agent = _bootstrap_method_work(
        state["methods"]["agentprof"], state["operations"], multiplicity, state["targets"], cell_totals
    )
    raw = _bootstrap_method_work(
        state["methods"]["raw"], state["operations"], multiplicity, state["targets"], cell_totals
    )
    return {"attempt": attempt, "agentprof": agent, "raw": raw, "delta": agent - raw}


def nearest_rank_interval(values: Sequence[float]) -> list[float]:
    if len(values) != 10000:
        raise ExperimentError("nearest-rank interval requires exactly 10,000 values")
    ordered = sorted(float(value) for value in values)
    return [ordered[249], ordered[9749]]


def run_bootstrap(
    operations: Sequence[Mapping[str, Any]], targets: Mapping[str, Mapping[str, Any]], method_index: Mapping[str, Any],
    attempts: int, seed: int, workers: int, out: Path
) -> dict[str, Any]:
    if attempts != 10000:
        raise ExperimentError("FULL requires exactly 10,000 bootstrap replicates")
    traces_by_cell: dict[str, list[str]] = collections.defaultdict(list)
    for trace_id, target in targets.items():
        traces_by_cell[str(target["cell"])].append(trace_id)
    for traces in traces_by_cell.values():
        traces.sort()
    global _BOOTSTRAP_STATE, _BOOTSTRAP_SEED
    _BOOTSTRAP_STATE = {
        "operations": list(operations),
        "targets": dict(targets),
        "methods": {
            "agentprof": {"fields": list(PROPOSED_STACK)},
            "raw": {"fields": list(RAW_STACK)},
        },
        "traces_by_cell": dict(traces_by_cell),
    }
    _BOOTSTRAP_SEED = seed
    indices = list(range(attempts))
    if workers == 1:
        rows = [_bootstrap_attempt(index) for index in indices]
    else:
        with mp.get_context("fork").Pool(processes=workers) as pool:
            rows = pool.map(_bootstrap_attempt, indices, chunksize=16)
    path = out / "metrics" / "bootstrap-effects.jsonl.gz"
    path.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(path, "wt", encoding="utf-8") as output:
        for row in rows:
            output.write(canonical_json(row) + "\n")
    return {
        "requested": attempts,
        "completed": len(rows),
        "seed": seed,
        "workers": workers,
        "cell_draws": {cell: len(traces) for cell, traces in sorted(traces_by_cell.items())},
        "agentprof_interval": nearest_rank_interval([row["agentprof"] for row in rows]),
        "raw_interval": nearest_rank_interval([row["raw"] for row in rows]),
        "paired_delta_interval": nearest_rank_interval([row["delta"] for row in rows]),
        "raw_path": str(path),
    }


def scientific_verdict(
    mode: str, point: Mapping[str, Any], permutation: Mapping[str, Any], bootstrap: Mapping[str, Any] | None
) -> tuple[str | None, dict[str, Any], bool]:
    if mode == "preflight":
        return "PREFLIGHT_ONLY", {"evaluated": False}, True
    if bootstrap is None or int(bootstrap.get("completed", 0)) != 10000:
        return None, {"evaluated": False, "reason": "bootstrap incomplete"}, False
    agent = float(point["agentprof"]["work_at_macro_recall"]["0.8"]["work_fraction"])
    raw = float(point["raw"]["work_at_macro_recall"]["0.8"]["work_fraction"])
    lower, upper = [float(value) for value in bootstrap["paired_delta_interval"]]
    engaged = permutation.get("p") == 1 / 201 and permutation.get("engaged") is True
    details = {
        "evaluated": True,
        "agentprof_work": agent,
        "raw_work": raw,
        "point_delta": agent - raw,
        "paired_delta_interval": [lower, upper],
        "permutation_p": permutation.get("p"),
        "permutation_engaged": engaged,
    }
    point_delta = agent - raw
    inconsistent = (upper < 0.0 and point_delta >= 0.0) or (lower > 0.0 and point_delta <= 0.0)
    if not math.isfinite(lower) or not math.isfinite(upper) or lower > upper or inconsistent:
        details["numerical_inconsistency"] = True
        return None, details, False
    details["numerical_inconsistency"] = False
    if agent < raw and upper < 0.0 and engaged:
        return "SUPPORTED", details, True
    if lower > 0.0:
        return "CONTRADICTED", details, True
    return "INCONCLUSIVE", details, True


def render_result_markdown(summary: Mapping[str, Any]) -> str:
    lines = [
        f"# TraceElephant RQ2 {str(summary['mode']).upper()} Report",
        "",
        f"**Execution status:** {summary['execution_status']}",
        f"**Tested-hypothesis verdict:** {summary['scientific_verdict']}",
        "**RQ:** RQ2 — Does Profiler Output Correspond to Real Problems?",
        "",
        "## Population And Signal",
        "",
        f"- traces: {summary['completion']['traces']}",
        f"- operations: {summary['completion']['operations']}",
        f"- terminal localizer outputs: {summary['completion']['localizers']}",
        f"- terminal tag batches: {summary['completion']['tag_batches']}",
        f"- exact localizer step accuracy: {summary['localizer_accuracy']['step_accuracy']:.6f}",
        "",
        "## Work At 80% Macro Decisive-Step Recall",
        "",
        "| Method | Work fraction | Macro recall |",
        "|---|---:|---:|",
    ]
    for name, metric in summary["point_results"].items():
        selected = metric["work_at_macro_recall"]["0.8"]
        lines.append(f"| {name} | {selected['work_fraction']:.6f} | {selected['macro_recall']:.6f} |")
    lines.extend(
        [
            "",
            "## Mechanism And Uncertainty",
            "",
            f"- matched semantic permutations: {summary['permutation']['permutations']}",
            f"- permutation p: {summary['permutation']['p']:.9f}",
            f"- mechanism engaged: {summary['permutation']['engaged']}",
        ]
    )
    if summary.get("bootstrap"):
        lines.extend(
            [
                f"- paired AgentProf-minus-raw 95% interval: {summary['bootstrap']['paired_delta_interval']}",
                f"- completed bootstrap replicates: {summary['bootstrap']['completed']}",
            ]
        )
    lines.extend(
        [
            "",
            "## Interpretation Boundary",
            "",
            "- this result answers one fixed tested hypothesis inside RQ2, not the entire paper-level RQ",
            "- reference outcome enters only the shared released localizer; scorer annotations enter only this scorer process",
            "- preflight values are path checks and are never interpreted as scientific evidence",
            "",
        ]
    )
    return "\n".join(lines)


def score_run(args: argparse.Namespace) -> dict[str, Any]:
    out = Path(args.out).expanduser().resolve()
    data_root = Path(args.data_root).expanduser().resolve()
    operations = read_jsonl(out / "operations" / "projection.jsonl")
    selected_trace_ids = {str(row["trace_id"]) for row in operations}
    targets = load_targets(data_root, out, selected_trace_ids)
    target_mapping = validate_target_mapping(operations, targets, out)
    if args.validate_targets_only:
        if not target_mapping["all_valid"]:
            raise ExperimentError("one or more normalized target steps do not map uniquely")
        return {
            "status": "ok",
            "mode": args.run_mode,
            "targets": len(targets),
            "target_mapping": target_mapping,
            "metrics_computed": False,
        }
    if not target_mapping["all_valid"]:
        summary = {
            "mode": args.run_mode,
            "execution_status": "INVALID",
            "scientific_verdict": None,
            "verdict_details": {
                "evaluated": False,
                "reason": "one or more normalized target steps do not map to exactly one operation",
            },
            "target_mapping": target_mapping,
            "scorer_process_isolated": True,
        }
        write_json(out / "metrics" / f"summary-{args.run_mode}.json", summary)
        report_path = out / "metrics" / f"report-{args.run_mode}.md"
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(
            "# TraceElephant RQ2 Invalid Result\n\n"
            "Execution is `INVALID`: at least one normalized official mistake step does not map "
            "to exactly one operation. No scientific verdict or metric was computed.\n",
            encoding="utf-8",
        )
        return summary
    method_index = read_json(out / "profiles" / "method-index.json")
    if not isinstance(method_index, dict):
        raise ExperimentError("invalid method index")
    point = evaluate_methods(operations, method_index, targets)
    permutation = evaluate_permutations(operations, targets, method_index, out)
    bootstrap = None
    if args.run_mode == "full":
        bootstrap = run_bootstrap(
            operations, targets, method_index, args.bootstrap, args.seed, args.bootstrap_workers, out
        )
    accuracy = localizer_accuracy(operations, targets, out)
    verdict, verdict_details, verdict_valid = scientific_verdict(args.run_mode, point, permutation, bootstrap)
    expected_traces = EXPECTED_TRACES if args.run_mode == "full" else 1
    expected_steps = EXPECTED_STEPS if args.run_mode == "full" else len(operations)
    completion = {
        "traces": len(selected_trace_ids),
        "operations": len(operations),
        "localizers": len(selected_trace_ids),
        "tag_batches": sum(1 for _ in (out / "responses" / "tagger").glob("*.json")),
        "expected_traces": expected_traces,
        "expected_operations": expected_steps,
        "complete": len(selected_trace_ids) == expected_traces and len(operations) == expected_steps,
    }
    if not completion["complete"]:
        execution_status = "INCOMPLETE"
        verdict = None
    elif not verdict_valid:
        execution_status = "INVALID"
        verdict = None
    else:
        execution_status = "VALID"
    summary = {
        "mode": args.run_mode,
        "execution_status": execution_status,
        "scientific_verdict": verdict,
        "verdict_details": verdict_details,
        "completion": completion,
        "localizer_accuracy": accuracy,
        "target_mapping": target_mapping,
        "point_results": point,
        "permutation": permutation,
        "bootstrap": bootstrap,
        "scorer_process_isolated": True,
    }
    write_json(out / "metrics" / f"summary-{args.run_mode}.json", summary)
    report_path = out / "metrics" / f"report-{args.run_mode}.md"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(render_result_markdown(summary), encoding="utf-8")
    return summary


def archive_completed_preflight(out: Path) -> None:
    preflight_summary = out / "metrics" / "summary-preflight.json"
    full_summary = out / "metrics" / "summary-full.json"
    archive = out / "preflight"
    if not preflight_summary.is_file() or full_summary.exists() or archive.exists():
        return
    archive.mkdir(parents=True)
    for name in ("requests", "operations", "profiles", "permutations", "metrics", "scorer"):
        path = out / name
        if path.exists():
            shutil.move(str(path), str(archive / name))


def run_child(command: Sequence[str]) -> None:
    try:
        subprocess.run(list(command), check=True)
    except subprocess.CalledProcessError as error:
        raise ExperimentError(f"child process failed with status {error.returncode}: {' '.join(command)}") from error


def run_experiment(args: argparse.Namespace) -> dict[str, Any]:
    validate_cli(args)
    started = time.perf_counter()
    out = Path(args.out).expanduser().resolve()
    data_root = Path(args.data_root).expanduser().resolve()
    official_code = Path(args.official_code).expanduser().resolve()
    binary = Path(args.agentpprof_bin).expanduser().resolve()
    out.mkdir(parents=True, exist_ok=True)
    if args.mode == "full":
        archive_completed_preflight(out)
    run_child(
        [
            sys.executable,
            str(Path(__file__).resolve()),
            "_project-visible",
            "--data-root",
            str(data_root),
            "--out",
            str(out),
        ]
    )
    traces = load_visible_traces(data_root, out)
    selected = choose_scope(traces, args.mode)
    server = validate_server(args.base_url, args.timeout, out)
    version = agentprof_version(binary)
    official = load_official_utils(official_code)
    localizer_requests, tag_requests = materialize_requests(selected, official, args.model, args.seed, out)
    localizer_tokens = tokenize_requests(localizer_requests, args.base_url, args.timeout, out, "localizer")
    tag_tokens = tokenize_requests(tag_requests, args.base_url, args.timeout, out, "tagger")
    localizer_records = collect_all_requests(
        localizer_requests, args.base_url, args.timeout, args.attempts, out, args.resume
    )
    tag_records = collect_all_requests(
        tag_requests, args.base_url, args.timeout, args.attempts, out, args.resume
    )
    if args.mode == "preflight":
        if any(record.get("status") != "success" for record in localizer_records):
            raise ExperimentError("REAL PREFLIGHT requires a successful localizer response, not terminal no-hit")
        if any(record.get("status") != "success" for record in tag_records):
            raise ExperimentError("REAL PREFLIGHT requires every tag batch to parse successfully")
        expected = set(int(step) for step in localizer_requests[0]["expected_steps"])
        predicted = localizer_records[0]["parsed"].get("predicted_step")
        if isinstance(predicted, bool) or not isinstance(predicted, int) or predicted not in expected:
            raise ExperimentError("REAL PREFLIGHT localizer did not engage an in-range source step")
    operations = derive_operations(selected, localizer_records, tag_records, out)
    method_index = materialize_profiles_and_controls(operations, binary, out, args.seed)
    if len(method_index["methods"]["agentprof"]["operation_leaves"]) != len(operations):
        raise ExperimentError("profile index does not cover every operation")
    run_child(
        [
            sys.executable,
            str(Path(__file__).resolve()),
            "_score",
            "--run-mode",
            args.mode,
            "--data-root",
            str(data_root),
            "--out",
            str(out),
            "--bootstrap",
            str(args.bootstrap),
            "--bootstrap-workers",
            str(args.bootstrap_workers),
            "--seed",
            str(args.seed),
        ]
    )
    scientific = read_json(out / "metrics" / f"summary-{args.mode}.json")
    result = {
        "status": "ok",
        "mode": args.mode,
        "builder_scorer_process_separation": True,
        "source": read_json(out / "sources" / "visible-source-summary.json"),
        "server": server,
        "agentprof_version": version,
        "scope": {"traces": len(selected), "steps": len(operations)},
        "requests": {
            "localizer": len(localizer_requests),
            "tag_batches": len(tag_requests),
            "localizer_terminal": len(localizer_records),
            "tag_terminal": len(tag_records),
        },
        "tokenization": {"localizer": localizer_tokens, "tagger": tag_tokens},
        "scientific": scientific,
        "elapsed_seconds": time.perf_counter() - started,
        "command": " ".join(sys.argv),
    }
    write_json(out / f"run-{args.mode}.json", result)
    return result


def validate_cli(args: argparse.Namespace) -> None:
    if args.model_workers != 1:
        raise ExperimentError("approved plan requires exactly one model worker")
    if args.localizer_max_tokens != 1024 or args.tag_max_tokens != 2048:
        raise ExperimentError("approved output reserves are 1024 localizer and 2048 tagger tokens")
    if args.attempts != 3 or args.seed != 20260713:
        raise ExperimentError("approved plan requires attempts=3 and seed=20260713")
    if args.timeout <= 0 or args.bootstrap_workers <= 0:
        raise ExperimentError("timeout and bootstrap workers must be positive")
    if args.mode == "full" and (args.bootstrap != 10000 or not args.resume):
        raise ExperimentError("FULL requires --bootstrap 10000 and --resume")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("preflight", "full", "_project-visible", "_score"))
    parser.add_argument("--run-mode", choices=("preflight", "full"), default="preflight")
    parser.add_argument("--data-root", required=True)
    parser.add_argument("--official-code", default=".agentsight/sources/TraceElephant/code/trace_locate")
    parser.add_argument("--base-url", default="http://127.0.0.1:8012/v1")
    parser.add_argument("--model", default="local")
    parser.add_argument("--agentpprof-bin", default="agentpprof/target/release/agentpprof")
    parser.add_argument("--out", required=True)
    parser.add_argument("--model-workers", type=int, default=1)
    parser.add_argument("--bootstrap-workers", type=int, default=8)
    parser.add_argument("--localizer-max-tokens", type=int, default=1024)
    parser.add_argument("--tag-max-tokens", type=int, default=2048)
    parser.add_argument("--timeout", type=float, default=600.0)
    parser.add_argument("--attempts", type=int, default=3)
    parser.add_argument("--bootstrap", type=int, default=10000)
    parser.add_argument("--seed", type=int, default=20260713)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--validate-targets-only", action="store_true")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        if args.mode == "_project-visible":
            result = project_visible_source(
                Path(args.data_root).expanduser().resolve(), Path(args.out).expanduser().resolve()
            )
        elif args.mode == "_score":
            result = score_run(args)
        else:
            result = run_experiment(args)
    except ExperimentError as error:
        print(canonical_json({"status": "error", "error": str(error)}))
        return 1
    print(canonical_json({"status": "ok", "result": result}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
