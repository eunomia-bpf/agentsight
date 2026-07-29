# Automatic Agent Operation Segmentation — Result

- mode: full
- status: complete
- registered interpretation: **supported-pending-semantic-review**

## Standard metrics

| Method | B³ P | B³ R | B³ F1 | Boundary P | Boundary R | Boundary F1 |
|---|---:|---:|---:|---:|---:|---:|
| native_turn | 0.983154 | 0.221199 | 0.361145 | 0.141910 | 0.934330 | 0.246396 |
| native_tree | 0.974547 | 0.248903 | 0.396530 | 0.151090 | 0.915454 | 0.259373 |
| multires_recurrence | 0.782026 | 0.575029 | 0.662740 | 0.192945 | 0.425875 | 0.265571 |
| candidate | 0.698188 | 0.819017 | 0.753791 | 0.431509 | 0.511600 | 0.468154 |

## Registered comparison

Candidate minus multi-resolution recurrence paired task-cluster 95% interval: `[+0.076903, +0.105117]`.

## Interpretation boundary

Official flat stages score only the leaf partition induced by complete visible operation paths. Nested topology, semantic names, cross-session equivalence, and user utility require the separately predeclared aggregate pprof review.
