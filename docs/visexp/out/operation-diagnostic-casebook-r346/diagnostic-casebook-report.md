# R346 Diagnostic Casebook

R346 links visible top-ranked operation-stack groups to hidden-label scoring, diagnostic lenses, optimization actions, and counterpoints without fetching or relabeling datasets.

## Summary

- Overall: pass.
- Tasks / datasets: 6 / 4.
- Case groups: 30.
- Top-1 positive tasks: 5/6.
- Top-5 positive tasks: 6/6.
- Median top-5 recall / precision / work: 0.1880 / 0.1991 / 0.0937.
- Actionable case cards: 6/6.

## Task Cards

| Task | Dataset | Top-5 recall | Top-5 precision | Work | First-positive work | Best views | Optimization action |
|---|---|---:|---:|---:|---:|---|---|
| agentreward_looping | agent-reward-bench | 0.6508 | 0.9111 | 0.4938 | 0.2058 | dataset_native; flat; operation_stack; raw_action_stack | Keep repeat_signal in the stack, but add prevalence-aware ranking because looping positives are common. |
| agentreward_side_effect | agent-reward-bench | 0.1139 | 0.2170 | 0.1454 | 0.0645 | fixed_session; flat; operation_stack | Increase weight on write/input actions or use a deeper side-effect mapping before ranking. |
| satraj_unsafe | satraj-os-safety | 0.2621 | 0.9056 | 0.0420 | 0.0112 | dataset_native; fixed_session; flat; operation_stack | Use environment + phase + action stack fields; prioritize risky environments and write actions. |
| agentnet_incorrect_step | agentnet | 0.0034 | 0.1429 | 0.0014 | 0.0007 | flat; operation_stack; raw_action_stack | Use desktop environment + phase + repeat/action fields, then drill into fixed sessions for examples. |
| agentnet_redundant_step | agentnet | 0.0177 | 0.1444 | 0.0089 | 0.0051 | flat; operation_stack; raw_action_stack | Use desktop environment + phase + repeat/action fields, then drill into fixed sessions for examples. |
| osworld_group_start | osworld-human | 0.3874 | 0.1812 | 0.4074 | 0.1311 | dataset_native; fixed_session; flat; operation_stack | Use group-depth or boundary-derived fields for higher recall; action-depth alone fragments starts. |

## Claim Scope

- Supports: concrete label-scored case evidence for profiler localization and actionability.
- Narrows: automated case evidence, not a human analyst study.
- Excludes: automatic universal selector, complete boundary discovery, and trace-ecosystem compatibility.
