#!/usr/bin/env python3
"""Evaluate task-rooted semantic planning against human workflow stages.

The ``infer`` process reconstructs public CodeTraceBench source without opening
the human-stage manifest.  A fixed local model first proposes reusable workflow
responsibilities from the task and then aligns each operation causally to that
plan.  A matched plan-free arm makes a causal stay-or-switch decision from
byte-identical current evidence.  The separate ``score`` process opens the
manifest and computes standard unlabeled span, B-cubed, and boundary metrics.
"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import html
import json
from pathlib import Path
import random
import re
import sys
import threading
import time
from typing import Any, Iterable

import requests


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "script"))

from codetracebench_agentprof_eval import (  # noqa: E402
    ADAPTERS,
    SourceError,
    load_json,
    load_openhands_call_records,
    load_openhands_events,
    tar_members,
    tar_text,
)
from rq3_codetracebench_stage_fidelity_eval import (  # noqa: E402
    bcubed,
    boundary_metrics,
    load_stages_after_prediction,
    percentile,
)
from rq3_qwen_semantic_task_stack_eval import (  # noqa: E402
    framework_for_session,
    load_visible_operations,
)


ALGORITHM_VERSION = "task-rooted-causal-stage-alignment-v7"
MODEL = "qwen2.5-3b-instruct-q4_k_m.gguf"
MODEL_PATH = Path(
    "/home/yunwei37/workspace/llama.cpp-latest/models/"
    "qwen2.5-3b-instruct-q4_k_m.gguf"
)
MODEL_SHA256 = "626b4a6678b86442240e33df819e00132d3ba7dddfe1cdc4fbb18e0a9615c62d"
EXPECTED_SESSIONS = 405
EXPECTED_OPERATIONS = 20_866
EXPECTED_STAGES = 2_948
EXPECTED_TASKS = 251
EXPECTED_FRAMEWORKS = {
    "mini-SWE-agent",
    "OpenHands",
    "SWE-agent",
    "Terminus2",
}
SEED = 20_260_720
BOOTSTRAP_RESAMPLES = 10_000
MAX_REQUEST_TOKENS = 8_192
TOKENIZER_PROJECTION_LIMIT = 8_000
PLANNER_OUTPUT_TOKENS = 2_048
CAUSAL_OUTPUT_TOKENS = 96
INITIAL_FIELD_CHARS = 2_400
MIN_FIELD_CHARS = 24
MIN_TASK_CHARS = 512
LABEL_MAX_CHARS = 64
VISIBLE_OPERATION_KEYS = {
    "step", "action_kind", "raw_action_key", "source_action", "preceding_observation"
}
PLANNER_SYSTEM = """Decompose one concrete agent task into stable workflow
responsibilities that can each own multiple operations. Return a nonempty JSON
array of concise lowercase verb phrases. Use task semantics, not agent, model,
session, tool, command, path, file extension, or success status. Do not describe
individual shell calls. Every item must begin with a task verb and name the
work's purpose. Rewrite any path, filename, line range, command placeholder, or
tool named in the request as its task intent. For example, write "repair object
detection loading", not "file /src/model.py"; write "verify maze solver", not
"test maze_1.txt". Check every item before returning. Use only as many
responsibilities as the task needs."""
ALIGN_SYSTEM = """Maintain one active workflow responsibility while reading an
agent trajectory causally. Choose exactly one item from the fixed task plan for
the current operation. Keep the preceding index by default when the operation
continues the same responsibility; switch only when the concrete work changes.
Return only {\"plan_index\":k}. Do not invent plan items."""
FLAT_SYSTEM = """Maintain one active semantic workflow stage while reading an
agent trajectory causally. Keep the current stage by default when the operation
continues the same concrete work. Switch only when a temporally extended new
workflow stage begins, and then name that stage with a concise lowercase verb
phrase. A stage owns multiple operations, not one command, tool, path, file,
status, agent, model, or session. Rewrite those details as their task purpose;
for example use "verify maze solver", not "test maze_1.txt". Return only the
required JSON decision."""
LABEL_RE = re.compile(r"^[a-z][a-z0-9 /+._-]*$")
PATH_RE = re.compile(r"(?:/[^\s'\";|]+|[A-Za-z0-9_.-]+\.(?:py|rs|c|h|md|json|ya?ml|toml|txt))")
_thread_local = threading.local()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    infer = subparsers.add_parser("infer")
    infer.add_argument("mode", choices=("preflight", "full"))
    infer.add_argument("--target-operations", type=Path, required=True)
    infer.add_argument("--raw-root", type=Path, required=True)
    infer.add_argument("--llama-url", required=True)
    infer.add_argument("--workers", type=int, default=4)
    infer.add_argument("--timeout-seconds", type=int, default=600)
    infer.add_argument("--out", type=Path, required=True)

    score = subparsers.add_parser("score")
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


def request_session() -> requests.Session:
    session = getattr(_thread_local, "requests_session", None)
    if session is None:
        session = requests.Session()
        _thread_local.requests_session = session
    return session


def clip_text(value: str | None, budget: int) -> str:
    if value is None:
        return "none"
    cleaned = value.strip()
    if not cleaned:
        return "none"
    if len(cleaned) <= budget:
        return cleaned
    left = (budget - 1) // 2
    right = budget - 1 - left
    return cleaned[:left] + "…" + cleaned[-right:]


def first_user_content(messages: Any) -> str | None:
    if not isinstance(messages, list):
        return None
    for message in messages:
        if not isinstance(message, dict) or message.get("role") != "user":
            continue
        content = message.get("content")
        if isinstance(content, str) and content.strip():
            return content.strip()
        if isinstance(content, list):
            parts = [
                str(block["text"]).strip()
                for block in content
                if isinstance(block, dict)
                and isinstance(block.get("text"), str)
                and str(block["text"]).strip()
            ]
            if parts:
                return "\n".join(parts)
    return None


def extract_task_text(
    archive: Path,
    members: list[str],
    framework: str,
) -> tuple[str, str]:
    if framework == "mini-SWE-agent":
        member = next((name for name in members if name.endswith(".traj.json")), None)
        if member:
            data = load_json(archive, member)
            task = first_user_content(data.get("messages") if isinstance(data, dict) else None)
            if task:
                return task, f"{member}#first-user"

    if framework == "SWE-agent":
        member = next((name for name in members if name.endswith(".traj")), None)
        if member:
            data = load_json(archive, member)
            trajectory = data.get("trajectory") if isinstance(data, dict) else None
            if isinstance(trajectory, list):
                for item in trajectory:
                    if not isinstance(item, dict):
                        continue
                    task = first_user_content(item.get("query"))
                    if task:
                        return task, f"{member}#first-user-query"

    if framework == "Terminus2":
        prompt = next(
            (
                name
                for name in members
                if name.endswith("/agent-logs/episode-0/prompt.txt")
            ),
            None,
        )
        if prompt:
            text = tar_text(archive, prompt)
            marker = "Task Description:\n"
            if marker in text and text.split(marker, 1)[1].strip():
                return text.split(marker, 1)[1].strip(), f"{prompt}#task-description"

    if framework == "OpenHands":
        calls = load_openhands_call_records(archive, members)
        if calls:
            _, _, member, record = max(calls, key=lambda row: (row[0], row[1], row[2]))
            task = first_user_content(record.get("messages"))
            if task:
                return task, f"{member}#first-user"
        for member, event in load_openhands_events(archive, members):
            if event.get("action") != "recall":
                continue
            args = event.get("args")
            query = args.get("query") if isinstance(args, dict) else None
            if isinstance(query, str) and query.strip():
                return query.strip(), f"{member}#recall-query"

    raise SourceError(f"{archive.name}: no complete public task text for {framework}")


def reconstruct_source(
    raw_root: Path,
    session: str,
    rows: list[dict[str, Any]],
) -> dict[str, Any]:
    framework = framework_for_session(session)
    archive = raw_root / "bench_artifacts" / "full" / f"{session}.tar.zst"
    require(archive.is_file(), f"missing public archive: {archive}")
    members = tar_members(archive)
    raw_steps, adapter = ADAPTERS[framework](archive, members, len(rows))
    require(len(raw_steps) == len(rows), f"{session}: source operation count mismatch")
    task, task_source = extract_task_text(archive, members, framework)
    operations = []
    for index, (visible, raw) in enumerate(zip(rows, raw_steps, strict=True)):
        require(raw.step_id == int(visible["step_id"]), f"{session}: source step mismatch")
        require(raw.source_ref == visible["source_ref"], f"{session}: source reference mismatch")
        operations.append(
            {
                "step": int(visible["step_id"]),
                "action_kind": str(visible["action"]),
                "raw_action_key": str(visible["action_detail"]),
                "phase": str(visible["phase"]),
                "source_action": raw.action,
                "preceding_observation": raw_steps[index - 1].observation if index else None,
                "current_observation": raw.observation,
            }
        )
    return {
        "session": session,
        "framework": framework,
        "adapter": adapter,
        "archive": relative(archive),
        "archive_sha256": sha256_file(archive),
        "task": task,
        "task_source": task_source,
        "operations": operations,
    }


def token_count(llama_url: str, content: str, timeout_seconds: int) -> int:
    response = request_session().post(
        llama_url.rstrip("/") + "/tokenize",
        json={"content": content, "add_special": True, "with_pieces": False},
        timeout=timeout_seconds,
    )
    response.raise_for_status()
    tokens = response.json().get("tokens")
    require(isinstance(tokens, list), "tokenizer response has no tokens[]")
    return len(tokens)


def project_planner_task(
    task: str,
    llama_url: str,
    timeout_seconds: int,
) -> tuple[str, int, int]:
    """Keep the largest deterministic head/tail task projection that fits."""

    def materialize(char_budget: int) -> tuple[str, int]:
        projected = clip_text(task, char_budget)
        user = "CONCRETE TASK\n" + projected
        return projected, token_count(llama_url, PLANNER_SYSTEM + "\n" + user, timeout_seconds)

    projected, tokens = materialize(len(task))
    if tokens <= TOKENIZER_PROJECTION_LIMIT:
        return projected, len(task), tokens
    low, high = min(MIN_TASK_CHARS, len(task)), len(task)
    best: tuple[str, int, int] | None = None
    while low <= high:
        middle = (low + high) // 2
        candidate, count = materialize(middle)
        if count <= TOKENIZER_PROJECTION_LIMIT:
            best = (candidate, middle, count)
            low = middle + 1
        else:
            high = middle - 1
    require(best is not None, "concrete task cannot fit planner context")
    return best


def visible_operation(row: dict[str, Any], field_budget: int) -> dict[str, Any]:
    record = {
        "step": row["step"],
        "action_kind": row["action_kind"],
        "raw_action_key": row["raw_action_key"],
        "source_action": clip_text(row["source_action"], field_budget),
        "preceding_observation": clip_text(row["preceding_observation"], field_budget),
    }
    require(set(record) == VISIBLE_OPERATION_KEYS, "visible operation key drift")
    return record


def causal_evidence(task: str, operation: dict[str, Any]) -> str:
    return (
        "CONCRETE TASK\n"
        + task
        + "\n\nCURRENT OPERATION\n"
        + json.dumps(operation, ensure_ascii=False, separators=(",", ":"))
    )


def candidate_user_text(evidence: str, plan: list[str], previous: int | None) -> str:
    return (
        evidence
        + "\n\nFIXED WORKFLOW PLAN\n"
        + json.dumps(plan, ensure_ascii=False, separators=(",", ":"))
        + "\n\nPRECEDING PLAN INDEX\n"
        + ("none" if previous is None else str(previous))
    )


def flat_user_text(evidence: str, previous_label: str | None) -> str:
    return (
        evidence
        + "\n\nPRECEDING FREE STAGE\n"
        + ("none" if previous_label is None else previous_label)
    )


def project_causal_call(
    source: dict[str, Any],
    row: dict[str, Any],
    planner_task: str,
    plan: list[str],
    candidate_previous: int | None,
    flat_previous_label: str | None,
    llama_url: str,
    timeout_seconds: int,
) -> dict[str, Any]:
    """Project shared evidence once; wrappers differ only by algorithm state."""

    def materialize(task_budget: int, field_budget: int) -> dict[str, Any]:
        task = clip_text(planner_task, task_budget)
        operation = visible_operation(row, field_budget)
        evidence = causal_evidence(task, operation)
        candidate = candidate_user_text(evidence, plan, candidate_previous)
        flat = flat_user_text(evidence, flat_previous_label)
        candidate_tokens = token_count(
            llama_url, ALIGN_SYSTEM + "\n" + candidate, timeout_seconds
        )
        flat_tokens = token_count(llama_url, FLAT_SYSTEM + "\n" + flat, timeout_seconds)
        return {
            "task": task,
            "operation": operation,
            "evidence": evidence,
            "candidate_user": candidate,
            "flat_user": flat,
            "candidate_request_tokens": candidate_tokens,
            "flat_request_tokens": flat_tokens,
            "task_char_budget": task_budget,
            "field_char_budget": field_budget,
        }

    task_budget = len(planner_task)
    initial = materialize(task_budget, INITIAL_FIELD_CHARS)
    if max(initial["candidate_request_tokens"], initial["flat_request_tokens"]) <= TOKENIZER_PROJECTION_LIMIT:
        return initial

    low, high = MIN_FIELD_CHARS, INITIAL_FIELD_CHARS - 1
    best: dict[str, Any] | None = None
    while low <= high:
        middle = (low + high) // 2
        candidate = materialize(task_budget, middle)
        if max(candidate["candidate_request_tokens"], candidate["flat_request_tokens"]) <= TOKENIZER_PROJECTION_LIMIT:
            best = candidate
            low = middle + 1
        else:
            high = middle - 1
    if best is not None:
        return best

    field_budget = MIN_FIELD_CHARS
    low, high = min(MIN_TASK_CHARS, len(planner_task)), len(planner_task)
    while low <= high:
        middle = (low + high) // 2
        candidate = materialize(middle, field_budget)
        if max(candidate["candidate_request_tokens"], candidate["flat_request_tokens"]) <= TOKENIZER_PROJECTION_LIMIT:
            best = candidate
            low = middle + 1
        else:
            high = middle - 1
    require(best is not None, f"{source['session']} step {row['step']}: causal context overflow")
    return best


def planner_grammar(maximum: int) -> str:
    require(maximum >= 1, "invalid planner grammar dimension")
    tail = f'(ws "," ws label){{0,{maximum - 1}}}' if maximum > 1 else ""
    return f'''root ::= "[" ws label {tail} ws "]" ws
label ::= "\\\"" [a-z] [a-z0-9 /+._-]{{0,{LABEL_MAX_CHARS - 1}}} "\\\""
ws ::= [ \\t\\n]*
'''


def candidate_grammar(maximum: int) -> str:
    require(maximum >= 0, "invalid candidate grammar dimension")
    values = " | ".join(f'"{value}"' for value in range(maximum + 1))
    return f'''root ::= "{{\\\"plan_index\\\":" index "}}"
index ::= {values}
'''


def flat_grammar(first: bool) -> str:
    root = "switch" if first else "stay | switch"
    return f'''root ::= {root}
stay ::= "{{\\\"decision\\\":\\\"stay\\\",\\\"new_label\\\":null}}"
switch ::= "{{\\\"decision\\\":\\\"switch\\\",\\\"new_label\\\":" label "}}"
label ::= "\\\"" [a-z] [a-z0-9 /+._-]{{0,{LABEL_MAX_CHARS - 1}}} "\\\""
'''


def call_model(
    llama_url: str,
    system: str,
    user: str,
    grammar: str,
    timeout_seconds: int,
    max_tokens: int,
) -> tuple[str, dict[str, Any], list[dict[str, Any]]]:
    body = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "temperature": 0,
        "seed": SEED,
        "max_tokens": max_tokens,
        "grammar": grammar,
        "stream": False,
    }
    attempts = []
    for attempt in range(3):
        started = time.monotonic()
        try:
            response = request_session().post(
                llama_url.rstrip("/") + "/v1/chat/completions",
                json=body,
                timeout=timeout_seconds,
            )
            elapsed_ms = (time.monotonic() - started) * 1_000.0
            response.raise_for_status()
            payload = response.json()
            raw = str(payload["choices"][0]["message"]["content"])
            prompt_tokens = int((payload.get("usage") or {}).get("prompt_tokens", 0))
            require(0 < prompt_tokens <= MAX_REQUEST_TOKENS, "model request exceeded input limit")
            attempts.append({"attempt": attempt + 1, "elapsed_ms": elapsed_ms, "status": "ok"})
            return raw, payload, attempts
        except requests.RequestException as error:
            attempts.append(
                {
                    "attempt": attempt + 1,
                    "elapsed_ms": (time.monotonic() - started) * 1_000.0,
                    "status": "transport-error",
                    "error": str(error),
                }
            )
            if attempt == 2:
                raise
    raise AssertionError("unreachable")


def parse_plan(raw: str, operation_count: int) -> list[str]:
    value = json.loads(raw)
    require(isinstance(value, list) and value, "planner returned no responsibilities")
    require(len(value) <= operation_count, "planner returned more items than operations")
    require(all(isinstance(label, str) for label in value), "planner label type")
    labels = [label.strip() for label in value]
    require(all(0 < len(label) <= LABEL_MAX_CHARS for label in labels), "planner label length")
    require(all(LABEL_RE.fullmatch(label) for label in labels), "planner label syntax")
    return labels


def label_is_semantic(label: str) -> bool:
    prohibited = re.compile(
        r"(?:^|[ /+._-])(agent|model|session|tool|command|status|success|failed|failure|shell|terminal|line|lines)(?:$|[ /+._-])"
    )
    extension = re.compile(r"\b[a-z0-9_.-]+\.(?:py|rs|c|h|md|json|ya?ml|toml|txt)\b")
    return not prohibited.search(label) and not extension.search(label) and not label.startswith("/")


def parse_candidate(raw: str, maximum: int) -> int:
    value = json.loads(raw)
    require(isinstance(value, dict) and set(value) == {"plan_index"}, "candidate response keys")
    index = value["plan_index"]
    require(type(index) is int, "candidate index type")
    require(0 <= index <= maximum, "candidate index out of range")
    return index


def parse_flat(raw: str, first: bool) -> tuple[str, str | None, bool]:
    value = json.loads(raw)
    require(
        isinstance(value, dict) and set(value) == {"decision", "new_label"},
        "plan-free response keys",
    )
    decision = value["decision"]
    label = value["new_label"]
    require(decision in {"stay", "switch"}, "plan-free decision")
    if first:
        require(decision == "switch", "first plan-free operation must switch")
    if decision == "stay":
        require(label is None, "stay must preserve a null new label")
        return decision, None, True
    require(isinstance(label, str), "switch label type")
    require(0 < len(label) <= LABEL_MAX_CHARS, "switch label length")
    require(bool(LABEL_RE.fullmatch(label)), "switch label syntax")
    return decision, label, label_is_semantic(label)


def session_cache_name(session: str) -> str:
    return hashlib.sha256(session.encode()).hexdigest()[:24] + ".json"


def infer_session(
    source: dict[str, Any],
    llama_url: str,
    timeout_seconds: int,
    cache_dir: Path,
) -> dict[str, Any]:
    session = source["session"]
    cache_path = cache_dir / session_cache_name(session)
    result: dict[str, Any]
    if cache_path.is_file():
        result = json.loads(cache_path.read_text(encoding="utf-8"))
        require(result["algorithm_version"] == ALGORITHM_VERSION, f"{session}: cache version")
        require(result["session"] == session, f"{session}: cache identity")
        require(result["model_sha256"] == MODEL_SHA256, f"{session}: cache model")
        require(result["archive_sha256"] == source["archive_sha256"], f"{session}: cache source")
    else:
        planner_task, task_char_budget, planner_request_tokens = project_planner_task(
            source["task"], llama_url, timeout_seconds
        )
        planner_user = "CONCRETE TASK\n" + planner_task
        plan_raw, plan_response, plan_attempts = call_model(
            llama_url,
            PLANNER_SYSTEM,
            planner_user,
            planner_grammar(len(source["operations"])),
            timeout_seconds,
            PLANNER_OUTPUT_TOKENS,
        )
        raw_plan = parse_plan(plan_raw, len(source["operations"]))
        plan = list(dict.fromkeys(raw_plan))
        require(bool(plan), "normalized planner returned no responsibilities")
        plan_semantic = [label_is_semantic(label) for label in plan]
        result = {
            "schema": "agentsight.rq3-task-rooted-stage-alignment.session.v2",
            "algorithm_version": ALGORITHM_VERSION,
            "session": session,
            "framework": source["framework"],
            "adapter": source["adapter"],
            "archive": source["archive"],
            "archive_sha256": source["archive_sha256"],
            "task_source": source["task_source"],
            "model": MODEL,
            "model_sha256": MODEL_SHA256,
            "seed": SEED,
            "planner_task": planner_task,
            "raw_plan": raw_plan,
            "plan": plan,
            "exact_duplicate_plan_items_removed": len(raw_plan) - len(plan),
            "plan_semantic": plan_semantic,
            "planner_request": {
                "system": PLANNER_SYSTEM,
                "user": planner_user,
                "request_tokens": int((plan_response.get("usage") or {})["prompt_tokens"]),
                "projection_tokens": planner_request_tokens,
                "task_char_budget": task_char_budget,
                "raw": plan_raw,
                "usage": plan_response.get("usage") or {},
                "attempts": plan_attempts,
            },
            "transitions": [],
        }
        write_json_atomic(cache_path, result)

    transitions = result["transitions"]
    require(len(transitions) <= len(source["operations"]), f"{session}: excessive cached transitions")
    candidate_previous = transitions[-1]["candidate"]["plan_index"] if transitions else None
    flat_previous_label = transitions[-1]["plan_free"]["active_label"] if transitions else None
    flat_previous_instance = transitions[-1]["plan_free"]["stage_instance"] if transitions else -1

    for operation_number in range(len(transitions), len(source["operations"])):
        row = source["operations"][operation_number]
        projection = project_causal_call(
            source,
            row,
            result["planner_task"],
            result["plan"],
            candidate_previous,
            flat_previous_label,
            llama_url,
            timeout_seconds,
        )
        candidate_raw, candidate_response, candidate_attempts = call_model(
            llama_url,
            ALIGN_SYSTEM,
            projection["candidate_user"],
            candidate_grammar(len(result["plan"]) - 1),
            timeout_seconds,
            CAUSAL_OUTPUT_TOKENS,
        )
        candidate_index = parse_candidate(candidate_raw, len(result["plan"]) - 1)
        flat_raw, flat_response, flat_attempts = call_model(
            llama_url,
            FLAT_SYSTEM,
            projection["flat_user"],
            flat_grammar(operation_number == 0),
            timeout_seconds,
            CAUSAL_OUTPUT_TOKENS,
        )
        decision, new_label, semantic_label = parse_flat(
            flat_raw, operation_number == 0
        )
        if decision == "switch":
            flat_previous_instance += 1
            flat_previous_label = new_label
        require(flat_previous_label is not None, f"{session}: missing active plan-free label")
        transition = {
            "operation_number": operation_number,
            "step": row["step"],
            "projection": {
                "task": projection["task"],
                "operation": projection["operation"],
                "shared_evidence": projection["evidence"],
                "task_char_budget": projection["task_char_budget"],
                "field_char_budget": projection["field_char_budget"],
            },
            "candidate": {
                "system": ALIGN_SYSTEM,
                "user": projection["candidate_user"],
                "preceding_plan_index": candidate_previous,
                "plan_index": candidate_index,
                "request_tokens": int((candidate_response.get("usage") or {})["prompt_tokens"]),
                "projection_tokens": projection["candidate_request_tokens"],
                "raw": candidate_raw,
                "usage": candidate_response.get("usage") or {},
                "attempts": candidate_attempts,
            },
            "plan_free": {
                "system": FLAT_SYSTEM,
                "user": projection["flat_user"],
                "decision": decision,
                "new_label": new_label,
                "semantic_label": semantic_label,
                "active_label": flat_previous_label,
                "stage_instance": flat_previous_instance,
                "request_tokens": int((flat_response.get("usage") or {})["prompt_tokens"]),
                "projection_tokens": projection["flat_request_tokens"],
                "raw": flat_raw,
                "usage": flat_response.get("usage") or {},
                "attempts": flat_attempts,
            },
        }
        transitions.append(transition)
        candidate_previous = candidate_index
        write_json_atomic(cache_path, result)
    require(len(result["transitions"]) == len(source["operations"]), f"{session}: incomplete transitions")
    return result


def prepare_sources(
    grouped: dict[str, list[dict[str, Any]]],
    raw_root: Path,
    workers: int,
) -> dict[str, dict[str, Any]]:
    prepared: dict[str, dict[str, Any]] = {}

    def prepare(session: str) -> dict[str, Any]:
        return reconstruct_source(raw_root, session, grouped[session])

    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {executor.submit(prepare, session): session for session in sorted(grouped)}
        for future in as_completed(futures):
            session = futures[future]
            prepared[session] = future.result()
            print(f"prepared {len(prepared)}/{len(grouped)} {session}", flush=True)
    return prepared


def preflight_selection(prepared: dict[str, dict[str, Any]]) -> list[str]:
    def estimated_chars(source: dict[str, Any]) -> int:
        operation = max(
            source["operations"],
            key=lambda row: len(row["source_action"] or "")
            + len(row["preceding_observation"] or ""),
        )
        return (
            len(source["task"])
            + len(operation["source_action"] or "")
            + len(operation["preceding_observation"] or "")
        )

    selected = []
    for framework in sorted(EXPECTED_FRAMEWORKS):
        candidates = [
            session for session, row in prepared.items() if row["framework"] == framework
        ]
        require(bool(candidates), f"no preflight source for {framework}")
        selected.append(
            max(candidates, key=lambda session: (estimated_chars(prepared[session]), session))
        )
    return sorted(selected)


def run_inference(args: argparse.Namespace) -> None:
    target_path = absolute(args.target_operations)
    raw_root = absolute(args.raw_root)
    out_dir = absolute(args.out)
    require(target_path.is_file(), f"missing input: {target_path}")
    require(raw_root.is_dir(), f"missing input: {raw_root}")
    health = requests.get(args.llama_url.rstrip("/") + "/health", timeout=10)
    health.raise_for_status()
    require(MODEL_PATH.is_file(), f"missing retained model: {MODEL_PATH}")
    require(sha256_file(MODEL_PATH) == MODEL_SHA256, "retained model SHA-256 changed")
    grouped = load_visible_operations(target_path)
    require(len(grouped) == EXPECTED_SESSIONS, "unexpected target session count")
    require(sum(map(len, grouped.values())) == EXPECTED_OPERATIONS, "unexpected operation count")
    prepared = prepare_sources(grouped, raw_root, args.workers)
    require(set(prepared) == set(grouped), "source preparation coverage mismatch")
    require(
        {row["framework"] for row in prepared.values()} == EXPECTED_FRAMEWORKS,
        "framework coverage mismatch",
    )
    selected = preflight_selection(prepared) if args.mode == "preflight" else sorted(prepared)

    out_dir.mkdir(parents=True, exist_ok=True)
    cache_dir = out_dir / "sessions"
    write_jsonl(
        out_dir / "projection-summary.jsonl",
        (
            {
                "session": session,
                "framework": prepared[session]["framework"],
                "operations": len(prepared[session]["operations"]),
                "task_chars": len(prepared[session]["task"]),
                "max_operation_evidence_chars": max(
                    len(row["source_action"] or "")
                    + len(row["preceding_observation"] or "")
                    for row in prepared[session]["operations"]
                ),
                "selected": session in selected,
            }
            for session in sorted(prepared)
        ),
    )

    started = time.monotonic()
    results: dict[str, dict[str, Any]] = {}
    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = {
            executor.submit(
                infer_session,
                prepared[session],
                args.llama_url,
                args.timeout_seconds,
                cache_dir,
            ): session
            for session in selected
        }
        for future in as_completed(futures):
            session = futures[future]
            results[session] = future.result()
            print(f"inferred {len(results)}/{len(selected)} {session}", flush=True)

    predictions = []
    for session in selected:
        result = results[session]
        source_operations = prepared[session]["operations"]
        require(len(result["transitions"]) == len(source_operations), "causal coverage")
        for index, row in enumerate(source_operations):
            transition = result["transitions"][index]
            require(transition["step"] == row["step"], "transition step mismatch")
            candidate_index = transition["candidate"]["plan_index"]
            predictions.append(
                {
                    "session": session,
                    "framework": result["framework"],
                    "step_id": row["step"],
                    "action": row["action_kind"],
                    "action_detail": row["raw_action_key"],
                    "phase": row["phase"],
                    "source_action": row["source_action"],
                    "current_observation": row["current_observation"],
                    "task_label": result["planner_task"],
                    "candidate_index": candidate_index,
                    "candidate_label": result["plan"][candidate_index],
                    "candidate_label_semantic": result["plan_semantic"][candidate_index],
                    "flat_index": transition["plan_free"]["stage_instance"],
                    "flat_label": transition["plan_free"]["active_label"],
                }
            )
    require(len(predictions) == sum(len(grouped[s]) for s in selected), "prediction coverage")
    write_jsonl(out_dir / "predictions.jsonl", predictions)

    usage: Counter[str] = Counter()
    request_tokens = []
    for result in results.values():
        model_requests = [result["planner_request"]]
        model_requests.extend(
            request
            for transition in result["transitions"]
            for request in (transition["candidate"], transition["plan_free"])
        )
        for request in model_requests:
            request_tokens.append(request["request_tokens"])
            for key, value in request["usage"].items():
                if isinstance(value, (int, float)):
                    usage[key] += value
    candidate_switches = sum(
        transition["candidate"]["plan_index"]
        != result["transitions"][index - 1]["candidate"]["plan_index"]
        for result in results.values()
        for index, transition in enumerate(result["transitions"])
        if index > 0
    )
    plan_free_switches = sum(
        transition["plan_free"]["decision"] == "switch"
        for result in results.values()
        for transition in result["transitions"]
    )
    plan_free_label_violations = sum(
        transition["plan_free"]["decision"] == "switch"
        and not transition["plan_free"]["semantic_label"]
        for result in results.values()
        for transition in result["transitions"]
    )
    candidate_label_violations = sum(
        not semantic
        for result in results.values()
        for semantic in result["plan_semantic"]
    )
    exact_duplicate_plan_items_removed = sum(
        result["exact_duplicate_plan_items_removed"] for result in results.values()
    )
    summary = {
        "schema": "agentsight.rq3-task-rooted-stage-alignment.inference.v1",
        "algorithm_version": ALGORITHM_VERSION,
        "status": "complete",
        "mode": args.mode,
        "model": MODEL,
        "model_sha256": MODEL_SHA256,
        "seed": SEED,
        "sessions": len(selected),
        "operations": len(predictions),
        "prepared_population": len(prepared),
        "selected_sessions": selected,
        "request_token_max": max(request_tokens),
        "model_calls": len(selected) + 2 * len(predictions),
        "plan_size": {
            "min": min(len(result["plan"]) for result in results.values()),
            "max": max(len(result["plan"]) for result in results.values()),
            "mean": sum(len(result["plan"]) for result in results.values()) / len(results),
        },
        "candidate_boundary_rate": candidate_switches
        / max(1, len(predictions) - len(selected)),
        "plan_free_boundary_rate": (plan_free_switches - len(selected))
        / max(1, len(predictions) - len(selected)),
        "plan_free_system_label_violations": plan_free_label_violations,
        "candidate_system_label_violations": candidate_label_violations,
        "exact_duplicate_plan_items_removed": exact_duplicate_plan_items_removed,
        "model_usage": dict(usage),
        "wall_seconds": time.monotonic() - started,
        "predictions": relative(out_dir / "predictions.jsonl"),
        "projection_summary": relative(out_dir / "projection-summary.jsonl"),
        "isolation": {
            "official_manifest_opened": False,
            "official_stages_opened": False,
            "visible_task_field": "initial public user request",
            "visible_operation_keys": sorted(VISIBLE_OPERATION_KEYS),
            "candidate_and_plan_free_share_byte_identical_evidence": True,
            "all_operations_retained": True,
        },
    }
    write_json(out_dir / "inference-summary.json", summary)
    print(json.dumps(summary, sort_keys=True), flush=True)


def load_prediction_rows(path: Path) -> dict[tuple[str, int], dict[str, Any]]:
    output = {}
    with path.open(encoding="utf-8") as source:
        for line_number, line in enumerate(source, 1):
            row = json.loads(line)
            key = (str(row["session"]), int(row["step_id"]))
            require(key not in output, f"duplicate prediction line {line_number}")
            output[key] = row
    return output


def load_baselines(path: Path) -> dict[tuple[str, int], dict[str, str]]:
    output = {}
    with path.open(encoding="utf-8") as source:
        for line_number, line in enumerate(source, 1):
            row = json.loads(line)
            key = (str(row["session"]), int(row["step_id"]))
            require(key not in output, f"duplicate baseline line {line_number}")
            output[key] = {
                "multires_recurrence": str(row["recurrence"]),
                "current_recurrence": str(row["current_recurrence"]),
                "phase": str(row["phase_change"]),
                "raw_action": str(row["raw_action_key_change"]),
                "action": str(row["action_change"]),
                "one_span": str(row["session_one_block"]),
            }
    return output


def score_rows(
    grouped: dict[str, list[dict[str, Any]]],
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
        "plan_free_qwen",
        "multires_recurrence",
        "current_recurrence",
        "phase",
        "raw_action",
        "action",
        "one_span",
    )
    for session in sorted(grouped):
        previous = None
        previous_candidate_index = None
        candidate_instance = -1
        for row in grouped[session]:
            key = (session, int(row["step_id"]))
            require(key in predictions, f"missing prediction: {key}")
            require(key in baselines, f"missing baseline: {key}")
            prediction = predictions[key]
            candidate_index = int(prediction["candidate_index"])
            if candidate_index != previous_candidate_index:
                candidate_instance += 1
                previous_candidate_index = candidate_index
            operation = {
                "session": session,
                "framework": frameworks[session],
                "task_name": tasks[session],
                "step_id": int(row["step_id"]),
                "official_stage": official[key],
                "candidate": f"{session}:candidate-run-{candidate_instance:04d}",
                "candidate_responsibility": (
                    f"{session}:candidate-plan-{candidate_index:04d}"
                ),
                "plan_free_qwen": f"{session}:flat-{int(prediction['flat_index']):04d}",
                **baselines[key],
            }
            operations.append(operation)
            if previous is not None:
                pair = {
                    "session": session,
                    "framework": frameworks[session],
                    "task_name": tasks[session],
                    "position": int(row["step_id"]) - 1,
                    "official_boundary": previous["official_stage"] != operation["official_stage"],
                }
                for method in methods:
                    pair[method] = previous[method] != operation[method]
                pairs.append(pair)
            previous = operation
    return pairs, operations


def spans_for(rows: list[dict[str, Any]], method: str) -> set[tuple[str, int, int]]:
    by_session: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_session[str(row["session"])].append(row)
    spans = set()
    for session, session_rows in by_session.items():
        session_rows.sort(key=lambda row: int(row["step_id"]))
        start = int(session_rows[0]["step_id"])
        previous = session_rows[0][method]
        for row in session_rows[1:]:
            if row[method] != previous:
                spans.add((session, start, int(row["step_id"]) - 1))
                start = int(row["step_id"])
                previous = row[method]
        spans.add((session, start, int(session_rows[-1]["step_id"])))
    return spans


def span_sufficient(rows: list[dict[str, Any]], method: str) -> tuple[int, int, int]:
    predicted = spans_for(rows, method)
    gold = spans_for(rows, "official_stage")
    return len(predicted & gold), len(predicted), len(gold)


def span_metrics(rows: list[dict[str, Any]], method: str) -> dict[str, Any]:
    true_positive, predicted, gold = span_sufficient(rows, method)
    precision = true_positive / predicted if predicted else 0.0
    recall = true_positive / gold if gold else 0.0
    f1 = 2 * true_positive / (predicted + gold) if predicted + gold else 0.0
    return {
        "true_positive": true_positive,
        "predicted_spans": predicted,
        "official_spans": gold,
        "precision": precision,
        "recall": recall,
        "f1": f1,
    }


def task_cluster_bootstrap(
    rows: list[dict[str, Any]],
    candidate: str,
    baseline: str,
    output: Path,
) -> dict[str, Any]:
    by_task: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_task[str(row["task_name"])].append(row)
    tasks = sorted(by_task)
    require(len(tasks) == EXPECTED_TASKS, "unexpected task cluster count")
    sufficient = {
        (task, method): span_sufficient(task_rows, method)
        for task, task_rows in by_task.items()
        for method in (candidate, baseline)
    }

    def f1(draw: list[str], method: str) -> float:
        true_positive = predicted = gold = 0
        for task in draw:
            local_tp, local_predicted, local_gold = sufficient[(task, method)]
            true_positive += local_tp
            predicted += local_predicted
            gold += local_gold
        return 2 * true_positive / (predicted + gold) if predicted + gold else 0.0

    generator = random.Random(SEED)
    deltas = []
    for _ in range(BOOTSTRAP_RESAMPLES):
        draw = generator.choices(tasks, k=len(tasks))
        deltas.append(f1(draw, candidate) - f1(draw, baseline))
    write_jsonl(
        output,
        ({"resample": index, "delta": delta} for index, delta in enumerate(deltas)),
    )
    return {
        "candidate": candidate,
        "baseline": baseline,
        "unit": "task_name",
        "clusters": len(tasks),
        "resamples": BOOTSTRAP_RESAMPLES,
        "seed": SEED,
        "mean_delta": sum(deltas) / len(deltas),
        "median_delta": percentile(deltas, 0.5),
        "ci95": [percentile(deltas, 0.025), percentile(deltas, 0.975)],
        "positive_fraction": sum(delta > 0 for delta in deltas) / len(deltas),
        "raw_deltas": relative(output),
    }


def safe_frame(value: str, limit: int = 72) -> str:
    cleaned = re.sub(r"[;\r\n\t]+", " ", value).strip()
    return clip_text(cleaned, limit)


def object_label(action: str, fallback: str) -> str:
    match = PATH_RE.search(action)
    return safe_frame(match.group(0) if match else fallback, 56)


def result_label(observation: str | None) -> str:
    if not observation or not observation.strip():
        return "no visible result"
    text = re.sub(r"<[^>]+>", " ", observation)
    line = next((part.strip() for part in text.splitlines() if part.strip()), "observed output")
    return safe_frame(line, 64)


def write_folded_and_svg(
    prediction_rows: dict[tuple[str, int], dict[str, Any]],
    session: str,
    out_dir: Path,
) -> tuple[Path, Path]:
    rows = sorted(
        (row for (row_session, _), row in prediction_rows.items() if row_session == session),
        key=lambda row: int(row["step_id"]),
    )
    require(bool(rows), "representative session has no rows")
    semantic_violations = sum(
        not bool(row.get("candidate_label_semantic", False)) for row in rows
    )
    folded = out_dir / "task-centric-example.folded"
    lines = []
    for row in rows:
        frames = (
            "task:" + safe_frame(str(row["task_label"]), 96),
            "subtask:"
            + ("[system-detail warning] " if not row.get("candidate_label_semantic") else "")
            + safe_frame(str(row["candidate_label"]), 64),
            "phase:" + safe_frame(str(row["phase"]), 32),
            "semantic-action:" + safe_frame(str(row["action"]), 32),
            "object:" + object_label(str(row["source_action"]), str(row["action_detail"])),
            "result:" + result_label(row.get("current_observation")),
        )
        lines.append(";".join(frames) + " 1")
    folded.write_text("\n".join(lines) + "\n", encoding="utf-8")

    counts: Counter[tuple[str, ...]] = Counter()
    for line in lines:
        stack, value = line.rsplit(" ", 1)
        counts[tuple(stack.split(";"))] += int(value)
    width, frame_height, left, top = 1800, 34, 24, 110
    total = sum(counts.values())
    prefixes: Counter[tuple[str, ...]] = Counter()
    for stack, value in counts.items():
        for depth in range(1, len(stack) + 1):
            prefixes[stack[:depth]] += value
    height = top + 6 * frame_height + 40
    chunks = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#f7f9fc"/>',
        '<style>text{font-family:Inter,system-ui,sans-serif}.t{font-size:20px;font-weight:700;fill:#17253d}.s{font-size:12px;fill:#60708a}.f{font-size:11px;fill:#fff;font-weight:600}</style>',
        '<text class="t" x="24" y="30">FAILED numeric-index mechanism diagnostic</text>',
        '<text class="s" x="24" y="52">not a recovered task-semantic hierarchy; width = operations; generated names are not gold-validated</text>',
        '<text class="s" x="24" y="70" fill="#b42318">registered exact-span test contradicted this candidate; lower frames remain runtime-derived evidence</text>',
    ]
    if semantic_violations:
        chunks.append(
            f'<text class="s" x="24" y="86" fill="#b42318">registered lexical rule matched the candidate label on {semantic_violations} operations; this is not a human semantic-error judgment</text>'
        )
    colors = ["#23395d", "#5b5bd6", "#2f80ed", "#00a6a6", "#778da9", "#43b581"]
    def render(prefix: tuple[str, ...], x: float) -> None:
        depth = len(prefix)
        value = prefixes[prefix]
        rect_width = (width - 2 * left) * value / total
        y = top + (6 - depth) * frame_height
        label = prefix[-1].split(":", 1)[-1]
        visible = label if rect_width > len(label) * 6 + 12 else ""
        title = html.escape(" → ".join(prefix) + f"\n{value} operations")
        chunks.append(f'<g><title>{title}</title><rect x="{x:.2f}" y="{y}" width="{rect_width:.2f}" height="{frame_height - 2}" rx="4" fill="{colors[depth - 1]}" stroke="#fff"/>')
        if visible:
            chunks.append(f'<text class="f" x="{x + 6:.2f}" y="{y + 21}">{html.escape(visible)}</text>')
        chunks.append("</g>")
        child_x = x
        children = sorted(
            (
                child
                for child in prefixes
                if len(child) == depth + 1 and child[:-1] == prefix
            ),
            key=lambda child: (-prefixes[child], child[-1]),
        )
        for child in children:
            render(child, child_x)
            child_x += (width - 2 * left) * prefixes[child] / total

    root_x = float(left)
    roots = sorted(
        (prefix for prefix in prefixes if len(prefix) == 1),
        key=lambda prefix: (-prefixes[prefix], prefix[-1]),
    )
    for prefix in roots:
        render(prefix, root_x)
        root_x += (width - 2 * left) * prefixes[prefix] / total
    chunks.append("</svg>")
    svg = out_dir / "task-centric-example.svg"
    svg.write_text("\n".join(chunks) + "\n", encoding="utf-8")
    return folded, svg


def report_markdown(summary: dict[str, Any]) -> str:
    lines = [
        "# Task-Rooted Stage Alignment — Complete Result",
        "",
        f"- status: {summary['status']}",
        f"- registered interpretation: **{summary['registered_interpretation']}**",
        f"- population: {summary['population']['sessions']} trajectories, "
        f"{summary['population']['operations']} operations, "
        f"{summary['population']['official_stages']} human stages, "
        f"{summary['population']['tasks']} task clusters",
        "",
        "## Standard Metrics",
        "",
        "| Method | Span P | Span R | Span F1 | B³ F1 | Boundary F1 |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for method, metric in summary["metrics"].items():
        lines.append(
            f"| {method} | {metric['span']['precision']:.6f} | "
            f"{metric['span']['recall']:.6f} | {metric['span']['f1']:.6f} | "
            f"{metric['bcubed']['f1']:.6f} | {metric['boundary']['f1']:.6f} |"
        )
    lines.extend(["", "## Paired Task-Cluster Bootstrap", ""])
    for name, bootstrap in summary["bootstrap"].items():
        lines.append(
            f"- candidate minus {name}: mean {bootstrap['mean_delta']:.6f}, "
            f"95% CI [{bootstrap['ci95'][0]:.6f}, {bootstrap['ci95'][1]:.6f}]"
        )
    label_audit = summary.get("label_audit") or {}
    if label_audit:
        lines.extend(
            [
                "",
                "## Registered Lexical-Rule Audit",
                "",
                f"- candidate lexical-rule hits: {label_audit.get('candidate_system_label_violations', 'unavailable')}",
                f"- plan-free lexical-rule hits: {label_audit.get('plan_free_system_label_violations', 'unavailable')}",
                f"- exact duplicate candidate plan items removed: {label_audit.get('exact_duplicate_plan_items_removed', 'unavailable')}",
                "- these deterministic lexical hits are diagnostics, not human-validated semantic error rates",
            ]
        )
    lines.extend(
        [
            "",
            "## Interpretation Boundary",
            "",
            "This result measures only unlabeled human workflow-stage fidelity. "
            "Generated task/subtask names and lower phase/action/object/result "
            "frames remain qualitative; the exact thesis and four paper RQs are unchanged.",
        ]
    )
    return "\n".join(lines) + "\n"


def run_scoring(args: argparse.Namespace) -> None:
    target_path = absolute(args.target_operations)
    prediction_input = absolute(args.predictions)
    inference_summary: dict[str, Any] = {}
    if prediction_input.is_dir():
        inference_summary_path = prediction_input / "inference-summary.json"
        require(inference_summary_path.is_file(), "missing full inference summary")
        inference_summary = json.loads(inference_summary_path.read_text(encoding="utf-8"))
        prediction_path = prediction_input / "predictions.jsonl"
    else:
        prediction_path = prediction_input
    manifest_path = absolute(args.verified_manifest)
    baseline_path = absolute(args.multires_assignments)
    out_dir = absolute(args.out)
    for path in (target_path, prediction_path, manifest_path, baseline_path):
        require(path.is_file(), f"missing score input: {path}")
    grouped = load_visible_operations(target_path)
    require(len(grouped) == EXPECTED_SESSIONS, "unexpected score target session count")
    require(
        sum(map(len, grouped.values())) == EXPECTED_OPERATIONS,
        "unexpected score target operation count",
    )
    selected = sorted(grouped)
    predictions = load_prediction_rows(prediction_path)
    expected = {
        (session, int(row["step_id"]))
        for session, rows in grouped.items()
        for row in rows
    }
    require(set(predictions) == expected, "full prediction coverage mismatch")
    baselines = load_baselines(baseline_path)
    require(expected <= set(baselines), "baseline coverage mismatch")

    official, frameworks, tasks = load_stages_after_prediction(
        manifest_path, grouped, selected
    )
    pairs, operations = score_rows(
        grouped, predictions, baselines, official, frameworks, tasks
    )
    require(len(operations) == EXPECTED_OPERATIONS, "scored operation count")
    require(
        len(pairs) == EXPECTED_OPERATIONS - EXPECTED_SESSIONS,
        "scored adjacent-pair count",
    )
    require(len(set(official.values())) == EXPECTED_STAGES, "official stage count")
    require(len(set(tasks.values())) == EXPECTED_TASKS, "task cluster count")
    require(set(frameworks.values()) == EXPECTED_FRAMEWORKS, "scored framework set")
    methods = (
        "candidate",
        "plan_free_qwen",
        "multires_recurrence",
        "current_recurrence",
        "phase",
        "raw_action",
        "action",
        "one_span",
    )
    metrics = {
        method: {
            "span": span_metrics(operations, method),
            "bcubed": bcubed(operations, method),
            "boundary": boundary_metrics(pairs, method),
        }
        for method in methods
    }
    out_dir.mkdir(parents=True, exist_ok=True)
    bootstrap = {
        baseline: task_cluster_bootstrap(
            operations,
            "candidate",
            baseline,
            out_dir / f"bootstrap-candidate-minus-{baseline}.jsonl",
        )
        for baseline in ("plan_free_qwen", "multires_recurrence")
    }
    candidate_f1 = metrics["candidate"]["span"]["f1"]
    higher = all(candidate_f1 > metrics[name]["span"]["f1"] for name in bootstrap)
    positive = all(result["ci95"][0] > 0 for result in bootstrap.values())
    interpretation = (
        "supported-and-adopted"
        if higher and positive
        else "promising-not-adopted"
        if higher
        else "contradicted"
    )
    representative = max(
        selected,
        key=lambda session: (len(grouped[session]), session),
    )
    folded, svg = write_folded_and_svg(predictions, representative, out_dir)
    summary = {
        "schema": "agentsight.rq3-task-rooted-stage-alignment.score.v1",
        "status": "complete",
        "registered_interpretation": interpretation,
        "population": {
            "sessions": len(selected),
            "operations": len(operations),
            "pairs": len(pairs),
            "official_stages": len(set(official.values())),
            "tasks": len(set(tasks.values())),
            "frameworks": dict(Counter(frameworks.values())),
        },
        "metrics": metrics,
        "bootstrap": bootstrap,
        "label_audit": {
            key: inference_summary.get(key)
            for key in (
                "candidate_system_label_violations",
                "plan_free_system_label_violations",
                "exact_duplicate_plan_items_removed",
            )
        },
        "representative_session": representative,
        "folded": relative(folded),
        "svg": relative(svg),
        "claim_boundary": (
            "human workflow-stage span fidelity only; generated responsibility "
            "names and deeper hierarchy are qualitative"
        ),
    }
    write_jsonl(out_dir / "operation-score-rows.jsonl", operations)
    write_jsonl(out_dir / "boundary-score-rows.jsonl", pairs)
    write_json(out_dir / "summary.json", summary)
    (out_dir / "report.md").write_text(report_markdown(summary), encoding="utf-8")
    print(json.dumps(summary, sort_keys=True), flush=True)


def main() -> None:
    args = parse_args()
    if args.command == "infer":
        run_inference(args)
    else:
        run_scoring(args)


if __name__ == "__main__":
    main()
