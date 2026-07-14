# AgentProf Design

## Design Goal

**Agent observability needs profiling, not only debugging.** AgentProf converts
heterogeneous agent histories, operation files, and supported trace containers
into weighted profile projections that existing profiler tooling can read.
Operations and operation stacks implement this thesis. Cross-run recurrence,
measure choice, and alternative hierarchies explain and test the model; they do
not replace the thesis.

This file describes the current mechanism. Experiment history and superseded
design proposals are archived in timestamped reports; the pre-recovery version
is at
`docs/tmp/cycle-0001-20260711T164850-0700/03-review-gate/idea-regression-recovery-20260712T021723-0700/archive-pre-recovery/design.md`.

## Two Core Abstractions

### Operation

An operation is a fielded, weighted observation:

```text
fields: key/value attributes describing recorded agent activity or effect
value:  non-negative measure in the paper model
```

Examples include a prompt, LLM call, tool/API call, process action, file effect,
network effect, benchmark action, or normalized trace event. The fields may
describe source identity, agent, task, phase, tool, action, status, path,
resource, or benchmark-provided context. A paper experiment must declare which
fields are visible to the profiler and which are scoring-only labels.

An operation is a profiling record, not a claim that all events are equivalent
execution units or that the profiler has recovered causality.

The current CLI represents positive integer sample values in its admitted
experiments. Imported zero is normalized to one, so zero-valued observations in
the formal model are not yet faithfully preserved. This is an artifact gap, not
evidence for changing existing positive-weight results.

### Operation Stack

An operation stack is an ordered recursive path derived from operation fields:

```text
project -> task -> phase -> tool -> action -> status
```

The stack is a query-time profile projection. The same operations can be folded
using a flat view, a source-native hierarchy, a manually declared semantic
stack, mapped fields, or an induced recursive stack. Changing stack shape does
not create another underlying event object.

For every operation with positive value, the profiler emits its selected frame
path and adds the operation's value to that path. All output formats derive from
the same folded paths.

## Data Flow

```text
local agent history / operation JSONL / trace container
    -> normalize to operations
    -> derive fields with declared mappings or taggers
    -> optionally filter operations by field predicates
    -> choose or induce an operation stack
    -> fold weighted paths
    -> optionally rank profile groups from visible fields
    -> pprof / folded stacks / JSON / SVG
```

Available source-native path fields can form one operation stack and an
important baseline. The artifact does not reconstruct a general native
execution tree when suitable fields are absent.

## Mapping, Filtering, And Tagging

Mappings and taggers derive operation fields before folding. They are backends
or policies over the two core abstractions, not new scientific objects.

Current rule order is:

1. normalize source events into operation records;
2. apply inline and file-backed field mappings;
3. apply query predicates such as `FIELD=REGEX` or `FIELD!=REGEX`;
4. construct the selected operation stack;
5. fold weights and compute optional visible-field rank summaries.

Later mappings may use earlier derived fields. A destination field uses the
first applicable mapping under the declared precedence. Experiments must expose
the mapping rules and keep scoring-only labels out of derivation and ranking.

## Stack Construction Modes

### Declared stacks

`--stack` selects a field path directly. This is the clearest implementation of
the profiling abstraction and supports multiple resolutions over the same
operations.

### Source-native stacks

Imported session, run, trace, span, prompt, tool, or parent/path fields can be
used as stack fields when the input supplies them. These preserve the available
execution view for comparison and drilldown; they do not prove complete native
lineage.

### Induced stacks

`--induce-operation-stack` uses visible boundary evidence to recursively split
a contiguous operation sequence and writes the resulting path into an
`operation` field. This is one experimental stack-construction backend. The
recent negative RQ2 result shows that its flattened leaves are not a generally
successful failure localizer on AgentRx or TELBench. The backend must not be
confused with the operation-stack abstraction as a whole.

Before Step 0017, the implementation combined information gain, semantic shift,
query overlap, balance, coverage, label quality, and several penalties with
fixed coefficients. The current implementation replaces that heuristic mixture
with one resource-weighted normalized information-gain objective. This is an
algorithm-detail change: it does not change the thesis, the two core
abstractions, or the four RQs, and it does not introduce a new named mechanism.

For a contiguous interval $I$, eligible visible field $f$, and candidate cut
$b$, let $H_w(f,I)$ be the categorical entropy of $f$ under operation weights.
The normalized gain for that field is

```text
G_f(I,b) = [H_w(f,I)
            - (W_L/W_I) H_w(f,L)
            - (W_R/W_I) H_w(f,R)] / H_w(f,I).
```

The cut score is the equal mean of $G_f(I,b)$ over eligible fields whose parent
entropy is positive. Candidate cuts occur only where adjacent operations differ
in at least one eligible visible field. Eligibility retains the existing
target-blind field rules: remove declared oracle/label, metadata, noisy,
session-by-default, near-numeric, constant, and high-cardinality fields. These
rules define the visible input schema; they do not score or accept a split.

For $n=|I|$ operations, the fixed complexity penalty is
$P(I)=\ln(n)/(2n)$. The inducer selects the largest mean gain and accepts it iff
$G(I,b)>P(I)$. There is no separate fixed score threshold, minimum node weight,
minimum second-child weight, majority-fraction gate, label-quality gate,
semantic-shift term, balance term, coverage term, or candidate subsampling.
Both children need only be nonempty. Maximum depth remains an explicit runtime
bound, fixed at four for the matched experiment.

The split's primary field is the positive-gain field with the greatest
$G_f(I,b)$ whose dominant weighted values differ between the two children.
Each child frame is `field=value` from that dominant value. Every accepted
split appends exactly one frame even if the same text appeared at an ancestor,
so the two children always have distinct reconstructable paths. If two distinct
raw values normalize to the same emitted folded frame, the implementation adds
a deterministic value-derived suffix; the common case remains `field=value`.
For a field,
query relevance is the fraction of supplied lowercase query terms that occur
as substrings of the lowercase field name or any parent-interval value of that
field. It breaks only exact per-field gain ties; a cut inherits its selected
primary field's relevance to break exact mean-gain ties. Earlier cut and then
lexical field order are the remaining deterministic tie-breaks. Query relevance
never changes $G$. Recursion ends at the depth limit or when no cut strictly
exceeds the penalty.

This revision is intentionally small: no new named abstraction, learned model,
or benchmark-specific feature enters the profiler. Its implementation and
tests must establish oracle-field exclusion, exactly one leaf assignment per
operation, additive-weight conservation, positive accepted gain, termination,
and deterministic output. Its paper value must then be tested through the real
Rust path on complete existing annotated workloads; unit tests and a one-case
preflight are engineering evidence only.

The principle behind the design is deliberately stronger than the individual
formula: stack induction should be a recursive partition of resource-weighted
operations under one explicit objective, not an accumulation of independently
tuned heuristics. Information gain and binary segmentation are established
ingredients; the research question is whether combining them with agent-visible
operation fields, additive profiling weights, and reconstructable stack frames
produces a useful profiling hierarchy. The complete proposal, including its
non-novel precedents, invariants, empirical boundary, and next single-variable
test, is recorded in Step 0017's `algorithm-note.md`.

### Learned boundary fields

External or learned models may derive fields before stack construction. They
remain optional backends and must be evaluated on held-out families. A learned
boundary model does not create a third boundary object in the profiler.

## Profile Measures And Output

One profile declares one sample measure and unit. Existing views cover operation
count and resource/effect-oriented measures such as tokens, time, files, and
network or system effects when those values are present in the source.

The pprof, folded-stack, JSON, and SVG outputs are serializations or renderers
of the same weighted operation-stack paths. The flamegraph is not the research
abstraction.

## Ranking And Diagnosis Boundary

A profile assigns recorded measure to groups. A diagnostic experiment then
tests whether high-priority groups correspond to independently labeled
failures, unsafe effects, or wasted work. These are different statements:

- **accounting:** an operation contributes its value to a declared profile path;
- **diagnostic correspondence:** a profile group overlaps an external problem
  label under a declared metric;
- **causality:** the group caused the problem.

The current system supports visible-text and visible-operation rank rules.
Ranking is a policy over profile groups, not a third core abstraction. The paper
must not infer causality from diagnostic correspondence.

The completed Hodoscope comparison adds a second boundary. A fixed 8/32/128
recursive partition did not reliably reduce first-hit inspection work. The
official Hodoscope density-gap/FPS bundle was decisively stronger, while adding
recursive parents to identical terminal clusters had no stable effect. The
design consequence is not another ranking subsystem. It is that the useful
stack may depend on how the recorded measure is distributed. A working
hypothesis is that a sparse action-level effect and an additive change spread
across recurring phases need not reward the same projection. Only the sparse
condition has current evidence; the additive-regression condition remains
untested.

The complete HINTBench experiment adds a target-blind transfer boundary rather
than a new abstraction. A fixed action/environment/phase/status profile had a
favorable inspection-work point estimate but did not separate from raw action
under the predeclared paired interval. The next mechanism therefore keeps the
same two-object model. Later AgentProcessBench and TraceElephant results supply
the cumulative positive RQ2 answer at their evaluated AP and recall operating
points; HINTBench remains one scoped transfer boundary rather than a reason to
change the model or RQ.

## Archived Proposal Mechanisms

The pre-recovery paper accumulated reviewer-generated mechanisms beyond the two
core abstractions. Their detailed names, contracts, and rationale remain in the
timestamped archive, not in the current design. None is an implemented or
claimed contribution. A future experiment may add one ordinary mechanism only
if it resolves a specific RQ more directly than the existing design.

## Invariants

- All profile outputs derive from operations and operation stacks.
- Every sampled operation contributes at most once to one path in a given
  projection, unless a profile explicitly declares a different aggregation.
- Changing the stack changes the projection, not the source operations.
- Source-native hierarchy fields remain available for baseline views when the
  input supplies them; the profiler does not infer missing native lineage.
- Scoring-only labels never enter mapping, stack construction, ranking, or
  tuning for the target evaluation split.
- Mappings, profile specs, and rank rules used in an experiment are visible and
  replayable.
- Trace import returns to operation semantics before profiling; a trace format
  is an exchange container, not a third profiler abstraction.
- Negative results for one stack constructor do not change a fixed RQ, weaken
  its positive hypothesis, or redefine the two core abstractions; they direct
  the next mechanism, signal, workload, or protocol revision.

## Deliberate Non-Goals

The current design is not:

- a complete multi-parent provenance graph;
- a counterfactual causal model;
- a universal automatic intent or failure-boundary detector;
- an automatic repair recommender;
- a replacement for OpenTelemetry, OpenInference, Perfetto, or trace UIs;
- a claim that one semantic hierarchy dominates every task.

## Evaluation Consequence

RQ1, RQ2, the human-boundary component of RQ3, and RQ4 have paper-linked
evidence. The current implementation step first replaces and directly tests
the shipped Rust induction algorithm described above, because the paper now
evaluates a separate supervised boundary predictor rather than that built-in
path. The full experiment reuses existing annotated operations and scoring
machinery. Only independently available labels score the induced output;
scorer labels and aliases stay out of induction inputs. This repairs the
mechanism/evidence mismatch without changing RQ3 or introducing another
dataset, classifier, or paper story.
