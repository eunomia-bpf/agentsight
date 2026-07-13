# AgentProf Literature And Novelty Frontier

## Current Question

The paper-level literature question is whether existing agent observability is
still centered on debugging individual executions, while recurring cost,
regression, safety, failure, and wasted-work questions require a distinct
profiling layer across runs. Within that broader question, the mechanism-level
novelty question is whether reusable operations and query-time operation stacks
provide a useful profiling model when flat, source-native, and semantic views
are compared against the analyst's real decision.

The literature program follows the paper's four fixed questions: improved
resource attribution, correspondence to real problems, tag accuracy, and
profiling cost. The fixed thesis is **Agent observability needs profiling, not
only debugging.** Literature search must strengthen that positive program and
find published protocols, real systems, benchmarks, and data for each question;
it must not replace the thesis with a narrower hierarchy-selection study.

This is the concise current frontier. The full pre-recovery search log, source
inventory, and dataset catalog are preserved at
`docs/tmp/cycle-0001-20260711T164850-0700/03-review-gate/idea-regression-recovery-20260712T021723-0700/archive-pre-recovery/background-related-work.md`.
Local PDFs collected by earlier searches remain under `docs/reference/`.

## Closest Source Families

### Profilers And Trace Analysis

- [Domain-specific program profiling](https://doi.org/10.1016/j.scico.2014.02.011)
  already turns domain-level execution events into a hierarchical model and
  reports along developer-chosen dimensions. This is a direct novelty threat to
  operations, arbitrary dimensions, and semantic hierarchy as standalone
  contributions.
- [pprof](https://github.com/google/pprof/blob/main/doc/README.md) represents
  weighted samples over location hierarchies and supports sample labels plus
  tag-derived pseudo frames. AgentProf therefore cannot claim weighted stack
  aggregation or tag-to-frame conversion as novel.
- [Flame graphs](https://queue.acm.org/detail.cfm?id=2927301) establish the
  folded-stack visualization lineage. A flamegraph renderer is not the paper's
  contribution.
- [Perfetto Trace Processor](https://perfetto.dev/docs/analysis/trace-processor)
  ingests trace formats, exposes SQL analysis, and derives events. Query-time
  aggregation and derived trace views are not novel by themselves.
- [Pivot Tracing](https://www.microsoft.com/en-us/research/publication/pivot-tracing-dynamic-causal-monitoring-for-distributed-systems/)
  dynamically selects, filters, and groups metrics by causally related events
  across component boundaries. It limits novelty claims for query-time
  cross-layer attribution and makes independent lineage—not only mass
  conservation—the relevant fidelity standard.
- [Visualizing Distributed Traces in Aggregate](https://arxiv.org/abs/2412.07036)
  groups traces by shared services, depth, structure, or latency and constructs
  aggregate trace views. Cross-run trace aggregation is therefore not new.
- [Differential Flame Graphs](https://doi.org/10.1109/SANER.2015.7081872)
  compare profiles from software versions to expose regressions. Differential
  profiling is a published protocol to reuse, not AgentProf's novelty.

The open opportunity is to make the profiling record and hierarchy explicit for
agent behavior, preserve source execution views as baselines, and test whether a
semantic operation-stack index changes real diagnostic outcomes.

### Semantic Cross-run Agent Analysis

- [Hodoscope](https://arxiv.org/abs/2604.11072) summarizes agent actions,
  embeds them in a common behavior space, and compares cohort densities for
  human review. Its [official SWE-bench replication](https://hodoscope.dev/blog/announcement.html)
  compares five model cohorts with 50 trajectories per model and rediscovers
  iQuest-Coder-V1's git-history exploit. This is the strongest current
  same-problem neighbor and a mandatory baseline for behavior-difference
  discovery.

Hodoscope prevents a claim that AgentProf first enables semantic cross-run
comparison or agent behavior discovery. It does not answer the broader
profiling question across recurring cost, regression, safety, failure, and
wasted work. Within that question, its flat continuous behavior space is a
strong baseline for deciding when a continuous flat view, source-native
hierarchy, or recursive semantic profile helps a real decision.

The current cycle now includes an exact official Table 2 reproduction and a
complete matched iQuest extension. Hodoscope's official density-gap/FPS bundle
finds the published action at rank 2.9 +/- 0.3, versus 24.9 +/- 15.8 for the
tested recursive bundle. Adding recursive parents does not stably improve over
the matched terminal partition or released turn-position grouping. This is a
real negative boundary for AgentProf, not evidence that flatness or continuous
geometry alone caused Hodoscope's advantage: the published bundle changes both
representation and scorer.

- [AgentDiagnose](https://aclanthology.org/2025.emnlp-demos.15/) embeds
  trajectory actions and provides semantic/state-transition visualizations for
  diagnosis and data curation. It limits novelty claims for semantic trajectory
  visualization.
- [ARIA](https://arxiv.org/abs/2506.00539) projects natural-language actions
  into intention space and aggregates reward across semantically similar
  behavior for training. It is not an observability profiler, but it limits the
  novelty of semantic projection plus additive aggregation as a mechanism.

### Agent Trace Standards And Observability Products

- [OpenTelemetry GenAI semantic conventions](https://github.com/open-telemetry/semantic-conventions-genai)
  define spans, events, and metrics for GenAI clients, providers, and MCP.
- [OpenInference](https://arize-ai.github.io/openinference/spec/) defines AI
  workload semantics over OpenTelemetry traces.
- [Phoenix](https://arize.com/docs/phoenix) combines tracing, evaluation,
  datasets, experiments, and span scoring.
- [Datadog LLM Observability Patterns](https://docs.datadoghq.com/llm_observability/monitoring/patterns/)
  performs hierarchical semantic clustering over production LLM traffic.
- [AgentTelemetry](https://dl.acm.org/doi/10.1145/3805760.3814931) presents an
  agent-observability fault-detection benchmark and toolkit.

These systems make generic claims about agent observability, trace/span
taxonomies, semantic grouping, or fault detection high-risk. They also provide
the strongest motivation for a fixed source-native trace/span hierarchy as a
baseline. AgentProf should not claim full ecosystem compatibility until it
imports and evaluates real ecosystem traces.

### Failure And Error Localization

- [AgentRx](https://github.com/microsoft/AgentRx) releases failed agent
  trajectories with critical failure steps and a diagnosis method spanning
  multiple domains.
- [TELBench / DRIFT](https://github.com/NJU-LINK/DRIFT) studies harmful error
  spans in deep-research trajectories and is a close semantic-span
  localization benchmark.
- [Holistic Evaluation and Failure Diagnosis](https://arxiv.org/abs/2605.14865)
  performs bottom-up span assessment and trace-level diagnosis.
- [TrajAD](https://arxiv.org/abs/2602.06443) studies trajectory anomaly
  detection and localization.
- [AgentFixer](https://arxiv.org/abs/2603.29848) extends detection to root-cause
  analysis and repair recommendations.

AgentProf cannot claim failure localization in general. Failure localization is
one condition inside the broader profiling problem. The relevant experiment
asks whether reorganizing the same visible operations changes a real profiling
decision, inspection work, or fragmentation compared with flat and native
execution views; it does not redefine the paper around localization.

## Real Data And Benchmark Assets

The selected primary RQ2 condition is
[CodeTraceBench](https://huggingface.co/datasets/NJU-LINK/CodeTraceBench),
released with [CodeTracer](https://arxiv.org/abs/2604.11641). Its verified split
provides 1,000 real coding-agent trajectories and 46,539 steps across OpenHands,
SWE-agent, Terminus2, and mini-SWE-agent, with human-verified incorrect and
unuseful step annotations. Raw per-trajectory archives are downloadable
separately from the annotation manifest, so AgentProf can construct every
profile before labels are joined for terminal scoring. CodeTracer's published
macro step-level precision, recall, F1, and token results provide an external
direct-diagnosis reference; its annotation-derived stages are not a fair
target-blind native baseline.

The repository already contains converters or analyses for public trajectory
families including WebLINX, Mind2Web, ToolBench/tau-bench, AgentRewardBench,
SATraj-OS, OSWorld-Human, AgentNet, and ScaleCUA, plus current AgentRx and
TELBench inputs. Their labels differ:

- grouped action or boundary annotations;
- step correctness and redundancy;
- task success, side effects, looping, or safety;
- critical failure steps or harmful error spans.

These are not interchangeable oracles. The next experiment should choose one
untouched family whose official metric directly answers one recovered RQ. A
large mixed benchmark matrix should follow only after the first decisive result
shows which construct matters.

ToolSafe TS-Bench and RedundancyBench are the strongest later independent-family
replication candidates for safety and redundant work respectively. TRAIL,
official OpenTelemetry/OpenInference trace exports, and additional real
tool/API trajectories remain useful only after their access, format, and
published protocol pass the same source preflight.

## Plain-Claim Novelty Map

| Candidate statement without project names | Same-claim risk | Current judgment |
|---|---|---|
| Agent behavior can be recorded as weighted fielded observations. | Very high | Profilers, domain-specific profiling, telemetry schemas, and event stores already provide related records. This is necessary infrastructure, not sufficient novelty. |
| Agent observations can be aggregated by fields into hierarchical views. | Very high | Domain-specific profiling, pprof tags, Perfetto SQL, and semantic clustering already cover this mechanism. |
| Agent observability needs profiling, not only debugging. | Medium | This is the author-fixed broad position. It must be grounded against trace/span observability work and demonstrated on real recurring measured behavior, not reduced to a hierarchy comparison. |
| The runtime execution tree is not necessarily the best diagnostic index for recurring behavior across runs. | Medium | This is a mechanism-level prediction that requires a direct native-tree comparison; it is not the paper-level thesis. |
| A target-blind semantic operation-stack profile concentrates independently annotated real problems and reduces analyst inspection. | High | The leaf-only and Hodoscope conditions reject two tested constructions. The restored positive hypothesis needs a materially better hidden-annotation localization experiment across real public benchmark families, not retuning on those labels. |
| No one hierarchy is automatically canonical; the useful profile depends on the measured signal and decision. | Medium | This is a competing mechanism explanation, not the paper's thesis or replacement story. |

## Novelty Risks

1. **Semantic grouping is already common.** New terminology cannot create the
   novelty gap.
2. **Failure localization has strong direct competitors.** A weak or unfair
   baseline will make a profiler result unconvincing.
3. **Extra information can masquerade as hierarchy value.** Visible fields,
   ranker capacity, tuning data, and compute must be matched.
4. **Dataset labels may define the semantic grouping.** Target labels must be
   scoring-only, and development mappings must transfer unchanged.
5. **A negative result may reveal task dependence rather than kill the broad
   question.** The paper should test competing explanations before shrinking.
6. **Trace interoperability is not yet demonstrated at ecosystem scale.** Keep
   exchange-format evidence separate from compatibility claims.

## Completed Hodoscope Boundary

The completed experiment separated the exact official reproduction from an
all-250 comparative extension and used four views:

1. flat semantic behavior units with no recursive parents;
2. the dataset- or source-native execution hierarchy;
3. one cross-run operation-stack profile specified on non-iQuest development
   cohorts and applied unchanged;
4. official Hodoscope density-difference output as the strongest flat semantic
   end-to-end comparator.

All views received the same actions, released summaries and embeddings, cohort
labels, target-time information, and raw-action inspection accounting. The
official reproduction completed all three testbeds and ten seeds. The matched
comparison completed ten Phase A and ten full-corpus Phase B seeds. The full
audit is in
`docs/tmp/cycle-0001-20260711T164850-0700/01-experiment-gate/loop-rq2-02/result-review.md`.

The result does not isolate flatness because Hodoscope also uses its continuous
KDE contrast and normalization. The native comparator is exact released
`turn_id` grouping rather than a complete execution tree. These are literature
and experiment boundaries for the next claim, not reasons to add more controls
to the completed run.

## Literature Tasks For The Next RQ2 Condition

1. Use the complete CodeTraceBench verified split, not a convenience sample.
2. Extract raw steps from its four official framework formats before reading
   incorrect or unuseful labels; annotation-derived stages remain oracle-only.
3. Freeze one target-blind measured signal, ranking, and semantic stack before
   terminal scoring.
4. Compare flat, per-session, source-native, raw-action, and one semantic stack
   over identical visible operations and resource weights.
5. Reuse the official macro step-level precision/recall/F1 unit and add ranked
   inspection-work metrics appropriate to profiler output.

## Current Verdict

The individual mechanisms are substantially precedented, but the broad
opportunity remains the missing profiling layer for recurring agent behavior.
Hodoscope is a serious same-problem neighbor and a strong baseline for behavior
difference discovery; its published task is not the paper's replacement story.
AgentProf must now demonstrate the original complete positive chain across the
four fixed RQs, beginning with target-blind localization of independently
annotated real problems across official public benchmarks and a measurable
reduction in analyst inspection. The next experiment must begin with accessible
real evidence, not a smaller problem or a larger unimplemented mechanism stack.
