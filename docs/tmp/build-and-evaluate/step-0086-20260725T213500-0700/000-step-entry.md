# Step 0086 entry: self-referential long-horizon case study (annotation run)

Timestamp: 2026-07-25T21:35:00-07:00
Outer gate: EXPERIMENT
Branch at entry: `research/semantic-flamegraph-artifacts-v2`
Executor: external `codex` CLI agent (also the annotation backend model
family), orchestrated by the root session

## Why this step exists

Step 0084's inventory recommended the AgentSight research worktree as the
primary Long Horizon case-study population: all 42 local sessions of the
`agentsight-research-semantic-flamegraph` project (8,991 operations, 10
long-horizon sessions, estimated ~15M annotation input tokens, ~2.3 h
worker time). These are the real Codex/Claude sessions that built the
AgentPProf system and this paper — the native no-sudo agentpprof scenario
and a memorable self-referential case: profiling the agents that built the
profiler.

This step freezes the population, runs the fixed automatic annotation, and
materializes the standard pprof profiles. Analysis and any paper text are
subsequent steps; nothing here edits `docs/paper/`.

## Fixed constraints

- Population frozen BEFORE annotation: the 42 sessions identified by the
  step-0084 inventory (project label exactly
  `agentsight-research-semantic-flamegraph`), each pinned at its
  freeze-time byte length so still-growing sessions are cut at a fixed
  boundary. No rescan-and-select after seeing annotations.
- Annotation uses the same fixed source-only instruction as step 0077
  (`step-0077-20260723T233616-0700/experiment-001/automatic-backend-instruction.md`)
  and the standard three-file annotation workspace contract; the backend
  writes only `annotation.json`.
- Outcome labels do not exist for this population; the case is RQ1-style
  attribution (where the budget went, which responsibilities recur), and
  the report must not invent success/failure judgments.
- Validity checks: complete coverage of every source node, exact
  conservation of operation and token mass, profiles open in stock pprof.
- Cost instrumentation: wall time and, where the codex CLI reports usage,
  provider token counters for the complete annotation run (RQ4-compatible).
- Anonymization for any reportable text: coarse project labels only, no
  quoted prompt/response content, no absolute paths.

Full task specification: `experiment-001/task-spec.md`.
