# Agent Behavior Analysis Skills

This directory contains repo-local skills for analyzing AI agent behavior from
local logs, observability traces, and AgentSight evidence. These are prototypes
for a shareable skills pack, not AgentSight runtime code.

## Skills

| Skill | Use for |
|-------|---------|
| `agentpprof-flamegraph` | Generate semantic flamegraphs to visualize where token budget went |
| `agent-interaction-insights` | Analyze transcripts to reduce corrections, improve trust, stop loops |
| `agentsight-system-friction` | Analyze AgentSight system data for resource/retry/cleanup improvements |

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

## Usage

**In this repo**: Skills are symlinked from `.claude/skills` and work directly.

**In other projects**: Symlink or copy individual skill directories to `.claude/skills/`:

```bash
ln -s /path/to/agentsight/skills/agentpprof-flamegraph .claude/skills/
```

Or install the full pack:

```bash
ln -s /path/to/agentsight/skills .claude/skills
```
