# Results: profile-guided reader v2 on TraceElephant (RQ2/RQ4)

## Scientific question

Does protocol v2 (width-annotated stage-1 skeleton + lean stage-2,
no skeleton re-send) retain ranking quality while reducing logical
input tokens below the full-trace reader and content opened ≤ step 0080?

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
- Step 0079 direct_reader: `/home/yunwei37/workspace/agentsight-research-semantic-flamegraph/docs/tmp/build-and-evaluate/step-0079-20260724T235753-0700/experiment-001/raw-results.json`
- Step 0080 profile_reader: `/home/yunwei37/workspace/agentsight-research-semantic-flamegraph/docs/tmp/build-and-evaluate/step-0080-20260725T004136-0700/experiment-001/raw-results.json`
- Step 0081 raw_action_reader: `/home/yunwei37/workspace/agentsight-research-semantic-flamegraph/docs/tmp/build-and-evaluate/step-0081-20260725T012438-0700/experiment-001/raw-results.json`
- **Frozen Agent+Evidence group mapping**: `/home/yunwei37/workspace/agentsight-research-semantic-flamegraph/.agentsight/experiments/rq2-canonical-tags-v2-current/trace/results/fixed-groups.jsonl`
  (key `source_preserving_agent`)
- Scoring: sklearn non-interpolated `average_precision_score`; arithmetic MAP
- Paired bootstrap: 10,000 trajectory-cluster resamples within strata; seeds {'local_only': 20260923, 'local_agentprof': 20260924, 'direct_reader': 20260925, 'profile_reader': 20260926, 'raw_action_reader': 20260927}
- Logical tokens: tiktoken `o200k_base` over stored packet JSON (indent=2, sort_keys)

## Protocol changes vs step 0080

### Change A — width-annotated stage 1

- Each group carries member operation count and additive mass.
- Additive measure used: **`operation_count`**.
- Frozen projection.jsonl and source packets expose no per-operation token mass field; pprof count units equal 1 per operation. Group additive mass is therefore member operation count only (ops=N).
- Format: `<path>  [ops=N]  members: ordinals=... ids=...` in `group_line` / `group_lines`.
- Stage-1 instruction unchanged: select up to 5 groups, ordered, strict JSON.

### Change B — lean stage 2

- Packet contains ONLY: task text + opened operations (`operation_id`, `ordinal`, `source_summary`).
- NO skeleton re-send; NO paths for unopened operations.
- Instruction: rank opened operation IDs; deterministic completion appends
  unopened ops in original trace order (identical to step 0080 completion).

## Registered targets (from 000-step-entry.md)

| Target | Threshold | Measured | Met? |
|---|---:|---:|:---:|
| MAP | ≥ 0.48 | 0.447170 | NO |
| Mean total logical tokens / query | < 12615 | 14830.4 | NO |
| Mean content-opened fraction | ≤ 53% | 0.5338 | NO |

- All three registered targets met: **NO**

## MAP

| Method | MAP |
|---|---:|
| Profile reader v2 (this experiment) | 0.447170 |
| Profile reader (step 0080) | 0.455333 |
| Raw-action reader (step 0081) | 0.465129 |
| Direct reader (step 0079) | 0.501967 |
| Direct+AgentProf (stored) | 0.325504 |
| Direct-only (stored) | 0.208713 |

## Paired differences (profile_reader_v2 − baseline)

| Baseline | Point ΔMAP | 95% interval | Nonpositive draws / 10000 |
|---|---:|---:|---:|
| Profile reader (step 0080) | -0.008163 | [-0.041613, +0.025051] | 6941 |
| Raw-action reader (step 0081) | -0.017958 | [-0.058174, +0.021966] | 8128 |
| Direct reader (step 0079) | -0.054796 | [-0.090485, -0.020990] | 9991 |
| Direct+AgentProf | +0.121666 | [+0.070589, +0.172032] | 0 |
| Direct-only | +0.238458 | [+0.183359, +0.294234] | 0 |

## Index-hit rate (step-0080 analysis-001 definition)

Hit = every target operation's group is among the ≤5 selected groups.

| Run | Hits / 220 | Rate |
|---|---:|---:|
| Profile reader v2 (this) | 159/220 | 0.7227 |
| Profile reader (step 0080) | 154/220 | 0.7000 |

## Failure tally

- Stage-1 largest-groups fallbacks: 0
- Stage-1 OK first attempt: 219
- Stage-1 OK after retry: 1
- Stage-2 original-order failures: 0
- Stage-2 OK first attempt: 220
- Stage-2 OK after retry: 0

## Cost — logical tokens (tiktoken o200k_base over stored packets)

| Metric | Profile reader v2 | Step 0080 two-stage | Step 0079 full-trace |
|---|---:|---:|---:|
| Mean total tokens / query | 14830.4 | 15991 | 12615 |
| Median total tokens / query | 12445.5 | — | — |
| Mean stage-1 tokens | 8648.1 | 4837 | — |
| Mean stage-2 tokens | 6182.3 | 11154 | — |

- Ratio vs step-0079 full-trace mean: **1.176x**
- Ratio vs step-0080 two-stage mean: **0.927x**

## Cost — characters / content opened (same definition as step 0080)

| Metric | Profile reader v2 | Direct reader (0079) |
|---|---:|---:|
| Queries | 220 | 220 |
| Mean total chars / query | 45675.9 | 44589.2 |
| Median total chars / query | 38352.0 | — |
| Mean stage-1 chars | 23662.1 | — |
| Mean stage-2 chars | 22013.8 | — |
| Mean stage-2 evidence-only chars | 21547.2 | — |
| Mean wall seconds / query | 44.95 | 29.88 |
| Median wall seconds / query | 41.27 | 25.68 |
| Total wall seconds (sum) | 9889.50 | 6573.99 |

- Mean content-opened fraction (stage-2 evidence chars / step-0079 full packet chars): **0.5338**
- Median content-opened fraction: 0.5349
- Step-0080 mean content-opened fraction (reference): 0.53
- Mean selected evidence operations / query: 14.38
- Mean groups available / query: 13.70

## Honest interpretation

On the complete TraceElephant population (n=220), profile-guided reader v2 achieves MAP=0.4472. Step-0080 profile reader MAP is 0.4553; step-0081 raw-action reader is 0.4651; step-0079 full-trace direct reader is 0.5020; stored Direct+AgentProf is 0.3255 and Direct-only is 0.2087.

Versus Profile reader (step 0080), the paired point difference is -0.0082 with 95% interval [-0.0416, +0.0251].
Versus Raw-action reader (step 0081), the paired point difference is -0.0180 with 95% interval [-0.0582, +0.0220].
Versus Direct reader (step 0079), the paired point difference is -0.0548 with 95% interval [-0.0905, -0.0210].
Versus Direct+AgentProf, the paired point difference is +0.1217 with 95% interval [+0.0706, +0.1720].
Versus Direct-only, the paired point difference is +0.2385 with 95% interval [+0.1834, +0.2942].

Mean logical input is 14830 tokens/query (stage-1 8648 + stage-2 6182) versus step-0079 full-trace 12615 and step-0080 two-stage 15991. Mean content opened is 53.4% of the step-0079 full packet character volume. Index-hit rate is 159/220 versus step-0080's 154/220.

Registered targets were not all met. Under the no-negative-results policy this remains an iteration step: findings feed protocol v3 rather than any paper claim.

This measures whether width annotations and a lean stage-2 packet improve the once-built Agent+Evidence index protocol relative to step 0080. It does not evaluate a different grouping construction, multi-query reuse, or models other than the grok CLI reader used in steps 0079–0081.

This file reports the complete population run only. The ≤3-query harness validation is not a paper result.
