# R388 E3 Main-Display Gate

Status: **pass**

RQ3/E3 presents task diagnosis cards as the main mechanism/actionability display with R365/R373 recorded as provenance.

## Table Shape

| Paper | Rows |
|---|---:|
| English | 6 |
| Chinese | 6 |

## Checks

| Check | Passed | Detail |
|---|---:|---|
| e3_tables_present_once | True | Both drafts have exactly one E3 task diagnosis-card table. |
| tables_live_inside_rq3_sections | True | Both actionability tables are located inside RQ3/E3 before RQ4/E4. |
| six_task_rows_preserved | True | Missing task rows=[]; English rows=6; Chinese rows=6. |
| task_card_numbers_preserved | True | Missing table tokens=[]. |
| section_actionability_numbers_preserved | True | Missing English=[]; missing Chinese=[]. |
| source_artifact_role_visible | True | R365/R373 are framed as provenance for the E3 main display, not new main experiments. |
| no_hidden_label_leakage_or_auto_selector_claim | True | E3 keeps hidden-label no-leakage and automatic-selector/boundary/patch non-claims visible. |
| ledger_records_r388_as_focus_gate_when_present | True | If R388 is present in the ledger, it is a paper-focus gate, not a profiler experiment. |
| no_data_or_profiler_rerun | True | Runtime commands=['git_stdout(args)', 'git ls-files --error-unmatch -- <dynamic>', 'git diff --quiet -- <dynamic>', 'git diff --cached --quiet -- <dynamic>', 'git_stdout call: git rev-parse HEAD', 'git_stdout call: git ls-files -s -- <dynamic>']; forbidden hits=[]; non-git commands=[]. |

## Sources

| Source | Status | Path |
|---|---:|---|
| generator script | tracked_dirty_allowed | `script/paper_e3_main_display_r388.py` |
| English paper | tracked_clean | `docs/agentpprof-paper/main.tex` |
| Chinese paper | tracked_dirty_allowed | `docs/visexp/paper/main.tex` |
| evaluation ledger | tracked_dirty_allowed | `docs/evaluation.md` |
| English paper submodule gitlink | tracked_dirty_allowed | `docs/agentpprof-paper` |
