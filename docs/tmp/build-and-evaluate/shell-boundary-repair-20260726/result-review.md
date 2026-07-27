# Result review

## Decision

**Pass stage 1 and proceed to stage 2 RQ1--RQ4 recomputation.**

The required original repair-corpus gate remains B+C 60/60. The repaired
116-question corpus reaches 100/116 overall, B+C 58/58, and D 29/29. Its
attempted, confirmed-effect, edge/call-status, and session-order ledgers all
match exactly.

## Material finding closure

The four lost B-family points in v2 are closed by source-direct semantics:

- the rejected leading-backslash wrapper call contributes no attempted read;
- both nested static exec calls are retained; and
- oracle-only shell parsing losses no longer alter the selected P0 relation
  counts.

The remaining audited calls also reconcile exactly: multi-source copy
destinations use source basenames, process-substitution reads survive,
multiline quotes do not erase earlier commands, non-recursive `git rm` keeps
its exact operands, and recursive deletes remain directory scope.

Intermediate preflights reached B+C 58/58 while the edge ledgers still
disagreed. The strict ledger gate correctly prevented those question-level
results from being accepted. Row-level review found that non-directory exact
actions could inherit an event-level scope from the first segment of a
compound command, and that directory knowledge was being applied in
candidate-file scan order rather than global event order. The final
implementation scopes actual directory operations only, applies scope state
after global sorting, updates oracle directory rename/delete state per action,
does not carry recursive scope across shell control operators, and keeps the
pre-existing conservative `mv` rule. The final rerun has zero missing and zero
extra entries in every ledger.

Independent review also caught two provenance/generalization defects before
commit. The active measurement's version had advanced to v5 while its embedded
general question specification still described v3; the embedded text now
matches the repaired grammar. Nested exec normalization could also overwrite
the outer native cwd with the first nested workdir, so a later nested exec
without a workdir inherited the wrong directory. The event builders now save
the outer cwd before unwrapping, and a dedicated fixture covers that fallback.
Final independent review also found that production stripped `&>` itself but
kept its named target as a copy operand, unlike both source-direct oracles.
The redirection reducer now distinguishes inline fd duplication such as
`2>&1` from named targets such as `&> log`, and a shared fixture covers the
latter.

A later attempt to generalize one ToolPath across multiple inline `cd`
transitions immediately failed the original repair gate at B+C 58/60
(eunomia.dev C2/C5). The 116-question run was not started. The generalized
change was rejected, its failed output retained only in the ignored debug
area, and the repaired grammar was narrowed to the audited single-leading-`cd`
process-substitution shape. A clean rebuild restored the required 60/60 before
the final 116-question run.

The 70/70 session-order ledger is a retained per-project aggregate check, not
a newly repaired score. Question answers and artifact identities were
recomputed under the repaired specification while the parent 116 question IDs
and P0--P4 paths remained fixed. This reduces selection independence by
design: it measures repair closure, not a new held-out sample.

## Validity boundary

The former held-out v2 corpus was inspected during this repair. It is therefore
strictly downgraded to **repair-corpus-v2**. The 100/116 result demonstrates
closure on the known failures, not fresh out-of-sample generalization. Any new
generality statement requires a third, independently selected corpus.

This stage intentionally does not modify `docs/paper/` or
`docs/evaluation.md`. Paper numbers should be synchronized only after the
stage-2 RQ1--RQ4 recomputation.
