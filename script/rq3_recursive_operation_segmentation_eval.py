#!/usr/bin/env python3
"""Infer and score recursive Agent-authored operation segmentation.

Inference reads complete public CodeTrace trajectories, asks a local LLM Agent
to name the task root and recursively choose one semantic transition or STOP,
and emits stable-ID operation marks for AgentPProf. Scoring is a separate
command that opens official workflow stages only after predictions are fixed.
"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import hashlib
import inspect
import json
from pathlib import Path
import re
import subprocess
import sys
import time
from typing import Any, Callable, Iterable

import requests


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "script"))

import rq3_global_task_semantic_segmentation_eval as global_eval  # noqa: E402
import rq3_source_native_task_progress_boundary_eval as source  # noqa: E402
import rq3_stateful_native_turn_task_stack_eval as stateful  # noqa: E402


base = source.base
ALGORITHM_VERSION = "recursive-operation-segmentation-v1"
SCHEMA = "agentsight.rq3-recursive-operation-segmentation"
EXPECTED_SESSIONS = 405
EXPECTED_OPERATIONS = 20_866
EXPECTED_TURNS = 17_148
EXPECTED_STAGES = 2_948
EXPECTED_TASKS = 251
EXPECTED_FRAMEWORKS = base.EXPECTED_FRAMEWORKS
LONG_HORIZON_SESSIONS = 41
LONG_HORIZON_OPERATIONS = 5_750
SEED = 20_260_722
CONTEXT_MARGIN = 512
OUTPUT_TOKENS = 128
LABEL_MAX_CHARS = 80

ROOT_SYSTEM = """Name the concrete responsibility represented by the user's
request. Return one concise lowercase semantic operation phrase. Describe the
task responsibility, not an agent, model, session, tool, command, file path,
status, or generic word such as task. Return only the required JSON."""

SPLIT_SYSTEM = """Read the complete visible evidence for one contiguous
interval of an already-finished AI-agent trajectory. Decide whether the
interval contains one most important transition between two distinct,
persistent task responsibilities or task-progress states.

Return STOP when the interval advances one persistent responsibility, even if
tools, commands, files, actions, statuses, errors, retries, or observations
change. Return SPLIT only when both sides can be named as distinct semantic
responsibilities that explain a sustained change in what the agent is trying
to accomplish. Choose the single most important such boundary. Child names
must be concise lowercase semantic operation phrases, not tool or file labels.
Return only the required JSON."""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)

    infer = commands.add_parser("infer")
    infer.add_argument("mode", choices=("preflight", "full"))
    infer.add_argument("--target-operations", type=Path, required=True)
    infer.add_argument("--raw-root", type=Path, required=True)
    infer.add_argument("--llama-url", required=True)
    infer.add_argument("--model-name", required=True)
    infer.add_argument("--model-path", type=Path, required=True)
    infer.add_argument("--model-sha256", required=True)
    infer.add_argument("--agentpprof-manifest", type=Path, default=Path("agentpprof/Cargo.toml"))
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


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )


def write_json_atomic(path: Path, value: Any) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    write_json(temporary, value)
    temporary.replace(path)


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as stream:
        for row in rows:
            stream.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
    with path.open(encoding="utf-8") as stream:
        for line_number, line in enumerate(stream, 1):
            if not line.strip():
                continue
            row = json.loads(line)
            require(isinstance(row, dict), f"{path}:{line_number}: expected object")
            rows.append(row)
    return rows


def canonical_label(value: Any, field: str = "label") -> str:
    require(isinstance(value, str), f"{field} is not a string")
    label = re.sub(r"\s+", " ", value).strip().lower()
    require(0 < len(label) <= LABEL_MAX_CHARS, f"{field} length")
    require(bool(re.fullmatch(r"[a-z][a-z0-9 -]*", label)), f"{field} characters")
    require(";" not in label, f"{field} folded delimiter")
    return label


def semantic_id(label: str) -> str:
    canonical = canonical_label(label)
    return "op-" + sha256_bytes(canonical.encode())[:24]


def label_rule() -> str:
    return f'"\\\"" [a-z] [a-z0-9 -]{{0,{LABEL_MAX_CHARS - 1}}} "\\\""'


def root_grammar() -> str:
    return (
        'root ::= "{\\\"operation\\\":" label "}"\n'
        + "label ::= "
        + label_rule()
        + "\n"
    )


def split_grammar(valid_turn_ids: list[str]) -> str:
    require(bool(valid_turn_ids), "split grammar needs an interior boundary")
    require(len(set(valid_turn_ids)) == len(valid_turn_ids), "duplicate split IDs")
    choices = " | ".join(json.dumps(value) for value in valid_turn_ids)
    return (
        'root ::= stop | split\n'
        'stop ::= "{\\\"decision\\\":\\\"stop\\\"}"\n'
        'split ::= "{\\\"decision\\\":\\\"split\\\",\\\"split_before\\\":" boundary '
        '",\\\"left\\\":" label ",\\\"right\\\":" label "}"\n'
        f"boundary ::= {choices}\n"
        f"label ::= {label_rule()}\n"
    )


def parse_root(raw: str) -> str:
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as error:
        raise RuntimeError(f"root output is not JSON: {raw[:200]!r}") from error
    require(isinstance(value, dict) and set(value) == {"operation"}, "root output keys")
    return canonical_label(value["operation"], "root operation")


def parse_decision(raw: str, valid_turn_ids: list[str], ancestors: list[str]) -> dict[str, str]:
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as error:
        raise RuntimeError(f"split output is not JSON: {raw[:200]!r}") from error
    require(isinstance(value, dict), "split output object")
    decision = value.get("decision")
    if decision == "stop":
        require(set(value) == {"decision"}, "STOP output keys")
        return {"decision": "stop"}
    require(decision == "split", "unknown split decision")
    require(
        set(value) == {"decision", "split_before", "left", "right"},
        "SPLIT output keys",
    )
    split_before = str(value["split_before"])
    require(split_before in valid_turn_ids, "split boundary outside interval")
    left = canonical_label(value["left"], "left operation")
    right = canonical_label(value["right"], "right operation")
    require(left != right, "child operations collide")
    forbidden = set(ancestors)
    require(left not in forbidden and right not in forbidden, "child operation equals ancestor")
    return {"decision": "split", "split_before": split_before, "left": left, "right": right}


def server_properties(llama_url: str, timeout_seconds: int) -> dict[str, Any]:
    response = requests.get(llama_url.rstrip("/") + "/props", timeout=timeout_seconds)
    response.raise_for_status()
    payload = response.json()
    defaults = payload["default_generation_settings"]
    return {
        "slots": int(payload["total_slots"]),
        "context_tokens": int(defaults["n_ctx"]),
        "model_path": str(payload["model_path"]),
        "model_alias": str(payload["model_alias"]),
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


def call_model(
    llama_url: str,
    model_name: str,
    system: str,
    prompt: str,
    grammar: str,
    timeout_seconds: int,
) -> tuple[str, dict[str, Any], float]:
    started = time.monotonic()
    response = requests.post(
        llama_url.rstrip("/") + "/v1/chat/completions",
        json={
            "model": model_name,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0,
            "seed": SEED,
            "max_tokens": OUTPUT_TOKENS,
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


def request_hash(system: str, prompt: str, grammar: str, model_sha256: str) -> str:
    contract = {
        "algorithm": ALGORITHM_VERSION,
        "model_sha256": model_sha256,
        "seed": SEED,
        "temperature": 0,
        "system": system,
        "prompt": prompt,
        "grammar": grammar,
    }
    return sha256_bytes(
        json.dumps(contract, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    )


def projected_turn(turn: dict[str, Any]) -> dict[str, Any]:
    visible = global_eval.visible_turn(turn)
    visible["turn_id"] = str(turn["operations"][0]["step"])
    return visible


def root_prompt(task: str) -> str:
    return "TARGET-BLIND PUBLIC TASK TEXT\n" + task


def interval_prompt(
    task: str,
    ancestors: list[str],
    current: str,
    turns: list[dict[str, Any]],
) -> str:
    return (
        "TARGET-BLIND PUBLIC TASK TEXT\n"
        + task
        + "\n\nACTIVE SEMANTIC PATH\n"
        + json.dumps([*ancestors, current], ensure_ascii=False, separators=(",", ":"))
        + "\n\nCOMPLETE CONTIGUOUS TURN INTERVAL\n"
        + json.dumps(turns, ensure_ascii=False, separators=(",", ":"))
    )


DecisionFunction = Callable[[int, int, list[str], str], dict[str, str]]


def decompose_turns(
    turns: list[dict[str, Any]],
    root: str,
    decide: DecisionFunction,
) -> list[dict[str, Any]]:
    require(bool(turns), "empty turn sequence")
    leaves: list[dict[str, Any]] = []

    def visit(start: int, end: int, ancestors: list[str], current: str) -> None:
        require(0 <= start < end <= len(turns), "invalid recursive interval")
        if end - start == 1:
            leaves.append({"start": start, "end": end, "labels": [*ancestors, current]})
            return
        decision = decide(start, end, ancestors, current)
        if decision["decision"] == "stop":
            leaves.append({"start": start, "end": end, "labels": [*ancestors, current]})
            return
        valid = {
            str(turns[index]["turn_id"]): index for index in range(start + 1, end)
        }
        split_before = decision["split_before"]
        require(split_before in valid, "decision did not strictly shrink interval")
        boundary = valid[split_before]
        path = [*ancestors, current]
        left = canonical_label(decision["left"], "left operation")
        right = canonical_label(decision["right"], "right operation")
        require(left != right, "recursive child collision")
        require(left not in path and right not in path, "recursive child equals ancestor")
        visit(start, boundary, path, left)
        visit(boundary, end, path, right)

    visit(0, len(turns), [], canonical_label(root, "root operation"))
    require(leaves[0]["start"] == 0 and leaves[-1]["end"] == len(turns), "leaf coverage ends")
    for left, right in zip(leaves, leaves[1:]):
        require(left["end"] == right["start"], "leaf coverage gap")
    return leaves


def cache_name(session: str) -> str:
    return sha256_bytes(session.encode())[:24] + ".json"


def prepare_material(raw_root: Path, session: str, rows: list[dict[str, Any]]) -> dict[str, Any]:
    material = source.reconstruct_source(raw_root, session, rows)
    turns = stateful.group_turns(material["operations"])
    projected = [projected_turn(turn) for turn in turns]
    require(len({turn["turn_id"] for turn in projected}) == len(projected), "turn IDs unique")
    return {"material": material, "turns": turns, "projected_turns": projected}


def material_contract(prepared: dict[str, Any], model_sha256: str) -> dict[str, Any]:
    material = prepared["material"]
    return {
        "algorithm_version": ALGORITHM_VERSION,
        "session": material["session"],
        "archive_sha256": material["archive_sha256"],
        "task_sha256": sha256_bytes(str(material["task"]).encode()),
        "projected_turns_sha256": sha256_bytes(
            json.dumps(
                prepared["projected_turns"],
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ).encode()
        ),
        "model_sha256": model_sha256,
        "inference_contract_sha256": inference_contract_hash(),
    }


def inference_contract_hash() -> str:
    contract = {
        "algorithm_version": ALGORITHM_VERSION,
        "seed": SEED,
        "output_tokens": OUTPUT_TOKENS,
        "context_margin": CONTEXT_MARGIN,
        "label_max_chars": LABEL_MAX_CHARS,
        "root_system": ROOT_SYSTEM,
        "split_system": SPLIT_SYSTEM,
        "root_grammar": root_grammar(),
        "split_grammar_shape": split_grammar(["example-2", "example-17"]),
        "root_prompt_source": inspect.getsource(root_prompt),
        "interval_prompt_source": inspect.getsource(interval_prompt),
        "projected_turn_source": inspect.getsource(projected_turn),
        "projection_chars": {
            "intent": global_eval.INTENT_CHARS,
            "progress": global_eval.PROGRESS_CHARS,
            "action": global_eval.ACTION_CHARS,
            "result": global_eval.RESULT_CHARS,
        },
    }
    return sha256_bytes(
        json.dumps(contract, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    )


def infer_session(
    prepared: dict[str, Any],
    llama_url: str,
    model_name: str,
    model_sha256: str,
    timeout_seconds: int,
    context_tokens: int,
    cache_dir: Path,
) -> dict[str, Any]:
    material = prepared["material"]
    session = str(material["session"])
    contract = material_contract(prepared, model_sha256)
    cache_path = cache_dir / cache_name(session)
    if cache_path.is_file():
        cached = json.loads(cache_path.read_text(encoding="utf-8"))
        require(cached.get("contract") == contract, f"{session}: stale session cache")
        require(cached.get("status") == "complete", f"{session}: incomplete session cache")
        return cached

    task = str(material["task"])
    r_prompt = root_prompt(task)
    r_grammar = root_grammar()
    root_tokens = token_count(llama_url, ROOT_SYSTEM + "\n" + r_prompt, timeout_seconds)
    require(root_tokens + OUTPUT_TOKENS + CONTEXT_MARGIN <= context_tokens, f"{session}: root context overflow")
    raw_root, root_payload, root_elapsed = call_model(
        llama_url, model_name, ROOT_SYSTEM, r_prompt, r_grammar, timeout_seconds
    )
    root = parse_root(raw_root)
    calls: list[dict[str, Any]] = [
        {
            "kind": "root",
            "start": 0,
            "end": len(prepared["projected_turns"]),
            "request_hash": request_hash(ROOT_SYSTEM, r_prompt, r_grammar, model_sha256),
            "prompt_tokens": root_tokens,
            "response": raw_root,
            "usage": root_payload.get("usage", {}),
            "elapsed_seconds": root_elapsed,
        }
    ]

    projected = prepared["projected_turns"]

    def decide(start: int, end: int, ancestors: list[str], current: str) -> dict[str, str]:
        valid_ids = [str(projected[index]["turn_id"]) for index in range(start + 1, end)]
        grammar = split_grammar(valid_ids)
        prompt = interval_prompt(task, ancestors, current, projected[start:end])
        tokens = token_count(llama_url, SPLIT_SYSTEM + "\n" + prompt, timeout_seconds)
        require(tokens + OUTPUT_TOKENS + CONTEXT_MARGIN <= context_tokens, f"{session}: interval context overflow {start}:{end}")
        raw, payload, elapsed = call_model(
            llama_url, model_name, SPLIT_SYSTEM, prompt, grammar, timeout_seconds
        )
        decision = parse_decision(raw, valid_ids, [*ancestors, current])
        calls.append(
            {
                "kind": "recursive",
                "start": start,
                "end": end,
                "active_path": [*ancestors, current],
                "valid_split_before": valid_ids,
                "request_hash": request_hash(SPLIT_SYSTEM, prompt, grammar, model_sha256),
                "prompt_tokens": tokens,
                "response": raw,
                "decision": decision,
                "usage": payload.get("usage", {}),
                "elapsed_seconds": elapsed,
            }
        )
        return decision

    leaves = decompose_turns(projected, root, decide)
    result = {
        "schema": SCHEMA + ".session.v1",
        "status": "complete",
        "contract": contract,
        "session": session,
        "framework": material["framework"],
        "adapter": material["adapter"],
        "archive": material["archive"],
        "task_source": material["task_source"],
        "root_operation": root,
        "turns": len(projected),
        "operations": len(material["operations"]),
        "leaves": leaves,
        "calls": calls,
    }
    write_json_atomic(cache_path, result)
    return result


def build_outputs(
    prepared: dict[str, dict[str, Any]],
    results: dict[str, dict[str, Any]],
    selected: list[str],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    predictions: list[dict[str, Any]] = []
    operation_names: dict[str, str] = {}
    marks: list[dict[str, Any]] = []
    display_to_id: dict[str, str] = {}
    for session in selected:
        material = prepared[session]["material"]
        turns = prepared[session]["turns"]
        leaves = results[session]["leaves"]
        for leaf_number, leaf in enumerate(leaves):
            labels = [canonical_label(value) for value in leaf["labels"]]
            operation_ids = []
            for label in labels:
                operation_id = semantic_id(label)
                previous = operation_names.setdefault(operation_id, label)
                require(previous == label, "semantic operation hash collision")
                previous_id = display_to_id.setdefault(label, operation_id)
                require(previous_id == operation_id, "semantic display-name collision")
                operation_ids.append(operation_id)
            first_turn = turns[int(leaf["start"])]
            first_operation = first_turn["operations"][0]
            marks.append(
                {
                    "sequence": session,
                    "start_operation_id": str(first_operation["step"]),
                    "operation_ids": operation_ids,
                }
            )
            for turn_index in range(int(leaf["start"]), int(leaf["end"])):
                turn = turns[turn_index]
                for operation in turn["operations"]:
                    predictions.append(
                        {
                            "session": session,
                            "framework": material["framework"],
                            "step_id": int(operation["step"]),
                            "turn_index": turn_index,
                            "source_turn_id": turn["source_turn_id"],
                            "source_ref": operation["source_ref"],
                            "leaf_number": leaf_number,
                            "leaf_start_turn": int(leaf["start"]),
                            "leaf_end_turn": int(leaf["end"]),
                            "operation_ids": operation_ids,
                            "semantic_stack": [
                                {"operation_id": operation_id, "label": label}
                                for operation_id, label in zip(operation_ids, labels, strict=True)
                            ],
                            "task_occurrence_instance": session + ":" + "/".join(operation_ids),
                        }
                    )
    predictions.sort(key=lambda row: (row["session"], row["step_id"]))
    marks.sort(key=lambda row: (row["sequence"], int(row["start_operation_id"])))
    return predictions, {
        "sequence_field": "traj_id",
        "id_field": "step_id",
        "operation_names": dict(sorted(operation_names.items())),
        "marks": marks,
    }


def filter_target_rows(
    target_rows: list[dict[str, Any]], selected: set[str]
) -> list[dict[str, Any]]:
    return [row for row in target_rows if str(row["fields"]["traj_id"]) in selected]


def filter_mark_file(mark_file: dict[str, Any], selected: set[str]) -> dict[str, Any]:
    marks = [row for row in mark_file["marks"] if row["sequence"] in selected]
    used = {operation_id for row in marks for operation_id in row["operation_ids"]}
    return {
        "sequence_field": mark_file["sequence_field"],
        "id_field": mark_file["id_field"],
        "operation_names": {
            key: value for key, value in mark_file["operation_names"].items() if key in used
        },
        "marks": marks,
    }


def run_agentpprof(
    manifest: Path,
    operations: Path,
    marks: Path,
    output: Path,
    expected_operations: int,
    expected_sessions: int,
    expected_marks: int,
) -> dict[str, Any]:
    operation_rows = read_jsonl(operations)
    mark_payload = json.loads(marks.read_text(encoding="utf-8"))
    sequence_field = str(mark_payload.get("sequence_field") or "")
    require(bool(sequence_field), "pprof mark sequence field")

    def operation_fields(row: dict[str, Any]) -> dict[str, Any]:
        nested = row.get("fields")
        return nested if isinstance(nested, dict) else row

    require(len(operation_rows) == expected_operations, "pprof input operation count")
    require(
        len({str(operation_fields(row)[sequence_field]) for row in operation_rows})
        == expected_sessions,
        "pprof input session count",
    )
    mark_rows = mark_payload.get("marks")
    require(isinstance(mark_rows, list) and len(mark_rows) == expected_marks, "pprof input mark count")
    require(
        len({str(row["sequence"]) for row in mark_rows}) == expected_sessions,
        "pprof mark session count",
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    command = [
        "cargo",
        "run",
        "--quiet",
        "--manifest-path",
        str(manifest),
        "--",
        "--operation-file",
        str(operations),
        "--operation-mark-file",
        str(marks),
        "--view",
        "operations",
        "--deterministic-output",
        "--output",
        str(output),
    ]
    result = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, check=True)
    try:
        report = json.loads(result.stdout)
    except json.JSONDecodeError as error:
        raise RuntimeError("AgentPProf stdout is not one JSON result") from error
    require(isinstance(report, dict), "AgentPProf report object")
    require(report.get("status") == "ok", "AgentPProf status")
    require(report.get("format") == "pprof", "AgentPProf output format")
    require(report.get("view") == "operations", "AgentPProf output view")
    require(report.get("operations") == expected_operations, "AgentPProf operation count")
    require(report.get("samples") == expected_operations, "AgentPProf sample mass")
    require(report.get("warnings") == [], "AgentPProf warnings")
    require(int(report.get("unique_stacks") or 0) > 0, "AgentPProf unique stacks")
    require(output.is_file() and output.stat().st_size > 0, "AgentPProf emitted no profile")
    top = subprocess.run(
        ["go", "tool", "pprof", "-top", str(output)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )
    return {
        "command": command,
        "report": report,
        "stderr": result.stderr.strip(),
        "path": relative(output),
        "bytes": output.stat().st_size,
        "sha256": sha256_file(output),
        "pprof_top": top.stdout,
    }


def select_preflight(prepared: dict[str, dict[str, Any]]) -> list[str]:
    by_framework: dict[str, list[str]] = defaultdict(list)
    for session, item in prepared.items():
        by_framework[str(item["material"]["framework"])].append(session)
    require(set(by_framework) == EXPECTED_FRAMEWORKS, "preflight framework coverage")
    return sorted(
        max(
            sessions,
            key=lambda session: (
                int(prepared[session]["projected_prompt_tokens"]),
                session,
            ),
        )
        for sessions in by_framework.values()
    )


def long_horizon_sessions(grouped: dict[str, list[dict[str, Any]]]) -> list[str]:
    require(len(grouped) == EXPECTED_SESSIONS, "long-horizon source population")
    selected = sorted(grouped, key=lambda session: (-len(grouped[session]), session))[
        :LONG_HORIZON_SESSIONS
    ]
    require(len(selected) == LONG_HORIZON_SESSIONS, "long-horizon collection count")
    require(sum(len(grouped[session]) for session in selected) == LONG_HORIZON_OPERATIONS, "long-horizon operation count")
    return selected


def run_infer(args: argparse.Namespace) -> None:
    started = time.monotonic()
    target_path = absolute(args.target_operations)
    raw_root = absolute(args.raw_root)
    model_path = absolute(args.model_path)
    manifest = absolute(args.agentpprof_manifest)
    out_dir = absolute(args.out)
    for path in (target_path, model_path, manifest):
        require(path.is_file(), f"missing inference input: {path}")
    require(raw_root.is_dir(), f"missing raw root: {raw_root}")
    require(sha256_file(model_path) == args.model_sha256, "model SHA-256 mismatch")
    props = server_properties(args.llama_url, args.timeout_seconds)
    require(props["slots"] == 1, "recursive experiment requires one llama slot")
    require(
        Path(props["model_path"]).resolve() == model_path.resolve(),
        "llama server model path mismatch",
    )

    grouped = base.load_visible_operations(target_path)
    require(len(grouped) == EXPECTED_SESSIONS, "CodeTrace session count")
    require(sum(len(rows) for rows in grouped.values()) == EXPECTED_OPERATIONS, "CodeTrace operation count")
    prepared: dict[str, dict[str, Any]] = {}
    for number, session in enumerate(sorted(grouped), 1):
        item = prepare_material(raw_root, session, grouped[session])
        full_prompt = interval_prompt(
            str(item["material"]["task"]),
            [],
            "placeholder root operation",
            item["projected_turns"],
        )
        item["projected_prompt_tokens"] = token_count(
            args.llama_url, SPLIT_SYSTEM + "\n" + full_prompt, args.timeout_seconds
        )
        prepared[session] = item
        if number % 50 == 0 or number == len(grouped):
            print(f"prepared {number}/{len(grouped)}", flush=True)
    selected = select_preflight(prepared) if args.mode == "preflight" else sorted(grouped)

    cache_dir = out_dir / "sessions"
    results: dict[str, dict[str, Any]] = {}
    for number, session in enumerate(selected, 1):
        results[session] = infer_session(
            prepared[session],
            args.llama_url,
            args.model_name,
            args.model_sha256,
            args.timeout_seconds,
            int(props["context_tokens"]),
            cache_dir,
        )
        print(
            f"inferred {number}/{len(selected)} {session} "
            f"leaves={len(results[session]['leaves'])}",
            flush=True,
        )

    predictions, mark_file = build_outputs(prepared, results, selected)
    expected_operations = sum(len(grouped[session]) for session in selected)
    expected_turns = sum(len(prepared[session]["turns"]) for session in selected)
    require(len(predictions) == expected_operations, "prediction operation coverage")
    require(
        len({(row["session"], row["step_id"]) for row in predictions}) == expected_operations,
        "prediction key coverage",
    )
    target_rows = read_jsonl(target_path)
    selected_rows = filter_target_rows(target_rows, set(selected))
    require(len(selected_rows) == expected_operations, "selected target coverage")
    out_dir.mkdir(parents=True, exist_ok=True)
    prediction_path = out_dir / "predictions.jsonl"
    mark_path = out_dir / "operation-marks.json"
    operation_path = out_dir / "selected-operations.jsonl"
    write_jsonl(prediction_path, predictions)
    write_json(mark_path, mark_file)
    write_jsonl(operation_path, selected_rows)
    profile = run_agentpprof(
        manifest,
        operation_path,
        mark_path,
        out_dir / ("complete-population.operations.pb.gz" if args.mode == "full" else "preflight.operations.pb.gz"),
        expected_operations,
        len(selected),
        len(mark_file["marks"]),
    )

    long_horizon: dict[str, Any] | None = None
    if args.mode == "full":
        long_sessions = long_horizon_sessions(grouped)
        long_set = set(long_sessions)
        long_operations = out_dir / "long-horizon-operations.jsonl"
        long_marks = out_dir / "long-horizon-marks.json"
        write_jsonl(long_operations, filter_target_rows(target_rows, long_set))
        write_json(long_marks, filter_mark_file(mark_file, long_set))
        long_profile = run_agentpprof(
            manifest,
            long_operations,
            long_marks,
            out_dir / "long-horizon.operations.pb.gz",
            LONG_HORIZON_OPERATIONS,
            LONG_HORIZON_SESSIONS,
            len(filter_mark_file(mark_file, long_set)["marks"]),
        )
        long_horizon = {
            "selection": "top decile by descending source-visible operation count; trajectory ID tie-break",
            "sessions": long_sessions,
            "session_count": len(long_sessions),
            "operation_count": sum(len(grouped[session]) for session in long_sessions),
            "minimum_operations_per_session": min(len(grouped[session]) for session in long_sessions),
            "frameworks": dict(Counter(prepared[session]["material"]["framework"] for session in long_sessions)),
            "profile": long_profile,
        }

    leaves = [leaf for session in selected for leaf in results[session]["leaves"]]
    calls = [call for session in selected for call in results[session]["calls"]]
    depths = [len(leaf["labels"]) for leaf in leaves]
    leaf_lengths = [int(leaf["end"]) - int(leaf["start"]) for leaf in leaves]
    split_calls = [call for call in calls if call.get("decision", {}).get("decision") == "split"]
    stop_calls = [call for call in calls if call.get("decision", {}).get("decision") == "stop"]
    usage: Counter[str] = Counter()
    for call in calls:
        for key, value in (call.get("usage") or {}).items():
            if isinstance(value, int):
                usage[key] += value
    summary = {
        "schema": SCHEMA + ".inference.v1",
        "algorithm_version": ALGORITHM_VERSION,
        "mode": args.mode,
        "status": "complete",
        "model": args.model_name,
        "model_sha256": args.model_sha256,
        "seed": SEED,
        "server": props,
        "sessions": len(selected),
        "turns": expected_turns,
        "operations": expected_operations,
        "frameworks": dict(Counter(results[session]["framework"] for session in selected)),
        "public_task_text_sources": dict(
            Counter(
                "openhands_public_recall_query"
                if str(prepared[session]["material"]["task_source"]).endswith("#recall-query")
                else "raw_first_user_message"
                for session in selected
            )
        ),
        "selected_sessions": selected,
        "recursive_calls": len(calls) - len(selected),
        "root_calls": len(selected),
        "split_calls": len(split_calls),
        "stop_calls": len(stop_calls),
        "sessions_with_internal_split": sum(len(results[session]["leaves"]) > 1 for session in selected),
        "leaves": {
            "total": len(leaves),
            "minimum_per_session": min(len(results[session]["leaves"]) for session in selected),
            "maximum_per_session": max(len(results[session]["leaves"]) for session in selected),
            "turn_length_counts": dict(sorted(Counter(leaf_lengths).items())),
        },
        "semantic_depth": {
            "minimum": min(depths),
            "maximum": max(depths),
            "counts": dict(sorted(Counter(depths).items())),
        },
        "model_usage": dict(usage),
        "profile": profile,
        "long_horizon": long_horizon,
        "predictions": relative(prediction_path),
        "operation_marks": relative(mark_path),
        "wall_seconds": time.monotonic() - started,
        "isolation": {
            "official_manifest_opened": False,
            "official_stages_opened": False,
            "visible_fields": [
                "target-blind public task text (raw first-user message when present; public OpenHands recall query otherwise)",
                "fixed projected native intent",
                "native progress",
                "planned source action",
                "visible source result",
            ],
            "future_source_context_visible": True,
            "session_slug_or_manifest_task_visible_to_model": False,
            "same_turn_operations_preserved": True,
            "post_hoc_contraction": False,
            "configured_depth_or_leaf_cap": False,
        },
    }
    if args.mode == "full":
        require(len(selected) == EXPECTED_SESSIONS, "full session coverage")
        require(expected_turns == EXPECTED_TURNS, "full turn coverage")
        require(expected_operations == EXPECTED_OPERATIONS, "full operation coverage")
    write_json(out_dir / "inference-summary.json", summary)
    print(json.dumps(summary, sort_keys=True), flush=True)


def load_predictions(path: Path) -> dict[tuple[str, int], dict[str, Any]]:
    rows: dict[tuple[str, int], dict[str, Any]] = {}
    for line_number, row in enumerate(read_jsonl(path), 1):
        key = (str(row["session"]), int(row["step_id"]))
        require(key not in rows, f"duplicate prediction {line_number}")
        require(isinstance(row.get("semantic_stack"), list), "missing semantic stack")
        rows[key] = row
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
                "candidate": str(prediction["task_occurrence_instance"]),
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
    pairs: list[dict[str, Any]],
    operations: list[dict[str, Any]],
    methods: Iterable[str],
) -> dict[str, Any]:
    return {
        method: {
            "bcubed": base.bcubed(operations, method),
            "boundary": base.boundary_metrics(pairs, method),
        }
        for method in methods
    }


def result_report(summary: dict[str, Any]) -> str:
    lines = [
        "# Recursive Operation Segmentation — Result",
        "",
        f"- mode: {summary['mode']}",
        f"- status: {summary['status']}",
        f"- registered interpretation: **{summary['registered_interpretation']}**",
        "",
        "## Standard metrics",
        "",
        "| Method | B³ P | B³ R | B³ F1 | Boundary P | Boundary R | Boundary F1 |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for method, values in summary["metrics"].items():
        lines.append(
            f"| {method} | {values['bcubed']['precision']:.6f} | "
            f"{values['bcubed']['recall']:.6f} | {values['bcubed']['f1']:.6f} | "
            f"{values['boundary']['precision']:.6f} | {values['boundary']['recall']:.6f} | "
            f"{values['boundary']['f1']:.6f} |"
        )
    interval = summary["bootstrap"]["candidate_minus_multires"]["ci95"]
    lines.extend(
        [
            "",
            "## Registered comparison",
            "",
            "Candidate minus multi-resolution recurrence paired task-cluster 95% "
            f"interval: `[{interval[0]:+.6f}, {interval[1]:+.6f}]`.",
            "",
            "## Interpretation boundary",
            "",
            summary["claim_boundary"],
            "",
        ]
    )
    return "\n".join(lines)


def run_score(args: argparse.Namespace) -> None:
    target_path = absolute(args.target_operations)
    prediction_path = absolute(args.predictions)
    inference_path = absolute(args.inference_summary)
    manifest_path = absolute(args.verified_manifest)
    baseline_path = absolute(args.multires_assignments)
    causal_path = absolute(args.causal_score_rows)
    out_dir = absolute(args.out)
    for path in (
        target_path,
        prediction_path,
        inference_path,
        manifest_path,
        baseline_path,
        causal_path,
    ):
        require(path.is_file(), f"missing score input: {path}")
    inference = json.loads(inference_path.read_text(encoding="utf-8"))
    require(inference.get("status") == "complete", "inference incomplete")
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
    causal = global_eval.load_causal(causal_path)
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
    mode = str(inference["mode"])
    interpretation = (
        "diagnostic-preflight"
        if mode == "preflight"
        else "supported-pending-semantic-review"
        if supported
        else "contradicted-not-adopted"
        if contradicted
        else "mixed-pending-semantic-review"
    )
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
            "secondary_metric": "exact adjacent-boundary precision, recall, and F1",
            "incumbent": "multires_recurrence",
            "candidate_point_higher": candidate_f1 > incumbent_f1,
            "candidate_interval_wholly_positive": candidate_minus_multires["ci95"][0] > 0,
            "candidate_interval_wholly_nonpositive": contradicted,
            "semantic_review_pending": mode == "full",
        },
        "claim_boundary": (
            "Official flat stages score only the leaf partition induced by complete visible "
            "operation paths. Nested topology, semantic names, cross-session equivalence, and "
            "user utility require the separately predeclared aggregate pprof review."
        ),
    }
    if mode == "full":
        require(len(selected) == EXPECTED_SESSIONS, "full scored sessions")
        require(len(operations) == EXPECTED_OPERATIONS, "full scored operations")
        require(len(set(official.values())) == EXPECTED_STAGES, "full official stages")
        require(len(set(tasks.values())) == EXPECTED_TASKS, "full task clusters")
    write_jsonl(out_dir / "operation-score-rows.jsonl", operations)
    write_jsonl(out_dir / "pair-score-rows.jsonl", pairs)
    write_json(out_dir / "summary.json", summary)
    (out_dir / "result-report.md").write_text(result_report(summary), encoding="utf-8")
    print(json.dumps(summary, sort_keys=True), flush=True)


def main() -> None:
    args = parse_args()
    if args.command == "infer":
        run_infer(args)
    else:
        require(args.command == "score", "unknown command")
        run_score(args)


if __name__ == "__main__":
    main()
