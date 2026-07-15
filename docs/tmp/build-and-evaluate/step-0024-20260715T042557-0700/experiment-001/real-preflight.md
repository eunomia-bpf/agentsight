# REAL PREFLIGHT — Execution Only

**Status:** VALID
**Scientific verdict:** not tested
**Candidate change after preflight:** none

Both approved preflights ran through the release implementation on existing
real trajectories. Displayed diagnostic metrics were not used to select,
change, or interpret the candidate.

## OSWorld-Human Fold 0

```bash
python3 script/rq3_recurrence_stack_induction_eval.py \
  --mode preflight \
  --out-dir .agentsight/experiments/rq3-monotone-recurrence-v1/preflight
```

- 45 sessions, 521 operations, and 476 adjacent decisions completed.
- Candidate predictions and assignments are complete.
- The candidate boundary set is a subset of the current set.
- Added current-relative boundaries: 0.
- Removed current boundaries: 0 on this execution-only fold.
- Profiler mass is conserved.
- Output: `.agentsight/experiments/rq3-monotone-recurrence-v1/preflight/summary.json`.

## CodeTraceBench First Target

```bash
python3 script/rq3_codetracebench_stage_fidelity_eval.py preflight \
  --agentpprof-bin agentpprof/target/release/agentpprof \
  --reference-operations docs/visexp/out/codetracebench-rq2/full/reference-operations.jsonl \
  --target-operations docs/visexp/out/codetracebench-rq2/full/target-operations.jsonl \
  --verified-manifest .agentsight/experiments/codetracebench-rq2/manifests/verified.parquet \
  --out .agentsight/experiments/rq3-monotone-recurrence-codetracebench-v1/preflight
```

- 1 session, 47 operations, and 46 adjacent decisions completed.
- Rust prediction completed before official stage scoring.
- The candidate boundary set is a subset of the current set.
- Added current-relative boundaries: 0.
- Removed current boundaries: 8.
- All target weight is conserved.
- The summary explicitly records `tested_hypothesis: not tested`.
- Output: `.agentsight/experiments/rq3-monotone-recurrence-codetracebench-v1/preflight/summary.json`.

## Decision

The approved real paths engage the intended monotone mechanism and satisfy the
execution, isolation, coverage, subset, and conservation checks. The plan is
unchanged. The three approved complete runs may proceed once, without any
additional tuning or candidate change.
