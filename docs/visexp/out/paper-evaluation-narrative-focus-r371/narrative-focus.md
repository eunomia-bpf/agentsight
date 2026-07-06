# R371 Evaluation Narrative Focus

- Status: `pass`.
- Checks: 10/10.
- This is a paper-organization guardrail, not a new empirical result.

## Checks

| Check | Status | Evidence |
|---|---|---|
| `four_rq_sections_in_both_papers` | pass | zh=['RQ1/E1', 'RQ2/E2', 'RQ3/E3', 'RQ4/E4']; en=['RQ1/E1', 'RQ2/E2', 'RQ3/E3', 'RQ4/E4'] |
| `rq1_keeps_ranker_ablation_out_of_primary_folding_story` | pass | English RQ1 no longer lists E3 ranker/actionability probes as recursive-folding evidence. |
| `rq2_primary_result_precedes_supporting_robustness_runs` | pass | RQ2 leads with the hidden-label localization benchmark before robustness/counterpoint slices. |
| `rq3_mechanism_runs_precede_patch_case` | pass | RQ3 explains rank-feature/mapping mechanisms before executable patch and boundary repair cases. |
| `rq4_replay_cost_precedes_hygiene_gates` | pass | RQ4 now leads with replay/cost evidence before paper-hygiene audits. |
| `each_section_has_claim_counterpoint_nonclaim` | pass | Each RQ section exposes claim test, counterpoint language, and scoped non-claim language. |
| `r370_contract_still_passes` | pass | {"checks_passed": 10, "checks_total": 10, "core_experiments": 4} |
| `paper_uses_compact_role_map_not_r371_log` | pass | Chinese and English drafts use the compact R374 role map instead of exposing R371 as a main-body process log. |
| `evaluation_records_r371` | pass | Evaluation ledger records R371 as paper-organization hygiene. |
| `source_policy_no_new_data_or_profiler_rerun` | pass | R371 reads tracked paper/docs/artifacts only; it downloads no data and reruns no profiler. |

## Section Summary

| Paper | RQ | Chars | R-run mentions | Claim-test | Counterpoint | Non-claim |
|---|---|---:|---:|---|---|---|
| zh | RQ1/E1 | 7444 | 20 | True | True | True |
| zh | RQ2/E2 | 9668 | 39 | True | True | True |
| zh | RQ3/E3 | 4979 | 23 | True | True | True |
| zh | RQ4/E4 | 5061 | 21 | True | True | True |
| en | RQ1/E1 | 4467 | 4 | True | True | True |
| en | RQ2/E2 | 11633 | 40 | True | True | True |
| en | RQ3/E3 | 8047 | 21 | True | True | True |
| en | RQ4/E4 | 4920 | 18 | True | True | True |
