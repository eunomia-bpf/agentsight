#!/usr/bin/env python3
"""Regression guard for command-root lineage joins.

R238 introduced a narrow `command_root_pid_self_time_window` fallback for the
record-command root process. This script proves, on a synthetic snapshot, that
the fallback joins only the root process itself and does not join sibling or
child processes merely because they share the same root PID.
"""

from __future__ import annotations

import argparse
import csv
import json
import subprocess
from collections import Counter
from datetime import date
from pathlib import Path
from typing import Any

import effect_lineage_smoke as lineage


RUN_ID = "R240"


def git_commit() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except Exception:
        return "unknown"


def git_dirty() -> bool | None:
    try:
        return bool(
            subprocess.check_output(
                ["git", "status", "--porcelain"],
                text=True,
                stderr=subprocess.DEVNULL,
            ).strip()
        )
    except Exception:
        return None


def synthetic_snapshot() -> dict[str, Any]:
    return {
        "project": "agentsight",
        "sessions": [
            {
                "id": "session-r240",
                "agent_type": "codex",
                "start_timestamp_ms": 900,
                "end_timestamp_ms": 2100,
                "attributes": {"session_tag": "record"},
            }
        ],
        "tool_calls": [
            {
                "id": "tool-r240",
                "tool_call_id": "tool-r240",
                "session_id": "session-r240",
                "tool_name": "shell",
                "timestamp_ms": 1000,
                "start_timestamp_ms": 1000,
                "end_timestamp_ms": 2000,
                "related_pid": 200,
                "input": {
                    "prompt_tag": "record",
                    "command_root_pid": 100,
                    "related_pid": 200,
                },
            }
        ],
        "process_nodes": [
            {
                "id": "proc-root",
                "pid": 100,
                "ppid": 1,
                "root_pid": 100,
                "comm": "python3",
                "start_timestamp_ms": 900,
                "end_timestamp_ms": 2100,
            },
            {
                "id": "proc-agent",
                "pid": 200,
                "ppid": 100,
                "root_pid": 100,
                "comm": "codex",
                "start_timestamp_ms": 950,
                "end_timestamp_ms": 2100,
            },
            {
                "id": "proc-agent-child",
                "pid": 201,
                "ppid": 200,
                "root_pid": 100,
                "comm": "python3",
                "start_timestamp_ms": 1100,
                "end_timestamp_ms": 1900,
            },
            {
                "id": "proc-sibling",
                "pid": 300,
                "ppid": 100,
                "root_pid": 100,
                "comm": "python3",
                "start_timestamp_ms": 1100,
                "end_timestamp_ms": 1900,
            },
        ],
        "audit_events": [
            {
                "id": "evt-root-self",
                "audit_type": "network",
                "action": "NET_CONNECT",
                "pid": 100,
                "timestamp_ms": 1200,
                "target": "127.0.0.1:10001",
                "status": "ok",
            },
            {
                "id": "evt-related-agent",
                "audit_type": "network",
                "action": "NET_CONNECT",
                "pid": 200,
                "timestamp_ms": 1300,
                "target": "127.0.0.1:10002",
                "status": "ok",
            },
            {
                "id": "evt-related-child",
                "audit_type": "network",
                "action": "NET_CONNECT",
                "pid": 201,
                "timestamp_ms": 1400,
                "target": "127.0.0.1:10003",
                "status": "ok",
            },
            {
                "id": "evt-sibling-negative",
                "audit_type": "network",
                "action": "NET_CONNECT",
                "pid": 300,
                "timestamp_ms": 1500,
                "target": "127.0.0.1:10004",
                "status": "ok",
            },
            {
                "id": "evt-root-outside-window",
                "audit_type": "network",
                "action": "NET_CONNECT",
                "pid": 100,
                "timestamp_ms": 3000,
                "target": "127.0.0.1:10005",
                "status": "ok",
            },
        ],
    }


def write_rows(path: Path, rows: list[dict[str, Any]]) -> None:
    fields = [
        "event_id",
        "pid",
        "process_id",
        "tool_id",
        "join_method",
        "orphan_reason",
        "joined",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field) for field in fields})


def assert_regression(rows: list[dict[str, Any]]) -> dict[str, Any]:
    by_event = {row["event_id"]: row for row in rows}
    checks = {
        "root_self_joined_by_command_root": by_event["evt-root-self"]["join_method"]
        == "command_root_pid_self_time_window"
        and by_event["evt-root-self"]["joined"],
        "related_agent_joined_by_pid_family": by_event["evt-related-agent"]["join_method"]
        == "pid_family_time_window"
        and by_event["evt-related-agent"]["joined"],
        "related_child_joined_by_pid_family": by_event["evt-related-child"]["join_method"]
        == "pid_family_time_window"
        and by_event["evt-related-child"]["joined"],
        "sibling_not_joined_by_command_root": not by_event["evt-sibling-negative"]["joined"]
        and by_event["evt-sibling-negative"]["join_method"] == "none",
        "outside_window_not_joined": not by_event["evt-root-outside-window"]["joined"]
        and by_event["evt-root-outside-window"]["join_method"] == "none",
    }
    return checks


def write_markdown(path: Path, result: dict[str, Any]) -> None:
    validation_lines = []
    for item in result["external_regression_tests"]:
        validation_lines.append(
            f"- `{item['command']}`: {item['status']} ({item['scope']})."
        )
    lines = [
        "# R240 Lineage Guard Regression",
        "",
        f"Last updated: {date.today().isoformat()}",
        "Stage at update: supplement / regression",
        "Source/command: `python3 docs/visexp/r240_lineage_guard_regression.py`",
        f"Completeness: {result['status']}",
        "",
        "## Result",
        "",
        f"- Events checked: {result['events_checked']}.",
        f"- Joined events: {result['joined_events']}.",
        f"- Orphan events: {result['orphan_events']}.",
        f"- Join methods: {result['join_methods']}.",
        f"- Orphan reasons: {result['orphan_reasons']}.",
        "",
        "## External Regression Tests",
        "",
        *validation_lines,
        "",
        "## Boundary",
        "",
        "This is checker-regression evidence. It proves the command-root fallback",
        "does not join a sibling process that merely shares the same root PID, and",
        "that root self events still join only inside the tool time window. It does",
        "not prove live agent-launched target-network coverage. The external test",
        "commands are regression checks only; they are not C5/C6 outcome evidence.",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run(args: argparse.Namespace) -> dict[str, Any]:
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    snapshot = synthetic_snapshot()
    rows, orphans, folded = lineage.lineage_rows(snapshot)
    checks = assert_regression(rows)
    status = "passed" if all(checks.values()) else "failed"
    result = {
        "schema_version": 1,
        "run_id": RUN_ID,
        "generated_at": date.today().isoformat(),
        "commit": git_commit(),
        "working_tree_dirty": git_dirty(),
        "status": status,
        "events_checked": len(rows),
        "joined_events": sum(1 for row in rows if row.get("joined")),
        "orphan_events": len(orphans),
        "folded_stack_count": len(folded),
        "join_methods": dict(Counter(row["join_method"] for row in rows)),
        "orphan_reasons": dict(Counter(row["orphan_reason"] for row in orphans)),
        "checks": checks,
        "external_regression_tests": [
            {
                "command": "make -C bpf test",
                "status": args.bpf_test_status,
                "scope": "BPF process runtime tests, including target-child network summary capture",
            },
            {
                "command": "cd collector && cargo test wait_for_process_runner_start",
                "status": args.rust_test_status,
                "scope": "Rust process-tracer readiness wait unit tests",
            },
        ],
        "claim_boundary": (
            "checker-regression evidence for command_root_pid_self_time_window; "
            "not live capture or broad target-network support"
        ),
    }
    (out_dir / "lineage-guard-r240-snapshot.json").write_text(
        json.dumps(snapshot, indent=2), encoding="utf-8"
    )
    (out_dir / "lineage-guard-r240.json").write_text(
        json.dumps(result, indent=2), encoding="utf-8"
    )
    write_rows(out_dir / "lineage-guard-r240-rows.csv", rows)
    write_markdown(out_dir / "lineage-guard-r240.md", result)
    print(json.dumps(result, indent=2))
    if status != "passed":
        raise SystemExit(1)
    return result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--out-dir",
        default="docs/visexp/out/lineage-guard-r240",
        help="directory for R240 artifacts",
    )
    parser.add_argument(
        "--bpf-test-status",
        choices=("not_run_by_script", "passed", "failed"),
        default="not_run_by_script",
        help="recorded status for the external BPF runtime regression command",
    )
    parser.add_argument(
        "--rust-test-status",
        choices=("not_run_by_script", "passed", "failed"),
        default="not_run_by_script",
        help="recorded status for the external Rust readiness regression command",
    )
    return parser


if __name__ == "__main__":
    run(build_parser().parse_args())
