# Round 5 — Reviewer Stress Test

**Date:** 2026-07-07

## Can a reviewer easily construct a reject?

**With difficulty.** The paper has a clear problem, clean model, and solid quantitative evidence. The easiest reject angles (novelty, methodology) have been preempted by careful scoping.

## Best reject argument (3 points)

1. **Insight is sound engineering, not research contribution.** The operation/operation-stack model is isomorphic to pprof's sample-with-labels/tag-derived-stack applied to a new domain. The "no execution stack" distinction is accurate but doesn't change the profiling model fundamentally.

2. **Evaluation disconnection.** RQ1 (real sessions) uses unvalidated regex labels. RQ2 (public datasets) uses mapping rules, not intent recognition. No experiment validates intent-recognition quality on free-form prompts — the hardest part of the system.

3. **Abstract headline cherry-picks weak baseline.** "90% less inspection work" is vs. flat (any hierarchy would achieve similar). The 45% vs. fixed-session is more informative.

## Where the reject is weakest

- The structural-mismatch insight is real (90% mixed weight, 417× fragmentation). Even if the resolution is straightforward, the evidence is solid.
- Workshop papers are allowed to defer ground-truth validation of the free-form path. The two evaluation worlds address different claims.

## What was changed

### Intro ¶6 (line 125): Balance baseline comparisons
- Before: "reduces inspection work by 90% versus flat summaries."
- After: "reduces inspection work by 90% versus flat summaries and group fragmentation by 45% versus fixed-session drilldown."

## Overall assessment

- **Workshop paper:** Strong enough. Clean problem/model/eval chain with honest scoping.
- **Full paper:** Not yet. Needs validated intent-recognition labels, multi-project data, real figures, and user study or case-study walkthrough.

## Non-framing issues noted (not fixable in this cycle)
- Placeholder figures (significant for a visualization paper)
- Single-project real data
- Evaluation disconnection between real sessions and public datasets
