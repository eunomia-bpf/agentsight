# Paper Claim Integrity Audit R338

R338 mechanically audits the current profiling-paper claim against R320-R337 result artifacts and the Chinese/English paper text. It does not fetch, sync, create, or relabel datasets.

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

## Text Coverage

| Doc | Key | Tokens | Status | Lines |
|---|---|---|---|---|
| evaluation | R320 headline operations | 34,539 / 34539 | pass | 15,101,123,205,237,293,300,302 |
| evaluation | R320 top5 work | 0.0937 / 9.37% | pass | 15,124,237,297,298,301,313,386 |
| evaluation | R333 budget30 recall | 0.3900 / 0.39 | pass | 237,323,385 |
| evaluation | R334 fragmentation | 5/6 / -54.0 / fewer groups | pass | 15,53,54,71,113,126,146,147 |
| evaluation | R335 actionability | actionability / 6/6 / optimization | pass | 5,15,57,76,113,129,132,150 |
| evaluation | R336 visible policies | 15 visible / 15 个 / 6 diagnostic | pass | 237,326 |
| evaluation | R337 fixed recall | 25% / 0.2000 / 16.0 | pass | 15,166,168,237,327 |
| zh_main | R320 headline | 0.0937 / 9.37 / 285.0 / 157.5 | pass | 63,394,401,411,412,496,551,645 |
| zh_main | R333 headline | 0.3900 / 0.390 | pass | 68,389,441,496,551,652 |
| zh_main | R337 headline | 0.2000 / 16.0 / 50.0 | pass | 72,472,551,656 |
| en_main | R320 headline | 0.0937 / 9.37 / 285.0 / 157.5 | pass | 45,48,318,320,338,347 |
| en_main | R333 headline | 0.3900 / 0.390 | pass | 70,319,338,405 |
| en_main | R337 headline | 0.2000 / 16.0 / 50.0 | pass | 89,90,91,518,520,683,684 |
| zh_claim_setup | two abstractions | 两个核心抽象 / operation stack | pass | 7,23,25,69,72,73,74,76 |
| zh_claim_setup | R337 result | R337 / 0.2000 / 16.0 | pass | 35,36,107,108 |
| evaluation | R320:datasets | 4 | pass | 12,13,14,15,41,45,47,53 |
| evaluation | R320:tasks | 6 | pass | 3,4,12,13,15,32,41,42 |
| evaluation | R320:operations | 34,539 | pass | 15,101,123,205,237,293,300,302 |
| evaluation | R320:positives | 3,699 | pass | 15,123,303,306,310,313,324,390 |
| evaluation | R320:policies | 144 | pass | 15,122,308,313,323,396,401 |
| evaluation | R320:operation_stack_top5_work_median | 0.0937 | pass | 313,386,387,388,389,390 |
| evaluation | R320:flat_top5_work_median | 1.0 | pass | 15,169,237,292,295,309,313,327 |
| evaluation | R320:operation_stack_groups_median | 157.5 | pass | 15,127,237,313,401 |
| evaluation | R320:fixed_session_groups_median | 285.0 | pass | 15,127,237,313,401 |
| evaluation | R320:top5_recall_wins_vs_fixed | 5/6 | pass | 15,53,54,71,113,126,146,147 |
| evaluation | R320:ap_wins_vs_width | 6/6 | pass | 15,113,129,151,153,159,160,167 |
| evaluation | R333:operation_stack:query_aware_budget30_median_recall | 0.3900 | pass | 237,323 |
| evaluation | R333:flat:width_budget30_median_recall | 0.0000 | pass | 237,323,328 |
| evaluation | R333:fixed_session:query_aware_budget30_median_recall | 0.3559 | pass | 237,323 |
| evaluation | R333:dataset_native:query_aware_budget30_median_recall | 0.3377 | pass | 237,323 |
| evaluation | R333:raw_action_stack:query_aware_budget30_median_recall | 0.3325 | pass | 237,323 |
| evaluation | R337:target25_tasks_reached | 6/6 | pass | 15,113,129,151,153,159,160,167 |
| evaluation | R337:target25_median_work | 0.2000 | pass | 15,168,237,327 |
| evaluation | R337:target25_median_groups | 16.0 | pass | 15,168,237,327 |
| evaluation | R337:target10_tasks_reached | 6/6 | pass | 15,113,129,151,153,159,160,167 |
| evaluation | R337:target10_median_groups | 12.5 | pass | 172,327 |
| evaluation | R337:target50_tasks_reached | 5/6 | pass | 15,53,54,71,113,126,146,147 |
| evaluation | R337:flat_target25_median_work | 1.0000 | pass | 15,169,237,327 |
| evaluation | R337:fixed_target25_median_groups | 50.0 | pass | 15,170,237,327 |
| evaluation | R337:fixed_target10_median_groups | 37.5 | pass | 172,327 |
| evaluation | R337:default_vs_flat_target25_work_wins | 6/6 | pass | 15,113,129,151,153,159,160,167 |
| evaluation | R337:default_vs_fixed_target25_group_wins | 5/6 | pass | 15,53,54,71,113,126,146,147 |
| evaluation | R337:default_vs_fixed_target10_group_wins | 5/6 | pass | 15,53,54,71,113,126,146,147 |
| evaluation | R337:target25_csv_median_work | 0.2000 | pass | 15,168,237,327 |
| evaluation | R337:target25_csv_group_wins_vs_fixed | 5/6 | pass | 15,53,54,71,113,126,146,147 |

## Guardrails

| Doc | Guardrail | Status | Occurrences | Occurrence lines | Unguarded overclaim lines |
|---|---|---|---:|---|---|
| evaluation | human_utility | pass | 12 | 15,237,300,304,378,381,383,384,388,392,393,395 | none |
| evaluation | automatic_boundary | pass | 5 | 184,237,377,378,400 | none |
| evaluation | ecosystem_compatibility | pass | 8 | 12,15,30,237,299,377,395,482 | none |
| evaluation | universal_selector | pass | 9 | 15,165,237,394,395,397,401,462,479 | none |
| zh_claim_setup | human_utility | pass | 12 | 26,28,36,72,73,74,81,82,85,86,88,99 | none |
| zh_claim_setup | automatic_boundary | pass | 5 | 23,25,26,36,231 | none |
| zh_claim_setup | ecosystem_compatibility | pass | 8 | 22,66,84,135,182,219,220,221 | none |
| zh_claim_setup | universal_selector | pass | 9 | 26,34,36,101,102,103,104,105,106 | none |
| zh_main | human_utility | pass | 9 | 73,199,379,422,553,620,630,657,658 | none |
| zh_main | automatic_boundary | pass | 1 | 73 | none |
| zh_main | ecosystem_compatibility | pass | 12 | 51,157,576,584,585,588,624,647,661,672,682,683 | none |
| zh_main | universal_selector | pass | 6 | 73,467,551,613,650,655 | none |
| en_main | human_utility | pass | 4 | 128,142,533,592 | none |
| en_main | automatic_boundary | pass | 2 | 533,691 | none |
| en_main | ecosystem_compatibility | pass | 12 | 625,627,635,637,638,639,645,646,692,772,773,775 | none |
| en_main | universal_selector | pass | 5 | 381,384,534,674,681 | none |
