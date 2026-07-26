# Cost record: direct multi-level annotation

## Configuration

- backend: `codex-cli 0.145.0`, model `gpt-5.6-sol`;
- one isolated call per trajectory, up to four workers;
- one ordinary format retry per trajectory;
- one additional Amendment-2 backend attempt authorized only for ordinal 53;
- interrupted valid outputs reused after schema validation.

## Complete backend and pipeline accounting

| Measure | Value |
|---|---:|
| Planned / valid trajectories | 405 / 405 |
| Total Codex calls | 415 |
| Calls after each trajectory's first | 10 |
| Amendment-2 additional attempts | 1 |
| Summed backend wall | 8689.405 s |
| Active backend wall across interrupted/resumed waves | 2215.858 s |
| Full deterministic downstream pipeline wall | 11.516 s |
| Input tokens | 12,050,384 |
| Cached input tokens | 6,008,320 |
| Output tokens | 231,886 |
| Reasoning output tokens | 116,909 |

Ordinal 53 completed through `authorized_backend_attempt_3`. The deterministic session-ID
normalization fallback was
`not used`.
The active-wall value is the union of recorded backend-call intervals and does
not count the interruption gap as inference time.

## Context

| Backend/run | Population | Inference/workflow wall evidence | Input / output tokens |
|---|---:|---:|---:|
| Direct multi-level (this run) | 405 | 2215.858 s active backend wall | 12,050,384 / 231,886 |
| A2 historical waves | 405 | 3,261.89 s artifact-time envelope; model time unavailable | unavailable |
| Step 0086 automatic pass | 42 records | 7,740.107 s summed; 2,674.314 s reconstructed three-worker critical path | 15,231,328 / 311,097 |

The A2 envelope mixes inference, scheduling, idle time, and file writing and is
not directly comparable to backend request wall.
