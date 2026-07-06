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
| evaluation | R354 profile patch | R354 / 5/6 / 0.0376 / 0.5750 | pass | 561,563,564 |
| evaluation | R355 oracle depth | R355 / 24 / 0.4342 / 20/24 / 22/24 | pass | 562,563 |
| evaluation | R356 refresh | R356 / R354 / R355 / claim-integrity | pass | 15,445,563,733,826 |
| zh_main | R354 profile patch | R354 / 5/6 / 0.0376 / 0.5750 | pass | 503,741 |
| zh_main | R355 oracle depth | R355 / 24 / 0.4342 / 20/24 / 22/24 | pass | 74,492,608,730,741 |
| zh_main | R356 refresh | R356 / R354 / R355 / claim-integrity | pass | 741 |
| en_main | R354 profile patch | R354 / 5 of 6 / 0.0376 / 0.5750 | pass | 754 |
| en_main | R355 oracle depth | R355 / 24 / 0.4342 / 20/24 / 22/24 | pass | missing |
| en_main | R356 refresh | R356 / R354 / R355 / claim-integrity | pass | 753 |
| zh_claim_setup | R354 profile patch | R354 / 5/6 / 0.0376 / 0.5750 | pass | 49,51,52,149 |
| zh_claim_setup | R355 oracle depth | R355 / 24 / 0.4342 / 20/24 / 22/24 | pass | 50,51,52,149 |
| zh_claim_setup | R356 refresh | R356 / R354 / R355 / claim-integrity | pass | 51 |
| design | R356 audit boundary | R356 / R354 / R355 / operation stack | pass | missing |
| implementation | R356 script | script/paper_claim_integrity_r356.py / R356 | pass | 39 |
| evaluation | R355 depth-gap counterpoint | R355 / depth-gap / fixed-session | pass | 445,562 |
| en_main | R355 depth-gap counterpoint | R355 / depth-gap / fixed-session | pass | missing |
| zh_main | R355 depth-gap counterpoint | R355 / depth-gap / fixed-session | pass | 74,608,730 |
| zh_claim_setup | R355 depth-gap counterpoint | R355 / depth-gap / fixed-session | pass | 50 |

## Guardrails

| Doc | Guardrail | Status | Occurrences | Occurrence lines | Unguarded lines |
|---|---|---|---:|---|---|
| evaluation | human_utility | pass | 12 | 15,30,136,445,517,521,615,618,620,621,625,629 | none |
| evaluation | automatic_boundary | pass | 11 | 15,29,30,221,392,445,614,615,637,646,745 | none |
| evaluation | ecosystem_compatibility | pass | 7 | 12,45,445,516,614,632,739 | none |
| evaluation | universal_selector | pass | 12 | 29,30,115,123,221,321,445,547,631,632,634,638 | none |
| zh_claim_setup | human_utility | pass | 12 | 26,28,36,42,43,47,49,51,52,53,76,100 | none |
| zh_claim_setup | automatic_boundary | pass | 12 | 23,25,26,47,48,50,51,52,53,76,148,150 | none |
| zh_claim_setup | ecosystem_compatibility | pass | 8 | 22,94,112,177,224,261,262,263 | none |
| zh_claim_setup | universal_selector | pass | 12 | 26,34,36,37,38,41,42,43,44,45,46,47 | none |
| zh_main | human_utility | pass | 12 | 84,211,395,438,498,503,624,691,702,741,742,743 | none |
| zh_main | automatic_boundary | pass | 3 | 84,85,504 | none |
| zh_main | ecosystem_compatibility | pass | 12 | 51,169,647,655,656,659,695,719,746,748,757,767 | none |
| zh_main | universal_selector | pass | 12 | 79,82,84,485,491,497,499,500,501,502,504,622 | none |
| en_main | human_utility | pass | 4 | 136,206,220,824 | none |
| en_main | automatic_boundary | pass | 5 | 173,731,742,752,960 | none |
| en_main | ecosystem_compatibility | pass | 12 | 858,860,868,870,871,872,878,879,961,1057,1058,1060 | none |
| en_main | universal_selector | pass | 12 | 131,458,461,614,640,683,702,714,732,758,907,914 | none |
| design | human_utility | pass | 2 | 232,449 | none |
| design | automatic_boundary | pass | 2 | 270,280 | none |
| design | ecosystem_compatibility | pass | 1 | 192 | none |
| design | universal_selector | pass | 2 | 144,260 | none |
| implementation | human_utility | pass | 2 | 141,332 | none |
| implementation | automatic_boundary | pass | 4 | 151,163,171,331 | none |
| implementation | ecosystem_compatibility | pass | 4 | 23,187,196,333 | none |
| implementation | universal_selector | pass | 3 | 141,151,171 | none |
| evaluation | r354_not_automatic_patch_selector | pass | 41 | 15,29,127,138,169,170,173,177 | none |
| evaluation | r354_boundary_derived_counterpoint | pass | 41 | 15,29,127,138,169,170,173,177 | none |
| evaluation | r355_no_latent_boundary_discovery | pass | 47 | 13,15,28,144,159,169,170,174 | none |
| evaluation | r355_positive_run_proxy | pass | 11 | 13,146,150,163,443,562,725,836 | none |
| evaluation | r355_depth_gap_counterpoint | pass | 2 | 445,562 | none |
| zh_claim_setup | r354_not_automatic_patch_selector | pass | 13 | 49,51,52,53,75,149 | none |
| zh_claim_setup | r354_boundary_derived_counterpoint | pass | 13 | 49,51,52,53,75,149 | none |
| zh_claim_setup | r355_no_latent_boundary_discovery | pass | 12 | 50,51,52,74,149 | none |
| zh_claim_setup | r355_positive_run_proxy | pass | 3 | 50 | none |
| zh_claim_setup | r355_depth_gap_counterpoint | pass | 1 | 50 | none |
| zh_main | r354_not_automatic_patch_selector | pass | 8 | 503,618,623,740,741 | none |
| zh_main | r354_boundary_derived_counterpoint | pass | 8 | 503,618,623,740,741 | none |
| zh_main | r355_no_latent_boundary_discovery | pass | 8 | 74,492,592,608,730,741 | none |
| zh_main | r355_positive_run_proxy | pass | 4 | 74,492,730 | none |
| zh_main | r355_depth_gap_counterpoint | pass | 3 | 74,608,730 | none |
| en_main | r354_not_automatic_patch_selector | pass | 5 | 160,715,753,754,1038 | none |
| en_main | r354_boundary_derived_counterpoint | pass | 5 | 160,715,753,754,1038 | none |
| en_main | r355_no_latent_boundary_discovery | pass | 9 | 162,615,629,733,753,755,921,1028 | none |
| en_main | r355_positive_run_proxy | pass | 6 | 98,618,623,735,738,922 | none |
| en_main | r355_depth_gap_counterpoint | pass | 3 | 104,163,925 | none |
| design | r354_not_automatic_patch_selector | pass | 5 | 250,259,263,283,284 | none |
| design | r354_boundary_derived_counterpoint | pass | 5 | 250,259,263,283,284 | none |
| design | r355_no_latent_boundary_discovery | pass | 4 | 272,280,283,284 | none |
| design | r355_positive_run_proxy | pass | 2 | 275,279 | none |
| design | r355_depth_gap_counterpoint | pass | 1 | 280 | none |
| implementation | r354_not_automatic_patch_selector | pass | 6 | 36,39,133,143,166,167 | none |
| implementation | r354_boundary_derived_counterpoint | pass | 6 | 36,39,133,143,166,167 | none |
| implementation | r355_no_latent_boundary_discovery | pass | 6 | 38,39,153,163,166,168 | none |
| implementation | r355_positive_run_proxy | pass | 2 | 38,156 | none |
| implementation | r355_depth_gap_counterpoint | pass | 1 | 162 | none |
