# RQ evidence audit before the terminal aggregate-aware run

Timestamp: 2026-07-24T01:16:00-07:00
Status: working analysis; no paper claim or result is changed here

## Why this audit exists

The current experiment measures more than profile materialization.  The
automatic backend reads source traces, creates operation annotations, receives
aggregate diagnostics, rereads implicated source intervals, revises the
annotations, and regenerates the same pprof.  The evaluation must therefore
separate semantic quality, problem usefulness, and end-to-end cost.  Reporting
only the deterministic `.pb.gz` construction time would omit the dominant
automatic component.

This document does not redefine the four fixed paper RQs.  It records what each
RQ must establish, which standard or direct measurements answer it, and which
current weaknesses the remaining experiments must address.

## RQ1: Does semantic profiling improve resource attribution?

### What this RQ should establish

For a fixed set of source calls, one reusable operation hierarchy should
conserve each additive measure and make consequential cross-run resource
concentrations inspectable.  The question is not whether AgentPProf reconstructs
kernel side effects, and it does not require a synthetic attribution oracle.

### Evidence required

- Exact conservation of operation count and provider-reported token mass.
- The same hierarchy replayed with at least two additive measures.
- A matched native/coarse organization over the same source calls and weights.
- A fixed user question answered from the generated profile with contributing
  sessions and source evidence.
- A masked comparison of first-pass and terminal profiles, so usefulness is not
  inferred from fewer singleton tags or a visually deeper graph.

### Current weakness and closing experiment

The paper currently has a strong repeated Git case but its focal SSH
responsibility was selected from the prior semantic profile.  Step 0077 retains
the complete three-run population and fixed question, hides the expected answer
from the backend, and compares the fresh first pass with the converged
aggregate-aware result.  It must report whether a reviewer can recover the
highest-cost shared responsibility, rank, contributing runs, operation/token
mass, evidence IDs, and terminal-condition status.  This strengthens
answerability and cross-run attribution; it must not be described as a
population-wide discovery-accuracy metric.

## RQ2: Does profiler output correspond to real problems?

### What this RQ should establish

Operation profiles should place independently defined failures or responsible
steps early enough to inspect, and aggregate success/failure differences should
correspond to an external problem label rather than merely to attractive names.

### Evidence required

- Standard per-query AP and MAP on the complete AgentProcessBench, HINTBench,
  and TraceElephant target-bearing populations.
- Direct-only and information-matched raw-action-plus-evidence baselines.
- Paired, trajectory-clustered uncertainty intervals.
- On AgentReward, a complete outcome-blind annotation of all 440 traces,
  followed only after freezing by the 338-pair signed difference.
- A fixed external label check such as expert looping AP, plus source-supported
  case answers for the strongest failed-side and successful-side paths.

### Current weakness and closing experiment

The existing semantic method improves over Direct-only but ties the
information-matched raw/evidence view.  Therefore the current result shows that
profile grouping and evidence help, not that the semantic prefix itself
improves target ranking.  After Step 0077 fixes the aggregate-aware mechanism,
RQ2 must be rerun on all three complete public populations without changing
targets or scoring.  The AgentReward case must use the terminal outcome-blind
annotations and must retain the fixed-chain comparison; a better-looking
flamegraph alone is not an RQ2 result.

## RQ3: How accurately do automatic backends recover operation structure?

### What this RQ should establish

An automatic backend should recover operation boundaries and partitions from
source-visible trace content, and its short names should support cross-session
reuse.  Boundary placement, partition agreement, and literal naming are
different outputs and must not be collapsed into a bespoke score.

### Evidence required

- Ordinary operation-level B-cubed precision, recall, and F1 for partitions.
- Exact adjacent-boundary precision, recall, and F1.
- V-measure where a benchmark exposes only partition-valued labels.
- Macro-F1 and accuracy only for genuinely closed literal-label tasks.
- Complete-population baselines: native source units, raw-action grouping,
  recurrence, always-boundary/action-change controls where applicable.
- Exact coverage and additive-mass conservation as validity checks, not quality
  scores.

### Current weakness and closing experiment

The current Automatic Agent reaches B-cubed F1 0.704 and boundary F1 0.394 on
CodeTraceBench, but this is the constructor's complete development population
and the first-pass naming remains fragmented.  Once Step 0077 reaches its
outcome-blind terminal mechanism, that fixed mechanism must be applied to all
405 CodeTraceBench trajectories before reading stages, then scored once against
the unchanged gold partitions and boundaries.  The report must include both
precision and recall so a gain cannot come from indiscriminate merging or
splitting.  Tag reuse, singleton fraction, near-name counts, and depth
distribution explain the result but do not replace the standard metrics.

## RQ4: What is the cost of constructing a semantic profile?

### What this RQ should establish

RQ4 must measure the complete automatic path as well as the deterministic
profiling core.  The dominant quantities are backend tokens and inference time;
`.pb.gz` construction time and memory are a separate, much smaller system cost.

### Cost decomposition

1. Source preparation and normalized trace serialization.
2. Fresh automatic annotation over the complete population.
3. Aggregate diagnosis and all local revision passes to convergence.
4. Deterministic annotation validation and stack/profile construction.
5. Stock-pprof replay or focus-query time.

### Values that must be reported separately

- Provider `input_tokens`, `cached_input_tokens`, `output_tokens`, and
  `reasoning_output_tokens`; uncached input is derived explicitly rather than
  conflated with total input.
- Tokenizer-counted logical request and annotation tokens for the exact
  source-visible payload.
- Backend calls, failures, retries, and fixed concurrency.
- End-to-end elapsed time from the first worker start to the last worker finish,
  plus summed worker-seconds.
- Trace nodes, sessions, source operations, and local intervals read.
- Tokens and time normalized per session, per 1,000 trace nodes, and per 1,000
  source operations.
- Cumulative revision cost versus a measured fresh complete pass using the same
  backend and population.
- CLI diagnosis/materialization wall time, peak RSS, throughput, and stock
  pprof replay time.

The experiment will report actual and logical token counts together.  Provider
actual input can include repeated orchestration and cached context, while the
logical payload measures the algorithm-visible serialized request; neither is a
substitute for the other.  Quality and cost remain separate results: lower cost
cannot compensate for worse answerability or structure, and higher cost does
not invalidate a quality improvement.

### Same-population backend comparison

The final cost table should also compare the source-native/no-annotation view,
deterministic recurrence, fresh Automatic Agent, and converged Automatic Agent
on the same CodeTraceBench population.  Each row reports its own construction
time, peak RSS, backend token use, and the already-defined RQ3 B-cubed/boundary
scores.  This exposes the quality--cost choice without inventing a combined
utility score.  AgentReward and the Git case remain the complete product-facing
cost measurements; their token counts must not be mixed with CodeTrace quality
as though they came from the same population.

## Paper-level closure order

1. Freeze the Step 0077 terminal annotations and cost telemetry.
2. Complete the masked RQ1/RQ2 case-answerability review.
3. Apply the fixed terminal mechanism to CodeTraceBench and compute RQ3
   standard metrics without gold-visible iteration.
4. Rerun the three complete RQ2 localization populations with the fixed
   mechanism.
5. Replace the current RQ4 inference omission with the full cost decomposition.
6. Only then update the paper's RQ text, tables, figures, limitations, abstract,
   and introduction from the frozen results.
