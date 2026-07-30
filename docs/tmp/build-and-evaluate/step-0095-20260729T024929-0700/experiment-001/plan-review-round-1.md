# Independent plan review, round 1

Reviewer verdict: **AMEND**

The reviewer found the causal chain promising but required five amendments
before execution:

1. Make model-visible information matching auditable by reconstructing every
   pprof sample tuple from the flat condition and removing metadata not
   queryable in pprof.
2. Let the independent output reviewer rerun cited commands against randomized
   evidence-package snapshots; require both replicate-1 policies to be valid
   before the three-condition downstream comparison.
3. Randomize and hash analyst run order; define time to a valid answer,
   right-censor failures, and disallow a permissive wall/token tradeoff.
4. Register one success and one cost endpoint with simultaneous inference
   rather than an opportunistic OR across many outcomes.
5. Freeze the exact ToolSandbox commit, evaluator mapping, paths, commands,
   seed/order files, and complete episode manifest before execution.

All five amendments are accepted. The revised plan uses a lossless flat
sample-tuple decode as the RAW comparator, rather than exposing pair/task
metadata that may not be available through pprof.
