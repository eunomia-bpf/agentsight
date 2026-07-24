# Step 0076 entry: matched RQ1 attribution control

Timestamp: 2026-07-23T22:47:18-07:00
Outer gate: EXPERIMENT
Branch at entry: `research/semantic-flamegraph-artifacts-v2`
Commit at entry: `6b02d65f42597fb16b71c5d3278baa277952e139`

## Why this step exists

RQ2, RQ3, and RQ4 already have complete quantitative evaluations. RQ1 has a
real three-run Git deployment case and exact operation/token attribution, but
the paper has not yet materialized the two organization controls on the same
489 operations. This step adds only that missing matched comparison. It does
not change the paper thesis, RQ wording, case population, operation
annotations, or benchmark scope.

## Fixed research question

> RQ1: Does semantic profiling improve resource attribution?

This step is a post-hoc explanatory projection narrower than the RQ:

> On the three existing real Git deployment executions, project the fixed
> candidate-defined SSH-authentication members into three matched
> organizations and show exactly which distinction the accepted semantic
> operation path makes visible relative to source identity and generic action
> organization.

Because the responsibility was discovered in the prior semantic case, this
step is not an independent superiority or accuracy test. It does not claim
that semantic profiling dominates every trace interface or that the observed
resource ratio generalizes beyond this case.
