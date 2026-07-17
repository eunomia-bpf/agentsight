#!/usr/bin/env python3
"""Evaluate local-first semantic ranking on the retained RQ2 trajectories.

The experiment changes no signal, operation stack, benchmark, or annotation.
It ranks each operation by the lexicographic key (local score, semantic group
score), compares it with matched local/raw, local-only, and semantic-only
rankings, and reuses the Step 0036 AP, tie-aware Recall@20%, and cluster
bootstrap implementations.
"""

from __future__ import annotations

import argparse
from collections import defaultdict
import json
import math
from pathlib import Path
import statistics
import sys
from typing import Any, Iterable, Mapping, Sequence

import rq2_same_signal_diagnostic_decomposition as step36
import rq2_standard_localization_metrics as base


DEFAULT_AGENTPROCESS = Path("docs/visexp/out/agentprocessbench-rq2/full")
DEFAULT_HINT = Path(
    "docs/tmp/cycle-0003-20260713T121925-0700/01-experiment-gate/"
    "loop-001-rq2-hintbench/results/full"
)
DEFAULT_TRACE = Path(".agentsight/experiments/traceelephant-rq2-v1")
DEFAULT_STEP0036 = Path(
    ".agentsight/experiments/rq2-same-signal-diagnostic-decomposition-v1/full"
)
DEFAULT_OUT = Path(".agentsight/experiments/rq2-local-first-semantic-ranking-v1")

METHODS = ("local_semantic", "local_raw", "atomic", "semantic")
BASELINES = ("local_raw", "atomic", "semantic")
EXPECTED = {
    "AgentProcessBench": (1000, 8509, 614, 386),
    "HINTBench": (536, 12877, 400, 136),
    "TraceElephant": (220, 5960, 220, 0),
}
EXPECTED_BOOTSTRAP = {
    "AgentProcessBench": (4, 178),
    "HINTBench": (44, 400),
    "TraceElephant": (5, 220),
}


class ExperimentError(RuntimeError):
    pass


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: Iterable[Mapping[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")


def ordinal_mapping(keys: Sequence[tuple[float, ...]]) -> dict[tuple[float, ...], int]:
    """Map a total preorder to exact integer tiers without consulting labels."""
    distinct = sorted(set(keys))
    if not distinct:
        raise ExperimentError("cannot rank an empty operation population")
    return {key: index for index, key in enumerate(distinct)}


def validate_strict_local_order(
    keys: Sequence[tuple[float, ...]], ordinals: Sequence[int], method: str
) -> None:
    by_local: defaultdict[float, list[int]] = defaultdict(list)
    for key, ordinal in zip(keys, ordinals, strict=True):
        by_local[key[0]].append(ordinal)
    ordered_local = sorted(by_local)
    for lower, higher in zip(ordered_local, ordered_local[1:]):
        if max(by_local[lower]) >= min(by_local[higher]):
            raise ExperimentError(
                f"{method}: secondary key overwrote strict local-score order"
            )


def construct_rank_keys(
    score_rows: Sequence[Mapping[str, float]],
) -> tuple[list[dict[str, Any]], dict[str, list[dict[str, Any]]], dict[str, Any]]:
    """Construct all rank tiers from score columns only.

    This function intentionally cannot receive correctness labels, target IDs,
    or benchmark annotations.
    """
    components: list[dict[str, float]] = []
    for index, row in enumerate(score_rows):
        if set(row) != {"local", "semantic", "raw_action"}:
            raise ExperimentError(f"score row {index} has unexpected columns")
        components.append(
            {
                name: step36.canonical_score(float(row[name]), f"{name} score")
                for name in ("local", "semantic", "raw_action")
            }
        )

    keys_by_method: dict[str, list[tuple[float, ...]]] = {
        "local_semantic": [
            (row["local"], row["semantic"]) for row in components
        ],
        "local_raw": [(row["local"], row["raw_action"]) for row in components],
        "atomic": [(row["local"],) for row in components],
        "semantic": [(row["semantic"],) for row in components],
    }
    maps = {method: ordinal_mapping(keys) for method, keys in keys_by_method.items()}
    ordinals = {
        method: [maps[method][key] for key in keys]
        for method, keys in keys_by_method.items()
    }
    validate_strict_local_order(
        keys_by_method["local_semantic"], ordinals["local_semantic"], "local_semantic"
    )
    validate_strict_local_order(
        keys_by_method["local_raw"], ordinals["local_raw"], "local_raw"
    )

    for method, keys in keys_by_method.items():
        seen: dict[tuple[float, ...], int] = {}
        for key, ordinal in zip(keys, ordinals[method], strict=True):
            previous = seen.setdefault(key, ordinal)
            if previous != ordinal:
                raise ExperimentError(f"{method}: equal keys do not remain tied")

    rows: list[dict[str, Any]] = []
    for index, component in enumerate(components):
        rows.append(
            {
                "components": component,
                "keys": {
                    method: list(keys_by_method[method][index]) for method in METHODS
                },
                "ordinals": {method: ordinals[method][index] for method in METHODS},
            }
        )
    serial_maps = {
        method: [
            {"key": list(key), "ordinal": ordinal}
            for key, ordinal in sorted(mapping.items(), key=lambda item: item[1])
        ]
        for method, mapping in maps.items()
    }
    checks = {
        "input_rows": len(rows),
        "score_columns": ["local", "semantic", "raw_action"],
        "target_columns_accepted": False,
        "strict_local_order": {"local_semantic": "PASS", "local_raw": "PASS"},
        "equal_keys_remain_tied": "PASS",
        "distinct_tiers": {method: len(maps[method]) for method in METHODS},
    }
    return rows, serial_maps, checks


def load_step0036(
    root: Path,
) -> tuple[dict[tuple[str, str], dict[str, Any]], dict[str, dict[str, Any]]]:
    rows = base.read_jsonl(root / "per-query.jsonl")
    indexed: dict[tuple[str, str], dict[str, Any]] = {}
    for row in rows:
        key = (str(row["benchmark"]), str(row["query_id"]))
        if key in indexed:
            raise ExperimentError(f"duplicate Step 0036 query row: {key}")
        indexed[key] = row
    summary = base.read_json(root / "summary.json")
    summaries = {str(row["benchmark"]): row for row in summary["benchmarks"]}
    if len(rows) != 1234 or set(summaries) != set(EXPECTED):
        raise ExperimentError("Step 0036 reproduction root is incomplete")
    return indexed, summaries


def prepare_benchmark(
    benchmark: base.Benchmark,
) -> tuple[
    dict[str, list[dict[str, Any]]],
    dict[str, list[dict[str, Any]]],
    dict[str, Any],
]:
    score_rows = [
        {
            "local": float(operation.scores["atomic"]),
            "semantic": float(operation.scores["agentprof"]),
            "raw_action": float(operation.scores["raw_action"]),
        }
        for operation in benchmark.operations
    ]
    rank_rows, mappings, construction_checks = construct_rank_keys(score_rows)

    grouped: defaultdict[str, list[dict[str, Any]]] = defaultdict(list)
    query_indices: defaultdict[str, int] = defaultdict(int)
    for source_index, (operation, rank_row) in enumerate(
        zip(benchmark.operations, rank_rows, strict=True)
    ):
        query_index = query_indices[operation.query_id]
        query_indices[operation.query_id] += 1
        grouped[operation.query_id].append(
            {
                "benchmark": benchmark.name,
                "query_id": operation.query_id,
                "stratum": operation.stratum,
                "cluster": operation.cluster,
                "source_operation_index": source_index,
                "query_operation_index": query_index,
                "label": int(operation.label),
                **rank_row,
            }
        )
    mapping_record = {
        "benchmark": benchmark.name,
        "methods": mappings,
    }
    return dict(grouped), mapping_record, construction_checks


def close(left: float, right: float, tolerance: float = 1e-15) -> bool:
    return math.isclose(float(left), float(right), rel_tol=0.0, abs_tol=tolerance)


def verify_step0036_query(
    row: Mapping[str, Any], expected: Mapping[str, Any]
) -> dict[str, float]:
    differences = {
        "atomic_ap": abs(float(row["ap"]["atomic"]) - float(expected["ap"]["atomic"])),
        "semantic_ap": abs(
            float(row["ap"]["semantic"]) - float(expected["ap"]["agentprof"])
        ),
        "atomic_recall20": abs(
            float(row["recall20"]["atomic"])
            - float(expected["recall20"]["atomic"])
        ),
        "semantic_recall20": abs(
            float(row["recall20"]["semantic"])
            - float(expected["recall20"]["agentprof"])
        ),
    }
    if any(not close(value, 0.0) for value in differences.values()):
        raise ExperimentError(
            f"{row['benchmark']} {row['query_id']}: Step 0036 baseline mismatch "
            f"{differences}"
        )
    return differences


def support_summary(
    benchmark_name: str,
    clean_rows: Sequence[Sequence[Mapping[str, Any]]],
    agentprocess_scale: int | None,
    expected_step36: Mapping[str, Any],
) -> dict[str, Any] | None:
    if not clean_rows:
        return None
    if benchmark_name == "AgentProcessBench":
        if agentprocess_scale is None:
            raise ExperimentError("AgentProcessBench support scale is missing")
        threshold = 0.5 * agentprocess_scale
        predicate = lambda value: float(value) > threshold
        label = "local harmful-vote fraction > 0.5"
    elif benchmark_name == "HINTBench":
        threshold = 0.0
        predicate = lambda value: step36.canonical_score(
            float(value), "HINT local support"
        ) > 0.0
        label = "canonicalized local score > 0"
    else:
        raise ExperimentError(f"unexpected clean workload {benchmark_name}")

    per_query: list[dict[str, Any]] = []
    supported_operations = 0
    supported_trajectories = 0
    total_operations = 0
    for operations in clean_rows:
        flags = [predicate(row["components"]["local"]) for row in operations]
        candidate_flags = list(flags)
        atomic_flags = list(flags)
        if candidate_flags != atomic_flags:
            raise ExperimentError("candidate support does not equal atomic support")
        any_support = any(flags)
        supported_operations += sum(flags)
        supported_trajectories += int(any_support)
        total_operations += len(flags)
        per_query.append(
            {
                "query_id": str(operations[0]["query_id"]),
                "operations": len(flags),
                "supported_operations": sum(flags),
                "any_support": any_support,
            }
        )

    expected_rows = {
        str(row["query_id"]): row
        for row in expected_step36["clean_support_propagation"]["methods"]["atomic"][
            "per_query"
        ]
    }
    for row in per_query:
        expected = expected_rows.get(str(row["query_id"]))
        if expected is None:
            raise ExperimentError(f"missing Step 0036 clean row {row['query_id']}")
        for field in ("operations", "supported_operations", "any_support"):
            if row[field] != expected[field]:
                raise ExperimentError(
                    f"{benchmark_name} {row['query_id']}: atomic support mismatch"
                )

    return {
        "classification": "algorithm_property_not_performance_metric",
        "threshold": threshold,
        "threshold_label": label,
        "identity_check": "PASS",
        "candidate_equals_atomic_per_operation": True,
        "clean_trajectories": len(clean_rows),
        "clean_operations": total_operations,
        "any_support_trajectories": supported_trajectories,
        "supported_clean_operations": supported_operations,
        "clean_trajectory_support_rate": supported_trajectories / len(clean_rows),
        "clean_operation_support_rate": supported_operations / total_operations,
        "per_query": per_query,
    }


def mechanism_engagement(
    selected_rows: Sequence[Sequence[Mapping[str, Any]]],
) -> dict[str, int]:
    local_tiers = 0
    semantic_split_tiers = 0
    raw_split_tiers = 0
    semantic_affected = 0
    raw_affected = 0
    semantic_engaged_queries = 0
    raw_engaged_queries = 0
    for operations in selected_rows:
        by_local: defaultdict[float, list[Mapping[str, Any]]] = defaultdict(list)
        for row in operations:
            by_local[float(row["components"]["local"])].append(row)
        local_tiers += len(by_local)
        query_semantic = False
        query_raw = False
        for tier in by_local.values():
            if len({float(row["components"]["semantic"]) for row in tier}) > 1:
                semantic_split_tiers += 1
                semantic_affected += len(tier)
                query_semantic = True
            if len({float(row["components"]["raw_action"]) for row in tier}) > 1:
                raw_split_tiers += 1
                raw_affected += len(tier)
                query_raw = True
        semantic_engaged_queries += int(query_semantic)
        raw_engaged_queries += int(query_raw)
    return {
        "queries": len(selected_rows),
        "local_score_tiers": local_tiers,
        "semantic_split_local_tiers": semantic_split_tiers,
        "semantic_affected_operations": semantic_affected,
        "semantic_engaged_queries": semantic_engaged_queries,
        "raw_split_local_tiers": raw_split_tiers,
        "raw_affected_operations": raw_affected,
        "raw_engaged_queries": raw_engaged_queries,
    }


def classify_workload(comparisons: Mapping[str, Mapping[str, Any]]) -> str:
    values = list(comparisons.values())
    if all(
        float(row["point_effect"]) > 0.0
        and float(row["interval_95"][0]) > 0.0
        for row in values
    ):
        return "SUPPORTED"
    if any(float(row["interval_95"][1]) < 0.0 for row in values):
        return "CONTRADICTED"
    return "INCONCLUSIVE"


def score_benchmark(
    benchmark: base.Benchmark,
    mode: str,
    repetitions: int,
    base_seed: int,
    benchmark_index: int,
    step0036_rows: Mapping[tuple[str, str], Mapping[str, Any]],
    step0036_summary: Mapping[str, Any],
    agentprocess_scale: int | None,
) -> tuple[
    dict[str, Any],
    list[dict[str, Any]],
    list[dict[str, Any]],
    dict[str, Any],
    dict[str, list[float]],
]:
    grouped, mapping_record, construction_checks = prepare_benchmark(benchmark)
    target_ids = [
        query_id
        for query_id in sorted(grouped)
        if sum(row["label"] for row in grouped[query_id]) > 0
    ]
    clean_ids = [
        query_id
        for query_id in sorted(grouped)
        if sum(row["label"] for row in grouped[query_id]) == 0
    ]
    observed = (
        benchmark.source_trajectories,
        len(benchmark.operations),
        len(target_ids),
        len(clean_ids),
    )
    if observed != EXPECTED[benchmark.name]:
        raise ExperimentError(
            f"{benchmark.name}: expected {EXPECTED[benchmark.name]}, got {observed}"
        )

    selected_targets = target_ids if mode == "full" else target_ids[:1]
    selected_clean = clean_ids if mode == "full" else clean_ids[:1]
    selected_ids = sorted(set(selected_targets) | set(selected_clean))
    selected_groups = [grouped[query_id] for query_id in selected_ids]
    selected_clean_groups = [grouped[query_id] for query_id in selected_clean]

    query_rows: list[dict[str, Any]] = []
    reproduction_max: defaultdict[str, float] = defaultdict(float)
    for query_id in selected_targets:
        operations = grouped[query_id]
        labels = [int(row["label"]) for row in operations]
        scores = {
            method: [float(row["ordinals"][method]) for row in operations]
            for method in METHODS
        }
        ap = {method: base.standard_ap(labels, scores[method]) for method in METHODS}
        recall_details = {
            method: step36.tie_averaged_recall_at_fraction(labels, scores[method])
            for method in METHODS
        }
        mapped_targets = sum(labels)
        official_targets = int(benchmark.official_targets[query_id])
        if mapped_targets > official_targets:
            raise ExperimentError(f"{benchmark.name} {query_id}: too many mapped targets")
        coverage = mapped_targets / official_targets
        row = {
            "benchmark": benchmark.name,
            "query_id": query_id,
            "stratum": str(operations[0]["stratum"]),
            "cluster": str(operations[0]["cluster"]),
            "operations": len(operations),
            "mapped_targets": mapped_targets,
            "official_targets": official_targets,
            "target_mapping_coverage": coverage,
            "ap": ap,
            "recall20": {
                method: float(recall_details[method]["expected_recall"])
                for method in METHODS
            },
            "recall20_detail": recall_details,
            "unmapped_target_sensitivity": {
                "ap": {method: ap[method] * coverage for method in METHODS},
                "recall20": {
                    method: float(recall_details[method]["expected_recall"]) * coverage
                    for method in METHODS
                },
            },
        }
        expected = step0036_rows.get((benchmark.name, query_id))
        if expected is None:
            raise ExperimentError(f"missing Step 0036 query {benchmark.name} {query_id}")
        differences = verify_step0036_query(row, expected)
        for name, value in differences.items():
            reproduction_max[name] = max(reproduction_max[name], value)
        query_rows.append(row)

    map_scores = {
        method: statistics.fmean(float(row["ap"][method]) for row in query_rows)
        for method in METHODS
    }
    recall_scores = {
        method: statistics.fmean(float(row["recall20"][method]) for row in query_rows)
        for method in METHODS
    }
    sensitivity_map = {
        method: statistics.fmean(
            float(row["unmapped_target_sensitivity"]["ap"][method])
            for row in query_rows
        )
        for method in METHODS
    }
    sensitivity_recall = {
        method: statistics.fmean(
            float(row["unmapped_target_sensitivity"]["recall20"][method])
            for row in query_rows
        )
        for method in METHODS
    }

    if mode == "full":
        for ours, previous in (("atomic", "atomic"), ("semantic", "agentprof")):
            if not close(map_scores[ours], float(step0036_summary["map"][previous])):
                raise ExperimentError(f"{benchmark.name}: full MAP reproduction failed")
            if not close(
                recall_scores[ours],
                float(step0036_summary["macro_tie_averaged_recall20"][previous]),
            ):
                raise ExperimentError(f"{benchmark.name}: full recall reproduction failed")

    bootstrap_summaries: dict[str, Any] = {}
    bootstrap_draws: dict[str, list[float]] = {}
    if mode == "full":
        internal_rows: list[dict[str, Any]] = []
        for row in query_rows:
            internal_rows.append(
                {
                    "stratum": row["stratum"],
                    "cluster": row["cluster"],
                    "ap": {
                        "agentprof": row["ap"]["local_semantic"],
                        **{baseline: row["ap"][baseline] for baseline in BASELINES},
                    },
                    "recall20": {
                        "agentprof": row["recall20"]["local_semantic"],
                        **{
                            baseline: row["recall20"][baseline]
                            for baseline in BASELINES
                        },
                    },
                }
            )
        for metric_index, metric in enumerate(("ap", "recall20")):
            for baseline_index, baseline in enumerate(BASELINES):
                seed = (
                    base_seed
                    + 100 * benchmark_index
                    + 10 * metric_index
                    + baseline_index
                )
                result, draws = step36.paired_cluster_bootstrap(
                    internal_rows, metric, baseline, repetitions, seed
                )
                expected_strata, expected_clusters = EXPECTED_BOOTSTRAP[benchmark.name]
                if (int(result["strata"]), int(result["clusters"])) != (
                    expected_strata,
                    expected_clusters,
                ):
                    raise ExperimentError(
                        f"{benchmark.name}: bootstrap universe changed for {metric}/{baseline}"
                    )
                result["candidate"] = "local_semantic"
                key = f"{metric}:local_semantic_minus_{baseline}"
                bootstrap_summaries[key] = result
                bootstrap_draws[key] = draws

    primary_comparisons: dict[str, Any] = {}
    secondary_comparisons: dict[str, Any] = {}
    if mode == "full":
        for baseline in BASELINES:
            ap_key = f"ap:local_semantic_minus_{baseline}"
            recall_key = f"recall20:local_semantic_minus_{baseline}"
            primary_comparisons[baseline] = {
                "point_effect": map_scores["local_semantic"] - map_scores[baseline],
                "interval_95": bootstrap_summaries[ap_key]["interval_95"],
                "seed": bootstrap_summaries[ap_key]["seed"],
            }
            secondary_comparisons[baseline] = {
                "point_effect": recall_scores["local_semantic"]
                - recall_scores[baseline],
                "interval_95": bootstrap_summaries[recall_key]["interval_95"],
                "seed": bootstrap_summaries[recall_key]["seed"],
                "fixed_budget_dominance_forbidden": float(
                    bootstrap_summaries[recall_key]["interval_95"][1]
                )
                < 0.0,
            }
        classification = classify_workload(primary_comparisons)
    else:
        classification = "NOT_EVALUATED_PREFLIGHT"

    support = support_summary(
        benchmark.name,
        selected_clean_groups,
        agentprocess_scale,
        step0036_summary,
    )
    engagement = mechanism_engagement(selected_groups)

    rank_key_rows: list[dict[str, Any]] = []
    for operations in selected_groups:
        for row in operations:
            rank_key_rows.append(
                {
                    "benchmark": row["benchmark"],
                    "query_id": row["query_id"],
                    "stratum": row["stratum"],
                    "cluster": row["cluster"],
                    "source_operation_index": row["source_operation_index"],
                    "query_operation_index": row["query_operation_index"],
                    "components": row["components"],
                    "keys": row["keys"],
                    "ordinals": row["ordinals"],
                }
            )

    summary = {
        "benchmark": benchmark.name,
        "source_trajectories": benchmark.source_trajectories,
        "source_operations": len(benchmark.operations),
        "source_target_queries": len(target_ids),
        "source_clean_queries": len(clean_ids),
        "scored_target_queries": len(selected_targets),
        "scored_clean_queries": len(selected_clean),
        "rank_key_rows": len(rank_key_rows),
        "map": map_scores,
        "macro_tie_averaged_recall20": recall_scores,
        "target_mapping": {
            "mapped_targets": sum(int(row["mapped_targets"]) for row in query_rows),
            "official_targets": sum(int(row["official_targets"]) for row in query_rows),
            "unmapped_targets": sum(
                int(row["official_targets"]) - int(row["mapped_targets"])
                for row in query_rows
            ),
            "unmapped_as_unrecovered_sensitivity_map": sensitivity_map,
            "unmapped_as_unrecovered_sensitivity_recall20": sensitivity_recall,
        },
        "rank_key_construction": construction_checks,
        "mechanism_engagement": engagement,
        "clean_support_identity": support,
        "step0036_reproduction": {
            "status": "PASS",
            "compared_methods": {"atomic": "atomic", "semantic": "agentprof"},
            "maximum_absolute_difference": dict(reproduction_max),
        },
        "paired_bootstrap": bootstrap_summaries,
        "primary_map_comparisons": primary_comparisons,
        "secondary_recall20_comparisons": secondary_comparisons,
        "primary_classification": classification,
    }
    return summary, query_rows, rank_key_rows, mapping_record, bootstrap_draws


def render_report(result: Mapping[str, Any]) -> str:
    lines = [
        f"# RQ2 Local-First Semantic Ranking — {str(result['mode']).title()}",
        "",
        f"- execution status: `{result['execution_status']}`",
        f"- primary verdict: **{result['primary_verdict']}**",
        "- primary metric: standard trajectory MAP",
        "- secondary metric: exact-K tie-averaged expected Recall@20%",
        "- scope: post-hoc adaptive development on the three previously observed complete populations; not untouched generalization",
        "",
        "| Benchmark | Ranking | MAP | Expected Recall@20% |",
        "|---|---|---:|---:|",
    ]
    labels = {
        "local_semantic": "local + semantic tie refinement",
        "local_raw": "local + raw-action tie refinement",
        "atomic": "local only",
        "semantic": "semantic only",
    }
    for benchmark in result["benchmarks"]:
        for method in METHODS:
            lines.append(
                "| {benchmark} | {method} | {map_value:.4f} | {recall:.4f} |".format(
                    benchmark=benchmark["benchmark"],
                    method=labels[method],
                    map_value=benchmark["map"][method],
                    recall=benchmark["macro_tie_averaged_recall20"][method],
                )
            )
    if result["mode"] == "full":
        lines.extend(
            [
                "",
                "## Paired primary MAP comparisons",
                "",
                "| Benchmark | Candidate minus | Point effect | 95% interval | Workload result |",
                "|---|---|---:|---:|---|",
            ]
        )
        for benchmark in result["benchmarks"]:
            for baseline in BASELINES:
                comparison = benchmark["primary_map_comparisons"][baseline]
                lines.append(
                    "| {benchmark} | {baseline} | {point:+.4f} | [{low:+.4f}, {high:+.4f}] | {result} |".format(
                        benchmark=benchmark["benchmark"],
                        baseline=labels[baseline],
                        point=comparison["point_effect"],
                        low=comparison["interval_95"][0],
                        high=comparison["interval_95"][1],
                        result=benchmark["primary_classification"],
                    )
                )
    lines.extend(
        [
            "",
            "Atomic and incumbent semantic rows must reproduce Step 0036; the raw artifacts record the maximum absolute difference.",
            "Candidate support is defined by the unchanged local predicate and must equal atomic support on every clean operation.",
            "No model, benchmark, target, operation stack, group, score column, cutoff, or paper-level claim was changed.",
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
    parser.add_argument("--step0036-root", type=Path, default=DEFAULT_STEP0036)
    parser.add_argument("--bootstraps", type=int, default=10000)
    parser.add_argument("--seed", type=int, default=20260717)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    if args.bootstraps <= 0:
        raise ExperimentError("--bootstraps must be positive")
    out = args.out or DEFAULT_OUT / args.mode
    out.mkdir(parents=True, exist_ok=True)

    step0036_rows, step0036_summaries = load_step0036(args.step0036_root)
    benchmarks = [
        base.load_agentprocess(args.agentprocess_root),
        base.load_hint(args.hint_root),
        base.load_trace(args.trace_root),
    ]
    risk_scale = step36.agentprocess_risk_scale(args.agentprocess_root)

    summaries: list[dict[str, Any]] = []
    per_query: list[dict[str, Any]] = []
    rank_keys: list[dict[str, Any]] = []
    mappings: list[dict[str, Any]] = []
    all_draws: dict[str, list[float]] = {}
    for benchmark_index, benchmark in enumerate(benchmarks):
        summary, rows, keys, mapping, draws = score_benchmark(
            benchmark=benchmark,
            mode=args.mode,
            repetitions=args.bootstraps,
            base_seed=args.seed,
            benchmark_index=benchmark_index,
            step0036_rows=step0036_rows,
            step0036_summary=step0036_summaries[benchmark.name],
            agentprocess_scale=(
                risk_scale if benchmark.name == "AgentProcessBench" else None
            ),
        )
        summaries.append(summary)
        per_query.extend(rows)
        rank_keys.extend(keys)
        mappings.append(mapping)
        for key, values in draws.items():
            all_draws[f"{benchmark.name}:{key}"] = values

    if args.mode == "full":
        totals = (
            sum(int(row["source_trajectories"]) for row in summaries),
            sum(int(row["source_operations"]) for row in summaries),
            sum(int(row["scored_target_queries"]) for row in summaries),
            sum(int(row["scored_clean_queries"]) for row in summaries),
            len(rank_keys),
        )
        if totals != (1756, 27346, 1234, 522, 27346):
            raise ExperimentError(f"full population changed: {totals}")
        if len(all_draws) != 18 or any(
            len(values) != args.bootstraps for values in all_draws.values()
        ):
            raise ExperimentError("full bootstrap matrix is incomplete")
        workload_verdicts = [str(row["primary_classification"]) for row in summaries]
        if all(value == "SUPPORTED" for value in workload_verdicts):
            primary_verdict = "SUPPORTED"
        elif any(value == "CONTRADICTED" for value in workload_verdicts):
            primary_verdict = "CONTRADICTED"
        else:
            primary_verdict = "INCONCLUSIVE"
        execution_status = "VALID_COMPLETE_PENDING_INDEPENDENT_RESULT_REVIEW"
    else:
        primary_verdict = "NOT_EVALUATED_PREFLIGHT"
        execution_status = "REAL_PREFLIGHT_COMPLETE_NOT_A_PAPER_RESULT"

    result = {
        "mode": args.mode,
        "execution_status": execution_status,
        "primary_verdict": primary_verdict,
        "adaptive_scope": (
            "post-hoc method development on three previously observed complete populations; "
            "conditional descriptive inference, not untouched generalization"
        ),
        "tested_hypothesis": (
            "preserve strict local diagnostic ordering and use semantic recurrence only "
            "to refine exact local-score ties"
        ),
        "runtime": {
            "python": sys.version.split()[0],
            "scikit_learn": base.sklearn_version,
        },
        "input_roots": {
            "AgentProcessBench": str(args.agentprocess_root.resolve()),
            "HINTBench": str(args.hint_root.resolve()),
            "TraceElephant": str(args.trace_root.resolve()),
            "Step0036": str(args.step0036_root.resolve()),
        },
        "metrics": {
            "primary": "sklearn non-interpolated AP per target-bearing trajectory; arithmetic workload MAP",
            "secondary": "exact-K analytic tie-averaged expected Recall@20%",
            "clean_support": "algorithm property check, not a performance metric",
        },
        "seed_formula": (
            "seed + 100*benchmark_index + 10*metric_index + baseline_index; "
            "benchmark=APB,HINT,Trace; metric=MAP,Recall20; "
            "baseline=local_raw,atomic,semantic"
        ),
        "base_seed": args.seed,
        "bootstraps_per_array": args.bootstraps if args.mode == "full" else 0,
        "benchmarks": summaries,
    }
    write_json(out / "summary.json", result)
    write_jsonl(out / "per-query.jsonl", per_query)
    write_jsonl(out / "rank-keys.jsonl", rank_keys)
    write_json(out / "rank-key-mappings.json", mappings)
    if all_draws:
        write_json(out / "bootstrap-deltas.json", all_draws)
    (out / "report.md").write_text(render_report(result), encoding="utf-8")
    print(
        json.dumps(
            {
                "status": "ok",
                "mode": args.mode,
                "out": str(out),
                "primary_verdict": primary_verdict,
            }
        )
    )


if __name__ == "__main__":
    main()
