# AgentProf Design

## Design Goal

**Agent observability needs profiling, not only debugging.** AgentProf converts
heterogeneous agent histories, operation files, and supported trace containers
into weighted profile projections that existing profiler tooling can read.
Operations and operation stacks implement this thesis. Multi-resolution cross-run recurrence,
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

An operation stack is an ordered recursive path derived from operation fields.
For example, the following runtime-field projection is supported and remains a
useful baseline:

```text
project -> task -> phase -> tool -> action -> status
```

This path is not the paper-level task-semantic main stack. The main semantic
responsibility target is:

```text
concrete task -> subtask (possibly nested) -> phase/strategy
              -> semantic action -> operation object -> result
```

Subtask nesting can be uneven and has no fixed depth. Agent, model, session,
tool, status, command, and path remain filters, colors, detail attributes, or
bottom-level evidence rather than consuming the main responsibility path.
Events, time, tokens, and source-linked effects are additive widths. A valid
task-semantic profile should expose where a task spends resources, repeats or
abandons work, produces evidence, and succeeds or fails, including differences
in task decomposition across agents.

The current artifact already supports the generic projection mechanism, while
automatic recovery of the full task-semantic path remains the next positive
mechanism target. Paper prose changes only after positive evidence. The same
operations can still be folded using a flat view, a source-native hierarchy, a
manually declared semantic stack, mapped fields, or induced recurring-operation
identities. Changing stack shape does not create another underlying event
object.

The completed source-native stateful prototype establishes a narrower design
boundary. Updating an unbounded stack once per native turn is mechanically
valid and improves substantially over treating low-level operations or native
turns as singleton task nodes, but a free transition policy repeatedly creates
new frame instances for an unchanged task label. That prototype is not the
current automatic constructor. The next mechanism must preserve the identity
of a continuing concrete goal before it tries to infer deeper topology; adding
more runtime fields, phase labels, or display layers cannot repair task
identity. Phase/action/object/result remain a transient evidence suffix below
the task path, and agent/model/session/tool/status remain metadata.

The profiling identity of a constructed task stack is its complete ordered
visible label sequence. Internal frame-instance IDs may preserve controller
lineage, but they are not emitted semantic frames and do not prevent equal
visible paths from folding. Repeated adjacent labels remain distinct depths in
the ordinary folded representation; removing them is a constructor
normalization experiment, not standard flamegraph behavior. Session can
namespace an occurrence-level accuracy evaluation without becoming a stack
frame or authorizing cross-run semantic equality.

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

`--induce-operation-stack` derives reusable operation identities from one
simple cross-run principle: adjacent visible actions that recur together across
sessions are likely to belong to the same operation. This is an experimental
stack-construction backend over the existing operation/operation-stack model,
not another research abstraction.

Every target and reference operation must contain exactly one nonempty
`session` and `action`. Within each session, record order defines adjacency;
each transition contributes one occurrence regardless of the operation's
profile weight. A separate label-free reference corpus may be supplied with
`--induce-reference-operation-file`; otherwise the selected target corpus is
also the reference. Missing, multivalued, empty, zero-transition, or degenerate
inputs are explicit errors rather than triggers for a fallback heuristic.

For a reference transition population of size `B`, let `c_L(a)` and
`c_R(b)` count left and right action occurrences and `c(a,b)` count the
ordered pair. The implementation computes

```text
p_L(a) = c_L(a) / B
p_R(b) = c_R(b) / B
p(a,b) = c(a,b) / B
NPMI(a,b) = ln[p(a,b)/(p_L(a)p_R(b))] / -ln[p(a,b)].
```

A deterministic occurrence-weighted one-dimensional two-means partition starts
from the minimum and maximum finite NPMI values, assigns exact distance ties to
the lower center, and uses the midpoint of the converged centers as the global
cutoff. The same partition over action-changing reference occurrences supplies
a cross-action cutoff. Same-action target pairs use the global cutoff;
action-changing pairs use the smaller of the global and cross-action cutoffs.
Thus the refinement can only merge a boundary produced by the global rule and
can never add one. When every reference and target operation also has a
nonempty `action_detail`, the constructor fits the same recurrence model to the
compound `(action, action_detail)` signature. Detailed continuity may remove a
coarse boundary but can never add one; missing, unseen, or weak detail falls
back exactly to the coarse decision. In a target session, an unseen transition or a score
strictly below its applied cutoff starts a new group; every other transition
continues the current group. No depth, field search, hand-weighted score term,
complexity penalty, query tie-break, label-tuned threshold, or resource-weighted
transition count enters this decision.

When independently grouped historical operations are available, an optional
`--induce-calibration-operation-file` replaces only the two-means cutoff with
one supervised scalar. The score-reference operations remain separate and
still define the same NPMI table. Calibration operations must provide exactly
one `session`, `action`, and `group` value, and their sessions must be disjoint
from the target. The implementation enumerates a cutoff below the minimum
observed calibration score, every midpoint between adjacent distinct scores,
and a cutoff above the maximum, then selects the cutoff with the highest
per-operation B-cubed partition F1; every operation gets one vote regardless of
its profile resource value, and exact ties choose the smallest cutoff.
Unseen target transitions remain boundaries. This mode spends additional group
annotations to calibrate the existing recurrence score; it is not an
equal-information replacement for the default label-free constructor.

Each group receives a run-length-compressed action motif such as
`action=click-then-type-then-press`. Identical motifs therefore fold to the
same cross-session operation identity. If distinct raw motifs normalize to the
same emitted frame spelling, a stable value-derived suffix preserves identity.
The JSON report exposes every `(session,input-position)` boundary decision and
every segment's start, end, and motif, so aggregation cannot hide duplicated or
missing assignments.

Legacy information-gain knobs remain parseable only to produce a clear error:
`--induce-max-depth`, `--induce-query-term`, and
`--induce-allow-session` cannot affect recurrence. The deprecated
`--induce-task-stack` flag invokes the same implementation under the legacy
derived-field name.

Steps 0020--0024 developed the coarse recurrence objective directly on the
already completed OSWorld-Human and CodeTraceBench trajectories. That monotone
coarse predecessor reaches 0.6799 boundary F1 and 0.7862 ordinary B-cubed F1
on OSWorld-Human and 0.2871 / 0.6492 on CodeTraceBench. Step 0049 adds only the
detailed visible-action continuity arm above. OSWorld-Human has no
non-redundant detail and therefore falls back exactly to the coarse result. On
all 405 CodeTraceBench targets, multi-resolution recurrence reaches 0.2656
boundary F1 and 0.6627 ordinary B-cubed F1; the +0.0136 gain over coarse has a
task-cluster bootstrap 95% interval of [+0.0087,+0.0180] and is positive in all
four frameworks. Both populations had already informed mechanism diagnosis,
so these remain post-hoc implementation-selection results rather than fresh
confirmation of all RQ3, motif-name semantics, or cross-family generalization.

The Rust port was then checked mechanically against the approved Python
candidate. Independent raw review reproduced exact equality for all 3,691
boundary decisions, 3,978 motif assignments, 2,656 segments, 44 motifs, and
3,978 units of profile mass. Focused tests also show that arbitrary changes to
group, label, oracle, and target fields leave the complete induction report
unchanged when `session` and `action` are fixed.

Step 0030 evaluates the optional grouped-reference calibration on the same
already completed trajectories. Five-fold held-out OSWorld-Human B-cubed F1
rises from 0.7862 to 0.8011. A cutoff fitted on 483 solved CodeTraceBench
sessions and applied unchanged to 405 disjoint failed sessions raises B-cubed
F1 from 0.6492 to 0.6666. CodeTraceBench boundary F1 falls from 0.2871 to
0.2362, exposing a real fragmentation/merging tradeoff: the supervised mode
improves the predeclared partition objective, not every boundary metric. A
complete release-binary replay matches the Python experiment on all 3,691
OSWorld and 20,461 CodeTrace decisions, cutoffs, segments, motifs, and pooled
metrics. Because these trajectories already informed mechanism development,
the result is supporting implementation evidence rather than untouched
cross-family confirmation.

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

The final same-signal RQ2 consolidation keeps the two-object model and makes the
ranking boundary explicit. Under standard per-trajectory AP/MAP, the incumbent
semantic organization beats matched raw-action grouping on complete
AgentProcessBench, HINTBench, and TraceElephant populations, but direct local
evidence is stronger on AgentProcessBench. One adaptive, parameter-free
follow-up therefore preserves every strict local ordering and uses semantic
recurrence only to refine exact local-score ties. On the same observed
populations it improves MAP over local-only and semantic-only ranking on all
three workloads and over an identically composed local-plus-raw refinement on
HINTBench and TraceElephant; AgentProcessBench does not distinguish the two
secondary keys. The design consequence is the simple principle that grouping
may refine otherwise-equal local evidence but should not override stronger
local evidence. Because the candidate was selected on these populations and
its registered all-workload comparison is inconclusive, it is mechanism
evidence rather than a universal replacement or a new ranking subsystem. No
further score tuning on these populations is part of the design.

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

RQ1, RQ2, the task-partition, task-family, and human-boundary components of
RQ3, and RQ4 have paper-linked evidence. Steps 0017--0018 established that the
former information-gain runtime
objective did not match heterogeneous human operation groups. Steps 0020--0024
changed that objective to coarse cross-session recurrence, and Step 0049 added
the detailed visible-action continuity arm specified above. The current rule
keeps OSWorld boundary F1 0.6799 and B-cubed F1 0.7862 unchanged through exact
coarse fallback, while reaching 0.6627 B-cubed F1 on CodeTraceBench versus
0.6492 for coarse recurrence and 0.5411 for raw-action grouping. The Rust port
reproduces the evaluated decisions and conserves every unit. Because both label
populations informed mechanism development, this is
implementation-selection evidence, not fresh confirmation of the whole RQ3
hypothesis. Further field, depth, penalty, threshold, or score-term tuning on
either reused population is not part of the design.

Step 0031 adds a distinct RQ3 measurement without changing the two-object
model: the existing local tagger can assign a separate task field from
user-declared labels. On all 1,012 AgentBoard goals, the fixed Qwen3.6-27B
backend reaches 0.695 macro-F1 and 0.733 accuracy versus majority 0.044 and
0.248, with exact three-run stability. This supports task-family labels for the
named backend; it does not turn tag assignment into a third abstraction or
establish phase/action labels and unknown-family transfer.
