# External Search and Primary-Source Verification

**Timestamp:** 2026-07-23T23:16:24-07:00
**Parent:** Step 0076 REVIEW gate, milestone review 001
**Objective:** Test the blind attack map against current primary sources in
agent diagnosis, trajectory analysis, profiling, observability, and AAAI-27.

## Method and provenance

Search began after the blind report was formed. Search snippets were used only
for discovery. Evidence below comes from primary paper pages/PDF text,
archival proceedings, official product documentation, official specifications,
and the AAAI-27 call.

Representative queries covered:

- semantic agent behavior taxonomy and automatic trajectory annotation;
- hierarchical failure attribution over agent trajectories;
- cross-run trajectory profiling, diagnosis, and recovery;
- current agent observability category/metric rollups;
- profiler trace linkage and pprof compatibility;
- AAAI-27 main-track criteria and page limits.

The search was intentionally bounded to the closest same-claim and
same-consequence work; it was not a comprehensive literature survey.

## Primary-source findings

### ACT*ONOMY is the closest missing same-claim work

[ACT*ONOMY](https://arxiv.org/abs/2605.13625) introduces a three-level
hierarchy of 10 actions, 46 subactions, and 120 leaf categories, plus an
automatic quote-grounded pipeline for applying it to raw trajectories. It
compares behavior profiles across agents and across diverse trajectories and
surfaces failure-mode patterns.

**Consequence:** hierarchical semantic vocabulary, automatic trajectory
annotation, and cross-run behavior profiling cannot be claimed as new by
themselves. AgentProf's defensible distinction is variable-depth responsibility
intervals composed with source-call evidence, arbitrary additive conservation,
replay under multiple weights, and standard pprof output.

ACT*ONOMY is absent from both `main.tex` and `references.bib`. That omission is
a real novelty-review defect.

### CHIEF makes hierarchy construction an established diagnosis mechanism

[CHIEF](https://arxiv.org/abs/2602.23701) decomposes tasks into subtasks,
parses observation/thought/action/result structure, constructs a hierarchical
causal graph, and performs top-down plus counterfactual failure attribution.
It compares eight baselines, reports agent- and step-level accuracy, multiple
base models, token cost, and module ablations.

**Consequence:** semantic task/subtask hierarchy over intervals is not itself
novel. CHIEF is not a population profiler and uses diagnosis-specific inputs,
so it is not a fair direct numerical baseline for every AgentProf RQ. It is,
however, mandatory positioning for the hierarchy-versus-profiling distinction.
It is also absent from the paper.

### Adjacent work demonstrates stronger user consequences

- [Hodoscope](https://arxiv.org/abs/2604.11072) compares group-wise behavior
  distributions, discovers unknown misbehavior, and reports 6–23× lower human
  review effort than uniform sampling.
- [TraceGraph](https://arxiv.org/abs/2605.31308) builds shared decision
  landscapes and uses trap regions in a recovery pipeline that improves
  official SWE-bench resolved rate on fired subsets.
- [TraceProbe](https://arxiv.org/abs/2607.06184) canonicalizes nine action
  types over 2,500 production-setting coding trajectories and reports process
  patterns, completion behavior, and failed work.
- [Graphectory](https://doi.org/10.1145/3798271) is an archival process-centric
  trajectory analysis system with cross-run patterns and intervention.

The paper's current one-sentence descriptions of these two works are
directionally correct but not equally precise. The TraceProbe primary abstract
describes a canonical action/effect taxonomy, single-run anti-pattern
detection, controlled paired-run alignment, and analysis of completion,
failed work, steps, time, and tokens. Calling that only a “resource-aware
process profile” is too narrow; the citation should explicitly acknowledge its
trajectory diagnostics and paired-run divergence analysis. The Graphectory
PDF does define temporal/semantic process graphs, phase-flow and pattern
analyses over 4,000 trajectories, and an online intervention that improves
resolution rate on problematic instances. “Per-trajectory process graphs with
aggregated phase patterns” is accurate but incomplete; the distinction should
also acknowledge its process metrics and intervention result.

**Consequence:** a current AAAI reviewer can expect evidence beyond “the
representation contains an independently labeled problem.” Review effort,
diagnostic accuracy, or downstream recovery are demonstrated by nearby work.
AgentProf's case studies are useful, but RQ1 remains post-hoc and RQ2's
semantic prefix is tied with the matched raw+evidence control.

### Products already provide hierarchical categories and rollups

[LangSmith Insights](https://docs.langchain.com/langsmith/insights) automatically
creates top-level categories and subcategories, aggregates error rate,
latency, cost, feedback, and extracted attributes, and drills down to
individual traces. It also publishes a typical 1,000-thread model-cost range.
Datadog Patterns documents analogous hierarchical pattern grouping and metric
rollups.

**Consequence:** the Introduction's narrow combination claim is more defensible
than a broad product-gap claim, but the paper does not empirically show what
decision its within-trace intervals and conserved pprof representation enable
that these category systems do not.

### Existing workflow profilers raise the RQ4 bar

[NVIDIA NeMo Agent Toolkit profiler](https://docs.nvidia.com/nemo/agent-toolkit/latest/improve-workflows/profiler.html)
records prompt/completion tokens, LLM/tool runtimes, workflow latency,
throughput, bottlenecks, concurrency, and percentile information. Its current
documentation exposes raw per-invocation statistics and hierarchical workflow
call-pattern analysis.

**Consequence:** AgentProf does not need to become an online NeMo replacement,
but an end-to-end cost claim for its distinguishing automatic semantic backend
must include annotation wall time, usage, failures, and model/config identity.
Fixed-mark serialization alone is not the comparable system boundary.

### pprof compatibility is real but not a novelty moat

[OpenTelemetry Profiles](https://opentelemetry.io/docs/specs/otel/profiles/)
defines a pprof-derived/superset representation, generalized attributes, and
direct trace/span references. Google pprof already supports profile labels,
focus/filter operations, and tag-derived pseudo-frames.

**Consequence:** AgentProf's standard output is a valuable systems choice, but
novelty must lie in deriving and validating semantic responsibility, not in
protobuf serialization or trace linkage.

### Diagnosis benchmarks validate the matched-evidence concern

- [AgentRx](https://arxiv.org/abs/2602.02475) localizes critical failure steps
  from annotated failed trajectories using auditable constraint-validation
  logs.
- [CodeTracer](https://arxiv.org/abs/2604.11641) constructs hierarchical state
  traces and CodeTraceBench supervision at stage and step levels for failure
  onset localization.
- [AgentProcessBench](https://arxiv.org/abs/2603.14465) has 1,000 trajectories
  and 8,509 human-labeled steps under a ternary process-quality scheme.
- [HINTBench](https://arxiv.org/abs/2604.13954) defines risk detection,
  risk-step localization, and failure-type identification; its headline
  localization result is Strict-F1 rather than MAP.
- The archival [TraceElephant ACL 2026 paper](https://aclanthology.org/2026.acl-long.912/)
  reports that full traces improve attribution accuracy by up to 76.5% over
  partial observation.

**Consequence:** Direct+Raw+Evidence is a necessary baseline, not an unfairly
strong one. Source information materially affects attribution. The paper's
MAP formulation is standard retrieval mathematics but a new cross-benchmark
protocol rather than each benchmark's official task. It needs to be described
as such, and its user meaning should be validated rather than implied.

### AAAI-27 standards create a hard submission blocker

The official [AAAI-27 Main Technical Track call](https://aaai.org/conference/aaai/aaai-27/main-technical-track-call/)
states:

- 7 pages of main content and 9 pages maximum total;
- pages beyond page 7 are exclusively references;
- critical evidence must appear in the main body because reviewers need not
  read supplementary material;
- review criteria include significance, novelty, soundness, relevance,
  clarity, responsible research, and reproducibility;
- integrative work is welcome, but incremental narrow work is disfavored.

The current PDF has 12 pages and references start on page 11. Therefore it has
10 pages of main content and 12 total, exceeding both limits.

## Baseline adequacy by RQ

| RQ | Current strongest baseline | What it establishes | What remains missing |
|---|---|---|---|
| RQ1 | Native source and coarse action on identical rows/weights; recurrence on complete CodeTrace | The selected responsibility is fragmented under native/coarse organization and directly focusable under the semantic path | Independent population-level responsibility selection or a measured user/decision outcome |
| RQ2 | Direct-only and information-matched Direct+Raw+Evidence | Group/evidence refinement helps Direct-only; semantic prefix has no detected ranking advantage | Official-metric or review-effort validation, and a setting where cross-run semantic responsibility is causally needed |
| RQ3 | Recurrence, native source, source turns, raw action, simple OSWorld controls | A2 is strongest on the reported complete development population; other backends recover specific literal/partition constructs | Untouched-family A2 confirmation, repeat stability, semantic-name/topology validation, and closest ACT*ONOMY positioning |
| RQ4 | Raw action, recurrence, fixed-mark replay; rejected local-model context | Deterministic construction and replay are measured accurately | Instrumented adopted-backend inference time, tokens, calls, errors, and variability |

ACT*ONOMY and CHIEF should not be forced into invented MAP rows when their
native output contracts differ. A capability comparison is mandatory; a
numerical baseline is warranted only where the released artifact can be
faithfully applied without changing its task or information.

## How external evidence changes the blind attack map

1. **Novelty risk rises from major to blocker-level.** Two missing sources
   directly occupy hierarchical behavior profiling and hierarchical
   attribution.
2. **The matched RQ2 baseline is confirmed as scientifically necessary.**
   Its null difference cannot be dismissed as over-control.
3. **RQ1's bounded case remains valid.** External work does not invalidate the
   matched pprof projection, but it raises the expected consequence beyond a
   post-hoc organization demonstration.
4. **RQ4 improves over the earlier paper but remains incomplete.** Step 0075
   measures honest deterministic components; the distinguishing Agent cost is
   still absent.
5. **Venue format becomes an independent hard blocker.**

## Sources and artifacts

Primary sources are linked inline. The repository sources checked were
`main.tex`, `references.bib`, the built PDF, and the complete Step 0072, 0075,
and 0076 experiment/result-review records.

## Paper and claim impact

The external record does not challenge the paper-level thesis. It challenges
novelty wording and the sufficiency of current evidence for hierarchy-specific
utility. The appropriate repair is stronger comparison and evidence, not a
smaller thesis.

## Completion assessment and next node

Targeted external verification is complete. A broader literature map may be
useful later, but no additional search is needed for this cycle's verdict.
Next node: source-grounded full-paper reread and per-RQ assessment.
