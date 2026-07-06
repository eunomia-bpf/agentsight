# R376 Three-Plus-One Paper Gate

Status: `pass`
Checks: 13/13

E1-E3 are the scientific profiling experiments; E4 is replayability/artifact evidence and must not be used as hidden-label accuracy evidence.

## Checks

| Check | Passed | Detail |
|---|---:|---|
| upstream_gates_pass | True | R374=pass; R375=pass |
| english_three_plus_one | True | English paper names three empirical profiling experiments plus one artifact/reproducibility block. |
| chinese_three_plus_one | True | Chinese paper names three empirical profiling experiments plus one artifact/reproducibility block. |
| main_tables_are_paper_blocks | True | Main result tables label rows as paper blocks rather than homogeneous fourth-experiment framing. |
| role_and_claim_tables_are_paper_blocks | True | R374/R375 generated tables use paper-block terminology and label RQ4 as artifact replayability. |
| role_and_claim_json_contracts_are_paper_blocks | True | R374/R375 generated JSON contracts use paper-block keys rather than legacy homogeneous-experiment keys. |
| r375_r374_source_hash_is_fresh | True | R375 provenance records the current R374 report hash, preventing stale three-plus-one claim tables. |
| no_four_core_research_question_framing | True | Current paper text avoids framing E4 as a fourth core empirical experiment. |
| evaluation_top_map_uses_three_plus_one | True | Evaluation ledger top map records the 3+1 structure. |
| evaluation_has_no_stale_four_core_framing | True | No stale homogeneous-experiment ledger terms remain; present=none |
| chinese_user_doc_deemphasizes_flamegraph | True | Chinese user doc no longer frames novelty as flamegraph-only. |
| no_new_data_or_profiler_rerun | True | R376 reads only paper text and existing guardrails; upstream gates did not sync data or rerun the profiler. |
| source_status_tracked | True | All R376 sources are tracked or dirty in this intentional edit. |
