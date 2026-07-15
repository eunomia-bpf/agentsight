# Common Evidence Model

Use this as a normalization target. Treat unavailable fields as coverage gaps.

## AgentSession

- `id`: source session id, trace id, or inferred stable id
- `agent`: Claude Code, Codex, Gemini CLI, custom agent, unknown
- `project`: cwd, repo, service, workspace, or inferred project
- `start_time`, `end_time`, `duration`
- `status`: success, failed, interrupted, partial, unknown
- `summary_claim`: final agent claim when available

## LlmCall

- `provider`, `model`
- `input_tokens`, `output_tokens`, `total_tokens`, `cost`
- `latency`, `status`, `error`
- `span_id`, `trace_id`, or source row id

## ToolCall

- `tool`: shell, file edit, read, search, browser, MCP tool, custom tool
- `input_summary`, `output_summary`
- `status`, `exit_code`, `duration`
- `target_summary`: command, file, endpoint, issue, PR, or resource id summary when safe

## UserSignal

- correction, interruption, approval, denial, retry request, scope change
- timestamp and source excerpt summary when available

## ValidationClaim

- claimed check, observed check, scope, status, and source ids
- use this to compare "verified" or "tests passed" claims with visible evidence

## ExternalSystemFinding

- optional summarized finding from `agentsight-system-friction`
- include id, severity, claim, and evidence summary
- do not expand raw AgentSight DB rows here

## Evidence Quality

Use `observed` for fields directly present in the source. Use `inferred` for reconstructed fields. Use `missing` when the source cannot observe a behavior.
