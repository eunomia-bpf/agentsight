# Blind Full-Paper Read and Attack Map

## Node record

- **Started:** 2026-07-14T01:41:00-07:00
- **Completed:** 2026-07-14T01:48:15-07:00
- **Parent:** Step 0004 `REVIEW_GATE`, review loop 001
- **Objective:** Review the active paper as an unprimed skeptical reviewer and record its argument, evidence surface, and strongest reject hypotheses before seeing experiment verdicts or cycle-change reports.
- **Inputs and provenance:** the complete active paper in `docs/paper/main.tex`; its compiled bibliography, claim-bearing figures, architecture source, and eight-page PDF; `docs/user-instruction.md` and `docs/idea-story.md` solely as fixed author-intent constraints; the `iter-review-critique` research-taste, systems, AI/ML, and cross-domain review references.
- **Method:** one blind read from title through conclusion, inspection of every included claim-bearing figure and the compiled references, then a second paper-only pass to map each RQ to its stated claim and evidence. I deliberately did not read `docs/evaluation.md`, `docs/background-related-work.md`, prior experiment reports, gate verdicts, paper checker reports, or cycle summaries before completing this attack map.
- **Reviewer context:** target is AAAI 2027 Main Track; the contribution is genuinely cross-domain because it makes a systems abstraction and artifact claim while relying on AI-agent semantic tagging, public trajectory data, and empirical generalization claims. I therefore apply both systems and AI/ML bars. The main body occupies six pages and references occupy pages seven and eight, so the currently compiled PDF satisfies the workspace's stated seven-page-main-content constraint.
- **Unavoidable contamination:** the author-intent files disclosed that the exact thesis and four RQs are fixed and that the paper was restored from a canonical source. They did not disclose Step 0004's outcome or the current experiment verdict, so the scientific evidence assessment below is still paper-only.

## Paper-only reconstruction

### Problem, stakes, and challenged belief

The paper argues that teams need population-level explanations of cost, failures, and unsafe effects across many long-running agent trajectories, while current observability emphasizes single-execution traces. Its challenged belief is that per-run execution structure and request-level tags are sufficient for such questions. In plain language, the intended durable principle is:

> Treat agent trajectories as profiling samples, then attribute additive measures to recurring semantic responsibility rather than treating every run only as a debugging trace.

That is a consequential and memorable problem. The paper's strongest taste property is its exact thesis, **“Agent observability needs profiling, not only debugging.”** It is simple, non-obvious enough to be falsifiable, and potentially durable across agent frameworks.

### Model and causal chain

The artifact normalizes prompts, LLM calls, tools, and system effects into weighted fielded **operations**. A query-time ordered field list forms an **operation stack**. Intent attribution supplies stable semantic fields; stack construction chooses hierarchy; folding sums a chosen additive weight; pprof/flamegraph output exposes the aggregate.

The claimed causal chain is:

```text
heterogeneous trajectories and system effects
-> uniform operations with inherited semantic fields
-> stable tags and query-time operation stacks
-> recurring responsibility groups
-> better attribution/localization at practical offline cost
```

The two-object core is appropriately small. Regex/LLM/clustering taggers, boundary induction, importers, and renderers should remain supporting mechanisms; promoting them to co-equal concepts would make the paper complicated without deepening the principle.

### Claimed contributions and four RQs

1. A semantic operation-stack model for the missing cross-run profiling layer.
2. AgentProf, an offline Rust profiler producing standard profile formats.
3. Empirical evidence over local trajectories and public datasets.

The paper exposes exactly four RQs:

| RQ | Paper-level goal | Stated paper answer | Blind evidence assessment |
|---|---|---|---|
| RQ1 attribution | Semantic stacks improve attribution of system/resource measures to task intent. | Prompt tags reduce mixed-weight buckets; multiple field/weight views differ. | **Not yet paper-credible.** The category used to score “mixing” appears to be derived from the same prompt semantics used to create the separating tag. It demonstrates partitioning, not independently correct responsibility. |
| RQ2 real problems | Target-blind profiles surface independently annotated failures/risky steps earlier. | Positive across AgentProcessBench, HINTBench, and TraceElephant. | **Promising and plausibly answered.** It uses complete public workloads and independent targets, but mixes AP, Work@80, and Work@50 into one headline and needs careful source/protocol verification. |
| RQ3 tag accuracy | Target-blind tags and boundaries agree with held-out semantic annotation. | Seven of nine datasets exceed 0.7 V-measure and boundary F1. | **Not answered as written.** The paper equates derived `phase` with dataset-native `action`; the figure visibly does not show both metrics above 0.7 for seven datasets; the threshold and rule-learning procedure are unspecified. |
| RQ4 profiling cost | Full construction scales predictably and cached repeat queries are cheap. | 76 configurations have 1.6 s median, 2.8 s p95; local tagger latency/cache statistics. | **Not answered as written.** Hardware, input sizes per run, cold/warm distinction, memory, scaling curve, repetitions, and the relationship between per-tag latency and full profiling time are absent. |

## Initial verdict

**Reject in current form; incomplete-but-promising rather than complicated-but-shallow.** The simple principle is stronger than the current evidence presentation. RQ2 appears materially stronger than the other three RQs, but the abstract, introduction, evaluation setup, and conclusion still describe an older result surface. The paper is therefore not submission-ready even if the new RQ2 subsection is scientifically valid.

## Ranked blind attack map

### 1. Blocker — the paper contradicts itself about its public-data result surface

The introduction says the evaluation uses “four public datasets (34,539 operations),” locates problems at “9.4% inspection work,” and uses “45% fewer groups than per-session grouping.” Its contribution paragraph repeats “4 public datasets.” The Evaluation setup says 15 families and identifies four older RQ2 families. The current RQ2 subsection instead evaluates AgentProcessBench, HINTBench, and TraceElephant with 8,509, 12,877, and 5,960 steps and reports AP, Work@80, and Work@50. The conclusion again asserts 9.4% inspection work and a six-task/per-session 4-of-6 counterpoint that no longer appears in RQ2.

This is a **global logic/consistency blocker**, not a scientific objection to the new experiment. A reviewer cannot tell what was actually run or which claim the abstract summarizes. It requires a minimal `WRITE_GATE` correction before any submission-quality verdict: update only the stale RQ2-facing sentences and dataset inventory, preserving the fixed story and four RQs.

### 2. Blocker — RQ3's construct does not match its claim, and its prose conflicts with its figure

RQ3 promises correct semantic tags, including identities and boundaries. The experiment compares a derived `phase` partition against native `action` labels. A coarse phase and an action vocabulary are different constructs, so high V-measure does not by itself establish “correct semantic phase,” while low agreement may reflect granularity mismatch rather than incorrect tags. The plotted figure has missing boundary values and appears to show only six datasets with both metrics above 0.7, yet the prose says seven of nine exceed 0.7 on both metrics. The 0.7 threshold is not justified. “Train mapping rules” is insufficiently specified for an AI/ML reviewer to audit target blindness, selection, or leakage.

This is the largest **scientific/evidence** gap because RQ1 and RQ2 both depend on useful semantic tags. A complete RQ3 experiment should repair the construct rather than weaken the RQ.

### 3. Major — RQ1 measures separability using a potentially circular category

The paper calls lower mixed weight “correct” resource attribution, but the task categories appear to be prompt-derived and the prompt tag is the tested intervention. A permutation test shows non-random association, not correctness of causal/system-effect attribution. The graph's zero or near-zero mixed weight when both session and prompt fields are present may also be a mechanical consequence of making groups nearly unique. “More unique stacks” can trivially reduce mixing, so the current ablation needs an independent target and a granularity-matched baseline.

This routes to a later `EXPERIMENT_GATE`, not claim shrinkage. It is not the best immediate next experiment only because RQ3 is a prerequisite and can reuse more existing assets.

### 4. Major — RQ4 reports timing numbers without a scaling experiment

The current statistics do not support “practical predictable scaling.” No hardware/software environment, number of runs, input-size sweep, operation throughput, memory, cold construction, warm repeat-query latency, or variance by size is reported. “Zero runtime overhead” is true only in the narrow sense of offline post-hoc execution and should not be confused with collection overhead. A later RQ4 experiment can likely reuse the existing 76 configurations and profiler binary; it should not require a new complex benchmark.

### 5. Major — novelty and the status quo are asserted too categorically

“Existing agent tools support debugging and tracing but not profiling,” “unable to aggregate by semantic category,” and “all [profiling tools] assume stable function names and a runtime call stack” are load-bearing claims. Existing products already support tags, metadata, trace aggregation, derived signals, and cross-run monitoring; process-mining and trace-clustering communities also aggregate event sequences without code call stacks. The paper may still own the more specific **additive-measure attribution to recurring semantic responsibility with standard profiler views**, but the related-work section is too short to establish it.

This is a novelty/search issue, not a reason to narrow the thesis. External source verification must test whether the sharper contribution survives.

### 6. Major — unsupported or underdefined algorithm claims

The design claims that an AI agent iterates regexes to under 5% unmatched in 5–10 rounds, that a 3B local tagger yields stable repeatable tags, and that automatic boundary induction creates useful variable-depth stacks. No algorithm specification, training/selection protocol, or current evidence justifies those exact performance/generalization statements. The paper also calls mappings target-blind without defining which fields, labels, or benchmark splits are visible at each stage.

These are technical-mechanism/evaluation issues. The immediate repair is evidence and protocol clarity, not adding more abstractions.

### 7. Minor/major writing — the paper reads as a restored positive baseline with partial evidence replacement

The abstract omits the exact thesis sentence; the introduction's current headline results do not include the strongest new RQ2 evidence; the related-work section is one short paragraph; the conclusion resurrects old negatives and old metrics. There are also local grammar defects (“quality ... of AI agent,” “an AI Agent can iterates”). These do not define the science, but they amplify the consistency blocker.

## Load-bearing claims requiring external verification

1. Current tools are per-run/debugging oriented and cannot perform the paper's cross-run additive attribution.
2. Pprof label features require an execution stack and cannot express the proposed agent profile directly.
3. AgentProcessBench has the claimed human step labels, populations, and provenance.
4. HINTBench and TraceElephant support the exact test population and annotations used in RQ2.
5. Native actions in the nine RQ3 datasets are defensible ground truth for semantic phase/tag accuracy.
6. Closest work in process mining, trace clustering, agent observability, failure localization, and semantic conventions does not already provide the same principle/mechanism.
7. AAAI 2027 review and formatting expectations relevant to empirical AI systems work.

## Largest claim worth defending

The strongest plausible paper is not merely “a field-list query can draw semantic flame graphs.” It is:

> A single profiling model can turn heterogeneous agent histories into conserved additive measures over recurring semantic responsibility, enabling population-level cost attribution and problem localization that per-run traces do not provide.

The current evidence almost supports the localization half. The remaining RQs should make the attribution and tag/cost halves equally direct.

## Initial next-experiment hypothesis

Subject to source verification and cycle evidence, the highest-value simple experiment is likely RQ3 using the repository's existing nine public-dataset adapters, operations, mapping/tagging path, AgentProf binary, and scoring code:

> **On unseen agent/task families, the fixed target-blind AgentProf tagger assigns independently defined semantic phase/action identities and change boundaries more accurately and stably than source-native/raw-action and simple lexical baselines.**

The experiment should use one externally defined label ontology or a clearly matched family-specific label mapping; it must not compare coarse phase directly to an incompatible action vocabulary and call that correctness. It should execute the full existing matrix once, not create a new taxonomy, model, benchmark, or elaborate protocol.

## Alternatives and decision

- **RQ1 next:** scientifically important, but independent responsibility labels are harder to obtain and new capture could expand complexity.
- **RQ3 next:** best leverage because existing public adapters/data/figures already exist and tag validity is prerequisite to RQ1/RQ2 interpretation.
- **RQ4 next:** simplest engineering run, but lower paper decision value than repairing the load-bearing semantic construct.

Provisional decision: verify sources, inspect cycle evidence, then route one complete reused-asset RQ3 experiment unless the internal evidence shows that the existing RQ3 inputs cannot support a construct-valid test.

## Tree/search and project-memory updates

- **Search tree opened:** status quo/closest profiling; benchmark annotation provenance; RQ3 construct/metrics; cost protocol; AAAI venue.
- **Search strategy change:** prioritize primary papers, official repositories/specifications, and benchmark data cards; search both systems observability/process mining and AI-agent evaluation communities.
- **Project-memory proposal:** none at blind-read time. Reviewer findings do not authorize story or RQ changes.

## Completion assessment and next node

The blind-read node is complete. It formed an unprimed paper-only verdict and attack map without using Step 0004's internal result assessment. Next node: mandatory external search and primary-source verification.
