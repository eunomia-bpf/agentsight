#!/usr/bin/env python3
"""Thin adapter for the published ASE literal-action identity experiment.

`prepare` is the only mode that can read the official annotation repository.
It emits an opaque visible-input file and a separate scorer manifest. `run`
accepts only the visible-input file and a llama.cpp endpoint. `score` joins
durable predictions to the scorer manifest after inference has completed.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import random
import re
import time
import urllib.error
import urllib.request
from collections import Counter, defaultdict
from pathlib import Path
from typing import Iterable


LABELS = (
    "Explore",
    "Locate",
    "Search",
    "Reproduce",
    "Generate Fix",
    "Run tests",
    "Refactor",
    "Explain",
)

DESCRIPTIONS = {
    "Explore": "Broadly inspect the task, repository, environment, or available context.",
    "Locate": "Identify the specific file, symbol, function, or code area to change.",
    "Search": "Run a targeted search for text, references, examples, or related behavior.",
    "Reproduce": "Run commands or checks to observe, reproduce, or isolate the problem.",
    "Generate Fix": "Create or edit code intended to solve the task.",
    "Run tests": "Run tests, linters, or validation commands after a change.",
    "Refactor": "Reorganize or simplify code without changing intended behavior.",
    "Explain": "Reason, summarize, or plan without directly changing or validating code.",
}

EXPECTED_CLASS_COUNTS = {
    "Explore": 606,
    "Locate": 196,
    "Search": 364,
    "Reproduce": 153,
    "Generate Fix": 883,
    "Run tests": 294,
    "Refactor": 23,
    "Explain": 218,
}

AGENTS = (
    ("autocoderover", ""),
    ("openhands", ".txt"),
    ("repairagent", ""),
)

EXPECTED_AGENT_COUNTS = {
    "autocoderover": (40, 218, 218),
    "openhands": (40, 1108, 1113),
    "repairagent": (40, 1411, 1420),
}

SOURCE_COMMIT = "e84f66f8d494e46ef336edfa137db25a629614fb"
SOURCE_URL = "https://github.com/sola-st/llm-agents-study"
CONTROL_LABEL = "Generate Fix"
SOURCE_LIMIT = 1600
BOOTSTRAP_SEED = 32025

ITERATION_HEADER = re.compile(
    r"^(Thought at Iteration|Iteration|Thought and Action at iteration) (\d+):",
    re.MULTILINE,
)

SYSTEM_PROMPT = "You assign exactly one published software-engineering action label."
GRAMMAR = "root ::= " + " | ".join(json.dumps(label) for label in LABELS)


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def truncate_clean(text: str, limit: int = SOURCE_LIMIT) -> str:
    """Match AgentProf's whitespace normalization and character truncation."""
    cleaned = " ".join(text.split())
    if len(cleaned) <= limit:
        return cleaned
    return cleaned[: limit - 1] + "."


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n")
    temporary.replace(path)


def write_jsonl(path: Path, rows: Iterable[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
    temporary.replace(path)


def read_jsonl(path: Path) -> list[dict]:
    rows = []
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as error:
                raise SystemExit(f"invalid JSON at {path}:{line_number}: {error}") from error
            if not isinstance(row, dict):
                raise SystemExit(f"non-object JSON at {path}:{line_number}")
            rows.append(row)
    return rows


def parse_thought_action(path: Path) -> dict[int, tuple[str, str]]:
    """Parse the official serialized thought/action view for all three agents."""
    text = path.read_text(errors="replace")
    matches = list(ITERATION_HEADER.finditer(text))
    parsed: dict[int, tuple[str, str]] = {}
    for ordinal, match in enumerate(matches):
        iteration = int(match.group(2))
        end = matches[ordinal + 1].start() if ordinal + 1 < len(matches) else len(text)
        body = text[match.end() : end].strip()
        body = re.sub(r"\n---\s*$", "", body).strip()
        if match.group(1) == "Thought at Iteration":
            marker = f"\nAction at Iteration {iteration}:"
            if marker not in body:
                raise SystemExit(f"missing action marker for iteration {iteration} in {path}")
            thought, action = body.split(marker, 1)
        else:
            if body.startswith("Thought="):
                body = body[len("Thought=") :]
            if "; Action=" not in body:
                raise SystemExit(f"missing thought/action separator for iteration {iteration} in {path}")
            thought, action = body.rsplit("; Action=", 1)
        if iteration in parsed:
            raise SystemExit(f"duplicate visible iteration {iteration} in {path}")
        parsed[iteration] = (thought.strip(), action.strip())
    return parsed


def source_rows(source_root: Path) -> tuple[list[dict], dict]:
    records: list[dict] = []
    total_visible = 0
    agent_summary: dict[str, dict] = {}
    class_counts: Counter[str] = Counter()

    for agent, extension in AGENTS:
        category_dir = source_root / f"{agent}_csv" / "actions_categories"
        trace_dir = source_root / "trajectories" / agent / "parsed" / "thoughts_actions"
        category_paths = sorted(category_dir.glob("*.csv"))
        if len(category_paths) != EXPECTED_AGENT_COUNTS[agent][0]:
            raise SystemExit(
                f"expected {EXPECTED_AGENT_COUNTS[agent][0]} {agent} category files, "
                f"found {len(category_paths)}"
            )

        agent_gold = 0
        agent_visible = 0
        for category_path in category_paths:
            trace_path = trace_dir / f"{category_path.stem}{extension}"
            if not trace_path.is_file():
                raise SystemExit(f"missing official visible trace: {trace_path}")
            visible = parse_thought_action(trace_path)
            agent_visible += len(visible)

            with category_path.open(newline="", encoding="utf-8") as handle:
                gold_rows = list(csv.DictReader(handle))
            gold_ids: set[int] = set()
            for gold_row in gold_rows:
                iteration = int(gold_row["iteration"])
                label = gold_row["category"].strip()
                if label not in LABELS:
                    raise SystemExit(f"unknown label {label!r} in {category_path}")
                if iteration in gold_ids:
                    raise SystemExit(f"duplicate gold iteration {iteration} in {category_path}")
                if iteration not in visible:
                    raise SystemExit(
                        f"gold iteration {iteration} has no visible input in {trace_path}"
                    )
                gold_ids.add(iteration)
                thought, action = visible[iteration]
                source = truncate_clean(f"Action:\n{action}\nThought:\n{thought}")
                records.append(
                    {
                        "agent": agent,
                        "trajectory": category_path.stem,
                        "iteration": iteration,
                        "target_label": label,
                        "source": source,
                        "source_sha256": sha256_text(source),
                    }
                )
                class_counts[label] += 1
                agent_gold += 1

        expected_files, expected_gold, expected_visible = EXPECTED_AGENT_COUNTS[agent]
        if agent_gold != expected_gold or agent_visible != expected_visible:
            raise SystemExit(
                f"unexpected {agent} counts: files={len(category_paths)}/{expected_files}, "
                f"gold={agent_gold}/{expected_gold}, visible={agent_visible}/{expected_visible}"
            )
        total_visible += agent_visible
        agent_summary[agent] = {
            "trajectories": len(category_paths),
            "gold_rows": agent_gold,
            "visible_iterations": agent_visible,
            "coverage": agent_gold / agent_visible,
        }

    if len(records) != 2737 or total_visible != 2751:
        raise SystemExit(
            f"unexpected complete counts: gold={len(records)}/2737, visible={total_visible}/2751"
        )
    if dict(class_counts) != EXPECTED_CLASS_COUNTS:
        raise SystemExit(f"unexpected class counts: {dict(class_counts)}")

    for ordinal, record in enumerate(records):
        record["row_id"] = f"ase-action-{ordinal:04d}"

    metadata = {
        "source_url": SOURCE_URL,
        "source_commit": SOURCE_COMMIT,
        "labels": list(LABELS),
        "control_label": CONTROL_LABEL,
        "gold_rows": len(records),
        "visible_iterations": total_visible,
        "published_label_coverage": len(records) / total_visible,
        "class_counts": dict(class_counts),
        "agents": agent_summary,
        "source_window_characters": SOURCE_LIMIT,
    }
    return records, metadata


def opaque_input(record: dict) -> dict:
    return {
        "row_id": record["row_id"],
        "source": record["source"],
        "source_sha256": record["source_sha256"],
    }


def scorer_row(record: dict) -> dict:
    return {
        "row_id": record["row_id"],
        "agent": record["agent"],
        "trajectory": record["trajectory"],
        "iteration": record["iteration"],
        "target_label": record["target_label"],
        "source_sha256": record["source_sha256"],
    }


def prepare(args: argparse.Namespace) -> None:
    records, metadata = source_rows(args.source_root)
    output_root = args.output_root

    write_jsonl(output_root / "visible-inputs.jsonl", map(opaque_input, records))
    write_json(
        output_root / "scorer-manifest.json",
        {"metadata": metadata, "rows": [scorer_row(record) for record in records]},
    )

    first_by_label: dict[str, dict] = {}
    for record in records:
        first_by_label.setdefault(record["target_label"], record)
    preflight = [first_by_label[label] for label in LABELS]
    preflight_metadata = {
        **metadata,
        "gold_rows": len(preflight),
        "visible_iterations": len(preflight),
        "published_label_coverage": 1.0,
        "preflight_only": True,
        "full_population_gold_rows": len(records),
        "full_population_visible_iterations": metadata["visible_iterations"],
    }
    write_jsonl(
        output_root / "preflight" / "visible-inputs.jsonl",
        map(opaque_input, preflight),
    )
    write_json(
        output_root / "preflight" / "scorer-manifest.json",
        {"metadata": preflight_metadata, "rows": [scorer_row(record) for record in preflight]},
    )

    print(
        json.dumps(
            {
                "status": "ok",
                "gold_rows": len(records),
                "visible_iterations": total_visible_from_metadata(metadata),
                "preflight_rows": len(preflight),
                "class_counts": dict(sorted(EXPECTED_CLASS_COUNTS.items())),
            },
            sort_keys=True,
        )
    )


def total_visible_from_metadata(metadata: dict) -> int:
    return int(metadata["visible_iterations"])


def taxonomy_prompt(source: str) -> str:
    taxonomy = "\n".join(f"- {label}: {DESCRIPTIONS[label]}" for label in LABELS)
    return (
        "Assign this action to exactly one published software-engineering action category.\n"
        "Return only the exact category label, with matching capitalization and no explanation.\n"
        f"Published action taxonomy:\n{taxonomy}\n\n"
        f"Input:\n{source}\n\nLabel:"
    )


def extract_response_text(payload: dict) -> str:
    try:
        content = payload["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as error:
        raise ValueError(f"response has no message content: {payload}") from error
    if not isinstance(content, str):
        raise ValueError(f"response content is not a string: {payload}")
    return content.strip()


def call_model(
    url: str,
    model: str,
    source: str,
    timeout: float,
    attempts: int,
) -> tuple[str, int, float]:
    endpoint = url.rstrip("/") + "/v1/chat/completions"
    body = json.dumps(
        {
            "model": model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": taxonomy_prompt(source)},
            ],
            "temperature": 0,
            "max_tokens": 8,
            "grammar": GRAMMAR,
            "stream": False,
        }
    ).encode("utf-8")

    last_error: Exception | None = None
    for attempt in range(1, attempts + 1):
        started = time.monotonic()
        request = urllib.request.Request(
            endpoint,
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                payload = json.loads(response.read().decode("utf-8"))
            prediction = extract_response_text(payload)
            if prediction not in LABELS:
                raise ValueError(f"model returned value outside exact grammar: {prediction!r}")
            return prediction, attempt, time.monotonic() - started
        except (OSError, urllib.error.URLError, json.JSONDecodeError, ValueError) as error:
            last_error = error
            if attempt < attempts:
                time.sleep(0.5 * attempt)
    raise RuntimeError(f"model request failed after {attempts} attempts: {last_error}")


def validate_visible_inputs(rows: list[dict], path: Path) -> None:
    expected_keys = {"row_id", "source", "source_sha256"}
    seen: set[str] = set()
    for row in rows:
        if set(row) != expected_keys:
            raise SystemExit(
                f"visible input contains unexpected fields in {path}: {sorted(set(row) - expected_keys)}"
            )
        row_id = row["row_id"]
        source = row["source"]
        source_hash = row["source_sha256"]
        if not all(isinstance(value, str) and value for value in (row_id, source, source_hash)):
            raise SystemExit(f"invalid visible input row in {path}: {row}")
        if row_id in seen:
            raise SystemExit(f"duplicate visible row ID in {path}: {row_id}")
        if sha256_text(source) != source_hash:
            raise SystemExit(f"visible input hash mismatch in {path}: {row_id}")
        seen.add(row_id)


def read_existing_predictions(
    path: Path, inputs: dict[str, dict], expected_model: str | None = None
) -> dict[str, dict]:
    if not path.exists():
        return {}
    rows = read_jsonl(path)
    predictions: dict[str, dict] = {}
    for row in rows:
        row_id = row.get("row_id")
        if row_id not in inputs:
            raise SystemExit(f"prediction has unknown row ID in {path}: {row_id}")
        if row_id in predictions:
            raise SystemExit(f"duplicate prediction in {path}: {row_id}")
        if row.get("source_sha256") != inputs[row_id]["source_sha256"]:
            raise SystemExit(f"prediction source hash mismatch in {path}: {row_id}")
        if row.get("prediction") not in LABELS:
            raise SystemExit(f"invalid stored prediction in {path}: {row}")
        if expected_model is not None and row.get("model") != expected_model:
            raise SystemExit(
                f"stored prediction model mismatch in {path}: "
                f"{row.get('model')!r} != {expected_model!r}"
            )
        predictions[row_id] = row
    return predictions


def run(args: argparse.Namespace) -> None:
    rows = read_jsonl(args.inputs)
    validate_visible_inputs(rows, args.inputs)
    inputs = {row["row_id"]: row for row in rows}
    existing = read_existing_predictions(args.output, inputs, args.model)
    args.output.parent.mkdir(parents=True, exist_ok=True)

    started = time.monotonic()
    completed_now = 0
    with args.output.open("a", encoding="utf-8", buffering=1) as handle:
        for ordinal, row in enumerate(rows, 1):
            if row["row_id"] in existing:
                continue
            prediction, attempts, elapsed = call_model(
                args.url,
                args.model,
                row["source"],
                args.timeout,
                args.attempts,
            )
            output = {
                "row_id": row["row_id"],
                "source_sha256": row["source_sha256"],
                "prediction": prediction,
                "request_attempts": attempts,
                "elapsed_seconds": elapsed,
                "model": args.model,
            }
            handle.write(json.dumps(output, ensure_ascii=False, sort_keys=True) + "\n")
            handle.flush()
            completed_now += 1
            if completed_now % 25 == 0 or ordinal == len(rows):
                print(
                    f"completed={len(existing) + completed_now}/{len(rows)} "
                    f"new={completed_now} elapsed={time.monotonic() - started:.1f}s",
                    flush=True,
                )

    final = read_existing_predictions(args.output, inputs, args.model)
    if set(final) != set(inputs):
        missing = sorted(set(inputs) - set(final))[:10]
        raise SystemExit(f"run incomplete: {len(final)}/{len(inputs)} predictions; missing={missing}")
    print(
        json.dumps(
            {
                "status": "complete",
                "rows": len(rows),
                "resumed": len(existing),
                "completed_now": completed_now,
                "elapsed_seconds": time.monotonic() - started,
            },
            sort_keys=True,
        )
    )


def empty_matrix() -> list[list[int]]:
    return [[0 for _ in LABELS] for _ in LABELS]


def add_matrix(target: list[list[int]], source: list[list[int]]) -> None:
    for row in range(len(LABELS)):
        for column in range(len(LABELS)):
            target[row][column] += source[row][column]


def matrix_for(rows: list[dict], predictions: dict[str, str]) -> list[list[int]]:
    index = {label: position for position, label in enumerate(LABELS)}
    matrix = empty_matrix()
    for row in rows:
        matrix[index[row["target_label"]]][index[predictions[row["row_id"]]]] += 1
    return matrix


def metrics_from_matrix(matrix: list[list[int]], active_labels: tuple[str, ...] = LABELS) -> dict:
    index = {label: position for position, label in enumerate(LABELS)}
    active = [index[label] for label in active_labels]
    total = sum(sum(row) for row in matrix)
    correct = sum(matrix[position][position] for position in range(len(LABELS)))
    per_label: dict[str, dict] = {}
    f1_values = []
    for label in active_labels:
        position = index[label]
        tp = matrix[position][position]
        fp = sum(matrix[row][position] for row in range(len(LABELS)) if row != position)
        fn = sum(matrix[position][column] for column in range(len(LABELS)) if column != position)
        support = sum(matrix[position])
        precision = tp / (tp + fp) if tp + fp else 0.0
        recall = tp / (tp + fn) if tp + fn else 0.0
        f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
        f1_values.append(f1)
        per_label[label] = {
            "support": support,
            "precision": precision,
            "recall": recall,
            "f1": f1,
        }
    return {
        "rows": total,
        "accuracy": correct / total if total else 0.0,
        "macro_f1": sum(f1_values) / len(f1_values) if f1_values else 0.0,
        "macro_labels": list(active_labels),
        "per_label": per_label,
        "confusion": {
            LABELS[row]: {LABELS[column]: matrix[row][column] for column in range(len(LABELS))}
            for row in range(len(LABELS))
        },
    }


def percentile(values: list[float], quantile: float) -> float:
    if not values:
        raise ValueError("cannot take percentile of an empty list")
    ordered = sorted(values)
    position = quantile * (len(ordered) - 1)
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    fraction = position - lower
    return ordered[lower] * (1 - fraction) + ordered[upper] * fraction


def bootstrap_effect(
    rows: list[dict],
    candidate: dict[str, str],
    majority: dict[str, str],
    replicates: int,
    seed: int,
) -> dict | None:
    if replicates <= 0:
        return None
    trajectory_rows: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for row in rows:
        trajectory_rows[(row["agent"], row["trajectory"])].append(row)
    trajectory_matrices = {
        key: (matrix_for(group, candidate), matrix_for(group, majority))
        for key, group in trajectory_rows.items()
    }
    by_agent: dict[str, list[tuple[str, str]]] = defaultdict(list)
    for key in trajectory_rows:
        by_agent[key[0]].append(key)
    for keys in by_agent.values():
        keys.sort()

    generator = random.Random(seed)
    deltas: list[float] = []
    for _ in range(replicates):
        candidate_matrix = empty_matrix()
        majority_matrix = empty_matrix()
        for agent in sorted(by_agent):
            keys = by_agent[agent]
            for _ in range(len(keys)):
                key = generator.choice(keys)
                candidate_part, majority_part = trajectory_matrices[key]
                add_matrix(candidate_matrix, candidate_part)
                add_matrix(majority_matrix, majority_part)
        candidate_f1 = metrics_from_matrix(candidate_matrix)["macro_f1"]
        majority_f1 = metrics_from_matrix(majority_matrix)["macro_f1"]
        deltas.append(candidate_f1 - majority_f1)
    return {
        "replicates": replicates,
        "seed": seed,
        "unit": "whole trajectory, stratified by agent framework",
        "interval": "percentile",
        "lower_95": percentile(deltas, 0.025),
        "median": percentile(deltas, 0.5),
        "upper_95": percentile(deltas, 0.975),
    }


def prediction_rows_by_id(path: Path) -> dict[str, dict]:
    predictions: dict[str, dict] = {}
    for row in read_jsonl(path):
        row_id = row.get("row_id")
        prediction = row.get("prediction")
        if not isinstance(row_id, str) or prediction not in LABELS:
            raise SystemExit(f"invalid prediction row in {path}: {row}")
        if row_id in predictions:
            raise SystemExit(f"duplicate prediction ID in {path}: {row_id}")
        predictions[row_id] = row
    return predictions


def score(args: argparse.Namespace) -> None:
    manifest = json.loads(args.manifest.read_text())
    metadata = manifest["metadata"]
    rows = manifest["rows"]
    if len(args.predictions) not in (1, 2):
        raise SystemExit("score requires one preflight or two full prediction files")
    prediction_rows = [prediction_rows_by_id(path) for path in args.predictions]
    expected_ids = {row["row_id"] for row in rows}
    manifest_by_id = {row["row_id"]: row for row in rows}
    for path, predictions in zip(args.predictions, prediction_rows):
        if set(predictions) != expected_ids:
            missing = sorted(expected_ids - set(predictions))[:10]
            extra = sorted(set(predictions) - expected_ids)[:10]
            raise SystemExit(f"population mismatch in {path}: missing={missing} extra={extra}")
        for row_id, prediction_row in predictions.items():
            if prediction_row.get("source_sha256") != manifest_by_id[row_id]["source_sha256"]:
                raise SystemExit(f"prediction/manifest source mismatch in {path}: {row_id}")

    repetitions = [
        {row_id: row["prediction"] for row_id, row in predictions.items()}
        for predictions in prediction_rows
    ]

    candidate = repetitions[0]
    majority = {row["row_id"]: metadata["control_label"] for row in rows}
    candidate_matrix = matrix_for(rows, candidate)
    majority_matrix = matrix_for(rows, majority)
    candidate_metrics = metrics_from_matrix(candidate_matrix)
    majority_metrics = metrics_from_matrix(majority_matrix)
    point_effect = candidate_metrics["macro_f1"] - majority_metrics["macro_f1"]
    bootstrap = bootstrap_effect(
        rows,
        candidate,
        majority,
        args.bootstrap_replicates,
        args.bootstrap_seed,
    )

    per_agent = {}
    for agent in sorted({row["agent"] for row in rows}):
        agent_rows = [row for row in rows if row["agent"] == agent]
        present = tuple(label for label in LABELS if any(row["target_label"] == label for row in agent_rows))
        per_agent[agent] = metrics_from_matrix(matrix_for(agent_rows, candidate), present)

    stable = (
        sum(repetitions[0][row_id] == repetitions[1][row_id] for row_id in expected_ids)
        if len(repetitions) == 2
        else None
    )
    source_groups: dict[str, list[str]] = defaultdict(list)
    for row in rows:
        source_groups[row["source_sha256"]].append(row["target_label"])
    conflicting = [labels for labels in source_groups.values() if len(set(labels)) > 1]

    result = {
        "status": "complete",
        "population": {
            "trajectories": len({(row["agent"], row["trajectory"]) for row in rows}),
            "scored_rows": len(rows),
            "visible_iterations": metadata["visible_iterations"],
            "published_label_coverage": metadata["published_label_coverage"],
            "class_counts": dict(Counter(row["target_label"] for row in rows)),
        },
        "candidate": candidate_metrics,
        "majority_control": majority_metrics,
        "primary_effect": {
            "metric": "eight-class operation-macro F1 difference",
            "candidate_minus_majority": point_effect,
            "trajectory_bootstrap": bootstrap,
        },
        "per_agent": per_agent,
        "repetitions": [
            metrics_from_matrix(matrix_for(rows, predictions)) for predictions in repetitions
        ],
        "stability": {
            "exact_agreement_rows": stable,
            "total_rows": len(rows),
            "exact_agreement": stable / len(rows) if stable is not None and rows else None,
        },
        "input_identifiability": {
            "unique_source_windows": len(source_groups),
            "duplicate_rows": len(rows) - len(source_groups),
            "conflicting_unique_source_windows": len(conflicting),
            "rows_in_conflicting_source_windows": sum(len(group) for group in conflicting),
        },
        "tested_hypothesis_supported": bool(
            bootstrap is not None and bootstrap["lower_95"] > 0
        ),
        "artifacts": {
            "manifest": str(args.manifest),
            "predictions": [str(path) for path in args.predictions],
        },
    }
    write_json(args.output, result)
    print(
        json.dumps(
            {
                "status": "complete",
                "candidate_macro_f1": candidate_metrics["macro_f1"],
                "candidate_accuracy": candidate_metrics["accuracy"],
                "majority_macro_f1": majority_metrics["macro_f1"],
                "macro_f1_effect": point_effect,
                "bootstrap_lower_95": bootstrap["lower_95"] if bootstrap else None,
                "stability": stable / len(rows) if stable is not None and rows else None,
                "hypothesis_supported": result["tested_hypothesis_supported"],
            },
            sort_keys=True,
        )
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)

    prepare_parser = commands.add_parser("prepare")
    prepare_parser.add_argument("--source-root", type=Path, required=True)
    prepare_parser.add_argument("--output-root", type=Path, required=True)
    prepare_parser.set_defaults(func=prepare)

    run_parser = commands.add_parser("run")
    run_parser.add_argument("--inputs", type=Path, required=True)
    run_parser.add_argument("--output", type=Path, required=True)
    run_parser.add_argument("--url", required=True)
    run_parser.add_argument("--model", required=True)
    run_parser.add_argument("--timeout", type=float, default=90.0)
    run_parser.add_argument("--attempts", type=int, default=3)
    run_parser.set_defaults(func=run)

    score_parser = commands.add_parser("score")
    score_parser.add_argument("--manifest", type=Path, required=True)
    score_parser.add_argument("--predictions", type=Path, nargs="+", required=True)
    score_parser.add_argument("--output", type=Path, required=True)
    score_parser.add_argument("--bootstrap-replicates", type=int, default=10000)
    score_parser.add_argument("--bootstrap-seed", type=int, default=BOOTSTRAP_SEED)
    score_parser.set_defaults(func=score)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
