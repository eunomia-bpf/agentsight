# Automatic Agent Operation Segmentation — Result

- mode: preflight
- status: complete
- registered interpretation: **diagnostic-preflight**

## Standard metrics

| Method | B³ P | B³ R | B³ F1 | Boundary P | Boundary R | Boundary F1 |
|---|---:|---:|---:|---:|---:|---:|
| native_turn | 0.985242 | 0.263996 | 0.416414 | 0.167033 | 0.926829 | 0.283054 |
| native_tree | 0.987532 | 0.223880 | 0.365010 | 0.148148 | 0.926829 | 0.255462 |
| multires_recurrence | 0.859949 | 0.491708 | 0.625667 | 0.211268 | 0.548780 | 0.305085 |
| candidate | 0.726243 | 0.737514 | 0.731835 | 0.368000 | 0.560976 | 0.444444 |

## Registered comparison

Candidate minus multi-resolution recurrence paired task-cluster 95% interval: `[+0.044864, +0.140582]`.

## Interpretation boundary

Official flat stages score only the leaf partition induced by complete visible operation paths. Nested topology, semantic names, cross-session equivalence, and user utility require the separately predeclared aggregate pprof review.
