# Background And Related Work

Last updated: 2026-07-21T02:04:51-07:00
Source/command: claim-oriented web search, primary paper pages, official repositories and datasets, and full-text checks of the local PDF corpus
Completeness: sufficient to reject generic trajectory-diagnosis, action/dependency-graph, temporal-graph-retrieval, full-fidelity trace-navigation, artifact-lifecycle, object-centric-analysis, reminder injection, trajectory reuse, and harness-attribution novelty; the surviving claim is the objectively measured intervention utility of cross-session workspace evidence beyond equal-budget Raw Retrieval and search controls

## Search Log

| Date | Query/source | Purpose | Result |
|---|---|---|---|
| 2026-07-19 | `automated failure diagnosis agent execution trajectories` | Find direct same-claim work | Found AgentRx, TrajAudit, AgentForesight, AgentLocate, REFLECT, and AgentDiagnose. Generic automated trace diagnosis has high same-claim risk. |
| 2026-07-19 | `repository-level coding trajectory failure diagnosis RootSE` | Find the closest coding diagnosis benchmark | Found TrajAudit and the 102-instance RootSE release. Its investigator-agent retrieval baseline is mandatory for coding failures. |
| 2026-07-19 | `agent harness trace diagnosis repair HarnessFix` | Test whether skill/harness diagnosis is novel | Found HarnessFix, which explicitly attributes failures to harness artifacts and repairs them. A generic harness-debugging claim is not novel. |
| 2026-07-19 | `online auditing earliest decisive error agent trajectory` | Test intervention novelty | Found AgentForesight and AFTraj-2K; early alarm and intervention are already explicit research targets. |
| 2026-07-19 | `agent trajectory controlled replay error attribution` | Find causal localization methods | Found REFLECT, which validates error attribution through controlled intervention and outcome flips. |
| 2026-07-19 | `longitudinal agent multiple sessions diagnosis` | Find work whose unit exceeds one run | Found AgingBench, Cross-Session Threats, and Plans Don't Persist. Cross-session state alone is not novel. |
| 2026-07-19 | `persistent multi-artifact workspace agent benchmark` | Find non-coding workspace workloads | Found OR-Space, with requirements, structured data, code, solver outputs, and stakeholder interactions in a persistent workspace. |
| 2026-07-19 | `trajectory behavioral drivers coding agents 9374` | Find confounds and process metrics | Found Beyond Resolution Rates; task difficulty and model identity are required controls, while read-first and validation behavior are useful precedents. |
| 2026-07-19 | `TRAJEVAL 16758 trajectories` | Find fine-grained process evaluation | Found TRAJEVAL; search/read/edit precision and real-time feedback already establish actionable process diagnostics in coding. |
| 2026-07-19 | `agent observability fault detection benchmark OpenTelemetry` | Test observability-taxonomy novelty | Found AgentTelemetry, a 14-fault, nine-span benchmark/toolkit. Merely adding agent span kinds is not the remaining novelty. |
| 2026-07-19 | Official AAAI-27 Main Technical Track and AI Alignment call | Check venue fit | AI Alignment explicitly lists scalable oversight and practical evaluation tools; this is the strongest current AAAI framing. |
| 2026-07-19 | `object-centric process mining lifecycle conformance` and official OCEL/OCPM/PM4Py sources | Test whether the workspace-lifecycle mechanism is prior art | OCEL 2.0, OC-PM, artifact-centric discovery, and conformance work already model co-evolving objects, lifecycle, interactions, deviations, and performance. Representation novelty is rejected. |
| 2026-07-19 | `process mining software repository AI agents` | Test whether applying OCPM to software or giving its output to an Agent is novel | PM4AA mines GitHub OCELs to generate Agent roles; PMAx has an Agent invoke deterministic PM algorithms and interpret artifacts. Both claims are rejected as standalone novelty. |
| 2026-07-19 | HarnessFix full-text and official repository audit | Fix the strongest RQ3 mechanism baseline | Full HTIR already combines data/control flow, artifact/state effects, and harness anchors and substantially outperforms raw traces on failed-trajectory diagnosis. It is mandatory on compatible RQ3 cases. |
| 2026-07-20 | `graph guided diagnosis runtime intervention LLM agent` | Test action/dependency-graph diagnosis novelty | Found AgentTether: Transition Units, Critical Transition Graph, HGT/Isolation-Forest localization, repair memory, and intervention. Graph-guided Agent diagnosis has high same-claim risk. |
| 2026-07-20 | `long horizon agent trajectory search segment retrieval aggregation` | Find a strong scalable Raw interface | Found AggAgent: full-fidelity trajectory navigation through solution retrieval, lexical search, and exact segment reads under one-context cost. This is the mandatory Raw Retrieval interface precedent. |
| 2026-07-20 | `dynamic graph RAG event temporal reasoning` | Test event-centric temporal retrieval novelty | Found DyG-RAG: dynamic event units, temporal/dependency graph, time-aware traversal, and temporal QA. Event graphs and temporal traversal are not novelty. |
| 2026-07-20 | `graph retrieval personalized PageRank long term memory` | Find a non-ad-hoc graph-ranking precedent | Found HippoRAG (NeurIPS 2024): knowledge graph plus Personalized PageRank. PPR may be absorbed as a standard optional retriever but cannot be claimed. |
| 2026-07-20 | Primary-source recheck of AggAgent, AgentTether, and OCEL 2.0 for the algorithm/baseline/ad-hoc audit | Decide which parts are established machinery and whether the current comparison is scientifically fair | Confirmed that long-trajectory search/segment access, dependency-graph diagnosis, and event-object lifecycle models are prior art. The remaining method must be presented as a conservative source-linked workspace index whose value is measured under resource-bounded supervision, not as a novel graph or information source. |
| 2026-07-21 | `long running agent benchmark persistent workspace multi round deterministic oracle` plus official Harness Bench repository audit | Replace forbidden human gold with an executable outcome | Harness Bench has six suitable deterministic multi-round tasks; its Codex adapter starts a fresh top-level session each round over one persistent workspace. Task 007 was excluded because it tests same-conversation memory. |
| 2026-07-21 | `agent harness optimization past trajectories self supervised` and `trajectory memory intervention long horizon agent reminder` | Test whether label-free supervision or reminder injection is novel | RHO already optimizes harnesses without external labels; Remember When It Matters already injects trajectory-grounded reminders. Neither is a standalone novelty claim. |
| 2026-07-21 | `harness evolution matched feedback inference budget held out tasks` | Identify the strongest confound for a closed-loop experiment | Rethinking Harness Evolution shows that extra search/feedback and benchmark overfitting can explain apparent gains. Matched generic/search controls and held-out task families are mandatory. |
| 2026-07-21 | Official SWE-Interact, SWE Context Bench, CORE-Bench, and RE-Bench sources/repositories | Select objective coding and auto-research expansions | SWE tasks provide official repository tests; CORE-Bench provides scientific reproducibility questions over 270 tasks; RE-Bench provides seven continuous-score R&D environments and transcripts. |

## 2026-07-21 Frontier Revision

The author rejected all human annotation for the current study. The prior
four-pathology classification and evidence-set scoring program is therefore
historical, not active. Agent-generated labels are also rejected because they
would make truth circular.

The active scientific test is closed-loop supervision. At a frozen benchmark
checkpoint, the same automatic supervisor observes either complete Raw
Retrieval or the same Raw evidence plus a deterministic, source-linked
workspace trajectory. It emits one bounded intervention or abstains. The same
worker then continues from byte-identical workspace forks, and an official
executable grader measures the realized effect. No LLM judge defines the
primary outcome.

The detailed current audit is
`docs/tmp/bootstrap/step-0001-20260719T181243-0700/literature-20260721T020451-0700/literature-report.md`.
The Harness Bench task-058 mechanics preflight completed, but its supervisors
made zero evidence-tool calls. A preregistered six-task no-op screen then failed
the 4/6 headroom gate, so no effect matrix was admitted. The next evidence node
must qualify a distinct workload prospectively: SWE Context Bench only if it
preserves persistent related-task lineage, and CORE-Bench only if its official
runner supports a fresh-session checkpoint and unchanged executable scoring.

## PDF Corpus

| Work | Local PDF path | Verification status | Why kept |
|---|---|---|---|
| AgentDiagnose (Ou et al., 2025) | `docs/reference/2025-ou-agentdiagnose.pdf` | Full PDF read/searchable; ACL metadata verified | Closest published diagnostic toolkit and competency-metric precedent. |
| AgentRx (Barke et al., 2026) | `docs/reference/2026-barke-agentrx.pdf` | Full PDF read/searchable; official Microsoft repository verified | Closest domain-general failure localization system and strongest invariant-based baseline. |
| TrajAudit (Wang et al., 2026) | `docs/reference/2026-wang-trajaudit.pdf` | Full PDF read/searchable; RootSE dataset verified | Closest repository-level investigator-agent diagnosis system. |
| HarnessFix (Chen et al., 2026) | `docs/reference/2026-chen-harnessfix.pdf` | Full PDF read/searchable | Direct overlap with harness-aware attribution and repair. |
| AgentForesight (Zhang et al., 2026) | `docs/reference/2026-zhang-agentforesight.pdf` | Full PDF read/searchable; official project and AFTraj-2K verified | Closest online auditor and intervention-decision baseline. |
| REFLECT (Lin et al., 2026) | `docs/reference/2026-lin-reflect.pdf` | Full PDF read/searchable | Strong protocol for validating attribution with interventions instead of judge agreement alone. |
| TRAJEVAL (Kim et al., 2026) | `docs/reference/2026-kim-trajeval.pdf` | Full PDF read/searchable | Establishes search/read/edit diagnostics at scale and actionable feedback. |
| Beyond Resolution Rates (Mehtiyev and Assunção, 2026) | `docs/reference/2026-mehtiyev-behavioral-drivers.pdf` | Full PDF read/searchable | Establishes task/model confounds and behavioral-process controls over 9,374 traces. |
| OR-Space (Zhou et al., 2026) | `docs/reference/2026-zhou-or-space.pdf` | Full PDF read/searchable; official code/data identified | Best current multi-artifact, non-coding workspace workload. |
| Your Agents Are Aging Too (Zhu et al., 2026) | `docs/reference/2026-zhu-agent-aging.pdf` | Full PDF read/searchable; official AgingBench repository identified | Closest longitudinal, multi-session mechanism-diagnosis benchmark. |
| Cross-Session Threats (Azarafrooz, 2026) | `docs/reference/2026-azarafrooz-cross-session-threats.pdf` | Full PDF read/searchable; CSTM-Bench verified | Shows that session-local inspection can miss aggregate cross-session signals and supplies a bounded-memory precedent. |
| Plans Don't Persist (Mehta and Datta, 2026) | `docs/reference/2026-mehta-plans-dont-persist.pdf` | Full PDF read/searchable | Supports the claim that task-critical process state can disappear across context management. |
| AgentTelemetry (Balusu, 2026) | not locally available; OpenReview `owdmAYFk6k` | Primary OpenReview PDF text and AIware acceptance page verified; local download returned HTTP 403 | Closest fault-detection observability taxonomy and instrumentation benchmark. |
| OCEL 2.0 (Berti et al., 2024) | `docs/reference/2024-berti-ocel-2-spec.pdf` | Full PDF read/searchable; official standard verified | Establishes the event/object/relationship/attribute-history data model; prevents a representation-novelty claim. |
| OC-PM (Berti and van der Aalst, 2022) | `docs/reference/2022-berti-ocpm.pdf` | Full PDF read/searchable; OCPM and PM4Py tools verified | Establishes lifecycle, interaction, discovery, filtering, feature, and conformance capabilities. |
| Object-Centric Conformance Alignments (Gianola et al., 2024) | `docs/reference/2024-gianola-object-centric-conformance.pdf` | Full PDF read/searchable | Establishes identity-aware multi-object deviation localization against normative process models. |
| PM4AA (Bala et al., 2026) | `docs/reference/2026-bala-process-mining-agents.pdf` | Full PDF read/searchable; `liorlimonad/pmaa` named in paper | Applies object-centric/imperative/declarative mining to software-repository records and generated Agent roles. |
| PMAx (Antonov et al., 2026) | `docs/reference/2026-antonov-pmax.pdf` | Full PDF read/searchable; ProMoAI/PMAx artifacts named in paper | Establishes an Agent consuming deterministic process-mining artifacts rather than raw logs. |
| AgentTether (Zhao et al., 2026) | `docs/reference/2026-zhao-agenttether.pdf` | Full PDF read/searchable; anonymous artifact URL named but no cloneable public repository verified | Closest graph-guided diagnosis, localization, repair-memory, and intervention mechanism. |
| AggAgent (Lee et al., 2026) | `docs/reference/2026-lee-aggagent.pdf` | Full PDF read/searchable; official `princeton-pli/AggAgent` repository HEAD pinned | Strongest full-fidelity, bounded, Agent-operated long-trajectory navigation precedent. |
| DyG-RAG (Sun et al., 2025) | `docs/reference/2025-sun-dygrag.pdf` | Full PDF read/searchable; official `RingBDStack/DyG-RAG` repository HEAD pinned | Establishes event-centric temporal graphs and time-aware graph retrieval. |
| HippoRAG (Gutiérrez et al., 2024) | not downloaded locally | NeurIPS proceedings and official `OSU-NLP-Group/HippoRAG` repository verified | Establishes Personalized-PageRank graph retrieval; absorbable standard ranking baseline. |

## Closest-Mechanism Closure

The detailed second-pass report is
`docs/tmp/bootstrap/step-0001-20260719T181243-0700/literature-20260719T211048-0700/literature-report.md`.
The subsequent graph-diagnosis/retrieval audit is
`docs/tmp/bootstrap/step-0001-20260719T181243-0700/literature-20260720T015952-0700/literature-report.md`.

Object-centric process mining already supplies a standard event/object model,
artifact lifecycles, object interactions, discovery, feature extraction,
performance analysis, and conformance checking. PM4AA already applies this
family to software-repository records, and PMAx already lets an Agent interpret
deterministically computed process artifacts. HarnessFix supplies the closest
structured-diagnosis comparison: Raw Trace, Raw + Data Flow, Raw + Data/Control,
and Full HTIR with artifact/state effects and harness anchors.

The surviving claim is not a new lifecycle representation. It is whether
cross-session persistent-workspace evolution improves the *executed outcome*
of a bounded automatic supervisor intervention beyond complete Raw Retrieval
and matched extra inference. Required primary controls are no intervention,
generic matched reflection/search, and equal-budget Full Raw Retrieval. State
Diff, Session Local, OCPM Features, and Full HTIR are conditional ablations or
external mechanism comparisons, not substitutes for that primary contrast. An
OCEL adapter is evaluation glue only; `agent-session` remains the production
source abstraction.
AgentTether further rules out action/dependency graphs and graph-guided diagnosis
as novelty. AggAgent rules out weak static Raw serialization: the strongest Raw
baseline must offer full-fidelity search and exact segment reading under the
same budget. DyG-RAG and HippoRAG rule out temporal graph traversal and PPR as
novel mechanisms.

## Claim-Oriented Novelty Map

| Claim | Closest prior work | Same-claim risk | Novelty delta | Baselines implied | Expansion opportunity |
|---|---|---|---|---|---|
| An automatic Agent can diagnose a failed trajectory. | AgentRx, TrajAudit, AgentLocate, AgentDiagnose | High | None by itself. | LLM judge, AgentRx, TrajAudit | Make failure diagnosis one evaluation slice, not the main novelty. |
| An auditor can identify an early intervention point. | AgentForesight; REFLECT | High | None by itself. | AgentForesight-style prefix auditor; retrospective judge | Test whether workspace state helps before and after explicit failure. |
| Trace evidence can diagnose harness defects. | HarnessFix | High | None for diagnosis alone. The remaining question is whether exact workspace evolution changes a later worker's objectively graded outcome. | HarnessFix protocol on compatible cases | Treat harness repair as a downstream intervention, not semantic gold. |
| Structured telemetry exposes faults hidden from ordinary spans. | AgentTelemetry | High | Workspace artifact evolution is external persistent state, not another orchestration span taxonomy. | OTel/GenAI spans, full agent spans | Combine native actions with realized workspace effects when native traces are incomplete. |
| Cross-session evidence matters. | Cross-Session Threats; AgingBench; Plans Don't Persist | Medium to high | Existing work studies security aggregation or memory aging, not how autonomous work transforms a persistent multi-artifact workspace. | session-local, full log, bounded-memory reader | Define longitudinal process states and test their incremental diagnostic value. |
| Persistent workspace state is a benchmark setting. | OR-Space | Medium | OR-Space evaluates task success; it does not isolate intervention utility of workspace history against same-source Raw access. | Official executable outcomes and logs | Reuse only if a real pause/fresh-session/continue protocol is possible. |
| Ordered artifact evolution adds intervention value beyond logs and counts. | TRAJEVAL; Beyond Resolution Rates; AgentDiagnose | Medium | The remaining delta is realized continuation utility from cross-session lifecycle, locality, revisitation, validation linkage, and transitions under equal information budgets. | Full Raw Retrieval; no-op; generic matched control | This is the leading falsifiable claim. |
| A queryable workspace trajectory improves supervisor-Agent oversight at fixed budget. | TrajAudit investigator, AgentRx IR, AgentForesight auditor | Medium | Test objective downstream outcome rather than semantic diagnosis agreement. | strongest tool-using Raw supervisor plus generic and no-op controls | If supported, this is the AAAI Alignment contribution. |
| A dependency graph localizes failure-critical Agent actions. | AgentTether | High | None as a generic claim. The remaining delta is exact persistent-workspace effects across independent top-level sessions/goals. | AgentTether on compatible failed-run cases or a faithful CTG relation/feature comparison | Use run-level CTG as the strongest structured-diagnosis competitor. |
| Full-fidelity long trajectories can be inspected within one context through tools. | AggAgent | High | None as an interface claim. | AggAgent-style search plus exact segment/read-record Raw interface | Make the Raw baseline competent and scalable instead of truncating it. |
| Temporal event graphs or graph ranking improve retrieval. | DyG-RAG; HippoRAG | High | None by itself. | lexical search; temporal traversal; optional PPR | Use established ranking only if deterministic queries are insufficient, and ablate it. |
| A separate Agent can inject trajectory-grounded guidance that improves a long-horizon worker. | Remember When It Matters | High | None as a generic reminder/intervention claim. | selective reminder, always-on reminder, advisor-only, general retrieval | Isolate realized cross-session workspace evolution against the same-source Raw interface. |
| Past trajectories can improve an Agent harness without human labels. | RHO | High | None as a label-free harness-optimization claim. | self-preference harness optimization; no-op | Keep harness optimization outside RQ1; test per-checkpoint supervision through official outcomes. |
| Workspace-centered supervision improves subsequent objective task outcomes. | Remember When It Matters; REFLECT; SWE Context Bench | Medium to high | The remaining delta is a matched Raw-versus-workspace-evolution comparison across fresh sessions and persistent heterogeneous artifacts. | Full Raw Retrieval; no intervention; generic matched reflection/search | This is the revised leading falsifiable claim. |

## Closest Work

| Work | Claim | Method/artifact | Evaluation | Same problem/mechanism/metric/setting? | Gap relative to this project |
|---|---|---|---|---|---|
| AgentRx | Domain-general automatic critical-step and failure-category diagnosis | Raw log → trajectory IR → synthesized invariants → checker → LLM judge | 115 failed traces from Tau-bench, Flash, and Magentic-One | Same automatic diagnosis and evidence; run-level failed traces | No cross-session persistent-workspace evolution; primarily critical failures, not ongoing progress and waste. |
| TrajAudit | Repository coding traces need filtering, priors, and investigator retrieval | Noise filter, test-failure prior, tool-using investigator | RootSE, 102 real coding failures in current dataset/PDF | Same coding setting, supervisor-agent retrieval, localization/cost metrics | Repository run is still the unit; depends on observed failure and does not model multi-session artifact lifecycle. |
| HarnessFix | Trace/harness provenance can locate and repair harness flaws | Harness-aware IR with control/data flow and repair mapping | Four agent benchmarks, held-out repair gains | Same harness-diagnosis ambition | Focuses run-level harness artifacts and repair; not longitudinal waste or success-with-pathology across a workspace. |
| AgentForesight | Online auditor should alarm at the earliest decisive error | Prefix-only 7B auditor trained with RL; AFTraj-2K | 2,276 safe/unsafe traces over coding, math, and agentic tasks | Same intervention decision, but predominantly multi-agent run prefixes | Does not use persistent workspace state or cross-session artifact evolution. |
| REFLECT | Attribution should be validated by controlled repair, not only localization labels | Hypothesis generation, intervention replay, outcome-feedback refinement | Four localization benchmarks | Same attribution validity concern | Supplies protocol rather than the workspace-centered representation. |
| AgentDiagnose | Outcome metrics miss process competencies | Five automatic competency metrics and diagnostic visualizations | 30 annotated web traces; training-data filtering | Same motivation and some process measures | Session trajectories, no persistent workspace or same-budget supervisor query evaluation. |
| TRAJEVAL | Search/read/edit stage quality predicts and improves coding success | Gold-patch-aligned precision/recall and online feedback | 16,758 code trajectories | Same process diagnosis in coding | Requires reference patches and operates within runs; does not handle cross-session artifact lifecycle or non-code artifacts. |
| Beyond Resolution Rates | Behavioral structure, task difficulty, and model identity explain outcomes | Large-scale observational analysis | 9,374 traces, 19 agents, 500 tasks | Same behavioral signals and confounds | Observational association rather than evidence-linked diagnosis of an ongoing persistent workspace. |
| AgingBench | Long-lived agent reliability needs longitudinal mechanism diagnosis | Temporal dependency graphs and counterfactual probes | About 400 runs spanning 8–200 sessions | Same longitudinal unit and diagnosis | Focuses memory-pipeline aging rather than workspace transformation and artifact process. |
| Cross-Session Threats | Session-bound detectors miss distributed behavior | Full-log and bounded-memory coreset readers | CSTM-Bench, 54 scenarios per split | Same cross-session evidence bottleneck | Security-specific messages rather than workspace actions and long-running productive work. |
| OR-Space | Realistic agents operate in persistent multi-artifact workspaces | Full-lifecycle operations-research benchmark | Requirements, data, code, solver feedback, and interactions | Same persistent-workspace setting | Evaluates task performance, not process pathology or automated oversight. |
| AgentTelemetry | Agent-specific spans make more faults structurally detectable | 14 faults, nine span kinds, seven framework adapters | 2,940 controlled configurations and SWE-bench case study | Same observability/fault-detection motivation | Instrumentation taxonomy rather than cross-session realized artifact state. |
| AgentTether | Failure-critical subtrajectories can be localized over a dependency-aware graph and turned into guided recovery | Transition Units, Critical Transition Graph, offline HGT, run-local Isolation Forest, analyst and repair memory | 261 tau-bench tasks; Qwen3.7-max and GPT-5.4 transfer | Same graph-guided automatic diagnosis and intervention mechanism; run-level tool/API state | No exact persistent workspace across top-level sessions/goals or equal-budget Raw retrieval comparison. |
| AggAgent | Long trajectories should remain external and be inspected on demand | `get_solution`, ROUGE-L `search_trajectory`, exact `get_segment` | Six benchmarks and three model families | Same long-context access bottleneck; different aggregation task | Supplies the Raw interface precedent, not the workspace diagnosis method. |
| DyG-RAG | Event-centric temporal graphs support time-aware retrieval | Dynamic Event Units, entity/time links, timeline traversal, Time CoT | Temporal QA benchmarks | Same temporal graph/retrieval mechanism; different evidence and task | Eliminates event-graph novelty but not persistent-workspace diagnosis. |
| HippoRAG | Graph plus PPR enables efficient multi-hop long-term-memory retrieval | Knowledge graph and Personalized PageRank | Multi-hop QA | Same graph-ranking family; different task | PPR is optional standard machinery, never the contribution. |
| Remember When It Matters | A separate memory Agent should selectively inject trajectory-grounded reminders | Structured memory bank plus a proactive reminder/abstention policy | Terminal-Bench 2.0 and tau2-Bench outcome gains | Same active-intervention shape; different evidence representation | Prevents an intervention novelty claim; requires raw-vs-workspace evidence isolation. |
| RHO | Harnesses can be optimized self-supervised from past rollouts | Coreset selection, parallel re-solving, self-validation, self-preference | SWE-Bench Pro plus technical and knowledge work | Same no-human-label motivation; optimizes a global harness rather than one continuation | Strong external label-free alternative and RQ3 threat. |
| Rethinking Harness Evolution | Harness evolution must beat simple search under matched feedback/inference budgets and held-out tasks | Matched test-time-scaling/discovery comparisons | Terminal-Bench 2.1 with frontier models | Same evaluation-confound problem | Makes generic reflection/search and task-family-held-out tests mandatory. |
| SWE Context Bench | Agents can reuse full trajectories or summaries across related repository tasks | Related-task sequences with oracle/autonomous retrieval | 300 base plus 99 related SWE tasks | Same shared-workspace/history access problem in coding | Experience reuse is prior art; useful objective workload and baseline. |

## Mandatory Baselines

| Baseline | Official artifact/version | Runnable status | Visible input/information | Tuning surface/budget | Evaluation protocol | Reproduction risk | Fairness notes | Claim consequence if unavailable |
|---|---|---|---|---|---|---|---|---|
| No intervention | Official benchmark prompt and frozen workspace checkpoint | Runnable | No supervisor evidence or message | Zero supervisor budget | Official executable outcome | Low | Byte-identical checkpoint fork | Required to measure benefit and intervention harm. |
| Generic matched reflection/search | Same supervisor/worker models and inference budget, no historical evidence | Runnable through thin adapter | Current task and checkpoint only | Match total inference/time/continuation budget | Official executable outcome | Low | Prevent extra inference from masquerading as representation value | Required primary control. |
| Per-session summaries | Native or fixed summarizer output | Runnable | One summary per prior session | Fixed summarizer model and matched total budget | Executed continuation and official outcome | Low to medium | Generate once and freeze | Useful reduced-information baseline after RQ1 admission. |
| Full raw log with retrieval tools | `agent-session` source logs plus an AggAgent-style search/exact-segment/exact-record interface; official `princeton-pli/AggAgent` HEAD `9638f7d88aee01eb636c02841e13a05bb2e3c449` as the interface precedent | Runnable after thin tool wrapper | Complete native/system/snapshot/evaluator/specification evidence within matched scope | Same rendered-token/byte and tool-call budget as trajectory condition | Same supervisor model, prompt, output schema | Medium | No static context flood or truncation; preserve full-fidelity on-demand access | If trajectory cannot beat this on accuracy, it must win materially on cost/evidence reliability. |
| AgentTether / Critical Transition Graph | arXiv:2607.06273; anonymous paper artifact not yet cloneable | Paper method fully audited; runtime availability unresolved | Run-level Transition Units and temporal/dependency/shared-artifact/error edges | Native published settings when runnable; otherwise a field-mapped relation/feature reproduction only on compatible cases | Failure localization/diagnosis and repair recommendation | High until artifact is public | Do not claim direct numerical superiority across incompatible domains | Required closest structured-diagnosis comparison or explicit incompatibility boundary. |
| Simple counts and time series | Deterministic action/session/artifact statistics | Runnable | Counts and durations | Same supervisor and continuation protocol | Official executable outcome | Low | No semantic labels | Conditional RQ2 ablation after a primary effect. |
| AgentRx | `microsoft/AgentRx`, current 2026 public release | Official code and samples runnable; endpoint adaptation needed | Normalized run trajectory, policy/tool schemas | Match judge model where possible; report API differences | Critical-step/category accuracy on compatible failed traces | Medium | Do not claim direct numerical superiority if domains/schema differ | Required direct mechanism comparison on compatible failure subset. |
| TrajAudit/RootSE | RootSE Hugging Face release; paper investigator design | Dataset available; complete official code not yet verified | Filtered coding trace plus test-failure prior and on-demand retrieval | Same diagnosis model and token accounting | Exact/tolerant localization and category accuracy | Medium to high | Implement only if official code remains unavailable; label as reproduction | Required on repository-level coding failures. |
| AgentForesight | `ZBox1005/AgentForesight`, AFTraj-2K | Official code/dataset identified | Prefix trajectory | Use released checkpoint and native protocol | Earliest-decisive-error alarm and intervention metrics | Medium | Only mandatory if the paper retains online intervention as a headline claim | Without it, narrow RQ1 to retrospective diagnosis and intervention recommendation. |
| TRAJEVAL stage metrics | Paper definitions and compatible code traces | Reimplementation likely | Search/read/edit relative to reference patch | Deterministic | Process-stage diagnostic accuracy/correlation | Medium | Applies only when a gold patch exists | Necessary coding-specific feature baseline, not a cross-domain method. |
| Selective trajectory-grounded reminder | Remember When It Matters protocol | Paper protocol available; artifact status to verify | Structured memory/reminder evidence | Native paper budget where compatible | Official task success and abstention/harm | Medium | External mechanism comparison only on compatible tasks | Required if the paper claims active reminder policy novelty; otherwise cite and narrow. |

## Experimental Precedents And External Assets

| RQ/claim | Accepted paper/protocol citation | Official benchmark/dataset/software/test tool | Version/artifact | Real-world provenance | Reusable design | Required deviation or glue |
|---|---|---|---|---|---|---|
| RQ1 diagnosis/localization | AgentRx; TrajAudit; AgentDiagnose | AgentRx repository and RootSE dataset | 2026 public releases | Tau/Flash/Magentic-One and SWE maintenance traces | Critical step/category labels and evidence reports | Add non-failure states, cross-session scope, and matched tool budgets. |
| RQ1 intervention | AgentForesight; REFLECT | AFTraj-2K and intervention replay protocol | 2,276 trajectories | Coding, math, and agentic executions | Prefix alarm and outcome-flip validation | Bind interventions to workspace evidence; separate recommendation from executed intervention. |
| RQ2 incremental process signal | Beyond Resolution Rates; TRAJEVAL | 9,374-trace analysis protocol; 16,758 coding traces | 2026 papers | Multi-agent/model SWE-bench-family runs | Difficulty/model controls, stage metrics, grouped splits | Add lifecycle, cross-session, and workspace-state ablations. |
| RQ2 cross-session continuity | Cross-Session Threats; AgingBench | `intrinsec-ai/cstm-bench`; `VITA-Group/AgingBench` | 2026 public datasets/code | Synthetic/security sessions and controlled long-lived agents | Session-local vs aggregate readers; temporal DAGs; counterfactual probes | Replace message-only state with artifact effects and productive-work diagnoses. |
| RQ3 non-coding generalization | CORE-Bench; OR-Space | Official repositories and evaluators | 2026 public code/data | Scientific reproduction and operations-research workflows | Persistent multi-artifact tasks and executable outcomes | Require a real structural pause, fresh-session continuation, unchanged evaluator, and prospective headroom gate. |
| Observability coverage | AgentTelemetry; AgentSight | AgentTelemetry anonymous artifact; AgentSight native/eBPF sources | 2026 and AgentSight current branch | Controlled faults and local real agents | Fault injection and native-vs-system evidence coverage | The first paper should keep system binding as an ablation unless missing effects invalidate native traces. |
| Closed-loop RQ1 preflight | Harness Bench | `Qihoo360/harness-bench` | `1025086a446653702b80cfb48babbeec35db6b2c` | Six deterministic multi-round tasks over persistent workspaces | Pause after a prefix round, fork, inject bounded advice, continue, run official oracle | Thin pause/fork/inject adapter; exclude tasks with LLM-weighted outcomes. |
| Coding expansion | SWE-Interact; SWE Context Bench | Official paper/dataset artifacts | 2026 releases | Interactive and related-task repository work | Official tests, evolving requirements, trajectory/summary reuse controls | Keep user simulation and supervisor intervention separate; cluster related tasks. |
| Scientific-work expansion | CORE-Bench; RE-Bench | Official repositories and evaluators | CORE `e32a298...`; RE-Bench `93b9806...` | Paper reproduction and ML research engineering | Objective answers or continuous scores | CORE through current HAL harness; RE-Bench only after cheaper preflight. |

## Baseline Candidates

| Baseline | Why required | Reproduction risk | Fairness notes |
|---|---|---|---|
| Session-local supervisor | Isolates the value of cross-session state. | Low | Same model, prompt, and total evidence budget. |
| Concatenated/full-log supervisor | Tests whether representation matters beyond giving more history. | Medium | Must have equivalent retrieval capability and budget. |
| Bounded raw-log coreset reader | Stronger long-horizon baseline inspired by Cross-Session Threats. | Medium | Preserve chronological ordering and report selection overhead. |
| Workspace snapshot differencing | Tests whether ordered actions add value beyond before/after state. | Low | Same final artifacts and diff metadata. |
| Artifact-lifecycle trajectory without semantic text | Isolates structural workspace signal. | Low | Deterministic projection; no hidden LLM labeling. |
| Full trajectory query service | Proposed condition. | Medium | Every answer must cite source actions and artifact paths. |

## Absorbable Ideas

| Source/community | Idea to absorb | Claim expansion enabled | Experiment implication | Risk |
|---|---|---|---|---|
| TrajAudit | Tool-using investigator retrieves evidence on demand instead of receiving a giant summary. | Makes equal-budget long-horizon diagnosis plausible. | Expose bounded queries over action time, artifacts, sessions, and validation links. | Could look like a domain adaptation unless workspace-specific signal is isolated. |
| AgentRx | Auditable intermediate checks and invariant violations. | Improves evidence grounding and diagnostic transparency. | Require each prediction to cite action IDs and artifacts; evaluate evidence precision/recall. | Generated invariants can leak labels or add model budget. |
| REFLECT | Validate attribution through intervention and replay. | Upgrades correlation into causal evidence for selected cases. | Create controlled harness faults or process disruptions and test whether repairing the cited cause changes outcomes. | Expensive; not all naturalistic failures are replayable. |
| Cross-Session Threats | Treat evidence presentation as an information bottleneck and measure retrieval stability. | Separates representation quality from context length. | Match tokens/tool calls and add session-local/full-log/coreset conditions. | Security-domain metrics do not directly transfer. |
| AgingBench | Temporal dependency graphs and paired counterfactual probes. | Supports mechanism-level longitudinal diagnosis. | Inject controlled write/retrieve/validate omissions across sessions. | Memory aging differs from artifact evolution. |
| Beyond Resolution Rates | Control task difficulty, model identity, and framework identity. | Prevents spurious process claims. | Grouped splits and fixed-effect or mixed-effect analyses. | Requires enough traces per stratum. |
| OR-Space | Persistent heterogeneous artifacts beyond code. | Tests the claimed workspace abstraction. | Include requirements/data/code/results, not only repositories. | Instrumentation and ground truth may require substantial glue. |

## Algorithm And Ad-Hoc Risk Audit

The active method has two separable parts. The first is a deterministic,
source-linked projection from native Agent calls, successful workspace effects,
session boundaries, and frozen workspace checkpoints into ordered
action--artifact relations. The second is an otherwise unchanged supervisor
Agent that chooses queries and emits one bounded continuation intervention or
abstains. No learned classifier, pathology label, anomaly score, graph ranker,
recency decay, hotspot threshold, semantic label, or visualization force belongs
to the research method. The intervention is evaluated only by executing the
forked continuation and running the official benchmark oracle.

This is not information-theoretically new evidence: with unlimited context and
computation, the relations can be reconstructed from the complete Raw store.
The defensible claim is resource-bounded supervisory utility: exact persistent-
workspace relations may make relevant process evidence more reliably accessible
to an automatic supervisor under matched context, response-byte, and tool-call
budgets. A tie in diagnosis with lower retrieval cost is therefore an efficiency
result; only a held-out accuracy, localization, or calibration gain under a
strong matched Raw interface supports the stronger oversight claim.

The non-ad-hoc core should be specified as a small, label-independent relation
algebra over actions, artifact identities/versions, ordered successful effects,
session/goal membership, workspace hierarchy, boundaries, and source-evidence
links. `artifact_history`, `goal_diff`, and `effects` are then derived query
plans over that algebra rather than three privileged features. Every returned
relation must cite Raw IDs, and unresolved ownership remains `unknown`.

The main residual ad-hoc risks are:

- the three current query names were selected before an ablation established
  that they are the minimal useful operators;
- exact argv/CWD/process-subtree ownership is intentionally conservative but
  may trade recall for precision in an implementation-specific way;
- the Raw baseline's lexical ROUGE-L search may be weaker than exact field,
  path, time, or semantic retrieval even though it follows AggAgent's published
  interface precedent;
- fixed token, byte, call, and response ceilings are engineering choices, so a
  single operating point cannot establish robustness;
- selecting checkpoints after observing outcome headroom can manufacture a
  treatment-friendly task slice; and
- giving Trajectory additional precomputed relations can prove interface or
  compression value, but not new source information.

The decisive study must strengthen Raw with the same exact metadata filters
available to the relation index, sweep multiple budgets, and ablate prior-
session history, action order, artifact lifecycle, and workspace transitions
only after the primary Raw-versus-Trajectory intervention contrast shows signal.
No intervention and generic matched reflection/search are required controls.
Related work such as selective memory reminders or self-supervised harness
optimization is compared only on compatible task slices. A learned graph
detector or PPR retriever should be added only after the deterministic comparison
shows signal; established retrieval machinery cannot repair a missing
workspace-history effect.

## Adjacent Communities

| Community/venue family | Why relevant | Keywords/aliases | Useful papers or benchmarks |
|---|---|---|---|
| AI alignment and scalable oversight | Primary claim is an automated supervisor judging long-horizon behavior. | process supervision, scalable oversight, monitorability, auditing, intervention | AgentForesight, REFLECT, AAAI AI Alignment. |
| Agent evaluation and debugging | Supplies diagnosis taxonomies, localization metrics, and baselines. | trajectory diagnosis, root-cause attribution, agent evaluator | AgentRx, TrajAudit, AgentDiagnose, TRAJEVAL. |
| Agent observability and software engineering | Supplies telemetry models and repository traces. | OTel GenAI, agent telemetry, coding-agent behavior | AgentTelemetry, AgentSight, Beyond Resolution Rates. |
| Long-lived agents and memory | Establishes cross-session failure and longitudinal mechanisms. | agent lifespan, memory aging, context compression, cross-session | AgingBench, Plans Don't Persist, CSTM-Bench. |
| Process mining and artifact-centric processes | Natural theory for events that act on multiple evolving artifacts. | object-centric process mining, artifact-centric process model, conformance checking | Search expansion required before the final paper; likely useful for formal representation and anomaly definitions. |
| Software evolution and dynamic graphs | Supports the visualization artifact, not the current core claim. | software evolution visualization, dynamic mental map | Evolution Matrix, History Flow, dynamic graph surveys. |

## Venue Evaluation Patterns

AAAI AI Alignment is the best current target because the official AAAI-27 call explicitly includes scalable oversight and practical evaluation tools. A competitive full paper needs more than a polished observability system: it needs a clearly defined automatic-supervision task, executed interventions with objective outcomes, strong LLM and system baselines, held-out generalization, and evidence that gains persist under matched information and inference budgets. The current AAAI-27 deadline is too near for responsible new empirical results, so the project should follow the next valid AAAI cycle unless a complete dataset and reviewed experiment already exist.

AAAI Demo is a useful secondary route for Agent Nebula and the query interface. It rewards a working system, short paper, video, and live interaction, but cannot substitute for the full scientific claim. IAAI becomes appropriate only after deployment produces measurable operational benefit.

## Must-Read List

1. AgentRx — closest domain-general automated diagnostic pipeline.
2. TrajAudit — closest repository-level investigator-agent baseline and RootSE benchmark.
3. HarnessFix — direct same-claim threat to generic harness diagnosis.
4. AgentForesight — direct same-claim threat to online intervention.
5. REFLECT — strongest causal validation protocol.
6. TRAJEVAL and Beyond Resolution Rates — coding process metrics and confounds.
7. AgingBench and Cross-Session Threats — strongest longitudinal/cross-session precedents.
8. OR-Space — strongest non-coding persistent-workspace workload.
9. AgentTelemetry — observability/fault-taxonomy boundary.
10. AgentTether — closest graph-guided diagnosis and intervention method.
11. AggAgent — strongest full-fidelity bounded trace-navigation interface.
12. DyG-RAG and HippoRAG — temporal graph retrieval and standard graph ranking precedents.
13. Remember When It Matters — strongest active reminder-injection precedent.
14. RHO and Rethinking Harness Evolution — strongest label-free harness alternative and matched-search evaluation warning.
15. Harness Bench, SWE Context Bench, CORE-Bench, and RE-Bench — objective multi-session/workspace evaluation assets.

## Novelty Verdict

- **Overall same-claim risk:** high for generic trajectory diagnosis, action/dependency graphs, temporal graph retrieval, harness diagnosis, reminder injection, trajectory reuse, and online failure localization; medium-to-high for the matched claim that exact cross-session workspace evolution improves the realized utility of automatic interventions beyond complete Raw access.
- **Ambitious target claim:** at a frozen long-horizon benchmark checkpoint, a fixed-budget supervisor using a queryable workspace-centered action trajectory produces interventions whose executed continuations receive better official outcomes than equal-budget Full Raw Retrieval and generic search/reflection controls across coding and scientific workspaces.
- **Claims requiring stronger differentiation or evidence:** cross-session continuity alone, persistent workspaces alone, dependency graphs, interactive trace navigation, and intervention are all already represented in prior work. The paper must isolate the incremental value of exact realized artifact effects across independent goal/session boundaries.
- **Larger claim opportunities:** establish when cross-session workspace evidence yields beneficial intervention, safe abstention, or harm on both coding and scientific work, and later analyze which process relations account for a supported effect.
- **Absorbable ideas to import:** AggAgent-style exact search/segment reading, auditable invariants, intervention replay, temporal dependency graphs, optional standard PPR, and difficulty/model controls.
- **Mandatory primary controls:** no intervention, generic matched reflection/search, and AggAgent-style full-fidelity Raw Retrieval. Session summaries, counts, State Diff, and structured diagnosis systems are secondary or compatibility-specific only after RQ1 admission.
- **Experimental precedents and external assets:** controlled replay from REFLECT; Harness Bench for the immediate persistent-workspace preflight; SWE-Interact/SWE Context Bench for coding; CORE-Bench and RE-Bench for scientific work; and Remember When It Matters/RHO as close intervention alternatives.
- **Next action:** preregister a cross-domain workload qualification. Verify persistent lineage and a fresh-session checkpoint for SWE Context Bench (otherwise SWE-Interact), and pause/resume compatibility with the unchanged CORE-Bench evaluator. Freeze eligibility before no-op headroom, then require matched evidence-tool engagement before any effect matrix. Do not solicit labels or use an LLM judge as primary truth.
