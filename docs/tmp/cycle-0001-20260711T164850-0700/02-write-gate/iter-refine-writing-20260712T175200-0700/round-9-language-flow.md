# Round 9 — Language Flow and Polish

**Started:** 2026-07-12T18:50:38-07:00  
**Completed:** 2026-07-12T18:56:43-07:00  
**Cycle/gate:** cycle 0001 / full WRITE  
**Parent:** round-8-terminology-claim-tone.md  
**Reviewer:** fresh read-only subagent using paper-writing-style, flow focus  
**Verdict after fixes:** PASS for flow; complete positive evidence remains an
EXPERIMENT blocker

## Objective And Method

The reviewer read the complete paper, docs/user-instruction.md, and the
paper-writing-style instructions. It checked paragraph topic and stress
positions, old-to-new information flow, transitions, register, and whether the
exact thesis and four fixed RQs form one strong story. It was prohibited from
editing files, running Git, touching the paper submodule, shrinking a claim, or
turning planned experiments into results.

## Raw Reviewer Findings

### Must fix

1. The Evaluation changes from a scientific paper into a project plan by mixing
   verified evidence with complete experiments still required for final
   answers.
2. RQ1 asks about resource attribution while its current result establishes
   measure conservation and declared-category separation, not independent
   lineage.
3. RQ2 and RQ4 contain protocols but no results. RQ2 is the paper's most
   attractive profile-to-intervention-to-held-out-improvement loop and must
   become its strongest empirical result.
4. RQ3 contains positive structured mapping and boundary evidence, but the
   complete target-blind tag experiment is still planned. “Evaluation below”
   is a stale forward reference.
5. Abstract, Introduction, and Conclusion promise four RQs but summarize only
   partial RQ1 evidence. Their final stress positions can report the complete
   chain only after the experiments run.

### Should fix

1. The tag definition interrupts the thesis paragraph's profiling-to-
   intervention climax and belongs in Profile Construction.
2. The final Introduction body paragraph carries system model, implementation,
   four RQs, results, corpus coverage, and future experiments at once.
3. Design presents the RQs out of argumentative order.
4. “For exploratory analysis” makes query-time projection sound peripheral.
5. The operation-stack mass paragraph carries too many concepts.
6. A cautious semantic-aggregation sentence repeats and weakens the central
   prediction that follows it.
7. RQ1 uses experiment-log openings instead of claim-first topic sentences.
8. The Introduction's “as developed in” phrase is unnecessary meta narration.
9. “Verified/current RQ1 ablation” reads like an audit status rather than paper
   prose.

### Consider

- Connect per-trajectory benchmark judging directly to why corpus-scale
  attribution cannot depend on repeated manual review.
- Give all four RQ subsections the same question, experiment, result, answer
  rhythm once their experiments finish.
- Preserve the Background sentence that the useful output identifies what to
  change and predicts the effect on later runs; RQ2 should directly fulfill it.

## Applied Fixes

### Introduction

- Connected per-trajectory evaluation cost directly to the need for corpus-scale
  attribution.
- Removed the “as developed in Background and Motivation” forward reference and
  ended the root-cause paragraph on the stronger point that execution trees need
  not be the hierarchy for aggregating cross-run effects.
- Moved the tag definition out of the thesis paragraph.
- Split the system/model content from the evaluation/evidence content.
- Replaced audit-style “verified RQ1 ablation” with “controlled RQ1 ablation”
  in the Abstract and “an RQ1 ablation” in the Introduction.

### Design

- Restored the argumentative RQ order: attribution and evidence preservation;
  real problem and intervention; tag accuracy; total cost.
- Split conservation from cross-run folding and held-out tag reliability.
- Replaced “For exploratory analysis” with a direct query-time mechanism
  statement.
- Defined tag and reference annotation at the beginning of Profile
  Construction, where the concepts become operational.
- Removed the tentative sentence before the central prediction, so the section
  directly states the bold hypothesis that a fixed semantic operation stack can
  reunite fragmented measurements, reveal accumulated effects, and suggest an
  intervention.

### Evaluation and Conclusion

- Replaced stale “evaluation below” prose with the existing positive conclusion
  that the results establish transfer for structured declared fields.
- Changed RQ1 evidence paragraphs from “additional checks” and “the same records
  also support” to claim-first openings about heterogeneous projections and the
  effect of measure selection.
- Replaced “current ablation” with the precise “grouping ablation” in the RQ1
  answer.
- Removed “current” from the Conclusion's RQ1 reference without changing its
  evidence scope.

## Deferred And Rejected Changes

- **Deferred to EXPERIMENT:** independent tool/span/process lineage for RQ1; a
  paired real-agent regression, profile-directed intervention, and held-out
  rerun for RQ2; target-blind leave-family-out semantic tags and attribution
  impact for RQ3; and complete cost/scaling for RQ4.
- **Deferred until those results exist:** rewriting Abstract, Introduction,
  Evaluation, and Conclusion as four completed answers. The final Abstract
  should place the RQ2 intervention outcome in its strongest result position,
  but no number may be invented.
- **Rejected:** changing RQ1 to grouping/conservation, changing RQ2 to a weaker
  localization question, treating structured mapping as the full RQ3 answer, or
  dropping RQ4.
- **Rejected:** removing honest status language before the experiments exist if
  that would make planned results appear completed.

## Preservation Check

The exact thesis and the four exact RQ headings remain unchanged. No number,
citation, mechanism, evidence block, figure, or limitation changed meaning.
Citation-command count remains 59. The paper still contains no failed
intermediate experiment in its reader-facing story. The revision adds no named
concept.

## Verification

make completed successfully. main.log contains no undefined
citation/reference, LaTeX error, emergency stop, or overfull-box report. The
PDF remains 9 letter-size pages. The Abstract remains exactly 200 words and 9
sentences.

No Git command was run in this round. No shared skill, submodule, canonical
research document, or user instruction file changed.

## Tree And Memory Impact

This was a writing-only node. The research frontier, thesis, RQs, hypotheses,
and evidence disposition did not change. The flow revision makes the existing
idea more forceful by foregrounding the profiling decision loop and making
hierarchy selection a mechanism rather than the destination.

## Next Node

Proceed serially to Round 10, the citation gate. After citation verification,
the independent WRITE audit must distinguish writing completion from the
remaining empirical work.
