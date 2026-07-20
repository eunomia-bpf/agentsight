#!/usr/bin/env python3
"""Infer and score a global task-semantic decomposition on CodeTraceBench.

Inference is offline: one model call sees one complete source-native trajectory
and emits contiguous semantic intervals.  Scoring is a separate command that
opens the independent human stages only after every candidate assignment has
been materialized.
"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import hashlib
import html
import json
from pathlib import Path
import re
import sys
import time
from typing import Any, Iterable

import requests


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "script"))

import rq3_source_native_task_progress_boundary_eval as source  # noqa: E402
import rq3_stateful_native_turn_task_stack_eval as stateful  # noqa: E402


base = source.base
ALGORITHM_VERSION = "global-task-semantic-segmentation-v2"
SCHEMA = "agentsight.rq3-global-task-semantic-segmentation"
EXPECTED_SESSIONS = 405
EXPECTED_OPERATIONS = 20_866
EXPECTED_TURNS = 17_148
EXPECTED_STAGES = 2_948
EXPECTED_TASKS = 251
EXPECTED_FRAMEWORKS = base.EXPECTED_FRAMEWORKS
SEED = 20_260_720
CONTEXT_TOKENS = 32_768
MIN_OUTPUT_TOKENS = 4_096
MAX_OUTPUT_TOKENS = 8_192
CONTEXT_MARGIN = 512
TASK_CHARS = 6_000
INTENT_CHARS = 256
PROGRESS_CHARS = 128
ACTION_CHARS = 128
RESULT_CHARS = 256
LABEL_MAX_CHARS = 96
SUBTASK_PATH_MAX_CHARS = 384

SYSTEM_PROMPT = """Read one COMPLETE, already-finished AI-agent trajectory and
decompose how it pursued the concrete user task. Return a small ordered set of
contiguous semantic segments that covers every numbered turn exactly once.

For each segment:
- subtask_path is one string containing the active path of persistent,
  concrete task goals, separated from parent to child by ` > `. Use an empty
  string when only the root task is active. Each frame must have a completion
  condition and may span many turns. This is a nested path, not a list of
  sequential plan steps, retries, or observations. Do not create a frame merely because the tool,
  command, file, path, status, or low-level action changed.
- phase names the strategy or stage used to advance that subtask.
- action names the logical semantic action, not the tool primitive.
- object names what the action concerns, such as a claim, test, component,
  document, or meaningful file.
- result states the observed outcome or conclusion, including failure,
  abandonment, missing evidence, or success.

Create a new segment when the persistent subtask path, phase/strategy, semantic
action, operation object, or observed outcome genuinely changes. Do not
collapse a nontrivial trajectory's distinct exploration, implementation,
testing, repair, and conclusion work into one whole-trajectory summary, and do
not make one segment per command or turn. Agent, model, session, tool, command, raw path, and raw status are
metadata/evidence and must not replace task, subtask, phase, or action frames.
Return only the required JSON."""

FORBIDDEN_RESPONSIBILITY_LABELS = {
    "agent",
    "command",
    "file path",
    "model",
    "path",
    "session",
    "shell",
    "status",
    "tool",
}

COMMAND_EXECUTABLES = {
    "apt",
    "apt-get",
    "awk",
    "bash",
    "cargo",
    "cat",
    "cd",
    "chmod",
    "chown",
    "cmake",
    "cp",
    "curl",
    "docker",
    "echo",
    "find",
    "g++",
    "gcc",
    "git",
    "grep",
    "head",
    "kill",
    "kubectl",
    "ls",
    "make",
    "mkdir",
    "mv",
    "npm",
    "pip",
    "pip3",
    "pkill",
    "ps",
    "pytest",
    "python",
    "python3",
    "qemu-img",
    "rm",
    "sed",
    "service",
    "sh",
    "ssh",
    "sshpass",
    "systemctl",
    "tail",
    "tar",
    "touch",
    "unzip",
    "wget",
}


def output_grammar(turn_count: int) -> str:
    require(turn_count >= 1, "grammar turn count")
    common = rf'''
path ::= "\"\"" | "\"" [a-zA-Z0-9] [a-zA-Z0-9 /+._:()?'=><-]{{0,{SUBTASK_PATH_MAX_CHARS - 1}}} "\""
label ::= "\"" [a-zA-Z0-9] [a-zA-Z0-9 /+._:()?'=-]{{0,{LABEL_MAX_CHARS - 1}}} "\""
'''.strip()
    final = (
        'final ::= "{\\\"subtask_path\\\":" path '
        '",\\\"phase\\\":" label '
        '",\\\"action\\\":" label '
        '",\\\"object\\\":" label '
        '",\\\"result\\\":" label "}"'
    )
    if turn_count == 1:
        return 'root ::= "{\\\"segments\\\":[" final "]}"\n' + final + "\n" + common
    boundaries = " | ".join(f'"{value}"' for value in range(turn_count - 1))
    intermediate = (
        'intermediate ::= "{\\\"through\\\":" boundary '
        '",\\\"subtask_path\\\":" path '
        '",\\\"phase\\\":" label '
        '",\\\"action\\\":" label '
        '",\\\"object\\\":" label '
        '",\\\"result\\\":" label "}"'
    )
    return (
        'root ::= "{\\\"segments\\\":[" '
        '(final | intermediate ("," intermediate)* "," final) "]}"\n'
        + intermediate
        + "\n"
        + final
        + "\n"
        + f"boundary ::= {boundaries}\n"
        + common
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)

    infer = commands.add_parser("infer")
    infer.add_argument("mode", choices=("preflight", "full"))
    infer.add_argument("--target-operations", type=Path, required=True)
    infer.add_argument("--source-cache-dir", type=Path, required=True)
    infer.add_argument("--turn-assignments", type=Path, required=True)
    infer.add_argument("--llama-url", required=True)
    infer.add_argument("--workers", type=int, default=1)
    infer.add_argument("--timeout-seconds", type=int, default=1_200)
    infer.add_argument("--out", type=Path, required=True)

    score = commands.add_parser("score")
    score.add_argument("--target-operations", type=Path, required=True)
    score.add_argument("--predictions", type=Path, required=True)
    score.add_argument("--inference-summary", type=Path, required=True)
    score.add_argument("--verified-manifest", type=Path, required=True)
    score.add_argument("--multires-assignments", type=Path, required=True)
    score.add_argument("--causal-score-rows", type=Path, required=True)
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


def write_json(path: Path, value: Any) -> None:
    source.write_json(path, value)


def write_json_atomic(path: Path, value: Any) -> None:
    source.write_json_atomic(path, value)


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    source.write_jsonl(path, rows)


def clean_label(value: Any, field: str, max_chars: int = LABEL_MAX_CHARS) -> str:
    require(isinstance(value, str), f"{field} is not a string")
    cleaned = re.sub(r"\s+", " ", value).strip()
    require(0 < len(cleaned) <= max_chars, f"{field} label length")
    require(";" not in cleaned, f"{field} contains folded-stack delimiter")
    return cleaned


def root_label(task: str) -> str:
    text = re.sub(r"\s+", " ", task).strip()
    return base.clip_text(text or "concrete task", 180)


def visible_turn(turn: dict[str, Any]) -> dict[str, Any]:
    operations = turn["operations"]
    return {
        "turn": int(turn["turn_index"]),
        "intent": base.clip_text(stateful.unique_text(operations, "intent"), INTENT_CHARS),
        "progress": base.clip_text(stateful.unique_text(operations, "progress"), PROGRESS_CHARS),
        "planned_action": base.clip_text(stateful.unique_text(operations, "action"), ACTION_CHARS),
        "visible_result": base.clip_text(stateful.unique_text(operations, "result"), RESULT_CHARS),
    }


def prompt_for(material: dict[str, Any], turns: list[dict[str, Any]]) -> str:
    payload = [visible_turn(turn) for turn in turns]
    return (
        "CONCRETE USER TASK\n"
        + base.clip_text(str(material["task"]), TASK_CHARS)
        + "\n\nCOMPLETE ORDERED TRAJECTORY\n"
        + json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
        + "\n\nThe first segment must start at turn 0 and the final segment must end at turn "
        + str(len(turns) - 1)
        + ". Adjacent segments must be gap-free and nonoverlapping."
    )


def server_properties(llama_url: str, timeout_seconds: int) -> dict[str, int]:
    response = requests.get(llama_url.rstrip("/") + "/props", timeout=timeout_seconds)
    response.raise_for_status()
    payload = response.json()
    defaults = payload["default_generation_settings"]
    return {
        "slots": int(payload["total_slots"]),
        "context_tokens": int(defaults["n_ctx"]),
    }


def token_count(llama_url: str, content: str, timeout_seconds: int) -> int:
    response = requests.post(
        llama_url.rstrip("/") + "/tokenize",
        json={"content": content, "add_special": True, "with_pieces": False},
        timeout=timeout_seconds,
    )
    response.raise_for_status()
    tokens = response.json().get("tokens")
    require(isinstance(tokens, list), "tokenizer response has no tokens")
    return len(tokens)


def parse_segments(raw: str, turn_count: int) -> list[dict[str, Any]]:
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as error:
        raise RuntimeError(f"model output is not JSON: {raw[:200]!r}") from error
    require(isinstance(payload, dict) and set(payload) == {"segments"}, "output keys")
    rows = payload["segments"]
    require(isinstance(rows, list) and rows, "segments must be nonempty")
    expected_start = 0
    parsed: list[dict[str, Any]] = []
    semantic_keys = {"subtask_path", "phase", "action", "object", "result"}
    for index, row in enumerate(rows):
        require(isinstance(row, dict), f"segment {index} object")
        final = index == len(rows) - 1
        require(
            set(row) == (semantic_keys if final else semantic_keys | {"through"}),
            f"segment {index} keys",
        )
        start = expected_start
        end = turn_count - 1 if final else row["through"]
        require(type(end) is int, f"segment {index} end")
        require(start <= end < turn_count, f"segment {index} range or order")
        path_raw = row["subtask_path"]
        require(isinstance(path_raw, str), f"segment {index} subtask path")
        subtasks = [
            clean_label(value, f"segment {index} subtask", SUBTASK_PATH_MAX_CHARS)
            for value in path_raw.split(">")
            if value.strip()
        ]
        responsibility_labels = [
            *subtasks,
            clean_label(row["phase"], f"segment {index} phase"),
            clean_label(row["action"], f"segment {index} action"),
        ]
        require(
            not any(label.casefold() in FORBIDDEN_RESPONSIBILITY_LABELS for label in responsibility_labels),
            f"segment {index} uses a system field as responsibility",
        )
        parsed.append(
            {
                "start": start,
                "end": end,
                "subtasks": subtasks,
                "phase": responsibility_labels[-2],
                "action": responsibility_labels[-1],
                "object": clean_label(row["object"], f"segment {index} object"),
                "result": clean_label(row["result"], f"segment {index} result"),
            }
        )
        expected_start = end + 1
    require(expected_start == turn_count, "segments do not cover final turn")
    return parsed


def request_hash(prompt: str, grammar: str) -> str:
    contract = {
        "algorithm": ALGORITHM_VERSION,
        "model": base.MODEL,
        "model_sha256": base.MODEL_SHA256,
        "seed": SEED,
        "temperature": 0,
        "system": SYSTEM_PROMPT,
        "grammar": grammar,
        "prompt": prompt,
    }
    return hashlib.sha256(
        json.dumps(contract, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def call_model(
    llama_url: str,
    prompt: str,
    grammar: str,
    max_tokens: int,
    timeout_seconds: int,
) -> tuple[str, dict[str, Any], float]:
    started = time.monotonic()
    response = requests.post(
        llama_url.rstrip("/") + "/v1/chat/completions",
        json={
            "model": base.MODEL,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0,
            "seed": SEED,
            "max_tokens": max_tokens,
            "grammar": grammar,
            "stream": False,
        },
        timeout=timeout_seconds,
    )
    elapsed = time.monotonic() - started
    response.raise_for_status()
    payload = response.json()
    choice = payload["choices"][0]
    require(choice.get("finish_reason") != "length", "model exhausted completion budget")
    return str(choice["message"]["content"]), payload, elapsed


def parse_cached_operation(text: str) -> dict[str, Any]:
    value = json.loads(text)
    require(isinstance(value, dict), "cached source operation is not an object")
    step = value.get("step")
    require(type(step) is int and step > 0, "cached source operation step")
    return {
        "step": step,
        "intent": str(value.get("native_intent") or ""),
        "progress": str(value.get("native_progress") or ""),
        "action": str(value.get("source_action") or ""),
        "result": str(value.get("result") or ""),
    }


def load_turn_assignments(path: Path) -> dict[tuple[str, int], dict[str, Any]]:
    rows: dict[tuple[str, int], dict[str, Any]] = {}
    with path.open(encoding="utf-8") as stream:
        for line_number, line in enumerate(stream, 1):
            row = json.loads(line)
            key = (str(row["session"]), int(row["step_id"]))
            require(key not in rows, f"duplicate turn assignment {line_number}")
            rows[key] = {
                "turn_index": int(row["turn_index"]),
                "turn_id": str(row["turn_instance"]),
                "source_ref": str(row["source_ref"]),
            }
    return rows


def reconstruct_from_completed_cache(
    cache_dir: Path,
    session: str,
    target_rows: list[dict[str, Any]],
    turn_assignments: dict[tuple[str, int], dict[str, Any]],
) -> dict[str, Any]:
    path = cache_dir / source.cache_name(session)
    require(path.is_file(), f"missing completed source cache: {path}")
    cache = json.loads(path.read_text(encoding="utf-8"))
    require(cache.get("session") == session, "completed source cache session")
    decisions = cache.get("decisions")
    require(isinstance(decisions, list) and decisions, "completed source cache decisions")
    operations: dict[int, dict[str, Any]] = {}
    task = ""
    for decision in decisions:
        user = str(decision["user"])
        task_candidate, pair = user.split("\n\nLEFT COMPLETED OPERATION\n", 1)
        task_candidate = task_candidate.removeprefix("CONCRETE TASK\n")
        if len(task_candidate) > len(task):
            task = task_candidate
        left, right = pair.split("\n\nRIGHT COMPLETED OPERATION\n", 1)
        for raw in (left, right):
            candidate = parse_cached_operation(raw)
            step = int(candidate["step"])
            previous = operations.get(step)
            if previous is None or sum(len(str(value)) for value in candidate.values()) > sum(
                len(str(value)) for value in previous.values()
            ):
                operations[step] = candidate
    expected_steps = [int(row["step_id"]) for row in target_rows]
    require(sorted(operations) == expected_steps, f"{session}: completed cache coverage")
    material_operations = []
    for step in expected_steps:
        assignment = turn_assignments.get((session, step))
        require(assignment is not None, f"{session}: missing turn assignment {step}")
        material_operations.append(
            {
                **operations[step],
                "turn_id": assignment["turn_id"],
                "source_ref": assignment["source_ref"],
            }
        )
    return {
        "session": session,
        "framework": str(cache["framework"]),
        "adapter": str(cache["adapter"]),
        "archive": str(cache["archive"]),
        "archive_sha256": str(cache["archive_sha256"]),
        "task": task,
        "task_source": str(cache["task_source"]),
        "operations": material_operations,
    }


def prepare_sessions(
    grouped: dict[str, list[dict[str, Any]]],
    source_cache_dir: Path,
    turn_assignments: dict[tuple[str, int], dict[str, Any]],
    llama_url: str,
    timeout_seconds: int,
) -> dict[str, dict[str, Any]]:
    prepared: dict[str, dict[str, Any]] = {}
    for number, session in enumerate(sorted(grouped), 1):
        material = reconstruct_from_completed_cache(
            source_cache_dir, session, grouped[session], turn_assignments
        )
        turns = stateful.group_turns(material["operations"])
        prompt = prompt_for(material, turns)
        projected_tokens = token_count(
            llama_url, SYSTEM_PROMPT + "\n" + prompt, timeout_seconds
        )
        prepared[session] = {
            "material": material,
            "turns": turns,
            "prompt": prompt,
            "projected_tokens": projected_tokens,
        }
        if number % 50 == 0 or number == len(grouped):
            print(f"prepared {number}/{len(grouped)}", flush=True)
    return prepared


def preflight_sessions(prepared: dict[str, dict[str, Any]]) -> list[str]:
    by_framework: dict[str, list[str]] = defaultdict(list)
    for session, row in prepared.items():
        by_framework[str(row["material"]["framework"])].append(session)
    require(set(by_framework) == EXPECTED_FRAMEWORKS, "preflight framework coverage")
    return sorted(
        max(sessions, key=lambda session: (prepared[session]["projected_tokens"], session))
        for sessions in by_framework.values()
    )


def cache_name(session: str) -> str:
    return hashlib.sha256(session.encode()).hexdigest()[:24] + ".json"


def infer_one(
    session: str,
    prepared: dict[str, Any],
    llama_url: str,
    timeout_seconds: int,
    cache_dir: Path,
    context_tokens: int,
) -> dict[str, Any]:
    material = prepared["material"]
    turns = prepared["turns"]
    prompt = prepared["prompt"]
    projected_tokens = int(prepared["projected_tokens"])
    require(
        projected_tokens + MIN_OUTPUT_TOKENS + CONTEXT_MARGIN <= context_tokens,
        f"{session}: prompt plus minimum completion budget exceeds context",
    )
    completion_budget = min(
        MAX_OUTPUT_TOKENS,
        context_tokens - projected_tokens - CONTEXT_MARGIN,
    )
    grammar = output_grammar(len(turns))
    digest = request_hash(prompt, grammar)
    path = cache_dir / cache_name(session)
    if path.is_file():
        result = json.loads(path.read_text(encoding="utf-8"))
        require(result.get("algorithm_version") == ALGORITHM_VERSION, "cache algorithm")
        require(result.get("session") == session, "cache session")
        require(result.get("archive_sha256") == material["archive_sha256"], "cache archive")
        require(result.get("request_sha256") == digest, "cache request drift")
        segments = parse_segments(str(result["raw_response"]), len(turns))
        require(result["segments"] == segments, "cache parsed segments")
        return result

    raw, response, elapsed = call_model(
        llama_url, prompt, grammar, completion_budget, timeout_seconds
    )
    segments = parse_segments(raw, len(turns))
    usage = response.get("usage") or {}
    actual_prompt_tokens = int(usage.get("prompt_tokens", 0))
    require(actual_prompt_tokens > 0, "missing actual prompt tokens")
    require(
        actual_prompt_tokens + completion_budget <= context_tokens,
        f"{session}: actual chat prompt plus completion budget exceeds context",
    )
    result = {
        "schema": SCHEMA + ".session.v1",
        "algorithm_version": ALGORITHM_VERSION,
        "session": session,
        "framework": material["framework"],
        "adapter": material["adapter"],
        "archive": material["archive"],
        "archive_sha256": material["archive_sha256"],
        "task_source": material["task_source"],
        "task": material["task"],
        "root_label": root_label(str(material["task"])),
        "model": base.MODEL,
        "model_sha256": base.MODEL_SHA256,
        "seed": SEED,
        "input_turns": len(turns),
        "input_operations": len(material["operations"]),
        "projected_prompt_tokens": projected_tokens,
        "completion_budget": completion_budget,
        "request_sha256": digest,
        "prompt": prompt,
        "raw_response": raw,
        "segments": segments,
        "usage": usage,
        "elapsed_seconds": elapsed,
    }
    write_json_atomic(path, result)
    return result


def predictions_for(result: dict[str, Any], prepared: dict[str, Any]) -> list[dict[str, Any]]:
    turns = prepared["turns"]
    session = str(result["session"])
    root = str(result["root_label"])
    rows: list[dict[str, Any]] = []
    for segment_index, segment in enumerate(result["segments"]):
        stack = [
            {"kind": "task", "label": root},
            *({"kind": "subtask", "label": label} for label in segment["subtasks"]),
            {"kind": "phase_or_strategy", "label": segment["phase"]},
            {"kind": "semantic_action", "label": segment["action"]},
            {"kind": "operation_object", "label": segment["object"]},
            {"kind": "result", "label": segment["result"]},
        ]
        instance = f"{session}:global-segment-{segment_index:04d}"
        for turn_index in range(int(segment["start"]), int(segment["end"]) + 1):
            turn = turns[turn_index]
            for operation in turn["operations"]:
                rows.append(
                    {
                        "session": session,
                        "framework": result["framework"],
                        "adapter": result["adapter"],
                        "step_id": int(operation["step"]),
                        "turn_index": turn_index,
                        "source_turn_id": turn["source_turn_id"],
                        "source_ref": operation["source_ref"],
                        "segment_index": segment_index,
                        "segment_instance": instance,
                        "task_root": root,
                        "subtasks": list(segment["subtasks"]),
                        "phase": segment["phase"],
                        "semantic_action": segment["action"],
                        "operation_object": segment["object"],
                        "semantic_result": segment["result"],
                        "semantic_stack": stack,
                    }
                )
    expected = sum(len(turn["operations"]) for turn in turns)
    require(len(rows) == expected, f"{session}: expanded operation coverage")
    require(len({row["step_id"] for row in rows}) == expected, f"{session}: step uniqueness")
    return rows


def semantic_output_diagnostics(
    results: dict[str, dict[str, Any]], selected: list[str]
) -> dict[str, Any]:
    total_segments = 0
    path_at_cap = 0
    path_near_cap = 0
    repeated_path = 0
    adjacent_repeated_path = 0
    all_same_path = 0
    command_primitive_action = 0
    sessions_with_internal_boundary = 0
    for session in selected:
        result = results[session]
        parsed_segments = result["segments"]
        raw_segments = json.loads(str(result["raw_response"]))["segments"]
        require(len(parsed_segments) == len(raw_segments), "raw/parsed segment mismatch")
        sessions_with_internal_boundary += len(parsed_segments) > 1
        for parsed, raw in zip(parsed_segments, raw_segments):
            total_segments += 1
            raw_path = str(raw["subtask_path"])
            path_at_cap += len(raw_path) == SUBTASK_PATH_MAX_CHARS
            path_near_cap += len(raw_path) >= SUBTASK_PATH_MAX_CHARS - 4
            normalized = [str(frame).casefold() for frame in parsed["subtasks"]]
            repeated_path += len(set(normalized)) < len(normalized)
            adjacent_repeated_path += any(
                left == right for left, right in zip(normalized, normalized[1:])
            )
            all_same_path += len(normalized) > 1 and len(set(normalized)) == 1
            tokens = str(parsed["action"]).casefold().split()
            direct_command = bool(tokens) and tokens[0] in COMMAND_EXECUTABLES
            wrapped_command = (
                len(tokens) > 1
                and tokens[0] in {"run", "execute"}
                and tokens[1] in COMMAND_EXECUTABLES
            )
            command_primitive_action += direct_command or wrapped_command
    return {
        "segments": total_segments,
        "sessions_with_internal_boundary": sessions_with_internal_boundary,
        "subtask_path_exactly_at_384_char_cap": path_at_cap,
        "subtask_path_at_least_380_chars": path_near_cap,
        "subtask_path_with_repeated_frame": repeated_path,
        "subtask_path_with_adjacent_repeated_frame": adjacent_repeated_path,
        "subtask_path_with_all_frames_identical": all_same_path,
        "command_primitive_shaped_semantic_action": command_primitive_action,
        "diagnostic_scope": (
            "output-shape and qualitative responsibility-frame diagnostics; "
            "not paper metrics"
        ),
    }


def run_inference(args: argparse.Namespace) -> None:
    require(args.workers == 1, "the reviewed full-context server is single-slot")
    target_path = absolute(args.target_operations)
    source_cache_dir = absolute(args.source_cache_dir)
    turn_assignment_path = absolute(args.turn_assignments)
    out_dir = absolute(args.out)
    require(target_path.is_file(), f"missing target operations: {target_path}")
    require(source_cache_dir.is_dir(), f"missing source cache: {source_cache_dir}")
    require(turn_assignment_path.is_file(), f"missing turn assignments: {turn_assignment_path}")
    props = server_properties(args.llama_url, args.timeout_seconds)
    require(props["slots"] == 1, "llama server must expose exactly one slot")
    require(props["context_tokens"] == CONTEXT_TOKENS, "llama server context is not 32768")

    grouped = base.load_visible_operations(target_path)
    require(len(grouped) == EXPECTED_SESSIONS, "unexpected source population")
    started = time.monotonic()
    turn_assignments = load_turn_assignments(turn_assignment_path)
    require(len(turn_assignments) == EXPECTED_OPERATIONS, "turn assignment population")
    prepared = prepare_sessions(
        grouped,
        source_cache_dir,
        turn_assignments,
        args.llama_url,
        args.timeout_seconds,
    )
    selected = sorted(prepared) if args.mode == "full" else preflight_sessions(prepared)
    cache_dir = out_dir / "sessions"
    cache_dir.mkdir(parents=True, exist_ok=True)
    results: dict[str, dict[str, Any]] = {}
    predictions: list[dict[str, Any]] = []
    for number, session in enumerate(selected, 1):
        result = infer_one(
            session,
            prepared[session],
            args.llama_url,
            args.timeout_seconds,
            cache_dir,
            props["context_tokens"],
        )
        results[session] = result
        predictions.extend(predictions_for(result, prepared[session]))
        print(f"inferred {number}/{len(selected)} {session}", flush=True)

    expected_operations = sum(len(grouped[session]) for session in selected)
    expected_turns = sum(len(prepared[session]["turns"]) for session in selected)
    require(len(predictions) == expected_operations, "prediction coverage")
    require(
        len({(row["session"], row["step_id"]) for row in predictions}) == expected_operations,
        "prediction uniqueness",
    )
    write_jsonl(out_dir / "predictions.jsonl", predictions)
    usage = Counter()
    for result in results.values():
        for key in ("prompt_tokens", "completion_tokens", "total_tokens"):
            value = (result.get("usage") or {}).get(key)
            if isinstance(value, int):
                usage[key] += value
    segment_counts = [len(result["segments"]) for result in results.values()]
    subtask_depths = [
        len(segment["subtasks"])
        for result in results.values()
        for segment in result["segments"]
    ]
    summary = {
        "schema": SCHEMA + ".inference.v1",
        "algorithm_version": ALGORITHM_VERSION,
        "mode": args.mode,
        "status": "complete",
        "model": base.MODEL,
        "model_sha256": base.MODEL_SHA256,
        "seed": SEED,
        "server": props,
        "sessions": len(selected),
        "turns": expected_turns,
        "operations": len(predictions),
        "frameworks": dict(Counter(results[session]["framework"] for session in selected)),
        "selected_sessions": selected,
        "segments": {
            "total": sum(segment_counts),
            "minimum_per_session": min(segment_counts),
            "maximum_per_session": max(segment_counts),
            "mean_per_session": sum(segment_counts) / len(segment_counts),
        },
        "subtask_depth": {
            "minimum": min(subtask_depths),
            "maximum": max(subtask_depths),
            "mean": sum(subtask_depths) / len(subtask_depths),
            "counts": dict(sorted(Counter(subtask_depths).items())),
        },
        "semantic_output_diagnostics": semantic_output_diagnostics(results, selected),
        "prompt_tokens": {
            "minimum": min(results[session]["projected_prompt_tokens"] for session in selected),
            "maximum": max(results[session]["projected_prompt_tokens"] for session in selected),
        },
        "model_usage": dict(usage),
        "wall_seconds": time.monotonic() - started,
        "predictions": relative(out_dir / "predictions.jsonl"),
        "isolation": {
            "official_manifest_opened": False,
            "official_stages_opened": False,
            "visible_fields": [
                "concrete user task",
                "complete ordered native intent",
                "native progress",
                "planned source action",
                "visible source result",
            ],
            "future_source_context_visible": True,
            "agent_model_session_status_used_as_frames": False,
            "all_turns_and_operations_retained": True,
        },
    }
    if args.mode == "full":
        require(len(selected) == EXPECTED_SESSIONS, "full sessions")
        require(expected_turns == EXPECTED_TURNS, "full turns")
        require(len(predictions) == EXPECTED_OPERATIONS, "full operations")
    write_json(out_dir / "inference-summary.json", summary)
    print(json.dumps(summary, sort_keys=True), flush=True)


def load_predictions(path: Path) -> dict[tuple[str, int], dict[str, Any]]:
    rows: dict[tuple[str, int], dict[str, Any]] = {}
    with path.open(encoding="utf-8") as stream:
        for line_number, line in enumerate(stream, 1):
            row = json.loads(line)
            key = (str(row["session"]), int(row["step_id"]))
            require(key not in rows, f"duplicate prediction line {line_number}")
            require(isinstance(row.get("semantic_stack"), list), "missing semantic stack")
            rows[key] = row
    return rows


def load_causal(path: Path) -> dict[tuple[str, int], str]:
    rows: dict[tuple[str, int], str] = {}
    with path.open(encoding="utf-8") as stream:
        for line_number, line in enumerate(stream, 1):
            row = json.loads(line)
            key = (str(row["session"]), int(row["step_id"]))
            require(key not in rows, f"duplicate causal row {line_number}")
            rows[key] = str(row["causal_visible_path"])
    return rows


def score_rows(
    grouped: dict[str, list[dict[str, Any]]],
    selected: list[str],
    predictions: dict[tuple[str, int], dict[str, Any]],
    baselines: dict[tuple[str, int], dict[str, str]],
    causal: dict[tuple[str, int], str],
    official: dict[tuple[str, int], str],
    frameworks: dict[str, str],
    tasks: dict[str, str],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    operations: list[dict[str, Any]] = []
    pairs: list[dict[str, Any]] = []
    methods = ("candidate", "multires_recurrence", "causal_qwen")
    for session in selected:
        previous: dict[str, Any] | None = None
        for source_row in grouped[session]:
            key = (session, int(source_row["step_id"]))
            require(key in predictions and key in baselines and key in causal, "score coverage")
            prediction = predictions[key]
            operation = {
                "session": session,
                "framework": frameworks[session],
                "task_name": tasks[session],
                "step_id": key[1],
                "official_stage": official[key],
                "candidate": str(prediction["segment_instance"]),
                "candidate_path": json.dumps(prediction["semantic_stack"], ensure_ascii=False),
                "multires_recurrence": baselines[key]["multires_recurrence"],
                "causal_qwen": causal[key],
            }
            operations.append(operation)
            if previous is not None:
                pair = {
                    "session": session,
                    "framework": frameworks[session],
                    "task_name": tasks[session],
                    "position": key[1] - 1,
                    "official_boundary": previous["official_stage"] != operation["official_stage"],
                }
                for method in methods:
                    pair[method] = previous[method] != operation[method]
                pairs.append(pair)
            previous = operation
    return pairs, operations


def metric_bundle(
    pairs: list[dict[str, Any]], operations: list[dict[str, Any]], methods: Iterable[str]
) -> dict[str, Any]:
    return {
        method: {
            "bcubed": base.bcubed(operations, method),
            "span": base.span_metrics(operations, method),
            "boundary": base.boundary_metrics(pairs, method),
        }
        for method in methods
    }


def report(summary: dict[str, Any]) -> str:
    lines = [
        "# Global Task-Semantic Segmentation — Result",
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
    interval = summary["bootstrap"]["candidate_minus_multires"]["ci95"]
    lines.extend(
        [
            "",
            "## Registered comparison",
            "",
            f"Candidate minus current multi-resolution recurrence paired task-cluster 95% interval: `[{interval[0]:+.6f}, {interval[1]:+.6f}]`.",
            "",
            "## Semantic-output audit",
            "",
            f"Task-progress partition contract: **{summary['semantic_contract']['task_progress_partition_contract']}**.",
            f"Qualitative responsibility-frame contract: **{summary['semantic_contract']['qualitative_responsibility_frame_contract']}**.",
            "",
            "## Claim boundary",
            "",
            summary["claim_boundary"],
            "",
        ]
    )
    return "\n".join(lines)


def safe_frame(kind: str, label: str) -> str:
    return f"{kind} · {re.sub(r'[;\r\n\t]+', ' ', label).strip()}"


class FlameNode:
    def __init__(self, frame: str) -> None:
        self.frame = frame
        self.value = 0
        self.children: dict[str, FlameNode] = {}


def frame_color(frame: str) -> str:
    kind = frame.split(" · ", 1)[0]
    return {
        "Task": "#23395d",
        "Subtask": "#2f80ed",
        "Phase/strategy": "#00a6a6",
        "Semantic action": "#6c5ce7",
        "Operation object": "#a8c7ee",
        "Result": "#43b581",
    }.get(kind, "#7f8c8d")


def write_representative_flamegraph(
    out_dir: Path,
    predictions: dict[tuple[str, int], dict[str, Any]],
    grouped: dict[str, list[dict[str, Any]]],
    selected: list[str],
) -> dict[str, Any]:
    session = max(selected, key=lambda value: (len(grouped[value]), value))
    session_rows = [
        predictions[(session, int(row["step_id"]))] for row in grouped[session]
    ]
    collapsed: Counter[tuple[str, ...]] = Counter()
    for row in session_rows:
        frames = []
        for item in row["semantic_stack"]:
            kind = {
                "task": "Task",
                "subtask": "Subtask",
                "phase_or_strategy": "Phase/strategy",
                "semantic_action": "Semantic action",
                "operation_object": "Operation object",
                "result": "Result",
            }[item["kind"]]
            frames.append(safe_frame(kind, str(item["label"])))
        collapsed[tuple(frames)] += 1
    folded = out_dir / "representative-task-semantic.folded"
    folded.write_text(
        "\n".join(f"{';'.join(stack)} {value}" for stack, value in sorted(collapsed.items())) + "\n",
        encoding="utf-8",
    )

    tree = FlameNode("root")
    for stack, value in collapsed.items():
        tree.value += value
        node = tree
        for frame in stack:
            node = node.children.setdefault(frame, FlameNode(frame))
            node.value += value
    max_depth = max(len(stack) for stack in collapsed)
    width = 1900
    plot_x = 28
    plot_width = width - 56
    top = 118
    frame_height = 38
    height = top + max_depth * frame_height + 44
    title = str(session_rows[0]["task_root"])
    svg = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        "<style>text{font-family:Inter,ui-sans-serif,system-ui,sans-serif}.title{font-size:24px;font-weight:750;fill:#17253d}.subtitle{font-size:13px;fill:#60708a}.label{font-size:11px;font-weight:700}.value{font-size:9px;font-weight:500;opacity:.9}.frame rect{stroke:#fff;stroke-width:2}</style>",
        '<rect width="100%" height="100%" fill="#f7f9fc"/>',
        '<text class="title" x="28" y="34">Automatic task-semantic flamegraph · complete real trajectory</text>',
        f'<text class="subtitle" x="28" y="60">{html.escape(title)}</text>',
        f'<text class="subtitle" x="28" y="84">{len(session_rows)} operations · global Qwen2.5-3B decomposition · variable subtask depth · width = operation count</text>',
        '<text class="subtitle" x="28" y="104">Agent/model/session/tool/command/path/status are metadata or source evidence, not responsibility frames.</text>',
    ]

    def short(text: str, pixel_width: float) -> str:
        limit = max(0, int((pixel_width - 14) / 6.4))
        if limit < 4:
            return ""
        return text if len(text) <= limit else text[: limit - 1] + "…"

    def render(node: FlameNode, x: float, depth: int, prefix: tuple[str, ...]) -> None:
        rect_width = node.value / tree.value * plot_width
        if rect_width < 0.7:
            return
        y = top + (max_depth - depth) * frame_height
        kind, label = node.frame.split(" · ", 1)
        full_path = " → ".join(item.split(" · ", 1)[1] for item in (*prefix, node.frame))
        text_fill = "#10233f" if kind == "Operation object" else "#ffffff"
        svg.append(f'<g class="frame"><title>{html.escape(full_path)}\n{node.value} operations</title>')
        svg.append(
            f'<rect x="{x:.3f}" y="{y}" width="{rect_width:.3f}" height="{frame_height - 3}" rx="6" fill="{frame_color(node.frame)}"/>'
        )
        shown = short(f"{kind}: {label}", rect_width)
        if shown:
            svg.append(
                f'<text class="label" x="{x + 7:.3f}" y="{y + 15}" fill="{text_fill}">{html.escape(shown)}</text>'
            )
            value_text = f"{node.value} ops · {100 * node.value / tree.value:.1f}%"
            if rect_width > len(value_text) * 5.5 + 16:
                svg.append(
                    f'<text class="value" x="{x + 7:.3f}" y="{y + 29}" fill="{text_fill}">{value_text}</text>'
                )
        svg.append("</g>")
        child_x = x
        for child in sorted(node.children.values(), key=lambda item: (-item.value, item.frame)):
            render(child, child_x, depth + 1, (*prefix, node.frame))
            child_x += child.value / tree.value * plot_width

    child_x = float(plot_x)
    for child in sorted(tree.children.values(), key=lambda item: (-item.value, item.frame)):
        render(child, child_x, 1, ())
        child_x += child.value / tree.value * plot_width
    svg.append("</svg>")
    svg_path = out_dir / "representative-task-semantic.svg"
    svg_path.write_text("\n".join(svg) + "\n", encoding="utf-8")
    return {
        "selection_rule": "complete selected session with maximum operation count; lexical tie break",
        "session": session,
        "operations": len(session_rows),
        "segments": len({row["segment_instance"] for row in session_rows}),
        "maximum_stack_depth": max_depth,
        "folded": relative(folded),
        "svg": relative(svg_path),
    }


def run_score(args: argparse.Namespace) -> None:
    target_path = absolute(args.target_operations)
    prediction_path = absolute(args.predictions)
    inference_path = absolute(args.inference_summary)
    manifest_path = absolute(args.verified_manifest)
    baseline_path = absolute(args.multires_assignments)
    causal_path = absolute(args.causal_score_rows)
    out_dir = absolute(args.out)
    for path in (target_path, prediction_path, inference_path, manifest_path, baseline_path, causal_path):
        require(path.is_file(), f"missing score input: {path}")
    inference = json.loads(inference_path.read_text(encoding="utf-8"))
    require(inference.get("status") == "complete", "inference incomplete")
    mode = str(inference["mode"])
    grouped = base.load_visible_operations(target_path)
    predictions = load_predictions(prediction_path)
    selected = sorted({session for session, _ in predictions})
    expected = {
        (session, int(row["step_id"]))
        for session in selected
        for row in grouped[session]
    }
    require(set(predictions) == expected, "prediction score coverage")
    baselines = base.load_baselines(baseline_path)
    causal = load_causal(causal_path)
    require(expected <= set(baselines) and expected <= set(causal), "baseline score coverage")

    official, frameworks, tasks = base.load_stages_after_prediction(
        manifest_path, grouped, selected
    )
    pairs, operations = score_rows(
        grouped, selected, predictions, baselines, causal, official, frameworks, tasks
    )
    methods = ("candidate", "multires_recurrence", "causal_qwen")
    metrics = metric_bundle(pairs, operations, methods)
    out_dir.mkdir(parents=True, exist_ok=True)
    candidate_minus_multires = source.bcubed_task_bootstrap(
        operations,
        "candidate",
        "multires_recurrence",
        out_dir / "bootstrap-candidate-minus-multires.jsonl",
    )
    candidate_minus_causal = source.bcubed_task_bootstrap(
        operations,
        "candidate",
        "causal_qwen",
        out_dir / "bootstrap-candidate-minus-causal.jsonl",
    )
    per_framework = {}
    for framework in sorted(set(frameworks.values())):
        local_operations = [row for row in operations if row["framework"] == framework]
        local_pairs = [row for row in pairs if row["framework"] == framework]
        per_framework[framework] = metric_bundle(local_pairs, local_operations, methods)
    candidate_f1 = metrics["candidate"]["bcubed"]["f1"]
    incumbent_f1 = metrics["multires_recurrence"]["bcubed"]["f1"]
    supported = candidate_f1 > incumbent_f1 and candidate_minus_multires["ci95"][0] > 0
    contradicted = candidate_minus_multires["ci95"][1] <= 0
    interpretation = (
        "diagnostic-preflight"
        if mode == "preflight"
        else "supported-and-adopted"
        if supported
        else "contradicted-not-adopted"
        if contradicted
        else "inconclusive-not-adopted"
    )
    figure = write_representative_flamegraph(out_dir, predictions, grouped, selected)
    summary = {
        "schema": SCHEMA + ".score.v1",
        "mode": mode,
        "status": "complete",
        "registered_interpretation": interpretation,
        "population": {
            "sessions": len(selected),
            "turns": int(inference["turns"]),
            "operations": len(operations),
            "pairs": len(pairs),
            "official_stages": len(set(official.values())),
            "task_clusters": len(set(tasks.values())),
            "frameworks": dict(Counter(frameworks.values())),
        },
        "metrics": metrics,
        "bootstrap": {
            "candidate_minus_multires": candidate_minus_multires,
            "candidate_minus_causal": candidate_minus_causal,
        },
        "per_framework": per_framework,
        "decision": {
            "primary_metric": "ordinary unweighted operation-level B-cubed F1",
            "incumbent": "multires_recurrence",
            "candidate_point_higher": candidate_f1 > incumbent_f1,
            "candidate_interval_wholly_positive": candidate_minus_multires["ci95"][0] > 0,
            "candidate_interval_wholly_nonpositive": contradicted,
        },
        "semantic_contract": {
            "main_stack": [
                "concrete task",
                "zero or more nested subtasks",
                "phase or strategy",
                "semantic action",
                "operation object",
                "result",
            ],
            "exact_turn_and_operation_coverage": True,
            "exact_reserved_system_word_check_passed": True,
            "system_fields_excluded_from_leading_schema": True,
            "qualitative_responsibility_frame_contract": (
                "failed"
                if inference["semantic_output_diagnostics"][
                    "command_primitive_shaped_semantic_action"
                ]
                else "no-command-primitive-detected"
            ),
            "task_progress_partition_contract": (
                "failed-no-internal-boundary"
                if metrics["candidate"]["boundary"]["true_positive"] == 0
                else "has-internal-boundary-evidence"
            ),
            "configured_frame_count_cap": None,
            "serialized_subtask_path_char_cap": SUBTASK_PATH_MAX_CHARS,
            "observed_output_diagnostics": inference["semantic_output_diagnostics"],
        },
        "figure": figure,
        "claim_boundary": (
            "CodeTraceBench's flat human stages test the emitted contiguous segment "
            "partition. They do not quantitatively validate nested ancestor topology "
            "or open-vocabulary label meaning. A rendered stack is diagnostic output, "
            "not positive representation evidence unless an independent semantic "
            "review separately accepts its responsibility frames."
        ),
    }
    if mode == "full":
        require(len(selected) == EXPECTED_SESSIONS, "full scored sessions")
        require(len(operations) == EXPECTED_OPERATIONS, "full scored operations")
        require(len(pairs) == EXPECTED_OPERATIONS - EXPECTED_SESSIONS, "full scored pairs")
        require(len(set(official.values())) == EXPECTED_STAGES, "full official stages")
        require(len(set(tasks.values())) == EXPECTED_TASKS, "full task clusters")
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
        run_score(args)


if __name__ == "__main__":
    main()
