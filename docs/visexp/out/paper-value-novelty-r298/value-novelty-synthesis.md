# R298 Paper Value And Novelty Synthesis

AgentSight should claim configurable semantic profiling over real labeled agent trajectories: operations provide the common record, operation stacks provide recursive query-time folding, and mappings/boundary backends only derive fields before folding. The evidence supports mechanism and diagnostic value, not unsupervised intent discovery or developer productivity.

## Real Problems And Evidence

| ID | Claim | Real problem | Headline evidence | Status | Limitation |
|---|---|---|---|---|---|
| P1 | C1 | Agent traces mix prompts, tools, GUI actions, API calls, safety labels, and quality labels; prompt/session/span object models split these into incompatible pipelines. | 15 datasets, 47590 operations, 1611 stacks in the supplemental smoke set. | supported for sampled public trajectories | Does not prove full-scale conversion of every public benchmark or image/video archive. |
| P2 | C2 | The useful boundary depends on the debugging question; a fixed session/prompt stack either hides phase structure or fragments aggregation. | R286 folds the same 13265 operations from 9 dataset stacks to 57 phase, 455 action, and 3757 fixed-session stacks; R293 stack override reduces AgentNet stacks by 86.349%. | supported with scoped limits | Does not identify one universal best stack for every task. |
| P3 | C3 | Raw dataset labels and action names are inconsistent; without field derivation, stacks are either too shallow or too fragmented. | R282 mapping reduces held-out unique stacks by 26.408% and improves compression by 35.889%; R285 has 0 negative folds; R297 supervised boundary F1 is 0.7735. | partial, with supervised expansion evidence | Does not support unsupervised or cross-family general boundary detection. |
| P4 | C2 | Desktop agents often need subtask-level inspection below a task but above a raw click/key action. | Conservative human-group projection reaches boundary F1 0.6268 at precision 1.0; R297 learned backend improves over phase/action/target baselines and folds 1132 held-out operations into 74 stacks. | supported as scoped boundary evidence | R290 conservative recall is limited; R297 is supervised and OSWorld-only. |
| P5 | C2 | Agent debugging requires failure, safety, looping, and step-quality diagnostics, not only hot paths. | AgentRewardBench repeat-signal/looping V-measure is 0.3777 versus 0.0105 for step-error; SATraj has 622 unsafe operations; AgentNet step_correct and step_redundant fields have 16741 and 16741 covered operations. | supported as diagnostic mechanism | Does not prove developer productivity or automatic quality prediction. |
| P6 | C1 | Paper claims drift when results are scattered across shell commands, folded files, and one-off visualizations. | R294 trace import and operation import folded outputs are identical; R296 indexes 11 visualization/evidence entries and 4 reviewer questions. | supported for artifact auditability | Reviewer packets are synthesis artifacts, not new empirical evidence. |

## Novelty Claims

- **Two-object agent profiling model**: The profiler does not privilege prompt, session, span, GUI, safety, or quality objects; they are operation shapes or fields. Evidence: C1 supported by 15 public labeled sources plus local trace exchange.
- **Query-time recursive operation stacks**: Folded-stack output is reused, but frames come from semantic operation fields and can be changed after capture. Evidence: R286 depth sweep and R293 profile-spec override on identical operations.
- **Unified field-derivation extension point**: Regex mappings, learned label-derived mappings, and supervised boundary backends all write operation fields before folding. Evidence: R282/R285 mapping generalization and R297 learned boundary backend.
- **Non-flamegraph diagnostic views over real labels**: Quality, looping, safety, attack, redundancy, and human-group labels become stackable and scoreable fields. Evidence: R288/R289/R290/R291 diagnostics and R296 evidence packet.

## Paper Readiness

- Maturity: level-3 conference-paper evidence, approaching level 4 for mechanism claims.
- Remaining level-4 gaps:
  - replicate the learned boundary backend on another family such as AgentNet or tau-bench
  - add a user-utility or task-answering study comparing flat trace, fixed session stack, and operation-stack views
  - add calibration/error analysis for boundary backends
- Must not claim:
  - The profiler fully discovers latent intent boundaries without labels or rules.
  - The profiler improves human developer productivity.
  - Every public agent trajectory dataset can be profiled at full scale without additional engineering.
  - R297 generalizes beyond OSWorld-Human
  - R296 reviewer packet is itself empirical evidence
