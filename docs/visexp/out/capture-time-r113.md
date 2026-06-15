# R113 Capture-Time Record Envelope Smoke

Last updated: 2026-06-14
Stage at update: implement/verify
Source/command: `cargo test --manifest-path collector/Cargo.toml cmd_exec::tests::record_agent_envelope_start_and_end_persist_to_sqlite`
Completeness: implementation smoke passed; live smoke tracked by R113-live

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

This is implementation evidence for the row-writing path. R113-live supplies
the live eBPF rerun: five real read-only Codex tasks create 5/5 capture-time
sessions/tools and join 508/508 raw effects. C4 remains partial because broader
task coverage, full-history exact integration, and user-task evidence are still
missing.
