# Round 3: Logic Flow

## Node identity

- **Started:** 2026-07-11 23:11:35 -0700
- **Cycle/Gate:** `cycle-0001-20260711T164850-0700` / `WRITE_GATE`
- **Parent:** `round-2-section-conventions.md`
- **Entry paper:** 9 pages, four fixed RQs, 59 citation commands
- **Completed:** 2026-07-11 23:26:14 -0700
- **Reviewer verdict:** `REVISE` on the first read; `PASS` after fixes and two focused rechecks

## Objective and method

The fresh read-only reviewer read the complete paper without a prior verdict and
checked whether the prose supports its claims and whether Abstract, Introduction,
Background, Design, Implementation, Evaluation, Related Work, and Conclusion form
one argument. It specifically audited implemented versus proposed status,
accounting versus correctness versus diagnostic correspondence, the central
identity--structure thesis versus navigator policy, the negative leaf result, and
unanswered evidence obligations. It did not perform an external novelty review.

The skill referenced `references/common-pitfalls.md`, but that path was absent
from the current working tree during this review. The reviewer therefore used the
core writing-loop contract and a complete paper read; the main agent independently
checked every accepted finding against the paper.

## Raw findings and decisions

### Must-fix now

1. The conservation equation is wrong for variable-length paths. If an operation
   terminates at an internal prefix, `W(n)=sum children` drops its direct mass.
   Define direct terminal mass `D(n)` and use `W(n)=D(n)+sum children`; distinguish
   one terminal assignment from derived inclusive ancestor totals.
2. Separate analyst-selected views, frozen query-independent identity/tree
   membership, and query-conditioned navigator priority. Replace the misleading
   phrase “query-conditioned hierarchy” and correct Chinese comments.
3. RQ2 says the same labels are supplied to methods, contradicting its hidden-label
   protocol. Methods receive the same label-free risk information; external labels
   are joined only for scoring.
4. Contribution 2/3 wording, Abstract/Introduction numbers, and Conclusion status
   do not consistently separate achieved substrate/proxy evidence from proposed
   mechanisms and unanswered central claims.
5. The 36.7%/84.4% result must be identified at the paper's front and back as
   declared-category separation/conservation, not lineage correctness. The RQ3
   threshold is taxonomy-seeded proxy transfer, not frozen induced identity.
6. The central thesis depends jointly on RQ2 diagnostic correspondence, RQ3 frozen
   identity, and RQ4 complete cost, with RQ1 as its accounting foundation; Setup
   currently maps it too narrowly to RQ2.
7. Split the RQ2 controls by purpose: identity--structure tests representation;
   pointwise versus whole-scope tests navigation policy; exact bundle emulation is
   an output-equivalence/cost check. Correct the stale Chinese RQ2 comment, which
   still promotes point coverage to the primary outcome.

### Should-fix

- Reserve “stable semantic scope tree” for a tree that passes RQ3; call current
  outputs candidate/profile or trace-local scope trees.
- Make the Introduction result sequence expose the four-RQ dependency.
- Use `exact multi-operation context completion` consistently.
- End Related Work with the ambitious frozen-identity/semantic-structure
  distinction and its current evidence caveat, not the smaller phrase
  category-level aggregate profiling.

### Later experiment blockers

The achieved-claim voice cannot become final merely through writing. The frozen
labeler/navigator and complete RQ1--RQ4 experiments remain mandatory. This round
will make current status logically exact without shrinking the target contribution.

## Fix plan

Apply the model correction first, then terminology, RQ2 leakage, RQ dependency,
control roles, and cross-section status wording. Preserve all RQ meanings,
quantitative values, citations, and the large target claim. Compile and reread the
front/back story after edits.

## Completion evidence

The paper now distinguishes terminal from inclusive mass, declared
views from frozen identity and query-time navigation, label-free method
inputs from post-freeze scoring labels, the four-RQ dependency, the
representation/policy/bundle-control roles, and achieved substrate
evidence from the completed-paper target. Front and back matter state
that the admitted positive values establish category separation rather
than lineage, that taxonomy-seeded transfer is only a proxy, and that
the negative leaf result leaves the full hierarchy open. English and
Chinese source comments carry the same evidence boundaries.

A clean `make` followed by a final `pdflatex` pass produced a 9-page
US-Letter PDF. The paper has seven content pages and References begins
on page 8. The source retains 59 citation commands and exactly four RQ
subsections; the final log contains no undefined citation or reference.
Two pre-existing overfull boxes remain (8.10556 pt in the architecture
goal block and 0.99261 pt in the RQ2 table); later language/layout
rounds own those local formatting defects.

The independent reviewer reread the complete current paper twice after
the edits. The first focused recheck found only three stale Chinese or
synthesis lines and one report statement; after those fixes, the final
recheck found all seven Must-fix and four Should-fix findings resolved
without changing an RQ, quantitative value, or target contribution.
The final Round 3 verdict is `PASS`.

The `docs/agentpprof-paper/` submodule remained internally clean at
`7f80c433c9555317a2aa45a78d0ff93518f4c12c`. This round did not edit
the protected pre-existing changes in `docs/evaluation.md` or
`docs/idea-story.md` and performed no Git operation.

## Remaining concerns and next node

The paper remains scientifically incomplete: frozen induced identity,
full-hierarchy diagnostic correspondence, lineage correctness, and
complete end-to-end cost still require experiments. These are carried
forward without narrowing the target thesis. The next node is Round 4,
which rebuilds the Abstract and Introduction from the current paper
body while preserving all evidence boundaries and numbers.
