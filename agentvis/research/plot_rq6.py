#!/usr/bin/env python3
"""Audit frozen source-signal coverage for skill/harness association (RQ6)."""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path, PurePosixPath

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import PercentFormatter

from plot_rq2 import load_projects, read_csv, verify_inputs, write_csv


KINDS = ["skill_tool", "instruction_read", "instruction_mutation"]
STATUSES = ["ok", "observed", "fail"]
VENDORS = ["claude", "codex", "gemini"]
INSTRUCTION_NAMES = {"agents.md", "claude.md", "skill.md"}
SHORT = {
    "agentsight": "AgentSight",
    "ActPlane": "ActPlane",
    "bpf-developer-tutorial": "BPF tutorial",
    "eunomia.dev": "eunomia.dev",
    "agentskill-observability-paper": "AgentSkill paper",
    "academic-writing-skills": "Writing skills",
}
KIND_SHORT = {"skill_tool": "Skill Tool", "instruction_read": "instruction read", "instruction_mutation": "instruction mutation"}


def is_instruction(path: str) -> bool:
    return bool(path) and PurePosixPath(path).name.lower() in INSTRUCTION_NAMES


def extract_signals(projects: list[tuple[str, list[dict[str, object]]]]) -> list[dict[str, object]]:
    signals = []
    for project, events in projects:
        for event_index, event in enumerate(events):
            base = {
                "project": project,
                "vendor": str(event["vendor"]),
                "session_id": str(event["session_id"]),
                "event_index": event_index,
                "event_id": str(event["id"]),
                "source_call_id": str(event.get("source_call_id") or ""),
                "ts_ms": int(event["ts_ms"]),
                "status": str(event.get("status", "observed")),
            }
            if str(event.get("tool_name", "")).lower() == "skill":
                signals.append({**base, "source_kind": "skill_tool", "action_ordinal": "", "operation": "", "path": "", "previous_path": ""})
            seen = set()
            for action_ordinal, action in enumerate(event.get("actions", [])):
                if bool(action.get("scope", False)):
                    continue
                operation = str(action.get("access", ""))
                path = str(action.get("path", ""))
                previous_path = str(action.get("previous_path", ""))
                if operation == "read" and is_instruction(path):
                    source_kind = "instruction_read"
                    qualified = path
                elif operation in {"write", "create", "rename", "delete"} and (is_instruction(path) or is_instruction(previous_path)):
                    source_kind = "instruction_mutation"
                    qualified = "|".join(sorted({candidate for candidate in [path, previous_path] if is_instruction(candidate)}))
                else:
                    continue
                # A rename with both instruction endpoints is one signal row.
                key = (source_kind, operation, qualified)
                if key in seen:
                    continue
                seen.add(key)
                signals.append({
                    **base,
                    "source_kind": source_kind,
                    "action_ordinal": action_ordinal,
                    "operation": operation,
                    "path": path,
                    "previous_path": previous_path,
                })
    return signals


def derive_tables(
    projects: list[tuple[str, list[dict[str, object]]]],
    signals: list[dict[str, object]],
    frozen_coverage: list[dict[str, object]],
) -> tuple[list[dict[str, object]], list[dict[str, object]], list[dict[str, object]]]:
    project_order = [project for project, _ in projects]
    frozen_by_project = {str(row["project"]): row for row in frozen_coverage}
    sessions: dict[tuple[str, str], set[str]] = defaultdict(set)
    event_counts: dict[str, int] = {}
    vendors_by_project: dict[str, set[str]] = defaultdict(set)
    for project, events in projects:
        event_counts[project] = len(events)
        for event in events:
            vendor = str(event["vendor"])
            sessions[(project, "ALL")].add(str(event["session_id"]))
            sessions[(project, vendor)].add(str(event["session_id"]))
            vendors_by_project[project].add(vendor)
        if len(sessions[(project, "ALL")]) != int(frozen_by_project[project]["included_sessions"]):
            raise ValueError(f"session denominator mismatch in {project}")
        frozen_vendors = frozen_by_project[project]["included_sessions_by_vendor"]
        for vendor, count in frozen_vendors.items():
            if len(sessions[(project, vendor)]) != int(count):
                raise ValueError(f"vendor session denominator mismatch in {project}/{vendor}")

    signal_sessions: dict[tuple[str, str, str], set[str]] = defaultdict(set)
    for row in signals:
        for vendor in ["ALL", str(row["vendor"])]:
            signal_sessions[(str(row["project"]), vendor, str(row["source_kind"]))].add(str(row["session_id"]))

    session_rows = []
    for project in project_order:
        for vendor in ["ALL", *sorted(vendors_by_project[project])]:
            denominator = len(sessions[(project, vendor)])
            kind_sets = [signal_sessions[(project, vendor, kind)] for kind in KINDS]
            any_signal = set().union(*kind_sets)
            session_rows.append({
                "project": project,
                "vendor": vendor,
                "admitted_sessions": denominator,
                "skill_tool_sessions": len(kind_sets[0]),
                "instruction_read_sessions": len(kind_sets[1]),
                "instruction_mutation_sessions": len(kind_sets[2]),
                "any_observed_source_event_sessions": len(any_signal),
                "no_observed_source_event_sessions": denominator - len(any_signal),
            })

    source_rows = []
    for project in project_order:
        for vendor in ["ALL", *sorted(vendors_by_project[project])]:
            for kind in KINDS:
                for status in STATUSES:
                    selected = [row for row in signals if row["project"] == project and row["source_kind"] == kind and row["status"] == status and (vendor == "ALL" or row["vendor"] == vendor)]
                    source_rows.append({
                        "project": project,
                        "vendor": vendor,
                        "source_kind": kind,
                        "status": status,
                        "signal_rows": len(selected),
                        "unique_event_ids": len({str(row["event_id"]) for row in selected}),
                        "unique_sessions": len({str(row["session_id"]) for row in selected}),
                        "source_call_id_present": sum(bool(row["source_call_id"]) for row in selected),
                        "source_call_id_missing": sum(not bool(row["source_call_id"]) for row in selected),
                        "first_ts_ms": min((int(row["ts_ms"]) for row in selected), default=""),
                        "last_ts_ms": max((int(row["ts_ms"]) for row in selected), default=""),
                    })

    bin_rows = []
    by_project_event: dict[tuple[str, int, str], list[dict[str, object]]] = defaultdict(list)
    for row in signals:
        by_project_event[(str(row["project"]), int(row["event_index"]), str(row["source_kind"]))].append(row)
    for project in project_order:
        total = event_counts[project]
        for kind in KINDS:
            for bin_index in range(60):
                rows = [
                    row
                    for (candidate, event_index, source_kind), values in by_project_event.items()
                    if candidate == project and source_kind == kind and min(59, event_index * 60 // total) == bin_index
                    for row in values
                ]
                bin_rows.append({
                    "project": project,
                    "source_kind": kind,
                    "action_bin": bin_index,
                    "signal_rows": len(rows),
                    "unique_event_ids": len({str(row["event_id"]) for row in rows}),
                    "unique_sessions": len({str(row["session_id"]) for row in rows}),
                })
    return session_rows, source_rows, bin_rows


def self_check() -> None:
    assert is_instruction("AGENTS.md")
    assert is_instruction(".agents/skills/x/SKILL.md")
    assert not is_instruction("skills.md")
    events = [{
        "id": "e", "vendor": "codex", "session_id": "s", "ts_ms": 1,
        "status": "observed", "tool_name": "exec", "source_call_id": None,
        "actions": [{
            "worktree_id": "w", "path": "new/SKILL.md", "previous_path": "old/SKILL.md",
            "access": "rename",
        }],
    }]
    rows = extract_signals([("p", events)])
    assert len(rows) == 1 and rows[0]["source_kind"] == "instruction_mutation"


def plot(raw: Path, figures: Path) -> None:
    session_rows = read_csv(raw / "rq6-session-coverage.csv")
    sessions = [row for row in session_rows if row["vendor"] == "ALL"]
    source = [row for row in read_csv(raw / "rq6-source-coverage.csv") if row["vendor"] != "ALL"]
    bins = read_csv(raw / "rq6-action-bins.csv")
    projects = [row["project"] for row in sessions]
    plt.rcParams["pdf.fonttype"] = 42
    plt.rcParams["ps.fonttype"] = 42
    fig = plt.figure(figsize=(7.05, 8.15))
    grid = fig.add_gridspec(3, 1, height_ratios=[2.0, 2.1, 3.0], hspace=0.55)

    session_axis = fig.add_subplot(grid[0, 0])
    markers = ["o", "s", "^"]
    colors = ["#2f78b7", "#72aa7b", "#d98545"]
    y = np.arange(len(projects))
    for kind_index, (kind, marker, color) in enumerate(zip(KINDS, markers, colors, strict=True)):
        offset_y = (kind_index - 1) * 0.22
        values = [int(row[f"{kind}_sessions"]) / int(row["admitted_sessions"]) for row in sessions]
        session_axis.scatter(values, y + offset_y, marker=marker, color=color, s=28, label=KIND_SHORT[kind])
        for index, (value, row) in enumerate(zip(values, sessions, strict=True)):
            session_axis.text(value + 0.007, index + offset_y, f"{int(row[f'{kind}_sessions'])}/{int(row['admitted_sessions'])}", va="center", fontsize=7, color=color)
    session_axis.set_yticks(y, [SHORT.get(project, project) for project in projects], fontsize=7)
    session_axis.invert_yaxis()
    session_axis.set_xlim(-0.015, 1.05)
    session_axis.xaxis.set_major_formatter(PercentFormatter(1.0))
    session_axis.set_xlabel("non-exclusive share of admitted sessions", fontsize=7)
    session_axis.set_title("A. Sessions containing each recoverable source signal", loc="left", fontsize=9, fontweight="bold")
    session_axis.legend(fontsize=7, ncol=1, loc="upper right")
    session_axis.grid(axis="x", alpha=0.18)

    coverage_axis = fig.add_subplot(grid[1, 0])
    columns = [(vendor, kind, status) for vendor in VENDORS for kind in KINDS for status in STATUSES]
    matrix = np.zeros((len(projects), len(columns)))
    availability = np.zeros_like(matrix, dtype=bool)
    available_project_vendors = {
        (row["project"], row["vendor"])
        for row in session_rows
        if row["vendor"] != "ALL" and int(row["admitted_sessions"]) > 0
    }
    for row_index, project in enumerate(projects):
        for column_index, (vendor, kind, status) in enumerate(columns):
            availability[row_index, column_index] = (project, vendor) in available_project_vendors
            match = next((row for row in source if row["project"] == project and row["vendor"] == vendor and row["source_kind"] == kind and row["status"] == status), None)
            matrix[row_index, column_index] = int(match["unique_event_ids"]) if match else 0
    cmap = plt.get_cmap("Blues").copy()
    cmap.set_bad("#d6d6d6")
    log_matrix = np.ma.array(np.log1p(matrix), mask=~availability)
    image = coverage_axis.imshow(
        log_matrix,
        aspect="auto",
        cmap=cmap,
        vmin=0,
        vmax=max(float(np.log1p(matrix.max())), 1.0),
    )
    count_ticks = [count for count in [0, 1, 3, 10, 30, 100, 300, 1000] if count <= matrix.max()]
    colorbar = fig.colorbar(image, ax=coverage_axis, pad=0.012, fraction=0.028)
    colorbar.set_ticks(
        [np.log1p(count) for count in count_ticks],
        labels=[str(count) for count in count_ticks],
    )
    colorbar.ax.tick_params(labelsize=7)
    colorbar.set_label("unique events (log1p color)", fontsize=7)
    coverage_axis.set_yticks(range(len(projects)), [SHORT.get(project, project) for project in projects], fontsize=7)
    status_code = {"ok": "k", "observed": "u", "fail": "f"}
    labels = [f"{vendor[0].upper()}-{KINDS.index(kind)+1}-{status_code[status]}" for vendor, kind, status in columns]
    coverage_axis.set_xticks(range(len(columns)), labels, rotation=90, fontsize=7)
    coverage_axis.set_title("B. Unique signal events by vendor × kind × status", loc="left", fontsize=9, fontweight="bold")
    coverage_axis.set_xlabel("C/K/G vendor; kind 1=Skill Tool, 2=instruction read, 3=instruction mutation; k=ok, u=observed, f=fail; gray=N/A", fontsize=7)

    bin_axis = fig.add_subplot(grid[2, 0])
    bin_matrix = np.zeros((len(projects) * len(KINDS), 60))
    bin_labels = []
    for project_index, project in enumerate(projects):
        for kind_index, kind in enumerate(KINDS):
            row_index = project_index * len(KINDS) + kind_index
            selected = [row for row in bins if row["project"] == project and row["source_kind"] == kind]
            for row in selected:
                bin_matrix[row_index, int(row["action_bin"])] = int(row["unique_event_ids"])
            maximum = bin_matrix[row_index].max()
            if maximum:
                bin_matrix[row_index] /= maximum
            total = sum(int(row["unique_event_ids"]) for row in selected)
            bin_labels.append(f"{SHORT.get(project, project)} · {kind_index+1} (n={total})")
    bin_axis.imshow(bin_matrix, aspect="auto", interpolation="nearest", cmap="PuBu", vmin=0, vmax=1)
    bin_axis.set_yticks(range(len(bin_labels)), bin_labels, fontsize=7)
    bin_axis.set_xticks([0, 14, 29, 44, 59], ["0", "25", "50", "75", "100"], fontsize=7)
    bin_axis.set_xlabel("position in merged native action order (%) — not wall-clock time", fontsize=7)
    bin_axis.set_title("C. Occurrence support over 60 equal-action-count bins (row-max color)", loc="left", fontsize=9, fontweight="bold")

    fig.text(0.5, 0.027, "ASSOCIATION ANALYSIS STOPPED", ha="center", fontsize=7, color="#9a3f35", fontweight="bold")
    fig.text(0.5, 0.012, "N/A: Skill names/arguments, model/config, external instructions, and actual non-exposure.", ha="center", fontsize=7, color="#9a3f35")
    fig.subplots_adjust(top=0.965, bottom=0.085, left=0.20, right=0.94)
    figures.mkdir(parents=True, exist_ok=True)
    fig.savefig(figures / "rq6-source-coverage.pdf")
    fig.savefig(figures / "rq6-source-coverage.png", dpi=200)
    plt.close(fig)


def write_result(path: Path, sessions: list[dict[str, object]], source: list[dict[str, object]], signals: list[dict[str, object]]) -> None:
    totals = [row for row in sessions if row["vendor"] == "ALL"]
    lines = [
        "# RQ6 Source-Signal Coverage Stop",
        "",
        "**Association analysis stopped.** The frozen export lacks Skill names/arguments, model/configuration fields, repository-external instructions, and proof that sessions with no visible signal were unexposed.",
        "",
        "| Project | Sessions | Skill Tool | Instruction read | Instruction mutation | Any visible signal |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for row in totals:
        lines.append(
            f"| {row['project']} | {row['admitted_sessions']} | {row['skill_tool_sessions']} | "
            f"{row['instruction_read_sessions']} | {row['instruction_mutation_sessions']} | {row['any_observed_source_event_sessions']} |"
        )
    lines.extend([
        "",
        f"The exact rule yields {len(signals)} signal rows across {len({str(row['event_id']) for row in signals})} native Tool events. Vendor/status/source-call-ID coverage is in `raw/rq6-source-coverage.csv`; 60-bin support is action-order coverage, not time spent or duration.",
        "",
        "These counts do not show that a skill was used, helpful, harmful, ignored, or causally related to any process outcome.",
    ])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--rq1-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    verify_inputs(args.rq1_root)
    self_check()
    projects = load_projects(args.rq1_root)
    with (args.rq1_root / "projects.json").open(encoding="utf-8") as stream:
        frozen_coverage = json.load(stream)
    signals = extract_signals(projects)
    sessions, source, bins = derive_tables(projects, signals, frozen_coverage)
    if sum(int(row["signal_rows"]) for row in source if row["vendor"] == "ALL") != len(signals):
        raise ValueError("signal rows do not reconcile")
    raw = args.output / "raw"
    write_csv(raw / "rq6-observed-events.csv", signals, list(signals[0]))
    write_csv(raw / "rq6-source-coverage.csv", source, list(source[0]))
    write_csv(raw / "rq6-session-coverage.csv", sessions, list(sessions[0]))
    write_csv(raw / "rq6-action-bins.csv", bins, list(bins[0]))
    write_result(args.output / "result.md", sessions, source, signals)
    plot(raw, args.output / "figures")


if __name__ == "__main__":
    main()
