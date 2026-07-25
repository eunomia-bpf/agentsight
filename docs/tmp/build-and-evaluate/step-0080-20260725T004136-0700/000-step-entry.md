# Step 0080 entry: profile-guided reader on TraceElephant (delegated to grok)

Timestamp: 2026-07-25T00:41:36-07:00
Outer gate: EXPERIMENT
Branch at entry: `research/semantic-flamegraph-artifacts-v2`
Executor: external `grok` CLI agent, orchestrated by the root session

## Why this step exists

Step 0079 measured the strongest current-practice competitor: a query-aware
reader over the full raw trajectory reaches MAP 0.502 on TraceElephant at a
mean 44.6K packet characters and 29.9 s per query, versus 0.326 for
Direct+AgentProf. The result review recorded the open complementarity
question: does the once-built semantic profile serve as an index that lets
the SAME reader reach comparable or better ranking quality while reading
materially less trajectory content?

This step tests exactly that. The reader, decoding settings, scoring, and
population are identical to step 0079. The only change is the input: a
compact profile skeleton first, then source evidence for only the operations
in the reader-selected groups (two fixed single-turn stages that materialize
pprof-style focus/drilldown).

Hypothesis (registered before the run): the profile-guided reader retains at
least Direct+AgentProf's MAP while using substantially fewer packet
characters than the full-trace reader; if it also approaches the full-trace
reader's MAP, the profile functions as a cost-reducing index for strong
readers.

## Fixed constraints

- RQ2 subject unchanged: real-problem localization; RQ4 coupling: per-query
  reading cost.
- Same 220-query TraceElephant population, same frozen targets, same AP/MAP
  scoring and paired task-cluster bootstrap as steps 0072/0079.
- Group structure comes from the frozen target-blind step-0072 Agent
  annotation (the same grouping behind Direct+AgentProf); no new annotation.
- The executor must not modify any existing repository file, must not run
  any git command, and must not touch `docs/agentpprof-paper/` or
  `docs/paper/`.
- Complete population run; ≤3-query harness validation never reported as a
  result.

Full task specification: `experiment-001/task-spec.md`. Result review follows
in this directory before any paper use.
