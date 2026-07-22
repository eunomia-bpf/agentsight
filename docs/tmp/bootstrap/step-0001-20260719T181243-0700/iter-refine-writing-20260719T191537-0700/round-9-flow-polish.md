# Round 9 — Flow Polish

## Scope

This round applied a final paragraph- and sentence-flow audit without changing
the RQs, evidence conditions, pathologies, equations, citations, implemented
status, or automatic-diagnosis-only scope.

## Independent review and disposition

The independent reviewer found no macro-structure defect and reported 4
must-fix, 9 should-fix, and 3 consider items. All four must-fix items were
accepted:

- replaced an ambiguous intervention pronoun with the exact `earliest
  supporting action` output;
- restored the query-interface lead-in by moving the candidate-validation
  definition after the list and explicitly connecting it to validation
  retrieval;
- reordered corpus admission as partition definition, label-independent
  admission, boundary/snapshot freezing, grouped splitting, then labeling and
  enrichment reporting;
- completed the fixed five-condition fairness contract before introducing the
  separate AgentRx/TrajAudit subset.

The pass also made contribution bullets parallel, bridged implemented source
affiliation to planned episode construction, removed a repeated `However`,
compressed repeated requirement prose, and introduced scalability as an
additional RQ1 decision rule. It retained the RQ roadmap, walkthrough, result
placeholders, and all three `Unanswered` gates because each carries distinct
protocol or evidence-boundary information.

## Validation

- `latexmk -pdf -interaction=nonstopmode main.tex`: pass;
- PDF length: 8 pages; all main content ends on page 7 and references start on
  page 8;
- abstract: exactly 200 words;
- no overfull boxes, undefined references, undefined citations, or LaTeX errors;
- `git diff --check`: pass.

Exit `main.tex` SHA-256:
`bf81d85782851402498e6c6ca8f88e0212a901b9b1ab3180e8b7e36122b8c810`.
