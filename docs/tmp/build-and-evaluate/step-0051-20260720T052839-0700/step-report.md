# Step 0051 Detailed Report

- step: `step-0051-20260720T052839-0700`
- outer state entered: EXPERIMENT
- gate completed: EXPERIMENT
- final route: EXPERIMENT
- paper thesis: **Agent observability needs profiling, not only debugging.**
- fixed RQs: attribution, localization/problem correspondence, tag accuracy,
  and cost
- paper mutation: none

## Objective

Test one bounded mechanism within RQ3: whether removing numeric indices and
asking Qwen2.5-3B to explicitly maintain or switch an active semantic
responsibility can recover flat human workflow-stage spans better than both
completed recurrence constructors.

This step preserved the user-defined main stack:

```text
concrete task -> nested subtask -> phase/strategy
              -> semantic action -> operation object -> result
```

It did not promote agent, model, session, tool, command, path, or status into
semantic frames.

## Plan And Preflight

The plan reused all 405 Step0050 responsibility plans, every operation-evidence
byte, numeric predecessor, recurrence assignments, model, and standard scorer.
Three mandatory serial reviews approved the final plan after clarifying the
bundled causal contrast and requiring adoption to beat both current and
multi-resolution recurrence on exact-span F1.

Real preflight completed one full trajectory per framework, 214/214 operations.
It exposed an all-switch exact-label alternation but no implementation,
coverage, context, grammar, or isolation defect. The approved mechanism was
therefore run unchanged to completion rather than stopped on a smoke result.

## Complete Execution And Result

The run completed 405 trajectories and 20,866 operations in 20,866 model calls
and 30.99 minutes. All raw evidence hashes, contexts, outputs, and assignments
validated. The model made 20,465 switches and only 401 stays, producing a
`0.980402` adjacent boundary rate and 16,528 `A -> B -> A` alternations.

| Method | Exact span F1 | Ordinary B-cubed F1 | Boundary F1 |
|---|---:|---:|---:|
| Index-free candidate | **0.008201** | 0.264371 | 0.221740 |
| Numeric predecessor | 0.011574 | 0.585237 | 0.158025 |
| Current recurrence | **0.068055** | 0.649173 | **0.287106** |
| Multi-resolution recurrence | 0.056435 | **0.662740** | 0.265571 |

The task-cluster bootstrap intervals for candidate minus current, multires, and
numeric are respectively `[-0.071057,-0.050050]`,
`[-0.057653,-0.039826]`, and `[-0.006583,-0.000418]`. The registered tested
hypothesis is **CONTRADICTED**.

## Independent Result Review

An independent read-only subagent explicitly used `research-experiment-design`
and reconstructed raw coverage, switch/stay behavior, all three standard
metrics, per-framework results, all 30,000 paired bootstrap deltas, gold
isolation, numeric contiguous instances, candidate instances, and adjacent pair
positions. It found zero mismatches, zero scorer bugs, zero must-fix items, and
no need to rerun.

## Scientific Interpretation

Step0051 rejects only the complete index-free `stay`/`switch-to-exact-label`
interface. It cannot claim that numeric tokens alone caused Step0050, because
representation and transition form both changed. It cannot reject semantic
responsibility planning, variable depth, or the intended task-semantic
hierarchy.

The concrete failure is transition coupling: label selection competes directly
with continuation in one grammar, and the policy almost always selects a new
label. Semantic text and legal state updates do not themselves guarantee
temporal responsibility continuity.

This is not a positive task-semantic flamegraph result. Only a flat unlabeled
stage was scored; nested subtasks, strategy, semantic actions, objects, results,
and generated names remain unvalidated.

## Disposition And Route

The candidate is not adopted. The negative mechanism result remains in
auditable experiment history and does not enter the positive paper. Thesis,
four RQs, contribution scope, and story remain unchanged. The paper, shared
skills, and canonical paper submodule were untouched.

The next EXPERIMENT may reuse all existing inputs and decouple the binary
continuation decision from responsibility-label selection. It should not add
system fields, thresholds, feature terms, depth caps, or post-hoc leaf deletion.
That route must receive its own approved Markdown plan before execution.

## Evidence Index

- approved plan and three serial reviews: `experiment-001/experiment-plan.md`
  and `experiment-001/plan-review-*.md`;
- complete real preflight: `experiment-001/real-preflight.md`;
- complete execution: `experiment-001/full-run.md`;
- independent reconstruction: `experiment-001/independent-result-review.md`;
- fixed predictions and caches:
  `.agentsight/experiments/rq3-index-free-responsibility-alignment-v1/full/`;
- standard score rows and bootstraps:
  `.agentsight/experiments/rq3-index-free-responsibility-alignment-v1/score/`.
