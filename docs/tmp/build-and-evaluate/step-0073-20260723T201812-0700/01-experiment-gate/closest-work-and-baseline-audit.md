# RQ3 Closest-Work and Baseline Audit

**Timestamp:** 2026-07-23T20:18:12-07:00
**Parent:** Step 0073 entry
**Objective:** Select real, comparable baselines for the fixed-instruction
follow-on structure test and identify external hierarchy work that must shape
the paper.

## Primary external finding

ACT*ONOMY, *How to Interpret Agent Behavior* (arXiv:2605.13625, May 2026), is
the closest newly identified semantic-profile work. It supplies:

- a fixed three-level taxonomy with 10 actions, 46 subactions, and 120 leaves;
- an automated quote-grounded trajectory-analysis pipeline;
- cross-agent and within-agent behavior profiles; and
- a public taxonomy/corpus release.

It is a serious novelty and design baseline. AgentProf must distinguish
variable-depth responsibility intervals, source-trace composition, conserved
additive measures, and standard pprof replay from ACT*ONOMY's shared fixed
action taxonomy.

## Why ACT*ONOMY is not a numerical row in this experiment

The public release contains the taxonomy, 664 construction-set behavioral
sentences, a 116-sentence held-out validation set, codebook evidence, and the
nested taxonomy. It does not publish complete operation-level predictions for
the 405 CodeTrace sessions or a compatible stage-boundary output. Reclassifying
AgentProf's already generated names into ACT*ONOMY categories would hold A2
boundaries fixed and would not test ACT*ONOMY's trajectory pipeline. Running a
new model adapter over the target population would change the automatic
backend as well as the representation.

Therefore, manufacturing an ACT*ONOMY B-cubed row here would not be a fair
baseline. It enters the paper as the closest capability/claim comparison and
motivates a future native artifact comparison if its trajectory outputs become
available.

## Numerical baselines selected

1. **Multi-resolution recurrence (primary):** the strongest adopted non-LLM
   constructor on the same operations. It uses visible action recurrence,
   reads no official stages, and is the existing headline comparator.
2. **Native source tree (secondary):** phase/action/raw-action hierarchy with
   adjacent identical paths contracted. It tests whether any source-native
   structure suffices.
3. **Source-native turn (diagnostic):** one occurrence per native turn. It
   exposes the fragmentation lower bound but is not promoted to a headline
   baseline.

Raw-action B-cubed remains a published full-population context value but is
not reconstructed for this subset merely to add another weaker row. The
primary scientific decision is A2 versus recurrence.

## Decision

Run one complete follow-on-only comparison using the existing fixed predictions
and standard metrics. Do not change names, prompts, fields, cutoffs, scores,
datasets, or backends. The experiment tests generality across the later
independent annotation batches, not nested-topology or literal-name accuracy.

## Sources

- Gao et al., *How to Interpret Agent Behavior*, arXiv:2605.13625.
- ACT*ONOMY public corpus and taxonomy:
  `https://huggingface.co/datasets/anonymous5999/Act-ONOMY`.
- Existing complete CodeTrace inputs and baseline assignments under
  `.agentsight/experiments/a2-canonical-v1/` and
  `.agentsight/experiments/rq3-multiresolution-recurrence-v1/`.
