# R398 Current Three-Plus-One Organization Gate

Status: `pass`
Checks: 12/12
Main-paper run-id hits: 0
Paper-facing self-undercut hits: 0

The current paper organization remains three empirical profiling experiments plus one artifact/reproducibility block. R-numbered runs are ledger provenance, support, ablations, counterpoints, or hygiene gates, not main-paper mini-experiments.

## Checks

| Check | Passed | Detail |
|---|---:|---|
| prerequisite_gates_pass | True | Prerequisite statuses={'R395 claim/verdict alignment': 'pass', 'R396 paper build smoke': 'pass', 'R397 anti-run-ledger': 'pass'} |
| papers_have_exactly_four_rq_subsections | True | Chinese RQs=['RQ1/E1', 'RQ2/E2', 'RQ3/E3', 'RQ4/E4']; English RQs=['RQ1/E1', 'RQ2/E2', 'RQ3/E3', 'RQ4/E4'] |
| three_plus_one_stated_in_both_papers | True | Both drafts state E1-E3 as core empirical profiling experiments and E4 as artifact/reproducibility. |
| e2_is_single_hidden_label_accuracy_block | True | Hidden-label profiler accuracy is concentrated in E2 rather than split into many small experiments. |
| e3_is_mechanism_actionability_not_fifth_experiment | True | Mechanism, actionability, patches, and boundary-field evidence remain inside E3. |
| e4_is_replay_hygiene_not_accuracy_or_ecosystem_claim | True | E4 remains an artifact/reproducibility block with explicit non-claims. |
| main_papers_stay_free_of_run_ids | True | Found 0 R-numbered run-id mentions in main paper bodies. |
| main_papers_avoid_venue_self_undercut | True | Found 0 paper-facing venue-readiness self-undercut phrases; limitations should bound the scoped profiling claim rather than disclaiming top-tier evidence. |
| ledger_keeps_runs_as_provenance | True | The evaluation ledger records run IDs as provenance/support/guardrails rather than main-paper structure. |
| new_runs_must_strengthen_core_blocks | True | New runs must be assigned a role inside E1-E4 instead of becoming scattered paper experiments. |
| canonical_next_action_rejects_small_experiment_sprawl | True | The idea story preserves the next-action rule against scattered new empirical blocks. |
| source_status_tracked_or_dirty_allowed | True | All inputs are tracked or intentionally dirty while this gate is generated. |
