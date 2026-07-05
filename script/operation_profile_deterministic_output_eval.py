#!/usr/bin/env python3
"""R328: byte-stable deterministic output probe for profile specs.

R327 showed semantic profile content is reproducible, but raw JSON bytes differ
because profiles include `generated_at`.  R328 exercises the Rust
`--deterministic-output` mode on the same tracked R300/R324/R326 profile specs
and operation JSONL inputs.  It checks whether raw output bytes, semantic
content, samples, and unique-stack counts are stable across repeated runs.
"""

from __future__ import annotations

import csv
import html
import json
import time
from pathlib import Path
from typing import Any

import operation_profile_cost_eval as r327


ROOT = r327.ROOT
DEFAULT_OUT_DIR = r327.OUT_ROOT / "operation-profile-deterministic-output-r328"
RUN_ID = "R328"
EXTRA_AGENTPPROF_ARGS = ["--deterministic-output"]


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_csv(out_dir: Path, rows: list[dict[str, Any]]) -> None:
    fieldnames = [
        "experiment",
        "spec",
        "format",
        "operation_rows",
        "samples",
        "unique_stacks",
        "median_runtime_ms",
        "output_bytes",
        "deterministic_semantic_hash",
        "deterministic_raw_hash",
        "stable_samples",
        "stable_unique_stacks",
        "hash",
        "raw_hash",
    ]
    with (out_dir / "deterministic-output-summary.csv").open(
        "w", encoding="utf-8", newline=""
    ) as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fieldnames})


def write_markdown(out_dir: Path, report: dict[str, Any]) -> None:
    summary = report["summary"]
    lines = [
        "# R328 Deterministic Profile Output",
        "",
        "This probe reruns the same tracked R300/R324/R326 profile specs as R327, but passes `--deterministic-output` to the Rust profiler.",
        "",
        f"- Specs: {summary['specs']}",
        f"- Repetitions per spec: {summary['reps_per_spec']}",
        f"- Profiler invocations: {summary['profiler_invocations']}",
        f"- Semantic deterministic specs: {summary['semantic_deterministic_specs']}",
        f"- Raw-byte deterministic specs: {summary['raw_byte_deterministic_specs']}",
        f"- Median runtime: {summary['median_runtime_ms']:.4f} ms",
        f"- P95 runtime: {summary['p95_runtime_ms']:.4f} ms",
        "",
        "## By Experiment",
        "",
        "| Experiment | Specs | Median runtime (ms) | P95 runtime (ms) | Median unique stacks | Median output bytes |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for experiment, row in summary["experiment_summary"].items():
        lines.append(
            f"| {experiment} | {row['specs']} | {row['median_runtime_ms']:.4f} | "
            f"{row['p95_runtime_ms']:.4f} | {row['median_unique_stacks']} | "
            f"{row['median_output_bytes']} |"
        )
    lines.extend(["", "## Claim Scope", "", report["claim"], ""])
    lines.extend(f"- {item}" for item in report["non_claims"])
    (out_dir / "deterministic-output-report.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )


def write_html(out_dir: Path, report: dict[str, Any]) -> None:
    summary = report["summary"]
    experiment_rows = "\n".join(
        f"<tr><td>{html.escape(name)}</td><td>{item['specs']}</td>"
        f"<td>{item['median_runtime_ms']:.4f}</td>"
        f"<td>{item['p95_runtime_ms']:.4f}</td>"
        f"<td>{item['median_unique_stacks']}</td>"
        f"<td>{item['median_output_bytes']}</td></tr>"
        for name, item in summary["experiment_summary"].items()
    )
    non_claim_items = "\n".join(
        f"<li>{html.escape(item)}</li>" for item in report["non_claims"]
    )
    html_doc = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>R328 Deterministic Profile Output</title>
<style>
body {{ font-family: system-ui, sans-serif; margin: 32px; color: #1f2937; }}
table {{ border-collapse: collapse; width: 100%; margin: 16px 0 28px; }}
th, td {{ border-bottom: 1px solid #d1d5db; padding: 8px; text-align: right; }}
th:first-child, td:first-child {{ text-align: left; }}
code {{ background: #f3f4f6; padding: 1px 4px; border-radius: 4px; }}
</style>
</head>
<body>
<h1>R328 Deterministic Profile Output</h1>
<p>The same tracked profile specs as R327 were rerun with <code>--deterministic-output</code>.</p>
<ul>
<li>Specs: {summary['specs']}</li>
<li>Profiler invocations: {summary['profiler_invocations']}</li>
<li>Semantic deterministic specs: {html.escape(summary['semantic_deterministic_specs'])}</li>
<li>Raw-byte deterministic specs: {html.escape(summary['raw_byte_deterministic_specs'])}</li>
<li>Median runtime: {summary['median_runtime_ms']:.4f} ms</li>
</ul>
<table><thead><tr><th>Experiment</th><th>Specs</th><th>Median ms</th><th>P95 ms</th><th>Median stacks</th><th>Median bytes</th></tr></thead><tbody>{experiment_rows}</tbody></table>
<h2>Claim Scope</h2>
<p>{html.escape(report['claim'])}</p>
<ul>{non_claim_items}</ul>
</body>
</html>
"""
    (out_dir / "index.html").write_text(html_doc, encoding="utf-8")


def main() -> None:
    started = time.perf_counter()
    out_dir = DEFAULT_OUT_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    binary_status = r327.ensure_agentpprof_binary(r327.DEFAULT_BINARY, skip_build=False)
    specs = r327.discover_specs()
    rows, source_check = r327.evaluate_specs(
        r327.DEFAULT_BINARY.resolve(),
        specs,
        reps=2,
        agentpprof_args=EXTRA_AGENTPPROF_ARGS,
    )
    summary = r327.aggregate(rows, reps=2)
    status = "pass" if summary["all_specs_deterministic"] and summary[
        "raw_byte_deterministic_specs"
    ] == f"{summary['specs']}/{summary['specs']}" else "fail"
    source_status = {
        "git_status_short": r327.git_output(["status", "--short"]),
        "code_status_short": r327.git_output(
            [
                "status",
                "--short",
                "--",
                "agentpprof",
                "script/operation_profile_cost_eval.py",
                "script/operation_profile_deterministic_output_eval.py",
            ]
        ),
    }
    report = {
        "run_id": RUN_ID,
        "status": status,
        "commit": r327.git_output(["rev-parse", "HEAD"]),
        "source_status": source_status,
        "elapsed_s": round(time.perf_counter() - started, 3),
        "agentpprof_args": EXTRA_AGENTPPROF_ARGS,
        "binary_status": binary_status,
        "source_check": source_check,
        "summary": summary,
        "spec_rows": rows,
        "claim": (
            "Deterministic output mode makes tracked operation-profile specs "
            "byte-stable across repeated offline profiler runs."
        ),
        "non_claims": [
            "This is not live eBPF capture overhead.",
            "This is not a human or agent analyst productivity study.",
            "This does not download, sync, or create a dataset.",
            "This does not claim complete trace-platform ecosystem compatibility.",
            "This does not claim a performance improvement over R327.",
            "This is not a detector or boundary-discovery benchmark.",
        ],
    }
    write_json(out_dir / "deterministic-output-report.json", r327.rounded(report))
    write_json(
        out_dir / "run-result.json",
        {
            "status": status,
            "report": r327.rel(out_dir / "deterministic-output-report.json"),
        },
    )
    write_csv(out_dir, rows)
    write_markdown(out_dir, report)
    write_html(out_dir, report)
    if status != "pass":
        raise SystemExit("R328 deterministic output check failed")


if __name__ == "__main__":
    main()
