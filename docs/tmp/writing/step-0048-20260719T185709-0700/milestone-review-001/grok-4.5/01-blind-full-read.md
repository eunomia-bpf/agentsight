# 01 — Blind Full-Paper Read and Reject-Hypothesis Map

**Reviewer:** Independent Grok 4.5 milestone reviewer (AgentProf / AAAI-27 main track)
**Timestamp (UTC):** 2026-07-19T18:57:09Z (session start); report written 2026-07-19
**Parent / gate:** Orchestrated milestone REVIEW (`iter-review-critique`), step-0048
**Objective:** Form an unprimed, paper-only whole-paper review and reject-hypothesis map before any prior review, `docs/tmp/`, evaluation memory, idea-story, user-instruction, or proposed fix.
**Read-only scope:** `docs/paper/main.tex`, `docs/paper/references.bib` (via in-paper citations), claim-bearing figures/tables referenced by the main text, and `docs/paper/main.pdf` text extraction.
**Contamination disclosure:** No prior reviewer reports, `docs/evaluation.md`, `docs/idea-story.md`, `docs/user-instruction.md`, or `docs/tmp/` contents were read before this report. Domain review references loaded: `research-taste.md`, `systems-review.md`, `ai-ml-review.md`, `cross-domain-review.md`. Unavoidable contamination: repository name and CLAUDE.md overview (AgentSight/agentpprof context) from system workspace instructions; these were not used as scientific evidence for claims.

---

## 1. Classification, Venue, and Rubric Routing

| Item | Judgment |
|------|----------|
| **Target venue** | AAAI-27 main track (paper uses `aaai2027` style/class; anonymized submission) |
| **Primary contribution type** | **Genuinely cross-domain systems + AI** |
| **Systems layer** | Offline profiler artifact; eBPF-linked AgentSight capture-and-join path; conservation/folding of additive measures; pprof/flame-graph export; construction cost |
| **AI/ML layer** | Semantic tagging (rules, local LLM, TF-IDF/K-Means); label-free recurrence / NPMI boundary induction; partition and boundary metrics (B³, V-measure); problem-localization ranking (MAP) over agent trajectories |
| **References loaded** | Research taste + systems + AI/ML + cross-domain (both bars applied) |
| **Ambiguity** | Paper is not pure systems (weak runtime mechanism depth) nor pure ML (weak learning novelty); residual claim is the *conjunction* of source-linked effects, conserved additive measures, and query-time operation stacks |

**Taste premise (pre-evidence):** The author-fixed thesis statement in the paper is verbatim: *“Agent observability needs profiling, not only debugging.”* The simple principle is that population-level agent analysis needs stable semantic identifiers and hierarchical attribution without relying on code paths or runtime call stacks; the mechanism is uniform weighted *operations* projected onto query-time *operation stacks*.

---

## 2. Paper-Only Argument Reconstruction

### 2.1 Problem and stakes

AI agents produce large populations of trajectories spanning intent (prompts, LLM calls, tools) and system effects (process, file, network). Developers need population answers: where failures concentrate, which workflows cause unsafe effects, which task categories consume budget. Manual inspection and per-trajectory LLM judging do not scale.

**Structural cause (paper claim):** Trajectories lack (1) shared identity for natural-language intent and (2) a reusable cross-run hierarchy of *semantic* responsibility (native nesting ≠ semantic responsibility stack).

### 2.2 Challenged belief

Existing agent tools do tracing, metadata grouping, dashboards, and some hierarchical rollups / process graphs / recovery landscapes, but **do not combine**:

1. source-linked agent *and* system effects,
2. conservation of arbitrary additive measures, and
3. selectable query-time operation stacks

over the same histories. Hence: observability today is debugging-centric; **profiling is missing**.

### 2.3 Principle and mechanism

| Concept | Definition (paper) | Role |
|---------|-------------------|------|
| **Operation** | Uniform weighted record: string fields + additive measures | Unifies prompts, tools, GUI events, process/file/network effects |
| **Operation stack** | Ordered field list \([f_1,\ldots,f_k]\) projecting \(o \mapsto \langle o.f_1,\ldots,o.f_k\rangle\); fold identical sequences, sum weights | Query-time hierarchy replacing runtime call stack |
| **View** | \((\varphi, \sigma, w)\): predicate, stack function, weight | Independent selection of inclusion, hierarchy, metric |
| **Intent attribution** | Rules / local LLM / unsupervised clustering / mapping rules → ordinary fields | D2 stable tags |
| **Label-free recurrence** | NPMI over adjacent visible-action transitions; 1D k-means cutoffs; RLE action sequences as stack frames | Automatic stack construction without user field list / without target labels |
| **AgentProf** | ~9.8K LOC Rust offline CLI; pprof / folded / SVG / JSON export | Implementation |

Pipeline: parse → field derivation → stack construction → fold → export. AgentSight recordings go through a source adapter; CLI does not read AgentSight DBs directly.

### 2.4 Design requirements D1–D3

- **D1** Cross-layer resource projection (intent ↔ system effects)
- **D2** Stable tags for folding
- **D3** Hierarchical attribution without call-stack nesting

### 2.5 Claimed contributions (three)

1. Semantic operation stack model (missing profiling layer)
2. System AgentProf (pluggable attribution + stack construction → pprof)
3. Evaluation: linked effects preserved; attribution and problem ranking improve vs raw action; field backends; cost at 27,765 ops / 1.17 s

### 2.6 Explicit RQs and stated answers (paper-only)

| RQ | Question | Evidence classes (paper) | Stated answer / strength |
|----|----------|--------------------------|---------------------------|
| **RQ1** | Does semantic profiling improve resource attribution? | 20 Codex + concurrent control (AgentSight join); 405 CodeTraceBench human stages (B³); multi-weight flame graphs; multi-depth field hierarchies | Scoped join: **100.0% P / 96.6% R**, reject 1629/1629 controls; recurrence B³ F1 **0.649** vs raw **0.541** (Δ0.108 CI [0.087,0.129]); phase-only **0.654** (close); multi-weight views differ; **post-hoc** on CodeTraceBench constructor selection |
| **RQ2** | Does profiler output correspond to real problems? | Full AgentProcessBench, HINTBench, TraceElephant; MAP vs raw-action grouping; post-hoc local+semantic | MAP up on all three: **.789/.773**, **.452/.281**, **.230/.121**; local-first mechanism adaptive/not primary confirmation |
| **RQ3** | How accurate are the tags? | OSWorld-Human boundaries; TF-IDF/K-Means V-measure; AgentBoard task-family; ASE action labels | Label-free recurrence boundary F1 **0.680**, B³ **0.786** (dev evidence); task-family macro-F1 **0.695**; action **0.498**; V-measure 0.557 / 0.815 |
| **RQ4** | What is the profiling cost? | Fixed-field JSONL construction only; 4 workloads + union | Union **1.17 s**, **464.5 MiB**, +18.2% time / +1.3% RSS vs raw; excludes capture, adaptation, tagging |

---

## 3. Claim-Bearing Figures and Tables (Paper-Referenced)

| Asset | Role | Reviewer reading |
|-------|------|------------------|
| **Fig. architecture** | Pipeline: local histories / operation JSONL → uniform ops → field derivation → stack+fold → profiles | Clear but thin: no failure boundaries, no AgentSight join detail in diagram |
| **Fig. flamegraph (tokens / time / files)** | Same 325 trajectories; different \(\varphi,\sigma,w\) | Visually supports multi-view claim; labels truncated; hierarchy is project→agent→session→prompt→… which is **session-heavy** relative to “cross-run semantic responsibility without session” rhetoric |
| **Table 1 (RQ1 B³)** | Partition agreement vs human stages | Recurrence beats raw; **phase-only slightly beats recurrence** (0.654 vs 0.649)—critical for “recurrence is the star mechanism” narratives |
| **Table 2 (RQ2 MAP)** | Semantic vs raw vs local hybrids | Semantic > raw on all; local+semantic best; AgentProcessBench gains tiny (+0.016) |
| **Table 3 (RQ3 OSWorld)** | Boundary + B³ | Supervised best; label-free solid; always-boundary already strong on B³ (0.678) |
| **Table 4 (RQ4 cost)** | Construction medians | Practical offline cost; **not** end-to-end profiling cost of the claimed stack |

**Note:** Auxiliary TeX tables under `figures/` (case-table, claim-gate-table, evidence-path-table, experiment-role-table, task-verdict-table) and `fig-rq1-separation` / `fig-rq3-vmeasure` are **not** `\input`/`\includegraphics`’d by `main.tex`. They are **not** part of the active paper argument for this review.

---

## 4. Blind Assessment Dimensions

### 4.1 Problem importance

**Real and timely.** Population analysis of agents is a genuine production pain. AAAI audience cares about agents, evaluation, and tools. The debugging-vs-profiling gap is rhetorically sharp.

**Risk:** Problem may be framed as “missing conjunction of three features” rather than a single falsifiable scientific gap. If commercial tools already fold cost by hierarchical categories, residual novelty must be precise.

### 4.2 Novelty articulation

Paper positions residual capability carefully against LangSmith Insights, Datadog Patterns, NeMo profilers, OTel Profiles, TraceProbe, Graphectory, Hodoscope, TraceGraph, AgentRx, CodeTracer, localization benchmarks.

**Blind novelty read:** Closest risk is *productized hierarchical aggregation + trace analytics*, not classical CPU profilers. Academic process-graph / trajectory-structure papers (2025–2026 citations) look adjacent. The combination claim may survive, but only if external search confirms commercial and research systems lack source-linked conserved multi-measure query-time stacks.

### 4.3 Architecture / mechanism depth

**Strengths:**

- Clean two-object model (operation + operation stack)
- Formal view triple \((\varphi,\sigma,w)\)
- Pluggable field backends keep model independent of tag source
- Recurrence algorithm is specified (NPMI, dual cutoffs, RLE frames)
- Explicit conservation language for additive weights

**Weaknesses:**

- AgentSight join is **upstream and scoped**; AgentProf does not implement cross-layer capture—adapter + declared process/tool scope. D1 is partly outsourced.
- “Profiling” here is mostly **offline fold of already-tagged JSONL**, not sampling, continuous production profiling, or online systems.
- Automatic induction defaults are admitted **post-hoc** on the corpora used for design.
- Flame graphs still lean on session/prompt hierarchy—tension with “no reusable hierarchy” diagnosis.

### 4.4 Claim calibration

Paper is unusually careful in places (post-hoc flags, local-first not primary confirmation, majority baselines for LLM tags, HINTBench 536 vs 629 snapshot honesty).

Still overclaims in abstract/conclusion relative to body:

- Abstract packs many numbers without post-hoc / scope caveats.
- “Improve resource attribution” is partly **partition agreement with human stages**, not measured token/I/O reassignment correctness vs ground-truth cost owners beyond predeclared totals.
- RQ2 “real problems” uses localization *benchmarks*, not production incidents or human analyst studies.
- RQ3 “tag accuracy” mixes structural partitions, boundaries, and literal labels; action macro-F1 0.498 is modest for a headline-ready tagger.
- RQ4 cost is construction-only.

### 4.5 Evaluation construct validity

| RQ | Construct | Valid for… | Weak for… |
|----|-----------|------------|-----------|
| RQ1 join | Precision/recall of in-scope effects vs concurrent control | Scoped lineage hygiene | General multi-tenant production; network-only/side-channel effects; undeclared scope |
| RQ1 B³ | Agreement with human contiguous stages | “Responsibility units” as annotators define them | Resource *attribution quality* (weights) or causal cost ownership |
| RQ1 multi-weight | Spearman / top-k disagreement | Multi-metric utility of views | Causal bottleneck correctness |
| RQ2 MAP | Ranking annotated problem ops earlier under group scores | Target-blind grouping utility on localization benches | Developer inspection work, safety remediation, online monitoring |
| RQ3 | Macro-F1 / V-measure / boundary F1 | Field backend quality under stated inputs | Universal semantic discovery; production tag stability |
| RQ4 | Parse/stack/fold/serialize time | Offline CLI practicality | Live eBPF, LLM tagging, adaptation cost |

**Baselines:** Raw-action grouping is the primary foil—necessary but possibly weak. Phase-only sometimes matches/beats recurrence. Always-boundary is a strong structural foil on OSWorld B³. Majority class for LLM tags is weak. Missing: commercial hierarchy rollups, OTel/Phoenix imported profiles, TraceProbe/Graphectory process profiles, strong unsupervised segmentation baselines, human time-to-insight.

### 4.6 Real-world relevance

**Positive:** 325 real local histories; 20 real Codex captures with concurrent controls; multi-agent-framework CodeTraceBench; public localization suites.

**Gaps:** No closed-loop “profile → fix → cost/safety improved” study; no multi-team production deployment; AgentSight path is 20 fixed tasks under declared scope; many results on public annotated corpora (adapter-mapped).

### 4.7 Global consistency

- Thesis, contributions, and conclusion align on profiling-not-debugging.
- Related work concedes adjacent systems; residual conjunction is consistent.
- Internal tension: phase-only ≥ recurrence on CodeTraceBench while abstract spotlights recurrence.
- Internal tension: D1 is central, yet most RQs run on public operation JSONL without live system effects.
- Flame graphs show session-centric stacks while prose emphasizes cross-run semantic fields without session.

### 4.8 Limitations honesty

Scope section is present and mostly accurate. Still soft on: AAAI significance of engineering packaging; modest effect sizes; lack of human utility; residual novelty vs 2026 process-centric agent analysis literature.

### 4.9 Submission readiness (blind)

Mechanically near-complete AAAI-shaped paper (abstract through conclusion, 4 RQs, tables, related work). Scientific readiness for AAAI main track is **uncertain-to-reject** without external novelty verification and stronger end-to-end causal evidence that *profiling* (not just better clustering/ranking) changes outcomes.

---

## 5. Reject-Hypothesis Map (Strongest First)

| ID | Severity hypothesis | Hypothesis | Paper location | Why it could kill |
|----|---------------------|------------|----------------|-------------------|
| **H1** | Blocker | **Novelty is incremental packaging:** hierarchical metadata rollups + process graphs + pprof export already cover the residual claim; “conjunction” is engineering, not a new principle. | Intro ¶4–5; Related Work | AAAI rejects “system that combines known pieces” without new prediction or decisive advantage |
| **H2** | Blocker | **Thesis mismatch with evidence:** paper proves offline semantic grouping/ranking, not that *observability needs profiling* as a distinct necessity; debugging tools + dashboards already answer population questions. | Abstract thesis; RQ1–RQ2 | Belief challenge collapses to strawman |
| **H3** | Blocker / Major | **D1 is not delivered by AgentProf:** cross-layer projection is AgentSight + adapter + 20-task scoped eval; the model mostly folds pre-linked fields. | Impl input reconstruction; RQ1 first experiment | Systems contribution hollow; AI contribution is tagging/segmentation |
| **H4** | Major | **Primary mechanism underwhelms:** recurrence ≤ phase-only on CodeTraceBench; gains vs raw are real but phase is a simpler semantic field. | Table 1; Limitations | Mechanism not load-bearing for headline improvement |
| **H5** | Major | **RQ2 construct validity:** MAP on localization benchmarks with group aggregation of judge votes / Wilson bounds ≠ “corresponds to real problems” for developers. | RQ2 | AI evaluation standard fails (proxy ranking) |
| **H6** | Major | **Post-hoc / adaptive contamination:** constructor designed after CodeTraceBench/OSWorld inspection; HINTBench field-order from val snapshot; local+semantic post-hoc. | RQ1/RQ3 text | Overfitting / researcher degrees of freedom |
| **H7** | Major | **Weak baselines:** missing commercial Insights/Patterns, TraceProbe, strong segmentation, OTel profiles; majority-class for LLM tags. | RQ2–RQ3 | Fair-comparison failure |
| **H8** | Major | **Cross-domain causal chain incomplete:** no evidence that better profiles improve agent quality, safety, or cost after intervention. | End-to-end thesis | Cross-domain reject: systems metric without outcome |
| **H9** | Major | **RQ4 answers the wrong cost:** construction of pre-tagged JSONL is cheap; true cost is capture + tagging + human interpretation. | RQ4 | Cost RQ fails claim match |
| **H10** | Minor–Major | **Metric collage:** B³, MAP, macro-F1, V-measure, boundary F1, precision/recall, Spearman—hard to form one scientific result. | Evaluation | Complicated-but-shallow taste failure |
| **H11** | Minor | **Figure readability:** flame graphs truncated labels; architecture omits join/conservation. | Fig 1–2 | Presentation, not science |
| **H12** | Minor | **Action tagger mediocre (0.498 macro-F1)** for a claimed tagging path. | RQ3 | Undermines D2 production story |
| **H13** | Minor | **Scale:** 27k ops / 1.17 s is not systems-impressive; millions of spans is production scale. | RQ4 | Underambition on scale |
| **H14** | Nit | Abstract number density without caveats; Chinese comments in source (harmless for PDF). | Abstract / source | Polish |

---

## 6. Load-Bearing Claims Requiring External Verification

1. **Closest same-claim systems:** LangSmith Insights, Datadog Patterns, NeMo Agent Toolkit profiler, OpenTelemetry Profiles, Phoenix, Laminar Signals—do they already support hierarchical cost folding and cross-trace categories over agent+system effects?
2. **Closest academic process/trajectory structure work:** TraceProbe, Graphectory, Hodoscope, TraceGraph, WebGraphEval, CodeTracer, AgentRx, MPBench / multi-perspective failure attribution—same-claim risk.
3. **AgentProcessBench, HINTBench, TraceElephant:** existence, protocols, whether MAP-with-group-scoring is an accepted use or paper-invented protocol.
4. **CodeTraceBench / OSWorld-Human:** stage/group annotations as responsibility ground truth validity.
5. **B³, V-measure, Wilson bound, non-interpolated AP:** correct use vs community norms.
6. **pprof tagroot/tagleaf** and flame graphs: does classical tooling already allow semantic pseudo-stacks?
7. **NPMI + 1D k-means segmentation:** prior art in collocation / boundary detection; is recurrence novel?
8. **Contradictory evidence:** negative results that hierarchical aggregation does not help localization or that LLM judges already suffice for population analysis.
9. **AAAI-27 main track** expectations for systems+agents tools papers.
10. **AgentSight** primary source: what it actually contributes vs AgentProf.

---

## 7. Initial Paper-Only Verdict (Pre-Search)

**Provisional recommendation: Weak reject / borderline major revision** under AAAI main-track + cross-domain taste bar.

**Strongest accept case (if external search is kind):** A clean, general principle—agent profiles need query-time semantic stacks over conserved multi-layer operations—with a working offline profiler, honest multi-RQ evaluation, and consistent residual novelty vs pure tracing tools.

**Strongest reject case (current paper-only):** The paper packages known aggregation ideas with a careful but proxy-heavy evaluation; the load-bearing automatic mechanism is not clearly superior to simple phase fields; D1 is scoped out; no outcome-level causal proof that “profiling not debugging” changes practice.

**Taste label (blind):** **Incomplete-but-promising** leaning **complicated-but-shallow**—many populations and metrics, one principle that is still partly engineering packaging.

**Scientific impact if claims hold:** Medium—could standardize how agent teams roll up cost/safety across runs.
**Uncertainty:** High until external closest-work and benchmark protocols are verified.

---

## 8. Method Notes

- Full `main.tex` read (title through conclusion).
- `main.pdf` text extraction cross-checked (layout fragmentation noted; numbers match TeX).
- All main-text figures/tables inspected.
- Non-included figure TeX tables noted as non-active.
- No external web search in this phase (by protocol).

---

## 9. Next Action

Proceed to **mandatory external search and primary-source verification** (`02-external-search.md`): attack H1–H8 with primary papers, product docs, and benchmark artifacts; verify load-bearing novelty and metric protocols; update attack map with source-supported facts.
