# R381 Diagnosis-Card Gate

Status: `pass`
Checks: 10/10

The E3 diagnosis cards now expose per-task localization signals, concrete profile-configuration actions, and counterpoints while staying inside the 3+1 paper structure.

## Checks

| Check | Passed | Detail |
|---|---:|---|
| upstream_artifacts_pass | True | R365/R373/R380 are passing tracked inputs. |
| six_task_cards_available | True | R365 task cards=6; R373 verdict rows=6. |
| paper_cards_preserve_task_numbers | True | Missing task tokens={} |
| paper_cards_have_actions_and_counterpoints | True | The cards include profile actions and explicit baseline counterpoints. |
| cards_link_e2_to_e3 | True | The table columns tie localization evidence to actionability and counterpoints. |
| no_new_experiment_language | True | The diagnosis cards are presented as paper integration, not a new experiment. |
| non_claims_preserved | True | The cards do not introduce automatic selector, human-utility, or metric-dominance claims. |
| evaluation_ledger_mentions_r381 | True | The evaluation ledger records this diagnosis-card gate. |
| english_submodule_input_committed | True | The English paper input is clean in the submodule and captured by the parent gitlink. |
| source_status_tracked | True | All R381 sources are tracked or intentionally dirty/staged. |
