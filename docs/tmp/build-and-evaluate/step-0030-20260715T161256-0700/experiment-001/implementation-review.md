# Step 0030 Implementation Review

**Reviewed:** 2026-07-15
**Skill used:** `research-experiment-design`
**Review type:** focused read-only implementation audit before REAL PREFLIGHT
**Verdict:** **REVISE**
**Candidate cutoff fitted:** no
**Candidate metric computed:** no

## Scope

I completely read the current `research-experiment-design` skill, the approved
Step 0030 experiment plan and plan review, the full 881-line
`script/rq3_reference_calibrated_existing_traces_eval.py`, and every imported
project helper on which the new script relies. This included the established
OSWorld operation loader and eligibility functions, deterministic fold rule,
NPMI scorer, current Step 0024 fold predictor, CodeTrace visible-operation
loader, and boundary and B-cubed metric implementations.

I ran only an AST syntax parse, `--help`, and read-only population/identity
checks. I did not invoke preflight or full mode, fit any candidate cutoff,
construct candidate predictions, or calculate any candidate metric.

## Must-Fix Finding

### 1. OSWorld target-oracle isolation is asserted but not implemented

The approved plan requires each target fold's group annotations to be loaded
only after that fold's predictions have been persisted. The implementation
does not currently satisfy that order:

- `osworld_source()` loads the complete labeled operation file before any fold
  prediction, retains every eligible row's `human_group`, and even reads all
  target group values to count the 2,042 groups
  (`script/rq3_reference_calibrated_existing_traces_eval.py:283-306`).
- `score_osworld_fold()` receives this already-labeled `groups` object. Its
  later file-existence check at lines 341-346 does not make the target oracle
  newly available; it was already resident and reachable before prediction.
- The returned `prediction_before_target_oracle: True` and summary validity
  value are therefore hard-coded claims about an ordering that the data path
  does not enforce.

The current candidate functions happen to consume only the separately derived
`visible` action lists, so this review found no demonstrated target-informed
cutoff computation. Nevertheless, the implementation cannot truthfully claim
the approved leakage barrier, and a future local change could access held-out
labels without crossing any enforced boundary. Because target-label isolation
is an explicit invalidation condition in the plan, this blocks REAL PREFLIGHT.

The minimal repair is to separate the established eligibility/visible-input
path from the oracle path. Before prediction, retain only the already-registered
eligible operation identities and visible session/turn/action fields. Load and
retain group values for the four calibration folds only when fitting their
cutoff; after the target-fold prediction file exists, separately load that
fold's group values for scoring. The established eligibility predicate,
population, folds, score, candidate enumeration, and output format need not
change. The runtime validity field should be derived from this actual ordering
rather than set to `True` unconditionally.

## Checks That Pass

### Registered populations and isolation

The established OSWorld eligibility semantics reproduce exactly 287 sessions,
3,978 operations, 3,691 adjacent pairs, and 2,042 human groups. The unchanged
fold rule gives 45, 55, 60, 62, and 65 target sessions across folds 0--4.
`score_osworld_fold()` uses the other four folds for both NPMI construction and
cutoff calibration and predicts only the held-out fold.

The CodeTrace sources reproduce exactly 2,634 reference sessions / 108,569
operations and 405 failed targets / 20,866 operations / 20,461 pairs / 2,948
stages. Removing the target IDs leaves the registered 2,229-session,
87,703-operation score reference. The calibration selector yields exactly 483
solved sessions, 18,152 operations, and 2,886 stages. Calibration and target
IDs are disjoint, score-reference and target IDs are disjoint, and every target
is marked failed. The script reads failed-target stages only after persisting
the selected target predictions.

### Candidate and tie semantics

The implementation preserves the existing action-transition NPMI function and
unseen-transition-as-boundary behavior. It enumerates precisely one threshold
equivalence representative below the smallest observed score, every midpoint
between adjacent distinct scores, and one above the largest score. It maximizes
operation-weighted B-cubed F1 on reference annotations and, among exactly tied
objectives, chooses the numerically smallest cutoff. No boundary metric,
framework, target result, or target annotation participates in selection.

OSWorld fits one scalar per training-fold instance, as required by five-fold
evaluation; CodeTrace fits one scalar on the solved reference calibration
population. This is one supervised calibration procedure for the retained
recurrence score, not a grammar, context model, new score, feature family, or
benchmark-specific algorithm branch.

### Current Step 0024 baseline and metrics

For OSWorld, the script reconstructs the current Step 0024 predictor with the
unchanged `predict_fold()` helper and requires its complete full-run boundary
and partition F1 to match the retained Step 0024 summary exactly. For
CodeTrace, the approved plan calls for reuse of the complete Step 0024 output;
the current score-reference and target visible inputs are byte-for-semantic-
content identical to the retained Step 0024 minimal inputs, and the script
loads that run's recurrence metrics as the current baseline.

The primary B-cubed implementation is operation-weighted and uses
session-qualified predicted and oracle groups. The fixed full-run classifier
implements the plan: both populations higher is `supported`, exactly one
higher is `mixed`, and all remaining valid relations are `contradicted`.
Aggregate population losses cannot be hidden. Boundary results remain
diagnostics.

### Completion and static executability

Full mode selects all five OSWorld folds and all 405 CodeTrace targets. The
implementation checks the registered source counts, pair and operation
coverage, manifest stage coverage, unique pair decisions, consecutive
CodeTrace steps, and complete contiguous stage intervals. Assignment creation
emits exactly one session-qualified group assignment per visible operation.
The file parses successfully as Python and its CLI help loads successfully.

## Return

**REVISE. Remaining must-fix findings: 1.**

Repair only the OSWorld oracle-loading order and the corresponding runtime
validity claim, then repeat this focused implementation review. Do not change
the hypothesis, populations, folds, NPMI score, scalar-calibration candidate,
tie rule, Step 0024 baseline, paper, story, RQs, product, or skills. REAL
PREFLIGHT must not run before this finding is closed.

## Focused Follow-Up Review

**Reviewed:** 2026-07-15
**Scope:** only the OSWorld prediction-before-oracle must-fix
**Verdict:** **APPROVE**
**Candidate cutoff fitted:** no
**Candidate metric computed:** no

The must-fix is resolved. `osworld_source()` now returns only the established
eligible sessions and their visible action sequences; no `human_group` value
or labeled row leaves that loader. The eligibility check still reuses the
predeclared `group_alignment=exact`, nonempty-group, at-least-two-operation
population rule, but the candidate path receives only visible actions.

For each fold, `score_osworld_fold()` now separately loads oracle values for
the four calibration folds, fits the cutoff, predicts the held-out fold, and
persists `fold-<f>-predictions.jsonl`. Only after that file exists does it call
`osworld_oracle()` for the held-out session set. That oracle loader filters to
the explicit requested sessions and verifies action/order alignment before
returning group assignments. The target oracle mapping is therefore not
available to association construction, cutoff fitting, current-baseline
prediction, candidate prediction, or prediction persistence.

The changed script still parses successfully. No preflight/full command,
candidate construction, cutoff fitting, or candidate metric was run during
this follow-up.

**APPROVE. Remaining must-fix findings: none.** The implementation may proceed
to REAL PREFLIGHT under the already-approved plan.

## Focused Execution-Repair Audit

**Reviewed:** 2026-07-15
**Scope:** only the isolated Parquet stage-row extraction repair
**Verdict:** **PASS**
**Candidate metric run:** no

The repair changes only how already-selected manifest rows cross the Parquet
reader boundary. `load_stage_map()` now spawns an isolated process, which reads
the existing manifest columns and writes only rows whose `traj_id` belongs to
the supplied selected set. The parent requires a successful child exit,
requires the exported ID set to equal the selected set exactly, rejects
duplicates, checks the expected `solved` value and operation count for every
row, and retains the unchanged contiguous-stage and complete-coverage checks.
A stale or partial child output cannot be accepted after a failed child exit.

Calibration isolation is preserved: the first invocation receives exactly the
same 483 solved calibration IDs and its selected stage rows alone reach the
parent fitting process. Although the short-lived extractor decodes the broad
manifest internally, unselected rows are neither exported nor available to
the cutoff-fitting process. Target isolation is also preserved: candidate
target predictions are constructed and `target-predictions.jsonl` is
persisted before the second isolated extraction is invoked with the selected
failed-target IDs. Exact selected-ID verification prevents calibration rows,
unselected target rows, or other manifest rows from crossing either boundary.

The patch does not change score-reference or target selection, the 483/405
populations, NPMI, cutoff candidates, tie handling, segment construction,
B-cubed or boundary metrics, Step 0024 comparison, or result classification.
It adds no candidate and no algorithm family; it is an execution containment
repair for the same approved calibration experiment.

**PASS. Remaining must-fix findings: none.** The repaired full execution may
resume under the approved plan.
