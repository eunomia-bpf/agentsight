from __future__ import annotations

import html
import json
from collections import Counter
from pathlib import Path
from typing import Any


class Node:
    def __init__(self, name: str) -> None:
        self.name = name
        self.value = 0
        self.children: dict[str, "Node"] = {}


def read_folded(path: Path) -> Counter[str]:
    stacks: Counter[str] = Counter()
    if not path.exists():
        return stacks
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        stack, _, weight = line.rpartition(" ")
        try:
            stacks[stack] += int(weight)
        except ValueError:
            continue
    return stacks


def build_tree(stacks: Counter[str], limit: int = 2000) -> Node:
    root = Node("root")
    for stack, weight in stacks.most_common(limit):
        root.value += weight
        node = root
        for frame in stack.split(";"):
            node = node.children.setdefault(frame, Node(frame))
            node.value += weight
    return root


def color_for(text: str, depth: int) -> str:
    import hashlib

    digest = hashlib.sha256(text.encode()).digest()
    hue = (digest[0] + depth * 19) % 360
    sat = 48 + digest[1] % 20
    light = 62 + digest[2] % 12
    return f"hsl({hue} {sat}% {light}%)"


def flamegraph_svg(stacks: Counter[str], title: str, metric: str = "events", width: int = 1400) -> str:
    root = build_tree(stacks)
    if not root.value:
        return f"<svg xmlns='http://www.w3.org/2000/svg' width='{width}' height='120'><text x='16' y='40'>No data</text></svg>"
    levels = max((len(stack.split(";")) for stack in stacks), default=1)
    frame_h = 22
    top = 64
    height = top + (levels + 1) * frame_h + 24
    out = [
        f"<svg xmlns='http://www.w3.org/2000/svg' width='{width}' height='{height}' viewBox='0 0 {width} {height}'>",
        "<style>text{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:11px}.title{font-family:system-ui,sans-serif;font-size:18px;font-weight:700}.frame{stroke:#fff;stroke-width:.7}</style>",
        f"<rect width='{width}' height='{height}' fill='#fbfbf7'/>",
        f"<text class='title' x='16' y='28'>{html.escape(title)}</text>",
        f"<text x='16' y='48'>width = {html.escape(metric)}; total = {root.value}</text>",
    ]

    def draw(node: Node, x: float, y: float, w: float, depth: int) -> None:
        cur = x
        for child in sorted(node.children.values(), key=lambda n: (-n.value, n.name)):
            cw = w * child.value / node.value if node.value else 0
            if cw < 0.5:
                continue
            label = child.name
            color = color_for(label, depth)
            out.append(
                f"<rect class='frame' x='{cur:.2f}' y='{y:.2f}' width='{cw:.2f}' height='{frame_h - 1}' fill='{color}'>"
                f"<title>{html.escape(label)} | {child.value} {html.escape(metric)}</title></rect>"
            )
            if cw > 54:
                clipped = label if len(label) < 34 else label[:31] + "..."
                out.append(f"<text x='{cur + 4:.2f}' y='{y + 15:.2f}'>{html.escape(clipped)}</text>")
            draw(child, cur, y + frame_h, cw, depth + 1)
            cur += cw

    draw(root, 16, top, width - 32, 0)
    out.append("</svg>")
    return "\n".join(out)


def bar_svg(rows: list[dict[str, Any]], label_key: str, value_key: str, title: str, width: int = 760, height: int = 300) -> str:
    rows = rows[:12]
    max_value = max((int(row.get(value_key) or 0) for row in rows), default=1)
    bar_h = 18
    gap = 6
    top = 46
    height = max(height, top + len(rows) * (bar_h + gap) + 24)
    out = [
        f"<svg xmlns='http://www.w3.org/2000/svg' width='{width}' height='{height}' viewBox='0 0 {width} {height}'>",
        "<style>text{font-family:system-ui,sans-serif;font-size:12px}.title{font-size:16px;font-weight:700}</style>",
        f"<rect width='{width}' height='{height}' fill='#fbfbf7'/>",
        f"<text class='title' x='16' y='26'>{html.escape(title)}</text>",
    ]
    for idx, row in enumerate(rows):
        value = int(row.get(value_key) or 0)
        label = str(row.get(label_key) or "")
        y = top + idx * (bar_h + gap)
        w = (width - 260) * value / max_value if max_value else 0
        out.append(f"<text x='16' y='{y + 13}'>{html.escape(label[:34])}</text>")
        out.append(f"<rect x='230' y='{y}' width='{w:.1f}' height='{bar_h}' fill='#3b82f6' rx='2'/>")
        out.append(f"<text x='{235 + w:.1f}' y='{y + 13}'>{value}</text>")
    out.append("</svg>")
    return "\n".join(out)


def command_label(row: dict[str, Any]) -> str:
    return f"{row.get('agent')}:{row.get('cmd')}:{row.get('effect')}:{row.get('status')}"


def write_dashboard(out_dir: Path, payload: dict[str, Any]) -> None:
    summary = payload["summary"]
    svgs: dict[str, str] = {}
    folded_specs = [
        ("system-flamegraph.svg", "semantic-system.folded.txt", "System Footprint Flamegraph", "events"),
        ("token-flamegraph.svg", "semantic-token.folded.txt", "Token Footprint Flamegraph", "tokens"),
        ("session-system.svg", "session-system.folded.txt", "Session-System Projection", "events"),
        ("prompt-system.svg", "prompt-system.folded.txt", "Prompt-System Projection", "events"),
        ("session-token.svg", "session-token.folded.txt", "Session-Token Projection", "tokens"),
        ("prompt-token.svg", "prompt-token.folded.txt", "Prompt-Token Projection", "tokens"),
        ("llm-token.svg", "llm-token.folded.txt", "LLM-Token Projection", "tokens"),
    ]
    for svg_name, folded_name, title, metric in folded_specs:
        svg = flamegraph_svg(read_folded(out_dir / folded_name), title, metric)
        (out_dir / svg_name).write_text(svg, encoding="utf-8")
        svgs[svg_name] = svg

    top_tags = summary["top_prompt_tags"]
    tag_svg = bar_svg(top_tags, "tag", "count", "Top Prompt Tags")
    (out_dir / "tag-bars.svg").write_text(tag_svg, encoding="utf-8")
    command_rows = [{"label": command_label(row), "count": row["count"]} for row in summary["command_summary"]]
    cmd_svg = bar_svg(command_rows, "label", "count", "Top Commands And Effects")
    (out_dir / "command-bars.svg").write_text(cmd_svg, encoding="utf-8")
    timeline_svg = bar_svg(summary["timeline"], "date", "sessions", "Session Timeline")
    (out_dir / "timeline.svg").write_text(timeline_svg, encoding="utf-8")

    mixing_rows = []
    for row in summary["semantic_mixing"]["nonsemantic"]["examples"][:10]:
        variants = "; ".join(f"{item['semantic']}={item['weight']}" for item in row["top_semantic_variants"][:4])
        mixing_rows.append(
            f"<tr><td>{html.escape(str(row['weight']))}</td><td>{html.escape(str(row['semantic_variant_count']))}</td>"
            f"<td><code>{html.escape(row['baseline_stack'])}</code></td><td>{html.escape(variants)}</td></tr>"
        )

    html_doc = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>AgentFlame Report</title>
  <style>
    body {{ margin:0; background:#f7f7f2; color:#17202a; font:14px/1.45 system-ui,-apple-system,Segoe UI,sans-serif; }}
    header {{ padding:24px 28px; background:#17202a; color:#fff; }}
    main {{ padding:24px 28px 56px; }}
    h1 {{ margin:0 0 6px; font-size:24px; }}
    h2 {{ margin:26px 0 12px; font-size:18px; }}
    .cards {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(180px,1fr)); gap:12px; }}
    .card {{ background:#fff; border:1px solid #ddd8ca; border-radius:8px; padding:14px; }}
    .k {{ color:#667085; font-size:12px; }}
    .v {{ font-size:24px; font-weight:700; }}
    .panel {{ background:#fff; border:1px solid #ddd8ca; border-radius:8px; padding:12px; margin:12px 0; overflow:auto; }}
    table {{ width:100%; border-collapse:collapse; background:#fff; }}
    th,td {{ border-bottom:1px solid #eee8da; padding:8px; text-align:left; vertical-align:top; }}
    code {{ font-family:ui-monospace,SFMono-Regular,Menlo,monospace; font-size:12px; }}
  </style>
</head>
<body>
  <header>
    <h1>AgentFlame Report</h1>
    <div>Generated {html.escape(payload['generated_at'])}. Tags are LLM-generated one-word local labels. Raw prompt text is redacted unless explicitly enabled.</div>
  </header>
  <main>
    <section class="cards">
      <div class="card"><div class="k">Sessions</div><div class="v">{summary['session_count']}</div></div>
      <div class="card"><div class="k">Tool Events</div><div class="v">{summary['raw_tool_events']}</div></div>
      <div class="card"><div class="k">System Stacks</div><div class="v">{summary['system']['unique_stacks']}</div></div>
      <div class="card"><div class="k">System Compression</div><div class="v">{summary['system']['compression_ratio']}x</div></div>
      <div class="card"><div class="k">Nonsemantic Mixed Weight</div><div class="v">{summary['semantic_mixing']['nonsemantic']['mixed_weight_pct']}%</div></div>
      <div class="card"><div class="k">LLM Calls For Tags</div><div class="v">{payload['llm_tagger']['llm_calls']}</div></div>
    </section>
    <h2>Task Tags And Commands</h2>
    <div class="panel">{tag_svg}</div>
    <div class="panel">{cmd_svg}</div>
    <div class="panel">{timeline_svg}</div>
    <h2>Semantic Flamegraphs</h2>
    <div class="panel">{svgs['system-flamegraph.svg']}</div>
    <div class="panel">{svgs['token-flamegraph.svg']}</div>
    <h2>Dimension Projections</h2>
    <div class="panel">{svgs['session-system.svg']}</div>
    <div class="panel">{svgs['prompt-system.svg']}</div>
    <div class="panel">{svgs['session-token.svg']}</div>
    <div class="panel">{svgs['prompt-token.svg']}</div>
    <div class="panel">{svgs['llm-token.svg']}</div>
    <h2>Baseline Buckets Split By Semantic Tags</h2>
    <div class="panel">
      <table><thead><tr><th>Weight</th><th>Semantic variants</th><th>Baseline stack</th><th>Top separated regions</th></tr></thead><tbody>
      {''.join(mixing_rows)}
      </tbody></table>
    </div>
    <h2>Machine-Readable Output</h2>
    <div class="panel"><code>agentflame.json</code> stores the complete redacted analysis. <code>tags.json</code> stores reusable LLM tag records for AgentSight or future AgentFlame runs.</div>
  </main>
</body>
</html>
"""
    (out_dir / "index.html").write_text(html_doc, encoding="utf-8")
