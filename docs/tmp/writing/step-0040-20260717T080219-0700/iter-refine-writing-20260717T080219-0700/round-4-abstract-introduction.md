# Round 4 — Abstract and Introduction Rebuild

## Node identity

- **Started:** 2026-07-17T13:25:00-07:00
- **Parent:** Step 0040 WRITE gate
- **Procedure:** root agent invoking the complete `rewrite-abstract-intro`
  workflow; no fork and no Git operation.
- **Source of truth:** complete current paper body only. Project story and
  evaluation docs are not used to invent or strengthen opening claims.

## Pre-edit role map

### Introduction

| Current paragraph | Current role | Diagnosis | Target action |
|---|---|---|---|
| 1 | Background/context | Clean two-layer workload context | Keep |
| 2 | Problem | Correct questions and consequence, but topic sentence states a need rather than the missing population-level view | Tighten topic sentence; preserve questions and citations |
| 3 | Root cause | Required because the insight answers missing stable identity and hierarchy | Keep after Round 2 correction |
| 4 | Existing solutions | Correct evidence and composite gap, but neutral first sentence delays the limitation | Put the unsolved profiling abstraction in topic position; preserve concessions and citations |
| 5 | Insight/model | Exact thesis and two abstractions are present and separable from the artifact | Keep scientific content |
| 6 | This paper/system | System and two mechanism families correspond to the insight | Keep; no fabricated challenge paragraph |
| 7 | Results | All four RQs represented, but literal task/action tag evidence is absent despite the contribution claiming it | Add existing 0.695/0.498 macro-F1 values alongside the existing RQ3 boundary result; do not add a result |
| 8 | Contributions | Correct model/system/evaluation deliverables in order | Keep |

The optional root-cause paragraph is required: the paper's insight directly
answers a structural identity/hierarchy gap. A separate challenges paragraph is
not justified. The technical design is already explained by the two missing
structures and D1--D3; fabricating another obstacle list would add jargon and
invite an unnecessary novelty attack.

### Abstract

| Current sentence | Current role | Diagnosis | Target role |
|---|---|---|---|
| 1 | Background | Correct | Background |
| 2 | Problem | Correct | Problem |
| 3 | Mixed root cause + existing-solutions gap | Violates one-role correspondence | Root cause |
| 4 | Thesis | Correct | Existing-solutions gap moves before it; retain exact thesis |
| 5 | System/model | Correct but list-heavy | System realization |
| 6 | Methodology | Correct | Methodology |
| 7 | RQ1 results | Correct standard metrics | Results block 1 |
| 8 | RQ2 + structural RQ3 | Correct but spends space on comparator detail and omits literal tags | Results block 1/2 |
| 9 | RQ4 | Correct | Results block 2 |

## Reorganization plan

The rebuilt Abstract will use nine sentences in causal order:

1. background;
2. population-level problem;
3. structural root cause: native execution structure is not a reusable
   cross-run semantic-responsibility hierarchy;
4. current tools' exact composite limitation;
5. exact thesis;
6. AgentProf and its operation/operation-stack realization;
7. complete evaluation population;
8. RQ1/RQ2 standard results; and
9. RQ3 literal/structural results plus RQ4 cost.

All numbers in the plan already appear in Evaluation. Comparator details may
be cut from the Abstract because their complete values remain in RQ3 and the
opening needs one result for literal fields. No citation command will be
removed from the Introduction. No body section will change in this round.

## Status

Complete.

## Applied Introduction rebuild

The root edited the opening one paragraph at a time in role order:

1. **Background:** retained the high-level intent/system-effect workload and
   growing trajectory population.
2. **Problem:** changed the topic sentence from a generic need to the missing
   population-level answers, then retained the three concrete questions and
   manual/LLM inspection consequence.
3. **Root cause:** retained the two structural gaps and Round 2's accurate
   execution-nesting boundary.
4. **Existing solutions:** put the missing profiling abstraction in topic
   position, then retained the complete tracing, hierarchical grouping,
   cross-run prior-work concessions, citations, and composite gap.
5. **Insight:** retained the exact thesis and operation/operation-stack model.
6. **System:** retained the offline pprof-compatible artifact and its pluggable
   attribution/stack-construction mechanisms.
7. **Results:** retained all existing RQ1, RQ2, structural-RQ3, and RQ4 values
   and added the already reported 0.695 task-family and 0.498 action macro-F1
   values so literal field derivation closes the contribution loop.
8. **Contributions:** unchanged.

No challenges paragraph was added. The opening already explains why direct
transfer fails, and the two-object model plus two mechanism families answer
those gaps without a fabricated obstacle taxonomy.

## Abstract derivation

The Abstract was derived last from the revised Introduction. Its nine rendered
sentences map in order to background, problem, root cause, existing-solutions
gap, exact thesis, AgentProf realization, evaluation population, RQ1/RQ2
results, and RQ3/RQ4 results. It is 232 rendered words.

The old mixed third sentence was split by role: the structural cause now has
its own sentence, and the closest-work composite limitation has its own
sentence. The old RQ3 comparator detail was removed from the Abstract but
remains in Table 3 and its result paragraph; that space now reports the
existing task-family/action macro-F1 values. No result or claim was invented.

## Correspondence and logic self-check

- Sentence 1 corresponds to Introduction background paragraph 1.
- Sentence 2 corresponds to the population-level problem paragraph.
- Sentence 3 corresponds to the two-structure root-cause paragraph.
- Sentence 4 corresponds to the existing-tools/composite-gap paragraph.
- Sentence 5 is the exact thesis from the insight paragraph.
- Sentence 6 corresponds to the AgentProf/system paragraph and references the
  model defined immediately before it in both versions.
- Sentence 7 corresponds to the complete evaluation population represented by
  the Introduction results and Evaluation overview.
- Sentences 8--9 correspond to the Introduction results paragraph; every number
  also appears in the corresponding RQ body.

The causal read passes end to end: population-level questions follow growing
histories; missing stable identity and reusable semantic hierarchy explain why
ordinary stacks do not transfer; current tools establish constituent
capabilities but not the composite; the thesis answers that gap; AgentProf
realizes the thesis; and the fixed four-RQ evaluation measures its links.

No citation command was removed by Round 4; two existing body sources were
cited in the expanded Introduction RQ3 sentence. The overall cycle count is
lower than the entry baseline only because Round 1 directly obeyed the user's
instruction to remove token-weighted B$^3$ and its citation, which is separately
recorded rather than hidden as compression.

## Compilation and open items

`make` completed all passes. The PDF remains nine US-Letter pages, main text
ends on page 7, and references begin on page 8. There is no undefined citation,
undefined reference, or overfull warning. The exact thesis appears in Abstract,
Introduction, and Conclusion; all four RQ headings remain.

No Abstract/Introduction item requires new evidence. Sentence-level rhythm and
word choice remain intentionally deferred to Rounds 6--9.

## Next node

Round 5 performs an independent paper-consistency audit across architecture,
mechanisms, RQs, figures/tables, claims, and numbers.
