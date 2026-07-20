# Experiment 004 Source-Only Implementation Review

Act as a read-only senior reviewer. Do not edit files and do not open the
official CodeTraceBench stage manifest or any score output. Read:

- `experiment-004/experiment-plan.md` and `experiment-004/plan-review.md`;
- `experiment-003/real-preflight-v2.3.md`;
- `script/rq3_qwen_semantic_task_stack_eval.py`;
- the full inference summary under
  `.agentsight/experiments/rq3-qwen3b-semantic-task-stack-v2/full/inference/`.

Audit the inference cache metadata and source-only contraction implementation.
In particular, independently check coverage, transition legality and replay,
model/seed/version provenance, immutable-root behavior, support counting,
nearest-retained-ancestor assignment, absence of a depth cap, deterministic
one-leaf-per-operation coverage, and whether contraction is materialized before
official stages are loaded. You may run read-only commands and source-only
calculations. Do not calculate B-cubed or boundary scores.

Return `APPROVE` or `REVISE`, list only necessary must-fix items, and state
whether the registered scorer may now open the official stages exactly once.

