# P2 Raw Baseline Paper Integration

## Scope

This integration replaces only the obsolete bounded-Raw N/A treatment.  It
uses the frozen fixed-reader, fixed-corpus interpretation, keeps the comparison
mixed/inconclusive, makes no Trajectory superiority, necessity, speed, or cost
claim, and leaves State Diff, Session Local, and OCPM Features as N/A.

## Modified locations and result provenance

- `docs/paper/main.tex:209-213` changes the capability-protocol status from an
  unexecuted Raw branch to the terminal 360-row matrix.  Source:
  `result.md:5-8` and `result.md:148-159`.
- `docs/paper/main.tex:420-422` scopes the existing figure to the deterministic
  conditions and points to the separately evaluated bounded Raw reader.
  Source: `result.md:84-104`.
- `docs/paper/main.tex:426-433` reports 191/360 (53.1%) overall, 94/180 (52.2%)
  B+C, 260/360 (72.2%) scoreable, 191/260 (73.5%) scoreable-row exact, and
  5/18 cells at the preregistered 1 MiB tool-return limit; it also records the
  frozen claim boundary and the three unchanged N/A conditions.  Source:
  `result.md:10-15` and `result.md:148-163`.
- `docs/paper/supplement.tex:367-373` replaces the obsolete incomplete-matrix
  statement with the terminal 360-row Raw denominator and fixed-reader,
  fixed-corpus scope.  Source: `result.md:5-8` and `result.md:148-159`.
- `docs/paper/supplement.tex:856-863` reports the same four Raw measurements,
  5/18 cap-triggered cells, mixed/inconclusive interpretation, prohibited
  claims, and unchanged historical N/A conditions.  Source:
  `result.md:10-15` and `result.md:148-163`.
- `docs/paper/supplement.tex:868-874` scopes the existing figure to the
  deterministic matrix and points to the separate bounded-Raw protocol.
  Source: `result.md:84-104`.
- `agentvis/research/rq7_measurement.py:3848` and the regenerated
  `docs/paper/figures/rq7-measurement-capability.{pdf,png}` remove the obsolete
  Raw=N/A footer while leaving all plotted deterministic values unchanged.
  Source: `result.md:84-104` and `result.md:148-159`.

## Validation

- `latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex`: passed.
- `latexmk -pdf -interaction=nonstopmode -halt-on-error supplement.tex`:
  passed.
- Neither LaTeX log contains an error, undefined citation, or undefined
  reference.
- `main.pdf`: 7 pages total; page 7 is References, so main content is 6 pages.
- `supplement.pdf`: 17 pages total.
- Citation commands: 28 before and 28 after; the paper diff removes none.
- The rebuilt PDFs contain all four requested Raw measurements and the 5/18
  cap disclosure, and contain no Raw=N/A statement.

## Commits

- Experiment outputs:
  `ec781d8781b34267ce40035b6a212398c8f160bc`
  (`research: add bounded raw baseline results`).
- Paper integration: this report is included in the paper-integration commit;
  its exact hash is reported in the final handoff.
