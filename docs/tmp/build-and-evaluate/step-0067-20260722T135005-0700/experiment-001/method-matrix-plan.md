# Method matrix plan: native-tree operation stacks

Timestamp: 2026-07-22T13:50:05-07:00
Status: approved after independent plan review

## Fixed paper questions

The experiment does not change the paper's four RQs:

1. **RQ1:** Does semantic profiling improve resource attribution?
2. **RQ2:** Does profiler output correspond to real problems?
3. **RQ3:** How accurate are the tags?
4. **RQ4:** What is the profiling cost?

The tested hypothesis is that automatic semantic paths which refine the
source-native hierarchy produce more useful attribution and localization than
native fields or recurrence alone while remaining practical to construct and
fold. This hypothesis concerns constructor detail; it does not revise the
paper thesis or RQs.

## Common product contract

All methods consume the same ordered source operations and preserve their
native session/request ancestry and replay-stable source IDs. Every method
emits the same sparse annotation configuration: the first source operation in
each sequence is marked, later marks start only where the complete semantic
path changes, and all unmarked operations inherit the latest path.

AgentPProf contains no method backend. It validates one operation file plus
one annotation configuration and produces one standard `.pb`/`.pb.gz`.
Evaluation scripts may construct configurations, but they do not add product
formats, renderers, services, or model adapters.

## Method set

### N0: native-tree folding (non-LLM)

Project each operation onto the source-provided hierarchy: available task or
request path followed by phase, action, object, and result evidence. Missing
fields create shorter paths. Adjacent identical complete paths fold together.
No learned model, recurrence statistic, threshold, inferred semantic name, or
depth target is used. This is the structurally matched baseline and exposes
what the mainline hierarchy already provides.

### N1: recurrence-tree folding (non-LLM)

Reuse the completed target-blind multi-resolution recurrence constructor.
Coarse visible actions establish continuity; recurrent detail can refine that
continuity. Its groups are attached beneath the existing native task/request
context and serialized as the same sparse complete-path marks. The algorithm
does not read evaluation targets or resource weights. No new recurrence score,
cutoff, dataset, or calibration is introduced in this step.

### A0: automatic Agent marks

Codex subagents receive source-only packets and the fixed collection question.
They may inspect task text, session summaries, selected intervals, and raw
source references adaptively. Each returns complete semantic paths directly;
AgentPProf does not infer stack actions. The root Agent checks configuration
validity, reconciles genuinely synonymous names across batches, and rejects
unsupported boundaries. This is an automatic backend output, not a human
reference. It targets no depth distribution.

### A1: source-preserving automatic Agent marks

A1 was added after the A0 full run exposed a mismatch with the already stated
product contract: the A0 localization projection used only
`project -> operation`, although the actual profiler starts from source-native
calls and places semantic operations above their evidence. A1 does not change
one annotation, boundary, name, model, threshold, or source input. It replays
the same A0 paths as
`project -> operation... -> source kind -> LLM/tool call`; unique session,
prompt, call, and evidence identifiers remain pprof labels so equal paths can
still aggregate across runs. The corresponding RQ2 row is a post-A0
source-preservation correction, not a retrospectively blind result.

### Excluded historical control: recursive LLM marks

Retain the implemented target-blind Qwen3.6-27B recursive segmenter as the
automatic-LLM development record. Its interrupted 259/405 run is incomplete and
is not required for this experiment: A0 is already an automatic Agent backend,
and N0/N1 represent the two distinct non-LLM explanations. The incomplete run
will not be scored, cited, or resumed merely to add another method row.

## RQ-specific complete evaluations

Each RQ is a separate complete experiment node using that RQ's existing
standard protocol. A method is not credited from a smoke run or another RQ.

### RQ1: attribution

- Workload: all 405 CodeTraceBench trajectories and 20,866 operations.
- Reference: the released 2,948 human stages already used by the paper.
- Primary metric: ordinary operation-level B-cubed precision, recall, and F1.
- Secondary diagnostic: exact adjacent-boundary precision, recall, and F1.
- Resource conservation: every method must fold the same operation weights.

### RQ2: problem localization

- Workloads: complete AgentProcessBench, HINTBench, and TraceElephant inputs
  already registered by the paper.
- Frozen benchmark localizer/judge signals and query targets remain unchanged.
- Primary metric: the existing standard per-query AP and workload MAP.
- Every constructor must emit groups before target labels are opened; semantic
  prefixes use the same group-scoring and tie handling as the current paper.

### RQ3: tag and structure accuracy

- Reuse the paper's complete named-tag, partition, and boundary workloads.
- Named labels retain benchmark-defined macro-F1/accuracy or V-measure.
- Partitions use ordinary B-cubed; exact boundaries use precision/recall/F1.
- No token-weighted B-cubed, reader budget, top-k cutoff, or custom scalar
  replaces these standard metrics.

### RQ4: cost

- Run the paper's four complete cost workloads and their union.
- Report AgentPProf construction wall time and peak RSS for the common fixed
  configurations exactly as the current protocol does.
- Separately report constructor cost when observable: deterministic method
  wall time, LLM/Agent elapsed time, and model usage exposed by the backend.
  Missing provider-side token accounting is reported as unavailable rather
  than estimated. Constructor cost never replaces the common CLI cost result.

## Case-study acceptance

The fixed 41-session, 5,750-operation long-horizon collection is a product
case, not a replacement for standard accuracy. Generate its actual pprof with
the automatic Agent marks, open it in stock `go tool pprof`, and inspect the
rendered flame graph. The figure enters the paper only if source drilldown
supports useful claims about task decomposition, recurrent/returned work, and
expensive paths without supported conclusions. Uneven and genuinely deep paths
must be observed rather than required by the annotation prompt.

The retained AgentRewardBench differential remains the second multi-session
case. It must likewise use a complete collection and one signed standard
pprof; a single good/bad pair is only evidence drilldown.

## Completion

The matrix completes only after N0, N1, A0, and the source-preserving A1
projection finish each registered RQ
workload, all configurations replay through the same CLI with exact operation
mass, standard metrics and costs are independently reviewed, both real pprof
cases are opened and inspected, and the paper embeds the actual accepted
figures. A method failure remains a method result; it does not change the RQ,
workload, metric, or product contract.
