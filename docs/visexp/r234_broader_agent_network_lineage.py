#!/usr/bin/env python3
"""Run R234 controlled agent/HTTP-network exact-lineage replication.

R234 extends the R114/R191/R232 scoped lineage oracle along two axes:

* another command-mode agent family (Claude, when available);
* two Codex HTTP-family target-network probes beyond the single R191 HTTP shape
  (single GET and repeated GET).

It is still a controlled local replication experiment. Passing R234 does not
prove arbitrary agents, arbitrary network workloads, C5 user utility, or C6 tag
adequacy. Raw DBs, snapshots, and lineage CSVs remain in the local work dir.
"""

from __future__ import annotations

import argparse
import json
import shlex
import shutil
from collections import Counter
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

import r114_live_record_suite as r114
import r191_target_network_lineage as r191


DEFAULT_WORK = Path("/tmp/agentsight-r234-broader-agent-network")
WORK_MARKER = ".agentsight-r234-broader-agent-network"
DEFAULT_OUT_DIR = r114.DEFAULT_OUT / "broader-agent-network-lineage-r234"


def scrub_r234_artifact_value(value: Any, work_dir: Path) -> Any:
    """Scrub machine-local R234 work paths after the shared R114 scrub."""
    if isinstance(value, str):
        work_abs = str(work_dir.resolve())
        text = value.replace(work_abs, "$R234_WORK")
        text = text.replace(str(work_dir), "$R234_WORK")
        return text
    if isinstance(value, list):
        return [scrub_r234_artifact_value(item, work_dir) for item in value]
    if isinstance(value, dict):
        return {key: scrub_r234_artifact_value(item, work_dir) for key, item in value.items()}
    return value


HTTP_PROBE = r"""from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
import json, os, threading, time, urllib.request

os.chdir(Path(__file__).resolve().parent)
nonce = "r234-http-probe"
Path("payload.txt").write_text(nonce, encoding="utf-8")
server = ThreadingHTTPServer(("127.0.0.1", 0), SimpleHTTPRequestHandler)
port = int(server.server_address[1])
thread = threading.Thread(target=server.serve_forever, daemon=True)
thread.start()
time.sleep(1.0)
started = time.time()
body = urllib.request.urlopen(f"http://127.0.0.1:{port}/payload.txt", timeout=5).read().decode("utf-8")
time.sleep(1.0)
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
encoded = json.dumps(result, sort_keys=True) + "\n"
Path("r234_result.json").write_text(encoded, encoding="utf-8")
Path("r191_result.json").write_text(encoded, encoding="utf-8")
print(json.dumps(result, sort_keys=True))
"""


HTTP_REPEAT_PROBE = r"""from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
import json, os, threading, time, urllib.request

os.chdir(Path(__file__).resolve().parent)
nonce = "r234-http-repeat"
Path("payload.txt").write_text(nonce, encoding="utf-8")
server = ThreadingHTTPServer(("127.0.0.1", 0), SimpleHTTPRequestHandler)
port = int(server.server_address[1])
thread = threading.Thread(target=server.serve_forever, daemon=True)
thread.start()
time.sleep(1.0)
started = time.time()
bodies = []
for _ in range(2):
    bodies.append(urllib.request.urlopen(f"http://127.0.0.1:{port}/payload.txt", timeout=5).read().decode("utf-8"))
time.sleep(1.0)
server.shutdown()
server.server_close()
thread.join(timeout=5)
body = "|".join(bodies)
result = {
    "status": "ok",
    "probe": "http_repeat",
    "port": port,
    "bytes": len(body),
    "body": body,
    "elapsed_ms": int((time.time() - started) * 1000),
}
encoded = json.dumps(result, sort_keys=True) + "\n"
Path("r234_result.json").write_text(encoded, encoding="utf-8")
Path("r191_result.json").write_text(encoded, encoding="utf-8")
print(json.dumps(result, sort_keys=True))
"""


TCP_PROBE = r"""import json, socket, threading, time
from pathlib import Path

nonce = b"r234-tcp-probe"
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind(("127.0.0.1", 0))
server.listen(1)
port = int(server.getsockname()[1])

def serve():
    conn, _ = server.accept()
    with conn:
        data = conn.recv(1024)
        conn.sendall(data.upper())

thread = threading.Thread(target=serve)
thread.start()
time.sleep(1.0)
started = time.time()
client = socket.create_connection(("127.0.0.1", port), timeout=5)
with client:
    client.sendall(nonce)
    body = client.recv(1024)
time.sleep(1.0)
thread.join(timeout=5)
server.close()
result = {
    "status": "ok",
    "probe": "tcp",
    "port": port,
    "bytes": len(body),
    "body": body.decode("utf-8"),
    "elapsed_ms": int((time.time() - started) * 1000),
}
encoded = json.dumps(result, sort_keys=True) + "\n"
Path("r234_result.json").write_text(encoded, encoding="utf-8")
Path("r191_result.json").write_text(encoded, encoding="utf-8")
print(json.dumps(result, sort_keys=True))
"""


MULTIPROCESS_TCP_PROBE = r"""import json, os, socket, subprocess, sys, tempfile, textwrap, time
from pathlib import Path

tmp = Path(tempfile.mkdtemp(prefix="r234-multiproc-"))
child = tmp / "child_server.py"
port_file = tmp / "port.json"
child.write_text(textwrap.dedent('''
    import json, socket, sys, time
    from pathlib import Path
    port_file = Path(sys.argv[1])
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(("127.0.0.1", 0))
    server.listen(1)
    port_file.write_text(json.dumps({"port": int(server.getsockname()[1])}), encoding="utf-8")
    time.sleep(1.0)
    conn, _ = server.accept()
    with conn:
        data = conn.recv(1024)
        conn.sendall(data[::-1])
    time.sleep(1.0)
    server.close()
''').strip() + "\n", encoding="utf-8")
proc = subprocess.Popen([sys.executable, str(child), str(port_file)])
for _ in range(100):
    if port_file.exists():
        break
    time.sleep(0.05)
port = int(json.loads(port_file.read_text(encoding="utf-8"))["port"])
time.sleep(1.0)
started = time.time()
client = socket.create_connection(("127.0.0.1", port), timeout=5)
with client:
    client.sendall(b"r234-multiproc")
    body = client.recv(1024)
returncode = proc.wait(timeout=5)
result = {
    "status": "ok" if returncode == 0 else "child_failed",
    "probe": "multiprocess_tcp",
    "port": port,
    "bytes": len(body),
    "body": body.decode("utf-8"),
    "child_returncode": returncode,
    "elapsed_ms": int((time.time() - started) * 1000),
}
encoded = json.dumps(result, sort_keys=True) + "\n"
Path("r234_result.json").write_text(encoded, encoding="utf-8")
Path("r191_result.json").write_text(encoded, encoding="utf-8")
print(json.dumps(result, sort_keys=True))
"""


@dataclass(frozen=True)
class AgentTask:
    task_id: str
    agent: str
    category: str
    prompt: str
    workspace: str
    sandbox: str = "workspace-write"


@dataclass(frozen=True)
class NetworkTask:
    task_id: str
    agent: str
    script_name: str
    script_body: str
    expected_probe: str
    expected_body: str
    required_actions: tuple[str, ...] = ("NET_BIND", "NET_LISTEN", "NET_CONNECT")


AGENT_TASKS = [
    AgentTask(
        task_id="r234-claude-json-write",
        agent="claude",
        category="write",
        workspace="claude_json_write",
        prompt=(
            "Create result.json with exactly {\"status\":\"ok\",\"agent\":\"claude\",\"run\":\"r234\"}. "
            "Use the current directory only. Then answer exactly one line: result_json=<created|missing>."
        ),
    )
]


NETWORK_TASKS = [
    NetworkTask(
        task_id="r234-codex-http",
        agent="codex",
        script_name="r234_http_probe.py",
        script_body=HTTP_PROBE,
        expected_probe="http",
        expected_body="r234-http-probe",
    ),
    NetworkTask(
        task_id="r234-codex-http-repeat",
        agent="codex",
        script_name="r234_http_repeat_probe.py",
        script_body=HTTP_REPEAT_PROBE,
        expected_probe="http_repeat",
        expected_body="r234-http-repeat|r234-http-repeat",
    ),
    NetworkTask(
        task_id="r234-codex-tcp",
        agent="codex",
        script_name="r234_tcp_probe.py",
        script_body=TCP_PROBE,
        expected_probe="tcp",
        expected_body="R234-TCP-PROBE",
    ),
    NetworkTask(
        task_id="r234-codex-multiprocess-tcp",
        agent="codex",
        script_name="r234_multiprocess_tcp_probe.py",
        script_body=MULTIPROCESS_TCP_PROBE,
        expected_probe="multiprocess_tcp",
        expected_body="corpitlum-432r",
    ),
    NetworkTask(
        task_id="r234-claude-http",
        agent="claude",
        script_name="r234_http_probe.py",
        script_body=HTTP_PROBE,
        expected_probe="http",
        expected_body="r234-http-probe",
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
        "owned by docs/visexp/r234_broader_agent_network_lineage.py\n",
        encoding="utf-8",
    )


def agent_command(
    agent: str,
    prompt: str,
    workspace: Path,
    answer_path: Path,
    codex_bin: str,
    claude_bin: str | None,
) -> tuple[list[str], Path]:
    if agent == "codex":
        return (
            [
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
            ],
            r114.REPO_ROOT,
        )
    if agent == "claude":
        if not claude_bin:
            raise RuntimeError("claude executable unavailable")
        command = (
            f"{shlex.quote(claude_bin)} -p --dangerously-skip-permissions "
            f"--output-format text {shlex.quote(prompt)} > {shlex.quote(str(answer_path))}"
        )
        return (["bash", "-lc", command], workspace)
    raise RuntimeError(f"unsupported agent: {agent}")


def write_agent_workspace(task: AgentTask, work_dir: Path) -> Path:
    workspace = work_dir / "workspaces" / task.task_id
    workspace.mkdir(parents=True, exist_ok=True)
    (workspace / "README.md").write_text(
        f"# {task.task_id}\n\nControlled R234 {task.agent} workspace.\n",
        encoding="utf-8",
    )
    return workspace


def run_recorded_command(
    task_id: str,
    agent: str,
    command_under_record: list[str],
    record_cwd: Path,
    agentsight_bin: Path,
    db_path: Path,
    timeout_s: int,
    negative_control: dict[str, str],
    negative_mode: str,
) -> Any:
    command = command_under_record
    if negative_mode == "wrapper":
        command = r114.wrap_with_negative_control(command, negative_control)
    elif negative_mode != "none":
        raise SystemExit(f"unsupported R234 negative mode: {negative_mode}")
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
    return r114.run_cmd(record_cmd, record_cwd, timeout_s)


def finish_lineage(
    row: dict[str, Any],
    agentsight_bin: Path,
    snapshot_path: Path,
    lineage_dir: Path,
    negative_control: dict[str, str],
    timeout_s: int,
) -> dict[str, Any]:
    if row.get("record_returncode") != 0:
        return row
    if not Path(str(row.get("db"))).exists():
        row["status"] = "missing_db"
        return row
    export_proc = r114.run_cmd(
        [
            str(agentsight_bin),
            "report",
            "export",
            "--db",
            str(row["db"]),
            "--output",
            str(snapshot_path),
            "--audit-limit",
            "50000",
        ],
        r114.REPO_ROOT,
        timeout_s,
    )
    row["export_returncode"] = export_proc.returncode
    row["snapshot"] = str(snapshot_path)
    if export_proc.returncode != 0 or not snapshot_path.exists():
        row["status"] = "export_failed"
        row["export_stdout_tail"] = r114.scrub(export_proc.stdout)
        row["export_stderr_tail"] = r114.scrub(export_proc.stderr)
        return row

    lineage_proc = r114.run_cmd(
        [
            "python3",
            str(r114.SCRIPT_DIR / "effect_lineage_smoke.py"),
            "--snapshot",
            str(snapshot_path),
            "--out",
            str(lineage_dir),
        ],
        r114.REPO_ROOT,
        timeout_s,
    )
    row["lineage_returncode"] = lineage_proc.returncode
    lineage_summary_path = lineage_dir / "effect-lineage-smoke.json"
    if lineage_summary_path.exists():
        row["lineage"] = r114.read_json(lineage_summary_path)

    snapshot = r114.read_json(snapshot_path)
    row.update(r114.target_status(snapshot))
    lineage_rows = r114.read_lineage_csv(lineage_dir / "effect-lineage.csv")
    row["precision_recall"] = r114.precision_recall_summary(
        snapshot,
        lineage_rows,
        [negative_control["marker"], negative_control["negative_dir"], negative_control["sibling_dir"]],
    )
    row["snapshot_counts"] = {
        "sessions": len(snapshot.get("sessions") or []),
        "tool_calls": len(snapshot.get("tool_calls") or []),
        "process_nodes": len(snapshot.get("process_nodes") or []),
        "audit_events": len(snapshot.get("audit_events") or []),
    }
    return row


def scoped_lineage_ok(row: dict[str, Any]) -> bool:
    pr = row.get("precision_recall") or {}
    return (
        row.get("record_status") == "ok"
        and row.get("target_status") == "completed"
        and int(pr.get("in_scope_effect_events") or 0) > 0
        and int(pr.get("negative_effect_events_observed") or 0) > 0
        and int(pr.get("negative_joined_effect_events") or 0) == 0
        and float(pr.get("precision_pct") or 0.0) >= 98.0
        and float(pr.get("recall_pct") or 0.0) >= 95.0
    )


def run_agent_task(
    task: AgentTask,
    agentsight_bin: Path,
    codex_bin: str,
    claude_bin: str | None,
    work_dir: Path,
    timeout_s: int,
    negative_mode: str,
) -> dict[str, Any]:
    task_dir = work_dir / "runs" / task.task_id
    task_dir.mkdir(parents=True, exist_ok=True)
    workspace = write_agent_workspace(task, work_dir)
    db_path = task_dir / f"{task.task_id}.db"
    snapshot_path = task_dir / f"{task.task_id}.snapshot.json"
    answer_path = task_dir / f"{task.task_id}.answer.txt"
    lineage_dir = task_dir / "lineage"
    helper = r114.Task(task.task_id, task.category, task.prompt, task.sandbox, task.workspace)
    negative_control = r114.negative_control_paths(helper, work_dir)

    row: dict[str, Any] = {
        "task_id": task.task_id,
        "kind": "agent",
        "agent": task.agent,
        "category": task.category,
        "workspace": task.workspace,
        "db": str(db_path),
        "record_status": "not_run",
        "negative_control": negative_control,
    }
    try:
        command, record_cwd = agent_command(task.agent, task.prompt, workspace, answer_path, codex_bin, claude_bin)
        record_proc = run_recorded_command(
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
    row = finish_lineage(row, agentsight_bin, snapshot_path, lineage_dir, negative_control, timeout_s)
    row["status"] = "ok" if scoped_lineage_ok(row) else "partial"
    return row


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


def network_oracle(row: dict[str, Any], task: NetworkTask) -> dict[str, Any]:
    net = row.get("network_lineage") or {}
    actions = {key: int(value) for key, value in (net.get("target_network_actions") or {}).items()}
    missing_actions = [action for action in task.required_actions if actions.get(action, 0) <= 0]
    target_total = int(net.get("target_network_effect_events") or 0)
    target_joined = int(net.get("joined_target_network_effect_events") or 0)
    return {
        "required_actions": list(task.required_actions),
        "missing_required_actions": missing_actions,
        "required_actions_ok": not missing_actions,
        "target_network_rows_observed": target_total > 0,
        "all_target_network_rows_joined": target_total > 0 and target_joined == target_total,
        "orphan_target_network_rows": int(net.get("orphan_target_network_effect_events") or 0),
    }


def network_lineage_ok(row: dict[str, Any]) -> bool:
    pr = row.get("precision_recall") or {}
    oracle = row.get("target_network_oracle") or {}
    return (
        scoped_lineage_ok(row)
        and bool(row.get("probe_result_ok"))
        and bool(oracle.get("required_actions_ok"))
        and bool(oracle.get("all_target_network_rows_joined"))
        and int(oracle.get("orphan_target_network_rows") or 0) == 0
        and int(pr.get("negative_joined_effect_events") or 0) == 0
    )


def run_network_task(
    task: NetworkTask,
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
        "contents of r234_result.json and nothing else."
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
        record_proc = run_recorded_command(
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
    row = finish_lineage(row, agentsight_bin, snapshot_path, lineage_dir, negative_control, timeout_s)
    if snapshot_path.exists():
        lineage_rows = r114.read_lineage_csv(lineage_dir / "effect-lineage.csv")
        row["network_lineage"] = r191.summarize_network(lineage_rows)
    probe_result = read_probe_result(workspace / "r234_result.json")
    row["probe_result"] = probe_result
    row["probe_result_ok"] = result_matches(task, probe_result)
    row["target_network_oracle"] = network_oracle(row, task)
    row["status"] = "ok" if network_lineage_ok(row) else "partial"
    return row


def run_network_task_with_r191_runner(
    task: NetworkTask,
    agentsight_bin: Path,
    codex_bin: str,
    claude_bin: str | None,
    work_dir: Path,
    timeout_s: int,
    negative_mode: str,
) -> dict[str, Any]:
    return run_network_task(task, agentsight_bin, codex_bin, claude_bin, work_dir, timeout_s, negative_mode)


def aggregate_agent(rows: list[dict[str, Any]]) -> dict[str, Any]:
    totals = Counter()
    statuses = Counter(str(row.get("status") or "unknown") for row in rows)
    agents = Counter(str(row.get("agent") or "unknown") for row in rows)
    for row in rows:
        pr = row.get("precision_recall") or {}
        totals["in_scope_effect_events"] += int(pr.get("in_scope_effect_events") or 0)
        totals["negative_effect_events_observed"] += int(pr.get("negative_effect_events_observed") or 0)
        totals["negative_joined_effect_events"] += int(pr.get("negative_joined_effect_events") or 0)
        totals["true_positives"] += int(pr.get("true_positives") or 0)
        totals["false_positives"] += int(pr.get("false_positives") or 0)
        totals["false_negatives"] += int(pr.get("false_negatives") or 0)
    tp = totals["true_positives"]
    fp = totals["false_positives"]
    fn = totals["false_negatives"]
    return {
        "tasks": len(rows),
        "statuses": dict(statuses),
        "agents": dict(agents),
        **dict(totals),
        "precision_pct": round(100.0 * tp / (tp + fp), 3) if (tp + fp) else 0.0,
        "recall_pct": round(100.0 * tp / (tp + fn), 3) if (tp + fn) else 0.0,
    }


def aggregate_network(rows: list[dict[str, Any]]) -> dict[str, Any]:
    base = r191.aggregate(rows)
    probes = Counter(str((row.get("probe_result") or {}).get("probe") or "unknown") for row in rows)
    agents = Counter(str(row.get("agent") or "unknown") for row in rows)
    required_actions_ok = sum(1 for row in rows if (row.get("target_network_oracle") or {}).get("required_actions_ok"))
    all_joined = sum(1 for row in rows if (row.get("target_network_oracle") or {}).get("all_target_network_rows_joined"))
    return {
        **base,
        "agents": dict(agents),
        "probes": dict(probes),
        "required_action_tasks_ok": required_actions_ok,
        "all_target_network_rows_joined_tasks": all_joined,
    }


def combined_aggregate(agent: dict[str, Any], network: dict[str, Any]) -> dict[str, Any]:
    tp = int(agent.get("true_positives") or 0) + int(network.get("true_positives") or 0)
    fp = int(agent.get("false_positives") or 0) + int(network.get("false_positives") or 0)
    fn = int(agent.get("false_negatives") or 0) + int(network.get("false_negatives") or 0)
    return {
        "agent_tasks": int(agent.get("tasks") or 0),
        "network_tasks": int(network.get("tasks") or 0),
        "tasks": int(agent.get("tasks") or 0) + int(network.get("tasks") or 0),
        "in_scope_effect_events": int(agent.get("in_scope_effect_events") or 0)
        + int(network.get("true_positives") or 0)
        + int(network.get("false_negatives") or 0),
        "target_network_effect_events": int(network.get("target_network_effect_events") or 0),
        "joined_target_network_effect_events": int(network.get("joined_target_network_effect_events") or 0),
        "negative_effect_events_observed": int(agent.get("negative_effect_events_observed") or 0)
        + int(network.get("negative_effect_events_observed") or 0),
        "negative_joined_effect_events": int(agent.get("negative_joined_effect_events") or 0)
        + int(network.get("negative_joined_effect_events") or 0),
        "true_positives": tp,
        "false_positives": fp,
        "false_negatives": fn,
        "precision_pct": round(100.0 * tp / (tp + fp), 3) if (tp + fp) else 0.0,
        "recall_pct": round(100.0 * tp / (tp + fn), 3) if (tp + fn) else 0.0,
    }


def keep_keys(source: dict[str, Any], keys: list[str]) -> dict[str, Any]:
    return {key: source[key] for key in keys if key in source}


def compact_precision_recall(summary: dict[str, Any]) -> dict[str, Any]:
    return keep_keys(
        summary,
        [
            "agent_process_count",
            "false_negatives",
            "false_positives",
            "in_scope_effect_events",
            "negative_control_status",
            "negative_effect_events_observed",
            "negative_joined_effect_events",
            "out_of_scope_effect_events",
            "precision_pct",
            "recall_pct",
            "true_positives",
        ],
    )


def compact_network_lineage(summary: dict[str, Any]) -> dict[str, Any]:
    return keep_keys(
        summary,
        [
            "joined_network_effect_events",
            "joined_target_network_effect_events",
            "network_effect_events",
            "network_process_comms",
            "orphan_target_network_effect_events",
            "target_network_actions",
            "target_network_effect_events",
            "target_network_join_pct",
            "target_network_process_comms",
        ],
    )


def compact_probe_result(result: dict[str, Any]) -> dict[str, Any]:
    return keep_keys(result, ["status", "probe", "body", "bytes"])


def compact_task_row(row: dict[str, Any]) -> dict[str, Any]:
    compact = keep_keys(
        row,
        [
            "task_id",
            "kind",
            "agent",
            "category",
            "script",
            "status",
            "record_status",
            "record_returncode",
            "target_status",
            "target_exit_code",
            "snapshot_counts",
            "probe_result_ok",
            "target_network_oracle",
        ],
    )
    if row.get("kind") == "agent":
        compact["workspace"] = row.get("workspace")
        compact["answer_summary"] = str(row.get("answer") or "").strip()
    if row.get("precision_recall"):
        compact["precision_recall"] = compact_precision_recall(row["precision_recall"])
    if row.get("network_lineage"):
        compact["network_lineage"] = compact_network_lineage(row["network_lineage"])
    if row.get("probe_result"):
        compact["probe_result"] = compact_probe_result(row["probe_result"])
    return compact


def compact_result_for_commit(result: dict[str, Any]) -> dict[str, Any]:
    network_aggregate = dict(result["network_aggregate"])
    network_aggregate.pop("target_network_targets", None)
    network_aggregate.pop("target_network_examples", None)
    return {
        **result,
        "network_aggregate": network_aggregate,
        "agent_tasks": [compact_task_row(row) for row in result["agent_tasks"]],
        "network_tasks": [compact_task_row(row) for row in result["network_tasks"]],
    }


def write_markdown(path: Path, result: dict[str, Any]) -> None:
    agent = result["agent_aggregate"]
    network = result["network_aggregate"]
    combined = result["aggregate"]
    lines = [
        "# R234 Controlled Agent/HTTP-Network Lineage",
        "",
        f"Last updated: {date.today().isoformat()}",
        "Stage at update: execute/analyze",
        "Source/command: `python3 docs/visexp/r234_broader_agent_network_lineage.py`",
        f"Completeness: {result['status']}",
        "",
        "R234 extends the controlled exact-lineage oracle to another agent family",
        "when available and to two Codex HTTP-family target-network probes: single GET",
        "and repeated GET. It remains a",
        "local controlled replication experiment, not user evidence.",
        "",
        "## Aggregate",
        "",
        f"- Agent tasks: {agent.get('tasks', 0)}; agents: {agent.get('agents', {})}; statuses: {agent.get('statuses', {})}.",
        f"- Network tasks: {network.get('tasks', 0)}; agents: {network.get('agents', {})}; probes: {network.get('probes', {})}; statuses: {network.get('task_statuses', {})}.",
        f"- Combined scoped precision/recall: {combined['precision_pct']}%/{combined['recall_pct']}%.",
        f"- Target network effects: {combined['joined_target_network_effect_events']}/{combined['target_network_effect_events']} joined.",
        f"- Negative controls: observed={combined['negative_effect_events_observed']}, joined={combined['negative_joined_effect_events']}.",
        f"- Gates: agent_family={result['agent_family_gate']}, network={result['network_gate']}, controlled_expansion={result['broader_agent_network_lineage_supported']}.",
        "",
        "## Agent Tasks",
        "",
        "| Task | Agent | Status | Target | In scope | Neg observed | Neg joined | Precision/Recall | Answer |",
        "|------|-------|--------|--------|---------:|-------------:|-----------:|------------------:|--------|",
    ]
    for row in result["agent_tasks"]:
        pr = row.get("precision_recall") or {}
        answer = str(row.get("answer_summary") or "").replace("|", "\\|").replace("\n", " ")[:100]
        lines.append(
            f"| `{row['task_id']}` | {row.get('agent')} | {row.get('status')} | {row.get('target_status')} | "
            f"{pr.get('in_scope_effect_events', 0)} | {pr.get('negative_effect_events_observed', 0)} | "
            f"{pr.get('negative_joined_effect_events', 0)} | {pr.get('precision_pct', 0.0)}%/{pr.get('recall_pct', 0.0)}% | {answer} |"
        )
    lines.extend(
        [
            "",
            "## Network Tasks",
            "",
            "| Task | Agent | Status | Probe | Target network | Required actions | Neg joined | Precision/Recall | Answer |",
            "|------|-------|--------|-------|---------------:|------------------|-----------:|------------------:|--------|",
        ]
    )
    for row in result["network_tasks"]:
        net = row.get("network_lineage") or {}
        pr = row.get("precision_recall") or {}
        oracle = row.get("target_network_oracle") or {}
        probe = row.get("probe_result") or {}
        answer = (
            f"body={probe.get('body')} bytes={probe.get('bytes')} ok={row.get('probe_result_ok')}"
            if probe
            else ""
        )
        answer = answer.replace("|", "\\|").replace("\n", " ")[:120]
        missing = oracle.get("missing_required_actions") or []
        lines.append(
            f"| `{row['task_id']}` | {row.get('agent')} | {row.get('status')} | "
            f"{probe.get('probe')}:{probe.get('status')} | "
            f"{net.get('joined_target_network_effect_events', 0)}/{net.get('target_network_effect_events', 0)} | "
            f"{'ok' if not missing else ','.join(missing)} | {pr.get('negative_joined_effect_events', 0)} | "
            f"{pr.get('precision_pct', 0.0)}%/{pr.get('recall_pct', 0.0)}% | {answer} |"
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

    selected_agent = AGENT_TASKS[: args.agent_task_limit]
    selected_network = NETWORK_TASKS[: args.network_task_limit]
    if args.print_manifest:
        payload = {
            "schema_version": 1,
            "run_id": "R234",
            "agent_tasks": [task.__dict__ for task in selected_agent],
            "network_tasks": [
                {
                    "task_id": task.task_id,
                    "agent": task.agent,
                    "script": task.script_name,
                    "probe": task.expected_probe,
                    "required_actions": list(task.required_actions),
                }
                for task in selected_network
            ],
        }
        print(json.dumps(payload, indent=2))
        return payload

    agent_rows = [
        run_agent_task(task, agentsight_bin, codex_bin, claude_bin, work_dir, args.timeout, args.negative_mode)
        for task in selected_agent
    ]
    network_rows = [
        run_network_task_with_r191_runner(
            task, agentsight_bin, codex_bin, claude_bin, work_dir, args.timeout, args.negative_mode
        )
        for task in selected_network
    ]
    agent_agg = aggregate_agent(agent_rows)
    network_agg = aggregate_network(network_rows)
    combined = combined_aggregate(agent_agg, network_agg)
    agent_family_gate = (
        any(row.get("agent") == "claude" and row.get("status") == "ok" for row in agent_rows + network_rows)
        and int(agent_agg.get("negative_joined_effect_events") or 0) == 0
    )
    network_gate = (
        network_agg.get("tasks") == len(network_rows)
        and (network_agg.get("task_statuses") or {}).get("ok", 0) == len(network_rows)
        and int(network_agg.get("target_network_effect_events") or 0) > 0
        and int(network_agg.get("joined_target_network_effect_events") or 0)
        == int(network_agg.get("target_network_effect_events") or 0)
        and int(network_agg.get("orphan_target_network_effect_events") or 0) == 0
        and int(network_agg.get("negative_joined_effect_events") or 0) == 0
        and int(network_agg.get("required_action_tasks_ok") or 0) == len(network_rows)
        and float(network_agg.get("precision_pct") or 0.0) >= 98.0
        and float(network_agg.get("recall_pct") or 0.0) >= 95.0
    )
    passed = agent_family_gate and network_gate
    status = "ok" if passed else "partial"
    boundary = (
        "R234 supports C4/RQ3 for this controlled local expansion: at least one "
        "Claude command-mode run and all target network probe rows across the "
        "default HTTP target-network workloads join to the recorded agent task, "
        "with zero negative-control joins. It does not prove arbitrary agents, "
        "raw-socket or Claude-launched target-network workloads, HTTP payload/URL "
        "reconstruction, C5 user utility, or C6 tag adequacy."
        if passed
        else "R234 is partial: the broader-agent, target-network, or negative-control gates did not all pass."
    )
    result = {
        "schema_version": 1,
        "run_id": "R234",
        "status": status,
        "scope": "controlled_broader_agent_network_lineage",
        "generated_at": date.today().isoformat(),
        "work_dir": str(work_dir),
        "agentsight_bin": r114.rel(agentsight_bin),
        "codex_bin": r114.scrub(codex_bin, limit=400),
        "claude_bin": r114.scrub(claude_bin or "unavailable", limit=400),
        "agent_task_limit": len(agent_rows),
        "network_task_limit": len(network_rows),
        "negative_mode": args.negative_mode,
        "agent_family_gate": agent_family_gate,
        "network_gate": network_gate,
        "broader_agent_network_lineage_supported": passed,
        "agent_aggregate": agent_agg,
        "network_aggregate": network_agg,
        "aggregate": combined,
        "agent_tasks": agent_rows,
        "network_tasks": network_rows,
        "boundary": boundary,
        "artifact_boundary": (
            "Raw SQLite DBs, exported snapshots, workspaces, and per-event lineage CSVs stay in the "
            "local work dir; committed artifacts contain aggregate/task summaries without per-event examples."
        ),
    }
    result = compact_result_for_commit(result)
    result = scrub_r234_artifact_value(r114.scrub_artifact_value(result), work_dir)
    json_path = out_dir / "broader-agent-network-lineage-r234.json"
    md_path = out_dir / "broader-agent-network-lineage-r234.md"
    result["outputs"] = {
        "json": r114.rel(json_path),
        "markdown": r114.rel(md_path),
    }
    json_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_markdown(md_path, result)
    print(
        json.dumps(
            {
                "status": result["status"],
                "agent_family_gate": result["agent_family_gate"],
                "network_gate": result["network_gate"],
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
    parser.add_argument("--agent-task-limit", type=int, default=len(AGENT_TASKS))
    parser.add_argument("--network-task-limit", type=int, default=2)
    parser.add_argument("--timeout", type=int, default=360)
    parser.add_argument("--negative-mode", choices=("wrapper", "none"), default="wrapper")
    parser.add_argument("--print-manifest", action="store_true")
    return parser


if __name__ == "__main__":
    run(build_parser().parse_args())
