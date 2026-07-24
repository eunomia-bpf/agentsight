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

The eventual paper wording should make the four questions form one causal
chain, while retaining their fixed subjects:

1. **Attribution:** does an operation hierarchy reveal cross-run resource
   concentrations hidden by source-native organization?
2. **Localization:** do those profiles rank independently defined real
   problems early?
3. **Construction quality:** how accurately do automatic backends recover
   operation boundaries, partitions, and reusable names?
4. **Cost:** what time/token/system cost buys that construction quality, and
   when is a reusable profile cheaper than repeated direct trace reading?

RQ1 is therefore not a low-level side-effect-correctness benchmark and RQ4 is
not merely `.pb.gz` serialization time.

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

The final RQ1 package should not rely on that one case alone.  Reuse the
complete 125-task AgentReward population and its frozen operation hierarchy to
rank the same operations once by count and once by provider tokens.  Report
per-task Kendall's tau-b (with a task-cluster bootstrap interval) and the
corresponding Spearman correlation as standard rank-agreement measurements.
This tests at population scale whether changing only the additive measure
changes which recurring responsibilities dominate; it does not invent a
project-specific attribution score.  Keep the Git profile as the explanatory
case that connects the rank difference to source evidence and an unmet user
condition.

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

The evaluation also needs the strongest current-practice competitor the user
asked about: a query-aware Agent that reads the same trace evidence directly
and returns a ranked diagnosis without AgentPProf.  Give that baseline the same
query, source-visible content, model family, and explicit source-ID requirement
as the profile reader; disclose that it is query-specific whereas the
AgentPProf hierarchy is constructed once and replayed across queries and
additive measures.  Score ranked outputs with the same AP/MAP and external
targets, and record its token/time cost.  A direct reader is not replaced by
the existing Direct-only numerical score or raw-action prefix because neither
is an Agent analyst.

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

CodeTraceBench alone cannot establish transfer because earlier constructor
choices observed that population.  Apply the fixed terminal instruction and
mechanism once to the complete OSWorld-Human population with its group labels
hidden until annotations are frozen, then report the same ordinary B-cubed and
exact-boundary precision, recall, and F1.  This is the independent-population
check; it replaces no existing complete-population result and does not permit
another prompt or mechanism change after labels are opened.

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
  source-visible payload, broken down into instruction, source packet, current
  annotation, revised annotation, and experiment-only Markdown decision
  report.  The product output is the revised annotation; the audit report may
  not be silently counted as an intrinsic product requirement.
- Backend calls, failures, retries, and fixed concurrency.
- End-to-end elapsed time from the first worker start to the last worker finish,
  plus summed worker-seconds.
- Trace nodes, sessions, source operations, and local intervals read.
- Unique source-context nodes presented to revision workers, both absolutely
  and as a fraction of the batch trace.  The third-pass packets currently
  cover 60.1--82.9% of their batch nodes because warning intervals overlap.
  That is selected rereading, but it is not yet a convincingly local-cost
  mechanism; the final result must expose this rather than describing every
  revision as a cheap local read.
- Tokens and time normalized per session, per 1,000 trace nodes, and per 1,000
  source operations.
- Cumulative revision cost versus a measured fresh complete pass using the same
  backend and population.
- Query-aware direct-Agent baseline cost on the same diagnosis inputs, kept
  separate from target-blind construction cost.
- CLI diagnosis/materialization wall time, peak RSS, throughput, and stock
  pprof replay time.
- Where both readers are measured, report the transparent amortization
  equation
  `construction + K * profile-reader query` versus
  `K * direct-trace query`, and the resulting break-even query count if one
  exists.  This is a cost derivation, not a new quality score: the two readers
  must still be compared with the same AP/MAP and answerability criteria.

The experiment will report actual and logical token counts together.  Provider
actual input can include repeated orchestration and cached context, while the
logical payload measures the algorithm-visible serialized request; neither is a
substitute for the other.  Quality and cost remain separate results: lower cost
cannot compensate for worse answerability or structure, and higher cost does
not invalidate a quality improvement.

### Observed repeated-review cost

The fresh AgentReward pass plus seven complete aggregate-review passes consumed
191,838,723 provider input tokens, including 180,865,536 cached and 10,973,187
derived uncached tokens; 1,476,432 provider output tokens; 469,409 reasoning
output tokens; and 35,231,169 logical serialized input tokens.  The sum of
complete-pass critical paths was 21,166.766 seconds (5.88 hours) under the fixed
two-worker schedule.  The seventh revision still changed 13 annotations, so
this is measured non-convergence rather than a terminal construction cost.

The next comparison replaces repeated whole-population review with stable
review keys and local context fingerprints.  From pass 006 to pass 007, only
five of 266 hierarchy diagnostics and 11 of 481 retained tag-reuse rows
changed their complete local fingerprints; 261 hierarchy decisions, 470 tag
decisions, and all 14 retained near-name decisions can be reused.  Two
incremental calls reviewed all 16 invalidated rows without changing the
annotation.  They presented 482 unique source nodes and consumed 3,691,400
provider input tokens, 259,167 packet logical tokens, and 387.202 seconds.
This is much lower than another full review but remains a material automatic
construction cost that the paper must disclose.

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
3. Apply the fixed terminal mechanism to CodeTraceBench and the independent
   OSWorld-Human population, then compute RQ3 standard metrics without
   gold-visible iteration.
4. Rerun the three complete RQ2 localization populations with the fixed
   mechanism and add the query-aware direct-Agent competitor.
5. Add the population-level RQ1 count/token rank-agreement analysis.
6. Replace the current RQ4 inference omission with the full cost decomposition.
7. Only then update the paper's RQ text, tables, figures, limitations, abstract,
   and introduction from the frozen results.
