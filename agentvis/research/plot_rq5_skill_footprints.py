#!/usr/bin/env python3
"""Measure source-explicit Skill and instruction footprints.

The unit is a native root session, not a transcript file.  Skill footprints
use Claude's source-native attributionSkill label.  Explicit Skill calls are
audited separately because invocation and execution may live in different
parent/subagent streams.  Instruction access is a separate focal-event
analysis and is never treated as evidence that a harness was active.
"""

from __future__ import annotations

import argparse
import csv
import itertools
import json
import math
import os
import random
from collections import Counter, defaultdict
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


EFFECTS = ("read", "write", "test", "process", "repo", "network", "other")
ARTIFACTS = (
    "code", "test", "paper/docs", "data/results", "config", "other",
    "no-artifact",
)
INSTRUCTION_NAMES = {"AGENTS.md", "CLAUDE.md", "SKILL.md"}
MUTATIONS = {"write", "create", "delete", "rename"}
FEATURES = tuple(f"effect:{x}" for x in EFFECTS) + tuple(
    f"artifact:{x}" for x in ARTIFACTS
)


def artifact_class(path: str) -> str:
    lower = path.lower()
    name = os.path.basename(lower)
    suffix = Path(lower).suffix
    if "test" in lower or "spec" in lower or suffix in {".snap"}:
        return "test"
    if suffix in {
        ".rs", ".py", ".c", ".h", ".cc", ".cpp", ".go", ".java",
        ".js", ".jsx", ".ts", ".tsx", ".sh", ".lua", ".rb",
    }:
        return "code"
    if suffix in {".md", ".rst", ".tex", ".bib", ".typ"} or any(
        token in lower for token in ("docs/", "paper", "readme")
    ):
        return "paper/docs"
    if suffix in {".csv", ".tsv", ".parquet", ".npy", ".npz", ".pdf", ".png", ".svg"} or any(
        token in lower for token in ("results/", "output/", "data/")
    ):
        return "data/results"
    if suffix in {".toml", ".yaml", ".yml", ".json", ".ini", ".cfg", ".lock"} or name in {
        "makefile", "dockerfile", ".gitignore",
    }:
        return "config"
    return "other"


def effect_name(event: dict) -> str:
    effect = event.get("effect") or "other"
    return effect if effect in EFFECTS else "other"


def normalized_blocks(counts: Counter) -> tuple[np.ndarray, np.ndarray]:
    effect = np.array([counts[f"effect:{x}"] for x in EFFECTS], dtype=float)
    artifact = np.array([counts[f"artifact:{x}"] for x in ARTIFACTS], dtype=float)
    if effect.sum():
        effect /= effect.sum()
    if artifact.sum():
        artifact /= artifact.sum()
    return effect, artifact


def normalized_feature(counts: Counter) -> np.ndarray:
    effect, artifact = normalized_blocks(counts)
    return np.concatenate((effect * 0.5, artifact * 0.5))


def jsd(left: np.ndarray, right: np.ndarray) -> float:
    middle = (left + right) / 2

    def kl(value: np.ndarray, target: np.ndarray) -> float:
        mask = value > 0
        return float(np.sum(value[mask] * np.log2(value[mask] / target[mask])))

    return math.sqrt(max(0.0, (kl(left, middle) + kl(right, middle)) / 2))


def load_projects(root: Path) -> list[tuple[str, list[dict]]]:
    projects = []
    for path in sorted((root / "events").glob("*.json")):
        with path.open() as stream:
            trace = json.load(stream)
        projects.append((path.stem, trace["events"]))
    if not projects:
        raise SystemExit(f"no event JSON files under {root / 'events'}")
    return projects


def source_coverage(project: str, events: list[dict]) -> dict:
    invocations = [event for event in events if event.get("skill_name")]
    attributed = [event for event in events if event.get("attribution_skill")]
    streams: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for event in events:
        streams[(event["native_session_id"], event["source_stream_id"])].append(event)

    linked_ids = set()
    linked_roots = set()
    for stream_events in streams.values():
        active: tuple[str, str] | None = None
        for event in sorted(stream_events, key=lambda row: (row["ts_ms"], row["id"])):
            if event.get("skill_name"):
                active = (event["id"], event["skill_name"])
                continue
            attribution = event.get("attribution_skill")
            if not attribution:
                active = None
                continue
            if active and attribution == active[1]:
                linked_ids.add(event["id"])
                linked_roots.add(event["native_session_id"])
            else:
                active = None

    return {
        "project": project,
        "tool_events": len(events),
        "native_root_sessions": len({event["native_session_id"] for event in events}),
        "source_streams": len({event["source_stream_id"] for event in events}),
        "skill_invocations": len(invocations),
        "invocation_roots": len({event["native_session_id"] for event in invocations}),
        "attributed_actions": len(attributed),
        "attribution_roots": len({event["native_session_id"] for event in attributed}),
        "contiguous_preceded_actions": len(linked_ids),
        "contiguous_preceded_roots": len(linked_roots),
        "not_contiguous_preceded_actions": len(attributed) - len(linked_ids),
        "long_argument_invocations": sum(
            len(event.get("skill_args") or "") > 300 for event in invocations
        ),
    }


def skill_footprints(project: str, events: list[dict]) -> list[dict]:
    groups: dict[tuple[str, str, str, str, str], list[dict]] = defaultdict(list)
    for event in events:
        skill = event.get("attribution_skill")
        if skill:
            groups[
                (
                    event["vendor"],
                    event.get("model") or "unknown",
                    event.get("source_role") or "unknown",
                    event["native_session_id"],
                    skill,
                )
            ].append(event)

    rows = []
    for (vendor, model, source_role, root_session, skill), group in sorted(groups.items()):
        counts = Counter()
        touched = set()
        for event in group:
            counts[f"effect:{effect_name(event)}"] += 1
            for action in event.get("actions", []):
                kind = artifact_class(action["path"])
                counts[f"artifact:{kind}"] += 1
                touched.add((action.get("worktree_id", ""), action["path"]))
        if not touched:
            counts["artifact:no-artifact"] = 1
        vector = normalized_feature(counts)
        effect_vector, artifact_vector = normalized_blocks(counts)
        rows.append(
            {
                "project": project,
                "vendor": vendor,
                "native_root_session_id": root_session,
                "skill": skill,
                "model": model,
                "source_role": source_role,
                "actions": len(group),
                "touched_artifacts": len(touched),
                "failed_actions": sum(event.get("status") == "fail" for event in group),
                "vector": vector,
                "effect_vector": effect_vector,
                "artifact_vector": artifact_vector,
                **{feature: counts[feature] for feature in FEATURES},
            }
        )
    return rows


def instruction_rows(project: str, events: list[dict]) -> list[dict]:
    streams: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for event in events:
        streams[(event["native_session_id"], event["source_stream_id"])].append(event)
    rows = []
    for stream_events in streams.values():
        stream_events.sort(key=lambda row: (row["ts_ms"], row["id"]))
        for index, event in enumerate(stream_events):
            matched = [
                path
                for path in event.get("source_paths", [])
                if os.path.basename(path.get("path", "")) in INSTRUCTION_NAMES
            ]
            if not matched:
                continue
            accesses = {path.get("access", "") for path in matched}
            kind = "mutation" if accesses & MUTATIONS else "read"
            row = {
                "project": project,
                "vendor": event["vendor"],
                "native_root_session_id": event["native_session_id"],
                "source_stream_id": event["source_stream_id"],
                "source_call_id": event.get("source_call_id") or "",
                "event_id": event["id"],
                "status": event.get("status", "unknown"),
                "kind": kind,
                "files": ";".join(sorted({os.path.basename(path["path"]) for path in matched})),
                "following_actions": 0,
                "next_event_id": "",
                "following_effect": "",
                "following_status": "",
            }
            prompt_index = event.get("prompt_index")
            for later in stream_events[index + 1 :]:
                if later.get("prompt_index") != prompt_index:
                    break
                row["following_actions"] = 1
                row["next_event_id"] = later["id"]
                row["following_effect"] = effect_name(later)
                row["following_status"] = later.get("status", "unknown")
                break
            rows.append(row)
    return rows


def distance_rows(footprints: list[dict]) -> list[dict]:
    eligible = qualifying_skills(footprints)
    by_context: dict[tuple[str, str, str, str], list[dict]] = defaultdict(list)
    for row in footprints:
        key = (
            row["project"], row["vendor"], row["model"],
            row["source_role"], row["skill"],
        )
        if key not in eligible:
            continue
        by_context[(row["project"], row["vendor"], row["model"], row["source_role"])].append(row)
    output = []
    for context, rows in by_context.items():
        if len({row["skill"] for row in rows}) < 2:
            continue
        for index, left in enumerate(rows):
            for right in rows[index + 1 :]:
                if left["native_root_session_id"] == right["native_root_session_id"]:
                    continue
                output.append(
                    {
                        "project": context[0],
                        "vendor": context[1],
                        "model": context[2],
                        "source_role": context[3],
                        "left_skill": left["skill"],
                        "right_skill": right["skill"],
                        "left_root": left["native_root_session_id"],
                        "right_root": right["native_root_session_id"],
                        "same_skill": left["skill"] == right["skill"],
                        "distance": jsd(left["vector"], right["vector"]),
                        "effect_distance": jsd(
                            left["effect_vector"], right["effect_vector"]
                        ),
                        "artifact_distance": jsd(
                            left["artifact_vector"], right["artifact_vector"]
                        ),
                    }
                )
    return output


def comparison_footprints(footprints: list[dict]) -> list[dict]:
    eligible = qualifying_skills(footprints)
    by_context: dict[tuple[str, str, str, str], list[dict]] = defaultdict(list)
    for row in footprints:
        key = (
            row["project"], row["vendor"], row["model"],
            row["source_role"], row["skill"],
        )
        if key in eligible:
            by_context[key[:4]].append(row)
    return [
        row
        for rows in by_context.values()
        if len({row["skill"] for row in rows}) >= 2
        for row in rows
    ]


def distance_stat(rows: list[dict], labels: dict[int, str] | None = None) -> float | None:
    same = []
    different = []
    by_context: dict[tuple[str, str, str, str], list[dict]] = defaultdict(list)
    for row in rows:
        by_context[(row["project"], row["vendor"], row["model"], row["source_role"])].append(row)
    for context_rows in by_context.values():
        for index, left in enumerate(context_rows):
            for right in context_rows[index + 1 :]:
                if left["native_root_session_id"] == right["native_root_session_id"]:
                    continue
                value = jsd(left["vector"], right["vector"])
                left_label = labels.get(id(left), left["skill"]) if labels else left["skill"]
                right_label = labels.get(id(right), right["skill"]) if labels else right["skill"]
                (same if left_label == right_label else different).append(value)
    if not same or not different:
        return None
    return float(np.median(same) - np.median(different))


def unique_permutations(values: list) -> list[tuple]:
    return sorted(set(itertools.permutations(values)))


def exact_context_labels(rows: list[dict], limit: int = 100_000) -> list[dict[int, str]] | None:
    by_root: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        by_root[row["native_root_session_id"]].append(row)
    by_size: dict[int, list[list[dict]]] = defaultdict(list)
    for root, root_rows in sorted(by_root.items()):
        by_size[len(root_rows)].append(sorted(root_rows, key=lambda row: row["skill"]))
    assignments = [{}]
    for root_groups in by_size.values():
        packets = [tuple(row["skill"] for row in group) for group in root_groups]
        group_assignments = []
        for packet_order in unique_permutations(packets):
            within_options = [unique_permutations(list(packet)) for packet in packet_order]
            for within in itertools.product(*within_options):
                labels = {}
                for target, packet in zip(root_groups, within):
                    labels.update({id(row): label for row, label in zip(target, packet)})
                group_assignments.append(labels)
                if len(group_assignments) > limit:
                    return None
        assignments = [
            {**left, **right}
            for left in assignments
            for right in group_assignments
        ]
        if len(assignments) > limit:
            return None
    return assignments


def root_block_permutation(
    footprints: list[dict], repetitions: int = 10_000, seed: int = 20260722
) -> tuple[float | None, float | None, int, int, str]:
    rows = comparison_footprints(footprints)
    observed = distance_stat(rows)
    if observed is None:
        return None, None, 0, 0, "N/A"
    by_context: dict[tuple[str, str, str, str], list[dict]] = defaultdict(list)
    for row in rows:
        by_context[(row["project"], row["vendor"], row["model"], row["source_role"])].append(row)
    context_assignments = [exact_context_labels(context_rows) for context_rows in by_context.values()]
    if all(assignments is not None for assignments in context_assignments):
        null = []
        for choices in itertools.product(*context_assignments):
            labels = {}
            for choice in choices:
                labels.update(choice)
            value = distance_stat(rows, labels)
            if value is not None:
                null.append(value)
        if null:
            p_value = sum(value <= observed for value in null) / len(null)
            return observed, p_value, len(null), len(set(null)), "exact"

    rng = random.Random(seed)
    null = []
    for _ in range(repetitions):
        labels: dict[int, str] = {}
        for context_rows in by_context.values():
            by_root: dict[str, list[dict]] = defaultdict(list)
            for row in context_rows:
                by_root[row["native_root_session_id"]].append(row)
            by_size: dict[int, list[list[dict]]] = defaultdict(list)
            for root_rows in by_root.values():
                by_size[len(root_rows)].append(root_rows)
            for root_groups in by_size.values():
                packets = [[row["skill"] for row in group] for group in root_groups]
                rng.shuffle(packets)
                for target, packet in zip(root_groups, packets):
                    rng.shuffle(packet)
                    for row, label in zip(target, packet):
                        labels[id(row)] = label
        value = distance_stat(rows, labels)
        if value is not None:
            null.append(value)
    if not null:
        return observed, None, 0, 0, "N/A"
    p_value = (1 + sum(value <= observed for value in null)) / (len(null) + 1)
    return observed, p_value, len(null), len(set(null)), "Monte Carlo"


def write_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def qualifying_skills(footprints: list[dict]) -> dict[tuple[str, str, str, str, str], int]:
    roots: dict[tuple[str, str, str, str, str], set[str]] = defaultdict(set)
    for row in footprints:
        roots[
            (
                row["project"], row["vendor"], row["model"],
                row["source_role"], row["skill"],
            )
        ].add(row["native_root_session_id"])
    return {key: len(value) for key, value in roots.items() if len(value) >= 3}


def plot_skill(coverage: list[dict], footprints: list[dict], distances: list[dict], output: Path) -> None:
    qualified = qualifying_skills(footprints)
    projects = [row["project"] for row in coverage]
    fig, axes = plt.subplots(1, 3, figsize=(14.2, 4.7), constrained_layout=True)

    x = np.arange(len(projects))
    axes[0].bar(x - 0.22, [row["invocation_roots"] for row in coverage], 0.22, label="invocation roots")
    axes[0].bar(x, [row["attribution_roots"] for row in coverage], 0.22, label="attribution roots")
    axes[0].bar(
        x + 0.22,
        [row["contiguous_preceded_roots"] for row in coverage],
        0.22,
        label="contiguously preceded roots",
    )
    axes[0].set_xticks(x, projects, rotation=35, ha="right")
    axes[0].set_ylabel("native root sessions")
    axes[0].set_title("A. Source-explicit Skill coverage")
    axes[0].legend(fontsize=7)

    skills = sorted(qualified, key=lambda key: (-qualified[key], key))
    if skills:
        labels = [
            f"{project} · {vendor} · {role}\n{skill}"
            for project, vendor, _model, role, skill in skills
        ]
        axes[1].barh(range(len(skills)), [qualified[key] for key in skills], color="#7957d5")
        axes[1].set_yticks(range(len(skills)), labels, fontsize=7)
        axes[1].invert_yaxis()
        axes[1].axvline(3, color="#333333", linestyle="--", linewidth=1)
        axes[1].set_xlabel("independent native root sessions")
    else:
        axes[1].text(0.5, 0.5, "No Skill meets n≥3", ha="center", va="center")
    axes[1].set_title("B. Qualified attributed footprints")

    same = [row["distance"] for row in distances if row["same_skill"]]
    different = [row["distance"] for row in distances if not row["same_skill"]]
    if same and different:
        # Pair distances share native-root footprints, so show the finite
        # descriptive support directly instead of implying an independent
        # sample distribution with a violin density.
        for position, values, color in (
            (1, same, "#32b67a"),
            (2, different, "#e76f51"),
        ):
            offsets = np.linspace(-0.10, 0.10, len(values))
            axes[2].scatter(
                position + offsets,
                values,
                color=color,
                edgecolor="white",
                linewidth=0.6,
                s=34,
                alpha=0.9,
                zorder=3,
            )
            median = float(np.median(values))
            axes[2].hlines(median, position - 0.18, position + 0.18, color="#172033", linewidth=2)
        axes[2].set_xticks([1, 2], [f"same Skill\nn={len(same)}", f"different Skill\nn={len(different)}"])
        axes[2].set_ylabel("Jensen–Shannon distance")
        axes[2].set_xlabel("descriptive root-pair distances")
    else:
        axes[2].text(0.5, 0.5, "Matched comparison N/A", ha="center", va="center")
        axes[2].set_xticks([])
    comparison_projects = len({row["project"] for row in distances})
    _delta, p_value, _permutations, _unique, _method = root_block_permutation(footprints)
    if p_value is not None:
        axes[2].set_title(
            f"C. No supported separation (p={p_value:.3f})"
        )
    else:
        axes[2].set_title(f"C. Qualified comparison ({comparison_projects} project)")
    fig.suptitle("F9a · Named Skill footprints (observational, source-attributed)", fontsize=13)
    fig.savefig(output / "rq5-skill-footprints.png", dpi=180)
    fig.savefig(output / "rq5-skill-footprints.pdf")
    plt.close(fig)


def plot_instruction(instructions: list[dict], output: Path) -> None:
    successful = [
        row for row in instructions
        if row["status"] == "ok" and row["high_confidence"]
    ]
    projects = sorted({row["project"] for row in instructions})
    fig, axes = plt.subplots(1, 2, figsize=(13.5, 6.2), constrained_layout=True)
    x = np.arange(len(projects))
    reads = [sum(row["project"] == project and row["kind"] == "read" for row in successful) for project in projects]
    mutations = [sum(row["project"] == project and row["kind"] == "mutation" for row in successful) for project in projects]
    axes[0].bar(x - 0.18, reads, 0.36, label="successful read", color="#4f8dd6")
    axes[0].bar(x + 0.18, mutations, 0.36, label="successful mutation", color="#e76f51")
    if max(reads + mutations, default=0) > 100:
        axes[0].set_yscale("log")
    axes[0].set_xticks(x, projects, rotation=35, ha="right")
    axes[0].set_ylabel("successful focal events")
    axes[0].set_title("A. Explicit instruction-file access")
    axes[0].legend(fontsize=8)

    next_rows = [row for row in successful if row["following_actions"]]
    labels = []
    matrix = []
    for project in projects:
        for kind in ("read", "mutation"):
            subset = [
                row for row in next_rows
                if row["project"] == project and row["kind"] == kind
            ]
            if not subset:
                continue
            counts = Counter(row["following_effect"] for row in subset)
            matrix.append([counts[effect] / len(subset) for effect in EFFECTS])
            labels.append(f"{project} · {kind} (n={len(subset)})")
    image = axes[1].imshow(np.array(matrix), aspect="auto", vmin=0, vmax=1, cmap="Blues")
    axes[1].set_xticks(range(len(EFFECTS)), EFFECTS, rotation=35, ha="right")
    axes[1].set_yticks(range(len(labels)), labels, fontsize=7)
    for row_index, values in enumerate(matrix):
        for column_index, value in enumerate(values):
            if value >= 0.05:
                axes[1].text(
                    column_index, row_index, f"{value:.0%}", ha="center", va="center",
                    fontsize=6, color="white" if value >= 0.55 else "#172033",
                )
    fig.colorbar(image, ax=axes[1], fraction=0.035, pad=0.02, label="within-project share")
    axes[1].set_title("B. Immediate next action before next prompt")
    fig.suptitle("F9b · Instruction access is a focal event, not harness exposure", fontsize=13)
    fig.savefig(output / "rq5-instruction-footprints.png", dpi=180)
    fig.savefig(output / "rq5-instruction-footprints.pdf")
    plt.close(fig)


def write_result(
    path: Path,
    coverage: list[dict],
    footprints: list[dict],
    distances: list[dict],
    instructions: list[dict],
) -> None:
    qualified = qualifying_skills(footprints)
    same = [row["distance"] for row in distances if row["same_skill"]]
    different = [row["distance"] for row in distances if not row["same_skill"]]
    comparison_projects = sorted({row["project"] for row in distances})
    observed_delta, permutation_p, permutation_n, unique_stats, permutation_method = root_block_permutation(footprints)
    with path.open("w") as out:
        out.write("# RQ5 Source-Explicit Skill And Instruction Footprints\n\n")
        out.write("This is an observational multi-case analysis. `attributionSkill` is source-native evidence; it does not prove that a Skill caused a useful or harmful outcome. A transcript file is not an independent session: all rows are blocked by native root session.\n\n")
        out.write("## Coverage\n\n")
        out.write("| Project | Tool events | Native roots | Skill calls (roots) | Attributed actions (roots) | Contiguously preceded actions (roots) | Not contiguously preceded | Args >300 |\n")
        out.write("|---|---:|---:|---:|---:|---:|---:|---:|\n")
        for row in coverage:
            out.write(
                f"| {row['project']} | {row['tool_events']} | {row['native_root_sessions']} | "
                f"{row['skill_invocations']} ({row['invocation_roots']}) | "
                f"{row['attributed_actions']} ({row['attribution_roots']}) | "
                f"{row['contiguous_preceded_actions']} ({row['contiguous_preceded_roots']}) | {row['not_contiguous_preceded_actions']} | "
                f"{row['long_argument_invocations']} |\n"
            )
        out.write("\nThe contiguous same-stream count is only a conservative coverage diagnostic: a matching Skill call immediately precedes an attributed run with no intervening unattributed Tool event. It is not an exact invocation join or episode boundary. Parent invocation and delegated execution may occupy different streams, so primary footprints use source-native attribution only.\n\n")
        out.write("## Qualified footprints\n\n")
        out.write("A named Skill qualifies only with attribution in at least three distinct native root sessions inside one exact project/vendor/model/source-role stratum.\n\n")
        out.write("| Project | Vendor/model/role | Skill | Native roots | Attributed actions |\n|---|---|---|---:|---:|\n")
        for (project, vendor, model, role, skill), roots in sorted(qualified.items()):
            actions = sum(
                row["actions"] for row in footprints
                if (row["project"], row["vendor"], row["model"], row["source_role"], row["skill"])
                == (project, vendor, model, role, skill)
            )
            out.write(f"| {project} | {vendor}/{model}/{role} | {skill} | {roots} | {actions} |\n")
        if not qualified:
            out.write("| — | — | — | N/A | N/A |\n")
        out.write("\n")
        if same and different:
            out.write(
                f"Only {', '.join(comparison_projects)} contains at least two qualified Skills in one exact project/vendor/model/source-role stratum. Within that case, median JSD is {np.median(same):.3f} for same-Skill pairs (n={len(same)}) and {np.median(different):.3f} for different-Skill pairs (n={len(different)}). This is a within-case descriptive association, not evidence for a cross-project fingerprint or causal effect.\n\n"
            )
            if permutation_p is not None:
                method = "one-sided exact" if permutation_method == "exact" else "one-sided Monte Carlo"
                out.write(
                    f"The root-block randomization statistic (median same minus median different) is {observed_delta:.3f}; {method} p={permutation_p:.3f} over {permutation_n:,} admissible assignments ({unique_stats} unique statistic values). "
                )
            else:
                out.write(
                    "The root-block randomization is N/A because no valid label assignment retained both pair classes. "
                )
            same_effect = [row["effect_distance"] for row in distances if row["same_skill"]]
            different_effect = [row["effect_distance"] for row in distances if not row["same_skill"]]
            same_artifact = [row["artifact_distance"] for row in distances if row["same_skill"]]
            different_artifact = [row["artifact_distance"] for row in distances if not row["same_skill"]]
            out.write(
                f"Action-only medians are {np.median(same_effect):.3f}/{np.median(different_effect):.3f} (same/different); artifact-only medians are {np.median(same_artifact):.3f}/{np.median(different_artifact):.3f}. "
                "Leave-one-project-out is N/A when only one project passes the exact comparison gate. Boundary-only membership is N/A because delegated execution crosses source streams and the source exposes no defensible per-invocation end boundary.\n\n"
            )
        else:
            out.write("The matched distance comparison is N/A because the exact support gate is not met.\n\n")
        instruction_counts = Counter(
            (row["project"], row["kind"], row["status"])
            for row in instructions if row["high_confidence"]
        )
        out.write("## Instruction focal events\n\n")
        out.write("Instruction reads/mutations are reported separately and never treated as proof of harness exposure or compliance. The primary plot uses only independently source-recomputed, high-confidence successful focal events; the CSV retains the broader parser set as sensitivity rows. Immediate following actions are counted at most once per focal event and only before a native prompt-index change.\n\n")
        out.write("| Project | Read ok/observed/fail | Mutation ok/observed/fail | Roots |\n|---|---:|---:|---:|\n")
        for project in [row["project"] for row in coverage]:
            values = []
            for kind in ("read", "mutation"):
                values.append("/".join(str(instruction_counts[(project, kind, status)]) for status in ("ok", "observed", "fail")))
            roots = len({
                row["native_root_session_id"]
                for row in instructions
                if row["project"] == project and row["high_confidence"]
            })
            out.write(f"| {project} | {values[0]} | {values[1]} | {roots} |\n")
        out.write("\n## Interpretation stop\n\n")
        out.write("These six author-associated projects are selected natural cases, not a representative sample of agents, repositories, or tasks. Repository-direct source streams were used (`global=false`). The study can characterize recoverable structure and expose measurement failures; it cannot estimate prevalence, productivity, waste, or causal Skill/harness effects.\n")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--source-audit", type=Path)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    projects = load_projects(args.input)
    coverage = []
    footprints = []
    instructions = []
    for project, events in projects:
        coverage.append(source_coverage(project, events))
        footprints.extend(skill_footprints(project, events))
        instructions.extend(instruction_rows(project, events))
    audit_path = args.source_audit or args.output / "source-check-instructions.csv"
    if not audit_path.exists():
        raise SystemExit(f"missing independent instruction audit: {audit_path}")
    with audit_path.open() as stream:
        audit = {
            (row["project"], row["source_stream_id"], row["source_call_id"]): row
            for row in csv.DictReader(stream)
        }
    for row in instructions:
        key = (row["project"], row["source_stream_id"], row["source_call_id"])
        source = audit.get(key)
        row["high_confidence"] = source is not None
        row["source_kind"] = source["source_kind"] if source else ""
        if source and row["kind"] != source["source_kind"]:
            raise SystemExit(f"instruction kind mismatch for {key}")
    distances = distance_rows(footprints)

    coverage_fields = list(coverage[0])
    footprint_fields = [
        "project", "vendor", "native_root_session_id", "skill", "model",
        "source_role", "actions", "touched_artifacts", "failed_actions", *FEATURES,
    ]
    distance_fields = [
        "project", "vendor", "model", "source_role", "left_skill",
        "right_skill", "left_root", "right_root", "same_skill", "distance",
        "effect_distance", "artifact_distance",
    ]
    instruction_fields = [
        "project", "vendor", "native_root_session_id", "source_stream_id", "source_call_id",
        "event_id", "status", "kind", "files", "following_actions",
        "next_event_id", "following_effect", "following_status",
        "high_confidence", "source_kind",
    ]
    write_csv(args.output / "rq5-source-coverage.csv", coverage, coverage_fields)
    write_csv(args.output / "rq5-skill-footprints.csv", footprints, footprint_fields)
    write_csv(args.output / "rq5-skill-distances.csv", distances, distance_fields)
    write_csv(args.output / "rq5-instruction-events.csv", instructions, instruction_fields)
    plot_skill(coverage, footprints, distances, args.output)
    plot_instruction(instructions, args.output)
    write_result(args.output / "result.md", coverage, footprints, distances, instructions)


if __name__ == "__main__":
    main()
