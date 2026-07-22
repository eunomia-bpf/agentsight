# Research Design Frontier

The proposed method reconstructs a persistent workspace trajectory from
existing `agent-session` records and immutable post-session workspace
snapshots. It does not define another general event model.
The planned representation will retain:

- ordered native tool actions across session and vendor boundaries, including
  actions with no resolved file effect;
- artifact paths and read/write/create/rename/delete lifecycle effects;
- immutable post-session manifests and their exact file-state differences; and
- source IDs that let a supervisor retrieve each supporting native record or
  registered snapshot byte.

The planned interface lets an automatic supervisor Agent query this projection
for bounded evidence rather than ingesting animation pixels or an unbounded
concatenation of logs. The representation exposes actions, file effects,
lifecycles, session differences, and supporting source records. The
supervisor emits one bounded continuation intervention or `ABSTAIN`; the query
layer does not generate a diagnosis or recommendation. Every returned item must
cite bottom-level raw identifiers that the matched Raw condition can retrieve
byte-for-byte. The intervention is evaluated only by executing a forked worker
continuation and invoking the official benchmark oracle.

Agent Nebula renders the same underlying action history as a standalone artifact. Its force layout, attention decay, directory colors, lifecycle effects, and media encoding remain governed by `docs/repository-nebula.zh-CN.md`. Layout quality is an implementation and demonstration concern in the current AAAI study, not a paper-level RQ.

The current method intentionally excludes generated semantic labels as a required input. Later semantic evidence may be retrieved from explicit session text for intent and reflection, but file motion alone cannot establish those claims.

## Neutral Core Projection

The paper method is a deterministic evidence projection, not the force-directed
Nebula layout and not a learned pathology classifier. For a frozen interval, let
`A` be all native tool actions in monotonic action order, `F` be
workspace-relative file artifacts, and `S` be admitted sessions. The
constructor performs one pass:

1. retain every action in `A`, including actions with no file effect;
2. assign its stable source ID and retain native session, vendor, tool/category,
   call status, and timestamp;
3. attach only adapter-qualified read, write, create, rename, or delete effects
   and close the action as `observed`, `no_effect`, or `unknown`;
4. update file existence and path lineage from qualified effects and retain
   exact immutable post-session manifests; and
5. preserve the source IDs supporting every emitted action, effect, and state
   difference.

No threshold, fixed event window, importance weight, command-text guess,
pathology label, generated intent, or outcome-dependent feature enters this
core. If evidence cannot establish a relation, the relation is absent or marked
unknown. This makes the projection outcome-independent and auditable; its value
must come from organizing the same facts available to Raw Retrieval.

## Formal Algorithm Contract

The research algorithm is a deterministic, source-linked projection. It is not
the force layout used by Agent Nebula and does not assign a pathology score.
For each native action, ordered by timestamp and stable source ID, retain

```text
a_i = (timestamp, session, vendor, call_id, tool_or_category, call_status)
id_i = (session, call_id)
```

and attach an action-effect status
`h_i ∈ {observed, no_effect, unknown}` plus zero or more effects
`(path, operation, previous_path)`, where `operation` is one of
`read`, `write`, `create`, `delete`, or `rename`. `previous_path` is populated
only for an observed rename. A failed native call contributes no successful
effect.

`observed` requires qualified source evidence for the emitted effect.
`no_effect` is permitted only when the adapter declares complete effect
coverage for that action and observes no effect. Missing or ambiguous evidence
remains `unknown`; the constructor never converts it into `no_effect`. In
particular, shell command text may be searchable Raw evidence but cannot create
a core file effect by itself. The resulting trajectory is the sequence of
`(a_i, h_i, effects_i)` sorted by `(timestamp, source_id)`.

If the input is already time ordered, construction is one pass over actions and
effects with path/artifact maps: $O(|A|+|E|)$ expected time and
$O(|F|+|A|)$ retained projection/index space. Sorting unordered inputs adds
$O((|A|+|E|)\log(|A|+|E|))$. The implementation may stream older action payloads
to storage while retaining their Raw IDs; the formal result does not depend on
an animation window, a decay constant, or a layout coordinate.

Artifact identity is not equated permanently with a path. An observed native
rename preserves lineage; delete followed by create does not unless the source
explicitly connects them. Each retained post-session manifest anchors exact
content state. A manifest difference is a state transition, not a causal claim,
and is never retroactively assigned to a nearby action. Any unresolved
disagreement about the task or workspace boundary blocks supervisor execution.

## Where Heuristics Are Allowed

The core above intentionally has no operation weights, importance decay,
hotspot threshold, recurrence similarity threshold, generated semantic label,
or query-generated intent. These belong to one of three separately named
layers:

1. deterministic query conveniences such as counts and exact filtering;
2. optional, independently ablated candidate indexes such as syntactic
   recurrence or validation linkage; or
3. Agent Nebula's visual layout, where force strengths, point sizes, color,
   decay, and animation timing affect presentation only.

This boundary is the main defense against an ad-hoc algorithm: a result must
survive removal of optional indexes, and the matched Raw condition must be able
to retrieve every bottom-level fact available to the trajectory condition.

## Minimal Query Surface For The Pilot

The static-full-context preflight is closed. The replacement candidate uses a
deliberately small, read-only interface over one source store. Full Raw and
Workspace Trajectory receive the following full-fidelity Raw operations:

- `list_sources()` returns neutral Raw source membership and identifiers;
- `search(query, scope, source_types, k)` returns matching Raw IDs and snippets
  using one frozen lexical method;
- `read_record(raw_id)` returns the exact source record or snapshot bytes; and
- `read_range(scope, start_raw_id, end_raw_id)` returns a contiguous source
  interval without summarization.

Workspace Trajectory Retrieval receives those same operations plus three
deterministic relational conveniences:

- `artifact_history(path)` returns source-backed reads, mutations, versions,
  renames, and deletion in order;
- `session_diff(from_session, to_session)` returns exact artifacts added,
  removed, or changed between two immutable post-session workspace snapshots;
  and
- `effects(action_id)` returns only observed file effects, with unresolved
  candidates explicitly marked `unknown`.

There is no `hotspot`, `importance`, `recurrence`, `validation`, anomaly, or
pathology query in the first pilot. The supervisor must derive such judgments
from returned source records. This removes hidden thresholds and prevents the
query layer from pre-solving the task. Optional recurrence or validation
indexes may be proposed later only as separately frozen and ablated methods.

All answers are deterministic projections of source-backed records and exact
quiescent workspace state. They do not generate pathology labels, intent, or
retrospectives. Raw can retrieve every bottom-level fact used by Trajectory,
including raw snapshot bytes rather than only precomputed diffs. Each pair
receives the same model, neutral prompt, output schema, total rendered
token/byte budget, and tool-call budget. The intended treatment is only whether
exact workspace relations are directly queryable.

## Relation Families Under Test

After RQ1 establishes an outcome benefit, RQ2 removes each registered
Workspace Trajectory relation family independently:

1. `artifact_history(path)`;
2. `session_diff(from_session, to_session)`; and
3. `effects(action_id)`.

Earlier-session source scope is not a fourth relation family. It is tested in a
separate matched contrast that removes those records identically from Full Raw
and Workspace Trajectory. Exact immutable snapshots bind session differences;
live copies and nearest Git commits are not substitutes. Git commits remain
optional milestones and never provide event time, goal boundaries, or implicit
success labels.

## Closed-Loop Comparison And Primary Estimand

The strong comparison is not “trajectory versus a summary” and no semantic gold
is constructed. For each official benchmark checkpoint `c`, freeze the prefix
workspace and source sessions, then create byte-identical forks for:

1. no intervention;
2. generic matched reflection/search without historical trajectory evidence;
3. same-source Full Raw Retrieval; and
4. Workspace Trajectory Retrieval with the same Raw tools plus only the
   deterministic relations above.

Each supervisor returns a bounded message or `ABSTAIN`. The message is appended
to the otherwise unchanged next official prompt. The same worker model,
reasoning effort, timeout, and remaining budget continue every fork in a fresh
top-level session. The unmodified official executable oracle returns outcome
`Y(c, condition)`.

The primary checkpoint-matched estimand is:

```text
Δ_workspace = E_c[Y(c, WorkspaceTrajectory) - Y(c, FullRaw)]
```

The no-intervention fork supplies realized benefit and harm for both evidence
conditions. The generic matched control tests whether any lift comes merely
from another inference/search pass:

```text
Gain(condition) = E_c[Y(c, condition) - Y(c, NoIntervention)]
Δ_structure = Gain(WorkspaceTrajectory) - Gain(GenericMatched)
```

All forks share the checkpoint, current official prompt, worker configuration,
continuation budget, and oracle. No Intervention invokes no supervisor. Generic,
Raw, and Trajectory share supervisor weights, output schema, decoding, and
budget ceilings but receive condition-specific interfaces; Raw and Trajectory
share the registered Raw universe. The supervisor cannot access future prompts,
benchmark ground truth, oracle code or results, repaired siblings, or another
condition's output. Repetitions are clustered by checkpoint and related
workspace/task families remain within one split.

Only after `Δ_workspace` is supported may component ablations remove
`artifact_history`, `session_diff`, or `effects`. A separate source-scope
contrast removes earlier-session records identically from Raw and Trajectory;
it is not a relation-family ablation.
Final State, Counts, State Diff, session summaries, AgentTether, OCPM, and HTIR
are secondary compatible controls rather than extra headline rows. A tie with
Raw but lower cost supports an efficiency claim only; parity with the generic
control or no intervention refutes the stronger representation claim.
