# Task: rewrite the submodule's Algorithms and Evaluation from current paper

Target file: docs/agentpprof-paper/main.tex (the submodule; the user has
explicitly authorized editing files inside it). ABSOLUTE RULES:
- NEVER run any git command anywhere (the user will review before any
  commit; the rewrite must remain uncommitted).
- Touch ONLY docs/agentpprof-paper/main.tex. Everything else read-only.
- Do not modify: abstract, Introduction, Background and Motivation,
  Related Work, Conclusion, title, author block, preamble.

Source of truth: docs/paper/main.tex (current verified paper).

## Scope of rewrite (content transplant, bilingual comments included)

1. Design section: replace the submodule's algorithm content (its
   \subsection{Algorithms} and any adjacent algorithm description that
   contradicts the current system) with the current paper's corresponding
   Design content: the three-object design paragraphs, Semantic Operation
   Stack Model subsection, Recursive Operation Annotation subsection with
   the DIRECT annotation protocol, and the canonicalization summary
   sentence. Keep the submodule's section/subsection ordering conventions.
2. Evaluation section: replace the submodule's entire Evaluation section
   with the current paper's Evaluation (research-questions paragraph, data
   classes, RQ1-RQ4 subsections with their question titles, all three
   case studies, tables, and figure blocks). Figure paths like
   ../visexp/out/... resolve correctly from the submodule directory; keep
   them as-is.
3. Append the current paper's Technical Appendix section (all
   subsections) before \end{document} so evaluation appendix references
   resolve. Add \clearpage\appendix wrapper as in the current paper.
4. Implementation section: if the submodule's Implementation contradicts
   the transplanted content (e.g., missing annotation-workspace or
   recurrence-backend paragraphs referenced by the appendix), replace it
   with the current paper's Implementation section as well; otherwise
   leave it.
5. Chinese %-comments transplant together with their English sentences
   (the source is already bilingual).

## Validation

cd docs/agentpprof-paper && latexmk -gg -pdf -interaction=nonstopmode
main.tex: 0 errors, 0 undefined citations (add missing bib entries to the
submodule's references.bib by copying them verbatim from
docs/paper/references.bib if the transplanted text cites keys absent
there — that file may be edited for this purpose only; list every added
key). Thesis sentence and RQ titles present. Report every section
replaced and every bib key added in write-report.md in THIS directory.
Leave everything uncommitted.
