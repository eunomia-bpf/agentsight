# Round 8 — Claim-before-Evidence and Academic Prose

**Started:** 2026-07-20T01:05:00-07:00  
**Step / parent:** Step 0049 / WRITE gate / iter-refine-writing  
**Skills:** `iter-refine-writing`, `paper-writing-style`  
**Completed:** 2026-07-20T01:20:15-07:00  
**Status:** complete

## Scope

This pass checks paragraph claim placement, named actors in method prose, and
direct transitions from evidence to conclusions. It cannot change paragraph
scientific roles, thesis, RQs, evidence, numbers, citations, qualifiers,
terminology, or story.

## Method

A fresh independent reviewer rereads the complete current paper after Round 7.
The root accepts only local sentence-order or actor repairs that preserve the
scientific contract and the AAAI page boundary.

## Reviewer findings

The fresh reviewer found zero Must-fix issues, five Should-fix issues, and zero
Consider items. Exact thesis, four RQs, Abstract, Introduction, Design, Related
Work, and Conclusion already followed an appropriate claim-to-support order.
No new claim, experiment, reframing, citation change, or global restructuring
was proposed.

## Applied repairs

All five bounded repairs were accepted:

1. The AgentSight adapter now directly `converts` recordings to operation JSONL
   instead of recordings passively moving through it.
2. The RQ1 controlled-suite paragraph states its scoped conclusion before the
   complete precision/recall/control/folding evidence.
3. The CodeTrace result now makes multi-resolution recurrence, not the table,
   the actor that improves partition agreement.
4. The RQ2 protocol names `we` as the actor that equalizes inputs, fixes the
   protocol before test labels, selects the validation field order, and assigns
   prefix scores.
5. The adaptive RQ2 paragraph states the bounded tie-breaking conclusion before
   reporting its post-hoc numbers.

The edits reorder or directly attribute existing content only. All evidence,
qualifiers, numbers, citations, and scientific meanings are unchanged.

## Exit validation

- `make -C docs/paper`: pass.
- PDF: 9 pages; Conclusion remains on page 7 and References begin on page 8.
- `main.log`: no undefined references/citations and no overfull boxes.
- Exact thesis and four RQs: unchanged.
