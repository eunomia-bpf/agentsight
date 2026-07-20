# Experiment 001 Plan Review 4

- reviewed: 2026-07-20T03:18:00-07:00
- reviewer: independent subagent after rereading `research-experiment-design`
- verdict: **REVISE**

## Judgment

The causal sequential repair is scientifically justified and minimal. The
source-only preflight exposed deterministic position cycling before any gold
was opened, while a fixed goal plan prevents the earlier per-operation policy
from inventing unlimited candidate frames.

## Blocking Repairs

1. Fix both output languages exactly. Specify the candidate's one-index JSON and
   the baseline's exact `stay` or `switch + new label` JSON, including label
   syntax, length, persistence, and rejection of system-field labels. State the
   planner's larger output limit separately from causal-call limits.
2. Remove the stale statement that Attempt 3 preflight scores stages. Stage
   scoring begins only after all 405 predictions are fixed. Change the evaluator
   algorithm/cache version and replace the full-trajectory implementation before
   the fresh third preflight.

Population, metrics, task-cluster bootstrap, thesis, four RQs, and task-centric
semantic contract remain valid.
