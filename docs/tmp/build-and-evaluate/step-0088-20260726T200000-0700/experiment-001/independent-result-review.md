# Independent Result Review

```text
run status: valid
tested hypothesis: contradicted
research value: supporting
paper impact: mechanism or workload boundary
next paper decision: Do not promote the frozen direct backend as competitive on
OSWorld-Human or use the pilot gate as positive evidence. Retain this complete
negative result as an internal backend-transfer boundary, keep the fixed RQ3,
thesis, and positive paper program unchanged, and require any materially revised
backend to earn fresh final evidence before it can replace the existing
specialized rows.
```

## Review scope

This review is independent of the executor's interpretation. I read the task
specification, the complete runner, the Step 0087 instruction and response
schema loaded by that runner, the packet index and source packets, the frozen
OSWorld source, all raw-result and Markdown reports, all 287 accepted mark
files, all 288 parsed responses, all 288 Codex event streams and stderr files,
all 287 run records, every pilot and full score row, and all 160,000 retained
bootstrap draws. I also read and joined the frozen supervised-OOF,
reference-calibrated, and label-free-recurrence predictions and their summary
artifacts. I made no model call and did not modify an experiment artifact.

## Completion and gate

The established source filter independently reconstructs 287 eligible
multi-operation sessions, 3,978 operations, 3,691 adjacent pairs, and 2,042
session-local human groups. The source has 320 sessions with exact aligned
group annotations; the established at-least-two-operation eligibility rule
excludes the 33 singleton sessions, for which no adjacent-boundary decision is
possible. The retained packet population is the complete declared 287-session
population in lexicographic session-ID order.

The pilot is exactly the first 40 sorted session IDs: 398 operations, 358
pairs, and 182 gold groups. Direct B-cubed F1 is `0.656802616`; same-slice
label-free recurrence is `0.703266497`, so the binding difference is
`-0.046463881`. This satisfies the registered compute gate
`direct >= recurrence - 0.05` by `0.003536119`. The execution events show the
pilot score and PASS before the full backend started. Running the remaining
247 sessions was therefore authorized. The much lower pilot boundary F1 was
not part of the gate, so it did not permit stopping or block the full run.

The full run covers every declared session and reaches terminal status. There
are exactly 3,978 operation assignments and 3,691 adjacent decisions, with no
duplicate or missing score key.

## Independent metric reconstruction

I rebuilt session-local segments directly from accepted mark starts and from
each frozen comparator's pair decisions, then recomputed ordinary
per-operation B-cubed and exact adjacent-boundary counts from the frozen
`human_group` sequence. The reconstructed operation and pair rows are exactly
equal to every retained pilot and full score row. All reported metric values
match the independent reconstruction.

| Method | Boundary TP/FP/FN | Boundary P/R/F1 | Predicted groups | B-cubed P/R/F1 |
|---|---:|---:|---:|---:|
| Direct multi-level | 152 / 130 / 1,603 | .539007 / .086610 / .149239 | 569 | .293428 / .947327 / .448069 |
| Supervised OOF | 1,373 / 589 / 382 | .699796 / .782336 / .738768 | 2,249 | .835863 / .797096 / .816019 |
| Reference-calibrated | 1,618 / 1,036 / 137 | .609646 / .921937 / .733953 | 2,941 | .917000 / .711190 / .801087 |
| Label-free recurrence | 1,402 / 967 / 353 | .591811 / .798860 / .679922 | 2,656 | .855872 / .726966 / .786170 |
| Always-boundary control | 1,755 / 1,936 / 0 | .475481 / 1.000000 / .644510 | 3,978 | 1.000000 / .513323 / .678405 |

The direct result is not a precision/recall trade that remains competitive on
the other registered construct: it is below every requested comparator on
both F1 measures, including the always-boundary lower-bound control.

## Paired uncertainty

The bootstrap resamples whole session clusters with replacement and recomputes
the operation-micro B-cubed F1 or aggregate exact-boundary F1 within each
draw. This is the correct clustering unit for these task-instance sessions. An
independent implementation reproduced every one of the 10,000 retained draws
for each of the 16 pilot/full comparison-metric cells and reproduced every
stored percentile interval exactly.

| Direct minus baseline, full population | B-cubed F1 delta [95% interval] | Boundary F1 delta [95% interval] |
|---|---:|---:|
| Supervised OOF | -.367950 [-.444016, -.279954] | -.589529 [-.641014, -.532755] |
| Reference-calibrated | -.353018 [-.442962, -.250125] | -.584714 [-.647641, -.510328] |
| Label-free recurrence | -.338100 [-.428975, -.234028] | -.530683 [-.603923, -.443659] |
| Always-boundary control | -.230336 [-.321986, -.139840] | -.495271 [-.574675, -.410903] |

None of the 80,000 full-population delta draws is positive. The full
separation therefore does not depend on selecting a favorable full-run
equivalence margin. The task specification did not define such a margin for
the word “competitive”; the pilot's `0.05` margin is only the registered
execution gate and must not be repurposed as a full-result definition.

## Under-segmentation diagnosis

The direct backend emits 569 segments for 2,042 human groups and only 282
scored boundaries for 1,755 gold boundaries. It misses 1,603 gold boundaries.
Its high B-cubed recall (`.947327`) paired with very low B-cubed precision
(`.293428`) is the expected signature of merging many human groups into large
predicted segments, not successful recovery with a different harmless
granularity.

This is population-wide:

- 169 of 287 sessions receive only one predicted segment;
- 221 sessions have fewer predicted than gold groups, 41 have equal counts,
  and 25 have more;
- the median session-level predicted/gold group-count ratio is `0.4`;
- one 255-operation session with 181 gold groups receives one predicted
  segment, and a 199-operation session with 116 gold groups receives two.

The deterministic pilot was a weak warning rather than a representative
estimate. Its direct B-cubed F1 is `.656803`; on the remaining 247 sessions it
is `.418520`, while recurrence is `.792488`. The pilot averages 9.95
operations per session, compared with 14.49 in the remainder, and does not
contain several of the catastrophic long-session merges. This does not make
the gate incorrect: the gate was followed exactly and served only to authorize
the full spend.

The 569 reported path depths are 156 at depth one, 355 at depth two, 54 at
depth three, and 4 at depth four. The registered metrics flatten every sparse
path change into a segment boundary. They therefore test group partition and
boundary recovery, but not literal tag-name correctness, hierarchy-name
accuracy, nesting quality, or reusable cross-session operation identity.

## Annotation execution, retry, and cost

All 287 accepted responses satisfy the exact object schema, session identity,
ordered valid operation starts, mandatory common root, action-first 1--3-word
tag grammar, and no-identical-adjacent-path rule. Accepted responses exactly
match the corresponding raw marks.

There is one retry and it complies with the one-retry limit. Ordinal 219's
first response repeated an unchanged complete path at consecutive marks; the
recorded validator rejected it for exactly that contract error. Attempt two
produced a valid complete response and is the accepted mark. No other session
was retried, and no session failed after its permitted retry. All event streams
contain a final agent message and usage counters matching their run record.
They contain no command execution, file change, MCP call, or web-search item.
Every stderr file contains the same nonfatal stale-temporary-directory cleanup
warning; every backend process nevertheless returned successfully.

Independent cost aggregation matches the retained totals:

- pilot: 40 calls, 0 retries, 418.635452 summed backend seconds and
  110.449843 active seconds;
- complete run including the pilot: 288 calls for 287 sessions, 1 retry,
  2,854.536138 summed backend seconds and 728.360034 active seconds;
- complete raw usage counters: 5,483,576 input, 3,838,464 cached input,
  64,231 output, 40,843 reasoning-output, and 0 cache-write-input tokens.

These are the provider counters as retained; cached input is reported
separately and should not be added again to the input counter without a
provider-specific billing definition.

## Gold exclusion and metric circularity

Every model-visible turn contains exactly the registered nine fields:
`action`, `phase`, `target`, `repeat_state`, `repeat_signal`, `app`,
`environment`, `status`, and `tool`. The packets contain zero occurrences of
the scorer-only field keys `human_group`, `group_index`, `group_position`,
`group_size`, `group_pattern`, and `group_alignment`. Packet values and
operation IDs reproduce the frozen source exactly. The runner loads the Step
0087 instruction literal and appends only this session packet (plus the single
format-error message on retry).

Column exclusion alone is not sufficient evidence of semantic separation, so
I also enumerated exact scorer-vocabulary overlaps. No `human_group` identifier
appears in a visible field. Some common categorical words overlap auxiliary
gold vocabulary: visible `action` shares `fail`, `scroll`, and `select` with
`group_pattern`; `phase` shares `fail`, `input`, `observe`, and `system`;
`target` shares `scroll` and `system`; and `repeat_state=single` shares the
literal `single` with `group_position`. These are common source-category
values under different field meanings, not group IDs or boundary indicators,
and the nine-field information budget was explicitly fixed because it is the
same source-visible budget used by the stored predictor. The overlap should
prevent a paper from claiming that the vocabularies are wholly disjoint, but
it does not make the partition metric circular.

The candidate never receives `human_group` or the adjacent gold-boundary
vector. Gold enters only after all marks exist, when ordinary B-cubed and exact
boundary P/R/F1 are computed. Neither metric uses tag text, path depth, or a
candidate-defined oracle. The comparison is therefore target-blind with
respect to the tested group structure and is not defined by the direct
backend's own output.

## Baseline fairness

Each frozen comparator has exactly one decision for all 3,691 expected pair
keys. The supervised and recurrence artifacts' retained gold labels and
previous/current source-line joins match the frozen source with zero error;
the reference-calibrated fold files also cover the exact pair set without
duplicate, missing, or extra keys.

The rows have different legitimate roles and must remain labeled by their
information budgets:

- **Label-free recurrence** is the closest target-label-blind comparison. It
  uses other-session visible action-transition recurrence, whereas direct sees
  all nine source fields and a pretrained model in one complete-session call.
  Both are blind to target human groups, and direct loses decisively despite
  its richer per-session input.
- **Supervised OOF** uses the same nine visible fields but learns from human
  boundaries in the other folds. It is a valid specialized supervised
  comparator, not an equal-label-budget baseline.
- **Reference-calibrated** uses human groups in disjoint reference folds to fit
  its scalar. It is a valid optional supervised comparator, again not an
  equal-information competitor.
- **Always-boundary** is a lower-bound/null control, not a main baseline.

All four mechanisms engaged and used the same target operations and gold
scorer. The direct interface was not an avoidable failure: the task
specification deliberately limited it to the same nine fields, its complete
session was accepted, and it could place a mark at every operation. Runtime
and token budgets are not matched across deterministic and model-backed rows,
so this experiment supports an accuracy comparison, not a cost-superiority
claim. The unequal supervision of the two specialized rows also cannot be
used to claim equal-information inferiority or superiority. Neither caveat
rescues the direct result against the label-free recurrence or the
always-boundary control.

## Scientific interpretation

The completed experiment provides clean independent-population evidence about
one frozen backend. It contradicts the hypothesis that the unchanged direct
multi-level instruction recovers OSWorld-Human group structure competitively
with the reported specialized backends. The result isolates a transfer
boundary: a policy that produced useful sparse multi-level marks on the prior
CodeTrace setting becomes extremely conservative on GUI action sequences and
merges most human operation groups.

This is supporting evidence within RQ3, not a direct challenge to **“Agent
observability needs profiling, not only debugging.”** It neither invalidates
the operation/operation-stack model nor answers the whole tag-accuracy RQ. It
also cannot evaluate literal tag names or hierarchy semantics. The paper
should not present this row as positive evidence or weaken the fixed RQ3 to
fit it. The valid negative result should remain in experiment provenance and
bound the frozen direct backend; any future positive claim requires a
materially improved, source-only backend and a fresh complete evaluation.
