# Independent plan review

Verdict: **REVISE**

## Blocking fixes

1. Fully freeze the Terminus2 timestamp mapping: occurrence-ordered command
   matching, exact normalized sequence equality, blank command assigned to the
   next retained timestamp, and explicit accounting for all imputed and
   minimum-one-second mass.
2. Add a direct unchanged-hierarchy oracle comparing evidence-to-operation
   paths or complete stack multisets against the accepted count replay.
3. Register exact adapter, test, replay, pprof, renderer commands, raw outputs,
   completion rule, and PNG filenames.
4. Bound the R114 claim to task responsibility -> outer wrapper tool ->
   retained system effects. It lacks inner LLM identity, exact filenames,
   reads, and network events; do not merge it rhetorically with Step-0086 into
   one stronger chain.
5. Call a target “created” only for a retained successful `Add File` header.
   Keep update/delete/move separate and do not infer truncated targets.

## Key cautions

- The time width is a product-compatible integer attribution convention, not
  exact observed wall duration.
- R114's failure-retry profile omits the expected `python3 missing_file.py`
  event and reports one false negative; failure-cause correlation is
  unavailable.
- Network-failure correlation is unavailable only after the full scan confirms
  the inventoried absence.

Reviewer disposition: full execution is blocked until all five repairs are
implemented and checked in preflight.

## Re-review

The first repair pass fixed the five design issues but left one executable
defect: the hierarchy oracle attempted to parse a full evidence ID as an
integer. The adapter now keys transitions by exact evidence ID, and an
integration test calls the oracle on the frozen artifacts and requires 489
expanded paths, 489 workspace paths, zero mismatches, and `exact_match=true`.

Final independent verdict: **APPROVED**. Seven adapter tests pass, including
the frozen-artifact 489/489 zero-mismatch hierarchy oracle. Proceed to real
preflight and the full deterministic replay under the registered boundaries.
