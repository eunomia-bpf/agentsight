# System Friction Taxonomy

Use the smallest category that explains the system evidence.

## Categories

- `process_failure`: command exited non-zero, crashed, timed out, wrong cwd/env.
- `long_running_process`: process remained alive longer than expected or after task end.
- `file_scope_risk`: file activity outside workspace, unexpected deletes, broad writes, or secret-adjacent paths.
- `network_scope_risk`: unexpected host, protocol, port, or request class.
- `resource_waste`: high CPU, RSS, IO, wall time, or repeated expensive command.
- `capture_gap`: AgentSight source lacks the capture mode needed for the claim.
- `correlation_gap`: system event cannot be confidently attached to a session or agent.

## Severity

- `high`: affects trust, safety, data exposure, merge/deploy decision, or incident recovery.
- `medium`: caused delay, cleanup, high cost, resource pressure, or incomplete validation.
- `low`: useful optimization or hygiene issue.
- `info`: evidence limitation or context needed for correlation.

## Finding Template

- `severity`: high, medium, low, or info
- `claim`: concrete system-level statement
- `evidence`: statuses, timestamps, samples, durations, resource numbers, and redacted categories for sessions, processes, commands, paths, and hosts
- `inference`: limited to system cause unless interaction evidence is supplied
- `next_action`: cleanup, verify, rerun with capture mode, or correlate with interaction summary

Use `agent-interaction-insights` when user intent, final summary trust, or conversation-level corrections are needed to interpret a system finding.
