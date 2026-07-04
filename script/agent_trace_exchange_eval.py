#!/usr/bin/env python3
"""Reproduce the agent-session trace exchange bridge.

This script keeps agent-native sessions outside the profiler abstraction:
sessions export to the portable `agentsight.agent-session.trace.v1` schema,
then the trace can either be imported directly by agentpprof or converted to
operation JSONL and profiled through the same operation-stack path.
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
DEFAULT_OUT_DIR = REPO_ROOT / "docs/visexp/out/agent-trace-exchange-r303"
DEFAULT_STACK = "project,agent,op,phase,tool,status"
TRACE_SCHEMA = "agentsight.agent-session.trace.v1"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Export a local agent session to the exchange trace schema, convert it "
            "to operation JSONL, and verify both profile paths fold identically."
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


def looks_host_path(value: str) -> bool:
    lowered = value.lower()
    return (
        value.startswith("/")
        or value.startswith("~/")
        or "/home/" in lowered
        or "/users/" in lowered
        or "\\users\\" in lowered
        or "\\home\\" in lowered
        or ".codex" in lowered
        or ".claude" in lowered
    )


def trace_portability_findings(path: Path) -> list[str]:
    payload = json.loads(path.read_text())
    sessions = payload.get("sessions", []) if isinstance(payload, dict) else []
    findings: list[str] = []
    for idx, session in enumerate(sessions):
        if not isinstance(session, dict):
            continue
        raw_path = session.get("path")
        if isinstance(raw_path, str) and looks_host_path(raw_path):
            findings.append(f"sessions[{idx}].path is host-local")
        if isinstance(raw_path, str) and not raw_path.startswith("trace/"):
            findings.append(f"sessions[{idx}].path is not trace-local")
        raw_cwd = session.get("cwd")
        if isinstance(raw_cwd, str) and raw_cwd not in {"", "repo"}:
            findings.append(f"sessions[{idx}].cwd is not portable")
        files = session.get("files")
        if isinstance(files, dict):
            for file_path, value in files.items():
                _ = value
                if isinstance(file_path, str) and looks_host_path(file_path):
                    findings.append(f"sessions[{idx}].files has host-local key")
        tools = session.get("events", {}).get("tools", [])
        if isinstance(tools, list):
            for tool_idx, tool in enumerate(tools):
                if not isinstance(tool, dict):
                    continue
                command = tool.get("command")
                command_name = tool.get("command_name")
                if command_name and command_name != "none" and command != command_name:
                    findings.append(
                        f"sessions[{idx}].events.tools[{tool_idx}].command keeps raw text"
                    )
                if (
                    isinstance(command, str)
                    and (not command_name or command_name == "none")
                    and (looks_host_path(command) or " " in command.strip())
                ):
                    findings.append(
                        f"sessions[{idx}].events.tools[{tool_idx}].command is not summarized"
                    )
    return findings


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
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


def write_markdown(path: Path, report: dict[str, Any]) -> None:
    lines = [
        "# Agent Trace Exchange R303",
        "",
        "This reproducer keeps local agent sessions as an exchange format, not a profiler object.",
        "The direct trace import and converted operation JSONL import must produce byte-identical folded stacks under the same operation stack.",
        "",
        "## Result",
        "",
        f"- Trace schema: `{report['trace_schema']}`",
        f"- Sessions exported: {report['sessions']}",
        f"- Operations converted: {report['operations']}",
        f"- Trace import: {report['trace_import']['samples']} samples / {report['trace_import']['unique_stacks']} stacks",
        f"- Operation import: {report['operation_import']['samples']} samples / {report['operation_import']['unique_stacks']} stacks",
        f"- Folded outputs identical: `{report['folded_outputs_identical']}`",
        f"- Trace filesystem portable: `{report['trace_filesystem_portable']}`",
        "",
        "## Files",
        "",
    ]
    for key in [
        "trace_file",
        "operation_file",
        "trace_folded",
        "operation_folded",
        "report_json",
    ]:
        lines.append(f"- `{key}`: `{report[key]}`")
    path.write_text("\n".join(lines) + "\n")


def write_html(path: Path, report: dict[str, Any]) -> None:
    status = "pass" if report["folded_outputs_identical"] else "fail"
    rows = [
        ("Trace schema", report["trace_schema"]),
        ("Sessions", report["sessions"]),
        ("Operations", report["operations"]),
        (
            "Trace import",
            f"{report['trace_import']['samples']} samples / {report['trace_import']['unique_stacks']} stacks",
        ),
        (
            "Operation import",
            f"{report['operation_import']['samples']} samples / {report['operation_import']['unique_stacks']} stacks",
        ),
        ("Folded equality", status),
        (
            "Trace filesystem portability",
            "pass" if report["trace_filesystem_portable"] else "fail",
        ),
    ]
    body = "\n".join(
        f"<tr><th>{html.escape(str(key))}</th><td>{html.escape(str(value))}</td></tr>"
        for key, value in rows
    )
    path.write_text(
        """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Agent Trace Exchange R303</title>
  <style>
    body { font-family: system-ui, sans-serif; margin: 2rem; color: #1f2933; }
    h1 { font-size: 1.6rem; margin-bottom: 0.25rem; }
    p { max-width: 760px; line-height: 1.5; }
    table { border-collapse: collapse; margin-top: 1.5rem; min-width: 520px; }
    th, td { border: 1px solid #d8dee9; padding: 0.55rem 0.75rem; text-align: left; }
    th { background: #f6f8fa; width: 190px; }
    .pass { color: #176f3d; font-weight: 700; }
    .fail { color: #a61b1b; font-weight: 700; }
    code { background: #f6f8fa; padding: 0.1rem 0.25rem; border-radius: 4px; }
  </style>
</head>
<body>
  <h1>Agent Trace Exchange R303</h1>
  <p>
    A local agent session exports to <code>agentsight.agent-session.trace.v1</code>,
    converts to operation JSONL, and then both paths are profiled with the same
    operation stack. This validates exchange and conversion without adding a
    third profiler abstraction.
  </p>
  <table>
"""
        + body
        + f"""
  </table>
  <p class="{status}">Folded-output equality: {status}</p>
</body>
</html>
"""
    )


def main() -> None:
    args = parse_args()
    out_dir = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    trace_file = out_dir / "fixture-trace.json"
    operation_file = out_dir / "fixture-operations.jsonl"
    trace_folded = out_dir / "trace-import.folded"
    operation_folded = out_dir / "operation-import.folded"

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
            command_path(trace_file),
        ],
        "trace export",
    )
    write_json(out_dir / "export-result.json", export_result)
    portability_findings = trace_portability_findings(trace_file)

    convert_result = run_json(
        [
            "python3",
            "script/agent_trace_to_operations.py",
            "--trace-file",
            command_path(trace_file),
            "--project-name",
            args.project_name,
            "--out",
            command_path(operation_file),
        ],
        "trace to operations",
    )
    write_json(out_dir / "trace-to-operations-result.json", convert_result)

    trace_import = run_json(
        agentpprof
        + common_profile_args
        + ["--trace-file", command_path(trace_file), "-o", command_path(trace_folded)],
        "trace import",
    )
    write_json(out_dir / "trace-import-result.json", trace_import)

    operation_import = run_json(
        agentpprof
        + common_profile_args
        + ["--operation-file", command_path(operation_file), "-o", command_path(operation_folded)],
        "operation import",
    )
    write_json(out_dir / "operation-import-result.json", operation_import)

    folded_outputs_identical = trace_folded.read_bytes() == operation_folded.read_bytes()
    report_json = out_dir / "exchange-report.json"
    report_md = out_dir / "exchange-report.md"
    index_html = out_dir / "index.html"
    report = {
        "run_id": "R303",
        "status": "ok" if folded_outputs_identical else "mismatch",
        "trace_schema": export_result.get("trace_schema", TRACE_SCHEMA),
        "session_file": relative(args.session_file),
        "trace_file": relative(trace_file),
        "operation_file": relative(operation_file),
        "trace_folded": relative(trace_folded),
        "operation_folded": relative(operation_folded),
        "report_json": relative(report_json),
        "report_markdown": relative(report_md),
        "index_html": relative(index_html),
        "sessions": export_result.get("sessions", 0),
        "operations": convert_result.get("operations", 0),
        "stack": args.stack,
        "trace_portability_scope": "filesystem fields and tool command text",
        "trace_filesystem_portable": not portability_findings,
        "trace_portability_findings": portability_findings,
        "folded_outputs_identical": folded_outputs_identical,
        "trace_import": {
            "samples": trace_import.get("samples", 0),
            "unique_stacks": trace_import.get("unique_stacks", 0),
        },
        "operation_import": {
            "samples": operation_import.get("samples", 0),
            "unique_stacks": operation_import.get("unique_stacks", 0),
        },
    }
    write_json(report_json, report)
    write_markdown(report_md, report)
    write_html(index_html, report)

    print(json.dumps(report, indent=2, sort_keys=True))
    if portability_findings:
        raise SystemExit("trace export is not portable: " + "; ".join(portability_findings))
    if not folded_outputs_identical:
        raise SystemExit("trace import and operation import folded outputs differ")


if __name__ == "__main__":
    main()
