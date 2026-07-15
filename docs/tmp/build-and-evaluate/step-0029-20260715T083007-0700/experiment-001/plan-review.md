# Independent Experiment-Plan Review

**Reviewed:** 2026-07-15T08:38:12-07:00
**Skill used:** `research-experiment-design`
**Review round:** 1 of at most 2
**Verdict:** **REVISE**
**Candidate metrics, preflight, full execution, or implementation:** none

## Scope And Independence

I first reread the complete `research-experiment-design` skill and its complete
required `references/plan-template.md`. I then performed a read-only review of
the Step 0029 experiment plan against:

- the verbatim `docs/user-instruction.md`;
- the fixed thesis, four RQs, scientific model, and story invariants in
  `docs/idea-story.md` and the current paper;
- the Step 0024--0028 evidence and closure boundaries in
  `docs/evaluation.md`;
- Step 0024's approved plan and retained complete raw summaries;
- the current `agentpprof` CLI and Rust operation-stack induction interface;
- the current OSWorld-Human and CodeTraceBench loaders, scorers, and
  recurrence/equivalence evaluators; and
- the existence and registered sizes of the real operation files, verified
  manifest, and Step 0024 result roots.

I also checked the primary algorithmic precedent. Standard Re-Pair is the
most-frequent-pair offline grammar compressor introduced by
[Larsson and Moffat](https://doi.org/10.1109/5.892708). SEQUITUR is a different,
incremental algorithm governed by digram uniqueness and rule utility in
[Nevill-Manning and Witten](https://doi.org/10.1613/jair.374).

I did not edit the experiment plan, code, paper, canonical documents, skills,
branch, or read-only submodule. I did not run a candidate, metric, evaluator,
preflight, full execution, fixture, or implementation test. This review file is
the only output.

## Verdict Summary

The **scientific direction is conditionally admissible and materially distinct
from the closed branches**. Re-Pair-style recursive substitution constructs
variable-length grammar symbols and removes the Step 0024 NPMI/two-means
decision path entirely. It is not another cutoff, sign, margin, fixed window,
support bucket, or Step 0028 supervised calibration. Step 0026 explicitly
closed flat action-pair and small-window tuning while leaving a genuinely
different sequence model open. The user also directly requested improving the
algorithm on already-run trajectories rather than creating a new benchmark.

The proposed experiment has different paper decisions under positive and
negative outcomes, uses two real complete public-data populations, preserves
the fixed RQ and story, and keeps Step 0024 as the strongest fair same-input
baseline. Its role is correctly limited to supporting automatic group-boundary
construction inside RQ3.

The plan is not executable or uniquely reproducible yet, however. It currently
conflates standard Re-Pair, SEQUITUR, and a new multi-session transfer
adaptation; leaves a non-total rule tie/application contract; supplies no
runnable product/evaluator commands even though every current evaluator is
NPMI-specific; and overstates target-label independence after the same labels
motivated selection of the grammar family. These are scientific-scope and
executability defects that must be repaired before REAL PREFLIGHT.

**Must-fix findings: 3.**

## Paper-Value Admission

### What passes

The plan names verbatim **RQ3: How accurate are the tags?** and tests one
specific supporting hypothesis: whether variable-length action recurrence
recovers official operation partitions more faithfully than the current
pairwise recurrence constructor. It does not change the exact thesis, four RQs,
two core abstractions, original AgentProf story, or contribution surface.

Success changes the product decision: adopt one different automatic
constructor if it Pareto-improves the two complete populations. Failure changes
the product decision in the other direction: restore Step 0024 and close this
candidate. The result is therefore not tautological, a positive control, or a
dependency-only run.

The work also answers the user's immediate request more directly than a new
phase/literal-name benchmark or RQ2 intervention. Those alternatives cover more
of the final paper, as the plan honestly states, but they do not improve the
existing algorithm on the already-run trajectories. Under the current explicit
instruction, that makes this a reasonable next supporting experiment rather
than activity for its own sake.

### Scientific boundary that must remain

Even a positive result is post-hoc implementation-selection evidence on two
reused development populations. It cannot become independent cross-family
confirmation, literal tag-name accuracy, a complete RQ3 answer, a new paper
thesis, or a new core abstraction. The plan mostly preserves this boundary;
must-fix 3 below removes its remaining contradictory independence language.

## Distinction From Closed Branches

The proposal is **not** a disguised third Step 0028 attempt. Step 0028 kept the
Step 0024 NPMI score and tried to fit one scalar cutoff from grouped reference
annotations. This proposal uses no group annotations and discards NPMI and the
cutoff entirely. Fixing the Step 0028 singleton adapter is neither necessary
nor part of this plan; importing the established eligibility loader is the
correct response.

It is also different from Steps 0025--0026. Those branches chose a boundary
from an action pair plus local score/window properties. Here, recursive
replacement changes the representation into variable-length nonterminals
learned across the whole reference corpus before target segmentation. That is a
different mechanism family, even though both consume only `session` and
`action`.

This distinction holds only if the final algorithm is fixed exactly before
execution. A second grammar variant, occurrence-versus-session-support sweep,
rule-application alternative, maximum depth, motif-length cap, or target-driven
retry would collapse the plan back into prohibited selection. The revised plan
should explicitly keep one choice at each of these points.

## Must-Fix Findings

### 1. State the actual algorithm and make its ordering total

The current plan calls the method “the closely related batch Re-Pair
construction,” but the registered procedure is not standard Re-Pair:

- standard Re-Pair chooses the most frequent adjacent pair by occurrence in a
  single input text and stops when no pair repeats;
- the plan chooses first by the number of distinct sessions containing a pair,
  using total non-overlapping occurrences only as a tie-breaker;
- the plan treats session boundaries as hard multi-string boundaries; and
- standard Re-Pair compresses the same text from which it learns, whereas this
  plan transfers a learned dictionary to separate target sessions.

All three adaptations may be scientifically sensible: distinct-session support
is a simple way to encode the paper's cross-run recurrence principle, hard
session boundaries avoid artificial transitions, and dictionary transfer is
what target-label-withheld evaluation requires. But they are load-bearing
method choices, not details inherited from the cited algorithm. SEQUITUR does
not supply them either; it uses different incremental constraints.

Revise the precedent and method sections to do all of the following without
adding another candidate or branded name:

1. cite the original Re-Pair paper directly and identify the registered method
   as one **multi-session, reference-to-target adaptation** of Re-Pair;
2. state that session support, hard session boundaries, and dictionary transfer
   are deliberate deviations needed for cross-run operation induction;
3. define the non-overlapping occurrence count with the exact left-to-right
   scan used for replacement;
4. make the tie key total in both Rust and Python. “Lexicographically by the
   pair's fully expanded action sequences” is ambiguous when different
   `(left expansion, right expansion)` pairs concatenate to the same action
   sequence. Compare the structured pair of expansions and add one stable final
   symbol/rule-ID fallback if necessary;
5. state whether each learned rule is applied to a target exactly once in
   creation order or repeatedly to a fixed point. The current prose suggests
   exactly once, but the equivalence contract must not infer this; and
6. state the termination argument and implementation complexity expected for
   the registered 87,703-operation reference, without introducing a hidden
   grammar-size/depth cutoff.

The revised plan may instead choose literal standard occurrence-frequency
Re-Pair, but it must choose one algorithm now. It must not plan both, compare
their target outcomes, or reserve the choice for implementation/preflight.

### 2. Register an executable product and evaluator path

The plan has no runnable command. This blocks PLAN REVIEW under the experiment
skill. The current product interface can plausibly remain simple:

```text
agentpprof --operation-file TARGET.jsonl
           --induce-operation-stack
           --induce-reference-operation-file REFERENCE.jsonl
           --view operations --format json
           --deterministic-output --output PROFILE.json
```

But the current implementation and all three existing RQ3 evaluators are
specifically NPMI/two-means implementations:

- CLI help says the inducer learns adjacent-action NPMI and deterministic
  two-means;
- the Rust report exposes NPMI scores, global/cross-action cutoffs, calibration
  populations, and boundary decisions; and
- the OSWorld, CodeTrace, and Rust/Python evaluators assert those exact policy
  names and report fields.

Therefore “replace only `profile.rs` internals” is not a complete product or
evaluation plan. The revision must:

1. give exact planned OSWorld preflight/full, CodeTrace preflight/full, and
   Rust/Python equivalence commands, including actual input and raw-output
   paths;
2. name the evaluator files that will be adapted or added and state that they
   import the established OSWorld `group_alignment=exact`/singleton behavior
   and CodeTrace visible/stage loaders rather than reimplementing them;
3. permit the minimum truthful CLI help/status update in `main.rs` if the
   normal `--induce-operation-stack` algorithm changes; no new candidate-only
   product flag is needed;
4. register the minimum grammar report needed for independent equivalence:
   selected policy/objective, reference and target coverage, ordered rules and
   their deterministic support/tie facts, target segments/assignments, and mass
   conservation. Do not retain meaningless NPMI/cutoff fields and do not create
   a promotion schema;
5. identify the exact retained Step 0024 raw summaries/decisions used as the
   main baseline and the existing comparator summaries. The modified binary
   must not silently relabel a fresh grammar run as the Step 0024 baseline; and
6. repeat the terminal totals in the command-level completion rule: five
   OSWorld folds / 287 sessions / 3,978 assignments and all 405 CodeTrace
   targets / 20,866 assignments, plus complete per-target group equivalence.

These additions are ordinary reproducibility, not a frozen protocol or extra
gate. They are necessary because the currently named interface does not yet
execute or verify the proposed algorithm.

### 3. Correct the adaptive-evidence and label-isolation wording

The construction is label-free **at fit and application time**, but the
algorithm-family decision is not target-label-naive. Step 0026 used the already
observed OSWorld and CodeTrace labels to show that visible pair identities and
small contexts are ambiguous; that diagnosis directly motivates moving to a
grammar model. Both populations have also been inspected through Steps
0020--0026. Thus the sentence “No target label chooses a rule or parameter” is
too broad.

Revise the fairness language to distinguish two facts:

- **execution isolation:** for every OSWorld fold, only reference actions train
  the grammar and the held-out fold's groups load after predictions; for
  CodeTrace, all 405 target IDs are excluded from the 2,229-session reference
  and target stages load only after persisted predictions; and
- **adaptive evidence scope:** the grammar family and this evaluation were
  selected after project agents had observed both populations' labels and
  earlier outcomes. Consequently both complete results are post-hoc
  mechanism-development evidence even though no target label enters the
  candidate code path.

This repair needs no new split, benchmark, or control. It prevents a valid run
from being promoted under an independence claim the provenance cannot support.

## Baselines And Comparison Fairness

Step 0024 is the correct main baseline. It is the current best same-product,
same-`session`/`action`, same-reference/target constructor and directly
represents the competing pairwise answer. The source-provided CodeTrace phase
partition and the richer supervised OSWorld predictor are appropriately
retained as information-richer comparators that bound “best” wording rather
than as fair same-input main baselines.

No additional main baseline is required for approval. In particular, do not
add a baseline collection merely because grammar compression has many
variants. If the paper later claims that **session support itself** is the
reason for improvement, then standard occurrence-frequency Re-Pair would be a
necessary component comparison. The simpler choice for this experiment is not
to make that causal claim: test only the one registered grammar constructor
against current Step 0024 and describe the session-support adaptation honestly.

Existing always-boundary, action-change, phase-change, one-session-block, and
supervised rows should be reused, not treated as new experiments or rerun IDs.
The revised executable section must make that reuse explicit.

## Workloads, Metrics, Matrix, And Promotion Rule

The planned full matrix is scientifically adequate:

- all 287 OSWorld-Human sessions appear as held-out targets once across five
  folds;
- the CodeTrace grammar learns from the exact target-disjoint 2,229-session /
  87,703-operation reference and applies once to all 405 target sessions;
- operation-weighted B-cubed F1 is claim-matched to group-partition fidelity;
- boundary metrics, grammar size, compression, and depth remain diagnostics;
- the two populations are interpreted separately, so an aggregate cannot hide
  a regression; and
- exact Rust/Python grouping equivalence, coverage, and mass conservation are
  validity checks rather than scientific promotion criteria.

One deterministic execution is sufficient for the algorithm itself. Session-
level paired deltas or a bootstrap interval would improve paper interpretation
across tasks, but this is optional for post-hoc finite-population implementation
selection and is not an approval blocker.

The exact Pareto rule—no lower B-cubed on either population and strictly higher
on at least one—is clear and consistent with Step 0024. The additional
requirement that the candidate remain above the strongest simple OSWorld
control is mathematically redundant if it is already no lower than Step 0024,
which is above that control. Removing the extra clause would simplify the
verdict without weakening it; this is optional because it cannot change any
outcome under the registered baseline values.

REAL PREFLIGHT correctly uses the real binary, reference construction,
prediction persistence, scorer, and equivalence path, and the full run covers
the entire matrix. Preflight metrics must remain uninterpreted and cannot
change the grammar. The skill's two-attempt limit still applies even though the
plan need not restate it.

## Optional Improvements

- Use one consistent plain term such as “grammar-based operation-stack
  induction” in the paper. “Multi-step grammar recurrence,” “Re-Pair,” and
  “grammar recurrence” need not become three terms for the same supporting
  mechanism.
- State an expected CPU/memory bound after fixing the algorithm contract. Do
  not introduce a maximum-rule or maximum-depth knob merely to control cost.
- Remove the redundant simple-control condition from the promotion rule and
  keep the stronger supervised/phase comparators as interpretation rows.
- Report per-session/per-framework paired deltas or uncertainty as diagnostics
  if readily available, without creating another success condition.

## Required Revision And Return

**REVISE.** The proposal is worth keeping and remains one experiment inside
fixed RQ3, but it may not enter implementation or REAL PREFLIGHT yet. Revise
the same plan once to:

1. identify and fully specify the one multi-session Re-Pair adaptation,
   including a total deterministic tie/application contract and correct primary
   citation;
2. register exact product/evaluator commands and the minimum truthful report/
   interface changes against existing loaders and Step 0024 raw baselines; and
3. correct the distinction between execution-time label isolation and
   post-hoc algorithm-family selection on previously observed populations.

The single permitted follow-up should review only those repairs. No candidate
metric, implementation, preflight, extra grammar variant, new benchmark, or
paper/story/RQ change is authorized by this verdict.

## Follow-Up Review — 2026-07-15T08:45:10-07:00

**Skill used:** `research-experiment-design`
**Review round:** 2 of 2; single permitted follow-up
**Final verdict:** **APPROVE**
**Remaining must-fix findings:** none
**Implementation, candidate metric, preflight, or full run:** none

This follow-up reviewed only the three repairs required above. I reread the
same revised `experiment-plan.md` and compared its registered commands and
paths with the already-inspected current product/evaluator interfaces and real
assets. I did not reopen admission, request a new baseline, broaden the matrix,
or convert an optional observation into a blocker.

### Repair 1 — Algorithm identity and deterministic contract: resolved

The plan now cites Larsson and Moffat's original Re-Pair paper directly and
accurately calls the candidate one **multi-session, reference-to-target
adaptation**, not standard Re-Pair or SEQUITUR. It explicitly identifies all
three load-bearing deviations:

- distinct-session support replaces single-text occurrence frequency;
- session boundaries are hard rather than concatenated into artificial
  transitions; and
- one ordered dictionary learned from reference sessions transfers unchanged
  to held-out target sessions.

The candidate remains one algorithm rather than a sweep. Pair eligibility is
fixed at occurrence in at least two distinct sessions, which is the minimum
definition of cross-run recurrence rather than a numeric support option. The
non-overlapping count and replacement both use the same position-zero,
left-to-right scan. The selection key is now total: descending session support,
descending non-overlapping occurrences, structured left/right expanded action
sequences, and stable terminal/rule identity with monotonic creation indices.

Target application is also unambiguous: each rule is applied exactly once in
creation order, never iterated to a fixed point. Remaining symbols define the
contiguous predicted groups and expand to the ordinary operation label. Every
operation is assigned once and keeps its original weight.

The plan supplies a valid termination argument—each accepted rule removes at
least one pair in two sessions—and registers uncapped direct complexity as
`O(RN)` time and `O(N+R)` space with `R <= N/2`, including the resulting
`O(N^2)` worst case. It adds no depth, grammar-size, motif-length, window,
support, or benchmark-specific knob. The 87,703-operation reference must
finish under that exact contract rather than under a hidden cap.

This fully resolves the first must-fix. Implementation review can now compare
Rust and Python against one predeclared rule order without choosing among
grammar variants.

### Repair 2 — Executable product/evaluator path: resolved

The plan retains the existing normal product interface and gives its exact
command. No candidate-only cutoff, grammar, promotion, or experiment-control
flag is introduced. It correctly expands implementation scope beyond
`profile.rs` to the minimum truthful NPMI-to-grammar help/status changes in
`main.rs` and focused existing tests.

All required execution paths are now named with complete commands and real
paths:

- OSWorld preflight and full through
  `script/rq3_grammar_stack_induction_eval.py`;
- Rust/Python full-fold equivalence through
  `script/rq3_grammar_stack_rust_equivalence.py`; and
- CodeTrace preflight and full through
  `script/rq3_grammar_codetracebench_stage_fidelity_eval.py`.

The scripts are required to import the established OSWorld eligibility,
singleton, fold, scorer, and control paths and the established CodeTrace
visible-operation and post-prediction stage loaders. This directly addresses
the Step 0028 adapter failure without repairing or rerunning Step 0028 and
without adding a new population parser.

The minimum product report is scientifically sufficient for independent
equivalence: it records the policy/objective, selected fields, reference/target
coverage, the ordered rule definitions and their support/tie evidence,
before/after symbol counts, grammar depth/count, target segments/motifs,
assignment coverage, excluded oracle fields, and conserved mass. Obsolete
NPMI/cutoff/calibration fields are removed rather than relabeled, and no
promotion boolean is made authoritative.

The plan identifies both exact Step 0024 summary paths, the existing supervised
OSWorld summary, and reuse of the simple/phase/action/session controls. It
explicitly prohibits labeling a modified-binary grammar run as the Step 0024
baseline. Terminal completion now requires all five OSWorld folds, 287
sessions, 3,978 assignments, and operation-level Rust/Python equivalence, plus
all 405 CodeTrace targets, 20,866 assignments, all 20,461 adjacency positions
derived from complete segments, per-target equivalence, every planned
comparator row, and all mass.

This resolves the second must-fix. The commands are executable specifications
for code that implementation review must inspect before REAL PREFLIGHT; their
planned script files need not pre-exist at PLAN REVIEW.

### Repair 3 — Execution isolation versus adaptive evidence: resolved

The revised plan no longer claims that the grammar family was selected without
target-label influence. It makes the necessary distinction consistently in
admission, both population protocols, and comparison fairness:

- at execution time, OSWorld target-fold groups and CodeTrace target stages are
  unavailable to grammar learning/application and load only after persisted
  predictions; and
- at research-design time, prior label-based outcomes on both reused
  populations motivated choosing the grammar family.

Thus a valid result may be called target-label-isolated during execution, but
not target-naive, untouched, or independent confirmation. Both populations
remain adaptive post-hoc mechanism-development evidence. The repair requires
no new split, benchmark, control, or weaker paper claim and preserves the exact
thesis and RQ.

This resolves the third must-fix.

## Final Judgment

**APPROVE.** Paper-value admission holds, the grammar candidate is genuinely
different from the closed cutoff/window/calibration branches, one simple and
fully deterministic algorithm is registered, reference/target information is
fair for the stated post-hoc scope, Step 0024 remains the correct strongest
same-input baseline, and the complete matrix and exact Pareto promotion rule
are scientifically adequate. There are zero must-fix findings.

The experiment may proceed to implementation and the required fresh read-only
implementation review exactly as registered. This approval does not authorize
a second grammar variant, target-informed repair, new benchmark, paper/story/RQ
change, or any candidate metric before implementation review. REAL PREFLIGHT
still remains execution-only and subject to the skill's two-attempt limit.
