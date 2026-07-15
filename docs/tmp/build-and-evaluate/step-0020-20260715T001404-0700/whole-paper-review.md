# Whole-Paper Review After Recurrence Port

**Review mode:** fresh read-only AAAI/cross-domain whole-paper review
**Step verdict:** **PASS after repair**
**Overall AAAI submission verdict:** **REPAIR**

## Scope

The reviewer read the complete current `docs/paper/main.tex` and compiled PDF,
then checked the Step 0020 evidence boundary, current Rust mechanism, and AAAI
format. It did not edit the paper. The review distinguished defects introduced
or exposed by the recurrence port from broader pre-existing submission gaps.

## Repaired Must-Fix Findings

The first pass returned six concrete paper issues:

1. the released recurrence mechanism was hidden behind the supervised
   extra-information result in the abstract, introduction, and conclusion;
2. “start a new operation” contradicted the paper's atomic operation
   abstraction because the algorithm actually starts a segment;
3. the NPMI/two-means mechanism lacked a compact mathematical contract;
4. the RQ2 headline generalized across workloads although TraceElephant's
   favorable 50%-recall point is descriptive;
5. page eight began with conclusion text and one embedded figure used a
   forbidden CID/Identity-H font;
6. the unused `pgfplots` package was forbidden by the author kit and all four
   table captions preceded rather than followed their tables.

The repaired paper now:

- reports the released label-free recurrence constructor before the supervised
  comparator and calls the latter an extra-information comparator;
- labels OSWorld-Human as the recurrence development corpus in every headline;
- uses operation, segment, motif, group, and stack consistently;
- gives the NPMI equation, common transition sample space, two-means
  initialization, tie rule, cutoff, unseen-transition rule, and output role;
- calls the TraceElephant Work@50 result descriptive and the RQ2 results
  workload-specific;
- starts References at page eight, embeds only acceptable Type 1 fonts, removes
  `pgfplots`, and places every table caption below its table.

The final mechanical re-review returned `PASS` for all Step 0020 paper and
format changes.

## Preserved Scientific Contract

The exact thesis remains **“Agent observability needs profiling, not only
debugging.”** The four RQs remain attribution, real-problem correspondence, tag
accuracy, and profiling cost. The reviewer confirmed that recurrence is a
simple, principled current mechanism rather than a new paper abstraction, and
that the supervised 0.739/0.816 result is not represented as the release
constructor. The post-hoc 0.680/0.786 recurrence result remains explicitly
separate from confirmatory RQ3 evidence.

The review proposed a hierarchy-authority framing as one possible novelty
articulation. The root rejected that route because the author had explicitly
rejected that replacement story. The paper retains the original profiling-not-
only-debugging thesis and differentiates the artifact through source-linked
effects, conserved additive measures, and selectable semantic projections.

## Remaining Submission Blockers

Two blockers remain outside this existing-trajectory mechanism-development
step:

1. **Independent RQ3 confirmation.** The current recurrence result was
   developed on the already observed OSWorld-Human population. An unchanged
   current Rust path still needs one independent real public family with
   matched phase/action/group annotations before the paper can claim the full
   fixed RQ3 hypothesis is confirmed.
2. **Reproducibility checklist.** `ReproducibilityChecklist.tex` remains the
   official unfilled template and must be completed as a separate AAAI upload
   from the final paper and experiment state.

Novelty may still be perceived as pprof plus semantic grouping, and RQ2 does
not dominate every existing view at every operating point. These are reviewer
risks, not reasons to change the thesis, narrow a contribution, or reopen the
completed OSWorld mechanism search.
