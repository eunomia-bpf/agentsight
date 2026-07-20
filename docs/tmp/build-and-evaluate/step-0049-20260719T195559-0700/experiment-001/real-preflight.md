# REAL PREFLIGHT — Multi-Resolution Recurrence

**Completed:** 2026-07-19  
**Status:** PASS / VALID  
**Scientific verdict:** not tested; no preflight metric may change the approved
algorithm, plan, field, threshold, population, or interpretation

## Scope

The preflight ran exactly the two approved real paths after Grok 4.5 approved
the plan and Claude Opus 4.8 passed the implementation audit:

1. the modified release Rust constructor on one existing detail-free
   OSWorld-Human fold; and
2. the modified release Rust constructor on one complete existing
   CodeTraceBench target, using all 2,229 disjoint reference sessions.

No code, plan, threshold, field, input selection, or scorer changed after the
preflight began.

## OSWorld-Human Fold 0 — Rust Fallback

The candidate binary consumed the retained Step 0024 fold-0 reference and
target inputs directly through `--induce-operation-stack`. The target contains
45 sessions and 521 operations; the reference contains 242 sessions and 3,457
operations. Neither input contains `action_detail`.

The resulting profile is byte-identical to the retained Step 0024 Rust profile:

- candidate SHA-256:
  `6d63f471dd3da83794091dc82fc2ad705692435e2dea066b3744da16f30d76a2`;
- Step 0024 SHA-256:
  `6d63f471dd3da83794091dc82fc2ad705692435e2dea066b3744da16f30d76a2`;
- `cmp`: exact equality;
- selected source fields: `action` only;
- `detail_recurrence`: absent;
- target mass: 521 in and 521 out;
- predicted groups: 267.

This is a Rust-level fallback check on the modified constructor. It is not the
Python-only OSWorld score path called out by the implementation reviewer; that
path would reproduce the old scores without exercising the changed Rust code.
The full run must use the existing five-fold Rust/Python equivalence evaluator
to close this obligation on all folds.

Raw outputs:

- `.agentsight/experiments/rq3-multiresolution-recurrence-v1/preflight/osworld/fold-0/command.json`
- `.agentsight/experiments/rq3-multiresolution-recurrence-v1/preflight/osworld/fold-0/stdout.json`
- `.agentsight/experiments/rq3-multiresolution-recurrence-v1/preflight/osworld/fold-0/profile.json`

## CodeTraceBench One-Target Path

The existing stage-fidelity evaluator passed only unit weight, `session`,
coarse `action`, and the existing source-visible `raw_action_key` renamed to
`action_detail`. The Rust constructor finished prediction before the evaluator
opened the verified manifest or official stages.

The execution is valid:

- 2,229 disjoint reference sessions / 87,703 operations;
- one complete 47-operation target / 46 adjacent decisions;
- all source-visible input fields present and non-empty;
- selected source fields exactly `action` and `action_detail`;
- detail recurrence constructed over all 85,474 reference transitions;
- 32 target transitions seen at detail resolution and 14 unseen;
- two coarse boundaries rescued and zero coarse boundaries added;
- every target pair scored once and every operation assigned once;
- all 47 units of mass conserved;
- official-stage coverage exact and loaded only after prediction;
- `tested_hypothesis = not tested` and no experiment verdict emitted.

The displayed preflight B-cubed and boundary values are diagnostics only. They
were not used to alter the constructor or decide whether to proceed.

Raw outputs:

- `.agentsight/experiments/rq3-multiresolution-recurrence-v1/preflight/codetrace/command.json`
- `.agentsight/experiments/rq3-multiresolution-recurrence-v1/preflight/codetrace/{reference-input,target-input}.jsonl`
- `.agentsight/experiments/rq3-multiresolution-recurrence-v1/preflight/codetrace/profile.json`
- `.agentsight/experiments/rq3-multiresolution-recurrence-v1/preflight/codetrace/{pair-decisions,operation-assignments}.jsonl`
- `.agentsight/experiments/rq3-multiresolution-recurrence-v1/preflight/codetrace/summary.json`

## Decision

REAL PREFLIGHT passes on the first attempt. The execution paths, input
isolation, optional-detail activation, detail-free fallback, coarse-boundary
subset property, complete selected coverage, and mass conservation all hold.
The approved full run may execute once with the implementation unchanged.
