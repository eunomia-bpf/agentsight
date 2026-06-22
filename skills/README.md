# Agent Behavior Analysis Skills

This directory contains repo-local skills for analyzing AI agent behavior from
local logs, observability traces, and AgentSight evidence. These are prototypes
for a shareable skills pack, not AgentSight runtime code.

## Skills

- `agent-interaction-insights`: analyze user-agent interaction behavior from
  transcripts, local agent logs, and observability traces. Use it to reduce
  user corrections, improve summary trust, stop retry loops, and decide what
  should change in prompts, AGENTS.md/CLAUDE.md, skills, evals, or workflows.
- `agentsight-system-friction`: analyze AgentSight system evidence. Use it to
  improve heavy-command budgets, retry behavior, service lifecycle cleanup,
  network binding, file/log hygiene, and next-run capture quality.

## Design Principles

- Split by evidence boundary, not by pipeline stage: semantic interaction vs
  system-level AgentSight facts.
- Treat AgentSight as a specialized strong evidence source, not a requirement
  for generic interaction analysis.
- Prefer evidence-backed findings over fixed dashboard layouts.
- Generate user-facing decision reports and dashboard layers on demand from
  the user's question; keep source manifests, ids, and handoff JSON in
  appendices unless the user asks for debug output.
- Use `agent-interaction-insights` for conversation-level analysis and
  `agentsight-system-friction` for OS/runtime analysis; combine them through
  the handoff contract when both matter.
- Do not include raw prompts, responses, auth headers, or secrets by default.
- Add scripts only after an adapter pattern repeats and needs deterministic
  behavior.

## Local Testing

These skills are stored in the repository so they can be reviewed and iterated
with the rest of the design docs. For local tests, point a client at this
directory or copy only the skill under test into that client's supported skills
location.
