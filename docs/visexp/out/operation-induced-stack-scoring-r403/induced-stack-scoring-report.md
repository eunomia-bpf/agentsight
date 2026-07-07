# R403 Induced Stack Scoring

This run scores Rust-induced task stacks on the existing R300/R320 hidden-label tasks. It is a mechanism ablation for E2/E3, not a new dataset and not a human-utility study.

## Policy Summary

| Policy | Tasks | Hidden | Median AP | Median R@5 | Median work@5 | Median budget30 recall | Median groups |
|---|---:|---:|---:|---:|---:|---:|---:|
| dataset_native:query_aware | 6 | False | 0.3571 | 0.8665 | 0.8539 | 0.3377 | 7.5 |
| fixed_session:query_aware | 6 | False | 0.3476 | 0.0233 | 0.0163 | 0.3559 | 285.0 |
| flat:width | 6 | False | 0.1678 | 1.0 | 1.0 | 0.0 | 1.0 |
| induced_task_stack:oracle_upper_bound | 6 | True | 0.3963 | 0.7083 | 0.492 | 0.3783 | 15.5 |
| induced_task_stack:query_aware | 6 | False | 0.2972 | 0.3215 | 0.3143 | 0.2941 | 15.5 |
| induced_task_stack:visible_risk | 6 | False | 0.1687 | 0.3608 | 0.3745 | 0.2809 | 15.5 |
| induced_task_stack:width | 6 | False | 0.2141 | 0.7476 | 0.6763 | 0.3412 | 15.5 |
| operation_stack:oracle_upper_bound | 6 | True | 0.5992 | 0.3004 | 0.044 | 0.564 | 157.5 |
| operation_stack:query_aware | 6 | False | 0.3116 | 0.188 | 0.0937 | 0.39 | 157.5 |
| operation_stack:width | 6 | False | 0.161 | 0.4746 | 0.5424 | 0.3372 | 157.5 |
| raw_action_stack:query_aware | 6 | False | 0.2743 | 0.2441 | 0.1507 | 0.3325 | 24.5 |

## Main Interpretation

- The induced task-stack view gives a label-scored automatic-boundary probe: median top-5 work is 0.3143 versus 1.0 for flat summaries, with median groups 15.5 versus 285.0 for fixed-session drilldown. All six real-trace tasks produce variable-depth recursive stacks rather than a fixed field-order tree.
- The hand-configured operation stack remains the stronger main E2 policy when median AP is compared (0.3116 versus 0.2972), so induction is evidence for configurable recursive folding rather than a replacement for task-specific profile specs.

## Checks

- uses_tracked_r300_source: `True`
- uses_tracked_r320_baselines: `True`
- covers_all_six_tasks: `True`
- all_rust_profiles_use_induction: `True`
- rust_stack_reconstruction_matches: `True`
- no_oracle_source_fields_selected: `True`
- variable_depth_induced_stacks: `True`
- hidden_labels_used_only_for_scoring: `True`
- contains_visible_and_oracle_rows: `True`
