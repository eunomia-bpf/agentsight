# Full Run and Result: Recursive Operation Segmentation

**Timestamp:** 2026-07-23T21:34:00-07:00
**Status:** complete, valid execution; registered constructor hypothesis contradicted

## Question and fixed intervention

This experiment tests one constructor inside unchanged paper RQ3:

> Can a fixed source-only Agent recursively choose the most important
> responsibility transition in an interval, split on it, and repeat until it
> decides that no further semantic split is useful?

The intervention is `recursive-operation-segmentation-v4`, exactly as approved
in the Step 0066 plan and resumed in Step 0074. It uses Qwen3.6-27B Q4_K_M,
llama.cpp build 9870, one 32,768-token slot, temperature zero, and seed
`20260722`. It has no depth, leaf-count, or interval-length limit. The model
can see only public task text and source-native intent, progress, planned
action, and visible result. Official stage IDs, recurrence assignments, prior
candidate names, task clusters, and all scores remain unavailable during
inference.

## Complete execution

The source-only phase completed before the scorer opened the verified
manifest:

| Quantity | Complete result |
|---|---:|
| Sessions | 405 |
| Source-native turns | 17,148 |
| Operations | 20,866 |
| Root model calls | 405 |
| Recursive model calls | 1,585 |
| Total model calls | 1,990 |
| Effective splits | 922 |
| Model stops | 638 |
| Degenerate-current split stops | 25 |
| Emitted leaves / sparse marks | 1,068 |
| Sessions with an internal split | 73 |
| Maximum leaves in one session | 38 |
| Observed semantic depth | 1--5 |

The full outputs contain exactly one prediction for every operation. The
complete-population and fixed long-horizon profiles load in stock
`go tool pprof`; their operation masses are 20,866 and 5,750, respectively.
Their SHA-256 digests are:

- complete population:
  `60ebeeebc11f49ab2834ca19a1cb70e513a74c7d80cf562a6cebe7bb4ed0087f`;
- long horizon:
  `0d6a9abae94ee67a64364faa005f249730f67690fe3a473749db223961f00e3d`.

## Direct cost observations

The completed session caches record 6,761,329 prompt tokens, 39,357
completion tokens, and 6,800,686 total model tokens. Summing the 1,990
per-request timers gives 3,070.96 seconds of model-request time.

The final resumed execution directly measured:

| Component | Seconds |
|---|---:|
| Source adaptation over all 405 raw archives | 503.42 |
| Annotation loop, reusing 256 complete caches | 1,240.61 |
| Two pprof materializations and validation | 12.44 |
| Complete resumed wall time | 1,762.63 |

Because the final run deliberately reused 256 fixed caches, 1,762.63 seconds
is not a fresh full-annotation time. A source-plus-recorded-request-plus-profile
reconstruction is approximately 3,586.82 seconds before the one-time
16.13-second model load. Step 0075 must keep the direct resumed wall time and
the reconstructed full request total distinct; neither may be presented as the
other.

## Standard RQ3 result

Only after all predictions and profiles were complete did the scorer read the
official contiguous stages. It scored every operation with ordinary
unweighted B-cubed and every adjacent pair with exact boundary precision,
recall, and F1.

| Method | B³ P | B³ R | B³ F1 | Boundary P | Boundary R | Boundary F1 |
|---|---:|---:|---:|---:|---:|---:|
| Recursive candidate | .242532 | .945422 | **.386034** | .218703 | .057019 | **.090455** |
| Multi-resolution recurrence | .782026 | .575029 | .662740 | .192945 | .425875 | .265571 |
| Causal Qwen 3B | .735681 | .581999 | .649878 | .183990 | .423909 | .256606 |
| Native source tree | .974547 | .248903 | .396530 | .151090 | .915455 | .259373 |
| Source-native turn | .983154 | .221199 | .361145 | .141910 | .934330 | .246396 |

The recursive candidate emits only 863 contiguous predicted occurrences for
2,948 official stages. Its high B-cubed recall and low precision, together
with only 145 recovered official boundaries out of 2,543, identify the
failure mode: the fixed policy under-segments most sessions. It avoids the
earlier one-leaf-per-turn fragmentation failure, but replaces it with a
one-or-few-leaves-per-session collapse.

Candidate minus recurrence B-cubed has a task-clustered 10,000-resample 95%
interval of `[-0.306589, -0.245664]`; candidate minus causal Qwen 3B is
`[-0.293000, -0.233085]`. Both positive fractions are zero. The registered
hypothesis is therefore contradicted, not mixed.

## Execution incidents

The first scoring command supplied the Step 0054 score table as the optional
causal control. That table does not contain the loader's expected
`causal_visible_path` field, so the process stopped with `KeyError` before it
loaded official stages or emitted a metric. The corrected invocation points
to the already completed Step 0056 compatible score rows. This changes no
prediction, reference, metric definition, bootstrap, or scientific decision.

An earlier one-second shell timeout also terminated a score invocation before
output. The successful score then ran the identical command with a sufficient
process timeout. These are execution incidents, not constructor iterations.

## Scientific disposition

The recursive constructor is not adopted and must not replace A2, recurrence,
the thesis, the four fixed RQs, or the two product cases. It should remain in
auditable research history as a complete negative mechanism result.

The result supplies useful RQ4 cost data for one fully automatic local backend,
but its cost cannot be used to imply acceptable structure quality. Conversely,
the positive A2 structure result cannot inherit this backend's measured token
or wall cost. Step 0075 must present backend-specific quality and cost
together.

The next scientific action is not another prompt or benchmark. It is the
already selected RQ4 accounting experiment, using existing complete runs:
shared source adaptation, deterministic recurrence, automatic Agent A2 worker
envelopes, local 3B, recursive 27B, and fixed-mark pprof replay. The current
paper remains unchanged until that evidence is independently reviewed.
