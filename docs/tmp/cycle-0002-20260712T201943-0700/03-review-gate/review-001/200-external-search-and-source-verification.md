# Review 001 / Node 200: External Search and Source Verification

## Context and status

- **Timestamp:** started 2026-07-13T10:47:08-07:00; completed 2026-07-13T10:56:00-07:00.
- **Phase / step / gate:** `BUILD_AND_EVALUATE` / cycle 0002 / `REVIEW_GATE`.
- **Parent:** `100-blind-full-paper-read-and-attack-map.md`.
- **Node status:** complete for the declared source-search scope.
- **Isolation:** this search began only after the blind paper-only attack map was committed. Before searching, I reread `docs/user-instruction.md` in full. I still did not read project narrative/evaluation memory, questions for the author, prior reviews, or current experiment/write-gate reports.
- **Target:** AAAI-27 Main Track, assessed as a cross-domain AI/systems submission.

## Objective

The purpose of this node is to test, rather than decorate, the paper-only judgment against external evidence. I separately searched systems work, AI/ML diagnosis and labeling work, and bridging agent-observability products/papers. The required targets were:

1. closest same-claim and same-mechanism work;
2. sources that contradict the manuscript's status-quo claims;
3. stronger baselines and accepted evaluation protocols;
4. official, executable external artifacts suitable for one decisive next experiment;
5. real-world evidence that the problem matters;
6. a potentially larger claim that preserves the exact thesis **“Agent observability needs profiling, not only debugging.”** and all four fixed RQs.

Search findings alter the confidence and priority of attacks, not the fixed thesis or RQ meanings.

## Inputs, provenance, and search method

I used keyword families independently rather than issuing one blended search:

- **Systems:** `data cube group by rollup drill down`, `distributed tracing aggregate diagnosis causal resource attribution`, `Pivot Tracing causal group by`, `workflow-centric tracing resource attribution diagnosis`, `Perfetto SQL aggregate traces`, `pprof tags tagroot tagleaf`, `aggregate distributed traces`, `workflow motifs tracing`.
- **AI/ML:** `agent failure localization benchmark critical step`, `AgentRx`, `trajectory error localization benchmark first error`, `TELBench DRIFT`, `intent classification public dataset CLINC MASSIVE`, `V-measure clustering evaluation`, `agent fault detection benchmark multi-framework`.
- **Bridging/product:** `LLM observability semantic topic clustering cost tokens errors`, `Datadog LLM patterns`, `Langfuse tags metrics`, `LangSmith dashboards group by tags`, `OpenTelemetry GenAI attributes`, `agent semantic profiling`, `AgentTelemetry`, `AgentSight`.
- **Problem/venue:** official OpenAI material about long-running agent workloads/support operations and the official AAAI-27 Main Track call.

I opened the primary paper PDF, author-hosted paper, official documentation, official repository/package page, official conference page, or original dataset repository whenever available. Search-result snippets were used only to discover sources. Vendor documentation is treated as evidence of current product capability, not as peer-reviewed evidence of effectiveness. Recent arXiv papers are explicitly marked as preprints. I excluded secondary blog summaries, SEO pages, Reddit posts, Wikipedia, and generic surveys from the scientific judgment.

The cutoff was sufficiency rather than exhaustiveness: the search stopped after each branch contained a closest mechanism, contradictory evidence, a stronger baseline/protocol, and an external artifact, and further queries mostly returned weaker variants.

## Systems branch

### S1 — Data Cube is the foundational mechanism-level prior art

- **Primary source:** Jim Gray et al., *Data Cube: A Relational Aggregation Operator Generalizing Group-By, Cross-Tab, and Sub-Totals*, Data Mining and Knowledge Discovery; [author/arXiv PDF](https://arxiv.org/pdf/cs/0701155).
- **Verified capability:** the paper formalizes aggregation over multiple dimensions and explicitly unifies group-by, cross-tab, histogram, roll-up, drill-down, and subtotals. Hierarchical multi-resolution views produced by ordered or selected dimensions are therefore not, by themselves, a new data abstraction.
- **Impact on AgentProf:** blind attack B4 strengthens substantially. AgentProf's operation stack, as currently specified, is an ordered tuple projection plus aggregation. The manuscript's claim that a flat `GROUP BY` cannot produce its views attacks an unnecessarily weak alternative. The source does **not** eliminate a contribution based on automatically deriving semantic dimensions, reconstructing cross-layer responsibility, or presenting the same conserved operations through flame-graph tooling. It does eliminate novelty based only on query-time multidimensional hierarchy.
- **Required baseline/positioning:** an information-equivalent cube/roll-up implementation must receive the same derived fields and weights. Any remaining advantage must come from responsibility reconstruction, semantic dimension derivation, useful defaults/induction, or operational integration—not expressiveness of grouping.

### S2 — Pivot Tracing is the closest systems mechanism

- **Primary source:** Jonathan Mace et al., *Pivot Tracing: Dynamic Causal Monitoring for Distributed Systems*, SOSP 2015; [author PDF](https://cs.brown.edu/~rfonseca/pubs/mace15pivot.pdf).
- **Verified capability:** Pivot Tracing dynamically selects, filters, and groups metrics at one execution point using causal context from events elsewhere across component and machine boundaries. It explicitly connects its query model to data cubes/pivot tables and demonstrates diagnosis of real distributed-system problems.
- **Same-mechanism risk:** this is much closer than the manuscript acknowledges. The shared core is query-time aggregation of metrics under causally propagated dimensions. Pivot Tracing has a stronger causal story across distributed components; AgentProf proposes agent-specific semantic fields, offline population views, local LLM tagging, system-effect reconstruction, and flame-graph-compatible ordered projections.
- **Impact:** the source strengthens B3 and B4. The novel delta cannot be “propagate a label and group a metric.” It could be: reconstruct semantic responsibility without application instrumentation across volatile agent/framework boundaries, then expose multiple additive resource/failure views over a population. That delta requires direct correctness evidence under concurrency and missing/ambiguous events.

### S3 — Workflow-centric tracing warns that resource attribution and diagnosis are different constructs

- **Primary source:** Raja R. Sambasivan et al., *Principled Workflow-Centric Tracing of Distributed Systems*, SoCC 2016; [author PDF](https://cs.brown.edu/people/jcmace/papers/sambasivan16principled.pdf).
- **Verified contradictory evidence:** the paper explains that causal workflows are valuable for resource attribution and diagnosis, but reports that infrastructure designed for resource attribution and reused for diagnosis proved ineffective because the two goals impose different design choices.
- **Impact:** this directly strengthens blind attacks B1 and the cross-domain causal-chain objection. The AgentProf manuscript currently assumes one representation that yields both resource attribution (RQ1) and real-problem localization (RQ2), but adds task-specific rankings and policies when it reaches RQ2. Prior systems evidence says this transfer is not automatic. RQ2 therefore needs its own frozen diagnostic construct and outcome rather than being inferred from RQ1's aggregation machinery.
- **What this does not imply:** it does not require changing or dropping RQ2. It requires explicitly designing and evaluating the localization layer while preserving RQ2's exact meaning.

### S4 — Perfetto provides a stronger information-equivalent analysis baseline

- **Primary official sources:** [PerfettoSQL getting started](https://perfetto.dev/docs/analysis/perfetto-sql-getting-started), [trace-based metrics](https://perfetto.dev/docs/analysis/metrics), [Data Explorer](https://perfetto.dev/docs/visualization/data-explorer), and [TracePacket documentation](https://perfetto.dev/docs/reference/synthetic-track-event).
- **Verified capability:** Perfetto supports SQL queries over traces, filters, joins, aggregations, custom derived metrics and visualizations, reusable batch queries over large trace sets, process/thread/async tracks, and combined system/userspace events.
- **Impact:** the paper's flat/session-only baselines are not competitive with contemporary trace analysis. Perfetto is an open, reproducible baseline substrate for equal-information SQL grouping and query budgeting. It also exposes concurrency semantics that AgentProf's inheritance rule currently leaves unspecified.
- **Fair comparison:** AgentProf may still win on automatic semantic fields, operation conservation across heterogeneous sources, population-oriented defaults, or inspection efficiency. The baseline should receive the same raw records and non-semantic native fields; a second parity condition should receive all AgentProf-derived tags to isolate representation/query value from tagger value.

### S5 — pprof already turns tags into stack-like hierarchy

- **Primary official source:** Google pprof, [profile format and command documentation](https://github.com/google/pprof/blob/main/doc/README.md).
- **Verified capability:** pprof supports label filtering/focusing, tag breakdowns, and `tagroot`/`tagleaf`, which insert pseudo stack frames derived from labels.
- **Impact:** the manuscript's statement that pprof labels can only sit “on top of an existing execution stack” is too categorical. pprof does not derive agent semantics or cross-layer ownership, but it can turn labels into stack positions. AgentProf's use of folded stacks and pprof is an implementation compatibility benefit, not a standalone hierarchy novelty claim.

### S6 — Aggregate trace visualization and workflow motifs show the same principle is active elsewhere

- **Primary preprints:** John K. Ousterhout et al., *Visualizing Distributed Traces in Aggregate*; [arXiv](https://arxiv.org/abs/2412.07036). *Workflow Motif: Identifying Frequent Patterns in Distributed Traces*; [arXiv](https://arxiv.org/abs/2506.00749).
- **Verified relevance:** the first explicitly identifies per-trace visualization as inadequate for large trace populations and groups traces to expose representatives. The second searches for frequent cross-request processing patterns and supports hierarchical exploration with performance information.
- **Impact:** these sources support the manuscript's problem diagnosis but weaken any claim that the shift from single trace to population view is itself new. They also suggest stronger aggregate-trace baselines than per-session grouping. Because both are preprints, they should be used as adjacent-work signals, not sole novelty blockers.

### S7 — AgentSight already provides the cross-layer capture and correlation substrate

- **Primary source:** Yusheng Zheng et al., *AgentSight: System-Level Observability for AI Agents Using eBPF*; [arXiv paper](https://arxiv.org/abs/2508.02736) and [official repository](https://github.com/agent-sight/agentsight).
- **Verified capability:** AgentSight captures LLM intent and kernel-visible effects at stable boundaries, correlates them across processes, and reports security/performance case studies with sub-3% overhead.
- **Impact:** AgentProf must clearly identify what is inherited from AgentSight and what is new. Boundary capture and intent/effect correlation are not an AgentProf contribution unless materially redesigned. The plausible new contribution is conserved, population-level profiling over the already correlated event stream. The current paper's shallow interface/correctness description makes that separation hard to audit.

## AI/ML branch

### A1 — AgentRx supplies a stronger real-problem localization protocol and executable baseline

- **Primary sources:** Microsoft, *AgentRx: Diagnosing AI Agent Failures from Execution Trajectories*; [paper PDF](https://arxiv.org/pdf/2602.02475), [official repository](https://github.com/microsoft/AgentRx), and the dataset linked from that repository.
- **Artifact and labels:** 115 failed trajectories from tau-bench, Flash, and Magentic-One are manually annotated with a critical failure step and a ten-category taxonomy. The repository includes normalization, invariant generation/checking, an LLM judge, ground truth, and an end-to-end CLI.
- **Accepted-style metrics:** exact critical-step accuracy, accuracy within ±1/±3/±5 steps, average distance, failure-category accuracy, and repeated-run mean/standard deviation.
- **Impact:** this strongly confirms blind attack B1. AgentProf reports group AP and work-at-five using task-specific group rankings, but does not report whether the actual critical step is found. AgentRx is not information- or cost-equivalent—it uses an LLM diagnosis pipeline—so it should be compared with token, latency, and dollar budgets disclosed. It is still a necessary “best available diagnosis” point or at minimum a protocol anchor.
- **Limit:** AgentRx is trajectory-centric and small, so using it alone would risk creating another benchmark resembling the paper's current six-task evaluation. It is better as a secondary external baseline/protocol than the sole next decisive experiment.

### A2 — TELBench/DRIFT raises the construct-validity bar for semantic-span error localization

- **Primary source:** *TELBench: A Benchmark for Trajectory Error Localization in LLM Agents* and the DRIFT method; [arXiv PDF](https://arxiv.org/pdf/2606.02060).
- **Artifact/protocol:** the authors report 2,790 real trajectories across two frameworks, three models, and three benchmarks, with a 1,000-trajectory expert-annotated semantic-span subset. The annotation process uses two LLM candidates followed by expert adjudication; the paper reports substantial expert effort.
- **Metrics:** macro precision/recall/F1 over error spans and first-error localization accuracy, with error-type analysis. The paper reports that first-error localization remains difficult.
- **Impact:** “locates problems” requires a direct localization target. AgentProf's group-level AP and 18.8% median top-five recall may measure triage concentration, but they cannot substitute for first-error or fault-bearing-span localization. TELBench also shows that semantic segmentation itself needs validation, whereas AgentProf treats group construction as given.
- **Status caveat:** this is a June 2026 preprint, not established accepted work. It is useful as a current protocol and artifact candidate, not as proof of settled community consensus.

### A3 — V-measure does not establish tag semantic accuracy

- **Primary source:** Andrew Rosenberg and Julia Hirschberg, *V-Measure: A Conditional Entropy-Based External Cluster Evaluation Measure*, EMNLP-CoNLL 2007; [ACL Anthology PDF](https://aclanthology.org/D07-1043.pdf).
- **Verified meaning:** V-measure evaluates agreement between a clustering and externally supplied classes through homogeneity and completeness and does not require a cluster-to-class mapping. It is robust to cluster-number differences in a defined sense.
- **Impact:** V-measure is a defensible partition-agreement metric, but it does not show that a tag has the right name, meaning, coverage, calibration, or operational usefulness. A mapping-derived `phase` can partition similarly to native `action` while being semantically wrong or merely re-encoding it. The paper's phrase “tag accuracy” and the 0.7 success threshold are unsupported by this source. Blind attack B2 strengthens.

### A4 — CLINC150 and MASSIVE are proper external RQ3 anchors for natural-language tags

- **Primary sources:** Stefan Larson et al., *An Evaluation Dataset for Intent Classification and Out-of-Scope Prediction*; [ACL paper](https://aclanthology.org/anthology-files/pdf/D/D19/D19-1131.pdf) and [official CLINC150/OOS repository](https://github.com/clinc/oos-eval). Jack FitzGerald et al., *MASSIVE: A 1M-Example Multilingual Natural Language Understanding Dataset with 51 Typologically-Diverse Languages*; [ACL paper](https://aclanthology.org/2023.acl-long.235.pdf) and [official repository](https://github.com/alexa/massive).
- **Verified artifact:** CLINC150 has a fixed ontology of 150 intents across ten domains plus explicit out-of-scope examples and fixed splits. MASSIVE has more than one million utterances, 60 intents, 18 domains, 51 languages, and public splits.
- **Impact:** these are direct tests of natural-language intent tagging, unlike structured action-field mappings. They support macro intent F1/accuracy, coverage/abstention, out-of-scope performance, and robustness across paraphrase/domain/language. They do not test system-effect inheritance, so they address RQ3 only and should not be presented as RQ1 evidence.
- **Priority:** RQ3 remains a blocker, but this is not the highest paper-value next experiment because it would leave real-problem localization and system novelty untouched.

### A5 — AgentTelemetry is the strongest external artifact for a decisive RQ2 experiment

- **Primary sources:** Krishna Chaitanya Balusu et al., *AgentTelemetry: A Fault Detection Benchmark and Toolkit for LLM Agent Observability*; [OpenReview paper](https://openreview.net/pdf?id=owdmAYFk6k), [official PyPI package](https://pypi.org/project/agenttelemetry/), [official repository](https://github.com/agenttelemetry/agenttelemetry), and the [AIware 2026 accepted benchmark/dataset-track program](https://2026.aiwareconf.org/track/aiware-2026/aiware-2026-benchmark---dataset-track).
- **Verified artifact:** the package is Apache-2.0, installable, and supports nine agent-specific span kinds and seven framework adapters: LangChain, CrewAI, AutoGen, Anthropic SDK, OpenAI SDK, LlamaIndex, and a custom API. It includes anomaly detection, cost aggregation, decision attribution, and three privacy levels.
- **Published protocol:** the paper describes 14 faults × five observability conditions × seven frameworks × six repetitions, totaling 2,940 configurations, plus GitHub-issue mining and a SWE-bench Lite case study. The conditions range from no instrumentation through vanilla OpenTelemetry and GenAI attributes to AgentTelemetry metadata/full views. Fault-detection rate is reported by fault and observability condition.
- **Why it is decisive:** this is a real external, accepted, multi-framework benchmark with pre-existing fault taxonomy and observability-level controls. It is structurally different from another custom AgentProcessBench-like collection. It directly tests whether AgentProf's semantic population view improves the real outcome in RQ2 under held-out faults/frameworks and exposes strong OTel baselines.
- **Caveat:** the controlled fault harness uses synthetic/injected faults and some mock-LLM conditions, so the experiment must preserve the official protocol and separately report the included real GitHub/SWE-bench evidence. Fault detection is not automatically localization; the run must use the benchmark's injected fault-bearing span/event or first anomalous span as a predeclared localization target. If the public artifact does not expose that target, the authors must not manufacture labels after seeing results; they should use official fault/run labels for fixed-recall triage and state the granularity precisely.
- **Same-claim pressure:** AgentTelemetry already performs cost aggregation and decision attribution. AgentProf must show what semantic population hierarchy and cross-layer effects add over these functions.

## Bridging product and observability branch

### B1 — Datadog LLM Observability Patterns is the closest same-claim current capability

- **Primary official sources:** [Datadog LLM Observability Patterns](https://docs.datadoghq.com/llm_observability/monitoring/patterns/) and [LLM cost monitoring](https://docs.datadoghq.com/llm_observability/monitoring/cost/).
- **Verified capability:** Patterns automatically clusters production LLM interactions with semantic summaries and a hierarchy of topics/subtopics, then shows interaction volume, cost, tokens, errors, latency, evaluations, and trace drilldown per cluster. The cost feature aggregates cost across traces/apps and supports bounded custom span tags.
- **Direct contradiction:** the manuscript says input clustering only characterizes input distributions. Datadog's official product documentation explicitly couples semantic topic hierarchies to resource and error metrics. It also contradicts a universal claim that request tags do not propagate to downstream cost aggregation.
- **Limits and plausible AgentProf delta:** Datadog's documented pattern run is capped at 10,000 records, is vendor-controlled, and operates primarily on application/LLM spans. AgentProf may offer offline/local processing, OS and process effects, open artifacts, arbitrary query-time ordered dimensions, conserved cross-layer responsibility, and pprof compatibility. Those distinctions are potentially important but are not directly evaluated in the manuscript.
- **Impact:** novelty/framing risk rises to blocker level unless the related-work and baseline story acknowledge this capability. The exact thesis can remain unchanged, but “profiling” must mean more than semantic topic clustering plus metrics.

### B2 — Langfuse and LangSmith already offer tag/metadata-sliced population metrics

- **Primary official sources:** [Langfuse tags](https://langfuse.com/docs/observability/features/tags), [Langfuse metrics](https://langfuse.com/docs/metrics/overview), [Langfuse Metrics API](https://langfuse.com/docs/api-and-data-platform/features/metrics-api), [LangSmith dashboards](https://docs.langchain.com/langsmith/dashboards), and [LangSmith cost tracking](https://docs.langchain.com/langsmith/cost-tracking).
- **Verified capability:** Langfuse propagates tags to observations/traces and slices latency, token, and cost metrics by user, session, geography, feature, model, and prompt version. LangSmith groups trace/run metrics by tags, metadata, names, and types and supports custom-run cost aggregation.
- **Nuance:** LangSmith documentation notes that metadata/tags are not necessarily automatically propagated across parent-child runs unless attached appropriately, so the paper's propagation criticism is partly valid for some tools. Neither source establishes automatic natural-language semantic tagging or OS-effect ownership.
- **Impact:** the status quo is not “single-trace debugging only.” The paper must compare against configurable application-level population analytics and identify cross-layer/automatic semantic attribution as the difference.

### B3 — OpenTelemetry provides the shared schema substrate, not AgentProf's semantic derivation

- **Primary official source:** [OpenTelemetry Generative AI semantic conventions](https://opentelemetry.io/docs/specs/semconv/gen-ai/).
- **Verified capability:** GenAI spans and attributes standardize agent/model/system identifiers, workflow names, usage tokens, tool calls, and related telemetry. OTel enables existing backends to query and aggregate these fields.
- **Impact:** AgentProf should ingest or map OTel GenAI records and compare on equal information. The standard does not automatically infer task intent from text or recover out-of-process system effects, leaving a meaningful potential contribution. Claiming generic tags/attributes as absent would be inaccurate.

## Real-world importance and venue requirements

### Workload evidence

- **Official sources:** OpenAI's [Codex app announcement](https://openai.com/index/introducing-the-codex-app/) describes agent tasks lasting hours to weeks and reports an internal run exceeding seven million tokens. OpenAI's [support-model deployment account](https://openai.com/index/openai-support-model/) describes very large support volume and uses traces, replay, tool-call inspection, and evaluation dashboards for root-cause analysis.
- **Interpretation:** these sources support the premise that agent workloads are long, costly, and operationally important. They do **not** establish that semantic population profiles solve a current failure better than trace/evaluation tooling. They actually reinforce the need to compare to mature trace/eval workflows.

### AAAI-27 bar

- **Official source:** [AAAI-27 Main Technical Track Call for Papers](https://aaai.org/conference/aaai/aaai-27/main-technical-track-call/).
- **Verified requirements:** the main paper is limited to seven pages with up to two additional reference pages; a reproducibility checklist is mandatory; evaluation emphasizes significance, novelty, empirical soundness, AI relevance, clarity, and reproducibility, and explicitly welcomes bridge work.
- **Impact:** the current nine-page PDF shape is compatible, but the unfilled checklist and missing prompts/models/hardware/splits make the submission incomplete. Cross-domain positioning is legitimate only if both the systems mechanism and AI semantic/evaluation chain are supported.

## Source-grounded attack update

| Blind attack | Search outcome | Updated severity | Reason |
|---|---|---:|---|
| B1: RQ2 does not establish real-problem localization | **Strongly confirmed** | **Blocker** | Workflow-centric tracing says resource attribution does not automatically solve diagnosis; AgentRx/TELBench provide more direct labels and metrics; AgentTelemetry supplies a stronger external protocol. |
| B2: RQ3 misses the load-bearing prompt tagger | **Strongly confirmed** | **Blocker** | V-measure is partition agreement, while CLINC/MASSIVE directly test natural-language intents and OOS behavior. |
| B3: RQ1 lacks causal responsibility validation | **Strengthened** | **Blocker** | Pivot Tracing gives a causal propagation precedent; Perfetto exposes async/concurrency semantics; AgentSight already owns capture/correlation, so AgentProf must state and validate its additional invariant. |
| B4: operation stacks may be renamed multidimensional aggregation | **Confirmed** | **Blocker unless novelty is relocated** | Data Cube, Pivot Tracing, Perfetto, and pprof tag frames cover core query/hierarchy mechanics. |
| M2: RQ4 excludes dominant tagging cost | **Unresolved but still major** | **Major** | No searched source excuses omitting cold/full-pipeline cost; AAAI reproducibility requirements reinforce the need for it. |
| M5: real need is asserted, not demonstrated | **Partly weakened** | **Major** | Official sources confirm long, costly workloads; they do not show the proposed profile improves an operational decision. |
| Status quo is per-trace only | **Contradicted** | **Blocker-level framing/novelty issue** | Datadog Patterns, Langfuse, LangSmith, aggregate tracing, and AgentTelemetry already provide population grouping and metrics. |

## Closest-work map

| Source | Same problem | Same information | Same mechanism | Same outcome | Most defensible AgentProf delta |
|---|---:|---:|---:|---:|---|
| Data Cube | Partial | Any dimensions | **High** | No agent diagnosis | Agent-specific semantic dimension derivation and cross-layer ownership |
| Pivot Tracing | **High** | Causal runtime context + metrics | **High** | Resource diagnosis | Offline agent populations, natural-language semantics, OS effects without app instrumentation |
| Perfetto | **High** | System/userspace traces | Medium-high | Metrics/root cause | Automatic agent semantic fields and conserved operation representation |
| pprof tags | Medium | Samples + labels | Medium | Resource profile | Derivation/reconstruction of labels and non-sampled agent operations |
| Datadog Patterns | **Very high** | LLM/application spans | **Very high** | Topic-level cost/error/latency triage | Cross-layer OS/process effects, local/open workflow, arbitrary projections |
| Langfuse/LangSmith | High | App spans/tags | Medium | Population metrics/drilldown | Automatic semantics and external effects |
| AgentTelemetry | **Very high** | Agent OTel spans | Medium-high | Fault detection/cost/decision attribution | Semantic population hierarchy plus AgentSight-derived system effects |
| AgentRx/TELBench | High | Trajectory content | Low | **Very high** localization | Lower-cost human profile and cross-run recurrence view |

The most dangerous prior art is not a single paper but the combination of Pivot Tracing/Data Cube at the mechanism layer and Datadog Patterns/AgentTelemetry at the agent-product layer. The manuscript must demonstrate an agent-specific cross-layer invariant and outcome that neither combination supplies.

## Strongest alternative explanation after search

The paper's results are explained by conventional OLAP/trace aggregation over curated semantic dimensions, coupled with task-specific ranking. Existing tools can group and drill into identical attributes, and current products can automatically cluster LLM interactions into semantic hierarchies with cost/error/token metrics. AgentProf may be an open, cross-layer implementation of that pattern, but the evaluation does not isolate the cross-layer responsibility reconstruction or show a better diagnosis outcome.

This explanation is now source-grounded, not hypothetical. The decisive discriminator is an equal-information, frozen-policy experiment on external faults where the only added capability is AgentProf's semantic/cross-layer representation and where inspected work is measured at fixed localization recall.

## Sources that support, rather than only attack, the paper

1. Aggregate-trace papers independently validate that single-trace inspection is insufficient at population scale.
2. Workflow-centric tracing and Pivot Tracing validate the value of causal workflow context for resource attribution.
3. AgentRx and TELBench show that long-horizon agent failure localization is a real, difficult task with external labels and repeatable protocols.
4. OpenAI's official reports establish that real agent tasks can be very long and token-intensive.
5. Datadog, Langfuse, and LangSmith demonstrate user demand for population metrics and semantic slices.

These sources make the high-level problem credible. They simultaneously show that the manuscript's novelty boundary and empirical bar must be much sharper.

## Larger claim found by search

A stronger claim that preserves the thesis and does not change any RQ is:

> **Agent profiling is the semantic continuation of causal tracing: it carries a conserved responsibility record from intent through model, tool, process, and OS effects, then exposes any additive resource or failure measure through query-time semantic hierarchies across runs.**

This is larger and more defensible than “flame graphs for agent logs” because it explicitly joins the systems lineage of causal context propagation with the AI need for semantic population analysis. Current evidence almost supports the representation and multiple-view portion, but does not yet validate conserved responsibility or the real-failure outcome. The claim must therefore remain a target, not a conclusion, until RQ1 and RQ2 are repaired.

## Accepted protocols and baseline requirements

### RQ1 resource attribution

- Compare against Data Cube/PerfettoSQL and Pivot-Tracing-like causal context at equal fields.
- Use ground-truth injected ownership under subprocesses, concurrency, async work, shared processes, missing events, and nested agents.
- Report operation/effect attribution precision, recall, ambiguity/abstention, conservation error, and resource-weight error—not category mixing against the grouping label.

### RQ2 real-problem localization

- Use a fixed external fault target: injected fault-bearing event/span, critical step, or first erroneous semantic span.
- Report fixed-recall inspection work, macro precision/recall/F1, exact/±k localization where applicable, per-fault/per-framework results, uncertainty across repetitions, and resource/token/dollar cost.
- Baselines: session/native trace drilldown; equal-information PerfettoSQL/OLAP grouping; official OTel and OTel+GenAI conditions; AgentTelemetry's native analysis; and, on compatible trajectories, AgentRx with compute parity disclosed.
- Freeze tagger, stack fields, depth, ranking, thresholds, and prompts before held-out faults/frameworks. Report every attempted policy, not only the best.

### RQ3 tag accuracy

- Use CLINC150/MASSIVE or another fixed public ontology with train/development/test isolation and OOS labels.
- Report macro F1/accuracy, coverage/abstention, OOS recall/F1, paraphrase stability, calibration if confidence is claimed, and prompt/model/version/decoding details.
- Keep V-measure only for unsupervised clustering agreement; do not rename it semantic tag accuracy.

### RQ4 profiling cost

- Separate capture, import, cold tagging, warm-cache query, hierarchy induction, folding/rendering, and storage.
- Report elapsed time, CPU/GPU/RAM, energy if feasible, tagger calls/tokens, model/quantization, cache state, concurrency, dataset size, and scaling distributions.

## One highest-value next experiment

**Route this single experiment to RQ2: real-problem localization. Do not create another custom AgentProcessBench variant.**

### Hypothesis

On held-out faults and frameworks from the official AgentTelemetry benchmark, a frozen AgentProf semantic profile reduces the fraction of telemetry inspected to recover fault-bearing runs/spans at a predeclared fixed macro recall relative to the strongest equal-information non-oracle trace/aggregation baseline.

### External artifact and protocol

Use the official AgentTelemetry artifact and its 14-fault, five-observability-condition, seven-framework, six-repetition matrix. Preserve its workload generation, fault definitions, seeds/repetitions, and OTel export. Treat the official injected fault target as hidden during configuration. If only run-level fault labels are public, predeclare run-level triage and do not claim span localization; if official fault-bearing span/first-anomaly targets are available, use those without author relabeling.

### Frozen split and information parity

- Develop the one AgentProf policy on a predeclared subset of frameworks and fault families.
- Freeze prompt/tagger, mapping rules, stack field order, induction settings, ranking, thresholds, and all retry/refinement behavior.
- Test on held-out frameworks **and** held-out fault families; do not re-run policy selection on the test labels.
- Run two parity tracks: native-information baselines on their official observability condition, and same-information baselines given every field visible to AgentProf. This separates semantic derivation/cross-layer capture from hierarchy/ranking.

### Baselines

1. chronological/native trace inspection and per-session grouping;
2. vanilla OTel and OTel+GenAI official conditions;
3. equal-information PerfettoSQL/Data-Cube grouping with the same dimensions and a predeclared ranking;
4. AgentTelemetry metadata/full analysis, including its anomaly detector where applicable;
5. an oracle using hidden labels, reported only as an upper bound.

Datadog Patterns should be included as a capability comparison and, if a reproducible export/API trial is feasible, an empirical baseline; it must not be the sole decisive baseline because paid/vendor behavior may not be reproducible.

### Primary outcome and success criterion

- **Primary metric:** fraction of spans/operations (and separately weighted work) inspected to reach a predeclared macro recall, preferably 80%, over hidden fault targets.
- **Secondary metrics:** macro precision/recall/F1, first-fault rank or reciprocal rank, per-fault/per-framework results, abstention, cold/warm cost, and bootstrap confidence intervals over fault × framework cells.
- **Success:** the confidence interval for AgentProf's inspection-work reduction excludes zero against the strongest same-information non-oracle baseline, while macro recall meets the fixed target on held-out frameworks and faults. Lower work achieved by collapsing recall is failure.

### Why this is the highest-value experiment

It addresses the largest evidence gap and paper's user-facing outcome; uses an external accepted artifact; crosses seven real framework adapters; includes OTel controls and known faults; tests generalization rather than retuning; and is structurally different from the current six-dataset custom benchmark. It also pressures the paper's systems and AI layers simultaneously without changing RQ2's meaning.

## Alternatives and decision

I considered three next experiments:

1. RQ3 on CLINC150/MASSIVE would cleanly validate prompt tagging but would not establish a profiling benefit or system novelty.
2. RQ1 causal attribution under synthetic concurrency would validate the cross-layer invariant but could still leave the headline diagnosis outcome unsupported.
3. RQ2 on AgentRx would use excellent critical-step labels, but it resembles the current trajectory-localization family and lacks the multi-framework observability-condition design.

The AgentTelemetry RQ2 study has the highest decision value. It should be the only new decisive experiment selected now. RQ1/RQ3/RQ4 gaps remain required before submission, but the orchestrator should not open parallel custom benchmark branches that repeat the same weak evidence pattern.

## Tree/search updates

Suggested non-canonical updates for the owning orchestrator:

- Mark `A-B4 / H-alt` as **verified** by Data Cube, Pivot Tracing, Perfetto, pprof, and Datadog Patterns.
- Add closest-work nodes for Pivot Tracing, Datadog Patterns, AgentTelemetry, AgentRx, TELBench, CLINC150, and MASSIVE.
- Replace the provisional external RQ2 benchmark node with `AgentTelemetry held-out fault/framework localization at fixed recall`.
- Add an explicit “same-information parity” requirement to every hierarchy/localization comparison.
- Add a novelty node: `cross-layer conserved responsibility`, distinct from `multidimensional query hierarchy`.
- Add contradiction node: `resource-attribution infrastructure does not automatically support diagnosis` from workflow-centric tracing.

## Paper/claim impact

No paper text is modified. Source verification implies the following eventual repairs after evidence exists:

- retain the exact thesis and fixed RQs;
- replace categorical status-quo claims with a capability-accurate comparison;
- position AgentProf relative to Data Cube, Pivot Tracing, Perfetto, pprof tag frames, Datadog Patterns, Langfuse/LangSmith, AgentTelemetry, AgentRx, and TELBench;
- separate four mechanisms: responsibility reconstruction, semantic tag derivation, query-time projection, and fault ranking;
- stop treating current RQ3 mapping agreement as prompt-tagger accuracy;
- stop treating low inspection work at low recall as localization success;
- report full cold/warm profiling cost and complete the mandatory reproducibility checklist.

## Project-memory updates

No canonical memory, paper, source, code, data, skill, AGENTS file, or experiment artifact was modified. This report is the only output of the node. The owning root may incorporate the suggested attack/source nodes after the outer audit.

## Completion, uncertainty, and next node

The systems, AI/ML, bridging/product, real-world, artifact, protocol, and venue searches are complete for review routing. The main remaining uncertainties are implementation-level: whether AgentTelemetry exposes exact fault-bearing span labels and whether AgentProf can ingest its OTel traces without an unplanned instrumentation project. Those affect feasibility and metric granularity, not the scientific choice of external benchmark.

**Next node:** a fresh, complete paper and all-figure/table reread after search, recorded in `300-full-paper-reread-and-scientific-assessment.md`. Internal project narrative and gate reports must remain unread until that reread and source-grounded assessment are committed.
