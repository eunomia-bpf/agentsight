# Complete Run — Index-Free Responsibility Alignment

- completed: 2026-07-20
- execution status: **VALID / COMPLETE**
- registered result: **CONTRADICTED**, pending independent complete-result review
- paper mutation: none

## Unchanged Scientific Contract

The approved experiment reused the complete Step0050 task plans and causal
operation evidence while replacing the numeric plan-index output with an
index-free semantic transition interface. The model chose either `stay` or
`switch` to one exact retained responsibility string. It never saw or emitted a
numeric plan index or temporal-instance identifier.

The paper-level target remains:

```text
concrete task -> subtask (possibly nested) -> phase/strategy
              -> semantic action -> operation object -> result
```

Agent, model, session, tool, command, path, and status remain metadata,
filters, colors, details, or leaf evidence rather than main stack frames. This
experiment scores only the one flat human workflow-stage level available in
CodeTraceBench. It cannot validate nested subtasks, strategy, semantic action,
object, result, generated-label quality, or the complete task-semantic stack.

## Complete Source-Only Inference

Before opening official stages, the fixed candidate completed:

- 405/405 real trajectories and 20,866/20,866 operations;
- 251 tasks and all four registered agent frameworks;
- 20,866 local Qwen2.5-3B-Instruct Q4_K_M calls at temperature zero and seed
  20260720;
- 22,638,265 total model tokens: 22,329,628 prompt and 308,637 completion;
- maximum actual request length 6,006 tokens, below the registered 8,192-token
  input limit;
- 1,859.146 seconds (30.99 minutes) wall time;
- no missing operation, malformed exact-label output, context overflow,
  evidence-hash mismatch, or assignment failure.

All retained source-evidence bytes matched their Step0050 SHA-256 values. The
candidate never opened the human stage manifest, a stage count, scorer output,
future operation, or the current action result.

The source-side policy nevertheless degenerated:

- `switch`: 20,465 calls including the required first call of each trajectory;
- `stay`: only 401 calls;
- adjacent predicted boundaries: 20,060/20,461 (`0.980402`);
- predicted temporal stage instances: 20,465;
- exact `A -> B -> A` adjacent label alternations: 16,528;
- summed per-trajectory responsibility types used: 1,231 of 2,568 available.

Five one-item-plan trajectories grammar-forced 148 of the 401 stays. Across
all multi-item plans, the model voluntarily stayed only 253 times.

The complete result therefore generalizes the real-preflight observation. The
interface usually selects `switch`, and the exact-label constraint then forces
selection of a responsibility different from the active one. Many trajectories
alternate between allowed semantic strings instead of maintaining extended
work responsibility.

Raw inference root:
`.agentsight/experiments/rq3-index-free-responsibility-alignment-v1/full/`.

## Gold-Opened Standard Scoring

Only after predictions were complete did the scorer open the verified stage
manifest. It covered exactly 405 trajectories, 20,866 operations, 20,461
adjacent pairs, 2,948 human workflow-stage spans, 251 task clusters, and the
registered framework population.

| Method | Exact-span F1 | Ordinary B-cubed F1 | Boundary F1 | Predicted spans |
|---|---:|---:|---:|---:|
| Index-free candidate | **0.008201** | 0.264371 | 0.221740 | 20,465 |
| Numeric-index predecessor | 0.011574 | 0.585237 | 0.158025 | 5,519 |
| Current recurrence | **0.068055** | 0.649173 | **0.287106** | 6,897 |
| Multi-resolution recurrence | 0.056435 | **0.662740** | 0.265571 | 6,018 |

The primary candidate exact-span counts are 96 true matches, precision
`0.004691`, recall `0.032564`, and F1 `0.008201`. The candidate's ordinary
B-cubed precision is `0.992830`, but recall is only `0.152488`; its near-
singleton groups explain that imbalance. Exact boundary recall is similarly
high (`0.985450`) while precision is only `0.124925`, with 17,554 false
boundaries.

The registered 10,000-resample paired task-cluster bootstrap gives:

- candidate minus current recurrence: mean `-0.060033`, 95% interval
  `[-0.071057,-0.050050]`, positive fraction `0.0000`;
- candidate minus multi-resolution recurrence: mean `-0.048405`, 95% interval
  `[-0.057653,-0.039826]`, positive fraction `0.0000`;
- candidate minus numeric predecessor: mean `-0.003374`, 95% interval
  `[-0.006583,-0.000418]`, positive fraction `0.0141`.

The candidate is worse than both adoption comparators and the paired numeric
diagnostic. The fixed hypothesis is therefore **CONTRADICTED**. Secondary
metrics cannot override the primary registered decision.

## What The Result Does And Does Not Explain

Removing numeric indices did not rescue responsibility alignment. It also did
not isolate numeric tokens as the cause of Step0050, because this experiment
changed the complete representation-and-transition interface. The valid causal
statement is narrower:

> With the same retained task plans, model, causal evidence, and trajectories,
> the combined index-free `stay`/`switch-to-exact-label` interface produced a
> near-singleton transition policy and lower span fidelity than the numeric
> predecessor and both recurrence constructors.

The result identifies a transition-policy problem, not a failure of the target
task semantics. A legal state machine, semantic labels, unrestricted task
depth in the broader design, and removal of numeric tokens are each
insufficient when the local decision structure strongly prefers creating a new
instance. The result does not reject task-derived responsibility plans,
variable-depth task stacks, or the user-defined hierarchy.

It also provides no positive task-semantic flamegraph. Rendering these
predictions as if they recovered tasks and subtasks would be misleading: almost
every operation would become a separate stage, and the remaining lower layers
would still be runtime-derived evidence rather than validated semantic action,
object, and result frames.

## Scientific Disposition

The index-free joint transition interface is not adopted. It does not change
the exact thesis, the four fixed RQs, contribution scope, or the positive paper
story. No negative result is authorized for the paper, and no paper, shared
skill, or canonical submodule file was changed.

The failure is specific enough to guide the next mechanism without adding
features or thresholds: semantic boundary detection and responsibility-label
selection should not be forced into one competing grammar branch. The next
experiment, if admitted after independent review, should preserve the same
plans, operations, benchmark, standard metrics, and model while first making a
binary continuation decision and requesting a responsibility label only after
a predicted change. This is a candidate route, not a conclusion of this run.

## Raw Evidence

- inference summary and fixed predictions:
  `.agentsight/experiments/rq3-index-free-responsibility-alignment-v1/full/`;
- score rows, summary, report, and three 10,000-row bootstrap files:
  `.agentsight/experiments/rq3-index-free-responsibility-alignment-v1/score/`;
- approved plan, three serial reviews, and real preflight: this experiment
  directory.
