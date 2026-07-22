# RQ2 Plan Review — Round 2

**Reviewed:** 2026-07-22  
**Verdict:** **BLOCK**

Round 1's scientific construct defects are substantially repaired. Cycles are
now worktree-local; the measure is correctly named inter-success mutation
accumulation; co-observed validation-command mutations are conservatively
separated; canonical worktree action ranks and local censoring are defined; the
known 3/6 gate is treated as a supporting within-case/coverage study; and F5's
labels and non-pooling rule are honest.

Three smaller but execution-critical gaps remain.

## Required repairs

1. **Add the frozen trajectory table required by Panel A.** The two declared
   outputs, `rq2-cycles.csv` and `rq2-coverage.csv`, do not contain the
   event-level action ranks needed to draw exact cumulative-mutation curves and
   validation markers. Add `raw/rq2-trajectory.csv` (or explicitly define an
   equivalent long-form table) with at least project, worktree ID, event ID,
   action rank, timestamp, session ID, validation status, per-event confirmed
   mutation-row count, co-observed mutation-row count, and cumulative mutation
   count. The plotting script must consume this frozen table rather than reopen
   RQ1 JSON independently. Otherwise F5 Panel A is not reproducible from the
   preregistered derived outputs.

2. **Close the compressed-versus-uncompressed freeze hole and state a real
   extraction command.** The plan pins hashes for `.json.gz` files but the raw
   directory also contains unhashed `.json` files. Checking the compressed
   hashes while analyzing an independently mutable uncompressed file does not
   enforce the source freeze. Require the analyzer to read the six verified
   `.json.gz` streams directly (or regenerate byte-identical JSON from them),
   and give the exact planned extraction command and analyzer path. The current
   plan names only the plotting script and says an exact command will be
   recorded later; that is insufficient for real preflight and completion
   checking.

3. **Resolve the artifact-type scope explicitly.** The first plan included
   artifact/module mix, and the canonical `docs/evaluation.md` RQ2 still asks
   for validation dynamics by artifact type. The repair silently drops that
   measurement. Either freeze the ordered path classifier before execution,
   or state that this supporting experiment does not answer the artifact-type
   slice and therefore cannot by itself close RQ2. Do not add a post-hoc
   classifier after seeing cycle results.

## Non-blocking precision

Use the literal legend label `status=observed (outcome unknown)` rather than
silently renaming the native value to a new status. This preserves the adapter
field while explaining its interpretation.

Once the three items above are fixed, the plan is ready for real preflight; no
additional baseline, workload, or event abstraction is needed.
