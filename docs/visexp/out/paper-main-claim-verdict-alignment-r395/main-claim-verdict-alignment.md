# R395 Main Claim / Verdict Alignment Gate

Status: `pass`
Checks: 13/13

The canonical docs and paper drafts align on the scoped profiling claim: label-scored localization/ranking with lower flat-summary inspection work, a fixed-session proxy fragmentation tradeoff, configuration-level actionability, and explicit non-claims. If the English submodule is read-only and behind, R405 records that sync gap instead of requiring a submodule edit in this workflow.

## Checks

| Check | Passed | Detail |
|---|---:|---|
| prerequisite_gates_current | True | Prerequisite statuses={'R377 main claim evidence': 'pass', 'R380 experiment-block consolidation': 'pass', 'R383 canonical reviewer acceptance': 'accepted', 'R391 core readiness': 'pass', 'R393 post-R392 reviewer acceptance': 'accepted', 'R394 two-abstraction doc gate': 'pass', 'R405 English read-only gap audit': 'pass'} |
| central_claim_consistent_across_docs_and_papers | True | The main claim is the same hidden-label profiler fidelity/tradeoff claim in canonical docs and both papers. |
| headline_numbers_and_workloads_match | True | Headline E2 workload and metric tokens are present across the aligned documents. |
| claim_verdict_excludes_unsupported_claims | True | The claim verdict and idea story keep unsupported human-utility, boundary, ecosystem, and universal-selector claims out. |
| fixed_session_is_proxy_not_span_tree_superiority | True | Fixed-session remains a proxy baseline; real span-tree ecosystem superiority is not claimed. |
| three_plus_one_claim_roles_visible | True | E1-E3 remain empirical profiling experiments; E4 remains replayability/scope-control. |
| actionability_is_configuration_guidance_not_auto_selector | True | Actionability is profile-configuration guidance, not automatic action/policy selection. |
| two_abstraction_boundary_still_visible | True | The two-abstraction boundary remains visible after claim-verdict alignment. |
| e4_not_accuracy_or_human_utility | True | E4 remains replayability/cost/scope-control, not accuracy, live overhead, or human utility. |
| r395_registered_in_evaluation_ledger | True | Evaluation ledger records this main-claim/verdict alignment gate. |
| idea_story_points_to_r395 | True | Idea story records that R395 aligned the current claim/verdict boundary. |
| english_submodule_clean | True | English paper submodule is clean and captured by the parent gitlink, or R405 records the read-only sync gap. |
| source_status_tracked_or_dirty_allowed | True | All guard inputs are tracked or intentionally dirty while this guard is being generated. |
