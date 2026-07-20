# Real Preflight — Step 0058 Experiment 001

## Purpose

The real preflight checked executable wiring for the approved stronger-model
sufficiency experiment. It did not tune the prompt, select a threshold, inspect
human stages before prediction, or change the candidate in response to model
behavior.

## Fixed Runtime

- Backend: local `llama.cpp` server on `127.0.0.1:18184`
- Model alias: `qwen3.6-27b`
- Model artifact: `Qwen.Qwen3.6-27B.f16.gguf.Q4_K_M.gguf`
- SHA-256:
  `f7da7eee0f1ffa280742a293f02052d1f58d3253c9e109c1be8fb0067eb1b3a9`
- Server shape: one slot, 32,768-token context, temperature zero, seed
  `20260720`, reasoning disabled
- Candidate version: `global-task-semantic-segmentation-v3`

The evaluator verified that the server's resolved model path matched the
registered artifact before inference.

## Real Cases

The preflight used the fixed projected-token-longest complete trajectory from
each CodeTrace framework:

- mini-SWE-agent:
  `miniswe-DeepSeek__DeepSeek-V3.2-fix-ocaml-gc-2299ab4a`
- OpenHands:
  `openhands-Anthropic__Claude-Sonnet-4-20250514-Thinking-tune-mjcf-9828b85f`
- SWE-agent:
  `sweagent-OpenAI__GPT-5-instance_internetarchive__openlibrary-d109cc7e6e161170391f98f9a6fa1d02534c18e4-ve8c8d62a2b60610a3c4631f5f23ed866bada9818-54010cb4`
- Terminus2:
  `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-make-doom-for-mips-cc5c8770`

All 4 trajectories, 584 turns, and 584 operations completed. The candidate
used 78,465 prompt tokens and 220 completion tokens in 38.72 seconds.

## Wiring And Representation Checks

- Every operation received exactly one full semantic stack.
- Every stack followed
  `task -> subtask* -> phase/strategy -> semantic action -> object -> result`.
- Agent, model, session, tool, command, raw path, and status were not inserted
  as explicit schema layers.
- Contiguous equal task/subtask paths were assigned one persistent task
  occurrence; lower-suffix changes would not create a new task occurrence.
- The actual four outputs contained one segment and one task occurrence per
  trajectory, so no lower-suffix transition was observed in preflight.
- No parser, context, coverage, cache-identity, or server-identity defect
  occurred. No implementation repair was needed.

## Diagnostic Standard Scores

After predictions were durable, the scorer opened the human stages.

| Method | B³ P | B³ R | B³ F1 | Exact-span F1 | Boundary F1 |
|---|---:|---:|---:|---:|---:|
| Qwen3.6-27B task occurrence | 0.088992 | 1.000000 | 0.163439 | 0.000000 | 0.000000 |
| Multi-resolution recurrence | 0.864882 | 0.382798 | 0.530705 | 0.030651 | 0.221344 |
| Causal Qwen2.5-3B path | 0.665861 | 0.604993 | 0.633970 | 0.011696 | 0.196319 |

The four-task diagnostic bootstrap interval for candidate minus recurrence B³
F1 was `[-0.410835, -0.293605]`. This is not the registered full-population
decision interval.

## Visual Inspection

The representative Terminus2 profile contains 200 operations but one full-width
stack. It therefore cannot expose task progress, repeated attempts, or failure
localization. Its root label also preserves a source-native `Current terminal
state` suffix. Although this is source text rather than an evaluator-added
system layer, it is not a clean concrete-task name and is a warning for the
registered qualitative semantic review.

Artifacts:

- SVG:
  `.agentsight/experiments/rq3-global-task-semantic-segmentation-qwen27b-v1/preflight/score/representative-task-semantic.svg`
- PNG:
  `.agentsight/experiments/rq3-global-task-semantic-segmentation-qwen27b-v1/preflight/score/representative-task-semantic.png`
- Standard-score report:
  `.agentsight/experiments/rq3-global-task-semantic-segmentation-qwen27b-v1/preflight/score/report.md`

## Preflight Disposition

**Proceed without semantic tuning.** The real backend, complete-trajectory
request, grammar, persistent task-occurrence construction, hidden-stage
separation, scorer, and renderer all executed. The observed whole-trajectory
collapse is a scientific result, not a wiring failure. The approved plan
requires all 405 trajectories to complete even when preflight is negative.
