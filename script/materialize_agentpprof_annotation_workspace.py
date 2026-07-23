#!/usr/bin/env python3
"""Materialize an AgentPProf workspace from existing source packets and marks.

This adapter does not annotate, infer, normalize, or rename semantic work.  It
only joins the already completed automatic-Agent marks to their source-native
session/turn/tool hierarchy and additive operation/token measurements.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Iterable


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--packet-dir", type=Path, required=True)
    parser.add_argument("--annotations", type=Path, required=True)
    parser.add_argument("--operation-count", type=Path, required=True)
    parser.add_argument("--tokens", type=Path, required=True)
    parser.add_argument(
        "--session-operation-tag",
        required=True,
        help=(
            "Agent-chosen session-level operation name; the existing semantic "
            "root is used as the prompt-level operation name."
        ),
    )
    parser.add_argument(
        "--session-contains",
        action="append",
        default=[],
        help="Keep sessions containing any supplied substring; default keeps all.",
    )
    parser.add_argument("--out", type=Path, required=True)
    return parser.parse_args()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as stream:
        return [json.loads(line) for line in stream if line.strip()]


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )


def write_jsonl(path: Path, values: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as stream:
        for value in values:
            stream.write(json.dumps(value, ensure_ascii=False, sort_keys=True) + "\n")


def node_id(kind: str, session: str, source_id: str | None = None) -> str:
    return f"{kind}:{session}" + (f":{source_id}" if source_id is not None else "")


def selected(session: str, filters: list[str]) -> bool:
    return not filters or any(value in session for value in filters)


def load_packets(packet_dir: Path, filters: list[str]) -> dict[str, dict[str, Any]]:
    packets = {}
    for path in sorted(packet_dir.glob("batch-*.json")):
        for packet in read_json(path)["sessions"]:
            session = str(packet["session"])
            if selected(session, filters):
                require(session not in packets, f"duplicate packet session: {session}")
                packets[session] = packet
    require(bool(packets), "no packet sessions matched")
    return packets


def indexed_weights(
    path: Path, sessions: set[str]
) -> tuple[dict[tuple[str, str], int], dict[tuple[str, str], dict[str, Any]]]:
    weights = {}
    fields = {}
    for row in read_jsonl(path):
        source = row["fields"]
        session = str(source["source_session"])
        if session not in sessions:
            continue
        key = (session, str(source["step_id"]))
        require(key not in weights, f"duplicate operation row: {key}")
        weights[key] = int(row["value"])
        fields[key] = source
    return weights, fields


def materialize(
    packets: dict[str, dict[str, Any]],
    normalized: dict[str, list[dict[str, Any]]],
    counts: dict[tuple[str, str], int],
    tokens: dict[tuple[str, str], int],
    operation_fields: dict[tuple[str, str], dict[str, Any]],
    session_operation_tag: str,
) -> tuple[list[dict[str, Any]], dict[str, dict[str, str | None]]]:
    trace = []
    annotations: dict[str, dict[str, str | None]] = {}
    sessions = set(packets)
    require(set(normalized).issuperset(sessions), "missing normalized session annotations")

    for session in sorted(packets):
        packet = packets[session]
        marks = normalized[session]
        require(bool(marks), f"empty annotations: {session}")
        root_path = list(marks[0]["semantic_path"])
        require(bool(root_path), f"empty root path: {session}")
        require(
            all(mark["semantic_path"][0] == root_path[0] for mark in marks),
            f"semantic root drift: {session}",
        )

        session_node = node_id("session", session)
        prompt_node = node_id("prompt", session)
        session_display = f"{packet['framework']}:{session.rsplit('-', 1)[-1]}"
        trace.append(
            {
                "id": session_node,
                "parent": None,
                "kind": "session",
                "data": {
                    "name": session_display,
                    "agent": str(packet["framework"]),
                    "source": str(packet.get("task_source", "")),
                },
                "metrics": {},
                "path": [],
            }
        )
        trace.append(
            {
                "id": prompt_node,
                "parent": session_node,
                "kind": "prompt",
                "data": {
                    "name": "user request",
                    "text": str(packet["task"]),
                },
                "metrics": {},
                "path": [],
            }
        )
        annotations[session_node] = {
            "tag": session_operation_tag,
            "parent": None,
            "next": None,
        }
        annotations[prompt_node] = {
            "tag": root_path[0],
            "parent": session_node,
            "next": None,
        }

        turns = list(packet["turns"])
        turn_by_first = {str(turn["first_operation_id"]): turn for turn in turns}
        first_to_llm = {
            first: node_id("llm", session, str(turn["turn_id"]))
            for first, turn in turn_by_first.items()
        }
        for turn in turns:
            turn_id = str(turn["turn_id"])
            llm_node = node_id("llm", session, turn_id)
            trace.append(
                {
                    "id": llm_node,
                    "parent": prompt_node,
                    "kind": "llm",
                    "data": {
                        "name": f"turn {turn_id}",
                        "intent": str(turn.get("intent", "")),
                        "response": str(turn.get("visible_result", "")),
                        "planned_action": str(turn.get("planned_action", "")),
                        "progress": str(turn.get("progress", "")),
                    },
                    "metrics": {},
                    "path": [],
                }
            )
            for operation_id in turn["operation_ids"]:
                step = str(operation_id)
                key = (session, step)
                require(key in counts and key in tokens and key in operation_fields, f"missing operation: {key}")
                fields = operation_fields[key]
                trace.append(
                    {
                        "id": node_id("tool", session, step),
                        "parent": llm_node,
                        "kind": "tool",
                        "data": {
                            "name": str(fields.get("tool", fields.get("raw_action_key", "tool"))),
                            "action": str(fields.get("action_kind", "")),
                            "source_ref": str(fields.get("source_ref", "")),
                        },
                        "metrics": {"operations": counts[key], "tokens": tokens[key]},
                        "path": [],
                    }
                )

        for mark_index, mark in enumerate(marks):
            start = str(mark["start_operation_id"])
            require(start in turn_by_first, f"mark does not start a source turn: {(session, start)}")
            semantic_path = list(mark["semantic_path"])
            require(semantic_path[0] == root_path[0], f"mark root mismatch: {(session, start)}")
            next_node = None
            if mark_index + 1 < len(marks):
                next_start = str(marks[mark_index + 1]["start_operation_id"])
                next_node = first_to_llm[next_start]
            parent = prompt_node
            candidate_nodes = [
                first_to_llm[start],
                *[
                    node_id("tool", session, str(operation_id))
                    for operation_id in turn_by_first[start]["operation_ids"]
                ],
            ]
            require(
                len(semantic_path) - 1 <= len(candidate_nodes),
                f"source turn cannot represent semantic depth at {(session, start)}",
            )
            for depth, tag in enumerate(semantic_path[1:]):
                boundary = candidate_nodes[depth]
                require(boundary not in annotations, f"duplicate annotation boundary: {boundary}")
                annotations[boundary] = {"tag": str(tag), "parent": parent, "next": next_node}
                parent = boundary

    expected_operations = sum(int(packet["operation_count"]) for packet in packets.values())
    observed_operations = sum(node["metrics"].get("operations", 0) for node in trace)
    require(observed_operations == expected_operations, "operation mass mismatch")
    return trace, annotations


def main() -> None:
    args = parse_args()
    packets = load_packets(args.packet_dir, args.session_contains)
    normalized = read_json(args.annotations)
    sessions = set(packets)
    counts, operation_fields = indexed_weights(args.operation_count, sessions)
    tokens, token_fields = indexed_weights(args.tokens, sessions)
    require(operation_fields.keys() == token_fields.keys(), "count/token operation mismatch")
    trace, annotations = materialize(
        packets,
        normalized,
        counts,
        tokens,
        operation_fields,
        args.session_operation_tag,
    )
    args.out.mkdir(parents=True, exist_ok=True)
    write_jsonl(args.out / "trace.jsonl", trace)
    write_json(args.out / "annotation.json", annotations)
    print(
        json.dumps(
            {
                "sessions": len(packets),
                "trace_nodes": len(trace),
                "annotations": len(annotations),
                "operations": sum(node["metrics"].get("operations", 0) for node in trace),
                "tokens": sum(node["metrics"].get("tokens", 0) for node in trace),
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
