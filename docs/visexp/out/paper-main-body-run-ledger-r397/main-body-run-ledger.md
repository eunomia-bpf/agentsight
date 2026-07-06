# R397 Main-Body Run-Ledger Suppression Gate

Status: `pass`
Checks: 13/13
Main-paper run-id hits: 0
Main-paper internal-style hits: 0
Chinese internal-style hits: 0

The main paper bodies now present E1/E2/E3/E4 as the reviewer-facing evaluation path; R-numbered runs remain provenance in the ledger and artifacts rather than main experiments.

## Checks

| Check | Passed | Detail |
|---|---:|---|
| main_papers_have_no_run_ids | True | Found 0 R-numbered run-id mentions in main papers. |
| main_papers_avoid_internal_checklist_terms | True | Found 0 internal checklist-style terms in the Chinese/English main papers. |
| english_three_plus_one_visible | True | English draft frames E1-E3 plus E4 and demotes support artifacts from main experiments. |
| chinese_three_plus_one_visible | True | Chinese draft frames E1-E3 plus E4 and demotes support artifacts from main experiments. |
| rq1_e1_present_in_both_papers | True | RQ1/E1 appears in both paper drafts. |
| rq2_e2_present_in_both_papers | True | RQ2/E2 appears in both paper drafts. |
| rq3_e3_present_in_both_papers | True | RQ3/E3 appears in both paper drafts. |
| rq4_e4_present_in_both_papers | True | RQ4/E4 appears in both paper drafts. |
| e4_not_accuracy_or_fifth_experiment | True | E4 is replayability/scope-control, not another hidden-label accuracy experiment. |
| ledger_keeps_run_ids_as_provenance | True | Evaluation ledger keeps run IDs as provenance rather than main-paper structure. |
| idea_story_next_action_matches | True | Idea story preserves the next-action constraint against more small empirical blocks. |
| r395_and_r396_still_pass | True | R395 status=pass; R396 status=pass |
| source_status_tracked_or_dirty_allowed | True | All R397 inputs are tracked or intentionally dirty while this gate is generated. |
