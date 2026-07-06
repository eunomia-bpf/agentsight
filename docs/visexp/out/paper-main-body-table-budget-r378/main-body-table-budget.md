# R378 Main-Body Table-Budget Gate

Status: `pass`
Checks: 9/9
Paper-facing organization: 3 empirical profiling experiments + 1 artifact/reproducibility block.
English table environments: 7
Chinese table environments: 6

The main papers now reserve table/figure weight for the core E1-E4 evidence, while R363/R365/R373 support artifacts remain provenance and checks rather than additional main-body experiments.

## Checks

| Check | Passed | Detail |
|---|---:|---|
| core_displays_preserved | True | English missing=[]; Chinese missing=[] |
| support_artifact_tables_demoted | True | Demoted labels absent from main paper text: ['tab:visualization-portfolio', 'tab:r365-headlines', 'tab:r365-cases', 'tab:r373-verdict']; still_present=[] |
| non_flamegraph_view_retained | True | The main body keeps one non-flamegraph E2/E3 figure while demoting the full portfolio table. |
| task_level_evidence_retained_as_prose | True | Task-level case/verdict evidence remains in prose with positive and counterpoint counts. |
| r377_claim_facets_unchanged | True | R378 consumes the passing R377 claim-facet packet rather than changing the evidence basis. |
| main_body_table_budget_reduced | True | English table environments=7; Chinese table environments=6. |
| evaluation_ledger_mentions_r378 | True | The evaluation ledger records this paper-presentation guardrail. |
| english_submodule_input_committed | True | The English paper input is clean in the submodule and captured by the parent gitlink. |
| source_status_tracked | True | All R378 sources are tracked or intentionally dirty/staged. |
