# Round 0: Macro Structure

## Node identity

- **Started:** 2026-07-11 22:31:10 -0700
- **Cycle:** `cycle-0001-20260711T164850-0700`
- **Gate:** `WRITE_GATE`
- **Parent:** `500-ideas-outer-audit-20260711T223016-0700.md`
- **Skill:** `iter-refine-writing`, Round 0
- **Review skill:** `check-paper-structure-flow`, Level 1
- **Entry paper:** `docs/paper/main.tex`, 11 US-Letter pages
- **Entry evidence:** 59 citation commands, four RQ subsections, 338 numeric
  source tokens, no undefined references, two overfull boxes

## Objective

Repair the AAAI-27 paper's top-level organization and page allocation without
changing any quantitative value, RQ meaning, contribution, or scientific
obligation. The target is seven content pages and at most nine total pages.

## Files and sources read

- complete `docs/paper/main.tex` and rendered `docs/paper/main.pdf`;
- `iter-refine-writing/references/common-pitfalls.md`;
- `check-paper-structure-flow/SKILL.md`;
- `check-paper-structure-flow/references/full-paper-12p.md`;
- `check-paper-structure-flow/references/workshop-paper-6p.md`;
- official-target summary in `docs/paper/README.md`;
- IDEA outer-audit report and current `docs/user-instruction.md`.

The reviewer used the full-paper role conventions with the compact-paper deltas
appropriate to a seven-page AAAI main-track paper. It did not read an earlier
writing verdict and made no edits.

## Raw reviewer findings

### Must-fix

1. `\maketitle` follows the abstract, forcing the abstract onto page 1 and the
   title onto page 2. Move it before the abstract and rebuild.
2. Design contains 1,625 words while Implementation contains only 64. Backend,
   Rust inducer, caching, and output details belong in Implementation; detailed
   experiment controls and metrics belong in Evaluation.
3. G1--G3 and the architecture figure should open Design, with implemented and
   proposed components distinguished in the same figure.
4. Evaluation needs one compact shared setup after the exact four-RQ list.
5. RQ1 is disproportionately large because it contains field-projection,
   multi-measure, and automatic-induction capability checks that do not establish
   lineage correctness. Keep RQ1 centered on inheritance and conservation and
   compress the checks into shared system validation.
6. Each unanswered RQ should keep one explicit decisive evidence requirement;
   detailed protocols belong in the auditable experiment reports rather than
   being repeated in the submission text.
7. RQ subsection titles must be noun phrases, while each block's first sentence
   restates the scientific question without changing its meaning.
8. Add one short Evaluation limitations block rather than scattering all model
   and extrapolation boundaries.

### Should-fix

1. Reduce the 942-word Introduction toward 700--750 words and make contributions
   its final unit. Move current research status to Implementation/Limitations.
2. Compress four short Background and Motivation subsections into two and move
   G1--G3 into Design.
3. Replace `\paragraph{}` algorithm headers with parallel noun-phrase Design
   subsections.
4. Reduce the three-view full-width flamegraph to a representative compact view;
   preserve the multi-measure facts in prose and the artifact.
5. Reduce the abstract from 262 toward 200--220 words by moving experiment-control
   detail to Evaluation. This is deferred to the dedicated Abstract/Introduction
   rebuild in Round 4 so the same text is not rewritten twice.

### Consider

- A compact RQ/claim/data/metric/current-answer table may replace repeated setup
  prose only if the rendered version is smaller.
- Related Work is already compact and should not be stripped further.
- Do not add Overview, Discussion, or Future Work sections.

## Target page budget

| Content | Pages |
|---|---:|
| Title and Abstract | 0.45 |
| Introduction | 1.00 |
| Background and Motivation | 0.40 |
| Design with architecture | 1.25 |
| Implementation | 0.35 |
| Evaluation with four RQs, Setup, Limitations, and floats | 2.75 |
| Related Work | 0.55 |
| Conclusion | 0.25 |
| **Total** | **7.00** |

## Approved restructuring outline

This outline is recorded before applying cross-subsection restructuring, as
required by the writing skill:

```text
Abstract

1. Introduction
   - contributions are the final unit

2. Background and Motivation
   2.1 Agent Trajectories and Profiling
   2.2 Cross-Run Attribution Gap

3. Design
   3.1 Requirements and System Overview
       - G1--G3
       - architecture and implemented/proposed boundary
   3.2 Semantic Scope-Tree Model
   3.3 Identity and Scope Construction
   3.4 Cost-Bounded Scope Navigation

4. Implementation
   - inputs and correlation
   - candidate-identity backends and Rust inducer
   - outputs, caching, and current implementation boundary

5. Evaluation
   - exact RQ1--RQ4 list
   5.1 Experimental Setup
   5.2 RQ1: Cross-Layer Attribution Correctness
   5.3 RQ2: Operational Problem Correspondence
   5.4 RQ3: Cross-Family Identity Transfer
   5.5 RQ4: End-to-End Work Advantage
   5.6 Limitations

6. Related Work
7. Conclusion
```

## Fix policy

All Must-fix findings will be applied. Should-fix 1--4 will be applied in this
round; abstract compression is explicitly deferred to Round 4, which is the
mandatory complete abstract/intro rebuild. The compact RQ table is rejected for
now because it would duplicate incomplete result blocks and its page savings are
unproven. No contribution, RQ, citation, quantitative result, or future evidence
obligation may be removed.

## Completion evidence

### Applied fixes

1. Moved `\maketitle` before the abstract. This alone reduced the paper from 11
   to 10 pages by eliminating the unintended abstract-only first page.
2. Reduced Background and Motivation from four short subsections to two:
   `Agent Trajectories and Profiling` and `Cross-Run Attribution Gap`.
3. Moved G1--G3 to `Requirements and System Overview` at the start of Design.
4. Moved and rebuilt the architecture figure at the Design opening. Following
   `paper-figures`, the TikZ now distinguishes the solid implemented substrate
   from the dashed proposed frozen-identity/navigation path and uses the paper's
   terminology. The prose explains what that distinction means.
5. Reorganized Design into four noun-phrase subsections. Removed run-in
   `\paragraph{}` headers. Kept model and mechanism in Design while moving regex,
   tagger, clustering, Rust-inducer, caching, input, and output details to
   Implementation.
6. Moved the shared identity--structure comparison, policy ablation, outcome
   definition, and end-to-end cost boundary into `Experimental Setup`, then
   compressed duplicate protocol prose without removing a control or evidence
   obligation.
7. Moved field-projection and multi-measure checks out of RQ1 into one shared
   setup paragraph. It retains 13,265 operations, all five group counts, all 15
   families, 7/10 overlap, rho 0.623, and ranks 8/93, while explicitly limiting
   those facts to implementation validation.
8. Replaced question-style RQ subsection titles with noun phrases. Each block's
   first sentence explicitly restates its unchanged RQ meaning.
9. Reduced the full-width flamegraph from three redundant rendered views to two
   representative views already discussed in the text; the multi-measure result
   remains in Evaluation and the complete images remain in the artifact.
10. Moved the Introduction's current-status paragraph to Implementation so that
    contributions again close the Introduction.
11. Condensed the long RQ2 future protocol to one decisive evidence paragraph
    while retaining failures, safety, redundancy, all fresh/development dataset
    roles, matched baselines, fixed localizer, identity--structure comparison,
    policy ablation, end-to-end cost, and separate-outcome requirement.
12. Added a short `Limitations` subsection that centralizes present evidence and
    extrapolation boundaries without narrowing any RQ.

### Applied, rejected, and deferred reviewer suggestions

- All eight Must-fix findings were applied.
- Should-fix 1--4 were applied. The abstract compression part of Should-fix 5 is
  deferred to mandatory Round 4 because that round rebuilds the abstract and
  Introduction from their role map; editing it twice would add churn without
  evidence.
- The compact RQ table was rejected for now because it would duplicate the four
  active result blocks and its rendered savings were unproven.
- Further Related Work compression was rejected because the reviewer found it
  already near the compact-paper minimum.

### Preservation checks

- Citation-command count: 59 before and 59 after.
- RQ subsections: four before and four after.
- RQ scientific meanings: unchanged; RQ2 still states exactly “does profiler
  output correspond to real problems?”
- Contributions: all three retained.
- Key empirical values retained and re-located without alteration: 90.4%, 36.7%,
  84.4%; 11,967, 15,027, 24,703; 13,265 and group counts 9/57/226/455/3,757;
  7/10, rho 0.623, ranks 8/93; the complete RQ2 table and controls; RQ3 7/9 and
  6/9; and all RQ4 timing, call, and cache values.
- Removed numeric source tokens were duplicated protocol wording and the figure's
  count of displayed panels, not changed experimental values.
- No citation or technical obligation disappeared without the review finding
  authorizing its relocation or compression.

### Compilation and page evidence

Completed 2026-07-11 22:44:56 -0700. A full build plus an additional
`pdflatex` pass succeeds:

- 9 US-Letter pages, down from 11;
- 5,338 counted words, down from 6,034;
- no undefined citations or references;
- two pre-existing overfull boxes remain: 8.10556 pt and 0.99261 pt;
- references begin on page 8, but Related Work and Conclusion still occupy the
  top of that page.

The total-page limit is now met, while the strict seven-content-page boundary is
still exceeded by roughly one column. The remaining compression is not a macro
route change: Round 4 must rebuild the 262-word abstract and 859-word
Introduction, and sentence/word/flow rounds must remove local redundancy. Those
rounds must move the References heading to the start of page 8 without changing
science.

## Round verdict and next node

**ROUND 0 COMPLETE WITH CARRIED FORMAT DEFECT.** The macro organization is now
coherent and all structural Must-fix findings are closed. The paper is not yet
format-compliant because Conclusion spills onto content page 8. Continue
immediately to Round 1 micro structure; do not treat the 9-page total as proof of
AAAI compliance.
