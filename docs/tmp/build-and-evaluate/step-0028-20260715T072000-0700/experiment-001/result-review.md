# Independent Result Review

**Skill used:** `research-experiment-design`
**Review type:** fresh read-only result and closure audit
**Verdict:** **PASS**
**Remaining must-fix findings:** none

## Scope And Standard

I read the complete `research-experiment-design` skill and its directly
required `references/plan-template.md`. I then read the approved experiment
plan, both plan-review rounds, the independent implementation review, the two-
attempt preflight failure record, the experiment result, and the current step
report. I inspected the current OSWorld evaluator control flow, the product and
checker changes, the raw experiment roots, and the worktree diff only to
determine what executed and what candidate-owned material remains.

I did not run a candidate metric, a preflight, a full evaluator, or a third
attempt. I did not edit product or evaluator code, the paper, canonical
research documents, skills, the branch, or the read-only paper submodule. This
report is the only file I changed.

The governing rule is unambiguous: REAL PREFLIGHT permits at most two attempts,
a self-authored harness failure spends an attempt, repairs do not reset the
count, and a second invalid attempt closes the experiment. An implementation
review approval establishes only that code may enter REAL PREFLIGHT; it is not
a scientific result and does not waive that limit.

## Execution Reconstruction

Both recorded commands are the same approved OSWorld-Human preflight command.
The failure record preserves the observed error for each attempt:

```text
06fe7178-4491-4589-810f-2e2bc9502122: fewer than two actions
```

The two failures occurred at different adapter states but at the same class of
self-authored eligibility defect:

1. attempt 1 loaded the broad source without first applying the established
   `group_alignment=exact` eligibility condition;
2. after that repair, attempt 2 still made a singleton exact-alignment session
   fatal instead of excluding it as the established Step 0024 helper does.

Current source control flow independently confirms the recorded stopping
point. `main()` creates the requested output directory, checks inputs and the
binary version, and then calls `load_visible()`. That loader raises on the
singleton at its `len(sequence) >= 2` assertion. NPMI and cutoff fitting occur
only later in `fit_cutoff()`, Rust input files and the product invocation occur
only later in `run_product()`, target predictions are written only after the
product and equivalence checks, and target annotations are scored only after
prediction persistence.

The raw-artifact state agrees with this control-flow reconstruction:

- `.agentsight/experiments/rq3-reference-calibrated-recurrence-v1/` contains
  only an empty `preflight/` directory;
- there is no fold directory, score-reference file, calibration file, target
  file, profile, prediction JSONL, pair/operation output, or summary;
- the CodeTraceBench and Rust-equivalence raw roots do not exist; and
- the failure record states that CodeTrace preflight and both full runs were
  never started.

Therefore neither attempt reached candidate construction or computation. In
particular, no fitted cutoff, candidate boundary, B-cubed score, comparator
relation, or target-aware feedback exists. The recorded 287-session / 3,978-
operation / 3,691-pair reconciliation is a read-only recovery of the already
registered Step 0024 population, not a candidate result.

## Result Classification

The reported classification is correct:

```text
run status: invalid
tested hypothesis: not tested
research value: dependency-only
paper impact: none
next paper decision: no paper, RQ, hypothesis, claim, thesis, contribution,
                     or story change
```

`inconclusive` would be too generous because no valid candidate execution
occurred. `contradicted` or a negative-result label would be scientifically
wrong because the algorithm never produced an observation. Static tests and
implementation review provide software evidence only; they do not answer RQ3,
support the calibration hypothesis, or count as research progress.

The experiment must remain closed after two attempts. Fixing the singleton
handling and rerunning it as a nominal third attempt, changing a run tag, or
opening another control interface would violate the skill rather than repair
the scientific record. No CodeTrace preflight or full run may be appended to
this closed experiment.

## Paper And Scientific-Scope Consequences

No reader-facing change is authorized. Specifically, this invalid run cannot:

- update the answer to **RQ3: How accurate are the tags?**;
- change the fixed reference-calibration hypothesis;
- change the exact thesis, the four-RQ architecture, the original AgentProf
  story, or the contribution surface;
- weaken or strengthen a claim;
- add a paper number, result row, limitation, or negative-result narrative; or
- motivate another cutoff, feature, benchmark selector, or target-informed
  retry.

The current `experiment-result.md`, `preflight-failures.md`, and step report
state these consequences accurately. They do not confuse harness closure with
scientific evidence.

## Minimum Disposition Of Candidate Changes

The minimum clean disposition is to preserve the complete Markdown audit trail
but remove the unvalidated candidate implementation before the outer loop
commits or continues research. Retaining it in a commit would make an
unvalidated user-facing calibration mode look like accepted product progress;
retaining it indefinitely as dirty code would leave the worktree ambiguous.
The implementation review is sufficient to preserve what was attempted but is
not promotion authority.

Removal must be narrow and ownership-aware:

- remove only the Step 0028 calibration hunks from
  `agentpprof/src/main.rs`, `agentpprof/src/profile.rs`, and
  `agentpprof/tests/profile_spec_cli.rs`;
- remove only the three Step 0028 untracked evaluators:
  `script/rq3_reference_calibrated_common.py`,
  `script/rq3_reference_calibrated_recurrence_eval.py`, and
  `script/rq3_reference_calibrated_codetracebench_eval.py`;
- retain the Step 0028 plan, reviews, failure record, result, step report, and
  this result review as the auditable history; and
- retain the separate Step 0027 arithmetic correction, which is factual and
  not candidate implementation.

This is not a whole-worktree revert and must not touch unrelated or prior
changes. No product version bump, documentation promotion, paper edit, skill
edit, branch action, or submodule action is appropriate. A future experiment
may use the recorded lesson when choosing a genuinely new admitted path, but
it cannot represent a repaired rerun of this closed two-attempt protocol.

## Final Verdict

**PASS.** The INVALID / no-scientific-result classification is supported by
the artifacts and control flow, closure after two self-authored preflight
failures is required by `research-experiment-design`, and the reports correctly
prohibit every paper-level change. There are zero must-fix findings in the
result record. The outer-loop disposition should now perform the narrow
candidate-code removal above and preserve the Markdown history.

## Follow-Up Disposition Audit — 2026-07-15T08:04:37-07:00

**Audit identity:** narrow post-removal follow-up under
`research-experiment-design`
**Final verdict after disposition:** **PASS**
**Remaining must-fix findings:** none

I performed the requested read-only follow-up after the outer agent applied
the disposition. I did not rerun a metric, preflight, full evaluator, or
candidate. I also did not edit product/evaluator code, the paper, skills, or
canonical documents, and performed no Git action.

The completed state matches the required disposition:

- `git diff --exit-code` reports zero difference from entry `HEAD` for
  `agentpprof/src/main.rs`, `agentpprof/src/profile.rs`, and
  `agentpprof/tests/profile_spec_cli.rs`;
- `script/rq3_reference_calibrated_common.py`,
  `script/rq3_reference_calibrated_recurrence_eval.py`, and
  `script/rq3_reference_calibrated_codetracebench_eval.py` are all absent;
- the only remaining tracked diff is the separate Step 0027 arithmetic
  correction;
- every untracked Step 0028 artifact is Markdown, consisting of the plan,
  plan review, implementation review, failure record, experiment result,
  result review, and step report; and
- the restored source inventory is the original 42 unit tests, 8 profile CLI
  tests, and 3 standard-trace CLI tests. The step report records that this
  restored original suite passed. The earlier 44 / 9 / 3 counts in the
  implementation record correctly describe the pre-removal candidate state,
  so the two sets of counts are historical stages rather than a contradiction.

`step-report.md` now states that candidate code was removed, the original
suite passed, the experiment remains closed invalid, the hypothesis was not
tested, and no paper action is authorized. `experiment-result.md` likewise
records the completed narrow disposition while preserving the fact that the
candidate implementation had passed static review before REAL PREFLIGHT. Both
reports are accurate and preserve the distinction between implementation
checks and scientific evidence.

**Follow-up final verdict: PASS.** The candidate implementation is gone, only
the intended Markdown history and independent Step 0027 correction remain,
and there are zero disposition or reporting must-fix findings.
