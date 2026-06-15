#!/usr/bin/env python3
"""Run the R114 live exact-lineage suite with negative controls.

The suite intentionally runs real `agentsight record -- codex exec ...` tasks.
It creates new local Codex session logs and temporary task workspaces as side
effects, but it never modifies or deletes existing agent traces.
"""

from __future__ import annotations

import argparse
import csv
import json
import shutil
import subprocess
import time
from collections import Counter
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[1]
DEFAULT_OUT = SCRIPT_DIR / "out"
DEFAULT_WORK = Path("/tmp/agentsight-r114-live")
WORK_MARKER = ".agentsight-r114-live"


@dataclass(frozen=True)
class Task:
    task_id: str
    category: str
    prompt: str
    sandbox: str = "read-only"
    workspace: str = "repo"


TASKS = [
    Task(
        "r114-read-state",
        "read",
        "Read docs/visexp/STATE.md. Answer exactly one line with the value after 'Next action:'. Do not modify files.",
    ),
    Task(
        "r114-read-verdict",
        "read",
        "Read docs/visexp/CLAIM_VERDICT.md. Answer exactly one line: c4=<verdict word>. Do not modify files.",
    ),
    Task(
        "r114-read-related",
        "read",
        "Read docs/visexp/RELATED_WORK_NOTES.md. Answer exactly one line naming the first listed system. Do not modify files.",
    ),
    Task(
        "r114-rg-baseline",
        "read",
        "Using read-only commands, count lines mentioning 'span-duration' in docs/visexp. Answer exactly one line: span_duration_lines=<n>.",
    ),
    Task(
        "r114-agentflame-readme",
        "read",
        "Read agentflame/README.md. Answer exactly one line with the command subcommand used for model benchmarks. Do not modify files.",
    ),
    Task(
        "r114-paper-search",
        "read",
        "Using read-only commands, check whether docs/visexp/paper/main.tex mentions AgentFlame. Answer exactly one line: paper_agentflame=<yes|no>.",
    ),
    Task(
        "r114-json-check",
        "read",
        "Using read-only commands, verify docs/visexp/out/model-benchmarks-r121.json parses as JSON. Answer exactly one line: json_ok=<yes|no>.",
    ),
    Task(
        "r114-claim-list",
        "read",
        "Read docs/visexp/EXPERIMENT_PLAN.md. Answer exactly one line with the claim ID for developer utility. Do not modify files.",
    ),
    Task(
        "r114-edit-python-bug",
        "edit",
        "Fix calc.py so `python3 -m unittest` passes. You may edit files in the current directory only. After running the test, answer exactly one line: tests=<passed|failed>.",
        sandbox="workspace-write",
        workspace="python_bug",
    ),
    Task(
        "r114-edit-doc-note",
        "edit",
        "Append one sentence to NOTES.md explaining that semantic effect profiling joins intent to system effects. You may edit files in the current directory only. Answer exactly one line: note_updated=<yes|no>.",
        sandbox="workspace-write",
        workspace="doc_note",
    ),
    Task(
        "r114-test-debug",
        "test",
        "Run `python3 -m unittest` and fix the failing assertion in test_math_ops.py. You may edit files in the current directory only. Answer exactly one line: unittest=<passed|failed>.",
        sandbox="workspace-write",
        workspace="test_debug",
    ),
    Task(
        "r114-edit-rust-text",
        "edit",
        "Fix the typo in README.md by changing 'flamgraph' to 'flamegraph'. You may edit files in the current directory only. Answer exactly one line: typo_fixed=<yes|no>.",
        sandbox="workspace-write",
        workspace="typo_repo",
    ),
    Task(
        "r114-dependency-inspect",
        "dependency",
        "Read pyproject.toml in the current directory. Answer exactly one line with the package name. Do not install dependencies.",
        sandbox="read-only",
        workspace="python_pkg",
    ),
    Task(
        "r114-failure-retry",
        "failure",
        "Run `python3 missing_file.py`, observe that it fails, then answer exactly one line with the missing filename. Do not create files.",
        sandbox="read-only",
        workspace="failure_repo",
    ),
    Task(
        "r114-network-docs",
        "dependency",
        "Do not browse the network. Read docs/visexp/FOLLOWUP_PLAN.md and answer exactly one line with the required R114 task count.",
    ),
    Task(
        "r114-ablation-read",
        "read",
        "Read docs/visexp/EXPERIMENT_TRACKER.md. Answer exactly one line with the planned R131 result path. Do not modify files.",
    ),
    Task(
        "r114-process-read",
        "read",
        "Using read-only commands, count occurrences of 'root_pid_time_window' in docs/visexp. Answer exactly one line: root_pid_refs=<n>.",
    ),
    Task(
        "r114-write-json",
        "edit",
        "Create result.json with exactly {\"status\":\"ok\"}. You may edit files in the current directory only. Answer exactly one line: result_json=<created|missing>.",
        sandbox="workspace-write",
        workspace="json_write",
    ),
    Task(
        "r114-fix-shell-script",
        "test",
        "Run `bash check.sh`, fix the script so it exits 0, then answer exactly one line: check=<passed|failed>.",
        sandbox="workspace-write",
        workspace="shell_fix",
    ),
    Task(
        "r114-summary-read",
        "read",
        "Read docs/visexp/RESEARCH_PLAN.md. Answer exactly one line naming the paper framing after 'AgentFlame:'. Do not modify files.",
    ),
]


NEGATIVE_WORKER_CODE = r"""
import pathlib
import sys
import time

neg_dir = pathlib.Path(sys.argv[1])
sibling_dir = pathlib.Path(sys.argv[2])
stop_file = pathlib.Path(sys.argv[3])
marker = sys.argv[4]
idx = 0
while idx < 200 and not stop_file.exists():
    for base in (neg_dir, sibling_dir):
        path = base / f"{marker}_{idx}.txt"
        path.write_text(marker + "\n", encoding="utf-8")
        _ = path.read_text(encoding="utf-8")
    idx += 1
    time.sleep(0.05)
"""


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT.resolve()))
    except Exception:
        return str(path)


def scrub(text: str, limit: int = 1600) -> str:
    home = str(Path.home())
    text = text.replace(home, "$HOME")
    text = text.replace(str(REPO_ROOT.resolve()), "$REPO")
    return text[-limit:]


def run_cmd(cmd: list[str], cwd: Path, timeout_s: int) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        cwd=str(cwd),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout_s,
        check=False,
    )


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def resolve_executable(value: str, label: str) -> str:
    path = Path(value)
    if path.parent != Path("."):
        candidates = [path]
        if not path.is_absolute():
            candidates.append(REPO_ROOT / path)
        for candidate in candidates:
            if candidate.exists() and candidate.is_file():
                return str(candidate.resolve())
        raise SystemExit(f"{label} executable not found: {value}")
    found = shutil.which(value)
    if found:
        return found
    raise SystemExit(f"{label} executable not found on PATH: {value}")


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
    (work_dir / WORK_MARKER).write_text("owned by docs/visexp/r114_live_record_suite.py\n", encoding="utf-8")


def workspace_for_task(task: Task, work_dir: Path) -> Path:
    if task.workspace == "repo":
        return REPO_ROOT
    path = work_dir / "workspaces" / task.task_id
    path.mkdir(parents=True, exist_ok=True)
    if task.workspace == "python_bug":
        (path / "calc.py").write_text("def add(a, b):\n    return a - b\n", encoding="utf-8")
        (path / "test_calc.py").write_text(
            "import unittest\nfrom calc import add\n\nclass CalcTest(unittest.TestCase):\n    def test_add(self):\n        self.assertEqual(add(2, 3), 5)\n\nif __name__ == '__main__':\n    unittest.main()\n",
            encoding="utf-8",
        )
    elif task.workspace == "doc_note":
        (path / "NOTES.md").write_text("# Notes\n\nAgentFlame records local agent activity.\n", encoding="utf-8")
    elif task.workspace == "test_debug":
        (path / "math_ops.py").write_text("def double(x):\n    return x + 1\n", encoding="utf-8")
        (path / "test_math_ops.py").write_text(
            "import unittest\nfrom math_ops import double\n\nclass MathOpsTest(unittest.TestCase):\n    def test_double(self):\n        self.assertEqual(double(4), 8)\n\nif __name__ == '__main__':\n    unittest.main()\n",
            encoding="utf-8",
        )
    elif task.workspace == "typo_repo":
        (path / "README.md").write_text("This flamgraph example is intentionally misspelled.\n", encoding="utf-8")
    elif task.workspace == "python_pkg":
        (path / "pyproject.toml").write_text("[project]\nname = \"agentflame-r114-fixture\"\nversion = \"0.0.1\"\n", encoding="utf-8")
    elif task.workspace == "failure_repo":
        (path / "README.md").write_text("This workspace intentionally lacks missing_file.py.\n", encoding="utf-8")
    elif task.workspace == "json_write":
        (path / "README.md").write_text("Create result.json here.\n", encoding="utf-8")
    elif task.workspace == "shell_fix":
        (path / "check.sh").write_text("#!/usr/bin/env bash\nexit 1\n", encoding="utf-8")
        (path / "check.sh").chmod(0o755)
    else:
        raise SystemExit(f"unknown task workspace: {task.workspace}")
    return path


def task_command(task: Task, task_cwd: Path, answer_path: Path, codex_bin: str) -> list[str]:
    return [
        codex_bin,
        "exec",
        "--sandbox",
        task.sandbox,
        "--cd",
        str(task_cwd),
        "--output-last-message",
        str(answer_path),
        task.prompt,
    ]


def negative_control_paths(task: Task, work_dir: Path) -> dict[str, str]:
    neg_dir = work_dir / "negative-controls" / task.task_id
    sibling_dir = work_dir / "sibling-repo-negative" / task.task_id
    neg_dir.mkdir(parents=True, exist_ok=True)
    sibling_dir.mkdir(parents=True, exist_ok=True)
    stop_file = neg_dir / "stop"
    marker = f"R114_NEGATIVE_CONTROL_{task.task_id}"
    worker = neg_dir / "negative_worker.py"
    worker.write_text(NEGATIVE_WORKER_CODE, encoding="utf-8")
    return {
        "marker": marker,
        "negative_dir": str(neg_dir),
        "sibling_dir": str(sibling_dir),
        "stop_file": str(stop_file),
        "worker": str(worker),
    }


def start_negative_control(task: Task, work_dir: Path) -> tuple[subprocess.Popen[str], dict[str, str]]:
    control = negative_control_paths(task, work_dir)
    proc = subprocess.Popen(
        [
            "python3",
            "-u",
            control["worker"],
            control["negative_dir"],
            control["sibling_dir"],
            control["stop_file"],
            control["marker"],
        ],
        cwd=str(work_dir),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return proc, control


def wrap_with_negative_control(command: list[str], control: dict[str, str]) -> list[str]:
    wrapper_script = (
        'python3 "$1" "$2" "$3" "$4" "$5" >/dev/null 2>&1 & '
        "shift 5; "
        'exec "$@"'
    )
    return [
        "bash",
        "-lc",
        wrapper_script,
        "r114-negative-wrapper",
        control["worker"],
        control["negative_dir"],
        control["sibling_dir"],
        control["stop_file"],
        control["marker"],
        *command,
    ]


def stop_negative_control(proc: subprocess.Popen[str], control: dict[str, str]) -> dict[str, Any]:
    Path(control["stop_file"]).write_text("stop\n", encoding="utf-8")
    try:
        stdout, stderr = proc.communicate(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()
        stdout, stderr = proc.communicate(timeout=5)
    return {
        **control,
        "returncode": proc.returncode,
        "stdout_tail": scrub(stdout or "", 400),
        "stderr_tail": scrub(stderr or "", 400),
    }


def failure_tail(proc: subprocess.CompletedProcess[str]) -> dict[str, str]:
    if proc.returncode == 0:
        return {}
    return {
        "stdout_tail": scrub(proc.stdout),
        "stderr_tail": scrub(proc.stderr),
    }


def read_lineage_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def row_joined(row: dict[str, str]) -> bool:
    return str(row.get("joined", "")).lower() in {"true", "1", "yes"}


def event_text(event: dict[str, Any]) -> str:
    parts = [
        str(event.get("id") or ""),
        str(event.get("target") or ""),
        str(event.get("summary") or ""),
        str(event.get("details") or ""),
    ]
    return "\n".join(parts)


def precision_recall_summary(
    snapshot: dict[str, Any],
    rows: list[dict[str, str]],
    marker_fragments: list[str],
) -> dict[str, Any]:
    negative_ids = {
        str(event.get("id"))
        for event in snapshot.get("audit_events") or []
        if event.get("id") and any(fragment in event_text(event) for fragment in marker_fragments)
    }
    row_by_id = {str(row.get("event_id")): row for row in rows if row.get("event_id")}
    negative_rows = [row_by_id[event_id] for event_id in sorted(negative_ids) if event_id in row_by_id]
    negative_joined = [row for row in negative_rows if row_joined(row)]
    nonnegative_rows = [row for row in rows if str(row.get("event_id")) not in negative_ids]
    true_positives = sum(1 for row in nonnegative_rows if row_joined(row))
    false_negatives = sum(1 for row in nonnegative_rows if not row_joined(row))
    false_positives = len(negative_joined)
    precision_den = true_positives + false_positives
    recall_den = true_positives + false_negatives
    return {
        "negative_effect_events_observed": len(negative_rows),
        "negative_joined_effect_events": false_positives,
        "true_positives": true_positives,
        "false_positives": false_positives,
        "false_negatives": false_negatives,
        "precision_pct": round(100.0 * true_positives / precision_den, 3) if precision_den else 0.0,
        "recall_pct": round(100.0 * true_positives / recall_den, 3) if recall_den else 0.0,
        "negative_control_status": "observed" if negative_rows else "not_observed",
        "negative_join_examples": negative_joined[:5],
    }


def record_task(
    task: Task,
    agentsight_bin: Path,
    codex_bin: str,
    work_dir: Path,
    timeout_s: int,
    negative_mode: str,
) -> dict[str, Any]:
    task_dir = work_dir / "runs" / task.task_id
    task_dir.mkdir(parents=True, exist_ok=True)
    task_cwd = workspace_for_task(task, work_dir)
    db_path = task_dir / f"{task.task_id}.db"
    snapshot_path = task_dir / f"{task.task_id}.snapshot.json"
    lineage_dir = task_dir / "lineage"
    answer_path = task_dir / f"{task.task_id}.answer.txt"

    task_cmd = task_command(task, task_cwd, answer_path, codex_bin)
    negative_proc: subprocess.Popen[str] | None = None
    if negative_mode == "external":
        negative_proc, negative_control = start_negative_control(task, work_dir)
        time.sleep(0.2)
        command_under_record = task_cmd
    elif negative_mode == "wrapper":
        negative_control = negative_control_paths(task, work_dir)
        command_under_record = wrap_with_negative_control(task_cmd, negative_control)
    else:
        raise SystemExit(f"unknown negative mode: {negative_mode}")
    record_cmd = [
        str(agentsight_bin),
        "record",
        "--no-server",
        "--db",
        str(db_path),
        "--",
        *command_under_record,
    ]

    started = time.time()
    try:
        record_proc = run_cmd(record_cmd, REPO_ROOT, timeout_s)
    except subprocess.TimeoutExpired as error:
        stopped = (
            stop_negative_control(negative_proc, negative_control)
            if negative_proc
            else {**negative_control, "mode": negative_mode, "returncode": None}
        )
        return {
            "task_id": task.task_id,
            "category": task.category,
            "status": "timeout",
            "duration_seconds": round(time.time() - started, 3),
            "db": str(db_path),
            "negative_control": stopped,
            "record_returncode": None,
            "stdout_tail": scrub(error.stdout or ""),
            "stderr_tail": scrub(error.stderr or ""),
        }
    if negative_proc:
        stopped = stop_negative_control(negative_proc, negative_control)
    else:
        Path(negative_control["stop_file"]).write_text("stop\n", encoding="utf-8")
        stopped = {**negative_control, "mode": negative_mode, "returncode": None}
    duration = round(time.time() - started, 3)
    row: dict[str, Any] = {
        "task_id": task.task_id,
        "category": task.category,
        "workspace": task.workspace,
        "sandbox": task.sandbox,
        "status": "record_failed" if record_proc.returncode else "record_ok",
        "record_status": "failed" if record_proc.returncode else "ok",
        "duration_seconds": duration,
        "db": str(db_path),
        "record_returncode": record_proc.returncode,
        "negative_control": stopped,
        "answer": scrub(answer_path.read_text(encoding="utf-8")) if answer_path.exists() else "",
    }
    row.update(failure_tail(record_proc))

    if not db_path.exists():
        row["status"] = "missing_db"
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
    row["snapshot"] = str(snapshot_path)
    if export_proc.returncode != 0:
        row["export_stdout_tail"] = scrub(export_proc.stdout)
        row["export_stderr_tail"] = scrub(export_proc.stderr)
    if export_proc.returncode != 0 or not snapshot_path.exists():
        row["status"] = "export_failed"
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
    if lineage_proc.returncode not in (0, 1):
        row["lineage_stdout_tail"] = scrub(lineage_proc.stdout)
        row["lineage_stderr_tail"] = scrub(lineage_proc.stderr)
    lineage_summary_path = lineage_dir / "effect-lineage-smoke.json"
    if lineage_summary_path.exists():
        row["lineage"] = read_json(lineage_summary_path)
    else:
        row["status"] = "lineage_missing"

    snapshot = read_json(snapshot_path)
    lineage_rows = read_lineage_csv(lineage_dir / "effect-lineage.csv")
    control_markers = [
        stopped["marker"],
        stopped["negative_dir"],
        stopped["sibling_dir"],
    ]
    row["precision_recall"] = precision_recall_summary(snapshot, lineage_rows, control_markers)
    row["snapshot_counts"] = {
        "sessions": len(snapshot.get("sessions") or []),
        "tool_calls": len(snapshot.get("tool_calls") or []),
        "process_nodes": len(snapshot.get("process_nodes") or []),
        "audit_events": len(snapshot.get("audit_events") or []),
        "resource_samples": len(snapshot.get("resource_samples") or []),
    }
    lineage = row.get("lineage") or {}
    if lineage:
        if int(lineage.get("orphan_effect_events") or 0) > 0:
            row["lineage_status"] = "partial"
        elif lineage_proc.returncode == 0 and lineage.get("status") != "lineage_smoke_failed":
            row["lineage_status"] = "ok"
        else:
            row["lineage_status"] = "failed"
    elif row.get("status") == "lineage_missing":
        row["lineage_status"] = "missing"
    if row["status"] == "record_ok":
        lineage_status = row.get("lineage_status")
        row["status"] = f"lineage_{lineage_status}" if lineage_status else "lineage_unparsed"
    return row


def aggregate(rows: list[dict[str, Any]]) -> dict[str, Any]:
    totals = Counter()
    join_methods = Counter()
    statuses = Counter(row.get("status", "unknown") for row in rows)
    record_statuses = Counter(row.get("record_status", "unknown") for row in rows)
    lineage_statuses = Counter(row.get("lineage_status", "unknown") for row in rows)
    negative_statuses = Counter()
    for row in rows:
        counts = row.get("snapshot_counts") or {}
        lineage = row.get("lineage") or {}
        pr = row.get("precision_recall") or {}
        totals["sessions"] += int(counts.get("sessions") or 0)
        totals["tool_calls"] += int(counts.get("tool_calls") or 0)
        totals["process_nodes"] += int(counts.get("process_nodes") or 0)
        totals["audit_events"] += int(counts.get("audit_events") or 0)
        totals["effect_events"] += int(lineage.get("effect_events") or 0)
        totals["joined_effect_events"] += int(lineage.get("joined_effect_events") or 0)
        totals["orphan_effect_events"] += int(lineage.get("orphan_effect_events") or 0)
        totals["true_positives"] += int(pr.get("true_positives") or 0)
        totals["false_positives"] += int(pr.get("false_positives") or 0)
        totals["false_negatives"] += int(pr.get("false_negatives") or 0)
        totals["negative_effect_events_observed"] += int(pr.get("negative_effect_events_observed") or 0)
        totals["negative_joined_effect_events"] += int(pr.get("negative_joined_effect_events") or 0)
        negative_statuses[str(pr.get("negative_control_status") or "unknown")] += 1
        join_methods.update(lineage.get("join_methods") or {})
    joined = totals["joined_effect_events"]
    effects = totals["effect_events"]
    precision_den = totals["true_positives"] + totals["false_positives"]
    recall_den = totals["true_positives"] + totals["false_negatives"]
    return {
        "tasks": len(rows),
        "task_statuses": dict(statuses),
        "record_statuses": dict(record_statuses),
        "lineage_statuses": dict(lineage_statuses),
        **dict(totals),
        "raw_join_pct": round(100.0 * joined / effects, 3) if effects else 0.0,
        "precision_pct": round(100.0 * totals["true_positives"] / precision_den, 3) if precision_den else 0.0,
        "recall_pct": round(100.0 * totals["true_positives"] / recall_den, 3) if recall_den else 0.0,
        "negative_control_statuses": dict(negative_statuses),
        "join_methods": dict(join_methods),
    }


def write_markdown(path: Path, result: dict[str, Any]) -> None:
    agg = result["aggregate"]
    lines = [
        "# R114 Live Record Suite",
        "",
        f"Last updated: {date.today().isoformat()}",
        "Stage at update: execute/analyze",
        "Source/command: `python3 docs/visexp/r114_live_record_suite.py --out docs/visexp/out`",
        f"Completeness: {result['status']}",
        "",
        "This suite wraps real `codex exec` tasks with `agentsight record`, runs concurrent",
        "negative-control processes, exports each SQLite DB, and checks lineage precision",
        "and recall from prompt/tool ancestry to process/file/network effects.",
        "",
        "Raw SQLite DBs and exported snapshots stay in the local work dir and are not committed.",
        "",
        "## Aggregate",
        "",
        f"- Tasks: {agg['tasks']} ({agg['task_statuses']})",
        f"- Record status: {agg.get('record_statuses', {})}; lineage status: {agg.get('lineage_statuses', {})}",
        f"- Effects: joined={agg['joined_effect_events']} / {agg['effect_events']} = {agg['raw_join_pct']}%",
        f"- Precision/recall: precision={agg['precision_pct']}%, recall={agg['recall_pct']}%",
        f"- Negative controls: observed={agg['negative_effect_events_observed']}, joined={agg['negative_joined_effect_events']}, statuses={agg['negative_control_statuses']}",
        f"- Join methods: {agg['join_methods']}",
        "",
        "## Per Task",
        "",
        "| Task | Cat | Record | Lineage | Effects | Joined | Orphans | Precision | Recall | Neg observed | Neg joined | Answer |",
        "|------|-----|--------|---------|--------:|-------:|--------:|----------:|-------:|-------------:|-----------:|--------|",
    ]
    for row in result["tasks"]:
        lineage = row.get("lineage") or {}
        pr = row.get("precision_recall") or {}
        answer = str(row.get("answer") or "").replace("|", "\\|").replace("\n", " ")[:80]
        lines.append(
            f"| `{row['task_id']}` | {row.get('category')} | {row.get('record_status')} | {row.get('lineage_status')} | "
            f"{int(lineage.get('effect_events') or 0)} | {int(lineage.get('joined_effect_events') or 0)} | "
            f"{int(lineage.get('orphan_effect_events') or 0)} | {pr.get('precision_pct', 0.0)}% | "
            f"{pr.get('recall_pct', 0.0)}% | {pr.get('negative_effect_events_observed', 0)} | "
            f"{pr.get('negative_joined_effect_events', 0)} | {answer} |"
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


def manifest_rows(tasks: list[Task]) -> list[dict[str, str]]:
    return [
        {
            "task_id": task.task_id,
            "category": task.category,
            "sandbox": task.sandbox,
            "workspace": task.workspace,
            "prompt": task.prompt,
        }
        for task in tasks
    ]


def run(args: argparse.Namespace) -> dict[str, Any]:
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    selected = TASKS[: args.task_limit]
    if args.print_manifest:
        payload = {"schema_version": 1, "run_id": "R114", "tasks": manifest_rows(selected)}
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
    aggregate_result = aggregate(rows)
    pass_lineage = (
        aggregate_result["recall_pct"] >= 95.0
        and aggregate_result["precision_pct"] >= 98.0
        and aggregate_result["negative_joined_effect_events"] == 0
        and aggregate_result["negative_effect_events_observed"] > 0
    )
    if pass_lineage:
        status = "ok"
        boundary = (
            "R114 supports C4 for this fixed task suite: in-scope effects meet the "
            "precision/recall threshold and concurrent negative controls were not attributed."
        )
    else:
        status = "partial"
        boundary = (
            "R114 is partial: exact semantic-effect lineage still needs the recorded "
            "precision/recall and negative-control thresholds before C4 can be widened."
        )
    result = {
        "schema_version": 1,
        "run_id": "R114",
        "status": status,
        "scope": "real_codex_exec_under_agentsight_record_with_negative_controls",
        "artifact_boundary": (
            "Raw SQLite DBs and exported snapshots stay in the local work dir and are not committed; "
            "rerun this suite to reproduce per-event evidence."
        ),
        "generated_at": date.today().isoformat(),
        "work_dir": str(work_dir),
        "agentsight_bin": rel(agentsight_bin),
        "codex_bin": scrub(codex_bin, limit=400),
        "task_limit": args.task_limit,
        "manifest": manifest_rows(selected),
        "aggregate": aggregate_result,
        "tasks": rows,
        "boundary": boundary,
    }
    json_path = out_dir / "live-record-r114.json"
    md_path = out_dir / "live-record-r114.md"
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
    parser.add_argument("--task-limit", type=int, default=20)
    parser.add_argument("--timeout", type=int, default=240)
    parser.add_argument("--negative-mode", choices=("wrapper", "external"), default="wrapper")
    parser.add_argument("--print-manifest", action="store_true", help="print the fixed task manifest without running agents")
    return parser


if __name__ == "__main__":
    run(build_parser().parse_args())
