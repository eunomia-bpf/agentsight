# R347 Case-Level Baseline Contrast

R347 compares top-ranked visible case groups across operation-stack, fixed-session, flat, dataset-native, and raw-action views on the same labeled operations.

## Summary

- Overall: pass.
- Tasks / datasets / visible views: 6 / 4 / 5.
- Operation-stack top-5 positives: 6/6; top-1 positives: 5/6.
- Operation-stack median top-5 recall / lift / work: 0.1880 / 1.6508 / 0.0937.
- Wins vs flat top-5 work: 6/6.
- Wins vs fixed-session top-5 recall / group count: 5/6 / 4/6.
- Tasks with explicit counterpoints: 6/6.

## Task Cards

| Task | OS recall | OS work | Fixed recall | Best recall policy | Best first-positive policy | Counterpoints |
|---|---:|---:|---:|---|---|---|
| agentnet_incorrect_step | 0.0034 | 0.0014 | 0.0126 | flat:width | operation_stack:query_aware | top5_recall->flat:width |
| agentnet_redundant_step | 0.0177 | 0.0089 | 0.0123 | flat:width | fixed_session:query_aware | top5_recall->flat:width; first_positive->fixed_session:query_aware |
| agentreward_looping | 0.6508 | 0.4938 | 0.2381 | flat:width | raw_action_stack:query_aware | top5_recall->flat:width; first_positive->raw_action_stack:query_aware |
| agentreward_side_effect | 0.1139 | 0.1454 | 0.0000 | flat:width | operation_stack:query_aware | top5_recall->flat:width; top5_lift->raw_action_stack:query_aware |
| osworld_group_start | 0.3874 | 0.4074 | 0.0340 | flat:width | fixed_session:query_aware | top5_recall->flat:width; top5_lift->fixed_session:query_aware; first_positive->fixed_session:query_aware |
| satraj_unsafe | 0.2621 | 0.0420 | 0.0579 | flat:width | fixed_session:query_aware | top5_recall->flat:width; first_positive->fixed_session:query_aware |

## Claim Scope

- Supports: case-level baseline tradeoff evidence over real labeled traces.
- Narrows: operation-stack is not the best view for every objective or task.
- Excludes: human productivity, automatic boundary discovery, ecosystem compatibility, and universal selector claims.
