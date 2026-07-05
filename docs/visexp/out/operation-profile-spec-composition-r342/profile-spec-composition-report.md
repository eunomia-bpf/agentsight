# R342 Profile-Spec Composition Audit

R342 reuses tracked R324 Rust outputs over the R300 real labeled operation suite.
It is a reproducibility and mechanism audit, not a new dataset run.

## Primary Findings

- R342 audits 12 Rust profile-spec variants over 6 real labeled R300/R324 tasks without downloading or relabeling data.
- All 12/12 variants compose operation files, query predicates, operation-level rank rules, rule-score ranking, and explicit stack depth.
- All 12/12 variants fold without prompt/session frames, reinforcing that prompt/session are optional operation fields rather than required boundaries.
- Visible operation-feature ranking improves AP over width on 9/12 variants and first-positive work on 10/12 variants.
- Coarse depth reduces groups on 6/6 tasks with median group reduction 0.827, while best AP depth splits as {'coarse': 2, 'semantic': 4}.

## Summary

- Variants: 12.
- Prompt/session-free variants: 12/12.
- AP wins vs width: 9/12.
- First-positive work wins vs width: 10/12.
- Median coarse group reduction: 0.827.

## Task Depth Tradeoff

| Task | Dataset | Semantic groups | Coarse groups | Coarse group reduction | Best AP depth |
|---|---|---:|---:|---:|---|
| agentnet_incorrect_step | agentnet | 289 | 43 | 0.851 | semantic |
| agentnet_redundant_step | agentnet | 260 | 42 | 0.838 | semantic |
| agentreward_looping | agent-reward-bench | 40 | 16 | 0.600 | semantic |
| agentreward_side_effect | agent-reward-bench | 40 | 16 | 0.600 | coarse |
| osworld_group_start | osworld-human | 173 | 32 | 0.815 | semantic |
| satraj_unsafe | satraj-os-safety | 142 | 22 | 0.845 | coarse |

## Non-Claims

- R342 is not a new dataset run and does not add new labels.
- R342 is not a human or agent analyst study.
- R342 does not claim automatic boundary discovery or a universal stack-depth selector.
- R342 does not add a profiler abstraction beyond operation and operation stack.
