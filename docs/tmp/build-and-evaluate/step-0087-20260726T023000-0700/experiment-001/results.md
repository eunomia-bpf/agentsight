# Results: direct multi-level annotation vs A2

Status: **COMPLETE / VALID**

## Completion repair

Amendment 2 authorized exactly one additional backend attempt for ordinal 53 with the complete session ID called out character for character. The attempt passed (`authorized_backend_attempt_3`), so deterministic normalization of attempt 2 was not used.

## Complete population

- 405 trajectories and 17,148 turns;
- 20,866 operations and 2,948 official stages;
- 251 task clusters across 4 frameworks;
- 494,862,929 source tokens conserved.

## Standard metrics

| Method | B³ P | B³ R | B³ F1 | Boundary P | Boundary R | Boundary F1 |
|---|---:|---:|---:|---:|---:|---:|
| Direct multi-level | 0.793409 | 0.735836 | 0.763539 | 0.389147 | 0.626032 | 0.479952 |
| A2 | 0.839025 | 0.606577 | 0.704113 | 0.290630 | 0.611089 | 0.393916 |
| Multi-resolution recurrence | 0.782026 | 0.575029 | 0.662740 | 0.192945 | 0.425875 | 0.265571 |

## Comparator provenance

The A2 numbers are paired against the stored adopted Step-0067 artifact. Its
experiment record describes automatic complete-path Agent marks followed by
deterministic root-only repair; it is not a binary-recursive policy. The result
therefore supports direct multi-level annotation over the actual adopted A2
artifact, and must not be described as defeating a binary-recursive A2.

## Paired task-cluster intervals

- Direct minus A2 B³ F1: point `+0.059426`, 95% interval `[+0.047665, +0.072580]`.
- Direct minus A2 boundary F1: point `+0.086035`, 95% interval `[+0.070105, +0.102593]`.
- Direct minus recurrence B³ F1: point `+0.100798`, 95% interval `[+0.086669, +0.115724]`.
- Direct minus recurrence boundary F1: point `+0.214380`, 95% interval `[+0.193321, +0.235083]`.

## Hypothesis verdict

The complete-population hypothesis is **SUPPORTED** under the predeclared
paired comparison rule against the actual stored A2 artifact. The result is a
backend comparison within fixed RQ3; it does not change the thesis or the
four-RQ paper story.

```text
run status: valid
tested hypothesis: supported
research value: decisive backend comparison
paper impact: additional RQ3 evidence
next paper decision: Adopt direct multi-level annotation over the stored adopted A2 artifact as the evaluated CodeTrace backend.
```

## Validity

- every one of 405 trajectories has a valid source-only annotation;
- all 17,148 turns and 20,866 operations are covered;
- operation mass is 20,866 and token mass is 494,862,929 on replay;
- canonicalization leaves zero adjacent display-path collisions;
- both operation and token profiles load in stock pprof;
- all 2,948 official stages and 251 task clusters are scored;
- paired populations match A2 and recurrence exactly.

## Cost

The backend used 415 Codex calls, 8689.405 s summed request wall, 2215.858 s active wall, 12,050,384 input tokens, and 231,886 output tokens. The full deterministic downstream pipeline took 11.516 s.

Machine-readable metrics, validity checks, costs, repair disclosure, and artifact paths are in `raw-results.json`.
