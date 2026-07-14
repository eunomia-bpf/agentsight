# Round 4 — Abstract and Introduction Rebuild

- Skill: `rewrite-abstract-intro`
- Invocation: required inside `iter-refine-writing`; plan recorded here instead of pausing
- Source of truth for this round: complete current paper body
- Scope contract: move and tighten existing opening content only; do not change thesis, four RQs, claims, evidence, citations, numbers, terminology, or contributions

## Pre-edit mapping diagnosis

### Introduction

| Current block | Current role | Target role | Plan |
|---|---|---|---|
| ¶1 | Background and accumulated trajectories | ¶1 Background | Keep. |
| ¶2 | Problem plus two profiling-solution sentences | ¶2 Problem | Keep the problem and cost; move the two profiling sentences to the insight paragraph. |
| ¶3 | Existing tools and limitation | ¶4 Existing solutions | Move after the structural root cause; keep citation and limitation intact. |
| ¶4 | Structural reason profiling does not transfer | ¶3 Root cause | Move before existing tools; rename the comment only. |
| ¶5 | Exact thesis plus model details | ¶5 Insight | Keep exact thesis first; add the moved traditional-profiling sentences as support; retain the existing model explanation. |
| ¶6 | System, mechanisms, and fixed-RQ evidence preview | ¶6 This paper | Keep content and result order. |
| ¶7 | Three concrete deliverables | ¶7 Contributions | Keep. |

Diagnosis: all required content exists, but the structural cause follows existing solutions and the problem paragraph ends with the solution. The minimal repair is movement, not a new idea or story. A separate ¶5b challenges paragraph is unnecessary because the structural transfer challenges are the root cause and the mechanisms are simple.

### Abstract

| Current sentence | Current role | Issue | Plan |
|---|---|---|---|
| S1 | Background | None | Keep role. |
| S2 | Problem | None | Keep role. |
| S3 | Traditional profiling plus existing-tool limitation | Maps to two intro paragraphs | Split correspondence through re-derivation. |
| S4 | Root cause | Appears after existing solutions | Move before existing solutions. |
| S5 | Exact thesis | None | Keep verbatim. |
| S6 | Model plus system | Maps to insight and system paragraphs | Separate model from system. |
| S7 | RQ1 result | Result without an evaluation-setup sentence | Derive a methodology sentence first. |
| S8 | Broader RQ2/RQ3 results | None scientifically | Fold into one final result sentence with the other key results. |
| S9 | RQ4 cost | Fragmented final result role | Fold into the final result sentence. |

Target: eight sentences in strict intro order—background, problem, root cause, existing-solution limitation, exact thesis/model, system, evaluation setup, and key results. Every clause and number will come from the current introduction and body.

## Reorganization authorization

Proceeding without a human pause because this skill is running inside the serial `iter-refine-writing` loop. The edits are structural only and preserve the restored scientific story.

## Applied reorganization

### Introduction

1. Kept the two-sentence background paragraph unchanged.
2. Removed the two profiling-solution sentences from the problem paragraph, leaving the cross-trajectory questions and inspection/evaluator cost as the problem.
3. Moved the existing two-challenge paragraph before existing tools and labeled its role as structural root cause. Tightened one pair of sentences without changing the two properties.
4. Moved the existing-tools capability/limitation paragraph after the root cause and made its limitation part of the same topic sentence.
5. Kept the exact thesis as the first sentence of the insight paragraph. Moved the traditional-profiling explanation here and compacted the already-defined operation and operation-stack model into the same paragraph.
6. Changed the system paragraph's topic sentence from “We implement” to “We present,” retaining the same offline-profiler and pprof claim. Added one methodology sentence that enumerates only evaluation populations and sizes already reported in the paragraph/body.
7. Left the three-contribution list scientifically unchanged.

No citation was removed or moved out of the Introduction.

### Abstract derivation

Derived an eight-sentence abstract from the reordered Introduction:

1. accumulated agent trajectories ← Introduction background;
2. cross-trajectory quality/safety/cost questions ← problem;
3. stable function/call-nesting mismatch ← root cause;
4. current agent-tool limitation ← existing solutions;
5. exact thesis ← insight;
6. \sys and semantic operation stack mechanisms ← this paper;
7. evaluation populations and conditions ← methodology;
8. existing RQ1/RQ2/RQ3/RQ4 evidence ← results.

The abstract is 214 prose words. Its long final sentence is intentional in this round because the required template assigns key results to one sentence; later style rounds may improve clause readability without changing the sentence-role mapping or evidence.

## Source-fidelity audit

- Exact thesis unchanged and still appears in Abstract, Introduction, and Conclusion.
- All four fixed RQs unchanged.
- Abstract numbers all appear in the Introduction and Evaluation.
- No number, claim, mechanism, citation, dataset, metric, or comparison was invented.
- Citation commands remain 52, so the count did not decrease.
- Scientific story remains the restored profiling thesis; only the causal order is now explicit.

## Abstract-to-Introduction correspondence check

PASS. Each abstract sentence maps to exactly one Introduction role in the same order. The system and methodology sentences both derive from the This Paper paragraph, as permitted by the template. No abstract concept is absent from its source paragraph.

## End-to-end logic check

PASS:

`accumulated trajectories → cross-run analysis problem → semantic-identity and hierarchy root cause → current-tool limitation → profiling thesis and semantic operation stack insight → \sys mechanisms → evaluation populations → measured results → concrete contributions`.

The insight answers both named structural properties, and the two system mechanisms answer stable tagging and stack construction. The Step 0007 lineage evidence remains owned by the R114-compatible AgentSight path followed by current \sys folding.

## Build verification

- `make` and final `pdflatex` completed.
- PDF: 9 pages total (7 content plus 2 references).
- Citation commands: 52.
- Undefined citations/references: 0.
- `git diff --check`: clean.
- Exit `main.tex` SHA-256: `3119b7e360d026971d8570edb6b32ba89b1c4cf6b2422cabfda73575cff930a2`.
- Exit `main.pdf` SHA-256: `5eb4fb1fb1615e3d5701b75b4a9bf0c461aad9ffbdf664d822fd83353148fb37`.

## Open items

None requiring new evidence or body-section work.

## Round decision

PASS. Proceed serially to the cross-paper consistency round.
