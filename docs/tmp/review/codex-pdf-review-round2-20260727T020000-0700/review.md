# Summary

This paper presents AgentProf, an offline profiler for populations of AI-agent trajectories. Its central claim is that agent observability needs profiling in addition to per-run tracing and debugging. AgentProf preserves a source-native tree of sessions, prompts, LLM calls, tool calls, and additive resource measures; an interchangeable backend recursively annotates source intervals with semantic operation paths; and a deterministic compiler combines those paths with source evidence into a standard pprof profile. The intended benefit is to fold semantically equivalent work across runs while retaining drilldown to individual calls and replaying the same hierarchy under measures such as operation count and tokens.

The paper is unusually broad for a systems-for-AI submission. It evaluates direct Agent annotation on 405 CodeTraceBench trajectories, recurrence and other backends on several public datasets, profile-assisted localization on three benchmarks, three case studies, and both deterministic and Agent-mediated construction cost. The strongest positive result is the TraceElephant reading experiment: at statistically indistinguishable ranking quality, the semantic skeleton causes a fixed reader to open 53.0% of source content, versus 65.0% for an information-matched raw-action skeleton. The implementation discipline—conserved mass, preserved evidence, and standard pprof output—is also compelling.

However, the central scientific claim is not yet established. The paper does not directly evaluate whether its open-vocabulary operation identities correctly merge equivalent responsibilities and avoid merging different responsibilities across runs. The main CodeTraceBench metrics measure within-trajectory partitions and boundaries and are explicitly unchanged by the name-canonicalization step that creates cross-run identity. Moreover, AgentProf is statistically tied with an information-matched raw-action grouping in the main RQ2 ranking experiment, and the paper’s RQ1 experiment shows that a selected hierarchy changes a visualization under different resource weights, not that semantic attribution is more correct. I therefore view the work as technically substantial and promising, but not yet ready for acceptance at AAAI.

# Strengths

1. **Important and timely problem.** The paper clearly distinguishes population-level profiling questions from single-execution debugging. The sentence “Agent observability needs profiling, not only debugging” is memorable, and the motivating questions about repeated cost, failure, and unsafe effects are relevant to deployed agents.

2. **A clean artifact boundary.** Emitting standard pprof rather than introducing another bespoke dashboard is an excellent design choice. The paper carefully preserves source labels and LLM/tool leaves, enabling drilldown rather than replacing evidence with a semantic summary.

3. **Useful invariants.** The separation among source nodes, annotations, and weighted stacks makes exact conservation of additive measures easy to state and test. Replaying a fixed hierarchy under operation count and token mass is practically useful, even though it is not by itself evidence of semantic correctness.

4. **Broad evaluation and commendable negative-result disclosure.** The paper does not hide several important null results. In particular, it states that the information-matched raw grouping ties the semantic grouping in RQ2, and that a fixed-chain recovery projection is statistically indistinguishable from the recursive profile. This honesty makes the empirical record easier to assess.

5. **End-to-end cost is at least partially reported.** The paper goes beyond the attractive 1.16-second post-annotation number and reports Agent wall time and token consumption for CodeTraceBench and AgentRewardBench. Many papers would omit the dominant semantic-annotation cost.

6. **The profile-guided reading result is genuinely interesting.** On TraceElephant, reducing opened source content from 65.0% to 53.0% relative to an information-matched raw-action skeleton, at statistically indistinguishable MAP, is direct evidence that semantic naming can concentrate attention for one reader and workload.

# Major concerns, ranked

## 1. The paper never validates the cross-run semantic identity on which profiling depends

The central mechanism is not merely segmentation. It is assigning shared identities so that responsibilities recur and fold across executions. The paper says:

> “Equal path prefixes fold across sessions; covered LLM/tool nodes remain below the path, while raw session and prompt IDs remain labels for evidence drilldown.”

It later states:

> “The adopted marks’ name replay maps 3,895 open-vocabulary operation IDs to 783 stable action-first canonical IDs, independently re-expanding all operations from the unchanged marks, preserving the temporal occurrence and adjacent-boundary vectors exactly, and leaving no adjacent display-path collision.”

This wording reveals the key evaluation gap. Table 2 evaluates a leaf partition and adjacent transitions:

> “Ordinary operation-level B3 measures the induced leaf partition, while exact adjacent-boundary F1 measures transition placement.”

Because canonicalization preserves the partition and boundary vectors exactly, these metrics cannot test whether the 3,895-to-783 identity mapping is semantically correct. “Zero adjacent display-path collision” is a structural consistency property, not evidence that equal names mean equal responsibilities across sessions or that different names do not split the same responsibility. The appendix makes the risk explicit:

> “Equal canonical names receive one stable operation ID across sessions.”

An erroneous canonical merge can therefore pool unrelated work, while synonymous names can fragment the very cross-run aggregation that motivates the paper. The closed-label AgentBoard and ASE classifiers do not repair this gap: the paper calls them “evaluation-only” backends, and they do not evaluate the actual direct-Agent open-vocabulary identities used by the main profiles.

This is the most serious issue because correct cross-run identity is the causal link between recursive annotations and population profiling. The authors need an independently annotated cross-run identity benchmark containing both positive pairs (same responsibility expressed differently) and hard negative pairs (similar words but different responsibility), evaluated with cluster/pairwise precision and recall. The test should score the complete annotation-plus-canonicalization pipeline on unseen tasks and agents and report false merges, false splits, model/run stability, and downstream distortion of resource attribution.

## 2. The strongest matched RQ2 control does not support a semantic-hierarchy advantage

The paper’s headline RQ2 gains compare Direct+AgentProf with Direct-only: +.031, +.107, and +.117 MAP. But the relevant matched baseline retains the same evidence under a raw-action prefix, and the paper correctly admits:

> “Candidate-minus-baseline intervals are [-.0003,.0029], [-.0116,.0103], and [-.0247,.0280], so this experiment does not establish that the semantic-operation prefix ranks targets better when both views retain the same source evidence.”

This is not a secondary caveat; it changes the interpretation of the headline result. Direct+AgentProf only refines exact diagnostic-score ties, and a nonsemantic grouping provides the same refinement. The claimed MAP gain therefore supports aggregation plus retained evidence, not the semantic responsibility hierarchy specifically.

The profile-guided TraceElephant study supplies one narrower positive result:

> “Semantic naming’s measured contribution in this regime is attention concentration at equal quality.”

That result is valuable, but it is limited to one benchmark, one unspecified “Grok-family CLI reader,” and one five-group protocol. The signed differential case likewise does not isolate recursion: the recursive recovery score obtains AP .634, while the fixed-chain projection obtains .656, with a recursive-minus-fixed interval of [-.107, .061].

The abstract and contributions should not foreground the three Direct-only MAP gains as evidence for semantic profiling without equally emphasizing that the matched raw grouping ties them. More importantly, the authors need matched downstream comparisons across several workloads and decisions: semantic, raw-action, native-tree, flat, and perhaps randomized-but-size-matched groupings must retain identical source evidence, use identical reader budgets, and be assessed on diagnosis accuracy, evidence opened, latency, and stability. At present, the strongest defensible claim is that semantic naming reduces evidence opened for one reader on TraceElephant.

## 3. RQ1 does not measure improved attribution

The paper explicitly narrows RQ1’s test:

> “RQ1 asks whether semantic profiling improves resource attribution. We test one necessary consequence: whether a fixed semantic hierarchy reveals materially different bottlenecks when the additive resource measure changes.”

Showing that token-weighted and operation-count-weighted views have different widths is expected of any weighted grouping; it does not establish that the semantic grouping attributes resources more correctly. Exact conservation is also necessary but not sufficient: an incorrect hierarchy can conserve every token.

The primary Git example is acknowledged to be post hoc:

> “As a post-hoc organization control, we replay the same 489 source operations and both weights over common project, agent prefixes and call, tool leaves with three middle organizations—native (session, prompt), coarse (action kind, raw action), or semantic.”

The conclusion that only the semantic organization provides one focusable SSH responsibility is plausible, but the responsibility is selected from the same case and has no independent attribution ground truth or user-decision outcome. The 440-session analysis mainly reports high rank correlation between operation-count and token views. That establishes replay stability; it does not establish improved attribution, and the ten tasks with tau-b below .7 are called a “material minority” without an externally defined decision criterion.

RQ1 requires an independent notion of responsibility. For multiple repeated real tasks, authors should define target responsibilities before viewing the profiles, then compare semantic, native, raw-action, and flat views on attribution precision/recall, mass assigned to the target, fragmentation, contamination, or a concrete engineering decision such as identifying the component whose optimization reduces measured cost on rerun. Otherwise, this section should be presented as a capability and motivating case rather than an answer to “improves attribution.”

## 4. The default automatic constructor is only moderately accurate, and the claim that over-segmentation is benign is unsupported

On CodeTraceBench, direct Agent annotation has boundary F1 0.480, with precision 0.389 and recall 0.626. The paper states:

> “The residual boundary error is over-segmentation rather than missed transitions (recall 0.626, precision 0.389), the benign direction for profiling because extra splits subdivide work without merging unrelated responsibilities, as the 0.793 B3 precision confirms.”

Over-segmentation is not generally benign for this paper’s use case. It fragments resource mass, creates excess operation identities, reduces cross-run folding, increases skeleton size, and can make comparisons unstable. A within-trajectory B3 precision of 0.793 does not establish that the resulting cross-run names are correct or useful. Indeed, the need to collapse 3,895 open-vocabulary IDs to 783 canonical IDs suggests that fragmentation is load-bearing rather than harmless.

The model-validation protocol is also too thin for a stochastic Agent backend. The appendix identifies Codex CLI 0.145.0 and `gpt-5.6-sol`, but the PDF does not provide the exact annotation prompt, prompt-development protocol, decoding parameters beyond “default decoding,” or repeated-run variability. A single adopted set of marks does not reveal whether the hierarchy is stable across seeds, model versions, or equivalent source formatting. The separate recurrence, supervised, TF-IDF/K-Means, and closed-label experiments use different datasets, supervision, outputs, and metrics; together they demonstrate backend flexibility, not the reliability of one deployable default.

The authors should report repeated annotation runs, cross-run partition/name stability, a human or expert upper bound, error categories, and the effect of false splits and merges on final profile queries. At least one default backend should be evaluated end to end across multiple held-out task families rather than assembling a positive RQ3 answer from several unrelated backends.

## 5. The RQ2 ranking protocol leaves important validity questions unanswered

First, the candidate can only refine ties:

> “The candidate (Direct+AgentProf) ranks operations lexicographically by (direct diagnostic, Agent+Evidence group score), so it can only refine exact diagnostic-score ties.”

The paper does not report how many queries or operation pairs contain such ties, their group sizes, or sensitivity to the direct diagnostic’s score discretization. Consequently, the large improvements on HINTBench and TraceElephant may reflect unusually coarse native scores rather than a generally useful profile.

Second, the paper excludes every no-target trajectory from the metric:

> “All 522 zero-positive trajectories are consumed for population coverage but excluded from MAP because AP is undefined without a relevant item.”

AP is indeed undefined for no-positive queries, but simply excluding them means the experiment does not measure false alarms, abstention, or the ability to recognize that no faulty operation exists. That omission is important for an observability tool intended for mixed populations. “Consumed for population coverage” is not a scored guarantee.

Third, the sentence

> “Thus the profile adds clear ranking information after a fixed trajectory reader on all three complete workloads”

is too strong. The added group score is derived by aggregating frozen benchmark-judge predictions, and the raw-action grouping performs equivalently. The evidence supports tie refinement by grouped evidence, not specifically semantic profile information.

The authors should report tie prevalence and sensitivity, score zero-positive cases with a metric that supports empty relevance sets, evaluate calibration/false-alarm behavior, and distinguish grouping gains from semantic gains. Calling the workloads “complete” also needs qualification because the appendix says the HINTBench release used here has 536 of the paper’s reported 629 trajectories.

## 6. The practicality claim is dominated by an expensive and incompletely reproducible annotation stage

The abstract and conclusion highlight:

> “After marks are fixed, AgentProf constructs a 27,765-operation profile in 1.16 s.”

The qualification is accurate, but the marks are the hard part. The paper later reports 2,215.858 seconds of active backend time and over 12 million input tokens for 405 CodeTraceBench trajectories. For AgentRewardBench:

> “the fixed automatic backend completes all 12 outcome-blind batches in 3,521.6 s on a fixed two-worker schedule (58.7 minutes; summed worker time 6,661.7 s), consuming 12,039,417 actual input tokens ... and 312,433 output tokens.”

The conclusion nevertheless says the 1.16-second result makes “population profiling practical.” That conclusion is justified only for deterministic replay after annotation. Practical end-to-end use depends on model availability, monetary cost, cache behavior, privacy constraints, incremental update behavior, and annotation stability. The Git population requires 832,544 input tokens for only three sessions, illustrating that workload shape matters.

The paper deserves credit for disclosing these figures, but RQ4 should make total cost—not post-mark serialization—the primary result. It should include cost per source token/operation/session, monetary cost or hardware energy where applicable, incremental-update cost, and an information-matched raw or direct-reader baseline. The unspecified Grok reader and evaluation-only Qwen backends also need exact versions, prompts, and decoding configurations for reproducibility.

## 7. Novelty is argued mainly as a conjunction of features rather than demonstrated against the closest systems

The related-work section names several very close contemporary systems: TraceProbe, Graphectory, Act·onomy, CHIEF, Hodoscope, TraceGraph, Datadog Patterns, and LangSmith Insights. Its main novelty conclusion is:

> “No compared system provides all four.”

The four items are variable-depth responsibility, exact conservation across measures, retained LLM/tool evidence, and pprof output. This is a useful engineering combination, but a feature conjunction is not by itself a non-obvious scientific contribution. The formal folding model is straightforward once annotations exist, while the difficult semantic-identity problem is delegated to backends and, as noted above, not directly validated across runs.

The paper needs either a clearer principle that makes a falsifiable prediction beyond “combine these four properties,” or an empirical head-to-head comparison showing that the missing combination enables decisions the closest systems cannot support under matched evidence and cost. Based only on the PDF, the novelty over the cited process-profile and cross-run graph systems remains uncertain.

# Minor issues

1. Several cross-references are broken in the compiled PDF: “Section measures this case,” “the case previewed in Section .,” and “the responsibility described in Section .” These are submission-readiness defects, not source-level hypotheticals.

2. Figure 3’s caption says “AgentPProf emits only standard pprof,” while the paper and system are named AgentProf.

3. The title emphasizes “Long Horizon AI Agents,” but the paper does not give horizon distributions for the principal 405-trajectory CodeTraceBench result. The long-horizon evidence is concentrated in descriptive private/local case studies.

4. “Complete public workloads” is confusing when the appendix states that the HINTBench snapshot contains 536 of 629 reported trajectories, and the main MAP excludes 522 zero-positive trajectories across workloads.

5. The paper alternates among “semantic operation,” “responsibility,” “tag,” “group,” “canonical ID,” “mark,” and “path.” Their exact relationships are eventually recoverable, but the exposition should distinguish boundary prediction, within-run partitioning, semantic naming, and cross-run identity earlier.

6. The private 42-session development case is not independently auditable. It is useful as an existence demonstration but should not carry scientific weight without a releasable counterpart.

7. The paper lacks a meaningful privacy/security discussion. Source packets contain prompts, responses, commands, and output summaries, and profiles retain drilldown labels. Local agent histories are likely to contain secrets, proprietary code, personal data, or credentials. Threat model, redaction, retention, and access control should be discussed.

8. The paper provides no artifact-availability statement or anonymous supplemental pointer. Given the number of adapters, prompts, scoring rules, and private/public data transformations, reproducibility cannot be assessed from the PDF alone.

9. The abstract foregrounds B3 F1 0.764 but omits the much weaker boundary F1 0.480 and precision 0.389. Since boundaries determine recursive intervals, reporting both would give a more balanced summary.

10. The statement that skeleton-guided drilldown “remains available at any trace length” is mechanically true, but does not show that the semantic skeleton remains accurate or cognitively manageable as trace length and operation vocabulary grow.

# Questions for authors

1. How was the action–object canonicalization map constructed, and what data were viewed while developing it? What independent evidence shows that the 783 stable IDs merge equivalent responsibilities and avoid collisions across sessions?

2. Can you provide a cross-session identity confusion analysis: examples of false merges, synonymous splits, and their effects on token/cost attribution?

3. What exact prompts, decoding settings, model snapshots, and retry logic were used for the Codex, Qwen, and “Grok-family” backends? Will all prompts and generated annotations be released?

4. How stable are direct-Agent annotations across repeated runs, model versions, equivalent serialization orders, and source-preview truncation? Why is one adopted annotation run sufficient?

5. What fraction of RQ2 queries and candidate pairs are affected by exact direct-score ties? Do the MAP gains persist if direct scores are recalibrated, jittered, or replaced by a less quantized diagnostic?

6. How does AgentProf behave on zero-positive trajectories? Can it abstain or return an empty diagnosis, and what are its false-positive and calibration results?

7. Why should over-segmentation be considered benign when the main goal is to fold recurring work across runs? How much resource mass and identity reuse are lost because of excess splits?

8. Can the 53.0%-versus-65.0% evidence-opening result be reproduced with additional readers, humans, and workloads? How sensitive is it to the five-group budget and semantic-name quality?

9. What is the full monetary and wall-clock cost of producing and incrementally updating a profile, including capture, normalization, packet construction, automatic annotation, validation, and replay?

10. Which closest system would be the strongest end-to-end baseline, and what concrete analyst decision can AgentProf support that this baseline cannot when both retain the same source evidence?

11. How are secrets and sensitive source content redacted before model annotation and pprof export, and what data remain recoverable through pprof labels?

# Final assessment

**Weak reject.**

The paper is well motivated, technically substantial, and more transparent than many agent-observability papers. Standard pprof output, exact mass conservation, and source-linked drilldown are sound engineering choices, and the TraceElephant evidence-opening result is promising. Nevertheless, the paper’s central object—correct shared semantic responsibility across runs—is not directly evaluated. Within-run segmentation metrics cannot validate the canonical identities that cause cross-run folding, the matched raw-action baseline ties the semantic hierarchy in the main localization experiment, and RQ1 demonstrates changed organization rather than improved attribution. These are central evidence gaps rather than presentation defects.

The strongest alternative explanation is that retaining source evidence and adding almost any useful grouping/tie aggregation produces most of the observed benefit; semantic recursive identity contributes only the single-workload reduction in evidence opened. The largest currently supported claim is therefore narrower than the paper’s headline: AgentProf is a practical pprof compiler for externally supplied semantic annotations, and one semantic skeleton reduced reader evidence consumption on TraceElephant. A decisive revision would validate open-vocabulary cross-run identity on unseen tasks and show matched downstream benefit over raw/native/randomized groupings on multiple real decisions, while reporting the complete annotation cost.

In research-taste terms, this is **incomplete but promising**. The durable principle may be important, but the experiment that distinguishes semantic profiling from generic grouped evidence is not yet complete.

# New problems not previously visible

The following issues became apparent on this careful PDF-only pass:

1. **The canonicalization step is mathematically invisible to the headline CodeTraceBench metrics.** The paper says canonicalization preserves the temporal occurrence and boundary vectors exactly, while B3 and boundary F1 score only those structures. Thus the reported 0.764/0.480 cannot validate the 3,895-to-783 cross-run identity mapping.

2. **The RQ4 microbenchmark appears to use a different hierarchy from the main recursive Agent profile.** It times `project, agent, task, phase, op, tool, status` versus `project, agent, action, status`, whereas the design’s main emitted stack is agent → semantic operations → LLM/tool evidence with session/prompt IDs as labels. The paper should show that the 1.16-second path measures the current product representation and not a legacy field-stack configuration.

3. **The PDF contains three visibly unresolved section references and one system-name typo.** These defects are present in the compiled submission itself.

4. **The “complete workload” wording conflicts with the appendix and metric coverage.** HINTBench uses 536 of 629 reported trajectories, and 522 zero-positive trajectories are not scored by MAP.

5. **The five-group reader budget is saturated on 99.5% of TraceElephant queries.** This makes the statement that misses were “not a budget cutoff” difficult to accept without a larger-budget sensitivity analysis: an ordered reader limited to five outputs may omit a target precisely because additional choices were disallowed.

6. **The private development case may actually expose a limitation.** The paper reports that 70.4% of token mass remains at mandatory prompt depth and that the largest semantic token path contains only 1.735%. This suggests that the recursive semantic layer leaves most resource mass coarsely attributed in this real long-horizon population, yet the paper does not analyze that as a failure mode.

7. **No privacy boundary is specified for model-visible trajectory content or pprof drilldown labels.** This is especially concerning for a profiler that reads local coding-agent histories and commands.
