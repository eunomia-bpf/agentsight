# Materialized View Architecture

AgentSight uses one live materialized view as the boundary between capture and
consumption.

```text
Runner Event
  -> analyzer chain
  -> MaterializingAnalyzer
  -> MaterializedView
       updates in-memory rows directly
       publishes row-level sinks: SQLite, OTel
       serves CLI, TUI, and Web API snapshots
```

There is no AgentSight JSONL persistence or replay path. The embedded web
server shares the live `MaterializedView`; it does not rebuild a temporary view
from a file on each request.

## View Rows

The view owns the read model:

- `llm_calls`
- `token_usage`
- `audit_events`
- `process_nodes`
- `tool_calls`
- `sessions`
- `network_targets`
- `resource_samples`

Raw runner events enter the view once through `MaterializedView::ingest_event`.
Projection and accumulation happen in the view implementation, so consumers do
not handle raw event streams.

## Consumers

Consumers read the same view-native rows:

- CLI/TUI query `MaterializedView` snapshots and helper methods.
- Web API serves `/api/v1/snapshot` and focused row endpoints from the shared
  live view.
- SQLite persists selected rows through `ViewSink`.
- OTel exports completed `llm_call` rows through `ViewSink`.

`ViewSink` is row-oriented, not enum-oriented:

```rust
pub trait ViewSink: Send {
    fn llm_call(&mut self, row: &LlmCallRow) -> ViewResult<()> { Ok(()) }
    fn token_usage(&mut self, row: &TokenUsageRow) -> ViewResult<()> { Ok(()) }
    fn audit_event(&mut self, row: &AuditEventRow) -> ViewResult<()> { Ok(()) }
    fn process_node(&mut self, row: &ProcessNodeRow) -> ViewResult<()> { Ok(()) }
    fn tool_call(&mut self, row: &ToolCallRow) -> ViewResult<()> { Ok(()) }
    fn network_target(&mut self, row: &NetworkTargetRow) -> ViewResult<()> { Ok(()) }
    fn resource_sample(&mut self, row: &ResourceSampleRow) -> ViewResult<()> { Ok(()) }
}
```

## Process Tree

Process tree rendering is view-native:

```text
Snapshot.process_nodes  -> tree skeleton
Snapshot.audit_events   -> events attached by pid and timestamp window
Snapshot.resource_samples -> metrics charts
```

The frontend no longer uploads or parses AgentSight logs, and it does not
reconstruct process nodes from pseudo events. It consumes the current snapshot
contract directly.

## SQLite

SQLite is an optional materialized row store for saved sessions. It is not raw
event storage. Loading a saved database calls `sources::sqlite::load_view`,
which inserts rows into a `MaterializedView` through `load_*` methods and then
uses the same query path as live capture.

Legacy raw-event-only databases are rejected. Capture into a fresh view database
instead.

## Code Layout

```text
collector/src/analyzers/materializing.rs
  Event-stream analyzer that drives the shared view.

collector/src/view/mod.rs
  MaterializedView state, row emit/load methods, snapshot export.

collector/src/view/projection.rs
  Event normalization, LLM request/response matching, audit/process/resource
  row projection implemented directly on MaterializedView.

collector/src/model.rs
  Snapshot, row types, ViewSink.

collector/src/sinks/sqlite.rs
  SQLite row store and ViewSink implementation.

collector/src/sinks/otel.rs
  OTel ViewSink for GenAI spans.
```
