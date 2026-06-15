#!/usr/bin/env python3
"""Render lightweight progress charts from committed visexp artifacts."""

from __future__ import annotations

import argparse
import csv
import html
import json
from pathlib import Path
from typing import Any


INK = "#1f2933"
MUTED = "#5f6b76"
GRID = "#d9e0d2"
BG = "#fbfcf8"
PANEL = "#ffffff"
BAR_BG = "#eef2e8"
SUPPORTED = "#2f855a"
DIAGNOSTIC = "#2b6cb0"
PARTIAL = "#b7791f"
UNSUPPORTED = "#c53030"


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def bar_width(value: float, maximum: float, full_width: int) -> int:
    if maximum <= 0:
        return 0
    return int(round(clamp(value / maximum, 0.0, 1.0) * full_width))


def verdict_color(verdict: str) -> str:
    return {
        "supported": SUPPORTED,
        "diagnostic": DIAGNOSTIC,
        "partial": PARTIAL,
        "unsupported": UNSUPPORTED,
    }.get(verdict, MUTED)


def verdict_score(verdict: str) -> float:
    return {
        "supported": 1.0,
        "diagnostic": 0.7,
        "partial": 0.5,
        "unsupported": 0.18,
    }.get(verdict, 0.1)


def shorten(text: str, limit: int = 120) -> str:
    if len(text) <= limit:
        return text
    return text[: max(0, limit - 3)].rstrip() + "..."


def label_lines(text: str, limit: int = 34, max_lines: int = 2) -> list[str]:
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if len(candidate) <= limit:
            current = candidate
            continue
        if current:
            lines.append(current)
        current = word[:limit]
        if len(lines) == max_lines - 1:
            break
    if current and len(lines) < max_lines:
        lines.append(current)
    if not lines:
        lines = [text[:limit]]
    return lines[:max_lines]


def text_block(x: int, y: int, lines: list[str], size: int = 13, color: str = INK) -> str:
    parts = [f'<text x="{x}" y="{y}" font-size="{size}" fill="{color}">']
    for idx, line in enumerate(lines):
        dy = 0 if idx == 0 else size + 4
        parts.append(f'<tspan x="{x}" dy="{dy}">{esc(line)}</tspan>')
    parts.append("</text>")
    return "".join(parts)


def svg_page(title: str, subtitle: str, width: int, height: int, body: str) -> str:
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-label="{esc(title)}">
  <rect width="{width}" height="{height}" fill="{BG}"/>
  <rect x="18" y="18" width="{width - 36}" height="{height - 36}" rx="8" fill="{PANEL}" stroke="{GRID}"/>
  <text x="36" y="54" font-size="22" font-weight="700" fill="{INK}">{esc(title)}</text>
  <text x="36" y="78" font-size="13" fill="{MUTED}">{esc(subtitle)}</text>
{body}
</svg>
"""


def bar_row(
    y: int,
    label: str,
    value: float,
    maximum: float,
    full_width: int,
    color: str,
    metric: str,
    note: str = "",
    label_x: int = 42,
    bar_x: int = 330,
) -> str:
    width = bar_width(value, maximum, full_width)
    body = [
        text_block(label_x, y + 17, label_lines(label), 13, INK),
        f'<rect x="{bar_x}" y="{y}" width="{full_width}" height="22" rx="4" fill="{BAR_BG}"/>',
        f'<rect x="{bar_x}" y="{y}" width="{width}" height="22" rx="4" fill="{color}"/>',
        f'<text x="{bar_x + full_width + 18}" y="{y + 16}" font-size="13" fill="{INK}">{esc(metric)}</text>',
    ]
    if note:
        body.append(
            f'<text x="{bar_x}" y="{y + 43}" font-size="12" fill="{MUTED}">{esc(shorten(note, 110))}</text>'
        )
    return "\n".join(body)


def write_claim_gates_svg(out_dir: Path, gates: list[dict[str, str]]) -> Path:
    width = 1120
    row_h = 70
    height = 118 + row_h * len(gates)
    parts = [
        f'<line x1="36" y1="96" x2="{width - 36}" y2="96" stroke="{GRID}"/>',
        f'<text x="330" y="112" font-size="12" fill="{MUTED}">claim-readiness bar</text>',
        f'<text x="720" y="112" font-size="12" fill="{MUTED}">current verdict</text>',
    ]
    for idx, gate in enumerate(gates):
        y = 130 + idx * row_h
        verdict = gate.get("verdict", "unknown")
        parts.append(
            bar_row(
                y,
                gate.get("claim", "unknown"),
                verdict_score(verdict),
                1.0,
                360,
                verdict_color(verdict),
                verdict,
                gate.get("evidence", ""),
            )
        )
        parts.append(f'<line x1="36" y1="{y + 58}" x2="{width - 36}" y2="{y + 58}" stroke="{GRID}"/>')
    path = out_dir / "claim-gates.svg"
    path.write_text(
        svg_page(
            "Claim Gate Progress",
            "Readiness of current artifacts; unsupported means missing required evidence, not a failed result.",
            width,
            height,
            "\n".join(parts),
        ),
        encoding="utf-8",
    )
    return path


def write_semantic_mixing_svg(out_dir: Path, evaluation: dict[str, Any]) -> Path:
    info = evaluation["semantic_information_gain"]
    nonsemantic = info["nonsemantic_stack_mixing"]
    flat = info["flat_effect_mixing"]
    compression = evaluation["aggregation_strength"]["semantic_system"]
    width = 1120
    rows = [
        (
            "Collapsed semantic observations",
            compression["collapsed_observation_share_pct"],
            SUPPORTED,
            f"{compression['collapsed_observations']} collapsed of {compression['total_observations']} observations",
        ),
        (
            "Nonsemantic baseline mixing",
            nonsemantic["mixed_weight_share_pct"],
            DIAGNOSTIC,
            (
                f"{nonsemantic['mixed_bucket_count']} mixed buckets; "
                f"max {nonsemantic['max_semantic_variants_per_bucket']} semantic variants"
            ),
        ),
        (
            "Flat effect baseline mixing",
            flat["mixed_weight_share_pct"],
            PARTIAL,
            (
                f"{flat['mixed_bucket_count']} mixed buckets; "
                f"max {flat['max_semantic_variants_per_bucket']} semantic variants"
            ),
        ),
    ]
    parts = [
        f'<line x1="36" y1="96" x2="{width - 36}" y2="96" stroke="{GRID}"/>',
        f'<text x="330" y="112" font-size="12" fill="{MUTED}">share of observation weight</text>',
    ]
    for idx, (label, value, color, note) in enumerate(rows):
        parts.append(
            bar_row(
                134 + idx * 78,
                label,
                float(value),
                100.0,
                440,
                color,
                f"{value}%",
                note,
            )
        )
    path = out_dir / "semantic-mixing.svg"
    path.write_text(
        svg_page(
            "Semantic Aggregation Value",
            "What semantic tags add beyond ordinary folded stacks and flat process/effect summaries.",
            width,
            390,
            "\n".join(parts),
        ),
        encoding="utf-8",
    )
    return path


def write_effect_lineage_svg(
    out_dir: Path,
    lineage: dict[str, Any],
    live_lineage: dict[str, Any] | None = None,
    native_lineage: dict[str, Any] | None = None,
    db_lineage: dict[str, Any] | None = None,
    capture_time: dict[str, Any] | None = None,
    live_record: dict[str, Any] | None = None,
) -> Path:
    total = int(lineage.get("effect_events") or 0)
    joined = int(lineage.get("joined_effect_events") or 0)
    orphan = int(lineage.get("orphan_effect_events") or 0)
    live_aggregate = (live_lineage or {}).get("aggregate") or {}
    live_total = int(live_aggregate.get("in_scope_effect_events") or 0)
    live_joined = int(live_aggregate.get("joined_effect_events") or 0)
    live_note = "R110 harness smoke missing"
    live_color = UNSUPPORTED
    if live_total:
        live_note = (
            f"{live_aggregate.get('raw_coverage_pct', 0)}% raw coverage; "
            f"{live_aggregate.get('join_rate_pct', 0)}% in-scope joined; "
            "session/tool envelope is harness-synthesized"
        )
        live_color = PARTIAL
    native_aggregate = (native_lineage or {}).get("aggregate") or {}
    native_total = int(native_aggregate.get("raw_effect_events") or 0)
    native_joined = int(native_aggregate.get("joined_effect_events") or 0)
    native_orphan = int(native_aggregate.get("orphan_effect_events") or 0)
    native_note = "native export missing"
    native_color = UNSUPPORTED
    if native_total:
        native_note = (
            f"{native_aggregate.get('raw_join_pct', 0)}% raw joined; "
            f"{native_orphan} orphan effects; "
            f"sessions={native_aggregate.get('sessions')}, "
            f"tool_calls={native_aggregate.get('tool_calls')}"
        )
        native_color = PARTIAL if native_orphan else SUPPORTED
    db_aggregate = (db_lineage or {}).get("aggregate") or {}
    db_total = int(db_aggregate.get("raw_effect_events") or 0)
    db_joined = int(db_aggregate.get("joined_effect_events") or 0)
    db_orphan = int(db_aggregate.get("orphan_effect_events") or 0)
    db_note = "DB-persisted backfill missing"
    db_color = UNSUPPORTED
    if db_total:
        db_note = (
            f"{db_aggregate.get('raw_join_pct', 0)}% raw joined; "
            f"{db_orphan} orphans; "
            f"db_sessions={db_aggregate.get('db_session_rows')}, "
            f"db_tools={db_aggregate.get('db_tool_rows')}"
        )
        db_color = PARTIAL if db_orphan else SUPPORTED
    capture_ready = 1 if capture_time else 0
    capture_note = "capture-time record-command smoke missing"
    capture_color = UNSUPPORTED
    if capture_time:
        capture_note = (
            f"{capture_time.get('status', 'unknown')}; "
            f"sessions={capture_time.get('sessions')}, "
            f"tools={capture_time.get('tool_calls')}; "
            f"live_rerun={capture_time.get('live_rerun', 'pending')}"
        )
        capture_color = PARTIAL
    record_aggregate = (live_record or {}).get("aggregate") or {}
    record_total = int(record_aggregate.get("effect_events") or 0)
    record_joined = int(record_aggregate.get("joined_effect_events") or 0)
    record_orphan = int(record_aggregate.get("orphan_effect_events") or 0)
    record_note = "R113 live Codex record missing"
    record_color = UNSUPPORTED
    if record_total:
        record_note = (
            f"{record_aggregate.get('raw_join_pct', 0)}% raw joined; "
            f"{record_orphan} orphans; "
            f"tasks={record_aggregate.get('tasks')}, "
            f"record_tools={record_aggregate.get('record_envelope_tool_calls')}"
        )
        record_color = PARTIAL if record_orphan else SUPPORTED
    rows = [
        (
            "Fixture effects joined",
            joined,
            total,
            SUPPORTED,
            f"{lineage.get('join_rate_pct', 0)}% joined; source={lineage.get('source', 'unknown')}",
        ),
        (
            "Fixture orphan effects",
            orphan,
            max(total, 1),
            UNSUPPORTED if orphan else SUPPORTED,
            f"orphan reasons: {lineage.get('orphan_reasons', {})}",
        ),
        (
            "R110 live in-scope",
            live_joined,
            max(live_total, 1),
            live_color,
            live_note,
        ),
        (
            "R111 native raw effects",
            native_joined,
            max(native_total, 1),
            native_color,
            native_note,
        ),
        (
            "R112 DB persisted raw effects",
            db_joined,
            max(db_total, 1),
            db_color,
            db_note,
        ),
        (
            "R113 capture-time rows",
            capture_ready,
            1,
            capture_color,
            capture_note,
        ),
        (
            "R113 live Codex raw effects",
            record_joined,
            max(record_total, 1),
            record_color,
            record_note,
        ),
    ]
    parts = [
        f'<line x1="36" y1="96" x2="1084" y2="96" stroke="{GRID}"/>',
        f'<text x="330" y="112" font-size="12" fill="{MUTED}">count or readiness</text>',
    ]
    for idx, (label, value, maximum, color, note) in enumerate(rows):
        if label == "R110 live in-scope" and not live_total:
            metric = "missing"
        elif label == "R111 native raw effects" and not native_total:
            metric = "missing"
        elif label == "R112 DB persisted raw effects" and not db_total:
            metric = "missing"
        elif label == "R113 capture-time rows" and not capture_time:
            metric = "missing"
        elif label == "R113 live Codex raw effects" and not record_total:
            metric = "missing"
        else:
            metric = f"{value}/{maximum}"
        parts.append(
            bar_row(
                134 + idx * 78,
                label,
                float(value),
                float(maximum),
                440,
                color,
                metric,
                note,
            )
        )
    path = out_dir / "effect-lineage.svg"
    path.write_text(
        svg_page(
            "Exact Effect Lineage",
            "Fixture checker plus R110/R111/R112 raw-effect smokes, R113 capture-time rows, and R113 live Codex records; C4 remains partial.",
            1120,
            702,
            "\n".join(parts),
        ),
        encoding="utf-8",
    )
    return path


def write_visual_summary_html(out_dir: Path) -> Path:
    cards = [
        ("Claim Gate Progress", "claim-gates.svg"),
        ("Semantic Aggregation Value", "semantic-mixing.svg"),
        ("Exact Effect Lineage", "effect-lineage.svg"),
        ("System Footprint Flamegraph", "system-flamegraph.svg"),
        ("Session System Footprint", "session-system.svg"),
        ("Prompt System Footprint", "prompt-system.svg"),
        ("Token Footprint Flamegraph", "token-flamegraph.svg"),
        ("Session Token Footprint", "session-token.svg"),
        ("Prompt Token Footprint", "prompt-token.svg"),
        ("LLM-Call Token Footprint", "llm-token.svg"),
    ]
    figures = "\n".join(
        f"""
    <section>
      <h2>{esc(title)}</h2>
      <div class="figure"><img src="{esc(filename)}" alt="{esc(title)}"></div>
    </section>"""
        for title, filename in cards
    )
    html_text = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>AgentSight Visual Progress Summary</title>
  <style>
    :root {{
      --bg: #fbfcf8;
      --ink: #1f2933;
      --muted: #5f6b76;
      --line: #d9e0d2;
      --panel: #ffffff;
    }}
    body {{
      margin: 0;
      background: var(--bg);
      color: var(--ink);
      font-family: ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      line-height: 1.45;
    }}
    main {{ max-width: 1200px; margin: 0 auto; padding: 24px; }}
    h1 {{ font-size: 24px; margin: 0 0 8px; letter-spacing: 0; }}
    h2 {{ font-size: 16px; margin: 24px 0 10px; letter-spacing: 0; }}
    p {{ color: var(--muted); margin: 0 0 14px; max-width: 980px; }}
    .figure {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 10px;
      overflow-x: auto;
    }}
    img {{ display: block; max-width: none; }}
    a {{ color: #0f766e; }}
  </style>
</head>
<body>
<main>
  <h1>AgentSight Visual Progress Summary</h1>
  <p>These charts summarize current artifact state. They do not replace the full semantic flamegraph report or the planned live-capture and user-study runs.</p>
  <p>Full report: <a href="index.html">index.html</a>. Artifact audit: <a href="evaluation-summary.md">evaluation-summary.md</a>.</p>
{figures}
</main>
</body>
</html>
"""
    path = out_dir / "visual-summary.html"
    path.write_text(html_text, encoding="utf-8")
    return path


def run(out_dir: Path) -> list[Path]:
    evaluation = read_json(out_dir / "evaluation.json")
    gates = read_csv_rows(out_dir / "claim-gates.csv")
    lineage = read_json(out_dir / "effect-lineage-smoke.json")
    live_path = out_dir / "live-lineage-r110.json"
    live_lineage = read_json(live_path) if live_path.exists() else None
    native_path = out_dir / "native-lineage-r111.json"
    native_lineage = read_json(native_path) if native_path.exists() else None
    db_path = out_dir / "native-lineage-r112.json"
    db_lineage = read_json(db_path) if db_path.exists() else None
    capture_path = out_dir / "capture-time-r113.json"
    capture_time = read_json(capture_path) if capture_path.exists() else None
    live_record_path = out_dir / "live-record-r113.json"
    live_record = read_json(live_record_path) if live_record_path.exists() else None
    return [
        write_claim_gates_svg(out_dir, gates),
        write_semantic_mixing_svg(out_dir, evaluation),
        write_effect_lineage_svg(
            out_dir,
            lineage,
            live_lineage,
            native_lineage,
            db_lineage,
            capture_time,
            live_record,
        ),
        write_visual_summary_html(out_dir),
    ]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default=str(Path(__file__).resolve().parent / "out"))
    return parser


if __name__ == "__main__":
    args = build_parser().parse_args()
    paths = run(Path(args.out))
    print(json.dumps({"written": [str(path) for path in paths]}, indent=2))
