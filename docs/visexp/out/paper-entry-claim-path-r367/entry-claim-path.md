# R367 Paper Entry Claim Path Audit

- Status: `pass`.
- Checks: 11/11.
- This is a paper-integration gate, not a new empirical result.
- It keeps the paper organized as RQ1/E1--RQ4/E4 rather than a scattered R-run list.

## Entry Token Matrix

| Language | Section | Status | Missing tokens |
|---|---|---|---|
| zh | abstract | pass |  |
| zh | intro_or_problem | pass |  |
| zh | main_result_framing | pass |  |
| en | abstract | pass |  |
| en | intro_or_problem | pass |  |
| en | main_result_framing | pass |  |

## Checks

| Check | Status | Evidence |
|---|---|---|
| `entry_sections_share_e1_e4_structure` | pass | 6/6 entry token rows pass. |
| `paper_uses_three_plus_one_not_scattered_experiments` | pass | Chinese and English entry text present RQ1/E1-RQ4/E4 as three empirical profiling questions plus one systems/reproducibility question, not a chronological run list. |
| `only_two_profiler_abstractions_in_entry_path` | pass | Prompt/session/tool/process/syscall are presented as operation forms or fields under operation and operation stack. |
| `r_runs_are_provenance_not_paper_structure` | pass | R-numbered artifacts remain provenance and no E5 paper-facing experiment is introduced. |
| `e2_hidden_label_localization_numbers_visible` | pass | Entry path keeps the E2 hidden-label scale and flat/fixed-session tradeoff numbers visible. |
| `e3_actionability_and_boundary_scope_visible` | pass | Entry path keeps profile-spec actionability, boundary-field improvement, and boundary counterpoints visible. |
| `e4_replayability_not_accuracy_claim_visible` | pass | Entry path presents E4 as reproducibility/cost evidence rather than another accuracy or live-overhead result. |
| `generated_ledgers_match_entry_numbers` | pass | R360/R361/R364/R366 ledgers pass and preserve four core experiments plus internal R366 mechanism evidence. |
| `must_not_claim_boundaries_visible` | pass | Entry path excludes human utility/productivity, automatic boundary discovery, metric dominance, and complete ecosystem compatibility claims. |
| `visualization_not_flamegraph_only` | pass | Presentation is framed as a small portfolio of analysis views, not a flamegraph-only result or extra experiment. |
| `input_policy_no_new_data_or_profiler_rerun` | pass | The R367 sources are tracked ledgers/docs only: no dataset sync, no relabeling, and no profiler rerun. |

## Non-Claims

- Not a new dataset, relabeling step, profiler rerun, or human/agent analyst task.
- Not a fifth paper-facing experiment.
- Not evidence for human productivity, automatic boundary discovery, metric dominance, live overhead, or complete trace-ecosystem compatibility.
