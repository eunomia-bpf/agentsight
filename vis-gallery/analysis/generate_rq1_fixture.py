#!/usr/bin/env python3
"""Generate the preregistered RQ1 controlled Git/session history."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path


UTC = timezone.utc


def run(repo: Path, *args: str, env: dict[str, str] | None = None) -> str:
    result = subprocess.run(
        [
            "git",
            "-c",
            "gc.auto=0",
            "-c",
            "maintenance.auto=false",
            "-c",
            "maintenance.autoDetach=false",
            "-c",
            "core.hooksPath=/dev/null",
            "-C",
            str(repo),
            *args,
        ],
        check=True,
        text=True,
        capture_output=True,
        env=env,
    )
    return result.stdout.strip()


def git_env(timestamp: datetime) -> dict[str, str]:
    env = os.environ.copy()
    value = timestamp.isoformat()
    env["GIT_AUTHOR_DATE"] = value
    env["GIT_COMMITTER_DATE"] = value
    return env


def commit(repo: Path, message: str, timestamp: datetime) -> str:
    run(repo, "add", "-A")
    run(repo, "commit", "-q", "-m", message, env=git_env(timestamp))
    return run(repo, "rev-parse", "HEAD")


def write(repo: Path, relative: str, text: str) -> None:
    path = repo / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def iso(timestamp: datetime) -> str:
    return timestamp.isoformat().replace("+00:00", "Z")


def millis(timestamp: datetime) -> int:
    return int(timestamp.timestamp() * 1000)


def add_event(
    events: dict[str, list[dict]],
    truth: list[dict],
    *,
    case_id: str,
    vendor: str,
    timestamp: datetime,
    edits: list[dict],
    split: str,
    scenario: str,
    targets: dict[str, list[str]] | None = None,
) -> None:
    events[vendor].append(
        {
            "case_id": case_id,
            "timestamp": timestamp,
            "edits": edits,
        }
    )
    targets = targets or {}
    for edit in edits:
        path = edit["path"]
        truth.append(
            {
                "case_id": case_id,
                "vendor": vendor,
                "ts_ms": millis(timestamp),
                "path": path,
                "target_commit_ids": targets.get(path, []),
                "label": "target" if targets.get(path) else "null",
                "split": split,
                "scenario": scenario,
                "adjudicable": True,
            }
        )


def initialize_repo(root: Path, repo_root: Path | None) -> Path:
    repo = repo_root or root / "repo"
    if repo.exists():
        shutil.rmtree(repo)
    repo.mkdir(parents=True)
    run(repo, "init", "-q", "-b", "main")
    run(repo, "config", "user.name", "RQ1 Fixture")
    run(repo, "config", "user.email", "rq1-fixture@example.test")
    return repo


def write_native_sessions(root: Path, repo: Path, events: dict[str, list[dict]]) -> list[Path]:
    sessions = root / "sessions"
    sessions.mkdir(parents=True)
    paths: list[Path] = []

    claude_path = sessions / ".claude" / "projects" / "fixture" / "claude.jsonl"
    claude_path.parent.mkdir(parents=True, exist_ok=True)
    with claude_path.open("w", encoding="utf-8") as output:
        for event in sorted(events["claude"], key=lambda item: item["timestamp"]):
            if event.get("pathless"):
                output.write(
                    json.dumps(
                        {
                            "type": "assistant",
                            "timestamp": iso(event["timestamp"]),
                            "cwd": str(repo),
                            "message": {
                                "model": "claude-fixture",
                                "content": [
                                    {
                                        "type": "tool_use",
                                        "id": event["case_id"],
                                        "name": "Bash",
                                        "input": {"command": "fixture pathless command"},
                                    }
                                ],
                                "usage": {"input_tokens": 1, "output_tokens": 1},
                            },
                        },
                        separators=(",", ":"),
                    )
                    + "\n"
                )
            for offset, edit in enumerate(event["edits"]):
                record = {
                    "type": "assistant",
                    "timestamp": iso(event["timestamp"] + timedelta(milliseconds=offset)),
                    "cwd": str(repo),
                    "message": {
                        "model": "claude-fixture",
                        "content": [
                            {
                                "type": "tool_use",
                                "id": f"{event['case_id']}-{offset}",
                                "name": "Edit",
                                "input": {
                                    "file_path": str(repo / edit["path"]),
                                    "old_string": edit["before"],
                                    "new_string": edit["after"],
                                },
                            }
                        ],
                        "usage": {"input_tokens": 1, "output_tokens": 1},
                    },
                }
                output.write(json.dumps(record, separators=(",", ":")) + "\n")
    paths.append(claude_path)

    codex_path = sessions / ".codex" / "sessions" / "codex.jsonl"
    codex_path.parent.mkdir(parents=True, exist_ok=True)
    with codex_path.open("w", encoding="utf-8") as output:
        first = min(event["timestamp"] for event in events["codex"])
        output.write(
            json.dumps(
                {
                    "type": "turn_context",
                    "timestamp": iso(first - timedelta(seconds=1)),
                    "payload": {"model": "codex-fixture", "cwd": str(repo)},
                },
                separators=(",", ":"),
            )
            + "\n"
        )
        for event in sorted(events["codex"], key=lambda item: item["timestamp"]):
            changes = {}
            for edit in event["edits"]:
                changes[str(repo / edit["path"])] = {
                    "type": "update",
                    "unified_diff": (
                        "@@ -1 +1 @@\n"
                        f"-{edit['before'].rstrip()}\n"
                        f"+{edit['after'].rstrip()}"
                    ),
                }
            output.write(
                json.dumps(
                    {
                        "type": "event_msg",
                        "timestamp": iso(event["timestamp"]),
                        "payload": {
                            "type": "patch_apply_end",
                            "call_id": event["case_id"],
                            "turn_id": event["case_id"],
                            "success": True,
                            "status": "completed",
                            "changes": changes,
                            "stdout": "",
                            "stderr": "",
                        },
                    },
                    separators=(",", ":"),
                )
                + "\n"
            )
    paths.append(codex_path)

    gemini_path = sessions / ".gemini" / "tmp" / "fixture" / "chats" / "session-fixture.json"
    gemini_path.parent.mkdir(parents=True, exist_ok=True)
    gemini_events = sorted(events["gemini"], key=lambda item: item["timestamp"])
    messages = []
    for event in gemini_events:
        tool_calls = []
        if event.get("pathless"):
            tool_calls.append(
                {
                    "id": event["case_id"],
                    "name": "run_shell_command",
                    "status": "success",
                    "args": {"command": "fixture pathless command"},
                }
            )
        for offset, edit in enumerate(event["edits"]):
            tool_calls.append(
                {
                    "id": f"{event['case_id']}-{offset}",
                    "name": "replace",
                    "status": "success",
                    "args": {
                        "file_path": edit["path"],
                        "old_string": edit["before"],
                        "new_string": edit["after"],
                    },
                }
            )
        messages.append(
            {
                "id": event["case_id"],
                "type": "gemini",
                "timestamp": iso(event["timestamp"]),
                "model": "gemini-fixture",
                "content": "fixture response",
                "tokens": {"input": 1, "output": 1, "total": 2},
                "toolCalls": tool_calls,
            }
        )
    gemini_path.write_text(
        json.dumps(
            {
                "sessionId": "gemini-rq1-fixture",
                "projectHash": hashlib.sha256(str(repo).encode()).hexdigest(),
                "startTime": iso(gemini_events[0]["timestamp"] - timedelta(seconds=1)),
                "lastUpdated": iso(gemini_events[-1]["timestamp"] + timedelta(seconds=1)),
                "messages": messages,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    paths.append(gemini_path)
    return paths


def generate(root: Path, repo_root: Path | None) -> None:
    if root.exists():
        shutil.rmtree(root)
    root.mkdir(parents=True)
    repo = initialize_repo(root, repo_root)
    events: dict[str, list[dict]] = defaultdict(list)
    truth: list[dict] = []
    vendors = ["claude", "codex", "gemini"]
    start = datetime(2026, 6, 1, 12, 0, tzinfo=UTC)

    cases: list[tuple[str, int, int]] = [
        ("calibration", 30, 30),
        ("heldout", 50, 50),
    ]
    event_index = 0
    main_rows: list[dict] = []
    for split, positives, nulls in cases:
        for index in range(positives):
            case_id = f"{split}-positive-{index:03d}"
            path = f"main/{case_id}.txt"
            before = f"old {case_id}\n"
            after = f"agent {case_id}\n"
            write(repo, path, before)
            main_rows.append(
                {
                    "kind": "positive",
                    "split": split,
                    "index": index,
                    "case_id": case_id,
                    "path": path,
                    "before": before,
                    "after": after,
                    "vendor": vendors[event_index % len(vendors)],
                    "timestamp": start + timedelta(minutes=20 * event_index),
                }
            )
            event_index += 1
        for index in range(nulls):
            case_id = f"{split}-null-{index:03d}"
            path = f"main/{case_id}.txt"
            before = f"old {case_id}\n"
            after = f"agent discarded {case_id}\n"
            write(repo, path, before)
            main_rows.append(
                {
                    "kind": "near_null" if index % 2 == 0 else "empty_null",
                    "split": split,
                    "index": index,
                    "case_id": case_id,
                    "path": path,
                    "before": before,
                    "after": after,
                    "vendor": vendors[event_index % len(vendors)],
                    "timestamp": start + timedelta(minutes=20 * event_index),
                }
            )
            event_index += 1

    for path in [
        "diagnostic/rename-old.txt",
        "diagnostic/recreate.txt",
        "diagnostic/ambiguous.txt",
        "diagnostic/squash.txt",
        "diagnostic/clock.txt",
        "diagnostic/merge.txt",
        "diagnostic/concurrent.txt",
    ]:
        write(repo, path, f"old {path}\n")
    for vendor in vendors:
        base = f"schema/{vendor}"
        write(
            repo,
            f"{base}/rename-old.txt",
            "stable 1\nstable 2\nstable 3\nstable 4\nold rename line\n",
        )
        for name in ["recreate", "ambiguous", "squash", "clock", "moved", "merge"]:
            write(repo, f"{base}/{name}.txt", f"old {vendor} {name}\n")
        write(repo, f"{base}/split-a.txt", f"old {vendor} split a\n")
        write(repo, f"{base}/split-b.txt", f"old {vendor} split b\n")
    initial_time = start - timedelta(days=1)
    commit(repo, "fixture initial state", initial_time)

    for row in main_rows:
        add_event(
            events,
            truth,
            case_id=row["case_id"],
            vendor=row["vendor"],
            timestamp=row["timestamp"],
            edits=[{"path": row["path"], "before": row["before"], "after": row["after"]}],
            split=row["split"],
            scenario=row["kind"],
        )
        if row["kind"] == "positive":
            write(repo, row["path"], row["after"])
            target = commit(repo, row["case_id"], row["timestamp"] + timedelta(minutes=5))
            truth[-1]["target_commit_ids"] = [target]
            truth[-1]["label"] = "target"
        elif row["kind"] == "near_null":
            write(repo, row["path"], f"unrelated human {row['case_id']}\n")
            commit(
                repo,
                f"unrelated-{row['case_id']}",
                row["timestamp"] + timedelta(minutes=5),
            )

    diagnostic_start = start + timedelta(days=4)

    # Rename plus edit.
    ts = diagnostic_start
    run(repo, "mv", "diagnostic/rename-old.txt", "diagnostic/rename-new.txt")
    before = "old diagnostic/rename-old.txt\n"
    after = "agent rename\n"
    write(repo, "diagnostic/rename-new.txt", after)
    target = commit(repo, "diagnostic rename", ts + timedelta(minutes=5))
    add_event(
        events,
        truth,
        case_id="diagnostic-rename",
        vendor="claude",
        timestamp=ts,
        edits=[{"path": "diagnostic/rename-new.txt", "before": before, "after": after}],
        split="diagnostic",
        scenario="rename",
        targets={"diagnostic/rename-new.txt": [target]},
    )

    # Pre-birth add.
    ts += timedelta(minutes=30)
    path = "diagnostic/prebirth.txt"
    after = "agent prebirth\n"
    write(repo, path, after)
    target = commit(repo, "diagnostic prebirth", ts + timedelta(minutes=5))
    add_event(
        events,
        truth,
        case_id="diagnostic-prebirth",
        vendor="gemini",
        timestamp=ts,
        edits=[{"path": path, "before": "", "after": after}],
        split="diagnostic",
        scenario="prebirth",
        targets={path: [target]},
    )

    # Deletion and same-path recreation.
    ts += timedelta(minutes=30)
    path = "diagnostic/recreate.txt"
    (repo / path).unlink()
    commit(repo, "diagnostic delete", ts - timedelta(minutes=10))
    after = "agent recreated\n"
    write(repo, path, after)
    target = commit(repo, "diagnostic recreate", ts + timedelta(minutes=5))
    add_event(
        events,
        truth,
        case_id="diagnostic-recreate",
        vendor="codex",
        timestamp=ts,
        edits=[{"path": path, "before": "", "after": after}],
        split="diagnostic",
        scenario="delete_recreate",
        targets={path: [target]},
    )

    # Two candidates, with the second as truth.
    ts += timedelta(minutes=30)
    path = "diagnostic/ambiguous.txt"
    before = (repo / path).read_text(encoding="utf-8")
    write(repo, path, "unrelated intermediate\n")
    commit(repo, "diagnostic ambiguous distractor", ts + timedelta(minutes=2))
    after = "agent ambiguous target\n"
    write(repo, path, after)
    target = commit(repo, "diagnostic ambiguous target", ts + timedelta(minutes=5))
    add_event(
        events,
        truth,
        case_id="diagnostic-ambiguous",
        vendor="claude",
        timestamp=ts,
        edits=[{"path": path, "before": before, "after": after}],
        split="diagnostic",
        scenario="ambiguous",
        targets={path: [target]},
    )

    # Two recorded edits squashed into one commit.
    ts += timedelta(minutes=30)
    path = "diagnostic/squash.txt"
    before = (repo / path).read_text(encoding="utf-8")
    middle = "agent squash middle\n"
    after = "agent squash final\n"
    write(repo, path, after)
    target = commit(repo, "diagnostic squash", ts + timedelta(minutes=8))
    add_event(
        events,
        truth,
        case_id="diagnostic-squash-a",
        vendor="codex",
        timestamp=ts,
        edits=[{"path": path, "before": before, "after": middle}],
        split="diagnostic",
        scenario="squash",
        targets={path: [target]},
    )
    add_event(
        events,
        truth,
        case_id="diagnostic-squash-b",
        vendor="gemini",
        timestamp=ts + timedelta(minutes=3),
        edits=[{"path": path, "before": middle, "after": after}],
        split="diagnostic",
        scenario="squash",
        targets={path: [target]},
    )

    # Commit timestamp before the event within the allowed skew.
    ts += timedelta(minutes=30)
    path = "diagnostic/clock.txt"
    before = (repo / path).read_text(encoding="utf-8")
    after = "agent clock skew\n"
    write(repo, path, after)
    target = commit(repo, "diagnostic clock skew", ts - timedelta(minutes=10))
    add_event(
        events,
        truth,
        case_id="diagnostic-clock",
        vendor="claude",
        timestamp=ts,
        edits=[{"path": path, "before": before, "after": after}],
        split="diagnostic",
        scenario="clock_skew",
        targets={path: [target]},
    )

    # Concurrent native events may map to one durable change.
    ts += timedelta(minutes=30)
    path = "diagnostic/concurrent.txt"
    before = (repo / path).read_text(encoding="utf-8")
    after = "agent concurrent\n"
    write(repo, path, after)
    target = commit(repo, "diagnostic concurrent", ts + timedelta(minutes=5))
    for vendor in ["claude", "gemini"]:
        add_event(
            events,
            truth,
            case_id=f"diagnostic-concurrent-{vendor}",
            vendor=vendor,
            timestamp=ts,
            edits=[{"path": path, "before": before, "after": after}],
            split="diagnostic",
            scenario="concurrent",
            targets={path: [target]},
        )

    # Merge diff is retained in a separate stratum and not a primary candidate.
    ts += timedelta(minutes=30)
    path = "diagnostic/merge.txt"
    before = (repo / path).read_text(encoding="utf-8")
    after = "agent merge\n"
    run(repo, "checkout", "-q", "-b", "fixture-feature")
    write(repo, path, after)
    commit(repo, "diagnostic feature commit", ts + timedelta(minutes=3))
    run(repo, "checkout", "-q", "main")
    run(
        repo,
        "merge",
        "--no-ff",
        "-m",
        "diagnostic merge",
        "fixture-feature",
        env=git_env(ts + timedelta(minutes=5)),
    )
    target = run(repo, "rev-parse", "HEAD")
    add_event(
        events,
        truth,
        case_id="diagnostic-merge",
        vendor="codex",
        timestamp=ts,
        edits=[{"path": path, "before": before, "after": after}],
        split="diagnostic",
        scenario="merge_stratum",
        targets={path: [target]},
    )

    # A durable Git change with no native event.
    ts += timedelta(minutes=30)
    write(repo, "diagnostic/git-unmatched.txt", "git only\n")
    commit(repo, "diagnostic git unmatched", ts)

    # Cross-schema edge coverage. These cases are diagnostic, not primary-gate
    # support, and retain the same frozen rules for every native parser.
    for vendor in vendors:
        base = f"schema/{vendor}"

        # Rename with enough stable context for -M50% detection.
        ts += timedelta(minutes=30)
        old_path = f"{base}/rename-old.txt"
        new_path = f"{base}/rename-new.txt"
        run(repo, "mv", old_path, new_path)
        before = "old rename line\n"
        after = f"agent {vendor} rename line\n"
        write(
            repo,
            new_path,
            f"stable 1\nstable 2\nstable 3\nstable 4\n{after}",
        )
        target = commit(repo, f"schema {vendor} rename", ts + timedelta(minutes=5))
        add_event(
            events,
            truth,
            case_id=f"schema-{vendor}-rename",
            vendor=vendor,
            timestamp=ts,
            edits=[{"path": new_path, "before": before, "after": after}],
            split="diagnostic",
            scenario="rename_by_schema",
            targets={new_path: [target]},
        )

        # Delete/recreate lifetime gap.
        ts += timedelta(minutes=30)
        path = f"{base}/recreate.txt"
        (repo / path).unlink()
        commit(repo, f"schema {vendor} delete", ts - timedelta(minutes=10))
        after = f"agent {vendor} recreated\n"
        write(repo, path, after)
        target = commit(repo, f"schema {vendor} recreate", ts + timedelta(minutes=5))
        add_event(
            events,
            truth,
            case_id=f"schema-{vendor}-recreate",
            vendor=vendor,
            timestamp=ts,
            edits=[{"path": path, "before": "", "after": after}],
            split="diagnostic",
            scenario="delete_recreate_by_schema",
            targets={path: [target]},
        )

        # Ambiguous timing with exact durable content in the second change.
        ts += timedelta(minutes=30)
        path = f"{base}/ambiguous.txt"
        intermediate = f"human {vendor} intermediate\n"
        write(repo, path, intermediate)
        commit(repo, f"schema {vendor} distractor", ts - timedelta(minutes=2))
        after = f"agent {vendor} ambiguous target\n"
        write(repo, path, after)
        target = commit(repo, f"schema {vendor} ambiguous target", ts + timedelta(minutes=5))
        add_event(
            events,
            truth,
            case_id=f"schema-{vendor}-ambiguous",
            vendor=vendor,
            timestamp=ts,
            edits=[{"path": path, "before": intermediate, "after": after}],
            split="diagnostic",
            scenario="ambiguous_by_schema",
            targets={path: [target]},
        )

        # Two native edits squashed into one durable change.
        ts += timedelta(minutes=30)
        path = f"{base}/squash.txt"
        before = (repo / path).read_text(encoding="utf-8")
        middle = f"agent {vendor} squash middle\n"
        after = f"agent {vendor} squash final\n"
        write(repo, path, after)
        target = commit(repo, f"schema {vendor} squash", ts + timedelta(minutes=8))
        for suffix, offset, old, new in [
            ("a", 0, before, middle),
            ("b", 3, middle, after),
        ]:
            add_event(
                events,
                truth,
                case_id=f"schema-{vendor}-squash-{suffix}",
                vendor=vendor,
                timestamp=ts + timedelta(minutes=offset),
                edits=[{"path": path, "before": old, "after": new}],
                split="diagnostic",
                scenario="squash_by_schema",
                targets={path: [target]},
            )

        # One recorded operation split over two durable commits.
        ts += timedelta(minutes=30)
        path_a = f"{base}/split-a.txt"
        path_b = f"{base}/split-b.txt"
        before_a = (repo / path_a).read_text(encoding="utf-8")
        before_b = (repo / path_b).read_text(encoding="utf-8")
        after_a = f"agent {vendor} split a\n"
        after_b = f"agent {vendor} split b\n"
        write(repo, path_a, after_a)
        target_a = commit(repo, f"schema {vendor} split a", ts + timedelta(minutes=4))
        write(repo, path_b, after_b)
        target_b = commit(repo, f"schema {vendor} split b", ts + timedelta(minutes=8))
        add_event(
            events,
            truth,
            case_id=f"schema-{vendor}-split",
            vendor=vendor,
            timestamp=ts,
            edits=[
                {"path": path_a, "before": before_a, "after": after_a},
                {"path": path_b, "before": before_b, "after": after_b},
            ],
            split="diagnostic",
            scenario="split_by_schema",
            targets={path_a: [target_a], path_b: [target_b]},
        )

        # Exact event-to-commit link whose line is later moved and rewritten.
        ts += timedelta(minutes=30)
        path = f"{base}/moved.txt"
        before = (repo / path).read_text(encoding="utf-8")
        after = f"agent {vendor} move source\n"
        write(repo, path, after)
        target = commit(repo, f"schema {vendor} move source", ts + timedelta(minutes=5))
        moved_path = f"{base}/moved-final.txt"
        run(repo, "mv", path, moved_path)
        write(repo, moved_path, f"rewritten after move {vendor}\n")
        commit(repo, f"schema {vendor} moved rewrite", ts + timedelta(minutes=20))
        add_event(
            events,
            truth,
            case_id=f"schema-{vendor}-moved-rewritten",
            vendor=vendor,
            timestamp=ts,
            edits=[{"path": path, "before": before, "after": after}],
            split="diagnostic",
            scenario="moved_rewritten_line_by_schema",
            targets={path: [target]},
        )

        # Clock skew within the frozen 15-minute allowance.
        ts += timedelta(minutes=30)
        path = f"{base}/clock.txt"
        before = (repo / path).read_text(encoding="utf-8")
        after = f"agent {vendor} clock skew\n"
        write(repo, path, after)
        target = commit(repo, f"schema {vendor} clock", ts - timedelta(minutes=10))
        add_event(
            events,
            truth,
            case_id=f"schema-{vendor}-clock",
            vendor=vendor,
            timestamp=ts,
            edits=[{"path": path, "before": before, "after": after}],
            split="diagnostic",
            scenario="clock_skew_by_schema",
            targets={path: [target]},
        )

        # Merge diff retained as a separate, non-primary stratum.
        ts += timedelta(minutes=30)
        path = f"{base}/merge.txt"
        before = (repo / path).read_text(encoding="utf-8")
        after = f"agent {vendor} merge\n"
        branch = f"fixture-{vendor}-merge"
        run(repo, "checkout", "-q", "-b", branch)
        write(repo, path, after)
        commit(repo, f"schema {vendor} feature", ts + timedelta(minutes=3))
        run(repo, "checkout", "-q", "main")
        run(
            repo,
            "merge",
            "--no-ff",
            "-m",
            f"schema {vendor} merge",
            branch,
            env=git_env(ts + timedelta(minutes=5)),
        )
        merge_target = run(repo, "rev-parse", "HEAD")
        add_event(
            events,
            truth,
            case_id=f"schema-{vendor}-merge",
            vendor=vendor,
            timestamp=ts,
            edits=[{"path": path, "before": before, "after": after}],
            split="diagnostic",
            scenario="merge_by_schema",
            targets={path: [merge_target]},
        )

        # A real native tool record with no repository path evidence.
        ts += timedelta(minutes=30)
        events[vendor].append(
            {
                "case_id": f"schema-{vendor}-pathless",
                "timestamp": ts,
                "edits": [],
                "pathless": True,
            }
        )

    session_paths = write_native_sessions(root, repo, events)
    calibration = [row for row in truth if row["split"] == "calibration"]
    heldout = [row for row in truth if row["split"] in {"heldout", "diagnostic"}]
    (root / "calibration.json").write_text(
        json.dumps({"schema": "agentsight.rq1.truth.v1", "pairs": calibration}, indent=2)
        + "\n",
        encoding="utf-8",
    )
    (root / "truth.json").write_text(
        json.dumps({"schema": "agentsight.rq1.truth.v1", "pairs": heldout}, indent=2)
        + "\n",
        encoding="utf-8",
    )
    (root / "manifest.json").write_text(
        json.dumps(
            {
                "repo": str(repo),
                "head": run(repo, "rev-parse", "HEAD"),
                "sessions": [str(path) for path in session_paths],
                "since": iso(start - timedelta(hours=1)),
                "until": iso(ts + timedelta(days=1)),
                "calibration_pairs": len(calibration),
                "heldout_pairs": len(heldout),
                "expected_pathless_events": len(vendors),
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument(
        "--repo-root",
        type=Path,
        help="place the temporary Git repository outside a workspace that auto-maintains nested repos",
    )
    args = parser.parse_args()
    generate(
        args.output_root.resolve(),
        args.repo_root.resolve() if args.repo_root else None,
    )


if __name__ == "__main__":
    main()
