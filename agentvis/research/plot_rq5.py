#!/usr/bin/env python3
"""Derive and render reviewed workspace activity allocation and migration (RQ3)."""

from __future__ import annotations

import argparse
import csv
import gc
import math
import re
from collections import Counter, defaultdict
from pathlib import Path, PurePosixPath

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.ticker import PercentFormatter

from plot_rq2 import load_projects, read_csv, sha256, verify_inputs


RQ4_ACCESS_SHA256 = "26466eb3a343ee6eb9a459a6c4690b8ae072b0317a775f6636093f0d3eb344cf"
SHORT = {
    "agentsight": "AgentSight",
    "ActPlane": "ActPlane",
    "bpf-developer-tutorial": "BPF tutorial",
    "eunomia.dev": "eunomia.dev",
    "agentskill-observability-paper": "AgentSkill paper",
    "academic-writing-skills": "Writing skills",
}
CLASSES = ["test", "paper/docs", "config/build", "data/input", "result/figure/log", "source", "other"]
CLASS_COLORS = ["#d55e5e", "#8e6bbd", "#d7a53f", "#4aa5a5", "#e57f43", "#3d79b5", "#8c929a"]
MUTATIONS = {"write", "create", "rename", "delete"}
TEST_PARTS = {"test", "tests", "spec", "specs", "bench", "benches", "benchmark", "benchmarks", "fixture", "fixtures"}
DOC_PARTS = {"doc", "docs", "paper", "papers", "note", "notes", "research"}
CONFIG_PARTS = {".github", ".gitlab", "config", ".config", "ci", "scripts"}
DATA_PARTS = {"data", "dataset", "datasets", "input", "inputs"}
RESULT_PARTS = {"result", "results", "output", "outputs", "figure", "figures", "plot", "plots", "log", "logs"}
CONFIG_NAMES = {
    "cargo.toml", "cargo.lock", "package.json", "package-lock.json", "pnpm-lock.yaml",
    "yarn.lock", "makefile", "cmakelists.txt", "dockerfile", "pyproject.toml",
    "setup.py", "requirements.txt", "go.mod", "go.sum", "build.gradle", "pom.xml",
}
SOURCE_EXT = {".c", ".h", ".cc", ".cpp", ".rs", ".go", ".py", ".js", ".jsx", ".ts", ".tsx", ".java", ".kt", ".swift", ".rb", ".php", ".sh", ".bash", ".css", ".scss", ".html"}


def write_csv(path: Path, rows: list[dict[str, object]], fields: list[str]) -> None:
    """Write deterministic LF-only research tables."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def classify_path(path: str) -> str:
    normalized = str(PurePosixPath(path)).lower()
    parts = PurePosixPath(normalized).parts
    basename = parts[-1] if parts else ""
    stem = PurePosixPath(basename).stem
    suffix = PurePosixPath(basename).suffix
    if any(part in TEST_PARTS for part in parts) or basename.startswith("test_") or re.match(r".+_test\..+", basename) or ".test." in basename or ".spec." in basename:
        return "test"
    if any(part in DOC_PARTS for part in parts) or re.match(r"^(readme|changelog|license)(\.[^.]+)?$", basename) or suffix in {".md", ".mdx", ".rst", ".tex", ".bib"}:
        return "paper/docs"
    if any(part in CONFIG_PARTS for part in parts) or basename in CONFIG_NAMES or suffix in {".toml", ".yaml", ".yml", ".ini", ".cfg"}:
        return "config/build"
    if any(part in DATA_PARTS for part in parts) or suffix in {".csv", ".tsv", ".jsonl", ".parquet", ".sqlite", ".db"}:
        return "data/input"
    if any(part in RESULT_PARTS for part in parts) or suffix in {".png", ".jpg", ".jpeg", ".svg", ".gif", ".mp4", ".log"}:
        return "result/figure/log"
    if suffix in SOURCE_EXT:
        return "source"
    return "other"


def module_for(path: str) -> str:
    parts = PurePosixPath(path).parts
    return parts[0] if len(parts) > 1 else "repo-root-files"


def bool_text(value: object) -> bool:
    return str(value).lower() == "true"


def derive(
    projects: list[tuple[str, list[dict[str, object]]]],
    access_rows: list[dict[str, str]],
) -> tuple[list[dict[str, object]], list[dict[str, object]], list[dict[str, object]], list[dict[str, object]], list[dict[str, object]]]:
    event_meta: dict[tuple[str, str], dict[str, object]] = {}
    source_stats: dict[tuple[str, str], Counter[str]] = defaultdict(Counter)
    project_order = []
    for project, events in projects:
        project_order.append(project)
        for event in events:
            vendor = str(event["vendor"])
            status = str(event.get("status", "observed"))
            actions = list(event.get("actions", []))
            has_scope = any(bool(action.get("scope", False)) for action in actions)
            has_non_scope = any(not bool(action.get("scope", False)) for action in actions)
            for key in [(project, "ALL"), (project, vendor)]:
                stats = source_stats[key]
                stats["tool_events"] += 1
                stats[f"status_{status}"] += 1
                stats["worktree_attributed_tool_events"] += bool(event.get("worktree_id")) or any(action.get("worktree_id") for action in actions)
                stats["source_action_rows"] += len(actions)
                stats["scope_action_rows"] += sum(bool(action.get("scope", False)) for action in actions)
                stats["non_scope_action_rows"] += sum(not bool(action.get("scope", False)) for action in actions)
                stats["retained_non_scope_action_rows"] += sum(not bool(action.get("scope", False)) for action in actions) * (status in {"ok", "observed"})
                stats["failed_status_action_rows"] += sum(not bool(action.get("scope", False)) for action in actions) * (status not in {"ok", "observed"})
                stats["scope_only_tool_events"] += has_scope and not has_non_scope
                stats["no_resolved_path_tool_events"] += not actions
                stats["failed_without_resolved_path"] += status == "fail" and not has_non_scope
            event_meta[(project, str(event["id"]))] = {
                "status": status,
                "vendor": vendor,
                "ts_ms": int(event["ts_ms"]),
                "session_id": str(event["session_id"]),
                "event_index": int(event["event_index"]) if "event_index" in event else None,
            }

    retained = []
    dropped_status = Counter()
    dropped_scope = Counter()
    for source in access_rows:
        meta = event_meta[(source["project"], source["event_id"])]
        status = str(meta["status"])
        if bool_text(source["scope"]):
            dropped_scope[source["project"]] += 1
            continue
        if status not in {"ok", "observed"}:
            dropped_status[source["project"]] += 1
            continue
        operation = source["operation"]
        stratum = "read" if operation == "read" else "mutation" if operation in MUTATIONS else ""
        if not stratum:
            continue
        identity_known = bool(source["artifact_id"])
        identity = source["artifact_id"] if identity_known else f"unresolved:{source['event_id']}:{source['action_ordinal']}"
        retained.append({
            "project": source["project"],
            "worktree_id": source["worktree_id"],
            "event_index": int(source["event_index"]),
            "event_id": source["event_id"],
            "ts_ms": int(source["ts_ms"]),
            "session_id": source["session_id"],
            "status": status,
            "vendor": meta["vendor"],
            "action_ordinal": int(source["action_ordinal"]),
            "artifact_id": identity,
            "identity_known": identity_known,
            "path": source["path"],
            "artifact_class": classify_path(source["path"]),
            "module": module_for(source["path"]),
            "operation": operation,
            "stratum": stratum,
            "previous_path": source["previous_path"],
        })

    # One primary unit per event/worktree/lineage/operation. Destination/latest
    # path is used only to collapse duplicate reports of the same lineage.
    units: dict[tuple[str, str, str, str, str], dict[str, object]] = {}
    for row in retained:
        key = (str(row["project"]), str(row["worktree_id"]), str(row["event_id"]), str(row["artifact_id"]), str(row["operation"]))
        previous = units.get(key)
        if previous is None or int(row["action_ordinal"]) > int(previous["action_ordinal"]):
            units[key] = row
    actions = sorted(units.values(), key=lambda row: (project_order.index(str(row["project"])), int(row["event_index"]), str(row["event_id"]), str(row["worktree_id"]), int(row["action_ordinal"])))

    by_call_stratum: dict[tuple[str, str, str, str], list[dict[str, object]]] = defaultdict(list)
    by_call: dict[tuple[str, str, str], list[dict[str, object]]] = defaultdict(list)
    for row in actions:
        by_call_stratum[(str(row["project"]), str(row["worktree_id"]), str(row["event_id"]), str(row["stratum"]))].append(row)
        by_call[(str(row["project"]), str(row["worktree_id"]), str(row["event_id"]))].append(row)
    for rows in by_call_stratum.values():
        lineage_counts = Counter(str(row["artifact_id"]) for row in rows)
        lineage_count = len(lineage_counts)
        for row in rows:
            # One Tool-call unit is split across lineages. If the same lineage
            # has multiple operations in the stratum, its share is split again
            # rather than counted repeatedly.
            row["fractional_weight"] = 1.0 / (lineage_count * lineage_counts[str(row["artifact_id"])])

    calls = []
    for (project, worktree, event_id), rows in by_call.items():
        calls.append({
            "project": project,
            "worktree_id": worktree,
            "event_index": min(int(row["event_index"]) for row in rows),
            "event_id": event_id,
            "ts_ms": min(int(row["ts_ms"]) for row in rows),
            "session_id": rows[0]["session_id"],
            "status": rows[0]["status"],
            "vendor": rows[0]["vendor"],
            "artifact_ids": ";".join(sorted({str(row["artifact_id"]) for row in rows if bool(row["identity_known"])})),
            "unknown_identity_actions": sum(not bool(row["identity_known"]) for row in rows),
            "modules": ";".join(sorted({str(row["module"]) for row in rows})),
            "read_lineages": len({str(row["artifact_id"]) for row in rows if row["stratum"] == "read"}),
            "mutation_lineages": len({str(row["artifact_id"]) for row in rows if row["stratum"] == "mutation"}),
        })
    calls.sort(key=lambda row: (project_order.index(str(row["project"])), str(row["worktree_id"]), int(row["event_index"]), str(row["event_id"])))

    lanes: dict[tuple[str, str], list[dict[str, object]]] = defaultdict(list)
    for row in calls:
        lanes[(str(row["project"]), str(row["worktree_id"]))].append(row)
    transitions = []
    returns = []
    for (project, worktree), rows in lanes.items():
        rows.sort(key=lambda row: (int(row["event_index"]), str(row["event_id"])))
        for rank, row in enumerate(rows, start=1):
            row["call_rank"] = rank
            row["call_count_lane"] = len(rows)
        for previous, current in zip(rows, rows[1:]):
            previous_ids = set(filter(None, str(previous["artifact_ids"]).split(";")))
            current_ids = set(filter(None, str(current["artifact_ids"]).split(";")))
            previous_modules = set(filter(None, str(previous["modules"]).split(";")))
            current_modules = set(filter(None, str(current["modules"]).split(";")))
            kind = "same_artifact" if previous_ids & current_ids else "same_module" if previous_modules & current_modules else "cross_module"
            transitions.append({
                "project": project,
                "worktree_id": worktree,
                "previous_event_id": previous["event_id"],
                "current_event_id": current["event_id"],
                "previous_call_rank": previous["call_rank"],
                "current_call_rank": current["call_rank"],
                "transition": kind,
                "same_session": previous["session_id"] == current["session_id"],
                "singleton_only": len(previous_ids) == len(current_ids) == 1 and len(previous_modules) == len(current_modules) == 1,
            })

        state: dict[str, dict[str, object]] = {}
        for index, row in enumerate(rows):
            present = set(filter(None, str(row["modules"]).split(";")))
            for module in sorted(state):
                module_state = state[module]
                if module not in present and not bool(module_state["open"]):
                    module_state["open"] = True
            for module in sorted(present):
                if module in state and bool(state[module]["open"]):
                    previous = state[module]
                    returns.append({
                        "project": project,
                        "worktree_id": worktree,
                        "module": module,
                        "origin_event_id": previous["event_id"],
                        "end_event_id": row["event_id"],
                        "observed": True,
                        # Strictly intervening calls: A, B, A has gap 1.
                        "distance_calls": index - int(previous["index"]) - 1,
                        "distance_ms": int(row["ts_ms"]) - int(previous["ts_ms"]),
                        "same_session": row["session_id"] == previous["session_id"],
                    })
                state[module] = {"index": index, "ts_ms": row["ts_ms"], "event_id": row["event_id"], "session_id": row["session_id"], "open": False}
        if rows:
            final = rows[-1]
            final_index = len(rows) - 1
            for module in sorted(state):
                module_state = state[module]
                if bool(module_state["open"]):
                    returns.append({
                        "project": project,
                        "worktree_id": worktree,
                        "module": module,
                        "origin_event_id": module_state["event_id"],
                        "end_event_id": final["event_id"],
                        "observed": False,
                        "distance_calls": final_index - int(module_state["index"]),
                        "distance_ms": int(final["ts_ms"]) - int(module_state["ts_ms"]),
                        "same_session": final["session_id"] == module_state["session_id"],
                    })

    coverage = []
    for project in project_order:
        vendors = sorted(vendor for candidate, vendor in source_stats if candidate == project and vendor != "ALL")
        for vendor in ["ALL", *vendors]:
            project_actions = [row for row in actions if row["project"] == project and (vendor == "ALL" or row["vendor"] == vendor)]
            project_calls = [row for row in calls if row["project"] == project and (vendor == "ALL" or row["vendor"] == vendor)]
            event_ids = {str(row["event_id"]) for row in project_calls}
            project_transitions = [row for row in transitions if row["project"] == project and row["previous_event_id"] in event_ids and row["current_event_id"] in event_ids]
            project_returns = [row for row in returns if row["project"] == project and bool(row["observed"]) and row["end_event_id"] in event_ids]
            module_names = {str(row["module"]) for row in project_actions}
            module_keys = {(str(row["worktree_id"]), str(row["module"])) for row in project_actions}
            stats = source_stats[(project, vendor)]
            coverage.append({
                "project": project,
                "vendor": vendor,
                "tool_events": stats["tool_events"],
                "status_ok_events": stats["status_ok"],
                "status_observed_events": stats["status_observed"],
                "status_fail_events": stats["status_fail"],
                "worktree_attributed_tool_events": stats["worktree_attributed_tool_events"],
                "source_action_rows": stats["source_action_rows"],
                "non_scope_action_rows": stats["non_scope_action_rows"],
                "retained_non_scope_action_rows": stats["retained_non_scope_action_rows"],
                "scope_action_rows": stats["scope_action_rows"],
                "scope_only_tool_events": stats["scope_only_tool_events"],
                "no_resolved_path_tool_events": stats["no_resolved_path_tool_events"],
                "failed_without_resolved_path": stats["failed_without_resolved_path"],
                "failed_status_action_rows": stats["failed_status_action_rows"],
                "path_resolved_units": len(project_actions),
                "ok_units": sum(row["status"] == "ok" for row in project_actions),
                "observed_units": sum(row["status"] == "observed" for row in project_actions),
                "identity_unknown_units": sum(not bool(row["identity_known"]) for row in project_actions),
                "resolved_event_ids": len(event_ids),
                "resolved_worktree_calls": len(project_calls),
                "worktrees": len({str(row["worktree_id"]) for row in project_calls}),
                "module_names": len(module_names),
                "module_keys": len(module_keys),
                "eligible_transitions": len(project_transitions),
                "observed_returns": len(project_returns),
                "allocation_qualified": vendor == "ALL" and len(project_actions) >= 100,
                "transition_qualified": vendor == "ALL" and len(project_transitions) >= 100 and len(module_keys) >= 2,
                "revisit_qualified": vendor == "ALL" and len(project_returns) >= 20 and len(module_keys) >= 2,
            })
    return actions, calls, transitions, returns, coverage


def top_module_keys(counts: Counter[str]) -> list[str]:
    admitted = sorted(counts, key=lambda key: (-counts[key], key))[:8]
    return sorted(admitted)


def action_bin(index: int, total: int) -> int:
    return min(59, math.floor(index * 60 / total)) if total else 0


def row_max_normalize(matrix: np.ndarray) -> np.ndarray:
    normalized = matrix.copy()
    for row_index in range(len(normalized)):
        maximum = normalized[row_index].max()
        if maximum:
            normalized[row_index] /= maximum
    return normalized


def derive_result_tables(
    actions: list[dict[str, object]],
    calls: list[dict[str, object]],
    transitions: list[dict[str, object]],
    returns: list[dict[str, object]],
) -> tuple[list[dict[str, object]], list[dict[str, object]], list[dict[str, object]]]:
    projects = list(dict.fromkeys(str(row["project"]) for row in actions))
    summary = []
    for project in projects:
        for status_scope in ["all", "ok"]:
            for stratum in ["read", "mutation"]:
                selected = [row for row in actions if row["project"] == project and row["stratum"] == stratum and (status_scope == "all" or row["status"] == "ok")]
                for artifact_class in CLASSES:
                    class_rows = [row for row in selected if row["artifact_class"] == artifact_class]
                    summary.append({
                        "project": project,
                        "family": "allocation",
                        "scope": status_scope,
                        "stratum": stratum,
                        "category": artifact_class,
                        "numerator": len(class_rows),
                        "denominator": len(selected),
                        "value": len(class_rows) / len(selected) if selected else "",
                        "fractional_numerator": sum(float(row["fractional_weight"]) for row in class_rows),
                        "fractional_denominator": sum(float(row["fractional_weight"]) for row in selected),
                    })
        for scope in ["all", "singleton_only"]:
            selected = [row for row in transitions if row["project"] == project and (scope == "all" or bool(row["singleton_only"]))]
            for kind in ["same_artifact", "same_module", "cross_module"]:
                count = sum(row["transition"] == kind for row in selected)
                summary.append({
                    "project": project, "family": "transition", "scope": scope,
                    "stratum": "", "category": kind, "numerator": count,
                    "denominator": len(selected), "value": count / len(selected) if selected else "",
                    "fractional_numerator": "", "fractional_denominator": "",
                })
        for observed in [True, False]:
            selected = [row for row in returns if row["project"] == project and bool(row["observed"]) == observed]
            call_values = sorted(int(row["distance_calls"]) for row in selected)
            wall_values = sorted(int(row["distance_ms"]) for row in selected)
            summary.append({
                "project": project, "family": "module_return", "scope": "observed" if observed else "right_censored",
                "stratum": "", "category": "distance", "numerator": len(selected),
                "denominator": len(selected), "value": float(np.median(call_values)) if call_values else "",
                "fractional_numerator": float(np.quantile(call_values, 0.9, method="higher")) if call_values else "",
                "fractional_denominator": float(np.median(wall_values)) if wall_values else "",
            })

    module_summary = []
    grouped_actions: dict[tuple[str, str, str], list[dict[str, object]]] = defaultdict(list)
    for row in actions:
        grouped_actions[(str(row["project"]), str(row["worktree_id"]), str(row["module"]))].append(row)
    for (project, worktree, module), rows in sorted(grouped_actions.items()):
        module_summary.append({
            "project": project, "worktree_id": worktree, "module": module,
            "action_units": len(rows),
            "read_units": sum(row["stratum"] == "read" for row in rows),
            "mutation_units": sum(row["stratum"] == "mutation" for row in rows),
            "resolved_calls": len({str(row["event_id"]) for row in rows}),
            "sessions": len({str(row["session_id"]) for row in rows}),
            "first_event_index": min(int(row["event_index"]) for row in rows),
            "last_event_index": max(int(row["event_index"]) for row in rows),
            "first_ts_ms": min(int(row["ts_ms"]) for row in rows),
            "last_ts_ms": max(int(row["ts_ms"]) for row in rows),
        })

    leader_changes = []
    lanes: dict[tuple[str, str], list[dict[str, object]]] = defaultdict(list)
    for row in calls:
        lanes[(str(row["project"]), str(row["worktree_id"]))].append(row)
    for (project, worktree), rows in sorted(lanes.items()):
        rows.sort(key=lambda row: (int(row["event_index"]), str(row["event_id"])))
        counts = Counter()
        previous_leaders: tuple[str, ...] = ()
        for call_rank, row in enumerate(rows, start=1):
            for module in set(filter(None, str(row["modules"]).split(";"))):
                counts[module] += 1
            maximum = max(counts.values(), default=0)
            leaders = tuple(sorted(module for module, count in counts.items() if count == maximum))
            if leaders != previous_leaders:
                leader_changes.append({
                    "project": project, "worktree_id": worktree,
                    "call_rank": call_rank, "event_id": row["event_id"],
                    "leaders": ";".join(leaders), "cumulative_call_count": maximum,
                })
                previous_leaders = leaders
    return summary, module_summary, leader_changes


def self_check() -> None:
    assert classify_path("tests/foo.rs") == "test"
    assert classify_path("docs/test_notes.md") == "test"
    assert classify_path("README") == "paper/docs"
    assert classify_path("src/config.rs") == "source"
    assert classify_path("Cargo.toml") == "config/build"
    assert classify_path("outputs/a.csv") == "data/input"  # extension precedence
    assert classify_path("assets/a.json") == "other"
    assert module_for("README.md") == "repo-root-files"
    assert module_for("src/main.rs") == "src"
    assert top_module_keys(Counter({"z": 2, "b": 3, "a": 3})) == ["a", "b", "z"]
    assert [action_bin(index, 2) for index in range(2)] == [0, 30]
    normalized = row_max_normalize(np.array([[0.0, 2.0], [0.0, 0.0]]))
    assert normalized.tolist() == [[0.0, 1.0], [0.0, 0.0]]
    synthetic_events = []
    synthetic_accesses = []
    specifications = [
        ("e0", "A", "src/a.rs", "read"),
        ("e1", "A", "src/a.rs", "write"),
        ("e2", "B", "src/b.rs", "read"),
        ("e3", "C", "docs/c.md", "read"),
        ("e4", "B", "src/b.rs", "read"),
    ]
    for index, (event_id, artifact_id, path, operation) in enumerate(specifications):
        event_actions = [{"worktree_id": "w", "path": path, "access": operation}]
        if event_id == "e1":
            event_actions.append({"worktree_id": "w", "path": "src/a2.rs", "access": "rename", "previous_path": path})
        synthetic_events.append({
            "id": event_id, "event_index": index, "ts_ms": index * 10,
            "session_id": "s1" if index < 3 else "s2", "vendor": "v",
            "status": "ok", "worktree_id": "w", "actions": event_actions,
        })
        for ordinal, action in enumerate(event_actions):
            synthetic_accesses.append({
                "project": "p", "worktree_id": "w", "event_index": str(index),
                "event_id": event_id, "ts_ms": str(index * 10),
                "session_id": "s1" if index < 3 else "s2", "action_ordinal": str(ordinal),
                "path": action["path"], "operation": action["access"], "scope": "False",
                "artifact_id": artifact_id, "previous_path": action.get("previous_path", ""),
            })
    synthetic_actions, _, synthetic_transitions, synthetic_returns, _ = derive([("p", synthetic_events)], synthetic_accesses)
    mutation_weights = [float(row["fractional_weight"]) for row in synthetic_actions if row["event_id"] == "e1"]
    assert math.isclose(sum(mutation_weights), 1.0)
    assert [row["transition"] for row in synthetic_transitions[:3]] == ["same_artifact", "same_module", "cross_module"]
    assert bool(synthetic_transitions[0]["singleton_only"])
    assert any(bool(row["observed"]) and row["module"] == "src" and int(row["distance_calls"]) == 1 for row in synthetic_returns)
    assert any(not bool(row["observed"]) and row["module"] == "docs" for row in synthetic_returns)


def plot(raw: Path, figures: Path) -> None:
    actions = read_csv(raw / "rq5-actions.csv")
    calls = read_csv(raw / "rq5-calls.csv")
    transitions = read_csv(raw / "rq5-transitions.csv")
    returns = read_csv(raw / "rq5-module-returns.csv")
    coverage = [row for row in read_csv(raw / "rq5-coverage.csv") if row["vendor"] == "ALL"]
    projects = [row["project"] for row in coverage]
    plt.rcParams["pdf.fonttype"] = 42
    plt.rcParams["ps.fonttype"] = 42

    figures.mkdir(parents=True, exist_ok=True)

    # F8a: keep the materially different ok-only sensitivity at full print size.
    allocation_fig, allocation_axes = plt.subplots(1, 2, figsize=(7.05, 4.65))
    y_positions = np.arange(len(projects) * 2)
    for axis_index, (axis, status_filter, title) in enumerate([
        (allocation_axes[0], None, "all path-resolved (ok + observed)"),
        (allocation_axes[1], "ok", "ok-only sensitivity"),
    ]):
        lefts = np.zeros(len(y_positions))
        totals = []
        values_by_class: dict[str, list[float]] = {name: [] for name in CLASSES}
        for project in projects:
            for stratum in ["read", "mutation"]:
                selected_rows = [row for row in actions if row["project"] == project and row["stratum"] == stratum and (status_filter is None or row["status"] == status_filter)]
                totals.append(len(selected_rows))
                for artifact_class in CLASSES:
                    values_by_class[artifact_class].append(sum(row["artifact_class"] == artifact_class for row in selected_rows) / len(selected_rows) if selected_rows else 0)
        for artifact_class, color in zip(CLASSES, CLASS_COLORS, strict=True):
            values = values_by_class[artifact_class]
            axis.barh(y_positions, values, left=lefts, color=color, height=0.72, label=artifact_class)
            lefts += np.array(values)
        labels = [f"{SHORT.get(project, project)} {'R' if stratum == 'read' else 'M'} (n={totals[index]:,})" for index, (project, stratum) in enumerate((project, stratum) for project in projects for stratum in ["read", "mutation"])]
        axis.set_yticks(y_positions, labels if axis_index == 0 else [f"R n={totals[i]:,}" if i % 2 == 0 else f"M n={totals[i]:,}" for i in range(len(totals))], fontsize=7)
        axis.invert_yaxis()
        axis.set_xlim(0, 1)
        axis.xaxis.set_major_formatter(PercentFormatter(1.0))
        axis.tick_params(axis="x", labelsize=7)
        axis.set_xlabel("primary units", fontsize=7)
        axis.set_title(title, fontsize=9, pad=5)
        axis.grid(axis="x", alpha=0.16)
    handles, labels = allocation_axes[0].get_legend_handles_labels()
    allocation_fig.suptitle("RQ3a: Artifact-type allocation and native-status sensitivity", fontsize=11, fontweight="bold", y=0.985)
    allocation_fig.legend(handles, labels, loc="upper center", bbox_to_anchor=(0.5, 0.925), ncol=4, fontsize=7, frameon=False)
    allocation_fig.text(0.5, 0.018, "R = read; M = mutation. `observed` is path-resolved activity with unknown outcome, not a confirmed effect.", ha="center", fontsize=7, color="#8b3e34")
    allocation_fig.subplots_adjust(top=0.80, bottom=0.12, left=0.25, right=0.985, wspace=0.46)
    allocation_fig.savefig(figures / "rq5-artifact-allocation.pdf")
    allocation_fig.savefig(figures / "rq5-artifact-allocation.png", dpi=200)
    plt.close(allocation_fig)

    # F8b: source-path spatial dynamics, separate from status sensitivity so
    # labels remain >= 7 pt at a two-column paper width.
    fig = plt.figure(figsize=(7.05, 8.9))
    outer = fig.add_gridspec(2, 1, height_ratios=[5.4, 2.2], hspace=0.42)
    heat_grid = outer[0].subgridspec(3, 2, hspace=0.55, wspace=0.67)
    cmap = LinearSegmentedColormap.from_list("activity", ["#f4f6f8", "#9ac7dd", "#135e82"])
    for project_index, project in enumerate(projects):
        axis = fig.add_subplot(heat_grid[project_index // 2, project_index % 2])
        project_calls = [row for row in calls if row["project"] == project]
        module_counts = Counter(f"{row['worktree_id']}:{module}" for row in project_calls for module in row["modules"].split(";") if module)
        selected = top_module_keys(module_counts)
        selected_set = set(selected)
        rows = selected + (["remainder"] if set(module_counts) - selected_set else [])
        matrix = np.zeros((len(rows), 60))
        ordered = sorted(project_calls, key=lambda row: (int(row["event_index"]), row["event_id"], row["worktree_id"]))
        for index, call in enumerate(ordered):
            column = action_bin(index, len(ordered))
            present = {f"{call['worktree_id']}:{module}" for module in call["modules"].split(";") if module}
            for module in present & selected_set:
                matrix[rows.index(module), column] += 1
            if present - selected_set and "remainder" in rows:
                matrix[rows.index("remainder"), column] += 1
        axis.imshow(row_max_normalize(matrix), aspect="auto", interpolation="nearest", cmap=cmap, vmin=0, vmax=1)
        labels = []
        worktree_count = len({key.split(":", 1)[0] for key in module_counts})
        for row_index, module in enumerate(rows):
            if module == "remainder":
                labels.append(f"remainder ({int(matrix[row_index].sum()):,})")
            else:
                worktree, name = module.split(":", 1)
                suffix = f"@{worktree[:4]}" if worktree_count > 1 else ""
                display_name = name if len(name) <= 17 else name[:16] + "…"
                labels.append(f"{display_name}{suffix} ({module_counts[module]:,})")
        axis.set_yticks(range(len(rows)), labels, fontsize=7)
        axis.set_xticks([0, 29, 59], ["0", "50", "100"], fontsize=7)
        axis.set_title(SHORT.get(project, project), fontsize=8, fontweight="bold", loc="left", pad=2)
        if project_index >= 4:
            axis.set_xlabel("native action order (%)", fontsize=7)

    bottom_grid = outer[1].subgridspec(1, 2, wspace=0.52)
    transition_axis = fig.add_subplot(bottom_grid[0, 0])
    return_axis = fig.add_subplot(bottom_grid[0, 1])
    transition_kinds = ["same_artifact", "same_module", "cross_module"]
    transition_colors = ["#2f78b7", "#75b798", "#e0964f"]
    lefts = [0.0] * len(projects)
    for kind, color in zip(transition_kinds, transition_colors, strict=True):
        values = []
        for project in projects:
            selected_rows = [row for row in transitions if row["project"] == project]
            values.append(sum(row["transition"] == kind for row in selected_rows) / len(selected_rows) if selected_rows else 0)
        transition_axis.barh(range(len(projects)), values, left=lefts, color=color, label=kind.replace("_", " "))
        lefts = [left + value for left, value in zip(lefts, values, strict=True)]
    transition_axis.set_yticks(range(len(projects)), [SHORT.get(project, project) for project in projects], fontsize=7)
    transition_axis.invert_yaxis()
    transition_axis.set_xlim(0, 1)
    transition_axis.xaxis.set_major_formatter(PercentFormatter(1.0))
    transition_axis.tick_params(axis="x", labelsize=7)
    transition_axis.set_xlabel("adjacent calls within worktree", fontsize=7)
    transition_axis.set_title("B. Source-path transitions", loc="left", fontweight="bold", fontsize=9)
    transition_axis.legend(fontsize=7, loc="lower center", bbox_to_anchor=(0.5, 1.10), ncol=3, frameon=False)
    transition_axis.grid(axis="x", alpha=0.16)

    positions = np.arange(len(projects))
    medians, p90s, counts = [], [], []
    revisit_qualified = {row["project"]: bool_text(row["revisit_qualified"]) for row in coverage}
    for project in projects:
        values = sorted(int(row["distance_calls"]) for row in returns if row["project"] == project and bool_text(row["observed"]))
        counts.append(len(values))
        admitted = revisit_qualified[project] and bool(values)
        medians.append(float(np.median(values)) if admitted else math.nan)
        p90s.append(float(np.quantile(values, 0.9, method="higher")) if admitted else math.nan)
    return_axis.scatter(medians, positions, color="#2f78b7", s=12, label="median", zorder=3)
    return_axis.scatter(p90s, positions, color="#d66b44", marker="|", s=80, label="p90", zorder=3)
    for index, (median, p90, count) in enumerate(zip(medians, p90s, counts, strict=True)):
        if math.isnan(median):
            return_axis.text(1.25, index, f"N/A (n={count}<20)", va="center", fontsize=7, color="#9a4a42")
        else:
            return_axis.plot([median, p90], [index, index], color="#9ba7ad", linewidth=1)
            return_axis.text(max(p90, 1) * 1.08, index, f"n={count:,}", va="center", fontsize=7)
    return_axis.set_yticks(positions, [SHORT.get(project, project) for project in projects], fontsize=7)
    return_axis.invert_yaxis()
    return_axis.set_xscale("log")
    return_axis.tick_params(axis="x", labelsize=7)
    return_axis.set_xlabel("path-resolved calls strictly between visits", fontsize=7)
    return_axis.set_title("C. Module-return distance", loc="left", fontweight="bold", fontsize=9)
    finite_p90 = [value for value in p90s if not math.isnan(value)]
    if finite_p90:
        return_axis.set_xlim(0.8, max(finite_p90) * 1.7)
    return_axis.legend(fontsize=7, loc="lower center", bbox_to_anchor=(0.5, 1.10), ncol=2, frameon=False)
    return_axis.grid(axis="x", alpha=0.16)

    qualified = {field: sum(bool_text(row[field]) for row in coverage) for field in ["allocation_qualified", "transition_qualified", "revisit_qualified"]}
    fig.suptitle("RQ3b: Worktree-module activity and source-path migration", fontsize=11, fontweight="bold", y=0.99)
    fig.text(0.17, 0.947, "A. Top (worktree, module) activity over native action order; row-max color only", fontsize=9, fontweight="bold")
    fig.text(0.5, 0.012, f"Activity is not duration, internal attention, importance, or productivity. Gates: transitions {qualified['transition_qualified']}/6; returns {qualified['revisit_qualified']}/6.", ha="center", fontsize=7, color="#8b3e34")
    fig.subplots_adjust(top=0.91, bottom=0.06, left=0.20, right=0.985)
    fig.savefig(figures / "rq5-activity-migration.pdf")
    fig.savefig(figures / "rq5-activity-migration.png", dpi=200)
    plt.close(fig)


def write_result(
    path: Path,
    coverage: list[dict[str, object]],
    summary: list[dict[str, object]],
    module_summary: list[dict[str, object]],
    leader_changes: list[dict[str, object]],
) -> None:
    totals = [row for row in coverage if row["vendor"] == "ALL"]
    lines = [
        "# RQ3 Workspace Activity Allocation and Migration",
        "",
        "Resolved means path-resolved, not confirmed effect. `observed` and `ok` statuses are retained and reported separately; duration, internal attention, importance, productivity, and causality are not measured.",
        "",
        "## Source reconciliation and gates",
        "",
        "| Project | Tool events (worktree) | Units ok/observed/unknown-ID | Calls event/lane | Module names/keys | Transitions | Returns | Gates A/T/R |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in totals:
        lines.append(
            f"| {row['project']} | {row['tool_events']} ({row['worktree_attributed_tool_events']}) | "
            f"{row['path_resolved_units']} ({row['ok_units']}/{row['observed_units']}/{row['identity_unknown_units']}) | "
            f"{row['resolved_event_ids']}/{row['resolved_worktree_calls']} | {row['module_names']}/{row['module_keys']} | "
            f"{row['eligible_transitions']} | {row['observed_returns']} | "
            f"{row['allocation_qualified']}/{row['transition_qualified']}/{row['revisit_qualified']} |"
        )
    lines.extend([
        "",
        "The vendor-stratified rows, scope-only calls, failed calls without a resolved path, status counts, and action-row reconciliation are in `raw/rq5-coverage.csv`.",
        "",
        "## Allocation status sensitivity",
        "",
        "| Project | Mutation dominant class: all | Mutation dominant class: ok-only | Total-variation shift |",
        "|---|---:|---:|---:|",
    ])
    for row in totals:
        project = str(row["project"])
        groups = {}
        for scope in ["all", "ok"]:
            selected = [item for item in summary if item["project"] == project and item["family"] == "allocation" and item["scope"] == scope and item["stratum"] == "mutation"]
            values = {str(item["category"]): float(item["value"]) if item["value"] != "" else 0.0 for item in selected}
            groups[scope] = values
        dominant_all = max(groups["all"], key=groups["all"].get)
        dominant_ok = max(groups["ok"], key=groups["ok"].get)
        shift = 0.5 * sum(abs(groups["all"][name] - groups["ok"][name]) for name in CLASSES)
        lines.append(
            f"| {project} | {dominant_all} {groups['all'][dominant_all]:.1%} | "
            f"{dominant_ok} {groups['ok'][dominant_ok]:.1%} | {shift:.1%} |"
        )
    lines.extend([
        "",
        "Exact action-weighted and Tool-call fractional allocations for every class/status/stratum are in `raw/rq5-summary.csv`; the difference between all path-resolved and ok-only activity is substantive and bounds interpretation of unknown-status events.",
        "",
        "## Transitions and return gaps",
        "",
        "| Project | Same artifact / module / cross (all) | Singleton-only n | Returns observed/censored | Intervening calls median/p90 |",
        "|---|---:|---:|---:|---:|",
    ])
    for row in totals:
        project = str(row["project"])
        transition_rows = [item for item in summary if item["project"] == project and item["family"] == "transition" and item["scope"] == "all"]
        transition_values = {str(item["category"]): float(item["value"]) if item["value"] != "" else 0.0 for item in transition_rows}
        singleton = next((int(item["denominator"]) for item in summary if item["project"] == project and item["family"] == "transition" and item["scope"] == "singleton_only"), 0)
        observed = next(item for item in summary if item["project"] == project and item["family"] == "module_return" and item["scope"] == "observed")
        censored = next(item for item in summary if item["project"] == project and item["family"] == "module_return" and item["scope"] == "right_censored")
        return_text = (
            f"{float(observed['value']):.1f}/{float(observed['fractional_numerator']):.1f}"
            if bool(row["revisit_qualified"]) else "N/A (coverage only)"
        )
        lines.append(
            f"| {project} | {transition_values['same_artifact']:.1%} / {transition_values['same_module']:.1%} / {transition_values['cross_module']:.1%} | "
            f"{singleton} | {observed['numerator']}/{censored['numerator']} | {return_text} |"
        )
    lines.extend([
        "",
        f"Module-level access/mutation/session/time rows: {len(module_summary)}. Cumulative leader-change rows: {len(leader_changes)}. Both are exported for exact inspection; no force-layout coordinate, entropy, cooling, internal-attention, or importance claim is made.",
    ])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--rq1-root", type=Path, required=True)
    parser.add_argument("--rq4-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    verify_inputs(args.rq1_root)
    access_path = args.rq4_root / "rq4-accesses.csv"
    if sha256(access_path) != RQ4_ACCESS_SHA256:
        raise ValueError("frozen RQ4 access hash mismatch")
    self_check()
    projects = load_projects(args.rq1_root)
    accesses = read_csv(access_path)
    actions, calls, transitions, returns, coverage = derive(projects, accesses)
    del projects, accesses
    gc.collect()
    total_coverage = [row for row in coverage if row["vendor"] == "ALL"]
    if sum(int(row["path_resolved_units"]) for row in total_coverage) != len(actions):
        raise ValueError("primary units do not reconcile")
    for project in [row["project"] for row in total_coverage]:
        for stratum in ["read", "mutation"]:
            selected = [row for row in actions if row["project"] == project and row["stratum"] == stratum]
            weight = sum(float(row["fractional_weight"]) for row in selected)
            calls_in_stratum = len({(row["worktree_id"], row["event_id"]) for row in selected})
            if not math.isclose(weight, calls_in_stratum, abs_tol=1e-8):
                raise ValueError(f"fractional weights do not reconcile: {project}/{stratum}")
    raw = args.output / "raw"
    summary, module_summary, leader_changes = derive_result_tables(actions, calls, transitions, returns)
    write_csv(raw / "rq5-actions.csv", actions, list(actions[0]))
    write_csv(raw / "rq5-calls.csv", calls, list(calls[0]))
    write_csv(raw / "rq5-transitions.csv", transitions, list(transitions[0]))
    write_csv(raw / "rq5-module-returns.csv", returns, list(returns[0]))
    write_csv(raw / "rq5-coverage.csv", coverage, list(coverage[0]))
    write_csv(raw / "rq5-summary.csv", summary, list(summary[0]))
    write_csv(raw / "rq5-module-summary.csv", module_summary, list(module_summary[0]))
    write_csv(raw / "rq5-leader-changes.csv", leader_changes, list(leader_changes[0]))
    write_result(args.output / "result.md", coverage, summary, module_summary, leader_changes)
    plot(raw, args.output / "figures")


if __name__ == "__main__":
    main()
