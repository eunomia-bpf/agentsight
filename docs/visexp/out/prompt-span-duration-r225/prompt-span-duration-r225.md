# R225 Prompt-Span Duration Baseline

Status: `done/prompt-span-duration-baseline`

This artifact reconstructs prompt-level span durations from R170 timestamps. It is a duration-weighted baseline over generated AgentFlame artifacts only; it does not provide true tool/LLM start-end spans or user-study outcomes. The duration is a prompt wall-clock interval and may include idle/user-wait time.

## Summary

- Prompt spans reconstructed: 2858
- Nonzero prompt spans: 2854
- Sessions with prompt spans: 324/325
- Total prompt duration: 859.019 h
- Covered effect observations compared: 183714/183714 (100.0%)
- Expanded effects match folded prompt totals: True
- Top-10 duration/effect overlap: 7/10
- Top-20 duration/effect overlap: 12/20
- Prompt-tag Spearman rank correlation: 0.623

## Top Duration Tags

| Rank | Prompt tag | Duration h | Duration % | Effect rank | Effect % |
|---:|---|---:|---:|---:|---:|
| 1 | `refactor` | 320.965 | 37.364 | 1 | 39.824 |
| 2 | `review` | 97.892 | 11.396 | 2 | 18.108 |
| 3 | `test` | 47.584 | 5.539 | 5 | 4.361 |
| 4 | `design` | 47.498 | 5.529 | 3 | 8.549 |
| 5 | `analyze` | 45.651 | 5.314 | 4 | 6.236 |
| 6 | `docs` | 44.337 | 5.161 | 8 | 1.893 |
| 7 | `research` | 24.702 | 2.876 | 6 | 2.578 |
| 8 | `network` | 24.373 | 2.837 | 93 | 0.04 |
| 9 | `compare` | 20.675 | 2.407 | 20 | 0.291 |
| 10 | `source` | 16.624 | 1.935 | 259 | 0.001 |

## Top Effect Tags

| Rank | Prompt tag | Effect weight | Effect % | Duration rank | Duration % |
|---:|---|---:|---:|---:|---:|
| 1 | `refactor` | 73162 | 39.824 | 1 | 37.364 |
| 2 | `review` | 33267 | 18.108 | 2 | 11.396 |
| 3 | `design` | 15705 | 8.549 | 4 | 5.529 |
| 4 | `analyze` | 11457 | 6.236 | 5 | 5.314 |
| 5 | `test` | 8012 | 4.361 | 3 | 5.539 |
| 6 | `research` | 4736 | 2.578 | 7 | 2.876 |
| 7 | `benchmark` | 4033 | 2.195 | 34 | 0.198 |
| 8 | `docs` | 3477 | 1.893 | 6 | 5.161 |
| 9 | `debug` | 1587 | 0.864 | 20 | 0.548 |
| 10 | `explain` | 1463 | 0.796 | 22 | 0.413 |

## Largest Share Disagreements

| Prompt tag | Duration % | Effect % | Delta pp | Duration rank | Effect rank |
|---|---:|---:|---:|---:|---:|
| `review` | 11.396 | 18.108 | 6.712 | 2 | 2 |
| `docs` | 5.161 | 1.893 | 3.268 | 6 | 8 |
| `design` | 5.529 | 8.549 | 3.02 | 4 | 3 |
| `network` | 2.837 | 0.04 | 2.797 | 8 | 93 |
| `refactor` | 37.364 | 39.824 | 2.46 | 1 | 1 |
| `compare` | 2.407 | 0.291 | 2.116 | 9 | 20 |
| `benchmark` | 0.198 | 2.195 | 1.997 | 34 | 7 |
| `source` | 1.935 | 0.001 | 1.934 | 10 | 259 |
| `test` | 5.539 | 4.361 | 1.178 | 3 | 5 |
| `question` | 1.163 | 0.045 | 1.118 | 14 | 85 |

## Claim Boundary

- Supports: a concrete prompt-span duration baseline and evidence that duration-weighted views differ from system-effect-count profiles.
- Does not support: C5 user utility, C6 tag adequacy, active runtime, true tool/LLM duration spans, or replacement of effect-count profiling.
- Next gate: collect R142 participant responses using this baseline only after updating the preregistered packet.
