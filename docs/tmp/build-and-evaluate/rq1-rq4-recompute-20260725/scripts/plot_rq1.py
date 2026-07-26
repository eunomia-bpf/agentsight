#!/usr/bin/env python3
"""Render RQ1 paper figures from frozen source-linked CSV rows."""

from __future__ import annotations

import argparse
import csv
import math
from collections import defaultdict
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

LABEL_OFFSETS = {
    "agentsight": (-62, -28),
    "ActPlane": (-52, -28),
    "bpf-developer-tutorial": (6, -28),
    "eunomia.dev": (6, -28),
    "agentskill-observability-paper": (6, -24),
    "academic-writing-skills": (6, -28),
}

ACTIVITY_OFFSETS = {
    "introduced_persisted": {
        "agentsight": (-64, -34),
        "ActPlane": (-54, -26),
        "eunomia.dev": (6, -34),
    },
    "reuse_observed": {
        "agentsight": (-70, -15),
        "ActPlane": (-70, -18),
        "bpf-developer-tutorial": (6, -20),
        "eunomia.dev": (6, -20),
        "agentskill-observability-paper": (6, -25),
        "academic-writing-skills": (6, -16),
    },
    "validation_observed": {
        "agentsight": (-82, -10),
        "ActPlane": (-62, 8),
        "eunomia.dev": (6, -25),
    },
}


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        raise SystemExit(f"missing frozen input: {path}")
    with path.open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    if not rows:
        raise SystemExit(f"empty frozen input: {path}")
    return rows


def integer(row: dict[str, str], key: str) -> int:
    return int(row[key])


def ratio(row: dict[str, str], numerator: str, denominator: str) -> float:
    den = integer(row, denominator)
    return integer(row, numerator) / den if den else math.nan


def aj_curve(rows: list[dict[str, str]], prefix: str) -> tuple[list[int], list[float]]:
    """Aalen--Johansen CIF with one endpoint and pooled competing outcomes."""
    by_time: dict[int, list[str]] = defaultdict(list)
    for row in rows:
        duration = max(1, integer(row, f"{prefix}_duration_events"))
        outcome = row[f"{prefix}_outcome"]
        if outcome.startswith("observed_"):
            kind = "interest"
        elif outcome.startswith("competing_"):
            kind = "competing"
        elif outcome == "censored_end":
            kind = "censored"
        else:
            raise ValueError(f"unknown {prefix} outcome: {outcome}")
        by_time[duration].append(kind)

    risk = len(rows)
    survival = 1.0
    incidence = 0.0
    xs = [0]
    ys = [0.0]
    for duration in sorted(by_time):
        kinds = by_time[duration]
        interest = kinds.count("interest")
        competing = kinds.count("competing")
        censored = kinds.count("censored")
        if risk <= 0:
            break
        incidence += survival * interest / risk
        survival *= 1.0 - (interest + competing) / risk
        xs.append(duration)
        ys.append(incidence)
        risk -= interest + competing + censored
    return xs, ys


def risk_at(rows: list[dict[str, str]], prefix: str, horizon: int) -> int:
    return sum(integer(row, f"{prefix}_duration_events") >= horizon for row in rows)


def display_horizons(rows: list[dict[str, str]], prefix: str) -> list[int]:
    values = sorted(max(1, integer(row, f"{prefix}_duration_events")) for row in rows)
    if not values:
        return []
    positions = [0.0, 0.25, 0.5, 0.75, 1.0]
    horizons = []
    for position in positions:
        index = round(position * (len(values) - 1))
        horizons.append(values[index])
    return sorted(set(horizons))


def add_risk_table(
    axis,
    groups: dict[str, list[dict[str, str]]],
    prefix: str,
    horizons: list[int],
) -> None:
    if not horizons:
        return
    labels = [SHORT.get(project, project) for project in groups]
    cells = [[str(risk_at(rows, prefix, horizon)) for horizon in horizons]
             for rows in groups.values()]
    table = axis.table(
        cellText=cells,
        rowLabels=labels,
        colLabels=[str(value) for value in horizons],
        cellLoc="center",
        rowLoc="right",
        bbox=[0.0, -0.62, 1.0, 0.30],
    )
    table.auto_set_font_size(False)
    table.set_fontsize(7)
    axis.text(0.0, -0.24, "At risk by event-step horizon", transform=axis.transAxes,
              fontsize=8, fontweight="bold", va="top")


def plot_progress(
    summaries: list[dict[str, str]],
    mutations: list[dict[str, str]],
    output: Path,
) -> None:
    projects = [row["project"] for row in summaries]
    colors = dict(zip(projects, plt.get_cmap("tab10").colors, strict=False))
    groups: dict[str, list[dict[str, str]]] = {
        project: [row for row in mutations
                  if row["project"] == project and row["operation"] != "delete"]
        for project in projects
    }
    summary_by_project = {row["project"]: row for row in summaries}
    validation_groups = {
        project: rows for project, rows in groups.items()
        if summary_by_project[project]["qualified_validation"] == "true"
    }
    fig = plt.figure(figsize=(7.05, 5.9))
    grid = fig.add_gridspec(2, 2, height_ratios=[0.9, 1.35], hspace=0.62, wspace=0.36)
    axes = [
        fig.add_subplot(grid[0, :]),
        fig.add_subplot(grid[1, 0]),
        fig.add_subplot(grid[1, 1]),
    ]

    rates = [ratio(row, "introduced_persisted", "introduced_eligible")
             for row in summaries]
    y = list(range(len(projects)))
    axes[0].barh(y, [0 if math.isnan(value) else value for value in rates],
                 color=[colors[project] if not math.isnan(value) else "#d4d4d4"
                        for project, value in zip(projects, rates, strict=True)], alpha=0.82)
    axes[0].set_yticks(y, [SHORT.get(project, project) for project in projects])
    axes[0].invert_yaxis()
    axes[0].set_xlim(0, 1.05)
    axes[0].xaxis.set_major_formatter(PercentFormatter(1.0))
    axes[0].set_title("A. Introduced-artifact persistence")
    axes[0].set_xlabel("Final path exists / confirmed creates")
    for index, (row, value) in enumerate(zip(summaries, rates, strict=True)):
        label = (f"{row['introduced_persisted']}/{row['introduced_eligible']}"
                 if integer(row, "introduced_eligible") else "N/A (no confirmed creates)")
        x = 0.02 if math.isnan(value) else min(value + 0.02, 0.96)
        axes[0].text(x, index, label, va="center", fontsize=8)

    all_reuse = [row for rows in groups.values() for row in rows]
    all_validation = [row for rows in validation_groups.values() for row in rows]
    horizons = {
        "reuse": display_horizons(all_reuse, "reuse"),
        "validation": display_horizons(all_validation, "validation"),
    }
    for axis, prefix, title, active_groups in [
        (axes[1], "reuse", "B. Later artifact reuse", groups),
        (axes[2], "validation", "C. Validation before supersession", validation_groups),
    ]:
        for project, rows in active_groups.items():
            if not rows:
                continue
            xs, ys = aj_curve(rows, prefix)
            axis.step(xs, ys, where="post", color=colors[project], linewidth=1.8,
                      label=f"{SHORT.get(project, project)} (n={len(rows)})")
        axis.set_xscale("symlog", linthresh=1)
        axis.set_ylim(0, 1.02)
        axis.yaxis.set_major_formatter(PercentFormatter(1.0))
        axis.set_title(title, fontsize=10)
        axis.set_xlabel("Action-event steps after mutation", labelpad=2)
        axis.set_ylabel("Competing-risk cumulative incidence")
        axis.grid(alpha=0.2)
        axis.legend(fontsize=7, frameon=False, loc="upper left")
        add_risk_table(axis, active_groups, prefix, horizons[prefix])

    persistence_qualified = sum(integer(row, "introduced_eligible") > 0 for row in summaries)
    validation_qualified = len(validation_groups)
    fig.subplots_adjust(left=0.21, right=0.98, top=0.95, bottom=0.24)
    save(fig, output, "rq1-progress-curves")


def average_ranks(values: list[float]) -> list[float]:
    order = sorted(range(len(values)), key=values.__getitem__)
    ranks = [0.0] * len(values)
    index = 0
    while index < len(order):
        end = index + 1
        while end < len(order) and values[order[end]] == values[order[index]]:
            end += 1
        rank = (index + 1 + end) / 2
        for position in order[index:end]:
            ranks[position] = rank
        index = end
    return ranks


def spearman(xs: list[float], ys: list[float]) -> float:
    if len(xs) < 2:
        return math.nan
    rx, ry = average_ranks(xs), average_ranks(ys)
    mx, my = sum(rx) / len(rx), sum(ry) / len(ry)
    numerator = sum((x - mx) * (y - my) for x, y in zip(rx, ry, strict=True))
    denominator = math.sqrt(sum((x - mx) ** 2 for x in rx) *
                            sum((y - my) ** 2 for y in ry))
    return numerator / denominator if denominator else math.nan


def plot_activity(summaries: list[dict[str, str]], output: Path) -> None:
    panels = [
        ("introduced_persisted", "introduced_eligible", "A. Introduced artifacts persisting", None),
        ("reuse_observed", "reuse_eligible", "B. Mutations later reused", "qualified_longitudinal"),
        ("validation_observed", "validation_eligible", "C. Validated before supersession", "qualified_validation"),
    ]
    fig = plt.figure(figsize=(7.05, 5.2))
    grid = fig.add_gridspec(2, 2, hspace=0.38, wspace=0.3)
    axes = [
        fig.add_subplot(grid[0, 0]),
        fig.add_subplot(grid[0, 1]),
        fig.add_subplot(grid[1, :]),
    ]
    colors = plt.get_cmap("tab10").colors
    color_by_project = {
        row["project"]: colors[index % len(colors)]
        for index, row in enumerate(summaries)
    }
    for axis, (numerator, denominator, title, qualifier) in zip(axes, panels, strict=True):
        eligible = [row for row in summaries if integer(row, denominator) > 0
                    and (qualifier is None or row[qualifier] == "true")]
        xs = [integer(row, "attributed_tool_actions") for row in eligible]
        ys = [ratio(row, numerator, denominator) for row in eligible]
        for row, x, y in zip(eligible, xs, ys, strict=True):
            label = (f"{SHORT.get(row['project'], row['project'])} "
                     f"{row[numerator]}/{row[denominator]}")
            axis.scatter(
                x,
                y,
                s=70,
                color=color_by_project[row["project"]],
                label=label,
                zorder=3,
            )
            if numerator == "reuse_observed":
                continue
            axis.annotate(
                f"{SHORT.get(row['project'], row['project'])}\n"
                f"{row[numerator]}/{row[denominator]}",
                (x, y), xytext=ACTIVITY_OFFSETS[numerator].get(
                    row["project"], LABEL_OFFSETS.get(row["project"], (5, 5))
                ),
                textcoords="offset points", fontsize=7,
            )
        if numerator == "reuse_observed":
            axis.legend(
                fontsize=7,
                loc="center",
                bbox_to_anchor=(0.5, 0.38),
                ncol=1,
                frameon=False,
            )
        rho = spearman([float(value) for value in xs], ys)
        rho_text = (f"descriptive Spearman ρ={rho:.2f}" if len(xs) >= 4
                    else f"Coverage only ({len(xs)}/6 cases); correlation stopped")
        axis.text(0.03, 0.94 if len(xs) < 4 else 0.04, rho_text,
                  transform=axis.transAxes, va="top" if len(xs) < 4 else "bottom", fontsize=8)
        axis.set_xscale("log")
        axis.set_ylim(-0.02, 1.08)
        axis.yaxis.set_major_formatter(PercentFormatter(1.0))
        axis.set_title(title)
        axis.set_xlabel("Worktree-attributed Tool actions (log scale)")
        axis.grid(alpha=0.2)
    fig.supylabel("Observed proportion (exact numerator/denominator shown)", fontsize=8, x=0.015)
    fig.subplots_adjust(left=0.12, right=0.985, top=0.95, bottom=0.11)
    save(fig, output, "rq1-activity-progress")


def save(fig, output: Path, stem: str) -> None:
    output.mkdir(parents=True, exist_ok=True)
    fig.savefig(output / f"{stem}.pdf", metadata={"Title": stem})
    fig.savefig(output / f"{stem}.png", dpi=180, metadata={"Title": stem})
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, type=Path, help="frozen raw directory")
    parser.add_argument("--output", required=True, type=Path, help="figure directory")
    args = parser.parse_args()
    summaries = read_csv(args.input / "rq1-summary.csv")
    mutations = read_csv(args.input / "rq1-mutations.csv")
    plot_progress(summaries, mutations, args.output)
    plot_activity(summaries, args.output)
    print(f"wrote RQ1 F3/F4 to {args.output}")


if __name__ == "__main__":
    main()
