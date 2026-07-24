# Full Run Report

**Execution status:** VALID COMPLETE — independent result review PASS

## Complete population

The approved full command consumed:

- 1,000 AgentProcessBench trajectories and 8,509 operations;
- 536 HINTBench trajectories and 12,877 operations;
- 220 TraceElephant trajectories and 5,960 operations;
- 1,756 trajectories and 27,346 operations in total.

All 1,234 target-bearing trajectories entered standard AP/MAP scoring. The 522
zero-positive trajectories were loaded and counted for population coverage but
excluded from MAP because AP is undefined without a relevant item.

## Standard MAP

| Workload | Local+AgentProf | Local+Raw+Evidence | Local only | AgentProf only |
|---|---:|---:|---:|---:|
| AgentProcessBench | .8943 | .8931 | .8632 | .7906 |
| HINTBench | .5175 | .5180 | .4106 | .4324 |
| TraceElephant | .3255 | .3239 | .2087 | .2593 |

The AgentProf-only column reproduces Step 0071 exactly, including zero maximum
per-query absolute difference.

## Paired candidate-minus-baseline differences

| Workload | Baseline | Difference | 95% interval |
|---|---|---:|---:|
| AgentProcessBench | local only | +.0311 | [+.0237, +.0393] |
| AgentProcessBench | local + raw + evidence | +.0012 | [-.0003, +.0029] |
| HINTBench | local only | +.1069 | [+.0934, +.1204] |
| HINTBench | local + raw + evidence | -.0005 | [-.0116, +.0103] |
| TraceElephant | local only | +.1168 | [+.0876, +.1479] |
| TraceElephant | local + raw + evidence | +.0016 | [-.0247, +.0280] |

Each interval uses 10,000 paired resamples with the approved workload-specific
strata and clusters. The deterministic seeds are derived from base seed
`20260723`: AgentProcessBench uses `20260723/20260724`, HINTBench uses
`20260823/20260824`, and TraceElephant uses `20260923/20260924` for
local-only/raw-evidence comparisons, respectively.

## Immediate scientific reading

The candidate gives a clear, positive improvement over the local diagnostic
signal alone on all three complete workloads. It does not establish superiority
over the information-matched raw-action plus source-evidence baseline: all
three paired intervals include zero, and HINTBench has a negligible negative
point difference.

Thus the experiment supports the practical claim that the current
Agent+Evidence profile complements a local diagnostic signal. It does not by
itself prove that the semantic-operation prefix is better than a raw-action
prefix when both retain the same tool/outcome evidence. The registered strong
hypothesis is only partially supported.

## Runtime and artifacts

The full Python run completed in 5.46 seconds with scikit-learn 1.4.1.post1.
Raw outputs are under:

`.agentsight/experiments/rq2-current-agent-local-first-v1/full/`
