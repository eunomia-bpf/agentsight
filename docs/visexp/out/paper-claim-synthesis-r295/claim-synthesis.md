# R295 Paper Claim Synthesis

This artifact is generated from tracked R282-R294 result JSON files. It is a paper-claim gate, not a new dataset run.

## Claim Verdicts

| Claim | Verdict | Paper-ready wording | Evidence keys | Unsupported wording |
|---|---|---|---|---|
| C1 | supported | The semantic profiler can represent heterogeneous public agent trajectories and local agent sessions as operations, then profile them through user-selected operation stacks without hard-coding prompt/session boundaries. | heterogeneous_coverage, recursive_depth, reproducibility_and_exchange | complete conversion of every public agent benchmark, raw image/video archive profiling |
| C2 | supported with scoped limits | Recursive operation stacks recover useful task, phase, action, human-group, safety, and quality-label views, and expose when a coarse field is not a valid proxy for a finer oracle. | recursive_depth, human_boundaries, quality_and_failure_diagnostics | perfect intent recovery, single universal stack depth, quality prediction from task outcome alone |
| C3 | partial | Label-derived deterministic mappings improve semantic aggregation on held-out sessions and leave-dataset-out folds; they should be presented as reproducible mapping/tagging, not as unsupervised boundary discovery. | mapping_generalization | fully unsupervised boundary detection, LLM-backed or model-backed boundary inference |

## Key Evidence

- Heterogeneous coverage: 14 core datasets / 42590 operations / 1497 stacks; with ScaleCUA supplement: 15 datasets / 47590 operations / 1611 stacks.
- Recursive depth: the same 13265 operations fold from 9 dataset stacks to 57 phase stacks, 226 semantic stacks, 455 action stacks, and 3757 fixed-session stacks.
- Mapping generalization: R282 held-out mapping improves compression from 14.049 to 19.091 and unique stacks from 284 to 209; R285 leave-dataset-out has 6/9 positive stack-reduction folds and 0 negative folds.
- Human grouped boundaries: OSWorld-Human has 6010 operations, 4011/6010 with exact human-group fields, and group-pattern vs human-group boundary F1 0.6268 at precision 1.0.
- Quality/failure diagnostics: AgentNet has 16741 operations with full step correctness/redundancy fields; AgentRewardBench repeat-signal/looping V-measure is 0.3777 vs step-error/looping 0.0105; SATraj attack/action V-measure is only 0.0932, so safety remains a diagnostic field rather than a phase proxy.
- Reproducibility/exchange: R293 spec replays 16741 AgentNet samples with 608 stacks and a stack override gives 83; R294 trace and operation imports both have 6 samples / 5 stacks and byte-identical folded output is True.

## Negative And Scope-Setting Evidence

- AgentNet task status is a weak proxy for per-step correctness (V-measure 0.0153); repeat signal is a weak proxy for step redundancy (V-measure 0.0103).
- SATraj attack type is weakly aligned with action taxonomy (V-measure 0.0932), so attack/safety should be treated as operation fields for filtering and diagnosis, not as inferred phases.
- C3 remains partial: current boundary evidence is deterministic mapping/tagging over labeled fields, not unsupervised boundary discovery.

## Sources

- `combined14_quality`: `docs/visexp/out/external-agent-trace-agentnet-r291/combined-14datasets-quality.json`
- `combined15_quality`: `docs/visexp/out/external-agent-trace-scalecua-r292/combined-15datasets-quality.json`
- `depth`: `docs/visexp/out/operation-stack-depth-r286/depth-summary.json`
- `heldout_profile`: `docs/visexp/out/operation-map-heldout-r282/agentpprof-result.json`
- `heldout_nomap_profile`: `docs/visexp/out/operation-map-heldout-r282/agentpprof-nomap-result.json`
- `heldout_quality`: `docs/visexp/out/operation-map-heldout-r282/quality.json`
- `heldout_nomap_quality`: `docs/visexp/out/operation-map-heldout-r282/quality-nomap.json`
- `leaveout`: `docs/visexp/out/operation-map-leaveout-api-r285/leaveout-summary.json`
- `osworld_quality`: `docs/visexp/out/external-agent-trace-osworldhuman-r290/osworld-human-quality.json`
- `osworld_stack`: `docs/visexp/out/external-agent-trace-osworldhuman-r290/osworld-human-stack-analysis.json`
- `osworld_grouped_stack`: `docs/visexp/out/external-agent-trace-osworldhuman-r290/osworld-human-grouped-stack-analysis.json`
- `agentnet_quality`: `docs/visexp/out/external-agent-trace-agentnet-r291/agentnet-quality.json`
- `agentreward_quality`: `docs/visexp/out/external-agent-trace-agentreward-r288/agentreward-quality.json`
- `satraj_quality`: `docs/visexp/out/external-agent-trace-satraj-r289/satraj-quality.json`
- `profile_spec`: `docs/visexp/out/profile-spec-r293/agentnet-diagnostic-result.json`
- `profile_spec_override`: `docs/visexp/out/profile-spec-r293/agentnet-diagnostic-override-result.json`
- `trace_convert`: `docs/visexp/out/agent-trace-exchange-r294/trace-to-operations-result.json`
- `trace_import`: `docs/visexp/out/agent-trace-exchange-r294/trace-import-result.json`
- `operation_import`: `docs/visexp/out/agent-trace-exchange-r294/operation-import-result.json`
- `trace_folded`: `docs/visexp/out/agent-trace-exchange-r294/trace-import.folded`
- `operation_folded`: `docs/visexp/out/agent-trace-exchange-r294/operation-import.folded`
