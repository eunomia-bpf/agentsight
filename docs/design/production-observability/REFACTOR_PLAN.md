# Production Observability Refactor Plan

This plan breaks the architecture into small, reviewable changes. It preserves
the existing JSONL-first workflow while adding SQLite, generic semantics, and
adapters.

## Principles

- Keep existing commands working during the migration.
- Add storage and semantics behind explicit flags before changing defaults.
- Keep raw events append-only and replayable.
- Extract reusable provider parsing from the current OpenTelemetry exporter
  instead of duplicating it.
- Make generic token/audit features work before agent adapters.
- Keep UI migration incremental: add `/api/v1` pages while keeping upload mode.

## Proposed Module Layout

```text
collector/src/
  semantic/
    mod.rs
    event.rs
    kind.rs
    normalize.rs
    llm.rs
    audit.rs
  storage/
    mod.rs
    sqlite.rs
    schema.rs
    migrations/
      0001_initial.sql
    retention.rs
    queries.rs
  adapters/
    mod.rs
    registry.rs
    contract.rs
    provider/
      mod.rs
      openai.rs
      anthropic.rs
      gemini.rs
    agent/
      mod.rs
      claude_code.rs
      openclaw.rs
      cosh.rs
  server/
    api_v1.rs
```

Frontend layout:

```text
frontend/src/
  lib/api/
    client.ts
    token.ts
    audit.ts
    sessions.ts
  components/token/
  components/audit/
  components/interruptions/
  components/sessions/
```

## Phase 0: Documentation and Fixtures

Deliverables:

- Architecture document.
- Testing plan.
- Refactor plan.
- Initial fixture directory structure.

No runtime changes.

Acceptance:

- Maintainers agree on canonical event fields and table names.
- First fixtures are synthetic or redacted, not copied from private captures.

## Phase 1: Canonical Event Types

Deliverables:

- `semantic::CanonicalEvent`.
- `semantic::EventKind`.
- `semantic::normalize_event(Event) -> CanonicalEvent`.
- Unit tests for HTTP, process, file, stdio, system, and unknown events.

Scope:

- Do not add SQLite yet.
- Do not add adapters yet.
- Use current `Event` as input.

Acceptance:

- Existing collector builds.
- Current JSONL output unchanged.
- Unit tests show stable classification for representative events.

## Phase 2: SQLite Storage Behind a Flag

Deliverables:

- `storage::SqliteStore`.
- Initial schema and migration runner.
- `StorageAnalyzer` that writes `raw_events` and `canonical_events`.
- CLI flags:

```text
--db <path>
--no-jsonl
--db-max-size-mb <n>
```

Environment support:

```text
AGENTSIGHT_DB_PATH
AGENTSIGHT_GENAI_DB_MAX_SIZE_MB
```

Scope:

- Keep JSONL enabled by default.
- SQLite is opt-in at first.
- Server can still serve `/api/events` from JSONL.

Acceptance:

- A trace run can write both JSONL and SQLite.
- `sqlite3 <db> 'select count(*) from raw_events'` shows rows.
- Retention policy has tests but does not need to be default yet.

## Phase 3: Generic LLM, Token, and Audit Projections

Deliverables:

- Extract provider/path/token parsing helpers from `otel_exporter.rs` into
  `semantic::llm`.
- `llm_calls` and `token_usage` projections.
- `audit_events` projections for LLM calls, process exec/exit, file mutations,
  stdio RPC, and HTTP errors.
- Tests using generic fixtures.

Scope:

- No agent session semantics.
- No Claude-specific assumptions.

Acceptance:

- Anthropic, OpenAI, and Gemini fixture replays produce token totals.
- `status_code >= 400` produces an audit failure.
- Process exec events appear in audit queries.

## Phase 4: Query CLI

Deliverables:

```text
agentsight token --db <path> --since 24h --group-by model --json
agentsight audit --db <path> --type llm --summary --json
agentsight audit --db <path> --pid 12345 --type process
```

Implementation:

- Add query functions under `storage::queries`.
- Keep output stable enough for scripting when `--json` is present.

Acceptance:

- CLI works from fixture DBs.
- Empty results are successful.
- Bad DB path returns a clean error.

## Phase 5: `/api/v1` Query Service

Deliverables:

- `server::api_v1`.
- Endpoints:

```text
GET /api/v1/events
GET /api/v1/token/summary
GET /api/v1/token/timeseries
GET /api/v1/audit/events
GET /api/v1/agents
GET /api/v1/interruptions
```

Scope:

- Keep `/api/events` compatibility.
- Use cursor pagination for event and audit tables.
- Add server option `--db`.

Acceptance:

- Frontend can fetch token and audit summaries without reading JSONL.
- API tests cover pagination and filters.

## Phase 6: Dashboard Token, Audit, and Error Pages

Deliverables:

- Token overview page.
- Audit page.
- Error/interruption page using generic signals.
- API client module.

Scope:

- Existing log/timeline/process-tree upload flow remains.
- Session details can be placeholder until adapters exist.

Acceptance:

- Dashboard loads from `/api/v1`.
- Token totals match CLI on the same DB.
- Long-running captures do not require loading entire event logs into browser
  memory.

## Phase 7: Adapter Registry and Replay Runner

Deliverables:

- Adapter trait and registry.
- Adapter contract tests.
- Replay command:

```text
agentsight replay --input <jsonl> --db <path> --adapter auto
agentsight adapters list
agentsight adapters run --db <path> --adapter claude-code
agentsight adapters run --db <path> --adapter gemini-cli
agentsight export --db <path> --output trace.agentsight.json
```

Scope:

- Implement provider adapters first, then agent adapters.
- The replay runner should use the same storage and adapter path as live
  capture.
- Export snapshots should be shaped like the read-only API responses so static
  web demos and live `/api/v1` views share one frontend data contract.

Acceptance:

- Generic provider fixtures pass through the adapter contract.
- Adapters can be disabled without breaking generic token/audit projections.

## Phase 8: Claude Code Adapter

Deliverables:

- `adapters::agent::claude_code`.
- Fixtures:

```text
basic_session.jsonl
tool_use_file_edit.jsonl
llm_401_error.jsonl
interrupted_stream.jsonl
```

Semantics:

- Detect Claude Code traffic and process identity.
- Group LLM calls into sessions/conversations when reliable IDs exist.
- Extract tool calls from request/response bodies.
- Attribute token usage to session/conversation.
- Emit interruptions for provider errors and interrupted streams.

Acceptance:

- Fixture replay creates expected sessions, conversations, tool calls, token
  totals, and interruptions.
- Generic token/audit output remains correct when adapter is off.
- Adapter confidence is visible in semantic tables.

## Phase 9: OpenClaw, Cosh, and Gemini CLI Adapters

Deliverables:

- OpenClaw adapter for gateway process/session conventions.
- Cosh adapter for built-in AgentSight skill workflows if data is available.
- Gemini CLI adapter for Node/Gemini-specific session hints.

Acceptance:

- Each adapter has fixtures and expected outputs.
- Gemini CLI fixture projects `usageMetadata` token totals and a
  `gemini-cli` session.
- `agentsight discover --list-known` documents target support.

## Phase 10: Production Defaults and Cleanup

Deliverables:

- SQLite enabled by default for `record` and `exec`.
- Default DB path policy.
- Retention enabled by default.
- Dashboard defaults to `/api/v1`.
- JSONL remains available with `--log-file` and/or `--jsonl`.

Potential defaults:

```text
local command: ./agentsight.db or record.db
service mode: /var/log/sysak/.agentsight/agentsight.db
default max DB size: 200 MB
```

Acceptance:

- Existing README quick start still works.
- A fresh `agentsight exec -- claude` creates DB-backed dashboard data.
- User can remove `/var/log/sysak/.agentsight` to clear history.

## Compatibility Plan

Short term:

- Keep `FileLogger`.
- Keep `/api/events`.
- Keep upload/paste frontend flow.
- Add DB as opt-in.

Middle term:

- Make DB default for production commands.
- Keep JSONL as replay/debug format.
- Use `agentsight export` snapshots for static upload/demo mode.
- Dashboard reads `/api/v1` by default.

Long term:

- JSONL can become a raw/replay compatibility format instead of the primary
  dashboard source.

## Risk Register

| Risk | Mitigation |
| --- | --- |
| SQLite write overhead affects capture | Batched writes, WAL mode, bounded queue, keep JSONL fallback |
| Schema changes block development | Migration tests and raw event replay |
| Adapter false positives | Confidence scores, explicit adapter selection, generic fallback |
| Sensitive prompt data indexed | Privacy mode, redaction tests, clear storage docs |
| Browser loads too much data | Cursor pagination and summary endpoints |
| Provider parsing duplicated | Extract shared parser from OTel exporter |
| Long captures grow without bound | Retention by size and by age |

## Suggested PR Slices

1. `semantic` module and unit tests.
2. SQLite schema/store and migrations.
3. StorageAnalyzer with opt-in `--db`.
4. Generic LLM/token/audit projections.
5. `token` and `audit` CLI.
6. `/api/v1` query endpoints.
7. Token/audit dashboard pages.
8. Adapter trait, registry, replay command.
9. Claude Code adapter and fixtures.
10. Default DB/retention behavior.

## Implementation Notes

- Use `rusqlite` initially unless async database access becomes necessary.
- Store timestamps in milliseconds since UNIX epoch to match current frontend
  expectations after `TimestampNormalizer`.
- Keep raw JSON as text for portability.
- Add common indexed columns instead of relying only on SQLite JSON functions.
- Avoid adding session IDs to the current `Event` type until storage and
  canonical events are in place.
- Make replay deterministic by sorting input by timestamp before semantic
  backfills when the input source is not already ordered.

## First Implementation Target

The smallest useful milestone is:

- `--db` writes raw and canonical events.
- Generic token usage is extracted from fixture LLM responses.
- `agentsight token --db ... --json` returns totals grouped by model.

This proves the unified model and SQLite storage without any agent adapter.
