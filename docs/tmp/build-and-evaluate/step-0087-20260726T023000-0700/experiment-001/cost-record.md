# Cost record: direct multi-level annotation

## Configuration

- backend: `codex-cli 0.145.0`, model `gpt-5.6-sol`;
- one isolated call per trajectory, up to four workers;
- one format retry permitted per trajectory;
- interrupted valid outputs reused after schema validation.

## Complete backend-call accounting

| Measure | Value |
|---|---:|
| Planned / terminal trajectories | 405 / 405 |
| Valid / failed-after-retry trajectories | 404 / 1 |
| Total Codex calls | 414 |
| Format retries | 9 |
| Summed backend wall | 8676.599 s |
| Active backend wall across interrupted/resumed waves | 2203.052 s |
| Elapsed span including interruption | 2947.097 s |
| Input tokens | 12,022,984 |
| Cached input tokens | 5,992,192 |
| Output tokens | 231,572 |
| Reasoning output tokens | 116,763 |

The active-wall value is the union of recorded backend-call intervals, so it
does not count the interruption gap twice or pretend that summed parallel call
time is elapsed wall time. The recovered ordinal-5 attempt uses its raw-event
completion mtime minus the earliest preceding worker completion as its timing
basis; that basis is explicit in `annotation-run-records.jsonl`.

## Context

| Backend/run | Population | Inference/workflow wall evidence | Input / output tokens |
|---|---:|---:|---:|
| Direct multi-level (this run) | 405 terminal, 404 valid | 2203.052 s active backend wall | 12,022,984 / 231,572 |
| A2 historical waves | 405 | 3,261.89 s artifact-time envelope; model time unavailable | unavailable |
| Step 0086 automatic pass | 42 records | 7,740.107 s summed; 2,674.314 s reconstructed three-worker critical path | 15,231,328 / 311,097 |

The A2 envelope mixes inference, scheduling, idle time, and file writing and is
not directly comparable to backend request wall. This run's full pipeline cost
is unavailable because the fixed format policy left one trajectory uncovered,
so assembly, canonicalization, pprof replay, and scoring were correctly not run
on a partial population.
