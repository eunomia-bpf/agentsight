# agent-session

`agent-session` is the reusable Rust library for local AI coding-agent session
data. It owns agent-specific transcript discovery/parsing and exposes a common
session IR for applications such as AgentSight.

## Responsibilities

- Discover and parse local Claude Code, Codex, and Gemini CLI session files.
- Normalize model usage, token totals, tool calls, file references, prompts,
  cwd, timestamps, and session identifiers.
- Serialize parsed sessions as `agentsight.agent-session.trace.v1` JSON for
  export/import between tools.
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

## Trace Exchange

Applications can exchange parsed sessions with the stable JSON wrapper:

```json
{
  "schema": "agentsight.agent-session.trace.v1",
  "sessions": []
}
```

The wrapper is not a profiling object. AgentSight's semantic profiler can read
it with `agentpprof --trace-file`, export the same sessions as
Chrome/Perfetto Trace Event JSON with `agentpprof --export-standard-trace`, or
import such a standard trace with `agentpprof --standard-trace-file`. The
standard trace path is still converted into ordinary operations before
profiling, so the only profiler abstractions remain operations and operation
stacks.

Use `script/agent_trace_to_operations.py` or
`script/agent_trace_convert.py import-standard --format chrome` when a workflow
needs an explicit operation JSONL file for `agentpprof --operation-file`. Trace
export accepts raw source selectors such as `--agent` and `--session-id`;
semantic tag filters remain a profiling step and are not applied while writing
the exchange trace. `AgentTrace::new` and `from_json_str` preserve their input
fields; `AgentTrace::portable` is the export constructor that normalizes
host-local filesystem fields before serialization. Portable export gives
sessions stable `trace/<agent>/<hash>.jsonl` names, writes `cwd` as `repo`,
merges file paths into path groups, and reduces tool command text to the
extracted command name.

## Release

AgentSight's release workflow publishes `agent-session` before publishing
`agentsight`. The workflow finds the next available `agent-session` patch
version on crates.io, updates `agent-session/Cargo.toml`, updates the collector
dependency, regenerates `collector/Cargo.lock`, and commits that release
snapshot before packaging.

After crates.io publish, docs.rs builds the Rust API docs and the unofficial
lib.rs index can discover the crate from crates.io metadata.
