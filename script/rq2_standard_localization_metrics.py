#!/usr/bin/env python3
"""Compute standard trajectory-level MAP from completed RQ2 artifacts.

The command is deliberately read-only with respect to its three input roots.
It reconstructs the fixed scores used by the completed AgentProcessBench,
HINTBench, and TraceElephant experiments, then calls scikit-learn's
non-interpolated average_precision_score for each target-bearing trajectory.
"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from dataclasses import dataclass
import json
import math
from pathlib import Path
import random
import statistics
from typing import Any, Iterable, Mapping, Sequence

from sklearn import __version__ as sklearn_version
from sklearn.metrics import average_precision_score


DEFAULT_AGENTPROCESS = Path("docs/visexp/out/agentprocessbench-rq2/full")
DEFAULT_HINT = Path(
    "docs/tmp/cycle-0003-20260713T121925-0700/01-experiment-gate/"
    "loop-001-rq2-hintbench/results/full"
)
DEFAULT_TRACE = Path(".agentsight/experiments/traceelephant-rq2-v1")
DEFAULT_OUT = Path(".agentsight/experiments/rq2-standard-map-existing-trajectories-v1")

EXPECTED = {
    "AgentProcessBench": (1000, 8509, 614),
    "HINTBench": (536, 12877, 400),
    "TraceElephant": (220, 5960, 220),
}


class ExperimentError(RuntimeError):
    pass


@dataclass(frozen=True)
class Operation:
    query_id: str
    stratum: str
    cluster: str
    label: int
    scores: Mapping[str, float]


@dataclass(frozen=True)
class Benchmark:
    name: str
    source_trajectories: int
    operations: Sequence[Operation]
    official_targets: Mapping[str, int]


def read_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: Iterable[Mapping[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")


def parse_score(value: Any) -> float:
    if isinstance(value, str):
        return float.fromhex(value)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ExperimentError(f"invalid scalar score {value!r}")
    return float(value)


def standard_ap(labels: Sequence[int], scores: Sequence[float]) -> float:
    if len(labels) != len(scores) or not labels or sum(labels) <= 0:
        raise ExperimentError("AP requires aligned nonempty arrays with a positive item")
    if not all(math.isfinite(value) for value in scores):
        raise ExperimentError("AP score is not finite")
    return float(average_precision_score(labels, scores))


def wilson_lower(hits: int, count: int) -> float:
    if count <= 0 or hits < 0 or hits > count:
        raise ExperimentError(f"invalid Wilson inputs h={hits}, n={count}")
    z = 1.959963984540054
    proportion = hits / count
    z2 = z * z
    return (
        proportion
        + z2 / (2.0 * count)
        - z
        * math.sqrt(
            proportion * (1.0 - proportion) / count
            + z2 / (4.0 * count * count)
        )
    ) / (1.0 + z2 / count)


def grouped_mean_scores(
    rows: Sequence[Mapping[str, Any]],
    method: str,
) -> dict[tuple[str, str], float]:
    sums: defaultdict[tuple[str, str], float] = defaultdict(float)
    counts: Counter[tuple[str, str]] = Counter()
    for row in rows:
        key = (str(row["family"]), str(row["groups"][method]))
        sums[key] += float(row["risk_units"])
        counts[key] += 1
    return {key: sums[key] / counts[key] for key in sums}


def load_agentprocess(root: Path) -> Benchmark:
    rows = read_jsonl(root / "group-assignments.jsonl")
    labels = {
        str(row["operation_id"]): int(row["human_label"])
        for row in read_jsonl(root / "labels.jsonl")
    }
    if len(labels) != len(rows):
        raise ExperimentError("AgentProcessBench label coverage mismatch")
    score_maps = {
        method: grouped_mean_scores(rows, method)
        for method in ("semantic", "raw_action", "session", "flat")
    }
    operations: list[Operation] = []
    for row in rows:
        operation_id = str(row["operation_id"])
        family = str(row["family"])
        operations.append(
            Operation(
                query_id=str(row["trajectory_id"]),
                stratum=family,
                cluster=str(row["task_id"]),
                label=int(labels[operation_id] == -1),
                scores={
                    "agentprof": score_maps["semantic"][(family, str(row["groups"]["semantic"]))],
                    "raw_action": score_maps["raw_action"][(family, str(row["groups"]["raw_action"]))],
                    "session": score_maps["session"][(family, str(row["groups"]["session"]))],
                    "flat": score_maps["flat"][(family, str(row["groups"]["flat"]))],
                    "atomic": float(row["risk_units"]),
                },
            )
        )
    query_ids = {row.query_id for row in operations}
    official = {
        query_id: sum(row.label for row in operations if row.query_id == query_id)
        for query_id in query_ids
    }
    return Benchmark("AgentProcessBench", len(query_ids), operations, official)


def hint_target_sets(source_rows: Sequence[Mapping[str, Any]]) -> dict[str, set[int]]:
    result: dict[str, set[int]] = {}
    for row in source_rows:
        key = f"test:{row['id']}"
        values: set[int] = set()
        for field in ("injected_risks", "risk_labels"):
            annotations = row.get(field, [])
            if not isinstance(annotations, list):
                raise ExperimentError(f"{key}: {field} is not a list")
            for annotation in annotations:
                if not isinstance(annotation, dict):
                    raise ExperimentError(f"{key}: invalid risk annotation")
                value = (
                    annotation.get("risk_origin_step")
                    if annotation.get("risk_origin_step") is not None
                    else annotation.get("step_id")
                )
                if isinstance(value, bool) or not isinstance(value, int):
                    raise ExperimentError(f"{key}: risk annotation has no integer target")
                values.add(value)
        result[key] = values
    return result


def grouped_wilson_scores(
    rows: Sequence[Mapping[str, Any]], keys: Sequence[str]
) -> dict[str, float]:
    counts: Counter[str] = Counter(keys)
    hits: Counter[str] = Counter()
    for row, key in zip(rows, keys, strict=True):
        hits[key] += int(row["localizer_hit"])
    return {key: wilson_lower(hits[key], counts[key]) for key in counts}


def load_hint(root: Path) -> Benchmark:
    rows = read_jsonl(root / "operations" / "test-projection.jsonl")
    point = read_json(root / "metrics" / "test-point-estimates.json")
    order = [str(value) for value in point["selected_order"]]
    identity = read_json(
        root / "profiles" / "test" / "__".join(order) / "identity.json"
    )
    leaves = [str(value) for value in identity["operation_leaves"]]
    if len(leaves) != len(rows) or identity["order"] != order:
        raise ExperimentError("HINTBench stored profile/order mismatch")
    agent_scores = {
        str(key): parse_score(value)
        for key, value in identity["agentprof_leaf_scores"].items()
    }
    flat_scores = {
        str(key): parse_score(value)
        for key, value in identity["flat_leaf_scores"].items()
    }
    if agent_scores != flat_scores:
        raise ExperimentError("HINTBench flat identity is not exact")
    raw_keys = [str(row["raw_fields"]["action"]) for row in rows]
    session_keys = [str(row["record_key"]) for row in rows]
    raw_scores = grouped_wilson_scores(rows, raw_keys)
    session_scores = grouped_wilson_scores(rows, session_keys)
    targets = hint_target_sets(read_json(root / "sources" / "test.json"))

    displayed: defaultdict[str, set[int]] = defaultdict(set)
    for row in rows:
        displayed[str(row["record_key"])].add(int(row["display_id"]))
    operations: list[Operation] = []
    for row, leaf, raw_key, session_key in zip(
        rows, leaves, raw_keys, session_keys, strict=True
    ):
        key = str(row["record_key"])
        operations.append(
            Operation(
                query_id=key,
                stratum=str(row["raw_fields"]["environment"]),
                cluster=key,
                label=int(int(row["display_id"]) in targets[key]),
                scores={
                    "agentprof": agent_scores[leaf],
                    "raw_action": raw_scores[raw_key],
                    "session": session_scores[session_key],
                    "flat_identity": flat_scores[leaf],
                    "atomic": float(int(row["localizer_hit"])),
                },
            )
        )
    mapped = {
        key: len(values & displayed[key]) for key, values in targets.items()
    }
    if sum(mapped.values()) != sum(row.label for row in operations):
        raise ExperimentError("HINTBench mapped target coverage mismatch")
    return Benchmark(
        "HINTBench",
        len(targets),
        operations,
        {key: len(value) for key, value in targets.items()},
    )


def method_operation_scores(method: Mapping[str, Any]) -> list[float]:
    leaves = [str(value) for value in method["operation_leaves"]]
    scores = {
        str(key): parse_score(value) for key, value in method["leaf_scores"].items()
    }
    return [scores[leaf] for leaf in leaves]


def load_trace(root: Path) -> Benchmark:
    rows = read_jsonl(root / "operations" / "projection.jsonl")
    method_index = read_json(root / "profiles" / "method-index.json")["methods"]
    source_names = {
        "agentprof": "agentprof",
        "raw_action": "raw",
        "session": "session",
        "source_native": "source_native",
        "flat": "flat",
        "atomic": "independent_step",
    }
    method_scores = {
        target: method_operation_scores(method_index[source])
        for target, source in source_names.items()
    }
    if any(len(values) != len(rows) for values in method_scores.values()):
        raise ExperimentError("TraceElephant method/operation coverage mismatch")
    targets = {
        str(row["trace_id"]): int(row["mistake_step"])
        for row in read_jsonl(root / "scorer" / "targets.jsonl")
    }
    operations: list[Operation] = []
    for index, row in enumerate(rows):
        trace_id = str(row["trace_id"])
        operations.append(
            Operation(
                query_id=trace_id,
                stratum=str(row["cell"]),
                cluster=trace_id,
                label=int(int(row["step_id"]) == targets[trace_id]),
                scores={method: values[index] for method, values in method_scores.items()},
            )
        )
    return Benchmark(
        "TraceElephant",
        len(targets),
        operations,
        {key: 1 for key in targets},
    )


def nearest_rank_interval(values: Sequence[float]) -> list[float]:
    ordered = sorted(values)
    if not ordered:
        raise ExperimentError("empty bootstrap")
    lower = math.ceil(0.025 * len(ordered)) - 1
    upper = math.ceil(0.975 * len(ordered)) - 1
    return [ordered[lower], ordered[upper]]


def paired_bootstrap(
    rows: Sequence[Mapping[str, Any]],
    repetitions: int,
    seed: int,
    cluster_universe: Mapping[str, Sequence[str]] | None = None,
) -> tuple[list[float], dict[str, Any]]:
    by_stratum: defaultdict[str, defaultdict[str, list[float]]] = defaultdict(
        lambda: defaultdict(list)
    )
    for row in rows:
        by_stratum[str(row["stratum"])][str(row["cluster"])].append(
            float(row["ap"]["agentprof"] - row["ap"]["raw_action"])
        )
    if cluster_universe is not None:
        for stratum, clusters in cluster_universe.items():
            for cluster in clusters:
                by_stratum[str(stratum)][str(cluster)]
    rng = random.Random(seed)
    draws: list[float] = []
    for _ in range(repetitions):
        sample: list[float] = []
        for clusters in by_stratum.values():
            keys = sorted(clusters)
            for _ in keys:
                sample.extend(clusters[rng.choice(keys)])
        if not sample:
            raise ExperimentError("bootstrap selected no target-bearing query")
        draws.append(statistics.fmean(sample))
    return draws, {
        "repetitions": repetitions,
        "seed": seed,
        "strata": len(by_stratum),
        "clusters": sum(len(value) for value in by_stratum.values()),
        "interval_95": nearest_rank_interval(draws),
        "median": statistics.median(draws),
        "nonpositive_draws": sum(value <= 0.0 for value in draws),
    }


def score_benchmark(
    benchmark: Benchmark, mode: str, repetitions: int, seed: int
) -> tuple[dict[str, Any], list[dict[str, Any]], list[float]]:
    grouped: defaultdict[str, list[Operation]] = defaultdict(list)
    for operation in benchmark.operations:
        grouped[operation.query_id].append(operation)
    target_ids = [
        key for key in sorted(grouped) if sum(row.label for row in grouped[key]) > 0
    ]
    if mode == "preflight":
        target_ids = target_ids[:1]
    methods = sorted(next(iter(benchmark.operations)).scores)
    if mode == "preflight":
        methods = ["agentprof", "raw_action"]
    query_rows: list[dict[str, Any]] = []
    for key in target_ids:
        operations = grouped[key]
        labels = [row.label for row in operations]
        mapped_targets = sum(labels)
        official_targets = int(benchmark.official_targets[key])
        ap = {
            method: standard_ap(labels, [row.scores[method] for row in operations])
            for method in methods
        }
        sensitivity = {
            method: value * mapped_targets / official_targets
            for method, value in ap.items()
        }
        query_rows.append(
            {
                "benchmark": benchmark.name,
                "query_id": key,
                "stratum": operations[0].stratum,
                "cluster": operations[0].cluster,
                "operations": len(operations),
                "mapped_targets": mapped_targets,
                "official_targets": official_targets,
                "ap": ap,
                "unmapped_target_sensitivity_ap": sensitivity,
            }
        )

    map_scores = {
        method: statistics.fmean(row["ap"][method] for row in query_rows)
        for method in methods
    }
    sensitivity_map = {
        method: statistics.fmean(
            row["unmapped_target_sensitivity_ap"][method] for row in query_rows
        )
        for method in methods
    }
    pooled_ap: dict[str, float] = {}
    if mode == "full":
        labels = [row.label for row in benchmark.operations]
        pooled_ap = {
            method: standard_ap(
                labels, [row.scores[method] for row in benchmark.operations]
            )
            for method in methods
        }
        cluster_universe = None
        if benchmark.name == "AgentProcessBench":
            universe: defaultdict[str, set[str]] = defaultdict(set)
            for operation in benchmark.operations:
                universe[operation.stratum].add(operation.cluster)
            cluster_universe = {
                key: sorted(values) for key, values in universe.items()
            }
        draws, bootstrap = paired_bootstrap(
            query_rows, repetitions, seed, cluster_universe
        )
    else:
        draws = []
        bootstrap = None
    summary = {
        "benchmark": benchmark.name,
        "source_trajectories": benchmark.source_trajectories,
        "source_operations": len(benchmark.operations),
        "source_target_bearing_queries": sum(
            sum(row.label for row in values) > 0 for values in grouped.values()
        ),
        "scored_queries": len(query_rows),
        "mapped_targets": sum(row.label for row in benchmark.operations),
        "official_targets": sum(benchmark.official_targets.values()),
        "methods": methods,
        "map": map_scores,
        "unmapped_target_sensitivity_map": sensitivity_map,
        "pooled_operation_ap": pooled_ap,
        "agentprof_minus_raw_map": map_scores["agentprof"] - map_scores["raw_action"],
        "paired_bootstrap": bootstrap,
    }
    return summary, query_rows, draws


def verdict(summaries: Sequence[Mapping[str, Any]]) -> str:
    effects = [float(row["agentprof_minus_raw_map"]) for row in summaries]
    if all(value > 0.0 for value in effects):
        return "SUPPORTED"
    if sum(value < 0.0 for value in effects) >= 2:
        return "CONTRADICTED"
    return "MIXED_OR_INCONCLUSIVE"


def render_report(result: Mapping[str, Any]) -> str:
    lines = [
        f"# RQ2 Standard Localization Metrics — {result['mode'].title()}",
        "",
        f"- scikit-learn: `{result['scikit_learn']}`",
        f"- metric: trajectory-level non-interpolated MAP",
        f"- verdict: **{result['verdict']}**",
        "",
        "| Benchmark | Queries | AgentProf MAP | Raw MAP | Delta | 95% interval | Pooled AP |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for row in result["benchmarks"]:
        bootstrap = row["paired_bootstrap"]
        interval = "—" if bootstrap is None else "[{:.4f}, {:.4f}]".format(*bootstrap["interval_95"])
        pooled = row["pooled_operation_ap"].get("agentprof")
        lines.append(
            "| {benchmark} | {scored_queries} | {agent:.4f} | {raw:.4f} | {delta:+.4f} | {interval} | {pooled} |".format(
                benchmark=row["benchmark"],
                scored_queries=row["scored_queries"],
                agent=row["map"]["agentprof"],
                raw=row["map"]["raw_action"],
                delta=row["agentprof_minus_raw_map"],
                interval=interval,
                pooled="—" if pooled is None else f"{pooled:.4f}",
            )
        )
    lines.extend(
        [
            "",
            "MAP excludes zero-positive trajectories by definition; pooled operation AP retains their nonrelevant operations.",
            "HINTBench's unmapped-target sensitivity counts its three absent official targets as unretrieved.",
            "No model, profiler, tagger, localizer, score, cutoff, or benchmark was rerun or changed.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("preflight", "full"))
    parser.add_argument("--agentprocess-root", type=Path, default=DEFAULT_AGENTPROCESS)
    parser.add_argument("--hint-root", type=Path, default=DEFAULT_HINT)
    parser.add_argument("--trace-root", type=Path, default=DEFAULT_TRACE)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--bootstraps", type=int, default=10000)
    parser.add_argument("--seed", type=int, default=20260716)
    args = parser.parse_args()
    if args.bootstraps <= 0:
        raise ExperimentError("--bootstraps must be positive")
    out = args.out or DEFAULT_OUT / args.mode

    benchmarks = [
        load_agentprocess(args.agentprocess_root),
        load_hint(args.hint_root),
        load_trace(args.trace_root),
    ]
    for benchmark in benchmarks:
        expected = EXPECTED[benchmark.name]
        target_queries = len({row.query_id for row in benchmark.operations if row.label})
        observed = (
            benchmark.source_trajectories,
            len(benchmark.operations),
            target_queries,
        )
        if observed != expected:
            raise ExperimentError(
                f"{benchmark.name}: expected population {expected}, got {observed}"
            )

    summaries: list[dict[str, Any]] = []
    query_rows: list[dict[str, Any]] = []
    bootstrap_draws: dict[str, list[float]] = {}
    for benchmark in benchmarks:
        summary, rows, draws = score_benchmark(
            benchmark, args.mode, args.bootstraps, args.seed
        )
        summaries.append(summary)
        query_rows.extend(rows)
        if draws:
            bootstrap_draws[benchmark.name] = draws
    result = {
        "mode": args.mode,
        "metric": "sklearn.metrics.average_precision_score per target-bearing trajectory; arithmetic mean across trajectories",
        "scikit_learn": sklearn_version,
        "seed": args.seed,
        "benchmarks": summaries,
        "verdict": (
            verdict(summaries) if args.mode == "full" else "NOT_EVALUATED_PREFLIGHT"
        ),
    }
    write_json(out / "summary.json", result)
    write_jsonl(out / "per-query.jsonl", query_rows)
    if bootstrap_draws:
        write_json(out / "bootstrap-deltas.json", bootstrap_draws)
    (out / "report.md").write_text(render_report(result), encoding="utf-8")
    print(json.dumps({"status": "ok", "mode": args.mode, "out": str(out), "verdict": result["verdict"]}))


if __name__ == "__main__":
    main()
