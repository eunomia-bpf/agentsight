# Target-Goal Truth Contract

Status: proposed, frozen for independent plan review.

## Units And Boundaries

A workspace supervision interval begins at registered $H_0$ and ends at the last
source/system action of one automatically selected target goal $g^*$. It includes
one or more completed prior top-level goals, $g^*$, and at least two genuine
resumed/replaced top-level sessions.

Compaction, automatic continuation, spawned workers, parallel subagents,
delegated subtasks, and tool subprocesses inherit their owning top-level
session/goal. They do not satisfy session resumption/replacement.

Two human boundary annotators who did not implement a tested view independently
see only user instructions, timestamps, parent/session relations, workspace
identity, capture records, and exact-state availability. They mark goals,
top-level sessions, inherited children, and the registry-selected target. A third
human adjudicates. Outcome/pathology/condition data cannot repair a boundary.

Boundary status is one of `resolved`, `goal_ambiguous`, `session_ambiguous`,
`concurrent_goal_contamination`, `snapshot_missing`, or `snapshot_nonquiescent`.
Only `resolved` enters eligibility.

## Eligibility

Every scientific target requires:

- one registered run and its automatically selected first eligible target;
- complete content-hashed native and system records, not global-search fragments;
- at least two top-level sessions, two explicit goals, 50 Tool actions, and 20
  artifact effects over full history;
- exact quiescent states at $H_0$, all included goal boundaries, and $W_T$;
- total and unique source-call IDs;
- no unattributed goal/evaluator/harness-relevant net state change;
- no boundary/order/scope/rename/concurrent-goal ambiguity; and
- one candidate only from that fresh run, with no shared history across runs.

Exclusion reasons are frozen and reported for all 80 registry rows.

## Target Pathology Labels

- **stagnation:** after target-goal progress, target actions sustain repetition or
  continued work without further target artifact/evaluator/decision progress.
  Time/action count alone is insufficient.
- **goal_drift:** target actions sustain work unsupported by the explicit target
  goal and never return a source-backed dependency. Exploration later used by the
  target is not drift.
- **validation_gap:** a target-relevant artifact is created/modified, but the
  target ends without observed validation relevant to that change. An explicit
  failed validation is not “missing” validation.
- **harness_waste:** a cited skill, instruction, hook, orchestration rule, or
  recurring harness mechanism causes target actions that add neither target
  artifact progress nor validation/decision evidence. General inefficiency is
  insufficient.
- **healthy_progress:** target progress exists and no pathology applies.
- **insufficient_evidence:** complete permitted evidence still cannot support a
  target judgment; never coerce it to negative.

For each target label, record `true|false|insufficient`, confidence on a frozen
three-level scale, affected artifact/state objects, earliest target onset, and a
minimal evidence set. Every positive evidence set contains at least one
canonical target-goal action/effect. It may additionally cite earlier evidence.

Let $L_{ira}\in\{T,F,U\}$ be reviewer $r$'s judgment for target $i$ and
pathology $a$, where $U$ is `insufficient`. Per-label sufficiency is
$S_{ira}=1[L_{ira}\ne U]$. A reviewer-level target record is sufficient iff all
four pathology labels **and** intervention need are non-$U$. The adjudicated
record uses the identical formula. Admission rule 2 requires both (a) at least
75% adjudicated record-level sufficiency per domain and (b) at least 75%
adjudicated sufficiency for every pathology and intervention need per domain.

## Target Intervention

For $g^*$ only, record:

- intervention need as `true|false|insufficient`;
- action: `continue|stop|redirect|clarify|repair_harness`;
- target path/goal/harness component;
- minimal evidence and rationale; and
- earliest **target-goal** source action after which intervention is supportable.

If need is `false`, action is `continue`; if need is `true`, action is one of
`stop|redirect|clarify|repair_harness`; if need is `insufficient`, action,
target, and earliest action are null. Evidence explaining insufficiency remains
mandatory.

Prior evidence may make an early target action interpretable, but the earliest
point cannot precede target start. This is an expert retrospective recommendation,
not causal proof that intervention improves outcome.

## Prior-Goal Auxiliary Records

Experts may annotate the same schema for prior goals solely to mark
`none|same_pattern|related` recurrence and verify cited historical evidence.
These records are stored in `auxiliary_prior_goals`, hidden from conditions, and
excluded from every scientific numerator/denominator, agreement/admission gate,
HTIR coverage, power input, and later score. They are never flattened into rows
beside target records.

## Human Procedure

1. Freeze registry, boundaries, raw manifests, target selection, guide, and JSON
   schemas.
2. Use exactly four development targets/domain (eight total) for guide wording;
   rerun both humans after any development-only change.
3. Freeze the guide permanently.
4. Two qualified humans independently annotate 24 scientific targets/domain from
   full raw evidence and exact states without any condition/supervisor output.
5. Retain raw submissions and compute pre-adjudication target-only statistics.
6. A third human adjudicates and emits source-grounded target gold plus separate
   auxiliary prior-goal records.
7. Freeze gold before condition construction.

Agent outputs may check JSON syntax/viewing on development fixtures only. They
cannot change wording, selection, thresholds, truth, or PASS.

## Target-Only Statistics

For the 48 scientific target records, report pooled and per domain:

- target sufficient-evidence rate;
- target pathology prevalence and positive counts;
- raw agreement, Gwet AC1, Cohen kappa, and positive agreement;
- jointly positive evidence-ID and artifact-object Jaccard;
- exact/adjacent target-onset agreement;
- target intervention-need agreement;
- intervention-action raw agreement and multicategory AC1; and
- exact/adjacent earliest-target-action agreement.

Denominators are frozen as follows; every one of the 48 targets appears in the
retained denominator table even when a statistic is not mathematically defined:

1. For each pathology and intervention need, raw agreement and multicategory
   Gwet AC1 use all 48 paired judgments with categories $T,F,U$. Cohen kappa is
   reported on the same three categories. `insufficient` is never converted to
   `false` or dropped.
2. For a binary positive-agreement report, $T$ is positive and $F/U$ are
   nonpositive solely for this formula:
   $PA=2n_{TT}/(2n_{TT}+n_{TF}+n_{FT}+n_{TU}+n_{UT})$. Thus a one-sided
   true/insufficient pair is a disagreement. Bilateral insufficient and
   false/insufficient pairs are separately counted and reported; they cannot
   inflate positive agreement. A zero denominator is undefined and fails the
   corresponding admission gate.
3. Evidence-ID Jaccard, artifact-object Jaccard, and onset agreement use exactly
   the independently jointly-positive targets for that label. The table reports
   the all-target joint-positive indicator and exclusion reason (`not_joint_true`
   or `missing_required_field`). Zero jointly-positive targets is undefined and
   fails; missing evidence/onset on a joint positive counts as zero agreement.
4. Intervention-action and earliest-intervention agreement use exactly targets
   for which both reviewers mark intervention need `true`. Zero such targets is
   undefined and fails; a missing action/earliest point counts as disagreement.
   Need-disagreement and insufficient counts remain visible in the all-target
   table and in the three-category need statistics.
5. Pooled and per-domain statistics use these same formulas. Adjudication does
   not alter their denominators. No complete target is silently discarded from
   sufficiency or three-category agreement.

Point estimates weight targets equally. Uncertainty resamples complete frozen
workspace/task-family clusters in 10,000 stratified bootstrap replicates and
reports percentile and BCa 95% intervals. Prior goals are absent from the
resampling table.

The numerical admission thresholds are exactly those in `plan.md`; all are
conjunctive. High negative agreement, pooled success, prior-goal positives, or
adjudication cannot rescue failed independent target-positive agreement.
