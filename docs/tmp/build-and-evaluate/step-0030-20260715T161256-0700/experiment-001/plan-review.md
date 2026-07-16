# Independent Experiment-Plan Review

**Reviewed:** 2026-07-15
**Skill used:** `research-experiment-design`
**Review round:** 1 of at most 2
**Verdict:** **APPROVE**
**Candidate metrics run:** none

## Scope And Independence

I completely read the current `research-experiment-design` skill and its
required plan template, the complete Step 0030 plan, the complete Step 0028
plan/review/preflight-failure record, the paper's fixed RQ3 hypothesis and
evaluation, the current RQ3 frontier in `docs/evaluation.md`, and Step 0029's
final result review and outer audit. I also checked, without scoring a
candidate, that the named OSWorld-Human and CodeTraceBench source artifacts
and retained Step 0024 summaries exist and that the current reusable loaders,
fold rule, NPMI implementation, and partition scorers expose the paths the
planned one-script evaluation needs.

I did not run a candidate, fit a cutoff, inspect a candidate outcome, edit the
plan, product, evaluator scripts, paper, skills, canonical documents, Git, or
the read-only paper submodule. This review is my only write.

## Paper-Value Admission

Admission is valid under the later user instruction to improve the existing
algorithm directly on already-run trajectories. The experiment tests one
unresolved mechanism-level hypothesis within the unchanged RQ3, reuses two
complete real annotated populations, and produces different paper decisions
for a consistent improvement, a one-population tradeoff, and a complete
failure. It is stronger than another grammar variant or another RQ2 reader
variant because Step 0029 has closed the grammar candidate, RQ2 already has a
bounded positive paper answer, and this run can distinguish a bad unsupervised
cutoff from an insufficient recurrence score without collecting another
benchmark.

The role is correctly **supporting algorithm evidence**, not a whole-RQ3
answer. Even a supported result would establish only an optional supervised
reference-calibrated recurrence mode on reused development populations. It
would not establish literal tag names, all phase/action identity, untouched
cross-family confirmation, or the paper's central thesis by itself.

## Step 0028 Closure

Step 0028 does not scientifically bar this user-requested outer step. Its two
preflight attempts both stopped in a self-authored OSWorld eligibility adapter
before NPMI construction, cutoff fitting, product invocation, prediction,
oracle loading, or metric computation. It therefore supplied no evidence for
or against the calibration hypothesis and created no target-outcome feedback
that could bias this candidate.

The Step 0028 record nevertheless remains closed and must not be rewritten as
a successful or negative run. This approval treats Step 0030 as a later,
explicitly user-directed outer-loop selection of the still-unanswered
scientific question, with its own minimal analysis-only execution path. It is
not authorization for a third Step 0028 preflight, a renamed repair tag, or a
restoration of Step 0028's product CLI, three-evaluator, and equivalence
program. The current plan respects that distinction by requiring one ordinary
analysis script and deferring any product port until after a complete supported
scientific result.

## Algorithm Identity And Minimality

The candidate is sufficiently specific and executable:

1. the visible action-transition table and NPMI score remain fixed;
2. unseen transitions remain boundaries;
3. one scalar is selected by reference-only operation-weighted B-cubed F1;
4. midpoint candidates and the exact tie rule are fixed before execution;
5. the scalar is applied once to label-withheld targets; and
6. segment construction and motif naming remain unchanged.

This is calibration of the retained recurrence family, not another grammar,
context model, score, feature set, benchmark-specific branch, or target-tuned
retry. A one-script full-population analysis is the right scientific sequence:
first determine whether the candidate works on the existing trajectories,
then consider a product port only if the result supports it. Requiring a Rust
port or Python/Rust equivalence before learning that relation would repeat the
Step 0028 implementation burden without adding validity to the algorithm test.

The current Step 0024 baseline internally uses a global cutoff and the
monotone `min(global, cross-action)` applied cutoff, while this candidate
deliberately fits one supervised scalar for all observed transitions. The
plan defines that difference unambiguously. Consequently, a later result may
call the candidate a **reference-calibrated recurrence variant**, but not
decision-for-decision the unchanged Step 0024 calibration rule. This wording
boundary is nonblocking because the proposed decisions themselves are fixed.

## Leakage And Isolation

The isolation protocol is scientifically adequate.

- **OSWorld-Human:** for every target fold, the other four folds alone build
  the NPMI table and supply calibration groups. The target-fold group labels
  load only after its predictions are persisted. All five folds run, so every
  one of the 287 eligible sessions is scored exactly once.
- **CodeTraceBench:** all 405 failed target IDs are removed before score-table
  construction and calibration. The 483 solved verified reference sessions
  alone supply the 18,152 calibration operations and 2,886 official stages.
  The 405 target stages load only after target predictions are persisted.
- Using B-cubed for both reference fitting and held-out evaluation is ordinary
  supervised calibration, not metric circularity. It would become circular
  only if a target partition or target result selected the scalar, which the
  plan explicitly prohibits.
- Prior observation of these development populations limits interpretation
  but does not invalidate the execution. The plan does not claim untouched
  confirmation, and the solved-reference to failed-target shift remains part
  of the test rather than a basis for a target-specific repair.

The complete source artifacts needed for this protocol are present: the
established OSWorld-Human operation file, CodeTrace reference and target
operation files, the verified parquet manifest, and both retained Step 0024
complete summaries. The established OSWorld helper already implements the
required `group_alignment=exact` filter followed by exclusion of sessions with
fewer than two eligible operations, so Step 0030 need not recreate the faulty
Step 0028 eligibility adapter.

## Baselines, Metrics, And Interpretation

Step 0024 is the correct single main baseline: it is the current strongest
same-score, zero-annotation constructor on the exact same target inputs, and a
matched comparison is necessary to decide whether reference labels improve
calibration. The information advantage is explicit, so a candidate win can
support an optional supervised mode but cannot be presented as equal-budget
superiority over label-free induction.

The existing OSWorld supervised predictor and CodeTrace phase-change
partition are correctly retained as interpretation comparators rather than
rerun or promoted to additional main baselines. They prevent a narrow win over
Step 0024 from becoming a best-supervised-method claim.

Operation-weighted B-cubed F1 is claim-matched because the question is target
partition fidelity. Reporting each complete population separately and
requiring strict improvement on both prevents an average from hiding a
regression. Boundary metrics, per-fold/per-framework rows, unseen transitions,
candidate/tie counts, coverage, and mass conservation are correctly
diagnostic. Deterministic fitting over complete fixed populations requires one
full run rather than arbitrary repeated seeds.

## Execution And Completion

The planned preflight and full commands are concrete and use one output root.
The preflight contains a real target path, real reference/calibration data, the
actual fitting objective, prediction persistence, and the actual scorer; it is
not a fixture or schema check. Its result cannot revise the candidate.

Full completion is also objective: all five OSWorld folds and all 405
CodeTrace targets must terminate, with 3,978 and 20,866 unique operation
assignments respectively, complete adjacent-pair coverage, unchanged source
populations, prediction-before-oracle ordering, and one conserved assignment
per operation. The full run cannot stop after a favorable prefix or one
population.

Implementation should bind the new script's defaults to the established
source paths and assert the registered population counts before fitting. That
is an ordinary implementation check against the approved plan, not another
plan round, product interface, or control contract.

## Return

**APPROVE. Remaining must-fix findings: none.**

The plan may proceed to minimal implementation and REAL PREFLIGHT exactly as
written. This approval does not authorize target-informed cutoff changes,
another candidate after seeing results, a new benchmark, a product port before
the complete scientific result, paper/story/RQ edits, or reinterpretation of
Step 0028/0029. Optional prose or packaging changes are nonblocking.
