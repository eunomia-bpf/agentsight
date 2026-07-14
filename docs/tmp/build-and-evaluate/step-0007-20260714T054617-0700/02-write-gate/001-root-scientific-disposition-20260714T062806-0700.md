# Root Scientific Disposition: Step 0007 RQ1 Evidence

## Decision

- Timestamp: 2026-07-14T06:28:06-07:00
- Disposition: accept the complete Step 0007 result as cumulative RQ1 evidence
- Narrative change: none
- Thesis change: none
- RQ change: none
- Contribution change: none

## Initial, previous, and chosen story

The Initial Narrative says agent observability needs profiling, not only
debugging, because developers must attribute cost, failures, safety effects,
and wasted work across many trajectories. Operations and operation stacks are
the two core abstractions. RQ1 asks whether semantic profiling improves
resource attribution.

The immediately previous paper already shows that declared semantic fields
separate cross-run system-effect responsibility better than tag-free or
session-only views, but that measurement alone does not independently establish
that each system effect belongs to the responsible agent activity.

The chosen story keeps the Initial Narrative unchanged and adds the missing
evidence link. R114 tests source-lineage correctness under concurrent controls;
current AgentProf then folds exactly the correctly attributed rows without
losing category mass. This makes the existing story more complete rather than
replacing it with an experiment-specific or hierarchy-centered narrative.

## Accepted paper interpretation

RQ1 is answered cumulatively by two distinct properties:

1. scoped operation-to-effect lineage connects real target activity to system
   effects while rejecting concurrent unrelated effects;
2. semantic operation stacks reorganize the correctly attributed effects
   across runs and measures while preserving their mass.

The full paper may state this positive answer. It must keep the fixed-suite and
known-category facts accurate, but those facts should not displace the larger
resource-attribution insight. The experiment does not require a new term,
mechanism, contribution, or RQ.

## Evidence admitted

- 20/20 target tasks completed.
- 20/20 concurrent controls observed.
- Scoped lineage: 1,520 TP, 0 FP, 54 FN.
- Precision 100.000%, recall 96.569%.
- 1,629 negative-control effects, zero joined.
- AgentProf: 1,520 selected rows to 1,520 samples and total mass.
- Exact category masses: dependency 121, edit 380, failure 39, read 723,
  test 257.
- Independent result review: PASS with zero mismatch.

## Rejected interpretations

- Do not say AgentProf inferred the manifest task categories.
- Do not say arbitrary causal attribution is solved for every agent.
- Do not say AgentSight 0.2.43 was evaluated.
- Do not turn process/tool scope or the replay adapter into a new abstraction.
- Do not narrow RQ1 to the R114 suite or make R114 the paper's thesis.

## Memory disposition

`docs/evaluation.md` now records RQ1 as an evidence-backed cumulative positive
answer and contains the admitted Step 0007 result and execution boundary.
`docs/idea-story.md` records Step 0007 only in the Current Frontier because no
idea, thesis, contribution, system direction, scope, or RQ changed. Adding a
new Narrative Evolution entry would falsely imply a story change.
