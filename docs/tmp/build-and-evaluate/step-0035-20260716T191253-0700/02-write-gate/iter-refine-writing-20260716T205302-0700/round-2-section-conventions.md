# Round 2 — Section Conventions

**Started:** 2026-07-16T21:23:00-07:00

**Completed:** 2026-07-16T21:33:16-07:00

**Parent:** Step 0035 `WRITE_GATE / EVIDENCE INTEGRATION`

**Objective:** Check every paper section against its role convention and repair
the rendered section-level reading order without changing the fixed thesis,
four RQs, scientific meaning, algorithm, citations, or numbers.

## Review Method

The fresh independent reviewer explicitly invoked `check-paper-structure-flow`
for Round 2 and read its full-paper and abstract/intro references. It read the
complete current LaTeX source, all nine rendered pages, and the Round 0/1
reports. It edited no file, ran no experiment, and performed no Git operation.

## Raw Findings

### Must-fix

1. RQ3 remains scientifically incomplete: literal phase-label accuracy has no
   direct evidence, and the current group-boundary test is session-held-out
   within OSWorld-Human rather than family-held-out. This belongs to the outer
   EXPERIMENT gate and cannot authorize a writing-only RQ or thesis change.
2. The contribution section references render as empty text under the
   unnumbered AAAI style: `(Sections and )` and `(Section )`. Replace numeric
   `\ref` forms with direct section names; do not alter the official style.
3. Figure 2 interrupts the Design opening's D1--D3 mapping in the rendered
   two-column reading order. Place it after the complete mapping and four-stage
   overview without floating into an unfinished sentence.
4. The Introduction puts the CodeTraceBench token sensitivity after RQ2 and
   OSWorld results, so `the same comparison` has the wrong nearest antecedent.
   Move it directly after the CodeTraceBench result and name that comparison.

### Should-fix

1. Compress the 233-word, 13-sentence abstract to the required 7--9 role
   sentences while retaining the exact thesis and RQ1--RQ4 headline evidence.
2. Close the formal view definition: make clear that the four built-ins choose
   the selection and weight functions while stack fields remain independently
   selectable.
3. Add one short Background/Motivation-to-Design bridge after D1--D3.
4. Make the Figure 1 body reference name all three displayed views: tokens,
   time, and files.
5. Decompose the dense novelty wording in the Introduction and Related Work
   into source linkage followed by semantic additive aggregation.

### Consider

- Rename the generic `Algorithms` subsection to `Attribution and Stack
  Construction`.
- Figure 1 is still at the top of page 3 before a continued D1 passage. It no
  longer interrupts the thesis/model paragraph; move it only if later layout
  work can improve this without adding a page.
- Related Work and Conclusion now satisfy their conventions; do not expand them
  mechanically.

## Target Outline Before Edits

Edits will be applied one subsection at a time:

1. **Abstract:** derive exactly nine sentences in the existing causal order:
   background; problem; profiling/root cause; existing-tool gap; exact thesis;
   model/system; RQ1 evidence; RQ2+RQ3 evidence; RQ4 cost.
2. **Introduction:** move the token-sensitivity sentence next to CodeTraceBench,
   simplify the existing-tool gap, and replace empty contribution references
   with direct section names.
3. **Background and Motivation:** add the one-sentence D1--D3 bridge.
4. **Design:** close the view triple, rename the algorithm subsection, and make
   Figure 2 non-floating after the complete opening explanation.
5. **Evaluation:** name tokens, time, and files in the Figure 1 reference.
6. **Related Work:** replace the repeated modifier stack with the same two-step
   source-linkage and additive-profile distinction.
7. Compile, inspect every page in column order, compare citation and number
   sets, and complete this report.

## Deferred Scientific Fix

The phase-label experiment remains required before a final submission-ready
claim that all of RQ3 is answered. This round will not delete phase, weaken the
hypothesis, call boundary agreement literal label accuracy, or replace the
paper story.

## Applied Fixes

### Abstract

Rebuilt the abstract as exactly nine role sentences and approximately 203
mechanically counted words:

1. agent context;
2. cross-execution developer problem;
3. profiling analogy and structural mismatch;
4. existing-tool gap;
5. the exact fixed thesis;
6. semantic operation stack and AgentProf;
7. RQ1 source-lineage, stage-agreement, and token-weight evidence;
8. RQ2 MAP and RQ3 boundary/partition evidence; and
9. RQ4 cost.

Every sentence maps to the corresponding Introduction role in the same order.
All abstract numbers remain present; no new number or claim was introduced.

### Introduction

- Rephrased the existing-tool gap as two concrete operations: link additive
  system effects to responsible agent actions, then aggregate them by semantic
  fields into selectable pprof profiles.
- Moved the token-weighted CodeTraceBench sentence directly after the ordinary
  B-cubed result and named `this CodeTraceBench comparison`, eliminating the
  incorrect OSWorld antecedent.
- Replaced section-number references with visible section names. The rendered
  contribution list now reads `Background and Motivation; Design`,
  `Implementation`, and `Evaluation` instead of empty parentheses under the
  unnumbered AAAI style.

### Background and Motivation

Added the single bridge `These requirements motivate AgentProf's design.` after
the complete D1--D3 description. It introduces no mechanism or claim.

### Design

- Made Figure 2 an in-place `[H]` evidence block. In the PDF, D1--D3 and the
  complete Design mapping paragraph now read continuously; the four-stage
  pipeline precedes the architecture figure.
- Closed the formal view definition by stating that stack function `sigma`
  remains independently selectable while the four built-in resource choices
  define selection predicate `phi` and weight `w`.
- Accepted the Consider item and renamed `Algorithms` to `Attribution and Stack
  Construction`, updating its Design cross-reference.

### Evaluation and Related Work

- Updated the Figure 1 body sentence to name all three displayed views:
  `tokens`, `time`, and `files`.
- Replaced the repeated Related Work modifier stack with the same source-linkage
  then additive-profile distinction used in the Introduction.

## Rejected or Deferred Alternatives

- **Move Figure 1 again:** deferred. It no longer interrupts the thesis/model
  paragraph, and the current full-width placement preserves the nine-page
  layout. Later layout rounds may move it only if they do not create a new
  interruption or page.
- **Expand Related Work or Conclusion:** rejected. The reviewer explicitly
  found their current three-topic and thesis--model--results structures
  complete; extra prose would consume space needed by scientific evidence.
- **Writing-only phase fix:** rejected as scientifically invalid and recorded
  for the outer experiment loop.

## Verification

- `make` completes with official `aaai2027` formatting.
- PDF remains 9 pages at letter size; main content ends on page 7 and references
  continue through pages 8--9.
- The compile log has no LaTeX warning, undefined reference/citation, overfull
  box, package warning, or compilation error.
- Direct PDF text inspection confirms visible contribution section names and a
  continuous D1--D3/Design/Figure-2 reading order.
- All four tables remain after their owning RQ protocol and before its
  interpretation.
- `git diff --check` passes.
- Entry and current citation sets remain identical at 52 unique keys.
- The exact thesis remains in Abstract, Introduction, and Conclusion.
- The four fixed RQ strings remain unchanged.
- No experimental number changed in this round.
- `docs/agentpprof-paper` remains clean at
  `7f80c433c9555317a2aa45a78d0ff93518f4c12c`.

## Remaining Concern and Next Node

RQ3 literal phase-label accuracy is the only section-convention finding that
cannot be repaired in WRITE. Continue serially to Round 3 logic flow; after the
writing cycle, the outer state machine must select a compact public phase-label
experiment rather than narrow RQ3 or alter the story.
