# Results: frozen direct backend on OSWorld-Human

Run status: **VALID / COMPLETE**

Tested hypothesis: **CONTRADICTED**

## Complete population

The run covers all 287 eligible sessions, 3,978 operations, 3,691 adjacent pairs, and 2,042 human groups.

## Metrics

| Method | Boundary P | Boundary R | Boundary F1 | B³ P | B³ R | B³ F1 |
|---|---:|---:|---:|---:|---:|---:|
| Direct multi-level | 0.539007 | 0.086610 | 0.149239 | 0.293428 | 0.947327 | 0.448069 |
| Supervised OOF | 0.699796 | 0.782336 | 0.738768 | 0.835863 | 0.797096 | 0.816019 |
| Reference-calibrated | 0.609646 | 0.921937 | 0.733953 | 0.917000 | 0.711190 | 0.801087 |
| Label-free recurrence | 0.591811 | 0.798860 | 0.679922 | 0.855872 | 0.726966 | 0.786170 |
| Always-boundary | 0.475481 | 1.000000 | 0.644510 | 1.000000 | 0.513323 | 0.678405 |

## Paired session-cluster intervals

| Direct minus baseline | B³ F1 point | B³ 95% interval | Boundary F1 point | Boundary 95% interval |
|---|---:|---:|---:|---:|
| Supervised OOF | -0.367950 | [-0.444016, -0.279954] | -0.589529 | [-0.641014, -0.532755] |
| Reference-calibrated | -0.353018 | [-0.442962, -0.250125] | -0.584714 | [-0.647641, -0.510328] |
| Label-free recurrence | -0.338100 | [-0.428975, -0.234028] | -0.530683 | [-0.603923, -0.443659] |
| Always-boundary | -0.230336 | [-0.321986, -0.139840] | -0.495271 | [-0.574675, -0.410903] |

## Hypothesis interpretation

The frozen direct-backend competitiveness hypothesis is **CONTRADICTED**:
both F1 measures are below all four requested comparators, and every paired
95% interval is wholly negative.

The direct backend reaches B³ F1 `0.448069` and boundary F1 `0.149239`. The strongest stored B³ row is Supervised OOF at `0.816019`; the strongest stored boundary row is Supervised OOF at `0.738768`.

The pilot margin authorized this complete run but is not silently promoted into a new full-run equivalence definition. The comparison above therefore reports the direct effects and uncertainty against every requested stored row; any use of “competitive” should retain both B³ and exact-boundary results.

## Validity and conservation

- All 287 source packets expose only the fixed nine visible fields and contain no human group labels.
- Exactly 3,978 operation assignments and 3,691 adjacent decisions are conserved.
- Backend failures after the single permitted format retry: 0.
- Direct marks: 569; path depths: `{"1": 156, "2": 355, "3": 54, "4": 4}`.

This is independent-population RQ3 evidence for the frozen direct instruction. It does not change the fixed RQ, thesis, or paper story.
