# WRITE task: structural condensation to reach the 7-page AAAI body

Edit EXACTLY ONE file: `docs/paper/main.tex` in
`/home/yunwei37/workspace/agentsight-research-semantic-flamegraph`.
No git commands. Never write outside the repository. Keep: thesis x3
verbatim, four RQ titles, Table 1 (RQ2) and Table 2 (RQ3 CodeTrace) in the
main body, ALL five flamegraph panels, every number, every cite key.
Moved text keeps its Chinese %-comments; new summary sentences get new
Chinese comments. These are MOVES and fusions, not deletions: no number or
claim may disappear from the document.

## Structural moves (in order)

1. **Table 3 (OSWorld, `tab:rq3-boundary`) and its remaining prose** move
   to appendix subsection `app:osworld` (which already holds the setup
   detail). Keep in the main body ONE sentence: the supervised predictor
   reaches 0.739 boundary F1 / 0.816 B^3 and label-free recurrence 0.680 /
   0.786 on 287 OSWorld-Human sessions, versus 0.645 / 0.678 for the
   strongest control (Appendix~\ref{app:osworld}).
2. **RQ3 literal-label prose** (AgentBoard task-family paragraph and ASE
   action paragraph, including the Locate-exclusion sentences): move both
   paragraphs to a new appendix subsection
   `\subsection{Literal-Label Backend Detail} \label{app:literal}`.
   Keep in the main body ONE sentence carrying: 0.695/0.733 on all 1,012
   AgentBoard goals versus 0.044/0.248 majority, and 0.498/0.628 on all
   2,737 ASE labels versus 0.061/0.323, with the existing citations
   (Appendix~\ref{app:literal}).
3. **Table 4 (RQ4 cost, `tab:rq4-cost`)** moves to a new appendix
   subsection `\subsection{Cost Scaling Table} \label{app:cost}`. Keep in
   the main body the existing prose numbers (union 27{,}765 ops, 1.16 s,
   465.2 MiB, +19.6%/+1.14%, slope 0.0418 ms/op, R^2 0.9997, 23,935 ops/s)
   plus "(Appendix~\ref{app:cost})".
4. **Figures to the floor**: both flamegraph figures' panels from
   `.70\linewidth` to `.65\linewidth`.
5. **RQ3 summary paragraph** ("Thus, across the named public
   populations..."): fuse into one sentence since the details now sit in
   the appendix.

## Validation

`cd docs/paper && latexmk -pdf -interaction=nonstopmode main.tex` — no
errors, no undefined references. Unique cite keys before == after
(multi-line-aware count). Report in `write-report.md`: total pages, page
where the body ends, References end page, appendix start page, and where
each moved block landed. Target: body ends on page 7-8.
