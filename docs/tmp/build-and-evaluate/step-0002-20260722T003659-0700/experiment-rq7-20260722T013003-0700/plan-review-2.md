# RQ7/F10 Independent Plan Review — Round 2

**Reviewed:** 2026-07-22  
**Reviewer role:** independent experiment-plan reviewer; no implementation or
result was changed  
**Verdict:** **PASS, for a dependency-only benchmark-readiness audit**

## Scope of this verdict

The revised plan no longer claims to answer canonical RQ7.  It asks only
whether the already frozen RQ1 directory contains the immutable native-source,
cutoff-state, method-interface, and template prerequisites required by a future
matched benchmark.  It explicitly forbids baseline execution, question
generation, accuracy/advantage/cost estimates, and imputed values.  Under that
narrow contract, the audit is scientifically honest and executable.

This PASS does **not** admit a paper claim that Artifact Trajectory is more
accurate, has higher coverage, supplies better evidence, or costs less than any
baseline.  It also does not close RQ7.  Its research value is
`dependency-only`; the result can only say which prerequisites are present and
why the matched comparison stopped.

## Round-1 blockers: disposition

| Round-1 blocker | Round-2 disposition | Status |
|---|---|---|
| Native admitted prefixes and cutoff worktree state were not frozen | They are now audit targets, not assumed inputs; absence is N/A and stops the comparison | Closed for this readiness audit |
| Five named methods lacked executable matched interfaces | No method is run; deterministic admission predicates replace performance claims | Closed for this readiness audit |
| Artifact lineage could become a circular oracle | No oracle or question set is built; RQ1 identity tables only establish that the normalized trajectory condition exists and cannot accuracy-score itself | Closed |
| TRUE/FALSE/UNAVAILABLE/AMBIGUOUS rules were contradictory | No facts are scored in this step; the four dispositions are deferred as mandatory inputs to a new reviewed matched-run plan | Closed |
| The 30-question/four-project gate hid template-level gaps | The gate is explicitly `not evaluated`; rename's three-project limit is disclosed and cannot be borrowed across families | Closed |
| Evidence precision/recall lacked a unique reference set | No evidence metric is emitted; validity/sufficiency/burden are deferred to a future plan | Closed |
| Accuracy, advantage, and cost estimands were undefined | All such panels and values are prohibited | Closed |
| F10 could fabricate missing values | Every cell has readiness status, N/A is distinct from zero, and the final panel states `MATCHED COMPARISON STOPPED` | Closed |

## Why the revised audit is non-circular

The script may inspect normalized events and the RQ1 artifact/mutation tables
only to answer structural questions such as “does this frozen file exist?”,
“does it match its preregistered hash?”, “which required linkage fields are
present?”, and “is the normalized trajectory projection available?”.  It does
not treat an RQ1 artifact ID, persistence label, reuse outcome, validation
outcome, or lineage relation as ground truth for another method.

Native-prefix, worktree-revision, untracked-snapshot, ProcGrep-preflight, and
Raw-log-LLM contracts must be verified by the presence and schema of their own
declared records.  They may not be inferred from normalized events, RQ1
tables, current live session files, or current worktrees.  Because the audit
never produces method answers, there is no oracle and therefore no circular
accuracy score in this step.

## Execution invariants for the PASS

These are interpretations of the approved plan, not requests for a broader
experiment.

1. **Do not re-baseline hashes.** “Immutable gzip and SHA-256 exists” means the
   script compares each current frozen input to the expected SHA-256 already
   recorded by the authoritative RQ1 run (the RQ1 `commands.log`, or an exact
   immutable copy of that list).  Computing a new hash and accepting that same
   value as its own reference is invalid.  If the expected hash is unavailable
   or mismatched, the normalized spine is `partial`/`N/A`, never `present`.
2. **Use exact contract locations.** The implementation must freeze the
   expected names/schemas for the native-prefix manifest/archive,
   per-worktree-revision manifest, cutoff-untracked disposition,
   ProcGrep-preflight record, and Raw-log-LLM contract before checking for them.
   It must not search loosely for a similarly named file and declare readiness.
   A missing file is an ordinary N/A row.
3. **Keep status vocabularies separate.** Source-contract cells use
   `present`, `partial`, or `N/A`; method rows use `measured` only to mean that
   the prerequisite itself was machine checked, `coverage-only` for a runnable
   normalized projection lacking independent truth, and `N/A` for an
   unexecutable matched condition.  None of these words denotes method
   accuracy.
4. **No current-state recovery.** A live Git checkout, live native session
   file, aggregate repository revision, or RQ1 final-state output cannot repair
   a missing cutoff-native or per-worktree contract.  Such a requirement stays
   N/A even if current state happens to be readable.
5. **No implicit ProcGrep enrichment.** The pinned revision is a declared
   candidate, not an executed baseline.  Readiness requires its own recorded
   real preflight for Claude, Codex, and Gemini.  No path/source-ID crosswalk or
   project-authored query result may be counted as an official ProcGrep
   preflight.
6. **No hidden question counts.** Event, session, source-call, artifact, or
   mutation counts may describe source structure, but cannot be labeled as
   eligible/scored questions.  The `30 x 4` gate remains literally “not
   evaluated”.
7. **Preserve N/A in plotting.** Plotting code must consume explicit status
   rows.  It may not coerce missing values to `0`, compute ratios with missing
   denominators, or drop stopped methods/templates from the axes.

## Expected decision shape, not a preregistered result

The existing directory is known to contain normalized project/event/artifact/
mutation outputs, while Round 1 found no frozen native-prefix archive or
per-worktree cutoff-state contract.  That makes a stopped matched comparison
the likely outcome, but the script must still derive every cell from the frozen
files and expected hashes.  This review does not pre-fill the result matrix or
authorize a value based on that expectation.

If the audit confirms the missing contracts, the valid interpretation is:

- normalized Counts prerequisites are present for descriptive source counts;
- the normalized Artifact Trajectory projection is available only as
  coverage-only, with no independent accuracy oracle;
- Final State, ProcGrep, and Raw-log LLM matched conditions are N/A;
- the four template families and their `30 x 4` gates are not evaluable; and
- the canonical matched RQ7 comparison is stopped.

Any stronger interpretation would violate the plan.

## Figure/paper boundary

The proposed matrix is valid as a transparent readiness/limitations figure and
as proof that missing prerequisites were not converted into fabricated
performance.  If copied into the paper, its title and caption must say
“benchmark-readiness/source-contract audit; no baseline was run” and must retain
the `MATCHED COMPARISON STOPPED` panel.  It cannot be described as the RQ7
measurement result, counted as evidence for trajectory superiority, or used to
claim that RQ7 is answered.  A future capability F10 still requires the new
reviewed matched-run plan specified in lines 127--130 of the revised plan.

## Decision

**PASS for execution of the narrowed dependency audit.** The plan now has a
real command, fixed frozen inputs, machine-checkable requirements, deterministic
stop behavior, explicit N/A semantics, and a non-fabrication figure contract.
No additional baseline, oracle, LLM call, question sampling, or performance
analysis is required or authorized in this step.  Independent result review
must enforce the invariants above before the readiness figure is used anywhere.
