# Operation Mechanism Attribution Audit R341

R341 reuses existing labeled-trace results. It does not fetch, sync, create, or relabel datasets.
It asks whether actionability is visible as concrete mechanism attribution rather than only as headline wins.

## Primary Findings

- R341 audits 36 objective-task recommendations and 96 held-out transfer decisions using only tracked R320/R335/R336/R340 artifacts.
- All 36/36 objective rows have a concrete optimization action tied to visible mechanism labels; the mechanism labels cover critical_rank_features=4, fixed_session_first_positive_counterpoint=4, mapping_helps=2, mapping_hurts=2, misleading_feature_risk=2, query_aware_ranker=3, raw_action_or_baseline_counterpoint=4, stack_depth_tradeoff=6, transfer_policy_signal=6.
- The best visible policy is not the default operation-stack view on 27/36 objective rows, so the actionable claim is knob selection and counterpoint exposure rather than a universal default hierarchy.
- Transfer misses are classifiable rather than opaque: 34/96 held-out decisions are outside tolerance, with classes dataset_native_counterpoint=6, fixed_session_counterpoint=6, operation_stack_overselected=1, ranker_mismatch_same_view=2, raw_action_counterpoint=1, selector_missed_good_default=14, view_mismatch_operation_stack_best=4.
- 32/34 transfer misses change view relative to the held-out best and 26/34 change ranker, identifying whether to adjust stack shape or ranking policy.

## Summary

- Objective rows: 36.
- Actionable objective rows: 36/36.
- Non-default best objective rows: 27/36.
- Transfer misses: 34/96.
- Transfer miss classes: dataset_native_counterpoint=6, fixed_session_counterpoint=6, operation_stack_overselected=1, ranker_mismatch_same_view=2, raw_action_counterpoint=1, selector_missed_good_default=14, view_mismatch_operation_stack_best=4.
- Mechanism task counts: critical_rank_features=4, fixed_session_first_positive_counterpoint=4, mapping_helps=2, mapping_hurts=2, misleading_feature_risk=2, query_aware_ranker=3, raw_action_or_baseline_counterpoint=4, stack_depth_tradeoff=6, transfer_policy_signal=6.

## Objective Tradeoff Classes

| Class | Count |
|---|---:|
| dataset_native_boundary_or_task_hierarchy | 5 |
| default_operation_stack_suffices | 9 |
| fixed_session_drilldown_counterpoint | 5 |
| fixed_session_first_positive_counterpoint | 2 |
| flat_summary_counterpoint | 7 |
| operation_stack_ranker_or_depth_tuning | 2 |
| raw_action_mapping_counterpoint | 6 |

## Transfer Miss Classes

| Class | Count |
|---|---:|
| dataset_native_counterpoint | 6 |
| fixed_session_counterpoint | 6 |
| operation_stack_overselected | 1 |
| ranker_mismatch_same_view | 2 |
| raw_action_counterpoint | 1 |
| selector_missed_good_default | 14 |
| view_mismatch_operation_stack_best | 4 |

## Non-Claims

- no new datasets, dataset sync, dataset creation, or relabeling
- no human or agent analyst productivity, accuracy, or time-to-answer claim
- no automatic universal policy selector
- no operation-stack dominance on every objective or cost metric
- no profiler abstraction beyond operation and operation stack
