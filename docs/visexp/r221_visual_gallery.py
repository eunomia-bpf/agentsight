#!/usr/bin/env python3
"""R221: render an AgentFlame visual gallery from existing artifacts.

This script is intentionally a presentation artifact. It reads the committed
R170/R180/R211/R212/R213/R214/R219 outputs and writes static SVG figures plus
one self-contained HTML flamegraph. It does not read raw Codex/Claude session
histories, call an LLM, or mutate the display map.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import html
import json
import math
import statistics
import subprocess
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[1]
DEFAULT_OUT_DIR = SCRIPT_DIR / "figures" / "agentflame-gallery-r221"
DEFAULT_VIS_OUT = SCRIPT_DIR / "out"

INK = "#17212b"
MUTED = "#5c6670"
SUBTLE = "#eef1ed"
GRID = "#d8dfd3"
BG = "#fbfcf8"
PANEL = "#ffffff"
RED = "#c2413b"
ORANGE = "#c46d2d"
YELLOW = "#b88b1f"
GREEN = "#2f7d55"
BLUE = "#2f6f9f"
CYAN = "#2b7f8f"
PURPLE = "#6f5aa7"
PINK = "#aa4b76"

FRAME_COLORS = {
    "project": "#5c6670",
    "agent": "#3b6f91",
    "session": "#2f7d55",
    "prompt": "#b7791f",
    "call": "#6f5aa7",
    "process": "#2b7f8f",
    "effect": "#c46d2d",
    "path": "#7d6b42",
    "status": "#6b7280",
}


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT.resolve()))
    except Exception:
        return str(path)


def git(args: list[str]) -> str | None:
    try:
        return subprocess.check_output(
            ["git", *args],
            cwd=REPO_ROOT,
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except Exception:
        return None


def now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def as_int(value: Any) -> int:
    if value in (None, ""):
        return 0
    return int(float(str(value)))


def as_float(value: Any) -> float:
    if value in (None, ""):
        return 0.0
    return float(str(value))


def pct(part: float, whole: float) -> float:
    return round(100.0 * part / whole, 3) if whole else 0.0


def clean_label(text: str, limit: int = 80) -> str:
    text = " ".join(str(text or "").split())
    if len(text) <= limit:
        return text
    return text[: max(0, limit - 3)].rstrip() + "..."


def wrap_label(text: str, width: int = 26, max_lines: int = 2) -> list[str]:
    words = str(text or "").replace("_", " ").split()
    if not words:
        return [""]
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if len(candidate) <= width:
            current = candidate
            continue
        if current:
            lines.append(current)
        current = word[:width]
        if len(lines) >= max_lines - 1:
            break
    if current and len(lines) < max_lines:
        lines.append(current)
    return lines[:max_lines]


def font_fit(text: str, pixel_width: float, char_px: float = 7.2) -> str:
    if pixel_width <= 16:
        return ""
    limit = max(1, int(pixel_width / char_px))
    text = str(text)
    if len(text) <= limit:
        return text
    if limit <= 3:
        return ""
    return text[: limit - 3] + "..."


def svg_shell(title: str, subtitle: str, width: int, height: int, body: str) -> str:
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-label="{esc(title)}">
  <rect width="{width}" height="{height}" fill="{BG}"/>
  <rect x="18" y="18" width="{width - 36}" height="{height - 36}" rx="8" fill="{PANEL}" stroke="{GRID}"/>
  <text x="38" y="54" font-family="Inter, Arial, sans-serif" font-size="24" font-weight="700" fill="{INK}">{esc(title)}</text>
  <text x="38" y="80" font-family="Inter, Arial, sans-serif" font-size="13" fill="{MUTED}">{esc(subtitle)}</text>
{body}
</svg>
"""


def text_lines(x: float, y: float, lines: list[str], size: int = 12, color: str = INK, weight: str = "400") -> str:
    spans = [f'<text x="{x:.1f}" y="{y:.1f}" font-family="Inter, Arial, sans-serif" font-size="{size}" font-weight="{weight}" fill="{color}">']
    for idx, line in enumerate(lines):
        dy = 0 if idx == 0 else size + 4
        spans.append(f'<tspan x="{x:.1f}" dy="{dy}">{esc(line)}</tspan>')
    spans.append("</text>")
    return "".join(spans)


def frame_kind(frame: str) -> str:
    return frame.split(":", 1)[0] if ":" in frame else "value"


def frame_value(frame: str) -> str:
    return frame.split(":", 1)[1] if ":" in frame else frame


def frame_color(frame: str) -> str:
    kind = frame_kind(frame)
    if kind in FRAME_COLORS:
        return FRAME_COLORS[kind]
    digest = sum(ord(ch) for ch in frame)
    palette = [GREEN, BLUE, ORANGE, PURPLE, CYAN, PINK, YELLOW]
    return palette[digest % len(palette)]


@dataclass
class TreeNode:
    name: str
    value: int = 0
    children: dict[str, "TreeNode"] = field(default_factory=dict)

    def add(self, frames: list[str], weight: int) -> None:
        self.value += weight
        node = self
        for frame in frames:
            child = node.children.setdefault(frame, TreeNode(frame))
            child.value += weight
            node = child


def stack_frames(stack: str) -> list[str]:
    return [part for part in str(stack or "").split(";") if part]


def build_tree(stack_rows: list[dict[str, str]], limit: int = 200) -> TreeNode:
    root = TreeNode("root")
    rows = sorted(stack_rows, key=lambda row: as_int(row.get("weight")), reverse=True)[:limit]
    for row in rows:
        root.add(stack_frames(row.get("stack", "")), as_int(row.get("weight")))
    return root


def tree_depth(node: TreeNode) -> int:
    if not node.children:
        return 0
    return 1 + max(tree_depth(child) for child in node.children.values())


def flame_rects(
    node: TreeNode,
    x: float,
    y: float,
    width: float,
    row_h: float,
    depth: int,
    max_depth: int,
    min_width: float = 1.5,
) -> list[dict[str, Any]]:
    if depth >= max_depth or not node.children or node.value <= 0:
        return []
    rects: list[dict[str, Any]] = []
    cursor = x
    children = sorted(node.children.values(), key=lambda item: (-item.value, item.name))
    for child in children:
        child_w = width * child.value / node.value
        if child_w < min_width:
            cursor += child_w
            continue
        rects.append(
            {
                "name": child.name,
                "value": child.value,
                "depth": depth,
                "x": cursor,
                "y": y + depth * row_h,
                "width": max(0.0, child_w - 0.8),
                "height": row_h - 2,
                "color": frame_color(child.name),
            }
        )
        rects.extend(
            flame_rects(
                child,
                cursor,
                y,
                child_w,
                row_h,
                depth + 1,
                max_depth,
                min_width,
            )
        )
        cursor += child_w
    return rects


def write_flamegraph_svg(out_dir: Path, top_stacks: list[dict[str, str]]) -> tuple[Path, list[dict[str, Any]]]:
    root = build_tree(top_stacks, 200)
    width = 1320
    left = 38
    top = 112
    graph_w = width - 76
    row_h = 27
    max_depth = min(9, tree_depth(root))
    height = int(top + row_h * max_depth + 54)
    rects = flame_rects(root, left, top, graph_w, row_h, 0, max_depth)
    body: list[str] = [
        f'<text x="{left}" y="102" font-family="Inter, Arial, sans-serif" font-size="12" fill="{MUTED}">width = system-effect weight over R170 top-200 semantic stacks; rectangles are collapsed stack prefixes</text>'
    ]
    for rect in rects:
        label = font_fit(frame_value(rect["name"]), rect["width"])
        body.append(
            f'<g><title>{esc(rect["name"])} | weight={rect["value"]}</title>'
            f'<rect x="{rect["x"]:.2f}" y="{rect["y"]:.2f}" width="{rect["width"]:.2f}" height="{rect["height"]:.2f}" rx="3" fill="{rect["color"]}" opacity="0.88"/>'
            f'<text x="{rect["x"] + 5:.2f}" y="{rect["y"] + 18:.2f}" font-family="Inter, Arial, sans-serif" font-size="11" fill="white">{esc(label)}</text></g>'
        )
    path = out_dir / "01-semantic-flamegraph-top200.svg"
    path.write_text(
        svg_shell(
            "Semantic Flamegraph",
            f"Collapsed stack prefixes from R170 top-200 stacks; top-200 weight={root.value}.",
            width,
            height,
            "\n".join(body),
        ),
        encoding="utf-8",
    )
    return path, rects


def write_flamegraph_html(out_dir: Path, rects: list[dict[str, Any]], total_weight: int) -> Path:
    rect_json = json.dumps(rects, ensure_ascii=False)
    path = out_dir / "02-semantic-flamegraph-top200.html"
    path.write_text(
        f"""<!doctype html>
<html lang="en">
<meta charset="utf-8">
<title>AgentFlame R221 semantic flamegraph</title>
<style>
body {{ margin: 0; font-family: Inter, Arial, sans-serif; background: {BG}; color: {INK}; }}
main {{ padding: 24px; }}
.panel {{ background: white; border: 1px solid {GRID}; border-radius: 8px; padding: 18px; }}
h1 {{ margin: 0 0 6px; font-size: 24px; }}
p {{ margin: 0 0 14px; color: {MUTED}; }}
input {{ width: 320px; padding: 8px 10px; border: 1px solid {GRID}; border-radius: 6px; }}
svg {{ width: 100%; height: auto; border: 1px solid {SUBTLE}; background: #fff; }}
.frame {{ cursor: pointer; }}
.frame:hover rect {{ stroke: #111827; stroke-width: 1.5; opacity: 1; }}
#detail {{ margin-left: 12px; color: {INK}; font-size: 13px; }}
</style>
<main>
  <section class="panel">
    <h1>Semantic Flamegraph</h1>
    <p>R170 top-200 semantic stacks. Width is system-effect weight; search highlights matching frame labels. Total rendered weight: {total_weight}.</p>
    <input id="search" placeholder="search frame, e.g. prompt:review or process:git">
    <span id="detail">Hover or click a frame.</span>
    <svg id="fg" viewBox="0 0 1320 360" role="img" aria-label="semantic flamegraph"></svg>
  </section>
</main>
<script>
const rects = {rect_json};
const svg = document.getElementById('fg');
const detail = document.getElementById('detail');
const ns = 'http://www.w3.org/2000/svg';
for (const r of rects) {{
  const g = document.createElementNS(ns, 'g');
  g.classList.add('frame');
  g.dataset.name = r.name;
  const title = document.createElementNS(ns, 'title');
  title.textContent = `${{r.name}} | weight=${{r.value}}`;
  const rect = document.createElementNS(ns, 'rect');
  rect.setAttribute('x', r.x);
  rect.setAttribute('y', r.y);
  rect.setAttribute('width', r.width);
  rect.setAttribute('height', r.height);
  rect.setAttribute('rx', 3);
  rect.setAttribute('fill', r.color);
  rect.setAttribute('opacity', '0.88');
  const text = document.createElementNS(ns, 'text');
  text.setAttribute('x', r.x + 5);
  text.setAttribute('y', r.y + 18);
  text.setAttribute('font-size', 11);
  text.setAttribute('fill', 'white');
  text.textContent = r.width > 42 ? r.name.split(':').slice(1).join(':').slice(0, Math.max(0, Math.floor(r.width / 7))) : '';
  g.append(title, rect, text);
  g.addEventListener('mouseenter', () => detail.textContent = `${{r.name}} | weight=${{r.value}} | depth=${{r.depth}}`);
  g.addEventListener('click', () => detail.textContent = `${{r.name}} | weight=${{r.value}} | share=${{(100*r.value/{max(total_weight, 1)}).toFixed(3)}}%`);
  svg.append(g);
}}
document.getElementById('search').addEventListener('input', (event) => {{
  const q = event.target.value.toLowerCase();
  for (const g of svg.querySelectorAll('.frame')) {{
    const hit = q && g.dataset.name.toLowerCase().includes(q);
    g.querySelector('rect').setAttribute('opacity', !q || hit ? '0.95' : '0.18');
  }}
}});
</script>
</html>
""",
        encoding="utf-8",
    )
    return path


def treemap_rects(node: TreeNode, x: float, y: float, w: float, h: float, depth: int, max_depth: int) -> list[dict[str, Any]]:
    if depth >= max_depth or not node.children or node.value <= 0:
        return []
    rects: list[dict[str, Any]] = []
    children = sorted(node.children.values(), key=lambda item: (-item.value, item.name))[:18]
    total = sum(child.value for child in children)
    cursor = x
    vertical = w < h
    for child in children:
        share = child.value / total if total else 0
        if vertical:
            child_h = h * share
            rect = {"name": child.name, "value": child.value, "x": x, "y": cursor, "width": w, "height": child_h}
            cursor += child_h
        else:
            child_w = w * share
            rect = {"name": child.name, "value": child.value, "x": cursor, "y": y, "width": child_w, "height": h}
            cursor += child_w
        rect["depth"] = depth
        rect["color"] = frame_color(child.name)
        rects.append(rect)
        pad = 5
        if rect["width"] > 70 and rect["height"] > 40:
            rects.extend(
                treemap_rects(
                    child,
                    rect["x"] + pad,
                    rect["y"] + 24,
                    rect["width"] - 2 * pad,
                    rect["height"] - 29,
                    depth + 1,
                    max_depth,
                )
            )
    return rects


def write_treemap_svg(out_dir: Path, top_stacks: list[dict[str, str]]) -> Path:
    root = build_tree(top_stacks, 200)
    width, height = 1320, 760
    x, y, w, h = 38, 110, 1244, 600
    rects = treemap_rects(root, x, y, w, h, 0, 4)
    body: list[str] = []
    for rect in rects:
        opacity = max(0.35, 0.9 - rect["depth"] * 0.12)
        label = font_fit(frame_value(rect["name"]), rect["width"], 7.0)
        body.append(
            f'<g><title>{esc(rect["name"])} | weight={rect["value"]}</title>'
            f'<rect x="{rect["x"]:.2f}" y="{rect["y"]:.2f}" width="{max(0, rect["width"] - 1):.2f}" height="{max(0, rect["height"] - 1):.2f}" rx="3" fill="{rect["color"]}" opacity="{opacity:.2f}" stroke="white"/>'
            f'<text x="{rect["x"] + 5:.2f}" y="{rect["y"] + 16:.2f}" font-family="Inter, Arial, sans-serif" font-size="11" fill="white">{esc(label)}</text></g>'
        )
    path = out_dir / "03-semantic-treemap-top200.svg"
    path.write_text(
        svg_shell(
            "Semantic Stack Treemap",
            "Slice-and-dice view of the same R170 top-200 collapsed stack tree; good for seeing dominant session/prompt/process regions.",
            width,
            height,
            "\n".join(body),
        ),
        encoding="utf-8",
    )
    return path


def parse_counter(text: str) -> Counter[str]:
    counter: Counter[str] = Counter()
    for part in str(text or "").split(";"):
        part = part.strip()
        if not part or "=" not in part:
            continue
        key, value = part.rsplit("=", 1)
        counter[key.strip()] += as_int(value)
    return counter


def write_heatmap_svg(out_dir: Path, process_rows: list[dict[str, str]]) -> Path:
    top_rows = sorted(process_rows, key=lambda row: as_int(row.get("total_weight")), reverse=True)[:12]
    prompt_counter: Counter[str] = Counter()
    parsed: list[tuple[str, Counter[str], int]] = []
    for row in top_rows:
        splits = parse_counter(row.get("top_prompt_splits", ""))
        prompt_counter.update(splits)
        parsed.append((row.get("process", ""), splits, as_int(row.get("total_weight"))))
    prompts = [name for name, _ in prompt_counter.most_common(10)]
    max_value = max((splits.get(prompt, 0) for _, splits, _ in parsed for prompt in prompts), default=1)
    width, height = 1180, 620
    left, top = 170, 125
    cell_w, cell_h = 82, 32
    body: list[str] = []
    for idx, prompt in enumerate(prompts):
        body.append(
            f'<text x="{left + idx * cell_w + 38}" y="{top - 12}" font-family="Inter, Arial, sans-serif" font-size="11" fill="{MUTED}" text-anchor="middle" transform="rotate(-35 {left + idx * cell_w + 38},{top - 12})">{esc(prompt)}</text>'
        )
    for r_idx, (process, splits, total) in enumerate(parsed):
        y = top + r_idx * cell_h
        body.append(
            f'<text x="{left - 12}" y="{y + 21}" font-family="Inter, Arial, sans-serif" font-size="12" fill="{INK}" text-anchor="end">{esc(process)}</text>'
        )
        for c_idx, prompt in enumerate(prompts):
            value = splits.get(prompt, 0)
            intensity = math.sqrt(value / max_value) if max_value else 0
            fill = f"rgba(47, 111, 159, {0.08 + 0.82 * intensity:.3f})"
            x = left + c_idx * cell_w
            body.append(
                f'<g><title>{esc(process)} -> {esc(prompt)}: {value} / {total}</title>'
                f'<rect x="{x}" y="{y}" width="{cell_w - 3}" height="{cell_h - 3}" rx="3" fill="{fill}" stroke="{PANEL}"/>'
                f'<text x="{x + cell_w / 2:.1f}" y="{y + 20}" font-family="Inter, Arial, sans-serif" font-size="10" fill="{INK}" text-anchor="middle">{value if value else ""}</text></g>'
            )
    body.append(f'<text x="{left}" y="{height - 52}" font-family="Inter, Arial, sans-serif" font-size="12" fill="{MUTED}">Darker cells mean more system-effect weight for process x prompt. This is where normal process-only summaries collapse distinct user intent.</text>')
    path = out_dir / "04-process-prompt-heatmap.svg"
    path.write_text(
        svg_shell(
            "Process x Prompt Heatmap",
            "R211 process split matrix: the same process names carry many prompt tags.",
            width,
            height,
            "\n".join(body),
        ),
        encoding="utf-8",
    )
    return path


def bar_row(
    label: str,
    value: float,
    max_value: float,
    x: float,
    y: float,
    bar_w: float,
    color: str,
    metric: str,
    note: str = "",
    label_w: int = 32,
) -> str:
    w = 0 if max_value <= 0 else bar_w * value / max_value
    parts = [
        text_lines(x, y + 15, wrap_label(label, label_w, 2), 12),
        f'<rect x="{x + 220}" y="{y}" width="{bar_w}" height="22" rx="4" fill="{SUBTLE}"/>',
        f'<rect x="{x + 220}" y="{y}" width="{w:.2f}" height="22" rx="4" fill="{color}"/>',
        f'<text x="{x + 220 + bar_w + 14}" y="{y + 16}" font-family="Inter, Arial, sans-serif" font-size="12" fill="{INK}">{esc(metric)}</text>',
    ]
    if note:
        parts.append(f'<text x="{x + 220}" y="{y + 40}" font-family="Inter, Arial, sans-serif" font-size="11" fill="{MUTED}">{esc(clean_label(note, 110))}</text>')
    return "\n".join(parts)


def write_baseline_collapse_svg(out_dir: Path, rows: list[dict[str, str]]) -> Path:
    top = sorted(rows, key=lambda row: as_float(row.get("ambiguous_share_pct")), reverse=True)[:12]
    max_weight = max((as_int(row.get("total_weight")) for row in top), default=1)
    width, height = 1220, 950
    body: list[str] = [
        f'<text x="38" y="104" font-family="Inter, Arial, sans-serif" font-size="12" fill="{MUTED}">bar length = bucket weight; red segment = weight not explained by the top prompt tag</text>'
    ]
    for idx, row in enumerate(top):
        y = 128 + idx * 64
        total = as_int(row.get("total_weight"))
        ambiguous = as_int(row.get("ambiguous_weight"))
        total_w = 560 * total / max_weight
        amb_w = 560 * ambiguous / max_weight
        label = row.get("system_key", "")
        body.append(text_lines(42, y + 15, wrap_label(label, 36, 2), 12))
        body.append(f'<rect x="330" y="{y}" width="560" height="22" rx="4" fill="{SUBTLE}"/>')
        body.append(f'<rect x="330" y="{y}" width="{total_w:.2f}" height="22" rx="4" fill="{BLUE}" opacity="0.85"/>')
        body.append(f'<rect x="330" y="{y}" width="{amb_w:.2f}" height="22" rx="4" fill="{RED}" opacity="0.85"/>')
        body.append(
            f'<text x="908" y="{y + 16}" font-family="Inter, Arial, sans-serif" font-size="12" fill="{INK}">{ambiguous}/{total} ambiguous, {row.get("distinct_prompt_tags")} prompt tags</text>'
        )
        body.append(f'<text x="330" y="{y + 42}" font-family="Inter, Arial, sans-serif" font-size="11" fill="{MUTED}">{esc(clean_label(row.get("top_prompt_splits", ""), 116))}</text>')
    path = out_dir / "05-baseline-collapse-ambiguity.svg"
    path.write_text(
        svg_shell(
            "Why Process-Only Flamegraphs Collapse Intent",
            "R211 examples where one process/effect bucket mixes many prompt tags.",
            width,
            height,
            "\n".join(body),
        ),
        encoding="utf-8",
    )
    return path


def write_tag_multiples_svg(out_dir: Path, tag_rows: list[dict[str, str]]) -> Path:
    dims = [
        ("session_tag_by_sessions", "Session tags / sessions", GREEN),
        ("session_tag_by_system_effect_weight", "Session tags / effects", BLUE),
        ("prompt_tag_by_prompt_rows", "Prompt tags / prompts", ORANGE),
        ("prompt_tag_by_system_effect_weight", "Prompt tags / effects", PURPLE),
        ("llm_tag_by_llm_events", "LLM-call tags / calls", CYAN),
        ("llm_tag_by_estimated_tokens", "LLM-call tags / tokens", PINK),
    ]
    width, height = 1320, 930
    panel_w, panel_h = 400, 245
    body: list[str] = []
    by_dim: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in tag_rows:
        by_dim[row.get("dimension", "")].append(row)
    for idx, (dim, title, color) in enumerate(dims):
        col = idx % 3
        row_idx = idx // 3
        x = 42 + col * 420
        y = 116 + row_idx * 335
        rows = sorted(by_dim.get(dim, []), key=lambda item: as_int(item.get("rank")))[:8]
        max_count = max((as_float(item.get("count")) for item in rows), default=1)
        body.append(f'<rect x="{x}" y="{y - 26}" width="{panel_w}" height="{panel_h}" rx="7" fill="#fff" stroke="{GRID}"/>')
        body.append(f'<text x="{x + 14}" y="{y - 6}" font-family="Inter, Arial, sans-serif" font-size="14" font-weight="700" fill="{INK}">{esc(title)}</text>')
        for r_idx, item in enumerate(rows):
            yy = y + 14 + r_idx * 25
            value = as_float(item.get("count"))
            bar_w = 205 * value / max_count if max_count else 0
            body.append(f'<text x="{x + 14}" y="{yy + 13}" font-family="Inter, Arial, sans-serif" font-size="11" fill="{INK}">{esc(clean_label(item.get("tag", ""), 18))}</text>')
            body.append(f'<rect x="{x + 120}" y="{yy}" width="205" height="16" rx="3" fill="{SUBTLE}"/>')
            body.append(f'<rect x="{x + 120}" y="{yy}" width="{bar_w:.2f}" height="16" rx="3" fill="{color}" opacity="0.85"/>')
            body.append(f'<text x="{x + 334}" y="{yy + 12}" font-family="Inter, Arial, sans-serif" font-size="10" fill="{MUTED}">{item.get("share_pct")}%</text>')
    path = out_dir / "06-tag-distribution-small-multiples.svg"
    path.write_text(
        svg_shell(
            "One-Word Tag Distributions",
            "R211 top tags by session count, prompt rows, LLM events, tokens, and system-effect weight.",
            width,
            height,
            "\n".join(body),
        ),
        encoding="utf-8",
    )
    return path


def write_zipf_svg(out_dir: Path, tag_rows: list[dict[str, str]]) -> Path:
    dims = [
        ("session_tag_by_system_effect_weight", "session/effects", GREEN),
        ("prompt_tag_by_system_effect_weight", "prompt/effects", ORANGE),
        ("llm_tag_by_llm_events", "llm/calls", CYAN),
    ]
    by_dim: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in tag_rows:
        by_dim[row.get("dimension", "")].append(row)
    width, height = 1120, 620
    x0, y0, w, h = 86, 112, 940, 410
    body = [
        f'<line x1="{x0}" y1="{y0 + h}" x2="{x0 + w}" y2="{y0 + h}" stroke="{GRID}"/>',
        f'<line x1="{x0}" y1="{y0}" x2="{x0}" y2="{y0 + h}" stroke="{GRID}"/>',
        f'<text x="{x0}" y="{y0 + h + 42}" font-family="Inter, Arial, sans-serif" font-size="12" fill="{MUTED}">rank, log scale</text>',
        f'<text x="34" y="{y0 + 10}" font-family="Inter, Arial, sans-serif" font-size="12" fill="{MUTED}" transform="rotate(-90 34,{y0 + 10})">count/weight, log scale</text>',
    ]
    for d_idx, (dim, label, color) in enumerate(dims):
        rows = sorted(by_dim.get(dim, []), key=lambda item: as_int(item.get("rank")))[:160]
        values = [max(1.0, as_float(row.get("count"))) for row in rows]
        if not values:
            continue
        max_rank = max(2, len(values))
        max_v, min_v = max(values), min(values)
        max_log, min_log = math.log10(max_v), math.log10(min_v)
        points = []
        for idx, value in enumerate(values, start=1):
            rank_pos = math.log10(idx) / math.log10(max_rank)
            val_pos = 0.0 if max_log == min_log else (math.log10(value) - min_log) / (max_log - min_log)
            x = x0 + rank_pos * w
            y = y0 + h - val_pos * h
            points.append(f"{x:.1f},{y:.1f}")
        body.append(f'<polyline points="{" ".join(points)}" fill="none" stroke="{color}" stroke-width="2.4"/>')
        body.append(f'<rect x="{x0 + 700}" y="{y0 + 20 + d_idx * 24}" width="14" height="14" fill="{color}"/>')
        body.append(f'<text x="{x0 + 722}" y="{y0 + 32 + d_idx * 24}" font-family="Inter, Arial, sans-serif" font-size="12" fill="{INK}">{esc(label)}</text>')
    path = out_dir / "07-tag-long-tail-zipf.svg"
    path.write_text(
        svg_shell(
            "Tag Long Tail",
            "Log-log rank curves from R170/R211 tag counts; long tails motivate reversible display control instead of hidden other buckets.",
            width,
            height,
            "\n".join(body),
        ),
        encoding="utf-8",
    )
    return path


def write_rollup_svg(out_dir: Path, rows: list[dict[str, str]]) -> Path:
    total = sum(as_int(row.get("support")) for row in rows)
    width, height = 1280, 610
    x, y, w = 62, 124, 1120
    colors = [GREEN, BLUE, CYAN, ORANGE, YELLOW, PINK, PURPLE]
    cursor = x
    body: list[str] = [
        f'<text x="{x}" y="104" font-family="Inter, Arial, sans-serif" font-size="12" fill="{MUTED}">stacked bar width = support; active_display_allowed is shown in green labels, pending in orange/red labels</text>'
    ]
    for idx, row in enumerate(rows):
        support = as_int(row.get("support"))
        seg_w = w * support / total if total else 0
        color = colors[idx % len(colors)]
        body.append(
            f'<g><title>{esc(row.get("rollup_bucket"))}: support={support}, rows={row.get("rows")}, allowed={row.get("active_display_allowed")}</title>'
            f'<rect x="{cursor:.2f}" y="{y}" width="{seg_w:.2f}" height="48" fill="{color}" opacity="0.9"/></g>'
        )
        if seg_w > 58:
            body.append(f'<text x="{cursor + 6:.2f}" y="{y + 30}" font-family="Inter, Arial, sans-serif" font-size="11" fill="white">{esc(font_fit(row.get("rollup_bucket", ""), seg_w, 6.4))}</text>')
        cursor += seg_w
    for idx, row in enumerate(rows):
        yy = 205 + idx * 46
        allowed = str(row.get("active_display_allowed")) == "True"
        color = GREEN if allowed else (ORANGE if "profile" in row.get("rollup_bucket", "") else RED)
        body.append(
            bar_row(
                row.get("rollup_bucket", ""),
                as_int(row.get("support")),
                max(as_int(item.get("support")) for item in rows),
                42,
                yy,
                420,
                color,
                f'{row.get("support_pct")}% support, {row.get("rows")} rows',
                row.get("required_gate", ""),
            )
        )
    path = out_dir / "08-long-tail-rollup.svg"
    path.write_text(
        svg_shell(
            "Long-Tail Governance Rollup",
            "R214 seven-bucket partition over all 1,811 raw-tag rows and 482,398 support.",
            width,
            height,
            "\n".join(body),
        ),
        encoding="utf-8",
    )
    return path


def write_trigger_gates_svg(out_dir: Path, rows: list[dict[str, str]]) -> Path:
    width, height = 1180, 590
    body: list[str] = []
    for idx, row in enumerate(rows):
        y = 122 + idx * 70
        passed = str(row.get("passed")).lower() == "true"
        color = GREEN if passed else RED
        actual = as_float(row.get("actual"))
        threshold = as_float(row.get("threshold"))
        scale = max(actual, threshold, 1.0)
        body.append(text_lines(42, y + 15, wrap_label(row.get("trigger", ""), 34, 2), 12))
        body.append(f'<rect x="330" y="{y}" width="430" height="22" rx="4" fill="{SUBTLE}"/>')
        body.append(f'<rect x="330" y="{y}" width="{430 * actual / scale:.2f}" height="22" rx="4" fill="{color}" opacity="0.85"/>')
        body.append(f'<line x1="{330 + 430 * threshold / scale:.2f}" y1="{y - 4}" x2="{330 + 430 * threshold / scale:.2f}" y2="{y + 28}" stroke="{INK}" stroke-dasharray="3 3"/>')
        gate_text = (
            f'actual {row.get("actual")} {row.get("comparator")} '
            f'{row.get("threshold")} -> {"pass" if passed else "fail"}'
        )
        body.append(f'<text x="780" y="{y + 16}" font-family="Inter, Arial, sans-serif" font-size="12" fill="{INK}">{esc(gate_text)}</text>')
        body.append(f'<text x="330" y="{y + 42}" font-family="Inter, Arial, sans-serif" font-size="11" fill="{MUTED}">{esc(clean_label(row.get("response", ""), 110))}</text>')
    path = out_dir / "09-long-tail-control-gates.svg"
    path.write_text(
        svg_shell(
            "Long-Tail Control Gates",
            "R214 automatic policy checks. Failed gates mean review is required before aggressive compaction.",
            width,
            height,
            "\n".join(body),
        ),
        encoding="utf-8",
    )
    return path


def write_review_queue_svg(out_dir: Path, rows: list[dict[str, str]]) -> Path:
    top = rows[:18]
    max_support = max((as_int(row.get("support")) for row in top), default=1)
    width, height = 1230, 940
    body: list[str] = []
    for idx, row in enumerate(top):
        y = 118 + idx * 43
        source = row.get("candidate_source", "")
        color = BLUE if "profile" in source else PURPLE
        label = f"{row.get('dimension')}:{row.get('raw_tag')} -> {row.get('candidate_display_tag')}"
        body.append(
            bar_row(
                label,
                as_int(row.get("support")),
                max_support,
                42,
                y,
                430,
                color,
                f"support {row.get('support')}",
                f"{row.get('candidate_source')} | {row.get('review_reason')}",
                label_w=34,
            )
        )
    path = out_dir / "10-review-priority-lane.svg"
    path.write_text(
        svg_shell(
            "Review Priority Lane",
            "Top R214 pending candidates by support; these are not active default merges.",
            width,
            height,
            "\n".join(body),
        ),
        encoding="utf-8",
    )
    return path


def write_display_modes_svg(out_dir: Path, rows: list[dict[str, str]]) -> Path:
    max_bucket = max((as_int(row.get("bucket_count")) for row in rows), default=1)
    width, height = 1120, 470
    body: list[str] = []
    for idx, row in enumerate(rows):
        y = 132 + idx * 95
        color = [BLUE, GREEN, ORANGE][idx % 3]
        body.append(
            bar_row(
                row.get("mode", ""),
                as_int(row.get("bucket_count")),
                max_bucket,
                48,
                y,
                430,
                color,
                f'{row.get("bucket_count")} buckets, support {row.get("total_support")}',
                (
                    f'active merges={row.get("active_merge_rows")}, '
                    f'candidate overlays={row.get("candidate_overlay_rows")}, '
                    f'review rows={row.get("review_required_rows")}, hidden-other={row.get("hidden_other_rows")}'
                ),
            )
        )
    path = out_dir / "11-display-mode-comparison.svg"
    path.write_text(
        svg_shell(
            "Display Modes Preserve Membership",
            "R213 raw/display/pending modes keep support constant while surfacing active aliases and pending review overlays.",
            width,
            height,
            "\n".join(body),
        ),
        encoding="utf-8",
    )
    return path


def write_compaction_ablation_svg(out_dir: Path, rows: list[dict[str, str]]) -> Path:
    max_count = max((as_int(row.get("stack_count")) for row in rows), default=1)
    width, height = 650, 520
    body: list[str] = []
    for idx, row in enumerate(rows):
        y = 122 + idx * 82
        unsafe = as_float(row.get("unreviewed_profile_merge_weight_pct"))
        color = RED if unsafe > 0 else GREEN
        body.append(
            bar_row(
                row.get("variant", ""),
                as_int(row.get("stack_count")),
                max_count,
                42,
                y,
                250,
                color,
                f'{row.get("stack_count")} stacks',
                f'reduction={row.get("stack_reduction_vs_raw_pct")}%, unreviewed active weight={row.get("unreviewed_profile_merge_weight_pct")}%',
                label_w=24,
            )
        )
    path = out_dir / "12-display-compaction-ablation.svg"
    path.write_text(
        svg_shell(
            "Display Compaction Ablation",
            "R212 shows why profile-guarded candidate merges stay pending despite reducing stack count more.",
            width,
            height,
            "\n".join(body),
        ),
        encoding="utf-8",
    )
    return path


def verdict_color(verdict: str) -> str:
    if verdict.startswith("supported"):
        return GREEN
    if "partial" in verdict:
        return ORANGE
    if verdict == "unsupported":
        return RED
    return BLUE


def verdict_score(verdict: str) -> float:
    if verdict == "supported":
        return 1.0
    if verdict.startswith("supported_for") or verdict.startswith("supported_as"):
        return 0.72
    if "partial" in verdict:
        return 0.48
    if verdict == "unsupported":
        return 0.14
    return 0.35


def write_claim_readiness_svg(out_dir: Path, rows: list[dict[str, str]]) -> Path:
    width, height = 1260, 710
    body: list[str] = []
    for idx, row in enumerate(rows):
        y = 118 + idx * 78
        verdict = row.get("verdict", "")
        body.append(
            bar_row(
                row.get("claim", ""),
                verdict_score(verdict),
                1.0,
                42,
                y,
                360,
                verdict_color(verdict),
                verdict,
                row.get("blocking_gap", ""),
                label_w=42,
            )
        )
    path = out_dir / "13-claim-readiness.svg"
    path.write_text(
        svg_shell(
            "Claim Readiness",
            "R219 status: mechanism claims have artifacts; developer utility and human adequacy remain blocked by missing returns.",
            width,
            height,
            "\n".join(body),
        ),
        encoding="utf-8",
    )
    return path


def write_lineage_svg(out_dir: Path, r114: dict[str, Any], r182: dict[str, Any]) -> Path:
    agg114 = r114.get("aggregate", {})
    agg182 = r182.get("aggregate", {})
    rows = [
        ("R114 precision", as_float(agg114.get("precision_pct")), 100.0, GREEN, f'{agg114.get("true_positives")} TP, {agg114.get("false_positives")} FP'),
        ("R114 recall", as_float(agg114.get("recall_pct")), 100.0, GREEN, f'{agg114.get("true_positives")} TP, {agg114.get("false_negatives")} FN'),
        ("R114 negative joined", as_int(agg114.get("negative_joined_effect_events")), max(1, as_int(agg114.get("negative_effect_events_observed"))), GREEN, f'{agg114.get("negative_joined_effect_events")}/{agg114.get("negative_effect_events_observed")}'),
        ("R182 joined network", as_int(agg182.get("joined_network_effect_events")), max(1, as_int(agg182.get("network_effect_events"))), ORANGE, f'{agg182.get("joined_network_effect_events")}/{agg182.get("network_effect_events")} network events'),
        ("R182 target-specific network", as_int(agg182.get("target_specific_network_effect_events")), max(1, as_int(agg182.get("network_effect_events"))), RED, f'{agg182.get("target_specific_network_effect_events")}/{agg182.get("network_effect_events")} target-specific'),
    ]
    width, height = 1120, 560
    body: list[str] = []
    for idx, (label, value, max_value, color, note) in enumerate(rows):
        y = 126 + idx * 74
        metric = f"{value:g}%" if "precision" in label or "recall" in label else str(value)
        body.append(bar_row(label, value, max_value, 46, y, 430, color, metric, note))
    path = out_dir / "14-lineage-evidence.svg"
    path.write_text(
        svg_shell(
            "Exact Lineage Evidence",
            "R114 command-mode exact lineage is strong; R182 network capture remains partial and motivates R191.",
            width,
            height,
            "\n".join(body),
        ),
        encoding="utf-8",
    )
    return path


def percentile(values: list[float], q: float) -> float:
    if not values:
        return 0.0
    if len(values) == 1:
        return values[0]
    ordered = sorted(values)
    index = (len(ordered) - 1) * q
    low = math.floor(index)
    high = math.ceil(index)
    if low == high:
        return ordered[low]
    return ordered[low] * (high - index) + ordered[high] * (index - low)


def write_model_benchmark_svg(out_dir: Path, r180: dict[str, Any]) -> Path:
    models = r180.get("bench", {}).get("models", [])
    rows: list[dict[str, Any]] = []
    for model in models:
        latency = [as_float(value) for value in model.get("latency_ms", []) if as_float(value) > 0]
        stability = model.get("stability", {})
        rows.append(
            {
                "label": model.get("label"),
                "p50": round(statistics.median(latency), 1) if latency else 0,
                "p95": round(percentile(latency, 0.95), 1) if latency else 0,
                "valid_pct": pct(as_int(model.get("valid_tags")), as_int(model.get("total_runs"))),
                "stable_pct": as_float(stability.get("exact_stability_pct")),
            }
        )
    width, height = 1060, 570
    max_p95 = max((row["p95"] for row in rows), default=1)
    body: list[str] = []
    for idx, row in enumerate(rows):
        y = 124 + idx * 112
        body.append(f'<text x="54" y="{y + 18}" font-family="Inter, Arial, sans-serif" font-size="16" font-weight="700" fill="{INK}">{esc(row["label"])}</text>')
        body.append(bar_row("p95 latency", row["p95"], max_p95, 150, y, 300, BLUE, f'{row["p95"]} ms'))
        body.append(bar_row("exact stability", row["stable_pct"], 100.0, 150, y + 38, 300, GREEN if row["stable_pct"] >= 95 else ORANGE, f'{row["stable_pct"]}%'))
        body.append(bar_row("valid outputs", row["valid_pct"], 100.0, 150, y + 76, 300, GREEN, f'{row["valid_pct"]}%'))
    path = out_dir / "15-small-model-benchmark.svg"
    path.write_text(
        svg_shell(
            "Small-Model Tagging Cost",
            "R180 local llama.cpp benchmark over 300 redacted fragments x 3 repeats per model.",
            width,
            height,
            "\n".join(body),
        ),
        encoding="utf-8",
    )
    return path


def write_system_model_svg(out_dir: Path) -> Path:
    width, height = 1220, 680
    stages = [
        ("Session", "one-word tag", 70, 125, GREEN),
        ("Prompt", "one-word tag", 260, 125, ORANGE),
        ("LLM call", "one-word tag", 450, 125, CYAN),
        ("Tool / shell", "call boundary", 640, 125, PURPLE),
        ("Process tree", "pid ancestry", 830, 125, BLUE),
        ("Effect", "file/network/process", 1020, 125, RED),
    ]
    body: list[str] = []
    for idx, (title, subtitle, x, y, color) in enumerate(stages):
        body.append(f'<rect x="{x}" y="{y}" width="140" height="74" rx="7" fill="{color}" opacity="0.9"/>')
        body.append(f'<text x="{x + 70}" y="{y + 32}" font-family="Inter, Arial, sans-serif" font-size="15" font-weight="700" fill="white" text-anchor="middle">{esc(title)}</text>')
        body.append(f'<text x="{x + 70}" y="{y + 54}" font-family="Inter, Arial, sans-serif" font-size="11" fill="white" text-anchor="middle">{esc(subtitle)}</text>')
        if idx < len(stages) - 1:
            nx = stages[idx + 1][2]
            body.append(f'<line x1="{x + 140}" y1="{y + 37}" x2="{nx}" y2="{y + 37}" stroke="{INK}" stroke-width="2" marker-end="url(#arrow)"/>')
    body.append(
        """<defs><marker id="arrow" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 z" fill="#17212b"/></marker></defs>"""
    )
    lanes = [
        ("Collapsed semantic stack", "sessionTag;promptTag;llmcall/tool;process*;effect", 130, 275, 960, GREEN),
        ("Default display", "active deterministic aliases only; raw drilldown required", 130, 372, 960, BLUE),
        ("Pending overlay", "profile merges, LLM regeneration, contextual split stay review-gated", 130, 469, 960, ORANGE),
    ]
    for title, subtitle, x, y, w, color in lanes:
        body.append(f'<rect x="{x}" y="{y}" width="{w}" height="58" rx="7" fill="{color}" opacity="0.12" stroke="{color}"/>')
        body.append(f'<text x="{x + 18}" y="{y + 25}" font-family="Inter, Arial, sans-serif" font-size="15" font-weight="700" fill="{INK}">{esc(title)}</text>')
        body.append(f'<text x="{x + 18}" y="{y + 45}" font-family="Inter, Arial, sans-serif" font-size="12" fill="{MUTED}">{esc(subtitle)}</text>')
    path = out_dir / "16-agentflame-system-model.svg"
    path.write_text(
        svg_shell(
            "AgentFlame Analysis Model",
            "The semantic layer names intent once; the system layer keeps exact process/effect lineage.",
            width,
            height,
            "\n".join(body),
        ),
        encoding="utf-8",
    )
    return path


def write_index(out_dir: Path, figure_rows: list[dict[str, Any]]) -> Path:
    lines = [
        "# AgentFlame Visual Gallery R221",
        "",
        f"Generated: `{now_iso()}`",
        "",
        "This gallery is generated from existing visexp artifacts. It does not read raw agent traces, call an LLM, or update the display map.",
        "",
        "## Figures",
        "",
    ]
    for row in figure_rows:
        lines.append(f"### {row['title']}")
        lines.append("")
        lines.append(f"- File: [`{row['file']}`]({row['file']})")
        lines.append(f"- Source: {row['source']}")
        lines.append(f"- What it shows: {row['meaning']}")
        if str(row["file"]).endswith(".svg"):
            lines.append("")
            lines.append(f"![{row['title']}]({row['file']})")
        lines.append("")
    path = out_dir / "README.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def render_gallery(vis_out: Path, out_dir: Path) -> dict[str, Any]:
    out_dir.mkdir(parents=True, exist_ok=True)

    top_stacks = read_csv(vis_out / "tag-stats-r189" / "top-semantic-stacks-r170.csv")
    r211_tags = read_csv(vis_out / "stack-examples-r211" / "tag-distribution-r211.csv")
    process_splits = read_csv(vis_out / "stack-examples-r211" / "process-splits-r211.csv")
    baseline_collapse = read_csv(vis_out / "stack-examples-r211" / "baseline-collapse-examples-r211.csv")
    rollup = read_csv(vis_out / "long-tail-control-r214" / "rollup-preview-r214.csv")
    triggers = read_csv(vis_out / "long-tail-control-r214" / "trigger-gates-r214.csv")
    review_priority = read_csv(vis_out / "long-tail-control-r214" / "review-priority-r214.csv")
    display_modes = read_csv(vis_out / "display-mode-drilldown-r213" / "mode-summary-r213.csv")
    compaction = read_csv(vis_out / "display-compaction-ablation-r212" / "variant-summary-r212.csv")
    claim_rows = read_csv(vis_out / "claim-readiness-r219" / "claim-readiness-r219.csv")
    r114 = read_json(vis_out / "live-record-r114-analysis.json")
    r182 = read_json(vis_out / "live-network-r182.json")
    r180 = read_json(vis_out / "model-benchmarks-r180.json")

    figures: list[dict[str, Any]] = []

    flame_svg, rects = write_flamegraph_svg(out_dir, top_stacks)
    figures.append(
        {
            "title": "01 Semantic Flamegraph",
            "file": flame_svg.name,
            "source": "R170 top-semantic-stacks-r170.csv",
            "meaning": "A true collapsed stack view: width is system-effect weight, not just duration spans.",
        }
    )
    flame_html = write_flamegraph_html(out_dir, rects, sum(as_int(row.get("weight")) for row in top_stacks[:200]))
    figures.append(
        {
            "title": "02 Interactive Semantic Flamegraph",
            "file": flame_html.name,
            "source": "R170 top-semantic-stacks-r170.csv",
            "meaning": "Same flamegraph with search, hover, and click details.",
        }
    )
    generated = [
        (
            write_treemap_svg(out_dir, top_stacks),
            "03 Semantic Stack Treemap",
            "R170 top-semantic-stacks-r170.csv",
            "Dominant session/prompt/process regions in the collapsed stack tree.",
        ),
        (
            write_heatmap_svg(out_dir, process_splits),
            "04 Process x Prompt Heatmap",
            "R211 process-splits-r211.csv",
            "Why process-only views hide intent: same process names spread across many prompt tags.",
        ),
        (
            write_baseline_collapse_svg(out_dir, baseline_collapse),
            "05 Baseline Collapse Ambiguity",
            "R211 baseline-collapse-examples-r211.csv",
            "Concrete buckets where ordinary process/effect grouping mixes many semantic tasks.",
        ),
        (
            write_tag_multiples_svg(out_dir, r211_tags),
            "06 Tag Distribution Small Multiples",
            "R211 tag-distribution-r211.csv",
            "Head tags and skew across session, prompt, and LLM-call dimensions.",
        ),
        (
            write_zipf_svg(out_dir, r211_tags),
            "07 Tag Long-Tail Zipf",
            "R211 tag-distribution-r211.csv",
            "Log-log long-tail curves that motivate reversible compaction.",
        ),
        (
            write_rollup_svg(out_dir, rollup),
            "08 Long-Tail Rollup",
            "R214 rollup-preview-r214.csv",
            "Seven governance buckets partition all raw-tag rows and support.",
        ),
        (
            write_trigger_gates_svg(out_dir, triggers),
            "09 Long-Tail Control Gates",
            "R214 trigger-gates-r214.csv",
            "Which compaction thresholds pass and which force review.",
        ),
        (
            write_review_queue_svg(out_dir, review_priority),
            "10 Review Priority Lane",
            "R214 review-priority-r214.csv",
            "Highest-support pending candidate merges/regenerations.",
        ),
        (
            write_display_modes_svg(out_dir, display_modes),
            "11 Display Mode Comparison",
            "R213 mode-summary-r213.csv",
            "Raw/display/pending mode membership preservation and overlay load.",
        ),
        (
            write_compaction_ablation_svg(out_dir, compaction),
            "12 Display Compaction Ablation",
            "R212 variant-summary-r212.csv",
            "Why unreviewed profile-guarded merges remain inactive.",
        ),
        (
            write_claim_readiness_svg(out_dir, claim_rows),
            "13 Claim Readiness",
            "R219 claim-readiness-r219.csv",
            "Current research evidence level and remaining human-evidence blockers.",
        ),
        (
            write_lineage_svg(out_dir, r114, r182),
            "14 Lineage Evidence",
            "R114 live-record analysis and R182 network record suite",
            "Exact lineage strength plus the remaining target-network gap.",
        ),
        (
            write_model_benchmark_svg(out_dir, r180),
            "15 Small-Model Benchmark",
            "R180 model-benchmarks-r180.json",
            "Local 0.6B/1.1B/3B one-word tag latency, validity, and stability.",
        ),
        (
            write_system_model_svg(out_dir),
            "16 AgentFlame System Model",
            "Design summary from current artifacts",
            "The intended stack schema and display-control model.",
        ),
    ]
    for path, title, source, meaning in generated:
        figures.append({"title": title, "file": path.name, "source": source, "meaning": meaning})

    index = write_index(out_dir, figures)
    manifest = {
        "schema_version": 1,
        "run_id": "R221",
        "generated_at": now_iso(),
        "out_dir": rel(out_dir),
        "figures": figures,
        "index": rel(index),
        "source_artifacts": {
            "r170_top_stacks": rel(vis_out / "tag-stats-r189" / "top-semantic-stacks-r170.csv"),
            "r211_tags": rel(vis_out / "stack-examples-r211" / "tag-distribution-r211.csv"),
            "r214_rollup": rel(vis_out / "long-tail-control-r214" / "rollup-preview-r214.csv"),
            "r219_claims": rel(vis_out / "claim-readiness-r219" / "claim-readiness-r219.csv"),
        },
        "git": {
            "commit": git(["rev-parse", "HEAD"]),
            "status_short": git(["status", "--short"]),
        },
        "claim_boundary": (
            "R221 is a visualization packaging run over existing artifacts. It does not add "
            "human adequacy labels, developer-utility outcomes, target-specific network lineage, "
            "or new semantic-quality evidence."
        ),
    }
    write_json(out_dir / "manifest-r221.json", manifest)
    write_csv(out_dir / "figure-index-r221.csv", figures, ["title", "file", "source", "meaning"])
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--vis-out", type=Path, default=DEFAULT_VIS_OUT)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT_DIR)
    args = parser.parse_args()
    manifest = render_gallery(args.vis_out, args.out)
    print(json.dumps({"status": "ok", "out_dir": manifest["out_dir"], "figures": len(manifest["figures"])}, indent=2))


if __name__ == "__main__":
    main()
