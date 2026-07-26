# Independent result review

## Judgment

```text
run status: valid
tested hypothesis: supported
research value: decisive
paper impact: additional RQ evidence
next paper decision: Adopt direct multi-level annotation as the evaluated
CodeTrace backend, while describing the comparator as the adopted A2
automatic-Agent/root-repair artifact rather than a binary-recursive policy.
```

The complete result is valid and the direct backend beats both paired
comparators on ordinary operation-level B-cubed F1 and exact adjacent-boundary
F1 with wholly positive task-clustered intervals. This is decisive for backend
selection on this fixed CodeTraceBench population and supporting evidence
toward fixed RQ3, not a complete answer to RQ3 or a thesis change.

## Independent reconstruction

I read `task-spec.md`, including both binding amendments, and independently
parsed the source packets, raw marks/events, run records, assembled and
canonical artifacts, score rows, stored A2 rows, recurrence assignments, and
the relevant harness/scorer/canonicalizer code. I did not call the experiment
scorer. I recomputed the standard metrics and all four 10,000-resample paired
intervals directly from the per-operation and adjacent-pair rows.

### Amendment-2 repair

Ordinal 53 has exactly three raw event files and no fourth. Attempts 1 and 2
both returned the same truncated session ID and otherwise passed the response
contract. The latest run record contains those two attempts plus exactly one
`amendment_2_additional_attempt`. Attempt 3 returns the complete required ID,
including `-f7c2004c`, has no validation errors, and its complete JSON response
is byte-for-value equal to `raw-marks/0053.json`. The repair method is therefore
`authorized_backend_attempt_3`; deterministic attempt-2 session normalization
was not used.

### Completion and conservation

Independent counts are:

| Quantity | Recomputed |
|---|---:|
| trajectories | 405 |
| source-native turns | 17,148 |
| operations / scored operation rows | 20,866 / 20,866 |
| adjacent pairs | 20,461 |
| official stages | 2,948 |
| task clusters | 251 |
| sparse direct marks | 4,496 |
| operation-count mass | 20,866 |
| provider-token mass | 494,862,929 |

All 405 raw annotations pass the exact response contract, their session set is
one-to-one with the sorted packet index, and the packaged annotation batch is
equal to the individual raw-mark files. Operation-count and token inputs have
the same 20,866 `(session, step_id)` keys. Assembled and canonical predictions
also have identical complete key sets and identical temporal occurrence/depth
partitions. Recomputing adjacent canonical display paths finds zero collisions.

Both emitted profiles load in stock `go tool pprof`. Its readback reports
`20,866 total` for the operations profile and `494,862,929 total` for the token
profile, agreeing with the source JSONL sums.

## Recomputed standard results

| Method | B³ P | B³ R | B³ F1 | Boundary P | Boundary R | Boundary F1 |
|---|---:|---:|---:|---:|---:|---:|
| Direct multi-level | 0.793409 | 0.735836 | 0.763539 | 0.389147 | 0.626032 | 0.479952 |
| A2 | 0.839025 | 0.606577 | 0.704113 | 0.290630 | 0.611089 | 0.393916 |
| Multi-resolution recurrence | 0.782026 | 0.575029 | 0.662740 | 0.192945 | 0.425875 | 0.265571 |

The direct boundary confusion counts are TP 1,592, FP 2,499, FN 951, and TN
15,419. A2 has TP 1,554, FP 3,793, FN 989; recurrence has TP 1,083, FP 4,530,
FN 1,460. Thus the direct gain is not only indiscriminate contraction: it
improves boundary precision and recall over both baselines, although its
absolute boundary precision remains 0.389 and it still emits 4,496 groups for
2,948 official stages.

Recomputed global point differences and paired task-cluster bootstrap intervals
are:

| Comparison | Metric | Point delta | 95% interval |
|---|---|---:|---:|
| Direct - A2 | B³ F1 | +0.059426 | [+0.047665, +0.072580] |
| Direct - A2 | Boundary F1 | +0.086035 | [+0.070105, +0.102593] |
| Direct - recurrence | B³ F1 | +0.100798 | [+0.086669, +0.115724] |
| Direct - recurrence | Boundary F1 | +0.214380 | [+0.193321, +0.235083] |

Every bootstrap has positive fraction 1.0. These values reproduce
`raw-results.json` and `results.md`; the small distinction between each global
point delta and the bootstrap mean is correctly not conflated.

## Validity, leakage, exclusions, and fairness

- The 415 raw Codex event files contain 415 final `agent_message` items and no
  command, file-change, MCP, or web-search item. The source-packet recursive key
  inventory contains only task/session/framework, turn intent/progress/action,
  visible result, operation IDs, and source provenance. It contains no
  stage/outcome/score/reward/label key, and none of the 2,948 exact official
  stage IDs occurs in packet text.
- Annotation and canonicalization complete before scoring. The canonicalizer
  accepts no target-stage, outcome, or score input and preserves the temporal
  partition exactly. Therefore the standard metrics are defined by independent
  official stages, not circularly by the method output.
- There are no scientific-population exclusions: all 405 trajectories, all
  20,866 operations, all 2,948 stages, and all 251 task clusters enter every
  reported comparison. Invalid format attempts remain in the raw event/run
  record rather than being hidden.
- Direct and A2 have exactly equal operation and pair keys, task clusters, and
  official oracles. Recurrence is scored on those same rows. Direct receives
  the fixed source-only packets; A2 had source-only evidence and could
  adaptively follow source references, so A2 is not handicapped on visible
  information. Recurrence is a deterministic alternative with a narrower
  visible-field mechanism; its comparison is useful but does not isolate equal
  model/information budgets.
- Important naming correction: the adopted A2 artifact is documented in Step
  0067 as automatic Codex-subagent complete-path marks plus a deterministic
  one-turn root-only repair. That plan explicitly excluded the incomplete
  recursive LLM method. Consequently, the numerical A2 comparison is fair and
  decisive against the actual adopted A2 artifact, but it must not be described
  as evidence against an A2 “binary-recursive policy.”

## Cost audit and interpretation boundary

Selecting the latest terminal record per ordinal independently gives 396
one-call trajectories, eight two-call trajectories, and ordinal 53 with three
calls: 415 calls total, including exactly one Amendment-2 additional call.
Summing retained telemetry reproduces 8,689.405 s request wall, 2,215.858 s
union-of-active-call intervals, 12,050,384 input tokens, 6,008,320 cached input
tokens, 231,886 output tokens, and 116,909 reasoning-output tokens. The reported
11.516 s downstream pipeline stopwatch is consistent with the recorded
successful assembly, canonicalization, two profile builds/readbacks, scoring,
and paired analysis.

The A2 3,261.89 s value is correctly labeled only as a historical artifact-time
envelope with unavailable model/provider tokens, not as comparable inference
time. Step 0086's 42-record figures are also context only, not a matched
per-trajectory cost baseline. The direct run therefore supplies valid absolute
backend telemetry, but it does not establish a statistically matched speed or
token-cost advantage over A2.

Finally, official flat stages evaluate the leaf occurrence partition and exact
boundaries. They do not validate nested topology, literal semantic-name
accuracy, cross-session name equivalence, user utility, or other agent/task
families. The admissible result is the strong positive CodeTrace backend
comparison above.
