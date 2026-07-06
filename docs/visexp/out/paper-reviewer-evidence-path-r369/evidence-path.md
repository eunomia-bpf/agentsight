# R369 Reviewer Evidence Path

- Status: `pass`.
- Checks: 9/9.
- This is a paper-integration guardrail, not a new empirical result.

## Evidence Path

| RQ | Claim test | Main paper evidence | Source artifact | Guardrail | Non-claim |
|---|---|---|---|---|---|
| RQ1/E1 | Two abstractions cover heterogeneous traces and recursive field-derived folding. | tab:results; RQ1/E1 subsection; dataset table. | R360/R361/R366: 47,590 operations; 9->3,757 stack sweep; 12/12 prompt/session-free specs; 4/5 boundary rows beat simple baseline. | R364 sufficiency; R359 RQ consolidation; R366 field-derivation scope. | Not complete trace-ecosystem compatibility, not automatic intent-boundary discovery. |
| RQ2/E2 | Hot groups localize hidden positives with less work than flat and less fragmentation than fixed-session drilldown. | tab:r320; fig:r363-portfolio; tab:r365-headlines; tab:r365-cases. | R320/R333/R334/R355/R368: 6 tasks, 34,539 ops, 3,699 positives, 144 policies; Work@5 0.0937 vs 1.0; groups 157.5 vs 285. | R368 fixed-session trace-tree-shaped baseline scope; R330/R331 uncertainty and negative controls. | Not metric dominance; not a human-productivity result; real OTel/Phoenix/LangSmith/Perfetto imports remain future baselines. |
| RQ3/E3 | Stack fields, mappings, rankers, profile specs, and boundary fields expose actionable optimization knobs. | fig:r363-portfolio; tab:r365-headlines; tab:r365-cases; RQ3/E3 subsection. | R354/R358/R365/R366: 5/6 accepted profile-spec patches; AP +0.0376 median; OSWorld AP 0.2583 vs 0.2402; 7 critical and 3 misleading feature rows. | R349 action-transfer counterpoint; R358 inspection-work counterpoint; R366 suitability/simple-baseline checks. | Not an automatic patch selector, automatic boundary detector, or universal default view. |
| RQ4/E4 | Tracked offline profile-spec path is replayable and cheap enough for artifact evaluation. | tab:results; RQ4/E4 subsection; artifact-hygiene paragraphs. | R327/R328/R352/R357/R361/R364: 76/76 semantic and raw-byte deterministic specs; 152 invocations; median 1.601s, p95 2.767s. | R352 OSDI rubric; R357 reviewer acceptance; R359-R368 claim/scope gates. | Not live eBPF overhead, not hidden-label accuracy, not human utility. |

## Checks

| Check | Status | Evidence |
|---|---|---|
| `four_rq_evidence_paths` | pass | Exactly one reviewer evidence-path row exists for each paper-facing RQ/core experiment. |
| `each_path_has_paper_artifact_guardrail_nonclaim` | pass | Each row records main paper evidence, source artifact, guardrail, and scoped non-claim. |
| `rq2_localization_path_complete` | pass | RQ2 links hidden-label localization numbers to the fixed-session baseline-scope guardrail. |
| `rq3_actionability_path_complete` | pass | RQ3 links executable patches, boundary-field repair, task cards, and mechanism counterpoints. |
| `paper_exposes_compact_role_map` | pass | Chinese and English papers expose the compact R374 role map instead of the old R369 run-ledger table. |
| `evaluation_mentions_r369` | pass | Evaluation ledger records R369 as a paper-integration guardrail. |
| `two_abstractions_and_must_not_claims_preserved` | pass | Evidence path preserves operation/operation-stack abstractions and must-not-claim boundaries. |
| `source_policy_no_new_data_or_profiler_rerun` | pass | R369 reads tracked paper/docs/artifacts only; it downloads no data and reruns no profiler. |
| `upstream_gates_pass` | pass | r360=pass; r361=pass; r363=pass; r365=pass; r368=pass |
