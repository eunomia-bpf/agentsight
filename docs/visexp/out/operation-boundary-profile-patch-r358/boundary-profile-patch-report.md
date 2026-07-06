# R358 Boundary-Derived Profile Patch Audit

R358 tests the R354 OSWorld-Human rejection directly: phase/action rank features are not enough, so this run uses the R297 learned boundary fields as ordinary operation fields and folds them through Rust profile specs.

## Result

- Held-out operations / positives: 1132 / 243.
- Learned-boundary AP: 0.2583; semantic-width AP: 0.2402; visible-rank AP: 0.2253.
- AP delta vs semantic width: 0.0181.
- AP delta vs visible rank patch: 0.0330.
- Learned-boundary groups: 74 vs semantic 108 and fixed-session 96.
- Top-5 recall delta vs semantic: 0.1111.
- Counterpoint: Boundary-derived fields improve AP and reduce groups, but they increase top-5 operation work and first-positive work on this held-out subset.

## Policy Metrics

| Policy | Hidden | Groups | AP | Top-5 work | Top-5 recall | First-positive work |
|---|---:|---:|---:|---:|---:|---:|
| flat_width | False | 1 | 0.2147 | 1.0000 | 1.0000 | 1.0 |
| fixed_session_width | False | 96 | 0.2392 | 0.4055 | 0.4403 | 0.2253 |
| semantic_width | False | 108 | 0.2402 | 0.5627 | 0.5844 | 0.1502 |
| semantic_visible_rank | False | 108 | 0.2253 | 0.4125 | 0.3704 | 0.1502 |
| learned_boundary_width | False | 74 | 0.2583 | 0.6440 | 0.6955 | 0.3083 |
| learned_boundary_rank | False | 74 | 0.2359 | 0.5115 | 0.4239 | 0.3083 |
| oracle_positive_rate_semantic | True | 108 | 0.5852 | 0.0053 | 0.0247 | 0.0018 |
| oracle_positive_rate_learned_stack | True | 74 | 0.5406 | 0.0062 | 0.0288 | 0.0018 |

Hidden labels are used only after Rust emits visible profile groups. The oracle policies are explicit upper bounds.
