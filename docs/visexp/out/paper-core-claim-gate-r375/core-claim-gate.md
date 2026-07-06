# R375 Three-Plus-One Claim Gate

Status: `pass`
Checks: 11/11

R375 is a paper-integration gate. It converts three empirical profiling experiments plus one artifact/reproducibility block into explicit claim decisions and keeps broader wording as future expansion rather than paper claims.

## Checks

| Check | Passed | Detail |
|---|---:|---|
| upstream_claim_gates_pass | True | R361=pass; R364=pass; R370=pass; R373=pass; R374=pass |
| exactly_three_plus_one_claim_gate_rows | True | rows=4 |
| each_gate_has_decision_allowed_failure_forbidden | True | Each row has a decision, allowed claim, failure interpretation, must-not-claim boundary, and evidence sources. |
| profiling_metrics_and_baselines_preserved | True | The paper still carries the profiler metrics and the named baseline families. |
| actionability_mechanisms_preserved | True | R375 ties actionability to fields, mappings/tags, rankers, profile specs, and boundary-derived operation fields. |
| must_not_claims_preserved | True | Metric dominance, human utility/productivity, automatic-boundary, and ecosystem-compatibility limits remain explicit. |
| paper_mentions_r375_claim_gate | True | Both papers and the evaluation ledger mention the R375 claim gate. |
| paper_summarizes_claim_gate_decisions | True | Both papers summarize the R375 decisions while the full table stays in the artifact ledger. |
| evaluation_records_claim_gate_role | True | The evaluation ledger records that R375 converts E1-E4 into scoped claim decisions. |
| no_new_data_or_profiler_rerun | True | R375 reads tracked artifacts and paper text only; it does not sync data, relabel traces, or invoke agentpprof. |
| source_status_tracked | True | All R375 sources and generated claim-gate tables are tracked or staged as intent-to-add. |

## Claim Gates

| Paper block | Gate decision | Allowed claim | Must not claim |
|---|---|---|---|
| RQ1/E1: generality and recursive folding | Supported with scoped limits. | A two-object model covers heterogeneous public labeled traces, and mappings/tags derive operation fields before query-time recursive stack folding. | Complete trace-ecosystem compatibility; automatic discovery of every latent intent boundary. |
| RQ2/E2: hidden-label localization and ranking | Supported as a hidden-label profiler benchmark. | Operation-stack profiling localizes dataset-provided positives with less inspection work than flat summaries and a better median-fragmentation tradeoff than fixed-session drilldown proxy. | Metric dominance; human or agent analyst productivity; superiority over imported OpenTelemetry/Phoenix/LangSmith/Langfuse/Perfetto traces. |
| RQ3/E3: mechanism and actionability | Supported as profile-configuration actionability. | Stack fields, mapping/tagging rules, rankers, profile specs, and boundary-derived fields expose actionable configuration knobs and explain task-specific wins and failures. | Automatic patch selection; label-free universal view/ranker selection; automatic boundary detection. |
| RQ4/E4: artifact replayability, offline cost, and hygiene | Supported as offline artifact replayability. | Tracked profile specs replay deterministically over tracked operation inputs at low local cost, and paper guardrails keep evidence, wording, and non-claims aligned. | Live eBPF overhead; hidden-label accuracy evidence; human utility; complete ecosystem compatibility. |
