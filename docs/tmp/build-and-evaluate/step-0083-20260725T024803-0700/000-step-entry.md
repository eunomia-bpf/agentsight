# Step 0083 entry: index-study replication on HINTBench (kimi reader)

Timestamp: 2026-07-25T02:48:03-07:00
Outer gate: EXPERIMENT
Branch at entry: `research/semantic-flamegraph-artifacts-v2`
Executor: external `kimi` CLI agent (also the reader model), orchestrated by
the root session

## Why this step exists

Steps 0079-0081 established on the complete TraceElephant workload: a
query-aware reader ladder (Direct-only 0.209 < Direct+AgentProf 0.326 <
semantic-skeleton profile-guided reader 0.455 ~ raw-skeleton 0.465 <
full-trace reader 0.502) and a significant semantic content-efficiency
effect (53.0% vs 65.0% content opened at equal MAP, paired delta +0.120
[+0.103, +0.137]). Before the paper states any cross-workload sentence,
the same fixed v1 protocol must replicate on a second complete public
workload. HINTBench (400 target-bearing queries) is next; AgentProcessBench
follows if budget allows.

The grok reader budget is exhausted, so this study uses the kimi CLI as the
reader for ALL conditions on this workload. Within-workload comparability is
preserved (every condition uses the same reader); the reader-family change
relative to the TraceElephant study is disclosed, and no number from this
step is merged with TraceElephant numbers into one pooled statistic.

## Registered hypotheses

1. Ladder replication: full-trace reader MAP > stored Direct+AgentProf, and
   the semantic-skeleton reader lands between them.
2. Content-efficiency replication: at the fixed 5-group budget, the
   semantic skeleton opens significantly less content than the raw-action
   skeleton at statistically indistinguishable MAP.

Per the no-negative-results policy, non-replication feeds iteration or
scopes the paper claim to TraceElephant; it does not enter the paper.

## Fixed constraints

Exact v1 protocols of steps 0079 (full-trace), 0080 (semantic skeleton),
and 0081 (raw-action skeleton), changed only in: workload (HINTBench frozen
step-0072 inputs), reader CLI (kimi -p, fixed flags, one retry), and the
raw/semantic group identities' HINTBench equivalents from the same frozen
artifact family. Complete population; no smoke-only reporting; no file
modification; no git; no docs/paper access.

Full task specification: `experiment-001/task-spec.md`.
