# Paper Real-Problem Narrative R317

R317 is a synthesis over existing labeled-agent-trajectory artifacts. It is not a new empirical run, not a human or agent study, and not a detector.

## Claim-First Takeaways

- Across 6 oracle-backed tasks from 4 datasets, operation stacks are a paper-ready inspectability surface rather than a single winning hierarchy: they are on the non-oracle Pareto frontier for 6/6 tasks, while flat and fixed-session also remain frontier counterpoints.
- The real-problem value is strongest for safety and step-quality triage: 5/6 tasks show higher selected recall than fixed-session, and 5/6 contain a high-lift operation-stack group under the hidden-key packet policy.
- The main counterpoint is also stable: operation stacks are lower-work than fixed-session on only 2/6 tasks, so the paper must claim a configurable tradeoff surface, not baseline dominance.
- The R316 assignment readout checks that the controlled-study instrument can recover the same tradeoff before running analysts: top-3 operation-stack positive/high-lift hit rates are 1.0/0.8333, versus 0.8333/0.6667 for fixed-session and 1.0/0.0 for flat.

## Task Narrative Matrix

| Task | Dataset | Value | Evidence pattern | OS work | OS recall | OS lift | Counterpoint |
|---|---|---|---|---:|---:|---:|---|
| agentnet_incorrect_step | agentnet | needle-in-haystack step-quality debugging | high_lift_low_recall | 0.0014 | 0.0034 | 2.4057 | Use this as selective evidence, not as a complete incorrect-step detector. |
| agentnet_redundant_step | agentnet | human desktop redundancy diagnosis | high_lift_low_recall | 0.0089 | 0.0177 | 1.9838 | Fixed-session reaches the first positive earlier on this task, so the result is a recall/aggregation tradeoff. |
| agentreward_looping | agent-reward-bench | prevalent web-agent looping diagnosis | prevalent_positive_recall | 0.4938 | 0.6508 | 1.3179 | This is a prevalence and aggregation result, not enriched anomaly detection. |
| agentreward_side_effect | agent-reward-bench | side-effectful web-agent behavior triage | higher_recall_lower_work | 0.1454 | 0.1139 | 0.7831 | The top-5 packet lift falls below prevalence, so the paper should highlight query/ranker choice instead of a universal default. |
| osworld_group_start | osworld-human | human grouped-action boundary inspection | higher_recall_higher_work | 0.4074 | 0.3874 | 0.951 | The work cost is much larger than fixed-session, so this is a boundary-coverage tradeoff, not cheaper inspection. |
| satraj_unsafe | satraj-os-safety | desktop safety auditing | higher_recall_higher_work | 0.042 | 0.2621 | 6.2384 | Fixed-session still reaches the first positive at lower work, preserving it as a drilldown counterpoint. |

## Claim Boundary

Supports: mechanism, novelty, and automated inspectability narrative over existing artifacts.
Does not support: human accuracy, agent accuracy, time-to-answer, productivity, automatic detection, single-view dominance, or full trace-platform compatibility.
