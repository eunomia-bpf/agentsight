#!/usr/bin/env python3
"""Unified trace conversion entrypoint for agent-session and standard traces.

The conversion boundary is intentionally outside the profiler model:
agent-session traces and Chrome/Perfetto trace files are exchange containers,
while AgentSight profiling consumes operation JSONL and folds operation stacks.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Iterable


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import agent_trace_chrome_trace as chrome_trace  # noqa: E402
import agent_trace_to_operations as trace_ops  # noqa: E402


SUPPORTED_STANDARD_FORMATS = {"chrome"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Convert parsed agent-session traces to standard trace containers, "
            "or import standard trace containers as AgentSight operation JSONL."
        )
    )
    subcommands = parser.add_subparsers(dest="command", required=True)

    export_standard = subcommands.add_parser(
        "export-standard",
        help="Export agentsight.agent-session.trace.v1 JSON as a standard trace file.",
    )
    add_standard_format_arg(export_standard)
    export_standard.add_argument(
        "--trace-file",
        action="append",
        type=Path,
        required=True,
        help="Input agentsight.agent-session.trace.v1 JSON file.",
    )
    export_standard.add_argument("--out", type=Path, required=True)
    export_standard.add_argument("--project-name", default="agent-session-trace")
    export_standard.add_argument(
        "--include-previews",
        action="store_true",
        help="Include prompt/LLM previews in exported standard trace args.",
    )

    import_standard = subcommands.add_parser(
        "import-standard",
        help="Import a standard trace file as AgentSight operation JSONL.",
    )
    add_standard_format_arg(import_standard)
    import_standard.add_argument(
        "--trace-file",
        action="append",
        type=Path,
        required=True,
        help="Input standard trace file.",
    )
    import_standard.add_argument("--out", type=Path, required=True)
    import_standard.add_argument("--project-name", default="standard-trace")
    import_standard.add_argument(
        "--include-args",
        action="store_true",
        help="Copy non-AgentSight Chrome event args into operation fields.",
    )

    to_operations = subcommands.add_parser(
        "to-operations",
        help="Convert agentsight.agent-session.trace.v1 JSON directly to operation JSONL.",
    )
    to_operations.add_argument(
        "--trace-file",
        action="append",
        type=Path,
        required=True,
        help="Input agentsight.agent-session.trace.v1 JSON file.",
    )
    to_operations.add_argument("--out", type=Path, required=True)
    to_operations.add_argument("--project-name", default="agent-session-trace")
    to_operations.add_argument(
        "--include-previews",
        action="store_true",
        help="Include prompt/LLM previews in operation fields.",
    )
    return parser.parse_args()


def add_standard_format_arg(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--format",
        default="chrome",
        choices=sorted(SUPPORTED_STANDARD_FORMATS),
        help="Standard trace container format. Currently supports Chrome/Perfetto Trace Event JSON.",
    )


def write_json(path: Path, payload: Any) -> None:
    if path.parent and str(path.parent) != ".":
        path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> int:
    if path.parent and str(path.parent) != ".":
        path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with path.open("w", encoding="utf-8") as out:
        for row in rows:
            out.write(json.dumps(row, sort_keys=True) + "\n")
            count += 1
    return count


def agent_trace_operations(
    trace_files: list[Path],
    project_name: str,
    include_previews: bool,
) -> list[dict[str, Any]]:
    operations: list[dict[str, Any]] = []
    for trace_file in trace_files:
        for session in trace_ops.load_sessions(trace_file):
            operations.extend(
                trace_ops.operations_for_session(session, project_name, include_previews)
            )
    return operations


def export_standard_command(args: argparse.Namespace) -> None:
    payload = chrome_trace.chrome_payload_from_agent_trace_files(
        args.trace_file,
        args.project_name,
        include_previews=args.include_previews,
    )
    events = payload.get("traceEvents", [])
    if not events:
        raise SystemExit("agent-session trace produced zero standard trace events")
    write_json(args.out, payload)
    print(
        json.dumps(
            {
                "status": "ok",
                "format": chrome_trace.CHROME_TRACE_FORMAT,
                "format_alias": args.format,
                "trace_files": [str(path) for path in args.trace_file],
                "output": str(args.out),
                "events": len(events),
            },
            indent=2,
            sort_keys=True,
        )
    )


def import_standard_command(args: argparse.Namespace) -> None:
    rows = chrome_trace.operations_from_chrome_trace_files(
        args.trace_file,
        args.project_name,
        include_args=args.include_args,
    )
    if not rows:
        raise SystemExit("standard trace produced zero operations")
    count = write_jsonl(args.out, rows)
    print(
        json.dumps(
            {
                "status": "ok",
                "format": chrome_trace.CHROME_TRACE_FORMAT,
                "format_alias": args.format,
                "trace_files": [str(path) for path in args.trace_file],
                "output": str(args.out),
                "operations": count,
            },
            indent=2,
            sort_keys=True,
        )
    )


def to_operations_command(args: argparse.Namespace) -> None:
    operations = agent_trace_operations(
        args.trace_file,
        args.project_name,
        include_previews=args.include_previews,
    )
    if not operations:
        raise SystemExit("agent-session trace produced zero operations")
    count = write_jsonl(args.out, operations)
    print(
        json.dumps(
            {
                "status": "ok",
                "trace_files": [str(path) for path in args.trace_file],
                "output": str(args.out),
                "operations": count,
            },
            indent=2,
            sort_keys=True,
        )
    )


def main() -> None:
    args = parse_args()
    if args.command == "export-standard":
        export_standard_command(args)
    elif args.command == "import-standard":
        import_standard_command(args)
    elif args.command == "to-operations":
        to_operations_command(args)
    else:
        raise SystemExit(f"unsupported command {args.command}")


if __name__ == "__main__":
    main()
