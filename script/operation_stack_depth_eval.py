#!/usr/bin/env python3
"""Evaluate the same operations under multiple recursive stack depths.

This is an experiment harness around the Rust `agentpprof --operation-file`
path. It does not define another profiler abstraction: operations are the
samples, operation-field mappings derive reusable fields, and each named stack
is only a different recursive operation-stack projection over the same samples.
"""

from __future__ import annotations

import argparse
import html
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


DEFAULT_STACKS: tuple[tuple[str, str], ...] = (
    ("dataset", "project,dataset"),
    ("task", "project,dataset,task"),
    ("phase", "project,dataset,task,phase"),
    ("op", "project,dataset,task,phase,op"),
    ("tool", "project,dataset,task,phase,op,tool"),
    ("semantic", "project,dataset,task,phase,op,tool,status"),
    ("action", "project,dataset,task,phase,op,tool,action,status"),
    ("fixed-session", "project,dataset,session,task,phase,op,tool,action,status"),
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--operation-file", action="append", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--op-map", action="append", default=[], help="FIELD:LABEL=REGEX")
    parser.add_argument("--op-map-file", action="append", type=Path, default=[])
    parser.add_argument(
        "--stack",
        action="append",
        default=[],
        help="Named stack as NAME=project,dataset,task,...; defaults to a depth sweep",
    )
    parser.add_argument("--project-root", default=".")
    parser.add_argument("--project-name", default="external-agent-traces")
    parser.add_argument("--agentpprof-manifest", default="agentpprof/Cargo.toml")
    args = parser.parse_args()

    stack_specs = parse_named_stacks(args.stack) if args.stack else list(DEFAULT_STACKS)
    args.out_dir.mkdir(parents=True, exist_ok=True)
    rows = []
    for name, stack in stack_specs:
        rows.append(run_stack_depth(name, stack, args))

    summary = build_summary(args, stack_specs, rows)
    (args.out_dir / "depth-summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (args.out_dir / "depth-summary.html").write_text(render_html(summary), encoding="utf-8")
    print(json.dumps(summary["summary"], indent=2, sort_keys=True))
    return 0


def parse_named_stacks(raw_stacks: list[str]) -> list[tuple[str, str]]:
    parsed = []
    seen = set()
    for raw in raw_stacks:
        name, sep, stack = raw.partition("=")
        name = name.strip()
        stack = stack.strip()
        if not sep or not name or not stack:
            raise SystemExit(f"invalid --stack {raw!r}; expected NAME=FIELD[,FIELD...]")
        if name in seen:
            raise SystemExit(f"duplicate stack name {name!r}")
        seen.add(name)
        parse_stack(stack)
        parsed.append((name, stack))
    return parsed


def parse_stack(raw: str) -> list[str]:
    fields = [part.strip() for part in raw.replace(";", ",").split(",") if part.strip()]
    if not fields:
        raise SystemExit("stack cannot be empty")
    return fields


def run_stack_depth(name: str, stack: str, args: argparse.Namespace) -> dict[str, Any]:
    depth_dir = args.out_dir / name
    depth_dir.mkdir(parents=True, exist_ok=True)
    folded = depth_dir / "stack.folded"
    agentpprof_result = depth_dir / "agentpprof-result.json"
    analysis_json = depth_dir / "stack-analysis.json"
    analysis_html = depth_dir / "stack-analysis.html"
    quality_json = depth_dir / "quality.json"
    quality_html = depth_dir / "quality.html"

    run_agentpprof(args, stack, folded, agentpprof_result)
    run_stack_analysis(folded, analysis_json, analysis_html)
    run_quality(args, stack, quality_json, quality_html)

    return summarize_row(
        name=name,
        stack=stack,
        depth_dir=depth_dir,
        agentpprof_result=read_json(agentpprof_result),
        analysis=read_json(analysis_json),
        quality=read_json(quality_json),
    )


def run_agentpprof(
    args: argparse.Namespace,
    stack: str,
    output: Path,
    result_path: Path,
) -> None:
    cmd = [
        "cargo",
        "run",
        "--quiet",
        "--manifest-path",
        args.agentpprof_manifest,
        "--",
        "--project-root",
        args.project_root,
        "--project-name",
        args.project_name,
        "--view",
        "operations",
        "--format",
        "folded",
        "-o",
        str(output),
        "--stack",
        stack,
    ]
    for path in args.operation_file:
        cmd.extend(["--operation-file", str(path)])
    for rule in args.op_map:
        cmd.extend(["--op-map", rule])
    for path in args.op_map_file:
        cmd.extend(["--op-map-file", str(path)])
    with result_path.open("w", encoding="utf-8") as f:
        run(cmd, stdout=f)


def run_stack_analysis(folded: Path, json_out: Path, html_out: Path) -> None:
    run(
        [
            sys.executable,
            "script/operation_stack_analysis.py",
            "--folded",
            str(folded),
            "--json-out",
            str(json_out),
            "--html-out",
            str(html_out),
        ]
    )


def run_quality(
    args: argparse.Namespace,
    stack: str,
    json_out: Path,
    html_out: Path,
) -> None:
    cmd = [
        sys.executable,
        "script/operation_stack_quality.py",
        "--stack",
        stack,
        "--coverage-field",
        "task",
        "--coverage-field",
        "phase",
        "--oracle-pair",
        "phase:action",
        "--oracle-pair",
        "task:dataset",
        "--oracle-pair",
        "tool:dataset",
        "--boundary-pair",
        "phase:action",
        "--json-out",
        str(json_out),
        "--html-out",
        str(html_out),
    ]
    for path in args.operation_file:
        cmd.extend(["--operation-file", str(path)])
    for rule in args.op_map:
        cmd.extend(["--op-map", rule])
    for path in args.op_map_file:
        cmd.extend(["--op-map-file", str(path)])
    run(cmd)


def run(cmd: list[str], stdout: Any | None = None) -> None:
    subprocess.run(cmd, check=True, stdout=stdout)


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def summarize_row(
    name: str,
    stack: str,
    depth_dir: Path,
    agentpprof_result: dict[str, Any],
    analysis: dict[str, Any],
    quality: dict[str, Any],
) -> dict[str, Any]:
    quality_summary = quality["summary"]
    boundary = first_metric(quality.get("boundary_alignment", []), "phase", "action")
    phase_action = first_metric(quality.get("oracle_alignment", []), "phase", "action")
    task_dataset = first_metric(quality.get("oracle_alignment", []), "task", "dataset")
    frames = parse_stack(stack)
    return {
        "name": name,
        "stack": stack,
        "depth": len(frames),
        "added_frame": frames[-1],
        "result_dir": str(depth_dir),
        "samples": int(agentpprof_result["samples"]),
        "unique_stacks": int(agentpprof_result["unique_stacks"]),
        "compression_ratio": round(float(quality_summary["compression_ratio"]), 3),
        "top_leaf": (analysis.get("top_leaves") or [{}])[0].get("name"),
        "top_leaf_weight": (analysis.get("top_leaves") or [{}])[0].get("weight", 0),
        "phase_action_v": phase_action.get("v_measure", 0.0),
        "task_dataset_v": task_dataset.get("v_measure", 0.0),
        "phase_action_boundary_f1": boundary.get("f1", 0.0),
    }


def first_metric(
    rows: list[dict[str, Any]],
    predicted: str,
    oracle: str,
) -> dict[str, Any]:
    for row in rows:
        if row.get("predicted") == predicted and row.get("oracle") == oracle:
            return row
    return {}


def build_summary(
    args: argparse.Namespace,
    stack_specs: list[tuple[str, str]],
    rows: list[dict[str, Any]],
) -> dict[str, Any]:
    baseline_unique = rows[0]["unique_stacks"] if rows else 0
    previous_unique = None
    for row in rows:
        unique = row["unique_stacks"]
        row["unique_vs_dataset_depth"] = (
            round(unique / baseline_unique, 4) if baseline_unique else 0.0
        )
        row["unique_delta_from_previous"] = (
            None if previous_unique is None else unique - previous_unique
        )
        previous_unique = unique
    return {
        "summary": {
            "stack_depths": len(rows),
            "samples": rows[0]["samples"] if rows else 0,
            "min_unique_stacks": min((row["unique_stacks"] for row in rows), default=0),
            "max_unique_stacks": max((row["unique_stacks"] for row in rows), default=0),
            "max_expansion_vs_dataset_depth": max(
                (row["unique_vs_dataset_depth"] for row in rows),
                default=0.0,
            ),
            "best_compression": max((row["compression_ratio"] for row in rows), default=0.0),
            "finest_stack": rows[-1]["name"] if rows else "",
        },
        "operation_files": [str(path) for path in args.operation_file],
        "op_maps": args.op_map,
        "op_map_files": [str(path) for path in args.op_map_file],
        "stack_specs": [{"name": name, "stack": stack} for name, stack in stack_specs],
        "rows": rows,
    }


def render_html(report: dict[str, Any]) -> str:
    summary = report["summary"]
    rows = report["rows"]
    return f"""<!doctype html>
<html>
<head>
<meta charset="utf-8">
<title>Operation Stack Depth Sweep</title>
<style>
body{{font-family:system-ui,-apple-system,Segoe UI,sans-serif;margin:24px;background:#fafafa;color:#171717}}
h1{{font-size:22px;margin:0 0 8px}}
.meta{{color:#555;margin-bottom:18px}}
table{{border-collapse:collapse;width:100%;font-size:13px;background:white;border:1px solid #ddd}}
td,th{{border-bottom:1px solid #eee;padding:7px;text-align:left;vertical-align:top}}
th{{background:#f5f5f5}}
code{{font-family:ui-monospace,Menlo,monospace;font-size:12px;white-space:pre-wrap}}
</style>
</head>
<body>
<h1>Operation Stack Depth Sweep</h1>
<div class="meta">samples={summary['samples']}; stack depths={summary['stack_depths']};
unique range={summary['min_unique_stacks']}..{summary['max_unique_stacks']};
best compression={summary['best_compression']}</div>
{rows_table(rows)}
</body>
</html>
"""


def rows_table(rows: list[dict[str, Any]]) -> str:
    columns = [
        "name",
        "depth",
        "added_frame",
        "unique_stacks",
        "unique_delta_from_previous",
        "unique_vs_dataset_depth",
        "compression_ratio",
        "phase_action_v",
        "phase_action_boundary_f1",
        "stack",
    ]
    out = ["<table><tr>"]
    out.extend(f"<th>{html.escape(column)}</th>" for column in columns)
    out.append("</tr>")
    for row in rows:
        out.append("<tr>")
        for column in columns:
            value = row.get(column)
            if column == "stack":
                out.append(f"<td><code>{html.escape(str(value))}</code></td>")
            else:
                out.append(f"<td>{html.escape(str(value))}</td>")
        out.append("</tr>")
    out.append("</table>")
    return "\n".join(out)


if __name__ == "__main__":
    raise SystemExit(main())
