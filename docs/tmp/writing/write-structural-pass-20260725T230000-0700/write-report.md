# WRITE report: structural condensation to 7-page AAAI body

Edit target: `docs/paper/main.tex` only. All five moves executed as
appendix moves / fusions, not deletions. No git commands run; nothing
written outside the repository.

## Validation

- `cd docs/paper && latexmk -pdf -interaction=nonstopmode main.tex`:
  **0 errors, 0 undefined references, 0 multiply-defined labels.** Only
  benign `Underfull \hbox / \vbox` warnings remain (same kind as the
  pre-edit build).
- Unique cite keys: **44 before == 44 after** (multi-line-aware count via
  `\cite{...}` extraction, split on `,`, trimmed, deduplicated).
- Thesis `Agent observability needs profiling, not only debugging.`
  appears **3× verbatim** (abstract L44, intro L145, conclusion L993) —
  unchanged.
- Four RQ subsection titles unchanged: `RQ1: Multi-Resource Attribution`
  (L525), `RQ2: Problem Correspondence` (L617), `RQ3: Automatic Operation
  Structure` (L787), `RQ4: Profiling Cost` (L884).
- Table 1 (`tab:rq2-localization`, L665) and Table 2 (`tab:rq3-codetrace`,
  L846) remain in the main body. All five flamegraph panels remain
  (`fig:flamegraph` L548–550, `fig:agentreward-diff` L743–744).
- All RQ4 prose numbers retained in body: union 27{,}765 ops, 1.16 s,
  465.2 MiB, +19.6 % time / +1.14 % RSS, slope 0.0418 ms/op, R^2 0.9997,
  23{,}935 ops/s (L897–904).
- OSWorld summary sentence retained in body: 0.739 boundary F1 / 0.816
  B$^3$, label-free 0.680 / 0.786, strongest control 0.645 / 0.678 on
  287 OSWorld-Human sessions (L857–859).
- Literal-label summary sentence retained in body: 0.695 / 0.733 on
  1{,}012 AgentBoard goals vs 0.044 / 0.248 majority, and 0.498 / 0.628
  on 2{,}737 ASE labels vs 0.061 / 0.323 majority, with the original
  citations `qwen36, agentboard, traceview-2026,
  bouzenia-pradel-2025-trajectories` (L864–872).

## Page accounting (AFTER)

| Item | Page |
| --- | --- |
| Total pages | **12** (unchanged from before) |
| Body ends (Conclusion's closing sentence "...making population profiling practical alongside per-run debugging.") | **page 8** (within 7–8 target) |
| References begin (bottom of right column) | page 8 |
| References end | page 10 |
| Appendix begins (`\section{Technical Appendix}`) | **page 11** (was page 12 before) |
| Appendix ends | page 12 |

Body end page was confirmed by extracting page 8: the Conclusion's last
sentence "...making population profiling practical alongside per-run
debugging." appears in the right column of page 8, immediately above the
`References` heading. Page 11 starts with `Technical Appendix` (verified
via `pdftotext -layout` and the `main.aux` `\newlabel{sec:appendix}{11}`).

## Where each moved block landed

| Move | Block | New location (file line) | Page in PDF |
| --- | --- | --- | --- |
| 1 | Table 3 `tab:rq3-boundary` (OSWorld boundary/partition) + setup sentence "We test all 287 OSWorld-Human..." + summary prose "The supervised predictor reaches 0.739 boundary F1..." | `\subsection{OSWorld-Human Boundary Study Detail}` (`app:osworld`), inserted at the head of the existing subsection at L1089; table label now L1136 | page 11 |
| 1 (body) | New one-sentence summary: "On all 287 OSWorld-Human task-instance sessions...supervised predictor reaches 0.739 boundary F1 and 0.816 B$^3$ F1, label-free recurrence reaches 0.680 / 0.786, and the strongest control reaches 0.645 / 0.678 (Appendix~\ref{app:osworld})." | L856–859 | page 7 |
| 2 | AgentBoard task-family paragraph ("For task-family tags...") + ASE action paragraph ("For action tags...") + Locate-exclusion sentences, all with their Chinese comments | New `\subsection{Literal-Label Backend Detail}` (`app:literal`) at L1176, placed between `app:partition` and `app:scope` | page 12 |
| 2 (body) | New one-sentence summary carrying 0.695/0.733 vs 0.044/0.248 and 0.498/0.628 vs 0.061/0.323 with original cite keys | L864–872 | page 7 |
| 3 | Table 4 `tab:rq4-cost` (cost-scaling table) | New `\subsection{Cost Scaling Table}` (`app:cost`) at L1091, placed between `app:a2-reconstruction` and `app:osworld`; table label now L1108 | page 11 |
| 3 (body) | Existing RQ4 prose retained verbatim; only added "(Table~\ref{tab:rq4-cost} in Appendix~\ref{app:cost})" to the slope sentence at L899–900 | L897–904 | page 8 |
| 4 | All five flamegraph panels resized from `.70\linewidth` to `.65\linewidth`: `fig:flamegraph` panels at L548, L549, L550; `fig:agentreward-diff` panels at L743, L744 | (in place) | pages 5 and 7 |
| 5 | RQ3 summary paragraph fused from two sentences into one: "Thus, across the named public populations, ... reach 0.695 and 0.498 macro-F1, evaluating complementary structural and literal outputs rather than one bespoke score." | L875–880 | page 7 |

## Notes on move semantics

- **No number or claim was deleted.** Every number that appeared in the
  pre-edit body is still present either in the body summary sentences or
  in the appendix subsections that now hold the moved tables/prose.
  Reference-calibrated recurrence (0.734/0.801), population counts
  (3{,}978 ops, 3{,}691 pairs, 2{,}042 groups), and the Locate-exclusion
  numbers (0.490 / 0.622) all moved with their original paragraphs into
  `app:osworld` / `app:literal`.
- **Chinese `%`-comments were preserved verbatim** with their moved
  paragraphs. New summary sentences in the body carry newly written
  Chinese comments matching the English content.
- **Two new appendix subsection labels were introduced** (`app:literal`,
  `app:cost`); both are referenced from the body via `Appendix~\ref{...}`
  and resolve without warnings. The pre-existing `app:osworld` subsection
  now also holds Table 3 and is referenced from the new body summary
  sentence.
- **Appendix table numbering shifted**: in the PDF, the moved
  `tab:rq4-cost` is now Table 3 and the moved `tab:rq3-boundary` is now
  Table 4 (they appear in appendix order: cost before osworld). The body
  refers to them by `\ref`, so all references resolve correctly.
- **No git commands were executed.** No files outside the repository
  were written. The only file modified is `docs/paper/main.tex`; this
  report is the only new file, written into the task-spec directory as
  instructed.
