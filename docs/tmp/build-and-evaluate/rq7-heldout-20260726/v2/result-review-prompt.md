# Independent result review: P1-v2 held-out conformance

You are the independent post-run reviewer.  Work strictly read-only.  Do not
edit, create, delete, stage, commit, or push any repository file.  Do not run
any held-out runner subcommand or repeat discovery, selection, oracle,
projection, preflight, or full.  Return only your evidence-based review.

The experiment is under:
`docs/tmp/build-and-evaluate/rq7-heldout-20260726/v2/`.

Read completely:

- `protocol.md`
- `plan-review.md`
- `freeze-attempt.json`
- `build-attempt.json`
- `preflight-attempt.json`
- `full-attempt.json`
- `raw/freeze/freeze-summary.json`
- `build/code-seal.json`
- `raw/full/summary.json`
- `raw/full/edge-summary.csv`
- `raw/full/edge-diff.csv`
- `raw/full/question-results.csv`
- `result.md`

Inspect `scripts/heldout_v4.py`,
`scripts/rq7_source_oracle_check_v2.py`, the private freeze manifest, and
frozen native calls only as needed to recompute or explain the results.

Independently decide:

1. Run status: valid, invalid, or incomplete.
2. Tested hypothesis: supported, contradicted, or inconclusive.
3. Research value: decisive, supporting, dependency-only, redundant, or
   unusable.
4. Paper impact: mechanism/workload boundary, additional RQ evidence, or
   direct thesis challenge.
5. The next paper decision.

Audit the exact corpus counts and quota formula, question independence,
checker counts/hash, attempt order, seal/manifest linkage, complete workload,
116 per-question decisions, B+C and D scores, all exclusions, and the
attempted/confirmed/call-status/session-order ledgers overall, by project, and
by vendor.  Check that wrong, negative, failed, and extra/missing rows remain
reported.

One known analysis issue requires an independent judgment.  The raw runner's
overall `session_order` aggregate counted one row per production call and
reported actual=6524, although the frozen key is the unique
`(native_session_id, session_ordinal)` pair.  Project and vendor rows use the
unique-pair definition and report 70/70 exact.  `result.md` preserves the raw
files but reports the protocol-defined corrected overall value 70/70 with
precision=recall=F1=1.0.  Recompute this and decide whether the correction is
valid and whether the aggregation bug changes run status or hypothesis.

Also audit whether loading the registration-revision measurement script
read-only from Git and using the newer working-tree copy only for the
build-time shared fixture (the only diff is an unreachable plot caption)
affects scientific validity.  Do not treat a plotting-only, fixture-unreached
line as semantic evidence without showing how it changes the executed path.

The old 60/60 is repair-corpus evidence over 72 different files.  Decide how
it relates to the new 54/58 held-out result; do not pool or rescale unequal
denominators.  Verify that A is reported but not a pass gate.

Return the five required judgments exactly and then concise supporting
evidence.  Do not propose changing any score.
