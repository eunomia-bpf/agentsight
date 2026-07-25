# Step 0079 entry: RQ2 query-aware direct-reader baseline (delegated to grok)

Timestamp: 2026-07-24T23:57:53-07:00
Outer gate: EXPERIMENT
Branch at entry: `research/semantic-flamegraph-artifacts-v2`
Executor: external `grok` CLI agent, orchestrated by the root session

## Why this step exists

The RQ evidence audit (step 0077, `rq-evidence-audit.md`) requires the
strongest current-practice competitor the user asked about:

> a query-aware Agent that reads the same trace evidence directly and returns
> a ranked diagnosis without AgentPProf. Give that baseline the same query,
> source-visible content, model family, and explicit source-ID requirement as
> the profile reader; disclose that it is query-specific whereas the
> AgentPProf hierarchy is constructed once and replayed across queries and
> additive measures. Score ranked outputs with the same AP/MAP and external
> targets, and record its token/time cost.

This step runs that baseline on the complete TraceElephant workload first
(the smallest complete RQ2 population, 220 target-bearing queries), because
one complete workload with the fixed protocol is required before extending to
the other two. The reader model is the external grok model family; this
differs from the annotation backend and is disclosed as such.

## Fixed constraints

- RQ2 subject unchanged: real-problem localization. No RQ rewording.
- Same scoring as the existing RQ2 protocol: non-interpolated per-query AP,
  arithmetic-mean MAP over target-bearing queries, paired task-cluster
  bootstrap when compared against stored per-query AP of existing conditions.
- Complete TraceElephant population; harness validation on ≤3 queries is
  allowed but never reported as a result.
- The executor must not modify any existing repository file, must not run
  any git command, and must not touch the `docs/agentpprof-paper/` submodule.
- All new files stay inside this step directory.

The full task specification is in `experiment-001/task-spec.md`. Result
review follows in this directory before any paper use.
