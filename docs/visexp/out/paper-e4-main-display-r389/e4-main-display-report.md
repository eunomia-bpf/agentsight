# R389 E4 Main-Display Gate

Status: **pass**

RQ4/E4 presents R327/R328 as the replayability/cost and deterministic-output main displays for the artifact/reproducibility block.

## Table Shape

| Paper | Replay/cost rows | Determinism rows |
|---|---:|---:|
| English | 4 | 2 |
| Chinese | 4 | 2 |

## Checks

| Check | Passed | Detail |
|---|---:|---|
| e4_tables_present_once | True | Both drafts expose the R327 cost table and R328 determinism table as E4 main displays. |
| tables_live_inside_rq4_sections | True | All E4 main-display tables are located inside RQ4/E4 before related work or the dataset discussion. |
| table_shapes_preserved | True | English rows=[4, 2]; Chinese rows=[4, 2]. |
| table_numbers_preserved | True | Missing English=[]; missing Chinese=[]. |
| section_numbers_preserved | True | Missing English=[]; missing Chinese=[]. |
| source_artifacts_match_headline_numbers | True | Missing R327=[]; missing R328=[]. |
| source_artifact_role_visible | True | R327/R328 are framed as provenance for E4 main displays, not additional accuracy experiments. |
| non_claim_boundaries_visible | True | E4 keeps live overhead, human utility, ecosystem compatibility, selector, and empirical-accuracy non-claims visible. |
| ledger_records_r389_as_focus_gate_when_present | True | If R389 is present in the ledger, it is a paper-focus gate, not a profiler experiment. |
| no_data_or_profiler_rerun | True | Runtime commands=['git_stdout(args)', 'git ls-files --error-unmatch -- <dynamic>', 'git diff --quiet -- <dynamic>', 'git diff --cached --quiet -- <dynamic>', 'git_stdout call: git rev-parse HEAD', 'git_stdout call: git ls-files -s -- <dynamic>']; forbidden hits=[]; non-git commands=[]. |

## Sources

| Source | Status | Path |
|---|---:|---|
| generator script | tracked_dirty_allowed | `script/paper_e4_main_display_r389.py` |
| English paper | tracked_clean | `docs/agentpprof-paper/main.tex` |
| Chinese paper | tracked_dirty_allowed | `docs/visexp/paper/main.tex` |
| evaluation ledger | tracked_dirty_allowed | `docs/evaluation.md` |
| R327 report | tracked_clean | `docs/visexp/out/operation-profile-cost-r327/profile-cost-report.md` |
| R327 summary | tracked_clean | `docs/visexp/out/operation-profile-cost-r327/profile-cost-summary.csv` |
| R328 report | tracked_clean | `docs/visexp/out/operation-profile-deterministic-output-r328/deterministic-output-report.md` |
| R328 summary | tracked_clean | `docs/visexp/out/operation-profile-deterministic-output-r328/deterministic-output-summary.csv` |
| English paper submodule gitlink | tracked_dirty_allowed | `docs/agentpprof-paper` |
