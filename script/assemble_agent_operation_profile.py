#!/usr/bin/env python3
"""Assemble source-grounded Agent marks into resource-weighted pprof inputs.

This is a research adapter, not an AgentPProf backend. It validates independent
Agent annotation batches against their source-only packets, canonicalizes only
explicitly declared task-family roots, and emits one shared mark file plus
normalized operation-count and provider-token inputs. AgentPProf remains the
only component that folds these inputs and emits the product pprof artifact.
"""

from __future__ import annotations

import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path
from typing import Any, Iterable


FULL_SESSIONS = 405
FULL_OPERATIONS = 20_866
FULL_TURNS = 17_148


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target-operations", type=Path, required=True)
    parser.add_argument("--operation-usage", type=Path, required=True)
    parser.add_argument("--packet-dir", type=Path, action="append", required=True)
    parser.add_argument("--annotation-dir", type=Path, action="append", required=True)
    parser.add_argument(
        "--annotation-override",
        type=Path,
        action="append",
        default=[],
        help="partial source-only Agent annotation file; later files replace named sessions",
    )
    parser.add_argument(
        "--contract-root-only-prefix",
        action="store_true",
        help="attach a one-turn root-only prefix to the first nested responsibility",
    )
    parser.add_argument("--canonical-names", type=Path, required=True)
    parser.add_argument("--mode", choices=("preflight", "full"), default="preflight")
    parser.add_argument("--out", type=Path, required=True)
    return parser.parse_args()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
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


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as stream:
        for row in rows:
            stream.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def semantic_id(label: str) -> str:
    return "op-" + hashlib.sha256(label.encode()).hexdigest()[:24]


def prompt_hash(task: str) -> str:
    return hashlib.sha256(task.encode()).hexdigest()[:16]


def load_packets(
    packet_dirs: list[Path],
) -> tuple[dict[str, dict[str, Any]], dict[str, Any]]:
    sessions: dict[str, dict[str, Any]] = {}
    manifests = []
    for packet_dir in packet_dirs:
        manifests.append(read_json(packet_dir / "manifest.json"))
        for path in sorted(packet_dir.glob("batch-*.json")):
            payload = read_json(path)
            for packet in payload["sessions"]:
                session = str(packet["session"])
                require(session not in sessions, f"duplicate packet session: {session}")
                sessions[session] = packet
    manifest = {
        "sessions": sum(int(item["sessions"]) for item in manifests),
        "operations": sum(int(item["operations"]) for item in manifests),
        "turns": sum(int(item["turns"]) for item in manifests),
    }
    require(len(sessions) == manifest["sessions"], "packet session count")
    require(
        sum(int(packet["operation_count"]) for packet in sessions.values())
        == int(manifest["operations"]),
        "packet operation count",
    )
    require(
        sum(int(packet["turn_count"]) for packet in sessions.values())
        == int(manifest["turns"]),
        "packet turn count",
    )
    return sessions, manifest


def load_annotations(
    annotation_dirs: list[Path], expected_sessions: int, override_paths: list[Path] | None = None
) -> dict[str, dict[str, Any]]:
    sessions: dict[str, dict[str, Any]] = {}
    for annotation_dir in annotation_dirs:
        for path in sorted(annotation_dir.glob("batch-*.json")):
            payload = read_json(path)
            require(set(payload) == {"batch", "sessions"}, f"unexpected keys: {path}")
            for annotation in payload["sessions"]:
                session = str(annotation["session"])
                require(session not in sessions, f"duplicate annotation session: {session}")
                sessions[session] = annotation
    require(len(sessions) == expected_sessions, "annotation session count")
    for path in override_paths or []:
        payload = read_json(path)
        require(set(payload) == {"backend", "sessions"}, f"unexpected override keys: {path}")
        require(payload["backend"] == "automatic-main-agent", f"unexpected override backend: {path}")
        for annotation in payload["sessions"]:
            session = str(annotation["session"])
            require(session in sessions, f"unknown override session: {session}")
            sessions[session] = annotation
    return sessions


def validate_and_merge_marks(
    packets: dict[str, dict[str, Any]],
    annotations: dict[str, dict[str, Any]],
    task_names: dict[str, str],
    canonical_task_roots: dict[str, str],
    canonical_semantic_labels: dict[str, str],
    contract_root_only_prefix: bool = False,
) -> tuple[dict[str, Any], dict[str, list[dict[str, Any]]], list[str]]:
    require(set(packets) == set(annotations), "packet/annotation session mismatch")
    names: dict[str, str] = {}
    display_ids: dict[str, str] = {}
    marks = []
    normalized: dict[str, list[dict[str, Any]]] = {}
    findings = []

    for session in sorted(packets):
        packet = packets[session]
        annotation = annotations[session]
        turns = packet["turns"]
        turn_ids = [str(turn["first_operation_id"]) for turn in turns]
        turn_positions = {operation_id: index for index, operation_id in enumerate(turn_ids)}
        annotated = annotation.get("marks")
        require(isinstance(annotated, list) and annotated, f"empty marks: {session}")
        annotated = [dict(mark) for mark in annotated]
        if contract_root_only_prefix and len(annotated) >= 2:
            first_path = annotated[0].get("semantic_path")
            second_path = annotated[1].get("semantic_path")
            if (
                isinstance(first_path, list)
                and len(first_path) == 1
                and isinstance(second_path, list)
                and len(second_path) > 1
                and second_path[0] == first_path[0]
                and str(annotated[1].get("start_operation_id"))
                == str(turns[1]["first_operation_id"])
            ):
                annotated[0]["semantic_path"] = list(second_path)
                annotated.pop(1)
        starts = [str(mark["start_operation_id"]) for mark in annotated]
        require(starts[0] == turn_ids[0], f"missing first mark: {session}")
        require(all(start in turn_positions for start in starts), f"unknown mark: {session}")
        positions = [turn_positions[start] for start in starts]
        require(positions == sorted(set(positions)), f"unordered marks: {session}")

        task_name = task_names[session]
        declared_root = canonical_task_roots.get(task_name)
        session_marks = []
        previous_path: list[str] | None = None
        for mark in annotated:
            path = mark.get("semantic_path")
            require(isinstance(path, list) and path, f"empty semantic path: {session}")
            labels = []
            for depth, raw_label in enumerate(path):
                require(isinstance(raw_label, str), f"non-string label: {session}")
                label = " ".join(raw_label.split()).strip()
                require(bool(label), f"blank label: {session}")
                if depth == 0 and declared_root is not None:
                    label = declared_root
                label = canonical_semantic_labels.get(label, label)
                # pprof frame names are case-insensitive.  Canonicalize here so
                # independently produced labels such as "Inspect repository"
                # and "inspect repository" share one semantic ID instead of
                # colliding only when the completed profile is serialized.
                label = label.casefold()
                operation_id = semantic_id(label)
                require(
                    names.setdefault(operation_id, label) == label,
                    "semantic hash collision",
                )
                require(
                    display_ids.setdefault(label, operation_id) == operation_id,
                    "semantic display collision",
                )
                labels.append((operation_id, label))
            normalized_path = [label for _, label in labels]
            if normalized_path == previous_path:
                continue
            previous_path = normalized_path
            session_mark = {
                "sequence": session,
                "start_operation_id": str(mark["start_operation_id"]),
                "operation_ids": [operation_id for operation_id, _ in labels],
            }
            marks.append(session_mark)
            session_marks.append(
                {
                    **session_mark,
                    "semantic_path": normalized_path,
                }
            )
        normalized[session] = session_marks
        for finding in annotation.get("findings", []):
            require(isinstance(finding, str) and finding.strip(), f"bad finding: {session}")
            findings.append(f"{session}: {finding.strip()}")

    return (
        {
            "sequence_field": "traj_id",
            "id_field": "step_id",
            "operation_names": dict(sorted(names.items())),
            "marks": marks,
        },
        normalized,
        findings,
    )


def allocate_provider_tokens(
    usage_rows: list[dict[str, Any]], selected: set[str]
) -> tuple[dict[tuple[str, int], int], dict[tuple[str, int], dict[str, Any]]]:
    selected_rows = [row for row in usage_rows if str(row["session"]) in selected]
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    metadata: dict[tuple[str, int], dict[str, Any]] = {}
    for row in selected_rows:
        key = (str(row["session"]), int(row["step_id"]))
        require(key not in metadata, f"duplicate usage row: {key}")
        metadata[key] = row
        groups[str(row["response_id"])].append(row)

    weights: dict[tuple[str, int], int] = {}
    for response_id, rows in groups.items():
        rows.sort(key=lambda row: (str(row["session"]), int(row["step_id"])))
        declared_counts = {int(row["response_operation_count"]) for row in rows}
        declared_totals = {int(row["response_total_tokens"]) for row in rows}
        require(declared_counts == {len(rows)}, f"response count mismatch: {response_id}")
        require(len(declared_totals) == 1, f"response token mismatch: {response_id}")
        total = next(iter(declared_totals))
        require(total >= len(rows), f"nonpositive per-operation token share: {response_id}")
        quotient, remainder = divmod(total, len(rows))
        for index, row in enumerate(rows):
            key = (str(row["session"]), int(row["step_id"]))
            weights[key] = quotient + (1 if index < remainder else 0)
        require(sum(weights[(str(row["session"]), int(row["step_id"]))] for row in rows) == total,
                f"token conservation failure: {response_id}")
    return weights, metadata


def operation_turns(
    packets: dict[str, dict[str, Any]], expected_operations: int
) -> dict[tuple[str, int], dict[str, Any]]:
    result = {}
    for session, packet in packets.items():
        for turn in packet["turns"]:
            for operation_id in turn["operation_ids"]:
                key = (session, int(operation_id))
                require(key not in result, f"duplicate packet operation: {key}")
                result[key] = turn
    require(len(result) == expected_operations, "packet operation coverage")
    return result


def packet_operation_order(packets: dict[str, dict[str, Any]]) -> dict[str, list[int]]:
    return {
        session: [
            int(operation_id)
            for turn in packet["turns"]
            for operation_id in turn["operation_ids"]
        ]
        for session, packet in packets.items()
    }


def validate_source_order(
    count_rows: list[dict[str, Any]], expected_order: dict[str, list[int]]
) -> None:
    observed_order: dict[str, list[int]] = defaultdict(list)
    for row in count_rows:
        observed_order[str(row["fields"]["traj_id"])].append(
            int(row["fields"]["step_id"])
        )
    require(dict(observed_order) == expected_order, "target/packet source order mismatch")


def enrich_operations(
    target_rows: list[dict[str, Any]],
    packets: dict[str, dict[str, Any]],
    usage_metadata: dict[tuple[str, int], dict[str, Any]],
    token_weights: dict[tuple[str, int], int],
    expected_operations: int,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    selected = set(packets)
    turns = operation_turns(packets, expected_operations)
    expected_order = packet_operation_order(packets)
    count_rows = []
    token_rows = []
    seen = set()
    for target in target_rows:
        fields = dict(target["fields"])
        session = str(fields["traj_id"])
        if session not in selected:
            continue
        step = int(fields["step_id"])
        key = (session, step)
        require(key not in seen, f"duplicate target operation: {key}")
        seen.add(key)
        require(key in turns and key in usage_metadata and key in token_weights,
                f"missing joined source operation: {key}")
        packet = packets[session]
        usage = usage_metadata[key]
        turn = turns[key]
        require(str(usage["framework"]) == str(packet["framework"]), f"framework mismatch: {key}")
        require(str(usage["source_ref"]) == str(fields["source_ref"]), f"source mismatch: {key}")
        fields.update(
            {
                "project": "codetracebench",
                "agent": str(packet["framework"]),
                "session": session,
                "prompt": str(usage["task_name"]),
                "call": str(usage["response_id"]),
                "tool": str(fields["raw_action_key"]),
                "source_kind": "tool",
                "source_session": session,
                "call_id": str(usage["response_id"]),
                "prompt_hash": prompt_hash(str(packet["task"])),
                "evidence_id": f"{session}:{step}",
            }
        )
        count_rows.append({"value": 1, "fields": fields})
        token_rows.append({"value": token_weights[key], "fields": fields})
    validate_source_order(count_rows, expected_order)
    require(len(seen) == expected_operations, "selected target operation count")
    require(set(turns) == seen == set(token_weights), "joined operation coverage")
    return count_rows, token_rows


def expand_predictions(
    count_rows: list[dict[str, Any]], mark_file: dict[str, Any], expected_operations: int
) -> list[dict[str, Any]]:
    names = mark_file["operation_names"]
    marks_by_session: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for mark in mark_file["marks"]:
        marks_by_session[str(mark["sequence"])].append(mark)
    for marks in marks_by_session.values():
        marks.sort(key=lambda mark: int(mark["start_operation_id"]))

    rows_by_session: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in count_rows:
        rows_by_session[str(row["fields"]["traj_id"])].append(row)
    predictions = []
    for session in sorted(rows_by_session):
        rows = sorted(rows_by_session[session], key=lambda row: int(row["fields"]["step_id"]))
        marks = marks_by_session[session]
        mark_index = 0
        active = marks[0]
        for row in rows:
            fields = row["fields"]
            step = int(fields["step_id"])
            while (
                mark_index + 1 < len(marks)
                and int(marks[mark_index + 1]["start_operation_id"]) <= step
            ):
                mark_index += 1
                active = marks[mark_index]
            operation_ids = [str(value) for value in active["operation_ids"]]
            predictions.append(
                {
                    "session": session,
                    "framework": str(fields["agent"]),
                    "step_id": step,
                    "source_ref": str(fields["source_ref"]),
                    "operation_ids": operation_ids,
                    "semantic_stack": [
                        {"operation_id": operation_id, "label": names[operation_id]}
                        for operation_id in operation_ids
                    ],
                    "task_occurrence_instance": f"{session}:mark-{mark_index:04d}",
                    "source_turn_id": str(fields["call"]),
                    "source_turn_instance": f"{session}:turn:{fields['call']}",
                }
            )
    require(len(predictions) == expected_operations, "prediction operation coverage")
    return predictions


def main() -> None:
    args = parse_args()
    packets, packet_manifest = load_packets(args.packet_dir)
    expected_sessions = int(packet_manifest["sessions"])
    expected_operations = int(packet_manifest["operations"])
    expected_turns = int(packet_manifest["turns"])
    annotations = load_annotations(
        args.annotation_dir, expected_sessions, args.annotation_override
    )
    target_rows = read_jsonl(args.target_operations)
    usage_rows = read_jsonl(args.operation_usage)
    canonical_names = read_json(args.canonical_names)
    require(isinstance(canonical_names, dict), "canonical name map must be an object")
    require(
        set(canonical_names) == {"task_roots", "semantic_labels"},
        "canonical name map keys",
    )
    canonical_task_roots = canonical_names["task_roots"]
    canonical_semantic_labels = canonical_names["semantic_labels"]
    require(isinstance(canonical_task_roots, dict), "canonical task roots must be an object")
    require(
        isinstance(canonical_semantic_labels, dict),
        "canonical semantic labels must be an object",
    )

    selected = set(packets)
    token_weights, usage_metadata = allocate_provider_tokens(usage_rows, selected)
    task_names = {}
    for (session, _), row in usage_metadata.items():
        task_name = str(row["task_name"])
        require(
            task_names.setdefault(session, task_name) == task_name,
            f"inconsistent task family: {session}",
        )
    require(
        set(canonical_task_roots).issubset(set(task_names.values())),
        "unknown canonical task family",
    )
    mark_file, normalized, findings = validate_and_merge_marks(
        packets,
        annotations,
        task_names,
        canonical_task_roots,
        canonical_semantic_labels,
        args.contract_root_only_prefix,
    )
    count_rows, token_rows = enrich_operations(
        target_rows, packets, usage_metadata, token_weights, expected_operations
    )
    predictions = expand_predictions(count_rows, mark_file, expected_operations)

    if args.mode == "full":
        require(expected_sessions == FULL_SESSIONS, "full session coverage")
        require(expected_operations == FULL_OPERATIONS, "full operation coverage")
        require(expected_turns == FULL_TURNS, "full turn coverage")

    out = args.out
    write_json(out / "operation-marks.json", mark_file)
    write_jsonl(out / "operations-count.jsonl", count_rows)
    write_jsonl(out / "operations-tokens.jsonl", token_rows)
    write_jsonl(out / "predictions.jsonl", predictions)
    write_json(out / "normalized-agent-annotations.json", normalized)
    (out / "findings.md").write_text(
        "# Source-grounded automatic Agent findings\n\n"
        + "\n".join(f"- {finding}" for finding in findings)
        + "\n",
        encoding="utf-8",
    )
    summary = {
        "sessions": len(packets),
        "operations": len(count_rows),
        "turns": sum(int(packet["turn_count"]) for packet in packets.values()),
        "marks": len(mark_file["marks"]),
        "semantic_names": len(mark_file["operation_names"]),
        "findings": len(findings),
        "path_depths": {
            str(expected_depth): sum(
                1
                for session_marks in normalized.values()
                for mark in session_marks
                if len(mark["semantic_path"]) == expected_depth
            )
            for expected_depth in sorted(
                {
                    len(mark["semantic_path"])
                    for session_marks in normalized.values()
                    for mark in session_marks
                }
            )
        },
        "operation_count_mass": sum(row["value"] for row in count_rows),
        "provider_token_mass": sum(row["value"] for row in token_rows),
        "canonicalized_task_families": canonical_task_roots,
        "canonicalized_semantic_labels": canonical_semantic_labels,
        "contract_root_only_prefix": args.contract_root_only_prefix,
    }
    write_json(out / "summary.json", summary)
    write_json(
        out / "inference-summary.json",
        {
            "schema": "agentsight.external-agent-operation-annotation.inference.v1",
            "algorithm_version": "automatic-agent-sparse-complete-path-v1",
            "mode": args.mode,
            "status": "complete",
            "sessions": len(packets),
            "turns": summary["turns"],
            "operations": len(predictions),
            "frameworks": {
                framework: sum(
                    1 for packet in packets.values() if packet["framework"] == framework
                )
                for framework in sorted({str(packet["framework"]) for packet in packets.values()})
            },
            "official_manifest_opened": False,
            "official_stages_opened": False,
            "configured_depth_or_leaf_cap": False,
            "annotation_backend": "independent Codex subagent batches with root validation",
            "main_agent_override_sessions": sum(
                len(read_json(path)["sessions"]) for path in args.annotation_override
            ),
            "contract_root_only_prefix": args.contract_root_only_prefix,
        },
    )
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
