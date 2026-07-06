#!/usr/bin/env python3
"""R353: standard trace exchange for real labeled operation JSONL.

This is a reproducibility/exchange smoke over existing tracked operation rows:

operation JSONL -> Chrome Trace Event JSON -> agentpprof --standard-trace-file

The standard trace remains an exchange container. The profiler still imports
events back into operations before constructing operation stacks.
"""

from __future__ import annotations

import argparse
import html
import json
import subprocess
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OPERATION_FILE = (
    REPO_ROOT
    / "docs/visexp/out/operation-rank-feature-r324/visible-query-utility-operations.jsonl"
)
DEFAULT_OUT_DIR = REPO_ROOT / "docs/visexp/out/operation-standard-trace-exchange-r353"
DEFAULT_STACK = "project,dataset,analysis_task,phase,op,action,status"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Export a deterministic prefix of an existing labeled operation JSONL "
            "corpus as Chrome Trace Event JSON, import it through the Rust "
            "standard-trace path, and check folded-stack equality."
        )
    )
    parser.add_argument("--operation-file", type=Path, default=DEFAULT_OPERATION_FILE)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--project-name", default="external-agent-traces")
    parser.add_argument("--limit", type=int, default=512)
    parser.add_argument("--stack", default=DEFAULT_STACK)
    parser.add_argument(
        "--agentpprof-bin",
        type=Path,
        help=(
            "Optional compiled agentpprof binary. If omitted, the script uses "
            "`cargo run --quiet --manifest-path agentpprof/Cargo.toml --`."
        ),
    )
    return parser.parse_args()


def relative(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def command_path(path: Path) -> str:
    return relative(path)


def agentpprof_command(args: argparse.Namespace) -> list[str]:
    if args.agentpprof_bin:
        return [str(args.agentpprof_bin)]
    return [
        "cargo",
        "run",
        "--quiet",
        "--manifest-path",
        "agentpprof/Cargo.toml",
        "--",
    ]


def run_json(command: list[str], label: str) -> dict[str, Any]:
    completed = subprocess.run(
        command,
        cwd=REPO_ROOT,
        check=False,
        text=True,
        capture_output=True,
    )
    if completed.returncode != 0:
        raise SystemExit(
            f"{label} failed with exit code {completed.returncode}\n"
            f"command: {' '.join(command)}\n"
            f"stdout:\n{completed.stdout}\n"
            f"stderr:\n{completed.stderr}"
        )
    try:
        payload = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise SystemExit(
            f"{label} did not emit JSON: {exc}\nstdout:\n{completed.stdout}\n"
            f"stderr:\n{completed.stderr}"
        ) from exc
    payload["_command"] = command
    if completed.stderr.strip():
        payload["_stderr"] = completed.stderr.strip()
    return payload


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_operation_prefix(src: Path, dst: Path, limit: int) -> int:
    if limit <= 0:
        raise SystemExit("--limit must be positive")
    count = 0
    with src.open("r", encoding="utf-8") as inp, dst.open("w", encoding="utf-8") as out:
        for line in inp:
            if not line.strip():
                continue
            out.write(line)
            count += 1
            if count >= limit:
                break
    if count == 0:
        raise SystemExit(f"operation file produced zero rows: {src}")
    return count


def folded_stats(path: Path) -> dict[str, int]:
    samples = 0
    stacks = 0
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        stacks += 1
        try:
            samples += int(line.rsplit(" ", 1)[1])
        except (IndexError, ValueError):
            pass
    return {"samples": samples, "unique_stacks": stacks}


def trace_shape(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    events = payload.get("traceEvents") if isinstance(payload, dict) else None
    metadata = payload.get("metadata", {}) if isinstance(payload, dict) else {}
    if not isinstance(events, list):
        return {"valid": False, "events": 0, "complete_events": 0}
    return {
        "valid": True,
        "events": len(events),
        "complete_events": sum(
            1 for event in events if isinstance(event, dict) and event.get("ph") == "X"
        ),
        "metadata_format": metadata.get("format"),
        "source_schema": metadata.get("source_schema"),
        "operation_schema": metadata.get("operation_schema"),
    }


def write_markdown(path: Path, report: dict[str, Any]) -> None:
    lines = [
        "# Operation Standard Trace Exchange R353",
        "",
        "R353 verifies the Rust operation-file standard trace export/import path on",
        "a deterministic prefix of an existing real labeled operation corpus.",
        "It is an exchange/reproducibility smoke, not a new accuracy result.",
        "",
        "## Result",
        "",
        f"- Status: `{report['status']}`",
        f"- Source operation file: `{report['source_operation_file']}`",
        f"- Prefix rows: {report['prefix_operations']}",
        f"- Standard trace events: {report['standard_trace']['events']}",
        f"- Direct/imported folded equality: `{report['folded_outputs_equal']}`",
        f"- Stack: `{report['stack']}`",
        "",
        "## Files",
        "",
    ]
    for key in [
        "prefix_operation_file",
        "standard_trace_file",
        "direct_folded",
        "imported_folded",
        "report_json",
        "index_html",
    ]:
        lines.append(f"- `{key}`: `{report[key]}`")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_html(path: Path, report: dict[str, Any]) -> None:
    rows = [
        ("Status", report["status"]),
        ("Prefix operations", report["prefix_operations"]),
        ("Standard trace events", report["standard_trace"]["events"]),
        ("Trace source schema", report["standard_trace"]["source_schema"]),
        ("Direct samples", report["direct_profile"]["samples"]),
        ("Imported samples", report["imported_profile"]["samples"]),
        ("Folded outputs equal", str(report["folded_outputs_equal"]).lower()),
    ]
    body = "\n".join(
        f"<tr><th>{html.escape(str(key))}</th><td>{html.escape(str(value))}</td></tr>"
        for key, value in rows
    )
    status_class = "pass" if report["status"] == "ok" else "fail"
    path.write_text(
        f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Operation Standard Trace Exchange R353</title>
  <style>
    body {{ font-family: system-ui, sans-serif; margin: 2rem; color: #1f2933; }}
    h1 {{ font-size: 1.6rem; margin-bottom: 0.25rem; }}
    p {{ max-width: 820px; line-height: 1.5; }}
    table {{ border-collapse: collapse; margin-top: 1.5rem; min-width: 560px; }}
    th, td {{ border: 1px solid #d8dee9; padding: 0.55rem 0.75rem; text-align: left; }}
    th {{ background: #f6f8fa; width: 240px; }}
    .pass {{ color: #176f3d; font-weight: 700; }}
    .fail {{ color: #a61b1b; font-weight: 700; }}
    code {{ background: #f6f8fa; padding: 0.1rem 0.25rem; border-radius: 4px; }}
  </style>
</head>
<body>
  <h1>Operation Standard Trace Exchange R353</h1>
  <p>
    A deterministic prefix of a real labeled operation corpus is exported by the
    Rust CLI as Chrome Trace Event JSON, then imported through
    <code>--standard-trace-file</code> and folded with the same operation stack.
    The standard trace is an exchange container; the profiler still uses only
    operations and operation stacks.
  </p>
  <table>
{body}
  </table>
  <p class="{status_class}">Exchange status: {html.escape(report["status"])}</p>
</body>
</html>
""",
        encoding="utf-8",
    )


def main() -> None:
    args = parse_args()
    out_dir = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    prefix_operation_file = out_dir / "operation-prefix.jsonl"
    standard_trace_file = out_dir / "operation-prefix-chrome-trace.json"
    direct_folded = out_dir / "direct-operation.folded"
    imported_folded = out_dir / "standard-trace-import.folded"
    report_json = out_dir / "standard-trace-exchange-report.json"
    report_md = out_dir / "standard-trace-exchange-report.md"
    index_html = out_dir / "index.html"

    prefix_operations = write_operation_prefix(
        args.operation_file, prefix_operation_file, args.limit
    )

    agentpprof = agentpprof_command(args)
    common_profile_args = [
        "--project-name",
        args.project_name,
        "--view",
        "operations",
        "--stack",
        args.stack,
        "--format",
        "folded",
    ]

    export_result = run_json(
        agentpprof
        + [
            "--project-name",
            args.project_name,
            "--operation-file",
            command_path(prefix_operation_file),
            "--export-standard-trace",
            command_path(standard_trace_file),
        ],
        "operation standard trace export",
    )
    write_json(out_dir / "operation-standard-trace-export-result.json", export_result)

    direct_result = run_json(
        agentpprof
        + common_profile_args
        + [
            "--operation-file",
            command_path(prefix_operation_file),
            "-o",
            command_path(direct_folded),
        ],
        "direct operation profile",
    )
    write_json(out_dir / "direct-operation-profile-result.json", direct_result)

    imported_result = run_json(
        agentpprof
        + common_profile_args
        + [
            "--standard-trace-file",
            command_path(standard_trace_file),
            "-o",
            command_path(imported_folded),
        ],
        "standard trace import profile",
    )
    write_json(out_dir / "standard-trace-import-profile-result.json", imported_result)

    folded_outputs_equal = direct_folded.read_bytes() == imported_folded.read_bytes()
    shape = trace_shape(standard_trace_file)
    status = (
        "ok"
        if shape["valid"]
        and shape["events"] == prefix_operations
        and shape["source_schema"] == "agentsight.operation.v1"
        and folded_outputs_equal
        else "mismatch"
    )

    report = {
        "run_id": "R353",
        "status": status,
        "input_policy": {
            "dataset_sync": "none",
            "dataset_creation": "none",
            "source": "tracked prefix of existing real labeled operation JSONL",
            "not_accuracy_result": True,
        },
        "source_operation_file": relative(args.operation_file),
        "prefix_operation_file": relative(prefix_operation_file),
        "standard_trace_file": relative(standard_trace_file),
        "direct_folded": relative(direct_folded),
        "imported_folded": relative(imported_folded),
        "report_json": relative(report_json),
        "report_markdown": relative(report_md),
        "index_html": relative(index_html),
        "stack": args.stack,
        "prefix_operations": prefix_operations,
        "standard_trace": shape,
        "folded_outputs_equal": folded_outputs_equal,
        "direct_profile": folded_stats(direct_folded),
        "imported_profile": folded_stats(imported_folded),
        "export_result": {
            "operations": export_result.get("operations"),
            "standard_trace_events": export_result.get("standard_trace_events"),
        },
        "direct_profile_result": {
            "samples": direct_result.get("samples"),
            "unique_stacks": direct_result.get("unique_stacks"),
        },
        "imported_profile_result": {
            "operations": imported_result.get("operations"),
            "samples": imported_result.get("samples"),
            "unique_stacks": imported_result.get("unique_stacks"),
        },
    }
    write_json(report_json, report)
    write_markdown(report_md, report)
    write_html(index_html, report)

    print(json.dumps(report, indent=2, sort_keys=True))
    if status != "ok":
        raise SystemExit("operation standard trace exchange did not preserve folded output")


if __name__ == "__main__":
    main()
