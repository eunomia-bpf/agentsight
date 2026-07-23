#!/usr/bin/env python3
"""Score source-native, recurrence, and automatic-Agent RQ2 groupings.

Group construction is completed and written before this command opens any
benchmark target or localizer signal.  AgentPProf remains the implementation
under test: N1 is induced by the release CLI, while N0 and A0 replay through
the same sparse operation-mark interface and produce standard pprof files.
The scorer then reuses each workload's existing per-query AP/MAP protocol.
"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import hashlib
import json
import math
from pathlib import Path
import re
import statistics
import subprocess
from typing import Any, Iterable, Mapping, Sequence

from sklearn.metrics import average_precision_score


ROOT = Path(__file__).resolve().parents[1]
METHODS = (
    "native_tree",
    "recurrence",
    "automatic_agent",
    "source_preserving_agent",
)
EXPECTED_HISTORICAL_MAP = {
    "agentprocess": 0.788919404004148,
    "hint": 0.45285157726449404,
    "trace": 0.23016832132386486,
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--benchmark", choices=("agentprocess", "hint", "trace"), required=True
    )
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--packet-dir", type=Path, required=True)
    parser.add_argument("--annotation-dir", type=Path, required=True)
    parser.add_argument(
        "--recurrence-reference-packet-dir",
        type=Path,
        help="source-only complete population used by N1; defaults to --packet-dir",
    )
    parser.add_argument(
        "--binary",
        type=Path,
        default=ROOT / "agentpprof" / "target" / "release" / "agentpprof",
    )
    parser.add_argument("--mode", choices=("preflight", "full"), required=True)
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


def write_jsonl(path: Path, rows: Iterable[Mapping[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as stream:
        for row in rows:
            stream.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def load_packets(path: Path) -> dict[str, dict[str, Any]]:
    packets: dict[str, dict[str, Any]] = {}
    for batch_path in sorted(path.glob("batch-*.json")):
        payload = read_json(batch_path)
        require(
            str(payload.get("schema")) == "agentsight.rq2-agent-annotation-packet.v1",
            f"{batch_path}: schema",
        )
        for packet in payload["sessions"]:
            sequence = str(packet["sequence"])
            require(sequence not in packets, f"duplicate packet sequence: {sequence}")
            operations = packet.get("operations")
            require(isinstance(operations, list) and operations, f"{sequence}: operations")
            ids = [str(row["operation_id"]) for row in operations]
            require(len(ids) == len(set(ids)), f"{sequence}: duplicate operation ID")
            require(
                [int(row["ordinal"]) for row in operations] == list(range(len(operations))),
                f"{sequence}: non-contiguous ordinals",
            )
            require(int(packet["operation_count"]) == len(operations), f"{sequence}: count")
            packets[sequence] = packet
    require(bool(packets), f"no packets in {path}")
    return packets


def load_annotations(
    path: Path, packets: Mapping[str, Mapping[str, Any]]
) -> dict[str, dict[str, Any]]:
    annotations: dict[str, dict[str, Any]] = {}
    for batch_path in sorted(path.glob("batch-*.json")):
        payload = read_json(batch_path)
        require(set(payload) == {"batch", "sessions"}, f"{batch_path}: top-level keys")
        for annotation in payload["sessions"]:
            sequence = str(annotation["sequence"])
            require(sequence not in annotations, f"duplicate annotation: {sequence}")
            annotations[sequence] = annotation
    require(set(annotations) == set(packets), "packet/annotation sequence mismatch")
    return annotations


def normalize_path(raw: Any, sequence: str) -> tuple[str, ...]:
    require(isinstance(raw, list) and raw, f"{sequence}: empty semantic path")
    path = []
    for item in raw:
        require(isinstance(item, str), f"{sequence}: non-string semantic path")
        value = " ".join(item.split()).strip().casefold()
        require(bool(value), f"{sequence}: blank semantic path")
        path.append(value)
    return tuple(path)


def expand_annotations(
    packets: Mapping[str, Mapping[str, Any]],
    annotations: Mapping[str, Mapping[str, Any]],
) -> dict[str, tuple[str, ...]]:
    result: dict[str, tuple[str, ...]] = {}
    for sequence in sorted(packets):
        operations = packets[sequence]["operations"]
        ids = [str(row["operation_id"]) for row in operations]
        positions = {operation_id: index for index, operation_id in enumerate(ids)}
        marks = annotations[sequence].get("marks")
        require(isinstance(marks, list) and marks, f"{sequence}: empty marks")
        starts = [str(mark["start_operation_id"]) for mark in marks]
        require(starts[0] == ids[0], f"{sequence}: first mark")
        require(all(start in positions for start in starts), f"{sequence}: unknown mark")
        offsets = [positions[start] for start in starts]
        require(offsets == sorted(set(offsets)), f"{sequence}: mark order")
        paths = [normalize_path(mark.get("semantic_path"), sequence) for mark in marks]
        require(
            all(left != right for left, right in zip(paths, paths[1:])),
            f"{sequence}: adjacent duplicate path",
        )
        for index, (start, path) in enumerate(zip(offsets, paths, strict=True)):
            end = offsets[index + 1] if index + 1 < len(offsets) else len(ids)
            for operation_id in ids[start:end]:
                require(operation_id not in result, f"duplicate expanded ID: {operation_id}")
                result[operation_id] = path
    expected = {
        str(operation["operation_id"])
        for packet in packets.values()
        for operation in packet["operations"]
    }
    require(set(result) == expected, "expanded annotation coverage")
    return result


def native_paths(
    packets: Mapping[str, Mapping[str, Any]]
) -> dict[str, tuple[str, ...]]:
    result = {}
    for packet in packets.values():
        for operation in packet["operations"]:
            operation_id = str(operation["operation_id"])
            path = tuple(str(value).strip().casefold() for value in operation["native_path"])
            require(bool(path) and all(path), f"{operation_id}: native path")
            result[operation_id] = path
    return result


def recurrence_fields(packet: Mapping[str, Any], operation: Mapping[str, Any]) -> tuple[str, str]:
    path = [str(value) for value in operation["native_path"]]
    benchmark = str(packet["benchmark"])
    if benchmark in {"AgentProcessBench", "HINTBench"}:
        require(len(path) >= 4, f"{operation['operation_id']}: short native path")
        action = path[3]
    elif benchmark == "TraceElephant":
        require(len(path) >= 3, f"{operation['operation_id']}: short native path")
        action = path[2]
    else:
        raise RuntimeError(f"unknown packet benchmark: {benchmark}")
    detail = json.dumps(path, ensure_ascii=False, separators=(",", ":"))
    return action, detail


def recurrence_input_rows(
    packets: Mapping[str, Mapping[str, Any]]
) -> list[dict[str, Any]]:
    rows = []
    for sequence in sorted(packets):
        packet = packets[sequence]
        for operation in packet["operations"]:
            action, detail = recurrence_fields(packet, operation)
            rows.append(
                {
                    "value": 1,
                    "fields": {
                        "session": sequence,
                        "source_session": sequence,
                        "evidence_id": str(operation["operation_id"]),
                        "action": action,
                        "action_detail": detail,
                    },
                }
            )
    return rows


def parse_pprof_operation_assignments(raw: str) -> dict[str, str]:
    sample_rows: list[tuple[str, list[int]]] = []
    location_names: dict[int, str] = {}
    section = ""
    pending_locations: list[int] | None = None
    for line in raw.splitlines():
        if line == "Samples:":
            section = "samples"
            continue
        if line == "Locations":
            section = "locations"
            pending_locations = None
            continue
        if line in {"Mappings", "Functions"}:
            section = line.casefold()
            pending_locations = None
            continue
        if section == "samples":
            match = re.match(r"^\s*(-?\d+):\s+([0-9 ]+)\s*$", line)
            if match:
                require(int(match.group(1)) == 1, "N1 sample mass is not one")
                pending_locations = [int(value) for value in match.group(2).split()]
                continue
            if pending_locations is not None and "evidence_id:[" in line:
                match = re.search(r"evidence_id:\[([^\]]+)\]", line)
                require(match is not None, "N1 sample lacks evidence ID")
                sample_rows.append((match.group(1), pending_locations))
                pending_locations = None
        elif section == "locations":
            match = re.match(r"^\s*(\d+):.*\soperation:(\S+)\s+agentpprof:", line)
            if match:
                location_names[int(match.group(1))] = match.group(2)
    result = {}
    for operation_id, locations in sample_rows:
        names = [location_names[location] for location in locations if location in location_names]
        require(len(names) == 1, f"{operation_id}: N1 operation stack is not one frame")
        require(operation_id not in result, f"duplicate N1 operation ID: {operation_id}")
        result[operation_id] = names[0]
    require(bool(result), "N1 pprof yielded no operation assignments")
    return result


def pprof_safe_label(value: str) -> str:
    output = []
    previous_underscore = False
    for character in value.casefold():
        if character.isalnum() or character in "._:/+-":
            output.append(character)
            previous_underscore = False
        elif not previous_underscore:
            output.append("_")
            previous_underscore = True
    normalized = "".join(output).strip("_;")
    return normalized or "unknown"


def run_recurrence(
    binary: Path,
    packets: Mapping[str, Mapping[str, Any]],
    reference_packets: Mapping[str, Mapping[str, Any]],
    out: Path,
) -> tuple[dict[str, tuple[str, ...]], dict[str, Any]]:
    input_path = out / "recurrence-input.jsonl"
    reference_path = out / "recurrence-reference.jsonl"
    profile_path = out / "recurrence-induced.pb.gz"
    raw_path = out / "recurrence-induced.pprof-raw.txt"
    write_jsonl(input_path, recurrence_input_rows(packets))
    write_jsonl(reference_path, recurrence_input_rows(reference_packets))
    command = [
        str(binary.resolve()),
        "--operation-file",
        str(input_path.resolve()),
        "--view",
        "operations",
        "--induce-operation-stack",
        "--induce-reference-operation-file",
        str(reference_path.resolve()),
        "--deterministic-output",
        "-o",
        str(profile_path.resolve()),
    ]
    completed = subprocess.run(
        command, cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    write_json(out / "recurrence-induced-command.json", command)
    (out / "recurrence-induced-stdout.json").write_text(
        completed.stdout, encoding="utf-8"
    )
    (out / "recurrence-induced-stderr.txt").write_text(
        completed.stderr, encoding="utf-8"
    )
    require(completed.returncode == 0, f"N1 AgentPProf failed: {completed.stderr}")
    status = json.loads(completed.stdout)
    require(int(status["operations"]) == sum(
        int(packet["operation_count"]) for packet in packets.values()
    ), "N1 operation count")
    pprof = subprocess.run(
        ["go", "tool", "pprof", "-raw", str(profile_path.resolve())],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    require(pprof.returncode == 0, f"go tool pprof failed: {pprof.stderr}")
    raw_path.write_text(pprof.stdout, encoding="utf-8")
    normalized_assignments = parse_pprof_operation_assignments(pprof.stdout)
    expected = {
        str(operation["operation_id"])
        for packet in packets.values()
        for operation in packet["operations"]
    }
    normalized_expected = {}
    for operation_id in expected:
        normalized = pprof_safe_label(operation_id)
        require(normalized not in normalized_expected, "normalized evidence ID collision")
        normalized_expected[normalized] = operation_id
    require(
        set(normalized_assignments) == set(normalized_expected),
        "N1 normalized assignment coverage",
    )
    assignments = {
        normalized_expected[normalized]: motif
        for normalized, motif in normalized_assignments.items()
    }
    require(set(assignments) == expected, "N1 assignment coverage")
    paths = {}
    for packet in packets.values():
        for operation in packet["operations"]:
            operation_id = str(operation["operation_id"])
            paths[operation_id] = (assignments[operation_id],)
    return paths, status


def semantic_id(label: str) -> str:
    return "op-" + hashlib.sha256(label.encode()).hexdigest()[:24]


def mark_file_for_paths(
    packets: Mapping[str, Mapping[str, Any]], paths: Mapping[str, tuple[str, ...]]
) -> dict[str, Any]:
    names: dict[str, str] = {}
    display_ids: dict[str, str] = {}
    marks = []
    for sequence in sorted(packets):
        previous: tuple[str, ...] | None = None
        for operation in packets[sequence]["operations"]:
            operation_id = str(operation["operation_id"])
            path = paths[operation_id]
            if path == previous:
                continue
            previous = path
            ids = []
            for raw_label in path:
                label = " ".join(raw_label.split()).strip().casefold()
                identifier = semantic_id(label)
                require(names.setdefault(identifier, label) == label, "semantic hash collision")
                require(
                    display_ids.setdefault(label, identifier) == identifier,
                    "semantic display collision",
                )
                ids.append(identifier)
            marks.append(
                {
                    "sequence": sequence,
                    "start_operation_id": operation_id,
                    "operation_ids": ids,
                }
            )
    return {
        "sequence_field": "session",
        "id_field": "operation_id",
        "operation_names": dict(sorted(names.items())),
        "marks": marks,
    }


def product_rows(packets: Mapping[str, Mapping[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for sequence in sorted(packets):
        packet = packets[sequence]
        agent, dataset = population_context(packet)
        for operation in packet["operations"]:
            call_kind, source_call, outcome = source_leaf_frames(packet, operation)
            fields = {
                "project": str(packet["benchmark"]),
                "dataset": dataset,
                "session": sequence,
                "source_session": sequence,
                "prompt": str(packet["task"]),
                "call": call_kind,
                "call_id": str(operation["ordinal"]),
                "source_kind": call_kind,
                "tool": source_call,
                "outcome": outcome,
                "operation_id": str(operation["operation_id"]),
                "evidence_id": str(operation["operation_id"]),
            }
            if agent:
                fields["agent"] = agent
            rows.append(
                {
                    "value": 1,
                    "fields": fields,
                }
            )
    return rows


def population_context(packet: Mapping[str, Any]) -> tuple[str, str]:
    """Separate experimental agent and dataset context from semantic paths."""
    family = str(packet["task_family"]).strip()
    if str(packet["benchmark"]) == "TraceElephant" and "/" in family:
        agent, dataset = family.split("/", 1)
        return agent.strip(), dataset.strip()
    return "", family


def source_leaf_frames(
    packet: Mapping[str, Any], operation: Mapping[str, Any]
) -> tuple[str, str, str]:
    """Return structured original-event fields retained below semantic operations."""
    native = [str(value).strip().casefold() for value in operation["native_path"]]
    benchmark = str(packet["benchmark"])
    if benchmark in {"AgentProcessBench", "HINTBench"}:
        require(len(native) >= 4, f"{operation['operation_id']}: short native path")
        source_kind = native[-3]
        source_call = native[-2]
        if source_call == "none" and len(native) >= 4:
            source_call = native[-4]
    elif benchmark == "TraceElephant":
        require(len(native) >= 4, f"{operation['operation_id']}: short native path")
        source_kind = native[2]
        source_call = native[3]
    else:
        raise RuntimeError(f"unknown packet benchmark: {benchmark}")
    require(bool(source_kind) and bool(source_call), "empty source leaf frame")
    outcome = native[-1]
    require(bool(outcome), "empty source outcome")
    return source_kind, source_call, outcome


def replay_marked_profile(
    method: str,
    binary: Path,
    packets: Mapping[str, Mapping[str, Any]],
    paths: Mapping[str, tuple[str, ...]],
    out: Path,
    *,
    stack: str = "project,operation",
) -> dict[str, Any]:
    operation_path = out / "source-operations.jsonl"
    write_jsonl(operation_path, product_rows(packets))
    mark_path = out / f"{method}-marks.json"
    profile_path = out / f"{method}.pb.gz"
    write_json(mark_path, mark_file_for_paths(packets, paths))
    command = [
        str(binary.resolve()),
        "--operation-file",
        str(operation_path.resolve()),
        "--operation-mark-file",
        str(mark_path.resolve()),
        "--stack",
        stack,
        "--view",
        "operations",
        "--deterministic-output",
        "-o",
        str(profile_path.resolve()),
    ]
    completed = subprocess.run(
        command, cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    write_json(out / f"{method}-command.json", command)
    (out / f"{method}-stdout.json").write_text(completed.stdout, encoding="utf-8")
    (out / f"{method}-stderr.txt").write_text(completed.stderr, encoding="utf-8")
    require(completed.returncode == 0, f"{method} AgentPProf failed: {completed.stderr}")
    status = json.loads(completed.stdout)
    expected = sum(int(packet["operation_count"]) for packet in packets.values())
    require(int(status["operations"]) == expected, f"{method}: operation count")
    require(int(status["samples"]) == expected, f"{method}: mass")
    opened = subprocess.run(
        ["go", "tool", "pprof", "-top", str(profile_path.resolve())],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    require(opened.returncode == 0, f"{method}: stock pprof open failed")
    (out / f"{method}-pprof-top.txt").write_text(opened.stdout, encoding="utf-8")
    return status


def fixed_group_rows(
    packets: Mapping[str, Mapping[str, Any]],
    path_by_method: Mapping[str, Mapping[str, tuple[str, ...]]],
) -> list[dict[str, Any]]:
    rows = []
    for sequence in sorted(packets):
        packet = packets[sequence]
        for operation in packet["operations"]:
            operation_id = str(operation["operation_id"])
            rows.append(
                {
                    "operation_id": operation_id,
                    "sequence": sequence,
                    "task_family": str(packet["task_family"]),
                    "groups": {
                        method: list(path_by_method[method][operation_id])
                        for method in METHODS
                    },
                }
            )
    return rows


def load_signals_after_groups(
    benchmark: str, root: Path, fixed: Sequence[Mapping[str, Any]]
) -> list[dict[str, Any]]:
    wanted = {str(row["operation_id"]) for row in fixed}
    if benchmark == "agentprocess":
        sources = {
            str(row["operation_id"]): row
            for row in read_jsonl(root / "group-assignments.jsonl")
        }
        labels = {
            str(row["operation_id"]): int(row["human_label"])
            for row in read_jsonl(root / "labels.jsonl")
        }
        require(wanted <= set(sources) and wanted <= set(labels), "AgentProcess coverage")
        return [
            {
                "operation_id": operation_id,
                "query_id": str(sources[operation_id]["trajectory_id"]),
                "label": int(labels[operation_id] == -1),
                "local_signal": float(sources[operation_id]["risk_units"]),
            }
            for operation_id in wanted
        ]
    if benchmark == "hint":
        projections = {
            str(row["operation_id"]): row
            for row in read_jsonl(root / "operations" / "test-projection.jsonl")
        }
        target_sets: dict[str, set[int]] = {}
        for source in read_json(root / "sources" / "test.json"):
            query_id = f"test:{source['id']}"
            values = set()
            for field in ("injected_risks", "risk_labels"):
                for annotation in source.get(field, []):
                    value = annotation.get("risk_origin_step")
                    if value is None:
                        value = annotation.get("step_id")
                    require(isinstance(value, int) and not isinstance(value, bool),
                            f"{query_id}: invalid target")
                    values.add(value)
            target_sets[query_id] = values
        require(wanted <= set(projections), "HINT coverage")
        return [
            {
                "operation_id": operation_id,
                "query_id": str(projections[operation_id]["record_key"]),
                "label": int(
                    int(projections[operation_id]["display_id"])
                    in target_sets[str(projections[operation_id]["record_key"])]
                ),
                "local_signal": float(int(projections[operation_id]["localizer_hit"])),
            }
            for operation_id in wanted
        ]
    if benchmark == "trace":
        projections = {
            str(row["operation_id"]): row
            for row in read_jsonl(root / "operations" / "projection.jsonl")
        }
        targets = {
            str(row["trace_id"]): int(row["mistake_step"])
            for row in read_jsonl(root / "scorer" / "targets.jsonl")
        }
        require(wanted <= set(projections), "Trace coverage")
        return [
            {
                "operation_id": operation_id,
                "query_id": str(projections[operation_id]["trace_id"]),
                "label": int(
                    int(projections[operation_id]["step_id"])
                    == targets[str(projections[operation_id]["trace_id"])]
                ),
                "local_signal": float(int(projections[operation_id]["localizer_hit"])),
            }
            for operation_id in wanted
        ]
    raise RuntimeError(f"unknown benchmark: {benchmark}")


def wilson_lower(hits: int, count: int, *, exact_zero: bool) -> float:
    require(count > 0 and 0 <= hits <= count, "invalid Wilson inputs")
    # Preserve each workload's already-published scorer exactly.  TraceElephant
    # canonicalizes a zero-hit group to +0.0; HINTBench evaluates the formula
    # directly, whose floating-point cancellation leaves signed near-zero values.
    if exact_zero and hits == 0:
        return 0.0
    z = 1.959963984540054
    proportion = hits / count
    z2 = z * z
    return (
        proportion
        + z2 / (2.0 * count)
        - z
        * math.sqrt(
            proportion * (1.0 - proportion) / count
            + z2 / (4.0 * count * count)
        )
    ) / (1.0 + z2 / count)


def historical_agentprof_paths(benchmark: str, root: Path) -> dict[str, tuple[str, ...]]:
    if benchmark == "agentprocess":
        return {
            str(row["operation_id"]): (
                str(row["family"]),
                str(row["groups"]["semantic"]),
            )
            for row in read_jsonl(root / "group-assignments.jsonl")
        }
    if benchmark == "hint":
        rows = read_jsonl(root / "operations" / "test-projection.jsonl")
        point = read_json(root / "metrics" / "test-point-estimates.json")
        order = [str(value) for value in point["selected_order"]]
        identity = read_json(
            root / "profiles" / "test" / "__".join(order) / "identity.json"
        )
        leaves = [str(value) for value in identity["operation_leaves"]]
        require(len(rows) == len(leaves), "HINT historical path coverage")
        return {
            str(row["operation_id"]): tuple(leaf.split(";"))
            for row, leaf in zip(rows, leaves, strict=True)
        }
    if benchmark == "trace":
        rows = read_jsonl(root / "operations" / "projection.jsonl")
        method = read_json(root / "profiles" / "method-index.json")["methods"]["agentprof"]
        leaves = [str(value) for value in method["operation_leaves"]]
        require(len(rows) == len(leaves), "Trace historical path coverage")
        return {
            str(row["operation_id"]): tuple(leaf.split(";"))
            for row, leaf in zip(rows, leaves, strict=True)
        }
    raise RuntimeError(f"unknown benchmark: {benchmark}")


def scores_for_method(
    benchmark: str,
    fixed: Sequence[Mapping[str, Any]],
    signals: Sequence[Mapping[str, Any]],
    method: str,
) -> dict[str, float]:
    fixed_by_id = {str(row["operation_id"]): row for row in fixed}
    if benchmark == "agentprocess":
        sums: defaultdict[tuple[str, ...], float] = defaultdict(float)
        counts: Counter[tuple[str, ...]] = Counter()
        for signal in signals:
            operation_id = str(signal["operation_id"])
            path = tuple(fixed_by_id[operation_id]["groups"][method])
            sums[path] += float(signal["local_signal"])
            counts[path] += 1
        return {
            str(signal["operation_id"]): sums[
                tuple(fixed_by_id[str(signal["operation_id"])]["groups"][method])
            ]
            / counts[tuple(fixed_by_id[str(signal["operation_id"])]["groups"][method])]
            for signal in signals
        }

    prefix_counts: Counter[tuple[str, ...]] = Counter()
    prefix_hits: Counter[tuple[str, ...]] = Counter()
    for signal in signals:
        operation_id = str(signal["operation_id"])
        path = tuple(fixed_by_id[operation_id]["groups"][method])
        for depth in range(1, len(path) + 1):
            prefix = path[:depth]
            prefix_counts[prefix] += 1
            prefix_hits[prefix] += int(signal["local_signal"])
    cache = {
        prefix: wilson_lower(
            prefix_hits[prefix],
            prefix_counts[prefix],
            exact_zero=benchmark == "trace",
        )
        for prefix in prefix_counts
    }
    scores = {}
    for signal in signals:
        operation_id = str(signal["operation_id"])
        path = tuple(fixed_by_id[operation_id]["groups"][method])
        scores[operation_id] = max(cache[path[:depth]] for depth in range(1, len(path) + 1))
    return scores


def standard_ap(labels: Sequence[int], scores: Sequence[float]) -> float:
    require(len(labels) == len(scores) and bool(labels) and sum(labels) > 0, "AP inputs")
    return float(average_precision_score(labels, scores))


def map_for_one_method(
    signals: Sequence[Mapping[str, Any]], operation_scores: Mapping[str, float]
) -> tuple[float | None, int]:
    by_query: defaultdict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for row in signals:
        by_query[str(row["query_id"])].append(row)
    values = []
    for rows in by_query.values():
        labels = [int(row["label"]) for row in rows]
        if sum(labels) == 0:
            continue
        values.append(
            standard_ap(
                labels,
                [operation_scores[str(row["operation_id"])] for row in rows],
            )
        )
    return (statistics.fmean(values) if values else None), len(values)


def score(
    benchmark: str,
    fixed: Sequence[Mapping[str, Any]],
    signals: Sequence[Mapping[str, Any]],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    by_query: defaultdict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in signals:
        by_query[str(row["query_id"])].append(row)
    method_scores = {
        method: scores_for_method(benchmark, fixed, signals, method) for method in METHODS
    }
    query_rows = []
    for query_id in sorted(by_query):
        rows = by_query[query_id]
        labels = [int(row["label"]) for row in rows]
        if sum(labels) == 0:
            continue
        query_rows.append(
            {
                "query_id": query_id,
                "operations": len(rows),
                "targets": sum(labels),
                "ap": {
                    method: standard_ap(
                        labels,
                        [method_scores[method][str(row["operation_id"])] for row in rows],
                    )
                    for method in METHODS
                },
            }
        )
    summary = {
        "benchmark": benchmark,
        "operations": len(signals),
        "queries": len(by_query),
        "target_bearing_queries": len(query_rows),
        "mapped_targets": sum(int(row["label"]) for row in signals),
        "metric": "sklearn.metrics.average_precision_score per target-bearing query; arithmetic mean",
        "map": {
            method: statistics.fmean(row["ap"][method] for row in query_rows)
            if query_rows
            else None
            for method in METHODS
        },
    }
    return summary, query_rows


def main() -> None:
    args = parse_args()
    root = args.root.resolve()
    packet_dir = args.packet_dir.resolve()
    annotation_dir = args.annotation_dir.resolve()
    reference_dir = (
        args.recurrence_reference_packet_dir.resolve()
        if args.recurrence_reference_packet_dir
        else packet_dir
    )
    binary = args.binary.resolve()
    out = args.out.resolve()
    for path in (root, packet_dir, annotation_dir, reference_dir):
        require(path.exists(), f"missing input: {path}")
    require(binary.is_file(), f"missing AgentPProf binary: {binary}")

    packets = load_packets(packet_dir)
    references = load_packets(reference_dir)
    annotations = load_annotations(annotation_dir, packets)
    automatic = expand_annotations(packets, annotations)
    native = native_paths(packets)
    recurrence, _recurrence_induced_status = run_recurrence(
        binary, packets, references, out
    )
    automatic_semantic_paths = {
        operation_id: automatic[operation_id]
        for packet in packets.values()
        for operation_id in [str(row["operation_id"]) for row in packet["operations"]]
    }
    automatic_paths = {
        operation_id: (
            str(packet["task_family"]).strip().casefold(),
            *automatic_semantic_paths[operation_id],
        )
        for packet in packets.values()
        for operation_id in [str(row["operation_id"]) for row in packet["operations"]]
    }
    source_preserving_paths = {
        str(operation["operation_id"]): (
            *automatic_paths[str(operation["operation_id"])],
            *source_leaf_frames(packet, operation),
        )
        for packet in packets.values()
        for operation in packet["operations"]
    }
    paths = {
        "native_tree": native,
        "recurrence": {
            str(operation["operation_id"]): (
                str(packet["task_family"]).strip().casefold(),
                *recurrence[str(operation["operation_id"])],
            )
            for packet in packets.values()
            for operation in packet["operations"]
        },
        "automatic_agent": automatic_paths,
        "source_preserving_agent": source_preserving_paths,
    }
    expected = set(native)
    require(all(set(values) == expected for values in paths.values()), "method coverage")

    product_status = {
        "native_tree": replay_marked_profile(
            "native_tree",
            binary,
            packets,
            {
                operation_id: path[1:]
                for operation_id, path in paths["native_tree"].items()
            },
            out,
            stack="project,dataset,agent,operation",
        ),
        "automatic_agent": replay_marked_profile(
            "automatic_agent",
            binary,
            packets,
            automatic_semantic_paths,
            out,
            stack="project,dataset,agent,operation",
        ),
        "source_preserving_agent": replay_marked_profile(
            "source_preserving_agent",
            binary,
            packets,
            automatic_semantic_paths,
            out,
            stack="project,agent,operation,tool",
        ),
        "recurrence": replay_marked_profile(
            "recurrence",
            binary,
            packets,
            recurrence,
            out,
            stack="project,dataset,agent,operation",
        ),
    }
    fixed = fixed_group_rows(packets, paths)
    # This write is the algorithm/target boundary.  Everything above used only
    # source packets and automatic annotations; target and localizer artifacts
    # are opened only below this point.
    write_jsonl(out / "fixed-groups.jsonl", fixed)

    signals = load_signals_after_groups(args.benchmark, root, fixed)
    summary, query_rows = score(args.benchmark, fixed, signals)
    historical_reproduction = None
    if args.mode == "full":
        historical = historical_agentprof_paths(args.benchmark, root)
        require(set(historical) == expected, "historical AgentProf path coverage")
        historical_fixed = [
            {
                **row,
                "groups": {"historical_agentprof": list(historical[str(row["operation_id"])])},
            }
            for row in fixed
        ]
        historical_scores = scores_for_method(
            args.benchmark,
            historical_fixed,
            signals,
            "historical_agentprof",
        )
        historical_map, historical_queries = map_for_one_method(signals, historical_scores)
        require(historical_map is not None, "historical AgentProf produced no MAP")
        expected_map = EXPECTED_HISTORICAL_MAP[args.benchmark]
        require(
            math.isclose(historical_map, expected_map, rel_tol=0.0, abs_tol=1e-12),
            f"historical AgentProf MAP drift: {historical_map} != {expected_map}",
        )
        historical_reproduction = {
            "map": historical_map,
            "expected_map": expected_map,
            "target_bearing_queries": historical_queries,
            "exact_within_1e-12": True,
        }
    summary.update(
        {
            "mode": args.mode,
            "source_only_group_construction": True,
            "methods": list(METHODS),
            "product_profiles": {
                method: {
                    "operations": int(status["operations"]),
                    "samples": int(status["samples"]),
                    "unique_stacks": int(status["unique_stacks"]),
                }
                for method, status in product_status.items()
            },
            "depths": {
                method: dict(
                    sorted(Counter(len(path) for path in paths[method].values()).items())
                )
                for method in METHODS
            },
            "historical_agentprof_reproduction": historical_reproduction,
        }
    )
    write_jsonl(out / "per-query.jsonl", query_rows)
    write_json(out / "summary.json", summary)
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
