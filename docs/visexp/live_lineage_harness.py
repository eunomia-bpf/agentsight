#!/usr/bin/env python3
"""Build a C4 live-lineage smoke snapshot from an AgentSight DB export.

Collector DB exports currently contain process/file/network effects but may not
materialize agent sessions or tool calls. This harness adds a minimal
agent-run envelope around detected Codex/Claude root processes, without editing
the low-level events. The downstream checker still validates whether each
in-scope effect joins through the real process family.
"""

from __future__ import annotations

import argparse
import json
import re
import urllib.error
import urllib.request
from collections import deque
from pathlib import Path
from typing import Any


WORD_RE = re.compile(r"^[a-z][a-z0-9]{1,23}$")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def sanitize_id(value: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_.:-]+", "-", value).strip("-") or "unknown"


def one_word_fallback(text: str) -> str:
    lowered = text.lower()
    for keyword in (
        "debug",
        "test",
        "review",
        "refactor",
        "docs",
        "trace",
        "ssl",
        "prompt",
        "smoke",
    ):
        if keyword in lowered:
            return keyword
    return "smoke"


def llama_tag(llama_url: str, text: str) -> str | None:
    if not llama_url:
        return None
    payload = {
        "model": "local",
        "temperature": 0,
        "max_tokens": 8,
        "messages": [
            {
                "role": "system",
                "content": "Return exactly one lowercase English word. No punctuation.",
            },
            {
                "role": "user",
                "content": "Name this coding-agent task in one word:\n" + text[:4000],
            },
        ],
    }
    data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        llama_url.rstrip("/") + "/v1/chat/completions",
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            body = json.loads(response.read().decode("utf-8"))
    except (OSError, urllib.error.URLError, json.JSONDecodeError):
        return None
    content = (
        body.get("choices", [{}])[0]
        .get("message", {})
        .get("content", "")
        .strip()
        .lower()
    )
    content = re.sub(r"[^a-z0-9]+", "", content)
    return content if WORD_RE.match(content) else None


def command_text(event: dict[str, Any]) -> str:
    details = event.get("details") or {}
    if not isinstance(details, dict):
        details = {}
    return str(details.get("full_command") or event.get("summary") or event.get("target") or "")


def process_key(row: dict[str, Any]) -> tuple[int | None, int]:
    return row.get("pid"), int(row.get("start_timestamp_ms") or 0)


def process_by_pid(snapshot: dict[str, Any]) -> dict[int, list[dict[str, Any]]]:
    out: dict[int, list[dict[str, Any]]] = {}
    for row in snapshot.get("process_nodes") or []:
        pid = row.get("pid")
        if pid is not None:
            out.setdefault(int(pid), []).append(row)
    return out


def matching_process(event: dict[str, Any], by_pid: dict[int, list[dict[str, Any]]]) -> dict[str, Any] | None:
    pid = event.get("pid")
    if pid is None:
        return None
    timestamp = int(event.get("timestamp_ms") or 0)
    for process in by_pid.get(int(pid), []):
        start = process.get("start_timestamp_ms")
        end = process.get("end_timestamp_ms")
        if start is not None and timestamp < int(start):
            continue
        if end is not None and timestamp > int(end):
            continue
        return process
    return None


def children_by_parent(process_nodes: list[dict[str, Any]]) -> dict[tuple[int | None, int], list[dict[str, Any]]]:
    by_parent: dict[tuple[int | None, int], list[dict[str, Any]]] = {}
    by_pid = process_by_pid({"process_nodes": process_nodes})
    for child in process_nodes:
        ppid = child.get("ppid")
        if ppid is None:
            continue
        child_start = child.get("start_timestamp_ms")
        for parent in by_pid.get(int(ppid), []):
            if child_start is not None:
                parent_start = parent.get("start_timestamp_ms")
                parent_end = parent.get("end_timestamp_ms")
                if parent_start is not None and int(child_start) < int(parent_start):
                    continue
                if parent_end is not None and int(child_start) > int(parent_end):
                    continue
            by_parent.setdefault(process_key(parent), []).append(child)
    return by_parent


def descendant_pids(root: dict[str, Any], process_nodes: list[dict[str, Any]]) -> set[int]:
    children = children_by_parent(process_nodes)
    out: set[int] = set()
    queue = deque([root])
    seen: set[tuple[int | None, int]] = set()
    while queue:
        node = queue.popleft()
        key = process_key(node)
        if key in seen:
            continue
        seen.add(key)
        if node.get("pid") is not None:
            out.add(int(node["pid"]))
        queue.extend(children.get(key, []))
    return out


def is_agent_exec(event: dict[str, Any]) -> bool:
    if event.get("audit_type") != "process" or event.get("action") != "exec":
        return False
    command = command_text(event).lower()
    target = str(event.get("target") or "").lower()
    comm = str(event.get("comm") or "").lower()
    is_codex = "codex" in comm or "/codex" in target or " codex " in f" {command} "
    is_claude = "claude" in comm or "/claude" in target or " claude " in f" {command} "
    return is_codex or is_claude


def agent_name(event: dict[str, Any]) -> str:
    text = " ".join([str(event.get("comm") or ""), str(event.get("target") or ""), command_text(event)]).lower()
    if "codex" in text:
        return "codex"
    if "claude" in text:
        return "claude"
    return "agent"


def extract_prompt(agent: str, command: str) -> str:
    if agent == "codex":
        marker = " --skip-git-repo-check "
        if marker in command:
            return command.split(marker, 1)[1].strip().strip("'\"")
        if " exec " in command:
            return command.split(" exec ", 1)[1].strip().strip("'\"")
    if agent == "claude":
        for marker in (" --print ", " -p "):
            if marker in command:
                rest = command.split(marker, 1)[1].strip()
                for stopper in (" --permission-mode", " --allowedTools", " --output-format"):
                    if stopper in rest:
                        rest = rest.split(stopper, 1)[0]
                return rest.strip().strip("'\"")
    return command.strip()


def detected_roots(snapshot: dict[str, Any]) -> list[dict[str, Any]]:
    by_pid = process_by_pid(snapshot)
    roots = []
    used_root_pids: set[int] = set()
    for event in sorted(snapshot.get("audit_events") or [], key=lambda row: int(row.get("timestamp_ms") or 0)):
        if not is_agent_exec(event):
            continue
        process = matching_process(event, by_pid)
        if not process or process.get("pid") is None:
            continue
        pid = int(process["pid"])
        if pid in used_root_pids:
            continue
        used_root_pids.add(pid)
        roots.append({"event": event, "process": process})
    return roots


def synthesize(
    snapshot: dict[str, Any],
    llama_url: str = "",
    scope_covered_effects: bool = False,
) -> tuple[dict[str, Any], dict[str, Any]]:
    out = json.loads(json.dumps(snapshot))
    process_nodes = out.get("process_nodes") or []
    audit_events = out.get("audit_events") or []
    roots = detected_roots(out)
    sessions = list(out.get("sessions") or [])
    tool_calls = list(out.get("tool_calls") or [])
    metrics = {
        "detected_agent_roots": len(roots),
        "synthesized_sessions": 0,
        "synthesized_tool_calls": 0,
        "covered_effect_events": 0,
        "raw_effect_events": sum(
            1
            for row in audit_events
            if row.get("audit_type") in {"process", "file", "network"}
        ),
        "excluded_out_of_scope_effect_events": 0,
        "tagger": "llama" if llama_url else "fallback",
    }
    covered_event_ids: set[str] = set()

    for root in roots:
        event = root["event"]
        process = root["process"]
        pid = int(process["pid"])
        agent = agent_name(event)
        command = command_text(event)
        prompt = extract_prompt(agent, command)
        tag = llama_tag(llama_url, prompt) or one_word_fallback(prompt)
        pids = descendant_pids(process, process_nodes)
        covered = [
            row
            for row in audit_events
            if row.get("audit_type") in {"process", "file", "network"}
            and row.get("pid") is not None
            and int(row["pid"]) in pids
        ]
        if not covered:
            continue
        start = min(int(row.get("timestamp_ms") or 0) for row in covered)
        end = max(int(row.get("timestamp_ms") or 0) for row in covered)
        sid = f"live:{agent}:{pid}:{start}"
        tool_id = f"tool:{sid}:agent-run"
        sessions.append(
            {
                "id": sid,
                "agent_type": agent,
                "start_timestamp_ms": start,
                "end_timestamp_ms": end,
                "status": "observed",
                "model": None,
                "input_tokens": 0,
                "output_tokens": 0,
                "total_tokens": 0,
                "view_source": "live_lineage_harness",
                "confidence": 0.8,
                "attributes": {
                    "session_tag": tag,
                    "semantic_session": tag,
                    "prompt_preview": prompt[:160],
                    "root_pid": pid,
                    "root_event_id": event.get("id"),
                },
            }
        )
        tool_calls.append(
            {
                "id": tool_id,
                "session_id": sid,
                "conversation_id": None,
                "timestamp_ms": start,
                "tool_name": "agent-run",
                "tool_call_id": tool_id,
                "start_timestamp_ms": start,
                "end_timestamp_ms": end,
                "duration_ms": end - start,
                "status": "observed",
                "input": {
                    "prompt_tag": tag,
                    "semantic_prompt": tag,
                    "prompt_preview": prompt[:160],
                },
                "output": {},
                "related_pid": pid,
                "related_event_id": event.get("id"),
                "view_source": "live_lineage_harness",
                "confidence": 0.8,
            }
        )
        metrics["synthesized_sessions"] += 1
        metrics["synthesized_tool_calls"] += 1
        covered_event_ids.update(str(row.get("id")) for row in covered if row.get("id"))

    metrics["covered_effect_events"] = len(covered_event_ids)
    if scope_covered_effects:
        scoped_events = [
            row
            for row in audit_events
            if row.get("audit_type") not in {"process", "file", "network"}
            or str(row.get("id")) in covered_event_ids
        ]
        out["audit_events"] = scoped_events
        metrics["excluded_out_of_scope_effect_events"] = (
            metrics["raw_effect_events"] - len(covered_event_ids)
        )
    out["sessions"] = sessions
    out["tool_calls"] = tool_calls
    out["lineage_harness"] = metrics
    return out, metrics


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--llama-url", default="")
    parser.add_argument(
        "--scope-covered-effects",
        action="store_true",
        help="keep only process/file/network effects covered by detected agent roots",
    )
    args = parser.parse_args()
    snapshot = read_json(Path(args.snapshot))
    enriched, metrics = synthesize(snapshot, args.llama_url, args.scope_covered_effects)
    write_json(Path(args.out), enriched)
    print(json.dumps({"out": args.out, **metrics}, indent=2))


if __name__ == "__main__":
    main()
