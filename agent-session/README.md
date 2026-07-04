# agent-session

`agent-session` normalizes local AI coding-agent transcripts into one portable
Rust session model. It discovers Claude Code, Codex, and Gemini CLI sessions,
parses tokens/tools/files/prompts into a common IR, and includes a matcher for
linking live process trees back to agent sessions.

```rust
let sessions = agent_session::SessionCache::new()
    .discover_cached(25, std::time::Duration::from_secs(2));
```

The same IR can be serialized as an exchange trace:

```rust
let trace = agent_session::AgentTrace::portable(sessions);
let json = trace.to_pretty_json()?;
let sessions = agent_session::AgentTrace::from_json_str(&json)?.sessions;
```

`agent-session` owns this parsed-session trace schema. Downstream applications
can import it directly, or convert it to their own storage/profiling formats.
Use `AgentTrace::portable` for exports that should normalize host-local
filesystem fields before serialization: session paths become stable trace-local
names, `cwd` becomes `repo`, file paths become path groups, and tool commands
keep only the extracted command name. `AgentTrace::new` and `from_json_str`
preserve their input fields.
For AgentSight's semantic profiler, `script/agent_trace_to_operations.py`
converts the trace into normalized operation JSONL consumed by
`agentpprof --operation-file`. The converter uses event-level prompt/tool/LLM
rows when present and falls back to session-level summaries; prompt and LLM
previews are omitted unless `--include-previews` is passed. The end-to-end
bridge can be replayed with `python3 script/agent_trace_exchange_eval.py`,
which exports a fixture trace, converts it, imports both paths, and checks that
the folded outputs are byte-identical under the same operation stack.
For tools that expect a more standard trace container, AgentSight also provides
`agentpprof --export-standard-trace`, which writes Chrome Trace Event JSON
that can be opened by Chrome/Perfetto-style trace viewers, and
`agentpprof --standard-trace-file`, which imports that container back as
ordinary operations before profiling. `script/agent_trace_convert.py`
provides the same bridge when a workflow needs explicit intermediate operation
JSONL files, and `script/agent_trace_chrome_trace.py` remains the lower-level
Chrome bridge used by the exchange evaluation.

## Scope

- Transcript/session discovery and parsing for local coding-agent logs.
- Token, tool, file, prompt, cwd, and timing normalization.
- Process-tree to session matching, including PID-to-session lookup.

`agent-session` intentionally does not export OpenTelemetry directly.
Applications such as AgentSight can map the IR to SQLite, OTEL, reports, or any
other telemetry backend they use.

## Publishing

The crate is published from the AgentSight release workflow before `agentsight`
itself, then `agentsight` depends on that published version. Publishing to
crates.io also makes the crate available to docs.rs and discoverable by the
unofficial lib.rs index.
