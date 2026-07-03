#!/usr/bin/env python3
"""Analyze folded operation stacks beyond flamegraphs."""

from __future__ import annotations

import argparse
import html
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--folded", type=Path, required=True)
    parser.add_argument("--json-out", type=Path, required=True)
    parser.add_argument("--html-out", type=Path)
    parser.add_argument("--top", type=int, default=30)
    args = parser.parse_args()

    stacks = read_folded(args.folded)
    analysis = analyze(stacks, args.top)
    write_json(args.json_out, analysis)
    if args.html_out:
        write_html(args.html_out, analysis)
    print(json.dumps(summary_line(analysis), indent=2, sort_keys=True))
    return 0


def read_folded(path: Path) -> list[tuple[list[str], int]]:
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        stack, weight_text = line.rsplit(" ", 1)
        rows.append((stack.split(";"), int(weight_text)))
    return rows


def analyze(stacks: list[tuple[list[str], int]], top: int) -> dict[str, Any]:
    total = sum(weight for _, weight in stacks)
    by_depth: Counter[str] = Counter()
    by_kind: dict[str, Counter[str]] = defaultdict(Counter)
    transitions: Counter[tuple[str, str]] = Counter()
    leaves: Counter[str] = Counter()
    tree: dict[str, Any] = {"name": "root", "value": total, "children": {}}

    for frames, weight in stacks:
        leaves[frames[-1] if frames else "empty"] += weight
        for depth, frame in enumerate(frames):
            kind, value = split_frame(frame)
            by_depth[str(depth)] += weight
            by_kind[kind][value] += weight
            add_tree_path(tree, frames[: depth + 1], weight)
            if depth:
                transitions[(frames[depth - 1], frame)] += weight

    return {
        "total_weight": total,
        "unique_stacks": len(stacks),
        "compression_ratio": round(total / len(stacks), 3) if stacks else 0,
        "depth_weight": dict(sorted(by_depth.items(), key=lambda item: int(item[0]))),
        "top_by_kind": {
            kind: top_counter(counter, top) for kind, counter in sorted(by_kind.items())
        },
        "top_transitions": [
            {"from": left, "to": right, "weight": weight}
            for (left, right), weight in transitions.most_common(top)
        ],
        "top_leaves": top_counter(leaves, top),
        "tree": compact_tree(tree),
    }


def split_frame(frame: str) -> tuple[str, str]:
    if ":" not in frame:
        return "frame", frame
    kind, value = frame.split(":", 1)
    return kind, value


def add_tree_path(root: dict[str, Any], frames: list[str], weight: int) -> None:
    node = root
    for frame in frames:
        children = node.setdefault("children", {})
        node = children.setdefault(frame, {"name": frame, "value": 0, "children": {}})
        node["value"] += weight


def compact_tree(node: dict[str, Any]) -> dict[str, Any]:
    children = node.get("children", {})
    return {
        "name": node["name"],
        "value": node["value"],
        "children": [
            compact_tree(child)
            for child in sorted(children.values(), key=lambda item: (-item["value"], item["name"]))
        ],
    }


def top_counter(counter: Counter[str], limit: int) -> list[dict[str, Any]]:
    return [
        {"name": name, "weight": weight}
        for name, weight in counter.most_common(limit)
    ]


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_html(path: Path, analysis: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    html_text = f"""<!doctype html>
<html>
<head>
<meta charset="utf-8">
<title>Operation Stack Analysis</title>
<style>
body{{font-family:system-ui,-apple-system,Segoe UI,sans-serif;margin:24px;background:#fafafa;color:#171717}}
h1{{font-size:22px;margin:0 0 8px}}
h2{{font-size:16px;margin:28px 0 10px}}
.meta{{color:#555;margin-bottom:18px}}
.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:16px}}
.panel{{background:white;border:1px solid #ddd;border-radius:6px;padding:14px}}
.bar{{height:18px;background:#e8eef9;border-radius:3px;margin:6px 0;position:relative;overflow:hidden}}
.fill{{height:100%;background:#4f7cac}}
.label{{font:12px ui-monospace,Menlo,monospace;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}}
table{{border-collapse:collapse;width:100%;font-size:13px}}
td,th{{border-bottom:1px solid #eee;padding:6px;text-align:left;vertical-align:top}}
.tree{{font:12px ui-monospace,Menlo,monospace;line-height:1.45;max-height:520px;overflow:auto;background:white;border:1px solid #ddd;border-radius:6px;padding:12px}}
</style>
</head>
<body>
<h1>Operation Stack Analysis</h1>
<div class="meta">total={analysis['total_weight']} operations; unique stacks={analysis['unique_stacks']}; compression={analysis['compression_ratio']}</div>
<div class="grid">
{kind_panels(analysis)}
</div>
<h2>Top Transitions</h2>
{transition_table(analysis)}
<h2>Stack Tree</h2>
<div class="tree">{tree_html(analysis['tree'])}</div>
</body>
</html>
"""
    path.write_text(html_text, encoding="utf-8")


def kind_panels(analysis: dict[str, Any]) -> str:
    panels = []
    for kind in ["dataset", "task", "phase", "action", "status"]:
        rows = analysis["top_by_kind"].get(kind, [])
        if not rows:
            continue
        panels.append(f"<div class='panel'><h2>{html.escape(kind)}</h2>{bars(rows)}</div>")
    return "\n".join(panels)


def bars(rows: list[dict[str, Any]]) -> str:
    max_weight = max((row["weight"] for row in rows), default=1)
    out = []
    for row in rows[:15]:
        pct = row["weight"] / max_weight * 100
        name = html.escape(str(row["name"]))
        out.append(
            f"<div class='label'>{name} {row['weight']}</div>"
            f"<div class='bar'><div class='fill' style='width:{pct:.1f}%'></div></div>"
        )
    return "\n".join(out)


def transition_table(analysis: dict[str, Any]) -> str:
    rows = ["<table><tr><th>From</th><th>To</th><th>Weight</th></tr>"]
    for edge in analysis["top_transitions"][:30]:
        rows.append(
            "<tr>"
            f"<td>{html.escape(edge['from'])}</td>"
            f"<td>{html.escape(edge['to'])}</td>"
            f"<td>{edge['weight']}</td>"
            "</tr>"
        )
    rows.append("</table>")
    return "\n".join(rows)


def tree_html(node: dict[str, Any], depth: int = 0) -> str:
    label = f"{'&nbsp;' * depth * 2}{html.escape(node['name'])} ({node['value']})<br>"
    children = "".join(tree_html(child, depth + 1) for child in node.get("children", [])[:80])
    return label + children


def summary_line(analysis: dict[str, Any]) -> dict[str, Any]:
    return {
        "total_weight": analysis["total_weight"],
        "unique_stacks": analysis["unique_stacks"],
        "compression_ratio": analysis["compression_ratio"],
        "top_datasets": analysis["top_by_kind"].get("dataset", [])[:5],
        "top_phases": analysis["top_by_kind"].get("phase", [])[:8],
    }


if __name__ == "__main__":
    raise SystemExit(main())
