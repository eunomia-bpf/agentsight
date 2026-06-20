---
name: agent-friction-analysis
description: Diagnose agent friction points, cost hotspots, and behavioral issues from AgentSight traces, session logs, or telemetry exports. Use when the user asks why an agent session was slow, expensive, or failed; when investigating tool call failures, retry storms, token waste, or resource exhaustion; or when comparing session efficiency. Do not use for simple session inventory or generating shareable artifacts.
---

# Agent Friction Analysis

## Goal

Identify the root causes of agent inefficiency, failures, and cost overruns. Produce actionable findings with specific evidence: call IDs, timestamps, token counts, error messages, and correlated events.

## When to Use

- User asks "why was this session so expensive?"
- User asks "what went wrong in this agent run?"
- User asks "why did the agent retry so many times?"
- User asks "what caused the timeout/failure?"
- User wants to understand token waste, tool failures, or resource exhaustion
- User wants to compare efficiency across sessions

## When NOT to Use

- Simple session inventory without diagnosis (use agent-session-inventory)
- Generating shareable HTML reports (use agent-behavior-artifact)
- Live debugging (use AgentSight directly)

## Friction Categories

### 1. Token Waste

- **Prompt bloat**: Large system prompts repeated across calls
- **Context overflow**: Hitting context limits and truncating
- **Retry storms**: Same prompt sent multiple times
- **Cache misses**: Low cache hit rate despite repeated prompts

Evidence: Compare input_tokens across calls, check cache_read_tokens ratio, look for duplicate request hashes.

### 2. Tool Failures

- **Command failures**: Non-zero exit codes from bash/shell tools
- **API errors**: HTTP 4xx/5xx responses from tool calls
- **Timeout exhaustion**: Tools hitting time limits
- **Permission denials**: Access denied errors

Evidence: Tool call status fields, exit codes, error messages in responses.

### 3. Latency Hotspots

- **Slow model calls**: High latency_ms relative to token count
- **Sequential blocking**: Long waits between parallel-capable calls
- **Network delays**: Slow external API responses
- **Resource contention**: CPU/memory pressure during calls

Evidence: latency_ms distribution, time gaps between calls, resource_samples correlation.

### 4. Behavioral Loops

- **Edit-fail-retry**: Repeated attempts to fix the same file
- **Read-without-action**: Reading files without making changes
- **Clarification spirals**: Multiple rounds of user clarification
- **Abandonment**: Starting tasks but not completing them

Evidence: Tool call patterns, file access sequences, conversation flow.

### 5. Resource Exhaustion

- **Memory pressure**: RSS growth leading to OOM or swapping
- **CPU saturation**: 100% CPU sustained during processing
- **Disk I/O**: Heavy read/write causing slowdown
- **Network saturation**: Many concurrent connections

Evidence: resource_samples peaks, process exit codes, correlation with failures.

## Workflow

1. Load session data from the most detailed source available
2. Build a timeline of events: LLM calls, tool calls, process events, resource samples
3. Identify anomalies: high token counts, failures, retries, latency spikes
4. Correlate events: what happened before/after each anomaly?
5. Classify findings by friction category
6. Rank by impact: cost, time, failure severity
7. Suggest specific remediation

## Output Format

### Friction Summary

| Category | Findings | Impact |
|----------|----------|--------|
| Token Waste | 3 | $2.40 estimated |
| Tool Failures | 5 | 12 min retry time |
| Latency Hotspots | 2 | 45s total delay |

### Finding 1: Retry Storm on File Edit (High Impact)

**Evidence**:
- Call IDs: `abc123`, `def456`, `ghi789`
- Timestamps: 14:23:01, 14:23:15, 14:23:28
- File: `src/main.rs`
- Token cost: 45K tokens across 3 attempts

**Root Cause**: Edit tool failed with syntax error on first attempt, agent retried with same approach.

**Remediation**: Add lint check before edit completion; reduce retry count for syntax errors.

### Finding 2: Cache Miss Pattern (Medium Impact)

**Evidence**:
- Cache read ratio: 12% (expected: 60%+ for repeated prompts)
- System prompt size: 8K tokens
- Repeated 15 times

**Root Cause**: System prompt changed slightly between calls, invalidating cache.

**Remediation**: Stabilize system prompt; use prompt caching hints.

### Evidence Timeline

```
14:23:01  LLM call (model: claude-3-opus, tokens: 15K)
14:23:08  Tool call: edit src/main.rs (FAILED: syntax error)
14:23:15  LLM call (model: claude-3-opus, tokens: 15K) -- RETRY
14:23:22  Tool call: edit src/main.rs (FAILED: syntax error)
14:23:28  LLM call (model: claude-3-opus, tokens: 15K) -- RETRY
14:23:35  Tool call: edit src/main.rs (SUCCESS)
```

## Commands

Export detailed snapshot for analysis:
```bash
agentsight report export -o snapshot.json --include-prompts
```

Query tool failures from record DB:
```bash
sqlite3 agentsight-latest.db "SELECT * FROM tool_calls WHERE status != 'success'"
```

Check resource pressure correlation:
```bash
sqlite3 agentsight-latest.db "SELECT * FROM resource_samples WHERE rss_bytes > 1000000000"
```

## References

Read `references/friction-patterns.md` for common friction signatures and remediation strategies.
Read `references/cost-estimation.md` for token-to-cost conversion rules.
