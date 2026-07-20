# Experiment 001 Plan Review 2

- reviewed: 2026-07-20T02:44:00-07:00
- reviewer: independent subagent after rereading `research-experiment-design`
- verdict: **REVISE**

## Blocking Findings

1. CodeTraceBench's human intervals justify stage-partition fidelity, not the
   semantic correctness of generated task/subtask names. The hypothesis and
   quantitative interpretation must say `human workflow-stage spans`; generated
   responsibility names may remain qualitative under the larger task-centric
   target.
2. The 405 trajectories contain repeated executions of 251 underlying tasks.
   A trajectory bootstrap treats correlated executions as independent. Both
   comparisons must use the already established paired task-cluster bootstrap.
3. A character budget cannot guarantee the declared Qwen token limit on
   code-heavy traces. Projection must use the retained model tokenizer, retain
   every operation, preflight the actual worst-token trajectory, and give
   runnable server/evaluator commands and model/runtime identifiers.

## Root Response

Accepted. Revision 2 makes unlabeled human workflow-stage fidelity the sole
quantitative construct while leaving the larger hierarchy unchanged. It uses
task-cluster bootstrap, exact tokenizer-based projection, worst-token real
preflight, and concrete commands. These are scientific validity and execution
repairs, not additional gates or new experiments.
