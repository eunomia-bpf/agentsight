# R377 Main Profiling-Claim Evidence Gate

Status: `pass`
Checks: 12/12
Paper-facing organization: 3 empirical profiling experiments + 1 artifact/reproducibility block.

The current paper can claim faithful hidden-label profiler localization/ranking with less flat inspection work, a better fixed-session fragmentation tradeoff, and actionable configuration insight. These are evidence facets inside the three empirical profiling experiments, not separate experiments, and they preserve non-dominance and non-human-utility scope.

## Claim Elements

| Claim element | Paper block | Evidence | Counterpoint |
|---|---|---|---|
| Faithful hidden-label localization and ranking | RQ2/E2 | R320 scores 144 policies over 6 tasks, 4 datasets, 34,539 operations, and 3,699 positives using precision@k, recall@budget, F1, AP/AUPRC-style score, nDCG, work-to-first-positive, and group metrics. | Flat and dataset-native views still win broad-recall or some nDCG/top-k objectives; the claim is a Pareto tradeoff, not metric dominance. |
| Less inspection work than flat summaries | RQ2/E2 | R333/R334 show top-5 operation work improves over flat on 6/6 tasks with median ratio 0.0937; budget-30 recall improves on 6/6 tasks; work-to-first-positive improves on 6/6 tasks. | Flat summaries retain full-recall behavior only by forcing inspection of the whole task. |
| Less fragmentation than fixed-session drilldown proxy | RQ2/E2 | R334 reports fewer groups than fixed-session on 4/6 tasks (median ratio 0.5543) and fewer groups-to-50%-recall on 5/6 tasks. R355 extends this below session scope: budget-30 positive-unit recall improves on 20/24 task-depth rows and groups-to-50%-positive-units improves on 22/24. | Fixed-session still wins top-5 work on 4/6 tasks and often finds the first positive earlier, so it remains a drilldown baseline. |
| Actionable optimization insight | RQ3/E3 | R354 accepts profile-guided patches on 5/6 tasks, with median AP delta 0.0376 and top-5 lift delta 0.575. R358 repairs the OSWorld-Human rejection with boundary-derived fields: AP 0.2583 vs 0.2402 and groups 74 vs 108. R366 identifies 7 critical and 3 misleading rank-feature rows. | Boundary-derived fields improve AP and reduce groups, but they increase top-5 operation work and first-positive work on this held-out subset. |
| Mechanism isolation and two-abstraction boundary | RQ1/E1 + RQ3/E3 | R366 passes 6/6 mechanism checks: mapping, tagging/rank features, profile specs, and supervised boundary backends write operation fields that operation stacks fold. R375/R376 keep E4 out of hidden-label accuracy evidence and preserve the operation / operation-stack abstraction boundary. | Boundary backends beat simple baselines on 4/5 rows, but AgentRewardBench looping is explained by repeat_signal_change. |

## Checks

| Check | Passed | Detail |
|---|---:|---|
| real_labeled_trace_scale_preserved | True | R320 totals={'datasets': 4, 'group_views': 36, 'policy_scores': 144, 'positive_operations': 3699, 'task_operations': 34539, 'tasks': 6} |
| fidelity_metric_surface_present | True | R320 records the profiler-paper metric surface. |
| flat_work_claim_supported | True | Top-5 work, budget-30 recall, and work-to-first-positive all improve over flat on 6/6 tasks. |
| fixed_session_tradeoff_not_dominance | True | Operation stacks improve fragmentation/localization metrics while preserving fixed-session work counterpoints. |
| actionability_claim_supported | True | Executable patches, boundary-field repair, and rank-feature ablations support actionability. |
| mechanism_isolation_supported | True | R366 isolates mapping/ranking/boundary mechanisms, and R375/R376 preserve claim scope. |
| paper_mentions_r377 | True | Both papers and the evaluation ledger mention the R377 main-claim evidence packet. |
| claim_elements_not_extra_experiments | True | The five R377 claim elements are paper-routing facets inside E1-E3, not additional experiments. |
| non_claims_preserved | True | The evidence packet keeps human utility, automatic detection/selection, metric dominance, and ecosystem compatibility out of scope. |
| no_new_data_or_profiler_rerun | True | R377 reads tracked artifacts and paper text only; it does not sync data, relabel traces, or invoke agentpprof. |
| english_submodule_input_committed | True | The English paper input must be clean inside docs/agentpprof-paper, and the parent index must point at the same submodule commit before R377 reports pass. |
| source_status_tracked | True | All R377 sources are tracked or intentionally dirty/staged. |
