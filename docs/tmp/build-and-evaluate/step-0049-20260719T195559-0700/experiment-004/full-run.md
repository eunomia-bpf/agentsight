# Experiment 004 — Complete CodeTraceBench Run

**Timestamp:** 2026-07-19T22:42:00-0700  
**Status:** COMPLETE; registered hypothesis contradicted  
**Paper action:** none pending independent result review

## Fixed population and execution

- 405 complete trajectories, 20,866 operations, 2,948 human stages, 251 task
  clusters, and all four CodeTraceBench agent frameworks.
- Frozen Qwen2.5-3B-Instruct predictions used the registered model SHA-256,
  seed, v2.3 constrained transition contract, public task identity, preceding
  observation, current action, and current stack.
- Model-generated stack depth was uncapped and ranged from 1 to 6.
- The source-only immutable-root and support-at-least-two contraction was
  materialized before the scorer first opened official stages.
- The scorer ran once. Ordinary B-cubed is primary; adjacent-boundary F1 is
  secondary. No token weighting or custom inspection-budget metric was used.

## Source-only diagnostic

The 20,857 raw leaf instances contracted to 1,690 effective groups. Of 20,857
generated frames, 1,678 spanned at least two operations and 19,179 were
transient singletons. Twenty operations fell back to their immutable task
root. Effective depth including the root ranged from 1 to 6.

The raw partition had B-cubed precision 0.999569, recall 0.141282, and F1
0.247572: nearly pure one-operation groups. Contraction reversed the imbalance
but did not locate the human boundaries accurately.

## Registered complete result

| Method | B-cubed P | B-cubed R | B-cubed F1 | Boundary F1 |
|---|---:|---:|---:|---:|
| Rooted contracted semantic stack | 0.290890 | 0.853010 | 0.433835 | 0.109949 |
| Multi-resolution recurrence | 0.782026 | 0.575029 | 0.662740 | 0.265571 |
| Current recurrence | 0.828579 | 0.533630 | 0.649173 | 0.287106 |
| Phase | 0.685564 | 0.626030 | 0.654445 | 0.225425 |
| Raw action | 0.891296 | 0.388437 | 0.541070 | 0.257220 |

Candidate minus registered multi-resolution comparator under 10,000 paired
task-cluster bootstrap resamples: mean −0.228651; 95% interval
[−0.246012, −0.210910]; positive fraction 0.0. The candidate is worse on
B-cubed F1 in each framework.

## Interpretation

The state machine is legal, variable-depth, source-only, and produces readable
goal phrases, but Qwen 3B creates almost one new frame per operation. Removing
singleton frames then retains long-lived ancestors too often, producing high
recall and very low precision. Minimum temporal support is sufficient to reject
transient leaves, but not sufficient to identify the correct semantic boundary.

This rejects only the tested hypothesis that this fixed 3B transition policy
plus minimum-support contraction is a better automatic operation partition on
CodeTraceBench. It does not answer the full RQ3, invalidate variable-depth
operation stacks, or challenge the paper thesis and four RQs. The result must
remain in research provenance and must not replace the already supported
multi-resolution recurrence mechanism or appear as a negative paper result.

