# Round 5 — Cross-Paper Consistency

## Node identity

- **Started:** 2026-07-17T13:35:00-07:00
- **Completed:** 2026-07-17T13:48:07-07:00
- **Parent:** Step 0040 WRITE gate
- **Procedure:** an independent read-only subagent invoked
  `check-terminology-infoflow` over the complete paper; the root evaluated its
  findings, changed only the affected prose, synchronized the bilingual source
  comments, and rebuilt the paper. Neither agent performed a Git operation.

## Independent audit result

The audit returned **REVISE** with two must-fix and two should-fix findings.
It separately verified that the exact thesis, four fixed RQs and their order,
headline result values, figure/table references, standard metric names, and
9.8 kSLOC implementation description were mutually consistent.

### Must-fix findings and dispositions

1. **RQ3 used a blanket target-blind description.** Thirty-nine
   AutoCodeRover inputs contain the literal action word `Locate`, so the input
   boundary is not identical across every RQ3 protocol. The root replaced the
   blanket statement with a protocol-scoped input-boundary statement and added
   the already computed sensitivity result: after excluding those 39 inputs,
   action assignment remains at 0.490 macro-F1 and 0.622 accuracy. The positive
   majority-baseline comparison is therefore unchanged. This is a
   source-fidelity qualifier, not a new development result or claim retreat.
2. **The contribution list blurred integrated and standalone field paths.**
   The root now distinguishes the integrated declared-task path from the
   standalone action-label backend. It does not imply that the latter is
   exposed through the integrated CLI.

### Should-fix findings and dispositions

3. **The RQ2 answer was broader than its comparisons.** The endpoint now says
   exactly that the matched semantic-versus-raw comparison is positive on all
   three complete workloads and that the adaptive local-first analysis supports
   semantic refinement without overriding operation-local scores. It makes no
   universal claim over every available diagnostic signal.
4. **Two population counts could be read as one coverage claim.** The RQ1
   five-depth sweep is now explicitly a nine-dataset, 13,265-operation analysis;
   separate adapters map the full 15-family, 47,590-operation annotated set to
   the common operation model. No population total changed.

The corresponding Chinese source comments were updated with the same scope.

## Direct metric-instruction verification

The manuscript and bibliography contain no token-weighted B$^3$, Recall@20\%,
fixed top-3 reader, or reader-protocol result. Ordinary operation-level B$^3$
is the RQ1/RQ3 partition metric; MAP is the RQ2 ranking metric; macro-F1 and
accuracy are the literal multiclass metrics; exact boundary precision, recall,
and F1 are the boundary metrics. Each paper-facing metric is connected to its
defining paper or established benchmark source in the manuscript.

The experiment-design skill was changed separately and minimally: its existing
workload/metric proposal and plan-review bullets now require published standard
paper-facing primary metrics and the defining paper or official benchmark.
Project-defined weighting, cutoff-budget scores, and model-reader protocols are
kept internal. No new gate, artifact type, or review stage was added. That skill
repository change remains unstaged, uncommitted, and unpushed for human review.

## Build and format check

`make` completed all PDF, bibliography, and final PDF passes. The output is US
Letter with embedded Type 1 fonts and has no undefined citation, undefined
reference, multiply-defined label, or overfull warning. The PDF is ten pages:
the conclusion currently begins at the top of page 8 and references begin
below it. This is one content-placement regression relative to Round 4, when
the complete body ended on page 7. Sentence-level Rounds 6--9 must recover that
space without deleting evidence or changing meaning.

## Status and next node

Round 5 is complete. Round 6 performs an independent sentence-structure pass
using `paper-writing-style`. Its accepted edits must be local, quantitative
content remains read-only, and page-budget recovery may only come from clearer
and tighter expression.
