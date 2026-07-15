# Independent Implementation Review — Step 0029 Experiment 001

**Reviewed:** 2026-07-15T14:26:43-07:00
**Skill used:** `research-experiment-design`
**Review stage:** fresh read-only implementation review after final PLAN REVIEW
**Verdict:** **REVISE**
**Must-fix findings:** **3**
**Candidate metric, REAL PREFLIGHT, or FULL run performed:** **none**

## Scope And Method

I completely reread `research-experiment-design`, its complete required
`references/plan-template.md`, and the relevant `references/technique-catalog.md`.
The technique catalog does not add a technique bundle here: the approved work
is a finite-population method comparison whose authoritative metric and scorer
are already fixed. I then reread, in full:

- `docs/user-instruction.md`;
- this experiment's final `experiment-plan.md` and both rounds in
  `plan-review.md`;
- the current `step-report.md`;
- the uncommitted Rust product implementation, CLI help, and focused tests;
- all three new grammar evaluators; and
- the established OSWorld-Human and CodeTraceBench loaders, folds, scorers,
  controls, and retained Step 0024 summaries that the plan requires the new
  evaluators to reuse.

I inspected the worktree and the three registered Step 0029 raw roots. All
three raw roots are absent, so there is no evidence that an OSWorld or
CodeTrace candidate metric, REAL PREFLIGHT, or FULL run occurred during
implementation. I ran only static and synthetic validation:

- `cargo test --manifest-path agentpprof/Cargo.toml --all-targets`: **53/53
  pass**;
- `cargo clippy --manifest-path agentpprof/Cargo.toml --all-targets -- -D
  warnings`: **pass**;
- Python compilation of all three new evaluators: **pass**;
- `git diff --check`: **pass**; and
- one four-symbol, label-free nested-grammar fixture in memory: **pass**.

I did not run either real operation file, read a new candidate score, execute a
preflight/full command, edit the product/evaluators/plan/paper/skills, touch the
read-only submodule, or perform Git operations. This review file is my only
edit.

## Verdict Summary

The **product algorithm is substantially faithful to the approved one
candidate**. Rust and Python both use hard session boundaries, count exact
left-to-right non-overlapping occurrences, require support in at least two
reference sessions, select by the registered total key, replace one pair per
rule without a cap, and apply every learned rule to targets exactly once in
creation order. Their structured expansion and stable terminal/rule ordering
agree. The product consumes only `session` and `action`, conserves operation
count and additive weight, keeps the existing normal CLI, removes obsolete
NPMI/cutoff report fields, and exports ordered rules and target segments. The
focused fixtures exercise nested rules, pair priority, hidden target-label
mutation, label normalization collisions, no-rule input, external-reference
transfer, deterministic output, and legacy CLI behavior.

The implementation may **not** enter REAL PREFLIGHT yet, however. The OSWorld
evaluator reads the scoring oracle before prediction despite the plan's
explicit temporal-isolation contract; the CodeTrace evaluator does not persist
the independent Python prediction before loading stages; the planned
comparator/diagnostic matrix is incomplete; and the claimed independent
equivalence path leaves several registered report and baseline identities
unchecked. These are not requests for more benchmarks, stronger evidence, or
optional polish. They are localized implementation defects in the already
approved execution and validity path. All can be repaired without changing the
algorithm, RQ, hypothesis, population, metric, promotion rule, paper, or story.

## What Is Correct And Must Be Preserved

### One registered grammar algorithm

`agentpprof/src/profile.rs` implements the registered rule semantics:

- `GrammarSymbol` orders terminals before rules, with terminal text and rule
  creation index providing the stable final identity fallback;
- the `min_by_key` order is descending session support, descending
  non-overlapping occurrence count, ascending left expansion, ascending right
  expansion, then stable left/right symbol identity;
- non-self adjacent pairs cannot overlap, while self-pair counts use
  `floor(run_length / 2)`, exactly matching the replacement scan;
- every accepted rule is applied to every reference session non-overlapping
  left-to-right and reduces the reference symbol count by the recorded number
  of occurrences;
- target spans start as terminals and traverse the ordered rule list once;
- every emitted segment remains contiguous, and assignment count plus additive
  weight are checked before a report is returned; and
- there is no support option, target retry, maximum depth, grammar-size cap,
  motif-length cap, field/window sweep, NPMI cutoff, or second candidate.

The Python implementation in `rq3_grammar_stack_induction_eval.py` independently
matches those mechanics rather than calling Rust to generate its expected
rules. Exact ordered-rule and segment equality is therefore a meaningful
correctness check once the coverage defects below are repaired.

### Product surface and scope

The existing `--induce-operation-stack` and
`--induce-reference-operation-file` interface is retained. CLI help and the
legacy-option error now truthfully describe grammar induction. The product
report includes the approved rule children/expansions/support/occurrences,
reference symbol counts, target segments, assignment coverage, and mass. No
candidate-only experiment-control interface or promotion boolean was added.

No paper, idea-story, user-instruction, skill, KVM, branch, or submodule change
is present in this implementation. This preserves the exact thesis, four RQs,
and authoritative AgentProf story.

## Must-Fix 1 — Implement Real Prediction-Before-Oracle Isolation

The approved plan requires prediction to be persisted before the scorer reads
the target oracle. The current evaluators do not satisfy that contract.

### OSWorld-Human violation

`rq3_grammar_stack_induction_eval.py:396-418` calls `load_operations()` and
`group_sequences(..., "human_group", group_alignment=exact)` in
`source_population()`. It reads every target `human_group`, counts human
groups, and returns label-bearing rows. `evaluate()` calls this function at
line 456, before learning any grammar or running the product at lines 470-485.
It later creates label-bearing pair rows at lines 504-523. The dedicated
`equivalence_only` path is not oracle-free either: it takes the same
label-bearing load path and constructs those pair rows before returning at
lines 555-571.

The minimal rows passed to Rust contain only `session` and `action`, so this is
not evidence that the product actually used a label. It is nevertheless a
direct failure of the approved, auditable execution order: **held-out groups
must load only after persisted predictions**, not merely be omitted from one
function argument.

The evaluator also locally redefines `FOLD_COUNT`, `FOLD_SEED`, and `fold_for`
at lines 34-35 and 95-97. Its current hash happens to match the established
function, but the approved plan explicitly requires reuse of the established
fold assignment. Copying the fold contract creates an unnecessary second
source of truth.

### CodeTrace persistence violation

The CodeTrace path correctly delays `load_stages_after_prediction()` until
after grammar learning and the Rust product call. However, the independent
Python prediction remains only in the in-memory `segments` value. The script
loads stages at lines 224-227 and does not persist `segments.jsonl` until line
245, after scoring. Its comment that both implementations have persisted their
predictions is therefore false under the approved contract.

### Exact required repair

1. Import the established OSWorld fold count, seed, and `fold_for` function;
   remove the local copies.
2. Build the OSWorld candidate input in a label-blind pass that reads only the
   fixed population-selection fields and visible `session`/`turn`/`action`.
   Do not read `human_group` or compute a human-group count in that pass.
3. For every target fold, write the Python segments/operation assignments and
   complete the Rust profile before invoking the established
   `group_alignment=exact`/singleton/scorer path. After the scorer load, assert
   that its eligible session IDs and operation identities exactly equal the
   already-persisted candidate population; any mismatch is invalid rather than
   silently repaired.
4. Keep the standalone equivalence command label-free: it must stop after
   visible population, rules, persisted segments/assignments, and exact
   Rust/Python checks without constructing label-bearing rows.
5. In CodeTrace, persist the Python segments and complete per-operation group
   assignments before calling `load_stages_after_prediction()`. Scoring may
   enrich a separate copy with stages afterward.

This repair must not introduce a new split, eligibility definition, parser
contract, or candidate feature. It only enforces the approved read order and
reuses the existing fold/scorer authorities.

## Must-Fix 2 — Complete And Bind The Approved Comparison Matrix

The current summaries cannot yet prove that every registered baseline,
control, and diagnostic was executed against the intended retained result.

### Missing rows and diagnostics

- OSWorld defines `METHODS` as grammar, action-change, phase-change, and
  always-boundary. The approved `one-session-block` control is absent from
  boundary rows, B-cubed rows, assignments, and the final summary.
- The OSWorld `folds` entries contain only population/grammar counts. The plan
  explicitly registers per-fold boundary and partition metrics as diagnostics;
  none are emitted.
- CodeTrace emits candidate and simple-control metrics per framework, but it
  never merges the retained Step 0024 recurrence row into `per_framework`.
  Thus the full per-framework candidate-versus-main-baseline comparison
  registered by the plan is missing.
- The scripts recompute deterministic controls but do not check them against
  the retained Step 0024 control rows. Recalculation is acceptable as a scorer
  check, but it must either equal the retained row exactly or the retained row
  must be used; it cannot silently become a different comparator result.

### Baseline identity is under-checked

The OSWorld path accepts a purported Step 0024 summary after checking only
`source_counts`. It does not require the registered schema, `mode=full`, five
folds, fold seed, selected session/operation/pair totals, or the Step 0024 NPMI
policy. The CodeTrace path likewise checks only four population counts before
using `current["metrics"]["recurrence"]`; it does not require the registered
schema, `mode=full`, target-pair total, recurrence policy, full-population
validity, or retained raw-result identity. A different historical summary with
the same population can therefore masquerade as the approved main baseline.
The supervised OSWorld comparator is also loaded without source/fold/identity
checks.

### Exact required repair

1. Add `session_one_block` to the complete OSWorld boundary and partition
   matrix and emit it in the full summary.
2. Emit per-fold grammar and comparator boundary/B-cubed diagnostics for all
   five OSWorld folds.
3. Include the retained Step 0024 recurrence metrics in every CodeTrace
   framework row, alongside grammar and the four approved controls.
4. Before using either Step 0024 summary, assert its exact schema, full mode,
   registered algorithm policy, fold/population/assignment totals, validity,
   and expected raw-result identity where available. Apply corresponding
   source/fold checks to the supervised OSWorld summary.
5. Reuse the retained control rows directly or assert exact equality between
   recomputed and retained controls. Keep controls labeled as controls and do
   not create new experiment IDs.

No new baseline is requested. This must-fix only makes the already approved
Step 0024, supervised, phase/action/always/session matrix complete and
unambiguous.

## Must-Fix 3 — Make Independent Equivalence Cover The Registered Report

`verify_product()` currently checks policy, sequence/action fields, one source
field list, operation and symbol totals, ordered rules, segments, and target
mass. Those checks are useful but do not cover the minimum report and exact
coverage contract approved in PLAN REVIEW.

In particular, the verifier does not assert:

- the registered objective, pair-priority description, or replacement order;
- external-reference source identity;
- exact reference-session and target-session counts;
- `selected_evidence_fields` or the absence/exclusion of oracle fields;
- grammar rule count and maximum depth;
- predicted-group, singleton-group, and unique-motif counts; or
- that the report's coverage values agree with complete per-session persisted
  assignments rather than only aggregate operation totals.

The Rust code currently appears to populate these fields correctly, but the
point of the independent path is to make a wrong report or changed product
fail before scoring. Direct code inspection is not a substitute for the
registered full-run verifier.

### Exact required repair

Extend the shared verifier to recompute and assert every item above from the
visible reference/target inputs, Python rules, and persisted segments. Assert
per-session contiguous segment coverage and one assignment for every original
operation before any scorer is called. Make the OSWorld standalone
equivalence summary require all five folds, exactly 287 sessions and 3,978
assignments; make the CodeTrace full path require exactly 2,229 reference
sessions/87,703 reference operations and 405 targets/20,866 assignments/20,461
adjacent decisions. These are fixed completion checks, not a new gate or
promotion condition.

## Non-Blocking Runtime Observation

The implementation contains no hidden rule/depth/length cap, which is correct.
A prior synthetic observation supplied to this review reported 146.10 seconds,
3,540 rules, and about 31 MB for an 87,703-symbol Python grammar build. I did
not repeat that run and do not treat it as a candidate metric. It does not by
itself block REAL PREFLIGHT after the three defects above are repaired: the
registered CodeTrace preflight intentionally builds the complete reference and
will establish whether the real uncapped path terminates.

The literal `O(RN)`/`O(N+R)` statement is not yet independently established,
because both implementations materialize and repeatedly copy fully expanded
action vectors, and the report itself serializes every rule expansion. Do not
promote that asymptotic bound as a verified paper property from the current
implementation. This is a reporting/runtime caveat, not authorization for a
cap, knob, approximation, or second candidate.

## Final Judgment And Return

**REVISE.** The approved grammar candidate itself should be kept. Do not
replace it, tune it, add a grammar variant, change a threshold, add a benchmark,
or alter the fixed thesis/RQ/story. Repair only the three evaluator defects:

1. prediction-before-oracle persistence and established fold/scorer reuse;
2. the complete, identity-bound approved comparison/diagnostic matrix; and
3. full independent report and per-operation coverage verification.

After those repairs, rerun only static/synthetic validation and return this
same implementation for one focused follow-up review. REAL PREFLIGHT remains
prohibited until that follow-up returns **APPROVE**. The supplied runtime
observation does not justify a hidden cap or a preflight before the correctness
path is repaired.

## Focused Follow-Up Review — 2026-07-15T14:40:08-07:00

**Skill used:** `research-experiment-design`
**Scope:** only the three must-fix findings above
**Final verdict:** **APPROVE**
**Remaining must-fix findings:** **none**
**Candidate metric, REAL PREFLIGHT, or FULL run performed:** **none**

I completely reread `research-experiment-design`, its complete
`references/plan-template.md`, and the relevant complete
`references/technique-catalog.md`, then inspected only the repairs to the three
findings above. I did not reopen paper-value admission, request another
baseline or workload, or reconsider the approved grammar family. I reran only
static/synthetic validation: all 53 Rust/CLI tests pass, Clippy with
`-D warnings` passes, all three Python evaluators compile, and
`git diff --check` passes. The three registered Step 0029 real-result roots
remain absent; no candidate metric, REAL PREFLIGHT, or FULL run was used in
this verdict.

### Must-Fix 1 — prediction-before-oracle isolation: resolved

The OSWorld candidate path no longer opens the label-bearing OSWorld source
before prediction. `validate_current_summary()` binds the run to the exact
registered Step 0024 summary path, checks its schema, full mode, original
operation-file identity, source/fold/assignment totals, NPMI policy, required
validity fields, and required retained artifacts, then selects that summary's
`candidate_operations` artifact. `visible_population()` verifies that this
artifact contains no `human_group` or scorer-prefixed group/human/label/oracle
field and has exactly 287 sessions, 3,978 operations, and 3,691 adjacency
positions. The candidate itself receives only action sequences; the Rust
inputs are reduced to unit `session`/`action` rows.

The local fold implementation is gone. `FOLD_COUNT`, `FOLD_SEED`, and
`fold_for` are imported from the established Step 0024 OSWorld evaluator, and
the retained Step 0024 session artifact is checked against that same fold
function.

For each selected fold, the independent Python segments and complete
per-operation assignments are written before the product call; the product
then persists its profile, and ordered-rule/segment equivalence plus mass is
checked. Only after all selected folds have persisted both implementations'
predictions does `scorer_population()` open the original label-bearing source
through the established `group_alignment=exact` and singleton-exclusion path.
The scorer's sessions and ordered visible actions must exactly match the
already-persisted label-free population.

The standalone `equivalence_only` branch returns before
`scorer_population()`, `step24_group_numbers()`, pair-label construction, or
any B-cubed/boundary scoring. It therefore exercises all five visible folds
and exact Rust/Python equivalence without reading target label rows.

The CodeTrace path now persists `python-segments.jsonl` and the complete
`python-assignments.jsonl` after Rust equivalence and before its sole call to
`load_stages_after_prediction()`. The official manifest still cannot affect
grammar learning, target application, or either persisted prediction. No new
split, parser contract, candidate feature, or oracle-derived parameter was
introduced.

### Must-Fix 2 — complete identity-bound comparison matrix: resolved

OSWorld now includes `session_one_block` beside action-change, phase-change,
and always-boundary in both boundary and B-cubed computation. It reconstructs
the main Step 0024 assignments from the exact retained complete session-result
artifact rather than relabeling a modified binary. On FULL, the recomputed
Step 0024 boundary/partition result and every retained simple control must
match the registered summary; the supervised summary is separately checked
for full mode, operation-file/source/evaluated/fold identity, and required
validity before its aggregate row is admitted.

Every OSWorld fold report now contains boundary and partition diagnostics for
grammar, Step 0024, and all four simple controls. The information-richer
supervised comparator remains an aggregate interpretation row, which is
sufficient for this registered implementation-selection decision and does not
weaken the per-fold candidate-versus-main-baseline audit.

The CodeTrace validator binds the comparison to the exact registered Step 0024
summary and verifies schema, full/valid status, reference/target/manifest
paths, complete population and adjacency counts, recurrence policy, required
validity flags, and existence of every retained raw artifact. FULL execution
must reproduce all four deterministic control rows exactly, both globally and
within every framework. It then inserts the retained Step 0024 recurrence row
globally and for each framework, so the candidate-versus-main-baseline
comparison and all planned controls are present without creating a new
baseline run or experiment ID.

### Must-Fix 3 — independent report and assignment coverage: resolved

The shared `verify_product()` now checks the registered policy, objective,
pair priority, replacement order, external-reference source, sequence/action
fields, selected source/evidence fields, oracle field/prefix exclusions,
reference/target disjointness and session/operation counts, before/after symbol
counts, the entire ordered rule list, the entire segment list, rule count,
maximum depth, predicted/singleton/unique-motif counts, and assigned operation
and weight conservation.

It also reconstructs each target session's segment cursor and covered
positions, rejecting an unexpected session, gap, overlap, duplicate, missing
position, or wrong terminal cursor. The separately persisted assignment rows
must have one unique `(session, position)` key per target operation. Standalone
OSWorld equivalence additionally requires all five folds, all 287 sessions,
and all 3,978 assignments. CodeTrace FULL requires the fixed 2,229-session /
87,703-operation reference and all 405 targets / 20,866 assignments / 20,461
adjacency positions before interpretation.

The product still has no NPMI/cutoff/calibration report fields or promotion
boolean. The two remaining report details not independently enumerated by the
shared helper—`derived_stack_field` and the complete suffix list—are fixed and
covered by the focused Rust/CLI report tests; neither can affect the candidate
input, grammar, grouping, primary metric, or promotion relation. They are not
a scientific or executability blocker under the experiment skill's review
standard.

### Scope-preservation audit

The grammar mechanics reviewed in round one are unchanged: support remains
exactly two-or-more sessions, the total pair key and non-overlapping scan are
unchanged, every target rule still applies exactly once in creation order, and
there is still no cap, sweep, per-benchmark rule, target retry, or second
candidate. The repairs add only scorer ordering, artifact checks, required
comparison rows, and validity assertions. They do not modify the exact RQ3,
the thesis, the four-RQ organization, the AgentProf story, the paper, skills,
KVM material, or the read-only submodule.

## Follow-Up Final Judgment

**APPROVE.** All three implementation must-fix findings are resolved with zero
remaining blockers. The implementation may proceed to the registered REAL
PREFLIGHT. Approval authorizes only execution of the already approved
OSWorld fold-zero and first CodeTrace target paths; it does not authorize an
algorithm repair based on their metrics, a hidden cap, a second grammar
variant, a new benchmark, or any RQ/story/paper change. Preflight metrics remain
execution-only and uninterpreted, and the skill's two-attempt limit remains in
force.
