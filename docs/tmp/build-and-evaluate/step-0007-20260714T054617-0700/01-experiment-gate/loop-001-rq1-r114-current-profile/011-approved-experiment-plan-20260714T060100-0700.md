# Approved RQ1 R114 Current-Profile Replay Plan

## Approval record

- Approved: 2026-07-14T06:01:00-07:00
- Canonical base: `007-experiment-plan-v4-20260714T055657-0700.md`
- Canonical replacement: `009-experiment-plan-v5-20260714T055900-0700.md`
- Serial reviews: four minimal FAIL-and-repair rounds followed by one PASS
- State: `PROPOSE -> REVIEW -> REAL PREFLIGHT`

The approved experiment has exactly two reported stages. The unchanged R114
suite evaluates scoped lineage and concurrent negative controls under its
existing thresholds. One thin runner consumes already persisted R114 process
and tool scope identities, selects true-positive joined rows, converts them
once to ordinary operation JSONL, invokes current AgentProf once, and checks
exact row, total-mass, and per-category-mass preservation.

Execute only one full preflight task and the unchanged full 20-task suite. Do
not add a second profile, benchmark, model, task, tagger, ontology, ranker,
cutoff, statistical test, or robustness run.

