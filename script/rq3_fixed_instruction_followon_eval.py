#!/usr/bin/env python3
"""Score the fixed-instruction CodeTrace follow-on population.

This script does not construct, alter, or tune annotations. It filters the
already accepted complete A2 and baseline score rows by the manifest-defined
364-session follow-on population, then recomputes standard B-cubed and exact
adjacent-boundary metrics.
"""

from __future__ import annotations

import argparse
import json
import random
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable


METHODS = ("candidate", "multires_recurrence", "native_tree", "native_turn")
EXPECTED_SESSIONS = 364
EXPECTED_EXCLUDED_SESSIONS = 41
EXPECTED_OPERATIONS = 15_116
EXPECTED_PAIRS = 14_752
EXPECTED_TASKS = 238
EXPECTED_FRAMEWORKS = {
    "OpenHands": 202,
    "SWE-agent": 26,
    "Terminus2": 65,
    "mini-SWE-agent": 71,
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def read_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as source:
        return json.load(source)


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as source:
        for line_number, line in enumerate(source, 1):
            if not line.strip():
                continue
            row = json.loads(line)
            require(isinstance(row, dict), f"{path}:{line_number}: expected object")
            rows.append(row)
    return rows


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as sink:
        for row in rows:
            sink.write(json.dumps(row, sort_keys=True) + "\n")


def manifest_sessions(path: Path) -> tuple[dict[str, Any], set[str]]:
    manifest = read_json(path)
    require(isinstance(manifest, dict), f"{path}: manifest must be an object")
    batches = manifest.get("batches")
    require(isinstance(batches, list), f"{path}: batches must be a list")
    sessions = [
        str(session)
        for batch in batches
        for session in batch.get("session_ids", [])
    ]
    require(len(sessions) == len(set(sessions)), f"{path}: duplicate session")
    return manifest, set(sessions)


def percentile(values: list[float], probability: float) -> float:
    require(bool(values), "percentile requires values")
    ordered = sorted(values)
    position = (len(ordered) - 1) * probability
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    fraction = position - lower
    return ordered[lower] * (1.0 - fraction) + ordered[upper] * fraction


def bcubed(rows: list[dict[str, Any]], method: str) -> dict[str, Any]:
    require(bool(rows), "B-cubed requires operation rows")
    predicted = Counter(str(row[method]) for row in rows)
    official = Counter(str(row["official_stage"]) for row in rows)
    overlap = Counter(
        (str(row[method]), str(row["official_stage"])) for row in rows
    )
    precision_sum = sum(
        overlap[(str(row[method]), str(row["official_stage"]))]
        / predicted[str(row[method])]
        for row in rows
    )
    recall_sum = sum(
        overlap[(str(row[method]), str(row["official_stage"]))]
        / official[str(row["official_stage"])]
        for row in rows
    )
    precision = precision_sum / len(rows)
    recall = recall_sum / len(rows)
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {
        "operations": len(rows),
        "predicted_groups": len(predicted),
        "official_groups": len(official),
        "precision": precision,
        "recall": recall,
        "f1": f1,
    }


def boundary(rows: list[dict[str, Any]], method: str) -> dict[str, Any]:
    tp = sum(bool(row[method]) and bool(row["official_boundary"]) for row in rows)
    fp = sum(bool(row[method]) and not bool(row["official_boundary"]) for row in rows)
    fn = sum(not bool(row[method]) and bool(row["official_boundary"]) for row in rows)
    tn = sum(
        not bool(row[method]) and not bool(row["official_boundary"]) for row in rows
    )
    return {
        "pairs": len(rows),
        "true_positive": tp,
        "false_positive": fp,
        "false_negative": fn,
        "true_negative": tn,
        "precision": tp / (tp + fp) if tp + fp else 0.0,
        "recall": tp / (tp + fn) if tp + fn else 0.0,
        "f1": 2 * tp / (2 * tp + fp + fn) if 2 * tp + fp + fn else 0.0,
    }


def metric_bundle(
    operation_rows: list[dict[str, Any]], pair_rows: list[dict[str, Any]]
) -> dict[str, Any]:
    return {
        method: {
            "bcubed": bcubed(operation_rows, method),
            "boundary": boundary(pair_rows, method),
        }
        for method in METHODS
    }


def bootstrap(
    rows: list[dict[str, Any]], resamples: int, seed: int
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    by_task: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_task[str(row["task_name"])].append(row)
    tasks = sorted(by_task)
    require(len(tasks) == EXPECTED_TASKS, "bootstrap task-cluster count")

    sufficient: dict[tuple[str, str], tuple[int, float, float]] = {}
    for task, task_rows in by_task.items():
        for method in ("candidate", "multires_recurrence"):
            metric = bcubed(task_rows, method)
            count = len(task_rows)
            sufficient[(task, method)] = (
                count,
                float(metric["precision"]) * count,
                float(metric["recall"]) * count,
            )

    def sampled_f1(draw: list[str], method: str) -> float:
        count = 0
        precision_sum = 0.0
        recall_sum = 0.0
        for task in draw:
            local_count, local_precision, local_recall = sufficient[(task, method)]
            count += local_count
            precision_sum += local_precision
            recall_sum += local_recall
        precision = precision_sum / count
        recall = recall_sum / count
        return 2 * precision * recall / (precision + recall) if precision + recall else 0.0

    generator = random.Random(seed)
    draws: list[dict[str, Any]] = []
    deltas: list[float] = []
    for index in range(resamples):
        draw = generator.choices(tasks, k=len(tasks))
        delta = sampled_f1(draw, "candidate") - sampled_f1(
            draw, "multires_recurrence"
        )
        deltas.append(delta)
        draws.append({"resample": index, "delta": delta})

    return (
        {
            "candidate": "candidate",
            "baseline": "multires_recurrence",
            "resamples": resamples,
            "seed": seed,
            "task_clusters": len(tasks),
            "mean_delta": sum(deltas) / len(deltas),
            "ci95": [percentile(deltas, 0.025), percentile(deltas, 0.975)],
            "positive_fraction": sum(delta > 0 for delta in deltas) / len(deltas),
        },
        draws,
    )


def load_and_validate(
    manifest_path: Path,
    excluded_manifest_path: Path,
    operation_path: Path,
    pair_path: Path,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    manifest, selected = manifest_sessions(manifest_path)
    excluded_manifest, excluded = manifest_sessions(excluded_manifest_path)
    require(len(selected) == EXPECTED_SESSIONS, "selected session count")
    require(len(excluded) == EXPECTED_EXCLUDED_SESSIONS, "excluded session count")
    require(not (selected & excluded), "selected and initial sessions overlap")
    require(manifest.get("sessions") == EXPECTED_SESSIONS, "manifest session count")
    require(manifest.get("operations") == EXPECTED_OPERATIONS, "manifest operation count")
    require(
        excluded_manifest.get("sessions") == EXPECTED_EXCLUDED_SESSIONS,
        "excluded manifest session count",
    )

    all_operations = read_jsonl(operation_path)
    all_pairs = read_jsonl(pair_path)
    operation_rows = [row for row in all_operations if str(row["session"]) in selected]
    pair_rows = [row for row in all_pairs if str(row["session"]) in selected]

    require(len(operation_rows) == EXPECTED_OPERATIONS, "follow-on operation count")
    require(len(pair_rows) == EXPECTED_PAIRS, "follow-on adjacent-pair count")
    operation_sessions = {str(row["session"]) for row in operation_rows}
    pair_sessions = {str(row["session"]) for row in pair_rows}
    require(operation_sessions == selected, "operation session join")
    require(pair_sessions == selected, "pair session join")
    require(
        not ({str(row["session"]) for row in operation_rows} & excluded),
        "initial session leaked into operations",
    )
    require(
        not ({str(row["session"]) for row in pair_rows} & excluded),
        "initial session leaked into pairs",
    )

    operation_keys = [
        (str(row["session"]), int(row["step_id"])) for row in operation_rows
    ]
    pair_keys = [
        (str(row["session"]), int(row["position"])) for row in pair_rows
    ]
    require(len(operation_keys) == len(set(operation_keys)), "duplicate operation key")
    require(len(pair_keys) == len(set(pair_keys)), "duplicate pair key")
    for row in operation_rows:
        require(
            all(row.get(method) is not None for method in METHODS),
            "incomplete operation assignment",
        )
        require(row.get("official_stage") is not None, "missing official stage")
        require(row.get("task_name") is not None, "missing task name")
        require(row.get("framework") is not None, "missing framework")
    for row in pair_rows:
        require(
            all(isinstance(row.get(method), bool) for method in METHODS),
            "incomplete boundary assignment",
        )
        require(
            isinstance(row.get("official_boundary"), bool),
            "missing official boundary",
        )

    first_by_session: dict[str, dict[str, Any]] = {}
    for row in operation_rows:
        first_by_session.setdefault(str(row["session"]), row)
    frameworks = Counter(str(row["framework"]) for row in first_by_session.values())
    require(dict(frameworks) == EXPECTED_FRAMEWORKS, "framework population")
    tasks = {str(row["task_name"]) for row in operation_rows}
    require(len(tasks) == EXPECTED_TASKS, "task-cluster population")

    audit = {
        "selection": manifest.get("selection"),
        "sessions": len(selected),
        "excluded_initial_sessions": len(excluded),
        "operations": len(operation_rows),
        "pairs": len(pair_rows),
        "task_clusters": len(tasks),
        "framework_sessions": dict(sorted(frameworks.items())),
        "operation_session_join_complete": operation_sessions == selected,
        "pair_session_join_complete": pair_sessions == selected,
        "initial_sessions_excluded": not bool(selected & excluded),
    }
    return operation_rows, pair_rows, audit


def result_report(summary: dict[str, Any]) -> str:
    lines = [
        "# RQ3 Fixed-Instruction Follow-On Result",
        "",
        f"- mode: `{summary['mode']}`",
        f"- status: `{summary['status']}`",
        f"- sessions: {summary['population']['sessions']}",
        f"- operations: {summary['population']['operations']}",
        f"- task clusters: {summary['population']['task_clusters']}",
        "",
        "| Method | B³ P | B³ R | B³ F1 | Boundary F1 |",
        "|---|---:|---:|---:|---:|",
    ]
    for method in METHODS:
        metric = summary["metrics"][method]
        lines.append(
            f"| {method} | {metric['bcubed']['precision']:.6f} | "
            f"{metric['bcubed']['recall']:.6f} | "
            f"{metric['bcubed']['f1']:.6f} | "
            f"{metric['boundary']['f1']:.6f} |"
        )
    bootstrap_result = summary["bootstrap"]["candidate_minus_recurrence"]
    lines.extend(
        [
            "",
            "## Paired task-cluster inference",
            "",
            f"- mean B³ F1 delta: {bootstrap_result['mean_delta']:.6f}",
            f"- 95% interval: [{bootstrap_result['ci95'][0]:.6f}, "
            f"{bootstrap_result['ci95'][1]:.6f}]",
            f"- decision: **{summary['decision']}**",
            "",
            "## Scope",
            "",
            "This is a manifest-defined post-aggregate analysis of the complete "
            "364-session follow-on population. It excludes the initial 41-session "
            "product collection, but it remains part of the already observed "
            "CodeTrace development family. It evaluates flat partition and exact "
            "boundary fidelity, not semantic-name correctness, nested topology, "
            "or cross-family generalization.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("preflight", "full"))
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--excluded-manifest", type=Path, required=True)
    parser.add_argument("--operation-rows", type=Path, required=True)
    parser.add_argument("--pair-rows", type=Path, required=True)
    parser.add_argument("--bootstrap-resamples", type=int, default=10_000)
    parser.add_argument("--seed", type=int, default=20_260_723)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    operation_rows, pair_rows, audit = load_and_validate(
        args.manifest, args.excluded_manifest, args.operation_rows, args.pair_rows
    )
    args.out.mkdir(parents=True, exist_ok=True)
    write_json(args.out / "population-audit.json", audit)

    if args.mode == "preflight":
        write_json(
            args.out / "summary.json",
            {
                "mode": "preflight",
                "status": "pass",
                "population": audit,
                "paper_result": False,
            },
        )
        print(json.dumps({"status": "pass", **audit}, sort_keys=True))
        return

    require(args.bootstrap_resamples == 10_000, "full run requires 10,000 resamples")
    metrics = metric_bundle(operation_rows, pair_rows)
    bootstrap_result, draws = bootstrap(
        operation_rows, args.bootstrap_resamples, args.seed
    )
    candidate_f1 = float(metrics["candidate"]["bcubed"]["f1"])
    baseline_f1 = float(metrics["multires_recurrence"]["bcubed"]["f1"])
    lower, upper = bootstrap_result["ci95"]
    decision = (
        "supported"
        if candidate_f1 > baseline_f1 and lower > 0
        else "contradicted"
        if upper <= 0
        else "inconclusive"
    )

    per_framework = {}
    for framework in sorted(EXPECTED_FRAMEWORKS):
        local_operations = [
            row for row in operation_rows if str(row["framework"]) == framework
        ]
        local_pairs = [
            row for row in pair_rows if str(row["framework"]) == framework
        ]
        per_framework[framework] = metric_bundle(local_operations, local_pairs)

    summary = {
        "mode": "full",
        "status": "complete",
        "population": audit,
        "metrics": metrics,
        "per_framework": per_framework,
        "bootstrap": {"candidate_minus_recurrence": bootstrap_result},
        "decision": decision,
        "claim_boundary": (
            "Manifest-defined post-aggregate follow-on evidence within the "
            "already observed CodeTrace family; flat partition and exact "
            "adjacent-boundary fidelity only."
        ),
    }
    write_jsonl(args.out / "operation-score-rows.jsonl", operation_rows)
    write_jsonl(args.out / "pair-score-rows.jsonl", pair_rows)
    write_jsonl(
        args.out / "bootstrap-candidate-minus-recurrence.jsonl", draws
    )
    write_json(args.out / "summary.json", summary)
    (args.out / "result-report.md").write_text(
        result_report(summary), encoding="utf-8"
    )
    print(json.dumps({"status": "complete", "decision": decision}, sort_keys=True))


if __name__ == "__main__":
    main()
