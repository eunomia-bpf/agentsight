# Review spec: AAAI-27 review of the submodule paper (current working tree)

Target: docs/agentpprof-paper/main.tex (uncommitted working state) and its
compiled main.pdf in /home/yunwei37/workspace/agentsight-research-semantic-flamegraph.
READ-ONLY everywhere except writing your review file. No git commands that
modify state; no git stash.

Act as a rigorous AAAI-27 reviewer plus format checker.

## Part A — AAAI submission compliance

Template usage (aaai2027, submission mode, anonymity), page budget
(7 pages main content + up to 2 pages references), forbidden packages or
commands, figure/table placement and caption conventions, citation style
(natbib authoryear), reproducibility-checklist expectations. Report each
as pass/fail with the exact location.

## Part B — scientific review (AAAI style)

Summary, strengths, weaknesses, and a score in {reject, weak reject,
borderline, weak accept, accept}. Attack specifically:
- internal consistency: abstract/intro claims versus the rewritten
  Design/Algorithms/Implementation/Evaluation (the abstract retains
  older numbers by design — flag every specific mismatch precisely);
- number traceability within the document (every eval number is
  self-consistent across prose and tables);
- whether the Evaluation supports the four RQ answers as stated;
- figure-text alignment (the one flame-graph figure vs prose);
- undefined/dangling references, duplicate labels, bib entry quality.

## Deliverable

eval-review.md in THIS directory: compliance table, mismatch list with
line numbers, top-5 reviewer attack points with quoted sentences, and the
overall verdict. Factual and specific; no generic advice.
