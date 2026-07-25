# Results: query-aware direct-reader baseline on TraceElephant (RQ2)

## Population

- Workload: TraceElephant complete RQ2 collection
- Trajectories / target-bearing queries scored: 220
- Operations: 5960
- Zero-positive trajectories: 0 (excluded from MAP, same as existing protocol)
- All 220 target-bearing queries are included; zero-positive count is 0 on this workload.

## Input provenance (read-only, frozen)

- Source-only packets: `/home/yunwei37/workspace/agentsight-research-semantic-flamegraph/.agentsight/experiments/rq2-a0-v1/full/trace/packets`
- Operation projections / stable IDs: `/home/yunwei37/workspace/agentsight-research-semantic-flamegraph/.agentsight/experiments/traceelephant-rq2-v1/operations/projection.jsonl`
- Annotated targets (mistake_step): `/home/yunwei37/workspace/agentsight-research-semantic-flamegraph/.agentsight/experiments/traceelephant-rq2-v1/scorer/targets.jsonl`
- Stored Direct-only / Direct+AgentProf per-query AP: `/home/yunwei37/workspace/agentsight-research-semantic-flamegraph/.agentsight/experiments/rq2-current-agent-local-first-v1/full/per-query.jsonl`
  (from step 0072 / `rq2-current-agent-local-first-v1`; Direct-only = `local_only`, Direct+AgentProf = `local_agentprof`)
- Scoring: sklearn non-interpolated `average_precision_score` per target-bearing trajectory; arithmetic MAP
- Paired bootstrap: 10,000 resamples of trajectory clusters within benchmark strata (cell); seeds {'local_only': 20260923, 'local_agentprof': 20260924}

## Disclosures

- Reader model is the external **grok** family invoked via the grok CLI single-turn path
  (`-p` by default; `--prompt-file` for large packets that exceed OS ARG_MAX headroom).
  Fixed decoding: `--output-format plain --max-turns 3 --tools '' --no-subagents --verbatim`.
  This differs from the TraceElephant annotation backend used to build AgentProf groups.
- The direct reader is **query-specific**: it sees the task text and the full source-visible
  trajectory for that query and produces a ranking once per query.
  The AgentPProf hierarchy is constructed once (source-only, query-agnostic grouping) and
  then replayed for ranking; that asymmetry is intentional and not hidden.
- Reader packets contain only task text, operation_id, ordinal, native_path, and source_summary.
  No target labels, outcome labels, gold answers, localizer hits, or risk scores.

## MAP

| Method | MAP |
|---|---:|
| Direct reader (this experiment) | 0.501967 |
| Direct-only (stored) | 0.208713 |
| Direct+AgentProf (stored) | 0.325504 |

## Paired differences (reader − baseline)

| Baseline | Point ΔMAP | 95% interval | Nonpositive draws / 10000 |
|---|---:|---:|---:|
| Direct-only | +0.293254 | [+0.236545, +0.349977] | 0 |
| Direct+AgentProf | +0.176463 | [+0.129582, +0.224071] | 0 |

## Failure tally

- Parse failures scored as original-order ranking: 0
- OK first attempt: 217
- OK after one format retry: 3

## Cost

- Queries: 220
- Total wall time (sum of per-query grok walls): 6573.99 s
- Mean wall time per query: 29.88 s
- Median wall time per query: 25.68 s
- Total packet characters: 9809633
- Mean packet characters: 44589.2
- Max packet characters: 153291

Token counts are not always exposed by the plain-output CLI path; wall time and
packet character volume are the primary recorded cost measures.

## Honest interpretation

On the complete TraceElephant population (n=220), the query-aware direct reader achieves MAP=0.5020. Direct-only MAP is 0.2087 and Direct+AgentProf MAP is 0.3255 (stored step-0072 values).

Versus Direct-only, the paired point difference is +0.2933 with 95% interval [+0.2365, +0.3500].
Versus Direct+AgentProf, the paired point difference is +0.1765 with 95% interval [+0.1296, +0.2241].

Because the reader is query-specific and sees the full source-visible trajectory for that localization query, it is a strong current-practice competitor rather than an information-matched ablation of AgentPProf. A higher or lower MAP than Direct+AgentProf therefore does not by itself prove or refute the value of a once-built semantic hierarchy for multi-query / multi-measure reuse; it bounds how much ranking quality a one-shot full-trace reader can extract on this workload.

This file reports the complete population run only. The ≤3-query harness validation is not a paper result.
