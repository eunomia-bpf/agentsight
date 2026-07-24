# Step 0073 Entry — RQ3 Fixed-Instruction Follow-On

**Timestamp:** 2026-07-23T20:18:12-07:00
**Parent:** Step 0072 outer audit
**Outer gate:** EXPERIMENT
**Research question:** RQ3 — How accurately do automatic backends recover
operation structure?

## Objective

Test whether the current automatic Agent A2 structure result persists outside
the 41 long-horizon sessions used to design and visually inspect the product
case. This step does not change the thesis, story, RQ, constructor, names,
marks, benchmark, or metrics.

## Entry state and provenance

- Branch:
  `research/semantic-flamegraph-artifacts-v2`.
- Parent commit:
  `6d343588b`.
- The complete author-intent log and complete idea-story invariants were
  rechecked at entry.
- The fixed 41-session collection contains 5,750 operations.
- The already generated follow-on collection contains the other 364 sessions,
  15,116 operations, 238 task clusters, and four frameworks.
- The follow-on packets used the same source-only collection question and
  annotation instruction as the first 41 sessions. Their instruction explicitly
  forbade official stages, scores, outcomes, recurrence outputs, the 41-session
  annotations, and other workers' annotations.
- The current accepted A2 output is
  `.agentsight/experiments/a2-canonical-v1/`; no annotation or prediction will
  be regenerated.

## Why this node

The complete 405-session result is positive, but it combines the initial
41-session product-design subset with 364 later independent batches. Reporting
only the union obscures whether the gain comes mainly from the initial subset.
A manifest-defined post-aggregate follow-on-only analysis is the smallest experiment that
directly tests that alternative explanation without changing the method or
opening another benchmark.

This is not called a strict untouched test set: the full CodeTrace family and
its aggregate result have already been observed. It is fixed-instruction,
post-design follow-on evidence.

## Completion condition

The node completes after plan review, exact subset/join preflight, full
follow-on scoring with standard B-cubed and exact-boundary metrics, paired
task-cluster uncertainty, independent raw-row reconstruction, targeted paper
integration, and whole-paper review.
