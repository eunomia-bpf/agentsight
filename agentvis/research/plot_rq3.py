#!/usr/bin/env python3
"""Derive and render reviewed RQ3 mutation-episode figures from frozen RQ1 rows."""

from __future__ import annotations

import argparse
import csv
import gzip
import json
from collections import Counter, defaultdict
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter

plt.rcParams["pdf.fonttype"] = 42
plt.rcParams["ps.fonttype"] = 42


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


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def write_csv(path: Path, rows: list[dict[str, object]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def event_file(events_dir: Path, project: str) -> Path:
    candidates = [events_dir / f"{project}.json.gz"]
    if project == "eunomia.dev":
        candidates.append(events_dir / "eunomia-dev.json.gz")
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    raise FileNotFoundError(f"missing frozen event gzip for {project}")


def verify_event_ids(events_dir: Path, projects: list[str]) -> dict[str, set[str]]:
    result = {}
    for project in projects:
        with gzip.open(event_file(events_dir, project), "rt", encoding="utf-8") as stream:
            payload = json.load(stream)
        ids = [event["id"] for event in payload["events"]]
        if len(ids) != len(set(ids)):
            raise ValueError(f"duplicate event IDs in {project}")
        result[project] = set(ids)
    return result


def derive(
    artifacts: list[dict[str, str]],
    mutations: list[dict[str, str]],
    event_ids: dict[str, set[str]],
) -> tuple[list[dict[str, object]], list[dict[str, object]], list[dict[str, object]]]:
    grouped: dict[tuple[str, str, str, str], list[dict[str, str]]] = defaultdict(list)
    for row in mutations:
        if row["event_id"] not in event_ids[row["project"]]:
            raise ValueError(f"unresolved source event {row['project']}:{row['event_id']}")
        grouped[(row["project"], row["worktree_id"], row["artifact_id"], row["event_id"])].append(row)

    by_artifact: dict[tuple[str, str, str], list[dict[str, object]]] = defaultdict(list)
    raw_row_totals = Counter(row["project"] for row in mutations)
    for (project, worktree, artifact, event_id), rows in grouped.items():
        event_indexes = {int(row["event_index"]) for row in rows}
        timestamps = {int(row["ts_ms"]) for row in rows}
        sessions = {row["session_id"] for row in rows}
        if len(event_indexes) != 1 or len(timestamps) != 1 or len(sessions) != 1:
            raise ValueError(f"inconsistent compound episode {project}:{event_id}:{artifact}")
        episode = {
            "project": project,
            "worktree_id": worktree,
            "artifact_id": artifact,
            "event_id": event_id,
            "event_index": next(iter(event_indexes)),
            "ts_ms": next(iter(timestamps)),
            "session_id": next(iter(sessions)),
            "source_call_ids": ";".join(sorted({row["source_call_id"] for row in rows})),
            "operations": ";".join(sorted({row["operation"] for row in rows})),
            "raw_mutation_rows": len(rows),
        }
        by_artifact[(project, worktree, artifact)].append(episode)

    episodes: list[dict[str, object]] = []
    for key, rows in by_artifact.items():
        rows.sort(key=lambda row: (int(row["event_index"]), str(row["event_id"])))
        previous = None
        for ordinal, row in enumerate(rows, 1):
            row["episode_ordinal"] = ordinal
            row["repeat_observed"] = ordinal > 1
            row["cross_session_repeat"] = bool(
                previous and row["session_id"] != previous["session_id"]
            )
            row["inter_episode_events"] = (
                int(row["event_index"]) - int(previous["event_index"]) if previous else ""
            )
            row["inter_episode_ms"] = int(row["ts_ms"]) - int(previous["ts_ms"]) if previous else ""
            episodes.append(row)
            previous = row

    episode_counts = Counter(
        (row["project"], row["worktree_id"], row["artifact_id"]) for row in episodes
    )
    loads: list[dict[str, object]] = []
    for row in artifacts:
        key = (row["project"], row["worktree_id"], row["artifact_id"])
        loads.append({
            "project": row["project"],
            "worktree_id": row["worktree_id"],
            "artifact_id": row["artifact_id"],
            "birth_state": row["birth_state"],
            "lineage_state": row["lineage_state"],
            "episode_count": episode_counts[key],
        })

    summaries = []
    projects = list(dict.fromkeys(row["project"] for row in artifacts))
    for project in projects:
        project_loads = [row for row in loads if row["project"] == project]
        project_episodes = [row for row in episodes if row["project"] == project]
        mutated = [row for row in project_loads if int(row["episode_count"]) > 0]
        repeats = [row for row in project_episodes if row["repeat_observed"]]
        episode_loads = sorted(
            (int(row["episode_count"]) for row in mutated),
            reverse=True,
        )
        top_width = 0.1 * len(episode_loads)
        top_full = int(top_width)
        top_fraction = top_width - top_full
        top_10_load = sum(episode_loads[:top_full])
        if top_fraction and top_full < len(episode_loads):
            top_10_load += top_fraction * episode_loads[top_full]
        operations = Counter(
            operation
            for row in repeats
            for operation in str(row["operations"]).split(";")
        )
        birth_counts = Counter(str(row["birth_state"]) for row in project_loads)
        summaries.append({
            "project": project,
            "observed_artifacts": len(project_loads),
            "mutated_artifacts": len(mutated),
            "zero_episode_artifacts": len(project_loads) - len(mutated),
            "mutation_episodes": len(project_episodes),
            "raw_mutation_rows": raw_row_totals[project],
            "repeat_episodes": len(repeats),
            "cross_session_repeat_episodes": sum(bool(row["cross_session_repeat"]) for row in repeats),
            "repeat_rename_episodes": operations["rename"],
            "repeat_delete_episodes": operations["delete"],
            "repeat_episode_fraction": len(repeats) / len(project_episodes) if project_episodes else 0,
            "top_10pct_episode_share": (
                top_10_load / sum(episode_loads) if episode_loads else 0
            ),
            "max_episode_load": episode_loads[0] if episode_loads else 0,
            "observation_span_days": (
                (max(int(row["ts_ms"]) for row in project_episodes)
                 - min(int(row["ts_ms"]) for row in project_episodes)) / 86_400_000
                if project_episodes else 0
            ),
            "birth_confirmed_create": birth_counts["confirmed_create"],
            "birth_left_censored_existing": birth_counts["left_censored_existing"],
            "birth_unknown_create_status": birth_counts["unknown_create_status"],
            "birth_unknown_rename_source": birth_counts["unknown_rename_source"],
            "qualified_curve": len(project_episodes) >= 20 and len(mutated) >= 10,
        })
    return loads, episodes, summaries


def conditional_ccdf(values: list[int]) -> tuple[list[int], list[float]]:
    xs = sorted(set(value for value in values if value > 0))
    return xs, [sum(value >= x for value in values) / len(values) for x in xs]


def plot(loads: list[dict[str, object]], episodes: list[dict[str, object]], summaries: list[dict[str, object]], output: Path) -> None:
    projects = [str(row["project"]) for row in summaries]
    colors = dict(zip(projects, plt.get_cmap("tab10").colors, strict=False))
    # Compose at the final paper width instead of shrinking a panoramic canvas.
    figure = plt.figure(figsize=(7.05, 8.3))
    grid = figure.add_gridspec(
        3,
        2,
        height_ratios=[1.0, 1.25, 1.45],
        hspace=0.55,
        wspace=0.38,
    )
    zero_axis = figure.add_subplot(grid[0, 0])
    ccdf_axis = figure.add_subplot(grid[0, 1])
    concentration_axis = figure.add_subplot(grid[1, :])
    evolution_axis = figure.add_subplot(grid[2, :])
    summary_by_project = {str(row["project"]): row for row in summaries}

    zero_rates = []
    for summary in summaries:
        total = int(summary["observed_artifacts"])
        zero_rates.append(int(summary["zero_episode_artifacts"]) / total if total else 0)
    zero_axis.bar(range(len(projects)), zero_rates, color=[colors[p] for p in projects])
    zero_axis.set_ylim(0, 1)
    zero_axis.yaxis.set_major_formatter(PercentFormatter(1.0))
    zero_axis.set_xticks(
        range(len(projects)),
        [TINY.get(project, project) for project in projects],
        fontsize=7,
    )
    zero_axis.set_ylabel("Zero episodes")
    zero_axis.set_title("A1. Zero-episode artifacts")
    zero_axis.grid(axis="y", alpha=0.2)
    for index, (rate, summary) in enumerate(zip(zero_rates, summaries, strict=True)):
        inside = rate > 0.25
        zero_axis.text(
            index,
            rate - 0.025 if inside else rate + 0.035,
            f"{summary['zero_episode_artifacts']}\n/{summary['observed_artifacts']}",
            ha="center",
            va="top" if inside else "bottom",
            fontsize=7,
            color="white" if inside else "#222222",
        )

    for project in projects:
        values = [int(row["episode_count"]) for row in loads if row["project"] == project and int(row["episode_count"]) > 0]
        xs, ys = conditional_ccdf(values)
        if xs:
            ccdf_axis.step(xs, ys, where="post", color=colors[project], label=f"{SHORT.get(project, project)} (n={len(values)})")
    ccdf_axis.set_xscale("log")
    ccdf_axis.set_yscale("log")
    ccdf_axis.set_xlabel("Mutation episodes | at least one (log)")
    ccdf_axis.set_ylabel("Conditional CCDF (log)")
    ccdf_axis.set_title("A2. Conditional episode counts")
    ccdf_axis.grid(alpha=0.2, which="both")
    ccdf_axis.legend(fontsize=7, frameon=False)

    for project in projects:
        values = sorted(
            [int(row["episode_count"]) for row in loads if row["project"] == project and int(row["episode_count"]) > 0],
            reverse=True,
        )
        if not values:
            continue
        total = sum(values)
        cumulative = 0
        xs, ys = [0.0], [0.0]
        for index, value in enumerate(values, 1):
            cumulative += value
            xs.append(index / len(values))
            ys.append(cumulative / total)
        summary = summary_by_project[project]
        concentration_axis.plot(
            xs,
            ys,
            color=colors[project],
            label=(f"{SHORT.get(project, project)} "
                   f"({summary['mutation_episodes']}/{summary['raw_mutation_rows']} ep/rows)"),
        )
    concentration_axis.plot([0, 1], [0, 1], linestyle="--", color="#888888", linewidth=1, label="equal episode load")
    concentration_axis.set_xlim(0, 1)
    concentration_axis.set_ylim(0, 1)
    concentration_axis.xaxis.set_major_formatter(PercentFormatter(1.0))
    concentration_axis.yaxis.set_major_formatter(PercentFormatter(1.0))
    concentration_axis.set_xlabel("Most-mutated identities included")
    concentration_axis.set_ylabel("Cumulative episode share")
    concentration_axis.set_title("B. Episode concentration")
    concentration_axis.grid(alpha=0.2)
    concentration_axis.legend(fontsize=7, ncol=2, frameon=False)

    for project in projects:
        rows = sorted(
            [row for row in episodes if row["project"] == project],
            key=lambda row: (int(row["event_index"]), str(row["artifact_id"]), str(row["event_id"])),
        )
        by_event: dict[int, list[dict[str, object]]] = defaultdict(list)
        for row in rows:
            by_event[int(row["event_index"])].append(row)
        repeats = 0
        total = 0
        xs, ys = [], []
        for event_index in sorted(by_event):
            event_rows = by_event[event_index]
            repeats += sum(bool(row["repeat_observed"]) for row in event_rows)
            total += len(event_rows)
            xs.append(event_index)
            ys.append(repeats / total)
        if xs:
            summary = summary_by_project[project]
            cross = int(summary["cross_session_repeat_episodes"])
            repeat_total = int(summary["repeat_episodes"])
            cross_share = cross / repeat_total if repeat_total else 0
            label = f"{SHORT.get(project, project)} (repeat={repeat_total}, cross={cross_share:.1%})"
            evolution_axis.step(xs, ys, where="post", color=colors[project], label=label)
    evolution_axis.set_ylim(0, 1)
    evolution_axis.set_xscale("symlog", linthresh=100)
    evolution_axis.set_xlim(left=0)
    evolution_axis.yaxis.set_major_formatter(PercentFormatter(1.0))
    evolution_axis.set_xlabel("Frozen native Tool-action event index")
    evolution_axis.set_ylabel("Repeat-observed episode fraction")
    evolution_axis.set_title("C. Repeat-observed mutation over action time")
    evolution_axis.grid(alpha=0.2)
    evolution_axis.legend(fontsize=7, loc="lower right", ncol=2, frameon=False)
    evolution_axis.text(
        0.02,
        0.98,
        "Exact prefixes; no rolling window or convergence claim",
        transform=evolution_axis.transAxes,
        va="top",
        fontsize=7,
        color="#a33a32",
    )
    table_rows = []
    table_labels = []
    for project in projects:
        summary = summary_by_project[project]
        repeat_total = int(summary["repeat_episodes"])
        cross_share = int(summary["cross_session_repeat_episodes"]) / repeat_total if repeat_total else 0
        rename_share = int(summary["repeat_rename_episodes"]) / repeat_total if repeat_total else 0
        delete_share = int(summary["repeat_delete_episodes"]) / repeat_total if repeat_total else 0
        table_labels.append(SHORT.get(project, project))
        table_rows.append([
            f"{summary['mutation_episodes']}/{summary['raw_mutation_rows']}",
            f"{float(summary['repeat_episode_fraction']):.1%}",
            f"{cross_share:.1%}",
            f"{rename_share:.1%}/{delete_share:.1%}",
            f"{float(summary['observation_span_days']):.1f}",
        ])
    table = evolution_axis.table(
        cellText=table_rows,
        rowLabels=table_labels,
        colLabels=["ep/raw", "repeat", "cross", "rename/delete", "days"],
        cellLoc="center",
        rowLoc="right",
        bbox=[0.0, -0.66, 1.0, 0.40],
    )
    table.auto_set_font_size(False)
    table.set_fontsize(7)

    figure.subplots_adjust(top=0.975, bottom=0.24, left=0.14, right=0.965)
    output.mkdir(parents=True, exist_ok=True)
    figure.savefig(output / "rq3-rework-structure.pdf")
    figure.savefig(output / "rq3-rework-structure.png", dpi=180)
    plt.close(figure)


def plot_birth_sensitivity(loads: list[dict[str, object]], summaries: list[dict[str, object]], output: Path) -> None:
    projects = [str(row["project"]) for row in summaries]
    states = [
        "confirmed_create",
        "left_censored_existing",
        "unknown_create_status",
        "unknown_rename_source",
    ]
    labels = ["confirmed create", "left-censored", "unknown create", "unknown rename"]
    cells: list[list[float | None]] = []
    annotations: list[list[str]] = []
    for project in projects:
        value_row = []
        annotation_row = []
        for state in states:
            values = sorted(
                int(row["episode_count"])
                for row in loads
                if row["project"] == project
                and row["birth_state"] == state
                and int(row["episode_count"]) > 0
            )
            if len(values) < 10:
                value_row.append(None)
                annotation_row.append(f"n={len(values)}\ncount only")
            else:
                middle = len(values) // 2
                median = (
                    values[middle]
                    if len(values) % 2
                    else (values[middle - 1] + values[middle]) / 2
                )
                value_row.append(float(median))
                annotation_row.append(f"{median:g}\nn={len(values)}")
        cells.append(value_row)
        annotations.append(annotation_row)

    numeric = [value for row in cells for value in row if value is not None]
    upper = max(numeric) if numeric else 1.0
    image_values = [[-1 if value is None else value for value in row] for row in cells]
    cmap = plt.get_cmap("YlGnBu").copy()
    cmap.set_under("#eeeeee")
    fig, axis = plt.subplots(figsize=(7.05, 4.3))
    image = axis.imshow(image_values, cmap=cmap, vmin=0, vmax=upper, aspect="auto")
    axis.set_xticks(range(len(states)), labels)
    axis.set_yticks(range(len(projects)), [SHORT.get(project, project) for project in projects])
    axis.set_title("RQ3 sensitivity: median mutation episodes by observable birth state")
    for y, row in enumerate(annotations):
        for x, label in enumerate(row):
            value = cells[y][x]
            color = "white" if value is not None and value > upper * 0.55 else "#222222"
            axis.text(x, y, label, ha="center", va="center", fontsize=8, color=color)
    colorbar = fig.colorbar(image, ax=axis, pad=0.02)
    colorbar.set_label("Median episodes among mutated identities")
    fig.text(
        0.5,
        0.015,
        "Cells with fewer than 10 mutated identities remain count-only; unknown birth categories are retained rather than dropped.",
        ha="center",
        fontsize=8,
    )
    fig.subplots_adjust(left=0.2, right=0.92, top=0.88, bottom=0.14)
    fig.savefig(output / "rq3-birth-state-sensitivity.pdf")
    fig.savefig(output / "rq3-birth-state-sensitivity.png", dpi=180)
    plt.close(fig)


def write_result(path: Path, summaries: list[dict[str, object]]) -> None:
    lines = [
        "# RQ3 Mutation-Episode Summary",
        "",
        "This is a descriptive first/repeat-observed analysis, not a convergence, thrashing, or waste label.",
        "",
        "| Project | Artifacts (mutated/all) | Episodes/raw rows | Repeat fraction | Top-10% episode share | Maximum load |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for row in summaries:
        lines.append(
            f"| {row['project']} | {row['mutated_artifacts']}/{row['observed_artifacts']} | "
            f"{row['mutation_episodes']}/{row['raw_mutation_rows']} | {row['repeat_episode_fraction']:.1%} | "
            f"{row['top_10pct_episode_share']:.1%} | {row['max_episode_load']} |"
        )
    lines.extend([
        "",
        "Birth-state categories are retained exhaustively. Strata with fewer than 10 mutated identities are excluded from sensitivity curves and remain count-only.",
        "",
        "| Project | Confirmed create | Left-censored | Unknown create | Unknown rename |",
        "|---|---:|---:|---:|---:|",
    ])
    for row in summaries:
        lines.append(
            f"| {row['project']} | {row['birth_confirmed_create']} | "
            f"{row['birth_left_censored_existing']} | {row['birth_unknown_create_status']} | "
            f"{row['birth_unknown_rename_source']} |"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--rq1-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    artifacts = read_csv(args.rq1_root / "rq1-artifacts.csv")
    mutations = read_csv(args.rq1_root / "rq1-mutations.csv")
    projects = list(dict.fromkeys(row["project"] for row in artifacts))
    event_ids = verify_event_ids(args.rq1_root / "events", projects)
    loads, episodes, summaries = derive(artifacts, mutations, event_ids)

    raw = args.output / "raw"
    write_csv(raw / "rq3-artifact-load.csv", loads, [
        "project", "worktree_id", "artifact_id", "birth_state", "lineage_state", "episode_count",
    ])
    write_csv(raw / "rq3-episodes.csv", episodes, [
        "project", "worktree_id", "artifact_id", "event_id", "event_index", "ts_ms", "session_id",
        "source_call_ids", "operations", "raw_mutation_rows", "episode_ordinal", "repeat_observed",
        "cross_session_repeat", "inter_episode_events", "inter_episode_ms",
    ])
    write_csv(raw / "rq3-summary.csv", summaries, list(summaries[0]))
    plot(loads, episodes, summaries, args.output / "figures")
    plot_birth_sensitivity(loads, summaries, args.output / "figures")
    write_result(args.output / "result.md", summaries)


if __name__ == "__main__":
    main()
