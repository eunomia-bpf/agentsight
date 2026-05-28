# Production Observability TODO

This tracks the remaining work after the SQLite/adapters/export and real
Claude/Gemini smoke path. Keep items small enough to finish and test in one PR.

## P0: Validation Blocked by Credentials

- [ ] OpenClaw real provider token/session smoke
  - Status: gated test exists but has not been run with real provider
    credentials in this environment.
  - Required: `OPENAI_API_KEY` or `OPENCLAW_LIVE_OPENAI_KEY`.
  - Command:
    ```bash
    cd collector
    OPENAI_API_KEY=sk-... \
    AGENTSIGHT_REAL_OPENCLAW_SMOKE=1 \
    cargo test real_openclaw_provider_smoke -- --ignored --nocapture
    ```
  - Done when: `agent_sessions` contains `agent_type = 'openclaw'` with
    `total_tokens > 0`.

## P1: Local Implementation

- [x] Gemini HTTP/2/SSE response usage decoding
  - Added bounded HTTP/2 frame + HPACK reconstruction for TLS plaintext and a
    Gemini SSE/fragment fallback for `usageMetadata`.
  - Verified with fixture tests and a real Gemini CLI smoke that produces
    generic `response_usage` rows.

- [x] Claude Code real tool-use smoke
  - Added an ignored real smoke test that forces one allowed Claude Code Bash
    tool call and asserts a `tool_calls` row.

- [x] `agentsight discover`
  - Scope: list known targets and local attach hints for Claude Code, Gemini
    CLI, OpenClaw containers, and generic Node/Python processes.
  - Done when: `agentsight discover --json` returns stable machine-readable
    candidates and `agentsight discover` prints a concise table.

- [x] `--no-adapters`
  - Scope: allow capture/replay/export paths to persist raw/canonical/generic
    projections without running SQL adapters.
  - Done when: `exec`, `record`, `trace`, and `replay` accept the flag and
    tests prove `adapter_runs` stays empty.

- [x] Adapter auto detection
  - Scope: add boolean detection for built-in SQL adapters and only run
    adapters with matching DB evidence when `--adapter auto`.
  - Done when: `adapters list --json` exposes detection support and auto mode
    skips adapters with no evidence.

- [x] `/api/v1/*` SQLite HTTP API
  - Scope: serve events, token summary, audit events, sessions, agents, and
    interruptions from SQLite instead of scanning JSONL.
  - Done when: API tests run against a fixture DB and do not read the raw log
    for common dashboard calls.

- [x] Dashboard/UI SQLite path
  - Scope: add DB-backed dashboard client and keep static JSON snapshot upload
    for demos.
  - Done when: local server can show a SQLite-backed capture and static demo
    upload can show `agentsight export` snapshots.

## Cleanup Before PR

- [x] Move SQLite CLI/query/export/adapters out of `main.rs`.
- [x] Move headless CLI output evidence capture out of `main.rs`.
- [x] Reduce formatting noise in files that were only changed by rustfmt.
- [ ] Split final work into reviewable commits:
  - SQLite schema/projections/export.
  - SQL adapters and fixtures.
  - Real CLI smoke/evidence capture.
  - Docs.
- [ ] Open PR after tests and ignored real smokes are documented.
