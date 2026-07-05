# R331 Profile Negative-Control Audit

R331 keeps each visible ranking fixed and randomly reallocates hidden positive labels across same-size operation groups.
It is a prevalence/group-size negative control over existing R320 tasks, not a new dataset or human study.

## Primary Findings

- Operation-stack query-aware AP exceeds the label-permutation null on 6/6 tasks (median AP delta 0.0759).
- The same policy's top-5 precision exceeds the null on 3/6 tasks and 30% budget recall exceeds the null on 5/6 tasks.
- Width-only operation-stack AP exceeds the null on 5/6 tasks, so some signal comes from stack grouping itself; query-aware ranking remains needed for the stronger R320/R330 results.
- Fixed-session query-aware AP exceeds the null on 6/6 tasks, preserving it as a real low-work counterpoint rather than a strawman baseline.
- Raw action/status AP exceeds the null on 6/6 tasks, but R320/R330 show its mapped-depth comparison is task-sensitive; R331 therefore calibrates signal, not universal dominance.

## Policy-Level Null Summary

| Policy | Metric | Direction | Tasks beyond 95% null | Median delta | Median ratio | Median p |
|---|---|---:|---:|---:|---:|---:|
| dataset_native:query_aware | average_precision | higher | 5/6 | 0.0635 | 1.2467 | 0.0005 |
| dataset_native:query_aware | top5_precision | higher | 1/6 | 0.0 | 1.0 | 0.998 |
| dataset_native:query_aware | budget30_recall | higher | 4/6 | 0.0569 | 1.2097 | 0.018 |
| dataset_native:query_aware | work_to_first_positive | lower | 0/6 | 0.0 | 1.0 | 1.0 |
| fixed_session:query_aware | average_precision | higher | 6/6 | 0.1089 | 1.2945 | 0.0005 |
| fixed_session:query_aware | top5_precision | higher | 4/6 | 0.0921 | 1.6918 | 0.0045 |
| fixed_session:query_aware | budget30_recall | higher | 5/6 | 0.0566 | 1.1889 | 0.0007 |
| fixed_session:query_aware | work_to_first_positive | lower | 1/6 | -0.0 | 0.9954 | 0.9505 |
| operation_stack:query_aware | average_precision | higher | 6/6 | 0.0759 | 1.3448 | 0.0005 |
| operation_stack:query_aware | top5_precision | higher | 3/6 | 0.078 | 1.6588 | 0.0695 |
| operation_stack:query_aware | budget30_recall | higher | 5/6 | 0.0904 | 1.3018 | 0.0005 |
| operation_stack:query_aware | work_to_first_positive | lower | 0/6 | -0.0 | 0.9995 | 0.9995 |
| operation_stack:width | average_precision | higher | 5/6 | 0.0221 | 1.1584 | 0.0005 |
| operation_stack:width | top5_precision | higher | 3/6 | 0.0082 | 1.0496 | 0.0562 |
| operation_stack:width | budget30_recall | higher | 4/6 | 0.0373 | 1.1244 | 0.0142 |
| operation_stack:width | work_to_first_positive | lower | 0/6 | 0.0 | 1.0 | 1.0 |
| raw_action_stack:query_aware | average_precision | higher | 6/6 | 0.0398 | 1.1388 | 0.0005 |
| raw_action_stack:query_aware | top5_precision | higher | 2/6 | 0.0113 | 1.0371 | 0.3906 |
| raw_action_stack:query_aware | budget30_recall | higher | 3/6 | 0.0376 | 1.1261 | 0.3531 |
| raw_action_stack:query_aware | work_to_first_positive | lower | 0/6 | 0.0 | 1.0 | 1.0 |

## Claim Boundary

- Supports: the main R320/R330 ranking signal is not explainable by prevalence and group-size alone on the primary operation-stack query-aware comparisons.
- Also supports: fixed-session and raw-action baselines contain real signal and should remain counterpoints.
- Does not support: human utility, label-free deployment ranking, or operation-stack dominance on every metric.
