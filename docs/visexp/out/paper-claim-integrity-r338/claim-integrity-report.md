# Paper Claim Integrity Audit R338

R338 mechanically audits the current profiling-paper claim against R320-R340 result artifacts and the Chinese/English paper text. It does not fetch, sync, create, or relabel datasets.

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

## Text Coverage

| Doc | Key | Tokens | Status | Lines |
|---|---|---|---|---|
| evaluation | R320 headline operations | 34,539 / 34539 | pass | 15,101,123,228,260,316,323,325 |
| evaluation | R320 top5 work | 0.0937 / 9.37% | pass | 15,124,180,260,320,321,324,336 |
| evaluation | R333 budget30 recall | 0.3900 / 0.39 | pass | 183,260,346,410 |
| evaluation | R334 fragmentation | 5/6 / -54.0 / fewer groups | pass | 15,53,54,71,113,126,146,147 |
| evaluation | R335 actionability | actionability / 6/6 / optimization | pass | 5,15,57,76,113,129,132,150 |
| evaluation | R336 visible policies | 15 visible / 15 个 / 6 diagnostic | pass | 260,349,353 |
| evaluation | R337 fixed recall | 25% / 0.2000 / 16.0 | pass | 15,166,168,260,350 |
| evaluation | R339 sequence adequacy | R339 / 0.4669 / 0.9103 | pass | 13,15,176,184,187,191,260,351 |
| evaluation | R340 policy transfer | R340 / 96 / 62/96 / 72/96 | pass | 15,87,89,190,193,194,195,196 |
| zh_main | R320 headline | 0.0937 / 9.37 / 285.0 / 157.5 | pass | 63,73,396,403,413,414,475,500 |
| zh_main | R333 headline | 0.3900 / 0.390 | pass | 68,391,443,475,500,555,656 |
| zh_main | R337 headline | 0.2000 / 16.0 / 50.0 | pass | 72,474,555,660 |
| zh_main | R339 headline | 0.4669 / 0.9103 / 0.3467 | pass | 73,475,555,661 |
| zh_main | R340 headline | R340 / 62/96 / 72/96 / 69/96 | pass | 74,75,476,477,555,556,631,662 |
| en_main | R320 headline | 0.0937 / 9.37 / 285.0 / 157.5 | pass | 45,48,329,331,349,358,541 |
| en_main | R333 headline | 0.3900 / 0.390 | pass | 70,330,349,416,544 |
| en_main | R337 headline | 0.2000 / 16.0 / 50.0 | pass | 89,90,91,529,531,715,716 |
| en_main | R339 headline | 0.4669 / 0.9103 / 0.3467 | pass | 94,95,96,545,546,547,718,719 |
| en_main | R340 headline | R340 / 62 of 96 / 72 of 96 / 69 of 96 | pass | 103,549,560,720,723,799 |
| zh_claim_setup | two abstractions | 两个核心抽象 / operation stack | pass | 7,23,25,71,74,75,76,78 |
| zh_claim_setup | R337 result | R337 / 0.2000 / 16.0 | pass | 35,36,38,109,110,111 |
| zh_claim_setup | R339 result | R339 / 0.4669 / 0.9103 | pass | 36,37,38,110,111,112,245 |
| zh_claim_setup | R340 result | R340 / 62/96 / 72/96 / 69/96 | pass | 37,38,110,112 |
| evaluation | R320:datasets | 4 | pass | 12,13,14,15,41,45,47,53 |
| evaluation | R320:tasks | 6 | pass | 3,4,12,13,15,32,41,42 |
| evaluation | R320:operations | 34,539 | pass | 15,101,123,228,260,316,323,325 |
| evaluation | R320:positives | 3,699 | pass | 15,123,326,329,333,336,347,415 |
| evaluation | R320:policies | 144 | pass | 15,122,331,336,346,352,421,426 |
| evaluation | R320:operation_stack_top5_work_median | 0.0937 | pass | 180,336,352,411,412,413,414,415 |
| evaluation | R320:flat_top5_work_median | 1.0 | pass | 15,169,181,260,315,318,332,336 |
| evaluation | R320:operation_stack_groups_median | 157.5 | pass | 15,127,260,336,426 |
| evaluation | R320:fixed_session_groups_median | 285.0 | pass | 15,127,260,336,426 |
| evaluation | R320:top5_recall_wins_vs_fixed | 5/6 | pass | 15,53,54,71,113,126,146,147 |
| evaluation | R320:ap_wins_vs_width | 6/6 | pass | 15,113,129,151,153,159,160,167 |
| evaluation | R333:operation_stack:query_aware_budget30_median_recall | 0.3900 | pass | 183,260,346 |
| evaluation | R333:flat:width_budget30_median_recall | 0.0000 | pass | 260,346 |
| evaluation | R333:fixed_session:query_aware_budget30_median_recall | 0.3559 | pass | 260,346 |
| evaluation | R333:dataset_native:query_aware_budget30_median_recall | 0.3377 | pass | 260,346 |
| evaluation | R333:raw_action_stack:query_aware_budget30_median_recall | 0.3325 | pass | 260,346 |
| evaluation | R337:target25_tasks_reached | 6/6 | pass | 15,113,129,151,153,159,160,167 |
| evaluation | R337:target25_median_work | 0.2000 | pass | 15,168,260,350 |
| evaluation | R337:target25_median_groups | 16.0 | pass | 15,168,260,350 |
| evaluation | R337:target10_tasks_reached | 6/6 | pass | 15,113,129,151,153,159,160,167 |
| evaluation | R337:target10_median_groups | 12.5 | pass | 172,350 |
| evaluation | R337:target50_tasks_reached | 5/6 | pass | 15,53,54,71,113,126,146,147 |
| evaluation | R337:flat_target25_median_work | 1.0000 | pass | 15,169,181,260,350 |
| evaluation | R337:fixed_target25_median_groups | 50.0 | pass | 15,170,260,350 |
| evaluation | R337:fixed_target10_median_groups | 37.5 | pass | 172,350 |
| evaluation | R337:default_vs_flat_target25_work_wins | 6/6 | pass | 15,113,129,151,153,159,160,167 |
| evaluation | R337:default_vs_fixed_target25_group_wins | 5/6 | pass | 15,53,54,71,113,126,146,147 |
| evaluation | R337:default_vs_fixed_target10_group_wins | 5/6 | pass | 15,53,54,71,113,126,146,147 |
| evaluation | R337:target25_csv_median_work | 0.2000 | pass | 15,168,260,350 |
| evaluation | R337:target25_csv_group_wins_vs_fixed | 5/6 | pass | 15,53,54,71,113,126,146,147 |
| evaluation | R339:overall | pass | pass | 14,51,112,204,260,327,328,331 |
| evaluation | R339:datasets | 4 | pass | 12,13,14,15,41,45,47,53 |
| evaluation | R339:tasks | 6 | pass | 3,4,12,13,15,32,41,42 |
| evaluation | R339:policies_scored | 144 | pass | 15,122,331,336,346,352,421,426 |
| evaluation | R339:hidden_labels_used_only_for_scoring | hidden labels only for scoring | pass | 352 |
| evaluation | R339:top5_median_operation_work | 0.0937 | pass | 180,336,352,411,412,413,414,415 |
| evaluation | R339:top5_median_positive_session_recall | 0.2629 | pass | 181,352 |
| evaluation | R339:top5_fixed_positive_session_recall | 0.0160 | pass | 182,352 |
| evaluation | R339:top5_flat_operation_work | 1.0000 | pass | 15,169,181,260,350 |
| evaluation | R339:budget30_median_positive_operation_recall | 0.3900 | pass | 183,260,346 |
| evaluation | R339:budget30_median_positive_session_recall | 0.4669 | pass | 15,184,260,352 |
| evaluation | R339:budget30_median_session_work | 0.3467 | pass | 15,185,260,352 |
| evaluation | R339:budget30_fixed_positive_session_recall | 0.3230 | pass | 15,185,260,352 |
| evaluation | R339:budget30_raw_action_positive_session_recall | 0.5147 | pass | 15,187,260,352 |
| evaluation | R339:budget30_raw_action_session_work | 0.9103 | pass | 15,187,260,352 |
| evaluation | R339:top5_operation_work_lt_flat_tasks | 6/6 | pass | 15,113,129,151,153,159,160,167 |
| evaluation | R339:budget30_session_recall_gt_fixed_tasks | 6/6 | pass | 15,113,129,151,153,159,160,167 |
| evaluation | R339:budget30_session_work_lt_raw_action_tasks | 5/6 | pass | 15,53,54,71,113,126,146,147 |
| evaluation | R339:csv_default_median_top5_operation_work | 0.0937 | pass | 180,336,352,411,412,413,414,415 |
| evaluation | R339:csv_default_median_top5_positive_session_recall | 0.2629 | pass | 181,352 |
| evaluation | R339:csv_default_median_budget30_positive_operation_recall | 0.3900 | pass | 183,260,346 |
| evaluation | R339:csv_default_median_budget30_positive_session_recall | 0.4669 | pass | 15,184,260,352 |
| evaluation | R339:csv_default_median_budget30_session_work | 0.3467 | pass | 15,185,260,352 |
| evaluation | R339:csv_budget30_session_recall_wins_vs_fixed | 6/6 | pass | 15,113,129,151,153,159,160,167 |
| evaluation | R339:csv_budget30_session_work_wins_vs_raw_action | 5/6 | pass | 15,53,54,71,113,126,146,147 |
| evaluation | R340:overall | pass | pass | 14,51,112,204,260,327,328,331 |
| evaluation | R340:tasks | 6 | pass | 3,4,12,13,15,32,41,42 |
| evaluation | R340:visible_policies | 15 | pass | 12,13,15,127,157,260,304,308 |
| evaluation | R340:objectives | 8 | pass | 12,13,14,15,32,33,73,85 |
| evaluation | R340:total_decisions | 96 | pass | 15,87,89,193,194,195,196,197 |
| evaluation | R340:exact_best_decisions | 31 | pass | 15,104,106,110,112,115,137,194 |
| evaluation | R340:within_tolerance_decisions | 62 | pass | 13,15,181,194,260,329,352,353 |
| evaluation | R340:selected_beats_width | 72 | pass | 12,15,195,260,277,288,304,316 |
| evaluation | R340:selected_beats_fixed | 69 | pass | 15,123,184,195,260,279,294,306 |
| evaluation | R340:selected_beats_flat | 41 | pass | 13,15,196,204,260,280,294,307 |
| evaluation | R340:operation_stack_selected | 16 | pass | 13,15,168,182,197,204,260,268 |
| evaluation | R340:leave_task_decisions | 48 | pass | 289,290,315,381,396,398 |
| evaluation | R340:leave_task_within_tolerance | 32 | pass | 12,14,15,36,40,43,44,47 |
| evaluation | R340:leave_dataset_decisions | 48 | pass | 289,290,315,381,396,398 |
| evaluation | R340:leave_dataset_within_tolerance | 30 | pass | 12,15,39,50,81,82,92,93 |
| evaluation | R340:decision_rows | 96 | pass | 15,87,89,193,194,195,196,197 |
| evaluation | R340:objective_rows | 16 | pass | 13,15,168,182,197,204,260,268 |

## Guardrails

| Doc | Guardrail | Status | Occurrences | Occurrence lines | Unguarded overclaim lines |
|---|---|---|---:|---|---|
| evaluation | human_utility | pass | 12 | 15,260,323,327,403,406,408,409,413,417,418,420 | none |
| evaluation | automatic_boundary | pass | 5 | 207,260,402,403,425 | none |
| evaluation | ecosystem_compatibility | pass | 8 | 12,15,30,260,322,402,420,509 | none |
| evaluation | universal_selector | pass | 10 | 15,165,260,353,419,420,422,426,487,504 | none |
| zh_claim_setup | human_utility | pass | 12 | 26,28,36,38,74,75,76,83,84,87,88,90 | none |
| zh_claim_setup | automatic_boundary | pass | 5 | 23,25,26,38,235 | none |
| zh_claim_setup | ecosystem_compatibility | pass | 8 | 22,68,86,139,186,223,224,225 | none |
| zh_claim_setup | universal_selector | pass | 12 | 26,34,36,37,38,103,104,105,106,107,108,111 | none |
| zh_main | human_utility | pass | 9 | 75,201,381,424,557,624,634,663,664 | none |
| zh_main | automatic_boundary | pass | 1 | 75 | none |
| zh_main | ecosystem_compatibility | pass | 12 | 51,159,580,588,589,592,628,651,667,678,688,689 | none |
| zh_main | universal_selector | pass | 8 | 75,469,475,555,617,654,659,662 | none |
| en_main | human_utility | pass | 4 | 139,153,565,624 | none |
| en_main | automatic_boundary | pass | 2 | 565,730 | none |
| en_main | ecosystem_compatibility | pass | 12 | 657,659,667,669,670,671,677,678,731,812,813,815 | none |
| en_main | universal_selector | pass | 7 | 392,395,548,557,566,706,713 | none |
