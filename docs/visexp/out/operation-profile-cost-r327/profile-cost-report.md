# R327 Profile-Spec Cost and Reproducibility

This probe reruns existing tracked profile specs against existing tracked operation JSONL inputs. It does not download or sync datasets.

- Specs: 76
- Repetitions per spec: 2
- Profiler invocations: 152
- Deterministic specs: 76/76
- Raw-byte deterministic specs: 4/76 (JSON profiles include `generated_at`)
- Median per-spec runtime: 1581.3334 ms
- P95 per-spec runtime: 2719.3206 ms
- Max per-spec runtime: 4272.6763 ms
- Median output size: 37546.0 bytes
- Max unique stacks: 2012

## By Experiment

| Experiment | Specs | Median runtime (ms) | P95 runtime (ms) | Median unique stacks | Median output bytes |
|---|---:|---:|---:|---:|---:|
| r300_views | 4 | 3448.0200 | 4272.6763 | 631.0 | 109299.0 |
| r324_rank_features | 12 | 1538.8800 | 2691.5278 | 41.0 | 36339.0 |
| r326_rank_feature_robustness | 60 | 1541.8825 | 2640.3084 | 41.0 | 36339.0 |

## Claim Scope

R327 supports an offline reproducibility and profiler-cost claim for tracked operation-profile specs. It does not measure live eBPF capture overhead, human utility, or compatibility with full OpenTelemetry/Phoenix/LangSmith/Langfuse/Perfetto ecosystems.
The determinism gate hashes semantic profile content after excluding the JSON `generated_at` field; raw-byte hashes are reported separately.
