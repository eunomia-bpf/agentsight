# A0 fixed-input construction-cost supplement

Timestamp: 2026-07-22T16:05:00-07:00
Status: complete; independent result review PASS

## Scope

This supplement measures only release-mode AgentPProf construction after both
the normalized operation inputs and 5,901 automatic Agent marks are fixed. It
does not measure capture, source adaptation, Agent annotation, model calls, or
live-agent overhead. The independently reviewed Step 0005 four-workload and
union experiment remains the primary RQ4 scaling result.

Machine class: Intel Core Ultra 9 285K, 24 cores, Linux. Binary:
release `agentpprof 0.2.37`. Measurement tool: GNU `/usr/bin/time`; wall time is
reported as the three-run median and RSS as the largest observed per-run value,
matching the Step 0005 protocol.

## Exact commands

Operation width, repeated three times:

```bash
/usr/bin/time -f "operations rep=<1..3> elapsed_seconds=%e maxrss_kib=%M" \
  agentpprof/target/release/agentpprof \
  --operation-file .agentsight/experiments/codex-agent-full-v1/profile-inputs/operations-count.jsonl \
  --operation-mark-file .agentsight/experiments/codex-agent-full-v1/profile-inputs/operation-marks.json \
  --view operations --stack project,agent,operation \
  -o .agentsight/experiments/codex-agent-full-v1/cost/operations.pb.gz
```

Token width, repeated three times:

```bash
/usr/bin/time -f "tokens rep=<1..3> elapsed_seconds=%e maxrss_kib=%M" \
  agentpprof/target/release/agentpprof \
  --operation-file .agentsight/experiments/codex-agent-full-v1/profile-inputs/operations-tokens.jsonl \
  --operation-mark-file .agentsight/experiments/codex-agent-full-v1/profile-inputs/operation-marks.json \
  --view tokens --stack project,agent,operation \
  -o .agentsight/experiments/codex-agent-full-v1/cost/tokens.pb.gz
```

## Raw observations and result

| Width | Rep | Wall seconds | Peak RSS KiB |
|---|---:|---:|---:|
| operations | 1 | 0.62 | 313,960 |
| operations | 2 | 0.62 | 313,948 |
| operations | 3 | 0.62 | 314,032 |
| tokens | 1 | 0.63 | 313,864 |
| tokens | 2 | 0.65 | 314,060 |
| tokens | 3 | 0.64 | 314,140 |

| Width | Median wall | Approx. throughput | Largest peak RSS | Exact pprof mass |
|---|---:|---:|---:|---:|
| operations | 0.62 s | 33,655 operations/s | 314,032 KiB (306.67 MiB) | 20,866 |
| tokens | 0.64 s | 32,603 operations/s | 314,140 KiB (306.78 MiB) | 494,862,929 tokens |

Both outputs load in stock `go tool pprof`, contain semantic operation stacks,
and retain source drilldown labels. Automatic-subagent elapsed time and
provider/model usage are unavailable and are not estimated.

## Decision

Given fixed operation inputs and fixed A0 marks, the tested profiles complete
parse, stack construction, folding, and pprof serialization in 0.62--0.64
seconds with at most 306.78 MiB observed RSS. This is current-A0 replay
confirmation, not a second scaling study and not evidence that automatic mark
construction itself is inexpensive.
