# R348 Action-Counterfactual Audit

R348 asks whether the profiler's actionability cards correspond to measurable
counterfactual changes in already-scored visible policies. It does not fetch,
sync, create, or relabel datasets, and it does not turn hidden labels into a
deployment selector.

## Summary

- Overall: pass.
- Objective rows: 36.
- Non-default action rows: 27.
- Rows where the best policy is visible and non-oracle: 36.
- Objective rows requiring a view change: 25.
- Objective rows requiring operation-stack ranker/depth tuning: 2.
- Tasks with at least three action classes: 6.
- Median default regret: 0.14475.

## Action Classes

| Action class | Rows | Tasks | Median gain | Max gain |
|---|---:|---:|---:|---:|
| drill_down_fixed_session | 7 | 3 | 0.6021 | 16.0 |
| keep_default_operation_stack | 9 | 5 | 0.0 | 0.0 |
| retune_operation_stack_ranker | 2 | 2 | 0.0655 | 0.127 |
| use_dataset_native_hierarchy | 5 | 3 | 0.2723 | 61.0 |
| use_flat_full_recall_counterpoint | 7 | 6 | 141.0 | 288.0 |
| use_raw_action_mapping_counterpoint | 6 | 3 | 1.1022 | 185.0 |

## Task Cards

| Task | Non-default rows | Action classes | Case counterpoints |
|---|---:|---|---|
| agentnet_incorrect_step | 3 | keep_default_operation_stack; use_flat_full_recall_counterpoint; use_raw_action_mapping_counterpoint | top5_recall->flat:width |
| agentnet_redundant_step | 4 | keep_default_operation_stack; retune_operation_stack_ranker; use_flat_full_recall_counterpoint; use_raw_action_mapping_counterpoint | top5_recall->flat:width; first_positive->fixed_session:query_aware |
| agentreward_looping | 4 | keep_default_operation_stack; use_dataset_native_hierarchy; use_flat_full_recall_counterpoint; use_raw_action_mapping_counterpoint | top5_recall->flat:width; first_positive->raw_action_stack:query_aware |
| agentreward_side_effect | 5 | drill_down_fixed_session; keep_default_operation_stack; use_flat_full_recall_counterpoint | top5_recall->flat:width; top5_lift->raw_action_stack:query_aware |
| osworld_group_start | 6 | drill_down_fixed_session; retune_operation_stack_ranker; use_dataset_native_hierarchy; use_flat_full_recall_counterpoint | top5_recall->flat:width; top5_lift->fixed_session:query_aware; first_positive->fixed_session:query_aware |
| satraj_unsafe | 5 | drill_down_fixed_session; keep_default_operation_stack; use_dataset_native_hierarchy; use_flat_full_recall_counterpoint | top5_recall->flat:width; first_positive->fixed_session:query_aware |
