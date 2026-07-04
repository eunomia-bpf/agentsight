# Paper Claim Readiness R307

R307 refreshes the paper claim gate after R300-R306, with R303 explicitly included for scripted agent-session exchange evidence. It uses tracked artifacts only and treats trace, case-packet, and synthesis files as exchange or review surfaces rather than profiler abstractions.

## Headline

- Public-operation coverage: 15 datasets / 47590 operations.
- Analysis task suite: 6 tasks / 34539 operations.
- R303 agent-session exchange: 1 session / 6 operations, folded equality `True`.
- R305 operation-stack case packets: work 0.0937, recall 0.188, lift 1.6509.
- R305 vs fixed-session: recall ratio 3.63, lift ratio 1.2676, work ratio 1.7172.
- R306 Chrome trace bridge: 6 events, folded equality `True`.

## Claim Verdicts

### C1 - supported

AgentSight represents heterogeneous public agent trajectories and local agent-session traces as operations, then profiles them with user-selected operation stacks. Chrome Trace Event JSON is supported as an exchange container that imports back to operation JSONL.

Evidence:
- 15 sampled public datasets / 47590 operations
- R293 profile-spec replay and stack override
- R294 claim-gated exchange plus R303 scripted agent-session exchange with 1 session / 6 operations and folded equality
- R306 Chrome Trace Event JSON round trip with 6 samples / 5 stacks on all paths

Must not claim:
- all public agent datasets are fully converted at full scale
- Chrome/OpenTelemetry ecosystem compatibility is complete
- trace exchange is a third profiler abstraction

Maximal plausible wording: The operation/operation-stack model can serve as an interchange layer across common agent trace containers.

Expansion experiments:
- import one real OpenTelemetry GenAI span export or Perfetto trace from another agent tool and verify operation-stack parity
- run the trace bridge on a multi-session public trace bundle rather than a fixture

### C2 - supported with scoped limits

Recursive operation stacks recover useful task, phase, action, human-group, safety, and quality-label views on sampled labeled trajectories, and the same operations can be folded at different depths by changing stack fields.

Evidence:
- R286 recursive depth sweep
- R290 OSWorld-Human grouped boundary evidence
- R291 AgentNet step-quality fields
- R299 boundary-family calibration

Must not claim:
- perfect intent recovery
- one universal stack depth
- unsupervised boundary discovery

Maximal plausible wording: Operation stacks are a general query-time boundary language for agent trajectories when adequate operation fields or learned field derivation are available.

Expansion experiments:
- calibrate the learned boundary backend on AgentNet step-quality boundaries
- compare learned operation-boundary fields against an LLM boundary-labeling baseline on one held-out family

### C3 - partial

Deterministic mappings and supervised boundary backends improve semantic aggregation by deriving operation fields before folding.

Evidence:
- R282 held-out mapping
- R285 leave-dataset-out mapping
- R297 OSWorld-Human supervised boundary backend
- R299 family calibration with negative controls

Must not claim:
- field derivation is unsupervised
- one learned backend generalizes across all families
- AgentRewardBench looping requires learned boundaries when repeat_signal_change is sufficient

Maximal plausible wording: Field derivation is a reusable extension point that can host regex, learned, and model-backed mapping backends under one operation-stack contract.

Expansion experiments:
- add a calibrated learned backend on AgentNet and report precision/recall/error cases
- add one model-backed mapping baseline that writes ordinary operation fields and compare it with regex mappings

### C4 - supported as automated proxy, not user utility

On six oracle-backed analysis tasks over existing labeled operations, operation-stack views provide a useful inspectability tradeoff: they are far more selective than flat summaries and higher-recall than fixed-session case packets at the same top-k packet count, but they are not uniformly cheaper than fixed-session drilldown.

Evidence:
- R300 operation-stack vs flat lift 5.726x with inspection ratio 0.288
- R301 label-hidden 30% budget recall 0.3361 vs 0.2844
- R302 top-10 query-aware work 0.1163 with lift 1.5867
- R305 operation-stack vs fixed-session recall ratio 3.63 and work ratio 1.7172

Must not claim:
- human productivity improvement
- automatic anomaly detection
- operation stacks dominate fixed-session views on every work metric

Maximal plausible wording: Current evidence supports automated inspectability proxy metrics; human analyst accuracy or time improvement remains a hypothesis for the next controlled study.

Expansion experiments:
- run a controlled human/agent analyst study using R301/R302/R304/R305 visible packets and hidden answer keys
- measure answer accuracy, time-to-first-positive, inspected operations, and confidence for flat, fixed-session, and operation-stack packets

## Next Gate

Use the existing R301/R302/R304/R305 visible packets and answer keys for a controlled analyst study before claiming user utility.

## Source Artifacts

- `r295_claim`: `docs/visexp/out/paper-claim-synthesis-r295/claim-synthesis.json`
- `r298_value`: `docs/visexp/out/paper-value-novelty-r298/value-novelty-synthesis.json`
- `r300_query`: `docs/visexp/out/operation-query-utility-r300/query-utility-report.json`
- `r301_task`: `docs/visexp/out/operation-analyst-task-r301/analyst-task-report.json`
- `r302_ranking`: `docs/visexp/out/operation-analyst-ranking-r302/ranking-report.json`
- `r303_agent_session_exchange`: `docs/visexp/out/agent-trace-exchange-r303/exchange-report.json`
- `r304_case`: `docs/visexp/out/operation-case-study-r304/case-study-report.json`
- `r305_baseline`: `docs/visexp/out/operation-case-baseline-r305/case-baseline-report.json`
- `r306_chrome`: `docs/visexp/out/agent-trace-chrome-exchange-r306/chrome-exchange-report.json`
