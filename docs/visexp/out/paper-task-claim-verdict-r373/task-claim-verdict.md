# R373 Task-Level Claim Verdict

Status: `pass`

R373 summarizes existing hidden-label artifacts into one task-level verdict matrix. It is not a new profiler run.

## Summary

- `tasks`: 6
- `datasets`: 4
- `operations`: 34539
- `positives`: 3699
- `ap_beats_flat_tasks`: 6
- `top5_work_beats_flat_tasks`: 6
- `top5_recall_beats_fixed_tasks`: 5
- `budget30_recall_beats_fixed_tasks`: 4
- `fewer_groups_than_fixed_tasks`: 4
- `fixed_first_positive_counterpoint_tasks`: 4
- `actionability_supported_tasks`: 6
- `supports_with_counterpoints_tasks`: 6
- `r354_accepted_patches`: 5/6
- `r358_boundary_repair`: True

## Verdict Rows

| Task | AP delta vs flat | Work | R@5 delta vs fixed | Group delta | Actionability | Verdict |
|---|---:|---:|---:|---:|---|---|
| agentreward_looping | 0.1894 | 0.4938 | 0.4127 | 11 | accept_patch | supports_with_counterpoints |
| agentreward_side_effect | 0.1208 | 0.1454 | 0.1139 | 11 | accept_patch | supports_with_counterpoints |
| satraj_unsafe | 0.3423 | 0.042 | 0.2042 | -108 | accept_patch | supports_with_counterpoints |
| agentnet_incorrect_step | 0.0292 | 0.0014 | -0.0092 | -546 | accept_patch | supports_with_counterpoints |
| agentnet_redundant_step | 0.0147 | 0.0089 | 0.0054 | -289 | accept_patch | supports_with_counterpoints |
| osworld_group_start | 0.0349 | 0.4074 | 0.3534 | -147 | reject_patch_or_needs_new_mapping | supports_with_counterpoints |

## Checks

| Check | Passed | Detail |
|---|---:|---|
| upstream_artifacts_pass | True | R320/R354/R355/R358/R365 are available and pass or record no-network provenance. |
| six_task_rows | True | rows=6 |
| flat_work_support_all_tasks | True | AP wins vs flat=6/6; top-5 work wins vs flat=6/6 |
| fixed_session_tradeoff_visible | True | top5 recall wins=5/6; fewer groups=4/6; fixed first-positive counterpoints=4/6 |
| actionability_all_tasks | True | actionability-supported=6/6; R354 accepted=5/6; R358 boundary repair=True |
| oracle_depth_not_ignored | True | Every task has at least one oracle-depth row where operation-stack improves fixed-session budget-30 positive-unit recall. |
| non_claims_preserved | True | Existing paper text keeps human utility, automatic boundary discovery, metric dominance, and ecosystem compatibility out of scope. |
| paper_mentions_r373 | True | Both papers and the evaluation ledger mention the task-level verdict synthesis. |
| no_new_data_or_profiler_rerun | True | R373 reads existing tracked artifacts only; it does not sync data or invoke agentpprof. |
