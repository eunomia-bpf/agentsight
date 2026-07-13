# Round 2 — Section Conventions

**Started:** 2026-07-12T14:45:00-07:00  
**Completed:** 2026-07-12T14:55:00-07:00  
**Cycle/gate:** cycle 0001 / WRITE  
**Parent:** `iter-refine-writing-20260712T141013-0700`

## Review Method And Findings

A fresh read-only subagent invoked section-convention review. It found the
three-RQ overview, one evidence block per RQ, experiment subordination,
four-group Related Work, Limitations placement, one-paragraph Conclusion, and
7+2 structure correct. Must-fix writing findings concerned abstract sentence
roles, exact abstract/Introduction number correspondence, and an overlong split
Introduction system/evaluation preview. Scientific must-fix findings were the
still-unanswered RQ1 lineage, RQ2 real decision/end-to-end cost, and RQ3
unchanged-transfer experiments, plus missing controlled timing metadata.

## Applied Writing Fixes

- Reduced the abstract to nine role-aligned sentences and 209 words. Combined
  model and implementation, added explicit evaluation scope, and consolidated
  public negative results with the synthesis. No number or qualifier changed.
- Rebuilt the Introduction's “this paper” material as one five-sentence block
  containing system, evaluation scope, local result, public results, and honest
  boundary. It now carries the exact Hodoscope values `2.9 +/- 0.3` and
  `24.9 +/- 15.8` from the abstract. Secondary mapping details remain only in
  Evaluation.
- Replaced prose contribution routing with actual section references.
- Made the three Design requirements traceable in plain language—evidence
  preservation, explicit accounting, and auditable drilldown—without adopting
  new G1/G2/G3 terminology. Explicitly states that RQ1 has not yet verified
  lineage.
- Added a compact Setup statement that controlled release hardware/software and
  warm-up metadata are absent and require rerunning before a performance claim.
- Replaced the process-facing final Limitations sentence with the scientific
  conclusion that current evidence does not authorize general causal,
  decision-value, transfer, or performance claims.
- Refocused Discussion on the implication of profiling beyond debugging and
  moved the formal evidence-gap inventory to Limitations.
- Broadened the localization Related Work topic sentence to agent behavior
  diagnosis and labeled trajectory benchmarks.
- Added one context sentence to the Introduction opening so it follows the
  three-sentence full-paper convention.

The suggestion to add code size/platform metadata was not applied because no
verified compact artifact record was provided in this writing round. It remains
an implementation-document check, not a value to estimate.

## Scientific Routing

WRITE cannot close the fixed RQs. RQ1 requires independently recorded native
tool/span and process lineage; RQ2 requires a real directly recorded additive
change with matched flat/native/semantic views, effort, and total cost; RQ3
requires an unchanged mapping and stack on an untouched family. Controlled
hardware/software, warm-up, repetitions, CPU, memory, time, storage, and capture
overhead must accompany the affected cost rerun. The paper continues to state
these gaps rather than masking them.

## Preservation And Verification

All 57 citation commands, all RQ meanings, all numbers, and the exact thesis
were preserved. `make` completed with exit code 0. The PDF remains nine
US-Letter pages; Conclusion is on page 7 and pages 8--9 contain references
only. Round 3 next checks whole-paper logic flow.
