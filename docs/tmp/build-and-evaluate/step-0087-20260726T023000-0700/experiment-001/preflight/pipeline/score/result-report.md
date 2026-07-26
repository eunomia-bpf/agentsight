# Automatic Agent Operation Segmentation — Result

- mode: preflight
- status: complete
- registered interpretation: **diagnostic-preflight**

## Standard metrics

| Method | B³ P | B³ R | B³ F1 | Boundary P | Boundary R | Boundary F1 |
|---|---:|---:|---:|---:|---:|---:|
| native_turn | 0.875000 | 0.829167 | 0.851467 | 0.333333 | 0.333333 | 0.333333 |
| native_tree | 1.000000 | 0.287500 | 0.446602 | 0.200000 | 1.000000 | 0.333333 |
| multires_recurrence | 0.880000 | 0.600000 | 0.713514 | 0.400000 | 0.666667 | 0.500000 |
| candidate | 0.652778 | 0.829167 | 0.730475 | 0.000000 | 0.000000 | 0.000000 |

## Registered comparison

Candidate minus multi-resolution recurrence paired task-cluster 95% interval: `[+0.016961, +0.016961]`.

## Interpretation boundary

Official flat stages score only the leaf partition induced by complete visible operation paths. Nested topology, semantic names, cross-session equivalence, and user utility require the separately predeclared aggregate pprof review.
