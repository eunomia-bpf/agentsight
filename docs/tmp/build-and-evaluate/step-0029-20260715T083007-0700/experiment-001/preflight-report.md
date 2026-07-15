# REAL PREFLIGHT Report

**Executed:** 2026-07-15T14:43:00-07:00
**Status:** **PASS**
**Attempts used:** 1 of at most 2 for each registered path
**Scientific interpretation:** prohibited; dependency/executability only

## Approved Scope

The implementation entered REAL PREFLIGHT only after the independent
implementation review's focused follow-up returned **APPROVE** with zero
must-fix findings. The registered algorithm, inputs, folds, target selection,
metrics, baselines, and promotion rule were unchanged.

## OSWorld-Human Fold 0

The approved preflight command completed on the exact existing fold-0 target:

- 45 target sessions;
- 521 target operations;
- the other four established folds as the label-free reference;
- Python segments and assignments persisted before scorer loading;
- the release Rust profile persisted before scorer loading;
- exact ordered-rule, segment, per-session assignment, and mass equivalence;
- the established scorer loaded only after prediction; and
- final run status `valid` with the explicit verdict `preflight-only; no
  scientific verdict`.

Raw output is under
`.agentsight/experiments/rq3-grammar-recurrence-v1/preflight/`.

## CodeTraceBench First Target

The approved preflight command completed on the lexicographically first exact
target:

- the complete target-disjoint reference of 2,229 sessions and 87,703
  operations;
- one complete target session with 47 operations;
- uncapped grammar construction and creation-order transfer;
- Python segments and all per-operation assignments persisted before official
  stages were loaded;
- exact ordered-rule, segment, per-session assignment, and mass equivalence;
- the official verified manifest loaded only after prediction; and
- final run status `valid` with the explicit verdict `preflight-only; no
  scientific verdict`.

Raw output is under
`.agentsight/experiments/rq3-grammar-recurrence-codetracebench-v1/preflight/`.

## Disposition

Both real paths passed on their first attempt. No execution defect, recovery,
algorithm edit, parameter edit, target retry, cap, or second candidate was
introduced. The displayed preflight metrics are diagnostics only and were not
used to interpret the hypothesis. The fixed FULL matrix is authorized without
changing the approved plan.
