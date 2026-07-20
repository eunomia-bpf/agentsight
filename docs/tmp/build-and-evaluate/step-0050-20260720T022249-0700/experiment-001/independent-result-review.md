# Independent Complete-Result Review — Task-Rooted Stage Alignment

**Reviewed:** 2026-07-20
**Reviewer:** independent read-only subagent
**Skill followed:** `research-experiment-design` complete-result review
**Run status:** **VALID / COMPLETE**
**Tested hypothesis:** **CONTRADICTED**
**Paper impact:** local mechanism boundary only

The reviewer independently read the approved plan, evaluator, complete session
caches, fixed prediction rows, corrected operation and boundary score rows, and
both 10,000-row bootstrap files. Aggregate prose was not trusted as the source
of primary values.

## Verdict

| Judgment | Value |
|---|---|
| validity | **PASS** |
| completeness | **COMPLETE** |
| registered scientific verdict | **CONTRADICTED** |
| mechanism decision | **DO NOT ADOPT** |
| paper decision | no paper change; preserve thesis, four RQs, scope, and positive story |

This is not an invalid or wasted experiment. It credibly rejects the fixed
numeric-index causal aligner. It does not reject task-semantic profiling,
variable-depth task stacks, the paper thesis, or RQ3.

## Independent Completeness And Isolation Reconstruction

All fixed counts and invariants pass:

- 405 trajectories, 20,866 operations, 2,948 official human stages, 251 task
  clusters, and 20,461 adjacent pairs;
- 405 nonempty session caches;
- no duplicate or missing `(session, step_id)` and continuous step numbering
  within every trajectory;
- framework sessions: OpenHands 213, Terminus2 93, mini-SWE-agent 71, and
  SWE-agent 28;
- 42,137 logical model calls, exactly `405 + 2 * 20,866`;
- every model call completed in one successful attempt;
- maximum input length 5,991 tokens, below the fixed 8,192-token limit;
- candidate and plan-free prompts share the same source-evidence prefix for
  each operation;
- no official-stage, gold, or solved field occurs in the inference caches;
- the 20,866 imported multi-resolution assignments match the retained
  comparator file item by item.

## Independent Primary Reconstruction

| Method | Exact-span P | Exact-span R | Exact-span F1 | Exact TP | Predicted spans |
|---|---:|---:|---:|---:|---:|
| Numeric-index candidate | 0.008878420004 | 0.016621438263 | **0.011574347467** | 49 | 5,519 |
| Matched plan-free Qwen | 0.004908410080 | 0.032903663501 | 0.008542492294 | 97 | 19,762 |
| Multi-resolution recurrence | 0.042040545032 | 0.085820895522 | **0.056435422708** | 253 | 6,018 |

Recomputing the registered task-cluster bootstrap reproduces every retained raw
delta:

- candidate minus plan-free Qwen: mean `+0.003036415125`, 95% interval
  `[+0.000002254944,+0.006315789271]`;
- candidate minus multi-resolution recurrence: mean `-0.045031039690`, 95%
  interval `[-0.054570427580,-0.035972967328]`.

The candidate is slightly above the nearly-singleton plan-free policy, but its
interval against the strongest comparator is wholly negative. The registered
decision rule therefore requires **CONTRADICTED**.

## Corrected Secondary Reconstruction

| Method | Ordinary B-cubed P | Recall | F1 | Boundary F1 |
|---|---:|---:|---:|---:|
| Numeric-index candidate | 0.505759090110 | 0.694350689708 | **0.585236749086** | 0.158025336294 |
| Matched plan-free Qwen | 0.985051092339 | 0.165843988400 | 0.283891737250 | 0.219543378995 |
| Multi-resolution recurrence | 0.782025634215 | 0.575028961707 | **0.662740305102** | 0.265571358509 |

The first score attempt incorrectly made the reusable numeric plan index the
candidate B-cubed cluster ID. This merged non-contiguous visits to one
responsibility type into one temporal cluster, contrary to the approved rule
that consecutive equal choices form stage instances. The corrected scorer
assigns a unique ID to each contiguous run and preserves the plan index only as
`candidate_responsibility`.

This correction changes candidate B-cubed F1 from approximately `0.425210` to
`0.585237`. It changes neither predictions, exact-span or boundary results,
bootstrap deltas, nor the contradicted decision. The first attempt is preserved
under `score-attempt-1-plan-index-bcubed/`.

## Specific Failure Mechanism: Numeric Ordinal Bias

The raw choices reject a vague explanation such as “the model is simply too
small.” They show a strong interface-specific pattern:

- 397/405 trajectories choose `plan_index=1` at the first operation; only
  eight choose index 0;
- index 0 occurs on only 180/20,866 operations (`0.8626%`) and appears in only
  18 trajectories;
- 4,384/5,114 candidate switches (`85.73%`) increment the previous index by
  exactly one;
- 638 switches jump from an index greater than one back to index 1;
- 3,347 switches return to a responsibility type used in an earlier
  non-adjacent run, involving 275/405 trajectories;
- the candidate temporal-run median is one operation;
- 206 trajectories have one label covering at least half of all operations;
  118 have one label covering at least 90%.

The longest representative trajectory has the fixed plan:

```text
0 initialize git server
1 configure ssh authentication
2 deploy main branch
3 deploy dev branch
4 verify deployment
5 test deployment
```

Its 275 choices are `1,2,3,4,5` followed by index 5 for the rest. Therefore
`test deployment` owns 271 operations while `initialize git server` owns none.
This is the direct source of the visibly overwide frame and the low exact-span
score. Qwen treated the number as a one-based ordered-list counter or “next
item” continuation rather than comparing task meanings.

## Planner And Lexical Diagnostics

The raw caches independently yield:

- 2,754 raw planner items;
- 2,568 normalized responsibility labels;
- 186 exact duplicates removed;
- 182 candidate registered lexical-rule hits;
- 1,247 plan-free registered lexical-rule hits.

The 186 duplicate items occur in eight trajectories; the largest removes 77.
Three trajectories collapse 32--34 repeated raw items to one normalized label.

The lexical-rule counts are not semantic error rates. The deterministic rule
also matches legitimate task phrases such as `load speech recognition model`
and `validate model accuracy`. Reports may retain the counts as diagnostics but
must not call them human-validated semantic violations.

## Flamegraph Judgment

The longest-trajectory figure is an honest failure diagnostic only after its
title states that the registered candidate was contradicted:

- its very wide `test deployment` frame exposes the 271/275 collapse;
- the candidate supplies only one flat generated responsibility level;
- `phase` comes from the existing `explore/change` field;
- `semantic-action` comes from the coarse action classifier;
- `object` is extracted from command/path text;
- `result` is the first visible observation line;
- the concrete task string still includes terminal-screen material.

It does not implement or validate the target main stack:

```text
concrete task -> subtask -> phase/strategy
              -> semantic action -> operation object -> result
```

It must not be used as a positive paper figure or described as a recovered
task-semantic hierarchy. System-derived lower frames remain evidence, not main
semantic structure.

## Minimal Next Mechanism

The next experiment should isolate the discovered ordinal confound before
adding hierarchy complexity. Reuse the existing 405 normalized plans,
20,866 operations, matched plan-free predictions, recurrence comparators, and
scoring inputs. Rerun only candidate causal choices through an index-free
interface:

```json
{"decision":"stay","responsibility":null}
```

or:

```json
{"decision":"switch","responsibility":"exact retained plan label"}
```

The model sees the active responsibility text and the retained responsibility
strings, but no numeric index or instance number. Its output may select only an
exact existing string.

The representation must keep two identities separate:

- `responsibility_type`: reusable semantic planner label;
- `stage_instance`: one contiguous temporal visit. Every `switch` creates a
  new instance even when returning to a previous responsibility type; only
  `stay` extends the current instance.

This tests whether removing ordinal bias improves human workflow-stage
alignment. It still cannot validate open-vocabulary label accuracy, nested
hierarchy, or the complete task-semantic stack.

## Process Retrospective

Nine plan reviews and seven real-preflight attempts exceeded the intended lean
experiment loop. The repeated preflights repaired real implementation defects
and do not invalidate the completed result, but the next experiment should not
repeat review inflation. One complete plan, the required small number of
scientific reviews, one real preflight after implementation, the full run, and
one independent result reconstruction are sufficient unless a concrete defect
requires a narrowly documented repair.

## Required Disposition

1. Keep the corrected B-cubed score and archived first attempt.
2. Record run status valid, hypothesis contradicted, and paper impact limited
   to this mechanism.
3. Do not adopt the numeric-index aligner and do not change the thesis, RQs,
   scope, or paper story.
4. Call 182/1,247 lexical-rule hits, not semantic error rates.
5. Keep the figure only as a failed-mechanism diagnostic.
6. Use the index-free responsibility interface as the next smallest causal
   test before introducing a more complex stack controller.
