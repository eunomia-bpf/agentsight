#!/usr/bin/env python3
"""Generate a readable real-trace operation-stack flamegraph artifact.

R401 intentionally focuses on one benchmark slice from the tracked R300 real
labeled operation file. The mixed four-benchmark flamegraph is too fragmented
for visual inspection, so this artifact shows AgentReward at two recursive
folding depths: an overview without session frames and a drilldown with session
frames.
"""

from __future__ import annotations

import html
import json
import shutil
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs/visexp/out/latest-real-trace-flamegraph-r401"
SOURCE = ROOT / "docs/visexp/out/operation-query-utility-r300/query-utility-operations.jsonl"
BENCHMARK_FILTER = "dataset=agent-reward-bench"
VIEW_SPECS = {
    "agentreward-overview": {
        "title": "AgentReward overview",
        "purpose": "A readable benchmark-level workload-shape view without per-session fragmentation.",
        "stack": "source,dataset,analysis_task,phase,tool,action,status",
    },
    "agentreward-session-drilldown": {
        "title": "AgentReward session drilldown",
        "purpose": "A deeper view that adds session only after the benchmark overview is readable.",
        "stack": "source,dataset,analysis_task,session,phase,tool,action,status",
    },
}
HIDDEN_LABEL_FIELDS = {
    "target_positive",
    "problem_value",
    "problem_oracle",
    "looping",
    "side_effect",
    "redundant",
    "correct",
    "unsafe",
    "boundary_label",
    "boundary_positive",
    "oracle",
    "label",
}


def run(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        cwd=ROOT,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )


def cargo_agentpprof(output: Path, fmt: str, stack: str, width: int | None = None) -> dict:
    cmd = [
        "cargo",
        "run",
        "--manifest-path",
        "agentpprof/Cargo.toml",
        "--",
        "--operation-file",
        str(SOURCE.relative_to(ROOT)),
        "--view",
        "operations",
        "--format",
        fmt,
        "--output",
        str(output.relative_to(ROOT)),
        "--where",
        BENCHMARK_FILTER,
        "--stack",
        stack,
        "--deterministic-output",
    ]
    if width is not None:
        cmd.extend(["--svg-width", str(width)])
    completed = run(cmd)
    start = completed.stdout.find("{")
    if start == -1:
        raise RuntimeError(f"agentpprof did not print JSON status:\n{completed.stdout}")
    status = json.loads(completed.stdout[start:])
    status["command"] = cmd
    return status


def clean_output_dir() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for path in OUT.iterdir():
        if path.is_file():
            path.unlink()


def parse_stack_fields(stack: str) -> dict[str, str]:
    fields: dict[str, str] = {}
    for token in stack.split(";"):
        token = token.strip()
        if ":" in token:
            key, value = token.split(":", 1)
            fields[key] = value
    return fields


def summarize_profile(view_name: str, spec: dict, profile_doc: dict) -> dict:
    profile = profile_doc["profile"]
    summary = profile["summary"]
    ranking = profile["ranking"]
    totals: dict[str, dict[str, int]] = {
        "source": {},
        "dataset": {},
        "analysis_task": {},
        "phase": {},
        "action": {},
        "status": {},
    }
    for stack, weight in profile["stacks"].items():
        fields = parse_stack_fields(stack)
        for field, values in totals.items():
            if field in fields:
                values[fields[field]] = values.get(fields[field], 0) + weight
    top_by_field = {
        field: sorted(values.items(), key=lambda item: (-item[1], item[0]))[:10]
        for field, values in totals.items()
    }
    return {
        "view": view_name,
        "title": spec["title"],
        "purpose": spec["purpose"],
        "operations": summary["total_weight"],
        "unique_stacks": summary["unique_stacks"],
        "compression_ratio": summary["compression_ratio"],
        "max_stack_reuse": summary["max_stack_reuse"],
        "stack": spec["stack"],
        "where": BENCHMARK_FILTER,
        "hidden_label_fields_in_stack": sorted(set(spec["stack"].split(",")) & HIDDEN_LABEL_FIELDS),
        "top_by_field": top_by_field,
        "top_stacks": ranking.get("top", [])[:12],
    }


def maybe_convert_png(svg: Path, png: Path) -> bool:
    converter = shutil.which("convert")
    if not converter:
        return False
    run(
        [
            converter,
            "-background",
            "white",
            str(svg.relative_to(ROOT)),
            str(png.relative_to(ROOT)),
        ]
    )
    return True


def generate_view(view_name: str, spec: dict) -> dict:
    base = OUT / view_name
    statuses = {
        "svg": cargo_agentpprof(base.with_suffix(".svg"), "svg", spec["stack"], width=1600),
        "folded": cargo_agentpprof(base.with_suffix(".folded"), "folded", spec["stack"]),
        "profile_json": cargo_agentpprof(base.with_suffix(".profile.json"), "json", spec["stack"]),
    }
    png_written = maybe_convert_png(base.with_suffix(".svg"), base.with_suffix(".png"))
    profile_doc = json.loads(base.with_suffix(".profile.json").read_text())
    summary = summarize_profile(view_name, spec, profile_doc)
    return {
        "summary": summary,
        "statuses": statuses,
        "outputs": {
            "svg": base.name + ".svg",
            "png": base.name + ".png" if png_written else None,
            "folded": base.name + ".folded",
            "profile_json": base.name + ".profile.json",
        },
    }


def write_markdown(result: dict) -> None:
    lines = [
        "# R401 Latest Real-Trace Operation-Stack Flamegraph",
        "",
        "This artifact focuses on one real benchmark slice, AgentReward, from the tracked R300 operation file.",
        "The overview omits session frames to avoid fragmentation. The drilldown adds session as a deeper recursive fold.",
        "",
        f"- source: `{result['source']}`",
        f"- filter: `{BENCHMARK_FILTER}`",
        "",
    ]
    for view_name, view in result["views"].items():
        summary = view["summary"]
        lines.extend(
            [
                f"## {summary['title']}",
                "",
                summary["purpose"],
                "",
                f"- operations: {summary['operations']}",
                f"- unique stacks: {summary['unique_stacks']}",
                f"- compression ratio: {summary['compression_ratio']}",
                f"- max stack reuse: {summary['max_stack_reuse']}",
                f"- stack: `{summary['stack']}`",
                f"- hidden label fields in stack: {summary['hidden_label_fields_in_stack']}",
                "",
                "| analysis task | operations |",
                "|---|---:|",
            ]
        )
        lines.extend(
            f"| {name} | {weight} |"
            for name, weight in summary["top_by_field"]["analysis_task"]
        )
        lines.extend(["", "| phase | operations |", "|---|---:|"])
        lines.extend(f"| {name} | {weight} |" for name, weight in summary["top_by_field"]["phase"])
        lines.append("")
    (OUT / "report.md").write_text("\n".join(lines) + "\n")


def write_index(result: dict) -> None:
    def row(cells: list[str]) -> str:
        return "<tr>" + "".join(f"<td>{html.escape(str(cell))}</td>" for cell in cells) + "</tr>"

    sections = []
    for view_name, view in result["views"].items():
        summary = view["summary"]
        output = view["outputs"]
        task_rows = "\n".join(
            row([name, weight]) for name, weight in summary["top_by_field"]["analysis_task"]
        )
        phase_rows = "\n".join(row([name, weight]) for name, weight in summary["top_by_field"]["phase"])
        top_rows = "\n".join(
            row([item["weight"], item["stack"]]) for item in summary["top_stacks"][:10]
        )
        command_rows = "\n".join(
            row([name, " ".join(status["command"])])
            for name, status in view["statuses"].items()
        )
        sections.append(
            f"""
<section>
<h2>{html.escape(summary['title'])}</h2>
<p>{html.escape(summary['purpose'])}</p>
<p>
<span class="metric">operations: {summary['operations']}</span>
<span class="metric">unique stacks: {summary['unique_stacks']}</span>
<span class="metric">hidden label fields in stack: {len(summary['hidden_label_fields_in_stack'])}</span>
</p>
<p><code>{html.escape(summary['stack'])}</code></p>
<iframe src="{html.escape(output['svg'])}"></iframe>
<h3>Analysis Tasks</h3>
<table><thead><tr><th>analysis task</th><th>operations</th></tr></thead><tbody>{task_rows}</tbody></table>
<h3>Phases</h3>
<table><thead><tr><th>phase</th><th>operations</th></tr></thead><tbody>{phase_rows}</tbody></table>
<h3>Top Stacks</h3>
<table><thead><tr><th>weight</th><th>stack</th></tr></thead><tbody>{top_rows}</tbody></table>
<h3>Replay Commands</h3>
<table><thead><tr><th>output</th><th>command</th></tr></thead><tbody>{command_rows}</tbody></table>
</section>
"""
        )
    html_doc = f"""<!doctype html>
<meta charset="utf-8">
<title>R401 AgentReward Operation-Stack Flamegraphs</title>
<style>
body {{ font-family: system-ui, sans-serif; margin: 24px; color: #1f2933; }}
h1, h2, h3 {{ margin-bottom: 0.3rem; }}
p {{ max-width: 980px; line-height: 1.45; }}
table {{ border-collapse: collapse; margin: 12px 0 24px; width: 100%; }}
th, td {{ border: 1px solid #d8dee9; padding: 6px 8px; vertical-align: top; font-size: 13px; }}
th {{ background: #eef2f7; text-align: left; }}
.metric {{ display: inline-block; margin-right: 18px; font-weight: 650; }}
iframe {{ width: 100%; height: 420px; border: 1px solid #d8dee9; }}
code {{ background: #eef2f7; padding: 1px 4px; border-radius: 4px; }}
section {{ margin-bottom: 42px; }}
</style>
<h1>R401 AgentReward Operation-Stack Flamegraphs</h1>
<p>The profiler folds one real benchmark slice from the tracked R300 operation
file. This avoids mixing unrelated benchmarks and shows why stack depth is a
profile choice: the overview gives a compact benchmark structure, while the
session drilldown adds session frames only when the reader wants deeper detail.</p>
<p><strong>Source:</strong> <code>{html.escape(result['source'])}</code><br>
<strong>Filter:</strong> <code>{html.escape(BENCHMARK_FILTER)}</code></p>
{''.join(sections)}
"""
    (OUT / "index.html").write_text(html_doc)


def main() -> None:
    if not SOURCE.exists():
        raise FileNotFoundError(SOURCE)
    clean_output_dir()
    views = {name: generate_view(name, spec) for name, spec in VIEW_SPECS.items()}
    checks = {
        "uses_tracked_real_trace": SOURCE.exists(),
        "single_benchmark_filter": BENCHMARK_FILTER == "dataset=agent-reward-bench",
        "overview_avoids_session_fragmentation": "session" not in VIEW_SPECS["agentreward-overview"]["stack"],
        "drilldown_adds_session": "session" in VIEW_SPECS["agentreward-session-drilldown"]["stack"],
        "no_hidden_label_stack_frames": all(
            not view["summary"]["hidden_label_fields_in_stack"] for view in views.values()
        ),
        "overview_matches_agentreward_count": views["agentreward-overview"]["summary"]["operations"] == 1458,
        "drilldown_matches_agentreward_count": views["agentreward-session-drilldown"]["summary"]["operations"] == 1458,
        "overview_is_less_fragmented_than_drilldown": views["agentreward-overview"]["summary"]["unique_stacks"]
        < views["agentreward-session-drilldown"]["summary"]["unique_stacks"],
    }
    result = {
        "run_id": "R401",
        "status": "pass" if all(checks.values()) else "fail",
        "source": str(SOURCE.relative_to(ROOT)),
        "filter": BENCHMARK_FILTER,
        "checks": checks,
        "views": views,
    }
    (OUT / "run-result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    (OUT / "summary.json").write_text(
        json.dumps({name: view["summary"] for name, view in views.items()}, indent=2, sort_keys=True)
        + "\n"
    )
    write_markdown(result)
    write_index(result)
    print(json.dumps({"status": result["status"], "checks": checks}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
