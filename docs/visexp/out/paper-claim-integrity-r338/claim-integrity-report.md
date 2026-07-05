# Paper Claim Integrity Audit R338

R338 mechanically audits the current profiling-paper claim against R320-R344 result artifacts and the Chinese/English paper text. It does not fetch, sync, create, or relabel datasets.

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

## Text Coverage

| Doc | Key | Tokens | Status | Lines |
|---|---|---|---|---|
| evaluation | R320 headline operations | 34,539 / 34539 | pass | 15,123,145,261,293,358,365,367 |
| evaluation | R320 top5 work | 0.0937 / 9.37% | pass | 15,146,202,293,362,363,366,378 |
| evaluation | R333 budget30 recall | 0.3900 / 0.39 | pass | 205,293,388,456 |
| evaluation | R334 fragmentation | 5/6 / -54.0 / fewer groups | pass | 15,53,54,71,99,135,148,168 |
| evaluation | R335 actionability | actionability / 6/6 / optimization | pass | 5,15,57,76,85,87,99,135 |
| evaluation | R336 visible policies | 15 visible / 15 个 / 6 diagnostic | pass | 293,391,395 |
| evaluation | R337 fixed recall | 25% / 0.2000 / 16.0 | pass | 15,188,190,293,392 |
| evaluation | R339 sequence adequacy | R339 / 0.4669 / 0.9103 | pass | 13,15,198,206,209,213,293,393 |
| evaluation | R340 policy transfer | R340 / 96 / 62/96 / 72/96 | pass | 15,109,111,212,215,216,217,218 |
| evaluation | R341 mechanism attribution | R341 / 36/36 / 27/36 / 34/96 | pass | 15,225,226,227,228,293,393,396 |
| evaluation | R342 profile spec composition | R342 / 12/12 / 9/12 / 0.8267 | pass | 12,15,78,80,83,85,290,293 |
| evaluation | R344 metric consistency | R344 / 30 / 16 / groups | pass | 12,13,15,39,41,50,64,79 |
| zh_main | R320 headline | 0.0937 / 9.37 / 285.0 / 157.5 | pass | 63,73,399,406,416,417,478,506 |
| zh_main | R333 headline | 0.3900 / 0.390 | pass | 68,394,446,478,506,577,690 |
| zh_main | R337 headline | 0.2000 / 16.0 / 50.0 | pass | 72,477,580,694 |
| zh_main | R339 headline | 0.4669 / 0.9103 / 0.3467 | pass | 73,478,581,695 |
| zh_main | R340 headline | R340 / 62/96 / 72/96 / 69/96 | pass | 74,78,479,480,567,582,590,696 |
| zh_main | R341 headline | R341 / 36/36 / 27/36 / 34/96 | pass | 75,78,480,567,583,590,697 |
| zh_main | R342 headline | R342 / 12/12 / 9/12 / 0.8267 | pass | 76,78,481,568,584 |
| zh_main | R344 headline | R344 / 30 / 16 / nDCG | pass | 55,61,62,65,66,67,68,69 |
| en_main | R320 headline | 0.0937 / 9.37 / 285.0 / 157.5 | pass | 45,48,344,346,364,373,556 |
| en_main | R333 headline | 0.3900 / 0.390 | pass | 70,345,364,431,559 |
| en_main | R337 headline | 0.2000 / 16.0 / 50.0 | pass | 89,90,91,544,546,749,750 |
| en_main | R339 headline | 0.4669 / 0.9103 / 0.3467 | pass | 94,95,96,560,561,562,752,753 |
| en_main | R340 headline | R340 / 62 of 96 / 72 of 96 / 69 of 96 | pass | 564,594,754,838 |
| en_main | R341 headline | R341 / 36 of 36 / 27 of 36 / 34 of 96 | pass | 104,105,106,574,594,757,839 |
| en_main | R342 headline | R342 / 12/12 / 9/12 / 0.8267 | pass | 109,112,113,580,581,584,586,594 |
| en_main | R344 headline | R344 / 30 / 16 / nDCG | pass | 69,76,90,93,95,101,115,116 |
| zh_claim_setup | two abstractions | 两个核心抽象 / operation stack | pass | 7,23,25,74,77,78,79,81 |
| zh_claim_setup | R337 result | R337 / 0.2000 / 16.0 | pass | 35,36,41,112,113,114 |
| zh_claim_setup | R339 result | R339 / 0.4669 / 0.9103 | pass | 36,37,41,113,114,115,251 |
| zh_claim_setup | R340 result | R340 / 62/96 / 72/96 / 69/96 | pass | 37,38,41,113,115,116 |
| zh_claim_setup | R341 result | R341 / 36/36 / 27/36 / 34/96 | pass | 38,41,113,116 |
| zh_claim_setup | R342 result | R342 / 12/12 / 9/12 / 0.8267 | pass | 39,41,113,117 |
| zh_claim_setup | R344 result | R344 / 30 / 16 / nDCG | pass | 22,23,24,26,28,31,32,34 |
| evaluation | R320:datasets | 4 | pass | 12,13,14,15,41,45,47,53 |
| evaluation | R320:tasks | 6 | pass | 3,4,12,13,15,32,41,42 |
| evaluation | R320:operations | 34,539 | pass | 15,123,145,261,293,358,365,367 |
| evaluation | R320:positives | 3,699 | pass | 15,145,368,371,375,378,389,461 |
| evaluation | R320:policies | 144 | pass | 15,144,373,378,388,394,467,472 |
| evaluation | R320:operation_stack_top5_work_median | 0.0937 | pass | 202,378,394,457,458,459,460,461 |
| evaluation | R320:flat_top5_work_median | 1.0 | pass | 15,191,203,293,357,360,374,378 |
| evaluation | R320:operation_stack_groups_median | 157.5 | pass | 15,149,293,378,472 |
| evaluation | R320:fixed_session_groups_median | 285.0 | pass | 15,149,293,378,472 |
| evaluation | R320:top5_recall_wins_vs_fixed | 5/6 | pass | 15,53,54,71,99,135,148,168 |
| evaluation | R320:ap_wins_vs_width | 6/6 | pass | 15,85,99,135,151,173,175,181 |
| evaluation | R333:operation_stack:query_aware_budget30_median_recall | 0.3900 | pass | 205,293,388 |
| evaluation | R333:flat:width_budget30_median_recall | 0.0000 | pass | 293,388 |
| evaluation | R333:fixed_session:query_aware_budget30_median_recall | 0.3559 | pass | 293,388 |
| evaluation | R333:dataset_native:query_aware_budget30_median_recall | 0.3377 | pass | 293,388 |
| evaluation | R333:raw_action_stack:query_aware_budget30_median_recall | 0.3325 | pass | 293,388 |
| evaluation | R337:target25_tasks_reached | 6/6 | pass | 15,85,99,135,151,173,175,181 |
| evaluation | R337:target25_median_work | 0.2000 | pass | 15,190,293,392 |
| evaluation | R337:target25_median_groups | 16.0 | pass | 15,190,293,392 |
| evaluation | R337:target10_tasks_reached | 6/6 | pass | 15,85,99,135,151,173,175,181 |
| evaluation | R337:target10_median_groups | 12.5 | pass | 194,392 |
| evaluation | R337:target50_tasks_reached | 5/6 | pass | 15,53,54,71,99,135,148,168 |
| evaluation | R337:flat_target25_median_work | 1.0000 | pass | 15,191,203,293,392 |
| evaluation | R337:fixed_target25_median_groups | 50.0 | pass | 15,192,293,392 |
| evaluation | R337:fixed_target10_median_groups | 37.5 | pass | 194,392 |
| evaluation | R337:default_vs_flat_target25_work_wins | 6/6 | pass | 15,85,99,135,151,173,175,181 |
| evaluation | R337:default_vs_fixed_target25_group_wins | 5/6 | pass | 15,53,54,71,99,135,148,168 |
| evaluation | R337:default_vs_fixed_target10_group_wins | 5/6 | pass | 15,53,54,71,99,135,148,168 |
| evaluation | R337:target25_csv_median_work | 0.2000 | pass | 15,190,293,392 |
| evaluation | R337:target25_csv_group_wins_vs_fixed | 5/6 | pass | 15,53,54,71,99,135,148,168 |
| evaluation | R339:overall | pass | pass | 14,15,51,134,237,293,369,370 |
| evaluation | R339:datasets | 4 | pass | 12,13,14,15,41,45,47,53 |
| evaluation | R339:tasks | 6 | pass | 3,4,12,13,15,32,41,42 |
| evaluation | R339:policies_scored | 144 | pass | 15,144,373,378,388,394,467,472 |
| evaluation | R339:hidden_labels_used_only_for_scoring | hidden labels only for scoring | pass | 394 |
| evaluation | R339:top5_median_operation_work | 0.0937 | pass | 202,378,394,457,458,459,460,461 |
| evaluation | R339:top5_median_positive_session_recall | 0.2629 | pass | 203,394 |
| evaluation | R339:top5_fixed_positive_session_recall | 0.0160 | pass | 204,394 |
| evaluation | R339:top5_flat_operation_work | 1.0000 | pass | 15,191,203,293,392 |
| evaluation | R339:budget30_median_positive_operation_recall | 0.3900 | pass | 205,293,388 |
| evaluation | R339:budget30_median_positive_session_recall | 0.4669 | pass | 15,206,293,394 |
| evaluation | R339:budget30_median_session_work | 0.3467 | pass | 15,207,293,394 |
| evaluation | R339:budget30_fixed_positive_session_recall | 0.3230 | pass | 15,207,293,394 |
| evaluation | R339:budget30_raw_action_positive_session_recall | 0.5147 | pass | 15,209,293,394 |
| evaluation | R339:budget30_raw_action_session_work | 0.9103 | pass | 15,209,293,394 |
| evaluation | R339:top5_operation_work_lt_flat_tasks | 6/6 | pass | 15,85,99,135,151,173,175,181 |
| evaluation | R339:budget30_session_recall_gt_fixed_tasks | 6/6 | pass | 15,85,99,135,151,173,175,181 |
| evaluation | R339:budget30_session_work_lt_raw_action_tasks | 5/6 | pass | 15,53,54,71,99,135,148,168 |
| evaluation | R339:csv_default_median_top5_operation_work | 0.0937 | pass | 202,378,394,457,458,459,460,461 |
| evaluation | R339:csv_default_median_top5_positive_session_recall | 0.2629 | pass | 203,394 |
| evaluation | R339:csv_default_median_budget30_positive_operation_recall | 0.3900 | pass | 205,293,388 |
| evaluation | R339:csv_default_median_budget30_positive_session_recall | 0.4669 | pass | 15,206,293,394 |
| evaluation | R339:csv_default_median_budget30_session_work | 0.3467 | pass | 15,207,293,394 |
| evaluation | R339:csv_budget30_session_recall_wins_vs_fixed | 6/6 | pass | 15,85,99,135,151,173,175,181 |
| evaluation | R339:csv_budget30_session_work_wins_vs_raw_action | 5/6 | pass | 15,53,54,71,99,135,148,168 |
| evaluation | R340:overall | pass | pass | 14,15,51,134,237,293,369,370 |
| evaluation | R340:tasks | 6 | pass | 3,4,12,13,15,32,41,42 |
| evaluation | R340:visible_policies | 15 | pass | 12,13,15,149,179,293,346,350 |
| evaluation | R340:objectives | 8 | pass | 12,13,14,15,32,33,73,85 |
| evaluation | R340:total_decisions | 96 | pass | 15,109,111,215,216,217,218,219 |
| evaluation | R340:exact_best_decisions | 31 | pass | 15,126,128,132,134,137,159,216 |
| evaluation | R340:within_tolerance_decisions | 62 | pass | 13,15,203,216,293,371,394,395 |
| evaluation | R340:selected_beats_width | 72 | pass | 12,15,217,293,319,330,346,358 |
| evaluation | R340:selected_beats_fixed | 69 | pass | 15,145,206,217,293,321,336,348 |
| evaluation | R340:selected_beats_flat | 41 | pass | 13,15,218,225,293,322,336,349 |
| evaluation | R340:operation_stack_selected | 16 | pass | 13,15,190,204,219,237,293,310 |
| evaluation | R340:leave_task_decisions | 48 | pass | 331,332,357,427,442,444 |
| evaluation | R340:leave_task_within_tolerance | 32 | pass | 12,14,15,36,40,43,44,47 |
| evaluation | R340:leave_dataset_decisions | 48 | pass | 331,332,357,427,442,444 |
| evaluation | R340:leave_dataset_within_tolerance | 30 | pass | 12,15,39,50,79,91,99,103 |
| evaluation | R340:decision_rows | 96 | pass | 15,109,111,215,216,217,218,219 |
| evaluation | R340:objective_rows | 16 | pass | 13,15,190,204,219,237,293,310 |
| evaluation | R340:selected_policy_visible_rows | 96/96 | pass | 223,224 |
| evaluation | R340:best_policy_visible_rows | 96/96 | pass | 223,224 |
| evaluation | R340:selected_policy_no_oracle_or_label_drilldown | 96/96 | pass | 223,224 |
| evaluation | R340:best_policy_no_oracle_or_label_drilldown | 96/96 | pass | 223,224 |
| evaluation | R340:leave_task_excludes_target_task | 96/96 | pass | 223,224 |
| evaluation | R340:leave_dataset_excludes_target_dataset | 96/96 | pass | 223,224 |
| evaluation | R341:overall | R341 | pass | 15,225,293,393,396,557,560,631 |
| evaluation | R341:tasks | 6 tasks | pass | 15,293,396 |
| evaluation | R341:objective_rows | 36 objective rows | pass | 15,293,396 |
| evaluation | R341:objective_best_policy_visible_rows | 36/36 best policies visible | pass | 396 |
| evaluation | R341:objective_best_policy_non_oracle_rows | 36/36 best policies non-oracle | pass | 396 |
| evaluation | R341:actionable_objective_rows | 36/36 objective rows have optimization actions | pass | 15,293,396 |
| evaluation | R341:nondefault_best_objective_rows | 27/36 best visible policies are non-default | pass | 15,293,396 |
| evaluation | R341:transfer_decisions | 96 transfer decisions | pass | 396 |
| evaluation | R341:transfer_misses | 34/96 transfer decisions | pass | 396 |
| evaluation | R341:transfer_misses_with_view_change | 32/34 misses change view | pass | 396 |
| evaluation | R341:transfer_misses_with_ranker_change | 26/34 change ranker | pass | 396 |
| evaluation | R341:high_regret_transfer_misses | 29/34 high-regret misses | pass | 293,396 |
| evaluation | R341:stack_depth_tradeoff_tasks | stack-depth signals on 6/6 | pass | 396 |
| evaluation | R341:transfer_policy_signal_tasks | transfer-policy signals on 6/6 | pass | 396 |
| evaluation | R341:critical_rank_feature_tasks | critical features on 4/6 | pass | 396 |
| evaluation | R341:misleading_feature_tasks | misleading features on 2/6 | pass | 15,396 |
| evaluation | R341:tasks_with_three_or_more_mechanism_labels | three or more mechanism labels on 6/6 | pass | 396 |
| evaluation | R342:overall | R342 | pass | 12,15,78,290,293,295,393,397 |
| evaluation | R342:tasks | 6 tasks | pass | 15,293,397,398,480 |
| evaluation | R342:profile_spec_variants | 12 profile-spec variants | pass | 397,480 |
| evaluation | R342:composition_variants | 12/12 compose | pass | 15,397 |
| evaluation | R342:prompt_session_free_variants | 12/12 prompt/session-free | pass | 397 |
| evaluation | R342:rule_score_rank_policy_variants | rank_mode=rule-score | pass | 15,397,480 |
| evaluation | R342:ap_improves_vs_width_variants | 9/12 variants | pass | 15,397,480 |
| evaluation | R342:top5_lift_improves_vs_width_variants | 8/12 | pass | 15 |
| evaluation | R342:first_positive_work_improves_vs_width_variants | 10/12 | pass | 15,397,480 |
| evaluation | R342:tasks_with_ap_improvement_any_depth | 5/6 | pass | 15,293 |
| evaluation | R342:tasks_with_first_positive_improvement_any_depth | 6/6 | pass | 15,293,397,480 |
| evaluation | R342:tasks_where_coarse_reduces_groups | 6/6 tasks | pass | 15,293,397,480 |
| evaluation | R342:median_coarse_group_reduction | 0.8267 | pass | 15,397,480 |
| evaluation | R342:tasks_where_depth_choice_changes_objective | 3/6 tasks | pass | 397 |
| evaluation | R342:best_ap_semantic_depth_tasks | semantic 4 / coarse 2 | pass | 15,397,480 |
| evaluation | R342:best_ap_coarse_depth_tasks | semantic 4 / coarse 2 | pass | 15,397,480 |
| evaluation | R342:committed_variant_csv_matches_sources | 12/12 | pass | 12,15,290,397,398,480 |
| evaluation | R342:committed_task_csv_matches_sources | 6/6 | pass | 15,293,397,480 |
| evaluation | R344:overall | R344 | pass | 15,88,99,233,293,393,399,473 |
| evaluation | R344:tasks | 6 tasks | pass | 15,293,399 |
| evaluation | R344:metric_comparisons | 50 baseline-metric comparisons | pass | 15,293,399,473 |
| evaluation | R344:task_metric_delta_rows | 300 task-metric deltas | pass | 399 |
| evaluation | R344:support_verdicts | 30 support verdicts | pass | 15,399,473 |
| evaluation | R344:counterpoint_verdicts | 16 counterpoints | pass | 15,399,473 |
| evaluation | R344:mixed_or_weak_verdicts | 4 mixed/weak | pass | 15,399,473 |
| evaluation | R344:required_metric_count | groups | pass | 15,99,293,473 |
| evaluation | R344:required_groups_metric_present | groups | pass | 15,99,293,473 |
| evaluation | R344:metric_summary_rows | 50 | pass | 15,293,399,473 |
| evaluation | R344:task_delta_rows | 300 | pass | 15,293,399 |
| evaluation | R344:summary_support_verdicts | 30 support verdicts | pass | 15,399,473 |
| evaluation | R344:summary_counterpoint_verdicts | 16 counterpoints | pass | 15,399,473 |
| evaluation | R344:summary_mixed_or_weak_verdicts | 4 mixed/weak | pass | 15,399,473 |
| evaluation | R344:required_metric_groups_in_summary | groups | pass | 15,99,293,473 |
| evaluation | R344:flat_ap_wins | flat AP 6/6 | pass | 99 |
| evaluation | R344:flat_budget30_recall_wins | budget30 recall 6/6 | pass | 99 |
| evaluation | R344:flat_work_to_first_positive_wins | work-to-first-positive 6/6 | pass | 99 |
| evaluation | R344:fixed_session_top5_f1_wins | top-5 F1 5/6 | pass | 99 |
| evaluation | R344:fixed_session_group_wins | groups 4/6 | pass | 99 |
| evaluation | R344:width_ap_wins | width AP 6/6 | pass | 99 |
| evaluation | R344:width_budget30_recall_wins | budget30 recall 5/6 | pass | 99 |
| evaluation | R344:flat_ndcg_losses | nDCG | pass | 15,293,399,473,551 |
| evaluation | R344:flat_top5_recall_losses | top-k recall | pass | 15,293,399,473 |

## Guardrails

| Doc | Guardrail | Status | Occurrences | Occurrence lines | Unguarded overclaim lines |
|---|---|---|---:|---|---|
| evaluation | human_utility | pass | 12 | 15,293,365,369,449,452,454,455,459,463,464,466 | none |
| evaluation | automatic_boundary | pass | 6 | 240,293,448,449,471,480 | none |
| evaluation | ecosystem_compatibility | pass | 8 | 12,15,30,293,364,448,466,561 | none |
| evaluation | universal_selector | pass | 11 | 15,187,293,395,465,466,468,472,480,537,555 | none |
| zh_claim_setup | human_utility | pass | 12 | 26,28,36,41,77,78,79,86,87,90,91,93 | none |
| zh_claim_setup | automatic_boundary | pass | 5 | 23,25,26,41,241 | none |
| zh_claim_setup | ecosystem_compatibility | pass | 8 | 22,71,89,145,192,229,230,231 | none |
| zh_claim_setup | universal_selector | pass | 12 | 26,34,36,37,38,41,106,107,108,109,110,111 | none |
| zh_main | human_utility | pass | 9 | 78,204,384,427,591,658,668,699,700 | none |
| zh_main | automatic_boundary | pass | 1 | 78 | none |
| zh_main | ecosystem_compatibility | pass | 12 | 51,162,614,622,623,626,662,685,703,714,724,725 | none |
| zh_main | universal_selector | pass | 8 | 78,472,478,589,651,688,693,696 | none |
| en_main | human_utility | pass | 4 | 154,168,599,658 | none |
| en_main | automatic_boundary | pass | 2 | 599,770 | none |
| en_main | ecosystem_compatibility | pass | 12 | 691,693,701,703,704,705,711,712,771,856,857,859 | none |
| en_main | universal_selector | pass | 7 | 407,410,563,572,600,740,747 | none |
