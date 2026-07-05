# R335 Actionability Synthesis

R335 reads tracked R320/R325/R326/R329/R332/R334 artifacts and merges them into task-level actionability cards. It does not fetch, sync, create, or relabel a dataset.

## Primary Findings

- R335 turns scattered profiler results into six task-level actionability cards, one for each R320 task, without fetching, syncing, creating, or relabeling data.
- All 6/6 cards contain a concrete optimization action; query-aware ranking improves AP over width on 6/6 cards.
- Mechanism evidence is task-specific: mapping helps 2/6 cards and hurts 4/6, while feature ablations find critical features for 4/6 and misleading features for 2/6.
- Stack depth is an explicit cost/accuracy knob: coarse depth reduces group count on 6/6 cards but is AP-preferred on only 2/6.
- Fragmentation and work remain separate objectives: operation stacks reach 50% positives with fewer groups than fixed sessions on 5/6 cards and inspect fewer groups at 30% work on 5/6, while fixed-session drilldown has lower work-to-first-positive on 4/6.

## Mechanism Ledger

- **query-aware operation-stack ranking**: 6/6. visible query-aware ranking improves AP over width-only operation-stack ranking Action: Expose ranker policy as a query-time knob instead of hard-coding width. Counterpoint: Query-aware ranking is not a label-free universal detector.
- **mapping/tagging before stacking**: 2/6. mapping helps some tasks but hurts or is neutral on others Action: Keep mappings first-class and task-scoped; compare against raw-action stacks. Counterpoint: Mapping is not universally better than raw action/status stacks.
- **operation-level rank features**: 4/6 tasks with critical feature evidence. feature ablations identify which visible fields drive localization Action: Use leave-one-feature reports to keep helpful fields and remove misleading ones. Counterpoint: Ablation-guided repair is post-hoc evidence, not a deployed oracle policy.
- **stack depth**: 2/6 tasks prefer coarse AP; 6/6 reduce groups under coarse depth. depth changes accuracy and visible group count differently by task Action: Expose stack fields/depth as a configurable view rather than one fixed hierarchy. Counterpoint: No single depth is best for AP, top-5 F1, recall, and work simultaneously.
- **cross-task/global rank-policy transfer**: 5/6. simple global/source-task visible policies often beat width Action: Use global defaults and leave-task transfer as auditable candidate policies. Counterpoint: Transfer is mixed and should remain an auditable policy choice.
- **fixed-session drilldown**: 4/6. fixed sessions often find a first positive with less operation work Action: Keep fixed-session/span-tree views as drilldown baselines, not profiler abstractions. Counterpoint: Operation stacks reduce group fragmentation on most tasks but do not dominate first-positive work.

## Non-Claims

- no new datasets, dataset sync, dataset creation, or relabeling
- no human or agent analyst productivity, accuracy, or time-to-answer claim
- no automatic view selector or universal boundary detector
- no claim that repaired rank policies are deployable without labels
- no claim that operation stacks dominate fixed-session drilldown on first-positive work
- no profiler abstraction beyond operation and operation stack

## Artifacts

- Report: `docs/visexp/out/operation-actionability-synthesis-r335/actionability-synthesis-report.json`
- Task cards: `docs/visexp/out/operation-actionability-synthesis-r335/task-actionability-cards.csv`
- Mechanism ledger: `docs/visexp/out/operation-actionability-synthesis-r335/mechanism-evidence.csv`
