#!/usr/bin/env python3
"""Score C5 user-task responses against the committed answer key.

This script is the result pipeline for a pilot or paper user study. It does not
invent participant data. C5 remains unsupported until a real response CSV is
provided and scored.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import itertools
import json
import math
import random
import statistics
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


SEMANTIC_CONDITION = "semantic-stack"
BASELINE_CONDITIONS = ("trace-tree", "event-count-proxy", "flat-summary", "nonsemantic-stack")
PRIMARY_ROLE = "primary_utility"
DEFAULT_MIN_PARTICIPANTS_FOR_CLAIM = 12
PILOT_MIN_PARTICIPANTS = 5
MIN_TASK_PAIRS_FOR_CLAIM = 8
ACCURACY_DELTA_THRESHOLD_PP = 10.0
TIME_REDUCTION_THRESHOLD_PCT = 20.0
MAX_FALSE_POSITIVE_INCREASE_PP = 5.0
P_VALUE_THRESHOLD = 0.05
MAX_EXACT_PERMUTATIONS = 32768
MONTE_CARLO_PERMUTATIONS = 4096
REQUIRED_RESPONSE_FIELDS = {
    "participant_id",
    "order_index",
    "packet_id",
    "task_id",
    "condition",
    "response_json",
    "task_time_seconds",
    "confidence",
    "notes",
}


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def load_answer_key(path: Path) -> dict[str, dict[str, Any]]:
    answers = {}
    for row in read_csv_rows(path):
        task_id = row.get("task_id")
        if not task_id:
            continue
        answers[task_id] = json.loads(row.get("answer_json") or "{}")
    return answers


def required_fields_by_task(bundle: dict[str, Any]) -> dict[str, list[str]]:
    out = {}
    for task in bundle.get("tasks", []):
        scoring = task.get("scoring") or {}
        required = scoring.get("required_fields")
        if not required:
            required = sorted((task.get("oracle") or {}).keys())
        out[str(task["task_id"])] = list(required)
    return out


def parse_response_json(text: str) -> tuple[dict[str, Any], str | None]:
    try:
        value = json.loads(text or "{}")
    except json.JSONDecodeError as exc:
        return {}, f"invalid_json:{exc.msg}"
    if not isinstance(value, dict):
        return {}, "invalid_json:not_object"
    return value, None


def values_match(expected: Any, actual: Any) -> bool:
    if isinstance(expected, bool):
        if isinstance(actual, bool):
            return expected == actual
        if isinstance(actual, str):
            lowered = actual.strip().lower()
            if lowered in {"true", "false"}:
                return expected == (lowered == "true")
        return False
    if isinstance(expected, int) and not isinstance(expected, bool):
        try:
            return int(actual) == expected
        except (TypeError, ValueError):
            return False
    if isinstance(expected, float):
        try:
            return abs(float(actual) - expected) <= 1e-6
        except (TypeError, ValueError):
            return False
    return str(actual).strip() == str(expected).strip()


def parse_float(value: str, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def parse_finite_float(value: str) -> float | None:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return parsed if math.isfinite(parsed) else None


def is_placeholder_response(row: dict[str, str]) -> bool:
    empty_response = row.get("response_json", "").strip() in {"", "{}"}
    no_measurements = not row.get("task_time_seconds", "").strip() and not row.get("confidence", "").strip()
    return empty_response and no_measurements


def score_response(
    row: dict[str, str],
    answer: dict[str, Any],
    required_fields: list[str],
) -> dict[str, Any]:
    response, parse_error = parse_response_json(row.get("response_json", ""))
    missing = []
    mismatched = []
    matched = []
    for field in required_fields:
        if field not in response:
            missing.append(field)
        elif values_match(answer.get(field), response[field]):
            matched.append(field)
        else:
            mismatched.append(field)
    extra_fields = sorted(set(response) - set(required_fields))
    false_positive_count = len(mismatched) + len(extra_fields)
    total = len(required_fields)
    accuracy = round(100.0 * len(matched) / total, 3) if total else 0.0
    exact = not parse_error and not missing and not mismatched and not extra_fields
    return {
        "participant_id": row.get("participant_id", ""),
        "order_index": row.get("order_index", ""),
        "packet_id": row.get("packet_id", ""),
        "task_id": row.get("task_id", ""),
        "condition": row.get("condition", ""),
        "task_time_seconds": parse_float(row.get("task_time_seconds", "")),
        "confidence": parse_float(row.get("confidence", "")),
        "exact": exact,
        "field_accuracy_pct": accuracy,
        "matched_fields": matched,
        "missing_fields": missing,
        "mismatched_fields": mismatched,
        "extra_fields": extra_fields,
        "false_positive_count": false_positive_count,
        "parse_error": parse_error or "",
    }


def mean(values: list[float]) -> float | None:
    return round(statistics.fmean(values), 3) if values else None


def median(values: list[float]) -> float | None:
    return round(statistics.median(values), 3) if values else None


def pct(part: int | float, whole: int | float) -> float | None:
    return round(100.0 * part / whole, 3) if whole else None


def summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    by_condition: dict[str, list[dict[str, Any]]] = defaultdict(list)
    by_task_condition: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_condition[row["condition"]].append(row)
        by_task_condition[(row["task_id"], row["condition"])].append(row)

    def section(items: list[dict[str, Any]]) -> dict[str, Any]:
        return {
            "response_count": len(items),
            "exact_accuracy_pct": round(100.0 * sum(1 for item in items if item["exact"]) / len(items), 3) if items else None,
            "mean_field_accuracy_pct": mean([item["field_accuracy_pct"] for item in items]),
            "mean_time_seconds": mean([item["task_time_seconds"] for item in items]),
            "median_time_seconds": median([item["task_time_seconds"] for item in items]),
            "mean_confidence": mean([item["confidence"] for item in items]),
            "false_positive_count": sum(int(item["false_positive_count"]) for item in items) if items else None,
            "false_positive_response_share_pct": pct(
                sum(1 for item in items if int(item["false_positive_count"]) > 0),
                len(items),
            ),
            "parse_error_count": sum(1 for item in items if item["parse_error"]) if items else None,
        }

    return {
        "overall": section(rows),
        "by_condition": {
            condition: section(items)
            for condition, items in sorted(by_condition.items())
        },
        "by_task_condition": {
            f"{task_id}/{condition}": section(items)
            for (task_id, condition), items in sorted(by_task_condition.items())
        },
        "condition_assignment_counts": dict(Counter(row["condition"] for row in rows)),
    }


def task_roles(bundle: dict[str, Any]) -> dict[str, str]:
    return {
        str(task["task_id"]): str(task.get("analysis_role") or "")
        for task in bundle.get("tasks", [])
    }


def mean_unrounded(values: list[float]) -> float | None:
    return statistics.fmean(values) if values else None


def paired_sign_flip_p_value(deltas: list[float], alternative: str = "greater") -> float | None:
    if not deltas:
        return None
    observed = statistics.fmean(deltas)
    if all(delta == 0 for delta in deltas):
        return 1.0
    extreme = 0
    total = 0
    for signs in itertools.product((-1, 1), repeat=len(deltas)):
        value = statistics.fmean([sign * delta for sign, delta in zip(signs, deltas)])
        total += 1
        if alternative == "greater":
            if value >= observed - 1e-12:
                extreme += 1
        elif alternative == "less":
            if value <= observed + 1e-12:
                extreme += 1
        else:
            if abs(value) >= abs(observed) - 1e-12:
                extreme += 1
    return round(extreme / total, 6)


def solve_linear_system(matrix: list[list[float]], vector: list[float]) -> list[float] | None:
    size = len(vector)
    if len(matrix) != size:
        return None
    coefficients = []
    for idx, matrix_row in enumerate(matrix):
        if not isinstance(matrix_row, list) or len(matrix_row) != size:
            return None
        coefficients.append([float(value) for value in matrix_row])
    rhs = [float(value) for value in vector]
    for col in range(size):
        pivot = max(range(col, size), key=lambda row_idx: abs(coefficients[row_idx][col]))
        if abs(coefficients[pivot][col]) < 1e-9:
            return None
        coefficients[col], coefficients[pivot] = coefficients[pivot], coefficients[col]
        rhs[col], rhs[pivot] = rhs[pivot], rhs[col]
        pivot_value = coefficients[col][col]
        pivot_row = [value / pivot_value for value in coefficients[col]]
        pivot_rhs = rhs[col] / pivot_value
        coefficients[col] = pivot_row
        rhs[col] = pivot_rhs
        for row_idx in range(size):
            if row_idx == col:
                continue
            factor = coefficients[row_idx][col]
            if factor == 0:
                continue
            coefficients[row_idx] = [
                value - factor * pivot_row[idx]
                for idx, value in enumerate(coefficients[row_idx])
            ]
            rhs[row_idx] -= factor * pivot_rhs
    return rhs


def metric_value(row: dict[str, Any], metric: str) -> float | None:
    if metric == "exact_accuracy_pct":
        return 100.0 if row["exact"] else 0.0
    if metric == "field_accuracy_pct":
        return float(row["field_accuracy_pct"])
    if metric == "false_positive_response_share_pct":
        return 100.0 if int(row["false_positive_count"]) > 0 else 0.0
    if metric == "log_time_seconds":
        value = float(row["task_time_seconds"])
        return math.log(value) if value > 0 else None
    raise AssertionError(f"unknown metric {metric!r}")


def fixed_effect_items(
    rows: list[dict[str, Any]],
    roles: dict[str, str],
    baseline: str,
    role_filter: str | None,
    metric: str,
) -> list[dict[str, Any]]:
    items = []
    for row in rows:
        if row["condition"] not in {SEMANTIC_CONDITION, baseline}:
            continue
        if role_filter and roles.get(row["task_id"], "") != role_filter:
            continue
        value = metric_value(row, metric)
        if value is None:
            continue
        items.append(
            {
                "participant_id": row["participant_id"],
                "task_id": row["task_id"],
                "order_index": row.get("order_index", ""),
                "condition": row["condition"],
                "semantic": row["condition"] == SEMANTIC_CONDITION,
                "value": value,
            }
        )
    return items


def ols_condition_coefficient(items: list[dict[str, Any]], semantic_labels: list[bool]) -> float | None:
    if not items or len(items) != len(semantic_labels):
        return None
    participants = sorted({str(item["participant_id"]) for item in items})
    tasks = sorted({str(item["task_id"]) for item in items})
    orders = sorted({str(item.get("order_index") or "") for item in items if str(item.get("order_index") or "")})
    if len(participants) < 2 or len(tasks) < 2:
        return None

    participant_cols = {participant: idx for idx, participant in enumerate(participants[1:], start=2)}
    task_offset = 2 + len(participant_cols)
    task_cols = {task: idx for idx, task in enumerate(tasks[1:], start=task_offset)}
    order_offset = task_offset + len(task_cols)
    order_cols = {order: idx for idx, order in enumerate(orders[1:], start=order_offset)}
    col_count = 2 + len(participant_cols) + len(task_cols) + len(order_cols)
    if len(items) <= col_count:
        return None

    xtx = [[0.0 for _ in range(col_count)] for _ in range(col_count)]
    xty = [0.0 for _ in range(col_count)]
    for item, semantic in zip(items, semantic_labels):
        row = [0.0] * col_count
        row[0] = 1.0
        row[1] = 1.0 if semantic else 0.0
        participant_col = participant_cols.get(str(item["participant_id"]))
        if participant_col is not None:
            row[participant_col] = 1.0
        task_col = task_cols.get(str(item["task_id"]))
        if task_col is not None:
            row[task_col] = 1.0
        order_col = order_cols.get(str(item.get("order_index") or ""))
        if order_col is not None:
            row[order_col] = 1.0
        value = float(item["value"])
        for left in range(col_count):
            xty[left] += row[left] * value
            if row[left] == 0:
                continue
            for right in range(col_count):
                xtx[left][right] += row[left] * row[right]

    coefficients = solve_linear_system(xtx, xty)
    if coefficients is None:
        return None
    return coefficients[1]


def stable_seed(text: str) -> int:
    return int.from_bytes(hashlib.sha256(text.encode("utf-8")).digest()[:8], "big")


def extreme_enough(value: float, observed: float, alternative: str) -> bool:
    if alternative == "greater":
        return value >= observed - 1e-12
    if alternative == "less":
        return value <= observed + 1e-12
    return abs(value) >= abs(observed) - 1e-12


def blocked_condition_permutation_test(
    items: list[dict[str, Any]],
    alternative: str,
    seed_key: str,
) -> dict[str, Any]:
    observed_labels = [bool(item["semantic"]) for item in items]
    observed = ols_condition_coefficient(items, observed_labels)
    if observed is None:
        return {
            "coefficient": None,
            "p_value": None,
            "mode": "insufficient_fixed_effect_data",
            "permutation_count": 0,
        }

    positions_by_task: dict[str, list[int]] = defaultdict(list)
    for idx, item in enumerate(items):
        positions_by_task[str(item["task_id"])].append(idx)

    group_options = []
    exact_permutation_count = 1
    exact_possible = True
    for positions in positions_by_task.values():
        semantic_count = sum(1 for pos in positions if observed_labels[pos])
        if semantic_count == 0 or semantic_count == len(positions):
            exact_possible = False
            break
        option_count = math.comb(len(positions), semantic_count)
        exact_permutation_count *= option_count
        if exact_permutation_count > MAX_EXACT_PERMUTATIONS:
            exact_possible = False
            break
        group_options.append(list(itertools.combinations(positions, semantic_count)))

    extreme = 0
    total = 0
    if exact_possible:
        for assignment in itertools.product(*group_options):
            labels = [False] * len(items)
            for group in assignment:
                for pos in group:
                    labels[pos] = True
            coefficient = ols_condition_coefficient(items, labels)
            if coefficient is None:
                continue
            total += 1
            if extreme_enough(coefficient, observed, alternative):
                extreme += 1
        mode = "exact_blocked_permutation"
    else:
        rng = random.Random(stable_seed(seed_key))
        grouped_positions = list(positions_by_task.values())
        for _ in range(MONTE_CARLO_PERMUTATIONS):
            labels = [False] * len(items)
            for positions in grouped_positions:
                semantic_count = sum(1 for pos in positions if observed_labels[pos])
                if semantic_count == 0 or semantic_count == len(positions):
                    for pos in positions:
                        labels[pos] = observed_labels[pos]
                    continue
                for pos in rng.sample(positions, semantic_count):
                    labels[pos] = True
            coefficient = ols_condition_coefficient(items, labels)
            if coefficient is None:
                continue
            total += 1
            if extreme_enough(coefficient, observed, alternative):
                extreme += 1
        mode = "monte_carlo_blocked_permutation"

    if total == 0:
        p_value = None
    elif exact_possible:
        p_value = extreme / total
    else:
        p_value = (extreme + 1) / (total + 1)
    return {
        "coefficient": round(observed, 6),
        "p_value": round(p_value, 6) if p_value is not None else None,
        "mode": mode,
        "permutation_count": total,
    }


def holm_adjust(p_values: list[tuple[str, float | None]]) -> dict[str, float | None]:
    adjusted: dict[str, float | None] = {name: None for name, _ in p_values}
    valid = sorted((p_value, name) for name, p_value in p_values if p_value is not None)
    total = len(valid)
    previous = 0.0
    for rank, (p_value, name) in enumerate(valid):
        candidate = min(1.0, (total - rank) * p_value)
        candidate = max(previous, candidate)
        previous = candidate
        adjusted[name] = round(candidate, 6)
    return adjusted


def condition_task_metrics(rows: list[dict[str, Any]], roles: dict[str, str]) -> dict[tuple[str, str], dict[str, Any]]:
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[(row["task_id"], row["condition"])].append(row)

    out: dict[tuple[str, str], dict[str, Any]] = {}
    for (task_id, condition), items in grouped.items():
        exact_values = [100.0 if item["exact"] else 0.0 for item in items]
        fp_values = [100.0 if int(item["false_positive_count"]) > 0 else 0.0 for item in items]
        out[(task_id, condition)] = {
            "task_id": task_id,
            "condition": condition,
            "analysis_role": roles.get(task_id, ""),
            "response_count": len(items),
            "exact_accuracy_pct": mean_unrounded(exact_values),
            "field_accuracy_pct": mean_unrounded([float(item["field_accuracy_pct"]) for item in items]),
            "time_seconds": mean_unrounded([float(item["task_time_seconds"]) for item in items]),
            "confidence": mean_unrounded([float(item["confidence"]) for item in items]),
            "false_positive_response_share_pct": mean_unrounded(fp_values),
            "false_positive_count": mean_unrounded([float(item["false_positive_count"]) for item in items]),
        }
    return out


def compare_condition_pair(
    task_metrics: dict[tuple[str, str], dict[str, Any]],
    baseline: str,
    role_filter: str | None,
) -> dict[str, Any]:
    paired = []
    for (task_id, condition), semantic in sorted(task_metrics.items()):
        if condition != SEMANTIC_CONDITION:
            continue
        if role_filter and semantic.get("analysis_role") != role_filter:
            continue
        base = task_metrics.get((task_id, baseline))
        if not base:
            continue
        baseline_time = float(base["time_seconds"] or 0.0)
        semantic_time = float(semantic["time_seconds"] or 0.0)
        time_reduction = 100.0 * (baseline_time - semantic_time) / baseline_time if baseline_time > 0 else 0.0
        paired.append(
            {
                "task_id": task_id,
                "accuracy_delta_pp": float(semantic["exact_accuracy_pct"] or 0.0) - float(base["exact_accuracy_pct"] or 0.0),
                "field_accuracy_delta_pp": float(semantic["field_accuracy_pct"] or 0.0) - float(base["field_accuracy_pct"] or 0.0),
                "time_reduction_pct": time_reduction,
                "false_positive_delta_pp": float(semantic["false_positive_response_share_pct"] or 0.0)
                - float(base["false_positive_response_share_pct"] or 0.0),
                "confidence_delta": float(semantic["confidence"] or 0.0) - float(base["confidence"] or 0.0),
            }
        )

    accuracy_deltas = [row["accuracy_delta_pp"] for row in paired]
    field_deltas = [row["field_accuracy_delta_pp"] for row in paired]
    time_reductions = [row["time_reduction_pct"] for row in paired]
    fp_deltas = [row["false_positive_delta_pp"] for row in paired]
    confidence_deltas = [row["confidence_delta"] for row in paired]
    return {
        "baseline_condition": baseline,
        "role_filter": role_filter or "all",
        "paired_task_count": len(paired),
        "mean_accuracy_delta_pp": round(mean_unrounded(accuracy_deltas), 3) if accuracy_deltas else None,
        "median_accuracy_delta_pp": median(accuracy_deltas),
        "accuracy_delta_p_value": paired_sign_flip_p_value(accuracy_deltas, "greater"),
        "mean_field_accuracy_delta_pp": round(mean_unrounded(field_deltas), 3) if field_deltas else None,
        "median_time_reduction_pct": median(time_reductions),
        "mean_time_reduction_pct": round(mean_unrounded(time_reductions), 3) if time_reductions else None,
        "time_reduction_p_value": paired_sign_flip_p_value(time_reductions, "greater"),
        "mean_false_positive_delta_pp": round(mean_unrounded(fp_deltas), 3) if fp_deltas else None,
        "median_false_positive_delta_pp": median(fp_deltas),
        "mean_confidence_delta": round(mean_unrounded(confidence_deltas), 3) if confidence_deltas else None,
        "paired_tasks": paired,
    }


def paper_scale_condition_comparison(
    rows: list[dict[str, Any]],
    roles: dict[str, str],
    task_comparison: dict[str, Any],
    baseline: str,
    role_filter: str | None,
) -> dict[str, Any]:
    accuracy_items = fixed_effect_items(rows, roles, baseline, role_filter, "exact_accuracy_pct")
    time_items = fixed_effect_items(rows, roles, baseline, role_filter, "log_time_seconds")
    fp_items = fixed_effect_items(rows, roles, baseline, role_filter, "false_positive_response_share_pct")
    accuracy_model = blocked_condition_permutation_test(
        accuracy_items,
        "greater",
        f"{baseline}:{role_filter}:exact_accuracy",
    )
    time_model = blocked_condition_permutation_test(
        time_items,
        "less",
        f"{baseline}:{role_filter}:log_time",
    )
    fp_model = blocked_condition_permutation_test(
        fp_items,
        "greater",
        f"{baseline}:{role_filter}:false_positive",
    )
    time_coefficient = time_model.get("coefficient")
    model_time_reduction = None
    if time_coefficient is not None:
        model_time_reduction = 100.0 * (1.0 - math.exp(float(time_coefficient)))
    return {
        "baseline_condition": baseline,
        "role_filter": role_filter or "all",
        "task_pair_count": task_comparison["paired_task_count"],
        "model_row_count": len(accuracy_items),
        "model_participant_count": len({item["participant_id"] for item in accuracy_items}),
        "model_task_count": len({item["task_id"] for item in accuracy_items}),
        "model_accuracy_delta_pp": accuracy_model.get("coefficient"),
        "accuracy_p_value": accuracy_model.get("p_value"),
        "accuracy_holm_p_value": None,
        "accuracy_test": accuracy_model,
        "median_task_time_reduction_pct": task_comparison["median_time_reduction_pct"],
        "model_time_reduction_pct": round(model_time_reduction, 3) if model_time_reduction is not None else None,
        "time_p_value": time_model.get("p_value"),
        "time_holm_p_value": None,
        "time_test": time_model,
        "model_false_positive_delta_pp": fp_model.get("coefficient"),
        "mean_false_positive_delta_pp": task_comparison["mean_false_positive_delta_pp"],
        "false_positive_test": fp_model,
    }


def paper_scale_comparisons(
    rows: list[dict[str, Any]],
    roles: dict[str, str],
    task_comparisons: list[dict[str, Any]],
    role_filter: str | None,
) -> list[dict[str, Any]]:
    comparisons = [
        paper_scale_condition_comparison(rows, roles, comparison, comparison["baseline_condition"], role_filter)
        for comparison in task_comparisons
    ]
    p_values = []
    for comparison in comparisons:
        baseline = comparison["baseline_condition"]
        p_values.append((f"{baseline}:accuracy", comparison["accuracy_p_value"]))
        p_values.append((f"{baseline}:time", comparison["time_p_value"]))
    adjusted = holm_adjust(p_values)
    for comparison in comparisons:
        baseline = comparison["baseline_condition"]
        comparison["accuracy_holm_p_value"] = adjusted[f"{baseline}:accuracy"]
        comparison["time_holm_p_value"] = adjusted[f"{baseline}:time"]
    return comparisons


def success_for_comparison(comparison: dict[str, Any]) -> bool:
    if comparison["paired_task_count"] < MIN_TASK_PAIRS_FOR_CLAIM:
        return False
    fp_delta = comparison["mean_false_positive_delta_pp"]
    fp_ok = fp_delta is not None and fp_delta <= MAX_FALSE_POSITIVE_INCREASE_PP
    accuracy_ok = (
        comparison["mean_accuracy_delta_pp"] is not None
        and comparison["mean_accuracy_delta_pp"] >= ACCURACY_DELTA_THRESHOLD_PP
        and comparison["accuracy_delta_p_value"] is not None
        and comparison["accuracy_delta_p_value"] <= P_VALUE_THRESHOLD
    )
    time_ok = (
        comparison["median_time_reduction_pct"] is not None
        and comparison["median_time_reduction_pct"] >= TIME_REDUCTION_THRESHOLD_PCT
        and comparison["time_reduction_p_value"] is not None
        and comparison["time_reduction_p_value"] <= P_VALUE_THRESHOLD
    )
    return fp_ok and (accuracy_ok or time_ok)


def success_for_paper_comparison(comparison: dict[str, Any]) -> bool:
    if comparison["task_pair_count"] < MIN_TASK_PAIRS_FOR_CLAIM:
        return False
    fp_delta = comparison["model_false_positive_delta_pp"]
    if fp_delta is None:
        fp_delta = comparison["mean_false_positive_delta_pp"]
    fp_ok = fp_delta is not None and fp_delta <= MAX_FALSE_POSITIVE_INCREASE_PP
    accuracy_ok = (
        comparison["model_accuracy_delta_pp"] is not None
        and comparison["model_accuracy_delta_pp"] >= ACCURACY_DELTA_THRESHOLD_PP
        and comparison["accuracy_holm_p_value"] is not None
        and comparison["accuracy_holm_p_value"] <= P_VALUE_THRESHOLD
    )
    time_ok = (
        comparison["median_task_time_reduction_pct"] is not None
        and comparison["median_task_time_reduction_pct"] >= TIME_REDUCTION_THRESHOLD_PCT
        and comparison["time_holm_p_value"] is not None
        and comparison["time_holm_p_value"] <= P_VALUE_THRESHOLD
    )
    return fp_ok and (accuracy_ok or time_ok)


def claim_analysis(rows: list[dict[str, Any]], bundle: dict[str, Any]) -> dict[str, Any]:
    roles = task_roles(bundle)
    participant_count = len({row["participant_id"] for row in rows if row["participant_id"]})
    if not rows:
        return {
            "status": "participant_results_empty",
            "participant_count": 0,
            "response_count": 0,
            "thresholds": claim_thresholds(),
            "task_level_primary_utility": None,
            "paper_scale_primary": None,
            "primary_utility": None,
            "all_tasks": None,
            "claim_gate": {
                "c5_supported": False,
                "pilot_ready": False,
                "requires_real_participants": True,
                "reason": "no scorable participant responses",
            },
        }

    metrics = condition_task_metrics(rows, roles)
    primary = [
        compare_condition_pair(metrics, baseline, PRIMARY_ROLE)
        for baseline in BASELINE_CONDITIONS
    ]
    paper_primary = paper_scale_comparisons(rows, roles, primary, PRIMARY_ROLE)
    all_tasks = [
        compare_condition_pair(metrics, baseline, None)
        for baseline in BASELINE_CONDITIONS
    ]
    diagnostic_successes = [row for row in primary if success_for_comparison(row)]
    paper_successes = [row for row in paper_primary if success_for_paper_comparison(row)]
    complete_primary_baseline_coverage = all(row["paired_task_count"] >= MIN_TASK_PAIRS_FOR_CLAIM for row in primary)
    enough_participants_for_claim = participant_count >= DEFAULT_MIN_PARTICIPANTS_FOR_CLAIM
    pilot_ready = participant_count >= PILOT_MIN_PARTICIPANTS and complete_primary_baseline_coverage
    paper_model_ready = all(
        row["model_row_count"] > 0
        and row["model_participant_count"] >= DEFAULT_MIN_PARTICIPANTS_FOR_CLAIM
        and row["model_task_count"] >= MIN_TASK_PAIRS_FOR_CLAIM
        and row["accuracy_holm_p_value"] is not None
        and row["time_holm_p_value"] is not None
        for row in paper_primary
    )
    c5_supported = (
        enough_participants_for_claim
        and complete_primary_baseline_coverage
        and paper_model_ready
        and len(paper_successes) == len(paper_primary)
    )
    return {
        "status": "participant_results_analyzed",
        "participant_count": participant_count,
        "response_count": len(rows),
        "thresholds": claim_thresholds(),
        "task_level_primary_utility": {
            "comparisons": primary,
            "successful_comparison_count": len(diagnostic_successes),
            "complete_baseline_coverage": complete_primary_baseline_coverage,
            "claim_boundary": "diagnostic only; paper-scale C5 support uses paper_scale_primary",
        },
        "paper_scale_primary": {
            "comparisons": paper_primary,
            "successful_comparison_count": len(paper_successes),
            "model_ready": paper_model_ready,
            "holm_family": "primary baseline comparisons x {exact accuracy, log time}",
            "statistical_model": "participant-task-order fixed-effect blocked permutation",
        },
        "primary_utility": {
            "comparisons": paper_primary,
            "successful_comparison_count": len(paper_successes),
            "complete_baseline_coverage": complete_primary_baseline_coverage,
        },
        "all_tasks": {
            "comparisons": all_tasks,
        },
        "claim_gate": {
            "c5_supported": c5_supported,
            "pilot_ready": pilot_ready,
            "requires_real_participants": False,
            "enough_participants_for_claim": enough_participants_for_claim,
            "complete_primary_baseline_coverage": complete_primary_baseline_coverage,
            "paper_model_ready": paper_model_ready,
            "success_rule": (
                "All four baselines must be beaten on primary utility tasks by >=10 pp exact accuracy "
                "or >=20% median task time reduction with Holm-corrected participant/task/order "
                "fixed-effect permutation p<=0.05, "
                "without >5 pp false-positive increase."
            ),
        },
    }


def claim_thresholds() -> dict[str, Any]:
    return {
        "semantic_condition": SEMANTIC_CONDITION,
        "baseline_conditions": list(BASELINE_CONDITIONS),
        "primary_role": PRIMARY_ROLE,
        "min_participants_for_claim": DEFAULT_MIN_PARTICIPANTS_FOR_CLAIM,
        "pilot_min_participants": PILOT_MIN_PARTICIPANTS,
        "min_task_pairs_for_claim": MIN_TASK_PAIRS_FOR_CLAIM,
        "accuracy_delta_threshold_pp": ACCURACY_DELTA_THRESHOLD_PP,
        "time_reduction_threshold_pct": TIME_REDUCTION_THRESHOLD_PCT,
        "max_false_positive_increase_pp": MAX_FALSE_POSITIVE_INCREASE_PP,
        "p_value_threshold": P_VALUE_THRESHOLD,
        "diagnostic_test": "paired task-level sign-flip permutation",
        "paper_scale_test": "participant-task-order fixed-effect blocked permutation",
        "holm_correction_family": "primary baseline comparisons x accuracy/time endpoints",
        "monte_carlo_permutations": MONTE_CARLO_PERMUTATIONS,
    }


def write_scored_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    fields = [
        "participant_id",
        "order_index",
        "packet_id",
        "task_id",
        "condition",
        "task_time_seconds",
        "confidence",
        "exact",
        "field_accuracy_pct",
        "false_positive_count",
        "parse_error",
        "missing_fields",
        "mismatched_fields",
        "extra_fields",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    **{field: row.get(field, "") for field in fields},
                    "missing_fields": ";".join(row.get("missing_fields", [])),
                    "mismatched_fields": ";".join(row.get("mismatched_fields", [])),
                    "extra_fields": ";".join(row.get("extra_fields", [])),
                }
            )


def write_summary_md(path: Path, result: dict[str, Any]) -> None:
    lines = [
        "# User Task Results",
        "",
        "This report scores participant responses for C5 against the committed answer key.",
        "",
        "## Overall",
        "",
    ]
    overall = result["summary"]["overall"]
    analysis = result["claim_analysis"]
    gate = analysis["claim_gate"]
    lines.extend(
        [
            f"- Responses: {overall['response_count']}.",
            f"- Exact accuracy: {overall['exact_accuracy_pct'] if overall['exact_accuracy_pct'] is not None else 'n/a'}.",
            f"- Mean field accuracy: {overall['mean_field_accuracy_pct'] if overall['mean_field_accuracy_pct'] is not None else 'n/a'}.",
            f"- Mean time: {overall['mean_time_seconds'] if overall['mean_time_seconds'] is not None else 'n/a'} seconds.",
            f"- False positives: {overall['false_positive_count'] if overall['false_positive_count'] is not None else 'n/a'}.",
            f"- C5 supported: {gate['c5_supported']}.",
            f"- Pilot ready: {gate['pilot_ready']}.",
            "",
            "## Claim Boundary",
            "",
            "- This is scored evidence only when `source` points to a real participant-response file.",
            "- Pilot-scale results should guide task/instrument changes, not final user-utility claims.",
            "- Paper-scale support requires the Holm-corrected participant/task/order fixed-effect gate in `claim_analysis` to pass.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def assignment_key(row: dict[str, str]) -> tuple[str, str, str, str]:
    return (
        row.get("participant_id", "").strip(),
        row.get("task_id", "").strip(),
        row.get("condition", "").strip(),
        row.get("packet_id", "").strip(),
    )


def task_condition_packets(bundle: dict[str, Any]) -> dict[tuple[str, str], str]:
    packets = {}
    for task in bundle.get("tasks", []):
        task_id = str(task["task_id"])
        for condition in task.get("participant_view_conditions", []):
            name = str(condition["condition"])
            packets[(task_id, name)] = f"{task_id}-{name}"
    return packets


def load_assignment_rows(path_text: str | None) -> list[dict[str, str]]:
    if not path_text:
        return []
    path = Path(path_text)
    if not path.exists():
        return []
    return read_csv_rows(path)


def validate_response_contract(
    response_rows: list[dict[str, str]],
    bundle: dict[str, Any],
    assignment_rows: list[dict[str, str]],
) -> dict[str, Any]:
    errors = []
    warnings = []
    fieldnames = set(response_rows[0].keys()) if response_rows else set()
    missing_fields = sorted(REQUIRED_RESPONSE_FIELDS - fieldnames)
    if missing_fields:
        errors.append(f"response CSV is missing required fields: {missing_fields}")

    task_ids = {str(task["task_id"]) for task in bundle.get("tasks", [])}
    allowed_packets = task_condition_packets(bundle)
    allowed_conditions = {condition for _, condition in allowed_packets}
    response_key_counts = Counter(assignment_key(row) for row in response_rows)
    duplicate_response_keys = [key for key, count in response_key_counts.items() if count > 1]
    if duplicate_response_keys:
        errors.append(f"duplicate response assignment rows: {duplicate_response_keys[:5]}")

    scorable_count = 0
    placeholder_count = 0
    for row_number, row in enumerate(response_rows, start=2):
        key = assignment_key(row)
        participant_id, task_id, condition, packet_id = key
        if task_id not in task_ids:
            errors.append(f"row {row_number} references unknown task_id {task_id!r}")
            continue
        if condition not in allowed_conditions:
            errors.append(f"row {row_number} references unknown condition {condition!r}")
            continue
        expected_packet = allowed_packets.get((task_id, condition))
        if packet_id != expected_packet:
            errors.append(f"row {row_number} packet_id {packet_id!r} does not match {expected_packet!r}")
        placeholder = is_placeholder_response(row)
        if placeholder:
            placeholder_count += 1
            continue
        scorable_count += 1
        if not participant_id:
            errors.append(f"row {row_number} has a scorable response without participant_id")
        task_time = parse_finite_float(row.get("task_time_seconds", ""))
        if task_time is None or task_time <= 0:
            errors.append(f"row {row_number} has invalid task_time_seconds {row.get('task_time_seconds')!r}")
        confidence = parse_finite_float(row.get("confidence", ""))
        if confidence is None or not (1.0 <= confidence <= 5.0):
            errors.append(f"row {row_number} has invalid confidence {row.get('confidence')!r}; expected 1..5")

    if assignment_rows:
        assignment_key_counts = Counter(assignment_key(row) for row in assignment_rows)
        duplicate_assignment_keys = [key for key, count in assignment_key_counts.items() if count > 1]
        if duplicate_assignment_keys:
            errors.append(f"duplicate assignment rows: {duplicate_assignment_keys[:5]}")
        response_keys = set(response_key_counts)
        assignment_keys = set(assignment_key_counts)
        missing_response_rows = sorted(assignment_keys - response_keys)
        extra_response_rows = sorted(response_keys - assignment_keys)
        if missing_response_rows:
            errors.append(f"response CSV is missing assigned rows: {missing_response_rows[:5]}")
        if extra_response_rows:
            errors.append(f"response CSV contains rows outside assignment file: {extra_response_rows[:5]}")
    else:
        warnings.append("assignment file missing; packet/task/condition shape validated but assignment coverage was not checked")

    if scorable_count and placeholder_count:
        errors.append(
            "partial participant response files are not accepted: every assigned row must be completed once scoring starts"
        )

    return {
        "valid": not errors,
        "errors": errors,
        "warnings": warnings,
        "assignment_row_count": len(assignment_rows),
        "response_row_count": len(response_rows),
        "scorable_row_count": scorable_count,
        "placeholder_row_count": placeholder_count,
        "complete_assigned_rows": scorable_count > 0 and placeholder_count == 0,
        "template_only": scorable_count == 0 and placeholder_count == len(response_rows),
        "requires_complete_assigned_rows": scorable_count > 0,
    }


def run(args: argparse.Namespace) -> dict[str, Any]:
    out_dir = Path(args.out).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    bundle = read_json(Path(args.bundle))
    answers = load_answer_key(Path(args.answer_key))
    required = required_fields_by_task(bundle)
    response_rows = read_csv_rows(Path(args.responses))
    assignment_rows = load_assignment_rows(getattr(args, "assignments", None))
    response_contract = validate_response_contract(response_rows, bundle, assignment_rows)
    if not response_contract["valid"]:
        formatted = "\n- ".join(response_contract["errors"])
        raise AssertionError(f"invalid C5 response CSV:\n- {formatted}")
    scorable_rows = [row for row in response_rows if not is_placeholder_response(row)]
    scored = []
    for row in scorable_rows:
        task_id = row.get("task_id", "")
        if task_id not in answers:
            raise AssertionError(f"response references unknown task_id {task_id!r}")
        scored.append(score_response(row, answers[task_id], required.get(task_id, sorted(answers[task_id]))))

    result = {
        "schema_version": 1,
        "claim": "C5",
        "status": "participant_results_scored" if scored else "participant_results_empty",
        "source": Path(args.responses).name,
        "template_row_count": len(response_rows),
        "ignored_placeholder_rows": len(response_rows) - len(scorable_rows),
        "response_contract": response_contract,
        "participant_count": len({row["participant_id"] for row in scored if row["participant_id"]}),
        "response_count": len(scored),
        "task_count": len({row["task_id"] for row in scored}),
        "summary": summarize(scored),
        "claim_analysis": claim_analysis(scored, bundle),
        "scored_rows": scored,
        "claim_boundary": "C5 requires real participant responses and adequate sample size before becoming supported",
    }
    (out_dir / "user-task-results.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    write_scored_csv(out_dir / "user-task-results.csv", scored)
    write_summary_md(out_dir / "user-task-results.md", result)
    print(json.dumps({key: result[key] for key in ("status", "participant_count", "response_count", "task_count")}, indent=2))
    return result


def build_parser() -> argparse.ArgumentParser:
    here = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--responses", required=True, help="CSV collected from user-task-response-template.csv")
    parser.add_argument("--bundle", default=str(here / "out" / "user-task-benchmark.json"))
    parser.add_argument("--answer-key", default=str(here / "out" / "user-task-answer-key.csv"))
    parser.add_argument("--assignments", default=str(here / "out" / "user-task-assignments.csv"))
    parser.add_argument("--out", default=str(here / "out"))
    return parser


if __name__ == "__main__":
    run(build_parser().parse_args())
