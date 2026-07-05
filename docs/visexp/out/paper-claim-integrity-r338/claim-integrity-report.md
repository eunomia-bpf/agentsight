# Paper Claim Integrity Audit R338

R338 mechanically audits the current profiling-paper claim against R320-R345 result artifacts and the Chinese/English paper text. It does not fetch, sync, create, or relabel datasets.

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

## Text Coverage

| Doc | Key | Tokens | Status | Lines |
|---|---|---|---|---|
| evaluation | R320 headline operations | 34,539 / 34539 | pass | 15,125,147,263,295,360,367,369 |
| evaluation | R320 top5 work | 0.0937 / 9.37% | pass | 15,148,204,295,364,365,368,380 |
| evaluation | R333 budget30 recall | 0.3900 / 0.39 | pass | 207,295,390,459 |
| evaluation | R334 fragmentation | 5/6 / -54.0 / fewer groups | pass | 15,53,54,71,99,137,150,170 |
| evaluation | R335 actionability | actionability / 6/6 / optimization | pass | 5,15,57,76,85,87,99,100 |
| evaluation | R336 visible policies | 15 visible / 15 个 / 6 diagnostic | pass | 15,101,295,393,397,402 |
| evaluation | R337 fixed recall | 25% / 0.2000 / 16.0 | pass | 15,190,192,295,394 |
| evaluation | R339 sequence adequacy | R339 / 0.4669 / 0.9103 | pass | 13,15,200,208,211,215,295,395 |
| evaluation | R340 policy transfer | R340 / 96 / 62/96 / 72/96 | pass | 15,111,113,214,217,218,219,220 |
| evaluation | R341 mechanism attribution | R341 / 36/36 / 27/36 / 34/96 | pass | 15,100,227,228,229,230,295,395 |
| evaluation | R342 profile spec composition | R342 / 12/12 / 9/12 / 0.8267 | pass | 12,15,78,80,83,85,292,295 |
| evaluation | R344 metric consistency | R344 / 30 / 16 / groups | pass | 12,13,15,39,41,50,64,79 |
| evaluation | R345 diagnostic lens portfolio | R345 / 6 diagnostic lenses / 11/36 / 25/36 | pass | 15,100,101,235,295,395,402,555 |
| zh_main | R320 headline | 0.0937 / 9.37 / 285.0 / 157.5 | pass | 63,73,400,407,417,418,479,508 |
| zh_main | R333 headline | 0.3900 / 0.390 | pass | 68,395,447,479,508,579,693 |
| zh_main | R337 headline | 0.2000 / 16.0 / 50.0 | pass | 72,478,582,697 |
| zh_main | R339 headline | 0.4669 / 0.9103 / 0.3467 | pass | 73,479,583,698 |
| zh_main | R340 headline | R340 / 62/96 / 72/96 / 69/96 | pass | 74,79,480,481,569,584,593,699 |
| zh_main | R341 headline | R341 / 36/36 / 27/36 / 34/96 | pass | 75,79,481,484,569,585,593,700 |
| zh_main | R342 headline | R342 / 12/12 / 9/12 / 0.8267 | pass | 76,79,482,570,586 |
| zh_main | R344 headline | R344 / 30 / 16 / nDCG | pass | 55,61,62,65,66,67,68,69 |
| zh_main | R345 headline | R345 / 6 / 11/36 / 25/36 | pass | 3,16,17,18,30,50,54,55 |
| en_main | R320 headline | 0.0937 / 9.37 / 285.0 / 157.5 | pass | 45,48,349,351,369,378,561 |
| en_main | R333 headline | 0.3900 / 0.390 | pass | 70,350,369,436,564 |
| en_main | R337 headline | 0.2000 / 16.0 / 50.0 | pass | 89,90,91,549,551,760,761 |
| en_main | R339 headline | 0.4669 / 0.9103 / 0.3467 | pass | 94,95,96,565,566,567,763,764 |
| en_main | R340 headline | R340 / 62 of 96 / 72 of 96 / 69 of 96 | pass | 569,606,765,851 |
| en_main | R341 headline | R341 / 36 of 36 / 27 of 36 / 34 of 96 | pass | 104,105,106,579,599,606,768,852 |
| en_main | R342 headline | R342 / 12/12 / 9/12 / 0.8267 | pass | 109,112,113,585,586,589,591,606 |
| en_main | R344 headline | R344 / 30 / 16 / nDCG | pass | 69,76,90,93,95,101,115,116 |
| en_main | R345 headline | R345 / 6 / 11/36 / 25/36 | pass | 42,47,51,52,56,75,76,77 |
| zh_claim_setup | two abstractions | 两个核心抽象 / operation stack | pass | 7,23,25,75,78,79,80,82 |
| zh_claim_setup | R337 result | R337 / 0.2000 / 16.0 | pass | 35,36,42,113,114,115 |
| zh_claim_setup | R339 result | R339 / 0.4669 / 0.9103 | pass | 36,37,42,114,115,116,253 |
| zh_claim_setup | R340 result | R340 / 62/96 / 72/96 / 69/96 | pass | 37,38,42,114,116,117 |
| zh_claim_setup | R341 result | R341 / 36/36 / 27/36 / 34/96 | pass | 38,41,42,114,117,120 |
| zh_claim_setup | R342 result | R342 / 12/12 / 9/12 / 0.8267 | pass | 39,42,114,118 |
| zh_claim_setup | R344 result | R344 / 30 / 16 / nDCG | pass | 22,23,24,26,28,31,32,34 |
| zh_claim_setup | R345 result | R345 / 6 / 11/36 / 25/36 | pass | 3,22,23,24,25,26,27,28 |
| evaluation | R320:datasets | 4 | pass | 12,13,14,15,41,45,47,53 |
| evaluation | R320:tasks | 6 | pass | 3,4,12,13,15,32,41,42 |
| evaluation | R320:operations | 34,539 | pass | 15,125,147,263,295,360,367,369 |
| evaluation | R320:positives | 3,699 | pass | 15,147,370,373,377,380,391,464 |
| evaluation | R320:policies | 144 | pass | 15,146,375,380,390,396,470,475 |
| evaluation | R320:operation_stack_top5_work_median | 0.0937 | pass | 204,380,396,460,461,462,463,464 |
| evaluation | R320:flat_top5_work_median | 1.0 | pass | 15,193,205,295,359,362,376,380 |
| evaluation | R320:operation_stack_groups_median | 157.5 | pass | 15,151,295,380,475 |
| evaluation | R320:fixed_session_groups_median | 285.0 | pass | 15,151,295,380,475 |
| evaluation | R320:top5_recall_wins_vs_fixed | 5/6 | pass | 15,53,54,71,99,137,150,170 |
| evaluation | R320:ap_wins_vs_width | 6/6 | pass | 15,85,99,100,101,137,153,175 |
| evaluation | R333:operation_stack:query_aware_budget30_median_recall | 0.3900 | pass | 207,295,390 |
| evaluation | R333:flat:width_budget30_median_recall | 0.0000 | pass | 295,390 |
| evaluation | R333:fixed_session:query_aware_budget30_median_recall | 0.3559 | pass | 295,390 |
| evaluation | R333:dataset_native:query_aware_budget30_median_recall | 0.3377 | pass | 295,390 |
| evaluation | R333:raw_action_stack:query_aware_budget30_median_recall | 0.3325 | pass | 295,390 |
| evaluation | R337:target25_tasks_reached | 6/6 | pass | 15,85,99,100,101,137,153,175 |
| evaluation | R337:target25_median_work | 0.2000 | pass | 15,192,295,394 |
| evaluation | R337:target25_median_groups | 16.0 | pass | 15,192,295,394 |
| evaluation | R337:target10_tasks_reached | 6/6 | pass | 15,85,99,100,101,137,153,175 |
| evaluation | R337:target10_median_groups | 12.5 | pass | 196,394 |
| evaluation | R337:target50_tasks_reached | 5/6 | pass | 15,53,54,71,99,137,150,170 |
| evaluation | R337:flat_target25_median_work | 1.0000 | pass | 15,193,205,295,394 |
| evaluation | R337:fixed_target25_median_groups | 50.0 | pass | 15,194,295,394 |
| evaluation | R337:fixed_target10_median_groups | 37.5 | pass | 196,394 |
| evaluation | R337:default_vs_flat_target25_work_wins | 6/6 | pass | 15,85,99,100,101,137,153,175 |
| evaluation | R337:default_vs_fixed_target25_group_wins | 5/6 | pass | 15,53,54,71,99,137,150,170 |
| evaluation | R337:default_vs_fixed_target10_group_wins | 5/6 | pass | 15,53,54,71,99,137,150,170 |
| evaluation | R337:target25_csv_median_work | 0.2000 | pass | 15,192,295,394 |
| evaluation | R337:target25_csv_group_wins_vs_fixed | 5/6 | pass | 15,53,54,71,99,137,150,170 |
| evaluation | R339:overall | pass | pass | 14,51,136,239,371,372,375,378 |
| evaluation | R339:datasets | 4 | pass | 12,13,14,15,41,45,47,53 |
| evaluation | R339:tasks | 6 | pass | 3,4,12,13,15,32,41,42 |
| evaluation | R339:policies_scored | 144 | pass | 15,146,375,380,390,396,470,475 |
| evaluation | R339:hidden_labels_used_only_for_scoring | hidden labels only for scoring | pass | 396 |
| evaluation | R339:top5_median_operation_work | 0.0937 | pass | 204,380,396,460,461,462,463,464 |
| evaluation | R339:top5_median_positive_session_recall | 0.2629 | pass | 205,396 |
| evaluation | R339:top5_fixed_positive_session_recall | 0.0160 | pass | 206,396 |
| evaluation | R339:top5_flat_operation_work | 1.0000 | pass | 15,193,205,295,394 |
| evaluation | R339:budget30_median_positive_operation_recall | 0.3900 | pass | 207,295,390 |
| evaluation | R339:budget30_median_positive_session_recall | 0.4669 | pass | 15,208,295,396 |
| evaluation | R339:budget30_median_session_work | 0.3467 | pass | 15,209,295,396 |
| evaluation | R339:budget30_fixed_positive_session_recall | 0.3230 | pass | 15,209,295,396 |
| evaluation | R339:budget30_raw_action_positive_session_recall | 0.5147 | pass | 15,211,295,396 |
| evaluation | R339:budget30_raw_action_session_work | 0.9103 | pass | 15,211,295,396 |
| evaluation | R339:top5_operation_work_lt_flat_tasks | 6/6 | pass | 15,85,99,100,101,137,153,175 |
| evaluation | R339:budget30_session_recall_gt_fixed_tasks | 6/6 | pass | 15,85,99,100,101,137,153,175 |
| evaluation | R339:budget30_session_work_lt_raw_action_tasks | 5/6 | pass | 15,53,54,71,99,137,150,170 |
| evaluation | R339:csv_default_median_top5_operation_work | 0.0937 | pass | 204,380,396,460,461,462,463,464 |
| evaluation | R339:csv_default_median_top5_positive_session_recall | 0.2629 | pass | 205,396 |
| evaluation | R339:csv_default_median_budget30_positive_operation_recall | 0.3900 | pass | 207,295,390 |
| evaluation | R339:csv_default_median_budget30_positive_session_recall | 0.4669 | pass | 15,208,295,396 |
| evaluation | R339:csv_default_median_budget30_session_work | 0.3467 | pass | 15,209,295,396 |
| evaluation | R339:csv_budget30_session_recall_wins_vs_fixed | 6/6 | pass | 15,85,99,100,101,137,153,175 |
| evaluation | R339:csv_budget30_session_work_wins_vs_raw_action | 5/6 | pass | 15,53,54,71,99,137,150,170 |
| evaluation | R340:overall | pass | pass | 14,51,136,239,371,372,375,378 |
| evaluation | R340:tasks | 6 | pass | 3,4,12,13,15,32,41,42 |
| evaluation | R340:visible_policies | 15 | pass | 12,13,15,151,181,295,348,352 |
| evaluation | R340:objectives | 8 | pass | 12,13,14,15,32,33,73,85 |
| evaluation | R340:total_decisions | 96 | pass | 15,111,113,217,218,219,220,221 |
| evaluation | R340:exact_best_decisions | 31 | pass | 15,128,130,134,136,139,161,218 |
| evaluation | R340:within_tolerance_decisions | 62 | pass | 13,15,205,218,295,373,396,397 |
| evaluation | R340:selected_beats_width | 72 | pass | 12,15,219,295,321,332,348,360 |
| evaluation | R340:selected_beats_fixed | 69 | pass | 15,147,208,219,295,323,338,350 |
| evaluation | R340:selected_beats_flat | 41 | pass | 13,15,100,220,227,295,324,338 |
| evaluation | R340:operation_stack_selected | 16 | pass | 13,15,101,192,206,221,239,295 |
| evaluation | R340:leave_task_decisions | 48 | pass | 333,334,359,430,445,447 |
| evaluation | R340:leave_task_within_tolerance | 32 | pass | 12,14,15,36,40,43,44,47 |
| evaluation | R340:leave_dataset_decisions | 48 | pass | 333,334,359,430,445,447 |
| evaluation | R340:leave_dataset_within_tolerance | 30 | pass | 12,15,39,50,79,91,99,101 |
| evaluation | R340:decision_rows | 96 | pass | 15,111,113,217,218,219,220,221 |
| evaluation | R340:objective_rows | 16 | pass | 13,15,101,192,206,221,239,295 |
| evaluation | R340:selected_policy_visible_rows | 96/96 | pass | 225,226 |
| evaluation | R340:best_policy_visible_rows | 96/96 | pass | 225,226 |
| evaluation | R340:selected_policy_no_oracle_or_label_drilldown | 96/96 | pass | 225,226 |
| evaluation | R340:best_policy_no_oracle_or_label_drilldown | 96/96 | pass | 225,226 |
| evaluation | R340:leave_task_excludes_target_task | 96/96 | pass | 225,226 |
| evaluation | R340:leave_dataset_excludes_target_dataset | 96/96 | pass | 225,226 |
| evaluation | R341:overall | R341 | pass | 15,100,227,295,395,398,402,555 |
| evaluation | R341:tasks | 6 tasks | pass | 15,100,295,398,402 |
| evaluation | R341:objective_rows | 36 objective rows | pass | 15,100,295,398,402 |
| evaluation | R341:objective_best_policy_visible_rows | 36/36 best policies visible | pass | 398 |
| evaluation | R341:objective_best_policy_non_oracle_rows | 36/36 best policies non-oracle | pass | 398 |
| evaluation | R341:actionable_objective_rows | 36/36 objective rows have optimization actions | pass | 15,295,398 |
| evaluation | R341:nondefault_best_objective_rows | 27/36 best visible policies are non-default | pass | 15,295,398 |
| evaluation | R341:transfer_decisions | 96 transfer decisions | pass | 398 |
| evaluation | R341:transfer_misses | 34/96 transfer decisions | pass | 398 |
| evaluation | R341:transfer_misses_with_view_change | 32/34 misses change view | pass | 398 |
| evaluation | R341:transfer_misses_with_ranker_change | 26/34 change ranker | pass | 398 |
| evaluation | R341:high_regret_transfer_misses | 29/34 high-regret misses | pass | 295,398 |
| evaluation | R341:stack_depth_tradeoff_tasks | stack-depth signals on 6/6 | pass | 398 |
| evaluation | R341:transfer_policy_signal_tasks | transfer-policy signals on 6/6 | pass | 398 |
| evaluation | R341:critical_rank_feature_tasks | critical features on 4/6 | pass | 398 |
| evaluation | R341:misleading_feature_tasks | misleading features on 2/6 | pass | 15,398 |
| evaluation | R341:tasks_with_three_or_more_mechanism_labels | three or more mechanism labels on 6/6 | pass | 398 |
| evaluation | R342:overall | R342 | pass | 12,15,78,292,295,297,395,399 |
| evaluation | R342:tasks | 6 tasks | pass | 15,295,399,400,483 |
| evaluation | R342:profile_spec_variants | 12 profile-spec variants | pass | 399,483 |
| evaluation | R342:composition_variants | 12/12 compose | pass | 15,399 |
| evaluation | R342:prompt_session_free_variants | 12/12 prompt/session-free | pass | 399 |
| evaluation | R342:rule_score_rank_policy_variants | rank_mode=rule-score | pass | 15,399,483 |
| evaluation | R342:ap_improves_vs_width_variants | 9/12 variants | pass | 15,399,483 |
| evaluation | R342:top5_lift_improves_vs_width_variants | 8/12 | pass | 15 |
| evaluation | R342:first_positive_work_improves_vs_width_variants | 10/12 | pass | 15,399,483 |
| evaluation | R342:tasks_with_ap_improvement_any_depth | 5/6 | pass | 15,295 |
| evaluation | R342:tasks_with_first_positive_improvement_any_depth | 6/6 | pass | 15,295,399,483 |
| evaluation | R342:tasks_where_coarse_reduces_groups | 6/6 tasks | pass | 15,295,399,483 |
| evaluation | R342:median_coarse_group_reduction | 0.8267 | pass | 15,399,483 |
| evaluation | R342:tasks_where_depth_choice_changes_objective | 3/6 tasks | pass | 399 |
| evaluation | R342:best_ap_semantic_depth_tasks | semantic 4 / coarse 2 | pass | 15,399,483 |
| evaluation | R342:best_ap_coarse_depth_tasks | semantic 4 / coarse 2 | pass | 15,399,483 |
| evaluation | R342:committed_variant_csv_matches_sources | 12/12 | pass | 12,15,292,399,400,483 |
| evaluation | R342:committed_task_csv_matches_sources | 6/6 | pass | 15,295,399,483 |
| evaluation | R344:overall | R344 | pass | 15,88,99,100,295,395,401,402 |
| evaluation | R344:tasks | 6 tasks | pass | 15,100,295,401,402 |
| evaluation | R344:metric_comparisons | 50 baseline-metric comparisons | pass | 15,295,401,476 |
| evaluation | R344:task_metric_delta_rows | 300 task-metric deltas | pass | 401 |
| evaluation | R344:support_verdicts | 30 support verdicts | pass | 15,401,476 |
| evaluation | R344:counterpoint_verdicts | 16 counterpoints | pass | 15,401,476 |
| evaluation | R344:mixed_or_weak_verdicts | 4 mixed/weak | pass | 15,401,476 |
| evaluation | R344:required_metric_count | groups | pass | 15,99,100,295,476 |
| evaluation | R344:required_groups_metric_present | groups | pass | 15,99,100,295,476 |
| evaluation | R344:metric_summary_rows | 50 | pass | 15,295,401,476 |
| evaluation | R344:task_delta_rows | 300 | pass | 15,295,401 |
| evaluation | R344:summary_support_verdicts | 30 support verdicts | pass | 15,401,476 |
| evaluation | R344:summary_counterpoint_verdicts | 16 counterpoints | pass | 15,401,476 |
| evaluation | R344:summary_mixed_or_weak_verdicts | 4 mixed/weak | pass | 15,401,476 |
| evaluation | R344:required_metric_groups_in_summary | groups | pass | 15,99,100,295,476 |
| evaluation | R344:flat_ap_wins | flat AP 6/6 | pass | 99 |
| evaluation | R344:flat_budget30_recall_wins | budget30 recall 6/6 | pass | 99 |
| evaluation | R344:flat_work_to_first_positive_wins | work-to-first-positive 6/6 | pass | 99 |
| evaluation | R344:fixed_session_top5_f1_wins | top-5 F1 5/6 | pass | 99 |
| evaluation | R344:fixed_session_group_wins | groups 4/6 | pass | 99 |
| evaluation | R344:width_ap_wins | width AP 6/6 | pass | 99 |
| evaluation | R344:width_budget30_recall_wins | budget30 recall 5/6 | pass | 99 |
| evaluation | R344:flat_ndcg_losses | nDCG | pass | 15,295,401,476,554 |
| evaluation | R344:flat_top5_recall_losses | top-k recall | pass | 15,295,401,476 |
| evaluation | R345:overall | R345 | pass | 15,100,101,235,295,395,402,555 |
| evaluation | R345:tasks | 6 tasks | pass | 15,100,101,295,402 |
| evaluation | R345:datasets | 4 datasets | pass | 15,101,402 |
| evaluation | R345:lens_count | 6 diagnostic lenses | pass | 15,101,295,402 |
| evaluation | R345:objective_rows | 36 objective rows | pass | 15,100,101,295,402 |
| evaluation | R345:task_cards | 6/6 actionable task cards | pass | 101 |
| evaluation | R345:actionable_task_cards | 6/6 actionable task cards | pass | 101 |
| evaluation | R345:distinct_optimization_actions | 5 distinct optimization actions | pass | 101 |
| evaluation | R345:default_operation_stack_best_objectives | 9/36 default operation-stack | pass | 101 |
| evaluation | R345:operation_stack_family_best_objectives | 11/36 operation-stack family | pass | 101 |
| evaluation | R345:non_operation_stack_best_objectives | 25/36 counterpoints | pass | 101 |
| evaluation | R345:tasks_with_three_or_more_best_views | 6/6 tasks need at least three best views | pass | 15,100,101,295,402 |
| evaluation | R345:min_distinct_best_views_per_task | 3 best views | pass | 101 |
| evaluation | R345:max_distinct_best_views_per_task | 4 best views | pass | 101 |
| evaluation | R345:counterpoint_rows | 46 counterpoint rows | pass | 101,402 |
| evaluation | R345:r344_support_verdicts | 30 support | pass | 15,101 |
| evaluation | R345:r344_counterpoint_verdicts | 16 counterpoints | pass | 15,101 |
| evaluation | R345:r344_mixed_or_weak_verdicts | 4 mixed/weak | pass | 15,101 |
| evaluation | R345:lens_summary_rows | 6 diagnostic lenses | pass | 15,101,295,402 |
| evaluation | R345:task_lens_card_rows | 6 tasks | pass | 15,100,101,295,402 |
| evaluation | R345:counterpoint_ledger_rows | 46 counterpoint rows | pass | 101,402 |

## Guardrails

| Doc | Guardrail | Status | Occurrences | Occurrence lines | Unguarded overclaim lines |
|---|---|---|---:|---|---|
| evaluation | human_utility | pass | 12 | 15,295,367,371,452,455,457,458,462,466,467,469 | none |
| evaluation | automatic_boundary | pass | 6 | 242,295,451,452,474,483 | none |
| evaluation | ecosystem_compatibility | pass | 8 | 12,15,30,295,366,451,469,565 | none |
| evaluation | universal_selector | pass | 12 | 15,100,189,295,397,468,469,471,475,483,540,555 | none |
| zh_claim_setup | human_utility | pass | 12 | 26,28,36,42,78,79,80,87,88,91,92,94 | none |
| zh_claim_setup | automatic_boundary | pass | 5 | 23,25,26,42,243 | none |
| zh_claim_setup | ecosystem_compatibility | pass | 8 | 22,72,90,147,194,231,232,233 | none |
| zh_claim_setup | universal_selector | pass | 12 | 26,34,36,37,38,41,42,107,108,109,110,111 | none |
| zh_main | human_utility | pass | 9 | 79,205,385,428,594,661,671,703,704 | none |
| zh_main | automatic_boundary | pass | 1 | 79 | none |
| zh_main | ecosystem_compatibility | pass | 12 | 51,163,617,625,626,629,665,688,707,718,728,729 | none |
| zh_main | universal_selector | pass | 11 | 78,79,473,479,484,592,654,691,696,699,702 | none |
| en_main | human_utility | pass | 4 | 159,173,610,669 | none |
| en_main | automatic_boundary | pass | 2 | 611,783 | none |
| en_main | ecosystem_compatibility | pass | 12 | 702,704,712,714,715,716,722,723,784,871,872,874 | none |
| en_main | universal_selector | pass | 8 | 122,412,415,568,577,611,751,758 | none |
