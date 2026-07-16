# Experiment 002 Plan Revision Disposition

**Revised:** 2026-07-15T21:07:00-07:00
**Input:** independent `REVISE` verdict in `plan-review.md`
**State:** revised; awaiting the same reviewer

Both must-fix items were accepted without changing the experimental cells.

1. The intervention is now named a fixed Qwen3.6-27B backend/artifact
   substitution. Greater capacity is motivation and a plausible explanation,
   not an isolated causal variable, because model generation, training, and
   architecture also differ.
2. The plan now gives the exact llama.cpp and AgentProf command shapes and a
   dedicated `27b/` raw-output directory containing separate preflight, three
   full profiles, and scored summary. Experiment 001 outputs cannot be
   overwritten, and the future result-review inputs are explicit.

No benchmark, split, predictor field, label, description, prompt, grammar,
metric, threshold, repetition, evaluator, or protocol was added or changed.
