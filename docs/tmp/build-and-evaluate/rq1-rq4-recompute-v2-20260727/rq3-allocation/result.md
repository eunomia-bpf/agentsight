# RQ3 Workspace Activity Allocation and Migration

Resolved means path-resolved, not confirmed effect. `observed` and `ok` statuses are retained and reported separately; duration, internal attention, importance, productivity, and causality are not measured.

## Source reconciliation and gates

| Project | Tool events (worktree) | Units ok/observed/unknown-ID | Calls event/lane | Module names/keys | Transitions | Returns | Gates A/T/R |
|---|---:|---:|---:|---:|---:|---:|---:|
| agentsight | 97586 (94052) | 38333 (32342/5991/0) | 31833/31837 | 27/39 | 31834 | 4641 | True/True/True |
| ActPlane | 66238 (65341) | 24968 (20502/4466/0) | 22942/22942 | 18/25 | 22940 | 2754 | True/True/True |
| bpf-developer-tutorial | 1664 (1663) | 841 (779/62/0) | 783/783 | 5/5 | 782 | 49 | True/True/True |
| eunomia.dev | 13876 (13393) | 3422 (2901/521/0) | 2947/2947 | 17/18 | 2945 | 711 | True/True/True |
| agentskill-observability-paper | 991 (990) | 438 (438/0/0) | 438/438 | 1/1 | 437 | 0 | True/False/False |
| academic-writing-skills | 948 (879) | 462 (457/5/0) | 450/450 | 4/4 | 449 | 30 | True/True/True |

The vendor-stratified rows, scope-only calls, failed calls without a resolved path, status counts, and action-row reconciliation are in `raw/rq5-coverage.csv`.

## Allocation status sensitivity

| Project | Mutation dominant class: all | Mutation dominant class: ok-only | Total-variation shift |
|---|---:|---:|---:|
| agentsight | paper/docs 64.1% | paper/docs 74.9% | 11.1% |
| ActPlane | paper/docs 72.6% | paper/docs 85.1% | 13.4% |
| bpf-developer-tutorial | paper/docs 89.0% | paper/docs 98.9% | 10.0% |
| eunomia.dev | paper/docs 60.7% | paper/docs 86.8% | 26.7% |
| agentskill-observability-paper | paper/docs 100.0% | paper/docs 100.0% | 0.0% |
| academic-writing-skills | paper/docs 96.1% | paper/docs 96.0% | 0.0% |

Exact action-weighted and Tool-call fractional allocations for every class/status/stratum are in `raw/rq5-summary.csv`; the difference between all path-resolved and ok-only activity is substantive and bounds interpretation of unknown-status events.

## Transitions and return gaps

| Project | Same artifact / module / cross (all) | Singleton-only n | Returns observed/censored | Intervening calls median/p90 |
|---|---:|---:|---:|---:|
| agentsight | 38.7% / 48.4% / 13.0% | 25643 | 4641/35 | 3.0/47.0 |
| ActPlane | 46.4% / 42.5% / 11.1% | 21100 | 2754/23 | 4.0/46.0 |
| bpf-developer-tutorial | 25.6% / 68.0% / 6.4% | 749 | 49/4 | 2.0/62.0 |
| eunomia.dev | 35.0% / 41.8% / 23.2% | 2520 | 711/16 | 3.0/37.0 |
| agentskill-observability-paper | 82.6% / 17.4% / 0.0% | 437 | 0/0 | N/A (coverage only) |
| academic-writing-skills | 35.9% / 56.8% / 7.3% | 434 | 30/3 | 2.0/56.0 |

Module-level access/mutation/session/time rows: 92. Cumulative leader-change rows: 47. Both are exported for exact inspection; no force-layout coordinate, entropy, cooling, internal-attention, or importance claim is made.
