# Round 8 — Terminology and Claim Tone

## Scope

This round applied `check-terminology-infoflow` to the paper and its scientific
contract documents. It treated the paper's fixed vocabulary as authoritative:
four pathologies, five evidence conditions, one retrospective-intervention
output protocol, and one offline supervisor-agent consumer.

## Independent review and disposition

The independent reviewer reported 11 must-fix, 12 should-fix, and 3 consider
items. All 11 must-fix items were accepted. The root pass synchronized
`docs/paper/main.tex`, `docs/idea-story.md`, `docs/design.md`,
`docs/implementation.md`, and `docs/evaluation.md`.

The resulting contract is:

- pathologies: `stagnation`, `goal drift`, `validation gap`, and `harness waste`;
- conditions: `Workspace Trajectory`, `Raw Retrieval`, `Final State`,
  `Native Report`, and `Counts`;
- intervention output: whether intervention was warranted plus the earliest
  source action supporting that retrospective recommendation;
- evaluated consumer: an offline supervisor agent performing automatic
  diagnosis; humans only construct and adjudicate gold;
- representation boundary: deterministic actions, projected effects,
  lifecycle, transitions, candidate checks, activity counts, and source
  provenance; pathology, intent, harness attribution, and intervention remain
  supervisor outputs;
- implementation boundary: ingestion, action-time repository projection,
  optional source-call provenance, and media export are implemented; goal
  episodes, snapshots, diagnostic indexes, queries, and matched-condition
  runner remain planned.

The pass also mapped the motivating table to three named evaluation conditions,
defined candidate-validation before query use, removed `attention` as an
inferred representation-level quantity, and changed all executed-sounding
future claims to proposal or planned-evaluation language.

Rejected suggestions were those that would add a human-usability claim, turn a
candidate check into verified validation, infer causality from temporal
adjacency, replace action time with Git time, or insert system evidence into the
fixed native-evidence comparison.

## Validation

- `latexmk -pdf -interaction=nonstopmode main.tex`: pass;
- PDF length: 8 pages; all main content ends on page 7 and references start on
  page 8;
- abstract: exactly 200 words;
- citations: 20 citation commands;
- no overfull boxes, undefined references, undefined citations, or LaTeX errors;
- `git diff --check`: pass.

Exit `main.tex` SHA-256:
`9d79fb1d60ca1fe9e09840ae7857cd9a6f86ce0be9aa59edd40424b31c248cbd`.
