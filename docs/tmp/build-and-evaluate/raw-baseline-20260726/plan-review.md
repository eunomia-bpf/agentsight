# BLOCK

Two defects can invalidate the registered run:

1. **Invalid cells can be misreported as Trajectory superiority.** The protocol requires any invalid cell to make the comparison mixed/inconclusive ([protocol.md](/home/yunwei37/workspace/agentsight-agent-nebula-research/docs/tmp/build-and-evaluate/raw-baseline-20260726/protocol.md:189)). The scorer nevertheless converts invalid cells to zero-correct denominator rows and declares superiority whenever the bootstrap lower bound is positive, without an invalid-cell veto ([runner.py](/home/yunwei37/workspace/agentsight-agent-nebula-research/docs/tmp/build-and-evaluate/raw-baseline-20260726/runner.py:562)). Thus timeouts or transport failures could incorrectly become evidence for Trajectory.

2. **The checkpoint/resume boundary is not atomic.** The vendored model call first writes `scored.json` using the obsolete frozen answers ([rq7_measurement_frozen.py](/home/yunwei37/workspace/agentsight-agent-nebula-research/docs/tmp/build-and-evaluate/raw-baseline-20260726/vendor/rq7_measurement_frozen.py:2851)); the wrapper subsequently overwrites it with corrected-v4 scoring ([runner.py](/home/yunwei37/workspace/agentsight-agent-nebula-research/docs/tmp/build-and-evaluate/raw-baseline-20260726/runner.py:340)). An interruption between those writes leaves an old-scored checkpoint that resume accepts solely because the file exists ([runner.py](/home/yunwei37/workspace/agentsight-agent-nebula-research/docs/tmp/build-and-evaluate/raw-baseline-20260726/runner.py:364)). Failed preflights are likewise permanently skipped, so the registered allowance of up to three infrastructure-repair attempts is not executable.

## Optional notes

- The frozen corpus does contain exactly 6 projects, 72 files, 120 unique matching question IDs, and 20 questions per project.
- The 18-cell matrix, three repetitions, original 64-call/1 MiB/64 KiB/900-second budgets, post-call corrected-v4 join, filesystem boundary repair, and hierarchical fixed-corpus bootstrap otherwise match the requested protocol.
- Repaired Trajectory is correctly frozen at 102/120 overall and 60/60 B+C.
- State Diff, Session Local, and OCPM Features are appropriately kept out of numerical pooling; Final State is not misrepresented as historical State Diff.
- Requests for additional baselines, held-out data, or edge-level conformance are nonblocking for this bounded Raw run.