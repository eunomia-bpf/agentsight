# agent-session

`agent-session` normalizes local AI coding-agent transcripts into one portable
Rust session model. It discovers Claude Code, Codex, and Gemini CLI sessions,
parses tokens/tools/files/prompts into a common IR, and includes a matcher for
linking live process trees back to agent sessions.

The crate does not export OpenTelemetry directly; applications can map the IR to
any telemetry backend they use.
