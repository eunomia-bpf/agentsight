# Full Result Report: RQ2 Cumulative Baseline Synthesis

- Completed: `2026-07-14T10:09:00-07:00`
- Run status: **VALID / COMPLETE**
- Tested cumulative hypothesis: **SUPPORTED under the approved cumulative rule
  as a retrospective synthesis, not a new confirmatory test**
- Original workload verdicts: **unchanged; all three remain INCONCLUSIVE for
  their original conjunctive tested hypotheses**
- New data/model/metric/resample/code: **none**

## Inputs and completion

The full read-only workflow consumed exactly the three approved full summaries
and their corresponding reviewed reports:

1. `docs/visexp/out/agentprocessbench-rq2/full/summary.json` and
   `docs/tmp/cycle-0002-20260712T201943-0700/01-experiment-gate/loop-rq2-agentprocessbench/full-execution-report.md`;
2. `docs/tmp/cycle-0003-20260713T121925-0700/01-experiment-gate/loop-001-rq2-hintbench/results/full/summary.json`
   and
   `docs/tmp/cycle-0003-20260713T121925-0700/01-experiment-gate/loop-001-rq2-hintbench/full-result-review.md`;
3. `.agentsight/experiments/traceelephant-rq2-v1/metrics/summary-full.json`
   and
   `docs/tmp/build-and-evaluate/step-0004-20260713T172452-0700/01-experiment-gate/loop-001-rq2-traceelephant/008-independent-result-review-20260714T011915-0700.md`.

All three summaries report valid and complete execution. Every planned method,
baseline/control role, original verdict, primary point, uncertainty result,
group count, and descriptive TraceElephant curve point was extracted. Direct
comparison with the reviewed reports found zero unexplained mismatch.

## AgentProcessBench

The full run contains 1,000 trajectories, 8,509 human-labeled assistant steps,
and four equally weighted task families.

| View | Role | Groups | Macro AP | Work@50 |
|---|---|---:|---:|---:|
| Flat | lower-bound control | 1 | 0.324684 | 1.000000 |
| Raw action | main baseline | 259 | 0.556133 | 0.329920 |
| AgentProf semantic | proposed | 419 | **0.587655** | **0.313600** |
| Session | structural reference | 1,000 | 0.598611 | 0.273997 |
| Ungrouped step risk | diagnostic reference | 8,509 | 0.776683 | 0.194959 |

Semantic-minus-raw AP is `+0.031522`, with paired 95% interval
`[+0.015138, +0.053514]`. Semantic AP is higher than raw action in BFCL, GAIA,
HotpotQA, and tau-bench. A 200-replicate within-raw-action matched subgroup-size
permutation gives `p=0.009950` with exact size preservation, so this positive
component is semantic-specific rather than a consequence of merely producing
419 instead of 259 groups.

This is the synthesis's direct semantic-specific result: the matched control
holds each raw-action leaf and semantic subgroup size fixed.

Raw-minus-semantic Work@50 is `+0.016320`, but its paired interval
`[-0.022550, +0.074214]` crosses zero. Session and ungrouped step risk attain
stronger macro points with 2.39x and 20.31x as many groups as the semantic
profile; they remain visible diagnostic references, not claimed losses.

**Original workload verdict: INCONCLUSIVE.** The prospective AP component is
supported and semantic-specific, while the co-primary inspection-work
condition is unresolved.

## HINTBench

The full test snapshot contains 536 trajectories and 12,877 scored steps.
Lower Work@80 is better.

| View | Role | Groups | Work@80 | AgentProf-minus-view paired 95% interval |
|---|---|---:|---:|---:|
| AgentProf | proposed | 2,294 | **0.415702** | -- |
| Raw action | main baseline | 412 | 0.462918 | `[-0.293709, +0.008566]` |
| Native sequence | structural reference | 12,877 | 0.579327 | `[-0.222393, -0.101682]` |
| Independent step | structural reference | 12,877 | 1.000000 | `[-0.629675, -0.509304]` |
| Session | structural reference | 536 | 0.591442 | `[-0.225393, -0.104603]` |
| Exact reconstruction | identity control | 2,294 | 0.415702 | exact identity |
| Width only | control | 2,294 | 0.894308 | not a main comparison |

AgentProf is prospectively better than native sequence, independent-step, and
session organization because all three paired intervals lie below zero. Its
point estimate is also better than raw action, but that interval crosses zero
by `0.008566`. The exact reconstruction row is an implementation identity
control for the same constructed profile, not independent semantic evidence.

This positive component belongs to the complete existing HINTBench method:
the semantic profile, validation-selected prefix policy, and fixed scorer
together. It does not isolate the hierarchy as the sole cause.

**Original workload verdict: INCONCLUSIVE.** The approved conjunct required
the raw-action interval as well as the other structural comparisons to exclude
zero. The positive primary components against native, independent-step, and
session remain valid evidence; they do not relabel the full original verdict.

## TraceElephant

The full run contains all 220 released real failures and 5,960 steps. Lower
work and higher recall are better.

| View | Role | Groups | Work@80 primary | Work@50 descriptive | Recall@20 descriptive |
|---|---|---:|---:|---:|---:|
| AgentProf | proposed | 37 | 1.000000 | **0.195470** | **0.525687** |
| Raw action | main baseline | 13 | 0.719128 | 0.466443 | 0.237858 |
| Source native | structural reference | 17 | 1.000000 | 0.577517 | 0.147412 |
| Independent-step signal | structural reference | 2 | 1.000000 | 1.000000 | 0.173920 |
| Session | structural reference | 11 | 1.000000 | 0.568289 | 0.060657 |
| Flat | lower-bound control | 1 | 1.000000 | 1.000000 | 0.000000 |
| Width only | control | 61 | 0.676846 | 0.396477 | 0.309095 |
| Oracle | diagnostic upper bound | 2 | 0.036913 | 0.036913 | 1.000000 |

At the prospective 80%-recall point, AgentProf-minus-raw work is `+0.280872`
with paired interval `[-0.018950, +0.458639]`; the interval crosses zero, and
all 200 matched permutations require no more work than the actual assignment
(`p=1.0`). The primary result is therefore not positive, but its uncertainty
also does not establish a reliable contradiction.

The Work@50 and Recall@20 columns expose a real early-curve region in which the
semantic view is ahead of every non-oracle row shown. They are descriptive and
cannot change the original primary verdict.

**Original workload verdict: INCONCLUSIVE.** The large final semantic score
tier removes the early advantage at high recall.

## Approved cumulative rule

The rule is evaluated without averaging AP, Work@80, Work@50, or Recall@20:

1. **Positive prospective primary components in at least two independent
   workloads:** PASS. AgentProcessBench supplies positive AP; HINTBench supplies
   positive Work@80 comparisons against native, independent-step, and session.
2. **At least one semantic-specific matched/null positive:** PASS.
   AgentProcessBench passes the matched subgroup-size permutation and its AP
   interval excludes zero.
3. **No originally supported primary contradiction:** PASS. TraceElephant's
   adverse Work@80 point and the unresolved HINTBench raw comparison have
   intervals crossing zero; neither is a supported contradiction.

**Retrospective cumulative synthesis: SUPPORTING.** Under the approved rule,
existing target-blind semantic
profiles add problem concentration beyond structural organization on two
independent prospective evidence components, with the strongest
semantic-specific proof on AgentProcessBench. This does not mean that all three
original experiments passed, that semantic profiles dominate every structural
view, that the post-result cumulative rule is a new confirmatory test, or that
high-recall behavior is uniform.

## Result-review return fields

- run status: **valid / complete**
- tested hypothesis: **supported under the approved cumulative rule as a
  retrospective synthesis**
- research value: **supporting synthesis of existing evidence; no new
  independent observation or confirmatory test claimed**
- paper impact: **existing RQ2 evidence synthesis and reporting correction;
  not additional evidence and not a direct thesis challenge**
- next paper decision: **return to WRITE with one compact full-baseline RQ2
  presentation that preserves original verdicts and marks TraceElephant's
  early region descriptive; do not start a new benchmark/model/metric/human
  experiment before that presentation is reviewed**

## Remaining uncertainty

The synthesis does not show a downstream agent intervention or analyst-time
outcome, and it does not prove semantic dominance at every recall level. Those
are separate scientific questions. The present result answers the selected
reuse question completely and identifies no need to rerun or retune the three
completed workloads.
