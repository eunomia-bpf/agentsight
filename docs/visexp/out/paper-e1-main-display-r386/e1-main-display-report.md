# R386 E1 Main-Display Gate

Status: **pass**

RQ1/E1 now has one compact claim-test display for the operation/operation-stack abstraction, recursive folding, field derivation, and human-boundary scope.

## Table Shape

| Paper | Rows |
|---|---:|
| English | 4 |
| Chinese | 4 |

## Checks

| Check | Passed | Detail |
|---|---:|---|
| english_e1_table_present_once | True | English paper has exactly one E1 claim-test summary table. |
| chinese_e1_table_present_once | True | Chinese paper has exactly one E1 main-evidence table. |
| tables_have_four_claim_tests | True | English rows=4; Chinese rows=4. |
| required_e1_numbers_preserved | True | Missing English=[]; missing Chinese=[]. |
| recursive_and_mapping_scope_is_visible | True | The display ties recursive folding, mapping, and boundary backends to scoped mechanisms. |
| non_claim_boundaries_visible | True | The display preserves E1 non-claims and does not imply universal intent-boundary recovery. |
| ledger_records_r386_as_focus_gate_when_present | True | If R386 is present in the ledger, it is a paper-focus gate, not a profiler experiment. |
| no_data_or_profiler_rerun | True | Runtime commands=['git_stdout(args)', 'git ls-files --error-unmatch -- <dynamic>', 'git diff --quiet -- <dynamic>', 'git diff --cached --quiet -- <dynamic>', 'git_stdout call: git rev-parse HEAD', 'git_stdout call: git ls-files -s -- <dynamic>']; forbidden hits=[]; non-git commands=[]. |

## Sources

| Source | Status | Path |
|---|---:|---|
| generator script | tracked_dirty_allowed | `script/paper_e1_main_display_r386.py` |
| English paper | tracked_clean | `docs/agentpprof-paper/main.tex` |
| Chinese paper | tracked_dirty_allowed | `docs/visexp/paper/main.tex` |
| evaluation ledger | tracked_dirty_allowed | `docs/evaluation.md` |
| English paper submodule gitlink | tracked_dirty_allowed | `docs/agentpprof-paper` |
