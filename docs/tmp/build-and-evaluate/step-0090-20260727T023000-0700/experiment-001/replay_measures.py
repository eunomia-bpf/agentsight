#!/usr/bin/env python3
"""Prepare deterministic multi-measure AgentPProf operation inputs.

This is an experiment adapter, not a product output path. It reads fixed
artifacts and emits normalized operation JSONL plus one audit manifest.
"""

from __future__ import annotations

import argparse
import ast
from collections import Counter, defaultdict
from datetime import datetime
import hashlib
import json
import math
from pathlib import Path
import re
import subprocess
from typing import Any, Iterable


GIT_SESSIONS = {
    "openhands-Anthropic__Claude-Sonnet-4-20250514-Thinking-git-multibranch-75c1745e":
        "openhands-Anthropic__Claude-Sonnet-4-20250514-Thinking-git-multibranch-75c1745e.tar.zst",
    "openhands-DeepSeek__DeepSeek-V3.2-git-multibranch-0bbc5d81":
        "openhands-DeepSeek__DeepSeek-V3.2-git-multibranch-0bbc5d81.tar.zst",
    "terminus2-DeepSeek__DeepSeek-V3.2-git-multibranch-c063fb97":
        "terminus2-DeepSeek__DeepSeek-V3.2-git-multibranch-c063fb97.tar.zst",
}
OPENHANDS_ACTIONS = {"edit", "finish", "read", "run", "think"}
PATCH_TARGET_RE = re.compile(r"\*\*\* (Add|Update|Delete) File:\s+(\S+)")
PATCH_MOVE_RE = re.compile(r"\*\*\* Move to:\s+(\S+)")


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
    with path.open(encoding="utf-8") as source:
        for line_number, line in enumerate(source, 1):
            if line.strip():
                row = json.loads(line)
                if not isinstance(row, dict):
                    raise ValueError(f"{path}:{line_number}: expected JSON object")
                rows.append(row)
    return rows


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as output:
        for row in rows:
            output.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")


def write_json(path: Path, payload: Any) -> None:
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def tar_members(archive: Path) -> list[str]:
    completed = subprocess.run(
        ["tar", "--zstd", "-tf", str(archive)],
        check=True,
        text=True,
        capture_output=True,
    )
    return completed.stdout.splitlines()


def tar_text(archive: Path, member: str) -> str:
    completed = subprocess.run(
        ["tar", "--zstd", "-xOf", str(archive), member],
        check=True,
        text=True,
        capture_output=True,
    )
    return completed.stdout


def exactly_one(values: Iterable[str], what: str) -> str:
    materialized = list(values)
    if len(materialized) != 1:
        raise ValueError(f"expected exactly one {what}, got {len(materialized)}")
    return materialized[0]


def openhands_timestamps(archive: Path) -> dict[str, float]:
    session_member = exactly_one(
        (
            member
            for member in tar_members(archive)
            if re.search(r"/sessions/[^/]+\.json$", member)
        ),
        f"OpenHands session JSON in {archive.name}",
    )
    events = json.loads(tar_text(archive, session_member))
    timestamps: dict[str, float] = {}
    for event in events:
        if event.get("source") != "agent" or event.get("action") not in OPENHANDS_ACTIONS:
            continue
        model_response = (event.get("tool_call_metadata") or {}).get("model_response") or {}
        call_id = model_response.get("id")
        if not call_id:
            raise ValueError(f"selected OpenHands action {event.get('id')} lacks model response ID")
        if call_id in timestamps:
            raise ValueError(f"duplicate OpenHands model response ID: {call_id}")
        timestamps[call_id] = datetime.fromisoformat(event["timestamp"]).timestamp()
    return timestamps


def normalize_terminal_input(value: str) -> str:
    if value == "C-c":
        return "\x03"
    return value.replace("\r", "\n").rstrip("\n")


def command_text(value: Any) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        return "".join("\r" if part == "Enter" else str(part) for part in value)
    raise ValueError(f"unsupported commands.txt value: {type(value).__name__}")


def terminus_timestamps(
    archive: Path,
    rows: list[dict[str, Any]],
) -> tuple[dict[str, float], dict[str, Any]]:
    members = tar_members(archive)
    commands_member = exactly_one(
        (member for member in members if member.endswith("/commands.txt")),
        f"Terminus2 commands.txt in {archive.name}",
    )
    cast_member = exactly_one(
        (member for member in members if member.endswith("/agent.cast")),
        f"Terminus2 agent.cast in {archive.name}",
    )
    commands = [ast.literal_eval(line) for line in tar_text(archive, commands_member).splitlines()]
    inputs = []
    for line in tar_text(archive, cast_member).splitlines():
        event = json.loads(line)
        if isinstance(event, list) and len(event) >= 3 and event[1] == "i":
            inputs.append(event)

    selected = []
    for row in rows:
        fields = row["fields"]
        match = re.search(r"#line-(\d+)$", fields["source_ref"])
        if not match:
            raise ValueError(f"Terminus2 row lacks commands.txt line: {fields['source_ref']}")
        line_number = int(match.group(1))
        command = normalize_terminal_input(command_text(commands[line_number - 1]))
        selected.append((fields["evidence_id"], line_number, command))

    observed = [
        (float(event[0]), normalize_terminal_input(event[2]))
        for event in inputs
    ]
    if not observed or observed[0][1] != "clear":
        raise ValueError("Terminus2 cast does not begin with the expected initial clear")
    observed = observed[1:]
    expected_nonblank = [
        (evidence_id, line_number, command)
        for evidence_id, line_number, command in selected
        if command
    ]
    expected_commands = [command for _, _, command in expected_nonblank]
    observed_commands = [command for _, command in observed]
    if expected_commands != observed_commands:
        mismatch = next(
            (
                index
                for index, (expected, actual) in enumerate(
                    zip(expected_commands, observed_commands)
                )
                if expected != actual
            ),
            min(len(expected_commands), len(observed_commands)),
        )
        raise ValueError(
            "Terminus2 normalized command sequence differs from cast after clear: "
            f"expected={len(expected_commands)} observed={len(observed_commands)} "
            f"first_mismatch={mismatch}"
        )

    mapped = {
        evidence_id: observed[index][0]
        for index, (evidence_id, _, _) in enumerate(expected_nonblank)
    }
    blank_ids = []
    for index, (evidence_id, _, command) in enumerate(selected):
        if command:
            continue
        blank_ids.append(evidence_id)
        next_id = next(
            (
                later_id
                for later_id, _, later_command in selected[index + 1 :]
                if later_command
            ),
            None,
        )
        if next_id is None:
            raise ValueError("terminal blank Terminus2 command has no next retained input")
        mapped[evidence_id] = mapped[next_id]
    return mapped, {
        "commands_member": commands_member,
        "cast_member": cast_member,
        "cast_input_events": len(inputs),
        "excluded_initial_inputs": 1,
        "exact_nonblank_sequence_equal": True,
        "mapped_rows": len(mapped),
        "blank_commands_bound_to_next_input": len(blank_ids),
        "blank_evidence_ids": blank_ids,
    }


def elapsed_values(starts: list[float]) -> list[int]:
    if not starts:
        return []
    values = [
        max(1, math.floor(starts[index + 1] - starts[index]))
        for index in range(len(starts) - 1)
    ]
    values.append(1)
    return values


def accepted_git_paths(
    repo: Path,
    rows: list[dict[str, Any]],
) -> dict[str, Any]:
    marks_path = (
        repo
        / ".agentsight/experiments/rq1-matched-organization-v1/full/"
        "accepted-operation-marks.json"
    )
    trace_path = (
        repo
        / "docs/visexp/out/codex-agent-long-horizon-v1/"
        "annotation-workspace-git-v1/trace.jsonl"
    )
    marks = json.loads(marks_path.read_text(encoding="utf-8"))
    names = marks["operation_names"]
    transitions: dict[str, dict[str, list[str]]] = defaultdict(dict)
    for mark in marks["marks"]:
        transitions[mark["sequence"]][mark["start_operation_id"]] = [
            names[operation_id] for operation_id in mark["operation_ids"]
        ]
    trace_paths = {}
    for node in read_jsonl(trace_path):
        if node.get("kind") == "tool":
            evidence_id = node["id"].removeprefix("tool:")
            trace_paths[evidence_id] = list(node.get("path") or [])
    expanded = {}
    current_by_session: dict[str, list[str]] = {}
    mismatches = []
    for row in rows:
        fields = row["fields"]
        session = fields["source_session"]
        evidence_id = fields["evidence_id"]
        if evidence_id in transitions[session]:
            current_by_session[session] = transitions[session][evidence_id]
        if session not in current_by_session:
            raise ValueError(f"accepted Git path missing at {evidence_id}")
        path = current_by_session[session]
        expanded[evidence_id] = path
        if trace_paths.get(evidence_id) != path:
            mismatches.append(
                {
                    "evidence_id": evidence_id,
                    "expanded": path,
                    "workspace": trace_paths.get(evidence_id),
                }
            )
    missing_workspace = sorted(set(expanded) - set(trace_paths))
    extra_workspace = sorted(set(trace_paths) - set(expanded))
    encoded = json.dumps(
        [
            (row["fields"]["evidence_id"], expanded[row["fields"]["evidence_id"]])
            for row in rows
        ],
        separators=(",", ":"),
    ).encode()
    return {
        "marks": str(marks_path.relative_to(repo)),
        "workspace_trace": str(trace_path.relative_to(repo)),
        "rows": len(rows),
        "expanded_paths": len(expanded),
        "workspace_paths": len(trace_paths),
        "mismatches": mismatches,
        "missing_workspace_evidence": missing_workspace,
        "extra_workspace_evidence": extra_workspace,
        "ordered_evidence_path_sha256": hashlib.sha256(encoded).hexdigest(),
        "exact_match": not mismatches and not missing_workspace and not extra_workspace,
    }


def git_time_rows(repo: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    source = (
        repo
        / ".agentsight/experiments/rq1-matched-organization-v1/full/operations-count.jsonl"
    )
    archives = (
        repo / ".agentsight/experiments/codetracebench-rq2/hub/bench_artifacts/full"
    )
    rows = read_jsonl(source)
    by_session: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_session[row["fields"]["source_session"]].append(row)
    if set(by_session) != set(GIT_SESSIONS):
        raise ValueError(
            f"Git session set changed: expected {sorted(GIT_SESSIONS)}, "
            f"got {sorted(by_session)}"
        )

    output = []
    session_audit: dict[str, Any] = {}
    imputed_evidence_ids = []
    one_second_minimum_intervals = 0
    one_second_minimum_added = 0
    raw_observed_gap_seconds = 0.0
    floored_observed_gap_seconds = 0
    for session, session_rows in by_session.items():
        archive = archives / GIT_SESSIONS[session]
        if session.startswith("openhands-"):
            timestamps_by_call = openhands_timestamps(archive)
            starts = []
            for row in session_rows:
                call = row["fields"]["call"].split(":openhands:", 1)[1]
                if call not in timestamps_by_call:
                    raise ValueError(f"missing OpenHands timestamp for {call}")
                starts.append(timestamps_by_call[call])
            detail = {
                "kind": "openhands_iso_action",
                "archive": str(archive.relative_to(repo)),
                "raw_selected_actions": len(timestamps_by_call),
            }
        else:
            timestamps_by_id, detail = terminus_timestamps(archive, session_rows)
            starts = [timestamps_by_id[row["fields"]["evidence_id"]] for row in session_rows]
            detail.update(
                {
                    "kind": "terminus_asciinema_input",
                    "archive": str(archive.relative_to(repo)),
                }
            )
        if any(later < earlier for earlier, later in zip(starts, starts[1:])):
            raise ValueError(f"non-monotonic Git operation timestamps in {session}")
        values = elapsed_values(starts)
        gaps = [
            starts[index + 1] - starts[index]
            for index in range(len(starts) - 1)
        ]
        floors = [math.floor(gap) for gap in gaps]
        raw_observed_gap_seconds += sum(gaps)
        floored_observed_gap_seconds += sum(floors)
        minimum_additions = [max(1, floor) - floor for floor in floors]
        one_second_minimum_intervals += sum(addition > 0 for addition in minimum_additions)
        one_second_minimum_added += sum(minimum_additions)
        terminal_id = session_rows[-1]["fields"]["evidence_id"]
        imputed_evidence_ids.append(terminal_id)
        imputed_evidence_ids.extend(detail.get("blank_evidence_ids", []))
        for source_row, value, start in zip(session_rows, values, starts):
            projected = json.loads(json.dumps(source_row))
            projected["value"] = value
            output.append(projected)
        detail.update(
            {
                "rows": len(session_rows),
                "elapsed_seconds": sum(values),
                "minimum_start": min(starts),
                "maximum_start": max(starts),
                "raw_observed_gap_seconds": sum(gaps),
                "floored_observed_gap_seconds": sum(floors),
                "one_second_minimum_intervals": sum(
                    addition > 0 for addition in minimum_additions
                ),
                "one_second_minimum_added_seconds": sum(minimum_additions),
                "terminal_imputation_evidence_id": terminal_id,
            }
        )
        session_audit[session] = detail

    expected_ids = [row["fields"]["evidence_id"] for row in rows]
    actual_ids = [row["fields"]["evidence_id"] for row in output]
    if actual_ids != expected_ids:
        # defaultdict traversal follows first appearance in the fixed input;
        # fail rather than silently reorder if that assumption changes.
        raise ValueError("Git evidence-ID order changed during projection")
    diagnose_ids = set(
        json.loads(
            (
                repo
                / ".agentsight/experiments/rq1-matched-organization-v1/full/"
                "diagnose-evidence-ids.json"
            ).read_text(encoding="utf-8")
        )
    )
    diagnose_mass = sum(
        row["value"] for row in output if row["fields"]["evidence_id"] in diagnose_ids
    )
    total = sum(row["value"] for row in output)
    hierarchy = accepted_git_paths(repo, rows)
    if not hierarchy["exact_match"]:
        raise ValueError("accepted Git hierarchy expansion differs from frozen workspace")
    return output, {
        "source": str(source.relative_to(repo)),
        "rows": len(output),
        "unique_evidence_ids": len(set(actual_ids)),
        "total_elapsed_seconds": total,
        "diagnose_authentication_rows": sum(
            row["fields"]["evidence_id"] in diagnose_ids for row in output
        ),
        "diagnose_authentication_elapsed_seconds": diagnose_mass,
        "diagnose_authentication_share_pct": 100.0 * diagnose_mass / total,
        "measure_definition": "max(1,floor(next_start-start)) seconds; terminal=1",
        "raw_observed_gap_seconds": raw_observed_gap_seconds,
        "floored_observed_gap_seconds": floored_observed_gap_seconds,
        "one_second_minimum_intervals": one_second_minimum_intervals,
        "one_second_minimum_added_seconds": one_second_minimum_added,
        "imputed_samples": len(imputed_evidence_ids),
        "imputed_mass_seconds": len(imputed_evidence_ids),
        "imputed_evidence_ids": imputed_evidence_ids,
        "hierarchy_check": hierarchy,
        "sessions": session_audit,
    }


def ancestry(node: dict[str, Any], index: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    chain = [node]
    current = node
    seen = {node["id"]}
    while current.get("parent"):
        parent_id = current["parent"]
        if parent_id in seen or parent_id not in index:
            raise ValueError(f"invalid ancestry at {node['id']}: {parent_id}")
        current = index[parent_id]
        chain.append(current)
        seen.add(parent_id)
    chain.reverse()
    return chain


def normalize_target(target: str, repo: Path) -> str:
    target = target.strip().strip("\"'")
    prefix = str(repo.resolve()) + "/"
    if target.startswith(prefix):
        return target[len(prefix):]
    return target


def patch_targets(arguments: str, repo: Path) -> list[tuple[str, str]]:
    targets = []
    disposition = {
        "Add": "created",
        "Update": "updated",
        "Delete": "deleted",
    }
    for match in PATCH_TARGET_RE.finditer(arguments):
        targets.append((normalize_target(match.group(2), repo), disposition[match.group(1)]))
    for match in PATCH_MOVE_RE.finditer(arguments):
        targets.append((normalize_target(match.group(1), repo), "moved"))
    deduplicated = []
    seen = set()
    for item in targets:
        if item not in seen:
            deduplicated.append(item)
            seen.add(item)
    return deduplicated


def compact_evidence(node_id: str, kind: str) -> str:
    match = re.search(rf":{re.escape(kind)}:(\d+)(?::|$)", node_id)
    return f"{kind}:{match.group(1)}" if match else node_id


def target_evidence_id(node_id: str, disposition: str, target: str) -> str:
    digest = hashlib.sha256(f"{node_id}\0{disposition}\0{target}".encode()).hexdigest()[:16]
    return f"{node_id}:target:{digest}"


def step86_effect_rows(
    repo: Path,
) -> tuple[dict[str, list[dict[str, Any]]], dict[str, Any]]:
    source = (
        repo
        / "docs/tmp/build-and-evaluate/step-0086-20260725T213500-0700/"
        "experiment-001/workspace/trace.jsonl"
    )
    nodes = read_jsonl(source)
    index = {node["id"]: node for node in nodes}
    if len(index) != len(nodes):
        raise ValueError("duplicate node ID in Step-0086 trace")
    outputs = {"file-read": [], "file-write": [], "network": []}
    tool_counts = Counter()
    status_counts = Counter()
    created = []
    projected_nodes = Counter()
    for node in nodes:
        if node.get("kind") != "tool":
            continue
        data = node.get("data") or {}
        effect = data.get("effect")
        tool_counts[effect] += 1
        if effect == "network":
            status_counts[data.get("status", "unknown")] += 1
        if effect not in {"read", "write", "network"}:
            continue
        chain = ancestry(node, index)
        session = chain[0]
        llm_nodes = [candidate for candidate in chain if candidate.get("kind") == "llm"]
        if len(llm_nodes) != 1:
            raise ValueError(f"tool {node['id']} has {len(llm_nodes)} LLM ancestors")
        llm = llm_nodes[0]
        agent = (session.get("data") or {}).get("agent", "unknown")
        tool_name = data.get("tool") or data.get("name") or "tool"
        tool_label = f"{tool_name}:{compact_evidence(node['id'], 'tool')}"
        llm_label = compact_evidence(llm["id"], "llm")

        if effect == "write" and tool_name == "apply_patch":
            targets = patch_targets(data.get("arguments_preview", ""), repo)
            if data.get("status") != "ok":
                targets = [
                    (target, "unconfirmed_" + disposition)
                    for target, disposition in targets
                ]
            if not targets:
                targets = [
                    (normalize_target(target, repo), "affected")
                    for target in data.get("path_groups", [])
                ]
        elif effect == "network":
            targets = [
                (target, data.get("status", "unknown"))
                for target in (data.get("domains") or ["unknown"])
            ]
        else:
            disposition = "read" if effect == "read" else "affected"
            targets = [
                (normalize_target(target, repo), disposition)
                for target in data.get("path_groups", [])
            ]

        output_key = {
            "read": "file-read",
            "write": "file-write",
            "network": "network",
        }[effect]
        projected_nodes[output_key] += bool(targets)
        for target, disposition_value in targets:
            fields = {
                "agent": agent,
                "operation": list(node.get("path") or []),
                "llm_evidence": llm_label,
                "tool_evidence": tool_label,
                "effect": f"file.{effect}" if effect != "network" else "network.connect",
                "disposition": disposition_value,
                "target": target,
                "source_session": session["id"],
                "source_prompt": next(
                    (
                        candidate["id"]
                        for candidate in chain
                        if candidate.get("kind") == "prompt"
                    ),
                    "unknown",
                ),
                "source_kind": "tool",
                "source_evidence_id": node["id"],
                "evidence_id": target_evidence_id(node["id"], disposition_value, target),
                "status": data.get("status", "unknown"),
            }
            row = {"fields": fields, "value": 1}
            outputs[output_key].append(row)
            if disposition_value == "created" and data.get("status") == "ok":
                created.append(
                    {
                        "semantic_operation": node.get("path") or [],
                        "llm_evidence": llm_label,
                        "tool_evidence": tool_label,
                        "source_evidence_id": node["id"],
                        "target": target,
                    }
                )
    if set(row["fields"]["source_evidence_id"] for row in outputs["file-read"]) & set(
        row["fields"]["source_evidence_id"] for row in outputs["file-write"]
    ):
        raise ValueError("Step-0086 read/write source evidence overlaps")
    return outputs, {
        "source": str(source.relative_to(repo)),
        "nodes": len(nodes),
        "source_tool_effect_counts": dict(sorted(tool_counts.items())),
        "network_status_counts": dict(sorted(status_counts.items())),
        "projected_target_rows": {
            key: len(value) for key, value in sorted(outputs.items())
        },
        "projected_source_nodes": dict(sorted(projected_nodes.items())),
        "created_files": created,
    }


def r114_system_rows(repo: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    source = (
        repo
        / ".agentsight/experiments/rq1-r114-current-profile-v1/full/profile/"
        "scoped-lineage-operations.jsonl"
    )
    result_path = (
        repo
        / ".agentsight/experiments/rq1-r114-current-profile-v1/full/r114/"
        "live-record-r114.json"
    )
    rows = read_jsonl(source)
    result = json.loads(result_path.read_text(encoding="utf-8"))
    task_tools = {}
    task_records = {}
    for task in result["tasks"]:
        tools = task["precision_recall"]["agent_tool_ids"]
        if len(tools) != 1:
            raise ValueError(f"R114 task {task['task_id']} has {len(tools)} wrapper IDs")
        task_tools[task["task_id"]] = tools[0]
        task_records[task["task_id"]] = task
    output = []
    effect_counts = Counter()
    task_counts = Counter()
    for index, row in enumerate(rows, 1):
        projected = json.loads(json.dumps(row))
        fields = projected["fields"]
        session = fields["session"]
        if session not in task_tools:
            raise ValueError(f"R114 effect row has unknown task/session: {session}")
        fields["tool_evidence"] = task_tools[session]
        fields["source_session"] = session
        fields["source_kind"] = "system_effect"
        fields["evidence_id"] = f"r114-effect-{index:04d}"
        effect_counts[fields["effect"]] += projected["value"]
        task_counts[session] += projected["value"]
        output.append(projected)
    if sum(row["value"] for row in output) != sum(row["value"] for row in rows):
        raise ValueError("R114 mass changed during wrapper-tool join")
    return output, {
        "source": str(source.relative_to(repo)),
        "task_result": str(result_path.relative_to(repo)),
        "rows": len(output),
        "mass": sum(row["value"] for row in output),
        "tasks": len(task_tools),
        "wrapper_tool_ids": len(set(task_tools.values())),
        "effect_counts": dict(sorted(effect_counts.items())),
        "selected_by_task": dict(sorted(task_counts.items())),
        "failure_retry": {
            "tool_evidence": task_tools["r114-failure-retry"],
            "rows": task_counts["r114-failure-retry"],
            "processes": dict(
                sorted(
                    Counter(
                        row["fields"]["process"]
                        for row in output
                        if row["fields"]["session"] == "r114-failure-retry"
                    ).items()
                )
            ),
            "effects": dict(
                sorted(
                    Counter(
                        row["fields"]["effect"]
                        for row in output
                        if row["fields"]["session"] == "r114-failure-retry"
                    ).items()
                )
            ),
            "false_negatives": task_records["r114-failure-retry"]["precision_recall"][
                "false_negatives"
            ],
            "expected_python3_effect_retained": any(
                row["fields"]["session"] == "r114-failure-retry"
                and row["fields"]["process"] == "python3"
                for row in output
            ),
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args()
    repo = args.repo.resolve()
    out_dir = args.out_dir.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    git_rows, git_audit = git_time_rows(repo)
    effect_rows, effect_audit = step86_effect_rows(repo)
    r114_rows, r114_audit = r114_system_rows(repo)

    outputs = {
        "git_time": out_dir / "git-multibranch.time.jsonl",
        "file_read": out_dir / "selfprofile.file-read.jsonl",
        "file_write": out_dir / "selfprofile.file-write.jsonl",
        "network": out_dir / "selfprofile.network.jsonl",
        "r114_system_effects": out_dir / "r114.system-effects.jsonl",
    }
    write_jsonl(outputs["git_time"], git_rows)
    write_jsonl(outputs["file_read"], effect_rows["file-read"])
    write_jsonl(outputs["file_write"], effect_rows["file-write"])
    write_jsonl(outputs["network"], effect_rows["network"])
    write_jsonl(outputs["r114_system_effects"], r114_rows)

    manifest = {
        "schema_version": 1,
        "status": "prepared",
        "generated_at": "1970-01-01T00:00:00Z",
        "deterministic_replay": True,
        "product_code_changed": False,
        "outputs": {
            key: str(path.relative_to(out_dir)) for key, path in outputs.items()
        },
        "git_time": git_audit,
        "step0086_effects": effect_audit,
        "r114_system_effects": r114_audit,
        "network_failure_correlation": {
            # Availability requires a failed network row with responsibility
            # evidence, not merely the existence of any network row.
            "available": effect_audit["network_status_counts"].get("fail", 0) > 0,
            "reason_if_unavailable": (
                "Step-0086 has no failed network-classified tool; R114 retains "
                "zero network effects; the Git case has no eBPF recording."
            ),
        },
    }
    write_json(out_dir / "prepared-measures.json", manifest)
    print(json.dumps(manifest, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
