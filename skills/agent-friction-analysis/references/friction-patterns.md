# Friction Patterns Reference

## Token Waste Patterns

### Pattern: Repeated System Prompts

**Signature**:
- High input_tokens with low output_tokens ratio
- Similar prompt content across consecutive calls
- Low cache_read_tokens / input_tokens ratio

**Detection Query**:
```sql
SELECT 
  model,
  COUNT(*) as calls,
  AVG(input_tokens) as avg_input,
  AVG(output_tokens) as avg_output,
  SUM(cache_read_tokens) * 1.0 / SUM(input_tokens) as cache_ratio
FROM llm_calls
GROUP BY model
HAVING cache_ratio < 0.3 AND calls > 5;
```

**Remediation**:
- Use prompt caching (Anthropic: cache_control blocks)
- Stabilize system prompts across calls
- Move dynamic content to user messages

### Pattern: Context Window Overflow

**Signature**:
- input_tokens approaching model context limit
- Truncation indicators in response
- Increasing token counts per conversation turn

**Detection**: Check if input_tokens > 0.8 * model_context_limit

**Remediation**:
- Summarize conversation history
- Use retrieval instead of full context
- Split into multiple sessions

### Pattern: Retry Storm

**Signature**:
- Multiple LLM calls with similar prompts in short time window
- Tool failures between retries
- Exponential token usage

**Detection Query**:
```sql
SELECT 
  session_id,
  COUNT(*) as retry_count,
  SUM(input_tokens) as total_tokens
FROM llm_calls
WHERE timestamp BETWEEN :start AND :start + 60000  -- 60 second window
GROUP BY session_id
HAVING retry_count > 3;
```

**Remediation**:
- Add retry limits with backoff
- Validate tool inputs before execution
- Use different approach after N failures

## Tool Failure Patterns

### Pattern: Edit-Fail-Retry Loop

**Signature**:
- Edit tool called repeatedly on same file
- Non-success status between edits
- Growing token cost per attempt

**Detection**: Group tool_calls by target file, count failures

**Remediation**:
- Lint/compile check before marking edit complete
- Read file state after failure
- Limit retry attempts per file

### Pattern: Permission Denial Cascade

**Signature**:
- Multiple tool calls with "permission denied" or "access denied"
- Different targets hit with same error
- Agent trying alternatives without understanding root cause

**Detection**: Grep for permission-related error strings in tool outputs

**Remediation**:
- Surface permission errors clearly to agent
- Provide elevated permissions if safe
- Stop cascading attempts early

### Pattern: Timeout Exhaustion

**Signature**:
- Tool calls with latency near timeout limit
- Partial results or empty responses
- Subsequent retries

**Detection**: tool_calls.latency_ms > timeout_threshold * 0.9

**Remediation**:
- Increase timeout for known slow operations
- Split large operations into chunks
- Use async execution with polling

## Latency Patterns

### Pattern: Sequential Blocking

**Signature**:
- Multiple independent operations executed serially
- Large time gaps between completions
- Low CPU utilization during waits

**Detection**: Calculate time between call completions vs parallel potential

**Remediation**:
- Use parallel tool execution
- Batch independent operations
- Pipeline results when possible

### Pattern: Network Roundtrip Overhead

**Signature**:
- Many small LLM calls
- Latency dominated by network time (not token processing)
- Chatty conversation pattern

**Detection**: latency_ms / output_tokens ratio > threshold

**Remediation**:
- Batch requests where possible
- Use streaming for long outputs
- Reduce call frequency with better planning

## Behavioral Patterns

### Pattern: Read-Without-Action

**Signature**:
- File read operations not followed by edits
- Growing context without changes
- Agent "exploring" without committing

**Detection**: Count read tool calls vs edit tool calls per file

**Remediation**:
- Explicit action planning before exploration
- Limit exploration budget
- Require justification for reads

### Pattern: Clarification Spiral

**Signature**:
- Multiple user turns with questions
- Growing message count without task progress
- Same question rephrased

**Detection**: Count clarifying questions vs action completions

**Remediation**:
- Better initial task specification
- Assume reasonable defaults
- Provide structured prompts

## Resource Exhaustion Patterns

### Pattern: Memory Pressure

**Signature**:
- RSS growth over session lifetime
- Sudden failures after high memory
- OOM errors in process exits

**Detection Query**:
```sql
SELECT 
  session_id,
  MAX(rss_bytes) as peak_rss,
  (SELECT status FROM tracked_sessions WHERE id = session_id) as final_status
FROM resource_samples
GROUP BY session_id
HAVING peak_rss > 4000000000;  -- 4GB
```

**Remediation**:
- Monitor memory during long sessions
- Restart after memory threshold
- Identify memory-leaking tools

### Pattern: CPU Saturation

**Signature**:
- Sustained 100% CPU on one or more cores
- Increased latency for all operations
- Thermal throttling indicators

**Detection**: cpu_percent >= 95 for extended periods

**Remediation**:
- Profile CPU-heavy operations
- Add cooling pauses
- Use more efficient algorithms
