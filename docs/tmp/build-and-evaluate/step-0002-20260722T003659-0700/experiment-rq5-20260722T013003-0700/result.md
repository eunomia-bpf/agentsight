# RQ5 Workspace Activity Allocation and Migration

Resolved means path-resolved, not confirmed effect. `observed` and `ok` statuses are retained and reported separately; duration, internal attention, importance, productivity, and causality are not measured.

## Source reconciliation and gates

| Project | Tool events (worktree) | Units ok/observed/unknown-ID | Calls event/lane | Module names/keys | Transitions | Returns | Gates A/T/R |
|---|---:|---:|---:|---:|---:|---:|---:|
| agentsight | 126476 (96982) | 57652 (51352/6300/0) | 40377/40381 | 41/54 | 40378 | 6663 | True/True/True |
| ActPlane | 65699 (65473) | 32388 (27962/4426/0) | 26805/26805 | 40/47 | 26803 | 3699 | True/True/True |
| bpf-developer-tutorial | 1865 (1865) | 1148 (1086/62/0) | 976/976 | 6/9 | 973 | 60 | True/True/True |
| eunomia.dev | 10560 (10193) | 2906 (2388/518/0) | 2140/2140 | 14/15 | 2138 | 498 | True/True/True |
| agentskill-observability-paper | 991 (991) | 463 (463/0/0) | 463/463 | 2/2 | 462 | 3 | True/True/False |
| academic-writing-skills | 658 (658) | 554 (549/5/0) | 485/485 | 6/6 | 484 | 36 | True/True/True |

The vendor-stratified rows, scope-only calls, failed calls without a resolved path, status counts, and action-row reconciliation are in `raw/rq5-coverage.csv`.

## Allocation status sensitivity

| Project | Mutation dominant class: all | Mutation dominant class: ok-only | Total-variation shift |
|---|---:|---:|---:|
| agentsight | paper/docs 64.1% | paper/docs 75.3% | 11.4% |
| ActPlane | paper/docs 72.7% | paper/docs 85.4% | 13.4% |
| bpf-developer-tutorial | paper/docs 89.0% | paper/docs 98.9% | 10.0% |
| eunomia.dev | paper/docs 39.2% | paper/docs 88.2% | 49.7% |
| agentskill-observability-paper | paper/docs 100.0% | paper/docs 100.0% | 0.0% |
| academic-writing-skills | paper/docs 97.2% | paper/docs 97.2% | 0.0% |

Exact action-weighted and Tool-call fractional allocations for every class/status/stratum are in `raw/rq5-summary.csv`; the difference between all path-resolved and ok-only activity is substantive and bounds interpretation of unknown-status events.

## Transitions and return gaps

| Project | Same artifact / module / cross (all) | Singleton-only n | Returns observed/censored | Return calls median/p90 |
|---|---:|---:|---:|---:|
| agentsight | 42.5% / 44.2% / 13.3% | 28379 | 6663/51 | 4.0/39.0 |
| ActPlane | 49.3% / 39.9% / 10.8% | 22218 | 3699/45 | 5.0/43.0 |
| bpf-developer-tutorial | 29.3% / 64.6% / 6.1% | 844 | 60/6 | 5.0/63.0 |
| eunomia.dev | 30.6% / 48.6% / 20.8% | 1493 | 498/13 | 4.0/38.0 |
| agentskill-observability-paper | 81.6% / 17.5% / 0.9% | 462 | 3/1 | N/A (coverage only) |
| academic-writing-skills | 37.6% / 54.5% / 7.9% | 428 | 36/5 | 3.0/61.0 |

Module-level access/mutation/session/time rows: 133. Cumulative leader-change rows: 50. Both are exported for exact inspection; no force-layout coordinate, entropy, cooling, internal-attention, or importance claim is made.
