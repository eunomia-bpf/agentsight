#!/usr/bin/env python3
"""Score retrospective cross-framework same-task retrieval for Step 0093.

This script is intentionally standard-library-only. It never uses session IDs
to resolve score ties: AP, Top-1, and MRR marginalize uniformly over tied
permutations, and AUROC assigns tied positive/negative pairs weight 0.5.
"""

from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import math
import random
import statistics
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable


SEED = 20260729
BOOTSTRAP_REPLICATES = 10_000
HERE = Path(__file__).resolve().parent
INPUT_DIR = (
    HERE.parent.parent
    / "step-0087-20260726T023000-0700"
    / "experiment-001"
)
INPUTS = {
    "source_operations": INPUT_DIR / "assembled" / "operations-count.jsonl",
    "precanonical_predictions": INPUT_DIR / "assembled" / "predictions.jsonl",
    "canonical_predictions": INPUT_DIR / "canonical" / "predictions.jsonl",
    "step0087_summary": INPUT_DIR / "assembled" / "summary.json",
    "canonicalization_report": INPUT_DIR
    / "canonical"
    / "canonicalization-report.json",
}

VECTOR_METHODS = (
    "canonical_full",
    "action_kind",
    "raw_action_key",
    "precanonical_full",
    "canonical_root_only",
    "canonical_root_stripped",
    "phase",
    "canonical_leaf",
    "canonical_generic_removed",
    "canonical_root_stripped_generic_removed",
    "canonical_full_binary",
    "action_kind_binary",
    "raw_action_key_binary",
    "canonical_full_tfidf",
    "action_kind_tfidf",
    "raw_action_key_tfidf",
)
SPECIAL_METHODS = ("operation_count", "random")
METHODS = VECTOR_METHODS + SPECIAL_METHODS

BOOTSTRAP_COMPARISONS = {
    "canonical_full-minus-action_kind": ("canonical_full", "action_kind"),
    "canonical_full-minus-raw_action_key": (
        "canonical_full",
        "raw_action_key",
    ),
    "canonical_full-minus-canonical_root_only": (
        "canonical_full",
        "canonical_root_only",
    ),
    "canonical_root_stripped-minus-action_kind": (
        "canonical_root_stripped",
        "action_kind",
    ),
    "canonical_root_stripped-minus-raw_action_key": (
        "canonical_root_stripped",
        "raw_action_key",
    ),
    "canonical_root_stripped_generic_removed-minus-action_kind": (
        "canonical_root_stripped_generic_removed",
        "action_kind",
    ),
    "canonical_root_stripped_generic_removed-minus-raw_action_key": (
        "canonical_root_stripped_generic_removed",
        "raw_action_key",
    ),
    "canonical_generic_removed-minus-action_kind": (
        "canonical_generic_removed",
        "action_kind",
    ),
    "canonical_generic_removed-minus-raw_action_key": (
        "canonical_generic_removed",
        "raw_action_key",
    ),
    "canonical_full-minus-phase": ("canonical_full", "phase"),
    "canonical_full-minus-operation_count": (
        "canonical_full",
        "operation_count",
    ),
    "canonical_full-minus-precanonical_full": (
        "canonical_full",
        "precanonical_full",
    ),
    "canonical_full_binary-minus-action_kind_binary": (
        "canonical_full_binary",
        "action_kind_binary",
    ),
    "canonical_full_binary-minus-raw_action_key_binary": (
        "canonical_full_binary",
        "raw_action_key_binary",
    ),
    "canonical_full_tfidf-minus-action_kind_tfidf": (
        "canonical_full_tfidf",
        "action_kind_tfidf",
    ),
    "canonical_full_tfidf-minus-raw_action_key_tfidf": (
        "canonical_full_tfidf",
        "raw_action_key_tfidf",
    ),
}


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                value = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}:{line_number}: invalid JSON: {exc}") from exc
            if not isinstance(value, dict):
                raise ValueError(f"{path}:{line_number}: row is not an object")
            rows.append(value)
    return rows


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_json(path: Path, value: Any) -> None:
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(
                json.dumps(row, sort_keys=True, ensure_ascii=False) + "\n"
            )


def normalized_label(value: Any) -> str:
    label = " ".join(str(value).strip().lower().split())
    if not label:
        raise ValueError("empty semantic-stack label")
    return label


def row_key(row: dict[str, Any]) -> tuple[str, str]:
    try:
        session = str(row["session"])
        step_id = str(row["step_id"])
    except KeyError as exc:
        raise ValueError(f"prediction lacks {exc.args[0]}") from exc
    if not session or not step_id:
        raise ValueError("empty prediction session or step_id")
    return session, step_id


def source_row_key(row: dict[str, Any]) -> tuple[str, str]:
    fields = row.get("fields")
    if not isinstance(fields, dict):
        raise ValueError("source operation row lacks fields object")
    try:
        session = str(fields["session"])
        step_id = str(fields["step_id"])
    except KeyError as exc:
        raise ValueError(f"source operation lacks fields.{exc.args[0]}") from exc
    if not session or not step_id:
        raise ValueError("empty source session or step_id")
    return session, step_id


def prediction_map(
    rows: list[dict[str, Any]], name: str
) -> dict[tuple[str, str], dict[str, Any]]:
    result: dict[tuple[str, str], dict[str, Any]] = {}
    for row in rows:
        key = row_key(row)
        if key in result:
            raise ValueError(f"duplicate {name} prediction key: {key}")
        stack = row.get("semantic_stack")
        if not isinstance(stack, list) or not stack:
            raise ValueError(f"{name} prediction {key} has empty/non-list stack")
        for frame in stack:
            if not isinstance(frame, dict) or "label" not in frame:
                raise ValueError(f"{name} prediction {key} has invalid frame")
            normalized_label(frame["label"])
        result[key] = row
    return result


def stack_labels(row: dict[str, Any]) -> list[str]:
    return [normalized_label(frame["label"]) for frame in row["semantic_stack"]]


def path_feature(labels: list[str]) -> str:
    return " / ".join(labels) if labels else "<empty>"


def clip_binary(
    vectors: dict[str, Counter[str]]
) -> dict[str, Counter[str]]:
    return {
        session: Counter({feature: 1.0 for feature in values})
        for session, values in vectors.items()
    }


def apply_tfidf(
    vectors: dict[str, Counter[str]]
) -> dict[str, Counter[str]]:
    total = len(vectors)
    document_frequency: Counter[str] = Counter()
    for values in vectors.values():
        document_frequency.update(values.keys())
    transformed: dict[str, Counter[str]] = {}
    for session, values in vectors.items():
        transformed[session] = Counter(
            {
                feature: count
                * (math.log((1.0 + total) / (1.0 + document_frequency[feature])) + 1.0)
                for feature, count in values.items()
            }
        )
    return transformed


def build_dataset() -> dict[str, Any]:
    for name, path in INPUTS.items():
        if not path.is_file():
            raise FileNotFoundError(f"missing frozen input {name}: {path}")

    source_rows = load_jsonl(INPUTS["source_operations"])
    precanonical_rows = load_jsonl(INPUTS["precanonical_predictions"])
    canonical_rows = load_jsonl(INPUTS["canonical_predictions"])
    precanonical = prediction_map(precanonical_rows, "precanonical")
    canonical = prediction_map(canonical_rows, "canonical")

    source: dict[tuple[str, str], dict[str, Any]] = {}
    session_order: list[str] = []
    session_seen: set[str] = set()
    session_meta: dict[str, dict[str, str]] = {}

    base_vectors: dict[str, dict[str, Counter[str]]] = {
        method: defaultdict(Counter)
        for method in (
            "canonical_full",
            "action_kind",
            "raw_action_key",
            "precanonical_full",
            "canonical_root_only",
            "canonical_root_stripped",
            "phase",
            "canonical_leaf",
            "canonical_generic_removed",
            "canonical_root_stripped_generic_removed",
        )
    }
    operation_counts: Counter[str] = Counter()
    canonical_roots: set[str] = set()

    for row in source_rows:
        key = source_row_key(row)
        if key in source:
            raise ValueError(f"duplicate source operation key: {key}")
        if row.get("value") != 1:
            raise ValueError(f"source operation {key} has non-unit value")
        fields = row["fields"]
        for required in ("prompt", "agent", "action_kind", "raw_action_key", "phase"):
            if required not in fields:
                raise ValueError(f"source operation {key} lacks fields.{required}")
        session, _ = key
        prompt = str(fields["prompt"])
        agent = str(fields["agent"])
        if not prompt or not agent:
            raise ValueError(f"source operation {key} has empty prompt/agent")
        if session not in session_seen:
            session_seen.add(session)
            session_order.append(session)
            session_meta[session] = {"task": prompt, "framework": agent}
        elif session_meta[session] != {"task": prompt, "framework": agent}:
            raise ValueError(f"session {session} disagrees on prompt or agent")
        source[key] = row

    source_keys = set(source)
    if set(precanonical) != source_keys:
        missing = len(source_keys - set(precanonical))
        extra = len(set(precanonical) - source_keys)
        raise ValueError(
            f"precanonical/source key mismatch: missing={missing}, extra={extra}"
        )
    if set(canonical) != source_keys:
        missing = len(source_keys - set(canonical))
        extra = len(set(canonical) - source_keys)
        raise ValueError(
            f"canonical/source key mismatch: missing={missing}, extra={extra}"
        )

    for key, row in source.items():
        fields = row["fields"]
        session = key[0]
        expected_framework = str(fields["agent"])
        for name, predictions in (
            ("precanonical", precanonical),
            ("canonical", canonical),
        ):
            actual_framework = str(predictions[key].get("framework", ""))
            if actual_framework != expected_framework:
                raise ValueError(
                    f"{name} framework mismatch at {key}: "
                    f"{actual_framework!r} != {expected_framework!r}"
                )

        direct_labels = stack_labels(precanonical[key])
        canonical_labels = stack_labels(canonical[key])
        root_stripped = canonical_labels[1:]
        generic_removed = [
            label for label in canonical_labels if not label.endswith(" work")
        ]
        root_stripped_generic_removed = [
            label for label in root_stripped if not label.endswith(" work")
        ]

        base_vectors["canonical_full"][session][
            path_feature(canonical_labels)
        ] += 1.0
        base_vectors["action_kind"][session][
            normalized_label(fields["action_kind"])
        ] += 1.0
        base_vectors["raw_action_key"][session][
            normalized_label(fields["raw_action_key"])
        ] += 1.0
        base_vectors["precanonical_full"][session][
            path_feature(direct_labels)
        ] += 1.0
        base_vectors["canonical_root_only"][session][canonical_labels[0]] += 1.0
        base_vectors["canonical_root_stripped"][session][
            path_feature(root_stripped)
        ] += 1.0
        base_vectors["phase"][session][normalized_label(fields["phase"])] += 1.0
        base_vectors["canonical_leaf"][session][canonical_labels[-1]] += 1.0
        base_vectors["canonical_generic_removed"][session][
            path_feature(generic_removed)
        ] += 1.0
        base_vectors["canonical_root_stripped_generic_removed"][session][
            path_feature(root_stripped_generic_removed)
        ] += 1.0
        operation_counts[session] += 1
        canonical_roots.add(canonical_labels[0])

    for method, vectors in base_vectors.items():
        if set(vectors) != set(session_order):
            raise ValueError(f"{method} does not cover every session")
        if any(not values for values in vectors.values()):
            raise ValueError(f"{method} contains an empty session vector")

    vectors: dict[str, dict[str, Counter[str]]] = dict(base_vectors)
    vectors["canonical_full_binary"] = clip_binary(
        base_vectors["canonical_full"]
    )
    vectors["action_kind_binary"] = clip_binary(base_vectors["action_kind"])
    vectors["raw_action_key_binary"] = clip_binary(
        base_vectors["raw_action_key"]
    )
    vectors["canonical_full_tfidf"] = apply_tfidf(
        base_vectors["canonical_full"]
    )
    vectors["action_kind_tfidf"] = apply_tfidf(base_vectors["action_kind"])
    vectors["raw_action_key_tfidf"] = apply_tfidf(
        base_vectors["raw_action_key"]
    )

    tasks = sorted({meta["task"] for meta in session_meta.values()})
    frameworks = sorted({meta["framework"] for meta in session_meta.values()})
    query_sessions = [
        query
        for query in session_order
        if any(
            session_meta[candidate]["task"] == session_meta[query]["task"]
            and session_meta[candidate]["framework"]
            != session_meta[query]["framework"]
            for candidate in session_order
            if candidate != query
        )
    ]
    eligible_tasks = sorted({session_meta[q]["task"] for q in query_sessions})
    if not query_sessions:
        raise ValueError("no eligible cross-framework queries")

    relevant_framework_pairs: Counter[str] = Counter()
    candidate_counts: list[int] = []
    relevant_counts: list[int] = []
    for query in query_sessions:
        candidates = [
            candidate
            for candidate in session_order
            if candidate != query
            and session_meta[candidate]["framework"]
            != session_meta[query]["framework"]
        ]
        relevant = [
            candidate
            for candidate in candidates
            if session_meta[candidate]["task"] == session_meta[query]["task"]
        ]
        candidate_counts.append(len(candidates))
        relevant_counts.append(len(relevant))
        for candidate in relevant:
            pair = (
                f"{session_meta[query]['framework']} -> "
                f"{session_meta[candidate]['framework']}"
            )
            relevant_framework_pairs[pair] += 1

    manifest = {
        "seed": SEED,
        "inputs": {
            name: {
                "path": str(path),
                "bytes": path.stat().st_size,
                "sha256": sha256_file(path),
            }
            for name, path in INPUTS.items()
        },
        "integrity": {
            "passed": True,
            "source_rows": len(source_rows),
            "precanonical_rows": len(precanonical_rows),
            "canonical_rows": len(canonical_rows),
            "unique_operation_keys": len(source_keys),
            "prediction_framework_matches_source": True,
            "all_values_unit": True,
        },
        "population": {
            "sessions": len(session_order),
            "tasks": len(tasks),
            "frameworks": frameworks,
            "eligible_tasks": len(eligible_tasks),
            "eligible_queries": len(query_sessions),
            "candidate_count_min": min(candidate_counts),
            "candidate_count_median": statistics.median(candidate_counts),
            "candidate_count_max": max(candidate_counts),
            "relevant_count_min": min(relevant_counts),
            "relevant_count_median": statistics.median(relevant_counts),
            "relevant_count_max": max(relevant_counts),
            "relevant_directed_framework_pairs": dict(
                sorted(relevant_framework_pairs.items())
            ),
        },
        "target_oracle_inventory": {
            "field": "fields.prompt",
            "exact_strings": tasks,
            "count": len(tasks),
            "used_in_representations": False,
        },
        "canonical_root_inventory": {
            "exact_strings": sorted(canonical_roots),
            "count": len(canonical_roots),
        },
        "task_bearing_session_ids": sum(
            meta["task"] in session
            for session, meta in session_meta.items()
        ),
        "tie_policy": "permutation-marginalized; session IDs never order ties",
    }

    return {
        "session_order": session_order,
        "session_meta": session_meta,
        "query_sessions": query_sessions,
        "eligible_tasks": eligible_tasks,
        "vectors": vectors,
        "operation_counts": operation_counts,
        "manifest": manifest,
    }


def sparse_cosine(
    left: Counter[str],
    right: Counter[str],
    left_norm: float,
    right_norm: float,
) -> float:
    if left_norm == 0.0 or right_norm == 0.0:
        return 0.0
    if len(left) > len(right):
        left, right = right, left
    dot = sum(value * right.get(feature, 0.0) for feature, value in left.items())
    return dot / (left_norm * right_norm)


def random_pair_score(query_index: int, candidate_index: int) -> float:
    # Only numeric source-order positions enter this deterministic control.
    # Neither the task field nor a task-bearing session identifier enters the
    # seed material.
    payload = f"{SEED}\0{query_index}\0{candidate_index}".encode("ascii")
    value = int.from_bytes(hashlib.sha256(payload).digest()[:8], "big")
    return value / float(2**64)


def grouped_scores(scored: list[tuple[float, bool]]) -> list[tuple[float, int, int]]:
    groups: dict[float, list[int]] = defaultdict(lambda: [0, 0])
    for score, relevant in scored:
        groups[score][0] += 1
        groups[score][1] += int(relevant)
    return [
        (score, groups[score][0], groups[score][1])
        for score in sorted(groups, reverse=True)
    ]


def tie_aware_metrics(scored: list[tuple[float, bool]]) -> dict[str, float | int]:
    if not scored:
        raise ValueError("query has no candidates")
    total_relevant = sum(int(relevant) for _, relevant in scored)
    if total_relevant == 0:
        raise ValueError("eligible query has no relevant candidates")

    groups = grouped_scores(scored)
    ap_numerator = 0.0
    candidates_before = 0
    relevant_before = 0
    expected_mrr: float | None = None

    for _, n, r in groups:
        if r:
            if n == 1:
                ap_numerator += (relevant_before + 1) / (candidates_before + 1)
            else:
                for k in range(1, n + 1):
                    expected_relevant_before_in_group = (
                        (k - 1) * (r - 1) / (n - 1)
                    )
                    ap_numerator += (
                        (r / n)
                        * (
                            relevant_before
                            + 1
                            + expected_relevant_before_in_group
                        )
                        / (candidates_before + k)
                    )
            if expected_mrr is None:
                denominator = math.comb(n, r)
                expected_mrr = sum(
                    (
                        math.comb(n - k, r - 1) / denominator
                        / (candidates_before + k)
                    )
                    for k in range(1, n - r + 2)
                )
        candidates_before += n
        relevant_before += r

    first_n = groups[0][1]
    first_r = groups[0][2]
    return {
        "ap": ap_numerator / total_relevant,
        "top1": first_r / first_n,
        "mrr": expected_mrr if expected_mrr is not None else 0.0,
        "tie_groups": sum(n > 1 for _, n, _ in groups),
        "max_tie_size": max(n for _, n, _ in groups),
    }


def ordinary_metrics(labels: tuple[bool, ...]) -> tuple[float, float, float]:
    relevant_total = sum(labels)
    relevant_seen = 0
    ap_numerator = 0.0
    first_rank: int | None = None
    for rank, relevant in enumerate(labels, 1):
        if relevant:
            relevant_seen += 1
            ap_numerator += relevant_seen / rank
            if first_rank is None:
                first_rank = rank
    return (
        ap_numerator / relevant_total,
        float(labels[0]),
        1.0 / first_rank if first_rank is not None else 0.0,
    )


def self_test_ties() -> None:
    labels = (True, False, True)
    permutations = sorted(set(itertools.permutations(labels)))
    expected = tuple(
        statistics.mean(values)
        for values in zip(*(ordinary_metrics(order) for order in permutations))
    )
    actual = tie_aware_metrics([(0.5, label) for label in labels])
    for key, wanted in zip(("ap", "top1", "mrr"), expected):
        if not math.isclose(float(actual[key]), wanted, rel_tol=1e-12, abs_tol=1e-12):
            raise AssertionError(
                f"tie-aware {key} self-test failed: {actual[key]} != {wanted}"
            )

    untied = tie_aware_metrics([(3.0, False), (2.0, True), (1.0, True)])
    wanted_untied = ordinary_metrics((False, True, True))
    for key, wanted in zip(("ap", "top1", "mrr"), wanted_untied):
        if not math.isclose(float(untied[key]), wanted, abs_tol=1e-12):
            raise AssertionError(f"untied {key} self-test failed")


def pair_auroc(scored: list[tuple[float, bool]]) -> float:
    positives = sum(int(relevant) for _, relevant in scored)
    negatives = len(scored) - positives
    if positives == 0 or negatives == 0:
        raise ValueError("AUROC requires positive and negative candidate pairs")
    groups: dict[float, list[int]] = defaultdict(lambda: [0, 0])
    for score, relevant in scored:
        groups[score][int(relevant)] += 1
    negatives_before = 0
    numerator = 0.0
    for score in sorted(groups):
        negative_count, positive_count = groups[score]
        numerator += positive_count * (
            negatives_before + 0.5 * negative_count
        )
        negatives_before += negative_count
    return numerator / (positives * negatives)


def score_methods(
    dataset: dict[str, Any],
    query_sessions: list[str],
) -> tuple[
    dict[str, dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
    dict[str, dict[str, float]],
]:
    session_order: list[str] = dataset["session_order"]
    session_meta: dict[str, dict[str, str]] = dataset["session_meta"]
    vectors: dict[str, dict[str, Counter[str]]] = dataset["vectors"]
    operation_counts: Counter[str] = dataset["operation_counts"]
    session_indices = {
        session: index for index, session in enumerate(session_order)
    }

    norms: dict[str, dict[str, float]] = {
        method: {
            session: math.sqrt(sum(value * value for value in values.values()))
            for session, values in method_vectors.items()
        }
        for method, method_vectors in vectors.items()
    }

    summaries: dict[str, dict[str, Any]] = {}
    per_query_rows: list[dict[str, Any]] = []
    per_task_rows: list[dict[str, Any]] = []
    per_task_ap: dict[str, dict[str, float]] = {}

    for method in METHODS:
        method_query_rows: list[dict[str, Any]] = []
        all_pairs: list[tuple[float, bool]] = []
        relevant_scores: list[float] = []
        nonrelevant_scores: list[float] = []

        for query in query_sessions:
            candidates = [
                candidate
                for candidate in session_order
                if candidate != query
                and session_meta[candidate]["framework"]
                != session_meta[query]["framework"]
            ]
            scored: list[tuple[float, bool]] = []
            for candidate in candidates:
                if method == "operation_count":
                    score = -abs(
                        math.log1p(operation_counts[query])
                        - math.log1p(operation_counts[candidate])
                    )
                elif method == "random":
                    score = random_pair_score(
                        session_indices[query], session_indices[candidate]
                    )
                else:
                    score = sparse_cosine(
                        vectors[method][query],
                        vectors[method][candidate],
                        norms[method][query],
                        norms[method][candidate],
                    )
                relevant = (
                    session_meta[candidate]["task"]
                    == session_meta[query]["task"]
                )
                scored.append((score, relevant))
                all_pairs.append((score, relevant))
                if relevant:
                    relevant_scores.append(score)
                else:
                    nonrelevant_scores.append(score)

            metrics = tie_aware_metrics(scored)
            query_row = {
                "method": method,
                "query_session": query,
                "task": session_meta[query]["task"],
                "query_framework": session_meta[query]["framework"],
                "candidates": len(scored),
                "relevant_candidates": sum(
                    int(relevant) for _, relevant in scored
                ),
                **metrics,
            }
            method_query_rows.append(query_row)
            per_query_rows.append(query_row)

        task_groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for row in method_query_rows:
            task_groups[row["task"]].append(row)
        task_ap_values: dict[str, float] = {}
        for task in sorted(task_groups):
            rows = task_groups[task]
            task_row = {
                "method": method,
                "task": task,
                "queries": len(rows),
                "mean_ap": statistics.mean(float(row["ap"]) for row in rows),
                "mean_top1": statistics.mean(
                    float(row["top1"]) for row in rows
                ),
                "mean_mrr": statistics.mean(float(row["mrr"]) for row in rows),
            }
            task_ap_values[task] = task_row["mean_ap"]
            per_task_rows.append(task_row)
        per_task_ap[method] = task_ap_values

        summaries[method] = {
            "eligible_queries": len(method_query_rows),
            "eligible_tasks": len(task_groups),
            "task_macro_map": statistics.mean(task_ap_values.values()),
            "query_micro_map": statistics.mean(
                float(row["ap"]) for row in method_query_rows
            ),
            "expected_top1_accuracy": statistics.mean(
                float(row["top1"]) for row in method_query_rows
            ),
            "expected_mrr": statistics.mean(
                float(row["mrr"]) for row in method_query_rows
            ),
            "pair_auroc": pair_auroc(all_pairs),
            "mean_relevant_score": statistics.mean(relevant_scores),
            "mean_nonrelevant_score": statistics.mean(nonrelevant_scores),
            "score_gap": (
                statistics.mean(relevant_scores)
                - statistics.mean(nonrelevant_scores)
            ),
            "queries_with_any_tie": sum(
                int(row["tie_groups"] > 0) for row in method_query_rows
            ),
            "maximum_tie_size": max(
                int(row["max_tie_size"]) for row in method_query_rows
            ),
        }

    return summaries, per_query_rows, per_task_rows, per_task_ap


def percentile(sorted_values: list[float], probability: float) -> float:
    if not sorted_values:
        raise ValueError("cannot take percentile of empty values")
    position = (len(sorted_values) - 1) * probability
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return sorted_values[lower]
    weight = position - lower
    return (
        sorted_values[lower] * (1.0 - weight)
        + sorted_values[upper] * weight
    )


def bootstrap(
    per_task_ap: dict[str, dict[str, float]],
    eligible_tasks: list[str],
) -> dict[str, Any]:
    for method in METHODS:
        if set(per_task_ap[method]) != set(eligible_tasks):
            raise ValueError(f"bootstrap task mismatch for {method}")

    deltas: dict[str, list[float]] = {}
    for name, (left, right) in BOOTSTRAP_COMPARISONS.items():
        deltas[name] = [
            per_task_ap[left][task] - per_task_ap[right][task]
            for task in eligible_tasks
        ]

    rng = random.Random(SEED)
    distributions: dict[str, list[float]] = {
        name: [] for name in BOOTSTRAP_COMPARISONS
    }
    task_count = len(eligible_tasks)
    for _ in range(BOOTSTRAP_REPLICATES):
        sample = [rng.randrange(task_count) for _ in range(task_count)]
        for name, values in deltas.items():
            distributions[name].append(
                sum(values[index] for index in sample) / task_count
            )

    comparisons: dict[str, Any] = {}
    for name, values in deltas.items():
        distribution = sorted(distributions[name])
        comparisons[name] = {
            "left": BOOTSTRAP_COMPARISONS[name][0],
            "right": BOOTSTRAP_COMPARISONS[name][1],
            "point_delta": statistics.mean(values),
            "ci95_percentile": [
                percentile(distribution, 0.025),
                percentile(distribution, 0.975),
            ],
        }
    return {
        "seed": SEED,
        "replicates": BOOTSTRAP_REPLICATES,
        "resampling_unit": "complete eligible CodeTrace task",
        "eligible_tasks": task_count,
        "interval_scope": (
            "conditional topic/task resampling over the fixed candidate library; "
            "not a new-task population interval"
        ),
        "comparisons": comparisons,
    }


def gate_decision(
    summaries: dict[str, dict[str, Any]],
    bootstrap_summary: dict[str, Any],
) -> dict[str, Any]:
    comparisons = bootstrap_summary["comparisons"]

    def lower_positive(name: str) -> bool:
        return comparisons[name]["ci95_percentile"][0] > 0.0

    checks = {
        "canonical_full_beats_action_kind_ci": lower_positive(
            "canonical_full-minus-action_kind"
        ),
        "canonical_full_beats_raw_action_key_ci": lower_positive(
            "canonical_full-minus-raw_action_key"
        ),
        "canonical_full_beats_root_only_ci": lower_positive(
            "canonical_full-minus-canonical_root_only"
        ),
        "root_stripped_beats_action_kind_ci": lower_positive(
            "canonical_root_stripped-minus-action_kind"
        ),
        "root_stripped_beats_raw_action_key_ci": lower_positive(
            "canonical_root_stripped-minus-raw_action_key"
        ),
        "root_stripped_generic_removed_beats_action_kind_ci": lower_positive(
            "canonical_root_stripped_generic_removed-minus-action_kind"
        ),
        "root_stripped_generic_removed_beats_raw_action_key_ci": lower_positive(
            "canonical_root_stripped_generic_removed-minus-raw_action_key"
        ),
        "canonical_full_beats_phase_point": (
            summaries["canonical_full"]["task_macro_map"]
            > summaries["phase"]["task_macro_map"]
        ),
        "canonical_full_beats_operation_count_point": (
            summaries["canonical_full"]["task_macro_map"]
            > summaries["operation_count"]["task_macro_map"]
        ),
    }
    return {
        "automatic_gate_without_independent_review": all(checks.values()),
        "checks": checks,
        "independent_review_required": True,
        "canonicalization_credit_allowed": lower_positive(
            "canonical_full-minus-precanonical_full"
        ),
        "admissible_claim_if_reviewed": (
            "Within CodeTrace, under repeated task-prompt exposure, non-root "
            "canonical operation-path distributions show retrospective "
            "cross-framework representational consistency beyond source-native "
            "action histograms."
        ),
    }


def run_preflight(dataset: dict[str, Any]) -> None:
    query = dataset["query_sessions"][0]
    summaries, per_query, _, _ = score_methods(dataset, [query])
    result = {
        "status": "pass",
        "mode": "preflight",
        "selected_query": query,
        "selected_task": dataset["session_meta"][query]["task"],
        "selected_framework": dataset["session_meta"][query]["framework"],
        "integrity": dataset["manifest"]["integrity"],
        "methods_exercised": list(METHODS),
        "method_metrics": summaries,
        "query_records": per_query,
        "tie_self_test": "pass",
        "full_run_started": False,
    }
    write_json(HERE / "input-manifest.json", dataset["manifest"])
    write_json(HERE / "preflight.json", result)
    print(
        json.dumps(
            {
                "status": "pass",
                "mode": "preflight",
                "query": query,
                "methods": len(METHODS),
            },
            sort_keys=True,
        )
    )


def run_full(dataset: dict[str, Any]) -> None:
    summaries, per_query, per_task, per_task_ap = score_methods(
        dataset, dataset["query_sessions"]
    )
    bootstrap_summary = bootstrap(per_task_ap, dataset["eligible_tasks"])
    decision = gate_decision(summaries, bootstrap_summary)
    result = {
        "status": "pass",
        "mode": "full",
        "analysis_type": "retrospective_descriptive",
        "manifest": dataset["manifest"],
        "method_summaries": summaries,
        "bootstrap": bootstrap_summary,
        "paper_admission": decision,
        "limitations": [
            "The same concrete task prompt was exposed across frameworks.",
            "Task IDs score retrieval but never enter a representation.",
            "This does not validate individual-operation semantic equivalence.",
            "Intervals are conditional on the fixed CodeTrace candidate library.",
        ],
    }
    write_json(HERE / "input-manifest.json", dataset["manifest"])
    write_jsonl(HERE / "per-query.jsonl", per_query)
    write_jsonl(HERE / "per-task.jsonl", per_task)
    write_json(HERE / "bootstrap-summary.json", bootstrap_summary)
    write_json(HERE / "raw-results.json", result)
    print(
        json.dumps(
            {
                "status": "pass",
                "mode": "full",
                "sessions": dataset["manifest"]["population"]["sessions"],
                "eligible_tasks": len(dataset["eligible_tasks"]),
                "eligible_queries": len(dataset["query_sessions"]),
                "canonical_full_task_macro_map": summaries["canonical_full"][
                    "task_macro_map"
                ],
                "root_stripped_task_macro_map": summaries[
                    "canonical_root_stripped"
                ]["task_macro_map"],
                "automatic_gate_without_independent_review": decision[
                    "automatic_gate_without_independent_review"
                ],
            },
            sort_keys=True,
        )
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("preflight", "full"))
    args = parser.parse_args()
    self_test_ties()
    dataset = build_dataset()
    if args.mode == "preflight":
        run_preflight(dataset)
    else:
        run_full(dataset)


if __name__ == "__main__":
    main()
