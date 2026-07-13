# Review 001 / Node 300: Full-Paper Reread and Scientific Assessment

## Context and status

- **Timestamp:** started 2026-07-13T10:56:00-07:00; completed 2026-07-13T11:00:00-07:00.
- **Phase / step / gate:** `BUILD_AND_EVALUATE` / cycle 0002 / `REVIEW_GATE`.
- **Parent:** `200-external-search-and-source-verification.md`.
- **Node status:** complete for the post-search scientific-review scope.
- **Isolation:** I still have not read `docs/idea-story.md`, `docs/evaluation.md`, `docs/background-related-work.md`, `docs/questions-for-author.md`, prior review conclusions, or the current cycle's experiment/write-gate reports. This report is based only on the submitted paper and independently opened external primary sources.

## Objective

This node performs the mandatory fresh reread after source search. It asks whether the complete paper—claims, mechanism, all four fixed RQs, figures, tables, implementation description, related work, and conclusion—survives the strongest source-grounded attacks. It also distinguishes defects that require new evidence from those repairable through writing without changing the fixed thesis or RQ meanings.

The scientific contract remains exact:

- thesis: **“Agent observability needs profiling, not only debugging.”**
- RQ1: resource attribution;
- RQ2: real-problem localization;
- RQ3: tag accuracy;
- RQ4: profiling cost.

## Inputs and provenance

I reread all 936 lines of `docs/paper/main.tex`, the complete nine-page `main.pdf` in layout-preserving text, the bibliography, and the reader-facing figure/table sources. I visually reinspected the token, time, and file flame graphs, the RQ1 field-ablation plot, and the RQ3 plot; I reread the rendered RQ2 table and the architecture source/rendered placement. I checked every abstract/introduction/conclusion number against the corresponding evaluation result and reread the related-work section after source verification.

External comparison relies on the primary sources documented in Node 200, especially Data Cube, Pivot Tracing, workflow-centric tracing, Perfetto, pprof, Datadog Patterns, Langfuse/LangSmith, AgentTelemetry, AgentRx, TELBench, CLINC150/MASSIVE, V-measure, AgentSight, and the AAAI-27 call.

No internal repair proposal is used as evidence.

## Method

The reread follows the full causal chain rather than treating the RQs as independent mini-papers:

```text
real population-scale observability need
-> stable and correctly inherited semantic responsibility
-> operation-stack abstraction adds value beyond standard cubes/traces
-> profile exposes resource concentration correctly (RQ1)
-> profile improves localization of real problems (RQ2)
-> the load-bearing semantic tags are accurate (RQ3)
-> the whole path is practical (RQ4)
-> quality, safety, or cost decisions improve
```

For each edge, I asked whether the manuscript supplies a construct definition, comparable baseline, frozen protocol, independent ground truth, uncertainty, and a result that supports the exact claimed consequence. I then audited every displayed artifact for whether it answers the reader's likely question.

## Paper in one sentence

AgentProf converts heterogeneous agent and system events into uniform weighted records, derives or maps semantic fields, projects an ordered list of those fields into a stack-shaped aggregation key at query time, and renders folded population profiles intended to reveal resource concentration and recurring problems across runs.

## Scientific taste assessment

### Plain-language principle

**Treat many agent runs like a program profile: carry additive costs and effects to stable semantic responsibility categories, then aggregate across runs at the hierarchy that answers the current question.**

This is the paper's best idea. It is easy to state, transfers a durable systems principle into agent observability, and can organize a meaningful cross-domain artifact.

### Challenged belief

The paper challenges the belief that per-execution traces, span trees, and input clusters are sufficient for agent observability. The search shows that the strong form of this belief is false as a description of the field: Datadog Patterns already provides semantic topic hierarchies with cost/token/error/latency metrics; Langfuse and LangSmith provide population metrics sliced by tags/metadata; Perfetto and aggregate-trace work provide population analysis; and AgentTelemetry includes cost aggregation and decision attribution.

A defensible challenged belief remains: **application-level population metrics are sufficient even when responsibility crosses prompt, model, tool, process, and OS boundaries.** That is sharper and important, but the paper does not yet validate the cross-layer responsibility edge that would defeat it.

### Depth classification

The core is **incomplete-but-promising**. It is not complicated-but-shallow: the central idea is economical, and a conserved semantic responsibility record could be deep. It is not yet simple-but-deep in demonstrated form because the manuscript's specified mechanism reduces largely to field projection and aggregation while the hard semantic/cross-layer correctness is assumed. The implementation breadth and dataset counts are larger than the demonstrated scientific content.

### Strongest alternative explanation

AgentProf's reported gains come from conventional OLAP/trace aggregation over curated or dataset-native fields, plus task-specific depth and ranking choices. Given the same fields and tuning budget, Data Cube/Perfetto-style grouping or existing semantic observability products could yield equivalent profiles; the pprof/flame-graph shape is a presentation choice. The experiments do not isolate automatic semantic derivation, correct cross-layer responsibility, or representation-specific localization benefit.

## Final source-grounded verdict

**Reject for AAAI-27 Main Track in the current cycle, with high confidence.**

The problem is significant and AI-relevant, and the exact thesis is plausible. The current manuscript does not establish novelty over a combination of established multidimensional/causal trace analysis and current agent-observability products; does not show that operation-stack profiling improves real-problem localization; does not evaluate the natural-language tagger that the resource-attribution result depends on; and excludes the dominant cold semantic-enrichment cost from its “complete profiling” answer. At a systems bar, the central responsibility invariant and baseline parity are missing. At an AI/ML bar, the semantic construct, held-out protocol, and statistical reporting are insufficient. At the cross-domain bar, neither side validates the bridge.

This is not a paper that should be routed to idea refinement: the fixed principle is good enough. It needs one decisive external experiment plus targeted evidence completion and then writing repair.

## Source-grounded blocker map

### B1 — Novelty/mechanism blocker: the operation-stack abstraction is not distinguished from established multidimensional and causal trace aggregation

- **Category:** novelty; mechanism; related work.
- **Paper claims:** operation stacks replace a missing runtime hierarchy; a flat `GROUP BY` cannot produce multi-resolution views; per-execution tools lack population attribution.
- **External contradiction:** [Data Cube](https://arxiv.org/pdf/cs/0701155) formalizes roll-up/drill-down over dimensions; [Pivot Tracing](https://cs.brown.edu/~rfonseca/pubs/mace15pivot.pdf) groups metrics using causally propagated context; [PerfettoSQL](https://perfetto.dev/docs/analysis/perfetto-sql-getting-started) provides reusable trace queries, joins, aggregates, and batch metrics; [pprof](https://github.com/google/pprof/blob/main/doc/README.md) can insert label-derived pseudo-frames; [Datadog Patterns](https://docs.datadoghq.com/llm_observability/monitoring/patterns/) automatically builds semantic topic hierarchies and reports cost, tokens, errors, and latency per topic.
- **Post-search reread:** the formal model confirms the overlap: $\sigma=[f_1,\ldots,f_k]$ maps a record to an ordered tuple, then identical tuples are merged and additive weights summed. This is a cube/pivot expressed as a stack. The field-count demonstration (9, 57, 226, 455, 3,757 groups) establishes expressiveness already expected from multidimensional aggregation, not a new capability.
- **Why blocker:** the paper's first claimed contribution is the model itself. Without an invariant or outcome not supplied by the combination above, the contribution reads as relabeling.
- **Required evidence/repair:** relocate novelty to a **conserved cross-layer semantic responsibility record** constructed without application instrumentation. Specify that invariant, show what Pivot Tracing/OTel/Perfetto/Datadog cannot observe, and compare against an equal-information cube/trace implementation. Do not change the thesis or RQs.

### B2 — Evaluation blocker: RQ2 does not show real-problem localization and appears adaptively configured on the evaluated tasks

- **Category:** evidence; evaluation protocol; claim validity.
- **Paper claim:** profiles locate real problems while inspecting 9.4% of work, use 45% fewer groups, and produce fewer, higher-quality groups.
- **Displayed result:** operation-stack AP is 0.312, below per-session 0.348 and native hierarchy 0.357. Top-five recall is 0.188. At 30% inspection, recall is 0.390. The 9.4% work headline therefore corresponds to recovering fewer than one fifth of positives. “Higher-quality” is not supported by AP or F1 relative to multiple baselines.
- **Adaptive protocol:** the paper says depth should be tuned per objective and reports that modifying fields, mapping rules, or ranking criteria on the same operations improves 5/6 tasks. It does not define a development split, total selection budget, frozen final policy, or ranking formula. The phrase “query-aware AP” appears without a reproducible query/ranker definition.
- **External bar:** [AgentRx](https://github.com/microsoft/AgentRx) uses critical-step labels and exact/±k/distance metrics; [TELBench](https://arxiv.org/pdf/2606.02060) uses semantic-span macro P/R/F1 and first-error accuracy; [AgentTelemetry](https://openreview.net/pdf?id=owdmAYFk6k) supplies an accepted multi-framework fault protocol and OTel controls. [Workflow-centric tracing](https://cs.brown.edu/people/jcmace/papers/sambasivan16principled.pdf) specifically warns that resource attribution infrastructure does not automatically support diagnosis.
- **Why blocker:** RQ2 is the causal bridge from a profile to quality/safety/cost utility. Current evidence shows one triage tradeoff point, not better localization.
- **Required route:** `EXPERIMENT_GATE`. Run one frozen-policy, held-out AgentTelemetry experiment at fixed recall, defined in the selected-experiment section below.

### B3 — AI semantic blocker: RQ3 evaluates structured action remapping, not the natural-language intent attribution that is load-bearing in RQ1

- **Category:** construct validity; AI/ML evaluation; global consistency.
- **Paper claim:** stable tags are derived from natural language; derived tags agree with ground truth on seven of nine held-out datasets; RQ3 validates RQ1 tag quality.
- **Actual construct:** RQ3 maps visible structured fields into `phase` and compares them to each dataset's native `action`. It never evaluates regex tags or the local LLM tagger on the prompts used in RQ1. It does not report tag-name correctness, OOS behavior, unmatched/abstention errors, paraphrase stability, or inheritance accuracy.
- **Metric issue:** [V-measure](https://aclanthology.org/D07-1043.pdf) measures cluster/class partition agreement, not semantic label correctness. The source does not justify a universal 0.7 pass threshold. The figure shows severe failures on ToolBench and API-Bank, and the other seven scores may follow nearly direct field mappings.
- **Leakage/replicability issue:** “infer mapping rules from the other eight” is not operationally specified. No algorithm, prompts, author intervention, schema access, split artifacts, or per-dataset rule set is given. The paper claims an AI agent can iteratively refine production regex rules until <5% unmatched in 5–10 rounds, but provides no measurement.
- **External bar:** [CLINC150](https://github.com/clinc/oos-eval) and [MASSIVE](https://github.com/alexa/massive) provide fixed natural-language intent ontologies, OOS examples, public splits, and standard macro metrics.
- **Why blocker:** natural-language stable tags are one of three stated design requirements and the decisive RQ1 field. The manuscript validates a different mechanism on a different signal.
- **Required completion:** keep RQ3 unchanged but directly evaluate the actual prompt tagger on a fixed public ontology and on held-out real AgentProf prompts; disclose rules/model/prompt/version/decoding and report macro accuracy/F1, coverage/abstention, OOS and paraphrase stability.

### B4 — Systems correctness blocker: RQ1's separation score is circular and no experiment validates cross-layer responsibility

- **Category:** mechanism correctness; construct validity; evidence.
- **Paper claim:** cross-layer resource projection connects effects to responsible intent; semantic profiling separates more than 90% of cost that session views leave mixed.
- **Circular metric:** the score asks whether groups mix prompt categories, then adds `prompt_tag`—the scoring category—to the grouping tuple. With both `session` and `prompt_tag`, zero mixing is definitional. The permutation says the real labels align better than shuffled labels but does not validate that an intent is responsible for each file/process/network effect.
- **Ambiguous headline:** prompt-only reduces mixed weight from 90.4% to 36.7% (a 53.7-point reduction); session-only is 84.4%; both fields visually produce zero. “Separates over 90%” is either numerically inconsistent with the prompt-only ablation or a ratio derived from the tautological both-fields case. The exact numerator/denominator are never stated.
- **Missing semantics:** no definition or audit covers concurrent tools, nested agents, subprocesses, async/background operations, shared processes, overlapping prompts, missing events, clock skew, or ambiguous parentage. AgentSight supplies capture/correlation; the paper does not state which responsibility edges AgentProf inherits versus reconstructs.
- **Architecture-chain break:** the architecture explicitly says public datasets enter as preconstructed operations. Thus RQ2/RQ3 bypass local-history reconstruction and cross-layer inheritance; RQ1 uses reconstructed local observations but has no independent ground truth. No one experiment validates the end-to-end bridge.
- **Resource-accounting issue:** duration is treated as an additive measure across all timed operations. The time flame graph totals 2,263,796 seconds (about 26.2 days) and may double-count nested/overlapping work; the paper does not define exclusive versus inclusive time. The same ambiguity affects what “conserved” means.
- **Why blocker:** cross-layer ownership is the most defensible novelty after search. It cannot remain assumed.
- **Required completion:** state the responsibility/conservation invariant and validate it against known ownership under concurrency/subprocess/async/missing-event conditions. This is RQ1 completion, not a new RQ.

## Major findings

### M1 — RQ4 answers warm folding cost, not complete profiling cost

- **Category:** evidence; reproducibility; claim validity.
- The 1.6 s median over 76 configurations appears to begin after most tags are cached. The same section reports 35,136 llama.cpp calls for full history but never measures their total wall time. A separate 300-fragment microbenchmark has 31 ms p95; it cannot be multiplied into a reliable end-to-end result because concurrency, batching, I/O, model load, and hardware are unspecified.
- The manuscript omits capture/import cost, model identity, quantization, prompt length, token throughput, CPU/GPU/RAM, cold load, cache construction, storage, and scaling by operation count.
- “Complete profiling takes seconds” and “adds no agent-runtime overhead” are therefore scope-dependent overclaims. Offline execution avoids in-agent latency but not capture overhead or delayed availability.

### M2 — The mechanism description is not sufficient to reproduce the claimed system

- **Category:** systems mechanism; reproducibility.
- The 9.8K LOC claim and a five-box linear architecture do not expose IDs, schemas, joins, ordering, correlation, tag precedence, inheritance, ambiguity, failure modes, persistence, or complexity.
- Stack induction omits its score equation, tokenization, candidate construction, objective, recursion/stopping rule, balance/depth parameters, tie handling, and development protocol.
- The architecture figure visually presents `Agent histories / Public datasets -> Parse -> Intent attribution -> Stack construction -> Folded profiles`; it does not show the key cross-layer inputs/edges, mapping-rule path, cache, query tuple, or which stages each RQ exercises.

### M3 — Baseline information and tuning budgets are not matched

- **Category:** evaluation fairness.
- Flat, session, native hierarchy, raw action, hand stacks, automatic stacks, and oracles receive different structures and possibly different task knowledge. The paper never states which fields each ranking observes, how query-aware ranking is computed, or how many choices were attempted.
- Data Cube/PerfettoSQL, Pivot-Tracing-like propagated context, Datadog-like semantic clustering, AgentTelemetry, and AgentRx are absent as empirical baselines even though several appear in related work.
- An oracle-ranker AP of 0.599 shows grouping leaves headroom, but does not identify whether semantic representation or ranking is limiting.

### M4 — RQ2 aggregates six incompatible tasks into medians that hide failures

- **Category:** statistical reporting; construct validity.
- Loops, side effects, unsafe operations, incorrect/redundant steps, and group starts are not instances of one clearly defined positive construct. The paper gives only medians, not task-level rows, prevalence, intervals, effect differences, or seeds.
- Bootstrap intervals are described but not displayed numerically; with four dataset families and task dependence, family-resampling support is limited. The null control fixes a visible ranking whose selection process is not frozen.
- “5/6 tasks improve” after reconfiguration is evidence of adaptivity without the complete attempt log, not evidence of generality.

### M5 — The related-work section is capability-inaccurate and too compressed to support novelty

- **Category:** framing; novelty; writing.
- Two short paragraphs list tools and then assert a trace-versus-profile distinction. They do not discuss Data Cube, Pivot Tracing, aggregate trace visualization, pprof tag frames, Datadog Patterns' hierarchy/metrics, Langfuse/LangSmith population slices, AgentTelemetry's cost/decision modules, or protocol differences from AgentRx/TELBench.
- Datadog is cited, but its documented semantic hierarchy plus per-topic resource/error metrics contradicts the manuscript's input-clustering characterization. Merely adding citations without changing the comparison logic will not fix this.

### M6 — Real workload scale is established, but operational usefulness is not

- **Category:** significance; external validity.
- Official OpenAI sources substantiate long-running, high-token agent work. The local evidence, however, is one multi-month development project with 325 readable sessions, unknown sampling, tasks, authors, models, versions, privacy treatment, and held-out time period.
- None of the flame graphs leads to a validated decision: no optimization, safety intervention, regression discovery, budget reallocation, or analyst outcome follows from a discovered category.
- The fixed thesis can remain bold, but RQ2 must carry the consequence.

### M7 — Global claims blend four separable mechanisms and overstate each result

- **Category:** writing; logic; claim consistency.
- Responsibility reconstruction, prompt tag derivation, field projection, and problem ranking have different algorithms and evidence, but the paper calls all of them “semantic profiling.”
- “Tags agree with ground truth” overstates mapping partition agreement; “locates problems” overstates low-recall group triage; “complete profiling” excludes cold tagging; “multi-resolution view unavailable from flat grouping” ignores standard cubes; and “higher-quality groups” conflicts with the AP table.
- The fixed thesis sentence is clear. The supporting claims need mechanism-specific subjects and numerically complete qualifiers.

### M8 — Submission reproducibility is incomplete

- **Category:** submission readiness; reproducibility.
- `ReproducibilityChecklist.tex` is unfilled, and the rendered main PDF contains no completed checklist response. The official AAAI-27 call makes it mandatory.
- Missing items include code/artifact access, private-data license/ethics, preprocessing, prompts/rules, model checkpoints, hardware/software, random seeds, per-task results, attempted configurations, and exact statistical outputs.

## Minor findings

1. **Mechanism scope:** nonnegative additive weights support counts/sums, but not ratios, distinct counts, quantiles, distributions, critical paths, or tail latency without additional statistics. The limitation matters because observability commonly asks p95/p99 and success rate.
2. **Time semantics:** “wall-clock duration” is additive in the model even when nested or concurrent events may overlap; the paper should define inclusive/exclusive time and conservation.
3. **Terminology:** “semantic operation stack,” “intent attribution,” “stack construction,” “phase,” “action,” and “task category” drift across mechanisms. A phase derived from action fields is not necessarily intent.
4. **Tag stability:** one-word grammar validity (2,700/2,700 syntactically valid outputs) is not semantic correctness, repeatability, or low cardinality.
5. **Public-dataset coverage:** fifteen heterogeneous families demonstrate importer flexibility, not one unified semantic ontology or end-to-end agent-profiler correctness.
6. **Privacy:** local prompts and intercepted traffic are sensitive; offline/local processing helps, but the paper does not state retention, redaction, or what the LLM tagger sees.
7. **Portability:** public datasets arrive as preconstructed operations, so supporting 15 families may reflect adapters rather than a framework-agnostic capture path.

## Nits

1. The rendered flame graphs say `agentpprof`, while the paper and title say AgentProf.
2. The token flame graph reports a total of 21,899,030,768 tokens without explaining whether prompt, completion, cached, or repeated context tokens are counted; at 325 trajectories the magnitude needs a sanity check.
3. The flame graphs hide 7,331, 7,474, and 19,126 tiny nodes respectively, and most labels truncate at paper scale; they demonstrate renderability more than interpretability.
4. Figure 3's both-fields bars vanish at zero and its legend partly crowds the top of the plot; exact labels would prevent ambiguity.
5. Figure 4's dashed 0.7 threshold visually implies a recognized pass criterion that the text never sources.
6. Table 1's em dashes under group count hide a basic scale comparison for two baselines.
7. Figure captions and accessible descriptions do not identify a concrete operational conclusion from any profile.

## Figure- and table-level reread

### Figure 1: three semantic flame graphs

- **What it establishes:** the implementation can render token, time, and file counts from a shared project into stack-shaped population views; different measures yield visibly different width distributions.
- **What it does not establish:** correct cross-layer ownership, a stable semantic hierarchy, novelty over labeled pprof/cube tools, or improved decisions.
- **New post-search concern:** the visible hierarchy includes project, agent, session, prompt, kind/call/model layers and changes depth across views. This looks like a chosen dimension order, precisely what cube/pivot baselines express. The caption says both stack fields and weight change, so visual differences cannot isolate the weight function.

### Figure 2: architecture

- **What it establishes:** a simple pipeline and two input classes.
- **What it exposes:** public datasets are preconstructed operations, bypassing local reconstruction. This makes the four-RQ causal chain non-end-to-end.
- **Missing:** responsibility edges, AgentSight boundary, tag propagation, caches, stack induction/manual branch, ranker, hidden labels, and outputs used for each RQ.

### Figure 3: RQ1 separation

- **What it establishes:** including a prompt category in the grouping key mechanically reduces category mixing and increases stack count.
- **What it does not establish:** category correctness, effect ownership, useful attribution, or superiority over an equal-information trace/cube.
- **Tradeoff:** unique stacks rise from about 12k to 25–27k; the paper calls separation a benefit without measuring analyst cost or cardinality/storage penalty.

### Table 1: RQ2 localization

- **What it establishes:** operation stacks occupy an intermediate work/coverage point between flat and highly fragmented alternatives.
- **What it contradicts:** the method is not best on AP, F1@5, R@5, or work-to-first-positive among non-oracles. Its best displayed non-oracle statistic is R@30% 0.390, only modestly above 0.356/0.338/0.333 and without task-level uncertainty.
- **Headline issue:** work reduction is inseparable from recall reduction. A fixed-recall comparison is required.

### Figure 4: RQ3 mapping quality

- **What it establishes:** author-derived cross-dataset mapping rules align with action partitions/boundaries on seven datasets and fail badly on ToolBench/API-Bank.
- **What it does not establish:** prompt-intent tagging, semantic label identity, stability, or a universal seven-of-nine success criterion.
- **Visual/statistical issue:** no uncertainty or sample count per dataset is displayed; Android sits near the unsourced threshold.

## Fixed-RQ assessment after source verification

| Fixed RQ | Exact required construct | Current evidence | Source-grounded judgment | Completion needed |
|---|---|---|---|---|
| **RQ1 resource attribution** | Correctly assign additive resources/effects to responsible semantic entities across layers | Category-mixing ablation, field/weight views, 325 local trajectories | **Not answered credibly.** Grouping by the scored tag is circular; responsibility edges and overlapping-time semantics are unvalidated; equal-information cube/trace baselines are absent. | Ground-truth responsibility/conservation under concurrency and equal-information Pivot/Perfetto/Data-Cube comparison. |
| **RQ2 real-problem localization** | A frozen profile helps recover real fault-bearing work with less inspection at matched recall | Six tasks/four datasets; medians; AP 0.312; R@5 0.188; Work@5 0.094 | **Not answered.** It shows a tradeoff point with adaptive task-specific tuning and weaker AP than two baselines. | One held-out external AgentTelemetry experiment at fixed recall and matched information/tuning. |
| **RQ3 tag accuracy** | Natural-language intent tags are semantically correct, stable, and usable | Leave-one-dataset-out structured field mappings scored by V-measure/boundary F1 | **Not answered for the load-bearing tagger.** A different proxy mechanism is evaluated. | Direct regex/LLM tag evaluation on fixed natural-language ontology and held-out real prompts, including OOS/abstention/stability. |
| **RQ4 profiling cost** | Full cold and warm end-to-end resource cost of the deployed profiling workflow | 76 warm configurations at 1.6 s median; 35,136 unpriced tag calls; 300-fragment microbenchmark | **Partially answered only for cached projection/folding.** | Measured cold import/tag/induce/fold/render plus warm query, hardware/resources/model/cache/scaling. |

No RQ is submission-complete. RQ1 and RQ4 have useful implementation evidence; RQ2 and RQ3 remain the sharpest empirical failures.

## Largest gaps and opportunity

- **Largest evidence gap:** no leakage-resistant, external, end-to-end RQ2 result demonstrates that a frozen AgentProf profile reduces inspection work at fixed real-fault localization recall against a strong same-information baseline.
- **Largest writing-only gap:** the paper does not separate responsibility reconstruction, semantic tag derivation, query-time projection, and problem ranking in its claims or evidence. This produces inaccurate status-quo comparisons and lets proxy results appear to validate different mechanisms. Once evidence exists, this can be fixed without changing thesis/RQs.
- **Largest claim current evidence almost supports:** **A uniform operation record lets heterogeneous agent telemetry be reprojected into multiple additive population resource views, with per-session drilldown retained as a special case.** Fifteen importers, field sweeps, multiple weights, and pprof output nearly support this. Required final proof is parity against a standard multidimensional trace query and a precise account of what uniformity preserves/loses.
- **Potential larger claim:** **Agent profiling is the semantic continuation of causal tracing: a conserved responsibility record connects intent to model, tool, process, and OS effects, then supports query-time resource and failure hierarchies across runs.** This preserves the exact thesis and all RQs, but it is not yet supported because responsibility and fault-localization edges are missing.

## One highest-value next experiment

### Selection

Route exactly one decisive experiment to **RQ2 real-problem localization** using the official [AgentTelemetry](https://pypi.org/project/agenttelemetry/) benchmark/toolkit. Do not create another custom AgentProcessBench-like benchmark.

### Single hypothesis

On held-out fault families and frameworks, a completely frozen AgentProf policy reduces the fraction of telemetry inspected to recover fault-bearing runs/spans at a predeclared fixed macro recall relative to the strongest same-information non-oracle trace/aggregation baseline.

### Minimal complete design

- Preserve AgentTelemetry's official 14 faults, five observability conditions, seven framework adapters, and six repetitions.
- Use official injected fault labels/targets; keep them hidden while configuring. If the artifact exposes only run-level faults, measure run triage and do not claim span localization.
- Predeclare development frameworks/faults and disjoint held-out framework **and** fault-family tests.
- Freeze tagger/prompt/rules, stack fields/order/depth, induction, ranker, threshold, and retry/refinement budget before test.
- Compare chronological/native trace, per-session, vanilla OTel, OTel+GenAI, equal-information PerfettoSQL/Data-Cube grouping, and AgentTelemetry's strongest applicable analysis. Use an oracle only as an upper bound.
- Primary metric: fraction of operations/spans and weighted work inspected at 80% macro recall, or another recall fixed before results. Secondary: macro P/R/F1, first-fault rank, per-fault/per-framework distributions, abstention, cold/warm cost, and uncertainty over fault × framework cells.
- Success requires an interval excluding zero improvement versus the strongest same-information non-oracle baseline while meeting fixed recall. Saving work by losing recall is failure.

### Why this experiment, not another

It uses an accepted external artifact, crosses seven real framework adapters, contains explicit OTel controls and known faults, directly targets the paper's user-facing consequence, and forces both the systems representation and AI semantic policy to generalize. RQ3 on CLINC/MASSIVE and RQ1 attribution-injection studies remain needed for final completeness, but they are not the one highest-value next decision.

## Alternatives and routing decision

- **Writing-first:** rejected as primary. Accurate wording and related work are necessary but cannot create responsibility correctness or localization evidence.
- **Targeted RQ3 experiment first:** clean but lower paper-level decision value; it could validate tags while leaving the profile's usefulness and novelty unresolved.
- **RQ1 synthetic attribution first:** scientifically important but easier to dismiss as an internal microbenchmark; it would not establish the headline consequence.
- **Idea refinement:** not allowed or needed in `BUILD_AND_EVALUATE`. The principle and exact thesis should be preserved.

**Scientific route after this node: `EXPERIMENT_GATE`.** If the external AgentTelemetry preflight proves infeasible because exact telemetry/labels are unavailable, the orchestrator should record that fact and choose the nearest official artifact/protocol, not silently create another custom dataset. Targeted WRITE should follow only after the decisive result and RQ completions; submission-completion work comes last.

## Tree/search updates

Suggested review-state updates for the owning orchestrator:

- Confirm blockers `B1 novelty/parity`, `B2 external RQ2`, `B3 actual tagger`, and `B4 responsibility correctness`.
- Mark `H-alt: conventional cube + curated fields + tuned ranker` as the leading alternative explanation.
- Make the AgentTelemetry fixed-recall held-out study the single highest-value experiment node.
- Require same-information and same-tuning-budget controls.
- Preserve the larger causal-tracing claim only as an evidence target.
- Do not open an idea-refinement node in this phase.

## Paper/claim impact

No paper file is modified. The scientific assessment says the exact thesis is worth retaining, but every headline result must eventually be tied to its actual construct:

- RQ1: responsibility accuracy, not category-key separation;
- RQ2: localization at fixed recall, not low work at low recall;
- RQ3: actual natural-language tag accuracy, not structured partition agreement;
- RQ4: measured cold and warm full-path cost, not cached folding alone.

The eventual paper must also acknowledge existing population semantic metrics and distinguish AgentProf's cross-layer/open/local contribution.

## Project-memory updates

No canonical memory, paper, code, data, skill, AGENTS file, or experiment artifact was changed. Suggested state changes are confined to this review report until the outer audit.

## Completion, uncertainty, and next node

The post-search full-paper reread and scientific assessment are complete. Scientific confidence is high on the current reject verdict because independent systems, AI/ML, and product evidence converge on the same missing causal edges. Uncertainty remains about whether unpublished artifacts contain per-task results, exact mapping rules, or fault-bearing labels; such material cannot rescue a submitted paper if the reviewer cannot see it, but it affects repair cost.

**Next node:** only now read the authorized internal narrative/evaluation/background/questions and current cycle experiment/write-gate reports; audit cycle change, capability violations, repeated waste, and route the project in `400-cycle-change-audit-final-verdict-and-routing.md`. Internal material may explain the state but must not revise this paper-only/source-grounded scientific verdict.
