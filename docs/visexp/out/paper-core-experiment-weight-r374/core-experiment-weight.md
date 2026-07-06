# R374 Core-Experiment Weight Gate

Status: `pass`
Checks: 12/12

R374 is a paper-organization gate. It assigns every main result to one of four core experiments and downgrades non-primary R-runs to support, presentation, guardrail, or future-protocol roles.

## Checks

| Check | Passed | Detail |
|---|---:|---|
| upstream_organization_gates_pass | True | R370=pass; R371=pass; R372=pass; R373=pass |
| exactly_four_weighted_core_experiments | True | rows=4 |
| each_core_has_primary_anchor | True | Every RQ has a named primary anchor and supporting evidence. |
| primary_anchors_are_substantial | True | Primary anchors include operation scale, hidden positives, and replay invocations. |
| support_runs_are_downgraded_to_roles | True | Non-primary R-runs are assigned support, presentation, guardrail, or future-protocol roles. |
| fidelity_actionability_tradeoff_covered | True | The role map covers fidelity/work, fragmentation, and actionability mechanisms. |
| non_claims_preserved | True | Human utility, automatic-boundary, metric-dominance, and ecosystem-compatibility limits remain explicit. |
| paper_mentions_r374 | True | Both papers and the evaluation ledger mention the core-experiment weight gate. |
| paper_has_role_table | True | Both papers include the R374 primary/support/guardrail role table. |
| evaluation_records_three_plus_one | True | The evaluation ledger records the three-empirical-plus-one-systems organization. |
| no_new_data_or_profiler_rerun | True | R374 reads tracked artifacts and paper text only; it does not sync data, relabel traces, or invoke agentpprof. |
| source_status_tracked | True | All R374 sources and generated role tables are tracked or staged as intent-to-add. |

## Role Map

| Core experiment | Primary anchor | Non-claim |
|---|---|---|
| RQ1/E1: generality and recursive folding | One operation layer over 47,590 operations, recursive stack-depth sweep, profile-spec override, standard-trace round trip, and field derivation (sources: R286/R290/R342/R353/R366). | Not complete trace-ecosystem compatibility and not automatic discovery of every latent intent boundary. |
| RQ2/E2: hidden-label localization and ranking | Hidden-label localization benchmark over six real labeled tasks, 34,539 operations, 3,699 positives, and 144 policies, scored only after profiling (source: R320). | Not metric dominance, not human or agent analyst productivity, and not superiority over imported ecosystem traces. |
| RQ3/E3: mechanism and actionability | Rank-feature mechanisms, feature ablations, executable profile-spec patches, boundary-field repair, and field-derivation mechanism audit (sources: R324/R325/R354/R358/R366). | Not an automatic patch selector, label-free universal selector, or automatic boundary detector. |
| RQ4/E4: replayability, offline cost, and artifact hygiene | Profile-spec replay over 76 tracked specs executed twice, 152 invocations, deterministic semantic/raw-byte outputs, median 1.601s and p95 2.767s per spec (sources: R327/R328). | Not hidden-label accuracy evidence, not live eBPF overhead, not human utility, and not complete ecosystem compatibility. |
