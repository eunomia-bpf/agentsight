from __future__ import annotations

import hashlib
import html
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

from .pprof import SemanticSample


@dataclass
class FlameNode:
    name: str
    value: int = 0
    children: dict[str, "FlameNode"] = field(default_factory=dict)


def _add_sample(root: FlameNode, stack: tuple[str, ...], value: int) -> None:
    root.value += value
    node = root
    for frame in stack:
        child = node.children.get(frame)
        if child is None:
            child = FlameNode(frame)
            node.children[frame] = child
        child.value += value
        node = child


def _depth(node: FlameNode) -> int:
    if not node.children:
        return 0
    return 1 + max(_depth(child) for child in node.children.values())


def _color(name: str) -> str:
    digest = hashlib.sha1(name.encode("utf-8", errors="ignore")).digest()
    hue = int.from_bytes(digest[:2], "big") % 360
    sat = 46 + digest[2] % 22
    light = 58 + digest[3] % 14
    return f"hsl({hue} {sat}% {light}%)"


def _label(text: str, width: float) -> str:
    max_chars = int((width - 8) / 7)
    if max_chars < 4:
        return ""
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 1] + "."


def _iter_children(node: FlameNode) -> list[FlameNode]:
    return sorted(node.children.values(), key=lambda child: (-child.value, child.name))


def _render_node(
    out: list[str],
    node: FlameNode,
    x: float,
    depth: int,
    max_depth: int,
    total: int,
    plot_width: int,
    frame_height: int,
    top: int,
    min_width: float,
    path: tuple[str, ...],
) -> None:
    width = node.value / total * plot_width if total else 0
    if width < min_width:
        return
    y = top + (max_depth - depth) * frame_height
    escaped_name = html.escape(node.name)
    escaped_label = html.escape(_label(node.name, width))
    pct = node.value / total * 100 if total else 0
    title = html.escape(f"{';'.join(path + (node.name,))}\n{node.value} ({pct:.2f}%)")
    out.append(
        f'<g class="frame"><title>{title}</title>'
        f'<rect x="{x:.3f}" y="{y}" width="{width:.3f}" height="{frame_height - 1}" '
        f'rx="2" ry="2" fill="{_color(node.name)}"/>'
        f'<text x="{x + 4:.3f}" y="{y + frame_height - 5}">{escaped_label}</text></g>'
    )
    child_x = x
    for child in _iter_children(node):
        child_width = child.value / total * plot_width if total else 0
        _render_node(
            out,
            child,
            child_x,
            depth + 1,
            max_depth,
            total,
            plot_width,
            frame_height,
            top,
            min_width,
            path + (node.name,),
        )
        child_x += child_width
    _ = escaped_name


def build_tree(samples: list[SemanticSample]) -> FlameNode:
    collapsed: defaultdict[tuple[str, ...], int] = defaultdict(int)
    for sample in samples:
        if sample.value > 0 and sample.stack:
            collapsed[sample.stack] += sample.value
    root = FlameNode("root")
    for stack, value in collapsed.items():
        _add_sample(root, stack, value)
    return root


def write_flamegraph_svg(
    path: Path,
    samples: list[SemanticSample],
    title: str,
    unit: str,
    width: int = 1600,
    frame_height: int = 18,
    min_width: float = 0.5,
) -> None:
    root = build_tree(samples)
    plot_width = width - 32
    max_depth = max(1, _depth(root))
    top = 52
    height = top + (max_depth + 1) * frame_height + 36
    out = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}">',
        "<style>",
        "text{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;font-size:11px;fill:#111}",
        ".title{font-size:18px;font-weight:700}",
        ".meta{font-size:12px;fill:#444}",
        ".frame rect{stroke:#fff;stroke-width:.5}",
        ".frame:hover rect{stroke:#000;stroke-width:1}",
        "</style>",
        f'<text class="title" x="16" y="24">{html.escape(title)}</text>',
        f'<text class="meta" x="16" y="42">total={root.value} {html.escape(unit)}; '
        "width is cumulative sample value; hover rectangles for full stack</text>",
    ]
    child_x = 16.0
    total = max(root.value, 1)
    for child in _iter_children(root):
        child_width = child.value / total * plot_width
        _render_node(
            out,
            child,
            child_x,
            1,
            max_depth,
            total,
            plot_width,
            frame_height,
            top,
            min_width,
            (),
        )
        child_x += child_width
    out.append("</svg>")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(out) + "\n", encoding="utf-8")
