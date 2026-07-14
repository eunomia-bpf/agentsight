#!/usr/bin/env python3
"""Replay R114 scoped lineage rows through the current AgentProf profile path.

This runner does not compute lineage or process scope. It consumes the process
and tool identities already emitted by R114, selects the corresponding joined
rows, converts each row once to ordinary operation JSONL, and checks exact
count and mass preservation after one AgentProf fold.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import subprocess
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
STACK = "project,task,effect,process,target"
TASK_FRAME = re.compile(r"(?:^|;)task:([^;]+)")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--r114-result", type=Path, required=True)
    parser.add_argument("--agentpprof-bin", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    return parser.parse_args()


def read_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def joined(row: dict[str, str]) -> bool:
    return str(row.get("joined") or "").lower() in {"1", "true", "yes"}


def lineage_path(task: dict[str, Any]) -> Path:
    db_path = Path(str(task.get("db") or ""))
    if not db_path.is_absolute():
        db_path = ROOT / db_path
    return db_path.parent / "lineage" / "effect-lineage.csv"


def operation(task: dict[str, Any], row: dict[str, str]) -> dict[str, Any]:
    return {
        "value": 1,
        "fields": {
            "project": "agentsight-r114",
            "agent": "codex",
            "task": str(task.get("category") or "unknown"),
            "session": str(task.get("task_id") or "unknown"),
            "op": str(row.get("audit_type") or "effect"),
            "action": str(row.get("action") or "unknown"),
            "effect": str(row.get("effect") or "unknown"),
            "process": str(row.get("process_comm") or "unknown"),
            "target": str(row.get("target_group") or "unknown"),
            "source": "r114-scoped-lineage",
        },
    }


def selected_rows(task: dict[str, Any]) -> tuple[list[dict[str, str]], Path]:
    precision_recall = task.get("precision_recall") or {}
    process_ids = {str(value) for value in precision_recall.get("agent_process_ids") or []}
    tool_ids = {str(value) for value in precision_recall.get("agent_tool_ids") or []}
    if not process_ids:
        raise SystemExit(f"{task.get('task_id')}: missing persisted agent_process_ids")
    path = lineage_path(task)
    if not path.exists():
        raise SystemExit(f"{task.get('task_id')}: missing lineage CSV {path}")
    rows = []
    for row in read_csv(path):
        if not joined(row):
            continue
        if str(row.get("process_id") or "") not in process_ids:
            continue
        if tool_ids and str(row.get("tool_id") or "") not in tool_ids:
            continue
        rows.append(row)
    return rows, path


def stage_a_support(result: dict[str, Any]) -> tuple[bool, dict[str, Any]]:
    aggregate = result.get("aggregate") or {}
    tasks = int(aggregate.get("tasks") or 0)
    target_statuses = aggregate.get("target_statuses") or {}
    checks = {
        "precision_at_least_98": float(aggregate.get("precision_pct") or 0.0) >= 98.0,
        "recall_at_least_95": float(aggregate.get("recall_pct") or 0.0) >= 95.0,
        "zero_negative_joins": int(aggregate.get("negative_joined_effect_events") or 0) == 0,
        "control_observed_every_task": int(aggregate.get("negative_control_tasks_observed") or 0)
        == tasks,
        "all_targets_completed": int(target_statuses.get("completed") or 0) == tasks,
    }
    return all(checks.values()), checks


def category_mass_from_stacks(stacks: dict[str, Any]) -> Counter[str]:
    mass: Counter[str] = Counter()
    for stack, weight in stacks.items():
        match = TASK_FRAME.search(stack)
        if not match:
            raise SystemExit(f"profile stack is missing task frame: {stack}")
        mass[match.group(1)] += int(weight)
    return mass


def write_markdown(path: Path, payload: dict[str, Any]) -> None:
    stage_a = payload["stage_a"]
    stage_b = payload["stage_b"]
    lines = [
        "# R114 Current-AgentProf Replay",
        "",
        f"- Status: **{payload['status']}**",
        f"- R114 result: `{payload['r114_result']}`",
        f"- AgentProf: `{payload['agentpprof_bin']}`",
        "",
        "## Stage A: R114 scoped lineage",
        "",
        f"- Precision: {stage_a['precision_pct']}%",
        f"- Recall: {stage_a['recall_pct']}%",
        f"- True positives: {stage_a['true_positives']}",
        f"- Negative-control effects: {stage_a['negative_effect_events_observed']}",
        f"- Joined negative-control effects: {stage_a['negative_joined_effect_events']}",
        f"- Tasks with controls: {stage_a['negative_control_tasks_observed']}/{stage_a['tasks']}",
        f"- Completed targets: {stage_a['completed_targets']}/{stage_a['tasks']}",
        f"- Existing R114 thresholds pass: {stage_a['support']}",
        "",
        "## Stage B: current AgentProf preservation",
        "",
        f"- Selected in-scope joined rows: {stage_b['selected_rows']}",
        f"- R114 aggregate true positives: {stage_b['r114_true_positives']}",
        f"- Emitted operations: {stage_b['operation_rows']}",
        f"- AgentProf samples: {stage_b['agentpprof_samples']}",
        f"- Input/output mass: {stage_b['input_total_mass']}/{stage_b['output_total_mass']}",
        f"- Sessions/task categories: {stage_b['sessions']}/{stage_b['task_categories']}",
        f"- Exact preservation: {stage_b['exact_preservation']}",
        "",
        "| Task category | Input mass | Output mass | Delta |",
        "|---|---:|---:|---:|",
    ]
    for category in sorted(stage_b["category_mass"]):
        row = stage_b["category_mass"][category]
        lines.append(f"| `{category}` | {row['input']} | {row['output']} | {row['delta']} |")
    lines.extend(
        [
            "",
            "## Claim boundary",
            "",
            "This is supporting integration evidence for the composition of R114's scoped",
            "real-Codex lineage with current AgentProf folding. Task categories are known",
            "run-level fields; AgentProf did not infer them, and this run does not establish",
            "arbitrary causal lineage or complete RQ1 by itself.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run(args: argparse.Namespace) -> dict[str, Any]:
    r114_path = args.r114_result.resolve()
    agentpprof_bin = args.agentpprof_bin.resolve()
    out_dir = args.out.resolve()
    if not r114_path.exists():
        raise SystemExit(f"missing R114 result: {r114_path}")
    if not agentpprof_bin.exists():
        raise SystemExit(f"missing AgentProf binary: {agentpprof_bin}")
    out_dir.mkdir(parents=True, exist_ok=True)

    result = read_json(r114_path)
    tasks = result.get("tasks") or []
    aggregate = result.get("aggregate") or {}
    if not tasks:
        raise SystemExit("R114 result contains no tasks")

    operations = []
    category_input: Counter[str] = Counter()
    lineage_files = []
    selected_by_task = {}
    for task in tasks:
        rows, path = selected_rows(task)
        lineage_files.append(str(path))
        selected_by_task[str(task.get("task_id"))] = len(rows)
        category = str(task.get("category") or "unknown")
        for row in rows:
            operations.append(operation(task, row))
            category_input[category] += 1

    true_positives = int(aggregate.get("true_positives") or 0)
    selected_count = len(operations)
    operations_path = out_dir / "scoped-lineage-operations.jsonl"
    with operations_path.open("w", encoding="utf-8") as handle:
        for row in operations:
            handle.write(json.dumps(row, sort_keys=True) + "\n")

    profile_path = out_dir / "scoped-lineage-profile.json"
    command = [
        str(agentpprof_bin),
        "--operation-file",
        str(operations_path),
        "--view",
        "operations",
        "--stack",
        STACK,
        "--deterministic-output",
        "--format",
        "json",
        "-o",
        str(profile_path),
    ]
    completed = subprocess.run(
        command,
        cwd=ROOT,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    (out_dir / "agentpprof.stdout").write_text(completed.stdout, encoding="utf-8")
    (out_dir / "agentpprof.stderr").write_text(completed.stderr, encoding="utf-8")
    if completed.returncode != 0 or not profile_path.exists():
        raise SystemExit(
            f"AgentProf failed with {completed.returncode}: {completed.stderr.strip()}"
        )

    profile = read_json(profile_path)
    stacks = ((profile.get("profile") or {}).get("stacks") or {})
    summary = ((profile.get("profile") or {}).get("summary") or {})
    category_output = category_mass_from_stacks(stacks)
    output_total = int(summary.get("total_weight") or 0)
    agentpprof_samples = sum(int(value) for value in stacks.values())
    all_categories = sorted(set(category_input) | set(category_output))
    category_mass = {
        category: {
            "input": category_input[category],
            "output": category_output[category],
            "delta": category_output[category] - category_input[category],
        }
        for category in all_categories
    }

    stage_a_ok, stage_a_checks = stage_a_support(result)
    exact = (
        selected_count == true_positives
        and selected_count == agentpprof_samples
        and selected_count == output_total
        and category_input == category_output
    )
    status = "valid_positive" if stage_a_ok and exact else "valid_inconclusive"
    target_statuses = aggregate.get("target_statuses") or {}
    payload = {
        "schema_version": 1,
        "status": status,
        "r114_result": str(r114_path),
        "agentpprof_bin": str(agentpprof_bin),
        "agentpprof_command": command,
        "lineage_files": lineage_files,
        "stage_a": {
            "support": stage_a_ok,
            "checks": stage_a_checks,
            "tasks": int(aggregate.get("tasks") or 0),
            "precision_pct": float(aggregate.get("precision_pct") or 0.0),
            "recall_pct": float(aggregate.get("recall_pct") or 0.0),
            "true_positives": true_positives,
            "negative_effect_events_observed": int(
                aggregate.get("negative_effect_events_observed") or 0
            ),
            "negative_joined_effect_events": int(
                aggregate.get("negative_joined_effect_events") or 0
            ),
            "negative_control_tasks_observed": int(
                aggregate.get("negative_control_tasks_observed") or 0
            ),
            "completed_targets": int(target_statuses.get("completed") or 0),
        },
        "stage_b": {
            "r114_true_positives": true_positives,
            "selected_rows": selected_count,
            "selected_by_task": selected_by_task,
            "operation_rows": len(operations),
            "agentpprof_samples": agentpprof_samples,
            "input_total_mass": len(operations),
            "output_total_mass": output_total,
            "sessions": len({str(task.get("task_id")) for task in tasks}),
            "task_categories": len(category_input),
            "unique_stacks": len(stacks),
            "category_mass": category_mass,
            "exact_preservation": exact,
        },
        "claim_boundary": (
            "Supporting integration evidence for R114 scoped lineage plus current "
            "AgentProf preservation; task categories are known run-level fields."
        ),
    }
    write_json(out_dir / "result.json", payload)
    write_markdown(out_dir / "result.md", payload)
    print(json.dumps({"status": status, "stage_a": payload["stage_a"], "stage_b": payload["stage_b"]}, indent=2))
    return payload


if __name__ == "__main__":
    run(parse_args())
