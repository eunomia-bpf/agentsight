import json

import pytest

from agentsight_py.snapshot import SnapshotError, load_snapshot, summarize_snapshot


def test_summarize_snapshot_counts_top_level_lists():
    summary = summarize_snapshot(
        {
            "schema_version": 1,
            "generated_at": "2026-01-01T00:00:00Z",
            "summary": {
                "llm_calls": 3,
                "input_tokens": 10,
                "output_tokens": 20,
                "total_tokens": 30,
            },
            "sessions": [{}, {}],
            "process_nodes": [{}],
            "tool_calls": [{}, {}, {}],
            "audit_events": [{}],
            "network_targets": [{}, {}],
            "resource_samples": [{}, {}, {}, {}],
        }
    )

    assert summary.schema_version == 1
    assert summary.sessions == 2
    assert summary.process_nodes == 1
    assert summary.tool_calls == 3
    assert summary.audit_events == 1
    assert summary.network_targets == 2
    assert summary.resource_samples == 4
    assert summary.llm_calls == 3
    assert summary.total_tokens == 30


def test_summarize_snapshot_preserves_empty_top_level_lists():
    summary = summarize_snapshot(
        {
            "summary": {
                "sessions": 7,
                "audit_events": 9,
            },
            "sessions": [],
            "audit_events": [],
        }
    )

    assert summary.sessions == 0
    assert summary.audit_events == 0


def test_load_snapshot_wraps_common_read_errors(tmp_path):
    directory = tmp_path / "snapshot-dir"
    directory.mkdir()

    with pytest.raises(SnapshotError, match="snapshot cannot be read"):
        load_snapshot(directory)

    invalid_utf8 = tmp_path / "invalid.json"
    invalid_utf8.write_bytes(b"\xff")

    with pytest.raises(SnapshotError, match="snapshot is not valid UTF-8"):
        load_snapshot(invalid_utf8)


def test_load_snapshot_reads_json_object(tmp_path):
    snapshot = tmp_path / "snapshot.json"
    snapshot.write_text(json.dumps({"schema_version": 1}), encoding="utf-8")

    assert load_snapshot(snapshot) == {"schema_version": 1}
