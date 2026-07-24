#!/usr/bin/env python3
"""Evaluate current AgentProf paths as a tie-breaker for local diagnostics.

This script uses the complete retained RQ2 populations.  It constructs all
rank scores from source-only operation paths and fixed local diagnostic signals
before loading target labels, then reports standard per-query AP and workload
MAP.  The matched raw-action baseline retains the exact source-evidence suffix
used by the AgentProf candidate.
"""

from __future__ import annotations

import argparse
from collections import defaultdict
import json
import math
from pathlib import Path
import random
import statistics
import sys
import time
from typing import Any, Iterable, Mapping, Sequence

from sklearn import __version__ as sklearn_version
from sklearn.metrics import average_precision_score

import rq2_agent_segmentation_eval as segmentation


DEFAULT_AGENTPROCESS_ROOT = Path("docs/visexp/out/agentprocessbench-rq2/full")
DEFAULT_AGENTPROCESS_GROUPS = Path(
    ".agentsight/experiments/rq2-canonical-tags-v2-current/agentprocess/results"
)
DEFAULT_HINT_ROOT = Path(
    "docs/tmp/cycle-0003-20260713T121925-0700/01-experiment-gate/"
    "loop-001-rq2-hintbench/results/full"
)
DEFAULT_HINT_GROUPS = Path(
    ".agentsight/experiments/rq2-canonical-tags-v2-current/hint/results"
)
DEFAULT_TRACE_ROOT = Path(".agentsight/experiments/traceelephant-rq2-v1")
DEFAULT_TRACE_GROUPS = Path(
    ".agentsight/experiments/rq2-canonical-tags-v2-current/trace/results"
)
DEFAULT_OUT = Path(
    ".agentsight/experiments/rq2-current-agent-local-first-v1"
)

METHODS = (
    "local_agentprof",
    "local_raw_evidence",
    "local_only",
    "agentprof_only",
)
MAIN_BASELINES = ("local_only", "local_raw_evidence")
EXPECTED = {
    "AgentProcessBench": {
        "trajectories": 1000,
        "operations": 8509,
        "target_queries": 614,
        "clean_queries": 386,
    },
    "HINTBench": {
        "trajectories": 536,
        "operations": 12877,
        "target_queries": 400,
        "clean_queries": 136,
    },
    "TraceElephant": {
        "trajectories": 220,
        "operations": 5960,
        "target_queries": 220,
        "clean_queries": 0,
    },
}


class ExperimentError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ExperimentError(message)


def read_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def write_jsonl(path: Path, rows: Iterable[Mapping[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")


def unique_by_id(
    rows: Sequence[Mapping[str, Any]], source: str
) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for row in rows:
        operation_id = str(row["operation_id"])
        require(operation_id not in result, f"{source}: duplicate {operation_id}")
        result[operation_id] = dict(row)
    return result


def source_suffix(fixed_row: Mapping[str, Any]) -> tuple[str, ...]:
    groups = fixed_row["groups"]
    automatic = tuple(str(value) for value in groups["automatic_agent"])
    preserved = tuple(str(value) for value in groups["source_preserving_agent"])
    require(
        len(preserved) > len(automatic)
        and preserved[: len(automatic)] == automatic,
        f"{fixed_row['operation_id']}: source-preserving path is not an extension",
    )
    suffix = preserved[len(automatic) :]
    require(
        len(suffix) == 3,
        f"{fixed_row['operation_id']}: expected three source-evidence frames",
    )
    return suffix


def load_agentprocess_sources(root: Path) -> list[dict[str, Any]]:
    return [
        {
            "operation_id": str(row["operation_id"]),
            "query_id": str(row["trajectory_id"]),
            "stratum": str(row["family"]),
            "cluster": str(row["task_id"]),
            "local_signal": float(row["risk_units"]),
            "raw_identity": str(row["groups"]["raw_action"]),
        }
        for row in read_jsonl(root / "group-assignments.jsonl")
    ]


def load_hint_sources(root: Path) -> list[dict[str, Any]]:
    return [
        {
            "operation_id": str(row["operation_id"]),
            "query_id": str(row["record_key"]),
            "stratum": str(row["raw_fields"]["environment"]),
            "cluster": str(row["record_key"]),
            "local_signal": float(int(row["localizer_hit"])),
            "raw_identity": str(row["raw_fields"]["action"]),
            "display_id": int(row["display_id"]),
        }
        for row in read_jsonl(root / "operations" / "test-projection.jsonl")
    ]


def load_trace_sources(root: Path) -> list[dict[str, Any]]:
    projections = read_jsonl(root / "operations" / "projection.jsonl")
    raw_method = read_json(root / "profiles" / "method-index.json")["methods"]["raw"]
    leaves = [str(value) for value in raw_method["operation_leaves"]]
    require(len(projections) == len(leaves), "Trace raw path coverage mismatch")
    return [
        {
            "operation_id": str(row["operation_id"]),
            "query_id": str(row["trace_id"]),
            "stratum": str(row["cell"]),
            "cluster": str(row["trace_id"]),
            "local_signal": float(int(row["localizer_hit"])),
            "raw_identity": leaf,
            "step_id": int(row["step_id"]),
        }
        for row, leaf in zip(projections, leaves, strict=True)
    ]


def load_labels(
    benchmark_key: str,
    root: Path,
    sources: Mapping[str, Mapping[str, Any]],
) -> dict[str, int]:
    if benchmark_key == "agentprocess":
        labels = {
            str(row["operation_id"]): int(int(row["human_label"]) == -1)
            for row in read_jsonl(root / "labels.jsonl")
        }
    elif benchmark_key == "hint":
        targets: dict[str, set[int]] = {}
        for row in read_json(root / "sources" / "test.json"):
            query_id = f"test:{row['id']}"
            values: set[int] = set()
            for field in ("injected_risks", "risk_labels"):
                for annotation in row.get(field, []):
                    value = annotation.get("risk_origin_step")
                    if value is None:
                        value = annotation.get("step_id")
                    require(
                        isinstance(value, int) and not isinstance(value, bool),
                        f"{query_id}: invalid target",
                    )
                    values.add(value)
            targets[query_id] = values
        labels = {
            operation_id: int(
                int(row["display_id"]) in targets[str(row["query_id"])]
            )
            for operation_id, row in sources.items()
        }
    elif benchmark_key == "trace":
        targets = {
            str(row["trace_id"]): int(row["mistake_step"])
            for row in read_jsonl(root / "scorer" / "targets.jsonl")
        }
        labels = {
            operation_id: int(
                int(row["step_id"]) == targets[str(row["query_id"])]
            )
            for operation_id, row in sources.items()
        }
    else:
        raise ExperimentError(f"unknown benchmark {benchmark_key}")
    require(set(labels) == set(sources), f"{benchmark_key}: label coverage mismatch")
    return labels


def ordinal_scores(keys: Sequence[tuple[float, ...]]) -> list[int]:
    distinct = {key for key in keys}
    require(bool(distinct), "cannot rank an empty population")
    mapping = {key: index for index, key in enumerate(sorted(distinct))}
    return [mapping[key] for key in keys]


def validate_local_order(
    local: Sequence[float], ordinals: Sequence[int], method: str
) -> None:
    by_local: defaultdict[float, list[int]] = defaultdict(list)
    for value, ordinal in zip(local, ordinals, strict=True):
        by_local[value].append(ordinal)
    ordered = sorted(by_local)
    for lower, higher in zip(ordered, ordered[1:]):
        require(
            max(by_local[lower]) < min(by_local[higher]),
            f"{method}: secondary score changed strict local order",
        )


def construct_scores(
    benchmark_key: str,
    fixed_rows: Sequence[Mapping[str, Any]],
    source_rows: Sequence[Mapping[str, Any]],
) -> tuple[dict[str, dict[str, float]], dict[str, Any]]:
    fixed = unique_by_id(fixed_rows, f"{benchmark_key} fixed paths")
    sources = unique_by_id(source_rows, f"{benchmark_key} source operations")
    require(
        set(fixed) == set(sources),
        f"{benchmark_key}: fixed/source operation-ID join mismatch",
    )

    raw_fixed: list[dict[str, Any]] = []
    for operation_id in sorted(fixed):
        row = fixed[operation_id]
        suffix = source_suffix(row)
        task_family = str(row["task_family"]).strip().casefold()
        raw_path = (
            task_family,
            f"raw:{str(sources[operation_id]['raw_identity']).strip().casefold()}",
            *suffix,
        )
        raw_fixed.append(
            {
                "operation_id": operation_id,
                "groups": {"raw_source_evidence": list(raw_path)},
            }
        )

    signal_rows = [
        {
            "operation_id": operation_id,
            "local_signal": float(sources[operation_id]["local_signal"]),
        }
        for operation_id in sorted(sources)
    ]
    agentprof_group = segmentation.scores_for_method(
        benchmark_key,
        fixed_rows,
        signal_rows,
        "source_preserving_agent",
    )
    raw_group = segmentation.scores_for_method(
        benchmark_key,
        raw_fixed,
        signal_rows,
        "raw_source_evidence",
    )

    operation_ids = sorted(sources)
    local_values = [float(sources[value]["local_signal"]) for value in operation_ids]
    agent_values = [float(agentprof_group[value]) for value in operation_ids]
    raw_values = [float(raw_group[value]) for value in operation_ids]
    keys = {
        "local_agentprof": list(zip(local_values, agent_values, strict=True)),
        "local_raw_evidence": list(zip(local_values, raw_values, strict=True)),
        "local_only": [(value,) for value in local_values],
        "agentprof_only": [(value,) for value in agent_values],
    }
    ordinals = {method: ordinal_scores(keys[method]) for method in METHODS}
    validate_local_order(local_values, ordinals["local_agentprof"], "local_agentprof")
    validate_local_order(
        local_values, ordinals["local_raw_evidence"], "local_raw_evidence"
    )

    scores = {
        operation_id: {
            method: float(ordinals[method][index]) for method in METHODS
        }
        for index, operation_id in enumerate(operation_ids)
    }
    checks = {
        "operations": len(operation_ids),
        "operation_id_join": "PASS",
        "rank_constructor_target_columns": [],
        "strict_local_order": {
            "local_agentprof": "PASS",
            "local_raw_evidence": "PASS",
        },
        "equal_keys_remain_tied": "PASS",
        "distinct_rank_tiers": {
            method: len(set(ordinals[method])) for method in METHODS
        },
        "source_suffix_frames": 3,
    }
    return scores, checks


def standard_ap(labels: Sequence[int], scores: Sequence[float]) -> float:
    require(
        len(labels) == len(scores) and bool(labels) and sum(labels) > 0,
        "AP requires aligned nonempty inputs with a positive item",
    )
    require(all(math.isfinite(value) for value in scores), "non-finite AP score")
    return float(average_precision_score(labels, scores))


def nearest_interval(values: Sequence[float]) -> list[float]:
    ordered = sorted(float(value) for value in values)
    require(bool(ordered), "empty bootstrap")
    lower = math.ceil(0.025 * len(ordered)) - 1
    upper = math.ceil(0.975 * len(ordered)) - 1
    return [ordered[lower], ordered[upper]]


def paired_bootstrap(
    query_rows: Sequence[Mapping[str, Any]],
    baseline: str,
    repetitions: int,
    seed: int,
) -> tuple[dict[str, Any], list[float]]:
    by_stratum: defaultdict[str, defaultdict[str, list[float]]] = defaultdict(
        lambda: defaultdict(list)
    )
    for row in query_rows:
        delta = float(row["ap"]["local_agentprof"]) - float(row["ap"][baseline])
        by_stratum[str(row["stratum"])][str(row["cluster"])].append(delta)
    require(bool(by_stratum), "bootstrap received no query rows")
    rng = random.Random(seed)
    draws: list[float] = []
    for _ in range(repetitions):
        sampled: list[float] = []
        for clusters in by_stratum.values():
            keys = sorted(clusters)
            for _ in keys:
                sampled.extend(clusters[rng.choice(keys)])
        require(bool(sampled), "bootstrap sampled no queries")
        draws.append(statistics.fmean(sampled))
    return (
        {
            "baseline": baseline,
            "repetitions": repetitions,
            "seed": seed,
            "strata": len(by_stratum),
            "clusters": sum(len(value) for value in by_stratum.values()),
            "interval_95": nearest_interval(draws),
            "median": statistics.median(draws),
            "nonpositive_draws": sum(value <= 0.0 for value in draws),
        },
        draws,
    )


def score_benchmark(
    benchmark_key: str,
    benchmark_name: str,
    root: Path,
    groups_root: Path,
    source_rows: Sequence[Mapping[str, Any]],
    mode: str,
    bootstraps: int,
    seed: int,
) -> tuple[dict[str, Any], list[dict[str, Any]], dict[str, list[float]]]:
    fixed_rows = read_jsonl(groups_root / "fixed-groups.jsonl")
    scores, construction_checks = construct_scores(
        benchmark_key, fixed_rows, source_rows
    )
    sources = unique_by_id(source_rows, f"{benchmark_name} source operations")

    # Target labels are intentionally opened only after every rank vector exists.
    labels = load_labels(benchmark_key, root, sources)
    by_query: defaultdict[str, list[str]] = defaultdict(list)
    for operation_id, row in sources.items():
        by_query[str(row["query_id"])].append(operation_id)
    target_queries = [
        query_id
        for query_id in sorted(by_query)
        if sum(labels[value] for value in by_query[query_id]) > 0
    ]
    clean_queries = [
        query_id
        for query_id in sorted(by_query)
        if sum(labels[value] for value in by_query[query_id]) == 0
    ]
    expected = EXPECTED[benchmark_name]
    observed = {
        "trajectories": len(by_query),
        "operations": len(sources),
        "target_queries": len(target_queries),
        "clean_queries": len(clean_queries),
    }
    require(observed == expected, f"{benchmark_name}: population drift {observed}")

    selected = target_queries if mode == "full" else target_queries[:1]
    query_rows: list[dict[str, Any]] = []
    for query_id in selected:
        operation_ids = by_query[query_id]
        query_labels = [labels[value] for value in operation_ids]
        first = sources[operation_ids[0]]
        query_rows.append(
            {
                "benchmark": benchmark_name,
                "query_id": query_id,
                "stratum": str(first["stratum"]),
                "cluster": str(first["cluster"]),
                "operations": len(operation_ids),
                "targets": sum(query_labels),
                "ap": {
                    method: standard_ap(
                        query_labels,
                        [scores[value][method] for value in operation_ids],
                    )
                    for method in METHODS
                },
            }
        )
    map_scores = {
        method: statistics.fmean(float(row["ap"][method]) for row in query_rows)
        for method in METHODS
    }

    current_summary = read_json(groups_root / "summary.json")
    incumbent_expected = float(
        current_summary["map"]["source_preserving_agent"]
    )
    current_queries = {
        str(row["query_id"]): row
        for row in read_jsonl(groups_root / "per-query.jsonl")
    }
    incumbent_max_difference = max(
        abs(
            float(row["ap"]["agentprof_only"])
            - float(current_queries[str(row["query_id"])]["ap"]["source_preserving_agent"])
        )
        for row in query_rows
    )
    if mode == "full":
        require(
            math.isclose(
                map_scores["agentprof_only"],
                incumbent_expected,
                rel_tol=0.0,
                abs_tol=1e-12,
            ),
            f"{benchmark_name}: incumbent MAP reproduction failed",
        )
    require(
        incumbent_max_difference <= 1e-12,
        f"{benchmark_name}: incumbent per-query reproduction failed",
    )

    comparisons: dict[str, Any] = {}
    draws_by_name: dict[str, list[float]] = {}
    if mode == "full":
        for index, baseline in enumerate(MAIN_BASELINES):
            bootstrap, draws = paired_bootstrap(
                query_rows,
                baseline=baseline,
                repetitions=bootstraps,
                seed=seed + index,
            )
            comparisons[baseline] = {
                "point_effect": (
                    map_scores["local_agentprof"] - map_scores[baseline]
                ),
                **bootstrap,
            }
            draws_by_name[f"{benchmark_name}:{baseline}"] = draws

    summary = {
        "benchmark": benchmark_name,
        "mode": mode,
        **observed,
        "scored_target_queries": len(query_rows),
        "zero_positive_queries_loaded_but_excluded_from_map": len(clean_queries),
        "map": map_scores,
        "candidate_minus_component_ablation": (
            map_scores["local_agentprof"] - map_scores["agentprof_only"]
        ),
        "main_comparisons": comparisons,
        "construction_checks": construction_checks,
        "incumbent_reproduction": {
            "expected_full_map": incumbent_expected,
            "observed_map": map_scores["agentprof_only"],
            "max_per_query_absolute_difference": incumbent_max_difference,
            "full_map_exact_within_1e-12": (
                mode != "full"
                or math.isclose(
                    map_scores["agentprof_only"],
                    incumbent_expected,
                    rel_tol=0.0,
                    abs_tol=1e-12,
                )
            ),
        },
    }
    return summary, query_rows, draws_by_name


def render_report(result: Mapping[str, Any]) -> str:
    lines = [
        f"# RQ2 Current AgentProf Local-First Result — {str(result['mode']).title()}",
        "",
        f"- status: `{result['execution_status']}`",
        "- primary metric: standard per-query average precision and workload MAP",
        "- candidate: local diagnostic score + current Agent+Evidence tie refinement",
        "- main baselines: local only; local + information-matched raw action and source evidence",
        "- component ablation: current Agent+Evidence score alone",
        "- scope: adaptive mechanism evaluation on three previously observed complete populations",
        "",
        "| Workload | Local+AgentProf | Local+Raw+Evidence | Local only | AgentProf only |",
        "|---|---:|---:|---:|---:|",
    ]
    for row in result["benchmarks"]:
        values = row["map"]
        lines.append(
            "| {name} | {candidate:.4f} | {raw:.4f} | {local:.4f} | {component:.4f} |".format(
                name=row["benchmark"],
                candidate=values["local_agentprof"],
                raw=values["local_raw_evidence"],
                local=values["local_only"],
                component=values["agentprof_only"],
            )
        )
    if result["mode"] == "full":
        lines.extend(
            [
                "",
                "## Paired candidate-minus-baseline MAP differences",
                "",
                "| Workload | Baseline | Difference | 95% interval |",
                "|---|---|---:|---:|",
            ]
        )
        labels = {
            "local_only": "local only",
            "local_raw_evidence": "local + raw + evidence",
        }
        for row in result["benchmarks"]:
            for baseline in MAIN_BASELINES:
                comparison = row["main_comparisons"][baseline]
                lines.append(
                    "| {name} | {baseline} | {effect:+.4f} | [{low:+.4f}, {high:+.4f}] |".format(
                        name=row["benchmark"],
                        baseline=labels[baseline],
                        effect=comparison["point_effect"],
                        low=comparison["interval_95"][0],
                        high=comparison["interval_95"][1],
                    )
                )
    lines.extend(
        [
            "",
            "All score vectors are constructed before target labels are loaded.",
            "All zero-positive trajectories are consumed for coverage and excluded from MAP.",
            "AgentProf-only scores reproduce the current Step 0071 result.",
            "",
        ]
    )
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("preflight", "full"))
    parser.add_argument(
        "--agentprocess-root", type=Path, default=DEFAULT_AGENTPROCESS_ROOT
    )
    parser.add_argument(
        "--agentprocess-groups", type=Path, default=DEFAULT_AGENTPROCESS_GROUPS
    )
    parser.add_argument("--hint-root", type=Path, default=DEFAULT_HINT_ROOT)
    parser.add_argument("--hint-groups", type=Path, default=DEFAULT_HINT_GROUPS)
    parser.add_argument("--trace-root", type=Path, default=DEFAULT_TRACE_ROOT)
    parser.add_argument("--trace-groups", type=Path, default=DEFAULT_TRACE_GROUPS)
    parser.add_argument("--bootstraps", type=int, default=10000)
    parser.add_argument("--seed", type=int, default=20260723)
    parser.add_argument("--out", type=Path)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    require(args.bootstraps > 0, "--bootstraps must be positive")
    out = args.out or DEFAULT_OUT / args.mode
    started = time.monotonic()
    specifications = [
        (
            "agentprocess",
            "AgentProcessBench",
            args.agentprocess_root.resolve(),
            args.agentprocess_groups.resolve(),
            load_agentprocess_sources(args.agentprocess_root.resolve()),
        ),
        (
            "hint",
            "HINTBench",
            args.hint_root.resolve(),
            args.hint_groups.resolve(),
            load_hint_sources(args.hint_root.resolve()),
        ),
        (
            "trace",
            "TraceElephant",
            args.trace_root.resolve(),
            args.trace_groups.resolve(),
            load_trace_sources(args.trace_root.resolve()),
        ),
    ]

    summaries: list[dict[str, Any]] = []
    per_query: list[dict[str, Any]] = []
    all_draws: dict[str, list[float]] = {}
    for index, (key, name, root, groups, sources) in enumerate(specifications):
        summary, rows, draws = score_benchmark(
            benchmark_key=key,
            benchmark_name=name,
            root=root,
            groups_root=groups,
            source_rows=sources,
            mode=args.mode,
            bootstraps=args.bootstraps,
            seed=args.seed + 100 * index,
        )
        summaries.append(summary)
        per_query.extend(rows)
        all_draws.update(draws)

    if args.mode == "full":
        totals = {
            "trajectories": sum(row["trajectories"] for row in summaries),
            "operations": sum(row["operations"] for row in summaries),
            "target_queries": sum(row["target_queries"] for row in summaries),
            "clean_queries": sum(row["clean_queries"] for row in summaries),
            "scored_queries": len(per_query),
        }
        require(
            totals
            == {
                "trajectories": 1756,
                "operations": 27346,
                "target_queries": 1234,
                "clean_queries": 522,
                "scored_queries": 1234,
            },
            f"full population changed: {totals}",
        )
        require(
            len(all_draws) == 6
            and all(len(values) == args.bootstraps for values in all_draws.values()),
            "bootstrap matrix is incomplete",
        )
        execution_status = "VALID_COMPLETE_PENDING_INDEPENDENT_RESULT_REVIEW"
    else:
        totals = {
            "trajectories": sum(row["trajectories"] for row in summaries),
            "operations": sum(row["operations"] for row in summaries),
            "scored_queries": len(per_query),
        }
        execution_status = "REAL_PREFLIGHT_COMPLETE_NOT_A_PAPER_RESULT"

    result = {
        "mode": args.mode,
        "execution_status": execution_status,
        "tested_hypothesis": (
            "current fixed source-only AgentProf paths add ranking information "
            "to unchanged local diagnostic scores"
        ),
        "adaptive_scope": (
            "mechanism evaluation on three previously observed complete populations; "
            "not untouched generalization of one universal LLM backend"
        ),
        "methods": {
            "candidate": "local_agentprof",
            "main_baselines": list(MAIN_BASELINES),
            "component_ablation": "agentprof_only",
        },
        "metric": (
            "sklearn.metrics.average_precision_score per target-bearing query; "
            "arithmetic workload MAP"
        ),
        "metric_reference": "Robertson, A New Interpretation of Average Precision, SIGIR 2008",
        "runtime": {
            "python": sys.version.split()[0],
            "scikit_learn": sklearn_version,
            "elapsed_seconds": time.monotonic() - started,
        },
        "seed": args.seed,
        "bootstraps": args.bootstraps if args.mode == "full" else 0,
        "totals": totals,
        "benchmarks": summaries,
    }
    write_json(out / "summary.json", result)
    write_jsonl(out / "per-query.jsonl", per_query)
    if all_draws:
        write_json(out / "bootstrap-deltas.json", all_draws)
    (out / "report.md").write_text(render_report(result), encoding="utf-8")
    print(
        json.dumps(
            {
                "status": "ok",
                "mode": args.mode,
                "out": str(out),
                "execution_status": execution_status,
            }
        )
    )


if __name__ == "__main__":
    main()
