#!/usr/bin/env python3
"""Thin AgentBoard adapter for the AgentProf declared-task experiment.

The adapter only validates official rows, builds portable AgentSight traces,
and scores AgentProf JSON outputs. Model requests and tag derivation stay in
the shared Rust AgentProf implementation.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path


TASK_FILES = (
    "alfworld",
    "babyai",
    "jericho",
    "pddl",
    "scienceworld",
    "tool-operation",
    "tool-query",
    "webarena",
    "webshop",
)
ALIASES = {
    "alfworld": "alfworld",
    "babyai": "babyai",
    "jericho": "jericho",
    "pddl": "pddl",
    "scienceworld": "scienceworld",
    "tool-operation": "toolop",
    "tool-query": "toolquery",
    "webbrowse": "webbrowse",
    "webshop": "webshop",
}
EXPECTED_COUNTS = {
    "alfworld": 134,
    "babyai": 112,
    "jericho": 20,
    "pddl": 60,
    "scienceworld": 90,
    "tool-operation": 40,
    "tool-query": 60,
    "webbrowse": 245,
    "webshop": 251,
}


def read_rows(data_root: Path) -> list[dict]:
    rows: list[dict] = []
    counts: Counter[str] = Counter()
    for source_name in TASK_FILES:
        path = data_root / source_name / "test.jsonl"
        if not path.is_file():
            raise SystemExit(f"missing official AgentBoard file: {path}")
        with path.open(encoding="utf-8") as handle:
            for source_row, line in enumerate(handle):
                row = json.loads(line)
                goal = row.get("goal")
                task = row.get("task")
                if not isinstance(goal, str) or not goal.strip():
                    raise SystemExit(f"empty goal at {path}:{source_row + 1}")
                if task not in ALIASES:
                    raise SystemExit(
                        f"unknown official task {task!r} at {path}:{source_row + 1}"
                    )
                ordinal = len(rows)
                rows.append(
                    {
                        "ordinal": ordinal,
                        "session_id": f"agentboard-{ordinal:04d}",
                        "source_file": f"{source_name}/test.jsonl",
                        "source_row": source_row,
                        "source_id": row.get("id"),
                        "task": task,
                        "target_tag": ALIASES[task],
                        "goal": goal.strip(),
                        "goal_sha256": hashlib.sha256(goal.strip().encode()).hexdigest(),
                    }
                )
                counts[task] += 1
    if len(rows) != 1012:
        raise SystemExit(f"expected 1,012 rows, found {len(rows)}")
    if dict(sorted(counts.items())) != dict(sorted(EXPECTED_COUNTS.items())):
        raise SystemExit(f"unexpected official class counts: {dict(counts)}")
    return rows


def trace_session(row: dict) -> dict:
    return {
        "agent_type": "agentboard",
        "session_id": row["session_id"],
        "conversation_id": None,
        "display_id": row["session_id"],
        "path": f"agentboard/{row['ordinal']:04d}.jsonl",
        "updated": {"secs_since_epoch": 0, "nanos_since_epoch": 0},
        "start_timestamp_ms": row["ordinal"] + 1,
        "end_timestamp_ms": row["ordinal"] + 2,
        "model": None,
        "usage": {
            "input_tokens": 0,
            "output_tokens": 0,
            "cache_creation_tokens": 0,
            "cache_read_tokens": 0,
            "total_tokens": 0,
        },
        "model_usage": {},
        "tools": {},
        "files": {},
        "prompt_preview": row["goal"],
        "duration_ms": 1,
        "cwd": None,
        "last_message_at": None,
        "events": {
            "prompts": [
                {
                    "index": 0,
                    "ts_ms": row["ordinal"] + 1,
                    "text_hash": row["goal_sha256"][:12],
                    "preview": row["goal"],
                }
            ],
            "tools": [],
            "llm_responses": [],
        },
    }


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n")


def prepare(args: argparse.Namespace) -> None:
    rows = read_rows(args.data_root)
    first_by_task: dict[str, dict] = {}
    for row in rows:
        first_by_task.setdefault(row["task"], row)
    preflight = [first_by_task[task] for task in ALIASES]
    write_json(args.raw_dir / "scorer-manifest.json", {"rows": rows})
    write_json(
        args.raw_dir / "agentboard-full.trace.json",
        {
            "schema": "agentsight.agent-session.trace.v1",
            "sessions": [trace_session(row) for row in rows],
        },
    )
    write_json(
        args.raw_dir / "agentboard-preflight.trace.json",
        {
            "schema": "agentsight.agent-session.trace.v1",
            "sessions": [trace_session(row) for row in preflight],
        },
    )
    print(
        json.dumps(
            {
                "status": "ok",
                "rows": len(rows),
                "preflight_rows": len(preflight),
                "class_counts": dict(Counter(row["task"] for row in rows)),
            },
            sort_keys=True,
        )
    )


def classification_metrics(targets: list[str], predictions: list[str]) -> dict:
    labels = list(ALIASES.values())
    per_label: dict[str, dict] = {}
    f1s: list[float] = []
    correct = sum(target == prediction for target, prediction in zip(targets, predictions))
    for label in labels:
        tp = sum(t == label and p == label for t, p in zip(targets, predictions))
        fp = sum(t != label and p == label for t, p in zip(targets, predictions))
        fn = sum(t == label and p != label for t, p in zip(targets, predictions))
        support = sum(t == label for t in targets)
        precision = tp / (tp + fp) if tp + fp else 0.0
        recall = tp / (tp + fn) if tp + fn else 0.0
        f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
        f1s.append(f1)
        per_label[label] = {
            "support": support,
            "precision": precision,
            "recall": recall,
            "f1": f1,
        }
    confusion = {
        target: {
            prediction: sum(
                t == target and p == prediction
                for t, p in zip(targets, predictions)
            )
            for prediction in labels
        }
        for target in labels
    }
    return {
        "rows": len(targets),
        "accuracy": correct / len(targets),
        "macro_f1": sum(f1s) / len(f1s),
        "per_label": per_label,
        "confusion": confusion,
    }


def read_predictions(path: Path) -> dict[str, dict[str, str]]:
    payload = json.loads(path.read_text())
    sessions = payload.get("sessions")
    if not isinstance(sessions, list):
        raise SystemExit(f"profile has no session rows: {path}")
    predictions = {}
    for session in sessions:
        session_id = session.get("session_id")
        raw_tag = session.get("session_tag")
        task_tag = session.get("task_tag")
        if not all(isinstance(value, str) and value for value in (session_id, raw_tag, task_tag)):
            raise SystemExit(f"missing raw/canonical prediction in {path}: {session}")
        if session_id in predictions:
            raise SystemExit(f"duplicate session prediction in {path}: {session_id}")
        predictions[session_id] = {"raw_tag": raw_tag, "task_tag": task_tag}
    return predictions


def score(args: argparse.Namespace) -> None:
    rows = json.loads(args.manifest.read_text())["rows"]
    repetitions = [read_predictions(path) for path in args.profiles]
    expected_ids = {row["session_id"] for row in rows}
    for path, predictions in zip(args.profiles, repetitions):
        if set(predictions) != expected_ids:
            missing = sorted(expected_ids - set(predictions))[:5]
            extra = sorted(set(predictions) - expected_ids)[:5]
            raise SystemExit(f"population mismatch in {path}: missing={missing} extra={extra}")

    targets = [row["target_tag"] for row in rows]
    candidate = [repetitions[0][row["session_id"]]["task_tag"] for row in rows]
    raw = [repetitions[0][row["session_id"]]["raw_tag"] for row in rows]
    majority = ["webshop"] * len(rows)
    allowed = set(ALIASES.values())
    candidate_stable = sum(
        len({rep[row["session_id"]]["task_tag"] for rep in repetitions}) == 1
        for row in rows
    )
    raw_stable = sum(
        len({rep[row["session_id"]]["raw_tag"] for rep in repetitions}) == 1
        for row in rows
    )
    valid = sum(prediction in allowed for rep in repetitions for prediction in (
        rep[row["session_id"]]["task_tag"] for row in rows
    ))
    candidate_metrics = classification_metrics(targets, candidate)
    raw_metrics = classification_metrics(targets, raw)
    majority_metrics = classification_metrics(targets, majority)
    supported = (
        candidate_metrics["macro_f1"] >= 0.80
        and candidate_metrics["accuracy"] >= 0.80
        and candidate_metrics["macro_f1"] > majority_metrics["macro_f1"]
        and candidate_metrics["accuracy"] > majority_metrics["accuracy"]
        and valid == len(rows) * len(repetitions)
    )
    output = {
        "status": "ok",
        "population": len(rows),
        "repetitions": len(repetitions),
        "candidate": candidate_metrics,
        "open_vocabulary_context": raw_metrics,
        "majority_control": majority_metrics,
        "candidate_stability": candidate_stable / len(rows),
        "open_vocabulary_stability": raw_stable / len(rows),
        "grammar_valid": valid,
        "grammar_total": len(rows) * len(repetitions),
        "support_rule": {
            "macro_f1_at_least": 0.80,
            "accuracy_at_least": 0.80,
            "beats_majority": True,
            "all_outputs_valid": True,
        },
        "hypothesis_supported": supported,
        "predictions": [
            {
                "ordinal": row["ordinal"],
                "session_id": row["session_id"],
                "target_tag": row["target_tag"],
                "raw_tags": [rep[row["session_id"]]["raw_tag"] for rep in repetitions],
                "task_tags": [rep[row["session_id"]]["task_tag"] for rep in repetitions],
            }
            for row in rows
        ],
    }
    write_json(args.output, output)
    print(
        json.dumps(
            {
                "status": "ok",
                "candidate_macro_f1": candidate_metrics["macro_f1"],
                "candidate_accuracy": candidate_metrics["accuracy"],
                "candidate_stability": candidate_stable / len(rows),
                "hypothesis_supported": supported,
            },
            sort_keys=True,
        )
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    commands = parser.add_subparsers(dest="command", required=True)
    prepare_parser = commands.add_parser("prepare")
    prepare_parser.add_argument("--data-root", type=Path, required=True)
    prepare_parser.add_argument("--raw-dir", type=Path, required=True)
    prepare_parser.set_defaults(func=prepare)
    score_parser = commands.add_parser("score")
    score_parser.add_argument("--manifest", type=Path, required=True)
    score_parser.add_argument("--profiles", type=Path, nargs=3, required=True)
    score_parser.add_argument("--output", type=Path, required=True)
    score_parser.set_defaults(func=score)
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
