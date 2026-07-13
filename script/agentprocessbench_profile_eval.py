#!/usr/bin/env python3
"""AgentProcessBench RQ2 semantic-profile localization experiment.

The experiment consumes the official 1,000-trajectory benchmark and the 20
released blind judge outputs. Human labels are used only by the scorer. Real
AgentProf builds the flat, session, raw-action, and semantic grouped views.
"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import gzip
import json
import math
import multiprocessing as mp
import os
from pathlib import Path
import subprocess
import sys
from typing import Any, Iterable, Sequence

import numpy as np


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(REPO_ROOT / "agentpprof" / "backend" / "python"))

from agent_trace_datasets import repeat_features_for_signatures, sanitize_label  # noqa: E402
from cluster_tagger import cluster_prompts, hash_prompt  # noqa: E402


FAMILIES = ("bfcl", "gaia_dev", "hotpotqa", "tau2")
EXPECTED_TRAJECTORIES_PER_FAMILY = 250
EXPECTED_TASKS_PER_FAMILY = 50
EXPECTED_TRAJECTORIES = 1_000
EXPECTED_TASKS = 200
EXPECTED_OPERATIONS = 8_509
EXPECTED_MODELS = 20
EXPECTED_ALL_NULL = 3
AGENTPROF_VERSION = "agentpprof 0.2.37"
RISK_SCALE = math.lcm(*range(1, EXPECTED_MODELS + 1))

PROFILE_FIELDS: dict[str, tuple[str, ...]] = {
    "flat": ("flat",),
    "session": ("session",),
    "raw_action": ("action", "target", "repeat_state"),
    "semantic": ("intent", "phase", "action", "target", "repeat_state"),
    "ungrouped_risk": ("operation_id",),
}
ALL_VIEWS = tuple(PROFILE_FIELDS)
SAFE_STACK_VALUE = frozenset(
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._:/+-"
)


class ExperimentError(RuntimeError):
    """Raised when the approved experiment contract is not satisfied."""


def iter_jsonl(path: Path) -> Iterable[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as source:
        for line_number, line in enumerate(source, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as error:
                raise ExperimentError(f"{path}:{line_number}: {error}") from error
            if not isinstance(row, dict):
                raise ExperimentError(f"{path}:{line_number}: expected object")
            yield row


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ExperimentError(f"{path}: expected JSON object")
    return value


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as output:
        for row in rows:
            output.write(json.dumps(row, sort_keys=True, ensure_ascii=False))
            output.write("\n")


def safe_stack_value(value: Any) -> str:
    text = str(value)
    if not text or any(character not in SAFE_STACK_VALUE for character in text):
        raise ExperimentError(f"unsafe AgentProf stack value {text!r}")
    return text


def agentprof_frame_value(value: Any) -> str:
    """Mirror AgentProf safe-frame encoding for pre-sanitized fields."""
    text = safe_stack_value(value)
    output = ""
    for character in text.lower():
        if character.isascii() and (
            character.isalnum() or character in "._:/+-"
        ):
            output += character
        elif not output.endswith("_"):
            output += "_"
    return output.strip("_;") or "unknown"


def method_key(row: dict[str, Any], method: str) -> str:
    return ";".join(
        f"{field}:{agentprof_frame_value(row[field])}"
        for field in PROFILE_FIELDS[method]
    )


def operation_id(family: str, query_index: int, sample_index: int, message_index: str | int) -> str:
    return f"{family}:{query_index}:{sample_index}:{message_index}"


def trajectory_id(family: str, query_index: int, sample_index: int) -> str:
    return f"{family}:{query_index}:{sample_index}"


def task_id(family: str, query_index: int) -> str:
    return f"{family}:{query_index}"


def message_action_target(message: dict[str, Any], final_assistant: bool) -> tuple[str, str]:
    calls = message.get("tool_calls")
    if calls is None:
        calls = []
    if not isinstance(calls, list):
        raise ExperimentError("assistant tool_calls must be a list")
    if calls:
        names: list[str] = []
        for call in calls:
            if not isinstance(call, dict):
                raise ExperimentError("tool call must be an object")
            function = call.get("function")
            name: Any = None
            if isinstance(function, dict):
                name = function.get("name")
            if name is None:
                name = call.get("name")
            names.append(sanitize_label(str(name or "unknown")))
        return "tool_call", "+".join(sorted(set(names))) or "unknown"
    if final_assistant:
        return "final_answer", "final"
    return "reasoning", "user"


def phase_for_ordinal(
    ordinal: int, tool_ordinals: Sequence[int]
) -> str:
    if not tool_ordinals:
        return "no_tool"
    if ordinal < tool_ordinals[0]:
        return "open"
    if ordinal <= tool_ordinals[-1]:
        return "work"
    return "close"


def _official_data_dir(source: Path) -> Path:
    path = source / "data" / "AgentProcessBench"
    if not path.is_dir():
        raise ExperimentError(f"missing official data directory: {path}")
    return path


def _source_commit(source: Path) -> str:
    completed = subprocess.run(
        ["git", "-C", str(source), "rev-parse", "HEAD"],
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return completed.stdout.strip()


def load_source(
    source: Path, query_limit: int | None
) -> tuple[list[dict[str, Any]], set[str], dict[str, Any]]:
    """Load visible operations without accessing human-label values."""
    data_dir = _official_data_dir(source)
    records: dict[str, list[dict[str, Any]]] = {}
    task_prompts: dict[str, str] = {}
    trajectory_keys: set[str] = set()

    for family in FAMILIES:
        path = data_dir / f"{family}.jsonl"
        rows = list(iter_jsonl(path))
        if len(rows) != EXPECTED_TRAJECTORIES_PER_FAMILY:
            raise ExperimentError(
                f"{family}: expected {EXPECTED_TRAJECTORIES_PER_FAMILY} trajectories, got {len(rows)}"
            )
        records[family] = rows
        for row in rows:
            query = int(row["query_index"])
            sample = int(row["sample_index"])
            trajectory = trajectory_id(family, query, sample)
            if trajectory in trajectory_keys:
                raise ExperimentError(f"duplicate trajectory {trajectory}")
            trajectory_keys.add(trajectory)
            key = task_id(family, query)
            prompt = str(row.get("question") or row.get("task_description") or "").strip()
            if not prompt:
                raise ExperimentError(f"{key}: missing task description")
            previous = task_prompts.setdefault(key, prompt)
            if previous != prompt:
                raise ExperimentError(f"{key}: rollout prompts differ")

    if len(trajectory_keys) != EXPECTED_TRAJECTORIES:
        raise ExperimentError(f"expected {EXPECTED_TRAJECTORIES} trajectories")
    if len(task_prompts) != EXPECTED_TASKS:
        raise ExperimentError(f"expected {EXPECTED_TASKS} unique tasks")
    for family in FAMILIES:
        tasks = {int(row["query_index"]) for row in records[family]}
        samples = {int(row["sample_index"]) for row in records[family]}
        if len(tasks) != EXPECTED_TASKS_PER_FAMILY or samples != set(range(5)):
            raise ExperimentError(f"{family}: unexpected task/sample population")

    ordered_tasks = sorted(task_prompts)
    prompts = [task_prompts[key] for key in ordered_tasks]
    tag_map, cluster_info = cluster_prompts(prompts)
    intent_by_task: dict[str, str] = {}
    for key, prompt in zip(ordered_tasks, prompts, strict=True):
        tag = tag_map.get(hash_prompt(prompt))
        if not tag:
            raise ExperimentError(f"{key}: prompt tagger emitted no intent")
        intent_by_task[key] = sanitize_label(tag)

    visible: list[dict[str, Any]] = []
    full_operation_ids: set[str] = set()
    family_operation_counts: Counter[str] = Counter()

    for family in FAMILIES:
        for record in records[family]:
            query = int(record["query_index"])
            sample = int(record["sample_index"])
            messages = record.get("messages")
            if not isinstance(messages, list):
                raise ExperimentError(f"{family}:{query}:{sample}: missing messages")
            assistant = [
                (index, message)
                for index, message in enumerate(messages)
                if isinstance(message, dict) and message.get("role") == "assistant"
            ]
            if not assistant:
                raise ExperimentError(f"{family}:{query}:{sample}: no assistant steps")
            official_labels = record.get("step_labels")
            if not isinstance(official_labels, dict):
                raise ExperimentError(f"{family}:{query}:{sample}: missing step labels")
            assistant_keys = {str(index) for index, _ in assistant}
            if assistant_keys != set(map(str, official_labels)):
                raise ExperimentError(
                    f"{family}:{query}:{sample}: assistant/label keys differ"
                )

            parsed: list[tuple[int, int, dict[str, Any], str, str]] = []
            tool_ordinals: list[int] = []
            signatures: list[tuple[str, str]] = []
            for ordinal, (message_index, message) in enumerate(assistant):
                action, target = message_action_target(
                    message, final_assistant=ordinal == len(assistant) - 1
                )
                if action == "tool_call":
                    tool_ordinals.append(ordinal)
                signatures.append((action, target))
                parsed.append((ordinal, message_index, message, action, target))
            repeats = repeat_features_for_signatures(signatures)

            for ordinal, message_index, _message, action, target in parsed:
                op_id = operation_id(family, query, sample, message_index)
                if op_id in full_operation_ids:
                    raise ExperimentError(f"duplicate operation {op_id}")
                full_operation_ids.add(op_id)
                family_operation_counts[family] += 1
                visible.append(
                    {
                        "operation_id": op_id,
                        "family": family,
                        "task_id": task_id(family, query),
                        "trajectory_id": trajectory_id(family, query, sample),
                        "session": trajectory_id(family, query, sample),
                        "query_index": query,
                        "sample_index": sample,
                        "message_index": message_index,
                        "step_ordinal": ordinal,
                        "intent": intent_by_task[task_id(family, query)],
                        "phase": phase_for_ordinal(ordinal, tool_ordinals),
                        "action": action,
                        "target": target,
                        "repeat_state": repeats[ordinal]["repeat_state"],
                        "flat": "all",
                    }
                )

    if len(full_operation_ids) != EXPECTED_OPERATIONS:
        raise ExperimentError(
            f"expected {EXPECTED_OPERATIONS} operations, got {len(full_operation_ids)}"
        )

    selected_tasks: set[str] = set(task_prompts)
    if query_limit is not None:
        if query_limit <= 0:
            raise ExperimentError("query limit must be positive")
        selected_tasks = set()
        for family in FAMILIES:
            values = sorted(
                int(row["query_index"]) for row in records[family]
            )
            values = sorted(set(values))
            if len(values) < query_limit:
                raise ExperimentError(f"{family}: fewer than {query_limit} tasks")
            selected_tasks.update(task_id(family, value) for value in values[:query_limit])

    selected_visible = [row for row in visible if row["task_id"] in selected_tasks]
    audit = {
        "source_commit": _source_commit(source),
        "global": {
            "families": len(FAMILIES),
            "trajectories": len(trajectory_keys),
            "tasks": len(task_prompts),
            "operations": len(full_operation_ids),
            "operations_by_family": dict(family_operation_counts),
            "intent_tags": len(set(intent_by_task.values())),
            "intent_tag_samples": cluster_info,
        },
        "selected": {
            "query_limit": query_limit,
            "tasks": len(selected_tasks),
            "trajectories": len({row["trajectory_id"] for row in selected_visible}),
            "operations": len(selected_visible),
            "operations_by_family": dict(Counter(row["family"] for row in selected_visible)),
        },
    }
    return selected_visible, full_operation_ids, audit


def load_human_labels(
    source: Path, full_operation_ids: set[str], selected_ids: set[str]
) -> tuple[dict[str, int], dict[str, Any]]:
    """Read human-label values only after all fixed profile views exist."""
    data_dir = _official_data_dir(source)
    labels: dict[str, int] = {}
    for family in FAMILIES:
        for record in iter_jsonl(data_dir / f"{family}.jsonl"):
            query = int(record["query_index"])
            sample = int(record["sample_index"])
            official_labels = record.get("step_labels")
            if not isinstance(official_labels, dict):
                raise ExperimentError(f"{family}:{query}:{sample}: missing step labels")
            for message_index, value in official_labels.items():
                op_id = operation_id(family, query, sample, message_index)
                if op_id not in full_operation_ids:
                    raise ExperimentError(f"human label has unknown operation {op_id}")
                if op_id in labels:
                    raise ExperimentError(f"duplicate human label for {op_id}")
                if isinstance(value, bool) or value not in (-1, 0, 1):
                    raise ExperimentError(f"{op_id}: invalid human label {value!r}")
                labels[op_id] = int(value)
    if set(labels) != full_operation_ids:
        raise ExperimentError(
            f"human-label coverage {len(labels)} != {len(full_operation_ids)}"
        )
    selected = {op_id: labels[op_id] for op_id in selected_ids}
    return selected, {
        "global_steps": len(labels),
        "selected_steps": len(selected),
        "exact_coverage": True,
        "loaded_after_profiles": True,
    }


def _prediction_model_dirs(source: Path) -> list[Path]:
    root = source / "eval" / "results"
    if not root.is_dir():
        raise ExperimentError(f"missing official blind results: {root}")
    directories = []
    for path in sorted((item for item in root.iterdir() if item.is_dir()), key=lambda p: p.name):
        if len(list(path.glob("*.jsonl"))) == len(FAMILIES):
            directories.append(path)
    if len(directories) != EXPECTED_MODELS:
        raise ExperimentError(
            f"expected {EXPECTED_MODELS} complete model result directories, got {len(directories)}"
        )
    return directories


def load_external_risks(
    source: Path, full_operation_ids: set[str], selected_ids: set[str]
) -> tuple[dict[str, dict[str, int | float]], dict[str, Any]]:
    slots: dict[str, list[int | None]] = {op_id: [] for op_id in full_operation_ids}
    model_dirs = _prediction_model_dirs(source)
    failures_by_model: dict[str, int] = {}

    for model_dir in model_dirs:
        model_seen: set[str] = set()
        model_failures = 0
        for family in FAMILIES:
            files = list(model_dir.glob(f"{family}__*.jsonl"))
            if len(files) != 1:
                raise ExperimentError(f"{model_dir}: expected one {family} result file")
            records = list(iter_jsonl(files[0]))
            if len(records) != EXPECTED_TRAJECTORIES_PER_FAMILY:
                raise ExperimentError(f"{files[0]}: expected 250 records")
            for record in records:
                query = int(record["query_index"])
                sample = int(record["sample_index"])
                if str(record.get("comment") or "").startswith("llm_annotate_failed:"):
                    model_failures += 1
                predictions = record.get("step_labels")
                if not isinstance(predictions, dict):
                    raise ExperimentError(f"{files[0]}: missing step predictions")
                for message_index, value in predictions.items():
                    op_id = operation_id(family, query, sample, message_index)
                    if op_id not in slots:
                        raise ExperimentError(f"blind result has unknown operation {op_id}")
                    if op_id in model_seen:
                        raise ExperimentError(f"{model_dir.name}: duplicate {op_id}")
                    if value is not None:
                        if isinstance(value, bool) or value not in (-1, 0, 1):
                            raise ExperimentError(f"{op_id}: invalid blind prediction {value!r}")
                        value = int(value)
                    slots[op_id].append(value)
                    model_seen.add(op_id)
        if model_seen != full_operation_ids:
            raise ExperimentError(
                f"{model_dir.name}: prediction coverage {len(model_seen)} != {len(full_operation_ids)}"
            )
        failures_by_model[model_dir.name] = model_failures

    risks: dict[str, dict[str, int | float]] = {}
    all_null: list[str] = []
    full_non_null = 0
    below_fifteen = 0
    for op_id, values in slots.items():
        if len(values) != EXPECTED_MODELS:
            raise ExperimentError(f"{op_id}: expected 20 prediction slots")
        available = [value for value in values if value is not None]
        if not available:
            negative = 0
            risk = 0.5
            risk_units = RISK_SCALE // 2
            all_null.append(op_id)
        else:
            negative = sum(value == -1 for value in available)
            risk = negative / len(available)
            risk_units = negative * (RISK_SCALE // len(available))
        if len(available) == EXPECTED_MODELS:
            full_non_null += 1
        if len(available) < 15:
            below_fifteen += 1
        risks[op_id] = {
            "risk": risk,
            "risk_units": risk_units,
            "available_predictions": len(available),
            "negative_predictions": negative,
            "prediction_slots": EXPECTED_MODELS,
        }

    if len(all_null) != EXPECTED_ALL_NULL:
        raise ExperimentError(
            f"expected {EXPECTED_ALL_NULL} all-null steps, got {len(all_null)}"
        )
    selected = {op_id: risks[op_id] for op_id in selected_ids}
    audit = {
        "models": len(model_dirs),
        "model_names": [path.name for path in model_dirs],
        "failures_by_model": failures_by_model,
        "global_steps": len(risks),
        "full_20_non_null": full_non_null,
        "below_15_non_null": below_fifteen,
        "all_null_steps": sorted(all_null),
        "selected_steps": len(selected),
        "selected_all_null_steps": sorted(set(all_null) & selected_ids),
        "risk_scale": RISK_SCALE,
    }
    return selected, audit


def agentprof_version(binary: Path) -> str:
    completed = subprocess.run(
        [str(binary), "--version"],
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    version = completed.stdout.strip()
    if version != AGENTPROF_VERSION:
        raise ExperimentError(f"expected {AGENTPROF_VERSION!r}, got {version!r}")
    return version


def invoke_agentprof(
    binary: Path, operation_file: Path, output: Path, fields: Sequence[str]
) -> Counter[str]:
    output.parent.mkdir(parents=True, exist_ok=True)
    completed = subprocess.run(
        [
            str(binary),
            "--operation-file",
            str(operation_file),
            "--view",
            "operations",
            "--format",
            "json",
            "--output",
            str(output),
            "--stack",
            ",".join(fields),
            "--deterministic-output",
        ],
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    status = json.loads(completed.stdout)
    if status.get("status") != "ok":
        raise ExperimentError(f"AgentProf returned {status}")
    stacks = read_json(output).get("profile", {}).get("stacks")
    if not isinstance(stacks, dict):
        raise ExperimentError(f"{output}: missing profile.stacks")
    return Counter({str(key): int(value) for key, value in stacks.items()})


def construct_profiles(
    rows: list[dict[str, Any]],
    risks: dict[str, dict[str, int | float]],
    binary: Path,
    out: Path,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    projection_path = out / "projection.jsonl"
    risk_path = out / "risks.jsonl"
    operation_path = out / "operations.jsonl"
    risk_operation_path = out / "risk-operations.jsonl"
    write_jsonl(projection_path, rows)
    write_jsonl(
        risk_path,
        (
            {"operation_id": row["operation_id"], **risks[row["operation_id"]]}
            for row in rows
        ),
    )
    all_fields = sorted({field for fields in PROFILE_FIELDS.values() for field in fields})
    operations = [
        {
            "value": 1,
            "fields": {
                field: safe_stack_value(row[field]) for field in all_fields
            },
        }
        for row in rows
    ]
    write_jsonl(operation_path, operations)
    risk_operations = [
        {
            # AgentProf treats a zero operation value as its default count of
            # one. Add one to every operation, then subtract the independently
            # verified operation count from each emitted group exactly.
            "value": int(risks[row["operation_id"]]["risk_units"]) + 1,
            "fields": {
                field: safe_stack_value(row[field]) for field in all_fields
            },
        }
        for row in rows
    ]
    write_jsonl(risk_operation_path, risk_operations)
    input_risk_units = sum(
        int(risks[row["operation_id"]]["risk_units"]) for row in rows
    )

    report: dict[str, Any] = {
        "agentprof_version": agentprof_version(binary),
        "operations": len(rows),
        "input_risk_units": input_risk_units,
        "risk_value_encoding": "risk_units_plus_one_minus_group_operation_count",
        "views": {},
    }
    assignments: list[dict[str, Any]] = []
    for row in rows:
        assignment = {
            "operation_id": row["operation_id"],
            "family": row["family"],
            "task_id": row["task_id"],
            "trajectory_id": row["trajectory_id"],
            **risks[row["operation_id"]],
            "groups": {
                method: method_key(row, method) for method in PROFILE_FIELDS
            },
        }
        assignments.append(assignment)

    for method, fields in PROFILE_FIELDS.items():
        expected_operations = Counter(method_key(row, method) for row in rows)
        observed_operations = invoke_agentprof(
            binary,
            operation_path,
            out / "profiles" / f"{method}.json",
            fields,
        )
        if expected_operations != observed_operations:
            raise ExperimentError(f"AgentProf {method} stacks differ from assignments")
        expected_risk: Counter[str] = Counter()
        for row in rows:
            expected_risk[method_key(row, method)] += int(
                risks[row["operation_id"]]["risk_units"]
            )
        observed_shifted_risk = invoke_agentprof(
            binary,
            risk_operation_path,
            out / "profiles" / f"{method}-risk.json",
            fields,
        )
        operation_groups = set(expected_operations)
        unexpected_risk_groups = set(observed_shifted_risk) - operation_groups
        observed_risk: Counter[str] = Counter()
        for group in operation_groups:
            shifted = observed_shifted_risk.get(group, 0)
            if shifted < expected_operations[group]:
                raise ExperimentError(
                    f"AgentProf {method} shifted risk is smaller than operation count"
                )
            observed_risk[group] = shifted - expected_operations[group]
        risk_groups_exact = not unexpected_risk_groups and all(
            observed_risk[group] == expected_risk[group]
            for group in operation_groups
        )
        observed_risk_units = sum(observed_risk.values())
        if not risk_groups_exact or observed_risk_units != input_risk_units:
            raise ExperimentError(f"AgentProf {method} risk conservation failed")
        report["views"][method] = {
            "groups": len(expected_operations),
            "expected_operations": len(rows),
            "observed_operations": sum(observed_operations.values()),
            "operation_conservation_exact": True,
            "expected_risk_units": input_risk_units,
            "observed_risk_units": observed_risk_units,
            "risk_conservation_exact": True,
            "per_group_risk_exact": True,
        }
    write_jsonl(out / "group-assignments.jsonl", assignments)
    write_json(out / "profile-report.json", report)
    return assignments, report


def group_index(keys: Sequence[str]) -> tuple[np.ndarray, list[str]]:
    labels: list[str] = []
    indices: dict[str, int] = {}
    result = np.empty(len(keys), dtype=np.int32)
    for offset, key in enumerate(keys):
        if key not in indices:
            indices[key] = len(labels)
            labels.append(key)
        result[offset] = indices[key]
    return result, labels


def build_states(
    rows: list[dict[str, Any]],
    labels: dict[str, int],
    risks: dict[str, dict[str, int | float]],
    assignments: list[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    assignment_by_id = {row["operation_id"]: row for row in assignments}
    states: dict[str, dict[str, Any]] = {}
    for family in FAMILIES:
        family_rows = [row for row in rows if row["family"] == family]
        tasks = sorted({row["task_id"] for row in family_rows})
        task_to_index = {task: index for index, task in enumerate(tasks)}
        operation_ids = [row["operation_id"] for row in family_rows]
        state: dict[str, Any] = {
            "family": family,
            "rows": family_rows,
            "operation_ids": operation_ids,
            "task_ids": tasks,
            "task_index": np.asarray(
                [task_to_index[row["task_id"]] for row in family_rows], dtype=np.int32
            ),
            "labels": np.asarray(
                [1 if labels[op_id] == -1 else 0 for op_id in operation_ids],
                dtype=np.int8,
            ),
            "risk_units": np.asarray(
                [int(risks[op_id]["risk_units"]) for op_id in operation_ids],
                dtype=np.int64,
            ),
            "groups": {},
            "group_labels": {},
        }
        for method in ALL_VIEWS:
            keys = [assignment_by_id[op_id]["groups"][method] for op_id in operation_ids]
            indices, group_labels = group_index(keys)
            state["groups"][method] = indices
            state["group_labels"][method] = group_labels
        states[family] = state
    return states


def metric_from_group_arrays(
    scores: np.ndarray, counts: np.ndarray, positives: np.ndarray
) -> dict[str, float | int]:
    valid = counts > 0
    scores = scores[valid].astype(np.float64, copy=False)
    counts = counts[valid].astype(np.float64, copy=False)
    positives = positives[valid].astype(np.float64, copy=False)
    if not len(counts):
        raise ExperimentError("metric has no groups")
    total = float(counts.sum())
    total_positive = float(positives.sum())
    if total <= 0 or total_positive <= 0 or total_positive > total:
        raise ExperimentError("metric population needs positive operations")

    order = np.argsort(-scores, kind="mergesort")
    scores = scores[order]
    counts = counts[order]
    positives = positives[order]
    starts = np.concatenate(([0], np.flatnonzero(scores[1:] != scores[:-1]) + 1))
    tier_counts = np.add.reduceat(counts, starts)
    tier_positives = np.add.reduceat(positives, starts)
    tier_groups = np.diff(np.append(starts, len(scores)))

    cumulative_count = 0.0
    cumulative_positive = 0.0
    average_precision = 0.0
    recall30_positive = 0.0
    work50 = 1.0
    groups_to50 = len(scores)
    reached50 = False
    top5_work = 1.0
    top5_recall = 1.0
    cumulative_groups = 0
    reached5 = False
    for count, positive, group_count in zip(
        tier_counts, tier_positives, tier_groups, strict=True
    ):
        end_count = cumulative_count + float(count)
        end_positive = cumulative_positive + float(positive)
        end_groups = cumulative_groups + int(group_count)
        if positive > 0:
            average_precision += (float(positive) / total_positive) * (
                end_positive / end_count
            )
        if end_count <= 0.30 * total + 1e-12:
            recall30_positive = end_positive
        if not reached50 and end_positive >= 0.50 * total_positive:
            work50 = end_count / total
            groups_to50 = end_groups
            reached50 = True
        if not reached5 and end_groups >= min(5, len(scores)):
            top5_work = end_count / total
            top5_recall = end_positive / total_positive
            reached5 = True
        cumulative_count = end_count
        cumulative_positive = end_positive
        cumulative_groups = end_groups

    return {
        "average_precision": average_precision,
        "recall_at_30": recall30_positive / total_positive,
        "work_to_50": work50,
        "groups": int(len(scores)),
        "groups_to_50": int(groups_to50),
        "top5_work": top5_work,
        "top5_recall": top5_recall,
        "operations": total,
        "positives": total_positive,
    }


def metric_for_view(
    state: dict[str, Any], method: str, weights: np.ndarray
) -> dict[str, float | int]:
    group = state["groups"][method]
    group_count = len(state["group_labels"][method])
    counts = np.bincount(group, weights=weights, minlength=group_count)
    risk_sum = np.bincount(
        group,
        weights=weights * state["risk_units"],
        minlength=group_count,
    )
    positives = np.bincount(
        group,
        weights=weights * state["labels"],
        minlength=group_count,
    )
    scores = np.divide(
        risk_sum,
        counts,
        out=np.full(group_count, -np.inf, dtype=np.float64),
        where=counts > 0,
    )
    return metric_from_group_arrays(scores, counts, positives)


def classification_metrics(
    state: dict[str, Any], method: str
) -> dict[str, float | int]:
    weights = np.ones(len(state["rows"]), dtype=np.float64)
    group = state["groups"][method]
    group_count = len(state["group_labels"][method])
    counts = np.bincount(group, minlength=group_count).astype(np.float64)
    risk_sum = np.bincount(
        group, weights=state["risk_units"], minlength=group_count
    ).astype(np.float64)
    scores = np.divide(risk_sum, counts, where=counts > 0) / RISK_SCALE
    predictions = scores[group] > 0.5
    labels = state["labels"].astype(bool)
    binary_accuracy = float(np.mean(predictions == labels))

    first_matches = 0
    trajectories = 0
    by_trajectory: dict[str, list[int]] = defaultdict(list)
    for offset, row in enumerate(state["rows"]):
        by_trajectory[row["trajectory_id"]].append(offset)
    for offsets in by_trajectory.values():
        offsets.sort(key=lambda value: state["rows"][value]["step_ordinal"])
        predicted = next((value for value in offsets if predictions[value]), None)
        actual = next((value for value in offsets if labels[value]), None)
        first_matches += predicted == actual
        trajectories += 1
    return {
        "binary_harmful_accuracy": binary_accuracy,
        "adapted_first_error_accuracy": first_matches / trajectories,
        "trajectories": trajectories,
        "operations": int(weights.sum()),
    }


def base_results(states: dict[str, dict[str, Any]]) -> dict[str, Any]:
    per_family: dict[str, dict[str, Any]] = {}
    for family, state in states.items():
        weights = np.ones(len(state["rows"]), dtype=np.float64)
        per_family[family] = {}
        for method in ALL_VIEWS:
            result = metric_for_view(state, method, weights)
            result.update(classification_metrics(state, method))
            per_family[family][method] = result

    macro: dict[str, dict[str, float]] = {}
    for method in ALL_VIEWS:
        macro[method] = {
            metric: float(
                np.mean([per_family[family][method][metric] for family in FAMILIES])
            )
            for metric in (
                "average_precision",
                "recall_at_30",
                "work_to_50",
                "binary_harmful_accuracy",
                "adapted_first_error_accuracy",
            )
        }
    effects = {
        "semantic_minus_raw_ap": (
            macro["semantic"]["average_precision"]
            - macro["raw_action"]["average_precision"]
        ),
        "raw_minus_semantic_work50": (
            macro["raw_action"]["work_to_50"]
            - macro["semantic"]["work_to_50"]
        ),
    }
    return {"per_family": per_family, "macro": macro, "effects": effects}


def shuffled_semantic_keys(
    state: dict[str, Any], seed: int, permutation: int, family_index: int
) -> tuple[list[str], bool]:
    rows = state["rows"]
    by_raw: dict[tuple[str, str, str], list[int]] = defaultdict(list)
    for offset, row in enumerate(rows):
        by_raw[(row["action"], row["target"], row["repeat_state"])].append(offset)
    rng = np.random.default_rng(np.random.SeedSequence([seed, permutation, family_index]))
    shuffled_pairs: list[tuple[str, str] | None] = [None] * len(rows)
    exact = True
    for indices in by_raw.values():
        original = [(rows[index]["intent"], rows[index]["phase"]) for index in indices]
        order = rng.permutation(len(indices))
        assigned = [original[int(value)] for value in order]
        if Counter(original) != Counter(assigned):
            exact = False
        for index, pair in zip(indices, assigned, strict=True):
            shuffled_pairs[index] = pair
    keys: list[str] = []
    for row, pair in zip(rows, shuffled_pairs, strict=True):
        if pair is None:
            raise ExperimentError("shuffle left operation unassigned")
        keys.append(
            ";".join(
                [
                    f"intent:{agentprof_frame_value(pair[0])}",
                    f"phase:{agentprof_frame_value(pair[1])}",
                    f"action:{agentprof_frame_value(row['action'])}",
                    f"target:{agentprof_frame_value(row['target'])}",
                    f"repeat_state:{agentprof_frame_value(row['repeat_state'])}",
                ]
            )
        )
    original_sizes = sorted(Counter(method_key(row, "semantic") for row in rows).values())
    shuffled_sizes = sorted(Counter(keys).values())
    exact = exact and original_sizes == shuffled_sizes
    return keys, exact


def run_shuffles(
    states: dict[str, dict[str, Any]], base: dict[str, Any], permutations: int, seed: int
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    if permutations != 200:
        raise ExperimentError("approved experiment requires exactly 200 shuffles")
    rows: list[dict[str, Any]] = []
    observed = float(base["effects"]["semantic_minus_raw_ap"])
    for permutation in range(permutations):
        family_metrics: dict[str, dict[str, float | int]] = {}
        exact = True
        for family_index, family in enumerate(FAMILIES):
            state = states[family]
            keys, family_exact = shuffled_semantic_keys(
                state, seed, permutation, family_index
            )
            exact = exact and family_exact
            group, labels = group_index(keys)
            shuffled_state = dict(state)
            shuffled_state["groups"] = dict(state["groups"])
            shuffled_state["group_labels"] = dict(state["group_labels"])
            shuffled_state["groups"]["shuffled"] = group
            shuffled_state["group_labels"]["shuffled"] = labels
            family_metrics[family] = metric_for_view(
                shuffled_state,
                "shuffled",
                np.ones(len(state["rows"]), dtype=np.float64),
            )
        if not exact:
            raise ExperimentError(f"shuffle {permutation}: group sizes changed")
        macro_ap = float(
            np.mean([family_metrics[family]["average_precision"] for family in FAMILIES])
        )
        macro_work = float(
            np.mean([family_metrics[family]["work_to_50"] for family in FAMILIES])
        )
        rows.append(
            {
                "permutation": permutation,
                "macro_average_precision": macro_ap,
                "macro_work_to_50": macro_work,
                "delta_ap_vs_raw": (
                    macro_ap - base["macro"]["raw_action"]["average_precision"]
                ),
                "size_preservation_exact": True,
            }
        )
    exceed = sum(row["delta_ap_vs_raw"] >= observed for row in rows)
    summary = {
        "permutations": permutations,
        "observed_delta_ap": observed,
        "shuffle_delta_ap_min": min(row["delta_ap_vs_raw"] for row in rows),
        "shuffle_delta_ap_median": float(
            np.median([row["delta_ap_vs_raw"] for row in rows])
        ),
        "shuffle_delta_ap_max": max(row["delta_ap_vs_raw"] for row in rows),
        "greater_or_equal": exceed,
        "p_shuffle": (1 + exceed) / (permutations + 1),
        "size_preservation_exact": all(row["size_preservation_exact"] for row in rows),
    }
    return rows, summary


_BOOT_STATES: dict[str, dict[str, Any]] | None = None
_BOOT_SEED = 0


def _bootstrap_attempt(attempt: int) -> dict[str, Any] | None:
    if _BOOT_STATES is None:
        raise RuntimeError("bootstrap state not initialized")
    rng = np.random.default_rng(np.random.SeedSequence([_BOOT_SEED, attempt]))
    per_family: dict[str, dict[str, dict[str, float | int]]] = {}
    for family in FAMILIES:
        state = _BOOT_STATES[family]
        task_count = len(state["task_ids"])
        draw = rng.integers(0, task_count, size=task_count)
        multiplicity = np.bincount(draw, minlength=task_count)
        weights = multiplicity[state["task_index"]].astype(np.float64)
        weighted_positive = float(np.sum(weights * state["labels"]))
        if weighted_positive <= 0:
            return None
        per_family[family] = {
            method: metric_for_view(state, method, weights) for method in ALL_VIEWS
        }

    macro: dict[str, dict[str, float]] = {}
    for method in ALL_VIEWS:
        macro[method] = {
            metric: float(
                np.mean([per_family[family][method][metric] for family in FAMILIES])
            )
            for metric in ("average_precision", "recall_at_30", "work_to_50")
        }
    return {
        "attempt": attempt,
        "semantic_minus_raw_ap": (
            macro["semantic"]["average_precision"]
            - macro["raw_action"]["average_precision"]
        ),
        "raw_minus_semantic_work50": (
            macro["raw_action"]["work_to_50"]
            - macro["semantic"]["work_to_50"]
        ),
        "macro": macro,
    }


def run_bootstrap(
    states: dict[str, dict[str, Any]],
    requested: int,
    max_attempts: int,
    seed: int,
    workers: int,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    global _BOOT_STATES, _BOOT_SEED
    _BOOT_STATES = states
    _BOOT_SEED = seed
    valid: list[dict[str, Any]] = []
    examined = 0
    batch_size = 256
    pool: Any = None
    try:
        if workers > 1:
            pool = mp.get_context("fork").Pool(processes=workers)
        for start in range(0, max_attempts, batch_size):
            attempts = list(range(start, min(start + batch_size, max_attempts)))
            results = (
                pool.map(_bootstrap_attempt, attempts)
                if pool is not None
                else [_bootstrap_attempt(attempt) for attempt in attempts]
            )
            for attempt, result in zip(attempts, results, strict=True):
                examined = attempt + 1
                if result is not None:
                    valid.append(result)
                if len(valid) == requested:
                    break
            if len(valid) == requested:
                break
    finally:
        if pool is not None:
            pool.close()
            pool.join()

    intervals: dict[str, list[float]] = {}
    for field in ("semantic_minus_raw_ap", "raw_minus_semantic_work50"):
        values = np.asarray([row[field] for row in valid], dtype=np.float64)
        intervals[field] = (
            [float(value) for value in np.percentile(values, [2.5, 97.5])]
            if len(values)
            else []
        )
    summary = {
        "requested": requested,
        "valid": len(valid),
        "examined": examined,
        "discarded": examined - len(valid),
        "max_attempts": max_attempts,
        "seed": seed,
        "workers": workers,
        "intervals": intervals,
        "complete": len(valid) == requested,
    }
    return valid, summary


def scientific_verdict(
    mode: str, bootstrap: dict[str, Any], shuffle: dict[str, Any]
) -> str:
    if not bootstrap["complete"]:
        return "INCOMPLETE"
    if mode != "full":
        return "PREFLIGHT_ONLY"
    ap_interval = bootstrap["intervals"]["semantic_minus_raw_ap"]
    work_interval = bootstrap["intervals"]["raw_minus_semantic_work50"]
    if ap_interval[0] > 0 and work_interval[0] > 0 and shuffle["p_shuffle"] <= 0.05:
        return "SUPPORTED"
    if ap_interval[1] < 0 or work_interval[1] < 0:
        return "CONTRADICTED"
    return "INCONCLUSIVE"


def markdown_report(summary: dict[str, Any]) -> str:
    lines = [
        f"# AgentProcessBench {summary['mode'].upper()} report",
        "",
        f"**Execution:** {summary['execution_status']}",
        f"**Scientific verdict:** {summary['scientific_verdict']}",
        f"**Source commit:** `{summary['source']['source_commit']}`",
        f"**AgentProf:** `{summary['profiles']['agentprof_version']}`",
        "",
        "## Complete population accounting",
        "",
        f"- selected trajectories: {summary['source']['selected']['trajectories']:,}",
        f"- selected tasks: {summary['source']['selected']['tasks']:,}",
        f"- selected operations: {summary['source']['selected']['operations']:,}",
        f"- official judge models: {summary['risk']['models']}",
        f"- global all-null steps: {len(summary['risk']['all_null_steps'])}",
        f"- selected all-null steps: {len(summary['risk']['selected_all_null_steps'])}",
        "",
        "## Base localization results",
        "",
        "| Family | View | AP | Recall@30 | Work-to-50 | FirstErrAcc | Binary accuracy | Groups |",
        "|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    for family in FAMILIES:
        for method in ALL_VIEWS:
            value = summary["results"]["per_family"][family][method]
            lines.append(
                f"| {family} | {method} | {value['average_precision']:.6f} | "
                f"{value['recall_at_30']:.6f} | {value['work_to_50']:.6f} | "
                f"{value['adapted_first_error_accuracy']:.6f} | "
                f"{value['binary_harmful_accuracy']:.6f} | {value['groups']} |"
            )
    effects = summary["results"]["effects"]
    intervals = summary["bootstrap"]["intervals"]
    lines.extend(
        [
            "",
            "## Predeclared effects",
            "",
            f"- semantic − raw macro AP: {effects['semantic_minus_raw_ap']:.6f}; "
            f"95% interval {intervals['semantic_minus_raw_ap']}",
            f"- raw − semantic macro work-to-50: "
            f"{effects['raw_minus_semantic_work50']:.6f}; "
            f"95% interval {intervals['raw_minus_semantic_work50']}",
            f"- matched-shuffle empirical p: {summary['shuffle']['p_shuffle']:.6f}",
            "",
            "## Completion and controls",
            "",
            f"- bootstrap: {summary['bootstrap']['valid']:,} valid / "
            f"{summary['bootstrap']['examined']:,} examined; "
            f"{summary['bootstrap']['discarded']:,} discarded",
            f"- matched shuffles: {summary['shuffle']['permutations']}; "
            f"size preservation exact: {summary['shuffle']['size_preservation_exact']}",
            "- AgentProf operation counts and stack assignments match every grouped view",
            "- human labels score the fixed external risk/profile outputs; they do not define them",
            "",
            "The verdict applies only to this tested RQ2 construction. It does not change",
            "the paper thesis, canonical story, positive RQ2 hypothesis, or four RQs.",
        ]
    )
    return "\n".join(lines) + "\n"


def validate_cli_contract(args: argparse.Namespace) -> None:
    if args.seed != 4204 or args.permutations != 200:
        raise ExperimentError("approved seed/permutation contract differs")
    if args.mode == "preflight":
        if (
            args.query_limit != 10
            or args.bootstraps != 1_000
            or args.max_bootstrap_attempts != 5_000
        ):
            raise ExperimentError("preflight must use 10 tasks/family, 1000/5000 bootstrap")
    elif args.mode == "full":
        if (
            args.query_limit is not None
            or args.bootstraps != 10_000
            or args.max_bootstrap_attempts != 50_000
        ):
            raise ExperimentError("full must use complete data and 10000/50000 bootstrap")


def run(args: argparse.Namespace) -> dict[str, Any]:
    validate_cli_contract(args)
    source = Path(args.source).resolve()
    binary = Path(args.agentpprof_bin).resolve()
    out = Path(args.out).resolve()
    out.mkdir(parents=True, exist_ok=True)

    rows, full_ids, source_audit = load_source(source, args.query_limit)
    selected_ids = {row["operation_id"] for row in rows}
    risks, risk_audit = load_external_risks(source, full_ids, selected_ids)
    if set(risks) != selected_ids:
        raise ExperimentError("selected operation/risk sets differ")

    assignments, profile_report = construct_profiles(rows, risks, binary, out)
    labels, label_audit = load_human_labels(source, full_ids, selected_ids)
    if set(labels) != selected_ids:
        raise ExperimentError("selected operation/label sets differ")
    states = build_states(rows, labels, risks, assignments)
    results = base_results(states)
    shuffle_rows, shuffle_summary = run_shuffles(
        states, results, args.permutations, args.seed
    )
    bootstrap_rows, bootstrap_summary = run_bootstrap(
        states,
        args.bootstraps,
        args.max_bootstrap_attempts,
        args.seed,
        args.workers,
    )

    write_jsonl(
        out / "labels.jsonl",
        (
            {"operation_id": row["operation_id"], "human_label": labels[row["operation_id"]]}
            for row in rows
        ),
    )
    write_jsonl(out / "shuffle-effects.jsonl", shuffle_rows)
    with gzip.open(out / "bootstrap-effects.jsonl.gz", "wt", encoding="utf-8") as output:
        output.write(
            json.dumps(
                {
                    "type": "header",
                    "requested": args.bootstraps,
                    "max_attempts": args.max_bootstrap_attempts,
                    "seed": args.seed,
                },
                sort_keys=True,
            )
            + "\n"
        )
        for row in bootstrap_rows:
            output.write(json.dumps(row, sort_keys=True) + "\n")

    execution_status = "VALID" if bootstrap_summary["complete"] else "INCOMPLETE"
    verdict = scientific_verdict(args.mode, bootstrap_summary, shuffle_summary)
    summary = {
        "mode": args.mode,
        "execution_status": execution_status,
        "scientific_verdict": verdict,
        "source": source_audit,
        "labels": label_audit,
        "risk": risk_audit,
        "profiles": profile_report,
        "results": results,
        "shuffle": shuffle_summary,
        "bootstrap": bootstrap_summary,
        "contract": {
            "query_limit": args.query_limit,
            "permutations": args.permutations,
            "bootstraps": args.bootstraps,
            "max_bootstrap_attempts": args.max_bootstrap_attempts,
            "seed": args.seed,
        },
    }
    write_json(out / "summary.json", summary)
    (out / "report.md").write_text(markdown_report(summary), encoding="utf-8")
    return summary


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="mode", required=True)
    for mode in ("preflight", "full"):
        command = subparsers.add_parser(mode)
        command.add_argument("--source", required=True)
        command.add_argument("--agentpprof-bin", required=True)
        command.add_argument("--out", required=True)
        command.add_argument("--permutations", type=int, required=True)
        command.add_argument("--bootstraps", type=int, required=True)
        command.add_argument("--max-bootstrap-attempts", type=int, required=True)
        command.add_argument("--seed", type=int, required=True)
        command.add_argument(
            "--workers",
            type=int,
            default=max(1, min(8, os.cpu_count() or 1)),
        )
        if mode == "preflight":
            command.add_argument("--query-limit", type=int, required=True)
        else:
            command.set_defaults(query_limit=None)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if args.workers <= 0:
        raise ExperimentError("workers must be positive")
    summary = run(args)
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if summary["execution_status"] == "VALID" else 2


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ExperimentError as error:
        print(f"experiment error: {error}", file=sys.stderr)
        raise SystemExit(2) from error
