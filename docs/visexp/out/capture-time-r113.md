# R113 Capture-Time Record Envelope Smoke

Last updated: 2026-06-14
Stage at update: implement/verify
Source/command: `cargo test --manifest-path collector/Cargo.toml cmd_exec::tests::record_agent_envelope_start_and_end_persist_to_sqlite`
Completeness: partial

R113 moves one part of the R112 boundary into the `record` hot path:
`agentsight record -- <command>` now writes a first-class SQLite `sessions` row
and matching `tool_calls` row as soon as the target child PID is known, before
the child is continued. When the target exits, the same row ids are updated with
end time, duration, exit status, and exit code.

## Result

| Scope | Sessions | Tool calls | View source | Status |
|-------|---------:|-----------:|-------------|--------|
| unit smoke over temp SQLite DB | 1 | 1 | `record_capture_time_agent_envelope` | passed |

The rows use `related_pid=<target child pid>`, `tool_name=agent-run`, and
`prompt_tag=record`. Existing export paths can read them through
`collector/src/sources/sqlite.rs` without observed-session projection.

## Boundary

This is implementation evidence, not a live lineage result. R113 does not rerun
fresh eBPF workloads, does not reduce the R112 orphan count of 136 effects, and
does not add direct per-effect `tool_call_id` or `related_event_id` links. C4
therefore remains partial until fresh live `record` tasks show high raw join
coverage and explain the remaining orphan classes.
