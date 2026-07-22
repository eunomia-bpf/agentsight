# Same-Source View Contract

Status: frozen proposal for independent review.

## Common Membership And Identity

Every condition binds to one immutable workspace supervision manifest. Full-
history conditions use the identical $H_0\rightarrow W_T$ interval. Target-only
Raw and Trajectory use the identical target-goal action window, its atomic
start/end snapshots, target evaluator evidence, and the same static task/skill/
harness specifications. This paired window difference is explicit rather than a
hidden membership change.

Native actions use `<session_id>#<source_call_id>`. System effects, snapshot
manifests/bytes, evaluator records, and static specifications use typed
`system:`, `snapshot:`, `evaluator:`, and `spec:` canonical IDs. Every derived
object carries the sorted bottom-level IDs supporting it, and the matching Raw
scope must byte-retrieve them. No renderer, adapter, index, or budget truncation
changes its declared scope. Unsupported items are typed, never silently dropped.

## Condition Contract

| View | May expose | Must not expose |
|---|---|---|
| Final State/Outcome | exact $W_T$, declared evaluator/outcome, final artifact metadata | intermediate order, prior reports, generated process labels |
| Native Report | source-native assistant reports inside the full interval, with native timestamps/session IDs | later messages, generated summaries, hidden evaluator commentary |
| Counts | action/session/goal/token/artifact/duration/status counts over full membership | artifact paths or evidence text that make localization possible |
| State Diff | exact create/delete/rename/content/mode changes between retained $H_0$ and $W_T$ | nearest-commit approximations, intermediate order, reads, retries, session boundaries |
| Session Local | one genuine top-level session's native/system/evaluator records, enclosing goal snapshots and static specs per reset run; inherited children remain with parent | other-session raw evidence, shared scratchpad, prior session outputs |
| Full-History Raw Retrieval | every permitted native/system/snapshot/evaluator/spec record in the full interval through generic indexes and byte retrieval | derived lifecycle, flow, recurrence, conformance, pathology, intent, or generated summary |
| OCPM Features | frozen official object-centric process-mining outputs from the full interval | label-informed feature selection, LLM-generated intent/cause, invented conformance rules |
| Full HTIR | faithful HarnessFix ladder, source-backed TraceSteps/links/effects/anchors/layers for full membership | weakened ordered-step proxy, annotation-derived edges, invented anchors, implicit cross-goal recurrence |
| Full-History Workspace Trajectory | source order, artifact lifecycle, exact state changes, workspace relations, real session/goal boundaries, cross-goal recurrence candidates, candidate-validation links, typed raw IDs | generated pathology, intent, cause, or summary unavailable in raw evidence |
| Target-Only Raw Retrieval | identical generic Raw interface over target actions/effects, target start/end snapshots, target evaluator and static specs | any prior-goal action/effect or derived structure |
| Target-Only Workspace Trajectory | identical projection over the target scope, excluding prior-goal actions and recurrence | prior-goal evidence, generated diagnosis/intent/cause |

Full-versus-target is the declared longitudinal ablation. Within either scope,
Raw and Trajectory receive identical bottom-level evidence and the same broker
budget. Other minimal conditions intentionally expose reduced representations
whose membership is fixed in `plan.md`.

## Exact State Diff

State Diff compares the retained scope manifests and raw bytes at $H_0$ and
$W_T$:

- create/delete from path existence;
- rename only when exact content identity plus source/system rename evidence
  supports identity; otherwise emit delete+create;
- content change from raw-byte SHA-256 inequality, with optional deterministic
  text diff for decodable files;
- mode/symlink/directory change from manifest fields; and
- `unattributed_external_effect` for a net change lacking source/system evidence.

Git commit IDs may accompany the two boundaries but never supply missing bytes.
Both boundaries must be atomic read-only snapshots created under the frozen
cgroup/quiescence protocol. Missing or live-copied state fails the case.

## OCEL 2.0 Evaluation Adapter

OCEL exists only to run established OCPM baselines:

- **event:** one source Agent action; zero-file-effect actions remain events;
- **event ID:** canonical action ID;
- **event type:** normalized source Agent/tool category and name;
- **object types:** artifact/file, directory/workspace scope, top-level session,
  inherited child session, explicit goal, optional harness artifact, and declared
  evaluator/run object;
- **event-object relation:** source/system-backed read, write, create, delete,
  rename, validate, execute-on-path, session membership, or goal membership;
- **object-object relation:** path hierarchy, source-backed rename identity,
  explicit parent-session relation, goal succession, or other retained relation;
- **object attribute history:** path, existence, content hash, type, and mode at
  exact action/snapshot time where available.

An arbitrary Bash command does not become a file effect without path-level
source/system evidence. A directory argument can be a weak access relation but
not a file read. Git commits may be objects/milestones for outcome binding but
never define Agent-event time, goal boundaries, or workspace snapshots.

The adapter emits schema-valid OCEL 2.0 plus a source-coverage report. It does
not become a shipping IR or production dependency; `agent-session` remains the
source abstraction.

## Frozen OCPM Projection

Using `pm4py==2.7.23.3` and `ocpa==1.3.4`, expose only the families frozen in
`plan.md`:

1. OC-DFG activity, edge, unique-object frequency, and performance tables;
2. per-object lifecycle traces, variant counts, length distribution, and
   entropy;
3. object-interaction graph degree, connected-component, and type-pair tables;
4. event/object type counts and duration summaries; and
5. official object-centric Petri-net discovery and token replay/conformance
   results when executable.

Normative conformance constraints must be quoted and hashed from a task,
evaluator, skill, or harness specification frozen before annotation. A missing
constraint yields `not_applicable`; pathology labels cannot manufacture it.
Outputs carry tool version, command, configuration, and OCEL hash.
All four non-conformance feature families run on every eligible scientific
interval. Only conformance without a pre-frozen normative specification may be
`not_applicable`; execution failures are reported and fail the obligation.

## Full-HTIR Fidelity Projection

The baseline targets HarnessFix revision
`9167a0b9a58748c73b56c3ee04fdc3437ba0c56e` and preserves its published ladder:

- `Raw`;
- `Raw + data-flow`;
- `Raw + data/control`; and
- `Full HTIR`.

Full HTIR must contain recoverable TraceSteps with request/response, derived
role, status, and artifact/state effect; data/context-flow links with precise
source/target spans and reuse relation; control-flow links with trigger logic and
condition/status; effect entity/transition/support; concrete implementation
anchors with relation/support; and responsibility-layer mapping when supported.

Every edge, effect, and anchor cites typed Raw IDs for native/system/evaluator
records or frozen harness/spec artifacts. The adapter/reproduction cannot use human pathology annotations,
intervention labels, or Workspace Trajectory output. A field-level fidelity
report marks `present`, `source_unsupported`, or `implementation_incompatible`
for every required element. Any missing required family makes Full HTIR
infeasible; ordered actions plus file effects cannot be relabeled Full HTIR.

Compatibility is frozen in the run registry from trace/harness/interface facts,
never labels. Full HTIR runs on every eligible compatible interval and must meet
the per-domain, per-cluster, success-rate, and shared-target label-coverage gates
in `plan.md`. A single successful case cannot satisfy closest-work coverage.

## Workspace Trajectory Projection

This is a raw-grounded process view, not a diagnosis. Every listed item cites
bottom-level Raw IDs and is rejected by parity audit if Raw cannot return the
same bytes:

- all actions in source order with real timestamp and session/goal identity;
- artifact lifecycle from exact state plus source/system effects;
- read/write/create/delete/rename/validate/execute-on-path relations;
- directory/path hierarchy and source-backed rename identity;
- goal succession and top-level-session resumption/replacement;
- inherited child-session ownership;
- candidate-validation relations under the rule below; and
- cross-goal recurrence **candidates** such as repeated access/action motifs,
  explicitly marked as candidates rather than pathology.

It must not emit “stagnation,” “drift,” “waste,” “failed because,” “intended to,”
or “should intervene.” Those remain supervisor predictions evaluated against
independent human truth.

## Candidate-Validation Relation

A candidate validation relation is temporal and scope-based, not causal. It may
be emitted only when:

1. a source/system-backed test, checker, evaluator, build, read-result, or other
   validation action occurs after a source-backed artifact write;
2. its declared/observed scope contains the changed path, module, artifact type,
   or evaluator target; and
3. both endpoint source IDs and the deterministic matching rule are retained.

The relation records `candidate`, `scope_rule`, `write_source_id`,
`validation_source_id`, and temporal distance. “Validated,” “validation passed,”
and “failure caused by” are not emitted unless an explicit evaluator record
states that fact, and even then remain evidence rather than diagnosis.

## Cross-Goal Recurrence Candidate

A recurrence candidate may be emitted when a target-goal action/effect motif has
an exact deterministic match in prior-goal history—for example the same
normalized action category on the same artifact, or the same write-then-check
sequence under a frozen matcher. It carries both goal/action sets and matcher
version. It never declares semantic equivalence or pathology. Full-History Raw
contains both underlying action sets so a supervisor can recover the candidate;
Target-Only Trajectory/Raw both omit the prior side by construction.
