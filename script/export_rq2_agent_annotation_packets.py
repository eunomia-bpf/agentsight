#!/usr/bin/env python3
"""Export source-only RQ2 trajectories for automatic Agent segmentation.

The three retained localization workloads expose different source schemas.  This
adapter projects each one onto the same ordered contract: one source sequence,
one replay-stable operation ID per visible step, a native hierarchy, and a
compact source summary.  It deliberately omits target, risk, localizer, judge,
score, and existing grouping fields.

This is an experiment adapter, not an AgentPProf model backend.  The automatic
Agent writes sparse complete-path marks; AgentPProf only validates and folds
those marks into a standard pprof profile.
"""

from __future__ import annotations

import argparse
from collections import defaultdict
import json
from pathlib import Path
import re
from typing import Any, Iterable


SCHEMA = "agentsight.rq2-agent-annotation-packet.v1"
QUESTION = (
    "How did the agent decompose and advance the assigned task, including "
    "distinct work, verification, recovery, returns, and completion?"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--benchmark", choices=("agentprocess", "hint", "trace"), required=True
    )
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--selection", choices=("preflight", "full"), default="preflight")
    parser.add_argument("--batches", type=int, default=3)
    parser.add_argument("--out", type=Path, required=True)
    return parser.parse_args()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as stream:
        for line_number, line in enumerate(stream, 1):
            if not line.strip():
                continue
            row = json.loads(line)
            require(isinstance(row, dict), f"{path}:{line_number}: expected object")
            rows.append(row)
    return rows


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )


def clean_text(value: Any, limit: int = 1200) -> str:
    if value is None:
        return ""
    if not isinstance(value, str):
        value = json.dumps(value, ensure_ascii=False, sort_keys=True)
    value = " ".join(value.split())
    if len(value) <= limit:
        return value
    head = max(1, limit * 2 // 3)
    tail = max(1, limit - head - 24)
    return value[:head] + " ... [middle omitted] ... " + value[-tail:]


def native_path(*values: Any) -> list[str]:
    return [clean_text(value, 180) for value in values if clean_text(value, 180)]


def balanced_batches(
    packets: list[dict[str, Any]], count: int
) -> list[list[dict[str, Any]]]:
    require(count > 0, "batch count must be positive")
    count = min(count, len(packets))
    batches: list[list[dict[str, Any]]] = [[] for _ in range(count)]
    loads = [0] * count
    for packet in sorted(
        packets,
        key=lambda item: (-int(item["operation_count"]), str(item["sequence"])),
    ):
        index = min(range(count), key=lambda candidate: (loads[candidate], candidate))
        batches[index].append(packet)
        loads[index] += int(packet["operation_count"])
    for batch in batches:
        batch.sort(key=lambda item: str(item["sequence"]))
    return batches


def agentprocess_packets(root: Path) -> list[dict[str, Any]]:
    rows = read_jsonl(root / "projection.jsonl")
    grouped: defaultdict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[str(row["trajectory_id"])].append(row)
    packets = []
    for sequence, operations in sorted(grouped.items()):
        operations.sort(
            key=lambda row: (
                int(row["message_index"]),
                int(row["step_ordinal"]),
                str(row["operation_id"]),
            )
        )
        first = operations[0]
        packets.append(
            {
                "sequence": sequence,
                "benchmark": "AgentProcessBench",
                "task_family": str(first["family"]),
                "task": f"{first['family']} task {first['task_id']}",
                "operation_count": len(operations),
                "operations": [
                    {
                        "operation_id": str(row["operation_id"]),
                        "ordinal": index,
                        "native_path": native_path(
                            row.get("family"),
                            row.get("phase"),
                            row.get("intent"),
                            row.get("action"),
                            row.get("target"),
                            row.get("repeat_state"),
                        ),
                        "source_summary": clean_text(
                            {
                                "message_index": row.get("message_index"),
                                "query_index": row.get("query_index"),
                                "phase": row.get("phase"),
                                "intent": row.get("intent"),
                                "action": row.get("action"),
                                "target": row.get("target"),
                                "repeat_state": row.get("repeat_state"),
                            }
                        ),
                        "source_ref": f"projection.jsonl#{row['operation_id']}",
                    }
                    for index, row in enumerate(operations)
                ],
            }
        )
    require(len(packets) == 1000, "AgentProcessBench sequence count")
    require(sum(packet["operation_count"] for packet in packets) == 8509,
            "AgentProcessBench operation count")
    return packets


def visible_hint_item(item: dict[str, Any]) -> dict[str, Any]:
    visible: dict[str, Any] = {"role": item.get("role")}
    if item.get("action") is not None:
        visible["action"] = item["action"]
    if item.get("thought") is not None:
        visible["thought"] = clean_text(item["thought"], 700)
    if item.get("content") is not None:
        visible["content"] = clean_text(item["content"], 900)
    return visible


def hint_packets(root: Path) -> list[dict[str, Any]]:
    rows = read_jsonl(root / "operations" / "test-projection.jsonl")
    sources = {int(row["id"]): row for row in read_json(root / "sources" / "test.json")}
    grouped: defaultdict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[str(row["record_key"])].append(row)
    packets = []
    for sequence, operations in sorted(grouped.items()):
        operations.sort(key=lambda row: (int(row["ordinal"]), str(row["operation_id"])))
        record_ids = {int(row["record_id"]) for row in operations}
        require(len(record_ids) == 1, f"{sequence}: multiple source records")
        record_id = next(iter(record_ids))
        source = sources[record_id]
        trajectory = source["trajectory"]
        trajectory_by_step = {int(item["step_id"]): item for item in trajectory}
        require(
            len(trajectory_by_step) == len(trajectory),
            f"{sequence}: duplicate source step ID",
        )
        first_user = next(
            (
                clean_text(item.get("content"), 1200)
                for item in trajectory
                if item.get("role") == "user" and item.get("content")
            ),
            str(source["task_id"]),
        )
        packet_operations = []
        for index, row in enumerate(operations):
            source_step = int(row["display_id"])
            require(source_step in trajectory_by_step, f"{sequence}: source step")
            raw = row["raw_fields"]
            source_item = trajectory_by_step[source_step]
            packet_operations.append(
                {
                    "operation_id": str(row["operation_id"]),
                    "ordinal": index,
                    "native_path": native_path(
                        raw.get("environment"),
                        row.get("role"),
                        raw.get("phase"),
                        raw.get("action"),
                        raw.get("status"),
                    ),
                    "source_summary": visible_hint_item(source_item),
                    "source_ref": (
                        f"sources/test.json#record-{record_id}/step-{source_step}"
                    ),
                }
            )
        packets.append(
            {
                "sequence": sequence,
                "benchmark": "HINTBench",
                "task_family": str(operations[0]["raw_fields"]["environment"]),
                "task": first_user,
                "operation_count": len(packet_operations),
                "operations": packet_operations,
            }
        )
    require(len(packets) == 536, "HINTBench sequence count")
    require(sum(packet["operation_count"] for packet in packets) == 12877,
            "HINTBench operation count")
    return packets


def parse_trace_source(root: Path) -> dict[str, dict[str, Any]]:
    traces: dict[str, dict[str, Any]] = {}
    task_pattern = re.compile(
        r"Task instruction: (.*?)\nAgent system introduction:", re.DOTALL
    )
    steps_pattern = re.compile(r"\nSteps: (\[.*\])\s*$", re.DOTALL)
    for request in read_jsonl(root / "requests" / "tagger.jsonl"):
        messages = request["payload"]["messages"]
        content = str(messages[-1]["content"])
        task_match = task_pattern.search(content)
        steps_match = steps_pattern.search(content)
        require(task_match is not None, f"{request['trace_id']}: missing task")
        require(steps_match is not None, f"{request['trace_id']}: missing steps")
        sequence = str(request["trace_id"])
        target = traces.setdefault(
            sequence, {"task": clean_text(task_match.group(1), 1600), "steps": {}}
        )
        require(target["task"] == clean_text(task_match.group(1), 1600),
                f"{sequence}: inconsistent task")
        for step in json.loads(steps_match.group(1)):
            step_id = int(step["step"])
            require(step_id not in target["steps"], f"{sequence}: duplicate step {step_id}")
            target["steps"][step_id] = step
    return traces


def visible_trace_step(step: dict[str, Any]) -> dict[str, Any]:
    result: dict[str, Any] = {
        "agent_name": clean_text(step.get("agent_name"), 160),
        "last_input": clean_text(step.get("last_input"), 900),
        "response": clean_text(step.get("response"), 1100),
    }
    tool_calls = step.get("tool_calls")
    if tool_calls not in (None, "null", "[]", []):
        result["tool_calls"] = clean_text(tool_calls, 700)
    tool_logs = step.get("tool_logs")
    if tool_logs not in (None, "null", "[]", []):
        result["tool_logs"] = clean_text(tool_logs, 700)
    return result


def trace_packets(root: Path) -> list[dict[str, Any]]:
    rows = read_jsonl(root / "operations" / "projection.jsonl")
    sources = parse_trace_source(root)
    grouped: defaultdict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[str(row["trace_id"])].append(row)
    packets = []
    for sequence, operations in sorted(grouped.items()):
        operations.sort(key=lambda row: (int(row["step_id"]), str(row["operation_id"])))
        source = sources[sequence]
        packet_operations = []
        for index, row in enumerate(operations):
            step_id = int(row["step_id"])
            require(step_id in source["steps"], f"{sequence}: missing source step {step_id}")
            raw = row["raw_fields"]
            packet_operations.append(
                {
                    "operation_id": str(row["operation_id"]),
                    "ordinal": index,
                    "native_path": native_path(
                        raw.get("system"),
                        raw.get("role"),
                        raw.get("intent"),
                        raw.get("component"),
                        raw.get("raw_action"),
                        raw.get("status"),
                    ),
                    "source_summary": visible_trace_step(source["steps"][step_id]),
                    "source_ref": f"requests/tagger.jsonl#{sequence}:step-{step_id}",
                }
            )
        packets.append(
            {
                "sequence": sequence,
                "benchmark": "TraceElephant",
                "task_family": str(operations[0]["cell"]),
                "task": source["task"],
                "operation_count": len(packet_operations),
                "operations": packet_operations,
            }
        )
    require(len(packets) == 220, "TraceElephant sequence count")
    require(sum(packet["operation_count"] for packet in packets) == 5960,
            "TraceElephant operation count")
    return packets


def select_packets(
    packets: list[dict[str, Any]], selection: str
) -> tuple[list[dict[str, Any]], str]:
    if selection == "full":
        return packets, "complete registered workload"
    selected = sorted(
        packets,
        key=lambda item: (-int(item["operation_count"]), str(item["sequence"])),
    )[:1]
    return selected, "one longest real sequence; sequence-ID tie break"


def emit(
    packets: list[dict[str, Any]], selection: str, batches: int, out: Path
) -> None:
    selected, selection_description = select_packets(packets, selection)
    partition = balanced_batches(selected, batches)
    records = []
    for index, batch in enumerate(partition, 1):
        filename = f"batch-{index:02d}.json"
        payload = {
            "schema": SCHEMA,
            "question": QUESTION,
            "annotation_contract": {
                "input": (
                    "source-only ordered operations; no target, risk, localizer, judge, "
                    "score, or existing-group field"
                ),
                "output": "ordered sparse marks with complete semantic_path values",
                "boundary": "an operation_id where the complete path changes",
                "continuation": "emit no mark while the complete path is unchanged",
                "names": (
                    "reuse the same concise semantic name for genuinely equivalent work; "
                    "do not copy unique sequence IDs into semantic names"
                ),
                "depth": "no minimum, maximum, target, or balancing requirement",
                "evidence": "inspect source_summary and source_ref only when needed",
            },
            "sessions": batch,
        }
        write_json(out / filename, payload)
        records.append(
            {
                "file": filename,
                "sequences": len(batch),
                "operations": sum(int(item["operation_count"]) for item in batch),
                "sequence_ids": [str(item["sequence"]) for item in batch],
            }
        )
    manifest = {
        "schema": SCHEMA + ".manifest",
        "question": QUESTION,
        "selection": selection_description,
        "sequences": len(selected),
        "operations": sum(int(packet["operation_count"]) for packet in selected),
        "minimum_operations_per_sequence": min(
            int(packet["operation_count"]) for packet in selected
        ),
        "maximum_operations_per_sequence": max(
            int(packet["operation_count"]) for packet in selected
        ),
        "batches": records,
        "excluded_fields": [
            "target labels",
            "risk annotations and scores",
            "localizer/judge outputs",
            "existing semantic/raw/session group assignments",
        ],
    }
    write_json(out / "manifest.json", manifest)
    print(json.dumps(manifest, ensure_ascii=False, sort_keys=True))


def main() -> None:
    args = parse_args()
    root = args.root.resolve()
    out = args.out.resolve()
    require(root.is_dir(), f"missing root: {root}")
    loaders = {
        "agentprocess": agentprocess_packets,
        "hint": hint_packets,
        "trace": trace_packets,
    }
    packets = loaders[args.benchmark](root)
    emit(packets, args.selection, args.batches, out)


if __name__ == "__main__":
    main()
