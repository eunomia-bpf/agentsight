# External Search and Primary-Source Verification

**Timestamp:** 2026-07-23T20:50:54-07:00
**Parent:** Step 0073 / REVIEW Gate / milestone review 001
**Status:** complete

## Objective

Verify the blind review's RQ3 construct, closest-work, baseline, and cost
attacks against current primary sources. This is a focused update for Step
0073, not a repetition of Step 0072's complete novelty review.

## Inputs and provenance

The search used official specifications/product documentation and primary
paper pages:

- [ACT*ONOMY](https://arxiv.org/abs/2605.13625)
- [CodeTracer / CodeTraceBench](https://arxiv.org/abs/2604.11641)
- [TraceProbe](https://arxiv.org/abs/2607.06184)
- [Hodoscope](https://arxiv.org/abs/2604.11072)
- [TraceGraph](https://arxiv.org/abs/2605.31308)
- [AgentRx](https://arxiv.org/abs/2602.02475)
- [AgentRewardBench](https://arxiv.org/abs/2504.08942)
- [OpenTelemetry Profiles](https://opentelemetry.io/docs/specs/otel/profiles/)
- [NVIDIA NeMo Agent Toolkit Profiler](https://docs.nvidia.com/nemo/agent-toolkit/1.4/improve-workflows/profiler.html)
- [LangSmith Insights](https://docs.langchain.com/langsmith/insights)
- [Datadog Patterns](https://docs.datadoghq.com/llm_observability/monitoring/patterns/)

The current literature frontier and Step 0072 primary-source report were also
read in full so this update could distinguish a new finding from an already
recorded one.

## Method

Search questions were deliberately bounded:

1. What does CodeTraceBench's stage reference actually validate?
2. Is recurrence the strongest fair runnable numerical baseline for the fixed
   Step 0073 rows?
3. Does ACT*ONOMY supply a compatible operation-boundary prediction?
4. What consequence do adjacent systems already demonstrate?
5. What must an honest end-to-end cost experiment include?

No secondary summary is used as evidence below.

## Results

### 1. CodeTrace stages validate a flat failure-analysis partition

CodeTracer reconstructs hierarchical per-run state transitions and uses
CodeTraceBench for failure-onset localization. The released stage annotations
are therefore a reasonable independent target for contiguous segmentation and
boundary placement.

They do **not** directly validate:

- recursive ancestor topology;
- stable equality of semantic names across sessions;
- task-resource responsibility;
- a universal operation ontology; or
- cross-family generalization.

**Step 0073 consequence:** ordinary operation-level B³ and exact adjacent
boundary F1 are appropriate. The experiment must interpret them as flat
partition and transition fidelity, not full semantic-hierarchy correctness.

### 2. ACT*ONOMY is closest work, not a fair numerical row here

ACT*ONOMY defines a fixed three-level hierarchy with 10 actions, 46 subactions,
and 120 leaves, plus an automatic quote-grounded trajectory-analysis pipeline
and cross-agent behavioral profiles. It directly raises the novelty bar for
“semantic behavior profile.”

Its public release does not provide predictions aligned to the 405
CodeTraceBench operations or stage boundaries. Mapping existing A2 names into
the taxonomy would keep A2's segmentation fixed; running a fresh classifier
would change both backend and representation. Either row would be a proxy, not
ACT*ONOMY's method.

**Step 0073 consequence:** the closest-work audit correctly declines to
manufacture an ACT*ONOMY B³ row. ACT*ONOMY must instead be cited and compared
at the claim/capability level in a later WRITE pass.

### 3. The selected numerical baselines are minimal and fair

For the fixed follow-on rows:

- multi-resolution recurrence is the strongest existing same-input non-LLM
  constructor;
- native source tree tests the alternative that source structure is already
  sufficient; and
- native turn is a diagnostic fragmentation bound.

Adding raw action to this subset would supply context but not change the
decisive A2-versus-recurrence question. Adding a new model or taxonomy would
change the experiment.

**Step 0073 consequence:** no baseline is missing from this experiment. The
review should not turn a fixed subset sensitivity test into a new benchmark
paper.

### 4. Exact boundaries and B³ measure different failure modes

The Step 0073 protocol's boundary F1 asks whether a transition is placed at the
correct adjacent pair. B³ asks whether the resulting clusters have the right
item memberships. A method can detect many real transitions yet insert too
many extra transitions, yielding higher boundary recall but fragmented
partitions.

This distinction is particularly important because the source literature uses
stages to localize failure progress, while AgentProf needs usable recurring
responsibility intervals.

**Step 0073 consequence:** boundary F1 cannot override the registered B³
decision. It can diagnose why B³ changed.

### 5. Adjacent work sets a consequence bar beyond label correspondence

- Hodoscope compares group-wise behavior distributions and reports a 6–23×
  reduction in review effort relative to uniform review.
- TraceGraph uses shared decision landscapes to guide a recovery policy and
  reports official resolved-rate improvements on fired SWE-bench subsets.
- TraceProbe analyzes 2,500 production-setting coding trajectories with
  canonical actions, deterministic effect labels, milestones, tokens, duration,
  and failed work.
- AgentRx uses structured trajectory evidence to localize critical failure
  steps and categories.

**Paper consequence:** AgentProf's profile and case studies are meaningful, but
structure scores alone do not establish downstream diagnostic superiority.
Step 0073 should remain an automatic-backend fidelity test, not be repackaged as
user utility.

### 6. Standard profile output is credible but not the novelty by itself

OpenTelemetry Profiles is a pprof-compatible/superset signal and supports
direct trace/span references. This verifies that profile/trace correlation and
pprof interoperability are legitimate standards directions.

**Paper consequence:** AgentProf's differentiator is the derived semantic
responsibility and conserved agent-specific measures, not protobuf emission or
trace linkage alone.

### 7. End-to-end annotation cost is a real missing experiment

The NeMo Agent Toolkit profiler records per-invocation tokens, time, and LLM
calls in real time and reports latency, throughput, bottleneck, and concurrency
metrics. LangSmith Insights and Datadog Patterns also perform model-backed
cross-trace categorization. The paper's fixed-mark 1.16-second result therefore
measures only a fast materialization core, not the cost of the capability that
distinguishes AgentProf.

An honest AgentProf end-to-end cost experiment needs, at minimum:

- source adaptation time;
- automatic annotation wall time;
- model calls and input/output tokens;
- profile construction time;
- peak host and accelerator memory when available;
- complete coverage/failure count; and
- normalization per session and per 1,000 source operations.

The smallest fair controls are:

1. fixed-mark replay as the lower bound;
2. the same fixed automatic backend end to end; and
3. the label-free recurrence backend end to end on the same source operations.

NeMo is an important capability and scope comparison, but it is not a fair
numerical row unless both systems can consume the same complete histories and
produce the same semantic output. Inventing such an adapter by default would
be a second research program.

## Primary-source impact on Step 0073

| Question | Verified answer | Review consequence |
|---|---|---|
| Are B³ and boundary F1 valid? | Yes, for flat membership and adjacent transitions. | Keep both; do not call them nested-topology fidelity. |
| Is recurrence a fair primary baseline? | Yes, among existing same-input constructors. | No new numerical baseline required. |
| Must ACT*ONOMY be a row? | No compatible CodeTrace boundary output exists. | Cite/compare; do not fabricate. |
| Does higher boundary F1 prove a better hierarchy? | No; over-fragmentation can coexist with better recall. | B³ decision remains primary. |
| Is fixed-mark timing end to end? | No. | RQ4 annotation cost remains mandatory. |

## Paper/claim impact

External verification strengthens the Step 0073 design and weakens any attempt
to interpret a pooled CodeTrace score as universal semantic-hierarchy accuracy.
It also confirms that the current paper's Related Work is incomplete without
ACT*ONOMY and that RQ4's scope is explicitly, materially narrower than
end-to-end automatic profiling.

These findings do not authorize a smaller thesis. They identify exactly where
the larger claim still needs evidence.

## Alternatives and decision

The fixed follow-on experiment should proceed with recurrence, native tree, and
native turn only. If it diagnoses fragmentation, the next RQ3 mechanism must
change how a split is decided—using interval-wide context and an explicit stop
decision—rather than contracting groups with stage labels.

Automatic-annotation cost should be measured only for a fixed backend whose
quality result is reportable. Measuring a backend that is immediately rejected
would not answer the paper's practical RQ4.

## Tree/search updates

- Confirmed the Step 0073 baseline branch as closed and adequate.
- Opened a mandatory later Related Work update for ACT*ONOMY.
- Retained one later RQ4 end-to-end cost node.
- Did not open a product reimplementation, custom metric, or new dataset.

## Project-memory updates

None. This phase is read-only.

## Completion assessment, uncertainty, and next node

Focused primary-source verification is complete. The remaining uncertainty is
empirical: whether the fixed A2 output preserves its pooled advantage on the
manifest-defined follow-on. The next node is a complete source-grounded reread
of the paper and Step 0073 result.
