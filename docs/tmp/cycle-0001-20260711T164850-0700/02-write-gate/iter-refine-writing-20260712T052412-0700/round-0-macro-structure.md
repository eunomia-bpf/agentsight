# Round 0: Macro Structure

**Timestamp:** 2026-07-12T05:24:12-07:00  
**Reviewer:** fresh independent subagent; paper read-only  
**Initial verdict:** REVISE  
**Final status:** FIXED

## Must-Fix Findings

1. RQ subsection openings had drifted from the three canonical RQs: RQ1 was
   narrowed to lineage and RQ3 to phase-mapping transfer.
2. `Current Performance Evidence` appeared after RQ3 even though it closes
   RQ2's cost condition.
3. The paper introduced a new post-result principle in the abstract and
   conclusion but had no discussion that separated execution location,
   cross-run similarity, and decision-oriented aggregation.

## Applied Changes

- Restated all three canonical RQs in the evaluation overview.
- Began RQ1 and RQ3 with the full RQ, then explicitly marked the current
  experiment as partial/proxy evidence.
- Moved and compressed cost evidence into RQ2 as `Cost boundary`, so RQ2 closes
  once.
- Added a short Discussion after Evaluation. It distinguishes execution
  nesting, behavior similarity, and the hierarchy used to aggregate a measured
  change; it also keeps Hodoscope's bundle confound and the inconclusive matched
  hierarchy isolation explicit.
- Replaced the conclusion's future-plan ending with the current principle that
  hierarchy must be made explicit and validated.

## Verification

- `make` in `docs/paper/`: PASS.
- Output: 9 pages, 743,759 bytes.
- Undefined citations/references: zero.
- Overfull boxes: zero.
- Skills and Git: untouched.
