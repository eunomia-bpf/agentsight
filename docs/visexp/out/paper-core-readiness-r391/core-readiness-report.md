# R391 Core Evaluation Readiness Gate

Status: **pass**

The current evaluation is organized as three empirical profiling experiments plus one artifact/reproducibility block, with each block carrying a reviewer-facing success criterion and failure narrowing rule.

## Blocks

| Block | Role | Success Criterion | Failure Interpretation | Ready |
|---|---|---|---|---:|
| RQ1/E1 | Representation validity and recursive folding | One operation layer covers heterogeneous traces and folds at multiple depths. | Narrow the abstraction claim or require additional operation-field derivation. | yes |
| RQ2/E2 | Primary hidden-label localization and baseline tradeoff | Hot groups match hidden positives with lower flat work and better fixed-session fragmentation tradeoff. | Narrow to the metrics/tasks where the Pareto condition holds. | yes |
| RQ3/E3 | Mechanism isolation and profile-configuration actionability | Mechanism ablations and executable profile-spec patches expose concrete tuning actions. | Keep only descriptive localization and remove actionability wording. | yes |
| RQ4/E4 | Replayability, cost, and claim hygiene | Tracked profile specs replay deterministically and paper claims stay scoped. | Treat the artifact as exploratory and remove reproducibility wording. | yes |

## Checks

| Check | Passed | Detail |
|---|---:|---|
| reviewer_evidence_path_visible | True | Missing global evidence-path tokens=[]. |
| rq1_e1_contract_complete | True | Missing English tokens=[]; missing Chinese tokens=[]. |
| rq2_e2_contract_complete | True | Missing English tokens=[]; missing Chinese tokens=[]. |
| rq3_e3_contract_complete | True | Missing English tokens=[]; missing Chinese tokens=[]. |
| rq4_e4_contract_complete | True | Missing English tokens=[]; missing Chinese tokens=[]. |
| prereq_display_and_novelty_gates_pass | True | Non-pass prerequisite gates=[]. |
| ledger_records_r391_when_present | True | If R391 is present in the ledger, it is recorded as core evaluation readiness. |
| no_data_sync_or_profiler_rerun | True | Forbidden imports or runtime calls=[]. |

## Prerequisite Gates

| Run | Status | Path |
|---|---:|---|
| R386 | pass | `docs/visexp/out/paper-e1-main-display-r386/run-result.json` |
| R387 | pass | `docs/visexp/out/paper-e2-main-display-r387/run-result.json` |
| R388 | pass | `docs/visexp/out/paper-e3-main-display-r388/run-result.json` |
| R389 | pass | `docs/visexp/out/paper-e4-main-display-r389/run-result.json` |
| R390 | pass | `docs/visexp/out/paper-novelty-positioning-r390/run-result.json` |
