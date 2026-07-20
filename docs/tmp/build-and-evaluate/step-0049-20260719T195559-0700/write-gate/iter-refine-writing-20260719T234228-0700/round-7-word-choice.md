# Round 7 — Word Choice and Sentence Openings

**Started:** 2026-07-20T00:41:10-07:00  
**Step / parent:** Step 0049 / WRITE gate / iter-refine-writing  
**Skills:** `iter-refine-writing`, `paper-writing-style`  
**Completed:** 2026-07-20T01:03:40-07:00  
**Status:** complete

## Scope

This pass checks every live English sentence for vague verbs, avoidable
nominalization, weak openings, unnatural academic word choice, and passive
constructions that hide an important actor. It cannot alter the thesis, RQs,
scientific meaning, evidence, numbers, citations, qualifiers, terminology, or
story.

## Method

A fresh independent reviewer reads the complete paper and returns exact local
before/after proposals. The root accepts only changes that make the existing
meaning more direct; scientific reframing and stylistic churn are rejected.

## Reviewer findings

The reviewer read all 996 source lines and every live English sentence. It
reported three Must-fix actor/parallelism defects, eleven Should-fix wording
items, and two Consider items. It found no canned verbosity, weak existential
openings, stacked hedges, excessive passive methodology, or unauthorized
scientific change.

## Applied repairs

Fifteen targeted passages were repaired. The changes restore the correct actor
for folding, split the action backend's inputs from its evaluation population,
make backend-versus-majority metrics dimensionally explicit, replace weak
nominal constructions with direct actors, and clarify the cost result. The pass
also removes one unnecessary intensifier and supplies a missing Related Work
referent.

The two Consider items were accepted: the optional mode now `uses the same NPMI
score`, and the RQ4 result has a measured-object subject.

## Deliberately rejected

The proposed expansion of `These results establish scoped capture-and-join
accuracy and lossless folding...` was rejected. Its replacement could make
losslessness appear conditional on predeclared categories, whereas the current
sentence reports two separate properties compactly.

No claim, number, citation, qualifier, RQ, or established term changed.

## Exit validation

- `make -C docs/paper`: pass.
- PDF: 9 pages; Conclusion remains on page 7 and References begin on page 8.
- `main.log`: no undefined references/citations and no overfull boxes.
- Exact thesis and four RQs: unchanged.
- Citation commands: no deletion.
