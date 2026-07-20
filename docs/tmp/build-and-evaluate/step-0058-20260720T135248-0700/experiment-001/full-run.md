# Full Run — Step 0058 Experiment 001

## Registered Candidate

The full run executed the approved stronger-model sufficiency test without
changing the Step 0057 prompt, output grammar, visible source reconstruction,
temperature, seed, context, workload, baselines, or standard metrics. The only
candidate changes were the fixed Qwen3.6-27B checkpoint and the corrected
interpretation of contiguous equal task/subtask paths as one persistent task
occurrence.

The full semantic stack remained:

```text
concrete task -> nested subtask* -> phase/strategy
              -> semantic action -> operation object -> result
```

Only the persistent `concrete task -> nested subtask*` occurrence was compared
with flat CodeTrace human stages. The complete stack was retained for the
registered qualitative semantic review.

## Fixed Runtime And Model Identity

- Model alias: `qwen3.6-27b`
- Model artifact: local Qwen3.6-27B Q4_K_M GGUF
- SHA-256:
  `f7da7eee0f1ffa280742a293f02052d1f58d3253c9e109c1be8fb0067eb1b3a9`
- Server: one `llama.cpp` slot, 32,768-token context, reasoning disabled,
  temperature zero, seed `20260720`
- Candidate implementation:
  `script/rq3_global_task_semantic_segmentation_eval.py`
- Candidate version: `global-task-semantic-segmentation-v3`

The evaluator checked the server model path against the registered artifact.
Per-session cache reuse required the exact algorithm, archive, model, model
SHA, and request identity.

## Complete Execution

The run completed:

- 405/405 real failed CodeTraceBench trajectories;
- 17,148/17,148 source-native turns;
- 20,866/20,866 operations;
- 4/4 frameworks: OpenHands 213, SWE-agent 28, Terminus2 93, and
  mini-SWE-agent 71;
- 2,948 human stage occurrences across 251 task clusters, opened only after
  all candidate assignments were durable.

Inference consumed 2,869,593 prompt tokens and 23,804 completion tokens,
2,893,397 total. Wall time was 2,361.36 seconds.

Every operation was assigned exactly once and every emitted stack followed the
six-part schema. The model nevertheless emitted exactly one segment and one
task occurrence for every session:

- total semantic segments: 405;
- sessions with an internal boundary: 0;
- total persistent task occurrences: 405;
- subtask depth 0: 43 segments;
- subtask depth 1: 362 segments;
- maximum subtask depth: 1;
- command-primitive-shaped semantic actions: 0.

Thus the stronger checkpoint produced readable open-vocabulary summaries but
did not produce temporal task decomposition.

## Standard Metrics

| Method | B³ P | B³ R | B³ F1 | Exact-span F1 | Boundary F1 |
|---|---:|---:|---:|---:|---:|
| Qwen3.6-27B persistent task occurrence | 0.173563 | 1.000000 | 0.295788 | 0.000000 | 0.000000 |
| Multi-resolution recurrence | 0.782026 | 0.575029 | 0.662740 | 0.056435 | 0.265571 |
| Causal Qwen2.5-3B task path | 0.735681 | 0.581999 | 0.649878 | 0.049501 | 0.256606 |

The candidate predicted 405 groups against 2,948 human stage occurrences.
Its perfect B³ recall is the mathematical consequence of placing every
operation in its session's single group; the corresponding precision 0.1736,
zero detected boundaries, and zero exact spans show that it did not recover
the task-progress partition.

The registered 10,000-resample paired task-cluster bootstrap gave:

- candidate minus multi-resolution recurrence B³ F1:
  `[-0.381647, -0.350845]`, positive fraction 0;
- candidate minus causal Qwen2.5-3B B³ F1:
  `[-0.373469, -0.332215]`, positive fraction 0.

The registered quantitative decision is therefore
**contradicted—not adopted**.

## Representative Full-Stack Profile

The fixed selection rule chose the complete selected session with the maximum
operation count, lexical tie-break:

`terminus2-DeepSeek__DeepSeek-V3.2-git-multibranch-c063fb97`

It contains 275 operations and renders one six-level, full-width stack. The
labels are superficially task-centered—setting up a Git server, installing
dependencies, creating users—but the profile cannot reveal progress,
repetition, failure, abandonment, or strategy changes because it contains no
temporal task boundary. Its root also retains a source-native `Current terminal
state` suffix, so it is not a clean concrete-task frame.

Artifacts:

- SVG:
  `.agentsight/experiments/rq3-global-task-semantic-segmentation-qwen27b-v1/full/score/representative-task-semantic.svg`
- PNG:
  `.agentsight/experiments/rq3-global-task-semantic-segmentation-qwen27b-v1/full/score/representative-task-semantic.png`
- Folded stacks:
  `.agentsight/experiments/rq3-global-task-semantic-segmentation-qwen27b-v1/full/score/representative-task-semantic.folded`
- Machine-readable inference summary:
  `.agentsight/experiments/rq3-global-task-semantic-segmentation-qwen27b-v1/full/inference-summary.json`
- Machine-readable score summary:
  `.agentsight/experiments/rq3-global-task-semantic-segmentation-qwen27b-v1/full/score/summary.json`

## Scientific Interpretation

This experiment rejects the fixed global one-shot interface for task-progress
construction on the declared workload. It does not show that Qwen3.6-27B is
generally worse, that parameter count is irrelevant, or that semantic task
stacks are impossible. The 3B and 27B checkpoints differ in more than capacity.

The shared behavior of both tested checkpoints is more specific and more
useful: when one grammar allows a single final segment to cover a complete
trajectory, both checkpoints choose that shortest legal whole-trajectory
summary for all 405 sessions despite the instruction to expose distinct work.
Increasing checkpoint strength alone does not repair that interface.

The result does not narrow the thesis, paper story, four RQs, or positive
hypothesis. It rejects one constructor. The next scientifically distinct
candidate should change the mechanism that caused the common bottleneck—for
example, maintain a live task stack and classify each next semantic operation
as keep, push, or pop—rather than repeat a global prompt with another model,
benchmark, score, or cutoff.

No paper file, shared skill, `docs/idea-story.md`, or
`docs/user-instruction.md` was changed by this experiment.
