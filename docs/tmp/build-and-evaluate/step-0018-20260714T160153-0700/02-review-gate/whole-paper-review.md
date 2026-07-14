# Independent AAAI-27 Whole-Paper Review

## Verdict

- **Overall score:** 4/10 — Weak Reject
- **Confidence:** 4/5
- **Submission readiness:** not yet submission-ready
- **Paper type:** incomplete but promising
- **Format:** the current PDF appears compliant with AAAI-27's seven content
  pages plus references allowance; the reproducibility checklist is unfilled.

The paper is promising and unusually evidence-rich, but its central empirical
conclusion is stronger than its current experiments support, and the novelty
comparison misses several close systems. The durable idea is good: agent
observability can aggregate conserved resources and effects through reusable
semantic responsibility fields rather than limit analysis to individual
execution traces. The paper is held back by evidence-to-claim alignment, not a
weak motivating problem.

## Summary

AgentProf converts heterogeneous agent events into uniform weighted operations,
derives semantic fields, projects operations onto query-selected hierarchical
stacks, and emits pprof-compatible profiles. It evaluates source-linked
system-effect attribution, semantic separation and problem concentration,
tag/group fidelity, and offline construction cost.

The simplest formulation of the contribution is:

> AgentProf propagates semantic responsibility into source-linked system
> effects and folds conserved additive measures through selectable
> operation-stack projections.

That is clearer and more defensible than the broad claim that agent
observability presently lacks profiling. Current systems already perform
cross-trace semantic aggregation and phase profiling; AgentProf's distinctive
claim is the conjunction of source-linked cross-layer effects, conservation,
query-selectable semantic hierarchy, and profiler-compatible output.

## Strengths

1. The exact thesis, “Agent observability needs profiling, not only debugging,”
   is important and memorable.
2. Uniform operations plus query-time field stacks form a coherent, simple,
   extensible representation compatible with existing profiling infrastructure.
3. RQ1's 20-task lineage experiment has meaningful concurrent controls, 100%
   precision, 96.6% recall, and exact conservation during folding.
4. The evaluation uses real trajectories and many public agent families,
   reports controls, separates held-out labels from construction, and discloses
   important limitations.
5. Offline operation JSONL, pprof export, local processing, and pluggable field
   derivation form a plausible tool rather than only an analysis prototype.
6. The paper explicitly states that RQ1's local-model tags are declared
   categories, that the RQ3 supervised predictor is not the Rust inducer, and
   that phase/action/literal tag accuracy remains untested.

## Ranked Scientific Objections

### Blocker 1 — RQ2's Aggregate Positive Answer Exceeds Its Outcomes

The paper concludes that three complete workloads answer RQ2 positively, but
the registered results are mixed:

- AgentProcessBench improves macro AP from .556 to .588, while session and step
  groupings reach .599 and .777.
- HINTBench improves Work@80 numerically, but the interval against raw action
  crosses zero.
- TraceElephant is strong at descriptive Work@50, while prospective Work@80 is
  inconclusive and worse numerically than raw.

The individual disclosures are honest; the cumulative synthesis is not. It
combines different metrics and operating points after the fact. The strongest
alternative explanation is grouping granularity plus the supplied step-risk
signal rather than semantic operation stacks specifically.

Required repair: use workload-specific conclusions and a predeclared rule for
an RQ-level answer rather than aggregate heterogeneous AP, Work@80, and
descriptive Work@50 into universal positive evidence.

### Blocker 2 — The Headline Boundary Result Can Be Misread As Built-In Inducer Evidence

The .739 boundary F1 and .816 B-cubed result comes from a pre-specified
supervised Bernoulli Naive Bayes predictor, not the built-in Rust inducer. The
body says so, but the abstract and contribution narrative place the result near
pluggable algorithms and automatic construction.

Step 0018 confirms that cap removal improves the built-in inducer (.472/.672
versus .423/.616) without validating it against the strongest simple controls
(.645/.678). The negative development numbers need not enter the reader-facing
paper, but method identity must be exact.

Required repair: say in the Abstract and Introduction that the headline result
validates an optional supervised field-construction backend, not the built-in
unsupervised Rust inducer. Describe the latter as exploratory and make its
current/default cap behavior reproducible.

### Major 1 — RQ3 Does Not Yet Answer Every Component Of “Tag Accuracy”

The tags driving RQ1's 90.4%-to-36.7% result come from a local 3B model but are
treated as declared categories. RQ3 instead evaluates supervised group
boundaries on OSWorld-Human and permutation-invariant TF-IDF/K-Means task
partitions on Mind2Web and ScienceWorld. It leaves phase, action, literal tag
names, and the real-trajectory local tagger untested.

Required repair: preserve the fixed RQ but answer it component by component,
distinguishing task-partition fidelity, boundary fidelity, literal labels, and
unmeasured phase/action components.

### Major 2 — Closest-Work Comparison Is Incomplete

The related-work section is too short for the claimed missing layer. Material
closest systems and scholarship include:

- [AWS agent profiling guidance](https://docs.aws.amazon.com/wellarchitected/latest/agentic-ai-lens/agentperf01-bp03.html),
  which aggregates trace telemetry into phase contributions and task/model
  pivots;
- [NVIDIA NeMo Agent Toolkit profiler](https://docs.nvidia.com/nemo/agent-toolkit/1.4/improve-workflows/profiler.html),
  which collects per-invocation token/time/call data and performs nested-stack
  bottleneck analysis;
- [LangSmith Insights](https://docs.langchain.com/langsmith/insights) and
  [Datadog Patterns](https://docs.datadoghq.com/llm_observability/monitoring/patterns/),
  which derive cross-trace categories and aggregate error, latency, cost, and
  evaluation signals;
- [Agentic CLEAR](https://arxiv.org/abs/2605.22608), which aggregates recurrent
  failure patterns over trace collections;
- [Agentic AI Process Observability](https://ceur-ws.org/Vol-4087/paper3-Long.pdf),
  which aggregates process variants, frequencies, and split points;
- [AgentGraph](https://ojs.aaai.org/index.php/AAAI/article/view/42393), which
  links agents, tasks, tools, inputs, outputs, and trace spans; and
- [AgentDiagnose](https://aclanthology.org/2025.emnlp-demos.15/), which ties
  trajectory diagnostics to downstream filtering and performance improvement.

These works do not erase AgentProf's novelty. They invalidate novelty based
only on profiling, semantic aggregation, or hierarchical grouping. The
defensible novelty is the combination of conserved additive cross-layer
effects, source linkage, selectable responsibility projections, and pprof
compatibility.

### Major 3 — RQ4 Measures Offline Construction, Not All Profiling Cost

The 1.17-second result excludes capture, source adaptation, and current tag
generation; it uses five natural sizes and one machine; 464.5 MiB for 27,765
operations is notable; and the cache result belongs to predecessor AgentFlame.

Required repair: present RQ4 as post-session parse/construct/fold/serialize
cost, separate field-derivation cost, qualify predictable scaling, and explain
the memory footprint.

### Major 4 — Reproducibility And Private-Data Reporting Need Precision

The private 325-trajectory result needs the exact model checkpoint,
quantization, prompt, grammar, decoding, cache, mappings, supervised features,
threshold selection, conversion scripts, and a privacy/data statement. The
paper's AgentProcessBench risk-signal protocol is derived rather than the
benchmark's standard headline protocol and should be identified as such.

### Major 5 — The AI Method Is Weaker Than The Systems Integration

Bernoulli Naive Bayes, TF-IDF/K-Means, and the local 3B tagger are standard or
unvalidated; the built-in inducer does not beat simple controls. The paper is
currently strongest as a systems representation and profiling interface. For
AAAI, the AI claim should be reliable target-blind semantic responsibility
attribution across agent families, which needs stronger direct evidence.

## Four-RQ Audit

| RQ | Assessment | Reason |
|---|---|---|
| RQ1 | Partially positive | Source lineage, control rejection, conservation, and multi-view projection are strong; semantic improvement is conditional on declared unvalidated tags. |
| RQ2 | Mixed/inconclusive | AgentProcess gives a small isolated gain, HINT versus raw is inconclusive, and Trace's strong result is at a descriptive point. |
| RQ3 | Partially positive | Positive evidence covers one supervised boundary predictor and task partitions, not the built-in inducer, local 3B tags, phase/action labels, or literal names. |
| RQ4 | Answered for current offline construction | Capture and current semantic derivation are excluded. |

The fixed thesis and four RQs remain scientifically sound. They should not be
replaced or narrowed; each should receive an evidence-calibrated answer.

## Clarity And Presentation

- Figure 1 is too dense and needs two or three annotated takeaways.
- Figure 2 does not show source-lineage/tag inheritance or distinguish explicit
  fields, the supervised predictor, and the built-in inducer.
- Table 1 combines heterogeneous metrics and operating points.
- “Tag accuracy” conflates literal labels, partitions, mappings, and boundaries.
- The Abstract is number-dense and compresses distinct mechanisms.
- The manuscript is otherwise compact and its RQ organization is strong.

## Deadline-Prioritized Repairs

Before the July 21 abstract deadline:

1. remove the implication that all three RQ2 workloads positively validate
   semantic problem concentration;
2. identify .739/.816 as an optional supervised boundary backend;
3. center novelty on source-linked, conserved, selectable semantic-effect
   projections rather than absence of all existing profiling/aggregation; and
4. retain the thesis/title while making the empirical synthesis precise.

Before the July 28 paper deadline:

1. repair the RQ2 synthesis with workload-specific outcomes and a predeclared
   cumulative criterion;
2. add and distinguish the closest work above;
3. add a compact mechanism-to-evidence mapping;
4. make defaults and experimental configurations reproducible;
5. answer RQ3 component by component;
6. scope RQ4 and memory cost;
7. improve Figures 1--2 and Table 1; and
8. complete the reproducibility checklist and privacy/data/artifact statements.

## Reviewer's Highest-Value Experiment

The reviewer recommends one pre-registered end-to-end RQ2 comparison against
the closest current profiler on shared traces: AgentProf, NVIDIA NeMo Agent
Toolkit nested-stack/profile output, and native/raw grouping on one held-out
public workload plus one real AgentSight workload, with matched visible
information, problem signal, ranking, and Work@80.

This proposal attacks RQ2's mixed evidence and the missing closest-system
baseline simultaneously. Another OSWorld depth/penalty/threshold sweep would
not improve the paper.

## Prior-Verdict Exposure

The reviewer formed the initial paper-only verdict after reading the complete
manuscript and before reading the Step 0018 verdict. It later saw Step 0018's
`CONTRADICTED` result and some historical result labels. It did not intentionally
read a prior whole-paper verdict; the primary RQ2 and novelty objections were
already apparent from the manuscript.

## Root Feasibility Disposition

The reviewer is correct that NeMo is the closest executable profiler and must
enter the novelty comparison. Its proposed same-trace execution is not admitted
unchanged. NVIDIA's official profiler runs through `nat eval`, instruments a
NeMo-supported workflow with callbacks, and then produces
`all_requests_profiler_traces.json`, nested-stack bottleneck reports, and usage
metrics. The current official interface documents trace export, not importing
arbitrary existing AgentSight/OTel/public trajectory files into the profiler.
Therefore a shared-input experiment would require a new NeMo workflow/adapter
or a second execution path; it would not be the proposed one-variable replay.

The next plan must retain the reviewer's scientific target while using a fair,
available comparison. The highest-value feasible route is the paused fixed RQ2
reader experiment over existing R315 packets, which already compares AgentProf
profiles with native/raw views under one downstream decision and one fixed
reader. It directly tests whether the added semantic projection changes
actionable diagnosis without inventing a NeMo importer. NeMo, AWS, Agentic
CLEAR, process observability, and AgentGraph must still enter Related Work and
the capability comparison. Any later executable NeMo experiment must first
demonstrate a genuinely shared real workflow and matched information budget in
its plan; it is not a prerequisite for resuming the existing RQ2 evidence path.
