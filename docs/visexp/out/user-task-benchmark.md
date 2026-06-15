# User Task Benchmark Bundle

This bundle defines B4/C5 pilot analysis tasks and answer keys. It is not a human-study result.

- Tasks: 14.
- Primary utility tasks: 8.
- Limitation/comprehension tasks: 6.
- Participant packets: 70.
- Pilot assignment rows: 70.
- Conditions: trace-tree, span-duration, flat-summary, nonsemantic-stack, semantic-stack.

## Tasks

- UT01 (find-hidden-semantic-mixing): Top Nonsemantic System Mixing.
- UT02 (compare-semantic-axis): Prompt Axis Contribution.
- UT03 (compare-semantic-axis): Session Versus Prompt Axis.
- UT04 (find-repeated-heavy-behavior): Heaviest Repeated Semantic Stack.
- UT05 (find-path-effect-provenance): Heaviest Path-Specific Read.
- UT06 (explain-command-effect-mixing): Cargo Test Semantic Split.
- UT07 (explain-command-effect-mixing): Python Process Semantic Split.
- UT08 (explain-command-effect-mixing): Docker Process Semantic Split.
- UT09 (compare-flat-vs-semantic): Flat Git Read Baseline Failure.
- UT10 (find-token-hotspot): Largest Token Region.
- UT11 (avoid-axis-overclaim): LLM-Call Axis Boundary.
- UT12 (check-exact-lineage): Exact-Lineage Negative Controls.
- UT13 (avoid-lineage-overclaim): Raw Join Versus Scoped Recall.
- UT14 (avoid-tag-overclaim): 3B Tag Stability Boundary.

## Claim Boundary

- The bundle makes the C5 pilot executable by defining questions, condition packets, assignments, and answer keys.
- `user-task-response-template.csv` defines the response schema consumed by `score_user_task_results.py`.
- Participants should see only their assigned condition packet; oracle sources and answer keys are for graders.
- Every task's five condition excerpts share one `slice_id`; this checks the same-event-slice baseline-fairness requirement for the pilot packet.
- C5 remains unsupported until participant responses are collected and scored.
