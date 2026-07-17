# Step 0033 Milestone Review 001 — External Search and Primary-Source Verification

**Timestamp:** 2026-07-16T17:25:08-07:00
**Parent node:** Step 0033, `REVIEW_GATE`, milestone review 001
**Objective:** Attack the blind-read map with primary and official sources before rereading the paper or consulting internal author/change documents.

## Inputs and provenance

This phase began only after `01-blind-full-paper-read.md` was complete. It used the paper's load-bearing claims and bibliography as the search seed, but still did not consult `docs/user-instruction.md`, `docs/idea-story.md`, prior reviews, Step 0033 plans/results, or the cycle diff.

I searched and opened primary papers, official benchmark pages, official product documentation, official metric documentation, and the official venue site. Search snippets and third-party pages were used only for discovery and excluded from substantive conclusions. The key source families were:

- NIST TREC and scikit-learn documentation for AP/MAP;
- LangSmith, Datadog, NVIDIA NeMo Agent Toolkit, Google pprof, and OpenTelemetry official documentation;
- primary papers/pages for AgentProcessBench, HINTBench, TraceElephant, AgentRx, TELBench/DRIFT, and AgentDiagnose;
- the official AAAI-27 page and official recent AAAI main-track formatting precedent.

## Search questions, representative queries, and coverage

| Branch | Questions | Representative query families | Included evidence | Exclusions |
|---|---|---|---|---|
| Standard ranking protocol | Is per-query non-interpolated AP with arithmetic-mean MAP standard? How are ties and zero-relevant queries handled? | `site:trec.nist.gov average precision MAP topic`; `site:scikit-learn.org average_precision_score non-interpolated`; `no relevant average precision topic` | NIST TREC ranked-list evaluation; scikit-learn API definition/source | Wikipedia and generic tutorials were excluded; they add no authority over NIST/library docs. |
| Cross-run profiling/observability | Do current products already cluster behavior hierarchically and aggregate cost/error? Does a workflow profiler already exist? | `LangSmith Insights hierarchy traces cost`; `Datadog Patterns topic hierarchy errors cost`; `NeMo Agent Toolkit profiler nested stack bottleneck` | LangSmith, Datadog, and NVIDIA official docs | Vendor blogs and marketing summaries were excluded when equivalent product docs were available. |
| pprof/semantic substrate | Does pprof already support labels as dimensions or pseudo-frames? | `google pprof tagroot tagleaf labels official` | Google pprof documentation | Unresolved GitHub issues were not used as capability evidence. |
| Failure localization | Which direct diagnostic systems and protocols would reviewers expect? | `AgentRx failure step`; `TELBench DRIFT span localization`; `AgentDiagnose trajectories`; `TraceElephant failure attribution` | Primary arXiv/ACL/ACM pages and full arXiv HTML where available | Model-generated summaries, news posts, and social discussions were excluded. |
| Benchmark construct | What do the three RQ2 datasets actually label and report? | benchmark names plus `official`, `labels`, `metrics`, `test split` | Benchmark authors' papers/pages and repositories linked by them | Unverified mirrors and leaderboard reposts were excluded. |
| Venue readiness | What are the 2027 deadline/style signals and the current main-track page convention? | `AAAI-27 author kit`; `AAAI main track 7 pages technical content references` | AAAI-27 official conference page; official AAAI-26/25 main-track instructions as current precedent | Template aggregator sites and forum posts were excluded. |

## Source verification results

### 1. AP/MAP is standard; the paper's conditional population must remain explicit

The [NIST TREC ranked-list evaluation page](https://trec.nist.gov/presentations/TREC9/overview/tsld014.htm) defines AP for one topic from precision at relevant retrieval points and MAP as the mean across topics. This supports the paper's mapping of a target-bearing trajectory to a retrieval query and the arithmetic mean of per-trajectory AP values.

The [scikit-learn `average_precision_score` documentation](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.average_precision_score.html) defines non-interpolated AP as

\[
\mathrm{AP}=\sum_n (R_n-R_{n-1})P_n,
\]

with recall increments weighting the precision at score thresholds. It explicitly distinguishes this from trapezoidal area under the precision-recall curve, which can be optimistic. The threshold formulation also means tied scores are evaluated together rather than being broken by arbitrary item order. Thus “standard non-interpolated average precision” is accurate if the implementation really calls this function on the declared operation scores.

A trajectory with no relevant operation has no meaningful per-query recall progression in the usual IR question. The paper's choice to call the primary quantity **target-bearing trajectory MAP** is scientifically defensible, not metric invention, provided the conditioning is impossible to miss. The current evaluation subsection does disclose the query definition and gives 614, 400, and 220 queries. However, the introduction says “Across three complete public benchmarks ... trajectory MAP,” which can be read as averaging all 1,756 trajectories rather than the 1,234 target-bearing queries. The fix is not to abandon MAP or count no-target trajectories as ordinary AP queries; it is to say that all operations were scored and MAP was then computed over the target-bearing query population.

The pooled operation AP is not the same estimand as MAP: it concatenates operations and therefore weights longer trajectories more heavily. It is useful as a **secondary directional safeguard** because it retains operations from zero-positive trajectories as nonrelevant work. The paper already labels it “pooled operation AP,” does not average it into MAP, and reports the same direction. This is appropriate; it should not be promoted as a replacement primary metric.

**Verdict:** the new metric family is standard and suitable. The remaining issue is conditional-population wording, not metric validity. Work@80/Work@50 remains useful as a task-specific inspection-budget diagnostic, but it should stay secondary and benchmark-specific, as the paper currently does.

### 2. The RQ2 dataset constructs are real, but MAP is an AgentProf-derived protocol

The [AgentProcessBench primary paper](https://arxiv.org/abs/2603.14465) reports 1,000 tool-using trajectories and 8,509 human-labeled assistant steps, with ternary labels: correct/progressing, neutral/exploratory, and incorrect/harmful. It reports 89.1% inter-annotator agreement and describes StepAcc/FirstErrAcc as native evaluation tasks. Treating `-1` operations as relevant for an AgentProf ranking analysis is a reasonable derived use of the released labels, but MAP is not the benchmark authors' native headline protocol.

The [HINTBench primary page](https://arxiv.org/abs/2604.13954) reports 629 trajectories (523 risky, 106 safe) and three tasks: risk detection, risk-step localization, and intrinsic-failure-type identification. The paper under review states that the current official test snapshot enumerates 536 trajectories and separately declares 400 target-bearing queries. That snapshot mismatch cannot be resolved from the abstract alone and must be checked against the cycle's actual downloaded artifact during the later audit. The paper does not incorrectly call the 136 remaining test records “safe” in reader-facing text; it calls the MAP subset target-bearing, which is safer.

The [TraceElephant primary paper](https://arxiv.org/html/2604.22708) defines a decisive failure step as the point where failure becomes inevitable under role- and recoverability-aware responsibility, releases 220 failed traces from three systems, and uses agent-level and step-level accuracy for its native attribution experiments. It evaluates full-trace LLM/agentic methods and shows that input context materially improves step attribution. AgentProf's use of the released decisive step as a relevant item is construct-aligned, but again the MAP ranking view is a derived AgentProf protocol rather than the benchmark's official metric.

**Verdict:** the paper should continue to call AP/MAP a standard ranking metric, but must not imply that the source benchmarks prescribed this exact ranking protocol. The present evaluation wording does not make that false claim. The benchmark-specific Work measures and the atomic-score boundary help keep the interpretation honest.

### 3. Cross-run semantic aggregation already exists; AgentProf's distinction is narrower but still substantive

The [LangSmith Insights official documentation](https://docs.langchain.com/langsmith/insights) says the product analyzes traces to detect usage patterns, agent behaviors, and failure modes without manually reviewing thousands of traces. It builds hierarchical categories and subcategories, attaches error, latency, cost, feedback, and extracted-attribute aggregates, can discover or accept predefined categories, and can reuse discovered categories in later runs. The default sample is capped at 1,000 traces.

The [Datadog Patterns official documentation](https://docs.datadoghq.com/llm_observability/monitoring/patterns/) is even closer to the paper's motivating decision: it summarizes and clusters production interactions, assigns each interaction to one topic, builds a parent-child topic hierarchy, reports volume/cost/error metrics, and explicitly says the taxonomy lets teams prioritize fixes instead of debugging trace by trace. A run processes at most 10,000 sampled interactions. Datadog's [cost documentation](https://docs.datadoghq.com/llm_observability/monitoring/cost/) also supports trace- and span-level cost breakdowns across applications.

The [NVIDIA NeMo Agent Toolkit profiler documentation](https://docs.nvidia.com/nemo/agent-toolkit/latest/workflows/evaluate.html) describes per-invocation token/time collection, aggregate workflow metrics, nested call profiling, bottleneck and concurrency analysis, and offline reports over evaluation runs. It is an actual agent-workflow profiler, though it follows instrumented call/workflow structure rather than deriving selectable semantic-responsibility projections over heterogeneous histories and system effects.

These sources mean the broad proposition “existing agent observability is only single-trace debugging” would be a strawman. The paper avoids that exact false statement in its updated Introduction: it acknowledges cross-trace hierarchies and metrics, then claims they lack the particular combination of source-linked additive system effects and selectable pprof-compatible operation-stack projections. That narrower distinction is supported by the opened docs:

- LangSmith and Datadog categorize whole traces/interactions, not a uniform cross-layer operation stream carrying source-linked file/process/network effects;
- their hierarchy is generated for a report, not exposed as an arbitrary query-time ordered field projection over conserved additive weights;
- NeMo profiles nested instrumented workflow/call paths, not semantic responsibility across heterogeneous offline histories.

The novelty risk remains high because a skeptical reviewer may see AgentProf as an open, source-linked, pprof-shaped unification of capabilities that products already approximate, rather than a wholly missing analysis category. The paper needs a deeper closest-work comparison and ideally an external baseline or case showing a decision that the product-style trace/topic hierarchy cannot express. This is a broader next-cycle issue, not evidence that Step 0033's MAP reanalysis is invalid.

### 4. pprof provides labels and pseudo-frames, so AgentProf must claim the semantic construction—not generic labeled profiles

The [Google pprof documentation](https://github.com/google/pprof/blob/main/doc/README.md) says sample tags are additional dimensions for filtering and breakdown, call graphs visualize tag pseudo-nodes, and `-tagroot`/`-tagleaf` can promote a selected tag value to pseudo-frames. It also supports merging compatible profiles.

The paper explicitly acknowledges this in Background. Therefore the contribution cannot be “pprof can contain semantic labels” or “labels can become frames.” The credible novelty is the operation model, source/effect linkage, field derivation, arbitrary ordered multi-field operation stacks, and the evaluation of those profiles on agent decisions. The current text mostly observes this boundary, but Related Work is too compressed to make it reviewer-proof.

### 5. Strong diagnostic systems are expected adjacent baselines, not interchangeable replacements

The [AgentRx primary page](https://arxiv.org/abs/2602.02475) describes a domain-agnostic LLM/constraint framework that localizes the critical failure step and category in 115 failed trajectories across three domains. It produces an auditable validation log and compares against diagnostic baselines.

The [TELBench/DRIFT primary paper](https://arxiv.org/html/2606.02060) evaluates 1,000 verified deep-research trajectories using first-error accuracy and macro precision/recall/F1. DRIFT builds a claim ledger, checks support, and traces dependencies; it substantially outperforms bare full-trajectory prompting and generic Codex/Claude Code auditing. This is a much stronger *diagnosis* baseline than raw grouping when the task is to find erroneous spans from content.

The [AgentDiagnose EMNLP 2025 system paper](https://aclanthology.org/2025.emnlp-demos.15/) provides trajectory-level competency metrics and semantic visualizations, evaluates correlation with human annotations, and uses its scores to filter a 46K-trajectory training corpus. It is not cited in the current paper despite being adjacent in name, goal, and population analysis.

These works do not invalidate AgentProf's profiling goal. They read and reason over trajectory content to diagnose individual failures, whereas AgentProf aims to aggregate recurring semantic responsibility and additive resources across runs. But they establish two reviewer expectations:

1. the paper must not equate semantic grouping with root-cause diagnosis;
2. if RQ2 is presented as competitive failure localization rather than “problem correspondence of an already-built profile,” a learned/agentic diagnosis method is a required stronger baseline.

The current RQ2 answer is carefully bounded to matched raw-action grouping, prioritization, and correspondence; it explicitly avoids universal dominance and human-utility claims. Thus absence of DRIFT/AgentRx in the Step 0033 MAP table is not a protocol blocker. A future decisive experiment could instead test complementarity: use a fixed strong diagnostic score as the atomic signal and ask whether semantic profile aggregation improves cross-run triage under the same score budget.

### 6. The challenged belief is real as a workflow gap, but not as an absolute product-capability claim

The primary sources collectively show that:

- trace/span trees remain the native representation in OpenTelemetry and product trace explorers;
- current products recognize that developers need cross-trace categories and population summaries;
- direct diagnosis systems reason over complete trajectories and localize steps;
- workflow profilers aggregate call-path latency/tokens.

So the belief worth challenging is not “nobody aggregates agent traces” or “debugging is the only existing workflow.” It is:

> execution-local call/span hierarchy should not be the sole responsibility hierarchy for population-level agent observability.

That remains plausible and important. AgentProf's simple principle is strongest when it explains how the same additive operations can support multiple responsibility projections, not when it claims categorical absence of adjacent functionality.

### 7. AAAI submission readiness: the current PDF has a concrete overlength defect

The [official AAAI-27 page](https://aaai.org/conference/aaai/aaai-27/) confirms the 2027 conference, official author kit, anonymous review timeline, and July 2026 deadlines. The author-kit endpoint was not retrievable through the browser, so I used official recent main-track instructions only as page-limit precedent: the [AAAI-26 main-track call](https://aaai.org/conference/aaai/aaai-26/main-technical-track-call/) specifies up to seven pages of technical content plus additional pages solely for references, mandatory reproducibility checklist, and optional supplementary material that reviewers need not read. The bundled `aaai2027` source confirms the current paper uses the official 2027 submission style, US letter, and anonymous mode.

The PDF has nine pages, but page 8 begins with the continuation of Related Work and then the Conclusion before references start. Therefore it is **not currently a seven-content-page plus reference-only-pages manuscript**. This is not a speculative formatting preference: the rendered artifact shows technical content beyond page 7. Step 0033's expanded RQ2 section likely contributed to the spill, so this is a Step 0033 repair-WRITE must-fix before outer PASS. The repair must use prose/table economy, not prohibited style or spacing tricks.

The PDF is otherwise US-letter, anonymous, unencrypted, and uses embedded Type 1 fonts. It has exactly seven mostly technical pages plus two pages containing references, but the first part of page 8 must be pulled back to page 7.

## Search-induced changes to the blind attack map

| Blind hypothesis | Source-grounded update |
|---|---|
| MAP may be nonstandard | Rejected. Non-interpolated AP and arithmetic-mean MAP are standard. The scientific issue is query conditioning and precise language. |
| Product hierarchy may be only superficial | Strengthened novelty concern. LangSmith and Datadog already perform cross-trace hierarchical categorization with error/cost/latency aggregates and prioritization language. AgentProf's remaining distinction is source-linked additive operation effects plus selectable pprof projections. |
| NeMo may be merely tracing | Rejected. NeMo explicitly calls its component a profiler and performs nested call/bottleneck aggregation. It remains structurally call/workflow based. |
| Raw action may be enough as RQ2 baseline | Adequate for the narrow matched grouping effect, not for a universal localization claim. AgentRx/DRIFT are stronger adjacent diagnostic systems. |
| TraceElephant is a generic mistake label | Refined. It uses role- and recoverability-aware decisive failure steps, a meaningful developer-facing target. |
| Nine pages likely fit AAAI | Rejected. Page 8 contains technical prose before references, creating a concrete overlength defect. |

## Paper and claim impact

The external evidence does **not** justify shrinking the thesis. It does require precise novelty: selectable semantic responsibility over source-linked additive operations, not the existence of cross-run grouping itself. The strongest source-grounded reject argument is now:

> Current products already hierarchically cluster traces, aggregate cost/errors, and advertise cross-run prioritization, while AgentProf's evidence mainly compares against raw grouping rather than those closest alternatives; therefore the paper has not yet shown that its pprof-compatible semantic projection changes an important decision beyond an engineering unification.

The strongest defense is that those products operate on whole trace/interactions or instrumented call paths, while AgentProf provides arbitrary query-time multi-field projections over one conserved cross-layer operation stream and shows matched ranking gains on complete released operation populations.

For Step 0033 specifically, external sources support the MAP/AP change and retention of Work and atomic boundaries. The remaining Step 0033 must-fixes are presentation/formatting: unambiguous target-bearing wording in the intro/evaluation and technical content spilling to page 8.

## Alternatives and decision

- Keep trajectory MAP as the primary standard RQ2 metric.
- Keep pooled operation AP as a secondary zero-positive/length-sensitive direction check, not as another headline metric.
- Keep HINT Work@80 and Trace Work@50/80 as benchmark-specific inspection diagnostics.
- Keep the atomic-score comparison because it states when aggregation does and does not dominate.
- Do not add nDCG, Recall@K, or more composite metrics merely for breadth.
- In a later research cycle, prefer a single high-value complementarity experiment or closest-product comparison over another benchmark swap.
- Repair the page-8 spill through concise writing/table layout only.

## Tree, search, and memory implications

- The standard-metric search branch is closed positively.
- The closest-product branch remains open and likely merits a dedicated literature/experimental comparison in a future outer cycle.
- AgentDiagnose is a concrete missing citation candidate for the future related-work map.
- The stronger-diagnosis branch suggests a fixed-score complementarity experiment, not replacement of the profiling thesis.
- No project-memory edit is authorized; the final cycle audit may propose a durable instruction to check rendered page allocation after any evidence table is added.

## Completion assessment, uncertainty, and next node

**External-search completion:** complete for Step 0033's metric/protocol question and targeted for the major novelty/baseline branches.
**Uncertainty:** the official AAAI-27 author-kit endpoint was not browser-readable; page-limit judgment uses official recent main-track precedent plus the bundled 2027 style. HINTBench's 629-paper population versus 536 current test snapshot requires artifact-level cycle audit. Product internals are proprietary, so claims about what they do *not* preserve are limited to public official documentation.
**Next node:** reread the complete paper and all figures/tables under this source-grounded attack map, without yet consulting author intent or cycle reports.
