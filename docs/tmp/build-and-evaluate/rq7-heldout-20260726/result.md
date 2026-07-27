# P1 Held-Out Question and Full Edge-Ledger Conformance

## Outcome

- **Run status:** invalid.
- **Tested hypothesis:** inconclusive.
- **Failure stage:** frozen-corpus selection, before question generation,
  projection, scoring, or edge-ledger materialization.
- **Held-out score:** N/A; no held-out question was generated or scored.
- **Full edge-ledger conclusion:** N/A; no oracle or projection edge ledger
  was generated.

The unique preregistered freeze attempt failed the fixed corpus contract.  The
formal selector completed the first two cases (`agentsight` and `ActPlane`)
and, while processing the third fixed case (`bpf-developer-tutorial`), found
only 10 eligible semantic sessions after applying the cutoff, metadata
eligibility rules, and three historical-corpus exclusions:

```text
source selection failed: 10 sessions, available=['claude'], represented=['claude']
```

The project identification is an execution-transcript inference from the
frozen project order and the runner's two preceding successful-selection
messages; those stdout lines were not copied into the durable attempt JSON.
The authoritative durable machine record is `freeze-attempt.json`, which
records
`terminal_status=failed`, `error_type=RuntimeError`, the exact error above,
and runner SHA-256
`6df7a7ee8bed4ce2a5b4320da9b10aac1f710976b7af88623d21bd002fd6c33e`.
It establishes the 10-session corpus failure but does not independently name
the case; this provenance limitation does not change the invalid verdict.

## Protocol gates

| Gate | Result | Evidence |
|---|---|---|
| Preregistration before held-out generation | Pass | `protocol.md` |
| Independent pre-run review | Pass | `plan-review.md` |
| Shared fixtures | Pass | 8 action, 4 lifecycle, 5 native-root |
| v4-only fixtures | Pass | 4/4 primary/checker/expected controls |
| Six cases × 12 distinct roots | **Fail** | third case had 10 eligible sessions |
| Exactly 72 held-out sources | Not reached | corpus was never frozen |
| Exactly 120 new questions | Not reached | no question rows exist |
| Independent 120-answer/source-ledger check | Not reached | no oracle freeze exists |
| Real projection preflight | Not run | forbidden after corpus-contract failure |
| Six-case full run | Not run | forbidden after corpus-contract failure |

The fixture attempt completed at `2026-07-26T23:56:25.488067+00:00`.  The
single freeze attempt ran from `2026-07-26T23:56:37.225085+00:00` to
`2026-07-26T23:58:59.713512+00:00`.  No replacement project, lower quota,
second seed, or retry was used.

## Per-question decisions

There are no per-question decisions.  The registered questions were to be
instantiated only after all 72 source files and six workspace manifests were
copied and hash-sealed.  Because the corpus contract failed first, generating
questions would violate the preregistration.  N/A must not be reported as
0/120, an abstention, or a scientific failure.

## Edge-level ledger

There is no edge ledger.  Neither the private source oracle nor the production
projection was run on a frozen six-case corpus.  Consequently there are no
matched, missing, or extra edge counts and no precision/recall/F1 values.
Empty/N/A here must not be interpreted as exact equality or as a zero-edge
workload.

## Comparison with the prior 60/60

The prior **60/60 B+C** remains same-question repair-corpus regression
evidence over its original 72 files.  This attempt produced no independent
held-out 60-question B+C denominator, so it cannot confirm, contradict, pool
with, or numerically compare against the old 60/60.

## Interpretation and paper impact

Per the frozen decision rule, a corpus-contract failure makes the run invalid
and the held-out conformance hypothesis inconclusive.  The paper must not cite
this attempt as held-out or full-edge-ledger support.  Its conformance section
should retain the existing repair-corpus limitation and explicitly leave P1
open.

A future experiment would require a new preregistration whose feasibility
inventory executes the exact eligibility and historical-exclusion path before
fixing its per-case quota.  That would be a new study, not a repair or retry of
this immutable attempt.
