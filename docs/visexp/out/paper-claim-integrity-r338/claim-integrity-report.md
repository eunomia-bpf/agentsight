# Paper Claim Integrity Audit R338

R338 mechanically audits the current profiling-paper claim against R320-R342 result artifacts and the Chinese/English paper text. It does not fetch, sync, create, or relabel datasets.

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
| R342 | overall | pass | pass | pass | R342 CSV-derived invariants |
| R342 | tasks | 6 | 6 | pass | R342 profile-spec-composition-tasks.csv |
| R342 | profile_spec_variants | 12 | 12 | pass | R342 profile-spec-composition-variants.csv |
| R342 | composition_variants | 12 | 12 | pass | R342 profile-spec-composition-variants.csv |
| R342 | prompt_session_free_variants | 12 | 12 | pass | R342 profile-spec-composition-variants.csv |
| R342 | rule_score_rank_policy_variants | 12 | 12 | pass | R342 profile-spec-composition-variants.csv |
| R342 | ap_improves_vs_width_variants | 9 | 9 | pass | R342 profile-spec-composition-variants.csv |
| R342 | top5_lift_improves_vs_width_variants | 8 | 8 | pass | R342 profile-spec-composition-variants.csv |
| R342 | first_positive_work_improves_vs_width_variants | 10 | 10 | pass | R342 profile-spec-composition-variants.csv |
| R342 | tasks_with_ap_improvement_any_depth | 5 | 5 | pass | R342 profile-spec-composition-tasks.csv |
| R342 | tasks_with_first_positive_improvement_any_depth | 6 | 6 | pass | R342 profile-spec-composition-tasks.csv |
| R342 | tasks_where_coarse_reduces_groups | 6 | 6 | pass | R342 profile-spec-composition-tasks.csv |
| R342 | median_coarse_group_reduction | 0.8267 | 0.8267 | pass | R342 profile-spec-composition-tasks.csv |
| R342 | tasks_where_depth_choice_changes_objective | 3 | 3 | pass | R342 profile-spec-composition-tasks.csv |
| R342 | best_ap_semantic_depth_tasks | 4 | 4 | pass | R342 profile-spec-composition-tasks.csv |
| R342 | best_ap_coarse_depth_tasks | 2 | 2 | pass | R342 profile-spec-composition-tasks.csv |

## Text Coverage

| Doc | Key | Tokens | Status | Lines |
|---|---|---|---|---|
| evaluation | R320 headline operations | 34,539 / 34539 | pass | 15,111,133,249,281,346,353,355 |
| evaluation | R320 top5 work | 0.0937 / 9.37% | pass | 15,134,190,281,350,351,354,366 |
| evaluation | R333 budget30 recall | 0.3900 / 0.39 | pass | 193,281,376,442 |
| evaluation | R334 fragmentation | 5/6 / -54.0 / fewer groups | pass | 15,53,54,71,123,136,156,157 |
| evaluation | R335 actionability | actionability / 6/6 / optimization | pass | 5,15,57,76,85,87,123,139 |
| evaluation | R336 visible policies | 15 visible / 15 个 / 6 diagnostic | pass | 281,379,383 |
| evaluation | R337 fixed recall | 25% / 0.2000 / 16.0 | pass | 15,176,178,281,380 |
| evaluation | R339 sequence adequacy | R339 / 0.4669 / 0.9103 | pass | 13,15,186,194,197,201,281,381 |
| evaluation | R340 policy transfer | R340 / 96 / 62/96 / 72/96 | pass | 15,97,99,200,203,204,205,206 |
| evaluation | R341 mechanism attribution | R341 / 36/36 / 27/36 / 34/96 | pass | 15,213,214,215,216,281,381,384 |
| evaluation | R342 profile spec composition | R342 / 12/12 / 9/12 / 0.8267 | pass | 12,15,78,80,83,85,221,278 |
| zh_main | R320 headline | 0.0937 / 9.37 / 285.0 / 157.5 | pass | 63,73,397,404,414,415,476,502 |
| zh_main | R333 headline | 0.3900 / 0.390 | pass | 68,392,444,476,502,557,658 |
| zh_main | R337 headline | 0.2000 / 16.0 / 50.0 | pass | 72,475,557,662 |
| zh_main | R339 headline | 0.4669 / 0.9103 / 0.3467 | pass | 73,476,557,663 |
| zh_main | R340 headline | R340 / 62/96 / 72/96 / 69/96 | pass | 74,76,477,478,557,558,664 |
| zh_main | R341 headline | R341 / 36/36 / 27/36 / 34/96 | pass | 75,76,478,479,557,558,633,665 |
| en_main | R320 headline | 0.0937 / 9.37 / 285.0 / 157.5 | pass | 45,48,334,336,354,363,546 |
| en_main | R333 headline | 0.3900 / 0.390 | pass | 70,335,354,421,549 |
| en_main | R337 headline | 0.2000 / 16.0 / 50.0 | pass | 89,90,91,534,536,726,727 |
| en_main | R339 headline | 0.4669 / 0.9103 / 0.3467 | pass | 94,95,96,550,551,552,729,730 |
| en_main | R340 headline | R340 / 62 of 96 / 72 of 96 / 69 of 96 | pass | 554,571,731,813 |
| en_main | R341 headline | R341 / 36 of 36 / 27 of 36 / 34 of 96 | pass | 104,105,106,108,564,571,734,738 |
| zh_claim_setup | two abstractions | 两个核心抽象 / operation stack | pass | 7,23,25,72,75,76,77,79 |
| zh_claim_setup | R337 result | R337 / 0.2000 / 16.0 | pass | 35,36,39,110,111,112 |
| zh_claim_setup | R339 result | R339 / 0.4669 / 0.9103 | pass | 36,37,39,111,112,113,247 |
| zh_claim_setup | R340 result | R340 / 62/96 / 72/96 / 69/96 | pass | 37,38,39,111,113,114 |
| zh_claim_setup | R341 result | R341 / 36/36 / 27/36 / 34/96 | pass | 38,39,111,114 |
| evaluation | R320:datasets | 4 | pass | 12,13,14,15,41,45,47,53 |
| evaluation | R320:tasks | 6 | pass | 3,4,12,13,15,32,41,42 |
| evaluation | R320:operations | 34,539 | pass | 15,111,133,249,281,346,353,355 |
| evaluation | R320:positives | 3,699 | pass | 15,133,356,359,363,366,377,447 |
| evaluation | R320:policies | 144 | pass | 15,132,361,366,376,382,453,458 |
| evaluation | R320:operation_stack_top5_work_median | 0.0937 | pass | 190,366,382,443,444,445,446,447 |
| evaluation | R320:flat_top5_work_median | 1.0 | pass | 15,179,191,281,345,348,362,366 |
| evaluation | R320:operation_stack_groups_median | 157.5 | pass | 15,137,281,366,458 |
| evaluation | R320:fixed_session_groups_median | 285.0 | pass | 15,137,281,366,458 |
| evaluation | R320:top5_recall_wins_vs_fixed | 5/6 | pass | 15,53,54,71,123,136,156,157 |
| evaluation | R320:ap_wins_vs_width | 6/6 | pass | 15,85,123,139,161,163,169,170 |
| evaluation | R333:operation_stack:query_aware_budget30_median_recall | 0.3900 | pass | 193,281,376 |
| evaluation | R333:flat:width_budget30_median_recall | 0.0000 | pass | 281,376 |
| evaluation | R333:fixed_session:query_aware_budget30_median_recall | 0.3559 | pass | 281,376 |
| evaluation | R333:dataset_native:query_aware_budget30_median_recall | 0.3377 | pass | 281,376 |
| evaluation | R333:raw_action_stack:query_aware_budget30_median_recall | 0.3325 | pass | 281,376 |
| evaluation | R337:target25_tasks_reached | 6/6 | pass | 15,85,123,139,161,163,169,170 |
| evaluation | R337:target25_median_work | 0.2000 | pass | 15,178,281,380 |
| evaluation | R337:target25_median_groups | 16.0 | pass | 15,178,281,380 |
| evaluation | R337:target10_tasks_reached | 6/6 | pass | 15,85,123,139,161,163,169,170 |
| evaluation | R337:target10_median_groups | 12.5 | pass | 182,380 |
| evaluation | R337:target50_tasks_reached | 5/6 | pass | 15,53,54,71,123,136,156,157 |
| evaluation | R337:flat_target25_median_work | 1.0000 | pass | 15,179,191,281,380 |
| evaluation | R337:fixed_target25_median_groups | 50.0 | pass | 15,180,281,380 |
| evaluation | R337:fixed_target10_median_groups | 37.5 | pass | 182,380 |
| evaluation | R337:default_vs_flat_target25_work_wins | 6/6 | pass | 15,85,123,139,161,163,169,170 |
| evaluation | R337:default_vs_fixed_target25_group_wins | 5/6 | pass | 15,53,54,71,123,136,156,157 |
| evaluation | R337:default_vs_fixed_target10_group_wins | 5/6 | pass | 15,53,54,71,123,136,156,157 |
| evaluation | R337:target25_csv_median_work | 0.2000 | pass | 15,178,281,380 |
| evaluation | R337:target25_csv_group_wins_vs_fixed | 5/6 | pass | 15,53,54,71,123,136,156,157 |
| evaluation | R339:overall | pass | pass | 14,51,122,225,281,357,358,361 |
| evaluation | R339:datasets | 4 | pass | 12,13,14,15,41,45,47,53 |
| evaluation | R339:tasks | 6 | pass | 3,4,12,13,15,32,41,42 |
| evaluation | R339:policies_scored | 144 | pass | 15,132,361,366,376,382,453,458 |
| evaluation | R339:hidden_labels_used_only_for_scoring | hidden labels only for scoring | pass | 382 |
| evaluation | R339:top5_median_operation_work | 0.0937 | pass | 190,366,382,443,444,445,446,447 |
| evaluation | R339:top5_median_positive_session_recall | 0.2629 | pass | 191,382 |
| evaluation | R339:top5_fixed_positive_session_recall | 0.0160 | pass | 192,382 |
| evaluation | R339:top5_flat_operation_work | 1.0000 | pass | 15,179,191,281,380 |
| evaluation | R339:budget30_median_positive_operation_recall | 0.3900 | pass | 193,281,376 |
| evaluation | R339:budget30_median_positive_session_recall | 0.4669 | pass | 15,194,281,382 |
| evaluation | R339:budget30_median_session_work | 0.3467 | pass | 15,195,281,382 |
| evaluation | R339:budget30_fixed_positive_session_recall | 0.3230 | pass | 15,195,281,382 |
| evaluation | R339:budget30_raw_action_positive_session_recall | 0.5147 | pass | 15,197,281,382 |
| evaluation | R339:budget30_raw_action_session_work | 0.9103 | pass | 15,197,281,382 |
| evaluation | R339:top5_operation_work_lt_flat_tasks | 6/6 | pass | 15,85,123,139,161,163,169,170 |
| evaluation | R339:budget30_session_recall_gt_fixed_tasks | 6/6 | pass | 15,85,123,139,161,163,169,170 |
| evaluation | R339:budget30_session_work_lt_raw_action_tasks | 5/6 | pass | 15,53,54,71,123,136,156,157 |
| evaluation | R339:csv_default_median_top5_operation_work | 0.0937 | pass | 190,366,382,443,444,445,446,447 |
| evaluation | R339:csv_default_median_top5_positive_session_recall | 0.2629 | pass | 191,382 |
| evaluation | R339:csv_default_median_budget30_positive_operation_recall | 0.3900 | pass | 193,281,376 |
| evaluation | R339:csv_default_median_budget30_positive_session_recall | 0.4669 | pass | 15,194,281,382 |
| evaluation | R339:csv_default_median_budget30_session_work | 0.3467 | pass | 15,195,281,382 |
| evaluation | R339:csv_budget30_session_recall_wins_vs_fixed | 6/6 | pass | 15,85,123,139,161,163,169,170 |
| evaluation | R339:csv_budget30_session_work_wins_vs_raw_action | 5/6 | pass | 15,53,54,71,123,136,156,157 |
| evaluation | R340:overall | pass | pass | 14,51,122,225,281,357,358,361 |
| evaluation | R340:tasks | 6 | pass | 3,4,12,13,15,32,41,42 |
| evaluation | R340:visible_policies | 15 | pass | 12,13,15,137,167,281,334,338 |
| evaluation | R340:objectives | 8 | pass | 12,13,14,15,32,33,73,85 |
| evaluation | R340:total_decisions | 96 | pass | 15,97,99,203,204,205,206,207 |
| evaluation | R340:exact_best_decisions | 31 | pass | 15,114,116,120,122,125,147,204 |
| evaluation | R340:within_tolerance_decisions | 62 | pass | 13,15,191,204,281,359,382,383 |
| evaluation | R340:selected_beats_width | 72 | pass | 12,15,205,281,307,318,334,346 |
| evaluation | R340:selected_beats_fixed | 69 | pass | 15,133,194,205,281,309,324,336 |
| evaluation | R340:selected_beats_flat | 41 | pass | 13,15,206,213,281,310,324,337 |
| evaluation | R340:operation_stack_selected | 16 | pass | 13,15,178,192,207,225,281,298 |
| evaluation | R340:leave_task_decisions | 48 | pass | 319,320,345,413,428,430 |
| evaluation | R340:leave_task_within_tolerance | 32 | pass | 12,14,15,36,40,43,44,47 |
| evaluation | R340:leave_dataset_decisions | 48 | pass | 319,320,345,413,428,430 |
| evaluation | R340:leave_dataset_within_tolerance | 30 | pass | 12,15,39,50,79,91,92,102 |
| evaluation | R340:decision_rows | 96 | pass | 15,97,99,203,204,205,206,207 |
| evaluation | R340:objective_rows | 16 | pass | 13,15,178,192,207,225,281,298 |
| evaluation | R340:selected_policy_visible_rows | 96/96 | pass | 211,212 |
| evaluation | R340:best_policy_visible_rows | 96/96 | pass | 211,212 |
| evaluation | R340:selected_policy_no_oracle_or_label_drilldown | 96/96 | pass | 211,212 |
| evaluation | R340:best_policy_no_oracle_or_label_drilldown | 96/96 | pass | 211,212 |
| evaluation | R340:leave_task_excludes_target_task | 96/96 | pass | 211,212 |
| evaluation | R340:leave_dataset_excludes_target_dataset | 96/96 | pass | 211,212 |
| evaluation | R341:overall | R341 | pass | 15,213,281,381,384,540,543,614 |
| evaluation | R341:tasks | 6 tasks | pass | 15,281,384 |
| evaluation | R341:objective_rows | 36 objective rows | pass | 15,281,384 |
| evaluation | R341:objective_best_policy_visible_rows | 36/36 best policies visible | pass | 384 |
| evaluation | R341:objective_best_policy_non_oracle_rows | 36/36 best policies non-oracle | pass | 384 |
| evaluation | R341:actionable_objective_rows | 36/36 objective rows have optimization actions | pass | 15,281,384 |
| evaluation | R341:nondefault_best_objective_rows | 27/36 best visible policies are non-default | pass | 15,281,384 |
| evaluation | R341:transfer_decisions | 96 transfer decisions | pass | 384 |
| evaluation | R341:transfer_misses | 34/96 transfer decisions | pass | 384 |
| evaluation | R341:transfer_misses_with_view_change | 32/34 misses change view | pass | 384 |
| evaluation | R341:transfer_misses_with_ranker_change | 26/34 change ranker | pass | 384 |
| evaluation | R341:high_regret_transfer_misses | 29/34 high-regret misses | pass | 281,384 |
| evaluation | R341:stack_depth_tradeoff_tasks | stack-depth signals on 6/6 | pass | 384 |
| evaluation | R341:transfer_policy_signal_tasks | transfer-policy signals on 6/6 | pass | 384 |
| evaluation | R341:critical_rank_feature_tasks | critical features on 4/6 | pass | 384 |
| evaluation | R341:misleading_feature_tasks | misleading features on 2/6 | pass | 15,384 |
| evaluation | R341:tasks_with_three_or_more_mechanism_labels | three or more mechanism labels on 6/6 | pass | 384 |
| evaluation | R342:overall | R342 | pass | 12,15,78,221,278,281,283,381 |
| evaluation | R342:tasks | 6 tasks | pass | 15,281,385,465 |
| evaluation | R342:profile_spec_variants | 12 profile-spec variants | pass | 385,465 |
| evaluation | R342:composition_variants | 12/12 compose | pass | 15,385 |
| evaluation | R342:prompt_session_free_variants | 12/12 prompt/session-free | pass | 385 |
| evaluation | R342:rule_score_rank_policy_variants | rank_mode=rule-score | pass | 15,385,465 |
| evaluation | R342:ap_improves_vs_width_variants | 9/12 variants | pass | 15,385,465 |
| evaluation | R342:top5_lift_improves_vs_width_variants | 8/12 | pass | 15 |
| evaluation | R342:first_positive_work_improves_vs_width_variants | 10/12 | pass | 15,385,465 |
| evaluation | R342:tasks_with_ap_improvement_any_depth | 5/6 | pass | 15,281 |
| evaluation | R342:tasks_with_first_positive_improvement_any_depth | 6/6 | pass | 15,281,385,465 |
| evaluation | R342:tasks_where_coarse_reduces_groups | 6/6 tasks | pass | 15,281,385,465 |
| evaluation | R342:median_coarse_group_reduction | 0.8267 | pass | 15,385,465 |
| evaluation | R342:tasks_where_depth_choice_changes_objective | 3/6 tasks | pass | 385 |
| evaluation | R342:best_ap_semantic_depth_tasks | semantic 4 / coarse 2 | pass | 15,385,465 |
| evaluation | R342:best_ap_coarse_depth_tasks | semantic 4 / coarse 2 | pass | 15,385,465 |

## Guardrails

| Doc | Guardrail | Status | Occurrences | Occurrence lines | Unguarded overclaim lines |
|---|---|---|---:|---|---|
| evaluation | human_utility | pass | 12 | 15,281,353,357,435,438,440,441,445,449,450,452 | none |
| evaluation | automatic_boundary | pass | 6 | 228,281,434,435,457,465 | none |
| evaluation | ecosystem_compatibility | pass | 8 | 12,15,30,281,352,434,452,544 | none |
| evaluation | universal_selector | pass | 11 | 15,175,281,383,451,452,454,458,465,521,538 | none |
| zh_claim_setup | human_utility | pass | 12 | 26,28,36,39,75,76,77,84,85,88,89,91 | none |
| zh_claim_setup | automatic_boundary | pass | 5 | 23,25,26,39,237 | none |
| zh_claim_setup | ecosystem_compatibility | pass | 8 | 22,69,87,141,188,225,226,227 | none |
| zh_claim_setup | universal_selector | pass | 12 | 26,34,36,37,38,39,104,105,106,107,108,109 | none |
| zh_main | human_utility | pass | 9 | 76,202,382,425,559,626,636,666,667 | none |
| zh_main | automatic_boundary | pass | 1 | 76 | none |
| zh_main | ecosystem_compatibility | pass | 12 | 51,160,582,590,591,594,630,653,670,681,691,692 | none |
| zh_main | universal_selector | pass | 8 | 76,470,476,557,619,656,661,664 | none |
| en_main | human_utility | pass | 4 | 144,158,576,635 | none |
| en_main | automatic_boundary | pass | 2 | 576,745 | none |
| en_main | ecosystem_compatibility | pass | 12 | 668,670,678,680,681,682,688,689,746,829,830,832 | none |
| en_main | universal_selector | pass | 7 | 397,400,553,562,577,717,724 | none |
