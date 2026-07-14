# Blind Full-Paper Review: AgentProf

## Reviewer Context

- **Target venue:** AAAI-27 Main Track.
- **Classification:** Genuinely cross-domain, but systems-primary. The paper proposes a systems-observability abstraction whose claimed value is improved analysis of AI-agent behavior. I therefore applied both the AI/ML and systems bars.
- **Review references loaded:** `research-taste.md`, `systems-review.md`, `ai-ml-review.md`, and `cross-domain-review.md`.
- **Sources read:** Complete `main.pdf`, complete `main.tex`, cited bibliography entries, and claim-bearing included figures/tables.
- **Blindness:** I did not read the prohibited planning/evaluation documents, `docs/tmp`, Git history/diffs, prior verdicts, or external sources, and I performed no web search. While auditing `figures/*.tex`, I encountered several unused, non-included table sources containing internal R-number provenance; I excluded them entirely from this assessment. The verdict below is based on the submitted manuscript only.

## Plain-Sentence Thesis and Principle

**Thesis:** AI-agent behavior can be profiled across runs by turning heterogeneous trajectory events into weighted records and treating selected semantic fields as synthetic stack frames.

**Purported principle:** A runtime call stack is not necessary for profiling if responsibility can instead be represented by stable semantic categories and additive measurements.

The recurring problem is plausible and important: developers cannot efficiently inspect growing collections of long agent trajectories to find repeated cost, failure, or safety patterns. The challenged belief, however, is not yet established as a real community belief. The paper shows that tracing tools center individual executions, but does not establish that users or existing systems regard runtime stacks as necessary, nor that multidimensional semantic aggregation is absent from current observability practice.

My taste assessment is **incomplete-but-promising**. The core idea is simple, but its claimed depth is not yet established: the paper does not demonstrate that a field-ordered aggregation is a valid responsibility stack rather than a useful OLAP/group-by view, and the broad dataset count obscures missing causal and end-user evidence.

## Paper Outline

1. **Motivation:** Agent developers need aggregate views of cost, failures, and unsafe effects across trajectories, beyond per-run debugging.
2. **Challenges:** Agent histories lack stable semantic identifiers and runtime call nesting.
3. **Model:** Normalize prompts, LLM calls, tools, and system effects into uniform weighted `operation` records. Project ordered operation fields into an `operation stack`, then fold identical stacks.
4. **Algorithms:** Derive fields through regex rules, a local LLM, TF-IDF/K-Means, structured mappings, or adjacent-operation boundary detection.
5. **Implementation:** An offline Rust CLI exports pprof, folded-stack, SVG, and JSON profiles. AgentSight data first passes through a separate adapter.
6. **Evaluation:**
   - RQ1: source-lineage fidelity, semantic separation, multi-view aggregation, and automatic grouping.
   - RQ2: concentration of released failure/risk signals on three public workloads.
   - RQ3: supervised group-boundary prediction and two task-partition clustering tests.
   - RQ4: offline profile construction time and memory.
7. **Claim:** Cross-trajectory semantic profiling complements run-local tracing and debugging.

## Claim–RQ–Evidence Map

| Claim or RQ | Presented evidence | Largest conclusion directly supported | Blind-review assessment |
|---|---|---|---|
| **Core model:** uniform operations plus query-time operation stacks constitute a new profiling layer | Formal view triple \((\varphi,\sigma,w)\), pprof export, three flame graphs, examples across multiple fields | Categorical agent-event data can be normalized and exported as field-ordered aggregate hierarchies | **Not enough for the claimed profiling principle.** Ordered categorical fields do not inherently encode causal nesting or shared responsibility. This currently resembles a relational group-by/pivot compiled into a flame-graph representation. |
| **D1 / source-linked cross-layer attribution** | Existing AgentSight path recovers 1,520/1,574 in-scope effects, reports 100% precision and 96.569% recall, and rejects 1,629 concurrent controls; AgentProf preserves all recovered samples | On the fixed 20-task declared process/tool scope, the existing source linker is highly precise and AgentProf folds its output without loss | Strong scoped engineering evidence, but most attribution correctness belongs to the predecessor AgentSight path. The current CLI does not directly ingest those recordings, and causal inheritance behavior is under-specified. |
| **RQ1: semantic profiling improves resource attribution** | Prompt tags reduce mixed weight from 90.4% to 36.7%; session-only leaves 84.4%; unique stacks rise from roughly 12k to 25k; tag permutation \(p=0.001\) | Adding a supplied prompt category refines groups according to that category | The construct is partly circular: grouping by the category used to define “mixed” groups must reduce mixing, especially as group count rises. This is partition refinement, not independent attribution correctness. |
| **RQ1: multiple resolutions and weights expose useful views** | Same operations fold into 9–3,757 groups; top token/time categories differ; three flame graphs | One normalized dataset can support several descriptive aggregate projections | Credible descriptive functionality, but no evidence that these views lead to correct or better decisions. The shown flame graphs contain thousands of hidden/truncated nodes and no worked diagnostic insight. |
| **RQ1: automatic induction helps initial exploration** | Six tasks; median 12 groups; median AP 0.276 versus 0.312 hand-specified; inspection work 65.3% of flat | The automatic method creates intermediate-size partitions and sometimes reduces inspection work relative to a flat summary | Weak and incomplete. It underperforms hand-specified stacks in AP, lacks per-task results and strong controls, and is not the method evaluated in RQ3. |
| **RQ2: output corresponds to real problems** | Three public workloads totaling 27,346 steps; AP 0.588 vs 0.556, Work@80 41.57% vs 46.29%, Work@50 19.55% vs 46.64%; targets held from final scoring; HINT field order chosen on validation data | Selected semantic grouping can concentrate existing released risk/localization signals better than raw-action grouping at the reported operating points | Encouraging, especially TraceElephant, but the baseline is weak and the construct is indirect. The groups are ranked using already available judge/localization signals; no comparison is made to raw step-signal ranking, native trace/session hierarchies, matched-size partitions, standard clustering, SQL/observability views, or analyst diagnosis. |
| **RQ3: tags are accurate and stable across unseen families** | Session-folded Bernoulli NB reaches 0.739 boundary F1 and 0.816 B³ F1 on OSWorld-Human; TF-IDF/K-Means reaches V-measure 0.557 on 9 Mind2Web sessions and 0.815 on 100 ScienceWorld sessions | An in-domain supervised boundary model generalizes to held-out sessions, and lexical clustering recovers some dataset task partitions | **RQ mismatch and incomplete answer.** Boundaries are not intent-tag semantics; the evaluated predictor is not the built-in stack inducer; literal tag accuracy and stability are untested; phase/action components are explicitly left unevaluated; “unseen agent and task families” is not established by session-blocked folds. |
| **RQ4: profiling is practical and predictable** | 27,765-operation union takes 1.17 s and 464.5 MiB; 18.2% time and 1.3% RSS over raw grouping; three runs; predecessor cache example | The current folding/export path runs quickly on inputs up to 27,765 operations on one high-end machine | Expensive capture and field derivation are excluded, scale is small relative to the motivation, 464.5 MiB is high for 27k operations, and the linear fit uses five heterogeneous natural workloads. The predecessor LLM-cache timing is not evidence about the current system. |
| **Generality across 15 families** | 47,590 mapped operations from heterogeneous agent/human datasets | A common record schema can encode these selected converted datasets | This demonstrates schema flexibility, not automatic semantic generalization. Dataset-specific mappings and available annotations may do most of the work. |

## Strongest Accept Case

The best accept argument is that the paper identifies a timely observability gap and offers a compact, reusable interface: normalize heterogeneous trajectory and system events into a single weighted representation, derive semantic fields through pluggable methods, and compile arbitrary projections into an established profiling ecosystem. The implementation is real, the source-lineage negative controls are unusually concrete, conservation during folding is checked, and several evaluations use held-out or target-blind signals rather than scoring the same labels used to build profiles. The paper also acknowledges important scope limits, including fixed manifest categories, the distinction between the supervised predictor and built-in inducer, and missing phase/action evidence.

The three RQ2 workloads suggest that semantic grouping can add signal beyond raw action, with a particularly large TraceElephant improvement. The OSWorld-Human evaluation uses session-blocked out-of-fold prediction and evaluates both local boundaries and whole-partition agreement. These are better practices than a purely visual tool paper.

If the contribution were judged as an AI-systems artifact or demonstration, a strong artifact with transparent configurations and compelling interactive cases could be useful. For AAAI Main Track, however, the paper must show that the abstraction changes how agent failures are understood or fixed, not only that agent traces can be rearranged into pprof-shaped categories.

## Ranked Attack Map

### Blocker 1 — A categorical projection is not yet a responsibility stack

**Category:** Scientific framing / technical mechanism  
**Locations:** Abstract; Introduction thesis; D3; “Semantic Operation Stack Model”; RQ1.

A runtime call stack has execution-defined ancestry: each prefix corresponds to an actual active causal context, and self/inclusive cost has a defined interpretation. AgentProf permits any ordered list of fields to become a stack. Field order therefore creates visual parent–child relationships that may have no causal, temporal, containment, or responsibility semantics.

The paper claims that operation stacks “serve the same role” as call stacks, but currently demonstrates only nested categorical aggregation. For example, switching the order of `session`, `prompt_tag`, `kind`, and `model` changes the apparent responsibility hierarchy without any invariant explaining which order is truthful. A user-selected hierarchy may be useful, but it is not automatically an attribution hierarchy.

The reviewer inference that fails is: “width under an operation-stack prefix is cost for which that prefix shares responsibility.” What is shown is only: “width is the sum of records sharing a field prefix.”

**Required gate:** Both WRITE and EXPERIMENT. Define hierarchy-validity invariants, distinguish causal containment from exploratory faceting, and test whether valid stack configurations support correct attribution better than ordinary multidimensional aggregation.

### Blocker 2 — The central promised utility is not measured

**Category:** Evidence/evaluation  
**Locations:** Abstract and Introduction motivation; RQ2; Conclusion.

The paper motivates improvements to agent quality, safety, and cost efficiency, but measures none of these outcomes. RQ2 measures how grouping affects the concentration of already available judge or localization signals. It does not show that a developer finds the correct root cause faster, avoids a false accusation, identifies a recurring pattern unavailable in a trace, chooses a corrective action, or improves a subsequent agent run.

The baseline is raw-action grouping, not the strongest available diagnosis workflow. The paper does not compare against:

- ranking the released step signal directly;
- native per-session or span-tree inspection;
- fixed-window or change-point segmentation;
- matched-cardinality random or lexical partitions;
- SQL/OLAP aggregation over the same fields;
- pprof labels without the new abstraction;
- current hierarchical observability products;
- a trained localization/ranking baseline;
- human analysts using a standard trace UI.

The strong TraceElephant result may arise from useful aggregation, but the paper has not shown that “profiling” rather than dataset-specific grouping improves diagnosis.

**Required gate:** EXPERIMENT. The repair should strengthen the larger human/actionability claim, not merely narrow “improves diagnosis” to “changes AP.”

### Blocker 3 — RQ3 is materially unanswered and methodologically mismatched

**Category:** Evidence/evaluation / global consistency  
**Locations:** RQ3 question and hypothesis; Implementation boundary construction; Scope and Limitations; Abstract.

RQ3 asks “How accurate are the tags?” and hypothesizes accurate, stable task, phase, action, and boundary recovery on unseen agent and task families. The main result instead evaluates an in-domain supervised Bernoulli Naive Bayes boundary predictor under session-held-out folds. The paper explicitly states that this is not the built-in Rust stack inducer described as AgentProf’s automatic construction method.

The task-partition evidence also does not close the RQ:

- Mind2Web has only nine sessions.
- ScienceWorld has 100 sessions from one environment.
- V-measure evaluates partition agreement, not tag meaning.
- A constant-tag control is too weak.
- Cluster-count selection and other hyperparameters are not reported.
- Repeatability across model runs, prompts, or time is not measured.
- Phase and action accuracy are explicitly left for future work.

The paper nonetheless says RQ3 is answered positively. Under the skill’s full-paper bar, a load-bearing empirical RQ cannot retain untested components while being reported as answered.

**Required gate:** EXPERIMENT, followed by WRITE. Evaluate the actual production/default methods under cross-task or cross-family holdout, or separate the RQ into claims that are genuinely answered.

### Major 1 — RQ1’s primary metric rewards adding the evaluated tag

**Category:** Evidence/evaluation  
**Location:** RQ1 mixed-weight ablation and Figure 3.

“Mixed weight” is defined by whether groups contain multiple prompt-tag categories, and the intervention adds `prompt_tag` to the grouping key. Lower mixing is therefore structurally expected. The simultaneous near-doubling of unique stacks makes the result even less diagnostic: sufficiently fine partitioning drives purity upward regardless of semantic quality.

The within-tag permutation test shows the observed tag aligns with its resulting partitions better than a random assignment, but it does not establish attribution correctness or rule out fragmentation as the cause. A fair analysis needs matched-cardinality/random-refinement controls, adjusted information measures, compression-versus-purity curves, and an independent outcome.

**Required gate:** EXPERIMENT.

### Major 2 — “Additive measures” are not validly defined for duration

**Category:** Technical mechanism / systems soundness  
**Locations:** Operation definition; built-in `time` view; flame graphs.

Token counts, file-event counts, and network-event counts can be additive under a clearly defined sampling unit. Wall-clock duration generally is not additive across nested, overlapping, or concurrent prompts, LLM calls, tools, and processes. Summing durations for all timed operation types may double- or triple-count the same elapsed interval. The paper does not define self time versus inclusive time, overlap handling, concurrency semantics, sampling, or conservation for duration.

This threatens the meaning of the time flame graph and the claim that all measures can be folded uniformly. The very motivation involves concurrent and cross-layer activity, where duration additivity is most dangerous.

**Required gate:** Technical clarification plus correctness experiment using synthetic overlapping/nested timelines and known total/self-time or resource-time oracles.

### Major 3 — Source attribution belongs partly to a separate predecessor path

**Category:** Technical mechanism / global logic  
**Locations:** Implementation input reconstruction; RQ1 lineage experiment; Conclusion.

The paper uses the existing AgentSight 0.2.37 capture/join path, converts its output through an adapter, and only then folds it with AgentProf. The current CLI does not directly read AgentSight recordings. Thus, the impressive precision/recall and concurrent-control result verifies the predecessor correlation path, while AgentProf’s demonstrated contribution is lossless folding of already joined records.

Moreover, the paper says the operation representation and tag propagation “satisfy D1,” but a record schema does not establish causal linkage. The algorithm for inheritance through asynchronous tools, subprocesses, retries, concurrent tasks, and many-to-many effects is not specified.

**Required gate:** WRITE for contribution ownership and mechanism definition; EXPERIMENT for end-to-end current-system attribution.

### Major 4 — Existing-tool and novelty baseline risk is load-bearing

**Category:** Novelty / scientific framing  
**Locations:** Introduction existing solutions; Related Work.

The paper itself acknowledges LangSmith Insights and Datadog Patterns as cross-trace hierarchical categorization systems with aggregate metrics. The distinction is then narrowed to the conjunction of “source-linked,” “additive,” “selectable,” and “pprof-compatible.” This may be an engineering feature combination rather than a durable scientific principle.

Likewise, pprof already supports labels/tag promotion, and Perfetto supports flexible derived-event queries. Without external verification and direct comparison, a reviewer can reasonably read AgentProf as a standard relational event table plus group-by dimensions exported into an existing visualization.

**Required gate:** External source verification in the next review phase, then a direct baseline or a sharper mechanism distinction. This is a blocker risk if the closest systems already implement the same claim.

### Major 5 — Generalization is produced by mappings more than demonstrated by the model

**Category:** Evidence/evaluation  
**Locations:** Dataset overview; intent-attribution interface; RQ1 and RQ2.

Fifteen datasets demonstrate that a flexible string-field schema can encode heterogeneous data, but each public family is converted using mapping rules and potentially source-native task, phase, action, or quality attributes. The paper provides no compact table of per-dataset input fields, mapping logic, selected stack, group count, or tuning decisions. It is therefore impossible to tell how much value comes from AgentProf versus benchmark-specific semantic engineering.

HINT explicitly uses validation labels to select among 24 field orders. That is defensible for benchmark tuning, but it weakens the claim of a general target-blind profiler and should not be blended with zero-configuration or cross-family generalization.

**Required gate:** EXPERIMENT with preregistered configurations and dataset/family holdout; WRITE with full per-workload provenance.

### Major 6 — RQ2 mixes targets, ranking signals, metrics, and operating points

**Category:** Global logic / evaluation  
**Location:** RQ2.

AgentProcessBench uses AP; HINT uses Work@80; TraceElephant uses Work@50. Different signals and ranking rules are used across datasets. This may be justified by workload properties, but the manuscript does not give a common metric surface or explain why those operating points were fixed before evaluation. A skeptical reviewer will suspect favorable-point selection.

The paper should report a common suite such as AP plus work/recall curves for every workload, uncertainty at the task/family level, and negative cases. HINT’s improvement is modest, AgentProcessBench’s AP gain is small, and TraceElephant’s gain is large; the heterogeneity is scientifically interesting but currently hidden behind three headline numbers.

**Required gate:** EXPERIMENT/analysis, then WRITE.

### Major 7 — The performance claim excludes the expensive and relevant path

**Category:** Systems evaluation  
**Location:** RQ4.

The measured path begins from operation JSONL and excludes capture, reconstruction from native histories, current-model field derivation, and analyst iteration. Only three runs are used. The 27,765-operation maximum is small relative to the motivation of multi-month production histories and even smaller than the paper’s 183,714 system observations. Peak RSS of 464.5 MiB for 27,765 operations is potentially concerning.

The \(R^2=0.9997\) line across four heterogeneous workloads and their union is descriptive rather than a scaling experiment. The predecessor AgentFlame cache result should not support current AgentProf performance.

**Required gate:** EXPERIMENT at controlled scales through at least millions of operations, with end-to-end cold/warm timings and memory breakdown.

### Major 8 — Reproducibility details are insufficient for the semantic methods

**Category:** Evidence/evaluation / submission readiness  
**Locations:** Implementation and RQ3.

Missing information includes:

- exact local 3B model, quantization, prompt, decoding configuration, and taxonomy;
- regex rules and how “5–10 rounds” was measured;
- all nine Naive Bayes feature fields;
- fold construction and threshold-selection objective;
- clustering \(k\), initialization, seeds, preprocessing, and tuning;
- boundary-inducer formula, weights, thresholds, and depth behavior;
- per-workload fields and mappings;
- exact signal/ranker/profile definitions for RQ2.

The “stable” and “repeatable” tag claims are especially unsupported without repeated-run agreement.

**Required gate:** WRITE plus replication tests.

### Minor Findings

- The manuscript alternates among AgentProf, the `agentpprof` binary, prior AgentFlame, and the AgentSight adapter, producing an unclear artifact boundary.
- “The same model covers all 15 families” appears to mean data schema, not a learned model.
- The flame graphs are visually dense, contain thousands of hidden nodes, and truncate most labels; they demonstrate renderability more than insight.
- The paper lacks a worked case where a profile reveals a recurring issue and leads to a concrete configuration or agent fix.
- “Real problems” conflates human process labels, judge votes, released localization predictions, safety risk, and causal root causes.
- Privacy and data-governance implications of parsing local agent histories are absent.
- “Five to ten rounds” of regex refinement is an unsubstantiated usability claim.
- Evaluation is listed as a contribution, but the scientific contribution of the evaluation itself is not identified.

## Strongest Alternative Explanations

1. **Partition refinement:** Adding prompt tags reduces mixed-weight percentage because the purity metric is defined by those same tags and the number of groups increases sharply.
2. **Dataset metadata does the work:** RQ2 gains may come from hand-selected/mapped dataset-native semantic fields rather than the operation-stack abstraction.
3. **Existing risk signals do the work:** RQ2 ranks groups using released judge/localization signals. Aggregating a good step signal may explain the result without a novel profiling mechanism.
4. **In-domain lexical regularity:** TF-IDF/K-Means task partitioning may exploit benchmark-specific lexical templates rather than general intent understanding.
5. **Boundary base rate and visible annotations:** The always-boundary baseline already reaches 0.645 F1, and the supervised model may learn action/phase regularities tightly coupled to OSWorld-Human’s annotation policy.
6. **Source fidelity is inherited:** The cross-layer precision/recall result is primarily evidence for AgentSight’s existing source join; AgentProf only preserves the accepted records.
7. **Low cost comes from excluding semantics:** RQ4 appears fast because current LLM tagging, source reconstruction, capture, and analyst iteration are outside the timed path.
8. **The visualization is incidental:** A conventional event table queried with SQL and rendered as nested bars could yield the same information; pprof compatibility may not change analytic capability.

## Missing Evidence and Baselines

### Central utility

- A blinded analyst study measuring time to correct root cause, false diagnoses, coverage, and successful corrective action.
- Real examples where aggregate semantic profiling finds a repeated failure or unsafe effect missed by per-run tracing.
- Evidence that identified hot categories produce a quality, safety, latency, token, or cost improvement after intervention.

### Fair aggregation baselines

- Direct step-signal ranking.
- Flat, per-session, native span-tree, fixed-window, and change-point views.
- Matched-cardinality random partitions.
- Hierarchical clustering or embedding-based grouping.
- SQL/OLAP aggregation using the same fields.
- pprof label/tagroot views without AgentProf’s new model.
- Current observability hierarchy systems using the same traces, or faithful reproductions of their category/metric views.

### Attribution validity

- Ground-truth causal linkage across asynchronous subprocesses, concurrent tasks, retries, shared processes, and background effects.
- Per-measure conservation tests, especially duration with overlapping operations.
- Comparison of inherited semantic fields against independently annotated responsible prompts/tools.

### Tag and hierarchy quality

- Literal semantic tag accuracy, coverage, calibration, and inter-run stability.
- Cross-project, cross-agent, or leave-family-out evaluation.
- Evaluation of the actual built-in Rust inducer.
- Strong supervised and unsupervised segmentation controls.
- Phase/action results or a narrower completed RQ.
- Profile-order validity: whether different field orders produce truthful versus misleading attributions.

### Scale and systems behavior

- Controlled scaling to multi-month production sizes.
- End-to-end reconstruction, derivation, folding, serialization, and rendering.
- Current LLM-tagging latency and resource use.
- Peak-memory breakdown and streaming alternatives.
- Robustness to malformed traces, missing fields, clock errors, and partial source linkage.

### External verification needed after the blind phase

- Whether current LangSmith, Datadog, Phoenix, Langfuse, OpenTelemetry, and Perfetto capabilities already cover the same semantic hierarchy and aggregation claim.
- Whether “agent observability needs profiling” reflects a documented user/deployment problem rather than a terminology choice.
- Whether cited benchmark signals and snapshots support the exact uses described.
- Whether the pprof/label distinction is technically novel.

## Story and Terminology Problems

- **“Operation stack”** overstates the semantics. A stack implies execution nesting or valid ancestry; the mechanism is an ordered categorical projection.
- **“Resource attribution”** is used for both causal source linkage and reduced category mixing. These are different constructs and should not share one RQ without a clear causal chain.
- **“Intent attribution”** umbrellas regex classification, LLM naming, TF-IDF clustering, structured mappings, and boundary prediction. Several do not infer intent.
- **“Tag accuracy”** includes task partitioning and temporal boundaries but does not evaluate tag-name accuracy.
- **“Stable and repeatable”** is asserted but never measured.
- **“Automatic stack induction”** refers to at least three distinct mechanisms: the Rust boundary inducer, supervised Naive Bayes boundaries, and TF-IDF/K-Means task grouping.
- **“Source-linked” and “source lineage”** are central but not operationally defined in the model section.
- **“Additive duration”** is technically unsafe without self/inclusive/concurrency semantics.
- **“Same model covers 15 families”** conflates a common schema with one generalizing inference model.
- **“Real problems”** includes benchmark labels and released model predictions, not necessarily real root causes or unsafe outcomes.
- The story moves among three possible contributions—cross-layer source attribution, semantic grouping, and pprof export—without identifying which is the indispensable scientific mechanism.
- The paper’s strongest empirical result, target-blind problem concentration, is not causally connected to the source-linked system-effects contribution: all RQ2 workloads appear to operate on public mapped operations rather than the end-to-end AgentSight path.

Terms that could be deleted or merged without losing explanatory power include “semantic operation stack model” and “operation stack” unless a valid hierarchy invariant is added; “intent attribution” could be replaced by the more accurate “field derivation”; and “tag accuracy” should be separated into semantic classification, task partitioning, and boundary segmentation.

## AAAI-27 Relevance and Fit

The problem is relevant to AAAI: reliable, safe, and economical AI agents need scalable behavioral diagnosis. A general method that demonstrably reduces the effort to locate recurring agent failures would have broad AI significance.

The current contribution, however, reads primarily as a systems-observability data model and export tool:

- The AI algorithms are standard regex, small-LLM tagging, TF-IDF/K-Means, and Bernoulli Naive Bayes.
- No new empirical insight about agent behavior is established.
- No agent policy, quality, safety, or cost outcome improves.
- The central abstraction is close to multidimensional aggregation.
- The strongest system mechanism, source lineage, is inherited from AgentSight.
- The paper does not yet show analyst or developer utility against trace-centric tools.

This makes the manuscript a more natural fit for an AI-systems workshop, observability venue, systems artifact track, or AAAI demonstration in its current form. It can become AAAI Main Track material if it elevates and substantiates the broader claim that semantic cross-trajectory profiles enable materially better agent diagnosis across systems.

## Largest Defensible Claim

The largest claim fully supported by the current manuscript is:

> Given correctly linked operations and supplied or derived categorical fields, AgentProf losslessly folds heterogeneous offline agent records into selectable pprof-compatible aggregate hierarchies; on the tested public corpora, selected semantic groupings concentrate released problem signals better than raw-action grouping at specific reported operating points, while processing 27,765 operations in 1.17 seconds.

The larger claim worth defending is:

> Cross-trajectory semantic profiling reduces the effort required to discover recurring, actionable agent failures compared with trace-centric observability.

The current evidence almost approaches this claim, but does not measure discovery effort, correctness, or actionability directly.

## Decisive Minimal Next Experiment

Run one preregistered, held-out, time-bounded diagnosis study over real agent failures.

- Use at least three agent/workload families from a project not used to choose mappings or stack orders.
- Give each condition exactly the same source data and released risk signals.
- Compare:
  1. AgentProf with configuration fixed before test release;
  2. direct step-signal ranking;
  3. native session/span-tree inspection;
  4. a matched SQL/category or current observability-style hierarchy.
- Use a blinded crossover with roughly 12 practitioners and 30–40 diagnosis tasks.
- Require participants to identify a human-verified root cause and choose a corrective action; where feasible, execute the action and check whether the failure recurs.
- Measure time to correct diagnosis, operations inspected, false attribution rate, root-cause recall, action validity, and confidence.
- Include an AgentProf ablation without source-linked effects to test whether the cross-layer mechanism contributes beyond semantic grouping.

A clear reduction in diagnosis time and false attribution across held-out families would validate the important AAAI-level principle. Failure would reveal whether the useful contribution is only a visualization/export layer or whether a different hierarchy mechanism is needed.

## Provisional Verdict

- **Score:** **4/10 — Weak Reject**
- **Confidence:** **4/5**
- **Taste classification:** **Incomplete-but-promising.**

The paper is polished, timely, and backed by substantial implementation and dataset work. Its acceptance case is weakened by three load-bearing issues: a categorical field order is not yet shown to be a valid responsibility stack; the central agent-diagnosis utility is measured only through indirect concentration proxies against weak baselines; and RQ3 is broader than the evaluated methods and remains explicitly incomplete. A decisive end-to-end diagnosis experiment, together with stronger hierarchy semantics and baseline parity, could materially change the verdict.
