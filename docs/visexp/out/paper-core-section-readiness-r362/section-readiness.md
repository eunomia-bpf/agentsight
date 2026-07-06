# R362 Paper Core Section Readiness

- Status: `pass`.
- Checks: 16/16.
- This is a paper-structure gate, not a new empirical result.

## Section Token Matrix

| Experiment | Language | Status | Missing tokens |
|---|---|---|---|
| E1 | zh | pass |  |
| E1 | en | pass |  |
| E2 | zh | pass |  |
| E2 | en | pass |  |
| E3 | zh | pass |  |
| E3 | en | pass |  |
| E4 | zh | pass |  |
| E4 | en | pass |  |

## Checks

| Check | Status | Evidence |
|---|---|---|
| `r361_core_claim_ledger_is_current_and_passing` | pass | R361 has 4 ledger rows and 10/10 checks passing. |
| `both_papers_have_e1_e4_sections` | pass | Chinese and English papers both expose E1-E4 result subsections. |
| `zh_e1_claim_oracle_baseline_metric_scope_tokens` | pass | zh E1 has all section-readiness tokens. |
| `en_e1_claim_oracle_baseline_metric_scope_tokens` | pass | en E1 has all section-readiness tokens. |
| `zh_e2_claim_oracle_baseline_metric_scope_tokens` | pass | zh E2 has all section-readiness tokens. |
| `en_e2_claim_oracle_baseline_metric_scope_tokens` | pass | en E2 has all section-readiness tokens. |
| `zh_e3_claim_oracle_baseline_metric_scope_tokens` | pass | zh E3 has all section-readiness tokens. |
| `en_e3_claim_oracle_baseline_metric_scope_tokens` | pass | en E3 has all section-readiness tokens. |
| `zh_e4_claim_oracle_baseline_metric_scope_tokens` | pass | zh E4 has all section-readiness tokens. |
| `en_e4_claim_oracle_baseline_metric_scope_tokens` | pass | en E4 has all section-readiness tokens. |
| `e1_r361_claim_wording_visible_in_papers` | pass | E1 ledger labels are visible in paper/evaluation text. |
| `e2_r361_claim_wording_visible_in_papers` | pass | E2 ledger labels are visible in paper/evaluation text. |
| `e3_r361_claim_wording_visible_in_papers` | pass | E3 ledger labels are visible in paper/evaluation text. |
| `e4_r361_claim_wording_visible_in_papers` | pass | E4 ledger labels are visible in paper/evaluation text. |
| `must_not_claim_scope_visible` | pass | The combined paper text keeps human/productivity, automatic, complete compatibility, live overhead, and metric-dominance guardrails visible. |
| `two_abstraction_boundary_visible` | pass | The papers describe prompt/session/tool/process/syscall concepts as operation fields or forms, not profiler objects. |
