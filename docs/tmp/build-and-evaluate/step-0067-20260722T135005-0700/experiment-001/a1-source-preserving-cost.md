# A1 source-preserving construction cost

Timestamp: 2026-07-22T16:59:21-07:00

## Question

Does retaining `source_kind` and the LLM/tool-call leaf below the unchanged
automatic semantic path make standard pprof construction impractical?

## Inputs and command

The measurement replays the complete A1 inputs used for RQ2: 8,509
AgentProcessBench operations, 12,877 HINTBench operations, and 5,960
TraceElephant operations. Each exact command is recorded in that workload's
`source_preserving_agent-command.json`. The release AgentPProf binary was run
three times per workload. Python `perf_counter` measures the complete child
process; `/usr/bin/time` independently reports elapsed seconds and peak RSS.
Every run overwrites the same standard `.pb.gz`; no renderer or frontend enters
the measurement.

## Complete observations

| Workload | Rep | Python wall (s) | `/usr/bin/time` wall (s) | Peak RSS (KiB) | Operations / samples | Unique stacks |
|---|---:|---:|---:|---:|---:|---:|
| AgentProcessBench | 1 | 0.151020 | 0.15 | 65,336 | 8,509 / 8,509 | 317 |
| AgentProcessBench | 2 | 0.148922 | 0.14 | 65,252 | 8,509 / 8,509 | 317 |
| AgentProcessBench | 3 | 0.149732 | 0.14 | 65,328 | 8,509 / 8,509 | 317 |
| HINTBench | 1 | 0.272290 | 0.26 | 109,848 | 12,877 / 12,877 | 2,872 |
| HINTBench | 2 | 0.260449 | 0.25 | 109,664 | 12,877 / 12,877 | 2,872 |
| HINTBench | 3 | 0.256458 | 0.25 | 109,760 | 12,877 / 12,877 | 2,872 |
| TraceElephant | 1 | 0.129112 | 0.12 | 61,952 | 5,960 / 5,960 | 674 |
| TraceElephant | 2 | 0.129380 | 0.12 | 62,200 | 5,960 / 5,960 | 674 |
| TraceElephant | 3 | 0.129349 | 0.12 | 61,960 | 5,960 / 5,960 | 674 |

Median complete-process wall time is 0.149732 seconds for AgentProcessBench,
0.260449 seconds for HINTBench, and 0.129349 seconds for TraceElephant. Largest
observed peak RSS is respectively 65,336, 109,848, and 62,200 KiB. All nine
runs preserve exact operation/sample mass and a deterministic unique-stack
count.

## Interpretation

The A1 projection adds two visible stack frames but does not alter annotation
or run another model. Its measured profile-construction cost is small on all
three complete inputs. This supplements, rather than replaces, the paper's
existing four-workload and union RQ4 scaling experiment. It measures only
fixed-input CLI construction; automatic annotation, capture, and provider-side
model cost remain outside this number.
