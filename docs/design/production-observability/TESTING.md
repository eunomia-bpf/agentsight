# Production Observability Testing Plan

This document defines how to test the unified event model, SQLite storage,
generic projections, adapters, and the migration from JSONL-first behavior.

The testing goal is not only correctness. The system must also be replayable,
privacy-safe, and stable under long-running production captures.

## Test Layers

### 1. Unit Tests

Scope:

- Canonical event conversion.
- Event kind classification.
- Provider detection from host and path.
- Token extraction from common usage shapes.
- Redaction of headers and sensitive JSON fields.
- Adapter detection and adapter state machines.
- Retention policy decisions.

Recommended files:

```text
collector/src/semantic/event.rs
collector/src/semantic/kind.rs
collector/src/storage/sqlite.rs
collector/src/storage/retention.rs
collector/src/adapters/provider/*.rs
collector/src/adapters/agent/*.rs
```

Example assertions:

- An Anthropic `/v1/messages` response with `usage.input_tokens` and
  `usage.output_tokens` produces one `token_usage` row.
- An OpenAI chat response with `prompt_tokens` and `completion_tokens` maps to
  the same normalized fields.
- A 401 response becomes `llm.error` and an `audit_events` row with status
  `failure`.
- A raw process `EXEC` event becomes `process.exec`.

Command:

```bash
cd collector
cargo test
```

### 2. SQLite Integration Tests

Use a temp directory and a real SQLite database.

Scope:

- Schema creation and migration.
- Batched inserts.
- WAL mode setup.
- Index-backed time range queries.
- Pagination cursor correctness.
- Retention cleanup by size and by time.
- Replay idempotency.

Planned commands:

```bash
cd collector
cargo test storage_sqlite
cargo test storage_retention
```

Minimum checks:

- Insert 10,000 mixed events and query the newest 100 by time.
- Query by `pid`, `comm`, `kind`, `model`, and `session_id`.
- Re-run a migration on an already migrated DB and verify no data loss.
- Apply retention and verify raw/canonical/semantic rows stay referentially
  consistent.

### 3. Fixture Replay Tests

Replay tests are the most important adapter tests. They allow adapter behavior
to be deterministic without running the original agent.

Recommended fixture layout:

```text
docs/fixtures/
  generic/
    anthropic_messages.jsonl
    openai_responses.jsonl
    gemini_generate_content.jsonl
    process_file_stdio.jsonl
  adapters/
    claude-code/
      basic_session.jsonl
      tool_use_file_edit.jsonl
      llm_401_error.jsonl
      interrupted_stream.jsonl
      expected_sessions.json
      expected_token_usage.json
      expected_interruptions.json
    openclaw/
      gateway_session.jsonl
      expected_sessions.json
    gemini-cli/
      generate_content.jsonl
      expected_sessions.json
```

Fixture replay command:

```bash
cd collector
cargo run -- replay \
  --input ../docs/fixtures/sql-adapters/claude-code-tools/input.jsonl \
  --db /tmp/agentsight-fixture.db \
  --adapter claude-code
```

Expected-output tests should compare semantic tables, not raw row ordering.

Gemini CLI fixture replay command:

```bash
cd collector
cargo run -- replay \
  --input ../docs/fixtures/sql-adapters/gemini-cli-basic/input.jsonl \
  --db /tmp/agentsight-gemini-fixture.db \
  --adapter auto
cargo run -- export \
  --db /tmp/agentsight-gemini-fixture.db \
  --output /tmp/agentsight-gemini-fixture.agentsight.json
```

Recommended checks:

- `llm_calls` count.
- `token_usage` sums.
- `agent_sessions` IDs and status.
- `conversations` count.
- `tool_calls` names and statuses.
- `interruptions` category and severity.
- Confidence values above required thresholds.
- Export snapshot contains API-shaped `summary`, `token_summary`, `events`,
  `audit_events`, `sessions`, `agents`, and `interruptions`.

### 4. Adapter Contract Tests

Every adapter must pass the same contract.

Contract requirements:

- `id()` is stable and globally unique.
- `version()` is not empty.
- `detect()` is deterministic for the same input.
- `process()` never panics on unknown or malformed JSON.
- Output rows always include `adapter_id` and confidence. Adapter execution
  version is checked through `adapter_runs.adapter_version`; per-row
  `adapter_version` columns are planned.
- Running the same fixture twice with the same DB either produces identical
  rows or explicitly updates a previous adapter run.
- Adapter output remains valid if provider adapters have already produced
  generic rows.

Planned command:

```bash
cd collector
cargo test adapter_contract
```

### 5. SQL Adapter Tests

SQL adapters should be the default adapter implementation for projections that
can be expressed as deterministic queries: provider token extraction, LLM call
classification, audit rows, simple session grouping, and stable tool-call
extraction.

The test harness should treat SQL adapters as data transformations:

```text
fixture input DB
  + adapter manifest
  + adapter SQL files
  -> output DB
  -> expected semantic rows
```

Recommended SQL adapter layout:

```text
collector/adapters/sql/
  anthropic/
    adapter.toml
    detect.sql
    project_llm_calls.sql
    project_token_usage.sql
  claude-code/
    adapter.toml
    detect.sql
    project_tool_calls.sql
    project_sessions.sql
```

Recommended fixture layout:

```text
docs/fixtures/sql-adapters/
  anthropic-basic/
    input.jsonl
    expected/
      llm_calls.json
      token_usage.json
      audit_events.json
  claude-code-tools/
    input.jsonl
    expected/
      agent_sessions.json
      conversations.json
      tool_calls.json
```

Planned commands:

```bash
cd collector
cargo test sql_adapter_manifest
cargo test sql_adapter_safety
cargo test sql_adapter_fixtures
```

Future CLI command:

```bash
agentsight adapter test \
  --adapter collector/adapters/sql/anthropic \
  --fixture docs/fixtures/sql-adapters/anthropic-basic
```

#### Manifest Validation

Validate `adapter.toml` before running any SQL.

Checks:

- `id`, `version`, `type`, and `schema_version` are present.
- Referenced SQL files exist.
- Adapter type is one of `provider`, `agent`, or `target`.
- IDs use stable lowercase names such as `anthropic`, `claude-code`.
- SQL files are run in a deterministic order.

#### SQL Safety Validation

SQL adapters should not have unrestricted database power.

The current built-in SQL runner is intentionally stricter than the full target
contract: it allows only `INSERT OR IGNORE` / `INSERT OR REPLACE` into approved
semantic tables and records adapter execution state in `adapter_runs`.

Allowed:

- `INSERT INTO` approved semantic tables
- `INSERT OR IGNORE`
- `INSERT OR REPLACE` only when the primary key is deterministic
- `SELECT` / `WITH` clauses inside those insert statements

Planned for external adapters:

- `UPDATE` only for approved adapter-owned correlation columns or adapter run
  metadata, through a tighter validator or structured adapter API

Forbidden by default:

- `DROP`
- `ALTER`
- `DELETE`
- `VACUUM`
- `ATTACH`
- `DETACH`
- `PRAGMA writable_schema`
- writes to `raw_events`
- writes that omit `adapter_id` or confidence where required

The safety test should prepare SQL against an in-memory SQLite database and
also scan for forbidden statements before execution. This is not a complete SQL
sandbox, but it catches accidental destructive adapters and keeps the extension
surface narrow.

#### Golden Output Tests

Golden tests should compare semantic tables, not raw SQL text.

Flow:

1. Create a temporary SQLite database.
2. Load fixture `input.jsonl` through the same raw/canonical normalization path
   used by live capture.
3. Run generic projections.
4. Run the SQL adapter.
5. Dump selected semantic tables in stable order.
6. Compare against `expected/*.json`.

Stable ordering:

```sql
ORDER BY timestamp_ms, id
```

Fields that should be ignored or normalized:

- `adapter_runs.id` if generated randomly.
- `ingest_timestamp_ms` unless fixture controls it.
- floating confidence should compare with a small tolerance.

#### Idempotency Tests

Every SQL adapter must be safe to run more than once.

Required assertion:

```text
run adapter once -> dump semantic tables
run adapter again -> dump semantic tables
outputs are identical
```

This forces deterministic primary keys such as:

```text
anthropic-token-{llm_call_id}
claude-tool-{canonical_event_id}-{tool_call_id}
```

It also prevents duplicate token and audit rows during replay/backfill.

#### Incremental vs Full Replay Tests

Adapters must behave the same whether events are processed in one replay or in
small batches.

Flow:

1. Load the whole fixture and run the adapter once.
2. Load the same fixture in timestamp-ordered chunks, running the adapter after
   each chunk.
3. Compare final semantic tables.

This catches SQL that accidentally depends on "all future rows already exist".
For complex state, the adapter should either store explicit intermediate state
or be marked as full-replay-only.

#### Cross-adapter Order Tests

Provider adapters run before agent adapters. Tests should verify that agent SQL
can consume generic/provider rows without changing their meaning.

Example:

```text
generic projections
  -> anthropic SQL adapter
  -> claude-code SQL adapter
```

Checks:

- `token_usage` totals remain the same.
- `agent_sessions.total_tokens` equals the sum of linked `token_usage` rows.
- Agent adapter adds session/conversation IDs without duplicating LLM calls.

#### Malformed Input Tests

SQL adapters must tolerate bad or partial data.

Fixture cases:

- invalid JSON body string
- missing `usage`
- missing `model`
- unknown provider host
- response without request
- request without response
- HTTP error body that is plain text

Expected behavior:

- Adapter succeeds.
- Missing fields become `NULL` or zero where appropriate.
- Low-confidence rows are marked low confidence.
- No destructive changes occur.

#### SQL Adapter Performance Tests

Run adapters on larger fixture databases.

Targets:

- 100k canonical events.
- 10k LLM calls.
- Re-running an adapter should not degrade linearly because of duplicate scans
  when avoidable.

Recommended checks:

- `EXPLAIN QUERY PLAN` for key adapter SQL files uses indexed columns.
- Token projection over 10k LLM calls completes under a practical threshold on
  a developer laptop.
- Adapter memory usage remains bounded because work stays inside SQLite.

### 6. SQL Adapter vs Rust Adapter Boundary Tests

Some logic should remain in Rust. Boundary tests make sure the split is clear.

Use SQL adapters for:

- extracting fields from already reconstructed JSON bodies
- deterministic joins and aggregations
- token totals
- simple audit rows
- simple session grouping

Use Rust adapters for:

- stream timeout state machines
- SSE or chunk reconstruction
- process/container/binary discovery
- fuzzy version-specific parsing
- actions such as restart, alert delivery, or external API calls

Tests should include at least one case that SQL explicitly marks as unresolved,
for example `request_without_response`. A Rust interruption detector can later
turn it into an `interruption` row after a timeout.

### 7. CLI Tests

The new CLI commands should be tested against fixture databases.

Implemented commands:

```bash
agentsight token --db /tmp/agentsight-fixture.db --group-by model --json
agentsight audit --db /tmp/agentsight-fixture.db --audit-type llm --json
agentsight adapters list --json
agentsight adapters run --db /tmp/agentsight-fixture.db --adapter claude-code
```

Checks:

- JSON output is stable enough for scripts.
- Human output is readable but not used as the only test oracle.
- Time filters include boundary timestamps correctly.
- Empty results return success with empty arrays and zero totals.

### 8. Real Tool Smoke Tests

These checks validate the production path against installed tools instead of
only fixtures.

Claude Code, with a valid local Claude Code login:

```bash
cd collector
sudo -n rm -f /tmp/agentsight-claude-real.*
timeout 120s sudo -n env PATH="$PATH" HOME="$HOME" \
  ./target/debug/agentsight exec \
  --no-server \
  --db /tmp/agentsight-claude-real.db \
  --adapter auto \
  -o /tmp/agentsight-claude-real.log \
  -- claude -p 'Reply with exactly: agentsight-smoke' --output-format json

sudo -n ./target/debug/agentsight token \
  --db /tmp/agentsight-claude-real.db \
  --json
```

Expected result:

- The command prints `agentsight-smoke`.
- The capture exits with status 0.
- `raw_events` contains redacted `cli_output` evidence for the JSON result.
  Prompt text, raw stdout/stderr, and assistant response text are not stored;
  only usage-shaped fields needed by adapters are persisted.
- `token_usage` contains `claude_code_stdout_model_usage` rows from
  `modelUsage`; generic response usage and telemetry remain fallback evidence.
- `agent_sessions` contains a `claude-code` row after adapters run.

Automated gated test:

```bash
cd collector
AGENTSIGHT_REAL_CLI_SMOKE=1 \
cargo test real_claude_code_smoke -- --ignored --nocapture
```

OpenClaw container attach smoke, without requiring provider credentials:

```bash
docker run -d --name openclaw-smoke \
  -e OPENAI_API_KEY=dummy \
  -e OPENCLAW_GATEWAY_TOKEN=agentsight-smoke \
  ghcr.io/openclaw/openclaw:latest \
  node openclaw.mjs gateway --allow-unconfigured

cd collector
sudo -n rm -f /tmp/agentsight-openclaw-real.*
timeout -s INT 18s sudo -n env PATH="$PATH" HOME="$HOME" \
  ./target/debug/agentsight record \
  -c node \
  --binary-path docker://openclaw-smoke \
  --db /tmp/agentsight-openclaw-real.db \
  --adapter auto \
  -o /tmp/agentsight-openclaw-real.log \
  --server-port 7396
```

While `record` is running, generate real container Node HTTPS traffic:

```bash
docker exec openclaw-smoke node -e \
  "fetch('https://example.com').then(r=>r.text()).then(t=>console.log(t.length))"
```

The built-in capture timer stops the run through the normal shutdown path and
runs adapters automatically. To rerun adapters after a manually interrupted
capture:

```bash
sudo -n ./target/debug/agentsight adapters run \
  --db /tmp/agentsight-openclaw-real.db \
  --adapter auto
```

Expected result:

- `docker://openclaw-smoke` resolves to the container host PID and
  `/proc/<pid>/exe`.
- The capture does not panic in `SystemRunner`.
- `raw_events` contains `process`, `system`, and at least one parsed HTTP event
  from Node/OpenSSL.
- Token rows are expected to be empty unless valid provider credentials are
  available and an actual OpenClaw LLM request is triggered.

Cleanup:

```bash
docker rm -f openclaw-smoke
```

OpenClaw provider-token smoke, with a real OpenAI-compatible provider key:

```bash
cd collector
OPENAI_API_KEY=sk-... \
AGENTSIGHT_REAL_OPENCLAW_SMOKE=1 \
cargo test real_openclaw_provider_smoke -- --ignored --nocapture
```

Expected result:

- The test starts a fresh OpenClaw container, configures an API-key auth
  profile, attaches AgentSight with `--binary-path docker://<container>`, and
  triggers `openclaw infer model run --local --json`.
- `token_usage` contains provider response usage from the real OpenClaw LLM
  request.
- `agent_sessions` contains an `openclaw` row with `total_tokens > 0`.
- If no provider key is present, the test is skipped by default and should not
  be treated as coverage for real provider capture.

Gemini CLI, with a valid cached Gemini CLI login or API key:

```bash
cd collector
rm -f /tmp/agentsight-gemini-real.*
sudo -n env PATH="$PATH" HOME="$HOME" \
  ./target/debug/agentsight exec \
  --no-server \
  --db /tmp/agentsight-gemini-real.db \
  --adapter auto \
  -o /tmp/agentsight-gemini-real.log \
  -- gemini --model gemini-2.5-flash-lite \
    -p 'Reply with exactly: agentsight-smoke' --output-format json

sudo -n ./target/debug/agentsight token \
  --db /tmp/agentsight-gemini-real.db \
  --json
```

Expected result:

- The command prints `agentsight-smoke`.
- `canonical_events` contains a `gcp.gen_ai` request to
  `generativelanguage.googleapis.com` or `cloudcode-pa.googleapis.com`.
- `llm_calls` contains a Gemini row when AgentSight captures the matching
  response event.
- `raw_events` contains redacted `cli_output` evidence for Gemini JSON stats.
  Prompt text and raw stdout/stderr are not stored.
- `token_usage` contains `gemini_cli_stdout` rows from
  `stats.models.*.tokens`.
- `token_usage` contains generic `response_usage` rows when the TLS/SSE stream
  exposes Gemini `usageMetadata`; the gated test retries because Google may
  gzip or split some response bodies in ways that do not expose the final
  usage fragment every run.
- `agent_sessions` contains a `gemini-cli` row with `total_tokens > 0`.
- Invalid DB paths and migration errors return clean one-line errors.

Automated gated test:

```bash
cd collector
AGENTSIGHT_REAL_CLI_SMOKE=1 \
cargo test real_gemini_cli_smoke -- --ignored --nocapture
```

### 8. HTTP API Tests

Use a temp database and start the embedded server on a random port.

Implemented smoke scope:

- `/api/v1/snapshot` serves the same schema as `agentsight export`.
- `/api/v1/summary`, `/api/v1/events`, `/api/v1/token/summary`,
  `/api/v1/audit/events`, `/api/v1/agents`, `/api/v1/sessions`, and
  `/api/v1/interruptions` read from SQLite.
- `/api/events` remains as the legacy JSONL compatibility endpoint.

Remaining deeper API coverage:

- Pagination/cursor semantics beyond snapshot limits.
- Token timeseries bucket boundaries.
- Mutable interruption state transitions.

Planned command:

```bash
cd collector
cargo test server_api
```

Checks:

- API does not read the entire raw log for common dashboard calls.
- Cursor pagination is stable when new events are inserted.
- CORS and auth behavior are explicit in tests once auth exists.

### 9. Frontend Tests

The production frontend should consume `/api/v1` endpoints. The existing upload
path should remain tested separately.

Recommended test types:

- Component tests for token cards, audit table, interruption panel, and session
  detail views.
- API client tests with mocked `/api/v1` responses.
- E2E tests against a fixture-backed local server.

Planned commands:

```bash
cd frontend
npm test
npm run build
```

If Playwright is added:

```bash
cd frontend
npm run test:e2e
```

Minimum UI checks:

- Empty states render without raw JSONL upload.
- Token totals match fixture API responses.
- Audit filters update URL or internal state predictably.
- Long model names, paths, and error messages do not overflow.
- Session detail can show generic and adapter-backed rows.

### 10. Privileged eBPF Smoke Tests

These tests require root or the relevant BPF capabilities and should not run in
ordinary unit test jobs.

Manual smoke commands:

```bash
make build
sudo ./target/release/agentsight exec -- python3 -c 'print("hello")'
sudo ./target/release/agentsight record -c python --server-port 7395
```

Optional LLM smoke command when credentials are available:

```bash
sudo ./target/release/agentsight exec -- python3 script/test-python/test_openai.py
```

Checks:

- JSONL still receives events.
- SQLite DB receives raw and canonical events.
- Dashboard opens and uses `/api/v1`.
- Ctrl+C shuts down without corrupting the DB.

### 11. Performance and Durability Tests

Production queries should remain usable with large captures.

Recommended replay benchmarks:

- 100k raw events.
- 1M raw events.
- 24-hour simulated capture with repeated token summaries.
- Retention cleanup at 200 MB.

Metrics:

- Insert throughput.
- P95 query time for token summary and audit table.
- DB file size.
- Memory usage during replay.
- Adapter backfill time.

Planned command:

```bash
cd collector
cargo run -- bench-replay \
  --input ../docs/fixtures/large/mixed-1m.jsonl \
  --db /tmp/agentsight-bench.db
```

Initial acceptance targets:

- Token summary over 24h under 500 ms on a developer laptop.
- Audit page query under 300 ms for first page.
- Replay memory bounded and not proportional to total events.
- Retention cleanup completes without broken foreign keys.

### 12. Privacy and Redaction Tests

Production storage must not accidentally index secrets.

Tests should include:

- Authorization headers.
- API keys in JSON fields: `api_key`, `access_token`, `refresh_token`,
  `session_token`, `cookie`.
- Provider-specific headers such as `x-api-key`.
- Nested secret fields.
- Raw payload storage under privacy mode.

Expected behavior:

- Default mode redacts common headers before semantic projections.
- Privacy mode may store raw bodies as redacted summaries.
- Tests should assert that known secret strings do not appear in
  `canonical_events`, `llm_calls`, or token/audit summaries.

Raw event retention policy must be explicit. If raw events can contain full
prompts, production docs and CLI flags must make that clear.

## Manual Validation Matrix

| Scenario | Adapter | Expected result |
| --- | --- | --- |
| Python OpenAI script | none/provider | token and audit rows only |
| Anthropic messages fixture | provider | LLM calls and token totals |
| Anthropic SQL adapter fixture | sql/provider | deterministic token rows, idempotent rerun |
| Claude Code fixture | claude-code | session, conversation, tool calls |
| Claude Code SQL tool fixture | sql/agent | deterministic tool-call rows |
| OpenClaw fixture | openclaw | gateway session and token attribution |
| Gemini CLI fixture | gemini-cli | Gemini session and usageMetadata token totals |
| HTTP 401 response | generic/provider | open interruption and audit failure |
| Process exit during request | generic | interruption candidate |
| Large JSONL replay | none | bounded memory and indexed queries |

## Definition of Done for a New Adapter

- Fixture JSONL and expected semantic outputs are committed.
- Unit tests cover detection and malformed inputs.
- Replay test produces expected sessions/tool calls/tokens.
- Adapter contract tests pass.
- SQL adapters pass manifest, safety, idempotency, and incremental/full replay
  equivalence tests.
- Documentation lists supported versions and known limitations.
- Generic features still work when the adapter is disabled.

## Definition of Done for SQLite Storage

- Schema migration tests pass.
- Existing JSONL output remains compatible.
- Raw and canonical events are written in the same capture.
- Token and audit queries run from SQLite, not JSONL.
- Retention can enforce `AGENTSIGHT_GENAI_DB_MAX_SIZE_MB`.
- A corrupt or missing DB returns a clear error.
