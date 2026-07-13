# Round 1: Micro Structure

## Node identity

- **Started:** 2026-07-11 22:45:10 -0700
- **Cycle/Gate:** `cycle-0001-20260711T164850-0700` / `WRITE_GATE`
- **Parent:** `round-0-macro-structure.md`
- **Skill:** `iter-refine-writing`, Round 1
- **Review skill:** `check-paper-structure-flow`, Levels 2--3
- **Entry paper:** 9 pages total; Related Work and Conclusion spill onto content
  page 8 before References
- **Entry invariants:** 59 citation commands, four fixed RQs, three contributions,
  all quantitative values read-only

## Objective and method

The read-only reviewer loaded the common pitfalls and micro-structure checklist,
then read the complete current paper without a prior writing verdict. It checked
abstract/Introduction role correspondence, paragraph responsibilities,
topic-sentence order, why-before-what, RQ opening/answer closure, Setup and
Limitations ownership, and structural repetition that causes the page overflow.

## Raw findings

### Must-fix

1. Abstract and Introduction do not follow the same role order. The abstract is
   12 sentences and introduces navigator/best-policy/bundle controls at a level
   not mirrored in the Introduction's this-paper paragraph. Align both to
   background, problem, root cause, existing approaches, insight, challenge,
   system/method, and results.
2. The Introduction problem paragraph buries run-centric fragmentation after a
   generic need sentence and ends with traditional profiling. The this-paper
   paragraph mixes backend inventory, identity qualification, construction, three
   results, and an open question. Give each one role and move backend detail out.
3. Design uses G1--G3 before defining them, mixes implementation status into the
   overview, and lacks a typical trajectory-to-output walkthrough.
4. The scope-tree model's main paragraph contains the contract, constructors,
   query independence, responsibility, inheritance, views, SQL equivalence, and
   built-in measures. Split it into role-focused paragraphs without deleting the
   formal contract.
5. Implementation mixes ingestion, backends, construction, output, and evidence
   status. Organize it by mechanism; evidence status belongs in Evaluation or
   Limitations.
6. Experimental Setup contains two empirical capability results with no RQ
   ownership while omitting the actual repetition/measurement boundaries. Move
   those checks into RQ1 as representation/conservation support and make Setup
   state the shared frozen-policy, resampling, and cost rules.
7. RQ1 states the same 36.7%/84.4%/183,714 result in prose, a bold result block,
   the caption, and a bold partial answer. Keep the metric definition, figure,
   one interpretation/answer, and independent-oracle obligation.
8. Related Work is one paragraph containing four topic groups and repeats the
   Evaluation control protocol. Split it by topic and retain only precise
   comparison boundaries.
9. Conclusion spills onto content page 8 and closes with a duplicate four-RQ
   experiment plan. Keep thesis, system/model, and key positive/negative result;
   leave detailed obligations in the RQ blocks and Limitations.

### Should-fix

- Deepen rather than repeat the Introduction in Background and Motivation.
- Put why before what in Identity and Navigation.
- Combine RQ3 caption interpretation and partial answer while preserving the
  counterexamples and boundary-audit limitation.
- Let Limitations focus on external validity and point to, rather than repeat,
  the four RQ-specific evidence gaps.
- Replace bold run-in answer/TODO labels with normal topic sentences.

### Consider

- Move the flamegraph float source if it interrupts the intro logic after final
  layout.
- Keep the central falsifier complete in Evaluation and shorten its repeated
  Design form to the property the mechanism must realize.

## Fix plan

All Must-fix items and Should-fix items will be applied subsection by subsection.
The Abstract and Introduction will receive a role-preserving structural repair in
this round; the required Round 4 procedure will later rebuild them again from the
canonical role map. The flamegraph source placement is deferred until the
post-edit PDF shows whether it still interrupts reading. No RQ, contribution,
number, citation, dataset role, negative result, or evidence obligation may be
removed. Duplicate evidence may be consolidated only when the surviving location
contains the complete fact and boundary.

## Completion evidence

### Applied fixes

1. Rebuilt the Abstract into nine role sentences in the same causal order as the
   Introduction: context, fragmented problem, current tradeoff, insight, model,
   system/mechanism, decisive comparison, positive result, and negative/open
   result. All values and the unanswered failure/safety/redundancy boundary remain.
2. Made run-centric fragmentation the Introduction problem topic sentence and
   moved profiling into the root-cause transition. Reordered root cause before
   existing approaches. Preserved every citation command.
3. Split the insight from its realization challenges. Compressed the this-paper
   paragraph from backend inventory into system, navigator, and the three current
   evidence statements. Contributions still close the Introduction.
4. Defined G1--G3 before mapping components. Added a trajectory-to-operation-to-
   identity/tree-to-profile/navigation walkthrough tied to the architecture figure.
   Implementation status no longer occupies the Design overview.
5. Split the long scope-model prose into contract, construction, responsibility,
   selectable-view, and relational-substrate paragraphs without changing the
   formula or contract.
6. Put why before what in identity construction and navigation.
7. Organized Implementation into ingestion/inheritance, identity/construction,
   emission, and implemented-boundary paragraphs. Moved evidence status to
   Limitations.
8. Removed empirical sanity results from Setup. Setup now states the common data,
   frozen policy/control rules, accounting boundary, offline execution, 1,000
   RQ1 permutations, 1,000 RQ2 bootstrap resamples, and RQ3 leave-dataset-out
   protocol. It explicitly says hardware-controlled performance evidence is absent.
9. Consolidated RQ1's four repeated answers into one self-contained figure
   caption, one permutation interpretation, one representation-check paragraph,
   and one direct partial answer plus independent-lineage requirement. All prior
   values remain once in the RQ block.
10. Replaced bold run-in answer/TODO labels with normal topic sentences across
    Evaluation.
11. Combined RQ3 interpretation and partial answer while preserving both
    counterexamples, the four-of-five boundary result, six-of-nine threshold
    answer, and backend-validation gap.
12. Split Related Work into observability/signals, aggregation substrate,
    diagnostic benchmarks, and closest scope-first methods. Removed repeated
    execution-protocol prose while retaining SDBL, same-risk control, reproducible
    mechanism boundary, Who&When, and TRAIL.
13. Removed the Conclusion's duplicate four-RQ future plan. The RQ blocks and
    Limitations retain every evidence obligation.

### Should-fix and Consider decisions

- Background was not shortened directly. After the Introduction compression, it
  now supplies the concrete intent/effect pipeline, profiler mechanics, AgentSight
  substrate, and abstraction gap assumed by Design rather than repeating the full
  Introduction argument. Further sentence economy remains available to later
  language rounds.
- Identity/navigation why-before-what, RQ3 consolidation, Limitations focus, and
  removal of fake run-in headers were applied.
- The flamegraph source placement was retained: after recompilation it floats away
  from the causal paragraph boundary and no longer forces content past page 7.
- The repeated Design falsifier was retained in shorter property form because it
  is the design's explicit falsifiability boundary; Evaluation owns the complete
  comparison protocol.

### Preservation and compilation

Completed 2026-07-11 22:58:53 -0700.

- Citation-command count: 59 before and after.
- RQ count and meanings: four, unchanged; RQ2 still asks exactly whether profiler
  output corresponds to real problems.
- Contributions: all three remain.
- Quantitative values: no admitted value changed. Consolidated values remain in
  the figure caption, RQ answer, or their new RQ-owned representation paragraph.
- Paper size: 9 US-Letter pages.
- Main-content boundary: Related Work, Conclusion, and the References heading now
  fit on page 7; pages 8--9 contain references only. This satisfies AAAI's seven
  content pages and nine total pages.
- Counted words: 4,676, down from 5,338 at Round 0 entry through role-based
  deduplication rather than scientific narrowing.
- Undefined citations/references: none.
- Remaining overfull boxes: 8.10556 pt and 0.99261 pt.
- Protected submodule remains at `7f80c433c9555317a2aa45a78d0ff93518f4c12c`;
  no Git operation or submodule edit occurred.

## Round verdict and next node

**ROUND 1 PASS.** Paragraph roles, RQ ownership, and the content-page boundary are
now coherent. Continue to Round 2 section conventions. Overfull boxes and any
remaining local repetition are carried to the appropriate later rounds.
