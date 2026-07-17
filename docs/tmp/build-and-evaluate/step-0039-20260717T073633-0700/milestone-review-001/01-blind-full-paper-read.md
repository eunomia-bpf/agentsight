# Milestone Review 001 — Blind Full-Paper Read

## Node identity

- **Timestamp:** 2026-07-17T07:41:09-0700
- **Parent node:** `step-0039-20260717T073633-0700`
- **Gate:** REVIEW
- **Venue under review:** AAAI-27 Main Technical Track
- **Artifact:** `docs/paper/main.tex` and the rendered `docs/paper/main.pdf`
- **Review mode:** whole-paper read before the Step 0039 external novelty search and before reading prior review verdicts
- **Mutation policy:** read-only for the paper; this report records observations and routes questions but does not revise the manuscript

## Objective

Read the complete paper as an unprimed program-committee reviewer would, reconstruct its thesis and evidence chain, inspect every rendered figure and table, and identify the smallest set of paper-level objections that could determine an AAAI accept/reject decision. This node deliberately does not select a new experiment: external closest-work verification and an independent reviewer must first test whether the apparent gaps are real.

## Review provenance and contamination disclosure

The reviewer read the current abstract, introduction, background, design, implementation, all four RQ subsections, limitations, related work, conclusion, bibliography, architecture source, all three flame-graph images, and rendered pages 1--7. The PDF is nine US-Letter pages; main content ends on page 7 and pages 8--9 contain references only.

Perfect blindness is impossible because the root agent has participated in earlier project cycles. To reduce anchoring, this report was written from the current paper alone, before opening Step 0039 literature notes or any previous reviewer report. Earlier numeric results may be familiar; the judgments below were re-derived from how the current paper presents them. This limitation is material and is why the next node requires an independent whole-paper reviewer.

## Reconstructed paper in one sentence

Agent observability needs profiling, not only debugging: AgentProf turns heterogeneous agent events and additive effects into uniform operations, derives stable semantic fields, constructs selectable cross-run operation stacks without runtime nesting, and folds them into pprof-compatible profiles for resource attribution and problem localization.

## What the paper asks the reader to believe

The paper advances a larger systems-and-AI claim rather than merely a visualization claim:

1. Single-run tracing and debugging do not provide the population-level aggregation needed to understand recurring agent responsibilities, problems, and costs.
2. Traditional profiling transfers to agents if code identities and runtime call stacks are replaced by stable semantic tags and query-time operation stacks.
3. A uniform additive operation model is sufficient to connect high-level agent intent to low-level effects and to expose multiple profiling views over the same corpus.
4. The resulting semantic organization is not cosmetic: it improves attribution agreement and problem ranking relative to raw action identity, while tags/groups can be recovered with useful accuracy and the profile can be built at practical cost.

This is a coherent and potentially important thesis. The paper does not need to retreat to a narrower claim such as “a convenient pprof exporter.” Its acceptance depends on showing that the semantic profiling abstraction changes an important AI-agent analysis capability beyond what existing trace aggregation, grouping, and local diagnosis already provide.

## Strongest elements on a blind read

### 1. The thesis is simple, memorable, and larger than the implementation

“Agent observability needs profiling, not only debugging” challenges the current per-run tracing/debugging default and transfers a durable systems concept to an emerging AI setting. The abstract and introduction maintain this line consistently. The operation-stack model is understandable without a large vocabulary: operations carry fields and additive measures; a selected field sequence becomes a stack; identical stacks are folded.

### 2. The representation has a real systems invariant

Every operation enters a selectable view, additive weights are conserved, and the same event corpus can be reprojected by task, phase, action, status, or resource measure. This is more principled than a collection of disconnected dashboards. The separation between uniform operations, field derivation, stack construction, and folding is also implementation-friendly.

### 3. The evaluation uses real released populations and mostly construct-matched standard metrics

The paper evaluates a real Codex capture suite, all reconstructable CodeTraceBench failures, complete public localization workloads, session-held-out OSWorld-Human groups, literal task/action tags, and complete public cost workloads. AP/MAP, macro-F1, accuracy, V-measure, ordinary B-cubed, and boundary precision/recall/F1 are recognizable metrics. Token-weighted B-cubed is explicitly secondary rather than presented as a universal standard.

### 4. The paper is unusually candid about evidence boundaries

It identifies development versus untouched evidence, reports that phase-only matches recurrence on CodeTraceBench, distinguishes label-free from reference-calibrated construction, and limits RQ4 to offline profile construction. This honesty improves credibility and need not weaken the central thesis if the positive claim is tied to the correct construct.

### 5. The paper is compact and readable

The seven-page body is dense but navigable. All four RQs are explicit and appear in the promised order: attribution, problem localization, tag accuracy, and cost. The current AAAI page boundary is visually correct. There is no obvious terminology explosion in the main model.

## Evidence-chain reconstruction by RQ

### RQ1 — Resource attribution

The capture-and-join experiment establishes scoped low-level correctness: 1,520/1,574 in-scope effects are recovered, no concurrent controls are joined, and AgentProf preserves all admitted weight. The CodeTraceBench comparison then tests whether a semantic partition aligns with human work stages better than raw action identity. Ordinary B-cubed F1 rises from 0.541 to 0.649, and the direction remains positive under three secondary shared-response token allocations.

The evidence supports two concrete propositions: the scoped adapter preserves correctly joined additive effects, and semantic stage-aligned grouping is more faithful than raw action identity. It does **not** show that the label-free recurrence constructor is uniquely necessary: phase-only reaches 0.654, statistically indistinguishable from recurrence. The paper states this boundary. The paper-level model can survive it because selectable semantic fields, not one universally dominant constructor, are the contribution.

The unresolved construct question is whether partition agreement plus conservation is sufficient to call the result improved “resource attribution.” B-cubed measures agreement of responsibility units, while the weighted variant only changes the aggregation measure. A skeptical reviewer may ask for a direct user- or task-level attribution consequence. The next review stages must decide whether the current scoped claim and multiple-resource flame graphs already answer this, or whether a stronger existing-data analysis is necessary.

### RQ2 — Problem correspondence

The primary result is cleanly stated: on target-bearing queries in three complete public workloads, semantic grouping improves standard MAP over a matched raw-action grouping by +0.016, +0.171, and +0.109. The target labels come from released benchmarks and the semantic/raw comparison uses the same operations and local evidence.

This is the paper’s most important empirical bridge from representation to agent quality. It is also the largest acceptance risk. Raw action identity may be a weak baseline for a reviewer who expects operation-local diagnostic scores, trace clustering, workflow categories, or product-native pattern views. The post-hoc local-first analysis is much stronger: semantic recurrence improves over local-only on all three workloads and over an equally composed local-plus-raw tie-breaker on HINTBench and TraceElephant. However, that analysis was selected after observing the populations and is presented only in prose. AgentProcessBench cannot distinguish semantic from raw tie refinement.

The current evidence therefore establishes that semantic grouping can organize benchmark-provided diagnostic signal better than raw action grouping. It does not yet establish untouched superiority over the strongest available diagnostic organization, lower analyst work, faster repair, or better human decisions. Those broader outcomes should not be silently inferred. The external review must determine which of them is actually necessary for AAAI significance.

### RQ3 — Tag accuracy

RQ3 correctly distinguishes literal labels from permutation-invariant partitions and exact boundaries. Its strongest coherent result is OSWorld-Human group recovery: the label-free recurrence method obtains 0.680 exact boundary F1 and 0.786 ordinary B-cubed F1, above all simple controls and below the supervised and reference-calibrated comparators. The result validates the structural output that AgentProf folds, on a session-held-out population.

The remainder demonstrates backend breadth: task partitions on Mind2Web and ScienceWorld, Qwen task-family classification, Qwen action classification, and deterministic phase structure on CodeTraceBench. This breadth helps the pluggable-tagging story, but the subsection risks reading as several unrelated mini-experiments. Mind2Web contains only nine sessions and 49 operations; action macro-F1 is 0.498; different constructs use different backends and gold semantics. The paper should be judged on whether each experiment validates one declared plug-in mode, not on an implied universal tagger.

The strongest defensible answer is: AgentProf can consume literal or structural semantic fields produced by fixed, target-blind mechanisms, and the evaluated mechanisms materially outperform trivial controls on the named populations. The paper does not establish a universal phase ontology, open-set transfer, or uniform accuracy across agent frameworks; the current limitations say so.

### RQ4 — Profiling cost

The cost experiment reports complete fixed-input runs, three-run medians, a monotonic scale curve, throughput, and peak RSS. The semantic hierarchy processes 27,765 operations in 1.17 seconds and adds 18.2% time and 1.3% maximum RSS over raw grouping. This is adequate evidence that folding and serialization are practical at the evaluated scale.

It is not end-to-end agent observability overhead: capture, source adaptation, and field/tag generation are excluded. The subsection clearly declares that boundary. A reviewer may still ask whether model-based tag generation dominates the stated cost, but the correct response may be to describe RQ4 as profile-construction cost rather than to add a new expensive benchmark. The full review should not manufacture a broader cost claim than the paper makes.

## Rendered artifact and figure audit

### Figure 1 — three semantic flame graphs

The figure visually demonstrates a genuine property: the same corpus produces different token, time, and file views. It is the only end-user-facing picture of the proposed capability and is therefore important. At AAAI two-column print size, most frame labels are extremely small, repeated colors have no legend, and the reader cannot infer a concrete action from the graph. The caption explains what changes but not what surprising finding a developer obtains.

This is a presentation risk rather than evidence that the model is wrong. A stronger figure could add two or three callouts to the existing images, for example the category that ranks eighth by time but 93rd by tokens, without inventing a new experiment. The current paper states that finding in RQ1 but does not visually connect it to Figure 1.

### Figure 2 — pipeline

The architecture is simple and legible. It makes the four-stage implementation clear, but it omits the low-level effect-joining path emphasized in RQ1 and does not show that the same operations can be reprojected into multiple query-time stacks. Those details are described in text. No architectural contradiction is visible.

### Tables 1--4

The tables are compact and readable. Table 1 appropriately exposes phase-only as a strong semantic view. Table 2 reports only the confirmatory raw-action comparison; the stronger local-first mechanism analysis remains prose, which may make the empirical story look weaker than it is. Table 3 combines boundary and partition metrics well. Table 4 is clear about construction scope.

No figure or table contains an obviously inconsistent number on the blind read. This node did not independently recompute values; prior construct verification is outside the blind protocol.

## Paper-level attack map

### Must investigate before an accept claim

1. **Closest-capability novelty.** Is “selectable semantic stacks over cross-run operations and additive effects” substantively beyond current cross-trace category discovery, trace patterning, workflow profiling, and trace/continuous-profile correlation, or mainly a pprof serialization choice? This requires current primary-source product and paper search.
2. **Strongest-baseline sufficiency for RQ2.** Does comparison to matched raw-action organization answer the paper-level claim, given that benchmark-local evidence and current trace-analytics products are plausible alternatives? Existing local-first results may already contain the answer, but they are post-hoc and not independently confirmed.
3. **AAAI significance beyond systems packaging.** What general AI-agent belief or capability changes if the paper is accepted? The thesis is large enough, but the evaluation must make the developer decision enabled by population profiling unmistakable.
4. **Unifying interpretation of RQ3.** Can readers see the tag/partition experiments as validation of one pluggable model rather than as a metric and backend collection assembled after the fact?

### Important but plausibly solvable without a new experiment

5. **Related-work depth.** The current related-work section is only three short paragraphs and cannot visibly establish distance from the closest 2025--2026 agent-observability and diagnosis work.
6. **Figure actionability.** Figure 1 is conceptually central but visually dense and lacks callouts that connect different resource widths to a developer finding.
7. **Baseline/result prominence.** The local-first mechanism result may deserve a table or visual because it directly addresses the “semantic grouping versus local evidence” objection; this is a WRITE decision after evidence review, not a blind-edit instruction.
8. **Name consistency.** The paper title/system prose uses AgentProf while the executable is `agentpprof`. This can be intentional, but a reader should not wonder whether they are different artifacts.

### Not a current blocker

9. **Metric standardness.** The main metrics are established metrics matched to declared constructs. The custom budget and resource-weighted variants are secondary. Adding a large metric suite would make the evaluation less coherent, not more convincing.
10. **Universal constructor dominance.** The contribution does not require recurrence to beat every semantic view. The selectable operation-stack abstraction is compatible with phase-only, supervised, mapped, or label-free fields.
11. **End-to-end online overhead.** The paper explicitly evaluates offline construction and does not currently claim negligible capture or model-tagging overhead. A new online-overhead experiment is not automatically required.

## Reviewer questions that the next nodes must answer

1. What is the closest existing system that can group many agent traces by recurring semantic behavior and aggregate cost, latency, evaluation failures, or system effects within those groups?
2. Can any existing system change the semantic attribution hierarchy at query time while preserving the same additive operation corpus and export the result to a standard profiler?
3. Is the operation-stack abstraction meaningfully different from ordinary `GROUP BY`, trace clustering, sequence segmentation, process mining, or adding OpenTelemetry span attributes?
4. What is the strongest same-signal baseline for RQ2, and does the existing local-first result already isolate the incremental value of semantic recurrence?
5. Does the current evidence enable a concrete decision that per-run debuggers cannot make, such as prioritizing a recurring problem or comparing resource bottlenecks across semantic categories?
6. Are the paper’s 2025--2026 academic citations the closest claim-level work, or are recent profiling/trace-mining papers missing?

## Provisional blind verdict

**Weak reject / genuinely borderline, approximately 4.5--5/10 for AAAI, with high upside.**

The thesis, representation, real populations, and standard evaluation measures are credible. The paper is closer to a top-conference submission than a prototype report. It is not yet safe to call acceptable because a skeptical reviewer can currently reduce the contribution to “semantic grouping plus pprof,” challenge raw action as the decisive RQ2 baseline, and find too little closest-work analysis to resolve that objection. These risks may be addressable with existing results and stronger positioning rather than a new algorithm or a larger metric suite.

This is not a recommendation to shrink the story. The correct next move is to attack the large thesis with current external evidence and the strongest existing-data baseline, then strengthen the paper if it survives.

## Search-tree and project-memory update

The next search branches are:

1. cross-trace agent analytics and category/pattern discovery in real products;
2. academic agent observability, diagnosis, trajectory mining, and operation profiling;
3. distributed-trace aggregation, profile/trace correlation, process mining, and semantic sequence segmentation;
4. standard evaluation precedent for population-level problem localization and partition recovery.

No thesis, RQ, hypothesis, algorithm, or paper prose changes are authorized by this blind read. The original large story remains intact. Any later proposed story change must be compared against the complete idea history and must be justified by a direct thesis challenge, not by a single bounded result.

## Completion and next node

This blind-read node is complete. The next node performs external primary-source verification, updates the canonical related-work/novelty map, and tests the four must-investigate objections. Only after a full-paper reread and independent review may the outer REVIEW gate route one concrete experiment or writing action.
