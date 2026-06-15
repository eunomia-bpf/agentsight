# R170 Full-History Refresh

Status: `full_history_refresh_passed`

## Scope

- Sessions: 325.
- Source counts: `{'claude': 50, 'claude-subagent': 77, 'codex': 198}`.
- Raw tool events: 142468.
- Raw LLM events: 114837.
- System observations: 183714.

## LLM Tagger

- Requests: 118021.
- Cache hits: 82886.
- New llama.cpp calls: 35136.
- Failures: 0.
- Cache entries: 29342 -> 64477.

## Integrity

- Folded totals match report: True.
- Warning count: 1 (details redacted).

## Claim Boundary

R170 refreshes the current full-history AgentFlame annotation path with a real llama.cpp-compatible server and a seeded local tag cache. It strengthens mechanism and artifact reproducibility evidence only; it does not provide human tag adequacy, developer utility, broad exact lineage, or community adoption evidence.
