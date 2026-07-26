# WRITE task: front-matter compression round 2 + reference field trim

Edit EXACTLY TWO files in
`/home/yunwei37/workspace/agentsight-research-semantic-flamegraph`:
`docs/paper/main.tex` and `docs/paper/references.bib`.
No git commands. Never write outside the repository. Keep: thesis x3
verbatim, RQ titles, contributions enumerate structure, all tables/figures,
every number, every cite key. Chinese %-comments updated for rewritten
sentences. Compression only; paragraph roles and order unchanged.

## main.tex (enumerated)

1. Introduction paragraphs 1-6: second-round fusion — remove remaining
   connective filler, convert relative clauses to appositives. Target -10
   source lines total. Paragraphs 7-8 untouched except filler words.
2. Background: fuse the profiling-pipeline sentences in
   \subsection{System Profiling} once more (one sentence for
   sample/attach/fold + one for the tools, citations kept); in
   \subsection{Challenges for Agent Profiling} fuse the two
   AgentSight sentences. Target -6 lines.
3. Design: in \subsection{Semantic Operation Stack Model}, fuse the
   sigma/lambda notation sentences where possible without dropping any
   symbol definition; in the A2/CodeTraceBench paragraph fuse the
   worker/merge sentences. Target -8 lines.
4. Related Work: one more fusion pass within paragraphs; all citations
   stay. Target -5 lines.
5. Conclusion: fuse to at most 6 sentences; thesis sentence stays
   verbatim. Target -4 lines.

## references.bib

Remove `editor`, `publisher`, `address`, `month`, and `series` fields from
@inproceedings/@article entries (keep them where the entry would otherwise
lose its venue identity, e.g. @book). Do not remove or rename any entry;
do not touch entries lacking those fields.

## Validation

Compile clean; unique cite keys before == after (multi-line-aware);
thesis x3. Report in write-report.md: per-section line deltas, total
pages, body end page, References end page. Target: body ends on page 7.
