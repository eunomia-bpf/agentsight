# 02 — External Search and Primary-Source Verification

- **Reviewer:** Independent Claude Opus milestone reviewer (AgentProf, AAAI-27 main track)
- **Report written:** 2026-07-19, step `step-0048-20260719T185709-0700`, `milestone-review-001`
- **Stage:** Step 2 of 4. Written after `01-blind-full-read.md` and before rereading the paper. Still no prior review, `docs/tmp/` artifact, `docs/idea-story.md`, `docs/user-instruction.md`, `docs/evaluation.md`, or `docs/background-related-work.md` has been read.
- **Method:** 12 targeted web searches against the live web (current as of 2026-07-19), verifying (a) every dataset/benchmark the evaluation depends on, (b) the model identity used in RQ3, (c) every named prior system in Related Work against its primary source, (d) the three prior-art fields I asserted from memory in Report 01, and (e) contradictory evidence bearing on the four RQs. One `WebFetch` to `docs.langchain.com` was denied by the permission layer; I substituted a web search that returned the same documentation content and have marked that item's provenance accordingly.
- **Scope note:** My training cutoff is January 2026 and much of this literature is 2026-dated. Everything below that post-dates the cutoff comes from the searches recorded here, not from memory. Where I could only reach an abstract/landing page rather than a full PDF, I say so and mark confidence accordingly.

---

## Part A — Verification of the paper's own evidence base

### A1. CodeTraceBench (RQ1's main population) — **REAL, but the paper's coverage language is misleading**

Primary source confirms: CodeTracer/CodeTraceBench is real (arXiv 2604.11641, posted 2026-04-15), with a GitHub repo and a HuggingFace dataset. Verified composition: **4,316 agent trajectories** with human-verified step-level annotations, covering **4 agents (mini-SWE-agent, OpenHands, Terminus2, SWE-agent) × 5 models (Claude Sonnet 4, DeepSeek-V3.2, Kimi-K2, GPT-5, Qwen3-Coder) across 26 task categories.**

The paper's four agent names match exactly. But:

- The paper writes "**all** 405 failed CodeTraceBench trajectories whose released sources yield the official operation sequence" and the Scope paragraph repeats "**all** 405." Against a 4,316-trajectory benchmark, 405 is **9.4%**. Even if only failed trajectories are eligible, agentic SWE resolve rates in this range imply on the order of 1,000–3,000 failures, so the reconstructability filter plausibly discards the large majority of eligible trajectories.
- The paper never states the denominator, never characterizes *why* some trajectories fail to reconstruct, and never tests whether reconstructability correlates with trajectory length, agent, model, or task category. **Reconstructability is very plausibly non-random** (e.g., longer or more complex trajectories may be likelier to break a parser), which would bias exactly the segmentation metric being reported.
- The paper also never mentions the **5-model** dimension. Table 1's claim that the gain "is positive in all four agent frameworks" stratifies on agent but not on model, even though model is a first-class dimension of the benchmark and the more likely source of behavioral heterogeneity.

**Upgrade from Report 01 M5 → this is now a Major finding with a concrete number attached.** The word "all" in "all 405" is doing rhetorical work that the underlying 405/4,316 does not support.

Sources: [arXiv:2604.11641](https://arxiv.org/abs/2604.11641), [NJU-LINK/CodeTracer](https://github.com/NJU-LINK/CodeTracer), [NJU-LINK/CodeTraceBench dataset](https://huggingface.co/datasets/NJU-LINK/CodeTraceBench)

### A2. HINTBench (RQ2) — **REAL, disclosure accurate, but its own baselines are ignored**

Verified: arXiv 2604.13954, **629 trajectories (523 risky, 106 safe), average length 33 steps**, three tasks: risk detection, **risk-step localization**, and intrinsic failure-type identification. The paper's "Of HINTBench's reported 629 trajectories, the released test snapshot used here contains 536" is consistent and is a good disclosure. RQ2's 400 target-bearing queries is consistent with a 536-trajectory snapshot containing ~523-proportion risky items.

**But:** HINTBench ships a **risk-step localization task with published baselines**, and the primary source reports that strong LLMs fall "below 35 Strict-F1 on risk-step localization." AgentProf runs on this benchmark and compares only against its own raw-action control. It does not report any HINTBench-published baseline. When you evaluate on a benchmark that ships baselines, not reporting them is a reviewer red flag regardless of metric mismatch — at minimum the paper owes a sentence explaining why Strict-F1 baselines cannot be placed on the same axis as its MAP.

Sources: [arXiv:2604.13954](https://arxiv.org/abs/2604.13954), [HTML](https://arxiv.org/html/2604.13954v1)

### A3. TraceElephant (RQ2) — **REAL, ACL 2026, and its central finding sharpens a question for AgentProf**

Verified: arXiv 2604.22708, ACL 2026, [GitHub](https://github.com/TraceElephant/TraceElephant). Task = "identifying the responsible agent and decisive step of a failure." Its headline result: **full traces improve attribution accuracy by up to 76% over a partial-observation counterpart.**

This is directly relevant and cuts both ways:
- **For AgentProf:** it independently supports the paper's premise that more complete observability (AgentProf's cross-layer effects) helps attribution. The paper does not exploit this argument and should.
- **Against AgentProf:** TraceElephant's own framing is that *observability completeness*, not *aggregation*, drives the gain. AgentProf's TraceElephant result (semantic .230 vs raw .121) is measured over the same complete traces for both arms, so it isolates grouping — good — but the absolute MAP of .230 is low, and the benchmark's own methods are not reported alongside.

Source: [arXiv:2604.22708](https://arxiv.org/abs/2604.22708)

### A4. AgentProcessBench (RQ2) — **REAL, KDD '26, and the verification exposes the single most important unresolved question in the paper**

Verified: arXiv 2603.14465, KDD '26 (Jeju, August 2026). Composition: **1,000 trajectories, 8,509 human-labeled step annotations, 89.1% inter-annotator agreement.** Labeling is **ternary: +1 correct/advancing, 0 neutral/exploratory, −1 incorrect/harmful**, with an error-propagation rule.

This lets me sharpen Report 01's B3.3 from "under-specified" to a **specific fork with different verdicts**:

The paper says AgentProf "averages **judge votes** within each group" and that queries contain "an annotated target."
- **Reading 1 (sound):** "judge votes" = outputs of the LLM judges that AgentProcessBench evaluates; "targets" = the 8,509 human labels. Then RQ2 measures *"does semantic grouping improve an LLM judge's step ranking against human labels?"* — a valid, interesting claim. **But then AgentProf's pipeline requires an LLM judge pass over every step**, which is strictly more expensive than the "separate evaluator pass per trajectory" the Introduction cites as the cost problem AgentProf exists to avoid. The paper's motivating economic argument would be self-refuting.
- **Reading 2 (unsound):** "judge votes" are derived from the ternary human labels. Then averaging them within groups to rank against those same labels is **circular** and RQ2's primary comparison is invalid.

The paper's text does not let a reviewer distinguish these. **This is a blocking clarity defect**, because one reading undermines the Introduction and the other undermines the experiment. It must be resolved in the paper, not in a rebuttal.

Sources: [arXiv:2603.14465](https://arxiv.org/abs/2603.14465), [HTML](https://arxiv.org/html/2603.14465v1)

### A5. OSWorld-Human (RQ3's boundary population) — **REAL, but a construct-validity question emerges**

Verified: arXiv 2506.16042, ICML 2025 Workshop on Computer-Use Agents, [WukLab/osworld-human](https://github.com/WukLab/osworld-human). It is "a manually annotated version of the original OSWorld dataset that contains a human-determined trajectory for each task." Its **purpose is efficiency/latency**: agents take 1.4–2.7× more steps than necessary; planning and reflection account for 75–94% of latency. Its step categorization is: relevant information retrieval, step planning, step grounding, action-taking, screenshotting, reflection.

The concern: OSWorld-Human's annotations are **human reference trajectories for measuring agent step-efficiency**, not annotations of *semantic responsibility units*. AgentProf uses them as ground truth for "2,042 human independently annotated action groups" against which it scores boundary F1 and B³. Whether the released grouping is a genuine responsibility partition — the construct RQ3 needs — or an efficiency-oriented step decomposition is not established by the paper and is not obvious from the primary source's abstract.

I could not verify the exact form of the released group annotations without pulling the repository data, which is outside my read-only scope for this review. **Flagging as an open construct-validity question with medium confidence**, and it is directly checkable by the authors: the paper should state, in one sentence, what OSWorld-Human's group annotation *is* and why it is the right target for semantic responsibility grouping. Note this population is *also* the one the paper admits the recurrence rule was designed on, so it is carrying a lot of weight for a construct that is not pinned down.

Sources: [arXiv:2506.16042](https://arxiv.org/abs/2506.16042), [HTML](https://arxiv.org/html/2506.16042v1), [GitHub](https://github.com/WukLab/osworld-human)

### A6. Qwen3.6-27B (RQ3's tagger) — **REAL, and it quantifies the RQ4 cost omission**

Verified: released **2026-04-22** by the Qwen team, Apache 2.0, dense 27B, multimodal, 262,144-token native context, **Q4_K_M quantization ≈ 16.8 GB, runs on a single consumer GPU**. SWE-bench Verified 77.2. The citation is accurate and the model is genuinely locally runnable — this is a point in the paper's favor and partially mitigates my Report 01 concern that the tagger is impractical.

It does **not** mitigate the accounting problem. Order-of-magnitude estimate: even at an optimistic 5–20 items/s for grammar-constrained single-token-ish tagging with a 27B Q4 model on one consumer GPU, tagging 27,765 operations is **~25 minutes to ~1.5 hours**, versus the reported 1.17 s for folding — roughly **3–4 orders of magnitude**. (This is my estimate from the verified model size and quantization, not a measurement; treat the exponent, not the digits.) The conclusion is robust to wide error bars: the excluded term dominates the reported term by orders of magnitude, so "AgentProf constructs a 27,765-operation profile in 1.17 s" in the abstract is not a defensible summary of profiling cost.

It also confirms the **3B-vs-27B internal inconsistency** from Report 01 M1 is material, not cosmetic: 3B and 27B differ by ~9× in parameters and correspondingly in tagging throughput and hardware floor.

Sources: [Qwen/Qwen3.6-27B](https://huggingface.co/Qwen/Qwen3.6-27B), [vLLM recipe](https://recipes.vllm.ai/Qwen/Qwen3.6-27B), [OpenRouter](https://openrouter.ai/qwen/qwen3.6-27b)

### A7. AgentSight — **REAL, and it absorbs more of the contribution than the paper acknowledges**

Verified: arXiv 2508.02736, published in *Proceedings of the 4th Workshop on Practical Adoption Challenges of ML for Systems* (DOI 10.1145/3766882.3767169). Its stated core: "boundary tracing" via eBPF to intercept TLS LLM traffic for intent and kernel events for effects, with **"a novel, two-stage correlation process: a real-time engine links an LLM response to the system behavior it triggers, and a secondary 'observer' LLM performs a deep semantic analysis."**

So **D1 (cross-layer resource projection) is fully solved by the cited prior system**, and AgentSight *also* already performs LLM-based semantic analysis over the correlated trace. AgentProf's RQ1 experiment credits AgentSight explicitly for the join. AgentProf's own contribution in that experiment is a source-specific adapter plus lossless folding.

This matters for the novelty argument in a way the paper does not surface: the Related Work sentence "AgentProf's residual capability is their conjunction in one operation corpus: joining agent actions to process, file, and network effects while conserving arbitrary additive measures and supporting selectable query-time field stacks" lists three conjuncts, and **the first conjunct is prior work by the citation the paper itself gives.**

Sources: [arXiv:2508.02736](https://arxiv.org/abs/2508.02736), [ACM DL](https://dl.acm.org/doi/10.1145/3766882.3767169)

---

## Part B — Testing the novelty/conjunction claim against primary sources

The paper's novelty is stated as a conjunction of three properties that no prior system allegedly combines. I verified each named system.

### B1. LangSmith Insights — **has more of the claimed conjunction than the paper implies**

Verified from LangChain's own documentation and blog: Insights "uses clustering to automatically discover patterns in your traces… analyzes thousands of conversations and surfaces the clusters that matter — usage patterns, error modes, **or any dimension you specify**." Structure: "**top level clusters, then a second level of more detailed groupings, and then individual runs beneath that. There will be multiple different hierarchies of clusters.**" Metrics: "aggregate attributes associated with the traces in those groups… **error rates, latency, cost**," with drill-down through categories and subcategories.

So LangSmith Insights already provides: cross-run semantic grouping ✓, **multi-level hierarchy** ✓, **multiple simultaneous hierarchies** ✓, user-specified grouping dimension ✓, additive metric rollup over a fixed set (cost/latency/errors) ✓. What it lacks: kernel-level system effects ✗, arbitrary user-defined additive measures (partial), pprof compatibility ✗.

*Provenance caveat:* my direct `WebFetch` of `docs.langchain.com/langsmith/insights` was denied by the permission layer; the quoted content came back through web search results that surface that documentation page and LangChain's own blog. Confidence: high on substance, medium on exact wording.

Sources: [LangSmith Insights docs](https://docs.langchain.com/langsmith/insights), [LangChain blog: From Traces to Insights](https://www.langchain.com/blog/from-traces-to-insights-understanding-agent-behavior-at-scale)

### B2. Datadog LLM Observability Patterns — **likewise closer than implied**

Verified from Datadog docs and blog: "You can get the **topic hierarchy** for a run with span IDs inlined on each leaf topic, with options to include **per-span duration, cost, token counts, and evaluations**." And: "Each cluster surfaces cost, latency, error rate, and evaluation coverage benchmarked against other patterns, so the interactions driving quality and cost issues are immediately visible."

So Datadog Patterns provides: automatic topic hierarchy ✓, per-cluster token/cost/duration/evaluation rollup ✓, cross-cluster comparison ✓. Lacks: kernel-level effects ✗, query-time re-projection of the same corpus onto an arbitrary user-chosen field order ✗ (the hierarchy is derived, not user-ordered), pprof ✗.

Sources: [Datadog Patterns blog](https://www.datadoghq.com/blog/patterns-agent-observability/), [Agent Observability metrics docs](https://docs.datadoghq.com/llm_observability/monitoring/metrics/), [cost docs](https://docs.datadoghq.com/llm_observability/monitoring/cost/)

### B3. Commercial tooling already ships flame-graph views of agent traces

A general search of the 2026 LLM-observability tooling landscape returns, as a routine product-category description: "Modern LLM agent observability tools support multiple visualization formats including **waterfall, flame graph, topology, and sequence-diagram views** for multi-agent systems," and "**span-level token attribution shows which tool calls, retrieval steps, retries, or sub-agent runs are driving cost inside an agent trace.**"

**Consequence for the paper:** the Background sentence "Existing tools record agent events as per-execution span trees for single-run debugging" is an understatement that a practitioner-reviewer will contest. Flame graphs over agent spans with token weights are a shipped product feature. The paper's real differentiator is *cross-run folding of semantically-tagged operations* versus *per-trace visualization*, and it needs to say that explicitly rather than implying flame graphs for agents are new.

Sources: [Augment Code tool survey](https://www.augmentcode.com/tools/best-ai-agent-observability-tools), [Braintrust token-usage article](https://www.braintrust.dev/articles/how-to-track-llm-token-usage-2026), [MLflow LLM tracing](https://mlflow.org/llm-tracing)

### B4. TraceProbe — **already has canonical actions + deterministic effects + cross-run additive rollups**

Verified (arXiv 2607.06184): "TraceProbe first converts raw trajectories into **normalized steps, typed canonical actions, and deterministic effect labels**," with INSIGHT (single-run pattern detection), CONVERGE (reference comparison with divergence spans), and Milestones. The paper's own bib abstract adds that it "reports recurring anti-patterns, milestones, **tokens, duration, and failed work across runs**" over 2,500 trajectories.

So TraceProbe independently has: uniform normalized representation ✓, canonical action vocabulary ✓, **effects** ✓ (deterministic labels rather than kernel-observed), **additive measures aggregated across runs** ✓. AgentProf's residual against TraceProbe narrows to: kernel-observed rather than inferred effects, arbitrary rather than fixed measures, and query-time selectable field order. That is a real residual but a **thin** one, and TraceProbe is the single most important missing baseline in the paper.

Source: [arXiv:2607.06184](https://arxiv.org/pdf/2607.06184)

### B5. Graphectory — **sets a downstream-outcome bar AgentProf does not meet**

Verified (arXiv 2512.02393; *PACMPL* OOPSLA, April 2026, DOI 10.1145/3798271): nodes are agent actions; edges are temporal or entity-relatedness; introduces **Langutory**, "a human-readable abstract of Graphectory representing the language of trajectories"; supports **Phase Flow Analysis and Pattern Detection**; and — critically — "online monitoring and process-centric analysis can **improve resolution rates by 23.5%** across models for problematic instances."

Two consequences:
1. Graphectory already performs **phase-level cross-trajectory structural analysis** — extremely close to AgentProf's phase/action hierarchy — and is peer-reviewed at OOPSLA.
2. The closest archival neighbor **demonstrates a measured downstream consequence** (+23.5% resolve rate). AgentProf demonstrates none. My Report 01 hypothesis RH8 ("no decision consequence") is therefore not a reviewer preference; **the bar is set by the paper's own cited related work.**

Sources: [arXiv:2512.02393](https://arxiv.org/abs/2512.02393), [PACMPL/OOPSLA](https://dl.acm.org/doi/10.1145/3798271)

### B6. Hodoscope — **also demonstrates a decision consequence**

Verified (arXiv 2604.11072, [hodoscope.dev](https://hodoscope.dev/)): formulates *unsupervised monitoring*; "agent trajectories are decomposed into individual actions, summarized to abstract away task-specific details, embedded, and projected to 2D, with the density-difference overlay highlighting actions overrepresented in one group." Explicitly positions against "human-written rules or LLM-based judges that check for known failure modes" being unreliable. The paper's own bib records its 6–23× review-effort reduction.

This is a second cited neighbor with (a) label-free cross-run semantic abstraction of agent actions and (b) a measured human-effort outcome.

Source: [arXiv:2604.11072](https://arxiv.org/abs/2604.11072)

---

## Part C — The three prior-art fields the paper does not cite (Report 01 B5, now verified)

I asserted these from memory in Report 01 and flagged them for verification. **All three are confirmed and all three are closer than I initially claimed.**

### C1. OLAP data cube — **confirmed; the paper's model is a roll-up**

Gray, Chaudhuri, Bosworth, Layman, Reichart, Venkatrao, Pellow, Pirahesh, "Data Cube: A Relational Aggregation Operator Generalizing Group-By, Cross-Tab, and Sub-Totals," *Data Mining and Knowledge Discovery* 1(1):29–53, 1997. Verified description: "The cube operator generalizes the histogram, cross-tabulation, **roll-up, drill-down**, and sub-total constructs… applications need the N-dimensional generalization of these operators… explains the cube and **roll-up** operators, shows how they fit in SQL, explains how users can **define new aggregate functions**."

Map onto AgentProf's §Semantic Operation Stack Model:

| AgentProf | Data cube / OLAP |
|---|---|
| `operation` (string fields + additive measures) | fact-table row (dimension attributes + measures) |
| ordered field list `[f₁…f_k]` | roll-up dimension order |
| `σ(o) = ⟨o.f₁…o.f_k⟩` | roll-up path / group-by key |
| fold identical stacks, sum weights | `GROUP BY … SUM(measure)` |
| predicate `φ` | `WHERE` |
| weight `w` | measure + user-defined aggregate function |
| "fields chosen at query time, not by execution" | ad-hoc OLAP query over a materialized cube |

The correspondence is essentially exact. A flame graph *is* a visualization of a roll-up hierarchy. The paper cites zero OLAP work. Any reviewer with a databases background will make this identification within one paragraph of reading `(φ, σ, w)`.

**This does not make the paper unoriginal** — deciding *what the dimensions should be for agent traces*, and *inducing them from natural language*, is the actual contribution, and cubes do not do that. But contribution 1 is currently framed as the model itself, and that framing is not survivable without positioning.

Sources: [Springer](https://link.springer.com/article/10.1023/A:1009726021843), [arXiv:cs/0701155](https://arxiv.org/abs/cs/0701155)

### C2. Query-time cross-layer trace aggregation — **confirmed; two SOSP papers own D1 and D3's query model**

**Canopy** (Kaldor et al., SOSP '17, DOI 10.1145/3132747.3132749). Verified: "records causally related performance data across the end-to-end execution path of requests, including from browsers, mobile applications, and backend services"; "processes traces in near real-time, **derives user-specified features**, and outputs to **performance datasets that aggregate across billions of requests**"; addresses "**supporting the range of execution and performance models used by different components** of the Facebook stack" and "enabling **deep customization by users**, from sampling traces to extracting and visualizing features."

Canopy's stated core problem — heterogeneous components with different execution models, unified into one representation, with user-specified feature extraction feeding aggregate queryable datasets — is a near-isomorphic statement of AgentProf's "uniform operations without type-specific objects → user-selected field projections → aggregate profiles." At 1 billion traces/day.

**Pivot Tracing** (Mace, Roelke, Fonseca, SOSP '15 / TOCS 35(4)). Verified: the "**happened-before join** operator… obtain an almost arbitrary metric at one point of the system, while **selecting, filtering, and grouping by causally preceding events from other parts of the system, even when crossing component or machine boundaries.**"

That is a precise formal statement of **D1**: attribute a low-layer resource metric (file I/O, process spawn) to the causally-preceding high-layer entity (prompt, LLM call), selecting/filtering/grouping at query time. AgentProf's `(φ, σ, w)` view over cross-layer joined operations is Pivot Tracing's query model instantiated on agent traces.

Neither is cited. For a paper claiming a systems contribution about cross-layer query-time aggregation, omitting both is the kind of gap that produces a confident reject from a systems-trained reviewer.

Sources: [Canopy (ACM DL)](https://dl.acm.org/doi/10.1145/3132747.3132749), [Canopy PDF](https://cs.brown.edu/people/jcmace/papers/kaldor2017canopy.pdf), [Pivot Tracing (TOCS)](https://dl.acm.org/doi/10.1145/3208104), [Pivot Tracing PDF](https://web.eecs.umich.edu/~mosharaf/Readings/Pivot-Tracing.pdf)

### C3. Process mining event abstraction — **confirmed; a mature field with a survey, a taxonomy, and matched baselines**

Verified that "event abstraction" — grouping low-level events into higher-level activities in an event log — is a named subfield with a literature review and taxonomy (*Granular Computing*, Springer, 2020) and multiple method families. Verified statement of the problem: "there is often a gap between the low-level nature of the events recorded in an event log and the high-level of abstraction at which the process is modeled… when events are recorded on a too low level of abstraction, process discovery methods tend to generate overgeneralizing process models." Verified statement of methods: "**existing event abstraction methods are mainly based on common sub-sequences and clustering techniques.**"

AgentProf's label-free recurrence — find recurring adjacent action transitions, cut at weak ones, use the run-length-compressed action subsequence as the higher-level frame value — is a **common-subsequence-based unsupervised event abstraction method**, which is the exact center of that literature. Directly matched prior work includes unsupervised event abstraction via pattern abstraction and local process models (arXiv 1704.03520), supervised event abstraction (arXiv 1606.07283), and session-based low-level-events-to-activities (arXiv 1903.03993).

Sources: [Event abstraction in process mining: literature review and taxonomy](https://link.springer.com/article/10.1007/s41066-020-00226-2), [Unsupervised Event Abstraction using Pattern Abstraction and Local Process Models](https://arxiv.org/pdf/1704.03520), [Event Abstraction for Process Mining using Supervised Learning](https://arxiv.org/pdf/1606.07283), [From Low-Level Events to Activities — A Session-Based Approach](https://arxiv.org/pdf/1903.03993)

### C4. Unsupervised segmentation "goodness measures" — **confirmed; the missing baseline family has a name**

Verified: Zellig Harris (1955/1967) established boundary detection from transition uncertainty; the derived family is standard and named. Verified enumeration: "popular goodness measures include **description length gain (DLG), accessor variety (AV), boundary entropy (BE), and normalized variation of branching entropy (nVBE)**," with a comparative literature integrating them (e.g., *Information Sciences*, "Integrating unsupervised and supervised word segmentation: the role of goodness measures").

AgentProf's NPMI-over-adjacent-transitions + threshold is a member of this family in everything but name. The paper cites Ruokolainen et al. 2016 — *A Comparative Study of Minimally Supervised Morphological Segmentation* — **for the boundary metric only**, while omitting that same literature's methods as baselines. That is now a specific, named, low-cost gap: AV, BE, nVBE, and DLG are all one-pass statistics over the same transition table AgentProf already builds, so running them is nearly free.

Sources: [Branching entropy & accessor variety overview](https://lovit.github.io/nlp/2018/04/09/branching_entropy_accessor_variety/), [Integrating unsupervised and supervised word segmentation: the role of goodness measures](https://www.sciencedirect.com/science/article/abs/pii/S0020025510004366), [An Efficient Algorithm for Unsupervised Word Segmentation with Branching Entropy and MDL](https://www.researchgate.net/publication/221013021_An_Efficient_Algorithm_for_Unsupervised_Word_Segmentation_with_Branching_Entropy_and_MDL)

---

## Part D — Contradictory evidence and recent work the paper should engage

### D1. MP-Bench directly challenges RQ2's evaluation protocol
Verified (arXiv 2603.25001, [GitHub](https://github.com/yeonjun-in/MP-Bench)): "existing benchmarks and methods largely **assume a single deterministic root cause** for each failure. In practice, MAS failures often admit **multiple plausible attributions**." And the finding: "**prior conclusions suggesting LLMs struggle with failure attribution are largely driven by limitations in existing benchmark designs.**"

RQ2 scores per-query AP against a single annotated target per trajectory on TraceElephant and HINTBench. MP-Bench's contribution is precisely that this protocol misestimates attribution quality. AgentProf cites `mpbench2026` **once, in a trailing list in Related Work**, and does not engage the critique. A reviewer aware of MP-Bench will ask why AgentProf's single-target MAP is trustworthy given a primary source arguing that single-target protocols distort exactly this measurement. This is the strongest external contradictory evidence bearing on any RQ.

### D2. CHIEF constructs hierarchical attribution from flat agent logs — the closest competitor to D3, uncited
Verified: "From Flat Logs to Causal Graphs: Hierarchical Failure Attribution for LLM-based Multi-Agent Systems" (arXiv 2602.23701, Feb 2026; also on OpenReview). CHIEF "transforms chaotic trajectories into a **structured hierarchical causal graph**," then does oracle-guided backtracking and counterfactual attribution. Its stated motivation: "existing failure attribution methods typically treat execution logs as **flat sequences**… this linear perspective fails to disentangle the intricate causal links… leading to weak observability and **ambiguous responsibility boundaries**."

That motivating sentence is nearly identical to AgentProf's D3 ("span trees do not encode semantic responsibility… the profiler must construct attribution hierarchies from the data"). CHIEF constructs a hierarchy from flat agent logs, with causal rather than co-occurrence semantics. Uncited. This is the most direct competitor to the paper's third design requirement.

Sources: [arXiv:2602.23701](https://arxiv.org/abs/2602.23701), [OpenReview](https://openreview.net/forum?id=KdBu1X4t5A)

### D3. OpenClawBench — an untouched, much larger population that would fix Report 01 B2
Verified (arXiv 2605.29253, May 2026): built from BFCL-driven OpenClaw sessions across 6 source models, **31,264 annotated trajectories**. Its "FullTax" supervision provides "binary labels, supporting evidence, **onset/span localization**, severity, recoverability, and a 5-class anomaly taxonomy," framed around the **Outcome-Process Gap** ("task success can hide process anomalies… unresolved ambiguity, unsafe external writes, ignored errors").

This is directly usable as the **untouched confirmation population** the label-free recurrence constructor currently lacks: it has span localization targets (for an RQ2-style protocol), a released taxonomy (for RQ3-style tag accuracy), and it is 77× larger than the CodeTraceBench subset. Its "unsafe external writes" category is also the closest public proxy for the paper's system-effects motivation. Uncited.

Source: [arXiv:2605.29253](https://arxiv.org/abs/2605.29253)

### D4. Other verified-real, directly adjacent, uncited work
Encountered during these searches, all with live arXiv records:
- **ProcBench** (2605.20251) — process-level defects and control preservation in coding agents. *Present in the paper's `.bib` as `procbench2026`, VERIFIED 2026-07-19, but never cited.*
- **AgentLens** (2605.12925) — context-sensitive intent stages over OpenHands trajectories. *Present in `.bib` as `agentlens2026`, never cited.* Most relevant to RQ3's stage/phase construct.
- **AgentLocate** (2607.07989) — responsible-agent and decisive-step localization. *Present in `.bib` as `agentlocate2026`, never cited.*
- **FALAT** (2606.00765) — dependency-guided failure tracing in agent trajectories.
- **MASPrism** (2605.07509) — lightweight failure attribution from prefill-stage signals.
- **TelBench/DRIFT** (2606.02060) — span-level error localization for deep-research agents. *Present in `.bib` as `telbench`, marked `STATUS: unused`.*
- **ClawTrace** (2604.23853) — cost-aware tracing for LLM agent skill distillation. Directly relevant to the cost framing.
- **AJ-Bench** (2604.18240), **ATBench** (2604.02022), **WildClawBench** (2605.10912) — adjacent trajectory-evaluation populations.

The pattern is notable: three of these are already in the authors' `.bib` with today's verification date and no `STATUS: unused` marker (unlike ~12 entries that carry that marker explicitly), which suggests they were prepared for citation and not wired in. Given the repository's stated citation policy of retaining even tangentially relevant references, this looks like an unfinished edit rather than a deliberate exclusion.

---

## Part E — What the search did **not** overturn

Being explicit about failed falsification attempts, since these strengthen the paper:

1. **No fabricated citations found.** Every one of the 11 primary sources I checked (CodeTraceBench, HINTBench, TraceElephant, AgentProcessBench, OSWorld-Human, Qwen3.6-27B, AgentSight, TraceProbe, Graphectory, Hodoscope, MP-Bench) exists with the claimed venue, identifier, and substance. Several `.bib` VERIFICATION_NOTE fields (e.g., "COLM 2025 lists this OpenReview record… metadata APIs that return only CoRR are incomplete"; "the official paper PDF states Published as a conference paper at ICLR 2025") reflect genuine, careful metadata resolution.
2. **No prior "semantic flame graph over cross-run agent trajectories with kernel-level effect linkage" system found.** I searched for it directly. The specific combination the paper claims does appear to be unoccupied. The novelty problem is **positioning against adjacent fields**, not the existence of a duplicate.
3. **The four RQs are not contradicted by external evidence.** Nothing I found suggests resource attribution, problem correspondence, tag accuracy, or profiling cost are the wrong questions. My objections remain about construct validity and generalization within RQ2/RQ3/RQ4, not about the RQ set. I do not recommend altering the RQs.
4. **The thesis is not externally refuted.** No source argues that population-level agent analysis is useless. On the contrary, Graphectory (+23.5% resolve rate), Hodoscope (6–23× review reduction), and OpenClawBench's Outcome-Process Gap all *support* the premise that cross-run process-level analysis matters. The thesis is well-supported by the field; the paper's problem is that it does not yet demonstrate the consequence its neighbors demonstrate.

---

## Scientific impact of this report

- **Two Report-01 findings are upgraded to blocker severity by primary sources:** the uncited OLAP/Canopy/Pivot-Tracing/process-mining prior art (C1–C3), and the RQ2 "judge votes" fork (A4), which primary-source verification turned from a clarity gap into a dilemma where both readings damage the paper.
- **One Report-01 finding is quantified:** the RQ4 cost omission is ~3–4 orders of magnitude (A6).
- **One Report-01 finding is upgraded with a number:** 405/4,316 = 9.4% coverage on CodeTraceBench, versus the paper's "all 405" (A1).
- **One new external contradiction is introduced:** MP-Bench's methodological critique of single-target attribution evaluation applies directly to RQ2 (D1).
- **One new competitor for D3 is introduced:** CHIEF (D2).
- **A concrete, constructive fix is now available:** OpenClawBench (31,264 trajectories, span localization + taxonomy) is a ready-made untouched confirmation population (D3).
- **The missing-baseline critique is now specific and cheap to satisfy:** AV / BE / nVBE / DLG for segmentation (C4); TraceProbe for grouping (B4); HINTBench's and TraceElephant's own published baselines (A2, A3).

## Uncertainty

- **High confidence:** existence, venue, and substance of all 11 verified primary sources; the OLAP/Canopy/Pivot-Tracing/process-mining/goodness-measure correspondences; the CodeTraceBench 4,316 denominator; Qwen3.6-27B's identity and size.
- **Medium confidence:** exact wording of LangSmith Insights capabilities (WebFetch denied; content reached via search results, B1); my throughput estimate for 27B-Q4 tagging (order of magnitude only, A6); whether OSWorld-Human's released group annotations constitute a semantic responsibility partition (A5) — this needs a data-level check I did not perform.
- **Unresolved and only resolvable by the authors:** the RQ2 "judge votes" provenance (A4); the CodeTraceBench reconstructability filter's selection mechanism (A1).
- **Deliberately not assessed:** I did not read the full PDFs of most 2026 works, only abstracts, HTML landing pages, and search-surfaced content. For the *positioning* claims I make, abstract-level evidence is sufficient; for any claim that a specific prior method would *outperform* AgentProf, it would not be, and I make no such claim.

## Next action

Proceed to Report 03: reread the entire paper end to end with these sources in hand, and re-verify all four RQs, every number, the operation/operation-stack mechanism, the automatic induction algorithm, the baseline set, metric construct validity, real-world relevance, and the end-to-end causal chain from operation model → tags → stacks → folded profile → developer conclusion. Only after 03 is complete will I read `docs/user-instruction.md`, `docs/idea-story.md`, `docs/evaluation.md`, and `docs/background-related-work.md` for the drift audit in Report 04.
