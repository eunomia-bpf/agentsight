#!/usr/bin/env python3
"""Validate exact-effect lineage invariants on an AgentSight snapshot.

This smoke test uses the collector materialized-view shape:
sessions, tool_calls, process_nodes, and audit_events. It proves the checker and
stack grammar are executable. A fixture run does not prove live exact-effect
capture over real agent sessions.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter, defaultdict, deque
from pathlib import Path
from typing import Any


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def safe_frame(text: str, prefix: str | None = None) -> str:
    value = re.sub(r"[^a-zA-Z0-9._:/+-]+", "_", str(text or "unknown").lower()).strip("_;")
    value = value or "unknown"
    return f"{prefix}:{value}" if prefix else value


def target_group(row: dict[str, Any]) -> str:
    target = str(row.get("target") or row.get("summary") or "none")
    if row.get("audit_type") == "network":
        return target.split("/", 1)[0]
    target = target.strip("'\"")
    if target.startswith("/"):
        parts = [part for part in target.split("/") if part]
    else:
        parts = [part for part in target.split("/") if part]
    if parts[:1] in (["collector"], ["docs"], ["frontend"], ["bpf"]):
        return "/".join(parts[:3])
    if len(parts) >= 2:
        return "/".join(parts[:2])
    return target[:80] or "none"


def effect_name(row: dict[str, Any]) -> str:
    audit_type = str(row.get("audit_type") or "effect")
    action = str(row.get("action") or "observed")
    return f"{audit_type}.{action}"


def row_time(row: dict[str, Any]) -> int:
    return int(row.get("timestamp_ms") or row.get("start_timestamp_ms") or 0)


def process_time_contains(process: dict[str, Any], timestamp_ms: int) -> bool:
    start = process.get("start_timestamp_ms")
    end = process.get("end_timestamp_ms")
    if start is not None and timestamp_ms < int(start):
        return False
    if end is not None and timestamp_ms > int(end):
        return False
    return True


def tool_time_contains(tool: dict[str, Any], timestamp_ms: int) -> bool:
    start = tool.get("start_timestamp_ms") or tool.get("timestamp_ms")
    end = tool.get("end_timestamp_ms")
    if start is not None and timestamp_ms < int(start):
        return False
    if end is not None and timestamp_ms > int(end):
        return False
    return True


def process_key(process: dict[str, Any]) -> str:
    if process.get("id"):
        return str(process["id"])
    return "|".join(
        [
            f"pid={process.get('pid')}",
            f"start={process.get('start_timestamp_ms')}",
            f"end={process.get('end_timestamp_ms')}",
            f"comm={process.get('comm') or process.get('command') or ''}",
        ]
    )


def process_intervals_overlap(left: dict[str, Any], right: dict[str, Any]) -> bool:
    left_start = left.get("start_timestamp_ms")
    left_end = left.get("end_timestamp_ms")
    right_start = right.get("start_timestamp_ms")
    right_end = right.get("end_timestamp_ms")
    if left_end is not None and right_start is not None and int(left_end) < int(right_start):
        return False
    if right_end is not None and left_start is not None and int(right_end) < int(left_start):
        return False
    return True


def process_tool_overlaps(process: dict[str, Any], tool: dict[str, Any]) -> bool:
    tool_interval = {
        "start_timestamp_ms": tool.get("start_timestamp_ms") or tool.get("timestamp_ms"),
        "end_timestamp_ms": tool.get("end_timestamp_ms"),
    }
    return process_intervals_overlap(process, tool_interval)


def process_for_event(event: dict[str, Any], processes_by_pid: dict[int, list[dict[str, Any]]]) -> dict[str, Any] | None:
    pid = event.get("pid")
    if pid is None:
        return None
    candidates = processes_by_pid.get(int(pid), [])
    timestamp = row_time(event)
    for process in candidates:
        if process_time_contains(process, timestamp):
            return process
    return None


def related_process_keys_for_tool(tool: dict[str, Any], indexes: dict[str, Any]) -> set[str]:
    direct_keys = indexes["tool_related_process_keys"].get(str(tool.get("id")), set())
    if direct_keys:
        return set(direct_keys)
    related_pid = tool.get("related_pid")
    if related_pid is None:
        return set()
    candidates = indexes["processes_by_pid"].get(int(related_pid), [])
    tool_anchor = tool.get("start_timestamp_ms") or tool.get("timestamp_ms")
    if tool_anchor is not None:
        anchored = [
            process
            for process in candidates
            if process_time_contains(process, int(tool_anchor))
        ]
        if anchored:
            return {process_key(process) for process in anchored}
    return {
        process_key(process)
        for process in candidates
        if process_tool_overlaps(process, tool)
    }


def child_belongs_to_parent(child: dict[str, Any], parent: dict[str, Any]) -> bool:
    if child.get("ppid") is None or parent.get("pid") is None:
        return False
    if int(child["ppid"]) != int(parent["pid"]):
        return False
    if not process_intervals_overlap(parent, child):
        return False
    child_start = child.get("start_timestamp_ms")
    if child_start is not None:
        return process_time_contains(parent, int(child_start))
    return True


def descendants_by_process(process_nodes: list[dict[str, Any]]) -> dict[str, set[str]]:
    children: dict[str, list[str]] = defaultdict(list)
    for child in process_nodes:
        for parent in process_nodes:
            if child is parent:
                continue
            if child_belongs_to_parent(child, parent):
                children[process_key(parent)].append(process_key(child))
    out: dict[str, set[str]] = {}
    for root in process_nodes:
        root_key = process_key(root)
        seen = {root_key}
        queue = deque(children.get(root_key, []))
        while queue:
            child_key = queue.popleft()
            if child_key in seen:
                continue
            seen.add(child_key)
            queue.extend(children.get(child_key, []))
        out[root_key] = seen
    return out


def tool_prompt_tag(tool: dict[str, Any]) -> str:
    input_json = tool.get("input") or {}
    if isinstance(input_json, str):
        try:
            input_json = json.loads(input_json)
        except json.JSONDecodeError:
            input_json = {}
    if isinstance(input_json, dict):
        for key in ("prompt_tag", "semantic_prompt", "task_tag"):
            if input_json.get(key):
                return str(input_json[key])
    return "unknown"


def session_tag(session: dict[str, Any]) -> str:
    attrs = session.get("attributes") or {}
    if isinstance(attrs, str):
        try:
            attrs = json.loads(attrs)
        except json.JSONDecodeError:
            attrs = {}
    if isinstance(attrs, dict):
        for key in ("session_tag", "semantic_session", "task_tag"):
            if attrs.get(key):
                return str(attrs[key])
    return str(session.get("agent_type") or "session")


def build_indexes(snapshot: dict[str, Any]) -> dict[str, Any]:
    process_nodes = list(snapshot.get("process_nodes") or [])
    tool_calls = list(snapshot.get("tool_calls") or [])
    sessions = list(snapshot.get("sessions") or [])
    processes_by_pid: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for process in process_nodes:
        if process.get("pid") is not None:
            processes_by_pid[int(process["pid"])].append(process)
    tools_by_key: dict[str, dict[str, Any]] = {}
    for tool in tool_calls:
        for key in (tool.get("id"), tool.get("tool_call_id")):
            if key:
                tools_by_key[str(key)] = tool
    audit_events_by_id = {
        str(event["id"]): event
        for event in snapshot.get("audit_events") or []
        if event.get("id")
    }
    tool_related_process_keys: dict[str, set[str]] = defaultdict(set)
    for tool in tool_calls:
        tool_id = tool.get("id")
        related_event_id = tool.get("related_event_id")
        if not tool_id or not related_event_id:
            continue
        event = audit_events_by_id.get(str(related_event_id))
        if not event:
            continue
        process = process_for_event(event, processes_by_pid)
        if process:
            tool_related_process_keys[str(tool_id)].add(process_key(process))
    return {
        "process_nodes": process_nodes,
        "tool_calls": tool_calls,
        "sessions": {str(row["id"]): row for row in sessions if row.get("id")},
        "processes_by_pid": processes_by_pid,
        "tools_by_key": tools_by_key,
        "descendants": descendants_by_process(process_nodes),
        "tool_related_process_keys": tool_related_process_keys,
    }


def matching_process(event: dict[str, Any], indexes: dict[str, Any]) -> dict[str, Any] | None:
    return process_for_event(event, indexes["processes_by_pid"])


def matching_tool(event: dict[str, Any], process: dict[str, Any] | None, indexes: dict[str, Any]) -> tuple[dict[str, Any] | None, str]:
    details = event.get("details") or {}
    if isinstance(details, str):
        try:
            details = json.loads(details)
        except json.JSONDecodeError:
            details = {}
    if isinstance(details, dict):
        for key in ("tool_call_id", "tool_id", "tool"):
            value = details.get(key)
            if value and str(value) in indexes["tools_by_key"]:
                return indexes["tools_by_key"][str(value)], f"details.{key}"

    event_id = str(event.get("id") or "")
    for tool in indexes["tool_calls"]:
        if event_id and tool.get("related_event_id") == event_id:
            return tool, "related_event_id"

    timestamp = row_time(event)
    if process:
        event_process_key = process_key(process)
        for tool in indexes["tool_calls"]:
            if not tool_time_contains(tool, timestamp):
                continue
            for related_process_key in related_process_keys_for_tool(tool, indexes):
                related_family = indexes["descendants"].get(related_process_key, {related_process_key})
                if event_process_key in related_family:
                    return tool, "pid_family_time_window"

        root_pid = process.get("root_pid")
        if root_pid is not None:
            for tool in indexes["tool_calls"]:
                related_pid = tool.get("related_pid")
                if related_pid is None or int(related_pid) != int(root_pid):
                    continue
                if not tool_time_contains(tool, timestamp):
                    continue
                for related_process_key in related_process_keys_for_tool(tool, indexes):
                    related_family = indexes["descendants"].get(related_process_key, {related_process_key})
                    if event_process_key in related_family:
                        return tool, "root_pid_time_window"
    return None, "none"


def orphan_reason(process: dict[str, Any] | None, tool: dict[str, Any] | None, session: dict[str, Any] | None) -> str:
    if not process:
        return "missing_process_time_match"
    if not tool:
        return "missing_tool_ancestry"
    if not session:
        return "missing_session"
    return ""


def lineage_rows(snapshot: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], Counter[str]]:
    indexes = build_indexes(snapshot)
    project = snapshot.get("project") or "agentsight"
    rows = []
    orphans = []
    folded: Counter[str] = Counter()
    for event in snapshot.get("audit_events") or []:
        if event.get("audit_type") not in {"process", "file", "network"}:
            continue
        process = matching_process(event, indexes)
        tool, join_method = matching_tool(event, process, indexes)
        session = indexes["sessions"].get(str(tool.get("session_id"))) if tool else None
        joined = bool(process and tool and session)
        reason = orphan_reason(process, tool, session)
        row = {
            "event_id": event.get("id"),
            "audit_type": event.get("audit_type"),
            "action": event.get("action"),
            "effect": effect_name(event),
            "target_group": target_group(event),
            "pid": event.get("pid"),
            "process_id": process.get("id") if process else None,
            "process_comm": process.get("comm") if process else None,
            "tool_id": tool.get("id") if tool else None,
            "session_id": session.get("id") if session else None,
            "session_tag": session_tag(session) if session else None,
            "prompt_tag": tool_prompt_tag(tool) if tool else None,
            "join_method": join_method,
            "orphan_reason": reason,
            "joined": joined,
        }
        rows.append(row)
        if not joined:
            orphans.append(row)
            continue
        stack = [
            safe_frame(project, "project"),
            safe_frame(session_tag(session), "session"),
            safe_frame(tool_prompt_tag(tool), "prompt"),
            safe_frame(tool.get("tool_name") or "tool", "tool"),
            safe_frame(process.get("comm") or process.get("command") or "process", "process"),
            safe_frame(effect_name(event), "effect"),
            safe_frame(target_group(event), "target"),
            safe_frame(event.get("status") or "observed", "status"),
        ]
        folded[";".join(stack)] += 1
    return rows, orphans, folded


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    fields = [
        "event_id",
        "audit_type",
        "action",
        "effect",
        "target_group",
        "pid",
        "process_id",
        "process_comm",
        "tool_id",
        "session_id",
        "session_tag",
        "prompt_tag",
        "join_method",
        "orphan_reason",
        "joined",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field) for field in fields})


def write_folded(path: Path, folded: Counter[str]) -> None:
    lines = [f"{stack} {weight}" for stack, weight in folded.most_common()]
    path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")


def write_summary(path: Path, result: dict[str, Any]) -> None:
    source_line = (
        "The committed run is fixture-backed; it is not a live exact-capture result."
        if result["source"] == "fixture"
        else "This run used a non-fixture AgentSight snapshot; scope is limited to the supplied snapshot."
    )
    claim_lines = (
        [
            "- This supports the C4 checker and stack grammar only.",
            "- C4 remains unsupported until live AgentSight exact effects from real sessions pass the same checker.",
        ]
        if result["source"] == "fixture"
        else [
            "- This supports C4 for the in-scope effects present in this snapshot.",
            "- Broader C4 still requires lower orphan rates, DB-persisted ancestry, and more live tasks.",
        ]
    )
    lines = [
        "# Effect Lineage Smoke",
        "",
        "This smoke validates exact-effect lineage invariants on an AgentSight-shaped snapshot.",
        source_line,
        "",
        "## Metrics",
        "",
        f"- Effects checked: {result['effect_events']}.",
        f"- Joined effects: {result['joined_effect_events']} ({result['join_rate_pct']}%).",
        f"- Orphan effects: {result['orphan_effect_events']}.",
        f"- Orphan reasons: {result['orphan_reasons']}.",
        f"- Folded exact-effect stacks: {result['folded_stack_count']}.",
        "",
        "## Claim Boundary",
        "",
        *claim_lines,
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run(args: argparse.Namespace) -> dict[str, Any]:
    out_dir = Path(args.out).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    snapshot_path = Path(args.snapshot)
    snapshot = read_json(snapshot_path)
    rows, orphans, folded = lineage_rows(snapshot)
    joined = len(rows) - len(orphans)
    passed = bool(rows and not orphans)
    passed_status = "fixture_lineage_smoke_passed" if args.fixture else "lineage_smoke_passed"
    result = {
        "schema_version": 1,
        "status": passed_status if passed else "lineage_smoke_failed",
        "source": "fixture" if args.fixture else "snapshot",
        "snapshot": snapshot_path.name,
        "effect_events": len(rows),
        "joined_effect_events": joined,
        "orphan_effect_events": len(orphans),
        "join_rate_pct": round(100.0 * joined / len(rows), 3) if rows else 0.0,
        "folded_stack_count": len(folded),
        "join_methods": dict(Counter(row["join_method"] for row in rows)),
        "orphan_reasons": dict(Counter(row["orphan_reason"] for row in orphans)),
        "orphan_examples": orphans[:10],
        "claim_boundary": (
            "checker evidence only; live exact capture over real sessions is still missing"
            if args.fixture
            else "live snapshot evidence for joined effects; broader exact-lineage claim still needs lower orphan rates, DB-persisted ancestry, and more tasks"
        ),
    }
    (out_dir / "effect-lineage-smoke.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    write_csv(out_dir / "effect-lineage.csv", rows)
    write_folded(out_dir / "effect-lineage.folded.txt", folded)
    write_summary(out_dir / "effect-lineage-summary.md", result)
    print(json.dumps(result, indent=2))
    return result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    here = Path(__file__).resolve().parent
    parser.add_argument("--snapshot", default=str(here / "fixtures" / "effect-lineage-snapshot.json"))
    parser.add_argument("--out", default=str(here / "out"))
    parser.add_argument("--fixture", action="store_true", help="mark the input as a fixture-backed smoke")
    return parser


if __name__ == "__main__":
    result = run(build_parser().parse_args())
    if result["status"] == "lineage_smoke_failed":
        raise SystemExit(1)
