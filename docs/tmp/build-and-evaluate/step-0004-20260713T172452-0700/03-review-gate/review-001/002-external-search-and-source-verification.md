# External Search and Primary-Source Verification

## Node record

- **Started:** 2026-07-14T01:48:16-07:00
- **Completed:** 2026-07-14T01:50:54-07:00
- **Parent:** `001-blind-full-paper-read-and-attack-map.md`
- **Objective:** Attack the paper's load-bearing status-quo, novelty, benchmark, protocol, and venue claims using current primary or official sources.
- **Inputs and provenance:** paper-only attack map; official product/specification documentation; primary papers and official repositories discovered through current web search on 2026-07-14.
- **Method:** searched systems observability and process mining independently from AI-agent monitoring/failure-localization work; opened primary papers, ACL/AAAI proceedings, official benchmark repositories, and official product/specification documentation. Search snippets were used only for discovery, not as final evidence.

## Search questions and queries

| Search question | Representative queries | Included source families | Excluded or qualified |
|---|---|---|---|
| Can current observability aggregate by semantic category and additive measure? | `LangSmith metadata tags dashboards traces official`; `Datadog LLM observability query group tags metrics`; `OpenTelemetry GenAI semantic conventions agent spans metrics` | Official LangSmith, Datadog, OpenTelemetry docs | Product marketing without operational documentation |
| Can pprof express tag-derived hierarchy without AgentProf? | `google pprof tagroot tagleaf official` | Official google/pprof documentation | Blogs and secondary tutorials |
| Does adjacent work already abstract and aggregate trajectories? | `process mining semantic abstraction event logs cross trace`; `process-centric analysis agentic software systems`; `Hodoscope agent observability semantic hierarchy` | Primary event-abstraction paper; PACMPL/arXiv process-centric paper; Hodoscope paper/artifact | Unreviewed announcements are clearly marked; unrelated “profiling” usages excluded |
| Are RQ2 benchmark populations and labels real and appropriate? | exact benchmark titles plus `official`, `paper`, `GitHub`, annotation counts | AgentProcessBench paper/repo; HINTBench paper/artifact; TraceElephant ACL paper/repo | Hugging Face summaries used only to locate official sources |
| What externally grounded RQ3 annotation can be reused? | official GUI/web trajectory annotation and group-boundary sources | OSWorld-Human official repo/paper; event-abstraction primary paper; existing benchmark papers | Generic intent-classification corpora excluded because they are not agent trajectories |
| Is AAAI the correct venue context? | `AAAI 2027 author kit main track official` | Official AAAI-27 conference page | Reddit discussion excluded from scientific/format evidence |

## Verified primary evidence

### Status quo: the paper's categorical gap statements are false as written

1. **LangSmith already supports cross-trace aggregation by tags and metadata.** Its official dashboard documentation says users can group charts by run tag or metadata and its prebuilt dashboards aggregate trace count, latency, errors, tokens, cost, tools, and feedback. Its documentation also states that metadata/tags do **not** automatically propagate between parent and child runs. Source: [LangSmith dashboards](https://docs.langchain.com/langsmith/dashboards) and [tags/metadata](https://docs.langchain.com/langsmith/add-metadata-tags).
2. **Datadog already supports semantic grouping and aggregate measures over agent spans.** Official Agent Observability docs expose span/trace queries by tags and attributes, plus aggregate cost, token, duration, error, tool, and trace statistics; current SDK docs also support propagating chosen span tag keys to metrics. Sources: [querying spans and traces](https://docs.datadoghq.com/llm_observability/monitoring/querying/), [Agent Observability metrics](https://docs.datadoghq.com/llm_observability/monitoring/metrics/), and [SDK reference](https://docs.datadoghq.com/llm_observability/instrumentation/sdk/).
3. **OpenTelemetry defines semantic attributes and agent/workflow/tool operations.** Current official semantics include agent ID/description, conversation ID, workflow name, tool name/type/call data, evaluation labels, and input/output token measures. Source: [OpenTelemetry GenAI attribute registry](https://opentelemetry.io/docs/specs/semconv/registry/attributes/gen-ai/).
4. **Pprof itself can break down sample values by tags and turn `tagroot`/`tagleaf` values into pseudo stack frames.** The paper's claim that this works “only on top of an existing execution stack” is not stated by the official documentation and is too categorical. Source: [google/pprof tag documentation](https://github.com/google/pprof/blob/main/doc/README.md#tags).

These findings strengthen—not shrink—the most defensible novelty statement: AgentProf is not the first system to aggregate tags or attach semantic fields. Its potentially new contribution is **automatically deriving recurring responsibility fields from heterogeneous agent histories, propagating them to additive cross-layer effects, and materializing alternative query-time profile hierarchies in standard profiler form**. The paper should compare against existing tagged aggregation rather than call it impossible.

### Adjacent science: cross-run semantic abstraction already exists

1. Tax et al., *Event Abstraction for Process Mining using Supervised Learning Techniques*, explicitly map low-level events to high-level semantic events from labeled trace subsets and propose sequence-focused evaluation. This is close prior art for RQ3's learning and boundary construct, though it does not provide AgentProf's agent-specific cross-layer additive attribution or standard-profiler interface. Source: [primary paper](https://arxiv.org/abs/1606.07283).
2. Liu et al., *Process-Centric Analysis of Agentic Software Systems* (PACMPL 2026), encode temporal/semantic relations in a graph and analyze 4,000 SWE-agent/OpenHands trajectories to expose phases, repetition, inefficiency, and process differences. This is a major missing closest work for the broad “cross-run agent behavior analysis” claim. Source: [primary paper](https://arxiv.org/abs/2512.02393).
3. Zhong et al., *Hodoscope: Unsupervised Monitoring for AI Misbehaviors*, summarize and embed actions across many traces, compare behavior distributions, and report 6–23× lower review effort for discovering anomalous behavior. This is the closest same-problem neighbor for cross-run semantic behavior grouping and inspection reduction. AgentProf's distinction must be additive responsibility profiling and explicitly chosen operation-stack views, not the mere existence of population-level semantic grouping. Source: [primary paper](https://arxiv.org/abs/2604.11072) and [official artifact](https://hodoscope.dev/).
4. AgentGraph converts traces into linked task/tool/data graphs and supports qualitative/quantitative robustness analysis; it is an AAAI-26 Demonstration paper rather than a full research-paper bar, but it further disproves the claim that all current work is only a raw per-run tree. Source: [AAAI proceedings](https://ojs.aaai.org/index.php/AAAI/article/view/42393).

**Novelty verdict after search:** the exact thesis still identifies a real problem, but the introduction and Related Work currently construct a strawman status quo. Novelty is plausible only at the joint mechanism/evidence level. This remains a `WRITE_GATE`/literature-mapping requirement and does not justify changing the thesis or four RQs.

### RQ2 benchmark verification

| Benchmark | Primary-source facts | Paper claim status |
|---|---|---|
| AgentProcessBench | 1,000 tool-using trajectories, 8,509 human-labeled steps, 89.1% inter-annotator agreement, ternary labels, BFCL/GAIA/HotpotQA/τ-bench coverage in the release. [Paper](https://arxiv.org/abs/2603.14465), [official repository](https://github.com/RUCBM/AgentProcessBench). | Population and independent step-label premise verified. “Consensus” should be used only if the local release/protocol specifically supports that term; the primary abstract reports human labeling and agreement. |
| HINTBench | 629 trajectories total (523 risky, 106 safe; 33 steps average), with trajectory detection, risk-step localization, and failure-type labels under a five-constraint taxonomy. [Paper](https://arxiv.org/abs/2604.13954). | Annotation construct is appropriate for RQ2. The paper's “all 536 released test trajectories” is not explained in its own protocol; the external source alone does not establish why the reported subset is 536, so the local experiment report must supply the split provenance. |
| TraceElephant | ACL 2026 paper reports 380 collected traces and all 220 naturally occurring failures as benchmark instances from Captain-Agent, Magentic-One, and SWE-Agent on GAIA, AssistantBench, and SWE-bench; every failure has an expert-consensus responsible component and decisive step. Initial agreement is α=0.72 component and α=0.64 step. [ACL paper](https://aclanthology.org/2026.acl-long.912.pdf), [official repository](https://github.com/TraceElephant/TraceElephant). | The “all 220 real failed executions” and decisive-step target are verified. The benchmark's step label is recoverability-aware, so reporting it merely as any risky/error step would be incorrect; the current subsection correctly says decisive step. |

All three are legitimate real public anchors. No external finding requires another RQ2 experiment. The main unresolved question is whether AgentProf's local target-blind construction and statistics match the paper; that is checked in the next node from internal artifacts.

### RQ3 construct and reusable external anchors

- The nine plotted datasets mostly expose **source-native action types**, which are operational labels, not automatically high-level phase or task-intent ground truth. The paper cannot infer semantic phase correctness from action-type agreement without an explicit construct mapping.
- OSWorld-Human is a useful existing, citable exception: it supplies manually annotated human reference trajectories and both single-action and grouped-action efficiency scores. Its grouped human actions can provide independently defined boundary structure without authoring a new toy benchmark. Source: [official repository](https://github.com/WukLab/osworld-human) and linked paper.
- The process-mining event-abstraction protocol supplies a published precedent: learn high-level event abstraction from labeled traces and evaluate it with sequence-focused metrics. This is a better methodological citation for leave-family-out tags/boundaries than an arbitrary 0.7 cutoff.
- A newly discovered GUI evaluator, GUIDE, performs semantic trajectory segmentation, but using a new benchmark/model would violate the user's simplicity/reuse preference unless the current OSWorld-Human and existing adapters prove insufficient. It is therefore excluded from the next experiment.

The best reusable RQ3 experiment is consequently not “collect another dataset.” It should rerun the existing AgentProf adapters and tagger over the existing public operation files, use native action identity only for an action-normalization submetric, and use OSWorld-Human's existing grouped human boundaries for the phase/boundary submetric. One experiment can test the fixed RQ3 hypothesis across these already present assets without a new ontology or model.

### Venue verification

The official AAAI-27 page confirms the Main Technical Track and conference schedule. AAAI's stated mission covers research across AI and affiliated disciplines, so a cross-domain agent-observability paper is in scope, but an AAAI reviewer will expect direct AI significance, construct-valid tags, and credible public-dataset evaluation rather than only systems implementation. Source: [AAAI-27 official page](https://aaai.org/conference/aaai/aaai-27/).

## How external evidence changes the attack map

1. The status-quo/novelty issue rises from major to a **submission blocker**: official products and adjacent papers directly contradict broad claims in Introduction, Background, and Related Work.
2. RQ2's public-data foundation becomes stronger. All three data sources are suitable; the result should be judged from the local evidence, not rejected for benchmark choice.
3. RQ3 remains the highest-value next experiment and becomes simpler: reuse current data/adapters/tagger, separate action identity from phase boundaries, and use existing OSWorld-Human human grouping rather than inventing a benchmark.
4. RQ4 remains a later easy reuse experiment. No source makes it higher scientific priority than RQ3.

## Sources/artifacts and inclusion rationale

The source set spans official product behavior, standards, profiler behavior, peer-reviewed/accepted closest work, primary arXiv work where publication is not yet available, and official benchmark artifacts. It intentionally includes evidence against the paper. Search did not attempt a comprehensive systematic review of process mining; the uncovered same-problem branches are sufficient to show that the current novelty text is incomplete. A later `research-literature-novelty` pass should map this branch before submission.

## Paper/claim impact, alternatives, and decision

- Preserve the exact thesis and four RQs.
- Replace categorical “cannot aggregate” statements with the larger and more defensible challenge: existing tools require application-supplied tags and run structure, while AgentProf derives and propagates recurring semantic responsibility across heterogeneous histories and system effects.
- Cite and distinguish process mining, Process-Centric Analysis, Hodoscope, and current product aggregation.
- Do not add a new RQ2 scheme.
- Provisional next experiment remains one complete reused-asset RQ3 validation.

## Tree/search and project-memory updates

- **Closed branch:** “existing observability cannot aggregate tags” is false.
- **Opened branch:** joint novelty = derived semantic responsibility + cross-layer additive attribution + query-time profiler hierarchy.
- **Opened RQ3 branch:** action identity and phase boundary are separate scoreable constructs using existing sources.
- **Project-memory proposal:** related-work map should eventually record the four closest branches, but REVIEW itself must not edit canonical memory.

## Completion assessment and next node

Mandatory current external search is complete and source-grounded. Next node: read the canonical evaluation/background and Step 0004 experiment/write reports, then reread the entire paper and reconcile internal evidence with this external attack.
