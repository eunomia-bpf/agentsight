# Step 0052 Detailed Report

- step: `step-0052-20260720T064136-0700`
- outer state entered: EXPERIMENT
- gate completed: EXPERIMENT
- final route: EXPERIMENT, but only with a distinct observable source of task
  continuity rather than another local prompt variant
- paper thesis: **Agent observability needs profiling, not only debugging.**
- fixed RQs: attribution, localization/problem correspondence, tag accuracy,
  and cost
- paper mutation: none

## Objective

Test whether factorizing current-operation responsibility continuation from
semantic-label selection can recover human workflow-stage spans better than
both completed recurrence constructors.

The fixed semantic target remained:

```text
concrete task -> nested subtask -> phase/strategy
              -> semantic action -> operation object -> result
```

This experiment evaluated only one flat stage-boundary component inside RQ3.
It did not treat system fields as semantic frames or claim full-hierarchy
validation.

## Plan And Reviews

One detailed Markdown plan reused the complete Step0050 plans, causal operation
evidence, Qwen2.5-3B model, 405-trajectory population, current/multires
assignments, Step0051 predecessor, and standard exact-span/B-cubed/boundary
metrics.

Three serial independent plan reviews explicitly used
`research-experiment-design`. Round 1 required four scientific corrections:
bound the contrast to same-operation factorization rather than causal
independence; fix exact label-call inputs; make supported/contradicted/
inconclusive/incomplete disjoint; and register concrete commands/artifact paths.
Rounds 2 and 3 returned APPROVE with no remaining issue and did not add gates,
baselines, or protocol complexity.

## Real Preflight

The actual implementation completed one entire trajectory per framework,
214/214 operations. It made 210 continuation and 28 label calls. The source-
side boundary rate was `0.114286`, compared with Step0051's near-all-switch
behavior. All grammar, evidence, output, context, coverage, and isolation checks
passed, so the fixed mechanism proceeded unchanged to a complete run.

## Complete Execution

The full source-only pass completed:

- 405 sessions and 20,866 operations;
- 20,313 continuation calls and 4,359 label calls;
- 3,954 changes, 16,359 learned continues, and 148 forced one-item continues;
- 4,359 predicted instances and adjacent boundary rate `0.193246`;
- 24,672 model calls, 24,735,341 total tokens, and 1,433.673 seconds;
- zero missing operations, invalid outputs, context overflow, evidence mismatch,
  or gold access.

The candidate inventory was never injected into a continuation prompt. The
unchanged source task/evidence naturally contained another retained label in
1,138/20,313 calls (`5.60%`), so this is not a single-factor label-visibility
ablation.

## Complete Result

| Method | Exact span F1 | Ordinary B-cubed F1 | Boundary F1 |
|---|---:|---:|---:|
| Decoupled candidate | **0.020802** | 0.622385 | 0.153609 |
| Step0051 joint interface | 0.008201 | 0.264371 | 0.221740 |
| Current recurrence | **0.068055** | 0.649173 | **0.287106** |
| Multi-resolution recurrence | 0.056435 | **0.662740** | 0.265571 |

Candidate-minus-joint exact-span bootstrap is wholly positive
`[+0.007819,+0.017686]`. Candidate-minus-current and candidate-minus-multires
are wholly negative `[-0.059199,-0.036636]` and
`[-0.045914,-0.026248]`. The mutually exclusive registered verdict is
**CONTRADICTED / NOT ADOPTED**.

All four frameworks separately lose to both recurrence comparators on exact
span F1. Candidate boundaries contain 499 TP, 3,455 FP, and 2,044 FN. The
interface fixes fragmentation but does not place human stages accurately.

## Return Diagnostics

- operation-triplet `A -> B -> A`, where B lasts one operation: 1,605;
- collapsed temporal-stage-sequence `A -> B -> A`: 2,808;
- changes returning to a responsibility seen earlier: 3,348;
- first-time responsibility entries: 606;
- total: `3,348 + 606 = 3,954` changes.

The fixed inventory is heavily revisited rather than progressively recovering a
nested typed hierarchy.

## Independent Result Review And Resolution

An independent read-only result reviewer explicitly used
`research-experiment-design` and reconstructed every population count, cache,
instance, pair, metric, framework slice, and 30,000 bootstrap deltas. It found
no scorer bug and confirmed the verdict.

Review iterations corrected provenance without changing model outputs:

- distinguish no injected inventory from naturally occurring label text;
- separate operation-triplet and collapsed-stage ABA definitions;
- materialize non-adjacent returns;
- preserve original inference wall time across cache-only summary regeneration.

The final reviewer verdict was **APPROVE**, with zero must-fix and zero
should-fix.

## Scientific Disposition

The candidate is rejected. The complete two-stage interface improves its
failed predecessor but does not beat current evidence. This is a mechanism
boundary, not evidence against semantic planning, larger models, variable
depth, RQ3, or the thesis.

It does not authorize a positive task-semantic flamegraph, paper negative
result, thesis/RQ/story change, or contribution narrowing. Paper, shared
skills, and canonical submodule remained untouched.

Further local prompt-only variants are not supported. A later experiment must
introduce a distinct observable source of task continuity and receive its own
reviewed plan while reusing this complete benchmark and standard scorer.

## Evidence Index

- plan and three reviews: `experiment-001/experiment-plan.md` and
  `experiment-001/plan-review-*.md`;
- real preflight: `experiment-001/real-preflight.md`;
- complete run: `experiment-001/full-run.md`;
- independent review and corrections:
  `experiment-001/independent-result-review.md`;
- raw full predictions:
  `.agentsight/experiments/rq3-decoupled-responsibility-continuation-v1/full/`;
- raw score and bootstrap outputs:
  `.agentsight/experiments/rq3-decoupled-responsibility-continuation-v1/score/`.
