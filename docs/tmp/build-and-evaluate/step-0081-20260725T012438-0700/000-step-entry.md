# Step 0081 entry: raw-action skeleton control for the profile-guided reader

Timestamp: 2026-07-25T01:24:38-07:00
Outer gate: EXPERIMENT
Branch at entry: `research/semantic-flamegraph-artifacts-v2`
Executor: external `grok` CLI agent, orchestrated by the root session

## Why this step exists

Step 0080 showed the semantic profile skeleton concentrates a strong reader's
attention: selecting groups from semantic paths alone (zero source content in
stage 1), the reader opened 53% of the source evidence and reached MAP 0.455,
91% of the full-trace reader's 0.502 and far above Direct+AgentProf's 0.326.

The step-0072 information-matched experiment found the semantic prefix adds
no ranking value over raw action in the pooled-score regime. Step 0080's
stage-1 selection is a different regime: the reader chooses WHERE TO LOOK
using only group labels. If a raw-action skeleton concentrates attention
materially worse than the semantic skeleton (lower MAP and/or more content
opened for the same group budget), that isolates the first measured
independent value of semantic naming for localization. If it ties again,
the semantic prefix's localization value remains unestablished and the
0080 result attributes to grouping-plus-drilldown generally.

## Registered hypothesis

Under the identical two-stage protocol and ≤5-group budget, the raw-action
skeleton yields lower MAP than the semantic skeleton (paired interval
excluding zero) and/or opens a larger fraction of source content, because
coarse raw-action groups (e.g. `run`) mix unrelated responsibilities.

## Fixed constraints

- Identical population, reader, decoding flags, retry/fallback rules,
  scoring, and paired-bootstrap procedure as steps 0079/0080.
- The raw-action grouping must be the SAME raw-action identity used by the
  step-0072 Direct+Raw+Evidence information-matched baseline, located in the
  frozen artifacts; if it cannot be located, stop and report.
- The executor must not modify any existing repository file, must not run
  any git command, and must not touch `docs/agentpprof-paper/` or `docs/paper/`.
- Complete 220-query run.

Full task specification: `experiment-001/task-spec.md`. Result review follows
in this directory before any paper use.
