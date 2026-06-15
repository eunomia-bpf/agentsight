from agentsight_py.snapshot import summarize_snapshot


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

