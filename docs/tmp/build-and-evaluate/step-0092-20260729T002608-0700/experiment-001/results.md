# Same-model flat-segmentation ablation

Status: **COMPLETE / VALID**

## Scientific result

| Method | B³ P | B³ R | B³ F1 | Boundary P | Boundary R | Boundary F1 | Groups |
|---|---:|---:|---:|---:|---:|---:|---:|
| Direct variable-depth hierarchy (Step 0087) | 0.793409 | 0.735836 | 0.763539 | 0.389147 | 0.626032 | 0.479952 | 4,496 |
| Same-model flat partition | 0.698188 | 0.819017 | 0.753791 | 0.431509 | 0.511600 | 0.468154 | 3,420 |

Hierarchy minus flat B³ F1 is
`+0.009747`
with a 10,000-resample paired task-cluster 95% interval of
`[-0.003361, +0.023660]` (seed `20260720`).
Hierarchy minus flat exact adjacent-boundary F1 is
`+0.011798`
with interval
`[-0.007351, +0.031698]`
(seed `20260722`).

The predeclared hierarchy-benefit hypothesis is **INCONCLUSIVE**.

## Control-2 audit

Step 0087 directly generated complete variable-depth paths in one isolated
request per trajectory and explicitly prohibited STOP/SPLIT recursion. It had
no external recursive controller or iterative semantic refinement. Its complete
20,866 operation rows and 20,461 pair rows are therefore the requested direct
hierarchy control and were reused without new calls. No
recursive/refined-minus-direct comparison is reported because no distinct
refined condition exists.

## Completion and mechanism engagement

- all 405 trajectories, 17,148 turns, 20,866 operations, 20,461 pairs, 2,948
  stages, and 251 task clusters are included;
- every raw flat path has exactly the mandatory root plus one non-root semantic
  name;
- the flat arm emits 3,420 marks/groups and its raw path-depth
  distribution is `{"2": 3420}`;
- the reused Step 0087 raw depth distribution is
  `{"1": 3, "2": 2873, "3": 1588, "4": 32}`;
- operation mass 20,866 and token mass 494,862,929
  are conserved; canonicalization preserves the temporal partition and leaves
  zero adjacent display-path collisions; both profiles load in stock pprof.

## Backend and cost

The flat arm used pinned `codex-cli 0.145.0`, `gpt-5.6-sol`, ignored user
configuration, default reasoning/decoding, read-only ephemeral isolation, up
to four workers, a 1,200-second timeout, and one ordinary format retry.

| Measure | Flat arm |
|---|---:|
| Model calls | 410 |
| Format retries | 5 |
| Deterministic mechanical repairs | 1 |
| Input tokens | 11,885,715 |
| Cached input tokens | 3,977,984 |
| Output tokens | 183,961 |
| Reasoning-output tokens | 101,215 |
| Summed request time | 8110.029 s |
| Union active request time | 2038.273 s |
| Backend command wall | 2030.232 s |
| Deterministic pipeline wall | 7.081 s |
| End-to-end full-arm wall | 2829.456 s |

Step 0087's reused hierarchy cost remains 415 calls, 12,050,384 input tokens,
231,886 output tokens, 116,909 reasoning-output tokens, 8,689.405 seconds
summed request time, 2,215.858 seconds union active request time, and 11.516
seconds downstream pipeline wall.

## Scope and next paper decision

```text
run status: valid
tested hypothesis: inconclusive
research value: decisive mechanism ablation
paper impact: additional RQ3 evidence and hierarchy-mechanism boundary
next paper decision: Do not claim that variable depth explains the adopted result on both registered metrics.
```

This complete same-model ablation measures leaf-occurrence partition and exact
boundary fidelity on CodeTraceBench. It does not validate nested topology,
literal name accuracy, cross-run name equivalence, user utility, or other
task/agent families. It changes neither the fixed RQs nor the thesis,
“Agent observability needs profiling, not only debugging.”
