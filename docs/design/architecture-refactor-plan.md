# Architecture Refactor Plan: One Typed Pipeline, Adapter-Based Agent Support

Status: **implemented** (2026-06) — see §9 "As-built record" for what shipped
and where the plan was amended after contact with the code.
Scope: collector (primary), bpf userspace, frontend data contract, docs
Related: `product-scope-agent-native.md`, `materialized-view-architecture.md`,
`view-session-process-model.md`

## 1. Why refactor now

The product bet (see `product-scope-agent-native.md`) is:

> As agents replace task-specific tools, users and teams will need a small,
> trusted layer that records what those agents actually did.

The key words are **small** and **trusted**. The current codebase delivers the
right features but with an architecture that grew by accretion: the same LLM
payload is parsed three to four times in different layers, agent-specific
knowledge is scattered across at least ten files, and two parallel ingestion
systems feed the same view. Every new agent (Codex, OpenClaw, Qwen-Code, ...)
and every new scenario (policy suggest, behavior diff, verify) currently
requires touching many layers instead of one.

This plan reorganizes the collector around a single typed pipeline and an
agent-adapter registry. The goals, in priority order:

1. **Adapting to diverse agents becomes a one-file change.** Supporting a new
   agent CLI or a new LLM provider must not require edits in `view/`,
   `analyzers/`, `sources/`, `cmd_trace`, `cli_discover`, and the frontend.
2. **Large maintainability gain.** Each payload is parsed exactly once, by
   exactly one owner; the view layer only aggregates; surfaces only render.
3. **Large code reduction.** Estimated collector reduction from ~18.9k to
   ~13k LOC (-30%), plus ~1.5k LOC of unused bpf code out of the default build.
4. **No functional regression.** CLI surface, SQLite schema (versioned), web
   snapshot contract, and OTel export stay compatible; every phase ships green.

## 2. Current state (measured)

Collector: ~18.9k LOC Rust across 52 files. bpf userspace C: ~3.5k LOC.
Frontend: ~3k LOC TS/TSX. Layer map as of this writing:

```text
runners/   1.8k  eBPF binary execution -> Event stream
analyzers/ 3.7k  HTTPParser, SSEProcessor, SSLFilter, HTTPFilter,
                 AuthHeaderRemover, TimestampNormalizer, Materializing
sources/   1.7k  agent_native (~/.claude session files), proc, sqlite replay
view/      3.5k  canonical, projection, llm, live_top, top,
                 session_process_match, process_select
sinks/     1.1k  sqlite, otel (ViewSink)
output/    1.7k  format (999), tui (683)
cmd_* CLI  2.9k  main, cmd_trace, cmd_exec, cmd_debug, cmd_perf{,_live,_tui},
                 cli_db, cli_discover
server/    0.5k  hyper + rust-embed snapshot API
```

### 2.1 Problem P1 — payloads are parsed three to four times

The internal bus is `Event { data: serde_json::Value }` — untyped JSON all the
way through. Consequence: every consumer re-derives structure.

A single LLM HTTP response is processed by:

1. `analyzers/http_parser.rs:319-516` — HTTP/2 frame + HPACK decode, body
   reassembly into an `HTTPMessage` whose body is re-serialized to a string.
2. `analyzers/sse_processor.rs:68-126` — SSE line parse; each `data:` chunk is
   JSON-parsed and accumulated into an `sse_events` JSON array on the event.
3. `view/canonical.rs:93-108` — re-extracts host/method/path/status from the
   event JSON; calls `provider_from_host()` and `extract_model()` which
   **JSON-parse the body string again**.
4. `view/projection.rs:297-334` + `view/llm.rs:160-182` — re-iterates the
   `sse_events` array to extract token usage that the SSEProcessor already had
   in parsed form, then merges with body-derived usage via `max()` because
   neither path is authoritative.

`CanonicalEvent` (view/canonical.rs:38-60) is an option-bag — 14 `Option`
fields covering every possible kind — instead of an enum, so downstream code
is full of `if let Some(...)` chains and silent partial data.

### 2.2 Problem P2 — two competing ingestion systems

- **Runners** (live eBPF): `Event` → analyzer chain → `MaterializingAnalyzer`
  → `MaterializedView`.
- **Sources** (`sources/agent_native.rs`, 911 LOC; `sources/sqlite.rs`): parse
  `~/.claude` session files / saved DBs and push rows into the view directly,
  bypassing analyzers entirely (`agent_native.rs:145-157`).

Both populate the same view but share no contract. Logic that should be common
(session/token/audit extraction) exists twice with different shapes, and rows
carry no notion of where they came from.

### 2.3 Problem P3 — agent/provider knowledge is scattered

Knowing "what is Claude / Anthropic / Gemini" is encoded in at least:

| Knowledge | Where it lives today |
| --- | --- |
| host → provider | `view/llm.rs:31-46` (`provider_from_host`) |
| token usage field names per provider | `view/llm.rs` (`extract_token_usage`, `extract_token_usage_from_sse`) |
| model extraction from body/path | `view/llm.rs`, used from `view/canonical.rs` and `view/projection.rs` |
| Claude native session format | `sources/agent_native.rs` (911 LOC, hard-codes `/.claude/`) |
| which agents exist + how to find them | `cli_discover.rs` (hard-coded Claude/Gemini/OpenClaw rows) |
| BoringSSL/static-OpenSSL attach strategy | `cmd_trace.rs` (`build_trace_agent`), `binary_resolver.rs` (`binary_embeds_ssl`), docker:// handling in `main.rs` |
| Claude stdio/RPC protocol | `frontend/src/utils/stdioParser.ts:175-235` (client-side re-parse) |
| fixture payloads per provider | `runners/fake.rs` |

Adding one new agent today means touching most of this list. This is the
single biggest obstacle to the stated goal of "adapting to diverse agents and
scenarios".

### 2.4 Problem P4 — the view layer is too smart, and duplicated

`view/` should be a fold (events → rows → snapshot). Today it also parses
(P1), matches requests/responses (`projection.rs`, 945 LOC), correlates
sessions to processes (`session_process_match.rs`, 486 LOC), re-models the
process tree (`process_select.rs`, 377 LOC, overlapping `sources/proc.rs`,
387 LOC), and recomputes aggregations on every read (`live_top.rs`, 779 LOC
re-grouping rows the view already holds in BTreeMaps).

### 2.5 Problem P5 — three filter implementations

`ssl_filter.rs` (302) + `http_filter.rs` (281) + `filter_base.rs` are parallel
implementations of "drop events matching a field/op/value expression"
(~850 LOC total). One generic filter over typed events suffices (~250 LOC).

### 2.6 Problem P6 — CLI assembly partially duplicated

`cmd_trace.rs` is a good shared hub (`build_trace_agent_with_view`,
`configure_ssl_runner`, `run_debug_runner` are reused by record/debug). But
the perf trio (`cmd_perf.rs` + `cmd_perf_live.rs` + `cmd_perf_tui.rs`,
~930 LOC) splits one feature ("top") across three files by render mode, and
`output/format.rs` (999 LOC) re-aggregates snapshot data per output style.

### 2.7 Problem P7 — bpf userspace has no shared infra; dead weight

- Each userspace program implements its own JSON escaping and emit loop:
  `sslsniff.c:550-614` (inline printf escaping), `stdiocap.c:248-285`
  (own `print_json_escaped`), `process.c` (escape helper in
  `process_ext/map_flush.h:37-50`). Three different escape implementations is
  a correctness risk (one bad escape corrupts the JSONL stream).
- `browsertrace` (1263 LOC userspace + 273 LOC bpf) is compiled in the default
  `APPS` but is referenced nowhere in the collector — experimental code in the
  production build.

### 2.8 Problem P8 — documentation drift

`CLAUDE.md` and `materialized-view-architecture.md` reference
`collector/src/framework/`, `view/types.rs`, and `stores/sqlite.rs`; the tree
is now flat (`analyzers/`, `runners/`, `sinks/`, `model.rs`). Drifted docs
actively mislead agent-assisted development — expensive for this project in
particular.

## 3. Target architecture

Four stages, one typed contract, one place per piece of knowledge:

```text
┌────────────── Capture ──────────────┐   raw bytes/lines, no semantics
│ eBPF runners (sslsniff/process/     │
│ stdiocap)  ·  agent-native session  │   trait EventSource
│ files  ·  saved SQLite (replay)     │   -> Stream<RawEvent>
└──────────────────┬──────────────────┘
                   ▼
┌────────────── Decode ───────────────┐   parse ONCE, type EARLY
│ ssl bytes -> HTTP(1/2) -> SSE       │
│ -> LLM call (via ProviderAdapter)   │   -> Stream<SemanticEvent>
│ stdio bytes -> RPC msg (via         │      (typed enum, serde-stable)
│   AgentAdapter)                     │
│ proc events -> exec/exit/fs/net     │
└──────────────────┬──────────────────┘
                   ▼
┌────────────── Project ──────────────┐   pure fold, no parsing
│ MaterializedView: SemanticEvent ->  │
│ rows (llm_calls, audit_events, ...) │   + incremental pre-aggregates
│ + req/resp + session↔process match  │     (top groups, counters, peaks)
└──────────────────┬──────────────────┘
                   ▼
┌────────────── Serve ────────────────┐   render only
│ ViewSinks: SQLite, OTel             │
│ Surfaces: report/stat (text|json),  │
│ top (TUI), web /api/v1/snapshot     │
└─────────────────────────────────────┘
```

### 3.1 `SemanticEvent`: the single internal contract

Replace the untyped `Event.data: Value` bus *after decode* and the
`CanonicalEvent` option-bag with one enum:

```rust
pub struct SemanticEvent {
    pub ts_ms: u64,
    pub actor: Actor,            // pid, tid, comm, ppid, session hint
    pub source: SourceId,        // live-ebpf | agent-native | replay
    pub body: SemanticBody,
}

pub enum SemanticBody {
    LlmRequest(LlmRequest),      // provider, model, prompt summary, headers⁻
    LlmResponse(LlmResponse),    // usage: TokenUsage, stop reason, latency
    HttpExchange(HttpExchange),  // non-LLM traffic: host, method, path, status
    ProcessExec(ProcessExec),
    ProcessExit(ProcessExit),
    FileOp(FileOp),              // open/write/rename/unlink, path, flags
    NetConnect(NetConnect),
    StdioMessage(StdioMessage),  // decoded RPC: method, tool name, direction
    ResourceSample(ResourceSample),
    Raw(Value),                  // escape hatch for debug surfaces only
}
```

Rules:

- **Decode owns parsing.** `TokenUsage`, `model`, `provider` are computed
  exactly once, in the decode stage, by a `ProviderAdapter`. `view/llm.rs`'s
  dual body/SSE extraction paths and the `max()` merge disappear; SSE-derived
  usage is authoritative for streamed responses, body-derived for non-streamed
  — decided at decode time where the distinction is known.
- **Project owns matching and aggregation.** Request/response pairing and
  session↔process correlation stay in the view, but operate on typed fields,
  not JSON navigation.
- **`Raw` is quarantined.** Only `debug ssl/process/stdio` print raw events;
  nothing downstream of decode may match on JSON keys.
- The enum is serde-serializable with a `schema_version`, so the same type is
  the debug JSONL format, replacing today's ad-hoc shapes.

### 3.2 `EventSource`: one ingestion contract (merges runners and sources)

```rust
trait EventSource {
    fn id(&self) -> SourceId;
    async fn run(self: Box<Self>) -> Stream<SemanticEvent>;
}
```

- Live eBPF runners keep `BinaryExecutor` internally but emit through decode.
- `agent_native` becomes a source that **emits `SemanticEvent`s** (LlmRequest/
  LlmResponse/StdioMessage reconstructed from session files) instead of
  writing rows directly. Its 911 LOC shrink to the Claude-specific file format
  reader inside the Claude adapter (§3.3); generic session-walking moves to a
  shared `NativeSessionSource`.
- SQLite replay stays a row-level loader (it stores rows, not events) but is
  documented as the one sanctioned bypass.

Result: the view has exactly one write path for events
(`ingest(SemanticEvent)`) and one for replayed rows (`load_*`).

### 3.3 `AgentAdapter` + `ProviderAdapter`: knowledge gets one home each

```rust
/// One per agent CLI (claude.rs, gemini.rs, codex.rs, openclaw.rs, generic.rs)
trait AgentAdapter {
    fn name(&self) -> &str;                          // "claude"
    fn discover(&self) -> Vec<DiscoveredInstall>;    // replaces cli_discover rows
    fn attach(&self) -> AttachStrategy;              // comm filter? binary-path
                                                     // required? ssl-embedded?
                                                     // docker-aware?
    fn native_sessions(&self) -> Option<&dyn NativeSessionReader>; // ~/.claude
    fn stdio_codec(&self) -> Option<&dyn StdioCodec>; // decode RPC protocol
}

/// One per LLM wire protocol (anthropic.rs, openai.rs, gemini.rs)
trait ProviderAdapter {
    fn matches(&self, host: &str, path: &str) -> bool;
    fn decode_request(&self, http: &HttpRequest) -> Option<LlmRequest>;
    fn decode_response(&self, http: &HttpResponse, sse: Option<&SseStream>)
        -> Option<LlmResponse>;   // sole owner of token/model extraction
}
```

A static registry holds both lists. This directly absorbs:

- `provider_from_host` / `extract_token_usage*` / `extract_model*`
  (view/llm.rs) → provider adapters.
- hard-coded discover rows (cli_discover.rs) → `AgentAdapter::discover`.
- BoringSSL/static-OpenSSL/binary-path heuristics in `cmd_trace.rs` →
  `AttachStrategy` (the generic adapter keeps today's auto-discovery via
  `binary_embeds_ssl` as fallback, so unknown agents still work).
- `sources/agent_native.rs` Claude format → Claude adapter's
  `NativeSessionReader`.
- `frontend/src/utils/stdioParser.ts` → Claude adapter's `StdioCodec`; the
  snapshot then carries decoded stdio fields and the frontend stops parsing
  raw payloads entirely (it currently is the last client-side parser).

**Definition of done for this section: adding agent N+1 = adding one file in
`collector/src/agents/` (+ optionally one in `providers/`), zero edits
elsewhere.** Codex is the test case: today we can track its processes but not
rustls traffic (see memory note); a `codex.rs` adapter would declare
`AttachStrategy::ProcessOnly` + a native session reader, giving useful
receipts without TLS capture — something the current architecture cannot
express cleanly.

### 3.4 View becomes a pure, pre-aggregating fold

- `canonical.rs` is deleted (subsumed by `SemanticEvent`).
- `projection.rs` keeps pairing/correlation but drops all body/SSE/host
  parsing; estimated 945 → ~450 LOC.
- The view maintains incremental aggregates (per-pid/per-session token sums,
  exec counts, resource peaks) updated on ingest; `live_top.rs` (779) and the
  aggregation half of `output/format.rs` become thin renderers over snapshot
  fields; estimated combined ~1.8k → ~0.8k LOC.
- `process_select.rs` merges with `sources/proc.rs` into one process-tree
  model used by both live and view paths.

### 3.5 One filter, one debug shape

`ssl_filter` + `http_filter` + `filter_base` → one `EventFilter` operating on
`SemanticEvent` fields with the existing `field op value` expression syntax
(CLI flags `--ssl-filter`/`--http-filter` remain as aliases). ~850 → ~250 LOC.

### 3.6 CLI: commands pick sources + surfaces, nothing else

A command becomes declarative: `record = {sources: [ssl, process, stdio,
system], sinks: [sqlite], surfaces: [web, summary-on-exit]}`. Concretely:

- Fold `cmd_perf.rs`/`cmd_perf_live.rs`/`cmd_perf_tui.rs` into one
  `cmd_top.rs` with a `RenderMode { Tui, Table, Json }`; ~930 → ~500 LOC.
- `cmd_trace.rs` stays the assembly hub but consults the adapter registry for
  attach strategy instead of inlining BoringSSL/Node heuristics.
- `cmd_debug.rs` thin wrappers stay (they are already small).

### 3.7 bpf userspace: shared emit library, demote experiments

- Extract `bpf/jsonl.h` + `jsonl.c`: JSON string escaping, event envelope
  (`timestamp_ns`, `pid`, `comm`, `source`), perf-buffer poll loop helper.
  sslsniff/process/stdiocap link it; three escape implementations become one.
  This is a behavior-preserving change validated by the existing 60 C tests
  plus golden-output comparison.
- Move `browsertrace` out of the default `APPS` list (still buildable via
  `make experimental`). The default build, CI, and release artifact drop
  ~1.5k LOC of unused code.
- **Non-goal:** no rewrite of `.bpf.c` kernel code; CO-RE programs are stable
  and the risk/benefit is bad.

### 3.8 Documentation as part of the architecture

- Update `CLAUDE.md` and `materialized-view-architecture.md` to the real tree
  (no `framework/`, `model.rs` not `view/types.rs`, `sinks/` not `stores/`).
- Add `docs/design/semantic-events.md` documenting the `SemanticEvent` schema
  and its versioning policy once Phase 1 lands; it becomes the contract for
  frontend, OTel mapping, and future scenario features.

## 4. How this serves the product scenarios

Mapping to `product-scope-agent-native.md` — the point of the refactor is that
**new scenarios become readers of existing typed rows, not new pipelines**:

| Scenario | What enables it after refactor |
| --- | --- |
| Run receipt (S3) | `report` renders snapshot rows; richer because stdio/LLM fields are decoded server-side |
| Delegation confidence / policy suggest (S1, S2) | aggregation over typed `FileOp`/`ProcessExec`/`NetConnect` rows across saved DBs — a new reader, zero pipeline change |
| Recovery / incident (S4, S6) | typed `FileOp` with op kind + path makes "destructive op list" a filter, not a parser |
| Verify / review (S5) | declared-vs-observed = assertions over `SemanticEvent` stream; adapters make claims machine-checkable per agent |
| Behavior diff (S8) | diff two row sets; possible only because rows are schema-stable and provider-normalized |
| New agent (Codex/Qwen/...) | one adapter file (§3.3) |
| New provider endpoint | one provider adapter; token accounting correct everywhere at once |
| Live airlock (S9, later) | decode stage is the natural tap point for policy hooks — typed events exist *before* projection |

## 5. Estimated code impact

| Area | Today | After | Delta |
| --- | --- | --- | --- |
| view/ (canonical, projection, llm, live_top, top, matching) | ~3.5k | ~1.8k | -1.7k |
| analyzers/ (incl. filters → one) | ~3.7k | ~2.4k | -1.3k |
| sources/ + agents/ + providers/ (new) | ~1.7k | ~1.6k | -0.1k (net; adds adapter scaffolding, deletes duplication) |
| output/format + tui | ~1.7k | ~1.1k | -0.6k |
| cmd_perf trio → cmd_top | ~0.9k | ~0.5k | -0.4k |
| main/cmd_trace/cli_discover | ~1.8k | ~1.5k | -0.3k |
| **collector total** | **~18.9k** | **~13.4k** | **~-29%** |
| bpf default build (browsertrace out, jsonl.{h,c} in) | ~3.5k | ~2.3k | -1.2k |
| frontend (stdioParser removed) | ~3.0k | ~2.7k | -0.3k |

Numbers are estimates from the per-file analysis in §2; treat ±20%.

## 6. Migration plan

Each phase is independently shippable with `cargo test`, `bpf make test`, and
the smoke test (`collector/tests/real_cli_smoke_test.rs`) green. No phase
breaks the CLI surface or the SQLite schema without a version bump.

**Phase 0 — hygiene (small, immediate).**
Fix doc drift (§3.8); move `browsertrace` to experimental; extract
`bpf/jsonl.{h,c}` with golden-output tests. No Rust changes.

**Phase 1 — type the pipeline core (the keystone).**
Introduce `SemanticEvent` + `ProviderAdapter` (anthropic/openai/gemini).
Decode stage: HTTPParser/SSEProcessor emit typed LLM events; delete
`view/llm.rs` dual extraction, `view/canonical.rs`, and all JSON navigation in
`projection.rs`. Acceptance: a recorded Claude/Gemini session produces
byte-identical SQLite rows and web snapshot vs. before (golden test), and
`rg 'data\["' collector/src/view` returns nothing.

**Phase 2 — view as pure fold.**
Pre-aggregates in the view; shrink `live_top`/`format`; merge
`process_select` into one process model; unify the three filters.

**Phase 3 — one ingestion contract.**
`EventSource` trait; `agent_native` re-emits `SemanticEvent`s; rows gain a
`source` column (schema version bump with migration).

**Phase 4 — agent adapter registry.**
`collector/src/agents/{claude,gemini,openclaw,codex,generic}.rs`; move attach
heuristics out of `cmd_trace`, discover rows out of `cli_discover`, Claude
session format out of `sources/agent_native`, stdio decoding out of the
frontend (snapshot carries decoded stdio; frontend deletes `stdioParser.ts`).
Acceptance: the Codex adapter (process-only + native sessions) is added as a
single file and `agentsight discover` / `record` / `report` pick it up.

**Phase 5 — CLI consolidation.**
Merge the perf trio into `cmd_top.rs` with render modes; commands become
source+surface declarations.

Suggested order rationale: Phase 1 removes the most risk and unlocks every
later phase; Phase 4 is the user-visible payoff (new agents cheap); Phase 5 is
cleanup that gets easier after 2.

## 7. Risks and non-goals

- **Golden-output discipline.** Phases 1–3 must be validated by recorded
  fixture sessions (extend `FakeRunner` payloads into committed fixtures) so
  refactors are provably behavior-preserving.
- **SQLite compatibility.** Existing user DBs must keep loading; schema bumps
  only in Phase 3, with a loader for version N-1.
- **Do not** rewrite kernel-side eBPF, the web server, or the frontend views.
- **Do not** add a plugin/dylib system for adapters — static registry of
  in-tree modules is enough; "one file per agent" is the extensibility story.
- **Do not** generalize `SemanticEvent` for hypothetical telemetry; variants
  are added when a real source produces them (feature kill test applies to
  internal architecture too).

## 8. Acceptance criteria (project level)

1. Every payload byte is parsed by exactly one module; no JSON key access
   outside decode and `Raw` debug surfaces.
2. Adding an agent = one adapter file; demonstrated by the Codex adapter.
3. Collector ≤ ~14k LOC with unchanged CLI behavior and all tests green.
4. The frontend performs no raw payload parsing.
5. `CLAUDE.md` and design docs describe the tree as it exists.

## 9. As-built record (2026-06)

All phases were executed with every test suite green throughout (Rust
112 unit + 5 + 3 integration tests, bpf 160 C unit tests + runtime tests,
clippy clean). What shipped, and where reality forced amendments:

### Shipped as planned

- **Phase 0**: `bpf/jsonl.h` is now the single owner of JSON escaping for all
  userspace loaders (was three divergent implementations; the strict UTF-8
  validator with overlong/surrogate rejection won). `browsertrace` left the
  default `APPS` (buildable via `make experimental`), removing ~1.5k LOC from
  the default build and release artifact. Doc drift in `CLAUDE.md` and
  `materialized-view-architecture.md` fixed.
- **Phase 1 (the keystone)**: `semantic.rs` (typed `SemanticEvent`/
  `SemanticBody`), `decode.rs` (single owner of raw JSON navigation), and
  `providers/{anthropic,openai,gemini}.rs` landed. `view/canonical.rs`
  (option-bag) and `view/llm.rs` (dual token extraction) were deleted;
  `projection.rs` is a pure fold over typed events. Token usage is extracted
  once, at decode time, with the SSE/body decision made where the distinction
  is known. Row ids, matching logic (request-id 0.95 / single-pending 0.75,
  5-min TTL), and SQLite/snapshot output are behavior-identical.
- **Phase 2 (filters)**: one shared `ExprNode` boolean-expression core +
  comparison helpers in `filter_base.rs`; `--ssl-filter` and `--http-filter`
  DSL semantics preserved exactly.
- **Phase 4 (agents)**: `agents/{claude,codex,gemini,openclaw,opencode,aider,
  goose}.rs` registry now owns exec-name/package-path identification
  (absorbed from `view/process_select.rs`), `discover` rows (absorbed from
  `cli_discover.rs`), and native session locations (absorbed from
  `sources/agent_native.rs`). **Acceptance demo met**: the Codex adapter is
  one file and `agentsight discover` now lists `codex-cli` (process/stdio
  tracking + native `~/.codex` session receipts; no TLS capture — rustls).
- **Phase 5**: `cmd_perf.rs` + `cmd_perf_live.rs` + `cmd_perf_tui.rs` merged
  into `cmd_top.rs` with a shared refresh loop; `FakeRunner` is now
  test-only (`#[cfg(test)]`).

### Amendments (plan vs. reality)

- **§2.4 / Phase 2 view claims were partly misdiagnosed.** `view/live_top.rs`
  is live session↔process *correlation* plus presentation assembly (with
  tests), not redundant re-aggregation; `view/process_select.rs` and
  `sources/proc.rs` are complementary (selection logic vs. /proc reading),
  not duplicates; `output/format.rs` is rendering, not re-aggregation. These
  were left intact — destroying tested correlation logic to chase a LOC
  target would have violated the no-regression goal.
- **§3.2 / Phase 3 `EventSource` trait was dropped.** Agent-native data is
  intrinsically session-level aggregates (totals parsed from session files),
  not wire events; re-encoding rows as `SemanticEvent`s to immediately fold
  them back into rows is ceremony. The view's two write paths (event
  ingestion via decode; row loads for replay/import) are now the documented
  contract (`view/mod.rs` module docs), and rows already carry provenance via
  `view_source` — no schema bump was needed, so saved DBs keep loading.
- **§3.3 `AttachStrategy` was dropped.** Attach is mechanism-based
  (`binary_embeds_ssl` auto-discovery + `docker://`), not per-agent; adding
  unused per-agent attach metadata would be dead weight. Documented in
  `agents/mod.rs`.
- **§3.3 frontend stdio decoding stays in the frontend.**
  `stdioParser.ts` is woven into three display components (modal formatting,
  block adapters); relocating it requires a snapshot-contract change and UI
  verification, with low payoff since the snapshot legitimately carries raw
  stdio payloads as evidence. Revisit when the snapshot schema is next
  versioned.

### Second pass: attribution modeling + reduction sweep

A follow-up pass added the explicit per-agent attribution model the first
pass was missing, and swept the remaining mechanical redundancy:

- **`agents::Attribution`** (`NativeSessionFiles` / `SelfReported` /
  `ProcessOnly`) is now declared on every adapter and consumed by
  `view::session_process_match` (matching eligibility is explicit, not
  implicit in "which sessions happen to exist") and by `top`'s evidence
  notes (generated from the registry instead of a hardcoded dir list).
- **`AgentAdapter::decode_observations`**: the agent-reported telemetry
  decoders (Claude tengu batches, Gemini stdout stats) moved out of
  `decode.rs` into `agents/claude.rs` and `agents/gemini.rs`. Each agent's
  full attribution story — declaration plus decoding code — now lives in its
  adapter file. `decode.rs` only dispatches.
- Reduction sweep: deleted the 13/15-parameter constructors in
  `protocol_events.rs` (struct literals at call sites), inlined 25
  single-caller print functions from `format.rs` into their call sites,
  flattened the `ViewSink` delegation layer in `sinks/sqlite.rs`, and
  generated the view's `emit_*` fan-out from a macro.
- Explicitly rejected cuts: `agent_native::parse_content` (dense per-format
  semantics, tested), `system.rs` metrics (different CPU accounting semantics
  than `sources/proc.rs`), `cli_db`/`server` (already lean), and all test
  code.
- **`stat` folded into `report summary`** (the product call flagged below).
  `stat` is now a thin clap alias: `stat [--db] [--json]` runs the same code
  path as `report summary`, and `stat -- <cmd>` records like `record` then
  prints the merged receipt. `SessionSummary` absorbed every `stat` counter
  (view events, LLM calls, aggregate tokens, process execs/exits with
  success/failure split, file events + unique files, network hosts, HTTP/LLM
  errors, tool-call total, resource peaks), `report summary` gained `--json`,
  and the parallel `StatOutput` / `print_stat` / `load_stat` / `run_stat_query`
  machinery (plus a now-tautological `cmd_top` test, whose intent moved to
  `cli_db`) was deleted. Measured net change across the touched files was small
  (~-7 LOC in `cmd_top.rs` + `output/format.rs` + `cli_db.rs` + `main.rs`:
  ~102 lines of stat machinery removed, offset by the merged-summary population
  and counter-printing code added to the shared path) — the duplication was
  shallow, so the win is one summary surface with zero information loss rather
  than the ~200-line reduction the product call optimistically projected.

### LOC outcome (honest accounting)

The §5 reduction estimate did not survive the corrected diagnosis. After the
first pass, collector Rust stood at 18,864 → 19,460 (+~600); the second-pass
sweep brought it to **19,318 (+454 vs baseline)** — production code +~310,
test code +~150. The default bpf build dropped ~1.2k LOC (browsertrace out,
escaping deduplicated). Criterion 3 is therefore **not met** with the feature
set unchanged: the typed contract and the adapter registries cost roughly as
many lines as the duplication they removed, and the remaining mass is
essential parsers, the row store, three top render modes, and live
correlation. Going net-negative from here requires feature-level decisions
(e.g. folding `stat` into `report summary`, or consolidating `top`'s plain
table modes onto the TUI + `--json`), which are product calls — see the
options recorded alongside this section. Criteria 1, 2, 5 are met; 4 is met
except for the documented stdio display decoding. The structural wins stand:
payloads parsed once with a typed contract, the per-agent attribution story
declared and consumed from one place, and live correlation logic untouched.
