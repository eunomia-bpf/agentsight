#!/usr/bin/env python3
"""Build paper figures from generated visexp artifacts."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle


PAPER_DIR = Path(__file__).resolve().parent
VIS_DIR = PAPER_DIR.parent
OUT_DIR = VIS_DIR / "out"
FIG_DIR = PAPER_DIR / "figures"


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def read_folded(path: Path) -> Counter[str]:
    stacks: Counter[str] = Counter()
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        stack, _, weight = line.rpartition(" ")
        stacks[stack] += int(weight)
    return stacks


def save(fig, name: str) -> None:
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIG_DIR / name, bbox_inches="tight")
    plt.close(fig)


def draw_model() -> None:
    fig, ax = plt.subplots(figsize=(7.2, 2.4))
    ax.axis("off")
    boxes = [
        ("Session", 0.02, 0.62, 0.14),
        ("Prompt", 0.20, 0.62, 0.14),
        ("LLM call", 0.38, 0.62, 0.14),
        ("Tool call", 0.56, 0.62, 0.14),
        ("Child proc", 0.74, 0.62, 0.14),
        ("File/net", 0.56, 0.20, 0.32),
    ]
    for label, x, y, w in boxes:
        ax.add_patch(Rectangle((x, y), w, 0.22, facecolor="#eef2e8", edgecolor="#4b5563", linewidth=1))
        ax.text(x + w / 2, y + 0.11, label, ha="center", va="center", fontsize=10)
    arrows = [
        (0.16, 0.73, 0.20, 0.73),
        (0.34, 0.73, 0.38, 0.73),
        (0.52, 0.73, 0.56, 0.73),
        (0.70, 0.73, 0.74, 0.73),
        (0.63, 0.62, 0.63, 0.42),
        (0.80, 0.62, 0.72, 0.42),
    ]
    for x1, y1, x2, y2 in arrows:
        ax.annotate("", xy=(x2, y2), xytext=(x1, y1), arrowprops={"arrowstyle": "->", "lw": 1.1})
    ax.text(0.08, 0.43, "one-word tags", ha="left", va="center", fontsize=9, color="#2f855a")
    ax.text(0.57, 0.05, "folded stack: session/prompt tag + lineage/tool-log footprint", ha="left", fontsize=9)
    save(fig, "fig-model.pdf")


def draw_results() -> None:
    evaluation = read_json(OUT_DIR / "evaluation.json")
    compression = evaluation["aggregation_strength"]["semantic_system"]
    nonsemantic = evaluation["semantic_information_gain"]["nonsemantic_stack_mixing"]
    flat = evaluation["semantic_information_gain"]["flat_effect_mixing"]
    lineage = evaluation["effect_lineage_smoke"]
    quality = evaluation["tag_quality"]
    values = [
        compression["collapsed_observation_share_pct"],
        nonsemantic["mixed_weight_share_pct"],
        flat["mixed_weight_share_pct"],
        lineage["join_rate_pct"],
        quality["generic_prompt_row_share_pct"],
    ]
    labels = ["Collapsed", "Nonsem. mix", "Flat mix", "C6 fixture", "Generic tags"]
    colors = ["#2f855a", "#2b6cb0", "#b7791f", "#2f855a", "#c53030"]
    fig, ax = plt.subplots(figsize=(7.1, 2.6))
    ax.bar(labels, values, color=colors)
    ax.set_ylim(0, 105)
    ax.set_ylabel("percent")
    ax.grid(axis="y", alpha=0.25)
    for idx, value in enumerate(values):
        ax.text(idx, value + 2, f"{value:.1f}", ha="center", fontsize=9)
    save(fig, "fig-results.pdf")


def draw_dimensions() -> None:
    dims = read_json(OUT_DIR / "tag-dimensions.json")["views"]
    labels = [row["view"].replace("-", "\n") for row in dims]
    values = [row["compression_ratio"] for row in dims]
    colors = ["#2b6cb0" if row["source"] == "system" else "#805ad5" for row in dims]
    fig, ax = plt.subplots(figsize=(7.1, 2.8))
    ax.bar(labels, values, color=colors)
    ax.set_yscale("log")
    ax.set_ylabel("compression ratio (log)")
    ax.grid(axis="y", alpha=0.25)
    for idx, value in enumerate(values):
        ax.text(idx, value * 1.1, f"{value:.1f}x", ha="center", fontsize=8)
    save(fig, "fig-dimensions.pdf")


class Node:
    def __init__(self, name: str) -> None:
        self.name = name
        self.value = 0
        self.children: dict[str, "Node"] = {}


def build_tree(stacks: Counter[str], limit: int = 80) -> Node:
    root = Node("root")
    for stack, weight in stacks.most_common(limit):
        root.value += weight
        node = root
        for frame in stack.split(";")[:7]:
            node = node.children.setdefault(frame, Node(frame))
            node.value += weight
    return root


def draw_flame_excerpt() -> None:
    root = build_tree(read_folded(OUT_DIR / "semantic-system.folded.txt"))
    fig, ax = plt.subplots(figsize=(7.2, 2.8))
    ax.axis("off")
    colors = ["#68d391", "#63b3ed", "#f6ad55", "#fc8181", "#b794f4", "#4fd1c5", "#f687b3"]

    def draw(node: Node, x: float, y: float, w: float, level: int) -> None:
        cur = x
        for idx, child in enumerate(sorted(node.children.values(), key=lambda c: (-c.value, c.name))):
            cw = w * child.value / node.value if node.value else 0
            if cw < 0.015:
                continue
            ax.add_patch(Rectangle((cur, y), cw, 0.09, facecolor=colors[level % len(colors)], edgecolor="white", linewidth=0.6))
            if cw > 0.09:
                text = child.name if len(child.name) <= 20 else child.name[:19] + "."
                ax.text(cur + 0.004, y + 0.055, text, fontsize=7, va="center")
            draw(child, cur, y - 0.10, cw, level + 1)
            cur += cw

    draw(root, 0.02, 0.88, 0.96, 0)
    ax.text(0.02, 0.04, "excerpt of top 80 semantic system stacks; width = aggregated observations", fontsize=9)
    save(fig, "fig-flame-excerpt.pdf")


def main() -> None:
    draw_model()
    draw_results()
    draw_dimensions()
    draw_flame_excerpt()
    print(json.dumps({"figures": sorted(path.name for path in FIG_DIR.glob("*.pdf"))}, indent=2))


if __name__ == "__main__":
    main()
