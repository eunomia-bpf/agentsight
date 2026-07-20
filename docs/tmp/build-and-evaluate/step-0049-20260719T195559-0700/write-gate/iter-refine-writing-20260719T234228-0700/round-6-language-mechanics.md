# Round 6 — Language Mechanics

**Started:** 2026-07-20T00:25:59-07:00  
**Step / parent:** Step 0049 / WRITE gate / iter-refine-writing  
**Skills:** `iter-refine-writing`, `paper-writing-style`  
**Completed:** 2026-07-20T00:39:30-07:00  
**Status:** complete

## Scope

This pass covers punctuation, coordination, fragments, subject--verb distance,
dangling modifiers, and grammatical referents. It cannot change scientific
meaning, thesis, RQs, numbers, citations, qualifiers, terminology, or evidence.

## Method

A fresh reviewer reads every live English sentence and reports exact
LaTeX-ready local fixes. The root applies Must-fix and justified Should-fix
items, evaluates every Consider item, records rejections, rebuilds, and checks
page and citation boundaries.

## Reviewer findings

The independent sentence-level reviewer identified ten grammatical or
coordination defects and four worthwhile local wording repairs. The defects
were concentrated in compound clauses whose semicolon obscured the actor,
colon constructions that did not introduce a true list, and two sentences
whose grammatical subject accidentally made a capture path or a profile perform
multiple unlike actions. It found no fragment, agreement error, dangling
modifier, or antecedent defect that required a scientific rewrite.

## Applied repairs

1. Made the abstract's `AgentSight capture-and-join path` the single actor for
   precision, recall, and control rejection.
2. Split four semicolon-linked constructions in stack construction, the
   multi-resolution fallback, adapter coverage, and RQ2 label timing.
3. Replaced `This establishes` with the evidence-bearing subject `These
   results establish`.
4. Clarified that prompt-span duration measures elapsed rather than active CPU
   time.
5. Replaced `are not untouched confirmation` with `do not constitute untouched
   confirmation`.
6. Recast the RQ3 CodeTraceBench and OSWorld population sentences so their
   colons no longer connect independent propositions.
7. Split the task-family backend parenthetical into a direct method sentence
   and a direct input sentence.
8. Split the Scope sentence after `post-hoc support`.
9. Replaced the vague Related Work phrase `residual capability is their
   conjunction` with the direct actor construction `AgentProf combines these
   capabilities ... by joining`.
10. Repaired the Conclusion's compound actor: profiles preserve/improve/recover,
    while AgentProf builds the 27,765-operation profile.

Fourteen live English sentences changed. Every change is local and preserves
the entry evidence, qualifiers, citations, notation, exact thesis, and four
RQs.

## Deliberately rejected

- The Introduction's explanatory parenthetical was retained: it is short,
  grammatical, and distinguishes one example without interrupting the claim.
- Title, contribution, RQ, and design-item colons were retained because each
  introduces a genuine definition, list, or scoped question.
- Compact metric parentheticals and the numbered pipeline were retained; their
  punctuation is conventional and changing it would add prose without improving
  referents.
- No em dash was introduced, and no hard-coded replacement for `\\sys` was
  made.

## Exit validation

- `make -C docs/paper`: pass.
- PDF: 9 pages; Conclusion remains on page 7 and References begin on page 8.
- `main.log`: no undefined references/citations and no overfull boxes.
- Scientific contract: exact thesis and the four RQs unchanged.
- Citation commands: no deletion.
