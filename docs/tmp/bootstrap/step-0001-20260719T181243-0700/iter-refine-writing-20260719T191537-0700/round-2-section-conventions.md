# Round 2 — Section Conventions

Started: 2026-07-19T19:40:59-07:00
Completed: 2026-07-19T19:48:58-07:00
Parent: BOOTSTRAP step 0001 / WRITE_GATE
Objective: make every section fulfill the expected AAAI full-paper role without upgrading the protocol into a completed empirical contribution.

## Baseline and method

Round 2 began from `main.tex` SHA-256 `fc724112f6d1df561b71751a252ef533dc3f80bb1baea00707e085d3fb3c95c6`. A fresh read-only reviewer checked the complete draft against the full-paper and abstract/Introduction conventions in `check-paper-structure-flow`. The root applied convention-only fixes and preserved every visible evidence placeholder.

## Findings

Must-fix issues were incomplete abstract/Introduction correspondence, problem evidence in the background paragraph, taxonomy drift between Motivation and RQ1, missing exact reproducibility fields, and the necessarily incomplete result blocks. Should-fix issues were Design/Implementation leakage, no Implementation mapping paragraph, no Requirements-to-Design handoff, contribution bullets without section references, RQ-name drift, mixed title capitalization, table narration after rather than before the float, a narrow code-centric Discussion, and unstable names for the automatic consumer.

## Applied fixes

1. Standardized the consumer as an `automatic diagnoser/supervisor Agent` on first mention and `supervisor Agent` thereafter.
2. Kept the first Introduction paragraph as workload background. Moved plan loss and long-lived reliability failures into the problem paragraph before its transient-session/durable-workspace root cause.
3. Mirrored the deterministic, no-generated-label boundary and fixed four-pathology scope in the Introduction system paragraph.
4. Added section labels and references from all three contribution bullets.
5. Reduced the Problem section's goal episode to its semantic definition; moved parent/delegation, half-open boundary, and concurrent-different-goal policy to Implementation.
6. Introduced Table 1 in the motivating narrative before its environment.
7. Added an explicit Requirements-to-Design bridge and mapped continuity, evidentiary fidelity, and fair bounded comparison to Design mechanisms.
8. Removed parser implementation language and literal command names from Design. Kept conceptual query families there and concrete API names in Implementation.
9. Added an Implementation opening that maps its three components to the three requirements.
10. Aligned overview and evidence-block names for RQ1 `Diagnostic Utility`, RQ2 `Information Contribution`, and RQ3 `Harness Diagnosis and Generalization`.
11. Defined RQ1 over the exact stagnation, goal-drift, validation-gap, and harness-waste taxonomy plus intervention need. RQ3 retains the deeper harness-mechanism and grouped-generalization tests.
12. Added a visible reproducibility placeholder for model revision, decoding, repetitions, environment, budgets, evaluator revisions, and seeds.
13. Added a bounded Discussion paragraph on non-code artifacts while stating that transfer requires held-out RQ3 evidence.
14. Standardized subsection capitalization.

## Explicitly unresolved

The full-paper result blocks, empirical contribution, implementation measurements, direct RQ answers, and outcome-aware conclusion remain unresolved. This is intentional: the prior experiment proposal is closed, not approved. No amount of prose review can satisfy these evidence requirements; a newly admitted experiment is required.

## Preservation audit

The fixed RQs, pathology meanings, comparison conditions, model/evidence-budget control, human-labeling role, and exclusion of human-interface outcomes are unchanged. The citation count remains 20 across 12 verified references. The abstract is 200 words by the round's conservative text count, within the 200--300-word convention without adding an unsupported claim.

## Validation

- Official-template `latexmk`: success after cross-reference convergence.
- PDF: 7 pages, 244,036 bytes.
- No overfull box, negative label-width, undefined citation, or undefined reference warning.
- `git diff --check`: success.
- Exit `main.tex` SHA-256: `8b3b8de5c663e908e06683b83b1ae24be5ef99ebc9189bc6980ff10a2ffdb441`.

## Next node

Round 3 reviews whole-paper logical progression and cross-section handoffs. It may tighten causal language or expose missing bridges, but it must not reinterpret a protocol as a result.
