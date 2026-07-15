# Data Source Routing

Choose the source that can answer the user's decision question with the least private data.

## Local Agent Logs

- Claude Code: `~/.claude/projects/**/*.jsonl`, `~/.claude/usage-data/session-meta/*.json`.
- Codex: `~/.codex/sessions/**/*.jsonl`.
- Gemini CLI: use exported logs or `agent-session`-derived data when available.

Prefer pre-summarized exports when available. If raw JSONL is necessary, extract only the fields required for the question: timestamps, model/tool category, status, short task/claim summaries, validation claims, user correction markers, and internal session ids when correlation is required. Use full prompt/response text only for private-debug analysis requested by the user.

Use local logs for task intent, transcript flow, model/tool usage, user corrections, and final summaries. State that transcript-only evidence usually cannot prove OS side effects.

## Observability Platforms

- OpenTelemetry GenAI: map `gen_ai.*` spans to LLM calls and tool/agent spans.
- LangSmith/Langfuse: map traces, runs, observations, scores, feedback, and costs.
- Datadog MCP: treat MCP results as queried trace facts and preserve links or ids.

Use platform traces for app-reported calls, tools, evals, feedback, latency, cost, and errors. Use system findings for OS-level side effects.

## Plain Transcripts

Extract task, tool calls, commands, visible failures, corrections, and final claims. Label structured fields as inferred.

## Summarized System Findings

Use summarized system findings from `agentsight-system-friction` as external evidence. Correlate internally by session/time when available, and render only redacted command/path/host/session categories in reader-facing output.

## AgentSight Boundary

Use `agentsight-system-friction` for AgentSight record DBs, monitor DBs, and system snapshots. If the user provides already summarized AgentSight findings, treat them as supporting evidence and cite them as external system findings.
