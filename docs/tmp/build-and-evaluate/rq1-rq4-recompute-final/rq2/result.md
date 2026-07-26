# RQ2 Recognized-Validation Dynamics

Supporting coverage and within-case evidence only; 6/6 projects expose a recognized successful validation.

| Project | Attributed actions | Success/fail/observed | Co-observed mutation rows | Complete worktree-local intervals |
|---|---:|---:|---:|---:|
| agentsight | 94031 | 3288/373/202 | 7 | 3285 |
| ActPlane | 65334 | 2576/277/159 | 48 | 2574 |
| bpf-developer-tutorial | 1661 | 22/0/0 | 0 | 21 |
| eunomia.dev | 13393 | 52/3/95 | 0 | 51 |
| agentskill-observability-paper | 990 | 1/3/0 | 0 | 0 |
| academic-writing-skills | 879 | 9/0/0 | 7 | 8 |

| Project/worktree | Complete intervals | Zero-mutation | Median | P90 | Maximum |
|---|---:|---:|---:|---:|---:|
| ActPlane/3dae89cd06ae | 2574 | 84.4% | 0 | 1 | 817 |
| academic-writing-skills/4725c74bf420 | 8 | 62.5% | 0 | 10 | 140 |
| agentsight/b5bc34dabe6a | 659 | 29.3% | 2 | 17 | 291 |
| agentsight/e58fce112c6e | 2623 | 86.1% | 0 | 1 | 95 |
| agentsight/f2407a7d66d5 | 3 | 66.7% | 0 | 1 | 1 |
| bpf-developer-tutorial/a192f642f3ee | 21 | 47.6% | 2 | 43 | 69 |
| eunomia.dev/30e8a01e495d | 51 | 56.9% | 0 | 21 | 361 |

Most complete intervals contain no confirmed mutation row, while rare intervals contain hundreds; this is cadence/adapter evidence, not proof of redundant testing or missing coverage.

Artifact-type stratification is deferred to RQ5; this experiment does not close canonical RQ2.
