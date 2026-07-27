#!/usr/bin/env python3
"""Mine cross-stratum invariants from the frozen final-HEAD analyses.

This is a descriptive external-validity audit.  It never treats the sparse
project×vendor grid as a randomized vendor comparison, and it keeps public RQ6
task traces separate from the six natural-workspace cases.
"""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import importlib.util
import json
import math
import statistics
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable, Sequence

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy.optimize import minimize, minimize_scalar
from scipy.special import zeta
from scipy.stats import norm, spearmanr


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
BUILD = ROOT / "docs/tmp/build-and-evaluate"
FINAL = BUILD / "rq1-rq4-recompute-final"
BEHAVIOR = BUILD / "toolcall-behavior-20260726"
PROFILE = BUILD / "toolcall-profile-20260726"
SESSION = BUILD / "session-dynamics-20260726"
USER_QUESTIONS = BUILD / "user-questions-20260726"
RQ_EXTENSIONS = BUILD / "rq-extensions-final-20260726"
RQ2_CROSS = BUILD / "rq2-crosscase-20260726"
RQ6 = (
    ROOT
    / "docs/tmp/bootstrap/step-0002-20260722T182000-0700/"
    "experiment-rq6-external-boundary/full"
)
RQ6_CODE = ROOT / "agentvis/research/rq6_external_boundary.py"

PROJECTS = [
    "agentsight",
    "ActPlane",
    "bpf-developer-tutorial",
    "eunomia.dev",
    "agentskill-observability-paper",
    "academic-writing-skills",
]
VENDORS = ["claude", "codex", "gemini"]
PAIRED_PROJECTS = ["agentsight", "ActPlane", "eunomia.dev"]

METRICS: dict[str, dict[str, Any]] = {
    "artifact_reuse_access_share": {
        "label": "Stable-identity access reuse",
        "kind": "share",
        "anchor": 0.5,
        "source": "final-HEAD RQ4 accesses",
    },
    "top10_session_call_share": {
        "label": "Top-10% session call concentration",
        "kind": "share",
        "anchor": 0.1,
        "source": "toolcall-behavior/session_metrics",
    },
    "path_locality_share": {
        "label": "Within-session path locality",
        "kind": "share",
        "anchor": 0.5,
        "source": "final-HEAD RQ4 accesses",
    },
    "same_prompt_repeat_read_share": {
        "label": "Same-prompt repeated identity reads",
        "kind": "share",
        "anchor": 0.5,
        "source": "toolcall-behavior/repeated_reads",
    },
    "shell_share": {
        "label": "Shell tool share",
        "kind": "share",
        "anchor": 0.5,
        "source": "toolcall-behavior/tool_family_distribution",
    },
    "shell_shell_bigram_share": {
        "label": "Shell→shell bigram share",
        "kind": "share",
        "anchor": 0.5,
        "source": "toolcall-behavior/markov_transitions",
    },
    "zero_decisive_validation_session_share": {
        "label": "Sessions with zero decisive validation",
        "kind": "share",
        "anchor": 0.5,
        "source": "final-HEAD RQ2 trajectory",
    },
    "startup_extended_excess_median": {
        "label": "Startup extended-proxy excess (first 10 − calls 11–20)",
        "kind": "signed",
        "anchor": 0.0,
        "source": "session-dynamics/startup_sessions",
    },
    "late_reread_delta_median": {
        "label": "Late-minus-early reread share (median)",
        "kind": "signed",
        "anchor": 0.0,
        "source": "session-dynamics/drift_paired",
    },
    "dormant_revival_transition_share": {
        "label": "Dormant revival among repeat touches",
        "kind": "share",
        "anchor": 0.5,
        "source": "final-HEAD RQ4 accesses",
    },
    "decisive_failure_rate": {
        "label": "Decisive Tool-call failure rate",
        "kind": "share",
        "anchor": 0.5,
        "source": "toolcall-behavior/tool_family_distribution",
    },
    "bigram_entropy_bits": {
        "label": "Tool-family bigram entropy",
        "kind": "positive",
        "anchor": 0.0,
        "source": "toolcall-behavior/markov_transitions",
    },
    "shell_burst_p90": {
        "label": "Same-prompt shell-burst p90",
        "kind": "positive",
        "anchor": 0.0,
        "source": "final-HEAD events",
    },
    "module_return_call_share": {
        "label": "Within-session module-return call share",
        "kind": "share",
        "anchor": 0.0,
        "source": "final-HEAD RQ4 accesses",
    },
    "session_top_path_share_median": {
        "label": "Per-session top-path share (median)",
        "kind": "share",
        "anchor": 0.1,
        "source": "final-HEAD RQ4 accesses",
    },
}

EXTERNAL_MAP = {
    "path_locality_share": "path_locality_excess",
    "shell_share": "shell_share",
    "late_reread_delta_median": "late_path_reread_delta_median",
    "module_return_call_share": "module_return_call_share",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=HERE)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--preflight", action="store_true")
    mode.add_argument("--full", action="store_true")
    return parser.parse_args()


def canonical_project(value: str) -> str:
    return "eunomia.dev" if value == "eunomia-dev" else value


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def write_csv(path: Path, rows: list[dict[str, Any]], fields: Sequence[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fields is None:
        fields = list(rows[0]) if rows else []
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(fields), extrasaction="raise", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def as_float(value: Any) -> float | None:
    if value in {"", None}:
        return None
    number = float(value)
    return number if math.isfinite(number) else None


def median(values: Iterable[float]) -> float | None:
    clean = [float(value) for value in values if value is not None and math.isfinite(float(value))]
    return float(statistics.median(clean)) if clean else None


def percentile(values: Sequence[float], q: float) -> float | None:
    if not values:
        return None
    return float(np.quantile(np.asarray(values, dtype=float), q))


def safe_div(numerator: float, denominator: float) -> float | None:
    return numerator / denominator if denominator else None


def top_fraction_share(values: Sequence[int], fraction: float = 0.1) -> float | None:
    if not values or sum(values) == 0:
        return None
    take = max(1, math.ceil(len(values) * fraction))
    return sum(sorted(values, reverse=True)[:take]) / sum(values)


def vendor_from_session(session_id: str) -> str:
    return session_id.split(":", 1)[0].lower()


def metric_row(
    metric: str,
    project: str,
    vendor: str,
    value: float | None,
    numerator: float | int | None,
    denominator: float | int | None,
    n_units: int,
    eligible: bool,
    reason: str,
    contrast_value: float | None = None,
    contrast_definition: str = "N/A",
    decisive_coverage: float | None = None,
    recognized_test_session_coverage: float | None = None,
    decisive_test_status_coverage: float | None = None,
    independent_worktrees: int | None = None,
) -> dict[str, Any]:
    return {
        "metric": metric,
        "metric_label": METRICS[metric]["label"],
        "project": project,
        "vendor": vendor,
        "value": "" if value is None else value,
        "numerator": "" if numerator is None else numerator,
        "denominator": "" if denominator is None else denominator,
        "n_units": n_units,
        "eligible": eligible,
        "eligibility_reason": reason,
        "contrast_value": "" if contrast_value is None else contrast_value,
        "contrast_definition": contrast_definition,
        "decisive_coverage": "" if decisive_coverage is None else decisive_coverage,
        "recognized_test_session_coverage": (
            "" if recognized_test_session_coverage is None else recognized_test_session_coverage
        ),
        "decisive_test_status_coverage": (
            "" if decisive_test_status_coverage is None else decisive_test_status_coverage
        ),
        "independent_worktrees": "" if independent_worktrees is None else independent_worktrees,
        "source": METRICS[metric]["source"],
    }


def load_behavior_metrics(
    selected_projects: set[str],
) -> tuple[dict[tuple[str, str, str], dict[str, Any]], dict[tuple[str, str], list[int]]]:
    cells: dict[tuple[str, str, str], dict[str, Any]] = {}
    session_counts: dict[tuple[str, str], list[int]] = defaultdict(list)

    session_rows = read_csv(BEHAVIOR / "session_metrics.csv")
    for row in session_rows:
        project = canonical_project(row["project"])
        if project not in selected_projects:
            continue
        key = (project, row["vendor"])
        session_counts[key].append(int(row["calls"]))

    pace = {
        (canonical_project(row["project"]), row["vendor"]): row
        for row in read_csv(BEHAVIOR / "session_pace_summary.csv")
        if row["stratum_type"] == "project_vendor"
    }
    family_groups: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in read_csv(BEHAVIOR / "tool_family_distribution.csv"):
        if row["stratum_type"] == "project_vendor":
            family_groups[(canonical_project(row["project"]), row["vendor"])].append(row)

    repeat_lookup: dict[tuple[str, str], dict[str, str]] = {}
    for row in read_csv(BEHAVIOR / "repeated_reads.csv"):
        if (
            row["stratum_type"] == "project_vendor"
            and row["analysis_unit"] == "source_stream"
            and row["prompt_scope"] == "same_prompt"
            and row["evidence_source"] == "artifact_actions"
            and row["identity_basis"] == "registered_artifact_identity"
        ):
            repeat_lookup[(canonical_project(row["project"]), row["vendor"])] = row

    transition_groups: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in read_csv(BEHAVIOR / "markov_transitions.csv"):
        if (
            row["stratum_type"] == "project_vendor"
            and row["sequence_scope"] == "same_prompt"
            and row["sequence_granularity"] == "tool_family"
        ):
            transition_groups[(canonical_project(row["project"]), row["vendor"])].append(row)

    for project in selected_projects:
        for vendor in VENDORS:
            key = (project, vendor)
            calls = session_counts.get(key, [])
            pace_row = pace.get(key)
            value = as_float(pace_row["top_10pct_sessions_call_share"]) if pace_row else None
            eligible = len(calls) >= 10
            cells[(project, vendor, "top10_session_call_share")] = metric_row(
                "top10_session_call_share",
                project,
                vendor,
                value,
                None,
                sum(calls) if calls else None,
                len(calls),
                eligible,
                ">=10 sessions" if eligible else f"{len(calls)} sessions; need 10",
            )

            families = family_groups.get(key, [])
            total_calls = sum(int(row["calls"]) for row in families)
            shell_calls = sum(int(row["calls"]) for row in families if row["tool_family"] == "shell")
            decisive = sum(int(row["ok"]) + int(row["fail"]) for row in families)
            failures = sum(int(row["fail"]) for row in families)
            eligible_calls = total_calls >= 100 and len(calls) >= 10
            cells[(project, vendor, "shell_share")] = metric_row(
                "shell_share",
                project,
                vendor,
                safe_div(shell_calls, total_calls),
                shell_calls,
                total_calls,
                len(calls),
                eligible_calls,
                ">=100 calls and >=10 sessions"
                if eligible_calls
                else f"{total_calls} calls/{len(calls)} sessions; need 100/10",
            )
            eligible_failure = decisive >= 100 and len(calls) >= 10
            cells[(project, vendor, "decisive_failure_rate")] = metric_row(
                "decisive_failure_rate",
                project,
                vendor,
                safe_div(failures, decisive),
                failures,
                decisive,
                len(calls),
                eligible_failure,
                ">=100 decisive calls and >=10 sessions"
                if eligible_failure
                else f"{decisive} decisive calls/{len(calls)} sessions; need 100/10",
                decisive_coverage=safe_div(decisive, total_calls),
            )

            repeated = repeat_lookup.get(key)
            reads = int(repeated["read_instances"]) if repeated else 0
            repeats = int(repeated["repeat_read_instances"]) if repeated else 0
            eligible_reads = reads >= 50 and len(calls) >= 10
            cells[(project, vendor, "same_prompt_repeat_read_share")] = metric_row(
                "same_prompt_repeat_read_share",
                project,
                vendor,
                safe_div(repeats, reads),
                repeats,
                reads,
                len(calls),
                eligible_reads,
                ">=50 reads and >=10 sessions"
                if eligible_reads
                else f"{reads} reads/{len(calls)} sessions; need 50/10",
            )

            transitions = transition_groups.get(key, [])
            transition_n = sum(int(row["count"]) for row in transitions)
            shell_shell = sum(
                int(row["count"])
                for row in transitions
                if row["from_family"] == "shell" and row["to_family"] == "shell"
            )
            entropy = 0.0
            if transition_n:
                for row in transitions:
                    probability = int(row["count"]) / transition_n
                    entropy -= probability * math.log2(probability)
                nonzero_bins = sum(int(row["count"]) > 0 for row in transitions)
                entropy += (nonzero_bins - 1) / (2 * transition_n * math.log(2))
            eligible_transitions = transition_n >= 100 and len(calls) >= 10
            origin_shell = sum(int(row["count"]) for row in transitions if row["from_family"] == "shell")
            destination_shell = sum(int(row["count"]) for row in transitions if row["to_family"] == "shell")
            independence = safe_div(origin_shell * destination_shell, transition_n * transition_n)
            shell_shell_share = safe_div(shell_shell, transition_n)
            cells[(project, vendor, "shell_shell_bigram_share")] = metric_row(
                "shell_shell_bigram_share",
                project,
                vendor,
                shell_shell_share,
                shell_shell,
                transition_n,
                len(calls),
                eligible_transitions,
                ">=100 same-prompt bigrams and >=10 sessions"
                if eligible_transitions
                else f"{transition_n} bigrams/{len(calls)} sessions; need 100/10",
                None
                if shell_shell_share is None or independence is None
                else shell_shell_share - independence,
                "observed shell→shell share minus origin×destination marginal expectation",
            )
            cells[(project, vendor, "bigram_entropy_bits")] = metric_row(
                "bigram_entropy_bits",
                project,
                vendor,
                entropy if transition_n else None,
                None,
                transition_n,
                len(calls),
                eligible_transitions,
                ">=100 same-prompt bigrams and >=10 sessions"
                if eligible_transitions
                else f"{transition_n} bigrams/{len(calls)} sessions; need 100/10",
            )
    return cells, session_counts


def load_startup_and_drift(
    cells: dict[tuple[str, str, str], dict[str, Any]],
    selected_projects: set[str],
) -> None:
    startup_prefixes: dict[tuple[str, str, str], dict[int, float]] = defaultdict(dict)
    for row in read_csv(SESSION / "raw/startup_sessions.csv"):
        project = canonical_project(row["project"])
        if project not in selected_projects or row["n_prefix"] not in {"10", "20"} or row["complete_prefix"] != "True":
            continue
        value = as_float(row["extended_share"])
        if value is not None:
            startup_prefixes[(project, row["vendor"], row["session_id"])][int(row["n_prefix"])] = value
    startup_values: dict[tuple[str, str], list[float]] = defaultdict(list)
    for (project, vendor, _session), prefixes in startup_prefixes.items():
        if 10 in prefixes and 20 in prefixes:
            calls_11_to_20_share = 2 * prefixes[20] - prefixes[10]
            startup_values[(project, vendor)].append(prefixes[10] - calls_11_to_20_share)

    drift_values: dict[tuple[str, str], list[float]] = defaultdict(list)
    for row in read_csv(SESSION / "raw/drift_paired.csv"):
        project = canonical_project(row["project"])
        if project not in selected_projects:
            continue
        value = as_float(row["repeat_read_share_late_minus_early"])
        if value is not None:
            drift_values[(project, row["vendor"])].append(value)

    for project in selected_projects:
        for vendor in VENDORS:
            key = (project, vendor)
            values = startup_values.get(key, [])
            eligible = len(values) >= 10
            cells[(project, vendor, "startup_extended_excess_median")] = metric_row(
                "startup_extended_excess_median",
                project,
                vendor,
                median(values),
                None,
                len(values),
                len(values),
                eligible,
                ">=10 complete 20-call matched prefixes"
                if eligible
                else f"{len(values)} complete 20-call prefixes; need 10",
                median(values),
                "first-10 minus calls-11–20 extended orientation share",
            )
            values = drift_values.get(key, [])
            eligible = len(values) >= 10
            cells[(project, vendor, "late_reread_delta_median")] = metric_row(
                "late_reread_delta_median",
                project,
                vendor,
                median(values),
                None,
                len(values),
                len(values),
                eligible,
                ">=10 long sessions with paired reread shares" if eligible else f"{len(values)} paired sessions; need 10",
                median(values),
                "late-tertile minus early-tertile resolved-identity reread share",
            )


def load_zero_validation(
    cells: dict[tuple[str, str, str], dict[str, Any]],
    selected_projects: set[str],
) -> None:
    sessions: dict[tuple[str, str], set[str]] = defaultdict(set)
    validated: dict[tuple[str, str], set[str]] = defaultdict(set)
    recognized: dict[tuple[str, str], set[str]] = defaultdict(set)
    test_status_counts: dict[tuple[str, str], Counter[str]] = defaultdict(Counter)
    with (FINAL / "rq2/raw/rq2-trajectory.csv").open(newline="", encoding="utf-8") as stream:
        for row in csv.DictReader(stream):
            project = canonical_project(row["project"])
            if project not in selected_projects:
                continue
            key = (project, row["vendor"])
            sessions[key].add(row["session_id"])
            if row["effect"] == "test":
                recognized[key].add(row["session_id"])
                test_status_counts[key][row["status"] or "missing"] += 1
                if row["status"] in {"ok", "fail"}:
                    validated[key].add(row["session_id"])
    for project in selected_projects:
        for vendor in VENDORS:
            key = (project, vendor)
            total = len(sessions.get(key, set()))
            zero = total - len(validated.get(key, set()))
            statuses = test_status_counts[key]
            test_total = sum(statuses.values())
            decisive_test = statuses["ok"] + statuses["fail"]
            eligible = total >= 10
            cells[(project, vendor, "zero_decisive_validation_session_share")] = metric_row(
                "zero_decisive_validation_session_share",
                project,
                vendor,
                safe_div(zero, total),
                zero,
                total,
                total,
                eligible,
                ">=10 sessions" if eligible else f"{total} sessions; need 10",
                recognized_test_session_coverage=safe_div(len(recognized.get(key, set())), total),
                decisive_test_status_coverage=safe_div(decisive_test, test_total),
            )


def load_path_metrics(
    cells: dict[tuple[str, str, str], dict[str, Any]],
    selected_projects: set[str],
) -> tuple[
    dict[tuple[str, str], list[tuple[str, float]]],
    dict[tuple[str, str], dict[str, float | int | None]],
]:
    calls: dict[tuple[str, str, str], dict[str, Any]] = {}
    with (FINAL / "rq4/raw/rq4-accesses.csv").open(newline="", encoding="utf-8") as stream:
        for row in csv.DictReader(stream):
            project = canonical_project(row["project"])
            if project not in selected_projects:
                continue
            key = (project, row["worktree_id"], row["event_id"])
            call = calls.setdefault(
                key,
                {
                    "project": project,
                    "worktree": row["worktree_id"],
                    "event_id": row["event_id"],
                    "event_index": int(row["event_index"]),
                    "session_id": row["session_id"],
                    "vendor": vendor_from_session(row["session_id"]),
                    "paths": set(),
                    "modules": set(),
                    "path_operations": defaultdict(set),
                    "artifacts": set(),
                },
            )
            path = row["path"].strip()
            if path:
                call["paths"].add(path)
                call["modules"].add(row["module"] or "repo-root-files")
                call["path_operations"][path].add(row["operation"])
            if row["artifact_id"]:
                call["artifacts"].add(row["artifact_id"])

    authoritative_revivals = {
        (
            canonical_project(row["project"]),
            row["worktree_id"],
            int(row["revival_event_index"]),
            row["artifact_id"],
        )
        for row in read_csv(RQ_EXTENSIONS / "rq1-revivals.csv")
        if row["variant"] == "action_gap_gt_100"
        and canonical_project(row["project"]) in selected_projects
    }

    sessions: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    worktrees: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for call in calls.values():
        sessions[(call["project"], call["session_id"])].append(call)
        worktrees[(call["project"], call["worktree"])].append(call)
    for sequence in sessions.values():
        sequence.sort(key=lambda call: (call["event_index"], call["event_id"]))
    for sequence in worktrees.values():
        sequence.sort(key=lambda call: (call["event_index"], call["event_id"]))

    transition_counts: dict[tuple[str, str], Counter[str]] = defaultdict(Counter)
    return_counts: dict[tuple[str, str], Counter[str]] = defaultdict(Counter)
    path_reuse_counts: dict[tuple[str, str], Counter[str]] = defaultdict(Counter)
    path_read_counts: dict[tuple[str, str], Counter[str]] = defaultdict(Counter)
    top_path_values: dict[tuple[str, str], list[float]] = defaultdict(list)
    top_path_excess_values: dict[tuple[str, str], list[float]] = defaultdict(list)
    target_count_distributions: dict[tuple[str, str], list[tuple[str, float]]] = defaultdict(list)
    cell_sessions: dict[tuple[str, str], set[str]] = defaultdict(set)
    cell_worktrees: dict[tuple[str, str], set[str]] = defaultdict(set)
    artifact_sessions: dict[tuple[str, str], set[str]] = defaultdict(set)
    repeat_touch_sessions: dict[tuple[str, str], set[str]] = defaultdict(set)
    path_call_sessions: dict[tuple[str, str], set[str]] = defaultdict(set)
    path_transition_sessions: dict[tuple[str, str], set[str]] = defaultdict(set)
    for call in calls.values():
        cell = (call["project"], call["vendor"])
        cell_sessions[cell].add(call["session_id"])
        cell_worktrees[cell].add(call["worktree"])
        if call["artifacts"]:
            artifact_sessions[cell].add(call["session_id"])
        if call["paths"]:
            path_call_sessions[cell].add(call["session_id"])

    for (project, _session), sequence in sessions.items():
        path_calls = [call for call in sequence if call["paths"]]
        for previous, current in zip(path_calls, path_calls[1:]):
            if previous["vendor"] != current["vendor"]:
                continue
            cell = (project, current["vendor"])
            transition_counts[cell]["total"] += 1
            path_transition_sessions[cell].add(current["session_id"])
            if previous["paths"] & current["paths"]:
                transition_counts[cell]["same_path"] += 1
            elif previous["modules"] & current["modules"]:
                transition_counts[cell]["same_module_only"] += 1
            else:
                transition_counts[cell]["cross_module"] += 1

        module_state: dict[str, dict[str, Any]] = {}
        for call in path_calls:
            cell = (project, call["vendor"])
            present = set(call["modules"])
            returned = False
            for module_name in module_state:
                if module_name not in present:
                    module_state[module_name]["left"] = True
            for module_name in present:
                previous = module_state.get(module_name)
                if previous and previous["left"]:
                    returned = True
                module_state[module_name] = {"index": call["event_index"], "left": False}
            return_counts[cell]["path_calls"] += 1
            return_counts[cell]["return_calls"] += returned

        seen_paths: set[str] = set()
        seen_read_paths: set[str] = set()
        weights: Counter[str] = Counter()
        for call in path_calls:
            cell = (project, call["vendor"])
            for path in call["paths"]:
                path_reuse_counts[cell]["instances"] += 1
                path_reuse_counts[cell]["reused"] += path in seen_paths
                if "read" in call["path_operations"][path]:
                    path_read_counts[cell]["instances"] += 1
                    path_read_counts[cell]["repeated"] += path in seen_read_paths
                    seen_read_paths.add(path)
                seen_paths.add(path)
                weights[path] += 1
        if weights:
            vendor = sequence[0]["vendor"]
            # Native root sessions are vendor-homogeneous in the frozen source.
            if all(call["vendor"] == vendor for call in sequence):
                cell = (project, vendor)
                top_path_values[cell].append(max(weights.values()) / sum(weights.values()))
                top_path_excess_values[cell].append(
                    max(weights.values()) / sum(weights.values()) - 1 / len(weights)
                )
                target_count_distributions[cell].extend(
                    (str(_session), float(value)) for value in weights.values()
                )

    touch_counts: dict[tuple[str, str], Counter[str]] = defaultdict(Counter)
    for (project, _worktree), sequence in worktrees.items():
        histories: dict[str, tuple[int, str]] = {}
        for call in sequence:
            cell = (project, call["vendor"])
            for artifact in call["artifacts"]:
                touch_counts[cell]["touches"] += 1
                previous = histories.get(artifact)
                if previous:
                    touch_counts[cell]["reused"] += 1
                    touch_counts[cell]["repeat_transitions"] += 1
                    repeat_touch_sessions[cell].add(call["session_id"])
                    if (
                        project,
                        call["worktree"],
                        call["event_index"],
                        artifact,
                    ) in authoritative_revivals:
                        touch_counts[cell]["revivals"] += 1
                histories[artifact] = (call["event_index"], call["session_id"])

    external_local: dict[tuple[str, str], dict[str, float | int | None]] = {}
    for project in selected_projects:
        for vendor in VENDORS:
            key = (project, vendor)
            sessions_n = len(cell_sessions.get(key, set()))
            worktrees_n = len(cell_worktrees.get(key, set()))
            touches = touch_counts[key]
            contributing_sessions = len(artifact_sessions.get(key, set()))
            eligible = touches["touches"] >= 100 and contributing_sessions >= 10
            cells[(project, vendor, "artifact_reuse_access_share")] = metric_row(
                "artifact_reuse_access_share",
                project,
                vendor,
                safe_div(touches["reused"], touches["touches"]),
                touches["reused"],
                touches["touches"],
                contributing_sessions,
                eligible,
                ">=100 stable-identity touches and >=10 denominator-contributing sessions"
                if eligible
                else f"{touches['touches']} touches/{contributing_sessions} contributing sessions; need 100/10",
                independent_worktrees=worktrees_n,
            )
            repeats = touches["repeat_transitions"]
            contributing_sessions = len(repeat_touch_sessions.get(key, set()))
            eligible = repeats >= 100 and contributing_sessions >= 10
            cells[(project, vendor, "dormant_revival_transition_share")] = metric_row(
                "dormant_revival_transition_share",
                project,
                vendor,
                safe_div(touches["revivals"], repeats),
                touches["revivals"],
                repeats,
                contributing_sessions,
                eligible,
                ">=100 repeat-touch transitions and >=10 denominator-contributing sessions"
                if eligible
                else f"{repeats} repeat transitions/{contributing_sessions} contributing sessions; need 100/10",
                independent_worktrees=worktrees_n,
            )
            transitions = transition_counts[key]
            local_transitions = transitions["same_path"] + transitions["same_module_only"]
            contributing_sessions = len(path_transition_sessions.get(key, set()))
            eligible = transitions["total"] >= 100 and contributing_sessions >= 10
            locality = safe_div(local_transitions, transitions["total"])
            cross_share = safe_div(transitions["cross_module"], transitions["total"])
            cells[(project, vendor, "path_locality_share")] = metric_row(
                "path_locality_share",
                project,
                vendor,
                locality,
                local_transitions,
                transitions["total"],
                contributing_sessions,
                eligible,
                ">=100 within-session path transitions and >=10 denominator-contributing sessions"
                if eligible
                else f"{transitions['total']} transitions/{contributing_sessions} contributing sessions; need 100/10",
                None if locality is None or cross_share is None else locality - cross_share,
                "(same exact path + same-module-only) share minus cross-module share",
            )
            returns = return_counts[key]
            contributing_sessions = len(path_call_sessions.get(key, set()))
            eligible = returns["path_calls"] >= 100 and contributing_sessions >= 10
            cells[(project, vendor, "module_return_call_share")] = metric_row(
                "module_return_call_share",
                project,
                vendor,
                safe_div(returns["return_calls"], returns["path_calls"]),
                returns["return_calls"],
                returns["path_calls"],
                contributing_sessions,
                eligible,
                ">=100 path calls and >=10 denominator-contributing sessions"
                if eligible
                else f"{returns['path_calls']} path calls/{contributing_sessions} contributing sessions; need 100/10",
            )
            tops = top_path_values.get(key, [])
            target_observations = target_count_distributions.get(key, [])
            target_accesses = sum(value for _, value in target_observations)
            eligible = len(tops) >= 10 and target_accesses >= 100
            cells[(project, vendor, "session_top_path_share_median")] = metric_row(
                "session_top_path_share_median",
                project,
                vendor,
                median(tops),
                None,
                len(tops),
                len(tops),
                eligible,
                ">=10 path-bearing sessions and >=100 path accesses"
                if eligible
                else f"{len(tops)} sessions/{int(target_accesses)} accesses",
            )
            reuse = path_reuse_counts[key]
            reread = path_read_counts[key]
            external_local[key] = {
                "path_locality_share": locality,
                "path_locality_n": transitions["total"],
                "same_path_share": safe_div(transitions["same_path"], transitions["total"]),
                "same_module_only_share": safe_div(transitions["same_module_only"], transitions["total"]),
                "cross_module_share": cross_share,
                "module_return_call_share": safe_div(returns["return_calls"], returns["path_calls"]),
                "module_return_n": returns["path_calls"],
                "path_reuse_share": safe_div(reuse["reused"], reuse["instances"]),
                "path_reuse_n": reuse["instances"],
                "repeat_path_read_share": safe_div(reread["repeated"], reread["instances"]),
                "repeat_path_read_n": reread["instances"],
                "unit_top_path_share_median": median(tops),
                "unit_top_path_n": len(tops),
            }
    return target_count_distributions, external_local


def import_module(path: Path, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def load_shell_bursts(
    cells: dict[tuple[str, str, str], dict[str, Any]],
    selected_projects: set[str],
) -> tuple[dict[tuple[str, str], list[tuple[str, float]]], list[Path]]:
    behavior_code = import_module(BEHAVIOR / "analyze_toolcalls.py", "frozen_toolcall_behavior")
    burst_values: dict[tuple[str, str], list[tuple[str, float]]] = defaultdict(list)
    cell_sessions: dict[tuple[str, str], set[str]] = defaultdict(set)
    decisive_sessions: dict[tuple[str, str], set[str]] = defaultdict(set)
    read_sessions: dict[tuple[str, str], set[str]] = defaultdict(set)
    bigram_sessions: dict[tuple[str, str], set[str]] = defaultdict(set)
    shell_run_sessions: dict[tuple[str, str], set[str]] = defaultdict(set)
    input_files: list[Path] = []
    for path in behavior_code.discover_event_files(FINAL / "rq1-raw/events"):
        payload = behavior_code.load_json(path)
        project = canonical_project(str(payload["repository"]))
        if project not in selected_projects:
            continue
        input_files.append(path)
        streams: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for event in payload.get("events") or []:
            event["_family_invariance"] = behavior_code.tool_family(event)
            streams[event["source_stream_id"]].append(event)
            cell_sessions[(project, event["vendor"])].add(event["session_id"])
            if event.get("status") in {"ok", "fail"}:
                decisive_sessions[(project, event["vendor"])].add(event["session_id"])
            if any(
                action.get("access") == "read" and action.get("artifact_id")
                for action in event.get("actions") or []
            ):
                read_sessions[(project, event["vendor"])].add(event["session_id"])
        for sequence in streams.values():
            sequence.sort(key=behavior_code.event_sort_key)
            vendor = sequence[0]["vendor"]
            segments: list[list[dict[str, Any]]] = []
            for event in sequence:
                if not segments or segments[-1][-1].get("prompt_index") != event.get("prompt_index"):
                    segments.append([event])
                else:
                    segments[-1].append(event)
            for segment in segments:
                families = [event["_family_invariance"] for event in segment]
                if len(families) >= 2:
                    bigram_sessions[(project, vendor)].add(str(segment[0]["session_id"]))
                index = 0
                while index < len(families):
                    family = families[index]
                    end = index + 1
                    while end < len(families) and families[end] == family:
                        end += 1
                    if family == "shell":
                        shell_run_sessions[(project, vendor)].add(
                            str(segment[0]["session_id"])
                        )
                        burst_values[(project, vendor)].append(
                            (str(segment[0]["session_id"]), float(end - index))
                        )
                    index = end

    for project in selected_projects:
        for vendor in VENDORS:
            cell = (project, vendor)
            contribution_rules = {
                "shell_share": (len(cell_sessions.get(cell, set())), 100, "calls"),
                "decisive_failure_rate": (
                    len(decisive_sessions.get(cell, set())),
                    100,
                    "decisive calls",
                ),
                "same_prompt_repeat_read_share": (
                    len(read_sessions.get(cell, set())),
                    50,
                    "reads",
                ),
                "shell_shell_bigram_share": (
                    len(bigram_sessions.get(cell, set())),
                    100,
                    "bigrams",
                ),
                "bigram_entropy_bits": (
                    len(bigram_sessions.get(cell, set())),
                    100,
                    "bigrams",
                ),
            }
            for metric, (contributing_sessions, minimum_denominator, denominator_label) in contribution_rules.items():
                row = cells[(project, vendor, metric)]
                denominator = int(float(row["denominator"] or 0))
                eligible = denominator >= minimum_denominator and contributing_sessions >= 10
                row["eligible"] = eligible
                row["n_units"] = contributing_sessions
                row["eligibility_reason"] = (
                    f">={minimum_denominator} {denominator_label} and >=10 denominator-contributing sessions"
                    if eligible
                    else f"{denominator} {denominator_label}/{contributing_sessions} contributing sessions; "
                    f"need {minimum_denominator}/10"
                )
            clustered_values = burst_values.get((project, vendor), [])
            values = [value for _, value in clustered_values]
            sessions_n = len(shell_run_sessions.get((project, vendor), set()))
            eligible = len(values) >= 50 and sessions_n >= 10
            cells[(project, vendor, "shell_burst_p90")] = metric_row(
                "shell_burst_p90",
                project,
                vendor,
                percentile(values, 0.9),
                None,
                len(values),
                sessions_n,
                eligible,
                ">=50 same-prompt shell runs and >=10 sessions"
                if eligible
                else f"{len(values)} shell runs/{sessions_n} sessions; need 50/10",
            )
    return burst_values, input_files


def rq6_raw_path(manifest_row: dict[str, str]) -> Path:
    stratum = f"{manifest_row['config']}-{manifest_row['split']}"
    return RQ6 / "raw" / manifest_row["corpus"] / stratum / f"{int(manifest_row['row_offset']):06d}.json.gz"


def public_metrics(preflight: bool) -> tuple[
    list[dict[str, Any]],
    dict[tuple[str, str], list[tuple[str, float]]],
    dict[tuple[str, str], list[tuple[str, float]]],
    dict[tuple[str, str], list[tuple[str, float]]],
]:
    rq6_code = import_module(RQ6_CODE, "frozen_rq6_projection")
    manifest = read_csv(RQ6 / "sample-manifest.csv")
    if preflight:
        grouped: dict[tuple[str, str, str], list[dict[str, str]]] = defaultdict(list)
        for row in manifest:
            grouped[(row["corpus"], row["config"], row["split"])].append(row)
        manifest = [row for key in sorted(grouped) for row in grouped[key][:2]]
    rows: list[dict[str, Any]] = []
    call_distributions: dict[tuple[str, str], list[tuple[str, float]]] = defaultdict(list)
    target_distributions: dict[tuple[str, str], list[tuple[str, float]]] = defaultdict(list)
    shell_bursts: dict[tuple[str, str], list[tuple[str, float]]] = defaultdict(list)
    for manifest_row in manifest:
        path = rq6_raw_path(manifest_row)
        with gzip.open(path, "rt", encoding="utf-8") as stream:
            source = json.load(stream)
        actual = rq6_code.digest_bytes(rq6_code.canonical(source))
        if actual != manifest_row["row_sha256"]:
            raise ValueError(f"RQ6 row hash mismatch: {path}")
        corpus = manifest_row["corpus"]
        stratum = (
            "default/train"
            if corpus == "ideatrail"
            else f"{manifest_row['config']}/{manifest_row['split']}"
        )
        actions = rq6_code.calls_from_row(source, corpus)
        key = (corpus, stratum)
        cluster = manifest_row["row_id"]
        call_distributions[key].append((cluster, float(len(actions))))
        shell_flags = [
            str(action["tool"]).lower() in {"bash", "execute_bash"} for action in actions
        ]
        index = 0
        while index < len(shell_flags):
            if not shell_flags[index]:
                index += 1
                continue
            end = index + 1
            while end < len(shell_flags) and shell_flags[end]:
                end += 1
            shell_bursts[key].append((cluster, float(end - index)))
            index = end

        path_actions = [action for action in actions if action["paths"]]
        transition_total = 0
        local_transitions = 0
        same_path_transitions = 0
        same_module_only_transitions = 0
        cross_module_transitions = 0
        for previous, current in zip(path_actions, path_actions[1:]):
            transition_total += 1
            if set(previous["paths"]) & set(current["paths"]):
                same_path_transitions += 1
                local_transitions += 1
            elif set(previous["modules"]) & set(current["modules"]):
                same_module_only_transitions += 1
                local_transitions += 1
            else:
                cross_module_transitions += 1

        module_state: dict[str, dict[str, Any]] = {}
        return_calls = 0
        for path_index, action in enumerate(path_actions):
            present = set(action["modules"])
            returned = False
            for module_name in module_state:
                if module_name not in present:
                    module_state[module_name]["left"] = True
            for module_name in present:
                previous = module_state.get(module_name)
                if previous and previous["left"]:
                    returned = True
                module_state[module_name] = {"index": path_index, "left": False}
            return_calls += returned

        seen_paths: set[str] = set()
        seen_read_paths: set[str] = set()
        path_instances = 0
        reused_path_instances = 0
        read_instances = 0
        repeated_read_instances = 0
        weights: Counter[str] = Counter()
        for action in path_actions:
            for target in action["paths"]:
                path_instances += 1
                reused_path_instances += target in seen_paths
                if action["explore"]:
                    read_instances += 1
                    repeated_read_instances += target in seen_read_paths
                    seen_read_paths.add(target)
                seen_paths.add(target)
                weights[target] += 1
        if weights:
            target_distributions[key].extend(
                (cluster, float(value)) for value in weights.values()
            )
        top_share = safe_div(max(weights.values(), default=0), sum(weights.values()))
        top_excess = (
            top_share - 1 / len(weights) if top_share is not None and weights else None
        )

        repeat_flags: list[tuple[int, int]] = []
        seen_for_phase: set[str] = set()
        for action in actions:
            reads = list(action["paths"]) if action["explore"] else []
            repeat_flags.append((len(reads), sum(target in seen_for_phase for target in reads)))
            seen_for_phase.update(reads)
        early_read = early_repeat = late_read = late_repeat = 0
        if len(actions) >= 30:
            n = len(actions)
            for action_index, (reads, repeats) in enumerate(repeat_flags):
                phase = min(2, math.floor(3 * action_index / n))
                if phase == 0:
                    early_read += reads
                    early_repeat += repeats
                elif phase == 2:
                    late_read += reads
                    late_repeat += repeats
        delta = (
            late_repeat / late_read - early_repeat / early_read
            if early_read and late_read
            else None
        )
        rows.append(
            {
                "corpus": corpus,
                "stratum": stratum,
                "cluster_id": manifest_row["cluster_id"],
                "row_id": manifest_row["row_id"],
                "tool_calls": len(actions),
                "shell_calls": sum(shell_flags),
                "shell_share": safe_div(sum(shell_flags), len(actions)),
                "path_calls": len(path_actions),
                "path_transitions": transition_total,
                "local_path_transitions": local_transitions,
                "same_path_transitions": same_path_transitions,
                "same_module_only_transitions": same_module_only_transitions,
                "cross_module_transitions": cross_module_transitions,
                "path_locality_share": safe_div(local_transitions, transition_total),
                "module_return_calls": return_calls,
                "module_return_call_share": safe_div(return_calls, len(path_actions)),
                "path_instances": path_instances,
                "reused_path_instances": reused_path_instances,
                "path_reuse_share": safe_div(reused_path_instances, path_instances),
                "path_read_instances": read_instances,
                "repeated_path_read_instances": repeated_read_instances,
                "repeat_path_read_share": safe_div(repeated_read_instances, read_instances),
                "top_path_share": top_share,
                "unique_target_paths": len(weights),
                "top_path_excess": top_excess if top_excess is not None else "",
                "late_path_reread_delta": delta if delta is not None else "",
            }
        )
    return rows, call_distributions, target_distributions, shell_bursts


def summarize_public(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[(row["corpus"], row["stratum"])].append(row)
    result: list[dict[str, Any]] = []
    for group_index, ((corpus, stratum), group) in enumerate(sorted(groups.items())):
        calls = [int(row["tool_calls"]) for row in group]
        totals = {
            "shell": sum(int(row["shell_calls"]) for row in group),
            "calls": sum(calls),
            "local": sum(int(row["local_path_transitions"]) for row in group),
            "same_path": sum(int(row["same_path_transitions"]) for row in group),
            "same_module_only": sum(int(row["same_module_only_transitions"]) for row in group),
            "cross_module": sum(int(row["cross_module_transitions"]) for row in group),
            "transitions": sum(int(row["path_transitions"]) for row in group),
            "returns": sum(int(row["module_return_calls"]) for row in group),
            "path_calls": sum(int(row["path_calls"]) for row in group),
            "path_reused": sum(int(row["reused_path_instances"]) for row in group),
            "path_instances": sum(int(row["path_instances"]) for row in group),
            "read_repeated": sum(int(row["repeated_path_read_instances"]) for row in group),
            "read_instances": sum(int(row["path_read_instances"]) for row in group),
        }
        deltas = [float(row["late_path_reread_delta"]) for row in group if row["late_path_reread_delta"] != ""]
        tops = [float(row["top_path_share"]) for row in group if row["top_path_share"] not in {"", None}]
        top_excesses = [float(row["top_path_excess"]) for row in group if row["top_path_excess"] not in {"", None}]
        summary = {
            "corpus": corpus,
            "stratum": stratum,
            "units": len(group),
            "tool_calls": totals["calls"],
            "top10_unit_call_share": top_fraction_share(calls),
            "top10_unit_call_excess": (
                (top_fraction_share(calls) or 0) - math.ceil(0.1 * len(calls)) / len(calls)
                if calls
                else None
            ),
            "shell_share": safe_div(totals["shell"], totals["calls"]),
            "path_locality_share": safe_div(totals["local"], totals["transitions"]),
            "path_locality_excess": (
                safe_div(totals["local"] - totals["cross_module"], totals["transitions"])
            ),
            "same_path_share": safe_div(totals["same_path"], totals["transitions"]),
            "same_module_only_share": safe_div(totals["same_module_only"], totals["transitions"]),
            "cross_module_share": safe_div(totals["cross_module"], totals["transitions"]),
            "path_locality_n": totals["transitions"],
            "module_return_call_share": safe_div(totals["returns"], totals["path_calls"]),
            "module_return_n": totals["path_calls"],
            "path_reuse_share": safe_div(totals["path_reused"], totals["path_instances"]),
            "path_reuse_n": totals["path_instances"],
            "repeat_path_read_share": safe_div(totals["read_repeated"], totals["read_instances"]),
            "repeat_path_read_n": totals["read_instances"],
            "unit_top_path_share_median": median(tops),
            "unit_top_path_excess_median": median(top_excesses),
            "unit_top_path_n": len(tops),
            "late_path_reread_delta_median": median(deltas),
            "late_path_reread_delta_n": len(deltas),
        }

        def estimate(sample: list[dict[str, Any]], metric: str) -> float | None:
            if metric == "top10_unit_call_share":
                return top_fraction_share([int(row["tool_calls"]) for row in sample])
            if metric == "top10_unit_call_excess":
                sample_calls = [int(row["tool_calls"]) for row in sample]
                base = math.ceil(0.1 * len(sample_calls)) / len(sample_calls)
                return (top_fraction_share(sample_calls) or 0) - base
            if metric == "path_locality_excess":
                local = sum(int(row["local_path_transitions"]) for row in sample)
                cross = sum(int(row["cross_module_transitions"]) for row in sample)
                total = sum(int(row["path_transitions"]) for row in sample)
                return safe_div(local - cross, total)
            if metric == "module_return_call_share":
                return safe_div(
                    sum(int(row["module_return_calls"]) for row in sample),
                    sum(int(row["path_calls"]) for row in sample),
                )
            if metric == "path_reuse_share":
                return safe_div(
                    sum(int(row["reused_path_instances"]) for row in sample),
                    sum(int(row["path_instances"]) for row in sample),
                )
            if metric == "repeat_path_read_share":
                return safe_div(
                    sum(int(row["repeated_path_read_instances"]) for row in sample),
                    sum(int(row["path_read_instances"]) for row in sample),
                )
            if metric == "shell_share":
                return safe_div(
                    sum(int(row["shell_calls"]) for row in sample),
                    sum(int(row["tool_calls"]) for row in sample),
                )
            if metric == "unit_top_path_excess_median":
                return median(
                    float(row["top_path_excess"])
                    for row in sample
                    if row["top_path_excess"] not in {"", None}
                )
            if metric == "unit_top_path_share_median":
                return median(
                    float(row["top_path_share"])
                    for row in sample
                    if row["top_path_share"] not in {"", None}
                )
            if metric == "late_path_reread_delta_median":
                return median(
                    float(row["late_path_reread_delta"])
                    for row in sample
                    if row["late_path_reread_delta"] != ""
                )
            raise KeyError(metric)

        rng = np.random.default_rng(20260726 + group_index)
        for metric in [
            "top10_unit_call_share",
            "top10_unit_call_excess",
            "path_locality_excess",
            "module_return_call_share",
            "path_reuse_share",
            "repeat_path_read_share",
            "shell_share",
            "unit_top_path_excess_median",
            "unit_top_path_share_median",
            "late_path_reread_delta_median",
        ]:
            bootstrap = []
            for _ in range(2000):
                sample = [group[int(index)] for index in rng.integers(0, len(group), len(group))]
                value = estimate(sample, metric)
                if value is not None and math.isfinite(value):
                    bootstrap.append(value)
            summary[f"{metric}_ci95_low"] = percentile(bootstrap, 0.025)
            summary[f"{metric}_ci95_high"] = percentile(bootstrap, 0.975)
        result.append(summary)
    return result


def fit_tail(
    clustered_values: Sequence[tuple[str, float]],
    minimum_tail: int = 50,
    fixed_xmin: int | None = None,
) -> dict[str, Any] | None:
    materialized = [
        (str(cluster), int(round(float(value))))
        for cluster, value in clustered_values
        if value is not None and float(value) > 0
    ]
    clean = np.asarray([value for _, value in materialized], dtype=int)
    clusters = np.asarray([cluster for cluster, _ in materialized], dtype=object)
    if len(clean) < minimum_tail:
        return None
    candidates = [fixed_xmin] if fixed_xmin is not None else sorted(set(clean))
    best: tuple[float, float, float, np.ndarray, np.ndarray] | None = None
    for xmin in (candidates if fixed_xmin is not None else candidates[:-1]):
        mask = clean >= xmin
        tail = clean[mask]
        tail_clusters = clusters[mask]
        if len(tail) < minimum_tail or len(set(tail_clusters)) < 10:
            continue
        log_sum = float(np.log(tail).sum())

        def power_objective(alpha_value: float) -> float:
            normalizer = float(zeta(alpha_value, xmin))
            if not math.isfinite(normalizer) or normalizer <= 0:
                return 1e100
            return len(tail) * math.log(normalizer) + alpha_value * log_sum

        power_fit = minimize_scalar(
            power_objective,
            bounds=(1.0001, 20.0),
            method="bounded",
            options={"xatol": 1e-10, "maxiter": 2000},
        )
        alpha = float(power_fit.x)
        support = np.asarray(sorted(set(tail)), dtype=int)
        empirical = np.asarray([np.mean(tail <= value) for value in support])
        model = 1.0 - np.asarray(
            [float(zeta(alpha, int(value) + 1) / zeta(alpha, xmin)) for value in support]
        )
        ks = float(np.max(np.abs(empirical - model)))
        if best is None or ks < best[0]:
            best = (ks, float(xmin), float(alpha), tail, tail_clusters)
    if best is None:
        return None
    ks_power, xmin, alpha, tail, tail_clusters = best
    logs = np.log(tail)
    lower_edge = max(xmin - 0.5, 1e-12)
    lower = math.log(lower_edge)

    def log_interval_mass(lower_z: np.ndarray, upper_z: np.ndarray) -> np.ndarray:
        """Stable log P(lower_z < Z <= upper_z) for standard normal Z."""

        result = np.empty_like(lower_z, dtype=float)
        use_survival = lower_z > 0
        if np.any(use_survival):
            first = norm.logsf(lower_z[use_survival])
            second = norm.logsf(upper_z[use_survival])
            result[use_survival] = first + np.log1p(
                -np.minimum(np.exp(second - first), 1.0 - 1e-15)
            )
        if np.any(~use_survival):
            first = norm.logcdf(upper_z[~use_survival])
            second = norm.logcdf(lower_z[~use_survival])
            result[~use_survival] = first + np.log1p(
                -np.minimum(np.exp(second - first), 1.0 - 1e-15)
            )
        return result

    def objective(parameters: np.ndarray) -> float:
        mu = float(parameters[0])
        sigma = math.exp(float(parameters[1]))
        a = (lower - mu) / sigma
        log_survival = float(norm.logsf(a))
        if not math.isfinite(log_survival):
            return 1e100
        lower_z = (np.log(np.maximum(tail - 0.5, 1e-12)) - mu) / sigma
        upper_z = (np.log(tail + 0.5) - mu) / sigma
        log_masses = log_interval_mass(lower_z, upper_z)
        return -float((log_masses - log_survival).sum())

    start_sigma = max(float(np.std(logs)), 0.2)
    mu_low = min(lower - 20.0, float(np.min(logs)) - 5.0)
    mu_high = float(np.max(logs)) + 5.0
    optimized = minimize(
        objective,
        np.asarray([float(np.mean(logs)), math.log(start_sigma)]),
        method="L-BFGS-B",
        bounds=[(mu_low, mu_high), (math.log(0.05), math.log(20.0))],
        options={"maxiter": 5000, "ftol": 1e-12},
    )
    mu = float(optimized.x[0])
    sigma = math.exp(float(optimized.x[1]))
    a = (lower - mu) / sigma
    log_pl = -alpha * logs - math.log(float(zeta(alpha, xmin)))
    lower_z = (np.log(np.maximum(tail - 0.5, 1e-12)) - mu) / sigma
    upper_z = (np.log(tail + 0.5) - mu) / sigma
    log_ln = log_interval_mass(lower_z, upper_z) - norm.logsf(a)
    differences = log_pl - log_ln
    ratio = float(differences.sum())
    cluster_lr: dict[str, float] = defaultdict(float)
    for cluster, value in zip(tail_clusters, differences):
        cluster_lr[str(cluster)] += float(value)
    cluster_contributions = np.asarray(list(cluster_lr.values()), dtype=float)
    sd = (
        float(np.std(cluster_contributions, ddof=1))
        if len(cluster_contributions) > 1
        else 0.0
    )
    z_value = (
        ratio / (math.sqrt(len(cluster_contributions)) * sd)
        if sd > 0
        else 0.0
    )
    p_value = float(2 * norm.sf(abs(z_value))) if sd > 0 else 1.0
    rng = np.random.default_rng(
        20260726 + int(xmin) + len(clean) + len(cluster_contributions)
    )
    bootstrap_lr = []
    if len(cluster_contributions) >= 2:
        for _ in range(2000):
            bootstrap_lr.append(
                float(
                    cluster_contributions[
                        rng.integers(0, len(cluster_contributions), len(cluster_contributions))
                    ].sum()
                )
            )
    lr_low = percentile(bootstrap_lr, 0.025)
    lr_high = percentile(bootstrap_lr, 0.975)
    preferred = "indistinguishable"
    if (
        lr_low is not None
        and lr_high is not None
        and (lr_low > 0 or lr_high < 0)
    ):
        preferred = "power_law" if ratio > 0 else "lognormal"
    support = np.asarray(sorted(set(tail)), dtype=int)
    empirical = np.asarray([np.mean(tail <= value) for value in support])
    lognormal_cdf = 1.0 - np.exp(
        norm.logsf((np.log(support + 0.5) - mu) / sigma) - norm.logsf(a)
    )
    ks_lognormal = float(np.max(np.abs(empirical - lognormal_cdf)))
    return {
        "n_total": len(clean),
        "xmin": xmin,
        "tail_n": len(tail),
        "tail_fraction": len(tail) / len(clean),
        "tail_clusters": len(cluster_contributions),
        "power_law_alpha": alpha,
        "lognormal_mu": mu,
        "lognormal_sigma": sigma,
        "ks_power_law": ks_power,
        "ks_lognormal": ks_lognormal,
        "log_likelihood_ratio_pl_minus_ln": ratio,
        "vuong_z": z_value,
        "vuong_p": p_value,
        "cluster_bootstrap_lr_ci95_low": lr_low,
        "cluster_bootstrap_lr_ci95_high": lr_high,
        "preferred_family": preferred,
        "optimizer_success": bool(optimized.success),
    }


def distribution_fits(
    session_counts: dict[tuple[str, str], list[int]],
    local_target_counts: dict[tuple[str, str], list[tuple[str, float]]],
    local_shell_bursts: dict[tuple[str, str], list[tuple[str, float]]],
    public_calls: dict[tuple[str, str], list[tuple[str, float]]],
    public_targets: dict[tuple[str, str], list[tuple[str, float]]],
    public_bursts: dict[tuple[str, str], list[tuple[str, float]]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    clustered_session_counts = {
        key: [(f"unit-{index}", float(value)) for index, value in enumerate(values)]
        for key, values in session_counts.items()
    }
    local_sets = {
        "unit_call_count": clustered_session_counts,
        "target_access_count": local_target_counts,
        "shell_burst_length": local_shell_bursts,
    }
    public_sets = {
        "unit_call_count": public_calls,
        "target_access_count": public_targets,
        "shell_burst_length": public_bursts,
    }
    for distribution, groups in local_sets.items():
        for (project, vendor), values in sorted(groups.items()):
            fit = fit_tail(values)
            common = fit_tail(values, fixed_xmin=1)
            row = {
                "population": "local",
                "distribution": distribution,
                "project_or_corpus": project,
                "vendor_or_stratum": vendor,
                "observations": len(values),
                "fit_status": "fit" if fit else "insufficient_tail",
            }
            if fit:
                row.update(fit)
            if common:
                for field in [
                    "power_law_alpha",
                    "lognormal_mu",
                    "lognormal_sigma",
                    "log_likelihood_ratio_pl_minus_ln",
                    "cluster_bootstrap_lr_ci95_low",
                    "cluster_bootstrap_lr_ci95_high",
                    "preferred_family",
                ]:
                    output_field = (
                        "common_xmin1_relative_family_unadjusted"
                        if field == "preferred_family"
                        else f"common_xmin1_{field}"
                    )
                    row[output_field] = common[field]
            rows.append(row)
    for distribution, groups in public_sets.items():
        for (corpus, stratum), values in sorted(groups.items()):
            fit = fit_tail(values)
            common = fit_tail(values, fixed_xmin=1)
            row = {
                "population": "public",
                "distribution": distribution,
                "project_or_corpus": corpus,
                "vendor_or_stratum": stratum,
                "observations": len(values),
                "fit_status": "fit" if fit else "insufficient_tail",
            }
            if fit:
                row.update(fit)
            if common:
                for field in [
                    "power_law_alpha",
                    "lognormal_mu",
                    "lognormal_sigma",
                    "log_likelihood_ratio_pl_minus_ln",
                    "cluster_bootstrap_lr_ci95_low",
                    "cluster_bootstrap_lr_ci95_high",
                    "preferred_family",
                ]:
                    output_field = (
                        "common_xmin1_relative_family_unadjusted"
                        if field == "preferred_family"
                        else f"common_xmin1_{field}"
                    )
                    row[output_field] = common[field]
            rows.append(row)
    fitted = [row for row in rows if row["fit_status"] == "fit"]
    ranked = sorted(enumerate(fitted), key=lambda item: float(item[1]["vuong_p"]))
    adjusted = [1.0] * len(fitted)
    running = 1.0
    total_tests = len(fitted)
    for reverse_rank, (original_index, row) in enumerate(reversed(ranked), start=1):
        rank = total_tests - reverse_rank + 1
        candidate = min(1.0, float(row["vuong_p"]) * total_tests / rank)
        running = min(running, candidate)
        adjusted[original_index] = running
    for index, row in enumerate(fitted):
        row["relative_family_unadjusted"] = row["preferred_family"]
        row["vuong_q_bh"] = adjusted[index]
        if adjusted[index] >= 0.05:
            row["preferred_family"] = "indistinguishable"
    fields = [
        "population",
        "distribution",
        "project_or_corpus",
        "vendor_or_stratum",
        "observations",
        "fit_status",
        "n_total",
        "xmin",
        "tail_n",
        "tail_fraction",
        "tail_clusters",
        "power_law_alpha",
        "lognormal_mu",
        "lognormal_sigma",
        "ks_power_law",
        "ks_lognormal",
        "log_likelihood_ratio_pl_minus_ln",
        "vuong_z",
        "vuong_p",
        "vuong_q_bh",
        "cluster_bootstrap_lr_ci95_low",
        "cluster_bootstrap_lr_ci95_high",
        "relative_family_unadjusted",
        "preferred_family",
        "optimizer_success",
        "common_xmin1_power_law_alpha",
        "common_xmin1_lognormal_mu",
        "common_xmin1_lognormal_sigma",
        "common_xmin1_log_likelihood_ratio_pl_minus_ln",
        "common_xmin1_cluster_bootstrap_lr_ci95_low",
        "common_xmin1_cluster_bootstrap_lr_ci95_high",
        "common_xmin1_relative_family_unadjusted",
    ]
    return [{field: row.get(field, "") for field in fields} for row in rows]


def distribution_summary(fits: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in fits:
        if row["fit_status"] == "fit":
            groups[(row["population"], row["distribution"])].append(row)
    result = []
    for (population, distribution), rows in sorted(groups.items()):
        counts = Counter(row["preferred_family"] for row in rows)
        decisive = counts["power_law"] + counts["lognormal"]
        dominant = ""
        agreement = 0.0
        distinct_local_projects = len(
            {row["project_or_corpus"] for row in rows}
        ) if population == "local" else 0
        if decisive >= 3:
            family, count = max(
                (("power_law", counts["power_law"]), ("lognormal", counts["lognormal"])),
                key=lambda item: item[1],
            )
            agreement = count / len(rows)
            if agreement >= 0.70 and (population != "local" or distinct_local_projects >= 3):
                dominant = family
        parameter = (
            [
                float(row["common_xmin1_power_law_alpha"])
                for row in rows
                if row["preferred_family"] == "power_law"
                and row.get("common_xmin1_power_law_alpha") not in {"", None}
            ]
            if dominant == "power_law"
            else [
                float(row["common_xmin1_lognormal_sigma"])
                for row in rows
                if row["preferred_family"] == "lognormal"
                and row.get("common_xmin1_lognormal_sigma") not in {"", None}
            ]
        )
        mu_values = [
            float(row["common_xmin1_lognormal_mu"])
            for row in rows
            if row["preferred_family"] == "lognormal"
            and row.get("common_xmin1_lognormal_mu") not in {"", None}
        ]
        xmins = [float(row["xmin"]) for row in rows]
        parameter_cv = (
            statistics.stdev(parameter) / abs(statistics.mean(parameter))
            if len(parameter) >= 2 and statistics.mean(parameter) != 0
            else None
        )
        result.append(
            {
                "population": population,
                "distribution": distribution,
                "fit_cells": len(rows),
                "distinct_local_projects": distinct_local_projects,
                "power_law_wins": counts["power_law"],
                "lognormal_wins": counts["lognormal"],
                "indistinguishable": counts["indistinguishable"],
                "decisive_fits": decisive,
                "dominant_family": dominant or "none",
                "decisive_agreement": agreement if decisive else "",
                "decisive_coverage": decisive / len(rows) if rows else "",
                "dominant_parameter_cv": "" if parameter_cv is None else parameter_cv,
                "common_support_lognormal_mu_sd": (
                    statistics.stdev(mu_values) if len(mu_values) >= 2 else ""
                ),
                "selected_xmin_cv": (
                    statistics.stdev(xmins) / statistics.mean(xmins)
                    if len(xmins) >= 2 and statistics.mean(xmins) != 0
                    else ""
                ),
                "shape_stable_parameter_drifting": bool(
                    dominant and parameter_cv is not None and parameter_cv >= 0.30
                ),
            }
        )
    return result


def transform_value(value: float, kind: str) -> float:
    if kind == "share":
        clipped = min(max(value, 1e-6), 1 - 1e-6)
        return math.log(clipped / (1 - clipped))
    if kind == "positive":
        return math.log(max(value, 1e-12))
    return value


def direction(value: float, anchor: float) -> int:
    if value > anchor:
        return 1
    if value < anchor:
        return -1
    return 0


def external_rows_and_status(
    local_metric_rows: list[dict[str, Any]],
    local_external: dict[tuple[str, str], dict[str, float | int | None]],
    public_summary: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], dict[str, str], list[dict[str, Any]]]:
    rows: list[dict[str, Any]] = []
    local_by_metric: dict[str, list[float]] = defaultdict(list)

    local_core = {
        (row["project"], row["vendor"], row["metric"]): row for row in local_metric_rows
    }
    comparison_metrics = [
        ("top10_unit_call_share", "top10_session_call_share", 0.0),
        ("path_locality_excess", "path_locality_share", 0.0),
        ("module_return_call_share", "module_return_call_share", 0.0),
        ("path_reuse_share", "", 0.0),
        ("repeat_path_read_share", "", 0.0),
        ("shell_share", "shell_share", 0.5),
        ("unit_top_path_share_median", "session_top_path_share_median", 0.0),
        ("late_path_reread_delta_median", "late_reread_delta_median", 0.0),
    ]
    for project in PROJECTS:
        for vendor in VENDORS:
            external = local_external.get((project, vendor), {})
            for public_metric, local_metric, anchor in comparison_metrics:
                if local_metric:
                    core = local_core[(project, vendor, local_metric)]
                    value = (
                        as_float(core["contrast_value"])
                        if public_metric
                        in {
                            "path_locality_excess",
                            "late_path_reread_delta_median",
                        }
                        else as_float(core["value"])
                    )
                    eligible = bool(core["eligible"])
                    n = core["denominator"] if core["denominator"] != "" else core["n_units"]
                else:
                    value = as_float(external.get(public_metric))
                    n_key = {
                        "path_reuse_share": "path_reuse_n",
                        "repeat_path_read_share": "repeat_path_read_n",
                    }[public_metric]
                    n = int(external.get(n_key) or 0)
                    eligible = n >= 100
                rows.append(
                    {
                        "population": "local",
                        "corpus_or_project": project,
                        "stratum_or_vendor": vendor,
                        "metric": public_metric,
                        "value": "" if value is None else value,
                        "n": n,
                        "eligible": eligible,
                        "direction_anchor": anchor,
                        "ci95_low": "",
                        "ci95_high": "",
                    }
                )
                if eligible and value is not None:
                    local_by_metric[public_metric].append(value)
    for summary in public_summary:
        for public_metric, _local_metric, anchor in comparison_metrics:
            value = as_float(summary.get(public_metric))
            n_key = {
                "top10_unit_call_share": "units",
                "path_locality_excess": "path_locality_n",
                "module_return_call_share": "module_return_n",
                "path_reuse_share": "path_reuse_n",
                "repeat_path_read_share": "repeat_path_read_n",
                "shell_share": "tool_calls",
                "unit_top_path_share_median": "unit_top_path_n",
                "late_path_reread_delta_median": "late_path_reread_delta_n",
            }[public_metric]
            n = int(summary.get(n_key) or 0)
            threshold = 50 if public_metric in {
                "top10_unit_call_share",
                "unit_top_path_share_median",
                "late_path_reread_delta_median",
            } else 100
            eligible = n >= threshold
            rows.append(
                {
                    "population": "public",
                    "corpus_or_project": summary["corpus"],
                    "stratum_or_vendor": summary["stratum"],
                    "metric": public_metric,
                    "value": "" if value is None else value,
                    "n": n,
                    "eligible": eligible,
                    "direction_anchor": anchor,
                    "ci95_low": (
                        ""
                        if summary.get(f"{public_metric}_ci95_low") is None
                        else summary.get(f"{public_metric}_ci95_low")
                    ),
                    "ci95_high": (
                        ""
                        if summary.get(f"{public_metric}_ci95_high") is None
                        else summary.get(f"{public_metric}_ci95_high")
                    ),
                }
            )

    summaries: list[dict[str, Any]] = []
    statuses: dict[str, str] = {}
    for public_metric, local_metric, anchor in comparison_metrics:
        local_values = local_by_metric[public_metric]
        local_signs = [direction(value, anchor) for value in local_values]
        nonzero_local = [sign for sign in local_signs if sign]
        modal = Counter(nonzero_local).most_common(1)[0][0] if nonzero_local else 0
        local_consistency = safe_div(sum(sign == modal for sign in local_signs), len(local_signs))
        public_metric_rows = [
            row
            for row in rows
            if row["population"] == "public"
            and row["metric"] == public_metric
            and row["eligible"]
            and row["value"] != ""
        ]

        def ci_supports(row: dict[str, Any], target_direction: int) -> bool:
            low = as_float(row["ci95_low"])
            high = as_float(row["ci95_high"])
            if low is None or high is None:
                return False
            return low > anchor if target_direction > 0 else high < anchor

        idea_rows = [row for row in public_metric_rows if row["corpus_or_project"] == "ideatrail"]
        open_rows = [row for row in public_metric_rows if row["corpus_or_project"] == "openswe"]
        idea_support = bool(idea_rows and ci_supports(idea_rows[0], modal))
        open_support_n = sum(ci_supports(row, modal) for row in open_rows)
        public_values = [float(row["value"]) for row in public_metric_rows]
        public_point_match = safe_div(
            sum(direction(value, anchor) == modal for value in public_values),
            len(public_values),
        )
        if public_metric in {
            "top10_unit_call_share",
            "unit_top_path_share_median",
        }:
            status = "descriptive_magnitude"
        elif public_metric == "shell_share":
            status = "harness-shaped"
        elif len(local_values) < 6 or len(public_metric_rows) < 5:
            status = "undercovered"
        elif (local_consistency or 0) >= 0.8 and idea_support and open_support_n >= 3:
            status = (
                "replicated_presence"
                if public_metric
                in {"module_return_call_share", "path_reuse_share", "repeat_path_read_share"}
                else "replicated_direction"
            )
        elif public_point_match is not None and public_point_match <= 0.2:
            status = "contradicted"
        else:
            status = "heterogeneous"
        if local_metric:
            statuses[local_metric] = status
        summaries.append(
            {
                "metric": public_metric,
                "mapped_local_metric": local_metric or "analogous_only",
                "anchor": anchor,
                "local_eligible_cells": len(local_values),
                "local_modal_direction": modal,
                "local_direction_consistency": "" if local_consistency is None else local_consistency,
                "public_eligible_strata": len(public_metric_rows),
                "public_matching_direction_share": "" if public_point_match is None else public_point_match,
                "ideatrail_ci_support": idea_support,
                "openswe_ci_support_strata": open_support_n,
                "external_status": status,
                "local_range": (
                    f"{min(local_values):.6g}..{max(local_values):.6g}" if local_values else ""
                ),
                "public_range": (
                    f"{min(public_values):.6g}..{max(public_values):.6g}" if public_values else ""
                ),
            }
        )
    return rows, statuses, summaries


def classify_metrics(
    metric_rows: list[dict[str, Any]],
    external_status: dict[str, str],
) -> list[dict[str, Any]]:
    by_metric: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in metric_rows:
        by_metric[row["metric"]].append(row)
    result = []
    for metric in METRICS:
        rows = by_metric[metric]
        eligible = [row for row in rows if row["eligible"] and row["value"] != ""]
        values = [float(row["value"]) for row in eligible]
        mean = statistics.mean(values) if values else None
        sd = statistics.stdev(values) if len(values) >= 2 else None
        cv = sd / abs(mean) if sd is not None and mean not in {None, 0} else math.inf
        contrasts = [
            float(row["contrast_value"])
            for row in eligible
            if row.get("contrast_value") not in {"", None}
        ]
        signs = [direction(value, 0.0) for value in contrasts]
        nonzero = [sign for sign in signs if sign]
        modal = Counter(nonzero).most_common(1)[0][0] if nonzero else 0
        consistency = safe_div(sum(sign == modal for sign in signs), len(signs)) or 0.0
        valid_contrast = len(contrasts) == len(eligible) and len(contrasts) > 0
        eligible_projects = sorted({row["project"] for row in eligible})
        eligible_vendors = sorted({row["vendor"] for row in eligible})
        eligible_pairs = sum(
            all(
                any(
                    row["project"] == project and row["vendor"] == vendor
                    for row in eligible
                )
                for vendor in ("claude", "codex")
            )
            for project in PROJECTS
        )
        coverage_sufficient = (
            len(eligible) >= 6
            and len(eligible_projects) >= 4
            and {"claude", "codex"}.issubset(eligible_vendors)
            and eligible_pairs >= 2
        )
        rng = np.random.default_rng(20260726 + list(METRICS).index(metric))
        cv_bootstrap = []
        if len(values) >= 2:
            array = np.asarray(values)
            for _ in range(2000):
                sample = array[rng.integers(0, len(array), len(array))]
                sample_mean = float(np.mean(sample))
                if sample_mean != 0 and len(sample) >= 2:
                    cv_bootstrap.append(float(np.std(sample, ddof=1) / abs(sample_mean)))
        cv_low = percentile(cv_bootstrap, 0.025)
        cv_high = percentile(cv_bootstrap, 0.975)
        loo_checks = []
        if len(eligible) >= 3 and valid_contrast:
            for omitted in range(len(eligible)):
                kept_values = [value for index, value in enumerate(values) if index != omitted]
                kept_contrasts = [value for index, value in enumerate(contrasts) if index != omitted]
                kept_mean = statistics.mean(kept_values)
                kept_cv = (
                    statistics.stdev(kept_values) / abs(kept_mean)
                    if len(kept_values) >= 2 and kept_mean != 0
                    else math.inf
                )
                kept_signs = [direction(value, 0.0) for value in kept_contrasts]
                kept_nonzero = [sign for sign in kept_signs if sign]
                kept_modal = Counter(kept_nonzero).most_common(1)[0][0] if kept_nonzero else 0
                kept_consistency = (
                    sum(sign == kept_modal for sign in kept_signs) / len(kept_signs)
                    if kept_signs
                    else 0
                )
                loo_checks.append(kept_cv < 0.30 and kept_consistency >= 0.80)
        loo_stability = safe_div(sum(loo_checks), len(loo_checks)) or 0.0

        paired: dict[tuple[str, str], float] = {
            (row["project"], row["vendor"]): float(row["value"])
            for row in eligible
            if row["project"] in PAIRED_PROJECTS and row["vendor"] in {"claude", "codex"}
        }
        paired_complete = all(
            (project, vendor) in paired
            for project in PAIRED_PROJECTS
            for vendor in ("claude", "codex")
        )
        rho = vendor_consistency = project_share = vendor_share = interaction_share = None
        median_vendor_delta = None
        leave_one_project_out_shape_stability = None
        if paired_complete:
            claude = [paired[(project, "claude")] for project in PAIRED_PROJECTS]
            codex = [paired[(project, "codex")] for project in PAIRED_PROJECTS]
            rho_value = spearmanr(claude, codex).statistic
            rho = float(rho_value) if math.isfinite(float(rho_value)) else 0.0
            deltas = [right - left for left, right in zip(claude, codex)]
            median_vendor_delta = float(statistics.median(deltas))
            delta_sign = direction(median_vendor_delta, 0.0)
            vendor_consistency = sum(direction(delta, 0.0) == delta_sign for delta in deltas) / len(deltas)

            matrix = np.asarray(
                [
                    [
                        transform_value(paired[(project, vendor)], METRICS[metric]["kind"])
                        for vendor in ("claude", "codex")
                    ]
                    for project in PAIRED_PROJECTS
                ]
            )
            grand = float(matrix.mean())
            project_means = matrix.mean(axis=1)
            vendor_means = matrix.mean(axis=0)
            ss_project = float(matrix.shape[1] * np.sum((project_means - grand) ** 2))
            ss_vendor = float(matrix.shape[0] * np.sum((vendor_means - grand) ** 2))
            residual = matrix - project_means[:, None] - vendor_means[None, :] + grand
            ss_interaction = float(np.sum(residual**2))
            total = ss_project + ss_vendor + ss_interaction
            if total > 0:
                project_share = ss_project / total
                vendor_share = ss_vendor / total
                interaction_share = ss_interaction / total
            target_shape = (
                "vendor"
                if vendor_share is not None
                and vendor_share >= 0.50
                and vendor_consistency == 1.0
                else "project"
                if project_share is not None and project_share >= 0.50 and rho >= 0.50
                else "other"
            )
            loo_shapes = []
            for omitted in range(len(PAIRED_PROJECTS)):
                reduced = np.delete(matrix, omitted, axis=0)
                reduced_grand = float(reduced.mean())
                reduced_project_means = reduced.mean(axis=1)
                reduced_vendor_means = reduced.mean(axis=0)
                reduced_project_ss = float(
                    reduced.shape[1]
                    * np.sum((reduced_project_means - reduced_grand) ** 2)
                )
                reduced_vendor_ss = float(
                    reduced.shape[0]
                    * np.sum((reduced_vendor_means - reduced_grand) ** 2)
                )
                reduced_residual = (
                    reduced
                    - reduced_project_means[:, None]
                    - reduced_vendor_means[None, :]
                    + reduced_grand
                )
                reduced_interaction_ss = float(np.sum(reduced_residual**2))
                reduced_total = (
                    reduced_project_ss + reduced_vendor_ss + reduced_interaction_ss
                )
                reduced_project_share = (
                    reduced_project_ss / reduced_total if reduced_total else 0
                )
                reduced_vendor_share = (
                    reduced_vendor_ss / reduced_total if reduced_total else 0
                )
                reduced_deltas = reduced[:, 1] - reduced[:, 0]
                reduced_vendor_consistency = (
                    len(set(np.sign(reduced_deltas))) == 1
                    and not np.any(reduced_deltas == 0)
                )
                reduced_rho = float(spearmanr(reduced[:, 0], reduced[:, 1]).statistic)
                reduced_shape = (
                    "vendor"
                    if reduced_vendor_share >= 0.50 and reduced_vendor_consistency
                    else "project"
                    if reduced_project_share >= 0.50 and reduced_rho >= 0.50
                    else "other"
                )
                loo_shapes.append(reduced_shape)
            leave_one_project_out_shape_stability = (
                sum(shape == target_shape for shape in loo_shapes) / len(loo_shapes)
            )

        ext = external_status.get(metric, "N/A")
        external_gate = (
            ext == "replicated_direction" if metric in EXTERNAL_MAP else True
        )
        invariant = (
            coverage_sufficient
            and cv < 0.30
            and valid_contrast
            and consistency >= 0.80
            and loo_stability >= 0.80
            and external_gate
        )
        if invariant:
            classification = "invariant-candidate"
            evidence = f"CV={cv:.3f}, direction={consistency:.2f}, external={ext}"
        elif (
            paired_complete
            and vendor_share is not None
            and vendor_share >= 0.50
            and vendor_consistency == 1.0
            and (leave_one_project_out_shape_stability or 0) >= 2 / 3
        ):
            classification = "vendor-shaped"
            evidence = (
                f"paired vendor SS={vendor_share:.2f}, vendor sign={vendor_consistency:.2f}, "
                f"project SS={project_share:.2f}"
            )
        elif (
            paired_complete
            and project_share is not None
            and project_share >= 0.50
            and rho is not None
            and rho >= 0.50
            and (leave_one_project_out_shape_stability or 0) >= 2 / 3
        ):
            classification = "project-shaped"
            evidence = (
                f"paired project SS={project_share:.2f}, rank rho={rho:.2f}, "
                f"vendor SS={vendor_share:.2f}"
            )
        else:
            classification = "idiosyncratic"
            evidence = (
                f"eligible={len(eligible)}, CV={'inf' if not math.isfinite(cv) else f'{cv:.3f}'}, "
                f"direction={consistency:.2f}, external={ext}"
            )
        if classification in {"vendor-shaped", "project-shaped"}:
            evidence_sufficiency = "limited"
            classification_status = "descriptive-3x2-paired-grid"
        elif not coverage_sufficient:
            evidence_sufficiency = "limited"
            classification_status = "insufficient-for-six-cell-rule"
        else:
            evidence_sufficiency = "sufficient"
            classification_status = "classified"
        result.append(
            {
                "metric": metric,
                "metric_label": METRICS[metric]["label"],
                "eligible_cells": len(eligible),
                "mean": "" if mean is None else mean,
                "sd": "" if sd is None else sd,
                "cv": cv if math.isfinite(cv) else "inf",
                "cv_cell_bootstrap_ci95_low": "" if cv_low is None else cv_low,
                "cv_cell_bootstrap_ci95_high": "" if cv_high is None else cv_high,
                "direction_contrast_available": valid_contrast,
                "modal_direction": modal,
                "direction_consistency": consistency,
                "leave_one_cell_out_invariant_stability": loo_stability,
                "eligible_projects": len(eligible_projects),
                "eligible_vendors": len(eligible_vendors),
                "complete_claude_codex_pairs": eligible_pairs,
                "paired_grid_complete": paired_complete,
                "project_rank_spearman": "" if rho is None else rho,
                "vendor_direction_consistency": "" if vendor_consistency is None else vendor_consistency,
                "median_codex_minus_claude": "" if median_vendor_delta is None else median_vendor_delta,
                "project_ss_share": "" if project_share is None else project_share,
                "vendor_ss_share": "" if vendor_share is None else vendor_share,
                "interaction_ss_share": "" if interaction_share is None else interaction_share,
                "leave_one_project_out_shape_stability": (
                    ""
                    if leave_one_project_out_shape_stability is None
                    else leave_one_project_out_shape_stability
                ),
                "external_status": ext,
                "classification": classification,
                "evidence_sufficiency": evidence_sufficiency,
                "classification_status": classification_status,
                "evidence": evidence,
            }
        )
    return result


def plot_heatmaps(rows: list[dict[str, Any]], output: Path) -> None:
    lookup = {(row["metric"], row["project"], row["vendor"]): row for row in rows}
    metrics = list(METRICS)
    fig, axes = plt.subplots(5, 3, figsize=(14, 20), constrained_layout=True)
    for ax, metric in zip(axes.flat, metrics):
        data = np.full((len(PROJECTS), len(VENDORS)), np.nan)
        annotations = [["N/A" for _ in VENDORS] for _ in PROJECTS]
        for i, project in enumerate(PROJECTS):
            for j, vendor in enumerate(VENDORS):
                row = lookup[(metric, project, vendor)]
                if row["value"] != "":
                    data[i, j] = float(row["value"])
                    annotations[i][j] = f"{float(row['value']):.2f}" + ("" if row["eligible"] else "*")
        finite = data[np.isfinite(data)]
        vmin, vmax = (float(finite.min()), float(finite.max())) if len(finite) else (0.0, 1.0)
        if vmin == vmax:
            vmax = vmin + 1
        image = ax.imshow(data, aspect="auto", cmap="viridis", vmin=vmin, vmax=vmax)
        ax.set_title(METRICS[metric]["label"], fontsize=10)
        ax.set_xticks(range(len(VENDORS)), VENDORS, rotation=30)
        ax.set_yticks(range(len(PROJECTS)), PROJECTS, fontsize=7)
        for i in range(len(PROJECTS)):
            for j in range(len(VENDORS)):
                ax.text(j, i, annotations[i][j], ha="center", va="center", fontsize=7, color="white")
        fig.colorbar(image, ax=ax, fraction=0.046, pad=0.04)
    fig.suptitle("Project × vendor core metrics (* = below eligibility threshold)", fontsize=15)
    fig.savefig(output, dpi=180)
    plt.close(fig)


def plot_classification(rows: list[dict[str, Any]], output: Path) -> None:
    colors = {
        "invariant-candidate": "#009E73",
        "vendor-shaped": "#0072B2",
        "project-shaped": "#E69F00",
        "idiosyncratic": "#999999",
    }
    ordered = sorted(
        rows,
        key=lambda row: (
            ["invariant-candidate", "vendor-shaped", "project-shaped", "idiosyncratic"].index(row["classification"]),
            float(row["cv"]) if row["cv"] != "inf" else 999,
        ),
    )
    fig, ax = plt.subplots(figsize=(12, 7), constrained_layout=True)
    y = np.arange(len(ordered))
    values = [min(float(row["cv"]), 2.0) if row["cv"] != "inf" else 2.0 for row in ordered]
    ax.barh(y, values, color=[colors[row["classification"]] for row in ordered])
    ax.axvline(0.3, color="black", linestyle="--", linewidth=1, label="invariant CV threshold")
    ax.set_yticks(y, [row["metric_label"] for row in ordered], fontsize=8)
    ax.invert_yaxis()
    ax.set_xlabel("Cross-cell coefficient of variation (capped at 2.0)")
    ax.set_title("Metric stability and evidence class")
    handles = [
        plt.Rectangle((0, 0), 1, 1, color=color, label=label) for label, color in colors.items()
    ]
    ax.legend(handles=handles, loc="lower right", fontsize=8)
    ax.grid(axis="x", alpha=0.2)
    fig.savefig(output, dpi=180)
    plt.close(fig)


def plot_external(rows: list[dict[str, Any]], output: Path) -> None:
    metrics = [
        "path_locality_excess",
        "module_return_call_share",
        "path_reuse_share",
        "repeat_path_read_share",
        "shell_share",
        "late_path_reread_delta_median",
    ]
    fig, axes = plt.subplots(2, 3, figsize=(16, 9), constrained_layout=True)
    for ax, metric in zip(axes.flat, metrics):
        subset = [row for row in rows if row["metric"] == metric and row["eligible"] and row["value"] != ""]
        local = [float(row["value"]) for row in subset if row["population"] == "local"]
        public = [float(row["value"]) for row in subset if row["population"] == "public"]
        positions = [1, 2]
        if local and public:
            ax.boxplot([local, public], positions=positions, widths=0.55, showfliers=True)
            ax.scatter(np.full(len(local), 1) + np.linspace(-0.08, 0.08, len(local)), local, s=18, alpha=0.7)
            ax.scatter(np.full(len(public), 2) + np.linspace(-0.08, 0.08, len(public)), public, s=24, alpha=0.8)
        ax.axhline(
            next(row["direction_anchor"] for row in subset) if subset else 0,
            color="black",
            linestyle="--",
            linewidth=0.8,
        )
        ax.set_xticks(positions, ["local cells", "public strata"])
        ax.set_title(metric.replace("_", " "), fontsize=10)
        ax.grid(axis="y", alpha=0.2)
    fig.suptitle("Compatible relation directions: local natural cases vs RQ6 public strata")
    fig.savefig(output, dpi=180)
    plt.close(fig)


def plot_distribution_likelihood_ratios(rows: list[dict[str, Any]], output: Path) -> None:
    distributions = ["unit_call_count", "target_access_count", "shell_burst_length"]
    labels = {
        "unit_call_count": "Tool calls per session / trajectory",
        "target_access_count": "Exact-path accesses per (unit, path)",
        "shell_burst_length": "Consecutive shell-run length",
    }
    colors = {
        "power_law": "#D55E00",
        "lognormal": "#0072B2",
        "indistinguishable": "#777777",
    }
    fig, axes = plt.subplots(1, 3, figsize=(18, 11), constrained_layout=True)
    for ax, distribution in zip(axes, distributions):
        subset = [
            row
            for row in rows
            if row["distribution"] == distribution and row["fit_status"] == "fit"
        ]
        subset.sort(
            key=lambda row: (
                row["population"],
                row["project_or_corpus"],
                row["vendor_or_stratum"],
            )
        )
        positions = np.arange(len(subset))
        for position, row in zip(positions, subset):
            estimate = float(row["log_likelihood_ratio_pl_minus_ln"])
            low = float(row["cluster_bootstrap_lr_ci95_low"])
            high = float(row["cluster_bootstrap_lr_ci95_high"])
            ax.errorbar(
                estimate,
                position,
                xerr=[[estimate - low], [high - estimate]],
                fmt="o",
                markersize=4,
                capsize=2,
                color=colors[row["preferred_family"]],
            )
        ylabels = [
            f"{row['population'][0].upper()} · {row['project_or_corpus']} · {row['vendor_or_stratum']}"
            for row in subset
        ]
        ax.set_yticks(positions, ylabels, fontsize=6)
        ax.invert_yaxis()
        ax.axvline(0, color="black", linewidth=0.9, linestyle="--")
        ax.set_xscale("symlog", linthresh=1.0)
        ax.set_xlabel("LR = log L(power law) − log L(lognormal)")
        ax.set_title(labels[distribution], fontsize=10)
        ax.grid(axis="x", alpha=0.2)
    handles = [
        plt.Line2D(
            [0],
            [0],
            marker="o",
            linestyle="",
            color=color,
            label=label.replace("_", " "),
        )
        for label, color in colors.items()
    ]
    fig.legend(handles=handles, loc="lower center", ncol=3, fontsize=8)
    fig.suptitle(
        "Discrete power law vs truncated lognormal: selected-xmin cluster-bootstrap likelihood ratios",
        fontsize=14,
    )
    fig.savefig(output, dpi=180)
    plt.close(fig)


def build_manifest(paths: Sequence[Path]) -> list[dict[str, Any]]:
    rows = []
    for path in sorted(set(paths)):
        rows.append(
            {
                "path": str(path.relative_to(ROOT)),
                "bytes": path.stat().st_size,
                "sha256": sha256(path),
            }
        )
    return rows


def main() -> None:
    args = parse_args()
    output = args.output_dir.resolve()
    output.mkdir(parents=True, exist_ok=True)
    (output / "figures").mkdir(parents=True, exist_ok=True)
    selected_projects = set(PROJECTS[:2] if args.preflight else PROJECTS)

    cells, session_counts = load_behavior_metrics(selected_projects)
    load_startup_and_drift(cells, selected_projects)
    load_zero_validation(cells, selected_projects)
    target_counts, local_external = load_path_metrics(cells, selected_projects)
    shell_bursts, event_files = load_shell_bursts(cells, selected_projects)

    metric_rows = []
    for metric in METRICS:
        for project in PROJECTS:
            for vendor in VENDORS:
                key = (project, vendor, metric)
                if key in cells:
                    metric_rows.append(cells[key])
                else:
                    metric_rows.append(
                        metric_row(
                            metric,
                            project,
                            vendor,
                            None,
                            None,
                            None,
                            0,
                            False,
                            "not evaluated in preflight" if args.preflight else "no observations",
                        )
                    )

    public_trajectory_rows, public_calls, public_targets, public_bursts = public_metrics(args.preflight)
    public_summary = summarize_public(public_trajectory_rows)
    external_rows, external_status, external_summary = external_rows_and_status(
        metric_rows, local_external, public_summary
    )
    classifications = classify_metrics(metric_rows, external_status)
    fits = distribution_fits(
        session_counts,
        target_counts,
        shell_bursts,
        public_calls,
        public_targets,
        public_bursts,
    )
    fit_summary = distribution_summary(fits)

    write_csv(output / "local_grid_metrics.csv", metric_rows)
    write_csv(output / "metric_classification.csv", classifications)
    write_csv(output / "public_trajectory_metrics.csv", public_trajectory_rows)
    write_csv(output / "public_stratum_summary.csv", public_summary)
    write_csv(output / "external_replication.csv", external_rows)
    write_csv(output / "external_replication_summary.csv", external_summary)
    write_csv(output / "distribution_fits.csv", fits)
    write_csv(output / "distribution_shape_summary.csv", fit_summary)

    direct_inputs = [
        HERE / "analysis.py",
        HERE / "plan.md",
        BEHAVIOR / "session_metrics.csv",
        BEHAVIOR / "session_pace_summary.csv",
        BEHAVIOR / "tool_family_distribution.csv",
        BEHAVIOR / "repeated_reads.csv",
        BEHAVIOR / "markov_transitions.csv",
        BEHAVIOR / "analyze_toolcalls.py",
        PROFILE / "transition_patterns.csv",
        PROFILE / "failure_recovery.csv",
        PROFILE / "report.md",
        SESSION / "raw/startup_sessions.csv",
        SESSION / "raw/drift_paired.csv",
        USER_QUESTIONS / "a-created-revisit-summary.csv",
        USER_QUESTIONS / "b-module-session-episodes.csv",
        USER_QUESTIONS / "result.md",
        RQ_EXTENSIONS / "rq1-dormancy-summary.csv",
        RQ_EXTENSIONS / "rq1-revivals.csv",
        RQ_EXTENSIONS / "result.md",
        FINAL / "rq2/raw/rq2-trajectory.csv",
        FINAL / "rq4/raw/rq4-accesses.csv",
        RQ2_CROSS / "project-vendor-summary.csv",
        RQ6 / "sample-manifest.csv",
        RQ6 / "trajectory-metrics.csv",
        RQ6_CODE,
        *event_files,
        *[rq6_raw_path(row) for row in read_csv(RQ6 / "sample-manifest.csv")],
    ]
    forbidden = [
        path for path in direct_inputs if "rq7-heldout-20260726" in str(path.resolve())
    ]
    if forbidden:
        raise RuntimeError(f"forbidden rq7-heldout input resolved: {forbidden}")
    manifest_rows = build_manifest(direct_inputs)
    write_csv(output / "input-manifest.csv", manifest_rows)

    authoritative_revival_total = sum(
        int(row["revival_transitions"])
        for row in read_csv(RQ_EXTENSIONS / "rq1-dormancy-summary.csv")
        if row["variant"] == "action_gap_gt_100"
        and canonical_project(row["project"]) in selected_projects
    )
    grid_revival_total = int(
        sum(
            float(row["numerator"] or 0)
            for row in metric_rows
            if row["metric"] == "dormant_revival_transition_share"
        )
    )
    reconciliation_rows = [
        {
            "check": "local_grid_rows",
            "expected": 18 * len(METRICS),
            "actual": len(metric_rows),
            "pass": len(metric_rows) == 18 * len(METRICS),
        },
        {
            "check": "classified_metrics",
            "expected": len(METRICS),
            "actual": len(classifications),
            "pass": len(classifications) == len(METRICS),
        },
        {
            "check": "public_trajectories",
            "expected": 10 if args.preflight else 320,
            "actual": len(public_trajectory_rows),
            "pass": len(public_trajectory_rows) == (10 if args.preflight else 320),
        },
        {
            "check": "public_strata",
            "expected": 5,
            "actual": len(public_summary),
            "pass": len(public_summary) == 5,
        },
        {
            "check": "action_gap_gt_100_revivals_vs_rq_extensions",
            "expected": authoritative_revival_total,
            "actual": grid_revival_total,
            "pass": authoritative_revival_total == grid_revival_total,
        },
        {
            "check": "local_tool_calls_from_session_metrics",
            "expected": "descriptive",
            "actual": sum(sum(values) for values in session_counts.values()),
            "pass": True,
        },
        {
            "check": "input_manifest_files",
            "expected": "descriptive",
            "actual": len(manifest_rows),
            "pass": True,
        },
    ]
    write_csv(output / "reconciliation.csv", reconciliation_rows)
    if not all(row["pass"] for row in reconciliation_rows):
        raise RuntimeError(f"reconciliation failed: {reconciliation_rows}")

    plot_heatmaps(metric_rows, output / "figures/local-grid-heatmaps.png")
    plot_classification(classifications, output / "figures/classification-cv.png")
    plot_external(external_rows, output / "figures/external-replication.png")
    plot_distribution_likelihood_ratios(
        fits, output / "figures/distribution-likelihood-ratios.png"
    )

    checks = {
        "mode": "preflight" if args.preflight else "full",
        "local_grid_rows": len(metric_rows),
        "expected_local_grid_rows": 18 * len(METRICS),
        "public_rows": len(public_trajectory_rows),
        "expected_public_rows": 10 if args.preflight else 320,
        "public_strata": len(public_summary),
        "expected_public_strata": 5,
        "metrics": len(METRICS),
        "rq7_heldout_accessed": False,
        "checks_pass": (
            len(metric_rows) == 18 * len(METRICS)
            and len(public_trajectory_rows) == (10 if args.preflight else 320)
            and len(public_summary) == 5
        ),
    }
    (output / ("preflight.json" if args.preflight else "run-summary.json")).write_text(
        json.dumps(checks, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    if not checks["checks_pass"]:
        raise RuntimeError(f"completion checks failed: {checks}")
    print(json.dumps(checks, sort_keys=True))


if __name__ == "__main__":
    main()
