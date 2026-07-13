#!/usr/bin/env python3
"""Compare Hodoscope, flat, native, and recursive views on iQuest/SWE-bench.

This is the necessary adapter/analysis glue for loop-rq2-02. It deliberately
reuses Hodoscope's released summaries, embeddings, t-SNE path, KDE contrast,
FPS implementation, and oracle. Oracle labels are joined only after complete
rankings have been written.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import math
import resource
import sys
import time
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

import numpy as np
from sklearn.cluster import MiniBatchKMeans
from sklearn.preprocessing import normalize


METHODS = ("hodoscope", "flat", "native", "recursive")
TARGET_GROUP = "iquest"
BOOTSTRAP_RESAMPLES = 10_000


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("preflight", "phase-a", "phase-b", "all"), required=True)
    parser.add_argument("--paper-root", type=Path, required=True)
    parser.add_argument("--data-root", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--seeds", type=int, default=10)
    parser.add_argument("--bootstrap-seed", type=int, default=20260712)
    return parser.parse_args()


def load_official_module(paper_root: Path):
    hodoscope_root = paper_root / "hodoscope"
    sys.path.insert(0, str(hodoscope_root))
    path = paper_root / "experiments" / "run_table2.py"
    spec = importlib.util.spec_from_file_location("hodoscope_run_table2", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load official script: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, ensure_ascii=False) + "\n")


@dataclass
class Corpus:
    records: list[dict[str, Any]]
    X: np.ndarray
    labels: np.ndarray
    type_names: list[str]
    target_label: int


def load_corpus(data_root: Path, official) -> Corpus:
    swe_dir = data_root / "analysis_files" / "swebench"
    if not swe_dir.is_dir():
        raise FileNotFoundError(swe_dir)

    files = [swe_dir / "iquest_samples.hodoscope.json", *sorted(swe_dir.glob("docent_*.hodoscope.json"))]
    groups: dict[str, list[dict[str, Any]]] = {}
    records: list[dict[str, Any]] = []
    for file_path in files:
        doc = official.read_analysis_json(file_path)
        group = "iquest" if file_path.name.startswith("iquest") else doc.get("fields", {}).get("model", file_path.stem)
        group_rows = groups.setdefault(str(group), [])
        for ordinal, summary in enumerate(doc["summaries"]):
            if summary.get("embedding") is None:
                continue
            row = dict(summary)
            row["_analysis_source"] = file_path.name
            row["_within_source_ordinal"] = ordinal
            row["_group"] = str(group)
            row["_action_key"] = (
                file_path.name,
                str(row["trajectory_id"]),
                str(row["turn_id"]),
                ordinal,
            )
            group_rows.append(row)
            records.append(row)

    # Match the official dict and within-group iteration order.
    type_names = list(groups)
    ordered = [row for group in type_names for row in groups[group]]
    X = np.asarray([row["embedding"] for row in ordered], dtype=np.float32)
    if X.ndim != 2 or not np.isfinite(X).all():
        raise ValueError("embeddings must be one finite matrix")
    label_map = {name: index for index, name in enumerate(type_names)}
    labels = np.asarray([label_map[row["_group"]] for row in ordered], dtype=np.int64)
    return Corpus(ordered, X, labels, type_names, label_map[TARGET_GROUP])


def oracle_iquest(record: dict[str, Any]) -> bool:
    text = str(record.get("action_text", "")).lower()
    return "git log" in text or "git show" in text


def subset_indices(corpus: Corpus, seed: int, subsample: bool) -> np.ndarray:
    if not subsample:
        return np.arange(len(corpus.records), dtype=np.int64)
    rng = np.random.RandomState(seed)
    keep = np.zeros(len(corpus.records), dtype=bool)
    for label in range(len(corpus.type_names)):
        group_idx = np.where(corpus.labels == label)[0]
        n_keep = max(1, len(group_idx) // 2)
        keep[rng.choice(group_idx, size=n_keep, replace=False)] = True
    return np.where(keep)[0]


def fit_kmeans(X: np.ndarray, n_clusters: int, seed: int) -> MiniBatchKMeans | None:
    k = min(n_clusters, len(X))
    if k <= 1:
        return None
    model = MiniBatchKMeans(
        n_clusters=k,
        random_state=seed,
        batch_size=1024,
        n_init=10,
    )
    model.fit(X)
    return model


def predict_or_zero(model: MiniBatchKMeans | None, X: np.ndarray) -> np.ndarray:
    if len(X) == 0:
        return np.empty(0, dtype=np.int64)
    if model is None:
        return np.zeros(len(X), dtype=np.int64)
    return model.predict(X).astype(np.int64)


def build_nested_paths(
    X: np.ndarray,
    ref_local: np.ndarray,
    target_local: np.ndarray,
    seed: int,
) -> dict[int, tuple[str, str, str]]:
    X = normalize(X, norm="l2", axis=1)
    paths: dict[int, list[str]] = {int(index): [] for index in np.concatenate([ref_local, target_local])}
    coarse_model = fit_kmeans(X[ref_local], 8, seed)
    ref_coarse = predict_or_zero(coarse_model, X[ref_local])
    target_coarse = predict_or_zero(coarse_model, X[target_local])

    for local, label in zip(ref_local, ref_coarse, strict=True):
        paths[int(local)].append(f"c{int(label)}")
    for local, label in zip(target_local, target_coarse, strict=True):
        paths[int(local)].append(f"c{int(label)}")

    coarse_labels = sorted(set(ref_coarse.tolist()))
    for coarse in coarse_labels:
        ref_members = ref_local[ref_coarse == coarse]
        target_members = target_local[target_coarse == coarse]
        middle_model = fit_kmeans(X[ref_members], 4, seed * 100 + coarse + 1)
        ref_middle = predict_or_zero(middle_model, X[ref_members])
        target_middle = predict_or_zero(middle_model, X[target_members])
        for local, middle in zip(ref_members, ref_middle, strict=True):
            paths[int(local)].append(f"c{coarse}/m{int(middle)}")
        for local, middle in zip(target_members, target_middle, strict=True):
            paths[int(local)].append(f"c{coarse}/m{int(middle)}")

        for middle in sorted(set(ref_middle.tolist())):
            fine_ref = ref_members[ref_middle == middle]
            fine_target = target_members[target_middle == middle]
            fine_model = fit_kmeans(X[fine_ref], 4, seed * 10_000 + coarse * 100 + middle + 1)
            ref_fine = predict_or_zero(fine_model, X[fine_ref])
            target_fine = predict_or_zero(fine_model, X[fine_target])
            for local, fine in zip(fine_ref, ref_fine, strict=True):
                paths[int(local)].append(f"c{coarse}/m{middle}/f{int(fine)}")
            for local, fine in zip(fine_target, target_fine, strict=True):
                paths[int(local)].append(f"c{coarse}/m{middle}/f{int(fine)}")

    bad = [index for index, path in paths.items() if len(path) != 3]
    if bad:
        raise RuntimeError(f"nested assignment incomplete for {len(bad)} actions")
    return {index: tuple(path) for index, path in paths.items()}


def node_contrasts(
    paths: dict[int, tuple[str, ...]],
    ref_local: np.ndarray,
    target_local: np.ndarray,
) -> dict[str, float]:
    ref_counts: Counter[str] = Counter(node for index in ref_local for node in paths[int(index)])
    target_counts: Counter[str] = Counter(node for index in target_local for node in paths[int(index)])
    return {
        node: max(0.0, target_counts[node] / len(target_local) - ref_counts[node] / len(ref_local))
        for node in set(ref_counts) | set(target_counts)
    }


def representation(
    method: str,
    X: np.ndarray,
    records: list[dict[str, Any]],
    labels: np.ndarray,
    target_label: int,
    seed: int,
) -> tuple[np.ndarray, dict[int, tuple[str, ...]]]:
    ref_local = np.where(labels != target_label)[0]
    target_local = np.where(labels == target_label)[0]
    if method in {"flat", "recursive"}:
        nested = build_nested_paths(X, ref_local, target_local, seed)
        paths = nested if method == "recursive" else {index: (path[-1],) for index, path in nested.items()}
    elif method == "native":
        paths = {index: (f"turn:{records[index]['turn_id']}",) for index in range(len(records))}
    else:
        raise ValueError(method)
    contrasts = node_contrasts(paths, ref_local, target_local)
    action_contrast = np.zeros(len(records), dtype=np.float64)
    for index in target_local:
        action_contrast[index] = max(contrasts[node] for node in paths[int(index)])
    return action_contrast, paths


def choose_tie(candidates: np.ndarray, records: list[dict[str, Any]]) -> int:
    return int(min(candidates.tolist(), key=lambda index: records[index]["_action_key"]))


def matched_fps_order(
    X_2d: np.ndarray,
    labels: np.ndarray,
    target_label: int,
    contrast: np.ndarray,
    records: list[dict[str, Any]],
) -> list[int]:
    target = np.where(labels == target_label)[0]
    std = np.std(X_2d, axis=0)
    std[std == 0] = 1.0
    coords = X_2d / std
    selected: list[int] = []
    min_dists = np.full(len(records), np.inf, dtype=np.float64)
    remaining = np.zeros(len(records), dtype=bool)
    remaining[target] = True
    for _ in range(len(target)):
        candidate_idx = np.where(remaining)[0]
        positive = contrast[candidate_idx] > 0
        if not selected:
            scores = contrast[candidate_idx].copy()
        elif positive.any():
            scores = contrast[candidate_idx] * min_dists[candidate_idx]
        else:
            scores = min_dists[candidate_idx].copy()
        best_score = np.max(scores)
        best = choose_tie(candidate_idx[np.flatnonzero(scores == best_score)], records)
        selected.append(best)
        remaining[best] = False
        distances = np.sqrt(np.sum((coords - coords[best]) ** 2, axis=1))
        min_dists = np.minimum(min_dists, distances)
    return selected


def official_order(
    official,
    X_2d: np.ndarray,
    labels: np.ndarray,
    target_label: int,
    records: list[dict[str, Any]],
) -> tuple[list[int], set[int]]:
    bandwidth = official.compute_bandwidth(X_2d)
    densities = official.compute_kde_densities(X_2d, labels, len(np.unique(labels)), bandwidth)
    ranks = official.compute_fps_ranks(
        X_2d,
        labels,
        len(np.unique(labels)),
        point_densities=densities,
        max_per_group=official.MAX_PER_GROUP,
        bandwidth=bandwidth,
    )
    target = np.where(labels == target_label)[0]
    prefix = [index for index in target if ranks[index] != official.UNRANKED_SENTINEL]
    prefix.sort(key=lambda index: (ranks[index], records[index]["_action_key"]))
    tail = [index for index in target if ranks[index] == official.UNRANKED_SENTINEL]
    tail.sort(key=lambda index: records[index]["_action_key"])
    return prefix + tail, set(prefix)


def ranking_rows(
    order: list[int],
    records: list[dict[str, Any]],
    X_2d: np.ndarray,
    contrast: np.ndarray | None,
    paths: dict[int, tuple[str, ...]],
    official_prefix: set[int] | None = None,
) -> list[dict[str, Any]]:
    rows = []
    for rank, index in enumerate(order, 1):
        record = records[index]
        rows.append(
            {
                "rank": rank,
                "action_key": list(record["_action_key"]),
                "analysis_source": record["_analysis_source"],
                "trajectory_id": str(record["trajectory_id"]),
                "turn_id": record["turn_id"],
                "within_source_ordinal": record["_within_source_ordinal"],
                "representation_path": list(paths.get(index, ("hodoscope",))),
                # The official Hodoscope API returns ranks but does not export
                # its per-action normalized density-gap score.  Do not encode
                # a missing score as an observed zero.
                "contrast": None if contrast is None else float(contrast[index]),
                "x": float(X_2d[index, 0]),
                "y": float(X_2d[index, 1]),
                "action_text_characters": len(str(record.get("action_text", ""))),
                "official_prefix": None if official_prefix is None else index in official_prefix,
            }
        )
    return rows


def score_rows(rows: list[dict[str, Any]], record_by_key: dict[tuple[Any, ...], dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    scored = []
    first_hit = None
    chars = 0
    hits20 = 0
    first_in_prefix = None
    for row in rows:
        key = tuple(row["action_key"])
        positive = oracle_iquest(record_by_key[key])
        scored_row = dict(row)
        scored_row["oracle_positive"] = positive
        scored.append(scored_row)
        chars += row["action_text_characters"]
        if row["rank"] <= 20 and positive:
            hits20 += 1
        if positive and first_hit is None:
            first_hit = row["rank"]
            first_in_prefix = row["official_prefix"]
            first_chars = chars
    n_target = len(rows)
    if first_hit is None:
        return scored, {
            "no_hit": True,
            "first_hit_rank": n_target + 1,
            "fraction_inspected": 1.0,
            "characters_inspected": sum(row["action_text_characters"] for row in rows),
            "hits_at_20": hits20,
            "first_hit_in_official_prefix": False,
        }
    return scored, {
        "no_hit": False,
        "first_hit_rank": first_hit,
        "fraction_inspected": first_hit / n_target,
        "characters_inspected": first_chars,
        "hits_at_20": hits20,
        "first_hit_in_official_prefix": first_in_prefix,
    }


def run_seed(
    corpus: Corpus,
    official,
    phase: str,
    seed: int,
    subsample: bool,
    out_dir: Path,
) -> list[dict[str, Any]]:
    started = time.perf_counter()
    subset = subset_indices(corpus, seed, subsample)
    records = [corpus.records[index] for index in subset]
    X = corpus.X[subset]
    labels = corpus.labels[subset]
    target_label = corpus.target_label
    if not np.array_equal(np.unique(labels), np.arange(len(corpus.type_names))):
        raise RuntimeError("paired subset lost a cohort")
    X_2d = official.run_tsne_with_seed(X, labels, seed)
    record_by_key = {tuple(record["_action_key"]): record for record in records}
    target_count = int(np.sum(labels == target_label))
    ref_count = len(labels) - target_count
    oracle_count = sum(oracle_iquest(record) for record, label in zip(records, labels, strict=True) if label == target_label)
    metrics: list[dict[str, Any]] = []
    for method in METHODS:
        method_started = time.perf_counter()
        if method == "hodoscope":
            order, prefix = official_order(official, X_2d, labels, target_label, records)
            contrast = None
            paths: dict[int, tuple[str, ...]] = {}
        else:
            contrast, paths = representation(method, X, records, labels, target_label, seed)
            order = matched_fps_order(X_2d, labels, target_label, contrast, records)
            prefix = None
        rows = ranking_rows(order, records, X_2d, contrast, paths, prefix)
        ranking_path = out_dir / phase / f"seed-{seed:02d}" / f"{method}-ranking.jsonl"
        write_jsonl(ranking_path, rows)
        scored, score = score_rows(rows, record_by_key)
        write_jsonl(ranking_path.with_name(f"{method}-ranking-scored.jsonl"), scored)
        metric = {
            "phase": phase,
            "seed": seed,
            "method": method,
            "subsample": subsample,
            "total_actions": len(records),
            "target_actions": target_count,
            "reference_actions": ref_count,
            "oracle_positive_target_actions": oracle_count,
            "runtime_seconds": time.perf_counter() - method_started,
            "peak_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
            **score,
        }
        metrics.append(metric)
    write_jsonl(out_dir / phase / f"seed-{seed:02d}" / "metrics.jsonl", metrics)
    write_json(
        out_dir / phase / f"seed-{seed:02d}" / "run-summary.json",
        {"elapsed_seconds": time.perf_counter() - started, "metrics": metrics},
    )
    return metrics


def paired_summary(metrics: list[dict[str, Any]], bootstrap_seed: int) -> dict[str, Any]:
    by_method = {method: sorted((row for row in metrics if row["method"] == method), key=lambda row: row["seed"]) for method in METHODS}
    recursive = by_method["recursive"]
    rng = np.random.RandomState(bootstrap_seed)
    comparisons = {}
    for baseline in ("flat", "native", "hodoscope"):
        pairs = list(zip(recursive, by_method[baseline], strict=True))
        deltas = np.asarray([a["first_hit_rank"] - b["first_hit_rank"] for a, b in pairs], dtype=float)
        samples = np.asarray([np.mean(rng.choice(deltas, size=len(deltas), replace=True)) for _ in range(BOOTSTRAP_RESAMPLES)])
        comparisons[baseline] = {
            "deltas": deltas.tolist(),
            "mean_delta": float(np.mean(deltas)),
            "win_rate": float(np.mean(deltas < 0)),
            "bootstrap_95": [float(np.quantile(samples, 0.025)), float(np.quantile(samples, 0.975))],
            "positive_rule_pass": bool(np.mean(deltas < 0) >= 0.8 and np.mean(deltas) < 0 and np.quantile(samples, 0.975) < 0),
        }
    return {"comparisons": comparisons, "recursive_positive_against_all": all(item["positive_rule_pass"] for item in comparisons.values())}


def main() -> int:
    args = parse_args()
    official = load_official_module(args.paper_root)
    corpus = load_corpus(args.data_root, official)
    total_oracle = sum(oracle_iquest(record) for record in corpus.records if record["_group"] == TARGET_GROUP)
    inventory = {
        "total_actions": len(corpus.records),
        "target_actions": int(np.sum(corpus.labels == corpus.target_label)),
        "reference_actions": int(np.sum(corpus.labels != corpus.target_label)),
        "oracle_positive_target_actions": total_oracle,
        "groups": {name: int(np.sum(corpus.labels == index)) for index, name in enumerate(corpus.type_names)},
        "embedding_shape": list(corpus.X.shape),
    }
    write_json(args.out_dir / "inventory.json", inventory)
    if inventory["total_actions"] != 11_855 or inventory["target_actions"] != 4_006 or total_oracle != 132:
        raise RuntimeError(f"official inventory mismatch: {inventory}")

    phases: list[tuple[str, bool, range]] = []
    if args.mode == "preflight":
        phases.append(("preflight", True, range(1, 2)))
    if args.mode in {"phase-a", "all"}:
        phases.append(("phase-a", True, range(1, args.seeds + 1)))
    if args.mode in {"phase-b", "all"}:
        phases.append(("phase-b", False, range(1, args.seeds + 1)))

    all_metrics = []
    for phase, subsample, seeds in phases:
        phase_metrics = []
        for seed in seeds:
            phase_metrics.extend(run_seed(corpus, official, phase, seed, subsample, args.out_dir))
        all_metrics.extend(phase_metrics)
        if len(list(seeds)) > 1:
            write_json(args.out_dir / phase / "paired-summary.json", paired_summary(phase_metrics, args.bootstrap_seed))
    write_jsonl(args.out_dir / "metrics.jsonl", all_metrics)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
