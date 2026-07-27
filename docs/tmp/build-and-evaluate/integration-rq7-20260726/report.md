# RQ7 + Held-Out Conformance Integration Report

Date: 2026-07-26

## Scope and revision strategy

The paper keeps RQ1--RQ6 scientifically and textually unchanged.  The edit
appends one workload question, RQ7, and treats measurement capability as the
same separate tool question as before.  The opening now describes the study as
six longitudinal questions plus one workload question.  In the abstract and
introduction, only the scope sentence, result synopsis, and contribution
summary were updated; their argument order and existing citations were
preserved.

The body edit is question-led and answer-closing.  It asks about composition,
repetition, dependency, and waiting structure; reports the requested
observation and opportunity bounds; and closes by limiting them to structural
bounds rather than realized performance or utility effects.  The supplement
organizes the same estimators into three groups: composition/repetition/timing,
existing/remaining concurrency, and prediction/speculation/event-driven
control.

## RQ7 locations

- RQ overview: `docs/paper/main.tex:239`.
- Main evidence block: `docs/paper/main.tex:399`.
- Supplement RQ wording: `docs/paper/supplement.tex:429`.
- Full estimator definitions and results:
  `docs/paper/supplement.tex:936` (`RQ7: Tool-Call Workload and Optimization
  Bounds`).
- Abstract count wording: `docs/paper/main.tex:43` and
  `docs/paper/supplement.tex:47`.

The main block reports:

- shell calls: 68.6% (observation bound);
- same-prompt, stream-local repeated artifact-identity reads: 46.7%
  (observation bound);
- exact shell-command reruns: 15.4% (observation bound);
- native overlap: 42,679/49,612 = 86.0256%, rounded to 86.0% of
  logical-parallel edges (observation bound);
- actionable chronological next-read prefetch precision: 21.75%
  (opportunity bound);
- same-handle event-driven polling removal: at most 1,456 calls
  (opportunity bound); and
- between-tool gaps: 74.83%, rounded to 74.8% of timing-complete episode span
  (observation bound).

The first three values are checked against
`toolcall-behavior-20260726/report.md`; the remaining four are checked against
`toolcall-profile-20260726/report.md`.

## Conformance changes

- Main held-out paragraph: `docs/paper/main.tex:454`.
- Main validity limitation: `docs/paper/main.tex:494`.
- Complete supplement section:
  `docs/paper/supplement.tex:1044` (`Root-Disjoint Held-Out Conformance`).
- All 116 item-level oracle/trajectory decisions:
  `docs/paper/supplement.tex:1058`.
- Full four-ledger summary: `docs/paper/supplement.tex:1099`.
- Non-pooling and no-general-conformance boundary:
  `docs/paper/supplement.tex:1136`.

The integrated result is the preregistered 70-root/116-question held-out
corpus, with B+C = 54/58.  Attempted-edge precision/recall/F1 is
0.9906/0.9995/0.9950; confirmed-effect-edge precision/recall/F1 is
0.9903/0.9995/0.9949.  The paper reports the four B errors and 20 row-level
edge differences as a compound shell/wrapper path-admission boundary.  These
values and the seven-call localization were checked against both
`rq7-heldout-20260726/v2/result.md` and `result-review.md`.

The older 60/60 remains explicitly labeled repair-corpus regression evidence.
It is not pooled, rescaled, or denominator-matched with 54/58, and neither
result is presented as general exact conformance.

## Build and submission gates

- `latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex`: pass.
- `latexmk -pdf -interaction=nonstopmode -halt-on-error supplement.tex`: pass.
- Undefined references/citations: 0 in both final logs.
- Main PDF: 7 pages total; page 7 begins `References`, so the main content is
  6 pages (gate: at most 7).
- Supplement PDF: 20 pages.
- Citation-command count across the two entry points: 28, unchanged.
- `git diff --check`: pass.
- RQ1--RQ6 question and evidence text: unchanged.

## Commits

- Held-out v2 public artifacts and fixture audit outputs:
  `c8447f192ef60d74a9efa2a193e734172a2e6460`.
- RQ proposal document:
  `9d927c36ba58deab1662d53956d2a4d487a99e0c`.
- Paper, supplement, PDFs, and this report:
  the commit containing this report, with subject
  `research: integrate RQ7 and held-out conformance`.

The third commit cannot embed its own immutable hash without changing that
hash.  Its exact hash is therefore recorded in the post-commit handoff; from
this checkout it is also `git rev-parse HEAD`.

## Remaining risks

No evidence gap remains for the requested integration.  The substantive
limitations are those stated in the paper: opportunity estimates are not
implemented performance results; 49.47% of adjacent edges have unknown
semantic dependence; and held-out exact conformance fails at compound
shell/wrapper path admission.
