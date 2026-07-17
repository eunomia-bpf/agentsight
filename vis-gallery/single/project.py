#!/usr/bin/env python3
"""Build compact data for one repository visualization."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import subprocess
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from itertools import combinations
from pathlib import Path
from typing import Any


HOUR_MS = 60 * 60 * 1_000
SOURCE_EXTENSIONS = {
    ".c",
    ".cc",
    ".cpp",
    ".css",
    ".go",
    ".h",
    ".html",
    ".js",
    ".jsx",
    ".md",
    ".py",
    ".rs",
    ".sh",
    ".toml",
    ".ts",
    ".tsx",
    ".yaml",
    ".yml",
}
BLAME_HEADER = re.compile(r"^([0-9a-f]{40})\s+\d+\s+(\d+)(?:\s+\d+)?$")


def compact_hash(value: str, size: int = 12) -> str:
    return hashlib.sha256(value.encode()).hexdigest()[:size]


def group_for_path(path: str) -> str:
    parts = path.split("/")
    if len(parts) == 1:
        return "(root)"
    return "/".join(parts[: min(2, len(parts) - 1)])


def hour_floor(timestamp_ms: int) -> int:
    return timestamp_ms // HOUR_MS * HOUR_MS


def date_label(timestamp_ms: int) -> str:
    return datetime.fromtimestamp(timestamp_ms / 1000, timezone.utc).date().isoformat()


def run_git(repo: Path, *args: str) -> bytes:
    result = subprocess.run(
        ["git", "-C", str(repo), *args], check=True, capture_output=True
    )
    return result.stdout


def endpoint_files(repo: Path, head: str) -> dict[str, int]:
    output = run_git(repo, "ls-tree", "-r", "-z", "--long", head)
    files = {}
    for record in output.split(b"\0"):
        if not record:
            continue
        metadata, separator, raw_path = record.partition(b"\t")
        if not separator:
            continue
        fields = metadata.decode("utf-8", errors="replace").split()
        if len(fields) < 4 or fields[1] != "blob":
            continue
        path = raw_path.decode("utf-8", errors="replace")
        files[path] = int(fields[3]) if fields[3].isdigit() else 0
    return files


def lightweight_commits(repo: Path, head: str, since_ms: int, until_ms: int) -> list[dict[str, Any]]:
    output = run_git(
        repo,
        "log",
        "--first-parent",
        "--format=%H%x1f%P%x1f%ct%x1f%an%x1e",
        head,
    )
    rows = []
    for record in output.split(b"\x1e"):
        fields = record.strip().split(b"\x1f")
        if len(fields) < 4:
            continue
        timestamp = int(fields[2]) * 1_000
        if not since_ms <= timestamp <= until_ms:
            continue
        commit_id = fields[0].decode("ascii", errors="replace")
        parents = fields[1].decode("ascii", errors="replace").split()
        author = fields[3].decode("utf-8", errors="replace").strip()
        rows.append(
            {
                "id": commit_id,
                "parents": parents,
                "committed_at_ms": timestamp,
                "author_label": f"author-{compact_hash(author, 8)}",
                "is_merge": len(parents) > 1,
            }
        )
    return sorted(rows, key=lambda row: (row["committed_at_ms"], row["id"]))


def parse_blame(repo: Path, head: str, path: str) -> list[dict[str, Any]]:
    try:
        output = run_git(
            repo, "blame", "-M", "--line-porcelain", head, "--", path
        ).decode("utf-8", errors="replace")
    except subprocess.CalledProcessError:
        return []
    rows = []
    commit = ""
    final_line = 0
    author = "unknown"
    author_time = 0
    for line in output.splitlines():
        match = BLAME_HEADER.match(line)
        if match:
            commit = match.group(1)
            final_line = int(match.group(2))
            author = "unknown"
            author_time = 0
        elif line.startswith("author "):
            author = line.removeprefix("author ")
        elif line.startswith("author-time "):
            author_time = int(line.removeprefix("author-time ")) * 1_000
        elif line.startswith("\t"):
            rows.append(
                {
                    "path": path,
                    "line": final_line,
                    "origin_commit": commit[:12],
                    "origin_ms": author_time,
                    "author_label": f"author-{compact_hash(author, 8)}",
                }
            )
    return rows


def pattern_name(file: dict[str, Any], window_start: int, window_end: int) -> str:
    lifetime_ms = None
    if file.get("death_ms"):
        lifetime_ms = int(file["death_ms"]) - int(file["birth_ms"])
    if lifetime_ms is not None and lifetime_ms <= 7 * 24 * HOUR_MS:
        return "Dayfly"
    daily = file["daily"]
    active_days = sum(value.get("touches", 0) > 0 for value in daily.values())
    max_growth = max((value.get("additions", 0) for value in daily.values()), default=0)
    if max_growth >= 300 or file["additions"] >= 1_000:
        return "Supernova"
    if active_days >= 3 and file["touches"] >= 12:
        return "Pulsar"
    if file["deletions"] > file["additions"] * 1.5 and file["deletions"] >= 20:
        return "White Dwarf"
    if file["touches"] == 0 and int(file["birth_ms"]) < window_start:
        return "Fossil"
    if int(file["birth_ms"]) >= window_start and int(file["birth_ms"]) <= window_end:
        return "Nova"
    return "Steady"


def build(
    artifacts: list[dict[str, Any]],
    repo: Path,
    lean_nebula: bool = False,
) -> dict[str, Any]:
    heads = {artifact["repository"]["head"] for artifact in artifacts}
    if len(heads) != 1:
        raise ValueError("gallery inputs must share a frozen repository endpoint")
    head = next(iter(heads))
    repository = artifacts[0]["repository"]
    path_events: list[dict[str, Any]] = []
    agent_events: dict[str, dict[str, Any]] = {}
    verification_events: dict[str, dict[str, Any]] = {}
    sessions: dict[str, dict[str, Any]] = {}
    commits: dict[str, dict[str, Any]] = {}
    changes: dict[str, dict[str, Any]] = {}
    buckets: dict[int, Counter] = defaultdict(Counter)
    file_stats: dict[str, dict[str, Any]] = {}
    day_stats: dict[str, dict[str, Any]] = defaultdict(
        lambda: {
            "sessions": set(),
            "events": 0,
            "path_events": 0,
            "write_event_paths": 0,
            "verification_events": 0,
        }
    )
    session_days: dict[str, set[str]] = defaultdict(set)
    lifetimes = artifacts[-1]["file_lifetimes"]

    lifetimes_for_path: dict[str, list[dict[str, Any]]] = defaultdict(list)
    endpoint_lifetime_for_path: dict[str, dict[str, Any]] = {}
    for lifetime in lifetimes:
        for path in lifetime["paths"]:
            lifetimes_for_path[path].append(lifetime)
        if lifetime["survives_to_head"] and lifetime.get("current_path"):
            current_path = lifetime["current_path"]
            if current_path in endpoint_lifetime_for_path:
                raise ValueError(f"multiple surviving lifetimes for endpoint path {current_path}")
            endpoint_lifetime_for_path[current_path] = lifetime

    def lifetime_for_record(path: str) -> dict[str, Any] | None:
        endpoint = endpoint_lifetime_for_path.get(path)
        if endpoint is not None:
            return endpoint
        candidates = lifetimes_for_path.get(path, [])
        return max(
            candidates,
            key=lambda value: (int(value["birth_ms"]), value["id"]),
            default=None,
        )

    censored_days: set[str] = set()
    now_ms = int(datetime.now(timezone.utc).timestamp() * 1_000)
    for artifact in artifacts:
        retrieval_after_ms = int(artifact["window"].get("retrieval_after_ms", 0))
        if int(artifact["window"]["until_ms"]) >= now_ms - retrieval_after_ms:
            maturity_cutoff = now_ms - retrieval_after_ms
            censored_days.update(
                date_label(int(event["ts_ms"]))
                for event in artifact["events"]
                if event.get("write_paths") and int(event["ts_ms"]) > maturity_cutoff
            )
    for artifact in artifacts:
        changes_by_id = {row["id"]: row for row in artifact["changes"]}
        association_index = {
            (row["event_id"], row["path"]): row
            for row in artifact["associations"]
        }
        durable_by_event: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for association in artifact["associations"]:
            top = association["candidates"][0] if association["candidates"] else None
            change = changes_by_id.get(top["change_id"]) if top else None
            if not change or change["status"][:1] not in {"A", "D", "R", "C"}:
                continue
            durable_by_event[association["event_id"]].append(
                {
                    "status": change["status"],
                    "path": change["path"],
                    "old_path": change.get("old_path"),
                    "lifetime_id": change["lifetime_id"],
                    "association_state": association["state"],
                    "evidence_bin": top["evidence_bin"],
                }
            )
        for session in artifact["sessions"]:
            current = sessions.setdefault(
                session["id"],
                {
                    "id": session["id"],
                    "conversation_id": session.get("conversation_id"),
                    "vendor": session["vendor"],
                    "model": session.get("model") or "unknown",
                    "started_at_ms": session.get("started_at_ms"),
                    "ended_at_ms": session.get("ended_at_ms"),
                    "tool_events": 0,
                    "reported_tokens": 0,
                    "days": [],
                },
            )
            starts = [value for value in [current["started_at_ms"], session.get("started_at_ms")] if value]
            ends = [value for value in [current["ended_at_ms"], session.get("ended_at_ms")] if value]
            current["started_at_ms"] = min(starts) if starts else None
            current["ended_at_ms"] = max(ends) if ends else None
            current["tool_events"] = max(current["tool_events"], int(session["tool_events"]))
            current["reported_tokens"] = max(current["reported_tokens"], int(session["total_tokens"]))
        for event in artifact["events"]:
            timestamp = int(event["ts_ms"])
            agent_events.setdefault(
                event["id"],
                {
                    "id": event["id"],
                    "session_id": event["session_id"],
                    "vendor": event["vendor"],
                    "model": event.get("model") or "unknown",
                    "ts_ms": timestamp,
                    "kind": event["kind"],
                    "action": event["action"],
                    "category": event["category"],
                    "effect": event["effect"],
                    "status": event["status"],
                    "prompt_index": event["prompt_index"],
                    "paths": list(event["paths"]),
                    "read_paths": list(event.get("read_paths", [])),
                    "write_paths": list(event.get("write_paths", [])),
                    "path_groups": list(event.get("path_groups", [])),
                    "process_chain": list(event.get("process_chain", [])),
                    "domains": list(event.get("domains", [])),
                    "durable_changes": durable_by_event.get(event["id"], []),
                },
            )
            day = date_label(timestamp)
            stats = day_stats[day]
            stats["sessions"].add(event["session_id"])
            stats["events"] += 1
            stats["path_events"] += int(bool(event["paths"]))
            stats["write_event_paths"] += len(event.get("write_paths", []))
            stats["verification_events"] += int(event["effect"] == "test")
            session_days[event["session_id"]].add(day)
            bucket = buckets[hour_floor(timestamp)]
            bucket["events"] += 1
            bucket[event["effect"]] += 1
            token_value = int(event["input_tokens"]) + int(event["output_tokens"]) + int(event["cache_tokens"])
            bucket["reported_tokens"] += token_value
            if event["effect"] == "test":
                verification_events[event["id"]] = {
                    "id": event["id"],
                    "session_id": event["session_id"],
                    "vendor": event["vendor"],
                    "ts_ms": timestamp,
                    "day": day,
                    "action": event["action"],
                    "status": event["status"],
                }
            if not event["paths"]:
                continue
            write_paths = set(event.get("write_paths", []))
            for path in event["paths"]:
                path_effect = (
                    "write"
                    if path in write_paths
                    else "read" if event["effect"] == "write" else event["effect"]
                )
                association = (
                    association_index.get((event["id"], path))
                    if path_effect == "write" and day not in censored_days
                    else None
                )
                if (
                    not lean_nebula
                    and
                    day not in censored_days
                    and path_effect == "write"
                    and association is None
                ):
                    raise ValueError(
                        f"mature write path has no association row: {event['id']} {path}"
                    )
                state = association["state"] if association else "not_eligible"
                top = association["candidates"][0] if association and association["candidates"] else None
                row = {
                    "id": f"{event['id']}:{compact_hash(path, 8)}",
                    "event_id": event["id"],
                    "session_id": event["session_id"],
                    "vendor": event["vendor"],
                    "model": event.get("model") or "unknown",
                    "ts_ms": timestamp,
                    "day": day,
                    "action": event["action"],
                    "category": event["category"],
                    "effect": path_effect,
                    "status": event["status"],
                    "prompt_index": event["prompt_index"],
                    "path": path,
                    "group": group_for_path(path),
                    "association_state": state,
                    "candidate_count": len(association["candidates"]) if association else 0,
                    "evidence_bin": top["evidence_bin"] if top else None,
                    "exact_hunk": bool(top and top["exact_hunk_match"]),
                }
                path_events.append(row)
                file = file_stats.setdefault(
                    path,
                    new_file_stats(
                        path,
                        lifetime_for_record(path),
                        lifetimes_for_path.get(path, []),
                    ),
                )
                file["touches"] += 1
                effect_key = {
                    "read": "read_events",
                    "write": "write_events",
                    "test": "verify_events",
                }.get(path_effect, "other_events")
                file[effect_key] += 1
                file["effect_counts"][path_effect] += 1
                file["vendors"].add(event["vendor"])
                file["sessions"].add(event["session_id"])
                file["first_event_ms"] = min(file["first_event_ms"] or timestamp, timestamp)
                file["last_event_ms"] = max(file["last_event_ms"] or timestamp, timestamp)
                file["daily"][day]["touches"] += 1
                file["association_states"][state] += 1

        for commit in artifact["commits"]:
            commits[commit["id"]] = commit
        for change in artifact["changes"]:
            changes[change["id"]] = change

    for commit in commits.values():
        bucket = buckets[hour_floor(int(commit["committed_at_ms"]))]
        bucket["commits"] += 1
        if commit["is_merge"]:
            bucket["merges"] += 1
    for change in changes.values():
        path = change["path"]
        file = file_stats.setdefault(
            path,
            new_file_stats(
                path,
                lifetime_for_record(path),
                lifetimes_for_path.get(path, []),
            ),
        )
        additions = int(change["additions"])
        deletions = int(change["deletions"])
        file["git_changes"] += 1
        file["additions"] += additions
        file["deletions"] += deletions
        file["authors"].add(commits.get(change["commit_id"], {}).get("author_label", "unknown"))
        day = date_label(int(change["committed_at_ms"]))
        file["daily"][day]["additions"] += additions
        file["daily"][day]["deletions"] += deletions
        bucket = buckets[hour_floor(int(change["committed_at_ms"]))]
        bucket["additions"] += additions
        bucket["deletions"] += deletions

    for session_id, session in sessions.items():
        session["days"] = sorted(session_days.get(session_id, set()))

    source_days = [
        {
            "day": day,
            "sessions": len(values["sessions"]),
            "events": values["events"],
            "path_events": values["path_events"],
            "write_event_paths": values["write_event_paths"],
            "verification_events": values["verification_events"],
            "quantitative_status": (
                "right_censored_excluded"
                if day in censored_days
                else "mature_descriptive"
            ),
        }
        for day, values in sorted(day_stats.items())
    ]

    if lean_nebula and not lifetimes:
        for path, size in endpoint_files(repo, head).items():
            file = file_stats.setdefault(path, new_file_stats(path, None, []))
            file["survives_to_head"] = True
            file["current_path"] = path
            file["current_bytes"] = size
        for commit in lightweight_commits(
            repo,
            head,
            min(int(artifact["window"]["since_ms"]) for artifact in artifacts),
            max(int(artifact["window"]["until_ms"]) for artifact in artifacts),
        ):
            commits[commit["id"]] = commit

    # Seed every frozen endpoint path even if it was untouched in the sampled
    # native-session windows. The endpoint map must represent the repository
    # tree, not only paths that happened to receive an event.
    for path, lifetime in endpoint_lifetime_for_path.items():
        file_stats.setdefault(
            path,
            new_file_stats(path, lifetime, lifetimes_for_path.get(path, [])),
        )

    # Keep the requested observation window, including periods with no native
    # events. Trimming to the first/last path event would hide agent silence and
    # discard Git or verification evidence near the window boundaries.
    window_start = min(int(artifact["window"]["since_ms"]) for artifact in artifacts)
    window_end = max(int(artifact["window"]["until_ms"]) for artifact in artifacts)
    files = finalize_files(file_stats, window_start, window_end)
    cochange_edges = [] if lean_nebula else build_cochange_edges(changes.values())
    blame_rows = [] if lean_nebula else build_blame_rows(repo, head, files)
    tree = build_tree(files)
    endpoint_paths = (
        {
            file["path"]
            for file in files
            if file["survives_to_head"] and file.get("current_path") == file["path"]
        }
        if lean_nebula
        else set(endpoint_lifetime_for_path)
    )
    projected_endpoint_paths = tree_leaf_paths(tree)
    if projected_endpoint_paths != endpoint_paths:
        missing = sorted(endpoint_paths - projected_endpoint_paths)
        extra = sorted(projected_endpoint_paths - endpoint_paths)
        raise ValueError(
            f"endpoint tree mismatch: missing={missing[:5]} extra={extra[:5]}"
        )
    time_buckets = [
        {"ts_ms": timestamp, **dict(counter)}
        for timestamp, counter in sorted(buckets.items())
        if window_start - 24 * HOUR_MS <= timestamp <= window_end + 24 * HOUR_MS
    ]
    meta = {
        "repository": repository["name"],
        "endpoint_revision": head,
        "window_start_ms": window_start,
        "window_end_ms": window_end,
        "session_scope": (
            "global_tool_operations"
            if any(artifact["window"].get("global", False) for artifact in artifacts)
            else "repository_identity"
        ),
    }
    projected_lifetimes = [
        {
            key: lifetime.get(key)
            for key in [
                "id", "paths", "birth_ms", "death_ms", "current_path",
                "current_bytes", "survives_to_head",
            ]
        }
        for lifetime in lifetimes
    ]
    sorted_agent_events = sorted(
        agent_events.values(), key=lambda row: (row["ts_ms"], row["id"])
    )
    sorted_commits = sorted(
        commits.values(), key=lambda row: (row["committed_at_ms"], row["id"])
    )
    if lean_nebula:
        return {
            "meta": meta,
            "agent_events": sorted_agent_events,
            "files": files,
            "commits": sorted_commits,
            "file_lifetimes": projected_lifetimes,
        }
    return {
        "meta": meta,
        "source_days": source_days,
        "sessions": sorted(sessions.values(), key=lambda row: (row["started_at_ms"] or 0, row["id"])),
        "agent_events": sorted_agent_events,
        "events": sorted(path_events, key=lambda row: (row["ts_ms"], row["id"])),
        "verification_events": sorted(
            verification_events.values(), key=lambda row: (row["ts_ms"], row["id"])
        ),
        "time_buckets": time_buckets,
        "files": files,
        "tree": tree,
        "commits": sorted_commits,
        "changes": [
            {
                key: row.get(key)
                for key in [
                    "id",
                    "commit_id",
                    "committed_at_ms",
                    "status",
                    "old_path",
                    "path",
                    "additions",
                    "deletions",
                    "lifetime_id",
                    "is_merge",
                ]
            }
            for row in sorted(
                changes.values(), key=lambda value: (value["committed_at_ms"], value["id"])
            )
        ],
        "file_lifetimes": projected_lifetimes,
        "cochange_edges": cochange_edges,
        "line_pixels": blame_rows,
        "survival_cohorts": [] if lean_nebula else build_survival_cohorts(lifetimes),
        "ownership": [] if lean_nebula else build_ownership(changes.values(), commits),
    }


def new_file_stats(
    path: str,
    lifetime: dict[str, Any] | None,
    matching_lifetimes: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    lifetime = lifetime or {}
    matching_lifetimes = matching_lifetimes or []
    return {
        "path": path,
        "group": group_for_path(path),
        "extension": Path(path).suffix.lower() or "(none)",
        "lifetime_id": lifetime.get("id"),
        "lifetime_ids": sorted(value["id"] for value in matching_lifetimes),
        "birth_ms": lifetime.get("birth_ms", 0),
        "death_ms": lifetime.get("death_ms"),
        "survives_to_head": lifetime.get("survives_to_head", False),
        "current_path": lifetime.get("current_path"),
        "current_bytes": lifetime.get("current_bytes") or 0,
        "touches": 0,
        "read_events": 0,
        "write_events": 0,
        "verify_events": 0,
        "other_events": 0,
        "git_changes": 0,
        "additions": 0,
        "deletions": 0,
        "vendors": set(),
        "sessions": set(),
        "authors": set(),
        "first_event_ms": None,
        "last_event_ms": None,
        "daily": defaultdict(Counter),
        "association_states": Counter(),
        "effect_counts": Counter(),
    }


def finalize_files(
    file_stats: dict[str, dict[str, Any]], window_start: int, window_end: int
) -> list[dict[str, Any]]:
    output = []
    for path, file in file_stats.items():
        serial = {
            **file,
            "vendors": sorted(file["vendors"]),
            "sessions": sorted(file["sessions"]),
            "authors": sorted(file["authors"]),
            "daily": {
                day: dict(counter) for day, counter in sorted(file["daily"].items())
            },
            "association_states": dict(sorted(file["association_states"].items())),
            "effect_counts": dict(sorted(file["effect_counts"].items())),
        }
        serial["churn"] = serial["additions"] + serial["deletions"]
        serial["net_lines"] = serial["additions"] - serial["deletions"]
        serial["risk_score"] = round(
            math.log1p(serial["touches"] + serial["git_changes"])
            * math.log1p(serial["churn"] + 1),
            4,
        )
        serial["pattern"] = pattern_name(serial, window_start, window_end)
        serial["stable_x"] = int(compact_hash(path + ":x", 8), 16) / 0xFFFFFFFF
        serial["stable_y"] = int(compact_hash(path + ":y", 8), 16) / 0xFFFFFFFF
        output.append(serial)
    return sorted(output, key=lambda row: row["path"])


def build_cochange_edges(changes: Any) -> list[dict[str, Any]]:
    paths_by_commit: dict[str, set[str]] = defaultdict(set)
    for change in changes:
        paths_by_commit[change["commit_id"]].add(change["path"])
    edges = Counter()
    for paths in paths_by_commit.values():
        ordered = sorted(paths)
        if len(ordered) > 50:
            continue
        for source, target in combinations(ordered, 2):
            edges[(source, target)] += 1
    return [
        {
            "source": source,
            "target": target,
            "count": count,
            "semantics": "same-commit correlation; not causal coupling",
        }
        for (source, target), count in sorted(
            edges.items(), key=lambda item: (-item[1], item[0])
        )[:400]
    ]


def build_tree(files: list[dict[str, Any]]) -> dict[str, Any]:
    root: dict[str, Any] = {"name": "repository", "children": {}}
    for file in files:
        if (
            not file["survives_to_head"]
            or not file.get("current_path")
            or file["path"] != file["current_path"]
        ):
            continue
        node = root
        parts = file["current_path"].split("/")
        for part in parts[:-1]:
            node = node["children"].setdefault(
                part, {"name": part, "children": {}}
            )
        node["children"][parts[-1]] = {
            "name": parts[-1],
            "path": file["current_path"],
            "value": max(1, int(file["current_bytes"])),
            "touches": file["touches"],
            "risk_score": file["risk_score"],
            "pattern": file["pattern"],
            "children": {},
        }

    def materialize(node: dict[str, Any]) -> dict[str, Any]:
        children = [
            materialize(child)
            for _, child in sorted(node.pop("children").items())
        ]
        if children:
            node["children"] = children
            node["value"] = sum(child.get("value", 0) for child in children)
        return node

    return materialize(root)


def tree_leaf_paths(tree: dict[str, Any]) -> set[str]:
    paths = set()
    stack = [tree]
    while stack:
        node = stack.pop()
        if node.get("path"):
            paths.add(node["path"])
        stack.extend(node.get("children", []))
    return paths


def build_blame_rows(
    repo: Path, head: str, files: list[dict[str, Any]], limit: int = 12_000
) -> list[dict[str, Any]]:
    candidates = [
        file
        for file in files
        if file["survives_to_head"]
        and file.get("current_path")
        and file["path"] == file["current_path"]
        and file["extension"] in SOURCE_EXTENSIONS
        and 0 < file["current_bytes"] <= 250_000
    ]
    candidates.sort(
        key=lambda row: (-row["risk_score"], -row["touches"], row["path"])
    )
    rows = []
    for file in candidates:
        values = parse_blame(repo, head, file["current_path"])
        if rows and len(rows) + len(values) > limit:
            continue
        rows.extend(values)
        if len(rows) >= limit:
            break
    return sorted(rows, key=lambda row: (row["path"], row["line"]))


def build_survival_cohorts(lifetimes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    cohorts: dict[str, Counter] = defaultdict(Counter)
    for lifetime in lifetimes:
        cohort = date_label(int(lifetime["birth_ms"]))[:7]
        counter = cohorts[cohort]
        counter["born_files"] += 1
        if lifetime["survives_to_head"]:
            counter["surviving_files"] += 1
            counter["surviving_bytes"] += int(lifetime.get("current_bytes") or 0)
        else:
            counter["dead_files"] += 1
    return [
        {"cohort": cohort, **dict(counter)}
        for cohort, counter in sorted(cohorts.items())
    ]


def build_ownership(
    changes: Any, commits: dict[str, dict[str, Any]]
) -> list[dict[str, Any]]:
    ownership: dict[tuple[str, str], Counter] = defaultdict(Counter)
    for change in changes:
        author = commits.get(change["commit_id"], {}).get("author_label", "unknown")
        key = (author, group_for_path(change["path"]))
        ownership[key]["changes"] += 1
        ownership[key]["churn"] += int(change["additions"]) + int(change["deletions"])
    return [
        {"author": author, "group": group, **dict(values)}
        for (author, group), values in sorted(ownership.items())
    ]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--lean-nebula", action="store_true")
    args = parser.parse_args()
    output = build([json.load(sys.stdin)], args.repo, lean_nebula=args.lean_nebula)
    json.dump(output, sys.stdout, separators=(",", ":"), sort_keys=True)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
