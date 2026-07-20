# Implementation Review — Three-Transition Well-Nested Task Stack

## Scope

An independent read-only reviewer explicitly applied
`research-experiment-design` to the approved plan, plan review, and
`script/rq3_well_nested_task_stack_eval.py`. The review checked the transition
language, state application, exact-leaf invariant, request/cache isolation,
operation coverage, standard scorer, and registered decision rule. It did not
edit any file.

## Round 1 — Revise

Two local must-fix issues were found:

1. The initial implementation treated an empty subtask suffix as having no
   active leaf, so `push(root_label)` would not become `stay`. This incompletely
   carried forward the approved exact-leaf invariant, under which the immutable
   root is the active leaf when no subtask is open.
2. The supported condition redundantly required both a positive point estimate
   and a wholly positive paired interval. The approved plan made the paired
   B-cubed interval the only scientific outcome criterion after coverage.

Both issues were corrected without changing the prompt, workload, model,
metrics, or experiment scope. `apply_transition` now receives the recorded root
label explicitly, and support is determined only by the registered interval.

Direct behavior checks confirmed that a root-equal push preserves the root and
does not increment the frame counter, while a legal pop removes exactly one
leaf. The complete preflight cache replayed without request or state drift.

## Round 2 — Approve

The reviewer returned **APPROVE** with zero remaining must-fix:

- the grammar and execution expose only `stay`, `push-one`, and `pop-one`;
- root pop is illegal and a pop can never target an arbitrary ancestor;
- exact same-leaf push, including a root-equal push, becomes `stay`;
- each source-native turn applies one transition and all operations in that
  turn receive the resulting complete path exactly once;
- the cache binds the algorithm, source archive, adapter, model artifact,
  system prompt, grammar, seed, visible prompt, and causally reconstructed
  stack;
- inference never opens human stages or recurrence assignments;
- scoring correctly maps the candidate, Step 0056, and recurrence columns and
  reuses ordinary B-cubed, adjacent-boundary F1, exact-span F1, and the fixed
  10,000-resample task-cluster bootstrap; and
- there is no replace, target depth, depth cap, threshold, contraction,
  post-processing rule, or hidden extra decision gate.

The inference implementation was therefore admitted to the complete run
unchanged.

## Post-Run Scorer Correction

Outer audit later found one scorer-contract defect that neither implementation
round had detected. The approved plan defines an occurrence as a maximal
contiguous run of one exact visible path, while the first scorer keyed only by
`session::path` and merged non-contiguous revisits. This did not affect model
inference or stack transitions.

The scorer now walks each session in step order and creates a new candidate and
Step 0056 occurrence ID whenever the corresponding visible path changes. It
retains the raw visible paths for audit. A fresh independent result review
reconstructed all 5,761 candidate and 6,264 Step 0056 contiguous occurrences,
recalculated the standard metrics and both 10,000-draw bootstraps, and returned
**APPROVE — 0 must-fix**. The registered disposition remains
`inconclusive-not-adopted`.
