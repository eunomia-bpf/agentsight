# Results: hierarchical vs flat semantic skeleton (one reader family)

## Hypothesis (the review's "why hierarchy" question)

With the reader family held fixed, the HIERARCHICAL semantic skeleton
directs a reader to responsible operations at least as well as a FLAT
skeleton of the same leaf tags, while opening less source content — i.e.,
the nesting itself carries navigation value beyond the names.

## Verdict: SUPPORTED

## Population

- Workload: TraceElephant complete RQ2 collection
- Target-bearing queries scored: 220
- Operations: 5960

## Input provenance (read-only, frozen; reused from step 0080)

- Source-only packets: `/home/yunwei37/workspace/agentsight-research-semantic-flamegraph/.agentsight/experiments/rq2-a0-v1/full/trace/packets`
- Operation projections / stable IDs: `/home/yunwei37/workspace/agentsight-research-semantic-flamegraph/.agentsight/experiments/traceelephant-rq2-v1/operations/projection.jsonl`
- Annotated targets (mistake_step): `/home/yunwei37/workspace/agentsight-research-semantic-flamegraph/.agentsight/experiments/traceelephant-rq2-v1/scorer/targets.jsonl`
- Stored Direct-only / Direct+AgentProf per-query AP: `/home/yunwei37/workspace/agentsight-research-semantic-flamegraph/.agentsight/experiments/rq2-current-agent-local-first-v1/full/per-query.jsonl`
- Step 0079 direct_reader per-query AP / costs: `/home/yunwei37/workspace/agentsight-research-semantic-flamegraph/docs/tmp/build-and-evaluate/step-0079-20260724T235753-0700/experiment-001/raw-results.json`
- **Frozen Agent+Evidence group mapping**: `/home/yunwei37/workspace/agentsight-research-semantic-flamegraph/.agentsight/experiments/rq2-canonical-tags-v2-current/trace/results/fixed-groups.jsonl`
  (key `source_preserving_agent`; step-0072 source_preserving_agent paths)
- Leaf-tag vocabulary (arm F grouping key): 5 tags — blocked, failure, progress, success, unclear
- Scoring: sklearn non-interpolated `average_precision_score`; arithmetic MAP
- Paired bootstrap: 10,000 resamples of trajectory clusters within strata
  (H−F seed 20260989; content-delta seed 20260990)

## Arms (reader family held fixed)

- **Arm H (hierarchical)**: full source_preserving_agent path grouped by full path (step-0080 style).
- **Arm F (flat)**: leaf tag (last path component) only, parent paths stripped, grouped by leaf.
- Reader (BOTH arms): `opencode run --pure` from an empty jail, `stdin=/dev/null`, default model glm-5.2, no tools, one format retry, deterministic fallbacks. Same flags / same instruction text for both arms.

## MAP

| Arm / method | MAP |
|---|---:|
| **Arm H — hierarchical** | **0.425965** |
| **Arm F — flat (leaf tag)** | **0.366408** |
| Direct reader (step 0079, reference) | 0.501967 |
| Direct+AgentProf (stored, reference) | 0.325504 |
| Direct-only (stored, reference) | 0.208713 |

## Paired difference (H − F)

| Metric | Point Δ | 95% interval | Nonpositive draws / 10000 |
|---|---:|---:|---:|
| MAP (H − F) | +0.059556 | [+0.013879, +0.104702] | 55 |
| content_opened_fraction (H − F) | -0.242895 | [-0.274459, -0.210212] | 10000 |
| stage2_evidence_chars (H − F) | -11267.4 | [-13363.2, -9148.7] | 10000 |
| selected_evidence_ops (H − F) | -7.114 | [-8.523, -5.745] | 10000 |

## Index-hit rate (target operation inside a selected group)

| Arm | Index-hit rate | Hits / 220 | Mean groups | Median groups | Largest group (mean) |
|---|---:|---:|---:|---:|---:|
| H (hierarchical) | 0.6500 | 143 | 13.70 | 12.00 | 6.04 |
| F (flat) | 0.7455 | 164 | 2.34 | 2.00 | 17.21 |

## Content opened (stage-2 evidence chars / step-0079 full packet chars)

| Arm | Mean opened | Median opened | Mean selected evidence ops |
|---|---:|---:|---:|
| H (hierarchical) | 0.4910 | 0.4970 | 13.16 |
| F (flat) | 0.7339 | 0.9077 | 20.27 |

## Failure tally

| Tally | H | F |
|---|---:|---:|
| Stage-1 OK first attempt | 215 | 219 |
| Stage-1 OK after retry | 5 | 1 |
| Stage-1 largest-groups fallback | 0 | 0 |
| Stage-2 OK first attempt | 213 | 218 |
| Stage-2 OK after retry | 5 | 0 |
| Stage-2 original-order failures | 2 | 2 |

## Cost (per query)

| Metric | H | F | Direct reader (0079) |
|---|---:|---:|---:|
| Mean total chars | 44704.7 | 43161.3 | 44589.2 |
| Median total chars | 37039.0 | 34684.0 | — |
| Mean wall seconds | 65.22 | 51.01 | 29.88 |
| Median wall seconds | 53.05 | 42.95 | 25.68 |
| Mean prompt tokens (o200k) | 13624 | 13062 | — |

## Honest interpretation

On the complete TraceElephant population (n=220), with the opencode/glm-5.2 reader family held fixed for both arms:
- Hierarchical MAP = 0.4260; Flat MAP = 0.3664.
- Paired H − F ΔMAP = +0.0596, 95% interval [+0.0139, +0.1047], 55/10000 nonpositive draws.
- Mean content opened: H = 49.1%, F = 73.4% of the step-0079 full-trace packet volume.
- Index-hit rate: H = 65.0%, F = 74.5%.

**Verdict: SUPPORTED.**

Caveats: the flat arm's leaf tag is the operation outcome (success/progress/failure/blocked/unclear), so arm F groups by outcome only — a deliberately coarse flat projection of the same operations. This measures whether the hierarchical nesting carries navigation value beyond the leaf names for THIS reader family and workload. It does not evaluate other flat projections (e.g., a mid-depth prefix), other readers, or other workloads, and it is not pooled with the step-0080 grok-reader result.

This file reports the complete 220-query run. The 40-per-arm pilot is an operational gate (parse-failure rate < 10%), recorded in `execution-log.md`, and is not a paper result.
