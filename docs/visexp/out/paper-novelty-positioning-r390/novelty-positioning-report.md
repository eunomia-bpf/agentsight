# R390 Novelty-Positioning Gate

Status: **pass**

The paper scopes novelty to agent-operation records, recursive operation-stack projections, and hidden-label profile-group scoring, not to flamegraphs, generic aggregation, generic observability, or failure localization by itself.

## Checks

| Check | Passed | Detail |
|---|---:|---|
| english_abstract_scopes_novelty | True | Missing English abstract tokens=[]. |
| english_related_work_names_closest_threats | True | Missing English related-work tokens=[]. |
| english_conclusion_restates_scoped_novelty | True | Missing English conclusion tokens=[]. |
| chinese_abstract_scopes_novelty | True | Missing Chinese abstract tokens=[]. |
| chinese_related_work_names_closest_threats | True | Missing Chinese related-work tokens=[]. |
| chinese_conclusion_restates_scoped_novelty | True | Missing Chinese conclusion tokens=[]. |
| background_map_records_same_claim_risk | True | Missing background tokens=[]. |
| non_claim_boundaries_visible | True | Missing non-claim tokens=[]. |
| core_experiment_structure_visible | True | Missing English core-experiment tokens=[]; missing Chinese core-experiment tokens=[]. |
| idea_story_matches_scoped_claim | True | Idea story preserves non-generic novelty and scoped profiler claim. |
| ledger_records_r390_as_focus_gate_when_present | True | If R390 is present in the ledger, it is a paper-focus gate, not a profiler experiment. |
| no_data_or_profiler_rerun | True | Runtime commands=['git_stdout(args)', 'git ls-files --error-unmatch -- <dynamic>', 'git diff --quiet -- <dynamic>', 'git diff --cached --quiet -- <dynamic>', 'git_stdout call: git rev-parse HEAD', 'git_stdout call: git ls-files -s -- <dynamic>']; forbidden hits=[]; non-git commands=[]. |

## Sources

| Source | Status | Path |
|---|---:|---|
| generator script | tracked_dirty_allowed | `script/paper_novelty_positioning_r390.py` |
| English paper | tracked_clean | `docs/agentpprof-paper/main.tex` |
| Chinese paper | tracked_dirty_allowed | `docs/visexp/paper/main.tex` |
| related-work map | tracked_clean | `docs/background-related-work.md` |
| idea story | tracked_clean | `docs/idea-story.md` |
| evaluation ledger | tracked_dirty_allowed | `docs/evaluation.md` |
| English paper submodule gitlink | tracked_dirty_allowed | `docs/agentpprof-paper` |
