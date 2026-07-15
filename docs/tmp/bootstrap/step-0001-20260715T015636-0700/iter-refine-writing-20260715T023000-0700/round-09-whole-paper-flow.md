# Round 09: Whole-Paper Flow

Reviewer mode: independent fresh read-only flow review

## Reviewer Findings

### Must-fix

1. Design did not name the frozen core-view combinations or describe the
   association-state matrix/detail view introduced by RQ3.
2. RQ3's condition sentence was grammatically broken, and its task map was
   separated from the RQ and then repeated.
3. Discussion imposed a linear RQ chain even though RQ4 independently bounds
   scale and only RQ2/RQ3 depend on RQ1 association validity.

### Should-fix

The reviewer identified an RQ term introduced too early in the Introduction, a
status-first system paragraph, a weak Background-to-Motivation bridge, repeated
review questions in Motivation, missing goals-to-pipeline and walkthrough-to-
contract transitions, mixed projection/coordination roles, and repetition
between Limitations and Discussion.

### Consider

The reviewer proposed an Implementation-to-Evaluation bridge, layer-oriented
Related Work openers, and an uncertainty-preserving Conclusion.

## Root Decisions And Applied Fixes

- Added the four task-facing core combinations in Design and an explicit
  association-state matrix/detail encoding for eligibility, candidates,
  unmatched state, confidence, and granularity.
- Moved the task map into RQ3, repaired the four-condition sentence, and kept
  metrics after the tasks.
- Recast the RQs as a shared-foundation argument in which RQ1 gates RQ2/RQ3 and
  RQ4 independently bounds scale.
- Applied every Should-fix bridge and role correction. The Introduction now
  describes the planned extension before status, Motivation turns repeated
  questions into a cross-layer consequence, Design formalizes the walkthrough,
  and Coordinated Interaction contains only propagation mechanics.
- Added the implementation/evaluation bridge, layer-oriented Related Work
  openers, and the uncertainty-preserving Conclusion.

## Meaning And Evidence Check

The core-view roadmap makes the pre-run contract more specific without claiming
that the views exist. Moving text did not change the four tasks, conditions, or
metrics. No evidence scope, result placeholder, association semantics, or RQ
dependency changed beyond correcting RQ4's already-stated independence.

## Verification

`make -C docs/paper` completed successfully and produced a six-page PDF. The
cumulative snapshot diff contains 452 insertions and 163 deletions. A manual
trace confirmed that each RQ3 task now names a Design view combination and that
Discussion matches the Evaluation dependency structure.
