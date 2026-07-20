# Complete Run — Task-Rooted Semantic Stage Alignment

**Completed:** 2026-07-20T05:07:36-07:00
**Execution status:** VALID / COMPLETE
**Registered result:** CONTRADICTED, pending independent complete-result review

## Unchanged Scientific Contract

The approved revision-8 experiment ran the fixed task-rooted candidate and
matched plan-free Qwen baseline on the complete real CodeTraceBench target
population. The run did not change the thesis, four RQs, paper story,
population, evidence projection, model, baselines, primary metric, bootstrap
unit, or decision rule.

The paper-level target representation remains:

```text
concrete task -> subtask (possibly nested) -> phase/strategy
              -> semantic action -> operation object -> result
```

Agent, model, session, tool, command, path, and status remain metadata or
bottom-level evidence, not main semantic frames. This experiment scores only
one human workflow-stage level. It cannot validate generated responsibility
names or the complete nested representation.

## Complete Causal Inference

The exact real-preflight implementation completed source-only inference before
the official stage manifest was opened:

- 405/405 trajectories and 20,866/20,866 operations;
- 251 distinct tasks and all four registered agent frameworks;
- 405 goal-planner calls plus two causal decisions for every operation,
  totaling 42,137 model calls;
- Qwen2.5-3B-Instruct Q4_K_M, temperature zero, seed 20260720;
- 43,620,419 total model tokens;
- maximum actual request length 5,991 tokens, below the registered 8,192-token
  input limit;
- wall time 4,317.499 seconds (71.96 minutes);
- no missing operation, malformed retained output, context overflow, or
  assignment-conservation failure.

The candidate planner produced 2,568 normalized responsibility types: mean
6.341 per trajectory, median 6, range 1--29. It removed 186 exact duplicate
strings by the registered stable-first-occurrence rule. It used 2,172 of the
2,568 retained types at least once. The registered lexical rule matched
182/2,568 labels (7.09%); those labels and their predictions were retained
without retry or rewriting. This is not a human-validated semantic error rate:
the rule also matches legitimate task objects such as `model`.

The complete candidate causal pass made 5,114 switches over 20,461 adjacent
pairs, a boundary rate of 0.249939. The plan-free pass made 19,357 switches, a
boundary rate of 0.946044. Thus the fixed task plan prevented the earlier
nearly one-new-frame-per-operation degeneration, but this is only a source-side
fragmentation diagnostic, not gold fidelity.

Raw inference root:
`.agentsight/experiments/rq3-task-rooted-stage-alignment-v1/full/`.

## Gold-Opened Standard Scoring

After all predictions were fixed, the scorer opened the verified manifest and
covered exactly:

- 405 trajectories;
- 20,866 operations;
- 20,461 adjacent pairs;
- 2,948 human workflow-stage spans;
- 251 task clusters;
- OpenHands 213, Terminus2 93, mini-SWE-agent 71, and SWE-agent 28 sessions.

### Primary exact unlabeled span metric

| Method | Precision | Recall | F1 | Exact spans | Predicted spans |
|---|---:|---:|---:|---:|---:|
| Task-rooted candidate | 0.008878 | 0.016621 | **0.011574** | 49 | 5,519 |
| Matched plan-free Qwen | 0.004908 | 0.032904 | 0.008542 | 97 | 19,762 |
| Multi-resolution recurrence | 0.042041 | 0.085821 | **0.056435** | 253 | 6,018 |
| Current recurrence | 0.048572 | 0.113636 | 0.068055 | 335 | 6,897 |

The candidate is slightly above the matched plan-free Qwen segmenter but far
below the registered strongest comparator. The paired 10,000-resample
task-cluster bootstrap gives:

- candidate minus plan-free Qwen: mean `+0.003036`, 95% interval
  `[+0.000002,+0.006316]`, positive fraction `0.975`;
- candidate minus multi-resolution recurrence: mean `-0.045031`, 95% interval
  `[-0.054570,-0.035973]`, positive fraction `0.000`.

Because the second interval is wholly negative, the fixed hypothesis is
**CONTRADICTED** under its registered rule.

### Ordinary unweighted B-cubed partition metric

| Method | Precision | Recall | F1 | Predicted groups |
|---|---:|---:|---:|---:|
| Task-rooted candidate | 0.505759 | 0.694351 | **0.585237** | 5,519 |
| Matched plan-free Qwen | 0.985051 | 0.165844 | 0.283892 | 19,762 |
| Multi-resolution recurrence | 0.782026 | 0.575029 | **0.662740** | 6,018 |
| Current recurrence | 0.828579 | 0.533630 | 0.649173 | 6,897 |

The candidate B-cubed score confirms that the fixed plan materially improves
partition coherence over almost-singleton plan-free decisions. It remains
below both recurrence constructors and cannot rescue the failed primary rule.

### Exact adjacent-boundary diagnostic

| Method | Precision | Recall | F1 | TP | FP | FN |
|---|---:|---:|---:|---:|---:|---:|
| Task-rooted candidate | 0.118303 | 0.237908 | **0.158025** | 605 | 4,509 | 1,938 |
| Matched plan-free Qwen | 0.124193 | 0.945340 | 0.219543 | 2,404 | 16,953 | 139 |
| Multi-resolution recurrence | 0.192945 | 0.425875 | **0.265571** | 1,083 | 4,530 | 1,460 |

The candidate suppresses most plan-free false boundaries, but also misses most
human stage boundaries. Its 5,519 temporal responsibility runs are 1.872 times
the 2,948 human stages, yet 79.13% of candidate runs contain one operation.
Across trajectories, 3,347 runs are returns to a responsibility type used in
an earlier non-adjacent run; these revisits are 60.65% of candidate runs. The
model therefore learned reusable responsibility *types* without reliably
maintaining the active concrete task *instance*.

The raw choices expose a more specific structural confound. The first choice
is numeric index 1 in 397/405 trajectories, while index 0 appears on only
180/20,866 operations. Of 5,114 candidate switches, 4,384 (85.73%) increment
the preceding index by exactly one, and 638 jump from an index greater than one
back to index 1. In the rendered 275-operation trajectory, the choices are
`1,2,3,4,5` and then index 5 (`test deployment`) for the remaining 270
operations. The fixed output therefore does not isolate semantic alignment:
Qwen appears to treat the numeric plan index as an ordinal counter or one-based
list position. This numeric-interface bias is a direct explanation for both
the initial march through the plan and the overwide final responsibility.

## Scorer Correction Before Result Review

The first scoring attempt incorrectly used a plan index as the candidate's
B-cubed cluster identifier. When the model left an index and later revisited
it, non-contiguous temporal runs were merged into one cluster. That violated
the approved definition that consecutive equal indices form spans and
conflated responsibility type with task instance.

The prediction file, primary exact-span metric, boundary metric, population,
and bootstrap outputs were not changed. The scorer was corrected so each
contiguous plan-index run receives a unique candidate instance identifier while
retaining the plan index separately as `candidate_responsibility`. The complete
score was rerun. The old attempt remains archived at
`.agentsight/experiments/rq3-task-rooted-stage-alignment-v1/score-attempt-1-plan-index-bcubed/`;
the corrected score is under
`.agentsight/experiments/rq3-task-rooted-stage-alignment-v1/score/`.

## Qualitative Representation Audit

The mechanically rendered example is explicitly titled a failed numeric-index
mechanism diagnostic. It roots the profile in a concrete task, but its broad
generated `test deployment` responsibility covers nearly the whole trajectory.
Lower frames revert to runtime-derived `explore/change`, `execute/search/edit`,
command or path, and a coarse visible-result field.

Consequently the renderer is **not** evidence that the intended task-semantic
stack has been recovered. The run validates only that a fixed responsibility
inventory reduces singleton fragmentation. It does not recover the desired
concrete task -> nested subtask -> strategy -> semantic action -> object ->
result hierarchy, and it provides no quantitative gold for generated names.

## Registered Root Disposition

The run is valid and complete, but the tested local mechanism is contradicted.
It is not adopted. It cannot narrow or replace RQ3, alter the exact thesis,
change the four RQs, or rewrite the positive AgentProf story. No negative result
is authorized for the paper.

The scientific lesson is mechanism-specific. Before testing a more elaborate
task-instance stack, the numeric-index confound must be removed. The smallest
next mechanism preserves all 405 generated responsibility plans and the same
causal evidence, but asks for an explicit `stay` or a switch to one exact
responsibility string; the model never sees or emits numeric indices. That
experiment can distinguish ordinal-interface bias from failure of the task
plan itself without changing benchmark, metric, or paper story. Only if the
semantic interface still fails should the next mechanism add explicit task
instance continuation, suspension, return, and completion. Neither step should
add system fields or heuristic feature terms.
