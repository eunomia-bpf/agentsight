#!/usr/bin/env python3
"""Build the status-preserving access ledger required by RQ3 and its RQ6 anchor."""

from __future__ import annotations

import argparse
import csv
import gzip
import json
from pathlib import Path, PurePosixPath
from typing import Any


def read_payload(path: Path) -> dict[str, Any]:
    with gzip.open(path, "rt", encoding="utf-8") as handle:
        return json.load(handle)


def module_for(path: str) -> str:
    parts = PurePosixPath(path).parts
    return parts[0] if len(parts) > 1 else "repo-root-files"


def derive(events_dir: Path) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    files = sorted(events_dir.glob("*.json.gz"))
    if len(files) != 6:
        raise ValueError(f"expected six gzip event exports, found {len(files)}")
    for path in files:
        payload = read_payload(path)
        project = str(payload["repository"])
        for event_index, event in enumerate(payload["events"]):
            if str(event.get("status", "observed")) not in {"ok", "observed"}:
                continue
            for fallback_ordinal, action in enumerate(event.get("actions") or []):
                worktree = str(action.get("worktree_id") or "")
                action_path = str(action.get("path") or "")
                if not worktree or not action_path:
                    continue
                artifact_id = str(action.get("artifact_id") or "")
                if not bool(action.get("scope", False)) and not artifact_id:
                    raise ValueError(
                        f"missing projected identity: {project}/{event['id']}/{action_path}"
                    )
                rows.append(
                    {
                        "project": project,
                        "worktree_id": worktree,
                        "event_index": event_index,
                        "event_id": str(event["id"]),
                        "ts_ms": int(event["ts_ms"]),
                        "session_id": str(event["session_id"]),
                        "action_ordinal": int(
                            action.get("action_ordinal", fallback_ordinal)
                        ),
                        "path": action_path,
                        "module": module_for(action_path),
                        "operation": str(action.get("access") or ""),
                        "scope": bool(action.get("scope", False)),
                        "artifact_id": artifact_id,
                        "previous_path": str(action.get("previous_path") or ""),
                    }
                )
    return rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--events-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    rows = derive(args.events_dir)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle, fieldnames=list(rows[0]), lineterminator="\n"
        )
        writer.writeheader()
        writer.writerows(rows)
    print(f"{args.output}: {len(rows)} rows")


if __name__ == "__main__":
    main()
