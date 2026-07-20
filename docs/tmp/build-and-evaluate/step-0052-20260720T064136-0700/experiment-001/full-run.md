# Complete Run — Decoupled Responsibility Continuation

- completed: 2026-07-20
- execution status: **VALID / COMPLETE**
- registered result: **CONTRADICTED / NOT ADOPTED**, pending independent review
- paper mutation: none

## Unchanged Scientific Contract

The experiment reused all 405 retained task-responsibility plans and complete
causal operation evidence. It changed only the current-operation interface:
one call decided `continue` or `change` without an injected alternative-label
inventory, and a second call selected an exact semantic responsibility only at
initialization or after `change`.

This factorizes the current decision but does not make boundary inference
causally independent of label selection: a selected label becomes later active
state. The complete candidate interface is the tested mechanism.

The paper-level target remains:

```text
concrete task -> nested subtask -> phase/strategy
              -> semantic action -> operation object -> result
```

System fields remain metadata or leaf evidence. This run scores one flat
unlabeled workflow-stage level and cannot validate the full hierarchy or a
positive task-semantic flamegraph.

## Complete Source-Only Inference

Before opening official stages, the fixed implementation completed:

- 405/405 trajectories and 20,866/20,866 operations;
- 251 tasks and all four registered frameworks;
- 20,313 binary continuation calls and 4,359 exact-label calls, totaling
  24,672 Qwen2.5-3B calls;
- 24,735,341 total model tokens: 24,562,828 prompt and 172,513 completion;
- request lengths 172--5,951, below the 8,192-token limit;
- 1,433.673 seconds (23.89 minutes) wall time;
- no missing operation, invalid exact response, context overflow, evidence-hash
  mismatch, or assignment failure.

The model produced:

- `change`: 3,954;
- learned `continue`: 16,359;
- structurally forced one-item-plan `continue`: 148;
- temporal stage instances: 4,359;
- adjacent boundary rate: `0.193246`;
- operation-triplet `A -> B -> A` alternations, where the middle stage has one
  operation: 1,605;
- collapsed temporal-stage-sequence `A -> B -> A` alternations: 2,808;
- changes returning to a previously used responsibility: 3,348;
- changes entering a responsibility not previously used in that trajectory:
  606;
- responsibility types used: 1,011 of 2,568 summed per trajectory.

Five one-item-plan sessions contain 153 operations. Their 148 later operations
were deterministically continued because no distinct responsibility exists;
this is not learned success.

Every continuation call omitted the candidate-label inventory. Because the
unchanged public task and causal evidence remain visible, 1,138/20,313 calls
(`5.60%`) naturally contained an exact string equal to some other retained
responsibility. This is not injected label-list visibility and was not filtered,
but it means the comparison cannot claim complete absence of alternative-label
text. Neither inference command accepted or opened the human manifest,
official stages, score output, future operations, current action results,
numeric plan indices, or temporal instance IDs.

Raw inference root:
`.agentsight/experiments/rq3-decoupled-responsibility-continuation-v1/full/`.

## Gold-Opened Standard Scoring

After all predictions were fixed, the separate scorer covered exactly 405
sessions, 20,866 operations, 20,461 adjacent pairs, 2,948 human stage spans,
251 task clusters, and the registered framework population.

| Method | Exact-span F1 | Ordinary B-cubed F1 | Boundary F1 | Predicted spans |
|---|---:|---:|---:|---:|
| Decoupled candidate | **0.020802** | 0.622385 | 0.153609 | 4,359 |
| Step0051 joint interface | 0.008201 | 0.264371 | 0.221740 | 20,465 |
| Current recurrence | **0.068055** | 0.649173 | **0.287106** | 6,897 |
| Multi-resolution recurrence | 0.056435 | **0.662740** | 0.265571 | 6,018 |

The candidate exact-span counts are 76 true matches, precision `0.017435`,
recall `0.025780`, and F1 `0.020802`. Ordinary B-cubed precision is `0.557246`
and recall `0.704768`. Boundary counts are TP 499, FP 3,455, FN 2,044, and TN
14,463, yielding precision `0.126201`, recall `0.196225`, and F1 `0.153609`.

Thus factorization repairs Step0051's near-singleton partition but still places
most exact boundaries incorrectly: it misses 2,044 human boundaries while
adding 3,455 false boundaries.

The registered paired 10,000-resample task-cluster bootstrap gives:

- candidate minus Step0051 joint interface: mean `+0.012603`, 95% interval
  `[+0.007819,+0.017686]`, positive fraction `1.0000`;
- candidate minus current recurrence: mean `-0.047430`, 95% interval
  `[-0.059199,-0.036636]`, positive fraction `0.0000`;
- candidate minus multi-resolution recurrence: mean `-0.035802`, 95% interval
  `[-0.045914,-0.026248]`, positive fraction `0.0000`.

The candidate materially improves its joint-interface predecessor but is
wholly below both adoption comparators. Under the disjoint registered decision
rule, the hypothesis is **CONTRADICTED / NOT ADOPTED**.

## Per-Framework Direction

Candidate exact-span F1 remains below both recurrence comparators in all four
frameworks:

- OpenHands: `0.021451` versus current `0.083542` and multires `0.067162`;
- SWE-agent: `0.039024` versus `0.079498` and `0.084567`;
- Terminus2: `0.018779` versus `0.038112` and `0.031202`;
- mini-SWE-agent: `0.015826` versus `0.087329` and `0.079621`.

No framework-level win is hidden by pooled scoring.

## Scientific Interpretation Boundary

The complete two-stage interface has one real positive mechanism effect: it
prevents the same-operation label grammar from forcing near-all-switch behavior
and improves partition fidelity over Step0051. That comparison does not prove
boundary-policy independence, grammar-order causality, or label quality.

It still fails the paper-value adoption test. A local active-only continuation
decision does not reliably place human workflow-stage boundaries even when it
maintains extended responsibility spans. The result does not reject semantic
responsibility planning, larger models, variable-depth stacks, or the intended
task-semantic hierarchy.

This experiment does not validate nested subtasks, phase/strategy,
semantic-action, object, result, generated names, or diagnostic value. It is
not positive evidence for the requested task-semantic flamegraph and must not
enter the positive paper.

## Disposition

The candidate is not adopted. Thesis, attribution/localization/tag-accuracy/
cost RQs, contribution scope, and positive story remain unchanged. The paper,
shared skills, and canonical paper submodule were not modified.

No further prompt-only local transition variant is authorized by this result.
Any next mechanism must introduce a scientifically distinct observable source
of task continuity while reusing the completed benchmark and standard metrics;
it must receive a new reviewed plan.

## Raw Evidence

- full source-only caches, predictions, and summary:
  `.agentsight/experiments/rq3-decoupled-responsibility-continuation-v1/full/`;
- operation rows, boundary rows, summary, report, and three 10,000-row
  bootstrap files:
  `.agentsight/experiments/rq3-decoupled-responsibility-continuation-v1/score/`;
- plan, three serial reviews, and real preflight: this experiment directory.
