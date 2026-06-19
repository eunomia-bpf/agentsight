#!/usr/bin/env python3
"""Run R237 runtime-witness network capture diagnostics.

R237 follows R236's partial boundary result. It asks a stricter question:
did the agent-launched probe actually execute with a runtime-only witness, and
can the collector observe and join the target network rows for that same
runtime port?

This is still a diagnostic gate, not user evidence. Raw DBs, exported snapshots,
and per-event lineage CSVs stay in the local work directory.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import secrets
import shutil
import subprocess
from collections import Counter
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

import r114_live_record_suite as r114
import r191_target_network_lineage as r191
import r234_broader_agent_network_lineage as r234
import r235_raw_claude_network_lineage as r235


DEFAULT_WORK = Path("/tmp/agentsight-r237-execution-witness-network")
WORK_MARKER = ".agentsight-r237-execution-witness-network"
DEFAULT_OUT_DIR = r114.DEFAULT_OUT / "agent-execution-witness-network-capture-r237"


HTTP_WITNESS_PROBE = r"""from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
import hashlib, json, os, threading, time, urllib.request

os.chdir(Path(__file__).resolve().parent)
time.sleep(2.5)
token = os.environ["R237_WITNESS_TOKEN"]
nonce = "r237-http-witness"
Path("payload.txt").write_text(nonce, encoding="utf-8")
server = ThreadingHTTPServer(("127.0.0.1", 0), SimpleHTTPRequestHandler)
port = int(server.server_address[1])
thread = threading.Thread(target=server.serve_forever, daemon=True)
thread.start()
started = time.time()
body = urllib.request.urlopen(f"http://127.0.0.1:{port}/payload.txt", timeout=5).read().decode("utf-8")
time.sleep(1.0)
server.shutdown()
server.server_close()
thread.join(timeout=5)
body_sha = hashlib.sha256(body.encode("utf-8")).hexdigest()
witness = {
    "status": "ok",
    "witness": "r237-runtime",
    "probe": "http_witness",
    "pid": os.getpid(),
    "port": port,
    "body_sha256": body_sha,
    "token_sha256": hashlib.sha256(token.encode("utf-8")).hexdigest(),
    "proof": hashlib.sha256(f"{token}:{port}:{body_sha}".encode("utf-8")).hexdigest(),
    "elapsed_ms": int((time.time() - started) * 1000),
}
result = {
    "status": "ok",
    "probe": "http_witness",
    "port": port,
    "bytes": len(body),
    "body": body,
    "witness_status": witness["status"],
}
encoded = json.dumps(result, sort_keys=True) + "\n"
Path("r237_result.json").write_text(encoded, encoding="utf-8")
Path("r237_witness.json").write_text(json.dumps(witness, sort_keys=True) + "\n", encoding="utf-8")
print(json.dumps(result, sort_keys=True))
"""


MULTIPROCESS_WITNESS_PROBE = r"""import hashlib, json, os, socket, subprocess, sys, tempfile, textwrap, time
from pathlib import Path

token = os.environ["R237_WITNESS_TOKEN"]
tmp = Path(tempfile.mkdtemp(prefix="r237-multiproc-"))
child = tmp / "child_server.py"
port_file = tmp / "port.json"
child_witness = tmp / "child_witness.json"
child.write_text(textwrap.dedent('''
    import json, os, socket, sys, time
    from pathlib import Path
    port_file = Path(sys.argv[1])
    child_witness = Path(sys.argv[2])
    time.sleep(2.5)
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(("127.0.0.1", 0))
    server.listen(1)
    port = int(server.getsockname()[1])
    port_file.write_text(json.dumps({"port": port, "child_pid": os.getpid()}), encoding="utf-8")
    conn, _ = server.accept()
    with conn:
        data = conn.recv(1024)
        conn.sendall(data[::-1])
    time.sleep(1.0)
    server.close()
    child_witness.write_text(json.dumps({"child_pid": os.getpid(), "port": port, "served": True}), encoding="utf-8")
''').strip() + "\n", encoding="utf-8")
proc = subprocess.Popen([sys.executable, str(child), str(port_file), str(child_witness)])
for _ in range(160):
    if port_file.exists():
        break
    time.sleep(0.05)
port_payload = json.loads(port_file.read_text(encoding="utf-8"))
port = int(port_payload["port"])
time.sleep(1.0)
started = time.time()
client = socket.create_connection(("127.0.0.1", port), timeout=5)
with client:
    client.sendall(b"r237-multiproc")
    body = client.recv(1024)
returncode = proc.wait(timeout=8)
child_payload = json.loads(child_witness.read_text(encoding="utf-8")) if child_witness.exists() else {}
body_text = body.decode("utf-8")
body_sha = hashlib.sha256(body_text.encode("utf-8")).hexdigest()
witness = {
    "status": "ok" if returncode == 0 and child_payload.get("served") else "child_failed",
    "witness": "r237-runtime",
    "probe": "multiprocess_tcp_witness",
    "pid": os.getpid(),
    "child_pid": int(port_payload.get("child_pid") or 0),
    "child_witness_pid": int(child_payload.get("child_pid") or 0),
    "port": port,
    "body_sha256": body_sha,
    "token_sha256": hashlib.sha256(token.encode("utf-8")).hexdigest(),
    "proof": hashlib.sha256(f"{token}:{port}:{body_sha}".encode("utf-8")).hexdigest(),
    "elapsed_ms": int((time.time() - started) * 1000),
}
result = {
    "status": "ok" if witness["status"] == "ok" else "child_failed",
    "probe": "multiprocess_tcp_witness",
    "port": port,
    "bytes": len(body),
    "body": body_text,
    "child_returncode": returncode,
    "witness_status": witness["status"],
}
encoded = json.dumps(result, sort_keys=True) + "\n"
Path("r237_result.json").write_text(encoded, encoding="utf-8")
Path("r237_witness.json").write_text(json.dumps(witness, sort_keys=True) + "\n", encoding="utf-8")
print(json.dumps(result, sort_keys=True))
"""


@dataclass(frozen=True)
class WitnessTask:
    task_id: str
    launcher: str
    agent: str
    script_name: str
    script_body: str
    expected_probe: str
    expected_body: str
    required_actions: tuple[str, ...] = ("NET_BIND", "NET_LISTEN", "NET_CONNECT")


TASKS = [
    WitnessTask(
        task_id="r237-direct-http-witness",
        launcher="direct-python",
        agent="python3",
        script_name="r237_http_witness_probe.py",
        script_body=HTTP_WITNESS_PROBE,
        expected_probe="http_witness",
        expected_body="r237-http-witness",
    ),
    WitnessTask(
        task_id="r237-direct-multiprocess-witness",
        launcher="direct-python",
        agent="python3",
        script_name="r237_multiprocess_witness_probe.py",
        script_body=MULTIPROCESS_WITNESS_PROBE,
        expected_probe="multiprocess_tcp_witness",
        expected_body="corpitlum-732r",
    ),
    WitnessTask(
        task_id="r237-codex-http-witness",
        launcher="codex",
        agent="codex",
        script_name="r237_http_witness_probe.py",
        script_body=HTTP_WITNESS_PROBE,
        expected_probe="http_witness",
        expected_body="r237-http-witness",
    ),
    WitnessTask(
        task_id="r237-claude-http-witness",
        launcher="claude",
        agent="claude",
        script_name="r237_http_witness_probe.py",
        script_body=HTTP_WITNESS_PROBE,
        expected_probe="http_witness",
        expected_body="r237-http-witness",
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
        "owned by docs/visexp/r237_agent_execution_witness_network_capture.py\n",
        encoding="utf-8",
    )


def scrub_r237_artifact_value(value: Any, work_dir: Path) -> Any:
    if isinstance(value, str):
        text = value.replace(str(work_dir.resolve()), "$R237_WORK")
        text = text.replace(str(work_dir), "$R237_WORK")
        return text
    if isinstance(value, list):
        return [scrub_r237_artifact_value(item, work_dir) for item in value]
    if isinstance(value, dict):
        return {key: scrub_r237_artifact_value(item, work_dir) for key, item in value.items()}
    return value


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def read_json_file(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"status": "missing_result"}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        return {"status": "invalid_json", "error": str(error)}


def command_for_task(
    task: WitnessTask,
    workspace: Path,
    answer_path: Path,
    codex_bin: str,
    claude_bin: str | None,
) -> tuple[list[str], Path]:
    if task.launcher == "direct-python":
        return (["python3", task.script_name], workspace)

    prompt = (
        f"Run exactly `python3 {task.script_name}` in the current directory. "
        "Do not inspect, edit, create, or synthesize result or witness files yourself. "
        "The script uses an inherited runtime witness token, and the verifier cross-checks "
        "the witness port against captured Python network syscalls. After the script exits, "
        "answer exactly the contents of r237_result.json and nothing else."
    )
    if task.launcher == "codex":
        return r234.agent_command("codex", prompt, workspace, answer_path, codex_bin, claude_bin)
    if task.launcher == "claude":
        return r235.agent_command("claude", prompt, workspace, answer_path, codex_bin, claude_bin)
    raise RuntimeError(f"unsupported launcher: {task.launcher}")


def run_recorded_command_env(
    task_id: str,
    agent: str,
    command_under_record: list[str],
    record_cwd: Path,
    agentsight_bin: Path,
    db_path: Path,
    timeout_s: int,
    negative_control: dict[str, str],
    negative_mode: str,
    token: str,
) -> subprocess.CompletedProcess[str]:
    command = command_under_record
    if negative_mode == "wrapper":
        command = r114.wrap_with_negative_control(command, negative_control)
    elif negative_mode != "none":
        raise SystemExit(f"unsupported R237 negative mode: {negative_mode}")
    record_cmd = [
        str(agentsight_bin),
        "record",
        "--no-server",
        "--db",
        str(db_path),
        "--agent-comm",
        agent,
        "--",
        *command,
    ]
    env = dict(os.environ)
    env["R237_WITNESS_TOKEN"] = token
    return subprocess.run(
        record_cmd,
        cwd=str(record_cwd),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout_s,
        check=False,
        env=env,
    )


def result_matches(task: WitnessTask, result: dict[str, Any]) -> bool:
    return (
        result.get("status") == "ok"
        and result.get("probe") == task.expected_probe
        and result.get("body") == task.expected_body
        and int(result.get("bytes") or 0) == len(task.expected_body)
        and int(result.get("port") or 0) > 0
    )


def witness_matches(token: str, task: WitnessTask, result: dict[str, Any], witness: dict[str, Any]) -> bool:
    if witness.get("status") != "ok" or witness.get("witness") != "r237-runtime":
        return False
    if witness.get("probe") != task.expected_probe:
        return False
    port = int(witness.get("port") or 0)
    if port <= 0 or port != int(result.get("port") or 0):
        return False
    body_sha = sha256_text(str(result.get("body") or ""))
    expected_proof = sha256_text(f"{token}:{port}:{body_sha}")
    return (
        witness.get("body_sha256") == body_sha
        and witness.get("token_sha256") == sha256_text(token)
        and witness.get("proof") == expected_proof
    )


def committed_witness_summary(witness: dict[str, Any]) -> dict[str, Any]:
    summary = {
        key: witness.get(key)
        for key in (
            "status",
            "witness",
            "probe",
            "port",
            "body_sha256",
            "token_sha256",
            "proof",
            "elapsed_ms",
        )
        if key in witness
    }
    child_pid = int(witness.get("child_pid") or 0)
    child_witness_pid = int(witness.get("child_witness_pid") or 0)
    summary["parent_pid_observed"] = int(witness.get("pid") or 0) > 0
    if "child_pid" in witness or "child_witness_pid" in witness:
        summary["child_pid_observed"] = child_pid > 0
        summary["child_witness_pid_observed"] = child_witness_pid > 0
        summary["child_pid_consistent"] = (
            child_pid > 0 and child_witness_pid > 0 and child_pid == child_witness_pid
        )
    return summary


def target_network_rows(lineage_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    return [row for row in lineage_rows if r191.target_network_row(row)]


def snapshot_network_rows(snapshot_path: Path) -> list[dict[str, Any]]:
    if not snapshot_path.exists():
        return []
    snapshot = r114.read_json(snapshot_path)
    return [
        row
        for row in snapshot.get("audit_events") or []
        if row.get("audit_type") == "network"
    ]


def target_rows_matching_port(snapshot_path: Path, port: int) -> list[dict[str, Any]]:
    if port <= 0:
        return []
    marker = f":{port}"
    matched = []
    for row in snapshot_network_rows(snapshot_path):
        target = str(row.get("target") or "")
        details = row.get("details") or {}
        detail = str(details.get("detail") or "") if isinstance(details, dict) else ""
        if marker in target or marker in detail:
            matched.append(row)
    return matched


def snapshot_diagnostics(snapshot_path: Path, script_name: str, witness_port: int) -> dict[str, Any]:
    if not snapshot_path.exists():
        return {"snapshot_exists": False}
    snapshot = r114.read_json(snapshot_path)
    process_nodes = snapshot.get("process_nodes") or []
    audit_events = snapshot.get("audit_events") or []
    network_events = [row for row in audit_events if row.get("audit_type") == "network"]
    script_processes = [
        row
        for row in process_nodes
        if script_name in str(row.get("command") or row.get("full_command") or "")
    ]
    port_rows = target_rows_matching_port(snapshot_path, witness_port)
    return {
        "snapshot_exists": True,
        "process_nodes": len(process_nodes),
        "audit_events": len(audit_events),
        "network_events": len(network_events),
        "network_actions": dict(Counter(row.get("action") or "unknown" for row in network_events)),
        "network_process_comms": dict(
            Counter(row.get("comm") or row.get("process_comm") or "unknown" for row in network_events)
        ),
        "script_process_nodes": len(script_processes),
        "python_process_nodes": sum(
            1 for row in process_nodes if str(row.get("comm") or "").startswith("python")
        ),
        "witness_port_network_rows": len(port_rows),
        "witness_port_actions": dict(Counter(row.get("action") or "unknown" for row in port_rows)),
    }


def lineage_invariant_summary(lineage_rows: list[dict[str, str]], witness_port: int) -> dict[str, Any]:
    target_rows = target_network_rows(lineage_rows)
    port_marker = f":{witness_port}" if witness_port > 0 else ""
    port_rows = [
        row for row in target_rows if port_marker and port_marker in str(row.get("target_group") or "")
    ]
    orphan_rows = [row for row in target_rows if not r114.row_joined(row)]
    return {
        "target_network_rows": len(target_rows),
        "joined_target_network_rows": sum(1 for row in target_rows if r114.row_joined(row)),
        "orphan_target_network_rows": len(orphan_rows),
        "target_join_methods": dict(Counter(row.get("join_method") or "unknown" for row in target_rows)),
        "target_orphan_reasons": dict(Counter(row.get("orphan_reason") or "unknown" for row in orphan_rows)),
        "witness_port_target_rows": len(port_rows),
        "witness_port_joined_rows": sum(1 for row in port_rows if r114.row_joined(row)),
        "witness_port_orphan_rows": sum(1 for row in port_rows if not r114.row_joined(row)),
    }


def classify_capture(row: dict[str, Any]) -> str:
    if row.get("record_status") != "ok":
        return "record_failed"
    if not row.get("probe_result_ok"):
        return "probe_failed"
    if not row.get("runtime_witness_ok"):
        return "runtime_witness_failed"
    oracle = row.get("target_network_oracle") or {}
    invariant = row.get("collector_invariant") or {}
    if int(invariant.get("witness_port_target_rows") or 0) <= 0:
        return "witness_unlinked_to_capture"
    if oracle.get("required_actions_ok") and oracle.get("all_target_network_rows_joined"):
        return "captured_joined"
    if int(invariant.get("witness_port_orphan_rows") or 0) > 0:
        return "collector_lineage_orphaned"
    if not oracle.get("required_actions_ok"):
        return "captured_missing_required_actions"
    return "captured_partial"


def run_task(
    task: WitnessTask,
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

    token = secrets.token_urlsafe(32)
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
        "token_sha256": sha256_text(token),
        "negative_control": negative_control,
    }
    try:
        command, record_cwd = command_for_task(task, workspace, answer_path, codex_bin, claude_bin)
        task_negative_mode = "none" if task.launcher == "direct-python" else negative_mode
        record_proc = run_recorded_command_env(
            task.task_id,
            task.agent,
            command,
            record_cwd,
            agentsight_bin,
            db_path,
            timeout_s,
            negative_control,
            task_negative_mode,
            token,
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

    result = read_json_file(workspace / "r237_result.json")
    witness = read_json_file(workspace / "r237_witness.json")
    row["probe_result"] = result
    row["runtime_witness"] = committed_witness_summary(witness)
    row["probe_result_ok"] = result_matches(task, result)
    row["runtime_witness_ok"] = witness_matches(token, task, result, witness)
    witness_port = int(witness.get("port") or result.get("port") or 0)

    if snapshot_path.exists():
        lineage_rows = r114.read_lineage_csv(lineage_dir / "effect-lineage.csv")
        row["network_lineage"] = r191.summarize_network(lineage_rows)
        row["target_network_oracle"] = r234.network_oracle(row, task)
        row["collector_invariant"] = lineage_invariant_summary(lineage_rows, witness_port)
        row["snapshot_diagnostics"] = snapshot_diagnostics(snapshot_path, task.script_name, witness_port)
    else:
        row["network_lineage"] = {}
        row["target_network_oracle"] = {}
        row["collector_invariant"] = {}
        row["snapshot_diagnostics"] = {"snapshot_exists": False}

    row["capture_status"] = classify_capture(row)
    row["status"] = "ok" if row["capture_status"] == "captured_joined" else "partial"
    return row


def compact_task_row(row: dict[str, Any]) -> dict[str, Any]:
    compact = r234.compact_task_row(row)
    precision_recall = compact.get("precision_recall")
    if isinstance(precision_recall, dict):
        if "precision_pct" in precision_recall:
            precision_recall["scoped_lineage_oracle_precision_pct"] = precision_recall.pop(
                "precision_pct"
            )
        if "recall_pct" in precision_recall:
            precision_recall["scoped_lineage_oracle_recall_pct"] = precision_recall.pop(
                "recall_pct"
            )
    for key in (
        "launcher",
        "capture_status",
        "runtime_witness_ok",
        "runtime_witness",
        "collector_invariant",
        "snapshot_diagnostics",
        "token_sha256",
    ):
        if key in row:
            compact[key] = row[key]
    if row.get("error"):
        compact["error"] = r114.scrub(str(row["error"]), limit=400)
    return compact


def aggregate_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    network = r234.aggregate_network(rows)
    status_counts = Counter(row.get("capture_status") or "unknown" for row in rows)
    launcher_counts = Counter(row.get("launcher") or "unknown" for row in rows)
    witness_ok_rows = [row for row in rows if row.get("runtime_witness_ok")]
    port_observed_rows = [
        row
        for row in rows
        if int((row.get("collector_invariant") or {}).get("witness_port_target_rows") or 0) > 0
    ]
    port_joined_rows = [
        row
        for row in rows
        if int((row.get("collector_invariant") or {}).get("witness_port_joined_rows") or 0) > 0
    ]
    return {
        "tasks": len(rows),
        "ok_tasks": sum(1 for row in rows if row.get("status") == "ok"),
        "capture_statuses": dict(status_counts),
        "launchers": dict(launcher_counts),
        "runtime_witness_ok_tasks": len(witness_ok_rows),
        "witness_port_observed_tasks": len(port_observed_rows),
        "witness_port_joined_tasks": len(port_joined_rows),
        "witness_port_linked_tasks": len(port_observed_rows),
        "required_action_tasks_ok": sum(
            1 for row in rows if (row.get("target_network_oracle") or {}).get("required_actions_ok")
        ),
        "target_network_effect_events": network.get("target_network_effect_events", 0),
        "joined_target_network_effect_events": network.get("joined_target_network_effect_events", 0),
        "orphan_target_network_effect_events": network.get("orphan_target_network_effect_events", 0),
        "target_network_actions": network.get("target_network_actions", {}),
        "target_network_process_comms": network.get("target_network_process_comms", {}),
        "negative_effect_events_observed": network.get("negative_effect_events_observed", 0),
        "negative_joined_effect_events": network.get("negative_joined_effect_events", 0),
        "scoped_lineage_oracle_precision_pct": network.get("precision_pct", 0.0),
        "scoped_lineage_oracle_recall_pct": network.get("recall_pct", 0.0),
    }


def claim_gate(rows: list[dict[str, Any]], aggregate: dict[str, Any]) -> dict[str, Any]:
    claude_rows = [row for row in rows if row.get("launcher") == "claude"]
    direct_rows = [row for row in rows if row.get("launcher") == "direct-python"]
    codex_rows = [row for row in rows if row.get("launcher") == "codex"]
    negative_clean = (
        int(aggregate.get("negative_joined_effect_events") or 0) == 0
        and int(aggregate.get("negative_effect_events_observed") or 0) > 0
    )
    claude_capture_ok = bool(claude_rows) and all(
        row.get("capture_status") == "captured_joined" for row in claude_rows
    )
    codex_witness_observed_ok = bool(codex_rows) and all(
        row.get("runtime_witness_ok")
        and int((row.get("collector_invariant") or {}).get("witness_port_target_rows") or 0) > 0
        for row in codex_rows
    )
    witness_port_observed_ok = int(
        aggregate.get("witness_port_observed_tasks")
        or aggregate.get("witness_port_linked_tasks")
        or 0
    ) == len(rows)
    witness_port_joined_ok = int(aggregate.get("witness_port_joined_tasks") or 0) == len(rows)
    direct_orphan_resolved = bool(direct_rows) and all(
        row.get("capture_status") == "captured_joined" for row in direct_rows
    )
    return {
        "runtime_witness_gate": int(aggregate.get("runtime_witness_ok_tasks") or 0) == len(rows),
        "witness_port_observed_gate": witness_port_observed_ok,
        "witness_port_joined_gate": witness_port_joined_ok,
        "witness_port_capture_gate": witness_port_observed_ok,
        "negative_control_gate": negative_clean,
        "codex_witness_observed_gate": codex_witness_observed_ok,
        "positive_controls_gate": codex_witness_observed_ok,
        "claude_launched_capture_gate": claude_capture_ok,
        "direct_orphan_resolved_gate": direct_orphan_resolved,
        "r237_claude_target_network_supported": claude_capture_ok and negative_clean,
        "r237_boundary_resolved": claude_capture_ok and direct_orphan_resolved and negative_clean,
    }


def boundary_text(gate: dict[str, Any], run_id: str) -> str:
    if gate["r237_boundary_resolved"]:
        return (
            f"{run_id} resolves the prior boundary for this controlled workload: runtime witnesses "
            "pass, witness ports are captured, target network rows join, and negative "
            "controls remain clean. This still does not prove arbitrary network workloads."
        )
    if gate["r237_claude_target_network_supported"]:
        return (
            f"{run_id} supports the controlled Claude-launched HTTP witness path, but one or more "
            "direct or non-Claude diagnostic rows still need lineage cleanup."
        )
    if gate["runtime_witness_gate"] and gate["direct_orphan_resolved_gate"] and gate["negative_control_gate"]:
        return (
            f"{run_id} partially localizes the remaining boundary: runtime witnesses pass, "
            "direct controls pass, witness ports are observed, and negative controls remain "
            "clean, but agent-launched Codex/Claude rows still have target-network "
            "orphan or missing-action cases. This supports a named "
            "collector/launcher boundary, not broad Claude-launched network coverage."
        )
    return (
        f"{run_id} remains partial: runtime witnesses, witness-port capture, or target-row lineage "
        "did not all pass. The result narrows C4 but does not upgrade broad Claude-launched "
        "or raw network coverage."
    )


def write_markdown(path: Path, result: dict[str, Any]) -> None:
    agg = result["aggregate"]
    gate = result["claim_gate"]
    lines = [
        f"# {result['run_id']} Agent Execution Witness Network Capture",
        "",
        f"Last updated: {date.today().isoformat()}",
        "Stage at update: execute/analyze",
        "Source/command: `python3 docs/visexp/r237_agent_execution_witness_network_capture.py`",
        f"Completeness: {result['status']}",
        "",
        f"{result['run_id']} diagnoses whether agent-launched network probes execute with a runtime-only witness",
        "and whether the same witness port appears in target network capture rows.",
        "",
        "## Aggregate",
        "",
        f"- Tasks: {agg['tasks']}; ok tasks: {agg['ok_tasks']}.",
        f"- Capture statuses: {agg['capture_statuses']}.",
        f"- Launchers: {agg['launchers']}.",
        f"- Runtime witness ok tasks: {agg['runtime_witness_ok_tasks']}/{agg['tasks']}.",
        f"- Witness-port observed tasks: {agg.get('witness_port_observed_tasks', agg['witness_port_linked_tasks'])}/{agg['tasks']}.",
        f"- Witness-port joined tasks: {agg.get('witness_port_joined_tasks', 'n/a')}/{agg['tasks']}.",
        f"- Required-action task gate: {agg['required_action_tasks_ok']}/{agg['tasks']}.",
        f"- Target network effects: {agg['joined_target_network_effect_events']}/{agg['target_network_effect_events']} joined.",
        f"- Negative controls: observed={agg['negative_effect_events_observed']}, joined={agg['negative_joined_effect_events']}.",
        f"- Gates: runtime_witness={gate['runtime_witness_gate']}, "
        f"witness_port_observed={gate.get('witness_port_observed_gate', gate['witness_port_capture_gate'])}, "
        f"witness_port_joined={gate.get('witness_port_joined_gate', 'n/a')}, "
        f"codex_witness_observed={gate.get('codex_witness_observed_gate', gate['positive_controls_gate'])}, "
        f"claude_capture={gate['claude_launched_capture_gate']}, "
        f"direct_orphan_resolved={gate['direct_orphan_resolved_gate']}, "
        f"boundary_resolved={gate['r237_boundary_resolved']}.",
        f"- Metric boundary: {result['metric_boundary']}",
        "",
        "## Tasks",
        "",
        "| Task | Launcher | Status | Capture status | Witness | Port rows | Target network | Orphan reasons | Neg joined |",
        "|------|----------|--------|----------------|---------|----------:|---------------:|----------------|-----------:|",
    ]
    for row in result["tasks_detail"]:
        invariant = row.get("collector_invariant") or {}
        net = row.get("network_lineage") or {}
        pr = row.get("precision_recall") or {}
        reasons = invariant.get("target_orphan_reasons") or {}
        reason_text = ",".join(f"{key}:{value}" for key, value in reasons.items()) or "none"
        lines.append(
            f"| `{row['task_id']}` | {row.get('launcher')} | {row.get('status')} | "
            f"{row.get('capture_status')} | {row.get('runtime_witness_ok')} | "
            f"{invariant.get('witness_port_target_rows', 0)} | "
            f"{net.get('joined_target_network_effect_events', 0)}/{net.get('target_network_effect_events', 0)} | "
            f"{reason_text} | {pr.get('negative_joined_effect_events', 0)} |"
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
            "run_id": args.run_id,
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
            "witness_model": "per-task environment token; committed artifacts contain token hash/proof only",
        }
        print(json.dumps(payload, indent=2))
        return payload

    rows = [
        run_task(task, agentsight_bin, codex_bin, claude_bin, work_dir, args.timeout, args.negative_mode)
        for task in selected
    ]
    aggregate = aggregate_rows(rows)
    gate = claim_gate(rows, aggregate)
    status = "ok" if gate["r237_boundary_resolved"] else "partial"
    result = {
        "schema_version": 1,
        "run_id": args.run_id,
        "status": status,
        "scope": "agent_execution_witness_and_target_network_capture_boundary",
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
        "boundary": boundary_text(gate, args.run_id),
        "metric_boundary": (
            "scoped_lineage_oracle_precision_pct and scoped_lineage_oracle_recall_pct "
            f"are computed over observed in-scope and negative effects. {args.run_id} support is "
            "governed by runtime witness, witness-port capture, target-network join, "
            "and negative-control gates."
        ),
        "witness_boundary": (
            "The raw per-task witness token is generated by the harness and passed through the "
            "recorded process environment. It is not written to committed artifacts. This is a "
            "controlled execution witness, not an adversarial proof against an agent that "
            "intentionally inspects its environment."
        ),
        "artifact_boundary": (
            "Raw SQLite DBs, exported snapshots, workspaces, and per-event lineage CSVs stay in the "
            "local work dir; committed artifacts contain aggregate/task summaries without per-event examples."
        ),
    }
    result = scrub_r237_artifact_value(r114.scrub_artifact_value(result), work_dir)
    run_slug = args.run_id.lower()
    json_path = out_dir / f"agent-execution-witness-network-capture-{run_slug}.json"
    md_path = out_dir / f"agent-execution-witness-network-capture-{run_slug}.md"
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
    parser.add_argument("--timeout", type=int, default=300)
    parser.add_argument("--negative-mode", choices=("wrapper", "none"), default="wrapper")
    parser.add_argument("--task-limit", type=int, default=len(TASKS))
    parser.add_argument("--print-manifest", action="store_true")
    parser.add_argument("--run-id", default="R237")
    return parser.parse_args()


if __name__ == "__main__":
    run(parse_args())
