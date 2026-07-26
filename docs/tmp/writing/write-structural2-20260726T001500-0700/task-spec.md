# WRITE task: final structural bundle toward the 7-page body

Edit EXACTLY ONE file: `docs/paper/main.tex` in
`/home/yunwei37/workspace/agentsight-research-semantic-flamegraph`.
No git commands. Never write outside the repository. Keep: thesis x3
verbatim, four RQ titles, Tables 1-2 in the body, ALL five flamegraph
panels rendered in the document, every number, every cite key. Moves and
fusions only — nothing disappears from the document.

## Moves (in order)

1. **Main-body \subsection{Scope and Limitations}**: move its remaining
   sentences into the existing appendix subsection (label `app:scope`),
   delete the main-body subsection heading, and end RQ4 with one pointer
   sentence: "Scope details appear in Appendix~\ref{app:scope}." (plus
   Chinese comment).
2. **fig:agentreward-diff to single column**: change its environment from
   `figure*` to `figure`, panels from `.65\linewidth` to `\columnwidth`
   (two stacked panels), keep the caption. It stays in the main body.
3. **RQ2 residual protocol prose**: move the paragraph describing the
   per-workload scoring mechanics that remains in the body (the "Within
   each workload, we fix operations..." material and the group-score
   summary sentence) into appendix `app:rq2-scoring`, keeping in the body
   only: one sentence stating targets/paths/scoring were fixed before
   loading test targets with the appendix pointer, and the sentence
   defining the direct diagnostic (needed to read Table 1).
4. **RQ1 six-way-control paragraph**: fuse to at most 4 sentences; all
   numbers (105, six kinds, 39.42%, 102/105, 97) stay.
5. **Case Study 1 drilldown paragraph** ("Source drilldown shows..."):
   fuse with the preceding numbers paragraph; every number stays.

## Validation

Compile clean; no undefined references; unique cite keys before == after;
thesis x3; five \includegraphics present. Report in write-report.md:
total pages, body end page, References end page, and the rendered
position/size of fig:agentreward-diff. Target: body ends on page 7 or
within a few lines of it.
