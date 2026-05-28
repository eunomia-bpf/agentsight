# Production Observability Architecture

This document designs the next production-oriented layer for AgentSight:
unified events, SQLite-backed storage, generic query APIs, and optional
agent-specific adapters.

The core rule is simple: raw capture stays generic and lossless. Adapters add
semantic meaning, but they must not be required for basic audit, token, error,
and process queries.

## Goals

- Preserve the current zero-instrumentation capture path.
- Add a durable local event store that supports filtering, pagination, and
  aggregation without reading an entire JSONL file.
- Define one canonical event model that all built-in analyzers, APIs, and
  adapters use.
- Support useful generic features first: token totals, audit queries, HTTP/LLM
  error panels, process status, retention cleanup.
- Let Claude Code, OpenClaw, Cosh, Gemini CLI, and future tools plug in through
  adapters without scattering tool-specific logic through collectors or UI.
- Keep raw event replay possible so adapters can be developed and backfilled
  after a capture.

## Non-goals

- Replacing the existing JSONL output in the first refactor.
- Requiring a Claude Code or OpenClaw adapter before generic views work.
- Building a distributed multi-host trace store in the first phase.
- Making every provider schema perfect up front. Unknown fields should remain
  in JSON attributes and raw payloads.

## Current Baseline

The current collector emits `Event` records:

```rust
pub struct Event {
    pub timestamp: u64,
    pub source: String,
    pub pid: u32,
    pub comm: String,
    pub data: serde_json::Value,
}
```

This is a good ingestion envelope. The missing production layer is a stable
semantic index around it.

## Target Architecture

```text
eBPF runners
  | raw JSON
  v
runner Event stream
  |
  +--> existing analyzers
  |      TimestampNormalizer, SSEProcessor, HTTPParser, AuthHeaderRemover
  |
  +--> FileLogger (compat JSONL)
  |
  +--> StorageAnalyzer
          |
          +--> raw_events
          +--> canonical_events
          +--> generic projections
                 llm_calls, token_usage, audit_events, agent_processes
          |
          +--> AdapterRunner
                 provider adapters: openai, anthropic, gemini
                 agent adapters: claude-code, openclaw, cosh, gemini-cli
                 |
                 +--> sessions, conversations, tool_calls, interruptions

SQLite query service
  |
  +--> CLI: token, audit, discover, serve
  +--> HTTP API: dashboard, pagination, summaries
  +--> MCP/Skill tools later
```

## Data Tiers

AgentSight should store data in three tiers.

1. Raw events

   The original `Event` serialized as JSON. Raw events are append-only and are
   the source of truth for replay, debugging, and adapter backfills.

2. Canonical events

   A normalized, stable envelope with indexed fields: timestamp, event kind,
   process identity, HTTP fields, LLM fields, correlation fields, and summary.
   The canonical layer is intentionally broad but shallow.

3. Semantic artifacts

   Higher-level records produced by generic parsers or adapters: LLM calls,
   token usage, sessions, conversations, tool calls, interruptions, and agent
   process status.

Adapters write semantic artifacts. They may also update canonical correlation
fields, but they never mutate raw events.

## Canonical Event Model

The canonical model should be implemented as a Rust type and SQLite projection.
The current `Event` remains the ingestion envelope.

```rust
pub struct CanonicalEvent {
    pub schema_version: u16,
    pub event_id: String,
    pub raw_event_id: String,
    pub timestamp_ms: u64,
    pub ingest_timestamp_ms: u64,

    pub source: String,
    pub kind: EventKind,
    pub severity: Severity,
    pub summary: Option<String>,

    pub pid: Option<u32>,
    pub tid: Option<u64>,
    pub ppid: Option<u32>,
    pub uid: Option<u32>,
    pub comm: Option<String>,
    pub container_id: Option<String>,

    pub host: Option<String>,
    pub method: Option<String>,
    pub path: Option<String>,
    pub status_code: Option<u16>,

    pub provider: Option<String>,
    pub model: Option<String>,
    pub request_id: Option<String>,

    pub trace_id: Option<String>,
    pub session_id: Option<String>,
    pub conversation_id: Option<String>,
    pub parent_event_id: Option<String>,

    pub adapter_id: Option<String>,
    pub adapter_version: Option<String>,
    pub confidence: Option<f32>,

    pub attributes: serde_json::Value,
}
```

Recommended event kinds:

```text
http.request
http.response
llm.request
llm.response
llm.error
token.usage
process.exec
process.exit
process.signal
fs.open
fs.write
fs.mutation
stdio.message
stdio.rpc
resource.sample
agent.status
session.start
session.end
tool.call
interruption
security.redaction
unknown
```

The enum should be extensible. Unknown kinds must continue to store cleanly.

## SQLite Storage Design

SQLite is the first production store because it is local, simple to ship, easy
to inspect, and good enough for single-node AgentSight workflows. Use WAL mode
and batched writes.

### Core Tables

```sql
CREATE TABLE raw_events (
  id TEXT PRIMARY KEY,
  timestamp_ms INTEGER NOT NULL,
  source TEXT NOT NULL,
  pid INTEGER,
  comm TEXT,
  raw_json TEXT NOT NULL
);

CREATE TABLE canonical_events (
  id TEXT PRIMARY KEY,
  raw_event_id TEXT NOT NULL REFERENCES raw_events(id),
  schema_version INTEGER NOT NULL,
  timestamp_ms INTEGER NOT NULL,
  ingest_timestamp_ms INTEGER NOT NULL,
  source TEXT NOT NULL,
  kind TEXT NOT NULL,
  severity TEXT NOT NULL DEFAULT 'info',
  summary TEXT,
  pid INTEGER,
  tid INTEGER,
  ppid INTEGER,
  uid INTEGER,
  comm TEXT,
  container_id TEXT,
  host TEXT,
  method TEXT,
  path TEXT,
  status_code INTEGER,
  provider TEXT,
  model TEXT,
  request_id TEXT,
  trace_id TEXT,
  session_id TEXT,
  conversation_id TEXT,
  parent_event_id TEXT,
  adapter_id TEXT,
  adapter_version TEXT,
  confidence REAL,
  attributes_json TEXT NOT NULL DEFAULT '{}'
);

CREATE INDEX idx_canonical_time ON canonical_events(timestamp_ms);
CREATE INDEX idx_canonical_kind_time ON canonical_events(kind, timestamp_ms);
CREATE INDEX idx_canonical_pid_time ON canonical_events(pid, timestamp_ms);
CREATE INDEX idx_canonical_comm_time ON canonical_events(comm, timestamp_ms);
CREATE INDEX idx_canonical_host_time ON canonical_events(host, timestamp_ms);
CREATE INDEX idx_canonical_model_time ON canonical_events(model, timestamp_ms);
CREATE INDEX idx_canonical_session_time ON canonical_events(session_id, timestamp_ms);
```

### Generic Semantic Tables

```sql
CREATE TABLE llm_calls (
  id TEXT PRIMARY KEY,
  request_event_id TEXT,
  response_event_id TEXT,
  start_timestamp_ms INTEGER NOT NULL,
  end_timestamp_ms INTEGER,
  pid INTEGER,
  comm TEXT,
  provider TEXT,
  model TEXT,
  host TEXT,
  path TEXT,
  status_code INTEGER,
  error_type TEXT,
  error_message TEXT,
  request_body_json TEXT,
  response_body_json TEXT,
  adapter_id TEXT,
  confidence REAL
);

CREATE TABLE token_usage (
  id TEXT PRIMARY KEY,
  llm_call_id TEXT REFERENCES llm_calls(id),
  timestamp_ms INTEGER NOT NULL,
  pid INTEGER,
  comm TEXT,
  provider TEXT,
  model TEXT,
  input_tokens INTEGER DEFAULT 0,
  output_tokens INTEGER DEFAULT 0,
  cache_creation_tokens INTEGER DEFAULT 0,
  cache_read_tokens INTEGER DEFAULT 0,
  total_tokens INTEGER DEFAULT 0,
  source TEXT NOT NULL,
  adapter_id TEXT,
  confidence REAL
);

CREATE INDEX idx_token_time ON token_usage(timestamp_ms);
CREATE INDEX idx_token_model_time ON token_usage(model, timestamp_ms);
CREATE INDEX idx_token_comm_time ON token_usage(comm, timestamp_ms);

CREATE TABLE audit_events (
  id TEXT PRIMARY KEY,
  canonical_event_id TEXT REFERENCES canonical_events(id),
  timestamp_ms INTEGER NOT NULL,
  audit_type TEXT NOT NULL,
  pid INTEGER,
  comm TEXT,
  subject TEXT,
  action TEXT,
  target TEXT,
  status TEXT,
  summary TEXT,
  details_json TEXT NOT NULL DEFAULT '{}'
);
```

### Adapter Semantic Tables

These tables are optional at first but should be designed now so adapters write
to common surfaces.

```sql
CREATE TABLE agent_sessions (
  id TEXT PRIMARY KEY,
  agent_type TEXT NOT NULL,
  agent_name TEXT,
  pid INTEGER,
  comm TEXT,
  start_timestamp_ms INTEGER NOT NULL,
  end_timestamp_ms INTEGER,
  status TEXT NOT NULL DEFAULT 'active',
  model TEXT,
  input_tokens INTEGER DEFAULT 0,
  output_tokens INTEGER DEFAULT 0,
  total_tokens INTEGER DEFAULT 0,
  adapter_id TEXT NOT NULL,
  confidence REAL,
  attributes_json TEXT NOT NULL DEFAULT '{}'
);

CREATE TABLE conversations (
  id TEXT PRIMARY KEY,
  session_id TEXT REFERENCES agent_sessions(id),
  start_timestamp_ms INTEGER NOT NULL,
  end_timestamp_ms INTEGER,
  model TEXT,
  input_tokens INTEGER DEFAULT 0,
  output_tokens INTEGER DEFAULT 0,
  total_tokens INTEGER DEFAULT 0,
  status TEXT NOT NULL DEFAULT 'active',
  attributes_json TEXT NOT NULL DEFAULT '{}'
);

CREATE TABLE tool_calls (
  id TEXT PRIMARY KEY,
  session_id TEXT,
  conversation_id TEXT,
  timestamp_ms INTEGER NOT NULL,
  tool_name TEXT,
  tool_call_id TEXT,
  status TEXT,
  input_json TEXT,
  output_json TEXT,
  related_pid INTEGER,
  related_event_id TEXT,
  adapter_id TEXT NOT NULL,
  confidence REAL
);

CREATE TABLE interruptions (
  id TEXT PRIMARY KEY,
  timestamp_ms INTEGER NOT NULL,
  session_id TEXT,
  conversation_id TEXT,
  severity TEXT NOT NULL,
  category TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'open',
  reason TEXT NOT NULL,
  evidence_json TEXT NOT NULL DEFAULT '{}',
  adapter_id TEXT,
  confidence REAL
);
```

### Metadata and Retention

```sql
CREATE TABLE adapter_runs (
  id TEXT PRIMARY KEY,
  adapter_id TEXT NOT NULL,
  adapter_version TEXT NOT NULL,
  started_at_ms INTEGER NOT NULL,
  finished_at_ms INTEGER,
  mode TEXT NOT NULL,
  input_range_start_ms INTEGER,
  input_range_end_ms INTEGER,
  status TEXT NOT NULL,
  error_message TEXT
);

CREATE TABLE schema_migrations (
  version INTEGER PRIMARY KEY,
  applied_at_ms INTEGER NOT NULL,
  description TEXT NOT NULL
);
```

Retention should be controlled by:

```text
AGENTSIGHT_DB_PATH
AGENTSIGHT_GENAI_DB_MAX_SIZE_MB
AGENTSIGHT_DB_RETENTION_DAYS
```

Cleanup policy:

1. Delete oldest semantic records whose raw events are outside the retention
   window.
2. Delete oldest raw and canonical events until the database is under the size
   limit.
3. Run `VACUUM` only when requested or during low-traffic maintenance because it
   can block.

## Generic Parsing Without Adapters

The first useful layer should not depend on agent adapters.

Generic normalization can infer:

- HTTP request/response from `http_parser` events.
- LLM request/response from paths such as `/v1/messages`, `/v1/responses`,
  `/chat/completions`, `/v1/completions`, `:generateContent`, and
  `:streamGenerateContent`.
- Provider from host: OpenAI, Anthropic, Gemini, Azure OpenAI, Bedrock, or host
  fallback.
- Token usage from common response `usage` shapes:
  `input_tokens`, `output_tokens`, `prompt_tokens`, `completion_tokens`,
  `cache_creation_input_tokens`, `cache_read_input_tokens`.
- Errors from HTTP status, response body, missing response timeout, process
  exit, and resource alerts.

This supports `token`, `audit`, error panels, and basic process status before
any agent adapter exists.

## Adapter Types

There are three adapter categories.

### Provider Adapters

Provider adapters parse LLM API semantics. Examples:

- `anthropic`
- `openai`
- `gemini`
- `azure-openai`

They produce or refine:

- `llm_calls`
- `token_usage`
- `llm.error`
- model and provider fields
- finish reasons

### Agent Adapters

Agent adapters understand specific tools and sessions. Examples:

- `claude-code`
- `openclaw`
- `cosh`
- `gemini-cli`

They produce or refine:

- `agent_sessions`
- `conversations`
- `tool_calls`
- session/conversation IDs on canonical events
- agent-specific interruptions
- token attribution by session and conversation

### Target Adapters

Target adapters help discovery and attach strategy. Examples:

- Detect a Claude Code binary and recommend `--binary-path`.
- Detect an OpenClaw container and resolve `docker://openclaw`.
- Detect a Node-based Gemini CLI and attach to the Node binary.

These should feed `agentsight discover`, not the event ingestion schema.

## Adapter Contract

Adapters should work in both streaming and replay modes.

```rust
pub trait Adapter: Send {
    fn id(&self) -> &'static str;
    fn version(&self) -> &'static str;
    fn adapter_type(&self) -> AdapterType;
    fn capabilities(&self) -> AdapterCapabilities;

    fn detect(&mut self, event: &CanonicalEvent, ctx: &AdapterContext) -> Detection;

    fn process(
        &mut self,
        event: &CanonicalEvent,
        raw: Option<&serde_json::Value>,
        ctx: &mut AdapterContext,
        out: &mut SemanticEmitter,
    ) -> Result<(), AdapterError>;

    fn flush(
        &mut self,
        ctx: &mut AdapterContext,
        out: &mut SemanticEmitter,
    ) -> Result<(), AdapterError>;
}
```

Detection result:

```rust
pub struct Detection {
    pub matched: bool,
    pub confidence: f32,
    pub reason: Option<String>,
}
```

Adapters should follow these rules:

- Always include `adapter_id` and `confidence` on semantic rows they produce.
  Adapter execution version is recorded in `adapter_runs`; per-row
  `adapter_version` columns are planned for a later schema migration.
- Never modify raw events.
- Prefer adding semantic rows over rewriting canonical events.
- If an adapter needs to update correlation fields, do it through a dedicated
  correlation update table or explicit storage API.
- Be deterministic over a replayed raw event sequence.
- Be safe when two adapters match the same event. The query layer decides which
  semantic row wins based on confidence and specificity.

## Adapter Registry and Selection

CLI/API options:

```text
--adapter auto
--adapter claude-code
--adapter openclaw
--adapter gemini-cli
agentsight adapters list
agentsight adapters run --db record.db --adapter claude-code
agentsight discover --json
--no-adapters
```

Selection rules:

1. `--adapter auto` runs built-in SQL adapters when their DB evidence is
   present. The adapter SQL is idempotent, so reruns are safe for replay and
   backfill.
2. Explicit adapters run only the named adapter.
3. Adapter output records `adapter_id` and `confidence`; the query layer can use
   those fields to prefer more specific rows.
4. Agent adapters may consume generic `llm_calls` and `token_usage`.
5. `--no-adapters` leaves raw, canonical, and generic projections in SQLite
   without running any SQL adapter.

## Query Surfaces

### CLI

```text
agentsight exec --db record.db -- claude -p "hello"
agentsight record --db record.db -c node --binary-path docker://openclaw-smoke
agentsight exec --db record.db -- gemini -p "hello" --output-format text
agentsight token --db record.db --group-by model
agentsight token --db record.db --group-by comm --json
agentsight audit --db record.db --audit-type llm --json
agentsight export --db record.db --output trace.agentsight.json
agentsight adapters list
agentsight adapters run --db record.db --adapter auto
agentsight discover --json
```

`agentsight export` writes a static web/demo snapshot shaped like the read-only
API responses. The dashboard should consume this snapshot in upload/static mode
and `/api/v1/*` in live mode, so the UI has one data contract instead of a
separate JSONL parser.

### HTTP API

The embedded server serves SQLite-backed `/api/v1` endpoints when started with
`--db` or `AGENTSIGHT_DB_PATH`. The old `/api/events` JSONL endpoint remains for
compatibility.

```text
GET /api/v1/snapshot?event_limit=&audit_limit=
GET /api/v1/summary
GET /api/v1/events?event_limit=
GET /api/v1/token/summary?group_by=model|provider|comm|pid
GET /api/v1/audit/events?audit_limit=
GET /api/v1/agents
GET /api/v1/sessions
GET /api/v1/interruptions
```

`agentsight export` writes the same snapshot shape as `/api/v1/snapshot`, so
static demos can upload `trace.agentsight.json` without a live SQLite server.

## Frontend Model

The UI should stop parsing the full JSONL file directly for production use.
Recommended production pages:

- Overview: live process status, event rate, open interruptions.
- Token: input/output/total cards, model ranking, process ranking, timeseries.
- Audit: filterable table for LLM calls, process exec, file operations, stdio.
- Errors: HTTP/LLM errors, request timeout, process exits, resource alerts.
- Sessions: adapter-backed session and conversation details.
- Raw events: paginated fallback for debugging.

The existing upload/JSONL parser should stay useful for offline demos and bug
reports.

## Rollout Order

1. Add SQLite storage and canonical projection behind an opt-in flag.
2. Add generic LLM/token/audit projections.
3. Add query CLI and `/api/v1` endpoints.
4. Move dashboard token/audit/error pages to the query API.
5. Add adapter registry and replay runner.
6. Add Claude Code adapter as the first agent adapter.
7. Add OpenClaw and Cosh adapters.

## Open Questions

- Should the default DB path be `record.db` in local mode and
  `/var/log/sysak/.agentsight/agentsight.db` in service mode?
- Should JSONL and SQLite both be enabled by default for one release?
- How much prompt/response content should be indexed when privacy mode is on?
- Should remote dashboard auth be a static bearer token first, or delegated to
  a reverse proxy?
