# RQ2 Revision-0 Grouping Result Review

## Verdict

- **Evidence validity:** PASS / admitted for the grouping half.
- **Claim effect:** contradictory.
- **RQ:** unchanged — “Does profiler output correspond to real problems?”
- **Next scientific state:** finish the predeclared native TELBench rows, then
  close revision 0 and return to PROPOSE for claim revision 1 under the same RQ.

This report does not narrow or remove the multi-resolution semantic operation
stack contribution. It admits that the current leaf-ranking mechanism fails and
therefore requires a stronger mechanism and a new complete experiment.

## Independent Review History

The first independent full-grouping audit rejected the result because the
instance bootstrap held full-population group means fixed, the execution had
parsed label-bearing sources before its claimed boundary, and deterministic
training seeds were pooled as though they represented model variance. Those
issues were repaired and the complete grouping matrix was rerun.

A fresh reviewer then independently reconstructed development selection,
labels, point metrics, matched partitions, and all 1,000 bootstrap repetitions
without using the experiment scorer. It returned PASS. Across 240 method rows
and 600 matched rows, the maximum metric difference was zero.

## Execution Coverage

- Development selection: 5 tasks, 3 family-held-out folds, 3 deterministic
  checks, 540 complete selection cells.
- Selected only from development: mean aggregation, induced depth 2,
  `sql_role_action`, `explicit_action`, and `fixed_sequential_w10`.
- AgentRx: 73/73 public annotated trajectories, 3,265 operations, 73 critical
  failure steps; Tau 29 and Magentic-One 44.
- TELBench: 1,000/1,000 cases, 11,934 spans, 2,552 harmful spans.
- Confirmation: every deployable method, width/rarity/random/oracle ablations,
  and 100 matched partitions per family and deterministic check.
- Uncertainty: one 1,000-repetition trajectory/instance bootstrap for the
  deterministic ranker. The other fixed seeds verify determinism and generate
  independent matched partitions; they are not described as model variance.

## Leakage Boundary

A completed `prepare-full-visible` process projected official sources into
`full/visible-input/` and exited. The grouping process read only those label-free
records/questions while producing risk scores, Rust induction, all deployable
rankings, ablations, and matched partitions. Failure locations and TELBench
error labels entered only after these artifacts existed.

Precise AgentRx disclosure: official annotated-trajectory membership defined
the 73-trajectory evaluation set during projection. The projection did not read
or output failure locations. The paper and reports must not claim that the
projection never opened the ground-truth file.

## Primary Results

| Family | Prevalence | Induced AP | Work@25 | Groups@25 | Recall@30% work | Strongest baseline |
|---|---:|---:|---:|---:|---:|---|
| AgentRx | 0.02236 | 0.02584 | 0.20214 | 32 | 0.34247 | tag: AP 0.02834, work 0.14609, groups 1 |
| TELBench | 0.21384 | 0.21487 | 0.64563 | 82 | 0.19005 | session: AP 0.22342, work 0.23605, groups 268 |

Neither family reaches the predeclared absolute AP gain of 0.05 or 50% recall
within 30% work. Neither satisfies any relative Pareto branch.

Correct instance-bootstrap AP-minus-prevalence intervals:

- AgentRx: median 0.003399, 95% [-0.000349, 0.007981].
- TELBench: median 0.003329, 95% [-0.007183, 0.018036].

Matched-null work deltas (`matched - induced`) also fail in the required
direction:

- AgentRx: median -0.016539, 95% [-0.033851, 0.028047].
- TELBench: median -0.030711, 95% [-0.050827, 0.000224].

## Mechanism Evidence

TELBench width-only ordering dominates the current learned-risk leaf ordering:

- induced: AP 0.21487, work@25 0.64563, groups@25 82;
- width: AP 0.27730, work@25 0.37230, groups@25 1;
- rarity: AP 0.22753, work@25 0.64362, groups@25 132.

The experiment also flattened every full semantic path to its leaf key. It
therefore validly rejects the current label-free risk-ranked leaf mechanism but
does not test parent-to-child navigation, prefix scopes, or interactive
coarse-to-fine inspection. That missing mechanism cannot be repaired by wording;
it requires claim revision 1 and a new experiment.

## Disclosed Non-Blocking Deviations

- Results contain 100 matched partitions per deterministic check, 300 pooled;
  report both the per-check count and pooled count.
- SQL controls are separately executed/scored SQLite `GROUP BY` views, not the
  SQL `ROLLUP` keyword or an interactive rollup hierarchy.
- Secondary top-5, AgentRx exact-step, group-size distribution, and cold/warm
  timing results are not yet in the formal table. Raw rankings permit the first
  three to be computed; they cannot overturn the failed primary criteria.
- The native bare/DRIFT half remains outside this verdict until all 1,000 cases
  complete and fallback limitations are reviewed.

## Decision

Do not adjust thresholds or statistical definitions to rescue revision 0. On
native completion, classify revision 0 as a valid contradictory result. Then
use [the source-grounded mechanism search](claim-revision-01-mechanism-search.md)
to PROPOSE a coarse-to-fine semantic navigation mechanism, review its plan for
three to five rounds, and test it on fresh external confirmation data rather
than presenting retuning on AgentRx/TELBench as untouched confirmation.
