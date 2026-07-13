# Root Application Of Accepted Scientific Disposition

**Completed:** 2026-07-12T17:52:00-07:00  
**Cycle/gate:** cycle 0001 / full WRITE  
**Parent:** `000-gate-entry-20260712T174900-0700.md`  
**Status:** complete; paper ready for writing Round 0

## Objective

Apply the already accepted REVIEW disposition to the reader-facing paper before
writing refinement. This node changes scientific organization only where the
root disposition explicitly authorized it; the following writing rounds treat
the thesis, RQ meanings, and positive hypotheses as read-only.

## Changes Applied

- Changed the title from a generic semantic-profiling label to
  **“AgentProf: Profiling AI Agents, Not Just Debugging Them.”**
- Rebuilt the Abstract around the exact thesis, two abstractions, four-part
  evaluation chain, and valid current conservation evidence.
- Removed AgentRx/TELBench and the recursive Hodoscope experiment results from
  the Abstract, Introduction, contribution list, Evaluation, Limitations,
  Discussion, Related Work result summary, and Conclusion.
- Removed the two obsolete negative result tables and all references to their
  labels. Their complete data and reports remain in `docs/evaluation.md` and
  timestamped experiment nodes.
- Restored the exact four RQs in the Evaluation overview and as four separate
  subsections.
- Reframed RQ1 as resource attribution, keeping only verified conservation and
  declared-category separation as necessary evidence rather than claiming
  independent lineage.
- Reframed RQ2 around a real before/after additive regression, matched flat,
  native, and semantic profiles, a concrete profile-guided intervention, and a
  held-out rerun.
- Reframed RQ3 around target-blind tag accuracy, stability, and downstream
  attribution consequence; retained current mapping transfer only as a proxy.
- Restored RQ4 as a separate complete cost question covering release-build cold
  construction, warm reprojection, CPU, peak memory, model use, storage, and
  capture overhead when evaluated.
- Rebuilt Discussion and Conclusion around profiling as an optimization
  interface rather than a hierarchy-choice or failed-mechanism paper.

## Evidence And Preservation

No positive number was invented. The current paper keeps existing valid values
for 325 trajectories, 183,714 recorded units, conservation, declared-category
separation, and mapping-transfer proxy evidence. Unfinished positive answers are
explicitly marked unresolved result TODOs. The root deliberately removed
citations attached only to obsolete experiment-detail paragraphs; all
closest-work families remain cited in Related Work.

The exact RQ headings now appear in the overview and section headings:

1. `RQ1: Does Semantic Profiling Improve Resource Attribution?`
2. `RQ2: Does Profiler Output Correspond to Real Problems?`
3. `RQ3: How Accurate Are the Tags?`
4. `RQ4: What Is the Profiling Cost?`

The accepted narrative is stronger than the initial draft because it preserves
the initial problem, thesis, two abstractions, and complete four-RQ chain while
retaining later evidence discipline. It is stronger than the immediately
previous paper because controls and intermediate failures no longer replace the
population-level profiling contribution.

## Verification

`make clean && make` completed successfully under `docs/paper/`. The resulting
PDF has 8 letter-size pages. The final log contains no undefined citation,
undefined reference, LaTeX error, or emergency stop. The source contains no
reference or label for the removed negative tables. The paper submodule and
shared skill repository were not edited.

## Next Action

Run all eleven serial rounds of `iter-refine-writing`, beginning with a fresh
read-only macro-structure review. Each round must reread the verbatim user
instructions, preserve the exact RQs and scientific meaning, apply fixes in
subsection-sized edits, and recompile before advancing.
