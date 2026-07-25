# Results: raw-action skeleton control on TraceElephant (RQ2)

## Scientific question

Holding the two-stage profile-guided reading protocol of step 0080 fixed,
does replacing the semantic operation paths in the skeleton with raw action
labels degrade attention concentration (lower MAP and/or more source content
opened)? This isolates whether semantic naming itself — not grouping plus
drilldown in general — directs a strong reader's attention.

## Population

- Workload: TraceElephant complete RQ2 collection
- Trajectories / target-bearing queries scored: 220
- Operations: 5960
- Zero-positive trajectories: 0 (excluded from MAP)

## Raw-action identity provenance (frozen, step-0072)

Step 0072 Direct+Raw+Evidence (`local_raw_evidence`) on TraceElephant does
**not** group by `projection.raw_fields.raw_action` alone. It reads the
composite raw leaf from the frozen method index and builds the
information-matched path used as the group identity:

- **Raw identity source file:** `/home/yunwei37/workspace/agentsight-research-semantic-flamegraph/.agentsight/experiments/traceelephant-rq2-v1/profiles/method-index.json`
- **Raw identity field:** `methods["raw"]["operation_leaves"]`
- **Join:** zip(projection.jsonl file order, operation_leaves) → operation_id
- **Evidence suffix source:** `/home/yunwei37/workspace/agentsight-research-semantic-flamegraph/.agentsight/experiments/rq2-canonical-tags-v2-current/trace/results/fixed-groups.jsonl`
  — fixed-groups.jsonl groups[source_preserving_agent] after automatic_agent prefix (exactly 3 frames: source-kind, source-call/tool, outcome)
- **Path construction:** (task_family.casefold(), 'raw:' + leaf.casefold(), *source_suffix) — identical to script/rq2_current_agent_local_first.py construct_scores for local_raw_evidence / raw_source_evidence
- **Not used as the identity:** projection.raw_fields.raw_action alone is NOT the step-0072 TraceElephant raw identity; the frozen leaf is the composite encoded system;component;raw_action string from method-index
- **Step-0072 script:** `script/rq2_current_agent_local_first.py`
- **Step-0072 condition key:** `local_raw_evidence`
- Unique raw leaves across population: 143

## Other input provenance (read-only, frozen)

- Source-only packets: `/home/yunwei37/workspace/agentsight-research-semantic-flamegraph/.agentsight/experiments/rq2-a0-v1/full/trace/packets`
- Operation projections / stable IDs: `/home/yunwei37/workspace/agentsight-research-semantic-flamegraph/.agentsight/experiments/traceelephant-rq2-v1/operations/projection.jsonl`
- Annotated targets (mistake_step): `/home/yunwei37/workspace/agentsight-research-semantic-flamegraph/.agentsight/experiments/traceelephant-rq2-v1/scorer/targets.jsonl`
- Stored Direct-only / Direct+AgentProf per-query AP: `/home/yunwei37/workspace/agentsight-research-semantic-flamegraph/.agentsight/experiments/rq2-current-agent-local-first-v1/full/per-query.jsonl`
  (Direct-only = `local_only`, Direct+AgentProf = `local_agentprof`)
- Step 0079 direct_reader per-query AP / costs: `/home/yunwei37/workspace/agentsight-research-semantic-flamegraph/docs/tmp/build-and-evaluate/step-0079-20260724T235753-0700/experiment-001/raw-results.json`
- Step 0080 profile_reader per-query AP: `/home/yunwei37/workspace/agentsight-research-semantic-flamegraph/docs/tmp/build-and-evaluate/step-0080-20260725T004136-0700/experiment-001/raw-results.json`
- Scoring: sklearn non-interpolated `average_precision_score`; arithmetic MAP
- Paired bootstrap: 10,000 resamples of trajectory clusters within strata; seeds {'local_only': 20260923, 'local_agentprof': 20260924, 'direct_reader': 20260925, 'profile_reader': 20260926}

## Protocol

- Stage 1: profile skeleton only (operation_id, ordinal, raw-action path), grouped by full path; select ≤5 groups.
- Stage 2: same skeleton + `source_summary` for members of selected groups only; rank operation IDs.
- Reader: grok CLI, `--output-format plain --max-turns 3 --tools '' --no-subagents --verbatim`.
- Fallbacks: stage-1 fail → largest 5 groups; stage-2 fail → original-order ranking.
- Manipulated variable only: group path = step-0072 information-matched raw+evidence path instead of source_preserving_agent.

## Grouping structure (raw-action vs step 0080 semantic)

- Mean raw-action groups / trajectory: **9.82**
- Median raw-action groups / trajectory: 9.0
- Mean size of largest raw-action group / trajectory: 9.24
- Median size of largest raw-action group / trajectory: 7.0
- Max largest-group size (any trajectory): 77
- Step 0080 mean semantic groups / trajectory (reported): **13.70**

## MAP

| Method | MAP |
|---|---:|
| Raw-action reader (this experiment) | 0.465129 |
| Profile reader (step 0080) | 0.455333 |
| Direct reader (step 0079) | 0.501967 |
| Direct+AgentProf (stored) | 0.325504 |
| Direct-only (stored) | 0.208713 |

## Paired differences (raw_action_reader − baseline)

| Baseline | Point ΔMAP | 95% interval | Nonpositive draws / 10000 |
|---|---:|---:|---:|
| Profile reader (step 0080) | +0.009795 | [-0.020767, +0.042417] | 2822 |
| Direct reader (step 0079) | -0.036838 | [-0.070317, -0.003739] | 9850 |
| Direct+AgentProf | +0.139624 | [+0.092003, +0.187928] | 0 |
| Direct-only | +0.256416 | [+0.199979, +0.312434] | 0 |

## Failure tally

- Stage-1 largest-groups fallbacks: 0
- Stage-1 OK first attempt: 220
- Stage-1 OK after retry: 0
- Stage-2 original-order failures: 0
- Stage-2 OK first attempt: 219
- Stage-2 OK after retry: 1

## Cost (side-by-side with step 0079 full-trace reader)

| Metric | Raw-action reader | Direct reader (0079) |
|---|---:|---:|
| Queries | 220 | 220 |
| Mean total chars / query | 53401.0 | 44589.2 |
| Median total chars / query | 43297.0 | nan |
| Mean stage-1 chars | 13335.1 | — |
| Mean stage-2 chars | 40065.9 | — |
| Mean stage-2 evidence-only chars | 25716.1 | — |
| Mean wall seconds / query | 55.94 | 29.88 |
| Median wall seconds / query | 50.57 | 25.68 |
| Total wall seconds (sum) | 12307.26 | 6573.99 |

- Mean content-opened fraction (stage-2 evidence chars / step-0079 full packet chars): **0.6501**
- Median content-opened fraction: 0.6628
- Mean selected evidence operations / query: 16.96
- Mean groups available / query: 9.82

### Cost side-by-side with step 0080 profile reader

- Step 0080 mean content-opened fraction: 0.5301
- Step 0080 mean selected evidence ops: 14.17
- Step 0080 mean groups available: 13.70
- Step 0080 mean total chars / query: 46529.6

## Honest interpretation

On the complete TraceElephant population (n=220), the raw-action skeleton reader achieves MAP=0.4651. Step-0080 semantic profile reader MAP is 0.4553; step-0079 full-trace direct reader MAP is 0.5020; stored Direct+AgentProf is 0.3255 and Direct-only is 0.2087.

Versus Profile reader (step 0080), the paired point difference is +0.0098 with 95% interval [-0.0208, +0.0424].
Versus Direct reader (step 0079), the paired point difference is -0.0368 with 95% interval [-0.0703, -0.0037].
Versus Direct+AgentProf, the paired point difference is +0.1396 with 95% interval [+0.0920, +0.1879].
Versus Direct-only, the paired point difference is +0.2564 with 95% interval [+0.2000, +0.3124].

Mean content opened is 65.0% of the step-0079 full packet character volume (evidence-only stage-2 payload), with mean total two-stage packet characters 53401 versus step-0079 mean 44589.

Mean raw-action groups per trajectory is 9.82 (median 9.0), versus step 0080's 13.70 mean semantic groups. Mean largest raw-action group size is 9.24.

This measures whether replacing the semantic operation path with the frozen step-0072 information-matched raw-action path (same grouping + drilldown protocol) degrades a strong reader's attention concentration. It does not evaluate a different selection budget, a multi-query reuse setting, or models other than the grok CLI reader used in steps 0079–0080.

This file reports the complete population run only. The ≤3-query harness validation is not a paper result.
