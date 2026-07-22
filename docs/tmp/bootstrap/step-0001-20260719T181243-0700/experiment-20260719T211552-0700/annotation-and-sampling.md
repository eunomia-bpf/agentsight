# Annotation And Sampling Contract

Status: frozen proposal for independent review; no scientific annotation has
started.

## Nested Units

### Workspace supervision interval

The sampling and supervisor unit is a **workspace supervision interval**. It
starts at a prospectively declared capture boundary $H_0$ and ends at the final
source action of one label-independently selected target goal. It contains:

- the complete retained workspace history since $H_0$;
- at least one completed prior explicit top-level goal;
- the target explicit top-level goal;
- at least two resumed or replaced top-level Agent sessions; and
- exact snapshots at $H_0$, each goal boundary, and interval end $W_T$.

A top-level session is a user-owned Agent context that can be resumed or
replaced. Context compaction and automatic continuation do not start a new
session. Spawned workers, parallel subagents, delegated research tasks, and tool
subprocesses inherit their parent's session/goal and do **not** satisfy the
multi-session criterion.

The prior-history window is label-independent: the complete capture from $H_0$
to the target goal start. It is never shortened around a pathology, last access,
Git commit, token limit, or convenient session. Full-History Raw and Trajectory
receive the identical complete interval; Target-Only Raw and Trajectory receive
the identical target-goal window; Session Local receives the complete interval's
exact session partition.

### Goal episode

Within an interval, a **goal episode** begins at an explicit top-level user goal
and ends immediately before a later top-level instruction replaces that goal,
or at the interval's final source action. A clarification, correction, added
constraint, compaction, or automatic continuation remains part of the current
goal unless it replaces the objective. Spawned tasks inherit the active goal.

Pathology and intervention labels are emitted for every included goal. The
target-goal record is the main diagnosis target. Annotators also record whether
the same pathology/evidence pattern occurred in a prior goal, so the study can
measure incremental cross-goal recurrence rather than only concatenated
within-goal sessions.

## Prospective Capture And Atomic Exact State

Before any source action in a registered run:

1. freeze the workspace identity and in-scope roots;
2. freeze exclusions such as `.git` object storage and named ephemeral caches;
3. create an isolated Btrfs workspace subvolume/mount namespace and place every
   Agent, harness, child and background writer in the owned cgroup;
4. retain an atomic $H_0$ read-only snapshot and manifest; and
5. start complete native/system capture for every supported Agent source.

The controller applies the freeze/quiescence/syncfs/read-only-Btrfs-snapshot
protocol in `plan.md` before dispatching a new goal. It records monotonic/wall
time, last completed source/system action, cgroup/process membership, open-writer
audit, and snapshot/mount identity. Any in-flight action, external writer,
failed freeze/sync/snapshot, or clock-order inconsistency rejects the run.

At every goal boundary and at $W_T$, retain the resulting atomic archive and manifest.
For regular files the manifest contains raw-byte SHA-256, path, mode, size, and
type; for symlinks it contains the link target; for directories it preserves
existence. The archive and manifest have their own hashes. A Git commit or
nearest checkout is outcome metadata, not an exact snapshot.

An existing historical interval is eligible only if it already has the same
exact artifacts or if deterministic replay from an exact retained start
reproduces every boundary manifest and accounts for every source/system effect.

## Boundary Annotation

Two independent human boundary annotators who did not implement a tested view
see only:

- top-level user instructions;
- timestamps;
- parent/session/source relations;
- workspace identity and capture scope; and
- exact snapshot availability.

They do not see outcomes, condition views, pathology labels, or supervisor
outputs. Each independently marks $H_0$, every goal start/end, target goal,
genuine top-level sessions, inherited children, and one boundary status:

- `resolved`;
- `goal_ambiguous`;
- `session_ambiguous`;
- `concurrent_goal_contamination`; or
- `snapshot_missing_or_approximate`.

Both files are retained before a third human adjudicates. Any unresolved
ambiguity makes the candidate ineligible; it is never repaired using pathology
knowledge.

## Eligibility

An interval is eligible only when all conditions hold:

- complete source-native session records are affiliated by frozen workspace
  identity/cwd/project/remote; line-selected `--global` search matches alone are
  ineligible;
- at least two genuine top-level sessions and at least two explicit goals;
- at least 50 Tool actions and 20 artifact effects across the interval;
- at least one prior goal has ended before the target goal starts;
- atomic retained snapshots and boundary-order records exist at every required
  boundary;
- source-call IDs are present and unique within source session;
- source-reported effects and net snapshot changes pass the coverage audit, with
  no unattributed goal/evaluator/harness-relevant change; and
- no unresolved concurrent top-level goal changes the same workspace.

Every exclusion receives one frozen reason:
`boundary_uncertain`, `incomplete_source`, `insufficient_actions`,
`insufficient_artifact_effects`, `missing_prior_goal`,
`parallel_children_only`, `snapshot_missing_or_approximate`, `snapshot_nonatomic`,
`effect_coverage_failure`, `duplicate_goal`, or
`concurrent_goal_contamination`.

## Frozen Registry And Fixed Sampling

Sampling is stratified into coding and non-coding auto-research. Before capture,
`raw/registry.json` freezes 40 scheduled runs/domain, the common capture window,
run/workload/Agent/harness/skill/base-image metadata, and at least eight
workspace/task-family clusters per domain with at most five runs/cluster.

1. Keep all 40 registered runs/domain in the capture-yield denominator,
   including crashes and ineligible runs.
2. Enumerate exactly one candidate/run: the first target goal following a prior
   completed goal and a top-level session resumption/replacement. Never reuse a
   target goal or substitute a later target.
3. Within each domain, sort eligible registered runs by SHA-256 of
   `workspace_scope_hash || capture_start || target_goal_start ||
   target_goal_end || sorted_top_level_session_ids`.
4. Take the first four per domain for guide development. These eight intervals
   are permanently excluded from every scientific estimate and held-out test.
5. Take the next 24 per domain for the fixed feasibility census. There is no
   optional stopping, positive-count stopping, or replacement based on labels.
6. Later eligible runs are unused reserve. If fewer than 28/domain are eligible,
   fail; do not extend the registry or capture window.

The fixed 48 scientific intervals are a feasibility census, not the later
accuracy test set. None may enter held-out diagnosis evaluation.

## Pathology Labels

- **stagnation:** after observable goal-relevant progress, a sustained interval
  repeats or continues work without further artifact, evaluator, or decision
  progress. Time/action volume alone is insufficient; the annotation cites the
  repeated action/effect pattern and the last preceding progress evidence.
- **goal_drift:** a sustained interval acts on artifacts or questions that do
  not support the explicit goal and never returns a source-backed dependency.
  Exploration that later becomes goal-relevant is not drift.
- **validation_gap:** a goal-relevant artifact is created or modified, but the
  goal ends or is replaced without observed validation relevant to that change.
  An explicit failed validation plus unresolved handoff is not a missing
  validation; it may be a different pathology.
- **harness_waste:** a skill, instruction, hook, orchestration rule, or recurring
  harness behavior causes actions that add neither goal-relevant artifact
  progress nor validation/decision evidence. The causal harness requirement and
  corresponding harness artifact/instruction must be cited; general
  inefficiency is insufficient.
- **healthy_progress:** none of the four pathologies applies and source-backed
  goal progress exists.
- **insufficient_evidence:** complete permitted evidence still cannot support a
  confident judgment. It is reported, never coerced into a negative label.

For each label on each goal, annotators record:

- `present: true|false|insufficient`;
- a minimal sufficient set of canonical
  `<session_id>#<source_call_id>` evidence actions;
- affected artifact paths or persistent state objects;
- onset/earliest-supporting action;
- confidence on a fixed three-level scale; and
- for a target-goal positive, `prior_recurrence: none|same_pattern|related` with
  prior goal/evidence IDs.

Cross-goal recurrence is descriptive truth. It is not inferred merely because
the same path or tool name appears twice.

## Intervention Labels

For every goal, annotators answer whether a retrospective automatic supervisor
should intervene before the goal ends, the earliest source action after which
that decision is supportable, and one action:

- `continue` — no intervention;
- `stop` — halt wasteful or unsafe work;
- `redirect` — return to a goal-relevant plan/artifact;
- `clarify` — request missing goal or acceptance information;
- `repair_harness` — change a cited skill/instruction/hook/orchestration artifact.

They also record the target path/goal/harness component, minimal evidence set,
and one-sentence source-grounded rationale. These are expert retrospective
recommendations, not causal proof that an intervention improves outcome. Such a
causal claim would require a separate replay/injection experiment.

Intervention is part of the fixed scientific contract. If need/action/earliest
evidence cannot meet the admission criteria in either domain, this dependency
fails; the output is not silently removed.

## Independent Human Procedure

1. Freeze interval boundaries, snapshots, source manifests, sampling order,
   guide, and schemas.
2. Two qualified human experts with prior autonomous-Agent trace-review
   experience and no role in implementing a tested view independently inspect
   complete raw records, atomic snapshots, explicit goals, task/evaluator/test
   evidence, and declared harness artifacts.
3. Each emits one schema-valid JSON record without seeing another annotation,
   condition view, supervisor output, or generated diagnosis.
4. Compute all pre-adjudication statistics and preserve both raw files.
5. A third qualified human adjudicator resolves disagreements from the same
   source bundle and emits the gold record plus a source-backed resolution note.
6. Freeze gold records before constructing any supervisor condition.

Agent-produced dry runs are segregated under `mechanics/`. They may validate
JSON syntax or viewer behavior only. They cannot change the guide, thresholds,
sample, admissibility, evidence, gold labels, or any reported statistic.

## Development And Scientific Separation

The eight development intervals may be used to clarify ambiguous wording before
the guide freezes. Both human annotators rerun every affected development item.
Development cases and dry-run Agent output are excluded from:

- prevalence and positive counts;
- raw agreement, AC1, kappa, and positive agreement;
- evidence/earliest-action agreement;
- admission thresholds;
- later power nuisance estimates unless a future plan explicitly allocates a
  separate development pilot; and
- all held-out supervisor evaluation.

No wording changes after scientific annotation starts. A newly discovered label
defect stops the node and returns to the outer idea gate.

## Fixed Feasibility Statistics

Use the fixed 48-item census; no interval is treated as statistically independent
when it shares a frozen workspace/task-family cluster. Point estimates remain
interval-weighted. Uncertainty uses a 10,000-replicate stratified cluster
bootstrap that resamples complete clusters within domain and preserves every
within-cluster interval/annotation pair. Report percentile and BCa 95% intervals,
cluster count/size, and effective sample size. Exact binomial intervals may be
reported only as descriptive sensitivity analyses, never as admission evidence.

Report for each domain and pooled:

- eligible/captured and sufficient-evidence proportions with cluster-bootstrap
  95% intervals;
- adjudicated prevalence for each pathology with cluster-bootstrap 95% intervals;
- pre-adjudication raw agreement, Gwet's AC1, and Cohen's kappa;
- positive agreement $P_{pos}=2a/(2a+b+c)$ for each pathology;
- evidence-action and artifact-path Jaccard among jointly positive annotations;
- exact and adjacent-action earliest-evidence agreement; and
- intervention-need, intervention-action, and earliest-intervention agreement.

Intervention need uses the same binary raw/AC1/positive-agreement thresholds as
pathologies. Action uses multicategory AC1 plus exact raw agreement; earliest
evidence uses exact and adjacent-action agreement, with the fixed numerical gates
in `plan.md`.

Every threshold in `plan.md` is conjunctive and non-bypassable. In particular,
high negative agreement cannot rescue low positive agreement, and pooled success
cannot rescue a failed domain.
