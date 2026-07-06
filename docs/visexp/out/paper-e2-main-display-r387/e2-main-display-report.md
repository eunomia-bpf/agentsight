# R387 E2 Main-Display Gate

Status: **pass**

RQ2/E2 presents the hidden-label localization/ranking benchmark as one paper-facing main display with R320 recorded as provenance.

## Table Shape

| Paper | Rows |
|---|---:|
| English | 8 |
| Chinese | 8 |

## Checks

| Check | Passed | Detail |
|---|---:|---|
| english_e2_table_present_once | True | English paper has exactly one E2 hidden-label localization benchmark table. |
| chinese_e2_table_present_once | True | Chinese paper has exactly one E2 hidden-label localization benchmark table. |
| tables_live_inside_rq2_sections | True | Both E2 tables are located inside the RQ2/E2 source section before RQ3/E3. |
| policy_rows_preserved | True | Missing English rows=[]; missing Chinese rows=[]. |
| headline_numbers_preserved_in_rq2 | True | Missing English tokens=[]; missing Chinese tokens=[]. |
| caption_is_e2_not_run_led | True | Captions make R320 provenance explicit while presenting the table as E2. |
| scope_and_counterpoints_visible | True | E2 keeps flat/fixed-session counterpoints and must-not-claim boundaries visible. |
| ledger_records_r387_as_focus_gate_when_present | True | If R387 is present in the ledger, it is a paper-focus gate, not a profiler experiment. |
| no_data_or_profiler_rerun | True | Runtime commands=['git_stdout(args)', 'git ls-files --error-unmatch -- <dynamic>', 'git diff --quiet -- <dynamic>', 'git diff --cached --quiet -- <dynamic>', 'git_stdout call: git rev-parse HEAD', 'git_stdout call: git ls-files -s -- <dynamic>']; forbidden hits=[]; non-git commands=[]. |

## Sources

| Source | Status | Path |
|---|---:|---|
| generator script | tracked_dirty_allowed | `script/paper_e2_main_display_r387.py` |
| English paper | tracked_clean | `docs/agentpprof-paper/main.tex` |
| Chinese paper | tracked_dirty_allowed | `docs/visexp/paper/main.tex` |
| evaluation ledger | tracked_dirty_allowed | `docs/evaluation.md` |
| English paper submodule gitlink | tracked_dirty_allowed | `docs/agentpprof-paper` |
