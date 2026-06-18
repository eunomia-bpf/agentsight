#!/usr/bin/env python3
"""Run the R191 target-specific network lineage hardening suite.

R191 is a fixed Codex workload: the task pre-creates a deterministic network
probe and asks `codex exec` to run it.  The oracle checks the resulting
AgentSight snapshot for target `python3` bind/listen/connect rows, their
prompt/tool/process lineage, and concurrent negative-control rejection.
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

from r114_live_record_suite import (
    REPO_ROOT,
    SCRIPT_DIR,
    DEFAULT_OUT,
    Task,
    failure_tail,
    negative_control_paths,
    precision_recall_summary,
    read_json,
    read_lineage_csv,
    rel,
    resolve_executable,
    row_joined,
    run_cmd,
    scrub,
    scrub_artifact_value,
    target_status,
    wrap_with_negative_control,
)


DEFAULT_WORK = Path("/tmp/agentsight-r191-target-network")
WORK_MARKER = ".agentsight-r191-target-network"
EXPECTED_TARGET_ACTIONS = {"NET_BIND": 1, "NET_LISTEN": 1, "NET_CONNECT": 2}


HTTP_PROBE = r"""from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
import json, os, threading, time, urllib.request

os.chdir(Path(__file__).resolve().parent)
nonce = "r191-http-probe"
Path("payload.txt").write_text(nonce, encoding="utf-8")
server = ThreadingHTTPServer(("127.0.0.1", 0), SimpleHTTPRequestHandler)
port = int(server.server_address[1])
thread = threading.Thread(target=server.serve_forever, daemon=True)
thread.start()
started = time.time()
body = urllib.request.urlopen(f"http://127.0.0.1:{port}/payload.txt", timeout=5).read().decode("utf-8")
server.shutdown()
server.server_close()
thread.join(timeout=5)
result = {
    "status": "ok",
    "probe": "http",
    "port": port,
    "bytes": len(body),
    "body": body,
    "elapsed_ms": int((time.time() - started) * 1000),
}
Path("r191_result.json").write_text(json.dumps(result, sort_keys=True) + "\n", encoding="utf-8")
print(json.dumps(result, sort_keys=True))
"""


@dataclass(frozen=True)
class NetworkTask:
    task_id: str
    script_name: str
    script_body: str
    expected_probe: str
    expected_body: str


TASKS = [
    NetworkTask(
        task_id="r191-codex-http",
        script_name="r191_http_probe.py",
        script_body=HTTP_PROBE,
        expected_probe="http",
        expected_body="r191-http-probe",
    )
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
        "owned by docs/visexp/r191_target_network_lineage.py\n",
        encoding="utf-8",
    )


def codex_command(task: NetworkTask, workspace: Path, answer_path: Path, codex_bin: str) -> list[str]:
    prompt = (
        f"Run exactly `python3 {task.script_name}` in the current directory. "
        f"Do not modify {task.script_name}. After it exits, answer exactly the "
        "contents of r191_result.json and nothing else."
    )
    return [
        codex_bin,
        "exec",
        "--sandbox",
        "danger-full-access",
        "--cd",
        str(workspace),
        "--skip-git-repo-check",
        "--output-last-message",
        str(answer_path),
        prompt,
    ]


def lineage_csv_path(row: dict[str, Any]) -> Path:
    db_path = Path(str(row.get("db") or ""))
    return db_path.parent / "lineage" / "effect-lineage.csv"


def target_network_row(row: dict[str, str]) -> bool:
    target = str(row.get("target_group") or "")
    return row.get("audit_type") == "network" and (
        str(row.get("process_comm") or "") == "python3" or target.startswith("127.")
    )


def summarize_network(rows: list[dict[str, str]]) -> dict[str, Any]:
    network = [row for row in rows if row.get("audit_type") == "network"]
    target = [row for row in network if target_network_row(row)]
    joined_target = [row for row in target if row_joined(row)]
    return {
        "network_effect_events": len(network),
        "joined_network_effect_events": sum(1 for row in network if row_joined(row)),
        "target_network_effect_events": len(target),
        "joined_target_network_effect_events": len(joined_target),
        "orphan_target_network_effect_events": len(target) - len(joined_target),
        "target_network_join_pct": round(100.0 * len(joined_target) / len(target), 3) if target else 0.0,
        "network_process_comms": dict(Counter(row.get("process_comm") or "unknown" for row in network)),
        "target_network_targets": dict(Counter(row.get("target_group") or "unknown" for row in target)),
        "target_network_actions": dict(Counter(row.get("action") or "unknown" for row in target)),
        "target_network_process_comms": dict(Counter(row.get("process_comm") or "unknown" for row in target)),
        "target_network_examples": target[:8],
    }


def read_probe_result(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"status": "missing_result"}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        return {"status": "invalid_json", "error": str(error)}


def result_matches(task: NetworkTask, result: dict[str, Any]) -> bool:
    return (
        result.get("status") == "ok"
        and result.get("probe") == task.expected_probe
        and result.get("body") == task.expected_body
        and int(result.get("bytes") or 0) == len(task.expected_body)
        and int(result.get("port") or 0) > 0
    )


def target_network_oracle(net: dict[str, Any]) -> dict[str, Any]:
    target_total = int(net.get("target_network_effect_events") or 0)
    expected_total = sum(EXPECTED_TARGET_ACTIONS.values())
    actions = {key: int(value) for key, value in (net.get("target_network_actions") or {}).items()}
    process_comms = {
        key: int(value) for key, value in (net.get("target_network_process_comms") or {}).items()
    }
    return {
        "expected_target_network_effect_events": expected_total,
        "expected_target_network_actions": EXPECTED_TARGET_ACTIONS,
        "target_network_effect_count_ok": target_total == expected_total,
        "target_network_actions_ok": actions == EXPECTED_TARGET_ACTIONS,
        "target_network_process_comm_ok": process_comms == {"python3": expected_total},
    }


def run_task(
    task: NetworkTask,
    agentsight_bin: Path,
    codex_bin: str,
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
    helper_task = Task(task.task_id, "network", "", workspace="json_write")
    negative_control = negative_control_paths(helper_task, work_dir)
    command_under_record = codex_command(task, workspace, answer_path, codex_bin)
    if negative_mode == "wrapper":
        command_under_record = wrap_with_negative_control(command_under_record, negative_control)
    elif negative_mode != "none":
        raise SystemExit(f"unsupported negative mode for R191: {negative_mode}")

    record_cmd = [
        str(agentsight_bin),
        "record",
        "--no-server",
        "--db",
        str(db_path),
        "--agent-comm",
        "codex",
        "--",
        *command_under_record,
    ]
    record_proc = run_cmd(record_cmd, REPO_ROOT, timeout_s)
    row: dict[str, Any] = {
        "task_id": task.task_id,
        "status": "record_failed" if record_proc.returncode else "record_ok",
        "record_status": "failed" if record_proc.returncode else "ok",
        "record_returncode": record_proc.returncode,
        "db": str(db_path),
        "snapshot": str(snapshot_path),
        "workspace": str(workspace),
        "answer": scrub(answer_path.read_text(encoding="utf-8")) if answer_path.exists() else "",
        "negative_control": negative_control,
    }
    row.update(failure_tail(record_proc))
    if record_proc.returncode != 0 or not db_path.exists():
        return row

    export_proc = run_cmd(
        [
            str(agentsight_bin),
            "report",
            "export",
            "--db",
            str(db_path),
            "--output",
            str(snapshot_path),
            "--audit-limit",
            "50000",
        ],
        REPO_ROOT,
        timeout_s,
    )
    row["export_returncode"] = export_proc.returncode
    if export_proc.returncode != 0 or not snapshot_path.exists():
        row["status"] = "export_failed"
        row["export_stdout_tail"] = scrub(export_proc.stdout)
        row["export_stderr_tail"] = scrub(export_proc.stderr)
        return row

    lineage_proc = run_cmd(
        [
            "python3",
            str(SCRIPT_DIR / "effect_lineage_smoke.py"),
            "--snapshot",
            str(snapshot_path),
            "--out",
            str(lineage_dir),
        ],
        REPO_ROOT,
        timeout_s,
    )
    row["lineage_returncode"] = lineage_proc.returncode
    lineage_summary_path = lineage_dir / "effect-lineage-smoke.json"
    if lineage_summary_path.exists():
        row["lineage"] = read_json(lineage_summary_path)

    snapshot = read_json(snapshot_path)
    row.update(target_status(snapshot))
    lineage_rows = read_lineage_csv(lineage_csv_path(row))
    row["network_lineage"] = summarize_network(lineage_rows)
    control_markers = [
        negative_control["marker"],
        negative_control["negative_dir"],
        negative_control["sibling_dir"],
    ]
    row["precision_recall"] = precision_recall_summary(snapshot, lineage_rows, control_markers)
    probe_result = read_probe_result(workspace / "r191_result.json")
    row["probe_result"] = probe_result
    row["probe_result_ok"] = result_matches(task, probe_result)
    row["target_network_oracle"] = target_network_oracle(row["network_lineage"])
    row["snapshot_counts"] = {
        "sessions": len(snapshot.get("sessions") or []),
        "tool_calls": len(snapshot.get("tool_calls") or []),
        "process_nodes": len(snapshot.get("process_nodes") or []),
        "audit_events": len(snapshot.get("audit_events") or []),
    }

    net = row["network_lineage"]
    pr = row["precision_recall"]
    passed = (
        row["record_status"] == "ok"
        and row.get("target_status") == "completed"
        and row["probe_result_ok"]
        and row["target_network_oracle"]["target_network_effect_count_ok"]
        and row["target_network_oracle"]["target_network_actions_ok"]
        and row["target_network_oracle"]["target_network_process_comm_ok"]
        and net.get("joined_target_network_effect_events") == net.get("target_network_effect_events")
        and int(net.get("orphan_target_network_effect_events") or 0) == 0
        and int(pr.get("negative_effect_events_observed") or 0) > 0
        and int(pr.get("negative_joined_effect_events") or 0) == 0
        and float(pr.get("precision_pct") or 0.0) >= 98.0
        and float(pr.get("recall_pct") or 0.0) >= 95.0
    )
    row["status"] = "ok" if passed else "partial"
    return row


def aggregate(rows: list[dict[str, Any]]) -> dict[str, Any]:
    totals = Counter()
    statuses = Counter(row.get("status", "unknown") for row in rows)
    record_statuses = Counter(row.get("record_status", "unknown") for row in rows)
    target_statuses = Counter(row.get("target_status", "unknown") for row in rows)
    targets = Counter()
    actions = Counter()
    process_comms = Counter()
    target_process_comms = Counter()
    for row in rows:
        net = row.get("network_lineage") or {}
        pr = row.get("precision_recall") or {}
        totals["network_effect_events"] += int(net.get("network_effect_events") or 0)
        totals["joined_network_effect_events"] += int(net.get("joined_network_effect_events") or 0)
        totals["target_network_effect_events"] += int(net.get("target_network_effect_events") or 0)
        totals["joined_target_network_effect_events"] += int(net.get("joined_target_network_effect_events") or 0)
        totals["orphan_target_network_effect_events"] += int(net.get("orphan_target_network_effect_events") or 0)
        totals["negative_effect_events_observed"] += int(pr.get("negative_effect_events_observed") or 0)
        totals["negative_joined_effect_events"] += int(pr.get("negative_joined_effect_events") or 0)
        totals["true_positives"] += int(pr.get("true_positives") or 0)
        totals["false_positives"] += int(pr.get("false_positives") or 0)
        totals["false_negatives"] += int(pr.get("false_negatives") or 0)
        targets.update(net.get("target_network_targets") or {})
        actions.update(net.get("target_network_actions") or {})
        process_comms.update(net.get("network_process_comms") or {})
        target_process_comms.update(net.get("target_network_process_comms") or {})
    target_total = totals["target_network_effect_events"]
    target_joined = totals["joined_target_network_effect_events"]
    tp = totals["true_positives"]
    fp = totals["false_positives"]
    fn = totals["false_negatives"]
    return {
        "tasks": len(rows),
        "task_statuses": dict(statuses),
        "record_statuses": dict(record_statuses),
        "target_statuses": dict(target_statuses),
        **dict(totals),
        "target_network_join_pct": round(100.0 * target_joined / target_total, 3) if target_total else 0.0,
        "precision_pct": round(100.0 * tp / (tp + fp), 3) if (tp + fp) else 0.0,
        "recall_pct": round(100.0 * tp / (tp + fn), 3) if (tp + fn) else 0.0,
        "target_network_targets": dict(targets),
        "target_network_actions": dict(actions),
        "network_process_comms": dict(process_comms),
        "target_network_process_comms": dict(target_process_comms),
    }


def write_markdown(path: Path, result: dict[str, Any]) -> None:
    agg = result["aggregate"]
    lines = [
        "# R191 Target Network Lineage",
        "",
        f"Last updated: {date.today().isoformat()}",
        "Stage at update: execute/analyze",
        "Source/command: `python3 docs/visexp/r191_target_network_lineage.py --out docs/visexp/out`",
        f"Completeness: {result['status']}",
        "",
        "R191 runs a fixed Codex task whose only useful answer is produced by a",
        "pre-created local Python network probe. It checks target-process network",
        "rows, not low-level Codex HTTP client rows.",
        "",
        "## Aggregate",
        "",
        f"- Tasks: {agg['tasks']} ({agg['task_statuses']})",
        f"- Record status: {agg['record_statuses']}; target status: {agg['target_statuses']}",
        f"- Target network effects: {agg['joined_target_network_effect_events']} / {agg['target_network_effect_events']} joined ({agg['target_network_join_pct']}%)",
        f"- Negative controls: observed={agg['negative_effect_events_observed']}, joined={agg['negative_joined_effect_events']}",
        f"- Scoped precision/recall: {agg['precision_pct']}% / {agg['recall_pct']}%",
        f"- Target network targets: {agg['target_network_targets']}",
        f"- Target network actions: {agg['target_network_actions']}",
        f"- Target process commands: {agg['target_network_process_comms']}",
        f"- Network process commands: {agg['network_process_comms']}",
    ]
    lineage_failures = [
        row for row in result["tasks"] if int(row.get("lineage_returncode") or 0) != 0
    ]
    if lineage_failures:
        lines.append(
            f"- Broad lineage smoke: {len(lineage_failures)} task(s) returned non-zero; "
            "R191 status is scoped to the target-network oracle, while wrapper/out-of-scope "
            "effects may remain orphaned."
        )
        lines.append("")
    lines.extend(
        [
            "",
            "## Per Task",
            "",
            "| Task | Status | Probe | Target network | Negative joined | Precision/Recall | Answer |",
            "|------|--------|-------|---------------:|----------------:|------------------:|--------|",
        ]
    )
    for row in result["tasks"]:
        net = row.get("network_lineage") or {}
        pr = row.get("precision_recall") or {}
        probe = row.get("probe_result") or {}
        answer = str(row.get("answer") or "").replace("|", "\\|").replace("\n", " ")[:120]
        lines.append(
            f"| `{row['task_id']}` | {row.get('status')} | {probe.get('probe')}:{probe.get('status')} | "
            f"{net.get('joined_target_network_effect_events', 0)}/{net.get('target_network_effect_events', 0)} | "
            f"{pr.get('negative_joined_effect_events', 0)} | "
            f"{pr.get('precision_pct', 0.0)}%/{pr.get('recall_pct', 0.0)}% | {answer} |"
        )
    lines.extend(["", "## Claim Boundary", "", result["boundary"]])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run(args: argparse.Namespace) -> dict[str, Any]:
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    selected = TASKS[: args.task_limit]
    if args.print_manifest:
        rows = [
            {"task_id": task.task_id, "script": task.script_name, "probe": task.expected_probe}
            for task in selected
        ]
        payload = {"schema_version": 1, "run_id": "R191", "tasks": rows}
        print(json.dumps(payload, indent=2))
        return payload

    work_dir = Path(args.work_dir)
    prepare_work_dir(work_dir)
    agentsight_bin = Path(resolve_executable(args.agentsight_bin, "agentsight"))
    codex_bin = resolve_executable(args.codex_bin, "codex")
    rows = [
        run_task(task, agentsight_bin, codex_bin, work_dir, args.timeout, args.negative_mode)
        for task in selected
    ]
    aggregate_result = aggregate(rows)
    passed = (
        aggregate_result["task_statuses"].get("ok", 0) == len(rows)
        and aggregate_result["target_network_effect_events"]
        == sum(EXPECTED_TARGET_ACTIONS.values()) * len(rows)
        and aggregate_result["target_network_actions"]
        == {key: value * len(rows) for key, value in EXPECTED_TARGET_ACTIONS.items()}
        and aggregate_result["target_network_process_comms"]
        == {"python3": sum(EXPECTED_TARGET_ACTIONS.values()) * len(rows)}
        and aggregate_result["joined_target_network_effect_events"] == aggregate_result["target_network_effect_events"]
        and aggregate_result["orphan_target_network_effect_events"] == 0
        and aggregate_result["negative_effect_events_observed"] > 0
        and aggregate_result["negative_joined_effect_events"] == 0
        and aggregate_result["precision_pct"] >= 98.0
        and aggregate_result["recall_pct"] >= 95.0
    )
    status = "ok" if passed else "partial"
    boundary = (
        "R191 supports C4 for a fixed command-mode Codex task that executes a local "
        "Python network probe: target-process bind/listen/connect rows are "
        "observed and joined, while wrapper negative-control effects remain "
        "unattributed. It does not prove arbitrary prompt compliance, full-history "
        "exact lineage, HTTP URL reconstruction, or C5/C6 user/tag evidence."
        if passed
        else "R191 is partial: target-process network rows or negative-control gates did not all pass."
    )
    result = {
        "schema_version": 1,
        "run_id": "R191",
        "status": status,
        "scope": "fixed_codex_command_mode_target_network_lineage_with_wrapper_negative_controls",
        "generated_at": date.today().isoformat(),
        "work_dir": str(work_dir),
        "agentsight_bin": rel(agentsight_bin),
        "codex_bin": str(codex_bin),
        "task_limit": args.task_limit,
        "negative_mode": args.negative_mode,
        "manifest": [
            {"task_id": task.task_id, "script": task.script_name, "probe": task.expected_probe}
            for task in selected
        ],
        "aggregate": aggregate_result,
        "tasks": rows,
        "boundary": boundary,
        "artifact_boundary": (
            "Raw SQLite DBs, exported snapshots, and per-event lineage CSVs stay in the local work dir; "
            "the committed artifact contains scrubbed summaries and examples."
        ),
    }
    result = scrub_artifact_value(result)
    json_path = out_dir / "live-network-r191.json"
    md_path = out_dir / "live-network-r191.md"
    json_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    write_markdown(md_path, result)
    print(json.dumps({"status": result["status"], "aggregate": result["aggregate"]}, indent=2))
    return result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default=str(DEFAULT_OUT))
    parser.add_argument("--work-dir", default=str(DEFAULT_WORK))
    parser.add_argument("--agentsight-bin", default=str(REPO_ROOT / "collector/target/debug/agentsight"))
    parser.add_argument("--codex-bin", default="codex")
    parser.add_argument("--task-limit", type=int, default=len(TASKS))
    parser.add_argument("--timeout", type=int, default=300)
    parser.add_argument("--negative-mode", choices=("wrapper", "none"), default="wrapper")
    parser.add_argument("--print-manifest", action="store_true")
    return parser


if __name__ == "__main__":
    run(build_parser().parse_args())
