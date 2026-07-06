# R350 Evidence-Packet Budget Audit

R350 checks whether existing profiler outputs form bounded diagnostic packets
over real labeled agent traces. Each packet joins top-ranked operation-stack
evidence, baseline counterpoints, action counterfactuals, and a held-out
transfer guardrail. Hidden labels are used only through already-scored
artifacts, not to rank deployment-time traces.

## Summary

- Overall: pass.
- Tasks / datasets / objective rows: 6 / 4 / 36.
- Top-5 operation-stack packets contain positives on 6/6 tasks; top-1 contains positives on 5/6.
- Strict 30% operation-work budget holds on 4/6 tasks; first-positive <=10% work holds on 4/6.
- Median top-5 work / recall / lift: 0.0937 / 0.1880 / 1.6508.
- Operation-stack beats flat top-5 work on 6/6 tasks and has fewer groups than fixed-session on 4/6 tasks.
- Non-default visible action rows: 27/36; median non-default gain over default: 0.6188.
- Held-out action transfer is partial: 35/60 within tolerance and 7/60 exact action.

## Task Packets

| Task | Verdict | Top-5 work | Top-5 recall | First-positive work | Non-default rows | Counterpoints |
|---|---|---:|---:|---:|---:|---|
| agentnet_incorrect_step | bounded_30pct_packet | 0.0014 | 0.0034 | 0.0007 | 3 | top5_recall->flat:width |
| agentnet_redundant_step | bounded_30pct_packet | 0.0089 | 0.0177 | 0.0051 | 4 | top5_recall->flat:width; first_positive->fixed_session:query_aware |
| agentreward_looping | actionable_budget_exception | 0.4938 | 0.6508 | 0.2058 | 4 | top5_recall->flat:width; first_positive->raw_action_stack:query_aware |
| agentreward_side_effect | bounded_30pct_packet | 0.1454 | 0.1139 | 0.0645 | 5 | top5_recall->flat:width; top5_lift->raw_action_stack:query_aware |
| osworld_group_start | actionable_budget_exception | 0.4074 | 0.3874 | 0.1311 | 6 | top5_recall->flat:width; top5_lift->fixed_session:query_aware; first_positive->fixed_session:query_aware |
| satraj_unsafe | bounded_30pct_packet | 0.0420 | 0.2621 | 0.0112 | 5 | top5_recall->flat:width; first_positive->fixed_session:query_aware |

## Claim Scope

- Supports: operation/operation-stack profiler output can localize positives, expose counterpoints, and identify actionable knobs under bounded inspection budgets on real labeled traces.
- Narrows: two tasks exceed the strict 30% work budget, and held-out action transfer is only a partial proxy.
- Excludes: human utility, label-free universal action selection, complete intent-boundary recovery, and complete trace-ecosystem compatibility.
