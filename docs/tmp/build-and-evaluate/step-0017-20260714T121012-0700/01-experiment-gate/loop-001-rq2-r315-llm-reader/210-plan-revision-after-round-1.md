# Plan Revision after Review Round 1

## Accepted Necessary Fixes

1. The plan now freezes the runner path, preflight/full output directories, exact collect and score commands, API model value, observed llama.cpp binary/configuration, and both server- and request-level reasoning-disable options.
2. The plan now states that any persistently invalid or missing cell makes the complete 18-cell experiment `INVALID`. It forbids dropping tasks, imputing responses, manual repair, or computing a paired verdict on a reduced matrix.

## Rejected Expansion

No multi-model run, decoding repetition, new benchmark, new dataset, extra baseline, hash binding, sealing, attestation, or additional infrastructure was added. The experiment remains one complete 18-call matrix over reused R315/R316 artifacts.

## Status

The revised plan is ready for serial review round 2. No implementation or experimental execution has started.
