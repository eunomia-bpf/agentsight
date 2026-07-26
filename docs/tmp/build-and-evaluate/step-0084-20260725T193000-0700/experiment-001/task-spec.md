# Task spec: inventory local agent sessions for the long-horizon case study

You are an autonomous engineering agent working in
`/home/yunwei37/workspace/agentsight-research-semantic-flamegraph`.
SIZING ONLY. Read-only over all session data. Never run git commands.
Write deliverables only into THIS directory.

## Step 1: locate and count local sessions

- Codex sessions: `~/.codex/sessions/` (rollout JSONL files).
- Claude Code sessions: `~/.claude/projects/*/` (session JSONL files).
- The repository's `agent-session/` Rust crate documents both formats;
  `agentpprof --project-root` reads them. You may use
  `cargo run -p agentpprof -- --help` or read `agent-session/src/` to
  understand formats, but a direct Python scan of the JSONL files is fine
  and faster.

## Step 2: characterize (per session, then aggregate)

For every session file: project (coarse label only — e.g. the workspace
directory basename), start/end timestamps, duration, number of user
prompts, number of LLM calls, number of tool calls, and total
provider-reported tokens if present in the records. DO NOT quote prompt or
response content in your report.

Aggregate into a table by project and by duration bucket
(<10 min, 10-60 min, 1-6 h, >6 h). Identify the LONG-HORIZON candidates:
sessions with duration >= 1 hour OR >= 100 tool calls.

## Step 3: propose 2-3 candidate populations

Examples of the shape wanted (adapt to what the data shows):
(a) "all long-horizon sessions across all projects in the last N weeks";
(b) "all sessions of the agentsight research project (the agents that
    built this paper)";
(c) a single heavy project's complete session set.
For each candidate: session count, total operations (LLM+tool calls),
total tokens, and the estimated automatic-annotation cost using
step-0077's measured figures (27,362 actual input tokens and 15.14
worker-seconds per session; scale by relative session size where sizes
differ materially — document your scaling rule).

## Deliverables (all in THIS directory)

- `inventory.py` — the scan script (venv python at
  /home/yunwei37/workspace/.venv/bin/python3 has standard libs).
- `inventory-results.json` — raw per-session rows (coarse labels only).
- `results.md` — the aggregate tables, long-horizon candidate populations
  with annotation-cost estimates, and a recommendation of which population
  gives the strongest paper case study for the "Long Horizon" title.
- `execution-log.md` — commands and wall time.
