# Round 1 — Micro-structure

- Time: 2026-07-14T06:48:07-07:00
- Branch: `research/semantic-flamegraph-artifacts-v2`
- Entry commit: `a95cbab73e52d916c0b4df626e7d3c4c33429e80`
- Reviewer method: full-paper paragraph-role and sentence-flow review using `check-paper-structure-flow`
- Scope contract: writing structure only; no thesis, RQ, claim-meaning, contribution, experiment, or number change

## Reviewer findings

### Must fix

1. The abstract was approximately 251 words in 12 sentences. Compress it to 7–9 sentences while preserving the complete problem, thesis, model, system, and measured results.
2. Introduction paragraph 6 mixed the system mechanisms with four evaluation previews in one long paragraph. Split the mechanism description from the evaluation preview.

### Should fix

1. Consider reordering the introduction so the problem, root cause, and existing-solution gap appear before the profiling solution.
2. Make the evaluation overview announce the fixed R114 suite as well as the three broader data classes.
3. Split the operation-stack definition from the formal view/projection definition.
4. Place the flame-graph interpretation with the granularity/weight evidence and interpret the automatic-construction result.
5. Mark the six-task automatic RQ2 result as auxiliary and keep it distinct from the three primary public workloads.
6. Close RQ3 explicitly as a partial answer and name the still-open tag components.
7. Split the System Profiling paragraph before the paper-specific contrast with agent trajectories.
8. Rename `Field derivation and boundaries` because boundary construction already has its own implementation paragraph.

### Consider

1. Add another sentence to the first introduction paragraph.
2. Reorder Stack Construction to lead with motivation rather than supported inputs.

## Root disposition

### Applied

- Rebuilt the abstract as nine sentences and 198 prose words. It still contains the exact thesis, all RQ1 lineage numbers, all RQ3 numbers, and the RQ4 cost number.
- Inserted a paragraph boundary between the system mechanisms and evaluation preview in the introduction.
- Changed the evaluation overview to state that the fixed R114 real-Codex suite is used alongside three broader data classes.
- Split the operation-stack discussion before the formal view triple and added a direct topic sentence about selection and weighting.
- Moved the existing flame-graph sentence into `Granularity and weights`; added a one-sentence interpretation of automatic construction without changing its result.
- Labeled the six-task RQ2 result an auxiliary no-configuration check and distinguished it in the RQ2 answer.
- Added a `Partial answer` paragraph to RQ3 and linked it to the existing scope statement for task, phase, and action accuracy.
- Split System Profiling before the agent-specific contrast.
- Renamed the implementation paragraph to `Field derivation`.

### Rejected

- Rejected the optional introduction reorder. The restored canonical story already proceeds from user problem, through existing-tool gap, to the agent-specific challenge and profiling thesis. Reordering it again would create narrative churn without correcting a defect.
- Rejected an extra first-paragraph sentence. The two-sentence context paragraph is complete and the added sentence would delay the problem.
- Rejected a motivation-first rewrite of Stack Construction. Its present direct/manual/group/automatic progression is a clear interface-to-fallback sequence, and a rewrite would not materially improve comprehension.

## Preservation audit

- Thesis remains exactly: “Agent observability needs profiling, not only debugging.”
- Fixed RQs remain attribution, problem correspondence, tag accuracy, and profiling cost.
- RQ1 remains a positive cumulative answer; RQ3 remains the only explicitly partial answer.
- No experimental protocol, baseline, metric, dataset, or measured value changed.
- The auxiliary RQ2 values `0.276`, `0.312`, and `65.3%` remain present.
- Citation commands remain 52.

## Build verification

- `pdflatex` completed after bibliography and cross-reference convergence.
- Final PDF: 9 pages total (7 content pages plus 2 reference pages).
- Undefined citations: 0.
- Undefined references: 0.
- `git diff --check`: clean.
- Exit `main.tex` SHA-256: `a5059c76600c0698a5a84e1a656a11edd76a5fc80171bb4dd0ff8270c84b0b96`.
- Exit `main.pdf` SHA-256: `d0c0c5a80782f9db6e1cd389ba0ae3aec13ab2f97e9655faa60766127fd5f83a`.

## Round decision

PASS. Proceed serially to the section-conventions round.
