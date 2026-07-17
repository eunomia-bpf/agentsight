# Step 0033 Independent Result Review

## Judgment

```text
run status: valid
tested hypothesis: supported
research value: decisive
paper impact: additional RQ evidence
next paper decision: use trajectory-level MAP as the common primary RQ2 localization metric, retain the existing Work curves as secondary inspection diagnostics, and preserve the atomic-control boundary
```

I independently reconstructed labels and fixed operation scores from the three
authoritative source roots before consulting the new summary and result report.
The reconstruction used scikit-learn's non-interpolated AP once per
target-bearing trajectory and the arithmetic mean of those AP values. A
separate threshold-level AP calculation agreed with scikit-learn to below
`1e-12`, including score ties; no operation ID, timestamp, or file order broke
ties.

## Completion And Primary Values

| Workload | Source trajectories / operations | MAP queries | AgentProf MAP | Raw-action MAP | Difference |
|---|---:|---:|---:|---:|---:|
| AgentProcessBench | 1,000 / 8,509 | 614 | 0.7889194040 | 0.7731699925 | +0.0157494115 |
| HINTBench | 536 / 12,877 | 400 | 0.4528515773 | 0.2814907821 | +0.1713607952 |
| TraceElephant | 220 / 5,960 | 220 | 0.2301683213 | 0.1212702780 | +0.1088980434 |

These values match
`.agentsight/experiments/rq2-standard-map-existing-trajectories-v1/full/summary.json`
and all 1,234 rows in `full/per-query.jsonl`. AgentProcess scores were
recomputed as family-scoped group means, as required by
`script/rq2_standard_localization_metrics.py:117-157`; this is important
because pooling group names across benchmark families would be a different
comparison.

The 386 zero-positive AgentProcess trajectories and 136 safe HINT trajectories
are correctly excluded from query MAP and retained as nonrelevant operations
in pooled AP. The independently recomputed AgentProf/raw pooled AP pairs are
0.691779/0.668811, 0.249714/0.180484, and 0.077569/0.052791, respectively.

HINT contains 938 official targets, of which 935 map to displayed operations.
Counting the three absent targets as unretrieved changes AgentProf/raw MAP to
0.4521209751/0.2808273165, exactly matching the registered sensitivity and not
changing the sign. The stored selected leaf scores, independently reconstructed
raw/session Wilson scores, and flat-identity relation are internally
consistent.

## Uncertainty And Source Separation

The registered task-cluster bootstrap was independently repeated with seed
`20260716`, 10,000 draws per workload, and nearest-rank endpoints. It includes
all 200 AgentProcess tasks in four family strata, 400 target-bearing HINT
records in 44 environment strata, and 220 TraceElephant traces in five cell
strata. The results exactly match `full/bootstrap-deltas.json`:

| Workload | Paired 95% interval | Nonpositive draws |
|---|---:|---:|
| AgentProcessBench | [0.0047271790, 0.0270813375] | 21 |
| HINTBench | [0.1545337996, 0.1887394465] | 0 |
| TraceElephant | [0.0780095347, 0.1413016307] | 0 |

The fixed score paths are target-blind with respect to their scorer labels:
AgentProcess constructs profiles before loading human labels
(`script/agentprocessbench_profile_eval.py:1194-1202`); HINT constructs the
test profile before loading test targets
(`script/hintbench_profile_localization_eval.py:2390-2405`); and TraceElephant
materializes the method index before its scorer subprocess opens official
targets (`script/traceelephant_profile_localization_eval.py:1811-1820` and
`:1657-1699`). The raw-action baseline uses the same operations and underlying
fixed evidence signal, so its mechanism engaged and the matched comparison is
fair.

The controls also set the correct interpretation boundary. Atomic ranking is
stronger on AgentProcessBench (0.863171 MAP), while AgentProf is stronger than
the atomic control on HINTBench and TraceElephant. Thus the result supports the
registered AgentProf-over-raw ranking hypothesis; it does not support universal
dominance over atomic scores or a claim about debugging time.

## Ranked Result-Invalidating Must-Fixes

None.

result status: PASS
