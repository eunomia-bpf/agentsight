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
| evaluation | R354 profile patch | R354 / 5/6 / 0.0376 / 0.5750 | pass | 686,688,689 |
| evaluation | R355 oracle depth | R355 / 24 / 0.4342 / 20/24 / 22/24 | pass | 687,688 |
| evaluation | R356 refresh | R356 / R354 / R355 / claim-integrity | pass | 570,688,866,967 |
| zh_main | R354 profile patch | R354 / 5/6 / 0.0376 / 0.5750 | pass | 395,440 |
| zh_main | R355 oracle depth | R355 / 24 / 0.4342 / 20/24 / 22/24 | pass | missing |
| zh_main | R356 refresh | R356 / R354 / R355 / claim-integrity | pass | missing |
| en_main | R354 profile patch | R354 / 5 of 6 / 0.0376 / 0.5750 | pass | missing |
| en_main | R355 oracle depth | R355 / 24 / 0.4342 / 20/24 / 22/24 | pass | missing |
| en_main | R356 refresh | R356 / R354 / R355 / claim-integrity | pass | missing |
| zh_claim_setup | R354 profile patch | R354 / 5/6 / 0.0376 / 0.5750 | pass | 49,51,52,151 |
| zh_claim_setup | R355 oracle depth | R355 / 24 / 0.4342 / 20/24 / 22/24 | pass | 50,51,52,151 |
| zh_claim_setup | R356 refresh | R356 / R354 / R355 / claim-integrity | pass | 51 |
| design | R356 audit boundary | R356 / R354 / R355 / operation stack | pass | missing |
| implementation | R356 script | script/paper_claim_integrity_r356.py / R356 | pass | 46 |
| evaluation | R355 depth-gap counterpoint | R355 / depth-gap / fixed-session | pass | 570,687 |
| en_main | R355 depth-gap counterpoint | R355 / depth-gap / fixed-session | pass | 616 |
| zh_main | R355 depth-gap counterpoint | R355 / depth-gap / fixed-session | pass | missing |
| zh_claim_setup | R355 depth-gap counterpoint | R355 / depth-gap / fixed-session | pass | 50 |

## Guardrails

| Doc | Guardrail | Status | Occurrences | Occurrence lines | Unguarded lines |
|---|---|---|---:|---|---|
| evaluation | human_utility | pass | 12 | 16,36,175,570,642,646,748,751,753,754,758,762 | none |
| evaluation | automatic_boundary | pass | 12 | 35,36,65,260,517,569,570,747,748,770,779,886 | none |
| evaluation | ecosystem_compatibility | pass | 8 | 13,16,84,570,641,747,765,880 | none |
| evaluation | universal_selector | pass | 12 | 35,36,154,162,260,446,570,672,764,765,767,771 | none |
| zh_claim_setup | human_utility | pass | 12 | 26,28,36,42,43,47,49,51,52,53,78,102 | none |
| zh_claim_setup | automatic_boundary | pass | 12 | 23,25,26,47,48,50,51,52,53,78,150,152 | none |
| zh_claim_setup | ecosystem_compatibility | pass | 8 | 22,96,114,181,228,265,266,267 | none |
| zh_claim_setup | universal_selector | pass | 12 | 26,34,36,37,38,41,42,43,44,45,46,47 | none |
| zh_main | human_utility | pass | 9 | 60,180,240,395,408,447,590,601,623 | none |
| zh_main | automatic_boundary | pass | 6 | 237,239,321,412,443,517 | none |
| zh_main | ecosystem_compatibility | pass | 12 | 138,408,537,545,546,549,594,621,624,633,643,644 | none |
| zh_main | universal_selector | pass | 8 | 238,395,437,443,447,583,617,623 | none |
| en_main | human_utility | pass | 8 | 70,100,113,245,262,466,686,779 | none |
| en_main | automatic_boundary | pass | 7 | 235,255,355,617,653,740,895 | none |
| en_main | ecosystem_compatibility | pass | 12 | 69,813,815,823,825,826,827,834,896,897,927,932 | none |
| en_main | universal_selector | pass | 9 | 255,466,508,511,567,640,687,895,926 | none |
| design | human_utility | pass | 2 | 238,491 | none |
| design | automatic_boundary | pass | 3 | 276,286,300 | none |
| design | ecosystem_compatibility | pass | 1 | 198 | none |
| design | universal_selector | pass | 2 | 150,266 | none |
| implementation | human_utility | pass | 3 | 148,181,405 | none |
| implementation | automatic_boundary | pass | 5 | 158,218,234,242,404 | none |
| implementation | ecosystem_compatibility | pass | 4 | 23,258,267,406 | none |
| implementation | universal_selector | pass | 3 | 148,158,242 | none |
| evaluation | r354_not_automatic_patch_selector | pass | 56 | 16,35,39,46,52,166,177,208 | none |
| evaluation | r354_boundary_derived_counterpoint | pass | 56 | 16,35,39,46,52,166,177,208 | none |
| evaluation | r355_no_latent_boundary_discovery | pass | 57 | 14,16,34,39,46,183,198,208 | none |
| evaluation | r355_positive_run_proxy | pass | 11 | 14,185,189,202,568,687,858,985 | none |
| evaluation | r355_depth_gap_counterpoint | pass | 2 | 570,687 | none |
| zh_claim_setup | r354_not_automatic_patch_selector | pass | 16 | 49,51,52,53,55,77,151,154 | none |
| zh_claim_setup | r354_boundary_derived_counterpoint | pass | 16 | 49,51,52,53,55,77,151,154 | none |
| zh_claim_setup | r355_no_latent_boundary_discovery | pass | 14 | 50,51,52,55,76,151,154 | none |
| zh_claim_setup | r355_positive_run_proxy | pass | 3 | 50 | none |
| zh_claim_setup | r355_depth_gap_counterpoint | pass | 1 | 50 | none |
| zh_main | r354_not_automatic_patch_selector | pass | 6 | 239,368,395,439,440 | none |
| zh_main | r354_boundary_derived_counterpoint | pass | 6 | 239,368,395,439,440 | none |
| zh_main | r355_no_latent_boundary_discovery | pass | 3 | 238,401,405 | none |
| zh_main | r355_positive_run_proxy | pass | 2 | 394 | none |
| zh_main | r355_depth_gap_counterpoint | pass | 1 | 429 | none |
| en_main | r354_not_automatic_patch_selector | pass | 6 | 248,416,435,466,643,705 | none |
| en_main | r354_boundary_derived_counterpoint | pass | 6 | 248,416,435,466,643,705 | none |
| en_main | r355_no_latent_boundary_discovery | pass | 4 | 416,610,616,705 | none |
| en_main | r355_positive_run_proxy | pass | 2 | 465 | none |
| en_main | r355_depth_gap_counterpoint | pass | 1 | 616 | none |
| design | r354_not_automatic_patch_selector | pass | 8 | 25,256,265,269,289,290,309,491 | none |
| design | r354_boundary_derived_counterpoint | pass | 8 | 25,256,265,269,289,290,309,491 | none |
| design | r355_no_latent_boundary_discovery | pass | 7 | 23,278,286,289,290,309,491 | none |
| design | r355_positive_run_proxy | pass | 3 | 281,285,491 | none |
| design | r355_depth_gap_counterpoint | pass | 1 | 286 | none |
| implementation | r354_not_automatic_patch_selector | pass | 10 | 36,46,140,150,170,176,192,202 | none |
| implementation | r354_boundary_derived_counterpoint | pass | 10 | 36,46,140,150,170,176,192,202 | none |
| implementation | r355_no_latent_boundary_discovery | pass | 10 | 38,46,170,176,193,202,223,234 | none |
| implementation | r355_positive_run_proxy | pass | 3 | 38,226,233 | none |
| implementation | r355_depth_gap_counterpoint | pass | 1 | 232 | none |
