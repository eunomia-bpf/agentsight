#!/usr/bin/env python3
"""Derive and render reviewed source-session component continuity (RQ4)."""

from __future__ import annotations

import argparse
import csv
from collections import Counter, defaultdict
from pathlib import Path, PurePosixPath

import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter

plt.rcParams["pdf.fonttype"] = 42
plt.rcParams["ps.fonttype"] = 42

from plot_rq2 import load_projects, read_csv, verify_inputs, write_csv


SHORT = {
    "agentsight": "AgentSight",
    "ActPlane": "ActPlane",
    "bpf-developer-tutorial": "BPF tutorial",
    "eunomia.dev": "eunomia.dev",
    "agentskill-observability-paper": "AgentSkill paper",
    "academic-writing-skills": "Writing skills",
}

TINY = {
    "agentsight": "AS",
    "ActPlane": "AP",
    "bpf-developer-tutorial": "BPF",
    "eunomia.dev": "EU",
    "agentskill-observability-paper": "Skill",
    "academic-writing-skills": "Write",
}

PREFIX_CLASSES = [
    "predecessor_artifact",
    "predecessor_module",
    "other_resolved_artifact",
    "other_resolved_scope",
    "no_resolved_path",
]

FIRST_STATES = [
    "predecessor_mutated",
    "predecessor_accessed",
    "earlier_history",
    "confirmed_create",
    "first_observed_existing",
    "unknown_lineage",
]


def module_for(path: str) -> str:
    parts = PurePosixPath(path).parts
    return parts[0] if len(parts) > 1 else "repo-root-files"


def bool_text(value: object) -> bool:
    return str(value).lower() == "true"


def pre_mutation_events(events: list[dict[str, object]], first_index: int | None) -> list[dict[str, object]]:
    if first_index is None:
        return []
    return [event for event in events if int(event["event_index"]) < first_index]


def prefix_class(
    event_accesses: list[dict[str, object]],
    predecessor_accessed: set[str],
    predecessor_modules: set[str],
) -> str:
    identities = {
        str(row["artifact_id"])
        for row in event_accesses
        if row["artifact_id"] and not bool(row["scope"])
    }
    modules = {str(row["module"]) for row in event_accesses}
    if identities & predecessor_accessed:
        return "predecessor_artifact"
    if modules & predecessor_modules:
        return "predecessor_module"
    if any(not bool(row["scope"]) for row in event_accesses):
        return "other_resolved_artifact"
    if event_accesses:
        return "other_resolved_scope"
    return "no_resolved_path"


def project_events(
    projects: list[tuple[str, list[dict[str, object]]]],
    artifacts: list[dict[str, str]],
    mutations: list[dict[str, str]],
) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    mutation_by_event: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in mutations:
        mutation_by_event[(row["project"], row["event_id"])].append(row)

    expected_artifacts: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in artifacts:
        expected_artifacts[row["project"]].append(row)
    for rows in expected_artifacts.values():
        rows.sort(key=lambda row: int(row["artifact_id"].rsplit("a", 1)[1]))

    lane_events: list[dict[str, object]] = []
    accesses: list[dict[str, object]] = []
    live: dict[tuple[str, str], dict[str, str]] = defaultdict(dict)
    for project, events in projects:
        artifact_cursor = 0

        def new_identity(event_index: int, path: str) -> str:
            nonlocal artifact_cursor
            rows = expected_artifacts[project]
            if artifact_cursor >= len(rows):
                raise ValueError(f"identity replay created an extra artifact in {project}")
            artifact = rows[artifact_cursor]
            artifact_cursor += 1
            if int(artifact["first_event_index"]) != event_index or artifact["first_path"] != path:
                raise ValueError(
                    f"identity replay diverged in {project}: expected "
                    f"{artifact['artifact_id']}@{artifact['first_event_index']}:{artifact['first_path']}, "
                    f"got event {event_index}:{path}"
                )
            return artifact["artifact_id"]

        for event_index, event in enumerate(events):
            event_id = str(event["id"])
            home = str(event["worktree_id"]) if event.get("worktree_id") else ""
            target_worktrees = {
                str(action["worktree_id"])
                for action in event.get("actions", [])
                if action.get("worktree_id")
            }
            if home:
                target_worktrees.add(home)
            event_mutations = mutation_by_event[(project, event_id)]
            for worktree in sorted(target_worktrees):
                lane_events.append({
                    "project": project,
                    "worktree_id": worktree,
                    "event_index": event_index,
                    "event_id": event_id,
                    "ts_ms": int(event["ts_ms"]),
                    "session_id": str(event["session_id"]),
                    "home_worktree": worktree == home,
                    "mutation_rows": sum(row["worktree_id"] == worktree for row in event_mutations),
                })

            event_accesses = []
            for action_ordinal, action in enumerate(event.get("actions", [])):
                worktree = action.get("worktree_id")
                path = action.get("path")
                if not worktree or not path:
                    continue
                worktree = str(worktree)
                path = str(path)
                scope = bool(action.get("scope", False))
                operation = str(action.get("access", "read"))
                previous_path = str(action.get("previous_path", ""))
                identity = live[(project, worktree)].get(path, "")
                if not scope:
                    if operation == "rename":
                        # Match RQ1 apply_action exactly: destination replacement
                        # happens first; only an explicit same-worktree source
                        # preserves lineage. Status does not suppress lifecycle.
                        live[(project, worktree)].pop(path, None)
                        previous_worktree = str(action.get("previous_worktree_id", ""))
                        source = ""
                        if previous_path and previous_worktree == worktree:
                            source = live[(project, worktree)].pop(previous_path, "")
                        identity = source or new_identity(event_index, path)
                        live[(project, worktree)][path] = identity
                    else:
                        identity = live[(project, worktree)].get(path, "")
                        if not identity:
                            identity = new_identity(event_index, path)
                            live[(project, worktree)][path] = identity
                        if operation == "delete":
                            live[(project, worktree)].pop(path, None)
                access_row = {
                    "project": project,
                    "worktree_id": worktree,
                    "event_index": event_index,
                    "event_id": event_id,
                    "ts_ms": int(event["ts_ms"]),
                    "session_id": str(event["session_id"]),
                    "action_ordinal": action_ordinal,
                    "path": path,
                    "module": module_for(path),
                    "operation": operation,
                    "scope": scope,
                    "artifact_id": identity,
                    "previous_path": previous_path,
                }
                accesses.append(access_row)
                event_accesses.append(access_row)
            # Every confirmed mutation must resolve to the RQ1 artifact ID.
            replayed = {
                (str(row["worktree_id"]), str(row["path"]), str(row["operation"])): str(row["artifact_id"])
                for row in event_accesses
                if not bool(row["scope"])
            }
            for mutation in event_mutations:
                key = (mutation["worktree_id"], mutation["path"], mutation["operation"])
                if replayed.get(key) != mutation["artifact_id"]:
                    raise ValueError(f"confirmed mutation identity mismatch: {project}/{event_id}/{key}")
        if artifact_cursor != len(expected_artifacts[project]):
            raise ValueError(
                f"identity replay did not consume all artifacts in {project}: "
                f"{artifact_cursor}/{len(expected_artifacts[project])}"
            )
    return lane_events, accesses


def build_components(lane_events: list[dict[str, object]]) -> tuple[list[dict[str, object]], dict[tuple[str, str, int], list[dict[str, object]]]]:
    by_session: dict[tuple[str, str, str], list[dict[str, object]]] = defaultdict(list)
    for row in lane_events:
        by_session[(str(row["project"]), str(row["worktree_id"]), str(row["session_id"]))].append(row)
    intervals: dict[tuple[str, str], list[dict[str, object]]] = defaultdict(list)
    for (project, worktree, session), rows in by_session.items():
        intervals[(project, worktree)].append({
            "session_id": session,
            "start_ms": min(int(row["ts_ms"]) for row in rows),
            "end_ms": max(int(row["ts_ms"]) for row in rows),
            "rows": rows,
        })

    components = []
    component_events: dict[tuple[str, str, int], list[dict[str, object]]] = {}
    for (project, worktree), rows in intervals.items():
        rows.sort(key=lambda row: (int(row["start_ms"]), int(row["end_ms"]), str(row["session_id"])))
        groups: list[list[dict[str, object]]] = []
        current: list[dict[str, object]] = []
        current_end = -1
        for row in rows:
            if current and int(row["start_ms"]) > current_end:
                groups.append(current)
                current = []
                current_end = -1
            current.append(row)
            current_end = max(current_end, int(row["end_ms"]))
        if current:
            groups.append(current)
        for component_index, group in enumerate(groups):
            unique_events = {
                str(event["event_id"]): event
                for interval in group
                for event in interval["rows"]
            }
            events = sorted(unique_events.values(), key=lambda row: (int(row["event_index"]), str(row["event_id"])))
            key = (project, worktree, component_index)
            component_events[key] = events
            components.append({
                "project": project,
                "worktree_id": worktree,
                "component_index": component_index,
                "start_ms": min(int(row["start_ms"]) for row in group),
                "end_ms": max(int(row["end_ms"]) for row in group),
                "session_count": len(group),
                "session_ids": ";".join(sorted(str(row["session_id"]) for row in group)),
                "action_count": len(events),
                "mutation_rows": sum(int(event["mutation_rows"]) for event in events),
            })
    return components, component_events


def first_state(
    artifact: dict[str, str],
    predecessor_mutated: set[str],
    predecessor_accessed: set[str],
    earlier: set[str],
    next_event_indexes: set[int],
) -> str:
    artifact_id = artifact["artifact_id"]
    if artifact_id in predecessor_mutated:
        return "predecessor_mutated"
    if artifact_id in predecessor_accessed:
        return "predecessor_accessed"
    if artifact_id in earlier:
        return "earlier_history"
    if artifact["birth_state"] == "confirmed_create" and int(artifact["first_event_index"]) in next_event_indexes:
        return "confirmed_create"
    if artifact["birth_state"] == "left_censored_existing":
        return "first_observed_existing"
    return "unknown_lineage"


def derive_boundaries(
    components: list[dict[str, object]],
    component_events: dict[tuple[str, str, int], list[dict[str, object]]],
    accesses: list[dict[str, object]],
    artifacts: list[dict[str, str]],
    mutations: list[dict[str, str]],
) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    access_by_key: dict[tuple[str, str, str], list[dict[str, object]]] = defaultdict(list)
    for row in accesses:
        access_by_key[(str(row["project"]), str(row["worktree_id"]), str(row["event_id"]))].append(row)
    mutation_by_key: dict[tuple[str, str, str], list[dict[str, str]]] = defaultdict(list)
    for row in mutations:
        mutation_by_key[(row["project"], row["worktree_id"], row["event_id"])].append(row)
    artifact_by_id = {(row["project"], row["worktree_id"], row["artifact_id"]): row for row in artifacts}
    by_lane: dict[tuple[str, str], list[dict[str, object]]] = defaultdict(list)
    for row in components:
        by_lane[(str(row["project"]), str(row["worktree_id"]))].append(row)

    boundaries = []
    prefix_rows = []
    for (project, worktree), lane_components in by_lane.items():
        lane_components.sort(key=lambda row: int(row["component_index"]))
        earlier_artifacts: set[str] = set()
        for previous, current in zip(lane_components, lane_components[1:]):
            previous_events = component_events[(project, worktree, int(previous["component_index"]))]
            current_events = component_events[(project, worktree, int(current["component_index"]))]
            previous_ids = {str(row["event_id"]) for row in previous_events}
            current_ids = {str(row["event_id"]) for row in current_events}
            current_indexes = {int(row["event_index"]) for row in current_events}
            predecessor_accessed = {
                str(access["artifact_id"])
                for event_id in previous_ids
                for access in access_by_key[(project, worktree, event_id)]
                if access["artifact_id"] and not bool(access["scope"])
            }
            predecessor_modules = {
                str(access["module"])
                for event_id in previous_ids
                for access in access_by_key[(project, worktree, event_id)]
            }
            predecessor_mutated = {
                mutation["artifact_id"]
                for event_id in previous_ids
                for mutation in mutation_by_key[(project, worktree, event_id)]
            }
            current_mutations = [
                mutation
                for event_id in current_ids
                for mutation in mutation_by_key[(project, worktree, event_id)]
            ]
            mutation_event_indexes = {
                int(event["event_index"])
                for event in current_events
                if mutation_by_key[(project, worktree, str(event["event_id"]))]
            }
            first_index = min(mutation_event_indexes) if mutation_event_indexes else None
            # A component without a mutation contributes only to the separate
            # terminal no-mutation outcome. It has no defined pre-mutation
            # prefix and must not be pooled into Panel B.
            prefix_events = pre_mutation_events(current_events, first_index)
            prefix_counter = Counter()
            for event in prefix_events:
                event_accesses = access_by_key[(project, worktree, str(event["event_id"]))]
                category = prefix_class(event_accesses, predecessor_accessed, predecessor_modules)
                prefix_counter[category] += 1
                prefix_rows.append({
                    "project": project,
                    "worktree_id": worktree,
                    "previous_component": previous["component_index"],
                    "next_component": current["component_index"],
                    "event_id": event["event_id"],
                    "event_index": event["event_index"],
                    "prefix_class": category,
                })

            current_artifacts = {row["artifact_id"] for row in current_mutations}
            current_modules = {module_for(row["path"]) for row in current_mutations}
            artifact_overlap = (
                len(current_artifacts & predecessor_accessed) / len(current_artifacts)
                if current_artifacts and predecessor_accessed else None
            )
            module_overlap = (
                len(current_modules & predecessor_modules) / len(current_modules)
                if current_modules and predecessor_modules else None
            )
            first_mutations = [row for row in current_mutations if int(row["event_index"]) == first_index] if first_index is not None else []
            state_counter = Counter()
            for mutation in {row["artifact_id"]: row for row in first_mutations}.values():
                artifact = artifact_by_id[(project, worktree, mutation["artifact_id"])]
                state_counter[first_state(artifact, predecessor_mutated, predecessor_accessed, earlier_artifacts, current_indexes)] += 1

            row = {
                "project": project,
                "worktree_id": worktree,
                "previous_component": previous["component_index"],
                "next_component": current["component_index"],
                "previous_sessions": previous["session_count"],
                "next_sessions": current["session_count"],
                "gap_ms": int(current["start_ms"]) - int(previous["end_ms"]),
                "next_action_count": current["action_count"],
                "no_observed_mutation": first_index is None,
                "first_mutation_action_step": "" if first_index is None else 1 + sum(int(event["event_index"]) < first_index for event in current_events),
                "first_mutation_delay_ms": "" if first_index is None else next(int(event["ts_ms"]) for event in current_events if int(event["event_index"]) == first_index) - int(current["start_ms"]),
                "prefix_actions": len(prefix_events),
                "predecessor_artifact_count": len(predecessor_accessed),
                "predecessor_module_count": len(predecessor_modules),
                "next_mutated_artifact_count": len(current_artifacts),
                "next_mutated_module_count": len(current_modules),
                "artifact_overlap": "" if artifact_overlap is None else artifact_overlap,
                "module_overlap": "" if module_overlap is None else module_overlap,
            }
            row.update({f"prefix_{name}": prefix_counter[name] for name in PREFIX_CLASSES})
            row.update({f"first_{name}": state_counter[name] for name in FIRST_STATES})
            boundaries.append(row)
            earlier_artifacts.update(predecessor_accessed)
            earlier_artifacts.update(predecessor_mutated)
        if lane_components:
            last = lane_components[-1]
            for event in component_events[(project, worktree, int(last["component_index"]))]:
                for access in access_by_key[(project, worktree, str(event["event_id"]))]:
                    if access["artifact_id"]:
                        earlier_artifacts.add(str(access["artifact_id"]))
    return boundaries, prefix_rows


def plot(raw: Path, figures: Path) -> None:
    boundaries = read_csv(raw / "rq4-boundaries.csv")
    components = read_csv(raw / "rq4-components.csv")
    projects = list(dict.fromkeys(row["project"] for row in boundaries))
    colors = dict(zip(projects, plt.get_cmap("tab10").colors, strict=False))
    # Paper-width vertical composition preserves the mental map without
    # shrinking five diagnostic panels from a panoramic canvas.
    fig = plt.figure(figsize=(7.05, 8.3))
    grid = fig.add_gridspec(
        3,
        2,
        height_ratios=[1.0, 1.05, 1.15],
        wspace=0.42,
        hspace=0.58,
    )
    no_mut_axis = fig.add_subplot(grid[0, 0])
    timing_axis = fig.add_subplot(grid[0, 1])
    prefix_axis = fig.add_subplot(grid[1, :])
    overlap_axis = fig.add_subplot(grid[2, 0])
    state_axis = fig.add_subplot(grid[2, 1])

    no_rates = []
    for project in projects:
        rows = [row for row in boundaries if row["project"] == project]
        no_rates.append(sum(bool_text(row["no_observed_mutation"]) for row in rows) / len(rows))
    no_mut_axis.bar(range(len(projects)), no_rates, color=[colors[p] for p in projects])
    no_mut_axis.set_ylim(0, 1)
    no_mut_axis.yaxis.set_major_formatter(PercentFormatter(1.0))
    no_mut_axis.set_xticks(
        range(len(projects)),
        [TINY.get(project, project) for project in projects],
        fontsize=7,
    )
    no_mut_axis.set_ylabel("No mutation")
    no_mut_axis.set_title("A. No mutation after boundary")
    for index, project in enumerate(projects):
        rows = [row for row in boundaries if row["project"] == project]
        no_mut_axis.text(index, min(no_rates[index] + 0.05, 0.96), f"{sum(bool_text(row['no_observed_mutation']) for row in rows)}/{len(rows)}", ha="center", fontsize=7)

    for project in projects:
        values = sorted(int(row["first_mutation_action_step"]) for row in boundaries if row["project"] == project and row["first_mutation_action_step"])
        if values:
            xs = sorted(set(values))
            ys = [sum(value <= x for value in values) / len(values) for x in xs]
            timing_axis.step(xs, ys, where="post", color=colors[project], label=f"{SHORT.get(project, project)} (n={len(values)})")
    timing_axis.set_xscale("log")
    timing_axis.set_ylim(0, 1.02)
    timing_axis.set_xlabel("Tool actions to first mutation")
    timing_axis.set_ylabel("Conditional share")
    timing_axis.set_title("B. Actions to first mutation")
    timing_axis.grid(alpha=0.2)
    timing_axis.legend(fontsize=7, frameon=False)

    bottoms = [0.0] * len(projects)
    palette = ["#2f78b7", "#65a9cf", "#76b77a", "#d8a24a", "#8a8f98"]
    for category, color in zip(PREFIX_CLASSES, palette, strict=True):
        values = []
        for project in projects:
            rows = [row for row in boundaries if row["project"] == project]
            total = sum(int(row["prefix_actions"]) for row in rows)
            values.append(sum(int(row[f"prefix_{category}"]) for row in rows) / total if total else 0)
        prefix_axis.barh(range(len(projects)), values, left=bottoms, color=color, label=category.replace("_", " "))
        bottoms = [left + value for left, value in zip(bottoms, values, strict=True)]
    prefix_axis.set_yticks(range(len(projects)), [SHORT.get(project, project) for project in projects])
    prefix_axis.invert_yaxis()
    prefix_axis.xaxis.set_major_formatter(PercentFormatter(1.0))
    prefix_axis.set_xlabel("Pre-mutation Tool-event composition")
    prefix_axis.set_title("C. Mutation-observed prefix composition")
    prefix_axis.legend(
        fontsize=7,
        loc="upper center",
        bbox_to_anchor=(0.5, -0.19),
        ncol=3,
        frameon=False,
    )
    prefix_axis.grid(axis="x", alpha=0.2)

    for project_index, project in enumerate(projects):
        rows = [row for row in boundaries if row["project"] == project]
        artifact = [float(row["artifact_overlap"]) for row in rows if row["artifact_overlap"]]
        module = [float(row["module_overlap"]) for row in rows if row["module_overlap"]]
        for offset, values, marker in [(-0.12, artifact, "o"), (0.12, module, "x")]:
            for ordinal, value in enumerate(values):
                jitter = ((ordinal % 7) - 3) * 0.012
                overlap_axis.scatter(project_index + offset + jitter, value, color=colors[project], marker=marker, s=12, alpha=0.55)
    overlap_axis.set_xticks(
        range(len(projects)),
        [TINY.get(project, project) for project in projects],
        fontsize=7,
    )
    overlap_axis.set_ylim(0, 1.02)
    overlap_axis.yaxis.set_major_formatter(PercentFormatter(1.0))
    overlap_axis.set_ylabel("Unique next-mutation overlap")
    overlap_axis.set_title("D. Artifact ○ / module × continuity")
    overlap_axis.grid(axis="y", alpha=0.2)

    bottoms = [0.0] * len(projects)
    state_colors = plt.get_cmap("Set2").colors
    for state, color in zip(FIRST_STATES, state_colors, strict=False):
        values = []
        for project in projects:
            rows = [row for row in boundaries if row["project"] == project]
            total = sum(int(row[f"first_{name}"]) for row in rows for name in FIRST_STATES)
            values.append(sum(int(row[f"first_{state}"]) for row in rows) / total if total else 0)
        state_axis.barh(range(len(projects)), values, left=bottoms, color=color, label=state.replace("_", " "))
        bottoms = [left + value for left, value in zip(bottoms, values, strict=True)]
    state_axis.set_yticks(
        range(len(projects)),
        [TINY.get(project, project) for project in projects],
        fontsize=7,
    )
    state_axis.invert_yaxis()
    state_axis.xaxis.set_major_formatter(PercentFormatter(1.0))
    state_axis.set_xlabel("First-mutation artifact identities")
    state_axis.set_title("E. First-artifact provenance")
    handles, labels = state_axis.get_legend_handles_labels()
    short_labels = [
        "prior mutated",
        "prior accessed",
        "earlier history",
        "created",
        "existing",
        "unknown",
    ]
    fig.legend(
        handles,
        short_labels[:len(labels)],
        fontsize=7,
        loc="lower center",
        bbox_to_anchor=(0.5, 0.135),
        ncol=3,
        frameon=False,
    )
    state_axis.set_xlabel("")
    state_axis.grid(axis="x", alpha=0.2)

    coverage_rows = []
    for project in projects:
        project_components = [row for row in components if row["project"] == project]
        project_boundaries = [row for row in boundaries if row["project"] == project]
        mutation_observed = [
            row for row in project_boundaries if not bool_text(row["no_observed_mutation"])
        ]
        prefix_actions = sum(int(row["prefix_actions"]) for row in project_boundaries)
        overlap_defined = sum(bool(row["artifact_overlap"]) for row in project_boundaries)
        resolved_prefix = sum(
            int(row["prefix_actions"]) - int(row["prefix_no_resolved_path"]) > 0
            for row in mutation_observed
        )
        coverage_rows.append(
            [
                TINY.get(project, project),
                len(project_components),
                len(project_boundaries),
                len(mutation_observed),
                prefix_actions,
                overlap_defined,
                resolved_prefix,
            ]
        )
    coverage_axis = fig.add_axes([0.18, 0.035, 0.785, 0.10])
    coverage_axis.axis("off")
    coverage_table = coverage_axis.table(
        cellText=coverage_rows,
        colLabels=["project", "C", "B", "M", "P", "O", "R"],
        cellLoc="center",
        bbox=[0.0, 0.0, 1.0, 0.73],
    )
    coverage_table.auto_set_font_size(False)
    coverage_table.set_fontsize(7)
    coverage_table.scale(1.0, 0.92)
    coverage_axis.text(
        0.5,
        0.92,
        "Estimator coverage: C components; B boundaries; M mutation-observed; P prefix actions\n"
        "O overlap-defined; R resolved-prefix boundaries",
        ha="center",
        va="center",
        fontsize=7,
    )

    fig.text(
        0.5,
        0.006,
        "All four-project gates stopped: component continuity only; not a reset, resume, memory, or forgetting estimate.",
        ha="center",
        fontsize=7,
        color="#a33a32",
    )
    fig.subplots_adjust(top=0.975, bottom=0.23, left=0.18, right=0.965)
    figures.mkdir(parents=True, exist_ok=True)
    fig.savefig(figures / "rq4-component-continuity.pdf")
    fig.savefig(figures / "rq4-component-continuity.png", dpi=180)
    plt.close(fig)


def write_result(path: Path, components: list[dict[str, object]], boundaries: list[dict[str, object]]) -> None:
    projects = list(dict.fromkeys(str(row["project"]) for row in components))
    lines = [
        "# RQ4 Source-Session Component Continuity",
        "",
        "Coverage/within-case evidence only. Frozen records do not identify portable top-level/child roles, and fewer than four projects meet the 20-boundary gate.",
        "",
        "| Project | Components | Boundaries | With first mutation | Artifact-overlap defined | Module-overlap defined |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for project in projects:
        project_components = [row for row in components if row["project"] == project]
        project_boundaries = [row for row in boundaries if row["project"] == project]
        lines.append(
            f"| {project} | {len(project_components)} | {len(project_boundaries)} | "
            f"{sum(not bool(row['no_observed_mutation']) for row in project_boundaries)} | "
            f"{sum(row['artifact_overlap'] != '' for row in project_boundaries)} | "
            f"{sum(row['module_overlap'] != '' for row in project_boundaries)} |"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def self_check() -> None:
    rows = [
        {"project": "p", "worktree_id": "w", "session_id": "A", "event_id": "a", "event_index": 0, "ts_ms": 0, "mutation_rows": 0},
        {"project": "p", "worktree_id": "w", "session_id": "A", "event_id": "b", "event_index": 1, "ts_ms": 100, "mutation_rows": 0},
        {"project": "p", "worktree_id": "w", "session_id": "B", "event_id": "c", "event_index": 2, "ts_ms": 10, "mutation_rows": 0},
        {"project": "p", "worktree_id": "w", "session_id": "B", "event_id": "d", "event_index": 3, "ts_ms": 20, "mutation_rows": 0},
        {"project": "p", "worktree_id": "w", "session_id": "C", "event_id": "e", "event_index": 4, "ts_ms": 30, "mutation_rows": 0},
        {"project": "p", "worktree_id": "w", "session_id": "C", "event_id": "f", "event_index": 5, "ts_ms": 40, "mutation_rows": 0},
    ]
    components, _ = build_components(rows)
    assert len(components) == 1

    # Equal endpoints overlap; worktrees remain separate lanes.
    equal = [
        {"project": "p", "worktree_id": "w1", "session_id": "A", "event_id": "a", "event_index": 0, "ts_ms": 0, "mutation_rows": 0},
        {"project": "p", "worktree_id": "w1", "session_id": "A", "event_id": "b", "event_index": 1, "ts_ms": 10, "mutation_rows": 0},
        {"project": "p", "worktree_id": "w1", "session_id": "B", "event_id": "c", "event_index": 2, "ts_ms": 10, "mutation_rows": 0},
        {"project": "p", "worktree_id": "w1", "session_id": "B", "event_id": "d", "event_index": 3, "ts_ms": 20, "mutation_rows": 0},
        {"project": "p", "worktree_id": "w2", "session_id": "A", "event_id": "e", "event_index": 4, "ts_ms": 5, "mutation_rows": 0},
    ]
    equal_components, _ = build_components(equal)
    assert Counter(row["worktree_id"] for row in equal_components) == Counter({"w1": 1, "w2": 1})

    # No-mutation components have no pre-mutation prefix.
    assert pre_mutation_events([{"event_index": 1}], None) == []
    assert pre_mutation_events([{"event_index": 1}, {"event_index": 2}], 2) == [{"event_index": 1}]

    # Multi-path events obey the frozen highest-priority classification.
    synthetic_accesses = [
        {"artifact_id": "other", "module": "old", "scope": False},
        {"artifact_id": "prior", "module": "new", "scope": False},
    ]
    assert prefix_class(synthetic_accesses, {"prior"}, {"old"}) == "predecessor_artifact"
    assert prefix_class([{"artifact_id": "", "module": "old", "scope": True}], set(), {"old"}) == "predecessor_module"
    assert prefix_class([], set(), set()) == "no_resolved_path"

    # Exact RQ1 lifecycle replay: an observed rename preserves lineage, an
    # observed delete closes it, and a subsequent create starts a new identity.
    synthetic_events = [{
        "id": "e0", "ts_ms": 0, "session_id": "s", "worktree_id": "w", "status": "observed",
        "actions": [{"worktree_id": "w", "path": "a", "access": "read"}],
    }, {
        "id": "e1", "ts_ms": 1, "session_id": "s", "worktree_id": "w", "status": "observed",
        "actions": [{"worktree_id": "w", "path": "b", "access": "rename", "previous_path": "a", "previous_worktree_id": "w"}],
    }, {
        "id": "e2", "ts_ms": 2, "session_id": "s", "worktree_id": "w", "status": "observed",
        "actions": [{"worktree_id": "w", "path": "b", "access": "delete"}],
    }, {
        "id": "e3", "ts_ms": 3, "session_id": "s2", "worktree_id": "w", "status": "ok",
        "actions": [{"worktree_id": "w", "path": "b", "access": "create"}],
    }]
    synthetic_artifacts = [
        {"project": "p", "artifact_id": "p:a00000001", "first_event_index": "0", "first_path": "a"},
        {"project": "p", "artifact_id": "p:a00000002", "first_event_index": "3", "first_path": "b"},
    ]
    synthetic_mutations = [{"project": "p", "event_id": "e3", "worktree_id": "w", "path": "b", "operation": "create", "artifact_id": "p:a00000002"}]
    _, replayed = project_events([("p", synthetic_events)], synthetic_artifacts, synthetic_mutations)
    assert [row["artifact_id"] for row in replayed] == ["p:a00000001", "p:a00000001", "p:a00000001", "p:a00000002"]

    # Every first-mutation state is reachable and exclusive.
    base = {"artifact_id": "x", "birth_state": "confirmed_create", "first_event_index": "7"}
    assert first_state(base, {"x"}, set(), set(), {7}) == "predecessor_mutated"
    assert first_state(base, set(), {"x"}, set(), {7}) == "predecessor_accessed"
    assert first_state(base, set(), set(), {"x"}, {7}) == "earlier_history"
    assert first_state(base, set(), set(), set(), {7}) == "confirmed_create"
    assert first_state({**base, "birth_state": "left_censored_existing"}, set(), set(), set(), {7}) == "first_observed_existing"
    assert first_state({**base, "birth_state": "unknown_rename_source"}, set(), set(), set(), {7}) == "unknown_lineage"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--rq1-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    verify_inputs(args.rq1_root)
    self_check()
    projects = load_projects(args.rq1_root)
    artifacts = read_csv(args.rq1_root / "rq1-artifacts.csv")
    mutations = read_csv(args.rq1_root / "rq1-mutations.csv")
    lane_events, accesses = project_events(projects, artifacts, mutations)
    if sum(int(row["mutation_rows"]) for row in lane_events) != len(mutations):
        raise ValueError("mutation rows do not reconcile in worktree lanes")
    components, component_events = build_components(lane_events)
    boundaries, prefix_rows = derive_boundaries(components, component_events, accesses, artifacts, mutations)

    raw = args.output / "raw"
    write_csv(raw / "rq4-accesses.csv", accesses, list(accesses[0]))
    write_csv(raw / "rq4-components.csv", components, list(components[0]))
    write_csv(raw / "rq4-boundaries.csv", boundaries, list(boundaries[0]))
    write_csv(raw / "rq4-prefix-actions.csv", prefix_rows, list(prefix_rows[0]))
    write_result(args.output / "result.md", components, boundaries)
    plot(raw, args.output / "figures")


if __name__ == "__main__":
    main()
