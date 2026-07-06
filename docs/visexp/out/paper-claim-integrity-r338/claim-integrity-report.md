# Paper Claim Integrity Audit R338

R338 mechanically audits the current profiling-paper claim against R320-R347 result artifacts and the Chinese/English paper text. It does not fetch, sync, create, or relabel datasets.

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

## Text Coverage

| Doc | Key | Tokens | Status | Lines |
|---|---|---|---|---|
| evaluation | R320 headline operations | 34,539 / 34539 | pass | 15,129,151,267,299,364,371,373 |
| evaluation | R320 top5 work | 0.0937 / 9.37% | pass | 15,103,105,152,208,299,368,369 |
| evaluation | R333 budget30 recall | 0.3900 / 0.39 | pass | 211,299,394,465 |
| evaluation | R334 fragmentation | 5/6 / -54.0 / fewer groups | pass | 15,53,54,71,99,103,105,141 |
| evaluation | R335 actionability | actionability / 6/6 / optimization | pass | 5,15,57,76,85,87,99,100 |
| evaluation | R336 visible policies | 15 visible / 15 个 / 6 diagnostic | pass | 15,101,299,397,401,406 |
| evaluation | R337 fixed recall | 25% / 0.2000 / 16.0 | pass | 15,194,196,299,398 |
| evaluation | R339 sequence adequacy | R339 / 0.4669 / 0.9103 | pass | 13,15,204,212,215,219,299,399 |
| evaluation | R340 policy transfer | R340 / 96 / 62/96 / 72/96 | pass | 15,115,117,218,221,222,223,224 |
| evaluation | R341 mechanism attribution | R341 / 36/36 / 27/36 / 34/96 | pass | 15,100,231,232,233,234,299,399 |
| evaluation | R342 profile spec composition | R342 / 12/12 / 9/12 / 0.8267 | pass | 12,15,78,80,83,85,296,299 |
| evaluation | R344 metric consistency | R344 / 30 / 16 / groups | pass | 12,13,15,39,41,50,64,79 |
| evaluation | R345 diagnostic lens portfolio | R345 / 6 diagnostic lenses / 11/36 / 25/36 | pass | 15,100,101,102,299,399,406,407 |
| evaluation | R346 diagnostic casebook | R346 / 30 case groups / 5/6 / 1.6508 | pass | 15,53,54,71,99,102,103,105 |
| evaluation | R347 case baseline contrast | R347 / 5 visible views / 6/6 / 5/6 / 4/6 | pass | 15,41,45,53,54,70,71,72 |
| zh_main | R320 headline | 0.0937 / 9.37 / 285.0 / 157.5 | pass | 63,73,79,402,409,419,420,481 |
| zh_main | R333 headline | 0.3900 / 0.390 | pass | 68,397,449,481,512,583,699 |
| zh_main | R337 headline | 0.2000 / 16.0 / 50.0 | pass | 72,480,586,703 |
| zh_main | R339 headline | 0.4669 / 0.9103 / 0.3467 | pass | 73,481,587,704 |
| zh_main | R340 headline | R340 / 62/96 / 72/96 / 69/96 | pass | 74,81,482,483,573,588,599,705 |
| zh_main | R341 headline | R341 / 36/36 / 27/36 / 34/96 | pass | 75,81,483,486,573,589,599,706 |
| zh_main | R342 headline | R342 / 12/12 / 9/12 / 0.8267 | pass | 76,81,484,574,590 |
| zh_main | R344 headline | R344 / 30 / 16 / nDCG | pass | 55,61,62,65,66,67,68,69 |
| zh_main | R345 headline | R345 / 6 / 11/36 / 25/36 | pass | 3,16,17,18,30,50,54,55 |
| zh_main | R346 headline | R346 / 30 / 5/6 / 1.6508 | pass | 59,60,61,63,65,66,67,68 |
| zh_main | R347 headline | R347 / 5 / 6/6 / 5/6 / 4/6 | pass | 12,22,46,48,49,50,59,60 |
| en_main | R320 headline | 0.0937 / 9.37 / 285.0 / 157.5 | pass | 45,48,126,359,361,379,388,571 |
| en_main | R333 headline | 0.3900 / 0.390 | pass | 70,360,379,446,574 |
| en_main | R337 headline | 0.2000 / 16.0 / 50.0 | pass | 89,90,91,559,561,787,788 |
| en_main | R339 headline | 0.4669 / 0.9103 / 0.3467 | pass | 94,95,96,575,576,577,790,791 |
| en_main | R340 headline | R340 / 62 of 96 / 72 of 96 / 69 of 96 | pass | 579,633,792,883 |
| en_main | R341 headline | R341 / 36 of 36 / 27 of 36 / 34 of 96 | pass | 104,105,106,589,609,633,795,884 |
| en_main | R342 headline | R342 / 12/12 / 9/12 / 0.8267 | pass | 109,112,113,595,596,599,601,633 |
| en_main | R344 headline | R344 / 30 / 16 / nDCG | pass | 69,76,90,93,95,101,115,116 |
| en_main | R345 headline | R345 / 6 / 11/36 / 25/36 | pass | 42,47,51,52,56,75,76,77 |
| en_main | R346 headline | R346 / 30 / 5/6 / 1.6508 | pass | 69,76,93,95,115,123,124,125 |
| en_main | R347 headline | R347 / 5 / 6/6 / 5/6 / 4/6 | pass | 39,40,42,47,48,51,70,71 |
| zh_claim_setup | two abstractions | 两个核心抽象 / operation stack | pass | 7,23,25,77,80,81,82,84 |
| zh_claim_setup | R337 result | R337 / 0.2000 / 16.0 | pass | 35,36,44,115,116,117 |
| zh_claim_setup | R339 result | R339 / 0.4669 / 0.9103 | pass | 36,37,44,116,117,118,257 |
| zh_claim_setup | R340 result | R340 / 62/96 / 72/96 / 69/96 | pass | 37,38,44,116,118,119 |
| zh_claim_setup | R341 result | R341 / 36/36 / 27/36 / 34/96 | pass | 38,41,44,116,119,122 |
| zh_claim_setup | R342 result | R342 / 12/12 / 9/12 / 0.8267 | pass | 39,44,116,120 |
| zh_claim_setup | R344 result | R344 / 30 / 16 / nDCG | pass | 22,23,24,26,28,31,32,34 |
| zh_claim_setup | R345 result | R345 / 6 / 11/36 / 25/36 | pass | 3,22,23,24,25,26,27,28 |
| zh_claim_setup | R346 result | R346 / 30 / 5/6 / 1.6508 | pass | 22,23,26,28,31,32,34,35 |
| zh_claim_setup | R347 result | R347 / 5 / 6/6 / 5/6 / 4/6 | pass | 3,22,23,24,25,26,27,28 |
| evaluation | R320:datasets | 4 | pass | 12,13,14,15,41,45,47,53 |
| evaluation | R320:tasks | 6 | pass | 3,4,12,13,15,32,41,42 |
| evaluation | R320:operations | 34,539 | pass | 15,129,151,267,299,364,371,373 |
| evaluation | R320:positives | 3,699 | pass | 15,151,374,377,381,384,395,470 |
| evaluation | R320:policies | 144 | pass | 15,150,379,384,394,400,476,481 |
| evaluation | R320:operation_stack_top5_work_median | 0.0937 | pass | 103,105,208,384,400,407,408,466 |
| evaluation | R320:flat_top5_work_median | 1.0 | pass | 15,197,209,299,363,366,380,384 |
| evaluation | R320:operation_stack_groups_median | 157.5 | pass | 15,155,299,384,481 |
| evaluation | R320:fixed_session_groups_median | 285.0 | pass | 15,155,299,384,481 |
| evaluation | R320:top5_recall_wins_vs_fixed | 5/6 | pass | 15,53,54,71,99,103,105,141 |
| evaluation | R320:ap_wins_vs_width | 6/6 | pass | 15,85,99,100,101,103,105,141 |
| evaluation | R333:operation_stack:query_aware_budget30_median_recall | 0.3900 | pass | 211,299,394 |
| evaluation | R333:flat:width_budget30_median_recall | 0.0000 | pass | 299,394 |
| evaluation | R333:fixed_session:query_aware_budget30_median_recall | 0.3559 | pass | 299,394 |
| evaluation | R333:dataset_native:query_aware_budget30_median_recall | 0.3377 | pass | 299,394 |
| evaluation | R333:raw_action_stack:query_aware_budget30_median_recall | 0.3325 | pass | 299,394 |
| evaluation | R337:target25_tasks_reached | 6/6 | pass | 15,85,99,100,101,103,105,141 |
| evaluation | R337:target25_median_work | 0.2000 | pass | 15,196,299,398 |
| evaluation | R337:target25_median_groups | 16.0 | pass | 15,196,299,398 |
| evaluation | R337:target10_tasks_reached | 6/6 | pass | 15,85,99,100,101,103,105,141 |
| evaluation | R337:target10_median_groups | 12.5 | pass | 200,398 |
| evaluation | R337:target50_tasks_reached | 5/6 | pass | 15,53,54,71,99,103,105,141 |
| evaluation | R337:flat_target25_median_work | 1.0000 | pass | 15,197,209,299,398 |
| evaluation | R337:fixed_target25_median_groups | 50.0 | pass | 15,198,299,398 |
| evaluation | R337:fixed_target10_median_groups | 37.5 | pass | 200,398 |
| evaluation | R337:default_vs_flat_target25_work_wins | 6/6 | pass | 15,85,99,100,101,103,105,141 |
| evaluation | R337:default_vs_fixed_target25_group_wins | 5/6 | pass | 15,53,54,71,99,103,105,141 |
| evaluation | R337:default_vs_fixed_target10_group_wins | 5/6 | pass | 15,53,54,71,99,103,105,141 |
| evaluation | R337:target25_csv_median_work | 0.2000 | pass | 15,196,299,398 |
| evaluation | R337:target25_csv_group_wins_vs_fixed | 5/6 | pass | 15,53,54,71,99,103,105,141 |
| evaluation | R339:overall | pass | pass | 14,51,140,243,375,376,379,382 |
| evaluation | R339:datasets | 4 | pass | 12,13,14,15,41,45,47,53 |
| evaluation | R339:tasks | 6 | pass | 3,4,12,13,15,32,41,42 |
| evaluation | R339:policies_scored | 144 | pass | 15,150,379,384,394,400,476,481 |
| evaluation | R339:hidden_labels_used_only_for_scoring | hidden labels only for scoring | pass | 400,408 |
| evaluation | R339:top5_median_operation_work | 0.0937 | pass | 103,105,208,384,400,407,408,466 |
| evaluation | R339:top5_median_positive_session_recall | 0.2629 | pass | 209,400 |
| evaluation | R339:top5_fixed_positive_session_recall | 0.0160 | pass | 210,400 |
| evaluation | R339:top5_flat_operation_work | 1.0000 | pass | 15,197,209,299,398 |
| evaluation | R339:budget30_median_positive_operation_recall | 0.3900 | pass | 211,299,394 |
| evaluation | R339:budget30_median_positive_session_recall | 0.4669 | pass | 15,212,299,400 |
| evaluation | R339:budget30_median_session_work | 0.3467 | pass | 15,213,299,400 |
| evaluation | R339:budget30_fixed_positive_session_recall | 0.3230 | pass | 15,213,299,400 |
| evaluation | R339:budget30_raw_action_positive_session_recall | 0.5147 | pass | 15,215,299,400 |
| evaluation | R339:budget30_raw_action_session_work | 0.9103 | pass | 15,215,299,400 |
| evaluation | R339:top5_operation_work_lt_flat_tasks | 6/6 | pass | 15,85,99,100,101,103,105,141 |
| evaluation | R339:budget30_session_recall_gt_fixed_tasks | 6/6 | pass | 15,85,99,100,101,103,105,141 |
| evaluation | R339:budget30_session_work_lt_raw_action_tasks | 5/6 | pass | 15,53,54,71,99,103,105,141 |
| evaluation | R339:csv_default_median_top5_operation_work | 0.0937 | pass | 103,105,208,384,400,407,408,466 |
| evaluation | R339:csv_default_median_top5_positive_session_recall | 0.2629 | pass | 209,400 |
| evaluation | R339:csv_default_median_budget30_positive_operation_recall | 0.3900 | pass | 211,299,394 |
| evaluation | R339:csv_default_median_budget30_positive_session_recall | 0.4669 | pass | 15,212,299,400 |
| evaluation | R339:csv_default_median_budget30_session_work | 0.3467 | pass | 15,213,299,400 |
| evaluation | R339:csv_budget30_session_recall_wins_vs_fixed | 6/6 | pass | 15,85,99,100,101,103,105,141 |
| evaluation | R339:csv_budget30_session_work_wins_vs_raw_action | 5/6 | pass | 15,53,54,71,99,103,105,141 |
| evaluation | R340:overall | pass | pass | 14,51,140,243,375,376,379,382 |
| evaluation | R340:tasks | 6 | pass | 3,4,12,13,15,32,41,42 |
| evaluation | R340:visible_policies | 15 | pass | 12,13,15,155,185,299,352,356 |
| evaluation | R340:objectives | 8 | pass | 12,13,14,15,32,33,73,85 |
| evaluation | R340:total_decisions | 96 | pass | 15,115,117,221,222,223,224,225 |
| evaluation | R340:exact_best_decisions | 31 | pass | 15,132,134,138,140,143,165,222 |
| evaluation | R340:within_tolerance_decisions | 62 | pass | 13,15,209,222,299,377,400,401 |
| evaluation | R340:selected_beats_width | 72 | pass | 12,15,223,299,325,336,352,364 |
| evaluation | R340:selected_beats_fixed | 69 | pass | 15,151,212,223,299,327,342,354 |
| evaluation | R340:selected_beats_flat | 41 | pass | 13,15,100,224,231,299,328,342 |
| evaluation | R340:operation_stack_selected | 16 | pass | 13,15,101,196,210,225,243,299 |
| evaluation | R340:leave_task_decisions | 48 | pass | 337,338,363,436,451,453 |
| evaluation | R340:leave_task_within_tolerance | 32 | pass | 12,14,15,36,40,43,44,47 |
| evaluation | R340:leave_dataset_decisions | 48 | pass | 337,338,363,436,451,453 |
| evaluation | R340:leave_dataset_within_tolerance | 30 | pass | 12,15,39,50,79,91,99,101 |
| evaluation | R340:decision_rows | 96 | pass | 15,115,117,221,222,223,224,225 |
| evaluation | R340:objective_rows | 16 | pass | 13,15,101,196,210,225,243,299 |
| evaluation | R340:selected_policy_visible_rows | 96/96 | pass | 229,230 |
| evaluation | R340:best_policy_visible_rows | 96/96 | pass | 229,230 |
| evaluation | R340:selected_policy_no_oracle_or_label_drilldown | 96/96 | pass | 229,230 |
| evaluation | R340:best_policy_no_oracle_or_label_drilldown | 96/96 | pass | 229,230 |
| evaluation | R340:leave_task_excludes_target_task | 96/96 | pass | 229,230 |
| evaluation | R340:leave_dataset_excludes_target_dataset | 96/96 | pass | 229,230 |
| evaluation | R341:overall | R341 | pass | 15,100,231,299,399,402,406,561 |
| evaluation | R341:tasks | 6 tasks | pass | 15,100,299,402,406 |
| evaluation | R341:objective_rows | 36 objective rows | pass | 15,100,299,402,406 |
| evaluation | R341:objective_best_policy_visible_rows | 36/36 best policies visible | pass | 402 |
| evaluation | R341:objective_best_policy_non_oracle_rows | 36/36 best policies non-oracle | pass | 402 |
| evaluation | R341:actionable_objective_rows | 36/36 objective rows have optimization actions | pass | 15,299,402 |
| evaluation | R341:nondefault_best_objective_rows | 27/36 best visible policies are non-default | pass | 15,299,402 |
| evaluation | R341:transfer_decisions | 96 transfer decisions | pass | 402 |
| evaluation | R341:transfer_misses | 34/96 transfer decisions | pass | 402 |
| evaluation | R341:transfer_misses_with_view_change | 32/34 misses change view | pass | 402 |
| evaluation | R341:transfer_misses_with_ranker_change | 26/34 change ranker | pass | 402 |
| evaluation | R341:high_regret_transfer_misses | 29/34 high-regret misses | pass | 299,402 |
| evaluation | R341:stack_depth_tradeoff_tasks | stack-depth signals on 6/6 | pass | 402 |
| evaluation | R341:transfer_policy_signal_tasks | transfer-policy signals on 6/6 | pass | 402 |
| evaluation | R341:critical_rank_feature_tasks | critical features on 4/6 | pass | 402 |
| evaluation | R341:misleading_feature_tasks | misleading features on 2/6 | pass | 15,402 |
| evaluation | R341:tasks_with_three_or_more_mechanism_labels | three or more mechanism labels on 6/6 | pass | 402 |
| evaluation | R342:overall | R342 | pass | 12,15,78,296,299,301,399,403 |
| evaluation | R342:tasks | 6 tasks | pass | 15,299,403,404,489 |
| evaluation | R342:profile_spec_variants | 12 profile-spec variants | pass | 403,489 |
| evaluation | R342:composition_variants | 12/12 compose | pass | 15,403 |
| evaluation | R342:prompt_session_free_variants | 12/12 prompt/session-free | pass | 403 |
| evaluation | R342:rule_score_rank_policy_variants | rank_mode=rule-score | pass | 15,403,489 |
| evaluation | R342:ap_improves_vs_width_variants | 9/12 variants | pass | 15,403,489 |
| evaluation | R342:top5_lift_improves_vs_width_variants | 8/12 | pass | 15 |
| evaluation | R342:first_positive_work_improves_vs_width_variants | 10/12 | pass | 15,403,489 |
| evaluation | R342:tasks_with_ap_improvement_any_depth | 5/6 | pass | 15,299 |
| evaluation | R342:tasks_with_first_positive_improvement_any_depth | 6/6 | pass | 15,299,403,489 |
| evaluation | R342:tasks_where_coarse_reduces_groups | 6/6 tasks | pass | 15,299,403,489 |
| evaluation | R342:median_coarse_group_reduction | 0.8267 | pass | 15,403,489 |
| evaluation | R342:tasks_where_depth_choice_changes_objective | 3/6 tasks | pass | 403 |
| evaluation | R342:best_ap_semantic_depth_tasks | semantic 4 / coarse 2 | pass | 15,403,489 |
| evaluation | R342:best_ap_coarse_depth_tasks | semantic 4 / coarse 2 | pass | 15,403,489 |
| evaluation | R342:committed_variant_csv_matches_sources | 12/12 | pass | 12,15,296,403,404,489 |
| evaluation | R342:committed_task_csv_matches_sources | 6/6 | pass | 15,299,403,489 |
| evaluation | R344:overall | R344 | pass | 15,88,99,100,299,399,405,406 |
| evaluation | R344:tasks | 6 tasks | pass | 15,100,299,405,406 |
| evaluation | R344:metric_comparisons | 50 baseline-metric comparisons | pass | 15,299,405,482 |
| evaluation | R344:task_metric_delta_rows | 300 task-metric deltas | pass | 405 |
| evaluation | R344:support_verdicts | 30 support verdicts | pass | 15,405,482 |
| evaluation | R344:counterpoint_verdicts | 16 counterpoints | pass | 15,405,482 |
| evaluation | R344:mixed_or_weak_verdicts | 4 mixed/weak | pass | 15,405,482 |
| evaluation | R344:required_metric_count | groups | pass | 15,99,100,299,482 |
| evaluation | R344:required_groups_metric_present | groups | pass | 15,99,100,299,482 |
| evaluation | R344:metric_summary_rows | 50 | pass | 15,299,405,482 |
| evaluation | R344:task_delta_rows | 300 | pass | 15,299,405 |
| evaluation | R344:summary_support_verdicts | 30 support verdicts | pass | 15,405,482 |
| evaluation | R344:summary_counterpoint_verdicts | 16 counterpoints | pass | 15,405,482 |
| evaluation | R344:summary_mixed_or_weak_verdicts | 4 mixed/weak | pass | 15,405,482 |
| evaluation | R344:required_metric_groups_in_summary | groups | pass | 15,99,100,299,482 |
| evaluation | R344:flat_ap_wins | flat AP 6/6 | pass | 99 |
| evaluation | R344:flat_budget30_recall_wins | budget30 recall 6/6 | pass | 99 |
| evaluation | R344:flat_work_to_first_positive_wins | work-to-first-positive 6/6 | pass | 99 |
| evaluation | R344:fixed_session_top5_f1_wins | top-5 F1 5/6 | pass | 99 |
| evaluation | R344:fixed_session_group_wins | groups 4/6 | pass | 99 |
| evaluation | R344:width_ap_wins | width AP 6/6 | pass | 99 |
| evaluation | R344:width_budget30_recall_wins | budget30 recall 5/6 | pass | 99 |
| evaluation | R344:flat_ndcg_losses | nDCG | pass | 15,299,405,482,560 |
| evaluation | R344:flat_top5_recall_losses | top-k recall | pass | 15,299,405,482 |
| evaluation | R345:overall | R345 | pass | 15,100,101,102,299,399,406,407 |
| evaluation | R345:tasks | 6 tasks | pass | 15,100,101,299,406,407 |
| evaluation | R345:datasets | 4 datasets | pass | 15,101,406,407 |
| evaluation | R345:lens_count | 6 diagnostic lenses | pass | 15,101,299,406 |
| evaluation | R345:objective_rows | 36 objective rows | pass | 15,100,101,299,406 |
| evaluation | R345:task_cards | 6/6 actionable task cards | pass | 101 |
| evaluation | R345:actionable_task_cards | 6/6 actionable task cards | pass | 101 |
| evaluation | R345:distinct_optimization_actions | 5 distinct optimization actions | pass | 101 |
| evaluation | R345:default_operation_stack_best_objectives | 9/36 default operation-stack | pass | 101 |
| evaluation | R345:operation_stack_family_best_objectives | 11/36 operation-stack family | pass | 101 |
| evaluation | R345:non_operation_stack_best_objectives | 25/36 counterpoints | pass | 101 |
| evaluation | R345:tasks_with_three_or_more_best_views | 6/6 tasks need at least three best views | pass | 15,100,101,299,406 |
| evaluation | R345:min_distinct_best_views_per_task | 3 best views | pass | 101 |
| evaluation | R345:max_distinct_best_views_per_task | 4 best views | pass | 101 |
| evaluation | R345:counterpoint_rows | 46 counterpoint rows | pass | 101,406 |
| evaluation | R345:r344_support_verdicts | 30 support | pass | 15,101 |
| evaluation | R345:r344_counterpoint_verdicts | 16 counterpoints | pass | 15,101 |
| evaluation | R345:r344_mixed_or_weak_verdicts | 4 mixed/weak | pass | 15,101 |
| evaluation | R345:lens_summary_rows | 6 diagnostic lenses | pass | 15,101,299,406 |
| evaluation | R345:task_lens_card_rows | 6 tasks | pass | 15,100,101,299,406,407 |
| evaluation | R345:counterpoint_ledger_rows | 46 counterpoint rows | pass | 101,406 |
| evaluation | R346:overall | R346 | pass | 15,102,103,299,399,407,408,562 |
| evaluation | R346:tasks | 6 tasks | pass | 15,103,299,407,408 |
| evaluation | R346:datasets | 4 datasets | pass | 15,103,407,408 |
| evaluation | R346:case_groups | 30 case groups | pass | 103,299,407 |
| evaluation | R346:top_groups_per_task | top-5 | pass | 15,102,103,299,407,408 |
| evaluation | R346:tasks_with_top1_positive | 5/6 top-1 | pass | 103,299 |
| evaluation | R346:tasks_with_positive_in_top5 | 6/6 top-5 | pass | 103,299 |
| evaluation | R346:median_top5_recall | 0.188 | pass | 103,407 |
| evaluation | R346:median_top5_precision | 0.1991 | pass | 103,407 |
| evaluation | R346:median_top5_lift | 1.6508 | pass | 15,103,299,407,408 |
| evaluation | R346:median_top5_work | 0.0937 | pass | 103,407,408 |
| evaluation | R346:median_first_positive_work | 0.0378 | pass | 103,407 |
| evaluation | R346:tasks_with_actionable_case_cards | 6/6 actionable case cards | pass | 103,299 |
| evaluation | R346:tasks_with_counterpoints | 6/6 counterpoints | pass | 103 |
| evaluation | R346:tasks_with_three_or_more_best_views | 6/6 tasks need at least three best views | pass | 15,103,299 |
| evaluation | R346:min_distinct_best_views_per_task | 3 best views | pass | 103 |
| evaluation | R346:max_distinct_best_views_per_task | 4 best views | pass | 103 |
| evaluation | R346:task_case_card_rows | 6 tasks | pass | 15,103,299,407,408 |
| evaluation | R346:top_stack_evidence_rows | 30 case groups | pass | 103,299,407 |
| evaluation | R347:overall | R347 | pass | 15,104,105,239,299,399,408,563 |
| evaluation | R347:tasks | 6 tasks | pass | 15,105,299,408 |
| evaluation | R347:datasets | 4 datasets | pass | 15,105,408 |
| evaluation | R347:visible_views | 5 visible views | pass | 15,105,408 |
| evaluation | R347:view_task_rows | 30 view-task rows | pass | 105,408 |
| evaluation | R347:top_groups_per_view | top-5 groups | pass | 15,105,299,408 |
| evaluation | R347:operation_stack_top5_positive_tasks | 6/6 top-5 positive tasks | pass | 105,299 |
| evaluation | R347:operation_stack_top1_positive_tasks | 5/6 top-1 positive tasks | pass | 105,299 |
| evaluation | R347:operation_stack_median_top5_recall | 0.188 | pass | 105 |
| evaluation | R347:operation_stack_median_top5_lift | 1.6508 | pass | 15,105,299,408 |
| evaluation | R347:operation_stack_median_top5_work | 0.0937 | pass | 105,408 |
| evaluation | R347:operation_stack_median_first_positive_work | 0.0378 | pass | 105 |
| evaluation | R347:wins_vs_flat_top5_work | 6/6 wins vs flat top-5 work | pass | 105 |
| evaluation | R347:wins_vs_fixed_top5_recall | 5/6 wins vs fixed-session top-5 recall | pass | 105 |
| evaluation | R347:wins_vs_fixed_group_count | 4/6 wins vs fixed-session group count | pass | 105 |
| evaluation | R347:tasks_with_counterpoints | 6/6 tasks with counterpoints | pass | 105 |
| evaluation | R347:view_case_metric_rows | 30 view-task rows | pass | 105,408 |
| evaluation | R347:task_baseline_card_rows | 6 task cards | pass | 105,299 |
| evaluation | R347:baseline_pair_summary_rows | 24 baseline-pair rows | pass | 105 |
| evaluation | R347:top_group_contrast_rows | 124 top-group rows | pass | 105 |
| evaluation | R347:flat_top5_work_wins | 6/6 wins vs flat top-5 work | pass | 105 |
| evaluation | R347:fixed_session_top5_recall_wins | 5/6 wins vs fixed-session top-5 recall | pass | 105 |
| evaluation | R347:fixed_session_group_wins | 4/6 wins vs fixed-session group count | pass | 105 |
| evaluation | R347:fixed_session_first_positive_losses | fixed-session first-positive counterpoint 4/6 | pass | 105 |
| evaluation | R347:flat_top5_recall_losses | flat full-work recall counterpoint 6/6 | pass | 105 |

## Guardrails

| Doc | Guardrail | Status | Occurrences | Occurrence lines | Unguarded overclaim lines |
|---|---|---|---:|---|---|
| evaluation | human_utility | pass | 12 | 15,299,371,375,458,461,463,464,468,472,473,475 | none |
| evaluation | automatic_boundary | pass | 6 | 246,299,457,458,480,489 | none |
| evaluation | ecosystem_compatibility | pass | 8 | 12,15,30,299,370,457,475,573 | none |
| evaluation | universal_selector | pass | 12 | 15,100,193,299,401,474,475,477,481,489,546,561 | none |
| zh_claim_setup | human_utility | pass | 12 | 26,28,36,42,43,44,80,81,82,89,90,93 | none |
| zh_claim_setup | automatic_boundary | pass | 5 | 23,25,26,44,247 | none |
| zh_claim_setup | ecosystem_compatibility | pass | 8 | 22,74,92,151,198,235,236,237 | none |
| zh_claim_setup | universal_selector | pass | 12 | 26,34,36,37,38,41,42,43,44,109,110,111 | none |
| zh_main | human_utility | pass | 10 | 81,207,387,430,487,600,667,677,711,712 | none |
| zh_main | automatic_boundary | pass | 1 | 81 | none |
| zh_main | ecosystem_compatibility | pass | 12 | 51,165,623,631,632,635,671,694,715,726,736,737 | none |
| zh_main | universal_selector | pass | 12 | 78,81,475,481,486,488,598,660,697,702,705,708 | none |
| en_main | human_utility | pass | 5 | 127,169,183,637,696 | none |
| en_main | automatic_boundary | pass | 2 | 638,815 | none |
| en_main | ecosystem_compatibility | pass | 12 | 729,731,739,741,742,743,749,750,816,905,906,908 | none |
| en_main | universal_selector | pass | 9 | 122,422,425,578,587,630,638,778,785 | none |
