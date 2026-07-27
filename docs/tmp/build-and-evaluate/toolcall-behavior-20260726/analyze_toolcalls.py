#!/usr/bin/env python3
"""Full descriptive analysis of Agent tool-call behavior.

The script consumes the frozen per-project event exports under rq1-raw/events.
When the source_file paths embedded in those exports are still readable, it
also reconstructs native multi-call assistant batches. All primary sequence
statistics remain source-stream-local so concurrently interleaved subagents do
not create artificial tool transitions.

Only Python's standard library is required.
"""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
import math
import os
import re
import statistics
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable, Sequence


ALL = "ALL"
FAIL_STATUSES = {"fail"}
DECISIVE_STATUSES = {"ok", "fail"}
MUTATION_ACCESSES = {"write", "create", "delete", "rename", "rename_from"}


def parse_args() -> argparse.Namespace:
    here = Path(__file__).resolve().parent
    default_events = (
        here.parent
        / "rq1-rq4-recompute-final"
        / "rq1-raw"
        / "events"
    )
    parser = argparse.ArgumentParser()
    parser.add_argument("--events-dir", type=Path, default=default_events)
    parser.add_argument("--output-dir", type=Path, default=here)
    parser.add_argument(
        "--no-native-batches",
        action="store_true",
        help="Do not inspect source_file paths to reconstruct native call batches.",
    )
    return parser.parse_args()


def percentile(values: Sequence[float], q: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    if len(ordered) == 1:
        return float(ordered[0])
    pos = (len(ordered) - 1) * q
    lo = math.floor(pos)
    hi = math.ceil(pos)
    if lo == hi:
        return float(ordered[lo])
    return float(ordered[lo] * (hi - pos) + ordered[hi] * (pos - lo))


def safe_div(num: float, den: float) -> float | None:
    return num / den if den else None


def fmt_int(value: Any) -> str:
    if value is None or value == "":
        return "N/A"
    return f"{int(round(float(value))):,}"


def fmt_float(value: Any, digits: int = 2) -> str:
    if value is None or value == "":
        return "N/A"
    return f"{float(value):.{digits}f}"


def fmt_pct(value: Any, digits: int = 1) -> str:
    if value is None or value == "":
        return "N/A"
    return f"{100 * float(value):.{digits}f}%"


def entropy(labels: Sequence[str]) -> float:
    if not labels:
        return 0.0
    counts = Counter(labels)
    total = len(labels)
    return -sum((n / total) * math.log2(n / total) for n in counts.values())


def gini(values: Sequence[float]) -> float | None:
    clean = sorted(float(v) for v in values if v >= 0)
    if not clean or sum(clean) == 0:
        return None
    n = len(clean)
    weighted = sum((i + 1) * value for i, value in enumerate(clean))
    return (2 * weighted) / (n * sum(clean)) - (n + 1) / n


def top_fraction_share(values: Sequence[int], fraction: float) -> float | None:
    if not values or sum(values) == 0:
        return None
    take = max(1, math.ceil(len(values) * fraction))
    return sum(sorted(values, reverse=True)[:take]) / sum(values)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def discover_event_files(events_dir: Path) -> list[Path]:
    selected: dict[str, Path] = {}
    for path in sorted(events_dir.glob("*.json")):
        selected[path.name] = path
    for path in sorted(events_dir.glob("*.json.gz")):
        logical = path.name[:-3]
        if logical not in selected:
            selected[logical] = path
    if not selected:
        raise FileNotFoundError(f"No .json or .json.gz files found in {events_dir}")
    return [selected[key] for key in sorted(selected)]


def load_json(path: Path) -> dict[str, Any]:
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rt", encoding="utf-8") as handle:
        return json.load(handle)


def tool_family(event: dict[str, Any]) -> str:
    name = str(event.get("tool_name") or "")
    low = name.lower()
    category = str(event.get("category") or "").lower()

    if category == "shell" or low in {"bash", "exec", "exec_command", "run_shell_command", "bash"}:
        return "shell"
    if low in {"read", "read_file"}:
        return "read"
    if low in {"write", "write_file"}:
        return "write"
    if low in {"edit", "apply_patch"}:
        return "edit"
    if low == "toolsearch":
        return "tool discovery"
    if low in {"grep", "glob", "grep_search", "websearch"}:
        return "search"
    if low in {"webfetch", "_fetch"}:
        return "fetch"
    if (
        category == "subagent"
        or low
        in {
            "agent",
            "spawn_agent",
            "taskcreate",
            "taskupdate",
            "taskstop",
            "close_agent",
            "resume_agent",
        }
    ):
        if low in {
            "wait_agent",
            "send_message",
            "followup_task",
            "interrupt_agent",
            "list_agents",
            "sendmessage",
            "close_agent",
            "resume_agent",
        }:
            return "coordination"
        return "task"
    if low in {
        "wait_agent",
        "send_message",
        "followup_task",
        "interrupt_agent",
        "list_agents",
        "sendmessage",
        "close_agent",
        "resume_agent",
    }:
        return "coordination"
    if low in {
        "wait",
        "write_stdin",
        "send_input",
        "monitor",
        "read_thread_terminal",
    }:
        return "wait/control"
    if category == "plan" or low in {
        "update_plan",
        "todowrite",
        "enterplanmode",
        "exitplanmode",
        "create_goal",
        "update_goal",
        "get_goal",
    }:
        return "plan/goal"
    if low == "skill":
        return "skill"
    if low in {"view_image", "senduserfile"}:
        return "multimodal"
    if category == "network":
        return "network/other"
    return "other"


SHELL_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    (
        "lint/format",
        re.compile(
            r"(?i)(?:\bcargo\s+(?:fmt|clippy)\b|\bnpm\s+run\s+lint\b|"
            r"\bpnpm\s+(?:run\s+)?lint\b|\byarn\s+(?:run\s+)?lint\b|"
            r"\b(?:ruff|black|prettier|eslint|rustfmt|clang-format)\b)"
        ),
    ),
    (
        "test",
        re.compile(
            r"(?i)(?:\bcargo\s+(?:nextest|test)\b|\bpytest\b|\bpy\.test\b|"
            r"\bgo\s+test\b|\bctest\b|\bnpm\s+(?:run\s+)?test\b|"
            r"\bpnpm\s+(?:run\s+)?test\b|\byarn\s+(?:run\s+)?test\b|"
            r"\bmake\s+(?:[^;&|]*\s)?test\b|\bjest\b|\bvitest\b|"
            r"\b(?:python|python3)\s+-m\s+unittest\b|"
            r"\b(?:python|python3)\s+(?:\S*/)?test_[A-Za-z0-9_.-]+\b|"
            r"(?:^|[;&|]\s*)(?:\./|bash\s+)(?:\S*/)?test_[A-Za-z0-9_.-]+\b)"
        ),
    ),
    (
        "build/check",
        re.compile(
            r"(?i)(?:\bcargo\s+(?:build|check)\b|\bnpm\s+run\s+build\b|"
            r"\bpnpm\s+(?:run\s+)?build\b|\byarn\s+(?:run\s+)?build\b|"
            r"\bmake(?:\s|$)|\bcmake\b|\bninja\b|\bmeson\b|"
            r"\bgcc\b|\bg\+\+\b|\bclang\b|\brustc\b|\btsc\b)"
        ),
    ),
    ("container/orchestration", re.compile(r"(?i)\b(?:docker|podman|kubectl|crictl|helm)\b")),
    (
        "package/dependency",
        re.compile(
            r"(?i)(?:\b(?:npm|pnpm|yarn)\s+(?:install|add|remove|update|ci)\b|"
            r"\b(?:pip|pip3|uv)\s+(?:install|add|remove|sync)\b|"
            r"\bcargo\s+(?:install|add|remove|update|fetch)\b|"
            r"\bapt(?:-get)?\b|\bbrew\b)"
        ),
    ),
    ("git/repository", re.compile(r"(?i)(?:^|[\s;&|({])(?:git|gh)(?:\s|$)")),
    (
        "network/remote",
        re.compile(r"(?i)(?:^|[\s;&|({])(?:curl|wget|ssh|scp|rsync)(?:\s|$)"),
    ),
    (
        "search/text",
        re.compile(
            r"(?i)(?:^|[\s;&|({])(?:rg|grep|egrep|fgrep|find|fd|sed|awk|jq|"
            r"head|tail|wc|sort|uniq|cut|tr|diff|comm|xargs|nl|less|more|strings)"
            r"(?:\s|$)"
        ),
    ),
    (
        "filesystem/navigation",
        re.compile(
            r"(?i)(?:^|[\s;&|({])(?:ls|pwd|cat|stat|realpath|readlink|dirname|"
            r"basename|cp|mv|rm|mkdir|touch|chmod|chown|ln)(?:\s|$)"
        ),
    ),
    (
        "data/analysis/runtime",
        re.compile(
            r"(?i)(?:^|[\s;&|({])(?:python|python3|Rscript|jupyter|node|deno|"
            r"ruby|perl|sqlite3)(?:\s|$)"
        ),
    ),
    (
        "process/system",
        re.compile(
            r"(?i)(?:^|[\s;&|({])(?:ps|pgrep|pkill|kill|lsof|top|htop|uname|"
            r"env|printenv|which|whereis|timeout|sleep|time|date|df|du|free)(?:\s|$)"
        ),
    ),
]

COMMAND_NAME_HINTS = {
    **{
        name: "search/text"
        for name in (
            "rg",
            "grep",
            "egrep",
            "fgrep",
            "find",
            "fd",
            "sed",
            "awk",
            "jq",
            "head",
            "tail",
            "wc",
            "sort",
            "uniq",
            "cut",
            "tr",
            "diff",
            "comm",
            "xargs",
            "nl",
            "less",
            "more",
            "strings",
        )
    },
    **{
        name: "filesystem/navigation"
        for name in (
            "ls",
            "pwd",
            "cat",
            "stat",
            "realpath",
            "readlink",
            "dirname",
            "basename",
            "cp",
            "mv",
            "rm",
            "mkdir",
            "touch",
            "chmod",
            "chown",
            "ln",
            "cd",
        )
    },
    "git": "git/repository",
    "gh": "git/repository",
    "docker": "container/orchestration",
    "podman": "container/orchestration",
    "kubectl": "container/orchestration",
    "crictl": "container/orchestration",
    "helm": "container/orchestration",
    "curl": "network/remote",
    "wget": "network/remote",
    "ssh": "network/remote",
    "scp": "network/remote",
    "rsync": "network/remote",
    "ps": "process/system",
    "pgrep": "process/system",
    "pkill": "process/system",
    "kill": "process/system",
    "lsof": "process/system",
    "top": "process/system",
    "htop": "process/system",
    "uname": "process/system",
    "env": "process/system",
    "printenv": "process/system",
    "which": "process/system",
    "whereis": "process/system",
    "timeout": "process/system",
    "sleep": "process/system",
    "date": "process/system",
}


def shell_labels(command: str, command_name: str = "") -> list[str]:
    labels = [label for label, pattern in SHELL_PATTERNS if pattern.search(command)]
    hint = COMMAND_NAME_HINTS.get(command_name.lower())
    if hint:
        labels = [hint, *[label for label in labels if label != hint]]
    return labels or ["other"]


def shell_primary(command: str, command_name: str = "") -> str:
    return shell_labels(command, command_name)[0]


def event_paths(event: dict[str, Any]) -> set[tuple[str, str]]:
    result: set[tuple[str, str]] = set()
    for action in event.get("actions") or []:
        path = action.get("path")
        if path:
            result.add((str(action.get("worktree_id") or event.get("worktree_id") or ""), str(path)))
    for source_path in event.get("source_paths") or []:
        path = source_path.get("path")
        if path:
            result.add((str(event.get("worktree_id") or ""), str(path)))
    return result


def event_artifact_ids(event: dict[str, Any]) -> set[tuple[str, str]]:
    result: set[tuple[str, str]] = set()
    for action in event.get("actions") or []:
        artifact_id = action.get("artifact_id")
        if artifact_id:
            result.add(
                (
                    str(action.get("worktree_id") or event.get("worktree_id") or ""),
                    str(artifact_id),
                )
            )
    return result


def event_sort_key(event: dict[str, Any]) -> tuple[int, int, str]:
    return (
        int(event.get("ts_ms") or 0),
        int(event.get("source_tool_ordinal") or 0),
        str(event.get("id") or ""),
    )


def stratum_keys(project: str, vendor: str) -> list[tuple[str, str]]:
    return [(ALL, ALL), (project, ALL), (ALL, vendor), (project, vendor)]


def stratum_type(project: str, vendor: str) -> str:
    if project == ALL and vendor == ALL:
        return "overall"
    if project != ALL and vendor == ALL:
        return "project"
    if project == ALL and vendor != ALL:
        return "vendor"
    return "project_vendor"


def with_stratum(project: str, vendor: str) -> dict[str, str]:
    return {
        "stratum_type": stratum_type(project, vendor),
        "project": project,
        "vendor": vendor,
    }


def normalize_command(command: str) -> str:
    return " ".join(command.split())


def same_command_text(a: dict[str, Any], b: dict[str, Any]) -> bool:
    return (
        str(a.get("command") or "") != ""
        and str(a.get("command") or "") == str(b.get("command") or "")
    )


def same_command(a: dict[str, Any], b: dict[str, Any]) -> bool:
    return (
        a.get("tool_name") == b.get("tool_name")
        and same_command_text(a, b)
    )


def summarize_numeric(values: Sequence[float], prefix: str = "") -> dict[str, Any]:
    return {
        f"{prefix}n": len(values),
        f"{prefix}mean": statistics.fmean(values) if values else None,
        f"{prefix}p50": percentile(values, 0.50),
        f"{prefix}p90": percentile(values, 0.90),
        f"{prefix}p95": percentile(values, 0.95),
        f"{prefix}p99": percentile(values, 0.99),
        f"{prefix}max": max(values) if values else None,
    }


def classify_adjacent_dependency(prev: dict[str, Any], nxt: dict[str, Any]) -> tuple[str, str]:
    if prev.get("status") == "fail" and same_command(prev, nxt):
        return "dependency_cue", "exact_retry_after_failure"
    if (
        prev["_family"] in {"shell", "task"}
        and nxt["_family"] in {"wait/control", "coordination"}
    ):
        return "dependency_cue", "control_or_wait_handoff"
    if (
        prev["_family"] in {"edit", "write"}
        and nxt["_family"] == "shell"
        and nxt["_shell_primary"] in {"test", "build/check", "lint/format"}
    ):
        return "dependency_cue", "edit_then_validation"
    if prev["_artifact_ids"] & nxt["_artifact_ids"]:
        return "observed_overlap", "shared_artifact_identity"
    if prev["_paths"] & nxt["_paths"]:
        return "observed_overlap", "shared_exact_path"
    if prev["_paths"] and nxt["_paths"]:
        return "observed_disjoint", "disjoint_observed_paths"
    return "unknown", "insufficient_observable_evidence"


def reconstruct_native_batches(
    events: list[dict[str, Any]], enabled: bool
) -> tuple[dict[int, str], dict[str, Any]]:
    """Map event list indices to native assistant-call batch identifiers."""
    event_batch: dict[int, str] = {}
    coverage = Counter()

    # Claude exports retain the assistant JSONL event UUID. Multiple tool_use
    # blocks from one assistant message therefore share this key.
    for idx, event in enumerate(events):
        if event["vendor"] == "claude" and event.get("source_event_id"):
            event_batch[idx] = (
                f"{event['_project']}|claude|{event['source_file']}|"
                f"{event['source_event_id']}"
            )
            coverage["claude_mapped"] += 1

    if not enabled:
        return event_batch, dict(coverage)

    by_vendor_file: dict[str, set[str]] = defaultdict(set)
    for event in events:
        source_file = str(event.get("source_file") or "")
        if source_file:
            by_vendor_file[event["vendor"]].add(source_file)

    call_to_batch: dict[tuple[str, str], str] = {}

    # Codex: one assistant tool batch is a consecutive run of *_call
    # response_items before the first corresponding *_call_output.
    for source_file in sorted(by_vendor_file.get("codex", set())):
        path = Path(source_file)
        if not path.is_file():
            coverage["codex_missing_source_files"] += 1
            continue
        coverage["codex_readable_source_files"] += 1
        batch_no = 0
        batch_open = False
        try:
            with path.open(encoding="utf-8") as handle:
                for line in handle:
                    try:
                        record = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    if record.get("type") != "response_item":
                        continue
                    payload = record.get("payload") or {}
                    ptype = str(payload.get("type") or "")
                    is_output = ptype.endswith("_call_output") or ptype in {
                        "function_call_output",
                        "custom_tool_call_output",
                        "tool_search_output",
                    }
                    is_call = (
                        not is_output
                        and (
                            ptype.endswith("_call")
                            or ptype
                            in {
                                "function_call",
                                "custom_tool_call",
                                "tool_search_call",
                                "web_search_call",
                            }
                        )
                    )
                    if is_call:
                        if not batch_open:
                            batch_no += 1
                            batch_open = True
                        call_id = payload.get("call_id") or payload.get("id")
                        if call_id:
                            call_to_batch[(source_file, str(call_id))] = (
                                f"codex|{source_file}|{batch_no}"
                            )
                    elif is_output or ptype in {"reasoning"}:
                        batch_open = False
        except OSError:
            coverage["codex_unreadable_source_files"] += 1

    # Gemini: each model message contains a toolCalls array.
    for source_file in sorted(by_vendor_file.get("gemini", set())):
        path = Path(source_file)
        if not path.is_file():
            coverage["gemini_missing_source_files"] += 1
            continue
        coverage["gemini_readable_source_files"] += 1
        try:
            payload = load_json(path)
        except (OSError, json.JSONDecodeError):
            coverage["gemini_unreadable_source_files"] += 1
            continue
        for msg_no, message in enumerate(payload.get("messages") or []):
            calls = message.get("toolCalls") or []
            if not calls:
                continue
            batch_id = f"gemini|{source_file}|{message.get('id') or msg_no}"
            for call in calls:
                call_id = call.get("id")
                if call_id:
                    call_to_batch[(source_file, str(call_id))] = batch_id

    for idx, event in enumerate(events):
        if idx in event_batch:
            continue
        key = (str(event.get("source_file") or ""), str(event.get("source_call_id") or ""))
        batch_id = call_to_batch.get(key)
        if batch_id:
            # One native source file can contribute events to multiple project
            # exports. Project identity must remain part of the batch key or
            # project-level coverage can exceed 100%.
            event_batch[idx] = f"{event['_project']}|{batch_id}"
            coverage[f"{event['vendor']}_mapped"] += 1

    return event_batch, dict(coverage)


def md_table(headers: list[str], rows: list[list[str]]) -> str:
    if not rows:
        return "_无可报告数据。_\n"
    out = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    out.extend("| " + " | ".join(str(cell) for cell in row) + " |" for row in rows)
    return "\n".join(out) + "\n"


def main() -> None:
    args = parse_args()
    events_dir = args.events_dir.resolve()
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    input_files = discover_event_files(events_dir)
    events: list[dict[str, Any]] = []
    manifests: list[dict[str, Any]] = []
    schema_counts: Counter[str] = Counter()

    for path in input_files:
        payload = load_json(path)
        project = str(payload["repository"])
        project_events = payload.get("events") or []
        for event in project_events:
            event["_project"] = project
            event["_family"] = tool_family(event)
            event["_shell_labels"] = (
                shell_labels(
                    str(event.get("command") or ""),
                    str(event.get("command_name") or ""),
                )
                if event["_family"] == "shell"
                else []
            )
            event["_shell_primary"] = (
                event["_shell_labels"][0] if event["_shell_labels"] else ""
            )
            event["_hybrid_sequence_token"] = (
                f"shell:{event['_shell_primary']}"
                if event["_family"] == "shell"
                else event["_family"]
            )
            event["_paths"] = event_paths(event)
            event["_artifact_ids"] = event_artifact_ids(event)
            schema_counts.update(event.keys())
        events.extend(project_events)
        logical_gz = Path(str(path) + ".gz") if path.suffix != ".gz" else path
        manifests.append(
            {
                "project": project,
                "selected_file": str(path),
                "selected_format": "json.gz" if path.suffix == ".gz" else "json",
                "bytes": path.stat().st_size,
                "sha256": sha256_file(path),
                "events": len(project_events),
                "declared_sessions": payload.get("session_count"),
                "declared_source_events": payload.get("source_event_count"),
                "start_ms": payload.get("start_ms"),
                "end_ms": payload.get("end_ms"),
                "paired_gzip_present": logical_gz.is_file(),
            }
        )

    event_total = len(events)
    if event_total != 181_303:
        print(
            f"warning: expected 181,303 events from the frozen corpus, found {event_total}",
            flush=True,
        )

    event_indices = {id(event): idx for idx, event in enumerate(events)}
    streams: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    sessions: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for event in events:
        streams[(event["_project"], event["source_stream_id"])].append(event)
        sessions[(event["_project"], event["session_id"])].append(event)
    for group in streams.values():
        group.sort(key=event_sort_key)
    for group in sessions.values():
        group.sort(key=event_sort_key)

    # Coverage and schema.
    native_source_counts: Counter[tuple[str, str, str]] = Counter()
    for event in events:
        native_source_counts[
            (event["_project"], event["vendor"], str(event.get("source_file") or ""))
        ] += 1
    native_source_rows = []
    native_source_hashes: dict[str, str | None] = {}
    for (project, vendor, source_file), count in sorted(native_source_counts.items()):
        source_path = Path(source_file)
        readable = source_path.is_file()
        if source_file not in native_source_hashes:
            native_source_hashes[source_file] = (
                sha256_file(source_path) if readable else None
            )
        native_source_rows.append(
            {
                "project": project,
                "vendor": vendor,
                "source_file": source_file,
                "projected_events": count,
                "readable": readable,
                "bytes": source_path.stat().st_size if readable else None,
                "sha256": native_source_hashes[source_file],
            }
        )

    coverage_counts: dict[tuple[str, str], Counter[str]] = defaultdict(Counter)
    for event in events:
        for key in stratum_keys(event["_project"], event["vendor"]):
            counter = coverage_counts[key]
            counter["events"] += 1
            if event.get("worktree_id"):
                counter["events_with_worktree"] += 1
            if event.get("source_event_id"):
                counter["events_with_source_event_id"] += 1
            if event.get("actions"):
                counter["events_with_artifact_actions"] += 1
            counter["artifact_action_entries"] += len(event.get("actions") or [])
            if event.get("status") == "observed":
                counter["observed_status_events"] += 1

    for (project, session_id), group in sessions.items():
        vendor = group[0]["vendor"]
        for key in stratum_keys(project, vendor):
            coverage_counts[key]["sessions"] += 1
    for (project, stream_id), group in streams.items():
        vendor = group[0]["vendor"]
        for key in stratum_keys(project, vendor):
            coverage_counts[key]["streams"] += 1

    coverage_rows: list[dict[str, Any]] = []
    for (project, vendor), counts in sorted(coverage_counts.items()):
        row = with_stratum(project, vendor)
        row.update(counts)
        row["worktree_coverage"] = safe_div(
            counts["events_with_worktree"], counts["events"]
        )
        row["artifact_action_event_coverage"] = safe_div(
            counts["events_with_artifact_actions"], counts["events"]
        )
        row["observed_status_share"] = safe_div(
            counts["observed_status_events"], counts["events"]
        )
        coverage_rows.append(row)

    schema_rows = []
    for field, count in sorted(schema_counts.items()):
        if field.startswith("_"):
            continue
        schema_rows.append(
            {
                "field": field,
                "events_present": count,
                "coverage": count / event_total,
            }
        )

    # Tool family, raw tool, status, and shell command distributions.
    family_counts: dict[tuple[str, str, str, str], int] = Counter()
    raw_tool_counts: dict[tuple[str, str, str, str, str], int] = Counter()
    effect_counts: dict[tuple[str, str, str, str, str, str], int] = Counter()
    shell_primary_counts: dict[tuple[str, str, str], int] = Counter()
    shell_label_counts: dict[tuple[str, str, str], int] = Counter()
    shell_command_name_counts: dict[tuple[str, str, str], int] = Counter()
    stratum_event_totals: Counter[tuple[str, str]] = Counter()
    stratum_shell_totals: Counter[tuple[str, str]] = Counter()
    for event in events:
        for project, vendor in stratum_keys(event["_project"], event["vendor"]):
            stratum_event_totals[(project, vendor)] += 1
            family_counts[(project, vendor, event["_family"], event["status"])] += 1
            raw_tool_counts[
                (project, vendor, event["tool_name"], event["_family"], event["status"])
            ] += 1
            effect_counts[
                (
                    project,
                    vendor,
                    event["_family"],
                    str(event.get("category") or ""),
                    str(event.get("effect") or ""),
                    event["status"],
                )
            ] += 1
            if event["_family"] == "shell":
                stratum_shell_totals[(project, vendor)] += 1
                shell_command_name_counts[
                    (project, vendor, str(event.get("command_name") or "(missing)"))
                ] += 1
                shell_primary_counts[
                    (project, vendor, event["_shell_primary"])
                ] += 1
                for label in event["_shell_labels"]:
                    shell_label_counts[(project, vendor, label)] += 1

    family_rows = []
    family_status_totals: dict[tuple[str, str, str], Counter[str]] = defaultdict(Counter)
    for (project, vendor, family, status), count in family_counts.items():
        family_status_totals[(project, vendor, family)][status] += count
    for (project, vendor, family), statuses in sorted(family_status_totals.items()):
        total = sum(statuses.values())
        decisive = sum(statuses[s] for s in DECISIVE_STATUSES)
        row = with_stratum(project, vendor)
        row.update(
            {
                "tool_family": family,
                "calls": total,
                "share": total / stratum_event_totals[(project, vendor)],
                "ok": statuses["ok"],
                "fail": statuses["fail"],
                "observed": statuses["observed"],
                "decisive_failure_rate": safe_div(statuses["fail"], decisive),
                "observed_share": safe_div(statuses["observed"], total),
            }
        )
        family_rows.append(row)

    raw_tool_rows = []
    raw_tool_status_totals: dict[
        tuple[str, str, str, str], Counter[str]
    ] = defaultdict(Counter)
    for (project, vendor, name, family, status), count in raw_tool_counts.items():
        raw_tool_status_totals[(project, vendor, name, family)][status] += count
    for (project, vendor, name, family), statuses in sorted(
        raw_tool_status_totals.items()
    ):
        total = sum(statuses.values())
        decisive = statuses["ok"] + statuses["fail"]
        row = with_stratum(project, vendor)
        row.update(
            {
                "tool_name": name,
                "tool_family": family,
                "calls": total,
                "share": total / stratum_event_totals[(project, vendor)],
                "ok": statuses["ok"],
                "fail": statuses["fail"],
                "observed": statuses["observed"],
                "decisive_failure_rate": safe_div(statuses["fail"], decisive),
            }
        )
        raw_tool_rows.append(row)

    effect_rows = []
    effect_status_totals: dict[
        tuple[str, str, str, str, str], Counter[str]
    ] = defaultdict(Counter)
    for (project, vendor, family, category, effect, status), count in effect_counts.items():
        effect_status_totals[(project, vendor, family, category, effect)][status] += count
    for (project, vendor, family, category, effect), statuses in sorted(
        effect_status_totals.items()
    ):
        total = sum(statuses.values())
        row = with_stratum(project, vendor)
        row.update(
            {
                "tool_family": family,
                "source_category": category,
                "projected_effect": effect,
                "calls": total,
                "share": total / stratum_event_totals[(project, vendor)],
                "ok": statuses["ok"],
                "fail": statuses["fail"],
                "observed": statuses["observed"],
            }
        )
        effect_rows.append(row)

    shell_primary_rows = []
    for (project, vendor, label), count in sorted(shell_primary_counts.items()):
        row = with_stratum(project, vendor)
        row.update(
            {
                "shell_class": label,
                "classification": "primary",
                "calls": count,
                "share_of_shell_calls": count / stratum_shell_totals[(project, vendor)],
            }
        )
        shell_primary_rows.append(row)
    shell_multilabel_rows = []
    for (project, vendor, label), count in sorted(shell_label_counts.items()):
        row = with_stratum(project, vendor)
        row.update(
            {
                "shell_class": label,
                "classification": "multi_label_presence",
                "calls": count,
                "share_of_shell_calls": count / stratum_shell_totals[(project, vendor)],
            }
        )
        shell_multilabel_rows.append(row)
    shell_command_name_rows = []
    for (project, vendor, command_name), count in sorted(
        shell_command_name_counts.items()
    ):
        row = with_stratum(project, vendor)
        row.update(
            {
                "command_name": command_name,
                "calls": count,
                "share_of_shell_calls": count
                / stratum_shell_totals[(project, vendor)],
            }
        )
        shell_command_name_rows.append(row)

    # Stream-local n-grams, Markov transitions, and same-family runs.
    ngram_counts: Counter[
        tuple[str, str, str, str, int, tuple[str, ...]]
    ] = Counter()
    ngram_totals: Counter[tuple[str, str, str, str, int]] = Counter()
    transition_counts: Counter[
        tuple[str, str, str, str, str, str]
    ] = Counter()
    transition_origins: Counter[tuple[str, str, str, str, str]] = Counter()
    run_lengths: dict[tuple[str, str, str, str], list[int]] = defaultdict(list)
    for (project, _stream_id), group in streams.items():
        vendor = group[0]["vendor"]
        prompt_segments: list[list[dict[str, Any]]] = []
        for event in group:
            if (
                not prompt_segments
                or prompt_segments[-1][-1].get("prompt_index")
                != event.get("prompt_index")
            ):
                prompt_segments.append([event])
            else:
                prompt_segments[-1].append(event)
        scoped_segments = {
            "same_prompt": prompt_segments,
            "full_stream": [group],
        }
        for skey in stratum_keys(project, vendor):
            sp, sv = skey
            for scope, segments in scoped_segments.items():
                for segment in segments:
                    sequences = {
                        "tool_family": [event["_family"] for event in segment],
                        "hybrid_shell": [
                            event["_hybrid_sequence_token"] for event in segment
                        ],
                    }
                    for granularity, tokens in sequences.items():
                        for n in (2, 3, 4):
                            if len(tokens) < n:
                                continue
                            ngram_totals[
                                (sp, sv, scope, granularity, n)
                            ] += len(tokens) - n + 1
                            for idx in range(len(tokens) - n + 1):
                                ngram_counts[
                                    (
                                        sp,
                                        sv,
                                        scope,
                                        granularity,
                                        n,
                                        tuple(tokens[idx : idx + n]),
                                    )
                                ] += 1
                        for before, after in zip(tokens, tokens[1:]):
                            transition_counts[
                                (sp, sv, scope, granularity, before, after)
                            ] += 1
                            transition_origins[
                                (sp, sv, scope, granularity, before)
                            ] += 1
                    families = sequences["tool_family"]
                    if families:
                        current = families[0]
                        length = 1
                        for family in families[1:]:
                            if family == current:
                                length += 1
                            else:
                                run_lengths[(sp, sv, scope, current)].append(
                                    length
                                )
                                current = family
                                length = 1
                        run_lengths[(sp, sv, scope, current)].append(length)

    ngram_rows = []
    by_stratum_n: dict[
        tuple[str, str, str, str, int], list[tuple[tuple[str, ...], int]]
    ] = defaultdict(list)
    for (
        project,
        vendor,
        scope,
        granularity,
        n,
        gram,
    ), count in ngram_counts.items():
        by_stratum_n[(project, vendor, scope, granularity, n)].append(
            (gram, count)
        )
    for (project, vendor, scope, granularity, n), values in sorted(
        by_stratum_n.items()
    ):
        for rank, (gram, count) in enumerate(
            sorted(values, key=lambda item: (-item[1], item[0]))[:30], start=1
        ):
            row = with_stratum(project, vendor)
            row.update(
                {
                    "sequence_scope": scope,
                    "sequence_granularity": granularity,
                    "n": n,
                    "rank": rank,
                    "ngram": " → ".join(gram),
                    "count": count,
                    "share": count
                    / ngram_totals[(project, vendor, scope, granularity, n)],
                    "total_ngrams": ngram_totals[
                        (project, vendor, scope, granularity, n)
                    ],
                }
            )
            ngram_rows.append(row)

    transition_rows = []
    transition_totals: Counter[tuple[str, str, str, str]] = Counter()
    for (
        project,
        vendor,
        scope,
        granularity,
        _before,
        _after,
    ), count in transition_counts.items():
        transition_totals[(project, vendor, scope, granularity)] += count
    for (project, vendor, scope, granularity, before, after), count in sorted(
        transition_counts.items()
    ):
        row = with_stratum(project, vendor)
        row.update(
            {
                "sequence_scope": scope,
                "sequence_granularity": granularity,
                "from_family": before,
                "to_family": after,
                "count": count,
                "conditional_probability": count
                / transition_origins[
                    (project, vendor, scope, granularity, before)
                ],
                "all_transition_share": count
                / transition_totals[(project, vendor, scope, granularity)],
            }
        )
        transition_rows.append(row)

    run_rows = []
    for (project, vendor, scope, family), values in sorted(run_lengths.items()):
        row = with_stratum(project, vendor)
        row.update(
            {
                "sequence_scope": scope,
                "tool_family": family,
                **summarize_numeric(values, "run_"),
            }
        )
        row["runs_ge_3_share"] = safe_div(sum(v >= 3 for v in values), len(values))
        row["runs_ge_5_share"] = safe_div(sum(v >= 5 for v in values), len(values))
        run_rows.append(row)

    # Session-level pace, composition, and concentration.
    session_metric_rows = []
    for (project, session_id), group in sorted(sessions.items()):
        vendor = group[0]["vendor"]
        timestamps = [int(event["ts_ms"]) for event in group]
        span_ms = max(timestamps) - min(timestamps) if len(timestamps) > 1 else 0
        stream_ids = {event["source_stream_id"] for event in group}
        stream_pairs = 0
        stream_switches = 0
        same_prompt_gaps: list[int] = []
        capped_active_ms = 0
        for stream_id in stream_ids:
            stream = streams[(project, stream_id)]
            if stream[0]["session_id"] != session_id:
                continue
            for prev, nxt in zip(stream, stream[1:]):
                if prev.get("prompt_index") != nxt.get("prompt_index"):
                    continue
                stream_pairs += 1
                stream_switches += prev["_family"] != nxt["_family"]
                delta = max(0, int(nxt["ts_ms"]) - int(prev["ts_ms"]))
                capped_active_ms += min(delta, 300_000)
                if prev.get("prompt_index") == nxt.get("prompt_index"):
                    same_prompt_gaps.append(delta)
        calls_per_active_hour = (
            len(group) / (capped_active_ms / 3_600_000)
            if capped_active_ms > 0
            else None
        )
        session_metric_rows.append(
            {
                "project": project,
                "vendor": vendor,
                "session_id": session_id,
                "calls": len(group),
                "streams": len(stream_ids),
                "active_span_hours": span_ms / 3_600_000,
                "capped_active_hours": capped_active_ms / 3_600_000,
                "calls_per_capped_active_hour": calls_per_active_hour,
                "tool_family_entropy_bits": entropy([event["_family"] for event in group]),
                "stream_local_switch_rate": safe_div(stream_switches, stream_pairs),
                "same_prompt_intercall_p50_ms": percentile(same_prompt_gaps, 0.50),
                "same_prompt_intercall_p90_ms": percentile(same_prompt_gaps, 0.90),
                "failed_calls": sum(event["status"] == "fail" for event in group),
                "observed_status_calls": sum(
                    event["status"] == "observed" for event in group
                ),
            }
        )

    session_pace_rows = []
    pace_buckets: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in session_metric_rows:
        for key in stratum_keys(row["project"], row["vendor"]):
            pace_buckets[key].append(row)
    for (project, vendor), rows in sorted(pace_buckets.items()):
        call_values = [row["calls"] for row in rows]
        spans = [row["active_span_hours"] for row in rows]
        rates = [
            row["calls_per_capped_active_hour"]
            for row in rows
            if row["calls_per_capped_active_hour"] is not None
        ]
        entropies = [row["tool_family_entropy_bits"] for row in rows]
        switches = [
            row["stream_local_switch_rate"]
            for row in rows
            if row["stream_local_switch_rate"] is not None
        ]
        out = with_stratum(project, vendor)
        out.update(
            {
                "sessions": len(rows),
                "calls": sum(call_values),
                "calls_p50": percentile(call_values, 0.50),
                "calls_p90": percentile(call_values, 0.90),
                "calls_p99": percentile(call_values, 0.99),
                "active_span_hours_p50": percentile(spans, 0.50),
                "active_span_hours_p90": percentile(spans, 0.90),
                "calls_per_capped_active_hour_p50": percentile(rates, 0.50),
                "tool_family_entropy_bits_p50": percentile(entropies, 0.50),
                "stream_local_switch_rate_p50": percentile(switches, 0.50),
                "session_call_gini": gini(call_values),
                "top_10pct_sessions_call_share": top_fraction_share(call_values, 0.10),
            }
        )
        session_pace_rows.append(out)

    # Repeat reads under two explicit estimands: registered artifact identity
    # from actions, and exact source path from source_paths.
    repeated_read_rows = []
    for unit_name, groups in (("source_stream", streams), ("root_session", sessions)):
        prompt_scopes = (
            ("same_prompt", "full_stream")
            if unit_name == "source_stream"
            else ("full_stream",)
        )
        for evidence_source in ("artifact_actions", "source_paths_exact_path"):
            for prompt_scope in prompt_scopes:
                accum: dict[tuple[str, str], dict[str, Any]] = defaultdict(
                    lambda: {
                        "read_instances": 0,
                        "repeat_read_instances": 0,
                        "unchanged_repeat_instances": 0,
                        "group_identity_units": 0,
                        "repeated_group_identity_units": 0,
                        "gap_calls": [],
                        "gap_ms": [],
                    }
                )
                for (project, _group_id), group in groups.items():
                    vendor = group[0]["vendor"]
                    if prompt_scope == "same_prompt":
                        segments: list[list[dict[str, Any]]] = []
                        for event in group:
                            if (
                                not segments
                                or segments[-1][-1].get("prompt_index")
                                != event.get("prompt_index")
                            ):
                                segments.append([event])
                            else:
                                segments[-1].append(event)
                    else:
                        segments = [group]

                    local = {
                        "read_instances": 0,
                        "repeat_read_instances": 0,
                        "unchanged_repeat_instances": 0,
                        "group_identity_units": 0,
                        "repeated_group_identity_units": 0,
                        "gap_calls": [],
                        "gap_ms": [],
                    }
                    for segment in segments:
                        seen_read: dict[
                            tuple[str, str], tuple[int, int, tuple[int, int]]
                        ] = {}
                        last_mutation: dict[tuple[str, str], tuple[int, int]] = {}
                        identity_counts: Counter[tuple[str, str]] = Counter()
                        for event_idx, event in enumerate(segment):
                            if evidence_source == "artifact_actions":
                                records = sorted(
                                    event.get("actions") or [],
                                    key=lambda item: int(
                                        item.get("action_ordinal") or 0
                                    ),
                                )
                            else:
                                records = list(event.get("source_paths") or [])
                            for record_idx, record in enumerate(records):
                                if evidence_source == "artifact_actions":
                                    identity = record.get("artifact_id") or record.get(
                                        "path"
                                    )
                                    worktree = (
                                        record.get("worktree_id")
                                        or event.get("worktree_id")
                                        or ""
                                    )
                                else:
                                    identity = record.get("path")
                                    worktree = event.get("worktree_id") or ""
                                if not identity:
                                    continue
                                key = (str(worktree), str(identity))
                                position = (event_idx, record_idx)
                                access = str(record.get("access") or "")
                                if access == "read":
                                    identity_counts[key] += 1
                                    local["read_instances"] += 1
                                    if key in seen_read:
                                        (
                                            prev_event_idx,
                                            prev_ts,
                                            prev_position,
                                        ) = seen_read[key]
                                        local["repeat_read_instances"] += 1
                                        local["gap_calls"].append(
                                            event_idx - prev_event_idx
                                        )
                                        local["gap_ms"].append(
                                            max(
                                                0,
                                                int(event["ts_ms"]) - prev_ts,
                                            )
                                        )
                                        if (
                                            last_mutation.get(key, (-1, -1))
                                            <= prev_position
                                        ):
                                            local[
                                                "unchanged_repeat_instances"
                                            ] += 1
                                    seen_read[key] = (
                                        event_idx,
                                        int(event["ts_ms"]),
                                        position,
                                    )
                                elif access in MUTATION_ACCESSES:
                                    last_mutation[key] = position
                        local["group_identity_units"] += len(identity_counts)
                        local["repeated_group_identity_units"] += sum(
                            count >= 2 for count in identity_counts.values()
                        )
                    for skey in stratum_keys(project, vendor):
                        target = accum[skey]
                        for key in (
                            "read_instances",
                            "repeat_read_instances",
                            "unchanged_repeat_instances",
                            "group_identity_units",
                            "repeated_group_identity_units",
                        ):
                            target[key] += local[key]
                        target["gap_calls"].extend(local["gap_calls"])
                        target["gap_ms"].extend(local["gap_ms"])
                for (project, vendor), values in sorted(accum.items()):
                    row = with_stratum(project, vendor)
                    row.update(
                        {
                            "analysis_unit": unit_name,
                            "prompt_scope": prompt_scope,
                            "evidence_source": evidence_source,
                            "identity_basis": (
                                "registered_artifact_identity"
                                if evidence_source == "artifact_actions"
                                else "exact_source_path"
                            ),
                            "read_instances": values["read_instances"],
                            "repeat_read_instances": values[
                                "repeat_read_instances"
                            ],
                            "repeat_read_share": safe_div(
                                values["repeat_read_instances"],
                                values["read_instances"],
                            ),
                            "unchanged_repeat_instances": values[
                                "unchanged_repeat_instances"
                            ],
                            "unchanged_share_among_repeats": safe_div(
                                values["unchanged_repeat_instances"],
                                values["repeat_read_instances"],
                            ),
                            "group_identity_units": values[
                                "group_identity_units"
                            ],
                            "repeated_group_identity_units": values[
                                "repeated_group_identity_units"
                            ],
                            "repeated_group_identity_share": safe_div(
                                values["repeated_group_identity_units"],
                                values["group_identity_units"],
                            ),
                            "gap_calls_p50": percentile(
                                values["gap_calls"], 0.50
                            ),
                            "gap_calls_p90": percentile(
                                values["gap_calls"], 0.90
                            ),
                            "gap_ms_p50": percentile(values["gap_ms"], 0.50),
                            "gap_ms_p90": percentile(values["gap_ms"], 0.90),
                        }
                    )
                    repeated_read_rows.append(row)

    # Exact shell-command reruns.
    shell_repeat_rows = []
    for unit_name, groups in (("source_stream", streams), ("root_session", sessions)):
        prompt_scopes = (
            ("same_prompt", "full_stream")
            if unit_name == "source_stream"
            else ("full_stream",)
        )
        for prompt_scope in prompt_scopes:
            accum: dict[tuple[str, str], Counter[str]] = defaultdict(Counter)
            for (project, _group_id), group in groups.items():
                vendor = group[0]["vendor"]
                if prompt_scope == "same_prompt":
                    segments: list[list[dict[str, Any]]] = []
                    for event in group:
                        if (
                            not segments
                            or segments[-1][-1].get("prompt_index")
                            != event.get("prompt_index")
                        ):
                            segments.append([event])
                        else:
                            segments[-1].append(event)
                else:
                    segments = [group]
                local: Counter[str] = Counter()
                for segment in segments:
                    seen: set[str] = set()
                    seen_normalized: set[str] = set()
                    commands: set[str] = set()
                    previous_event: dict[str, Any] | None = None
                    for event in segment:
                        if event["_family"] != "shell":
                            previous_event = event
                            continue
                        command = str(event.get("command") or "")
                        if not command:
                            previous_event = event
                            continue
                        normalized = normalize_command(command)
                        local["shell_calls_with_command"] += 1
                        commands.add(command)
                        if command in seen:
                            local["exact_reruns"] += 1
                        if normalized in seen_normalized:
                            local["whitespace_normalized_reruns"] += 1
                        if previous_event is not None and same_command_text(
                            previous_event, event
                        ):
                            local["immediate_exact_reruns"] += 1
                            if previous_event.get("status") == "fail":
                                local["immediate_reruns_after_failure"] += 1
                                if event.get("status") == "ok":
                                    local[
                                        "immediate_failure_rerun_successes"
                                    ] += 1
                        seen.add(command)
                        seen_normalized.add(normalized)
                        previous_event = event
                    local["unique_commands"] += len(commands)
                for skey in stratum_keys(project, vendor):
                    accum[skey].update(local)
            for (project, vendor), values in sorted(accum.items()):
                row = with_stratum(project, vendor)
                row.update(
                    {
                        "analysis_unit": unit_name,
                        "prompt_scope": prompt_scope,
                        "shell_calls_with_command": values[
                            "shell_calls_with_command"
                        ],
                        "unique_commands": values["unique_commands"],
                        "exact_reruns": values["exact_reruns"],
                        "whitespace_normalized_reruns": values[
                            "whitespace_normalized_reruns"
                        ],
                        "immediate_exact_reruns": values[
                            "immediate_exact_reruns"
                        ],
                        "immediate_reruns_after_failure": values[
                            "immediate_reruns_after_failure"
                        ],
                        "immediate_failure_rerun_successes": values[
                            "immediate_failure_rerun_successes"
                        ],
                    }
                )
                row["exact_rerun_share"] = safe_div(
                    values["exact_reruns"], values["shell_calls_with_command"]
                )
                row["immediate_exact_rerun_share"] = safe_div(
                    values["immediate_exact_reruns"],
                    values["shell_calls_with_command"],
                )
                row["failure_rerun_success_rate"] = safe_div(
                    values["immediate_failure_rerun_successes"],
                    values["immediate_reruns_after_failure"],
                )
                shell_repeat_rows.append(row)

    # Failure rates and first/within-three follow-up behavior.
    failure_rate_rows = []
    for source_name, rows in (("tool_family", family_rows), ("tool_name", raw_tool_rows)):
        for base in rows:
            out = {
                "stratum_type": base["stratum_type"],
                "project": base["project"],
                "vendor": base["vendor"],
                "grouping": source_name,
                "tool_group": base[source_name],
                "calls": base["calls"],
                "ok": base["ok"],
                "fail": base["fail"],
                "observed": base["observed"],
                "decisive_calls": base["ok"] + base["fail"],
                "decisive_failure_rate": base["decisive_failure_rate"],
                "observed_share": safe_div(base["observed"], base["calls"]),
            }
            failure_rate_rows.append(out)

    followup_counts: Counter[tuple[str, str, str, str]] = Counter()
    failure_totals: Counter[tuple[str, str, str]] = Counter()
    within3_counts: Counter[tuple[str, str, str, str]] = Counter()
    for (project, _stream_id), group in streams.items():
        vendor = group[0]["vendor"]
        for idx, event in enumerate(group):
            if event.get("status") != "fail":
                continue
            family = event["_family"]
            if idx + 1 >= len(group):
                behavior = "end_of_stream"
                candidates: list[dict[str, Any]] = []
            elif group[idx + 1].get("prompt_index") != event.get("prompt_index"):
                behavior = "end_of_prompt"
                candidates = []
            else:
                nxt = group[idx + 1]
                if same_command(event, nxt):
                    behavior = (
                        "exact_retry_success"
                        if nxt.get("status") == "ok"
                        else "exact_retry_not_success"
                    )
                elif nxt.get("tool_name") == event.get("tool_name"):
                    if family == "shell":
                        behavior = (
                            "generic_shell_changed_command_same_class"
                            if event["_shell_primary"] == nxt["_shell_primary"]
                            else "generic_shell_changed_command_different_class"
                        )
                    else:
                        behavior = "same_raw_tool_changed_arguments"
                elif nxt["_family"] == family:
                    behavior = "same_family_changed_tool_or_arguments"
                else:
                    behavior = f"switch_to:{nxt['_family']}"
                candidates = []
                for candidate in group[idx + 1 : idx + 4]:
                    if candidate.get("prompt_index") != event.get("prompt_index"):
                        break
                    candidates.append(candidate)
            exact_within3 = any(same_command(event, candidate) for candidate in candidates)
            same_family_within3 = any(
                candidate["_family"] == family for candidate in candidates
            )
            for sp, sv in stratum_keys(project, vendor):
                failure_totals[(sp, sv, family)] += 1
                followup_counts[(sp, sv, family, behavior)] += 1
                within3_counts[
                    (
                        sp,
                        sv,
                        family,
                        "exact_retry_within_3" if exact_within3 else "no_exact_retry_within_3",
                    )
                ] += 1
                within3_counts[
                    (
                        sp,
                        sv,
                        family,
                        "same_family_within_3"
                        if same_family_within3
                        else "no_same_family_within_3",
                    )
                ] += 1

    failure_followup_rows = []
    for (project, vendor, family, behavior), count in sorted(followup_counts.items()):
        row = with_stratum(project, vendor)
        total = failure_totals[(project, vendor, family)]
        row.update(
            {
                "tool_family": family,
                "analysis_scope": "same_prompt_source_stream",
                "window": "next_call",
                "behavior": behavior,
                "count": count,
                "share": count / total,
                "failed_calls": total,
            }
        )
        failure_followup_rows.append(row)
    for (project, vendor, family, behavior), count in sorted(within3_counts.items()):
        row = with_stratum(project, vendor)
        total = failure_totals[(project, vendor, family)]
        row.update(
            {
                "tool_family": family,
                "analysis_scope": "same_prompt_source_stream",
                "window": "within_3_calls",
                "behavior": behavior,
                "count": count,
                "share": count / total,
                "failed_calls": total,
            }
        )
        failure_followup_rows.append(row)

    # Adjacent-call observable dependency estimate.
    dependency_counts: Counter[tuple[str, str, str, str]] = Counter()
    dependency_totals: Counter[tuple[str, str]] = Counter()
    for (project, _stream_id), group in streams.items():
        vendor = group[0]["vendor"]
        for prev, nxt in zip(group, group[1:]):
            if prev.get("prompt_index") != nxt.get("prompt_index"):
                continue
            classification, reason = classify_adjacent_dependency(prev, nxt)
            for sp, sv in stratum_keys(project, vendor):
                dependency_counts[(sp, sv, classification, reason)] += 1
                dependency_totals[(sp, sv)] += 1
    dependency_rows = []
    for (project, vendor, classification, reason), count in sorted(
        dependency_counts.items()
    ):
        row = with_stratum(project, vendor)
        row.update(
            {
                "analysis_scope": "same_prompt_source_stream",
                "classification": classification,
                "reason": reason,
                "adjacent_pairs": count,
                "share": count / dependency_totals[(project, vendor)],
                "all_adjacent_pairs": dependency_totals[(project, vendor)],
            }
        )
        dependency_rows.append(row)

    # Native assistant multi-call batches.
    event_batch, batch_coverage = reconstruct_native_batches(
        events, not args.no_native_batches
    )
    batches: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for event in events:
        idx = event_indices[id(event)]
        if idx in event_batch:
            batches[event_batch[idx]].append(event)
    parallel_batch_rows = []
    parallel_accum: dict[tuple[str, str], dict[str, Any]] = defaultdict(
        lambda: {
            "covered_calls": 0,
            "batches": 0,
            "multi_call_batches": 0,
            "calls_in_multi_call_batches": 0,
            "batch_sizes": [],
            "shared_path_batches": 0,
            "disjoint_path_batches": 0,
            "unknown_dependency_batches": 0,
        }
    )
    for batch_id, group in sorted(batches.items()):
        group.sort(key=event_sort_key)
        project = group[0]["_project"]
        vendor = group[0]["vendor"]
        size = len(group)
        all_have_paths = all(event["_paths"] for event in group)
        shared_path = any(
            group[i]["_paths"] & group[j]["_paths"]
            for i in range(size)
            for j in range(i + 1, size)
        )
        if shared_path:
            dep = "shared_observed_path"
        elif all_have_paths and size > 1:
            dep = "pairwise_disjoint_observed_paths"
        else:
            dep = "unknown"
        for skey in stratum_keys(project, vendor):
            acc = parallel_accum[skey]
            acc["covered_calls"] += size
            acc["batches"] += 1
            acc["batch_sizes"].append(size)
            if size > 1:
                acc["multi_call_batches"] += 1
                acc["calls_in_multi_call_batches"] += size
                if dep == "shared_observed_path":
                    acc["shared_path_batches"] += 1
                elif dep == "pairwise_disjoint_observed_paths":
                    acc["disjoint_path_batches"] += 1
                else:
                    acc["unknown_dependency_batches"] += 1
        if size > 1:
            parallel_batch_rows.append(
                {
                    "project": project,
                    "vendor": vendor,
                    "session_id": group[0]["session_id"],
                    "source_stream_id": group[0]["source_stream_id"],
                    "source_file": group[0]["source_file"],
                    "batch_id": batch_id,
                    "batch_size": size,
                    "source_call_ids": " | ".join(
                        str(event.get("source_call_id") or "") for event in group
                    ),
                    "source_event_ids": " | ".join(
                        str(event.get("source_event_id") or "") for event in group
                    ),
                    "tool_families": " | ".join(event["_family"] for event in group),
                    "tool_names": " | ".join(event["tool_name"] for event in group),
                    "observable_path_relation": dep,
                    "timestamp_spread_ms": max(int(event["ts_ms"]) for event in group)
                    - min(int(event["ts_ms"]) for event in group),
                }
            )

    parallel_usage_rows = []
    for (project, vendor), acc in sorted(parallel_accum.items()):
        row = with_stratum(project, vendor)
        row.update(
            {
                "covered_calls": acc["covered_calls"],
                "all_calls": stratum_event_totals[(project, vendor)],
                "native_batch_coverage": safe_div(
                    acc["covered_calls"], stratum_event_totals[(project, vendor)]
                ),
                "batches": acc["batches"],
                "multi_call_batches": acc["multi_call_batches"],
                "multi_call_batch_share": safe_div(
                    acc["multi_call_batches"], acc["batches"]
                ),
                "calls_in_multi_call_batches": acc["calls_in_multi_call_batches"],
                "batched_call_share": safe_div(
                    acc["calls_in_multi_call_batches"], acc["covered_calls"]
                ),
                "batch_size_p50": percentile(acc["batch_sizes"], 0.50),
                "batch_size_p90": percentile(acc["batch_sizes"], 0.90),
                "batch_size_max": max(acc["batch_sizes"]) if acc["batch_sizes"] else None,
                "shared_path_multi_batches": acc["shared_path_batches"],
                "disjoint_path_multi_batches": acc["disjoint_path_batches"],
                "unknown_dependency_multi_batches": acc[
                    "unknown_dependency_batches"
                ],
            }
        )
        parallel_usage_rows.append(row)

    # Inter-call timing. These are start-to-next-start gaps, not tool durations.
    gap_records: list[dict[str, Any]] = []
    for (project, _stream_id), group in streams.items():
        vendor = group[0]["vendor"]
        for prev, nxt in zip(group, group[1:]):
            gap_records.append(
                {
                    "project": project,
                    "vendor": vendor,
                    "preceding_family": prev["_family"],
                    "gap_ms": max(0, int(nxt["ts_ms"]) - int(prev["ts_ms"])),
                    "same_prompt": prev.get("prompt_index") == nxt.get("prompt_index"),
                }
            )

    timing_values: dict[tuple[str, str, str, str], list[int]] = defaultdict(list)
    for record in gap_records:
        scopes = ["all_adjacent"]
        if record["same_prompt"]:
            scopes.append("same_prompt")
        for sp, sv in stratum_keys(record["project"], record["vendor"]):
            for scope in scopes:
                timing_values[(sp, sv, scope, ALL)].append(record["gap_ms"])
                timing_values[
                    (sp, sv, scope, record["preceding_family"])
                ].append(record["gap_ms"])
    timing_rows = []
    for (project, vendor, scope, family), values in sorted(timing_values.items()):
        row = with_stratum(project, vendor)
        row.update(
            {
                "scope": scope,
                "preceding_tool_family": family,
                "gaps": len(values),
                "gap_ms_p50": percentile(values, 0.50),
                "gap_ms_p90": percentile(values, 0.90),
                "gap_ms_p95": percentile(values, 0.95),
                "gap_ms_p99": percentile(values, 0.99),
                "gap_ms_max": max(values) if values else None,
                "gap_le_1s_share": safe_div(sum(v <= 1_000 for v in values), len(values)),
                "gap_le_10s_share": safe_div(
                    sum(v <= 10_000 for v in values), len(values)
                ),
                "gap_gt_60s_count": sum(v > 60_000 for v in values),
                "gap_gt_60s_share": safe_div(
                    sum(v > 60_000 for v in values), len(values)
                ),
                "gap_gt_10m_count": sum(v > 600_000 for v in values),
                "gap_gt_10m_share": safe_div(
                    sum(v > 600_000 for v in values), len(values)
                ),
            }
        )
        timing_rows.append(row)
    long_gap_totals: Counter[tuple[str, str, str]] = Counter()
    for row in timing_rows:
        if row["preceding_tool_family"] == ALL:
            long_gap_totals[(row["project"], row["vendor"], row["scope"])] = row[
                "gap_gt_60s_count"
            ]
    for row in timing_rows:
        row["share_of_stratum_gaps_gt_60s"] = (
            safe_div(
                row["gap_gt_60s_count"],
                long_gap_totals[(row["project"], row["vendor"], row["scope"])],
            )
            if row["preceding_tool_family"] != ALL
            else 1.0
        )

    # Source-record duplication diagnostic. This never changes the registered
    # 181,303-call denominator; it exposes repeated native call IDs across
    # included source streams/sessions.
    duplicate_groups: dict[
        tuple[str, str, str], list[dict[str, Any]]
    ] = defaultdict(list)
    for event in events:
        duplicate_groups[
            (event["_project"], event["vendor"], str(event.get("source_call_id") or ""))
        ].append(event)
    duplicate_accum: dict[tuple[str, str], Counter[str]] = defaultdict(Counter)
    for (project, vendor, _call_id), group in duplicate_groups.items():
        source_streams = {event["source_stream_id"] for event in group}
        source_files = {event["source_file"] for event in group}
        native_sessions = {event["session_id"] for event in group}
        core_fingerprints = {
            (
                event.get("tool_name"),
                event.get("command"),
                event.get("status"),
                event.get("ts_ms"),
            )
            for event in group
        }
        for skey in stratum_keys(project, vendor):
            acc = duplicate_accum[skey]
            acc["calls"] += len(group)
            acc["unique_source_call_ids"] += 1
            if len(group) > 1:
                acc["duplicated_id_groups"] += 1
                acc["records_in_duplicated_id_groups"] += len(group)
                acc["duplicate_records_beyond_first"] += len(group) - 1
                acc["cross_stream_duplicated_groups"] += len(source_streams) > 1
                acc["cross_file_duplicated_groups"] += len(source_files) > 1
                acc["cross_session_duplicated_groups"] += len(native_sessions) > 1
                acc["exact_core_duplicated_groups"] += len(core_fingerprints) == 1
    duplicate_rows = []
    for (project, vendor), values in sorted(duplicate_accum.items()):
        row = with_stratum(project, vendor)
        row.update(
            {
                "calls": values["calls"],
                "unique_source_call_ids": values["unique_source_call_ids"],
                "duplicated_id_groups": values["duplicated_id_groups"],
                "records_in_duplicated_id_groups": values[
                    "records_in_duplicated_id_groups"
                ],
                "duplicate_records_beyond_first": values[
                    "duplicate_records_beyond_first"
                ],
                "cross_stream_duplicated_groups": values[
                    "cross_stream_duplicated_groups"
                ],
                "cross_file_duplicated_groups": values[
                    "cross_file_duplicated_groups"
                ],
                "cross_session_duplicated_groups": values[
                    "cross_session_duplicated_groups"
                ],
                "exact_core_duplicated_groups": values[
                    "exact_core_duplicated_groups"
                ],
            }
        )
        row["duplicate_records_beyond_first_share"] = safe_div(
            values["duplicate_records_beyond_first"], values["calls"]
        )
        duplicate_rows.append(row)

    # Recalculation invariants. These are ordinary audit rows, not scientific
    # acceptance gates; they catch denominator drift and accidental file
    # double-loading.
    overall_family_calls = sum(
        row["calls"] for row in family_rows if row["stratum_type"] == "overall"
    )
    overall_shell_primary = sum(
        row["calls"] for row in shell_primary_rows if row["stratum_type"] == "overall"
    )
    direct_read_action_entries = sum(
        action.get("access") == "read"
        for event in events
        for action in (event.get("actions") or [])
    )
    direct_source_path_read_entries = sum(
        source_path.get("access") == "read"
        for event in events
        for source_path in (event.get("source_paths") or [])
    )
    expected_transitions = sum(max(0, len(group) - 1) for group in streams.values())
    expected_same_prompt_transitions = sum(
        prev.get("prompt_index") == nxt.get("prompt_index")
        for group in streams.values()
        for prev, nxt in zip(group, group[1:])
    )
    overall_transitions = sum(
        row["count"]
        for row in transition_rows
        if row["stratum_type"] == "overall"
        and row["sequence_scope"] == "same_prompt"
        and row["sequence_granularity"] == "tool_family"
    )
    overall_full_stream_transitions = sum(
        row["count"]
        for row in transition_rows
        if row["stratum_type"] == "overall"
        and row["sequence_scope"] == "full_stream"
        and row["sequence_granularity"] == "tool_family"
    )
    overall_parallel_covered = sum(
        row["covered_calls"]
        for row in parallel_usage_rows
        if row["stratum_type"] == "overall"
    )
    validation_specs = [
        ("selected_input_event_sum", sum(row["events"] for row in manifests), event_total),
        (
            "declared_root_session_sum",
            sum(int(row["declared_sessions"] or 0) for row in manifests),
            len(sessions),
        ),
        ("registered_root_sessions", 551, len(sessions)),
        ("registered_tool_actions", 181_303, event_total),
        ("overall_tool_family_sum", event_total, overall_family_calls),
        (
            "overall_shell_primary_sum",
            sum(event["_family"] == "shell" for event in events),
            overall_shell_primary,
        ),
        (
            "overall_session_metric_call_sum",
            event_total,
            sum(row["calls"] for row in session_metric_rows),
        ),
        (
            "same_prompt_source_stream_transition_sum",
            expected_same_prompt_transitions,
            overall_transitions,
        ),
        (
            "full_source_stream_transition_sum",
            expected_transitions,
            overall_full_stream_transitions,
        ),
        (
            "read_action_entry_sum",
            direct_read_action_entries,
            next(
                row["read_instances"]
                for row in repeated_read_rows
                if row["stratum_type"] == "overall"
                and row["analysis_unit"] == "source_stream"
                and row["prompt_scope"] == "full_stream"
                and row["evidence_source"] == "artifact_actions"
            ),
        ),
        (
            "source_path_read_entry_sum",
            direct_source_path_read_entries,
            next(
                row["read_instances"]
                for row in repeated_read_rows
                if row["stratum_type"] == "overall"
                and row["analysis_unit"] == "source_stream"
                and row["prompt_scope"] == "full_stream"
                and row["evidence_source"] == "source_paths_exact_path"
            ),
        ),
        (
            "native_batch_covered_calls",
            event_total if not args.no_native_batches else overall_parallel_covered,
            overall_parallel_covered,
        ),
    ]
    validation_rows = [
        {
            "check": name,
            "expected": expected,
            "actual": actual,
            "passed": expected == actual,
        }
        for name, expected, actual in validation_specs
    ]
    if not all(row["passed"] for row in validation_rows):
        failed = [row for row in validation_rows if not row["passed"]]
        raise RuntimeError(f"validation checks failed: {failed}")

    # Persist all tables.
    write_csv(
        output_dir / "input_manifest.csv",
        manifests,
        [
            "project",
            "selected_file",
            "selected_format",
            "bytes",
            "sha256",
            "events",
            "declared_sessions",
            "declared_source_events",
            "start_ms",
            "end_ms",
            "paired_gzip_present",
        ],
    )
    write_csv(output_dir / "schema_coverage.csv", schema_rows, list(schema_rows[0]))
    write_csv(
        output_dir / "native_source_coverage.csv",
        native_source_rows,
        [
            "project",
            "vendor",
            "source_file",
            "projected_events",
            "readable",
            "bytes",
            "sha256",
        ],
    )
    write_csv(
        output_dir / "corpus_coverage.csv",
        coverage_rows,
        [
            "stratum_type",
            "project",
            "vendor",
            "events",
            "sessions",
            "streams",
            "events_with_worktree",
            "worktree_coverage",
            "events_with_source_event_id",
            "events_with_artifact_actions",
            "artifact_action_event_coverage",
            "artifact_action_entries",
            "observed_status_events",
            "observed_status_share",
        ],
    )
    write_csv(
        output_dir / "tool_family_distribution.csv",
        family_rows,
        [
            "stratum_type",
            "project",
            "vendor",
            "tool_family",
            "calls",
            "share",
            "ok",
            "fail",
            "observed",
            "decisive_failure_rate",
            "observed_share",
        ],
    )
    write_csv(
        output_dir / "tool_name_distribution.csv",
        raw_tool_rows,
        [
            "stratum_type",
            "project",
            "vendor",
            "tool_name",
            "tool_family",
            "calls",
            "share",
            "ok",
            "fail",
            "observed",
            "decisive_failure_rate",
        ],
    )
    write_csv(
        output_dir / "tool_effect_distribution.csv",
        effect_rows,
        [
            "stratum_type",
            "project",
            "vendor",
            "tool_family",
            "source_category",
            "projected_effect",
            "calls",
            "share",
            "ok",
            "fail",
            "observed",
        ],
    )
    write_csv(
        output_dir / "shell_command_distribution.csv",
        shell_primary_rows + shell_multilabel_rows,
        [
            "stratum_type",
            "project",
            "vendor",
            "shell_class",
            "classification",
            "calls",
            "share_of_shell_calls",
        ],
    )
    write_csv(
        output_dir / "shell_command_name_distribution.csv",
        shell_command_name_rows,
        [
            "stratum_type",
            "project",
            "vendor",
            "command_name",
            "calls",
            "share_of_shell_calls",
        ],
    )
    write_csv(
        output_dir / "tool_ngrams.csv",
        ngram_rows,
        [
            "stratum_type",
            "project",
            "vendor",
            "sequence_scope",
            "sequence_granularity",
            "n",
            "rank",
            "ngram",
            "count",
            "share",
            "total_ngrams",
        ],
    )
    write_csv(
        output_dir / "markov_transitions.csv",
        transition_rows,
        [
            "stratum_type",
            "project",
            "vendor",
            "sequence_scope",
            "sequence_granularity",
            "from_family",
            "to_family",
            "count",
            "conditional_probability",
            "all_transition_share",
        ],
    )
    write_csv(
        output_dir / "same_family_runs.csv",
        run_rows,
        [
            "stratum_type",
            "project",
            "vendor",
            "sequence_scope",
            "tool_family",
            "run_n",
            "run_mean",
            "run_p50",
            "run_p90",
            "run_p95",
            "run_p99",
            "run_max",
            "runs_ge_3_share",
            "runs_ge_5_share",
        ],
    )
    write_csv(
        output_dir / "session_metrics.csv",
        session_metric_rows,
        list(session_metric_rows[0]),
    )
    write_csv(
        output_dir / "session_pace_summary.csv",
        session_pace_rows,
        list(session_pace_rows[0]),
    )
    write_csv(
        output_dir / "repeated_reads.csv",
        repeated_read_rows,
        list(repeated_read_rows[0]),
    )
    write_csv(
        output_dir / "shell_repetition.csv",
        shell_repeat_rows,
        list(shell_repeat_rows[0]),
    )
    write_csv(
        output_dir / "failure_rates.csv",
        failure_rate_rows,
        list(failure_rate_rows[0]),
    )
    write_csv(
        output_dir / "failure_followups.csv",
        failure_followup_rows,
        list(failure_followup_rows[0]),
    )
    write_csv(
        output_dir / "dependency_estimates.csv",
        dependency_rows,
        [
            "stratum_type",
            "project",
            "vendor",
            "analysis_scope",
            "classification",
            "reason",
            "adjacent_pairs",
            "share",
            "all_adjacent_pairs",
        ],
    )
    write_csv(
        output_dir / "parallel_usage.csv",
        parallel_usage_rows,
        list(parallel_usage_rows[0]),
    )
    write_csv(
        output_dir / "parallel_batches.csv",
        parallel_batch_rows,
        [
            "project",
            "vendor",
            "session_id",
            "source_stream_id",
            "source_file",
            "batch_id",
            "batch_size",
            "source_call_ids",
            "source_event_ids",
            "tool_families",
            "tool_names",
            "observable_path_relation",
            "timestamp_spread_ms",
        ],
    )
    write_csv(
        output_dir / "intercall_timing.csv",
        timing_rows,
        list(timing_rows[0]),
    )
    write_csv(
        output_dir / "source_duplication.csv",
        duplicate_rows,
        list(duplicate_rows[0]),
    )
    write_csv(
        output_dir / "validation_checks.csv",
        validation_rows,
        ["check", "expected", "actual", "passed"],
    )
    with (output_dir / "native_batch_coverage.json").open("w", encoding="utf-8") as handle:
        json.dump(batch_coverage, handle, ensure_ascii=False, indent=2, sort_keys=True)
        handle.write("\n")

    report = build_report(
        events_dir=events_dir,
        manifests=manifests,
        coverage_rows=coverage_rows,
        family_rows=family_rows,
        effect_rows=effect_rows,
        shell_rows=shell_primary_rows,
        shell_command_name_rows=shell_command_name_rows,
        ngram_rows=ngram_rows,
        transition_rows=transition_rows,
        run_rows=run_rows,
        pace_rows=session_pace_rows,
        repeated_read_rows=repeated_read_rows,
        shell_repeat_rows=shell_repeat_rows,
        failure_rate_rows=failure_rate_rows,
        failure_followup_rows=failure_followup_rows,
        dependency_rows=dependency_rows,
        parallel_rows=parallel_usage_rows,
        timing_rows=timing_rows,
        duplicate_rows=duplicate_rows,
        batch_coverage=batch_coverage,
        validation_rows=validation_rows,
    )
    with (output_dir / "report.md").open("w", encoding="utf-8") as handle:
        handle.write(report)

    print(f"wrote analysis to {output_dir}")
    print(f"events={len(events):,} sessions={len(sessions):,} streams={len(streams):,}")


def build_report(
    *,
    events_dir: Path,
    manifests: list[dict[str, Any]],
    coverage_rows: list[dict[str, Any]],
    family_rows: list[dict[str, Any]],
    effect_rows: list[dict[str, Any]],
    shell_rows: list[dict[str, Any]],
    shell_command_name_rows: list[dict[str, Any]],
    ngram_rows: list[dict[str, Any]],
    transition_rows: list[dict[str, Any]],
    run_rows: list[dict[str, Any]],
    pace_rows: list[dict[str, Any]],
    repeated_read_rows: list[dict[str, Any]],
    shell_repeat_rows: list[dict[str, Any]],
    failure_rate_rows: list[dict[str, Any]],
    failure_followup_rows: list[dict[str, Any]],
    dependency_rows: list[dict[str, Any]],
    parallel_rows: list[dict[str, Any]],
    timing_rows: list[dict[str, Any]],
    duplicate_rows: list[dict[str, Any]],
    batch_coverage: dict[str, Any],
    validation_rows: list[dict[str, Any]],
) -> str:
    def overall(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return [
            row
            for row in rows
            if row.get("project") == ALL and row.get("vendor") == ALL
        ]

    def projects(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return [
            row
            for row in rows
            if row.get("stratum_type") == "project"
        ]

    def vendors(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return [
            row
            for row in rows
            if row.get("stratum_type") == "vendor"
        ]

    lines: list[str] = []
    append = lines.append
    append("# Agent 工具调用行为的全量描述统计")
    append("")
    append(
        "本报告对冻结事件导出的 **551 个 root session、1,918 个 source stream、"
        "181,303 次 Tool action** 做确定性描述统计。它回答“Agent 实际怎样调用工具”，"
        "而不是评判任务质量、生产率或因果上的 vendor 优劣。"
    )
    append("")
    append("## 1. 数据、schema 与统计口径")
    append("")
    coverage_project_rows = sorted(projects(coverage_rows), key=lambda r: r["project"])
    append(
        md_table(
            ["项目", "Tool action", "root session", "source stream", "artifact-action coverage", "observed status"],
            [
                [
                    row["project"],
                    fmt_int(row["events"]),
                    fmt_int(row["sessions"]),
                    fmt_int(row["streams"]),
                    fmt_pct(row["artifact_action_event_coverage"]),
                    fmt_pct(row["observed_status_share"]),
                ]
                for row in coverage_project_rows
            ],
        )
    )
    append(
        "每个事件均有工具名、命令/参数摘要、毫秒时间戳、`ok/fail/observed` 状态、"
        "root session、source stream 和稳定的 tool ordinal；文件证据只在 `actions`"
        " 或 `source_paths` 出现时可用。序列、重试和相邻依赖的主单位是 source stream，"
        "因此不会把并行 subagent 的 root-timeline 交错误当成一条顺序链。"
    )
    append(
        "同目录的 `.json` 与 `.json.gz` 是配对导出，本脚本每项目只选择一个逻辑输入，"
        "优先未压缩 `.json`；`input_manifest.csv` 记录投影输入的 SHA-256、文件大小和"
        "事件数，`native_source_coverage.csv` 也记录并行批次重建所读原生日志的哈希。"
    )
    append(
        "时间戳只有调用开始时间，没有统一的调用结束时间，所以本文的时间指标是"
        "“前一调用开始到下一调用开始”的间隔，不能直接解释为工具执行 latency。"
    )
    append(
        "所有项目/vendor 对比都是观察性分层；任务、模型、日期、harness 与项目组成"
        "同时变化，不能把比例差异解释为 vendor 固有能力；overall 是 action-weighted"
        " 池化值，也不是六项目等权平均。"
    )
    append(
        f"`validation_checks.csv` 的 {fmt_int(len(validation_rows))} 个独立分母/守恒检查"
        "全部通过，包括输入事件和、session 和、工具族和、Shell 主类和、stream 转移和、"
        "artifact/source-path read 和 native batch 覆盖。"
    )
    append("")

    append("## 2. 工具类型分布")
    append("")
    overall_families = sorted(overall(family_rows), key=lambda r: -r["calls"])
    append(
        md_table(
            ["工具族", "调用数", "份额", "fail/(ok+fail)", "observed 份额"],
            [
                [
                    row["tool_family"],
                    fmt_int(row["calls"]),
                    fmt_pct(row["share"]),
                    fmt_pct(row["decisive_failure_rate"]),
                    fmt_pct(row["observed_share"]),
                ]
                for row in overall_families
            ],
        )
    )
    vendor_family_map = {
        (row["vendor"], row["tool_family"]): row
        for row in vendors(family_rows)
    }
    top_families = [row["tool_family"] for row in overall_families[:8]]
    vendor_names = sorted({row["vendor"] for row in vendors(family_rows)})
    append(
        md_table(
            ["vendor", *top_families],
            [
                [
                    vendor,
                    *[
                        fmt_pct(vendor_family_map.get((vendor, family), {}).get("share"))
                        for family in top_families
                    ],
                ]
                for vendor in vendor_names
            ],
        )
    )
    project_family_rows = projects(family_rows)
    project_top_families = []
    for project in sorted({row["project"] for row in project_family_rows}):
        subset = sorted(
            [row for row in project_family_rows if row["project"] == project],
            key=lambda row: -row["calls"],
        )[:3]
        project_top_families.append(
            [
                project,
                "; ".join(
                    f"{row['tool_family']} {fmt_pct(row['share'])}" for row in subset
                ),
            ]
        )
    append(md_table(["项目", "前三个工具族"], project_top_families))
    overall_effects = sorted(overall(effect_rows), key=lambda row: -row["calls"])[:12]
    append(
        md_table(
            ["工具族", "source category", "projected effect", "调用数", "份额"],
            [
                [
                    row["tool_family"],
                    row["source_category"],
                    row["projected_effect"],
                    fmt_int(row["calls"]),
                    fmt_pct(row["share"]),
                ]
                for row in overall_effects
            ],
        )
    )
    shell_share = next(
        row["share"] for row in overall_families if row["tool_family"] == "shell"
    )
    read_edit_write_share = sum(
        row["share"]
        for row in overall_families
        if row["tool_family"] in {"read", "edit", "write"}
    )
    orchestration_share = sum(
        row["share"]
        for row in overall_families
        if row["tool_family"] in {"task", "coordination", "wait/control"}
    )
    append(
        f"Shell 是主体（{fmt_pct(shell_share)}），但原生 read/edit/write 仍合计"
        f" {fmt_pct(read_edit_write_share)}；因此只按工具名统计 Bash/exec 会掩盖大量"
        " shell 内部的读取、测试和仓库操作。"
    )
    append(
        f"任务委派、协调和 wait/control 合计占 {fmt_pct(orchestration_share)}，"
        "说明“做工作”的调用和“管理并发/长任务”的调用在日志中形成可分离的控制平面。"
    )
    append(
        "vendor 表显示明显的接口语法差异（例如 Codex 的 apply_patch/wait、Claude 的"
        " Read/Edit/Agent）；这些差异既是行为，也是产品工具面设计造成的测量差异。"
    )
    append(
        "Gemini 只有 3 个 session、44 个调用，所有 Gemini 百分比都只是极小样本描述，"
        "不与 Claude/Codex 作稳定差异判断。"
    )
    append(
        "`tool_family_distribution.csv` 给出所有 project、vendor 和 project×vendor"
        " 单元；`tool_name_distribution.csv` 保留未经合并的原始工具名。"
    )
    append("")

    append("## 3. Shell 命令内部构成")
    append("")
    overall_shell = sorted(overall(shell_rows), key=lambda r: -r["calls"])
    append(
        md_table(
            ["Shell 主类", "调用数", "Shell 内份额"],
            [
                [row["shell_class"], fmt_int(row["calls"]), fmt_pct(row["share_of_shell_calls"])]
                for row in overall_shell
            ],
        )
    )
    overall_command_names = sorted(
        overall(shell_command_name_rows), key=lambda row: -row["calls"]
    )[:15]
    append(
        md_table(
            ["提取的 command_name", "调用数", "Shell 内份额"],
            [
                [
                    row["command_name"],
                    fmt_int(row["calls"]),
                    fmt_pct(row["share_of_shell_calls"]),
                ]
                for row in overall_command_names
            ],
        )
    )
    project_shell = projects(shell_rows)
    shell_top_by_project = []
    for project in sorted({row["project"] for row in project_shell}):
        subset = sorted(
            [row for row in project_shell if row["project"] == project],
            key=lambda r: -r["calls"],
        )[:3]
        shell_top_by_project.append(
            [
                project,
                "; ".join(
                    f"{row['shell_class']} {fmt_pct(row['share_of_shell_calls'])}"
                    for row in subset
                ),
            ]
        )
    append(md_table(["项目", "前三个 Shell 主类"], shell_top_by_project))
    append(
        "分类以完整命令字符串的可复算正则为基础；exporter 能可靠提取首命令时，"
        "`command_name` 会优先于参数/引号内的误命中，其他情况按 lint/format→test→"
        "build/check→container→package→git 的固定优先级选主类。含多个阶段的复合"
        "命令另在同一 CSV 的 `multi_label_presence` 行保留所有命中，避免把"
        " `git diff && cargo test` 简化成单一语义。"
    )
    append(
        "`command_name` 是 exporter 提取的首命令提示；Codex `exec` 中的 `const` 等值"
        "反映外层 JavaScript 包装，不应当成真实系统命令；这类无可靠提示的记录回退到"
        "完整命令文本分类。"
    )
    append(
        "search/text 与 filesystem/navigation 反映大量 shell 被当作通用读取接口；"
        "它们应与原生 Read/Grep 一起理解，而不应都算作“执行”。"
    )
    append(
        "lint/format、test 和 build/check 是命令语法识别，不等于检查覆盖了某次 edit，"
        "也不等于成功状态"
        "证明结果正确；这一口径比论文 RQ2 的 validation adapter 更宽，仅用于工具行为描述。"
    )
    append(
        "项目表说明 shell mix 具有明显案例依赖，因此跨项目池化份额只是 corpus 描述，"
        "不是六类项目总体发生率估计。"
    )
    append("")

    append("## 4. 调用序列、n-gram 与 Markov 转移")
    append("")
    overall_ngrams = [
        row
        for row in overall(ngram_rows)
        if row["sequence_scope"] == "same_prompt"
        and row["sequence_granularity"] == "tool_family"
    ]
    for n in (2, 3, 4):
        subset = sorted(
            [row for row in overall_ngrams if row["n"] == n],
            key=lambda r: r["rank"],
        )[:8]
        append(f"### {n}-gram 前 8")
        append("")
        append(
            md_table(
                ["rank", "工具链", "次数", "全部窗口份额"],
                [
                    [
                        fmt_int(row["rank"]),
                        row["ngram"],
                        fmt_int(row["count"]),
                        fmt_pct(row["share"]),
                    ]
                    for row in subset
                ],
            )
        )
    overall_transitions = sorted(
        [
            row
            for row in overall(transition_rows)
            if row["sequence_scope"] == "same_prompt"
            and row["sequence_granularity"] == "tool_family"
        ],
        key=lambda r: -r["count"],
    )[:15]
    append("### 高频 Markov 转移")
    append("")
    append(
        md_table(
            ["from", "to", "次数", "P(to|from)", "全部转移份额"],
            [
                [
                    row["from_family"],
                    row["to_family"],
                    fmt_int(row["count"]),
                    fmt_pct(row["conditional_probability"]),
                    fmt_pct(row["all_transition_share"]),
                ]
                for row in overall_transitions
            ],
        )
    )
    hybrid_ngrams = [
        row
        for row in overall(ngram_rows)
        if row["sequence_scope"] == "same_prompt"
        and row["sequence_granularity"] == "hybrid_shell"
        and row["n"] in {2, 3}
        and row["rank"] <= 10
    ]
    append("### Shell 展开后的 hybrid 工具链")
    append("")
    append(
        md_table(
            ["n", "rank", "工具链", "次数", "份额"],
            [
                [
                    fmt_int(row["n"]),
                    fmt_int(row["rank"]),
                    row["ngram"],
                    fmt_int(row["count"]),
                    fmt_pct(row["share"]),
                ]
                for row in sorted(hybrid_ngrams, key=lambda row: (row["n"], row["rank"]))
            ],
        )
    )
    overall_runs = sorted(
        [
            row
            for row in overall(run_rows)
            if row["sequence_scope"] == "same_prompt"
        ],
        key=lambda r: -r["run_n"],
    )
    long_run = max(overall_runs, key=lambda r: r["run_p90"] or 0)
    stratum_ngrams = [
        row
        for row in ngram_rows
        if row["stratum_type"] in {"project", "vendor"}
        and row["sequence_scope"] == "same_prompt"
        and row["sequence_granularity"] == "tool_family"
        and row["rank"] == 1
        and row["n"] in {2, 3}
    ]
    stratum_ngram_map = {
        (
            row["stratum_type"],
            row["project"] if row["stratum_type"] == "project" else row["vendor"],
            row["n"],
        ): row
        for row in stratum_ngrams
    }
    stratum_labels = sorted(
        {
            (
                row["stratum_type"],
                row["project"] if row["stratum_type"] == "project" else row["vendor"],
            )
            for row in stratum_ngrams
        }
    )
    append("### 项目与 vendor 的首位模式")
    append("")
    append(
        md_table(
            ["层", "top bigram", "份额", "top trigram", "份额"],
            [
                [
                    label,
                    stratum_ngram_map[(stype, label, 2)]["ngram"],
                    fmt_pct(stratum_ngram_map[(stype, label, 2)]["share"]),
                    stratum_ngram_map[(stype, label, 3)]["ngram"],
                    fmt_pct(stratum_ngram_map[(stype, label, 3)]["share"]),
                ]
                for stype, label in stratum_labels
                if (stype, label, 2) in stratum_ngram_map
                and (stype, label, 3) in stratum_ngram_map
            ],
        )
    )
    append(
        "主 n-gram 在每个 source stream 的同一 `prompt_index` 连续段内滑窗，"
        "不跨 prompt/root session，也不把多个 subagent stream 拼接；因此"
        " `read→edit→shell` 表示单次用户 prompt 下可观察的局部调用语法。"
    )
    append(
        "Markov 表给出一阶条件概率而非因果依赖；高 self-loop 既可能是批量独立读取，"
        "也可能是反复尝试，需要与文件重读和失败重试表联合解释。"
    )
    append(
        "`hybrid_shell` 只把 Shell token 展开为命令主类，其他原生工具族保持不变，"
        "用于显露 family-level `shell→shell` 下面的搜索、Git、测试与构建链条。"
    )
    append(
        f"同工具族 run 的长尾以 `{long_run['tool_family']}` 最明显："
        f"p90={fmt_float(long_run['run_p90'], 1)}、max={fmt_int(long_run['run_max'])}；"
        "这补充了 n-gram 的局部模式，显示某些行为以长 burst 出现。"
    )
    append(
        "完整 2–4 阶每层前 30 模式、所有 project/vendor 分层以及完整长格式转移矩阵"
        "分别在 `tool_ngrams.csv`、`markov_transitions.csv` 和"
        " `same_family_runs.csv`；三表同时保留 `full_stream` 敏感性口径。"
    )
    append("")

    append("## 5. 会话调用节奏、异质性与集中度")
    append("")
    pace_project_vendor = sorted(
        projects(pace_rows) + vendors(pace_rows),
        key=lambda r: (r["stratum_type"], r["project"], r["vendor"]),
    )
    append(
        md_table(
            ["层", "session", "calls p50/p90", "active span p50(h)", "capped-active calls/h p50", "switch p50", "Gini", "top 10% share"],
            [
                [
                    row["project"] if row["stratum_type"] == "project" else row["vendor"],
                    fmt_int(row["sessions"]),
                    f"{fmt_float(row['calls_p50'], 1)} / {fmt_float(row['calls_p90'], 1)}",
                    fmt_float(row["active_span_hours_p50"], 2),
                    fmt_float(row["calls_per_capped_active_hour_p50"], 1),
                    fmt_pct(row["stream_local_switch_rate_p50"]),
                    fmt_float(row["session_call_gini"], 2),
                    fmt_pct(row["top_10pct_sessions_call_share"]),
                ]
                for row in pace_project_vendor
            ],
        )
    )
    overall_pace = overall(pace_rows)[0]
    append(
        f"每 session 的调用量高度右偏：中位数 {fmt_float(overall_pace['calls_p50'], 1)}、"
        f"p90 {fmt_float(overall_pace['calls_p90'], 1)}、p99 "
        f"{fmt_float(overall_pace['calls_p99'], 1)}；top 10% session 承担"
        f" {fmt_pct(overall_pace['top_10pct_sessions_call_share'])} 的调用。"
    )
    append(
        "active span 是首末调用墙钟跨度，会包含用户离开；`capped-active calls/h` 把"
        "每个 source-stream 的同 prompt 相邻间隔最多计 5 分钟。其分子仍是 session"
        " 全部调用，所以单调用 prompt 只增加分子、不增加 active-time 分母，会使该"
        "启发式 burst 速率机械上偏；并行 stream 还会重复计算重叠墙钟，因此它不是"
        " token、root-session 墙钟或人工时间效率。"
    )
    append(
        "same-prompt stream-local switch rate 衡量工具族切换，不受 subagent 交错或"
        "新用户 prompt 边界影响；高切换可表示"
        "紧密 read/edit/test 循环，也可表示频繁上下文切换，不能单独赋予好坏。"
    )
    append(
        "`session_metrics.csv` 保留 551 个 session 的原始指标，便于识别极端会话；"
        "`session_pace_summary.csv` 给出项目、vendor 和交叉分层。"
    )
    append("")

    append("## 6. 重复与潜在冗余")
    append("")
    rr_rows = [
        row
        for row in repeated_read_rows
        if row["analysis_unit"] == "source_stream"
        and row["prompt_scope"] == "same_prompt"
        and row["stratum_type"] in {"overall", "project", "vendor"}
    ]
    append("### 同 prompt、source-stream 内的重复 read")
    append("")
    append(
        md_table(
            ["estimand", "层", "read instance", "重复份额", "无中间 mutation/重复", "重复 identity-unit", "call gap p50/p90", "time gap p50/p90(s)"],
            [
                [
                    (
                        "artifact identity"
                        if row["evidence_source"] == "artifact_actions"
                        else "exact source path"
                    ),
                    (
                        "overall"
                        if row["stratum_type"] == "overall"
                        else row["project"]
                        if row["stratum_type"] == "project"
                        else row["vendor"]
                    ),
                    fmt_int(row["read_instances"]),
                    fmt_pct(row["repeat_read_share"]),
                    fmt_pct(row["unchanged_share_among_repeats"]),
                    fmt_pct(row["repeated_group_identity_share"]),
                    f"{fmt_float(row['gap_calls_p50'], 1)} / {fmt_float(row['gap_calls_p90'], 1)}",
                    f"{fmt_float((row['gap_ms_p50'] or 0) / 1000, 1)} / {fmt_float((row['gap_ms_p90'] or 0) / 1000, 1)}",
                ]
                for row in rr_rows
            ],
        )
    )
    sr_rows = [
        row
        for row in shell_repeat_rows
        if row["analysis_unit"] == "source_stream"
        and row["prompt_scope"] == "same_prompt"
        and row["stratum_type"] in {"overall", "project", "vendor"}
    ]
    append("### 同 prompt、source-stream 内的 Shell 原样重跑")
    append("")
    append(
        md_table(
            ["层", "Shell call", "exact rerun", "immediate exact", "失败后立即原样重跑", "该重跑成功率"],
            [
                [
                    (
                        "overall"
                        if row["stratum_type"] == "overall"
                        else row["project"]
                        if row["stratum_type"] == "project"
                        else row["vendor"]
                    ),
                    fmt_int(row["shell_calls_with_command"]),
                    fmt_pct(row["exact_rerun_share"]),
                    fmt_pct(row["immediate_exact_rerun_share"]),
                    fmt_int(row["immediate_reruns_after_failure"]),
                    fmt_pct(row["failure_rerun_success_rate"]),
                ]
                for row in sr_rows
            ],
        )
    )
    rr_artifact_overall = next(
        row
        for row in rr_rows
        if row["stratum_type"] == "overall"
        and row["evidence_source"] == "artifact_actions"
    )
    rr_path_overall = next(
        row
        for row in rr_rows
        if row["stratum_type"] == "overall"
        and row["evidence_source"] == "source_paths_exact_path"
    )
    sr_overall = next(row for row in sr_rows if row["stratum_type"] == "overall")
    append(
        f"`actions` 给出 {fmt_int(rr_artifact_overall['read_instances'])} 个"
        f" artifact-identity read，其中 {fmt_pct(rr_artifact_overall['repeat_read_share'])}"
        " 在同 prompt 内重复；`source_paths` 给出"
        f" {fmt_int(rr_path_overall['read_instances'])} 个 exact-path read，对应重复率"
        f" {fmt_pct(rr_path_overall['repeat_read_share'])}。"
    )
    append(
        "artifact identity 可跨 rename 延续，exact path 则把 rename 前后视为不同路径；"
        "两者回答不同问题，不能把前者表述成纯“同路径”比例。"
    )
    append(
        f"两种 estimand 的重复读中，分别有"
        f" {fmt_pct(rr_artifact_overall['unchanged_share_among_repeats'])} 和"
        f" {fmt_pct(rr_path_overall['unchanged_share_among_repeats'])} 未观察到中间同 identity/path"
        " mutation；这只是潜在重复线索，不能排除外部修改、输出截断或合理的记忆刷新。"
    )
    append(
        f"Shell 的原样重跑率为 {fmt_pct(sr_overall['exact_rerun_share'])}，立即相邻原样"
        f"重跑率为 {fmt_pct(sr_overall['immediate_exact_rerun_share'])}；这里的 exact"
        " 指原始 command 字符串完全相等（不要求 vendor 原始工具名相同），前者包括"
        "合理的周期性 `git status`/测试，不能全部视为浪费。"
    )
    append(
        "`full_stream` 与 root-session 口径也保留在 CSV；前者允许跨用户 prompt 的"
        " re-grounding，后者还会合并不同 subagent，因此都不作为主要冗余估计。"
    )
    append("")

    append("## 7. 并行批次与顺序关系线索")
    append("")
    parallel_subset = sorted(
        overall(parallel_rows) + vendors(parallel_rows) + projects(parallel_rows),
        key=lambda r: (r["stratum_type"], r["project"], r["vendor"]),
    )
    append(
        md_table(
            ["层", "native coverage", "batch", "multi-call batch", "batched-call share", "batch max", "disjoint/shared/unknown multi-batch"],
            [
                [
                    (
                        "overall"
                        if row["stratum_type"] == "overall"
                        else row["project"]
                        if row["stratum_type"] == "project"
                        else row["vendor"]
                    ),
                    fmt_pct(row["native_batch_coverage"]),
                    fmt_int(row["batches"]),
                    f"{fmt_int(row['multi_call_batches'])} ({fmt_pct(row['multi_call_batch_share'])})",
                    fmt_pct(row["batched_call_share"]),
                    fmt_int(row["batch_size_max"]),
                    (
                        f"{fmt_int(row['disjoint_path_multi_batches'])} / "
                        f"{fmt_int(row['shared_path_multi_batches'])} / "
                        f"{fmt_int(row['unknown_dependency_multi_batches'])}"
                    ),
                ]
                for row in parallel_subset
            ],
        )
    )
    dep_subset = overall(dependency_rows)
    dep_class = Counter()
    for row in dep_subset:
        dep_class[row["classification"]] += row["adjacent_pairs"]
    dep_total = sum(dep_class.values())
    append(
        md_table(
            ["相邻调用分类", "pairs", "份额"],
            [
                [key, fmt_int(value), fmt_pct(value / dep_total)]
                for key, value in sorted(dep_class.items(), key=lambda item: -item[1])
            ],
        )
    )
    dep_strata = [
        row
        for row in dependency_rows
        if row["stratum_type"] in {"project", "vendor"}
    ]
    dep_stratum_counts: dict[tuple[str, str], Counter[str]] = defaultdict(Counter)
    for row in dep_strata:
        label = row["project"] if row["stratum_type"] == "project" else row["vendor"]
        dep_stratum_counts[(row["stratum_type"], label)][row["classification"]] += row[
            "adjacent_pairs"
        ]
    append(
        md_table(
            ["层", "dependency cue", "observed overlap", "observed disjoint", "unknown"],
            [
                [
                    label,
                    fmt_pct(
                        safe_div(values["dependency_cue"], sum(values.values()))
                    ),
                    fmt_pct(
                        safe_div(values["observed_overlap"], sum(values.values()))
                    ),
                    fmt_pct(
                        safe_div(values["observed_disjoint"], sum(values.values()))
                    ),
                    fmt_pct(safe_div(values["unknown"], sum(values.values()))),
                ]
                for (_stype, label), values in sorted(dep_stratum_counts.items())
            ],
        )
    )
    parallel_overall = overall(parallel_rows)[0]
    append(
        f"native batch 重建覆盖 {fmt_pct(parallel_overall['native_batch_coverage'])}"
        f" 的调用；其中 {fmt_pct(parallel_overall['batched_call_share'])} 位于同一 assistant"
        " message/response batch 的多调用批次。这证明“发出多个调用”的原生并行机会，"
        "但无统一结束时间，不能证明这些调用在墙钟上实际重叠。"
    )
    append(
        "池化比例几乎全部来自 Codex（41.7% 的 covered call）和极小的 Gemini 子样本；"
        "Claude 的 36,826 个调用中没有同一 assistant event 的多 tool_use，"
        "所以不能把 33.2% 当成跨 vendor 的一般发生率。"
    )
    append(
        "Claude 用同一 assistant JSONL 事件中的多个 `tool_use`，Codex 用首个 call output"
        " 前连续的 `*_call`，Gemini 用同一 message 的 `toolCalls` 数组重建；"
        "`native_batch_coverage.json` 记录可读源文件与映射覆盖，"
        "`parallel_batches.csv` 保留 source file、call ID 和 event ID 供逐批审计。"
    )
    append(
        "同 prompt 相邻调用只把失败原样重试、edit/write→test/build/lint 和"
        " shell/task→wait/control 或 coordination 记为 `dependency_cue`；共享"
        " artifact/path 仅记 `observed_overlap`，不自动当成顺序依赖。"
    )
    append(
        "双方 path 非空且不相交只记 `observed_disjoint`，并不证明独立；unknown 往往"
        "来自 shell/网络/控制工具缺少 path 证据。因此这里能给出依赖线索的下界，"
        "不能给出可信的“独立调用率”；CSV 按具体证据原因拆分。"
    )
    append("")

    append("## 8. 失败率与失败后的行为")
    append("")
    overall_failure_family = sorted(
        [
            row
            for row in overall(failure_rate_rows)
            if row["grouping"] == "tool_family"
        ],
        key=lambda r: -r["calls"],
    )
    append(
        md_table(
            ["工具族", "calls", "decisive calls", "fail", "fail/(ok+fail)", "observed"],
            [
                [
                    row["tool_group"],
                    fmt_int(row["calls"]),
                    fmt_int(row["decisive_calls"]),
                    fmt_int(row["fail"]),
                    fmt_pct(row["decisive_failure_rate"]),
                    fmt_pct(row["observed_share"]),
                ]
                for row in overall_failure_family
            ],
        )
    )
    fail_stratum_rows = [
        row
        for row in failure_rate_rows
        if row["stratum_type"] in {"project", "vendor"}
        and row["grouping"] == "tool_family"
    ]
    fail_totals: dict[tuple[str, str], Counter[str]] = defaultdict(Counter)
    for row in fail_stratum_rows:
        label = row["project"] if row["stratum_type"] == "project" else row["vendor"]
        fail_totals[(row["stratum_type"], label)].update(
            {
                "ok": row["ok"],
                "fail": row["fail"],
                "observed": row["observed"],
                "calls": row["calls"],
            }
        )
    append(
        md_table(
            ["层", "calls", "fail/(ok+fail)", "observed 份额"],
            [
                [
                    label,
                    fmt_int(values["calls"]),
                    fmt_pct(safe_div(values["fail"], values["ok"] + values["fail"])),
                    fmt_pct(safe_div(values["observed"], values["calls"])),
                ]
                for (_stype, label), values in sorted(fail_totals.items())
            ],
        )
    )
    overall_followups = [
        row
        for row in overall(failure_followup_rows)
        if row["window"] == "next_call"
    ]
    followup_behavior_counts: Counter[str] = Counter()
    for row in overall_followups:
        followup_behavior_counts[row["behavior"]] += row["count"]
    follow_total = sum(followup_behavior_counts.values())
    append(
        md_table(
            ["失败后的下一 Tool 行为", "次数", "份额"],
            [
                [behavior, fmt_int(count), fmt_pct(count / follow_total)]
                for behavior, count in followup_behavior_counts.most_common()
            ],
        )
    )
    total_ok = sum(row["ok"] for row in overall_failure_family)
    total_fail = sum(row["fail"] for row in overall_failure_family)
    total_observed = sum(row["observed"] for row in overall_failure_family)
    append(
        f"全量共有 {fmt_int(total_fail)} 个 fail；在有明确 ok/fail 的调用中失败率为"
        f" {fmt_pct(safe_div(total_fail, total_ok + total_fail))}。另有"
        f" {fmt_int(total_observed)} 个 observed 状态，它们是结果未知/仅观测，不能放进"
        "成功率分母当作成功。"
    )
    append(
        "失败后的第一步只在同一 prompt 连续段内按 exact retry、非 Shell 原始工具改参数、"
        "通用 Shell 更换命令"
        "（同/不同命令类）、同工具族换工具、切换工具族和 stream 结束拆分；"
        "`end_of_prompt` 单列为保守的放弃/转入下一用户指示代理量，`within_3_calls`"
        " 也不会跨 prompt。"
    )
    append(
        "失败率同时受工具接口的 status 语义影响，尤其 observed 比例在 vendor 间差异大；"
        "因此 vendor 失败率只在各自 decisive 子集内描述，不作能力排名。"
    )
    append(
        "原始工具名层面的长尾（例如具体 MCP/API 工具）在 `failure_rates.csv` 中完整"
        "保留，可用于定位家族汇总掩盖的高失败工具。"
    )
    append("")

    append("## 9. 时间结构与长尾等待")
    append("")
    timing_overall = [
        row
        for row in overall(timing_rows)
        if row["scope"] == "same_prompt" and row["preceding_tool_family"] != ALL
    ]
    timing_overall.sort(key=lambda r: -(r["gap_ms_p99"] or 0))
    append(
        md_table(
            ["前一工具族", "gap", "p50(s)", "p90(s)", "p99(s)", ">60s", "占全部 >60s gap"],
            [
                [
                    row["preceding_tool_family"],
                    fmt_int(row["gaps"]),
                    fmt_float((row["gap_ms_p50"] or 0) / 1000, 2),
                    fmt_float((row["gap_ms_p90"] or 0) / 1000, 2),
                    fmt_float((row["gap_ms_p99"] or 0) / 1000, 2),
                    fmt_pct(row["gap_gt_60s_share"]),
                    fmt_pct(row["share_of_stratum_gaps_gt_60s"]),
                ]
                for row in timing_overall
            ],
        )
    )
    timing_all = next(
        row
        for row in overall(timing_rows)
        if row["scope"] == "same_prompt" and row["preceding_tool_family"] == ALL
    )
    top_long_gap = max(
        timing_overall,
        key=lambda r: r["share_of_stratum_gaps_gt_60s"] or 0,
    )
    timing_strata = sorted(
        [
            row
            for row in timing_rows
            if row["stratum_type"] in {"project", "vendor"}
            and row["scope"] == "same_prompt"
            and row["preceding_tool_family"] == ALL
        ],
        key=lambda row: (row["stratum_type"], row["project"], row["vendor"]),
    )
    append("### 项目与 vendor 的同 prompt gap")
    append("")
    append(
        md_table(
            ["层", "gap", "p50(s)", "p90(s)", "p99(s)", ">60s"],
            [
                [
                    row["project"] if row["stratum_type"] == "project" else row["vendor"],
                    fmt_int(row["gaps"]),
                    fmt_float((row["gap_ms_p50"] or 0) / 1000, 2),
                    fmt_float((row["gap_ms_p90"] or 0) / 1000, 2),
                    fmt_float((row["gap_ms_p99"] or 0) / 1000, 2),
                    fmt_pct(row["gap_gt_60s_share"]),
                ]
                for row in timing_strata
            ],
        )
    )
    append(
        f"同一 prompt 内的相邻 source-stream 调用，p50="
        f"{fmt_float((timing_all['gap_ms_p50'] or 0)/1000, 2)}s、p90="
        f"{fmt_float((timing_all['gap_ms_p90'] or 0)/1000, 2)}s、p99="
        f"{fmt_float((timing_all['gap_ms_p99'] or 0)/1000, 2)}s；"
        f"{fmt_pct(timing_all['gap_gt_60s_share'])} 超过 60 秒。"
    )
    append(
        f"`{top_long_gap['preceding_tool_family']}` 对全部 >60s gap 的计数贡献最大"
        f"（{fmt_pct(top_long_gap['share_of_stratum_gaps_gt_60s'])}），但这只是“长间隔"
        "前一个可见工具”的归属，间隔还包含模型推理、工具执行、调度和潜在用户等待。"
    )
    append(
        "same-prompt 口径排除了显式新 prompt 边界的大部分用户离线时间；"
        "`all_adjacent` 口径仍保留在 CSV，可用于完整墙钟轨迹。"
    )
    append(
        "没有 end timestamp 时，不能回答真实 runtime 或工具内部等待；要做 latency 研究"
        "需回到原生 tool_result/runner duration 字段，不能从本表反推。"
    )
    append("")

    append("## 10. 数据记录重复与稳健性提醒")
    append("")
    duplicate_subset = overall(duplicate_rows) + projects(duplicate_rows) + vendors(duplicate_rows)
    append(
        md_table(
            ["层", "calls", "重复 source-call ID 组", "跨 stream / core 完全一致", "首条之外记录", "份额"],
            [
                [
                    (
                        "overall"
                        if row["stratum_type"] == "overall"
                        else row["project"]
                        if row["stratum_type"] == "project"
                        else row["vendor"]
                    ),
                    fmt_int(row["calls"]),
                    fmt_int(row["duplicated_id_groups"]),
                    (
                        f"{fmt_int(row['cross_stream_duplicated_groups'])} / "
                        f"{fmt_int(row['exact_core_duplicated_groups'])}"
                    ),
                    fmt_int(row["duplicate_records_beyond_first"]),
                    fmt_pct(row["duplicate_records_beyond_first_share"]),
                ]
                for row in duplicate_subset
            ],
        )
    )
    duplicate_overall = overall(duplicate_rows)[0]
    append(
        f"冻结投影中有 {fmt_int(duplicate_overall['duplicate_records_beyond_first'])}"
        " 条记录与同项目/vendor 的既有 `source_call_id` 重复，约占"
        f" {fmt_pct(duplicate_overall['duplicate_records_beyond_first_share'])}。"
    )
    append(
        f"{fmt_int(duplicate_overall['duplicated_id_groups'])} 个重复组全部跨 source stream、"
        "跨 source file，且 tool/command/status/timestamp 核心字段完全一致；这符合"
        " resumed/copied native stream 的同一源调用再次进入投影的特征。"
    )
    append(
        "本报告保持注册的 181,303 action 分母，不擅自去重，但把该比例单列。"
    )
    append(
        "stream-local 重读、重跑和 n-gram 可能受这种复制轻微影响；按 source-call ID"
        " 去重会改变“记录行为”与“Agent 实际执行行为”的 estimand，需另行预注册。"
    )
    append(
        "项目/vendor 分层可以定位重复集中位置，后续若把这些统计写入论文，建议同时给出"
        "保留全部记录与 source-call 去重的敏感性版本。"
    )
    append("")

    append("## 11. 可能之前 empirical study 没覆盖的发现")
    append("")
    append(
        "下面是相对于当前 RQ1（artifact fate/reuse）、RQ2（mutation-validation）、"
        "RQ3（workspace focus）、RQ4（component continuity）和 RQ5（skill footprint）"
        "最可能新增的观察角度；它们是候选发现，不自动升级为论文 claim。"
    )
    append("")
    top_bigram = min(
        [
            row
            for row in overall(ngram_rows)
            if row["n"] == 2
            and row["sequence_scope"] == "same_prompt"
            and row["sequence_granularity"] == "tool_family"
        ],
        key=lambda r: r["rank"],
    )
    append(
        f"- **工具语法而非 artifact 语法：** 最常见 bigram 是"
        f" `{top_bigram['ngram']}`（{fmt_pct(top_bigram['share'])}）；2–4 阶链和"
        " Markov self-loop/switch 描述了 Agent 的局部操作 grammar，现有 RQ 没有系统"
        "比较这种 grammar。"
    )
    append(
        f"- **控制平面开销：** task、coordination、wait/control 合计"
        f" {fmt_pct(orchestration_share)} 的调用，可单独研究“产出动作”和“管理并发/等待”"
        "的比例、burst 与失败面。"
    )
    append(
        f"- **原生多调用批次很少/很常用到什么程度：** 可映射调用中"
        f" {fmt_pct(parallel_overall['batched_call_share'])} 位于 multi-call batch；"
        "此前 component 分析区分并行 subagent，但没有量化同一 assistant turn 的"
        " batched tool use。"
    )
    append(
        f"- **无可见状态变化的重读：** 同 prompt 重复 read 中，artifact identity"
        f" 口径有 {fmt_pct(rr_artifact_overall['unchanged_share_among_repeats'])}、"
        f"exact-path 口径有 {fmt_pct(rr_path_overall['unchanged_share_among_repeats'])}"
        " 未观察到中间 mutation；两种 estimand 的差异本身就是需要报告的测量边界。"
    )
    append(
        f"- **命令级重试与周期性复查：** exact shell rerun 占"
        f" {fmt_pct(sr_overall['exact_rerun_share'])}；把失败后的原样重跑、改参数、换工具"
        "和成功后的周期性复查分开，可以形成更细的 recovery taxonomy。"
    )
    append(
        f"- **调用量集中在少数超长 session：** top 10% session 占"
        f" {fmt_pct(overall_pace['top_10pct_sessions_call_share'])} 的调用，说明以"
        "“平均 session”为中心会漏掉 corpus 的主要行为质量；应报告 session-level"
        "分布或按 root block 加权。"
    )
    append(
        f"- **长尾是 next-call lag，不只是 test/build 等待：** 同 prompt gap 的 p99"
        f" 达 {fmt_float((timing_all['gap_ms_p99'] or 0)/1000, 1)}s，且长尾贡献按前一"
        "工具族高度不均；需要带 end timestamp 的后续研究拆分模型思考、工具 runtime"
        "和调度等待。"
    )
    append(
        f"- **状态语义本身是 vendor 测量偏差：** observed 状态共有"
        f" {fmt_int(total_observed)} 次；若把它默认当成功，会系统性改变失败率和恢复路径。"
    )
    append(
        f"- **source stream 复制是行为统计的隐藏敏感性：**"
        f" {fmt_pct(duplicate_overall['duplicate_records_beyond_first_share'])} 的记录是"
        "同项目/vendor 下重复 source-call ID；长期轨迹研究需要明确“记录实例”还是"
        "“唯一执行调用”作为 estimand。"
    )
    append(
        "- **可观察依赖的覆盖缺口：** retry/validation/control handoff 只能提供保守"
        " dependency cue，path overlap/disjoint 都不能分别证明依赖/独立；大量 pair"
        "仍是 unknown，说明只靠 file effects 无法恢复完整工具依赖 DAG。"
    )
    append("")

    append("## 12. 复算与产物索引")
    append("")
    append("复算命令：")
    append("")
    append("```bash")
    append(
        "python3 docs/tmp/build-and-evaluate/toolcall-behavior-20260726/"
        "analyze_toolcalls.py \\"
    )
    append(
        "  --events-dir docs/tmp/build-and-evaluate/rq1-rq4-recompute-final/"
        "rq1-raw/events \\"
    )
    append(
        "  --output-dir docs/tmp/build-and-evaluate/toolcall-behavior-20260726"
    )
    append("```")
    append("")
    append("主要 CSV：")
    append("")
    append("- `corpus_coverage.csv`, `schema_coverage.csv`, `input_manifest.csv`, `native_source_coverage.csv`")
    append("- `tool_family_distribution.csv`, `tool_name_distribution.csv`, `tool_effect_distribution.csv`")
    append("- `shell_command_distribution.csv`, `shell_command_name_distribution.csv`")
    append("- `tool_ngrams.csv`, `markov_transitions.csv`, `same_family_runs.csv`")
    append("- `session_metrics.csv`, `session_pace_summary.csv`, `intercall_timing.csv`")
    append("- `repeated_reads.csv`, `shell_repetition.csv`")
    append("- `failure_rates.csv`, `failure_followups.csv`")
    append("- `parallel_usage.csv`, `parallel_batches.csv`, `dependency_estimates.csv`")
    append("- `source_duplication.csv`, `native_batch_coverage.json`")
    append("- `validation_checks.csv`")
    append("")
    append(
        f"输入目录：`{events_dir}`。本次分析未修改 `docs/paper/`，没有执行 git 写操作。"
    )
    append("")
    return "\n".join(lines)


if __name__ == "__main__":
    main()
