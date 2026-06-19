# R246 Post-Review Hygiene Gate

Run ID: `R246`
Status: `post_review_hygiene_passed`
Generated at: `2026-06-19T09:23:30.049876+00:00`
Source command: `python3 docs/visexp/r246_post_review_hygiene.py`

## Verdict

The post-R245 OSDI review keeps the project at Level 3 mechanism evidence, not weak accept.
The blocking evidence gaps are unchanged: C5 has no real participant responses and C6 has no real human adequacy labels.
R246 records only author-side hygiene fixes for provenance and run identity.

## Must Fix Before Weak Accept

- Collect and score real R142/R151 developer-task responses for C5.
- Collect and score blinded R124 human tag-adequacy labels for C6.

## Author Response

- Record R170 as dirty-provenance mechanism evidence rather than a clean release artifact.
- Align the paper's R170 command with the committed R170 source command.
- Clarify that R224 is a paper-level rerun of the R131 semantic-axis checker over the R170 denominator.
- Keep all C5/C6/weak-accept gates false until real human data exists.

## Mechanical Checks

| Check | Passed | Observed |
|-------|--------|----------|
| `c5_real_participants_still_absent` | `True` | `{"r195_c5_supported": false, "user_task_c5_supported": false, "user_task_participant_count": 0, "user_task_status": "participant_results_empty"}` |
| `c6_human_labels_still_absent` | `True` | `{"r124_adequacy_supported": false, "r124_final_label_count": 0, "r124_status": "human_labels_empty", "r195_c6_adequacy_supported": false}` |
| `weak_accept_still_not_supported` | `True` | `{"r195_weak_accept_supported": null, "r245_weak_accept_supported": false}` |
| `r170_source_command_matches_paper` | `True` | `{"paper_has_exact_command": true, "r170_source_command": "cargo run --manifest-path agentflame/Cargo.toml -- run --project-root . --scan-files 10000 --max-sessions 10000 --llama-url http://127.0.0.1:18080 --model local-r170 --timeout 60 --out .agentsight/agentflame/r170-full-current"}` |
| `r170_dirty_provenance_acknowledged` | `True` | `{"docs_mention_dirty_provenance": true, "docs_mention_repo_dirty_true": true, "r170_repo_dirty": true}` |
| `r224_metadata_clarifies_rerun_identity` | `True` | `{"results_mentions_checker_id": true, "results_mentions_metadata": true, "source_run_id": "R131"}` |
| `r246_recorded_in_main_evidence_docs` | `True` | `{"claim_verdict": true, "experiment_audit": true, "experiment_tracker": true, "followup_plan": true, "results_summary": true}` |
| `r170_dirty_caveat_reaches_verdict_and_audit` | `True` | `{"audit_mentions_repo_dirty_true": true, "verdict_mentions_repo_dirty_true": true}` |
| `tracker_records_r246_gate` | `True` | `{"tracker_has_no_outcome_boundary": true, "tracker_has_r246_row": true}` |

## Claim Gate

- weak_accept_supported: `False`
- c5_supported: `False`
- c6_adequacy_supported: `False`
- broad_c4_supported: `False`
- outcome_evidence_added: `False`
