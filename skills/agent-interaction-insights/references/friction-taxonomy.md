# Friction Taxonomy

Use the smallest category that explains the evidence.

## Categories

- `tool_failure`: tool returned error, timeout, malformed input, permission denial as reported in transcript or trace evidence. Use `agentsight-system-friction` for OS-level exit codes, process crashes, or resource consumption details.
- `command_failure`: shell/tool command was reported as non-zero, crashed, timed out, or used wrong cwd/env in transcript or trace evidence. Use `agentsight-system-friction` to verify OS-level process facts.
- `test_failure`: build/test/lint/check failed or was narrowed after failure.
- `loop_retry`: repeated similar command, tool call, edit, read, or prompt pattern.
- `context_miss`: missed relevant file, instruction, prior result, or project rule.
- `goal_drift`: work moved away from the user's stated objective.
- `summary_mismatch`: final summary conflicts with observed evidence.
- `resource_waste`: high tokens, latency, repeated tool attempts, or cost without clear interaction progress. Use `agentsight-system-friction` for CPU/RSS/IO/wall-time waste.
- `evidence_gap`: question cannot be answered from available data.

## Severity

- `high`: affects trust, merge, deployment, review, or recovery decision.
- `medium`: caused delay, rework, cost, or incomplete validation.
- `low`: useful optimization or hygiene issue.
- `info`: context or evidence limitation.

Examples:

- `high`: final summary claims validation passed but visible checks failed; merge or review decision depends on the finding.
- `medium`: repeated failed command, avoidable expensive retries, or missing validation after code edits.
- `low`: inefficient file reads, redundant searches, or minor instruction hygiene.
- `info`: missing timestamps, no transcript coverage, or source format cannot prove side effects.

## Finding Template

- `severity`: high, medium, low, or info
- `claim`: concrete statement
- `evidence`: counts, statuses, timestamps, and redacted categories for ids, paths, commands, tools, or agents
- `inference`: likely cause, clearly labeled
- `next_action`: focused recommendation
