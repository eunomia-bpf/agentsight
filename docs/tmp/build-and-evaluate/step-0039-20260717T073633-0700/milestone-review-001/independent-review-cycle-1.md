# Independent AAAI-27 Cross-Domain Review — Cycle 1

## Node identity

- **Timestamp:** 2026-07-17T07:57:33-07:00
- **Parent:** `step-0039-20260717T073633-0700/milestone-review-001`
- **Target venue:** AAAI-27 Main Technical Track
- **Review class:** genuinely cross-domain AI/agent + systems
- **Artifacts reviewed:** complete `docs/paper/main.tex`, rendered `docs/paper/main.pdf`, all included figures and tables, `docs/paper/main.bbl`, Step 0039 reports 01/02, `docs/background-related-work.md`, the complete current author instructions and idea history, and the Step 0019/0037 result reviews needed to judge the fixed-reader and local-first evidence
- **Mutation policy:** read-only for the paper, skills, submodule, and canonical documents; this file is the only output

## Reviewer-context and contamination disclosure

I first read the paper from title through bibliography without opening the Step
0039 reports. I inspected all seven body pages, both reference pages, the three
flame graphs at their source resolution, the architecture figure, and all four
result tables. Only after writing a paper-only attack map did I read
`01-blind-full-paper-read.md`, `02-external-search-primary-source-verification.md`,
and `docs/background-related-work.md`. I then independently opened primary
sources for TraceProbe, WebGraphEval, Hodoscope, TraceGraph, Datadog Patterns,
LangSmith Insights, and OpenTelemetry Profiles, and read the complete Step 0019
and Step 0037 result reviews.

Perfect independence is impossible because the requested report path and task
identify the paper's fixed thesis, RQs, and named novelty threats. I therefore
treat those as declared review questions, not conclusions. The score and
must-fix list below are my own disposition after the paper-first read and source
verification.

## Executive verdict

**Overall score: 5/10 — Weak Reject, genuinely borderline.**

**Confidence: 4/5.**

The paper is much closer to an AAAI submission than a prototype report. It has
a memorable and consequential thesis, a compact two-object model, a real Rust
artifact, complete public populations, mostly standard metrics, and positive
answers to four explicit RQs within declared scopes. I would nevertheless vote
weak reject on the current PDF because its visible novelty argument and its
strongest evidence are out of sync with the July 2026 frontier. The current
Related Work omits the most direct academic threats, Table 2 foregrounds the
weaker raw-action-only comparison while the stronger local-evidence-preserving
comparison is buried in prose, and the paper does not explicitly close the
causal chain from its surviving unique systems mechanism to an AI-agent
decision.

This is **incomplete-but-promising and potentially simple-but-deep**, not
complicated-but-shallow. The correct repair is not a smaller thesis, a new
algorithm, a metric zoo, or another benchmark. The smallest acceptance-changing
repair is a focused WRITE pass that exposes the actual composite contribution,
the strongest already-completed baseline comparison, and the exact construct
answered by each RQ.

## Paper reconstructed in one sentence

Agent observability needs profiling, not only debugging: completed agent
histories should be represented as weighted operations and folded through
query-time semantic operation stacks so that recurring responsibility for
tokens, time, files, network activity, and independently annotated problems can
be analyzed across runs without depending on runtime call nesting.

## Research taste and AAAI significance

### The durable principle

The principle is simple: **execution occurrence and cross-run responsibility
are different structures, so profiling an agent population requires selectable
semantic responsibility views over conserved measured activity.** Operations
and operation stacks are sufficient to express that principle. The model does
not need more abstractions.

### The challenged belief

The paper challenges the operational default that tracing or replaying
individual agent executions is the adequate observability unit. This is not a
strawman: current Datadog Patterns and LangSmith Insights explicitly add
cross-trace hierarchical categorization and aggregate cost, latency, errors,
feedback, and evaluations, while NVIDIA calls its workflow analysis a profiler.
Those products validate the problem's importance while simultaneously making
generic cross-run grouping non-novel.

### AAAI significance

The fixed thesis still has AAAI-level significance. Long-running agents create
quality, safety, and cost questions that cannot be reduced to one execution,
and a reusable population-level responsibility abstraction is relevant beyond
one model or benchmark. The paper's broad significance survives only if the
reader sees the joint capability—source-linked agent/system effects, conserved
additive measures, selectable query-time semantic hierarchies, and a verified
decision consequence—not isolated components such as clustering or pprof
export.

### Strongest alternative explanation

The strongest alternative is that AgentProf is ordinary trace/span
categorization plus `GROUP BY`, rendered in pprof. Datadog and LangSmith already
hierarchically categorize traces and roll up cost/error/latency; TraceProbe and
WebGraphEval already canonicalize actions and produce weighted cross-run process
representations; OpenTelemetry Profiles already supplies pprof-compatible
profile/trace linkage. The paper must show why a conserved operation-level
responsibility profile over heterogeneous effects is a scientific abstraction,
not merely a different serialization.

## Verified novelty threats

| Threat | What the primary source already establishes | Direct consequence for this paper | Surviving distinction |
|---|---|---|---|
| **Datadog Patterns** | Production interactions are summarized, embedded, clustered into a hierarchy, assigned to topics, and reported with volume, cost, tokens, errors, latency, and online evaluations. | Generic hierarchical semantic grouping and additive metric rollups are not novel. | No verified source-linked process/file/network responsibility, arbitrary conserved operation corpus, or user-selected stack field sequence. |
| **LangSmith Insights** | Traces are hierarchically categorized, including user-declared categories, and receive aggregate error, latency, cost, feedback, and extracted attributes. | A reviewer can fairly ask whether AgentProf is an offline/open version of an existing product feature. | The documented unit is a trace; the paper's strongest distinction is lower-level effect responsibility and selectable operation-level projections. |
| **TraceProbe** | 2,500 coding-agent trajectories are normalized into canonical actions and deterministic effects; setting-level process profiles report workflow phases, tokens, duration, failed work, and milestones. | The paper cannot claim first canonical agent operations, first resource-aware process profile, or first cross-run process comparison. This is the closest current academic vocabulary/capability neighbor. | Coding-specific deterministic diagnostics and reference comparisons, rather than arbitrary additive cross-layer effects and query-time field stacks. |
| **WebGraphEval** | 4,768 trajectories from six web agents are merged into weighted action graphs with recurring behavior, reward propagation, redundancy, inefficiency, and critical-decision analysis. | Weighted recurring-action representations and population-level trajectory structure are prior art. | Task-specific outcome graphs, not heterogeneous profiler samples with exact resource conservation or selectable field projections. |
| **Hodoscope** | Cross-group behavior distributions surface real unknown vulnerabilities, reduce review effort 6–23x, and improve some monitoring prompts. | It is a materially stronger inspection/actionability precedent than AgentProf's current MAP-only main presentation. | It compares behavior distributions for unknown misbehavior discovery rather than attributing arbitrary additive resources across layers. |
| **TraceGraph** | Shared action-observation landscapes expose traps and feed a recovery policy that raises resolved rate on fired SWE-bench subsets. | It sets a stronger analysis-to-intervention bar; AgentProf cannot imply repair or downstream agent improvement. | Outcome-informed task graphs, not a general cross-layer resource profiler. |
| **OpenTelemetry Profiles** | The alpha profile signal is a pprof superset, supports lossless pprof conversion, and can link samples directly to traces/spans. | pprof compatibility and profile/trace linkage are infrastructure, not scientific novelty. | Deriving agent semantic responsibility units and query-time hierarchies remains outside the standard. |

I found no verified source that combines all of AgentProf's surviving joint
capabilities. That absence makes the composite defensible, but combination
novelty is fragile: the paper must explain the causal necessity of the
combination rather than enumerate six features.

## Evaluation audit by fixed RQ

### RQ1 — Does semantic profiling improve resource attribution?

**Judgment: conditionally answered within the declared scope, but the current
term “resource attribution” compresses two different constructs.**

The 20-task AgentSight experiment establishes scoped source lineage and capture
correctness: 1,520/1,574 in-scope effects are recovered, all 1,629 controls are
rejected, and all admitted samples and category totals are conserved by
AgentProf. This is direct evidence for the cross-layer input edge.

CodeTraceBench ordinary B-cubed measures agreement between predicted
responsibility partitions and human stages. The gain from raw action 0.541 to
recurrence 0.649 is real and positive across four frameworks, while phase-only
is statistically indistinguishable at 0.654. This supports semantic stage
responsibility over raw operation identity; it does not independently prove
that recurrence is uniquely correct or that every token is causally assigned
to its one true phase. The paper mostly acknowledges this.

The RQ is acceptable if the manuscript explicitly presents the answer as a
two-edge chain: scoped effect lineage plus lossless folding, followed by
standard partition agreement for the responsibility units. B-cubed alone must
not be described as a direct resource-ground-truth metric. No new metric is
needed.

### RQ2 — Does profiler output correspond to real problems?

**Judgment: answered positively against raw action on three complete public
workloads; the strongest mechanism evidence is present but under-promoted.**

Per-query AP and workload MAP are the right standard primary metrics. Semantic
grouping improves over matched raw-action organization on AgentProcessBench,
HINTBench, and TraceElephant. This is a clean scoped answer to the written RQ.

The local-first analysis is more important than the current table makes clear.
Preserving every strict operation-local ordering and using semantic recurrence
only for ties reaches MAP .896/.545/.322, above local-only and semantic-only on
all three. Against an information- and composition-matched local-plus-raw
tie-breaker, the effect is positive on HINTBench and TraceElephant and
indistinguishable on AgentProcessBench. This directly defeats the explanation
that semantic grouping merely overrides stronger local evidence, while honestly
showing where raw and semantic refinement are equivalent. Its adaptive status
must remain visible.

Step 0019's fixed reader is useful but only supporting: recall improves on 5/6
tasks and precision on 4/6, yet inspected work is higher on 4/6, there is one
model, only six related tasks, and no matched raw-action packet. It does not
establish human productivity, lower work, repair, or universal view dominance.

### RQ3 — How accurate are the tags?

**Judgment: answered on the named populations and constructs, not as a
universal tagger guarantee.**

The section correctly separates literal multiclass identities from
permutation-invariant partitions and exact boundaries. Macro-F1/accuracy for
task and action names, V-measure and ordinary B-cubed for partitions, and exact
adjacent-boundary precision/recall/F1 for structure are construct-matched
standard measures. The strongest coherent structural evidence is the complete
OSWorld-Human population: label-free recurrence reaches 0.680 boundary F1 and
0.786 B-cubed F1, above simple controls and below supervised/reference-calibrated
comparators.

The subsection remains vulnerable to looking like a collection of unrelated
backends: TF-IDF/K-means, mapping-derived phases, Qwen task classification, Qwen
action classification, supervised Naive Bayes, and recurrence. The 49-operation
Mind2Web sample is especially weak, and majority class is a weak literal-label
baseline. This is not a demand for more baselines or another tag experiment.
The minimum repair is to state that RQ3 validates the pluggable field interface
through representative literal and structural modes, not one universal
induction algorithm. The text should also make explicit that the evaluated
Qwen3.6-27B configuration is a named backend using the same interface, whereas
the implementation paragraph's quantized 3B model is an example, not the exact
evaluated model.

### RQ4 — What is the profiling cost?

**Judgment: answered for profile construction, not end-to-end observability.**

The complete public workloads, three-run medians, throughput, peak RSS, and
semantic-versus-raw comparison are appropriate. Processing 27,765 operations in
1.17 seconds is adequate for the stated offline construction path. The explicit
exclusion of capture, source adaptation, and tag generation prevents a broad
end-to-end overhead claim. The abstract and conclusion should consistently say
“profile construction” when using the 1.17-second result. No additional cost
run is acceptance-changing.

## Metric and construct validity

| Measurement | Classification | Construct judgment |
|---|---|---|
| Per-query AP / workload MAP | Standard primary ranking metrics | Correct for independently annotated problem ranking. |
| Macro-F1 / accuracy | Standard classification metrics | Correct for literal task/action labels; macro-F1 should remain primary under imbalance. |
| V-measure | Standard external clustering metric | Correct for permutation-invariant partitions, not literal label names. |
| Ordinary B-cubed P/R/F1 | Standard partition/coreference metric | Correct for group agreement and fragmentation/merging, not direct resource truth. |
| Exact adjacent-boundary P/R/F1 | Standard metric family with a paper-declared adjacency unit | Correct because the unit and exact-match rule are stated. |
| Token-weighted B-cubed | Published weighting adaptation, non-default | Correctly secondary; it must not be presented as ordinary B-cubed. |
| Recall@20% / fixed-reader recall and precision | Standard metric families under project-defined protocols | Suitable only as secondary decision evidence; protocol customness must remain explicit. |
| Runtime, throughput, peak RSS | Standard systems measurements | Correct for fixed-input construction cost; insufficient for excluded capture/tag-generation cost. |

The current problem is not lack of standard metrics. Adding ARI, NMI, another
cutoff score, another inspection metric, or a composite would dilute the paper.
The remaining issue is interpretation: each standard metric must authorize only
its measured construct.

## Matched raw-action reader decision

**Do not require a matched raw-action reader extension in the next cycle.**

The current standard-MAP experiment already compares semantic and raw-action
organization over three complete public populations. Step 0037 further compares
local-plus-semantic with the exactly composition-matched local-plus-raw
tie-breaker. Those are more direct, larger, and more standard answers to RQ2
than another six-task LLM-reader run.

Extending Step 0019 would remain adaptive to already observed tasks, would still
use one artificial reader rather than a human or repair outcome, and would need
an operation-matched rather than group-matched inspection budget to avoid the
existing work confound. Even a positive result would not answer the unique
cross-layer novelty question. It is therefore not an acceptance-changing use of
the next experiment slot.

Only if the rewritten paper insists on a new claim that semantic profiles
reduce analyst inspection should a reader extension be admitted. In that case,
reuse the existing R315 trajectories, add a raw-action view, match the number of
underlying inspected operations rather than the number of groups, keep the same
reader and prompt, and report ordinary precision/recall at that declared budget.
That is a conditional future route, not a current must-fix.

## Severity-ranked findings

### Must-fix 1 — Major, novelty and scientific framing: the paper does not visibly defend the surviving composite against the closest July 2026 frontier

**Paper locations:** Introduction's existing-tool gap, the three-paragraph
Related Work, contribution list, and conclusion.

**Failure:** A reviewer can currently reduce the contribution to semantic trace
clustering plus pprof because the paper cites Datadog/LangSmith but omits the
closest academic process-profile/action-graph work and OpenTelemetry Profiles.
The current statement that existing tools do not link effects and aggregate
them into selectable pprof profiles is precise, but the paper does not explain
why that conjunction matters scientifically.

**Primary evidence:** Datadog Patterns and LangSmith Insights already supply
hierarchical cross-trace categories with cost/error/latency/evaluation rollups;
TraceProbe supplies canonical effects and resource-aware process profiles;
WebGraphEval supplies weighted recurring action graphs; OpenTelemetry Profiles
supplies pprof/trace linkage; Hodoscope and TraceGraph supply stronger downstream
consequence precedents.

**Route:** `WRITE_GATE`, not a new experiment.

**Minimum repair:** Replace generic Related Work lists with a concise
claim-oriented comparison covering at least TraceProbe, WebGraphEval,
Hodoscope/TraceGraph, Datadog/LangSmith, and OpenTelemetry Profiles. Explicitly
concede that grouping, profile naming, pprof export, and trace/profile linkage
are prior components. State the surviving principle as conserved cross-layer
semantic responsibility with selectable operation-stack projections. Preserve
the exact thesis and four RQs.

### Must-fix 2 — Major, evidence/evaluation: Table 2 hides the strongest already-completed baseline test

**Paper location:** RQ2 Table 2 and its following local-first paragraph.

**Failure:** The headline table compares semantic grouping only with raw-action
grouping, although the paper itself shows that operation-local evidence is a
stronger alternative. A skeptical reviewer can reject on a weak-baseline
reading before reaching the post-hoc prose.

**Evidence:** The completed local-first comparison uses identical operations,
local scores, composition, and budgets. It beats local-only and semantic-only
on all three workloads and beats local-plus-raw on HINTBench and TraceElephant,
while AgentProcessBench is correctly inconclusive. This is the mechanism result
needed to answer the baseline objection; it already exists and has been
independently reconstructed.

**Route:** `WRITE_GATE` using existing evidence.

**Minimum repair:** Make the local-first/local-plus-raw/local-only comparison
visible in Table 2 or an equally prominent compact table, retain the adaptive
label, and state the one-line mechanism: semantic recurrence refines rather
than overrides local diagnostic evidence. Do not claim all-workload dominance
or untouched confirmation. Do not add another score, model, or benchmark.

### Must-fix 3 — Major, global logic/construct validity: the four RQ answers need one explicit evidence-to-claim synthesis

**Paper locations:** end of each RQ, Scope and Limitations, abstract, and
conclusion.

**Failure:** The individual measurements are mostly valid, but the current
seven-page argument leaves readers to infer how capture correctness,
partition agreement, problem ranking, tag recovery, and construction cost join
into the paper-level thesis. This makes RQ1 look like B-cubed is resource truth,
RQ3 look like a metric/backend collection, and RQ4 look broader than its
construction-only scope.

**Route:** `WRITE_GATE`.

**Minimum repair:** Add one compact synthesis paragraph or contribution-to-RQ
mapping: (1) RQ1 verifies scoped lineage/conservation and responsibility
partition agreement; (2) RQ2 verifies problem ranking and the local-evidence
refinement mechanism; (3) RQ3 verifies literal and structural field-generation
modes on named populations; and (4) RQ4 verifies fixed-input profile
construction. This preserves the ambitious thesis while preventing metric
overinterpretation.

## Minor findings that do not justify another gate

- Figure 1 demonstrates three projections but its labels are too small at AAAI
  print size and it does not call out the reported 8th-versus-93rd ranking
  reversal. Adding two annotations to the existing figure would improve the
  artifact-to-insight connection without a new experiment.
- The system name AgentProf and executable `agentpprof` are probably intentional
  but should be related once explicitly.
- The Related Work can absorb the new sources by replacing generic product
  lists; it need not become a long survey.
- The conclusion is memorable but too short to carry the composite novelty or
  four-RQ evidence chain. One additional evidence-bearing sentence would help,
  provided it does not narrow or replace the thesis.

## Terms and concepts that can be reduced

The two core terms—**operation** and **operation stack**—are load-bearing and
should remain. “Semantic operation stack model” can remain as the name of their
combination. “Intent attribution,” “label-free recurrence,” and
“reference-calibrated recurrence” are supporting mechanisms and should not be
promoted into independent contributions. The paper should avoid adding names
for the local-first ranking, novelty composite, evidence chain, or RQ
subconstructs.

## Largest claim worth defending

The largest credible claim is the existing one, made concrete rather than
smaller:

> Agent observability needs profiling, not only debugging, because recurring
> responsibility for additive agent and system effects cannot be recovered from
> one execution tree alone; a conserved operation corpus and selectable semantic
> operation stacks make that responsibility queryable across runs and improve
> independently annotated problem prioritization.

The current evidence can support this after the three WRITE repairs above. It
does not yet support first cross-run agent analysis, universal tag accuracy,
reduced human work, automatic repair, or universal superiority over every
semantic/native view.

## Final routing

**Route: `WRITE_GATE`, then one fresh full-paper review. Do not admit a new
experiment at this point.**

The current paper is not submission-ready, so the verdict remains weak reject.
However, all acceptance-changing scientific evidence requested by this review
already exists in the repository. The next cycle should:

1. repair the closest-work boundary without shrinking the thesis;
2. promote the existing local-first matched baseline evidence;
3. synthesize the four scoped RQ answers into the joint contribution; and
4. rerun a genuinely independent whole-paper review against the revised PDF.

If that rereview still finds no direct causal connection between cross-layer
responsibility and an AI-agent decision, only then should the experiment gate
consider one existing-trajectory consequence test. It must not create a new
algorithm, RQ, metric suite, benchmark, or story.

## Completion assessment and remaining uncertainty

This independent review is complete. It supplies a score, verdict, source-
grounded novelty attack, fixed-RQ audit, metric audit, matched-reader decision,
and minimal routing. Residual uncertainty comes from two facts: Datadog and
LangSmith are proprietary products whose documentation proves capability but
not an information-matched numerical baseline, and several closest 2026 papers
are very recent preprints. Those facts weaken demands for direct reproduction
but do not remove their force as novelty and consequence precedents.

No paper, skill, submodule, canonical memory, code, experiment artifact, or Git
state was changed by this review.
