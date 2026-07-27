# Independent result-status review: RQ7 P1 held-out conformance

You are the independent post-run reviewer. Work strictly read-only. Do not
edit, create, delete, stage, commit, or push any repository file. Return only
your review as the final response.

The experiment is under:
`docs/tmp/build-and-evaluate/rq7-heldout-20260726/`.

Read completely:

- `protocol.md`
- `plan-review.md`
- `check-fixtures-attempt.json`
- `freeze-attempt.json`
- `result.md`
- `heldout-projects.json`
- the P1 and decision-d sections of
  `docs/tmp/build-and-evaluate/experiment-gap-audit-20260726/report.md`

You may inspect the runner statically if needed, but must not execute any of
its subcommands. Do not perform a second discovery/selection attempt. The
registered runner is append-only.

Independently decide:

1. Run status: valid, invalid, or incomplete.
2. Tested hypothesis: supported, contradicted, or inconclusive.
3. Whether the failed freeze permits any held-out question score or
   edge-ledger metric.
4. How, if at all, this attempt can be compared with the old repair-corpus
   60/60 B+C result.
5. Research value: decisive, supporting, diagnostic, or unusable.
6. Paper impact and the next paper-level decision.

Check that the report neither converts N/A into 0 nor treats absent ledgers as
exact equality. Distinguish an infrastructure/corpus/oracle validity failure
from a valid scientific negative. State whether build/preflight/full correctly
did not run after the frozen corpus contract failed. Keep the review concise
but evidence-based.
