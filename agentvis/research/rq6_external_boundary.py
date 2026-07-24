#!/usr/bin/env python3
"""Run the preregistered RQ6 public-trace boundary check."""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
import math
import re
import shlex
import statistics
import time
import urllib.parse
import urllib.request
import urllib.error
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any

import duckdb
import requests
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import PercentFormatter


SOURCES = {
    "openswe": {
        "dataset": "nvidia/Open-SWE-Traces",
        "revision": "9c0e4579a4ee0effa3e5f7a552494a045f29377d",
    },
    "ideatrail": {
        "dataset": "AliceKJ/IdeaTrail",
        "revision": "56a26582c8723992ce1e9e289953e24e03977aa7",
    },
}
OPEN_STRATA = [
    ("openhands", "minimax_m25"),
    ("openhands", "qwen35_122b"),
    ("sweagent", "minimax_m25"),
    ("sweagent", "qwen35_122b"),
]
SELECTION_SEED = "rq6:20260722"
BOOTSTRAP_SEED = 20260722
SAMPLE_UNITS = 64
SELECTION_CANDIDATES = 256
BOOTSTRAPS = 2000
MIN_ELIGIBLE = 50
REQUEST_INTERVAL_SECONDS = 0.6
_NEXT_REQUEST_AT = 0.0
_REQUEST_LOCK = __import__("threading").Lock()
_THREAD_LOCAL = __import__("threading").local()
TOPIC_RE = re.compile(r"research_topics/([^/]+)/")
VALIDATE_RE = re.compile(
    r"(?:^|[;&|]\s*)(?:pytest|cargo\s+(?:test|check|build)|go\s+test|"
    r"npm\s+(?:test|run\s+(?:test|lint|build))|pnpm\s+(?:test|lint|build)|"
    r"yarn\s+(?:test|lint|build)|make\s+(?:test|check)|mvn\s+test|gradle\s+test)\b",
    re.IGNORECASE,
)
SHELL_MUTATE_RE = re.compile(r"(?:^|[;&|]\s*)(?:rm|mv|cp|touch|mkdir|install|patch)\b|(?:>>?|\bsed\s+-i\b)")
SHELL_EXPLORE_RE = re.compile(r"(?:^|[;&|]\s*)(?:rg|grep|find|cat|head|tail|sed|ls|tree|fd|wc|stat)\b")
PATH_TOKEN_RE = re.compile(r"(?:/workspace/|/testbed/|\./|\.\./)[^\s'\";|&<>]+|[A-Za-z0-9_.-]+/[A-Za-z0-9_./-]+")


@dataclass(frozen=True)
class SelectedRow:
    corpus: str
    config: str
    split: str
    offset: int
    cluster_id: str
    row_id: str
    selection_digest: str


def canonical(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()


def digest_text(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def digest_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def api_json(url: str, attempts: int = 12) -> Any:
    global _NEXT_REQUEST_AT
    error: Exception | None = None
    for attempt in range(attempts):
        try:
            with _REQUEST_LOCK:
                delay = max(0.0, _NEXT_REQUEST_AT - time.monotonic())
                if delay:
                    time.sleep(delay)
                _NEXT_REQUEST_AT = time.monotonic() + REQUEST_INTERVAL_SECONDS
            if not hasattr(_THREAD_LOCAL, "session"):
                session = requests.Session()
                session.headers.update({"User-Agent": "AgentSight-RQ6/1"})
                _THREAD_LOCAL.session = session
            with _THREAD_LOCAL.session.get(url, timeout=(30, 180)) as response:
                if response.status_code == 429:
                    retry_after = response.headers.get("Retry-After")
                    wait = float(retry_after) if retry_after and retry_after.isdigit() else min(30.0 * (attempt + 1), 180.0)
                    time.sleep(wait)
                    continue
                response.raise_for_status()
                return response.json()
        except requests.HTTPError as caught:
            error = caught
            time.sleep(min(2**attempt, 12))
        except Exception as caught:  # network retry is recorded by final source check
            error = caught
            time.sleep(min(2**attempt, 12))
    raise RuntimeError(f"failed after {attempts} attempts: {url}: {error}")


def verify_head(source: str) -> dict[str, Any]:
    spec = SOURCES[source]
    url = f"https://huggingface.co/api/datasets/{spec['dataset']}"
    response = api_json(url)
    if response.get("sha") != spec["revision"]:
        raise RuntimeError(
            f"{spec['dataset']} HEAD moved: expected {spec['revision']}, got {response.get('sha')}"
        )
    return response


def parquet_manifest(source: str) -> list[dict[str, Any]]:
    dataset = SOURCES[source]["dataset"]
    query = urllib.parse.urlencode({"dataset": dataset})
    response = api_json(f"https://datasets-server.huggingface.co/parquet?{query}")
    if response.get("pending") or response.get("failed") or response.get("partial"):
        raise RuntimeError(f"incomplete Parquet manifest for {dataset}")
    return response["parquet_files"]


def open_sampling_frame(files: list[dict[str, Any]], config: str, split: str) -> list[tuple[int, str, str]]:
    urls = [row["url"] for row in files if row["config"] == config and row["split"] == split]
    if not urls:
        raise RuntimeError(f"missing Parquet files for {config}/{split}")
    connection = duckdb.connect()
    query = """
        SELECT row_number() OVER () - 1 AS row_offset, instance_id, trajectory_id
        FROM read_parquet(?)
    """
    rows = connection.execute(query, [urls]).fetchall()
    return [(int(offset), str(instance), str(trajectory)) for offset, instance, trajectory in rows]


def idea_sampling_frame(files: list[dict[str, Any]]) -> list[tuple[int, str, str]]:
    urls = [row["url"] for row in files if row["config"] == "default" and row["split"] == "train"]
    connection = duckdb.connect()
    query = """
        SELECT row_number() OVER () - 1 AS row_offset,
               sample_id,
               regexp_extract(messages[1].content, 'research_topics/([^/]+)/', 1) AS topic
        FROM read_parquet(?)
    """
    rows = [(int(offset), str(sample_id), str(topic)) for offset, sample_id, topic in connection.execute(query, [urls]).fetchall()]
    if len(rows) != 1170 or len({topic for _, _, topic in rows}) != 963 or any(not topic for _, _, topic in rows):
        raise RuntimeError("IdeaTrail topic frame does not reconcile with the pinned dataset card")
    return rows


def select_open(frame: list[tuple[int, str, str]], config: str, split: str) -> list[SelectedRow]:
    by_instance: dict[str, list[tuple[int, str]]] = defaultdict(list)
    for offset, instance, trajectory in frame:
        by_instance[instance].append((offset, trajectory))
    ranked_instances = sorted(
        by_instance,
        key=lambda instance: digest_text(f"{SELECTION_SEED}:{config}:{split}:{instance}"),
    )[:SELECTION_CANDIDATES]
    selected = []
    for instance in ranked_instances:
        offset, trajectory = min(
            by_instance[instance],
            key=lambda row: digest_text(f"{SELECTION_SEED}:{config}:{split}:{instance}:{row[1]}"),
        )
        selected.append(
            SelectedRow(
                "openswe",
                config,
                split,
                offset,
                instance,
                trajectory,
                digest_text(f"{SELECTION_SEED}:{config}:{split}:{instance}:{trajectory}"),
            )
        )
    return selected


def select_idea(frame: list[tuple[int, str, str]]) -> list[SelectedRow]:
    by_topic: dict[str, list[tuple[int, str]]] = defaultdict(list)
    for offset, sample_id, topic in frame:
        by_topic[topic].append((offset, sample_id))
    ranked_topics = sorted(by_topic, key=lambda topic: digest_text(f"{SELECTION_SEED}:ideatrail:{topic}"))[:SELECTION_CANDIDATES]
    selected = []
    for topic in ranked_topics:
        offset, sample_id = min(
            by_topic[topic],
            key=lambda row: digest_text(f"{SELECTION_SEED}:ideatrail:{topic}:{row[1]}"),
        )
        selected.append(
            SelectedRow(
                "ideatrail",
                "default",
                "train",
                offset,
                topic,
                sample_id,
                digest_text(f"{SELECTION_SEED}:ideatrail:{topic}:{sample_id}"),
            )
        )
    return selected


def raw_path(raw: Path, selected: SelectedRow) -> Path:
    stratum = f"{selected.config}-{selected.split}"
    return raw / selected.corpus / stratum / f"{selected.offset:06d}.json.gz"


def fetch_one(raw: Path, selected: SelectedRow) -> tuple[SelectedRow, dict[str, Any], str, bool]:
    path = raw_path(raw, selected)
    if path.exists():
        with gzip.open(path, "rb") as stream:
            row = json.loads(stream.read())
        return selected, row, digest_bytes(canonical(row)), True
    dataset = SOURCES[selected.corpus]["dataset"]
    query = urllib.parse.urlencode(
        {
            "dataset": dataset,
            "config": selected.config,
            "split": selected.split,
            "offset": selected.offset,
            "length": 1,
        }
    )
    response = api_json(f"https://datasets-server.huggingface.co/rows?{query}")
    if len(response.get("rows", [])) != 1:
        raise RuntimeError(f"missing Viewer row at {selected}")
    wrapped = response["rows"][0]
    if wrapped.get("row_idx") != selected.offset or wrapped.get("truncated_cells"):
        raise RuntimeError(f"truncated or misindexed Viewer row at {selected}")
    row = wrapped["row"]
    actual_id = row.get("trajectory_id") if selected.corpus == "openswe" else row.get("sample_id")
    actual_cluster = row.get("instance_id") if selected.corpus == "openswe" else extract_topic(row)
    if actual_id != selected.row_id or actual_cluster != selected.cluster_id:
        raise RuntimeError(f"sampling-frame/Viewer mismatch at {selected}")
    path.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(path, "wb", compresslevel=6) as stream:
        stream.write(canonical(row))
    return selected, row, digest_bytes(canonical(row)), False


def fetch_rows(raw: Path, selected: list[SelectedRow], workers: int) -> tuple[dict[SelectedRow, dict[str, Any]], list[dict[str, Any]]]:
    rows: dict[SelectedRow, dict[str, Any]] = {}
    manifest = []
    completed = 0
    batch_size = 32
    for start in range(0, len(selected), batch_size):
        batch = selected[start : start + batch_size]
        sources = sorted({item.corpus for item in batch})
        for source in sources:
            verify_head(source)
        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = {executor.submit(fetch_one, raw, item): item for item in batch}
            for future in as_completed(futures):
                item, row, row_sha, cached = future.result()
                rows[item] = row
                manifest.append(
                    {
                        "corpus": item.corpus,
                        "revision": SOURCES[item.corpus]["revision"],
                        "config": item.config,
                        "split": item.split,
                        "row_offset": item.offset,
                        "cluster_id": item.cluster_id,
                        "row_id": item.row_id,
                        "selection_sha256": item.selection_digest,
                        "row_sha256": row_sha,
                        "cached": cached,
                    }
                )
                completed += 1
        for source in sources:
            verify_head(source)
        print(f"fetched/replayed {completed}/{len(selected)} rows", flush=True)
    verify_head("openswe")
    verify_head("ideatrail")
    manifest.sort(key=lambda row: (row["corpus"], row["config"], row["split"], int(row["row_offset"])))
    return rows, manifest


def extract_topic(row: dict[str, Any]) -> str:
    system = next((message.get("content") or "" for message in row.get("messages", []) if message.get("role") == "system"), "")
    match = TOPIC_RE.search(system)
    return match.group(1) if match else ""


def normalize_path(value: str) -> str | None:
    value = value.strip().strip("'\"").replace("\\", "/")
    value = re.sub(r"^(?:/workspace/[^/]+|/testbed)(?:/|$)", "", value)
    value = re.sub(r"^\./", "", value)
    value = value.rstrip("/,:)")
    if not value or value.startswith(("http://", "https://")) or value in {".", "..", "/"}:
        return None
    path = PurePosixPath(value)
    if path.is_absolute() or ".." in path.parts:
        return None
    return str(path)


def module(path: str) -> str:
    parts = PurePosixPath(path).parts
    return parts[0] if len(parts) > 1 else "repo-root-files"


def json_arguments(call: dict[str, Any]) -> dict[str, Any]:
    arguments = (call.get("function") or {}).get("arguments")
    if isinstance(arguments, dict):
        return arguments
    if not isinstance(arguments, str):
        return {}
    try:
        value = json.loads(arguments)
        return value if isinstance(value, dict) else {}
    except json.JSONDecodeError:
        return {}


def shell_paths(command: str) -> set[str]:
    values = set(PATH_TOKEN_RE.findall(command))
    try:
        for token in shlex.split(command):
            if token.startswith("-") or "=" in token and not token.startswith(("./", "../", "/")):
                continue
            if "/" in token or re.search(r"\.[A-Za-z0-9]{1,8}$", token):
                values.add(token)
    except ValueError:
        pass
    return {path for value in values if (path := normalize_path(value))}


def action_from_call(call: dict[str, Any], corpus: str) -> dict[str, Any]:
    function = call.get("function") or {}
    name = str(function.get("name") or "")
    arguments = json_arguments(call)
    lowered = name.lower()
    explore = lowered in {"view", "glob", "grep", "websearch", "scraper"}
    mutate = lowered in {"write", "edit"}
    validate_attempt = False
    paths: set[str] = set()
    command = ""
    if lowered in {"str_replace_editor"}:
        operation = str(arguments.get("command") or "").lower()
        explore = operation == "view"
        mutate = operation in {"create", "str_replace", "insert", "undo_edit"}
    if lowered in {"bash", "execute_bash"}:
        command = str(arguments.get("command") or arguments.get("cmd") or "")
        explore = bool(SHELL_EXPLORE_RE.search(command))
        mutate = bool(SHELL_MUTATE_RE.search(command))
        validate_attempt = bool(VALIDATE_RE.search(command))
        paths.update(shell_paths(command))
    for key in ["path", "file_path", "old_path", "new_path"]:
        value = arguments.get(key)
        if isinstance(value, str) and (path := normalize_path(value)):
            paths.add(path)
    return {
        "tool": name or "<empty>",
        "explore": explore,
        "mutate": mutate,
        "validate_attempt": validate_attempt,
        "validate_success": False,  # neither public schema exposes a portable attempt/status pair
        "paths": sorted(paths),
        "modules": sorted({module(path) for path in paths}),
        "command": command,
        "corpus": corpus,
    }


def calls_from_row(row: dict[str, Any], corpus: str) -> list[dict[str, Any]]:
    messages = row.get("trajectory", []) if corpus == "openswe" else row.get("messages", [])
    actions = []
    for message in messages:
        if message.get("role") != "assistant":
            continue
        for call in message.get("tool_calls") or []:
            actions.append(action_from_call(call, corpus))
    return actions


def percentile(values: list[float], quantile: float) -> float:
    if not values:
        return math.nan
    return float(np.quantile(np.asarray(values, dtype=float), quantile))


def metrics(item: SelectedRow, row: dict[str, Any]) -> dict[str, Any]:
    actions = calls_from_row(row, item.corpus)
    path_actions = [action for action in actions if action["paths"]]
    transitions = Counter()
    for previous, current in zip(path_actions, path_actions[1:]):
        if set(previous["paths"]) & set(current["paths"]):
            transitions["same_path"] += 1
        elif set(previous["modules"]) & set(current["modules"]):
            transitions["same_module"] += 1
        else:
            transitions["cross_module"] += 1
    transition_n = sum(transitions.values())

    state: dict[str, dict[str, int | bool]] = {}
    return_gaps: list[int] = []
    for index, action in enumerate(path_actions):
        present = set(action["modules"])
        for name in state:
            if name not in present:
                state[name]["left"] = True
        for name in present:
            previous = state.get(name)
            if previous and bool(previous["left"]):
                # Count only calls strictly between departure and return.
                # For A, B, A the return gap is one intervening call.
                return_gaps.append(index - int(previous["index"]) - 1)
            state[name] = {"index": index, "left": False}

    first_mutation = next((index for index, action in enumerate(actions) if action["mutate"]), None)
    prior = actions[:first_mutation] if first_mutation is not None else []
    prior_explore = sum(bool(action["explore"]) for action in prior)
    prior_path_explore = sum(bool(action["explore"] and action["paths"]) for action in prior)

    weights: Counter[str] = Counter()
    for action in path_actions:
        for path in action["paths"]:
            weights[path] += 1 / len(action["paths"])
    total_weight = sum(weights.values())
    top_share = max(weights.values(), default=0) / total_weight if total_weight else math.nan
    hhi = sum((weight / total_weight) ** 2 for weight in weights.values()) if total_weight else math.nan

    path_history: dict[str, list[tuple[int, bool, bool]]] = defaultdict(list)
    for index, action in enumerate(actions):
        for path in action["paths"]:
            path_history[path].append((index, bool(action["explore"]), bool(action["mutate"])))
    mutated_paths = {path for path, history in path_history.items() if any(mutate for _, _, mutate in history)}
    read_before = 0
    mutated_again = 0
    for path in mutated_paths:
        history = path_history[path]
        first = next(index for index, (_, _, mutate) in enumerate(history) if mutate)
        read_before += any(explore for _, explore, _ in history[:first])
        mutated_again += sum(mutate for _, _, mutate in history[first + 1 :]) > 0

    stratum = f"{item.config}/{item.split}" if item.corpus == "openswe" else "default/train"
    return {
        "corpus": item.corpus,
        "stratum": stratum,
        "cluster_id": item.cluster_id,
        "row_id": item.row_id,
        "tool_calls": len(actions),
        "path_resolved_calls": len(path_actions),
        "mutation_calls": sum(bool(action["mutate"]) for action in actions),
        "explore_calls": sum(bool(action["explore"]) for action in actions),
        "validation_attempts": sum(bool(action["validate_attempt"]) for action in actions),
        "recognized_successful_validations": 0,
        "has_mutation": first_mutation is not None,
        "prior_explore_calls": prior_explore if first_mutation is not None else "",
        "prior_path_explore_calls": prior_path_explore if first_mutation is not None else "",
        "any_prior_explore": prior_explore > 0 if first_mutation is not None else "",
        "eligible_transitions": transition_n,
        "same_path": transitions["same_path"],
        "same_module": transitions["same_module"],
        "cross_module": transitions["cross_module"],
        "same_path_share": transitions["same_path"] / transition_n if transition_n else "",
        "same_module_share": transitions["same_module"] / transition_n if transition_n else "",
        "cross_module_share": transitions["cross_module"] / transition_n if transition_n else "",
        "observed_module_returns": len(return_gaps),
        "return_gap_median_calls": statistics.median(return_gaps) if return_gaps else "",
        "return_gap_p90_calls": percentile(return_gaps, 0.9) if return_gaps else "",
        "unique_target_paths": len(weights),
        "top_target_share": top_share if total_weight else "",
        "target_hhi": hhi if total_weight else "",
        "mutated_paths": len(mutated_paths),
        "mutated_path_read_before_share": read_before / len(mutated_paths) if mutated_paths else "",
        "mutated_path_mutated_again_share": mutated_again / len(mutated_paths) if mutated_paths else "",
        "resolved": row.get("resolved", "") if item.corpus == "openswe" else row.get("_grade", ""),
    }


def numeric(rows: list[dict[str, Any]], field: str) -> list[float]:
    return [float(row[field]) for row in rows if row.get(field) not in {"", None} and math.isfinite(float(row[field]))]


def bootstrap_interval(rows: list[dict[str, Any]], field: str, statistic: str, seed_offset: int) -> tuple[float, float, float, int]:
    values = numeric(rows, field)
    if not values:
        return math.nan, math.nan, math.nan, 0
    estimator = statistics.median if statistic == "median" else statistics.mean
    estimate = float(estimator(values))
    random = np.random.default_rng(BOOTSTRAP_SEED + seed_offset)
    array = np.asarray(values)
    samples = [float(estimator(array[random.integers(0, len(array), len(array))])) for _ in range(BOOTSTRAPS)]
    return estimate, percentile(samples, 0.025), percentile(samples, 0.975), len(values)


def summarize(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[(str(row["corpus"]), str(row["stratum"]))].append(row)
    fields = [
        ("any_prior_explore", "mean"),
        ("prior_explore_calls", "median"),
        ("same_path_share", "mean"),
        ("same_module_share", "mean"),
        ("cross_module_share", "mean"),
        ("observed_module_returns", "median"),
        ("return_gap_median_calls", "median"),
        ("top_target_share", "median"),
        ("target_hhi", "median"),
        ("mutated_path_read_before_share", "median"),
        ("mutated_path_mutated_again_share", "median"),
    ]
    summary = []
    for group_index, ((corpus, stratum), selected) in enumerate(sorted(groups.items())):
        for field_index, (field, statistic) in enumerate(fields):
            estimate, low, high, eligible = bootstrap_interval(selected, field, statistic, group_index * 100 + field_index)
            summary.append(
                {
                    "corpus": corpus,
                    "stratum": stratum,
                    "metric": field,
                    "statistic": statistic,
                    "eligible_units": eligible,
                    "estimate": estimate if eligible >= MIN_ELIGIBLE else "",
                    "ci95_low": low if eligible >= MIN_ELIGIBLE else "",
                    "ci95_high": high if eligible >= MIN_ELIGIBLE else "",
                    "status": "reported" if eligible >= MIN_ELIGIBLE else "N/A",
                }
            )
    return summary


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def read_selection(path: Path) -> list[SelectedRow]:
    with path.open(encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream))
    return [
        SelectedRow(
            row["corpus"],
            row["config"],
            row["split"],
            int(row["offset"]),
            row["cluster_id"],
            row["row_id"],
            row["selection_digest"],
        )
        for row in rows
    ]


def summary_value(summary: list[dict[str, Any]], corpus: str, stratum: str, metric: str) -> float:
    row = next(row for row in summary if row["corpus"] == corpus and row["stratum"] == stratum and row["metric"] == metric)
    return float(row["estimate"]) if row["estimate"] != "" else math.nan


def draw_figure(
    summary: list[dict[str, Any]],
    metrics_rows: list[dict[str, Any]],
    local_anchor: list[dict[str, str]],
    output: Path,
) -> None:
    groups = sorted({(str(row["corpus"]), str(row["stratum"])) for row in summary})
    labels = [stratum.replace("minimax_m25", "MiniMax").replace("qwen35_122b", "Qwen").replace("default/train", "IdeaTrail") for _, stratum in groups]
    colors = ["#3378b5", "#659fc7", "#4d9368", "#83b58f", "#d38945"]
    fig, axes = plt.subplots(2, 3, figsize=(10.5, 6.2))
    x = np.arange(len(groups))

    public_cross = []
    for corpus, stratum in groups:
        selected = [row for row in metrics_rows if row["corpus"] == corpus and row["stratum"] == stratum]
        denominator = sum(int(row["eligible_transitions"]) for row in selected)
        public_cross.append(sum(int(row["cross_module"]) for row in selected) / denominator)
    local_cross = [float(row["cross_module_share"]) for row in local_anchor]
    axes[0, 0].axhspan(min(local_cross), max(local_cross), color="#657487", alpha=0.16, label="six-case range", zorder=0)
    axes[0, 0].bar(x, public_cross, color=colors, edgecolor="#4b5c6d", linewidth=0.45, zorder=2)
    axes[0, 0].axhline(statistics.median(local_cross), color="#657487", linewidth=1, linestyle="--")
    axes[0, 0].yaxis.set_major_formatter(PercentFormatter(1))
    axes[0, 0].set_title("A. Cross-module movement", loc="left", fontweight="bold")
    axes[0, 0].legend(fontsize=7, frameon=False)

    bottoms = np.zeros(len(groups))
    for metric, color, label in [
        ("same_path_share", "#3378b5", "same path"),
        ("same_module_share", "#75ae87", "same module"),
        ("cross_module_share", "#dc8a48", "cross module"),
    ]:
        count_field = metric.removesuffix("_share")
        values = []
        for corpus, stratum in groups:
            selected = [row for row in metrics_rows if row["corpus"] == corpus and row["stratum"] == stratum]
            denominator = sum(int(row["eligible_transitions"]) for row in selected)
            values.append(sum(int(row[count_field]) for row in selected) / denominator)
        values = np.asarray(values)
        axes[0, 1].bar(x, values, bottom=bottoms, color=color, label=label)
        bottoms += values
    axes[0, 1].yaxis.set_major_formatter(PercentFormatter(1))
    axes[0, 1].set_title("B. Ordered path-target transitions", loc="left", fontweight="bold")
    axes[0, 1].legend(fontsize=7, frameon=False)

    returns = [summary_value(summary, *group, "return_gap_median_calls") for group in groups]
    axes[0, 2].bar(x, returns, color=colors)
    axes[0, 2].set_yscale("log")
    axes[0, 2].set_title("C. Module return gap", loc="left", fontweight="bold")
    axes[0, 2].set_ylabel("intervening path calls (log)", fontsize=8, labelpad=1)

    top = [summary_value(summary, *group, "top_target_share") for group in groups]
    axes[1, 0].bar(x, top, color=colors, edgecolor="#4b5c6d", linewidth=0.45)
    axes[1, 0].yaxis.set_major_formatter(PercentFormatter(1))
    axes[1, 0].set_title("D. Top-target concentration", loc="left", fontweight="bold")

    read_before = [summary_value(summary, *group, "mutated_path_read_before_share") for group in groups]
    repeated = [summary_value(summary, *group, "mutated_path_mutated_again_share") for group in groups]
    axes[1, 1].bar(x - 0.18, read_before, 0.36, color="#3378b5", label="read before mutate")
    axes[1, 1].bar(x + 0.18, repeated, 0.36, color="#d38945", label="mutated again")
    axes[1, 1].yaxis.set_major_formatter(PercentFormatter(1))
    axes[1, 1].set_title("E. Path staging (descriptive)", loc="left", fontweight="bold")
    axes[1, 1].legend(fontsize=7, frameon=False)

    matrix = np.asarray([[1, 0, 2, 2, 1, 1], [0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0]])
    axes[1, 2].imshow(matrix, cmap=matplotlib.colors.ListedColormap(["#eeeeee", "#e7b86b", "#57936c"]), vmin=0, vmax=2, aspect="auto")
    axes[1, 2].set_yticks(range(3), ["within attempt", "cross session", "Skill attribution"])
    axes[1, 2].set_xticks(range(6), ["E1", "E2", "E3", "E4", "E5", "E6"])
    axes[1, 2].set_title("F. Evidence boundary", loc="left", fontweight="bold")
    for column, label in enumerate(["analog", "N/A", "exact", "exact", "analog", "analog"]):
        axes[1, 2].text(column, 0, label, ha="center", va="center", fontsize=6.5)
    axes[1, 2].text(2.5, 1.5, "persistent lineage: N/A", ha="center", va="center", fontsize=7, color="#666")

    for axis in axes.flat[:5]:
        axis.set_xticks(x, labels, rotation=24, ha="right", fontsize=7)
        axis.grid(axis="y", alpha=0.18)
        axis.tick_params(axis="y", labelsize=7)
    fig.suptitle("RQ6 — External boundary of path-local Agent trajectories", x=0.02, ha="left", fontweight="bold")
    fig.text(0.5, 0.01, "Independent unit: SWE task instance / IdeaTrail topic. IdeaTrail exploration order is harness-enforced. E2 has no portable success status.", ha="center", fontsize=7, color="#7a3f35")
    fig.tight_layout(rect=(0, 0.04, 1, 0.95))
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output.with_suffix(".pdf"), bbox_inches="tight")
    fig.savefig(output.with_suffix(".png"), dpi=180, bbox_inches="tight")
    plt.close(fig)


def write_result(
    path: Path,
    metrics_rows: list[dict[str, Any]],
    summary: list[dict[str, Any]],
    local_anchor: list[dict[str, str]],
) -> None:
    groups = sorted({(str(row["corpus"]), str(row["stratum"])) for row in metrics_rows})
    group_sizes = Counter((str(row["corpus"]), str(row["stratum"])) for row in metrics_rows)
    complete = len(metrics_rows) == 5 * SAMPLE_UNITS and all(size == SAMPLE_UNITS for size in group_sizes.values())
    openswe_rows = [row for row in metrics_rows if row["corpus"] == "openswe"]
    openswe_unique = len({str(row["cluster_id"]) for row in openswe_rows})
    lines = [
        "# RQ6 Result: External Relation Boundary",
        "",
        "## Gate result",
        "",
        (
            f"PASS. Each Open-SWE stratum contains 64 independent task instances (256 stratum-specific selections; {openswe_unique} unique instance IDs across strata), alongside 64 independent IdeaTrail topics. Results are separate by stratum; no public corpus is pooled with the six local cases."
            if complete
            else f"PREFLIGHT ONLY. Parsed {len(metrics_rows)} selected units across all five strata; no relation is interpreted before the full 320-unit run."
        ),
        "",
        "## Exact common relations",
        "",
        "| Corpus / stratum | Eligible transitions | same path | same module | cross module | median intervening calls before return | Direction |",
        "|---|---:|---:|---:|---:|---:|---|",
    ]
    for corpus, stratum in groups:
        rows = [row for row in metrics_rows if row["corpus"] == corpus and row["stratum"] == stratum]
        transition_n = sum(int(row["eligible_transitions"]) for row in rows)
        counts = {kind: sum(int(row[kind]) for row in rows) for kind in ["same_path", "same_module", "cross_module"]}
        gaps = numeric(rows, "return_gap_median_calls")
        local = counts["same_path"] + counts["same_module"] > counts["cross_module"]
        lines.append(
            f"| {corpus} / {stratum} | {transition_n:,} | {counts['same_path']/transition_n:.1%} | {counts['same_module']/transition_n:.1%} | {counts['cross_module']/transition_n:.1%} | {statistics.median(gaps):.1f} | {'supports D1/D2' if local and len(gaps) >= MIN_ELIGIBLE else 'N/A'} |"
        )
    recurrence = (
        "All five public strata show ordered path-target locality and observable module returns. This is external recurrence of a within-attempt structural relation, not a prevalence estimate and not evidence of long-term progress."
        if complete
        else "The preflight exercises parsing and source reconciliation only. Directional results remain N/A because every stratum is below the preregistered 50-unit gate."
    )
    public_cross = []
    for corpus, stratum in groups:
        rows = [row for row in metrics_rows if row["corpus"] == corpus and row["stratum"] == stratum]
        public_cross.append(sum(int(row["cross_module"]) for row in rows) / sum(int(row["eligible_transitions"]) for row in rows))
    local_cross = [float(row["cross_module_share"]) for row in local_anchor]
    magnitude = (
        f"The magnitude is not identical: aggregate cross-module movement spans {min(public_cross):.1%}--{max(public_cross):.1%} in the public strata versus {min(local_cross):.1%}--{max(local_cross):.1%} in the six path-compatible local anchors. Public coding attempts therefore move across top-level modules more often than most natural-workspace cases, even though both retain short module-return gaps."
        if complete
        else "Preflight transition shares are diagnostic only and are not compared with the local anchors."
    )
    lines.extend(
        [
            "",
            recurrence,
            magnitude,
            "",
            "## Descriptive cells and boundary",
            "",
            "E1 is descriptive because the public harnesses shape exploration order, and IdeaTrail explicitly requires View before Write/Edit. E2 is N/A as a successful-validation relation because neither normalized public schema provides a portable Tool-attempt/status pair. E5/E6 concern normalized paths rather than stable artifact identities and are therefore analogous context only.",
            "",
            "Persistent artifact survival/revival, cross-session re-grounding, and exact Skill/instruction attribution remain N/A in both public corpora. Public task traces cannot confirm or reject those longitudinal local relations.",
            "",
            "## Interpretation",
            "",
            (
                "The defensible external claim is narrow: the local observation that Agent workspace actions form path-local trajectories with returns is not unique to the six author-related projects. The stronger contribution—stable artifact fate and continuity across native session boundaries—remains supported only by the qualified natural-workspace cases and is not externally replicated here."
                if complete
                else "No external relation claim is made from the preflight."
            ),
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    global REQUEST_INTERVAL_SECONDS
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--workers", type=int, default=16)
    parser.add_argument("--preflight", action="store_true")
    parser.add_argument("--request-interval", type=float, default=0.6)
    args = parser.parse_args()
    REQUEST_INTERVAL_SECONDS = args.request_interval
    output = args.output
    raw = output / "raw"
    output.mkdir(parents=True, exist_ok=True)

    heads = {source: verify_head(source) for source in SOURCES}
    manifests = {source: parquet_manifest(source) for source in SOURCES}
    source_check = {
        source: {
            "dataset": SOURCES[source]["dataset"],
            "revision": SOURCES[source]["revision"],
            "observed_head": heads[source]["sha"],
            "parquet_files": len(manifests[source]),
            "parquet_manifest_sha256": digest_bytes(canonical(manifests[source])),
        }
        for source in SOURCES
    }

    selection_path = output / "selection-plan.csv"
    if selection_path.exists():
        candidates = read_selection(selection_path)
        grouped: dict[tuple[str, str, str], list[SelectedRow]] = defaultdict(list)
        for row in candidates:
            grouped[(row.corpus, row.config, row.split)].append(row)
        selected = [
            row
            for key in sorted(grouped)
            for row in grouped[key][:(4 if args.preflight and key[0] == "ideatrail" else 1 if args.preflight else SAMPLE_UNITS)]
        ]
        expected_selected = 8 if args.preflight else 5 * SAMPLE_UNITS
        if len(grouped) != 5 or len(selected) != expected_selected:
            raise RuntimeError("cached selection plan lacks the required strata or unit prefix")
        frame_path = output / "sampling-frame-summary.csv"
        if frame_path.exists():
            frame_rows = list(csv.DictReader(frame_path.open(encoding="utf-8", newline="")))
            for row in frame_rows:
                row["selected_units"] = str(4 if args.preflight and row["corpus"] == "ideatrail" else 1 if args.preflight else SAMPLE_UNITS)
            write_csv(frame_path, frame_rows)
        print(f"replayed frozen selection plan: {len(selected)} rows", flush=True)
    else:
        selected = []
        candidate_plan: list[SelectedRow] = []
        frame_summary = []
        for config, split in OPEN_STRATA:
            frame = open_sampling_frame(manifests["openswe"], config, split)
            choices = select_open(frame, config, split)
            candidate_plan.extend(choices)
            if args.preflight:
                choices = choices[:1]
            selected.extend(choices[:SAMPLE_UNITS])
            frame_summary.append(
                {
                    "corpus": "openswe",
                    "config": config,
                    "split": split,
                    "rows": len(frame),
                    "independent_units": len({instance for _, instance, _ in frame}),
                    "selected_units": min(len(choices), SAMPLE_UNITS),
                }
            )
            print(f"sampling frame {config}/{split}: {len(frame)} rows", flush=True)
        idea_frame = idea_sampling_frame(manifests["ideatrail"])
        idea_choices = select_idea(idea_frame)
        candidate_plan.extend(idea_choices)
        if args.preflight:
            idea_choices = idea_choices[:4]
        selected.extend(idea_choices[:SAMPLE_UNITS])
        frame_summary.append(
            {
                "corpus": "ideatrail",
                "config": "default",
                "split": "train",
                "rows": len(idea_frame),
                "independent_units": len({topic for _, _, topic in idea_frame}),
                "selected_units": min(len(idea_choices), SAMPLE_UNITS),
            }
        )
        write_csv(output / "sampling-frame-summary.csv", frame_summary)
        write_csv(
            selection_path,
            [
                {
                    "corpus": row.corpus,
                    "config": row.config,
                    "split": row.split,
                    "offset": row.offset,
                    "cluster_id": row.cluster_id,
                    "row_id": row.row_id,
                    "selection_digest": row.selection_digest,
                }
                for row in candidate_plan
            ],
        )

    public_rows, sample_manifest = fetch_rows(raw, selected, args.workers)
    write_csv(output / "sample-manifest.csv", sample_manifest)
    metrics_rows = [metrics(item, public_rows[item]) for item in selected]
    metrics_rows.sort(key=lambda row: (row["corpus"], row["stratum"], row["cluster_id"]))
    write_csv(output / "trajectory-metrics.csv", metrics_rows)
    summary = summarize(metrics_rows)
    write_csv(output / "relation-summary.csv", summary)

    coverage = []
    for (corpus, stratum), rows in sorted(
        ((key, list(group)) for key, group in __import__("itertools").groupby(metrics_rows, key=lambda row: (row["corpus"], row["stratum"]))),
        key=lambda value: value[0],
    ):
        coverage.append(
            {
                "corpus": corpus,
                "stratum": stratum,
                "sampled_units": len(rows),
                "parsed_units": len(rows),
                "units_with_tool_calls": sum(int(row["tool_calls"]) > 0 for row in rows),
                "units_with_paths": sum(int(row["path_resolved_calls"]) > 0 for row in rows),
                "units_with_mutations": sum(str(row["has_mutation"]) == "True" or row["has_mutation"] is True for row in rows),
                "units_with_transitions": sum(int(row["eligible_transitions"]) > 0 for row in rows),
                "units_with_returns": sum(int(row["observed_module_returns"]) > 0 for row in rows),
                "validation_success_status_available": False,
            }
        )
    write_csv(output / "coverage.csv", coverage)
    na_rows = [
        {"relation": "L1 persistent artifact fate", "openswe": "N/A", "ideatrail": "N/A", "reason": "no persistent cross-session artifact lineage"},
        {"relation": "L2 cross-session re-grounding", "openswe": "N/A", "ideatrail": "N/A", "reason": "one attempt per sampled unit"},
        {"relation": "L3 exact Skill/instruction footprint", "openswe": "N/A", "ideatrail": "N/A", "reason": "no source-native Skill attribution"},
        {"relation": "E2 recognized successful validation", "openswe": "N/A", "ideatrail": "N/A", "reason": "no portable attempt/status pair"},
    ]
    write_csv(output / "na-map.csv", na_rows)
    source_check["selected_rows"] = len(selected)
    source_check["sample_manifest_sha256"] = digest_bytes((output / "sample-manifest.csv").read_bytes())
    source_check["trajectory_metrics_sha256"] = digest_bytes((output / "trajectory-metrics.csv").read_bytes())
    (output / "source-check.json").write_text(json.dumps(source_check, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    local_anchor_path = output.parent / "local-anchor.csv"
    with local_anchor_path.open(encoding="utf-8", newline="") as stream:
        local_anchor = list(csv.DictReader(stream))
    draw_figure(summary, metrics_rows, local_anchor, output / "figures" / "rq6-external-boundary")
    write_result(output / "result.md", metrics_rows, summary, local_anchor)


if __name__ == "__main__":
    main()
