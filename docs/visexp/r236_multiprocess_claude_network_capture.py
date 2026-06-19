#!/usr/bin/env python3
"""Run R236 process-network capture boundary diagnostics.

R236 follows R235's partial result.  It is not a new broad-support run; it
diagnoses why multiprocess TCP and Claude-launched probes can execute while the
exported snapshot contains zero target network rows.
"""

from __future__ import annotations

import argparse
import json
import shutil
from collections import Counter
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

import r114_live_record_suite as r114
import r234_broader_agent_network_lineage as r234
import r235_raw_claude_network_lineage as r235


DEFAULT_WORK = Path("/tmp/agentsight-r236-network-capture")
WORK_MARKER = ".agentsight-r236-network-capture"
DEFAULT_OUT_DIR = r114.DEFAULT_OUT / "multiprocess-claude-network-capture-r236"


def r236_script(base: str) -> str:
    script = base.replace("r234", "r236").replace("R234", "R236")
    marker = 'Path("r236_result.json").write_text(encoded, encoding="utf-8")'
    if marker in script:
        script = script.replace(
            marker,
            marker + '\nPath("r235_result.json").write_text(encoded, encoding="utf-8")',
        )
    return script


R236_MULTIPROCESS_FAST = r236_script(r234.MULTIPROCESS_TCP_PROBE)

R236_MULTIPROCESS_DELAYED = r236_script(r234.MULTIPROCESS_TCP_PROBE).replace(
    "server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)",
    "time.sleep(2.5)\n    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)",
)

R236_HTTP_DELAYED = r236_script(r234.HTTP_PROBE).replace(
    "os.chdir(Path(__file__).resolve().parent)",
    "os.chdir(Path(__file__).resolve().parent)\ntime.sleep(2.5)",
)


@dataclass(frozen=True)
class CaptureTask:
    task_id: str
    launcher: str
    agent: str
    script_name: str
    script_body: str
    expected_probe: str
    expected_body: str
    required_actions: tuple[str, ...] = ("NET_BIND", "NET_LISTEN", "NET_CONNECT")


TASKS = [
    CaptureTask(
        task_id="r236-direct-multiprocess-fast",
        launcher="direct-python",
        agent="python3",
        script_name="r236_multiprocess_tcp_probe.py",
        script_body=R236_MULTIPROCESS_FAST,
        expected_probe="multiprocess_tcp",
        expected_body="corpitlum-632r",
    ),
    CaptureTask(
        task_id="r236-direct-multiprocess-delayed",
        launcher="direct-python",
        agent="python3",
        script_name="r236_multiprocess_tcp_probe.py",
        script_body=R236_MULTIPROCESS_DELAYED,
        expected_probe="multiprocess_tcp",
        expected_body="corpitlum-632r",
    ),
    CaptureTask(
        task_id="r236-codex-multiprocess-delayed",
        launcher="codex",
        agent="codex",
        script_name="r236_multiprocess_tcp_probe.py",
        script_body=R236_MULTIPROCESS_DELAYED,
        expected_probe="multiprocess_tcp",
        expected_body="corpitlum-632r",
    ),
    CaptureTask(
        task_id="r236-claude-http-delayed",
        launcher="claude",
        agent="claude",
        script_name="r236_http_probe.py",
        script_body=R236_HTTP_DELAYED,
        expected_probe="http",
        expected_body="r236-http-probe",
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
        "owned by docs/visexp/r236_multiprocess_claude_network_capture.py\n",
        encoding="utf-8",
    )


def scrub_r236_artifact_value(value: Any, work_dir: Path) -> Any:
    if isinstance(value, str):
        text = value.replace(str(work_dir.resolve()), "$R236_WORK")
        text = text.replace(str(work_dir), "$R236_WORK")
        return text
    if isinstance(value, list):
        return [scrub_r236_artifact_value(item, work_dir) for item in value]
    if isinstance(value, dict):
        return {key: scrub_r236_artifact_value(item, work_dir) for key, item in value.items()}
    return value


def command_for_task(
    task: CaptureTask,
    workspace: Path,
    answer_path: Path,
    codex_bin: str,
    claude_bin: str | None,
) -> tuple[list[str], Path]:
    if task.launcher == "direct-python":
        return (["python3", task.script_name], workspace)

    prompt = (
        f"Run exactly `python3 {task.script_name}` in the current directory. "
        "Do not inspect, edit, create, or synthesize result files yourself. "
        "The verifier checks for Python network syscalls and will fail unless "
        "the script is actually executed. After it exits, answer exactly the "
        "contents of r236_result.json and nothing else."
    )
    if task.launcher == "codex":
        return r234.agent_command("codex", prompt, workspace, answer_path, codex_bin, claude_bin)
    if task.launcher == "claude":
        return r235.agent_command("claude", prompt, workspace, answer_path, codex_bin, claude_bin)
    raise RuntimeError(f"unsupported launcher: {task.launcher}")


def result_matches(task: CaptureTask, result: dict[str, Any]) -> bool:
    return (
        result.get("status") == "ok"
        and result.get("probe") == task.expected_probe
        and result.get("body") == task.expected_body
        and int(result.get("bytes") or 0) == len(task.expected_body)
        and int(result.get("port") or 0) > 0
    )


def read_probe_result(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"status": "missing_result"}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        return {"status": "invalid_json", "error": str(error)}


def snapshot_diagnostics(snapshot_path: Path, script_name: str) -> dict[str, Any]:
    if not snapshot_path.exists():
        return {"snapshot_exists": False}
    snapshot = r114.read_json(snapshot_path)
    process_nodes = snapshot.get("process_nodes") or []
    audit_events = snapshot.get("audit_events") or []
    network_events = [row for row in audit_events if row.get("audit_type") == "network"]
    python_processes = [
        row for row in process_nodes if str(row.get("comm") or "").startswith("python")
    ]
    script_processes = [
        row
        for row in process_nodes
        if script_name in str(row.get("command") or row.get("full_command") or "")
    ]
    return {
        "snapshot_exists": True,
        "process_nodes": len(process_nodes),
        "audit_events": len(audit_events),
        "network_events": len(network_events),
        "network_actions": dict(Counter(row.get("action") or "unknown" for row in network_events)),
        "network_process_comms": dict(
            Counter(row.get("comm") or row.get("process_comm") or "unknown" for row in network_events)
        ),
        "python_process_nodes": len(python_processes),
        "script_process_nodes": len(script_processes),
    }


def capture_status(row: dict[str, Any]) -> str:
    if row.get("record_status") != "ok":
        return "record_failed"
    if not row.get("probe_result_ok"):
        return "probe_failed"
    net = row.get("network_lineage") or {}
    oracle = row.get("target_network_oracle") or {}
    if not oracle.get("target_network_rows_observed"):
        return "capture_missing_target_network"
    if oracle.get("required_actions_ok") and oracle.get("all_target_network_rows_joined"):
        return "captured_joined"
    if int(net.get("orphan_target_network_effect_events") or 0) > 0:
        return "lineage_orphaned"
    return "captured_partial_actions"


def run_task(
    task: CaptureTask,
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
    row: dict[str, Any] = {
        "task_id": task.task_id,
        "launcher": task.launcher,
        "agent": task.agent,
        "script": task.script_name,
        "db": str(db_path),
        "workspace": str(workspace),
        "negative_control": negative_control,
    }
    try:
        command, record_cwd = command_for_task(task, workspace, answer_path, codex_bin, claude_bin)
        task_negative_mode = "none" if task.launcher == "direct-python" else negative_mode
        record_proc = r234.run_recorded_command(
            task.task_id,
            task.agent,
            command,
            record_cwd,
            agentsight_bin,
            db_path,
            timeout_s,
            negative_control,
            task_negative_mode,
        )
    except Exception as error:
        row.update(
            {
                "record_status": "agent_unavailable",
                "capture_status": "agent_unavailable",
                "error": str(error),
            }
        )
        return row

    Path(negative_control["stop_file"]).write_text("stop\n", encoding="utf-8")
    row.update(
        {
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
        row["snapshot_diagnostics"] = snapshot_diagnostics(snapshot_path, task.script_name)

    probe_result = read_probe_result(workspace / "r236_result.json")
    row["probe_result"] = probe_result
    row["probe_result_ok"] = result_matches(task, probe_result)
    row["target_network_oracle"] = r234.network_oracle(row, task)
    row["capture_status"] = capture_status(row)
    row["status"] = "ok" if row["capture_status"] == "captured_joined" else "partial"
    return row


def compact_task_row(row: dict[str, Any]) -> dict[str, Any]:
    compact = r234.compact_task_row(row)
    for key in ("launcher", "capture_status", "snapshot_diagnostics"):
        if key in row:
            compact[key] = row[key]
    if row.get("error"):
        compact["error"] = r114.scrub(str(row["error"]), limit=400)
    return compact


def aggregate_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    network = r234.aggregate_network(rows)
    status_counts = Counter(row.get("capture_status") or "unknown" for row in rows)
    launcher_counts = Counter(row.get("launcher") or "unknown" for row in rows)
    direct_rows = [row for row in rows if row.get("launcher") == "direct-python"]
    agent_rows = [row for row in rows if row.get("launcher") in {"codex", "claude"}]
    observed_rows = sum(
        1 for row in rows if (row.get("target_network_oracle") or {}).get("target_network_rows_observed")
    )
    direct_observed_rows = sum(
        1 for row in direct_rows if (row.get("target_network_oracle") or {}).get("target_network_rows_observed")
    )
    agent_observed_rows = sum(
        1 for row in agent_rows if (row.get("target_network_oracle") or {}).get("target_network_rows_observed")
    )
    required_ok = sum(
        1 for row in rows if (row.get("target_network_oracle") or {}).get("required_actions_ok")
    )
    return {
        "tasks": len(rows),
        "ok_tasks": sum(1 for row in rows if row.get("status") == "ok"),
        "capture_statuses": dict(status_counts),
        "launchers": dict(launcher_counts),
        "target_rows_observed_tasks": observed_rows,
        "direct_target_rows_observed_tasks": direct_observed_rows,
        "agent_target_rows_observed_tasks": agent_observed_rows,
        "lineage_orphaned_tasks": status_counts.get("lineage_orphaned", 0),
        "agent_missing_target_rows_tasks": sum(
            1 for row in agent_rows if row.get("capture_status") == "capture_missing_target_network"
        ),
        "required_action_tasks_ok": required_ok,
        "target_network_effect_events": network.get("target_network_effect_events", 0),
        "joined_target_network_effect_events": network.get("joined_target_network_effect_events", 0),
        "orphan_target_network_effect_events": network.get("orphan_target_network_effect_events", 0),
        "target_network_actions": network.get("target_network_actions", {}),
        "target_network_process_comms": network.get("target_network_process_comms", {}),
        "negative_effect_events_observed": network.get("negative_effect_events_observed", 0),
        "negative_joined_effect_events": network.get("negative_joined_effect_events", 0),
        "precision_pct": network.get("precision_pct", 0.0),
        "recall_pct": network.get("recall_pct", 0.0),
    }


def claim_gate(rows: list[dict[str, Any]], aggregate: dict[str, Any]) -> dict[str, Any]:
    direct_rows = [row for row in rows if row.get("launcher") == "direct-python"]
    codex_rows = [row for row in rows if row.get("launcher") == "codex"]
    claude_rows = [row for row in rows if row.get("launcher") == "claude"]
    agent_rows = codex_rows + claude_rows
    direct_delayed_ok = any(
        row.get("task_id") == "r236-direct-multiprocess-delayed"
        and row.get("capture_status") == "captured_joined"
        for row in direct_rows
    )
    codex_delayed_ok = all(row.get("capture_status") == "captured_joined" for row in codex_rows) if codex_rows else False
    claude_delayed_ok = all(row.get("capture_status") == "captured_joined" for row in claude_rows) if claude_rows else False
    negative_clean = (
        int(aggregate.get("negative_joined_effect_events") or 0) == 0
        and int(aggregate.get("negative_effect_events_observed") or 0) > 0
    )
    direct_rows_observed = any(
        (row.get("target_network_oracle") or {}).get("target_network_rows_observed") for row in direct_rows
    )
    agent_rows_observed = any(
        (row.get("target_network_oracle") or {}).get("target_network_rows_observed") for row in agent_rows
    )
    lineage_orphaned = int(aggregate.get("orphan_target_network_effect_events") or 0) > 0
    agent_probe_ok_missing_capture = any(
        (row.get("probe_result") or {}).get("status") == "ok"
        and row.get("capture_status") == "capture_missing_target_network"
        for row in agent_rows
    )
    partially_localized = (
        direct_rows_observed
        and negative_clean
        and (lineage_orphaned or agent_probe_ok_missing_capture)
        and not (codex_delayed_ok and claude_delayed_ok)
    )
    return {
        "r236_capture_boundary_localized": False,
        "r236_capture_boundary_partially_localized": partially_localized,
        "direct_target_rows_observed_gate": direct_rows_observed,
        "agent_target_rows_observed_gate": agent_rows_observed,
        "direct_delayed_multiprocess_gate": direct_delayed_ok,
        "codex_delayed_multiprocess_gate": codex_delayed_ok,
        "claude_delayed_http_gate": claude_delayed_ok,
        "lineage_orphan_gate": lineage_orphaned,
        "agent_probe_ok_missing_capture_gate": agent_probe_ok_missing_capture,
        "negative_control_gate": negative_clean,
        "r236_broad_raw_claude_network_supported": codex_delayed_ok and claude_delayed_ok,
    }


def boundary_text(gate: dict[str, Any], aggregate: dict[str, Any]) -> str:
    if gate["r236_broad_raw_claude_network_supported"]:
        return (
            "R236 shows delayed Codex multiprocess and delayed Claude HTTP probes can observe and join "
            "target network rows under the controlled diagnostic workload. This supports a narrower "
            "follow-up to R235, not arbitrary network coverage."
        )
    if gate["r236_capture_boundary_partially_localized"]:
        return (
            "R236 partially localizes the R235 boundary: direct Python controls can produce target "
            "network rows and negative controls stay clean; the Codex delayed multiprocess probe "
            "can also join target rows. However, direct rows can still orphan and the "
            "Claude-launched delayed HTTP probe exports zero target rows despite probe_result_ok. "
            "Therefore probe_result_ok is not sufficient execution/capture evidence; the next gate "
            "must add a non-synthesizable runtime witness and inspect the collector lineage invariant."
        )
    return (
        "R236 remains partial: the diagnostic matrix did not isolate a supported capture path for "
        "multiprocess or agent-launched target network rows."
    )


def write_markdown(path: Path, result: dict[str, Any]) -> None:
    agg = result["aggregate"]
    gate = result["claim_gate"]
    lines = [
        "# R236 Multiprocess/Claude Network Capture Boundary",
        "",
        f"Last updated: {date.today().isoformat()}",
        "Stage at update: execute/analyze",
        "Source/command: `python3 docs/visexp/r236_multiprocess_claude_network_capture.py`",
        f"Completeness: {result['status']}",
        "",
        "R236 diagnoses R235's partial network-capture boundary. It is not user evidence.",
        "",
        "## Aggregate",
        "",
        f"- Tasks: {agg['tasks']}; ok tasks: {agg['ok_tasks']}.",
        f"- Capture statuses: {agg['capture_statuses']}.",
        f"- Launchers: {agg['launchers']}.",
        f"- Target-row observed tasks: {agg['target_rows_observed_tasks']}/{agg['tasks']}.",
        f"- Direct/agent target-row observed tasks: {agg['direct_target_rows_observed_tasks']}/"
        f"{agg['agent_target_rows_observed_tasks']}.",
        f"- Lineage orphaned tasks: {agg['lineage_orphaned_tasks']}; agent missing-target tasks: "
        f"{agg['agent_missing_target_rows_tasks']}.",
        f"- Required-action task gate: {agg['required_action_tasks_ok']}/{agg['tasks']}.",
        f"- Target network effects: {agg['joined_target_network_effect_events']}/{agg['target_network_effect_events']} joined.",
        f"- Negative controls: observed={agg['negative_effect_events_observed']}, joined={agg['negative_joined_effect_events']}.",
        f"- Metric boundary: {result['metric_boundary']}",
        f"- Gates: direct_delayed={gate['direct_delayed_multiprocess_gate']}, "
        f"direct_rows_observed={gate['direct_target_rows_observed_gate']}, "
        f"agent_rows_observed={gate['agent_target_rows_observed_gate']}, "
        f"codex_delayed={gate['codex_delayed_multiprocess_gate']}, "
        f"claude_delayed={gate['claude_delayed_http_gate']}, "
        f"partial_localized={gate['r236_capture_boundary_partially_localized']}, "
        f"broad_supported={gate['r236_broad_raw_claude_network_supported']}.",
        "",
        "## Tasks",
        "",
        "| Task | Launcher | Status | Capture status | Probe | Target network | Required actions | Snapshot network | Neg joined |",
        "|------|----------|--------|----------------|-------|---------------:|------------------|-----------------:|-----------:|",
    ]
    for row in result["tasks_detail"]:
        probe = row.get("probe_result") or {}
        net = row.get("network_lineage") or {}
        oracle = row.get("target_network_oracle") or {}
        snap = row.get("snapshot_diagnostics") or {}
        missing = oracle.get("missing_required_actions") or []
        lines.append(
            f"| `{row['task_id']}` | {row.get('launcher')} | {row.get('status')} | "
            f"{row.get('capture_status')} | {probe.get('probe')}:{probe.get('status')} | "
            f"{net.get('joined_target_network_effect_events', 0)}/{net.get('target_network_effect_events', 0)} | "
            f"{'ok' if not missing else ','.join(missing)} | "
            f"{snap.get('network_events', 0)} | "
            f"{(row.get('precision_recall') or {}).get('negative_joined_effect_events', 0)} |"
        )
    lines.extend(["", "## Boundary", "", result["boundary"]])
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

    selected = TASKS[: args.task_limit]
    if args.print_manifest:
        payload = {
            "schema_version": 1,
            "run_id": "R236",
            "tasks": [
                {
                    "task_id": task.task_id,
                    "launcher": task.launcher,
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
    status = "ok" if gate["r236_broad_raw_claude_network_supported"] else "partial"
    result = {
        "schema_version": 1,
        "run_id": "R236",
        "status": status,
        "scope": "multiprocess_and_claude_launched_process_network_capture_boundary",
        "generated_at": date.today().isoformat(),
        "work_dir": str(work_dir),
        "agentsight_bin": r114.rel(agentsight_bin),
        "codex_bin": "$CODEX_BIN",
        "claude_bin": "$CLAUDE_BIN" if claude_bin else "unavailable",
        "task_limit": len(rows),
        "negative_mode": args.negative_mode,
        "aggregate": aggregate,
        "claim_gate": gate,
        "tasks_detail": [compact_task_row(row) for row in rows],
        "boundary": boundary_text(gate, aggregate),
        "metric_boundary": (
            "precision_pct and recall_pct are scoped lineage-oracle metrics over observed "
            "in-scope and negative effects; target-network capture support is governed by "
            "target-row observation, required-action, join, and broad-support gates."
        ),
        "artifact_boundary": (
            "Raw SQLite DBs, exported snapshots, workspaces, and per-event lineage CSVs stay in the "
            "local work dir; committed artifacts contain aggregate/task summaries without per-event examples."
        ),
    }
    result = scrub_r236_artifact_value(r114.scrub_artifact_value(result), work_dir)
    json_path = out_dir / "multiprocess-claude-network-capture-r236.json"
    md_path = out_dir / "multiprocess-claude-network-capture-r236.md"
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


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--agentsight-bin", default=str(r114.REPO_ROOT / "collector/target/debug/agentsight"))
    parser.add_argument("--codex-bin", default="codex")
    parser.add_argument("--claude-bin", default="claude")
    parser.add_argument("--work-dir", default=str(DEFAULT_WORK))
    parser.add_argument("--out-dir", default=str(DEFAULT_OUT_DIR))
    parser.add_argument("--timeout", type=int, default=240)
    parser.add_argument("--task-limit", type=int, default=len(TASKS))
    parser.add_argument("--negative-mode", choices=["wrapper", "none"], default="wrapper")
    parser.add_argument("--print-manifest", action="store_true")
    return parser.parse_args()


def main() -> None:
    run(parse_args())


if __name__ == "__main__":
    main()
