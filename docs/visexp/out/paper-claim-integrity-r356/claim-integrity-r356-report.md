# Paper Claim Integrity Refresh R356

R356 reuses the R338 R320-R350 paper gate and extends it to R354/R355. It does not fetch, sync, create, or relabel datasets.

## Verdict

- Overall: pass.
- Base R338 gate: pass.
- R354/R355 result invariants: pass.
- Paper text coverage: pass.
- Guardrails: pass.
- Two-abstraction boundary: pass.
- Source artifacts tracked clean: True.

## Claim Position

R356 keeps the paper claim scoped to profiler fidelity, ranking, inspection work, fragmentation, oracle-depth triage, and executable profile-spec actionability on existing labeled traces. R354/R355 strengthen actionability and boundary-depth evidence, but they do not support automatic patch selection, human utility, or complete latent intent-boundary discovery.

## R354/R355 Checks

| Run | Key | Expected | Actual | Status | Source |
|---|---|---:|---:|---|---|
| R338 | overall | pass | pass | pass | R338 build_payload summary |
| R338 | number_checks_total | 350 | 350 | pass | R338 build_payload summary |
| R338 | source_policy | pass | pass | pass | R338 build_payload summary |
| R338 | guardrails | pass | pass | pass | R338 build_payload summary |
| R338 | two_abstraction_boundary | pass | pass | pass | R338 build_payload summary |
| R354 | status | pass | pass | pass | profile-patch-report.json |
| R354 | run_result_status | pass | pass | pass | run-result.json |
| R354 | tasks | 6 | 6 | pass | profile-patch-report.json |
| R354 | datasets | 4 | 4 | pass | profile-patch-report.json |
| R354 | summary_rows | 6 | 6 | pass | profile-patch-summary.csv |
| R354 | profile_spec_files | 12 | 12 | pass | R354 glob *-profile-spec.json |
| R354 | rust_json_profiles | 12 | 12 | pass | R354 glob profile JSON outputs |
| R354 | accepted_patches | 5/6 | 5/6 | pass | profile-patch-report.json summary |
| R354 | rejected_or_needs_mapping | 1/6 | 1/6 | pass | profile-patch-report.json summary |
| R354 | ap_improved_tasks | 5/6 | 5/6 | pass | profile-patch-report.json summary |
| R354 | top5_lift_improved_tasks | 5/6 | 5/6 | pass | profile-patch-report.json summary |
| R354 | first_positive_work_improved_tasks | 5/6 | 5/6 | pass | profile-patch-report.json summary |
| R354 | groups_reduced_tasks | 2/6 | 2/6 | pass | profile-patch-report.json summary |
| R354 | median_delta_ap | 0.0376 | 0.0376 | pass | profile-patch-report.json summary |
| R354 | median_delta_top5_lift | 0.575 | 0.575 | pass | profile-patch-report.json summary |
| R354 | median_delta_first_positive_work | -0.0859 | -0.0859 | pass | profile-patch-report.json summary |
| R354 | median_group_reduction | 0.0 | 0.0 | pass | profile-patch-report.json summary |
| R354 | csv_accepted_patch_rows | 5 | 5 | pass | profile-patch-summary.csv |
| R354 | csv_rejected_patch_rows | 1 | 1 | pass | profile-patch-summary.csv |
| R354 | csv_rejected_patch_task | osworld_group_start | osworld_group_start | pass | profile-patch-summary.csv |
| R354 | csv_ap_improved_rows | 5 | 5 | pass | profile-patch-summary.csv |
| R354 | csv_top5_lift_improved_rows | 5 | 5 | pass | profile-patch-summary.csv |
| R354 | csv_first_positive_improved_rows | 5 | 5 | pass | profile-patch-summary.csv |
| R354 | csv_groups_reduced_rows | 2 | 2 | pass | profile-patch-summary.csv |
| R354 | csv_median_delta_ap | 0.0376 | 0.0376 | pass | profile-patch-summary.csv |
| R354 | csv_median_delta_top5_lift | 0.575 | 0.5749 | pass | profile-patch-summary.csv |
| R354 | csv_median_delta_first_positive_work | -0.0859 | -0.0859 | pass | profile-patch-summary.csv |
| R354 | agentpprof_result_status_ok | 6 | 6 | pass | profile-patch-report.json tasks_detail |
| R354 | profile_specs_label_free | 12 | 12 | pass | R354 profile specs |
| R354 | nonclaim_no_human_or_agent_analyst | True | True | pass | profile-patch-report.json non_claims |
| R354 | nonclaim_not_automatic_patch_selector | True | True | pass | profile-patch-report.json non_claims |
| R354 | nonclaim_two_abstractions_only | True | True | pass | profile-patch-report.json non_claims |
| R355 | status | pass | pass | pass | oracle-depth-adequacy-report.json |
| R355 | run_result_status | pass | pass | pass | run-result.json |
| R355 | tasks | 6 | 6 | pass | claim_summary |
| R355 | datasets | 4 | 4 | pass | claim_summary |
| R355 | accuracy_unit_depth_rows | 24 | 24 | pass | claim_summary |
| R355 | subtask_eligible_unit_depth_rows | 16 | 16 | pass | claim_summary |
| R355 | true_subtask_oracle_rows | 5 | 5 | pass | claim_summary |
| R355 | context_only_rows | 1 | 1 | pass | claim_summary |
| R355 | default_policy | operation_stack:query_aware | operation_stack:query_aware | pass | claim_summary |
| R355 | unit_depths | ['agentnet_step', 'agentreward_turn', 'operation', 'osworld_human_group', 'positive_run', 'satraj_step', 'session'] | ['agentnet_step', 'agentreward_turn', 'operation', 'osworld_human_group', 'positive_run', 'satraj_step', 'session'] | pass | claim_summary |
| R355 | default_median_top5_unit_work | 0.1307 | 0.1307 | pass | claim_summary.default_all_depth_medians |
| R355 | default_median_budget30_positive_unit_recall | 0.4342 | 0.4342 | pass | claim_summary.default_all_depth_medians |
| R355 | default_median_budget30_positive_unit_f1 | 0.4484 | 0.4484 | pass | claim_summary.default_all_depth_medians |
| R355 | default_median_budget30_spillover_operation_fraction | 0.729 | 0.729 | pass | claim_summary.default_all_depth_medians |
| R355 | default_median_groups_to_50pct_positive_units | 27.5 | 27.5 | pass | claim_summary.default_all_depth_medians |
| R355 | positive_run_median_recall | 0.4908 | 0.4908 | pass | claim_summary.positive_run_medians |
| R355 | top5_unit_work_lt_flat_rows | 24 | 24 | pass | claim_summary.paired_checks |
| R355 | budget30_unit_recall_gt_fixed_rows | 20 | 20 | pass | claim_summary.paired_checks |
| R355 | budget30_unit_f1_gt_fixed_rows | 18 | 18 | pass | claim_summary.paired_checks |
| R355 | groups_to_50pct_units_lt_fixed_rows | 22 | 22 | pass | claim_summary.paired_checks |
| R355 | positive_units_per_group_lt_raw_rows | 24 | 24 | pass | claim_summary.paired_checks |
| R355 | depth_gap_lt_fixed_rows | 0 | 0 | pass | claim_summary.paired_checks |
| R355 | task_depth_card_rows | 24 | 24 | pass | task-depth-cards.csv |
| R355 | oracle_depth_matrix_rows | 25 | 25 | pass | oracle-depth-matrix.csv |
| R355 | policy_depth_summary_rows | 42 | 42 | pass | policy-depth-summary.csv |
| R355 | policy_depth_adequacy_rows | 144 | 144 | pass | policy-depth-adequacy.csv |
| R355 | depth_policy_comparison_rows | 50 | 50 | pass | depth-policy-comparisons.csv |
| R355 | task_cards_default_policy_rows | 10 | 10 | pass | task-depth-cards.csv |
| R355 | nonclaim_no_human_or_agent_analyst | True | True | pass | oracle-depth-adequacy-report.json non_claims |
| R355 | nonclaim_no_auto_all_boundaries | True | True | pass | oracle-depth-adequacy-report.json non_claims |
| R355 | nonclaim_positive_run_proxy | True | True | pass | oracle-depth-adequacy-report.json non_claims |
| R355 | nonclaim_scalecua_context_only | True | True | pass | oracle-depth-adequacy-report.json non_claims |

## Text Coverage

| Doc | Key | Tokens | Status | Lines |
|---|---|---|---|---|
| evaluation | R354 profile patch | R354 / 5/6 / 0.0376 / 0.5750 | pass | 651,653,654 |
| evaluation | R355 oracle depth | R355 / 24 / 0.4342 / 20/24 / 22/24 | pass | 652,653 |
| evaluation | R356 refresh | R356 / R354 / R355 / claim-integrity | pass | 15,535,653,829,928 |
| zh_main | R354 profile patch | R354 / 5/6 / 0.0376 / 0.5750 | pass | 472 |
| zh_main | R355 oracle depth | R355 / 24 / 0.4342 / 20/24 / 22/24 | pass | missing |
| zh_main | R356 refresh | R356 / R354 / R355 / claim-integrity | pass | missing |
| en_main | R354 profile patch | R354 / 5 of 6 / 0.0376 / 0.5750 | pass | 587 |
| en_main | R355 oracle depth | R355 / 24 / 0.4342 / 20/24 / 22/24 | pass | missing |
| en_main | R356 refresh | R356 / R354 / R355 / claim-integrity | pass | 586 |
| zh_claim_setup | R354 profile patch | R354 / 5/6 / 0.0376 / 0.5750 | pass | 49,51,52,151 |
| zh_claim_setup | R355 oracle depth | R355 / 24 / 0.4342 / 20/24 / 22/24 | pass | 50,51,52,151 |
| zh_claim_setup | R356 refresh | R356 / R354 / R355 / claim-integrity | pass | 51 |
| design | R356 audit boundary | R356 / R354 / R355 / operation stack | pass | missing |
| implementation | R356 script | script/paper_claim_integrity_r356.py / R356 | pass | 44 |
| evaluation | R355 depth-gap counterpoint | R355 / depth-gap / fixed-session | pass | 535,652 |
| en_main | R355 depth-gap counterpoint | R355 / depth-gap / fixed-session | pass | missing |
| zh_main | R355 depth-gap counterpoint | R355 / depth-gap / fixed-session | pass | missing |
| zh_claim_setup | R355 depth-gap counterpoint | R355 / depth-gap / fixed-session | pass | 50 |

## Guardrails

| Doc | Guardrail | Status | Occurrences | Occurrence lines | Unguarded lines |
|---|---|---|---:|---|---|
| evaluation | human_utility | pass | 12 | 15,30,144,535,607,611,711,714,716,717,721,725 | none |
| evaluation | automatic_boundary | pass | 11 | 15,29,30,229,482,535,710,711,733,742,847 | none |
| evaluation | ecosystem_compatibility | pass | 7 | 12,53,535,606,710,728,841 | none |
| evaluation | universal_selector | pass | 12 | 29,30,123,131,229,411,535,637,727,728,730,734 | none |
| zh_claim_setup | human_utility | pass | 12 | 26,28,36,42,43,47,49,51,52,53,78,102 | none |
| zh_claim_setup | automatic_boundary | pass | 12 | 23,25,26,47,48,50,51,52,53,78,150,152 | none |
| zh_claim_setup | ecosystem_compatibility | pass | 8 | 22,96,114,181,228,265,266,267 | none |
| zh_claim_setup | universal_selector | pass | 12 | 26,34,36,37,38,41,42,43,44,45,46,47 | none |
| zh_main | human_utility | pass | 9 | 60,180,368,411,479,558,638,649,671 | none |
| zh_main | automatic_boundary | pass | 3 | 445,475,557 | none |
| zh_main | ecosystem_compatibility | pass | 12 | 138,585,593,594,597,642,669,672,681,691,692,693 | none |
| zh_main | universal_selector | pass | 8 | 469,475,479,556,558,631,665,671 | none |
| en_main | human_utility | pass | 6 | 66,96,110,239,576,675 | none |
| en_main | automatic_boundary | pass | 6 | 67,247,528,564,585,790 | none |
| en_main | ecosystem_compatibility | pass | 12 | 709,711,719,721,722,723,729,730,791,792,822,827 | none |
| en_main | universal_selector | pass | 9 | 247,423,426,482,551,577,591,790,821 | none |
| design | human_utility | pass | 2 | 232,485 | none |
| design | automatic_boundary | pass | 3 | 270,280,293 | none |
| design | ecosystem_compatibility | pass | 1 | 192 | none |
| design | universal_selector | pass | 2 | 144,260 | none |
| implementation | human_utility | pass | 3 | 146,179,378 | none |
| implementation | automatic_boundary | pass | 4 | 156,207,215,377 | none |
| implementation | ecosystem_compatibility | pass | 4 | 23,231,240,379 | none |
| implementation | universal_selector | pass | 3 | 146,156,215 | none |
| evaluation | r354_not_automatic_patch_selector | pass | 55 | 15,29,33,135,146,177,178,181 | none |
| evaluation | r354_boundary_derived_counterpoint | pass | 55 | 15,29,33,135,146,177,178,181 | none |
| evaluation | r355_no_latent_boundary_discovery | pass | 59 | 13,15,28,33,152,167,177,178 | none |
| evaluation | r355_positive_run_proxy | pass | 11 | 13,154,158,171,533,652,821,944 | none |
| evaluation | r355_depth_gap_counterpoint | pass | 2 | 535,652 | none |
| zh_claim_setup | r354_not_automatic_patch_selector | pass | 16 | 49,51,52,53,55,77,151,154 | none |
| zh_claim_setup | r354_boundary_derived_counterpoint | pass | 16 | 49,51,52,53,55,77,151,154 | none |
| zh_claim_setup | r355_no_latent_boundary_discovery | pass | 14 | 50,51,52,55,76,151,154 | none |
| zh_claim_setup | r355_positive_run_proxy | pass | 3 | 50 | none |
| zh_claim_setup | r355_depth_gap_counterpoint | pass | 1 | 50 | none |
| zh_main | r354_not_automatic_patch_selector | pass | 4 | 471,472,557 | none |
| zh_main | r354_boundary_derived_counterpoint | pass | 4 | 471,472,557 | none |
| zh_main | r355_no_latent_boundary_discovery | pass | 1 | 556 | none |
| zh_main | r355_positive_run_proxy | pass | 1 | none | none |
| zh_main | r355_depth_gap_counterpoint | pass | 1 | 461 | none |
| en_main | r354_not_automatic_patch_selector | pass | 4 | 242,554,586,587 | none |
| en_main | r354_boundary_derived_counterpoint | pass | 4 | 242,554,586,587 | none |
| en_main | r355_no_latent_boundary_discovery | pass | 2 | 586,588 | none |
| en_main | r355_positive_run_proxy | pass | 1 | none | none |
| en_main | r355_depth_gap_counterpoint | pass | 1 | 527 | none |
| design | r354_not_automatic_patch_selector | pass | 6 | 250,259,263,283,284,303 | none |
| design | r354_boundary_derived_counterpoint | pass | 6 | 250,259,263,283,284,303 | none |
| design | r355_no_latent_boundary_discovery | pass | 5 | 272,280,283,284,303 | none |
| design | r355_positive_run_proxy | pass | 2 | 275,279 | none |
| design | r355_depth_gap_counterpoint | pass | 1 | 280 | none |
| implementation | r354_not_automatic_patch_selector | pass | 9 | 36,44,138,148,168,174,190,210 | none |
| implementation | r354_boundary_derived_counterpoint | pass | 9 | 36,44,138,148,168,174,190,210 | none |
| implementation | r355_no_latent_boundary_discovery | pass | 9 | 38,44,168,174,191,197,207,210 | none |
| implementation | r355_positive_run_proxy | pass | 2 | 38,200 | none |
| implementation | r355_depth_gap_counterpoint | pass | 1 | 206 | none |
