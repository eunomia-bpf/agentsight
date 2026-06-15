#!/usr/bin/env python3
"""Summarize R114 child-depth, specificity, and redaction evidence."""

from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter
from datetime import date
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_RESULT = SCRIPT_DIR / "out" / "live-record-r114.json"
DEFAULT_OUT = SCRIPT_DIR / "out"
REPO_ROOT = SCRIPT_DIR.parents[1]


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def row_joined(row: dict[str, str]) -> bool:
    return str(row.get("joined", "")).lower() in {"true", "1", "yes"}


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT.resolve()))
    except Exception:
        return str(path)


def scrub_value(value: Any) -> str:
    text = str(value or "unknown")
    home = Path.home()
    text = text.replace(str(home), "$HOME")
    text = text.replace(f"home/{home.name}", "$HOME")
    return text


def event_text(event: dict[str, Any]) -> str:
    return "\n".join(
        [
            str(event.get("id") or ""),
            str(event.get("target") or ""),
            str(event.get("summary") or ""),
            str(event.get("details") or ""),
        ]
    )


def process_interval_overlaps(left: dict[str, Any], right: dict[str, Any]) -> bool:
    left_start = left.get("start_timestamp_ms")
    left_end = left.get("end_timestamp_ms")
    right_start = right.get("start_timestamp_ms")
    right_end = right.get("end_timestamp_ms")
    if left_end is not None and right_start is not None and int(left_end) < int(right_start):
        return False
    if right_end is not None and left_start is not None and int(right_end) < int(left_start):
        return False
    return True


def process_indexes(snapshot: dict[str, Any]) -> tuple[dict[str, dict[str, Any]], dict[int, list[dict[str, Any]]]]:
    by_id: dict[str, dict[str, Any]] = {}
    by_pid: dict[int, list[dict[str, Any]]] = {}
    for process in snapshot.get("process_nodes") or []:
        if process.get("id"):
            by_id[str(process["id"])] = process
        if process.get("pid") is not None:
            by_pid.setdefault(int(process["pid"]), []).append(process)
    return by_id, by_pid


def parent_process(process: dict[str, Any], by_pid: dict[int, list[dict[str, Any]]]) -> dict[str, Any] | None:
    if process.get("ppid") is None:
        return None
    for candidate in by_pid.get(int(process["ppid"]), []):
        if process_interval_overlaps(candidate, process):
            return candidate
    return None


def related_pid(snapshot: dict[str, Any]) -> int | None:
    for tool in snapshot.get("tool_calls") or []:
        if tool.get("view_source") == "record_capture_time_agent_envelope" and tool.get("related_pid") is not None:
            return int(tool["related_pid"])
    for tool in snapshot.get("tool_calls") or []:
        if tool.get("related_pid") is not None:
            return int(tool["related_pid"])
    return None


def process_depth(process_id: str, snapshot: dict[str, Any], root_pid: int | None) -> int | None:
    if root_pid is None:
        return None
    by_id, by_pid = process_indexes(snapshot)
    process = by_id.get(process_id)
    if not process:
        return None
    depth = 0
    seen: set[str] = set()
    while process:
        current_id = str(process.get("id") or "")
        if current_id in seen:
            return None
        seen.add(current_id)
        if process.get("pid") is not None and int(process["pid"]) == root_pid:
            return depth
        if process.get("ppid") is not None and int(process["ppid"]) == root_pid:
            return depth + 1
        process = parent_process(process, by_pid)
        depth += 1
    return None


def negative_event_ids(snapshot: dict[str, Any], markers: list[str]) -> set[str]:
    return {
        str(event.get("id"))
        for event in snapshot.get("audit_events") or []
        if event.get("id") and any(marker in event_text(event) for marker in markers)
    }


def redaction_summary(paths: list[Path]) -> dict[str, Any]:
    home = str(Path.home())
    home_fragment = f"home/{Path.home().name}"
    secret_re = re.compile(r"\b(?:sk|ghp|hf)_[A-Za-z0-9_]{16,}|\bsk-[A-Za-z0-9]{20,}")
    home_hits = 0
    secret_hits = 0
    scanned = 0
    for path in paths:
        if not path.exists():
            continue
        scanned += 1
        text = path.read_text(encoding="utf-8", errors="replace")
        home_hits += text.count(home)
        home_hits += text.count(home_fragment)
        secret_hits += len(secret_re.findall(text))
    return {
        "files_scanned": scanned,
        "home_path_occurrences": home_hits,
        "secret_pattern_occurrences": secret_hits,
        "status": "ok" if home_hits == 0 and secret_hits == 0 else "needs_review",
    }


def top(counter: Counter[str], limit: int = 10) -> list[dict[str, Any]]:
    return [{"value": value, "count": count} for value, count in counter.most_common(limit)]


def analyze(result: dict[str, Any], committed_paths: list[Path]) -> dict[str, Any]:
    depth_counts: Counter[str] = Counter()
    joined_processes: Counter[str] = Counter()
    joined_targets: Counter[str] = Counter()
    joined_effects: Counter[str] = Counter()
    orphan_targets: Counter[str] = Counter()
    orphan_processes: Counter[str] = Counter()
    per_task = []
    for task in result.get("tasks") or []:
        snapshot_path = Path(str(task.get("snapshot") or ""))
        db_path = Path(str(task.get("db") or ""))
        lineage_path = db_path.parent / "lineage" / "effect-lineage.csv"
        if not snapshot_path.exists():
            continue
        snapshot = read_json(snapshot_path)
        rows = read_csv(lineage_path)
        control = task.get("negative_control") or {}
        negative_ids = negative_event_ids(
            snapshot,
            [str(control.get("marker") or ""), str(control.get("negative_dir") or ""), str(control.get("sibling_dir") or "")],
        )
        root_pid = related_pid(snapshot)
        task_depths: Counter[str] = Counter()
        for row in rows:
            if row_joined(row):
                depth = process_depth(str(row.get("process_id") or ""), snapshot, root_pid)
                depth_key = "unknown" if depth is None else str(depth)
                depth_counts[depth_key] += 1
                task_depths[depth_key] += 1
                joined_processes[scrub_value(row.get("process_comm"))] += 1
                joined_targets[scrub_value(row.get("target_group"))] += 1
                joined_effects[scrub_value(row.get("effect"))] += 1
            elif str(row.get("event_id") or "") not in negative_ids:
                orphan_targets[scrub_value(row.get("target_group"))] += 1
                orphan_processes[scrub_value(row.get("process_comm"))] += 1
        per_task.append(
            {
                "task_id": task.get("task_id"),
                "target_status": task.get("target_status"),
                "lineage_status": task.get("lineage_status"),
                "joined_depths": dict(task_depths),
                "negative_observed": (task.get("precision_recall") or {}).get("negative_effect_events_observed", 0),
            }
        )
    return {
        "schema_version": 1,
        "run_id": "R114-analysis",
        "generated_at": date.today().isoformat(),
        "source": rel(DEFAULT_RESULT),
        "aggregate": result.get("aggregate") or {},
        "child_depth_distribution": dict(depth_counts),
        "top_joined_processes": top(joined_processes),
        "top_joined_targets": top(joined_targets),
        "top_joined_effects": top(joined_effects),
        "top_out_of_scope_targets": top(orphan_targets),
        "top_out_of_scope_processes": top(orphan_processes),
        "per_task": per_task,
        "redaction": redaction_summary(committed_paths),
    }


def table(rows: list[dict[str, Any]], value_header: str) -> list[str]:
    lines = [f"| {value_header} | Count |", "|---|---:|"]
    for row in rows:
        lines.append(f"| `{row['value']}` | {row['count']} |")
    return lines


def write_markdown(path: Path, result: dict[str, Any]) -> None:
    agg = result["aggregate"]
    lines = [
        "# R114 Lineage Analysis",
        "",
        f"Last updated: {result['generated_at']}",
        f"Source: `{result['source']}`",
        "",
        "## Gate Summary",
        "",
        f"- Tasks: {agg.get('tasks')} target_statuses={agg.get('target_statuses')}",
        f"- In-scope effects: {agg.get('in_scope_effect_events')}; precision={agg.get('precision_pct')}%; recall={agg.get('recall_pct')}%",
        f"- Negative controls: tasks_observed={agg.get('negative_control_tasks_observed')}/{agg.get('tasks')}, observed={agg.get('negative_effect_events_observed')}, joined={agg.get('negative_joined_effect_events')}",
        f"- Raw join: {agg.get('joined_effect_events')} / {agg.get('effect_events')} = {agg.get('raw_join_pct')}%",
        f"- Redaction: {result['redaction']}",
        "",
        "## Child Depth",
        "",
        "| Depth from related agent pid | Joined effects |",
        "|---:|---:|",
    ]
    for depth, count in sorted(result["child_depth_distribution"].items(), key=lambda item: (item[0] == "unknown", int(item[0]) if item[0].isdigit() else 999)):
        lines.append(f"| {depth} | {count} |")
    lines.extend(["", "## Joined Process Commands", "", *table(result["top_joined_processes"], "Process")])
    lines.extend(["", "## Joined Effect Targets", "", *table(result["top_joined_targets"], "Target group")])
    lines.extend(["", "## Joined Effects", "", *table(result["top_joined_effects"], "Effect")])
    lines.extend(["", "## Out-of-Scope Targets", "", *table(result["top_out_of_scope_targets"], "Target group")])
    lines.extend(["", "## Out-of-Scope Processes", "", *table(result["top_out_of_scope_processes"], "Process")])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run(args: argparse.Namespace) -> dict[str, Any]:
    result_path = Path(args.result)
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    committed_paths = [
        result_path,
        result_path.with_suffix(".md"),
        out_dir / "live-record-r114-smoke.json",
        out_dir / "live-record-r114-smoke.md",
    ]
    result = analyze(read_json(result_path), committed_paths)
    json_path = out_dir / "live-record-r114-analysis.json"
    md_path = out_dir / "live-record-r114-analysis.md"
    committed_paths.extend([json_path, md_path])
    result["redaction"] = redaction_summary(committed_paths)
    json_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    write_markdown(md_path, result)
    print(json.dumps({"status": result["redaction"]["status"], "aggregate": result["aggregate"]}, indent=2))
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--result", default=str(DEFAULT_RESULT))
    parser.add_argument("--out", default=str(DEFAULT_OUT))
    run(parser.parse_args())


if __name__ == "__main__":
    main()
