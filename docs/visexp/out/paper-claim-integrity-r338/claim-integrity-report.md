# Paper Claim Integrity Audit R338

R338 mechanically audits the current profiling-paper claim against R320-R341 result artifacts and the Chinese/English paper text. It does not fetch, sync, create, or relabel datasets.

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
| R341 | overall | pass | pass | pass | R341 summary |
| R341 | tasks | 6 | 6 | pass | R341 summary |
| R341 | objective_rows | 36 | 36 | pass | R341 summary |
| R341 | objective_csv_rows | 36 | 36 | pass | R341 objective-mechanism-attribution.csv |
| R341 | actionable_objective_rows | 36 | 36 | pass | R341 summary |
| R341 | nondefault_best_objective_rows | 27 | 27 | pass | R341 summary |
| R341 | transfer_decisions | 96 | 96 | pass | R341 summary |
| R341 | transfer_csv_rows | 96 | 96 | pass | R341 transfer-error-attribution.csv |
| R341 | transfer_misses | 34 | 34 | pass | R341 summary |
| R341 | transfer_misses_with_view_change | 32 | 32 | pass | R341 summary |
| R341 | transfer_misses_with_ranker_change | 26 | 26 | pass | R341 summary |
| R341 | high_regret_transfer_misses | 29 | 29 | pass | R341 summary |
| R341 | stack_depth_tradeoff_tasks | 6 | 6 | pass | R341 summary.mechanism_task_counts |
| R341 | transfer_policy_signal_tasks | 6 | 6 | pass | R341 summary.mechanism_task_counts |
| R341 | critical_rank_feature_tasks | 4 | 4 | pass | R341 summary.mechanism_task_counts |
| R341 | misleading_feature_tasks | 2 | 2 | pass | R341 summary.mechanism_task_counts |
| R341 | tasks_with_three_or_more_mechanism_labels | 6 | 6 | pass | R341 summary |

## Text Coverage

| Doc | Key | Tokens | Status | Lines |
|---|---|---|---|---|
| evaluation | R320 headline operations | 34,539 / 34539 | pass | 15,101,123,239,271,327,334,336 |
| evaluation | R320 top5 work | 0.0937 / 9.37% | pass | 15,124,180,271,331,332,335,347 |
| evaluation | R333 budget30 recall | 0.3900 / 0.39 | pass | 183,271,357,422 |
| evaluation | R334 fragmentation | 5/6 / -54.0 / fewer groups | pass | 15,53,54,71,113,126,146,147 |
| evaluation | R335 actionability | actionability / 6/6 / optimization | pass | 5,15,57,76,113,129,132,150 |
| evaluation | R336 visible policies | 15 visible / 15 个 / 6 diagnostic | pass | 271,360,364 |
| evaluation | R337 fixed recall | 25% / 0.2000 / 16.0 | pass | 15,166,168,271,361 |
| evaluation | R339 sequence adequacy | R339 / 0.4669 / 0.9103 | pass | 13,15,176,184,187,191,271,362 |
| evaluation | R340 policy transfer | R340 / 96 / 62/96 / 72/96 | pass | 15,87,89,190,193,194,195,196 |
| evaluation | R341 mechanism attribution | R341 / 36/36 / 27/36 / 34/96 | pass | 15,203,204,205,206,211,271,362 |
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
| evaluation | R320:operations | 34,539 | pass | 15,101,123,239,271,327,334,336 |
| evaluation | R320:positives | 3,699 | pass | 15,123,337,340,344,347,358,427 |
| evaluation | R320:policies | 144 | pass | 15,122,342,347,357,363,433,438 |
| evaluation | R320:operation_stack_top5_work_median | 0.0937 | pass | 180,347,363,423,424,425,426,427 |
| evaluation | R320:flat_top5_work_median | 1.0 | pass | 15,169,181,271,326,329,343,347 |
| evaluation | R320:operation_stack_groups_median | 157.5 | pass | 15,127,271,347,438 |
| evaluation | R320:fixed_session_groups_median | 285.0 | pass | 15,127,271,347,438 |
| evaluation | R320:top5_recall_wins_vs_fixed | 5/6 | pass | 15,53,54,71,113,126,146,147 |
| evaluation | R320:ap_wins_vs_width | 6/6 | pass | 15,113,129,151,153,159,160,167 |
| evaluation | R333:operation_stack:query_aware_budget30_median_recall | 0.3900 | pass | 183,271,357 |
| evaluation | R333:flat:width_budget30_median_recall | 0.0000 | pass | 271,357 |
| evaluation | R333:fixed_session:query_aware_budget30_median_recall | 0.3559 | pass | 271,357 |
| evaluation | R333:dataset_native:query_aware_budget30_median_recall | 0.3377 | pass | 271,357 |
| evaluation | R333:raw_action_stack:query_aware_budget30_median_recall | 0.3325 | pass | 271,357 |
| evaluation | R337:target25_tasks_reached | 6/6 | pass | 15,113,129,151,153,159,160,167 |
| evaluation | R337:target25_median_work | 0.2000 | pass | 15,168,271,361 |
| evaluation | R337:target25_median_groups | 16.0 | pass | 15,168,271,361 |
| evaluation | R337:target10_tasks_reached | 6/6 | pass | 15,113,129,151,153,159,160,167 |
| evaluation | R337:target10_median_groups | 12.5 | pass | 172,361 |
| evaluation | R337:target50_tasks_reached | 5/6 | pass | 15,53,54,71,113,126,146,147 |
| evaluation | R337:flat_target25_median_work | 1.0000 | pass | 15,169,181,271,361 |
| evaluation | R337:fixed_target25_median_groups | 50.0 | pass | 15,170,271,361 |
| evaluation | R337:fixed_target10_median_groups | 37.5 | pass | 172,361 |
| evaluation | R337:default_vs_flat_target25_work_wins | 6/6 | pass | 15,113,129,151,153,159,160,167 |
| evaluation | R337:default_vs_fixed_target25_group_wins | 5/6 | pass | 15,53,54,71,113,126,146,147 |
| evaluation | R337:default_vs_fixed_target10_group_wins | 5/6 | pass | 15,53,54,71,113,126,146,147 |
| evaluation | R337:target25_csv_median_work | 0.2000 | pass | 15,168,271,361 |
| evaluation | R337:target25_csv_group_wins_vs_fixed | 5/6 | pass | 15,53,54,71,113,126,146,147 |
| evaluation | R339:overall | pass | pass | 14,51,112,215,271,338,339,342 |
| evaluation | R339:datasets | 4 | pass | 12,13,14,15,41,45,47,53 |
| evaluation | R339:tasks | 6 | pass | 3,4,12,13,15,32,41,42 |
| evaluation | R339:policies_scored | 144 | pass | 15,122,342,347,357,363,433,438 |
| evaluation | R339:hidden_labels_used_only_for_scoring | hidden labels only for scoring | pass | 363 |
| evaluation | R339:top5_median_operation_work | 0.0937 | pass | 180,347,363,423,424,425,426,427 |
| evaluation | R339:top5_median_positive_session_recall | 0.2629 | pass | 181,363 |
| evaluation | R339:top5_fixed_positive_session_recall | 0.0160 | pass | 182,363 |
| evaluation | R339:top5_flat_operation_work | 1.0000 | pass | 15,169,181,271,361 |
| evaluation | R339:budget30_median_positive_operation_recall | 0.3900 | pass | 183,271,357 |
| evaluation | R339:budget30_median_positive_session_recall | 0.4669 | pass | 15,184,271,363 |
| evaluation | R339:budget30_median_session_work | 0.3467 | pass | 15,185,271,363 |
| evaluation | R339:budget30_fixed_positive_session_recall | 0.3230 | pass | 15,185,271,363 |
| evaluation | R339:budget30_raw_action_positive_session_recall | 0.5147 | pass | 15,187,271,363 |
| evaluation | R339:budget30_raw_action_session_work | 0.9103 | pass | 15,187,271,363 |
| evaluation | R339:top5_operation_work_lt_flat_tasks | 6/6 | pass | 15,113,129,151,153,159,160,167 |
| evaluation | R339:budget30_session_recall_gt_fixed_tasks | 6/6 | pass | 15,113,129,151,153,159,160,167 |
| evaluation | R339:budget30_session_work_lt_raw_action_tasks | 5/6 | pass | 15,53,54,71,113,126,146,147 |
| evaluation | R339:csv_default_median_top5_operation_work | 0.0937 | pass | 180,347,363,423,424,425,426,427 |
| evaluation | R339:csv_default_median_top5_positive_session_recall | 0.2629 | pass | 181,363 |
| evaluation | R339:csv_default_median_budget30_positive_operation_recall | 0.3900 | pass | 183,271,357 |
| evaluation | R339:csv_default_median_budget30_positive_session_recall | 0.4669 | pass | 15,184,271,363 |
| evaluation | R339:csv_default_median_budget30_session_work | 0.3467 | pass | 15,185,271,363 |
| evaluation | R339:csv_budget30_session_recall_wins_vs_fixed | 6/6 | pass | 15,113,129,151,153,159,160,167 |
| evaluation | R339:csv_budget30_session_work_wins_vs_raw_action | 5/6 | pass | 15,53,54,71,113,126,146,147 |
| evaluation | R340:overall | pass | pass | 14,51,112,215,271,338,339,342 |
| evaluation | R340:tasks | 6 | pass | 3,4,12,13,15,32,41,42 |
| evaluation | R340:visible_policies | 15 | pass | 12,13,15,127,157,271,315,319 |
| evaluation | R340:objectives | 8 | pass | 12,13,14,15,32,33,73,85 |
| evaluation | R340:total_decisions | 96 | pass | 15,87,89,193,194,195,196,197 |
| evaluation | R340:exact_best_decisions | 31 | pass | 15,104,106,110,112,115,137,194 |
| evaluation | R340:within_tolerance_decisions | 62 | pass | 13,15,181,194,271,340,363,364 |
| evaluation | R340:selected_beats_width | 72 | pass | 12,15,195,271,288,299,315,327 |
| evaluation | R340:selected_beats_fixed | 69 | pass | 15,123,184,195,271,290,305,317 |
| evaluation | R340:selected_beats_flat | 41 | pass | 13,15,196,203,211,271,291,305 |
| evaluation | R340:operation_stack_selected | 16 | pass | 13,15,168,182,197,215,271,279 |
| evaluation | R340:leave_task_decisions | 48 | pass | 300,301,326,393,408,410 |
| evaluation | R340:leave_task_within_tolerance | 32 | pass | 12,14,15,36,40,43,44,47 |
| evaluation | R340:leave_dataset_decisions | 48 | pass | 300,301,326,393,408,410 |
| evaluation | R340:leave_dataset_within_tolerance | 30 | pass | 12,15,39,50,81,82,92,93 |
| evaluation | R340:decision_rows | 96 | pass | 15,87,89,193,194,195,196,197 |
| evaluation | R340:objective_rows | 16 | pass | 13,15,168,182,197,215,271,279 |
| evaluation | R340:selected_policy_visible_rows | 96/96 | pass | 201,202 |
| evaluation | R340:best_policy_visible_rows | 96/96 | pass | 201,202 |
| evaluation | R340:selected_policy_no_oracle_or_label_drilldown | 96/96 | pass | 201,202 |
| evaluation | R340:best_policy_no_oracle_or_label_drilldown | 96/96 | pass | 201,202 |
| evaluation | R340:leave_task_excludes_target_task | 96/96 | pass | 201,202 |
| evaluation | R340:leave_dataset_excludes_target_dataset | 96/96 | pass | 201,202 |
| evaluation | R341:overall | pass | pass | 14,51,112,215,271,338,339,342 |
| evaluation | R341:tasks | 6 | pass | 3,4,12,13,15,32,41,42 |
| evaluation | R341:objective_rows | 36 | pass | 15,157,203,204,205,271,290,317 |
| evaluation | R341:objective_csv_rows | 36 | pass | 15,157,203,204,205,271,290,317 |
| evaluation | R341:actionable_objective_rows | 36/36 | pass | 15,204,271,365 |
| evaluation | R341:nondefault_best_objective_rows | 27/36 | pass | 15,205,271,365 |
| evaluation | R341:transfer_decisions | 96 | pass | 15,87,89,193,194,195,196,197 |
| evaluation | R341:transfer_csv_rows | 96 | pass | 15,87,89,193,194,195,196,197 |
| evaluation | R341:transfer_misses | 34/96 | pass | 15,206,271,365 |
| evaluation | R341:transfer_misses_with_view_change | 32/34 | pass | 15,207,271,365 |
| evaluation | R341:transfer_misses_with_ranker_change | 26/34 | pass | 15,208,271,365 |
| evaluation | R341:high_regret_transfer_misses | 29/34 | pass | 208,271 |
| evaluation | R341:stack_depth_tradeoff_tasks | 6/6 | pass | 15,113,129,151,153,159,160,167 |
| evaluation | R341:transfer_policy_signal_tasks | 6/6 | pass | 15,113,129,151,153,159,160,167 |
| evaluation | R341:critical_rank_feature_tasks | 4/6 | pass | 15,41,45,53,54,70,72,152 |
| evaluation | R341:misleading_feature_tasks | 2/6 | pass | 15,64,115,147,152,153,154,164 |
| evaluation | R341:tasks_with_three_or_more_mechanism_labels | 6/6 | pass | 15,113,129,151,153,159,160,167 |

## Guardrails

| Doc | Guardrail | Status | Occurrences | Occurrence lines | Unguarded overclaim lines |
|---|---|---|---:|---|---|
| evaluation | human_utility | pass | 12 | 15,271,334,338,415,418,420,421,425,429,430,432 | none |
| evaluation | automatic_boundary | pass | 5 | 218,271,414,415,437 | none |
| evaluation | ecosystem_compatibility | pass | 8 | 12,15,30,271,333,414,432,522 | none |
| evaluation | universal_selector | pass | 10 | 15,165,271,364,431,432,434,438,499,516 | none |
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
