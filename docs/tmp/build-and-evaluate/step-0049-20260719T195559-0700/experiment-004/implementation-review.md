# Experiment 004 Source-Only Implementation Review

**Reviewer:** Grok 4.5, read-only  
**Verdict:** **APPROVE**  
**Must-fix:** None  
**Official stages:** The registered scorer may now open them exactly once.

The reviewer did not open the official stage manifest, any score output, or
compute B-cubed or boundary metrics.

## Independent audit

- Coverage: 405/405 complete trajectories and 20,866/20,866 unique operations;
  prediction keys exactly match session caches and contain no stage fields.
- Provenance: all caches agree on Qwen model SHA-256, seed `20260719`, algorithm
  version, and v2.3 output constraint. All 405 record the v2.2 compact-JSON
  origin. The 20,254 migrated prefixes are byte-identical to their archived
  source, and 612 operations were extended live under v2.3.
- Replay: 0 illegal transitions, empty stacks, forbidden keep-zero/null pairs,
  order/identity mismatches, label drifts, or non-compact responses across all
  20,866 transitions.
- Immutable root: no task-root instance occurs in model output; the scorer adds
  one fixed public-task root per trajectory, with stable label and full-session
  support.
- Contraction: 20,857 generated frames comprise 19,179 support-one frames and
  1,678 retained multi-operation frames. The result has 1,690 effective leaf
  groups; 20 operations in 12 sessions fall back to the task root.
- Ancestor and conservation properties: independent recomputation found zero
  nearest-retained-ancestor mismatches, one effective leaf per operation, and
  no dropped weight.
- Depth remains uncapped: retained effective depth including the root ranges
  from 1 to 6; support, rather than depth, is the only contraction condition.
- Ordering: `run_score` contracts and writes the source-only partition before
  its first call that loads official stages.

## Decision

The implementation matches the approved immutable-root plus minimum
multi-operation-support rule. The registered complete-population scorer may
now run once on the fixed prediction set.

