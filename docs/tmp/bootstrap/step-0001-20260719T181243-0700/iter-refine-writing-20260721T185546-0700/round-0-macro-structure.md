# Round 0 — Macro Structure

## Independent review

Reviewer: `writing_round0_macro` (read-only).

Verdict: no scientific-contract violation in the Evaluation body. The reviewer
identified one abstract mismatch (two conditions described where RQ1 has four),
an Evaluation structure that did not expose one evidence block per RQ, a
missing standalone insight paragraph, design requirements placed outside
Design, and excessive section fragmentation for a six-page paper.

## Applied changes

- named No Intervention and Generic in the abstract;
- separated the scientific hypothesis from the system description;
- added section pointers to the contribution list;
- moved checkpoint execution formalism into Evaluation;
- moved continuity, fidelity, bounded scalability, and fairness into Design;
- consolidated Design and Implementation headings;
- reorganized Evaluation into shared protocol followed by explicit RQ1, RQ2,
  and RQ3 subsections;
- stated separately that RQ1 remains unanswered, RQ2 was not admitted, and RQ3
  remains unanswered;
- required a frozen separation between RQ1 task families and held-out RQ3
  families; and
- folded the repetitive Discussion content into Limitations.

## Validation

- `latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex`: PASS
- compiled length: 6 pages
- undefined citations/references: none reported
