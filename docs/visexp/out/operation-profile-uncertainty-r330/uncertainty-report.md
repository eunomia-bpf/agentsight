# R330 Paired-Bootstrap Uncertainty Audit

- Source R320 report: `docs/visexp/out/operation-profile-accuracy-r320/profile-accuracy-report.json`
- Source R320 policy CSV: `docs/visexp/out/operation-profile-accuracy-r320/policy-scores.csv`
- Bootstrap repetitions: 10000
- Bootstrap seed: 330

## Supported Checks

| Comparison | Metric | Mean delta | 95% CI | Direction support | Tasks |
|---|---|---:|---|---:|---:|
| operation_stack_query_aware_vs_flat_width | average_precision | 0.1219 | [0.0406, 0.2175] | 1.000 | 6/6 |
| operation_stack_query_aware_vs_flat_width | top5_work | -0.8168 | [-0.9653, -0.6568] | 1.000 | 6/6 |
| operation_stack_query_aware_vs_flat_width | budget30_recall | 0.4510 | [0.3450, 0.6143] | 1.000 | 6/6 |
| operation_stack_query_aware_vs_flat_width | work_to_first_positive | -0.9303 | [-0.9855, -0.8650] | 1.000 | 6/6 |
| operation_stack_query_aware_vs_fixed_session_query_aware | top5_recall | 0.1801 | [0.0542, 0.3127] | 0.999 | 5/6 |
| operation_stack_query_aware_vs_fixed_session_query_aware | top5_f1 | 0.1702 | [0.0549, 0.2870] | 0.999 | 5/6 |
| operation_stack_query_aware_vs_fixed_session_query_aware | groups | -178.0000 | [-340.0000, -39.0000] | 0.999 | 4/6 |
| operation_stack_query_aware_vs_operation_stack_width | average_precision | 0.0932 | [0.0110, 0.2184] | 1.000 | 6/6 |
| operation_stack_query_aware_vs_operation_stack_width | top5_work | -0.3101 | [-0.4209, -0.1997] | 1.000 | 6/6 |
| operation_stack_query_aware_vs_operation_stack_width | work_to_first_positive | -0.1566 | [-0.3512, -0.0292] | 1.000 | 5/6 |

## Mixed Or Counterpoint Checks

| Comparison | Metric | Role | Mean delta | 95% CI | Direction support | Tasks |
|---|---|---|---:|---|---:|---:|
| operation_stack_query_aware_vs_flat_width | top5_recall | counterpoint_lower | -0.7608 | [-0.9303, -0.5658] | 1.000 | 6/6 |
| operation_stack_query_aware_vs_fixed_session_query_aware | top5_work | counterpoint_mixed | 0.1086 | [-0.0126, 0.2476] |  |  |
| operation_stack_query_aware_vs_fixed_session_query_aware | work_to_first_positive | counterpoint_mixed | 0.0031 | [-0.1190, 0.1044] |  |  |
| operation_stack_query_aware_vs_fixed_session_query_aware | average_precision | counterpoint_mixed | -0.0099 | [-0.0337, 0.0074] |  |  |
| operation_stack_query_aware_vs_operation_stack_width | budget30_recall | higher | 0.1392 | [-0.0264, 0.3841] | 0.919 | 5/6 |
| operation_stack_query_aware_vs_operation_stack_width | top5_f1 | counterpoint_mixed | -0.0045 | [-0.1491, 0.1694] |  |  |
| operation_stack_query_aware_vs_raw_action_stack_query_aware | average_precision | higher | 0.0202 | [-0.0420, 0.0743] | 0.747 | 5/6 |
| operation_stack_query_aware_vs_raw_action_stack_query_aware | budget30_recall | higher | 0.1068 | [-0.0088, 0.2168] | 0.967 | 4/6 |
| operation_stack_query_aware_vs_raw_action_stack_query_aware | top5_f1 | counterpoint_mixed | 0.0455 | [-0.1282, 0.2807] |  |  |
| operation_stack_query_aware_vs_raw_action_stack_query_aware | top5_recall | counterpoint_mixed | -0.0119 | [-0.1796, 0.2281] |  |  |

R330 bootstraps over the six R320 task families. It is an uncertainty audit over task-level policy scores, not a new dataset, human study, or per-operation independence claim.
