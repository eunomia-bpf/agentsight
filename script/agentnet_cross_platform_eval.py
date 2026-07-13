#!/usr/bin/env python3
"""Complete AgentNet cross-platform RQ2 evaluation.

Public commands are ``prepare``, ``preflight``, and ``full``.  ``prepare`` is
the only command that reads the raw AgentNet release.  Coordinators invoke a
label-blind ``predict-fold`` subprocess with exactly one reference-platform
label file, persist predictions/profile groups/bootstrap draws, and only then
invoke ``score-fold`` with the held-out label file.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import math
import multiprocessing as mp
import os
import shutil
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable, Iterator, Sequence

import numpy as np
from scipy import sparse
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from agent_trace_datasets import (
    agentnet_action_phase,
    agentnet_action_target,
    agentnet_code_action,
    repeat_features_for_signatures,
    sanitize_label,
)


REVISION = "d76ee50a63fad81cfdbe576416757d7c2091ed50"
REPO_ID = "xlangai/AgentNet"
RAW_FILE = "agentnet_win_mac_18k.jsonl"
META_FILE = "meta_data_merged.jsonl"
EXPECTED_FILES = {
    RAW_FILE: {
        "size": 1_400_605_632,
        "sha256": "5c0d782cbf55af02835c3d6d9120072b87c06d24c5a8354c2544bd8d3568e72c",
    },
    META_FILE: {
        "size": 18_840_344,
        "sha256": "9bb101e8373cd8cd1316f29d53c938b378f96aae1f09776a32bcc27454a0184d",
    },
}
PLATFORMS = ("windows", "darwin")
EXPECTED_TASKS = {"windows": 12_364, "darwin": 5_168}
EXPECTED_TRAJECTORIES = {"windows": 12_427, "darwin": 5_198}
EXPECTED_REPEATED_TASKS = {"windows": 63, "darwin": 30}
EXPECTED_RAW_RECORDS = 17_625
FORBIDDEN_PROJECTION_FIELDS = {
    "correct",
    "redundant",
    "step_correct",
    "step_redundant",
    "last_step_correct",
    "last_step_redundant",
    "reflection",
    "thought",
    "observation",
    "task_completed",
    "reason",
    "alignment_score",
    "efficiency_score",
    "task_difficulty",
    "natural_language_task",
    "actual_task",
    "complexity",
    "verify_feedback",
    "task_description_alignment",
    "task_description_ambiguity",
    "action_entropy",
    "action_frequency",
}
CAT_FEATURES = (
    "domain",
    "application",
    "action",
    "target",
    "phase",
    "repeat_state",
    "repeat_signal",
    "repeat_run",
    "previous_action",
    "action_changed",
)
NUM_FEATURES = ("step_fraction", "log_trajectory_length")
PROFILE_FIELDS: dict[str, tuple[str, ...]] = {
    "flat": ("dataset",),
    "fixed_session": ("session",),
    "source_native": ("system", "domain", "application", "session", "action"),
    "raw_action": ("action", "target", "repeat_state"),
    "semantic": ("domain", "application", "phase", "action", "repeat_state"),
}
PRIMARY_VIEWS = ("semantic", "raw_action")
ALL_METHODS = (
    "flat",
    "fixed_session",
    "source_native",
    "raw_action",
    "semantic",
    "exact_repeat",
    "ungrouped_risk",
)
SAFE_STACK_VALUE = set(chr(code) for code in range(32, 127)) - {";", "\n", "\r"}
MAX_ITER = 1_000
AGENTPROF_VERSION = "agentpprof 0.2.37"
PER_DOMAIN_MIN_SCORABLE_TASKS = 30
_BOOT_STATE: dict[str, Any] | None = None


class ExperimentError(RuntimeError):
    pass


class IncompleteExperiment(ExperimentError):
    pass


def read_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as source:
        return json.load(source)


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as output:
        json.dump(value, output, ensure_ascii=False, indent=2, sort_keys=True)
        output.write("\n")


def iter_jsonl(path: Path) -> Iterator[dict[str, Any]]:
    with path.open(encoding="utf-8") as source:
        for line_number, line in enumerate(source, 1):
            try:
                value = json.loads(line)
            except json.JSONDecodeError as error:
                raise ExperimentError(f"{path}:{line_number}: invalid JSON") from error
            if not isinstance(value, dict):
                raise ExperimentError(f"{path}:{line_number}: expected object")
            yield value


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return list(iter_jsonl(path))


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as output:
        for row in rows:
            output.write(json.dumps(row, ensure_ascii=False, sort_keys=True))
            output.write("\n")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_file(path: Path, expected: dict[str, Any]) -> dict[str, Any]:
    if not path.is_file():
        raise ExperimentError(f"missing source file: {path}")
    size = path.stat().st_size
    if size != expected["size"]:
        raise ExperimentError(f"{path}: expected {expected['size']} bytes, got {size}")
    digest = sha256_file(path)
    if digest != expected["sha256"]:
        raise ExperimentError(f"{path}: expected SHA-256 {expected['sha256']}, got {digest}")
    return {"path": str(path), "size": size, "sha256": digest}


def download_sources(out: Path, revision: str) -> dict[str, Any]:
    if revision != REVISION:
        raise ExperimentError(f"approved revision is {REVISION}, got {revision}")
    try:
        from huggingface_hub import hf_hub_download
    except ImportError as error:
        raise ExperimentError("huggingface_hub is required for prepare") from error
    out.mkdir(parents=True, exist_ok=True)
    status: dict[str, Any] = {}
    for filename, expected in EXPECTED_FILES.items():
        target = out / filename
        if not target.exists() or target.stat().st_size != expected["size"]:
            downloaded = Path(
                hf_hub_download(
                    repo_id=REPO_ID,
                    filename=filename,
                    repo_type="dataset",
                    revision=revision,
                    local_dir=out,
                )
            )
            if downloaded.resolve() != target.resolve():
                shutil.copyfile(downloaded, target)
        status[filename] = verify_file(target, expected)
    return status


def canonical_platform(value: Any) -> str:
    label = str(value or "").strip().lower()
    if label == "windows":
        return "windows"
    if label in {"darwin", "mac", "macos"}:
        return "darwin"
    if label == "ubuntu":
        return "ubuntu"
    raise ExperimentError(f"unexpected platform {value!r}")


def application_label(value: Any) -> str:
    if not isinstance(value, list):
        return "none"
    labels = sorted({sanitize_label(str(item)) for item in value if str(item).strip()})
    return "+".join(labels) if labels else "none"


def operation_id(trajectory_id: str, ordinal: int) -> str:
    return f"{trajectory_id}:{ordinal}"


def label_value(correct: Any, redundant: Any) -> int | None:
    if correct is False or redundant is True:
        return 1
    if correct is True and redundant is False:
        return 0
    return None


def source_metadata(path: Path) -> dict[str, dict[str, Any]]:
    rows: dict[str, dict[str, Any]] = {}
    counts: Counter[str] = Counter()
    for row in iter_jsonl(path):
        task_id = str(row.get("task_id") or "")
        if not task_id or task_id in rows:
            raise ExperimentError(f"metadata duplicate/missing task_id {task_id!r}")
        platform = canonical_platform(row.get("system"))
        counts[platform] += 1
        raw_domain = str(row.get("domains") or "none")
        raw_applications = [
            str(item) for item in row.get("applications") or [] if str(item).strip()
        ]
        rows[task_id] = {
            "task_id": task_id,
            "platform": platform,
            "source_domain": raw_domain,
            "source_applications": raw_applications,
            "domain": sanitize_label(raw_domain),
            "application": application_label(raw_applications),
        }
    for platform, expected in {**EXPECTED_TASKS, "ubuntu": 5_000}.items():
        if counts[platform] != expected:
            raise ExperimentError(
                f"metadata {platform}: expected {expected} tasks, got {counts[platform]}"
            )
    if len(rows) != 22_532:
        raise ExperimentError(f"metadata expected 22532 tasks, got {len(rows)}")
    return rows


def projection_and_labels(
    raw_path: Path, metadata: dict[str, dict[str, Any]], out: Path
) -> dict[str, Any]:
    projection_path = out / "projection.jsonl"
    label_paths = {platform: out / "labels" / f"{platform}.jsonl" for platform in PLATFORMS}
    projection_path.parent.mkdir(parents=True, exist_ok=True)
    for path in label_paths.values():
        path.parent.mkdir(parents=True, exist_ok=True)

    task_ids_by_platform: dict[str, set[str]] = {
        platform: set() for platform in PLATFORMS
    }
    trajectory_counts: Counter[str] = Counter()
    operation_counts: Counter[str] = Counter()
    label_states: dict[str, Counter[str]] = {platform: Counter() for platform in PLATFORMS}
    raw_task_occurrences: Counter[str] = Counter()
    with projection_path.open("w", encoding="utf-8") as projection_out, \
        label_paths["windows"].open("w", encoding="utf-8") as windows_out, \
        label_paths["darwin"].open("w", encoding="utf-8") as darwin_out:
        label_outputs = {"windows": windows_out, "darwin": darwin_out}
        for row_index, raw in enumerate(iter_jsonl(raw_path)):
            task_id = str(raw.get("task_id") or "")
            if not task_id:
                raise ExperimentError(f"raw row {row_index}: missing task_id")
            meta = metadata.get(task_id)
            if not meta or meta["platform"] not in PLATFORMS:
                raise ExperimentError(f"raw task has no Windows/Darwin metadata: {task_id}")
            platform = meta["platform"]
            trajectory_id = f"{task_id}@row-{row_index:05d}"
            raw_task_occurrences[task_id] += 1
            task_ids_by_platform[platform].add(task_id)
            trajectory_counts[platform] += 1
            traj = [step for step in raw.get("traj") or [] if isinstance(step, dict)]
            if not traj:
                raise ExperimentError(f"{task_id}: empty trajectory")
            parsed: list[tuple[str, str, str, dict[str, Any]]] = []
            signatures: list[tuple[str, str]] = []
            for step in traj:
                value = step.get("value") or {}
                if not isinstance(value, dict):
                    value = {}
                code = str(value.get("code") or "")
                action = agentnet_code_action(code)
                target = agentnet_action_target(action, code)
                parsed.append((code, action, target, value))
                signatures.append((action, target))
            repeats = repeat_features_for_signatures(signatures)
            previous_action = "start"
            for ordinal, ((code, action, target, value), repeat) in enumerate(
                zip(parsed, repeats, strict=True)
            ):
                op_id = operation_id(trajectory_id, ordinal)
                visible = {
                    "operation_id": op_id,
                    "task_id": task_id,
                    "trajectory_id": trajectory_id,
                    "platform": platform,
                    "dataset": "agentnet",
                    "session": sanitize_label(trajectory_id),
                    "system": platform,
                    "source_domain": meta["source_domain"],
                    "source_applications": meta["source_applications"],
                    "domain": meta["domain"],
                    "application": meta["application"],
                    "action_code": code,
                    "action": action,
                    "target": target,
                    "phase": agentnet_action_phase(action),
                    "repeat_state": repeat["repeat_state"],
                    "repeat_signal": repeat["repeat_signal"],
                    "repeat_run": repeat["repeat_run"],
                    "previous_action": previous_action,
                    "action_changed": "yes" if action != previous_action else "no",
                    "step_fraction": ordinal / max(1, len(traj) - 1),
                    "log_trajectory_length": math.log1p(len(traj)),
                }
                if FORBIDDEN_PROJECTION_FIELDS & set(visible):
                    raise ExperimentError("forbidden key reached visible projection")
                projection_out.write(json.dumps(visible, ensure_ascii=False, sort_keys=True) + "\n")
                label_row = {
                    "operation_id": op_id,
                    "task_id": task_id,
                    "trajectory_id": trajectory_id,
                    "platform": platform,
                    "correct": value.get("last_step_correct"),
                    "redundant": value.get("last_step_redundant"),
                }
                label_outputs[platform].write(
                    json.dumps(label_row, ensure_ascii=False, sort_keys=True) + "\n"
                )
                state = label_value(label_row["correct"], label_row["redundant"])
                label_states[platform]["unresolved" if state is None else str(state)] += 1
                operation_counts[platform] += 1
                previous_action = action
    expected_ids = {
        task_id for task_id, meta in metadata.items() if meta["platform"] in PLATFORMS
    }
    seen_task_ids = set(raw_task_occurrences)
    if seen_task_ids != expected_ids:
        missing = len(expected_ids - seen_task_ids)
        extra = len(seen_task_ids - expected_ids)
        raise ExperimentError(f"raw/metadata task mismatch: missing={missing}, extra={extra}")
    task_counts = {
        platform: len(task_ids_by_platform[platform]) for platform in PLATFORMS
    }
    for platform in PLATFORMS:
        if task_counts[platform] != EXPECTED_TASKS[platform]:
            raise ExperimentError(
                f"raw {platform}: expected {EXPECTED_TASKS[platform]}, got {task_counts[platform]}"
            )
    repeated_task_counts: Counter[str] = Counter()
    for task_id, occurrences in raw_task_occurrences.items():
        if occurrences > 2:
            raise ExperimentError(f"raw task {task_id} occurs {occurrences} times")
        if occurrences == 2:
            repeated_task_counts[metadata[task_id]["platform"]] += 1
    return {
        "raw_records": sum(trajectory_counts.values()),
        "task_counts": task_counts,
        "trajectory_counts": {
            platform: trajectory_counts[platform] for platform in PLATFORMS
        },
        "repeated_task_counts": {
            platform: repeated_task_counts[platform] for platform in PLATFORMS
        },
        "operation_counts": dict(operation_counts),
        "label_state_counts": {
            platform: dict(label_states[platform]) for platform in PLATFORMS
        },
        "projection": str(projection_path),
        "labels": {platform: str(path) for platform, path in label_paths.items()},
    }


def prepare(args: argparse.Namespace) -> dict[str, Any]:
    out = args.out.resolve()
    for stale in ("prepare-status.json", "source-report.md"):
        (out / stale).unlink(missing_ok=True)
    files = download_sources(out, args.revision)
    metadata = source_metadata(out / META_FILE)
    conversion = projection_and_labels(out / RAW_FILE, metadata, out)
    if conversion["raw_records"] != EXPECTED_RAW_RECORDS:
        raise ExperimentError(
            f"expected {EXPECTED_RAW_RECORDS} raw trajectory records, "
            f"got {conversion['raw_records']}"
        )
    for platform in PLATFORMS:
        if conversion["trajectory_counts"][platform] != EXPECTED_TRAJECTORIES[platform]:
            raise ExperimentError(
                f"{platform}: expected {EXPECTED_TRAJECTORIES[platform]} trajectories, "
                f"got {conversion['trajectory_counts'][platform]}"
            )
        if conversion["repeated_task_counts"][platform] != EXPECTED_REPEATED_TASKS[platform]:
            raise ExperimentError(
                f"{platform}: expected {EXPECTED_REPEATED_TASKS[platform]} repeated tasks, "
                f"got {conversion['repeated_task_counts'][platform]}"
            )
    status = {
        "status": "VALID",
        "revision": args.revision,
        "repo": REPO_ID,
        "files": files,
        "pure_helpers": [
            "agentnet_code_action",
            "agentnet_action_target",
            "agentnet_action_phase",
            "repeat_features_for_signatures",
        ],
        "legacy_normalize_agentnet_used": False,
        **conversion,
    }
    write_json(out / "prepare-status.json", status)
    report = [
        "# AgentNet source preparation report",
        "",
        f"- status: `{status['status']}`",
        f"- official revision: `{args.revision}`",
        f"- raw tasks: Windows {conversion['task_counts']['windows']:,}; Darwin {conversion['task_counts']['darwin']:,}",
        f"- released trajectory records: Windows {conversion['trajectory_counts']['windows']:,}; Darwin {conversion['trajectory_counts']['darwin']:,}",
        f"- repeated task IDs: Windows {conversion['repeated_task_counts']['windows']:,}; Darwin {conversion['repeated_task_counts']['darwin']:,}",
        f"- operations: Windows {conversion['operation_counts']['windows']:,}; Darwin {conversion['operation_counts']['darwin']:,}",
        "- every released trajectory row is retained; repeated task IDs remain one bootstrap cluster",
        "- visible projection and platform label files are separate",
        "- only the four approved pure helpers were used; `normalize_agentnet` was not used",
        "",
        "The label-state counts below are source-provenance diagnostics written by the",
        "only raw-reading stage. They are never present in `projection.jsonl` and are not",
        "available to a held-out predictor.",
        "",
        "```json",
        json.dumps(conversion["label_state_counts"], indent=2, sort_keys=True),
        "```",
    ]
    (out / "source-report.md").write_text("\n".join(report) + "\n", encoding="utf-8")
    return status


def safe_stack_value(value: Any) -> str:
    text = str(value)
    if not text or any(char not in SAFE_STACK_VALUE for char in text):
        raise ExperimentError(f"unsafe AgentProf stack value {text!r}")
    return text


def agentprof_frame_value(value: Any) -> str:
    """Mirror AgentProf safe-frame encoding for already visible stack fields."""
    text = safe_stack_value(value)
    output = ""
    for char in text.lower():
        if char.isascii() and (char.isalnum() or char in "._:/+-"):
            output += char
        elif not output.endswith("_"):
            output += "_"
    normalized = output.strip("_;")
    return normalized or "unknown"


def method_key(row: dict[str, Any], method: str) -> str:
    fields = PROFILE_FIELDS[method]
    return ";".join(f"{field}:{agentprof_frame_value(row[field])}" for field in fields)


def select_tasks(rows: list[dict[str, Any]], limit: int | None) -> list[dict[str, Any]]:
    if limit is None:
        return rows
    selected: set[str] = set()
    by_platform: dict[str, list[str]] = {platform: [] for platform in PLATFORMS}
    seen: dict[str, set[str]] = {platform: set() for platform in PLATFORMS}
    for row in rows:
        platform = row["platform"]
        task_id = row["task_id"]
        if task_id not in seen[platform]:
            seen[platform].add(task_id)
            by_platform[platform].append(task_id)
    for platform in PLATFORMS:
        if len(by_platform[platform]) < limit:
            raise ExperimentError(
                f"{platform}: requested {limit} tasks, found {len(by_platform[platform])}"
            )
        selected.update(sorted(by_platform[platform])[:limit])
    return [row for row in rows if row["task_id"] in selected]


def load_platform_labels(path: Path, expected_platform: str) -> dict[str, int | None]:
    labels: dict[str, int | None] = {}
    for row in iter_jsonl(path):
        if row.get("platform") != expected_platform:
            raise ExperimentError(
                f"{path}: expected {expected_platform} label, got {row.get('platform')}"
            )
        op_id = str(row.get("operation_id") or "")
        if not op_id or op_id in labels:
            raise ExperimentError(f"{path}: duplicate/missing operation_id")
        labels[op_id] = label_value(row.get("correct"), row.get("redundant"))
    return labels


def validate_projection_rows(rows: list[dict[str, Any]]) -> None:
    required = {
        "operation_id", "task_id", "trajectory_id", "platform", "dataset",
        "session", "system", "domain", "application", "action_code", "action",
        "target", "phase", "repeat_state", "repeat_signal", "repeat_run",
        "previous_action", "action_changed", "step_fraction",
        "log_trajectory_length",
    }
    operation_ids: set[str] = set()
    for index, row in enumerate(rows):
        missing = required - set(row)
        forbidden = FORBIDDEN_PROJECTION_FIELDS & set(row)
        if missing:
            raise ExperimentError(f"projection row {index} misses {sorted(missing)}")
        if forbidden:
            raise ExperimentError(
                f"projection row {index} contains forbidden fields {sorted(forbidden)}"
            )
        if row["platform"] not in PLATFORMS or row["system"] != row["platform"]:
            raise ExperimentError(f"projection row {index} has inconsistent platform")
        op_id = str(row["operation_id"])
        if not op_id or op_id in operation_ids:
            raise ExperimentError(f"projection row {index} duplicates operation_id {op_id!r}")
        operation_ids.add(op_id)


def validate_full_source(source: Path) -> dict[str, Any]:
    status_path = source / "prepare-status.json"
    if not status_path.is_file():
        raise ExperimentError("full run requires prepare-status.json")
    prepared = read_json(status_path)
    if prepared.get("status") != "VALID" or prepared.get("revision") != REVISION:
        raise ExperimentError("full run source was not prepared from the approved revision")
    rows = read_jsonl(source / "projection.jsonl")
    validate_projection_rows(rows)
    tasks: dict[str, set[str]] = {platform: set() for platform in PLATFORMS}
    trajectories: dict[str, set[str]] = {platform: set() for platform in PLATFORMS}
    operation_ids: dict[str, set[str]] = {platform: set() for platform in PLATFORMS}
    for row in rows:
        platform = row["platform"]
        tasks[platform].add(str(row["task_id"]))
        trajectories[platform].add(str(row["trajectory_id"]))
        operation_ids[platform].add(str(row["operation_id"]))
    for platform in PLATFORMS:
        if len(tasks[platform]) != EXPECTED_TASKS[platform]:
            raise ExperimentError(
                f"full {platform}: expected {EXPECTED_TASKS[platform]} tasks, "
                f"got {len(tasks[platform])}"
            )
        if len(trajectories[platform]) != EXPECTED_TRAJECTORIES[platform]:
            raise ExperimentError(
                f"full {platform}: expected {EXPECTED_TRAJECTORIES[platform]} trajectories, "
                f"got {len(trajectories[platform])}"
            )
        labels = load_platform_labels(source / "labels" / f"{platform}.jsonl", platform)
        if set(labels) != operation_ids[platform]:
            raise ExperimentError(
                f"full {platform}: projection/label operation IDs are not identical"
            )
    return {
        "revision": REVISION,
        "tasks": {platform: len(tasks[platform]) for platform in PLATFORMS},
        "trajectories": {
            platform: len(trajectories[platform]) for platform in PLATFORMS
        },
        "operations": {
            platform: len(operation_ids[platform]) for platform in PLATFORMS
        },
        "projection_label_exact_coverage": True,
    }


def feature_matrices(
    train_rows: list[dict[str, Any]], target_rows: list[dict[str, Any]]
) -> tuple[sparse.csr_matrix, sparse.csr_matrix, dict[str, Any]]:
    train_cat = np.asarray(
        [[str(row[field]) for field in CAT_FEATURES] for row in train_rows], dtype=object
    )
    target_cat = np.asarray(
        [[str(row[field]) for field in CAT_FEATURES] for row in target_rows], dtype=object
    )
    train_num = np.asarray(
        [[float(row[field]) for field in NUM_FEATURES] for row in train_rows], dtype=np.float64
    )
    target_num = np.asarray(
        [[float(row[field]) for field in NUM_FEATURES] for row in target_rows], dtype=np.float64
    )
    encoder = OneHotEncoder(handle_unknown="ignore", sparse_output=True, dtype=np.float64)
    scaler = StandardScaler()
    encoded_train = encoder.fit_transform(train_cat)
    encoded_target = encoder.transform(target_cat)
    scaled_train = sparse.csr_matrix(scaler.fit_transform(train_num))
    scaled_target = sparse.csr_matrix(scaler.transform(target_num))
    train = sparse.hstack((encoded_train, scaled_train), format="csr")
    target = sparse.hstack((encoded_target, scaled_target), format="csr")
    report = {
        "categorical_features": list(CAT_FEATURES),
        "numeric_features": list(NUM_FEATURES),
        "encoded_dimensions": int(train.shape[1]),
        "category_counts": {
            field: len(values) for field, values in zip(CAT_FEATURES, encoder.categories_, strict=True)
        },
        "unseen_target_category_counts": {
            field: len(set(target_cat[:, index]) - set(values))
            for index, (field, values) in enumerate(
                zip(CAT_FEATURES, encoder.categories_, strict=True)
            )
        },
    }
    return train, target, report


def agentprof_version(binary: Path) -> str:
    completed = subprocess.run(
        [str(binary), "--version"], check=True, text=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    value = completed.stdout.strip()
    if value != AGENTPROF_VERSION:
        raise ExperimentError(
            f"expected {AGENTPROF_VERSION!r}, got AgentProf version {value!r}"
        )
    return value


def invoke_agentprof(
    binary: Path, operation_file: Path, output: Path, fields: Sequence[str]
) -> Counter[str]:
    output.parent.mkdir(parents=True, exist_ok=True)
    completed = subprocess.run(
        [
            str(binary), "--operation-file", str(operation_file),
            "--view", "operations", "--format", "json", "--output", str(output),
            "--stack", ",".join(fields), "--deterministic-output",
        ],
        check=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    status = json.loads(completed.stdout)
    if status.get("status") != "ok":
        raise ExperimentError(f"AgentProf returned {status}")
    stacks = read_json(output).get("profile", {}).get("stacks")
    if not isinstance(stacks, dict):
        raise ExperimentError(f"{output}: missing profile.stacks")
    return Counter({str(key): int(value) for key, value in stacks.items()})


def write_operations_and_verify_profiles(
    rows: list[dict[str, Any]], binary: Path, out: Path
) -> dict[str, Any]:
    operation_file = out / "operations.jsonl"
    all_fields = sorted({field for fields in PROFILE_FIELDS.values() for field in fields})
    operations = [
        {"value": 1, "fields": {field: safe_stack_value(row[field]) for field in all_fields}}
        for row in rows
    ]
    write_jsonl(operation_file, operations)
    result: dict[str, Any] = {
        "agentprof_version": agentprof_version(binary),
        "operations": len(operations),
        "views": {},
    }
    for method, fields in PROFILE_FIELDS.items():
        expected = Counter(method_key(row, method) for row in rows)
        observed = invoke_agentprof(binary, operation_file, out / f"{method}.json", fields)
        if expected != observed:
            raise ExperimentError(
                f"AgentProf {method} counter mismatch: expected {sum(expected.values())}, "
                f"observed {sum(observed.values())}"
            )
        result["views"][method] = {
            "groups": len(observed), "operations": sum(observed.values()), "exact": True
        }
    return result


def group_index(keys: Sequence[str]) -> tuple[np.ndarray, list[str]]:
    labels: list[str] = []
    indices: dict[str, int] = {}
    values = np.empty(len(keys), dtype=np.int32)
    for offset, key in enumerate(keys):
        if key not in indices:
            indices[key] = len(labels)
            labels.append(key)
        values[offset] = indices[key]
    return values, labels


def write_draw_specs(
    path: Path, task_ids: list[str], attempts: int, seed: int
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(path, "wt", encoding="utf-8") as output:
        output.write(
            json.dumps(
                {
                    "type": "header",
                    "algorithm": "numpy-pcg64-task-bootstrap-v1",
                    "task_ids": task_ids,
                    "base_seed": seed,
                },
                separators=(",", ":"), sort_keys=True,
            )
            + "\n"
        )
        for attempt in range(attempts):
            digest = hashlib.sha256(f"{seed}|{attempt}".encode()).digest()
            draw_seed = int.from_bytes(digest[:8], "big", signed=False)
            output.write(
                json.dumps(
                    {"type": "draw", "attempt": attempt, "seed": draw_seed},
                    separators=(",", ":"), sort_keys=True,
                )
                + "\n"
            )


def fold_artifact_digests(out: Path) -> dict[str, str]:
    paths = [
        out / "predictions.jsonl",
        out / "group-assignments.jsonl",
        out / "group-summary.json",
        out / "bootstrap-draws.jsonl.gz",
        out / "model-report.json",
        out / "profile-report.json",
    ]
    return {path.name: sha256_file(path) for path in paths}


def validate_label_blind_artifacts(
    fold_dir: Path, assignments: list[dict[str, Any]]
) -> dict[str, Any]:
    predictions = read_jsonl(fold_dir / "predictions.jsonl")
    if len(predictions) != len(assignments):
        raise ExperimentError("prediction/group-assignment row counts differ")
    total_risk = 0.0
    recomputed: dict[str, dict[str, list[float]]] = {
        method: defaultdict(lambda: [0.0, 0.0]) for method in PROFILE_FIELDS
    }
    for index, (prediction, assignment) in enumerate(
        zip(predictions, assignments, strict=True)
    ):
        for field in ("operation_id", "task_id", "trajectory_id", "platform"):
            if prediction.get(field) != assignment.get(field):
                raise ExperimentError(
                    f"prediction/group assignment {index} differs on {field}"
                )
        prediction_risk = float(prediction["risk"])
        assignment_risk = float(assignment["risk"])
        if prediction_risk != assignment_risk or not math.isfinite(prediction_risk):
            raise ExperimentError(f"prediction/group assignment {index} risk differs")
        groups = assignment.get("groups")
        if not isinstance(groups, dict) or set(groups) != set(PROFILE_FIELDS):
            raise ExperimentError(f"group assignment {index} has incomplete views")
        total_risk += prediction_risk
        for method, key in groups.items():
            recomputed[method][str(key)][0] += prediction_risk
            recomputed[method][str(key)][1] += 1.0

    saved_summary = read_json(fold_dir / "group-summary.json")
    if set(saved_summary) != set(PROFILE_FIELDS):
        raise ExperimentError("saved group summary has incomplete views")
    view_report: dict[str, Any] = {}
    for method, groups in recomputed.items():
        saved_groups = saved_summary[method]
        if set(saved_groups) != set(groups):
            raise ExperimentError(f"{method}: saved/recomputed group keys differ")
        method_risk = 0.0
        method_operations = 0
        for key, (risk_sum, operations) in groups.items():
            saved = saved_groups[key]
            if int(saved["operations"]) != int(operations):
                raise ExperimentError(f"{method}/{key}: operation count differs")
            if not math.isclose(
                float(saved["risk_sum"]), risk_sum, rel_tol=1e-12, abs_tol=1e-12
            ):
                raise ExperimentError(f"{method}/{key}: predicted-risk sum differs")
            expected_density = risk_sum / operations
            if not math.isclose(
                float(saved["density"]), expected_density, rel_tol=1e-12, abs_tol=1e-12
            ):
                raise ExperimentError(f"{method}/{key}: risk density differs")
            method_risk += risk_sum
            method_operations += int(operations)
        if method_operations != len(assignments) or not math.isclose(
            method_risk, total_risk, rel_tol=1e-12, abs_tol=1e-12
        ):
            raise ExperimentError(f"{method}: total count/risk conservation failed")
        view_report[method] = {
            "groups": len(groups),
            "operations": method_operations,
            "risk_sum": method_risk,
        }

    profile_report = read_json(fold_dir / "profile-report.json")
    if int(profile_report.get("operations", -1)) != len(assignments):
        raise ExperimentError("AgentProf operation count differs from assignments")
    if set(profile_report.get("views", {})) != set(PROFILE_FIELDS):
        raise ExperimentError("AgentProf profile report has incomplete views")
    for method, value in profile_report["views"].items():
        if not value.get("exact") or int(value.get("operations", -1)) != len(assignments):
            raise ExperimentError(f"AgentProf {method} count conservation failed")
        if int(value.get("groups", -1)) != view_report[method]["groups"]:
            raise ExperimentError(f"AgentProf {method} group count differs")
    return {
        "predictions": len(predictions),
        "risk_sum": total_risk,
        "views": view_report,
        "agentprof_count_conservation": True,
    }


def predict_fold(args: argparse.Namespace) -> dict[str, Any]:
    if args.reference_platform == args.target_platform:
        raise ExperimentError("reference and target platform must differ")
    if {args.reference_platform, args.target_platform} != set(PLATFORMS):
        raise ExperimentError("fold must be Windows↔Darwin")
    out = args.out.resolve()
    draws_path = out / "bootstrap-draws.jsonl.gz"
    out.mkdir(parents=True, exist_ok=True)
    for path in out.iterdir():
        if path.is_file() or path.is_symlink():
            path.unlink()
        elif path.is_dir():
            shutil.rmtree(path)
    projection_rows = read_jsonl(args.projection)
    validate_projection_rows(projection_rows)
    rows = select_tasks(projection_rows, args.tasks_per_platform)
    reference = [row for row in rows if row["platform"] == args.reference_platform]
    target = [row for row in rows if row["platform"] == args.target_platform]
    if not reference or not target:
        raise ExperimentError("empty reference or target projection")
    labels = load_platform_labels(args.reference_label, args.reference_platform)
    if any(row["operation_id"] in labels for row in target):
        raise ExperimentError("held-out target labels reached predictor")
    train_rows: list[dict[str, Any]] = []
    train_labels: list[int] = []
    for row in reference:
        value = labels.get(row["operation_id"])
        if value is not None:
            train_rows.append(row)
            train_labels.append(value)
    classes = Counter(train_labels)
    if set(classes) != {0, 1}:
        raise ExperimentError(f"reference labels need both classes, got {classes}")
    train_matrix, target_matrix, feature_report = feature_matrices(train_rows, target)
    model = LogisticRegression(
        C=1.0, penalty="l2", class_weight="balanced", solver="liblinear",
        max_iter=MAX_ITER, random_state=args.seed,
    )
    model.fit(train_matrix, np.asarray(train_labels, dtype=np.int8))
    if int(model.n_iter_[0]) >= MAX_ITER:
        raise ExperimentError("logistic regression did not converge")
    risks = model.predict_proba(target_matrix)[:, 1]
    if not np.all(np.isfinite(risks)) or np.any((risks < 0.0) | (risks > 1.0)):
        raise ExperimentError("invalid predicted probabilities")

    predictions = [
        {
            "operation_id": row["operation_id"],
            "task_id": row["task_id"],
            "trajectory_id": row["trajectory_id"],
            "platform": row["platform"],
            "risk": float(risk),
        }
        for row, risk in zip(target, risks, strict=True)
    ]
    write_jsonl(out / "predictions.jsonl", predictions)

    assignments: list[dict[str, Any]] = []
    group_acc: dict[str, dict[str, list[float]]] = {
        method: defaultdict(lambda: [0.0, 0.0]) for method in PROFILE_FIELDS
    }
    for row, risk in zip(target, risks, strict=True):
        keys = {method: method_key(row, method) for method in PROFILE_FIELDS}
        exact_repeat = 0 if row["repeat_state"] == "single" else 1
        assignments.append(
            {
                "operation_id": row["operation_id"],
                "task_id": row["task_id"],
                "trajectory_id": row["trajectory_id"],
                "platform": row["platform"],
                "session": row["session"],
                "domain": row["domain"],
                "application": row["application"],
                "risk": float(risk),
                "exact_repeat": exact_repeat,
                "groups": keys,
            }
        )
        for method, key in keys.items():
            group_acc[method][key][0] += float(risk)
            group_acc[method][key][1] += 1.0
    write_jsonl(out / "group-assignments.jsonl", assignments)
    group_summary = {
        method: {
            key: {"risk_sum": values[0], "operations": int(values[1]),
                  "density": values[0] / values[1]}
            for key, values in groups.items()
        }
        for method, groups in group_acc.items()
    }
    write_json(out / "group-summary.json", group_summary)
    profile_report = write_operations_and_verify_profiles(
        target, args.agentpprof_bin.resolve(), out / "profiles"
    )
    write_json(out / "profile-report.json", profile_report)
    model_report = {
        "status": "VALID",
        "reference_platform": args.reference_platform,
        "target_platform": args.target_platform,
        "reference_operations_total": len(reference),
        "reference_operations_scorable": len(train_rows),
        "reference_label_counts": {str(key): value for key, value in sorted(classes.items())},
        "target_operations": len(target),
        "target_tasks": len({row["task_id"] for row in target}),
        "target_trajectories": len({row["trajectory_id"] for row in target}),
        "C": 1.0,
        "penalty": "l2",
        "class_weight": "balanced",
        "solver": "liblinear",
        "max_iter": MAX_ITER,
        "n_iter": int(model.n_iter_[0]),
        "seed": args.seed,
        "features": feature_report,
        "pure_helpers": [
            "agentnet_code_action", "agentnet_action_target",
            "agentnet_action_phase", "repeat_features_for_signatures",
        ],
        "legacy_normalize_agentnet_used": False,
        "predictor_inputs": [str(args.projection.resolve()), str(args.reference_label.resolve())],
        "target_label_input": None,
    }
    write_json(out / "model-report.json", model_report)
    task_ids = sorted({row["task_id"] for row in assignments})
    write_draw_specs(draws_path, task_ids, args.attempts, args.seed)
    digests = fold_artifact_digests(out)
    write_json(out / "label-blind-digests.json", digests)
    return {"status": "VALID", "model": model_report, "profiles": profile_report,
            "digests": digests}


def read_draw_specs(path: Path) -> tuple[dict[str, Any], list[dict[str, int]]]:
    with gzip.open(path, "rt", encoding="utf-8") as source:
        rows = [json.loads(line) for line in source]
    if not rows or rows[0].get("type") != "header":
        raise ExperimentError(f"{path}: missing draw header")
    draws = [row for row in rows[1:] if row.get("type") == "draw"]
    return rows[0], draws


def metric_from_blocks(counts: np.ndarray, positives: np.ndarray) -> dict[str, float]:
    counts = counts.astype(np.float64, copy=False)
    positives = positives.astype(np.float64, copy=False)
    total = float(counts.sum())
    total_positive = float(positives.sum())
    if total <= 0 or total_positive <= 0 or total_positive >= total:
        raise ExperimentError("metric population needs positive and negative operations")
    cumulative_count = 0.0
    cumulative_positive = 0.0
    ap = 0.0
    recall30_positive = 0.0
    budget = 0.30 * total
    work50 = 1.0
    reached50 = False
    for count, positive in zip(counts, positives, strict=True):
        if count <= 0:
            continue
        end_count = cumulative_count + float(count)
        end_positive = cumulative_positive + float(positive)
        if positive > 0:
            ap += (float(positive) / total_positive) * (end_positive / end_count)
        if end_count <= budget + 1e-12:
            recall30_positive = end_positive
        if not reached50 and end_positive >= 0.50 * total_positive:
            work50 = end_count / total
            reached50 = True
        cumulative_count = end_count
        cumulative_positive = end_positive
    return {
        "average_precision": ap,
        "recall_at_30": recall30_positive / total_positive,
        "work_to_50": work50,
        "operations": total,
        "positives": total_positive,
    }


def blocks_by_score(
    scores: np.ndarray, counts: np.ndarray, positives: np.ndarray
) -> tuple[np.ndarray, np.ndarray]:
    valid = counts > 0
    if not np.any(valid):
        raise ExperimentError("no scored groups")
    score = scores[valid]
    count = counts[valid]
    positive = positives[valid]
    order = np.argsort(-score, kind="mergesort")
    score = score[order]
    count = count[order]
    positive = positive[order]
    starts = np.concatenate(([0], np.flatnonzero(score[1:] != score[:-1]) + 1))
    return np.add.reduceat(count, starts), np.add.reduceat(positive, starts)


def grouped_metric(
    state: dict[str, Any], method: str, all_weights: np.ndarray,
    scored_weights: np.ndarray,
) -> dict[str, float]:
    all_groups = state["all_group_index"][method]
    scored_groups = state["scored_group_index"][method]
    group_count = state["group_count"][method]
    all_count = np.bincount(all_groups, weights=all_weights, minlength=group_count)
    risk_sum = np.bincount(
        all_groups, weights=all_weights * state["all_risk"], minlength=group_count
    )
    density = np.divide(
        risk_sum, all_count, out=np.full(group_count, -np.inf), where=all_count > 0
    )
    scored_count = np.bincount(
        scored_groups, weights=scored_weights, minlength=group_count
    )
    positive = np.bincount(
        scored_groups,
        weights=scored_weights * state["scored_labels"],
        minlength=group_count,
    )
    blocks = blocks_by_score(density, scored_count, positive)
    return metric_from_blocks(*blocks)


def fixed_score_metric(
    block_index: np.ndarray, block_count: int, scored_weights: np.ndarray,
    labels: np.ndarray,
) -> dict[str, float]:
    counts = np.bincount(block_index, weights=scored_weights, minlength=block_count)
    positives = np.bincount(
        block_index, weights=scored_weights * labels, minlength=block_count
    )
    return metric_from_blocks(counts, positives)


def fixed_score_blocks(scores: np.ndarray) -> tuple[np.ndarray, int]:
    order = np.argsort(-scores, kind="mergesort")
    sorted_scores = scores[order]
    starts = np.concatenate(([0], np.flatnonzero(sorted_scores[1:] != sorted_scores[:-1]) + 1))
    sorted_block = np.empty(len(scores), dtype=np.int32)
    for block, (start, end) in enumerate(
        zip(starts, np.append(starts[1:], len(scores)), strict=True)
    ):
        sorted_block[start:end] = block
    result = np.empty(len(scores), dtype=np.int32)
    result[order] = sorted_block
    return result, len(starts)


def build_score_state(
    assignments: list[dict[str, Any]], target_labels: dict[str, int | None]
) -> dict[str, Any]:
    task_ids = sorted({row["task_id"] for row in assignments})
    task_lookup = {task_id: index for index, task_id in enumerate(task_ids)}
    all_task_index = np.asarray([task_lookup[row["task_id"]] for row in assignments], dtype=np.int32)
    session_ids = sorted({row["session"] for row in assignments})
    session_lookup = {session_id: index for index, session_id in enumerate(session_ids)}
    all_session_index = np.asarray(
        [session_lookup[row["session"]] for row in assignments], dtype=np.int32
    )
    all_risk = np.asarray([float(row["risk"]) for row in assignments], dtype=np.float64)
    scorable_positions = np.asarray(
        [index for index, row in enumerate(assignments)
         if target_labels.get(row["operation_id"]) is not None],
        dtype=np.int64,
    )
    if len(scorable_positions) == 0:
        raise ExperimentError("held-out labels have no scorable operations")
    scored_labels = np.asarray(
        [target_labels[assignments[index]["operation_id"]] for index in scorable_positions],
        dtype=np.float64,
    )
    if set(np.unique(scored_labels)) != {0.0, 1.0}:
        raise ExperimentError("held-out labels need positive and negative operations")
    state: dict[str, Any] = {
        "task_ids": task_ids,
        "task_count": len(task_ids),
        "session_ids": session_ids,
        "session_count": len(session_ids),
        "all_task_index": all_task_index,
        "all_session_index": all_session_index,
        "all_risk": all_risk,
        "scored_task_index": all_task_index[scorable_positions],
        "scored_labels": scored_labels,
        "scorable_positions": scorable_positions,
        "all_group_index": {},
        "scored_group_index": {},
        "group_count": {},
    }
    for method in PROFILE_FIELDS:
        indices, labels = group_index([row["groups"][method] for row in assignments])
        state["all_group_index"][method] = indices
        state["scored_group_index"][method] = indices[scorable_positions]
        state["group_count"][method] = len(labels)
    risk_blocks, risk_count = fixed_score_blocks(all_risk[scorable_positions])
    repeat_scores = np.asarray(
        [float(assignments[index]["exact_repeat"]) for index in scorable_positions],
        dtype=np.float64,
    )
    repeat_blocks, repeat_count = fixed_score_blocks(repeat_scores)
    state["risk_blocks"] = risk_blocks
    state["risk_block_count"] = risk_count
    state["repeat_blocks"] = repeat_blocks
    state["repeat_block_count"] = repeat_count
    return state


def all_metrics(state: dict[str, Any], multiplicity: np.ndarray) -> dict[str, dict[str, float]]:
    all_weights = multiplicity[state["all_task_index"]].astype(np.float64)
    scored_weights = multiplicity[state["scored_task_index"]].astype(np.float64)
    total_positive = float(np.dot(scored_weights, state["scored_labels"]))
    total = float(scored_weights.sum())
    if total_positive <= 0 or total_positive >= total:
        raise ExperimentError("bootstrap draw lacks one class")
    result = {
        method: grouped_metric(state, method, all_weights, scored_weights)
        for method in PROFILE_FIELDS
    }
    result["ungrouped_risk"] = fixed_score_metric(
        state["risk_blocks"], state["risk_block_count"], scored_weights,
        state["scored_labels"],
    )
    result["exact_repeat"] = fixed_score_metric(
        state["repeat_blocks"], state["repeat_block_count"], scored_weights,
        state["scored_labels"],
    )
    return result


def grouped_secondary_diagnostics(
    state: dict[str, Any], method: str, rank_by: str = "density"
) -> dict[str, Any]:
    all_groups = state["all_group_index"][method]
    scored_groups = state["scored_group_index"][method]
    group_count = state["group_count"][method]
    all_count = np.bincount(all_groups, minlength=group_count).astype(np.float64)
    risk_sum = np.bincount(
        all_groups, weights=state["all_risk"], minlength=group_count
    )
    density = np.divide(
        risk_sum, all_count, out=np.full(group_count, -np.inf), where=all_count > 0
    )
    scored_count = np.bincount(scored_groups, minlength=group_count).astype(np.float64)
    positive = np.bincount(
        scored_groups, weights=state["scored_labels"], minlength=group_count
    )
    if rank_by == "density":
        score = density
    elif rank_by == "mass":
        score = risk_sum
    else:
        raise ExperimentError(f"unexpected secondary group rank mode {rank_by}")
    valid_groups = np.flatnonzero(scored_count > 0)
    scores = score[valid_groups]
    order = np.argsort(-scores, kind="mergesort")
    ranked_groups = valid_groups[order]
    ranked_scores = scores[order]
    starts = np.concatenate(
        ([0], np.flatnonzero(ranked_scores[1:] != ranked_scores[:-1]) + 1)
    )
    total_positive = float(positive.sum())
    cumulative_positive = 0.0
    groups_to_50 = len(ranked_groups)
    for start, end in zip(
        starts, np.append(starts[1:], len(ranked_groups)), strict=True
    ):
        cumulative_positive += float(positive[ranked_groups[start:end]].sum())
        if cumulative_positive >= 0.5 * total_positive:
            groups_to_50 = int(end)
            break
    first_end = int(starts[1]) if len(starts) > 1 else len(ranked_groups)
    hot_groups = ranked_groups[:first_end]
    hot_session_counts = sorted(
        int(len(np.unique(state["all_session_index"][all_groups == group])))
        for group in hot_groups
    )
    return {
        "ranking": rank_by,
        "groups": group_count,
        "scored_groups": int(len(valid_groups)),
        "groups_to_50_percent_positives": groups_to_50,
        "hot_score_tie_groups": int(len(hot_groups)),
        "sessions_per_hot_group": {
            "values": hot_session_counts,
            "minimum": min(hot_session_counts),
            "median": float(np.median(hot_session_counts)),
            "maximum": max(hot_session_counts),
        },
    }


def secondary_fold_diagnostics(
    assignments: list[dict[str, Any]], target_labels: dict[str, int | None],
    state: dict[str, Any],
) -> dict[str, Any]:
    grouped = {
        method: grouped_secondary_diagnostics(state, method)
        for method in PROFILE_FIELDS
    }
    mass_group_opening = {
        method: grouped_secondary_diagnostics(state, method, rank_by="mass")
        for method in PROFILE_FIELDS
    }

    domain_counts: dict[str, Counter[str]] = defaultdict(Counter)
    domain_scorable_tasks: dict[str, set[str]] = defaultdict(set)
    for row in assignments:
        domain = str(row["domain"])
        value = target_labels.get(row["operation_id"])
        if value is None:
            domain_counts[domain]["unresolved"] += 1
        elif value == 1:
            domain_counts[domain]["positive"] += 1
            domain_scorable_tasks[domain].add(str(row["task_id"]))
        else:
            domain_counts[domain]["negative"] += 1
            domain_scorable_tasks[domain].add(str(row["task_id"]))
    annotation_by_domain = {
        domain: {
            "positive": counts["positive"],
            "negative": counts["negative"],
            "unresolved": counts["unresolved"],
            "scorable_tasks": len(domain_scorable_tasks[domain]),
        }
        for domain, counts in sorted(domain_counts.items())
    }

    per_domain: dict[str, Any] = {}
    for domain, task_ids in sorted(domain_scorable_tasks.items()):
        if len(task_ids) < PER_DOMAIN_MIN_SCORABLE_TASKS:
            continue
        domain_assignments = [row for row in assignments if row["domain"] == domain]
        try:
            domain_state = build_score_state(domain_assignments, target_labels)
            metrics = all_metrics(
                domain_state, np.ones(domain_state["task_count"], dtype=np.int64)
            )
        except ExperimentError:
            continue
        per_domain[domain] = {
            "tasks": domain_state["task_count"],
            "scorable_tasks": len(task_ids),
            "scorable_operations": int(len(domain_state["scorable_positions"])),
            "positives": int(domain_state["scored_labels"].sum()),
            "metrics": {
                method: metrics[method]
                for method in ("semantic", "raw_action", "ungrouped_risk")
            },
        }
    return {
        "grouped_views": grouped,
        "additive_risk_mass_group_opening": mass_group_opening,
        "annotation_by_domain": annotation_by_domain,
        "per_domain_min_scorable_tasks": PER_DOMAIN_MIN_SCORABLE_TASKS,
        "eligible_per_domain": per_domain,
    }


def effect_row(attempt: int, metrics: dict[str, dict[str, float]]) -> dict[str, float | int]:
    semantic = metrics["semantic"]
    raw = metrics["raw_action"]
    risk = metrics["ungrouped_risk"]
    return {
        "attempt": attempt,
        "semantic_minus_raw_ap": semantic["average_precision"] - raw["average_precision"],
        "semantic_minus_raw_recall30": semantic["recall_at_30"] - raw["recall_at_30"],
        "raw_minus_semantic_work50": raw["work_to_50"] - semantic["work_to_50"],
        "semantic_minus_ungrouped_ap": semantic["average_precision"] - risk["average_precision"],
    }


def boot_worker(spec: tuple[int, int]) -> dict[str, float | int] | None:
    if _BOOT_STATE is None:
        raise RuntimeError("bootstrap worker state missing")
    attempt, seed = spec
    rng = np.random.default_rng(seed)
    draws = rng.integers(0, _BOOT_STATE["task_count"], size=_BOOT_STATE["task_count"])
    multiplicity = np.bincount(draws, minlength=_BOOT_STATE["task_count"])
    try:
        metrics = all_metrics(_BOOT_STATE, multiplicity)
    except ExperimentError:
        return None
    return effect_row(attempt, metrics)


def percentile_interval(values: Sequence[float]) -> list[float]:
    array = np.asarray(values, dtype=np.float64)
    return [float(np.quantile(array, 0.025)), float(np.quantile(array, 0.975))]


def score_fold(args: argparse.Namespace) -> tuple[dict[str, Any], int]:
    fold_dir = args.fold_dir.resolve()
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=True)
    assignments = read_jsonl(fold_dir / "group-assignments.jsonl")
    if not assignments:
        raise ExperimentError("empty group assignments")
    conservation = validate_label_blind_artifacts(fold_dir, assignments)
    target_platform = str(assignments[0]["platform"])
    if any(row["platform"] != target_platform for row in assignments):
        raise ExperimentError("fold assignments mix target platforms")
    labels = load_platform_labels(args.target_label, target_platform)
    target_ids = {row["operation_id"] for row in assignments}
    if not target_ids <= set(labels):
        raise ExperimentError("target label file does not cover assignments")
    state = build_score_state(assignments, labels)
    header, draws = read_draw_specs(fold_dir / "bootstrap-draws.jsonl.gz")
    if header.get("task_ids") != state["task_ids"]:
        raise ExperimentError("bootstrap header task IDs differ from assignments")

    base = all_metrics(state, np.ones(state["task_count"], dtype=np.int64))
    secondary = secondary_fold_diagnostics(assignments, labels, state)
    global _BOOT_STATE
    _BOOT_STATE = state
    specs = [(int(row["attempt"]), int(row["seed"])) for row in draws]
    valid: list[dict[str, float | int]] = []
    attempts_examined = 0
    batch_size = max(256, args.jobs * 32)
    if args.jobs == 1:
        for start in range(0, len(specs), batch_size):
            batch = specs[start : start + batch_size]
            results = [boot_worker(spec) for spec in batch]
            attempts_examined += len(batch)
            valid.extend(row for row in results if row is not None)
            if len(valid) >= args.required_valid:
                break
    else:
        context = mp.get_context("fork")
        with context.Pool(processes=args.jobs) as pool:
            for start in range(0, len(specs), batch_size):
                batch = specs[start : start + batch_size]
                results = pool.map(
                    boot_worker, batch,
                    chunksize=max(1, len(batch) // (args.jobs * 4)),
                )
                attempts_examined += len(batch)
                valid.extend(row for row in results if row is not None)
                if len(valid) >= args.required_valid:
                    break
    if len(valid) < args.required_valid:
        status = {
            "status": "INCOMPLETE",
            "target_platform": target_platform,
            "valid_draws": len(valid),
            "available_attempts": len(draws),
            "attempts_examined": attempts_examined,
            "required_valid": args.required_valid,
        }
        write_json(out / "need-more.json", status)
        return status, 3
    valid = valid[: args.required_valid]
    effects = effect_row(-1, base)
    effect_intervals = {
        key: percentile_interval([float(row[key]) for row in valid])
        for key in effects if key != "attempt"
    }
    coverage = {
        "target_operations": len(assignments),
        "scorable_operations": int(len(state["scorable_positions"])),
        "unresolved_operations": len(assignments) - int(len(state["scorable_positions"])),
        "positives": int(state["scored_labels"].sum()),
        "negatives": int(len(state["scored_labels"]) - state["scored_labels"].sum()),
        "tasks": state["task_count"],
        "trajectories": state["session_count"],
    }
    coverage["annotation_coverage"] = (
        coverage["scorable_operations"] / coverage["target_operations"]
    )
    coverage["positive_prevalence"] = coverage["positives"] / coverage["scorable_operations"]
    report = {
        "status": "VALID",
        "target_platform": target_platform,
        "coverage": coverage,
        "base_metrics": base,
        "base_effects": effects,
        "effect_intervals_95": effect_intervals,
        "valid_draws": len(valid),
        "available_attempts": len(draws),
        "attempts_examined": attempts_examined,
        "tie_policy": "complete exact-density blocks; display keys never break metric ties",
        "label_blind_artifact_validation": conservation,
        "secondary_diagnostics": secondary,
    }
    write_json(out / "metrics.json", report)
    with gzip.open(out / "bootstrap-effects.jsonl.gz", "wt", encoding="utf-8") as output:
        for row in valid:
            output.write(json.dumps(row, separators=(",", ":"), sort_keys=True) + "\n")
    lines = [
        f"# AgentNet held-out fold: {target_platform}", "",
        "- execution: `VALID`",
        f"- tasks: {coverage['tasks']:,}",
        f"- trajectories: {coverage['trajectories']:,}",
        f"- operations: {coverage['target_operations']:,}",
        f"- scorable: {coverage['scorable_operations']:,}",
        f"- positives: {coverage['positives']:,}",
        f"- valid paired task bootstraps: {len(valid):,}", "",
        "## Base effects", "", "```json",
        json.dumps(effects, indent=2, sort_keys=True), "```", "",
        "## 95% intervals", "", "```json",
        json.dumps(effect_intervals, indent=2, sort_keys=True), "```",
    ]
    (out / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (out / "need-more.json").unlink(missing_ok=True)
    return report, 0


def run_child(command: list[str], allowed: set[int] = {0}) -> tuple[dict[str, Any], int]:
    completed = subprocess.run(command, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if completed.returncode not in allowed:
        raise ExperimentError(
            f"child failed ({completed.returncode}): {' '.join(command)}\n"
            f"stdout:\n{completed.stdout}\nstderr:\n{completed.stderr}"
        )
    try:
        status = json.loads(completed.stdout)
    except json.JSONDecodeError as error:
        raise ExperimentError(f"child returned invalid status: {completed.stdout}") from error
    return status, completed.returncode


def fold_support(metrics: dict[str, Any]) -> bool:
    intervals = metrics["effect_intervals_95"]
    return all(
        intervals[key][0] > 0.0
        for key in (
            "semantic_minus_raw_ap",
            "semantic_minus_raw_recall30",
            "raw_minus_semantic_work50",
            "semantic_minus_ungrouped_ap",
        )
    )


def fold_adverse(metrics: dict[str, Any]) -> bool:
    intervals = metrics["effect_intervals_95"]
    return (
        intervals["semantic_minus_raw_ap"][1] < 0.0
        or intervals["semantic_minus_ungrouped_ap"][1] < 0.0
    )


def coordinator(args: argparse.Namespace, mode: str) -> dict[str, Any]:
    source = args.source.resolve()
    out = args.out.resolve()
    if args.bootstraps <= 0 or args.max_bootstrap_attempts < args.bootstraps:
        raise ExperimentError(
            "bootstrap count must be positive and the attempt cap cannot be smaller"
        )
    tasks_per_platform = getattr(args, "tasks_per_platform", None)
    if mode == "preflight":
        if tasks_per_platform is None or tasks_per_platform <= 0:
            raise ExperimentError("preflight requires a positive task subset per platform")
        if any(tasks_per_platform >= EXPECTED_TASKS[platform] for platform in PLATFORMS):
            raise ExperimentError("preflight subset must be smaller than each full population")
        source_validation = {
            "mode": "fixed_subset",
            "tasks_per_platform": tasks_per_platform,
        }
    elif mode == "full":
        if tasks_per_platform is not None:
            raise ExperimentError("full run cannot use a task subset")
        if (
            args.bootstraps != 10_000
            or args.max_bootstrap_attempts != 50_000
            or args.seed != 4204
        ):
            raise ExperimentError(
                "full run requires 10000 valid draws, 50000 maximum attempts, and seed 4204"
            )
        source_validation = validate_full_source(source)
    else:
        raise ExperimentError(f"unexpected coordinator mode {mode}")
    out.mkdir(parents=True, exist_ok=True)
    for stale in ("execution-status.json", "metrics.json", "report.md", "need-more.json"):
        (out / stale).unlink(missing_ok=True)
    script = Path(__file__).resolve()
    projection = source / "projection.jsonl"
    fold_specs = (("windows", "darwin"), ("darwin", "windows"))
    fold_dirs: dict[str, Path] = {}
    for reference, target in fold_specs:
        fold_dir = out / "folds" / f"{reference}-to-{target}"
        fold_dirs[target] = fold_dir
        command = [
            sys.executable, str(script), "predict-fold",
            "--projection", str(projection),
            "--reference-label", str(source / "labels" / f"{reference}.jsonl"),
            "--reference-platform", reference,
            "--target-platform", target,
            "--agentpprof-bin", str(args.agentpprof_bin.resolve()),
            "--out", str(fold_dir),
            "--attempts", str(args.max_bootstrap_attempts),
            "--seed", str(args.seed),
        ]
        if tasks_per_platform is not None:
            command.extend(["--tasks-per-platform", str(tasks_per_platform)])
        run_child(command)

    fold_metrics: dict[str, Any] = {}
    for target in PLATFORMS:
        fold_dir = fold_dirs[target]
        score_out = out / "scores" / target
        command = [
            sys.executable, str(script), "score-fold",
            "--fold-dir", str(fold_dir),
            "--target-label", str(source / "labels" / f"{target}.jsonl"),
            "--out", str(score_out),
            "--required-valid", str(args.bootstraps),
            "--jobs", str(args.jobs),
        ]
        status, code = run_child(command, {0, 3})
        if code == 3:
            incomplete = {
                "status": "INCOMPLETE",
                "mode": mode,
                "target_platform": target,
                **status,
            }
            write_json(out / "execution-status.json", incomplete)
            raise IncompleteExperiment(
                f"{target}: only {status['valid_draws']} valid draws in the fixed attempt cap"
            )
        fold_metrics[target] = status

    digest_checks: dict[str, Any] = {}
    for target, fold_dir in fold_dirs.items():
        before = read_json(fold_dir / "label-blind-digests.json")
        after = fold_artifact_digests(fold_dir)
        if before != after:
            raise ExperimentError(f"{target}: scoring changed label-blind artifacts")
        digest_checks[target] = {"unchanged_after_target_scoring": True, "digests": after}

    if mode == "preflight":
        verdict = "NOT_EVALUATED_PREFLIGHT"
    elif all(fold_support(fold_metrics[platform]) for platform in PLATFORMS):
        verdict = "SUPPORTED"
    elif any(fold_adverse(fold_metrics[platform]) for platform in PLATFORMS):
        verdict = "CONTRADICTED"
    else:
        windows = fold_metrics["windows"]["base_effects"]
        darwin = fold_metrics["darwin"]["base_effects"]
        both_raw_adverse = all(
            effects["semantic_minus_raw_ap"] < 0.0
            and effects["raw_minus_semantic_work50"] < 0.0
            for effects in (windows, darwin)
        )
        verdict = "CONTRADICTED" if both_raw_adverse else "MIXED"
    stratified = {
        key: 0.5 * (
            float(fold_metrics["windows"]["base_effects"][key])
            + float(fold_metrics["darwin"]["base_effects"][key])
        )
        for key in fold_metrics["windows"]["base_effects"]
        if key != "attempt"
    }
    status = {
        "status": "VALID",
        "mode": mode,
        "scientific_verdict": verdict,
        "tested_hypothesis_only": mode == "full",
        "source_validation": source_validation,
        "folds": fold_metrics,
        "secondary_equal_weight_fold_effect": stratified,
        "cross_model_pooled_ranking": False,
        "label_boundary": digest_checks,
    }
    if mode == "full" and any(
        int(fold_metrics[platform]["valid_draws"]) != 10_000 for platform in PLATFORMS
    ):
        raise ExperimentError("full run did not complete exactly 10000 valid draws per fold")
    write_json(out / "metrics.json", status)
    write_json(out / "execution-status.json", {
        "status": "VALID", "mode": mode, "scientific_verdict": verdict
    })
    lines = [
        f"# AgentNet {mode} report", "",
        "- execution: `VALID`",
        f"- scientific verdict: `{verdict}`",
        "- two independently trained model scores were never pooled into one ranking",
        "- target scoring did not change any label-blind prediction/profile/draw artifact",
        "", "## Fold results", "",
    ]
    for platform in PLATFORMS:
        value = fold_metrics[platform]
        lines.extend([
            f"### Held-out {platform}", "",
            f"- tasks: {value['coverage']['tasks']:,}",
            f"- trajectories: {value['coverage']['trajectories']:,}",
            f"- operations: {value['coverage']['target_operations']:,}",
            f"- scorable: {value['coverage']['scorable_operations']:,}",
            f"- positives: {value['coverage']['positives']:,}",
            f"- valid draws: {value['valid_draws']:,}", "", "```json",
            json.dumps(value["effect_intervals_95"], indent=2, sort_keys=True),
            "```", "",
        ])
    lines.extend([
        "## Scope", "",
        (
            "This preflight validates execution only; its metrics cannot support or "
            "contradict the hypothesis."
            if mode == "preflight"
            else "This verdict applies only to the approved AgentNet cross-platform construction."
        ),
        "It does not change the paper thesis, four RQs, positive RQ2 hypothesis, or story.",
    ])
    (out / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return status


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    prepare_parser = sub.add_parser("prepare")
    prepare_parser.add_argument("--revision", required=True)
    prepare_parser.add_argument("--out", type=Path, required=True)

    predict = sub.add_parser("predict-fold")
    predict.add_argument("--projection", type=Path, required=True)
    predict.add_argument("--reference-label", type=Path, required=True)
    predict.add_argument("--reference-platform", choices=PLATFORMS, required=True)
    predict.add_argument("--target-platform", choices=PLATFORMS, required=True)
    predict.add_argument("--agentpprof-bin", type=Path, required=True)
    predict.add_argument("--out", type=Path, required=True)
    predict.add_argument("--attempts", type=int, required=True)
    predict.add_argument("--seed", type=int, required=True)
    predict.add_argument("--tasks-per-platform", type=int)

    score = sub.add_parser("score-fold")
    score.add_argument("--fold-dir", type=Path, required=True)
    score.add_argument("--target-label", type=Path, required=True)
    score.add_argument("--out", type=Path, required=True)
    score.add_argument("--required-valid", type=int, required=True)
    score.add_argument("--jobs", type=int, default=max(1, min(16, os.cpu_count() or 1)))

    for name in ("preflight", "full"):
        run = sub.add_parser(name)
        run.add_argument("--source", type=Path, required=True)
        run.add_argument("--agentpprof-bin", type=Path, required=True)
        run.add_argument("--out", type=Path, required=True)
        run.add_argument("--bootstraps", type=int, required=True)
        run.add_argument("--max-bootstrap-attempts", type=int, required=True)
        run.add_argument("--seed", type=int, required=True)
        run.add_argument("--jobs", type=int, default=max(1, min(16, os.cpu_count() or 1)))
        if name == "preflight":
            run.add_argument("--tasks-per-platform", type=int, default=256)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        if args.command == "prepare":
            status = prepare(args)
            code = 0
        elif args.command == "predict-fold":
            status = predict_fold(args)
            code = 0
        elif args.command == "score-fold":
            status, code = score_fold(args)
        elif args.command in {"preflight", "full"}:
            status = coordinator(args, args.command)
            code = 0
        else:
            raise ExperimentError(f"unknown command {args.command}")
    except IncompleteExperiment as error:
        print(json.dumps({"status": "INCOMPLETE", "error": str(error)}, sort_keys=True))
        return 3
    except (ExperimentError, subprocess.CalledProcessError, OSError, ValueError) as error:
        print(json.dumps({"status": "ERROR", "error": str(error)}, sort_keys=True))
        return 1
    print(json.dumps(status, sort_keys=True))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
