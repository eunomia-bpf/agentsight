# Independent review spec: verify the RQ1/RQ3/RQ4 paper insertions

You are an independent reviewer. The repository is
`/home/yunwei37/workspace/agentsight-research-semantic-flamegraph`.
A writing agent has just edited `docs/paper/main.tex` and
`docs/paper/references.bib`. Its task spec is `task-spec.md` and its report is
`write-report.md`, both in this directory. You must verify the work, not
redo it. READ-ONLY except for writing your review file. No git commands that
modify state (`git diff`/`git status` are allowed and encouraged).

## Checks (all required)

1. **Diff scope.** `git diff docs/paper/` — confirm ONLY main.tex,
   references.bib (and rebuilt main.pdf) changed, and every changed hunk in
   main.tex belongs to one of the three specified insertions or the two
   mandated clause updates (RQ4 envelope clause, Scope-and-Limitations
   clause). Any other textual change is a FAIL finding.
2. **Number fidelity.** Re-verify every inserted number against the named
   source records:
   - step-0078 experiment-001/results.md (tau-b/rho/pooled/counts/masses)
   - step-0031 experiment-001 result records (3B accuracy/macro-F1)
   - step-0077 experiment-001/first-pass-cost-and-aggregate.md and
     git-convergence-result.md (all RQ4 cost numbers)
   Every number in the insertions must match its record exactly (rounding
   as documented in write-report.md is acceptable).
3. **Claim-scope fidelity.** The RQ1 insertion must not claim population-
   scale divergence (step-0078 result-review.md defines the admissible
   claim); the RQ3 insertion must not disparage beyond capacity attribution;
   the RQ4 insertion must not call the 54.36-minute envelope model latency.
4. **Story invariants.** Thesis sentence appears exactly once, verbatim:
   "Agent observability needs profiling, not only debugging." The four RQ
   subsection titles are unchanged. No contribution wording changed.
5. **Format.** Each inserted English sentence has a following Chinese
   %-comment line; LaTeX compiles (`cd docs/paper && latexmk -pdf
   -interaction=nonstopmode main.tex` — you may run this; it rebuilds
   main.pdf, which is acceptable); no undefined citations in main.log.
6. **Bib entries.** kendall1938 and spearman1904 metadata are correct
   (authors, venue, year, volume/pages, DOI) to your knowledge, follow the
   file's existing VERIFIED-comment convention, and are actually cited.

## Deliverable

Write `independent-review.md` in THIS directory: verdict PASS or FAIL, a
table of checks with what you actually ran/compared, and every discrepancy
found (file, line, expected vs actual). Do not fix anything yourself.
