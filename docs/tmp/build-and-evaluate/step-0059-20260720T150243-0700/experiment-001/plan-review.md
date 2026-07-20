# Experiment Plan Review — Step 0059 Experiment 001

## Review Scope

An independent read-only reviewer explicitly applied
`research-experiment-design` to the complete plan in three serial rounds. The
review focused on whether the candidate was a renamed repeat of Steps
0054--0056, whether the intervention was singular and identifiable, and whether
the workload, standard metrics, isolation, completion, claim boundary, and
decision rule were sufficient without adding process complexity.

## Round 1 — Revise

The reviewer accepted the experiment as non-duplicate. Steps 0054--0056 expose
an unrestricted path editor with arbitrary-suffix `pop(target_depth)` and
same-turn `replace(target_depth,label)`. Step 0059 deletes both abilities and
tests a literal `stay / push-one / pop-one` well-nested controller while fixing
the model, inputs, workload, scorer, and exact-leaf identity invariant.

One must-fix was found: the Decision section treated session collapse or
undefined `near-turn singleton` behavior as an independent contradiction gate,
despite classifying those quantities as diagnostics. That extra outcome
override was deleted. Collapse and fragmentation remain mechanism
interpretations only.

## Round 2 — Approve

The reviewer confirmed that the prior must-fix was removed. Coverage
correctness and the registered candidate-minus-recurrence B-cubed F1 interval
alone now determine supported, contradicted, or inconclusive. No remaining
scientific must-fix was found.

## Round 3 — Approve

The final adversarial reread returned **APPROVE** with zero remaining
scientific must-fix, no hidden duplication, and no extra gate. The fixed
model, inputs, complete workload, identity invariant, scorer, comparisons, and
claim boundaries remain internally consistent.

## Authorized Experiment

Implement and run exactly one well-nested online controller:

```text
stay
push one concrete nested task label
pop exactly one active leaf
```

Exact duplicate-leaf pushes remain identity-preserving stays. The plan does
not authorize replace, arbitrary-depth pop, prompt variants, model variants,
depth limits, thresholds, post-hoc contraction, alternate benchmarks, custom
metrics, paper changes, or shared-skill changes.
