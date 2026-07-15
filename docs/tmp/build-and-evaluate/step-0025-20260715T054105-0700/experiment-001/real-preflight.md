# REAL PREFLIGHT

**Completed:** 2026-07-15T06:40:00-07:00  
**State:** **VALID — GO**  
**Scientific verdict:** not tested

## OSWorld-Human Fold 0

The approved evaluator completed the entire existing fold 0: 45 held-out
sessions, 521 operations, and 476 adjacent decisions. Training and target
sessions remain disjoint. Every prediction and assignment appears once, scorer
fields remain excluded from construction, all scores/calibrations are finite,
and the resulting AgentProf profile conserves all 521 units.

The refinement suppressed 94 Step 0024 threshold boundaries, added zero global-
current boundaries, produced only a subset of threshold decisions, and changed
no same-action decision. Displayed accuracy values are preflight diagnostics and
do not test or select the hypothesis.

## CodeTraceBench First Target

The approved release path completed the first sorted target end to end: one
complete 47-operation trajectory, 46 adjacent decisions, and all 10 official
stages loaded only after prediction. The Rust reference contains the complete
2,229 disjoint sessions and 87,703 operations. Its target input contains only
unit weight, `session`, and `action`.

The refinement suppressed 7 Step 0024 threshold boundaries, added no global-
current boundary, preserves every same-action decision, assigns every operation
once, and conserves all 47 units. The reported accuracy values are diagnostics;
the summary explicitly records `tested_hypothesis: not tested`.

## Decision

Both real paths are executable and satisfy the approved source, isolation,
coverage, subset, same-action, and conservation contracts. No code, plan,
candidate, metric, or verdict changed after preflight. GO: execute all five
OSWorld-Human folds, exact Rust/Python equivalence, and all 405 CodeTraceBench
targets once.

Retained summaries:

- `.agentsight/experiments/rq3-contextual-recurrence-v1/preflight/summary.json`
- `.agentsight/experiments/rq3-contextual-recurrence-codetracebench-v1/preflight/summary.json`
