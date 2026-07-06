# R328 Deterministic Profile Output

This probe reruns the same tracked R300/R324/R326 profile specs as R327, but passes `--deterministic-output` to the Rust profiler.

- Specs: 76
- Repetitions per spec: 2
- Profiler invocations: 152
- Semantic deterministic specs: 76/76
- Raw-byte deterministic specs: 76/76
- Median runtime: 1601.0827 ms
- P95 runtime: 2767.1653 ms

## By Experiment

| Experiment | Specs | Median runtime (ms) | P95 runtime (ms) | Median unique stacks | Median output bytes |
|---|---:|---:|---:|---:|---:|
| r300_views | 4 | 3505.2170 | 4339.5190 | 631.0 | 109299.0 |
| r324_rank_features | 12 | 1578.0484 | 2726.1491 | 41.0 | 36339.0 |
| r326_rank_feature_robustness | 60 | 1566.8592 | 2716.5349 | 41.0 | 36339.0 |

## Claim Scope

Deterministic output mode makes tracked operation-profile specs byte-stable across repeated offline profiler runs.

- This is not live eBPF capture overhead.
- This is not a human or agent analyst productivity study.
- This does not download, sync, or create a dataset.
- This does not claim complete trace-platform ecosystem compatibility.
- This does not claim a performance improvement over R327.
- This is not a detector or boundary-discovery benchmark.
