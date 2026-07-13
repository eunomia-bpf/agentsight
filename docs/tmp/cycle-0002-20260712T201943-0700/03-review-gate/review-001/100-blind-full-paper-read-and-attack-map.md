# Review 001 / Node 100: Blind Full-Paper Read and Attack Map

## Context and status

- **Timestamp:** started 2026-07-13T10:39:42-07:00; completed 2026-07-13T10:47:08-07:00.
- **Phase / step / gate:** `BUILD_AND_EVALUATE` / cycle 0002 / `REVIEW_GATE`.
- **Parent:** `docs/tmp/cycle-0002-20260712T201943-0700/03-review-gate/000-gate-entry-20260713T103942-0700.md` (path observed but report content deliberately not read).
- **Node status:** complete for the declared paper-only blind-read scope.
- **Target venue and domain:** AAAI-27 Main Track; genuinely cross-domain because the central claim depends simultaneously on a systems abstraction and implementation, an AI semantic-attribution method, and an empirical agent-evaluation construct. I therefore apply both the systems and AI/ML bars, plus the cross-domain causal-chain bar.
- **Review references loaded before entry:** `iter-review-critique/SKILL.md`, `research-taste.md`, `systems-review.md`, `ai-ml-review.md`, `cross-domain-review.md`, `auto-research-orchestrator/SKILL.md`, and the requested sections of `hierarchical-research-state-machine.md`.

## Objective and entry conditions

This node asks what a fresh skeptical AAAI reviewer would conclude from the submitted paper alone, before searching the literature or seeing the project's intended answers, prior reviewer verdicts, repair plans, experiment history, or current-cycle gate reports. The fixed scientific contract used only as an authority constraint is:

- thesis: **“Agent observability needs profiling, not only debugging.”**
- RQ1: resource attribution;
- RQ2: real-problem localization;
- RQ3: tag accuracy;
- RQ4: profiling cost.

The review does not delete, merge, rename, or change the meaning of these RQs and does not recommend shrinking or replacing the thesis.

## Inputs, provenance, and isolation

I read `docs/user-instruction.md` in full to establish scope and permissions. I then read the reader-facing paper independently: all 936 lines of `docs/paper/main.tex`, all 794 lines of `references.bib`, the complete nine-page `main.pdf` as extracted text and rendered pages, every main-text claim-bearing figure and table, the architecture source, the build README and Makefile, the reproducibility checklist, and LaTeX build diagnostics. I visually inspected the three semantic flame graphs, RQ1 separation chart, RQ3 mapping chart, architecture diagram, and the full PDF page layout. I also inspected the paper-local figure-generating scripts and data present under `docs/paper/` to distinguish reader-facing evidence from stale assets.

I did **not** read `docs/evaluation.md`, `docs/idea-story.md`, `docs/background-related-work.md`, `docs/questions-for-author.md`, any historical or current reviewer verdict, any author repair report, or the experiment/write gate reports. I did not search the web or open external papers during this node.

### Reviewer-context and contamination disclosure

The task simultaneously required reading all content under `docs/paper/` and prohibited exposure to proposed fixes before the attack map. After reading `main.tex`, `references.bib`, and the rendered PDF and forming the core judgment below, the all-content pass exposed unused files under `docs/paper/figures/` named `claim-gate-table.tex`, `evidence-path-table.tex`, `experiment-role-table.tex`, `task-verdict-table.tex`, and `case-table.tex`. Those files contain old gate language, counterpoints, and patch dispositions and are not included by `main.tex`. This is an unavoidable limited contamination caused by the all-directory requirement. I quarantined them as non-reader-facing artifacts: none is used as support for a blind-review finding, and the paper-only verdict below was formed from the submitted manuscript first. The unrelated `make_benchmarks.py` and `data/{redis,startup}.json` are stale Sandlock assets and also play no role.

## Method

I reconstructed the paper as one argument rather than reviewing sections independently:

1. extract the problem, challenged belief, principle, mechanism, claimed scope, and causal chain;
2. map every major paper claim to one of the four fixed RQs;
3. inspect definitions, baselines, metrics, controls, and figures for construct validity and circularity;
4. test global agreement among abstract, introduction, design, implementation, evaluation, figures, and conclusion;
5. generate reject hypotheses across framing, novelty, mechanism, evidence, consistency, and writing;
6. rank them by whether they defeat the thesis at the current evidence level or can be repaired by stronger mechanism, protocol, baseline, or experiment without changing the scientific contract.

No external factual claim in this report is treated as verified yet. Novelty and status-quo objections below are search targets, not final literature conclusions.

## Paper reconstructed in plain language

### Problem and stakes

Teams accumulate many long agent trajectories. Debugging one execution at a time cannot answer population questions such as which semantic task categories consume tokens, time, files, or network operations, or where recurring failures and unsafe actions concentrate.

### Plain-language principle

**Treat many agent runs like a program profile: attach additive costs and effects to stable semantic categories, then aggregate them across runs at whatever hierarchy answers the current question.**

This is the paper's best durable idea and faithfully instantiates the fixed thesis that agent observability needs profiling, not only debugging.

### Challenged belief

The paper intends to challenge the belief that per-execution traces, span trees, and input clusters are sufficient observability abstractions for agents. From the paper alone, the belief is plausible but not yet shown to be a real community or operator belief rather than a contrast selected for the paper: no deployment incident, analyst workflow, user evidence, or accepted observability requirement demonstrates that teams currently fail because they lack population-level semantic resource attribution.

### Artifact and causal chain

The intended chain is:

```text
natural-language, multi-step agent workloads
-> no stable cross-run semantic identifiers or canonical hierarchy
-> reconstruct operations, inherit semantic tags across effects, and project fields into query-time stacks
-> fold additive resource measures across trajectories
-> expose costly categories and concentrate real problems for inspection
-> improve quality, safety, and cost decisions
```

The paper presents evidence for the middle aggregation step. It does not yet credibly establish the two hardest edges: that intent/effect inheritance is correct under real agent concurrency and that the resulting profile improves detection or decisions about real problems.

### Claimed contributions

1. A semantic operation-stack model: uniform weighted operations plus query-time ordered field projections.
2. AgentProf, a roughly 9.8K-line offline Rust implementation with regex, local-LLM, clustering, mapping, pprof, folded stacks, SVG, and JSON.
3. Evaluation over 325 local Codex/Claude trajectories and 15 public trajectory families, organized into the four fixed RQs.

## Initial verdict

**Paper-only verdict: reject in current form; incomplete-but-promising.** The principle is simple and potentially deep, and the system provides a concrete vehicle for it. The current evaluation, however, mostly demonstrates that curated semantic fields can repartition records and that tuned visible-field groupings correlate weakly with annotations. It does not yet isolate the operation-stack mechanism from ordinary multidimensional aggregation, validate the central prompt-intent tagger, establish correct cross-layer attribution, or show that a profile locates real problems better than strong trace/analysis baselines. At AAAI, the AI semantic-attribution bar and empirical validity bar are not met; at a systems bar, the attribution invariant, concurrency/failure semantics, baseline parity, and resource-cost accounting are not met.

The paper is not complicated-but-shallow in conception: the central idea is economical. It is **incomplete-but-promising** because the implementation and dataset volume currently exceed the explanatory and experimental force of the evidence.

## Strongest paper-only reject argument

The evaluation's central benefit is not independently identified. RQ1 defines success as lower mixing among task categories, then adds `prompt_tag`—the category identifier itself—to the grouping key. RQ2 allows dataset-specific stack fields, mapping rules, ranking criteria, and later re-runs on the same operations, yet compares against weak or mismatched flat/session/native groupings. RQ3 evaluates mappings from structured native action fields to phases, not the natural-language prompt tagger that RQ1 depends on. Therefore the reported gains can be explained by curated visible annotations and task-specific grouping/ranking, rather than by the proposed semantic operation-stack abstraction or a general agent-profiling capability.

This is a blocker because it breaks the claimed causal chain at both layers: the AI layer has not shown that natural-language intent can be tagged accurately out of distribution, and the systems layer has not shown that query-time operation stacks provide benefit beyond equivalent relational/trace aggregation under information and tuning parity.

## Attack map

### Blockers

#### B1 — Evidence/evaluation: RQ2 does not presently establish real-problem localization

- **Paper locations:** abstract; Introduction evaluation summary; §5.2; Table 1; conclusion.
- **Claim:** AgentProf “locates annotated problems while inspecting 9.4% of work,” uses 45% fewer groups than per-session grouping, and concentrates positives into fewer, higher-quality groups.
- **Failed inference:** Table 1 reports median operation-stack AP 0.312, below per-session AP 0.348 and native-hierarchy AP 0.357. Its top-five recall is only 0.188. The 9.4% number is work spent, not problem coverage; it omits in the headline that the top five recover a median 18.8% of positives. At 30% inspection, recall is 39%. The method therefore occupies one tradeoff point rather than showing superior localization.
- **Protocol threat:** “query-aware” ranking is not defined; task-specific fields, mapping rules, ranking criteria, and depth can be changed and re-run on the same operations, with improvement on 5/6 tasks. That reads as test-set adaptation. There is no frozen development/test split for the entire profiling policy, no end-to-end strong baseline with equal visible information and tuning, no per-task matrix in the paper, and no analyst or decision outcome.
- **Required route:** `EXPERIMENT_GATE`, not claim shrinkage. Freeze the profiler policy before evaluation, run it on an external benchmark whose problem annotations remain hidden, compare at matched information/tuning budget against strong trace, multidimensional-query, and diagnosis baselines, and report fixed-recall inspection cost plus per-task uncertainty.

#### B2 — Evidence/evaluation: RQ3 does not test the load-bearing tag-accuracy claim

- **Paper locations:** abstract; DR2; §3.3; implementation tagging backends; §5.3; Figure 4.
- **Claim:** intent attribution derives stable tags from natural-language behavior, and derived tags agree with ground truth on seven of nine held-out datasets.
- **Failed inference:** RQ3 evaluates mapping rules from existing structured fields to `phase`, compared with datasets' native `action` annotations. It does not evaluate regex prompt tags, the local 3B LLM tagger, TF-IDF/K-means authoring, tag stability across paraphrases/runs/models, or the `prompt_tag` used in the RQ1 ablation. “Tags” in the abstract therefore merges two different mechanisms and label meanings.
- **Construct threat:** action labels from nine heterogeneous datasets need not define a shared semantic phase ontology. V-measure of 1.0 can arise from nearly direct relabeling of native fields rather than general natural-language understanding. The rule-induction procedure, access to label schemas, human intervention, parameter choice, and train/test isolation are unspecified. The arbitrary 0.7 threshold is treated as success without justification.
- **Required route:** `EXPERIMENT_GATE`. Test the actual intent-attribution backends on a public, held-out, natural-language intent or trajectory dataset with a predeclared ontology and fully frozen rules/prompts; include paraphrase consistency, coverage/abstention, macro metrics, and variance. Preserve RQ3's meaning—tag accuracy—while measuring the load-bearing tagger rather than a structured-field proxy.

#### B3 — Mechanism/evidence: RQ1's main metric is partly tautological and never validates cross-layer responsibility

- **Paper locations:** DR1, operation/tag inheritance prose, §5.1, Figure 3.
- **Claim:** semantic profiling improves resource attribution and semantic tags are necessary for meaningful attribution.
- **Failed inference:** adding `prompt_tag` to the grouping key necessarily reduces groups that mix prompt tags. The “both fields” 0% result is definitional. A permutation only tests whether the observed labels are associated with the same categories used to score grouping; it does not establish that the prompt intent caused or is responsible for each downstream system effect.
- **Missing invariant:** the paper never specifies how inheritance behaves across concurrent tools, subprocesses, asynchronous I/O, nested subagents, shared processes, background work, ambiguous parentage, missing events, or overlapping prompts. No ground-truth attribution sample or error analysis validates the reconstructed intent-effect edge.
- **Numerical overclaim:** the reader-facing text says AgentProf “separates over 90%” of cost that session views cannot attribute. Figure 3 instead shows mixed weight declining from 90.4% with neither field (84.4% with session) to 36.7% with `prompt_tag`, a 53.7- or 47.7-point reduction, not separation of more than 90% of the cost.
- **Required route:** `EXPERIMENT_GATE`. Use externally generated traces or injected operations with known causal task/effect ownership and measure attribution precision/recall under concurrency, subprocesses, async work, and missing events, while preserving RQ1 as resource attribution.

#### B4 — Novelty/mechanism: operation stacks may be a renamed multidimensional aggregation, not a new hierarchy mechanism

- **Paper locations:** semantic operation-stack model; field-selection comparison; related work.
- **Claim:** a flat `GROUP BY` cannot produce the views, while operation stacks supply a new multi-resolution semantic hierarchy.
- **Failed inference:** the paper narrows the alternative to `GROUP BY` on one tag. An ordered tuple of fields followed by grouping is ordinary multidimensional aggregation; database grouping sets, rollups/cubes, dataframe pivots, trace SQL, and label-derived flame-graph frames are obvious candidate mechanisms. The paper does not show a semantic or computational property that those mechanisms cannot express.
- **Required route:** external novelty verification followed by a mechanism/baseline experiment. The repair should expose the deeper invariant—conserved cross-layer responsibility with query-time hierarchy—and compare against information-equivalent OLAP/trace implementations, rather than shrinking the thesis to a visualization tool.

### Major findings

#### M1 — Mechanism: automatic stack induction is underspecified and weakly justified

The induction score, objective, recursion, balance/depth constraints, tie handling, complexity, stopping condition, hyperparameters, and training/tuning boundary are absent. Median AP 0.276 is below hand-specified 0.312 and several baselines; “substantially outperforms flat” is insufficient to establish a reusable hierarchy. A reader cannot reproduce or reason about the algorithm or distinguish it from change-point segmentation.

#### M2 — Evidence/evaluation: RQ4 excludes the dominant one-time cost while calling the result “complete profiling”

The 1.6 s median over 76 configurations appears to cover parsing/stacking/folding after tags exist. The full-history path issued 35,136 llama.cpp calls. Multiplying the separately measured 31 ms p95 by that count suggests a scale of roughly 18 minutes, but the paper never reports measured full-history tagger wall time, hardware, memory, energy, model identity/quantization, batch/concurrency, cold-cache cost, or dataset size per configuration. “Complete profiling takes seconds” is not supported for first-time profiling. This needs a complete cold-cache and warm-cache resource accounting, not a smaller RQ.

#### M3 — AI/ML evidence: no uncertainty, model/version, prompt, or selection-budget accounting for semantic tagging

The local model is only described as “such as a quantized 3B-parameter model.” The prompt, grammar, decoding, model checkpoint, cache key, training contamination, sampling determinism, and rule-refinement budget are not given. “An AI agent can refine rules until unmatched rate drops below 5%, typically in 5–10 rounds” is an unsupported empirical claim and risks test-set steering.

#### M4 — Systems evidence: implementation description is too shallow for correctness or deployment reasoning

Nine point eight KLOC and file-format support do not substitute for interfaces and invariants. The paper omits event identity, timestamp/order semantics, cross-source joins, tag precedence/inheritance, collision handling, missing-data behavior, persistent storage, scale complexity, privacy, failure recovery, and correctness tests. It also does not distinguish AgentProf's contribution from the pre-existing AgentSight capture layer.

#### M5 — Framing/evidence: real-world importance is asserted at scale but not tied to the proposed failure mode

Millions of requests and million-token runs establish volume, not that population-level semantic resource attribution is a current operational bottleneck or changes a production decision. The evaluation's 325 local trajectories come from one multi-month development project, with no project/task sampling, ownership, privacy, representativeness, or held-out period. A production incident, workflow, or public multi-run deployment anchor is needed.

#### M6 — Evaluation: median-over-six aggregation hides heterogeneity and multiple-comparison risk

Six “tasks” span four datasets and different positive semantics (looping, side effects, safety, incorrect/redundant steps, human boundaries). Taking medians across them does not define a common population. Task-family bootstrap intervals with at most four families cannot compensate for selection and dependence. The main paper omits task-level results, prevalence, confidence intervals, and all exact differences mentioned in the statistical-validation paragraph.

#### M7 — Global consistency: multiple claims do not match their displayed evidence

- “over 90% separated” conflates baseline mixed weight with the reduction achieved;
- “higher-quality groups” conflicts with lower AP than per-session/native baselines;
- “locates problems while inspecting 9.4%” suppresses the accompanying 18.8% top-five recall;
- “tags agree with ground truth” conflates mapping-derived phase/action agreement with prompt-intent tagging;
- “complete profiling takes seconds” excludes the one-time tagger workload;
- Figure 1 says all views arise by changing stack fields and weight, but the displayed stacks still contain session and prompt hierarchy; it illustrates output variety, not causal or operational usefulness.

#### M8 — Submission readiness: reproducibility fields are absent

The AAAI reproducibility checklist is entirely unfilled. The manuscript omits code/artifact availability, dataset preprocessing, licenses for private trajectories, hardware/software versions, all hyperparameters, run counts for many results, random seeds, exact prompts/rules, and source-native result links. The paper compiles and visually fits the nine-page envelope with references beginning on page seven, but scientific reproducibility is not ready.

### Minor findings

1. **Writing/terminology:** “semantic operation stack,” “intent attribution,” and “stack construction” are useful only if each adds a distinct falsifiable property. At present, operation stacks are ordered grouping fields, intent attribution covers unrelated regex/LLM/clustering/mapping mechanisms, and stack induction is segmentation. The vocabulary risks making ordinary data transformations appear deeper than specified.
2. **Writing:** related work is one short paragraph and mostly enumerates tools. It does not compare problem, information access, hierarchy semantics, ranking, evaluation protocol, or mechanism.
3. **Evidence:** no ablation separates uniform-operation representation, tag inheritance, ordered projection, hierarchical visualization, and query-aware ranking.
4. **Evidence:** no quality/correctness constraint accompanies performance/resource views; grouping cost does not itself show better agent quality, safety, or cost decisions.
5. **Mechanism:** nonnegative additive measures exclude ratios, unique counts, quantiles, tail latency, critical paths, and overlapping time; the implications are not discussed.
6. **Framing:** “offline” makes zero agent-runtime overhead true by definition, but capture/storage overhead and freshness are relevant to the observability use case.

### Nits

1. Figure 3's legend is crowded and the “Both fields” zero bars visually disappear without numeric labels.
2. Figure 4's threshold is visually prominent but not scientifically motivated.
3. The flame graphs contain truncated labels at paper scale and do not show a concrete decision a reader can verify.
4. The title spells the system “AgentProf,” while several figure headings visibly say “agentpprof”; this looks like artifact-name drift.
5. The source retains extensive Chinese sentence comments and unused legacy bibliography/data assets; they do not affect PDF correctness but increase submission-maintenance risk.

## Fixed-RQ assessment

| Fixed RQ | Current answer in paper | Credible and complete? | Why |
|---|---|---:|---|
| **RQ1 resource attribution** | Prompt tags reduce mixed cost; field/weight choices expose multiple views; automatic stacks are a zero-config alternative. | **No; partial demonstration only.** | The separation metric is entangled with the grouping label, attribution correctness is not validated, the strongest equivalent aggregation baseline is missing, and the headline overstates the reduction. |
| **RQ2 real-problem localization** | Top five groups inspect 9.4% of work; 30% budget recovers 39%; 45% fewer groups than sessions. | **No.** | AP loses to per-session/native, top-five recall is 18.8%, policies appear tuned on evaluated tasks, and no external analyst/decision or fully held-out protocol establishes real localization benefit. |
| **RQ3 tag accuracy** | Mapping-derived phases exceed 0.7 V-measure/boundary F1 on 7/9 datasets. | **No.** | It evaluates structured-field mapping rather than the natural-language intent tagger and lacks a common ontology, rule-learning protocol, justified threshold, and variance. |
| **RQ4 profiling cost** | Warm/profile construction takes median 1.6 s; tag cache avoids repeated calls. | **No; warm-path partial evidence.** | Cold-cache “complete” profiling, actual 35,136-call wall time, hardware/resources, scaling, and acquisition cost are omitted. |

No fixed RQ currently has a fully credible submission-grade answer. RQ1 and RQ4 contain useful partial evidence; RQ2 and RQ3 remain decision-critical blockers.

## Alternative explanations and decisive discriminators

### Strongest alternative explanation

The gains come from manually curated or dataset-native fields plus task-specific ranking and depth selection. Any multidimensional query/trace tool given the same fields and tuning could produce the same or better groups; pprof-shaped output is a presentation choice, not the causal mechanism.

### Other plausible explanations

- positive concentration follows class prevalence and group size rather than semantic responsibility;
- reported cross-dataset agreement follows near-direct action-label mappings, not semantic generalization;
- the 325-trajectory results reflect one project's prompt conventions and cache, not general agent workloads;
- the best results were selected after viewing test annotations or task-level metrics;
- lower group count trades away recall rather than improving localization.

The decisive studies must freeze information access and tuning budgets, use unseen external traces/problems, report per-task distributions, and compare against equivalent multidimensional trace aggregation.

## Largest gaps and largest opportunity

- **Largest evidence gap:** no leakage-resistant, end-to-end RQ2 result shows that a frozen AgentProf profile causes a reviewer-meaningful improvement in locating hidden real agent problems against strong, information-equivalent baselines.
- **Largest writing-only gap:** the paper never precisely states the distinction between (a) cross-layer responsibility reconstruction, (b) semantic label derivation, (c) multidimensional hierarchy projection, and (d) problem ranking. Because those mechanisms and evidence are blended, the abstract and conclusion attribute every gain to “semantic profiling.” This can be repaired locally after the experiments without changing thesis or RQs.
- **Largest claim current evidence almost supports:** **A single conserved operation record can turn heterogeneous agent telemetry into multiple population-level resource views, while keeping single-run drilldown as a special case.** The current multi-dataset conversion, field sweeps, multiple weights, and pprof output nearly support this broader interoperability claim. What is missing is information-equivalent baseline parity and validated responsibility edges, not a smaller story.

## Candidate next decisive experiment before source verification

The highest-value target is RQ2 because it currently supplies the paper's user-facing consequence and strongest reject argument. The provisional experiment is: run a frozen AgentProf policy on a real external multi-framework agent fault benchmark with hidden injected fault labels, and test the single hypothesis that semantic profiles reduce inspected telemetry work at a fixed fault-localization recall relative to native traces, session drilldown, and an information-equivalent multidimensional-query baseline. The external-search node must identify a primary-source benchmark and accepted protocol before this candidate becomes the final routed experiment. This must not become another custom AgentProcessBench variant.

## Alternatives and decision

I considered a writing-first route because the manuscript has clear overclaims and a thin related-work section. I reject it as the primary route: wording fixes cannot validate attribution, natural-language tagging, or real-problem localization. I also considered selecting RQ3 next because it is the most obvious AI-layer gap. RQ2 has greater paper-level decision value because it tests whether the profiling abstraction changes the real observability outcome and can incorporate frozen semantic tagging as an upstream mechanism without changing RQ2's meaning.

The paper-only decision is therefore to continue to mandatory external source search, then reread. The likely final route is `EXPERIMENT_GATE`, subject to source verification.

## Tree and search-strategy updates

Suggested reviewer-attack nodes (no canonical files modified):

- `A-B1` **requires** a leakage-resistant external RQ2 benchmark and protocol.
- `A-B2` **requires** verification of public intent-tagging datasets and label semantics.
- `A-B3` **requires** a causal ground-truth trace or fault-injection source for cross-layer attribution.
- `A-B4` **motivates** systems search for pprof labels, Perfetto/SQL, OLAP grouping sets, trace analytics, and semantic observability products.
- `A-M2` **requires** accepted cold/warm profiling cost reporting conventions.
- Competing hypothesis `H-alt`: equivalent multidimensional aggregation plus curated fields explains all current wins.

The external search must run three separate branches: systems, AI/ML, and bridging observability/agent-diagnosis work. It must actively seek contradictory evidence and stronger baselines, not only citations that support the paper.

## Project-memory updates

No canonical memory, paper, skill, AGENTS file, code, data, or experiment artifact was modified. Suggested memory updates are limited to the attack nodes above and should be made, if accepted, by the owning root orchestrator after the outer audit.

## Completion, uncertainty, and next node

The declared blind full-paper read and attack map are complete. Uncertainty remains about novelty, the reality of the challenged belief, exact baseline capabilities, dataset protocols, and availability of a decisive external benchmark; those questions cannot be resolved from the paper alone.

**Next node:** `200-external-search-and-source-verification.md`. Completion requires separate systems, AI/ML, and bridging searches; opened primary sources for closest work, contradictory evidence, strong baselines, accepted protocols/metrics, official artifacts, real-world problem evidence, and a potentially larger claim; and an explicit account of which attacks strengthen, weaken, or remain unresolved.
