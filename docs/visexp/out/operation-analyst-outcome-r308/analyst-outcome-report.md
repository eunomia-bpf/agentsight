# R308 Analyst Outcome Proxy

R308 scores analyst-outcome proxies on the R305 label-hidden packets. Operation-stack packets contain a positive group in 6/6 tasks and a >=1.5x high-lift group in 5/6 tasks. Fixed-session packets reach 5/6 and 4/6; flat packets reach 6/6 and 0/6. Operation stacks keep median selected work at 9.4% with recall 18.8% and top-group lift 1.574.

## View Summary

| View | Positive tasks | High-lift tasks | First-positive work | Top-group lift | Work | Recall | Precision |
|---|---:|---:|---:|---:|---:|---:|---:|
| flat | 6/6 | 0/6 | 1.0 | 1.0 | 1.0 | 1.0 | 0.1678 |
| fixed_session | 5/6 | 4/6 | 0.0037 | 1.2514 | 0.0163 | 0.0226 | 0.2482 |
| operation_stack | 6/6 | 5/6 | 0.0379 | 1.5739 | 0.0937 | 0.188 | 0.1991 |

## Task-View Outcomes

| Task | View | Top lift | First positive work | High-lift rank | Work | Recall | Precision |
|---|---|---:|---:|---:|---:|---:|---:|
| agentreward_looping | flat | 1.0 | 1.0 | n/a | 1.0 | 1.0 | 0.6914 |
| agentreward_looping | fixed_session | 1.4464 | 0.0412 | n/a | 0.2058 | 0.2381 | 0.8 |
| agentreward_looping | operation_stack | 1.3114 | 0.2058 | n/a | 0.4938 | 0.6508 | 0.9111 |
| agentreward_side_effect | flat | 1.0 | 1.0 | n/a | 1.0 | 1.0 | 0.2771 |
| agentreward_side_effect | fixed_session | 0.0 | n/a | n/a | 0.1948 | 0.0 | 0.0 |
| agentreward_side_effect | operation_stack | 0.9982 | 0.0645 | 3 | 0.1454 | 0.1139 | 0.217 |
| satraj_unsafe | flat | 1.0 | 1.0 | n/a | 1.0 | 1.0 | 0.1452 |
| satraj_unsafe | fixed_session | 6.8891 | 0.0037 | 1 | 0.0154 | 0.0579 | 0.5455 |
| satraj_unsafe | operation_stack | 6.8891 | 0.0112 | 1 | 0.042 | 0.2621 | 0.9056 |
| agentnet_incorrect_step | flat | 1.0 | 1.0 | n/a | 1.0 | 1.0 | 0.0594 |
| agentnet_incorrect_step | fixed_session | 0.0 | 0.0017 | 2 | 0.0056 | 0.0126 | 0.1341 |
| agentnet_incorrect_step | operation_stack | 0.0 | 0.0007 | 3 | 0.0014 | 0.0034 | 0.1429 |
| agentnet_redundant_step | flat | 1.0 | 1.0 | n/a | 1.0 | 1.0 | 0.0728 |
| agentnet_redundant_step | fixed_session | 1.0565 | 0.0013 | 2 | 0.0086 | 0.0123 | 0.1034 |
| agentnet_redundant_step | operation_stack | 1.8851 | 0.0051 | 1 | 0.0089 | 0.0177 | 0.1444 |
| osworld_group_start | flat | 1.0 | 1.0 | n/a | 1.0 | 1.0 | 0.1905 |
| osworld_group_start | fixed_session | 2.3625 | 0.005 | 1 | 0.0172 | 0.0327 | 0.3623 |
| osworld_group_start | operation_stack | 1.8365 | 0.1311 | 1 | 0.4074 | 0.3874 | 0.1812 |

## Claim Scope

- Supports: operation-stack packets expose early positive and high-lift evidence on existing labeled analyst tasks while staying much more selective than flat packets.
- Narrows: fixed-session packets remain cheaper on some first-positive work metrics, so operation stacks are a configurable inspectability tradeoff rather than a universal winner.
- Does not support: human analyst accuracy/time improvement, automatic anomaly detection, or dominance over every baseline on every metric.

## Source Artifacts

- `r305_report`: `docs/visexp/out/operation-case-baseline-r305/case-baseline-report.json`
- `r305_visible_packet`: `docs/visexp/out/operation-case-baseline-r305/visible-case-packets.json`
- `r305_answer_key`: `docs/visexp/out/operation-case-baseline-r305/answer-key.json`
