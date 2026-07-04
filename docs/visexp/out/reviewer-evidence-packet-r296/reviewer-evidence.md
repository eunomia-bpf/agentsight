# R296 Reviewer Evidence Packet

This packet is generated from tracked R282-R295 artifacts. It is a reviewer navigation layer over existing results, not a new empirical dataset run.

## Claim Verdicts

| Claim | Verdict | Paper-ready wording | Unsupported wording |
|---|---|---|---|
| C1 | supported | The semantic profiler can represent heterogeneous public agent trajectories and local agent sessions as operations, then profile them through user-selected operation stacks without hard-coding prompt/session boundaries. | complete conversion of every public agent benchmark, raw image/video archive profiling |
| C2 | supported with scoped limits | Recursive operation stacks recover useful task, phase, action, human-group, safety, and quality-label views, and expose when a coarse field is not a valid proxy for a finer oracle. | perfect intent recovery, single universal stack depth, quality prediction from task outcome alone |
| C3 | partial | Label-derived deterministic mappings improve semantic aggregation on held-out sessions and leave-dataset-out folds; they should be presented as reproducible mapping/tagging, not as unsupervised boundary discovery. | fully unsupervised boundary detection, LLM-backed or model-backed boundary inference |

## Derived Reviewer Metrics

- Coverage: 15 datasets, 47590 operations, 1611 unique stacks; top-5 datasets hold 83.85% of operations.
- Recursive foldability: the same 13265 operations fold from 9 dataset stacks to 57 phase, 455 action, and 3757 fixed-session stacks.
- Mapping value: held-out mapping reduces unique stacks by 26.408% and improves compression by 35.889%; leave-dataset-out positive folds are 66.667% with 0 negative folds.
- Human-group value: OSWorld grouped-depth stacks reduce action-depth unique stacks by 78.008%; group-pattern/human-group F1 is 0.6268 at precision 1.0.
- Diagnostic value: AgentRewardBench repeat-signal/looping V-measure is 0.3777 vs 0.0105 for the step-error baseline (35.971x); AgentNet task status and repeat signal remain weak proxies for per-step quality.
- Reproducibility value: profile-spec override reduces AgentNet stacks by 86.349% without changing operations; trace and operation imports remain folded-output equivalent.

## Visualization Catalog

| View | Kind | Claim | Output | Takeaway |
|---|---|---|---|---|
| Claim synthesis gate | claim table | C1/C2/C3 | `docs/visexp/out/paper-claim-synthesis-r295/claim-synthesis.md` | Paper wording is grounded in tracked artifacts and unsupported claims stay explicit. |
| Recursive stack-depth sweep | depth sweep | C1/C2 | `docs/visexp/out/operation-stack-depth-r286/depth-summary.html` | The same operations fold from dataset to phase/action/fixed-session depths. |
| Held-out mapping quality | quality report | C2/C3 | `docs/visexp/out/operation-map-heldout-r282/quality.html` | Label-derived mappings improve held-out aggregation against no-map baseline. |
| Leave-dataset-out mapping | cross-dataset ablation | C3 | `docs/visexp/out/operation-map-leaveout-api-r285/leaveout-summary.html` | Operation-family precedence removes negative leave-out stack-reduction folds. |
| OSWorld-Human action-depth stack | stack tree and transitions | C2 | `docs/visexp/out/external-agent-trace-osworldhuman-r290/osworld-human-stack-analysis.html` | Desktop single-action trajectories profile through the same operation-stack path. |
| OSWorld-Human grouped-depth stack | human-boundary stack tree | C2 | `docs/visexp/out/external-agent-trace-osworldhuman-r290/osworld-human-grouped-stack-analysis.html` | Validated human grouped-action fields fold the same sequence at coarser depth. |
| AgentNet step-quality report | quality and coverage report | C1/C2 | `docs/visexp/out/external-agent-trace-agentnet-r291/agentnet-quality.html` | Step correctness and redundancy are ordinary operation fields with full coverage. |
| AgentRewardBench failure diagnostics | failure-quality report | C2 | `docs/visexp/out/external-agent-trace-agentreward-r288/agentreward-quality.html` | Looping labels expose sequence diagnostics beyond per-step error labels. |
| SATraj safety diagnostics | safety-quality report | C2 | `docs/visexp/out/external-agent-trace-satraj-r289/satraj-quality.html` | Safety and attack labels are diagnostic operation fields, not phase proxies. |
| ScaleCUA history-depth analysis | history-depth report | C1/C2 | `docs/visexp/out/external-agent-trace-scalecua-r292/scalecua-history-analysis.html` | Previous-operation context can be represented as stackable operation fields. |
| Fifteen-dataset combined stack analysis | stack tree and transitions | C1/C2 | `docs/visexp/out/external-agent-trace-scalecua-r292/combined-15datasets-stack-analysis.html` | The same profiler path spans web, desktop, mobile, API, dialogue, safety, and quality traces. |

## Reviewer Questions

| Question | Answer | Caveat |
|---|---|---|
| Does the profiler avoid prompt/session-specific abstraction? | Yes for the tested scope: heterogeneous public trajectories and a local session trace enter the same operation/operation-stack path. | This does not prove full-scale conversion of every public benchmark. |
| Can one operation sequence be folded at multiple useful depths? | Yes. R286 sweeps identical operations across eight stack depths, while R290 folds OSWorld-Human single actions at action or grouped depth. | The current grouped-boundary detector is conservative and incomplete. |
| Does mapping/tagging add value beyond pretty printing? | Partially. R282 improves held-out compression and R285 has zero negative leave-dataset-out folds after operation-family precedence fixes. | This remains label-derived deterministic mapping, not unsupervised discovery. |
| Does the profiler solve real diagnostic tasks, not just flamegraphs? | Yes as a mechanism: AgentRewardBench, SATraj, and AgentNet expose looping, safety, attack, correctness, and redundancy fields as stackable operation fields with negative controls. | No user study yet proves developer productivity gains. |

## Expansion Gates

| Gate | Why | Success condition |
|---|---|---|
| Non-rule boundary backend | Would convert C3 from deterministic mapping to a stronger boundary-detection claim. | Improve recall/calibration without losing the high precision seen in R282/R290/R291. |
| User utility task study | Would support a developer-productivity claim now explicitly excluded by R295/R296. | Operation-stack views outperform flat traces and fixed-session stacks. |
| Larger streaming corpus | Would expand C1 from sampled public trajectories to broader benchmark coverage. | Keep raw archives out of git while preserving auditable operation summaries. |

## Unsupported Final Claims

- The profiler fully discovers latent intent boundaries without labels or rules.
- The profiler improves human developer productivity.
- Every public agent trajectory dataset can be profiled at full scale without additional engineering.
