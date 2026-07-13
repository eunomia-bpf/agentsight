#!/usr/bin/env python3
"""Run the approved finite-evidence AgentProcessBench RQ2 construction.

Visible fields, released judge outputs, and real AgentProf assignments are
materialized before the separate human-label loader is called. Human labels
score the fixed construction; they never define its fields, groups, or scores.
"""

from __future__ import annotations

from collections import Counter
import argparse
import gzip
import importlib.util
import json
import math
import multiprocessing as mp
import os
from pathlib import Path
import sys
from typing import Any

import numpy as np


BASE_PATH = Path(__file__).with_name("agentprocessbench_profile_eval.py")
BASE_SPEC = importlib.util.spec_from_file_location(
    "agentprocessbench_profile_eval_base", BASE_PATH
)
if BASE_SPEC is None or BASE_SPEC.loader is None:
    raise RuntimeError(f"cannot load base experiment module: {BASE_PATH}")
base = importlib.util.module_from_spec(BASE_SPEC)
BASE_SPEC.loader.exec_module(base)

ExperimentError = base.ExperimentError
FAMILIES = base.FAMILIES
ALL_VIEWS = base.ALL_VIEWS
Z_975 = 1.959963984540054


def wilson_lower_score(harmful_votes: float, available_votes: float) -> float:
    """Return the fixed Wilson-shaped lower score, with no-evidence at zero."""
    if available_votes < 0 or harmful_votes < 0 or harmful_votes > available_votes:
        raise ExperimentError("invalid harmful/available vote totals")
    if available_votes == 0:
        return 0.0
    proportion = harmful_votes / available_votes
    z2 = Z_975 * Z_975
    numerator = (
        proportion
        + z2 / (2.0 * available_votes)
        - Z_975
        * math.sqrt(
            proportion * (1.0 - proportion) / available_votes
            + z2 / (4.0 * available_votes * available_votes)
        )
    )
    return numerator / (1.0 + z2 / available_votes)


def wilson_score_array(
    harmful_votes: np.ndarray, available_votes: np.ndarray
) -> np.ndarray:
    """Vectorized score used by point estimates, shuffles, and bootstraps."""
    harmful = harmful_votes.astype(np.float64, copy=False)
    available = available_votes.astype(np.float64, copy=False)
    if np.any(available < 0) or np.any(harmful < 0) or np.any(harmful > available):
        raise ExperimentError("invalid harmful/available vote arrays")
    scores = np.zeros_like(available, dtype=np.float64)
    observed = available > 0
    if not np.any(observed):
        return scores
    n = available[observed]
    proportion = harmful[observed] / n
    z2 = Z_975 * Z_975
    scores[observed] = (
        proportion
        + z2 / (2.0 * n)
        - Z_975
        * np.sqrt(proportion * (1.0 - proportion) / n + z2 / (4.0 * n * n))
    ) / (1.0 + z2 / n)
    return scores


def _assignment_index(
    assignments: list[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    indexed = {str(row["operation_id"]): row for row in assignments}
    if len(indexed) != len(assignments):
        raise ExperimentError("duplicate operation in AgentProf assignments")
    return indexed


def materialize_group_scores(
    rows: list[dict[str, Any]],
    risks: dict[str, dict[str, int | float]],
    assignments: list[dict[str, Any]],
    out: Path,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    """Write family-local group and operation scores before labels are loaded."""
    by_id = _assignment_index(assignments)
    row_ids = [str(row["operation_id"]) for row in rows]
    if set(row_ids) != set(by_id) or set(row_ids) != set(risks):
        raise ExperimentError("rows, risks, and AgentProf assignments differ")

    grouped: dict[tuple[str, str, str], Counter[str]] = {}
    global_operations = 0
    global_available = 0
    global_harmful = 0
    for row in rows:
        operation_id = str(row["operation_id"])
        family = str(row["family"])
        risk = risks[operation_id]
        available = int(risk["available_predictions"])
        harmful = int(risk["negative_predictions"])
        slots = int(risk["prediction_slots"])
        if slots != base.EXPECTED_MODELS:
            raise ExperimentError(f"{operation_id}: unexpected prediction slots")
        if available < 0 or available > slots or harmful < 0 or harmful > available:
            raise ExperimentError(f"{operation_id}: invalid released vote counts")
        global_operations += 1
        global_available += available
        global_harmful += harmful
        assignment = by_id[operation_id]
        if str(assignment["family"]) != family:
            raise ExperimentError(f"{operation_id}: assignment family mismatch")
        for view in ALL_VIEWS:
            stack_key = str(assignment["groups"][view])
            identity = (family, view, stack_key)
            totals = grouped.setdefault(identity, Counter())
            totals["operations"] += 1
            totals["available_votes"] += available
            totals["harmful_votes"] += harmful

    group_rows: list[dict[str, Any]] = []
    score_by_identity: dict[tuple[str, str, str], float] = {}
    zero_vote_groups: list[dict[str, str]] = []
    for (family, view, stack_key), totals in sorted(grouped.items()):
        score = wilson_lower_score(
            float(totals["harmful_votes"]), float(totals["available_votes"])
        )
        identity = (family, view, stack_key)
        score_by_identity[identity] = score
        record = {
            "family": family,
            "view": view,
            "stack_key": stack_key,
            "operations": int(totals["operations"]),
            "available_votes": int(totals["available_votes"]),
            "harmful_votes": int(totals["harmful_votes"]),
            "score": score,
        }
        group_rows.append(record)
        if totals["available_votes"] == 0:
            zero_vote_groups.append(
                {"family": family, "view": view, "stack_key": stack_key}
            )

    operation_rows: list[dict[str, Any]] = []
    for row in rows:
        operation_id = str(row["operation_id"])
        family = str(row["family"])
        assignment = by_id[operation_id]
        operation_rows.append(
            {
                "operation_id": operation_id,
                "family": family,
                "scores": {
                    view: score_by_identity[
                        (family, view, str(assignment["groups"][view]))
                    ]
                    for view in ALL_VIEWS
                },
            }
        )

    per_view: dict[str, dict[str, Any]] = {}
    for view in ALL_VIEWS:
        selected = [record for record in group_rows if record["view"] == view]
        by_family = {
            family: [record for record in selected if record["family"] == family]
            for family in FAMILIES
        }
        if any(not records for records in by_family.values()):
            raise ExperimentError(f"{view}: missing a family-local score group")
        operations = sum(int(record["operations"]) for record in selected)
        available = sum(int(record["available_votes"]) for record in selected)
        harmful = sum(int(record["harmful_votes"]) for record in selected)
        if (
            operations != global_operations
            or available != global_available
            or harmful != global_harmful
        ):
            raise ExperimentError(f"{view}: released-vote accounting failed")
        per_view[view] = {
            "groups": len(selected),
            "families": len(by_family),
            "operations": operations,
            "available_votes": available,
            "harmful_votes": harmful,
            "family_local_exact": True,
            "vote_accounting_exact": True,
        }

    base.write_jsonl(out / "wilson-group-scores.jsonl", group_rows)
    base.write_jsonl(out / "wilson-operation-scores.jsonl", operation_rows)
    audit = {
        "formula": "wilson_shaped_lower_score",
        "z": Z_975,
        "zero_vote_score": 0.0,
        "group_identity": "family_plus_agentprof_stack_key",
        "materialized_before_human_labels": True,
        "operations": global_operations,
        "available_votes": global_available,
        "harmful_votes": global_harmful,
        "zero_vote_groups": zero_vote_groups,
        "views": per_view,
    }
    base.write_json(out / "wilson-score-report.json", audit)
    return group_rows, operation_rows, audit


def build_states(
    rows: list[dict[str, Any]],
    labels: dict[str, int],
    risks: dict[str, dict[str, int | float]],
    assignments: list[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    states = base.build_states(rows, labels, risks, assignments)
    for state in states.values():
        operation_ids = state["operation_ids"]
        state["available_votes"] = np.asarray(
            [int(risks[operation_id]["available_predictions"]) for operation_id in operation_ids],
            dtype=np.int64,
        )
        state["harmful_votes"] = np.asarray(
            [int(risks[operation_id]["negative_predictions"]) for operation_id in operation_ids],
            dtype=np.int64,
        )
    return states


def metric_for_view(
    state: dict[str, Any], method: str, weights: np.ndarray
) -> dict[str, float | int]:
    group = state["groups"][method]
    group_count = len(state["group_labels"][method])
    counts = np.bincount(group, weights=weights, minlength=group_count)
    harmful_votes = np.bincount(
        group,
        weights=weights * state["harmful_votes"],
        minlength=group_count,
    )
    available_votes = np.bincount(
        group,
        weights=weights * state["available_votes"],
        minlength=group_count,
    )
    positives = np.bincount(
        group, weights=weights * state["labels"], minlength=group_count
    )
    scores = wilson_score_array(harmful_votes, available_votes)
    result = base.metric_from_group_arrays(scores, counts, positives)
    result.update(
        {
            "available_votes": float(available_votes.sum()),
            "harmful_votes": float(harmful_votes.sum()),
            "zero_vote_groups": int(np.sum((counts > 0) & (available_votes == 0))),
        }
    )
    return result


def base_results(states: dict[str, dict[str, Any]]) -> dict[str, Any]:
    per_family: dict[str, dict[str, Any]] = {}
    mean_risk_per_family: dict[str, dict[str, Any]] = {}
    for family, state in states.items():
        weights = np.ones(len(state["rows"]), dtype=np.float64)
        per_family[family] = {
            method: metric_for_view(state, method, weights) for method in ALL_VIEWS
        }
        mean_risk_per_family[family] = {
            method: base.metric_for_view(state, method, weights)
            for method in ("raw_action", "semantic")
        }

    macro = {
        method: {
            metric: float(
                np.mean([per_family[family][method][metric] for family in FAMILIES])
            )
            for metric in ("average_precision", "recall_at_30", "work_to_50")
        }
        for method in ALL_VIEWS
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
    mean_risk_macro = {
        method: {
            metric: float(
                np.mean(
                    [mean_risk_per_family[family][method][metric] for family in FAMILIES]
                )
            )
            for metric in ("average_precision", "recall_at_30", "work_to_50")
        }
        for method in ("raw_action", "semantic")
    }
    return {
        "per_family": per_family,
        "macro": macro,
        "effects": effects,
        "mean_risk_regression": {
            "per_family": mean_risk_per_family,
            "macro": mean_risk_macro,
            "effects": {
                "semantic_minus_raw_ap": (
                    mean_risk_macro["semantic"]["average_precision"]
                    - mean_risk_macro["raw_action"]["average_precision"]
                ),
                "raw_minus_semantic_work50": (
                    mean_risk_macro["raw_action"]["work_to_50"]
                    - mean_risk_macro["semantic"]["work_to_50"]
                ),
            },
        },
    }


def run_shuffles(
    states: dict[str, dict[str, Any]],
    results: dict[str, Any],
    permutations: int,
    seed: int,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    if permutations != 200:
        raise ExperimentError("approved experiment requires exactly 200 shuffles")
    rows: list[dict[str, Any]] = []
    observed_ap = float(results["effects"]["semantic_minus_raw_ap"])
    observed_work = float(results["effects"]["raw_minus_semantic_work50"])
    for permutation in range(permutations):
        family_metrics: dict[str, dict[str, float | int]] = {}
        exact = True
        for family_index, family in enumerate(FAMILIES):
            state = states[family]
            keys, family_exact = base.shuffled_semantic_keys(
                state, seed, permutation, family_index
            )
            exact = exact and family_exact
            group, labels = base.group_index(keys)
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
                    macro_ap - results["macro"]["raw_action"]["average_precision"]
                ),
                "raw_minus_shuffle_work50": (
                    results["macro"]["raw_action"]["work_to_50"] - macro_work
                ),
                "size_preservation_exact": True,
                "family_local": True,
            }
        )
    exceed = sum(row["delta_ap_vs_raw"] >= observed_ap for row in rows)
    work_values = [float(row["raw_minus_shuffle_work50"]) for row in rows]
    return rows, {
        "permutations": permutations,
        "observed_delta_ap": observed_ap,
        "observed_raw_minus_semantic_work50": observed_work,
        "shuffle_delta_ap_min": min(row["delta_ap_vs_raw"] for row in rows),
        "shuffle_delta_ap_median": float(
            np.median([row["delta_ap_vs_raw"] for row in rows])
        ),
        "shuffle_delta_ap_max": max(row["delta_ap_vs_raw"] for row in rows),
        "shuffle_work_effect_min": min(work_values),
        "shuffle_work_effect_median": float(np.median(work_values)),
        "shuffle_work_effect_max": max(work_values),
        "greater_or_equal": exceed,
        "p_shuffle_ap": (1 + exceed) / (permutations + 1),
        "size_preservation_exact": all(row["size_preservation_exact"] for row in rows),
        "family_local": True,
    }


_BOOT_STATES: dict[str, dict[str, Any]] | None = None
_BOOT_SEED = 0


def _bootstrap_attempt(attempt: int) -> dict[str, Any] | None:
    if _BOOT_STATES is None:
        raise RuntimeError("bootstrap states are not initialized")
    rng = np.random.default_rng(np.random.SeedSequence([_BOOT_SEED, attempt]))
    per_family: dict[str, dict[str, dict[str, float | int]]] = {}
    for family in FAMILIES:
        state = _BOOT_STATES[family]
        task_count = len(state["task_ids"])
        draw = rng.integers(0, task_count, size=task_count)
        multiplicity = np.bincount(draw, minlength=task_count)
        weights = multiplicity[state["task_index"]].astype(np.float64)
        if float(np.sum(weights * state["labels"])) <= 0:
            return None
        per_family[family] = {
            method: metric_for_view(state, method, weights) for method in ALL_VIEWS
        }
    macro = {
        method: {
            metric: float(
                np.mean([per_family[family][method][metric] for family in FAMILIES])
            )
            for metric in ("average_precision", "recall_at_30", "work_to_50")
        }
        for method in ALL_VIEWS
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
    pool: Any = None
    try:
        if workers > 1:
            pool = mp.get_context("fork").Pool(processes=workers)
        for start in range(0, max_attempts, 256):
            attempts = list(range(start, min(start + 256, max_attempts)))
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
    return valid, {
        "requested": requested,
        "valid": len(valid),
        "examined": examined,
        "discarded": examined - len(valid),
        "max_attempts": max_attempts,
        "seed": seed,
        "workers": workers,
        "intervals": intervals,
        "complete": len(valid) == requested,
        "family_local_score_recomputation": True,
    }


def scientific_verdict(
    mode: str, bootstrap: dict[str, Any], shuffle: dict[str, Any]
) -> str:
    if not bootstrap["complete"]:
        return "INCOMPLETE"
    if mode != "full":
        return "PREFLIGHT_ONLY"
    ap_interval = bootstrap["intervals"]["semantic_minus_raw_ap"]
    work_interval = bootstrap["intervals"]["raw_minus_semantic_work50"]
    if (
        ap_interval[0] > 0
        and work_interval[0] > 0
        and shuffle["p_shuffle_ap"] <= 0.05
    ):
        return "SUPPORTED"
    if ap_interval[1] < 0 or work_interval[1] < 0:
        return "CONTRADICTED"
    return "INCONCLUSIVE"


def markdown_report(summary: dict[str, Any]) -> str:
    lines = [
        f"# AgentProcessBench Wilson {summary['mode'].upper()} report",
        "",
        f"**Execution:** {summary['execution_status']}",
        f"**Scientific verdict:** {summary['scientific_verdict']}",
        f"**Source commit:** `{summary['source']['source_commit']}`",
        f"**AgentProf:** `{summary['profiles']['agentprof_version']}`",
        "",
        "## Complete input",
        "",
        f"- families: {len(summary['source']['selected']['operations_by_family'])}",
        f"- trajectories: {summary['source']['selected']['trajectories']:,}",
        f"- operations: {summary['source']['selected']['operations']:,}",
        f"- released judges: {summary['risk']['models']}",
        f"- zero-vote score groups: {len(summary['scores']['zero_vote_groups'])}",
        "- group identity: `(family, AgentProf stack key)`",
        "- human labels loaded after all point scores: yes",
        "",
        "## Family results",
        "",
        "| Family | View | AP | Recall@30 | Work-to-50 | Groups |",
        "|---|---|---:|---:|---:|---:|",
    ]
    for family in FAMILIES:
        for method in ("raw_action", "semantic"):
            value = summary["results"]["per_family"][family][method]
            lines.append(
                f"| {family} | {method} | {value['average_precision']:.6f} | "
                f"{value['recall_at_30']:.6f} | {value['work_to_50']:.6f} | "
                f"{value['groups']} |"
            )
    intervals = summary["bootstrap"]["intervals"]
    lines.extend(
        [
            "",
            "## Macro decision quantities",
            "",
            f"- semantic minus raw AP: {summary['results']['effects']['semantic_minus_raw_ap']:.9f}",
            f"- AP interval: {intervals['semantic_minus_raw_ap']}",
            f"- raw minus semantic work-to-50: {summary['results']['effects']['raw_minus_semantic_work50']:.9f}",
            f"- work interval: {intervals['raw_minus_semantic_work50']}",
            f"- matched-shuffle AP p: {summary['shuffle']['p_shuffle_ap']:.9f}",
            "",
            "## Completion",
            "",
            f"- bootstrap: {summary['bootstrap']['valid']:,} valid / {summary['bootstrap']['examined']:,} examined",
            f"- matched shuffles: {summary['shuffle']['permutations']}",
            f"- family-local vote accounting: {all(v['family_local_exact'] for v in summary['scores']['views'].values())}",
            "- group scores are Wilson-shaped finite-ensemble scores, not calibrated human-harm confidence bounds",
            "- this is supporting adaptive within-benchmark construction evidence, not a fresh holdout",
            "",
        ]
    )
    return "\n".join(lines)


def validate_cli(args: argparse.Namespace) -> None:
    base.validate_cli_contract(args)
    if args.workers <= 0:
        raise ExperimentError("workers must be positive")


def run(args: argparse.Namespace) -> dict[str, Any]:
    validate_cli(args)
    source = Path(args.source).resolve()
    binary = Path(args.agentpprof_bin).resolve()
    out = Path(args.out).resolve()
    out.mkdir(parents=True, exist_ok=True)

    rows, full_ids, source_audit = base.load_source(source, args.query_limit)
    selected_ids = {row["operation_id"] for row in rows}
    risks, risk_audit = base.load_external_risks(source, full_ids, selected_ids)
    if set(risks) != selected_ids:
        raise ExperimentError("selected operation/risk sets differ")

    assignments, profile_report = base.construct_profiles(rows, risks, binary, out)
    _, _, score_audit = materialize_group_scores(rows, risks, assignments, out)

    labels, label_audit = base.load_human_labels(source, full_ids, selected_ids)
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

    base.write_jsonl(
        out / "labels.jsonl",
        (
            {"operation_id": row["operation_id"], "human_label": labels[row["operation_id"]]}
            for row in rows
        ),
    )
    base.write_jsonl(out / "shuffle-effects.jsonl", shuffle_rows)
    with gzip.open(out / "bootstrap-effects.jsonl.gz", "wt", encoding="utf-8") as output:
        output.write(
            json.dumps(
                {
                    "type": "header",
                    "requested": args.bootstraps,
                    "max_attempts": args.max_bootstrap_attempts,
                    "seed": args.seed,
                    "score": "wilson_shaped_family_local",
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
        "paper_value_role": "supporting_adaptive_within_benchmark_construction",
        "source": source_audit,
        "labels": label_audit,
        "risk": risk_audit,
        "profiles": profile_report,
        "scores": score_audit,
        "results": results,
        "shuffle": shuffle_summary,
        "bootstrap": bootstrap_summary,
        "run_parameters": {
            "query_limit": args.query_limit,
            "permutations": args.permutations,
            "bootstraps": args.bootstraps,
            "max_bootstrap_attempts": args.max_bootstrap_attempts,
            "seed": args.seed,
        },
    }
    base.write_json(out / "summary.json", summary)
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
            "--workers", type=int, default=max(1, min(8, os.cpu_count() or 1))
        )
        if mode == "preflight":
            command.add_argument("--query-limit", type=int, required=True)
        else:
            command.set_defaults(query_limit=None)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    summary = run(args)
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if summary["execution_status"] == "VALID" else 2


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ExperimentError as error:
        print(f"experiment error: {error}", file=sys.stderr)
        raise SystemExit(2) from error
