#!/usr/bin/env python3
"""Infer and score a variable-depth semantic task stack on CodeTraceBench.

``infer`` never opens the official stage manifest. It reconstructs the exact
public operation sequence, asks a fixed local llama.cpp model for one causal
stack transition per operation, and materializes every prediction first.
``score`` is a separate process that loads those fixed predictions and only
then opens the official stage ranges.
"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
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
    tar_members,
)
from rq3_codetracebench_stage_fidelity_eval import (  # noqa: E402
    bcubed,
    boundary_metrics,
    load_stages_after_prediction,
    percentile,
)


ALGORITHM_VERSION = "qwen-semantic-task-stack-v2"
OUTPUT_CONSTRAINT_VERSION = "direct-gbnf-single-frame-nonempty-v2.3"
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
BOOTSTRAP_RESAMPLES = 10_000
BOOTSTRAP_SEED = 20_260_719
ROOT_BUDGET = 1_200
OBSERVATION_BUDGET = 2_400
ACTION_BUDGET = 2_400
LABEL_MAX_CHARS = 48
MIN_FRAME_SUPPORT = 2
SYSTEM_PROMPT = """You maintain the active semantic task stack of an AI agent.
Return JSON only. Keep the longest prefix of goals that still contains the
current work and drop goals that are no longer active. A frame is a temporally
extended semantic goal that can own multiple lower-level operations, not an
individual shell command, file, function, argument, expression, benchmark
stage, explanation, or word from an action. Continued work under the same goal
keeps the current leaf. One operation may introduce at most one newly active
goal as new_frame; use null when no new goal begins. A sibling task keeps its
parent and replaces the completed suffix. Use a concise lowercase English verb
phrase of at most 48 characters for a new frame. Never repeat a retained label.
The resulting stack must be non-empty."""
PROMPT_TEMPLATE = """PUBLIC TASK IDENTITY
{root_task}

CURRENT STACK (root to leaf)
{stack}

PRECEDING OBSERVATION
{preceding_observation}

CURRENT ACTION
{current_action}

Return keep_depth and new_frame only."""
LABEL_PATTERN = re.compile(r"^[a-z][a-z0-9 -]*$")
_thread_local = threading.local()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    infer = subparsers.add_parser("infer")
    infer.add_argument("mode", choices=("preflight", "full"))
    infer.add_argument("--target-operations", type=Path, required=True)
    infer.add_argument("--raw-root", type=Path, required=True)
    infer.add_argument("--llama-url", required=True)
    infer.add_argument("--model", required=True)
    infer.add_argument("--model-sha256", required=True)
    infer.add_argument("--seed", type=int, default=BOOTSTRAP_SEED)
    infer.add_argument("--workers", type=int, default=8)
    infer.add_argument("--timeout-seconds", type=int, default=180)
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
    temporary.write_text(
        json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as output:
        for row in rows:
            output.write(json.dumps(row, sort_keys=True, ensure_ascii=False) + "\n")


def load_visible_operations(path: Path) -> dict[str, list[dict[str, Any]]]:
    """Read source-visible fields only; no official stage file is available."""
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    with path.open(encoding="utf-8") as source:
        for line_number, line in enumerate(source, 1):
            record = json.loads(line)
            fields = record.get("fields")
            require(isinstance(fields, dict), f"{path}:{line_number}: missing fields")
            require(record.get("value") == 1, f"{path}:{line_number}: non-unit weight")
            for field in (
                "traj_id",
                "step_id",
                "action_kind",
                "raw_action_key",
                "phase",
                "source_ref",
            ):
                require(fields.get(field) not in (None, ""), f"{path}:{line_number}: {field}")
            grouped[str(fields["traj_id"])].append(
                {
                    "session": str(fields["traj_id"]),
                    "step_id": int(fields["step_id"]),
                    "action": str(fields["action_kind"]),
                    "action_detail": str(fields["raw_action_key"]),
                    "phase": str(fields["phase"]),
                    "source_ref": str(fields["source_ref"]),
                }
            )
    for session, rows in grouped.items():
        rows.sort(key=lambda row: int(row["step_id"]))
        require(
            [int(row["step_id"]) for row in rows] == list(range(1, len(rows) + 1)),
            f"{session}: non-consecutive operation ids",
        )
    return dict(grouped)


def framework_for_session(session: str) -> str:
    if session.startswith("miniswe-"):
        return "mini-SWE-agent"
    if session.startswith("openhands-"):
        return "OpenHands"
    if session.startswith("sweagent-"):
        return "SWE-agent"
    if session.startswith("terminus2-"):
        return "Terminus2"
    raise RuntimeError(f"unknown CodeTrace framework prefix: {session}")


def session_cache_name(session: str) -> str:
    return hashlib.sha256(session.encode()).hexdigest()[:24] + ".json"


def clip_text(value: str | None, budget: int) -> str:
    if value is None:
        return "none"
    cleaned = value.strip()
    if len(cleaned) <= budget:
        return cleaned or "none"
    left = (budget - 1) // 2
    right = budget - 1 - left
    return cleaned[:left] + "…" + cleaned[-right:]


def task_text_from_source_ref(source_ref: str) -> str:
    member = source_ref.split("#", 1)[0]
    path = Path(member)
    parts = path.parts
    name = path.name
    if len(parts) >= 3 and parts[0] == "swe_raw":
        task = parts[2]
    elif len(parts) >= 4 and parts[0] in {
        "miniswe",
        "openhands",
        "sweagent",
        "terminus2",
    }:
        task = parts[3]
    elif name.endswith(".traj.json"):
        task = name[: -len(".traj.json")]
    elif name.endswith(".traj"):
        task = name[: -len(".traj")]
    elif name == "commands.txt" and len(path.parents) >= 2:
        task = path.parent.parent.name
    else:
        task = path.parent.name
    return task.replace("__", " / ").replace("_", " ").replace("-", " ")


def reconstruct_session(
    raw_root: Path,
    session: str,
    rows: list[dict[str, Any]],
) -> tuple[str, list[dict[str, Any]]]:
    framework = framework_for_session(session)
    archive = raw_root / "bench_artifacts" / "full" / f"{session}.tar.zst"
    require(archive.is_file(), f"missing public archive: {archive}")
    members = tar_members(archive)
    raw_steps, adapter = ADAPTERS[framework](archive, members, len(rows))
    require(len(raw_steps) == len(rows), f"{session}: adapter operation count mismatch")
    evidence = []
    for index, (visible, raw) in enumerate(zip(rows, raw_steps, strict=True)):
        require(raw.step_id == int(visible["step_id"]), f"{session}: step mismatch")
        require(raw.source_ref == visible["source_ref"], f"{session}: source_ref mismatch")
        preceding = raw_steps[index - 1].observation if index else None
        evidence.append(
            {
                **visible,
                "source_action": raw.action,
                "preceding_observation": preceding,
            }
        )
    return adapter, evidence


def select_preflight_sessions(
    grouped: dict[str, list[dict[str, Any]]],
) -> list[str]:
    selected = []
    for framework in sorted(EXPECTED_FRAMEWORKS):
        sessions = sorted(
            session
            for session in grouped
            if framework_for_session(session) == framework
        )
        require(bool(sessions), f"no preflight session for {framework}")
        selected.append(sessions[0])
    return sorted(selected)


def grammar_for_depth(depth: int) -> str:
    """Compile the fixed transition contract directly to llama.cpp GBNF."""
    zero_transition = (
        '"{" "\\"keep_depth\\"" ":" "0" "," '
        '"\\"new_frame\\"" ":" label "}"'
    )
    if depth == 0:
        return f'''root ::= {zero_transition}
label ::= "\\"" [a-z] [a-z0-9 -]{{0,{LABEL_MAX_CHARS - 1}}} "\\""
'''
    nonzero_values = " | ".join(f'"{value}"' for value in range(1, depth + 1))
    return f'''root ::= zero-transition | nonzero-transition
zero-transition ::= {zero_transition}
nonzero-transition ::= "{{" "\\"keep_depth\\"" ":" nonzero-keep "," "\\"new_frame\\"" ":" frame "}}"
nonzero-keep ::= {nonzero_values}
frame ::= "null" | label
label ::= "\\"" [a-z] [a-z0-9 -]{{0,{LABEL_MAX_CHARS - 1}}} "\\""
'''


def request_session() -> requests.Session:
    session = getattr(_thread_local, "requests_session", None)
    if session is None:
        session = requests.Session()
        _thread_local.requests_session = session
    return session


def call_model(
    base_url: str,
    model: str,
    seed: int,
    timeout_seconds: int,
    prompt: str,
    grammar: str,
) -> tuple[str, dict[str, Any], float]:
    body = {
        "model": model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0,
        "seed": seed,
        "max_tokens": 96,
        "grammar": grammar,
        "stream": False,
    }
    started = time.monotonic()
    response = request_session().post(
        base_url.rstrip("/") + "/v1/chat/completions",
        json=body,
        timeout=timeout_seconds,
    )
    elapsed_ms = (time.monotonic() - started) * 1000.0
    response.raise_for_status()
    payload = response.json()
    raw = str(payload["choices"][0]["message"]["content"])
    return raw, payload, elapsed_ms


def validate_transition(
    raw: str,
    depth: int,
) -> tuple[int, str | None]:
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as error:
        raise RuntimeError(f"model output is not JSON: {raw!r}") from error
    require(
        set(parsed) == {"keep_depth", "new_frame"},
        "unexpected transition keys",
    )
    keep = parsed["keep_depth"]
    new_frame = parsed["new_frame"]
    require(type(keep) is int and 0 <= keep <= depth, "invalid keep_depth")
    require(new_frame is None or type(new_frame) is str, "invalid new_frame type")
    if new_frame is not None:
        require(0 < len(new_frame) <= LABEL_MAX_CHARS, "invalid new_frame length")
        require(
            LABEL_PATTERN.fullmatch(new_frame) is not None,
            "invalid new_frame syntax",
        )
    require(keep >= 1 or new_frame is not None, "transition produced an empty stack")
    return keep, new_frame


def prompt_for(
    task_text: str,
    stack: list[dict[str, str]],
    preceding_observation: str | None,
    current_action: str,
) -> str:
    return PROMPT_TEMPLATE.format(
        root_task=clip_text(task_text, ROOT_BUDGET),
        stack=json.dumps([frame["label"] for frame in stack], ensure_ascii=False),
        preceding_observation=clip_text(preceding_observation, OBSERVATION_BUDGET),
        current_action=clip_text(current_action, ACTION_BUDGET),
    )


def infer_one_session(
    session: str,
    rows: list[dict[str, Any]],
    raw_root: Path,
    cache_dir: Path,
    llama_url: str,
    model: str,
    model_sha256: str,
    seed: int,
    timeout_seconds: int,
) -> dict[str, Any]:
    cache_path = cache_dir / session_cache_name(session)
    adapter, evidence = reconstruct_session(raw_root, session, rows)
    task_text = task_text_from_source_ref(rows[0]["source_ref"])
    transitions: list[dict[str, Any]] = []
    stack: list[dict[str, str]] = []
    next_frame = 0
    origin_output_constraint_version: str | None = None

    if cache_path.is_file():
        cached = json.loads(cache_path.read_text(encoding="utf-8"))
        require(cached["algorithm_version"] == ALGORITHM_VERSION, f"{session}: cache version")
        require(cached["session"] == session, f"{session}: cache identity")
        require(cached["model"] == model, f"{session}: cache model")
        require(cached["model_sha256"] == model_sha256, f"{session}: cache SHA")
        require(
            cached["output_constraint_version"] == OUTPUT_CONSTRAINT_VERSION,
            f"{session}: cache output constraint",
        )
        transitions = list(cached.get("transitions") or [])
        origin_output_constraint_version = cached.get(
            "origin_output_constraint_version"
        )
        require(len(transitions) <= len(evidence), f"{session}: cache longer than input")
        for index, row in enumerate(transitions):
            require(int(row["step_id"]) == index + 1, f"{session}: cached step order")
        if transitions:
            stack = [dict(frame) for frame in transitions[-1]["stack_after"]]
            next_frame = int(cached["next_frame"])

    for operation in evidence[len(transitions) :]:
        prompt = prompt_for(
            task_text,
            stack,
            operation["preceding_observation"],
            operation["source_action"],
        )
        depth_before = len(stack)
        raw, response, elapsed_ms = call_model(
            llama_url,
            model,
            seed,
            timeout_seconds,
            prompt,
            grammar_for_depth(depth_before),
        )
        keep, new_frame = validate_transition(raw, depth_before)
        stack_before = [dict(frame) for frame in stack]
        stack = [dict(frame) for frame in stack[:keep]]
        if new_frame is not None:
            stack.append(
                {
                    "instance": f"{session}:frame-{next_frame:05d}",
                    "label": new_frame,
                }
            )
            next_frame += 1
        transition_kind = (
            "stay"
            if keep == depth_before and new_frame is None
            else "push"
            if keep == depth_before
            else "pop"
            if new_frame is None
            else "replace"
        )
        require(bool(stack), f"{session}: empty stack after valid transition")
        usage = response.get("usage") or {}
        transitions.append(
            {
                "session": session,
                "framework": framework_for_session(session),
                "step_id": int(operation["step_id"]),
                "source_ref": operation["source_ref"],
                "task_text": task_text,
                "source_action": operation["source_action"],
                "preceding_observation": operation["preceding_observation"],
                "prompt": prompt,
                "stack_before": stack_before,
                "keep_depth": keep,
                "new_frame": new_frame,
                "transition_kind": transition_kind,
                "stack_after": [dict(frame) for frame in stack],
                "leaf_instance": stack[-1]["instance"],
                "leaf_label": stack[-1]["label"],
                "raw_response": raw,
                "usage": usage,
                "elapsed_ms": elapsed_ms,
            }
        )
        write_json_atomic(
            cache_path,
            {
                "algorithm_version": ALGORITHM_VERSION,
                "session": session,
                "framework": framework_for_session(session),
                "adapter": adapter,
                "model": model,
                "model_sha256": model_sha256,
                "output_constraint_version": OUTPUT_CONSTRAINT_VERSION,
                **(
                    {
                        "origin_output_constraint_version":
                            origin_output_constraint_version
                    }
                    if origin_output_constraint_version is not None
                    else {}
                ),
                "seed": seed,
                "task_text": task_text,
                "next_frame": next_frame,
                "input_operations": len(evidence),
                "transitions": transitions,
            },
        )
    return json.loads(cache_path.read_text(encoding="utf-8"))


def run_inference(args: argparse.Namespace) -> None:
    target_path = absolute(args.target_operations)
    raw_root = absolute(args.raw_root)
    out_dir = absolute(args.out)
    for path in (target_path, raw_root):
        require(path.exists(), f"missing input: {path}")
    grouped = load_visible_operations(target_path)
    selected = (
        select_preflight_sessions(grouped)
        if args.mode == "preflight"
        else sorted(grouped)
    )
    if args.mode == "full":
        require(len(selected) == EXPECTED_SESSIONS, "unexpected full session count")
        require(
            sum(len(grouped[session]) for session in selected) == EXPECTED_OPERATIONS,
            "unexpected full operation count",
        )

    out_dir.mkdir(parents=True, exist_ok=True)
    cache_dir = out_dir / "sessions"
    started = time.monotonic()
    results: dict[str, dict[str, Any]] = {}
    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = {
            executor.submit(
                infer_one_session,
                session,
                grouped[session],
                raw_root,
                cache_dir,
                args.llama_url,
                args.model,
                args.model_sha256,
                args.seed,
                args.timeout_seconds,
            ): session
            for session in selected
        }
        for future in as_completed(futures):
            session = futures[future]
            results[session] = future.result()
            print(
                f"complete {len(results)}/{len(selected)} {session} "
                f"({len(results[session]['transitions'])} operations)",
                flush=True,
            )

    predictions = [
        transition
        for session in selected
        for transition in results[session]["transitions"]
    ]
    require(
        len(predictions) == sum(len(grouped[session]) for session in selected),
        "prediction coverage mismatch",
    )
    write_jsonl(out_dir / "predictions.jsonl", predictions)
    depths = [len(row["stack_after"]) for row in predictions]
    usage = Counter()
    for row in predictions:
        for key, value in row["usage"].items():
            if isinstance(value, (int, float)):
                usage[key] += value
    summary = {
        "schema": "agentsight.rq3-qwen-semantic-task-stack.inference.v2",
        "algorithm_version": ALGORITHM_VERSION,
        "mode": args.mode,
        "status": "complete",
        "model": args.model,
        "model_sha256": args.model_sha256,
        "output_constraint_version": OUTPUT_CONSTRAINT_VERSION,
        "llama_url": args.llama_url,
        "seed": args.seed,
        "workers": args.workers,
        "sessions": len(selected),
        "operations": len(predictions),
        "frameworks": sorted({framework_for_session(session) for session in selected}),
        "depth": {
            "minimum": min(depths),
            "maximum": max(depths),
            "mean": sum(depths) / len(depths),
            "counts": dict(sorted(Counter(depths).items())),
        },
        "transitions": {
            "counts": dict(
                sorted(Counter(row["transition_kind"] for row in predictions).items())
            ),
            "new_frame_rate": sum(
                row["new_frame"] is not None for row in predictions
            )
            / len(predictions),
        },
        "model_usage": dict(usage),
        "wall_seconds": time.monotonic() - started,
        "predictions": relative(out_dir / "predictions.jsonl"),
        "session_cache": relative(cache_dir),
        "label_isolation": {
            "official_manifest_opened": False,
            "official_stages_opened": False,
            "current_result_visible": False,
            "visible_fields": [
                "public task identity de-slugged from source_ref",
                "complete current stack labels",
                "preceding observation",
                "current source action",
            ],
        },
    }
    write_json(out_dir / "inference-summary.json", summary)
    print(json.dumps(summary, sort_keys=True), flush=True)


def load_predictions(path: Path) -> dict[tuple[str, int], dict[str, Any]]:
    output = {}
    with path.open(encoding="utf-8") as source:
        for line_number, line in enumerate(source, 1):
            row = json.loads(line)
            key = (str(row["session"]), int(row["step_id"]))
            require(key not in output, f"duplicate prediction line {line_number}")
            require(bool(row.get("leaf_instance")), f"missing leaf at line {line_number}")
            output[key] = row
    return output


def load_multires_assignments(path: Path) -> dict[tuple[str, int], dict[str, str]]:
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
            }
    return output


def contract_predictions(
    predictions: dict[tuple[str, int], dict[str, Any]],
) -> tuple[dict[tuple[str, int], dict[str, Any]], dict[str, Any]]:
    """Retain task roots and frames that span multiple source operations."""
    frame_support: Counter[str] = Counter()
    frame_labels: dict[str, str] = {}
    sessions: dict[str, list[tuple[int, dict[str, Any]]]] = defaultdict(list)
    for (session, step_id), row in predictions.items():
        sessions[session].append((step_id, row))
        for frame in row["stack_after"]:
            instance = str(frame["instance"])
            label = str(frame["label"])
            require(
                frame_labels.setdefault(instance, label) == label,
                f"{instance}: frame label drift",
            )
            frame_support[instance] += 1

    contracted: dict[tuple[str, int], dict[str, Any]] = {}
    raw_leaves: set[str] = set()
    effective_leaves: set[str] = set()
    retained_frames: set[str] = set()
    root_operations = 0
    effective_depths: list[int] = []
    for session, session_rows in sessions.items():
        session_rows.sort(key=lambda item: item[0])
        require(
            [step_id for step_id, _ in session_rows]
            == list(range(1, len(session_rows) + 1)),
            f"{session}: non-consecutive prediction ids",
        )
        task_labels = {str(row["task_text"]) for _, row in session_rows}
        require(len(task_labels) == 1, f"{session}: task-root label drift")
        root = {
            "instance": f"{session}:task-root",
            "label": next(iter(task_labels)),
            "support": len(session_rows),
            "kind": "task_root",
        }
        for step_id, row in session_rows:
            raw_stack = [dict(frame) for frame in row["stack_after"]]
            retained = [
                {
                    **frame,
                    "support": frame_support[str(frame["instance"])],
                    "kind": "generated_frame",
                }
                for frame in raw_stack
                if frame_support[str(frame["instance"])] >= MIN_FRAME_SUPPORT
            ]
            effective_stack = [dict(root), *retained]
            effective_leaf = effective_stack[-1]
            raw_leaf = raw_stack[-1]
            raw_leaves.add(str(raw_leaf["instance"]))
            effective_leaves.add(str(effective_leaf["instance"]))
            retained_frames.update(str(frame["instance"]) for frame in retained)
            root_operations += not retained
            effective_depths.append(len(effective_stack))
            contracted[(session, step_id)] = {
                "session": session,
                "step_id": step_id,
                "raw_leaf_instance": str(raw_leaf["instance"]),
                "raw_leaf_label": str(raw_leaf["label"]),
                "raw_depth": len(raw_stack),
                "effective_leaf_instance": str(effective_leaf["instance"]),
                "effective_leaf_label": str(effective_leaf["label"]),
                "effective_depth": len(effective_stack),
                "effective_stack": effective_stack,
            }

    require(set(contracted) == set(predictions), "contraction coverage mismatch")
    require(all(row["effective_stack"] for row in contracted.values()), "empty result")
    generated_frames = set(frame_support)
    raw_groups = len(raw_leaves)
    effective_groups = len(effective_leaves)
    return contracted, {
        "rule": (
            "immutable task root plus generated frame instances with active-path "
            f"support >= {MIN_FRAME_SUPPORT} operations"
        ),
        "minimum_generated_frame_support": MIN_FRAME_SUPPORT,
        "operations": len(contracted),
        "generated_frames": len(generated_frames),
        "retained_generated_frames": len(retained_frames),
        "contracted_generated_frames": len(generated_frames - retained_frames),
        "raw_leaf_groups": raw_groups,
        "effective_leaf_groups": effective_groups,
        "leaf_group_reduction_fraction": 1.0 - effective_groups / raw_groups,
        "operations_assigned_to_task_root": root_operations,
        "effective_depth_including_root": {
            "minimum": min(effective_depths),
            "maximum": max(effective_depths),
            "mean": sum(effective_depths) / len(effective_depths),
            "counts": dict(sorted(Counter(effective_depths).items())),
        },
        "properties": {
            "source_only": True,
            "depth_cap": None,
            "every_operation_has_exactly_one_effective_leaf": True,
            "operation_weight_conserved": True,
        },
    }


def build_score_rows(
    grouped: dict[str, list[dict[str, Any]]],
    selected: list[str],
    predictions: dict[tuple[str, int], dict[str, Any]],
    contracted: dict[tuple[str, int], dict[str, Any]],
    baselines: dict[tuple[str, int], dict[str, str]],
    official: dict[tuple[str, int], str],
    frameworks: dict[str, str],
    tasks: dict[str, str],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    operations = []
    pairs = []
    methods = (
        "semantic_stack",
        "multires_recurrence",
        "current_recurrence",
        "phase",
        "raw_action",
    )
    for session in selected:
        previous = None
        for row in grouped[session]:
            step_id = int(row["step_id"])
            key = (session, step_id)
            require(key in predictions, f"missing semantic prediction: {key}")
            require(key in contracted, f"missing contracted prediction: {key}")
            require(key in baselines, f"missing baseline prediction: {key}")
            operation = {
                "session": session,
                "framework": frameworks[session],
                "task_name": tasks[session],
                "step_id": step_id,
                "official_stage": official[key],
                "semantic_stack": str(contracted[key]["effective_leaf_instance"]),
                "semantic_label": str(contracted[key]["effective_leaf_label"]),
                "semantic_depth": int(contracted[key]["effective_depth"]),
                "raw_semantic_stack": str(predictions[key]["leaf_instance"]),
                "raw_semantic_label": str(predictions[key]["leaf_label"]),
                "raw_semantic_depth": len(predictions[key]["stack_after"]),
                **baselines[key],
            }
            operations.append(operation)
            if previous is not None:
                pair = {
                    "session": session,
                    "framework": frameworks[session],
                    "position": step_id - 1,
                    "official_boundary": previous["official_stage"]
                    != operation["official_stage"],
                }
                for method in methods:
                    pair[method] = previous[method] != operation[method]
                pair["raw_semantic_stack"] = (
                    previous["raw_semantic_stack"]
                    != operation["raw_semantic_stack"]
                )
                pairs.append(pair)
            previous = operation
    return pairs, operations


def metric_bundle(
    pair_rows: list[dict[str, Any]],
    operation_rows: list[dict[str, Any]],
    methods: tuple[str, ...],
) -> dict[str, Any]:
    return {
        method: {
            "partition": bcubed(operation_rows, method),
            "boundary": boundary_metrics(pair_rows, method),
        }
        for method in methods
    }


def task_bootstrap(
    rows: list[dict[str, Any]],
    candidate: str,
    baseline: str,
    out_dir: Path,
) -> dict[str, Any]:
    by_session: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_session[str(row["session"])].append(row)
    task_sessions: dict[str, list[str]] = defaultdict(list)
    sufficient: dict[tuple[str, str], tuple[float, float, int]] = {}
    for session, session_rows in by_session.items():
        task_names = {str(row["task_name"]) for row in session_rows}
        require(len(task_names) == 1, f"{session}: multiple task names")
        task = next(iter(task_names))
        task_sessions[task].append(session)
        for method in (candidate, baseline):
            metric = bcubed(session_rows, method)
            count = len(session_rows)
            sufficient[(session, method)] = (
                metric["precision"] * count,
                metric["recall"] * count,
                count,
            )
    tasks = sorted(task_sessions)
    require(len(tasks) == EXPECTED_TASKS, f"unexpected task cluster count: {len(tasks)}")

    def f1(draw: list[str], method: str) -> float:
        precision_sum = 0.0
        recall_sum = 0.0
        count_sum = 0
        for task in draw:
            for session in task_sessions[task]:
                precision, recall, count = sufficient[(session, method)]
                precision_sum += precision
                recall_sum += recall
                count_sum += count
        precision = precision_sum / count_sum
        recall = recall_sum / count_sum
        return 2 * precision * recall / (precision + recall) if precision + recall else 0.0

    generator = random.Random(BOOTSTRAP_SEED)
    deltas = []
    for _ in range(BOOTSTRAP_RESAMPLES):
        draw = generator.choices(tasks, k=len(tasks))
        deltas.append(f1(draw, candidate) - f1(draw, baseline))
    raw = out_dir / "task-bootstrap-deltas.jsonl"
    write_jsonl(
        raw,
        ({"resample": index, "delta": delta} for index, delta in enumerate(deltas)),
    )
    return {
        "candidate": candidate,
        "baseline": baseline,
        "unit": "task_name",
        "clusters": len(tasks),
        "resamples": BOOTSTRAP_RESAMPLES,
        "seed": BOOTSTRAP_SEED,
        "mean_delta": sum(deltas) / len(deltas),
        "median_delta": percentile(deltas, 0.5),
        "ci95": [percentile(deltas, 0.025), percentile(deltas, 0.975)],
        "positive_fraction": sum(delta > 0 for delta in deltas) / len(deltas),
        "raw_deltas": relative(raw),
    }


def result_markdown(summary: dict[str, Any]) -> str:
    lines = [
        "# Variable-Depth Semantic Task Stack — Complete CodeTraceBench Result",
        "",
        f"**Run status:** {summary['status']}",
        f"**Registered interpretation:** {summary['registered_interpretation']}",
        "",
        "## Complete Population",
        "",
        f"- {summary['population']['sessions']} trajectories",
        f"- {summary['population']['operations']} operations",
        f"- {summary['population']['stages']} human stages",
        f"- {summary['population']['tasks']} task clusters",
        f"- {summary['population']['pairs']} adjacent decisions",
        "",
        "## Standard Metrics",
        "",
        "| Method | B-cubed P | B-cubed R | B-cubed F1 | Boundary F1 |",
        "|---|---:|---:|---:|---:|",
    ]
    for method, metric in summary["metrics"].items():
        lines.append(
            f"| {method} | {metric['partition']['precision']:.6f} | "
            f"{metric['partition']['recall']:.6f} | "
            f"{metric['partition']['f1']:.6f} | "
            f"{metric['boundary']['f1']:.6f} |"
        )
    lines.extend(
        [
            "",
            "## Source-Only Contraction Diagnostic",
            "",
            f"The uncapped raw stack produced "
            f"{summary['contraction']['raw_leaf_groups']} leaf groups. The fixed "
            f"support rule produced {summary['contraction']['effective_leaf_groups']} "
            f"effective groups; {summary['contraction']['operations_assigned_to_task_root']} "
            f"operations fell back to their immutable task root.",
            f"Raw, uncontracted diagnostic: B-cubed F1 "
            f"{summary['raw_stack_diagnostic']['partition']['f1']:.6f}; boundary F1 "
            f"{summary['raw_stack_diagnostic']['boundary']['f1']:.6f}.",
            "",
            "## Paired Task-Cluster Bootstrap",
            "",
            f"Candidate minus registered multi-resolution comparator "
            f"(`{summary['bootstrap']['baseline']}`): mean "
            f"{summary['bootstrap']['mean_delta']:+.6f}, 95% interval "
            f"[{summary['bootstrap']['ci95'][0]:+.6f}, "
            f"{summary['bootstrap']['ci95'][1]:+.6f}], positive fraction "
            f"{summary['bootstrap']['positive_fraction']:.6f}.",
            "",
            "## Claim Boundary",
            "",
            summary["claim_boundary"],
            "",
        ]
    )
    return "\n".join(lines)


def run_score(args: argparse.Namespace) -> None:
    target_path = absolute(args.target_operations)
    prediction_path = absolute(args.predictions)
    manifest_path = absolute(args.verified_manifest)
    baseline_path = absolute(args.multires_assignments)
    out_dir = absolute(args.out)
    for path in (target_path, prediction_path, manifest_path, baseline_path):
        require(path.is_file(), f"missing input: {path}")

    grouped = load_visible_operations(target_path)
    selected = sorted(grouped)
    require(len(selected) == EXPECTED_SESSIONS, "unexpected complete session count")
    require(sum(map(len, grouped.values())) == EXPECTED_OPERATIONS, "operation count")
    predictions = load_predictions(prediction_path)
    baselines = load_multires_assignments(baseline_path)
    expected_keys = {
        (session, int(row["step_id"]))
        for session in selected
        for row in grouped[session]
    }
    require(set(predictions) == expected_keys, "semantic prediction coverage mismatch")
    require(expected_keys <= set(baselines), "baseline coverage mismatch")

    # The source-only hierarchy is finalized and materialized before labels open.
    contracted, contraction_summary = contract_predictions(predictions)
    out_dir.mkdir(parents=True, exist_ok=True)
    contracted_path = out_dir / "contracted-predictions.jsonl"
    write_jsonl(
        contracted_path,
        (contracted[key] for key in sorted(contracted)),
    )
    write_json(out_dir / "contraction-summary.json", contraction_summary)

    # This is the first point at which scorer-only official stages are opened.
    official, frameworks, tasks = load_stages_after_prediction(
        manifest_path, grouped, selected
    )
    require(len(set(official.values())) == EXPECTED_STAGES, "official stage count")
    require(set(frameworks.values()) == EXPECTED_FRAMEWORKS, "framework coverage")
    require(len(set(tasks.values())) == EXPECTED_TASKS, "task count")

    pair_rows, operation_rows = build_score_rows(
        grouped,
        selected,
        predictions,
        contracted,
        baselines,
        official,
        frameworks,
        tasks,
    )
    methods = (
        "semantic_stack",
        "multires_recurrence",
        "current_recurrence",
        "phase",
        "raw_action",
    )
    metrics = metric_bundle(pair_rows, operation_rows, methods)
    raw_stack_diagnostic = metric_bundle(
        pair_rows, operation_rows, ("raw_semantic_stack",)
    )["raw_semantic_stack"]
    strongest_baseline = max(
        methods[1:], key=lambda method: metrics[method]["partition"]["f1"]
    )
    registered_comparator = "multires_recurrence"
    bootstrap = task_bootstrap(
        operation_rows, "semantic_stack", registered_comparator, out_dir
    )
    per_framework = {}
    for framework in sorted(EXPECTED_FRAMEWORKS):
        framework_ops = [row for row in operation_rows if row["framework"] == framework]
        framework_pairs = [row for row in pair_rows if row["framework"] == framework]
        per_framework[framework] = metric_bundle(framework_pairs, framework_ops, methods)

    candidate_f1 = metrics["semantic_stack"]["partition"]["f1"]
    beats_all = all(
        candidate_f1 > metrics[method]["partition"]["f1"] for method in methods[1:]
    )
    framework_nonnegative = all(
        per_framework[framework]["semantic_stack"]["partition"]["f1"]
        >= per_framework[framework][registered_comparator]["partition"]["f1"]
        for framework in EXPECTED_FRAMEWORKS
    )
    supported = beats_all and bootstrap["ci95"][0] > 0 and framework_nonnegative
    registered = "supported_and_adopt" if supported else (
        "promising_not_adopted" if beats_all else "contradicted"
    )
    write_jsonl(out_dir / "operation-assignments.jsonl", operation_rows)
    write_jsonl(out_dir / "pair-decisions.jsonl", pair_rows)
    summary = {
        "schema": "agentsight.rq3-qwen-semantic-task-stack.score.v2",
        "status": "complete",
        "registered_interpretation": registered,
        "population": {
            "sessions": len(selected),
            "operations": len(operation_rows),
            "pairs": len(pair_rows),
            "stages": len(set(official.values())),
            "tasks": len(set(tasks.values())),
            "frameworks": sorted(set(frameworks.values())),
        },
        "metrics": metrics,
        "raw_stack_diagnostic": raw_stack_diagnostic,
        "contraction": contraction_summary,
        "per_framework": per_framework,
        "strongest_baseline": strongest_baseline,
        "registered_bootstrap_comparator": registered_comparator,
        "bootstrap": bootstrap,
        "validity": {
            "prediction_coverage_exact": set(predictions) == expected_keys,
            "official_stages_loaded_after_prediction": True,
            "all_stacks_nonempty": all(row["stack_after"] for row in predictions.values()),
            "contracted_partition_materialized_before_official_stages": True,
            "every_operation_has_exactly_one_effective_leaf": (
                len(contracted) == len(expected_keys)
            ),
            "all_framework_effects_nonnegative_vs_registered_comparator": framework_nonnegative,
        },
        "claim_boundary": (
            "This is a system-level comparison of a semantic-stack backend using "
            "public task-identity, action, and preceding-observation text against registered "
            "recurrence and source-field constructors. It is not matched-input "
            "action-only superiority, gold nested-hierarchy fidelity, literal frame-name "
            "accuracy, or evidence that hierarchy depth or stack discipline alone caused "
            "the difference."
        ),
        "inputs": {
            "predictions": relative(prediction_path),
            "target_operations": relative(target_path),
            "verified_manifest": relative(manifest_path),
            "multires_assignments": relative(baseline_path),
            "contracted_predictions": relative(contracted_path),
        },
        "outputs": {
            "operation_assignments": relative(out_dir / "operation-assignments.jsonl"),
            "pair_decisions": relative(out_dir / "pair-decisions.jsonl"),
        },
    }
    write_json(out_dir / "summary.json", summary)
    (out_dir / "report.md").write_text(result_markdown(summary), encoding="utf-8")
    print(json.dumps(summary, sort_keys=True), flush=True)


def main() -> None:
    args = parse_args()
    try:
        if args.command == "infer":
            run_inference(args)
        else:
            run_score(args)
    except (RuntimeError, SourceError, requests.RequestException) as error:
        raise SystemExit(str(error)) from error


if __name__ == "__main__":
    main()
