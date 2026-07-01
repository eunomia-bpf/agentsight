# AgentSight Sources

Use AgentSight/system evidence in this skill. Route raw Claude/Codex/Gemini transcripts to `agent-interaction-insights`. If AgentSight exports contain LLM request/response payloads, use metadata/join keys instead.

## Record Snapshot

Use exported record snapshots for the strongest per-run evidence:

```text
agentsight report export --db <db> -o snapshot.json
```

Record snapshots may include LLM call rows, audit rows, process nodes, stdio, file, network, and resource facts depending on capture mode. Use LLM row ids, timestamps, statuses, model names, and token counts only when needed for correlation; do not inspect prompt/response bodies in this skill.

## Saved SQLite Session

Use saved sessions when the user provides a DB path or asks about a specific recorded run. Prefer structured export when available; inspect table layout only when needed.

## Monitor DB

Use `~/.agentsight/monitor/monitor-*.db` for sampled, long-running monitor evidence. Treat it as aggregate or windowed evidence, not a complete trace.

## Live Or Local Summary

Use command output or user-provided summaries as system facts only if they include AgentSight source context. Ask for a DB/export when the claim needs stronger evidence.

## Collection Limits

State which capture modes were present: process, stdio, SSL/HTTP, file, network, resource, native session correlation. Missing capture mode means missing evidence, not absence of behavior.
