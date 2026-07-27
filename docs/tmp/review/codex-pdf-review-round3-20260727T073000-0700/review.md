# Review of “AgentProf: Semantic Profiler for Long Horizon AI Agents”

## Summary

This paper argues that “Agent observability needs profiling, not only debugging.” Its central idea is to replace unstable per-run prompt and action identities with recursively annotated semantic responsibilities, compose those responsibilities with native LLM/tool evidence, attach additive measures such as tokens or file effects, and fold equal paths across trajectories into a standard pprof profile. AgentProf implements this abstraction as an offline Rust pipeline with interchangeable Agent, LLM, recurrence, and rule-based annotation backends.

The evaluation is unusually broad. It includes semantic-structure agreement on CodeTraceBench and OSWorld-Human, diagnostic ranking on AgentProcessBench, HINTBench, and TraceElephant, a model-guided evidence-reading experiment, several population case studies, and construction-cost measurements. The plain-language principle I take from the paper is: population profiling of agents requires a shared semantic responsibility stack that preserves both additive resource mass and drill-down evidence.

I find the problem important, the abstraction coherent, and the standard-profile output attractive. However, the evidence does not yet establish the paper’s central claims. RQ1 demonstrates that changing an additive measure can change widths in an already constructed hierarchy, but not that the resulting attribution is correct or better. RQ2’s strongest controlled comparison explicitly finds no ranking advantage for the semantic prefix over an information-matched raw-action hierarchy. RQ3 largely evaluates partitions and boundaries rather than the correctness and cross-run stability of the open-vocabulary semantic identities that make the profile possible. The long-horizon, practical-cost, privacy, and reproducibility claims also have substantial unresolved problems.

## Strengths

1. **Important and well-motivated problem.** Cross-run understanding of agent cost, failure, and behavior is a real gap between trace inspection and population analysis. The profiling analogy is memorable and potentially useful beyond this particular artifact.

2. **Clean core abstraction.** The separation among an ordered source tree, nested semantic annotations, and weighted operation stacks is conceptually sound. Keeping raw session/prompt identities as labels while folding shared semantic paths is a sensible way to preserve aggregation and drilldown simultaneously.

3. **Conservation and interoperability are treated as invariants.** The paper is precise that changing the resource measure should change widths but not hierarchy, names, or boundaries. Emitting one standard pprof artifact rather than inventing a new visualization stack is a strong systems-design choice.

4. **The authors report several unfavorable or null results rather than hiding them.** In particular, the paper discloses the information-matched raw-action tie in RQ2, the lack of superiority over the fixed recovery indicator, the modest action-label macro-F1, and the dominance of annotation cost over deterministic materialization.

5. **Breadth of workloads and metrics.** The submission tests several distinct aspects of the system across coding, web, GUI, and local-development histories, and it reports clustered bootstrap intervals for several key comparisons.

6. **Good attention to source evidence.** Retaining LLM/tool leaves and exact identifiers below semantic frames makes the resulting aggregate auditable in a way that a summary-only taxonomy would not be.

## Major concerns, ranked

### 1. The evaluation does not establish that semantic profiling improves resource attribution or diagnosis

The paper itself narrows RQ1 substantially:

> “RQ1 asks whether semantic profiling improves resource attribution. We test one necessary consequence: whether a fixed semantic hierarchy reveals materially different bottlenecks when the additive resource measure changes.”

Showing that operation count, time, and token weights produce different widths is a capability test of additive replay. It is not evidence that the semantic hierarchy attributes responsibility correctly, that it is better than another hierarchy, or that it changes a sound engineering decision. The main Git example has only three executions of one task, the hierarchy has already been selected, and the conclusion that authentication is the important responsibility depends on the same semantic annotation whose validity is at issue. Exact conservation is valuable, but conservation would also hold for arbitrary nested groups.

RQ2 does not rescue this claim. The strongest information-matched control yields:

> “Candidate-minus-baseline intervals are [-.0003,.0029], [-.0116,.0103], and [-.0247,.0280], so this experiment does not establish that the semantic-operation prefix ranks targets better when both views retain the same source evidence.”

Thus, the reported MAP gains over Direct-only arise from adding group/evidence refinement, not specifically from semantic operation names or hierarchy. The TraceElephant reader experiment finds an efficiency difference at equal ranking quality, but only for one model reader and without a human diagnosis-time or decision-quality outcome. The paper’s most compelling scientific claim is specifically about semantic responsibility, yet its controlled evidence supports grouping plus retained evidence more clearly than semantics.

This is the principal acceptance blocker. A convincing evaluation should compare target-blind semantic profiles against strong information-matched native, action, embedding-cluster, and flat-summary alternatives on held-out populations. It should measure attribution correctness and downstream developer outcomes: fault/resource localization, diagnosis time, evidence opened, and decision quality. The evaluation should also include cases where different hierarchies lead to demonstrably different and independently validated conclusions.

### 2. RQ3 does not validate the core open-vocabulary semantic identities

The central mechanism requires different trajectories to receive the same short responsibility name and appropriate recursive boundaries. Yet the paper explicitly evaluates heterogeneous backend outputs using different constructs:

> “A backend output is evaluated at the level it predicts: literal names, permutation-invariant leaf partitions, or adjacent interval boundaries.”

For the primary direct Agent backend, B3 and boundary metrics ignore whether an open-vocabulary name is semantically correct, whether equivalent responsibilities receive the same name across sessions, and whether distinct responsibilities are incorrectly merged. The separately reported literal-label results use closed-label Qwen backends on AgentBoard task families and ASE action labels; they do not validate the names produced by the recursive Agent backend.

The quantitative result is also not strong enough to support the paper’s unqualified evaluation-chain statement that “semantic responsibility can be recovered accurately”:

> “Direct Agent annotation reaches 0.764 B3 F1, improving over recurrence by 0.101 … Its boundary F1 is 0.480 versus 0.266 for recurrence.”

A boundary F1 of 0.480, with precision 0.389, implies substantial over-segmentation. The paper treats the resulting pure subsets as relatively benign, but fragmentation is directly harmful to D2: extra semantic splits can prevent shared work from folding across runs. B3 precision therefore does not establish the cross-run identity property the system needs.

Finally, the most consequential identity transformation is under-specified:

> “Before folding, one fixed source-only action–object map canonicalizes the Agent annotation’s display identity.”

This map reduces 3,895 open-vocabulary IDs to 783 canonical IDs, but the PDF does not explain how the map was created, how much human knowledge it contains, how it behaves on unseen domains, or how results change without it. The paper needs human evaluation of name correctness and cross-run equivalence, inter-annotator agreement for the intended semantic construct, held-out-domain canonicalization tests, and an ablation separating raw Agent names, canonicalization, boundary repair, and hierarchy construction.

### 3. The “long horizon” claim is supported mainly by an unvalidated self-profile, and the annotation protocol conflicts with the context-length argument

The paper acknowledges:

> “Per-workload mean operations per trajectory are 8.5 (AgentProcessBench), 13.9 (OSWorld-Human), 24.0 (HINTBench), 27.1 (TraceElephant), and 51.5 (CodeTraceBench), so benchmark trajectories are short-to-medium horizon while the 42-session workstation population—whose longest sessions span tens of hours—supplies the long-horizon regime.”

The long-horizon evidence is therefore mostly 42 sessions from the authors’ own workstation, with no gold hierarchy, no independent correctness assessment, and only descriptive profile observations. Duration in hours is not by itself evidence of semantic complexity or that the method remains accurate as trajectory length grows.

There is also an unresolved mechanism-level tension:

> “The evaluated Agent backend reads each trajectory’s complete source-only packet once and directly emits sparse complete-path marks at the transition points it identifies, naming every enclosing responsibility.”

but later:

> “A per-query full read is bounded by the model context window: populations such as the 4,558,192-token repeated Git task cannot be read whole, whereas skeleton-guided drilldown remains available at any trace length.”

The hierarchy can only guide beyond-context drilldown after it has been constructed. The primary constructor itself reads a complete, preview-truncated packet in one call. The PDF does not report packet-length distributions, context limits, truncation rates, omitted semantic evidence, or annotation quality as horizon grows. “Available at any trace length” is therefore not established.

The title-level claim needs a real long-horizon evaluation with independently annotated responsibilities, length-stratified quality, explicit context accounting, and comparisons among one-shot, chunked, hierarchical, and recurrence-based annotation. At least one dataset should be independent of the authors and should include histories that genuinely exceed the annotator’s context budget before compression.

### 4. The practical-cost headline emphasizes post-annotation materialization while the semantic backend dominates end-to-end cost

The abstract and conclusion foreground:

> “On four public workloads, after marks are fixed, AgentProf constructs a 27,765-operation profile in 1.16 s.”

The qualification is present, but this is not the cost of constructing the semantic profile from trajectories. The end-to-end numbers are much larger:

> “On the complete 440-session AgentRewardBench population, the fixed automatic backend completes all 12 outcome-blind batches in 3,521.6 s on a fixed two-worker schedule (58.7 minutes; summed worker time 6,661.7 s), consuming 12,039,417 actual input tokens (10,929,408 reported cached) and 312,433 output tokens—27,362 input and 710 output tokens per session.”

The paper later concedes that “construction cost is dominated by the automatic backend.” The 42-session self-profile additionally consumes more than 15 million reported input tokens and has a 44.6-minute annotation critical path. These costs may still be worthwhile for offline analysis, but they do not support the broad statement that population profiling is practical “alongside per-run debugging” without a budget model, dollar cost, update/incremental cost, and comparison against simpler baselines.

RQ4 should lead with end-to-end cost, not serializer throughput. It should separate initial indexing from incremental updates, report distributions across trajectory lengths, include annotation-service cost and failure/retry rates, and compare the quality/cost frontier of Agent, local-model, recurrence, and raw-action backends.

### 5. The LLM-based evaluation protocols are not reproducible or robust enough

The primary constructor uses a single proprietary model configuration:

> “The direct annotation backend is the OpenAI Codex CLI (version 0.145.0, model gpt-5.6-sol, default decoding, sandboxed non-interactive mode): one call per trajectory over the source-only packet, at most one format retry, and independent workers with no shared state.”

The PDF gives a compact interface description but not the exact full prompt, all preprocessing details, a stability analysis, or repeated runs for this central backend. The TraceElephant reading experiment is even less specified: it names only a “fixed external Grok-family CLI reader,” without an exact model/version, decoding configuration, complete prompts, or replicate variability. A single model reader may prefer concise semantic labels because of its own training or prompting, so the 53% versus 65% evidence-opening result may not generalize to people or other models.

For an AAAI empirical submission, the paper needs executable prompts/configurations, model/API dates and versions, repeated runs or a deterministic justification, cross-model validation, order/position controls for skeleton presentation, and preferably human calibration for the reader experiment. The primary annotation result should also report run-to-run boundary and identity stability, not only accuracy from one materialized run.

### 6. RQ2 omits negative-query behavior and uses a potentially distorting pair-occurrence population

The localization evaluation states:

> “All 522 zero-positive trajectories are consumed for population coverage but excluded from MAP because AP is undefined without a relevant item.”

This is mathematically understandable for AP, but merely “consuming” these trajectories does not evaluate false alarms, specificity, calibration, or whether the profiler sends a developer toward a nonexistent problem. In deployment, no-problem histories are part of the population, and 522 is too large a subset to leave without an appropriate negative-query metric.

The differential case also reports that 202 successful and 238 unsuccessful sessions are reused across 338 bad–good pairs and are “pair-occurrence weighted.” This makes some source sessions contribute repeatedly. The resulting occurrence counts and percentages are not an independent population estimate, and the pairing multiplicity may drive apparent success/failure differences. The paper should report trajectory-weighted and task-weighted alternatives, describe the pairing rule, provide cluster-aware uncertainty, and show sensitivity to repeated-session weighting.

### 7. The privacy claim appears inconsistent with the evaluated default backend

The implementation section makes an absolute claim:

> “Privacy. AgentProf runs entirely offline on local histories; profiles carry only short semantic names, bounded text previews, and numeric measures as labels; no trajectory content leaves the machine unless the user shares the profile, and packet previews are truncated as disclosed in the appendix.”

However, the evaluated direct annotation backend is the OpenAI Codex CLI with a named hosted model and millions of reported input tokens. The PDF never says this model runs locally. On the paper’s own description, source-visible prompts, commands, and output summaries are supplied to that backend. Unless the authors can establish that this configuration executes locally, the statement that no trajectory content leaves the machine is false. Sandboxed execution does not imply local model inference.

The paper must distinguish the local parsing/materialization path from optional remote annotation, describe exactly what data each backend receives, state retention and privacy assumptions, and revise the privacy claim. A truly offline local backend could support the original claim, but its quality/cost should then be evaluated as the relevant configuration.

### 8. Novelty is argued as a conjunction of features rather than as a demonstrated new technical capability

The related-work argument culminates in:

> “No compared system provides all four.”

Those four properties—variable-depth semantic categories, conserved measures, retained evidence, and pprof output—form an appealing product combination, but absence of the exact conjunction does not by itself establish a substantial AI contribution. From the PDF alone, the mechanism may be viewed as LLM segmentation/canonicalization plus a standard hierarchical aggregation format. The paper does not experimentally compare AgentProf with the closest cross-trace hierarchy or graph systems, nor does it isolate a new prediction that would be impossible with those systems after adding evidence links and additive weights.

The paper should sharpen what is technically non-obvious about semantic operation stacks, distinguish abstraction novelty from implementation interoperability, and provide a capability table grounded in precise inputs, outputs, identity semantics, and aggregation guarantees. More importantly, it should demonstrate an outcome that depends on the proposed recursive semantic responsibility abstraction and cannot be reproduced by a simpler grouping baseline.

## Minor issues

1. The motivation includes identifying “which behavioral patterns trigger unsafe system effects,” but the evaluation does not test unsafe-effect detection, causal triggering, or safety outcomes. Exact conservation of file/process/network events is not equivalent to safety attribution.

2. “Real task” is used repeatedly, but several cases are benchmark trajectories, author-generated executions, or self-profiled development histories. The paper should distinguish public benchmark traces, naturally occurring production traces, and author-run case studies.

3. The elapsed-time measure in RQ1 is called “defined” but its definition is not visible in the main evaluation. Concurrency, idle time, and overlapping spans can make elapsed-time additivity nontrivial.

4. The interpretation that ten of 77 tasks below Kendall’s tau-b 0.7 constitute a “material minority” is plausible but post hoc; no decision threshold or independent consequence is specified.

5. Table 1 mixes a benchmark-native direct score with profile-derived group refinement. More explanation is needed to show information and computation parity across conditions, especially because the TraceElephant direct diagnostic reads the reference answer.

6. The CodeTraceBench claim uses “human-verified contiguous stages,” but the PDF does not report the annotator count, annotation protocol, disagreements, or inter-annotator reliability.

7. Several appendix experiments are extremely small, notably nine Mind2Web sessions with 49 operations. These should not carry generalization weight.

8. The action-label result of 0.498 macro-F1 is much weaker than the prose’s broad “tag accuracy” framing. Per-class scores and confusion patterns would be useful.

9. The canonicalizer’s “minimum source words needed” rule is not formal enough to reproduce and may create dataset-specific lexical identities.

10. The related-work section is dense with very recent systems but offers no compact comparison table. This makes it difficult to assess which difference is semantic, representational, operational, or merely an output-format choice.

11. The profile can carry bounded text previews and exact drilldown labels. The submission should discuss profile-file access control and re-identification risk rather than equating local generation with privacy.

12. The paper would benefit from a short, explicit failure-mode taxonomy: wrong boundary, wrong parent, synonymous-name fragmentation, polysemous-name merging, missing evidence, and truncation-induced errors have different consequences.

## Questions for authors

1. What independent ground truth would make a resource attribution “correct,” and where does the current evaluation test correctness rather than conservation or visual usefulness?

2. How much of the three localization gains remains if semantic names are replaced by opaque group IDs while boundaries and evidence leaves are kept fixed?

3. How was the action–object canonicalization map created? Did any author inspect test outputs, gold stages, outcomes, or benchmark labels while designing it?

4. What are the exact synonym-fragmentation and false-merge rates of canonical identities across held-out sessions and domains?

5. What are the input-length and truncation distributions for the one-shot Agent packets? How many long trajectories exceed the backend context before and after preview truncation?

6. Why is the profile-guided reader identified only as a Grok “family” model? Will the exact prompt, version, decoding settings, responses, and repeated-run variance be released?

7. Does the OpenAI Codex annotation configuration transmit packet content off machine? If so, how should the offline/privacy claim be interpreted?

8. What are the end-to-end dollar and wall-clock costs for creating and incrementally updating the 27,765-operation profile?

9. How do the RQ2 results change when zero-positive queries are scored with a metric that penalizes false alarms?

10. How do the differential-profile conclusions change under one-vote-per-trajectory and one-vote-per-task weighting rather than pair-occurrence weighting?

11. Why should over-segmentation be considered benign when cross-run folding depends on shared identity? Can the authors quantify the resource mass fragmented by false boundaries?

12. Which single result would fail if AgentProf used a flat information-matched raw-action grouping instead of recursive semantic responsibility?

## Final assessment

**Weak reject.**

AgentProf is incomplete-but-promising rather than complicated-but-shallow: the simple principle is useful, the pprof-based artifact is coherent, and the paper is commendably transparent about null results. Nevertheless, the current evaluation does not establish that the semantic hierarchy—rather than grouping, retained evidence, or an LLM reader—improves attribution or diagnosis. The open-vocabulary identity mechanism is insufficiently validated, the long-horizon and end-to-end practicality claims are not supported at the title/headline level, and the privacy statement appears inconsistent with the evaluated backend.

The strongest alternative explanation for the results is that any target-blind grouping with source evidence can refine tied diagnostic scores, while concise labels help one particular LLM allocate attention; the information-matched raw-action tie directly supports this explanation. The largest defensible claim is that semantic operation stacks are a promising interoperable representation for population-level agent histories, not yet that they provide accurate or superior resource attribution in long-horizon agents.

I would reconsider after a focused revision that validates cross-run semantic identity, demonstrates a semantic-specific downstream advantage over information-matched baselines, evaluates genuinely long histories under explicit context limits, and reports end-to-end cost and privacy accurately.

## New problems not previously visible in this PDF

Because I was instructed to review this PDF in isolation and not read prior reviews, I cannot determine which findings are historically new relative to earlier rounds. The following problems became visible through cross-reading distant sections of this PDF and may be easy to miss when considering individual results:

1. The absolute offline/privacy statement conflicts with the later disclosure that the principal annotation backend is OpenAI Codex CLI with millions of input tokens.

2. The “available at any trace length” claim concerns drilldown after construction, while the evaluated hierarchy constructor itself requires one complete, preview-truncated packet per trajectory.

3. The paper describes over-segmentation as mostly preserving purity, but false splits directly undermine the shared-identity folding property that motivates semantic profiling.

4. The 1.16-second headline measures deterministic materialization after semantic marks are fixed, while the automatic backend takes tens of minutes and millions of tokens.

5. The population-scale signed comparison reuses sessions under pair-occurrence weighting, so its visual mass can reflect pairing multiplicity rather than the prevalence of responsibilities across independent trajectories.

6. The core open-vocabulary backend is never evaluated for literal semantic-name correctness; the literal-label numbers come from separate closed-label backends on different tasks.
