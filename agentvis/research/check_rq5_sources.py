#!/usr/bin/env python3
"""Independent native-source audit for the RQ5 projection.

This checker deliberately does not import the Rust parser or the analysis
script.  It locates transcript files by the exported path hash, reparses the
source JSON, and reconciles exact Skill fields plus instruction-file mentions.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import shlex
from collections import Counter, defaultdict
from pathlib import Path


INSTRUCTIONS = {"AGENTS.md", "CLAUDE.md", "SKILL.md"}


def stream_id(path: Path) -> str:
    return hashlib.sha256(str(path).encode()).hexdigest()[:16]


def source_files() -> dict[str, Path]:
    home = Path.home()
    patterns = [
        home / ".claude" / "projects",
        home / ".codex" / "sessions",
        home / ".codex" / "archived_sessions",
        home / ".gemini" / "tmp",
    ]
    found = {}
    for root in patterns:
        if not root.exists():
            continue
        for path in root.rglob("*.jsonl"):
            found[stream_id(path)] = path
        for path in root.rglob("session-*.json"):
            found[stream_id(path)] = path
    return found


def is_prompt(obj: dict) -> bool:
    typ = obj.get("type")
    if typ == "user":
        if obj.get("isMeta") is True:
            return False
        content = obj.get("message", {}).get("content")
        if isinstance(content, list) and any(
            isinstance(item, dict) and item.get("type") == "tool_result"
            for item in content
        ):
            return False
        return True
    if typ == "queue-operation":
        return obj.get("operation") == "enqueue" and bool(obj.get("content"))
    if typ == "last-prompt":
        return bool(obj.get("lastPrompt"))
    if typ == "event_msg":
        return obj.get("payload", {}).get("type") == "user_message"
    return typ in {"input"}


def prompt_text(obj: dict) -> str:
    typ = obj.get("type")
    value = None
    if typ == "user":
        value = obj.get("message", {}).get("content")
    elif typ == "queue-operation":
        value = obj.get("content")
    elif typ == "last-prompt":
        value = obj.get("lastPrompt")
    elif typ == "event_msg":
        value = obj.get("payload", {}).get("message") or obj.get("payload", {}).get("content")
    else:
        value = obj.get("content") or obj.get("message") or obj.get("payload")

    def text(value: object) -> str:
        if isinstance(value, str):
            return value
        if isinstance(value, list):
            return " ".join(text(item) for item in value)
        if isinstance(value, dict):
            if value.get("type") == "tool_result":
                return ""
            return text(value.get("text") or value.get("content") or value.get("message") or "")
        return ""

    return " ".join(text(value).split())


def instruction_access(row: dict) -> tuple[set[str], str | None]:
    tool = (row.get("name") or "").lower()
    value = row.get("input")
    paths: list[str] = []

    def collect(value: object) -> None:
        if isinstance(value, dict):
            for key, child in value.items():
                if key.lower() in {
                    "path", "file_path", "filepath", "old_path", "new_path",
                    "notebook_path",
                } and isinstance(child, str):
                    paths.append(child)
                elif isinstance(child, (dict, list)):
                    collect(child)
        elif isinstance(value, list):
            for child in value:
                collect(child)

    collect(value)
    if "patch" in tool:
        patch = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False)
        paths.extend(
            match.group(1).strip()
            for match in re.finditer(
                r"^\*\*\* (?:Update|Add|Delete|Move to) File:\s*(.+)$",
                patch,
                re.MULTILINE,
            )
        )
    direct_names = {
        os.path.basename(path.rstrip("/"))
        for path in paths
        if os.path.basename(path.rstrip("/")) in INSTRUCTIONS
    }
    if any(token in tool for token in ("write", "edit", "patch")):
        return direct_names, "mutation" if direct_names else None
    if any(token in tool for token in ("read", "grep", "glob", "search")):
        return direct_names, "read" if direct_names else None

    command = ""
    if isinstance(value, dict):
        command = next(
            (value[key] for key in ("cmd", "command", "text") if isinstance(value.get(key), str)),
            "",
        )
    elif isinstance(value, str):
        command = value
    if not any(token in tool for token in ("bash", "shell", "exec", "command")):
        return set(), None
    if any(marker in command for marker in ("\n", "&&", ";", "|", "$(", "`", "<<")):
        return set(), None
    try:
        shell_tokens = shlex.split(command, comments=False, posix=True)
    except ValueError:
        shell_tokens = command.split()
    executable = os.path.basename(shell_tokens[0]).lower() if shell_tokens else ""
    read_commands = {
        "cat", "rg", "grep", "ls", "head", "tail", "stat", "wc",
        "git", "xxd", "cmp", "diff", "readlink", "realpath", "sha256sum",
    }
    mutation_commands = {"rm", "mv", "cp", "tee", "touch", "install"}
    if executable not in read_commands | mutation_commands | {"sed", "perl"}:
        return set(), None
    operands = [token.strip("'\"`,;:()[]{}") for token in shell_tokens[1:]]
    if executable in {"rg", "grep"}:
        non_options = [token for token in operands if token and not token.startswith("-")]
        operands = non_options if "--files" in shell_tokens else (non_options[1:] if non_options else [])
    shell_names = {
        os.path.basename(path.rstrip("/"))
        for path in operands
        if "*" not in path
        and "?" not in path
        and os.path.basename(path.rstrip("/")) in INSTRUCTIONS
    }
    names = direct_names | shell_names
    if not names:
        return set(), None
    if executable in mutation_commands:
        return names, "mutation"
    if executable in {"sed", "perl"}:
        kind = "mutation" if any(
            token == "-i" or token.startswith("-i") for token in shell_tokens[1:]
        ) else "read"
        return names, kind
    return names, "read"


def tool_rows(path: Path) -> dict[str, dict]:
    if path.suffix == ".json":
        return gemini_rows(path)
    rows = {}
    session_id = None
    source_role = None
    source_agent_id = None
    ordinal = 0
    prompt_epoch = 0
    last_prompt = None
    with path.open(errors="replace") as stream:
        for line_index, line in enumerate(stream):
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            if obj.get("sessionId") or obj.get("session_id"):
                session_id = obj.get("sessionId") or obj.get("session_id")
            if obj.get("type") == "session_meta":
                payload = obj.get("payload", {})
                source = payload.get("source")
                session_id = (
                    payload.get("session_id") or payload.get("thread_id")
                    or payload.get("id") or session_id
                )
                source_role = (
                    payload.get("thread_source")
                    or ("subagent" if isinstance(source, dict) and source.get("subagent") else "root")
                )
                source_agent_id = payload.get("agent_path") or payload.get("agent_nickname")
            if "isSidechain" in obj and obj.get("isSidechain") is not None:
                source_role = "subagent" if obj["isSidechain"] else "root"
            if obj.get("agentId"):
                source_agent_id = obj["agentId"]
            if is_prompt(obj):
                prompt = prompt_text(obj)
                if prompt and prompt != last_prompt:
                    prompt_epoch += 1
                    last_prompt = prompt
            if obj.get("type") == "assistant":
                content = obj.get("message", {}).get("content", [])
                for item in content if isinstance(content, list) else []:
                    if item.get("type") != "tool_use":
                        continue
                    this_ordinal = ordinal
                    ordinal += 1
                    if not item.get("id"):
                        continue
                    rows[item["id"]] = {
                        "name": item.get("name"),
                        "input": item.get("input"),
                        "serialized": json.dumps(item.get("input"), ensure_ascii=False),
                        "skill_name": (item.get("input") or {}).get("skill"),
                        "skill_args": (item.get("input") or {}).get("args"),
                        "attribution_skill": obj.get("attributionSkill"),
                        "attribution_agent": obj.get("attributionAgent"),
                        "source_event_id": obj.get("uuid") or obj.get("id"),
                        "session_id": session_id,
                        "source_role": source_role or "root",
                        "source_agent_id": source_agent_id,
                        "ordinal": this_ordinal,
                        "prompt_epoch": prompt_epoch,
                        "line_index": line_index,
                    }
            elif obj.get("type") == "response_item" and obj.get("payload", {}).get("type") in {
                "function_call", "custom_tool_call",
            }:
                payload = obj["payload"]
                call_id = payload.get("call_id") or payload.get("id")
                this_ordinal = ordinal
                ordinal += 1
                if not call_id:
                    continue
                raw = payload.get("arguments", payload.get("input"))
                try:
                    parsed = json.loads(raw) if isinstance(raw, str) else raw
                except json.JSONDecodeError:
                    parsed = raw
                rows[call_id] = {
                    "name": payload.get("name"),
                    "input": parsed,
                    "serialized": json.dumps(parsed, ensure_ascii=False),
                    "skill_name": parsed.get("skill") if isinstance(parsed, dict) else None,
                    "skill_args": parsed.get("args") if isinstance(parsed, dict) else None,
                    "attribution_skill": obj.get("attributionSkill"),
                    "attribution_agent": obj.get("attributionAgent"),
                    "source_event_id": obj.get("id") or payload.get("id"),
                    "session_id": session_id,
                    "source_role": source_role or "root",
                    "source_agent_id": source_agent_id,
                    "ordinal": this_ordinal,
                    "prompt_epoch": prompt_epoch,
                    "line_index": line_index,
                }
    return rows


def gemini_rows(path: Path) -> dict[str, dict]:
    try:
        root = json.loads(path.read_text(errors="replace"))
    except json.JSONDecodeError:
        return {}
    rows = {}
    ordinal = 0
    prompt_epoch = 0
    for line_index, message in enumerate(root.get("messages", [])):
        if message.get("type") == "user":
            prompt_epoch += 1
        for call in message.get("toolCalls", []):
            call_id = call.get("id")
            this_ordinal = ordinal
            ordinal += 1
            if not call_id:
                continue
            rows[call_id] = {
                "name": call.get("name"),
                "input": call,
                "serialized": json.dumps(call, ensure_ascii=False),
                "skill_name": None,
                "skill_args": None,
                "attribution_skill": None,
                "attribution_agent": None,
                "source_event_id": call_id,
                "session_id": root.get("sessionId"),
                "source_role": "root",
                "source_agent_id": None,
                "ordinal": this_ordinal,
                "prompt_epoch": prompt_epoch,
                "line_index": line_index,
            }
    return rows


def load_exported(root: Path) -> tuple[list[dict], list[dict]]:
    all_rows = []
    signals = []
    for path in sorted((root / "events").glob("*.json")):
        trace = json.loads(path.read_text())
        for event in trace["events"]:
            event["project"] = path.stem
            all_rows.append(event)
            if event.get("skill_name") or event.get("attribution_skill") or any(
                os.path.basename(item.get("path", "")) in INSTRUCTIONS
                for item in event.get("source_paths", [])
            ):
                signals.append(event)
    return all_rows, signals


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    all_exported, exported = load_exported(args.input)
    files = source_files()
    needed_streams = {row["source_stream_id"] for row in all_exported}
    missing_streams = sorted(needed_streams - files.keys())
    native = {key: tool_rows(files[key]) for key in needed_streams & files.keys()}

    counts = Counter()
    failures = []
    exported_signal_calls: dict[str, set[str]] = defaultdict(set)
    exported_calls: dict[str, dict[str, dict]] = defaultdict(dict)
    for event in all_exported:
        if event.get("source_call_id"):
            exported_calls[event["source_stream_id"]][event["source_call_id"]] = event
    for event in exported:
        counts["exported_signal_rows"] += 1
        call_id = event.get("source_call_id")
        if not call_id:
            counts["rows_without_call_id"] += 1
            continue
        stream = event["source_stream_id"]
        exported_signal_calls[stream].add(call_id)
        source = native.get(stream, {}).get(call_id)
        if source is None:
            failures.append(f"missing source call {event['project']} {stream} {call_id}")
            continue
        counts["matched_source_calls"] += 1
        for field in ("skill_name", "skill_args", "attribution_skill", "attribution_agent"):
            if event.get(field) != source.get(field):
                failures.append(
                    f"field mismatch {field} {event['project']} {stream} {call_id}"
                )
        expected_native_session = (
            f"{event['vendor']}:{source['session_id']}" if source.get("session_id") else None
        )
        if expected_native_session and event.get("native_session_id") != expected_native_session:
            failures.append(f"root session mismatch {event['project']} {stream} {call_id}")
        if event.get("source_role") != source.get("source_role"):
            failures.append(f"source role mismatch {event['project']} {stream} {call_id}")
        if event.get("source_agent_id") != source.get("source_agent_id"):
            failures.append(f"source agent mismatch {event['project']} {stream} {call_id}")
        try:
            exported_ordinal = int(event["id"].rsplit(":", 1)[1])
        except (ValueError, IndexError):
            exported_ordinal = -1
        if exported_ordinal != source["ordinal"]:
            failures.append(f"tool ordinal mismatch {event['project']} {stream} {call_id}")
        instruction_names = {
            os.path.basename(item.get("path", ""))
            for item in event.get("source_paths", [])
            if os.path.basename(item.get("path", "")) in INSTRUCTIONS
        }
        for name in instruction_names:
            if name not in source["serialized"]:
                failures.append(
                    f"instruction mention missing {name} {event['project']} {stream} {call_id}"
                )
        raw_names, raw_kind = instruction_access(source)
        if raw_names and not instruction_names.issubset(raw_names):
            failures.append(f"instruction names mismatch {event['project']} {stream} {call_id}")
        if instruction_names and raw_names:
            exported_kind = "mutation" if any(
                item.get("access") in {"write", "create", "delete", "rename"}
                for item in event.get("source_paths", [])
                if os.path.basename(item.get("path", "")) in INSTRUCTIONS
            ) else "read"
            if raw_kind and exported_kind != raw_kind:
                failures.append(f"instruction access mismatch {event['project']} {stream} {call_id}")
        if event.get("skill_name"):
            counts["skill_invocations_matched"] += 1
        if event.get("attribution_skill"):
            counts["attributions_matched"] += 1
        if instruction_names:
            counts["instruction_rows_matched"] += 1

    # Every native Skill/attribution call in an included stream must survive
    # the repository-direct projection.  This is stricter than sampling rows.
    audited_instructions = []
    for stream, calls in native.items():
        for call_id, source in calls.items():
            raw_instruction_names, _ = instruction_access(source)
            if source.get("skill_name") or source.get("attribution_skill"):
                counts["native_skill_signal_calls"] += 1
                if call_id not in exported_signal_calls[stream]:
                    failures.append(f"native signal omitted {stream} {call_id}")
            if raw_instruction_names:
                counts["native_high_confidence_instruction_calls"] += 1
                event = exported_calls[stream].get(call_id)
                if event is not None:
                    audited_instructions.append(
                        {
                            "project": event["project"],
                            "source_stream_id": stream,
                            "source_call_id": call_id,
                            "source_kind": instruction_access(source)[1],
                            "files": ";".join(sorted(raw_instruction_names)),
                        }
                    )
                if call_id not in exported_signal_calls[stream]:
                    failures.append(f"native signal omitted {stream} {call_id}")

    # Prompt boundaries are audited as equivalence relations rather than by
    # comparing arbitrary absolute counters.  Consecutive projected calls in
    # one source stream must agree on whether a native user turn intervened.
    for stream, calls in native.items():
        ordered = list(
            (source, exported_calls[stream].get(call_id))
            for call_id, source in calls.items()
            if exported_calls[stream].get(call_id) is not None
        )
        ordered.sort(key=lambda pair: pair[0]["ordinal"])
        for (left_source, left_event), (right_source, right_event) in zip(ordered, ordered[1:]):
            raw_same = left_source["prompt_epoch"] == right_source["prompt_epoch"]
            projected_same = left_event.get("prompt_index") == right_event.get("prompt_index")
            counts["prompt_boundaries_checked"] += 1
            if raw_same != projected_same:
                failures.append(
                    f"prompt boundary mismatch {stream} {left_event['source_call_id']} {right_event['source_call_id']}"
                )

    failure_types = Counter(
        next(
            (prefix for prefix in (
                "missing source call", "field mismatch", "root session mismatch",
                "source role mismatch", "source agent mismatch", "tool ordinal mismatch",
                "instruction mention missing", "instruction names mismatch",
                "instruction access mismatch", "native signal omitted",
                "prompt boundary mismatch",
            ) if failure.startswith(prefix)),
            "other",
        )
        for failure in failures
    )
    result = {
        "status": "PASS" if not missing_streams and not failures else "FAIL",
        "needed_source_streams": len(needed_streams),
        "located_source_streams": len(needed_streams) - len(missing_streams),
        "missing_source_streams": missing_streams,
        "counts": dict(sorted(counts.items())),
        "failure_count": len(failures),
        "failure_types": dict(sorted(failure_types.items())),
        "failures": failures[:100],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    with args.output.with_name("source-check-instructions.csv").open("w", newline="") as stream:
        writer = csv.DictWriter(
            stream,
            fieldnames=["project", "source_stream_id", "source_call_id", "source_kind", "files"],
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(audited_instructions)
    print(json.dumps(result, indent=2, sort_keys=True))
    if result["status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
