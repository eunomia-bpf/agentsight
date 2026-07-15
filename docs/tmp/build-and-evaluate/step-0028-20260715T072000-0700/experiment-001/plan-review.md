# Independent Experiment-Plan Review

**Skill used:** `research-experiment-design`
**Review round:** 2 of 2 (single allowed follow-up)
**Verdict:** **APPROVE**
**Candidate metrics run:** none

## Follow-Up Verdict

The revised plan repairs both round-one blockers without broadening the
experiment. The current plan consistently registers the real CodeTrace
calibration population as **483 sessions / 18,152 operations / 2,886 stages**,
while retaining the correct 2,229-session / 87,703-operation score reference,
405-session / 20,866-operation target, and 112 unavailable non-target
exclusions.

The execution path is now a user-meaningful supervised mode of the existing
constructor. `--induce-calibration-operation-file PATH` consumes ordinary
`session`, `action`, and `group` operation fields; `agentpprof` internally fits
the one registered reference B-cubed cutoff against the unchanged NPMI score
reference and applies it to the target. There is no raw numeric cutoff
injection. Omitting the option is required to reproduce Step 0024 decisions
and output compatibility.

The plan now supplies exact product, OSWorld preflight/full, and CodeTraceBench
preflight/full commands and raw roots. It also makes the isolation order
executable: target IDs are removed before score/calibration fitting, only
reference stages enter fitting, target predictions are persisted first, and
target stages load only afterward for scoring. These repairs satisfy PLAN
REVIEW; implementation review remains responsible for confirming that the new
code realizes them.

**Remaining must-fix findings:** none.

## Scope And Inputs

This is a fresh, read-only scientific and executability review of the proposed
RQ3 reference-calibrated recurrence experiment. I read the complete experiment
skill and its plan template, the current paper's exact thesis and RQ3 text,
Step 0024's approved plan and complete/result-review reports, Step 0026's
no-admit audit, Step 0027's final outer audit, the current recurrence design and
Rust/CLI path, and the actual OSWorld-Human and CodeTraceBench artifacts. I did
not run a candidate metric or edit the plan, code, paper, canonical documents,
skills, branch, or read-only submodule.

## Paper-Value Admission

Admission is scientifically sound; the two round-one defects recorded below
are resolved by the current plan.
This is genuinely one supervised calibration mode of the existing Step 0024
algorithm, not a new constructor or benchmark, provided the implementation
keeps all of the following exact:

```text
Step 0024 action-transition NPMI table
-> one reference-label-fitted scalar cutoff
-> Step 0024 boundary comparison, unseen-pair rule, segments, motifs,
   operation stacks, and additive folding
```

Step 0026 rejected choosing another action-only cutoff, window, sign, margin,
or population gate from already-observed target outcomes. It did not establish
that a cutoff trained on independently annotated reference sessions is
scientifically invalid. The proposed experiment asks a different and useful
question: whether the existing recurrence score is calibratable under a
declared supervised information regime. Positive and contradictory outcomes
produce different paper decisions, and reusing the two complete populations is
the best immediate response to the user's instruction to improve the existing
algorithm on already-run trajectories.

The planned role is correctly limited to **supporting group-boundary evidence
inside RQ3**. It cannot close phase, action, literal tag-name, cross-family, or
whole-RQ accuracy, and it does not alter the fixed thesis, story, or four RQs.

## Scientific Protocol Judgment

### Reference-only B-cubed fitting is fair

Maximizing operation-weighted B-cubed F1 over the training/reference
partitions is scientifically fair for a supervised calibration mode. It is the
declared training objective, uses one scalar, enumerates all induced decision
partitions deterministically, and applies the selected cutoff once to withheld
targets. Using the same metric for supervised training and held-out evaluation
is not circular: circularity would arise only if target partitions or target
metrics selected the cutoff. The midpoint enumeration, strict `score < cutoff`
decision, unseen-pair rule, and smallest-cutoff tie rule are sufficiently
specific and deterministic.

OSWorld's five session folds give a valid within-corpus out-of-fold protocol,
although the corpus remains previously observed development evidence.
CodeTraceBench's solved-reference to failed-target shift is also a fair and
informative transfer test; failure under that shift would contradict this
calibration hypothesis rather than invalidate the run. The 405 targets remain
reused development evidence, so the plan correctly forbids calling the outcome
untouched or independent confirmation.

### Baselines and result rules are adequate

Step 0024 is the correct main baseline because it represents the strongest
zero-annotation version of the same recurrence score. Reusing the complete
existing OSWorld supervised Bernoulli result and CodeTrace phase-change result
is preferable to rerunning them. The plan correctly prevents a win over Step
0024 from becoming a claim of best supervised method when either stronger
comparator wins.

The fixed supported/mixed/contradicted rules are strict but valid and do not
hide a population regression behind an average. Deterministic execution needs
no repeated seeds. The declared complete OSWorld target totals (287 sessions,
3,978 operations, 3,691 decisions, and 2,042 groups) and CodeTrace target totals
(405 sessions, 20,866 operations, 20,461 decisions, and 2,948 stages) agree
with the retained complete artifacts.

## Round-One Must-Fix Findings (Resolved)

### 1. Resolved: CodeTrace calibration operation/stage counts

Round one found that the original plan's `483` calibration-session count was
correct, but its `39,018 operations / 5,834 stages` was not produced by the
named current artifacts.
Independent reconstruction from
`.agentsight/experiments/codetracebench-rq2/manifests/verified.parquet` and
`docs/visexp/out/codetracebench-rq2/full/reference-operations.jsonl` gives:

| Population | Sessions | Operations | Official stages |
|---|---:|---:|---:|
| verified manifest | 1,000 | 46,539 | 6,739 |
| raw normalized reference file | 2,634 | 108,569 | n/a |
| target-disjoint score reference | 2,229 | 87,703 | n/a |
| solved manifest IDs present in that target-disjoint reference | **483** | **18,152** | **2,886** |
| fixed failed target | 405 | 20,866 | 2,948 |

For all 483 calibration sessions, the normalized operation count exactly
matches manifest `step_count`. The manifest has 112 non-target IDs absent from
the normalized reference artifact, so that exclusion count is correct. The
The current plan now uses `18,152 / 2,886` consistently and does not synthesize
or double normalized step rows.

This first-round blocker is resolved.

### 2. Resolved: executable, legitimate Rust product path

Round one found that the current `agentpprof 0.2.37` CLI has
`--induce-operation-stack` and a label-free
`--induce-reference-operation-file`; it has no supplied-cutoff or
reference-annotation calibration option. The plan leaves all authoritative
commands until after implementation review and says only that it will expose
an optional scalar cutoff. That is insufficient for PLAN REVIEW, which must
establish the real preflight and full workflow before implementation and
execution.

A raw numeric flag populated only by the experiment evaluator would be a
project-authored experiment-control seam, not by itself a usable supervised
constructor. The revision needed to define one minimal user-meaningful product
path and its exact planned CLI spelling. For example, the normal induction
path may consume reference operations whose existing generic fields include a
declared group/stage field, fit the one scalar internally, and then apply it to
the target operations. An alternative persisted scalar/model input is
acceptable only if the plan also specifies the ordinary reference-only fitting
workflow that produces it; target metrics cannot be the workflow. In either
case, omitting the supervised input must reproduce Step 0024 decisions exactly.

The revised plan now includes exact preflight and full commands for both
OSWorld and CodeTraceBench, including the input paths, the supervised-mode
activation, output roots, target-ID exclusion path, and scorer invocation. It
must make the temporal isolation executable rather than aspirational:

1. obtain the 405 target IDs without reading their stages;
2. remove those IDs before NPMI construction and calibration selection;
3. select the 483 calibration IDs using only manifest identity and `solved`;
4. read only the 483 reference stages to fit the cutoff;
5. write all target predictions; and
6. only then read the 405 target stages for scoring.

The registered calibration-operation input and exact commands resolve this
blocker; implementation review must verify that the code realizes the approved
path.

## Non-Blocking Observations

- No additional benchmark, feature family, context window, cutoff variant,
  per-framework exception, or extra baseline is needed.
- The richer OSWorld supervised comparator and CodeTrace phase-change
  comparator need not determine the tested-hypothesis verdict; their role is
  to bound interpretation.
- The solved-to-failed shift and prior observation of the target corpus are
  limitations to report, not reasons to block a complete run.
- The exact thesis, four RQs, original story, and read-only submodule are
  preserved by the proposal.

## Return

**APPROVE.** The same experiment may proceed to implementation and independent
implementation review exactly as revised. This approval does not authorize a
second cutoff, target-informed retry, extra feature, new benchmark, paper
claim, or candidate metric before REAL PREFLIGHT. No optional breadth or prose
repair is required.
