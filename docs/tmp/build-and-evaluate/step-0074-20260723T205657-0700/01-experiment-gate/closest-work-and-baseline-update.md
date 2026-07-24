# RQ3 Closest-Work and Baseline Update

**Timestamp:** 2026-07-23T21:04:00-07:00

**Purpose:** Confirm that the fixed recursive experiment uses the strongest
fair numerical baselines and record newly relevant external hierarchy work
before paper integration.

## Closest external work

### ACT*ONOMY

Gao et al., *How to Interpret Agent Behavior* (arXiv:2605.13625), builds an
automatically applied three-level behavior taxonomy with 10 actions, 46
subactions, and 120 leaves and uses it to compare behavior profiles across
agents and trajectories. It is the closest work on shared semantic behavioral
profiles.

The public release provides the taxonomy and construction/validation corpus,
but not compatible operation-level predictions or stage boundaries for the
405 CodeTrace sessions. Mapping AgentProf names into its taxonomy would hold
AgentProf boundaries fixed and would not execute ACT*ONOMY's pipeline.
Inventing a B-cubed row would therefore be scientifically invalid.

Paper obligation: cite and compare fixed shared taxonomy profiles against
AgentProf's variable-depth responsibility intervals, source-linked additive
measurements, and standard pprof materialization.

Primary sources:

- <https://arxiv.org/abs/2605.13625>
- <https://huggingface.co/datasets/anonymous5999/Act-ONOMY>

### GUIDE

Zhai et al., *GUIDE: Interpretable GUI Agent Evaluation via Hierarchical
Diagnosis* (arXiv:2604.04399), first segments a completed multimodal GUI
trajectory into coherent subtasks, diagnoses each segment, and aggregates an
overall evaluation. It evaluates downstream success classification over three
real benchmark families and reports a model-based usability judgment for
generated subtasks.

GUIDE strongly validates the importance of subtask segmentation for diagnosis,
but its released paper does not expose a compatible CodeTrace
operation-membership or boundary prediction artifact. Its headline accuracy,
precision, recall, and F1 score task-success classification, not segmentation
agreement. Those values cannot be placed in AgentProf's B-cubed table.

Paper obligation: distinguish GUIDE's bounded-context trajectory evaluator
from AgentProf's profiler representation, conserved multi-resource widths,
cross-run operation aggregation, source evidence, and pprof output.

Primary source:

- <https://arxiv.org/abs/2604.04399>

### Classical text segmentation

TextTiling, Bayesian unsupervised topic segmentation, and TopicTiling are
published flat document-segmentation precedents:

- Hearst, *TextTiling*, Computational Linguistics 1997:
  <https://aclanthology.org/J97-1003/>
- Eisenstein and Barzilay, *Bayesian Unsupervised Topic Segmentation*, EMNLP
  2008: <https://aclanthology.org/D08-1035/>
- Riedl and Biemann, *TopicTiling*, ACL SRW 2012:
  <https://aclanthology.org/W12-3307/>

They establish lexical/topic cohesion as a legitimate generic segmentation
family. They are not added as a rushed numerical row here: applying them would
require a new text projection plus window, topic-count, or segmentation-prior
choices, would output flat topical passages rather than nested task
responsibilities, and would not preserve the same source-operation information
boundary without a separately reviewed adapter. Such a new baseline is
eligible only if a future reviewer shows that it can change the paper-level
decision; it is not necessary to complete the already-fixed experiment.

## Numerical baseline set

The complete score must include:

1. **Multi-resolution recurrence:** strongest deterministic same-input
   constructor and primary incumbent.
2. **Native source tree:** tests whether existing phase/action/raw-action
   hierarchy is sufficient.
3. **Source-native turn:** exposes the high-precision fragmentation endpoint.
4. **Causal Qwen2.5-3B:** complete prior automatic model backend on the same
   population, supplied through its fixed score rows.
5. **One-shot Qwen3.6-27B and raw online Qwen2.5-3B:** retained mechanism
   controls showing whole-session collapse and near-turn-singleton
   fragmentation; they need not duplicate every table row if their complete
   degeneracy statistics are stated.

All scored methods use the same 20,866 operations and official stages.
Ordinary operation-level B-cubed F1 remains primary. Exact adjacent-boundary
F1, B-cubed precision/recall, group count, singleton fraction, and
per-framework rows explain fragmentation. No custom weighted metric or
gold-driven threshold is added.

## Decision

The numerical comparison is strong and fair for the fixed experiment. The
external-work gap is a citation/capability-comparison obligation, not
authorization to fabricate incompatible results or postpone the complete run.
