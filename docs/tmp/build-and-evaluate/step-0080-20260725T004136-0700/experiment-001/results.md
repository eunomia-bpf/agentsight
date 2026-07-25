# Results: profile-guided reader on TraceElephant (RQ2/RQ4)

## Scientific question

Does the once-built semantic profile act as an index for a strong query-aware
reader: retaining ranking quality while reading materially less trajectory
content than the full-trace reader of step 0079?

## Population

- Workload: TraceElephant complete RQ2 collection
- Trajectories / target-bearing queries scored: 220
- Operations: 5960
- Zero-positive trajectories: 0 (excluded from MAP)

## Input provenance (read-only, frozen)

- Source-only packets: `/home/yunwei37/workspace/agentsight-research-semantic-flamegraph/.agentsight/experiments/rq2-a0-v1/full/trace/packets`
- Operation projections / stable IDs: `/home/yunwei37/workspace/agentsight-research-semantic-flamegraph/.agentsight/experiments/traceelephant-rq2-v1/operations/projection.jsonl`
- Annotated targets (mistake_step): `/home/yunwei37/workspace/agentsight-research-semantic-flamegraph/.agentsight/experiments/traceelephant-rq2-v1/scorer/targets.jsonl`
- Stored Direct-only / Direct+AgentProf per-query AP: `/home/yunwei37/workspace/agentsight-research-semantic-flamegraph/.agentsight/experiments/rq2-current-agent-local-first-v1/full/per-query.jsonl`
  (Direct-only = `local_only`, Direct+AgentProf = `local_agentprof`)
- Step 0079 direct_reader per-query AP / costs: `/home/yunwei37/workspace/agentsight-research-semantic-flamegraph/docs/tmp/build-and-evaluate/step-0079-20260724T235753-0700/experiment-001/raw-results.json`
- **Frozen Agent+Evidence group mapping**: `/home/yunwei37/workspace/agentsight-research-semantic-flamegraph/.agentsight/experiments/rq2-canonical-tags-v2-current/trace/results/fixed-groups.jsonl`
  (key `source_preserving_agent`; step-0072 source_preserving_agent paths
  from `rq2-canonical-tags-v2-current` / TraceElephant)
- Scoring: sklearn non-interpolated `average_precision_score`; arithmetic MAP
- Paired bootstrap: 10,000 resamples of trajectory clusters within strata; seeds {'local_only': 20260923, 'local_agentprof': 20260924, 'direct_reader': 20260925}

## Protocol

- Stage 1: profile skeleton only (operation_id, ordinal, semantic path), grouped by full path; select ≤5 groups.
- Stage 2: same skeleton + `source_summary` for members of selected groups only; rank operation IDs.
- Reader: grok CLI, `--output-format plain --max-turns 3 --tools '' --no-subagents --verbatim`.
- Fallbacks: stage-1 fail → largest 5 groups; stage-2 fail → original-order ranking.

## MAP

| Method | MAP |
|---|---:|
| Profile reader (this experiment) | 0.455333 |
| Direct reader (step 0079) | 0.501967 |
| Direct+AgentProf (stored) | 0.325504 |
| Direct-only (stored) | 0.208713 |

## Paired differences (profile_reader − baseline)

| Baseline | Point ΔMAP | 95% interval | Nonpositive draws / 10000 |
|---|---:|---:|---:|
| Direct reader (step 0079) | -0.046633 | [-0.083111, -0.011590] | 9961 |
| Direct+AgentProf | +0.129829 | [+0.079722, +0.179067] | 0 |
| Direct-only | +0.246621 | [+0.189145, +0.304131] | 0 |

## Failure tally

- Stage-1 largest-groups fallbacks: 0
- Stage-1 OK first attempt: 220
- Stage-1 OK after retry: 0
- Stage-2 original-order failures: 0
- Stage-2 OK first attempt: 219
- Stage-2 OK after retry: 1

## Cost (side-by-side with step 0079 full-trace reader)

| Metric | Profile reader | Direct reader (0079) |
|---|---:|---:|
| Queries | 220 | 220 |
| Mean total chars / query | 46529.6 | 44589.2 |
| Median total chars / query | 38339.5 | (not stored in step 0079 summary) |
| Mean stage-1 chars | 12122.6 | — |
| Mean stage-2 chars | 34407.0 | — |
| Mean stage-2 evidence-only chars | 21527.0 | — |
| Mean wall seconds / query | 50.21 | 29.88 |
| Median wall seconds / query | 47.04 | 25.68 |
| Total wall seconds (sum) | 11047.12 | 6573.99 |

- Mean content-opened fraction (stage-2 evidence chars / step-0079 full packet chars): **0.5301**
- Median content-opened fraction: 0.5151
- Mean selected evidence operations / query: 14.17
- Mean groups available / query: 13.70

## Honest interpretation

On the complete TraceElephant population (n=220), the profile-guided reader achieves MAP=0.4553. Step-0079 full-trace direct reader MAP is 0.5020; stored Direct+AgentProf is 0.3255 and Direct-only is 0.2087.

Versus Direct reader (step 0079), the paired point difference is -0.0466 with 95% interval [-0.0831, -0.0116].
Versus Direct+AgentProf, the paired point difference is +0.1298 with 95% interval [+0.0797, +0.1791].
Versus Direct-only, the paired point difference is +0.2466 with 95% interval [+0.1891, +0.3041].

Mean content opened is 53.0% of the step-0079 full packet character volume (evidence-only stage-2 payload), with mean total two-stage packet characters 46530 versus step-0079 mean 44589.

This measures whether a once-built Agent+Evidence semantic path index, paired with a strong query-aware reader, can retain ranking quality while reading less source content than a full-trace reader. It does not evaluate a different grouping construction, a multi-query reuse setting beyond this single localization query per trajectory, or models other than the grok CLI reader used here and in step 0079.

This file reports the complete population run only. The ≤3-query harness validation is not a paper result.
