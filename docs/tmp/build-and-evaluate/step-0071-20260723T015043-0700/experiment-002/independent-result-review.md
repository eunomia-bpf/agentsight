# Independent result review: Experiment 002

Verdict: **PASS**
Role: supporting current RQ4 measurement; RQ1/RQ2 replays are dependency-only

The reviewer independently recomputed:

- 30/30 public scaling invocations;
- union semantic/raw median 1.16/0.97 s;
- union semantic maximum 476,320 KiB = 465.16 MiB;
- semantic slope 0.0418248 ms/operation, R² 0.999679, and 23,935
  operations/s;
- semantic overhead +0.19 s = 19.59% and +5,376 KiB = 5.25 MiB = 1.14%;
- six latest-A2 runs with operation median 0.79 s, token median 0.81 s,
  exact masses 20,866 and 494,862,929, 2,886 stacks, and no warnings;
- binary HEAD, version, and SHA-256 match the result report;
- both RQ1 pprof hashes equal the paper inputs;
- all three RQ2 per-query and summary files are byte-identical, with MAP
  0.790615/0.432392/0.259313.

No incomplete cell, dropped repetition, annotation latency, or stale-binary
number enters the current RQ4 result.
