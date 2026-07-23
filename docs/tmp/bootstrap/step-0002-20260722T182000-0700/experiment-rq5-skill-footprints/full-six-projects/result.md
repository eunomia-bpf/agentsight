# RQ1 Real-Run Summary

Generated deterministically from source-linked native-session rows.

| Project | Attributed/all sessions | Attributed/all actions | Mutations | Creates kept | Reuse | Validation before supersession |
|---|---:|---:|---:|---:|---:|---:|
| agentsight | 1147/1371 | 98151/127957 | 6614 | 962/1005 | 5693/6252 | 2070/6252 |
| ActPlane | 524/524 | 65473/65699 | 5746 | 3/48 | 5471/5616 | 863/5616 |
| bpf-developer-tutorial | 63/63 | 1911/1911 | 293 | N/A | 271/292 | N/A (coverage) |
| eunomia.dev | 49/49 | 10268/10683 | 170 | 4/9 | 152/157 | 32/157 |
| agentskill-observability-paper | 36/36 | 991/991 | 196 | N/A | 176/196 | N/A (coverage) |
| academic-writing-skills | 20/20 | 658/658 | 251 | N/A | 241/248 | N/A (coverage) |

- Longitudinal-qualified projects: 6/6
- Persistence-qualified projects: 3/6
- Validation-qualified projects: 3/6
- Coverage rows: 6
- Existing-file write content durability: unknown by design.
- Recognized validation: adapter-derived `effect=test,status=ok` only.
- Persistence is coverage-only: fewer than four cases have an eligible confirmed create.
- Validation is coverage-only: fewer than four cases expose recognized successful validation.
