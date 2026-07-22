# RQ1 Real-Run Summary

Generated deterministically from source-linked native-session rows.

| Project | Attributed/all sessions | Attributed/all actions | Mutations | Creates kept | Reuse | Validation before supersession |
|---|---:|---:|---:|---:|---:|---:|
| agentsight | 1139/1363 | 96670/126476 | 6482 | 939/983 | 5558/6118 | 2077/6118 |
| ActPlane | 524/524 | 65473/65699 | 5770 | 3/50 | 5476/5630 | 873/5630 |
| bpf-developer-tutorial | 58/58 | 1865/1865 | 283 | N/A | 264/282 | N/A (coverage) |
| eunomia.dev | 48/48 | 10193/10560 | 170 | 4/10 | 141/157 | 32/157 |
| agentskill-observability-paper | 36/36 | 991/991 | 196 | N/A | 176/196 | N/A (coverage) |
| academic-writing-skills | 20/20 | 658/658 | 251 | N/A | 239/248 | N/A (coverage) |

- Longitudinal-qualified projects: 6/6
- Persistence-qualified projects: 3/6
- Validation-qualified projects: 3/6
- Coverage rows: 6
- Existing-file write content durability: unknown by design.
- Recognized validation: adapter-derived `effect=test,status=ok` only.
- Persistence is coverage-only: fewer than four cases have an eligible confirmed create.
- Validation is coverage-only: fewer than four cases expose recognized successful validation.
