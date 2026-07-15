from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path
from typing import Any


class SnapshotError(ValueError):
    """Raised when an AgentSight snapshot cannot be read or summarized."""


@dataclass(frozen=True)
class SnapshotSummary:
    schema_version: int | None
    generated_at: str | None
    sessions: int
    process_nodes: int
    tool_calls: int
    audit_events: int
    network_targets: int
    resource_samples: int
    llm_calls: int
    input_tokens: int
    output_tokens: int
    total_tokens: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def load_snapshot(path: str | Path) -> dict[str, Any]:
    snapshot_path = Path(path)
    try:
        with snapshot_path.open("r", encoding="utf-8") as file:
            data = json.load(file)
    except FileNotFoundError as exc:
        raise SnapshotError(f"snapshot not found: {snapshot_path}") from exc
    except OSError as exc:
        raise SnapshotError(f"snapshot cannot be read: {snapshot_path}: {exc.strerror or exc}") from exc
    except UnicodeDecodeError as exc:
        raise SnapshotError(f"snapshot is not valid UTF-8: {snapshot_path}") from exc
    except json.JSONDecodeError as exc:
        raise SnapshotError(f"snapshot is not valid JSON: {snapshot_path}") from exc

    if not isinstance(data, dict):
        raise SnapshotError("snapshot root must be a JSON object")
    return data


def _count(data: dict[str, Any], key: str) -> int | None:
    value = data.get(key)
    return len(value) if isinstance(value, list) else None


def _int_from_summary(summary: dict[str, Any], key: str) -> int:
    value = summary.get(key)
    return value if isinstance(value, int) else 0


def _count_or_summary(data: dict[str, Any], summary: dict[str, Any], key: str) -> int:
    count = _count(data, key)
    return count if count is not None else _int_from_summary(summary, key)


def summarize_snapshot(data: dict[str, Any]) -> SnapshotSummary:
    summary = data.get("summary")
    if not isinstance(summary, dict):
        summary = {}

    schema_version = data.get("schema_version")
    if not isinstance(schema_version, int):
        schema_version = None

    generated_at = data.get("generated_at")
    if not isinstance(generated_at, str):
        generated_at = None

    return SnapshotSummary(
        schema_version=schema_version,
        generated_at=generated_at,
        sessions=_count_or_summary(data, summary, "sessions"),
        process_nodes=_count(data, "process_nodes") or 0,
        tool_calls=_count(data, "tool_calls") or 0,
        audit_events=_count_or_summary(data, summary, "audit_events"),
        network_targets=_count(data, "network_targets") or 0,
        resource_samples=_count(data, "resource_samples") or 0,
        llm_calls=_int_from_summary(summary, "llm_calls"),
        input_tokens=_int_from_summary(summary, "input_tokens"),
        output_tokens=_int_from_summary(summary, "output_tokens"),
        total_tokens=_int_from_summary(summary, "total_tokens"),
    )
