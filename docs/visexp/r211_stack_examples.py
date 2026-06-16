#!/usr/bin/env python3
"""R211: derive reviewer-facing tag distributions and stack examples.

This run reads generated AgentFlame/R189 artifacts only. It does not read raw
Codex/Claude traces, and it does not call an LLM. The upstream R170 run is the
real full-history llama.cpp annotation evidence; R211 packages its outputs into
small tables and figures for the paper.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import html
import json
import math
import subprocess
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[1]
DEFAULT_R170 = SCRIPT_DIR / "out" / "full-history-r170.json"
DEFAULT_TAG_STATS = SCRIPT_DIR / "out" / "tag-stats-r189"
DEFAULT_OUT = SCRIPT_DIR / "out" / "stack-examples-r211"

TAG_DIMENSIONS = [
    "session_tag_by_sessions",
    "session_tag_by_system_effect_weight",
    "prompt_tag_by_prompt_rows",
    "prompt_tag_by_system_effect_weight",
    "llm_tag_by_llm_events",
    "llm_tag_by_estimated_tokens",
]

TAG_DISTRIBUTION_FIELDS = [
    "dimension",
    "rank",
    "tag",
    "count",
    "share_pct",
    "unit",
    "coverage_top_5_pct",
    "unique_tags_in_dimension",
]

PROCESS_SPLIT_FIELDS = [
    "rank",
    "process",
    "total_weight",
    "top_prompt",
    "top_prompt_weight",
    "top_prompt_share_pct",
    "distinct_prompt_tags",
    "ambiguous_weight",
    "ambiguous_share_pct",
    "top_prompt_splits",
]

BASELINE_COLLAPSE_FIELDS = [
    "rank",
    "system_key",
    "total_weight",
    "distinct_prompt_tags",
    "top_prompt",
    "top_prompt_weight",
    "top_prompt_share_pct",
    "ambiguous_weight",
    "ambiguous_share_pct",
    "top_prompt_splits",
    "example_semantic_stacks",
]

STACK_EXAMPLE_FIELDS = [
    "rank",
    "weight",
    "share_pct",
    "session",
    "prompt",
    "process",
    "effect",
    "baseline_key",
    "short_stack",
]


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


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def as_int(value: Any) -> int:
    if value in (None, ""):
        return 0
    return int(float(str(value)))


def as_float(value: Any) -> float:
    if value in (None, ""):
        return 0.0
    return float(str(value))


def pct(part: int | float, whole: int | float) -> float | None:
    if not whole:
        return None
    return round(100.0 * float(part) / float(whole), 3)


def parse_counter(text: str) -> Counter[str]:
    out: Counter[str] = Counter()
    for item in str(text or "").split(";"):
        item = item.strip()
        if not item or "=" not in item:
            continue
        key, value = item.rsplit("=", 1)
        key = key.strip()
        if key:
            out[key] += as_int(value.strip())
    return out


def compact_counter(counter: Counter[str], limit: int = 8) -> str:
    return "; ".join(f"{key}={value}" for key, value in counter.most_common(limit))


def parse_folded_line(line: str) -> tuple[str, int]:
    stack, _, weight = line.rstrip("\n").rpartition(" ")
    if not stack or not weight:
        raise ValueError(f"invalid folded line: {line[:160]}")
    return stack, as_int(weight)


def frames_from_stack(stack: str) -> dict[str, list[str]]:
    frames: dict[str, list[str]] = defaultdict(list)
    for frame in stack.split(";"):
        if ":" not in frame:
            continue
        key, value = frame.split(":", 1)
        frames[key].append(value)
    return frames


def first_frame(frames: dict[str, list[str]], key: str, default: str = "") -> str:
    values = frames.get(key) or []
    return values[0] if values else default


def process_label(frames: dict[str, list[str]]) -> str:
    if first_frame(frames, "process"):
        return first_frame(frames, "process")
    call = first_frame(frames, "call")
    if call:
        return call.replace("/", ":")
    tool = first_frame(frames, "tool")
    cmd = first_frame(frames, "cmd")
    if cmd:
        return cmd
    return tool or "unknown"


def baseline_key_for(frames: dict[str, list[str]]) -> str:
    process = process_label(frames)
    effect = first_frame(frames, "effect", "unknown")
    status = first_frame(frames, "status", "unknown")
    path = first_frame(frames, "path", "")
    domain = first_frame(frames, "domain", "")
    suffix = f";path:{path}" if path else (f";domain:{domain}" if domain else "")
    return f"process:{process};effect:{effect};status:{status}{suffix}"


def read_folded(path: Path) -> Counter[str]:
    counter: Counter[str] = Counter()
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            stack, weight = parse_folded_line(line)
            counter[stack] += weight
    return counter


def tag_distribution_rows(tag_rows: list[dict[str, str]], top_n: int = 12) -> list[dict[str, Any]]:
    by_dim: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in tag_rows:
        by_dim[row.get("dimension", "")].append(row)

    out: list[dict[str, Any]] = []
    for dimension in TAG_DIMENSIONS:
        rows = sorted(by_dim.get(dimension, []), key=lambda row: as_int(row.get("rank")))
        coverage_top_5 = round(sum(as_float(row.get("share_pct")) for row in rows[:5]), 3)
        unique = len(rows)
        for row in rows[:top_n]:
            out.append(
                {
                    "dimension": dimension,
                    "rank": as_int(row.get("rank")),
                    "tag": row.get("tag", ""),
                    "count": as_int(row.get("count")),
                    "share_pct": as_float(row.get("share_pct")),
                    "unit": row.get("unit", ""),
                    "coverage_top_5_pct": coverage_top_5,
                    "unique_tags_in_dimension": unique,
                }
            )
    return out


def process_split_rows(rows: list[dict[str, str]], top_n: int = 16) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for index, row in enumerate(
        sorted(rows, key=lambda item: as_int(item.get("total_weight")), reverse=True)[:top_n],
        start=1,
    ):
        total = as_int(row.get("total_weight"))
        top_weight = as_int(row.get("top_prompt_weight"))
        ambiguous = max(total - top_weight, 0)
        out.append(
            {
                "rank": index,
                "process": row.get("process", ""),
                "total_weight": total,
                "top_prompt": row.get("top_prompt", ""),
                "top_prompt_weight": top_weight,
                "top_prompt_share_pct": as_float(row.get("top_prompt_share_pct")),
                "distinct_prompt_tags": as_int(row.get("distinct_prompt_tags")),
                "ambiguous_weight": ambiguous,
                "ambiguous_share_pct": pct(ambiguous, total),
                "top_prompt_splits": row.get("top_prompt_splits", ""),
            }
        )
    return out


def baseline_collapse_rows(system: Counter[str], top_n: int = 14) -> list[dict[str, Any]]:
    groups: dict[str, dict[str, Any]] = defaultdict(
        lambda: {"total": 0, "prompts": Counter(), "examples": Counter()}
    )
    for stack, weight in system.items():
        frames = frames_from_stack(stack)
        prompt = first_frame(frames, "prompt", "unknown")
        key = baseline_key_for(frames)
        group = groups[key]
        group["total"] += weight
        group["prompts"][prompt] += weight
        group["examples"][stack] += weight

    rows: list[dict[str, Any]] = []
    for key, group in groups.items():
        prompts: Counter[str] = group["prompts"]
        if len(prompts) < 2:
            continue
        total = int(group["total"])
        top_prompt, top_weight = prompts.most_common(1)[0]
        ambiguous = max(total - top_weight, 0)
        rows.append(
            {
                "system_key": key,
                "total_weight": total,
                "distinct_prompt_tags": len(prompts),
                "top_prompt": top_prompt,
                "top_prompt_weight": top_weight,
                "top_prompt_share_pct": pct(top_weight, total),
                "ambiguous_weight": ambiguous,
                "ambiguous_share_pct": pct(ambiguous, total),
                "top_prompt_splits": compact_counter(prompts, 10),
                "example_semantic_stacks": " || ".join(
                    stack for stack, _ in group["examples"].most_common(3)
                ),
            }
        )

    rows.sort(key=lambda row: (-as_int(row["ambiguous_weight"]), -as_int(row["total_weight"]), row["system_key"]))
    for index, row in enumerate(rows[:top_n], start=1):
        row["rank"] = index
    return rows[:top_n]


def stack_example_rows(rows: list[dict[str, str]], top_n: int = 12) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for row in rows[:top_n]:
        frames = frames_from_stack(row.get("stack", ""))
        out.append(
            {
                "rank": as_int(row.get("rank")),
                "weight": as_int(row.get("weight")),
                "share_pct": as_float(row.get("share_pct")),
                "session": row.get("session", ""),
                "prompt": row.get("prompt", ""),
                "process": row.get("process", ""),
                "effect": row.get("effect", ""),
                "baseline_key": baseline_key_for(frames),
                "short_stack": row.get("short_stack", ""),
            }
        )
    return out


def bar_svg(path: Path, title: str, rows: list[tuple[str, float, str]], width: int = 980, row_h: int = 30) -> None:
    height = 86 + row_h * len(rows)
    left = 235
    right = 110
    max_value = max((value for _, value, _ in rows), default=1.0)
    palette = ["#2563eb", "#0f766e", "#b45309", "#7c3aed", "#be123c", "#475569"]
    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#ffffff"/>',
        f'<text x="24" y="34" font-family="Arial, sans-serif" font-size="22" font-weight="700">{html.escape(title)}</text>',
        '<text x="24" y="58" font-family="Arial, sans-serif" font-size="13" fill="#475569">Generated from redacted AgentFlame/R189 artifacts; bar width is support share.</text>',
    ]
    for idx, (label, value, detail) in enumerate(rows):
        y = 86 + idx * row_h
        bar_w = 1 if max_value == 0 else int((width - left - right) * value / max_value)
        color = palette[idx % len(palette)]
        lines.extend(
            [
                f'<text x="24" y="{y + 18}" font-family="Arial, sans-serif" font-size="13" fill="#0f172a">{html.escape(label)}</text>',
                f'<rect x="{left}" y="{y}" width="{bar_w}" height="20" rx="2" fill="{color}"/>',
                f'<text x="{left + bar_w + 8}" y="{y + 15}" font-family="Arial, sans-serif" font-size="12" fill="#334155">{html.escape(detail)}</text>',
            ]
        )
    lines.append("</svg>")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_markdown(path: Path, payload: dict[str, Any], tag_rows: list[dict[str, Any]], process_rows: list[dict[str, Any]], collapse_rows: list[dict[str, Any]], stack_rows: list[dict[str, Any]]) -> None:
    summary = payload["summary"]
    lines = [
        "# R211 Stack Examples And Tag Distribution",
        "",
        f"Status: `{payload['status']}`",
        "",
        "## Scope",
        "",
        "- Reads generated R170/R189 artifacts only.",
        "- Does not read or mutate raw Codex/Claude traces.",
        "- Does not call an LLM; R170 is the upstream real llama.cpp annotation run.",
        "- Supports RQ2 figure construction and case-study selection, not C5/C6 outcome claims.",
        "",
        "## Summary",
        "",
        f"- Sessions: {summary['session_count']}.",
        f"- System observations: {summary['system_observations']}.",
        f"- Semantic system stacks: {summary['semantic_system_stacks']}.",
        f"- Nonsemantic mixed weight: {summary['nonsemantic_mixed_weight_pct']}%.",
        f"- Flat mixed weight: {summary['flat_mixed_weight_pct']}%.",
        f"- Tag dimensions summarized: {summary['tag_dimensions']}.",
        f"- Baseline collapse examples: {summary['baseline_collapse_examples']}.",
        "",
        "## Top Label Shares",
        "",
        "| dimension | top tag | share | top-5 coverage | unique tags |",
        "|---|---|---:|---:|---:|",
    ]
    seen: set[str] = set()
    for row in tag_rows:
        dimension = row["dimension"]
        if dimension in seen or row["rank"] != 1:
            continue
        seen.add(dimension)
        lines.append(
            f"| {dimension} | `{row['tag']}` | {row['share_pct']}% | "
            f"{row['coverage_top_5_pct']}% | {row['unique_tags_in_dimension']} |"
        )

    lines.extend(["", "## Process Split Examples", "", "| process | weight | prompt tags | top split | ambiguous share |", "|---|---:|---:|---|---:|"])
    for row in process_rows[:8]:
        lines.append(
            f"| `{row['process']}` | {row['total_weight']} | {row['distinct_prompt_tags']} | "
            f"{row['top_prompt_splits']} | {row['ambiguous_share_pct']}% |"
        )

    lines.extend(["", "## Baseline Collapse Examples", "", "| system key | weight | prompt tags | top split | ambiguous share |", "|---|---:|---:|---|---:|"])
    for row in collapse_rows[:8]:
        lines.append(
            f"| `{row['system_key']}` | {row['total_weight']} | {row['distinct_prompt_tags']} | "
            f"{row['top_prompt_splits']} | {row['ambiguous_share_pct']}% |"
        )

    lines.extend(["", "## Top Semantic Stacks", "", "| rank | weight | session | prompt | process/effect | short stack |", "|---:|---:|---|---|---|---|"])
    for row in stack_rows[:8]:
        lines.append(
            f"| {row['rank']} | {row['weight']} | `{row['session']}` | `{row['prompt']}` | "
            f"`{row['process']}/{row['effect']}` | `{row['short_stack']}` |"
        )

    lines.extend(
        [
            "",
            "## Claim Boundary",
            "",
            "R211 supports figure selection and reviewer-auditable examples for RQ2. "
            "It does not prove tag adequacy, developer utility, or exact lineage breadth; "
            "those remain governed by the existing C5/C6/C4 gates.",
            "",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def build_payload(args: argparse.Namespace) -> tuple[dict[str, Any], dict[str, list[dict[str, Any]]]]:
    r170 = json.loads(args.r170_json.read_text(encoding="utf-8"))
    artifact_dir = REPO_ROOT / str((r170.get("agentflame_artifacts") or {}).get("dir", ""))
    system_path = artifact_dir / "semantic-system.folded.txt"
    tag_counts_path = args.tag_stats_dir / "tag-counts-r170.csv"
    process_splits_path = args.tag_stats_dir / "process-prompt-splits-r170.csv"
    top_stacks_path = args.tag_stats_dir / "top-semantic-stacks-r170.csv"
    for path in [args.r170_json, system_path, tag_counts_path, process_splits_path, top_stacks_path]:
        if not path.exists():
            raise FileNotFoundError(f"missing R211 input artifact: {rel(path)}")

    tag_counts = read_csv(tag_counts_path)
    process_splits = read_csv(process_splits_path)
    top_stacks = read_csv(top_stacks_path)
    system = read_folded(system_path)

    tags = tag_distribution_rows(tag_counts)
    processes = process_split_rows(process_splits)
    collapse = baseline_collapse_rows(system)
    stacks = stack_example_rows(top_stacks)
    r170_summary = r170.get("summary") or {}
    semantic_mixing = r170_summary.get("semantic_mixing") or {}

    summary = {
        "session_count": r170_summary.get("session_count"),
        "system_observations": r170_summary.get("system_observations"),
        "semantic_system_stacks": r170_summary.get("semantic_system_stacks"),
        "nonsemantic_system_stacks": r170_summary.get("nonsemantic_system_stacks"),
        "semantic_system_total_weight": sum(system.values()),
        "tag_dimensions": len(TAG_DIMENSIONS),
        "tag_distribution_rows": len(tags),
        "process_split_rows": len(processes),
        "baseline_collapse_examples": len(collapse),
        "top_stack_examples": len(stacks),
        "nonsemantic_mixed_weight_pct": semantic_mixing.get("nonsemantic_mixed_weight_pct"),
        "flat_mixed_weight_pct": semantic_mixing.get("flat_mixed_weight_pct"),
        "top_process_by_weight": processes[0]["process"] if processes else "",
        "top_process_distinct_prompt_tags": processes[0]["distinct_prompt_tags"] if processes else 0,
        "largest_baseline_ambiguous_weight": collapse[0]["ambiguous_weight"] if collapse else 0,
        "largest_baseline_ambiguous_share_pct": collapse[0]["ambiguous_share_pct"] if collapse else None,
    }

    payload = {
        "run_id": "R211",
        "schema_version": 1,
        "generated_at": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),
        "status": "stack_examples_ready_no_outcome_claims",
        "claim": "RQ2/C3 figure and case-study evidence only",
        "claim_boundary": (
            "R211 packages generated R170/R189 semantic stack outputs into label distributions, "
            "process split examples, baseline-collapse examples, and figure inputs. It does not "
            "support C5 developer utility, C6 tag adequacy, or broader exact-lineage claims."
        ),
        "input": {
            "r170_json": rel(args.r170_json),
            "r170_json_sha256": sha256_file(args.r170_json),
            "semantic_system_folded": rel(system_path),
            "semantic_system_folded_sha256": sha256_file(system_path),
            "tag_counts_csv": rel(tag_counts_path),
            "tag_counts_csv_sha256": sha256_file(tag_counts_path),
            "process_splits_csv": rel(process_splits_path),
            "process_splits_csv_sha256": sha256_file(process_splits_path),
            "top_stacks_csv": rel(top_stacks_path),
            "top_stacks_csv_sha256": sha256_file(top_stacks_path),
        },
        "summary": summary,
        "claim_gate": {
            "rq2_figure_inputs_supported": bool(tags and processes and collapse and stacks),
            "reads_generated_artifacts_only": True,
            "raw_trace_read": False,
            "llm_called": False,
            "developer_utility_supported": False,
            "semantic_adequacy_supported": False,
            "exact_lineage_breadth_supported": False,
        },
        "provenance": {
            "repo_commit": git(["rev-parse", "HEAD"]),
            "repo_dirty": bool(git(["status", "--short"])),
            "script_sha256": sha256_file(Path(__file__).resolve()),
        },
    }
    return payload, {
        "tags": tags,
        "processes": processes,
        "collapse": collapse,
        "stacks": stacks,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--r170-json", type=Path, default=DEFAULT_R170)
    parser.add_argument("--tag-stats-dir", type=Path, default=DEFAULT_TAG_STATS)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    payload, tables = build_payload(args)
    out_dir = args.out_dir
    paths = {
        "summary_json": out_dir / "stack-examples-r211.json",
        "summary_md": out_dir / "stack-examples-r211.md",
        "tag_distribution_csv": out_dir / "tag-distribution-r211.csv",
        "process_splits_csv": out_dir / "process-splits-r211.csv",
        "baseline_collapse_csv": out_dir / "baseline-collapse-examples-r211.csv",
        "top_stack_examples_csv": out_dir / "top-stack-examples-r211.csv",
        "tag_distribution_svg": out_dir / "tag-distribution-r211.svg",
        "process_splits_svg": out_dir / "process-splits-r211.svg",
    }
    payload["outputs"] = {key: rel(path) for key, path in paths.items()}

    write_json(paths["summary_json"], payload)
    write_csv(paths["tag_distribution_csv"], tables["tags"], TAG_DISTRIBUTION_FIELDS)
    write_csv(paths["process_splits_csv"], tables["processes"], PROCESS_SPLIT_FIELDS)
    write_csv(paths["baseline_collapse_csv"], tables["collapse"], BASELINE_COLLAPSE_FIELDS)
    write_csv(paths["top_stack_examples_csv"], tables["stacks"], STACK_EXAMPLE_FIELDS)
    write_markdown(paths["summary_md"], payload, tables["tags"], tables["processes"], tables["collapse"], tables["stacks"])

    prompt_weight_rows = [
        (f"{row['tag']} ({row['dimension'].replace('_tag_by_', ':')})", as_float(row["share_pct"]), f"{row['share_pct']}%")
        for row in tables["tags"]
        if row["dimension"] in {"prompt_tag_by_system_effect_weight", "session_tag_by_sessions"}
        and as_int(row["rank"]) <= 8
    ]
    bar_svg(paths["tag_distribution_svg"], "R211 Label Distribution", prompt_weight_rows[:16])
    process_rows = [
        (
            f"{row['process']} ({row['distinct_prompt_tags']} prompts)",
            as_float(row["ambiguous_share_pct"]),
            f"{row['ambiguous_share_pct']}% non-top prompt weight",
        )
        for row in tables["processes"][:12]
    ]
    bar_svg(paths["process_splits_svg"], "R211 Process Split By Prompt Semantics", process_rows[:12])

    print(json.dumps({"status": payload["status"], "summary_json": rel(paths["summary_json"])}, sort_keys=True))


if __name__ == "__main__":
    main()
