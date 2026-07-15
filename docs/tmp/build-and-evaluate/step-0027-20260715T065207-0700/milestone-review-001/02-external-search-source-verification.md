# Milestone Review 001 — External Search And Source Verification

**Completed:** 2026-07-15T07:10:00-07:00  
**Mode:** primary papers and official product/conference documentation  
**Purpose:** attack novelty, evaluation relevance, and AAAI-27 readiness before
selecting another experiment

## AAAI-27 Contract

The official AAAI-27 conference page and Main Technical Track call establish
the relevant submission contract:

- abstract deadline: July 21, 2026; full paper: July 28; supplementary/code:
  July 31, all at 23:59 UTC-12;
- seven pages of technical content and up to two reference-only pages;
- the reproducibility checklist is mandatory;
- supplementary material is optional and cannot carry material necessary to
  evaluate the main claim;
- the track explicitly welcomes technically solid work that opens new
  directions, rather than rewarding a long checklist of incremental results.

The current paper satisfies the page geometry, anonymity, style-file, and
reference-page boundary. Its unfilled checklist is a concrete submission
blocker. The main scientific blockers must be solved in the seven-page paper,
not moved to a supplement.

Primary sources:

- <https://aaai.org/conference/aaai/aaai-27/>
- <https://aaai.org/conference/aaai/aaai-27/main-technical-track-call/>

## Closest Product And System Capabilities

### LangSmith Insights

Official documentation shows that Insights operates over tracing projects or
uploaded external chat histories, automatically creates categories and
subcategories, and aggregates trace count, error, latency, token, cost,
feedback, and related statistics. Reports can be scheduled and compared. Its
implementation uses LLM summarization and clustering over sampled traces.

This invalidates any broad novelty statement that agent tools lack cross-trace
hierarchies or corpus-level semantic aggregation. The paper already avoids that
obsolete statement. The remaining separation is narrower and technically
meaningful: AgentProf keeps source-linked additive effects, lets one operation
population be projected through selectable ordered stacks, conserves each
weight, and exports pprof-compatible profiles. Those properties must remain
central and should eventually be tested as a consequence, not only asserted.

Primary source: <https://docs.langchain.com/langsmith/insights>

### Datadog LLM Observability And Patterns

Datadog documents trace/span search, cost and latency metrics, evaluations, and
Patterns, which clusters production LLM traffic into hierarchical topics and
surfaces anomalies. It is therefore another real cross-trace hierarchy, not a
mere per-run debugger. As with LangSmith, the defensible distinction is not
"hierarchical grouping exists only here"; it is source-linked cross-layer
effects plus selectable conserved profiler projections over heterogeneous
offline inputs.

Primary sources:

- <https://docs.datadoghq.com/llm_observability/>
- <https://docs.datadoghq.com/llm_observability/monitoring/patterns/>

### NVIDIA NeMo Agent Toolkit Profiler

The official profiler instruments supported workflow frameworks through
callbacks/decorators, records per-invocation token/time/LLM statistics, and
performs offline latency, throughput, bottleneck, concurrency, and forecasting
analysis. It supports several common agent frameworks. This is a genuine agent
profiler baseline and prevents the paper from equating profiling with the mere
existence of flamegraphs or aggregate cost numbers.

AgentProf's distinct scope is heterogeneous already-recorded histories and
source-linked effects without requiring one supported instrumented workflow,
plus multiple operation-stack projections over the same additive operations.

Primary source:
<https://docs.nvidia.com/nemo/agent-toolkit/1.4/improve-workflows/profiler.html>

## Closest Research And Evaluation Threats

### Insights Generator

The May 2026 preprint *Insights Generator: Systematic Corpus-Level Trace
Diagnostics for LLM Agents* formalizes corpus-level trace diagnostics and uses
a scout/investigator multi-agent architecture to propose and test hypotheses
over trace groups. It reports evidence-backed natural-language findings and,
most importantly, a downstream result: human experts applying its reports
improve scaffold performance by 30.4 percentage points, while coding agents
using derived insights show stable gains.

This is the strongest same-problem threat found in the search. It does not
provide AgentProf's profiler data model, conserved multi-weight projections, or
source-linked cross-layer effects, but it closes the developer-decision edge
more directly than the current RQ2 evidence. It is not cited in the current
paper. A later WRITE pass should add it and distinguish diagnostic report
generation from profiler attribution; a later RQ2 experiment should treat its
decision consequence as the standard to beat, not pretend the work is absent.

Primary source: <https://arxiv.org/abs/2605.21347>

### AgentTelemetry

AgentTelemetry defines agent-specific telemetry and a fault benchmark across
multiple frameworks and faults, and reports a telemetry-guided intervention
gain on SWE-bench. The current paper cites it. It raises the bar for claims that
source-linked observations improve agent quality: detecting more fault classes
and changing task outcomes are stronger consequences than merely producing a
readable hierarchy.

Primary source: <https://openreview.net/pdf?id=owdmAYFk6k>

### CodeTracer And CodeTraceBench

CodeTracer reconstructs hierarchical state-transition traces, localizes
failure onset and propagation, and uses replayed diagnostic signals to recover
failed runs under matched budgets. CodeTraceBench spans four code-agent
frameworks and supplies consecutive stage plus step-level supervision. The
local verified manifest confirms complete stage intervals for 1,000
trajectories. Exact source-coverage reconstruction finds 483 already-normalized
verified reference trajectories disjoint from the 405 failed targets used by
the paper. The remaining 112 non-target manifest trajectories are absent from
the existing normalized reference artifact and are not counted or proposed.

This makes CodeTraceBench unusually valuable for the user's requested next
step: the algorithm can be improved and evaluated on trajectories already
downloaded and already normalized. No new benchmark is needed. The 483
reference trajectories can provide source-authored stage boundaries for a
supervised calibration of the existing recurrence score. The 405 failed
targets are a reused development population whose labels will be mechanically
withheld during fitting; they preserve a real solved-reference to failed-target
distribution shift but cannot provide untouched confirmation.

Primary source: <https://arxiv.org/abs/2604.11641>

### AgentAtlas

AgentAtlas proposes a diagnostic taxonomy and explicitly demonstrates that
label agreement can change when the label menu is hidden. Its demonstration is
synthetic and is not a definitive benchmark, but the measurement warning is
directly relevant: literal tag accuracy cannot be inferred from clustering
purity or a provided label menu. The current paper cites AgentAtlas and
correctly leaves literal-name accuracy outside current evidence.

Primary source: <https://arxiv.org/abs/2605.20530>

## Source-Grounded Scientific Decision

The literature search does not support inventing a new trajectory source. It
supports two high-value directions:

1. **RQ3 now:** reuse the already-normalized OSWorld-Human and CodeTraceBench
   trajectories to improve the existing operation-stack constructor under a
   target-label-withheld fitting protocol. This adds supporting evidence for
   the group-boundary part of RQ3 and follows the user's instruction; it does
   not answer phase, action, or literal-name accuracy.
2. **RQ2 later:** compare a fixed profiler output with a strong diagnostic
   workflow on an actual developer decision or repair consequence. Insights
   Generator, CodeTracer, and AgentTelemetry show why that standard matters.

The first direction wins now because it changes the current paper's weakest
algorithm/evidence row without collecting new data. It must not be another
action-only cutoff tweak: Step 0026 already showed that action pairs and short
action windows alias official boundaries. The smallest defensible change is to
retain the same recurrence statistic and operation-stack output, but replace
its unsupervised two-means calibration with a reference-label calibration when
independent boundary annotations are available. Reused development-target
labels remain withheld during fitting; the label-free constructor remains the
no-annotation baseline.
