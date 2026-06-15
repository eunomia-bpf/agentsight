#!/usr/bin/env python3
"""Run R113 live record tasks and summarize capture-time lineage evidence.

The harness intentionally uses real `agentsight record -- codex exec ...`
commands. It creates new local Codex session logs as a side effect of running
Codex, but it never modifies or deletes existing agent traces.
"""

from __future__ import annotations

import argparse
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
DEFAULT_WORK = Path("/tmp/agentsight-r113-live")
WORK_MARKER = ".agentsight-r113-live"


@dataclass(frozen=True)
class Task:
    task_id: str
    prompt: str


TASKS = [
    Task(
        "codex-count-r113",
        "Read docs/visexp/out/capture-time-r113.md. Answer exactly one line: "
        "r113_boundary=<implementation|live>. Do not modify files.",
    ),
    Task(
        "codex-find-next",
        "Read docs/visexp/STATE.md. Answer exactly one line naming the next "
        "R113 action after 'Next action:'. Do not modify files.",
    ),
    Task(
        "codex-claim-c4",
        "Read docs/visexp/CLAIM_VERDICT.md. Answer exactly one line with the "
        "current C4 verdict word. Do not modify files.",
    ),
    Task(
        "codex-rg-baseline",
        "Using read-only commands, count lines mentioning 'baseline' in "
        "docs/visexp/EXPERIMENT_PLAN.md. Answer exactly one line: baseline_lines=<n>. "
        "Do not modify files.",
    ),
    Task(
        "codex-paper-boundary",
        "Read docs/visexp/paper/main.tex and answer exactly one line: "
        "mentions_r113=<yes|no>. Do not modify files.",
    ),
]


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


def failure_tail(proc: subprocess.CompletedProcess[str]) -> dict[str, str]:
    if proc.returncode == 0:
        return {}
    return {
        "stdout_tail": scrub(proc.stdout),
        "stderr_tail": scrub(proc.stderr),
    }


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
    (work_dir / WORK_MARKER).write_text("owned by docs/visexp/r113_live_record_harness.py\n", encoding="utf-8")


def task_command(task: Task, work_dir: Path, codex_bin: str) -> list[str]:
    answer_path = work_dir / f"{task.task_id}.answer.txt"
    return [
        codex_bin,
        "exec",
        "--sandbox",
        "read-only",
        "--cd",
        str(REPO_ROOT),
        "--output-last-message",
        str(answer_path),
        task.prompt,
    ]


def record_task(
    task: Task,
    agentsight_bin: Path,
    codex_bin: str,
    work_dir: Path,
    timeout_s: int,
) -> dict[str, Any]:
    task_dir = work_dir / task.task_id
    task_dir.mkdir(parents=True, exist_ok=True)
    db_path = task_dir / f"{task.task_id}.db"
    snapshot_path = task_dir / f"{task.task_id}.snapshot.json"
    lineage_dir = task_dir / "lineage"
    answer_path = work_dir / f"{task.task_id}.answer.txt"
    record_cmd = [
        str(agentsight_bin),
        "record",
        "--no-server",
        "--db",
        str(db_path),
        "--",
        *task_command(task, work_dir, codex_bin),
    ]

    started = time.time()
    try:
        record_proc = run_cmd(record_cmd, REPO_ROOT, timeout_s)
    except subprocess.TimeoutExpired as error:
        return {
            "task_id": task.task_id,
            "status": "timeout",
            "duration_seconds": round(time.time() - started, 3),
            "db": str(db_path),
            "record_returncode": None,
            "stdout_tail": scrub(error.stdout or ""),
            "stderr_tail": scrub(error.stderr or ""),
        }
    duration = round(time.time() - started, 3)
    row: dict[str, Any] = {
        "task_id": task.task_id,
        "status": "record_failed" if record_proc.returncode else "record_ok",
        "record_status": "failed" if record_proc.returncode else "ok",
        "duration_seconds": duration,
        "db": str(db_path),
        "record_returncode": record_proc.returncode,
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
            "20000",
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

    snapshot = read_json(snapshot_path)
    sessions = snapshot.get("sessions") or []
    tools = snapshot.get("tool_calls") or []
    record_tools = [
        tool
        for tool in tools
        if tool.get("view_source") == "record_capture_time_agent_envelope"
    ]
    row["snapshot_counts"] = {
        "sessions": len(sessions),
        "tool_calls": len(tools),
        "process_nodes": len(snapshot.get("process_nodes") or []),
        "audit_events": len(snapshot.get("audit_events") or []),
        "resource_samples": len(snapshot.get("resource_samples") or []),
    }
    row["record_envelope"] = {
        "sessions": sum(
            1
            for session in sessions
            if session.get("view_source") == "record_capture_time_agent_envelope"
        ),
        "tool_calls": sum(
            1
            for tool in record_tools
        ),
        "completed_tool_calls": sum(
            1 for tool in record_tools if tool.get("status") == "completed"
        ),
        "related_pid_tool_calls": sum(
            1 for tool in record_tools if tool.get("related_pid") is not None
        ),
    }
    if row["status"] == "record_ok":
        lineage_status = row.get("lineage_status")
        row["status"] = f"lineage_{lineage_status}" if lineage_status else "lineage_unparsed"
    return row


def aggregate(rows: list[dict[str, Any]]) -> dict[str, Any]:
    totals = Counter()
    join_methods = Counter()
    orphan_reasons = Counter()
    statuses = Counter(row.get("status", "unknown") for row in rows)
    record_statuses = Counter(row.get("record_status", "unknown") for row in rows)
    lineage_statuses = Counter(row.get("lineage_status", "unknown") for row in rows)
    for row in rows:
        counts = row.get("snapshot_counts") or {}
        envelope = row.get("record_envelope") or {}
        lineage = row.get("lineage") or {}
        totals["sessions"] += int(counts.get("sessions") or 0)
        totals["tool_calls"] += int(counts.get("tool_calls") or 0)
        totals["record_envelope_sessions"] += int(envelope.get("sessions") or 0)
        totals["record_envelope_tool_calls"] += int(envelope.get("tool_calls") or 0)
        totals["completed_record_tool_calls"] += int(envelope.get("completed_tool_calls") or 0)
        totals["related_pid_record_tool_calls"] += int(envelope.get("related_pid_tool_calls") or 0)
        totals["process_nodes"] += int(counts.get("process_nodes") or 0)
        totals["audit_events"] += int(counts.get("audit_events") or 0)
        totals["effect_events"] += int(lineage.get("effect_events") or 0)
        totals["joined_effect_events"] += int(lineage.get("joined_effect_events") or 0)
        totals["orphan_effect_events"] += int(lineage.get("orphan_effect_events") or 0)
        join_methods.update(lineage.get("join_methods") or {})
        orphan_reasons.update(lineage.get("orphan_reasons") or {})
    effect_events = totals["effect_events"]
    joined = totals["joined_effect_events"]
    return {
        "tasks": len(rows),
        "task_statuses": dict(statuses),
        "record_statuses": dict(record_statuses),
        "lineage_statuses": dict(lineage_statuses),
        **dict(totals),
        "raw_join_pct": round(100.0 * joined / effect_events, 3) if effect_events else 0.0,
        "join_methods": dict(join_methods),
        "orphan_reasons": dict(orphan_reasons),
    }


def write_markdown(path: Path, result: dict[str, Any]) -> None:
    agg = result["aggregate"]
    completeness = "passed for this smoke" if agg.get("orphan_effect_events") == 0 else "partial"
    if agg.get("orphan_effect_events") == 0:
        boundary = [
            "R113-live proves that command-mode `record` creates capture-time session/tool rows",
            "around real Codex agent tasks and that the exported process/file/network effects",
            "inherit the agent-run envelope in this five-task smoke. This does not yet prove",
            "full-history exact lineage, cross-repository robustness, user utility, or tag adequacy.",
        ]
    else:
        boundary = [
            "R113-live proves that command-mode `record` creates capture-time session/tool rows",
            "around real Codex agent tasks. It does not yet prove complete C4 lineage: short-lived",
            "Codex helper processes can still lack enough persisted process ancestry to join to the",
            "agent-run tool. This is negative evidence for the next collector change, not a visualization",
            "problem.",
        ]
    lines = [
        "# R113 Live Record Harness",
        "",
        f"Last updated: {date.today().isoformat()}",
        "Stage at update: execute/analyze",
        "Source/command: `python3 docs/visexp/r113_live_record_harness.py --out docs/visexp/out`",
        f"Completeness: {completeness}",
        "",
        "This run wraps real `codex exec` tasks with `agentsight record`, exports each SQLite DB,",
        "and checks whether process/file/network effects inherit the capture-time agent-run envelope.",
        "Raw SQLite DBs and exported snapshots stay in the local work dir and are not committed;",
        "rerun this harness to reproduce per-event evidence.",
        "",
        "## Aggregate",
        "",
        f"- Tasks: {agg['tasks']} ({agg['task_statuses']})",
        f"- Record status: {agg.get('record_statuses', {})}; lineage status: {agg.get('lineage_statuses', {})}",
        f"- Record-envelope rows: sessions={agg['record_envelope_sessions']}, tool_calls={agg['record_envelope_tool_calls']}, completed_tools={agg['completed_record_tool_calls']}",
        f"- Effects: joined={agg['joined_effect_events']} / {agg['effect_events']} = {agg['raw_join_pct']}%",
        f"- Orphans: {agg['orphan_effect_events']} {agg['orphan_reasons']}",
        f"- Join methods: {agg['join_methods']}",
        "",
        "## Per Task",
        "",
        "| Task | Record | Lineage | Sessions | Tools | Effects | Joined | Orphans | Join | Answer |",
        "|------|--------|---------|---------:|------:|--------:|-------:|--------:|-----:|--------|",
    ]
    for row in result["tasks"]:
        counts = row.get("snapshot_counts") or {}
        lineage = row.get("lineage") or {}
        effects = int(lineage.get("effect_events") or 0)
        joined = int(lineage.get("joined_effect_events") or 0)
        orphans = int(lineage.get("orphan_effect_events") or 0)
        join_pct = round(100.0 * joined / effects, 3) if effects else 0.0
        answer = str(row.get("answer") or "").replace("|", "\\|").replace("\n", " ")[:80]
        lines.append(
            f"| `{row['task_id']}` | {row.get('record_status')} | {row.get('lineage_status')} | {counts.get('sessions', 0)} | "
            f"{counts.get('tool_calls', 0)} | {effects} | {joined} | {orphans} | "
            f"{join_pct}% | {answer} |"
        )
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            *boundary,
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run(args: argparse.Namespace) -> dict[str, Any]:
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    work_dir = Path(args.work_dir)
    prepare_work_dir(work_dir)

    agentsight_bin = Path(resolve_executable(args.agentsight_bin, "agentsight"))
    codex_bin = resolve_executable(args.codex_bin, "codex")
    selected = TASKS[: args.task_limit]
    rows = [record_task(task, agentsight_bin, codex_bin, work_dir, args.timeout) for task in selected]
    aggregate_result = aggregate(rows)
    if aggregate_result.get("orphan_effect_events") == 0:
        boundary = (
            "Real Codex agent runs are captured with record-time session/tool envelopes, "
            "and all raw effects in this smoke inherit the agent-run tool through process-family "
            "or root-pid ancestry. Broader full-history and user-task evidence remains required."
        )
    else:
        boundary = (
            "Real Codex agent runs are captured with record-time session/tool envelopes. "
            "Remaining orphan effects indicate incomplete process ancestry for short-lived helper "
            "processes, so C4 remains partial."
        )
    result = {
        "schema_version": 1,
        "run_id": "R113-live",
        "status": "partial" if any((row.get("lineage") or {}).get("orphan_effect_events") for row in rows) else "ok",
        "scope": "real_codex_exec_under_agentsight_record",
        "artifact_boundary": (
            "Raw SQLite DBs and exported snapshots stay in the local work dir and are not committed; "
            "rerun this harness to reproduce per-event evidence."
        ),
        "generated_at": date.today().isoformat(),
        "work_dir": str(work_dir),
        "agentsight_bin": rel(agentsight_bin),
        "codex_bin": scrub(codex_bin, limit=400),
        "task_limit": args.task_limit,
        "aggregate": aggregate_result,
        "tasks": rows,
        "boundary": boundary,
    }
    json_path = out_dir / "live-record-r113.json"
    md_path = out_dir / "live-record-r113.md"
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
    parser.add_argument("--task-limit", type=int, default=5)
    parser.add_argument("--timeout", type=int, default=240)
    return parser


if __name__ == "__main__":
    run(build_parser().parse_args())
