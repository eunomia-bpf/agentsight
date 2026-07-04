#!/usr/bin/env python3
"""Convert agent-session traces to and from Chrome/Perfetto trace JSON.

The Chrome Trace Event file is an exchange format. Importing a trace produces
AgentSight operation JSONL, so downstream profiling still uses only operations
and operation stacks.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import agent_trace_to_operations as trace_ops  # noqa: E402


CHROME_TRACE_FORMAT = "chrome-trace-event-json"
AGENTSIGHT_OPERATION_SCHEMA = "agentsight.operation.v1"
GENERIC_ARG_FIELDS = {
    "action",
    "agent",
    "category",
    "cmd",
    "command",
    "dataset",
    "domain",
    "effect",
    "model",
    "op",
    "operation",
    "path",
    "phase",
    "process",
    "project",
    "session",
    "session_id",
    "status",
    "target",
    "task",
    "tool",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Export portable agent-session traces as Chrome/Perfetto trace JSON, "
            "or import Chrome/Perfetto trace JSON as AgentSight operation JSONL."
        )
    )
    subcommands = parser.add_subparsers(dest="command", required=True)

    export_parser = subcommands.add_parser(
        "export",
        help="Convert agentsight.agent-session.trace.v1 JSON to Chrome Trace Event JSON.",
    )
    export_parser.add_argument("--trace-file", action="append", type=Path, required=True)
    export_parser.add_argument("--out", type=Path, required=True)
    export_parser.add_argument("--project-name", default="agent-session-trace")
    export_parser.add_argument(
        "--include-previews",
        action="store_true",
        help="Include prompt/LLM previews in exported operation args.",
    )

    import_parser = subcommands.add_parser(
        "import",
        help="Convert Chrome Trace Event JSON to AgentSight operation JSONL.",
    )
    import_parser.add_argument("--trace-file", action="append", type=Path, required=True)
    import_parser.add_argument("--out", type=Path, required=True)
    import_parser.add_argument("--project-name", default="standard-trace")
    import_parser.add_argument(
        "--include-args",
        action="store_true",
        help="Copy non-AgentSight event args into operation fields.",
    )
    return parser.parse_args()


def stable_int(value: str, modulo: int = 2_147_483_647) -> int:
    digest = hashlib.sha256(value.encode("utf-8", errors="replace")).hexdigest()
    return int(digest[:12], 16) % modulo


def write_json(path: Path, payload: Any) -> None:
    if path.parent and str(path.parent) != ".":
        path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> int:
    if path.parent and str(path.parent) != ".":
        path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with path.open("w", encoding="utf-8") as out:
        for row in rows:
            out.write(json.dumps(row, sort_keys=True) + "\n")
            count += 1
    return count


def parse_int(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def operation_value(raw: Any) -> int:
    value = parse_int(raw)
    if value is None or value <= 0:
        return 1
    return value


def event_name(fields: dict[str, Any]) -> str:
    op = str(fields.get("op") or "operation")
    for key in ("phase", "tool", "model", "action", "status"):
        value = fields.get(key)
        if isinstance(value, str) and value:
            return f"{op}:{value}"
    return op


def first_int(*values: Any) -> int | None:
    for value in values:
        parsed = parse_int(value)
        if parsed is not None:
            return parsed
    return None


def collect_agent_operation_records(
    trace_files: list[Path],
    project_name: str,
    include_previews: bool,
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for trace_file in trace_files:
        for session in trace_ops.load_sessions(trace_file):
            session_key = str(
                session.get("session_id")
                or session.get("display_id")
                or session.get("path")
                or trace_file
            )
            pid = stable_int(session_key)
            session_start_ms = first_int(
                session.get("start_timestamp_ms"), session.get("updated")
            )
            for sequence, event in enumerate(
                trace_ops.operation_events_for_session(
                    session, project_name, include_previews
                )
            ):
                operation = event["operation"]
                fields = operation.get("fields", {})
                prompt_index = parse_int(fields.get("prompt_index")) or 0
                records.append(
                    {
                        "operation": operation,
                        "ts_ms": first_int(event.get("ts_ms"), session_start_ms),
                        "sequence": len(records) + sequence,
                        "pid": pid,
                        "tid": prompt_index,
                        "session": session_key,
                    }
                )
    return records


def trace_timestamp_us(record: dict[str, Any], base_ms: int | None, index: int) -> int:
    ts_ms = parse_int(record.get("ts_ms"))
    if ts_ms is not None and base_ms is not None:
        return max(0, ts_ms - base_ms) * 1000 + index
    return index * 1000


def chrome_payload_from_agent_trace_files(
    trace_files: list[Path],
    project_name: str,
    include_previews: bool = False,
) -> dict[str, Any]:
    records = collect_agent_operation_records(trace_files, project_name, include_previews)
    base_ms_values = [parse_int(record.get("ts_ms")) for record in records]
    base_ms_candidates = [value for value in base_ms_values if value is not None]
    base_ms = min(base_ms_candidates) if base_ms_candidates else None

    events: list[dict[str, Any]] = []
    for index, record in enumerate(records):
        operation = record["operation"]
        fields = operation.get("fields", {})
        events.append(
            {
                "name": event_name(fields),
                "cat": str(fields.get("op") or "operation"),
                "ph": "X",
                "ts": trace_timestamp_us(record, base_ms, index),
                "dur": 1,
                "pid": record["pid"],
                "tid": record["tid"],
                "args": {
                    "agentsight.schema": AGENTSIGHT_OPERATION_SCHEMA,
                    "agentsight.value": operation_value(operation.get("value")),
                    "agentsight.operation": fields,
                },
            }
        )

    return {
        "displayTimeUnit": "ms",
        "metadata": {
            "format": CHROME_TRACE_FORMAT,
            "source_schema": trace_ops.TRACE_SCHEMA,
            "operation_schema": AGENTSIGHT_OPERATION_SCHEMA,
            "project": project_name,
        },
        "traceEvents": events,
    }


def load_chrome_trace_events(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, dict):
        events = payload.get("traceEvents")
    else:
        events = payload
    if not isinstance(events, list):
        raise SystemExit(f"Chrome trace {path} must be a list or contain traceEvents")
    if not all(isinstance(event, dict) for event in events):
        raise SystemExit(f"Chrome trace {path} contains non-object events")
    return events


def split_categories(value: Any) -> list[str]:
    if not isinstance(value, str):
        return []
    return [
        part.strip()
        for chunk in value.split(",")
        for part in chunk.split(";")
        if part.strip()
    ]


def normalize_label(value: Any, fallback: str) -> str:
    if isinstance(value, str) and value.strip():
        return value.strip().replace(" ", "_")
    return fallback


def is_operation_arg(value: Any) -> bool:
    return isinstance(value, (str, int, float, bool, list, dict)) or value is None


def maybe_copy_trace_args(
    fields: dict[str, Any],
    args: dict[str, Any],
    include_args: bool,
) -> None:
    allowed = set(GENERIC_ARG_FIELDS)
    if include_args:
        allowed.update(key for key in args.keys() if not str(key).startswith("agentsight."))
    for key, value in args.items():
        if key.startswith("agentsight.") or key not in allowed or key in fields:
            continue
        if is_operation_arg(value):
            fields[key] = value


def operation_from_chrome_event(
    event: dict[str, Any],
    project_name: str,
    include_args: bool = False,
) -> dict[str, Any] | None:
    phase = event.get("ph")
    if phase not in {"X", "I", "i"}:
        return None
    args = event.get("args")
    args = args if isinstance(args, dict) else {}
    operation_fields = args.get("agentsight.operation")
    if isinstance(operation_fields, dict):
        fields = trace_ops.clean_fields(dict(operation_fields))
        return {
            "value": operation_value(args.get("agentsight.value")),
            "fields": fields,
        }

    categories = split_categories(event.get("cat"))
    raw_name = str(event.get("name") or "event")
    raw_op = args.get("op") or args.get("operation") or (categories[0] if categories else raw_name)
    op = normalize_label(raw_op, "event")
    raw_phase = args.get("phase") or (categories[1] if len(categories) > 1 else op)
    session = str(
        args.get("session")
        or args.get("session_id")
        or f"pid:{event.get('pid', 'unknown')}"
    )
    dur_us = parse_int(event.get("dur")) or 0
    fields: dict[str, Any] = {
        "project": args.get("project") or project_name,
        "agent": args.get("agent") or "standard-trace",
        "session": session,
        "session_id": args.get("session_id") or session,
        "op": op,
        "phase": normalize_label(raw_phase, op),
        "status": args.get("status") or "observed",
        "trace_name": raw_name,
        "trace_cat": event.get("cat", ""),
        "trace_pid": event.get("pid", ""),
        "trace_tid": event.get("tid", ""),
        "trace_ts_us": parse_int(event.get("ts")) or 0,
        "trace_dur_us": max(dur_us, 0),
    }
    maybe_copy_trace_args(fields, args, include_args)
    return {"value": 1, "fields": trace_ops.clean_fields(fields)}


def complete_events_in_trace_order(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    stacks: dict[tuple[Any, Any, str, str], list[dict[str, Any]]] = defaultdict(list)
    completed: list[dict[str, Any]] = []
    for event in events:
        phase = event.get("ph")
        if phase in {"X", "I", "i"}:
            completed.append(event)
            continue
        key = (
            event.get("pid"),
            event.get("tid"),
            str(event.get("name") or ""),
            str(event.get("cat") or ""),
        )
        if phase == "B":
            stacks[key].append(event)
            continue
        if phase != "E" or not stacks[key]:
            continue
        begin = stacks[key].pop()
        begin_ts = parse_int(begin.get("ts")) or 0
        end_ts = parse_int(event.get("ts")) or begin_ts
        begin_args = begin.get("args") if isinstance(begin.get("args"), dict) else {}
        end_args = event.get("args") if isinstance(event.get("args"), dict) else {}
        completed.append(
            {
                "name": begin.get("name", event.get("name", "event")),
                "cat": begin.get("cat", event.get("cat", "")),
                "ph": "X",
                "ts": begin_ts,
                "dur": max(0, end_ts - begin_ts),
                "pid": begin.get("pid", event.get("pid", "")),
                "tid": begin.get("tid", event.get("tid", "")),
                "args": {**begin_args, **end_args},
            }
        )
    return completed


def operations_from_chrome_trace_payload(
    payload: dict[str, Any] | list[Any],
    project_name: str,
    include_args: bool = False,
) -> list[dict[str, Any]]:
    if isinstance(payload, dict):
        raw_events = payload.get("traceEvents", [])
    else:
        raw_events = payload
    events = [event for event in raw_events if isinstance(event, dict)]
    complete_events = complete_events_in_trace_order(events)
    rows = [
        operation
        for event in complete_events
        if (
            operation := operation_from_chrome_event(
                event, project_name, include_args=include_args
            )
        )
        is not None
    ]
    return rows


def operations_from_chrome_trace_files(
    trace_files: list[Path],
    project_name: str,
    include_args: bool = False,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in trace_files:
        payload = json.loads(path.read_text(encoding="utf-8"))
        rows.extend(
            operations_from_chrome_trace_payload(
                payload, project_name, include_args=include_args
            )
        )
    return rows


def export_command(args: argparse.Namespace) -> None:
    payload = chrome_payload_from_agent_trace_files(
        args.trace_file,
        args.project_name,
        include_previews=args.include_previews,
    )
    if not payload["traceEvents"]:
        raise SystemExit("agent-session trace produced zero Chrome trace events")
    write_json(args.out, payload)
    print(
        json.dumps(
            {
                "status": "ok",
                "format": CHROME_TRACE_FORMAT,
                "trace_files": [str(path) for path in args.trace_file],
                "output": str(args.out),
                "events": len(payload["traceEvents"]),
            },
            indent=2,
            sort_keys=True,
        )
    )


def import_command(args: argparse.Namespace) -> None:
    rows = operations_from_chrome_trace_files(
        args.trace_file,
        args.project_name,
        include_args=args.include_args,
    )
    if not rows:
        raise SystemExit("Chrome trace produced zero operations")
    count = write_jsonl(args.out, rows)
    print(
        json.dumps(
            {
                "status": "ok",
                "format": CHROME_TRACE_FORMAT,
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
    if args.command == "export":
        export_command(args)
    elif args.command == "import":
        import_command(args)
    else:
        raise SystemExit(f"unsupported command {args.command}")


if __name__ == "__main__":
    main()
