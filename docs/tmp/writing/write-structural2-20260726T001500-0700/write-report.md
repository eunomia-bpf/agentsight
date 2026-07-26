# WRITE report — final structural bundle toward the 7-page body

Task: `write-structural2-20260726T001500-0700`
File edited: `docs/paper/main.tex` only. No git commands run; nothing written
outside the repository.

## Moves executed (in order)

1. **Main-body `\subsection{Scope and Limitations}` → appendix.** Deleted the
   main-body subsection heading and moved its sentences into the existing
   appendix subsection `app:scope` (prepended before the original
   CodeTraceBench/AgentRewardBench limitations paragraph). RQ4 now ends with
   the pointer sentence plus Chinese comment:
   `Scope details appear in Appendix~\ref{app:scope}.`
2. **`fig:agentreward-diff` to single column.** Changed `\begin{figure*}[t]`/
   `\end{figure*}` to `\begin{figure}[tb]`/`\end{figure}`, and both panel
   widths from `.65\linewidth` to `\columnwidth`. Caption and label kept;
   figure remains in the main body.
3. **RQ2 residual protocol prose.** Moved the body paragraph
   ("Within each workload, we fix operations, target-blind paths, benchmark
   judge/localizer predictions, and scoring rules before loading test
   targets." + the group-score summary sentence with `\cite{wilson1927}`)
   into appendix `app:rq2-scoring` (prepended before the existing snapshot
   detail). Body now keeps one compressed fixed-before-loading sentence with
   the `Appendix~\ref{app:rq2-scoring}` pointer, followed by the
   direct-diagnostic definition sentence (needed to read Table 1).
4. **RQ1 six-way-control paragraph fused to 3 sentences** (≤4). All numbers
   preserved verbatim: 489, six profiles, 105, six coarse action kinds,
   39.42%, 102/105, 97.
5. **Case Study 1 drilldown fused with the preceding numbers paragraph.**
   The "Source drilldown shows..." clause is now joined to the subtree-numbers
   sentence in one paragraph. Every number preserved: 489, 4,558,192, 56.24%,
   43.76%, 86.62%, 97, 1,936,828, 105, 2,103,587, 21.47%, 46.15%, three.

## Validation

| Check | Result |
|---|---|
| Compiles clean (`pdflatex` ×3 + `bibtex`) | PASS (all exit 0, no errors) |
| Undefined references / citations | none |
| Multiply-defined labels | none |
| LaTeX / BibTeX warnings | none |
| Unique cite keys before == after | PASS — 44 unique keys; only relocation (e.g. `wilson1927` moved body→appendix `app:rq2-scoring`), none added/removed |
| Thesis x3 verbatim | PASS — lines 44, 144, 969 (`Agent observability needs profiling, not only debugging.`) |
| Four RQ subsection titles | PASS — RQ1 Multi-Resource Attribution / RQ2 Problem Correspondence / RQ3 Automatic Operation Structure / RQ4 Profiling Cost |
| Tables 1–2 in body | PASS — `tab:rq2-localization`, `tab:rq3-codetrace` both in body |
| Five flamegraph panels rendered | PASS — 3 panels of `fig:flamegraph` (PNG 1980×573) on p.5; 2 panels of `fig:agentreward-diff` (PNG 1980×532) on p.6 |

## Page measurements

| Quantity | Value |
|---|---|
| **Total pages** | **12** |
| **Body end page** (last line of Conclusion) | **8** (Conclusion occupies the right column of p.8; Related Work fills the left column of p.8) |
| **References end page** | **10** (References begins mid right-column of p.8, after the Conclusion) |
| Appendix pages | 11–12 |

## Rendered position/size of `fig:agentreward-diff`

- **Page:** 6 (single-column `figure` float, top-of-column placement `[tb]`).
- **Environment:** changed from `figure*` (two-column span) to `figure`
  (one-column span).
- **Panels:** two stacked, each `\includegraphics[width=\columnwidth]{...}`.
  Underlying PNGs are 1980×532; rendered at 598 ppi each panel measures
  ≈ 3.31 in × 0.89 in, i.e. one column wide (`\columnwidth` ≈ 3.3 in of the
  7.0 in `\textwidth`). Caption and `\label{fig:agentreward-diff}` retained.
- The previous `.65\linewidth` panels inside `figure*` were ≈ 4.55 in wide;
  the move narrows each panel to one column and frees the facing column for
  body text.

## Target assessment

Target was "body ends on page 7 or within a few lines of it."
**Actual body end: page 8.** The five moves reduced body content (Scope &
Limitations and RQ2 scoring prose moved to appendix; two paragraphs fused),
but the Conclusion still sits in the right column of page 8 with Related Work
in the left column — i.e. the body carries roughly one full left column plus
~9 lines of right column onto page 8, which is more than "a few lines" beyond
page 7. The bundle compresses the body but leaves it one page (about 1.25
columns) short of the page-7 target.
