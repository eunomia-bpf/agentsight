#!/usr/bin/env python3
"""Annotate four real AgentCap review traces with a shared variable-depth stack.

This is an experiment adapter, not a product-side semantic classifier.  It
marks a small number of source-line transitions after inspecting progress
summaries, lets ordinary operations inherit the active task path, and writes
AgentPProf's existing normalized-operation input format.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ROOT_TASK = "Review AgentCap research evidence"


@dataclass(frozen=True)
class Transition:
    start_line: int
    path: tuple[str, ...]


@dataclass(frozen=True)
class TraceSpec:
    alias: str
    transitions: tuple[Transition, ...]


TRACE_SPECS: dict[str, TraceSpec] = {
    "019f2996-ffd0-74d0-a591-4e04501fa093": TraceSpec(
        "agentcap-r024",
        (
            Transition(0, (ROOT_TASK, "Establish review scope")),
            Transition(1947, (ROOT_TASK, "Inspect implementation")),
            Transition(
                1959,
                (ROOT_TASK, "Audit experiment evidence", "Inspect result artifacts"),
            ),
            Transition(
                1993,
                (
                    ROOT_TASK,
                    "Audit experiment evidence",
                    "Compare official evaluator semantics",
                ),
            ),
            Transition(2052, (ROOT_TASK, "Synthesize findings")),
            Transition(
                2083, (ROOT_TASK, "Verify repairs", "Inspect repaired implementation")
            ),
            Transition(2094, (ROOT_TASK, "Verify repairs", "Rerun validation")),
            Transition(2127, (ROOT_TASK, "Synthesize findings", "Confirm resolution")),
        ),
    ),
    "019f29a7-8480-71f2-a651-6be1db1fd2b9": TraceSpec(
        "agentcap-r025",
        (
            Transition(0, (ROOT_TASK, "Establish review scope")),
            Transition(2090, (ROOT_TASK, "Inspect implementation")),
            Transition(
                2102,
                (ROOT_TASK, "Audit experiment evidence", "Inspect result artifacts"),
            ),
            Transition(2144, (ROOT_TASK, "Synthesize findings")),
            Transition(
                2160, (ROOT_TASK, "Verify repairs", "Inspect repaired implementation")
            ),
            Transition(2199, (ROOT_TASK, "Verify repairs", "Rerun validation")),
            Transition(2228, (ROOT_TASK, "Synthesize findings", "Confirm resolution")),
        ),
    ),
    "019f2af2-920c-7b70-a8ea-232cfd2b0cc8": TraceSpec(
        "agentcap-r035",
        (
            Transition(0, (ROOT_TASK, "Establish review scope")),
            Transition(3287, (ROOT_TASK, "Inspect implementation")),
            Transition(3300, (ROOT_TASK, "Validate execution", "Run focused checks")),
            Transition(3340, (ROOT_TASK, "Audit claims and documentation")),
            Transition(3382, (ROOT_TASK, "Synthesize findings")),
            Transition(
                3404, (ROOT_TASK, "Verify repairs", "Inspect repaired implementation")
            ),
            Transition(3428, (ROOT_TASK, "Verify repairs", "Rerun validation")),
            Transition(3455, (ROOT_TASK, "Synthesize findings", "Confirm resolution")),
        ),
    ),
    "019f2f0b-9caa-7f52-9cae-b00c5dcef37f": TraceSpec(
        "agentcap-r081",
        (
            Transition(0, (ROOT_TASK, "Establish review scope")),
            Transition(
                49,
                (ROOT_TASK, "Audit experiment evidence", "Inspect statistical semantics"),
            ),
            Transition(83, (ROOT_TASK, "Validate execution", "Reproduce reported results")),
            Transition(113, (ROOT_TASK, "Synthesize findings")),
            Transition(
                128, (ROOT_TASK, "Verify repairs", "Inspect repaired evidence")
            ),
            Transition(
                190,
                (
                    ROOT_TASK,
                    "Audit claims and documentation",
                    "Compare related-work evidence",
                ),
            ),
            Transition(242, (ROOT_TASK, "Synthesize findings", "Confirm resolution")),
        ),
    ),
}


def path_at(spec: TraceSpec, line: int) -> tuple[str, ...]:
    """Return the last marked task path at or before a source line."""

    active: tuple[str, ...] | None = None
    for transition in spec.transitions:
        if transition.start_line > line:
            break
        active = transition.path
    if active is None:
        raise ValueError(f"no task path covers source line {line}")
    return active


def semantic_action(row: dict[str, Any]) -> str:
    """Correct one known source-native label for these read-only reviews."""

    action = str(row["action"])
    if action == "Update repository":
        return "Inspect repository state"
    return action


def pprof_record(row: dict[str, Any], spec: TraceSpec, path: tuple[str, ...]) -> dict[str, Any]:
    operation_id = str(row["operation_id"])
    return {
        "value": int(row["event_weight"]),
        "fields": {
            "task": list(path),
            "action": semantic_action(row),
            "object": str(row["object"]),
            "result": str(row["result"]),
            "source_kind": str(row["operation_kind"]),
            "source_session": spec.alias,
            "evidence_id": hashlib.sha256(operation_id.encode()).hexdigest()[:16],
        },
    }


def annotate(input_path: Path, output_path: Path, summary_path: Path) -> dict[str, Any]:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    selected_counts: Counter[str] = Counter()
    task_counts: Counter[tuple[str, ...]] = Counter()
    responsibility_traces: dict[str, set[str]] = defaultdict(set)
    depth_counts: Counter[int] = Counter()
    input_weight = 0
    output_weight = 0

    with input_path.open() as source, output_path.open("w") as sink:
        for source_line in source:
            row = json.loads(source_line)
            session_id = str(row["session_id"])
            if session_id not in TRACE_SPECS:
                raise ValueError(f"unexpected session in bounded input: {session_id}")
            spec = TRACE_SPECS[session_id]
            path = path_at(spec, int(row["line"]))
            record = pprof_record(row, spec, path)
            sink.write(json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n")

            weight = int(row["event_weight"])
            selected_counts[spec.alias] += 1
            input_weight += weight
            output_weight += int(record["value"])
            task_counts[path] += weight
            depth_counts[len(path)] += weight
            responsibility_traces[path[1]].add(spec.alias)

    missing = sorted(spec.alias for spec in TRACE_SPECS.values() if not selected_counts[spec.alias])
    if missing:
        raise ValueError(f"selected input is missing traces: {missing}")
    if input_weight != output_weight:
        raise ValueError(f"resource conservation failed: {input_weight} != {output_weight}")

    summary = {
        "input": str(input_path),
        "output": str(output_path),
        "operations": sum(selected_counts.values()),
        "event_weight": output_weight,
        "trace_operations": dict(sorted(selected_counts.items())),
        "task_depth_operations": {
            str(depth): count for depth, count in sorted(depth_counts.items())
        },
        "task_paths": [
            {"path": list(path), "operations": count}
            for path, count in sorted(task_counts.items(), key=lambda item: (-item[1], item[0]))
        ],
        "responsibility_trace_coverage": {
            responsibility: sorted(traces)
            for responsibility, traces in sorted(responsibility_traces.items())
        },
    }
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n")
    return summary


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    args = parser.parse_args()
    summary = annotate(args.input, args.output, args.summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
