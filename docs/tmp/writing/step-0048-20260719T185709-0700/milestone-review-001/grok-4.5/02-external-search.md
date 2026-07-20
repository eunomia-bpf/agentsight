# 02 — External Search and Primary-Source Verification

**Reviewer:** Independent Grok 4.5 milestone reviewer (AgentProf / AAAI-27 main track)
**Timestamp (UTC):** 2026-07-19
**Parent:** `01-blind-full-read.md` (unprimed attack map H1–H14)
**Objective:** Search broadly and verify primary papers/docs for every load-bearing novelty, mechanism, benchmark, metric, and contradictory-evidence question before reassessing the full paper.
**Method:** Web search + open primary arXiv HTML/abs pages + official product documentation. Snippets used only as discovery; claims below are grounded in opened primary sources or official docs.
**Contamination:** Still no prior reviewer reports, `docs/tmp/` peer reports, `docs/evaluation.md`, `docs/idea-story.md`, or `docs/user-instruction.md`.

---

## 1. Search Plan and Coverage Matrix

| Load-bearing question | Queries / families | Primary sources opened | Attack map impact |
|----------------------|--------------------|------------------------|-------------------|
| Same-claim commercial hierarchy rollups | LangSmith Insights, Datadog Patterns | Official LangSmith Insights docs; Datadog Patterns blog/docs | **H1, H2 strengthened** |
| Classical profiling already supports tags | pprof tagroot/tagleaf, OTel Profiles | Polar Signals / pprof docs; OpenTelemetry Profiles concepts/spec | **H1 partially supported** |
| Cross-layer capture prior work | AgentSight eBPF | arXiv:2508.02736 (AgentSight) | **H3 confirmed: D1 is prior system** |
| Process graphs / trajectory structure | TraceProbe, Graphectory, Hodoscope, TraceGraph | arXiv TraceProbe 2607.06184; Graphectory 2512.02393 HTML; Hodoscope 2604.11072 | **H1 major same-claim risk** |
| Failure attribution / localization benches | AgentProcessBench, HINTBench, TraceElephant, MP-Bench | arXiv HTML for AgentProcessBench, HINTBench, TraceElephant abs; MP-Bench abs/repo | **H5: protocol mismatch** |
| Stage ground truth validity | CodeTracer / CodeTraceBench | arXiv:2604.11641 HTML | **RQ1 construct: stages designed for failure localization** |
| OSWorld group annotations | OSWorld-Human | arXiv:2506.16042 | **RQ3 groups = human efficiency trajectories, not profiler labels** |
| Metrics | B³, MAP/AP, V-measure, Wilson | Known standards (Bagga & Baldwin 1998; Robertson AP; Rosenberg & Hirschberg; Wilson 1927) | Constructs standard; **application novel/proxy** |
| Venue bar | AAAI-27 main track | aaai.org submission instructions / main track call | **7 content pages; broad AI significance** |

**Source families included:** agent observability products, classical profiling, systems AgentOps (eBPF), process-centric SE agents, failure attribution/safety localization, computer-use efficiency benchmarks, metric classics.
**Excluded as evidence:** secondary blogs without primary product/paper text; model-generated summaries.

---

## 2. Verified Closest Work (Novelty Attack)

### 2.1 Commercial agent observability (primary docs)

**LangSmith Insights** ([docs.langchain.com/langsmith/insights](https://docs.langchain.com/langsmith/insights); LangChain blog “From Traces to Insights”):

- Automatically analyzes production traces; **hierarchical categorization** (top-level categories → subcategories → individual runs).
- Aggregates **error rates, latency, cost**, feedback scores, and extracted attributes per category.
- Unsupervised clustering / hierarchical taxonomies; scheduled reports; predefined categories optional.
- Explicit goal: answer population questions without manual review of thousands of traces.

**Datadog Agent Observability Patterns** ([docs.datadoghq.com/llm_observability/](https://docs.datadoghq.com/llm_observability/); Patterns product posts):

- **Automated hierarchical topic clustering** of production traffic.
- Each pattern surfaces **cost, latency, error rate**, evaluation coverage.
- Designed for recurring behaviors and quality/cost drivers at population scale.

**Implication for paper residual claim:**
Paper claims existing tools “do not combine source-linked agent and system effects, conservation of arbitrary additive measures, and selectable query-time operation stacks.”
Primary sources show commercial tools **already** do hierarchical grouping + cost/latency rollups + population dashboards. What remains distinctive (if true) is:

1. **Source-linked process/file/network effects** (AgentSight path),
2. **Arbitrary additive measures** conserved under fold (files, network event counts, not only tokens/latency),
3. **User-selectable query-time field stacks** as first-class profile projection (pprof-like), not fixed Insights hierarchy.

This is a **narrow residual**, not a clean “missing profiling layer.” H1 remains open but **stronger**: novelty is conjunction engineering + multi-layer measures + offline pprof, not hierarchical population analysis per se.

### 2.2 OpenTelemetry Profiles and classical pprof tags

**OpenTelemetry Profiles** ([opentelemetry.io/docs/concepts/signals/profiles/](https://opentelemetry.io/docs/concepts/signals/profiles/); Profiles Alpha announcements 2026):

- Profiles as fourth signal: stack traces with resource values; bi-directional links to traces.
- Continuous production profiling orientation (CPU/heap/etc.), not agent semantic stacks.

**pprof labels / tagroot / tagleaf** (Go runtime/pprof docs; Polar Signals / Mark Hansen writeups):

- Labels already attach key-value pairs to samples; `tagroot`/`tagleaf` promote labels to **pseudo-frames**.
- Paper acknowledges this; residual is that agent tags must be *derived* (no function names).

**Implication:** Output compatibility and tag-as-frame ideas are **prior art**. The scientific claim must rest on **agent-specific identity + hierarchy construction**, not on inventing profiles.

### 2.3 AgentSight (upstream systems contribution)

**AgentSight** (Zheng et al., arXiv:2508.02736; PACMI workshop; github.com/eunomia-bpf/agentsight):

- eBPF boundary tracing: TLS LLM traffic + kernel effects; causal correlation; <3% overhead.
- Detects prompt injection, reasoning loops, multi-agent bottlenecks.
- **Already claims system-level agent observability / profiling-adjacent monitoring.**

**Implication for H3:** Cross-layer resource projection (D1) is **AgentSight’s contribution**. AgentProf’s RQ1 join experiment evaluates an **adapter path** under declared process/tool scope, not a new capture mechanism. Systems depth of AgentProf is primarily offline compile/fold/export.

### 2.4 Process-centric trajectory analysis (major same-claim neighbors)

| Work | Primary claim (source-supported) | Overlap with AgentProf | Differentiation (paper-side) |
|------|----------------------------------|------------------------|------------------------------|
| **TraceProbe** (Shu et al., arXiv:2607.06184) | Normalize runs to action taxonomy + effect labels; resource-aware **process profiles**; anti-pattern detectors; multi-run comparison | Process profiles, population diagnostics | Paper: conserved multi-measure fold + query-time stacks + system-effect join |
| **Graphectory** (Liu et al., arXiv:2512.02393 / OOPSLA 2026) | Graph encoding of trajectories; phase patterns; **online intervention improves resolution 6.9–23.5%** | Cross-run process structure, phase analysis | AgentProf offline profiles; Graphectory has **outcome causal evidence** AgentProf lacks |
| **Hodoscope** (Zhong et al., arXiv:2604.11072) | Unsupervised distributional diffing of agent behaviors for human review | Population unsupervised discovery | Not conserved additive multi-stack profiling |
| **TraceGraph** (Nian et al., arXiv:2605.31308, cited in paper) | Shared decision landscapes for diagnosis/improvement | Cross-run structure | Diagnosis-oriented, not pprof conservation |
| **CodeTracer** (Li et al., arXiv:2604.11641) | Hierarchical state transition trees; failure onset localization; **CodeTraceBench** stage/step labels | Hierarchical traces; paper’s RQ1 stages | Per-run diagnosis + replay recovery, not population fold |

**Strongest novelty risk:** TraceProbe + Graphectory already treat trajectories as **process profiles/graphs** for population analysis. AgentProf’s differentiator must be the **operation + query-time stack + multi-measure conservation + optional system effects** package—and evaluation must show that package buys something they do not. Current primary baselines (raw action only) **do not include these neighbors**.

### 2.5 Failure attribution / process evaluation benches (protocol validity)

**AgentProcessBench** (Fan et al., arXiv:2603.14465; KDD’26-bound; github RUCBM/AgentProcessBench):

- 1,000 trajectories, 8,509 human step labels (+1/0/−1) for **PRM / step effectiveness**.
- Task is LLM-as-judge of step quality, **not** profiler MAP ranking of groups.
- Paper’s use: average judge votes within semantic groups, score as MAP—**repurposed protocol**, not the benchmark’s primary evaluation.

**HINTBench** (Wang et al., arXiv:2604.13954):

- **629** trajectories (523 risky / 106 safe); tasks: risk detection, **risk-step localization**, failure-type ID.
- Primary metrics: detection accuracy, Strict-F1 on step localization (<35 for strong LLMs).
- Paper uses 536-test snapshot + MAP with Wilson-bound group scores—**again a profiler-invented ranking protocol** on localization-oriented annotations.

**TraceElephant** (Chen et al., arXiv:2604.22708; ACL 2026):

- Failure attribution (agent + decisive step) under **full execution observability**.
- Argues partial traces understate causes; full traces improve attribution up to 76%.
- Primary goal is **attribution method evaluation**, not semantic profile MAP.

**MP-Bench** (In et al., arXiv:2603.25001):

- Multi-perspective failure attribution; challenges single ground-truth labels.
- Paper cites related work but does not engage multi-perspective disagreement as a validity threat to RQ2 targets.

**Implication for H5:** RQ2’s “corresponds to real problems” is **construct-stretched**. Benchmarks supply step/risk/failure targets for *judges and attributors*; paper measures whether group aggregation ranks target ops earlier. Gains vs raw action can be real under that proxy without proving developer-facing problem correspondence or superiority over TraceProbe/Graphectory-style process analysis.

### 2.6 CodeTraceBench stages and OSWorld-Human groups

**CodeTraceBench** (via CodeTracer paper):

- Stage labels: environment verification, dependency install, inspection/debugging, patching, verification.
- Designed for **failure localization / hierarchical tracing**, with κ=0.73 on error-critical steps.
- Using stages as “human responsibility partitions” for B³ is plausible but **not the original annotation purpose**. Phase field may dominate because stages *are* phase-like (paper’s phase-only 0.654 ≈ recurrence 0.649).

**OSWorld-Human** (Abhyankar et al., arXiv:2506.16042):

- Human-efficient computer-use trajectories for **efficiency benchmarking** (steps vs humans).
- Group annotations paper uses for boundary F1 are human action groupings—valid structure, but **efficiency-oriented**, not agent-failure responsibility. Designing recurrence after inspecting this corpus (admitted) is development leakage.

---

## 3. Mechanism Prior Art

| Mechanism | Prior art | Novelty status |
|-----------|-----------|----------------|
| Uniform event records + fold by key | Traces, spans, pprof samples, metrics aggregation | Incremental packaging |
| Query-time field projection as stack | pprof tags; multi-dimensional OLAP rollups; Insights hierarchies | Framing as “operation stack” is useful; not deep new algorithm |
| NPMI on transitions | Collocation (Bouma 2009); classic NLP association | Standard scoring |
| 1D k-means thresholding | Classic clustering | Standard |
| RLE action sequences as frames | Sequence compression / motif | Engineering |
| Label-free recurrence over sessions | Adjacent to unsupervised segmentation / Hodoscope-style discovery | **Possible contribution if shown general**; current evidence post-hoc / phase-competitive |
| LLM closed-label task/action tagging | Ubiquitous classification | Not novel; 0.498 action macro-F1 is modest |
| eBPF SSL + process join | **AgentSight** | Not AgentProf’s invention |

---

## 4. Metric Construct Validity (External Norms)

| Metric | Standard use | Paper use | Validity note |
|--------|--------------|-----------|---------------|
| **B³** (Bagga & Baldwin 1998) | Coreference / cluster partition agreement | Predicted vs human stage/group partitions | Accepted partition metric; **does not measure resource weight correctness** |
| **V-measure** | Clustering purity/completeness | TF-IDF/K-Means task partitions | OK for partitions; small Mind2Web n=49 ops weak |
| **MAP / AP** (IR) | Ranking relevance | Ranking ops by group-derived scores vs annotated targets | Standard ranking math; **relevance = localization labels**, not human inspection value |
| **Wilson lower bound** | Binomial CI | Aggregate hit rate as group score | Statistically conventional; scoring rule paper-designed |
| **Macro-F1** | Multi-class classification | Task-family / action tags | Standard; majority baseline weak |
| **Precision/recall of joins** | IR / detection | In-scope effects vs concurrent control | Strong for **scoped** lineage hygiene |

**No external protocol** was found that evaluates “semantic profiler MAP on failure-localization benches.” This is an original evaluation design—acceptable if justified, but reviewers will demand baselines from process-graph and commercial hierarchy tools.

---

## 5. Contradictory / Negative Evidence Relative to Thesis

1. **Population analysis already exists without “profiling” framing:** LangSmith Insights and Datadog Patterns answer “where failures/cost concentrate” via hierarchical categories—undercuts “observability needs profiling, not only debugging” as a **missing** capability. Profiling may still be a *better abstraction*, but belief-challenge requires sharper contrast.

2. **Graphectory shows process analysis can change outcomes** (resolution + trajectory shortening under online intervention). AgentProf shows ranking/partition metrics only—**weaker causal chain** for “why profiling matters.”

3. **Phase fields ≈ recurrence** on CodeTraceBench stages: if stages are phase labels, automatic NPMI recurrence is not the key insight—**semantic fields matter**, automatic induction less so.

4. **HINTBench / AgentProcessBench show step-level auditing is hard for LLMs**; hierarchical grouping may help inspection, but paper does not show superiority over dedicated attributors or PRMs.

5. **MP-Bench multi-perspective disagreement:** single annotated targets for MAP may overstate “real problem” uniqueness.

6. **OTel Profiles + APM** already connect resource samples to traces—systems community may see agent semantic stacks as application-layer labeling, not systems profiling innovation.

---

## 6. Real-World Problem Existence (Belief Support)

**Supported by primary sources:**

- Agents generate large trajectory populations; manual review does not scale (LangSmith Insights motivation; Datadog Patterns).
- Cost, latency, errors concentrate in patterns (commercial tools).
- Process structure reveals inefficiency beyond pass/fail (Graphectory, TraceProbe, CodeTracer).
- Intent–effect gap is real (AgentSight).

**Thesis “needs profiling, not only debugging”:** Partially supported as a *useful framing*, but **not uniquely forced**—“needs hierarchical population analytics / process-centric evaluation” is equally supported and already partially productized.

---

## 7. Venue: AAAI-27 Main Track

Primary AAAI-27 instructions ([aaai.org](https://aaai.org/conference/aaai/aaai-27/submission-instructions/), main technical track call):

- **7 pages** main content; pages 8–9 references only (9 page total cap for refs).
- Double-blind; broad AI significance; technical soundness.
- Supplementary allowed; reviewers not required to read it.

**Implication:** Paper must deliver a clear AI-significant scientific claim in 7 pages. A long multi-RQ systems+tools evaluation risks looking like an **engineering report** unless the principle and decisive evidence are sharp. Cross-domain systems depth is secondary to AI significance at AAAI main (unlike SOSP/OSDI).

---

## 8. Updated Attack Map After Search

| ID | Status after search | Change |
|----|---------------------|--------|
| **H1 Novelty packaging** | **Strengthened toward blocker** | Insights/Patterns + TraceProbe/Graphectory close residual gap; raw-action baseline inadequate |
| **H2 Thesis strawman** | **Strengthened major→blocker risk** | Population hierarchical analytics exist; “profiling” must prove distinct necessity |
| **H3 D1 outsourced** | **Confirmed** | AgentSight is published capture system; AgentProf is offline profiler |
| **H4 Recurrence weak** | **Confirmed major** | Phase-competitive; stages are phase-like |
| **H5 RQ2 construct** | **Strengthened major** | Benches designed for PRM/attribution, not profiler MAP |
| **H6 Post-hoc** | Unchanged major | Still paper-admitted |
| **H7 Weak baselines** | **Strengthened blocker-adjacent** | Missing Insights-like hierarchy, TraceProbe, Graphectory, strong segmentation |
| **H8 No outcome chain** | **Strengthened major** | Neighbors show resolution gains; AgentProf does not |
| **H9 RQ4 wrong cost** | Unchanged major | Still construction-only |
| **H10 Metric collage** | Unchanged | Fits AAAI density risk |
| New **H15** | **Major** | **Page/venue mismatch risk:** 4 RQs × multi-bench evidence may crowd out clear AI claim in 7 pages |
| New **H16** | **Major** | **Baseline omission of same-claim academic process profilers (TraceProbe)** is a fairness defect |

---

## 9. What Would Discriminate Accept vs Reject (Experiments / Evidence)

**Missing requirements for a full empirical AAAI paper (not optional polish):**

1. **Same-claim baselines:** at least one of TraceProbe process profiles, Graphectory phase aggregation, or commercial-style hierarchical clustering on identical operations for RQ1/RQ2.
2. **Defend residual novelty with a precise table:** source-linked effects × conserved multi-measures × query-time stack selection—**with empirical win only when all three interact** (ablation of conjunction).
3. **RQ2 protocol validity:** human/analyst study or explicit mapping from MAP to inspection work; or use each bench’s **native** localization metrics (Strict-F1, attribution accuracy) not only custom MAP.
4. **Independent held-out family** for recurrence (no CodeTraceBench/OSWorld design influence).

**Optional strengthening (not missing requirements):**

- Closed-loop “profile → agent config change → cost/safety improved.”
- Live eBPF overhead end-to-end.
- Multi-million operation scale.
- MP-Bench multi-perspective sensitivity.

---

## 10. Scientific Impact of Search Findings

| Finding | Impact |
|---------|--------|
| Commercial hierarchical rollups | Shrinks “missing profiling” belief challenge |
| TraceProbe/Graphectory | Raise bar for process-profile novelty and baselines |
| AgentSight prior | Separates capture science from AgentProf fold science |
| Benchmark repurposing | Weakens RQ2 headline “real problems” |
| Graphectory outcome gains | Highlights AgentProf’s missing causal outcome edge |

**Uncertainty remaining:** Exact feature parity of LangSmith/Datadog with “arbitrary additive system measures” and pprof export—docs show cost/latency/errors, not clearly file/network event conservation under multi-field stacks. Residual conjunction may still be real but **must be demonstrated**, not asserted.

---

## 11. Sources (Primary / Official)

1. https://docs.langchain.com/langsmith/insights
2. https://www.langchain.com/blog/from-traces-to-insights-understanding-agent-behavior-at-scale
3. https://docs.datadoghq.com/llm_observability/
4. https://www.datadoghq.com/blog/patterns-agent-observability/
5. https://opentelemetry.io/docs/concepts/signals/profiles/
6. https://opentelemetry.io/docs/specs/otel/profiles/
7. https://arxiv.org/abs/2508.02736 (AgentSight)
8. https://arxiv.org/html/2603.14465v1 (AgentProcessBench)
9. https://arxiv.org/html/2604.13954v1 (HINTBench)
10. https://arxiv.org/abs/2604.22708 (TraceElephant)
11. https://arxiv.org/abs/2607.06184 (TraceProbe)
12. https://arxiv.org/html/2512.02393 (Graphectory)
13. https://arxiv.org/abs/2604.11072 (Hodoscope)
14. https://arxiv.org/html/2604.11641v3 (CodeTracer / CodeTraceBench)
15. https://arxiv.org/abs/2506.16042 (OSWorld-Human)
16. https://arxiv.org/abs/2603.25001 (MP-Bench)
17. https://aaai.org/conference/aaai/aaai-27/submission-instructions/
18. https://aaai.org/conference/aaai/aaai-27/main-technical-track-call/
19. pprof labels / tagroot documentation (Go runtime/pprof; Polar Signals demystifying labels)

---

## 12. Next Action

Full-paper reread (`03-full-reread-assessment.md`) with source-updated attack map: reassess all four RQs, numbers, operation-stack mechanism, induction algorithm, baselines, construct validity, real-world relevance, and end-to-end causal chain. No author-intent documents until report 04.
