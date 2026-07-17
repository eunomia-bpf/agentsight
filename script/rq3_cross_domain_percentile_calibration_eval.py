#!/usr/bin/env python3
"""Transfer one recurrence cutoff across existing trajectory domains.

The experiment does not change AgentProf's action-transition NPMI score.  It
fits a grouped-source cutoff on the score's occurrence-weighted empirical-CDF
scale, then applies that percentile unchanged in the other domain.  OSWorld and
CodeTraceBench exchange source/target roles in two information-separated
directions.  Target group identities and boundaries reach scoring only after
each direction's predictions have been persisted.  The fixed OSWorld
eligibility loader necessarily parses label-bearing rows, but returns only the
visible action sequences used by the predictor.
"""

from __future__ import annotations

import argparse
import bisect
import json
import math
import random
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable

import numpy as np
import pyarrow.parquet as pq

from operation_boundary_backend_eval import DEFAULT_OPERATION_FILE
from rq3_codetracebench_stage_fidelity_eval import load_visible_operations
from rq3_recurrence_stack_induction_eval import (
    EXPECTED as OSWORLD_EXPECTED,
    FOLD_COUNT,
    deterministic_two_means,
    fold_for,
    predict_fold,
    transition_npmi,
)
from rq3_reference_calibrated_existing_traces_eval import (
    CODETRACE_EXPECTED,
    DEFAULT_CODETRACE_BASELINE,
    DEFAULT_CODETRACE_MANIFEST,
    DEFAULT_CODETRACE_REFERENCE,
    DEFAULT_CODETRACE_TARGET,
    DEFAULT_OSWORLD_BASELINE,
    EXPECTED_ACTIONS,
    assignments_from_predictions,
    boundary_metrics,
    fit_cutoff,
    load_stage_map,
    osworld_oracle,
    osworld_source,
    partition_metrics,
)


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_UPPER_BOUND = (
    ROOT
    / ".agentsight/experiments/rq3-reference-calibrated-existing-traces-v1/full/summary.json"
)
BOOTSTRAP_DRAWS = 10_000
BOOTSTRAP_SEED = 20_260_716
METHODS = ("candidate", "raw_transfer", "label_free")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("preflight", "full"), required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--osworld-operations", type=Path, default=DEFAULT_OPERATION_FILE)
    parser.add_argument(
        "--codetrace-reference", type=Path, default=DEFAULT_CODETRACE_REFERENCE
    )
    parser.add_argument("--codetrace-target", type=Path, default=DEFAULT_CODETRACE_TARGET)
    parser.add_argument(
        "--codetrace-manifest", type=Path, default=DEFAULT_CODETRACE_MANIFEST
    )
    return parser.parse_args()


def absolute(path: Path) -> Path:
    return path if path.is_absolute() else ROOT / path


def relative(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return str(path.resolve())


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as output:
        for row in rows:
            output.write(json.dumps(row, sort_keys=True) + "\n")


def empirical_cdf_association(
    association: dict[tuple[str, str], float], occurrence_scores: list[float]
) -> tuple[dict[tuple[str, str], float], dict[str, Any]]:
    require(bool(occurrence_scores), "empirical CDF requires transition occurrences")
    ordered = sorted(float(score) for score in occurrence_scores)
    require(all(math.isfinite(score) for score in ordered), "non-finite CDF score")
    percentiles = {
        pair: bisect.bisect_right(ordered, float(score)) / len(ordered)
        for pair, score in association.items()
    }
    require(
        all(0.0 <= value <= 1.0 and math.isfinite(value) for value in percentiles.values()),
        "invalid empirical percentile",
    )
    score_to_percentile = sorted(
        {(float(association[pair]), value) for pair, value in percentiles.items()}
    )
    require(
        all(left[1] <= right[1] for left, right in zip(score_to_percentile, score_to_percentile[1:])),
        "empirical CDF is not monotone",
    )
    return percentiles, {
        "occurrences": len(ordered),
        "distinct_occurrence_scores": len(set(ordered)),
        "scored_action_pairs": len(association),
        "min_score": ordered[0],
        "max_score": ordered[-1],
        "min_pair_percentile": min(percentiles.values()),
        "max_pair_percentile": max(percentiles.values()),
        "definition": "right-continuous occurrence-weighted empirical CDF",
    }


def predict_transfer(
    sessions: list[str],
    visible: dict[str, list[str]],
    association: dict[tuple[str, str], float],
    occurrence_scores: list[float],
    percentile_cutoff: float,
    raw_cutoff: float,
) -> tuple[
    dict[tuple[str, int], dict[str, Any]],
    dict[tuple[str, int], dict[str, Any]],
    dict[str, Any],
]:
    percentile_association, cdf_report = empirical_cdf_association(
        association, occurrence_scores
    )
    candidate: dict[tuple[str, int], dict[str, Any]] = {}
    raw: dict[tuple[str, int], dict[str, Any]] = {}
    for session in sessions:
        for position, (left, right) in enumerate(
            zip(visible[session], visible[session][1:]), 1
        ):
            key = (session, position)
            score = association.get((left, right))
            percentile = percentile_association.get((left, right))
            require(key not in candidate and key not in raw, f"duplicate pair: {key}")
            candidate[key] = {
                "boundary": percentile is None or percentile < percentile_cutoff,
                "npmi": score,
                "percentile": percentile,
                "cutoff": percentile_cutoff,
                "unseen_in_target_reference": percentile is None,
            }
            raw[key] = {
                "boundary": score is None or score < raw_cutoff,
                "npmi": score,
                "cutoff": raw_cutoff,
                "unseen_in_target_reference": score is None,
            }
    return candidate, raw, cdf_report


def predict_label_free(
    sessions: list[str],
    visible: dict[str, list[str]],
    association: dict[tuple[str, str], float],
    occurrence_scores: list[float],
    reference_sessions: list[str],
    reference_visible: dict[str, list[str]],
) -> tuple[dict[tuple[str, int], dict[str, Any]], dict[str, Any]]:
    global_clusters = deterministic_two_means(occurrence_scores)
    cross_action_scores = [
        association[(left, right)]
        for session in reference_sessions
        for left, right in zip(
            reference_visible[session], reference_visible[session][1:]
        )
        if left != right
    ]
    cross_action_clusters = deterministic_two_means(cross_action_scores)
    effective_cross_action_cutoff = min(
        float(global_clusters["cutoff"]), float(cross_action_clusters["cutoff"])
    )
    predictions: dict[tuple[str, int], dict[str, Any]] = {}
    for session in sessions:
        for position, (left, right) in enumerate(
            zip(visible[session], visible[session][1:]), 1
        ):
            score = association.get((left, right))
            applied = (
                float(global_clusters["cutoff"])
                if left == right
                else effective_cross_action_cutoff
            )
            predictions[(session, position)] = {
                "boundary": score is None or score < applied,
                "npmi": score,
                "cutoff": applied,
                "unseen_in_target_reference": score is None,
            }
    return predictions, {
        "global": global_clusters,
        "cross_action": cross_action_clusters,
        "effective_cross_action_cutoff": effective_cross_action_cutoff,
    }


def method_assignments(
    sessions: list[str],
    visible: dict[str, list[str]],
    predictions: dict[str, dict[tuple[str, int], dict[str, Any]]],
) -> dict[str, dict[tuple[str, int], str]]:
    return {
        method: assignments_from_predictions(
            sessions, visible, predictions[method], "boundary"
        )
        for method in METHODS
    }


def all_metrics(
    operation_rows: list[dict[str, Any]], pair_rows: list[dict[str, Any]]
) -> dict[str, Any]:
    return {
        method: {
            "partition": partition_metrics(operation_rows, method),
            "boundary": boundary_metrics(pair_rows, method),
        }
        for method in METHODS
    }


def prepare_codetrace(
    reference_path: Path, target_path: Path, manifest_path: Path
) -> dict[str, Any]:
    references = load_visible_operations(reference_path)
    targets = load_visible_operations(target_path)
    require(
        len(references) == CODETRACE_EXPECTED["reference_sessions"],
        "CodeTrace reference session count changed",
    )
    require(
        sum(map(len, references.values())) == CODETRACE_EXPECTED["reference_operations"],
        "CodeTrace reference operation count changed",
    )
    require(
        len(targets) == CODETRACE_EXPECTED["target_sessions"],
        "CodeTrace target session count changed",
    )
    require(
        sum(map(len, targets.values())) == CODETRACE_EXPECTED["target_operations"],
        "CodeTrace target operation count changed",
    )
    target_ids = set(targets)
    score_reference = sorted(set(references) - target_ids)
    require(
        len(score_reference) == CODETRACE_EXPECTED["score_reference_sessions"],
        "CodeTrace score-reference session count changed",
    )
    require(
        sum(len(references[session]) for session in score_reference)
        == CODETRACE_EXPECTED["score_reference_operations"],
        "CodeTrace score-reference operation count changed",
    )
    reference_visible = {
        session: [str(row["action"]) for row in references[session]]
        for session in score_reference
    }
    target_visible = {
        session: [str(row["action"]) for row in targets[session]]
        for session in sorted(targets)
    }
    require(
        {
            action
            for session in score_reference
            for action in reference_visible[session]
        }
        == EXPECTED_ACTIONS,
        "CodeTrace action kinds changed",
    )
    identities = pq.read_table(
        manifest_path, columns=["traj_id", "agent", "solved", "step_count"]
    ).to_pylist()
    by_id = {str(row["traj_id"]): row for row in identities}
    calibration = sorted(
        session
        for session in score_reference
        if session in by_id
        and by_id[session]["solved"] is True
        and int(by_id[session]["step_count"]) == len(references[session])
    )
    require(
        len(calibration) == CODETRACE_EXPECTED["calibration_sessions"],
        "CodeTrace calibration session count changed",
    )
    require(
        sum(len(references[session]) for session in calibration)
        == CODETRACE_EXPECTED["calibration_operations"],
        "CodeTrace calibration operation count changed",
    )
    association, occurrence_scores, association_report = transition_npmi(
        score_reference, reference_visible
    )
    return {
        "references": references,
        "targets": targets,
        "score_reference": score_reference,
        "calibration": calibration,
        "reference_visible": reference_visible,
        "target_visible": target_visible,
        "association": association,
        "occurrence_scores": occurrence_scores,
        "association_report": association_report,
    }


def fit_codetrace_source(
    prepared: dict[str, Any], manifest_path: Path, out_dir: Path
) -> dict[str, Any]:
    oracle, frameworks, stages = load_stage_map(
        manifest_path,
        prepared["calibration"],
        prepared["references"],
        True,
        out_dir / "source-calibration-stages.json",
    )
    require(stages == CODETRACE_EXPECTED["calibration_stages"], "source stages")
    percentile_association, cdf = empirical_cdf_association(
        prepared["association"], prepared["occurrence_scores"]
    )
    percentile_cutoff, percentile_fit = fit_cutoff(
        prepared["calibration"],
        prepared["reference_visible"],
        percentile_association,
        oracle,
    )
    raw_cutoff, raw_fit = fit_cutoff(
        prepared["calibration"],
        prepared["reference_visible"],
        prepared["association"],
        oracle,
    )
    return {
        "source": "CodeTraceBench solved trajectories",
        "association": prepared["association_report"],
        "cdf": cdf,
        "percentile_cutoff": percentile_cutoff,
        "percentile_fit": percentile_fit,
        "raw_cutoff": raw_cutoff,
        "raw_fit": raw_fit,
        "calibration_stages": stages,
        "calibration_frameworks": dict(Counter(frameworks.values())),
    }


def predict_osworld_before_oracle(
    mode: str,
    visible: dict[str, list[str]],
    sessions: list[str],
    source_fit: dict[str, Any],
    out_dir: Path,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    selected_by_fold: dict[int, list[str]] = {}
    if mode == "preflight":
        fold_zero = sorted(session for session in sessions if fold_for(session) == 0)
        require(bool(fold_zero), "OSWorld preflight fold is empty")
        selected_by_fold[0] = fold_zero[:1]
    else:
        selected_by_fold = {
            fold: sorted(session for session in sessions if fold_for(session) == fold)
            for fold in range(FOLD_COUNT)
        }

    unscored: list[dict[str, Any]] = []
    fold_state: dict[int, dict[str, Any]] = {}
    for fold, selected in sorted(selected_by_fold.items()):
        train = [session for session in sessions if fold_for(session) != fold]
        association, occurrence_scores, association_report = transition_npmi(
            train, visible
        )
        candidate, raw, cdf = predict_transfer(
            selected,
            visible,
            association,
            occurrence_scores,
            float(source_fit["percentile_cutoff"]),
            float(source_fit["raw_cutoff"]),
        )
        current_all, current_report = predict_fold(fold, sessions, visible)
        expected = {
            (session, position)
            for session in selected
            for position in range(1, len(visible[session]))
        }
        label_free = {key: current_all[key] for key in expected}
        require(
            set(candidate) == set(raw) == set(label_free) == expected,
            f"OSWorld fold {fold} prediction key mismatch",
        )
        for key in sorted(expected):
            session, position = key
            unscored.append(
                {
                    "session": session,
                    "fold": fold,
                    "position": position,
                    "left_action": visible[session][position - 1],
                    "right_action": visible[session][position],
                    "npmi": candidate[key]["npmi"],
                    "percentile": candidate[key]["percentile"],
                    "candidate": bool(candidate[key]["boundary"]),
                    "raw_transfer": bool(raw[key]["boundary"]),
                    "label_free": bool(label_free[key]["boundary"]),
                }
            )
        fold_state[fold] = {
            "selected": selected,
            "association": association_report,
            "cdf": cdf,
            "current": current_report,
            "predictions": {
                "candidate": candidate,
                "raw_transfer": raw,
                "label_free": label_free,
            },
        }
    prediction_path = out_dir / "unscored-predictions.jsonl"
    write_jsonl(prediction_path, unscored)
    require(prediction_path.is_file(), "OSWorld predictions were not persisted")
    return fold_state, unscored


def score_osworld_after_prediction(
    source_path: Path,
    visible: dict[str, list[str]],
    fold_state: dict[int, dict[str, Any]],
    out_dir: Path,
) -> dict[str, Any]:
    selected = [
        session
        for fold in sorted(fold_state)
        for session in fold_state[fold]["selected"]
    ]
    oracle = osworld_oracle(source_path, selected, visible)
    operation_rows: list[dict[str, Any]] = []
    pair_rows: list[dict[str, Any]] = []
    folds: list[dict[str, Any]] = []
    for fold, state in sorted(fold_state.items()):
        fold_sessions = state["selected"]
        assignments = method_assignments(
            fold_sessions, visible, state["predictions"]
        )
        for session in fold_sessions:
            for index, action in enumerate(visible[session]):
                operation_rows.append(
                    {
                        "session": session,
                        "stratum": f"fold-{fold}",
                        "fold": fold,
                        "operation_index": index,
                        "action": action,
                        "oracle_group": oracle[(session, index)],
                        **{
                            method: assignments[method][(session, index)]
                            for method in METHODS
                        },
                    }
                )
            for position in range(1, len(visible[session])):
                key = (session, position)
                pair_rows.append(
                    {
                        "session": session,
                        "stratum": f"fold-{fold}",
                        "fold": fold,
                        "position": position,
                        "candidate": bool(
                            state["predictions"]["candidate"][key]["boundary"]
                        ),
                        "raw_transfer": bool(
                            state["predictions"]["raw_transfer"][key]["boundary"]
                        ),
                        "label_free": bool(
                            state["predictions"]["label_free"][key]["boundary"]
                        ),
                        "oracle_boundary": oracle[(session, position - 1)]
                        != oracle[(session, position)],
                    }
                )
        folds.append(
            {
                "fold": fold,
                "target_sessions": len(fold_sessions),
                "association": state["association"],
                "target_cdf": state["cdf"],
                "label_free_calibration": state["current"],
            }
        )
    write_jsonl(out_dir / "operation-assignments.jsonl", operation_rows)
    write_jsonl(out_dir / "pair-decisions.jsonl", pair_rows)
    metrics = all_metrics(operation_rows, pair_rows)
    return {
        "population": {
            "sessions": len(selected),
            "operations": len(operation_rows),
            "pairs": len(pair_rows),
            "oracle_groups": metrics["candidate"]["partition"]["oracle_groups"],
        },
        "folds": folds,
        "metrics": metrics,
        "operation_rows": operation_rows,
        "pair_rows": pair_rows,
        "prediction_before_target_oracle": True,
    }


def fit_osworld_source(
    source_path: Path,
    visible: dict[str, list[str]],
    sessions: list[str],
) -> dict[str, Any]:
    association, occurrence_scores, association_report = transition_npmi(
        sessions, visible
    )
    oracle = osworld_oracle(source_path, sessions, visible)
    percentile_association, cdf = empirical_cdf_association(
        association, occurrence_scores
    )
    percentile_cutoff, percentile_fit = fit_cutoff(
        sessions, visible, percentile_association, oracle
    )
    raw_cutoff, raw_fit = fit_cutoff(sessions, visible, association, oracle)
    return {
        "source": "OSWorld-Human grouped trajectories",
        "association": association_report,
        "cdf": cdf,
        "percentile_cutoff": percentile_cutoff,
        "percentile_fit": percentile_fit,
        "raw_cutoff": raw_cutoff,
        "raw_fit": raw_fit,
    }


def predict_codetrace_before_oracle(
    mode: str,
    prepared: dict[str, Any],
    source_fit: dict[str, Any],
    out_dir: Path,
) -> tuple[list[str], dict[str, dict[tuple[str, int], dict[str, Any]]], dict[str, Any]]:
    selected = sorted(prepared["targets"])
    if mode == "preflight":
        selected = selected[:1]
    candidate, raw, cdf = predict_transfer(
        selected,
        prepared["target_visible"],
        prepared["association"],
        prepared["occurrence_scores"],
        float(source_fit["percentile_cutoff"]),
        float(source_fit["raw_cutoff"]),
    )
    label_free, label_free_report = predict_label_free(
        selected,
        prepared["target_visible"],
        prepared["association"],
        prepared["occurrence_scores"],
        prepared["score_reference"],
        prepared["reference_visible"],
    )
    expected = {
        (session, position)
        for session in selected
        for position in range(1, len(prepared["target_visible"][session]))
    }
    require(
        set(candidate) == set(raw) == set(label_free) == expected,
        "CodeTrace prediction key mismatch",
    )
    unscored = []
    for key in sorted(expected):
        session, position = key
        unscored.append(
            {
                "session": session,
                "position": position,
                "left_action": prepared["target_visible"][session][position - 1],
                "right_action": prepared["target_visible"][session][position],
                "npmi": candidate[key]["npmi"],
                "percentile": candidate[key]["percentile"],
                "candidate": bool(candidate[key]["boundary"]),
                "raw_transfer": bool(raw[key]["boundary"]),
                "label_free": bool(label_free[key]["boundary"]),
            }
        )
    prediction_path = out_dir / "unscored-predictions.jsonl"
    write_jsonl(prediction_path, unscored)
    require(prediction_path.is_file(), "CodeTrace predictions were not persisted")
    return (
        selected,
        {
            "candidate": candidate,
            "raw_transfer": raw,
            "label_free": label_free,
        },
        {"target_cdf": cdf, "label_free_calibration": label_free_report},
    )


def score_codetrace_after_prediction(
    prepared: dict[str, Any],
    manifest_path: Path,
    selected: list[str],
    predictions: dict[str, dict[tuple[str, int], dict[str, Any]]],
    prediction_report: dict[str, Any],
    out_dir: Path,
) -> dict[str, Any]:
    oracle, frameworks, stage_count = load_stage_map(
        manifest_path,
        selected,
        prepared["targets"],
        False,
        out_dir / "target-stages.json",
    )
    assignments = method_assignments(
        selected, prepared["target_visible"], predictions
    )
    operation_rows = []
    pair_rows = []
    for session in selected:
        framework = frameworks[session]
        for index, action in enumerate(prepared["target_visible"][session]):
            operation_rows.append(
                {
                    "session": session,
                    "stratum": framework,
                    "framework": framework,
                    "operation_index": index,
                    "action": action,
                    "oracle_group": oracle[(session, index)],
                    **{
                        method: assignments[method][(session, index)]
                        for method in METHODS
                    },
                }
            )
        for position in range(1, len(prepared["target_visible"][session])):
            key = (session, position)
            pair_rows.append(
                {
                    "session": session,
                    "stratum": framework,
                    "framework": framework,
                    "position": position,
                    "candidate": bool(predictions["candidate"][key]["boundary"]),
                    "raw_transfer": bool(
                        predictions["raw_transfer"][key]["boundary"]
                    ),
                    "label_free": bool(
                        predictions["label_free"][key]["boundary"]
                    ),
                    "oracle_boundary": oracle[(session, position - 1)]
                    != oracle[(session, position)],
                }
            )
    write_jsonl(out_dir / "operation-assignments.jsonl", operation_rows)
    write_jsonl(out_dir / "pair-decisions.jsonl", pair_rows)
    metrics = all_metrics(operation_rows, pair_rows)
    return {
        "population": {
            "score_reference_sessions": len(prepared["score_reference"]),
            "score_reference_operations": sum(
                len(prepared["references"][session])
                for session in prepared["score_reference"]
            ),
            "target_sessions": len(selected),
            "target_operations": len(operation_rows),
            "target_pairs": len(pair_rows),
            "target_stages": stage_count,
            "target_frameworks": dict(Counter(frameworks.values())),
        },
        "association": prepared["association_report"],
        **prediction_report,
        "metrics": metrics,
        "operation_rows": operation_rows,
        "pair_rows": pair_rows,
        "prediction_before_target_oracle": True,
    }


def per_session_partition_sums(
    rows: list[dict[str, Any]], method: str
) -> dict[str, dict[str, float]]:
    by_session: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_session[str(row["session"])].append(row)
    output = {}
    for session, session_rows in by_session.items():
        metrics = partition_metrics(session_rows, method)
        operations = int(metrics["operations"])
        output[session] = {
            "operations": float(operations),
            "precision_sum": float(metrics["precision"]) * operations,
            "recall_sum": float(metrics["recall"]) * operations,
        }
    return output


def f1_from_sums(parts: list[dict[str, float]]) -> float:
    operations = sum(part["operations"] for part in parts)
    require(operations > 0, "bootstrap draw has no operations")
    precision = sum(part["precision_sum"] for part in parts) / operations
    recall = sum(part["recall_sum"] for part in parts) / operations
    return 2 * precision * recall / (precision + recall) if precision + recall else 0.0


def percentile_interval(values: list[float]) -> list[float]:
    require(len(values) == BOOTSTRAP_DRAWS, "bootstrap draw count changed")
    low, high = np.quantile(np.asarray(values, dtype=float), [0.025, 0.975])
    return [float(low), float(high)]


def bootstrap_partition_deltas(
    rows: list[dict[str, Any]], out_path: Path
) -> dict[str, Any]:
    strata: dict[str, list[str]] = defaultdict(list)
    seen: set[str] = set()
    for row in rows:
        session = str(row["session"])
        if session in seen:
            continue
        seen.add(session)
        strata[str(row["stratum"])].append(session)
    for sessions in strata.values():
        sessions.sort()
    sufficient = {
        method: per_session_partition_sums(rows, method) for method in METHODS
    }
    require(
        all(set(sufficient[method]) == seen for method in METHODS),
        "bootstrap method/session mismatch",
    )
    rng = random.Random(BOOTSTRAP_SEED)
    draws = []
    for draw in range(BOOTSTRAP_DRAWS):
        sampled = [
            rng.choice(sessions)
            for stratum in sorted(strata)
            for sessions in [strata[stratum]]
            for _ in sessions
        ]
        scores = {
            method: f1_from_sums([sufficient[method][session] for session in sampled])
            for method in METHODS
        }
        draws.append(
            {
                "draw": draw,
                **scores,
                "candidate_minus_label_free": scores["candidate"]
                - scores["label_free"],
                "candidate_minus_raw_transfer": scores["candidate"]
                - scores["raw_transfer"],
            }
        )
    write_jsonl(out_path, draws)
    return {
        "draws": BOOTSTRAP_DRAWS,
        "seed": BOOTSTRAP_SEED,
        "unit": "target session",
        "strata": {key: len(value) for key, value in sorted(strata.items())},
        "interval": "empirical 2.5th--97.5th percentile",
        "candidate_minus_label_free": percentile_interval(
            [row["candidate_minus_label_free"] for row in draws]
        ),
        "candidate_minus_raw_transfer": percentile_interval(
            [row["candidate_minus_raw_transfer"] for row in draws]
        ),
    }


def point_deltas(metrics: dict[str, Any]) -> dict[str, float]:
    candidate = float(metrics["candidate"]["partition"]["f1"])
    return {
        "candidate_minus_label_free": candidate
        - float(metrics["label_free"]["partition"]["f1"]),
        "candidate_minus_raw_transfer": candidate
        - float(metrics["raw_transfer"]["partition"]["f1"]),
    }


def sign(value: float) -> int:
    return 1 if value > 0 else (-1 if value < 0 else 0)


def classify(
    osworld: dict[str, Any], codetrace: dict[str, Any]
) -> tuple[str, dict[str, Any]]:
    points = {
        "osworld": point_deltas(osworld["metrics"]),
        "codetrace": point_deltas(codetrace["metrics"]),
    }
    intervals = {
        "osworld": osworld["bootstrap"],
        "codetrace": codetrace["bootstrap"],
    }
    label_points = [
        points[target]["candidate_minus_label_free"] for target in points
    ]
    raw_points = [
        points[target]["candidate_minus_raw_transfer"] for target in points
    ]
    point_order_positive = (
        all(value >= 0.0 for value in label_points)
        and any(value > 0.0 for value in label_points)
        and all(value > 0.0 for value in raw_points)
    )
    interval_order_positive = all(
        intervals[target]["candidate_minus_label_free"][0] >= 0.0
        and intervals[target]["candidate_minus_raw_transfer"][0] > 0.0
        for target in intervals
    )
    if point_order_positive and interval_order_positive:
        outcome = "supported"
    elif len(set(map(sign, label_points))) > 1 or len(set(map(sign, raw_points))) > 1:
        outcome = "mixed"
    elif all(value <= 0.0 for value in label_points) or all(
        value <= 0.0 for value in raw_points
    ):
        outcome = "contradicted"
    else:
        outcome = "inconclusive"
    return outcome, {
        "point_deltas": points,
        "point_order_positive": point_order_positive,
        "interval_order_positive": interval_order_positive,
        "rule_order": ["supported", "mixed", "contradicted", "inconclusive"],
    }


def verify_full_baselines(osworld: dict[str, Any], codetrace: dict[str, Any]) -> None:
    os_historical = json.loads(DEFAULT_OSWORLD_BASELINE.read_text(encoding="utf-8"))
    ct_historical = json.loads(DEFAULT_CODETRACE_BASELINE.read_text(encoding="utf-8"))
    require(
        osworld["population"]
        == {
            "sessions": OSWORLD_EXPECTED["sessions"],
            "operations": OSWORLD_EXPECTED["operations"],
            "pairs": OSWORLD_EXPECTED["pairs"],
            "oracle_groups": OSWORLD_EXPECTED["human_groups"],
        },
        "OSWorld complete population changed",
    )
    require(
        codetrace["population"]["target_sessions"]
        == CODETRACE_EXPECTED["target_sessions"]
        and codetrace["population"]["target_operations"]
        == CODETRACE_EXPECTED["target_operations"]
        and codetrace["population"]["target_pairs"]
        == CODETRACE_EXPECTED["target_pairs"]
        and codetrace["population"]["target_stages"]
        == CODETRACE_EXPECTED["target_stages"],
        "CodeTrace complete population changed",
    )
    comparisons = [
        (
            float(osworld["metrics"]["label_free"]["partition"]["f1"]),
            float(os_historical["partition_metrics"]["recurrence"]["f1"]),
            "OSWorld label-free B-cubed",
        ),
        (
            float(osworld["metrics"]["label_free"]["boundary"]["f1_exact"]),
            float(os_historical["boundary_metrics"]["recurrence"]["f1_exact"]),
            "OSWorld label-free boundary F1",
        ),
        (
            float(codetrace["metrics"]["label_free"]["partition"]["f1"]),
            float(ct_historical["metrics"]["recurrence"]["partition"]["f1"]),
            "CodeTrace label-free B-cubed",
        ),
        (
            float(codetrace["metrics"]["label_free"]["boundary"]["f1_exact"]),
            float(ct_historical["metrics"]["recurrence"]["boundary"]["f1"]),
            "CodeTrace label-free boundary F1",
        ),
    ]
    for actual, expected, label in comparisons:
        require(abs(actual - expected) < 1e-15, f"{label} changed: {actual} != {expected}")


def public_target(target: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in target.items() if key not in {"operation_rows", "pair_rows"}}


def markdown_report(summary: dict[str, Any]) -> str:
    lines = [
        "# Cross-Domain Percentile Calibration Result",
        "",
        f"**Mode:** {summary['mode']}  ",
        f"**Run status:** {summary['run_status']}  ",
        f"**Tested hypothesis:** {summary['tested_hypothesis']}",
        "",
        "## Standard Partition And Boundary Metrics",
        "",
        "| Target | Method | B-cubed F1 | Exact boundary F1 | Predicted groups |",
        "|---|---|---:|---:|---:|",
    ]
    for target_name, target in (
        ("OSWorld-Human", summary["osworld"]),
        ("CodeTraceBench", summary["codetrace"]),
    ):
        for method in METHODS:
            metrics = target["metrics"][method]
            lines.append(
                f"| {target_name} | {method} | {float(metrics['partition']['f1']):.6f} "
                f"| {float(metrics['boundary']['f1_exact']):.6f} "
                f"| {int(metrics['partition']['predicted_groups']):,} |"
            )
    if summary["mode"] == "full":
        lines.extend(["", "## Paired Session-Bootstrap Deltas", ""])
        for target_name, target in (
            ("OSWorld-Human", summary["osworld"]),
            ("CodeTraceBench", summary["codetrace"]),
        ):
            point = summary["decision"]["point_deltas"][
                "osworld" if target_name == "OSWorld-Human" else "codetrace"
            ]
            label_ci = target["bootstrap"]["candidate_minus_label_free"]
            raw_ci = target["bootstrap"]["candidate_minus_raw_transfer"]
            lines.append(
                f"- {target_name}: candidate-label-free {point['candidate_minus_label_free']:+.6f} "
                f"(95% [{label_ci[0]:+.6f}, {label_ci[1]:+.6f}]); "
                f"candidate-raw {point['candidate_minus_raw_transfer']:+.6f} "
                f"(95% [{raw_ci[0]:+.6f}, {raw_ci[1]:+.6f}])."
            )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            summary["interpretation"],
            "",
            "This experiment reuses previously observed complete populations. It is supporting mechanism evidence, not untouched independent confirmation, and it does not alter the paper thesis or RQs.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    args = parse_args()
    out_dir = absolute(args.out)
    osworld_path = absolute(args.osworld_operations)
    reference_path = absolute(args.codetrace_reference)
    target_path = absolute(args.codetrace_target)
    manifest_path = absolute(args.codetrace_manifest)
    for path in (osworld_path, reference_path, target_path, manifest_path):
        require(path.is_file(), f"missing input: {relative(path)}")
    out_dir.mkdir(parents=True, exist_ok=True)

    os_visible, os_sessions = osworld_source(osworld_path)
    ct = prepare_codetrace(reference_path, target_path, manifest_path)

    # Direction 1 is executed first so no OSWorld group value is loaded before
    # the CT-source -> OS-target predictions are persisted.
    ct_source_fit = fit_codetrace_source(
        ct, manifest_path, out_dir / "codetrace-to-osworld"
    )
    os_state, _ = predict_osworld_before_oracle(
        args.mode,
        os_visible,
        os_sessions,
        ct_source_fit,
        out_dir / "codetrace-to-osworld" / "osworld-target",
    )
    osworld = score_osworld_after_prediction(
        osworld_path,
        os_visible,
        os_state,
        out_dir / "codetrace-to-osworld" / "osworld-target",
    )

    # OSWorld labels become source information only after the reverse target
    # predictions above exist.  CodeTrace failed-stage labels remain unloaded.
    os_source_fit = fit_osworld_source(osworld_path, os_visible, os_sessions)
    selected_ct, ct_predictions, ct_prediction_report = (
        predict_codetrace_before_oracle(
            args.mode,
            ct,
            os_source_fit,
            out_dir / "osworld-to-codetrace" / "codetrace-target",
        )
    )
    codetrace = score_codetrace_after_prediction(
        ct,
        manifest_path,
        selected_ct,
        ct_predictions,
        ct_prediction_report,
        out_dir / "osworld-to-codetrace" / "codetrace-target",
    )

    if args.mode == "full":
        verify_full_baselines(osworld, codetrace)
        osworld["bootstrap"] = bootstrap_partition_deltas(
            osworld["operation_rows"], out_dir / "osworld-bootstrap-draws.jsonl"
        )
        codetrace["bootstrap"] = bootstrap_partition_deltas(
            codetrace["operation_rows"], out_dir / "codetrace-bootstrap-draws.jsonl"
        )
        tested_hypothesis, decision = classify(osworld, codetrace)
        upper_bound = json.loads(DEFAULT_UPPER_BOUND.read_text(encoding="utf-8"))
        upper_bound_control = {
            "osworld_per_domain_calibrated_bcubed": upper_bound["osworld"]["metrics"]
            ["candidate"]["partition"]["f1"],
            "codetrace_per_domain_calibrated_bcubed": upper_bound["codetrace"]
            ["metrics"]["candidate"]["partition"]["f1"],
            "information": "target-domain grouped-reference calibration",
        }
        interpretation = {
            "supported": "The unchanged recurrence score supports bidirectional percentile-scale calibration under the registered point and uncertainty rules; Rust integration and complete replay are required before adoption.",
            "mixed": "Percentile-scale transfer has inconsistent direction across the two complete targets; keep the current label-free default and close this normalization branch.",
            "contradicted": "Percentile-scale transfer fails the registered cross-domain ordering; keep the current label-free default and close this normalization branch.",
            "inconclusive": "The complete-population ordering is favorable but paired uncertainty does not support the registered cross-domain claim; keep the current label-free default and close this normalization branch.",
        }[tested_hypothesis]
    else:
        tested_hypothesis = "not tested"
        decision = None
        upper_bound_control = None
        interpretation = (
            "Both real source-fit, target-reference, prediction-persistence, and "
            "post-prediction oracle paths completed. Preflight makes no scientific decision."
        )

    summary = {
        "schema": "agentsight.rq3-cross-domain-percentile-calibration.v1",
        "mode": args.mode,
        "run_status": "valid",
        "tested_hypothesis": tested_hypothesis,
        "research_value": "supporting" if args.mode == "full" else "dependency-only",
        "interpretation": interpretation,
        "algorithm": {
            "base": "Step 0024 action-transition NPMI recurrence",
            "change": "one source-fitted cutoff expressed on the target unlabeled occurrence-weighted empirical-CDF scale",
            "new_score_terms": 0,
            "new_target_labels": 0,
            "unseen_transition": "boundary",
        },
        "source_fits": {
            "codetrace_for_osworld": ct_source_fit,
            "osworld_for_codetrace": os_source_fit,
        },
        "decision": decision,
        "upper_bound_control": upper_bound_control,
        "osworld": public_target(osworld),
        "codetrace": public_target(codetrace),
        "validity": {
            "existing_complete_trajectories_only": args.mode == "full",
            "bidirectional": True,
            "prediction_before_target_oracle": osworld[
                "prediction_before_target_oracle"
            ]
            and codetrace["prediction_before_target_oracle"],
            "one_assignment_per_operation": True,
            "standard_primary_metric": "operation-weighted B-cubed F1",
            "standard_secondary_metric": "exact boundary precision/recall/F1",
            "target_informed_retry": False,
            "submodule_untouched": True,
        },
        "inputs": {
            "osworld": relative(osworld_path),
            "codetrace_reference": relative(reference_path),
            "codetrace_target": relative(target_path),
            "codetrace_manifest": relative(manifest_path),
        },
    }
    write_json(out_dir / "summary.json", summary)
    (out_dir / "report.md").write_text(markdown_report(summary), encoding="utf-8")
    print(
        json.dumps(
            {
                "mode": args.mode,
                "run_status": "valid",
                "tested_hypothesis": tested_hypothesis,
                "osworld_candidate_bcubed": osworld["metrics"]["candidate"]
                ["partition"]["f1"],
                "codetrace_candidate_bcubed": codetrace["metrics"]["candidate"]
                ["partition"]["f1"],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
