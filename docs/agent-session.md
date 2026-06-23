# agent-session

`agent-session` is the reusable Rust library for local AI coding-agent session
data. It owns agent-specific transcript discovery/parsing and exposes a common
session IR for applications such as AgentSight.

## Responsibilities

- Discover and parse local Claude Code, Codex, and Gemini CLI session files.
- Normalize model usage, token totals, tool calls, file references, prompts,
  cwd, timestamps, and session identifiers.
- Match live process trees to sessions using real path evidence, sticky
  bindings, and recent cwd fallback.
- Expose PID-to-session lookup through `SessionProcessMatches::session_for_pid`.

## Non-goals

- No OpenTelemetry exporter in this crate. AgentSight owns OTEL and other
  product sinks.
- No UI, report rendering, database schema, or eBPF capture logic.
- No dependency on AgentSight collector internals.

## OTel Alignment

`agent-session` remains a local IR. Its public fields use OTel-friendly names
where they fit: `agent_type`, `conversation_id`, and aggregate `usage`.
AgentSight maps those fields to OTLP only at export time and leaves
`conversation_id` unset when a native log has no real session/thread id.

## Release

AgentSight's release workflow publishes `agent-session` before publishing
`agentsight`. The workflow finds the next available `agent-session` patch
version on crates.io, updates `agent-session/Cargo.toml`, updates the collector
dependency, regenerates `collector/Cargo.lock`, and commits that release
snapshot before packaging.

After crates.io publish, docs.rs builds the Rust API docs and the unofficial
lib.rs index can discover the crate from crates.io metadata.
