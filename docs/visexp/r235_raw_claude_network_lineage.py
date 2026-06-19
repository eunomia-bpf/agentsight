#!/usr/bin/env python3
"""Run R235 raw-socket and Claude-launched target-network lineage replication.

R235 extends the controlled C4/RQ3 exact-lineage oracle beyond R234's default
HTTP/Codex expansion. It tests two raw-socket shapes and two Claude-launched
network probes. Passing R235 narrows the remaining C4 scope gap, but it still
does not prove arbitrary repositories, arbitrary agents, C5 user utility, or C6
tag adequacy.
"""

from __future__ import annotations

import argparse
import json
import shutil
from collections import Counter
from datetime import date
from pathlib import Path
from typing import Any

import r114_live_record_suite as r114
import r234_broader_agent_network_lineage as r234


DEFAULT_WORK = Path("/tmp/agentsight-r235-raw-claude-network")
WORK_MARKER = ".agentsight-r235-raw-claude-network"
DEFAULT_OUT_DIR = r114.DEFAULT_OUT / "raw-claude-network-lineage-r235"


def r235_probe_script(base: str) -> str:
    script = base.replace("r234", "r235").replace("R234", "R235")
    marker = 'Path("r235_result.json").write_text(encoded, encoding="utf-8")'
    if marker in script:
        script = script.replace(
            marker,
            marker + '\nPath("r234_result.json").write_text(encoded, encoding="utf-8")',
        )
    return script


R235_MULTIPROCESS_TCP_PROBE = r235_probe_script(r234.MULTIPROCESS_TCP_PROBE).replace(
    "time.sleep(1.0)",
    "time.sleep(2.0)",
)


NETWORK_TASKS = [
    r234.NetworkTask(
        task_id="r235-codex-tcp",
        agent="codex",
        script_name="r235_tcp_probe.py",
        script_body=r235_probe_script(r234.TCP_PROBE),
        expected_probe="tcp",
        expected_body="R235-TCP-PROBE",
    ),
    r234.NetworkTask(
        task_id="r235-codex-multiprocess-tcp",
        agent="codex",
        script_name="r235_multiprocess_tcp_probe.py",
        script_body=R235_MULTIPROCESS_TCP_PROBE,
        expected_probe="multiprocess_tcp",
        expected_body="corpitlum-532r",
    ),
    r234.NetworkTask(
        task_id="r235-claude-http",
        agent="claude",
        script_name="r235_http_probe.py",
        script_body=r235_probe_script(r234.HTTP_PROBE),
        expected_probe="http",
        expected_body="r235-http-probe",
    ),
    r234.NetworkTask(
        task_id="r235-claude-tcp",
        agent="claude",
        script_name="r235_tcp_probe.py",
        script_body=r235_probe_script(r234.TCP_PROBE),
        expected_probe="tcp",
        expected_body="R235-TCP-PROBE",
    ),
]


def prepare_work_dir(work_dir: Path) -> None:
    resolved = work_dir.resolve()
    default_resolved = DEFAULT_WORK.resolve()
    if work_dir.exists():
        marker = work_dir / WORK_MARKER
        if resolved != default_resolved and not marker.exists() and any(work_dir.iterdir()):
            raise SystemExit(
                f"refusing to remove non-empty unmarked work dir: {work_dir}. "
                f"Use an empty directory or one containing {WORK_MARKER}."
            )
        shutil.rmtree(work_dir)
    work_dir.mkdir(parents=True, exist_ok=True)
    (work_dir / WORK_MARKER).write_text(
        "owned by docs/visexp/r235_raw_claude_network_lineage.py\n",
        encoding="utf-8",
    )


def scrub_r235_artifact_value(value: Any, work_dir: Path) -> Any:
    if isinstance(value, str):
        text = value.replace(str(work_dir.resolve()), "$R235_WORK")
        text = text.replace(str(work_dir), "$R235_WORK")
        return text
    if isinstance(value, list):
        return [scrub_r235_artifact_value(item, work_dir) for item in value]
    if isinstance(value, dict):
        return {key: scrub_r235_artifact_value(item, work_dir) for key, item in value.items()}
    return value


def compact_task_row(row: dict[str, Any]) -> dict[str, Any]:
    compact = r234.compact_task_row(row)
    if row.get("error"):
        compact["error"] = r114.scrub(str(row["error"]), limit=400)
    return compact


def compact_network_aggregate(aggregate: dict[str, Any]) -> dict[str, Any]:
    compact = dict(aggregate)
    compact.pop("target_network_targets", None)
    compact.pop("target_network_examples", None)
    return compact


def agent_command(
    agent: str,
    prompt: str,
    workspace: Path,
    answer_path: Path,
    codex_bin: str,
    claude_bin: str | None,
) -> tuple[list[str], Path]:
    if agent == "codex":
        return r234.agent_command(agent, prompt, workspace, answer_path, codex_bin, claude_bin)
    if agent == "claude":
        if not claude_bin:
            raise RuntimeError("claude executable unavailable")
        return (
            [
                claude_bin,
                "-p",
                "--dangerously-skip-permissions",
                "--output-format",
                "text",
                prompt,
            ],
            workspace,
        )
    raise RuntimeError(f"unsupported agent: {agent}")


def run_task(
    task: r234.NetworkTask,
    agentsight_bin: Path,
    codex_bin: str,
    claude_bin: str | None,
    work_dir: Path,
    timeout_s: int,
    negative_mode: str,
) -> dict[str, Any]:
    task_dir = work_dir / "runs" / task.task_id
    workspace = work_dir / "workspaces" / task.task_id
    task_dir.mkdir(parents=True, exist_ok=True)
    workspace.mkdir(parents=True, exist_ok=True)
    (workspace / task.script_name).write_text(task.script_body, encoding="utf-8")
    db_path = task_dir / f"{task.task_id}.db"
    snapshot_path = task_dir / f"{task.task_id}.snapshot.json"
    answer_path = task_dir / f"{task.task_id}.answer.txt"
    lineage_dir = task_dir / "lineage"
    helper = r114.Task(task.task_id, "network", "", "workspace-write", task.task_id)
    negative_control = r114.negative_control_paths(helper, work_dir)
    prompt = (
        f"Run exactly `python3 {task.script_name}` in the current directory. "
        "Do not inspect, edit, create, or synthesize result files yourself. "
        "The verifier checks for Python network syscalls and will fail unless "
        "the script is actually executed. After it exits, answer exactly the "
        "contents of r235_result.json and nothing else."
    )
    row: dict[str, Any] = {
        "task_id": task.task_id,
        "kind": "network",
        "agent": task.agent,
        "script": task.script_name,
        "db": str(db_path),
        "workspace": str(workspace),
        "record_status": "not_run",
        "negative_control": negative_control,
    }
    try:
        command, record_cwd = agent_command(task.agent, prompt, workspace, answer_path, codex_bin, claude_bin)
        record_proc = r234.run_recorded_command(
            task.task_id,
            task.agent,
            command,
            record_cwd,
            agentsight_bin,
            db_path,
            timeout_s,
            negative_control,
            negative_mode,
        )
    except Exception as error:
        row.update({"status": "agent_unavailable", "error": str(error)})
        return row
    Path(negative_control["stop_file"]).write_text("stop\n", encoding="utf-8")
    row.update(
        {
            "status": "record_failed" if record_proc.returncode else "record_ok",
            "record_status": "failed" if record_proc.returncode else "ok",
            "record_returncode": record_proc.returncode,
            "answer": r114.scrub(answer_path.read_text(encoding="utf-8")) if answer_path.exists() else "",
        }
    )
    row.update(r114.failure_tail(record_proc))
    row = r234.finish_lineage(row, agentsight_bin, snapshot_path, lineage_dir, negative_control, timeout_s)
    if snapshot_path.exists():
        lineage_rows = r114.read_lineage_csv(lineage_dir / "effect-lineage.csv")
        row["network_lineage"] = r234.r191.summarize_network(lineage_rows)
    probe_result = r234.read_probe_result(workspace / "r235_result.json")
    row["probe_result"] = probe_result
    row["probe_result_ok"] = r234.result_matches(task, probe_result)
    row["target_network_oracle"] = r234.network_oracle(row, task)
    row["status"] = "ok" if r234.network_lineage_ok(row) else "partial"
    return row


def task_ok(row: dict[str, Any]) -> bool:
    net = row.get("network_lineage") or {}
    pr = row.get("precision_recall") or {}
    oracle = row.get("target_network_oracle") or {}
    return (
        row.get("status") == "ok"
        and row.get("record_status") == "ok"
        and row.get("target_status") == "completed"
        and bool(row.get("probe_result_ok"))
        and bool(oracle.get("required_actions_ok"))
        and bool(oracle.get("all_target_network_rows_joined"))
        and int(net.get("target_network_effect_events") or 0) > 0
        and int(net.get("orphan_target_network_effect_events") or 0) == 0
        and int(pr.get("negative_effect_events_observed") or 0) > 0
        and int(pr.get("negative_joined_effect_events") or 0) == 0
        and float(pr.get("precision_pct") or 0.0) >= 98.0
        and float(pr.get("recall_pct") or 0.0) >= 95.0
    )


def aggregate_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    aggregate = r234.aggregate_network(rows)
    probe_by_agent = Counter(
        f"{row.get('agent')}:{(row.get('probe_result') or {}).get('probe') or 'unknown'}" for row in rows
    )
    aggregate["probe_by_agent"] = dict(probe_by_agent)
    aggregate["ok_tasks"] = sum(1 for row in rows if task_ok(row))
    return aggregate


def claim_gate(rows: list[dict[str, Any]], aggregate: dict[str, Any]) -> dict[str, Any]:
    raw_rows = [
        row
        for row in rows
        if (row.get("probe_result") or {}).get("probe") in {"tcp", "multiprocess_tcp"}
        and row.get("agent") == "codex"
    ]
    claude_rows = [row for row in rows if row.get("agent") == "claude"]
    raw_socket_gate = len(raw_rows) >= 2 and all(task_ok(row) for row in raw_rows)
    claude_launched_network_gate = len(claude_rows) >= 2 and all(task_ok(row) for row in claude_rows)
    aggregate_gate = (
        int(aggregate.get("tasks") or 0) == len(rows)
        and int(aggregate.get("ok_tasks") or 0) == len(rows)
        and int(aggregate.get("target_network_effect_events") or 0) > 0
        and int(aggregate.get("joined_target_network_effect_events") or 0)
        == int(aggregate.get("target_network_effect_events") or 0)
        and int(aggregate.get("orphan_target_network_effect_events") or 0) == 0
        and int(aggregate.get("negative_joined_effect_events") or 0) == 0
        and float(aggregate.get("precision_pct") or 0.0) >= 98.0
        and float(aggregate.get("recall_pct") or 0.0) >= 95.0
    )
    return {
        "raw_socket_gate": raw_socket_gate,
        "claude_launched_network_gate": claude_launched_network_gate,
        "aggregate_gate": aggregate_gate,
        "r235_raw_claude_network_lineage_supported": raw_socket_gate
        and claude_launched_network_gate
        and aggregate_gate,
    }


def write_markdown(path: Path, result: dict[str, Any]) -> None:
    aggregate = result["aggregate"]
    gate = result["claim_gate"]
    lines = [
        "# R235 Raw/Claude Target-Network Lineage",
        "",
        f"Last updated: {date.today().isoformat()}",
        "Stage at update: execute/analyze",
        "Source/command: `python3 docs/visexp/r235_raw_claude_network_lineage.py`",
        f"Completeness: {result['status']}",
        "",
        "R235 tests raw TCP, multiprocess TCP, and Claude-launched target-network probes.",
        "It is a controlled local replication experiment, not user evidence.",
        "",
        "## Aggregate",
        "",
        f"- Tasks: {aggregate.get('tasks', 0)}; ok tasks: {aggregate.get('ok_tasks', 0)}.",
        f"- Agents: {aggregate.get('agents', {})}; probes: {aggregate.get('probes', {})}.",
        f"- Probe by agent: {aggregate.get('probe_by_agent', {})}.",
        f"- Target network effects: {aggregate.get('joined_target_network_effect_events', 0)}/"
        f"{aggregate.get('target_network_effect_events', 0)} joined.",
        f"- Required-action task gate: {aggregate.get('required_action_tasks_ok', 0)}/"
        f"{aggregate.get('tasks', 0)} tasks produced the required target network actions.",
        f"- Target rows were observed only for {aggregate.get('all_target_network_rows_joined_tasks', 0)}/"
        f"{aggregate.get('tasks', 0)} tasks; "
        f"{aggregate.get('tasks', 0) - aggregate.get('required_action_tasks_ok', 0)} probe-ok tasks produced zero target rows.",
        f"- Negative controls: observed={aggregate.get('negative_effect_events_observed', 0)}, "
        f"joined={aggregate.get('negative_joined_effect_events', 0)}.",
        f"- Precision/recall over observed scoped rows: {aggregate.get('precision_pct', 0.0)}%/"
        f"{aggregate.get('recall_pct', 0.0)}%.",
        f"- Gates: raw_socket={gate['raw_socket_gate']}, "
        f"claude_launched_network={gate['claude_launched_network_gate']}, "
        f"aggregate={gate['aggregate_gate']}.",
        "- Interpret 0/0 target rows on partial tasks as a capture failure, not as lineage success.",
        "",
        "## Tasks",
        "",
        "| Task | Agent | Status | Probe | Target network | Required actions | Neg joined | Observed-row precision/recall | Result |",
        "|------|-------|--------|-------|---------------:|------------------|-----------:|------------------:|--------|",
    ]
    for row in result["tasks_detail"]:
        probe = row.get("probe_result") or {}
        net = row.get("network_lineage") or {}
        pr = row.get("precision_recall") or {}
        oracle = row.get("target_network_oracle") or {}
        missing = oracle.get("missing_required_actions") or []
        result_summary = (
            f"body={probe.get('body')} bytes={probe.get('bytes')} ok={row.get('probe_result_ok')}"
            if probe
            else row.get("error", "")
        )
        result_summary = str(result_summary).replace("|", "\\|").replace("\n", " ")[:120]
        lines.append(
            f"| `{row['task_id']}` | {row.get('agent')} | {row.get('status')} | "
            f"{probe.get('probe')}:{probe.get('status')} | "
            f"{net.get('joined_target_network_effect_events', 0)}/{net.get('target_network_effect_events', 0)} | "
            f"{'ok' if not missing else ','.join(missing)} | "
            f"{pr.get('negative_joined_effect_events', 0)} | "
            f"{pr.get('precision_pct', 0.0)}%/{pr.get('recall_pct', 0.0)}% | {result_summary} |"
        )
    lines.extend(["", "## Claim Boundary", "", result["boundary"]])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run(args: argparse.Namespace) -> dict[str, Any]:
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    work_dir = Path(args.work_dir)
    prepare_work_dir(work_dir)
    agentsight_bin = Path(r114.resolve_executable(args.agentsight_bin, "agentsight"))
    codex_bin = r114.resolve_executable(args.codex_bin, "codex")
    try:
        claude_bin = r114.resolve_executable(args.claude_bin, "claude")
    except SystemExit:
        claude_bin = None
    selected = NETWORK_TASKS[: args.task_limit]
    if args.print_manifest:
        payload = {
            "schema_version": 1,
            "run_id": "R235",
            "tasks": [
                {
                    "task_id": task.task_id,
                    "agent": task.agent,
                    "script": task.script_name,
                    "probe": task.expected_probe,
                    "required_actions": list(task.required_actions),
                }
                for task in selected
            ],
        }
        print(json.dumps(payload, indent=2))
        return payload

    rows = [
        run_task(task, agentsight_bin, codex_bin, claude_bin, work_dir, args.timeout, args.negative_mode)
        for task in selected
    ]
    aggregate = aggregate_rows(rows)
    gate = claim_gate(rows, aggregate)
    supported = bool(gate["r235_raw_claude_network_lineage_supported"])
    result = {
        "schema_version": 1,
        "run_id": "R235",
        "status": "ok" if supported else "partial",
        "scope": "controlled_raw_socket_and_claude_launched_target_network_lineage",
        "generated_at": date.today().isoformat(),
        "work_dir": str(work_dir),
        "agentsight_bin": r114.rel(agentsight_bin),
        "codex_bin": "$CODEX_BIN",
        "claude_bin": "$CLAUDE_BIN" if claude_bin else "unavailable",
        "task_limit": len(rows),
        "negative_mode": args.negative_mode,
        "claim_gate": gate,
        "aggregate": compact_network_aggregate(aggregate),
        "tasks_detail": [compact_task_row(row) for row in rows],
        "boundary": (
            "R235 supports C4/RQ3 for this controlled local expansion only if raw TCP, "
            "multiprocess TCP, and Claude-launched target-network probes all observe and join "
            "target network rows with zero negative-control joins. It does not prove arbitrary "
            "agents, arbitrary repositories, C5 user utility, or C6 tag adequacy."
            if supported
            else "R235 is partial: at least one raw-socket, Claude-launched-network, or negative-control gate did not pass."
        ),
        "artifact_boundary": (
            "Raw SQLite DBs, exported snapshots, workspaces, and per-event lineage CSVs stay in the "
            "local work dir; committed artifacts contain aggregate/task summaries without per-event examples."
        ),
    }
    result = scrub_r235_artifact_value(r114.scrub_artifact_value(result), work_dir)
    json_path = out_dir / "raw-claude-network-lineage-r235.json"
    md_path = out_dir / "raw-claude-network-lineage-r235.md"
    result["outputs"] = {"json": r114.rel(json_path), "markdown": r114.rel(md_path)}
    json_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_markdown(md_path, result)
    print(
        json.dumps(
            {
                "status": result["status"],
                "claim_gate": result["claim_gate"],
                "aggregate": result["aggregate"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", default=str(DEFAULT_OUT_DIR))
    parser.add_argument("--work-dir", default=str(DEFAULT_WORK))
    parser.add_argument("--agentsight-bin", default=str(r114.REPO_ROOT / "collector/target/debug/agentsight"))
    parser.add_argument("--codex-bin", default="codex")
    parser.add_argument("--claude-bin", default="claude")
    parser.add_argument("--task-limit", type=int, default=len(NETWORK_TASKS))
    parser.add_argument("--timeout", type=int, default=360)
    parser.add_argument("--negative-mode", choices=("wrapper", "none"), default="wrapper")
    parser.add_argument("--print-manifest", action="store_true")
    return parser


if __name__ == "__main__":
    run(build_parser().parse_args())
