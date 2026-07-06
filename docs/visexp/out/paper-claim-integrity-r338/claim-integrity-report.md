# Paper Claim Integrity Audit R338

R338 mechanically audits the current profiling-paper claim against R320-R350 result artifacts and the Chinese/English paper text. It does not fetch, sync, create, or relabel datasets.

## Verdict

- Overall: pass.
- Result invariants: pass.
- Source policy: pass.
- Paper text coverage: pass.
- Guardrails: pass.
- Two-abstraction boundary: pass.
- Source artifacts tracked clean: True.
- Paper sources hashed: 4.

## Claim Position

Operation/operation-stack profiling is currently supported as a profiler localization, ranking, fragmentation, and actionability claim over real labeled traces. The evidence supports faithful attribution and lower inspection work or fragmentation in scoped settings, while preserving counterpoints where fixed-session, flat, dataset-native, raw-action, or width policies are better.

## Headline Checks

| Run | Key | Expected | Actual | Status | Source |
|---|---|---:|---:|---|---|
| R320 | datasets | 4 | 4 | pass | R320 totals |
| R320 | tasks | 6 | 6 | pass | R320 totals |
| R320 | operations | 34539 | 34539 | pass | R320 totals |
| R320 | positives | 3699 | 3699 | pass | R320 totals |
| R320 | policies | 144 | 144 | pass | R320 totals |
| R320 | operation_stack_top5_work_median | 0.0937 | 0.0937 | pass | R320 policy-scores.csv |
| R320 | flat_top5_work_median | 1.0 | 1.0 | pass | R320 policy-scores.csv |
| R320 | operation_stack_groups_median | 157.5 | 157.5 | pass | R320 policy-scores.csv |
| R320 | fixed_session_groups_median | 285.0 | 285.0 | pass | R320 policy-scores.csv |
| R320 | top5_recall_wins_vs_fixed | 5 | 5 | pass | R320 policy-scores.csv |
| R320 | ap_wins_vs_width | 6 | 6 | pass | R320 policy-scores.csv |
| R333 | operation_stack:query_aware_budget30_median_recall | 0.39 | 0.39 | pass | R333 policy-curve-summary.csv |
| R333 | flat:width_budget30_median_recall | 0.0 | 0.0 | pass | R333 policy-curve-summary.csv |
| R333 | fixed_session:query_aware_budget30_median_recall | 0.3559 | 0.3559 | pass | R333 policy-curve-summary.csv |
| R333 | dataset_native:query_aware_budget30_median_recall | 0.3377 | 0.3377 | pass | R333 policy-curve-summary.csv |
| R333 | raw_action_stack:query_aware_budget30_median_recall | 0.3325 | 0.3325 | pass | R333 policy-curve-summary.csv |
| R334 | groups_lower_than_fixed | 4 | 4 | pass | R334 default-fragmentation-comparisons.csv |
| R334 | positive_groups_lower_than_fixed | 4 | 4 | pass | R334 default-fragmentation-comparisons.csv |
| R334 | groups_to_50pct_lower_than_fixed | 5 | 5 | pass | R334 default-fragmentation-comparisons.csv |
| R334 | work_to_50pct_lower_than_fixed | 1 | 1 | pass | R334 default-fragmentation-comparisons.csv |
| R334 | top5_work_lower_than_fixed | 2 | 2 | pass | R334 default-fragmentation-comparisons.csv |
| R334 | wtfp_lower_than_fixed | 2 | 2 | pass | R334 default-fragmentation-comparisons.csv |
| R334 | budget30_groups_lower_than_fixed | 5 | 5 | pass | R334 budget-fragmentation-comparisons.csv |
| R334 | budget30_groups_median_delta_vs_fixed | -54.0 | -54.0 | pass | R334 budget-fragmentation-comparisons.csv |
| R337 | target25_tasks_reached | 6 | 6 | pass | R337 summary |
| R337 | target25_median_work | 0.2 | 0.2 | pass | R337 summary |
| R337 | target25_median_groups | 16.0 | 16.0 | pass | R337 summary |
| R337 | target10_tasks_reached | 6 | 6 | pass | R337 summary |
| R337 | target10_median_groups | 12.5 | 12.5 | pass | R337 summary |
| R337 | target50_tasks_reached | 5 | 5 | pass | R337 summary |
| R337 | flat_target25_median_work | 1.0 | 1.0 | pass | R337 summary |
| R337 | fixed_target25_median_groups | 50.0 | 50.0 | pass | R337 summary |
| R337 | fixed_target10_median_groups | 37.5 | 37.5 | pass | R337 summary |
| R337 | default_vs_flat_target25_work_wins | 6 | 6 | pass | R337 summary |
| R337 | default_vs_fixed_target25_group_wins | 5 | 5 | pass | R337 summary |
| R337 | default_vs_fixed_target10_group_wins | 5 | 5 | pass | R337 summary |
| R337 | target25_csv_median_work | 0.2 | 0.2 | pass | R337 policy-target-summary.csv |
| R337 | target25_csv_group_wins_vs_fixed | 5 | 5 | pass | R337 default-target-comparisons.csv |
| R339 | overall | pass | pass | pass | R339 summary |
| R339 | datasets | 4 | 4 | pass | R339 summary |
| R339 | tasks | 6 | 6 | pass | R339 summary |
| R339 | policies_scored | 144 | 144 | pass | R339 summary |
| R339 | hidden_labels_used_only_for_scoring | True | True | pass | R339 summary |
| R339 | top5_median_operation_work | 0.0937 | 0.0937 | pass | R339 claim_summary.top5 |
| R339 | top5_median_positive_session_recall | 0.2629 | 0.2629 | pass | R339 claim_summary.top5 |
| R339 | top5_fixed_positive_session_recall | 0.016 | 0.016 | pass | R339 claim_summary.top5 |
| R339 | top5_flat_operation_work | 1.0 | 1.0 | pass | R339 claim_summary.top5 |
| R339 | budget30_median_positive_operation_recall | 0.39 | 0.39 | pass | R339 claim_summary.budget30 |
| R339 | budget30_median_positive_session_recall | 0.4669 | 0.4669 | pass | R339 claim_summary.budget30 |
| R339 | budget30_median_session_work | 0.3467 | 0.3467 | pass | R339 claim_summary.budget30 |
| R339 | budget30_fixed_positive_session_recall | 0.323 | 0.323 | pass | R339 claim_summary.budget30 |
| R339 | budget30_raw_action_positive_session_recall | 0.5147 | 0.5147 | pass | R339 claim_summary.budget30 |
| R339 | budget30_raw_action_session_work | 0.9103 | 0.9103 | pass | R339 claim_summary.budget30 |
| R339 | top5_operation_work_lt_flat_tasks | 6 | 6 | pass | R339 claim_summary.paired_checks |
| R339 | budget30_session_recall_gt_fixed_tasks | 6 | 6 | pass | R339 claim_summary.paired_checks |
| R339 | budget30_session_work_lt_raw_action_tasks | 5 | 5 | pass | R339 claim_summary.paired_checks |
| R339 | csv_default_median_top5_operation_work | 0.0937 | 0.0937 | pass | R339 policy-sequence-summary.csv |
| R339 | csv_default_median_top5_positive_session_recall | 0.2629 | 0.2629 | pass | R339 policy-sequence-summary.csv |
| R339 | csv_default_median_budget30_positive_operation_recall | 0.39 | 0.39 | pass | R339 policy-sequence-summary.csv |
| R339 | csv_default_median_budget30_positive_session_recall | 0.4669 | 0.4669 | pass | R339 policy-sequence-summary.csv |
| R339 | csv_default_median_budget30_session_work | 0.3467 | 0.3467 | pass | R339 policy-sequence-summary.csv |
| R339 | csv_budget30_session_recall_wins_vs_fixed | 6 | 6 | pass | R339 default-sequence-comparisons.csv |
| R339 | csv_budget30_session_work_wins_vs_raw_action | 5 | 5 | pass | R339 default-sequence-comparisons.csv |
| R340 | overall | pass | pass | pass | R340 summary |
| R340 | tasks | 6 | 6 | pass | R340 claim_summary |
| R340 | visible_policies | 15 | 15 | pass | R340 claim_summary |
| R340 | objectives | 8 | 8 | pass | R340 claim_summary |
| R340 | total_decisions | 96 | 96 | pass | R340 claim_summary |
| R340 | exact_best_decisions | 31 | 31 | pass | R340 claim_summary |
| R340 | within_tolerance_decisions | 62 | 62 | pass | R340 claim_summary |
| R340 | selected_beats_width | 72 | 72 | pass | R340 claim_summary |
| R340 | selected_beats_fixed | 69 | 69 | pass | R340 claim_summary |
| R340 | selected_beats_flat | 41 | 41 | pass | R340 claim_summary |
| R340 | operation_stack_selected | 16 | 16 | pass | R340 claim_summary |
| R340 | leave_task_decisions | 48 | 48 | pass | R340 claim_summary.leave_task |
| R340 | leave_task_within_tolerance | 32 | 32 | pass | R340 claim_summary.leave_task |
| R340 | leave_dataset_decisions | 48 | 48 | pass | R340 claim_summary.leave_dataset |
| R340 | leave_dataset_within_tolerance | 30 | 30 | pass | R340 claim_summary.leave_dataset |
| R340 | decision_rows | 96 | 96 | pass | R340 transfer-decisions.csv |
| R340 | objective_rows | 16 | 16 | pass | R340 objective-transfer-summary.csv |
| R340 | selected_policy_visible_rows | 96 | 96 | pass | R340 transfer-decisions.csv + R320 policy-scores.csv |
| R340 | best_policy_visible_rows | 96 | 96 | pass | R340 transfer-decisions.csv + R320 policy-scores.csv |
| R340 | selected_policy_no_oracle_or_label_drilldown | 96 | 96 | pass | R340 transfer-decisions.csv |
| R340 | best_policy_no_oracle_or_label_drilldown | 96 | 96 | pass | R340 transfer-decisions.csv |
| R340 | leave_task_excludes_target_task | 96 | 96 | pass | R340 transfer-decisions.csv |
| R340 | leave_dataset_excludes_target_dataset | 96 | 96 | pass | R340 transfer-decisions.csv + R320 policy-scores.csv |
| R341 | overall | pass | pass | pass | R341 CSV-derived invariants |
| R341 | tasks | 6 | 6 | pass | R341 objective-mechanism-attribution.csv |
| R341 | objective_rows | 36 | 36 | pass | R341 objective-mechanism-attribution.csv |
| R341 | objective_best_policy_visible_rows | 36 | 36 | pass | R341 objective-mechanism-attribution.csv + R320 policy-scores.csv |
| R341 | objective_best_policy_non_oracle_rows | 36 | 36 | pass | R341 objective-mechanism-attribution.csv |
| R341 | actionable_objective_rows | 36 | 36 | pass | R341 objective-mechanism-attribution.csv |
| R341 | nondefault_best_objective_rows | 27 | 27 | pass | R341 objective-mechanism-attribution.csv |
| R341 | transfer_decisions | 96 | 96 | pass | R341 transfer-error-attribution.csv |
| R341 | transfer_misses | 34 | 34 | pass | R341 transfer-error-attribution.csv |
| R341 | transfer_misses_with_view_change | 32 | 32 | pass | R341 transfer-error-attribution.csv |
| R341 | transfer_misses_with_ranker_change | 26 | 26 | pass | R341 transfer-error-attribution.csv |
| R341 | high_regret_transfer_misses | 29 | 29 | pass | R341 transfer-error-attribution.csv |
| R341 | stack_depth_tradeoff_tasks | 6 | 6 | pass | R341 objective-mechanism-attribution.csv |
| R341 | transfer_policy_signal_tasks | 6 | 6 | pass | R341 objective-mechanism-attribution.csv |
| R341 | critical_rank_feature_tasks | 4 | 4 | pass | R341 objective-mechanism-attribution.csv |
| R341 | misleading_feature_tasks | 2 | 2 | pass | R341 objective-mechanism-attribution.csv |
| R341 | tasks_with_three_or_more_mechanism_labels | 6 | 6 | pass | R341 objective-mechanism-attribution.csv |
| R342 | overall | pass | pass | pass | R342 upstream-source-derived invariants |
| R342 | tasks | 6 | 6 | pass | R342 source_paths -> R324 report/summary/specs/Rust JSON |
| R342 | profile_spec_variants | 12 | 12 | pass | R342 source_paths -> R324 report/summary/specs/Rust JSON |
| R342 | composition_variants | 12 | 12 | pass | R342 source_paths -> R324 profile specs |
| R342 | prompt_session_free_variants | 12 | 12 | pass | R342 source_paths -> R324 Rust JSON |
| R342 | rule_score_rank_policy_variants | 12 | 12 | pass | R342 source_paths -> R324 Rust JSON |
| R342 | ap_improves_vs_width_variants | 9 | 9 | pass | R342 source_paths -> R324 summary |
| R342 | top5_lift_improves_vs_width_variants | 8 | 8 | pass | R342 source_paths -> R324 summary |
| R342 | first_positive_work_improves_vs_width_variants | 10 | 10 | pass | R342 source_paths -> R324 summary |
| R342 | tasks_with_ap_improvement_any_depth | 5 | 5 | pass | R342 source_paths -> R324 summary |
| R342 | tasks_with_first_positive_improvement_any_depth | 6 | 6 | pass | R342 source_paths -> R324 summary |
| R342 | tasks_where_coarse_reduces_groups | 6 | 6 | pass | R342 source_paths -> R324 summary |
| R342 | median_coarse_group_reduction | 0.8267 | 0.8267 | pass | R342 source_paths -> R324 summary |
| R342 | tasks_where_depth_choice_changes_objective | 3 | 3 | pass | R342 source_paths -> R324 summary |
| R342 | best_ap_semantic_depth_tasks | 4 | 4 | pass | R342 source_paths -> R324 summary |
| R342 | best_ap_coarse_depth_tasks | 2 | 2 | pass | R342 source_paths -> R324 summary |
| R342 | committed_variant_csv_matches_sources | 12 | 12 | pass | R342 CSV compared with upstream-derived rows |
| R342 | committed_task_csv_matches_sources | 6 | 6 | pass | R342 CSV compared with upstream-derived rows |
| R344 | overall | pass | pass | pass | R344 report summary |
| R344 | tasks | 6 | 6 | pass | R344 report summary |
| R344 | metric_comparisons | 50 | 50 | pass | R344 report summary |
| R344 | task_metric_delta_rows | 300 | 300 | pass | R344 report summary |
| R344 | support_verdicts | 30 | 30 | pass | R344 report summary |
| R344 | counterpoint_verdicts | 16 | 16 | pass | R344 report summary |
| R344 | mixed_or_weak_verdicts | 4 | 4 | pass | R344 report summary |
| R344 | required_metric_count | 9 | 9 | pass | R344 report summary |
| R344 | required_groups_metric_present | True | True | pass | R344 report summary |
| R344 | metric_summary_rows | 50 | 50 | pass | R344 metric-summary.csv |
| R344 | task_delta_rows | 300 | 300 | pass | R344 task-metric-deltas.csv |
| R344 | summary_support_verdicts | 30 | 30 | pass | R344 metric-summary.csv |
| R344 | summary_counterpoint_verdicts | 16 | 16 | pass | R344 metric-summary.csv |
| R344 | summary_mixed_or_weak_verdicts | 4 | 4 | pass | R344 metric-summary.csv |
| R344 | required_metric_groups_in_summary | True | True | pass | R344 metric-summary.csv |
| R344 | flat_ap_wins | 6 | 6 | pass | R344 metric-summary.csv |
| R344 | flat_budget30_recall_wins | 6 | 6 | pass | R344 metric-summary.csv |
| R344 | flat_work_to_first_positive_wins | 6 | 6 | pass | R344 metric-summary.csv |
| R344 | fixed_session_top5_f1_wins | 5 | 5 | pass | R344 metric-summary.csv |
| R344 | fixed_session_group_wins | 4 | 4 | pass | R344 metric-summary.csv |
| R344 | width_ap_wins | 6 | 6 | pass | R344 metric-summary.csv |
| R344 | width_budget30_recall_wins | 5 | 5 | pass | R344 metric-summary.csv |
| R344 | flat_ndcg_losses | 6 | 6 | pass | R344 metric-summary.csv |
| R344 | flat_top5_recall_losses | 6 | 6 | pass | R344 metric-summary.csv |
| R345 | overall | pass | pass | pass | R345 report summary |
| R345 | tasks | 6 | 6 | pass | R345 report summary |
| R345 | datasets | 4 | 4 | pass | R345 report summary |
| R345 | lens_count | 6 | 6 | pass | R345 report summary |
| R345 | objective_rows | 36 | 36 | pass | R345 report summary |
| R345 | task_cards | 6 | 6 | pass | R345 report summary |
| R345 | actionable_task_cards | 6 | 6 | pass | R345 report summary |
| R345 | distinct_optimization_actions | 5 | 5 | pass | R345 report summary |
| R345 | default_operation_stack_best_objectives | 9 | 9 | pass | R345 report summary |
| R345 | operation_stack_family_best_objectives | 11 | 11 | pass | R345 report summary |
| R345 | non_operation_stack_best_objectives | 25 | 25 | pass | R345 report summary |
| R345 | tasks_with_three_or_more_best_views | 6 | 6 | pass | R345 report summary |
| R345 | min_distinct_best_views_per_task | 3 | 3 | pass | R345 report summary |
| R345 | max_distinct_best_views_per_task | 4 | 4 | pass | R345 report summary |
| R345 | counterpoint_rows | 46 | 46 | pass | R345 report summary |
| R345 | r344_support_verdicts | 30 | 30 | pass | R345 report summary |
| R345 | r344_counterpoint_verdicts | 16 | 16 | pass | R345 report summary |
| R345 | r344_mixed_or_weak_verdicts | 4 | 4 | pass | R345 report summary |
| R345 | lens_summary_rows | 6 | 6 | pass | R345 diagnostic-lens-summary.csv |
| R345 | task_lens_card_rows | 6 | 6 | pass | R345 task-lens-cards.csv |
| R345 | counterpoint_ledger_rows | 46 | 46 | pass | R345 counterpoint-ledger.csv |
| R346 | overall | pass | pass | pass | R346 report summary |
| R346 | tasks | 6 | 6 | pass | R346 report summary |
| R346 | datasets | 4 | 4 | pass | R346 report summary |
| R346 | case_groups | 30 | 30 | pass | R346 report summary |
| R346 | top_groups_per_task | 5 | 5 | pass | R346 report summary |
| R346 | tasks_with_top1_positive | 5 | 5 | pass | R346 report summary |
| R346 | tasks_with_positive_in_top5 | 6 | 6 | pass | R346 report summary |
| R346 | median_top5_recall | 0.188 | 0.188 | pass | R346 report summary |
| R346 | median_top5_precision | 0.1991 | 0.1991 | pass | R346 report summary |
| R346 | median_top5_lift | 1.6508 | 1.6508 | pass | R346 report summary |
| R346 | median_top5_work | 0.0937 | 0.0937 | pass | R346 report summary |
| R346 | median_first_positive_work | 0.0378 | 0.0378 | pass | R346 report summary |
| R346 | tasks_with_actionable_case_cards | 6 | 6 | pass | R346 report summary |
| R346 | tasks_with_counterpoints | 6 | 6 | pass | R346 report summary |
| R346 | tasks_with_three_or_more_best_views | 6 | 6 | pass | R346 report summary |
| R346 | min_distinct_best_views_per_task | 3 | 3 | pass | R346 report summary |
| R346 | max_distinct_best_views_per_task | 4 | 4 | pass | R346 report summary |
| R346 | task_case_card_rows | 6 | 6 | pass | R346 task-diagnostic-case-cards.csv |
| R346 | top_stack_evidence_rows | 30 | 30 | pass | R346 top-stack-evidence.csv |
| R347 | overall | pass | pass | pass | R347 report summary |
| R347 | tasks | 6 | 6 | pass | R347 report summary |
| R347 | datasets | 4 | 4 | pass | R347 report summary |
| R347 | visible_views | 5 | 5 | pass | R347 report summary |
| R347 | view_task_rows | 30 | 30 | pass | R347 report summary |
| R347 | top_groups_per_view | 5 | 5 | pass | R347 report summary |
| R347 | operation_stack_top5_positive_tasks | 6 | 6 | pass | R347 report summary |
| R347 | operation_stack_top1_positive_tasks | 5 | 5 | pass | R347 report summary |
| R347 | operation_stack_median_top5_recall | 0.188 | 0.188 | pass | R347 report summary |
| R347 | operation_stack_median_top5_lift | 1.6508 | 1.6508 | pass | R347 report summary |
| R347 | operation_stack_median_top5_work | 0.0937 | 0.0937 | pass | R347 report summary |
| R347 | operation_stack_median_first_positive_work | 0.0378 | 0.0378 | pass | R347 report summary |
| R347 | wins_vs_flat_top5_work | 6 | 6 | pass | R347 report summary |
| R347 | wins_vs_fixed_top5_recall | 5 | 5 | pass | R347 report summary |
| R347 | wins_vs_fixed_group_count | 4 | 4 | pass | R347 report summary |
| R347 | tasks_with_counterpoints | 6 | 6 | pass | R347 report summary |
| R347 | view_case_metric_rows | 30 | 30 | pass | R347 view-case-metrics.csv |
| R347 | task_baseline_card_rows | 6 | 6 | pass | R347 task-baseline-contrast-cards.csv |
| R347 | baseline_pair_summary_rows | 24 | 24 | pass | R347 baseline-pair-summary.csv |
| R347 | top_group_contrast_rows | 124 | 124 | pass | R347 top-group-contrast.csv |
| R347 | flat_top5_work_wins | 6 | 6 | pass | R347 baseline-pair-summary.csv |
| R347 | fixed_session_top5_recall_wins | 5 | 5 | pass | R347 baseline-pair-summary.csv |
| R347 | fixed_session_group_wins | 4 | 4 | pass | R347 baseline-pair-summary.csv |
| R347 | fixed_session_first_positive_losses | 4 | 4 | pass | R347 baseline-pair-summary.csv |
| R347 | flat_top5_recall_losses | 6 | 6 | pass | R347 baseline-pair-summary.csv |
| R348 | overall | pass | pass | pass | R348 report summary |
| R348 | tasks | 6 | 6 | pass | R348 report summary |
| R348 | datasets | 4 | 4 | pass | R348 report summary |
| R348 | objective_rows | 36 | 36 | pass | R348 report summary |
| R348 | nondefault_action_rows | 27 | 27 | pass | R348 report summary |
| R348 | default_best_rows | 9 | 9 | pass | R348 report summary |
| R348 | visible_non_oracle_best_rows | 36 | 36 | pass | R348 report summary |
| R348 | view_change_rows | 25 | 25 | pass | R348 report summary |
| R348 | operation_stack_tuning_rows | 2 | 2 | pass | R348 report summary |
| R348 | non_operation_stack_counterpoint_rows | 25 | 25 | pass | R348 report summary |
| R348 | tasks_with_nondefault_actions | 6 | 6 | pass | R348 report summary |
| R348 | tasks_with_three_or_more_action_classes | 6 | 6 | pass | R348 report summary |
| R348 | tasks_with_case_counterpoints | 6 | 6 | pass | R348 report summary |
| R348 | median_gain_over_default | 0.1447 | 0.1447 | pass | R348 report summary |
| R348 | median_nondefault_gain_over_default | 0.6188 | 0.6188 | pass | R348 report summary |
| R348 | max_gain_over_default | 288.0 | 288.0 | pass | R348 report summary |
| R348 | r335_actionability_cards | 6 | 6 | pass | R348 report summary |
| R348 | r341_actionable_objective_rows | 36 | 36 | pass | R348 report summary |
| R348 | r347_visible_views | 5 | 5 | pass | R348 report summary |
| R348 | objective_counterfactual_rows | 36 | 36 | pass | R348 objective-counterfactuals.csv |
| R348 | action_class_summary_rows | 6 | 6 | pass | R348 action-class-summary.csv |
| R348 | task_action_counterfactual_card_rows | 6 | 6 | pass | R348 task-action-counterfactual-cards.csv |
| R348 | flat_counterpoint_action_rows | 7 | 7 | pass | R348 action-class-summary.csv |
| R348 | fixed_session_drilldown_rows | 7 | 7 | pass | R348 action-class-summary.csv |
| R348 | dataset_native_hierarchy_rows | 5 | 5 | pass | R348 action-class-summary.csv |
| R348 | raw_action_counterpoint_rows | 6 | 6 | pass | R348 action-class-summary.csv |
| R348 | keep_default_operation_stack_rows | 9 | 9 | pass | R348 action-class-summary.csv |
| R348 | retune_operation_stack_ranker_rows | 2 | 2 | pass | R348 action-class-summary.csv |
| R349 | overall | pass | pass | pass | R349 report summary |
| R349 | transfer_decisions_total | 96 | 96 | pass | R349 report summary |
| R349 | aligned_decisions | 60 | 60 | pass | R349 report summary |
| R349 | excluded_decisions | 36 | 36 | pass | R349 report summary |
| R349 | aligned_objectives | 5 | 5 | pass | R349 report summary |
| R349 | tasks | 6 | 6 | pass | R349 report summary |
| R349 | datasets | 4 | 4 | pass | R349 report summary |
| R349 | selected_visible_non_oracle_rows | 60 | 60 | pass | R349 report summary |
| R349 | best_visible_non_oracle_rows | 60 | 60 | pass | R349 report summary |
| R349 | r340_r348_best_policy_match_rows | 50 | 50 | pass | R349 report summary |
| R349 | r340_r348_best_policy_mismatch_rows | 10 | 10 | pass | R349 report summary |
| R349 | selected_action_exact | 7 | 7 | pass | R349 report summary |
| R349 | selected_r348_policy_exact | 7 | 7 | pass | R349 report summary |
| R349 | selected_r340_exact_best | 13 | 13 | pass | R349 report summary |
| R349 | selected_view_exact | 11 | 11 | pass | R349 report summary |
| R349 | selected_ranker_exact | 27 | 27 | pass | R349 report summary |
| R349 | selected_within_tolerance | 35 | 35 | pass | R349 report summary |
| R349 | selected_beats_default | 30 | 30 | pass | R349 report summary |
| R349 | default_within_tolerance | 26 | 26 | pass | R349 report summary |
| R349 | nondefault_target_rows | 42 | 42 | pass | R349 report summary |
| R349 | nondefault_target_action_exact | 2 | 2 | pass | R349 report summary |
| R349 | nondefault_target_within_tolerance | 24 | 24 | pass | R349 report summary |
| R349 | nondefault_target_selected_default_action | 2 | 2 | pass | R349 report summary |
| R349 | leave_task_action_exact | 4 | 4 | pass | R349 report summary |
| R349 | leave_dataset_action_exact | 3 | 3 | pass | R349 report summary |
| R349 | leave_task_within_tolerance | 18 | 18 | pass | R349 report summary |
| R349 | leave_dataset_within_tolerance | 17 | 17 | pass | R349 report summary |
| R349 | sequence_objective_excluded_rows | 36 | 36 | pass | R349 report summary |
| R349 | r348_untransferred_objective_rows | 6 | 6 | pass | R349 report summary |
| R349 | decision_rows | 60 | 60 | pass | R349 action-transfer-decisions.csv |
| R349 | summary_rows | 13 | 13 | pass | R349 action-transfer-summary.csv |
| R349 | confusion_rows | 16 | 16 | pass | R349 action-transfer-confusion.csv |
| R349 | task_card_rows | 12 | 12 | pass | R349 task-action-transfer-cards.csv |
| R349 | excluded_rows | 36 | 36 | pass | R349 excluded-transfer-decisions.csv |
| R349 | untransferred_rows | 6 | 6 | pass | R349 untransferred-r348-objectives.csv |
| R350 | overall | pass | pass | pass | R350 report summary |
| R350 | tasks | 6 | 6 | pass | R350 report summary |
| R350 | datasets | 4 | 4 | pass | R350 report summary |
| R350 | objective_rows | 36 | 36 | pass | R350 report summary |
| R350 | action_classes | 6 | 6 | pass | R350 report summary |
| R350 | packets_with_top5_positive | 6 | 6 | pass | R350 report summary |
| R350 | packets_with_top1_positive | 5 | 5 | pass | R350 report summary |
| R350 | packets_with_30pct_work_budget | 4 | 4 | pass | R350 report summary |
| R350 | packets_with_first_positive_10pct_budget | 4 | 4 | pass | R350 report summary |
| R350 | packets_with_baseline_counterpoints | 6 | 6 | pass | R350 report summary |
| R350 | packets_with_nondefault_actions | 6 | 6 | pass | R350 report summary |
| R350 | packets_with_three_or_more_action_classes | 6 | 6 | pass | R350 report summary |
| R350 | operation_stack_beats_flat_work_tasks | 6 | 6 | pass | R350 report summary |
| R350 | operation_stack_beats_fixed_recall_tasks | 5 | 5 | pass | R350 report summary |
| R350 | operation_stack_fewer_groups_than_fixed_tasks | 4 | 4 | pass | R350 report summary |
| R350 | median_top5_work | 0.0937 | 0.0937 | pass | R350 report summary |
| R350 | median_first_positive_work | 0.0378 | 0.0378 | pass | R350 report summary |
| R350 | median_top5_recall | 0.188 | 0.188 | pass | R350 report summary |
| R350 | median_top5_lift | 1.6508 | 1.6508 | pass | R350 report summary |
| R350 | nondefault_objective_rows | 27 | 27 | pass | R350 report summary |
| R350 | visible_non_oracle_best_rows | 36 | 36 | pass | R350 report summary |
| R350 | median_nondefault_gain_over_default | 0.6188 | 0.6188 | pass | R350 report summary |
| R350 | max_gain_over_default | 288.0 | 288.0 | pass | R350 report summary |
| R350 | r349_aligned_transfer_decisions | 60 | 60 | pass | R350 report summary |
| R350 | r349_selected_within_tolerance | 35 | 35 | pass | R350 report summary |
| R350 | r349_selected_action_exact | 7 | 7 | pass | R350 report summary |
| R350 | r349_nondefault_target_within_tolerance | 24 | 24 | pass | R350 report summary |
| R350 | task_packet_rows | 6 | 6 | pass | R350 task-evidence-packets.csv |
| R350 | objective_packet_rows | 36 | 36 | pass | R350 objective-evidence-packets.csv |
| R350 | budget_summary_rows | 7 | 7 | pass | R350 budget-summary.csv |
| R350 | budget_top5_positive | 6 | 6 | pass | R350 budget-summary.csv |
| R350 | budget_30pct_packets | 4 | 4 | pass | R350 budget-summary.csv |
| R350 | budget_actionable_counterfactual | 27 | 27 | pass | R350 budget-summary.csv |

## Text Coverage

| Doc | Key | Tokens | Status | Lines |
|---|---|---|---|---|
| evaluation | R320 headline operations | 34,539 / 34539 | pass | 15,33,268,292,355,377,511,543 |
| evaluation | R320 top5 work | 0.0937 / 9.37% | pass | 15,131,133,139,269,378,434,477 |
| evaluation | R333 budget30 recall | 0.3900 / 0.39 | pass | 437,543,638,726 |
| evaluation | R334 fragmentation | 5/6 / -54.0 / fewer groups | pass | 15,81,82,99,127,131,133,137 |
| evaluation | R335 actionability | actionability / 6/6 / optimization | pass | 5,15,26,34,40,42,85,104 |
| evaluation | R336 visible policies | 15 visible / 15 个 / 6 diagnostic | pass | 129,543,641,645,650 |
| evaluation | R337 fixed recall | 25% / 0.2000 / 16.0 | pass | 420,422,543,642 |
| evaluation | R339 sequence adequacy | R339 / 0.4669 / 0.9103 | pass | 13,15,33,157,158,430,438,441 |
| evaluation | R340 policy transfer | R340 / 96 / 62/96 / 72/96 | pass | 34,136,137,229,239,341,343,444 |
| evaluation | R341 mechanism attribution | R341 / 36/36 / 27/36 / 34/96 | pass | 34,128,134,135,139,457,458,459 |
| evaluation | R342 profile spec composition | R342 / 12/12 / 9/12 / 0.8267 | pass | 12,32,34,106,108,111,113,261 |
| evaluation | R344 metric consistency | R344 / 30 / 16 / groups | pass | 12,13,15,32,33,34,35,67 |
| evaluation | R345 diagnostic lens portfolio | R345 / 6 diagnostic lenses / 11/36 / 25/36 | pass | 34,38,128,129,130,134,135,313 |
| evaluation | R346 diagnostic casebook | R346 / 30 case groups / 5/6 / 1.6508 | pass | 15,34,81,82,99,127,130,131 |
| evaluation | R347 case baseline contrast | R347 / 5 visible views / 6/6 / 5/6 / 4/6 | pass | 15,34,69,73,81,82,98,99 |
| evaluation | R348 action counterfactual | R348 / 36 objective rows / 27/36 / 0.1447 | pass | 34,38,128,129,134,135,136,137 |
| evaluation | R349 held-out action transfer | R349 / 60 aligned / 35/60 / 7/60 / 2/42 | pass | 34,136,137,138,139,465,466,467 |
| evaluation | R350 evidence packet budget | R350 / 6/6 / 4/6 / 27/36 / 35/60 | pass | 34,69,73,81,82,98,100,113 |
| zh_main | core experiment organization | 三个经验性 profiling / 系统/复现实验 / E1 / E2 / E3 / E4 | pass | 46,47,50,54,57,223,237,238 |
| zh_main | E2 headline | 34,539 / 3,699 / 0.0937 / 285.0 / 157.5 | pass | 51,52,238,331,335,341,358,359 |
| zh_main | E3 actionability headline | profile-configuration / 5/6 / 0.2402 / 0.2583 | pass | 52,54,56,147,149,184,238,239 |
| zh_main | E4 guardrails | 76 / two-abstraction / 不声称 / human productivity | pass | 57,60,138,146,151,152,240,406 |
| en_main | core experiment organization | three empirical profiling experiments / systems/reproducibility / E1 / E2 / E3 / E4 | pass | 39,40,44,52,59,116,117,118 |
| en_main | E2 headline | 34,539 / 3,699 / 0.0937 / 285.0 / 157.5 | pass | 46,47,48,50,238,239,240,356 |
| en_main | E3 actionability headline | profile-configuration / 5 of 6 / 0.2402 / 0.2583 | pass | 50,52,58,248,309,310,319,427 |
| en_main | E4 guardrails | 76 / two-abstraction / does not claim / human-productivity | pass | 60,61,70,100,246,253,254,255 |
| zh_claim_setup | two abstractions | 两个核心抽象 / operation stack | pass | 7,23,25,75,99,102,103,104 |
| zh_claim_setup | R337 result | R337 / 0.2000 / 16.0 | pass | 35,36,76,137,139 |
| zh_claim_setup | R339 result | R339 / 0.4669 / 0.9103 | pass | 36,37,50,76,139,140,287 |
| zh_claim_setup | R340 result | R340 / 62/96 / 72/96 / 69/96 | pass | 37,38,45,77,140,141,148 |
| zh_claim_setup | R341 result | R341 / 36/36 / 27/36 / 34/96 | pass | 38,41,44,46,77,141,144,147 |
| zh_claim_setup | R342 result | R342 / 12/12 / 9/12 / 0.8267 | pass | 39,55,75,77,142,154 |
| zh_claim_setup | R344 result | R344 / 30 / 16 / nDCG | pass | 22,23,24,26,28,31,32,34 |
| zh_claim_setup | R345 result | R345 / 6 / 11/36 / 25/36 | pass | 3,22,23,24,25,26,27,28 |
| zh_claim_setup | R346 result | R346 / 30 / 5/6 / 1.6508 | pass | 22,23,26,28,31,32,34,35 |
| zh_claim_setup | R347 result | R347 / 5 / 6/6 / 5/6 / 4/6 | pass | 22,23,24,25,26,27,28,30 |
| zh_claim_setup | R348 result | R348 / 36 / 27/36 / 0.1447 | pass | 24,25,34,35,38,41,44,45 |
| zh_claim_setup | R349 result | R349 / 60 / 35/60 / 7/60 / 2/42 | pass | 23,28,36,45,46,55,77,94 |
| zh_claim_setup | R350 result | R350 / 6/6 / 4/6 / 27/36 / 35/60 | pass | 26,33,34,35,38,39,40,41 |
| evaluation | R320:datasets | 4 | pass | 12,13,14,15,26,32,33,34 |
| evaluation | R320:tasks | 6 | pass | 3,4,5,12,13,15,32,33 |
| evaluation | R320:operations | 34,539 | pass | 15,33,268,292,355,377,511,543 |
| evaluation | R320:positives | 3,699 | pass | 15,33,268,292,377,618,621,625 |
| evaluation | R320:policies | 144 | pass | 15,135,268,376,543,623,628,638 |
| evaluation | R320:operation_stack_top5_work_median | 0.0937 | pass | 15,131,133,139,269,434,477,543 |
| evaluation | R320:flat_top5_work_median | 1.0 | pass | 15,269,423,435,543,607,610,624 |
| evaluation | R320:operation_stack_groups_median | 157.5 | pass | 15,381,543,628,665,742 |
| evaluation | R320:fixed_session_groups_median | 285.0 | pass | 15,381,543,628,742 |
| evaluation | R320:top5_recall_wins_vs_fixed | 5/6 | pass | 15,81,82,99,127,131,133,137 |
| evaluation | R320:ap_wins_vs_width | 6/6 | pass | 113,127,128,129,131,133,134,135 |
| evaluation | R333:operation_stack:query_aware_budget30_median_recall | 0.3900 | pass | 437,543,638 |
| evaluation | R333:flat:width_budget30_median_recall | 0.0000 | pass | 543,638 |
| evaluation | R333:fixed_session:query_aware_budget30_median_recall | 0.3559 | pass | 543,638 |
| evaluation | R333:dataset_native:query_aware_budget30_median_recall | 0.3377 | pass | 543,638 |
| evaluation | R333:raw_action_stack:query_aware_budget30_median_recall | 0.3325 | pass | 543,638 |
| evaluation | R337:target25_tasks_reached | 6/6 | pass | 113,127,128,129,131,133,134,135 |
| evaluation | R337:target25_median_work | 0.2000 | pass | 422,543,642 |
| evaluation | R337:target25_median_groups | 16.0 | pass | 422,543,642 |
| evaluation | R337:target10_tasks_reached | 6/6 | pass | 113,127,128,129,131,133,134,135 |
| evaluation | R337:target10_median_groups | 12.5 | pass | 426,642 |
| evaluation | R337:target50_tasks_reached | 5/6 | pass | 15,81,82,99,127,131,133,137 |
| evaluation | R337:flat_target25_median_work | 1.0000 | pass | 423,435,543,642 |
| evaluation | R337:fixed_target25_median_groups | 50.0 | pass | 424,543,642 |
| evaluation | R337:fixed_target10_median_groups | 37.5 | pass | 426,642 |
| evaluation | R337:default_vs_flat_target25_work_wins | 6/6 | pass | 113,127,128,129,131,133,134,135 |
| evaluation | R337:default_vs_fixed_target25_group_wins | 5/6 | pass | 15,81,82,99,127,131,133,137 |
| evaluation | R337:default_vs_fixed_target10_group_wins | 5/6 | pass | 15,81,82,99,127,131,133,137 |
| evaluation | R337:target25_csv_median_work | 0.2000 | pass | 422,543,642 |
| evaluation | R337:target25_csv_group_wins_vs_fixed | 5/6 | pass | 15,81,82,99,127,131,133,137 |
| evaluation | R339:overall | pass | pass | 14,79,190,191,199,200,218,247 |
| evaluation | R339:datasets | 4 | pass | 12,13,14,15,26,32,33,34 |
| evaluation | R339:tasks | 6 | pass | 3,4,5,12,13,15,32,33 |
| evaluation | R339:policies_scored | 144 | pass | 15,135,268,376,543,623,628,638 |
| evaluation | R339:hidden_labels_used_only_for_scoring | hidden labels only for scoring | pass | 644,652 |
| evaluation | R339:top5_median_operation_work | 0.0937 | pass | 15,131,133,139,269,434,477,543 |
| evaluation | R339:top5_median_positive_session_recall | 0.2629 | pass | 435,644 |
| evaluation | R339:top5_fixed_positive_session_recall | 0.0160 | pass | 436,644 |
| evaluation | R339:top5_flat_operation_work | 1.0000 | pass | 423,435,543,642 |
| evaluation | R339:budget30_median_positive_operation_recall | 0.3900 | pass | 437,543,638 |
| evaluation | R339:budget30_median_positive_session_recall | 0.4669 | pass | 438,543,644 |
| evaluation | R339:budget30_median_session_work | 0.3467 | pass | 439,543,644 |
| evaluation | R339:budget30_fixed_positive_session_recall | 0.3230 | pass | 439,543,644 |
| evaluation | R339:budget30_raw_action_positive_session_recall | 0.5147 | pass | 441,543,644 |
| evaluation | R339:budget30_raw_action_session_work | 0.9103 | pass | 441,543,644 |
| evaluation | R339:top5_operation_work_lt_flat_tasks | 6/6 | pass | 113,127,128,129,131,133,134,135 |
| evaluation | R339:budget30_session_recall_gt_fixed_tasks | 6/6 | pass | 113,127,128,129,131,133,134,135 |
| evaluation | R339:budget30_session_work_lt_raw_action_tasks | 5/6 | pass | 15,81,82,99,127,131,133,137 |
| evaluation | R339:csv_default_median_top5_operation_work | 0.0937 | pass | 15,131,133,139,269,434,477,543 |
| evaluation | R339:csv_default_median_top5_positive_session_recall | 0.2629 | pass | 435,644 |
| evaluation | R339:csv_default_median_budget30_positive_operation_recall | 0.3900 | pass | 437,543,638 |
| evaluation | R339:csv_default_median_budget30_positive_session_recall | 0.4669 | pass | 438,543,644 |
| evaluation | R339:csv_default_median_budget30_session_work | 0.3467 | pass | 439,543,644 |
| evaluation | R339:csv_budget30_session_recall_wins_vs_fixed | 6/6 | pass | 113,127,128,129,131,133,134,135 |
| evaluation | R339:csv_budget30_session_work_wins_vs_raw_action | 5/6 | pass | 15,81,82,99,127,131,133,137 |
| evaluation | R340:overall | pass | pass | 14,79,190,191,199,200,218,247 |
| evaluation | R340:tasks | 6 | pass | 3,4,5,12,13,15,32,33 |
| evaluation | R340:visible_policies | 15 | pass | 12,13,15,32,35,232,241,257 |
| evaluation | R340:objectives | 8 | pass | 12,13,14,15,32,33,34,35 |
| evaluation | R340:total_decisions | 96 | pass | 137,229,239,341,343,447,448,449 |
| evaluation | R340:exact_best_decisions | 31 | pass | 33,35,197,358,360,364,366,369 |
| evaluation | R340:within_tolerance_decisions | 62 | pass | 13,38,298,304,307,313,435,448 |
| evaluation | R340:selected_beats_width | 72 | pass | 12,449,543,569,580,596,608,629 |
| evaluation | R340:selected_beats_fixed | 69 | pass | 15,33,205,212,268,292,377,438 |
| evaluation | R340:selected_beats_flat | 41 | pass | 13,34,128,134,450,457,543,572 |
| evaluation | R340:operation_stack_selected | 16 | pass | 13,35,129,137,173,198,303,307 |
| evaluation | R340:leave_task_decisions | 48 | pass | 34,38,134,135,136,137,138,141 |
| evaluation | R340:leave_task_within_tolerance | 32 | pass | 12,14,15,32,33,34,35,38 |
| evaluation | R340:leave_dataset_decisions | 48 | pass | 34,38,134,135,136,137,138,141 |
| evaluation | R340:leave_dataset_within_tolerance | 30 | pass | 12,13,32,33,67,78,107,119 |
| evaluation | R340:decision_rows | 96 | pass | 137,229,239,341,343,447,448,449 |
| evaluation | R340:objective_rows | 16 | pass | 13,35,129,137,173,198,303,307 |
| evaluation | R340:selected_policy_visible_rows | 96/96 | pass | 455,456 |
| evaluation | R340:best_policy_visible_rows | 96/96 | pass | 455,456 |
| evaluation | R340:selected_policy_no_oracle_or_label_drilldown | 96/96 | pass | 455,456 |
| evaluation | R340:best_policy_no_oracle_or_label_drilldown | 96/96 | pass | 455,456 |
| evaluation | R340:leave_task_excludes_target_task | 96/96 | pass | 455,456 |
| evaluation | R340:leave_dataset_excludes_target_dataset | 96/96 | pass | 455,456 |
| evaluation | R341:overall | R341 | pass | 34,128,134,457,543,643,646,650 |
| evaluation | R341:tasks | 6 tasks | pass | 128,134,543,646,650,653 |
| evaluation | R341:objective_rows | 36 objective rows | pass | 128,134,543,646,650,653 |
| evaluation | R341:objective_best_policy_visible_rows | 36/36 best policies visible | pass | 646 |
| evaluation | R341:objective_best_policy_non_oracle_rows | 36/36 best policies non-oracle | pass | 646 |
| evaluation | R341:actionable_objective_rows | 36/36 objective rows have optimization actions | pass | 543,646 |
| evaluation | R341:nondefault_best_objective_rows | 27/36 best visible policies are non-default | pass | 543,646 |
| evaluation | R341:transfer_decisions | 96 transfer decisions | pass | 646 |
| evaluation | R341:transfer_misses | 34/96 transfer decisions | pass | 646 |
| evaluation | R341:transfer_misses_with_view_change | 32/34 misses change view | pass | 646 |
| evaluation | R341:transfer_misses_with_ranker_change | 26/34 change ranker | pass | 646 |
| evaluation | R341:high_regret_transfer_misses | 29/34 high-regret misses | pass | 543,646 |
| evaluation | R341:stack_depth_tradeoff_tasks | stack-depth signals on 6/6 | pass | 646 |
| evaluation | R341:transfer_policy_signal_tasks | transfer-policy signals on 6/6 | pass | 646 |
| evaluation | R341:critical_rank_feature_tasks | critical features on 4/6 | pass | 646 |
| evaluation | R341:misleading_feature_tasks | misleading features on 2/6 | pass | 646 |
| evaluation | R341:tasks_with_three_or_more_mechanism_labels | three or more mechanism labels on 6/6 | pass | 646 |
| evaluation | R342:overall | R342 | pass | 12,32,34,106,261,540,543,545 |
| evaluation | R342:tasks | 6 tasks | pass | 543,647,648,750 |
| evaluation | R342:profile_spec_variants | 12 profile-spec variants | pass | 647,750 |
| evaluation | R342:composition_variants | 12/12 compose | pass | 647 |
| evaluation | R342:prompt_session_free_variants | 12/12 prompt/session-free | pass | 647 |
| evaluation | R342:rule_score_rank_policy_variants | rank_mode=rule-score | pass | 647,750 |
| evaluation | R342:ap_improves_vs_width_variants | 9/12 variants | pass | 647,750 |
| evaluation | R342:top5_lift_improves_vs_width_variants | 8/12 | pass | 647 |
| evaluation | R342:first_positive_work_improves_vs_width_variants | 10/12 | pass | 647,750 |
| evaluation | R342:tasks_with_ap_improvement_any_depth | 5/6 | pass | 543,665 |
| evaluation | R342:tasks_with_first_positive_improvement_any_depth | 6/6 | pass | 543,647,750 |
| evaluation | R342:tasks_where_coarse_reduces_groups | 6/6 tasks | pass | 543,647,750 |
| evaluation | R342:median_coarse_group_reduction | 0.8267 | pass | 647,750 |
| evaluation | R342:tasks_where_depth_choice_changes_objective | 3/6 tasks | pass | 647 |
| evaluation | R342:best_ap_semantic_depth_tasks | semantic 4 / coarse 2 | pass | 647,750 |
| evaluation | R342:best_ap_coarse_depth_tasks | semantic 4 / coarse 2 | pass | 647,750 |
| evaluation | R342:committed_variant_csv_matches_sources | 12/12 | pass | 12,540,647,648,750 |
| evaluation | R342:committed_task_csv_matches_sources | 6/6 | pass | 543,647,750 |
| evaluation | R344:overall | R344 | pass | 33,116,127,128,543,643,649,650 |
| evaluation | R344:tasks | 6 tasks | pass | 128,543,649,650 |
| evaluation | R344:metric_comparisons | 50 baseline-metric comparisons | pass | 543,649,743 |
| evaluation | R344:task_metric_delta_rows | 300 task-metric deltas | pass | 649 |
| evaluation | R344:support_verdicts | 30 support verdicts | pass | 649,743 |
| evaluation | R344:counterpoint_verdicts | 16 counterpoints | pass | 649,743 |
| evaluation | R344:mixed_or_weak_verdicts | 4 mixed/weak | pass | 649,743 |
| evaluation | R344:required_metric_count | groups | pass | 33,127,128,543,743 |
| evaluation | R344:required_groups_metric_present | groups | pass | 33,127,128,543,743 |
| evaluation | R344:metric_summary_rows | 50 | pass | 543,643,649,743,836 |
| evaluation | R344:task_delta_rows | 300 | pass | 33,543,649 |
| evaluation | R344:summary_support_verdicts | 30 support verdicts | pass | 649,743 |
| evaluation | R344:summary_counterpoint_verdicts | 16 counterpoints | pass | 649,743 |
| evaluation | R344:summary_mixed_or_weak_verdicts | 4 mixed/weak | pass | 649,743 |
| evaluation | R344:required_metric_groups_in_summary | groups | pass | 33,127,128,543,743 |
| evaluation | R344:flat_ap_wins | flat AP 6/6 | pass | 127 |
| evaluation | R344:flat_budget30_recall_wins | budget30 recall 6/6 | pass | 127 |
| evaluation | R344:flat_work_to_first_positive_wins | work-to-first-positive 6/6 | pass | 127 |
| evaluation | R344:fixed_session_top5_f1_wins | top-5 F1 5/6 | pass | 127 |
| evaluation | R344:fixed_session_group_wins | groups 4/6 | pass | 127 |
| evaluation | R344:width_ap_wins | width AP 6/6 | pass | 127 |
| evaluation | R344:width_budget30_recall_wins | budget30 recall 5/6 | pass | 127 |
| evaluation | R344:flat_ndcg_losses | nDCG | pass | 33,543,649,743,821 |
| evaluation | R344:flat_top5_recall_losses | top-k recall | pass | 543,649,743 |
| evaluation | R345:overall | R345 | pass | 34,38,128,129,130,313,543,643 |
| evaluation | R345:tasks | 6 tasks | pass | 128,129,543,650,651 |
| evaluation | R345:datasets | 4 datasets | pass | 129,650,651 |
| evaluation | R345:lens_count | 6 diagnostic lenses | pass | 129,543,650 |
| evaluation | R345:objective_rows | 36 objective rows | pass | 128,129,543,650 |
| evaluation | R345:task_cards | 6/6 actionable task cards | pass | 129 |
| evaluation | R345:actionable_task_cards | 6/6 actionable task cards | pass | 129 |
| evaluation | R345:distinct_optimization_actions | 5 distinct optimization actions | pass | 129 |
| evaluation | R345:default_operation_stack_best_objectives | 9/36 default operation-stack | pass | 129 |
| evaluation | R345:operation_stack_family_best_objectives | 11/36 operation-stack family | pass | 129 |
| evaluation | R345:non_operation_stack_best_objectives | 25/36 counterpoints | pass | 129 |
| evaluation | R345:tasks_with_three_or_more_best_views | 6/6 tasks need at least three best views | pass | 128,129,543,650 |
| evaluation | R345:min_distinct_best_views_per_task | 3 best views | pass | 129 |
| evaluation | R345:max_distinct_best_views_per_task | 4 best views | pass | 129 |
| evaluation | R345:counterpoint_rows | 46 counterpoint rows | pass | 129,650 |
| evaluation | R345:r344_support_verdicts | 30 support | pass | 129 |
| evaluation | R345:r344_counterpoint_verdicts | 16 counterpoints | pass | 129 |
| evaluation | R345:r344_mixed_or_weak_verdicts | 4 mixed/weak | pass | 129 |
| evaluation | R345:lens_summary_rows | 6 diagnostic lenses | pass | 129,543,650 |
| evaluation | R345:task_lens_card_rows | 6 tasks | pass | 128,129,543,650,651 |
| evaluation | R345:counterpoint_ledger_rows | 46 counterpoint rows | pass | 129,650 |
| evaluation | R346:overall | R346 | pass | 34,130,131,138,472,543,643,651 |
| evaluation | R346:tasks | 6 tasks | pass | 131,543,651,652,655 |
| evaluation | R346:datasets | 4 datasets | pass | 131,651,652,655 |
| evaluation | R346:case_groups | 30 case groups | pass | 131,543,651 |
| evaluation | R346:top_groups_per_task | top-5 | pass | 130,131,543,651,652,655 |
| evaluation | R346:tasks_with_top1_positive | 5/6 top-1 | pass | 131,543 |
| evaluation | R346:tasks_with_positive_in_top5 | 6/6 top-5 | pass | 131,543 |
| evaluation | R346:median_top5_recall | 0.188 | pass | 131,543,651 |
| evaluation | R346:median_top5_precision | 0.1991 | pass | 131,651 |
| evaluation | R346:median_top5_lift | 1.6508 | pass | 131,543,651,652 |
| evaluation | R346:median_top5_work | 0.0937 | pass | 131,543,651,652 |
| evaluation | R346:median_first_positive_work | 0.0378 | pass | 131,651 |
| evaluation | R346:tasks_with_actionable_case_cards | 6/6 actionable case cards | pass | 131,543 |
| evaluation | R346:tasks_with_counterpoints | 6/6 counterpoints | pass | 131 |
| evaluation | R346:tasks_with_three_or_more_best_views | 6/6 tasks need at least three best views | pass | 131,543 |
| evaluation | R346:min_distinct_best_views_per_task | 3 best views | pass | 131 |
| evaluation | R346:max_distinct_best_views_per_task | 4 best views | pass | 131 |
| evaluation | R346:task_case_card_rows | 6 tasks | pass | 131,543,651,652,655 |
| evaluation | R346:top_stack_evidence_rows | 30 case groups | pass | 131,543,651 |
| evaluation | R347:overall | R347 | pass | 34,132,133,134,138,472,543,643 |
| evaluation | R347:tasks | 6 tasks | pass | 133,134,543,652,653,655 |
| evaluation | R347:datasets | 4 datasets | pass | 133,652,653,655 |
| evaluation | R347:visible_views | 5 visible views | pass | 133,652 |
| evaluation | R347:view_task_rows | 30 view-task rows | pass | 133,652 |
| evaluation | R347:top_groups_per_view | top-5 groups | pass | 133,543,652 |
| evaluation | R347:operation_stack_top5_positive_tasks | 6/6 top-5 positive tasks | pass | 133,543 |
| evaluation | R347:operation_stack_top1_positive_tasks | 5/6 top-1 positive tasks | pass | 133,543 |
| evaluation | R347:operation_stack_median_top5_recall | 0.188 | pass | 133,543 |
| evaluation | R347:operation_stack_median_top5_lift | 1.6508 | pass | 133,543,652 |
| evaluation | R347:operation_stack_median_top5_work | 0.0937 | pass | 133,543,652 |
| evaluation | R347:operation_stack_median_first_positive_work | 0.0378 | pass | 133 |
| evaluation | R347:wins_vs_flat_top5_work | 6/6 wins vs flat top-5 work | pass | 133 |
| evaluation | R347:wins_vs_fixed_top5_recall | 5/6 wins vs fixed-session top-5 recall | pass | 133 |
| evaluation | R347:wins_vs_fixed_group_count | 4/6 wins vs fixed-session group count | pass | 133 |
| evaluation | R347:tasks_with_counterpoints | 6/6 tasks with counterpoints | pass | 133 |
| evaluation | R347:view_case_metric_rows | 30 view-task rows | pass | 133,652 |
| evaluation | R347:task_baseline_card_rows | 6 task cards | pass | 133,543 |
| evaluation | R347:baseline_pair_summary_rows | 24 baseline-pair rows | pass | 133 |
| evaluation | R347:top_group_contrast_rows | 124 top-group rows | pass | 133 |
| evaluation | R347:flat_top5_work_wins | 6/6 wins vs flat top-5 work | pass | 133 |
| evaluation | R347:fixed_session_top5_recall_wins | 5/6 wins vs fixed-session top-5 recall | pass | 133 |
| evaluation | R347:fixed_session_group_wins | 4/6 wins vs fixed-session group count | pass | 133 |
| evaluation | R347:fixed_session_first_positive_losses | fixed-session first-positive counterpoint 4/6 | pass | 133 |
| evaluation | R347:flat_top5_recall_losses | flat full-work recall counterpoint 6/6 | pass | 133 |
| evaluation | R348:overall | R348 | pass | 34,38,134,135,136,137,138,141 |
| evaluation | R348:tasks | 6 tasks | pass | 134,135,137,543,653,655,659 |
| evaluation | R348:datasets | 4 datasets | pass | 135,137,653,655,659 |
| evaluation | R348:objective_rows | 36 objective rows | pass | 134,135,543,653,655 |
| evaluation | R348:nondefault_action_rows | 27/36 non-default action rows | pass | 135 |
| evaluation | R348:default_best_rows | 9/36 default-best rows | pass | 135 |
| evaluation | R348:visible_non_oracle_best_rows | 36/36 visible non-oracle best rows | pass | 135,655 |
| evaluation | R348:view_change_rows | 25/36 view-change rows | pass | 135 |
| evaluation | R348:operation_stack_tuning_rows | 2/36 operation-stack tuning rows | pass | 135 |
| evaluation | R348:non_operation_stack_counterpoint_rows | 25/36 non-operation-stack counterpoints | pass | 135 |
| evaluation | R348:tasks_with_nondefault_actions | 6/6 tasks with non-default actions | pass | 135 |
| evaluation | R348:tasks_with_three_or_more_action_classes | 6/6 tasks with at least three action classes | pass | 135 |
| evaluation | R348:tasks_with_case_counterpoints | 6/6 tasks with case counterpoints | pass | 135 |
| evaluation | R348:median_gain_over_default | 0.1447 | pass | 135,543,653 |
| evaluation | R348:median_nondefault_gain_over_default | 0.6188 | pass | 135,653 |
| evaluation | R348:max_gain_over_default | 288.0 | pass | 135 |
| evaluation | R348:r335_actionability_cards | 6 actionability cards | pass | 135 |
| evaluation | R348:r341_actionable_objective_rows | 36 objective rows | pass | 134,135,543,653,655 |
| evaluation | R348:r347_visible_views | 5 visible views | pass | 135 |
| evaluation | R348:objective_counterfactual_rows | 36 objective rows | pass | 134,135,543,653,655 |
| evaluation | R348:action_class_summary_rows | 6 action classes | pass | 135 |
| evaluation | R348:task_action_counterfactual_card_rows | 6 task cards | pass | 543 |
| evaluation | R348:flat_counterpoint_action_rows | 7 flat counterpoint rows | pass | 135 |
| evaluation | R348:fixed_session_drilldown_rows | 7 fixed-session drilldown rows | pass | 135 |
| evaluation | R348:dataset_native_hierarchy_rows | 5 dataset-native rows | pass | 135 |
| evaluation | R348:raw_action_counterpoint_rows | 6 raw-action rows | pass | 135 |
| evaluation | R348:keep_default_operation_stack_rows | 9 keep-default rows | pass | 135 |
| evaluation | R348:retune_operation_stack_ranker_rows | 2 operation-stack ranker rows | pass | 135 |
| evaluation | R349:overall | R349 | pass | 34,136,137,138,465,469,473,479 |
| evaluation | R349:transfer_decisions_total | 96 transfer decisions | pass | 137,654 |
| evaluation | R349:aligned_decisions | 60 aligned decisions | pass | 137,543,654 |
| evaluation | R349:excluded_decisions | 36 excluded decisions | pass | 137 |
| evaluation | R349:aligned_objectives | 5 aligned objectives | pass | 137 |
| evaluation | R349:tasks | 6 tasks | pass | 137,543,655 |
| evaluation | R349:datasets | 4 datasets | pass | 137,655 |
| evaluation | R349:selected_visible_non_oracle_rows | 60/60 selected visible non-oracle | pass | 137 |
| evaluation | R349:best_visible_non_oracle_rows | 60/60 best visible non-oracle | pass | 137 |
| evaluation | R349:r340_r348_best_policy_match_rows | 50/60 best-policy matches | pass | 137 |
| evaluation | R349:r340_r348_best_policy_mismatch_rows | 10/60 best-policy mismatches | pass | 137 |
| evaluation | R349:selected_action_exact | 7/60 exact action | pass | 137 |
| evaluation | R349:selected_r348_policy_exact | 7/60 policy exact | pass | 137 |
| evaluation | R349:selected_r340_exact_best | 13/60 R340 exact best | pass | 137 |
| evaluation | R349:selected_view_exact | 11/60 view exact | pass | 137 |
| evaluation | R349:selected_ranker_exact | 27/60 ranker exact | pass | 137 |
| evaluation | R349:selected_within_tolerance | 35/60 within tolerance | pass | 137 |
| evaluation | R349:selected_beats_default | 30/60 beats default | pass | 137 |
| evaluation | R349:default_within_tolerance | 26/60 default within tolerance | pass | 137 |
| evaluation | R349:nondefault_target_rows | 42 non-default target rows | pass | 137 |
| evaluation | R349:nondefault_target_action_exact | 2/42 non-default exact action | pass | 137 |
| evaluation | R349:nondefault_target_within_tolerance | 24/42 non-default within tolerance | pass | 137 |
| evaluation | R349:nondefault_target_selected_default_action | 2/42 selected default action | pass | 137 |
| evaluation | R349:leave_task_action_exact | leave-task 4/30 exact action | pass | 137 |
| evaluation | R349:leave_dataset_action_exact | leave-dataset 3/30 exact action | pass | 137 |
| evaluation | R349:leave_task_within_tolerance | leave-task 18/30 within tolerance | pass | 137 |
| evaluation | R349:leave_dataset_within_tolerance | leave-dataset 17/30 within tolerance | pass | 137 |
| evaluation | R349:sequence_objective_excluded_rows | 36 sequence objective exclusions | pass | 137 |
| evaluation | R349:r348_untransferred_objective_rows | 6 R348 untransferred objectives | pass | 137 |
| evaluation | R349:decision_rows | 60 aligned decisions | pass | 137,543,654 |
| evaluation | R349:summary_rows | 13 summary rows | pass | 137 |
| evaluation | R349:confusion_rows | 16 action-confusion rows | pass | 137 |
| evaluation | R349:task_card_rows | 12 task cards | pass | 137 |
| evaluation | R349:excluded_rows | 36 excluded decisions | pass | 137 |
| evaluation | R349:untransferred_rows | 6 R348 untransferred objectives | pass | 137 |
| evaluation | R350:overall | R350 | pass | 34,138,139,182,197,198,472,481 |
| evaluation | R350:tasks | 6 tasks | pass | 139,198,543,655 |
| evaluation | R350:datasets | 4 datasets | pass | 139,198,655 |
| evaluation | R350:objective_rows | 36 objective rows | pass | 139,543,655 |
| evaluation | R350:action_classes | 6 action classes | pass | 139 |
| evaluation | R350:packets_with_top5_positive | 6/6 top-5 positive packets | pass | 139,198 |
| evaluation | R350:packets_with_top1_positive | 5/6 top-1 positive packets | pass | 139 |
| evaluation | R350:packets_with_30pct_work_budget | 4/6 strict 30% work packets | pass | 139,198 |
| evaluation | R350:packets_with_first_positive_10pct_budget | 4/6 first-positive <=10% work packets | pass | 139 |
| evaluation | R350:packets_with_baseline_counterpoints | 6/6 baseline counterpoints | pass | 139,655 |
| evaluation | R350:packets_with_nondefault_actions | 6/6 non-default action packets | pass | 139 |
| evaluation | R350:packets_with_three_or_more_action_classes | 6/6 three-action-class packets | pass | 139 |
| evaluation | R350:operation_stack_beats_flat_work_tasks | 6/6 beats flat work | pass | 139 |
| evaluation | R350:operation_stack_beats_fixed_recall_tasks | 5/6 beats fixed recall | pass | 139 |
| evaluation | R350:operation_stack_fewer_groups_than_fixed_tasks | 4/6 fewer groups than fixed | pass | 139 |
| evaluation | R350:median_top5_work | 0.0937 | pass | 139,543 |
| evaluation | R350:median_first_positive_work | 0.0378 | pass | 139 |
| evaluation | R350:median_top5_recall | 0.188 | pass | 139,543 |
| evaluation | R350:median_top5_lift | 1.6508 | pass | 139,543 |
| evaluation | R350:nondefault_objective_rows | 27/36 non-default objective rows | pass | 139,543,655 |
| evaluation | R350:visible_non_oracle_best_rows | 36/36 visible non-oracle best rows | pass | 139,655 |
| evaluation | R350:median_nondefault_gain_over_default | 0.6188 | pass | 139 |
| evaluation | R350:max_gain_over_default | 288.0 | pass | 139 |
| evaluation | R350:r349_aligned_transfer_decisions | 60 aligned transfer decisions | pass | 139 |
| evaluation | R350:r349_selected_within_tolerance | 35/60 within tolerance | pass | 139 |
| evaluation | R350:r349_selected_action_exact | 7/60 exact action | pass | 139 |
| evaluation | R350:r349_nondefault_target_within_tolerance | 24/42 non-default within tolerance | pass | 139 |
| evaluation | R350:task_packet_rows | 6 task packets | pass | 139 |
| evaluation | R350:objective_packet_rows | 36 objective packets | pass | 139 |
| evaluation | R350:budget_summary_rows | 7 budget rows | pass | 139 |
| evaluation | R350:budget_top5_positive | 6/6 top-5 positive packets | pass | 139,198 |
| evaluation | R350:budget_30pct_packets | 4/6 strict 30% work packets | pass | 139,198 |
| evaluation | R350:budget_actionable_counterfactual | 27/36 non-default objective rows | pass | 139,543,655 |

## Guardrails

| Doc | Guardrail | Status | Occurrences | Occurrence lines | Unguarded overclaim lines |
|---|---|---|---:|---|---|
| evaluation | human_utility | pass | 12 | 15,35,149,543,615,619,719,722,724,725,729,733 | none |
| evaluation | automatic_boundary | pass | 10 | 34,35,234,490,543,718,719,741,750,855 | none |
| evaluation | ecosystem_compatibility | pass | 8 | 12,15,58,543,614,718,736,849 | none |
| evaluation | universal_selector | pass | 12 | 34,35,128,136,234,419,543,645,735,736,738,742 | none |
| zh_claim_setup | human_utility | pass | 12 | 26,28,36,42,43,47,49,51,52,53,78,102 | none |
| zh_claim_setup | automatic_boundary | pass | 12 | 23,25,26,47,48,50,51,52,53,78,150,152 | none |
| zh_claim_setup | ecosystem_compatibility | pass | 8 | 22,96,114,181,228,265,266,267 | none |
| zh_claim_setup | universal_selector | pass | 12 | 26,34,36,37,38,41,42,43,44,45,46,47 | none |
| zh_main | human_utility | pass | 8 | 60,180,240,374,413,554,565,587 | none |
| zh_main | automatic_boundary | pass | 3 | 239,378,409 | none |
| zh_main | ecosystem_compatibility | pass | 12 | 138,374,501,509,510,513,558,585,588,597,607,608 | none |
| zh_main | universal_selector | pass | 7 | 238,403,409,413,547,581,587 | none |
| en_main | human_utility | pass | 7 | 70,100,113,243,258,640,719 | none |
| en_main | automatic_boundary | pass | 4 | 251,571,607,835 | none |
| en_main | ecosystem_compatibility | pass | 12 | 69,753,755,763,765,766,767,774,836,837,867,872 | none |
| en_main | universal_selector | pass | 8 | 251,462,465,521,594,641,835,866 | none |
