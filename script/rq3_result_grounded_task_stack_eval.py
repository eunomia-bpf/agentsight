#!/usr/bin/env python3
"""Evaluate a result-grounded variable-depth task stack.

The controller uses one OPEN decision before a source-native turn and one
CLOSE decision after its visible result.  A persistent frame stores only a
task label and an observable completion condition.  ToolSandbox scoring uses
the public TED per-turn progress curves only after predictions are complete;
CodeTrace scoring reuses the already verified Step 0059 score rows.
"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import json
import math
from pathlib import Path
import random
import re
import statistics
import sys
import time
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "script"))

import rq3_recurrence_stack_induction_eval as recurrence  # noqa: E402
import rq3_source_native_task_progress_boundary_eval as source  # noqa: E402
import rq3_stateful_native_turn_task_stack_eval as stateful  # noqa: E402
import rq3_stateful_visible_path_identity_eval as visible  # noqa: E402


base = source.base
ALGORITHM_VERSION = "result-grounded-task-stack-v1"
CANDIDATE_CACHE_REVISION = "semantic-close-projection-r7"
BASELINE_CACHE_REVISION = "fresh-causal-source-r6"
SCHEMA = "agentsight.rq3-result-grounded-task-stack"
MODEL = base.MODEL
MODEL_SHA256 = base.MODEL_SHA256
SEED = 20_260_720
BOOTSTRAP_RESAMPLES = 10_000
LABEL_MAX_CHARS = 64
DONE_MAX_CHARS = 160
OUTPUT_TOKENS = 128
LABEL_RE = re.compile(r"^[a-z][a-z0-9 /+._,:;()-]*$")
PHASE_RE = re.compile(r"^phase-?\d+$")
COMMANDISH_RE = re.compile(
    r"(?:^|[ /+._,:;()-])(?:cd|cat|grep|rg|sed|git|python|pytest|cargo|npm|"
    r"file|path|command|tool|phase)(?:$|[ /+._,:;()-])"
)
ROOT_DONE_WHEN = "the user's concrete task is satisfied and truthfully reported"

EXPECTED_CODETRACE_SESSIONS = 405
EXPECTED_CODETRACE_TURNS = 17_148
EXPECTED_CODETRACE_OPERATIONS = 20_866
EXPECTED_CODETRACE_STAGES = 2_948
EXPECTED_CODETRACE_TASKS = 251

EXPECTED_TS_FILES = 96
EXPECTED_TS_CONDITIONS = 12
EXPECTED_TS_TRAJECTORIES = 3_551
EXPECTED_TS_SCENARIOS = 37
EXPECTED_TS_TURNS = 9_485
EXPECTED_TS_BOUNDARIES = 3_867
EXPECTED_TS_PADDED_POSITIVE = 5

OPEN_SYSTEM = """Maintain the active TASK stack for one AI agent. The root is
the user's immutable concrete task. Persistent child frames are only nested,
user-facing task goals with an observable completion condition. A phase,
strategy, semantic action, tool, command, file, path, object, status, result,
inspect/edit/test/retry step, or one atomic operation is evidence about a task,
not itself a persistent task frame.

Return continue when the current request advances the active task. Return
start only when it begins one genuinely nested goal that can own this turn and
possibly later turns. A start label is a concise lowercase goal phrase. It
must describe why the work is done, not copy a command, tool, file, path,
status, or phase. done_when is a concise lowercase observable outcome, not
another action. Return only the required JSON."""

CLOSE_SYSTEM = """Judge whether the current visible result newly satisfies
the active TASK leaf's stored completion condition. Return complete only when
the result provides affirmative evidence that the condition now holds. An attempted action,
tool invocation without its outcome, intermediate progress, inspection,
error, retry, plan, or promise is not completion. Return only the required
JSON."""

BASELINE_SYSTEM = """Maintain the active TASK stack for one AI agent. The
immutable concrete task is the root and is never removed. Persistent frames
are only nested task goals or responsibilities with a completion condition.
Use stay when the current turn advances the leaf. Use push only when it begins
one genuinely nested user-facing goal. Use pop only when the preceding visible
result completed the active child and its parent resumes. Pop
removes exactly one child. A label must be a concise lowercase task goal, not a
tool, command, file, path, phase, status, result, or atomic operation. Return
only the required JSON."""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)

    inspect = commands.add_parser("inspect-toolsandbox")
    inspect.add_argument("--source", type=Path, required=True)
    inspect.add_argument("--official-source", type=Path, required=True)
    inspect.add_argument("--out", type=Path, required=True)

    for name in ("infer-toolsandbox", "infer-codetrace"):
        infer = commands.add_parser(name)
        infer.add_argument("mode", choices=("preflight", "full"))
        if name == "infer-toolsandbox":
            infer.add_argument("--visible-trajectories", type=Path, required=True)
            infer.add_argument("--baseline-cache-dir", type=Path)
        else:
            infer.add_argument("--target-operations", type=Path, required=True)
            infer.add_argument("--raw-root", type=Path, required=True)
        infer.add_argument("--llama-url", required=True)
        infer.add_argument("--workers", type=int, default=8)
        infer.add_argument("--timeout-seconds", type=int, default=600)
        infer.add_argument("--out", type=Path, required=True)

    score_ts = commands.add_parser("score-toolsandbox")
    score_ts.add_argument("--visible-trajectories", type=Path, required=True)
    score_ts.add_argument("--completion-key", type=Path, required=True)
    score_ts.add_argument("--predictions", type=Path, required=True)
    score_ts.add_argument("--inference-summary", type=Path, required=True)
    score_ts.add_argument("--out", type=Path, required=True)

    score_ct = commands.add_parser("score-codetrace")
    score_ct.add_argument("--predictions", type=Path, required=True)
    score_ct.add_argument("--inference-summary", type=Path, required=True)
    score_ct.add_argument("--step0059-score-rows", type=Path, required=True)
    score_ct.add_argument("--out", type=Path, required=True)
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


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )


def write_json_atomic(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    write_json(temporary, value)
    temporary.replace(path)


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                value = json.loads(line)
                require(isinstance(value, dict), f"non-object row in {path}")
                rows.append(value)
    return rows


def clip(value: Any, limit: int) -> str:
    text = str(value or "").strip()
    return base.clip_text(text, limit)


def sequence_cache_name(sequence_id: str, revision: str) -> str:
    return hashlib.sha256(f"{revision}:{sequence_id}".encode()).hexdigest()[:24] + ".json"


def sequence_id(condition: str, trial_id: int, sample_id: str) -> str:
    return f"{condition}/trial-{trial_id}/{sample_id}"


def first_agent_request(chunk: list[dict[str, Any]]) -> dict[str, Any]:
    for message in chunk:
        if message.get("role") != "assistant":
            continue
        calls = []
        for call in message.get("tool_calls") or []:
            function = call.get("function") or {}
            calls.append(
                {
                    "name": clip(function.get("name"), 120),
                    "arguments": clip(function.get("arguments"), 800),
                }
            )
        content = clip(message.get("content"), 1_200) if calls else ""
        if calls or content:
            return {"content": content, "tool_calls": calls}
    return {"content": "", "tool_calls": []}


def toolsandbox_turn(chunk: list[dict[str, Any]], index: int) -> dict[str, Any]:
    require(bool(chunk), "empty ToolSandbox turn")
    users = [clip(row.get("content"), 1_200) for row in chunk if row.get("role") == "user"]
    open_evidence = {
        "user_utterance": "\n---\n".join(value for value in users if value),
        "agent_request": first_agent_request(chunk),
    }
    tool_results = []
    responses = []
    state_evidence = []
    actions = []
    action_turns = []
    for message in chunk:
        role = str(message.get("role") or "")
        if role == "assistant":
            calls = message.get("tool_calls") or []
            for call in calls:
                function = call.get("function") or {}
                name = clip(function.get("name"), 120) or "unknown"
                actions.append("tool:" + name)
                action_turns.append(index)
            content = clip(message.get("content"), 1_400)
            if content:
                responses.append(content)
                if not calls:
                    actions.append("respond:user")
                    action_turns.append(index)
        elif role == "tool":
            tool_results.append(
                {
                    "name": clip(message.get("name"), 120),
                    "content": clip(message.get("content"), 1_600),
                }
            )
            details = message.get("tool_details") or {}
            if isinstance(details, dict) and details.get("database_update") is not None:
                state_evidence.append(clip(json.dumps(details["database_update"], ensure_ascii=False), 2_000))
    if not actions:
        actions.append("respond:user")
        action_turns.append(index)
    close_evidence = {
        "agent_request": open_evidence["agent_request"],
        "tool_results": tool_results,
        "visible_state": state_evidence,
        "agent_responses": responses,
    }
    return {
        "turn_index": index,
        "open_evidence": open_evidence,
        "close_evidence": close_evidence,
        "actions": actions,
        "action_turns": action_turns,
    }


def task_from_turns(turns: list[dict[str, Any]]) -> str:
    for turn in turns:
        text = str(turn["open_evidence"]["user_utterance"]).strip()
        if text:
            return text
    return "complete the requested task"


def inspect_toolsandbox(args: argparse.Namespace) -> None:
    source_root = absolute(args.source)
    official_root = absolute(args.official_source)
    out_dir = absolute(args.out)
    files = sorted(source_root.glob("*/*/trial_*_results.json"))
    require(len(files) == EXPECTED_TS_FILES, f"expected {EXPECTED_TS_FILES} trial files")
    official_text = "\n".join(path.read_text(encoding="utf-8") for path in sorted(official_root.glob("*.py")))
    visible_rows: list[dict[str, Any]] = []
    key_rows: list[dict[str, Any]] = []
    file_rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    conditions: set[str] = set()
    scenarios: set[str] = set()
    observed_turns = eligible_boundaries = padded_positive = decreases = 0
    missing_expected: list[dict[str, Any]] = []

    for path in files:
        condition = f"{path.parent.parent.name}/{path.parent.name}"
        conditions.add(condition)
        payload = json.loads(path.read_text(encoding="utf-8"))
        trial_id = int(payload["trial_id"])
        samples = payload["samples"]
        require(isinstance(samples, list), f"samples missing in {path}")
        if len(samples) != EXPECTED_TS_SCENARIOS:
            missing_expected.append(
                {
                    "condition": condition,
                    "trial_id": trial_id,
                    "reported_total": int(payload.get("total_samples", len(samples))),
                    "available": len(samples),
                }
            )
        file_rows.append(
            {
                "path": relative(path),
                "sha256": sha256_file(path),
                "condition": condition,
                "trial_id": trial_id,
                "samples": len(samples),
            }
        )
        for sample in samples:
            sample_id = str(sample["sample_id"])
            scenarios.add(sample_id)
            sid = sequence_id(condition, trial_id, sample_id)
            require(sid not in seen, f"duplicate ToolSandbox trajectory {sid}")
            seen.add(sid)
            chunks = sample["trajectory"]
            require(isinstance(chunks, list) and chunks, f"empty trajectory {sid}")
            turns = [toolsandbox_turn(chunk, index) for index, chunk in enumerate(chunks)]
            progress = [float(value) for value in sample["metrics"]["progress_rates"]]
            require(len(progress) >= len(turns), f"progress shorter than trace {sid}")
            previous = 0.0
            boundaries = []
            for index, value in enumerate(progress):
                if value < previous:
                    decreases += 1
                if value > previous:
                    if index < len(turns):
                        boundaries.append(index)
                    else:
                        padded_positive += 1
                previous = value
            visible_rows.append(
                {
                    "schema": SCHEMA + ".toolsandbox-visible.v1",
                    "sequence_id": sid,
                    "scenario_id": sample_id,
                    "task": task_from_turns(turns),
                    "turns": turns,
                }
            )
            key_rows.append(
                {
                    "schema": SCHEMA + ".toolsandbox-key.v1",
                    "sequence_id": sid,
                    "scenario_id": sample_id,
                    "observed_turns": len(turns),
                    "completion_boundaries": boundaries,
                }
            )
            observed_turns += len(turns)
            eligible_boundaries += len(boundaries)

    missing_official = [
        name
        for name in sorted(scenarios)
        if re.search(r"[\"']" + re.escape(name) + r"[\"']", official_text) is None
    ]
    require(len(conditions) == EXPECTED_TS_CONDITIONS, "ToolSandbox condition count")
    require(len(seen) == EXPECTED_TS_TRAJECTORIES, "ToolSandbox trajectory count")
    require(len(scenarios) == EXPECTED_TS_SCENARIOS, "ToolSandbox scenario count")
    require(observed_turns == EXPECTED_TS_TURNS, "ToolSandbox observed turn count")
    require(eligible_boundaries == EXPECTED_TS_BOUNDARIES, "ToolSandbox boundary count")
    require(padded_positive == EXPECTED_TS_PADDED_POSITIVE, "ToolSandbox padded positives")
    require(decreases == 0, "ToolSandbox progress is not monotone")
    require(not missing_official, "ToolSandbox scenario missing from official sources")
    require(sum(row["available"] for row in missing_expected) == 36, "unexpected source-missing population")

    visible_rows.sort(key=lambda row: row["sequence_id"])
    key_rows.sort(key=lambda row: row["sequence_id"])
    write_jsonl(out_dir / "visible-trajectories.jsonl", visible_rows)
    write_jsonl(out_dir / "completion-key.jsonl", key_rows)
    audit = {
        "schema": SCHEMA + ".toolsandbox-source-audit.v1",
        "status": "complete",
        "trial_files": len(files),
        "conditions": len(conditions),
        "trajectories": len(seen),
        "scenario_ids": len(scenarios),
        "observed_turns": observed_turns,
        "eligible_progress_boundaries": eligible_boundaries,
        "padded_positive_changes_excluded": padded_positive,
        "monotonicity_violations": decreases,
        "missing_official_scenario_names": missing_official,
        "source_missing_records": missing_expected,
        "files": file_rows,
        "visible_trajectories": relative(out_dir / "visible-trajectories.jsonl"),
        "completion_key": relative(out_dir / "completion-key.jsonl"),
        "leakage_boundary": "inference reads visible-trajectories.jsonl only; scorer reads completion-key.jsonl",
    }
    write_json(out_dir / "source-audit.json", audit)
    print(json.dumps({key: value for key, value in audit.items() if key != "files"}, sort_keys=True))


def open_grammar() -> str:
    label = (
        'label ::= "\\\"" [a-z] [a-z0-9 /+._,:;()-]'
        f'{{0,{LABEL_MAX_CHARS - 1}}} "\\\""\n'
    )
    done = (
        'done ::= "\\\"" [a-z] [a-z0-9 /+._,:;()-]'
        f'{{0,{DONE_MAX_CHARS - 1}}} "\\\""\n'
    )
    return (
        'root ::= continue | start\n'
        'continue ::= "{\\\"transition\\\":\\\"continue\\\"}"\n'
        'start ::= "{\\\"transition\\\":\\\"start\\\",\\\"label\\\":" '
        'label ",\\\"done_when\\\":" done "}"\n'
        + label
        + done
    )


def close_grammar() -> str:
    return (
        'root ::= keep | complete\n'
        'keep ::= "{\\\"transition\\\":\\\"keep\\\"}"\n'
        'complete ::= "{\\\"transition\\\":\\\"complete\\\"}"\n'
    )


def baseline_grammar(depth: int) -> str:
    label = (
        'label ::= "\\\"" [a-z] [a-z0-9 /+._,:;()-]'
        f'{{0,{LABEL_MAX_CHARS - 1}}} "\\\""\n'
    )
    stay = 'stay ::= "{\\\"transition\\\":\\\"stay\\\"}"\n'
    push = (
        'push ::= "{\\\"transition\\\":\\\"push\\\",\\\"label\\\":" '
        'label "}"\n'
    )
    if depth == 0:
        return "root ::= stay | push\n" + stay + push + label
    pop = 'pop ::= "{\\\"transition\\\":\\\"pop\\\"}"\n'
    return "root ::= stay | push | pop\n" + stay + push + pop + label


def parse_open(raw: str) -> dict[str, str]:
    value = json.loads(raw)
    require(isinstance(value, dict), "OPEN response is not an object")
    transition = value.get("transition")
    if transition == "continue":
        require(set(value) == {"transition"}, "continue keys")
        return {"transition": "continue"}
    require(transition == "start", f"unknown OPEN transition {transition!r}")
    require(set(value) == {"transition", "label", "done_when"}, "start keys")
    label = str(value["label"])
    done_when = str(value["done_when"])
    require(0 < len(label) <= LABEL_MAX_CHARS and LABEL_RE.fullmatch(label) is not None, "label syntax")
    require(0 < len(done_when) <= DONE_MAX_CHARS and LABEL_RE.fullmatch(done_when) is not None, "done_when syntax")
    return {"transition": "start", "label": label, "done_when": done_when}


def parse_close(raw: str) -> dict[str, str]:
    value = json.loads(raw)
    require(isinstance(value, dict) and set(value) == {"transition"}, "CLOSE keys")
    transition = value.get("transition")
    require(transition in {"keep", "complete"}, "CLOSE transition")
    return {"transition": str(transition)}


def parse_baseline(raw: str, depth: int) -> dict[str, str]:
    value = json.loads(raw)
    require(isinstance(value, dict), "baseline response is not an object")
    transition = value.get("transition")
    if transition in {"stay", "pop"}:
        require(set(value) == {"transition"}, f"{transition} keys")
        require(transition != "pop" or depth > 0, "baseline pop at root")
        return {"transition": str(transition)}
    require(transition == "push", f"unknown baseline transition {transition!r}")
    require(set(value) == {"transition", "label"}, "baseline push keys")
    label = str(value["label"])
    require(0 < len(label) <= LABEL_MAX_CHARS and LABEL_RE.fullmatch(label) is not None, "baseline label syntax")
    return {"transition": "push", "label": label}


def task_stack(root: str, stack: list[dict[str, str]]) -> list[dict[str, str | int]]:
    return [
        {"depth": 0, "label": root, "done_when": ROOT_DONE_WHEN},
        *[
            {
                "depth": index + 1,
                "label": frame["label"],
                "done_when": frame["done_when"],
            }
            for index, frame in enumerate(stack)
        ],
    ]


def open_prompt(task: str, root: str, stack: list[dict[str, str]], evidence: dict[str, Any]) -> str:
    return (
        "CONCRETE TASK\n"
        + clip(task, 2_400)
        + "\n\nACTIVE TASK STACK\n"
        + json.dumps(task_stack(root, stack), ensure_ascii=False, separators=(",", ":"))
        + "\n\nCURRENT PREFIX-VISIBLE INTENT EVIDENCE\n"
        + json.dumps(evidence, ensure_ascii=False, separators=(",", ":"))
    )


def close_prompt(
    task: str,
    root: str,
    stack: list[dict[str, str]],
    evidence: dict[str, Any],
) -> str:
    raw_leaf = stack[-1] if stack else {"label": root, "done_when": ROOT_DONE_WHEN}
    leaf = {"label": raw_leaf["label"], "done_when": raw_leaf["done_when"]}
    return (
        "CONCRETE TASK\n"
        + clip(task, 2_400)
        + "\n\nACTIVE TASK STACK\n"
        + json.dumps(task_stack(root, stack), ensure_ascii=False, separators=(",", ":"))
        + "\n\nACTIVE LEAF COMPLETION CONTRACT\n"
        + json.dumps(leaf, ensure_ascii=False, separators=(",", ":"))
        + "\n\nCURRENT VISIBLE OUTCOME\n"
        + json.dumps(evidence, ensure_ascii=False, separators=(",", ":"))
    )


def baseline_prompt(
    task: str,
    root: str,
    stack: list[dict[str, str]],
    preceding_result: dict[str, Any] | str,
    current_evidence: dict[str, Any],
) -> str:
    visible_stack = [
        {"depth": 0, "label": root},
        *[
            {"depth": index + 1, "label": frame["label"]}
            for index, frame in enumerate(stack)
        ],
    ]
    return (
        "CONCRETE TASK\n"
        + clip(task, 2_400)
        + "\n\nACTIVE TASK STACK\n"
        + json.dumps(visible_stack, ensure_ascii=False, separators=(",", ":"))
        + "\n\nPRECEDING VISIBLE RESULT\n"
        + json.dumps(preceding_result, ensure_ascii=False, separators=(",", ":"))
        + "\n\nNEXT PREFIX-VISIBLE TURN EVIDENCE\n"
        + json.dumps(current_evidence, ensure_ascii=False, separators=(",", ":"))
    )


def model_request_hash(system: str, user: str, grammar: str) -> str:
    return hashlib.sha256(
        json.dumps(
            {
                "algorithm": ALGORITHM_VERSION,
                "model": MODEL,
                "model_sha256": MODEL_SHA256,
                "seed": SEED,
                "temperature": 0,
                "system": system,
                "grammar": grammar,
                "user": user,
            },
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode()
    ).hexdigest()


def call_model(
    llama_url: str,
    system: str,
    user: str,
    grammar: str,
    timeout_seconds: int,
    output_tokens: int = OUTPUT_TOKENS,
) -> dict[str, Any]:
    raw, response, attempts = base.call_model(
        llama_url, system, user, grammar, timeout_seconds, output_tokens
    )
    return {
        "request_sha256": model_request_hash(system, user, grammar),
        "prompt": user,
        "raw_response": raw,
        "usage": response.get("usage") or {},
        "attempts": attempts,
        "output_token_limit": output_tokens,
    }


def call_and_parse(
    llama_url: str,
    system: str,
    user: str,
    grammar: str,
    timeout_seconds: int,
    parser: Any,
) -> tuple[dict[str, Any], dict[str, str]]:
    first = call_model(llama_url, system, user, grammar, timeout_seconds)
    try:
        return first, parser(str(first["raw_response"]))
    except (json.JSONDecodeError, RuntimeError) as error:
        repaired = call_model(
            llama_url,
            system,
            user,
            grammar,
            timeout_seconds,
            OUTPUT_TOKENS * 2,
        )
        parsed = parser(str(repaired["raw_response"]))
        repaired["malformed_io_repair"] = {
            "first_response_sha256": hashlib.sha256(
                str(first["raw_response"]).encode()
            ).hexdigest(),
            "first_error": f"{type(error).__name__}: {error}",
            "first_output_token_limit": OUTPUT_TOKENS,
        }
        return repaired, parsed


def root_label(task: str) -> str:
    return clip(next((line.strip() for line in task.splitlines() if line.strip()), "complete the requested task"), 120)


def sequence_input_sha256(task: str, turns: list[dict[str, Any]]) -> str:
    return hashlib.sha256(
        json.dumps(
            {"task": task, "turns": turns},
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode()
    ).hexdigest()


def validate_candidate_cache(
    result: dict[str, Any], task: str, turns: list[dict[str, Any]]
) -> None:
    sequence = str(result["sequence_id"])
    root = str(result["root_label"])
    stack: list[dict[str, str]] = []
    next_frame = 0
    root_latched = False
    records = result["turns"]
    require(len(records) <= len(turns), "candidate cache longer than input")
    for index, (record, turn) in enumerate(zip(records, turns, strict=False)):
        require(int(record["turn_index"]) == index, "candidate cached turn order")
        require(record["stack_before_open"] == stack, "candidate cached stack linkage")
        open_user = open_prompt(task, root, stack, turn["open_evidence"])
        require(
            record["open_call"]["request_sha256"]
            == model_request_hash(OPEN_SYSTEM, open_user, open_grammar()),
            "candidate cached OPEN request drift",
        )
        proposal = parse_open(str(record["open_call"]["raw_response"]))
        require(record["open_proposal"] == proposal, "candidate cached OPEN parse")
        active_labels = {root, *(frame["label"] for frame in stack)}
        duplicate = proposal["transition"] == "start" and proposal["label"] in active_labels
        applied = {"transition": "continue"} if duplicate else dict(proposal)
        require(record["open_transition"] == applied, "candidate cached OPEN application")
        require(bool(record["duplicate_leaf_continue"]) == duplicate, "candidate cached duplicate invariant")
        if applied["transition"] == "start":
            stack.append(
                {
                    "instance": f"{sequence}:frame-{next_frame:05d}",
                    "label": applied["label"],
                    "done_when": applied["done_when"],
                }
            )
            next_frame += 1
            root_latched = False
        require(record["stack_for_turn"] == stack, "candidate cached assigned stack")
        skipped = root_latched and not stack
        require(bool(record["close_skipped_by_root_latch"]) == skipped, "candidate cached latch skip")
        if skipped:
            close = {"transition": "keep"}
            require(record["close_call"]["request_sha256"] is None, "candidate skipped CLOSE hash")
        else:
            close_user = close_prompt(task, root, stack, turn["close_evidence"])
            require(
                record["close_call"]["request_sha256"]
                == model_request_hash(CLOSE_SYSTEM, close_user, close_grammar()),
                "candidate cached CLOSE request drift",
            )
            close = parse_close(str(record["close_call"]["raw_response"]))
        require(record["close_transition"] == close, "candidate cached CLOSE parse")
        completion = close["transition"] == "complete"
        completed = None
        if completion:
            if stack:
                completed = dict(stack[-1])
                stack.pop()
            else:
                completed = {
                    "instance": f"{sequence}:task-root",
                    "label": root,
                    "done_when": ROOT_DONE_WHEN,
                }
                root_latched = True
        require(bool(record["completion_event"]) == completion, "candidate cached completion")
        require(record["completed_frame"] == completed, "candidate cached completed frame")
        require(record["stack_after_close"] == stack, "candidate cached CLOSE stack")
        require(bool(record["root_latched_after"]) == root_latched, "candidate cached root latch")
        require(int(record["next_frame"]) == next_frame, "candidate cached frame counter")


def validate_baseline_cache(
    result: dict[str, Any], task: str, turns: list[dict[str, Any]]
) -> None:
    sequence = str(result["sequence_id"])
    root = str(result["root_label"])
    stack: list[dict[str, str]] = []
    next_frame = 0
    preceding: dict[str, Any] | str = ""
    records = result["turns"]
    require(len(records) <= len(turns), "baseline cache longer than input")
    for index, (record, turn) in enumerate(zip(records, turns, strict=False)):
        require(int(record["turn_index"]) == index, "baseline cached turn order")
        require(record["stack_before"] == stack, "baseline cached stack linkage")
        user = baseline_prompt(task, root, stack, preceding, turn["open_evidence"])
        grammar = baseline_grammar(len(stack))
        require(
            record["call"]["request_sha256"]
            == model_request_hash(BASELINE_SYSTEM, user, grammar),
            "baseline cached request drift",
        )
        proposal = parse_baseline(str(record["call"]["raw_response"]), len(stack))
        require(record["proposal"] == proposal, "baseline cached parse")
        duplicate = proposal["transition"] == "push" and proposal["label"] == (stack[-1]["label"] if stack else root)
        applied = {"transition": "stay"} if duplicate else dict(proposal)
        require(record["transition"] == applied, "baseline cached application")
        require(bool(record["duplicate_leaf_stay"]) == duplicate, "baseline cached duplicate invariant")
        if applied["transition"] == "push":
            stack.append(
                {
                    "instance": f"{sequence}:baseline-frame-{next_frame:05d}",
                    "label": applied["label"],
                    "done_when": "not exposed by the step0059 baseline",
                }
            )
            next_frame += 1
        elif applied["transition"] == "pop":
            stack.pop()
        require(record["stack_after"] == stack, "baseline cached stack after")
        require(int(record["next_frame"]) == next_frame, "baseline cached frame counter")
        preceding = turn["close_evidence"]


def result_grounded_sequence(
    sequence: str,
    task: str,
    turns: list[dict[str, Any]],
    llama_url: str,
    timeout_seconds: int,
    cache_path: Path,
) -> dict[str, Any]:
    root = root_label(task)
    input_sha256 = sequence_input_sha256(task, turns)
    if cache_path.is_file():
        result = json.loads(cache_path.read_text(encoding="utf-8"))
        require(result.get("algorithm_version") == ALGORITHM_VERSION, "candidate cache version")
        require(result.get("cache_revision") == CANDIDATE_CACHE_REVISION, "candidate cache revision")
        require(result.get("sequence_id") == sequence, "candidate cache sequence")
        require(result.get("model_sha256") == MODEL_SHA256, "candidate cache model")
        require(result.get("root_label") == root, "candidate cache root")
        require(result.get("input_sha256") == input_sha256, "candidate cache input drift")
        validate_candidate_cache(result, task, turns)
    else:
        result = {
            "schema": SCHEMA + ".candidate-sequence.v1",
            "algorithm_version": ALGORITHM_VERSION,
            "cache_revision": CANDIDATE_CACHE_REVISION,
            "sequence_id": sequence,
            "model": MODEL,
            "model_sha256": MODEL_SHA256,
            "seed": SEED,
            "root_label": root,
            "input_sha256": input_sha256,
            "input_turns": len(turns),
            "turns": [],
        }
        write_json_atomic(cache_path, result)

    records = result["turns"]
    require(len(records) <= len(turns), "candidate cache longer than input")
    stack = [dict(frame) for frame in (records[-1]["stack_after_close"] if records else [])]
    next_frame = int(records[-1]["next_frame"] if records else 0)
    root_latched = bool(records[-1]["root_latched_after"] if records else False)
    for index in range(len(records), len(turns)):
        turn = turns[index]
        before_open = [dict(frame) for frame in stack]
        open_user = open_prompt(task, root, stack, turn["open_evidence"])
        open_call, proposal = call_and_parse(
            llama_url,
            OPEN_SYSTEM,
            open_user,
            open_grammar(),
            timeout_seconds,
            parse_open,
        )
        active_labels = {root, *(frame["label"] for frame in stack)}
        duplicate = proposal["transition"] == "start" and proposal["label"] in active_labels
        applied_open = {"transition": "continue"} if duplicate else dict(proposal)
        if applied_open["transition"] == "start":
            stack.append(
                {
                    "instance": f"{sequence}:frame-{next_frame:05d}",
                    "label": applied_open["label"],
                    "done_when": applied_open["done_when"],
                }
            )
            next_frame += 1
            root_latched = False
        stack_for_turn = [dict(frame) for frame in stack]

        close_skipped = root_latched and not stack
        if close_skipped:
            close_call: dict[str, Any] = {
                "request_sha256": None,
                "prompt": None,
                "raw_response": None,
                "usage": {},
                "attempts": 0,
            }
            close_proposal = {"transition": "keep"}
        else:
            close_user = close_prompt(task, root, stack, turn["close_evidence"])
            close_call, close_proposal = call_and_parse(
                llama_url,
                CLOSE_SYSTEM,
                close_user,
                close_grammar(),
                timeout_seconds,
                parse_close,
            )
        completion = close_proposal["transition"] == "complete"
        completed_frame = None
        if completion:
            if stack:
                completed_frame = dict(stack[-1])
                stack.pop()
            else:
                completed_frame = {
                    "instance": f"{sequence}:task-root",
                    "label": root,
                    "done_when": ROOT_DONE_WHEN,
                }
                root_latched = True
        record = {
            "turn_index": index,
            "open_call": open_call,
            "open_proposal": proposal,
            "open_transition": applied_open,
            "duplicate_leaf_continue": duplicate,
            "stack_before_open": before_open,
            "stack_for_turn": stack_for_turn,
            "close_call": close_call,
            "close_transition": close_proposal,
            "close_skipped_by_root_latch": close_skipped,
            "completion_event": completion,
            "completed_frame": completed_frame,
            "stack_after_close": [dict(frame) for frame in stack],
            "root_latched_after": root_latched,
            "next_frame": next_frame,
        }
        records.append(record)
        write_json_atomic(cache_path, result)
    require(len(records) == len(turns), "candidate turn coverage")
    return result


def baseline_sequence(
    sequence: str,
    task: str,
    turns: list[dict[str, Any]],
    llama_url: str,
    timeout_seconds: int,
    cache_path: Path,
) -> dict[str, Any]:
    root = root_label(task)
    input_sha256 = sequence_input_sha256(task, turns)
    if cache_path.is_file():
        result = json.loads(cache_path.read_text(encoding="utf-8"))
        require(result.get("algorithm_version") == ALGORITHM_VERSION, "baseline cache version")
        require(result.get("cache_revision") == BASELINE_CACHE_REVISION, "baseline cache revision")
        require(result.get("sequence_id") == sequence, "baseline cache sequence")
        require(result.get("model_sha256") == MODEL_SHA256, "baseline cache model")
        require(result.get("root_label") == root, "baseline cache root")
        require(result.get("input_sha256") == input_sha256, "baseline cache input drift")
        validate_baseline_cache(result, task, turns)
    else:
        result = {
            "schema": SCHEMA + ".baseline-sequence.v1",
            "algorithm_version": ALGORITHM_VERSION,
            "cache_revision": BASELINE_CACHE_REVISION,
            "sequence_id": sequence,
            "model": MODEL,
            "model_sha256": MODEL_SHA256,
            "seed": SEED,
            "root_label": root,
            "input_sha256": input_sha256,
            "input_turns": len(turns),
            "turns": [],
        }
        write_json_atomic(cache_path, result)
    records = result["turns"]
    stack = [dict(frame) for frame in (records[-1]["stack_after"] if records else [])]
    next_frame = int(records[-1]["next_frame"] if records else 0)
    preceding: dict[str, Any] | str = turns[len(records) - 1]["close_evidence"] if records else ""
    for index in range(len(records), len(turns)):
        turn = turns[index]
        user = baseline_prompt(task, root, stack, preceding, turn["open_evidence"])
        grammar = baseline_grammar(len(stack))
        call, proposal = call_and_parse(
            llama_url,
            BASELINE_SYSTEM,
            user,
            grammar,
            timeout_seconds,
            lambda raw: parse_baseline(raw, len(stack)),
        )
        duplicate = proposal["transition"] == "push" and proposal["label"] == (stack[-1]["label"] if stack else root)
        applied = {"transition": "stay"} if duplicate else dict(proposal)
        before = [dict(frame) for frame in stack]
        if applied["transition"] == "push":
            stack.append(
                {
                    "instance": f"{sequence}:baseline-frame-{next_frame:05d}",
                    "label": applied["label"],
                    "done_when": "not exposed by the step0059 baseline",
                }
            )
            next_frame += 1
        elif applied["transition"] == "pop":
            stack.pop()
        record = {
            "turn_index": index,
            "call": call,
            "proposal": proposal,
            "transition": applied,
            "duplicate_leaf_stay": duplicate,
            "stack_before": before,
            "stack_after": [dict(frame) for frame in stack],
            "next_frame": next_frame,
        }
        records.append(record)
        write_json_atomic(cache_path, result)
        preceding = turn["close_evidence"]
    require(len(records) == len(turns), "baseline turn coverage")
    return result


def summarize_usage(caches: Iterable[dict[str, Any]], keys: tuple[str, ...]) -> dict[str, int]:
    total: Counter[str] = Counter()
    for cache in caches:
        for record in cache["turns"]:
            for key in keys:
                call = record.get(key) or {}
                for name, value in (call.get("usage") or {}).items():
                    if isinstance(value, int):
                        total[name] += value
    return dict(total)


def infer_toolsandbox_sequence(
    row: dict[str, Any],
    llama_url: str,
    timeout_seconds: int,
    candidate_cache_dir: Path,
    baseline_cache_dir: Path,
) -> dict[str, Any]:
    sequence = str(row["sequence_id"])
    candidate = result_grounded_sequence(
        sequence,
        str(row["task"]),
        row["turns"],
        llama_url,
        timeout_seconds,
        candidate_cache_dir / sequence_cache_name(sequence, CANDIDATE_CACHE_REVISION),
    )
    baseline = baseline_sequence(
        sequence,
        str(row["task"]),
        row["turns"],
        llama_url,
        timeout_seconds,
        baseline_cache_dir / sequence_cache_name(sequence, BASELINE_CACHE_REVISION),
    )
    prediction = {
        "schema": SCHEMA + ".toolsandbox-prediction.v1",
        "sequence_id": sequence,
        "scenario_id": row["scenario_id"],
        "turns": len(row["turns"]),
        "candidate_completion_boundaries": [
            int(record["turn_index"])
            for record in candidate["turns"]
            if record["completion_event"]
        ],
        "step0059_completion_boundaries": [
            int(record["turn_index"]) - 1
            for record in baseline["turns"]
            if record["transition"]["transition"] == "pop" and int(record["turn_index"]) > 0
        ],
    }
    return {"prediction": prediction, "candidate": candidate, "baseline": baseline}


def run_infer_toolsandbox(args: argparse.Namespace) -> None:
    started = time.monotonic()
    visible_path = absolute(args.visible_trajectories)
    out_dir = absolute(args.out)
    rows = read_jsonl(visible_path)
    require(len(rows) == EXPECTED_TS_TRAJECTORIES, "ToolSandbox visible trajectory count")
    selected = [max(rows, key=lambda row: (len(row["turns"]), row["sequence_id"]))] if args.mode == "preflight" else rows
    cache_dir = out_dir / "sequences"
    baseline_cache_dir = (
        absolute(args.baseline_cache_dir)
        if args.baseline_cache_dir is not None
        else cache_dir / "step0059"
    )
    results: dict[str, dict[str, Any]] = {}
    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = {
            executor.submit(
                infer_toolsandbox_sequence,
                row,
                args.llama_url,
                args.timeout_seconds,
                cache_dir / "candidate",
                baseline_cache_dir,
            ): str(row["sequence_id"])
            for row in selected
        }
        for future in as_completed(futures):
            sequence = futures[future]
            results[sequence] = future.result()
            if len(results) % 50 == 0 or len(results) == len(selected):
                print(f"ToolSandbox {len(results)}/{len(selected)} {sequence}", flush=True)
    predictions = [results[key]["prediction"] for key in sorted(results)]
    require(sum(int(row["turns"]) for row in predictions) == sum(len(row["turns"]) for row in selected), "ToolSandbox turn coverage")
    write_jsonl(out_dir / "predictions.jsonl", predictions)
    candidates = [results[key]["candidate"] for key in sorted(results)]
    baselines = [results[key]["baseline"] for key in sorted(results)]
    candidate_turns = [record for cache in candidates for record in cache["turns"]]
    baseline_turns = [record for cache in baselines for record in cache["turns"]]
    open_labels = [
        record["open_proposal"].get("label", "")
        for record in candidate_turns
        if record["open_proposal"]["transition"] == "start"
    ]
    model_close_records = [
        record for record in candidate_turns if not record["close_skipped_by_root_latch"]
    ]
    visible_by_sequence = {str(row["sequence_id"]): row for row in selected}
    tool_name_label_copies = 0
    literal_done_when_contracts = 0
    for cache in candidates:
        tool_names = {
            str(call["name"])
            for turn in visible_by_sequence[str(cache["sequence_id"])]["turns"]
            for call in turn["open_evidence"]["agent_request"]["tool_calls"]
        }
        for record in cache["turns"]:
            proposal = record["open_proposal"]
            if proposal["transition"] == "start":
                tool_name_label_copies += proposal["label"] in tool_names
                literal_done_when_contracts += proposal["done_when"] == "done_when"
    summary = {
        "schema": SCHEMA + ".toolsandbox-inference.v1",
        "algorithm_version": ALGORITHM_VERSION,
        "candidate_cache_revision": CANDIDATE_CACHE_REVISION,
        "baseline_cache_revision": BASELINE_CACHE_REVISION,
        "status": "complete",
        "mode": args.mode,
        "model": MODEL,
        "model_sha256": MODEL_SHA256,
        "seed": SEED,
        "trajectories": len(selected),
        "scenario_ids": len({row["scenario_id"] for row in selected}),
        "turns": len(candidate_turns),
        "candidate_open_counts": dict(Counter(record["open_transition"]["transition"] for record in candidate_turns)),
        "candidate_close_counts": dict(Counter(record["close_transition"]["transition"] for record in candidate_turns)),
        "candidate_model_close_counts": dict(Counter(record["close_transition"]["transition"] for record in model_close_records)),
        "candidate_completion_events": sum(record["completion_event"] for record in candidate_turns),
        "candidate_duplicate_leaf_continues": sum(record["duplicate_leaf_continue"] for record in candidate_turns),
        "candidate_root_latch_skips": sum(record["close_skipped_by_root_latch"] for record in candidate_turns),
        "candidate_max_depth": max(1 + len(record["stack_for_turn"]) for record in candidate_turns),
        "commandish_open_labels": sum(bool(COMMANDISH_RE.search(label)) for label in open_labels),
        "phase_like_open_labels": sum(bool(PHASE_RE.fullmatch(label)) for label in open_labels),
        "tool_name_label_copies": tool_name_label_copies,
        "literal_done_when_contracts": literal_done_when_contracts,
        "step0059_counts": dict(Counter(record["transition"]["transition"] for record in baseline_turns)),
        "candidate_model_usage": summarize_usage(candidates, ("open_call", "close_call")),
        "candidate_malformed_io_repairs": sum(
            bool((record.get(key) or {}).get("malformed_io_repair"))
            for record in candidate_turns
            for key in ("open_call", "close_call")
        ),
        "step0059_model_usage": summarize_usage(baselines, ("call",)),
        "step0059_malformed_io_repairs": sum(
            bool((record.get("call") or {}).get("malformed_io_repair"))
            for record in baseline_turns
        ),
        "wall_seconds": time.monotonic() - started,
        "predictions": relative(out_dir / "predictions.jsonl"),
        "isolation": {
            "completion_key_opened": False,
            "published_subgoals_opened": False,
            "progress_rates_opened": False,
            "model_or_persona_exposed": False,
            "later_turns_exposed": False,
        },
    }
    if args.mode == "full":
        require(summary["trajectories"] == EXPECTED_TS_TRAJECTORIES, "full ToolSandbox trajectories")
        require(summary["turns"] == EXPECTED_TS_TURNS, "full ToolSandbox turns")
    write_json(out_dir / "inference-summary.json", summary)
    print(json.dumps(summary, sort_keys=True), flush=True)


def codetrace_turns(material: dict[str, Any]) -> list[dict[str, Any]]:
    output = []
    for turn in stateful.group_turns(material["operations"]):
        operations = turn["operations"]
        output.append(
            {
                "turn_index": int(turn["turn_index"]),
                "source_turn_id": turn["source_turn_id"],
                "operations": operations,
                "open_evidence": {
                    "native_intent": clip(stateful.unique_text(operations, "intent"), 1_600),
                    "native_progress": clip(stateful.unique_text(operations, "progress"), 1_600),
                },
                "close_evidence": {
                    "native_intent": clip(stateful.unique_text(operations, "intent"), 1_000),
                    "native_progress": clip(stateful.unique_text(operations, "progress"), 1_000),
                    "visible_result": clip(stateful.unique_text(operations, "result"), 2_400),
                },
            }
        )
    return output


def infer_codetrace_session(
    session: str,
    rows: list[dict[str, Any]],
    raw_root: Path,
    llama_url: str,
    timeout_seconds: int,
    cache_dir: Path,
) -> dict[str, Any]:
    material = source.reconstruct_source(raw_root, session, rows)
    turns = codetrace_turns(material)
    cache = result_grounded_sequence(
        session,
        str(material["task"]),
        turns,
        llama_url,
        timeout_seconds,
        cache_dir / sequence_cache_name(session, CANDIDATE_CACHE_REVISION),
    )
    predictions = []
    for turn, record in zip(turns, cache["turns"], strict=True):
        path = [
            {"instance": f"{session}:task-root", "label": cache["root_label"]},
            *[
                {"instance": frame["instance"], "label": frame["label"]}
                for frame in record["stack_for_turn"]
            ],
        ]
        for operation in turn["operations"]:
            predictions.append(
                {
                    "schema": SCHEMA + ".codetrace-prediction.v1",
                    "session": session,
                    "framework": material["framework"],
                    "adapter": material["adapter"],
                    "step_id": int(operation["step"]),
                    "source_ref": operation["source_ref"],
                    "turn_index": int(turn["turn_index"]),
                    "task_depth": len(path),
                    "task_path": path,
                    "active_leaf_instance": path[-1]["instance"],
                    "active_leaf_label": path[-1]["label"],
                    "open_transition": record["open_transition"]["transition"],
                    "close_transition": record["close_transition"]["transition"],
                    "completion_event": bool(record["completion_event"]),
                }
            )
    return {"cache": cache, "predictions": predictions, "adapter": material["adapter"], "framework": material["framework"]}


def run_infer_codetrace(args: argparse.Namespace) -> None:
    started = time.monotonic()
    target_path = absolute(args.target_operations)
    raw_root = absolute(args.raw_root)
    out_dir = absolute(args.out)
    grouped = base.load_visible_operations(target_path)
    require(len(grouped) == EXPECTED_CODETRACE_SESSIONS, "CodeTrace session count")
    require(sum(map(len, grouped.values())) == EXPECTED_CODETRACE_OPERATIONS, "CodeTrace operation count")
    selected = stateful.preflight_sessions(grouped) if args.mode == "preflight" else sorted(grouped)
    results: dict[str, dict[str, Any]] = {}
    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = {
            executor.submit(
                infer_codetrace_session,
                session,
                grouped[session],
                raw_root,
                args.llama_url,
                args.timeout_seconds,
                out_dir / "sessions",
            ): session
            for session in selected
        }
        for future in as_completed(futures):
            session = futures[future]
            results[session] = future.result()
            if len(results) % 20 == 0 or len(results) == len(selected):
                print(f"CodeTrace {len(results)}/{len(selected)} {session}", flush=True)
    predictions = [row for session in sorted(results) for row in results[session]["predictions"]]
    caches = [results[session]["cache"] for session in sorted(results)]
    records = [record for cache in caches for record in cache["turns"]]
    expected = sum(len(grouped[session]) for session in selected)
    require(len(predictions) == expected, "CodeTrace prediction coverage")
    write_jsonl(out_dir / "predictions.jsonl", predictions)
    labels = [
        record["open_proposal"].get("label", "")
        for record in records
        if record["open_proposal"]["transition"] == "start"
    ]
    model_close_records = [record for record in records if not record["close_skipped_by_root_latch"]]
    depths = [int(row["task_depth"]) for row in predictions]
    summary = {
        "schema": SCHEMA + ".codetrace-inference.v1",
        "algorithm_version": ALGORITHM_VERSION,
        "candidate_cache_revision": CANDIDATE_CACHE_REVISION,
        "status": "complete",
        "mode": args.mode,
        "model": MODEL,
        "model_sha256": MODEL_SHA256,
        "seed": SEED,
        "sessions": len(selected),
        "turns": len(records),
        "operations": len(predictions),
        "frameworks": dict(Counter(results[session]["framework"] for session in results)),
        "adapter_layouts": dict(Counter(results[session]["adapter"] for session in results)),
        "open_counts": dict(Counter(record["open_transition"]["transition"] for record in records)),
        "close_counts": dict(Counter(record["close_transition"]["transition"] for record in records)),
        "model_close_counts": dict(Counter(record["close_transition"]["transition"] for record in model_close_records)),
        "completion_events": sum(record["completion_event"] for record in records),
        "duplicate_leaf_continues": sum(record["duplicate_leaf_continue"] for record in records),
        "root_latch_skips": sum(record["close_skipped_by_root_latch"] for record in records),
        "depth_including_root": {
            "minimum": min(depths),
            "maximum": max(depths),
            "mean": statistics.fmean(depths),
            "counts": dict(sorted(Counter(depths).items())),
        },
        "commandish_open_labels": sum(bool(COMMANDISH_RE.search(label)) for label in labels),
        "phase_like_open_labels": sum(bool(PHASE_RE.fullmatch(label)) for label in labels),
        "literal_done_when_contracts": sum(
            record["open_proposal"].get("done_when") == "done_when"
            for record in records
            if record["open_proposal"]["transition"] == "start"
        ),
        "model_usage": summarize_usage(caches, ("open_call", "close_call")),
        "malformed_io_repairs": sum(
            bool((record.get(key) or {}).get("malformed_io_repair"))
            for record in records
            for key in ("open_call", "close_call")
        ),
        "wall_seconds": time.monotonic() - started,
        "predictions": relative(out_dir / "predictions.jsonl"),
        "isolation": {
            "human_stage_opened": False,
            "planned_action_opened": False,
            "tool_file_path_status_exposed_as_fields": False,
            "current_visible_result_exposed_only_to_close": True,
            "depth_cap": None,
            "all_operations_retained": True,
        },
    }
    if args.mode == "full":
        require(summary["sessions"] == EXPECTED_CODETRACE_SESSIONS, "full CodeTrace sessions")
        require(summary["turns"] == EXPECTED_CODETRACE_TURNS, "full CodeTrace turns")
        require(summary["operations"] == EXPECTED_CODETRACE_OPERATIONS, "full CodeTrace operations")
    write_json(out_dir / "inference-summary.json", summary)
    print(json.dumps(summary, sort_keys=True), flush=True)


def boundary_metric(gold: set[int], predicted: set[int]) -> tuple[int, int, int]:
    return len(gold & predicted), len(predicted - gold), len(gold - predicted)


def metric_from_counts(tp: int, fp: int, fn: int) -> dict[str, Any]:
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {"tp": tp, "fp": fp, "fn": fn, "precision": precision, "recall": recall, "f1": f1}


def toolsandbox_recurrence_boundaries(rows: list[dict[str, Any]]) -> tuple[dict[str, set[int]], list[dict[str, Any]]]:
    sequence_ids = sorted(str(row["sequence_id"]) for row in rows)
    by_id = {str(row["sequence_id"]): row for row in rows}
    actions = {
        sequence: [action for turn in by_id[sequence]["turns"] for action in turn["actions"]]
        for sequence in sequence_ids
    }
    action_turns = {
        sequence: [int(index) for turn in by_id[sequence]["turns"] for index in turn["action_turns"]]
        for sequence in sequence_ids
    }
    fold_predictions: dict[tuple[str, int], dict[str, Any]] = {}
    reports = []
    for fold in range(recurrence.FOLD_COUNT):
        predictions, report = recurrence.predict_fold(fold, sequence_ids, actions)
        overlap = set(fold_predictions) & set(predictions)
        require(not overlap, f"duplicate recurrence predictions: {next(iter(overlap)) if overlap else ''}")
        fold_predictions.update(predictions)
        reports.append(report)
    boundaries: dict[str, set[int]] = {}
    for sequence in sequence_ids:
        predicted: set[int] = set()
        for position in range(1, len(actions[sequence])):
            record = fold_predictions[(sequence, position)]
            if record["boundary"]:
                predicted.add(action_turns[sequence][position - 1])
        boundaries[sequence] = predicted
    return boundaries, reports


def paired_scenario_bootstrap(
    rows: list[dict[str, Any]],
    method_counts: dict[str, dict[str, tuple[int, int, int]]],
    candidate: str,
    baseline: str,
    output: Path,
) -> dict[str, Any]:
    scenarios = sorted({str(row["scenario_id"]) for row in rows})
    sequence_scenario = {str(row["sequence_id"]): str(row["scenario_id"]) for row in rows}
    sufficient: dict[tuple[str, str], tuple[int, int, int]] = {}
    for scenario in scenarios:
        ids = [sequence for sequence, value in sequence_scenario.items() if value == scenario]
        for method in (candidate, baseline):
            counts = [method_counts[method][sequence] for sequence in ids]
            sufficient[(scenario, method)] = tuple(sum(value[index] for value in counts) for index in range(3))

    def f1(draw: list[str], method: str) -> float:
        counts = tuple(sum(sufficient[(scenario, method)][index] for scenario in draw) for index in range(3))
        return float(metric_from_counts(*counts)["f1"])

    generator = random.Random(SEED)
    deltas = []
    for _ in range(BOOTSTRAP_RESAMPLES):
        draw = generator.choices(scenarios, k=len(scenarios))
        deltas.append(f1(draw, candidate) - f1(draw, baseline))
    write_jsonl(output, ({"resample": index, "delta": delta} for index, delta in enumerate(deltas)))
    return {
        "candidate": candidate,
        "baseline": baseline,
        "unit": "scenario_id",
        "clusters": len(scenarios),
        "resamples": BOOTSTRAP_RESAMPLES,
        "mean_delta": statistics.fmean(deltas),
        "median_delta": base.percentile(deltas, 0.5),
        "ci95": [base.percentile(deltas, 0.025), base.percentile(deltas, 0.975)],
        "positive_fraction": sum(value > 0 for value in deltas) / len(deltas),
    }


def toolsandbox_report(summary: dict[str, Any]) -> str:
    lines = [
        "# Result-Grounded Task Stack — ToolSandbox Completion Result",
        "",
        f"- status: {summary['status']}",
        f"- registered interpretation: **{summary['registered_interpretation']}**",
        "",
        "## Exact turn-boundary metrics",
        "",
        "| Method | Precision | Recall | F1 | TP | FP | FN |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for method, metric in summary["metrics"].items():
        lines.append(
            f"| {method} | {metric['precision']:.6f} | {metric['recall']:.6f} | "
            f"{metric['f1']:.6f} | {metric['tp']} | {metric['fp']} | {metric['fn']} |"
        )
    lines.extend(
        [
            "",
            "## Scientific boundary",
            "",
            summary["claim_boundary"],
            "",
        ]
    )
    return "\n".join(lines)


def run_score_toolsandbox(args: argparse.Namespace) -> None:
    visible_rows = read_jsonl(absolute(args.visible_trajectories))
    key_rows = read_jsonl(absolute(args.completion_key))
    predictions = read_jsonl(absolute(args.predictions))
    inference = json.loads(absolute(args.inference_summary).read_text(encoding="utf-8"))
    require(inference["status"] == "complete", "ToolSandbox inference incomplete")
    require(len(visible_rows) == len(key_rows) == len(predictions), "ToolSandbox score population mismatch")
    visible_by_id = {str(row["sequence_id"]): row for row in visible_rows}
    key_by_id = {str(row["sequence_id"]): row for row in key_rows}
    pred_by_id = {str(row["sequence_id"]): row for row in predictions}
    require(set(visible_by_id) == set(key_by_id) == set(pred_by_id), "ToolSandbox score key mismatch")
    recurrence_boundaries, recurrence_reports = toolsandbox_recurrence_boundaries(visible_rows)
    methods = ("candidate", "step0059", "recurrence", "first_turn")
    counts: dict[str, dict[str, tuple[int, int, int]]] = {method: {} for method in methods}
    score_rows = []
    for sequence in sorted(visible_by_id):
        turns = len(visible_by_id[sequence]["turns"])
        gold = {int(value) for value in key_by_id[sequence]["completion_boundaries"]}
        predicted = {
            "candidate": {int(value) for value in pred_by_id[sequence]["candidate_completion_boundaries"]},
            "step0059": {int(value) for value in pred_by_id[sequence]["step0059_completion_boundaries"]},
            "recurrence": recurrence_boundaries[sequence],
            "first_turn": {0},
        }
        for method in methods:
            require(all(0 <= value < turns for value in predicted[method]), f"{method} boundary range")
            counts[method][sequence] = boundary_metric(gold, predicted[method])
        for turn in range(turns):
            score_rows.append(
                {
                    "sequence_id": sequence,
                    "scenario_id": visible_by_id[sequence]["scenario_id"],
                    "turn_index": turn,
                    "gold": turn in gold,
                    **{method: turn in predicted[method] for method in methods},
                }
            )
    metrics = {
        method: metric_from_counts(
            *tuple(sum(counts[method][sequence][index] for sequence in counts[method]) for index in range(3))
        )
        for method in methods
    }
    out_dir = absolute(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    bootstraps = {
        baseline: paired_scenario_bootstrap(
            visible_rows,
            counts,
            "candidate",
            baseline,
            out_dir / f"bootstrap-candidate-minus-{baseline}.jsonl",
        )
        for baseline in ("step0059", "recurrence", "first_turn")
    }
    supported = all(
        metrics["candidate"]["f1"] > metrics[baseline]["f1"]
        and bootstraps[baseline]["ci95"][0] > 0
        for baseline in bootstraps
    )
    contradicted = any(bootstraps[baseline]["ci95"][1] < 0 for baseline in bootstraps)
    interpretation = (
        "diagnostic-preflight"
        if inference["mode"] == "preflight"
        else "supported-and-adopted"
        if supported
        else "contradicted-not-adopted"
        if contradicted
        else "inconclusive-not-adopted"
    )
    summary = {
        "schema": SCHEMA + ".toolsandbox-score.v1",
        "status": "complete",
        "mode": inference["mode"],
        "registered_interpretation": interpretation,
        "population": {
            "trajectories": len(visible_rows),
            "scenario_ids": len({row["scenario_id"] for row in visible_rows}),
            "observed_turns": sum(len(row["turns"]) for row in visible_rows),
            "gold_completion_boundaries": sum(len(row["completion_boundaries"]) for row in key_rows),
        },
        "metrics": metrics,
        "bootstrap": bootstraps,
        "recurrence_folds": recurrence_reports,
        "decision": {"constructor_adoption": "adopted" if supported else "not-adopted"},
        "claim_boundary": (
            "The released TED progress curves are an external LLM-judge subgoal-progress reference. "
            "They test exact completion timing, not manual task boundaries, full nested topology, "
            "open-vocabulary task-label equivalence, or the phase/action/object/result suffix."
        ),
    }
    if inference["mode"] == "full":
        require(summary["population"]["trajectories"] == EXPECTED_TS_TRAJECTORIES, "full scored ToolSandbox trajectories")
        require(summary["population"]["observed_turns"] == EXPECTED_TS_TURNS, "full scored ToolSandbox turns")
        require(summary["population"]["gold_completion_boundaries"] == EXPECTED_TS_BOUNDARIES, "full ToolSandbox gold boundaries")
    write_jsonl(out_dir / "turn-boundary-score-rows.jsonl", score_rows)
    write_json(out_dir / "summary.json", summary)
    (out_dir / "report.md").write_text(toolsandbox_report(summary), encoding="utf-8")
    print(json.dumps(summary, sort_keys=True), flush=True)


def keyed_operations(path: Path) -> dict[tuple[str, int], dict[str, Any]]:
    rows: dict[tuple[str, int], dict[str, Any]] = {}
    for row in read_jsonl(path):
        key = (str(row["session"]), int(row["step_id"]))
        require(key not in rows, f"duplicate operation key in {path}")
        rows[key] = row
    return rows


def build_codetrace_score_rows(
    predictions: dict[tuple[str, int], dict[str, Any]],
    step0059: dict[tuple[str, int], dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    require(set(predictions) == set(step0059), "CodeTrace prediction/Step0059 coverage")
    operations = []
    for key in sorted(step0059):
        prediction = predictions[key]
        labels = visible.visible_labels(prediction)
        operations.append(
            {
                **step0059[key],
                "step0059_task_occurrence": step0059[key]["candidate_task_occurrence"],
                "result_grounded_visible_path": key[0] + "::" + visible.encode_path(labels),
                "result_grounded_labels": list(labels),
                "result_grounded_depth": int(prediction["task_depth"]),
                "result_grounded_hidden_instance": str(prediction["active_leaf_instance"]),
            }
        )
    by_session: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in operations:
        by_session[str(row["session"])].append(row)
    pairs = []
    methods = ("result_grounded_occurrence", "step0059_task_occurrence", "multires_recurrence")
    for session in sorted(by_session):
        rows = sorted(by_session[session], key=lambda row: int(row["step_id"]))
        run = -1
        previous_path = None
        for row in rows:
            path = row["result_grounded_visible_path"]
            if path != previous_path:
                run += 1
                previous_path = path
            row["result_grounded_occurrence"] = f"{session}:result-grounded-occurrence-{run:04d}"
        for left, right in zip(rows, rows[1:]):
            pair = {
                "session": session,
                "framework": left["framework"],
                "task_name": left["task_name"],
                "position": int(left["step_id"]),
                "official_boundary": left["official_stage"] != right["official_stage"],
            }
            for method in methods:
                pair[method] = left[method] != right[method]
            pairs.append(pair)
    return operations, pairs


def codetrace_report(summary: dict[str, Any]) -> str:
    lines = [
        "# Result-Grounded Task Stack — CodeTrace Compatibility Result",
        "",
        "CodeTrace human stages are a flat phase/strategy reference. This result is a compatibility diagnostic, not the task-stack adoption oracle.",
        "",
        "| Method | B³ P | B³ R | B³ F1 | Boundary F1 | Exact-span F1 |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for method, values in summary["metrics"].items():
        lines.append(
            f"| {method} | {values['bcubed']['precision']:.6f} | {values['bcubed']['recall']:.6f} | "
            f"{values['bcubed']['f1']:.6f} | {values['boundary']['f1']:.6f} | {values['span']['f1']:.6f} |"
        )
    lines.extend(["", "## Interpretation", "", summary["claim_boundary"], ""])
    return "\n".join(lines)


def run_score_codetrace(args: argparse.Namespace) -> None:
    predictions = keyed_operations(absolute(args.predictions))
    step0059 = keyed_operations(absolute(args.step0059_score_rows))
    inference = json.loads(absolute(args.inference_summary).read_text(encoding="utf-8"))
    require(inference["status"] == "complete", "CodeTrace inference incomplete")
    operations, pairs = build_codetrace_score_rows(predictions, step0059)
    methods = ("result_grounded_occurrence", "step0059_task_occurrence", "multires_recurrence")
    metrics = {
        method: {
            "bcubed": base.bcubed(operations, method),
            "boundary": base.boundary_metrics(pairs, method),
            "span": base.span_metrics(operations, method),
        }
        for method in methods
    }
    out_dir = absolute(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    bootstraps = {
        baseline: source.bcubed_task_bootstrap(
            operations,
            "result_grounded_occurrence",
            baseline,
            out_dir / f"bootstrap-result-grounded-minus-{baseline}.jsonl",
        )
        for baseline in ("step0059_task_occurrence", "multires_recurrence")
    }
    summary = {
        "schema": SCHEMA + ".codetrace-score.v1",
        "status": "complete",
        "mode": inference["mode"],
        "registered_interpretation": "compatibility-diagnostic-only",
        "population": {
            "sessions": len({row["session"] for row in operations}),
            "operations": len(operations),
            "pairs": len(pairs),
            "stage_occurrences": len({row["official_stage"] for row in operations}),
            "task_clusters": len({row["task_name"] for row in operations}),
        },
        "metrics": metrics,
        "bootstrap": bootstraps,
        "claim_boundary": (
            "Ordinary operation-level B-cubed, adjacent-boundary F1, and exact-span F1 against "
            "session-local human workflow stages test partition compatibility only. They do not "
            "validate task names, ancestor topology, cross-run task equivalence, or completion timing."
        ),
    }
    if inference["mode"] == "full":
        require(summary["population"]["sessions"] == EXPECTED_CODETRACE_SESSIONS, "full scored CodeTrace sessions")
        require(summary["population"]["operations"] == EXPECTED_CODETRACE_OPERATIONS, "full scored CodeTrace operations")
        require(summary["population"]["stage_occurrences"] == EXPECTED_CODETRACE_STAGES, "full CodeTrace stages")
        require(summary["population"]["task_clusters"] == EXPECTED_CODETRACE_TASKS, "full CodeTrace tasks")
    write_jsonl(out_dir / "operation-score-rows.jsonl", operations)
    write_jsonl(out_dir / "boundary-score-rows.jsonl", pairs)
    write_json(out_dir / "summary.json", summary)
    (out_dir / "report.md").write_text(codetrace_report(summary), encoding="utf-8")
    print(json.dumps(summary, sort_keys=True), flush=True)


def main() -> None:
    args = parse_args()
    if args.command == "inspect-toolsandbox":
        inspect_toolsandbox(args)
    elif args.command == "infer-toolsandbox":
        run_infer_toolsandbox(args)
    elif args.command == "score-toolsandbox":
        run_score_toolsandbox(args)
    elif args.command == "infer-codetrace":
        run_infer_codetrace(args)
    else:
        require(args.command == "score-codetrace", f"unknown command {args.command}")
        run_score_codetrace(args)


if __name__ == "__main__":
    main()
