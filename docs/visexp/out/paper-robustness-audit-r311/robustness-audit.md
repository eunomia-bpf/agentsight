# Paper Robustness Audit R311

R311 reads existing tracked artifacts only. It does not sync datasets, rerun profilers, or add abstractions.

## Headline

- Abstractions: operation, operation stack.
- Workload: 4 datasets / 6 tasks / 34539 operations / 3699 positives.
- Operation-stack vs flat: more selective 6/6; positive group 6/6; high-lift 5/6.
- Operation-stack vs fixed-session: higher selected recall 5/6; lower selected work 2/6; fixed-session lower-work counterpoint 4/6.
- Guardrail: Counts are task-level robustness checks over six oracle-backed tasks, not a statistical generalization claim.

## Reviewer Stress Tests

| Question | Verdict | Evidence | Paper wording |
|---|---|---|---|
| Is this only a flat trace or prompt/session flamegraph? | pass | R310 keeps exactly two profiler abstractions: operation and operation stack; C1/C2 support arbitrary stack fields and recursive depth under scoped wording; +1 more | Claim a two-abstraction profiler model with stack specs, not a prompt/session/span hierarchy. |
| Does the operation-stack view add value over flat packets? | pass | operation-stack packets are more selective than flat on 6/6 tasks; positive groups appear in 6/6 tasks; +1 more | Claim inspectability over flat summaries under oracle-backed proxy tasks. |
| Does the operation-stack view universally dominate fixed-session drilldown? | narrow | selected recall is higher than fixed-session on 5/6 tasks; selected work is lower than fixed-session on only 2/6 tasks; +1 more | Claim a recall/selectivity tradeoff, not universal dominance. |
| Is query-aware analysis just oracle leakage? | pass_with_scope | R302 rankers exclude hidden oracle fields; top-10 query-aware operation-stack work/lift 0.1163/1.5867 vs width 0.6713/1.0795; +1 more | Use as configurable analysis-policy evidence, not automatic anomaly detection. |
| Does the evidence prove human/agent analyst utility? | fail_for_stronger_claim | R308/R309 are automated replays over hidden labels; no analyst timing, accuracy, or workload study has been run; +1 more | Claim automated inspectability proxy value only. |
| Is boundary discovery solved? | partial | R310 keeps C3 partial; R299 shows family-specific calibration and simple-baseline counterexamples; +1 more | Frame boundary backends as extension points that derive stackable fields. |
| Is the novelty only the flamegraph visualization? | pass | R302 ranking policies, R305 cross-view case packets, R308 first-evidence outcomes, and R309 problem cards are non-flamegraph analyses over the same stacks; R310 evidence matrix and this R311 stress audit are paper-facing analyses, not profiler abstractions | State novelty as query-time recursive operation stacks plus auditable non-flamegraph analyses. |

## Task Robustness

| Task | Dataset | Support | Operation-stack work/recall/lift | Counterpoints |
|---|---|---|---|---|
| agentnet_incorrect_step | agentnet | scoped_proxy_support | 0.0014 / 0.0034 / 2.406 | low_selected_positive_recall |
| agentnet_redundant_step | agentnet | strong_proxy_support | 0.0089 / 0.0177 / 1.984 | fixed_session_uses_less_selected_work; fixed_session_reaches_first_positive_earlier; +1 more |
| agentreward_looping | agent-reward-bench | scoped_proxy_support | 0.4938 / 0.6508 / 1.318 | fixed_session_uses_less_selected_work; fixed_session_reaches_first_positive_earlier; +1 more |
| agentreward_side_effect | agent-reward-bench | scoped_proxy_support | 0.1454 / 0.1139 / 0.7831 | top5_packet_lift_below_prevalence |
| osworld_group_start | osworld-human | scoped_proxy_support | 0.4074 / 0.3874 / 0.951 | fixed_session_uses_less_selected_work; fixed_session_reaches_first_positive_earlier; +1 more |
| satraj_unsafe | satraj-os-safety | strong_proxy_support | 0.042 / 0.2621 / 6.238 | fixed_session_uses_less_selected_work; fixed_session_reaches_first_positive_earlier |

## Must Not Claim

- Every public agent trajectory dataset can be profiled at full scale without additional engineering.
- R296 reviewer packet is itself empirical evidence
- R297 generalizes beyond OSWorld-Human
- R300-R305 prove human productivity
- R306 proves full OpenTelemetry/Chrome ecosystem compatibility
- The profiler fully discovers latent intent boundaries without labels or rules.
- The profiler improves human developer productivity.
- automatic anomaly detection
- case packets are a new profiler abstraction
- complete trace ecosystem compatibility
- human accuracy or time improvement
- universal dominance over fixed-session baselines
- unsupervised intent discovery
