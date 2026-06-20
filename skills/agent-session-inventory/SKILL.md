---
name: agent-session-inventory
description: Summarize AI coding-agent session histories from local Claude Code/Codex/Gemini logs, Claude usage-data, AgentSight snapshots or monitor DBs, OpenTelemetry GenAI JSON/span exports, LangSmith run JSON, Langfuse trace exports, Datadog MCP query results, or plain session logs. Use when the user asks for recent agent usage, project/session inventory, active projects, model/tool/token/cost distribution, session coverage, or evidence availability; do not use for root-cause diagnosis or shareable artifacts.
---

# Agent Session Inventory

## Goal

Produce a quick inventory of agent sessions: what projects were touched, which agents ran, how many tokens were used, what the session coverage looks like, and what evidence is available for deeper analysis.

## When to Use

- User asks "what agent sessions do I have?"
- User asks "what projects have I been working on?"
- User asks "show me my recent Claude/Codex/Gemini usage"
- User asks "what data is available for analysis?"
- User needs to understand session coverage before diving into friction analysis

## When NOT to Use

- Root-cause diagnosis of specific failures (use agent-friction-analysis)
- Generating shareable HTML artifacts (use agent-behavior-artifact)
- Live capture or real-time monitoring (use AgentSight directly)

## Data Sources (Priority Order)

1. **AgentSight Monitor DB** (`~/.agentsight/monitor/monitor-YYYY-Www.db`)
   - Background session tracking with process/resource samples
   - Query `tracked_sessions` for session inventory

2. **AgentSight Record DB** (`agentsight-*.db` in cwd or specified)
   - Richer LLM call data, audit events, token totals
   - Query `sessions`, `llm_calls` tables

3. **AgentSight Snapshot JSON** (exported via `agentsight report export`)
   - Self-contained summary with sessions, token_summary, tool_calls

4. **Claude Code Native Logs** (`~/.claude/projects/*/sessions/`)
   - JSONL session files with tool calls, prompts, responses

5. **OpenAI Codex Native Logs** (`~/.codex/sessions/`)
   - Session directories with conversation state

6. **OpenTelemetry GenAI Exports** (JSON files with `gen_ai.*` spans)
   - Standard telemetry format from instrumented agents

7. **LangSmith Run JSON** (exported runs from LangSmith)
   - Run metadata, token usage, latency

8. **Langfuse Trace Exports** (exported traces)
   - Observation trees with token counts

## Workflow

1. Identify available data sources in priority order
2. Load session metadata (no raw prompts needed for inventory)
3. Group sessions by project, agent type, date range
4. Calculate aggregate metrics: session count, token totals, model distribution
5. Report evidence gaps and suggest next actions

## Output Format

### Summary Table

| Metric | Value |
|--------|-------|
| Data sources found | AgentSight monitor DB, Claude native logs |
| Date range | 2026-06-01 to 2026-06-19 |
| Total sessions | 47 |
| Unique projects | 12 |

### Sessions by Agent Type

| Agent | Sessions | Tokens (approx) |
|-------|----------|-----------------|
| Claude Code | 32 | 2.4M |
| Codex | 15 | 890K |

### Sessions by Project (Top 10)

| Project | Sessions | Last Active |
|---------|----------|-------------|
| agentsight | 8 | 2026-06-19 |
| my-paper-work | 6 | 2026-06-18 |

### Evidence Availability

- Monitor DB: process samples, resource peaks, file/network targets
- Native logs: prompts, tool calls, responses (if needed for friction analysis)
- Missing: OpenTelemetry exports, LangSmith data

### Suggested Next Steps

- For friction analysis on a specific session, use `agent-friction-analysis`
- For a shareable report, use `agent-behavior-artifact`

## Commands

Check for AgentSight monitor data:
```bash
ls -la ~/.agentsight/monitor/*.db 2>/dev/null | tail -5
```

Quick session inventory from AgentSight:
```bash
agentsight report list
```

Export snapshot for analysis:
```bash
agentsight report export -o snapshot.json
```

Check Claude native sessions:
```bash
find ~/.claude/projects -name "*.jsonl" -type f | head -10
```

## References

Read `references/data-sources.md` for detailed schema information and query patterns.
