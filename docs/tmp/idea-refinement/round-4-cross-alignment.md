# Round 4 — Cross-Alignment

**Date:** 2026-07-07

## What was checked

Full narrative chain: Problem → Insight → Requirements → Design → Contributions → Evaluation.

## Findings

### Aligned chains (no issues)
- Problem → Insight: ✓
- Insight → R1/R2/R3: ✓ (1:1 mapping)
- R1/R2/R3 → Design §3.1/§3.2/§3.3: ✓ (subsection titles name requirements)
- Design → C1/C2: ✓

### Misalignments found

1. **RQ3 title mismatch (Important):** "How Reliable Is Intent Recognition?" but strongest evidence tests mapping rules on structured traces, not intent recognition on real sessions. Real-session tagger quality is future work (line 637).

2. **Actionability results orphaned (Important):** Profile-spec patches and rank-feature ablations (lines 609-627) are substantial but not promised by any contribution.

3. **Minor dimension drops:** Safety/failure in problem ¶1 but only cost weight in RQ1. RQ2 covers them, but a reviewer reading RQ1 alone may wonder.

## What was changed

### RQ3 title (line 630): Match what it tests
- Before: "How Reliable Is Intent Recognition?"
- After: "How Reliable Are the Derived Labels?"

### C3 (line 152): Anchor actionability
- Added: "Profile-spec patches identify actionable configuration knobs on 5/6 tasks"

## Remaining concerns

- Minor dimension-drop (safety in problem, only cost in RQ1) not fixed — RQ2 covers it adequately.
- The intent-recognition ablation gap (Round 2c also noted this) remains — RQ1 shows "no labels = 90% mixed" but doesn't isolate intent recognition from mapping rules. Acceptable scope for a workshop paper.
