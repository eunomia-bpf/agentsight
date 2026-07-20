# Experiment 004 — Semantic-Stack Flame-Graph Inspection

**Status:** complete diagnostic visualization  
**Scientific role:** explain the fixed complete result; no paper evidence change

## Question

Does the completed Qwen 3B prediction visibly recover a task-centered hierarchy,
and what exactly does support-at-least-two contraction change?

## Fixed input

- Complete, already-scored Experiment 004 artifacts; no inference rerun.
- Representative maximum-depth trajectory:
  `openhands-Anthropic__Claude-Sonnet-4-20250514-Thinking-3d-model-format-legacy-7498555b`.
- Public task: `3d model format legacy`.
- 95 operations; Qwen generated depth reaches six, or seven plotted levels after
  adding the immutable task root.
- Width is unweighted operation count. The official human stage is loaded only
  in the fourth diagnostic panel and did not affect either Qwen panel.

## Artifact

- Generator: `script/plot_qwen_semantic_stack_flamegraph.py`.
- Vector figure: `figures/qwen-task-stack-example.pdf`.
- Display figure: `figures/qwen-task-stack-example.png`.

The four aligned panels show (a) the raw active Qwen stack, (b) the fixed
support-at-least-two contraction, (c) the registered multi-resolution recurrence
comparator, and (d) the official flat human-stage partition. Each operation has
unit width; nesting height is active stack depth.

## Readout

The raw Qwen stack is genuinely variable-depth, so stack legality and uncapped
depth are not the failure. It combines a trajectory-wide early ancestor
(`explore project structure`) with many one-operation leaves. Contraction removes
the transient leaves but preserves the over-wide ancestor and a few intermittent
descendants, which does not reconstruct the six long human-stage intervals.

This supports the complete quantitative diagnosis: the fixed policy creates
almost one new frame per operation, while minimum temporal support alone cannot
identify semantic continuity. It also sharpens the next mechanism target:
`concrete task → subtask → stage/strategy → semantic action → object → result`,
with agent/model/tool/status as display dimensions and commands/files as evidence,
not primary hierarchy levels. The figure is diagnostic research provenance and
must not be inserted into the positive-result paper.
