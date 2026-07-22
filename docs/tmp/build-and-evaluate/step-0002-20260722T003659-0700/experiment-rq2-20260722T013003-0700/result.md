# RQ2 Recognized-Validation Dynamics

Supporting coverage and within-case evidence only; 3/6 projects expose a recognized successful validation.

| Project | Attributed actions | Success/fail/observed | Co-observed mutation rows | Complete worktree-local intervals |
|---|---:|---:|---:|---:|
| agentsight | 96670 | 2065/331/110 | 0 | 2063 |
| ActPlane | 65473 | 1493/201/77 | 44 | 1491 |
| bpf-developer-tutorial | 1865 | 0/0/0 | 0 | 0 |
| eunomia.dev | 10193 | 6/0/87 | 0 | 5 |
| agentskill-observability-paper | 991 | 0/0/0 | 0 | 0 |
| academic-writing-skills | 658 | 0/0/0 | 0 | 0 |

| Project/worktree | Complete intervals | Zero-mutation | Median | P90 | Maximum |
|---|---:|---:|---:|---:|---:|
| ActPlane/3dae89cd06ae | 1491 | 89.1% | 0 | 1 | 1144 |
| agentsight/b5bc34dabe6a | 311 | 25.1% | 2 | 26 | 800 |
| agentsight/e58fce112c6e | 1752 | 86.9% | 0 | 1 | 95 |
| eunomia.dev/30e8a01e495d | 5 | 60.0% | 0 | 32 | 32 |

Most complete intervals contain no confirmed mutation row, while rare intervals contain hundreds; this is cadence/adapter evidence, not proof of redundant testing or missing coverage.

Artifact-type stratification is deferred to RQ5; this experiment does not close canonical RQ2.
