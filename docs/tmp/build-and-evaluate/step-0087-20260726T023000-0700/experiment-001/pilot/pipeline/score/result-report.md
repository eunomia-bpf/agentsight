# Automatic Agent Operation Segmentation — Result

- mode: preflight
- status: complete
- registered interpretation: **diagnostic-preflight**

## Standard metrics

| Method | B³ P | B³ R | B³ F1 | Boundary P | Boundary R | Boundary F1 |
|---|---:|---:|---:|---:|---:|---:|
| native_turn | 1.000000 | 0.186099 | 0.313800 | 0.161017 | 1.000000 | 0.277372 |
| native_tree | 0.978027 | 0.266431 | 0.418779 | 0.179775 | 0.918660 | 0.300705 |
| multires_recurrence | 0.770809 | 0.601379 | 0.675634 | 0.207595 | 0.392344 | 0.271523 |
| candidate | 0.917259 | 0.637536 | 0.752235 | 0.377483 | 0.818182 | 0.516616 |

## Registered comparison

Candidate minus multi-resolution recurrence paired task-cluster 95% interval: `[+0.037371, +0.114878]`.

## Interpretation boundary

Official flat stages score only the leaf partition induced by complete visible operation paths. Nested topology, semantic names, cross-session equivalence, and user utility require the separately predeclared aggregate pprof review.
