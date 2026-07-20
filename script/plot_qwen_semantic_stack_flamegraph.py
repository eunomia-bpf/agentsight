#!/usr/bin/env python3
"""Plot one fixed Qwen semantic-stack trajectory against two references."""

from __future__ import annotations

import argparse
import hashlib
import json
import textwrap
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle


DEFAULT_SESSION = (
    "openhands-Anthropic__Claude-Sonnet-4-20250514-Thinking-"
    "3d-model-format-legacy-7498555b"
)

PALETTE = (
    "#4477AA",
    "#EE6677",
    "#228833",
    "#CCBB44",
    "#66CCEE",
    "#AA3377",
    "#BBBBBB",
    "#EE7733",
)

plt.rcParams.update(
    {
        "font.size": 8,
        "axes.labelsize": 8,
        "xtick.labelsize": 7,
        "ytick.labelsize": 7,
        "font.family": "serif",
        "axes.grid": False,
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
    }
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--predictions", type=Path, required=True)
    parser.add_argument("--contracted", type=Path, required=True)
    parser.add_argument("--assignments", type=Path, required=True)
    parser.add_argument("--session", default=DEFAULT_SESSION)
    parser.add_argument("--output-prefix", type=Path, required=True)
    return parser.parse_args()


def read_session(path: Path, session: str) -> list[dict]:
    rows = []
    with path.open(encoding="utf-8") as source:
        for line in source:
            row = json.loads(line)
            if row["session"] == session:
                rows.append(row)
    rows.sort(key=lambda row: int(row["step_id"]))
    if not rows:
        raise RuntimeError(f"session not found in {path}: {session}")
    expected = list(range(1, len(rows) + 1))
    actual = [int(row["step_id"]) for row in rows]
    if actual != expected:
        raise RuntimeError(f"non-consecutive steps in {path}: {actual[:5]}")
    return rows


def color_for(key: str, *, root: bool = False) -> str:
    if root:
        return "#17365D"
    digest = hashlib.sha256(key.encode("utf-8")).digest()
    return PALETTE[digest[0] % len(PALETTE)]


def short_identifier(identifier: str, prefix: str) -> str:
    suffix = identifier.rsplit("-", 1)[-1]
    if suffix.isdigit():
        return f"{prefix} {int(suffix)}"
    return prefix


def group_stacks(assignments: list[dict], field: str, prefix: str) -> list[list[dict]]:
    task = assignments[0]["task_name"].replace("-", " ")
    stacks = []
    for row in assignments:
        identifier = str(row[field])
        stacks.append(
            [
                {"instance": "task-root", "label": task, "kind": "task_root"},
                {
                    "instance": identifier,
                    "label": short_identifier(identifier, prefix),
                    "kind": "reference_group",
                },
            ]
        )
    return stacks


def raw_stacks(predictions: list[dict]) -> list[list[dict]]:
    task = predictions[0]["task_text"]
    root = {"instance": "task-root", "label": task, "kind": "task_root"}
    return [[root, *row["stack_after"]] for row in predictions]


def contiguous_rectangles(stacks: list[list[dict]]) -> list[tuple[int, int, int, dict]]:
    maximum = max(len(stack) for stack in stacks)
    rectangles = []
    for depth in range(maximum):
        start = 0
        current = stacks[0][depth] if depth < len(stacks[0]) else None
        for index in range(1, len(stacks) + 1):
            nxt = stacks[index][depth] if index < len(stacks) and depth < len(stacks[index]) else None
            current_id = None if current is None else current["instance"]
            next_id = None if nxt is None else nxt["instance"]
            if current_id != next_id:
                if current is not None:
                    rectangles.append((start, index - start, depth, current))
                start = index
                current = nxt
    return rectangles


def draw_stack_panel(ax, stacks: list[list[dict]], label: str, *, show_x: bool) -> None:
    operation_count = len(stacks)
    maximum = max(len(stack) for stack in stacks)
    for start, width, depth, frame in contiguous_rectangles(stacks):
        root = frame.get("kind") == "task_root"
        rectangle = Rectangle(
            (start, depth),
            width,
            0.86,
            facecolor=color_for(str(frame["label"]), root=root),
            edgecolor="white",
            linewidth=0.55,
        )
        ax.add_patch(rectangle)
        if width >= max(7, operation_count * 0.09):
            chars = max(9, int(width * 1.25))
            text = textwrap.shorten(str(frame["label"]), width=chars, placeholder="…")
            ax.text(
                start + width / 2,
                depth + 0.43,
                text,
                ha="center",
                va="center",
                fontsize=7,
                color="white" if root else "black",
                clip_on=True,
            )
    ax.set_xlim(0, operation_count)
    ax.set_ylim(0, maximum)
    ax.set_yticks([depth + 0.43 for depth in range(maximum)])
    ax.set_yticklabels([str(depth) for depth in range(maximum)])
    ax.set_ylabel("Stack depth")
    ax.text(
        0.0,
        1.02,
        label,
        transform=ax.transAxes,
        ha="left",
        va="bottom",
        fontweight="bold",
        fontsize=8,
    )
    if show_x:
        ax.set_xlabel("Operation index (each operation has unit width)")
    else:
        ax.tick_params(labelbottom=False)
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)


def main() -> None:
    args = parse_args()
    predictions = read_session(args.predictions, args.session)
    contracted = read_session(args.contracted, args.session)
    assignments = read_session(args.assignments, args.session)
    if not (len(predictions) == len(contracted) == len(assignments)):
        raise RuntimeError("input coverage differs for selected session")

    stacks = [
        raw_stacks(predictions),
        [row["effective_stack"] for row in contracted],
        group_stacks(assignments, "multires_recurrence", "Recurrence group"),
        group_stacks(assignments, "official_stage", "Human stage"),
    ]
    labels = [
        "(a) Raw Qwen 3B variable-depth stack",
        "(b) After support-at-least-two contraction",
        "(c) Multi-resolution recurrence comparator",
        "(d) Official human stage partition (evaluation only)",
    ]

    height_ratios = [max(len(stack) for stack in panel) for panel in stacks]
    figure, axes = plt.subplots(
        4,
        1,
        figsize=(10.2, 7.4),
        sharex=True,
        gridspec_kw={"height_ratios": height_ratios, "hspace": 0.34},
    )
    for index, (ax, panel, label) in enumerate(zip(axes, stacks, labels)):
        draw_stack_panel(ax, panel, label, show_x=index == len(axes) - 1)

    figure.subplots_adjust(left=0.075, right=0.995, top=0.975, bottom=0.075)
    args.output_prefix.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(args.output_prefix.with_suffix(".pdf"), bbox_inches="tight")
    figure.savefig(args.output_prefix.with_suffix(".png"), dpi=240, bbox_inches="tight")
    plt.close(figure)

    metadata = {
        "session": args.session,
        "task": predictions[0]["task_text"],
        "operations": len(predictions),
        "raw_maximum_depth_including_task_root": max(len(stack) for stack in stacks[0]),
        "contracted_maximum_depth_including_task_root": max(len(stack) for stack in stacks[1]),
        "outputs": {
            "pdf": str(args.output_prefix.with_suffix(".pdf")),
            "png": str(args.output_prefix.with_suffix(".png")),
        },
    }
    print(json.dumps(metadata, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
