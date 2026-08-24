# agent-session

`agent-session` normalizes local AI coding-agent transcripts into one portable
Rust session model. It discovers Claude Code, Codex, and Gemini CLI sessions,
parses tokens/tools/files/prompts into a common IR, and provides a portable
matcher for linking caller-supplied process trees back to those sessions.

```rust
let sessions = agent_session::SessionCache::new()
    .discover_cached(25, std::time::Duration::from_secs(2));
```

## Scope

- Transcript/session discovery and parsing for local coding-agent logs.
- Token, tool, file, prompt, cwd, timing, and plan normalization.
- Process-tree to session correlation from host-supplied process/evidence data.
- A `wasm32-wasip2` Component Model entrypoint for host-supplied transcript content.

Native process discovery (`/proc`, sysinfo, eBPF evidence) stays outside this
portable crate. AgentSight analysis adapts those host facts into the matcher and
then materializes views/storage/export data.

`agent-session` intentionally does not export OpenTelemetry directly.
Applications such as AgentSight can map the IR to SQLite, OTEL, reports, or any
other telemetry backend they use.

## Publishing

The crate is published from the AgentSight release workflow before `agentsight`
itself, then `agentsight` depends on that published version. Publishing to
crates.io also makes the crate available to docs.rs and discoverable by the
unofficial lib.rs index.
