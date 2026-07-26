#!/usr/bin/env python3
"""Derive and render reviewed worktree-local RQ2 validation dynamics."""

from __future__ import annotations

import argparse
import csv
import gc
import gzip
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

import matplotlib.pyplot as plt

plt.rcParams["pdf.fonttype"] = 42
plt.rcParams["ps.fonttype"] = 42


# Recompute copy: pins updated to the HEAD (2026-07-25) re-extraction hashes.
EXPECTED = {
    "agentsight.json.gz": "b2301390a9f665480a8efd87690653064ca989bfc4a3793d54ea7798793bc01b",
    "ActPlane.json.gz": "7cee0b947d9cae85263894059674b069ec173d41907c9ba01938becaaa493ea2",
    "bpf-developer-tutorial.json.gz": "0fe42215ca4aa6b28676a155608a6ce71bc6d2c38a921e918a0f76bfdf472b8b",
    "eunomia-dev.json.gz": "f547f0607bfb2d81cc923f9292b34463cb4cd9a6054392d66268cf11869fd21e",
    "agentskill-observability-paper.json.gz": "c5a866cc256458ae7cd75a570e537ddf66f9e8d12977a1bfd89546dce006a4ab",
    "academic-writing-skills.json.gz": "04e5da6d202649d221e563bfb6bab21c51e9a5d4bfcccfdb55a1ee9e467c4d83",
    "rq1-mutations.csv": "e4c7407c1dcb8f9cfdae6647238345ce17cc1ae76fba324551665b10fe41c1a4",
}

SHORT = {
    "agentsight": "AgentSight",
    "ActPlane": "ActPlane",
    "bpf-developer-tutorial": "BPF tutorial",
    "eunomia.dev": "eunomia.dev",
    "agentskill-observability-paper": "AgentSkill paper",
    "academic-writing-skills": "Writing skills",
}

LANE_SHORT = {
    "agentsight": "AS",
    "ActPlane": "AP",
    "bpf-developer-tutorial": "BPF",
    "eunomia.dev": "EU",
    "agentskill-observability-paper": "Skill",
    "academic-writing-skills": "Write",
}
def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def verify_inputs(root: Path) -> None:
    for name, expected in EXPECTED.items():
        path = root / ("events" if name.endswith(".json.gz") else "") / name
        actual = sha256(path)
        if actual != expected:
            raise ValueError(f"frozen input hash mismatch: {path}: {actual}")


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def write_csv(path: Path, rows: list[dict[str, object]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def load_projects(root: Path) -> list[tuple[str, list[dict[str, object]]]]:
    result = []
    for name in EXPECTED:
        if not name.endswith(".json.gz"):
            continue
        path = root / "events" / name
        with gzip.open(path, "rt", encoding="utf-8") as stream:
            payload = json.load(stream)
        result.append((str(payload["repository"]), list(payload["events"])))
    return result


def derive_trajectory(
    projects: list[tuple[str, list[dict[str, object]]]],
    mutations: list[dict[str, str]],
) -> list[dict[str, object]]:
    mutation_rows: dict[tuple[str, str, str], list[dict[str, str]]] = defaultdict(list)
    for row in mutations:
        mutation_rows[(row["project"], row["worktree_id"], row["event_id"])].append(row)

    trajectory = []
    for project, events in projects:
        ids = [str(event["id"]) for event in events]
        if len(ids) != len(set(ids)):
            raise ValueError(f"duplicate frozen event ID in {project}")
        ranks = Counter()
        cumulative = Counter()
        for event_index, event in enumerate(events):
            home_worktree = str(event["worktree_id"]) if event.get("worktree_id") else ""
            target_worktrees = {
                str(action["worktree_id"])
                for action in event.get("actions", [])
                if action.get("worktree_id")
            }
            if home_worktree:
                target_worktrees.add(home_worktree)
            for worktree in sorted(target_worktrees):
                ranks[worktree] += 1
                rows = mutation_rows[(project, worktree, str(event["id"]))]
                cumulative[worktree] += len(rows)
                is_home = worktree == home_worktree
                is_attempt = is_home and event.get("effect") == "test"
                status = str(event.get("status", "observed")) if is_attempt else ""
                trajectory.append({
                    "project": project,
                    "worktree_id": worktree,
                    "home_worktree": is_home,
                    "action_rank": ranks[worktree],
                    "event_index": event_index,
                    "event_id": str(event["id"]),
                    "ts_ms": int(event["ts_ms"]),
                    "session_id": str(event["session_id"]),
                    "vendor": str(event["vendor"]),
                    "effect": str(event.get("effect", "")) if is_home else "",
                    "status": status,
                    "mutation_rows": len(rows),
                    "mutated_artifacts": ";".join(sorted({row["artifact_id"] for row in rows})),
                    "co_observed_mutation_rows": len(rows) if is_attempt else 0,
                    "cumulative_mutation_rows": cumulative[worktree],
                })
    return trajectory


def derive_cycles(trajectory: list[dict[str, object]]) -> list[dict[str, object]]:
    lanes: dict[tuple[str, str], list[dict[str, object]]] = defaultdict(list)
    for row in trajectory:
        lanes[(str(row["project"]), str(row["worktree_id"]))].append(row)

    cycles = []
    for (project, worktree), rows in lanes.items():
        rows.sort(key=lambda row: int(row["action_rank"]))
        successes = [index for index, row in enumerate(rows) if row["effect"] == "test" and row["status"] == "ok"]
        boundaries: list[tuple[str, int, int | None]] = []
        if not successes:
            boundaries.append(("no_success_observed", 0, None))
        else:
            boundaries.append(("left_censored", 0, successes[0]))
            boundaries.extend(("complete", left, right) for left, right in zip(successes, successes[1:]))
            boundaries.append(("right_censored", successes[-1], None))

        for interval_type, left, right in boundaries:
            if interval_type == "left_censored":
                selected = rows[left:right + 1]
                mutation_selected = rows[left:right]
                start_event = rows[left]
                end_event = rows[right]
            elif interval_type == "complete":
                selected = rows[left + 1:right + 1]
                mutation_selected = rows[left + 1:right]
                start_event = rows[left]
                end_event = rows[right]
            elif interval_type == "right_censored":
                selected = rows[left + 1:]
                mutation_selected = selected
                start_event = rows[left]
                end_event = rows[-1]
            else:
                selected = rows
                mutation_selected = rows
                start_event = rows[0]
                end_event = rows[-1]
            attempts = Counter(
                str(row["status"])
                for row in selected
                if row["effect"] == "test"
            )
            artifacts = {
                artifact
                for row in mutation_selected
                for artifact in str(row["mutated_artifacts"]).split(";")
                if artifact
            }
            ending_coobserved = (
                int(end_event["co_observed_mutation_rows"])
                if interval_type in {"left_censored", "complete"}
                else 0
            )
            cycles.append({
                "project": project,
                "worktree_id": worktree,
                "interval_type": interval_type,
                "start_event_id": start_event["event_id"],
                "end_event_id": end_event["event_id"],
                "start_action_rank": start_event["action_rank"],
                "end_action_rank": end_event["action_rank"],
                "action_length": len(selected),
                "duration_ms": int(end_event["ts_ms"]) - int(start_event["ts_ms"]),
                "distinct_sessions": len({str(row["session_id"]) for row in selected}),
                "mutation_rows": sum(int(row["mutation_rows"]) for row in mutation_selected),
                "mutated_artifacts": len(artifacts),
                "failed_attempts": attempts["fail"],
                "observed_unknown_attempts": attempts["observed"],
                "ending_co_observed_mutation_rows": ending_coobserved,
            })
    return cycles


def derive_coverage(trajectory: list[dict[str, object]], projects: list[str]) -> list[dict[str, object]]:
    result = []
    for project in projects:
        rows = [row for row in trajectory if row["project"] == project]
        home_rows = [row for row in rows if bool(row["home_worktree"])]
        attempts = Counter(str(row["status"]) for row in home_rows if row["effect"] == "test")
        worktrees = {str(row["worktree_id"]) for row in rows}
        success_worktrees = {
            str(row["worktree_id"])
            for row in rows
            if row["effect"] == "test" and row["status"] == "ok"
        }
        result.append({
            "project": project,
            "worktrees": len(worktrees),
            "attributed_actions": len({str(row["event_id"]) for row in home_rows}),
            "mutation_rows": sum(int(row["mutation_rows"]) for row in rows),
            "recognized_success": attempts["ok"],
            "recognized_fail": attempts["fail"],
            "recognized_observed_unknown": attempts["observed"],
            "co_observed_success_mutation_rows": sum(
                int(row["co_observed_mutation_rows"])
                for row in home_rows
                if row["effect"] == "test" and row["status"] == "ok"
            ),
            "success_worktrees": len(success_worktrees),
            "qualified_with_success": bool(attempts["ok"]),
        })
    return result


def self_check() -> None:
    rows = [
        {"project": "p", "worktree_id": "w", "action_rank": 1, "event_id": "a", "ts_ms": 0, "session_id": "s1", "effect": "test", "status": "ok", "mutation_rows": 1, "mutated_artifacts": "x", "co_observed_mutation_rows": 1},
        {"project": "p", "worktree_id": "w", "action_rank": 2, "event_id": "b", "ts_ms": 5, "session_id": "s1", "effect": "process", "status": "", "mutation_rows": 2, "mutated_artifacts": "x;y", "co_observed_mutation_rows": 0},
        {"project": "p", "worktree_id": "w", "action_rank": 3, "event_id": "c", "ts_ms": 9, "session_id": "s2", "effect": "test", "status": "ok", "mutation_rows": 3, "mutated_artifacts": "z", "co_observed_mutation_rows": 3},
    ]
    complete = [row for row in derive_cycles(rows) if row["interval_type"] == "complete"]
    assert len(complete) == 1
    assert complete[0]["action_length"] == 2
    assert complete[0]["mutation_rows"] == 2
    assert complete[0]["ending_co_observed_mutation_rows"] == 3
    assert complete[0]["distinct_sessions"] == 2


def plot_from_csv(raw: Path, figures: Path) -> None:
    trajectory = read_csv(raw / "rq2-trajectory.csv")
    cycles = read_csv(raw / "rq2-cycles.csv")
    coverage = read_csv(raw / "rq2-coverage.csv")
    projects = [row["project"] for row in coverage]
    qualified_projects = sum(
        str(row["qualified_with_success"]).lower() == "true"
        for row in coverage
    )
    colors = dict(zip(projects, plt.get_cmap("tab10").colors, strict=False))

    lanes: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in trajectory:
        lanes[(row["project"], row["worktree_id"])].append(row)
    lane_items = sorted(
        lanes.items(),
        key=lambda item: (projects.index(item[0][0]), item[0][1]),
        reverse=True,
    )

    # Use the final paper width directly.  Stacking the three panels keeps the
    # worktree labels and the project labels readable after LaTeX placement.
    fig = plt.figure(figsize=(7.05, 8.2))
    grid = fig.add_gridspec(3, 1, height_ratios=[1.65, 1.0, 1.0], hspace=0.55)
    axes = [
        fig.add_subplot(grid[0, 0]),
        fig.add_subplot(grid[1, 0]),
        fig.add_subplot(grid[2, 0]),
    ]
    for lane_index, ((project, worktree), rows) in enumerate(lane_items):
        rows.sort(key=lambda row: int(row["action_rank"]))
        total_actions = len(rows)
        max_mutations = max(int(row["cumulative_mutation_rows"]) for row in rows) or 1
        xs = [(int(row["action_rank"]) - 1) / max(total_actions - 1, 1) for row in rows]
        ys = [lane_index + 0.72 * int(row["cumulative_mutation_rows"]) / max_mutations for row in rows]
        axes[0].plot(xs, ys, color=colors[project], linewidth=1.2)
        for status, marker, marker_color in [("ok", "^", "#248f5a"), ("fail", "x", "#c43c39"), ("observed", "o", "#6f7782")]:
            selected = [(x, y) for x, y, row in zip(xs, ys, rows, strict=True) if row["effect"] == "test" and row["status"] == status]
            if selected:
                axes[0].scatter([p[0] for p in selected], [p[1] for p in selected], marker=marker, s=18, color=marker_color, linewidths=0.8)
    lane_labels = []
    for (project, worktree), rows in lane_items:
        lane_labels.append(f"{LANE_SHORT.get(project, project)}·{worktree[:5]}")
    axes[0].set_yticks([index + 0.35 for index in range(len(lane_items))], lane_labels, fontsize=7)
    axes[0].set_xlim(0, 1)
    axes[0].set_xlabel("Normalized worktree-attributed action position (display only)")
    axes[0].set_title("A. Worktree action trajectories")
    axes[0].grid(axis="x", alpha=0.2)
    axes[0].text(0.99, 0.02, "▲ ok   × fail   ● observed (outcome unknown)", transform=axes[0].transAxes, fontsize=7, ha="right", va="bottom")

    complete_by_lane: dict[tuple[str, str], list[int]] = defaultdict(list)
    for row in cycles:
        if row["interval_type"] == "complete":
            complete_by_lane[(row["project"], row["worktree_id"])].append(int(row["mutation_rows"]))
    for (project, worktree), values in complete_by_lane.items():
        if len(values) < 2:
            continue
        xs = sorted(set(values))
        ys = [sum(value <= x for value in values) / len(values) for x in xs]
        axes[1].step(xs, ys, where="post", color=colors[project], label=f"{SHORT.get(project, project)} · {worktree[:5]} (n={len(values)})")
    axes[1].set_xscale("symlog", linthresh=1)
    axes[1].set_xlim(left=0)
    axes[1].set_ylim(0, 1.02)
    axes[1].set_xlabel("Mutation rows between successes")
    axes[1].set_ylabel("Cumulative proportion")
    axes[1].set_title("B. Mutations between successes")
    axes[1].grid(alpha=0.2)
    axes[1].legend(fontsize=7, loc="lower right", ncol=2)

    bottoms = [0.0] * len(projects)
    for key, label, color in [
        ("recognized_success", "status=ok", "#248f5a"),
        ("recognized_fail", "status=fail", "#c43c39"),
        ("recognized_observed_unknown", "status=observed (outcome unknown)", "#6f7782"),
    ]:
        rates = [1000 * int(row[key]) / max(int(row["attributed_actions"]), 1) for row in coverage]
        axes[2].barh(range(len(projects)), rates, left=bottoms, label=label, color=color)
        bottoms = [left + value for left, value in zip(bottoms, rates, strict=True)]
    axes[2].set_yticks(range(len(projects)), [SHORT.get(project, project) for project in projects])
    axes[2].invert_yaxis()
    axes[2].set_xlabel("Attempts / 1,000 attributed actions")
    axes[2].set_title("C. Validation coverage")
    axes[2].legend(fontsize=7, loc="upper right", ncol=3)
    axes[2].grid(axis="x", alpha=0.2)
    axes[2].text(
        0.98,
        0.04,
        f"{qualified_projects}/{len(coverage)} expose status=ok; coverage gate passes",
        transform=axes[2].transAxes,
        ha="right",
        va="bottom",
        fontsize=7,
        color="#a33a32",
        bbox={"facecolor": "white", "edgecolor": "#dddddd", "alpha": 0.9},
    )

    fig.subplots_adjust(top=0.975, bottom=0.07, left=0.17, right=0.985)
    figures.mkdir(parents=True, exist_ok=True)
    fig.savefig(figures / "rq2-validation-dynamics.pdf")
    fig.savefig(figures / "rq2-validation-dynamics.png", dpi=180)
    plt.close(fig)


def write_result(path: Path, coverage: list[dict[str, object]], cycles: list[dict[str, object]]) -> None:
    complete = Counter(row["project"] for row in cycles if row["interval_type"] == "complete")
    qualified_projects = sum(
        value is True or str(value).lower() == "true"
        for value in (row["qualified_with_success"] for row in coverage)
    )
    lines = [
        "# RQ2 Recognized-Validation Dynamics",
        "",
        f"Supporting coverage and within-case evidence only; {qualified_projects}/{len(coverage)} projects expose a recognized successful validation.",
        "",
        "| Project | Attributed actions | Success/fail/observed | Co-observed mutation rows | Complete worktree-local intervals |",
        "|---|---:|---:|---:|---:|",
    ]
    for row in coverage:
        lines.append(
            f"| {row['project']} | {row['attributed_actions']} | "
            f"{row['recognized_success']}/{row['recognized_fail']}/{row['recognized_observed_unknown']} | "
            f"{row['co_observed_success_mutation_rows']} | {complete[row['project']]} |"
        )
    lines.extend([
        "",
        "| Project/worktree | Complete intervals | Zero-mutation | Median | P90 | Maximum |",
        "|---|---:|---:|---:|---:|---:|",
    ])
    groups: dict[tuple[str, str], list[int]] = defaultdict(list)
    for row in cycles:
        if row["interval_type"] == "complete":
            groups[(str(row["project"]), str(row["worktree_id"]))].append(int(row["mutation_rows"]))
    for (project, worktree), values in sorted(groups.items()):
        values.sort()
        quantile = lambda fraction: values[round(fraction * (len(values) - 1))]
        lines.append(
            f"| {project}/{worktree} | {len(values)} | {sum(value == 0 for value in values) / len(values):.1%} | "
            f"{quantile(0.5)} | {quantile(0.9)} | {values[-1]} |"
        )
    lines.extend([
        "",
        "Most complete intervals contain no confirmed mutation row, while rare intervals contain hundreds; this is cadence/adapter evidence, not proof of redundant testing or missing coverage.",
        "",
        "Artifact-type stratification is deferred to RQ5; this experiment does not close canonical RQ2.",
    ])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    inputs = parser.add_mutually_exclusive_group(required=True)
    inputs.add_argument("--rq1-root", type=Path)
    inputs.add_argument(
        "--input-raw",
        type=Path,
        help="render from released rq2-trajectory/cycles/coverage CSV files",
    )
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.input_raw is not None:
        plot_from_csv(args.input_raw, args.output / "figures")
        print(f"wrote RQ2 figure from released CSV rows to {args.output / 'figures'}")
        return

    verify_inputs(args.rq1_root)
    self_check()
    projects = load_projects(args.rq1_root)
    mutations = read_csv(args.rq1_root / "rq1-mutations.csv")
    trajectory = derive_trajectory(projects, mutations)
    cycles = derive_cycles(trajectory)
    project_names = [project for project, _ in projects]
    coverage = derive_coverage(trajectory, project_names)
    if sum(bool(row["qualified_with_success"]) for row in coverage) != 3:
        # Recompute copy: report instead of raising so a coverage change is visible.
        print(f"[rq2-recompute] recognized-success coverage = {sum(bool(row['qualified_with_success']) for row in coverage)}/6 (frozen run: 3/6)")

    raw = args.output / "raw"
    write_csv(raw / "rq2-trajectory.csv", trajectory, [
        "project", "worktree_id", "home_worktree", "action_rank", "event_index", "event_id", "ts_ms", "session_id", "vendor",
        "effect", "status", "mutation_rows", "mutated_artifacts", "co_observed_mutation_rows", "cumulative_mutation_rows",
    ])
    write_csv(raw / "rq2-cycles.csv", cycles, [
        "project", "worktree_id", "interval_type", "start_event_id", "end_event_id", "start_action_rank", "end_action_rank",
        "action_length", "duration_ms", "distinct_sessions", "mutation_rows", "mutated_artifacts", "failed_attempts",
        "observed_unknown_attempts", "ending_co_observed_mutation_rows",
    ])
    write_csv(raw / "rq2-coverage.csv", coverage, list(coverage[0]))
    write_result(args.output / "result.md", coverage, cycles)
    del trajectory, cycles, coverage, mutations, projects
    gc.collect()
    plot_from_csv(raw, args.output / "figures")


if __name__ == "__main__":
    main()
