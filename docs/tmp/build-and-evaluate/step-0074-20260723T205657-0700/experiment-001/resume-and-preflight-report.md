# Resume and Real-Execution Report

**Timestamp:** 2026-07-23T20:58:00-07:00

**Status:** PASS; complete inference resumed

## Environment

- model: Qwen3.6-27B Q4_K_M;
- model SHA-256:
  `f7da7eee0f1ffa280742a293f02052d1f58d3253c9e109c1be8fb0067eb1b3a9`;
- runtime: llama.cpp build 9870 (`2d973636e`);
- server: one 32,768-token slot, reasoning disabled, temperature zero through
  the fixed request;
- accelerator: NVIDIA GeForce RTX 5090;
- input: all 405 CodeTrace sessions and 20,866 operations;
- ignored output root:
  `.agentsight/experiments/rq3-recursive-operation-segmentation-v1/full/`.

## Cache and interruption audit

The existing session directory contained 259 paths. Exactly 256 parsed
nonempty fixed-v4 results and matched the current model, source projection,
prompt/grammar, seed, and algorithm identity. Exactly three files were zero
bytes, a normal signature of interruption during a non-atomic write. They
could not contain a prediction, call response, or mark and were deleted. No
nonempty cache was removed or rewritten.

The inference identity remains
`73dd70e987d6f573bfaab2c13e4c91f8294cdc4a5ccd176e2d2c970ad27ae853`
before and after the execution-only correction below.

## Execution-only correction

`run_infer` previously called the server tokenizer for every session to compute
`projected_prompt_tokens`, even in `full` mode. That value is consumed only by
`select_preflight` to choose the longest projected session per framework.
Full mode processes every session in sorted order and never reads the value.

The implementation now performs those tokenizer calls only in `preflight`
mode. This changes no source projection, model prompt, grammar, inference
request, session ordering, cache identity, prediction, mark, metric, or
decision. It removes avoidable pre-execution work from the complete run and
prevents RQ4 from charging full automatic annotation for a preflight-only
selection feature.

The full runner now also records three direct wall-time components:
source adaptation, the annotation/cache loop, and profile materialization.
These are observation-only timers around existing phases. They do not enter
the inference identity or RQ3 decision and are required to avoid presenting
the fixed-mark replay time as end-to-end automatic cost.

Validation:

- Python compilation: PASS;
- all 14 focused recursive-backend tests: PASS;
- inference identity before/after: exact match;
- fixed server health: PASS;
- first 50 complete-population source reconstructions after resume: PASS.

## Scientific boundary

No official stage, task cluster, recurrence assignment, prior candidate name,
or score was opened. This report authorizes completing the same fixed full
run; it does not authorize a paper claim or a score-driven algorithm change.
