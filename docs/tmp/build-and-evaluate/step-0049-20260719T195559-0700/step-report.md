# Step 0049 Detailed Report

- step: `step-0049-20260719T195559-0700`
- outer state entered: EXPERIMENT
- gates completed: EXPERIMENT, WRITE, REVIEW
- final route: EXPERIMENT
- paper thesis: **Agent observability needs profiling, not only debugging.**
- RQs preserved: attribution, problem correspondence/localization, tag
  accuracy, and cost

## Step Objective

Improve the operation-stack constructor using already collected real agent
trajectories, carry supported evidence into the current paper without changing
its thesis or four RQs, and then obtain a complete adversarial paper review that
searches external closest work and selects the next highest-value experiment.

## EXPERIMENT Gate

### Experiment 001: multi-resolution recurrence

The admitted RQ3 hypothesis asked whether adding non-redundant visible action
detail to the existing label-free recurrence constructor improves ordinary
unweighted per-operation B-cubed F1 on the complete CodeTraceBench population,
while falling back exactly when detail is absent.

The full run covered 405 CodeTraceBench trajectories, 20,866 operations, 2,948
human stages, 251 task clusters, and four agent frameworks. The candidate
reached B-cubed F1 0.662740 versus 0.649173 for coarse recurrence, a delta of
+0.013567. The paired 10,000-resample task-cluster bootstrap interval was
[+0.008712, +0.018043], and all four framework deltas were positive. On
OSWorld-Human, where no non-redundant detail exists, the result fell back
exactly to the coarse constructor. An independent reviewer recomputed the
primary numbers and returned `SUPPORTED / ADOPT` for this bounded mechanism.

The accompanying boundary-F1 decline was retained as a diagnostic and did not
replace the registered standard primary metric. This experiment does not by
itself answer all of RQ3.

### Experiments 002--004: variable-depth Qwen transition policy

Experiment 002 tested an unconstrained variable-depth semantic stack maintained
by local Qwen2.5-3B. It was invalid and unscored because the grammar admitted an
unbounded list of new frames. Experiment 003 simplified the transition to
arbitrary multi-pop plus zero or one new frame. Two complete-population attempts
were stopped unscored by output-language defects: first unbounded whitespace,
then an independently admitted empty-stack transition.

Experiment 004 isolated the final V2.3 output-language repair and completed all
405 trajectories and 20,866 operations before scoring. The legal generated
depth ranged from 1 to 6, but the model created a new frame for nearly every
operation. Source-only singleton contraction reduced 20,857 generated frames
to 1,690 effective groups, yet reached only B-cubed F1 0.433835 and boundary F1
0.109949, versus 0.662740 and 0.265571 for multi-resolution recurrence. The
paired task-cluster bootstrap interval for candidate minus comparator was
[-0.246012, -0.210910]. Grok independently reconstructed the full result and
returned PASS for the registered `contradicted` outcome.

This contradiction applies only to the fixed Qwen 3B per-operation transition
policy plus minimum-support contraction. It does not reject variable-depth
task hierarchies, the paper thesis, or the four RQs. It is retained in research
provenance and not promoted as a negative paper result.

### Experiment-gate lesson

The Qwen branch spent too much effort on output-contract repairs after
operation-level over-segmentation was already visible. The mechanism also asked
one operation at a time to invent untyped free-form hierarchy. The next
mechanism must instead recover a typed task responsibility structure and must
be tested against independently annotated hierarchy rather than runtime-field
grouping.

## WRITE Gate

The paper completed all twelve `iter-refine-writing` rounds. The revisions
preserved the exact thesis, four RQs, positive evidence, terminology, numbers,
and citation meaning. The final meaning-preservation report found no scientific
contract drift.

This was nevertheless an orchestration-efficiency deviation: the full WRITE
loop ran inside the same BUILD_AND_EVALUATE step before the milestone REVIEW,
instead of using a smaller evidence-owned update and reserving full refinement
for a stable milestone. The edits are scientifically valid and are not
reverted; the deviation is recorded so a later cycle does not repeat the cost.

## REVIEW Gate

Two independent completed full-paper reviews were obtained:

- Grok 4.5: 4/10, Reject, confidence 4;
- Codex: 3/10, Reject, confidence 4.

A Claude Opus attempt produced no review and was explicitly excluded from the
completed-review count. Both completed reviews preserved the thesis and four
RQs. Their shared strongest objection is not wording: the present operation
stack evidence still looks too close to field grouping or post-hoc clustering,
and the paper has not yet shown that an automatically recovered hierarchy
corresponds to task responsibility strongly enough to support the claimed
profiling view.

The external search added GUIDE as the closest task-semantic trajectory method
and Magpie as a strong cross-layer systems ancestor. TaskBench, CRAB,
WorkArena++, AgiBotWorld2026, HABIT, AndroidControl, and AgentNet were inspected
as possible public hierarchy-bearing assets. Their annotation and input
limitations are documented rather than silently treated as equivalent gold.

The REVIEW verdict is `REJECT at current milestone; route to EXPERIMENT`.
Review completion does not require zero objections.

## User-Intent And Semantic-Contract Update

The latest instruction is recorded verbatim in `docs/user-instruction.md`.
The design now distinguishes a supported runtime-field projection from the
paper-level target. The main hierarchy is:

```text
concrete task -> subtask (possibly nested) -> phase/strategy
              -> semantic action -> operation object -> result
```

Agent, model, session, tool, command, path, and status are metadata, filters,
colors, side details, or bottom-level evidence. Event count, time, tokens, and
source-linked effects are additive widths. A valid task-semantic flame graph
must expose resource allocation by subtask, repetition, productive versus
failed or abandoned work, and differences in task decomposition across agents.

The earlier `project -> task -> phase -> tool -> action -> status` projection
remains a useful artifact capability and baseline, but is no longer described
as the paper-level task-semantic target.

## Provenance Correction

`chronology-correction.md` reconstructs the causal order of Experiments 003 and
004 without inventing missing wall-clock timestamps. This corrects report
metadata only; no raw result, metric, or scientific decision changed.

## Final Route And One Next Question

The next gate is EXPERIMENT, scoped to **RQ3 only**:

> Can a typed task-semantic hierarchy built from the same real execution
> evidence recover independently annotated task/subtask structure better than
> runtime-field and matched flat-semantic baselines under standard labeled and
> unlabeled span F1?

This experiment must test only the annotated level actually present in the
selected public asset. It must not invent bespoke gold, combine an RQ1 utility
claim into RQ3, or use flat B-cubed as evidence for an entire nested hierarchy.
The task root is immutable, subtask depth may be uneven, and lower frames are
typed as strategy, semantic action, operation object, and result.

## Files And Artifacts

- experiment reports: `experiment-001/` through `experiment-004/`
- complete writing audit: `write-gate/iter-refine-writing-20260719T234228-0700/`
- full-paper review: `review-gate/milestone-review-001/`
- closest-work and asset search:
  `literature-20260720T014450-0700/search-and-handoff.md`
- chronology repair: `chronology-correction.md`
- current semantic contract: `docs/design.md` and
  `docs/user-instruction.md`

