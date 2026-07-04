# R300 Operation-Query Utility

This run uses existing tracked operation JSONL only. It is an automated oracle-backed proxy for analysis utility, not a human user study.

## View Summary

| View | Tasks | Median groups | Median top-positive lift | Median inspection fraction for 50% positives | Median top-group sessions |
|---|---:|---:|---:|---:|---:|
| flat | 6 | 1.0 | 1.0 | 1.0 | 285.0 |
| fixed_session | 6 | 285.0 | 3.464 | 0.2288 | 1.0 |
| operation_stack | 6 | 157.5 | 5.726 | 0.2879 | 5.5 |
| label_drilldown | 6 | 86.5 | 6.069 | 0.0917 | 27.0 |

## Task Results

| Task | View | Ops | Positives | Groups | Top lift | Inspect frac @50% positives | Top sessions |
|---|---|---:|---:|---:|---:|---:|---:|
| agentreward_looping | flat | 729 | 504 | 1 | 1.0 | 1.0 | 29.0 |
| agentreward_looping | fixed_session | 729 | 504 | 29 | 1.446 | 0.3704 | 1.0 |
| agentreward_looping | operation_stack | 729 | 504 | 40 | 1.446 | 0.5377 | 3.0 |
| agentreward_looping | label_drilldown | 729 | 504 | 28 | 1.446 | 0.4129 | 7.0 |
| agentreward_side_effect | flat | 729 | 202 | 1 | 1.0 | 1.0 | 29.0 |
| agentreward_side_effect | fixed_session | 729 | 202 | 29 | 3.539 | 0.1399 | 1.0 |
| agentreward_side_effect | operation_stack | 729 | 202 | 40 | 3.037 | 0.2209 | 2.6 |
| agentreward_side_effect | label_drilldown | 729 | 202 | 30 | 3.609 | 0.166 | 2.0 |
| satraj_unsafe | flat | 4285 | 622 | 1 | 1.0 | 1.0 | 250.0 |
| satraj_unsafe | fixed_session | 4285 | 622 | 250 | 6.889 | 0.0744 | 1.0 |
| satraj_unsafe | operation_stack | 4285 | 622 | 142 | 6.889 | 0.0789 | 16.6 |
| satraj_unsafe | label_drilldown | 4285 | 622 | 108 | 6.889 | 0.081 | 17.4 |
| agentnet_incorrect_step | flat | 14718 | 874 | 1 | 1.0 | 1.0 | 835.0 |
| agentnet_incorrect_step | fixed_session | 14718 | 874 | 835 | 5.369 | 0.1961 | 1.0 |
| agentnet_incorrect_step | operation_stack | 14718 | 874 | 289 | 7.605 | 0.2921 | 8.0 |
| agentnet_incorrect_step | label_drilldown | 14718 | 874 | 287 | 16.84 | 0.0309 | 40.4 |
| agentnet_redundant_step | flat | 10067 | 733 | 1 | 1.0 | 1.0 | 549.0 |
| agentnet_redundant_step | fixed_session | 10067 | 733 | 549 | 3.389 | 0.2615 | 1.0 |
| agentnet_redundant_step | operation_stack | 10067 | 733 | 260 | 6.202 | 0.3013 | 8.0 |
| agentnet_redundant_step | label_drilldown | 10067 | 733 | 253 | 13.734 | 0.0371 | 36.6 |
| osworld_group_start | flat | 4011 | 764 | 1 | 1.0 | 1.0 | 320.0 |
| osworld_group_start | fixed_session | 4011 | 764 | 320 | 2.625 | 0.3007 | 1.0 |
| osworld_group_start | operation_stack | 4011 | 764 | 173 | 5.25 | 0.2837 | 2.4 |
| osworld_group_start | label_drilldown | 4011 | 764 | 65 | 5.25 | 0.1025 | 53.2 |

## Claim Scope

- Supports: operation-stack views can make existing labeled problems more inspectable than flat summaries, while avoiding fixed-session fragmentation.
- Does not support: human productivity improvement, unsupervised intent discovery, or online anomaly detection without labels/proxies.
