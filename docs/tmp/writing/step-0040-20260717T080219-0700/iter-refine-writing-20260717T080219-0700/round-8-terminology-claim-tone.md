# Round 8 — Terminology and Claim Tone

## Node identity

- **Started:** 2026-07-17T14:19:00-07:00
- **Completed:** 2026-07-17T14:27:00-07:00
- **Parent:** Step 0040 WRITE gate
- **Procedure:** an independent read-only subagent re-read and explicitly
  applied the complete `check-terminology-infoflow` and `paper-writing-style`
  skills to the complete paper. The root applied the bounded findings and
  rebuilt the manuscript. Neither agent performed a Git operation.

## Independent verdict

The reviewer returned **0 must-fix, 4 should-fix, and 2 consider** findings.
It explicitly passed the concept budget, system-name macro, operation/action/
tag/group distinction, protocol-specific input boundaries, standard metric
names and citations, exact thesis, four-RQ order, original story, quantitative
evidence, and all development/post-hoc/fixed-input qualifiers.

## Accepted changes

1. The Abstract no longer introduces its mechanism list with an unnumbered
   colon; all mechanisms remain present.
2. The Evaluation contribution now uses three direct sentences and consistent
   terms: “integrated task-family path” and “standalone action-label adapter.”
   It no longer shifts between declared-task path, backend, and backend-level
   adapter labels.
3. The RQ2 endpoint now states the positive measured result directly:
   semantic grouping improves MAP over matched raw-action grouping on all three
   complete workloads. It then states the bounded mechanism claim as a tie-
   breaking refinement rather than a replacement for operation-local scores.
4. The four-RQ evidence synthesis was split into two grammatical comparisons;
   the final thesis synthesis remains unchanged.
5. The one-off compound “responsibility-partition agreement” in the RQ1 table
   caption became “agreement with human responsibility partitions.”
6. Related Work now spells out conservation of user-selected additive measures
   instead of the opaque phrase “conserved selectable measures.”
7. Corresponding Chinese contribution and RQ2 comments were synchronized.

No new term, mechanism, result, metric, or claim was introduced.

## Explicit consistency passes

- `operation` remains the uniform weighted record; `action` remains a visible
  field/value; `tag` remains an operation field; group, partition, and boundary
  remain structural outputs measured by their respective standard metrics.
- `label-free recurrence` remains the default automatic constructor, while
  `reference-calibrated recurrence` remains explicitly optional and annotation-
  dependent.
- RQ3 no longer applies a blanket target-blind claim to the action adapter;
  only the protocols with that input boundary use the term.
- Ordinary B$^3$, AP/MAP, macro-F1/accuracy, V-measure, and exact boundary
  precision/recall/F1 remain the paper-facing outcome families. No custom
  weighted, cutoff-budget, or model-reader metric appears.

## Build and format verification

The final LaTeX pass produces nine US-Letter pages, with the complete main text
ending on page 7 and references beginning on page 8. There is no undefined
citation/reference, multiply-defined label, or overfull warning. The standard-
metrics exclusion search remains clean.

## Status and next node

Round 8 is complete. Round 9 performs the final sentence-flow pass under
`paper-writing-style`, concentrating on paragraph transitions rather than word
choice or terminology.
