# agent-session

`agent-session` is the reusable Rust library for local AI coding-agent session
data. It owns agent-specific transcript discovery/parsing, a common session IR,
and the portable process-to-session correlation algorithm.

## Responsibilities

- Discover and parse local Claude Code, Codex, and Gemini CLI session files.
- Normalize model usage, token totals, tool calls, file references, prompts,
  cwd, timestamps, and session identifiers.
- Correlate sessions with caller-supplied process trees and path evidence.
- Export the transcript parser as a `wasm32-wasip2` Component Model entrypoint
  when the host supplies transcript content.

AgentSight keeps native process discovery out of this crate. `agentsight-capture-core`
produces generic process facts; `agentsight-analysis` adapts those facts into the
portable matcher and owns materialized views, storage, and export.

## Non-goals

- No OpenTelemetry exporter in this crate. AgentSight owns OTEL and other
  product sinks.
- No UI, report rendering, database schema, eBPF capture, or `/proc` discovery.
- No dependency on AgentSight collector internals.

## OTel Alignment

`agent-session` remains a local IR. Its public fields use OTel-friendly names
where they fit: `agent_type`, `conversation_id`, and aggregate `usage`.
AgentSight maps those fields to OTLP only at export time and leaves
`conversation_id` unset when a native log has no real session/thread id.

## Release

AgentSight's release workflow publishes `agent-session` before publishing
`agentsight`. The workflow updates all consumers and regenerated locks from one
version updater before packaging.

After crates.io publish, docs.rs builds the Rust API docs and the unofficial
lib.rs index can discover the crate from crates.io metadata.
