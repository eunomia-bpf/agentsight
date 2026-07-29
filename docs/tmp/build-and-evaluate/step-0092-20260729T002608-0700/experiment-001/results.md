# Same-model flat-segmentation ablation

Status: **INCOMPLETE / UNSCORED**

## Outcome

All 405 trajectories reached terminal status, but only 404 produced valid flat
annotations under the registered initial-call plus one-format-retry policy.
Ordinal 118 (`openhands-Anthropic__Claude-Sonnet-4-20250514-Thinking-path-tracing-8cc10d94`) repeated an unchanged
adjacent complete path on both attempts. That error is not the plan's sole
permitted deterministic repair (an otherwise-valid top-level session-ID
replacement). The response was therefore not altered.

The frozen scorer, official stages, full-population assembly, canonicalization,
pprof materialization, and paired bootstrap were not run. No 404/405 prefix was
scored, so this experiment supplies no hierarchy-minus-flat estimate, precision,
recall, F1, confidence interval, or paper-level RQ3 evidence.

## Mechanism and completion audit

- requested/terminal/valid trajectories: 405 / 405 / 404;
- accepted flat marks: 3,417 across the 404 valid trajectories;
- accepted raw path-depth distribution:
  `{"2": 3417}`; every accepted path
  is exactly the mandatory root plus one flat name;
- accepted unique raw names including roots: 2,394;
- terminal failures after retry: 1;
- ordinary retries: 5;
- deterministic format repairs: 0.

The exact Step 0087 source-packet audit found no stage, outcome, score, reward,
target, or label fields. The flat pipeline did not open the official stages or
score rows. The saved prompt diff and all 410 raw backend event streams remain
available for audit.

## Reused direct-hierarchy control

Step 0087 already directly emits complete variable-depth paths in one isolated
request per trajectory, explicitly without STOP/SPLIT recursion or iterative
semantic refinement. It remains the requested direct-hierarchy control and was
not rerun under a second name. Its complete adopted result is B-cubed
P/R/F1 `0.793409` /
`0.735836` /
`0.763539` and exact adjacent-boundary P/R/F1
`0.389147` /
`0.626032` /
`0.479952` over 4,496 groups. No
recursive/refined-minus-direct comparison exists because there is no genuinely
distinct refined condition.

## Backend cost to terminal status

| Measure | Flat attempt |
|---|---:|
| Model calls | 410 |
| Format retries | 5 |
| Input tokens | 11,885,715 |
| Cached input tokens | 3,977,984 |
| Output tokens | 183,961 |
| Reasoning-output tokens | 101,215 |
| Summed request time | 8110.029 s |
| Union active request time | 2038.273 s |
| First population request to terminal status | 2064.284 s |
| Resumed full-command wall (excludes earlier reused preflight) | 2030.232 s |
| Downstream full-population pipeline | not run |

The 410-call/token totals include the valid preflight trajectory because that
annotation was reused as one of the 405 population members. The operational
preflight completed that packet end to end; its score is not a paper result.

## Next paper decision

Do not report a hierarchy-minus-flat effect from this run and do not normalize
the failed marks after seeing the failure. Retain the Step 0087 direct-hierarchy
result. If the reviewer control is still required, run a newly planned,
prospectively reviewed complete flat arm; do not present this terminal attempt
as a scored result.

This outcome changes neither the four fixed RQs nor the thesis,
“Agent observability needs profiling, not only debugging.”
