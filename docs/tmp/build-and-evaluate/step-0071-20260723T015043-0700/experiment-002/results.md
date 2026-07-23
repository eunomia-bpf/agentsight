# Experiment 002 result: current-binary RQ4 replay

Timestamp: 2026-07-23T02:34:00-07:00
Status: VALID / COMPLETE

## Binary provenance

- Git commit at build: `db465c32b312ce96f466a3975ede7d73525855fc`
- Version: `agentpprof 0.2.37`
- Release binary SHA-256:
  `c560754b3e1c0496b914ce49ee0e17a4d8004e7702556cccaa5814f7e6843d9b`
- Machine: 24-core Intel Core Ultra 9 285K, Linux 6.15.11

The release binary was built once before any timed run. Build time is excluded.
Agent inference, source adaptation, capture, and canonicalization are excluded.

## Complete public scaling matrix

All five inputs, two stack constructions, and three repetitions completed:
30/30 valid invocations. Every output is a standard `.pb.gz`, opens in stock
`go tool pprof`, and conserves exact operation mass.

| Workload | Ops | Semantic median (s) | Raw median (s) | Largest semantic RSS (MiB) |
|---|---:|---:|---:|---:|
| AgentRewardBench | 729 | 0.04 | 0.03 | 19.3 |
| SATraj-OS | 4,285 | 0.17 | 0.14 | 73.9 |
| OSWorld-Human | 6,010 | 0.24 | 0.21 | 109.1 |
| AgentNet | 16,741 | 0.70 | 0.58 | 279.3 |
| Union | 27,765 | 1.16 | 0.97 | 465.2 |

Both median curves are monotonic. The semantic descriptive fit has slope
0.041825 ms/operation and R² 0.999679; union throughput is 23,935
operations/s. Raw action has slope 0.034919 ms/operation and R² 0.999802.

On the union, semantic construction costs 0.19 s (19.6%) more time and 5.25
MiB (1.14%) more largest observed RSS than raw action. The complete
machine-readable result is
`.agentsight/experiments/rq4-cost-scaling-v2-current/result.json`.

## Latest A2 replay

The current binary replayed the latest canonical A2 marks three times for each
width: 6/6 valid invocations.

| Width | Wall observations (s) | Median (s) | Largest RSS (KiB / MiB) | Exact mass |
|---|---|---:|---:|---:|
| Operations | 0.80 / 0.79 / 0.79 | 0.79 | 314,692 / 307.32 | 20,866 |
| Tokens | 0.81 / 0.81 / 0.81 | 0.81 | 314,664 / 307.29 | 494,862,929 |

All six outputs contain 2,886 unique stacks, emit no warning, and load in stock
pprof. Canonical deterministic profiles are:

- `.agentsight/experiments/a2-canonical-v1/cost/operations.pb.gz`
  (`d8d0ad59fb43a4bef4c4f6fe4afaf058013ef435250db0325325a0a526517286`);
- `.agentsight/experiments/a2-canonical-v1/cost/tokens.pb.gz`
  (`c2cbba2ae474e4859952fa7aa4a0e53a9a8257938b487e2b12903068b75c936b`).

## Compatibility replays for RQ1 and RQ2

The same current build replayed the two fixed Git case widths. Both are
byte-identical to the existing paper figure inputs:

- operation profile:
  `325a9d1cabd0e6b8946722f90dfa1c5f1c5bd9a9313add78e46329dc645485e6`;
- token profile:
  `d23b7b68314da5477118154dc2370b4d2d3603740eae7ae7bde24007c341293a`.

It also reran the complete final RQ2 candidate on AgentProcessBench, HINTBench,
and TraceElephant. All three `per-query.jsonl` and `summary.json` files are
byte-identical to Step 0070. Current-binary MAP therefore remains
0.790615 / 0.432392 / 0.259313.

## Decision

Replace the stale RQ4 construction numbers with this current-binary matrix and
latest-A2 supplement. Preserve R160 only as one bounded predecessor cache
mechanism observation; it is not current-binary timing.
