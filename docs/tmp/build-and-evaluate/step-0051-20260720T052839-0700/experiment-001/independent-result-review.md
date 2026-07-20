# Independent Result Review — Step0051

- reviewer: independent read-only subagent
- skill explicitly used: `research-experiment-design`
- reviewed state: fixed complete inference, raw predictions/caches, scorer,
  gold-opened score rows, and bootstrap outputs
- final verdict: **VALID / COMPLETE; HYPOTHESIS CONTRADICTED**
- must-fix: **0**
- scorer bug: **none found**
- rerun required: **no**

## Independent Coverage Reconstruction

The reviewer independently rebuilt the population from raw target operations,
the verified gold parquet, candidate and numeric predictions, and recurrence
assignments:

- 405 sessions;
- 20,866 unique operations;
- 20,461 adjacent pairs;
- 2,948 human stage spans;
- 251 task clusters;
- OpenHands 213, Terminus2 93, mini-SWE-agent 71, and SWE-agent 28 sessions.

Every session uses consecutive one-based step IDs `1..N`; no operation is
missing or duplicated.

## Raw Inference Reconstruction

All 405 session caches and 20,866 transitions were checked:

- 20,465 switches, 401 stays, and 20,465 temporal instances;
- adjacent boundary rate `0.9804017399`;
- request length range 235--6,006, below the 8,192 limit;
- first-attempt valid responses 20,866/20,866;
- malformed or nonexact response 0;
- source-cache and shared-evidence hash mismatch 0;
- step mismatch 0;
- stored stage instance versus contiguous-label-run mismatch 0;
- 16,528 exact `A -> B -> A` adjacent alternations.

Five one-item plans grammar-forced 148 stays. Multi-item plans contain only 253
voluntary stays. This is genuine transition-policy behavior rather than a
partition created by the scorer.

## Independently Recomputed Metrics

| Method | Exact span F1 | Ordinary B-cubed F1 | Boundary F1 |
|---|---:|---:|---:|
| Candidate | 0.00820057 | 0.26437093 | 0.22174048 |
| Numeric predecessor | 0.01157435 | 0.58523675 | 0.15802534 |
| Current recurrence | 0.06805485 | 0.64917310 | 0.28710570 |
| Multi-resolution recurrence | 0.05643542 | 0.66274031 | 0.26557136 |

Candidate sufficient statistics also match exactly:

- span TP 96, predicted 20,465, gold 2,948;
- span precision `0.00469094`, recall `0.03256445`;
- boundary TP 2,506, FP 17,554, FN 37, TN 364;
- B-cubed precision `0.99282954`, recall `0.15248770`.

The high B-cubed precision is the expected consequence of a near-singleton
partition; the low recall and exact-span F1 expose the severe oversegmentation.
The candidate loses to both adoption comparators within every framework, so no
pooled result hides a framework-level win.

## Bootstrap Reconstruction

With the registered 251 task clusters, seed 20260720, and 10,000 paired
resamples, the reviewer reproduced every stored delta:

- candidate minus current recurrence: mean `-0.06003299`, 95% interval
  `[-0.07105694,-0.05005034]`, positive fraction `0.0000`;
- candidate minus multi-resolution recurrence: mean `-0.04840473`, interval
  `[-0.05765284,-0.03982619]`, positive fraction `0.0000`;
- candidate minus numeric predecessor: mean `-0.00337369`, interval
  `[-0.00658305,-0.00041758]`, positive fraction `0.0141`.

The registered `contradicted` verdict is correct.

## Scorer Audit

The numeric contiguous-instance mapping is correct. `score_rows()` stores a
pair's `position` as `current_step_id - 1`; because steps are continuous and
one-based, `(position, position + 1)` is exactly the left/right operation pair.
All 20,461 independently recomputed numeric boundaries have zero mismatches.

Candidate scoring also has zero mismatch against stored temporal instances and
contiguous exact-label runs. The grammar forbids switching to the active label,
so every switch necessarily starts a new observed run. A future protocol that
permits switch-to-same-label would require an explicit instance field in the
scorer, but that condition is absent here and is not a present bug.

## Isolation And Interpretation Boundary

Inference has no manifest argument; the official parquet is opened only by the
separate score path. Prompts contain the retained plan, active responsibility,
and source-derived causal evidence, but no plan index, stage instance, numbered
list, official stage, future operation, or scorer result. Source plans and
evidence hashes match Step0050.

The only authorized conclusion is:

> The complete index-free semantic transition interface did not recover human
> workflow-stage spans and, because it switched on nearly every operation, was
> significantly weaker than both recurrence constructors and the numeric
> predecessor.

The experiment changes both numeric representation and transition form. It
cannot identify numeric tokens as the sole cause, reject semantic planning in
general, or conclude that Qwen cannot perform any task decomposition.

It evaluates only one flat unlabeled workflow-stage level. It does not validate
the full target:

```text
concrete task -> nested subtask -> phase/strategy
              -> semantic action -> operation object -> result
```

There is no nested-subtask, strategy, semantic-action, object, result,
generated-name, variable-depth, or complete flamegraph validation in this run.

## Final Disposition

The experiment is decisive for this candidate mechanism. Reject the interface,
retain the result in experiment history, do not put it in the positive paper,
and do not change the thesis, four RQs, contribution scope, or paper story.
