# R405 English Paper Experiment Gap Audit

This is a read-only audit over the English submodule draft and outer-repo evidence.
It is not a new empirical experiment and it does not edit the submodule.

- Status: pass
- Git commit: `e34079bcefa2e00b15cb82f324922ebed1870b7c`
- Rows: 8

## Claim/Gaps

| Area | Status | Claim or gap | Outer evidence | Next action |
| --- | --- | --- | --- | --- |
| Overall structure | gap_to_sync_when_english_edits_are_allowed | English draft still presents three RQs, while the outer paper/evaluation ledger uses three empirical profiling experiments plus one replayability/scope-control block. | docs/visexp/paper/main.tex and docs/evaluation.md contain RQ1/E1-RQ4/E4. | Do not edit the submodule now. When explicitly allowed, port the four-block structure from the Chinese paper into English. |
| Fidelity / localization | supported_by_outer_artifacts | Operation-stack groups localize dataset-provided hidden positives with less flat-summary inspection work and less fixed-session fragmentation. | R320/R344/R355/R368: 6 tasks, 34,539 operations, 3,699 positives; Work@5 0.0937 vs flat 1.0; median groups 157.5 vs fixed-session 285.0; metric counterpoints preserved. | Use as the main profiling-paper claim; keep flat/fixed-session counterpoints visible. |
| Actionability | supported_as_profile_configuration | Profiler output can guide profile-configuration changes: stack fields, rank features, mapping rules, depth, and boundary-derived fields. | R324/R325/R335/R340/R341/R345-R350/R354/R358/R366/R400 provide feature, patch, boundary, and suitability evidence; R354 has 5/6 accepted executable profile-spec patches. | Write actionability as configuration insight, not automatic patch selection or agent-driven diagnosis. |
| Intent recognition / taggers | must_remain_future_work | Direct regex-vs-embedding-vs-LLM tagger comparison on the same free-form prompts remains future work. | R366 supports deterministic/supervised field derivation and suitability checks, but not a completed same-prompt backend comparison. R405 scans 6 tracked operation JSONL sources / 67304 rows and finds 0 rows with both public free-form text and oracle semantic labels. | Do not claim LLM/regex/embedding tagger accuracy until a same-input evaluation exists. |
| Boundary detection | supported_only_with_scope | Current boundary evidence is supervised or deterministic field derivation, not automatic discovery of every latent intent boundary. | R297/R299/R355/R366/R400: OSWorld-Human and selected label families support scoped boundary fields; family suitability includes accept/caution/reject outcomes. | Keep 'automatic intent boundary discovery' out of the claim; require family-specific suitability. |
| Human utility | unsupported_non_claim | The evidence does not show improved human/agent analyst accuracy, time-to-answer, or productivity. | R315/R316 are protocol/sensitivity artifacts; docs/evaluation.md explicitly gates human-utility claims. | Only run an analyst study if the paper wants human utility claims. |
| Trace ecosystem compatibility | unsupported_non_claim | The project has standard-trace exchange smoke tests, but no complete compatibility claim for OpenTelemetry/Phoenix/LangSmith/Langfuse/Perfetto producer traces. | R306/R353 cover Chrome/Perfetto-style exchange containers and byte-identical replay on fixtures/prefixes; real producer imports remain pending. | Import one real producer trace before claiming ecosystem compatibility or span-tree superiority. |
| Two abstractions | supported_in_outer_paper | Outer Chinese paper now frames prompt/session/span/task as fields, containers, or baseline shapes over operations, not profiler objects. | Chinese paper abstract/design plus R394/R375 guardrails preserve operation and operation-stack as the only profiler abstractions. | When English edits are allowed, align terminology to operation/operation-stack and avoid extra abstract objects. |

## Checks

| Check | Passed | Detail |
| --- | --- | --- |
| english_submodule_read_only_scope | True | This script opens docs/agentpprof-paper/main.tex for reading only and writes outputs only under the outer docs/visexp/out tree. |
| three_empirical_plus_one_scope_detected | True | Outer Chinese paper/evaluation ledger expose the four reviewer-facing blocks. |
| english_three_rq_gap_detected | True | The English submodule draft remains behind the outer four-block organization. |
| main_claim_has_outer_evidence | True | R405 maps the core localization/work/fragmentation claim to tracked outer artifacts. |
| future_work_gaps_explicit | True | R405 lists tagger-comparison, human-utility, and ecosystem-compatibility gaps as non-claims or future work. |
| tagger_gap_has_no_current_free_text_oracle | True | Scanned 6 tracked operation JSONL sources and 67304 rows; 0 rows had public free-form text fields, 60305 rows had oracle fields, and 0 rows had both. |
| two_abstraction_boundary_preserved | True | R405 routes mappings, tags, predicates, rankers, and profile specs back to the two profiler abstractions. |

## Operation Text/Oracle Scan

| Source | Rows | Free-text rows | Oracle rows | Rows with both | Free-text fields | Oracle fields |
| --- | ---: | ---: | ---: | ---: | --- | --- |
| AgentNet operations | 16741 | 0 | 16741 | 0 | - | step_correct, step_redundant |
| AgentRewardBench operations | 729 | 0 | 729 | 0 | - | looping, side_effect |
| OSWorld-Human operations | 6010 | 0 | 4011 | 0 | - | group_pattern, group_position, human_group |
| SATraj-OS operations | 4285 | 0 | 4285 | 0 | - | attack_type, safety |
| ScaleCUA operations | 5000 | 0 | 0 | 0 | - | - |
| R300 query utility operations | 34539 | 0 | 34539 | 0 | - | attack_type, group_pattern, group_position, human_group, looping, problem_oracle, problem_value, safety, side_effect, step_correct, step_redundant, target_positive |
