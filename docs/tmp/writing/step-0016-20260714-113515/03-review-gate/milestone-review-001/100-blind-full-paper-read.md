# Blind Full-Paper Read: *AgentProf: Semantic Profiling for AI Agents*

## Review-node metadata

- **Phase:** `BLIND FULL READ` only. No attack-map search, external search, source verification, paper reread after search, cycle audit, or final verdict was performed.
- **Started:** 2026-07-14 11:35:15 PDT.
- **Blind assessment completed:** 2026-07-14 11:38:54 PDT.
- **Parent node:** `step-0016 / 03-review-gate / milestone-review-001`.
- **Objective:** Form an unprimed, paper-only AAAI review and attack map under both systems and AI/ML standards.
- **Target venue:** AAAI 2027, inferred directly from `main.tex` (`aaai2027` submission style) and fixed by the reviewer instruction.
- **Contribution routing:** Genuinely cross-domain, but systems-primary. The claimed abstraction, artifact, resource projection, and profiling cost are systems contributions; intent attribution, learned boundary construction, agent-diagnosis construct validity, and task/problem outcomes are load-bearing AI contributions. Both bars therefore apply.
- **Review references loaded before the paper:** `research-taste.md`, `systems-review.md`, `ai-ml-review.md`, and `cross-domain-review.md` from the `iter-review-critique` skill.
- **Paper inputs read:** all 1,029 lines of `docs/paper/main.tex`; all 895 lines of `docs/paper/references.bib`; the included architecture source; all included flame-graph and RQ1 figure assets; the inline RQ2, RQ3, and RQ4 tables; and the complete nine-page built `docs/paper/main.pdf`, including its rendered figures, tables, references, and layout.
- **Appendix status:** the submitted `main.tex` and built PDF contain no appendix. `ReproducibilityChecklist.tex` is not included by `main.tex` and is not part of the built paper, so it was not treated as an appendix or as evidence.
- **Forbidden inputs:** I did not read `docs/tmp/` (other than creating this newly authorized output path), `docs/evaluation.md`, `docs/idea-story.md`, `docs/user-instruction.md`, any old review, any change summary, any canonical project document, or any next-experiment proposal. I did not run Git.
- **Unavoidable contamination:** none from prohibited sources. While establishing which assets constitute the paper, I encountered several unreferenced assets already under `docs/paper/figures/` that carry older `R...` labels. They are absent from `main.tex` and `main.pdf`; I excluded every claim and number in them from this assessment. The review below is based only on the submitted source, bibliography, included figures/tables, and built PDF.
- **Reviewer context:** skeptical senior reviewer applying an AAAI broad-AI-significance bar plus systems mechanism/evaluation standards. Confidence is high on internal argument and protocol mismatches, but novelty and factual validity remain deliberately unverified in this blind phase.

## Method and paper-only principle

I read the title, abstract, full argument, design, implementation, evaluation, limitations, related work, conclusion, bibliography, all claim-bearing rendered figures/tables, and the complete PDF before consulting any external source. I reconstructed the paper as one causal argument rather than scoring sections independently.

The strongest plain-language principle I can extract is:

> Agent behavior can be profiled across trajectories by treating every intent or system event as a weighted row, attaching stable semantic responsibility fields, and projecting selected fields into a hierarchy whose equal paths are additively folded.

This is coherent and separable from the artifact name. It predicts that changing semantic fields or weights over the same linked event set should expose different recurring concentrations without losing total additive weight. Whether it is non-obvious and distinct from labeled multidimensional aggregation is the central unresolved novelty question.

## Problem, stakes, and challenged belief

The paper addresses an important recurring problem: teams accumulate many agent trajectories and need aggregate answers about resource budget, repeated failures, and unsafe system effects. Per-run traces and judges are expensive to inspect one by one, while code-centric profilers attribute cost to code paths rather than semantic responsibility.

The challenged belief appears to be:

> Profiling requires an execution-provided call stack and code-level identifiers; agent observability therefore stops at trace trees, dashboards, or per-execution diagnosis.

The proposed replacement is that responsibility hierarchies can be constructed at query time from semantic fields, provided source lineage first connects downstream effects to the responsible intent and the fields are stable enough to fold. The paper cites current observability products that already provide cross-trace hierarchical categories, so the belief challenge is narrower than the slogan “profiling, not only debugging”: the claimed gap is specifically the combination of source-linked cross-layer effects, conserved additive measures, selectable hierarchies, and pprof-compatible export. External verification must establish that this combination is scientifically missing rather than merely absent from named product interfaces.

The stakes are plausible but not yet causally demonstrated. The paper measures group separation and problem concentration, not whether developers diagnose faster, choose better mitigations, reduce unsafe effects, improve task quality, or reduce production cost.

## Artifact and mechanism reconstruction

The artifact is **AgentProf**, an offline Rust CLI of approximately 9.8 KLOC. It reads Codex and Claude Code local JSONL histories plus a generic operation JSONL format. AgentSight recordings require a separate source-specific adapter; the current CLI does not ingest them directly. It emits pprof protobuf, folded stacks, SVG flame graphs, and JSON.

The mechanism decomposes into the following chain:

| Requirement | Claimed mechanism | Paper-only evidence | Blind-read concern |
|---|---|---|---|
| D1: cross-layer resource projection | Uniform operations hold string fields and additive measures; ingestion propagates intent fields to linked system effects. | A fixed AgentSight-derived 20-task suite reports 1,520/1,574 effects recovered, no false positives, and rejection of 1,629 concurrent controls; AgentProf preserves all 1,520 folded samples. | The source join is an existing AgentSight path plus an external adapter, not a mechanism described or implemented deeply enough here. Propagation semantics under asynchronous tools, concurrency, missing events, fan-out, retries, and shared subprocesses are not specified. |
| D2: stable tags | Regex rules, a local grammar-constrained 3B LLM tagger, TF-IDF/K-Means discovery, and mappings derive ordinary fields. | RQ1 conditions on local-LLM prompt tags; RQ3 reports task-partition V-measure on two small public families. | The production-default rules are manually iterated 5–10 rounds and the local tags used for the headline system-effect separation are never independently validated. Stability across model versions, prompts, users, and time is untested. |
| D3: hierarchical attribution | A query-time ordered field list becomes a frame sequence; identical sequences are folded. An automatic mode places boundaries from adjacent-operation features. | Multi-depth group counts, six-task induction summaries, and a separate supervised boundary predictor on OSWorld-Human. | The evaluated supervised predictor is explicitly not the built-in Rust inducer. A field projection may be a multidimensional `GROUP BY` rendered as a stack rather than a new hierarchy mechanism. Hierarchical parent/child semantics and correctness invariants are not formalized. |
| Additivity | Token count, event count, and duration become profile weights and are summed. | Exact preservation is shown for sample/event weights. | Event count and tokens are additive, but overlapping wall-clock durations generally are not. The paper does not state exclusivity rules, concurrency semantics, or whether duration is inclusive, exclusive, or double counted. |
| Actionability | Different fields and weights yield alternate profiles; problem-rich groups are ranked early. | Three RQ2 benchmarks and descriptive flame graphs. | The evaluation establishes concentration under specific signals, not correct analyst decisions or remediation. It does not isolate the profile representation from the external risk/localization signal. |

The architecture figure is clear but too shallow for a systems mechanism claim. It omits ownership of the adapter, provenance metadata, schema validation, tag propagation, boundary state, cache semantics, failure handling, and trust/privacy boundaries.

## Claimed contributions and present support

1. **Semantic operation stack model — joint systems/AI abstraction.** The model is simple and coherent: uniform weighted operations plus selectable field stacks. Its distinctness from labeled profiling, trace SQL, and general grouped analytics is not established paper-only. Calling arbitrary field projections “stacks” risks terminology inflation unless parent/child attribution yields behavior or guarantees unavailable from existing cube/group-by views.
2. **AgentProf system — systems artifact with AI plug-ins.** The exporter and pluggable derivation paths are concrete, but implementation detail is insufficient to evaluate correctness, deployment, or end-to-end reproducibility. The strongest source-lineage mechanism belongs to an existing capture path and adapter that the CLI does not directly ingest.
3. **Evaluation — cross-domain empirical contribution.** The breadth is substantial, but it combines heterogeneous evidence whose causal roles differ: lineage correctness, tag-conditional separation, benchmark-risk aggregation, a separate supervised boundary model, small clustering studies, and offline construction cost. Breadth does not compensate for the missing strongest baselines and the disconnect between claimed production mechanisms and evaluated substitutes.

## Paper-level RQ map and current answers

The paper states four fixed RQs, satisfying the requested two-to-five range. They are distinct at the headline level, but RQ1 and RQ3 each bundle several mechanisms and their answers do not fully match their wording.

| RQ | Claim/goal mapping | Evidence presented | Strongest answer supported now | Completeness under AAAI + systems standards |
|---|---|---|---|---|
| **RQ1: Does semantic profiling improve resource attribution?** | Supports D1–D3, the operation-stack model, and the claim that semantic fields provide responsibility views beyond tag-free aggregation. | Existing source-lineage suite; exact folding conservation; semantic-axis ablation on 325 local trajectories/183,714 observations; depth sweep; multi-weight ranking comparison; six-task automatic induction. | **Partially positive, conditional on declared tags and the selected grouping construct.** Source lineage is precise in one fixed scope and folding is lossless. Adding prompt tags necessarily separates observations by prompt-tag category and changes stack cardinality. Automatic induction is coarser and has lower median AP than hand-specified stacks. | **Incomplete.** Mixed-weight separation is close to construct-by-definition, the prompt tags lack an independent oracle, and there is no strong comparison against pprof labels, SQL/group-by trace analytics, or current hierarchical observability products. Lineage and current AgentProf are not evaluated as one native end-to-end path. |
| **RQ2: Does profiler output correspond to real problems?** | Supports the actionability and diagnosis motivation: target-blind groups should concentrate independently annotated failures/risky steps and reduce inspection work. | AgentProcessBench AP 0.588 vs raw action 0.556, but session 0.599 and step 0.777; HINT Work@80 0.416 vs raw 0.463 with a confidence interval crossing zero; TraceElephant Work@80 1.00 vs raw 0.719 and width 0.677, with a descriptive Work@50 advantage. Released judge/localization predictions are used as step signals. | **Mixed, benchmark- and operating-point-dependent.** Semantic grouping modestly improves one AP control and shows useful early concentration in some settings, but it is not uniformly superior, misses the prospective TraceElephant 80%-recall point, and does not significantly beat raw action on HINT. | **Not fully answered as written.** “Corresponds to real problems” is broader than ranking groups that aggregate released risk/localization signals. The signal itself may do most of the work; no analyst outcome, corrective action, or prospective deployment is tested. The paper’s positive summary is too categorical. |
| **RQ3: How accurate are the tags?** | Supports D2 and D3: task/phase/action fields and group boundaries should recover independent annotations on unseen agents/tasks. | Session-held-out Bernoulli NB boundary prediction on 287 OSWorld-Human instances; task partition V-measure on 9 Mind2Web sessions and 100 ScienceWorld sessions; only constant-tag and simple boundary controls. | **Positive for one separately trained boundary predictor and two task-partition probes.** The reported boundary and B-cubed gains over simple heuristics are meaningful within the given split. | **Unanswered for the full RQ and headline mechanisms.** The predictor is not the built-in Rust inducer; session-held-out is not clearly task/domain-held-out; the local 3B tags driving RQ1 are not scored; phase, action, and literal tag names are explicitly outside the evidence. The fixed hypothesis promises unseen agent/task-family generalization that is not demonstrated. |
| **RQ4: What is the profiling cost?** | Supports practicality of post-session construction and caching. | Three-run medians on four public workloads and their 27,765-operation union; 1.17 s, 464.5 MiB peak RSS, +18.2% time and +1.3% memory over raw action; an explicitly predecessor-only cache anecdote. | **Answered narrowly for construction on the tested small range.** The current binary’s parse/construct/fold/serialize path is fast enough for these inputs. | **Incomplete for end-to-end operational cost.** Field derivation, source joining/adapter work, cold-cache local-model cost, ingestion, and capture are absent or unclear; three medians provide little uncertainty; the largest workload is smaller than the paper’s own 183,714-observation local set; 464.5 MiB for 27,765 operations needs explanation and scaling evidence. |

### Cross-domain causal-chain audit

The intended chain is:

```text
natural-language, multi-step agent workload
→ code stacks fail to represent semantic responsibility
→ source-linked operations + derived semantic fields + selectable stack projection
→ conserved resource attribution and problem-rich recurring groups
→ faster or better quality/safety/cost decisions
```

The paper supports parts of the third and fourth nodes. It does not yet establish that existing semantic trace analytics fail at the second node, that the evaluated tag/boundary mechanisms reliably produce the fields used by the artifact, or that concentrated groups cause the developer outcomes in the last node. Under the cross-domain standard, these missing edges are load-bearing; strong systems folding cannot substitute for AI label validity, and benchmark concentration cannot substitute for end-to-end systems utility.

## Initial strengths

- The problem is timely, practical, and easy to motivate without relying on a leaderboard.
- The model has a memorable, compact center rather than a large taxonomy: rows with additive weights, semantic fields, and selectable projections.
- The paper is unusually candid about several non-claims: manifest categories are inputs, local prompt tags are declared rather than oracles, the OSWorld predictor is not the Rust inducer, phase/action labels remain untested, HINT’s raw interval crosses zero, TraceElephant fails at 80% recall, and predecessor timing is not current-binary timing.
- The 20-task negative-control design is a useful first correctness test for cross-process source attribution.
- RQ2 holds target labels away from tag/stack/ranking construction and includes counterpoints instead of claiming universal dominance.
- The PDF is readable and the high-level pipeline and numerical results are easy to locate.

## AAAI and cross-domain initial score

This is an **initial paper-only score, not a final source-grounded verdict**.

| Dimension | Score | Blind rationale |
|---|---:|---|
| Problem importance | 4/5 | Aggregate diagnosis and resource responsibility across agent trajectories are important. |
| Principle/taste | 3/5 | Coherent and memorable, but may collapse to known labeled multidimensional aggregation. |
| Novelty articulation | 2/5 | The narrow combination is stated; distinction from strongest systems and product baselines is not demonstrated. |
| Systems mechanism/soundness | 2/5 | Architecture and invariants are underspecified; source linkage is external to the current CLI path; end-to-end semantics are unclear. |
| AI/ML technical soundness | 2/5 | Evaluated tag/boundary substitutes do not match the production mechanisms or claimed generalization; controls are weak. |
| Evaluation construct validity | 2/5 | Several metrics are conditional or proxy-driven; strongest operating points and baselines are mixed; no user/deployment outcome. |
| Cross-domain causal closure | 2/5 | The workload→mechanism→resource/group→developer outcome chain has multiple unsupported edges. |
| Clarity and organization | 4/5 | Clear RQs and scoped prose, with some overpacked RQs and categorical summaries that outrun caveats. |
| Reproducibility from paper | 2/5 | Versions and some protocols appear, but datasets, prompts/rules/features, seeds, commands, provenance, and adapter details are insufficient in the paper. |
| AAAI fit and broad AI significance | 2/5 | Relevant to AI agents, but current contribution reads primarily as a systems representation/exporter with limited AI-method or AI-outcome evidence. |

**Overall initial recommendation: 4/10, Weak Reject (confidence 4/5).** The work is best characterized as **incomplete-but-promising**, not simple-but-deep yet. The core may become deep if external novelty survives and an end-to-end causal evaluation shows that semantic profiles enable materially better agent diagnosis or control. In the current paper, systems breadth masks incomplete AI validation, and AI benchmarks mask an underspecified systems mechanism.

## Strongest reject hypotheses / attack map

### H1 — Blocker candidate: the central abstraction is a renamed labeled `GROUP BY`, not a new profiling principle

- **Category:** novelty / scientific framing.
- **Locations:** Introduction paragraphs 3–6; Background “System Profiling”; Design “Semantic Operation Stack Model”; Related Work.
- **Failed reviewer inference:** ordered field projection plus summation may be ordinary multidimensional aggregation rendered in a flame graph. Pprof already has labels and `tagroot`/`tagleaf`; Perfetto has SQL-derived events; the paper itself says current products derive hierarchical cross-trace categories and aggregate metrics.
- **Why load-bearing:** if the abstraction does not create a new invariant, capability, prediction, or consequence, the artifact becomes an integration/export feature.
- **Paper-only evidence for rejection:** no direct baseline implements the same fields/weights in pprof labels, trace SQL, an OLAP pivot, LangSmith Insights, Datadog Patterns, Phoenix, or OpenInference/OTel analytics. “Selectable pprof-compatible operation stacks” is asserted as a missing combination rather than experimentally distinguished.
- **What external verification must decide:** whether prior systems/observability tools already support equivalent arbitrary label promotion, hierarchical pivoting, conserved metrics, or cross-span source fields; and whether the claimed combination changes capability rather than UI/format.

### H2 — Blocker candidate: RQ2 measures aggregation of an external diagnostic signal, not problem discovery by semantic profiling

- **Category:** evidence/evaluation construct validity.
- **Locations:** RQ2 protocol, Table 1, and the positive RQ2 conclusion.
- **Failed reviewer inference:** released judge votes or localization predictions are already problem signals. Grouping and ranking those signals may concentrate their own predictions without showing that semantic structure discovers failures or reduces analyst effort.
- **Paper-only evidence for rejection:** the step signal is held fixed and is not produced by AgentProf; session/per-step controls beat semantic AP on AgentProcessBench; HINT’s raw comparison is non-significant; TraceElephant loses at the prospective 80%-recall point and only wins in a descriptive early region.
- **Cross-domain consequence:** the AI diagnosis value could come from the external judge/localizer, while the systems layer merely bins scores.
- **Required discriminator:** compare equally informed end-to-end systems, including direct signal ranking, current trace analytics, raw/session/step views under matched fragmentation, and blinded analyst or executable diagnosis outcomes.

### H3 — Major: RQ3 does not evaluate the tagger or boundary inducer that the paper claims and deploys

- **Category:** AI/ML technical mechanism and global consistency.
- **Locations:** Implementation “Field derivation and boundaries” and “Boundary construction”; RQ1 local-tag ablation; all of RQ3; Scope and Limitations.
- **Failed reviewer inference:** accuracy of a separate session-cross-validated Bernoulli NB predictor does not establish accuracy of the built-in adjacent-operation Rust inducer. V-measure on two small families with a constant baseline does not validate regex/local-LLM tags, phase/action tags, literal semantics, or unseen-family generalization.
- **Paper-only evidence for rejection:** the paper explicitly disclaims that RQ3 tests the Rust inducer and explicitly leaves phase/action/literal tag names outside evidence. The local 3B tags behind the 325-trajectory headline are treated as declared categories and never independently scored.
- **Required discriminator:** evaluate each shipped backend against independent labels under task-, project-, family-, and time-held-out splits, with strong embedding/segmentation baselines, multiple runs, calibration/stability, and propagated downstream effects.

### H4 — Major: the joint source-to-semantics mechanism is not evaluated end to end

- **Category:** systems mechanism / cross-domain causality.
- **Locations:** Abstract; Introduction result paragraph; Implementation “Input reconstruction”; RQ1 lineage suite.
- **Failed reviewer inference:** the strongest cross-layer claim joins an existing AgentSight 0.2.37 capture path, an adapter, and AgentProf folding. The current CLI does not read AgentSight recordings directly, and the paper provides little adapter or inheritance detail.
- **Paper-only evidence for rejection:** source-lineage fidelity and lossless folding are separate tests; exact weight conservation after folding is expected arithmetic, not proof that semantic responsibility is correct. The 54 missed effects are not analyzed.
- **Required discriminator:** native end-to-end ingestion on realistic concurrent agents with lineage ground truth, failure analysis, missing/duplicate events, async/fan-out tools, shared descendants, and semantic-tag correctness.

### H5 — Major: the paper stops before the AAAI-relevant outcome

- **Category:** scientific significance / evidence.
- **Locations:** Introduction motivation and RQ2 conclusion.
- **Failed reviewer inference:** lower mixed weight or inspection work does not establish improved quality, safety, cost efficiency, or developer decisions.
- **Paper-only evidence for rejection:** no prospective team deployment, analyst study, time-to-diagnosis, remediation accuracy, prevented side effect, budget reduction, or agent-policy improvement is measured.
- **Required discriminator:** a blinded diagnosis/remediation study or executable closed-loop experiment on real agents, with matched information and time budgets, comparing AgentProf to raw traces and current hierarchical analytics.

### H6 — Major: system semantics, correctness, and scalability are too underspecified

- **Category:** systems technical mechanism.
- **Locations:** Design and Implementation; RQ4.
- **Failed reviewer inference:** readers cannot reason about additive duration, missing fields, hierarchy parent semantics, attribution under concurrency, determinism, cache invalidation, failure recovery, privacy, or resource scaling.
- **Paper-only evidence for rejection:** 9.8 KLOC is summarized in a few paragraphs; the largest test is 27,765 operations with 464.5 MiB RSS despite a local dataset containing 183,714 observations; no tail latency, complexity, or large multi-project run is reported.
- **Required discriminator:** formalize operation/weight invariants and execute scale, skew, concurrency, corruption, and cold-cache experiments on the full native pipeline.

### H7 — Major: dataset breadth is not the same as scope-matched generalization

- **Category:** AI/ML evaluation integrity.
- **Locations:** Evaluation dataset overview; RQ1 and RQ3.
- **Failed reviewer inference:** mappings over 15 families show schema flexibility, not automatic semantic validity. The 325 local trajectories come from one multi-month project, and session-held-out folds may share tasks/templates/domains.
- **Paper-only evidence for rejection:** label/mapping authoring, selection feedback, model versions, prompts, stability, repeated trials, and cross-family held-out results are not reported.
- **Required discriminator:** project-, task-, agent-, domain-, and temporal-held-out tests with frozen mappings/taggers and fully specified selection budgets.

## Global claim, number, mechanism, and figure consistency issues

1. **Built-in inducer versus supervised predictor:** the design promotes automatic boundary induction, but the headline RQ3 result explicitly evaluates a different Python/supervised predictor. This is the largest mechanism–evidence mismatch.
2. **RQ3 wording versus evidence:** “How accurate are the tags?” and the fixed hypothesis cover task, phase, action, and boundaries on unseen families. The paper only measures two task partitions and one boundary construct, then calls the answer positive.
3. **RQ2 categorical answer versus mixed results:** “complete workloads answer RQ2 positively” suppresses that HINT versus raw crosses zero and TraceElephant requires full work at the prospective 80%-recall point.
4. **RQ1 separation is conditional on the same categories:** mixed-weight percentage is defined by whether groups mix prompt-tag categories, then prompt tags are added as a grouping axis. The dramatic reduction is partly structural and does not establish tag correctness or usefulness.
5. **Existing capture versus current artifact:** the abstract and introduction place lineage and AgentProf in one contribution chain, but implementation states that AgentSight recordings need an adapter and are not directly read by the CLI.
6. **Additive duration ambiguity:** Figure 1 and the model treat wall-clock duration as additive profile width without explaining overlap. This can double count parallel operations and violate the conserved-resource analogy.
7. **Data-accounting opacity:** the paper uses 47,590 mapped operations, 27,346 labeled steps, 13,265 annotated operations, a 34,539-instance secondary analysis, 27,765 cost operations, and 183,714 local observations. Their overlaps and provenance are not summarized in one table.
8. **Flame-graph readability and units:** Figure 1 is visually dense with many truncated labels. The token profile displays a total around 21.9 billion while the prose gives no sanity check or unit/provenance explanation; the figure is illustrative rather than evidence a reviewer can audit.
9. **No submitted appendix:** protocols too detailed for the main-paper budget are not recovered elsewhere in the built PDF. The bibliography contains verification comments in source, but those are not paper evidence.
10. **Cost headline scope:** “processes 27,765 operations in 1.17 s” can be read as end-to-end processing, while the measured path excludes capture and appears not to include uncached model derivation or adapter work.

## Strongest alternative explanations

1. The observed gains come from adding any informative categorical feature to a group-by, not from an operation-stack abstraction.
2. The released risk/localization signal, rather than semantic grouping, drives RQ2 concentration.
3. Finer granularity increases apparent separation and AP; stack count/fragmentation differences, not semantic correctness, explain improvements.
4. Manual mapping and 5–10 rounds of regex refinement encode dataset/project knowledge that would not transfer to unseen trajectories.
5. Boundary gains come from supervised access to nine structured fields and same-domain session folds, not a general property of semantic profiling.
6. The artifact’s low measured time reflects pre-derived operation inputs and excludes the expensive or failure-prone stages needed in deployment.

## Terms/concepts that may be merged or deleted without loss

- **“Operation”** is currently a weighted row/event with sparse string dimensions. The paper must state what additional invariant justifies a new term.
- **“Operation stack”** is an ordered field projection. If hierarchy semantics do not exceed a grouped pivot, it could be called a “hierarchical semantic projection” without borrowing call-stack implications.
- **“Intent attribution,” “field derivation,” and “mapping rules”** overlap. A single field-derivation abstraction with explicit backend types would reduce conceptual stacking.
- **“Stack construction” and “boundary construction”** are presented as one mechanism but evaluated as different mechanisms. They should be separated precisely or one name removed.
- **“Profiling” versus “debugging”** is a useful contrast, but repeated slogans should not substitute for the narrower scientific distinction from current cross-trace hierarchical analytics.

## Load-bearing external-verification checklist

No item below has been searched or verified in this phase.

### Claims and source families

- Verify pprof’s exact label, `tagroot`, `tagleaf`, multi-sample-type, and conserved-value capabilities against the official repository/documentation.
- Verify Perfetto/Trace Processor support for arbitrary derived events, recursive/hierarchical grouping, pivots, and additive metrics.
- Verify OpenTelemetry GenAI and OpenInference data models, including links, baggage/resource attributes, span events, and cross-span propagation.
- Verify whether LangSmith Insights and Datadog Patterns already provide reusable hierarchical categories, multiple metric projections, failure/evaluation aggregation, and drilldown; test the paper’s claimed missing combination rather than marketing wording.
- Verify Phoenix, Langfuse, Laminar, AgentOps, and AgentTelemetry capabilities relevant to aggregation, semantic grouping, source lineage, and export.
- Verify the actual novelty and relationship of AgentSight’s source correlation to AgentProf, including artifact availability and whether the adapter is part of the claimed system.
- Verify every dataset count, split, annotation unit, license, and snapshot, especially HINTBench’s reported 629 versus enumerated 536 test trajectories.
- Verify what AgentProcessBench’s 20 judge votes represent and whether using their error fraction as a risk signal is target-blind in the scientifically relevant sense.
- Verify what HINTBench and TraceElephant “released localization predictions” encode, how they were trained/selected, and whether using them leaks benchmark target structure.
- Verify B-cubed’s suitability and exact operation weighting for contiguous segmentation rather than entity/coreference clustering.
- Verify all 2026 papers and product claims in primary proceedings, PDFs, official repositories, or official documentation; bibliography comments are not verification evidence.

### Stronger expected baselines

- A plain relational/columnar `GROUP BY` or OLAP pivot using identical fields, weights, and ranking signals.
- Pprof labels plus `tagroot`/`tagleaf` using identical input operations.
- Perfetto SQL/derived-event analysis over the same traces.
- Current LangSmith Insights and Datadog Patterns on importable matched trajectories, or a faithful feature-matched reproduction if export is impossible.
- OTel/OpenInference span-tree and linked-trace analytics with supplied semantic attributes.
- Direct per-step ranking by the released risk/localization signal, plus calibrated session, native hierarchy, and equal-cardinality partitions.
- Random partitions and size-matched/shuffled semantic partitions to isolate semantics from granularity.
- Strong text clustering/tagging baselines such as frozen sentence embeddings with hierarchical/agglomerative or density clustering, under matched tuning budgets.
- Strong change-point/sequence segmentation baselines and the actual built-in Rust inducer, not only always/action/phase boundaries.
- Existing agent failure localization systems (AgentRx, TELBench/DRIFT, TrajAD, AgentFixer where applicable) under information and compute parity.
- A manual expert-tag oracle and a no-tag trace baseline to bound the contribution of tag accuracy separately from visualization/export.

### Protocol and reproducibility checks

- Freeze mapping rules, local-LLM prompts/grammar/model/version, clustering hyperparameters, field orders, and ranking rules before held-out evaluation.
- Use task-, project-, agent-, family-, and temporal-held-out splits; show that no near-duplicate instruction/template crosses folds.
- Report all seeds/runs, variability, confidence intervals, multiple-comparison corrections, and selection budgets for stochastic tagging/clustering and 24-way field-order choice.
- Specify annotation provenance, inter-annotator agreement, label access, test-feedback boundaries, and whether released predictions were themselves tuned on test data.
- Audit selection leakage from the 5–10 regex refinement rounds and from designing mappings after inspecting dataset labels.
- Report model/API versions, prompts, tokenization, caching state, hardware, commands, input hashes/snapshots, and failed/excluded records.
- Measure end-to-end cold and warm paths: capture/source join, adapter, parsing, field derivation, boundary induction, folding, serialization, and visualization.
- Test realistic scale, skew, long trajectories, many projects/categories, concurrent and asynchronous tools, nested/fan-out process trees, missing/duplicate/out-of-order events, and corrupted inputs.
- Define inclusive/exclusive duration and prevent or quantify double counting under concurrency.
- Provide source-lineage ground truth construction and analyze all 54 false negatives, not only aggregate precision/recall.
- Address privacy, consent, security, retention, and anonymization for local prompt/tool/system histories.
- For the claimed developer value, run a prospective blinded task with time-to-correct-diagnosis, remediation correctness, unsafe-effect prevention, or budget savings—not only proxy inspection work.

## Largest claim the current evidence almost supports

The most ambitious defensible direction is not merely “pprof for agents.” It is:

> A source-linked semantic aggregation layer can make heterogeneous agent trajectories jointly accountable across intent, tools, and system effects while preserving resource totals and enabling recurring failure/resource patterns to be inspected under multiple views.

Current evidence almost supports the representation and conservation part, but not yet reliable automatic semantics or improved human/agent outcomes. The decisive falsifier would be a prospective, end-to-end comparison against feature-matched trace/group-by/hierarchical-product baselines on unseen real agent workloads, measuring both attribution correctness and time-to-correct diagnosis/remediation. This is recorded only as a blind-review discriminator, not as an executed next experiment.

## Alternatives, decision, and paper/claim impact

- **Current decision:** paper-only weak reject; retain for external novelty and protocol attack rather than dismissing it as obviously unsound.
- **If H1 survives external attack:** the work needs a precise capability/invariant that grouped trace analytics cannot express, or the contribution should be reframed as an empirical systems study with a strong deployment outcome. More terminology will not repair it.
- **If H2/H3 survive:** the paper needs evidence for the shipped semantic mechanisms and an outcome construct that does not inherit most value from external diagnostic predictions.
- **If novelty is stronger than it presently appears:** the paper’s clean principle, negative-control lineage test, and candid limitations could support an ambitious cross-layer observability contribution, provided the causal chain closes.
- **Paper impact:** abstract, introduction, RQ2/RQ3 conclusions, related work, and implementation/evaluation linkage are the most load-bearing areas. This blind phase makes no edit or routing decision.

## Tree/search updates, project-memory updates, and completion

- **Attack tree created:** H1 novelty equivalence; H2 proxy-driven problem concentration; H3 evaluated/mechanism mismatch; H4 non-native end-to-end source chain; H5 missing AI outcome; H6 missing systems invariants/scale; H7 scope/generalization leakage.
- **Search state:** intentionally untouched. No web search, repository search outside `docs/paper/`, primary-source opening, citation verification, or closest-work comparison was performed.
- **Project-memory updates:** none. No canonical document was read or modified.
- **Paper/code/test changes:** none.
- **Artifacts created:** this blind-read report only.
- **Completion assessment:** complete for the requested BLIND FULL READ phase. The paper-only principle, belief challenge, artifact/mechanism, contributions, four-RQ mapping and answers, AAAI/cross-domain scores, reject hypotheses, consistency defects, and pending external-verification inventory are all recorded.
- **Residual uncertainty:** novelty against trace/profiling products; validity of 2026 benchmark sources and released signals; exact data/mapping provenance; whether the artifact materials outside the paper close reproducibility gaps. These are intentionally unresolved.
- **Next node:** external attack/source-verification phase, only if separately authorized. It should begin with H1 and H2 because either can independently determine rejection. This report does not perform or pre-commit that phase.
