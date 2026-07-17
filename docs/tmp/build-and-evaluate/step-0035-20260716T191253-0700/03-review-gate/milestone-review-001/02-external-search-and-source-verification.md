# REVIEW 2/4 — External Search and Source Verification

**Started:** 2026-07-17T03:41:00-07:00
**Completed:** 2026-07-17T05:18:00-07:00
**Parent:** Step 0035, `REVIEW_GATE / milestone-review-001`
**Skill:** `iter-review-critique`
**Target:** AAAI 2027 Main Technical Track, cross-domain systems + AI/ML

## Objective

Resolve the external uncertainties raised by the blind full-paper read before
editing the paper or selecting another experiment. The search asks four
questions:

1. Do current products and prior systems already provide cross-run semantic
   profiling, hierarchical aggregation, or pprof-style tag projection?
2. Are the signals used in RQ2 independent predictions available before the
   scorer reads the benchmark target, or are they target-label leakage?
3. What do the public RQ1/RQ3 annotations and standard metrics actually
   establish?
4. Does an existing, genuinely untouched confirmation population already exist,
   and what does AAAI-27 require in the main paper?

This node is source verification, not a WRITE or EXPERIMENT node. It changes no
paper, code, algorithm, benchmark, or result.

## Search Method

Three independent read-only reviewers used the complete
`iter-review-critique` skill and its systems, AI/ML, cross-domain, and research-
taste references. They separately investigated:

- closest products, profiler/trace systems, standards, and process mining;
- AgentProcessBench, HINTBench, and TraceElephant protocols and implementation;
- CodeTraceBench, OSWorld-Human, RQ3 classification sources, standard metrics,
  sequence baselines, and AAAI-27 rules.

The root independently checked the current paper, experiment adapters, retained
raw outputs, the AgentSight paper, and the official AAAI-27 call. Sources were
restricted to official product documentation, official repositories and data
cards, original papers, publishers, conference pages, and standard metric
definitions. Marketing summaries, secondary blogs, Reddit, Wikipedia, and
search-result snippets were excluded from scientific conclusions.

Representative queries included:

- `LangSmith Insights cluster traces official docs semantic clusters`
- `Datadog LLM Observability Patterns official semantic hierarchy`
- `NeMo Agent Toolkit profiler nested stack bottleneck official`
- `pprof tagroot tagleaf labels official`
- `PerfettoSQL group_by SUM trace official`
- `Agentic AI Process Observability process mining trajectories`
- `AgentProcessBench judge predictions step labels official`
- `HINTBench evaluate.py risk_steps official`
- `TraceElephant All-at-Once localization with ground truth protocol`
- `CodeTraceBench stage annotation official`
- `OSWorld-Human grouped action same observation official`
- `AutoPlait TICC categorical HMM sequence segmentation`
- `B-cubed weighted Bcubed original definition`
- `AAAI-27 main technical track 7 pages references reproducibility`

Every conclusion below distinguishes source fact from reviewer inference.

## Finding 1 — Broad Cross-Run Profiling Novelty Does Not Hold

### Product and infrastructure capabilities

| Source | Verified capability | Capability not found in the source |
|---|---|---|
| [LangSmith Insights](https://docs.langchain.com/langsmith/insights) | Automatically summarizes and categorizes many traces into categories/subcategories; reports frequency, error rate, latency, cost, feedback, and underlying traces; categories can be reused. | No documented external OS-effect-to-action join, additive conservation invariant, arbitrary ordered operation stack, or pprof export. |
| [Datadog LLM Observability Patterns](https://docs.datadoghq.com/llm_observability/monitoring/patterns/) | Embeds and clusters production LLM interactions, assigns LLM labels, builds a parent-child topic hierarchy, shows volume/share/coherence, filters failed evaluations, and tracks changes over time. | No documented system-effect attribution, additive resource-conservation contract, ordered semantic responsibility stack, or pprof output. |
| [NeMo Agent Toolkit Profiler](https://docs.nvidia.com/nemo/agent-toolkit/1.4/improve-workflows/profiler.html) and [repository](https://github.com/NVIDIA/NeMo-Agent-Toolkit) | Records LLM/tool invocations, tokens, latency, throughput, confidence intervals, nested-stack bottlenecks, concurrency, workflow fingerprints, and recurring prefixes over evaluation runs. | It profiles instrumented/decorated supported workflows; it does not document AgentSight-style external system-effect attribution or query-time alternative semantic responsibility projections. |
| [Google pprof](https://github.com/google/pprof/blob/main/doc/README.md) | Carries numeric sample values and labels, merges profiles, filters/splits by tags, and promotes label values to pseudo frames with `tagroot`/`tagleaf`. | It does not derive agent semantics, join system effects to actions, or learn recurring operations. |
| [Perfetto Trace Processor and PerfettoSQL](https://perfetto.dev/docs/analysis/perfetto-sql-getting-started) | Imports trace tables, supports reusable SQL views/functions and derived metrics, and performs filter/group-by plus SUM/COUNT and other aggregates at scale. | It does not automatically construct agent semantic fields or recurrence groups; attribution is only as good as the imported trace relations. |
| [OpenTelemetry GenAI conventions](https://github.com/open-telemetry/semantic-conventions-genai) and [OpenInference](https://arize-ai.github.io/openinference/spec/semantic_conventions.html) | Standardize agent, LLM, chain, and tool span kinds; agent/session/graph identifiers; and token/cost attributes. | They specify representation, not automatic cross-run profiling or external effect attribution. |
| [Agentic AI Process Observability](https://arxiv.org/abs/2505.20127) and [workshop paper](https://ceur-ws.org/Vol-4087/paper3-Long.pdf) | Converts agent trajectories to event logs and applies process/causal discovery across runs to find dependencies, variants, and split points. | It does not document additive resource responsibility projected into standard profiler stacks. |

Traditional systems literature also establishes strong precedent for pieces of
the proposed pipeline: [lprof](https://www.usenix.org/conference/osdi14/technical-sessions/presentation/zhao)
reconstructs request flows from runtime logs; [Pivot
Tracing](https://www.microsoft.com/en-us/research/publication/pivot-tracing-dynamic-causal-monitoring-for-distributed-systems-2/)
performs causal joins plus arbitrary select/filter/group-by; [Spectroscope](https://www.usenix.org/events/nsdi11/tech/full_papers/Sambasivan.pdf)
compares request-flow categories across populations; and
[CRISP](https://www.usenix.org/conference/atc22/presentation/zhang-zhizhou)
aggregates critical paths across RPC traces and visualizes them with flame
graphs.

### Ownership boundary with AgentSight

The [AgentSight paper](https://arxiv.org/abs/2508.02736) explicitly contributes
boundary tracing, capture of LLM traffic and kernel effects, process-lineage and
temporal/content correlation, and cross-process intent/effect joining. Therefore
those mechanisms cannot be claimed as new AgentProf contributions. AgentProf
begins after a native history or source adapter has produced records, including
records already causally joined by AgentSight.

### Reviewer inference

The blind review's B2 attack is confirmed. None of the following can serve as
an AgentProf novelty claim:

- first profiling system for agents;
- first cross-trace semantic categories or hierarchy;
- first aggregation of token, latency, cost, or evaluation signals;
- first nested workflow bottleneck view;
- first use of pprof labels or pseudo frames;
- first causal intent/effect join; or
- first process/recurrence discovery over agent trajectories.

The narrowest externally defensible joint boundary is:

> AgentProf turns heterogeneous, optionally causally joined agent histories
> into additive operations whose same measured effects can be conservatively
> reprojected at query time through alternative semantic responsibility
> hierarchies and consumed by standard profilers.

No searched source documents all four of external/no-SDK effect attribution,
unified additive operations, query-time alternative semantic projections, and
standard pprof/flame output. That absence is not yet sufficient novelty proof:
the paper still must demonstrate a decision consequence or invariant that
ordinary trace clustering, SQL group-by, nested workflow profiling, or pprof
tag promotion does not provide.

**Attack-map update:** B2 remains open at blocker/major severity. The current
paper's Related Work is too compressed and occasionally assigns AgentSight's
join to AgentProf. NeMo is the strongest runnable agent-profiler comparator;
PerfettoSQL and pprof tags are the strongest expressiveness baselines; process
mining supplies the closest recurrence family.

## Finding 2 — RQ2 Does Not Read Scorer Gold, but It Aggregates External Signals

### AgentProcessBench

The [official repository](https://github.com/RUCBM/AgentProcessBench),
[project page](https://rucbm.github.io/AgentProcessBench-Homepage/), official
[judge program](https://raw.githubusercontent.com/RUCBM/AgentProcessBench/main/eval/llm_annotation.py),
and [comparison program](https://raw.githubusercontent.com/RUCBM/AgentProcessBench/main/eval/compare.py)
show that the release contains step predictions from 20 judge models. The
current experiment assigns each operation an external risk equal to the
fraction of available non-null judge predictions equal to harmful (`-1`), then
averages that fixed signal within each candidate group. Human step labels enter
only the final scorer.

**Fact:** the ranking signal is an officially released, target-label-blind
ensemble prediction, not scorer gold.
**Inference:** AgentProf reorganizes and smooths an external process-reward/
judge signal; it does not independently discover harmful steps. The official
benchmark metrics are StepAcc and FirstErrAcc, while AgentProf's trajectory AP/
MAP is a derived profile-ranking protocol.

### HINTBench

The [HINTBench paper](https://arxiv.org/abs/2604.13954) and official anonymous
[repository](https://anonymous.4open.science/r/HINTBench-B841),
[evaluator](https://anonymous.4open.science/api/repo/HINTBench-B841/file/eval/evaluate.py),
[test data](https://anonymous.4open.science/api/repo/HINTBench-B841/file/data/hintbench.json),
and [validation data](https://anonymous.4open.science/api/repo/HINTBench-B841/file/data/hintbench_val.json)
define risk detection and localization. The current experiment runs local
Qwen3.6-27B with the official prompt/parser over each complete trajectory. The
request excludes `is_risky`, `risk_labels`, target IDs, and target categories;
the generated `risk_steps` become the per-step `localizer_hit` signal. Gold test
targets are read only by the scorer. Gold labels for 80 validation trajectories
did select one of 24 predeclared field orders before the 536-test-trajectory
run.

**Fact:** the test ranking signal is a fresh official-style localizer output
that is blind to test gold; it is not a released prediction and not direct
target leakage.
**Inference:** the result includes a normal development-selection step and
measures how profile organization redistributes a fixed localizer signal. It
does not isolate zero-shot failure discovery by the profile itself. Official
HINTBench outcomes include risk-detection Macro-F1/Safe-F1/Unsafe-F1 and
localization recall/F1/Strict-F1.

### TraceElephant

The [official repository](https://github.com/TraceElephant/TraceElephant),
[inference program](https://github.com/TraceElephant/TraceElephant/blob/main/code/trace_locate/inference.py),
[prompt/data loader](https://github.com/TraceElephant/TraceElephant/blob/main/code/trace_locate/lib/utils.py),
[evaluator](https://github.com/TraceElephant/TraceElephant/blob/main/code/trace_locate/evaluate.py),
and [ACL paper](https://aclanthology.org/2026.acl-long.912.pdf) define an
All-at-Once trace localizer. The current reconstruction runs local Qwen3.6-27B
and produces one predicted agent/step per trace. It does not expose the scorer's
`mistake_agent` or `mistake_step`, but in the with-ground-truth setting it may
read the task reference answer or test outcome.

**Fact:** the prediction is not copied from the target annotation.
**Inference:** it is reference-assisted rather than fully oracle-free. Official
metrics are agent accuracy, step accuracy, and tolerance step accuracy. The
released workload contains failures only, so a clean-trajectory false-positive
rate is not available.

### Standard-metric consequence

[NIST/TREC](https://trec.nist.gov/presentations/TREC9/overview/tsld014.htm)
defines AP for a ranked query and MAP as the arithmetic mean across queries.
Therefore treating one target-bearing trajectory as a query and operations as
ranked items is a legitimate standard-IR mapping. It is nevertheless an
AgentProf-derived cross-benchmark protocol, not any source benchmark's official
primary task. Wilson group scores, Work@50/80, and the 20-judge ensemble are
protocol components or constructed signals, not standard metrics.

The correct two-stage construct is:

1. **Stage A, external signal quality:** report each benchmark's official
   localizer/judge metrics and assign that capability to the external model.
2. **Stage B, profile organization:** hold the signal fixed and compare atomic,
   raw-action, session, and operation-stack organization with standard MAP and
   one declared inspection-budget recall.

AgentProcessBench has 386 trajectories without a harmful target and HINTBench
has 136 test trajectories without a mapped target; these support clean any-
alert or false-positive-operation measurements. TraceElephant has no clean
population and should state `N/A`.

**Attack-map update:** the literal B1 charge that test gold creates the ranking
is rejected. A narrower construct-validity major remains: the paper currently
attributes too much diagnostic agency to AgentProf. Its evidence shows that a
semantic profile can redistribute a fixed external diagnostic signal more
usefully than matched raw-action grouping. It does not yet show independent
unknown-problem discovery.

## Finding 3 — RQ1 Measures Stage-Partition Agreement, Not Causal Resource Ownership

The [CodeTracer paper](https://arxiv.org/html/2604.11641v1),
[repository](https://github.com/NJU-LINK/CodeTracer), and
[CodeTraceBench data card](https://huggingface.co/datasets/NJU-LINK/CodeTraceBench)
show that executed commands define iterations and humans assign each step to
one of five workflow stages. Fifteen percent of the corpus was double-annotated;
the paper reports Cohen's kappa for error-critical steps. The official task
localizes erroneous stages/steps within the given segmentation and reports
step precision/recall/F1 and token cost. The source contains stage intervals,
not operation-level resource-responsibility labels, and it does not define the
paper's adapter-level allocation of provider tokens to operations.

The [original B-cubed definition](https://aclanthology.org/P98-1012/) computes
per-object overlap between predicted and gold clusters and averages these local
precision/recall quantities. The
[weighted B-cubed extension](https://pmc.ncbi.nlm.nih.gov/articles/PMC5103821/)
uses object weights both locally and globally; uniform weights reduce to the
ordinary form.

### Reviewer inference

- Ordinary B-cubed is a standard and appropriate measure of predicted-stage
  partition agreement.
- Token-weighted B-cubed is a literature-grounded resource-sensitive partition
  agreement: errors on token-heavy operations count more.
- Neither metric validates the causal owner of those tokens. The 494.9M token
  allocation is produced by the AgentProf adapter, not official ground truth.
- Phase-only B-cubed F1 (`0.654`) being statistically indistinguishable from
  recurrence (`0.649`) reinforces that this experiment validates semantic
  stage alignment over raw action identity, not a unique recurrence advantage.

**Attack-map update:** M1 is confirmed. The evidence is useful and should stay,
but reader-facing language must call it stage-partition agreement or resource-
sensitive stage-partition agreement rather than resource-attribution accuracy.
The fixed RQ1 remains unchanged; this finding distinguishes one tested
hypothesis from the entire RQ.

## Finding 4 — RQ3 References Are Narrower Than General Semantic Operations

### OSWorld-Human

The [OSWorld-Human paper](https://arxiv.org/abs/2506.16042) and
[repository](https://github.com/WukLab/osworld-human) provide 369 successful
human trajectories over nine applications. Consecutive actions belong to one
group when they can be executed correctly from the same visual observation or
screenshot; the purpose is to reduce observations, LLM calls, and latency. Two
CS graduate annotators performed two rounds and reconciled to consensus, but no
quantitative inter-annotator agreement is reported. Official outcomes are WES+
and WES-, not boundary F1 or B-cubed.

**Inference:** exact boundary F1 and B-cubed are standard, complementary
segmentation/partition metrics, but here their reference is specifically a
same-observation executable group. It is not generic semantic-stage ground
truth. The current 287/369 inclusion requires a clear 82-trajectory exclusion
and application-distribution account.

### AgentBoard and ASE action taxonomy

The [AgentBoard paper](https://proceedings.neurips.cc/paper_files/paper/2024/file/877b40688e330a0e2a3fc24084208dfa-Paper-Datasets_and_Benchmarks_Track.pdf)
and [repository](https://github.com/hkust-nlp/AgentBoard) evaluate agent success
and progress over nine environment-specific task directories. They do not
publish goal-to-task-family classification as an official task or split.

The [ASE 2025 trajectory study](https://software-lab.org/publications/ase2025_trajectories.pdf)
samples 40 trajectories from each of three software-engineering agents. Its
eight action categories were induced after inspecting trajectories; known tools
were mapped automatically, other actions manually, and 8.3% remained
unclassified and were excluded. It does not define an official action-
classification train/test split.

**Inference:** the fixed model's AgentBoard and ASE results are bounded literal-
label agreement measurements, not official benchmark leaderboards or evidence
of unseen-family generalization. Majority controls are weak. Matched baselines
should include text retrieval/embedding/classification controls, and the ASE
experiment should use leave-one-agent-out if it is made load-bearing.

**Attack-map update:** M3 remains major. Boundary F1 and B-cubed are not the
problem; reference construct, grouped split, coverage, and comparator strength
are.

## Finding 5 — No Existing Population Is Proven Untouched Confirmation

The current paper and history explicitly state that CodeTraceBench influenced
constructor selection and that the OSWorld-Human rule was adjusted after early
corpus results. Mind2Web/ScienceWorld, AgentBoard, and ASE provide task or
literal-label annotations, not group-boundary truth for recurrence. The 82
excluded OSWorld trajectories may be adapter-ineligible, and no provenance
audit establishes that unselected CodeTraceBench solved trajectories were never
examined.

Thus no current result may be relabeled as genuinely untouched confirmation.
Possible future populations are:

- a predeclared, never-loaded CodeTraceBench solved subset, which would be
  same-source confirmation rather than cross-domain confirmation;
- leave-one-application/snapshot-out OSWorld evaluation, which is stronger
  grouped generalization but remains post-hoc if the corpus already informed
  the method; or
- a new public, independently annotated sequence population, which is the
  strongest scientific option.

Closest standard sequence/process comparators include
[AutoPlait](https://www.cs.cmu.edu/~christos/PUBLICATIONS/14-sigmod-autoplait.pdf),
[TICC](https://stanford.edu/~boyd/papers/ticc.html),
[ruptures](https://github.com/deepcharles/ruptures), categorical HMMs, and
[PM4Py](https://github.com/process-intelligence-solutions/pm4py). A compact
future comparison should use recurrence, action/phase change, a categorical
HMM, PELT-RBF, and AutoPlait, with exact boundary F1, ordinary B-cubed F1, and
runtime. This is a baseline requirement, not authorization to replace the
current algorithm with an unrelated mechanism.

**Attack-map update:** B3 is confirmed and remains open. Repeated tuning on the
same two development populations cannot close it.

## Finding 6 — AAAI-27 Fit and Format

The official [AAAI-27 Main Technical Track
call](https://aaai.org/conference/aaai/aaai-27/main-technical-track-call/)
states:

- main content is limited to seven pages;
- total length is at most nine pages, with pages beyond seven reserved only for
  references;
- supplementary material may be submitted, but reviewers need not read it;
- evidence critical to evaluation must be in the main paper;
- authors must complete a reproducibility checklist; and
- submissions are evaluated for significance, novelty, soundness, relevance,
  clarity, and reproducibility, with integrative cross-area contributions
  explicitly in scope.

The current PDF is US Letter, nine pages, with technical content ending on page
7 and references occupying pages 7--9. It therefore satisfies the page-allocation
rule at this node. The deadline is July 28, 2026 AoE, with supplementary
material and code due July 31.

AAAI is a plausible target because the paper connects AI-agent behavior with
systems profiling and contains an automatic semantic grouping method. Format
compliance alone does not make it submission-ready: B2/B3 and the RQ2/RQ1
construct boundaries are scientific issues in the seven-page main body.

## Consolidated Attack-Map Disposition

| Blind attack | External disposition | Severity after verification |
|---|---|---|
| B1: test gold creates the RQ2 score | Literal charge rejected. All three localizers/judges produce predictions before scorer gold; TraceElephant is reference-assisted. | Major construct issue remains: aggregation of external diagnostic signal is not independent problem discovery. |
| B2: known group-by plus pseudo frames | Confirmed and strengthened by LangSmith, Datadog, NeMo, pprof, Perfetto, process mining, and prior trace systems. | Blocker/major until a clear joint invariant and decision consequence are demonstrated. |
| B3: no untouched recurrence confirmation | Confirmed; neither current boundary corpus is untouched. | Blocker for broad algorithmic generalization. |
| M1: B-cubed is not resource responsibility | Confirmed by CodeTraceBench and metric definitions. | Major wording/construct issue; does not remove RQ1. |
| M2: AgentSight owns causal joining | Confirmed. | Major novelty/ownership issue. |
| M3: mixed RQ3 constructs and weak controls | Confirmed. | Major; standard metrics are sound, but reference tasks and baselines are weak. |
| M4: core construction, not end-to-end cost | Unchanged; no source contradicts it. | Major but accurately disclosed in Scope. |
| M5: selected field order is not runtime ancestry | Strengthened by pprof/SQL/process-mining precedent. | Major conceptual distinction. |
| M6: breadth is mostly schema compatibility | Unchanged. | Major; no independent automatic-constructor confirmation. |
| M7: artifact decisions omitted from paper | AAAI requires critical evidence in the main paper and a reproducibility checklist. | Major within seven-page economy. |

## Implication for the Next Review Node

The external evidence does **not** authorize shrinking or replacing the fixed
thesis, story, contribution chain, or four RQs. It does require the full-paper
reread to answer three concrete questions:

1. Can the current seven-page paper accurately expose the ownership and
   construct boundaries without losing its large profiling thesis?
2. Which single experiment has the highest chance of changing the AAAI verdict:
   a standard same-signal RQ2 decomposition on existing complete artifacts, a
   closest-system/SQL baseline, or a recurrence confirmation/baseline test?
3. Can a current-algorithm refinement on existing trajectories be admitted as
   development evidence without pretending to close the untouched-confirmation
   blocker?

The likely immediate value is to reuse existing RQ2 artifacts for the official-
metric/same-signal decomposition and clean false-positive analysis, while an
algorithm experiment must be simple, explicitly post-hoc development, and
compared on standard boundary/B-cubed metrics. The next node will decide one
route after rereading the complete paper; no paper or experiment is changed in
this source-verification node.
