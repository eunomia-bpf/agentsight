# WRITE task: Evaluation prose squeeze (enumerated, final round)

Edit EXACTLY ONE file: `docs/paper/main.tex` in
`/home/yunwei37/workspace/agentsight-research-semantic-flamegraph`.
No git commands. Never write outside the repository (no /tmp). No
exploration beyond main.tex and this directory. Keep: thesis x3 verbatim,
RQ titles, all tables, all figure panels, every number, every cite key.
Rewritten sentences get updated Chinese %-comments. Compress WORDING only.

## Enumerated compressions (inside \section{Evaluation} and captions only)

1. Data-classes paragraph ("We evaluate three data classes separately...")
   -> fuse to at most 4 source lines of English, all counts and citations
   kept.
2. RQ1 opening paragraph ("RQ1 asks whether... coarse-leaf warnings.")
   -> fuse the population sentences; keep every number.
3. RQ1 tau-b paragraph ("The same population-scale behavior holds...")
   -> fuse the two reading sentences after the statistics; keep all
   statistics and both citations.
4. Profile-guided reading paragraph -> fuse the first two setup sentences
   into one; keep all numbers and the query-specific disclosure.
5. Case Study 2: fuse the population paragraph's benchmark-count sentence
   with the pair-weighting sentence; fuse the recovery/completion
   percentage sentences with the drilldown sentence; keep all numbers.
6. RQ3 CodeTraceBench prose: state the 5,752-mark count once (it appears
   with the depth breakdown and again near canonicalization); merge the
   two canonicalization sentences; keep all numbers.
7. RQ4: fuse the two scaling-slope sentences into one; keep slope, R2,
   throughput, and overhead numbers.
8. Captions of fig:flamegraph and fig:agentreward-diff: remove restatement;
   keep panel identification and the standard-pprof clause. Architecture
   caption: keep as is.

## Validation

`cd docs/paper && latexmk -pdf -interaction=nonstopmode main.tex` — no
errors, no undefined refs. Count unique cite keys before/after with one
command (multi-line aware): must be equal.
Report in `write-report.md` here: per-edit line deltas, total pages, page
where the body ends (before References), References end page.
