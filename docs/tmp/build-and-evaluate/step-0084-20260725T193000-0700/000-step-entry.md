# Step 0084 entry: local long-horizon population inventory (case-study sizing)

Timestamp: 2026-07-25T19:30:00-07:00
Outer gate: EXPERIMENT (sizing phase only)
Branch at entry: `research/semantic-flamegraph-artifacts-v2`
Executor: external `codex` CLI agent, orchestrated by the root session

## Why this step exists

The paper title now scopes to long-horizon agents. The strongest existing
long-horizon evidence is the 41-session Git-deployment population; the user
requested one additional case study over the long-horizon agent sessions on
the current machine — the native agentpprof scenario (no-sudo local-history
profiling of ~/.codex and ~/.claude session logs).

This step is SIZING ONLY: inventory the local sessions, characterize the
candidate population, and estimate annotation cost using step-0077's
measured per-session figures (about 27,362 actual input tokens and 15.1
worker-seconds per session for the automatic backend). No annotation, no
paper change, no LLM spend beyond the inventory itself.

## Fixed constraints

- Read-only over session histories; the executor must not modify, move, or
  delete any session file.
- Anonymization note: the eventual case study must sanitize user paths and
  project identifiers; the inventory report should already avoid quoting
  sensitive prompt content (counts, sizes, durations, and coarse project
  labels only).
- Population definition follows the user's case-study rule: a collection
  of many complete sessions, not one favorable trace.

Full task specification: `experiment-001/task-spec.md`.
