# Round 7 — Word Choice

## Scope

This round applied the word-choice pass from `paper-writing-style`. It kept the
scientific contract, evidence status, fixed pathology names, five condition
names, equations, citations, and result placeholders unchanged.

## Independent review and disposition

The read-only reviewer reported 10 must-fix, 22 principal should-fix, 17
additional concise improvements, and 3 consider items. The root pass accepted
all 10 must-fix items, all principal should-fix items that preserved the paper
contract, and the concise corrections that removed report-like or ambiguous
phrasing.

The highest-impact changes were:

- standardized the evaluated consumer as an `offline supervisor agent` that
  performs automatic diagnosis, replacing the ambiguous
  `automatic diagnoser/supervisor Agent` role;
- replaced opaque phrases such as `preclude a generic novelty claim`,
  `action namespace`, `query surface`, and `verbose streams` with direct
  scientific descriptions;
- corrected subjects and verbs in the external-baseline and episode-admission
  descriptions;
- replaced ambiguous goal-drift and retrospective-intervention wording with
  evidence-bounded definitions;
- standardized generic `agent` capitalization and tightened the abstract and
  conclusion without weakening positive or null-result branches.

The round retained `inductive bias`, `evidentiary fidelity`, and `grounding
veto`: each is standard research terminology and the paper explicitly defines
the fixed-budget mechanism or threshold consequence. It also retained the
artifact field name `source_call_id` and visible unanswered/result markers.

## Validation

- `latexmk -pdf -interaction=nonstopmode main.tex`: pass;
- PDF length: 8 pages; all main content ends on page 7 and references start on
  page 8;
- abstract: exactly 200 words;
- citations: 20 citation commands, unchanged;
- no overfull boxes, undefined references, undefined citations, or LaTeX errors;
- `git diff --check`: pass.

Exit `main.tex` SHA-256:
`684575500beb00b9cd68179911c530ab4f3357ff1be20a85406d21c61a2ac2e9`.
