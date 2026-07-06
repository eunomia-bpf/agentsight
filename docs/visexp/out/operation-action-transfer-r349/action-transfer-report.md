# R349 Held-Out Action-Transfer Audit

R349 maps R340 held-out policy selections to action classes and compares
them against the R348 target-task counterfactual action oracle. It is a
guardrail experiment: metric-tolerance transfer is useful, but exact
action-class transfer is intentionally not promoted to an automatic
selector claim.

## Summary

- Overall: pass.
- R340 transfer decisions: 96.
- Aligned R340/R348 decisions: 60.
- Excluded sequence decisions: 36.
- R348 objective rows not covered by R340 transfer: 6.
- Exact action-class transfer: 7/60.
- Within metric tolerance: 35/60.
- Beats default operation stack: 30/60.
- Default operation stack already within tolerance: 26/60.
- Non-default target rows: 42.
- Non-default target rows with exact action transfer: 2/42.
- Non-default target rows within metric tolerance: 24/42.

## Interpretation

- R349 supports using held-out policy transfer as an automated proxy for
  finding promising diagnostic views/rankers under a metric budget.
- R349 does not support claiming a label-free automatic action selector:
  exact action-class transfer is low, especially when the target best
  action is non-default.
- The paper should frame this as a protocol-sensitivity/actionability
  tradeoff and keep task-specific operation-stack inspection in scope.

## Protocol Summary

| Protocol | Decisions | Action exact | Within tolerance | Beats default |
|---|---:|---:|---:|---:|
| leave_dataset | 30 | 3 | 17 | 15 |
| leave_task | 30 | 4 | 18 | 15 |

## Action Confusion

| Selected action | Best action | Decisions | Within tolerance | Beats default |
|---|---|---:|---:|---:|
| use_flat_full_recall_counterpoint | use_raw_action_mapping_counterpoint | 10 | 10 | 10 |
| use_dataset_native_hierarchy | keep_default_operation_stack | 7 | 4 | 0 |
| use_dataset_native_hierarchy | drill_down_fixed_session | 6 | 0 | 2 |
| use_flat_full_recall_counterpoint | use_dataset_native_hierarchy | 6 | 6 | 6 |
| keep_default_operation_stack | keep_default_operation_stack | 5 | 5 | 0 |
| drill_down_fixed_session | use_dataset_native_hierarchy | 4 | 0 | 0 |
| retune_operation_stack_ranker | drill_down_fixed_session | 4 | 2 | 2 |
| use_flat_full_recall_counterpoint | drill_down_fixed_session | 4 | 2 | 4 |
| drill_down_fixed_session | keep_default_operation_stack | 2 | 0 | 0 |
| keep_default_operation_stack | retune_operation_stack_ranker | 2 | 0 | 0 |
| retune_operation_stack_ranker | keep_default_operation_stack | 2 | 2 | 0 |
| retune_operation_stack_ranker | retune_operation_stack_ranker | 2 | 2 | 2 |
| use_raw_action_mapping_counterpoint | keep_default_operation_stack | 2 | 0 | 0 |
| use_raw_action_mapping_counterpoint | use_flat_full_recall_counterpoint | 2 | 2 | 2 |
| drill_down_fixed_session | use_raw_action_mapping_counterpoint | 1 | 0 | 1 |
| retune_operation_stack_ranker | use_raw_action_mapping_counterpoint | 1 | 0 | 1 |
