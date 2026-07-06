# R384 Main-Paper Experiment Focus Gate

Status: **pass**

The main paper is organized as three substantial empirical profiling experiments plus one artifact/reproducibility block, with R-numbered artifacts kept as provenance/support rather than main experiments.

## Paper Blocks

| Block | Main experiment? | Role |
|---|---:|---|
| E1 | yes | Generality, two-abstraction coverage, recursive folding, and field derivation. |
| E2 | yes | Hidden-label localization/ranking over real labeled traces. |
| E3 | yes | Mechanism isolation and profile-configuration actionability. |
| E4 | artifact block only | Artifact replayability, offline cost, and claim hygiene. |

## Checks

| Check | Passed | Detail |
|---|---:|---|
| upstream_three_plus_one_gates_pass | True | R380 and R382 remain passing provenance for the three-plus-one organization. |
| core_result_tables_present | True | Both paper drafts keep a single paper-facing core result table. |
| required_english_focus_wording | True | English draft states E1/E2/E3/E4 roles and says support records are not additional experiments. |
| required_chinese_focus_wording | True | Chinese draft states E1/E2/E3/E4 roles and says support records do not form extra experiments. |
| no_main_body_role_map_table_or_run_ledger | True | Forbidden main-body role-map/run-ledger markers: {} |
| four_named_blocks_only | True | Both drafts explicitly route the paper through RQ1/E1--RQ4/E4. |
| ledger_records_r384_as_paper_hygiene_when_present | True | If R384 is already in the ledger, it is described as paper focus/hygiene, not a new profiler run. |
| no_data_or_profiler_rerun | True | This script reads paper text and prior gate reports only; it does not fetch data, relabel traces, or run agentpprof. |

## Sources

| Source | Status | Path |
|---|---:|---|
| generator script | tracked_dirty_allowed | `script/paper_main_experiment_focus_r384.py` |
| English paper | tracked_clean | `docs/agentpprof-paper/main.tex` |
| Chinese paper | tracked_dirty_allowed | `docs/visexp/paper/main.tex` |
| evaluation ledger | tracked_dirty_allowed | `docs/evaluation.md` |
| R380 experiment-block gate | tracked_clean | `docs/visexp/out/paper-experiment-block-consolidation-r380/experiment-block-consolidation-report.json` |
| R382 canonical three-plus-one gate | tracked_clean | `docs/visexp/out/paper-canonical-three-plus-one-r382/canonical-three-plus-one-report.json` |
| English paper submodule gitlink | tracked_dirty_allowed | `docs/agentpprof-paper` |
