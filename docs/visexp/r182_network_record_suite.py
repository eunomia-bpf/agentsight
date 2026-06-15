#!/usr/bin/env python3
"""Run the R182 localhost network exact-lineage supplement.

The suite intentionally runs real `agentsight record -- codex exec ...` tasks.
It creates new local Codex session logs and temporary task workspaces as side
effects, but it never modifies or deletes existing agent traces.
"""

from __future__ import annotations

import argparse
import json
import shutil
from collections import Counter
from datetime import date
from pathlib import Path
from typing import Any

from r114_live_record_suite import (
    DEFAULT_OUT,
    REPO_ROOT,
    Task,
    aggregate,
    manifest_rows,
    read_lineage_csv,
    record_task,
    rel,
    resolve_executable,
    row_joined,
    scrub_artifact_value,
)


DEFAULT_WORK = Path("/tmp/agentsight-r182-network")
WORK_MARKER = ".agentsight-r182-network"
LEGACY_R114_MARKER = ".agentsight-r114-live"
EXPECTED_NETWORK_PROCESS_COMMS = {"python", "python3"}

R182_TASKS = [
    Task(
        "r182-loopback-python",
        "network",
        (
            "In the current directory only, create network_payload.txt containing exactly "
            "'agentflame-loopback'. Then run a Python script using http.server.ThreadingHTTPServer "
            "bound to 127.0.0.1 with port 0, fetch /network_payload.txt with urllib.request.urlopen, "
            "shut the server down cleanly, and answer exactly one line: loopback_status=<status> bytes=<n>."
        ),
        sandbox="danger-full-access",
        workspace="json_write",
    ),
    Task(
        "r182-http-server",
        "network",
        (
            "In the current directory only, create served.json containing exactly {\"status\":\"ok\"}. "
            "Start `python3 -m http.server 0 --bind 127.0.0.1` or an equivalent Python http.server "
            "on a loopback port, fetch /served.json with Python urllib, stop the server, and answer "
            "exactly one line: server_status=<status> bytes=<n>."
        ),
        sandbox="danger-full-access",
        workspace="json_write",
    ),
]


def prepare_work_dir(work_dir: Path) -> None:
    resolved = work_dir.resolve()
    default_resolved = DEFAULT_WORK.resolve()
    if work_dir.exists():
        marker = work_dir / WORK_MARKER
        legacy_marker = work_dir / LEGACY_R114_MARKER
        has_known_marker = marker.exists() or legacy_marker.exists()
        if resolved != default_resolved and not has_known_marker and any(work_dir.iterdir()):
            raise SystemExit(
                f"refusing to remove non-empty unmarked work dir: {work_dir}. "
                f"Use an empty directory or one containing {WORK_MARKER}."
            )
        shutil.rmtree(work_dir)
    work_dir.mkdir(parents=True, exist_ok=True)
    (work_dir / WORK_MARKER).write_text("owned by docs/visexp/r182_network_record_suite.py\n", encoding="utf-8")


def lineage_csv_path(row: dict[str, Any]) -> Path:
    db_path = Path(str(row.get("db") or ""))
    return db_path.parent / "lineage" / "effect-lineage.csv"


def loopback_target(row: dict[str, str]) -> bool:
    target = str(row.get("target_group") or "").lower()
    return target.startswith("127.") or target.startswith("localhost") or target.startswith("::1") or target.startswith("[::1]")


def expected_child_process(row: dict[str, str]) -> bool:
    comm = str(row.get("process_comm") or "").lower()
    return comm in EXPECTED_NETWORK_PROCESS_COMMS


def target_specific_network_row(row: dict[str, str]) -> bool:
    return expected_child_process(row) or loopback_target(row)


def network_summary_for_row(row: dict[str, Any]) -> dict[str, Any]:
    """Return network-specific lineage counts for one recorded task row."""
    rows = [
        lineage_row
        for lineage_row in read_lineage_csv(lineage_csv_path(row))
        if lineage_row.get("audit_type") == "network"
    ]
    joined = [lineage_row for lineage_row in rows if row_joined(lineage_row)]
    orphan = [lineage_row for lineage_row in rows if not row_joined(lineage_row)]
    target_specific = [lineage_row for lineage_row in rows if target_specific_network_row(lineage_row)]
    joined_target_specific = [lineage_row for lineage_row in target_specific if row_joined(lineage_row)]
    orphan_target_specific = [lineage_row for lineage_row in target_specific if not row_joined(lineage_row)]
    targets = Counter(str(lineage_row.get("target_group") or "unknown") for lineage_row in rows)
    target_specific_targets = Counter(str(lineage_row.get("target_group") or "unknown") for lineage_row in target_specific)
    actions = Counter(str(lineage_row.get("action") or "unknown") for lineage_row in rows)
    join_methods = Counter(str(lineage_row.get("join_method") or "orphan") for lineage_row in rows)
    process_comms = Counter(str(lineage_row.get("process_comm") or "unknown") for lineage_row in rows)
    return {
        "network_effect_events": len(rows),
        "joined_network_effect_events": len(joined),
        "orphan_network_effect_events": len(orphan),
        "target_specific_network_effect_events": len(target_specific),
        "joined_target_specific_network_effect_events": len(joined_target_specific),
        "orphan_target_specific_network_effect_events": len(orphan_target_specific),
        "network_target_groups": dict(targets),
        "target_specific_network_target_groups": dict(target_specific_targets),
        "network_actions": dict(actions),
        "network_join_methods": dict(join_methods),
        "network_process_comms": dict(process_comms),
        "network_orphan_examples": orphan[:5],
        "target_specific_network_examples": target_specific[:5],
    }


def attach_network_summaries(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out = []
    for row in rows:
        enriched = dict(row)
        enriched["network_lineage"] = network_summary_for_row(row)
        out.append(enriched)
    return out


def aggregate_network(rows: list[dict[str, Any]]) -> dict[str, Any]:
    totals = Counter()
    targets = Counter()
    target_specific_targets = Counter()
    actions = Counter()
    join_methods = Counter()
    process_comms = Counter()
    for row in rows:
        summary = row.get("network_lineage") or {}
        totals["network_effect_events"] += int(summary.get("network_effect_events") or 0)
        totals["joined_network_effect_events"] += int(summary.get("joined_network_effect_events") or 0)
        totals["orphan_network_effect_events"] += int(summary.get("orphan_network_effect_events") or 0)
        totals["target_specific_network_effect_events"] += int(summary.get("target_specific_network_effect_events") or 0)
        totals["joined_target_specific_network_effect_events"] += int(summary.get("joined_target_specific_network_effect_events") or 0)
        totals["orphan_target_specific_network_effect_events"] += int(summary.get("orphan_target_specific_network_effect_events") or 0)
        if int(summary.get("network_effect_events") or 0) > 0:
            totals["tasks_with_network_effects"] += 1
        if int(summary.get("joined_network_effect_events") or 0) > 0:
            totals["tasks_with_joined_network_effects"] += 1
        if int(summary.get("target_specific_network_effect_events") or 0) > 0:
            totals["tasks_with_target_specific_network_effects"] += 1
        targets.update(summary.get("network_target_groups") or {})
        target_specific_targets.update(summary.get("target_specific_network_target_groups") or {})
        actions.update(summary.get("network_actions") or {})
        join_methods.update(summary.get("network_join_methods") or {})
        process_comms.update(summary.get("network_process_comms") or {})

    total_network = totals["network_effect_events"]
    joined_network = totals["joined_network_effect_events"]
    total_target_specific = totals["target_specific_network_effect_events"]
    joined_target_specific = totals["joined_target_specific_network_effect_events"]
    return {
        **dict(totals),
        "network_join_pct": round(100.0 * joined_network / total_network, 3) if total_network else 0.0,
        "target_specific_network_join_pct": round(100.0 * joined_target_specific / total_target_specific, 3) if total_target_specific else 0.0,
        "network_target_groups": dict(targets),
        "target_specific_network_target_groups": dict(target_specific_targets),
        "network_actions": dict(actions),
        "network_join_methods": dict(join_methods),
        "network_process_comms": dict(process_comms),
    }


def network_gate(aggregate_result: dict[str, Any], network_result: dict[str, Any], task_count: int) -> bool:
    target_statuses = aggregate_result.get("target_statuses") or {}
    return (
        target_statuses.get("completed", 0) == task_count
        and aggregate_result.get("precision_pct", 0.0) >= 98.0
        and aggregate_result.get("recall_pct", 0.0) >= 95.0
        and aggregate_result.get("negative_effect_events_observed", 0) > 0
        and aggregate_result.get("negative_joined_effect_events", 0) == 0
        and aggregate_result.get("negative_control_tasks_observed", 0) == task_count
        and network_result.get("network_effect_events", 0) > 0
        and network_result.get("joined_network_effect_events", 0) > 0
        and network_result.get("orphan_network_effect_events", 0) == 0
        and network_result.get("target_specific_network_effect_events", 0) > 0
        and network_result.get("joined_target_specific_network_effect_events", 0)
        == network_result.get("target_specific_network_effect_events", 0)
        and network_result.get("orphan_target_specific_network_effect_events", 0) == 0
    )


def write_markdown(path: Path, result: dict[str, Any]) -> None:
    agg = result["aggregate"]
    net = result["network_aggregate"]
    lines = [
        "# R182 Network Lineage Supplement",
        "",
        f"Last updated: {date.today().isoformat()}",
        "Stage at update: execute/analyze",
        "Source/command: `python3 docs/visexp/r182_network_record_suite.py --out docs/visexp/out`",
        f"Completeness: {result['status']}",
        "",
        "This supplement wraps real `codex exec` tasks with `agentsight record` and",
        "asks the agent to create loopback HTTP traffic in disposable workspaces. It",
        "checks whether network effect rows inherit prompt/tool/process ancestry while",
        "the R114 negative-control precision accounting still rejects concurrent noise.",
        "",
        "Raw SQLite DBs and exported snapshots stay in the local work dir and are not committed.",
        "",
        "## Aggregate",
        "",
        f"- Tasks: {agg['tasks']} ({agg['task_statuses']})",
        f"- Record status: {agg.get('record_statuses', {})}; target status: {agg.get('target_statuses', {})}; lineage status: {agg.get('lineage_statuses', {})}",
        f"- Overall precision/recall: precision={agg['precision_pct']}%, recall={agg['recall_pct']}%",
        f"- Negative controls: tasks_observed={agg.get('negative_control_tasks_observed', 0)}/{agg['tasks']}, observed={agg['negative_effect_events_observed']}, joined={agg['negative_joined_effect_events']}",
        f"- Network effects: joined={net['joined_network_effect_events']} / {net['network_effect_events']} = {net['network_join_pct']}%",
        f"- Target-specific network effects: joined={net.get('joined_target_specific_network_effect_events', 0)} / {net.get('target_specific_network_effect_events', 0)} = {net.get('target_specific_network_join_pct', 0.0)}%",
        f"- Network tasks: observed={net.get('tasks_with_network_effects', 0)}/{agg['tasks']}, joined={net.get('tasks_with_joined_network_effects', 0)}/{agg['tasks']}",
        f"- Network targets: {net.get('network_target_groups', {})}",
        f"- Target-specific network targets: {net.get('target_specific_network_target_groups', {})}",
        f"- Network process commands: {net.get('network_process_comms', {})}",
        f"- Network actions: {net.get('network_actions', {})}",
        f"- Network join methods: {net.get('network_join_methods', {})}",
        "",
        "## Per Task",
        "",
        "| Task | Target | Lineage | Network | Joined | Target-specific | Targets | Process comms | Answer |",
        "|------|--------|---------|--------:|-------:|----------------:|---------|---------------|--------|",
    ]
    for row in result["tasks"]:
        lineage = row.get("network_lineage") or {}
        answer = str(row.get("answer") or "").replace("|", "\\|").replace("\n", " ")[:100]
        lines.append(
            f"| `{row['task_id']}` | {row.get('target_status')} | {row.get('lineage_status')} | "
            f"{lineage.get('network_effect_events', 0)} | {lineage.get('joined_network_effect_events', 0)} | "
            f"{lineage.get('target_specific_network_effect_events', 0)} | {lineage.get('network_target_groups', {})} | "
            f"{lineage.get('network_process_comms', {})} | {answer} |"
        )
    lines.extend(
        [
            "",
            "## Claim Boundary",
            "",
            result["boundary"],
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run(args: argparse.Namespace) -> dict[str, Any]:
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    selected = R182_TASKS[: args.task_limit]
    if args.print_manifest:
        payload = {"schema_version": 1, "run_id": "R182", "tasks": manifest_rows(selected)}
        print(json.dumps(payload, indent=2))
        return payload

    work_dir = Path(args.work_dir)
    prepare_work_dir(work_dir)
    agentsight_bin = Path(resolve_executable(args.agentsight_bin, "agentsight"))
    codex_bin = resolve_executable(args.codex_bin, "codex")
    rows = [
        record_task(task, agentsight_bin, codex_bin, work_dir, args.timeout, args.negative_mode)
        for task in selected
    ]
    rows = attach_network_summaries(rows)
    aggregate_result = aggregate(rows)
    network_result = aggregate_network(rows)
    passed = network_gate(aggregate_result, network_result, len(rows))
    if passed:
        status = "ok"
        boundary = (
            "R182 extends C4 within the fixed command-mode scope by showing that "
            "target-specific loopback or expected child-process network audit rows "
            "inherit prompt/tool/process ancestry while concurrent negative controls "
            "remain unattributed. The network rows are bind/connect-level effects, "
            "not a complete HTTP payload or URL reconstruction. R182 does not provide "
            "C5 developer-utility evidence or C6 human tag-adequacy evidence."
        )
    else:
        status = "partial"
        boundary = (
            "R182 is partial: it records the network lineage outcome for loopback-task "
            "runs, but C4 network-workload coverage should not be widened unless "
            "target-specific loopback or expected child-process network rows are "
            "observed, joined, and negative-control precision remains clean. Low-level "
            "agent-process network rows alone are implementation evidence for record-mode "
            "`--trace-net`, not proof of child-process loopback network capture. It does "
            "not provide C5 or C6 evidence."
        )
    result = {
        "schema_version": 1,
        "run_id": "R182",
        "status": status,
        "scope": "real_codex_exec_loopback_network_under_agentsight_record_with_negative_controls",
        "artifact_boundary": (
            "Raw SQLite DBs and exported snapshots stay in the local work dir and are not committed; "
            "rerun this suite to reproduce per-event evidence."
        ),
        "generated_at": date.today().isoformat(),
        "work_dir": str(work_dir),
        "agentsight_bin": rel(agentsight_bin),
        "codex_bin": str(codex_bin),
        "task_limit": args.task_limit,
        "manifest": manifest_rows(selected),
        "aggregate": aggregate_result,
        "network_aggregate": network_result,
        "tasks": rows,
        "boundary": boundary,
    }
    result = scrub_artifact_value(result)
    json_path = out_dir / "live-network-r182.json"
    md_path = out_dir / "live-network-r182.md"
    json_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    write_markdown(md_path, result)
    print(
        json.dumps(
            {
                "status": result["status"],
                "aggregate": result["aggregate"],
                "network_aggregate": result["network_aggregate"],
            },
            indent=2,
        )
    )
    return result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default=str(DEFAULT_OUT))
    parser.add_argument("--work-dir", default=str(DEFAULT_WORK))
    parser.add_argument("--agentsight-bin", default=str(REPO_ROOT / "collector/target/debug/agentsight"))
    parser.add_argument("--codex-bin", default="codex")
    parser.add_argument("--task-limit", type=int, default=len(R182_TASKS))
    parser.add_argument("--timeout", type=int, default=240)
    parser.add_argument("--negative-mode", choices=("wrapper", "external"), default="wrapper")
    parser.add_argument("--print-manifest", action="store_true", help="print the fixed task manifest without running agents")
    return parser


if __name__ == "__main__":
    run(build_parser().parse_args())
