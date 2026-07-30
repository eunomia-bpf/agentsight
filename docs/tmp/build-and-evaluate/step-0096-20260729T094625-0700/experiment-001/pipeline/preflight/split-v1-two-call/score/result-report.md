# Automatic Agent Operation Segmentation — Result

- mode: preflight
- status: complete
- registered interpretation: **diagnostic-preflight**

## Standard metrics

| Method | B³ P | B³ R | B³ F1 | Boundary P | Boundary R | Boundary F1 |
|---|---:|---:|---:|---:|---:|---:|
| native_turn | 1.000000 | 0.133333 | 0.235294 | 0.118644 | 1.000000 | 0.212121 |
| native_tree | 1.000000 | 0.297854 | 0.458994 | 0.162791 | 1.000000 | 0.280000 |
| multires_recurrence | 0.930000 | 0.411616 | 0.570660 | 0.185185 | 0.714286 | 0.294118 |
| candidate | 0.909091 | 0.775000 | 0.836707 | 0.500000 | 0.857143 | 0.631579 |

## Registered comparison

Candidate minus multi-resolution recurrence paired task-cluster 95% interval: `[+0.266048, +0.266048]`.

## Interpretation boundary

Official flat stages score only the leaf partition induced by complete visible operation paths. Nested topology, semantic names, cross-session equivalence, and user utility require the separately predeclared aggregate pprof review.
