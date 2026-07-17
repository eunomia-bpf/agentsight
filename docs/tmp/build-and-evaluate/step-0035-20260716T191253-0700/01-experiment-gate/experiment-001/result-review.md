# Independent Full-Result Review

**Completed:** 2026-07-16T20:45:00-07:00

**State:** `EXPERIMENT_GATE / RESULT REVIEW`

**Verdict:** **PASS**

This verdict accepts the completed experiment result. It is not a verdict that
the whole paper is submission-ready.

## Review Method

A fresh read-only reviewer followed `research-experiment-design` result-review
discipline and the complete-paper claim boundaries in `iter-review-critique`.
It did not invoke the experiment scorer. It independently joined and recomputed
the result from:

1. the 20,866 records in the full run's `operation-usage.jsonl`;
2. the original Step 0024 operation assignments; and
3. the CodeTraceBench target operations and official manifest stages.

The review found exact `(session, step_id)` agreement and no drift in official
stage, recurrence assignment, framework identity, or raw-action key. It
independently recomputed ordinary and token-weighted B-cubed, all three
multi-operation allocations, framework effects, and the 10,000-replicate paired
task-cluster bootstrap.

## Independent Findings

- **Run status:** `VALID`.
- **Tested hypothesis:** `SUPPORTED`.
- **Research value:** `SUPPORTING`; strong evidence for the bounded RQ1
  comparison, but not untouched independent confirmation because the target
  population previously contributed to current-constructor selection.
- **Paper impact:** additional independent-target RQ1 evidence plus a clear
  mechanism boundary.
- **Next gate:** `WRITE_GATE`.
- **Further experiment decision:** no rerun, new benchmark, or new algorithm is
  required before writing this result.

The independently reconstructed ordinary recurrence-minus-raw-action-key
B-cubed F1 effect is `+0.108103`, with 95% task-cluster-bootstrap interval
`[+0.087091, +0.129132]`. The independently reconstructed token-weighted effects
are `+0.084574`, `+0.075910`, and `+0.075671` for equal, first, and last
allocation. All validity and conservation checks pass.

## Authorized Paper Claim

> On the complete pre-existing population of 405 source-valid failed
> CodeTraceBench trajectories, the current recurrence operation stack improves
> agreement with author-annotated stages over a matched contiguous
> raw-action-key view from 0.541 to 0.649 ordinary B-cubed F1, a gain of 0.108
> with a task-cluster-bootstrap 95% confidence interval of [0.087, 0.129]. The
> direction remains positive when mapped operation-producing token mass is
> allocated equally, to the first operation, or to the last operation of a
> multi-operation response, with weighted gains of 0.076--0.085.

The paper must immediately preserve the following scope:

> This is post-hoc evidence on the population previously used to select the
> current constructor, not untouched cross-family confirmation. A phase-only
> view attains a statistically indistinguishable 0.654 B-cubed F1, so the result
> supports semantic stage-aligned attribution over raw action identity, not
> recurrence's dominance over every semantic view.

## Claims Not Authorized

The result does not authorize statements that recurrence universally beats
phase-only, that recurrence is the best possible profiling hierarchy, that the
experiment is an unseen independent algorithm test, that 494.9 million tokens
represent every model call in the released trajectories, that this experiment
alone answers every resource and system in RQ1, or that recurrence is the only
possible cause of the improvement.

## Transition

Enter WRITE without altering the fixed thesis, four RQs, paper story, or
current algorithm. Replace the circular prompt-tag mixedness result as the main
RQ1 semantic-correctness evidence with the standard B-cubed comparison; retain
source fidelity and multi-resolution/multi-weight results. Show the phase-only
row and its non-dominance boundary rather than hiding it. After writing, run a
complete-paper REVIEW.
