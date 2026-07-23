#!/usr/bin/env python3
"""Score and build the recursive AgentRewardBench differential pprof.

This post-annotation evaluator is intentionally separate from the source-only
workspace materializer.  It may read expert labels and the fixed pair list only
after the backend's annotation has been persisted and applied to trace.jsonl.
It regenerates both the recursive candidate and fixed-chain baseline from the
same pair-expanded operation rows.
"""

from __future__ import annotations

import argparse
import csv
import gzip
import json
import re
import subprocess
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable

import numpy as np
from sklearn.metrics import average_precision_score


RECOVERY_OPERATION = "recover interaction"
COMPLETION_OPERATION = "report completion"
RECURSIVE_STACK = "agent,operation,call_id,tool"
FIXED_STACK = "task,subtask,strategy,action,object,result"
BOOTSTRAP_SEED = 20260722
BOOTSTRAP_DRAWS = 10_000


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset-root", type=Path, required=True)
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--pair-file", type=Path, required=True)
    parser.add_argument("--bad-operations", type=Path, required=True)
    parser.add_argument("--good-operations", type=Path, required=True)
    parser.add_argument("--agentpprof", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    return parser.parse_args()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def sanitize_slug(value: str) -> str:
    value = re.sub(r"[^A-Za-z0-9._-]+", "-", value).strip("-.")
    return value[:120] or "unknown"


def source_session_id(benchmark: str, task_id: str, model: str) -> str:
    return "__".join(sanitize_slug(part) for part in (benchmark, task_id, model))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as stream:
        return [json.loads(line) for line in stream if line.strip()]


def write_jsonl(path: Path, values: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as stream:
        for value in values:
            stream.write(json.dumps(value, ensure_ascii=False, sort_keys=True) + "\n")


def applied_paths(trace_file: Path) -> dict[str, list[str]]:
    paths = {}
    for node in read_jsonl(trace_file):
        if node["kind"] != "tool":
            continue
        evidence_id = str(node["data"]["evidence_id"])
        path = [str(value) for value in node.get("path") or []]
        require(bool(path), f"tool source {evidence_id} has no applied semantic path")
        require(evidence_id not in paths, f"duplicate workspace evidence ID: {evidence_id}")
        paths[evidence_id] = path
    require(bool(paths), "workspace contains no tool evidence")
    return paths


def source_key(record: dict[str, Any]) -> tuple[str, str, int]:
    fields = record["fields"]
    return (
        str(fields["source_session"]),
        str(fields["evidence_id"]),
        int(record.get("value", 1)),
    )


def recursive_records(
    records: list[dict[str, Any]], paths: dict[str, list[str]]
) -> list[dict[str, Any]]:
    output = []
    for record in records:
        fields = dict(record["fields"])
        evidence_id = str(fields["evidence_id"])
        require(evidence_id in paths, f"pair-expanded source is absent from workspace: {evidence_id}")
        fields["operation"] = paths[evidence_id]
        fields["call_id"] = evidence_id
        fields["tool"] = str(fields.get("action", "unknown"))
        fields["source_kind"] = "tool"
        output.append({"value": int(record.get("value", 1)), "fields": fields})
    return output


def run_profile(
    binary: Path,
    candidate: Path,
    base: Path,
    stack: str,
    output: Path,
) -> dict[str, Any]:
    command = [
        str(binary),
        "--operation-file",
        str(candidate),
        "--diff-base-operation-file",
        str(base),
        "--view",
        "operations",
        "--stack",
        stack,
        "--deterministic-output",
        "--output",
        str(output),
    ]
    run = subprocess.run(command, check=False, capture_output=True, text=True)
    require(run.returncode == 0, f"AgentPProf failed: {' '.join(command)}\n{run.stderr}")
    with gzip.open(output, "rb") as stream:
        require(bool(stream.read(1)), f"empty pprof: {output}")
    readback = subprocess.run(
        ["go", "tool", "pprof", "-top", str(output)],
        check=False,
        capture_output=True,
        text=True,
    )
    require(readback.returncode == 0, f"go tool pprof rejected {output}: {readback.stderr}")
    return {
        "command": command,
        "agentpprof": json.loads(run.stdout),
        "pprof_top": readback.stdout,
    }


def consensus_looping(dataset_root: Path) -> dict[str, bool | None]:
    grouped: dict[str, list[str]] = defaultdict(list)
    with (dataset_root / "data" / "annotations.csv").open(
        newline="", encoding="utf-8"
    ) as stream:
        for row in csv.DictReader(stream):
            session = source_session_id(
                row["benchmark"], row["task_id"], row["model_name"]
            )
            grouped[session].append(row["trajectory_looping"])
    output = {}
    for session, values in grouped.items():
        observed = set(values)
        require(
            observed <= {"Yes", "No"},
            f"unexpected trajectory_looping value for {session}: {sorted(observed)}",
        )
        output[session] = next(iter(observed)) == "Yes" if len(observed) == 1 else None
    return output


def unique_session_rows(
    bad: list[dict[str, Any]],
    good: list[dict[str, Any]],
    paths: dict[str, list[str]],
) -> dict[str, dict[str, Any]]:
    unique: dict[str, dict[str, Any]] = {}
    for record in [*bad, *good]:
        fields = record["fields"]
        evidence_id = str(fields["evidence_id"])
        session = str(fields["source_session"])
        row = unique.setdefault(
            evidence_id,
            {
                "session": session,
                "recovery": RECOVERY_OPERATION in paths[evidence_id],
                "fixed_problem": str(fields.get("result", "")).startswith("error:")
                or str(fields.get("result", "")) == "repeated",
            },
        )
        require(row["session"] == session, f"evidence session mismatch: {evidence_id}")
    by_session: dict[str, dict[str, Any]] = {}
    for row in unique.values():
        summary = by_session.setdefault(
            row["session"], {"operations": 0, "recovery": 0, "fixed_problem": 0}
        )
        summary["operations"] += 1
        summary["recovery"] += int(row["recovery"])
        summary["fixed_problem"] += int(row["fixed_problem"])
    for row in by_session.values():
        row["recursive_score"] = row["recovery"] / row["operations"]
        row["fixed_score"] = row["fixed_problem"] / row["operations"]
    return by_session


def task_by_session(pair_rows: list[dict[str, Any]]) -> dict[str, str]:
    output = {}
    for pair in pair_rows:
        task = f"{pair['benchmark']}::{pair['canonical_task']}"
        for side in ("bad", "good"):
            session = str(pair[side])
            previous = output.setdefault(session, task)
            require(previous == task, f"session belongs to multiple task IDs: {session}")
    return output


def ap(values: list[bool], scores: list[float]) -> float:
    require(any(values) and not all(values), "average precision needs both classes")
    return float(average_precision_score(np.asarray(values, dtype=int), np.asarray(scores)))


def score_looping(
    sessions: dict[str, dict[str, Any]],
    looping: dict[str, bool | None],
    tasks: dict[str, str],
) -> dict[str, Any]:
    eligible = [
        session
        for session in sorted(sessions)
        if looping.get(session) is not None and session in tasks
    ]
    labels = [bool(looping[session]) for session in eligible]
    recursive = [float(sessions[session]["recursive_score"]) for session in eligible]
    fixed = [float(sessions[session]["fixed_score"]) for session in eligible]
    task_groups: dict[str, list[str]] = defaultdict(list)
    for session in eligible:
        task_groups[tasks[session]].append(session)
    task_ids = sorted(task_groups)

    recursive_ap = ap(labels, recursive)
    fixed_ap = ap(labels, fixed)
    prevalence = sum(labels) / len(labels)
    rng = np.random.default_rng(BOOTSTRAP_SEED)
    recursive_minus_prevalence = []
    recursive_minus_fixed = []
    for _ in range(BOOTSTRAP_DRAWS):
        sampled_tasks = rng.choice(task_ids, size=len(task_ids), replace=True)
        sampled_sessions = [
            session for task in sampled_tasks for session in task_groups[str(task)]
        ]
        sampled_labels = [bool(looping[session]) for session in sampled_sessions]
        if not any(sampled_labels) or all(sampled_labels):
            continue
        candidate = ap(
            sampled_labels,
            [float(sessions[session]["recursive_score"]) for session in sampled_sessions],
        )
        baseline = ap(
            sampled_labels,
            [float(sessions[session]["fixed_score"]) for session in sampled_sessions],
        )
        sampled_prevalence = sum(sampled_labels) / len(sampled_labels)
        recursive_minus_prevalence.append(candidate - sampled_prevalence)
        recursive_minus_fixed.append(candidate - baseline)

    def interval(values: list[float]) -> list[float]:
        return [
            float(np.quantile(values, 0.025)),
            float(np.quantile(values, 0.975)),
        ]

    prevalence_interval = interval(recursive_minus_prevalence)
    fixed_interval = interval(recursive_minus_fixed)
    if prevalence_interval[0] > 0:
        hypothesis = "supported"
    elif prevalence_interval[1] < 0:
        hypothesis = "contradicted"
    else:
        hypothesis = "inconclusive"
    if fixed_interval[0] > 0:
        fixed_comparison = "recursive higher"
    elif fixed_interval[1] < 0:
        fixed_comparison = "recursive lower"
    else:
        fixed_comparison = "indistinguishable"
    return {
        "trajectories": len(eligible),
        "positive_looping": sum(labels),
        "negative_looping": len(labels) - sum(labels),
        "tasks": len(task_ids),
        "recursive_ap": recursive_ap,
        "fixed_chain_ap": fixed_ap,
        "prevalence": prevalence,
        "recursive_minus_prevalence_95ci": prevalence_interval,
        "recursive_minus_fixed_95ci": fixed_interval,
        "bootstrap_draws": len(recursive_minus_prevalence),
        "bootstrap_seed": BOOTSTRAP_SEED,
        "tested_hypothesis": hypothesis,
        "fixed_chain_comparison": fixed_comparison,
    }


def write_results_markdown(summary: dict[str, Any]) -> str:
    score = summary["looping_score"]
    return f"""# Recursive AgentReward Differential Result

## Population And Fairness

- Unique source trajectories: {summary['population']['unique_sessions']}
- Mixed-outcome tasks: {summary['population']['tasks']}
- Bad--good pair occurrences: {summary['population']['pairs']}
- Bad-side operation occurrences: {summary['population']['bad_occurrences']}
- Good-side operation occurrences: {summary['population']['good_occurrences']}
- Candidate/baseline source multiset equality: {summary['fairness']['same_source_multiset']}

## Independent Expert-Looping Endpoint

- Consensus-scored trajectories: {score['trajectories']}
- Expert looping positives/negatives: {score['positive_looping']} / {score['negative_looping']}
- Recursive recovery-path AP: {score['recursive_ap']:.6f}
- Fixed-chain repeated/error AP: {score['fixed_chain_ap']:.6f}
- Expert-looping prevalence: {score['prevalence']:.6f}
- Recursive minus prevalence 95% task-cluster interval:
  `[{score['recursive_minus_prevalence_95ci'][0]:+.6f},
  {score['recursive_minus_prevalence_95ci'][1]:+.6f}]`
- Recursive minus fixed-chain 95% task-cluster interval:
  `[{score['recursive_minus_fixed_95ci'][0]:+.6f},
  {score['recursive_minus_fixed_95ci'][1]:+.6f}]`
- Tested correspondence hypothesis: **{score['tested_hypothesis']}**
- Incremental comparison: **{score['fixed_chain_comparison']}**

## Profiles

- Recursive signed pprof: `{summary['profiles']['recursive']}`
- Fresh fixed-chain signed pprof: `{summary['profiles']['fixed_chain']}`

The signed profile is descriptive of bad-minus-good pair occurrences. The
expert-looping AP endpoint is computed on unique trajectories and is the
independent RQ2 correspondence test. Figure depth and hierarchy warnings are
descriptive product QA, not scientific support.
"""


def main() -> None:
    args = parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    paths = applied_paths(args.workspace / "trace.jsonl")
    bad = read_jsonl(args.bad_operations)
    good = read_jsonl(args.good_operations)
    pair_rows = json.loads(args.pair_file.read_text(encoding="utf-8"))

    recursive_bad = recursive_records(bad, paths)
    recursive_good = recursive_records(good, paths)
    fixed_bad = [{"value": int(row.get("value", 1)), "fields": dict(row["fields"])} for row in bad]
    fixed_good = [{"value": int(row.get("value", 1)), "fields": dict(row["fields"])} for row in good]
    require(
        Counter(source_key(row) for row in recursive_bad)
        == Counter(source_key(row) for row in fixed_bad),
        "recursive/fixed bad-side source multiset mismatch",
    )
    require(
        Counter(source_key(row) for row in recursive_good)
        == Counter(source_key(row) for row in fixed_good),
        "recursive/fixed good-side source multiset mismatch",
    )

    inputs = args.out / "inputs"
    recursive_bad_path = inputs / "recursive.bad.operations.jsonl"
    recursive_good_path = inputs / "recursive.good.operations.jsonl"
    fixed_bad_path = inputs / "fixed.bad.operations.jsonl"
    fixed_good_path = inputs / "fixed.good.operations.jsonl"
    write_jsonl(recursive_bad_path, recursive_bad)
    write_jsonl(recursive_good_path, recursive_good)
    write_jsonl(fixed_bad_path, fixed_bad)
    write_jsonl(fixed_good_path, fixed_good)

    recursive_profile = args.out / "recursive.bad-minus-good.operations.pb.gz"
    fixed_profile = args.out / "fixed.bad-minus-good.operations.pb.gz"
    recursive_run = run_profile(
        args.agentpprof, recursive_bad_path, recursive_good_path, RECURSIVE_STACK, recursive_profile
    )
    fixed_run = run_profile(
        args.agentpprof, fixed_bad_path, fixed_good_path, FIXED_STACK, fixed_profile
    )

    sessions = unique_session_rows(bad, good, paths)
    looping_score = score_looping(
        sessions,
        consensus_looping(args.dataset_root),
        task_by_session(pair_rows),
    )
    summary = {
        "population": {
            "unique_sessions": len(sessions),
            "tasks": len({f"{row['benchmark']}::{row['canonical_task']}" for row in pair_rows}),
            "pairs": len(pair_rows),
            "bad_occurrences": sum(int(row.get("value", 1)) for row in bad),
            "good_occurrences": sum(int(row.get("value", 1)) for row in good),
        },
        "fairness": {
            "same_source_multiset": True,
            "recursive_bad_rows": len(recursive_bad),
            "recursive_good_rows": len(recursive_good),
            "fixed_bad_rows": len(fixed_bad),
            "fixed_good_rows": len(fixed_good),
        },
        "looping_score": looping_score,
        "profiles": {
            "recursive": str(recursive_profile),
            "fixed_chain": str(fixed_profile),
        },
        "runs": {"recursive": recursive_run, "fixed_chain": fixed_run},
        "focus_operations": {
            "recovery": RECOVERY_OPERATION,
            "completion": COMPLETION_OPERATION,
        },
    }
    (args.out / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (args.out / "results.md").write_text(
        write_results_markdown(summary), encoding="utf-8"
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
