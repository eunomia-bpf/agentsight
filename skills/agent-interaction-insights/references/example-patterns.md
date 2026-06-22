# Example Patterns

Use these examples as field-shape hints.

## Usage Inventory

Input:

```json
{"session_id":"s1","cwd":"/repo","model":"claude-sonnet","total_tokens":42000}
```

Output:

- Session `s1` belongs to project `/repo`.
- Token total is session-level; per-call timing and tool status are unavailable.
- System side effects need external system findings.

## OTel GenAI Span

Input:

```json
{"name":"chat","attributes":{"gen_ai.system":"anthropic","gen_ai.request.model":"claude-sonnet","gen_ai.usage.input_tokens":1200}}
```

Output:

- `LlmCall.provider`: `gen_ai.system`
- `LlmCall.model`: `gen_ai.request.model`
- `LlmCall.tokens.input`: `gen_ai.usage.input_tokens`
- `AgentSession.id`: trace id or the strongest available session id

## Summary Mismatch

Input:

```json
{"final_summary":"all tests passed","observed_check":{"command":"cargo test","exit_code":101}}
```

Finding:

- `severity`: high
- `claim`: final summary conflicts with observed validation
- `evidence`: command and exit code
- `next_action`: require exact validation commands and statuses in summaries

## Findings To HTML Report

Input:

```json
[{"severity":"high","claim":"Final summary said tests passed, but cargo test failed","evidence":"cargo test exit_code=101"}]
```

Output shape: Markdown or HTML with high-severity findings first, then evidence tables, then gaps. Use short redacted prompt summaries by default.

## Collaboration Improvement Report

Input:

```json
{"reader":"agent owner","decision":"reduce user corrections in the next similar run","finding":"agent implemented pages before confirming the desired output shape"}
```

Output:

- Lead with the next-run collaboration changes.
- Explain the user-facing friction in plain language.
- Put technical source details in a short appendix.
