#!/usr/bin/env python3
"""R306: reproduce Chrome/Perfetto trace exchange for agent sessions.

The bridge is:

agent session -> agentsight.agent-session.trace.v1
  -> Chrome Trace Event JSON
  -> operation JSONL
  -> agentpprof operation stack

The standard trace is treated as an exchange format only. The profiler input
after import is still operation JSONL.
"""

from __future__ import annotations

import argparse
import html
import json
import subprocess
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SESSION = (
    REPO_ROOT
    / "agentpprof/examples/codex/sessions/2026/06/18/public-agentpprof-fixture.jsonl"
)
DEFAULT_OUT_DIR = REPO_ROOT / "docs/visexp/out/agent-trace-chrome-exchange-r306"
DEFAULT_STACK = "project,agent,op,phase,tool,status"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Export an agent session to Chrome Trace Event JSON, import it back "
            "to operation JSONL, and compare folded operation-stack output."
        )
    )
    parser.add_argument("--session-file", type=Path, default=DEFAULT_SESSION)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--project-name", default="agentsight")
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


def chrome_trace_shape(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    events = payload.get("traceEvents") if isinstance(payload, dict) else None
    if not isinstance(events, list):
        return {"valid": False, "events": 0, "complete_events": 0}
    return {
        "valid": True,
        "events": len(events),
        "complete_events": sum(1 for event in events if isinstance(event, dict) and event.get("ph") == "X"),
        "metadata_format": (payload.get("metadata") or {}).get("format"),
    }


def write_markdown(path: Path, report: dict[str, Any]) -> None:
    lines = [
        "# Agent Trace Chrome Exchange R306",
        "",
        "R306 verifies a standard trace exchange path for local agent sessions.",
        "Chrome/Perfetto trace JSON is used only as an import/export format; after import, profiling continues over operation JSONL.",
        "",
        "## Result",
        "",
        f"- Chrome trace valid: `{report['chrome_trace']['valid']}`",
        f"- Chrome events: {report['chrome_trace']['events']}",
        f"- Operations from direct trace conversion: {report['direct_operations']}",
        f"- Operations from Chrome trace import: {report['chrome_operations']}",
        f"- Direct trace/import folded equality: `{report['direct_trace_equals_direct_operations']}`",
        f"- Chrome import folded equality: `{report['chrome_operations_equal_direct_operations']}`",
        f"- Stack: `{report['stack']}`",
        "",
        "## Files",
        "",
    ]
    for key in [
        "agent_trace_file",
        "chrome_trace_file",
        "direct_operation_file",
        "chrome_operation_file",
        "trace_folded",
        "direct_operation_folded",
        "chrome_operation_folded",
        "report_json",
    ]:
        lines.append(f"- `{key}`: `{report[key]}`")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_html(path: Path, report: dict[str, Any]) -> None:
    rows = [
        ("Chrome trace valid", str(report["chrome_trace"]["valid"]).lower()),
        ("Chrome events", report["chrome_trace"]["events"]),
        ("Direct operations", report["direct_operations"]),
        ("Chrome operations", report["chrome_operations"]),
        (
            "Trace vs direct operations",
            str(report["direct_trace_equals_direct_operations"]).lower(),
        ),
        (
            "Chrome vs direct operations",
            str(report["chrome_operations_equal_direct_operations"]).lower(),
        ),
    ]
    body = "\n".join(
        f"<tr><th>{html.escape(str(key))}</th><td>{html.escape(str(value))}</td></tr>"
        for key, value in rows
    )
    status = "pass" if report["status"] == "ok" else "fail"
    path.write_text(
        """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Agent Trace Chrome Exchange R306</title>
  <style>
    body { font-family: system-ui, sans-serif; margin: 2rem; color: #1f2933; }
    h1 { font-size: 1.6rem; margin-bottom: 0.25rem; }
    p { max-width: 760px; line-height: 1.5; }
    table { border-collapse: collapse; margin-top: 1.5rem; min-width: 520px; }
    th, td { border: 1px solid #d8dee9; padding: 0.55rem 0.75rem; text-align: left; }
    th { background: #f6f8fa; width: 220px; }
    .pass { color: #176f3d; font-weight: 700; }
    .fail { color: #a61b1b; font-weight: 700; }
    code { background: #f6f8fa; padding: 0.1rem 0.25rem; border-radius: 4px; }
  </style>
</head>
<body>
  <h1>Agent Trace Chrome Exchange R306</h1>
  <p>
    A local agent session exports to Chrome Trace Event JSON, imports back to
    operation JSONL, and folds with the same operation stack. The standard trace
    remains an exchange format, not a profiler abstraction.
  </p>
  <table>
"""
        + body
        + f"""
  </table>
  <p class="{status}">Exchange status: {status}</p>
</body>
</html>
""",
        encoding="utf-8",
    )


def main() -> None:
    args = parse_args()
    out_dir = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    agent_trace_file = out_dir / "fixture-agent-trace.json"
    chrome_trace_file = out_dir / "fixture-chrome-trace.json"
    direct_operation_file = out_dir / "fixture-direct-operations.jsonl"
    chrome_operation_file = out_dir / "fixture-chrome-operations.jsonl"
    trace_folded = out_dir / "trace-import.folded"
    direct_operation_folded = out_dir / "direct-operation-import.folded"
    chrome_operation_folded = out_dir / "chrome-operation-import.folded"

    agentpprof = agentpprof_command(args)
    common_profile_args = [
        "--project-root",
        ".",
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
            "--project-root",
            ".",
            "--project-name",
            args.project_name,
            "--session-file",
            command_path(args.session_file),
            "--export-trace",
            command_path(agent_trace_file),
        ],
        "agent trace export",
    )
    write_json(out_dir / "agent-trace-export-result.json", export_result)

    direct_convert = run_json(
        [
            "python3",
            "script/agent_trace_convert.py",
            "to-operations",
            "--trace-file",
            command_path(agent_trace_file),
            "--project-name",
            args.project_name,
            "--out",
            command_path(direct_operation_file),
        ],
        "agent trace to operations",
    )
    write_json(out_dir / "direct-trace-to-operations-result.json", direct_convert)

    chrome_export = run_json(
        [
            "python3",
            "script/agent_trace_convert.py",
            "export-standard",
            "--format",
            "chrome",
            "--trace-file",
            command_path(agent_trace_file),
            "--project-name",
            args.project_name,
            "--out",
            command_path(chrome_trace_file),
        ],
        "Chrome trace export",
    )
    write_json(out_dir / "chrome-export-result.json", chrome_export)

    chrome_import = run_json(
        [
            "python3",
            "script/agent_trace_convert.py",
            "import-standard",
            "--format",
            "chrome",
            "--trace-file",
            command_path(chrome_trace_file),
            "--project-name",
            args.project_name,
            "--out",
            command_path(chrome_operation_file),
        ],
        "Chrome trace import",
    )
    write_json(out_dir / "chrome-import-result.json", chrome_import)

    trace_profile = run_json(
        agentpprof
        + common_profile_args
        + ["--trace-file", command_path(agent_trace_file), "-o", command_path(trace_folded)],
        "direct trace profile",
    )
    write_json(out_dir / "trace-profile-result.json", trace_profile)

    direct_profile = run_json(
        agentpprof
        + common_profile_args
        + [
            "--operation-file",
            command_path(direct_operation_file),
            "-o",
            command_path(direct_operation_folded),
        ],
        "direct operation profile",
    )
    write_json(out_dir / "direct-operation-profile-result.json", direct_profile)

    chrome_profile = run_json(
        agentpprof
        + common_profile_args
        + [
            "--operation-file",
            command_path(chrome_operation_file),
            "-o",
            command_path(chrome_operation_folded),
        ],
        "Chrome operation profile",
    )
    write_json(out_dir / "chrome-operation-profile-result.json", chrome_profile)

    direct_trace_equals_direct_operations = (
        trace_folded.read_bytes() == direct_operation_folded.read_bytes()
    )
    chrome_operations_equal_direct_operations = (
        chrome_operation_folded.read_bytes() == direct_operation_folded.read_bytes()
    )
    direct_operations_equal = (
        direct_operation_file.read_bytes() == chrome_operation_file.read_bytes()
    )
    chrome_shape = chrome_trace_shape(chrome_trace_file)

    report_json = out_dir / "chrome-exchange-report.json"
    report_md = out_dir / "chrome-exchange-report.md"
    index_html = out_dir / "index.html"
    status = (
        "ok"
        if chrome_shape["valid"]
        and direct_trace_equals_direct_operations
        and chrome_operations_equal_direct_operations
        and direct_operations_equal
        else "mismatch"
    )
    report = {
        "run_id": "R306",
        "status": status,
        "session_file": relative(args.session_file),
        "agent_trace_file": relative(agent_trace_file),
        "chrome_trace_file": relative(chrome_trace_file),
        "direct_operation_file": relative(direct_operation_file),
        "chrome_operation_file": relative(chrome_operation_file),
        "trace_folded": relative(trace_folded),
        "direct_operation_folded": relative(direct_operation_folded),
        "chrome_operation_folded": relative(chrome_operation_folded),
        "report_json": relative(report_json),
        "report_markdown": relative(report_md),
        "index_html": relative(index_html),
        "standard_trace_format": "Chrome Trace Event JSON / Perfetto-compatible traceEvents",
        "stack": args.stack,
        "sessions": export_result.get("sessions", 0),
        "direct_operations": direct_convert.get("operations", 0),
        "chrome_operations": chrome_import.get("operations", 0),
        "chrome_trace": chrome_shape,
        "direct_operations_byte_identical": direct_operations_equal,
        "direct_trace_equals_direct_operations": direct_trace_equals_direct_operations,
        "chrome_operations_equal_direct_operations": chrome_operations_equal_direct_operations,
        "trace_profile": folded_stats(trace_folded),
        "direct_operation_profile": folded_stats(direct_operation_folded),
        "chrome_operation_profile": folded_stats(chrome_operation_folded),
    }
    write_json(report_json, report)
    write_markdown(report_md, report)
    write_html(index_html, report)

    print(json.dumps(report, indent=2, sort_keys=True))
    if status != "ok":
        raise SystemExit("Chrome trace exchange did not preserve operation-stack output")


if __name__ == "__main__":
    main()
