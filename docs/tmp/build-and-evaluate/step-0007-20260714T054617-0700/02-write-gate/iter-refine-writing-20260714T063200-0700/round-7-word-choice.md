# Round 7 — Word Choice

- Reviewer: independent subagent, read-only
- Reviewer method: complete-paper diction review using `paper-writing-style`
- Scope contract: word choice only; preserve scientific meaning, claim strength, scope, RQs, terminology, numbers, citations, and story

## Independent verdict

NOT PASS initially. Two word choices obscured the measured quantity; seventeen bounded diction groups and two consider items remained.

## Must-fix actions

1. Changed the abstract from `separate resource use` to `separate resource use by responsibility category`, naming the separation axis already stated in the paper.
2. Changed the RQ1 evidence opening from `reduce mixed groups` to `reduce mixed system-effect weight`, matching the actual metric rather than implying a group-count measurement.

## Should-fix actions

Applied all bounded suggestions:

- replaced `methodology transfers` with `core profiling method applies`;
- replaced conversational `gets for free` with `automatically provide`;
- repaired the Introduction's out-of-fold/boundary-F1 collocation;
- replaced vague `more general` with `flexible` for Perfetto;
- made the profiler, rather than trajectories, derive and link responsibility fields;
- replaced all nonnative `propagate over effects` phrases with `propagate to linked effects`;
- removed the internal `R114` run identifier from active paper prose while retaining the fixed 20-task suite, version, and complete protocol;
- converted Evaluation status/meta wording into paper prose;
- described the HINTBench snapshot as the study input rather than mutable repository state;
- repaired source-lineage, unit-operation, and executable phrasing;
- replaced `barely helps` with the measured 84.4% mixed result;
- replaced anthropomorphic `depths answer questions` with granularity-supported analyses;
- stated held-out target use as methodology rather than a finalizer pipeline;
- replaced nonnative inspection-work phrasing;
- described the six-task evidence as a complementary evaluation without user-specified fields;
- removed `present`, `released path`, and `This test covers` project-status diction from RQ3;
- clarified RQ4 benchmark, machine, cache, and predecessor wording;
- recast Scope as scientific coverage rather than a TODO status;
- separated lineage and \sys folding ownership in the Conclusion.

## Consider disposition

- Accepted `realize the model` instead of `instantiate the model`.
- Accepted `approximately 9.8K lines of code` instead of the unexplained `LOC` abbreviation.

## Change count

35 prose-sentence or caption units received targeted word-choice edits. No scientific content was deleted.

## Preservation audit

- Exact thesis and four fixed RQs unchanged.
- No claim, scope qualifier, mechanism, result, metric, baseline, dataset, or number changed.
- Fixed suite identity remains scientifically complete as `fixed 20-task real-Codex suite`; only the internal run label was removed from reader-facing prose.
- All cited real/public workloads remain.
- Citation commands remain 52.

## Build verification

- `make` and final `pdflatex` completed.
- PDF: 9 pages total (7 content plus 2 references).
- Abstract: 225 prose words and eight role-mapped sentences.
- Undefined citations/references: 0.
- Overfull boxes: 0 in final pass.
- `git diff --check`: clean.
- Exit `main.tex` SHA-256: `f2d47e5a37657e64216f0f0acb30077f9648316d1977502af4728abc2331b82f`.
- Exit `main.pdf` SHA-256: `c04e306ed8a3f008c55665d5038a332ae496ff0815940095230e7839e81dbc26`.

## Round decision

PASS after fixes. Proceed serially to terminology and claim-tone review.
