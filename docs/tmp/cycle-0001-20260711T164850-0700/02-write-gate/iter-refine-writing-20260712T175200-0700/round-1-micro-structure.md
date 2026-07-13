# Round 1 — Micro Structure

**Completed:** 2026-07-12T18:14:00-07:00  
**Cycle/gate:** cycle 0001 / full WRITE  
**Parent:** `round-0-macro-structure.md`  
**Reviewer:** fresh read-only subagent using `check-paper-structure-flow`, Levels 2--3  
**Verdict after fixes:** PASS with explicit empirical TODOs

## Inputs And Method

The reviewer reread the complete verbatim user instructions, structure-flow
skill and references, full current paper after Round 0, and current PDF/build
state. It checked paragraph roles, topic sentences, one-idea-per-paragraph,
transitions, abstract/introduction correspondence, and the opening and closing
of every exact RQ block. It edited nothing and ran no Git operation.

## Raw Findings

Must-fix findings were: a 12-sentence Abstract; missing correspondence for the
three profile views between Abstract and Introduction; an overloaded
Introduction system/evaluation paragraph; an overloaded Evaluation Setup;
overloaded RQ1 opening and auxiliary-analysis paragraphs; no explicit RQ1
answer; and research-process language such as “superseded,” “research record,”
and “exploratory timings” in the reader-facing paper.

Should-fix findings asked for separation of Design requirements from RQ
mapping, cleaner Operations and output/weight paragraphs, moving lineage caveats
out of mechanism exposition, clearer Related Work topic sentences, and modest
compression of repeated projection language. The reviewer also suggested noun-
phrase RQ headings and further compression of the Introduction tool inventory.

## Applied Fixes

- Compressed the Abstract to nine sentences with the canonical causal order and
  the same claims, numbers, and terminology.
- Added semantic, flat, and source-native profiles to Introduction paragraph 6
  so it corresponds exactly with the Abstract.
- Reorganized Introduction paragraph 6 into system, evaluation, current
  evidence, and complete-evidence roles without adding a paragraph or claim.
- Split Evaluation Setup into data/coverage, matched comparison protocol, and
  per-RQ experiment paragraphs.
- Split the RQ1 opening into question/current answer, experiment setup, and
  metric interpretation.
- Split RQ1 auxiliary projection coverage from cross-measure ranking.
- Added an explicit positive RQ1 answer-to-date sentence, followed by the
  independent-lineage evidence requirement.
- Replaced process-history prose in RQ2 and RQ4 with concise
  `positive-evidence TODO` endings. Removed all references to superseded
  mechanisms, research records, and exploratory timing from the paper.
- Recast RQ3's closing as a positive answer-to-date plus the complete held-out
  semantic-tag experiment.
- Split Design requirements from their RQ mapping.
- Split Operations into record/field semantics and measures/source drilldown;
  removed the implementation-section lineage caveat because RQ1 owns it.
- Split output formats from weight semantics and removed duplicate positive-
  integer wording.
- Added category topic sentences for failure-localization work and cross-run
  comparison/intervention work in Related Work.

## Deferred Or Rejected Findings

- Final RQ2/RQ4 numeric answers remain an experiment dependency. The TODOs are
  honest and positive; they will be replaced only by complete results.
- Noun-phrase RQ subsection titles were rejected because exact question-style
  headings are a binding user and orchestrator requirement.
- Further Introduction related-work compression and duplicate projection
  compression are accepted for the later logic/flow and word-choice rounds,
  where their cross-paragraph effect can be judged safely.

## Preservation And User-Intent Check

The exact thesis and all four exact RQs are unchanged. No number changed. The
citation-command count remains 59 before and after this round. No technical
content disappeared except explicit research-process wording and duplicated
caveats identified by the reviewer. No failed intermediate experiment or result
entered the paper. The profiling-to-intervention story remains the paper center.

## Compile Evidence

`make` completed successfully. The final log contains no undefined citation or
reference, LaTeX error, or emergency stop. The output remains 9 letter-size
pages including references.

## Next Node

Proceed to Round 2 section conventions. The empirical TODOs remain ranked
EXPERIMENT blockers, not writing defects and not authority to change the RQs.
