# Step 0082 result review (root disposition)

Timestamp: 2026-07-25T04:05:00-07:00
Root disposition: COMPLETED AS ITERATION — no paper claim; protocol frozen
at v1 for the paper.

## Run validity

All 220 queries completed with raw responses, per-query results, and
bootstrap deltas before the executor's provider balance exhausted (the only
missing deliverable is execution-log.md; results.md and raw artifacts are
harness-written and complete). No independent review commissioned: none of
these numbers is paper-facing.

## Registered-target outcome

MAP 0.447 (target >= 0.48, v1 was 0.455, paired delta vs v1 not
significant); mean logical tokens 14,830/query (target < 12,615; v1 was
15,991); content opened 53.4% (target <= 53%). All three targets missed.

## Findings that close the branch

1. The frozen TraceElephant projection exposes no per-operation token mass,
   so "width annotation" reduced to member counts the reader could already
   infer — no new discrimination signal was actually added.
2. Lean stage 2 saved only ~1.2K logical tokens/query; opened evidence
   dominates cost, so single-query token parity with full-trace reading is
   not reachable by packet slimming at ~53% content opened.
3. MAP is insensitive to these packet changes (0.447 vs 0.455, interval
   crosses zero), consistent with analysis-001: the residual lever is
   stage-1 discrimination signal content, which these changes did not add.

## Consequences

- The paper reports protocol v1 (steps 0080/0081): quality ladder, the
  significant semantic content-efficiency effect, and the context-window
  feasibility argument. No total-token-savings claim is made anywhere.
- No protocol v3 on TraceElephant: marginal expected gain, and the grok
  reader budget is exhausted, ending same-reader comparability.
- Workload extension (step 0083+) proceeds with the kimi reader; each
  workload is internally consistent and the reader-family change across
  workload studies is disclosed.
