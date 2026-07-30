# Automatic Agent Operation Segmentation — Result

- mode: preflight
- status: complete
- registered interpretation: **diagnostic-preflight**

## Standard metrics

| Method | B³ P | B³ R | B³ F1 | Boundary P | Boundary R | Boundary F1 |
|---|---:|---:|---:|---:|---:|---:|
| native_turn | 0.986054 | 0.215632 | 0.353877 | 0.132653 | 0.933702 | 0.232302 |
| native_tree | 0.982190 | 0.218624 | 0.357641 | 0.134584 | 0.911602 | 0.234542 |
| multires_recurrence | 0.780309 | 0.597559 | 0.676815 | 0.189189 | 0.425414 | 0.261905 |
| candidate | 0.791881 | 0.726822 | 0.757958 | 0.354037 | 0.629834 | 0.453280 |

## Registered comparison

Candidate minus multi-resolution recurrence paired task-cluster 95% interval: `[+0.038828, +0.119120]`.

## Interpretation boundary

Official flat stages score only the leaf partition induced by complete visible operation paths. Nested topology, semantic names, cross-session equivalence, and user utility require the separately predeclared aggregate pprof review.
