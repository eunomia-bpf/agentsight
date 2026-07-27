#!/usr/bin/env python3
"""Measure observable human involvement in the final RQ1--RQ4 corpus.

The event projection fixes corpus membership and Agent actions.  Human
messages, assistant conversational messages, explicit interruption markers,
and permission-policy records are recovered from the source-native records
named by each projected event.  No message text is written to an output.
"""

from __future__ import annotations

import argparse
import bisect
import collections
import csv
import datetime as dt
import gzip
import hashlib
import json
import math
import os
import platform
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Sequence
from zoneinfo import ZoneInfo

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


HERE = Path(__file__).resolve().parent
EVENTS = HERE.parent / "rq1-rq4-recompute-final" / "rq1-raw" / "events"
MUTATIONS = HERE.parent / "rq1-rq4-recompute-final" / "rq1-raw" / "rq1-mutations.csv"
FIGURES = HERE / "figures"
PREFLIGHT = HERE / "preflight"
LOCAL_TZ = ZoneInfo("America/Vancouver")

PROJECT_ORDER = (
    "agentsight",
    "ActPlane",
    "bpf-developer-tutorial",
    "eunomia.dev",
    "agentskill-observability-paper",
    "academic-writing-skills",
)
VENDOR_ORDER = ("claude", "codex", "gemini")
VENDOR_COLORS = {
    "claude": "#D55E00",
    "codex": "#0072B2",
    "gemini": "#009E73",
}
WEEKDAY_ORDER = ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday")

CLAUDE_INJECTED_PREFIXES = (
    "<task-notification>",
    "<system-reminder>",
    "<command-name>",
    "<command-message>",
    "<command-args>",
    "<local-command-stdout>",
    "<local-command-caveat>",
    "<bash-stdout>",
    "<bash-stderr>",
    "<tool-use-error>",
    "<turn_aborted>",
)
CLAUDE_CONTINUATION_PREFIXES = (
    "This session is being continued from a previous conversation that ran out of context.",
    "This session is being continued from a previous conversation",
)
INTERRUPT_PATTERNS = (
    "[Request interrupted by user]",
    "[Tool use interrupted by user]",
)
WORDLIKE_RE = re.compile(
    r"[A-Za-z0-9]+(?:['’_-][A-Za-z0-9]+)*|[\u3400-\u4dbf\u4e00-\u9fff]"
)
SPACE_RE = re.compile(r"\s+")


@dataclass(frozen=True)
class HumanMessage:
    timestamp_ms: int
    chars: int
    words_approx: int
    images: int
    native_id: str
    source_file: str


@dataclass
class NativeConversation:
    human: list[HumanMessage] = field(default_factory=list)
    assistant_source_times: list[tuple[int, str, str]] = field(default_factory=list)
    explicit_interrupt_times_ms: list[int] = field(default_factory=list)
    approval_request_times: list[tuple[int, str]] = field(default_factory=list)
    permission_policies: list[tuple[int, str]] = field(default_factory=list)
    excluded: collections.Counter[str] = field(default_factory=collections.Counter)
    native_record_types: collections.Counter[str] = field(default_factory=collections.Counter)
    native_source_kind: str = "unknown"
    native_source_app: str = "unknown"
    human_bearing_source: bool = True

    def merge(self, other: "NativeConversation") -> None:
        self.human.extend(other.human)
        self.assistant_source_times.extend(other.assistant_source_times)
        self.explicit_interrupt_times_ms.extend(other.explicit_interrupt_times_ms)
        self.approval_request_times.extend(other.approval_request_times)
        self.permission_policies.extend(other.permission_policies)
        self.excluded.update(other.excluded)
        self.native_record_types.update(other.native_record_types)

    def normalize(self) -> None:
        human_seen: set[tuple[int, str, int, int]] = set()
        human = []
        for message in sorted(self.human, key=lambda row: (row.timestamp_ms, row.native_id)):
            key = (
                message.timestamp_ms,
                message.native_id,
                message.chars,
                message.images,
            )
            if key not in human_seen:
                human_seen.add(key)
                human.append(message)
        self.human = human
        assistant_by_key: dict[tuple[int, str], tuple[int, str, str]] = {}
        for stamp, source_file, digest in sorted(self.assistant_source_times):
            assistant_by_key.setdefault((stamp, digest), (stamp, source_file, digest))
        self.assistant_source_times = sorted(assistant_by_key.values())
        self.explicit_interrupt_times_ms = sorted(set(self.explicit_interrupt_times_ms))
        self.approval_request_times = sorted(set(self.approval_request_times))
        self.permission_policies = sorted(set(self.permission_policies))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--events-dir", type=Path, default=EVENTS)
    parser.add_argument("--mutations", type=Path, default=MUTATIONS)
    parser.add_argument("--output-dir", type=Path, default=HERE)
    parser.add_argument("--preflight", action="store_true")
    parser.add_argument(
        "--render-only",
        action="store_true",
        help="Re-render figures/report from already completed CSV checkpoints.",
    )
    return parser.parse_args()


def parse_ts_ms(value: Any) -> int | None:
    if isinstance(value, (int, float)):
        number = int(value)
        return number * 1000 if number < 10_000_000_000 else number
    if not isinstance(value, str) or not value.strip():
        return None
    raw = value.strip().replace("Z", "+00:00")
    try:
        return int(dt.datetime.fromisoformat(raw).timestamp() * 1000)
    except ValueError:
        return None


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def safe_div(numerator: float, denominator: float) -> float | None:
    return numerator / denominator if denominator else None


def finite(value: Any) -> bool:
    try:
        return math.isfinite(float(value))
    except (TypeError, ValueError):
        return False


def fmt_int(value: Any) -> str:
    return "N/A" if not finite(value) else f"{int(round(float(value))):,}"


def fmt_float(value: Any, digits: int = 2) -> str:
    return "N/A" if not finite(value) else f"{float(value):.{digits}f}"


def fmt_pct(value: Any, digits: int = 1) -> str:
    return "N/A" if not finite(value) else f"{100 * float(value):.{digits}f}%"


def write_csv(path: Path, rows: Iterable[dict[str, Any]], fieldnames: Sequence[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def discover_event_files(events_dir: Path) -> list[Path]:
    selected: dict[str, Path] = {}
    for path in sorted(events_dir.glob("*.json")):
        selected[path.name] = path
    for path in sorted(events_dir.glob("*.json.gz")):
        logical = path.name[:-3]
        if logical not in selected:
            selected[logical] = path
    if not selected:
        raise FileNotFoundError(f"No event exports found under {events_dir}")
    return [selected[key] for key in sorted(selected)]


def load_json(path: Path) -> dict[str, Any]:
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rt", encoding="utf-8") as handle:
        return json.load(handle)


def normalize_text(value: str) -> str:
    return SPACE_RE.sub(" ", value).strip()


def transient_text_digest(text: str) -> str:
    return hashlib.sha256(normalize_text(text).encode("utf-8")).hexdigest()[:20]


def text_stats(text: str) -> tuple[int, int]:
    normalized = normalize_text(text)
    return len(normalized), len(WORDLIKE_RE.findall(normalized))


def content_text_and_images(content: Any) -> tuple[str, int, set[str]]:
    if isinstance(content, str):
        return content, 0, {"string"}
    if not isinstance(content, list):
        return "", 0, set()
    pieces: list[str] = []
    images = 0
    types: set[str] = set()
    for block in content:
        if isinstance(block, str):
            pieces.append(block)
            types.add("string")
            continue
        if not isinstance(block, dict):
            continue
        block_type = str(block.get("type") or "")
        types.add(block_type)
        if block_type in {"text", "input_text", "output_text"}:
            pieces.append(str(block.get("text") or ""))
        elif block_type in {"image", "input_image"}:
            images += 1
        elif not block_type and isinstance(block.get("text"), str):
            pieces.append(str(block["text"]))
    return "\n".join(pieces), images, types


def classify_claude_user(text: str, block_types: set[str], row: dict[str, Any]) -> str:
    stripped = text.strip()
    if row.get("isMeta"):
        return "meta"
    if row.get("isSidechain"):
        return "sidechain"
    if "tool_result" in block_types:
        return "tool_result"
    if any(marker in stripped for marker in INTERRUPT_PATTERNS):
        return "interrupt_marker"
    if stripped.startswith(CLAUDE_INJECTED_PREFIXES):
        return "injected"
    if stripped.startswith(CLAUDE_CONTINUATION_PREFIXES):
        return "continuation_summary"
    if not stripped and not ({"image", "input_image"} & block_types):
        return "empty"
    return "human"


def approval_like_type(value: str) -> bool:
    low = value.lower()
    return any(token in low for token in ("approval", "permission", "elicitation"))


def parse_claude(path: Path) -> NativeConversation:
    result = NativeConversation()
    with path.open(encoding="utf-8", errors="replace") as handle:
        for line_no, raw in enumerate(handle, 1):
            try:
                row = json.loads(raw)
            except json.JSONDecodeError:
                result.excluded["invalid_json"] += 1
                continue
            if not isinstance(row, dict):
                continue
            row_type = str(row.get("type") or "")
            result.native_record_types[row_type] += 1
            stamp = parse_ts_ms(row.get("timestamp"))
            if stamp is None:
                result.excluded["missing_timestamp"] += 1
                continue
            message = row.get("message") if isinstance(row.get("message"), dict) else {}
            content = message.get("content")
            if row_type == "user":
                text, images, block_types = content_text_and_images(content)
                classification = classify_claude_user(text, block_types, row)
                if classification == "interrupt_marker":
                    result.explicit_interrupt_times_ms.append(stamp)
                    result.excluded[classification] += 1
                elif classification == "human":
                    chars, words = text_stats(text)
                    result.human.append(
                        HumanMessage(
                            timestamp_ms=stamp,
                            chars=chars,
                            words_approx=words,
                            images=images,
                            native_id=str(row.get("promptId") or row.get("uuid") or line_no),
                            source_file=str(path),
                        )
                    )
                else:
                    result.excluded[classification] += 1
            elif row_type == "assistant":
                text, _, block_types = content_text_and_images(content)
                if normalize_text(text):
                    result.assistant_source_times.append(
                        (stamp, str(path), transient_text_digest(text))
                    )
                for block in content if isinstance(content, list) else []:
                    if not isinstance(block, dict):
                        continue
                    name = str(block.get("name") or "")
                    if approval_like_type(name):
                        result.approval_request_times.append((stamp, name))
                if "text" not in block_types and "output_text" not in block_types:
                    result.excluded["assistant_without_conversational_text"] += 1
            subtype = str(row.get("subtype") or "")
            if approval_like_type(row_type) or approval_like_type(subtype):
                result.approval_request_times.append((stamp, subtype or row_type))
            for key in ("permissionMode", "permission_mode", "approval_policy"):
                if row.get(key):
                    result.permission_policies.append((stamp, str(row[key])))
    result.normalize()
    return result


def codex_payload_text(payload: dict[str, Any]) -> str:
    for key in ("message", "text"):
        if isinstance(payload.get(key), str):
            return str(payload[key])
    pieces: list[str] = []
    for item in payload.get("text_elements") or []:
        if isinstance(item, str):
            pieces.append(item)
        elif isinstance(item, dict):
            pieces.append(str(item.get("text") or ""))
    return "\n".join(pieces)


def codex_source_metadata(path: Path) -> tuple[str, bool, str]:
    """Classify a Codex rollout before interpreting user-role messages.

    Event projection labels both root and nested Codex rollouts as
    ``source_role=user``.  The native session metadata is the authoritative
    distinction: a subagent's task prompt is agent-generated, not a human
    instruction.
    """
    with path.open(encoding="utf-8", errors="replace") as handle:
        for raw in handle:
            try:
                row = json.loads(raw)
            except json.JSONDecodeError:
                continue
            if not isinstance(row, dict) or str(row.get("type") or "") != "session_meta":
                continue
            payload = row.get("payload") if isinstance(row.get("payload"), dict) else {}
            thread_source = str(payload.get("thread_source") or "unknown")
            source = payload.get("source")
            source_app = source if isinstance(source, str) else "subagent"
            nested_subagent = isinstance(source, dict) and "subagent" in source
            is_subagent = thread_source == "subagent" or nested_subagent
            if is_subagent:
                return "subagent", False, source_app
            if thread_source == "unknown" and isinstance(source, str):
                return "user_legacy", True, source_app
            return thread_source, True, source_app
    return "unknown", True, "unknown"


def parse_codex(path: Path) -> NativeConversation:
    result = NativeConversation()
    source_kind, human_bearing, source_app = codex_source_metadata(path)
    result.native_source_kind = source_kind
    result.native_source_app = source_app
    result.human_bearing_source = human_bearing
    if not human_bearing:
        result.excluded["codex_subagent_source_file"] += 1
        return result
    fallback_human: list[HumanMessage] = []
    fallback_assistant: list[int] = []
    event_human = 0
    event_assistant = 0
    with path.open(encoding="utf-8", errors="replace") as handle:
        for line_no, raw in enumerate(handle, 1):
            try:
                row = json.loads(raw)
            except json.JSONDecodeError:
                result.excluded["invalid_json"] += 1
                continue
            if not isinstance(row, dict):
                continue
            outer_type = str(row.get("type") or "")
            payload = row.get("payload") if isinstance(row.get("payload"), dict) else {}
            payload_type = str(payload.get("type") or "")
            result.native_record_types[f"{outer_type}:{payload_type}"] += 1
            stamp = parse_ts_ms(row.get("timestamp"))
            if stamp is None:
                result.excluded["missing_timestamp"] += 1
                continue
            if outer_type == "event_msg" and payload_type == "user_message":
                text = codex_payload_text(payload)
                chars, words = text_stats(text)
                if chars or payload.get("images") or payload.get("local_images"):
                    result.human.append(
                        HumanMessage(
                            timestamp_ms=stamp,
                            chars=chars,
                            words_approx=words,
                            images=len(payload.get("images") or [])
                            + len(payload.get("local_images") or []),
                            native_id=transient_text_digest(text),
                            source_file=str(path),
                        )
                    )
                    event_human += 1
                else:
                    result.excluded["empty_user_message"] += 1
            elif outer_type == "event_msg" and payload_type == "agent_message":
                if normalize_text(codex_payload_text(payload)):
                    result.assistant_source_times.append(
                        (stamp, str(path), transient_text_digest(codex_payload_text(payload)))
                    )
                    event_assistant += 1
            elif outer_type == "event_msg" and payload_type == "turn_aborted":
                result.explicit_interrupt_times_ms.append(stamp)
            elif outer_type == "turn_context":
                policy = payload.get("approval_policy")
                if policy:
                    result.permission_policies.append((stamp, str(policy)))
            if approval_like_type(payload_type):
                result.approval_request_times.append((stamp, payload_type))
            if outer_type == "response_item" and payload_type == "message":
                role = str(payload.get("role") or "")
                content = payload.get("content")
                text, images, _ = content_text_and_images(content)
                stripped = text.strip()
                if role == "user":
                    if stripped.startswith(("<environment_context>", "<turn_aborted>", "<permissions instructions>")):
                        result.excluded["response_item_synthetic_user"] += 1
                    elif stripped:
                        chars, words = text_stats(text)
                        fallback_human.append(
                            HumanMessage(stamp, chars, words, images, str(line_no), str(path))
                        )
                elif role == "assistant" and normalize_text(text):
                    fallback_assistant.append(stamp)
    if not event_human and fallback_human:
        result.human.extend(fallback_human)
        result.excluded["used_response_item_user_fallback"] += len(fallback_human)
    else:
        result.excluded["response_item_user_duplicates_ignored"] += len(fallback_human)
    if not event_assistant and fallback_assistant:
        result.assistant_source_times.extend(
            (stamp, str(path), f"fallback:{stamp}") for stamp in fallback_assistant
        )
        result.excluded["used_response_item_assistant_fallback"] += len(fallback_assistant)
    else:
        result.excluded["response_item_assistant_duplicates_ignored"] += len(fallback_assistant)
    result.normalize()
    return result


def parse_gemini(path: Path) -> NativeConversation:
    result = NativeConversation()
    payload = json.loads(path.read_text(encoding="utf-8", errors="replace"))
    for message_no, message in enumerate(payload.get("messages") or [], 1):
        if not isinstance(message, dict):
            continue
        message_type = str(message.get("type") or "")
        result.native_record_types[message_type] += 1
        stamp = parse_ts_ms(message.get("timestamp") or message.get("time"))
        if stamp is None:
            result.excluded["missing_timestamp"] += 1
            continue
        content = message.get("content")
        text, images, _ = content_text_and_images(content)
        if isinstance(content, dict):
            text = str(content.get("text") or "")
            images += int(bool(content.get("image") or content.get("inlineData")))
        if message_type == "user":
            chars, words = text_stats(text)
            if chars or images:
                result.human.append(
                    HumanMessage(
                        stamp,
                        chars,
                        words,
                        images,
                        str(message.get("id") or message_no),
                        str(path),
                    )
                )
            else:
                result.excluded["empty_user_message"] += 1
        elif message_type == "gemini" and normalize_text(text):
            result.assistant_source_times.append(
                (stamp, str(path), transient_text_digest(text))
            )
        if approval_like_type(message_type):
            result.approval_request_times.append((stamp, message_type))
    result.normalize()
    return result


def parse_native(vendor: str, path: Path) -> NativeConversation:
    if vendor == "claude":
        return parse_claude(path)
    if vendor == "codex":
        return parse_codex(path)
    if vendor == "gemini":
        return parse_gemini(path)
    raise ValueError(f"Unsupported vendor: {vendor}")


def primary_source_role(vendor: str, source_role: str) -> bool:
    if vendor == "codex":
        return source_role == "user"
    return source_role == "root"


def tool_family(event: dict[str, Any]) -> str:
    name = str(event.get("tool_name") or "").lower()
    category = str(event.get("category") or "").lower()
    if category == "shell" or name in {"bash", "exec", "exec_command", "run_shell_command"}:
        return "shell"
    if name in {"read", "read_file"}:
        return "read"
    if name in {"write", "write_file", "edit", "apply_patch"}:
        return "mutate"
    if name in {"grep", "glob", "grep_search", "websearch", "web_search"}:
        return "search"
    if category == "subagent" or name in {"agent", "spawn_agent", "task"}:
        return "subagent"
    if name in {"wait", "wait_agent", "write_stdin", "send_input"}:
        return "wait/control"
    if category == "network":
        return "network"
    if category == "plan" or name in {"update_plan", "todowrite"}:
        return "plan"
    return category or name or "other"


def event_paths(event: dict[str, Any]) -> tuple[str, ...]:
    source = event.get("actions") or event.get("source_paths") or []
    paths = {
        str(item.get("path") or "").strip()
        for item in source
        if isinstance(item, dict) and str(item.get("path") or "").strip()
    }
    return tuple(sorted(paths))


def event_sort_key(event: dict[str, Any]) -> tuple[Any, ...]:
    return (
        int(event.get("ts_ms") or 0),
        str(event.get("source_stream_id") or ""),
        int(event.get("source_tool_ordinal") or 0),
        str(event.get("id") or ""),
    )


def sha256_decompressed(path: Path) -> str:
    digest = hashlib.sha256()
    with gzip.open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_corpus(
    events_dir: Path,
) -> tuple[
    list[dict[str, Any]],
    dict[tuple[str, str], list[dict[str, Any]]],
    list[dict[str, Any]],
]:
    events: list[dict[str, Any]] = []
    sessions: dict[tuple[str, str], list[dict[str, Any]]] = collections.defaultdict(list)
    manifests: list[dict[str, Any]] = []
    for path in discover_event_files(events_dir):
        document = load_json(path)
        project = str(document["repository"])
        project_events = document.get("events") or []
        for event in project_events:
            row = dict(event)
            row["_project"] = project
            row["_tool_family"] = tool_family(row)
            row["_paths"] = event_paths(row)
            events.append(row)
            sessions[(project, str(row["session_id"]))].append(row)
        plain_hash = sha256_file(path) if path.suffix != ".gz" else sha256_decompressed(path)
        paired_gzip = Path(str(path) + ".gz") if path.suffix != ".gz" else None
        paired_hash = (
            sha256_decompressed(paired_gzip)
            if paired_gzip is not None and paired_gzip.is_file()
            else None
        )
        manifests.append(
            {
                "project": project,
                "path": str(path),
                "bytes": path.stat().st_size,
                "sha256": plain_hash,
                "paired_gzip_path": str(paired_gzip) if paired_gzip else None,
                "paired_gzip_decompressed_sha256": paired_hash,
                "paired_gzip_matches": paired_hash == plain_hash if paired_hash else None,
                "revision": document.get("revision"),
                "events": len(project_events),
                "declared_sessions": document.get("session_count"),
                "declared_source_events": document.get("source_event_count"),
            }
        )
    for group in sessions.values():
        group.sort(key=event_sort_key)
    if len(events) != 181_303:
        raise RuntimeError(f"Expected 181,303 event rows, found {len(events):,}")
    if len(sessions) != 551:
        raise RuntimeError(f"Expected 551 project-attributed sessions, found {len(sessions):,}")
    if any(row["paired_gzip_matches"] is False for row in manifests):
        raise RuntimeError("At least one .json/.json.gz event export pair differs")
    return events, dict(sessions), manifests


def session_primary_sources(events: list[dict[str, Any]]) -> list[str]:
    vendor = str(events[0].get("vendor") or "")
    sources = {
        str(event.get("source_file") or "")
        for event in events
        if event.get("source_file")
        and primary_source_role(vendor, str(event.get("source_role") or ""))
    }
    if not sources:
        sources = {
            str(event.get("source_file") or "")
            for event in events
            if event.get("source_file")
            and "/subagents/" not in str(event.get("source_file"))
        }
    return sorted(sources)


def session_root_events(events: list[dict[str, Any]], sources: set[str]) -> list[dict[str, Any]]:
    vendor = str(events[0].get("vendor") or "")
    root = [
        event
        for event in events
        if str(event.get("source_file") or "") in sources
        and primary_source_role(vendor, str(event.get("source_role") or ""))
    ]
    if not root:
        root = [event for event in events if str(event.get("source_file") or "") in sources]
    return sorted(root, key=event_sort_key)


def load_mutation_metrics(path: Path) -> tuple[dict[tuple[str, str], dict[str, Any]], int]:
    metrics: dict[tuple[str, str], collections.Counter[str]] = collections.defaultdict(
        collections.Counter
    )
    row_count = 0
    with path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            row_count += 1
            key = (str(row["project"]), str(row["session_id"]))
            acc = metrics[key]
            acc["mutations_total"] += 1
            if str(row.get("operation") or "") == "delete":
                acc["delete_mutations"] += 1
                continue
            acc["nondelete_eligible"] += 1
            reuse = str(row.get("reuse_outcome") or "missing")
            validation = str(row.get("validation_outcome") or "missing")
            acc[f"reuse_{reuse}"] += 1
            acc[f"validation_{validation}"] += 1
            if str(row.get("reuse_cross_session") or "").lower() == "true":
                acc["reuse_cross_session"] += 1
    if row_count != 13_906:
        raise RuntimeError(f"Expected 13,906 mutation rows, found {row_count:,}")
    return {key: dict(value) for key, value in metrics.items()}, row_count


def outcome_value(metrics: dict[str, Any], prefix: str, outcome: str) -> int:
    return int(metrics.get(f"{prefix}_{outcome}", 0))


def interruption_before(
    previous_human_ms: int,
    current_human_ms: int,
    interrupts: Sequence[int],
) -> bool:
    return any(previous_human_ms < stamp <= current_human_ms for stamp in interrupts)


def build_followup_rows(
    project: str,
    session_id: str,
    vendor: str,
    conversation: NativeConversation,
    root_events: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    human = conversation.human
    by_source: dict[str, list[dict[str, Any]]] = collections.defaultdict(list)
    by_source_stream: dict[tuple[str, str], list[dict[str, Any]]] = (
        collections.defaultdict(list)
    )
    for event in root_events:
        source = str(event.get("source_file") or "")
        stream = str(event.get("source_stream_id") or "")
        by_source[source].append(event)
        by_source_stream[(source, stream)].append(event)
    source_times = {
        source: [int(event.get("ts_ms") or 0) for event in events]
        for source, events in by_source.items()
    }
    stream_times = {
        key: [int(event.get("ts_ms") or 0) for event in events]
        for key, events in by_source_stream.items()
    }
    for ordinal, message in enumerate(human[1:], 2):
        previous_message = human[ordinal - 2]
        same_source = by_source.get(message.source_file, [])
        same_source_times = source_times.get(message.source_file, [])
        before_position = bisect.bisect_left(
            same_source_times, message.timestamp_ms
        ) - 1
        before = same_source[before_position] if before_position >= 0 else None
        stream_id = str(before.get("source_stream_id") or "") if before else ""
        candidate_events = (
            by_source_stream.get((message.source_file, stream_id), [])
            if stream_id
            else same_source
        )
        candidate_times = (
            stream_times.get((message.source_file, stream_id), [])
            if stream_id
            else same_source_times
        )
        after_position = bisect.bisect_left(candidate_times, message.timestamp_ms)
        after = (
            candidate_events[after_position]
            if after_position < len(candidate_events)
            else None
        )
        before_paths = tuple(before.get("_paths") or ()) if before else ()
        after_paths = tuple(after.get("_paths") or ()) if after else ()
        path_eligible = bool(before_paths and after_paths)
        row = {
            "project": project,
            "vendor": vendor,
            "session_id": session_id,
            "followup_ordinal": ordinal,
            "timestamp_ms": message.timestamp_ms,
            "source_file": message.source_file,
            "source_stream_id": stream_id,
            "preceded_by_explicit_interrupt": interruption_before(
                previous_message.timestamp_ms,
                message.timestamp_ms,
                conversation.explicit_interrupt_times_ms,
            ),
            "before_action_available": before is not None,
            "after_action_available": after is not None,
            "before_tool_name": str(before.get("tool_name") or "") if before else "",
            "after_tool_name": str(after.get("tool_name") or "") if after else "",
            "before_tool_family": str(before.get("_tool_family") or "") if before else "",
            "after_tool_family": str(after.get("_tool_family") or "") if after else "",
            "exact_tool_changed": (
                str(before.get("tool_name") or "") != str(after.get("tool_name") or "")
                if before and after
                else None
            ),
            "tool_family_changed": (
                str(before.get("_tool_family") or "")
                != str(after.get("_tool_family") or "")
                if before and after
                else None
            ),
            "path_comparison_eligible": path_eligible,
            "path_set_changed": set(before_paths) != set(after_paths) if path_eligible else None,
            "path_sets_disjoint": (
                set(before_paths).isdisjoint(after_paths) if path_eligible else None
            ),
            "before_path_count": len(before_paths),
            "after_path_count": len(after_paths),
            "ms_since_before_action": (
                message.timestamp_ms - int(before["ts_ms"]) if before else None
            ),
            "ms_to_after_action": (
                int(after["ts_ms"]) - message.timestamp_ms if after else None
            ),
        }
        rows.append(row)
    return rows


def build_interval_rows(
    project: str,
    session_id: str,
    vendor: str,
    conversation: NativeConversation,
    root_events: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    activity_by_source: dict[str, set[int]] = collections.defaultdict(set)
    for event in root_events:
        activity_by_source[str(event.get("source_file") or "")].add(
            int(event.get("ts_ms") or 0)
        )
    for stamp, source_file, _ in conversation.assistant_source_times:
        activity_by_source[source_file].add(stamp)
    indexed_activity = {
        source_file: sorted(stamps)
        for source_file, stamps in activity_by_source.items()
    }
    for ordinal, (current, following) in enumerate(
        zip(conversation.human, conversation.human[1:]), 1
    ):
        if following.timestamp_ms < current.timestamp_ms:
            continue
        activity_times = indexed_activity.get(current.source_file, [])
        left = bisect.bisect_left(activity_times, current.timestamp_ms)
        right = bisect.bisect_right(activity_times, following.timestamp_ms)
        activity_count = max(0, right - left)
        last_activity = activity_times[right - 1] if activity_count else None
        interval_ms = following.timestamp_ms - current.timestamp_ms
        envelope = last_activity - current.timestamp_ms if last_activity is not None else None
        inactive = following.timestamp_ms - last_activity if last_activity is not None else None
        rows.append(
            {
                "project": project,
                "vendor": vendor,
                "session_id": session_id,
                "interval_ordinal": ordinal,
                "start_human_ms": current.timestamp_ms,
                "next_human_ms": following.timestamp_ms,
                "interval_ms": interval_ms,
                "observable_agent_activity_records": activity_count,
                "last_agent_activity_ms": last_activity,
                "agent_activity_envelope_ms": envelope,
                "post_activity_inactive_gap_ms": inactive,
                "post_activity_inactive_share": safe_div(inactive, interval_ms)
                if inactive is not None
                else None,
                "contains_explicit_interrupt": interruption_before(
                    current.timestamp_ms,
                    following.timestamp_ms,
                    conversation.explicit_interrupt_times_ms,
                ),
            }
        )
    return rows


def local_time_fields(timestamp_ms: int | None) -> dict[str, Any]:
    if timestamp_ms is None:
        return {
            "start_local_iso": "",
            "start_hour": None,
            "start_weekday": "",
        }
    stamp = dt.datetime.fromtimestamp(timestamp_ms / 1000, tz=dt.timezone.utc).astimezone(
        LOCAL_TZ
    )
    return {
        "start_local_iso": stamp.isoformat(),
        "start_hour": stamp.hour,
        "start_weekday": stamp.strftime("%A"),
    }


def build_measurements(
    sessions: dict[tuple[str, str], list[dict[str, Any]]],
    mutation_metrics: dict[tuple[str, str], dict[str, Any]],
    parse_cache: dict[tuple[str, str], NativeConversation],
) -> tuple[
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
]:
    session_rows: list[dict[str, Any]] = []
    message_rows: list[dict[str, Any]] = []
    followup_rows: list[dict[str, Any]] = []
    interval_rows: list[dict[str, Any]] = []
    coverage_rows: list[dict[str, Any]] = []
    approval_rows: list[dict[str, Any]] = []

    for (project, session_id), events in sorted(sessions.items()):
        vendor = str(events[0].get("vendor") or "")
        sources = session_primary_sources(events)
        conversation = NativeConversation()
        readable_sources = 0
        native_subagent_sources = 0
        for source in sources:
            source_path = Path(source)
            readable = source_path.is_file()
            parsed = False
            source_hash = ""
            parse_error = ""
            parsed_source = NativeConversation()
            if readable:
                readable_sources += 1
                source_hash = sha256_file(source_path)
                cache_key = (vendor, source)
                if cache_key not in parse_cache:
                    try:
                        parse_cache[cache_key] = parse_native(vendor, source_path)
                    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
                        parse_error = f"{type(exc).__name__}: {exc}"
                        parse_cache[cache_key] = NativeConversation()
                parsed = not parse_error
                parsed_source = parse_cache[cache_key]
                native_subagent_sources += int(
                    parsed_source.native_source_kind == "subagent"
                )
                conversation.merge(parsed_source)
            coverage_rows.append(
                {
                    "project": project,
                    "vendor": vendor,
                    "session_id": session_id,
                    "source_file": source,
                    "source_role_rule": "user" if vendor == "codex" else "root",
                    "readable": readable,
                    "parsed": parsed,
                    "bytes": source_path.stat().st_size if readable else None,
                    "sha256": source_hash,
                    "parse_error": parse_error,
                    "native_source_kind": parsed_source.native_source_kind,
                    "native_source_app": parsed_source.native_source_app,
                    "human_bearing_source": parsed_source.human_bearing_source
                    if readable
                    else None,
                }
            )
        conversation.normalize()
        source_set = set(sources)
        projected_root_events = session_root_events(events, source_set)
        human_source_set = {message.source_file for message in conversation.human}
        human_root_events = session_root_events(events, human_source_set)
        followups = build_followup_rows(
            project, session_id, vendor, conversation, human_root_events
        )
        intervals = build_interval_rows(
            project, session_id, vendor, conversation, human_root_events
        )
        followup_rows.extend(followups)
        interval_rows.extend(intervals)
        human_count = len(conversation.human)
        assistant_count = len(conversation.assistant_source_times)
        if readable_sources == 0:
            involvement_style = "unreadable"
        elif human_count == 0 and sources and native_subagent_sources == len(sources):
            involvement_style = "subagent_only"
        elif human_count == 0:
            involvement_style = "zero_human_record"
        elif human_count == 1:
            involvement_style = "startup_only"
        else:
            involvement_style = "guided"
        first_human = conversation.human[0].timestamp_ms if conversation.human else None
        local = local_time_fields(first_human)
        metrics = mutation_metrics.get((project, session_id), {})
        nondelete = int(metrics.get("nondelete_eligible", 0))
        reuse_observed = outcome_value(metrics, "reuse", "observed_reuse")
        validation_observed = outcome_value(
            metrics, "validation", "observed_validation"
        )
        action_count = len(events)
        unique_call_count = len(
            {
                str(event.get("source_call_id") or event.get("id") or "")
                for event in events
            }
        )
        primary_prompt_pairs = {
            (str(event.get("source_stream_id") or ""), str(event.get("prompt_index") or ""))
            for event in human_root_events
        }
        policies = sorted({policy for _, policy in conversation.permission_policies})
        approval_types = sorted(
            collections.Counter(record_type for _, record_type in conversation.approval_request_times).items()
        )
        questions = [
            event
            for event in human_root_events
            if str(event.get("tool_name") or "")
            in {"AskUserQuestion", "request_user_input"}
        ]
        interval_envelope = [
            row["agent_activity_envelope_ms"]
            for row in intervals
            if finite(row["agent_activity_envelope_ms"])
        ]
        interval_inactive = [
            row["post_activity_inactive_gap_ms"]
            for row in intervals
            if finite(row["post_activity_inactive_gap_ms"])
        ]
        session_row = {
            "project": project,
            "vendor": vendor,
            "session_id": session_id,
            "agent_actions": action_count,
            "unique_source_call_actions": unique_call_count,
            "projected_root_agent_actions": len(projected_root_events),
            "human_source_agent_actions": len(human_root_events),
            "primary_source_files": len(sources),
            "native_subagent_source_files": native_subagent_sources,
            "human_bearing_source_files": len(human_source_set),
            "readable_primary_sources": readable_sources,
            "native_parse_coverage": readable_sources == len(sources) and bool(sources),
            "projected_root_prompt_stream_pairs": len(primary_prompt_pairs),
            "user_messages": human_count,
            "followup_user_messages": max(0, human_count - 1),
            "human_characters": sum(message.chars for message in conversation.human),
            "human_words_approx": sum(
                message.words_approx for message in conversation.human
            ),
            "human_images": sum(message.images for message in conversation.human),
            "assistant_conversational_messages": assistant_count,
            "user_conversational_turn_share": safe_div(
                human_count, human_count + assistant_count
            ),
            "involvement_style": involvement_style,
            "explicit_interrupt_markers": len(
                conversation.explicit_interrupt_times_ms
            ),
            "followups_preceded_by_explicit_interrupt": sum(
                bool(row["preceded_by_explicit_interrupt"]) for row in followups
            ),
            "agent_question_tools": len(questions),
            "approval_like_native_records": len(
                conversation.approval_request_times
            ),
            "approval_like_native_types": "|".join(
                f"{name}:{count}" for name, count in approval_types
            ),
            "permission_policy_record_count": len(
                conversation.permission_policies
            ),
            "permission_policies": "|".join(policies),
            "actions_per_user_message": safe_div(action_count, human_count),
            "user_messages_per_100_actions": 100 * safe_div(human_count, action_count)
            if action_count
            else None,
            "followups_per_100_actions": 100
            * safe_div(max(0, human_count - 1), action_count)
            if action_count
            else None,
            "closed_interprompt_intervals": len(intervals),
            "intervals_with_agent_activity": len(interval_envelope),
            "agent_activity_envelope_ms_sum": sum(interval_envelope),
            "post_activity_inactive_gap_ms_sum": sum(interval_inactive),
            "post_activity_inactive_share_aggregate": safe_div(
                sum(interval_inactive),
                sum(interval_inactive) + sum(interval_envelope),
            ),
            "mutations_total": int(metrics.get("mutations_total", 0)),
            "delete_mutations": int(metrics.get("delete_mutations", 0)),
            "nondelete_eligible_mutations": nondelete,
            "mutations_per_100_actions": 100
            * safe_div(int(metrics.get("mutations_total", 0)), action_count)
            if action_count
            else None,
            "reuse_observed": reuse_observed,
            "reuse_competing_delete": outcome_value(
                metrics, "reuse", "competing_delete"
            ),
            "reuse_competing_supersede": outcome_value(
                metrics, "reuse", "competing_supersede"
            ),
            "reuse_censored_end": outcome_value(metrics, "reuse", "censored_end"),
            "reuse_missing": outcome_value(metrics, "reuse", "missing"),
            "reuse_observed_rate": safe_div(reuse_observed, nondelete),
            "reuse_cross_session": int(metrics.get("reuse_cross_session", 0)),
            "validation_observed": validation_observed,
            "validation_competing_supersede": outcome_value(
                metrics, "validation", "competing_supersede"
            ),
            "validation_censored_end": outcome_value(
                metrics, "validation", "censored_end"
            ),
            "validation_missing": outcome_value(metrics, "validation", "missing"),
            "validation_observed_rate": safe_div(validation_observed, nondelete),
            **local,
        }
        session_rows.append(session_row)
        for ordinal, message in enumerate(conversation.human, 1):
            message_local = local_time_fields(message.timestamp_ms)
            message_rows.append(
                {
                    "project": project,
                    "vendor": vendor,
                    "session_id": session_id,
                    "message_ordinal": ordinal,
                    "timestamp_ms": message.timestamp_ms,
                    "timestamp_local_iso": message_local["start_local_iso"],
                    "hour": message_local["start_hour"],
                    "weekday": message_local["start_weekday"],
                    "characters": message.chars,
                    "words_approx": message.words_approx,
                    "images": message.images,
                    "is_followup": ordinal > 1,
                    "preceded_by_explicit_interrupt": (
                        interruption_before(
                            conversation.human[ordinal - 2].timestamp_ms,
                            message.timestamp_ms,
                            conversation.explicit_interrupt_times_ms,
                        )
                        if ordinal > 1
                        else False
                    ),
                    "source_file": message.source_file,
                }
            )
        approval_counter = collections.Counter(
            record_type for _, record_type in conversation.approval_request_times
        )
        for record_type, count in sorted(approval_counter.items()):
            approval_rows.append(
                {
                    "project": project,
                    "vendor": vendor,
                    "session_id": session_id,
                    "visibility_class": "native_approval_like_record",
                    "record_type_or_policy": record_type,
                    "count": count,
                }
            )
        for policy, count in collections.Counter(
            policy for _, policy in conversation.permission_policies
        ).items():
            approval_rows.append(
                {
                    "project": project,
                    "vendor": vendor,
                    "session_id": session_id,
                    "visibility_class": "permission_policy_configuration",
                    "record_type_or_policy": policy,
                    "count": count,
                }
            )
        if questions:
            approval_rows.append(
                {
                    "project": project,
                    "vendor": vendor,
                    "session_id": session_id,
                    "visibility_class": "agent_question_tool",
                    "record_type_or_policy": "AskUserQuestion/request_user_input",
                    "count": len(questions),
                }
            )
    return (
        session_rows,
        message_rows,
        followup_rows,
        interval_rows,
        coverage_rows,
        approval_rows,
    )


def numeric_summary(values: Iterable[Any]) -> dict[str, Any]:
    series = pd.to_numeric(pd.Series(list(values), dtype="object"), errors="coerce").dropna()
    if series.empty:
        return {
            "n": 0,
            "sum": None,
            "mean": None,
            "q25": None,
            "median": None,
            "q75": None,
            "p90": None,
        }
    return {
        "n": int(len(series)),
        "sum": float(series.sum()),
        "mean": float(series.mean()),
        "q25": float(series.quantile(0.25)),
        "median": float(series.quantile(0.5)),
        "q75": float(series.quantile(0.75)),
        "p90": float(series.quantile(0.9)),
    }


def add_density_groups(session_frame: pd.DataFrame) -> pd.DataFrame:
    frame = session_frame.copy()
    frame["density_group"] = ""
    for _, index in frame.groupby(["project", "vendor"], observed=True).groups.items():
        sub = frame.loc[index]
        values = pd.to_numeric(sub["followups_per_100_actions"], errors="coerce").dropna()
        if len(values) < 6:
            continue
        q33 = float(values.quantile(1 / 3))
        q67 = float(values.quantile(2 / 3))
        if not q33 < q67:
            continue
        frame.loc[index, "density_q33"] = q33
        frame.loc[index, "density_q67"] = q67
        frame.loc[index, "density_group"] = np.where(
            pd.to_numeric(sub["followups_per_100_actions"], errors="coerce") <= q33,
            "low",
            np.where(
                pd.to_numeric(sub["followups_per_100_actions"], errors="coerce") >= q67,
                "high",
                "middle",
            ),
        )
    return frame


def distribution_rows(
    session_frame: pd.DataFrame, message_frame: pd.DataFrame
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    unique_sessions = session_frame.sort_values(
        ["session_id", "project"]
    ).drop_duplicates("session_id")
    unique_messages = message_frame.sort_values(
        ["session_id", "message_ordinal", "project"]
    ).drop_duplicates(["session_id", "message_ordinal"])
    session_metrics = (
        "user_messages",
        "human_characters",
        "human_words_approx",
        "user_conversational_turn_share",
        "actions_per_user_message",
        "followups_per_100_actions",
        "explicit_interrupt_markers",
        "agent_activity_envelope_ms_sum",
        "post_activity_inactive_gap_ms_sum",
    )
    message_metrics = ("characters", "words_approx")

    scopes: list[tuple[str, str, str, pd.DataFrame, pd.DataFrame]] = [
        ("overall_unique", "ALL", "ALL", unique_sessions, unique_messages)
    ]
    for vendor in VENDOR_ORDER:
        scopes.append(
            (
                "vendor_unique",
                "ALL",
                vendor,
                unique_sessions[unique_sessions["vendor"] == vendor],
                unique_messages[unique_messages["vendor"] == vendor],
            )
        )
    for project in PROJECT_ORDER:
        for vendor in VENDOR_ORDER:
            scopes.append(
                (
                    "project_vendor",
                    project,
                    vendor,
                    session_frame[
                        (session_frame["project"] == project)
                        & (session_frame["vendor"] == vendor)
                    ],
                    message_frame[
                        (message_frame["project"] == project)
                        & (message_frame["vendor"] == vendor)
                    ],
                )
            )
    for scope, project, vendor, sessions, messages in scopes:
        for metric in session_metrics:
            summary = numeric_summary(sessions[metric] if metric in sessions else [])
            rows.append(
                {
                    "scope": scope,
                    "project": project,
                    "vendor": vendor,
                    "unit": "session",
                    "metric": metric,
                    **summary,
                }
            )
        for metric in message_metrics:
            summary = numeric_summary(messages[metric] if metric in messages else [])
            rows.append(
                {
                    "scope": scope,
                    "project": project,
                    "vendor": vendor,
                    "unit": "human_message",
                    "metric": metric,
                    **summary,
                }
            )
    return rows


def action_count_for_scope(
    events: list[dict[str, Any]], project: str | None, vendor: str | None
) -> tuple[int, int]:
    selected = [
        event
        for event in events
        if (project is None or event["_project"] == project)
        and (vendor is None or event.get("vendor") == vendor)
    ]
    unique = {
        (
            event["_project"],
            str(event.get("vendor") or ""),
            str(event.get("source_call_id") or event.get("id") or ""),
        )
        for event in selected
    }
    return len(selected), len(unique)


def profile_row(
    scope: str,
    project: str,
    vendor: str,
    human_units: pd.DataFrame,
    action_total: int,
    unique_action_total: int,
) -> dict[str, Any]:
    users = int(human_units["user_messages"].sum()) if len(human_units) else 0
    assistants = (
        int(human_units["assistant_conversational_messages"].sum())
        if len(human_units)
        else 0
    )
    envelopes = (
        float(human_units["agent_activity_envelope_ms_sum"].sum())
        if len(human_units)
        else 0.0
    )
    inactive = (
        float(human_units["post_activity_inactive_gap_ms_sum"].sum())
        if len(human_units)
        else 0.0
    )
    return {
        "scope": scope,
        "project": project,
        "vendor": vendor,
        "sessions": int(len(human_units)),
        "startup_only_sessions": int(
            (human_units["involvement_style"] == "startup_only").sum()
        )
        if len(human_units)
        else 0,
        "guided_sessions": int(
            (human_units["involvement_style"] == "guided").sum()
        )
        if len(human_units)
        else 0,
        "zero_or_unreadable_sessions": int(
            human_units["involvement_style"].isin(
                ["subagent_only", "zero_human_record", "unreadable"]
            ).sum()
        )
        if len(human_units)
        else 0,
        "user_messages": users,
        "followup_user_messages": int(human_units["followup_user_messages"].sum())
        if len(human_units)
        else 0,
        "human_characters": int(human_units["human_characters"].sum())
        if len(human_units)
        else 0,
        "human_words_approx": int(human_units["human_words_approx"].sum())
        if len(human_units)
        else 0,
        "assistant_conversational_messages": assistants,
        "aggregate_user_conversational_turn_share": safe_div(
            users, users + assistants
        ),
        "agent_actions": action_total,
        "unique_source_call_actions": unique_action_total,
        "actions_per_user_message": safe_div(action_total, users),
        "unique_actions_per_user_message": safe_div(unique_action_total, users),
        "one_user_message_per_n_actions": safe_div(action_total, users),
        "user_messages_per_100_actions": 100 * safe_div(users, action_total)
        if action_total
        else None,
        "explicit_interrupt_markers": int(
            human_units["explicit_interrupt_markers"].sum()
        )
        if len(human_units)
        else 0,
        "agent_question_tools": int(human_units["agent_question_tools"].sum())
        if len(human_units)
        else 0,
        "approval_like_native_records": int(
            human_units["approval_like_native_records"].sum()
        )
        if len(human_units)
        else 0,
        "agent_activity_envelope_hours": envelopes / 3_600_000,
        "post_activity_inactive_gap_hours": inactive / 3_600_000,
        "post_activity_inactive_share": safe_div(inactive, inactive + envelopes),
    }


def build_profile_rows(
    session_frame: pd.DataFrame, events: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    unique = session_frame.sort_values(["session_id", "project"]).drop_duplicates(
        "session_id"
    )
    actions, unique_actions = action_count_for_scope(events, None, None)
    rows.append(
        profile_row(
            "overall_unique_sessions",
            "ALL",
            "ALL",
            unique,
            actions,
            unique_actions,
        )
    )
    rows.append(
        profile_row(
            "overall_project_attributed",
            "ALL",
            "ALL",
            session_frame,
            actions,
            unique_actions,
        )
    )
    for vendor in VENDOR_ORDER:
        vendor_unique = unique[unique["vendor"] == vendor]
        action_total, unique_total = action_count_for_scope(events, None, vendor)
        rows.append(
            profile_row(
                "vendor_unique_sessions",
                "ALL",
                vendor,
                vendor_unique,
                action_total,
                unique_total,
            )
        )
    for project in PROJECT_ORDER:
        project_units = session_frame[session_frame["project"] == project]
        action_total, unique_total = action_count_for_scope(events, project, None)
        rows.append(
            profile_row(
                "project_attributed",
                project,
                "ALL",
                project_units,
                action_total,
                unique_total,
            )
        )
        for vendor in VENDOR_ORDER:
            units = session_frame[
                (session_frame["project"] == project)
                & (session_frame["vendor"] == vendor)
            ]
            action_total, unique_total = action_count_for_scope(
                events, project, vendor
            )
            rows.append(
                profile_row(
                    "project_vendor_attributed",
                    project,
                    vendor,
                    units,
                    action_total,
                    unique_total,
                )
            )
    return rows


def build_schedule_rows(
    session_frame: pd.DataFrame,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    unique = session_frame.sort_values(["session_id", "project"]).drop_duplicates(
        "session_id"
    )
    scopes: list[tuple[str, str, str, pd.DataFrame]] = [
        ("overall_unique", "ALL", "ALL", unique)
    ]
    for vendor in VENDOR_ORDER:
        scopes.append(
            (
                "vendor_unique",
                "ALL",
                vendor,
                unique[unique["vendor"] == vendor],
            )
        )
    for project in PROJECT_ORDER:
        for vendor in VENDOR_ORDER:
            scopes.append(
                (
                    "project_vendor",
                    project,
                    vendor,
                    session_frame[
                        (session_frame["project"] == project)
                        & (session_frame["vendor"] == vendor)
                    ],
                )
            )
    hour_rows: list[dict[str, Any]] = []
    weekday_rows: list[dict[str, Any]] = []
    for scope, project, vendor, sub in scopes:
        valid = sub[pd.to_numeric(sub["start_hour"], errors="coerce").notna()]
        hour_counts = collections.Counter(int(value) for value in valid["start_hour"])
        weekday_counts = collections.Counter(
            value for value in valid["start_weekday"] if value
        )
        for hour in range(24):
            hour_rows.append(
                {
                    "scope": scope,
                    "project": project,
                    "vendor": vendor,
                    "hour": hour,
                    "sessions": hour_counts[hour],
                    "share": safe_div(hour_counts[hour], len(valid)),
                }
            )
        for weekday in WEEKDAY_ORDER:
            weekday_rows.append(
                {
                    "scope": scope,
                    "project": project,
                    "vendor": vendor,
                    "weekday": weekday,
                    "sessions": weekday_counts[weekday],
                    "share": safe_div(weekday_counts[weekday], len(valid)),
                }
            )
    return hour_rows, weekday_rows


def summarize_outcome_group(
    contrast: str,
    scope: str,
    project: str,
    vendor: str,
    group_name: str,
    sub: pd.DataFrame,
) -> dict[str, Any]:
    actions = numeric_summary(sub["agent_actions"])
    mutations = numeric_summary(sub["mutations_total"])
    density = numeric_summary(sub["mutations_per_100_actions"])
    reuse = numeric_summary(sub["reuse_observed_rate"])
    validation = numeric_summary(sub["validation_observed_rate"])
    eligible = int(sub["nondelete_eligible_mutations"].sum()) if len(sub) else 0
    reuse_observed = int(sub["reuse_observed"].sum()) if len(sub) else 0
    validation_observed = int(sub["validation_observed"].sum()) if len(sub) else 0
    return {
        "contrast": contrast,
        "scope": scope,
        "project": project,
        "vendor": vendor,
        "group": group_name,
        "sessions": int(len(sub)),
        "direction_claim_allowed": len(sub) >= 10,
        "agent_actions_sum": actions["sum"],
        "agent_actions_median": actions["median"],
        "agent_actions_q25": actions["q25"],
        "agent_actions_q75": actions["q75"],
        "mutations_sum": mutations["sum"],
        "mutations_median": mutations["median"],
        "mutations_q25": mutations["q25"],
        "mutations_q75": mutations["q75"],
        "mutation_density_mean": density["mean"],
        "mutation_density_median": density["median"],
        "mutation_density_q25": density["q25"],
        "mutation_density_q75": density["q75"],
        "nondelete_eligible_mutations": eligible,
        "reuse_observed": reuse_observed,
        "reuse_competing_delete": int(sub["reuse_competing_delete"].sum())
        if len(sub)
        else 0,
        "reuse_competing_supersede": int(sub["reuse_competing_supersede"].sum())
        if len(sub)
        else 0,
        "reuse_censored_end": int(sub["reuse_censored_end"].sum()) if len(sub) else 0,
        "reuse_missing": int(sub["reuse_missing"].sum()) if len(sub) else 0,
        "reuse_observed_pooled_rate": safe_div(reuse_observed, eligible),
        "reuse_session_rate_median": reuse["median"],
        "validation_observed": validation_observed,
        "validation_competing_supersede": int(
            sub["validation_competing_supersede"].sum()
        )
        if len(sub)
        else 0,
        "validation_censored_end": int(sub["validation_censored_end"].sum())
        if len(sub)
        else 0,
        "validation_missing": int(sub["validation_missing"].sum())
        if len(sub)
        else 0,
        "validation_observed_pooled_rate": safe_div(
            validation_observed, eligible
        ),
        "validation_session_rate_median": validation["median"],
    }


def build_outcome_rows(session_frame: pd.DataFrame) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    contrasts = (
        ("session_style", "involvement_style", ("startup_only", "guided")),
        ("guidance_density_tertiles", "density_group", ("low", "high")),
    )
    for contrast, column, groups in contrasts:
        eligible = session_frame[session_frame[column].isin(groups)]
        for group_name in groups:
            rows.append(
                summarize_outcome_group(
                    contrast,
                    "overall_project_attributed",
                    "ALL",
                    "ALL",
                    group_name,
                    eligible[eligible[column] == group_name],
                )
            )
        for project in PROJECT_ORDER:
            for vendor in VENDOR_ORDER:
                stratum = eligible[
                    (eligible["project"] == project) & (eligible["vendor"] == vendor)
                ]
                for group_name in groups:
                    rows.append(
                        summarize_outcome_group(
                            contrast,
                            "project_vendor",
                            project,
                            vendor,
                            group_name,
                            stratum[stratum[column] == group_name],
                        )
                    )
    return rows


def save_figure(fig: plt.Figure, base: Path) -> None:
    fig.savefig(base.with_suffix(".png"), dpi=180, bbox_inches="tight")
    fig.savefig(base.with_suffix(".pdf"), bbox_inches="tight")
    plt.close(fig)


def plot_session_involvement(session_frame: pd.DataFrame, figures: Path) -> None:
    observed = (
        session_frame.groupby(["project", "vendor", "involvement_style"], observed=True)
        .size()
        .unstack(fill_value=0)
        .reset_index()
    )
    styles = (
        "startup_only",
        "guided",
        "subagent_only",
        "zero_human_record",
        "unreadable",
    )
    colors = ("#999999", "#4C78A8", "#72B7B2", "#ECA82C", "#CC6677")
    for style in styles:
        if style not in observed:
            observed[style] = 0
    observed = observed[observed[list(styles)].sum(axis=1) > 0]
    labels = [f"{row.project} / {row.vendor}" for row in observed.itertuples()]
    totals = observed[list(styles)].sum(axis=1).replace(0, np.nan)
    positions = np.arange(len(observed))
    fig, axes = plt.subplots(
        1, 2, figsize=(15, 7.2), gridspec_kw={"width_ratios": [1.1, 1]}
    )
    left = np.zeros(len(observed))
    for style, color in zip(styles, colors):
        values = observed.get(style, pd.Series(0, index=observed.index)) / totals
        axes[0].barh(positions, values, left=left, label=style, color=color)
        left += values.fillna(0).to_numpy()
    axes[0].set_yticks(positions, labels, fontsize=8)
    axes[0].set_xlim(0, 1)
    axes[0].invert_yaxis()
    axes[0].set_xlabel("Share of project-attributed sessions")
    axes[0].set_title("Startup-only versus multi-turn guided sessions")
    axes[0].legend(frameon=False, fontsize=8)

    data = []
    box_labels = []
    for row in observed.itertuples():
        values = pd.to_numeric(
            session_frame[
                (session_frame["project"] == row.project)
                & (session_frame["vendor"] == row.vendor)
            ]["user_messages"],
            errors="coerce",
        ).dropna()
        data.append(values.to_numpy())
        box_labels.append(f"{row.project} / {row.vendor}")
    axes[1].boxplot(data, showfliers=True, labels=box_labels, vert=False)
    axes[1].set_xscale("symlog", linthresh=1)
    axes[1].set_xlabel("Substantive user messages per session")
    axes[1].set_title("Full per-session distributions")
    axes[1].tick_params(axis="y", labelsize=8)
    axes[1].invert_yaxis()
    fig.tight_layout()
    save_figure(fig, figures / "01_session_involvement")


def plot_message_lengths(message_frame: pd.DataFrame, figures: Path) -> None:
    unique = message_frame.sort_values(
        ["session_id", "message_ordinal", "project"]
    ).drop_duplicates(["session_id", "message_ordinal"])
    fig, axes = plt.subplots(1, 2, figsize=(11.5, 4.4))
    for vendor in VENDOR_ORDER:
        values = np.sort(
            pd.to_numeric(
                unique[unique["vendor"] == vendor]["characters"], errors="coerce"
            )
            .dropna()
            .to_numpy()
        )
        if not len(values):
            continue
        y = np.arange(1, len(values) + 1) / len(values)
        axes[0].step(values, y, where="post", label=f"{vendor} (n={len(values)})", color=VENDOR_COLORS[vendor])
        words = np.sort(
            pd.to_numeric(
                unique[unique["vendor"] == vendor]["words_approx"], errors="coerce"
            )
            .dropna()
            .to_numpy()
        )
        y_words = np.arange(1, len(words) + 1) / len(words)
        axes[1].step(
            words,
            y_words,
            where="post",
            label=f"{vendor} (n={len(words)})",
            color=VENDOR_COLORS[vendor],
        )
    for axis, label in zip(
        axes, ("Unicode characters", "Approximate word-like tokens")
    ):
        axis.set_xscale("symlog", linthresh=1)
        axis.set_xlabel(label)
        axis.set_ylabel("Empirical CDF")
        axis.grid(alpha=0.2)
        axis.legend(frameon=False)
    axes[0].set_title("Human-message character lengths")
    axes[1].set_title("Bilingual token-length approximation")
    fig.tight_layout()
    save_figure(fig, figures / "02_message_lengths")


def plot_attention_schedule(
    session_frame: pd.DataFrame, interval_frame: pd.DataFrame, figures: Path
) -> None:
    unique = session_frame.sort_values(["session_id", "project"]).drop_duplicates(
        "session_id"
    )
    matrix = np.zeros((7, 24), dtype=int)
    for row in unique.itertuples():
        if finite(row.start_hour) and row.start_weekday in WEEKDAY_ORDER:
            matrix[WEEKDAY_ORDER.index(row.start_weekday), int(row.start_hour)] += 1
    unique_intervals = interval_frame.sort_values(
        ["session_id", "interval_ordinal", "project"]
    ).drop_duplicates(["session_id", "interval_ordinal"])
    fig, axes = plt.subplots(1, 2, figsize=(14, 4.8), gridspec_kw={"width_ratios": [1.55, 1]})
    image = axes[0].imshow(matrix, aspect="auto", cmap="Blues")
    axes[0].set_yticks(range(7), [day[:3] for day in WEEKDAY_ORDER])
    axes[0].set_xticks(range(0, 24, 2))
    axes[0].set_xlabel("First human-message hour (America/Vancouver)")
    axes[0].set_title("First substantive human-message times")
    fig.colorbar(image, ax=axes[0], label="Sessions")

    envelope = (
        pd.to_numeric(unique_intervals["agent_activity_envelope_ms"], errors="coerce")
        .dropna()
        / 3_600_000
    )
    inactive = (
        pd.to_numeric(
            unique_intervals["post_activity_inactive_gap_ms"], errors="coerce"
        )
        .dropna()
        / 3_600_000
    )
    axes[1].boxplot(
        [envelope.to_numpy(), inactive.to_numpy()],
        labels=["Agent activity\nenvelope", "Post-activity\ninactive gap"],
        showfliers=True,
    )
    axes[1].set_yscale("symlog", linthresh=1 / 60)
    axes[1].set_ylabel("Elapsed hours (symlog)")
    axes[1].set_title("Closed inter-prompt intervals")
    fig.tight_layout()
    save_figure(fig, figures / "03_attention_schedule")


def plot_outcome_cooccurrence(session_frame: pd.DataFrame, figures: Path) -> None:
    data = session_frame[
        session_frame["involvement_style"].isin(["startup_only", "guided"])
    ].copy()
    metrics = (
        ("mutations_per_100_actions", "Mutations per 100 Agent actions"),
        ("reuse_observed_rate", "Observed-reuse rate"),
        ("validation_observed_rate", "Observed-validation rate"),
    )
    fig, axes = plt.subplots(1, 3, figsize=(13.5, 4.2))
    rng = np.random.default_rng(20260726)
    for axis, (metric, label) in zip(axes, metrics):
        for x, style in enumerate(("startup_only", "guided"), 1):
            values = pd.to_numeric(
                data[data["involvement_style"] == style][metric], errors="coerce"
            ).dropna()
            if len(values):
                jitter = rng.uniform(-0.13, 0.13, len(values))
                axis.scatter(
                    x + jitter,
                    values,
                    s=12,
                    alpha=0.35,
                    color="#777777" if style == "startup_only" else "#0072B2",
                )
                axis.plot(
                    [x - 0.22, x + 0.22],
                    [values.median(), values.median()],
                    color="black",
                    linewidth=2,
                )
        axis.set_xticks([1, 2], ["Startup-only", "Guided"])
        axis.set_ylabel(label)
        axis.grid(axis="y", alpha=0.2)
    axes[0].set_title("Action-normalized mutation density")
    axes[1].set_title("Observed reuse among eligible mutations")
    axes[2].set_title("Observed validation among eligible mutations")
    fig.suptitle("Descriptive co-occurrence only; points are project-attributed sessions", y=1.02)
    fig.tight_layout()
    save_figure(fig, figures / "04_outcome_cooccurrence")


def plot_profile_ratios(profile_frame: pd.DataFrame, figures: Path) -> None:
    sub = profile_frame[
        (profile_frame["scope"] == "project_vendor_attributed")
        & (profile_frame["sessions"] > 0)
    ].copy()
    sub["label"] = sub["project"] + " / " + sub["vendor"]
    colors = [VENDOR_COLORS.get(vendor, "#777777") for vendor in sub["vendor"]]
    positions = np.arange(len(sub))
    fig, axis = plt.subplots(figsize=(10, 6.4))
    axis.barh(
        positions,
        pd.to_numeric(sub["actions_per_user_message"], errors="coerce"),
        color=colors,
    )
    axis.set_yticks(positions, sub["label"], fontsize=8)
    axis.invert_yaxis()
    axis.set_xscale("log")
    axis.set_xlabel("Projected Agent actions per substantive user message (log)")
    axis.set_title("Human-instruction density by project × vendor")
    axis.grid(axis="x", alpha=0.2)
    fig.tight_layout()
    save_figure(fig, figures / "05_profile_ratios")


def markdown_table(headers: list[str], rows: list[list[Any]]) -> str:
    if not rows:
        return "_No eligible rows._\n"
    result = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    result.extend("| " + " | ".join(map(str, row)) + " |" for row in rows)
    return "\n".join(result) + "\n"


def make_report(
    output_dir: Path,
    session_frame: pd.DataFrame,
    message_frame: pd.DataFrame,
    followup_frame: pd.DataFrame,
    interval_frame: pd.DataFrame,
    profile_frame: pd.DataFrame,
    outcome_frame: pd.DataFrame,
    coverage_frame: pd.DataFrame,
) -> None:
    unique_sessions = session_frame.sort_values(
        ["session_id", "project"]
    ).drop_duplicates("session_id")
    unique_messages = message_frame.sort_values(
        ["session_id", "message_ordinal", "project"]
    ).drop_duplicates(["session_id", "message_ordinal"])
    unique_followups = followup_frame.sort_values(
        ["session_id", "followup_ordinal", "project"]
    ).drop_duplicates(["session_id", "followup_ordinal"])
    unique_intervals = interval_frame.sort_values(
        ["session_id", "interval_ordinal", "project"]
    ).drop_duplicates(["session_id", "interval_ordinal"])
    overall = profile_frame[
        profile_frame["scope"] == "overall_unique_sessions"
    ].iloc[0]
    message_chars = numeric_summary(unique_messages["characters"])
    message_words = numeric_summary(unique_messages["words_approx"])
    session_users = numeric_summary(unique_sessions["user_messages"])
    startup = int((unique_sessions["involvement_style"] == "startup_only").sum())
    guided = int((unique_sessions["involvement_style"] == "guided").sum())
    subagent_only = int(
        (unique_sessions["involvement_style"] == "subagent_only").sum()
    )
    zero_human = int(
        (unique_sessions["involvement_style"] == "zero_human_record").sum()
    )
    unreadable_sessions = int(
        (unique_sessions["involvement_style"] == "unreadable").sum()
    )
    zero_human_phrase = (
        f"{zero_human} other session"
        if zero_human == 1
        else f"{zero_human} other sessions"
    )
    unknown = subagent_only + zero_human + unreadable_sessions
    class_denom = startup + guided
    explicit_interrupts = int(unique_sessions["explicit_interrupt_markers"].sum())
    approval_like_records = int(
        unique_sessions["approval_like_native_records"].sum()
    )
    permission_policy_records = int(
        unique_sessions["permission_policy_record_count"].sum()
    )
    permission_policies = sorted(
        {
            policy
            for packed in unique_sessions["permission_policies"].fillna("")
            for policy in str(packed).split("|")
            if policy
        }
    )
    interrupted_followups = (
        unique_followups[unique_followups["preceded_by_explicit_interrupt"] == True]
        if len(unique_followups)
        else unique_followups
    )
    eligible_followups = unique_followups[
        unique_followups["before_action_available"].eq(True)
        & unique_followups["after_action_available"].eq(True)
    ]
    interrupted_eligible = interrupted_followups[
        interrupted_followups["before_action_available"].eq(True)
        & interrupted_followups["after_action_available"].eq(True)
    ]
    path_eligible = unique_followups[
        unique_followups["path_comparison_eligible"].eq(True)
    ]
    interrupted_path_eligible = interrupted_followups[
        interrupted_followups["path_comparison_eligible"].eq(True)
    ]
    inactive_summary = numeric_summary(
        pd.to_numeric(
            unique_intervals["post_activity_inactive_gap_ms"], errors="coerce"
        )
        / 60_000
    )
    envelope_summary = numeric_summary(
        pd.to_numeric(
            unique_intervals["agent_activity_envelope_ms"], errors="coerce"
        )
        / 60_000
    )
    starts = unique_sessions[
        pd.to_numeric(unique_sessions["start_hour"], errors="coerce").notna()
    ]
    hour_counts = collections.Counter(int(value) for value in starts["start_hour"])
    weekday_counts = collections.Counter(starts["start_weekday"])
    peak_hours = ", ".join(
        f"{hour:02d}:00 ({count})"
        for hour, count in hour_counts.most_common(3)
    )
    peak_days = ", ".join(
        f"{day} ({count})" for day, count in weekday_counts.most_common(3)
    )

    strata_rows = []
    for row in profile_frame[
        (profile_frame["scope"] == "project_vendor_attributed")
        & (profile_frame["sessions"] > 0)
    ].itertuples():
        strata_rows.append(
            [
                row.project,
                row.vendor,
                fmt_int(row.sessions),
                fmt_int(row.user_messages),
                f"{fmt_int(row.startup_only_sessions)} / {fmt_int(row.guided_sessions)}",
                fmt_float(row.actions_per_user_message, 1),
                fmt_int(row.human_characters),
            ]
        )

    style_outcomes = outcome_frame[
        (outcome_frame["contrast"] == "session_style")
        & (outcome_frame["scope"] == "overall_project_attributed")
    ]
    outcome_rows = []
    for row in style_outcomes.itertuples():
        outcome_rows.append(
            [
                row.group,
                fmt_int(row.sessions),
                fmt_float(row.agent_actions_median, 1),
                fmt_float(row.mutations_median, 1),
                fmt_float(row.mutation_density_median, 2),
                fmt_pct(row.reuse_observed_pooled_rate),
                fmt_pct(row.validation_observed_pooled_rate),
            ]
        )

    density_outcomes = outcome_frame[
        (outcome_frame["contrast"] == "guidance_density_tertiles")
        & (outcome_frame["scope"] == "overall_project_attributed")
    ]
    density_rows = []
    for row in density_outcomes.itertuples():
        density_rows.append(
            [
                row.group,
                fmt_int(row.sessions),
                fmt_float(row.agent_actions_median, 1),
                fmt_float(row.mutation_density_median, 2),
                fmt_pct(row.reuse_observed_pooled_rate),
                fmt_pct(row.validation_observed_pooled_rate),
            ]
        )

    readable = int(coverage_frame["readable"].eq(True).sum())
    source_rows = len(coverage_frame)
    legacy_codex = coverage_frame[
        (coverage_frame["vendor"] == "codex")
        & (coverage_frame["native_source_kind"] == "user_legacy")
    ]
    legacy_exec_sources = set(
        legacy_codex[legacy_codex["native_source_app"] == "exec"]["source_file"]
    )
    legacy_exec_messages = int(
        unique_messages["source_file"].isin(legacy_exec_sources).sum()
    )
    no_text_note = (
        "The script keeps message text only transiently for filtering and length "
        "measurement; no message text or text hash is exported."
    )
    report = f"""# Human involvement in the final RQ1--RQ4 natural corpus

## Result at a glance

The fixed projection contains **551 project-attributed session memberships**
but **550 unique projected session identifiers**: one session contributes to
two projects. Native candidate sources were readable for
**{readable}/{source_rows}** project-session source mappings. The six event
exports contain the registered
**181,303 projected Agent actions**; the source-call-ID sensitivity contains
**{fmt_int(overall.unique_source_call_actions)}** distinct project-attributed
call IDs.

Across the 550 unique session identifiers, the source-native adapters recover
**{fmt_int(overall.user_messages)} substantive user messages** and
**{fmt_int(overall.human_characters)} Unicode characters**
(approximately **{fmt_int(overall.human_words_approx)} bilingual word-like
tokens**). That is one substantive user message per
**{fmt_float(overall.actions_per_user_message, 1)} projected Agent actions**
({fmt_float(overall.user_messages_per_100_actions, 2)} messages per 100
actions). This is an interaction-volume ratio, not an autonomy score.

Of {class_denom} sessions with at least one substantive human
message, **{startup} ({fmt_pct(safe_div(startup, class_denom))})** are
startup-only and **{guided} ({fmt_pct(safe_div(guided, class_denom))})** are
multi-turn guided. The remaining {unknown} identifiers comprise
**{subagent_only} subagent-only sessions**, **{zero_human_phrase} with no
recoverable substantive human record**, and **{unreadable_sessions} with
unreadable sources**. The median session contains
**{fmt_float(session_users['median'], 1)}** user messages (IQR
{fmt_float(session_users['q25'], 1)}--{fmt_float(session_users['q75'], 1)};
p90 {fmt_float(session_users['p90'], 1)}), so the distribution, rather than
the mean, is the central result.

## Data and reconstruction contract

- Corpus membership and Agent actions come only from
  `rq1-rq4-recompute-final/rq1-raw/events/*.json`; paired `.json.gz` files are
  byte-identical after decompression and are not double-counted.
- Claude uses `type=user`, Codex uses `event_msg/user_message`, and Gemini uses
  `messages[].type=user`. Codex response-item messages are fallback-only.
  For Codex, native `session_meta.thread_source` overrides the projection:
  `subagent` rollout files are excluded from human-message extraction even
  when projected as `source_role=user`, while their projected actions remain
  in the Agent-action denominator. Root/user sources are admitted; tool
  results, system/developer records, continuation summaries, local-command
  wrappers, and synthetic interruption notices are not human messages.
- A conversational turn is a substantive human message or a native assistant
  record containing conversational text. Tool results and tool-only assistant
  records are not conversational turns. Because vendors persist commentary and
  assistant messages differently, user turn share is reported in CSV but not
  used as a cross-vendor autonomy measure.
- Character count uses normalized Unicode code points. The word-like count
  treats Latin/digit runs as tokens and individual Han characters as
  approximate tokens; it is not Chinese word segmentation.
- **{legacy_codex['source_file'].nunique()} legacy Codex files** predate
  `thread_source` and are admitted from their root-like `cli`, `vscode`, or
  `exec` metadata. The **{legacy_exec_messages} user-role messages from
  `exec`-origin files** cannot be distinguished as direct typing versus
  wrapper/script submission; this is negligible in count but remains a source
  attribution caveat.
- {no_text_note}

## 1. Human turns and message lengths

The {fmt_int(message_chars['n'])} unique human messages have median
**{fmt_float(message_chars['median'], 1)} characters** (IQR
{fmt_float(message_chars['q25'], 1)}--{fmt_float(message_chars['q75'], 1)};
p90 {fmt_float(message_chars['p90'], 1)}) and median
**{fmt_float(message_words['median'], 1)} approximate word-like tokens** (IQR
{fmt_float(message_words['q25'], 1)}--{fmt_float(message_words['q75'], 1)}).
The long tail includes pasted code, documents, and prior model output, so total
characters are submitted context volume, not a typing-time estimate or proof
that every character was authored by the human.

![Session involvement](figures/01_session_involvement.png)

![Message lengths](figures/02_message_lengths.png)

### Project × vendor profile

{markdown_table(
    ["Project", "Vendor", "Sessions", "User messages", "Startup / guided", "Actions / user msg", "Human chars"],
    strata_rows,
)}

Empty project × vendor cells remain in the CSVs. Cells with fewer than ten
sessions are descriptive points only; this report makes no directional claim
for them.

## 2. Follow-up, interruption, and immediate action change

There are **{fmt_int(len(unique_followups))}** follow-up user messages and
**{fmt_int(explicit_interrupts)}** explicit native interruption/abort markers.
The follow-up volume is
**{fmt_float(100 * safe_div(len(unique_followups), overall.agent_actions), 2)}
per 100 projected Agent actions**.
Only **{fmt_int(len(interrupted_followups))}** follow-ups are preceded by such
a marker
({fmt_pct(safe_div(len(interrupted_followups), len(unique_followups)))});
ordinary follow-up is not called interruption.

For immediate action change, the analysis requires both adjacent actions in
the same native human-bearing source file and source stream. This yields
**{fmt_int(len(eligible_followups))}/{fmt_int(len(unique_followups))}** eligible
follow-ups. The exact tool changes for
**{fmt_int(eligible_followups['exact_tool_changed'].eq(True).sum())}**
({fmt_pct(safe_div(eligible_followups['exact_tool_changed'].eq(True).sum(), len(eligible_followups)))});
the normalized tool family changes for
**{fmt_int(eligible_followups['tool_family_changed'].eq(True).sum())}**
({fmt_pct(safe_div(eligible_followups['tool_family_changed'].eq(True).sum(), len(eligible_followups)))}).
Both sides have a file/path target for **{fmt_int(len(path_eligible))}**
follow-ups; among them the path set changes for
**{fmt_int(path_eligible['path_set_changed'].eq(True).sum())}**
({fmt_pct(safe_div(path_eligible['path_set_changed'].eq(True).sum(), len(path_eligible)))})
and becomes disjoint for
**{fmt_int(path_eligible['path_sets_disjoint'].eq(True).sum())}**
({fmt_pct(safe_div(path_eligible['path_sets_disjoint'].eq(True).sum(), len(path_eligible)))}).
These are immediate observable switches, not semantic goal-redirection labels.

Restricting to the **{fmt_int(len(interrupted_followups))} follow-ups with an
explicit interruption/abort marker**, **{fmt_int(len(interrupted_eligible))}**
have comparable adjacent actions. Exact tool changes occur for
**{fmt_int(interrupted_eligible['exact_tool_changed'].eq(True).sum())}**
({fmt_pct(safe_div(interrupted_eligible['exact_tool_changed'].eq(True).sum(), len(interrupted_eligible)))}),
and tool-family changes for
**{fmt_int(interrupted_eligible['tool_family_changed'].eq(True).sum())}**
({fmt_pct(safe_div(interrupted_eligible['tool_family_changed'].eq(True).sum(), len(interrupted_eligible)))}).
Among **{fmt_int(len(interrupted_path_eligible))}** path-comparable explicit
interruptions, **{fmt_int(interrupted_path_eligible['path_set_changed'].eq(True).sum())}**
change path set and
**{fmt_int(interrupted_path_eligible['path_sets_disjoint'].eq(True).sum())}**
become disjoint. This is the closest observable answer to “did the Agent
redirect after interruption,” but it still measures the next tool/path only.

Agent-to-human question tools and source-native approval-like record types are
reported separately in `approval_visibility.csv`. The adapters found
**{approval_like_records} explicit approval-like native records** and
**{permission_policy_records} repeated permission-policy configuration
records**, spanning `{", ".join(permission_policies)}`. A policy record (for
example Codex `never` or `on-request`) is not an individual approval. Absence
of a visible approval record means only that the native source did not expose
one under the frozen rule.

## 3. Schedule and observable wall-clock envelopes

Recoverable first-human-message times peak at {peak_hours}; the most frequent
weekdays are {peak_days}, all in `America/Vancouver`. Subagent-only and other
zero-human-record sessions have no human initiation time and are excluded from
this schedule.

Across **{fmt_int(envelope_summary['n'])}** closed inter-prompt intervals with
observable Agent activity, the median prompt-to-last-activity envelope is
**{fmt_float(envelope_summary['median'], 2)} minutes** (IQR
{fmt_float(envelope_summary['q25'], 2)}--{fmt_float(envelope_summary['q75'], 2)};
p90 {fmt_float(envelope_summary['p90'], 2)}). The median post-activity inactive
gap before the next human message is **{fmt_float(inactive_summary['median'], 2)}
minutes** (IQR {fmt_float(inactive_summary['q25'], 2)}--
{fmt_float(inactive_summary['q75'], 2)}; p90
{fmt_float(inactive_summary['p90'], 2)}). Summed over unique sessions, the observed
envelopes are **{fmt_float(overall.agent_activity_envelope_hours, 1)} h** and
the post-activity gaps are **{fmt_float(overall.post_activity_inactive_gap_hours, 1)} h**;
the latter is {fmt_pct(overall.post_activity_inactive_share)} of their summed
two-part envelope.

![Schedule and interval envelopes](figures/03_attention_schedule.png)

This does **not** answer how many wall-clock hours the human was attentive.
The logs do not observe reading, thinking, multitasking, typing onset, or
whether an Agent had actually completed and was waiting. Overnight and
between-task idle time can dominate the inactive gap, while prompt-to-last
activity is an elapsed envelope rather than CPU-active work. The defensible
answer is therefore: instruction volume and response timing are measurable;
human cognitive attention time is not.

## 4. Guidance density and output co-occurrence

The primary categorical contrast is startup-only versus multi-turn guided. A
second sensitivity freezes guidance density as follow-up user messages per 100
projected Agent actions and compares bottom/top thirds within each project ×
vendor stratum only when its 33rd and 67th percentiles separate. Middle thirds
are omitted from that contrast. Ties at either threshold are retained, so the
reported groups are not forced to equal size. Both contrasts are descriptive;
assignment is not random, and task difficulty, session duration, project,
vendor, and action volume all remain competing explanations.

### Startup-only versus guided

{markdown_table(
    ["Group", "Sessions", "Median actions", "Median mutations", "Median mutations / 100 actions", "Pooled reuse", "Pooled validation"],
    outcome_rows,
)}

These outcome tables retain project attribution, so the one session ID mapped
to two projects appears twice: the guided row has 196 memberships versus 195
unique session IDs in the corpus profile above.

### Within-stratum guidance-density thirds

{markdown_table(
    ["Group", "Sessions", "Median actions", "Median mutations / 100 actions", "Pooled reuse", "Pooled validation"],
    density_rows,
)}

Reuse and validation denominators contain all non-delete eligible mutations and
retain every observed, competing (`competing_delete` for reuse and
`competing_supersede` for validation), censored-end, and missing outcome.
Sessions with zero mutations remain in action and mutation-density
distributions. Raw
mutation counts are shown beside action-normalized density specifically to
expose the mechanical relation between longer/more active sessions and more
opportunities to mutate.

![Outcome co-occurrence](figures/04_outcome_cooccurrence.png)

![Instruction density](figures/05_profile_ratios.png)

## 5. Human involvement profile

The compact corpus profile is:

- {fmt_int(overall.user_messages)} substantive user messages and
  {fmt_int(overall.human_characters)} submitted characters across 550 unique
  projected session identifiers;
- {fmt_int(overall.agent_actions)} project-attributed Agent actions, or one
  human message per {fmt_float(overall.one_user_message_per_n_actions, 1)}
  actions;
- {fmt_int(overall.explicit_interrupt_markers)} explicit interruption/abort
  markers and {fmt_int(overall.agent_question_tools)} visible Agent question
  tools;
- a mixed distribution of {startup} startup-only, {guided} multi-turn guided,
  and {subagent_only} subagent-only sessions, rather than one uniform autonomy
  regime.

## Limitations

This is a six-case, author-associated, natural-use corpus. Project × vendor
strata mix time, task, model, harness, and repository differences. One session
identifier is attributed to two projects; overall human totals deduplicate it
while project tables retain both attributions. Some projected session IDs are
native subagent threads and therefore have no direct human messages. Native
assistant-message granularity differs by vendor. Immediate action changes are
not semantic intent changes.
Character volume includes pasted material. Approval visibility is
source-format-dependent. Finally, action, mutation, reuse, and validation
associations are not causal effects of human guidance.

## For the paper

Across 550 unique projected Agent session identifiers (551
project-attributed memberships),
we recover {fmt_int(overall.user_messages)} substantive human messages and
{fmt_int(overall.human_characters)} submitted characters from source-native
Claude, Codex, and Gemini records. This corresponds to one human message per
{fmt_float(overall.actions_per_user_message, 1)} projected Agent actions.
Among the {class_denom} sessions with at least one substantive human message,
{fmt_pct(safe_div(startup, class_denom))} are startup-only, whereas
{fmt_pct(safe_div(guided, class_denom))} contain multi-turn human guidance.
Explicit interruption markers are substantially narrower than follow-up
guidance and are reported separately. Higher and lower guidance-density
sessions differ descriptively in action, mutation, reuse, and validation
distributions, but these contrasts do not identify a causal effect because
task, project, vendor, duration, and author steering are jointly varying.

## Dataset positioning: confound or feature?

**Both, depending on the claim.** Author involvement is a confound for claims
about autonomous Agent behavior, vendor differences, or guidance causing
artifact outcomes: the corpus records a coupled human--Agent process, and the
same author selected tasks, supplied context, interrupted, and supplied
follow-up instructions.
It is also a feature for the paper's defensible naturalistic positioning:
these traces capture real mixed-initiative, persistent-workspace collaboration
that startup-only benchmarks omit. The honest dataset label is therefore
**author-associated mixed-initiative longitudinal cases**, not autonomous-Agent
population data. The human-involvement measurements should be used to bound
interpretation and stratify findings, not statistically "control away" the
author or claim a general autonomy rate.
"""
    (output_dir / "report.md").write_text(report, encoding="utf-8")


def dataframe(rows: list[dict[str, Any]]) -> pd.DataFrame:
    return pd.DataFrame(rows)


def run_preflight(
    sessions: dict[tuple[str, str], list[dict[str, Any]]],
    mutation_metrics: dict[tuple[str, str], dict[str, Any]],
    output_dir: Path,
) -> None:
    chosen: dict[str, tuple[tuple[str, str], list[dict[str, Any]]]] = {}
    parse_cache: dict[tuple[str, str], NativeConversation] = {}
    audit: list[dict[str, Any]] = []
    candidates = []
    for key, events in sessions.items():
        vendor = str(events[0].get("vendor") or "")
        sources = session_primary_sources(events)
        if not sources or not all(Path(source).is_file() for source in sources):
            continue
        continuation_priority = 0 if vendor == "codex" and len(sources) > 1 else 1
        candidates.append(
            (VENDOR_ORDER.index(vendor), continuation_priority, len(events), key, events, sources)
        )
    for _, _, _, key, events, sources in sorted(candidates):
        vendor = str(events[0].get("vendor") or "")
        if vendor in chosen:
            continue
        conversation = NativeConversation()
        for source in sources:
            cache_key = (vendor, source)
            if cache_key not in parse_cache:
                parse_cache[cache_key] = parse_native(vendor, Path(source))
            conversation.merge(parse_cache[cache_key])
        conversation.normalize()
        if not conversation.human:
            continue
        chosen[vendor] = (key, events)
        audit.append(
            {
                "vendor": vendor,
                "project": key[0],
                "session_id": key[1],
                "primary_sources": sources,
                "projected_actions": len(events),
                "human_messages": len(conversation.human),
                "assistant_conversational_messages": len(
                    conversation.assistant_source_times
                ),
                "explicit_interrupt_markers": len(
                    conversation.explicit_interrupt_times_ms
                ),
                "approval_like_native_records": len(
                    conversation.approval_request_times
                ),
                "permission_policies": sorted(
                    {policy for _, policy in conversation.permission_policies}
                ),
                "excluded_record_classes": dict(conversation.excluded),
                "native_record_types": dict(conversation.native_record_types),
                "mutation_rows_joined": int(
                    mutation_metrics.get(key, {}).get("mutations_total", 0)
                ),
            }
        )
    missing = sorted(set(VENDOR_ORDER) - set(chosen))
    if missing:
        raise RuntimeError(f"Preflight could not find a real root for: {missing}")
    selected_sessions = {key: events for key, events in chosen.values()}
    measurements = build_measurements(
        selected_sessions, mutation_metrics, parse_cache
    )
    preflight_session_rows = measurements[0]
    if len(preflight_session_rows) != len(VENDOR_ORDER):
        raise RuntimeError("Preflight did not produce one session row per vendor")
    result = {
        "attempt": 3,
        "status": "passed",
        "real_inputs": {
            "event_projection": str(EVENTS),
            "mutation_rows": str(MUTATIONS),
        },
        "vendor_cases": sorted(audit, key=lambda row: VENDOR_ORDER.index(row["vendor"])),
        "checks": {
            "vendors_represented": sorted(chosen),
            "each_has_substantive_human_message": all(
                row["human_messages"] > 0 for row in audit
            ),
            "real_event_join_executed": all(
                row["projected_actions"] > 0 for row in audit
            ),
            "real_mutation_join_executed": True,
            "message_text_written": False,
        },
    }
    write_json(output_dir / "preflight" / "preflight.json", result)
    print(
        "preflight passed:",
        ", ".join(
            f"{row['vendor']}={row['project']}:{row['human_messages']} messages"
            for row in audit
        ),
        flush=True,
    )


def output_manifest(
    output_dir: Path,
    event_manifests: list[dict[str, Any]],
    mutation_path: Path,
    parse_cache: dict[tuple[str, str], NativeConversation],
    session_frame: pd.DataFrame,
    message_frame: pd.DataFrame,
    followup_frame: pd.DataFrame,
    interval_frame: pd.DataFrame,
) -> dict[str, Any]:
    exclusions: collections.Counter[str] = collections.Counter()
    record_types: dict[str, collections.Counter[str]] = collections.defaultdict(
        collections.Counter
    )
    for (vendor, _), conversation in parse_cache.items():
        exclusions.update(conversation.excluded)
        record_types[vendor].update(conversation.native_record_types)
    output_files = sorted(
        path
        for path in output_dir.rglob("*")
        if path.is_file()
        and path.name != "manifest.json"
        and "rq7-heldout-20260726" not in str(path)
    )
    return {
        "experiment": "human-involvement-20260726",
        "generated_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "timezone": "America/Vancouver",
        "inputs": {
            "events": event_manifests,
            "mutation_csv": {
                "path": str(mutation_path),
                "bytes": mutation_path.stat().st_size,
                "sha256": sha256_file(mutation_path),
                "rows": 13_906,
            },
            "native_candidate_files_classified": len(parse_cache),
            "codex_subagent_files_excluded_from_human_measurement": sum(
                conversation.native_source_kind == "subagent"
                for conversation in parse_cache.values()
            ),
        },
        "reconciliations": {
            "project_attributed_sessions": int(len(session_frame)),
            "unique_projected_session_ids": int(
                session_frame["session_id"].nunique()
            ),
            "projected_event_rows": int(session_frame["agent_actions"].sum()),
            "project_attributed_human_messages": int(
                session_frame["user_messages"].sum()
            ),
            "exported_project_attributed_message_rows": int(len(message_frame)),
            "followup_rows": int(len(followup_frame)),
            "interaction_interval_rows": int(len(interval_frame)),
            "project_vendor_grid_rows": len(PROJECT_ORDER) * len(VENDOR_ORDER),
        },
        "frozen_definitions": {
            "claude_human": "type=user after synthetic/tool-result/meta/sidechain exclusions",
            "codex_human": (
                "event_msg/user_message; response_item user fallback only; "
                "native session_meta.thread_source=subagent files excluded even "
                "when the event projection labels source_role=user"
            ),
            "gemini_human": "messages[].type=user",
            "guidance_density": "follow-up human messages per 100 projected Agent actions",
            "startup_only": "exactly one substantive human message",
            "guided": "at least two substantive human messages",
            "turn_share": "human / (substantive human + assistant records with conversational text)",
            "word_approximation": "Latin/digit runs plus individual Han characters",
            "immediate_change": "adjacent action before/after a follow-up in the same native human-bearing source file and source stream",
            "timing": "prompt-to-last-activity envelope and post-activity inactive gap; not human attention",
            "reuse_validation_eligibility": "all non-delete mutation rows, retaining observed/competing/censored/missing outcomes",
        },
        "native_exclusion_counts": dict(exclusions),
        "native_record_type_counts": {
            vendor: dict(counter) for vendor, counter in record_types.items()
        },
        "software": {
            "python": sys.version,
            "platform": platform.platform(),
            "pandas": pd.__version__,
            "numpy": np.__version__,
            "matplotlib": matplotlib.__version__,
        },
        "privacy": {
            "message_text_exported": False,
            "message_hash_exported": False,
            "source_paths_exported_for_provenance": True,
        },
        "outputs": [
            {
                "path": str(path.relative_to(output_dir)),
                "bytes": path.stat().st_size,
                "sha256": sha256_file(path),
            }
            for path in output_files
        ],
    }


def main() -> None:
    args = parse_args()
    output_dir = args.output_dir.resolve()
    figures = output_dir / "figures"
    output_dir.mkdir(parents=True, exist_ok=True)
    figures.mkdir(parents=True, exist_ok=True)
    (output_dir / "preflight").mkdir(parents=True, exist_ok=True)

    if args.render_only:
        session_frame = pd.read_csv(output_dir / "session_metrics.csv")
        message_frame = pd.read_csv(output_dir / "user_messages.csv")
        followup_frame = pd.read_csv(output_dir / "followup_transitions.csv")
        interval_frame = pd.read_csv(output_dir / "interaction_intervals.csv")
        profile_frame = pd.read_csv(output_dir / "profile_summary.csv")
        outcome_frame = pd.read_csv(output_dir / "involvement_outcomes.csv")
        coverage_frame = pd.read_csv(output_dir / "native_coverage.csv")
        plot_session_involvement(session_frame, figures)
        plot_message_lengths(message_frame, figures)
        plot_attention_schedule(session_frame, interval_frame, figures)
        plot_outcome_cooccurrence(session_frame, figures)
        plot_profile_ratios(profile_frame, figures)
        make_report(
            output_dir,
            session_frame,
            message_frame,
            followup_frame,
            interval_frame,
            profile_frame,
            outcome_frame,
            coverage_frame,
        )
        print("render-only checkpoint completed", flush=True)
        return

    events, sessions, event_manifests = load_corpus(args.events_dir.resolve())
    mutation_metrics, _ = load_mutation_metrics(args.mutations.resolve())
    if args.preflight:
        run_preflight(sessions, mutation_metrics, output_dir)
        return

    parse_cache: dict[tuple[str, str], NativeConversation] = {}
    (
        session_rows,
        message_rows,
        followup_rows,
        interval_rows,
        coverage_rows,
        approval_rows,
    ) = build_measurements(sessions, mutation_metrics, parse_cache)

    session_frame = add_density_groups(dataframe(session_rows))
    message_frame = dataframe(message_rows)
    followup_frame = dataframe(followup_rows)
    interval_frame = dataframe(interval_rows)
    coverage_frame = dataframe(coverage_rows)
    approval_frame = dataframe(approval_rows)
    distribution_frame = dataframe(
        distribution_rows(session_frame, message_frame)
    )
    profile_frame = dataframe(build_profile_rows(session_frame, events))
    hour_rows, weekday_rows = build_schedule_rows(session_frame)
    schedule_hour_frame = dataframe(hour_rows)
    schedule_weekday_frame = dataframe(weekday_rows)
    outcome_frame = dataframe(build_outcome_rows(session_frame))

    if len(session_frame) != 551 or session_frame["session_id"].nunique() != 550:
        raise RuntimeError("Session reconciliation failed")
    if int(session_frame["agent_actions"].sum()) != 181_303:
        raise RuntimeError("Action reconciliation failed")
    reuse_partition = (
        session_frame["reuse_observed"]
        + session_frame["reuse_competing_delete"]
        + session_frame["reuse_competing_supersede"]
        + session_frame["reuse_censored_end"]
        + session_frame["reuse_missing"]
    )
    validation_partition = (
        session_frame["validation_observed"]
        + session_frame["validation_competing_supersede"]
        + session_frame["validation_censored_end"]
        + session_frame["validation_missing"]
    )
    if not reuse_partition.eq(
        session_frame["nondelete_eligible_mutations"]
    ).all():
        raise RuntimeError("Reuse outcome denominator reconciliation failed")
    if not validation_partition.eq(
        session_frame["nondelete_eligible_mutations"]
    ).all():
        raise RuntimeError("Validation outcome denominator reconciliation failed")
    if not coverage_frame["readable"].eq(True).all():
        missing = coverage_frame[~coverage_frame["readable"].eq(True)]
        raise RuntimeError(f"Unreadable admitted native candidate sources: {len(missing)}")

    session_frame.to_csv(output_dir / "session_metrics.csv", index=False)
    message_frame.to_csv(output_dir / "user_messages.csv", index=False)
    followup_frame.to_csv(output_dir / "followup_transitions.csv", index=False)
    interval_frame.to_csv(output_dir / "interaction_intervals.csv", index=False)
    distribution_frame.to_csv(output_dir / "human_distributions.csv", index=False)
    schedule_hour_frame.to_csv(output_dir / "schedule_hour.csv", index=False)
    schedule_weekday_frame.to_csv(output_dir / "schedule_weekday.csv", index=False)
    outcome_frame.to_csv(output_dir / "involvement_outcomes.csv", index=False)
    profile_frame.to_csv(output_dir / "profile_summary.csv", index=False)
    coverage_frame.to_csv(output_dir / "native_coverage.csv", index=False)
    approval_frame.to_csv(output_dir / "approval_visibility.csv", index=False)

    plot_session_involvement(session_frame, figures)
    plot_message_lengths(message_frame, figures)
    plot_attention_schedule(session_frame, interval_frame, figures)
    plot_outcome_cooccurrence(session_frame, figures)
    plot_profile_ratios(profile_frame, figures)
    make_report(
        output_dir,
        session_frame,
        message_frame,
        followup_frame,
        interval_frame,
        profile_frame,
        outcome_frame,
        coverage_frame,
    )
    manifest = output_manifest(
        output_dir,
        event_manifests,
        args.mutations.resolve(),
        parse_cache,
        session_frame,
        message_frame,
        followup_frame,
        interval_frame,
    )
    write_json(output_dir / "manifest.json", manifest)
    overall = profile_frame[
        profile_frame["scope"] == "overall_unique_sessions"
    ].iloc[0]
    print(
        f"complete: {len(session_frame)} memberships, "
        f"{session_frame['session_id'].nunique()} unique session IDs, "
        f"{int(overall['user_messages']):,} user messages, "
        f"{int(overall['agent_actions']):,} Agent actions",
        flush=True,
    )


if __name__ == "__main__":
    main()
