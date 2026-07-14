# Blind Full-Paper Read and Reject-Hypothesis Map

## Node metadata

- **Timestamp:** 2026-07-14T10:33:42-07:00
- **Parent:** Step 0013 REVIEW gate
- **Objective:** Perform a fresh paper-only AAAI-27 Main Track review and form an initial verdict before external search or exposure to project history.
- **Review mode:** Blind full-paper read. No external browsing and no prior review, evaluation-memory, idea-story, user-instruction, or cycle-report material was read.
- **Target venue:** AAAI-27 Main Technical Track, inferred from the `aaai2027` submission format and the assigned review task.
- **Contribution classification:** Genuinely cross-domain, but systems-heavy. The artifact and representation are systems contributions; the claims about semantic categories, learned boundaries, held-out trajectory data, and problem localization require AI/ML evaluation validity as well.
- **Review references loaded:** `research-taste.md`, `systems-review.md`, `ai-ml-review.md`, and `cross-domain-review.md` from `iter-review-critique`.
- **Inputs/provenance:** `docs/paper/main.tex`, rendered `docs/paper/main.pdf`, all figures and tables referenced by the paper, `docs/paper/references.bib`, and the rendered bibliography. The PDF is nine pages total, with seven manuscript pages and two reference pages, in US Letter format with embedded fonts.
- **Unavoidable contamination:** The assigned task explicitly called attention to whether RQ2 baseline presentation is convincing. I therefore knew RQ2 was a likely stress point, but I had no knowledge of whether or how it had changed and no access to earlier verdicts.

## Initial verdict

**Score: 5/10 — Weak Reject (borderline, incomplete but promising).**  
**Confidence: 4/5.**

The paper identifies an important recurring need and presents a coherent, memorable thesis: **agent observability needs profiling across runs, not only debugging within a run**. Its best scientific move is to separate the execution record from the responsibility view: preserve additive operations once, then project them into selectable semantic hierarchies. The artifact is real, the paper is unusually explicit about held-out targets and incomplete dominance, and the breadth of public data is substantially stronger than a toy demonstration.

The current rejection case is nevertheless stronger than the acceptance case. The paper does not yet establish that its semantic profiles provide a decisively better *diagnostic decision surface* than existing structural views. RQ2 is the load-bearing bridge from “we can fold records by semantic fields” to “this is useful profiling.” The new baseline table is clear and candid, but it shows one statistically supported semantic-specific gain, one comparison whose interval crosses zero, one descriptive early-recall gain whose prospective high-recall point fails, and finer session/step references that can outperform the proposed view. The paper names “recurring groups” as the value of the semantic profile but does not evaluate the claimed tradeoff between recurrence/compactness and localization quality consistently across the three workloads. Without that link, a skeptical reviewer can interpret the operation stack as an ordered multi-field aggregation rendered through pprof rather than a demonstrated new profiling abstraction for agent diagnosis.

## Paper reconstructed from the blind read

### Problem, stakes, and challenged belief

The problem is population-level analysis of many agent trajectories. Developers need to know which task classes consume resources, where failures recur, and which workflows cause system effects. Existing trace trees and per-run diagnosis primarily organize evidence by execution. The paper challenges the implicit belief that run-local traces plus metadata dashboards are sufficient: agent observability also needs a cross-run profiling layer that attributes additive evidence to recurring semantic responsibilities.

The stakes are credible. Long-running tool-using agents generate heterogeneous intent, tool, process, file, network, time, and token records, and inspection one trajectory at a time scales poorly. The paper is strongest when it treats profiling as a different question from debugging rather than as another trace visualization.

### Simple principle

**Preserve each agent effect once as an additive operation, then choose the responsibility hierarchy at query time instead of treating the execution tree as the only hierarchy.**

This principle is simple and potentially durable. It predicts that multiple responsibility views over the same evidence should expose different resource bottlenecks and different recurring problem concentrations while conserving total weight.

### Artifact and causal chain

The reconstructed causal chain is:

```text
heterogeneous cross-layer agent records
-> uniform weighted operations with inherited semantic fields
-> stable fields from rules, a local tagger, clustering, or mappings
-> query-time ordered field projection / induced boundaries
-> folding equal stacks with additive weights
-> pprof, flame graph, SVG, or JSON views
-> earlier inspection of resource- or problem-dense recurring groups
```

AgentProf is an offline Rust CLI of approximately 9.8 KLOC. It reads local Codex/Claude histories and operation JSONL, derives fields, constructs explicit or induced operation stacks, folds them, and exports profiler-compatible representations. AgentSight supplies part of the source-linkage path through an adapter; AgentProf does not directly read those recordings.

The last edge—profile output to better investigative decisions—is the least well established. RQ2 measures concentration and inspection proxies, not whether a developer finds, explains, or fixes a failure more effectively.

### Claimed contributions

1. A semantic operation stack model: uniform additive operations plus query-time responsibility stacks.
2. AgentProf: a profiler with pluggable intent attribution and stack construction, exporting pprof-compatible profiles.
3. An evaluation spanning source lineage, resource attribution, problem correspondence, tag/boundary accuracy, and construction cost across real local trajectories and public benchmarks.

### Explicit RQs and evidence map

| RQ | Intended answer | Main evidence in the paper | Blind-read assessment |
|---|---|---|---|
| **RQ1: Does semantic profiling improve resource attribution?** | Semantic fields produce more useful responsibility separation over source-linked additive effects. | 20 real Codex tasks plus concurrent controls; 1,520/1,574 in-scope effects recovered, zero false positives and zero joined control effects; exact folding preservation; 325 local trajectories with mixed weight falling from 90.4% to 36.7% under prompt tags; multi-weight rankings; induced-stack summaries. | Source fidelity and conservation are convincing for the declared suite. The semantic-separation metric is conditional on the same prompt tags that define category mixing, so it demonstrates refinement but not correctness of responsibility. Automatic induction is weaker than hand-specified stacks on AP and is only sparsely characterized. |
| **RQ2: Does profiler output correspond to real problems?** | Target-blind semantic profiles concentrate annotated failures/risky steps into recurring groups that can be inspected early. | Complete AgentProcessBench, HINTBench, and TraceElephant workloads. Semantic vs raw: AP .588 vs .556 on AgentProcess; Work@80 .416 vs .463 on HINT; Work@50 .195 vs .466 on Trace. Table also shows flat/native/session/step/width controls and the failed Trace Work@80 point. | The table is honest and much more convincing than a raw-only comparison would be. Still, only AgentProcess gives a clean semantic-specific effect. HINT-vs-raw uncertainty crosses zero; Trace’s prospective high-recall point is unfavorable; session or per-step views can score better. The untested value proposition is whether semantic profiles deliver the best useful tradeoff between recurring-group compactness and localization quality. |
| **RQ3: How accurate are the tags?** | Target-blind fields and boundaries recover independent annotations on unseen sessions/families. | Five-fold session-blocked supervised boundary prediction on 287 OSWorld-Human tasks: .739 boundary F1 and .816 B3 F1; task partition V-measure .557 on nine Mind2Web sessions and .815 on 100 ScienceWorld sessions. | The held-out boundary experiment is credible and clearly reported. However, it tests a supervised Bernoulli Naive Bayes predictor that is explicitly different from AgentProf’s built-in Rust inducer. Phase labels, action labels, literal names, and production-default regex/3B tags are not validated. The RQ is broader than the answered subset. |
| **RQ4: What is the profiling cost?** | Offline profile construction is practical and close to linear over the tested range. | Three-run medians on four public workloads and their union; 27,765 operations in 1.17 s, 464.5 MiB RSS, +18.2% time and +1.3% memory over raw-action construction. | Adequate for the deterministic parse/construct/fold/serialize path. It excludes capture and the potentially expensive field-derivation path, while the only tag-caching result belongs to a predecessor. Thus it answers core construction cost, not end-to-end profiling cost. |

## Ranked accept arguments

1. **Important and timely problem with a memorable thesis.** Cross-run profiling is a real abstraction gap between trace inspection and population-level agent operations. “Profiling, not only debugging” is clearer and more durable than a narrow benchmark claim.
2. **A simple representation principle connects the design.** Uniform additive operations plus selectable responsibility projection is easy to state, explains why the same data can produce token/time/file views, and is separable from the AgentProf name.
3. **The evaluation uses real and citable anchors.** The paper includes real Codex/Claude trajectories, concurrent source-lineage controls, complete public localization workloads, held-out OSWorld-Human sessions, and public task-partition datasets rather than only hand-built examples.
4. **The paper is candid about boundaries.** It reports that session/per-step views can outperform semantic AP, that HINT-vs-raw uncertainty crosses zero, that Trace Work@80 fails, that RQ3 does not cover literal tag names, and that the supervised boundary predictor is not the built-in inducer. This improves scientific trust.
5. **Core invariants have direct evidence.** Source scope, rejection of concurrent effects, and exact additive preservation are concrete and auditable properties rather than qualitative screenshots.
6. **The presentation is compact and submission-ready at the mechanical level.** The seven manuscript pages are readable, the four RQs are explicit, figures and tables render cleanly, and the main story remains consistent from abstract through conclusion.

## Ranked reject arguments and attack map

### Major 1 — Evidence/evaluation: RQ2 does not yet establish the decisive semantic-profile advantage

**Exact claim/location.** The abstract says semantic profiles “concentrate annotated problems”; the Introduction claims target-blind semantic profiles improve problem concentration over raw action; RQ2 concludes positively that operation stacks expose recurring problem-enriched groups.

**Failed reviewer inference.** A reviewer needs to infer that the semantic hierarchy is a better profiling decision surface than simpler structural organizations. Table 1 instead presents a mixed frontier:

- AgentProcess: semantic AP .588 exceeds raw .556 with a positive interval and a within-raw assignment test, but session .599 and per-step .777 are higher.
- HINT: semantic Work@80 .416 is directionally better than raw .463, but the paired interval crosses zero. It does beat native, session, and step views.
- Trace: semantic Work@80 is 1.00, worse than raw .719 and width .677. The strong Work@50 result is explicitly descriptive rather than the prospective endpoint.

The prose says the semantic groups are recurring and occupy an intermediate granularity, but only AgentProcess reports group counts. The table mixes AP, Work@80, and descriptive Work@50 and does not expose the compactness/localization frontier that would explain why a lower-scoring session/step view is not the better tool. Consequently, “positive without uniform dominance” is honest but not yet a crisp scientific answer.

**Strongest alternative explanation.** The observed gains may come from choosing a favorable grouping granularity and ranking policy for each workload, not from a generally useful semantic responsibility hierarchy. A sufficiently fine step/session view captures more target signal; a coarse raw/native view is cheaper to inspect as groups; semantic fields may simply occupy an intermediate point.

**Routing.** EXPERIMENT_GATE, using existing artifacts rather than a new benchmark or model.

**Ambition-preserving repair.** Demonstrate that semantic responsibility groups occupy a reproducible Pareto frontier: they retain substantially more localization signal than equally compact structural views while remaining reusable across runs, whereas session/step views gain quality by fragmenting recurrence. This would strengthen—not narrow—the profiling thesis.

### Major 2 — Scientific framing/novelty: the model risks reading as an ordered GROUP BY exported to pprof

**Exact claim/location.** The Introduction presents a missing profiling layer; Design defines an operation stack as an ordered list of fields projected to a frame sequence; Related Work acknowledges pprof labels/pseudo-frames, flexible trace queries, and commercial cross-trace category hierarchies.

**Failed reviewer inference.** From the paper alone, the novel principle is plausible but the mechanism novelty is not yet sharply separated from existing multi-dimensional aggregation, trace queries, supplied labels, category dashboards, and pseudo-frame rendering. “Source-linked + additive + selectable + pprof-compatible” is a conjunction of useful properties, but the paper does not show which property creates a new diagnostic capability unavailable through an ordinary tagged event table plus hierarchical grouping.

**Missing evidence.** The paper would benefit from a direct capability-level comparison grounded in the decision enabled, not merely a feature conjunction. This issue requires external source verification in the next review phase; the blind phase cannot determine whether the novelty claim survives the closest product and systems literature.

**Routing.** The same EXPERIMENT_GATE evidence as Major 1 can provide the missing scientific distinction if it shows a responsibility/recurrence tradeoff that ordinary execution-tree or raw-field views do not recover.

**Ambition-preserving repair.** Defend the larger principle that execution structure and responsibility structure are distinct, and that a profiler must conserve evidence while making responsibility selectable. Do not reduce the work to “pprof for agents.”

### Major 3 — Global logic/evidence: RQ3’s headline is broader than the tested AgentProf mechanisms

**Exact claim/location.** RQ3 asks “How accurate are the tags?” and hypothesizes accurate task, phase, action, and boundary fields. The strongest result is a supervised boundary predictor; the paper explicitly states that it is not the built-in Rust stack inducer. Task partition evidence uses TF-IDF/K-Means, while phase, action, literal names, regex tags, and the local 3B tagger remain untested.

**Failed reviewer inference.** The abstract’s .739/.816 result can easily be read as validating AgentProf’s automatic stack construction, but the Implementation section describes a different built-in algorithm. The paper is accurate when read closely, yet the best RQ3 number does not validate the default or built-in path that a user would run. Nine Mind2Web sessions are also too small to carry broad task-tag accuracy by themselves.

**Routing.** This is a major scope/evidence mismatch, but it should not displace the single RQ2 action below because RQ2 is more load-bearing for the whole paper. The current paper must continue to state the distinction explicitly.

**Ambition-preserving repair.** Treat accurate semantic field construction as a pluggable method problem and make the scientific contribution the profiling interface/invariant rather than implying that every included tagger is already validated.

### Major 4 — Evidence/evaluation: RQ1’s main semantic-separation metric is partly self-referential

**Exact claim/location.** RQ1 reports that adding prompt tags reduces “mixed weight,” where mixing is defined by whether a group contains observations from multiple prompt-tag categories. The 3B prompt tags are declared categories rather than an independent oracle.

**Failed reviewer inference.** Adding the category field used to define mixing will mechanically split many mixed groups. The permutation test shows that the observed assignment structure is not random, but it does not establish that the tags correspond to the correct responsibility or that the resulting separation helps a developer. The source-lineage and conservation evidence is valuable, yet it belongs partly to the predecessor capture path and proves correct plumbing rather than semantic attribution quality.

**Routing.** The same RQ2 experiment is the proper repair because independent problem annotations can validate whether the semantic separation has downstream diagnostic value.

**Ambition-preserving repair.** Retain the large cross-layer attribution claim, but ground its usefulness in independent outcomes rather than only a tag-conditioned purity measure.

### Major 5 — Evidence/evaluation: RQ4 excludes a potentially dominant part of the advertised pipeline

**Exact claim/location.** RQ4 asks what profiling costs, but times only post-session parse/construct/fold/serialize and excludes capture. It compares a fixed semantic hierarchy with raw action. The only local-model/caching result is from the predecessor AgentFlame, not the current binary.

**Failed reviewer inference.** The 1.17 s headline can be interpreted as end-to-end semantic profiling cost even though rule iteration, local-model tagging, clustering, source adaptation, and capture are outside the measurement. Peak RSS of 464.5 MiB for 27.8 K operations is not alarming on the stated machine but is high enough that scaling beyond this range remains uncertain.

**Routing.** Evidence gap, but secondary to RQ2. The wording is currently careful enough that this is not an independent immediate experiment recommendation.

**Ambition-preserving repair.** Continue distinguishing core construction cost from capture and derivation cost; do not use the core timing to imply full-pipeline cost.

### Minor 1 — Scientific clarity: automatic induction is underspecified relative to its role

The built-in inducer uses Jaccard distance, structured-field changes, segment balance, query-term overlap, and a depth cap, but the scoring function, normalization, threshold selection, and complexity are absent. Its reported median AP is lower than hand-specified stacks, and the “useful for initial exploration” claim is not independently evaluated.

### Minor 2 — Writing/information flow: RQ1 is overloaded

RQ1 contains source linkage, exact conservation, semantic-axis separation, multi-granularity folding, multi-weight rank divergence, and automatic induction. These are individually relevant but make the section feel like several mechanism checks combined under the broad word “attribution.” The strongest proof—the source-linked additive invariant—competes for space with weaker descriptive observations.

### Minor 3 — Terminology: several labels add less meaning than the paper assumes

- “Operation stack” is useful when it denotes an ordered responsibility path, but “semantic operation stack model” is often longer than the underlying principle requires.
- “Intent attribution” also covers mappings from structured action/quality fields, which are not necessarily intent.
- “Problem correspondence” means failure/risk concentration or localization and is less precise than either.
- “Source-linked additive cross-layer effects with selectable pprof-compatible operation-stack projections” stacks several properties into one novelty phrase and is difficult to retain.

These terms should not be multiplied further. The durable vocabulary is likely **operation**, **responsibility view/stack**, **additive weight**, and **cross-run profile**.

### Minor 4 — Submission polish: the central RQ2 evidence has no visual frontier

Table 1 is readable and commendably includes unfavorable controls, but its mixed metrics make the paper’s most important result cognitively expensive. A three-panel within-workload frontier would communicate the scientific point more directly than the current heterogeneous rows, provided it is generated from the same audited outputs rather than from new post-hoc metric selection.

## RQ2 baseline-presentation audit from the paper alone

The paper now passes the minimum honesty test: it names raw, flat, native, session, independent-step, and width views; states which comparisons are significant; reports the unfavorable Trace Work@80 outcome; and explicitly rejects uniform dominance. A reviewer can no longer reasonably claim that the evaluation hides all structural controls.

It does **not** yet pass the decisive-comparison test. The baseline table answers “what scores did the views obtain?” but not “why is the semantic profile the right operating point?” Three omissions keep that question open:

1. Recurrence/fragmentation is quantified only for AgentProcess, although recurrence is the stated advantage over session/step views.
2. The three datasets use different endpoints, so the rows cannot be synthesized into one cross-workload claim.
3. The paper does not show matched compactness or a Pareto analysis, so a reviewer cannot separate semantic value from grouping granularity.

My paper-only judgment is therefore: **baseline disclosure is convincing; baseline victory is not yet convincing.**

## Global consistency and presentation audit

- The title, abstract, Introduction, Design, four RQs, limitations, and Conclusion consistently support the profiling-not-only-debugging thesis.
- The paper does not silently claim uniform RQ2 dominance; unfavorable controls in Table 1 agree with the surrounding prose.
- RQ3’s broad question and hypothesis are explicitly narrowed in the same subsection and limitations, but the abstract foregrounds the boundary predictor without immediately reminding the reader that it is not the built-in inducer. This is a presentation risk, not a direct contradiction.
- RQ4 consistently labels the measurement as post-session construction and excludes capture. The abstract’s short cost headline omits this qualifier but does not explicitly claim online overhead.
- Figure 1 is visually attractive and makes multi-weight projection tangible, but labels are extremely small at manuscript scale and many frames are truncated. It motivates the system better than it supports a measured claim.
- Figure 3 is legible. Tables 1–3 render cleanly. The main manuscript ends on page 7 and references occupy pages 8–9.
- No obvious number contradiction was found among the abstract, Introduction, RQ summaries, tables, and Conclusion during the blind read.

## Research-taste assessment

- **Principle:** Preserve additive agent evidence once and choose responsibility hierarchy at query time, because execution hierarchy is not the only useful profiling hierarchy.
- **Belief challenged:** Rich execution traces and run-local diagnosis are sufficient for agent observability. The paper argues that recurring cross-run responsibility profiles are also necessary. Whether this belief is a real community default requires external verification after the blind phase.
- **Strongest alternative explanation:** Semantic fields merely choose an intermediate grouping granularity; any grouping with comparable cardinality could obtain the same localization tradeoff.
- **Largest plausible claim worth defending:** Execution structure and responsibility structure are distinct in agent systems; cross-run observability therefore requires conserved evidence that can be projected into selectable responsibility profiles, not a single canonical trace tree.
- **Classification:** **Incomplete but promising.** The core idea is simple and potentially deep, but the decisive independent evidence does not yet distinguish the principle from ordinary hierarchical aggregation plus favorable granularity.
- **Concepts that can be deleted or merged without losing predictive content:** Merge “intent attribution” into “field derivation” when the source is not natural-language intent; prefer “responsibility view” for the general concept and reserve “operation stack” for its ordered representation; replace “problem correspondence” with the actual localization/concentration construct. This is terminology cleanup, not a request to shrink the thesis.

## Exactly one highest-value next action

**Run one consolidated, matched-granularity RQ2 Pareto analysis using only the already completed AgentProcessBench, HINTBench, and TraceElephant outputs—no new benchmark, model, labels, human study, or collection.** For every already implemented semantic, raw, native, session, step, and width view, report its existing localization quality together with recurring-group count (or an equivalent already derivable fragmentation count) within each workload, with the existing uncertainty procedure. The tested hypothesis should be: *semantic responsibility profiles retain more independently labeled problem signal than structural views at comparable recurring-group compactness, while session/step views gain signal by fragmenting cross-run recurrence.*

This single analysis directly addresses all load-bearing doubts: it tests the larger responsibility-versus-execution principle, explains the stronger fine-grained baselines instead of hiding them, distinguishes semantic content from granularity, and reuses complete public experiments rather than creating a more complex pipeline. If semantic profiles lie on the Pareto frontier across the completed workloads, the AAAI case becomes substantially stronger; if they do not, the current central utility claim remains unsupported regardless of additional benchmark count.

## Completion assessment, uncertainty, and next node

- **Blind phase status:** Complete.
- **What is intentionally unresolved:** Closest-work novelty, whether the challenged industry/research belief is real, benchmark/protocol details, and citation accuracy require the mandatory external-search and source-verification phase. No external conclusion has been imported into this report.
- **Paper/claim impact:** No paper edit is authorized or recommended during this blind phase. The report identifies the load-bearing evidence gap without changing the thesis or fixed RQs.
- **Tree/search update:** Next review node should externally verify the closest semantic hierarchy, trace-query, profiling-label, agent-diagnosis, and population-observability systems, then reassess whether the proposed matched-granularity experiment is sufficient.
- **Project-memory update:** None from the blind reviewer.
- **Recommended route after this paper-only read:** EXPERIMENT_GATE, specifically the one reuse-only RQ2 analysis above, subject to source verification and the outer reviewer’s independent audit.

