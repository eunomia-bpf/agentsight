#!/usr/bin/env python3
"""Export source-only packets for external Agent annotation.

This is an experiment utility, not an AgentPProf inference backend.  It selects
either the registered longest-decile case collection or the complete
CodeTraceBench population, reconstructs source-native turns, and writes
balanced JSON packets. An Agent reads the packets and writes complete semantic
paths at sparse source-operation boundaries for AgentPProf's
--operation-mark-file.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "script"))

import rq3_recursive_operation_segmentation_eval as recursive  # noqa: E402


SCHEMA = "agentsight.agent-operation-annotation-packet.v1"
QUESTION = (
    "How did these long-horizon agents decompose their assigned tasks, where "
    "did they repeat or return to earlier work, and which expensive paths "
    "ended without a supported conclusion?"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target-operations", type=Path, required=True)
    parser.add_argument("--raw-root", type=Path)
    parser.add_argument(
        "--reuse-packet-dir",
        type=Path,
        help="reuse a previously exported complete packet population",
    )
    parser.add_argument(
        "--selection",
        choices=("long-horizon", "remaining", "all"),
        default="long-horizon",
    )
    parser.add_argument("--batches", type=int, default=3)
    parser.add_argument("--out", type=Path, required=True)
    return parser.parse_args()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )


def source_packet(prepared: dict[str, Any]) -> dict[str, Any]:
    material = prepared["material"]
    projected = prepared["projected_turns"]
    turns = prepared["turns"]
    require(len(projected) == len(turns), "projected/native turn count")
    packet_turns = []
    for visible, native in zip(projected, turns, strict=True):
        operations = native["operations"]
        require(bool(operations), "empty source-native turn")
        packet_turns.append(
            {
                **visible,
                "first_operation_id": str(operations[0]["step"]),
                "operation_ids": [str(operation["step"]) for operation in operations],
                "source_refs": [str(operation["source_ref"]) for operation in operations],
            }
        )
    return {
        "session": material["session"],
        "framework": material["framework"],
        "task": material["task"],
        "task_source": material["task_source"],
        "archive": material["archive"],
        "archive_sha256": material["archive_sha256"],
        "operation_count": len(material["operations"]),
        "turn_count": len(packet_turns),
        "turns": packet_turns,
    }


def balanced_batches(
    packets: list[dict[str, Any]], count: int
) -> list[list[dict[str, Any]]]:
    require(count > 0, "batch count must be positive")
    batches: list[list[dict[str, Any]]] = [[] for _ in range(count)]
    loads = [0 for _ in range(count)]
    for packet in sorted(
        packets,
        key=lambda item: (-int(item["operation_count"]), str(item["session"])),
    ):
        index = min(range(count), key=lambda candidate: (loads[candidate], candidate))
        batches[index].append(packet)
        loads[index] += int(packet["operation_count"])
    for batch in batches:
        batch.sort(key=lambda item: str(item["session"]))
    return batches


def load_reusable_packets(packet_dir: Path) -> dict[str, dict[str, Any]]:
    packets: dict[str, dict[str, Any]] = {}
    for path in sorted(packet_dir.glob("batch-*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        for packet in payload["sessions"]:
            session = str(packet["session"])
            require(session not in packets, f"duplicate reusable session: {session}")
            packets[session] = packet
    require(len(packets) == recursive.EXPECTED_SESSIONS, "reusable session coverage")
    require(
        sum(int(packet["operation_count"]) for packet in packets.values())
        == recursive.EXPECTED_OPERATIONS,
        "reusable operation coverage",
    )
    return packets


def main() -> None:
    args = parse_args()
    target = args.target_operations.resolve()
    raw_root = args.raw_root.resolve() if args.raw_root else None
    reuse_packet_dir = (
        args.reuse_packet_dir.resolve() if args.reuse_packet_dir else None
    )
    out = args.out.resolve()
    require(target.is_file(), f"missing target operations: {target}")
    require(
        (raw_root is None) != (reuse_packet_dir is None),
        "provide exactly one of --raw-root or --reuse-packet-dir",
    )
    if raw_root is not None:
        require(raw_root.is_dir(), f"missing raw root: {raw_root}")
    if reuse_packet_dir is not None:
        require(reuse_packet_dir.is_dir(), f"missing reusable packet dir: {reuse_packet_dir}")

    grouped = recursive.base.load_visible_operations(target)
    require(len(grouped) == recursive.EXPECTED_SESSIONS, "source session count")
    require(
        sum(len(rows) for rows in grouped.values()) == recursive.EXPECTED_OPERATIONS,
        "source operation count",
    )
    if args.selection == "long-horizon":
        selected = recursive.long_horizon_sessions(grouped)
        selection_description = (
            "top 41 sessions by descending source-visible operation count; "
            "trajectory ID tie-break"
        )
    elif args.selection == "remaining":
        excluded = set(recursive.long_horizon_sessions(grouped))
        selected = sorted(set(grouped) - excluded)
        selection_description = (
            "remaining 364 CodeTraceBench sessions after reusing the fixed "
            "41-session long-horizon automatic-Agent output"
        )
    else:
        selected = sorted(grouped)
        selection_description = "all 405 CodeTraceBench sessions"
    if reuse_packet_dir is not None:
        reusable = load_reusable_packets(reuse_packet_dir)
        packets = [reusable[session] for session in selected]
    else:
        assert raw_root is not None
        packets = [
            source_packet(recursive.prepare_material(raw_root, session, grouped[session]))
            for session in selected
        ]
    if args.selection == "long-horizon":
        expected_sessions = recursive.LONG_HORIZON_SESSIONS
        expected_operations = recursive.LONG_HORIZON_OPERATIONS
    elif args.selection == "remaining":
        expected_sessions = recursive.EXPECTED_SESSIONS - recursive.LONG_HORIZON_SESSIONS
        expected_operations = recursive.EXPECTED_OPERATIONS - recursive.LONG_HORIZON_OPERATIONS
    else:
        expected_sessions = recursive.EXPECTED_SESSIONS
        expected_operations = recursive.EXPECTED_OPERATIONS
    require(len(packets) == expected_sessions, "session count")
    require(
        sum(int(packet["operation_count"]) for packet in packets)
        == expected_operations,
        "operation count",
    )

    batches = balanced_batches(packets, args.batches)
    manifest_batches = []
    for index, batch in enumerate(batches, 1):
        filename = f"batch-{index:02d}.json"
        payload = {
            "schema": SCHEMA,
            "question": QUESTION,
            "annotation_contract": {
                "unit": "source-native turn; all operation_ids in one turn stay together",
                "boundary": "first_operation_id of a turn",
                "output": "ordered sparse marks with complete semantic_paths",
                "continuation": "emit no mark when the complete path is unchanged",
                "evidence": "use source_refs to inspect raw evidence when summaries are insufficient",
            },
            "sessions": batch,
        }
        write_json(out / filename, payload)
        manifest_batches.append(
            {
                "file": filename,
                "sessions": len(batch),
                "operations": sum(int(item["operation_count"]) for item in batch),
                "turns": sum(int(item["turn_count"]) for item in batch),
                "session_ids": [str(item["session"]) for item in batch],
            }
        )

    manifest = {
        "schema": SCHEMA + ".manifest",
        "selection": selection_description,
        "question": QUESTION,
        "sessions": len(packets),
        "operations": sum(int(packet["operation_count"]) for packet in packets),
        "turns": sum(int(packet["turn_count"]) for packet in packets),
        "minimum_operations_per_session": min(
            int(packet["operation_count"]) for packet in packets
        ),
        "maximum_operations_per_session": max(
            int(packet["operation_count"]) for packet in packets
        ),
        "batches": manifest_batches,
    }
    write_json(out / "manifest.json", manifest)
    print(json.dumps(manifest, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
