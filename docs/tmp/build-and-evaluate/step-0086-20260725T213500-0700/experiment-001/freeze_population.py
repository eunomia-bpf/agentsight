#!/usr/bin/env python3
"""Freeze the exact step-0084 AgentSight-research population read-only."""

from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[5]
OUTPUT_DIR = Path(__file__).resolve().parent
INVENTORY = (
    REPO
    / "docs/tmp/build-and-evaluate/"
    "step-0084-20260725T193000-0700/experiment-001/inventory-results.json"
)
PROJECT = "agentsight-research-semantic-flamegraph"
ROOTS = {
    "codex": Path.home() / ".codex/sessions",
    "claude": Path.home() / ".claude/projects",
}
COPY_ROOT = OUTPUT_DIR / "frozen-sessions"
MANIFEST = OUTPUT_DIR / "frozen-population.json"
CHUNK_SIZE = 1024 * 1024


def stable_key(agent: str, relative: str) -> str:
    value = f"{agent}:{relative}".encode("utf-8", errors="replace")
    return hashlib.sha256(value).hexdigest()[:16]


def selected_inventory_rows() -> list[dict[str, Any]]:
    payload = json.loads(INVENTORY.read_text(encoding="utf-8"))
    rows = [row for row in payload["sessions"] if row["project"] == PROJECT]
    keys = [row["session_key"] for row in rows]
    if len(keys) != len(set(keys)):
        raise RuntimeError("selected inventory contains duplicate session keys")
    return rows


def source_index() -> dict[str, tuple[str, str, Path]]:
    selected: dict[str, tuple[str, str, Path]] = {}
    for agent, root in ROOTS.items():
        for path in sorted(candidate for candidate in root.rglob("*.jsonl") if candidate.is_file()):
            relative = path.relative_to(root).as_posix()
            key = stable_key(agent, relative)
            if key in selected:
                raise RuntimeError(f"duplicate reconstructed session key: {key}")
            selected[key] = (agent, relative, path)
    return selected


def freeze_one(source: Path, destination: Path) -> tuple[int, str]:
    destination.parent.mkdir(parents=True, exist_ok=True)
    digest = hashlib.sha256()
    with source.open("rb") as input_stream:
        frozen_length = os.fstat(input_stream.fileno()).st_size
        remaining = frozen_length
        with destination.open("xb") as output_stream:
            while remaining:
                chunk = input_stream.read(min(CHUNK_SIZE, remaining))
                if not chunk:
                    raise RuntimeError(
                        f"source shortened while freezing after {frozen_length - remaining} bytes"
                    )
                output_stream.write(chunk)
                digest.update(chunk)
                remaining -= len(chunk)
    return frozen_length, digest.hexdigest()


def coarse_stats(row: dict[str, Any]) -> dict[str, Any]:
    return {
        key: row[key]
        for key in (
            "project",
            "start_time_utc",
            "end_time_utc",
            "duration_seconds",
            "duration_bucket",
            "user_prompts",
            "llm_calls",
            "tool_calls",
            "operations",
            "provider_reported_tokens",
            "long_horizon_candidate",
            "source_bytes",
            "source_lines",
            "timestamp_source",
            "decode_errors",
        )
    }


def main() -> None:
    if MANIFEST.exists() or COPY_ROOT.exists():
        raise RuntimeError("freeze outputs already exist; refusing to overwrite")

    rows = selected_inventory_rows()
    index = source_index()
    missing = [row["session_key"] for row in rows if row["session_key"] not in index]
    if missing:
        raise RuntimeError(f"could not reconstruct {len(missing)} selected session keys")

    COPY_ROOT.mkdir(parents=True, exist_ok=False)
    sessions: list[dict[str, Any]] = []
    for row in rows:
        key = row["session_key"]
        agent, relative, source = index[key]
        if agent != row["agent"]:
            raise RuntimeError(f"agent mismatch for {key}: {agent} != {row['agent']}")
        frozen_relative = Path("frozen-sessions") / agent / relative
        length, sha256 = freeze_one(source, OUTPUT_DIR / frozen_relative)
        sessions.append(
            {
                "session_key": key,
                "agent": agent,
                "source_relative_path": relative,
                "frozen_copy_relative_path": frozen_relative.as_posix(),
                "freeze_byte_length": length,
                "sha256": sha256,
                "inventory_coarse_stats": coarse_stats(row),
            }
        )

    known_tokens = [
        int(row["provider_reported_tokens"])
        for row in rows
        if row["provider_reported_tokens"] is not None
    ]
    payload = {
        "schema": "agentsight.frozen-local-session-population.v1",
        "frozen_at_utc": datetime.now(timezone.utc)
        .isoformat(timespec="seconds")
        .replace("+00:00", "Z"),
        "selection": {
            "inventory_relative_path": INVENTORY.relative_to(REPO).as_posix(),
            "coarse_project_label": PROJECT,
            "expected_sessions": 42,
            "actual_sessions": len(rows),
            "count_disposition": (
                "matched expected count"
                if len(rows) == 42
                else "used exactly the inventory rows matching the coarse project label"
            ),
        },
        "totals": {
            "sessions": len(rows),
            "user_prompts": sum(int(row["user_prompts"]) for row in rows),
            "llm_calls": sum(int(row["llm_calls"]) for row in rows),
            "tool_calls": sum(int(row["tool_calls"]) for row in rows),
            "operations": sum(int(row["operations"]) for row in rows),
            "known_token_mass": sum(known_tokens),
            "sessions_with_known_tokens": len(known_tokens),
            "frozen_bytes": sum(item["freeze_byte_length"] for item in sessions),
        },
        "sessions": sessions,
    }
    with MANIFEST.open("x", encoding="utf-8") as stream:
        json.dump(payload, stream, ensure_ascii=False, indent=2, sort_keys=True)
        stream.write("\n")
    print(json.dumps(payload["totals"], sort_keys=True))


if __name__ == "__main__":
    main()
